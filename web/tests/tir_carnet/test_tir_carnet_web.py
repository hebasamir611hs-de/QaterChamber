"""
web/tests/tir_carnet/test_tir_carnet_web.py — Web-platform cases for
PBI 129403 (QC-SVC-004 — TIR Carnet), sourced from the injected Azure DevOps
suite and handed off by the QA Manager (batch of 4 UI cases).

Scripted here: 138028, 138031, 138033 (delivered on the Web surface) and
138029 (scripted and complete, but BLOCKED — see below).

Batch 2 (2026-09-24, suite 138215) extends this module with 138007/138008
(EN<->AR language switch), 138035/138036 (light/dark mode) and
138037/138038/138039 (desktop/tablet/mobile). Every batch-2 test, plus the
existing 138028/138031/138033, runs in a fresh UNAUTHENTICATED context
(`{"auth": False}`) so a cached CMS storageState carrying
GUEST_LANGUAGE_ID=ar_SA cannot flip the English page under xdist; those
three existing tests also gained the `svc` selector marker. Their
assertions are unchanged. 138029 is untouched.

138029 — scripted, complete, and NOT VERIFIABLE IN THIS BATCH (blocked).
The case carries both `Web` and `Control_Panel` tags: its step 1 is a Liferay
authoring write (give an FAQ answer a heading, a two-item bullet list and an
inline hyperlink, then publish), which belongs to the Control_Panel batch that
is currently deferred — CMS credentials are not configured on this machine.
This module is the **Web** platform module only: per automation-standards.md a
case spanning two platforms becomes one test per platform, never one test with
a branch, and never two platforms in one module. The test below is written
with the case's FULL, unweakened assertions and detects the authored answer on
the live page instead of causing it; it CANNOT PASS until an FAQ answer is
authored with a heading, a two-item bullet list and an inline hyperlink, and
that authoring step is Control_Panel work outside this batch. Until then it
reports a LOUD, concrete `skip` naming the missing content and the CMS step —
never a silent one, and never a narrowed assertion (see automation-standards.md
→ Result integrity: an unavailable precondition is the one legitimate use of
`skip`; narrowing the assertion to make it pass is not). Count it as blocked /
not verified, not as delivered coverage.

Live-environment findings recorded 2026-09-16 against
https://qcdev.ihorizons.com/our-services/tir-carnet and
/ar/our-services/tir-carnet — the canonical paths the Page Object navigates
(see tir_carnet_page.py's module docstring for the locator/structure evidence
and the redirect chain the older /tir-carnet form goes through).
These are expected to turn 138031 RED — they are real deviations from the
design tokens the case states, reported to the QA Manager for Phase 3b bug
filing, and are deliberately NOT softened here:
  - hero gradient renders `linear-gradient(105deg, rgb(74,10,34) 0%,
    rgb(109,16,41) 46%, rgb(131,27,50) 100%)`, not the case's 118deg /
    rgba(70,7,30) → rgba(96,20,48) @48% → rgba(145,23,49);
  - the sticky index panel paints #F6F6F6 but draws NO border at all
    (border-style: none, border-width: 0px) instead of the #EDEDED border,
    and its item labels render #4A4A49 instead of #6C6C6B;
  - the embedded video frame and the numbered-step tiles draw no border at
    all, against the case's enumerated "the embedded video, statistics strip,
    benefit cards, criteria check marks, numbered steps, accordion and
    resource cards ALL render on #FFFFFF surfaces with #EDEDED borders" —
    QA Manager ruling 2026-09-16: "all", enumerated, is the literal contract,
    so a missing border is a deviation, not an exempt design choice. Whether
    the build or the case is wrong is Phase 3b triage's call, not this
    layer's.
"""

import re

import allure
import pytest

from core.web.design_tokens import font_family_contains, hex_to_rgb
from web.pages.tir_carnet.tir_carnet_page import TirCarnetPage

# ---------------------------------------------------------------------------
# Concrete expected data, mirrored verbatim from the approved Azure cases —
# never re-derived from what the live page happens to render.
# ---------------------------------------------------------------------------
# TC 138031 step 2 — hero
HERO_GRADIENT_ANGLE = "118deg"
HERO_GRADIENT_STOP_COLORS = [
    "rgb(70, 7, 30)",    # rgba(70,7,30,1)
    "rgb(96, 20, 48)",   # rgba(96,20,48,1)  @ 48%
    "rgb(145, 23, 49)",  # rgba(145,23,49,1)
]
HERO_GRADIENT_MID_STOP = "48%"
HERO_EYEBROW_TEXT = "Road Transport Service"
HERO_TITLE_TEXT = "TIR Carnet"
WHITE = hex_to_rgb("#FFFFFF")

# TC 138031 step 3 — quick facts + sticky index
QUICK_FACT_TILE_COUNT = 4
INDEX_PANEL_BG = hex_to_rgb("#F6F6F6")
INDEX_PANEL_BORDER = hex_to_rgb("#EDEDED")
INDEX_LABEL_COLOR = hex_to_rgb("#6C6C6B")
INDEX_NUMBERS = ["01", "02", "03", "04"]

# TC 138031 step 4 — content surfaces
SURFACE_BG = hex_to_rgb("#FFFFFF")
SURFACE_BORDER = hex_to_rgb("#EDEDED")
HEADING_COLOR = hex_to_rgb("#1D1D1B")

FONT_FAMILY = "Cairo"

# Numbered-step ("How it works") titles and descriptions are CENTRED in both
# locales — QA Manager ruling 2026-09-24 from the design source: Figma file
# J3e1thav8NIu6a3XhC6Wcl, frame 2878:98459 "Lang=EN, View=Desktop", instance
# "How it works" #2878:98488 is a horizontal stepper whose step-title text
# style "Text-md/Semibold" (8715:150715) has textAlignHorizontal: CENTER, with
# each step centred under its number tile. The cases' blanket "all text
# left/right-aligned" wording does not override the design for this component.
STEP_TEXT_ALIGN = "center"


def _rgb_channels(color: str) -> str:
    """'rgba(255, 255, 255, 0.65)' -> 'rgb(255, 255, 255)'.

    The hero eyebrow is painted white at 65% alpha; the case's expectation is
    the COLOUR ('in white'), not the opacity, so the comparison is made on
    the channels. Alpha is reported separately as an observation."""
    inner = color[color.find("(") + 1:color.rfind(")")]
    parts = [p.strip() for p in inner.split(",")]
    return f"rgb({parts[0]}, {parts[1]}, {parts[2]})"


def _attach(name: str, lines: list) -> None:
    allure.attach(
        "\n".join(lines) if lines else "(none)",
        name=name,
        attachment_type=allure.attachment_type.TEXT,
    )


# ---------------------------------------------------------------------------
# 138028 — FAQ answers are collapsed by default when the page first loads
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("FAQ accordion")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("FAQ answers are collapsed by default when the page first loads")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.eserv
@pytest.mark.pbi_129403
@pytest.mark.tc_138028
@pytest.mark.traceability("138028")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129403")
@allure.label("testcase", "138028")
def test_tir_carnet_faq_answers_collapsed_by_default(page):
    """Asserts ST-8 — the accordion must not render with answers already open."""
    tir = TirCarnetPage(page)

    with allure.step("Open the public TIR Carnet page in English"):
        tir.open_tir_carnet(locale="en")
        assert tir.is_hero_visible(), "TIR Carnet page did not load its hero"

    with allure.step("Scroll to Section 04 Frequently asked questions"):
        tir.scroll_to_faq_section()
        question_count = tir.faq_item_count()
        questions = tir.faq_questions()
        assert question_count > 0, "no FAQ questions rendered in Section 04"
        assert len(questions) == question_count, (
            f"{question_count} FAQ items rendered but {len(questions)} question rows"
        )
        assert all(q.strip() for q in questions), (
            f"an active FAQ question rendered with no text: {questions}"
        )

    with allure.step("Inspect every FAQ item without clicking"):
        expanded_flags = tir.faq_expanded_flags()
        answer_states = tir.faq_answer_states()
        marks_visible = tir.faq_marks_visible()

        assert expanded_flags == ["false"] * question_count, (
            f"an FAQ question is not collapsed on load: aria-expanded={expanded_flags}"
        )
        assert tir.faq_open_item_count() == 0, (
            "an FAQ item carries the expanded (.is-open) state on first load"
        )
        for i, state in enumerate(answer_states):
            assert state["hidden"] is True, f"FAQ answer {i} is not hidden on load: {state}"
            assert state["display"] == "none", f"FAQ answer {i} renders: {state}"
            assert state["height"] == 0, f"FAQ answer {i} occupies height: {state}"
        assert marks_visible == [True] * question_count, (
            f"a question is missing its collapsed-state indicator: {marks_visible}"
        )

    with allure.step("Measure the section height against the number of questions"):
        geometry = tir.faq_accordion_geometry()
        _attach("faq-collapsed-geometry", [str(geometry)])

        # A collapsed accordion's height is fully accounted for by its
        # question rows plus the measured inter-item gaps — no answer
        # contributes any height. Both the row heights and the gaps are read
        # off the live DOM, so no spacing constant is hard-coded here.
        for i, (item_h, question_h) in enumerate(
            zip(geometry["item_heights"], geometry["question_heights"])
        ):
            assert abs(item_h - question_h) <= 4, (
                f"FAQ item {i} is taller than its collapsed question row "
                f"(item {item_h}px vs question {question_h}px) — an answer is expanded"
            )
        expected_height = sum(geometry["item_heights"]) + sum(geometry["gaps"])
        assert abs(geometry["container_height"] - expected_height) <= 4, (
            f"accordion height {geometry['container_height']}px does not match a fully "
            f"collapsed stack of {question_count} questions ({expected_height}px)"
        )


# ---------------------------------------------------------------------------
# 138029 — an expanded FAQ answer renders its rich-text markup
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("FAQ accordion")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An expanded FAQ answer renders its rich-text markup")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.eserv
@pytest.mark.pbi_129403
@pytest.mark.tc_138029
@pytest.mark.traceability("138029")
@allure.label("pbi", "129403")
@allure.label("testcase", "138029")
def test_tir_carnet_expanded_faq_answer_renders_rich_text(page):
    """Asserts ST-9 — an FAQ answer configured with a heading, bullets and an
    inline hyperlink renders that markup, not raw HTML and not stripped.

    Step 1 of the case (authoring that answer in Liferay as a Site Content
    Editor) is the Control_Panel half and is out of this Web batch's scope —
    see the module docstring. This test detects the authored answer on the
    public page; when it is absent it skips with a concrete reason rather
    than asserting something weaker than the case's expected result."""
    tir = TirCarnetPage(page)

    with allure.step("Open the public TIR Carnet page in English and scroll to Section 04"):
        tir.open_tir_carnet(locale="en")
        tir.scroll_to_faq_section()
        assert tir.faq_open_item_count() == 0, "the accordion did not load collapsed"

    rich_index = tir.faq_index_with_rich_answer()
    if rich_index < 0:
        pytest.skip(
            "Precondition not present on this environment: no FAQ answer on "
            "the live TIR Carnet page is configured with a heading + a "
            "two-item bullet list + an inline hyperlink. Step 1 of TC 138029 "
            "authors that answer in Liferay (Control_Panel surface), which is "
            "outside this Web batch's scope. Observed live 2026-09-16: all 11 "
            "answers are a single <p>; only 'Where can I find details of the "
            "TIR convention, 1975?' carries an inline <a> (UNECE website). "
            "Author the answer, then re-run — this test will execute as-is."
        )

    with allure.step(f"Click FAQ question {rich_index + 1}"):
        tir.expand_faq(rich_index)
        assert tir.faq_expanded_flags()[rich_index] == "true", (
            "the clicked FAQ question did not report itself expanded"
        )
        assert tir.faq_answer_states()[rich_index]["display"] != "none", (
            "the clicked FAQ answer did not become visible"
        )

    with allure.step("Inspect the revealed answer"):
        markup = tir.faq_answer_markup(rich_index)
        _attach("faq-answer-html", [markup["html"]])

        # Rendered as markup: the heading, both bullet items and the anchor
        # exist as real DOM nodes.
        assert markup["headings"], f"answer rendered no heading element: {markup['tags']}"
        assert markup["headings"][0].strip(), "the answer's heading rendered empty"
        assert len(markup["bullets"]) >= 2, (
            f"answer rendered {len(markup['bullets'])} bullet items, expected the "
            f"configured two: {markup['bullets']}"
        )
        assert all(b.strip() for b in markup["bullets"][:2]), (
            f"a configured bullet item rendered empty: {markup['bullets']}"
        )
        assert markup["links"], "answer rendered no hyperlink element"
        link = markup["links"][0]
        assert link["text"].strip(), "the inline hyperlink rendered with no text"
        assert link["href"], "the inline hyperlink rendered without an href — not clickable"

        # NOT raw HTML: the tags must not be visible as literal text.
        visible_text = markup["text"]
        for literal in ("<h", "<ul", "<ol", "<li", "<a ", "<p>", "&lt;"):
            assert literal not in visible_text, (
                f"the answer rendered its markup as raw text ({literal!r} is visible): "
                f"{visible_text[:200]}"
            )

        # NOT stripped: the structural tags survived into the delivered DOM.
        tags = markup["tags"]
        assert any(t in tags for t in ("h1", "h2", "h3", "h4", "h5", "h6")), (
            f"the heading was stripped from the delivered answer: {tags}"
        )
        assert tags.get("li", 0) >= 2, f"the bullet list was stripped: {tags}"
        assert tags.get("a", 0) >= 1, f"the hyperlink was stripped: {tags}"


# ---------------------------------------------------------------------------
# 138031 — English page renders LTR and matches the approved Figma tokens
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("English TIR Carnet page renders left-to-right and matches the approved Figma design tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.eserv
@pytest.mark.pbi_129403
@pytest.mark.tc_138031
@pytest.mark.traceability("138031")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129403")
@allure.label("testcase", "138031")
def test_tir_carnet_english_ltr_design_tokens(page):
    """Figma-verified UI case against frame 2878:98459 (EN desktop light).

    Every token the case names is checked; deviations are COLLECTED and
    asserted once at the end so a single run reports the complete deviation
    list for bug filing instead of stopping at the first one. Nothing is
    softened — an empty deviation list is the only pass."""
    tir = TirCarnetPage(page)
    deviations: list = []
    observations: list = []

    with allure.step("Open the public TIR Carnet page in English on a desktop viewport"):
        tir.open_tir_carnet(locale="en")

        direction = tir.document_direction()
        if direction != "ltr":
            deviations.append(f"document dir is {direction!r}, expected 'ltr'")

        # Cairo throughout + left-aligned text, sampled across every block
        # the case's four steps name.
        text_samples = {
            "hero eyebrow": tir.HERO_EYEBROW,
            "hero title": tir.HERO_TITLE,
            "quick-fact label": tir.FACT_LABEL,
            "index label": tir.INDEX_LABEL,
            "section title": tir.SECTION_TITLE,
            "statistic label": tir.STAT_LABEL,
            "benefit card title": tir.CARD_TITLE,
            "criteria row": tir.CRITERION,
            "step title": tir.STEP_TITLE,
            "FAQ question": tir.FAQ_QUESTION,
            "resource card title": tir.FILE_TITLE,
        }
        for name, locator in text_samples.items():
            style = tir.computed_style(locator, ["fontFamily", "textAlign", "direction"])
            if not font_family_contains(style["fontFamily"], FONT_FAMILY):
                deviations.append(
                    f"{name} font-family is {style['fontFamily']!r}, expected {FONT_FAMILY}"
                )
            if name == "step title":
                continue  # centred per the Figma stepper — asserted below with STEP_TEXT_ALIGN
            # 'start' resolves to left under dir=ltr — the same reading used
            # by the sibling GM Message / VMO token tests.
            if style["textAlign"] not in ("left", "start"):
                deviations.append(
                    f"{name} text-align is {style['textAlign']!r}, expected left-aligned"
                )
        # Numbered steps: centred (Figma 2878:98488, see STEP_TEXT_ALIGN).
        for name, locator in (("step title", tir.STEP_TITLE), ("step description", tir.STEP_DESC)):
            for style in tir.computed_styles_all(locator, ["textAlign"]):
                if style["textAlign"] != STEP_TEXT_ALIGN:
                    deviations.append(
                        f"{name} text-align is {style['textAlign']!r}, expected {STEP_TEXT_ALIGN!r} (Figma 2878:98488)"
                    )

    with allure.step("Inspect the hero"):
        gradient = tir.hero_gradient_parts()
        _attach("hero-gradient-computed", [gradient["raw"]])

        if gradient["angle"] != HERO_GRADIENT_ANGLE:
            deviations.append(
                f"hero gradient angle is {gradient['angle']!r}, expected {HERO_GRADIENT_ANGLE!r}"
            )
        stop_colors = [color for color, _ in gradient["stops"]]
        if stop_colors != HERO_GRADIENT_STOP_COLORS:
            deviations.append(
                f"hero gradient stops are {stop_colors}, expected {HERO_GRADIENT_STOP_COLORS}"
            )
        stop_positions = [position for _, position in gradient["stops"]]
        if HERO_GRADIENT_MID_STOP not in stop_positions:
            deviations.append(
                f"hero gradient mid stop is at {stop_positions}, expected one at "
                f"{HERO_GRADIENT_MID_STOP}"
            )

        eyebrow_text = tir.hero_eyebrow_text()
        if eyebrow_text != HERO_EYEBROW_TEXT:
            deviations.append(f"hero eyebrow is {eyebrow_text!r}, expected {HERO_EYEBROW_TEXT!r}")
        title_text = tir.hero_title_text()
        if title_text != HERO_TITLE_TEXT:
            deviations.append(f"hero title is {title_text!r}, expected {HERO_TITLE_TEXT!r}")

        eyebrow_color = tir.computed_style(tir.HERO_EYEBROW, ["color"])["color"]
        if _rgb_channels(eyebrow_color) != WHITE:
            deviations.append(f"hero eyebrow colour is {eyebrow_color}, expected white")
        if "rgba" in eyebrow_color:
            observations.append(f"hero eyebrow is white at reduced opacity: {eyebrow_color}")
        title_color = tir.computed_style(tir.HERO_TITLE, ["color"])["color"]
        if _rgb_channels(title_color) != WHITE:
            deviations.append(f"hero title colour is {title_color}, expected white")

    with allure.step("Inspect the quick-facts strip and the sticky section index"):
        fact_count = tir.fact_count()
        if fact_count != QUICK_FACT_TILE_COUNT:
            deviations.append(
                f"quick-facts strip shows {fact_count} tiles, expected {QUICK_FACT_TILE_COUNT}"
            )
        if not all(tir.fact_labels()) or not all(tir.fact_values()):
            deviations.append(
                f"a quick-fact tile is not configured: labels={tir.fact_labels()} "
                f"values={tir.fact_values()}"
            )

        index_style = tir.computed_style(
            tir.INDEX, ["backgroundColor", "borderColor", "borderStyle", "borderWidth"]
        )
        _attach("sticky-index-computed", [str(index_style)])
        if index_style["backgroundColor"] != INDEX_PANEL_BG:
            deviations.append(
                f"sticky index panel background is {index_style['backgroundColor']}, "
                f"expected #F6F6F6 ({INDEX_PANEL_BG})"
            )
        if index_style["borderStyle"] == "none" or index_style["borderWidth"] == "0px":
            deviations.append(
                "sticky index panel draws no border at all "
                f"(border-style={index_style['borderStyle']}, "
                f"border-width={index_style['borderWidth']}), expected an #EDEDED border"
            )
        elif index_style["borderColor"] != INDEX_PANEL_BORDER:
            deviations.append(
                f"sticky index panel border is {index_style['borderColor']}, "
                f"expected #EDEDED ({INDEX_PANEL_BORDER})"
            )

        index_numbers = tir.index_numbers()
        if index_numbers != INDEX_NUMBERS:
            deviations.append(f"sticky index lists {index_numbers}, expected {INDEX_NUMBERS}")
        if not all(tir.index_labels()):
            deviations.append(f"a sticky index entry has no label: {tir.index_labels()}")
        index_label_color = tir.computed_style(tir.INDEX_LABEL, ["color"])["color"]
        if index_label_color != INDEX_LABEL_COLOR:
            deviations.append(
                f"sticky index labels are {index_label_color}, "
                f"expected #6C6C6B ({INDEX_LABEL_COLOR})"
            )

    with allure.step("Inspect the Overview video and statistics, a benefit card and a resource card"):
        if not tir.is_video_embedded():
            deviations.append("the Overview section renders no embedded video")
        if tir.stat_count() == 0:
            deviations.append("the statistics strip rendered no statistics")
        if tir.card_count() == 0:
            deviations.append("no benefit cards rendered")
        if tir.criterion_count() == 0:
            deviations.append("no criteria rows rendered")
        if tir.step_count() == 0:
            deviations.append("no numbered steps rendered")
        if tir.faq_item_count() == 0:
            deviations.append("the accordion rendered no FAQ items")
        if tir.file_count() == 0:
            deviations.append("no resource cards rendered")

        surfaces = {
            "embedded video": tir.VIDEO,
            "statistics strip": tir.STATS,
            "benefit card": tir.CARD,
            "criteria row": tir.CRITERION,
            "numbered step": tir.STEP,
            "accordion item": tir.FAQ_ITEM,
            "resource card": tir.FILE,
        }
        for name, locator in surfaces.items():
            # The blocks below mostly declare a transparent background and
            # render on the white .qc-tir-body surface, so the check is on
            # the surface they VISUALLY render on — see the Page Object's
            # effective_background().
            effective_bg = tir.effective_background(locator)
            if effective_bg != SURFACE_BG:
                deviations.append(
                    f"{name} renders on {effective_bg}, expected #FFFFFF ({SURFACE_BG})"
                )
            border = tir.computed_style(locator, ["borderStyle", "borderWidth", "borderColor"])
            if border["borderStyle"] == "none" or border["borderWidth"] == "0px":
                # The case enumerates all seven blocks and says they ALL
                # render with #EDEDED borders — QA Manager ruling 2026-09-16:
                # that literal, enumerated contract is what this layer
                # asserts, so a borderless block is a deviation, not an
                # exempt design choice (on the live build the video frame and
                # the step tiles are borderless). Triage decides in Phase 3b
                # whether the build or the case is wrong.
                deviations.append(
                    f"{name} draws no border (border-style={border['borderStyle']}, "
                    f"border-width={border['borderWidth']}), expected an #EDEDED border"
                )
            elif border["borderColor"] != SURFACE_BORDER:
                deviations.append(
                    f"{name} border is {border['borderColor']}, expected #EDEDED ({SURFACE_BORDER})"
                )

        headings = {
            "section title": tir.SECTION_TITLE,
            "benefit card title": tir.CARD_TITLE,
            "step title": tir.STEP_TITLE,
            "FAQ question": tir.FAQ_QUESTION,
            "resource card title": tir.FILE_TITLE,
        }
        for name, locator in headings.items():
            color = tir.computed_style(locator, ["color"])["color"]
            if color != HEADING_COLOR:
                deviations.append(
                    f"{name} colour is {color}, expected #1D1D1B ({HEADING_COLOR})"
                )

    _attach("design-token-deviations", deviations)
    _attach("design-token-observations", observations)
    assert not deviations, (
        "EN TIR Carnet page deviates from the approved Figma tokens:\n- "
        + "\n- ".join(deviations)
    )


# ---------------------------------------------------------------------------
# 138033 — Arabic page renders RTL with index, content and accordion mirrored
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("Arabic / RTL rendering")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Arabic TIR Carnet page renders right-to-left with the index, content and accordion mirrored")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.eserv
@pytest.mark.pbi_129403
@pytest.mark.tc_138033
@pytest.mark.traceability("138033")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129403")
@allure.label("testcase", "138033")
def test_tir_carnet_arabic_rtl_mirrored(page):
    """Figma-verified RTL case against frame 2878:98511 (AR desktop light)."""
    tir = TirCarnetPage(page)

    with allure.step("Open the public TIR Carnet page in Arabic on a desktop viewport"):
        tir.open_tir_carnet(locale="ar")
        assert tir.document_direction() == "rtl", (
            f"document dir is {tir.document_direction()!r}, expected 'rtl'"
        )

        for name, locator in {
            "hero title": tir.HERO_TITLE,
            "index label": tir.INDEX_LABEL,
            "section title": tir.SECTION_TITLE,
            "benefit card title": tir.CARD_TITLE,
            "criteria row": tir.CRITERION,
            "step title": tir.STEP_TITLE,
            "FAQ question": tir.FAQ_QUESTION,
        }.items():
            style = tir.computed_style(locator, ["fontFamily", "textAlign", "direction"])
            assert font_family_contains(style["fontFamily"], FONT_FAMILY), (
                f"{name} font-family is {style['fontFamily']!r}, expected {FONT_FAMILY}"
            )
            assert style["direction"] == "rtl", (
                f"{name} renders with direction {style['direction']!r}, expected rtl"
            )
            if name == "step title":
                continue  # centred per the Figma stepper — asserted below with STEP_TEXT_ALIGN
            # 'start' resolves to right under dir=rtl — same reading as the
            # sibling GM Message RTL token test.
            assert style["textAlign"] in ("right", "start"), (
                f"{name} text-align is {style['textAlign']!r}, expected right-aligned"
            )
        # Numbered steps: centred in AR too (Figma 2878:98488, see STEP_TEXT_ALIGN).
        for name, locator in (("step title", tir.STEP_TITLE), ("step description", tir.STEP_DESC)):
            for style in tir.computed_styles_all(locator, ["textAlign"]):
                assert style["textAlign"] == STEP_TEXT_ALIGN, (
                    f"{name} text-align is {style['textAlign']!r}, expected {STEP_TEXT_ALIGN!r} (Figma 2878:98488)"
                )

    with allure.step("Inspect the page direction and text alignment"):
        arabic_fields = {
            "index label": tir.index_labels(),
            "section badge": tir.section_badges(),
            "section title": tir.section_titles(),
            "statistic label": tir.stat_labels(),
            "benefit card title": tir.card_titles(),
            "criteria row": tir.criterion_texts(),
            "step title": tir.step_titles(),
            "FAQ question": tir.faq_questions(),
        }
        for name, values in arabic_fields.items():
            assert values, f"no {name} rendered on the Arabic page"
            for value in values:
                assert tir.contains_arabic(value), (
                    f"{name} did not render its Arabic value: {value!r}"
                )

    with allure.step("Inspect the placement of the sticky index relative to the content column"):
        index_box = tir.index_box()
        content_box = tir.content_box()
        assert index_box is not None and content_box is not None
        assert index_box["x"] >= content_box["x"] + content_box["width"], (
            "the sticky index is not mirrored to the right of the content column "
            f"(index x={index_box['x']}, content spans "
            f"{content_box['x']}-{content_box['x'] + content_box['width']})"
        )

    with allure.step("Inspect the criteria check marks, the numbered steps and the FAQ accordion"):
        # Criteria check marks sit on the leading (right) edge of each row.
        rows = tir.criterion_boxes()
        checks = tir.criterion_check_boxes()
        assert rows and len(checks) == len(rows)
        for i, (row, check) in enumerate(zip(rows, checks)):
            assert check["x"] > row["x"] + row["width"] / 2, (
                f"criteria check mark {i} is not on the leading (right) edge of its row "
                f"(check x={check['x']}, row spans {row['x']}-{row['x'] + row['width']})"
            )
            gap_to_right = (row["x"] + row["width"]) - (check["x"] + check["width"])
            gap_to_left = check["x"] - row["x"]
            assert gap_to_right < gap_to_left, (
                f"criteria check mark {i} is closer to the trailing edge than the leading one"
            )

        # Step numbers lead each step on the right: the numbered steps flow
        # right-to-left (step 01 rightmost) and each step's number precedes
        # its text.
        step_boxes = tir.step_boxes()
        assert len(step_boxes) > 1, "fewer than two numbered steps rendered"
        assert step_boxes[0]["x"] > step_boxes[-1]["x"], (
            "the numbered steps are not mirrored — the first step is not on the right "
            f"(first x={step_boxes[0]['x']}, last x={step_boxes[-1]['x']})"
        )
        num_boxes = tir.step_number_boxes()
        text_boxes = tir.step_text_boxes()
        for i, (num, text) in enumerate(zip(num_boxes, text_boxes)):
            assert num["y"] <= text["y"], (
                f"step {i}'s number does not lead its text (number y={num['y']}, "
                f"text y={text['y']})"
            )

        # The accordion expand indicator is mirrored: it sits at the RTL
        # trailing edge (visually left) of the question row, the mirror of the
        # English page where it renders at the right edge.
        mark = tir.faq_mark_box(0)
        question = tir.faq_question_box(0)
        assert mark is not None and question is not None
        assert mark["x"] < question["x"] + question["width"] / 2, (
            "the FAQ expand indicator is not mirrored — it still renders on the right "
            f"(mark x={mark['x']}, question spans "
            f"{question['x']}-{question['x'] + question['width']})"
        )


# ===========================================================================
# Batch 2 (2026-09-24, suite 138215): language switch, light/dark theme and
# desktop/tablet/mobile viewports. Each test collects every expected-vs-actual
# deviation in `_Check` and fails once with the full list.
# ===========================================================================
ANON = {"auth": False}
anonymous = pytest.mark.parametrize("page", [ANON], indirect=True)

EN_INDEX_ITEMS = ["01 Overview", "02 Eligibility & Prerequisites", "03 How it works",
                  "04 Frequently asked questions"]
HEADER_NAV_LIGHT = hex_to_rgb("#1D1D1B")
PAGE_BG_LIGHT = hex_to_rgb("#FFFFFF")
# WCAG 2.x AA — "remains legible" states no number; the published minimum is
# the measurable floor (4.5:1 normal text, 3:1 large text).
AA_NORMAL, AA_LARGE = 4.5, 3.0
# Leftover qcdev authoring/probe records look like this; a non-Arabic value
# matching it is labelled TEST DATA in the deviation text (triage aid only —
# it still fails).
_TEST_DATA_RE = re.compile(r"\b(test|probe|lorem|dummy|qa|editor\d*)\b", re.I)


class _Check:
    """Soft-assert collector: every comparison is recorded, the test ends with
    `assert not check.deviations, check.report()`."""

    def __init__(self):
        self.deviations = []
        self._step = ""

    def step(self, name: str) -> None:
        self._step = name

    def truthy(self, label: str, condition: bool, expected, actual) -> None:
        if not condition:
            self.deviations.append(f"[{self._step}] {label}: expected {expected!r}, got {actual!r}")

    def equals(self, label: str, actual, expected) -> None:
        self.truthy(label, actual == expected, expected, actual)

    def px(self, label: str, actual: float, expected: float, tol: float = 1.0) -> None:
        self.truthy(label, actual is not None and abs(actual - expected) <= tol, f"{expected}px", actual)

    def report(self) -> str:
        return "\n".join([f"{len(self.deviations)} deviation(s):", *(f"  - {d}" for d in self.deviations)])


def _overlap(a, b) -> bool:
    if not a or not b:
        return False
    return (a["x"] < b["x"] + b["width"] - 1 and b["x"] < a["x"] + a["width"] - 1
            and a["y"] < b["y"] + b["height"] - 1 and b["y"] < a["y"] + a["height"] - 1)


def _arabic_or_flag(check: _Check, name: str, value: str) -> None:
    if TirCarnetPage.contains_arabic(value):
        return
    tag = " [TEST DATA? leftover qcdev record]" if _TEST_DATA_RE.search(value or "") else ""
    check.truthy(f"{name} is Arabic{tag}", False, "Arabic text", value)


def _check_no_overflow(check: _Check, tir: TirCarnetPage) -> None:
    overflow = tir.horizontal_overflow_px()
    check.truthy("no horizontal scrollbar", overflow <= 0, "0px", f"{overflow}px {tir.overflowing_elements()}")
    clipped = tir.clipped_text_elements()
    check.truthy("no clipped content", not clipped, "no clipped text", clipped)


def _check_top_no_overlap(check: _Check, tir: TirCarnetPage) -> None:
    regions = {"hero copy": tir.HERO_COPY, "hero image": tir.HERO_ART, "quick-facts strip": tir.FACTS,
               "content column": tir.CONTENT}
    if tir.is_displayed(tir.INDEX_COL):
        regions["section index"] = tir.INDEX_COL
    boxes = {n: tir.box(l) for n, l in regions.items()}
    names = list(boxes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            check.truthy(f"{names[i]} / {names[j]} do not overlap", not _overlap(boxes[names[i]], boxes[names[j]]),
                         "no overlap", f"{boxes[names[i]]} vs {boxes[names[j]]}")


def _check_index_on_narrow(check: _Check, tir: TirCarnetPage) -> None:
    """The index must collapse (compact control) or reposition without
    overlapping content; removed entirely with no collapsed control is
    recorded as a deviation (same reading as the ATA Carnet batch)."""
    if tir.is_displayed(tir.INDEX_COL):
        check.truthy("section index repositioned without overlapping content",
                     not _overlap(tir.box(tir.INDEX_COL), tir.box(tir.CONTENT)), "no overlap",
                     f"index={tir.box(tir.INDEX_COL)} content={tir.box(tir.CONTENT)}")
    else:
        shown = sum(1 for i in range(tir.index_item_count()) if tir.is_displayed(tir.INDEX_ITEM, i))
        display = tir.computed_style(tir.INDEX_COL, ["display"])["display"]
        check.truthy("section index collapses or repositions", shown > 0,
                     "a collapsed or repositioned section index still offering section navigation",
                     f"index column display={display!r}; 0 of {tir.index_item_count()} index entries rendered "
                     f"and no collapsed control present (index removed entirely)")


def _check_sections(check: _Check, tir: TirCarnetPage) -> None:
    n = tir.count(tir.SECTION_BLOCK)
    check.truthy("four sections plus the resources block render", n == 5, 5, n)
    for i in range(n):
        check.truthy(f"section block {i + 1} rendered", tir.is_displayed(tir.SECTION_BLOCK, i), "visible", "hidden")


# ---------------------------------------------------------------------------
# 138007 — EN -> AR
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("Language toggle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Switching the site language from English to Arabic renders the TIR Carnet page in Arabic")
@allure.label("pbi", "129403")
@allure.label("testcase", "138007")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_129403
@pytest.mark.tc_138007
@anonymous
def test_tir_carnet_language_switch_en_to_ar(page):
    """Azure TC 138007 | PBI 129403 — EN page (four-entry index) -> header 'AR'
    toggle -> Arabic RTL, toggle offers 'EN'; index labels, section content,
    statistics labels, benefit card text, criteria, steps, FAQ questions AND
    answers (read via textContent while collapsed) and resource titles are
    Arabic and right-aligned."""
    tir = TirCarnetPage(page)
    check = _Check()

    with allure.step("Open the English page with the four-entry index"):
        tir.open_tir_carnet(locale="en")
        check.step("step 1")
        check.equals("index entries", [f"{n} {l}" for n, l in zip(tir.index_numbers(), tir.index_labels())],
                     EN_INDEX_ITEMS)

    with allure.step("Click the 'AR' toggle"):
        check.equals("toggle label before switch", tir.language_toggle_label(), "AR")
        tir.toggle_language()

    with allure.step("Arabic RTL; toggle offers 'EN'"):
        check.step("step 3")
        check.equals("document dir", tir.document_direction(), "rtl")
        check.equals("toggle label after switch", tir.language_toggle_label(), "EN")

    with allure.step("All content slots Arabic and right-aligned"):
        check.step("step 4")
        slots = {
            "index label": tir.INDEX_LABEL, "section title": tir.SECTION_TITLE, "section content": tir.SECTION_PROSE,
            "statistics label": tir.STAT_LABEL, "benefit card title": tir.CARD_TITLE,
            "benefit card text": tir.CARD_DESC, "criterion": tir.CRITERION, "step title": tir.STEP_TITLE,
            "step text": tir.STEP_DESC, "FAQ question": tir.FAQ_QUESTION, "FAQ answer": tir.FAQ_ANSWER,
            "resource title": tir.FILE_TITLE,
        }
        for name, loc in slots.items():
            values = tir.text_contents(loc)
            check.truthy(f"{name}s rendered", len(values) > 0, "at least one", values)
            for v in values:
                _arabic_or_flag(check, name, v)
            # Numbered steps are centred per Figma 2878:98488 (STEP_TEXT_ALIGN);
            # every other slot must be right-aligned.
            expected_align = STEP_TEXT_ALIGN if loc in (tir.STEP_TITLE, tir.STEP_DESC) else "right"
            for i in range(len(values)):
                align = tir.resolved_text_align(loc, i)
                check.truthy(f"{name} {i + 1} aligned {expected_align}", align == expected_align, expected_align, align)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138008 — AR -> EN
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("Language toggle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Switching the site language from Arabic back to English restores English content and LTR")
@allure.label("pbi", "129403")
@allure.label("testcase", "138008")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129403
@pytest.mark.tc_138008
@anonymous
def test_tir_carnet_language_switch_ar_to_en(page):
    """Azure TC 138008 | PBI 129403 — AR page -> 'EN' toggle -> English LTR, index
    on the left reading 01 Overview ... 04 Frequently asked questions. The
    step-2 "section in view" is recorded (Allure), not asserted — the
    expected result makes no claim about it."""
    tir = TirCarnetPage(page)
    check = _Check()

    with allure.step("Open the Arabic page"):
        tir.open_tir_carnet(locale="ar")
        check.step("step 1")
        check.equals("document dir", tir.document_direction(), "rtl")
        allure.attach(str(tir.section_in_view()), "section in view before switch", allure.attachment_type.TEXT)

    with allure.step("Click the 'EN' toggle"):
        tir.toggle_language()

    with allure.step("English LTR, index on the left with the four English entries"):
        check.step("step 4")
        check.equals("document dir", tir.document_direction(), "ltr")
        idx, content = tir.index_box(), tir.content_box()
        check.truthy("index on the left of the content column",
                     idx is not None and content is not None and idx["x"] + idx["width"] <= content["x"] + 1,
                     "index right edge <= content left edge", f"index={idx} content={content}")
        entries = [f"{n} {l}" for n, l in zip(tir.index_numbers(), tir.index_labels())]
        check.equals("index entries", entries, EN_INDEX_ITEMS)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138035 — light mode
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("Theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TIR Carnet page renders correctly in light mode")
@allure.label("pbi", "129403")
@allure.label("testcase", "138035")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.pbi_129403
@pytest.mark.tc_138035
@anonymous
def test_tir_carnet_light_mode(page):
    """Azure TC 138035 | PBI 129403 — ST-13 light mode (site default), frame
    2878:98459. "Light surface" = effective background #FFFFFF; "legible" =
    WCAG AA contrast (see AA_NORMAL/AA_LARGE)."""
    tir = TirCarnetPage(page)
    check = _Check()
    tir.open_tir_carnet(locale="en")
    check.step("step 1")
    check.truthy("light theme active", tir.theme() in (None, "light"), "light", tir.theme())

    with allure.step("Page, header and sticky index"):
        check.step("step 3")
        check.equals("page background", tir.computed_style(tir.PAGE_BODY, ["backgroundColor"])["backgroundColor"],
                     PAGE_BG_LIGHT)
        check.equals("header background", tir.computed_style(tir.HEADER, ["backgroundColor"])["backgroundColor"],
                     PAGE_BG_LIGHT)
        for colour in sorted({s["color"] for s in tir.computed_styles_all(tir.HEADER_NAV_LINK, ["color"])}):
            check.equals("header navigation label colour", colour, HEADER_NAV_LIGHT)
        idx = tir.computed_style(tir.INDEX, ["backgroundColor", "borderTopWidth", "borderTopStyle", "borderTopColor"])
        check.equals("index surface", idx["backgroundColor"], INDEX_PANEL_BG)
        check.equals("index border", f"{idx['borderTopWidth']} {idx['borderTopStyle']}", "1px solid")
        check.equals("index border colour", idx["borderTopColor"], INDEX_PANEL_BORDER)
        for colour in sorted({s["color"] for s in tir.computed_styles_all(tir.INDEX_LABEL, ["color"])}):
            check.equals("index label colour", colour, INDEX_LABEL_COLOR)

    with allure.step("Benefit cards, criteria list and resource cards"):
        check.step("step 4")
        for name, loc, text_loc in (("benefit card", tir.CARD, tir.CARD_TITLE),
                                    ("criteria row", tir.CRITERION, tir.CRITERION),
                                    ("resource card", tir.FILE, tir.FILE_TITLE)):
            styles = tir.computed_styles_all(loc, ["borderTopWidth", "borderTopStyle", "borderTopColor"])
            check.truthy(f"{name}s rendered", len(styles) > 0, "at least one", 0)
            check.equals(f"{name} surface", tir.effective_background(loc), SURFACE_BG)
            for i, s in enumerate(styles):
                check.equals(f"{name} {i + 1} border", f"{s['borderTopWidth']} {s['borderTopStyle']}", "1px solid")
                check.equals(f"{name} {i + 1} border colour", s["borderTopColor"], SURFACE_BORDER)
            for i in range(tir.count(text_loc)):
                c = tir.text_contrast(text_loc, i)
                need = AA_LARGE if c["fontSize"] >= 24 or (c["fontSize"] >= 18.66 and c["fontWeight"] >= 700) else AA_NORMAL
                check.truthy(f"{name} {i + 1} legible", c["ratio"] is not None and c["ratio"] >= need,
                             f">= {need}:1", f"{c['ratio']}:1 ({c['color']} on {c['background']})")

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138036 — dark mode
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("Theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TIR Carnet page renders correctly in dark mode")
@allure.label("pbi", "129403")
@allure.label("testcase", "138036")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.pbi_129403
@pytest.mark.tc_138036
@anonymous
def test_tir_carnet_dark_mode(page):
    """Azure TC 138036 | PBI 129403 — ST-14 dark mode via the Accessibility tools
    widget. No dark hex tokens are stated, so: page/header backgrounds dark
    (relative luminance < 0.2); index labels, section headings and section
    body text meet WCAG AA against their real background; benefit cards, the
    video frame, the FAQ accordion items and resource cards render on a dark
    effective surface; the hero gradient is unchanged from light mode."""
    tir = TirCarnetPage(page)
    check = _Check()
    tir.open_tir_carnet(locale="en")
    tir.wait_for_fonts()
    light_hero = tir.hero_gradient_raw()

    with allure.step("Turn dark mode on"):
        tir.enable_dark_mode()
        check.step("step 1")
        check.equals("dark theme active", tir.theme(), "dark")

    with allure.step("Page/header dark; index labels, headings and body text legible"):
        check.step("step 3")
        for name, loc in (("page", tir.PAGE_BODY), ("header", tir.HEADER)):
            bg = tir.computed_style(loc, ["backgroundColor"])["backgroundColor"]
            check.truthy(f"{name} background is dark", tir.relative_luminance(bg) < 0.2, "luminance < 0.2", bg)
        for name, loc in (("index label", tir.INDEX_LABEL), ("section heading", tir.SECTION_TITLE),
                          ("section body text", tir.SECTION_RT)):
            for i in range(tir.count(loc)):
                c = tir.text_contrast(loc, i)
                if c["ratio"] is None:
                    allure.attach(str(c), f"{name} {i + 1}: contrast not measurable", allure.attachment_type.TEXT)
                    continue
                need = AA_LARGE if c["fontSize"] >= 24 or (c["fontSize"] >= 18.66 and c["fontWeight"] >= 700) else AA_NORMAL
                check.truthy(f"{name} {i + 1} contrast", c["ratio"] >= need, f">= {need}:1",
                             f"{c['ratio']}:1 ({c['color']} on {c['background']}, '{c['text']}')")

    with allure.step("Cards, video frame, accordion and resource cards dark; hero gradient unchanged"):
        check.step("step 4")
        for name, loc in (("benefit card", tir.CARD), ("video player frame", tir.VIDEO),
                          ("FAQ accordion item", tir.FAQ_ITEM), ("resource card", tir.FILE)):
            bg = tir.effective_background(loc)
            check.truthy(f"{name} surface is dark", bg != "none" and tir.relative_luminance(bg) < 0.2,
                         "luminance < 0.2", bg)
        check.equals("hero gradient unchanged", tir.hero_gradient_raw(), light_hero)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138037 — desktop
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TIR Carnet page renders correctly at desktop viewport width (1920x1080)")
@allure.label("pbi", "129403")
@allure.label("testcase", "138037")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129403
@pytest.mark.tc_138037
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_tir_carnet_desktop_viewport(page):
    """Azure TC 138037 | PBI 129403 — ENV-1 at 1920x1080. "Video at its designed
    width" has no number in the case; it is read as the video spanning its
    content section's full width at a 16:9 ratio (disclosed)."""
    tir = TirCarnetPage(page)
    check = _Check()
    tir.open_tir_carnet(locale="en")

    with allure.step("No horizontal scrollbar, clipping or overlap"):
        check.step("steps 2-3")
        _check_no_overflow(check, tir)
        _check_top_no_overlap(check, tir)

    with allure.step("Sticky index left; facts, statistics and cards in rows; video width"):
        check.step("step 4")
        _check_sections(check, tir)
        idx, content = tir.index_box(), tir.content_box()
        check.truthy("sticky index on the left with the content beside it",
                     idx is not None and idx["x"] + idx["width"] <= content["x"] + 1,
                     "index right edge <= content left edge", f"index={idx} content={content}")
        for name, loc, n in (("quick-facts tile", tir.FACT, 4), ("statistic", tir.STAT, None),
                             ("benefit card", tir.CARD, None)):
            tir.scroll_to(loc)
            boxes = tir.boxes(loc)
            if n is not None:
                check.equals(f"{name} count", len(boxes), n)
            check.truthy(f"{name}s in one row", len({round(b['y']) for b in boxes if b}) == 1,
                         "same row", [b["y"] if b else None for b in boxes])
        tir.scroll_to(tir.VIDEO)
        video, section = tir.box(tir.VIDEO), tir.box(tir.SECTION_BLOCK)
        check.px("video width (full section width)", video["width"] if video else None,
                 section["width"] if section else 0)
        if video:
            check.truthy("video 16:9", abs(video["width"] / video["height"] - 16 / 9) < 0.02, "16:9",
                         f"{video['width']}x{video['height']}")

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138038 — tablet
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TIR Carnet page renders correctly at tablet viewport width (768x1024)")
@allure.label("pbi", "129403")
@allure.label("testcase", "138038")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129403
@pytest.mark.tc_138038
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_tir_carnet_tablet_viewport(page):
    """Azure TC 138038 | PBI 129403 — ENV-2 responsive integrity at 768x1024
    (no tablet frame, Assumption A-4). Index reading as in
    _check_index_on_narrow."""
    tir = TirCarnetPage(page)
    check = _Check()
    tir.open_tir_carnet(locale="en")

    with allure.step("No horizontal scrollbar, clipping or overlap"):
        check.step("steps 2-3")
        _check_no_overflow(check, tir)
        _check_top_no_overlap(check, tir)

    with allure.step("Sections, index, video scaling, legible accordion/criteria/resources"):
        check.step("step 4")
        _check_sections(check, tir)
        _check_index_on_narrow(check, tir)
        tir.scroll_to(tir.VIDEO)
        video, section = tir.box(tir.VIDEO), tir.box(tir.SECTION_BLOCK)
        check.truthy("video scales to the narrower column", video is not None and section is not None
                     and abs(video["width"] - section["width"]) <= 1 and video["x"] + video["width"] <= 769,
                     "video width == column width, inside viewport", f"video={video} column={section}")
        tir.scroll_to(tir.FILES)
        for i in range(tir.count(tir.FILE)):
            a, b = tir.child_box(tir.FILE, tir.FILE_TITLE, i), tir.child_box(tir.FILE, tir.FILE_BUTTON, i)
            check.truthy(f"resource card {i + 1} title/button no overlap", not _overlap(a, b), "no overlap", f"{a} vs {b}")
        tir.scroll_to(tir.CRITERIA)
        crit = [b for b in tir.criterion_boxes() if b]
        for i in range(len(crit) - 1):
            check.truthy(f"criteria rows {i + 1}/{i + 2} no overlap", not _overlap(crit[i], crit[i + 1]),
                         "no overlap", f"{crit[i]} vs {crit[i + 1]}")
        tir.scroll_to(tir.FAQ)
        faq = [b for b in tir.boxes(tir.FAQ_ITEM) if b]
        for i in range(len(faq) - 1):
            check.truthy(f"FAQ items {i + 1}/{i + 2} no overlap", not _overlap(faq[i], faq[i + 1]),
                         "no overlap", f"{faq[i]} vs {faq[i + 1]}")

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138039 — mobile
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("TIR Carnet")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TIR Carnet page renders correctly at mobile viewport width (375x812)")
@allure.label("pbi", "129403")
@allure.label("testcase", "138039")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129403
@pytest.mark.tc_138039
@pytest.mark.parametrize("page", [{"viewport": (375, 812), "auth": False}], indirect=True)
def test_tir_carnet_mobile_viewport(page):
    """Azure TC 138039 | PBI 129403 — ENV-3 at 375x812. Every listed block is
    checked for horizontal overflow; one-per-row stacking is asserted for the
    quick-facts, benefit cards, steps, accordion and resource cards. The
    statistics grid is checked for overflow only (it may wrap 2-up on a
    phone — same disclosed reading as the ATA country grid)."""
    tir = TirCarnetPage(page)
    check = _Check()
    tir.open_tir_carnet(locale="en")

    with allure.step("No horizontal scrollbar, clipping or overlap"):
        check.step("steps 2-3")
        _check_no_overflow(check, tir)
        _check_top_no_overlap(check, tir)

    with allure.step("Single column; index; video; blocks stack without overflow"):
        check.step("step 4")
        _check_sections(check, tir)
        content = tir.content_box()
        for i, s in enumerate(tir.boxes(tir.SECTION_BLOCK)):
            check.truthy(f"section block {i + 1} in the single column",
                         s is not None and s["x"] >= content["x"] - 1 and s["x"] + s["width"] <= content["x"] + content["width"] + 1,
                         "inside the single content column", f"{s} vs {content}")
        _check_index_on_narrow(check, tir)
        tir.scroll_to(tir.VIDEO)
        video = tir.box(tir.VIDEO)
        check.truthy("video scales to the viewport without overflowing",
                     video is not None and video["x"] >= 0 and video["x"] + video["width"] <= 376,
                     "inside the 375px viewport", video)
        for name, loc, stack in (("quick-facts tile", tir.FACT, True), ("statistic", tir.STAT, False),
                                 ("benefit card", tir.CARD, True), ("step", tir.STEP, True),
                                 ("FAQ item", tir.FAQ_ITEM, True), ("resource card", tir.FILE, True)):
            tir.scroll_to(loc)
            boxes = [b for b in tir.boxes(loc) if b]
            check.truthy(f"{name}s rendered", len(boxes) > 0, "at least one", 0)
            for i, b in enumerate(boxes):
                check.truthy(f"{name} {i + 1} within viewport", b["x"] >= -1 and b["x"] + b["width"] <= 376,
                             "no horizontal overflow", b)
            if stack:
                ok = all(boxes[i]["y"] + boxes[i]["height"] <= boxes[i + 1]["y"] + 1 for i in range(len(boxes) - 1))
                check.truthy(f"{name}s stacked", ok, "one per row", [round(b["y"]) for b in boxes])

    assert not check.deviations, check.report()

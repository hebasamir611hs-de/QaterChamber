"""
web/tests/tir_carnet/test_tir_carnet_web.py — Web-platform cases for
PBI 129403 (QC-SVC-004 — TIR Carnet), sourced from the injected Azure DevOps
suite and handed off by the QA Manager (batch of 4 UI cases).

Scripted here: 138028, 138031, 138033 (delivered on the Web surface) and
138029 (scripted and complete, but BLOCKED — see below).

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
            # 'start' resolves to left under dir=ltr — the same reading used
            # by the sibling GM Message / VMO token tests.
            if style["textAlign"] not in ("left", "start"):
                deviations.append(
                    f"{name} text-align is {style['textAlign']!r}, expected left-aligned"
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
            # 'start' resolves to right under dir=rtl — same reading as the
            # sibling GM Message RTL token test.
            assert style["textAlign"] in ("right", "start"), (
                f"{name} text-align is {style['textAlign']!r}, expected right-aligned"
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

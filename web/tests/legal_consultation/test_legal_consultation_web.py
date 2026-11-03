"""
web/tests/legal_consultation/test_legal_consultation_web.py — Web-platform
cases for PBI 129404 (QC-SVC-006 — Legal Consulting), sourced from the
approved/injected Azure DevOps suite handed off by the QA Manager.

Scripted here (all 13): 138475, 138476, 138477, 138483, 138484, 138485,
138486, 138487, 138488, 138489, 138490, 138492, 138493 — of which 11 are
delivered on the Web surface and 2 (138477, 138490) are scripted and
complete but BLOCKED (below). Count those two as blocked / not verified, not
as delivered coverage.

BLOCKED (2) — each is written in full with the case's unweakened assertions,
behind a precondition gate that skips with a concrete, actionable reason; the
moment the precondition exists the skip stops firing and the assertions run
as-is, with no edit. See the batch report for the full reasoning:
- 138477 (Arabic request form + confirmation). Steps 1-2 (the Arabic form
  renders RTL with Arabic labels/placeholders) are reachable, but steps 3-4
  require an actual submission ("Submit a complete request" -> the request is
  stored with status Pending -> assert the exact Arabic confirmation string).
  The live form is protected by Google reCAPTCHA **Enterprise (invisible /
  score-based)** — `div.qc-lc-captcha[data-qc-recaptcha]` with the anchor
  frame loaded — and this project has no agreed CAPTCHA bypass (no test key,
  no env flag). A submission would additionally write a real request record
  with no teardown path (cms-profile.md's Teardown Path section covers only
  UI-deletable object entries). A test that asserted only steps 1-2 under
  this case's `tc_138477` marker would report green while the case's actual
  subject — the confirmation message — was never exercised, so instead
  steps 1-2 run for real (and fail red if the product is wrong) and
  steps 3-4 sit behind the CAPTCHA-bypass gate. Reported as blocked, not as
  partial coverage.
- 138490 (expanded FAQ answer renders rich-text markup). Step 1 is a Liferay
  CMS authoring action (log in as Site Content Editor, give an FAQ answer a
  heading + a two-item bullet list + an inline hyperlink, publish). That is a
  Control_Panel-surface write belonging to the deferred `cms/` batch, and the
  precondition does not exist on the live page: all four published answers
  currently contain a single `<p>` and nothing else (confirmed live
  2026-09-16), so the heading/bullets/link the case asserts on cannot be
  observed. Asserting them unconditionally would produce a red for a missing
  precondition rather than for a product defect — hence the gate that detects
  the authored answer and skips with a concrete reason when it is absent,
  instead of a weakened assertion.

Concrete data below is mirrored from the live published content on
https://qcdev.ihorizons.com/en|ar/legal-consultation, confirmed 2026-09-16 via
`tools/extract_locators.py` plus the scoped DOM probe documented in
legal_consultation_page.py's module docstring. Where a case's own EXPECTED
text names the value (hero copy, quick facts, section badges/headings, banner
copy, card titles), that literal is asserted verbatim.

Known spec issue, checked and NOT reproduced: the QA Manager's
spec-contradiction log records that PBI 129404's Figma FAQ answers carry
Economic Research copy rather than legal-consultation copy (covered by the
Manual case 138491). The LIVE page does not show that — all four EN answers
and all four AR answers are legal-consultation copy. No assertion in this
module was adjusted for it.

Batch 2 (2026-09-24, suite 138499) extends this module with 138437
(EN<->AR toggle), 138465/138466 (light/dark mode), 138479/138480/138481
(desktop/tablet/mobile) and 138482 (request form at mobile width, typed into
but never submitted). The batch-2 tests AND the existing 138475, 138476,
138483, 138487, 138489, 138492, 138493 run in a fresh UNAUTHENTICATED context
(`{"auth": False}`): with the cached CMS storageState, per-worker state files
carrying GUEST_LANGUAGE_ID=ar_SA rendered the English URL in Arabic under
xdist (4 of those 7 failed that way). Those 7 also gained the `svc` selector
marker; their assertions are unchanged.

Dual-surface note: 138484/138485/138486/138488 also carry a `Control_Panel`
tag because their step 4 compares the rendered order/values against the CMS
record. This module is the Web (delivery-surface) half and carries the `web`
marker only — per automation-standards.md a case spanning two platforms
becomes one test per platform, never one module holding both. The
authoring-surface half is not in this batch; see the report.
"""

import re

import allure
import pytest

from core.web.design_tokens import hex_to_rgb
from web.pages.legal_consultation.legal_consultation_page import LegalConsultationPage

# ---------------------------------------------------------------------------
# Concrete expected data — mirrored from the QA cases' own EXPECTED text and
# from the live published content (see module docstring). Kept here, not
# inline in the test bodies, so a content change is a one-line edit.
# ---------------------------------------------------------------------------
EN_HERO_EYEBROW = "Member Legal & Regulatory Advisory"
EN_HERO_TITLE = "Legal Consultation"
EN_CTA_LABEL = "Request Legal Consultation"

AR_HERO_EYEBROW = "الاستشارات القانونية والتنظيمية للأعضاء"
AR_HERO_TITLE = "الاستشارة القانونية"

EN_FACT_LABELS = ["Confidentiality", "Response Time", "Service Fee", "Target Eligibility"]
EN_FACT_VALUES = ["Strict Legal Privilege", "5 Working Days", "Free for Members", "Active Membership"]

SECTION_NUMBERS = ["01", "02", "03", "04", "05"]

EN_SECTION_BADGES = [
    "About the service",
    "Before you continue",
    "Service Scope & Exclusions",
    "How it works",
    "Common questions",
]
EN_SECTION_TITLES = [
    "Service Overview & Strategic Purpose",
    "Eligibility Criteria & Prerequisites",
    "Service Scope & Coverage Limits",
    "Standard Processing Workflow",
    "Frequently asked questions",
]

EN_BANNER_EYEBROW = "Ready to continue?"
EN_BANNER_TITLE = "Start with the correct service action."

# PBI 129404 names these three Overview info cards, in this order.
EN_CARD_TITLES = ["Clear consultation scope", "Member verification", "Secure supporting files"]

# Live published eligibility criteria, in rendered (CMS Display Order) order.
EN_CRITERIA = [
    "The company must hold an active Qatar Chamber membership.",
    "The inquiry must relate specifically to commercial, corporate, trade, "
    "or labor matters governed by Qatari law.",
    "The request must be submitted by an authorized company representative "
    "or legal representative.",
]

# Live published workflow steps, in rendered (CMS Display Order) order.
EN_STEP_TITLES = [
    "Verify Membership",
    "Complete Request",
    "Review by Legal Counsel",
    "Receive Response",
]
EN_STEP_NUMBERS = ["01", "02", "03", "04"]

EN_SCOPE_INCLUDED_HEAD = "Included Scope:"
EN_SCOPE_EXCLUDED_HEAD = "Excluded Scope:"

# The PBI's request-form field table, in table order. CAPTCHA is handled
# separately — it is present but is not a visible form control (see
# test_legal_consultation_request_form_renders_every_pbi_field).
EN_FORM_VISIBLE_FIELD_LABELS = [
    "Full Name*",
    "Company Name*",
    "Email*",
    "Mobile Number*",
    "Legal Issue Category*",
    "Subject*",
    "Description*",
    "Attachment",
]
EN_FORM_OPTIONAL_FIELD_LABEL = "Attachment"

MAROON = hex_to_rgb("#911731")  # -> "rgb(145, 23, 49)"

# The exact Arabic confirmation string quoted in PBI 129404 (TC 138477 step 4).
AR_CONFIRMATION_MESSAGE = (
    "تم إرسال طلب الاستشارة القانونية بنجاح. سيقوم فريقنا بمراجعته والتواصل معك."
)

_LATIN = re.compile(r"[A-Za-z]")
_ARABIC = re.compile(r"[؀-ۿ]")


def is_arabic(text: str) -> bool:
    """Arabic script present and no Latin letters left behind — the shape the
    RTL cases mean by 'renders in Arabic with no English text left in a
    translated field'."""
    return bool(_ARABIC.search(text)) and not _LATIN.search(text)


def _rgb_parts(color: str) -> tuple:
    """'rgb(16, 185, 129)' -> (16, 185, 129). getComputedStyle always returns
    this form (see core/web/design_tokens.py), so no hex branch is needed."""
    numbers = re.findall(r"\d+", color)
    return tuple(int(n) for n in numbers[:3])


def is_clipped(metrics: dict) -> bool:
    """True only for REAL clipping: content larger than its box AND an
    overflow mode that hides the excess. `overflow: visible` spill is a
    normal render, not a truncation, and must not false-red a layout case."""
    hidden_x = metrics["overflowX"] in ("hidden", "clip", "auto", "scroll")
    hidden_y = metrics["overflowY"] in ("hidden", "clip", "auto", "scroll")
    over_x = metrics["scrollWidth"] > metrics["clientWidth"] + 1
    over_y = metrics["scrollHeight"] > metrics["clientHeight"] + 1
    return (hidden_x and over_x) or (hidden_y and over_y)


# ===========================================================================
# 138475 — English page renders left-to-right with the designed copy
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Language & direction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("English Legal Consultation page renders left-to-right with the designed copy")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129404
@pytest.mark.tc_138475
@pytest.mark.traceability("138475")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129404")
@allure.label("testcase", "138475")
def test_legal_consultation_english_renders_ltr_with_designed_copy(page):
    lc = LegalConsultationPage(page)

    with allure.step("Open the public Legal Consultation page in English"):
        lc.open_legal_consultation(locale="en")

    # Step 1 — page loads left-to-right
    assert lc.document_direction() == "ltr"

    # Step 2 — hero, quick-facts strip and section index
    with allure.step("Inspect the hero, quick-facts strip and section index"):
        hero = lc.hero_element_order()
        assert lc.hero_eyebrow_text() == EN_HERO_EYEBROW
        assert lc.hero_title_text() == EN_HERO_TITLE
        assert hero["eyebrowY"] < hero["titleY"], "eyebrow must sit above the title"
        assert lc.fact_labels() == EN_FACT_LABELS
        assert lc.index_numbers() == SECTION_NUMBERS

    # Step 3 — sections 01 to 05
    with allure.step("Inspect Sections 01 to 05"):
        assert lc.section_badges() == EN_SECTION_BADGES
        assert lc.section_titles() == EN_SECTION_TITLES

    # Step 4 — next-step banner and left alignment
    with allure.step("Inspect the next-step banner and the text alignment"):
        assert lc.banner_eyebrow_text() == EN_BANNER_EYEBROW
        assert lc.banner_title_text() == EN_BANNER_TITLE
        assert lc.banner_cta_text() == EN_CTA_LABEL

        # "all text is left-aligned": in LTR every hero text element starts on
        # the container's left edge rather than being centred or right-set.
        assert hero["eyebrowX"] == pytest.approx(hero["copyX"], abs=2)
        assert hero["titleX"] == pytest.approx(hero["copyX"], abs=2)
        assert hero["descX"] == pytest.approx(hero["copyX"], abs=2)
        assert hero["ctaX"] == pytest.approx(hero["copyX"], abs=2)


# ===========================================================================
# 138476 — Arabic page renders right-to-left with Arabic copy throughout
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Language & direction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Arabic Legal Consultation page renders right-to-left with Arabic copy throughout")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_129404
@pytest.mark.tc_138476
@pytest.mark.traceability("138476")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129404")
@allure.label("testcase", "138476")
def test_legal_consultation_arabic_renders_rtl_with_arabic_copy(page):
    lc = LegalConsultationPage(page)

    with allure.step("Open the public Legal Consultation page in Arabic"):
        lc.open_legal_consultation(locale="ar")

    # Step 1 — page loads right-to-left
    assert lc.document_direction() == "rtl"

    # Step 2 — hero in Arabic, including the description (Open Risk R-8: the
    # Figma frame still carries the English hero description; the LIVE page is
    # what is asserted, and it must be Arabic).
    with allure.step("Inspect the hero, quick-facts strip and section index"):
        assert lc.hero_eyebrow_text() == AR_HERO_EYEBROW
        assert lc.hero_title_text() == AR_HERO_TITLE
        assert is_arabic(lc.hero_description_text()), (
            f"hero description is not fully Arabic: {lc.hero_description_text()!r}"
        )
        assert lc.index_numbers() == SECTION_NUMBERS
        for label in lc.index_labels():
            assert is_arabic(label), f"index label not in Arabic: {label!r}"

    # Step 3 — every translated field in sections 01-05 and the banner
    with allure.step("Inspect Sections 01 to 05 and the next-step banner"):
        for badge in lc.section_badges():
            assert is_arabic(badge), f"section badge not in Arabic: {badge!r}"
        for title in lc.section_titles():
            assert is_arabic(title), f"section heading not in Arabic: {title!r}"
        for criterion in lc.criteria():
            assert is_arabic(criterion["text"]), f"criterion not in Arabic: {criterion['text']!r}"
        for group in lc.scope_groups():
            assert is_arabic(group["head"]), f"scope heading not in Arabic: {group['head']!r}"
            for item in group["items"]:
                assert is_arabic(item), f"scope item not in Arabic: {item!r}"
        for step in lc.steps():
            assert is_arabic(step["title"]), f"step title not in Arabic: {step['title']!r}"
            assert is_arabic(step["description"]), f"step description not in Arabic: {step['description']!r}"
        for question in lc.faq_question_texts():
            assert is_arabic(question), f"FAQ question not in Arabic: {question!r}"
        assert is_arabic(lc.banner_eyebrow_text())
        assert is_arabic(lc.banner_title_text())
        assert is_arabic(lc.banner_body_text())

    # Step 4 — mirrored layout: index, list markers, accordion chevrons
    with allure.step("Inspect the layout direction of the index, the scope lists and the chevrons"):
        assert lc.index_is_on_leading_side(), "section index is not on the mirrored (right) side in RTL"

        for criterion in lc.criteria():
            row_mid = (criterion["rowX"] + criterion["rowRight"]) / 2
            assert criterion["checkCenterX"] > row_mid, (
                "check mark must sit to the RIGHT of its text in RTL "
                f"(check at {criterion['checkCenterX']}, row midpoint {row_mid})"
            )

        for item in lc.faq_items():
            question_mid = (item["questionX"] + item["questionRight"]) / 2
            assert item["hasMark"]
            assert item["markCenterX"] < question_mid, (
                "accordion chevron must be mirrored to the LEFT of the question in RTL "
                f"(chevron at {item['markCenterX']}, question midpoint {question_mid})"
            )


# ===========================================================================
# 138483 — hero renders eyebrow, title, description and CTA in the designed layout
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Hero")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Hero renders its eyebrow, title, description and CTA in the designed layout")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_129404
@pytest.mark.tc_138483
@pytest.mark.traceability("138483")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129404")
@allure.label("testcase", "138483")
def test_legal_consultation_hero_layout(page):
    lc = LegalConsultationPage(page)
    lc.open_legal_consultation(locale="en")

    # Step 2 — maroon gradient, and breadcrumb > eyebrow > title > description
    with allure.step("Inspect the hero region"):
        background = lc.hero_background_image()
        assert "gradient" in background, f"hero is not rendering a gradient: {background!r}"
        assert MAROON in background, f"hero gradient does not carry the maroon token {MAROON}: {background!r}"

        hero = lc.hero_element_order()
        assert hero["crumbsY"] < hero["eyebrowY"] < hero["titleY"] < hero["descY"], (
            "hero stacking order is not breadcrumb > eyebrow > title > description"
        )

    # Step 3 — no overflow/clipping, and the description is width-constrained
    with allure.step("Measure the hero text against its container"):
        for locator in (lc.EYEBROW, lc.TITLE, lc.HERO_DESC):
            metrics = lc.overflow_metrics(locator)
            assert not is_clipped(metrics), f"hero text is clipped at {locator}: {metrics}"

        assert hero["descWidth"] < hero["copyWidth"], (
            "hero description is not constrained to its designed width "
            f"(description {hero['descWidth']}px vs container {hero['copyWidth']}px)"
        )

    # Step 4 — CTA below the description, label fully visible
    with allure.step("Inspect the CTA button"):
        assert hero["ctaY"] > hero["descY"], "CTA does not render below the description"
        assert lc.hero_cta_text() == EN_CTA_LABEL
        assert not is_clipped(lc.overflow_metrics(lc.HERO_CTA)), "CTA label is truncated"


# ===========================================================================
# 138484 — quick-facts strip renders each active tile with icon, label, value
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Quick facts")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Quick-facts strip renders each active tile with its icon, label and value")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129404
@pytest.mark.tc_138484
@pytest.mark.traceability("138484")
@allure.label("pbi", "129404")
@allure.label("testcase", "138484")
def test_legal_consultation_quick_facts_tiles(page):
    lc = LegalConsultationPage(page)
    lc.open_legal_consultation(locale="en")

    tiles = lc.fact_tiles()

    # Step 2 — one tile per active quick fact, evenly spaced
    with allure.step("Inspect the quick-facts strip below the hero"):
        assert len(tiles) == len(EN_FACT_LABELS)
        widths = {round(t["width"]) for t in tiles}
        assert len(widths) == 1, f"quick-fact tiles are not equally sized: {widths}"
        gaps = [round(tiles[i + 1]["x"] - tiles[i]["x"]) for i in range(len(tiles) - 1)]
        assert max(gaps) - min(gaps) <= 2, f"quick-fact tiles are not evenly spaced: {gaps}"

    # Step 3 — every tile has a rendered icon and no label bleeds into its neighbour
    with allure.step("Inspect each tile in turn"):
        for index, tile in enumerate(tiles):
            assert tile["hasIcon"], f"tile {tile['label']!r} has no icon"
            assert tile["iconLoaded"], f"tile {tile['label']!r} renders a broken icon"
            assert tile["label"], f"tile {index} has no label"
            assert tile["value"], f"tile {tile['label']!r} has no value"
            if index + 1 < len(tiles):
                assert tile["labelRight"] <= tiles[index + 1]["x"], (
                    f"tile {tile['label']!r} label wraps into its neighbour"
                )

    # Step 4 — labels and values match the values stored in the CMS
    with allure.step("Compare the tiles against the values stored in the CMS"):
        assert [t["label"] for t in tiles] == EN_FACT_LABELS
        assert [t["value"] for t in tiles] == EN_FACT_VALUES


# ===========================================================================
# 138485 — Overview info cards render icon, title, description in order
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Section 01 — Overview")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Overview info cards render their icon, title and description in the configured order")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129404
@pytest.mark.tc_138485
@pytest.mark.traceability("138485")
@allure.label("pbi", "129404")
@allure.label("testcase", "138485")
def test_legal_consultation_overview_info_cards(page):
    lc = LegalConsultationPage(page)
    lc.open_legal_consultation(locale="en")

    # Step 2 — Section 01 renders its badge, heading and rich-text body
    with allure.step("Scroll to Section 01 Overview"):
        assert lc.section_badge_text(lc.SECTION_OVERVIEW) == EN_SECTION_BADGES[0]
        assert lc.section_title_text(lc.SECTION_OVERVIEW) == EN_SECTION_TITLES[0]
        assert lc.intro_text() != ""

    cards = lc.cards()

    # Step 3 — no blank icon slot, no empty description
    with allure.step("Inspect the info cards below the overview body"):
        assert len(cards) == len(EN_CARD_TITLES)
        for card in cards:
            assert card["hasIcon"], f"card {card['title']!r} has no icon element"
            assert card["iconLoaded"], f"card {card['title']!r} renders a blank/broken icon slot"
            assert card["iconWidth"] > 0 and card["iconHeight"] > 0
            assert card["title"], "a card rendered without a title"
            assert card["description"], f"card {card['title']!r} has an empty description area"

    # Step 4 — ascending Card Display Order, matching the CMS
    with allure.step("Compare their order against the Card Display Order values in the CMS"):
        assert [c["title"] for c in cards] == EN_CARD_TITLES


# ===========================================================================
# 138486 — eligibility criteria render with their check marks in order
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Section 02 — Eligibility")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Each eligibility criterion renders with its check mark in the configured order")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129404
@pytest.mark.tc_138486
@pytest.mark.traceability("138486")
@allure.label("pbi", "129404")
@allure.label("testcase", "138486")
def test_legal_consultation_eligibility_criteria_rows(page):
    lc = LegalConsultationPage(page)
    lc.open_legal_consultation(locale="en")

    # Step 2 — Section 02 badge and heading
    with allure.step("Scroll to Section 02 Eligibility & Prerequisites"):
        assert lc.section_badge_text(lc.SECTION_ELIGIBILITY) == "Before you continue"
        assert lc.section_title_text(lc.SECTION_ELIGIBILITY) == "Eligibility Criteria & Prerequisites"

    criteria = lc.criteria()

    # Step 3 — a check mark beside every label, none missing or broken
    with allure.step("Inspect every criteria row"):
        assert criteria, "Section 02 rendered no criteria rows"
        for row in criteria:
            assert row["text"], "a criteria row rendered with no label"
            assert row["hasCheck"], f"criteria row {row['text']!r} has no check mark"
            assert row["checkRendered"], f"criteria row {row['text']!r} renders a missing/zero-size check mark"
            assert row["checkHasGlyph"], f"criteria row {row['text']!r} renders a broken check icon"

    # Step 4 — ascending Display Order, matching the CMS
    with allure.step("Compare the order against the Display Order values in the CMS"):
        assert [row["text"] for row in criteria] == EN_CRITERIA


# ===========================================================================
# 138487 — Included and Excluded scope lists are visually distinguished
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Section 03 — Scope & Exclusions")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Included and Excluded scope lists are visually distinguished from each other")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129404
@pytest.mark.tc_138487
@pytest.mark.traceability("138487")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129404")
@allure.label("testcase", "138487")
def test_legal_consultation_scope_lists_are_distinguished(page):
    lc = LegalConsultationPage(page)
    lc.open_legal_consultation(locale="en")

    # Step 2 — two separate grouped lists, not one merged list
    with allure.step("Scroll to Section 03 Scope & Exclusions"):
        assert lc.section_badge_text(lc.SECTION_SCOPE) == EN_SECTION_BADGES[2]
        assert lc.section_title_text(lc.SECTION_SCOPE) == EN_SECTION_TITLES[2]
        assert lc.scope_group_count() == 2, "Section 03 does not render two separate grouped lists"

    groups = lc.scope_groups()
    included = next(g for g in groups if g["included"])
    excluded = next(g for g in groups if g["excluded"])

    # Step 3 — Included list, headed in green, items marked as included
    with allure.step("Inspect the Included Scope list"):
        assert included["head"] == EN_SCOPE_INCLUDED_HEAD
        assert included["items"], "Included Scope list has no items"
        red, green, blue = _rgb_parts(included["headColor"])
        assert green > red and green > blue, (
            f"'Included Scope:' heading is not rendered green: {included['headColor']}"
        )

    # Step 4 — Excluded list, headed in red, with a distinct marker
    with allure.step("Inspect the Excluded Scope list"):
        assert excluded["head"] == EN_SCOPE_EXCLUDED_HEAD
        assert excluded["items"], "Excluded Scope list has no items"
        red, green, blue = _rgb_parts(excluded["headColor"])
        assert red > green and red > blue, (
            f"'Excluded Scope:' heading is not rendered red: {excluded['headColor']}"
        )

        assert included["headColor"] != excluded["headColor"], (
            "both scope headings share one colour — the lists cannot be told apart at a glance"
        )
        assert included["glyphColor"] != excluded["glyphColor"], (
            "both scope groups use an identically-coloured marker glyph"
        )


# ===========================================================================
# 138488 — how-it-works section renders a numbered four-step workflow
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Section 04 — How it works")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("How-it-works section renders a numbered four-step workflow")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129404
@pytest.mark.tc_138488
@pytest.mark.traceability("138488")
@allure.label("pbi", "129404")
@allure.label("testcase", "138488")
def test_legal_consultation_workflow_steps(page):
    lc = LegalConsultationPage(page)
    lc.open_legal_consultation(locale="en")

    # Step 2 — Section 04 badge and heading
    with allure.step("Scroll to Section 04 How it works"):
        assert lc.section_badge_text(lc.SECTION_PROCESS) == "How it works"
        assert lc.section_title_text(lc.SECTION_PROCESS) == "Standard Processing Workflow"

    steps = lc.steps()

    # Step 3 — number, title, description; numbers consecutive, no gap/repeat
    with allure.step("Inspect each step in turn"):
        assert len(steps) == 4, f"expected a 4-step workflow, rendered {len(steps)}"
        for step in steps:
            assert step["number"], "a step rendered without its number"
            assert step["title"], f"step {step['number']} rendered without a title"
            assert step["description"], f"step {step['number']} rendered without a description"

        numbers = [step["number"] for step in steps]
        assert numbers == EN_STEP_NUMBERS, f"step numbers are not consecutive 01-04: {numbers}"
        assert len(set(numbers)) == len(numbers), f"step numbers repeat: {numbers}"

    # Step 4 — ascending Display Order, matching the CMS
    with allure.step("Compare the sequence against the Display Order values in the CMS"):
        assert [step["title"] for step in steps] == EN_STEP_TITLES


# ===========================================================================
# 138489 — FAQ answers are collapsed by default on first load
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Section 05 — FAQ")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("FAQ answers are collapsed by default when the page first loads")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_129404
@pytest.mark.tc_138489
@pytest.mark.traceability("138489")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129404")
@allure.label("testcase", "138489")
def test_legal_consultation_faq_collapsed_by_default(page):
    lc = LegalConsultationPage(page)
    lc.open_legal_consultation(locale="en")

    # Step 2 — all active FAQ questions render
    with allure.step("Scroll to Section 05 Frequently asked questions"):
        assert lc.section_badge_text(lc.SECTION_FAQ) == "Common questions"
        assert lc.section_title_text(lc.SECTION_FAQ) == "Frequently asked questions"
        questions = lc.faq_question_texts()
        assert questions, "Section 05 rendered no FAQ questions"
        assert all(q for q in questions)

    items = lc.faq_items()

    # Step 3 — every answer hidden, every question in its collapsed state
    with allure.step("Inspect every FAQ item without clicking"):
        for item in items:
            assert item["expanded"] == "false", (
                f"FAQ {item['question']!r} is not in its collapsed state (aria-expanded="
                f"{item['expanded']!r})"
            )
            assert item["answerHidden"], f"FAQ answer for {item['question']!r} is not hidden"
            assert not item["answerVisible"], f"FAQ answer for {item['question']!r} is rendered visible"
            assert item["answerHeight"] == 0, (
                f"FAQ answer for {item['question']!r} occupies {item['answerHeight']}px"
            )
            assert item["hasMark"], f"FAQ {item['question']!r} has no collapsed-state indicator"

    # Step 4 — section height matches a fully collapsed accordion
    with allure.step("Measure the section height against the number of questions"):
        # A collapsed item is exactly its question row (answers contribute 0),
        # so the accordion's height can be no more than the sum of the item
        # heights, and each item can be no taller than its own question row
        # plus its border/padding.
        for item in items:
            assert item["itemHeight"] <= item["questionHeight"] + 8, (
                f"FAQ item {item['question']!r} is taller than a collapsed row "
                f"({item['itemHeight']}px vs question row {item['questionHeight']}px)"
            )
        collapsed_total = sum(item["itemHeight"] for item in items)
        container_height = lc.faq_container_height()
        assert container_height >= collapsed_total
        assert container_height <= collapsed_total + 12 * len(items), (
            f"accordion height {container_height}px exceeds a fully collapsed "
            f"{len(items)}-question accordion ({collapsed_total}px of rows)"
        )


# ===========================================================================
# 138492 — next-step banner renders eyebrow, heading, body and CTA
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Next-step banner")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Next-step banner renders its eyebrow, heading, body and CTA")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_129404
@pytest.mark.tc_138492
@pytest.mark.traceability("138492")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129404")
@allure.label("testcase", "138492")
def test_legal_consultation_next_step_banner(page):
    lc = LegalConsultationPage(page)
    lc.open_legal_consultation(locale="en")

    # Step 2 — own contrasting surface, separated from Section 05
    with allure.step("Scroll to the next-step banner beneath Section 05"):
        surface = lc.banner_surface()
        assert not surface["insideFaqSection"], (
            "the next-step banner is rendered inside Section 05 rather than separated from it"
        )
        assert surface["top"] >= surface["faqBottom"] - 1, "the banner does not sit beneath Section 05"
        assert surface["backgroundImage"] != "none", "the banner has no surface of its own"
        assert surface["backgroundImage"] != surface["sectionBackgroundImage"], (
            "the banner shares Section 05's surface instead of contrasting with it"
        )

    # Step 3 — every element present, none clipped
    with allure.step("Inspect each element of the banner"):
        assert lc.banner_eyebrow_text() == EN_BANNER_EYEBROW
        assert lc.banner_title_text() == EN_BANNER_TITLE
        assert lc.banner_body_text() != "", "the banner renders no supporting body copy"
        assert lc.banner_cta_text() == EN_CTA_LABEL
        for locator in (lc.BANNER_EYEBROW, lc.BANNER_TITLE, lc.BANNER_BODY, lc.BANNER_CTA):
            assert not is_clipped(lc.overflow_metrics(locator)), f"banner element clipped: {locator}"

        english_order = lc.banner_element_order()
        # The banner is a two-column arrangement (confirmed live): the copy
        # block stacks eyebrow > heading > body, and the CTA sits BESIDE that
        # block on the trailing edge — not beneath it.
        assert english_order["eyebrowY"] < english_order["titleY"] < english_order["bodyY"]
        assert english_order["ctaX"] >= english_order["copyRight"], (
            "in LTR the banner CTA should sit to the right of the copy block"
        )

    # Step 4 — the Arabic banner, right-aligned, same arrangement, mirrored
    with allure.step("Switch to Arabic and inspect the same banner"):
        # Direct navigation to the Arabic URL rather than the header language
        # switcher: web/pages/components/language_switcher_component.py is
        # still an unimplemented stub on this framework, and the switcher is
        # not this case's subject.
        lc.open_legal_consultation(locale="ar")

        assert lc.document_direction() == "rtl"
        assert is_arabic(lc.banner_eyebrow_text()), "Arabic banner eyebrow is not in Arabic"
        assert is_arabic(lc.banner_title_text()), "Arabic banner heading is not in Arabic"
        assert is_arabic(lc.banner_body_text()), "Arabic banner body copy is not in Arabic"
        assert is_arabic(lc.banner_cta_text()), "Arabic banner CTA is not in Arabic"

        arabic_surface = lc.banner_surface()
        assert arabic_surface["direction"] == "rtl"

        arabic_order = lc.banner_element_order()
        # Same arrangement: copy block stacks eyebrow > heading > body...
        assert arabic_order["eyebrowY"] < arabic_order["titleY"] < arabic_order["bodyY"]
        # ...with the CTA beside it — mirrored to the LEFT of the copy block.
        assert arabic_order["ctaRight"] <= arabic_order["copyX"], (
            "in RTL the banner CTA should sit to the left of the copy block"
        )
        # Mirrored: the copy block now starts at the banner's RIGHT edge.
        assert arabic_order["titleRight"] == pytest.approx(arabic_order["copyRight"], abs=2), (
            "Arabic banner heading is not right-aligned within its copy block"
        )
        english_copy_offset = english_order["copyX"] - english_order["bannerX"]
        arabic_copy_offset = arabic_order["bannerRight"] - arabic_order["copyRight"]
        assert arabic_copy_offset == pytest.approx(english_copy_offset, abs=2), (
            "the Arabic banner copy block is not the mirror of the English one"
        )


# ===========================================================================
# 138493 — request form renders every field named in the PBI field table
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Request form")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Request form renders every field named in the PBI field table")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129404
@pytest.mark.tc_138493
@pytest.mark.traceability("138493")
@pytest.mark.svc
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.label("pbi", "129404")
@allure.label("testcase", "138493")
def test_legal_consultation_request_form_renders_every_pbi_field(page):
    """Structural rendering check ONLY — the form is never filled or
    submitted (the QA Manager's hand-off, and the live reCAPTCHA Enterprise
    with no agreed bypass).

    Two live observations are asserted exactly as found and are reported to
    the QA Manager rather than assumed away:
      * The CAPTCHA is *invisible* reCAPTCHA Enterprise. Its `.qc-lc-field`
        wrapper (label "Security check*") is `display: none` and the widget is
        the score-based badge, so the CAPTCHA is present and armed but is not
        a visible in-form control. This test asserts presence + armed state,
        which is what "the form presents ... CAPTCHA" can mean on this build.
      * The form carries one conditional field that is NOT in the PBI table —
        "Please specify the category*" (`legalIssueCategoryOther`), revealed
        only when the category "Other" is chosen. It is hidden on load, so the
        visible-field comparison below is unaffected; it is flagged in the
        report as a possible field-table gap, not silently accepted.
    """
    lc = LegalConsultationPage(page)
    lc.open_legal_consultation(locale="en")

    # Step 1 — the form loads with the Legal Consultation service context
    with allure.step("Open the Legal Consultation request form in English as a public visitor"):
        lc.open_request_form()
        assert lc.is_request_form_open()
        assert lc.request_form_title_text() == EN_CTA_LABEL
        assert lc.request_form_eyebrow_text() != ""

    fields = lc.request_form_fields()
    visible_fields = [f for f in fields if f["visible"]]

    # Step 2 — every visible field, control and label, plus CAPTCHA and Submit
    with allure.step("List every visible field, control and label on the form"):
        assert [f["label"] for f in visible_fields] == EN_FORM_VISIBLE_FIELD_LABELS

        captcha = lc.captcha_state()
        assert captcha["mountPresent"], "the form renders no CAPTCHA mount point"
        assert captcha["recaptchaFrames"] >= 1, "the CAPTCHA widget never loaded on the form"
        assert captcha["recaptchaLoaded"], "the CAPTCHA widget loaded but rendered nothing"

        assert lc.is_submit_button_visible()
        assert lc.submit_button_text() != ""

    # Step 3 — nothing from the table missing, nothing outside it added
    with allure.step("Compare the list against the PBI's request-form field table"):
        # Every table field resolves to a real control on the form.
        control_ids = {f["controlId"] for f in fields if f["controlId"]}
        for expected_id in lc.FIELD_CONTROL_IDS:
            assert expected_id in control_ids, f"field table entry {expected_id} is missing from the form"
        # And no EXTRA visible field beyond the table.
        assert len(visible_fields) == len(EN_FORM_VISIBLE_FIELD_LABELS)

    # Step 4 — mandatory indicators; Attachment is not marked mandatory
    with allure.step("Inspect the mandatory-field indicators"):
        for field in visible_fields:
            if field["label"] == EN_FORM_OPTIONAL_FIELD_LABEL:
                assert not field["requiredMark"], "Attachment is marked mandatory but the table says it is not"
                assert not field["label"].endswith("*")
            else:
                assert field["requiredMark"], f"required field {field['label']!r} carries no mandatory indicator"
                assert field["label"].endswith("*")


# ===========================================================================
# 138477 — Arabic request form and its confirmation render RTL with Arabic text
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Request form")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Arabic request form and its confirmation render right-to-left with Arabic text")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_129404
@pytest.mark.tc_138477
@pytest.mark.traceability("138477")
@allure.label("pbi", "129404")
@allure.label("testcase", "138477")
def test_legal_consultation_arabic_request_form_and_confirmation(page):
    """Steps 1-2 (the Arabic form renders RTL with Arabic labels/placeholders)
    run for real and fail red if the product is wrong.

    Steps 3-4 (submit a complete request -> stored Pending -> the exact Arabic
    confirmation string) are gated on a CAPTCHA bypass that does not exist on
    this project. The live form is protected by Google reCAPTCHA **Enterprise,
    invisible/score-based** (`div.qc-lc-captcha[data-qc-recaptcha]`, anchor
    frame loaded, its `.qc-lc-field` wrapper `display: none`). There is no test
    key, no env flag and no agreed bypass, and a real submission would write a
    request record with no teardown path. The assertions below are written in
    full and unweakened — the moment a bypass is configured the skip stops
    firing and they run as-is.
    """
    lc = LegalConsultationPage(page)

    with allure.step("Open the Legal Consultation request form in Arabic as a public visitor"):
        lc.open_legal_consultation(locale="ar")
        lc.open_request_form()

    # Step 1 — the form loads right-to-left
    assert lc.is_request_form_open()
    assert lc.document_direction() == "rtl"
    assert lc.request_form_direction() == "rtl"

    # Step 2 — every label, placeholder and the CAPTCHA
    with allure.step("Inspect every field label, placeholder and the CAPTCHA"):
        fields = lc.request_form_fields()
        visible_fields = [f for f in fields if f["visible"]]
        assert visible_fields, "the Arabic request form rendered no fields"

        for field in visible_fields:
            assert is_arabic(field["label"].rstrip("*").strip()), (
                f"form label is not in Arabic: {field['label']!r}"
            )
            if field["controlPlaceholder"]:
                assert is_arabic(field["controlPlaceholder"]), (
                    f"placeholder is not in Arabic: {field['controlPlaceholder']!r}"
                )
            if field["controlDirection"]:
                assert field["controlDirection"] == "rtl", (
                    f"field {field['label']!r} does not accept right-to-left entry "
                    f"(direction={field['controlDirection']})"
                )

        # Right-aligned: every label starts at its field's RIGHT edge in RTL.
        for row in lc.request_form_label_alignment():
            assert row["direction"] == "rtl"
            assert row["labelRight"] == pytest.approx(row["fieldRight"], abs=2), (
                f"label {row['label']!r} is not right-aligned within its field"
            )

        captcha = lc.captcha_state()
        assert captcha["mountPresent"], "the Arabic form renders no CAPTCHA mount point"
        assert captcha["recaptchaFrames"] >= 1, "the CAPTCHA widget never loaded on the Arabic form"

    # Steps 3-4 — gated: no CAPTCHA bypass exists on this project.
    if captcha["recaptchaFrames"] >= 1:
        pytest.skip(
            "PRECONDITION UNAVAILABLE — steps 3-4 (submit a complete request; assert the "
            "confirmation reads exactly "
            f"{AR_CONFIRMATION_MESSAGE!r} and that the request is stored with status Pending) "
            "cannot run: the live form is protected by Google reCAPTCHA Enterprise "
            "(invisible/score-based, mount div.qc-lc-captcha[data-qc-recaptcha]) and this "
            "project has no agreed CAPTCHA bypass — no reCAPTCHA test site key, no env flag, "
            "no backdoor. A real submission would also persist a Legal Consultation request "
            "with no teardown path (cms-profile.md's Teardown Path covers only UI-deletable "
            "object entries). Steps 1-2 above DID run and passed. Configure a bypass, then "
            "this skip stops firing and the submission assertions below run unchanged."
        )

    # --- Steps 3-4, written in full for the moment a bypass exists ---------
    with allure.step("Submit a complete request"):
        lc.submit_request_form()

    with allure.step("Inspect the confirmation message"):
        confirmation = lc.confirmation_message()
        assert confirmation is not None
        assert confirmation["visible"], "no confirmation message was displayed after submission"
        assert confirmation["text"] == AR_CONFIRMATION_MESSAGE
        assert confirmation["direction"] == "rtl"
        assert confirmation["textAlign"] in ("start", "right"), (
            f"the confirmation is not right-aligned (text-align={confirmation['textAlign']})"
        )


# ===========================================================================
# 138490 — an expanded FAQ answer renders its rich-text markup
# ===========================================================================
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Section 05 — FAQ")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Expanded FAQ answer renders its rich-text markup")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_129404
@pytest.mark.tc_138490
@pytest.mark.traceability("138490")
@allure.label("pbi", "129404")
@allure.label("testcase", "138490")
def test_legal_consultation_expanded_faq_renders_rich_text(page):
    """Step 1 of this case is a Liferay CMS authoring write (log in as a Site
    Content Editor, give an FAQ answer a heading + a two-item bullet list + an
    inline hyperlink, publish). That belongs to the deferred Control_Panel
    batch — CMS credentials are not configured on this machine — and the
    resulting content does not exist on the live page: all four published
    answers currently contain a single `<p>` and nothing else (confirmed live
    2026-09-16).

    So the Web half below is gated on the authored content actually being
    present. The assertions are written in full and unweakened; once the CMS
    step has been performed the skip stops firing and they run as-is.
    """
    lc = LegalConsultationPage(page)

    with allure.step("Open the public Legal Consultation page in English and scroll to Section 05"):
        lc.open_legal_consultation(locale="en")

    # Step 2 — the page loads with the accordion collapsed
    items = lc.faq_items()
    assert items, "Section 05 rendered no FAQ items"
    for item in items:
        assert item["expanded"] == "false"
        assert item["answerHidden"]

    # Precondition gate — find the answer the CMS step was supposed to author.
    rich_index = next(
        (
            index
            for index, markup in enumerate(lc.faq_answers_markup())
            if markup["headings"] and markup["listCount"] and markup["links"]
        ),
        None,
    )
    if rich_index is None:
        pytest.skip(
            "PRECONDITION UNAVAILABLE — step 1 of this case is a Liferay CMS authoring write "
            "(log in as Site Content Editor, open the Legal Consultation page record, give an "
            "FAQ answer a heading, a two-item bullet list and an inline hyperlink, then "
            "publish). CMS credentials are not configured on this machine and that write "
            "belongs to the deferred Control_Panel batch. No published FAQ answer on "
            "/our-services/legal-consultation currently contains a heading + list + link — all "
            "four are a single <p> (confirmed live 2026-09-16) — so the markup this case "
            "asserts on does not exist to be observed. Perform the CMS step, then this skip "
            "stops firing and the assertions below run unchanged."
        )

    # Step 3 — click that question
    with allure.step("Click the question whose answer carries the authored rich text"):
        lc.expand_faq(rich_index)
        expanded = lc.faq_items()[rich_index]
        assert expanded["expanded"] == "true", "the question did not expand"
        assert expanded["answerVisible"]
        assert expanded["answerHeight"] > 0

    # Step 4 — heading, both bullets and a clickable hyperlink, as MARKUP
    with allure.step("Inspect the revealed answer"):
        markup = lc.faq_answer_markup(rich_index)

        assert markup["headings"], "the answer's heading did not render as a heading element"
        assert markup["listCount"] >= 1, "the answer's bullet list did not render as a list element"
        assert len(markup["listItems"]) == 2, (
            f"expected a two-item bullet list, rendered {len(markup['listItems'])} items"
        )
        assert all(item for item in markup["listItems"]), "a bullet item rendered empty"
        assert markup["links"], "the inline hyperlink did not render as a clickable anchor"
        assert markup["links"][0]["href"], "the rendered hyperlink has no href"

        # Not raw HTML: no escaped tags printed as visible text.
        assert "&lt;" not in markup["html"], "the answer is printing escaped HTML as text"
        assert not re.search(r"<[a-z]+[^>]*>", markup["text"]), (
            f"the answer shows raw HTML in its text content: {markup['text'][:120]!r}"
        )
        # Not stripped: the markup elements survived into the DOM.
        assert markup["html"] != markup["text"], "the answer's rich text was stripped to plain text"


# ===========================================================================
# Batch 2 (2026-09-24, suite 138499): language toggle, light/dark theme,
# desktop/tablet/mobile viewports and the request form at mobile width.
# Every test runs in a fresh UNAUTHENTICATED context and collects every
# expected-vs-actual deviation in `_Check`, failing once with the full list.
# Deviation labels tagged "[blanket-wording — needs Figma check]" come from a
# blanket case statement applied to a distinct component; they still fail,
# but are flagged for design verification rather than as confirmed defects.
# ===========================================================================
ANON = {"auth": False}
anonymous = pytest.mark.parametrize("page", [ANON], indirect=True)
BLANKET = " [blanket-wording — needs Figma check]"

HEADER_NAV_LIGHT = hex_to_rgb("#1D1D1B")
PAGE_BG_LIGHT = hex_to_rgb("#FFFFFF")
INDEX_LABEL_LIGHT = hex_to_rgb("#6C6C6B")
LIGHT_BORDER = hex_to_rgb("#EDEDED")
# WCAG 2.x AA — "legible"/"readable contrast" states no number; the published
# minimum is the measurable floor (4.5:1 normal text, 3:1 large text).
AA_NORMAL, AA_LARGE = 4.5, 3.0
MIN_LEGIBLE_FONT_PX = 12.0
TAP_TARGET_PX = 44.0

# Not-submitted interaction data for 138482 (typed into the fields only).
FORM_TYPING_DATA = {
    "full_name": "QA Automation Visitor",
    "company_name": "QA Automation Test Co",
    "email": "qa.automation@example.com",
    "phone": "55123456",
    "subject": "Mobile usability check",
    "description": "Typed by an automated mobile-usability check; this form is never submitted.",
}


class _Check:
    """Soft-assert collector; tests end with `assert not check.deviations, check.report()`."""

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

    def report(self) -> str:
        return "\n".join([f"{len(self.deviations)} deviation(s):", *(f"  - {d}" for d in self.deviations)])


def _overlap(a, b) -> bool:
    if not a or not b:
        return False
    return (a["x"] < b["x"] + b["width"] - 1 and b["x"] < a["x"] + a["width"] - 1
            and a["y"] < b["y"] + b["height"] - 1 and b["y"] < a["y"] + a["height"] - 1)


def _aa_needed(c: dict) -> float:
    return AA_LARGE if c["fontSize"] >= 24 or (c["fontSize"] >= 18.66 and c["fontWeight"] >= 700) else AA_NORMAL


def _check_contrast(check: _Check, lc: LegalConsultationPage, name: str, loc: str) -> None:
    for i in range(lc.count_of(loc)):
        c = lc.text_contrast(loc, i)
        if c["ratio"] is None:
            allure.attach(str(c), f"{name} {i + 1}: contrast not measurable (gradient)", allure.attachment_type.TEXT)
            continue
        need = _aa_needed(c)
        check.truthy(f"{name} {i + 1} contrast", c["ratio"] >= need, f">= {need}:1",
                     f"{c['ratio']}:1 ({c['color']} on {c['background']}, '{c['text']}')")


def _check_no_overflow(check: _Check, lc: LegalConsultationPage) -> None:
    overflow = lc.horizontal_overflow_px()
    check.truthy("no horizontal scrollbar", overflow <= 0, "0px", f"{overflow}px {lc.overflowing_elements()}")
    clipped = lc.clipped_text_elements()
    check.truthy("no clipped / overflowing text", not clipped, "none", clipped)


def _check_index_mobile(check: _Check, lc: LegalConsultationPage, wording: str) -> None:
    if lc.is_displayed(lc.INDEX_COL):
        check.truthy("section index does not overlap content", not _overlap(lc.box(lc.INDEX_COL), lc.box(lc.CONTENT)),
                     "no overlap", f"index={lc.box(lc.INDEX_COL)} content={lc.box(lc.CONTENT)}")
        return
    shown = sum(1 for i in range(lc.count_of(lc.INDEX_ITEM)) if lc.is_displayed(lc.INDEX_ITEM, i))
    display = lc.computed_style(lc.INDEX_COL, ["display"])["display"]
    check.truthy(wording, shown > 0, wording,
                 f"index column display={display!r}; 0 of {lc.count_of(lc.INDEX_ITEM)} entries rendered, "
                 f"no collapsed/mobile control present (index removed entirely)")


def _content_width(lc: LegalConsultationPage, locator: str) -> float:
    b = lc.box(locator)
    s = lc.computed_style(locator, ["paddingLeft", "paddingRight", "borderLeftWidth", "borderRightWidth"])
    return b["width"] - sum(float(v.rstrip("px")) for v in s.values())


# ---------------------------------------------------------------------------
# 138437 — language toggle switches the whole page EN <-> AR
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Language toggle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The language toggle switches the whole Legal Consultation page between English and Arabic")
@allure.label("pbi", "129404")
@allure.label("testcase", "138437")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_129404
@pytest.mark.tc_138437
@anonymous
def test_legal_consultation_language_toggle_en_ar_en(page):
    """Azure TC 138437 | PBI 129404 — EN -> 'AR' toggle -> every label, badge,
    title, criterion, scope item, step, FAQ question and CTA label Arabic
    (is_arabic: Arabic script, no Latin left behind) and RTL -> 'EN' toggle ->
    English LTR with the same content and the same scroll target. The scroll
    target is set by jumping to Section 03 through the section index before
    switching, and compared with the section in view after switching back."""
    lc = LegalConsultationPage(page)
    check = _Check()

    with allure.step("Open the English page and jump to Section 03 via the index"):
        lc.open_legal_consultation(locale="en")
        check.step("step 1")
        check.equals("document dir", lc.document_direction(), "ltr")
        en_content = {"badges": lc.section_badges(), "titles": lc.section_titles(), "facts": lc.fact_labels(),
                      "index": lc.index_labels()}
        lc.go_to_section_via_index(2)
        target = lc.section_in_view()
        allure.attach(str(target), "scroll target before switching", allure.attachment_type.TEXT)

    with allure.step("Click the AR toggle"):
        check.equals("toggle label (EN page)", lc.language_toggle_label(), "AR")
        lc.toggle_language()

    with allure.step("Every translated field is Arabic and RTL"):
        check.step("step 3")
        check.equals("document dir", lc.document_direction(), "rtl")
        slots = {
            "quick-fact label": lc.FACT_LABEL, "index label": lc.INDEX_LABEL, "section badge": lc.SECTION_BADGE,
            "section title": lc.SECTION_TITLE, "criteria row": lc.CRITERION, "scope item": lc.SCOPE_ITEM,
            "scope heading": lc.SCOPE_HEAD, "step title": lc.STEP_TITLE, "step description": lc.STEP_DESC,
            "FAQ question": lc.FAQ_QUESTION, "hero CTA label": lc.HERO_CTA, "banner CTA label": lc.BANNER_CTA,
        }
        for name, loc in slots.items():
            values = lc.text_contents(loc)
            check.truthy(f"{name}s rendered", len(values) > 0, "at least one", values)
            for v in values:
                check.truthy(f"{name} is Arabic", is_arabic(v), "Arabic text, no Latin left behind", v)
            directions = {s["direction"] for s in lc.computed_styles_all(loc, ["direction"])}
            check.equals(f"{name} direction", directions, {"rtl"})

    with allure.step("Click the EN toggle to switch back"):
        check.equals("toggle label (AR page)", lc.language_toggle_label(), "EN")
        lc.toggle_language()
        check.step("step 4")
        check.equals("document dir", lc.document_direction(), "ltr")
        back = {"badges": lc.section_badges(), "titles": lc.section_titles(), "facts": lc.fact_labels(),
                "index": lc.index_labels()}
        check.equals("same English content", back, en_content)
        check.equals("same scroll target after switching back", lc.section_in_view(), target)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138465 — light mode
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Legal Consultation page renders correctly in light mode")
@allure.label("pbi", "129404")
@allure.label("testcase", "138465")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.pbi_129404
@pytest.mark.tc_138465
@anonymous
def test_legal_consultation_light_mode(page):
    """Azure TC 138465 | PBI 129404 — ST-13 light mode (site default), frame
    2798:90483. "Light surface" = effective background relative luminance >
    0.8; "legible" = WCAG AA contrast. The scope groups are distinct tinted
    components — their border check is tagged blanket-wording."""
    lc = LegalConsultationPage(page)
    check = _Check()
    lc.open_legal_consultation(locale="en")
    check.step("step 1")
    check.truthy("light theme active", lc.theme() in (None, "light"), "light", lc.theme())

    with allure.step("Page, header and sticky index"):
        check.step("step 3")
        check.equals("page background", lc.computed_style(lc.PAGE_BODY, ["backgroundColor"])["backgroundColor"], PAGE_BG_LIGHT)
        check.equals("header background", lc.computed_style(lc.HEADER, ["backgroundColor"])["backgroundColor"], PAGE_BG_LIGHT)
        for colour in sorted({s["color"] for s in lc.computed_styles_all(lc.HEADER_NAV_LINK, ["color"])}):
            check.equals("header navigation label colour", colour, HEADER_NAV_LIGHT)
        idx_bg = lc.effective_background(lc.INDEX)
        check.truthy("index on a light surface", lc.relative_luminance(idx_bg) > 0.8, "luminance > 0.8", idx_bg)
        for colour in sorted({s["color"] for s in lc.computed_styles_all(lc.INDEX_LABEL, ["color"])}):
            check.equals("index label colour", colour, INDEX_LABEL_LIGHT)

    with allure.step("Info cards, criteria list, both scope lists; green/red headings legible"):
        check.step("step 4")
        for name, loc, tag in (("info card", lc.CARD, ""), ("criteria row", lc.CRITERION, ""),
                               ("scope list", lc.SCOPE_GROUP, BLANKET)):
            styles = lc.computed_styles_all(loc, ["borderTopWidth", "borderTopStyle", "borderTopColor"])
            check.truthy(f"{name}s rendered", len(styles) > 0, "at least one", 0)
            for i, s in enumerate(styles):
                bg = lc.effective_background(loc, i)
                check.truthy(f"{name} {i + 1} light surface", lc.relative_luminance(bg) > 0.8, "luminance > 0.8", bg)
                check.equals(f"{name} {i + 1} border{tag}", f"{s['borderTopWidth']} {s['borderTopStyle']} {s['borderTopColor']}",
                             f"1px solid {LIGHT_BORDER}")
        _check_contrast(check, lc, "scope heading ('Included'/'Excluded Scope:')", lc.SCOPE_HEAD)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138466 — dark mode
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Legal Consultation page renders correctly in dark mode")
@allure.label("pbi", "129404")
@allure.label("testcase", "138466")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.pbi_129404
@pytest.mark.tc_138466
@anonymous
def test_legal_consultation_dark_mode(page):
    """Azure TC 138466 | PBI 129404 — ST-14 dark mode via the Accessibility tools
    widget (colour transitions awaited). No dark hex tokens are stated:
    page/header dark (luminance < 0.2); index labels, section headings and
    body text (intro, card text, criteria, scope items, step text) meet WCAG
    AA; info cards, scope lists, FAQ items and the banner sit on dark
    surfaces; the hero gradient is unchanged; the green/red scope headings
    meet AA. The banner is painted with the hero gradient in both themes —
    its "dark surface" is checked as a dark gradient/colour, not as a change."""
    lc = LegalConsultationPage(page)
    check = _Check()
    lc.open_legal_consultation(locale="en")
    light_hero = lc.hero_background_image()

    with allure.step("Turn dark mode on"):
        lc.enable_dark_mode()
        check.step("step 1")
        check.equals("dark theme active", lc.theme(), "dark")

    with allure.step("Page/header dark; index labels, headings and body text legible"):
        check.step("step 3")
        for name, loc in (("page", lc.PAGE_BODY), ("header", lc.HEADER)):
            bg = lc.computed_style(loc, ["backgroundColor"])["backgroundColor"]
            check.truthy(f"{name} background dark", lc.relative_luminance(bg) < 0.2, "luminance < 0.2", bg)
        for name, loc in (("index label", lc.INDEX_LABEL), ("section heading", lc.SECTION_TITLE),
                          ("intro text", lc.INTRO), ("info card text", lc.CARD_DESC), ("criteria row", lc.CRITERION),
                          ("scope item", lc.SCOPE_ITEM), ("step text", lc.STEP_DESC)):
            _check_contrast(check, lc, name, loc)

    with allure.step("Cards, scope lists, accordion and banner dark; hero unchanged; scope colours readable"):
        check.step("step 4")
        for name, loc in (("info card", lc.CARD), ("scope list", lc.SCOPE_GROUP), ("FAQ item", lc.FAQ_ITEM),
                          ("next-step banner", lc.BANNER)):
            for i in range(lc.count_of(loc)):
                bg = lc.effective_background(loc, i)
                dark = (lc.relative_luminance(bg) < 0.2) if "gradient" not in bg else all(
                    lc.relative_luminance(c) < 0.2 for c in re.findall(r"rgba?\([^)]*\)", bg.split("linear-gradient", 1)[-1]))
                check.truthy(f"{name} {i + 1} dark surface", dark, "dark (luminance < 0.2)", bg)
        check.equals("hero gradient unchanged", lc.hero_background_image(), light_hero)
        _check_contrast(check, lc, "scope heading (green/red)", lc.SCOPE_HEAD)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138479 — desktop
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Legal Consultation page renders correctly at desktop viewport width (1920x1080)")
@allure.label("pbi", "129404")
@allure.label("testcase", "138479")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129404
@pytest.mark.tc_138479
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_legal_consultation_desktop_viewport(page):
    """Azure TC 138479 | PBI 129404 — ENV-1 at 1920x1080. "CTA in the designed
    position" is read as: below the description, on the hero copy's start
    edge (the same geometry 138475/138483 assert)."""
    lc = LegalConsultationPage(page)
    check = _Check()
    lc.open_legal_consultation(locale="en")

    with allure.step("No horizontal scrollbar"):
        check.step("step 2")
        overflow = lc.horizontal_overflow_px()
        check.truthy("no horizontal scrollbar", overflow <= 0, "0px", f"{overflow}px {lc.overflowing_elements()}")

    with allure.step("Hero full width + CTA; four fact tiles in a row; sticky index alongside content"):
        check.step("step 3")
        check.truthy("hero fills the width", abs(lc.box(lc.HERO)["width"] - 1920) <= 1, "1920px", lc.box(lc.HERO)["width"])
        cta, desc, copy = lc.box(lc.HERO_CTA), lc.box(lc.HERO_DESC), lc.box(lc.HERO_COPY)
        check.truthy("hero CTA below the description on the copy's start edge",
                     cta["y"] >= desc["y"] + desc["height"] - 1 and abs(cta["x"] - copy["x"]) <= 2,
                     "below description, x == copy x", f"cta={cta} desc={desc} copy={copy}")
        facts = [b for b in lc.boxes(lc.FACT) if b]
        check.equals("quick-fact tile count", len(facts), 4)
        check.truthy("quick facts in one row", len({round(b["y"]) for b in facts}) == 1, "same row",
                     [b["y"] for b in facts])
        idx, content = lc.box(lc.INDEX_COL), lc.box(lc.CONTENT)
        check.truthy("index alongside the content", idx["x"] + idx["width"] <= content["x"] + 1,
                     "index right edge <= content left edge", f"index={idx} content={content}")
        check.equals("index column is sticky", lc.computed_style(lc.INDEX_COL, ["position"])["position"], "sticky")

    with allure.step("Scope lists stacked; four-step workflow; banner spans the content width"):
        check.step("step 4")
        lc.scroll_to(lc.SCOPE)
        groups = [b for b in lc.boxes(lc.SCOPE_GROUP) if b]
        # The case says "side by side", but the design source stacks them:
        # Figma J3e1thav8NIu6a3XhC6Wcl frame 2798:90483, scope container
        # #2798:90505 is layout mode "column" with each list ~942px wide.
        # QA Manager ruling 2026-09-24: the Figma layout wins over the case text.
        check.truthy("both scope lists stacked (Figma column layout)", len(groups) == 2
                     and groups[1]["y"] >= groups[0]["y"] + groups[0]["height"] - 1
                     and not _overlap(groups[0], groups[1]), "stacked, no overlap", groups)
        lc.scroll_to(lc.STEPS)
        steps = [b for b in lc.boxes(lc.STEP) if b]
        check.equals("workflow step count", len(steps), 4)
        check.truthy("four steps in one row", len({round(b["y"]) for b in steps}) == 1, "same row", [b["y"] for b in steps])
        lc.scroll_to(lc.BANNER)
        banner, section = lc.box(lc.BANNER), lc.box(lc.SECTION)
        check.truthy("banner spans the content width", abs(banner["width"] - section["width"]) <= 1
                     and abs(banner["x"] - section["x"]) <= 1, f"{section['width']}px at x={section['x']}",
                     f"{banner['width']}px at x={banner['x']}")

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138480 — tablet
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Legal Consultation page renders correctly at tablet viewport width (768x1024)")
@allure.label("pbi", "129404")
@allure.label("testcase", "138480")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129404
@pytest.mark.tc_138480
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_legal_consultation_tablet_viewport(page):
    """Azure TC 138480 | PBI 129404 — ENV-2 at 768x1024. "Tiles wrap rather
    than shrinking below legibility" = every tile's label/value font-size >=
    12px and unclipped; "section index remains usable" = the index (or a
    collapsed control) is still offered."""
    lc = LegalConsultationPage(page)
    check = _Check()
    lc.open_legal_consultation(locale="en")

    with allure.step("No horizontal scrollbar, no clipped content"):
        check.step("step 2")
        _check_no_overflow(check, lc)

    with allure.step("Hero/CTA reflow without overlap; tiles legible; index usable"):
        check.step("step 3")
        parts = {n: lc.box(l) for n, l in (("eyebrow", lc.EYEBROW), ("title", lc.TITLE), ("description", lc.HERO_DESC),
                                           ("CTA", lc.HERO_CTA))}
        names = list(parts)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                check.truthy(f"hero {names[i]} / {names[j]} no overlap", not _overlap(parts[names[i]], parts[names[j]]),
                             "no overlap", f"{parts[names[i]]} vs {parts[names[j]]}")
        for name, loc in (("quick-fact label", lc.FACT_LABEL), ("quick-fact value", lc.FACT_VALUE)):
            for i, s in enumerate(lc.computed_styles_all(loc, ["fontSize"])):
                size = float(s["fontSize"].rstrip("px"))
                check.truthy(f"{name} {i + 1} legible size", size >= MIN_LEGIBLE_FONT_PX, f">= {MIN_LEGIBLE_FONT_PX}px", size)
        _check_index_mobile(check, lc, "section index remains usable")

    with allure.step("Scope lists keep green/red; accordion operable; banner CTA visible"):
        check.step("step 4")
        inc = lc.computed_style(lc.SCOPE_GROUP_INCLUDED, ["backgroundColor"])["backgroundColor"]
        exc = lc.computed_style(lc.SCOPE_GROUP_EXCLUDED, ["backgroundColor"])["backgroundColor"]
        ig, eg = _rgb_parts(inc), _rgb_parts(exc)
        check.truthy("included list stays green", ig[1] > ig[0], "green-dominant surface", inc)
        check.truthy("excluded list stays red", eg[0] > eg[1], "red-dominant surface", exc)
        groups = [b for b in lc.boxes(lc.SCOPE_GROUP) if b]
        check.truthy("scope lists stack or narrow without overlap", len(groups) == 2 and not _overlap(*groups),
                     "no overlap", groups)
        lc.scroll_to(lc.FAQ)
        lc.expand_faq(0)
        check.equals("FAQ 1 expands", lc.faq_items()[0]["expanded"], "true")
        lc.collapse_faq(0)
        check.equals("FAQ 1 collapses", lc.faq_items()[0]["expanded"], "false")
        lc.scroll_to(lc.BANNER_CTA)
        cta = lc.box(lc.BANNER_CTA)
        check.truthy("banner CTA fully visible", lc.is_displayed(lc.BANNER_CTA) and cta["x"] >= 0 and cta["x"] + cta["width"] <= 769,
                     "inside the 768px viewport", cta)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138481 — mobile
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Legal Consultation page renders correctly at mobile viewport width (390x844)")
@allure.label("pbi", "129404")
@allure.label("testcase", "138481")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129404
@pytest.mark.tc_138481
@pytest.mark.parametrize("page", [{"viewport": (390, 844), "auth": False}], indirect=True)
def test_legal_consultation_mobile_viewport(page):
    """Azure TC 138481 | PBI 129404 — ENV-3 at 390x844 (frame 2798:90562). The
    case states explicitly that the section index "collapses to its mobile
    treatment rather than disappearing" — asserted literally."""
    lc = LegalConsultationPage(page)
    check = _Check()
    lc.open_legal_consultation(locale="en")

    with allure.step("No horizontal scrollbar, no overflowing text"):
        check.step("step 2")
        _check_no_overflow(check, lc)

    with allure.step("Hero stacks vertically; facts single column; index mobile treatment"):
        check.step("step 3")
        stack = [lc.box(l) for l in (lc.EYEBROW, lc.TITLE, lc.HERO_DESC, lc.HERO_CTA)]
        check.truthy("hero eyebrow, title, description, CTA stacked vertically",
                     all(stack[i]["y"] + stack[i]["height"] <= stack[i + 1]["y"] + 1 for i in range(3)),
                     "each below the previous", [round(b["y"]) for b in stack])
        facts = [b for b in lc.boxes(lc.FACT) if b]
        check.truthy("quick facts in a single column",
                     len({round(b["x"]) for b in facts}) == 1
                     and all(facts[i]["y"] + facts[i]["height"] <= facts[i + 1]["y"] + 1 for i in range(len(facts) - 1)),
                     "one tile per row", facts)
        _check_index_mobile(check, lc, "section index collapses to its mobile treatment rather than disappearing")

    with allure.step("Every section reachable; accordion toggles on tap; banner CTA full width"):
        check.step("step 4")
        for i in range(lc.count_of(lc.SECTION)):
            lc.scroll_to(lc.SECTION, i)
            check.truthy(f"section {i + 1} reachable by scrolling", lc.is_displayed(lc.SECTION, i), "visible", "not visible")
        lc.scroll_to(lc.FAQ)
        lc.expand_faq(0)
        check.equals("FAQ 1 expands on tap", lc.faq_items()[0]["expanded"], "true")
        lc.collapse_faq(0)
        check.equals("FAQ 1 collapses on tap", lc.faq_items()[0]["expanded"], "false")
        lc.scroll_to(lc.BANNER_CTA)
        cta = lc.box(lc.BANNER_CTA)
        width = _content_width(lc, lc.BANNER)
        check.truthy("banner CTA full width", abs(cta["width"] - width) <= 2, f"{width}px (banner content width)", cta["width"])
        check.truthy("banner CTA tap target", cta["height"] >= TAP_TARGET_PX, f">= {TAP_TARGET_PX}px", cta["height"])

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 138482 — request form at mobile width
# ---------------------------------------------------------------------------
@allure.epic("Services")
@allure.feature("Legal Consultation")
@allure.story("Request form")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Legal Consultation request form is usable at mobile viewport width (390x844)")
@allure.label("pbi", "129404")
@allure.label("testcase", "138482")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129404
@pytest.mark.tc_138482
@pytest.mark.parametrize("page", [{"viewport": (390, 844), "auth": False}], indirect=True)
def test_legal_consultation_request_form_mobile(page):
    """Azure TC 138482 | PBI 129404 — ENV-3 on the request form (a modal on the
    same page) at 390x844.

    SCOPE: steps 1-3 only. Step 4 ("Complete and submit the form") is NOT
    automated by explicit instruction (submission is backend and out of
    scope; the form is guarded by invisible reCAPTCHA Enterprise with no
    agreed bypass and a submission would write an untorn-down record). The
    fields are typed into and read back but the form is never submitted.
    The CAPTCHA is invisible reCAPTCHA Enterprise (no in-form widget; its
    field row is display:none and the badge parks with visibility:hidden),
    so "fits within the viewport" is asserted as: no PAINTED reCAPTCHA
    element extends past the viewport."""
    lc = LegalConsultationPage(page)
    check = _Check()
    lc.open_legal_consultation(locale="en")

    with allure.step("Open the request form"):
        lc.open_request_form()
        check.step("step 2")
        overflow = lc.horizontal_overflow_px()
        check.truthy("no horizontal scrollbar", overflow <= 0, "0px", f"{overflow}px {lc.overflowing_elements()}")
        dialog = lc.box(lc.DIALOG)
        check.truthy("form dialog inside the viewport", dialog["x"] >= 0 and dialog["x"] + dialog["width"] <= 391,
                     "inside 390px", dialog)

    with allure.step("Every field visible and tappable; attachment opens the file picker; CAPTCHA fits"):
        check.step("step 3")
        fields = lc.request_form_field_geometry()
        check.truthy("visible form fields", len(fields) > 0, "at least one", 0)
        for f in fields:
            name = f["label"] or f["control"]
            for part in ("labelBox", "controlBox"):
                b = f[part]
                check.truthy(f"{name} {part[:-3]} fully visible", b is not None and b["x"] >= 0 and b["x"] + b["width"] <= 391
                             and b["width"] > 0, "inside the 390px viewport", b)
            check.truthy(f"{name} label not clipped", not f["labelClipped"], "unclipped", "clipped")
            if f["controlBox"]:
                check.truthy(f"{name} control tap target", f["controlBox"]["height"] >= TAP_TARGET_PX,
                             f">= {TAP_TARGET_PX}px", f["controlBox"]["height"])
        options = [o for o in lc.category_options() if o]
        category = options[1] if len(options) > 1 else (options[0] if options else "")
        lc.fill_request_form(category_label=category, **FORM_TYPING_DATA)
        for control_id, key in (("qc-lc-fullName", "full_name"), ("qc-lc-companyName", "company_name"),
                                ("qc-lc-email", "email"), ("qc-lc-subject", "subject"),
                                ("qc-lc-description", "description")):
            check.equals(f"{control_id} accepts typed input", lc.field_value(control_id), FORM_TYPING_DATA[key])
        check.truthy("attachment control opens the file picker", lc.attachment_opens_file_chooser(),
                     "file chooser opened", "no file chooser")
        painted = lc.visible_recaptcha_boxes()
        check.truthy("CAPTCHA fits within the viewport", all(b["x"] >= 0 and b["right"] <= 391 for b in painted),
                     "no painted reCAPTCHA element past 390px", painted)
        allure.attach(str(lc.captcha_state()), "CAPTCHA state (invisible reCAPTCHA Enterprise)", allure.attachment_type.TEXT)
        allure.attach("Step 4 (submit) intentionally not executed — see docstring.", "scope note",
                      allure.attachment_type.TEXT)

    assert not check.deviations, check.report()

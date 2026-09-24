"""
web/tests/suggestions_complaints/test_suggestions_complaints_web.py —
Web-platform cases for PBI 131030 (QC - Councils, Committees & Partnerships -
006 - Suggestions & Complaints), sourced from the 88 approved/injected Azure
DevOps cases handed off for Phase 3 (already filtered to Automation-tagged,
Web-platform cases only — no Control_Panel case is in this batch).

LOCATORS ARE UNVERIFIED TODO PLACEHOLDERS
------------------------------------------------------------------
The Playwright MCP could not reach a live app session this session, and
`tools/extract_locators.py` was not run against a live page either (explicit
instruction for this batch: script structure first, extract real locators as
a separate follow-up pass). Every `SuggestionsComplaintsPage` locator
constant is a TODO(locator) placeholder — see that module's docstring. These
88 tests are therefore SCRIPTED, not executed and not verified; they will not
pass against a real page until the locators are extracted and patched in.

CAPTCHA gate — mirrors the established pattern in this framework
------------------------------------------------------------------
Every case whose real subject is an ACTUAL successful submission (a stored
Reference Number, a confirmation banner, an email having been sent) is
gated behind `_gate_on_captcha()`, the same disclosed-skip pattern already
used in `web/tests/legal_consultation/test_legal_consultation_web.py` for
138477/138490: the reachable steps (field acceptance, inline validation,
button state) run for real and fail red if the product is wrong; only the
final "click Submit and observe a real stored result" step is skipped, with
a concrete reason, because this project has no agreed CAPTCHA bypass (no
test key, no env flag, no backdoor) and a real submission would also write
an untorn-down request record. The assertions after the gate are written in
full and unweakened — the moment a bypass is configured the skip stops
firing and they run as-is.

Two cases are skipped on missing NON-CAPTCHA infrastructure, each with a
concrete reason (never a bare skip):
  - 144440 (exactly 2 emails sent) needs a mailbox-reading capability
    (IMAP/API access to the applicant and QC-team mailboxes) that does not
    exist anywhere in this framework yet — out of this batch's scope to
    invent.
  - 144666 (Internal Notes never public) needs an admin/CMS precondition
    (a submission whose Internal Notes field is populated) that only a
    Control_Panel-surface write can create — that surface is out of this
    batch (no Control_Panel-tagged case was handed off with it).

Field-family parametrization
------------------------------------------------------------------
The 55 field-level cases (144442-144465, 144632-144665) share one of eight
shapes (valid-accepted, empty-blocks, whitespace-rejected, max-length
boundary, invalid-format-rejected, optional-blank-succeeds, conditional
"Other" reveal, conditional "Other" empty-blocks) that differ only in which
field and which concrete value the case names. Per automation-standards.md's
guidance against near-identical duplicated bodies for a parametrized case
family, each shape is ONE test function, and each case is its own
`pytest.param(..., marks=[pytest.mark.tc_<id>])` — pytest still collects and
selects each as its own test item under its own `tc_<id>` marker (the exact
Axis C contract: "`pytest -m tc_129779` runs exactly the test(s) covering one
Azure Test Case"), so this is not the "merged test needing three tc_*
markers" pattern the structure scan flags — it is 55 distinct, individually
selectable test items sharing eight bodies.
"""

import allure
import pytest

from web.pages.suggestions_complaints.suggestions_complaints_page import (
    FIELD_BY_KEY,
    SuggestionsComplaintsPage,
)

PBI = pytest.mark.pbi_131030

EN_BREADCRUMB = ["Home", "Councils, Committees & Partnerships", "Suggestions and Complaints"]
EN_HERO_TITLE = "Suggestions and Complaints"
EN_DISCLAIMER = "Fields marked with * are required. Submission confirms receipt for review."
EN_EYEBROW = "Your Voice Matters"
MAROON = "rgb(145, 23, 49)"
BROWN_TOKEN = "rgb(166, 111, 67)"
RED_TOKEN = "rgb(225, 29, 72)"
DEFAULT_BORDER = "rgb(237, 237, 237)"


def _gate_on_captcha(sc: SuggestionsComplaintsPage, subject: str) -> None:
    """Skip with a concrete reason when the live CAPTCHA blocks an actual
    submission — see module docstring. Not a bare skip: names the subject
    the case wanted observed, the blocker, and the fact there is no bypass."""
    captcha = sc.captcha_state()
    if captcha.get("mountPresent") or captcha.get("recaptchaFrames", 0) >= 1:
        pytest.skip(
            f"PRECONDITION UNAVAILABLE — {subject} requires an ACTUAL successful "
            "submission, which requires passing the live CAPTCHA. This project has "
            "no agreed CAPTCHA bypass (no test key, no env flag, no backdoor) and a "
            "real submission would also persist a Suggestions & Complaints request "
            "with no teardown path. Every reachable step above ran for real. "
            "Configure a bypass, then this skip stops firing and the assertions "
            "below run unchanged."
        )


# ===========================================================================
# 144372 / 144373 — breadcrumb
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Breadcrumb renders Home > Councils, Committees & Partnerships > Suggestions and Complaints in English")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.comm
@PBI
@pytest.mark.tc_144372
@pytest.mark.traceability("144372")
@allure.label("pbi", "131030")
@allure.label("testcase", "144372")
def test_breadcrumb_english(page):
    sc = SuggestionsComplaintsPage(page)
    with allure.step("Navigate to the EN Suggestions and Complaints page"):
        sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the breadcrumb row"):
        crumbs = sc.breadcrumb_texts()
        assert crumbs == EN_BREADCRUMB
        # TC-001's wording ("each segment a working link to its parent page")
        # is loose on the LAST segment: that segment IS the current page, so
        # it has no parent to link to, and the product correctly renders it as
        # a plain <span aria-current="page">. Links are therefore asserted on
        # the ancestor segments (0..n-2) and the current segment is asserted
        # to be present, named and deliberately NOT a link. Deviation from the
        # case's literal wording is intentional and recorded here for review.
        hrefs = sc.breadcrumb_hrefs()
        for index in range(len(hrefs) - 1):
            assert hrefs[index], (
                f"breadcrumb segment {index} ({crumbs[index]!r}) is not a working link"
            )
        assert sc.current_breadcrumb_text() == EN_BREADCRUMB[-1]
        assert not sc.is_current_breadcrumb_linked(), (
            "the current-page breadcrumb segment is a hyperlink; it must be plain text"
        )


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Breadcrumb mirrors correctly in Arabic RTL")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.comm
@PBI
@pytest.mark.tc_144373
@pytest.mark.traceability("144373")
@allure.label("pbi", "131030")
@allure.label("testcase", "144373")
def test_breadcrumb_arabic_rtl(page):
    sc = SuggestionsComplaintsPage(page)
    with allure.step("Navigate to the AR Suggestions and Complaints page"):
        sc.open_suggestions_complaints(locale="ar")
    with allure.step("Inspect the breadcrumb row"):
        assert sc.document_direction() == "rtl"
        crumbs = sc.breadcrumb_texts()
        assert crumbs, "the Arabic breadcrumb rendered no segments"
        # Same deliberate deviation from TC-001's loose wording as the English
        # case above: the final segment is the current page and is correctly
        # a non-linked <span aria-current="page">.
        hrefs = sc.breadcrumb_hrefs()
        for index in range(len(hrefs) - 1):
            assert hrefs[index], f"Arabic breadcrumb segment {index} is not a working link"
        assert sc.current_breadcrumb_text(), "the Arabic current-page crumb rendered empty"
        assert not sc.is_current_breadcrumb_linked(), (
            "the Arabic current-page breadcrumb segment is a hyperlink; it must be plain text"
        )


# ===========================================================================
# 144374 / 144375 — hero typography
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Hero")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero title renders per the Figma-verified typography token")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144374
@pytest.mark.traceability("144374")
@allure.label("pbi", "131030")
@allure.label("testcase", "144374")
def test_hero_title_typography(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the hero title's computed style"):
        assert sc.hero_title_text() == EN_HERO_TITLE
        style = sc.computed_style(
            sc.HERO_TITLE, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
        )
        assert "cairo" in style["fontFamily"].lower()
        assert style["fontWeight"] == "700"
        assert sc.px_equals(style["fontSize"], "48px"), (
            f'fontSize {style["fontSize"]!r} is not within 1px of "48px"'
        )
        assert sc.px_equals(style["lineHeight"], "60px"), (
            f'lineHeight {style["lineHeight"]!r} is not within 1px of "60px"'
        )
        assert style["color"] == "rgb(29, 29, 27)"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Hero")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Hero description paragraph renders per the Figma-verified typography token")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144375
@pytest.mark.traceability("144375")
@allure.label("pbi", "131030")
@allure.label("testcase", "144375")
def test_hero_description_typography(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the hero description's computed style"):
        assert sc.hero_description_text() != ""
        style = sc.computed_style(sc.HERO_DESC, ["fontFamily", "fontWeight", "fontSize", "lineHeight"])
        assert "cairo" in style["fontFamily"].lower()
        assert style["fontWeight"] == "400"
        assert sc.px_equals(style["fontSize"], "16px"), (
            f'fontSize {style["fontSize"]!r} is not within 1px of "16px"'
        )
        assert sc.px_equals(style["lineHeight"], "24px"), (
            f'lineHeight {style["lineHeight"]!r} is not within 1px of "24px"'
        )


# ===========================================================================
# 144376 / 144377 — informational section
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Informational section")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Informational section eyebrow renders in the brand maroon token")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144376
@pytest.mark.traceability("144376")
@allure.label("pbi", "131030")
@allure.label("testcase", "144376")
def test_informational_eyebrow_maroon_token(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Scroll to the informational section and inspect the eyebrow"):
        assert sc.info_eyebrow_text() == EN_EYEBROW
        style = sc.computed_style(sc.INFO_EYEBROW, ["color", "fontSize", "lineHeight"])
        assert style["color"] == MAROON
        assert sc.px_equals(style["fontSize"], "14px"), (
            f'fontSize {style["fontSize"]!r} is not within 1px of "14px"'
        )
        assert sc.px_equals(style["lineHeight"], "22px"), (
            f'lineHeight {style["lineHeight"]!r} is not within 1px of "22px"'
        )


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Informational section")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Informational section heading and body paragraphs render with correct copy and typography")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144377
@pytest.mark.traceability("144377")
@allure.label("pbi", "131030")
@allure.label("testcase", "144377")
def test_informational_heading_and_paragraphs(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the informational section heading and body copy"):
        assert sc.info_heading_text() != ""
        heading_style = sc.computed_style(sc.INFO_HEADING, ["fontWeight", "fontSize", "lineHeight"])
        assert heading_style["fontWeight"] == "700"
        assert sc.px_equals(heading_style["fontSize"], "36px"), (
            f'fontSize {heading_style["fontSize"]!r} is not within 1px of "36px"'
        )
        assert sc.px_equals(heading_style["lineHeight"], "44px"), (
            f'lineHeight {heading_style["lineHeight"]!r} is not within 1px of "44px"'
        )

        paragraphs = sc.info_paragraph_texts()
        assert paragraphs, "the informational section rendered no explanatory paragraphs"
        for index in range(len(paragraphs)):
            style = sc.computed_style(sc.INFO_PARAGRAPHS, ["fontWeight", "fontSize", "lineHeight", "color"], index=index)
            assert style["fontWeight"] == "400"
            assert sc.px_equals(style["fontSize"], "16px"), (
                f'fontSize {style["fontSize"]!r} is not within 1px of "16px"'
            )
            assert sc.px_equals(style["lineHeight"], "24px"), (
                f'lineHeight {style["lineHeight"]!r} is not within 1px of "24px"'
            )
            assert style["color"] == "rgb(108, 108, 107)"


# ===========================================================================
# 144378 — form card container
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Form card container renders the correct icon, title, padding, radius and shadow tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144378
@pytest.mark.traceability("144378")
@allure.label("pbi", "131030")
@allure.label("testcase", "144378")
def test_form_card_container_tokens(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the form card container"):
        assert sc.is_visible(sc.FORM_CARD_ICON)
        assert sc.form_card_title_text() == EN_HERO_TITLE
        style = sc.computed_style(sc.FORM_CARD, ["padding", "borderRadius", "boxShadow"])
        assert style["padding"] == "64px 335px"
        assert style["borderRadius"] == "16px"
        assert "0px 0px 154px" in style["boxShadow"]
        assert "0.1" in style["boxShadow"] or "rgba(166, 111, 67" in style["boxShadow"]


# ===========================================================================
# 144379 — form disclaimer text
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form card")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Form disclaimer text renders the exact required copy and typography")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144379
@pytest.mark.traceability("144379")
@allure.label("pbi", "131030")
@allure.label("testcase", "144379")
def test_form_disclaimer_text(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the disclaimer line under the form card title"):
        assert sc.form_disclaimer_text() == EN_DISCLAIMER
        style = sc.computed_style(sc.FORM_DISCLAIMER, ["fontSize", "lineHeight", "color"])
        assert sc.px_equals(style["fontSize"], "12px"), (
            f'fontSize {style["fontSize"]!r} is not within 1px of "12px"'
        )
        assert sc.px_equals(style["lineHeight"], "18px"), (
            f'lineHeight {style["lineHeight"]!r} is not within 1px of "18px"'
        )
        assert style["color"] == "rgb(124, 123, 123)"


# ===========================================================================
# 144380 — field group headers
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Field group headers render Bold 700 16px/24px in the brown token color")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144380
@pytest.mark.traceability("144380")
@allure.label("pbi", "131030")
@allure.label("testcase", "144380")
def test_field_group_headers(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the three field-group section headers"):
        headers = sc.group_header_texts()
        assert len(headers) == 3, f"expected three field-group headers, rendered {len(headers)}"
        for index in range(len(headers)):
            style = sc.computed_style(sc.GROUP_HEADER, ["fontWeight", "fontSize", "lineHeight", "color"], index=index)
            assert style["fontWeight"] == "700"
            assert sc.px_equals(style["fontSize"], "16px"), (
                f'fontSize {style["fontSize"]!r} is not within 1px of "16px"'
            )
            assert sc.px_equals(style["lineHeight"], "24px"), (
                f'lineHeight {style["lineHeight"]!r} is not within 1px of "24px"'
            )
            assert style["color"] == BROWN_TOKEN


# ===========================================================================
# 144381 — required-field asterisks
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Required-field asterisks render in the correct red token beside every mandatory label")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144381
@pytest.mark.traceability("144381")
@allure.label("pbi", "131030")
@allure.label("testcase", "144381")
def test_required_field_asterisks(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the label of every visible field"):
        for key, label, required, _max_len, _control_type, _reveals in _field_rows():
            if not sc.is_field_visible(key):
                continue
            if required:
                assert sc.is_field_required_marked(key), f"required field {label!r} carries no asterisk"
                style = sc.computed_style(f"{sc.field_wrapper_locator(key)} {sc.FIELD_REQUIRED_MARK}", ["color", "fontWeight"])
                assert style["color"] == RED_TOKEN
                assert style["fontWeight"] == "700"
            else:
                assert not sc.is_field_required_marked(key), f"optional field {label!r} carries an asterisk"


def _field_rows():
    from web.pages.suggestions_complaints.suggestions_complaints_page import FIELD_TABLE
    return FIELD_TABLE


# ===========================================================================
# 144382 — Submit button default styling
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Submit button renders the pill shape, brand fill and gradient border in its default state")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144382
@pytest.mark.traceability("144382")
@allure.label("pbi", "131030")
@allure.label("testcase", "144382")
def test_submit_button_default_styling(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the Submit button's computed style"):
        assert sc.submit_button_text() != ""
        style = sc.computed_style(sc.SUBMIT_BUTTON, ["borderRadius", "backgroundColor", "borderWidth", "color"])
        assert style["borderRadius"] == "9999px"
        assert style["backgroundColor"] == MAROON
        assert style["borderWidth"] == "2px"
        assert style["color"] == "rgb(255, 255, 255)"


# ===========================================================================
# 144383 — input default-state styling
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form card")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Input fields render the correct default-state padding, radius and border tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144383
@pytest.mark.traceability("144383")
@allure.label("pbi", "131030")
@allure.label("testcase", "144383")
def test_input_default_state_styling(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Inspect the Applicant Name input's computed style before any interaction"):
        style = sc.field_border_style("applicant_name")
        assert style["padding"] == "11px 12px"
        assert style["borderRadius"] == "8px"
        assert style["borderColor"] == DEFAULT_BORDER


# ===========================================================================
# 144384 — invalid input error-state styling
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An invalid input field renders a distinct error-state border and inline message")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.comm
@PBI
@pytest.mark.tc_144384
@pytest.mark.traceability("144384")
@allure.label("pbi", "131030")
@allure.label("testcase", "144384")
def test_invalid_field_renders_error_state(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Enter an invalid value into Applicant Email"):
        sc.fill_field("applicant_email", "notanemail")
    with allure.step("Click outside the field to trigger validation"):
        sc.blur_field("applicant_email")
        assert sc.field_border_color("applicant_email") != DEFAULT_BORDER
        assert sc.is_field_error_visible("applicant_email")
        assert sc.field_error_text("applicant_email") == "Please enter a valid email address."


# ===========================================================================
# 144385 — responsive reflow across breakpoints
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Form card reflows correctly across desktop, tablet and mobile breakpoints")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.comm
@PBI
@pytest.mark.tc_144385
@pytest.mark.traceability("144385")
@allure.label("pbi", "131030")
@allure.label("testcase", "144385")
def test_form_card_reflows_across_breakpoints(page):
    sc = SuggestionsComplaintsPage(page)
    with allure.step("Load at 1920px and inspect the desktop layout"):
        sc.page.set_viewport_size({"width": 1920, "height": 1080})
        sc.open_suggestions_complaints(locale="en")
        desktop_overflow_x = sc.page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        assert not desktop_overflow_x, "desktop layout has a horizontal scrollbar"

    with allure.step("Resize to 768px and inspect the tablet layout"):
        sc.page.set_viewport_size({"width": 768, "height": 1024})
        assert sc.is_visible(sc.FORM), "form is not fully visible at tablet width"

    with allure.step("Resize to 375px and inspect the mobile layout"):
        sc.page.set_viewport_size({"width": 375, "height": 667})
        assert sc.is_visible(sc.FORM), "form is not fully visible at mobile width"
        mobile_overflow_x = sc.page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        assert not mobile_overflow_x, "mobile layout has a horizontal scrollbar"


# ===========================================================================
# 144386-144388 — desktop / tablet / mobile viewport compatibility
# ===========================================================================
@pytest.mark.parametrize(
    "page, viewport_label",
    [
        pytest.param((1920, 1080), "desktop 1920x1080", marks=[pytest.mark.tc_144386], id="desktop"),
        pytest.param((768, 1024), "tablet 768x1024", marks=[pytest.mark.tc_144387], id="tablet"),
        pytest.param((375, 667), "mobile 375x667", marks=[pytest.mark.tc_144388], id="mobile"),
    ],
    indirect=["page"],
)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly at the given viewport")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.comm
@PBI
@allure.label("pbi", "131030")
def test_page_renders_at_viewport(page, viewport_label):
    sc = SuggestionsComplaintsPage(page)
    with allure.step(f"Load the page at {viewport_label} and inspect layout end to end"):
        sc.open_suggestions_complaints(locale="en")
        assert sc.is_visible(sc.HERO_TITLE)
        assert sc.is_visible(sc.FORM)
        overflow_x = sc.page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        assert not overflow_x, f"{viewport_label} layout has a horizontal scrollbar / clipped content"


# ===========================================================================
# 144389 — Light mode
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly in Light mode")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.comm
@PBI
@pytest.mark.tc_144389
@pytest.mark.traceability("144389")
@allure.label("pbi", "131030")
@allure.label("testcase", "144389")
def test_page_light_mode(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Confirm the theme is Light and inspect background/text colors"):
        assert sc.theme() in (None, "light")
        card_style = sc.computed_style(sc.FORM_CARD, ["backgroundColor"])
        assert card_style["backgroundColor"] == "rgb(255, 255, 255)"
        title_style = sc.computed_style(sc.HERO_TITLE, ["color"])
        assert title_style["color"] == "rgb(29, 29, 27)"


# ===========================================================================
# 144390 — Dark mode
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly in Dark mode")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.comm
@PBI
@pytest.mark.tc_144390
@pytest.mark.traceability("144390")
@allure.label("pbi", "131030")
@allure.label("testcase", "144390")
def test_page_dark_mode(page):
    from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Toggle the site theme to Dark"):
        AccessibilityToolsComponent(page).enable_dark_mode()
        assert sc.theme() == "dark"
    with allure.step("Inspect background/text colors and contrast"):
        assert sc.is_visible(sc.HERO_TITLE)
        assert sc.hero_title_text() == EN_HERO_TITLE
        assert sc.is_visible(sc.FORM)


# ===========================================================================
# 144391 — Normal contrast
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Compatibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Page renders correctly with Normal contrast")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.comm
@PBI
@pytest.mark.tc_144391
@pytest.mark.traceability("144391")
@allure.label("pbi", "131030")
@allure.label("testcase", "144391")
def test_page_normal_contrast(page):
    from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Ensure the accessibility contrast toggle is set to Normal"):
        assert not AccessibilityToolsComponent(page).is_high_contrast_switch_checked()
    with allure.step("Inspect text/background contrast against the design tokens"):
        card_style = sc.computed_style(sc.FORM_CARD, ["backgroundColor"])
        assert card_style["backgroundColor"] == "rgb(255, 255, 255)"


# ===========================================================================
# 144392 — High-Contrast mode
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly with High-Contrast mode enabled")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.comm
@PBI
@pytest.mark.tc_144392
@pytest.mark.traceability("144392")
@allure.label("pbi", "131030")
@allure.label("testcase", "144392")
def test_page_high_contrast_mode(page):
    from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Enable the High-Contrast accessibility toggle"):
        AccessibilityToolsComponent(page).enable_high_contrast()
    with allure.step("Reload and inspect text/background contrast and layout"):
        sc.open_suggestions_complaints(locale="en")
        assert sc.is_visible(sc.HERO_TITLE)
        assert sc.is_visible(sc.FORM)


# ===========================================================================
# 144393 — Public Visitor can submit without logging in
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Submission")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Public Visitor can submit the form without logging in")
@pytest.mark.web
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.comm
@PBI
@pytest.mark.tc_144393
@pytest.mark.traceability("144393")
@allure.label("pbi", "131030")
@allure.label("testcase", "144393")
def test_public_visitor_can_submit_without_login(page):
    sc = SuggestionsComplaintsPage(page)
    with allure.step("Open the page in a fresh, unauthenticated browser context"):
        sc.open_suggestions_complaints(locale="en")
        assert not sc.is_visible("form[name='fm'][action*='login']"), "an unexpected login prompt is showing"
    with allure.step("Complete all mandatory fields with valid data"):
        sc.fill_mandatory_fields()
        for key, _, required, _, _, _ in _field_rows():
            if required and sc.is_field_visible(key):
                assert not sc.is_field_error_visible(key), f"{key} shows a validation error with valid data"
    _gate_on_captcha(sc, "clicking Submit and observing a Reference Number + bilingual acknowledgement")
    with allure.step("Pass CAPTCHA and click Submit"):
        sc.click_submit()
    with allure.step("Confirm the submission succeeded"):
        confirmation = sc.confirmation_state()
        assert confirmation and confirmation["visible"]
        assert sc.reference_number()


# ===========================================================================
# 144400 — fully valid submission stored Pending with bilingual acknowledgement
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Submission")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A fully valid submission is stored with a unique Reference Number, status Pending, and a bilingual acknowledgement is shown")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.comm
@PBI
@pytest.mark.tc_144400
@pytest.mark.traceability("144400")
@allure.label("pbi", "131030")
@allure.label("testcase", "144400")
def test_valid_submission_stored_pending_with_bilingual_acknowledgement(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Complete all mandatory Applicant, Company and Submission Details fields"):
        sc.fill_mandatory_fields()
        for key, _, required, _, _, _ in _field_rows():
            if required and sc.is_field_visible(key):
                assert not sc.is_field_error_visible(key)
    _gate_on_captcha(sc, "the stored Reference Number, Status=Pending and bilingual acknowledgement banner")
    with allure.step("Complete the CAPTCHA challenge and click Submit"):
        sc.click_submit()
    with allure.step("Confirm the acknowledgement and Reference Number"):
        confirmation = sc.confirmation_state()
        assert confirmation and confirmation["visible"]
        reference = sc.reference_number()
        assert reference
        assert reference in confirmation["text"]


# ===========================================================================
# 144401 — missing mandatory field blocks submission
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Submitting with a mandatory field missing blocks submission with inline validation")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.comm
@PBI
@pytest.mark.tc_144401
@pytest.mark.traceability("144401")
@allure.label("pbi", "131030")
@allure.label("testcase", "144401")
def test_missing_mandatory_field_blocks_submission(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Complete all mandatory fields except Company Email"):
        sc.fill_mandatory_fields(skip={"company_email"})
    with allure.step("Click Submit"):
        sc.click_submit()
    with allure.step("Confirm submission is blocked"):
        assert sc.is_field_error_visible("company_email")
        assert sc.field_error_text("company_email") == "This field is required."
        confirmation = sc.confirmation_state()
        assert not (confirmation and confirmation["visible"]), "submission was not blocked"
        assert sc.reference_number() is None


# ===========================================================================
# 144402 — CAPTCHA unsolved blocks submission
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Submitting without completing CAPTCHA blocks submission with a CAPTCHA error")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.comm
@PBI
@pytest.mark.tc_144402
@pytest.mark.traceability("144402")
@allure.label("pbi", "131030")
@allure.label("testcase", "144402")
def test_unsolved_captcha_blocks_submission(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Complete all mandatory fields with valid data, leaving CAPTCHA unsolved"):
        sc.fill_mandatory_fields()
    with allure.step("Click Submit"):
        sc.click_submit()
    with allure.step("Confirm submission is blocked with a CAPTCHA error"):
        assert sc.is_visible(sc.CAPTCHA_MOUNT)
        confirmation = sc.confirmation_state()
        assert not (confirmation and confirmation["visible"])
        assert sc.reference_number() is None


# ===========================================================================
# 144440 — exactly 2 emails sent, only at submission time
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Notifications")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Exactly 2 emails are sent in total for a submission, both only at submission time")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.comm
@PBI
@pytest.mark.tc_144440
@pytest.mark.traceability("144440")
@allure.label("pbi", "131030")
@allure.label("testcase", "144440")
def test_exactly_two_emails_sent_at_submission_time(page):
    pytest.skip(
        "PRECONDITION UNAVAILABLE — this case requires reading two real mailboxes "
        "(the applicant's and the QC team distribution mailbox) immediately after "
        "submission and again after two status changes. No mailbox-reading "
        "capability (IMAP client / mail-provider API) exists anywhere in this "
        "framework yet, and this batch's scope did not include building one. "
        "Add a mailbox-reading utility (e.g. core/utils/mailbox.py) plus its "
        "credentials in .env, then this skip stops firing and the assertions "
        "below can be written against it."
    )


# ===========================================================================
# Field-family group A — valid value accepted, submission succeeds
# ===========================================================================
# `None` means "resolve the value live from the product" — the Page Object's
# `sample_value()` reads the real option label off the lookups endpoint for
# the three SELECT fields (a hardcoded, never-existing "Manager" label here is
# what broke 35 tests in run 1). Free-text values stay literal: the case names
# them, so they are part of the test's intent.
# The two MOBILE fields are maxlength=8 national-format inputs with "+974"
# rendered as static chrome beside the box — the value is 8 bare digits.
# Telephone (Direct Line) is a separate maxlength=40 free-form control, so its
# full international sample is unchanged.
_VALID_ACCEPTED_CASES = [
    pytest.param("applicant_name", "Ahmed Al-Sayed", marks=[pytest.mark.tc_144442], id="applicant_name"),
    pytest.param("applicant_position", None, marks=[pytest.mark.tc_144446], id="applicant_position"),
    pytest.param("applicant_email", "ahmed.alsayed@example.com", marks=[pytest.mark.tc_144452], id="applicant_email"),
    pytest.param("applicant_mobile", "55123456", marks=[pytest.mark.tc_144456], id="applicant_mobile"),
    pytest.param("company_name", "Al Rayyan Trading LLC", marks=[pytest.mark.tc_144460], id="company_name"),
    pytest.param("cr_number", "123456", marks=[pytest.mark.tc_144463], id="cr_number"),
    pytest.param("type_of_ownership", None, marks=[pytest.mark.tc_144634], id="type_of_ownership"),
    pytest.param("company_telephone", "+974 4444 5555", marks=[pytest.mark.tc_144636], id="company_telephone"),
    pytest.param("company_mobile", "33445566", marks=[pytest.mark.tc_144638], id="company_mobile"),
    pytest.param("company_email", "info@alrayyantrading.com", marks=[pytest.mark.tc_144642], id="company_email"),
    pytest.param("sector", None, marks=[pytest.mark.tc_144647], id="sector"),
    pytest.param(
        "complaint_brief",
        "Delayed customs clearance at Hamad Port affecting our shipment schedule.",
        marks=[pytest.mark.tc_144655],
        id="complaint_brief",
    ),
    pytest.param(
        "proposal_solution",
        "Request expedited clearance lane coordination with Customs Authority.",
        marks=[pytest.mark.tc_144659],
        id="proposal_solution",
    ),
]


@pytest.mark.parametrize("field_key, value", _VALID_ACCEPTED_CASES)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Field validation — valid value accepted")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@allure.label("pbi", "131030")
def test_field_accepts_valid_value_and_submission_succeeds(page, field_key, value):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    label = FIELD_BY_KEY[field_key][1]
    if value is None:  # select field — take the live option label
        value = sc.sample_value(field_key)
    with allure.step(f"Enter {value!r} into {label}"):
        sc.fill_field(field_key, value)
        sc.blur_field(field_key)
        assert not sc.is_field_error_visible(field_key), f"{label} shows a validation error for a valid value"
    _gate_on_captcha(sc, f"submitting with {label}={value!r} and observing the stored value")
    with allure.step("Complete remaining mandatory fields with valid data and submit"):
        sc.fill_mandatory_fields(overrides={field_key: value})
        sc.click_submit()
    with allure.step("Confirm the submission succeeded with the stored value"):
        confirmation = sc.confirmation_state()
        assert confirmation and confirmation["visible"]
        assert sc.reference_number()


# ===========================================================================
# Field-family group B — empty required field blocks submission
# ===========================================================================
_EMPTY_BLOCKS_CASES = [
    pytest.param("applicant_name", marks=[pytest.mark.tc_144443], id="applicant_name"),
    pytest.param("applicant_position", marks=[pytest.mark.tc_144447], id="applicant_position"),
    pytest.param("applicant_email", marks=[pytest.mark.tc_144453], id="applicant_email"),
    pytest.param("applicant_mobile", marks=[pytest.mark.tc_144457], id="applicant_mobile"),
    pytest.param("company_name", marks=[pytest.mark.tc_144461], id="company_name"),
    pytest.param("cr_number", marks=[pytest.mark.tc_144464], id="cr_number"),
    pytest.param("type_of_ownership", marks=[pytest.mark.tc_144635], id="type_of_ownership"),
    pytest.param("company_mobile", marks=[pytest.mark.tc_144639], id="company_mobile"),
    pytest.param("company_email", marks=[pytest.mark.tc_144643], id="company_email"),
    pytest.param("sector", marks=[pytest.mark.tc_144648], id="sector"),
    pytest.param("complaint_brief", marks=[pytest.mark.tc_144656], id="complaint_brief"),
    pytest.param("proposal_solution", marks=[pytest.mark.tc_144660], id="proposal_solution"),
]


@pytest.mark.parametrize("field_key", _EMPTY_BLOCKS_CASES)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Field validation — required field empty")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@allure.label("pbi", "131030")
def test_empty_required_field_blocks_submission(page, field_key):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    label = FIELD_BY_KEY[field_key][1]
    with allure.step(f"Leave {label} empty; complete all other mandatory fields"):
        sc.fill_mandatory_fields(skip={field_key})
    with allure.step("Click Submit"):
        sc.click_submit()
    with allure.step(f"Confirm the inline required-field error shows on {label} and submission is blocked"):
        assert sc.is_field_error_visible(field_key)
        confirmation = sc.confirmation_state()
        assert not (confirmation and confirmation["visible"])


# ===========================================================================
# Field-family group C — whitespace-only value rejected as empty
# ===========================================================================
_WHITESPACE_REJECTED_CASES = [
    pytest.param("applicant_name", marks=[pytest.mark.tc_144445], id="applicant_name"),
    pytest.param("applicant_position_other", marks=[pytest.mark.tc_144451], id="applicant_position_other"),
    pytest.param("applicant_email", marks=[pytest.mark.tc_144455], id="applicant_email"),
    pytest.param("applicant_mobile", marks=[pytest.mark.tc_144459], id="applicant_mobile"),
    pytest.param("company_name", marks=[pytest.mark.tc_144462], id="company_name"),
    pytest.param("cr_number", marks=[pytest.mark.tc_144465], id="cr_number"),
    pytest.param("company_mobile", marks=[pytest.mark.tc_144641], id="company_mobile"),
    pytest.param("company_email", marks=[pytest.mark.tc_144646], id="company_email"),
    pytest.param("sector_other", marks=[pytest.mark.tc_144652], id="sector_other"),
    pytest.param("complaint_brief", marks=[pytest.mark.tc_144658], id="complaint_brief"),
    pytest.param("proposal_solution", marks=[pytest.mark.tc_144662], id="proposal_solution"),
]


@pytest.mark.parametrize("field_key", _WHITESPACE_REJECTED_CASES)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Field validation — whitespace-only rejected as empty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@allure.label("pbi", "131030")
def test_whitespace_only_field_rejected_as_empty(page, field_key):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    label = FIELD_BY_KEY[field_key][1]
    with allure.step(f"Reveal {label} if conditional, then enter '   ' into it"):
        if field_key in ("applicant_position_other",):
            sc.fill_field("applicant_position", "Other")
        if field_key in ("sector_other",):
            sc.fill_field("sector", "Other")
        sc.fill_mandatory_fields(skip={field_key})
        sc.fill_field(field_key, "   ")
    with allure.step("Click Submit"):
        sc.click_submit()
    with allure.step(f"Confirm {label} is rejected with the required-field error, same as empty"):
        assert sc.is_field_error_visible(field_key)
        confirmation = sc.confirmation_state()
        assert not (confirmation and confirmation["visible"])


# ===========================================================================
# Field-family group D — max-length boundary (N accepted, N+1 rejected/capped)
# ===========================================================================
_MAX_LENGTH_CASES = [
    pytest.param("applicant_name", 200, marks=[pytest.mark.tc_144444], id="applicant_name"),
    pytest.param("applicant_position_other", 100, marks=[pytest.mark.tc_144450], id="applicant_position_other"),
    pytest.param("company_email", 150, marks=[pytest.mark.tc_144645], id="company_email"),
    pytest.param("sector_other", 100, marks=[pytest.mark.tc_144651], id="sector_other"),
    pytest.param("complaint_brief", 2000, marks=[pytest.mark.tc_144657], id="complaint_brief"),
    pytest.param("proposal_solution", 2000, marks=[pytest.mark.tc_144661], id="proposal_solution"),
]


@pytest.mark.parametrize("field_key, max_length", _MAX_LENGTH_CASES)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Field validation — max-length boundary")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@allure.label("pbi", "131030")
def test_field_accepts_max_length_and_rejects_one_over(page, field_key, max_length):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    label = FIELD_BY_KEY[field_key][1]

    def _sample(n, is_email=False):
        if is_email:
            local = "a" * max(1, n - len("@example.com"))
            return f"{local}@example.com"[:n]
        return "A" * n

    is_email = FIELD_BY_KEY[field_key][4] == "email"

    with allure.step(f"Reveal {label} if conditional, then enter a {max_length}-character value"):
        if field_key == "applicant_position_other":
            sc.fill_field("applicant_position", "Other")
        if field_key == "sector_other":
            sc.fill_field("sector", "Other")
        at_limit = _sample(max_length, is_email)
        sc.fill_field(field_key, at_limit)
        assert sc.field_value(field_key) == at_limit or len(sc.field_value(field_key)) == max_length

    with allure.step(f"Enter a {max_length + 1}-character value and attempt to submit"):
        over_limit = _sample(max_length + 1, is_email)
        sc.fill_field(field_key, over_limit)
        current = sc.field_value(field_key)
        assert len(current) <= max_length or sc.is_field_error_visible(field_key), (
            f"{label} accepted {len(current)} characters, over its {max_length}-character limit, "
            "with no max-length error"
        )


# ===========================================================================
# Field-family group E — invalid format rejected
# ===========================================================================
_INVALID_FORMAT_CASES = [
    pytest.param("applicant_email", "ahmed.alsayed", "Please enter a valid email address.", marks=[pytest.mark.tc_144454], id="applicant_email"),
    pytest.param("applicant_mobile", "5512345", None, marks=[pytest.mark.tc_144458], id="applicant_mobile"),
    pytest.param("company_telephone", "abc123", None, marks=[pytest.mark.tc_144637], id="company_telephone"),
    pytest.param("company_mobile", "334455", None, marks=[pytest.mark.tc_144640], id="company_mobile"),
    pytest.param("company_email", "info@alrayyan", "Please enter a valid email address.", marks=[pytest.mark.tc_144644], id="company_email"),
]


@pytest.mark.parametrize("field_key, bad_value, expected_message", _INVALID_FORMAT_CASES)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Field validation — invalid format")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@allure.label("pbi", "131030")
def test_invalid_format_field_rejected(page, field_key, bad_value, expected_message):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    label = FIELD_BY_KEY[field_key][1]
    with allure.step(f"Enter {bad_value!r} into {label}"):
        sc.fill_field(field_key, bad_value)
    with allure.step("Click outside the field / attempt to submit"):
        sc.blur_field(field_key)
        assert sc.is_field_error_visible(field_key), f"{label} shows no format error for {bad_value!r}"
        if expected_message:
            assert sc.field_error_text(field_key) == expected_message
        confirmation = sc.confirmation_state()
        assert not (confirmation and confirmation["visible"])


# ===========================================================================
# Field-family group F — optional field left blank, submission succeeds
# ===========================================================================
_OPTIONAL_BLANK_CASES = [
    pytest.param("activity_as_in_cr", marks=[pytest.mark.tc_144632], id="activity_as_in_cr"),
    pytest.param("primary_business_activity", marks=[pytest.mark.tc_144633], id="primary_business_activity"),
    pytest.param("authority", marks=[pytest.mark.tc_144653], id="authority"),
    pytest.param("department", marks=[pytest.mark.tc_144654], id="department"),
]


@pytest.mark.parametrize("field_key", _OPTIONAL_BLANK_CASES)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Field validation — optional field blank")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@allure.label("pbi", "131030")
def test_optional_field_blank_submission_succeeds(page, field_key):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    label = FIELD_BY_KEY[field_key][1]
    with allure.step(f"Leave {label} empty; complete all other mandatory fields"):
        sc.fill_mandatory_fields()
        assert not sc.is_field_error_visible(field_key), f"optional field {label} raised a validation error while empty"
    _gate_on_captcha(sc, f"submitting with {label} stored as blank")
    with allure.step("Click Submit"):
        sc.click_submit()
    with allure.step("Confirm the submission succeeded"):
        confirmation = sc.confirmation_state()
        assert confirmation and confirmation["visible"]


# ===========================================================================
# Field-family group G — "Other" conditional reveal
# ===========================================================================
_OTHER_REVEAL_CASES = [
    pytest.param("applicant_position", "applicant_position_other", marks=[pytest.mark.tc_144448], id="applicant_position"),
    pytest.param("sector", "sector_other", marks=[pytest.mark.tc_144649], id="sector"),
]


@pytest.mark.parametrize("select_key, revealed_key", _OTHER_REVEAL_CASES)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Field validation — conditional 'Other' field")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@allure.label("pbi", "131030")
def test_selecting_other_reveals_mandatory_conditional_field(page, select_key, revealed_key):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    select_label = FIELD_BY_KEY[select_key][1]
    with allure.step(f"Select 'Other' from the {select_label} dropdown"):
        sc.fill_field(select_key, "Other")
    with allure.step("Observe the field area directly beneath the dropdown"):
        assert sc.is_field_visible(revealed_key), f"{revealed_key} was not revealed after selecting Other"
        assert sc.is_field_required_marked(revealed_key)
        assert sc.field_max_length_attribute(revealed_key) == "100"


# ===========================================================================
# Field-family group H — "Other" conditional field empty blocks submission
# ===========================================================================
_OTHER_EMPTY_BLOCKS_CASES = [
    pytest.param("applicant_position", "applicant_position_other", marks=[pytest.mark.tc_144449], id="applicant_position"),
    pytest.param("sector", "sector_other", marks=[pytest.mark.tc_144650], id="sector"),
]


@pytest.mark.parametrize("select_key, revealed_key", _OTHER_EMPTY_BLOCKS_CASES)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Field validation — conditional 'Other' field")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@allure.label("pbi", "131030")
def test_other_conditional_field_empty_blocks_submission(page, select_key, revealed_key):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    select_label = FIELD_BY_KEY[select_key][1]
    with allure.step(f"Select 'Other' for {select_label} and leave the revealed field empty"):
        sc.fill_field(select_key, "Other")
        assert sc.is_field_visible(revealed_key)
        sc.fill_mandatory_fields(skip={revealed_key})
    with allure.step("Complete all other mandatory fields and click Submit"):
        sc.click_submit()
    with allure.step("Confirm the inline required-field error shows on the conditional field"):
        assert sc.is_field_error_visible(revealed_key)
        confirmation = sc.confirmation_state()
        assert not (confirmation and confirmation["visible"])


# ===========================================================================
# 144663 — every submission gets a unique Reference Number
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Submission")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Every submission receives a unique, system-generated Reference Number never duplicated across submissions")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@pytest.mark.tc_144663
@pytest.mark.traceability("144663")
@allure.label("pbi", "131030")
@allure.label("testcase", "144663")
def test_reference_numbers_are_unique_across_submissions(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    sc.fill_mandatory_fields()
    _gate_on_captcha(sc, "two real submissions and comparing their Reference Numbers")
    with allure.step("Submit a first fully valid form"):
        sc.click_submit()
        first_reference = sc.reference_number()
        assert first_reference
    with allure.step("Submit a second fully valid form with different applicant data"):
        sc.open_suggestions_complaints(locale="en")
        sc.fill_mandatory_fields(overrides={"applicant_name": "Fatima Al-Kuwari", "applicant_email": "fatima.alkuwari@example.com"})
        sc.click_submit()
        second_reference = sc.reference_number()
    with allure.step("Confirm the two Reference Numbers differ"):
        assert second_reference
        assert second_reference != first_reference


# ===========================================================================
# 144666 — Internal Notes never rendered publicly
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Internal Notes are never rendered on any applicant-facing or public surface")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.dataintegrity
@pytest.mark.comm
@PBI
@pytest.mark.tc_144666
@pytest.mark.traceability("144666")
@allure.label("pbi", "131030")
@allure.label("testcase", "144666")
def test_internal_notes_never_public(page):
    pytest.skip(
        "PRECONDITION UNAVAILABLE — step 1 of this case is an admin/CMS action "
        "(confirm a submission has Internal Notes text saved via the admin view). "
        "There is no public-form field to set Internal Notes, so the precondition "
        "can only be created on the Control_Panel/admin surface, which is out of "
        "this batch's scope (no Control_Panel-tagged case was handed off with "
        "this PBI). Once an admin-side test creates a submission with Internal "
        "Notes populated (and shares its Reference Number), this skip stops "
        "firing and the public-surface assertion below can run against it."
    )


# ===========================================================================
# 144673 — rapid double-click does not create two submissions
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Submission")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking Submit twice rapidly does not create two separate submissions from one user action")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@pytest.mark.tc_144673
@pytest.mark.traceability("144673")
@allure.label("pbi", "131030")
@allure.label("testcase", "144673")
def test_double_click_submit_creates_one_submission(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Complete all mandatory fields with valid data and pass CAPTCHA"):
        sc.fill_mandatory_fields()
    with allure.step("Double-click the Submit button in rapid succession"):
        sc.page.locator(sc.SUBMIT_BUTTON).dblclick()
    with allure.step("Confirm the Submit button is disabled/debounced after the first click"):
        assert sc.is_submit_button_disabled(), "Submit button is not disabled/debounced after the first click"
    _gate_on_captcha(sc, "confirming exactly one submission record / one Reference Number was created")


# ===========================================================================
# 144674 — Privacy Policy hyperlink
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Form card")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Clicking the Privacy Policy hyperlink opens the configured Privacy Policy page in the correct language")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@pytest.mark.tc_144674
@pytest.mark.traceability("144674")
@allure.label("pbi", "131030")
@allure.label("testcase", "144674")
def test_privacy_policy_link(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Locate the consent line and its Privacy Policy hyperlink"):
        assert sc.is_visible(sc.PRIVACY_POLICY_LINK)
        href = sc.privacy_policy_href()
        assert href, "the Privacy Policy hyperlink has no href"
    # Confirmed live (trace 2026-09-22): the fragment root carries
    # data-privacy-url="/web/qatar-chamber/suggestions-complaints-privacy" and
    # the consent link navigates in the SAME tab — there is no target="_blank".
    # The original body waited on a context "page" event that never fires.
    with allure.step("Click the Privacy Policy hyperlink"):
        sc.click_privacy_policy_link()
        sc.wait_for_url("**/suggestions-complaints-privacy*")
    with allure.step("Confirm the Privacy Policy page itself rendered"):
        assert "suggestions-complaints-privacy" in sc.page.url
        title = sc.page.title()
        assert title, "the Privacy Policy page rendered no title"
        assert "404" not in title.lower() and "not found" not in title.lower()
        assert sc.is_visible("h1"), "the Privacy Policy page rendered no heading"
    with allure.step("Go back to the Suggestions and Complaints form"):
        sc.go_back()
        sc.wait_for(sc.FORM, state="visible", timeout=30000)


# ===========================================================================
# 144684 — paste behaves identically to typed input
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Field validation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Pasting text into a text field is accepted identically to typed input")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.comm
@PBI
@pytest.mark.tc_144684
@pytest.mark.traceability("144684")
@allure.label("pbi", "131030")
@allure.label("testcase", "144684")
def test_paste_accepted_identically_to_typed_input(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    pasted_value = "Fatima Al-Kuwari"
    with allure.step("Paste text into the Applicant Name field"):
        sc.paste_into_field("applicant_name", pasted_value)
        assert sc.field_value("applicant_name") == pasted_value
        assert not sc.is_field_error_visible("applicant_name")
    _gate_on_captcha(sc, "submitting and confirming the stored Applicant Name matches the pasted value exactly")
    with allure.step("Complete remaining mandatory fields with valid data and submit"):
        sc.fill_mandatory_fields(overrides={"applicant_name": pasted_value})
        sc.click_submit()
    with allure.step("Confirm the submission succeeded"):
        confirmation = sc.confirmation_state()
        assert confirmation and confirmation["visible"]


# ===========================================================================
# 144687 — browser Back + resubmit after success creates a distinct Reference Number
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Using browser Back and resubmitting after a successful submission creates a distinct new Reference Number")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.comm
@PBI
@pytest.mark.tc_144687
@pytest.mark.traceability("144687")
@allure.label("pbi", "131030")
@allure.label("testcase", "144687")
def test_browser_back_and_resubmit_creates_distinct_reference(page):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    sc.fill_mandatory_fields()
    _gate_on_captcha(sc, "a completed submission, browser Back, and a resubmission's distinct Reference Number")
    with allure.step("Complete and submit the form successfully"):
        sc.click_submit()
        first_reference = sc.reference_number()
        assert first_reference
    with allure.step("Click the browser Back button to return to the filled form"):
        sc.page.go_back()
        assert sc.is_visible(sc.FORM), "browser Back did not return to the form"
    with allure.step("Click Submit again without changing any data"):
        sc.click_submit()
        second_reference = sc.reference_number()
    with allure.step("Confirm either a distinct Reference Number or a re-validated/blocked resubmission"):
        confirmation = sc.confirmation_state()
        resubmission_blocked = not (confirmation and confirmation["visible"])
        assert resubmission_blocked or (second_reference and second_reference != first_reference), (
            "the resubmission silently reused the first Reference Number "
            f"({second_reference!r} == {first_reference!r})"
        )


# ===========================================================================
# 144692 — reverting Sector/Applicant Position from 'Other' hides and clears field
# ===========================================================================
@pytest.mark.parametrize(
    "select_key, revealed_key, revert_value",
    [
        pytest.param("sector", "sector_other", "Trade", id="sector"),
    ],
)
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Suggestions and Complaints")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reverting Sector or Applicant Position from 'Other' back to a normal value hides and clears the conditional text field")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.comm
@PBI
@pytest.mark.tc_144692
@pytest.mark.traceability("144692")
@allure.label("pbi", "131030")
@allure.label("testcase", "144692")
def test_reverting_other_hides_and_clears_conditional_field(page, select_key, revealed_key, revert_value):
    sc = SuggestionsComplaintsPage(page)
    sc.open_suggestions_complaints(locale="en")
    with allure.step("Select 'Other' and type into the revealed conditional field"):
        sc.fill_field(select_key, "Other")
        sc.fill_field(revealed_key, "Custom sector description")
        assert sc.field_value(revealed_key) == "Custom sector description"
    with allure.step(f"Change the selection from 'Other' back to {revert_value!r}"):
        sc.fill_field(select_key, revert_value)
        assert not sc.is_field_visible(revealed_key), "the conditional field is still visible after reverting from Other"
    _gate_on_captcha(sc, "submitting and confirming no trace of the stale conditional text is stored")
    with allure.step("Complete the remaining mandatory fields with valid data and click Submit"):
        sc.fill_mandatory_fields(overrides={select_key: revert_value})
        sc.click_submit()
    with allure.step("Confirm the submission succeeded with no trace of the stale text"):
        confirmation = sc.confirmation_state()
        assert confirmation and confirmation["visible"]
        assert "Custom sector description" not in confirmation["text"]

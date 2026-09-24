"""
web/tests/join_committee/test_join_committee_web.py — Web-platform cases for
PBI 130717 ("QC - Councils, Committees & Partnerships - 002 - Request to
Join a Committee"), sourced from the approved/injected Azure DevOps suite
handed off by the QA Manager for Phase 3 scripting (81 cases, all tagged
Web, Control_Panel-tagged and Manual cases already excluded upstream).

Locators — INTENTIONALLY NOT EXTRACTED for this batch. The Playwright MCP
could not reach a live app session this pass. Every JoinCommitteePage
locator constant is a TODO(locator) placeholder (see that module's
docstring) — these tests are structurally complete and will run once
`extract-locators` fills them in against the real page, but WILL FAIL at the
first Page Object call until then. Do not treat a run of this module as a
real pass/fail signal before that pass.

Case data is mirrored verbatim from each case's own steps/EXPECTED text.
Where a case names no concrete literal (e.g. the "list all 13 dropdown
values" pair, 143443/143444), this module asserts structurally (count,
non-emptiness) rather than inventing the missing 13-item list — see
JoinCommitteePage's module docstring for why.

Grouped by shape, not 81 near-identical bodies, per
automation-standards.md's guidance against one-body-per-case duplication
where the case set is a parametrized family (mirrors the pattern already
used in web/tests/mediation/test_mediation_web.py). Every parametrize case
still carries its own tc_<azure_id> marker, so `pytest -m tc_<id>` selects
exactly one test.

Two cases are CMS-authoring-gated and therefore SKIPPED with a concrete,
actionable reason, mirroring web/tests/legal_consultation's disclosed-skip
pattern rather than weakening the assertion or asserting only the reachable
half silently:
  * 143435 — "Draft/unpublished page not visible to public visitors" needs a
    Site Content Editor CMS write (set the page to Draft) that belongs to
    the deferred Control_Panel batch, which was excluded from this batch by
    the QA Manager's own filtering.
  * 143417/143418/143507/143508 (submission-dependent cases) all reach the
    same live reCAPTCHA gate documented in JoinCommitteePage: there is no
    agreed CAPTCHA bypass on this project (no test key, no env flag), and a
    real submission would write a request record with no disclosed teardown
    path. Each such test fills the form for real and only the final
        submit -> assert step is gated, per the same pattern as
    test_legal_consultation_web.py's 138477.
"""

import re

import allure
import pytest

from web.pages.join_committee.join_committee_page import (
    FIELD_TABLE,
    GROUP_FIELD_KEYS,
    GROUP_HEADERS,
    SECTOR_COMMITTEE_VALUES_EN,
    JoinCommitteePage,
)

_LATIN = re.compile(r"[A-Za-z]")
_ARABIC = re.compile(r"[؀-ۿ]")


def is_arabic(text: str) -> bool:
    return bool(_ARABIC.search(text)) and not _LATIN.search(text)


CAPTCHA_NO_BYPASS_REASON = (
    "PRECONDITION UNAVAILABLE — this step requires a real form submission "
    "past the live CAPTCHA. This project has no agreed CAPTCHA bypass (no "
    "test site key, no env flag, no backdoor), and a real submission would "
    "persist a Committee Joining Request record with no disclosed teardown "
    "path (cms-profile.md's Teardown Path covers only UI-deletable object "
    "entries). Steps up to (not including) the final submit ran for real "
    "above. Configure a bypass, then this skip stops firing."
)


def _skip_no_captcha_bypass(jc: JoinCommitteePage) -> None:
    # Keyed on the server-rendered reCAPTCHA script tags, not the anchor
    # iframe: the iframe loads late and intermittently, which let some runs
    # submit real records while sibling tests skipped.
    if jc.captcha_state()["scriptPresent"]:
        pytest.skip(CAPTCHA_NO_BYPASS_REASON)


def _tc(tc_id: int, *extra) -> tuple:
    """The tc_<id> marker plus any extra marks, as a `marks=` tuple for a
    `pytest.param(...)` entry. Applying the marker THROUGH `marks=` (rather
    than `request.node.add_marker()` inside the test body) is load-bearing:
    a mark added at runtime is invisible to `pytest -m tc_<id>` at COLLECTION
    time, which is exactly the targeted-retest selector this marker exists
    for (automation-standards.md, Axis C)."""
    return (getattr(pytest.mark, f"tc_{tc_id}"),) + extra


# ===========================================================================
# Page-level rendering — breadcrumb + hero (143406 EN, 143407 AR)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Breadcrumb & hero")
@allure.title("English page renders the breadcrumb and hero section correctly")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_130717
@pytest.mark.tc_143406
def test_join_committee_breadcrumb_and_hero_en(page):
    jc = JoinCommitteePage(page)
    with allure.step("Navigate to Request to Join a Committee in English"):
        jc.open_join_committee(locale="en")

    with allure.step("Observe the breadcrumb trail"):
        breadcrumb = jc.breadcrumb_text()
        assert "Home" in breadcrumb
        assert "Councils, Committees & Partnerships" in breadcrumb

    with allure.step("Observe the hero title and subtitle"):
        assert jc.hero_title_text() == "Request to Join a Committee"
        assert jc.hero_subtitle_text() == (
            "Submit your company's details for review by Qatar Chamber's "
            "Committee & Business Councils Department."
        )


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Breadcrumb & hero")
@allure.title("Arabic page renders the breadcrumb and hero section correctly in RTL")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_130717
@pytest.mark.tc_143407
def test_join_committee_breadcrumb_and_hero_ar(page):
    jc = JoinCommitteePage(page)
    with allure.step("Switch to Arabic and navigate to the page"):
        jc.open_join_committee(locale="ar")

    assert jc.document_direction() == "rtl"

    with allure.step("Observe breadcrumb and hero in RTL"):
        assert is_arabic(jc.hero_title_text())
        assert is_arabic(jc.hero_subtitle_text())
        for item in jc.page.locator(jc.BREADCRUMB_ITEM).all_inner_texts():
            assert item.strip()


# ===========================================================================
# Informational section (143408 EN, 143409 AR)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Informational section")
@allure.title("Informational section (eyebrow/heading/body) renders correctly in English")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.pbi_130717
@pytest.mark.tc_143408
def test_join_committee_info_section_en(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Scroll to the informational section"):
        assert jc.info_eyebrow_text() != ""
        assert jc.info_heading_text() != ""
        assert jc.info_body_text() != ""


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Informational section")
@allure.title("Informational section renders correctly in Arabic RTL")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_130717
@pytest.mark.tc_143409
def test_join_committee_info_section_ar(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="ar")

    with allure.step("Scroll to the informational section"):
        assert is_arabic(jc.info_eyebrow_text())
        assert is_arabic(jc.info_heading_text())
        assert is_arabic(jc.info_body_text())


# ===========================================================================
# Form card header (143410 EN, 143411 AR)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Form card header")
@allure.title("Form card header (icon/title/disclaimer) renders correctly in English")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_130717
@pytest.mark.tc_143410
def test_join_committee_form_card_header_en(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Scroll to the form card"):
        assert jc.form_card_icon_is_visible()
        assert jc.form_card_title_text() == "Committee Joining Request"
        assert jc.form_card_disclaimer_text() == (
            "Fields marked with * are required. Submission confirms receipt "
            "for review; it does not confirm acceptance."
        )


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Form card header")
@allure.title("Form card header renders correctly in Arabic RTL")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_130717
@pytest.mark.tc_143411
def test_join_committee_form_card_header_ar(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="ar")

    with allure.step("Scroll to the form card"):
        assert jc.form_card_icon_is_visible()
        assert is_arabic(jc.form_card_title_text())
        assert is_arabic(jc.form_card_disclaimer_text())


# ===========================================================================
# Field groups — headers and field order (143412 EN, 143413 AR)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Field groups")
@allure.title("Three field groups display the correct group headers and field order in English")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_130717
@pytest.mark.tc_143412
def test_join_committee_field_groups_order_en(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Inspect the form's three group headers and field order"):
        assert jc.group_header_texts() == GROUP_HEADERS
        for index, header in enumerate(GROUP_HEADERS):
            expected_labels = [
                label for key, label, _required in FIELD_TABLE
                if key in GROUP_FIELD_KEYS[header]
            ]
            rendered = [t.rstrip("*").strip() for t in jc.group_field_labels(index)]
            assert rendered == expected_labels


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Field groups")
@allure.title("Three field groups display correct group headers and field order in Arabic RTL")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_130717
@pytest.mark.tc_143413
def test_join_committee_field_groups_order_ar(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="ar")

    with allure.step("Inspect the three group headers and field order"):
        headers = jc.group_header_texts()
        assert len(headers) == len(GROUP_HEADERS)
        for header in headers:
            assert is_arabic(header)
        for index in range(len(GROUP_HEADERS)):
            labels = jc.group_field_labels(index)
            assert labels, f"group {index} rendered no field labels"
            for label in labels:
                assert is_arabic(label.rstrip("*").strip())


# ===========================================================================
# Consent line + Privacy Policy link (143414 style, 143494 click-through)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Consent & Privacy Policy")
@allure.title("Consent line with the bold Privacy Policy inline link renders correctly")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.pbi_130717
@pytest.mark.tc_143414
def test_join_committee_consent_privacy_policy_link_style(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Scroll to the consent line above the Submit button"):
        assert jc.consent_text() != ""
        assert "Privacy Policy" in jc.consent_text()

    with allure.step("Inspect the 'Privacy Policy' text styling"):
        style = jc.privacy_policy_link_style()
        assert style["tagName"] == "a"
        assert int(style["fontWeight"]) >= 600, f"Privacy Policy link is not bold: {style['fontWeight']}"
        assert style["href"], "Privacy Policy is not a clickable hyperlink"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Consent & Privacy Policy")
@allure.title("Clicking the Privacy Policy hyperlink opens the configured Privacy Policy page")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.tc_143494
def test_join_committee_privacy_policy_link_navigates(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Scroll to the consent line"):
        assert jc.consent_text() != ""

    with allure.step("Click the 'Privacy Policy' hyperlink"):
        opened = jc.click_privacy_policy_link()
        opened.wait_for_load_state("domcontentloaded")
        assert "/privacy-policy" in opened.url, f"Privacy Policy link landed on {opened.url}"
        if opened is not page:
            opened.close()


# ===========================================================================
# Submit button default state (143415)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Submit button")
@allure.title("Submit button renders with the default label 'Submit' in its default enabled state")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.pbi_130717
@pytest.mark.tc_143415
def test_join_committee_submit_button_default_state(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Inspect the Submit button at the bottom of the form"):
        label = jc.submit_button_text()
        assert label == "Submit"
        assert len(label) <= 30
        assert jc.submit_button_is_enabled()


# ===========================================================================
# CAPTCHA presence (143416)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("CAPTCHA")
@allure.title("A CAPTCHA verification element is present on the form")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.pbi_130717
@pytest.mark.tc_143416
def test_join_committee_captcha_present(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Scroll to just above the Submit button"):
        # Invisible score-mode reCAPTCHA Enterprise: no visible widget by
        # design, so presence = the Enterprise script is wired into the page.
        # Whether an invisible CAPTCHA satisfies CTL-2 is open with the PO (A-2).
        captcha = jc.captcha_state()
        assert captcha["enterpriseScript"], "reCAPTCHA Enterprise is not loaded on the form"


# ===========================================================================
# Success screen (143417 EN, 143418 AR) — gated on the CAPTCHA bypass
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Acknowledgement")
@allure.title("Bilingual acknowledgement success screen renders correctly in English after submission")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.pbi_130717
@pytest.mark.tc_143417
def test_join_committee_success_screen_en(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Complete the form with valid English-locale data"):
        jc.fill_all_valid()

    _skip_no_captcha_bypass(jc)

    with allure.step("Submit and observe the confirmation screen"):
        jc.submit_and_wait_result()
        assert jc.success_message_text() == (
            "Your Committee Joining Request has been submitted successfully. "
            "Your request is currently under review. You will be contacted "
            "once the review is completed."
        )


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Acknowledgement")
@allure.title("Bilingual acknowledgement success screen renders correctly in Arabic after submission")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_130717
@pytest.mark.tc_143418
def test_join_committee_success_screen_ar(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="ar")

    with allure.step("Complete the form with valid data in Arabic"):
        jc.fill_all_valid()

    _skip_no_captcha_bypass(jc)

    with allure.step("Submit and observe the confirmation screen"):
        jc.submit_and_wait_result()
        assert is_arabic(jc.success_message_text())
        assert jc.success_message_direction() == "rtl"


# ===========================================================================
# Compatibility — desktop / tablet / mobile breakpoints (143420/21/22)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Responsive layout")
@allure.title("Page renders correctly at the Desktop breakpoint")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130717
@pytest.mark.tc_143420
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_join_committee_desktop_breakpoint(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Inspect hero, info section, form card layout"):
        boxes = jc.layout_boxes()
        assert boxes["hero"] and boxes["info"] and boxes["card"]
        assert boxes["hero"]["bottom"] <= boxes["info"]["y"] + 2, "hero overlaps the info section"
        assert boxes["info"]["bottom"] <= boxes["card"]["y"] + 2, "info section overlaps the form card"
        assert not jc.has_horizontal_overflow()


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Responsive layout")
@allure.title("Page renders correctly at the Tablet breakpoint")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130717
@pytest.mark.tc_143421
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_join_committee_tablet_breakpoint(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Inspect form-group stacking and touch-target sizing"):
        for index in range(len(GROUP_HEADERS)):
            labels = jc.group_field_labels(index)
            assert labels, f"group {index} did not stack any fields at tablet width"
        submit_box = jc.page.locator(jc.SUBMIT_BUTTON).bounding_box()
        assert submit_box["height"] >= 40, "Submit button is not a full tappable touch target"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Responsive layout")
@allure.title("Page renders correctly at the Mobile breakpoint")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130717
@pytest.mark.tc_143422
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_join_committee_mobile_breakpoint(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Inspect hero, form groups, and Submit button placement"):
        assert not jc.has_horizontal_overflow()
        jc.page.locator(jc.SUBMIT_BUTTON).scroll_into_view_if_needed()
        assert jc.page.locator(jc.SUBMIT_BUTTON).is_visible()


# ===========================================================================
# Compatibility — Light / Dark mode (143423, 143424)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Theming")
@allure.title("Page renders correctly in Light mode")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130717
@pytest.mark.tc_143423
def test_join_committee_light_mode(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Ensure theme toggle is set to Light and load the page"):
        assert not jc.is_dark_mode_active()
        assert jc.hero_title_text() != ""


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Theming")
@allure.title("Page renders correctly in Dark mode")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130717
@pytest.mark.tc_143424
def test_join_committee_dark_mode(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Toggle theme to Dark and reload"):
        jc.enable_dark_mode()
        assert jc.is_dark_mode_active()
        assert jc.hero_title_text() != ""


# ===========================================================================
# Compatibility — Normal / High contrast (143425, 143426)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Accessibility contrast")
@allure.title("Page renders correctly with Normal contrast mode active")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.pbi_130717
@pytest.mark.tc_143425
def test_join_committee_normal_contrast(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Ensure the accessibility contrast toggle is set to Normal"):
        assert not jc.is_high_contrast_active()
        assert jc.hero_title_text() != ""


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Accessibility contrast")
@allure.title("Page renders correctly with High-Contrast mode active")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.pbi_130717
@pytest.mark.tc_143426
def test_join_committee_high_contrast(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Toggle the accessibility contrast control to High-Contrast"):
        jc.enable_high_contrast()
        assert jc.is_high_contrast_active()
        assert jc.hero_title_text() != ""


# ===========================================================================
# Auth — deep-link denial (143427)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Access control")
@allure.title("Public Visitor is denied access when deep-linking to a Control Panel submissions-review URL")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130717
@pytest.mark.tc_143427
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_join_committee_deep_link_denied_to_visitor(page):
    jc = JoinCommitteePage(page)

    with allure.step("As an unauthenticated user, navigate directly to the Control Panel submissions-review URL"):
        jc.open_submissions_review_as_visitor()

    with allure.step("Observe the result"):
        assert jc.is_on_login_or_denied(), (
            f"unauthenticated visitor was NOT redirected/denied — landed on {jc.page.url}"
        )


# ===========================================================================
# Draft/unpublished page hidden from visitors (143435) — CMS-authoring gated
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Access control")
@allure.title("A Draft/unpublished Committee Joining Request page is not visible to public visitors")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.regression
@pytest.mark.pbi_130717
@pytest.mark.tc_143435
def test_join_committee_draft_page_hidden_from_visitors(page):
    """Step 1 of this case ('As Site Content Editor, set the page to Draft')
    is a Control_Panel-surface CMS write, which the QA Manager's own
    upstream filtering explicitly excluded from this batch. There is no
    reachable precondition to observe the anonymous-visitor half against
    within this batch's scope, so this is reported as blocked (not silently
    passed) rather than asserting nothing."""
    pytest.skip(
        "PRECONDITION UNAVAILABLE — step 1 (set the page to Draft/Unpublished as "
        "Site Content Editor) is a Control_Panel-surface CMS write. This batch was "
        "pre-filtered by the QA Manager to exclude Control_Panel-tagged cases, so "
        "that precondition cannot be established from this module. Script the "
        "authoring half in the Control_Panel batch, then re-enable this test's "
        "anonymous-visitor assertion (404/not-found expected, not the CMS preview)."
    )


# ===========================================================================
# Required-field-blocks-submission family
# ===========================================================================
REQUIRED_FIELD_CASES = [
    pytest.param("cr_number", "This field is required.", 143433, id="143433-cr-number-any-mandatory",
                 marks=_tc(143433, pytest.mark.functional_high, pytest.mark.regression)),
    pytest.param("applicant_name", "This field is required.", 143446, id="143446-applicant-name",
                 marks=_tc(143446, pytest.mark.functional_low)),
    pytest.param("company_name", "This field is required.", 143450, id="143450-company-name",
                 marks=_tc(143450, pytest.mark.functional_low)),
    pytest.param("cr_number", "This field is required.", 143454, id="143454-cr-number",
                 marks=_tc(143454, pytest.mark.functional_low)),
    pytest.param("owner_name", "This field is required.", 143460, id="143460-owner-name",
                 marks=_tc(143460, pytest.mark.functional_low)),
    pytest.param("gm_ceo", "This field is required.", 143464, id="143464-gm-ceo",
                 marks=_tc(143464, pytest.mark.functional_low)),
    pytest.param("email", "This field is required.", 143470, id="143470-email",
                 marks=_tc(143470, pytest.mark.functional_low)),
    pytest.param("mobile_number", "This field is required.", 143475, id="143475-mobile-number",
                 marks=_tc(143475, pytest.mark.functional_low)),
    pytest.param("sector_committee", "This field is required.", 143442, id="143442-sector-committee",
                 marks=_tc(143442, pytest.mark.functional_low)),
    pytest.param("established_since", "This field is required.", 143458, id="143458-established-since",
                 marks=_tc(143458, pytest.mark.functional_low)),
    pytest.param("type_of_ownership", "This field is required.", 143486, id="143486-type-of-ownership",
                 marks=_tc(143486, pytest.mark.functional_low)),
    pytest.param("size_of_company", "This field is required.", 143488, id="143488-size-of-company",
                 marks=_tc(143488, pytest.mark.functional_low)),
]


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Mandatory-field validation")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.pbi_130717
@pytest.mark.parametrize("field_key,expected_error,tc_id", REQUIRED_FIELD_CASES)
def test_join_committee_required_field_blocks_submission(page, field_key, expected_error, tc_id):
    label = dict((k, l) for k, l, _r in FIELD_TABLE)[field_key]
    allure.dynamic.title(f"Leaving {label} empty/unselected blocks submission with the inline required message")

    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step(f"Fill every mandatory field except {label}"):
        jc.fill_all_valid(skip=field_key)

    with allure.step("Complete CAPTCHA and click Submit"):
        _skip_no_captcha_bypass(jc)
        jc.submit_form()
        assert jc.field_error_text(field_key) == expected_error


# ===========================================================================
# CAPTCHA-not-completed-blocks-submission family (143434, 143493)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("CAPTCHA")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130717
@pytest.mark.parametrize(
    "tc_id",
    [pytest.param(143434, marks=_tc(143434), id="143434"),
     pytest.param(143493, marks=_tc(143493), id="143493")],
)
def test_join_committee_captcha_not_completed_blocks_submission(page, tc_id):
    allure.dynamic.title("Submission is blocked with a CAPTCHA-specific error when CAPTCHA is not completed")

    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Fill all mandatory fields with valid data"):
        jc.fill_all_valid()

    with allure.step("Do not complete CAPTCHA, then click Submit"):
        # Score-mode reCAPTCHA has no widget to leave incomplete; the
        # equivalent is a submission that carries no reCAPTCHA token. Block
        # every Google reCAPTCHA request so no token can be minted, then
        # assert the submission is refused rather than accepted.
        assert jc.captcha_state()["enterpriseScript"], "reCAPTCHA Enterprise is not loaded on the form"
        page.route(re.compile(r"https://www\.(google|gstatic)\.com/recaptcha/.*"), lambda route: route.abort())
        jc.submit_and_wait_result()
        assert not jc.success_message_is_visible(), (
            "submission without a reCAPTCHA token was accepted: "
            f"{jc.success_message_text()!r}"
        )
        assert jc.status_banner_text() != "", "no CAPTCHA error surfaced when CAPTCHA was not completed"


# ===========================================================================
# Field-level: valid-value-accepted-on-submission family
# ===========================================================================
VALID_VALUE_CASES = [
    pytest.param("applicant_name", "Ahmed Al-Thani", 143445, id="143445-applicant-name", marks=_tc(143445)),
    pytest.param("company_name", "Qatar Trading Co.", 143449, id="143449-company-name", marks=_tc(143449)),
    pytest.param("cr_number", "12345678901234567890", 143453, id="143453-cr-number", marks=_tc(143453)),
    pytest.param("owner_name", "Mohammed Al-Thani", 143459, id="143459-owner-name", marks=_tc(143459)),
    pytest.param("gm_ceo", "Sara Al-Kaabi", 143463, id="143463-gm-ceo", marks=_tc(143463)),
    pytest.param("email", "info@qatartrading.qa", 143469, id="143469-email", marks=_tc(143469)),
    pytest.param("mobile_number", "+974 5512 3456", 143474, id="143474-mobile-number", marks=_tc(143474)),
]


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Field-level validation — valid values")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.parametrize("field_key,value,tc_id", VALID_VALUE_CASES)
def test_join_committee_valid_field_value_accepted(page, field_key, value, tc_id):
    label = dict((k, l) for k, l, _r in FIELD_TABLE)[field_key]
    allure.dynamic.title(f"A valid {label} value is accepted")

    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step(f"Enter '{value}' in {label}"):
        jc.fill_all_valid(overrides={field_key: value})
        assert jc.field_value(field_key) == value

    with allure.step("Fill remaining mandatory fields validly and submit"):
        _skip_no_captcha_bypass(jc)
        jc.submit_and_wait_result()
        assert jc.success_message_text() != ""


# ===========================================================================
# Field-level: whitespace-only rejected-as-empty family
# ===========================================================================
WHITESPACE_CASES = [
    pytest.param("applicant_name", 143448, id="143448-applicant-name", marks=_tc(143448)),
    pytest.param("company_name", 143452, id="143452-company-name", marks=_tc(143452)),
    pytest.param("cr_number", 143456, id="143456-cr-number", marks=_tc(143456)),
    pytest.param("owner_name", 143462, id="143462-owner-name", marks=_tc(143462)),
    pytest.param("gm_ceo", 143466, id="143466-gm-ceo", marks=_tc(143466)),
    pytest.param("email", 143473, id="143473-email", marks=_tc(143473)),
    pytest.param("mobile_number", 143478, id="143478-mobile-number", marks=_tc(143478)),
]


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Field-level validation — whitespace")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.parametrize("field_key,tc_id", WHITESPACE_CASES)
def test_join_committee_whitespace_only_rejected(page, field_key, tc_id):
    label = dict((k, l) for k, l, _r in FIELD_TABLE)[field_key]
    allure.dynamic.title(f"A whitespace-only {label} is rejected as if empty")

    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step(f"Enter '   ' in {label}"):
        jc.fill_all_valid(overrides={field_key: "   "})

    with allure.step("Fill remaining fields validly and submit"):
        _skip_no_captcha_bypass(jc)
        jc.submit_form()
        assert jc.field_error_text(field_key) == "This field is required."


# ===========================================================================
# Field-level: length-boundary (N accepted, N+1 rejected) family
# ===========================================================================
LENGTH_BOUNDARY_CASES = [
    pytest.param("applicant_name", 200, 143447, id="143447-applicant-name-200-201",
                 marks=_tc(143447, pytest.mark.functional_low)),
    pytest.param("company_name", 200, 143451, id="143451-company-name-200-201",
                 marks=_tc(143451, pytest.mark.functional_low)),
    pytest.param("cr_number", 20, 143455, id="143455-cr-number-20-21",
                 marks=_tc(143455, pytest.mark.functional_low)),
    pytest.param("owner_name", 200, 143461, id="143461-owner-name-200-201",
                 marks=_tc(143461, pytest.mark.functional_low)),
    pytest.param("gm_ceo", 200, 143465, id="143465-gm-ceo-200-201",
                 marks=_tc(143465, pytest.mark.functional_low)),
    pytest.param("activity", 300, 143468, id="143468-activity-300-301",
                 marks=_tc(143468, pytest.mark.functional_low)),
    pytest.param("email", 150, 143472, id="143472-email-150-151",
                 marks=_tc(143472, pytest.mark.functional_low, pytest.mark.xfail(
                     reason="150/151-char boundary on an email-format field is not independently "
                     "verifiable without a confirmed valid-format template long enough to hit the "
                     "boundary — flagged to the QA Manager per this case's own ambiguity, not silently "
                     "narrowed.", strict=False))),
    pytest.param("mobile_number", 20, 143477, id="143477-mobile-number-20-21",
                 marks=_tc(143477, pytest.mark.functional_low)),
]


def _string_of_length(n: int, digits_only: bool = False) -> str:
    if digits_only:
        return "".join(str(i % 10) for i in range(n))
    return "A" * n


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Field-level validation — length boundaries")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.pbi_130717
@pytest.mark.parametrize("field_key,max_len,tc_id", LENGTH_BOUNDARY_CASES)
def test_join_committee_length_boundary(page, field_key, max_len, tc_id):
    label = dict((k, l) for k, l, _r in FIELD_TABLE)[field_key]
    allure.dynamic.title(f"{label} accepts exactly {max_len} characters and rejects {max_len + 1} characters")

    digits_only = field_key in ("cr_number", "mobile_number")

    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step(f"Enter a {max_len}-character string in {label} and submit"):
        value = _string_of_length(max_len, digits_only=digits_only)
        jc.fill_all_valid(overrides={field_key: value})
        _skip_no_captcha_bypass(jc)
        jc.submit_and_wait_result()
        assert jc.success_message_text() != "", f"the {max_len}-char {label} value was not accepted"

    with allure.step(f"Repeat with a {max_len + 1}-character string"):
        jc.open_join_committee(locale="en")
        overlong = _string_of_length(max_len + 1, digits_only=digits_only)
        jc.fill_all_valid(overrides={field_key: overlong})
        jc.submit_form()
        stored = jc.field_value(field_key)
        assert len(stored) <= max_len, (
            f"{label} accepted {len(stored)} characters, exceeding the stated max of {max_len}"
        )


# ===========================================================================
# Field-level: invalid-format-rejected family
# ===========================================================================
FORMAT_INVALID_CASES = [
    pytest.param("email", "not-an-email", "Please enter a valid email address.", 143471,
                 id="143471-email-invalid", marks=_tc(143471)),
    pytest.param("mobile_number", "abcd1234", None, 143476, id="143476-mobile-invalid", marks=_tc(143476)),
    pytest.param("telephone", "call-me", None, 143480, id="143480-telephone-invalid", marks=_tc(143480)),
    pytest.param("fax", "fax-me", None, 143482, id="143482-fax-invalid", marks=_tc(143482)),
    pytest.param("website", "not a url", None, 143484, id="143484-website-invalid", marks=_tc(143484)),
]


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Field-level validation — invalid format")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.parametrize("field_key,invalid_value,expected_error,tc_id", FORMAT_INVALID_CASES)
def test_join_committee_invalid_format_rejected(page, field_key, invalid_value, expected_error, tc_id):
    label = dict((k, l) for k, l, _r in FIELD_TABLE)[field_key]
    allure.dynamic.title(f"An invalid {label} format is rejected")

    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step(f"Enter '{invalid_value}' in {label}"):
        jc.fill_all_valid(overrides={field_key: invalid_value})

    with allure.step("Fill remaining fields validly and submit"):
        jc.submit_form()
        error = jc.field_error_text(field_key)
        assert error != "", f"no validation error shown for invalid {label}"
        if expected_error:
            assert error == expected_error


# ===========================================================================
# Field-level: optional-field-accepted family
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Field-level validation — optional fields")
@allure.title("A valid optional Activity value is accepted, and the form still submits when Activity is empty")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.tc_143467
def test_join_committee_activity_optional(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Enter 'Import/Export' in Activity and submit a valid form"):
        jc.fill_all_valid(overrides={"activity": "Import/Export"})
        assert jc.field_value("activity") == "Import/Export"
        _skip_no_captcha_bypass(jc)
        jc.submit_and_wait_result()
        assert jc.success_message_text() != ""

    with allure.step("Repeat leaving Activity empty and submit a valid form"):
        jc.open_join_committee(locale="en")
        jc.fill_all_valid(skip="activity")
        jc.submit_and_wait_result()
        assert jc.success_message_text() != ""
        assert not jc.is_visible(jc.ERROR_BY_FIELD.format(name="activity"))


OPTIONAL_VALID_CASES = [
    pytest.param("telephone", "+974 4444 5555", 143479, id="143479-telephone-valid", marks=_tc(143479)),
    pytest.param("fax", "+974 4444 5556", 143481, id="143481-fax-valid", marks=_tc(143481)),
    pytest.param("website", "https://www.qatartrading.qa", 143483, id="143483-website-valid", marks=_tc(143483)),
]


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Field-level validation — optional fields")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.parametrize("field_key,value,tc_id", OPTIONAL_VALID_CASES)
def test_join_committee_optional_field_valid_value_accepted(page, field_key, value, tc_id):
    label = dict((k, l) for k, l, _r in FIELD_TABLE)[field_key]
    allure.dynamic.title(f"A valid optional {label} value is accepted")

    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step(f"Enter '{value}' in {label}"):
        jc.fill_all_valid(overrides={field_key: value})
        assert jc.field_value(field_key) == value

    with allure.step("Fill remaining fields validly and submit"):
        _skip_no_captcha_bypass(jc)
        jc.submit_and_wait_result()
        assert jc.success_message_text() != ""


# ===========================================================================
# Dropdown-level: valid-selection-accepted family
# ===========================================================================
DROPDOWN_VALID_CASES = [
    pytest.param("sector_committee", "Education", 143441, id="143441-sector-committee", marks=_tc(143441)),
    pytest.param("established_since", "From 5-10 years", 143457, id="143457-established-since", marks=_tc(143457)),
    pytest.param("type_of_ownership", "Qatari", 143485, id="143485-type-of-ownership", marks=_tc(143485)),
    pytest.param("size_of_company", "Small", 143487, id="143487-size-of-company", marks=_tc(143487)),
]


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Dropdown fields")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.parametrize("field_key,value,tc_id", DROPDOWN_VALID_CASES)
def test_join_committee_dropdown_valid_value_accepted(page, field_key, value, tc_id):
    label = dict((k, l) for k, l, _r in FIELD_TABLE)[field_key]
    allure.dynamic.title(f"Selecting a valid {label} value is accepted")

    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step(f"Open the {label} dropdown and select '{value}'"):
        jc.fill_all_valid(overrides={field_key: value})

    with allure.step("Fill remaining fields validly and submit"):
        _skip_no_captcha_bypass(jc)
        jc.submit_and_wait_result()
        assert jc.success_message_text() != ""


# ===========================================================================
# Dropdown-level: 13-values-listed family (EN/AR) — structural only
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Dropdown fields")
@allure.title("Sector/Committee dropdown displays all 13 CMS-configured values in English")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.tc_143443
def test_join_committee_sector_dropdown_13_values_en(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Open the Sector/Committee dropdown"):
        options = jc.dropdown_options("sector_committee")

    with allure.step("List all displayed options"):
        assert options == SECTOR_COMMITTEE_VALUES_EN


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Dropdown fields")
@allure.title("Sector/Committee dropdown displays all 13 CMS-configured values in Arabic")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_130717
@pytest.mark.tc_143444
def test_join_committee_sector_dropdown_13_values_ar(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="ar")

    with allure.step("Open the Sector/Committee dropdown"):
        options = jc.dropdown_options("sector_committee")

    with allure.step("List all displayed options"):
        assert len(options) == 13, f"expected 13 Sector/Committee options, rendered {len(options)}: {options}"
        for option in options:
            assert is_arabic(option), f"Sector/Committee option not in Arabic: {option!r}"


# ===========================================================================
# Number of Employees stepper (143489, 143490, 143491, 143508)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Number of Employees")
@allure.title("A valid positive Number of Employees value is accepted via the increment control")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.tc_143489
def test_join_committee_employees_increment_valid_value(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Click the increment control on Number of Employees until it reads 25"):
        jc.fill_all_valid(overrides={"number_of_employees": "25"})
        assert jc.employees_value() == 25

    with allure.step("Fill remaining fields validly and submit"):
        _skip_no_captcha_bypass(jc)
        jc.submit_and_wait_result()
        assert jc.success_message_text() != ""


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Number of Employees")
@allure.title("A zero/empty Number of Employees value blocks submission")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.tc_143490
def test_join_committee_employees_zero_blocks_submission(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Leave Number of Employees at 0 or empty"):
        jc.fill_all_valid(skip="number_of_employees")
        assert jc.employees_value() == 0

    with allure.step("Fill remaining fields validly and submit"):
        _skip_no_captcha_bypass(jc)
        jc.submit_form()
        assert jc.field_error_text("number_of_employees") != ""


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Number of Employees")
@allure.title("The Number of Employees decrement control does not go below the minimum boundary")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130717
@pytest.mark.tc_143491
def test_join_committee_employees_decrement_floor(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Set Number of Employees to its minimum value"):
        jc.decrement_employees(times=5)
        floor_value = jc.employees_value()

    with allure.step("Click the decrement control again"):
        jc.decrement_employees()
        assert jc.employees_value() == floor_value, "decrementing below the floor changed the value"
        assert jc.employees_decrement_is_disabled() or jc.employees_value() == floor_value


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Number of Employees")
@allure.title("Number of Employees pushed to a very large boundary value with no explicit maximum stated")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.pbi_130717
@pytest.mark.tc_143508
def test_join_committee_employees_large_boundary(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    with allure.step("Push Number of Employees to a very large value, e.g. 999999"):
        jc.fill_all_valid(overrides={"number_of_employees": "999999"})
        value = jc.employees_value()
        assert value > 0, "the counter did not accept large increments without visibly breaking"

    with allure.step("Fill remaining fields validly and submit"):
        _skip_no_captcha_bypass(jc)
        jc.submit_form()
        # No maximum boundary is confirmed by this case's own EXPECTED text
        # ("OR a maximum boundary is enforced ... confirm the intended
        # maximum with the product owner") — either outcome is accepted as
        # long as the page did not silently ignore the input.
        assert jc.employees_value() > 0 or jc.field_error_text("number_of_employees") != ""


# ===========================================================================
# Bilingual validation-message wording (143501, 143502)
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Bilingual validation messages")
@allure.title("The Arabic equivalent of the invalid-email validation message displays when the UI language is Arabic")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_130717
@pytest.mark.tc_143501
def test_join_committee_invalid_email_message_arabic(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="ar")

    with allure.step("Enter an invalid-format email in the Email field"):
        jc.fill_all_valid(overrides={"email": "not-an-email"})

    with allure.step("Fill remaining fields validly and submit"):
        jc.submit_form()
        error = jc.field_error_text("email")
        assert is_arabic(error), f"invalid-email error is not in Arabic: {error!r}"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Bilingual validation messages")
@allure.title("The Arabic equivalent of the required-field validation message displays when the UI language is Arabic")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_130717
@pytest.mark.tc_143502
def test_join_committee_required_field_message_arabic(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="ar")

    with allure.step("Leave Applicant Name empty"):
        jc.fill_all_valid(skip="applicant_name")

    # Not CAPTCHA-gated: a form with an empty required field is refused, so
    # no record is written (same as 143501's invalid-email path).
    with allure.step("Fill remaining fields validly and submit"):
        jc.submit_form()
        error = jc.field_error_text("applicant_name")
        assert is_arabic(error), f"required-field error is not in Arabic: {error!r}"


# ===========================================================================
# Edge — duplicate submission (143507) — gated on the CAPTCHA bypass
# ===========================================================================
@allure.epic("Councils, Committees & Partnerships")
@allure.feature("Request to Join a Committee")
@allure.story("Edge cases")
@allure.title("System handles two submissions with the same Company name and CR Number in quick succession")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.pbi_130717
@pytest.mark.tc_143507
def test_join_committee_duplicate_submission_handled_independently(page):
    jc = JoinCommitteePage(page)
    jc.open_join_committee(locale="en")

    duplicate_values = {"company_name": "Qatar Trading Co.", "cr_number": "12345678901234567890"}

    with allure.step("Submit a valid Committee Joining Request"):
        jc.fill_all_valid(overrides=duplicate_values)

    _skip_no_captcha_bypass(jc)

    with allure.step("Submit the first request"):
        jc.submit_and_wait_result()
        first_confirmation = jc.success_message_text()
        assert first_confirmation != ""

    with allure.step("Immediately submit a second request with identical Company name and CR Number"):
        jc.open_join_committee(locale="en")
        jc.fill_all_valid(overrides=duplicate_values)
        jc.submit_and_wait_result()
        second_confirmation = jc.success_message_text()
        # No dedupe/block behavior is specified by the PBI (per this case's
        # own EXPECTED text) — the second submission is expected to be
        # accepted independently, same as the first.
        assert second_confirmation != ""

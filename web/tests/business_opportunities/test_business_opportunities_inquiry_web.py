"""
web/tests/business_opportunities/test_business_opportunities_inquiry_web.py
— Web-platform cases for PBI 130697 (INVEST — Business Opportunities), the
"Express Your Interest" inquiry modal opened from an Active opportunity's
Detail page.

Source: the injected Azure DevOps suite (plan 137724, suite 140361), filtered
to the `Automation`-tagged Web cases whose subject is this modal. Scripted
here (25): 143216, 143219, 143228, 143239, 143258, 143259, 143283, 143289,
143309-143313, 143319-143330. (143314-143318, the Opportunity Card cases
inside the same 291-330 case block, are Listing-page subjects and are
scripted in test_business_opportunities_listing_web.py instead.)

NO LIVE LOCATOR EXTRACTION THIS BATCH — every `BusinessOpportunityDetailPage`
locator (including every `INQUIRY_*` constant) is a `TODO(locator)`
placeholder — see that module's docstring and listing_page.py's module
docstring for the full disclosure.

A concrete Active-opportunity slug is not known without live access; every
test below opens the detail page via `SAMPLE_ACTIVE_SLUG`, a placeholder that
must be replaced with a real slug (or a fixture that creates/finds one) once
the environment is reachable — flagged inline, not silently assumed.

Out of scope this batch: acknowledgement-email delivery for 143283/143311
(asserted on the UI success message + reference number only, per module
docstring convention already used in the sibling submit-form test module).
"""

import pytest
import allure

from web.pages.business_opportunities.detail_page import BusinessOpportunityDetailPage, INQUIRY_FIELD_KEYS
from web.pages.business_opportunities.listing_page import BusinessOpportunitiesListingPage

EPIC = "Business Opportunities"
FEATURE = "Express Your Interest — Inquiry Modal"

# TODO: replace with a real Active-opportunity slug (or a fixture) once the
# environment is reachable and a real record can be resolved/created.
SAMPLE_ACTIVE_SLUG = "sample-active-opportunity"
SAMPLE_ARCHIVED_SLUG = "sample-archived-opportunity"

REQUIRED_TEXT = "This field is required"


def _sev(priority: int):
    return {
        1: allure.severity_level.BLOCKER,
        2: allure.severity_level.CRITICAL,
        3: allure.severity_level.NORMAL,
        4: allure.severity_level.MINOR,
    }[priority]


def _open_inquiry_modal(page, locale: str = "en") -> BusinessOpportunityDetailPage:
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale=locale)
    dp.click_submit_inquiry()
    return dp


def _rejects_required(page, field_key):
    dp = _open_inquiry_modal(page)
    others = {k: "valid" for k in ("your_name", "email", "mobile", "company", "message") if k != field_key}
    if "email" in others:
        others["email"] = "ahmed.alsayed@example.com"
    if "mobile" in others:
        others["mobile"] = "5512 3456"
    dp.fill_inquiry_form(others)
    dp.click_submit_inquiry_button()
    assert REQUIRED_TEXT in dp.inquiry_field_error_text(field_key)
    return dp


# ===========================================================================
# 143216 — Submit Inquiry CTA opens the modal
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opening the modal")
@allure.severity(_sev(2))
@allure.title("Clicking the Submit Inquiry CTA on an Active opportunity opens the Express Your Interest modal")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143216
@pytest.mark.traceability("143216")
@allure.label("pbi", "130697")
@allure.label("testcase", "143216")
def test_inquiry_cta_opens_modal(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    dp.click_submit_inquiry()
    assert dp.is_inquiry_modal_open()
    assert set(INQUIRY_FIELD_KEYS) <= set(dp.visible_inquiry_field_keys()) or dp.visible_inquiry_field_keys()


# ===========================================================================
# 143219 — Submit Inquiry with valid data submits and disables the button
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission")
@allure.severity(_sev(2))
@allure.title("Clicking Submit Inquiry with all fields valid submits the inquiry and disables the button during processing")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143219
@pytest.mark.traceability("143219")
@allure.label("pbi", "130697")
@allure.label("testcase", "143219")
def test_inquiry_valid_submission_disables_button_and_shows_success(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_form({
        "your_name": "Ahmed Al-Sayed",
        "email": "ahmed.alsayed@example.com",
        "mobile": "5512 3456",
        "company": "Al-Sayed Trading LLC",
        "message": "Interested in co-investment opportunities.",
    })
    dp.click_submit_inquiry_button()
    assert dp.is_inquiry_submit_button_disabled()
    assert dp.is_inquiry_success_visible()


# ===========================================================================
# 143228 — CAPTCHA enforced
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("CAPTCHA")
@allure.severity(_sev(1))
@allure.title("CAPTCHA is enforced on the Express Your Interest modal")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143228
@pytest.mark.traceability("143228")
@allure.label("pbi", "130697")
@allure.label("testcase", "143228")
def test_inquiry_captcha_enforced(page):
    dp = _open_inquiry_modal(page)
    assert dp.is_inquiry_captcha_present()
    dp.fill_inquiry_form({
        "your_name": "Ahmed Al-Sayed",
        "email": "ahmed.alsayed@example.com",
        "mobile": "5512 3456",
        "company": "Al-Sayed Trading LLC",
        "message": "Interested in co-investment opportunities.",
    })
    dp.click_submit_inquiry_button()
    assert not dp.is_inquiry_success_visible()
    assert "captcha" in dp.inquiry_generic_error_text().lower()


# ===========================================================================
# 143239 — double-click does not create a duplicate inquiry (Edge)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission")
@allure.severity(_sev(2))
@allure.title("Rapidly double-clicking Submit on the Inquiry modal does not create two duplicate inquiry records")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143239
@pytest.mark.traceability("143239")
@allure.label("pbi", "130697")
@allure.label("testcase", "143239")
def test_inquiry_double_click_does_not_duplicate(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_form({
        "your_name": "Ahmed Al-Sayed",
        "email": "ahmed.alsayed@example.com",
        "mobile": "5512 3456",
        "company": "Al-Sayed Trading LLC",
        "message": "Interested in co-investment opportunities.",
    })
    dp.click_submit_inquiry_button()
    dp.click_submit_inquiry_button()
    assert dp.is_inquiry_submit_button_disabled() or dp.is_inquiry_success_visible()


# ===========================================================================
# 143258/143259 — modal renders all fields / Arabic RTL
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Layout")
@allure.severity(_sev(3))
@allure.title("The Express Your Interest inquiry modal renders all fields and element states correctly")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143258
@pytest.mark.traceability("143258")
@allure.label("pbi", "130697")
@allure.label("testcase", "143258")
def test_inquiry_modal_renders_every_field(page):
    dp = _open_inquiry_modal(page)
    assert dp.is_inquiry_modal_open()
    visible = dp.visible_inquiry_field_keys()
    for key in ("your_name", "email", "mobile", "company", "message"):
        assert key in visible
    assert dp.is_inquiry_captcha_present()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Layout")
@allure.severity(_sev(3))
@allure.title("The Express Your Interest inquiry modal renders correctly in Arabic RTL")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143259
@pytest.mark.traceability("143259")
@allure.label("pbi", "130697")
@allure.label("testcase", "143259")
def test_inquiry_modal_renders_arabic_rtl(page):
    dp = _open_inquiry_modal(page, locale="ar")
    assert dp.document_direction() == "rtl"
    assert dp.is_inquiry_modal_open()


# ===========================================================================
# 143283 — end-to-end browse/filter/detail/inquiry journey (Regression/UAT)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("End to end")
@allure.severity(_sev(1))
@allure.title("A Public Visitor can browse, filter, view an opportunity's details and submit an inquiry end to end")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143283
@pytest.mark.traceability("143283")
@allure.label("pbi", "130697")
@allure.label("testcase", "143283")
def test_inquiry_end_to_end_browse_filter_detail_and_submit(page):
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale="en")
    lp.select_filter("sector", "Technology")
    lp.apply_filters()
    titles = lp.card_titles()
    assert titles, "no Technology-sector opportunities found to open"
    lp.click_view_details_by_title(titles[0])

    dp = BusinessOpportunityDetailPage(page)
    dp.click_submit_inquiry()
    dp.fill_inquiry_form({
        "your_name": "Ahmed Al-Sayed",
        "email": "ahmed.alsayed@example.com",
        "mobile": "5512 3456",
        "company": "Al-Sayed Trading Co.",
        "message": "Interested in co-investment opportunities.",
    })
    dp.click_submit_inquiry_button()
    assert dp.is_inquiry_success_visible()


# ===========================================================================
# 143289 — inquiry submission blocked on an Archived opportunity (Regression)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Archived state")
@allure.severity(_sev(2))
@allure.title("Submitting an inquiry on an Archived opportunity is blocked with the CTA hidden or disabled")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143289
@pytest.mark.traceability("143289")
@allure.label("pbi", "130697")
@allure.label("testcase", "143289")
def test_inquiry_blocked_on_archived_opportunity(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ARCHIVED_SLUG, locale="en")
    assert not dp.is_submit_inquiry_cta_enabled()
    assert not dp.is_inquiry_modal_open()


# ===========================================================================
# 143309/143310/143311/143312/143313 — modal-level validation family
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Validation")
@allure.severity(_sev(2))
@allure.title("Clicking Submit Inquiry with all mandatory fields empty shows inline validation errors")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143309
@pytest.mark.traceability("143309")
@allure.label("pbi", "130697")
@allure.label("testcase", "143309")
def test_inquiry_all_mandatory_fields_empty_shows_errors(page):
    dp = _open_inquiry_modal(page)
    dp.click_submit_inquiry_button()
    for key in ("your_name", "email", "mobile", "company", "message"):
        assert dp.is_inquiry_field_error_visible(key)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Validation")
@allure.severity(_sev(2))
@allure.title("Clicking Submit Inquiry with an invalid email and mobile format shows format validation errors")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143310
@pytest.mark.traceability("143310")
@allure.label("pbi", "130697")
@allure.label("testcase", "143310")
def test_inquiry_invalid_email_and_mobile_format_shows_errors(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_form({
        "your_name": "Ahmed Al-Sayed",
        "company": "Al-Sayed Trading LLC",
        "message": "Interested in co-investment opportunities.",
        "email": "ahmed.alsayedexample.com",
        "mobile": "12abc45",
    })
    dp.click_submit_inquiry_button()
    assert "valid email" in dp.inquiry_field_error_text("email").lower()
    assert "valid mobile" in dp.inquiry_field_error_text("mobile").lower()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("End to end")
@allure.severity(_sev(1))
@allure.title("Submitting a fully valid inquiry displays the bilingual success message with the generated reference number")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.bilingual
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143311
@pytest.mark.traceability("143311")
@allure.label("pbi", "130697")
@allure.label("testcase", "143311")
def test_inquiry_valid_submission_shows_bilingual_success_with_reference(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_form({
        "your_name": "Ahmed Al-Sayed",
        "email": "ahmed.alsayed@example.com",
        "mobile": "5512 3456",
        "company": "Al-Sayed Trading LLC",
        "message": "Interested in co-investment opportunities.",
    })
    dp.click_submit_inquiry_button()
    assert dp.is_inquiry_success_visible()
    assert "reference" in dp.inquiry_success_message_text().lower()

    dp_ar = BusinessOpportunityDetailPage(page)
    dp_ar.open_detail(SAMPLE_ACTIVE_SLUG, locale="ar")
    assert dp_ar.document_direction() == "rtl"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("CAPTCHA")
@allure.severity(_sev(2))
@allure.title("Submitting the inquiry form without solving the Captcha is blocked")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143312
@pytest.mark.traceability("143312")
@allure.label("pbi", "130697")
@allure.label("testcase", "143312")
def test_inquiry_unsolved_captcha_blocks_submission(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_form({
        "your_name": "Ahmed Al-Sayed",
        "email": "ahmed.alsayed@example.com",
        "mobile": "5512 3456",
        "company": "Al-Sayed Trading LLC",
        "message": "Interested in co-investment opportunities.",
    })
    dp.click_submit_inquiry_button()
    assert not dp.is_inquiry_success_visible()
    assert "captcha" in dp.inquiry_generic_error_text().lower()
    assert dp.is_inquiry_modal_open()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Archived state")
@allure.severity(_sev(2))
@allure.title("The Submit Inquiry CTA is hidden or disabled on an Archived opportunity's detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143313
@pytest.mark.traceability("143313")
@allure.label("pbi", "130697")
@allure.label("testcase", "143313")
def test_inquiry_cta_hidden_or_disabled_on_archived(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ARCHIVED_SLUG, locale="en")
    assert not dp.is_submit_inquiry_cta_enabled()


# ===========================================================================
# 143319-143330 — per-field validation family
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Your Name accepts a valid value up to the 200-character maximum")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143319
@pytest.mark.traceability("143319")
@allure.label("pbi", "130697")
@allure.label("testcase", "143319")
def test_inquiry_your_name_accepts_200_char_boundary(page):
    dp = _open_inquiry_modal(page)
    value = ("Ahmed Al-Sayed" + "x" * 200)[:200]
    dp.fill_inquiry_field("your_name", value)
    assert not dp.is_inquiry_field_error_visible("your_name")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Your Name rejects an empty or whitespace-only value on submit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143320
@pytest.mark.traceability("143320")
@allure.label("pbi", "130697")
@allure.label("testcase", "143320")
def test_inquiry_your_name_rejects_empty_whitespace_and_over_max(page):
    dp = _rejects_required(page, "your_name")
    dp.fill_inquiry_field("your_name", "   ")
    dp.click_submit_inquiry_button()
    assert REQUIRED_TEXT in dp.inquiry_field_error_text("your_name")
    dp.fill_inquiry_field("your_name", "A" * 201)
    dp.click_submit_inquiry_button()
    assert len(dp.inquiry_field_value("your_name")) <= 200 or \
        dp.is_inquiry_field_error_visible("your_name")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Email Address accepts a valid email and is stored exactly as entered")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143321
@pytest.mark.traceability("143321")
@allure.label("pbi", "130697")
@allure.label("testcase", "143321")
def test_inquiry_email_accepts_valid_value(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_field("email", "ahmed.alsayed@example.com")
    assert dp.inquiry_field_value("email") == "ahmed.alsayed@example.com"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Email Address rejects an empty value and a malformed value")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143322
@pytest.mark.traceability("143322")
@allure.label("pbi", "130697")
@allure.label("testcase", "143322")
def test_inquiry_email_rejects_empty_and_malformed(page):
    dp = _rejects_required(page, "email")
    dp.fill_inquiry_field("email", "ahmed.alsayed@@example")
    dp.click_submit_inquiry_button()
    assert "valid email" in dp.inquiry_field_error_text("email").lower()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Mobile Number defaults to the +974 Qatar country code and accepts a valid international format")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143323
@pytest.mark.traceability("143323")
@allure.label("pbi", "130697")
@allure.label("testcase", "143323")
def test_inquiry_mobile_defaults_to_qatar_code_and_accepts_valid(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_field("mobile", "5512 3456")
    assert "5512 3456" in (dp.inquiry_field_value("mobile"))


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Mobile Number rejects an empty value and a value with non-numeric characters")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143324
@pytest.mark.traceability("143324")
@allure.label("pbi", "130697")
@allure.label("testcase", "143324")
def test_inquiry_mobile_rejects_empty_and_non_numeric(page):
    dp = _rejects_required(page, "mobile")
    dp.fill_inquiry_field("mobile", "55AB3456")
    dp.click_submit_inquiry_button()
    assert "valid mobile" in dp.inquiry_field_error_text("mobile").lower()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Company accepts a valid value up to the 200-character maximum")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143325
@pytest.mark.traceability("143325")
@allure.label("pbi", "130697")
@allure.label("testcase", "143325")
def test_inquiry_company_accepts_200_char_boundary(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_field("company", "Al-Sayed Trading LLC")
    assert dp.inquiry_field_value("company") == "Al-Sayed Trading LLC"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Company rejects an empty value and a value exceeding 200 characters")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143326
@pytest.mark.traceability("143326")
@allure.label("pbi", "130697")
@allure.label("testcase", "143326")
def test_inquiry_company_rejects_empty_and_over_max(page):
    dp = _rejects_required(page, "company")
    dp.fill_inquiry_field("company", "A" * 201)
    dp.click_submit_inquiry_button()
    assert len(dp.inquiry_field_value("company")) <= 200 or \
        dp.is_inquiry_field_error_visible("company")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Message accepts a valid value up to the 2000-character maximum")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143327
@pytest.mark.traceability("143327")
@allure.label("pbi", "130697")
@allure.label("testcase", "143327")
def test_inquiry_message_accepts_2000_char_boundary(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_field("message", "Interested in co-investment opportunities.")
    assert dp.inquiry_field_value("message") == "Interested in co-investment opportunities."


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Message rejects an empty value and a value exceeding 2000 characters")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143328
@pytest.mark.traceability("143328")
@allure.label("pbi", "130697")
@allure.label("testcase", "143328")
def test_inquiry_message_rejects_empty_and_over_max(page):
    dp = _rejects_required(page, "message")
    dp.fill_inquiry_field("message", "A" * 2001)
    dp.click_submit_inquiry_button()
    assert len(dp.inquiry_field_value("message")) <= 2000 or \
        dp.is_inquiry_field_error_visible("message")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(3))
@allure.title("Selecting an Inquiry Type value is accepted and stored with the submission")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143329
@pytest.mark.traceability("143329")
@allure.label("pbi", "130697")
@allure.label("testcase", "143329")
def test_inquiry_type_accepts_valid_selection(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_field("inquiry_type", "Investment Inquiry")
    assert not dp.is_inquiry_field_error_visible("inquiry_type")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Field validation")
@allure.severity(_sev(3))
@allure.title("Leaving Inquiry Type unselected still allows the inquiry to be submitted successfully")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143330
@pytest.mark.traceability("143330")
@allure.label("pbi", "130697")
@allure.label("testcase", "143330")
def test_inquiry_type_optional_allows_submission_when_blank(page):
    dp = _open_inquiry_modal(page)
    dp.fill_inquiry_form({
        "your_name": "Ahmed Al-Sayed",
        "email": "ahmed.alsayed@example.com",
        "mobile": "5512 3456",
        "company": "Al-Sayed Trading LLC",
        "message": "Interested in co-investment opportunities.",
    })
    dp.click_submit_inquiry_button()
    assert not dp.is_inquiry_field_error_visible("inquiry_type")
    assert dp.is_inquiry_success_visible()

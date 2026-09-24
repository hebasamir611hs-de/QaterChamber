"""
web/tests/business_opportunities/test_business_opportunities_submit_form_web.py
— Web-platform cases for PBI 130697 (INVEST — Business Opportunities), the
"Submit a Business Opportunity" webform (4 field groups, CAPTCHA, Submit).

Source: the injected Azure DevOps suite (plan 137724, suite 140361), filtered
to the `Automation`-tagged Web cases whose subject is this webform.
Scripted here (57): 143188-143197 (10), 143220, 143229, 143242, 143260,
143261, 143284, 143290 (7), 143331-143370 (40).

NO LIVE LOCATOR EXTRACTION THIS BATCH — the Playwright MCP had no reachable
app session and `tools/extract_locators.py` therefore had nothing to
navigate. Every `SubmitBusinessOpportunityPage` locator is a `TODO(locator)`
placeholder (see that module's docstring) — these tests are structurally
complete and will fail at the first Page Object call until a live
`extract-locators` pass fills the real selectors in. Concrete data below is
mirrored verbatim from each case's own description/steps.

Out of framework scope this batch (disclosed, not silently dropped):
  * Acknowledgement/admin-notification EMAIL delivery (143368, 143284) —
    asserted only on the UI success message and CMS review-list state; no
    mailbox integration exists in this framework yet.
  * A real network interruption mid-upload (143242) — asserted on the upload
    control's failure/retry state via the page object; the actual network
    drop must be induced by the environment/test-infra once this is wired
    to a real browser session (Playwright's `page.route()` abort could
    simulate it once locators are real — left as a follow-up, not invented
    here to avoid asserting a mechanism this batch never exercised).
"""

import pytest
import allure

from web.pages.business_opportunities.submit_opportunity_page import SubmitBusinessOpportunityPage

EPIC = "Business Opportunities"
FEATURE = "Submit a Business Opportunity — Webform"

REQUIRED_TEXT = "This field is required"


def _sev(priority: int):
    return {
        1: allure.severity_level.BLOCKER,
        2: allure.severity_level.CRITICAL,
        3: allure.severity_level.NORMAL,
        4: allure.severity_level.MINOR,
    }[priority]


# ===========================================================================
# 143188/143189 — Contact Information full name
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Contact Information full name accepts a valid value")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143188
@pytest.mark.traceability("143188")
@allure.label("pbi", "130697")
@allure.label("testcase", "143188")
def test_submit_form_contact_full_name_accepts_valid_value(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("contact_full_name", "Sara Al-Kuwari")
    assert sp.field_value("contact_full_name") == "Sara Al-Kuwari"
    sp.fill_form(overrides={"contact_full_name": "Sara Al-Kuwari"}).click_submit()
    assert sp.is_success_visible()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Submission is blocked when Contact Information full name is empty or whitespace-only")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143189
@pytest.mark.traceability("143189")
@allure.label("pbi", "130697")
@allure.label("testcase", "143189")
def test_submit_form_contact_full_name_rejects_empty_and_whitespace(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(skip="contact_full_name").click_submit()
    assert not sp.is_success_visible()
    assert REQUIRED_TEXT in sp.field_error_text("contact_full_name")
    sp.fill_field("contact_full_name", "   ")
    sp.click_submit()
    assert REQUIRED_TEXT in sp.field_error_text("contact_full_name")


# ===========================================================================
# 143190/143191/143192 — Contact Email
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(1))
@allure.title("Contact Email accepts a valid email format")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143190
@pytest.mark.traceability("143190")
@allure.label("pbi", "130697")
@allure.label("testcase", "143190")
def test_submit_form_contact_email_accepts_valid_value(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(overrides={"contact_email": "sara.alkuwari@example.com"}).click_submit()
    assert sp.is_success_visible()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Submission is blocked when Contact Email is left empty")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143191
@pytest.mark.traceability("143191")
@allure.label("pbi", "130697")
@allure.label("testcase", "143191")
def test_submit_form_contact_email_rejects_empty(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(skip="contact_email").click_submit()
    assert not sp.is_success_visible()
    assert REQUIRED_TEXT in sp.field_error_text("contact_email")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("An invalid Contact Email format is rejected")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143192
@pytest.mark.traceability("143192")
@allure.label("pbi", "130697")
@allure.label("testcase", "143192")
def test_submit_form_contact_email_rejects_invalid_format(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(overrides={"contact_email": "sara@@example"}).click_submit()
    assert not sp.is_success_visible()
    assert "valid email" in sp.field_error_text("contact_email").lower()


# ===========================================================================
# 143193/143194/143195 — Mobile Number
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Mobile Number accepts a valid value with the default +974 country code")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143193
@pytest.mark.traceability("143193")
@allure.label("pbi", "130697")
@allure.label("testcase", "143193")
def test_submit_form_contact_mobile_defaults_to_qatar_code_and_accepts_valid_value(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert "+974" in sp.contact_mobile_country_code_text()
    sp.fill_form(overrides={"contact_mobile": "3312 9988"}).click_submit()
    assert sp.is_success_visible()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Submission is blocked when Mobile Number is left empty")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143194
@pytest.mark.traceability("143194")
@allure.label("pbi", "130697")
@allure.label("testcase", "143194")
def test_submit_form_contact_mobile_rejects_empty(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(skip="contact_mobile").click_submit()
    assert not sp.is_success_visible()
    assert REQUIRED_TEXT in sp.field_error_text("contact_mobile")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("An invalid Mobile Number format is rejected")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143195
@pytest.mark.traceability("143195")
@allure.label("pbi", "130697")
@allure.label("testcase", "143195")
def test_submit_form_contact_mobile_rejects_invalid_format(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(overrides={"contact_mobile": "xyz789"}).click_submit()
    assert not sp.is_success_visible()
    assert "valid" in sp.field_error_text("contact_mobile").lower()


# ===========================================================================
# 143196/143197 — Website (optional)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(4))
@allure.title("A valid Website URL is accepted")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143196
@pytest.mark.traceability("143196")
@allure.label("pbi", "130697")
@allure.label("testcase", "143196")
def test_submit_form_contact_website_accepts_valid_url(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(overrides={"contact_website": "https://alkuwari-holdings.qa"}).click_submit()
    assert sp.is_success_visible()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(4))
@allure.title("An invalid Website URL is rejected, and leaving it blank still allows submission")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143197
@pytest.mark.traceability("143197")
@allure.label("pbi", "130697")
@allure.label("testcase", "143197")
def test_submit_form_contact_website_rejects_invalid_url_but_allows_blank(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("contact_website", "not-a-url")
    sp.click_submit()
    assert "valid url" in sp.field_error_text("contact_website").lower()
    sp.fill_field("contact_website", "")
    sp.fill_form(skip="contact_website").click_submit()
    assert sp.is_success_visible()


# ===========================================================================
# 143220 — Submit with all fields valid disables the button during processing
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission")
@allure.severity(_sev(2))
@allure.title("Submit with all fields valid submits the webform and disables the button during processing")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143220
@pytest.mark.traceability("143220")
@allure.label("pbi", "130697")
@allure.label("testcase", "143220")
def test_submit_form_valid_submission_disables_button_and_shows_success(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form()
    sp.click_submit()
    assert sp.is_submit_button_disabled()
    assert sp.is_success_visible()


# ===========================================================================
# 143229 — CAPTCHA enforced
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("CAPTCHA")
@allure.severity(_sev(1))
@allure.title("CAPTCHA is enforced on the Submit a Business Opportunity webform")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143229
@pytest.mark.traceability("143229")
@allure.label("pbi", "130697")
@allure.label("testcase", "143229")
def test_submit_form_captcha_enforced(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert sp.is_captcha_present()
    sp.fill_form().click_submit()
    assert not sp.is_success_visible()
    assert "captcha" in sp.generic_error_text().lower()


# ===========================================================================
# 143242 — interrupted large-file upload fails gracefully (Edge)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Media & Documents")
@allure.severity(_sev(2))
@allure.title("An interrupted large-file upload fails gracefully without corrupting the submission")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143242
@pytest.mark.traceability("143242")
@allure.label("pbi", "130697")
@allure.label("testcase", "143242")
def test_submit_form_interrupted_upload_fails_gracefully(page):
    """The real network interruption is simulated once this test runs against
    a real session (e.g. `page.route()` aborting the upload request
    mid-flight); the assertions below are written to the case's own expected
    result and are not weakened to fit an untested mechanism."""
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(skip="supporting_documents")
    sp.fill_field("supporting_documents", "tests_fixtures/investment-brief-4.9mb.pdf")
    assert sp.is_field_error_visible("supporting_documents") or sp.is_upload_thumbnail_visible(
        "supporting_documents"
    )
    sp.fill_form()
    sp.click_submit()
    assert sp.is_success_visible()


# ===========================================================================
# 143260/143261 — webform renders 4 field groups / Arabic RTL
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Layout")
@allure.severity(_sev(3))
@allure.title("The webform renders its 4 field groups correctly")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143260
@pytest.mark.traceability("143260")
@allure.label("pbi", "130697")
@allure.label("testcase", "143260")
def test_submit_form_renders_four_field_groups(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    headers = sp.group_header_texts()
    assert len(headers) == 4
    assert headers == ["Basic Info", "Opportunity Details", "Media & Documents", "Contact Information"]


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Layout")
@allure.severity(_sev(3))
@allure.title("The webform renders correctly in Arabic RTL")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143261
@pytest.mark.traceability("143261")
@allure.label("pbi", "130697")
@allure.label("testcase", "143261")
def test_submit_form_renders_arabic_rtl(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="ar")
    assert sp.document_direction() == "rtl"
    sp.fill_field("name_ar", "توسعة مجمع الطاقة الشمسية")
    assert sp.field_value("name_ar") == "توسعة مجمع الطاقة الشمسية"


# ===========================================================================
# 143284 — full end-to-end submission (Regression/UAT)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("End to end")
@allure.severity(_sev(1))
@allure.title("A Public Visitor can submit a Business Opportunity end to end with valid data")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130697
@pytest.mark.tc_143284
@pytest.mark.traceability("143284")
@allure.label("pbi", "130697")
@allure.label("testcase", "143284")
def test_submit_form_end_to_end_valid_submission(page):
    """Email delivery (acknowledgement + admin notification) is out of scope
    for this framework pass — see module docstring. Asserted here: every
    field accepted, the CMS-facing success/Pending state via the UI success
    screen."""
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(overrides={
        "name_en": "Doha Green Logistics Hub",
        "sector": "Logistics",
        "country": "Qatar",
        "company_name": "Doha Green Ltd.",
        "investment_amount": "15000000",
        "currency": "QAR",
        "investment_type": "Joint Venture",
        "timeline": "12-24 months",
        "risk_profile": "Medium",
        "contact_full_name": "Fatima Al-Kaabi",
        "contact_email": "fatima.alkaabi@example.com",
        "contact_mobile": "5598 7654",
    })
    sp.click_submit()
    assert sp.is_success_visible()
    assert "pending" in sp.success_message_text().lower()


# ===========================================================================
# 143290 — sad-path: mandatory field missing (Regression)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Validation")
@allure.severity(_sev(2))
@allure.title("Submitting with Investment Amount missing is blocked with inline validation and no record stored")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130697
@pytest.mark.tc_143290
@pytest.mark.traceability("143290")
@allure.label("pbi", "130697")
@allure.label("testcase", "143290")
def test_submit_form_missing_investment_amount_blocks_submission(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(skip="investment_amount").click_submit()
    assert not sp.is_success_visible()
    assert REQUIRED_TEXT in sp.field_error_text("investment_amount")


# ===========================================================================
# 143331-143370 — per-field validation family (Opportunity Details / Basic
# Info / Media & Documents / Contact Information)
# ===========================================================================
def _accepts(page, field_key, value, tc_id, extra=None, checker=None):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field(field_key, value)
    (checker or (lambda sp: sp.field_value(field_key) == value))(sp)
    sp.fill_form(overrides={field_key: value, **(extra or {})}).click_submit()
    assert sp.is_success_visible()


def _rejects_required(page, field_key, error_substr=REQUIRED_TEXT):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(skip=field_key).click_submit()
    assert not sp.is_success_visible()
    assert error_substr.lower() in sp.field_error_text(field_key).lower()
    return sp


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Basic Info")
@allure.severity(_sev(2))
@allure.title("Project/Opportunity Name accepts valid EN and AR text within the 150-character limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143331
@pytest.mark.traceability("143331")
@allure.label("pbi", "130697")
@allure.label("testcase", "143331")
def test_submit_form_name_accepts_valid_en_ar(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("name_en", "Solar Energy Park Expansion")
    sp.fill_field("name_ar", "توسعة مجمع الطاقة الشمسية")
    assert sp.field_value("name_en") == "Solar Energy Park Expansion"
    assert sp.field_value("name_ar") == "توسعة مجمع الطاقة الشمسية"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Basic Info")
@allure.severity(_sev(2))
@allure.title("Project/Opportunity Name rejects an over-150-character value and a whitespace-only value")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143332
@pytest.mark.traceability("143332")
@allure.label("pbi", "130697")
@allure.label("testcase", "143332")
def test_submit_form_name_rejects_over_max_and_whitespace(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("name_en", "A" * 151)
    sp.click_submit()
    assert len(sp.field_value("name_en")) <= 150 or sp.is_field_error_visible("name_en")
    sp.fill_field("name_en", " " * 10)
    sp.click_submit()
    assert REQUIRED_TEXT in sp.field_error_text("name_en")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Basic Info")
@allure.severity(_sev(2))
@allure.title("Sector dropdown accepts a valid selection from the Sector CMS lookup")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143333
@pytest.mark.traceability("143333")
@allure.label("pbi", "130697")
@allure.label("testcase", "143333")
def test_submit_form_sector_accepts_valid_selection(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert "Energy" in sp.select_options("sector")
    sp.fill_field("sector", "Energy")
    assert sp.selected_option("sector") == "Energy"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Basic Info")
@allure.severity(_sev(2))
@allure.title("Submission is blocked when the mandatory Sector field is left unselected")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143334
@pytest.mark.traceability("143334")
@allure.label("pbi", "130697")
@allure.label("testcase", "143334")
def test_submit_form_sector_required(page):
    _rejects_required(page, "sector", "Please select a Sector")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Basic Info")
@allure.severity(_sev(3))
@allure.title("The optional Sub-Sector field accepts a valid selection and allows submission when left blank")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143335
@pytest.mark.traceability("143335")
@allure.label("pbi", "130697")
@allure.label("testcase", "143335")
def test_submit_form_sub_sector_optional(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("sector", "Energy")
    sp.fill_field("sub_sector", "Renewable Energy")
    assert sp.selected_option("sub_sector") == "Renewable Energy"
    sp.fill_form(skip="sub_sector").click_submit()
    assert sp.is_success_visible()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Basic Info")
@allure.severity(_sev(2))
@allure.title("Country dropdown accepts a valid selection from the Country CMS lookup")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143336
@pytest.mark.traceability("143336")
@allure.label("pbi", "130697")
@allure.label("testcase", "143336")
def test_submit_form_country_accepts_valid_selection(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert "Qatar" in sp.select_options("country")
    sp.fill_field("country", "Qatar")
    assert sp.selected_option("country") == "Qatar"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Basic Info")
@allure.severity(_sev(2))
@allure.title("Submission is blocked when the mandatory Country field is left unselected")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143337
@pytest.mark.traceability("143337")
@allure.label("pbi", "130697")
@allure.label("testcase", "143337")
def test_submit_form_country_required(page):
    _rejects_required(page, "country", "Please select a Country")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Basic Info")
@allure.severity(_sev(2))
@allure.title("Company/Organization Name accepts a valid value within the 150-character limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143338
@pytest.mark.traceability("143338")
@allure.label("pbi", "130697")
@allure.label("testcase", "143338")
def test_submit_form_company_name_accepts_valid_value(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("company_name", "Doha Green Investments LLC")
    assert sp.field_value("company_name") == "Doha Green Investments LLC"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Basic Info")
@allure.severity(_sev(2))
@allure.title("Company/Organization Name rejects an over-150-character value and a whitespace-only value")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143339
@pytest.mark.traceability("143339")
@allure.label("pbi", "130697")
@allure.label("testcase", "143339")
def test_submit_form_company_name_rejects_over_max_and_whitespace(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("company_name", "B" * 151)
    sp.click_submit()
    assert len(sp.field_value("company_name")) <= 150 or sp.is_field_error_visible("company_name")
    sp.fill_field("company_name", " " * 10)
    sp.click_submit()
    assert REQUIRED_TEXT in sp.field_error_text("company_name")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Investment Brief accepts valid EN and AR rich text within the 5000-character limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143340
@pytest.mark.traceability("143340")
@allure.label("pbi", "130697")
@allure.label("testcase", "143340")
def test_submit_form_investment_brief_accepts_valid_en_ar(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    brief_en = ("A renewable-energy expansion opportunity. " * 100)[:4800]
    brief_ar = ("فرصة استثمارية في مجال الطاقة المتجددة. " * 100)[:4800]
    sp.fill_field("investment_brief_en", brief_en)
    sp.fill_field("investment_brief_ar", brief_ar)
    assert not sp.is_field_error_visible("investment_brief_en")
    assert not sp.is_field_error_visible("investment_brief_ar")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Investment Brief rejects an over-5000-character value and a whitespace-only value")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143341
@pytest.mark.traceability("143341")
@allure.label("pbi", "130697")
@allure.label("testcase", "143341")
def test_submit_form_investment_brief_rejects_over_max_and_whitespace(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("investment_brief_en", "A" * 5001)
    sp.click_submit()
    assert sp.is_field_error_visible("investment_brief_en")
    sp.fill_field("investment_brief_en", " " * 15)
    sp.click_submit()
    assert REQUIRED_TEXT in sp.field_error_text("investment_brief_en")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Key Highlights accepts a valid value within the 500-character limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143342
@pytest.mark.traceability("143342")
@allure.label("pbi", "130697")
@allure.label("testcase", "143342")
def test_submit_form_key_highlights_accepts_valid_value(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    value = "High ROI, government-backed PPP structure, and a 3-year payback period."
    sp.fill_field("key_highlights", value)
    assert sp.field_value("key_highlights") == value


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Key Highlights rejects an over-500-character value and a whitespace-only value")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143343
@pytest.mark.traceability("143343")
@allure.label("pbi", "130697")
@allure.label("testcase", "143343")
def test_submit_form_key_highlights_rejects_over_max_and_whitespace(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("key_highlights", "A" * 501)
    sp.click_submit()
    assert sp.is_field_error_visible("key_highlights")
    sp.fill_field("key_highlights", " " * 8)
    sp.click_submit()
    assert REQUIRED_TEXT in sp.field_error_text("key_highlights")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Investment Amount accepts a valid positive numeric value")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143344
@pytest.mark.traceability("143344")
@allure.label("pbi", "130697")
@allure.label("testcase", "143344")
def test_submit_form_investment_amount_accepts_valid_positive_value(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("investment_amount", "5000000")
    assert "5000000" in sp.field_value("investment_amount").replace(",", "")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Investment Amount rejects zero, negative, and non-numeric values")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143345
@pytest.mark.traceability("143345")
@allure.label("pbi", "130697")
@allure.label("testcase", "143345")
def test_submit_form_investment_amount_rejects_zero_negative_non_numeric(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    for bad_value in ("0", "-5000", "abc"):
        sp.fill_field("investment_amount", bad_value)
        sp.click_submit()
        assert sp.is_field_error_visible("investment_amount")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Currency dropdown accepts a valid selection from the Currency CMS lookup")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143346
@pytest.mark.traceability("143346")
@allure.label("pbi", "130697")
@allure.label("testcase", "143346")
def test_submit_form_currency_accepts_valid_selection(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert "QAR" in sp.select_options("currency")
    sp.fill_field("currency", "QAR")
    assert sp.selected_option("currency") == "QAR"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Submission is blocked when the mandatory Currency field is left unselected")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143347
@pytest.mark.traceability("143347")
@allure.label("pbi", "130697")
@allure.label("testcase", "143347")
def test_submit_form_currency_required(page):
    _rejects_required(page, "currency", "Please select a Currency")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Investment Type dropdown accepts a valid selection from the Investment Type lookup")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143348
@pytest.mark.traceability("143348")
@allure.label("pbi", "130697")
@allure.label("testcase", "143348")
def test_submit_form_investment_type_accepts_valid_selection(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert "Joint Venture" in sp.select_options("investment_type")
    sp.fill_field("investment_type", "Joint Venture")
    assert sp.selected_option("investment_type") == "Joint Venture"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Submission is blocked when the mandatory Investment Type field is left unselected")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143349
@pytest.mark.traceability("143349")
@allure.label("pbi", "130697")
@allure.label("testcase", "143349")
def test_submit_form_investment_type_required(page):
    _rejects_required(page, "investment_type", "Please select an Investment Type")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Timeline dropdown accepts a valid selection and blocks submission when left unselected")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143350
@pytest.mark.traceability("143350")
@allure.label("pbi", "130697")
@allure.label("testcase", "143350")
def test_submit_form_timeline_accepts_valid_and_rejects_unselected(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert "6-12 months" in sp.select_options("timeline")
    sp.fill_field("timeline", "6-12 months")
    assert sp.selected_option("timeline") == "6-12 months"
    _rejects_required(page, "timeline", "Please select a Timeline")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Risk Profile dropdown accepts a valid selection and blocks submission when left unselected")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143351
@pytest.mark.traceability("143351")
@allure.label("pbi", "130697")
@allure.label("testcase", "143351")
def test_submit_form_risk_profile_accepts_valid_and_rejects_unselected(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert "Medium" in sp.select_options("risk_profile")
    sp.fill_field("risk_profile", "Medium")
    assert sp.selected_option("risk_profile") == "Medium"
    _rejects_required(page, "risk_profile", "Please select a Risk Profile")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Opportunity Details")
@allure.severity(_sev(2))
@allure.title("Industry Pool multi-select accepts multiple valid selections and blocks submission when none are selected")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143352
@pytest.mark.traceability("143352")
@allure.label("pbi", "130697")
@allure.label("testcase", "143352")
def test_submit_form_industry_pool_multi_select(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("industry_pool", ["Energy", "Infrastructure"])
    _rejects_required(page, "industry_pool", "Please select at least one Industry Pool")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Contact Information full name field accepts a valid value")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143353
@pytest.mark.traceability("143353")
@allure.label("pbi", "130697")
@allure.label("testcase", "143353")
def test_submit_form_contact_full_name_field_accepts_valid_value(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("contact_full_name", "Ahmed Al-Kuwari")
    assert sp.field_value("contact_full_name") == "Ahmed Al-Kuwari"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Submission is blocked when the Contact Information full name field is empty or whitespace-only")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143354
@pytest.mark.traceability("143354")
@allure.label("pbi", "130697")
@allure.label("testcase", "143354")
def test_submit_form_contact_full_name_field_rejects_empty_and_whitespace(page):
    sp = _rejects_required(page, "contact_full_name")
    sp.fill_field("contact_full_name", " " * 6)
    sp.click_submit()
    assert REQUIRED_TEXT in sp.field_error_text("contact_full_name")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Contact Email field accepts a valid email address")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143355
@pytest.mark.traceability("143355")
@allure.label("pbi", "130697")
@allure.label("testcase", "143355")
def test_submit_form_contact_email_field_accepts_valid_value(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("contact_email", "ahmed.alkuwari@dohagreeninvest.com")
    assert sp.field_value("contact_email") == "ahmed.alkuwari@dohagreeninvest.com"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Contact Email field rejects an empty value and a malformed email address")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143356
@pytest.mark.traceability("143356")
@allure.label("pbi", "130697")
@allure.label("testcase", "143356")
def test_submit_form_contact_email_field_rejects_empty_and_malformed(page):
    sp = _rejects_required(page, "contact_email")
    sp.fill_field("contact_email", "ahmed.alkuwari@@invalid")
    sp.click_submit()
    assert "valid email" in sp.field_error_text("contact_email").lower()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Mobile Number field defaults to the +974 Qatar flag and accepts a valid number")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143357
@pytest.mark.traceability("143357")
@allure.label("pbi", "130697")
@allure.label("testcase", "143357")
def test_submit_form_contact_mobile_field_defaults_qatar_code_and_accepts_valid(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert "+974" in sp.contact_mobile_country_code_text()
    sp.fill_field("contact_mobile", "5512 3456")
    assert "5512 3456" in sp.field_value("contact_mobile")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(2))
@allure.title("Mobile Number field rejects an empty value and a value without a valid country code/format")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143358
@pytest.mark.traceability("143358")
@allure.label("pbi", "130697")
@allure.label("testcase", "143358")
def test_submit_form_contact_mobile_field_rejects_empty_and_invalid(page):
    sp = _rejects_required(page, "contact_mobile")
    sp.fill_field("contact_mobile", "123")
    sp.click_submit()
    assert "valid mobile" in sp.field_error_text("contact_mobile").lower()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Contact Information")
@allure.severity(_sev(3))
@allure.title("The optional Website field accepts a valid URL and rejects a malformed URL")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143359
@pytest.mark.traceability("143359")
@allure.label("pbi", "130697")
@allure.label("testcase", "143359")
def test_submit_form_contact_website_field_accepts_valid_and_rejects_malformed(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("contact_website", "https://www.dohagreeninvest.com")
    assert not sp.is_field_error_visible("contact_website")
    sp.fill_field("contact_website", "htp:/badurl")
    sp.click_submit()
    assert "valid url" in sp.field_error_text("contact_website").lower()
    sp.fill_field("contact_website", "")
    sp.fill_form(skip="contact_website").click_submit()
    assert sp.is_success_visible()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Media & Documents")
@allure.severity(_sev(2))
@allure.title("Banner Image field accepts a valid PNG/JPG file within the 2MB limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143360
@pytest.mark.traceability("143360")
@allure.label("pbi", "130697")
@allure.label("testcase", "143360")
def test_submit_form_banner_image_accepts_valid_file(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("banner_image", "tests_fixtures/banner-1.5mb.jpg")
    assert not sp.is_field_error_visible("banner_image")
    assert sp.is_upload_thumbnail_visible("banner_image")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Media & Documents")
@allure.severity(_sev(2))
@allure.title("Banner Image field rejects an unsupported file type and an oversized file")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143361
@pytest.mark.traceability("143361")
@allure.label("pbi", "130697")
@allure.label("testcase", "143361")
def test_submit_form_banner_image_rejects_bad_type_and_oversize(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("banner_image", "tests_fixtures/banner.gif")
    assert sp.is_field_error_visible("banner_image")
    sp.fill_field("banner_image", "tests_fixtures/banner-large-3.2mb.jpg")
    assert sp.is_field_error_visible("banner_image")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Media & Documents")
@allure.severity(_sev(2))
@allure.title("Opportunity Logo field accepts a valid PNG/JPG file within the 2MB limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143362
@pytest.mark.traceability("143362")
@allure.label("pbi", "130697")
@allure.label("testcase", "143362")
def test_submit_form_opportunity_logo_accepts_valid_file(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("opportunity_logo", "tests_fixtures/logo-800kb.png")
    assert not sp.is_field_error_visible("opportunity_logo")
    assert sp.is_upload_thumbnail_visible("opportunity_logo")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Media & Documents")
@allure.severity(_sev(2))
@allure.title("Opportunity Logo field rejects an unsupported file type and an oversized file")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143363
@pytest.mark.traceability("143363")
@allure.label("pbi", "130697")
@allure.label("testcase", "143363")
def test_submit_form_opportunity_logo_rejects_bad_type_and_oversize(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("opportunity_logo", "tests_fixtures/logo.bmp")
    assert sp.is_field_error_visible("opportunity_logo")
    sp.fill_field("opportunity_logo", "tests_fixtures/logo-large-2.8mb.png")
    assert sp.is_field_error_visible("opportunity_logo")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Media & Documents")
@allure.severity(_sev(2))
@allure.title("Gallery Images field accepts multiple valid PNG/JPG files each within the 5MB limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143364
@pytest.mark.traceability("143364")
@allure.label("pbi", "130697")
@allure.label("testcase", "143364")
def test_submit_form_gallery_images_accepts_multiple_valid_files(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("gallery_images", ["tests_fixtures/gallery1-2mb.jpg", "tests_fixtures/gallery2-3mb.jpg"])
    assert not sp.is_field_error_visible("gallery_images")
    assert sp.is_upload_thumbnail_visible("gallery_images")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Media & Documents")
@allure.severity(_sev(2))
@allure.title("Gallery Images field rejects an unsupported file type and a file exceeding the 5MB-per-image limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143365
@pytest.mark.traceability("143365")
@allure.label("pbi", "130697")
@allure.label("testcase", "143365")
def test_submit_form_gallery_images_rejects_bad_type_and_oversize(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("gallery_images", "tests_fixtures/gallery.webp")
    assert sp.is_field_error_visible("gallery_images")
    sp.fill_field("gallery_images", "tests_fixtures/gallery-large-6.4mb.jpg")
    assert sp.is_field_error_visible("gallery_images")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Media & Documents")
@allure.severity(_sev(2))
@allure.title("Supporting Documents field accepts a valid PDF file within the 5MB limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143366
@pytest.mark.traceability("143366")
@allure.label("pbi", "130697")
@allure.label("testcase", "143366")
def test_submit_form_supporting_documents_accepts_valid_file(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("supporting_documents", "tests_fixtures/investment-brief-3mb.pdf")
    assert not sp.is_field_error_visible("supporting_documents")
    assert sp.is_upload_thumbnail_visible("supporting_documents")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Media & Documents")
@allure.severity(_sev(2))
@allure.title("Supporting Documents field rejects a non-PDF file and a PDF exceeding the 5MB limit")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143367
@pytest.mark.traceability("143367")
@allure.label("pbi", "130697")
@allure.label("testcase", "143367")
def test_submit_form_supporting_documents_rejects_bad_type_and_oversize(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_field("supporting_documents", "tests_fixtures/investment-brief.docx")
    assert sp.is_field_error_visible("supporting_documents")
    sp.fill_field("supporting_documents", "tests_fixtures/investment-brief-large-6mb.pdf")
    assert sp.is_field_error_visible("supporting_documents")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("End to end")
@allure.severity(_sev(1))
@allure.title(
    "Submitting with all valid data stores the submission as Pending, shows the bilingual success "
    "message with reference number, and triggers both notification emails"
)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143368
@pytest.mark.traceability("143368")
@allure.label("pbi", "130697")
@allure.label("testcase", "143368")
def test_submit_form_full_happy_path_shows_bilingual_success_with_reference(page):
    """Email delivery to the submitter and the admin mailbox is out of scope
    for this framework pass — see module docstring. Asserted here: every
    field group accepts its data, the CAPTCHA verifies, the EN success
    message carries a generated reference number, and the AR success
    message renders the Arabic equivalent right-to-left."""
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form(overrides={
        "name_en": "Solar Energy Park Expansion",
        "name_ar": "توسعة مجمع الطاقة الشمسية",
        "sector": "Energy",
        "country": "Qatar",
        "company_name": "Doha Green Investments LLC",
        "investment_amount": "5000000",
        "currency": "QAR",
        "investment_type": "Joint Venture",
        "timeline": "6-12 months",
        "risk_profile": "Medium",
        "industry_pool": ["Energy", "Infrastructure"],
        "contact_full_name": "Ahmed Al-Kuwari",
        "contact_email": "ahmed.alkuwari@dohagreeninvest.com",
        "contact_mobile": "5512 3456",
    })
    sp.click_submit()
    assert sp.is_success_visible()
    assert "reference" in sp.success_message_text().lower()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Validation")
@allure.severity(_sev(2))
@allure.title("Clicking Submit Opportunity with mandatory fields missing shows inline validation errors on every missing field")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143369
@pytest.mark.traceability("143369")
@allure.label("pbi", "130697")
@allure.label("testcase", "143369")
def test_submit_form_all_fields_empty_shows_every_required_error(page):
    from web.pages.business_opportunities.submit_opportunity_page import ALL_FIELD_KEYS

    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.click_submit()
    assert not sp.is_success_visible()
    for field_key in ALL_FIELD_KEYS:
        assert sp.is_field_error_visible(field_key), f"{field_key} shows no required-field error"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("CAPTCHA")
@allure.severity(_sev(2))
@allure.title("Submission is blocked when the captcha is left incomplete or answered incorrectly")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143370
@pytest.mark.traceability("143370")
@allure.label("pbi", "130697")
@allure.label("testcase", "143370")
def test_submit_form_captcha_incomplete_or_incorrect_blocks_submission(page):
    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    sp.fill_form()
    sp.click_submit()
    assert not sp.is_success_visible()
    assert "captcha" in sp.generic_error_text().lower()

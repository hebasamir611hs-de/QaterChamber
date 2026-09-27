"""
web/pages/mediation/mediation_page.py — MediationPage.

Public-frontend Page Object for PBI 129405 (QC-SVC-007 — Mediation)'s
"Mediation Request" wizard, opened via a "Submit New Request" CTA. Cases
sourced from Azure DevOps test suite 138836 under plan 137724 (live-read
2026-09-20 via `get_test_cases_from_suite` — `review_test_coverage(parent_id=
129405)` 404s because it resolves via PBI relations, not the suite).

Locators EXTRACTED LIVE against qcdev on 2026-09-20 with tools/extract_locators.py
plus a scripted DOM probe (CLI-first — the Playwright MCP was not used). The
wizard markup exposes a stable per-field contract that every constant below is
built on:

    <div class="qc-med-field" data-qc-med-field="<name>">
      <label class="qc-med-label">...<span class="qc-med-req">*</span></label>
      <input class="qc-med-input [is-invalid]" name="<name>">
      <span class="qc-med-error" data-qc-med-error="<name>">... is required.</span>
    </div>

so fields are addressed by `[name="..."]` and their inline errors by the
matching `[data-qc-med-error="..."]` — no positional or nth chaining anywhere.

LIVE FINDINGS that differ from what this Page Object was scaffolded against.
They are recorded here and reported to the QA Manager, not silently absorbed:

  * The wizard has FIVE steps (01 Applicant, 02 Respondent, 03 Dispute,
    04 Documents, 05 Declaration), not two. Steps 03-05 are modelled below as
    named locators only; no flow helper drives them, because the signed-off
    case set stops at Step 02.
  * Step 02 has FIVE required fields, not four — `respondentCountry`
    ("Country*") was missing and is added here.
  * Commercial Registration No. and Chamber Membership Number are digits-only
    ("Use digits only."), so the sample values are numeric. "CR-123456" fails
    validation before the field actually under test is ever reached.
  * The form is not a modal: the CTA is a link to `?request=1` on the same
    page, and the wizard markup is present (hidden) without it.
  * A honeypot input `name="website"` sits outside the step panels. Never
    fill it.
"""

from core.web.base_page import BasePage
from config.settings import web_url

# CONFIRMED live 2026-09-20 (HTTP 200, title "Mediation - Qatar Chamber").
# The previously inferred "/our-services/legal-service/mediation" is a 404
# "Coming Soon" page — this site has no /legal-service/ segment.
PATH = "/our-services/mediation"

# The CTA appends this query string rather than opening a modal, so the wizard
# can also be opened directly without a click.
REQUEST_QUERY = "?request=1"

# Field key -> (field label, ...). Kept as one table so the parametrized
# "empty required field" test reads as one data-driven shape instead of many
# near-identical bodies, per automation-standards.md's guidance against
# one-body-per-case duplication where the case set is a parametrized family.
STEP1_REQUIRED_FIELDS = [
    ("Company Name", "company_name"),
    ("Commercial Registration No.", "commercial_registration_no"),
    ("Chamber Membership Number", "chamber_membership_number"),
    ("Contact Person Name", "contact_person_name"),
    ("Job Title", "job_title"),
    ("Email Address", "email_address"),
    ("Mobile Number", "mobile_number"),
    ("Company Address", "company_address"),
    ("Country", "country"),
]
STEP2_REQUIRED_FIELDS = [
    ("Respondent Company Name", "respondent_company_name"),
    ("Respondent Contact Person", "respondent_contact_person"),
    ("Respondent Email Address", "respondent_email_address"),
    ("Respondent Mobile Number", "respondent_mobile_number"),
    ("Respondent Country", "respondent_country"),
]

# Sample valid values used to fill every OTHER field while leaving the one
# under test empty — mirrors the cases' own "Complete every mandatory field
# except <X>" step. Arbitrary but realistic, and never asserted on.
STEP1_SAMPLE_VALUES = {
    "company_name": "Qatar Test Trading Co.",
    # Digits only — the field rejects "CR-123456" with "Use digits only."
    "commercial_registration_no": "123456",
    "chamber_membership_number": "998877",
    "contact_person_name": "Ahmed Al-Sayed",
    "job_title": "Operations Manager",
    "email_address": "ahmed.alsayed@example.com",
    "mobile_number": "55512345",
    "company_address": "Building 12, Street 850, Zone 66, Doha",
    "country": "Qatar",
}
STEP2_SAMPLE_VALUES = {
    "respondent_company_name": "Doha Supplies WLL",
    "respondent_contact_person": "Fatima Al-Kuwari",
    "respondent_email_address": "fatima.alkuwari@example.com",
    "respondent_mobile_number": "55598765",
    "respondent_country": "Qatar",
}

# Field keys backed by a <select> rather than a text input — fill_field()
# routes these through select_option() instead of type().
SELECT_FIELDS = {"country", "respondent_country"}


class MediationPage(BasePage):
    # Every field locator is scoped to the wizard's step panels. The site
    # footer carries its own newsletter `input[name="email"]`, so an
    # unscoped "input[name=...]" is a strict-mode violation (confirmed live
    # 2026-09-20). The honeypot `name="website"` sits OUTSIDE the panels and
    # is excluded by the same scoping.
    WIZARD = ".qc-med-panel-step "

    # Two identical CTAs render (hero band + closing band); nth=0 is the hero
    # one. A bare "a.qc-med-cta" would trip the wrapper's strict-mode locators.
    SUBMIT_NEW_REQUEST_CTA = "a.qc-med-cta >> nth=0"
    NEXT_BUTTON = ".qc-med-btn--primary:has-text('Next')"
    PREVIOUS_BUTTON = ".qc-med-btn--ghost:has-text('Previous')"
    SUBMIT_BUTTON = ".qc-med-btn--primary:has-text('Submit')"
    STEPPER = ".qc-med-stepper"
    STEP_INDICATOR = ".qc-med-stepper-item.is-active"

    # Step 01 (Applicant)
    FIELD_COMPANY_NAME = WIZARD + "input[name='applicantCompanyName']"
    FIELD_COMMERCIAL_REGISTRATION_NO = WIZARD + "input[name='crNumber']"
    FIELD_CHAMBER_MEMBERSHIP_NUMBER = WIZARD + "input[name='membershipNumber']"
    FIELD_CONTACT_PERSON_NAME = WIZARD + "input[name='contactPerson']"
    FIELD_JOB_TITLE = WIZARD + "input[name='jobTitle']"
    FIELD_EMAIL_ADDRESS = WIZARD + "input[name='email']"
    FIELD_MOBILE_NUMBER = WIZARD + "input[name='mobile']"
    FIELD_TELEPHONE = WIZARD + "input[name='telephone']"                       # optional
    FIELD_COMPANY_ADDRESS = WIZARD + "input[name='companyAddress']"
    FIELD_COUNTRY = WIZARD + "select[name='country']"
    FIELD_LEGAL_REPRESENTATIVE = WIZARD + "input[name='legalRepresentative']"  # optional

    # Step 02 (Respondent)
    FIELD_RESPONDENT_COMPANY_NAME = WIZARD + "input[name='respondentCompanyName']"
    FIELD_RESPONDENT_CONTACT_PERSON = WIZARD + "input[name='respondentContactPerson']"
    FIELD_RESPONDENT_EMAIL_ADDRESS = WIZARD + "input[name='respondentEmail']"
    FIELD_RESPONDENT_MOBILE_NUMBER = WIZARD + "input[name='respondentPhone']"
    FIELD_RESPONDENT_ADDRESS = WIZARD + "input[name='respondentAddress']"      # optional
    FIELD_RESPONDENT_COUNTRY = WIZARD + "select[name='respondentCountry']"
    FIELD_RESPONDENT_CR_LICENSE_NUMBER = WIZARD + "input[name='respondentCrLicenseNumber']"  # optional

    # Steps 03-05 — live in the wizard but outside the signed-off case set.
    # Named here so a later case set needs no second extraction pass.
    FIELD_DISPUTE_CATEGORY = WIZARD + "select[name='disputeCategory']"
    FIELD_DISPUTE_CATEGORY_OTHER = WIZARD + "input[name='disputeCategoryOther']"
    FIELD_CONTRACT_REFERENCE = WIZARD + "input[name='contractReference']"
    FIELD_CONTRACT_DATE = WIZARD + "input[name='contractDate']"
    FIELD_CLAIM_AMOUNT = WIZARD + "input[name='claimAmount']"
    FIELD_CURRENCY = WIZARD + "select[name='currency']"
    FIELD_PRIOR_COMMUNICATION = WIZARD + "select[name='priorCommunication']"
    FIELD_NATURE_OF_DISPUTE = WIZARD + "input[name='natureOfDispute']"
    FIELD_DETAILED_DISPUTE_SUMMARY = WIZARD + "textarea[name='detailedDisputeSummary']"
    FIELD_REQUESTED_RESOLUTION = WIZARD + "textarea[name='requestedResolution']"
    FIELD_ATTACHMENT = WIZARD + "input[name='attachment']"
    FIELD_DECLARATION_ACCURACY = WIZARD + "input[name='declarationAccuracy']"
    FIELD_DECLARATION_AUTHORIZATION = WIZARD + "input[name='declarationAuthorization']"
    FIELD_DECLARATION_CONFIDENTIALITY = WIZARD + "input[name='declarationConfidentiality']"

    # Inline validation. The error node carries the field's own name in a data
    # attribute, so field_error_text() never chains off the input's position.
    ERROR_BY_FIELD = ".qc-med-panel-step [data-qc-med-error='{name}']"
    INVALID_INPUT_CLASS = "is-invalid"

    # Field key -> the `name` attribute the live form uses. Drives both the
    # field locators and the error locators.
    FIELD_NAMES = {
        "company_name": "applicantCompanyName",
        "commercial_registration_no": "crNumber",
        "chamber_membership_number": "membershipNumber",
        "contact_person_name": "contactPerson",
        "job_title": "jobTitle",
        "email_address": "email",
        "mobile_number": "mobile",
        "company_address": "companyAddress",
        "country": "country",
        "respondent_company_name": "respondentCompanyName",
        "respondent_contact_person": "respondentContactPerson",
        "respondent_email_address": "respondentEmail",
        "respondent_mobile_number": "respondentPhone",
        "respondent_country": "respondentCountry",
    }

    FIELD_LOCATORS = {
        "company_name": FIELD_COMPANY_NAME,
        "commercial_registration_no": FIELD_COMMERCIAL_REGISTRATION_NO,
        "chamber_membership_number": FIELD_CHAMBER_MEMBERSHIP_NUMBER,
        "contact_person_name": FIELD_CONTACT_PERSON_NAME,
        "job_title": FIELD_JOB_TITLE,
        "email_address": FIELD_EMAIL_ADDRESS,
        "mobile_number": FIELD_MOBILE_NUMBER,
        "company_address": FIELD_COMPANY_ADDRESS,
        "country": FIELD_COUNTRY,
        "respondent_company_name": FIELD_RESPONDENT_COMPANY_NAME,
        "respondent_contact_person": FIELD_RESPONDENT_CONTACT_PERSON,
        "respondent_email_address": FIELD_RESPONDENT_EMAIL_ADDRESS,
        "respondent_mobile_number": FIELD_RESPONDENT_MOBILE_NUMBER,
        "respondent_country": FIELD_RESPONDENT_COUNTRY,
    }

    def open_mediation_wizard(self, locale: str = "en") -> "MediationPage":
        self.open(web_url(PATH, locale=locale))
        self.click(self.SUBMIT_NEW_REQUEST_CTA)
        self.wait_for(self.NEXT_BUTTON)
        return self

    def fill_field(self, field_key: str, value: str) -> None:
        if field_key in SELECT_FIELDS:
            self.select_option(self.FIELD_LOCATORS[field_key], label=value)
        else:
            self.type(self.FIELD_LOCATORS[field_key], value)

    def fill_step1(self, overrides: dict | None = None, skip: str | None = None) -> "MediationPage":
        """Fills every Step 01 field from STEP1_SAMPLE_VALUES, optionally
        skipping one field key (left empty) and/or overriding others."""
        values = {**STEP1_SAMPLE_VALUES, **(overrides or {})}
        for key, value in values.items():
            if key == skip:
                continue
            self.fill_field(key, value)
        return self

    def advance_to_step2(self) -> "MediationPage":
        self.fill_step1()
        self.click(self.NEXT_BUTTON)
        self.wait_for(self.FIELD_RESPONDENT_COMPANY_NAME)
        return self

    def fill_step2(self, overrides: dict | None = None, skip: str | None = None) -> "MediationPage":
        values = {**STEP2_SAMPLE_VALUES, **(overrides or {})}
        for key, value in values.items():
            if key == skip:
                continue
            self.fill_field(key, value)
        return self

    def click_next(self) -> "MediationPage":
        self.click(self.NEXT_BUTTON)
        return self

    def current_step_text(self) -> str:
        return self.text(self.STEP_INDICATOR)

    def field_value(self, field_key: str) -> str:
        return self.page.locator(self.FIELD_LOCATORS[field_key]).input_value()

    def field_error_text(self, field_key: str) -> str:
        """Reads the inline required-field error rendered for the given
        field, addressed by that field's own `data-qc-med-error` name."""
        locator = self.ERROR_BY_FIELD.format(name=self.FIELD_NAMES[field_key])
        return self.text(locator)

    def field_is_marked_invalid(self, field_key: str) -> bool:
        """True when the field itself carries the wizard's invalid styling —
        the visual half of the validation the cases assert on."""
        classes = self.page.locator(self.FIELD_LOCATORS[field_key]).get_attribute("class") or ""
        return self.INVALID_INPUT_CLASS in classes.split()

    def next_button_is_enabled(self) -> bool:
        return self.page.locator(self.NEXT_BUTTON).is_enabled()

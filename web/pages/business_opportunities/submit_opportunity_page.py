"""
web/pages/business_opportunities/submit_opportunity_page.py —
SubmitBusinessOpportunityPage.

Public-frontend Page Object for PBI 130697 (INVEST — Business Opportunities)'s
"Submit a Business Opportunity" webform: 4 field groups (Basic Info,
Opportunity Details, Media & Documents, Contact Information), a CAPTCHA and a
Submit button.

LOCATORS — CLI-first, verified live 2026-09-22 (qcdev)
------------------------------------------------------------------
Real path resolved via the "Submit Opportunity" CTA's `href` on the listing
page (`a.qc-bol-cta`), confirmed as `/web/qatar-chamber/submit-business-opportunity`
— an ad-hoc structural dump (scripted, not MCP) then enumerated every field
in the live form. Every field carries a stable, unique `id` (`#qc-bos-*`) —
the framework's highest confirmed tier here. The real CSS namespace is
`qc-bos__*` (BEM-style), not the guessed `qc-bosub-*`.

Two labelling surprises worth flagging to devs (see the batch report):
the Contact group's "full name" field renders with the visible label
"Contact Information" (id `qc-bos-contactInformation`) rather than
"Contact Full Name"/"Contact Person" — kept mapped to this batch's
`contact_full_name` field key since it is that field's only candidate.
`investment_brief_en` / `investment_brief_ar` are plain `<textarea>`
elements (with a live character counter), not the contenteditable rich-text
control the original placeholder assumed — `type()` still fills them
correctly, so no fill-logic changed, only the locator value.

Field-key data-map design, mirroring the pattern already used in this
framework (`web/pages/mediation/mediation_page.py`'s FIELD_LOCATORS /
FIELD_NAMES / fill_field()): a single generic `fill_field()` /
`field_error_text()` pair driven by one FIELD_LOCATORS map keeps the ~19
mandatory-field cases in this batch as one data-driven family instead of one
near-identical method per field.
"""

from config.settings import web_url
from core.web.base_page import BasePage

PATH = "/web/qatar-chamber/submit-business-opportunity"

# Text-input / textarea / rich-text fields filled via type().
TEXT_FIELD_KEYS = (
    "name_en",
    "name_ar",
    "company_name",
    "investment_brief_en",
    "investment_brief_ar",
    "key_highlights",
    "investment_amount",
    "contact_full_name",
    "contact_email",
    "contact_mobile",
    "contact_website",
)
# <select> fields filled via select_option().
SELECT_FIELD_KEYS = ("sector", "sub_sector", "country", "currency", "investment_type", "timeline", "risk_profile")
# Multi-select field(s) — filled by one or more select_option() calls.
MULTI_SELECT_FIELD_KEYS = ("industry_pool",)
# File-upload fields filled via upload_file().
UPLOAD_FIELD_KEYS = ("banner_image", "opportunity_logo", "gallery_images", "supporting_documents")

ALL_FIELD_KEYS = TEXT_FIELD_KEYS + SELECT_FIELD_KEYS + MULTI_SELECT_FIELD_KEYS + UPLOAD_FIELD_KEYS

# Realistic sample values for "fill every OTHER mandatory field with valid
# data" steps — mirrors this batch's own "Fill the remaining mandatory
# fields" wording. Arbitrary but plausible; never the value under assertion
# in a field-level case (that case supplies its own concrete value).
SAMPLE_VALUES = {
    "name_en": "Solar Energy Park Expansion",
    "name_ar": "توسعة مجمع الطاقة الشمسية",
    "sector": "Energy",
    "sub_sector": "Renewable Energy",
    "country": "Qatar",
    "company_name": "Doha Green Investments LLC",
    "investment_brief_en": "A renewable-energy expansion opportunity with strong projected returns.",
    "investment_brief_ar": "فرصة استثمارية في توسعة الطاقة المتجددة بعوائد متوقعة قوية.",
    "key_highlights": "High ROI, government-backed PPP structure, and a 3-year payback period.",
    "investment_amount": "5000000",
    "currency": "QAR",
    "investment_type": "Joint Venture",
    "timeline": "6-12 months",
    "risk_profile": "Medium",
    "industry_pool": ["Energy", "Infrastructure"],
    "contact_full_name": "Ahmed Al-Kuwari",
    "contact_email": "ahmed.alkuwari@dohagreeninvest.com",
    "contact_mobile": "5512 3456",
    "contact_website": "https://www.dohagreeninvest.com",
}


class SubmitBusinessOpportunityPage(BasePage):
    # ---- Field groups -----------------------------------------------------
    # 4 groups render as identical `section.qc-bos__group` elements in DOM
    # order (Basic Information, Opportunity Details, Media & Documents,
    # Contact Information) — no per-group class, so positional CSS is the
    # highest confirmed tier.
    GROUP_BASIC_INFO = "section.qc-bos__group:nth-of-type(1)"  # "Basic Information" group section
    GROUP_OPPORTUNITY_DETAILS = "section.qc-bos__group:nth-of-type(2)"  # "Opportunity Details" group
    GROUP_MEDIA_DOCUMENTS = "section.qc-bos__group:nth-of-type(3)"  # "Media & Documents" group
    GROUP_CONTACT_INFO = "section.qc-bos__group:nth-of-type(4)"  # "Contact Information" group
    GROUP_HEADER = "h2.qc-bos__grouphead span.qc-bos__grouphead-label"  # one group section header label

    # ---- CAPTCHA / submit ---------------------------------------------------
    CAPTCHA_MOUNT = "div.qc-bos__captcha"  # webform CAPTCHA mount node (under "Security Check")
    SUBMIT_BUTTON = "button.qc-bos__submit"  # "Submit" button
    SUCCESS_MESSAGE = "div.qc-bos__done"  # post-submit success/confirmation panel ("Submission received")
    GENERIC_ERROR = "div.qc-bos__status"  # top-level submission status/error banner

    # ---- Mobile country-code prefix -----------------------------------------
    CONTACT_MOBILE_COUNTRY_CODE = "span.qc-bos__dial-code"  # contact mobile "+974" prefix indicator

    FIELD_LOCATORS = {
        "name_en": "#qc-bos-projectOpportunityName",  # Project/Opportunity Name (EN)
        "name_ar": "#qc-bos-projectOpportunityNameAr",  # Project/Opportunity Name (AR)
        "sector": "#qc-bos-sector",  # Sector dropdown
        "sub_sector": "#qc-bos-subSector",  # Sub-Sector dropdown (optional)
        "country": "#qc-bos-country",  # Country dropdown
        "company_name": "#qc-bos-companyOrganizationName",  # Company/Organization Name
        "investment_brief_en": "#qc-bos-investmentBrief",  # Investment Brief (EN) — plain textarea, not rich text
        "investment_brief_ar": "#qc-bos-investmentBriefAr",  # Investment Brief (AR) — plain textarea, not rich text
        "key_highlights": "#qc-bos-keyHighlights",  # Key Highlights textarea
        "investment_amount": "#qc-bos-investmentAmount",  # Investment Amount
        "currency": "#qc-bos-currency",  # Currency dropdown
        "investment_type": "#qc-bos-investmentType",  # Investment Type dropdown
        "timeline": "#qc-bos-timeline",  # Timeline dropdown
        "risk_profile": "#qc-bos-riskProfile",  # Risk Profile dropdown
        "industry_pool": "#qc-bos-industryPool",  # Industry Pool multi-select
        "banner_image": "#qc-bos-bannerImage",  # Banner Image upload control
        "opportunity_logo": "#qc-bos-opportunityLogo",  # Opportunity Logo upload control
        "gallery_images": "#qc-bos-galleryImages",  # Gallery Images upload control
        "supporting_documents": "#qc-bos-supportingDocuments",  # Supporting Documents upload control
        # Renders with visible label "Contact Information" on the live form,
        # not "Contact Full Name" — kept on this field key as its only
        # candidate; flag to devs (see batch report) if a distinct name field
        # is intended.
        "contact_full_name": "#qc-bos-contactInformation",  # Contact "Full Name" input (labelled "Contact Information" live)
        "contact_email": "#qc-bos-contactEmail",  # Contact Email
        "contact_mobile": "#qc-bos-mobileNumber",  # Contact Mobile Number (digits only; +974 prefix is a separate display chip)
        "contact_website": "#qc-bos-website",  # Contact Website (optional)
    }
    # Each field's error `<span class="qc-bos__error">` is the last child of
    # its own `.qc-bos__field` wrapper, with no per-field data attribute —
    # `:has()` scopes to the wrapper containing this field's confirmed id.
    FIELD_ERROR_LOCATORS = {
        key: f"div.qc-bos__field:has({FIELD_LOCATORS_ID}) span.qc-bos__error"
        for key, FIELD_LOCATORS_ID in {
            "name_en": "#qc-bos-projectOpportunityName",
            "name_ar": "#qc-bos-projectOpportunityNameAr",
            "sector": "#qc-bos-sector",
            "sub_sector": "#qc-bos-subSector",
            "country": "#qc-bos-country",
            "company_name": "#qc-bos-companyOrganizationName",
            "investment_brief_en": "#qc-bos-investmentBrief",
            "investment_brief_ar": "#qc-bos-investmentBriefAr",
            "key_highlights": "#qc-bos-keyHighlights",
            "investment_amount": "#qc-bos-investmentAmount",
            "currency": "#qc-bos-currency",
            "investment_type": "#qc-bos-investmentType",
            "timeline": "#qc-bos-timeline",
            "risk_profile": "#qc-bos-riskProfile",
            "industry_pool": "#qc-bos-industryPool",
            "banner_image": "#qc-bos-bannerImage",
            "opportunity_logo": "#qc-bos-opportunityLogo",
            "gallery_images": "#qc-bos-galleryImages",
            "supporting_documents": "#qc-bos-supportingDocuments",
            "contact_full_name": "#qc-bos-contactInformation",
            "contact_email": "#qc-bos-contactEmail",
            "contact_mobile": "#qc-bos-mobileNumber",
            "contact_website": "#qc-bos-website",
        }.items()
    }
    # TODO(locator): no per-field thumbnail/preview class was observed on the
    # live drop-zones at extraction time (only icon/CTA/hint text nodes) —
    # flag for dev-added data-testid once an uploaded-file preview state
    # exists to inspect.
    FIELD_THUMBNAIL_LOCATORS = {
        key: f"TODO(locator): uploaded-file thumbnail/preview for {key} — not observed on the live drop-zone"
        for key in UPLOAD_FIELD_KEYS
    }

    # ---- Navigation -----------------------------------------------------------
    def open_submit_form(self, locale: str = "en") -> "SubmitBusinessOpportunityPage":
        self.open(web_url(PATH, locale=locale))
        self.wait_for(self.SUBMIT_BUTTON, state="visible", timeout=30000)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def group_header_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.GROUP_HEADER).all_inner_texts()]

    # ---- Field-driven fill / read -------------------------------------------
    def fill_field(self, field_key: str, value) -> None:
        locator = self.FIELD_LOCATORS[field_key]
        if field_key in SELECT_FIELD_KEYS:
            self.select_option(locator, label=value)
        elif field_key in MULTI_SELECT_FIELD_KEYS:
            self.page.locator(locator).select_option(label=value if isinstance(value, list) else [value])
        elif field_key in UPLOAD_FIELD_KEYS:
            self.upload_file(locator, value)
        else:
            self.type(locator, value)

    def fill_form(self, overrides: dict | None = None, skip: str | None = None) -> "SubmitBusinessOpportunityPage":
        """Fills every mandatory field from SAMPLE_VALUES, optionally
        skipping one field key (left empty, for a "missing field" case) and/
        or overriding others with a case's own concrete test data."""
        values = {**SAMPLE_VALUES, **(overrides or {})}
        for key, value in values.items():
            if key == skip:
                continue
            self.fill_field(key, value)
        return self

    def field_value(self, field_key: str) -> str:
        return self.get_attribute(self.FIELD_LOCATORS[field_key], "value") or ""

    def field_error_text(self, field_key: str) -> str:
        return self.text(self.FIELD_ERROR_LOCATORS[field_key]).strip()

    def is_field_error_visible(self, field_key: str) -> bool:
        return self.is_visible(self.FIELD_ERROR_LOCATORS[field_key])

    def select_options(self, field_key: str) -> list:
        return [t.strip() for t in self.page.locator(f"{self.FIELD_LOCATORS[field_key]} option").all_inner_texts()]

    def selected_option(self, field_key: str) -> str:
        return self.page.locator(self.FIELD_LOCATORS[field_key]).locator("option:checked").inner_text().strip()

    def is_upload_thumbnail_visible(self, field_key: str) -> bool:
        return self.is_visible(self.FIELD_THUMBNAIL_LOCATORS[field_key])

    def contact_mobile_country_code_text(self) -> str:
        return self.text(self.CONTACT_MOBILE_COUNTRY_CODE).strip()

    # ---- CAPTCHA / submit ---------------------------------------------------
    def is_captcha_present(self) -> bool:
        return self.page.locator(self.CAPTCHA_MOUNT).count() > 0

    def click_submit(self) -> "SubmitBusinessOpportunityPage":
        self.click(self.SUBMIT_BUTTON)
        return self

    def is_submit_button_disabled(self) -> bool:
        return self.get_attribute(self.SUBMIT_BUTTON, "disabled") is not None

    def success_message_text(self) -> str:
        return self.text(self.SUCCESS_MESSAGE).strip()

    def is_success_visible(self) -> bool:
        return self.is_visible(self.SUCCESS_MESSAGE)

    def generic_error_text(self) -> str:
        return self.text(self.GENERIC_ERROR).strip()

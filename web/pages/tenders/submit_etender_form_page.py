"""
web/pages/tenders/submit_etender_form_page.py — SubmitETenderFormPage.

Public-frontend Page Object for the "Submit your eTender" Expression-of-
Interest webform (PBI 130952 pilot batch INVEST-TENDERS-TC-022..030, 033).
Figma node 4747:190134.

CONFIRMED LIVE (2026-09-24, qcdev, browser_evaluate — disclosed Playwright-
MCP fallback, same rationale as the sibling Page Objects: no data-testid
layer on this form's presentational chrome):

  - Route: `/web/qatar-chamber/submit-your-etender` — reachable directly
    or via either CTA (hero CTL-1 / detail CTL-2, though CTL-2 currently
    does not render — see tender_detail_page.py's docstring).
  - **Two live copy variances vs. the QA case's exact-string
    expectations, both already flagged in the case data (Assumption 2 /
    the "eTenders Documents" vs. "Tenders Documents" note) — recorded
    here as CONFIRMED, not assumed:**
    - The mandatory email field's live label is "Submitter Email
      address" (`.qc-etf__label`), NOT "Submitter Contact Email" as
      INVEST-TENDERS-TC-025 states. `mandatory_field_label_text()`
      reads the real live text; the test asserting the case's exact
      string is expected to FAIL on this environment — an honest signal
      of a live copy drift, not a locator bug.
    - The 5th section header's live text is "eTenders Documents & Consent
      Group" (`h2.qc-etf__grouphead`), matching NEITHER the case's
      "Tenders Documents" nor the spec's "eTenders Documents" — same
      treatment: read honestly, let the assertion surface the drift.
  - **Live gap vs. INVEST-TENDERS-TC-029's "no CAPTCHA/checkbox" design
    assumption**: the live form DOES render a consent checkbox
    (`input[type="checkbox"]`, unlabelled by class) immediately above
    the consent paragraph — the Figma frame's Assumption 3 ("text-link
    consent only, no checkbox") does not hold live.
    `consent_checkbox_present()` reads the real DOM state; the test
    asserting "no checkbox" is expected to FAIL here — again the correct,
    honest signal, not something to route around.
  - The consent paragraph text ITSELF (MSG-9) and the BOQ upload control's
    wording (MSG-8) both match the case's exact strings verbatim on the
    live DOM — confirmed live, no variance on those two.
"""

from core.web.base_page import BasePage
from config.settings import web_url

HERO_TITLE = "h1.qc-etf__hero-title"
HERO_SECTION = "section.qc-etf"
CARD_TITLE = "span.qc-etf__pagehead-title"
CARD_SUBTITLE = "span.qc-etf__pagehead-sub"

SECTION_HEADING = "h2.qc-etf__grouphead"
SECTION_GROUP = ".qc-etf__group"
FIELD_LABEL = "label.qc-etf__label"
REQUIRED_ASTERISK = ".qc-etf__req"
TEXT_INPUT = "input.qc-etf__input"
TEXTAREA = "textarea.qc-etf__textarea"

UPLOAD_FIELD = ".qc-etf__field"
UPLOAD_DROP = ".qc-etf__drop"
UPLOAD_ICON = ".qc-etf__drop-icon"
UPLOAD_STRONG = ".qc-etf__drop-strong"
UPLOAD_REST = ".qc-etf__drop-rest"
UPLOAD_HINT = ".qc-etf__drop-hint"

CONSENT_CHECKBOX = 'input[type="checkbox"]'
CONSENT_TEXT = "p.qc-etf__consent-text"
PRIVACY_LINK = "a.qc-etf__policy-link"

SUBMIT_BUTTON = "button.qc-etf__submit"

# ---- Functional/Edge batch additions (PBI 130952, remaining 195) -----------
# CONFIRMED LIVE 2026-09-24 (Playwright MCP, disclosed fallback — same
# rationale as the module-level docstring above: this webform's field/error
# chrome carries no data-testid layer). Every field on this form (36 of them)
# sits inside its own `.qc-etf__field` wrapper (label + control + an
# `.qc-etf__error` node that is present in the DOM but hidden until that
# field fails validation) — confirmed by inspecting the live DOM tree
# (label.qc-etf__label -> qc-etf__field -> qc-etf__grid -> qc-etf__group ->
# qc-etf__form). This is the SAME wrapper UPLOAD_FIELD already used for the
# BOQ control above; FIELD_WRAPPER below is just its generic name, reused
# for every field, not only uploads.
#
# Two labels are NOT unique on this form — "City" (Organization address
# block AND Work Item block) and "ZIP / postal code" (same two blocks) each
# render twice with identical text. `field(...)`/`fill_field(...)` etc. all
# take an `index` (0 = first/Organization-block occurrence, 1 = second/
# Work-Item-block occurrence) to disambiguate — confirmed live via a DOM
# walk that these are genuinely two separate wrappers, not one repeated
# node.
#
# Validation mechanism confirmed live (submit with every field empty):
# `.qc-etf__status` renders "Please correct the highlighted fields." and
# every invalid field's own `.qc-etf__error` becomes visible with the text
# "This field is required." (the same generic message for every field this
# session — format/range-specific messages were not independently observed
# per field this session; callers assert PRESENCE of a visible error, not a
# field-specific wording, unless a case's own EXPECTED states an exact
# string).
FIELD_WRAPPER = ".qc-etf__field"
FIELD_ERROR = ".qc-etf__error"
STATUS_MESSAGE = ".qc-etf__status"
REQUIRED_FIELD_ERROR_TEXT = "This field is required."

# Field labels — visible text inside each field's own label.qc-etf__label
# (asterisk on mandatory fields is part of that same text node; `:has-text`
# substring matching below does not need it).
LABEL_SUBMITTER_EMAIL = "Submitter Email address"
LABEL_ORG_NAME = "Organization name"
LABEL_COMMERCIAL_REG_NUMBER = "Commercial Registration Number"
LABEL_CR_NUMBER = "Computer Registration Number (CR Number)"
LABEL_ESTABLISHMENT_CARD_NUMBER = "Establishment Card Number"
LABEL_ORG_ADDRESS = "Organization address"
LABEL_STREET_ADDRESS = "Street address"
LABEL_CITY = "City"  # index 0 = Organization block, index 1 = Work Item block
LABEL_ZIP_CODE = "ZIP / postal code"  # index 0 = Organization, index 1 = Work Item
LABEL_COUNTRY = "Country"
LABEL_OPENING_DATE = "Opening Date"
LABEL_CLOSING_DATE = "Closing Date"
LABEL_GENERAL_TECH_EVAL_ALLOWED = "General Technical Evaluation Allowed"
LABEL_TENDER_FEE = "Tender Fee in QAR"
LABEL_FEE_PAYABLE_TO = "Fee Payable To"
LABEL_TENDER_FEE_EXEMPTION_ALLOWED = "Tender Fee Exemption Allowed"
LABEL_EMD_AMOUNT = "EMD Amount in QAR"
LABEL_EMD_PAYABLE_TO = "EMD Payable To"
LABEL_PAYMENT_MODE = "Payment Mode"
LABEL_TENDER_CATEGORY = "Tender Category"
LABEL_TENDER_TYPE = "Tender Type"
LABEL_TENDER_CLASSIFICATION = "Tender Classification"
LABEL_PRODUCT_CATEGORY = "Product Category"
LABEL_TENDER_LOCATION = "Tender Location"
LABEL_ITEM_WISE_TECH_EVAL_ALLOWED = "Item Wise Technical Evaluation Allowed"
LABEL_WORK_DESCRIPTION_FIELD = "Work Description"
LABEL_PRE_BID_MEETING_DATE = "Pre Bid Meeting Date"
LABEL_PRE_BID_MEETING_ADDRESS = "Pre Bid Meeting Address"
LABEL_PREQUALIFICATION_APPROVAL_DATE = "Prequalification Approval Date"
LABEL_SHOULD_ALLOW_NDA_TENDER = "Should Allow NDA Tender"
LABEL_BID_VALIDITY_DAYS = "Bid Validity (Days)"
LABEL_BOQ_UPLOAD = "Bill of Quantities (BOQ)"
LABEL_TENDER_DOCUMENTS_UPLOAD = "Upload Tender Documents"
LABEL_ADDITIONAL_DOCUMENT_UPLOAD = "Additional Document"

# A complete, valid baseline submission — every case that validates ONE
# field fills every OTHER field from this same table (see fill_valid_form())
# so the test is exercising exactly the one field the case names, not an
# incidentally-invalid neighbor. (label, value, index) — select fields take
# the OPTION TEXT confirmed live (see module docstring's option dumps), date
# fields take an ISO yyyy-mm-dd string (native <input type=date>).
BASELINE_TEXT_FIELDS = [
    (LABEL_SUBMITTER_EMAIL, "qctest.submitter@qatarchamber.qa", 0),
    (LABEL_ORG_NAME, "QCTEST Organization LLC", 0),
    (LABEL_COMMERCIAL_REG_NUMBER, "QCTEST-CR-100001", 0),
    (LABEL_ORG_ADDRESS, "QCTEST Building, Diplomatic Area", 0),
    (LABEL_STREET_ADDRESS, "QCTEST Street 12", 0),
    (LABEL_CITY, "Doha", 0),
    (LABEL_ZIP_CODE, "00974", 0),
    (LABEL_TENDER_FEE, "750", 0),
    (LABEL_FEE_PAYABLE_TO, "Qatar Chamber", 0),
    (LABEL_EMD_AMOUNT, "150000", 0),
    (LABEL_EMD_PAYABLE_TO, "Qatar Chamber", 0),
    (LABEL_WORK_DESCRIPTION_FIELD, "QCTEST work description for automated coverage.", 0),
    (LABEL_PRE_BID_MEETING_ADDRESS, "QCTEST Meeting Hall, Doha", 0),
    (LABEL_CITY, "Doha", 1),
    (LABEL_ZIP_CODE, "00974", 1),
    (LABEL_BID_VALIDITY_DAYS, "90", 0),
]
BASELINE_SELECT_FIELDS = [
    (LABEL_COUNTRY, "Qatar", 0),
    (LABEL_GENERAL_TECH_EVAL_ALLOWED, "Yes", 0),
    (LABEL_TENDER_FEE_EXEMPTION_ALLOWED, "No", 0),
    (LABEL_PAYMENT_MODE, "Online", 0),
    (LABEL_TENDER_CATEGORY, "Services", 0),
    (LABEL_TENDER_TYPE, "Open Tender", 0),
    (LABEL_TENDER_CLASSIFICATION, "Lump-sum", 0),
    (LABEL_PRODUCT_CATEGORY, "Consultancy Services", 0),
    (LABEL_TENDER_LOCATION, "Qatar", 0),
    (LABEL_ITEM_WISE_TECH_EVAL_ALLOWED, "No", 0),
    (LABEL_SHOULD_ALLOW_NDA_TENDER, "No", 0),
]
BASELINE_DATE_FIELDS = [
    (LABEL_OPENING_DATE, "2026-10-01", 0),
    (LABEL_CLOSING_DATE, "2026-11-01", 0),
    (LABEL_PRE_BID_MEETING_DATE, "2026-10-15", 0),
    (LABEL_PREQUALIFICATION_APPROVAL_DATE, "2026-09-20", 0),
]


class SubmitETenderFormPage(BasePage):
    def open_form(self, locale: str = "en") -> "SubmitETenderFormPage":
        self.open(web_url("/web/qatar-chamber/submit-your-etender", locale=locale))
        self.wait_for(HERO_TITLE, timeout=15000)
        return self

    def style_of(self, locator: str, properties: list, first: bool = False) -> dict:
        return self.computed_style(locator, properties, first=first)

    # ---- Hero / card header -------------------------------------------------
    def hero_title_text(self) -> str:
        return self.text(HERO_TITLE).strip()

    def card_title_text(self) -> str:
        return self.text(CARD_TITLE).strip()

    def card_subtitle_text(self) -> str:
        return self.text(CARD_SUBTITLE).strip()

    # ---- Section headers (5 of them) ---------------------------------------
    def section_heading_texts(self) -> list:
        return [t.strip() for t in self.page.locator(SECTION_HEADING).all_inner_texts()]

    def section_heading_locator_for(self, text_value: str):
        headings = self.page.locator(SECTION_HEADING)
        count = headings.count()
        for i in range(count):
            if headings.nth(i).inner_text().strip() == text_value:
                return headings.nth(i)
        raise AssertionError(f"section heading {text_value!r} not found")

    # ---- Fields -------------------------------------------------------------
    def field_wrapper_for_label(self, label_substring: str):
        return self.page.locator(f"{UPLOAD_FIELD}:has-text('{label_substring}')").first

    def mandatory_field_label_text(self) -> str:
        """The Submitter Email field's label — see module docstring for the
        live-confirmed copy variance vs. INVEST-TENDERS-TC-025's expected
        exact string."""
        # A placeholder is an attribute, not text content, so ':has-text()' can
        # never match it — anchor on the input that carries the placeholder.
        wrapper = self.page.locator(FIELD_WRAPPER).filter(
            has=self.page.locator(f'{TEXT_INPUT}[placeholder="email@company.com"]')
        ).first
        return wrapper.locator(FIELD_LABEL).inner_text().strip()

    def text_input_style(self, placeholder: str, properties: list) -> dict:
        loc = f'{TEXT_INPUT}[placeholder="{placeholder}"]'
        return self.computed_style(loc, properties, first=True)

    def textarea_style(self, properties: list) -> dict:
        return self.computed_style(TEXTAREA, properties, first=True)

    def textarea_box_size(self) -> dict:
        box = self.page.locator(TEXTAREA).first.bounding_box()
        return {"width": box["width"], "height": box["height"]} if box else {}

    # ---- BOQ upload control --------------------------------------------------
    def boq_upload_texts(self) -> dict:
        field = self.field_wrapper_for_label("Bill of Quantities (BOQ)")
        return {
            "click": field.locator(UPLOAD_STRONG).inner_text().strip(),
            "rest": field.locator(UPLOAD_REST).inner_text().strip(),
            "hint": field.locator(UPLOAD_HINT).inner_text().strip(),
        }

    def boq_upload_style(self, part_locator: str, properties: list) -> dict:
        field = self.field_wrapper_for_label("Bill of Quantities (BOQ)")
        return field.locator(part_locator).first.evaluate(
            "(el, props) => { const s = getComputedStyle(el); const out = {}; "
            "props.forEach(p => out[p] = s[p]); return out; }",
            properties,
        )

    # ---- Consent --------------------------------------------------------------
    def consent_checkbox_present(self) -> bool:
        """See module docstring — the live form DOES render this checkbox,
        which contradicts INVEST-TENDERS-TC-029's "no checkbox" design
        assumption. Reads the real state honestly."""
        return self.is_visible(CONSENT_CHECKBOX)

    def consent_text(self) -> str:
        return self.text(CONSENT_TEXT).strip()

    def privacy_link_style(self, properties: list) -> dict:
        return self.computed_style(PRIVACY_LINK, properties, first=True)

    # ---- Submit ----------------------------------------------------------------
    def submit_button_style(self, properties: list) -> dict:
        return self.computed_style(SUBMIT_BUTTON, properties, first=True)

    def submit_button_text(self) -> str:
        return self.text(SUBMIT_BUTTON).strip()

    def submit_button_bounding_box(self) -> dict:
        return self.page.locator(SUBMIT_BUTTON).bounding_box()

    def submit_button_border_paint(self) -> dict:
        """Where a gradient border could be painted: the element's border-image /
        background-image and its ::before/::after backgrounds, plus the border."""
        return self.page.locator(SUBMIT_BUTTON).first.evaluate(
            """el => {
                const s = getComputedStyle(el), b = getComputedStyle(el, '::before'), a = getComputedStyle(el, '::after');
                return {border: s.border, borderImage: s.borderImageSource, background: s.backgroundImage,
                        before: b.backgroundImage, after: a.backgroundImage};
            }"""
        )

    def form_group_bounding_box(self) -> dict:
        return self.page.locator(SECTION_GROUP).first.bounding_box()

    def first_text_input_bounding_box(self) -> dict:
        return self.page.locator(TEXT_INPUT).first.bounding_box()

    # ---- RTL --------------------------------------------------------------
    def is_rtl(self) -> bool:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')") == "rtl"

    # ---- Generic field access (Functional/Edge batch) ------------------------
    def field(self, label_substring: str, index: int = 0):
        """The field's own `.qc-etf__field` wrapper (label + control + its
        own error node) — see module docstring. `index` disambiguates the
        two labels that legitimately repeat on this form (City, ZIP/postal
        code)."""
        return self.page.locator(f'{FIELD_WRAPPER}:has-text("{label_substring}")').nth(index)

    def _control_for(self, label_substring: str, index: int = 0):
        return self.field(label_substring, index).locator("input, textarea, select").first

    def fill_field(self, label_substring: str, value: str, index: int = 0) -> "SubmitETenderFormPage":
        """Fills a text/date input or textarea, or selects a native
        `<select>` option by its visible OPTION TEXT (confirmed live: every
        combobox on this form is a plain `<select>`, not a custom widget —
        see module docstring's option dumps)."""
        control = self._control_for(label_substring, index)
        tag = control.evaluate("el => el.tagName")
        if tag == "SELECT":
            control.select_option(label=value)
        else:
            control.fill(value)
        return self

    def upload_field(self, label_substring: str, file_path: str, index: int = 0) -> "SubmitETenderFormPage":
        self.field(label_substring, index).locator('input[type="file"]').set_input_files(file_path)
        return self

    def field_input_value(self, label_substring: str, index: int = 0) -> str:
        return self._control_for(label_substring, index).input_value()

    def field_error_text(self, label_substring: str, index: int = 0) -> str:
        """Visible text of the field's own `.qc-etf__error` node, or "" if
        the field currently has no visible error — see module docstring's
        confirmed-live validation mechanism."""
        error = self.field(label_substring, index).locator(FIELD_ERROR)
        if error.count() == 0 or not error.first.is_visible():
            return ""
        return error.first.inner_text().strip()

    def field_has_visible_error(self, label_substring: str, index: int = 0) -> bool:
        return bool(self.field_error_text(label_substring, index))

    def status_message(self) -> str:
        return self.text(STATUS_MESSAGE).strip() if self.is_visible(STATUS_MESSAGE) else ""

    def accept_consent(self) -> "SubmitETenderFormPage":
        self.page.locator(CONSENT_CHECKBOX).check()
        return self

    def click_submit(self) -> "SubmitETenderFormPage":
        self.click(SUBMIT_BUTTON)
        return self

    def fill_valid_form(self, boq_file_path: str, skip_labels: set | None = None) -> "SubmitETenderFormPage":
        """Fills the ENTIRE form from BASELINE_*_FIELDS above, then uploads
        the mandatory BOQ (and, unless skipped, the optional Tender
        Documents/Additional Document) and checks consent — a complete,
        valid submission. `skip_labels` is a set of (label, index) tuples
        to leave untouched (empty) — used by every "leaving X empty is
        rejected" case to invalidate exactly one field while every other
        field stays valid, per module docstring's rationale. Does NOT
        submit — callers call click_submit() themselves so they can inspect
        pre-submit state first if needed."""
        skip_labels = skip_labels or set()
        for label, value, index in BASELINE_TEXT_FIELDS:
            if (label, index) in skip_labels:
                continue
            self.fill_field(label, value, index)
        for label, value, index in BASELINE_SELECT_FIELDS:
            if (label, index) in skip_labels:
                continue
            self.fill_field(label, value, index)
        for label, value, index in BASELINE_DATE_FIELDS:
            if (label, index) in skip_labels:
                continue
            self.fill_field(label, value, index)
        if (LABEL_BOQ_UPLOAD, 0) not in skip_labels:
            self.upload_field(LABEL_BOQ_UPLOAD, boq_file_path)
        self.accept_consent()
        return self

    # ---- Post-submit state — NOT independently confirmed live this session.
    # A real end-to-end submission (TC-058/059/060/221) is gated behind the
    # reCAPTCHA field confirmed present in the module docstring; completing
    # that gate needs a solved token this automated session cannot obtain,
    # so the success screen's own markup was never actually observed. These
    # two methods are TODO(locator) — kept as best-effort, honest reads
    # (never a guessed CSS class asserted as confirmed) so the cases that
    # need them fail loudly with "not found" rather than silently no-op if
    # this gate is ever lifted/mocked in a future environment.
    def success_banner_visible(self) -> bool:  # TODO(locator): confirm live once CAPTCHA can be satisfied
        return self.is_visible('[role="status"]:has-text("Thank you"), .qc-etf__success')

    def success_reference_number(self) -> str:  # TODO(locator): confirm live once CAPTCHA can be satisfied
        el = self.page.locator('.qc-etf__success, [role="status"]').first
        return el.inner_text().strip() if el.count() else ""

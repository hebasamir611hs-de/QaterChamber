"""
cms/pages/tenders/tender_admin_page.py — TenderAdminPage.

Control_Panel Page Object for PBI 130952's manual-create-tender path
("Path 2" in this PBI's own case wording) — the raw Object Definition
admin surface at `/web/qatar-chamber/manage-tender` (slug "tender").

CONFIRMED LIVE 2026-09-24 (Playwright MCP, authenticated as TEST_USER
against qcdev, disclosed live fallback per automation-standards.md's
Tooling priority — same rationale as the sibling public-frontend Page
Objects under web/pages/tenders/: this admin form's fields carry no
data-testid layer, and the stateless CLI extractor's role-tier harvest
does not reach a multi-step-authenticated Control_Panel surface):

  - `object-authoring`'s index lists exactly ONE Tender-related Object
    Definition reachable at this route: "Tender"
    (`/web/qatar-chamber/manage-tender`). There is NO separate "eTender
    Submissions" review object visible in that index under that name —
    see eoi_submission_admin_page.py's own module docstring for the
    object that actually IS the public webform's backing store
    ("EOISubmission", `/web/qatar-chamber/manage-eoi-submission`).
  - `manage-tender` with no `editEntry` param IS this object's own
    create-new form (same confirmed-live state machine
    ObjectAuthoringPage documents generically) — every field below was
    read directly off that live, blank create form's real `name`
    attributes (`ObjectField_<fieldName>`), confirmed NOT disabled/
    read-only despite a decorative "(Read Only)" string appearing next
    to several labels' help-icon tooltip text (confirmed via
    `el.disabled`/`el.readOnly` on every one of them — all `false`).
    Field labels below are the accessible names Object Authoring's own
    confirmed-live `get_by_role(<role>, name=<label>, exact=True)`
    convention resolves against (see ObjectAuthoringPage's own module
    docstring) — the SAME convention every other Object Definition on
    this project already uses, not independently re-verified role-by-
    role this session beyond the live `name=` attribute dump.
  - `ObjectField_tenderReferenceNumber` carries the native HTML5
    `required` attribute (confirmed live: `el.required === true`) — this
    project's own precedent (object_authoring_page.py's module
    docstring, "native HTML5 'Please fill out this field' validation
    silently blocking Submit") already documents this exact mechanism
    for another object; `field_validity()` below reads
    `checkValidity()`/`validationMessage` directly rather than assuming
    a custom Liferay error banner exists for this field, since none was
    observed in the live DOM for the create form.
  - The entries list showed 15 real PUBLISHED tenders live (Status
    column literally "PUBLISHED ON THE WEBSITE" for every row observed)
    — there is no separate "Submitted"/"Pending"/"Approved" status
    visible on this raw admin surface; those states belong to the
    EOISubmission review flow (Path 1), not to this manually-created
    object's own Draft/Approved lifecycle.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import control_panel_url, settings

TENDER_SLUG = "tender"

ADMIN_HOME_EN_URL_PATH = "/en/home"
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'

# ---- Field labels — confirmed live off the create form's own DOM (see
# module docstring) ----------------------------------------------------------
FIELD_TENDER_REFERENCE_NUMBER = "Tender Reference Number"
FIELD_TENDER_TITLE = "Tender Title"
FIELD_TENDER_TITLE_AR = "Tender Title — العربية"
FIELD_ORGANIZATION_NAME = "Organization Name"
FIELD_ORGANIZATION_NAME_AR = "Organization Name — العربية"
FIELD_OPENING_DATE = "Opening Date"
FIELD_CLOSING_DATE = "Closing Date"
FIELD_PUBLICATION_DATE = "Publication Date"
FIELD_TENDER_CATEGORY = "Tender Category"
FIELD_OVERVIEW_BODY = "Overview Body"
FIELD_OVERVIEW_BODY_AR = "Overview Body — العربية"
FIELD_WORK_DESCRIPTION = "Work Description"
FIELD_WORK_DESCRIPTION_AR = "Work Description — العربية"
FIELD_TENDER_TYPE = "Tender Type"
FIELD_TENDER_CLASSIFICATION = "Tender Classification"
FIELD_PRODUCT_CATEGORY = "Product Category"
FIELD_TENDER_LOCATION = "Tender Location"
FIELD_ORGANIZATION_ADDRESS = "Organization Address"
FIELD_ORGANIZATION_ADDRESS_AR = "Organization Address — العربية"
FIELD_TENDER_FEE = "Tender Fee in QAR"
FIELD_FEE_PAYABLE_TO = "Fee Payable To"
FIELD_FEE_PAYABLE_TO_AR = "Fee Payable To — العربية"
FIELD_TENDER_FEE_EXEMPTION_ALLOWED = "Tender Fee Exemption Allowed"
FIELD_EMD_AMOUNT = "EMD Amount in QAR"
FIELD_EMD_PAYABLE_TO = "EMD Payable To"
FIELD_EMD_PAYABLE_TO_AR = "EMD Payable To — العربية"
FIELD_PAYMENT_MODE = "Payment Mode"
FIELD_GENERAL_TECH_EVAL_ALLOWED = "General Technical Evaluation Allowed"
FIELD_ITEM_WISE_TECH_EVAL_ALLOWED = "Item Wise Technical Evaluation Allowed"
FIELD_PRE_BID_MEETING_DATE = "Pre Bid Meeting Date"
FIELD_PRE_BID_MEETING_ADDRESS = "Pre Bid Meeting Address"
FIELD_PRE_BID_MEETING_ADDRESS_AR = "Pre Bid Meeting Address — العربية"
FIELD_NEED_HELP_CONTACT_EMAIL = "Need Help Contact Email"
FIELD_UPLOAD_TENDER_DOCUMENTS = "Upload Tender Documents"
FIELD_BILL_OF_QUANTITIES = "Bill of Quantities (BOQ)"
FIELD_STATUS = "Status"

# A complete, valid baseline for the manual-create ("Path 2") form —
# mirrors web/pages/tenders/submit_etender_form_page.py's
# BASELINE_*_FIELDS in spirit: every "leaving X empty/invalid is
# rejected" case fills every OTHER field from this table so exactly one
# field is the invalid one under test.
BASELINE_TEXT_FIELDS = {
    FIELD_TENDER_REFERENCE_NUMBER: "QCTEST-REF-0001",
    FIELD_TENDER_TITLE: "QCTEST Manual Tender",
    FIELD_TENDER_TITLE_AR: "مناقصة تجريبية QCTEST",
    FIELD_ORGANIZATION_NAME: "QCTEST Organization",
    FIELD_ORGANIZATION_NAME_AR: "منظمة QCTEST",
    FIELD_OVERVIEW_BODY: "QCTEST overview body.",
    FIELD_WORK_DESCRIPTION: "QCTEST work description.",
    FIELD_WORK_DESCRIPTION_AR: "وصف عمل QCTEST",
    FIELD_ORGANIZATION_ADDRESS: "QCTEST Address, Doha",
    FIELD_ORGANIZATION_ADDRESS_AR: "عنوان QCTEST، الدوحة",
    FIELD_FEE_PAYABLE_TO: "Qatar Chamber",
    FIELD_EMD_PAYABLE_TO: "Qatar Chamber",
    FIELD_PRE_BID_MEETING_ADDRESS: "QCTEST Meeting Hall",
    FIELD_NEED_HELP_CONTACT_EMAIL: "etenders@qcci.org",
}
BASELINE_NUMBER_FIELDS = {
    FIELD_TENDER_FEE: "750",
    FIELD_EMD_AMOUNT: "150000",
}
BASELINE_DATE_FIELDS = {
    FIELD_OPENING_DATE: "2026-10-01",
    FIELD_CLOSING_DATE: "2026-11-01",
    FIELD_PUBLICATION_DATE: "2026-09-25",
    FIELD_PRE_BID_MEETING_DATE: "2026-10-15",
}
BASELINE_COMBOBOX_FIELDS = {
    FIELD_TENDER_CATEGORY: "Services",
    FIELD_TENDER_TYPE: "Open Tender",
    FIELD_TENDER_CLASSIFICATION: "Lump-sum",
    FIELD_PRODUCT_CATEGORY: "Consultancy Services",
    FIELD_TENDER_LOCATION: "Qatar",
    FIELD_TENDER_FEE_EXEMPTION_ALLOWED: "No",
    FIELD_PAYMENT_MODE: "Online",
    FIELD_GENERAL_TECH_EVAL_ALLOWED: "Yes",
    FIELD_ITEM_WISE_TECH_EVAL_ALLOWED: "No",
}


class TenderAdminPage(ObjectAuthoringPage):
    """Drives `manage-tender` (slug="tender") — composes the generic
    ObjectAuthoringPage state machine, adding this object's own field
    actions/baseline data."""

    def __init__(self, page):
        super().__init__(page, TENDER_SLUG)

    def _ensure_logged_in(self, email: str | None = None, password: str | None = None) -> None:
        """Mirrors ChamberEventsAdminPage's confirmed-live "re-login via
        /en/home before hitting manage-<slug> directly" pattern."""
        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            user = email or settings.test_user
            pwd = password or settings.test_password
            login.open_login().login(user, pwd)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_create_form(self, email: str | None = None, password: str | None = None) -> "TenderAdminPage":
        self._ensure_logged_in(email, password)
        self.open_new_entry_form()
        return self

    def open_list(self, email: str | None = None, password: str | None = None) -> "TenderAdminPage":
        self._ensure_logged_in(email, password)
        self.open_entries_list()
        return self

    # ---- Field actions --------------------------------------------------------
    def fill_reference_number(self, value: str) -> "TenderAdminPage":
        self.fill_text(FIELD_TENDER_REFERENCE_NUMBER, value)
        return self

    def fill_date(self, field_label: str, iso_value: str) -> "TenderAdminPage":
        """Native `<input type=date>` — confirmed live for Opening/Closing/
        Publication/Pre Bid Meeting Date. `.fill()` on a date input accepts
        an ISO yyyy-mm-dd string directly (Playwright's own documented
        behavior for this input type)."""
        self.page.get_by_role("textbox", name=field_label, exact=True).fill(iso_value)
        return self

    def select_combobox(self, field_label: str, option_label: str) -> "TenderAdminPage":
        return self.select_combobox_option_for_field(field_label, option_label)

    def select_combobox_option_for_field(self, field_label: str, option_label: str) -> "TenderAdminPage":
        """Mirrors ChamberEventsAdminPage's confirmed-live multi-combobox
        scoping pattern (this object's Tender Category/Type/Classification/
        Product Category/Location/Payment Mode/Yes-No fields are all the
        same Liferay combobox widget, not a native <select> — unlike the
        PUBLIC webform's plain <select> fields, confirmed separately in
        submit_etender_form_page.py)."""
        combobox = self.page.get_by_role("combobox", name=field_label, exact=True)
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        option = self.page.locator(f'#{listbox_id} [role="option"]:text-is("{option_label}")')
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return self

    def upload_tender_document(self, file_path: str) -> "TenderAdminPage":
        self.upload_file(FIELD_UPLOAD_TENDER_DOCUMENTS, file_path)
        return self

    def upload_boq(self, file_path: str) -> "TenderAdminPage":
        self.upload_file(FIELD_BILL_OF_QUANTITIES, file_path)
        return self

    def fill_valid_form(self, boq_file_path: str, skip_fields: set | None = None) -> "TenderAdminPage":
        """Fills the whole create form from BASELINE_*_FIELDS above, minus
        any field named in `skip_fields` (left empty) — the CMS-side
        counterpart of SubmitETenderFormPage.fill_valid_form(), used by
        every "leaving X empty/invalid on manual create is rejected" case
        so only the one field under test is invalid."""
        skip_fields = skip_fields or set()
        for label, value in BASELINE_TEXT_FIELDS.items():
            if label in skip_fields:
                continue
            self.fill_text(label, value)
        for label, value in BASELINE_NUMBER_FIELDS.items():
            if label in skip_fields:
                continue
            self.fill_number(label, value)
        for label, value in BASELINE_DATE_FIELDS.items():
            if label in skip_fields:
                continue
            self.fill_date(label, value)
        for label, value in BASELINE_COMBOBOX_FIELDS.items():
            if label in skip_fields:
                continue
            self.select_combobox_option_for_field(label, value)
        if FIELD_BILL_OF_QUANTITIES not in skip_fields:
            self.upload_boq(boq_file_path)
        return self

    # ---- Validation state -------------------------------------------------------
    def field_validity(self, object_field_name: str) -> dict:
        """Reads native HTML5 constraint-validation state directly off
        `[name="ObjectField_<object_field_name>"]` — see module docstring's
        confirmed-live finding that Tender Reference Number (and, by the
        same Object Authoring framework, every other plain text/number/
        date field on this form) relies on the browser's own `required`
        attribute rather than a custom Liferay error banner. Returns
        `{"valid": bool, "message": str}`; `{"valid": True, "message":
        ""}` if the field is not found (never raises)."""
        return self.page.evaluate(
            """(name) => {
                const el = document.querySelector(`[name="ObjectField_${name}"]`);
                if (!el) return {valid: true, message: ""};
                return {valid: el.checkValidity(), message: el.validationMessage || ""};
            }""",
            object_field_name,
        )

    def row_status_text_for_reference(self, reference_number: str) -> str:
        return self.row_status_text(reference_number)

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


# --- field validation (Agent B) ---
# =============================================================================
# Field-level helpers for PBI 130952's Control_Panel field-validation cases
# (146142-146167, 146295) — cms/tests/tenders/test_tenders_fields_control_panel.py.
#
# Kept in its OWN subclass so nothing here overrides, renames or depends on the
# core TenderAdminPage methods maintained alongside it (only the slug is
# inherited). Everything below was read live 2026-10-05 off `/en/` manage-tender
# as the Site Content Editor (156488):
#
#   - EN text fields are `[name="ObjectField_<key>"]`; their Arabic twins are
#     `#qc-ar-<key>` (no name). Text keys: tenderReferenceNumber, tenderTitle,
#     organizationName, organizationAddress, preBidMeetingAddress,
#     needHelpContactEmail; textarea: workDescription.
#   - Rich text (CKEditor iframes): overviewBody, feePayableTo, emdPayableTo
#     (EN required; the AR editors are optional).
#   - Dates: a visible text box `#qc-dtp-<id>` (dd/mm/yyyy) bound to the hidden
#     `input[type=date][name="ObjectField_<key>"]` (yyyy-mm-dd) whose id is <id>.
#   - Picklists ("select from list"): hidden `input[name="ObjectField_<key>"]`
#     id `<prefix>-value-input`; options `li[role=option][data-option-label]`
#     with ids `<prefix>-option-*`, opened by `button[aria-controls=<prefix>-listbox]`.
#     The list does NOT close on Escape — the toggle is clicked again.
#   - Uploads: tenderDocument / billOfQuantities, help line "Upload a .pdf no
#     larger than 5 MB.", Documents & Media picker iframe.
#   - activeStatus checkbox is TICKED by default; buttons "Save as Draft" /
#     "Publish" (Editor).
#   - Entries list: ENTRY column = Tender Title (EN); every row action carries
#     `data-qc-oel-<action>="<entryId>"` and `data-qc-oel-label="<title>"`;
#     15 real tenders (codes QC-TENDER-130952-NN[-…]) are never acted on.
#
# DELETE SAFETY: same guards as annual_report_admin_page.py — only a record
# THIS test created (captured ref + title + entry id + code, in the
# QCTEST-130952-B- namespace), re-read immediately before the click; never a
# positional, looping or substring delete.
# =============================================================================
import os as _os
import re as _re
import shutil as _shutil
import tempfile as _tempfile
import uuid as _uuid
from dataclasses import dataclass as _dataclass, replace as _replace
from time import monotonic as _monotonic

from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import cms_role_credentials as _cms_role_credentials
from core.utils.logger import get_logger as _get_logger
from core.utils.waits import WaitTimeoutError as _WaitTimeoutError
from core.utils.waits import wait_until as _wait_until
from core.web.overlays import _dismiss_chatbot_launcher

_b_logger = _get_logger("tender_fields_admin_page")

B_QCTEST_PREFIX = "QCTEST-130952-B-"
B_REAL_ENTRY_CODE_PREFIX = "QC-TENDER-130952-"
B_ROLE_EDITOR = "Site Content Editor"
B_ROLE_USER_IDS = {B_ROLE_EDITOR: "156488"}
B_AUTH_FAILED_BANNER_TEXT = "Authentication failed"

B_MSG_DRAFT_SAVED = "Draft saved."
B_MSG_SAVED_AND_PUBLISHED = "Saved and published."
B_MSG_BLOCKED = "Please complete the required fields"
B_MSG_TENDER_DOC_REQUIRED = "Upload Tender Documents is required — upload a file before publishing."
B_MSG_BOQ_REQUIRED = "Bill of Quantities (BOQ) is required — upload a file before publishing."
B_UPLOAD_HELP = "Upload a .pdf no larger than 5 MB."

# Object field keys
K_REF = "tenderReferenceNumber"
K_TITLE = "tenderTitle"
K_ORG = "organizationName"
K_ORG_ADDRESS = "organizationAddress"
K_PREBID_ADDRESS = "preBidMeetingAddress"
K_HELP_EMAIL = "needHelpContactEmail"
K_WORK_DESCRIPTION = "workDescription"
K_OVERVIEW = "overviewBody"
K_FEE_PAYABLE = "feePayableTo"
K_EMD_PAYABLE = "emdPayableTo"
K_OPENING = "openingDate"
K_CLOSING = "closingDate"
K_PUBLICATION = "publicationDate"
K_PREBID_DATE = "preBidMeetingDate"
K_TENDER_FEE = "tenderFee"
K_EMD_AMOUNT = "emdAmount"
K_TENDER_DOCUMENT = "tenderDocument"
K_BOQ = "billOfQuantities"
K_PICKLISTS = ("tenderCategory", "tenderType", "tenderClassification", "productCategory", "tenderLocation",
               "tenderFeeExemptionAllowed", "paymentMode", "generalTechnicalEvaluationAllowed",
               "itemWiseTechnicalEvaluationAllowed", "pageStatus")
B_UPLOAD_LABELS = {K_TENDER_DOCUMENT: "Upload Tender Documents", K_BOQ: "Bill of Quantities (BOQ)"}


@_dataclass(frozen=True)
class TenderCreatedEntry:
    """Identity of a tender THIS test created."""

    title: str
    reference: str
    entry_id: str
    code: str

    def in_namespace(self) -> bool:
        return self.reference.startswith(B_QCTEST_PREFIX) or self.title.strip().startswith(B_QCTEST_PREFIX)

    def with_title(self, title: str) -> "TenderCreatedEntry":
        return _replace(self, title=title)


class TenderFieldsAdminPage(TenderAdminPage):
    """manage-tender field-level helpers (Agent B). See the section notes above."""

    FORM = 'form:has(input[name="ObjectField_tenderReferenceNumber"])'
    SUBMIT_NAME = _re.compile(r"^\s*(Publish|Submit for Review)\s*$")
    SAVE_AS_DRAFT_NAME = _re.compile(r"^\s*Save as Draft\s*$")
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    ENTRY_COUNT = "[data-qc-oel-count]"
    EDITBAR = "[data-qc-oel-editbar]"
    FIELD_ERROR = "[data-qc-oel-field-error]"
    DELETE_LINK_BY_ID = 'a[data-qc-oel-delete="{entry_id}"]'
    ID_ATTRS = ("delete", "history", "view", "approve", "reject", "resubmit", "publish",
                "unpublish", "archive", "restore", "return", "schedule")
    LIST_LOADED = ", ".join(f"[data-qc-oel-{n}]" for n in ID_ATTRS)
    SAVE_REQUEST_PATTERN = _re.compile(r"edit_info_item|/o/c/tenders")
    UPLOAD_REQUEST_PATTERN = _re.compile(r"com_liferay_document_library_web_portlet_DLPortlet.*p_p_lifecycle=1")
    PICKER_ERROR = (".alert-danger, .alert-warning, [role='alert'], .text-danger, .invalid-feedback, "
                    ".form-feedback-item, .lfr-dropzone-error, .upload-error")
    REFUSAL_QUIET_WINDOW_S = 6.0
    SAVE_OUTCOME_TIMEOUT_S = 90.0
    _DOC_MARK = "__qcTenderBBeforeSave"
    EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "evidence", "tenders_130952_b")

    def __init__(self, page):
        super().__init__(page)
        self.owned_entry_ids: set[str] = set()
        self.last_uploaded_name = ""

    # ---- session ----------------------------------------------------------
    def login_as_role(self, role: str) -> str:
        """Real login as `role` in this auth-free context: "ok" / "auth_failed" / "unknown"."""
        email, password = _cms_role_credentials(role)
        login = CmsLoginPage(self.page)
        login.open_login()
        try:
            login.login(email, password)
            return "ok"
        except Exception:  # noqa: BLE001 — classified below
            try:
                self.page.wait_for_load_state("load")
                if self.signed_in_user()[0]:
                    return "ok"
            except Exception:  # noqa: BLE001
                pass
            try:
                body = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001
                body = ""
            return "auth_failed" if B_AUTH_FAILED_BANNER_TEXT in body else "unknown"

    def signed_in_user(self) -> tuple[str, str]:
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']"""
        )
        return info[0], info[1]

    # ---- evidence ------------------------------------------------------------
    def evidence(self, name: str, full_page: bool = True) -> str:
        """Saves a PNG under reports/evidence/tenders_130952_b/ (and attaches it to Allure)."""
        _os.makedirs(self.EVIDENCE_DIR, exist_ok=True)
        path = _os.path.join(self.EVIDENCE_DIR, _re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "tenders")
        except Exception as exc:  # noqa: BLE001 — evidence only
            _b_logger.warning("evidence %s failed: %r", name, exc)
        return path

    # ---- navigation ----------------------------------------------------------
    def open_create_form_en(self) -> "TenderFieldsAdminPage":
        self.open(self._manage_url(locale="en"))
        self._entry_code = None
        self._locale = "en"
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.wait_for(timeout=90000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entry_en(self, code: str) -> "TenderFieldsAdminPage":
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self.page.locator(f'{self.FORM} input[name="ObjectField_{K_REF}"]').first.wait_for(timeout=90000)
        try:
            _wait_until(lambda: self.text_value(K_REF) != "" or self.text_value(K_TITLE) != "",
                        timeout=15.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_list_all(self) -> "TenderFieldsAdminPage":
        self.open(self._manage_url(locale="en"))
        self.wait_for(self.LIST_LOADED, first=True, timeout=90000)
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.first.is_visible() and select.input_value() != "0":
            select.select_option("0")
        total = self.total_entry_count()
        try:
            _wait_until(lambda: total is None or self.rendered_row_count() >= total, timeout=15.0, poll=0.3)
        except _WaitTimeoutError:
            _b_logger.warning("page-size ALL did not settle to %s rows", total)
        _dismiss_chatbot_launcher(self.page)
        return self

    def total_entry_count(self) -> int | None:
        counter = self.page.locator(self.ENTRY_COUNT)
        if counter.count() == 0:
            return None
        match = _re.search(r"(\d+)\s*total", counter.first.inner_text())
        return int(match.group(1)) if match else None

    def rendered_row_count(self) -> int:
        return self.page.locator(f"{self.ENTRIES_TABLE_ROW}:has({self.LIST_LOADED})").count()

    def is_list_fully_expanded(self) -> bool:
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.first.is_visible() and select.input_value() != "0":
            return False
        total = self.total_entry_count()
        return total is not None and self.rendered_row_count() == total

    _ROWS_JS = """(attrs) => [...document.querySelectorAll('table tbody tr')].map(r => {
            const tds = r.querySelectorAll('td');
            let id = '';
            for (const a of attrs) { const n = r.querySelector('[data-qc-oel-' + a + ']');
                                     if (n) { id = n.getAttribute('data-qc-oel-' + a); break; } }
            const del = r.querySelector('a[data-qc-oel-delete]');
            const link = [...r.querySelectorAll('a[href*="editEntry="]')][0];
            let code = '';
            if (link) { const m = link.getAttribute('href').match(/editEntry=([^&#]+)/); code = m ? decodeURIComponent(m[1]) : ''; }
            return {entry_id: id, title: tds[0] ? tds[0].innerText.trim() : '', code: code,
                    status: tds[1] ? tds[1].innerText.trim() : '',
                    delete_id: del ? del.getAttribute('data-qc-oel-delete') : '',
                    label: del ? (del.getAttribute('data-qc-oel-label') || '') : ''};
        }).filter(r => r.entry_id)"""

    def list_rows(self) -> list[dict]:
        return self.page.evaluate(self._ROWS_JS, list(self.ID_ATTRS))

    def snapshot_ids(self) -> set[str]:
        self.open_list_all()
        if not self.is_list_fully_expanded():
            raise AssertionError("the Tender list did not expand to show every row; cannot snapshot ids safely")
        return {r["entry_id"] for r in self.list_rows()}

    def b_leftovers(self) -> list[dict]:
        """Read-only: rows whose title is in the QCTEST-130952-B- namespace."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].startswith(B_QCTEST_PREFIX)]

    def identify_created(self, reference: str, title: str, ids_before: set[str]) -> TenderCreatedEntry | None:
        """The ONE new row (id not in `ids_before`, not a real tender code) whose own
        form reads Reference Number == `reference` (when `reference` is in the
        QCTEST-130952-B- namespace) or else Tender Title == `title`. The
        returned identity carries the title/ref exactly as STORED (a
        whitespace-only title may be stored trimmed)."""
        probe = TenderCreatedEntry(title=title, reference=reference, entry_id="x", code="x")
        if not probe.in_namespace():
            raise ValueError(f"neither {reference!r} nor {title!r} is in the {B_QCTEST_PREFIX} namespace")
        by_ref = reference.startswith(B_QCTEST_PREFIX)
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].startswith(B_REAL_ENTRY_CODE_PREFIX)]
        matches = []
        for row in fresh:
            for attempt in (1, 2):
                try:
                    self.open_entry_en(row["code"])
                    stored_ref, stored_title = self.text_value(K_REF), self.text_value(K_TITLE)
                    if (stored_ref == reference) if by_ref else (stored_title == title):
                        matches.append({**row, "stored_ref": stored_ref, "stored_title": stored_title})
                    break
                except Exception as exc:  # noqa: BLE001 — unreadable row is not ours
                    _b_logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            _b_logger.warning("identify_created(%r): %s matches among new rows %s", reference, len(matches), fresh)
            return None
        entry = TenderCreatedEntry(title=matches[0]["stored_title"], reference=matches[0]["stored_ref"],
                                   entry_id=matches[0]["entry_id"], code=matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def adopt(self, entry: TenderCreatedEntry) -> TenderCreatedEntry:
        if not entry.in_namespace() or not entry.entry_id or not entry.code \
                or entry.code.startswith(B_REAL_ENTRY_CODE_PREFIX):
            raise ValueError(f"refusing to adopt {entry}: not a captured {B_QCTEST_PREFIX} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def row_status(self, entry: TenderCreatedEntry) -> str:
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return normalize_status(rows[0]["status"]) if len(rows) == 1 else ""

    def row_present(self, entry: TenderCreatedEntry) -> bool:
        return any(r["entry_id"] == entry.entry_id for r in self.list_rows())

    # ---- guarded delete -------------------------------------------------------
    def _delete_preconditions(self, entry: TenderCreatedEntry) -> str:
        if not self.is_list_fully_expanded():
            return f"list not fully expanded ({self.rendered_row_count()} of {self.total_entry_count()})"
        links = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
        if links.count() != 1:
            return f"{links.count()} delete links carry id {entry.entry_id}"
        rows = [r for r in self.list_rows() if r["delete_id"] == entry.entry_id]
        if len(rows) != 1:
            return f"{len(rows)} rows carry delete id {entry.entry_id}"
        row = rows[0]
        if row["code"] != entry.code:
            return f"row {entry.entry_id} points at {row['code']!r}, not {entry.code!r}"
        if row["code"].startswith(B_REAL_ENTRY_CODE_PREFIX):
            return f"row {entry.entry_id} has a REAL tender code {row['code']!r}"
        if row["title"].strip() != entry.title.strip() or row["label"].strip() != entry.title.strip():
            return (f"row {entry.entry_id} shows {row['title']!r} / label {row['label']!r}, "
                    f"not the captured {entry.title!r}")
        return ""

    def delete_disposable_entry(self, entry: TenderCreatedEntry) -> bool:
        """Deletes exactly the captured record or refuses (never raises)."""
        try:
            if (not entry.in_namespace() or not entry.entry_id or not entry.code
                    or entry.code.startswith(B_REAL_ENTRY_CODE_PREFIX)
                    or entry.entry_id not in self.owned_entry_ids):
                _b_logger.error("DELETE REFUSED: %r is not a captured %s record", entry, B_QCTEST_PREFIX)
                return False
            self.open_entry_en(entry.code)
            live = (self.text_value(K_REF), self.text_value(K_TITLE))
            if live != (entry.reference, entry.title):
                _b_logger.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
                return False
            self.open_list_all()
            reason = self._delete_preconditions(entry)
            if reason:
                _b_logger.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            reason = self._delete_preconditions(entry)  # re-check immediately before the click
            if reason:
                _b_logger.error("DELETE REFUSED for %r on re-check: %s", entry, reason)
                return False
            names = [n for n in (entry.title.strip(), entry.code) if n]
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                if any(n in dialog.message for n in names):
                    dialog.accept()
                else:
                    dialog.dismiss()

            self.page.on("dialog", _on_dialog)
            try:
                link.click(force=True)
                try:
                    link.wait_for(state="detached", timeout=20000)
                except Exception:  # noqa: BLE001 — verified below
                    pass
            finally:
                self.page.remove_listener("dialog", _on_dialog)
            self.last_delete_dialogs = dialogs
            if not any(any(n in m for n in names) for m in dialogs):
                _b_logger.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            gone = self.is_list_fully_expanded() and not self.row_present(entry)
            if gone:
                _b_logger.info("deleted %r", entry)
            return gone
        except Exception as exc:  # noqa: BLE001
            _b_logger.error("delete of %r failed: %r", entry, exc)
            return False

    # ---- field access -----------------------------------------------------------
    def _form(self):
        return self.page.locator(self.FORM).first

    def _en(self, key: str):
        return self._form().locator(f'[name="ObjectField_{key}"]:not([type="hidden"])').first

    def _ar(self, key: str):
        return self._form().locator(f'[id="qc-ar-{key}"]').first

    def fill_en(self, key: str, value: str) -> "TenderFieldsAdminPage":
        self._en(key).fill(value)
        return self

    def fill_ar(self, key: str, value: str) -> "TenderFieldsAdminPage":
        self._ar(key).fill(value)
        return self

    def text_value(self, key: str) -> str:
        return self._en(key).input_value()

    def ar_value(self, key: str) -> str:
        return self._ar(key).input_value()

    def _rich_iframe(self, key: str) -> str:
        return f'div.cke[class*="-ObjectField_{key}"] iframe[title="editor"]'

    def fill_rich(self, key: str, text: str) -> "TenderFieldsAdminPage":
        self.fill_iframe_editor(self._rich_iframe(key), text)
        return self

    def _date_box(self, key: str):
        hidden_id = self._form().locator(f'input[type="date"][name="ObjectField_{key}"]').first.get_attribute("id")
        return self._form().locator(f'[id="qc-dtp-{hidden_id}"]').first

    def set_date(self, key: str, value: str) -> "TenderFieldsAdminPage":
        """`value` dd/mm/yyyy, typed key by key the way a user would ("" clears)."""
        box = self._date_box(key)
        box.click()
        box.press("Control+A")
        box.press("Delete")
        if value:
            self.page.keyboard.type(value, delay=20)
        box.press("Tab")
        return self

    def date_text(self, key: str) -> str:
        return self._date_box(key).input_value()

    def date_stored(self, key: str) -> str:
        return self._form().locator(f'input[type="date"][name="ObjectField_{key}"]').first.input_value()

    def date_block_text(self, key: str) -> str:
        """Text rendered inside one date field's block (inline messages), calendar noise removed."""
        text = self._date_box(key).evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 6 && c && !c.querySelector('label'); i++) c = c.parentElement;
                       return c ? c.innerText : ''; }"""
        )
        noise = {"?", "‹", "›", "Today", "Clear", ""}
        lines = [ln.strip() for ln in text.split("\n")]
        return " ".join(ln for ln in lines if ln not in noise
                        and not _re.fullmatch(r"[\d\s]+|[A-Z][a-z]{1,2}|[A-Z][a-z]+ \d{4}", ln))

    def _picklist_prefix(self, key: str) -> str:
        hidden_id = self._form().locator(
            f'input[type="hidden"][name="ObjectField_{key}"]').first.get_attribute("id")
        return _re.sub(r"-value-input$", "", hidden_id or "")

    def pick(self, key: str, option_label: str) -> "TenderFieldsAdminPage":
        prefix = self._picklist_prefix(key)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        option = self.page.locator(
            f'li[role="option"][id^="{prefix}-option-"][data-option-label="{option_label}"]')
        toggle.click()
        option.first.wait_for(state="visible", timeout=10000)
        option.first.click()
        hidden = self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]').first
        try:
            _wait_until(lambda: hidden.input_value() != "", timeout=5.0, poll=0.25)
        except _WaitTimeoutError:
            raise AssertionError(f"picking {option_label!r} in {key} left ObjectField_{key} empty") from None
        if self.page.locator(f'li[role="option"][id^="{prefix}-option-"]:visible').count():
            toggle.click()
        return self

    def picklist_value(self, key: str) -> str:
        return self._form().locator(f'input[type="hidden"][name="ObjectField_{key}-label"]').first.input_value()

    def fill_number_key(self, key: str, value: str) -> "TenderFieldsAdminPage":
        self._en(key).fill(value)
        return self

    def set_active_status(self, active: bool) -> "TenderFieldsAdminPage":
        box = self._form().locator('input[type="checkbox"][name="ObjectField_activeStatus"]').first
        box.check() if active else box.uncheck()
        if box.is_checked() != active:
            raise AssertionError(f"Active Status checkbox did not take the value {active}")
        return self

    def active_status_stored(self) -> str:
        box = self._form().locator('input[type="checkbox"][name="ObjectField_activeStatus"]')
        if box.count() == 0:
            return ""
        return "true" if box.first.is_checked() else "false"

    # ---- uploads ----------------------------------------------------------------
    @staticmethod
    def _unique_upload_copy(file_path: str, stem: str | None = None) -> str:
        base, ext = _os.path.splitext(_os.path.basename(file_path))
        folder = _os.path.join(_tempfile.gettempdir(), "qctest_uploads_130952_b")
        _os.makedirs(folder, exist_ok=True)
        target = _os.path.join(folder, f"{stem or base}-{_uuid.uuid4().hex[:8]}{ext}")
        _shutil.copyfile(file_path, target)
        return target

    def _open_picker(self, key: str) -> None:
        hidden = self._form().locator(f'input[name="ObjectField_{key}"]').first
        hidden.locator("xpath=..").get_by_role("button", name="Select File").click()

    def upload(self, key: str, file_path: str, stem: str | None = None) -> "TenderFieldsAdminPage":
        """Uploads a uniquely named copy through the field's picker and closes it with Add."""
        result = self.attempt_upload(key, file_path, stem)
        if not result.get("attached"):
            raise AssertionError(f"upload of {file_path} into {key} was not attached: {result}")
        return self

    def attempt_upload(self, key: str, file_path: str, stem: str | None = None,
                       response_timeout_ms: int = 60000) -> dict:
        """Tries an upload; returns hard evidence {file, status, body, success, errors,
        picker_text, add_clicked, attached, field_text, field_errors}."""
        upload_path = self._unique_upload_copy(file_path, stem)
        result = {"file": _os.path.basename(upload_path), "status": None, "body": "", "success": None,
                  "errors": [], "add_clicked": False, "attached": False, "picker_text": ""}
        self.last_uploaded_name = result["file"]
        self._open_picker(key)
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        try:
            with self.page.expect_response(
                lambda r: r.request.method == "POST" and bool(self.UPLOAD_REQUEST_PATTERN.search(r.url)),
                timeout=response_timeout_ms,
            ) as upload:
                frame.locator('input[type="file"]').set_input_files(upload_path)
            result["status"] = upload.value.status
            try:
                result["body"] = upload.value.text()[:1000]
            except Exception:  # noqa: BLE001
                result["body"] = ""
            compact = result["body"].replace(" ", "")
            if '"success":false' in compact:
                result["success"] = False
            elif '"success":true' in compact or '"file":' in compact:
                result["success"] = True
        except Exception:  # noqa: BLE001 — no upload POST answered
            pass
        finally:
            try:
                _os.remove(upload_path)
            except OSError:
                pass
        errors = frame.locator(self.PICKER_ERROR)
        try:
            _wait_until(lambda: errors.count() > 0 and any(t.strip() for t in errors.all_inner_texts()),
                        timeout=5.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        try:
            result["errors"] = [t.strip() for t in errors.all_inner_texts() if t.strip()]
            result["picker_text"] = " ".join(frame.locator("body").inner_text(timeout=5000).split())[:600]
        except Exception:  # noqa: BLE001
            pass
        modal = self.page.locator(self.UPLOAD_MODAL_IFRAME)
        if result["success"] is True and not result["errors"]:
            add = frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT)

            def _added() -> bool:
                if modal.count() == 0:
                    return True
                try:
                    add.click(timeout=3000)
                    result["add_clicked"] = True
                except Exception:  # noqa: BLE001
                    pass
                return modal.count() == 0

            try:
                _wait_until(_added, timeout=30.0, poll=1.5)
            except _WaitTimeoutError:
                result["errors"] = [t.strip() for t in errors.all_inner_texts() if t.strip()]
        if modal.count():
            result["picker_evidence"] = self.evidence(f"picker_{key}_{result['file']}", full_page=False)
            self.page.keyboard.press("Escape")
            try:
                modal.wait_for(state="detached", timeout=8000)
            except Exception:  # noqa: BLE001
                _b_logger.warning("upload picker did not close on Escape")
        result["field_text"] = self.upload_block_text(key)
        result["field_errors"] = self.field_errors()
        result["attached"] = _os.path.splitext(result["file"])[0] in result["field_text"]
        self.last_upload_attempt = result
        return result

    def upload_block_text(self, key: str) -> str:
        """All text inside one upload field's block (label, help line, selected/current file, messages)."""
        label = B_UPLOAD_LABELS[key]
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return node.evaluate(
            """(el, label) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !(c.innerText || '').includes(label); i++) c = c.parentElement;
                const v = el.value || el.placeholder || '';
                return ((c ? c.innerText : '') + ' ' + v).replace(/\\s+/g, ' ').trim(); }""",
            label,
        )

    def stored_file_name(self, key: str) -> str:
        """Persisted file of a reopened record ("Current file: <name> (<size>)")."""
        match = _re.search(r"Current file:\s*(.+?)\s*(\(|—)", self.upload_block_text(key))
        return match.group(1).strip() if match else ""

    # ---- save / publish with an outcome probe ------------------------------------
    def click_publish(self) -> "TenderFieldsAdminPage":
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def click_save_as_draft(self) -> "TenderFieldsAdminPage":
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SAVE_AS_DRAFT_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def _arm_save_probe(self) -> None:
        self._save_requests: list[str] = []
        self._save_responses: list[int] = []
        self._navigated = False
        self._errors_before = set(self._safe_field_errors())

        def _is_save(request) -> bool:
            return request.method != "GET" and bool(self.SAVE_REQUEST_PATTERN.search(request.url))

        def _on_request(request):
            try:
                if _is_save(request):
                    self._save_requests.append(f"{request.method} {request.url}")
            except Exception:  # noqa: BLE001
                pass

        def _on_response(response):
            try:
                if _is_save(response.request):
                    self._save_responses.append(response.status)
            except Exception:  # noqa: BLE001
                pass

        def _on_navigation(frame):
            if frame == self.page.main_frame:
                self._navigated = True

        self._probe_handlers = (_on_request, _on_navigation, _on_response)
        self.page.on("request", _on_request)
        self.page.on("framenavigated", _on_navigation)
        self.page.on("response", _on_response)
        self.page.evaluate(
            f"""() => {{
                window.{self._DOC_MARK} = true;
                window.__qcTbInvalid = []; window.__qcTbInvalidMsg = {{}};
                if (!window.__qcTbHooked) {{
                    window.__qcTbHooked = true;
                    document.addEventListener('invalid', (e) => {{
                        const t = e.target; const k = t.name || t.id || '';
                        window.__qcTbInvalid.push(k); window.__qcTbInvalidMsg[k] = t.validationMessage;
                    }}, true);
                }}
            }}"""
        )

    def _disarm_save_probe(self) -> None:
        on_request, on_navigation, on_response = getattr(self, "_probe_handlers", (None, None, None))
        for event, handler in (("request", on_request), ("framenavigated", on_navigation),
                               ("response", on_response)):
            if handler is not None:
                try:
                    self.page.remove_listener(event, handler)
                except Exception:  # noqa: BLE001
                    pass

    def _document_replaced(self) -> bool:
        try:
            return not self.page.evaluate(f"() => Boolean(window.{self._DOC_MARK})")
        except Exception:  # noqa: BLE001
            return False

    def _safe_field_errors(self) -> list[str]:
        try:
            return self.field_errors()
        except Exception:  # noqa: BLE001
            return []

    def _invalid_fields(self) -> list[str]:
        try:
            return list(self.page.evaluate("() => window.__qcTbInvalid || []"))
        except Exception:  # noqa: BLE001
            return []

    def _native_messages(self) -> dict:
        try:
            return dict(self.page.evaluate("() => window.__qcTbInvalidMsg || {}"))
        except Exception:  # noqa: BLE001
            return {}

    def _refusal_shown(self) -> bool:
        try:
            return (bool(self._invalid_fields()) or bool(self._safe_field_errors())
                    or any(B_MSG_BLOCKED in t or "not saved" in t for t in self.editbar_texts()))
        except Exception:  # noqa: BLE001
            return False

    def _wait_for_save_outcome(self) -> None:
        started = _monotonic()
        state = {"value": ""}
        settled = f"{self.LIST_LOADED}, {self.SAVE_AS_DRAFT_BUTTON}"

        def _outcome() -> bool:
            if self._document_replaced():
                if self.page.locator(settled).count() > 0:
                    state["value"] = "reloaded"
                    return True
                return False
            answered = len(self._save_responses) >= len(self._save_requests)
            accepted = any(code < 400 for code in self._save_responses)
            quiet = answered and not self._navigated and _monotonic() - started >= self.REFUSAL_QUIET_WINDOW_S
            if quiet and not accepted and self._refusal_shown():
                state["value"] = "refused"
                return True
            if quiet and accepted and any(t not in self._errors_before for t in self._safe_field_errors()):
                state["value"] = "refused"
                return True
            return False

        try:
            _wait_until(_outcome, timeout=self.SAVE_OUTCOME_TIMEOUT_S, poll=0.5)
        except _WaitTimeoutError:
            _b_logger.warning("save outcome did not settle; requests=%s responses=%s",
                              self._save_requests, self._save_responses)
        finally:
            self._disarm_save_probe()
        self.last_save_reloaded = state["value"] == "reloaded"
        self.last_save_refused = state["value"] == "refused"
        self.last_save_requests = list(self._save_requests)
        self.last_save_responses = list(self._save_responses)
        self.last_invalid_fields = [] if self.last_save_reloaded else self._invalid_fields()
        self.last_native_messages = {} if self.last_save_reloaded else self._native_messages()

    def save_went_through(self) -> bool:
        return bool(getattr(self, "last_save_reloaded", False))

    def save_was_refused(self) -> bool:
        return bool(getattr(self, "last_save_refused", False))

    def editbar_texts(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.EDITBAR).all_inner_texts() if t.strip()]

    def field_errors(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.FIELD_ERROR).all_inner_texts() if t.strip()]

    def field_error_owners(self) -> list[dict]:
        """[{field, text}] — each inline field error with the field it belongs to
        (the nearest enclosing block's `ObjectField_<key>` name or `qc-ar-<key>` id)."""
        try:
            return self.page.evaluate(
                """(sel) => [...document.querySelectorAll(sel)].filter(e => e.innerText.trim()).map(e => {
                    let c = e.parentElement, owners = [];
                    for (let i = 0; i < 6 && c && !owners.length; i++, c = c.parentElement) {
                        owners = [...c.querySelectorAll('[name^="ObjectField_"]:not([type="hidden"]), [id^="qc-ar-"]')]
                            .map(n => n.name || n.id);
                    }
                    return {field: owners.join(','), text: e.innerText.trim()}; })""",
                self.FIELD_ERROR,
            )
        except Exception:  # noqa: BLE001 — mid-navigation
            return []

    def refusal_evidence(self) -> dict:
        return {
            "invalid_fields": list(getattr(self, "last_invalid_fields", [])),
            "native_messages": dict(getattr(self, "last_native_messages", {})),
            "field_errors": self._safe_field_errors(),
            "field_error_owners": self.field_error_owners(),
            "editbar": self.editbar_texts(),
            "save_requests": list(getattr(self, "last_save_requests", [])),
            "save_responses": list(getattr(self, "last_save_responses", [])),
        }

    def all_messages_text(self) -> str:
        parts = self.editbar_texts() + self._safe_field_errors()
        parts += [m for m in getattr(self, "last_native_messages", {}).values() if m]
        return " | ".join(parts)

    def success_messages(self, expected: str, timeout: float = 15.0) -> list[str]:
        def _done() -> bool:
            return any(expected in t for t in self.editbar_texts())
        try:
            _wait_until(_done, timeout=timeout, poll=0.5)
        except _WaitTimeoutError:
            pass
        return self.editbar_texts()

    # ---- whole-record data ---------------------------------------------------------
    def fill_tender(self, data: dict) -> "TenderFieldsAdminPage":
        """Fills every key `data` carries (None/absent = left untouched, i.e. empty on a new form)."""
        for key in (K_REF, K_TITLE, K_ORG, K_ORG_ADDRESS, K_PREBID_ADDRESS, K_HELP_EMAIL, K_WORK_DESCRIPTION):
            if data.get(key) is not None:
                self.fill_en(key, data[key])
        for key in (K_TITLE, K_ORG, K_ORG_ADDRESS, K_PREBID_ADDRESS, K_WORK_DESCRIPTION):
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, data[f"{key}_ar"])
        for key in (K_OVERVIEW, K_FEE_PAYABLE, K_EMD_PAYABLE):
            if data.get(key):
                self.fill_rich(key, data[key])
        for key in (K_TENDER_FEE, K_EMD_AMOUNT):
            if data.get(key) is not None:
                self.fill_number_key(key, data[key])
        for key in (K_OPENING, K_CLOSING, K_PUBLICATION, K_PREBID_DATE):
            if data.get(key):
                self.set_date(key, data[key])
        for key in K_PICKLISTS:
            if data.get(key):
                self.pick(key, data[key])
        for key in (K_TENDER_DOCUMENT, K_BOQ):
            if data.get(key):
                self.upload(key, data[key], data.get(f"{key}_stem"))
                data[f"{key}_uploaded_as"] = self.last_uploaded_name
        if data.get("active_status") is not None:
            self.set_active_status(bool(data["active_status"]))
        return self

    @staticmethod
    def default_tender_data(reference: str, title: str, pdf_path: str, **overrides) -> dict:
        data = {
            K_REF: reference,
            K_TITLE: title,
            f"{K_TITLE}_ar": f"{title} مناقصة تجريبية",
            K_ORG: "QCTEST Organization",
            f"{K_ORG}_ar": "منظمة تجريبية",
            K_OPENING: "01/11/2026",
            K_CLOSING: "30/11/2026",
            K_PUBLICATION: "05/10/2026",
            K_PREBID_DATE: "10/11/2026",
            K_OVERVIEW: "QCTEST disposable automated-test tender overview.",
            K_WORK_DESCRIPTION: "QCTEST disposable work description.",
            f"{K_WORK_DESCRIPTION}_ar": "وصف عمل تجريبي.",
            K_ORG_ADDRESS: "QCTEST Address, Doha",
            f"{K_ORG_ADDRESS}_ar": "عنوان تجريبي، الدوحة",
            K_TENDER_FEE: "500",
            K_FEE_PAYABLE: "QCTEST fee account",
            K_EMD_AMOUNT: "1000",
            K_EMD_PAYABLE: "QCTEST EMD account",
            K_PREBID_ADDRESS: "QCTEST Meeting Room",
            f"{K_PREBID_ADDRESS}_ar": "قاعة اجتماعات تجريبية",
            K_HELP_EMAIL: "qctest@example.com",
            "tenderCategory": "Services",
            "tenderType": "Open Tender",
            "tenderClassification": "Lump-sum",
            "productCategory": "Consultancy Services",
            "tenderLocation": "Qatar",
            "tenderFeeExemptionAllowed": "No",
            "paymentMode": "Online",
            "generalTechnicalEvaluationAllowed": "Yes",
            "itemWiseTechnicalEvaluationAllowed": "No",
            "pageStatus": "Published",
            K_TENDER_DOCUMENT: pdf_path,
            K_BOQ: pdf_path,
            "active_status": True,
        }
        data.update(overrides)
        return data


from core.web.base_page import BasePage as _BasePageB  # noqa: E402


class TenderPublicViewB(_BasePageB):
    """Read-only public listing/detail reads for the field cases (Agent B).
    Always driven from a fresh LOGGED-OUT context. Live 2026-10-05: the listing
    (`/web/qatar-chamber/tenders`) renders 6 cards + "Load more"; each
    `a.qc-tenders-card` links to `tender-details?tender=<entry code>`; the
    detail page renders `.qc-tnd-file` rows (Tender document / BOQ) with a
    Download link."""

    LISTING_PATH = "/web/qatar-chamber/tenders"
    CARD = "a.qc-tenders-card"
    CARD_TITLE = ".qc-tenders-card-title"
    LOAD_MORE = "button.qc-tenders-more"
    DETAIL_TITLE = "h1.qc-tnd-title"
    FILE_ROW = ".qc-tnd-file"

    def open_listing_all(self, locale: str = "en") -> "TenderPublicViewB":
        from config.settings import web_url  # noqa: PLC0415
        self.open(web_url(self.LISTING_PATH, locale=locale))
        try:
            self.page.locator(self.CARD).first.wait_for(timeout=60000)
        except Exception:  # noqa: BLE001 — an empty grid is reported by the caller
            return self
        cards, button = self.page.locator(self.CARD), self.page.locator(self.LOAD_MORE)
        for _ in range(30):
            if button.count() == 0 or not button.first.is_visible():
                break
            before = cards.count()
            button.first.click()
            try:
                _wait_until(lambda: cards.count() > before, timeout=10.0, poll=0.25)
            except _WaitTimeoutError:
                break
        return self

    def cards(self) -> list[dict]:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('a.qc-tenders-card')].map(a => {
                const q = s => { const n = a.querySelector(s); return n ? n.innerText.trim() : ''; };
                const dates = {};
                a.querySelectorAll('.qc-tenders-date').forEach(d => {
                    const l = d.querySelector('.qc-tenders-date-label'), v = d.querySelector('.qc-tenders-date-value');
                    if (l && v) dates[l.innerText.trim()] = v.innerText.trim(); });
                return {href: a.getAttribute('href') || '', title: q('.qc-tenders-card-title'),
                        ref: q('.qc-tenders-ref'), org: q('.qc-tenders-org'), badge: q('.qc-tenders-badge'),
                        dates: dates};
            })"""
        )

    def card_index_by_href_code(self, code: str) -> int:
        for i, card in enumerate(self.cards()):
            if card["href"].endswith(f"tender={code}"):
                return i
        return -1

    def open_detail(self, code: str, locale: str = "en") -> "TenderPublicViewB":
        from config.settings import web_url  # noqa: PLC0415
        self.open(web_url(f"/web/qatar-chamber/tender-details?tender={code}", locale=locale))
        self.page.locator(self.DETAIL_TITLE).wait_for(timeout=60000)
        return self

    def detail_text(self) -> str:
        """Whole page text (the Opening date / deadline sidebar sits outside <main>)."""
        return self.page.locator("body").inner_text()

    def detail_header(self) -> dict:
        return self.page.evaluate(
            """() => { const q = s => { const n = document.querySelector(s); return n ? n.innerText.trim() : ''; };
                return {title: q('h1.qc-tnd-title'), org: q('p.qc-tnd-org'), ref: q('.qc-tnd-ref-value'),
                        published: q('.qc-tnd-ref-pub'), deadline: q('strong.qc-tnd-dl-date')}; }"""
        )

    def file_rows(self) -> list[dict]:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('.qc-tnd-file')].map(f => {
                const links = [...f.querySelectorAll('a')];
                return {text: f.innerText.replace(/\\s+/g, ' ').trim(),
                        hrefs: links.map(a => a.href)}; })"""
        )

    def url_status(self, url: str) -> dict:
        """Anonymous GET through this logged-out context -> {status, size, is_pdf, content_type}."""
        response = self.page.request.get(url, max_redirects=5, timeout=60000)
        try:
            body = response.body()
        except Exception:  # noqa: BLE001
            body = b""
        return {"url": url, "status": response.status, "content_type": response.headers.get("content-type", ""),
                "size": len(body), "is_pdf": body[:5] == b"%PDF-"}

    def overflow_report(self, selectors: list[str]) -> list[dict]:
        """Per element of `selectors`: text cut-off / overflow signals
        (scrollWidth > clientWidth with hidden overflow, ellipsis, element wider
        than the viewport, horizontal page scroll)."""
        return self.page.evaluate(
            """(sels) => {
                const out = []; const vw = document.documentElement.clientWidth;
                for (const s of sels) document.querySelectorAll(s).forEach(el => {
                    const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
                    out.push({sel: s, text: el.innerText.slice(0, 80),
                              clipped: (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)
                                       && (cs.overflow.includes('hidden') || cs.textOverflow === 'ellipsis'
                                           || cs.webkitLineClamp !== 'none'),
                              ellipsis: cs.textOverflow === 'ellipsis', line_clamp: cs.webkitLineClamp,
                              beyond_viewport: r.right > vw + 1 || r.left < -1,
                              width: Math.round(r.width), vw: vw}); });
                out.push({sel: 'document', page_hscroll: document.documentElement.scrollWidth > vw + 1,
                          scrollWidth: document.documentElement.scrollWidth, vw: vw});
                return out; }""",
            selectors,
        )


# --- workflow (Agent A) ---
# =============================================================================
# Workflow / publish / persistence helpers for PBI 130952's Control_Panel
# workflow cases (146108, 146133-146136, 146283, 146293) —
# cms/tests/tenders/test_tenders_workflow_control_panel.py.
#
# Builds on the field / save-probe / guarded-delete helpers of
# TenderFieldsAdminPage above (nothing there is overridden in place) and adds:
# the QCTEST-130952-A- namespace, Editor + Author sessions, id-scoped row
# workflow actions (`data-qc-oel-<action>`), the in-table History trail, the
# row Preview, the Arabic rich-text editors and a full read-back of the form.
#
# LIVE 2026-10-05 (/en/ manage-tender, read-only probes):
#   - Editor (156488) form ends "Save as Draft" / "Publish" ("As an Editor,
#     what you publish here goes live straight away."); Author (156492) form
#     ends "Save as Draft" / "Submit for Review" ("Entries here are reviewed
#     before they go live.").
#   - Editor rows on a Published tender: Edit / Preview / Unpublish / History /
#     Delete. Author rows on tenders it does not own: View / Preview / History
#     (no Edit, no Delete).
#   - "Status" (`ObjectField_pageStatus`) is a plain picklist — Submitted /
#     Approved / Rejected / Published / Closed — independent of the editorial
#     workflow badge (the real QC-TENDER-130952-15-SUBMITTED row is workflow
#     PUBLISHED with Status = Submitted and is NOT on the public listing).
#   - The public listing shows a tender only when its workflow is PUBLISHED,
#     Active Status is ticked, Status = Published and its Closing Date is not
#     past (observed on the 15 real rows; 2 expired + the Submitted one hidden).
#   - Rich-text editors: EN `div.cke[class*="-ObjectField_<key>"] iframe`,
#     AR `#cke_qc-ar-<key> iframe` (both title="editor").
#   - History expands inside the table (`td.qc-oel__history`), not a modal.
#
# DELETE SAFETY: `delete_own_entry()` accepts only a TenderEntryA whose title
# AND reference start with QCTEST-130952-A-, adopted from this test's own
# capture, then runs the single guarded delete above (exact ref + title re-read
# by code, captured id, fully expanded list, exactly one delete link, confirm()
# must name the title). No positional, looping or substring delete exists here.
# =============================================================================
from cms.pages.components.object_authoring_page import normalize_status as _a_normalize_status  # noqa: E402

_a_logger = _get_logger("tender_workflow_admin_page")

A_QCTEST_PREFIX = "QCTEST-130952-A-"
A_ROLE_EDITOR = "Site Content Editor"
A_ROLE_AUTHOR = "Site Content Author"
A_ROLE_USER_IDS = {A_ROLE_EDITOR: "156488", A_ROLE_AUTHOR: "156492"}
A_MSG_DRAFT_SAVED = "Draft saved."
A_MSG_SAVED_AND_PUBLISHED = "Saved and published."
A_MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
A_MSG_ARABIC_SAVED = "Arabic content saved for this record."
A_STATUS_INACTIVE = "Inactive"
A_VALID_PDF = _os.path.join(str(_PROJECT_ROOT), "cms", "tests", "tenders", "fixtures", "qctest_valid_document.pdf")

A_TEXT_KEYS = (K_REF, K_TITLE, K_ORG, K_ORG_ADDRESS, K_PREBID_ADDRESS, K_HELP_EMAIL, K_WORK_DESCRIPTION)
A_AR_TEXT_KEYS = (K_TITLE, K_ORG, K_ORG_ADDRESS, K_PREBID_ADDRESS, K_WORK_DESCRIPTION)
A_RICH_KEYS = (K_OVERVIEW, K_FEE_PAYABLE, K_EMD_PAYABLE)
A_NUMBER_KEYS = (K_TENDER_FEE, K_EMD_AMOUNT)
A_DATE_KEYS = (K_OPENING, K_CLOSING, K_PUBLICATION, K_PREBID_DATE)
A_FILE_KEYS = (K_TENDER_DOCUMENT, K_BOQ)


@_dataclass(frozen=True)
class TenderEntryA(TenderCreatedEntry):
    """Identity of a tender an Agent-A test created (title AND ref in the A namespace)."""

    def in_namespace(self) -> bool:
        return self.title.startswith(A_QCTEST_PREFIX) and self.reference.startswith(A_QCTEST_PREFIX)


class TenderWorkflowAdminPage(TenderFieldsAdminPage):
    """manage-tender editorial-workflow helpers (Agent A). See the section notes above."""

    EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "evidence", "tenders_130952_a")
    ROW_ACTION_NAMES = ("view", "approve", "reject", "resubmit", "publish", "unpublish", "archive",
                        "restore", "return", "schedule", "history", "delete")
    DESTRUCTIVE_ROW_ACTIONS = frozenset({"delete", "trash", "untrash"})
    HISTORY_CELL = "td.qc-oel__history"
    HISTORY_ACTION = ".qc-oel__history-action"

    # ---- namespace / identity ---------------------------------------------------
    @staticmethod
    def a_name(tc_id: str, stamp: str, suffix: str = "") -> str:
        return f"{A_QCTEST_PREFIX}{tc_id}-{stamp}" + (f" {suffix}" if suffix else "")

    def identify_created_a(self, reference: str, title: str, ids_before: set[str]) -> TenderEntryA | None:
        """The ONE new row (id not in `ids_before`, not a real tender code) whose
        Entry cell reads `title` and whose own form reads exactly `reference` +
        `title`. None for zero or several matches. Read-only."""
        if not (reference.startswith(A_QCTEST_PREFIX) and title.startswith(A_QCTEST_PREFIX)):
            raise ValueError(f"{reference!r} / {title!r} are not both in the {A_QCTEST_PREFIX} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].startswith(B_REAL_ENTRY_CODE_PREFIX) and r["title"].strip() == title]
        matches = []
        for row in fresh:
            for attempt in (1, 2):  # one retry: a slow editEntry load must not orphan our record
                try:
                    self.open_entry_en(row["code"])
                    if self.text_value(K_REF) == reference and self.text_value(K_TITLE) == title:
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — an unreadable row is not ours
                    _a_logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            _a_logger.warning("identify_created_a(%r): %s matches among new rows %s", reference, len(matches), fresh)
            return None
        entry = TenderEntryA(title=title, reference=reference, entry_id=matches[0]["entry_id"],
                             code=matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def adopt_a(self, entry: TenderEntryA) -> TenderEntryA:
        if (not isinstance(entry, TenderEntryA) or not entry.in_namespace() or not entry.entry_id
                or not entry.code or entry.code.startswith(B_REAL_ENTRY_CODE_PREFIX)):
            raise ValueError(f"refusing to adopt {entry}: not a captured {A_QCTEST_PREFIX} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def delete_own_entry(self, entry: TenderEntryA) -> bool:
        """Deletes exactly this test's captured record through the guarded
        single-record delete, or refuses (False, never raises)."""
        if not isinstance(entry, TenderEntryA) or not entry.in_namespace():
            _a_logger.error("DELETE REFUSED: %r is not a captured %s record", entry, A_QCTEST_PREFIX)
            return False
        if entry.entry_id not in self.owned_entry_ids:
            _a_logger.error("DELETE REFUSED: id of %r was not adopted from this test's capture", entry)
            return False
        return self.delete_disposable_entry(entry)

    def a_leftovers(self) -> list[dict]:
        """Read-only: rows whose title is in the QCTEST-130952-A- namespace."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].startswith(A_QCTEST_PREFIX)]

    # ---- rows ---------------------------------------------------------------------
    def _row_a(self, entry: TenderEntryA):
        return self.page.locator(", ".join(
            f'{self.ENTRIES_TABLE_ROW}:has([data-qc-oel-{a}="{entry.entry_id}"])' for a in self.ID_ATTRS))

    def row_status_a(self, entry: TenderEntryA) -> str:
        """Normalized workflow badge of the captured row ("" when the row is gone)."""
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        if len(rows) != 1:
            return ""
        raw = " ".join(rows[0]["status"].split())
        if raw.casefold() == A_STATUS_INACTIVE.casefold():
            return A_STATUS_INACTIVE
        return _a_normalize_status(raw)

    def row_status_raw(self, entry: TenderEntryA) -> str:
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return rows[0]["status"] if len(rows) == 1 else ""

    def row_actions(self, entry: TenderEntryA) -> list[str]:
        """`data-qc-oel-<action>` controls the captured row offers to this session."""
        row = self._row_a(entry).first
        return [n for n in self.ROW_ACTION_NAMES if row.locator(f"[data-qc-oel-{n}]").count() > 0]

    def row_link_labels(self, entry: TenderEntryA) -> list[str]:
        return [t.strip() for t in self._row_a(entry).first.locator("td").last.locator("a, button")
                .all_inner_texts() if t.strip()]

    def row_has_edit_link(self, entry: TenderEntryA) -> bool:
        return self._row_a(entry).first.locator('a[href*="editEntry="]').count() > 0

    def row_preview_href(self, entry: TenderEntryA) -> str:
        from config.settings import control_panel_url  # noqa: PLC0415
        link = self._row_a(entry).first.get_by_role("link", name="Preview")
        href = link.first.get_attribute("href") if link.count() else ""
        return (href if href.startswith("http") else control_panel_url(href)) if href else ""

    def run_row_action(self, entry: TenderEntryA, action: str, comment: str = "") -> list[str]:
        """Clicks ONE id-scoped workflow action on a record this test captured,
        accepting every native confirm()/prompt() it raises (prompts get
        `comment`); returns the dialog messages. Destructive actions refused."""
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(f"run_row_action refuses {action!r}; use delete_own_entry()")
        if action != "history":
            if not isinstance(entry, TenderEntryA) or not entry.in_namespace():
                raise ValueError(f"run_row_action refuses {entry}: not a {A_QCTEST_PREFIX} record")
            if entry.entry_id not in self.owned_entry_ids:
                raise ValueError(f"run_row_action refuses {entry}: id not captured at creation by this test")
            rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
            if len(rows) != 1 or rows[0]["title"].strip() != entry.title:
                raise ValueError(f"run_row_action refuses {entry}: the row now reads {rows}")
        control = self._row_a(entry).first.locator(f"[data-qc-oel-{action}]")
        if control.count() == 0:
            raise AssertionError(f"row {entry.title!r} offers no {action!r} action; offered {self.row_actions(entry)}")
        messages: list[str] = []

        def _accept(dialog):
            messages.append(f"{dialog.type}: {dialog.message}")
            try:
                if dialog.type == "prompt":
                    dialog.accept(comment)
                else:
                    dialog.accept()
            except Exception:  # noqa: BLE001 — already handled
                pass

        self.page.on("dialog", _accept)
        try:
            control.first.click(force=True)
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        self.last_row_action_dialogs = messages
        return messages

    def history(self, entry: TenderEntryA) -> list[dict]:
        """Expands the captured row's History (inside the table) ->
        [{action, who, when, comment, text}] in the order rendered."""
        self.open_list_all()
        self._row_a(entry).first.locator("[data-qc-oel-history]").first.click(force=True)
        cell = self._row_a(entry).first.locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        try:
            _wait_until(lambda: cell.count() == 1 and "Loading" not in cell.inner_text(), timeout=20.0, poll=0.5)
        except _WaitTimeoutError:
            return []
        items = cell.locator("li")
        trail = []
        for i in range(items.count()):
            item = items.nth(i)

            def _part(sel: str, node=item) -> str:
                found = node.locator(sel)
                return found.first.inner_text().strip() if found.count() else ""

            trail.append({"action": _part(self.HISTORY_ACTION), "who": _part(self.HISTORY_WHO),
                          "when": _part(self.HISTORY_WHEN), "comment": _part(self.HISTORY_COMMENT),
                          "text": " ".join(item.inner_text().split())})
        return [h for h in trail if h["action"] or h["who"]]

    def history_cell_text(self, entry: TenderEntryA) -> str:
        """Raw text of the expanded History cell (call after history())."""
        cell = self._row_a(entry).first.locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        return " ".join(cell.inner_text().split()) if cell.count() else ""

    def wait_status(self, entry: TenderEntryA, expected: tuple, timeout: float = 120.0) -> str:
        seen = {"status": ""}

        def _reached() -> bool:
            self.open_list_all()
            seen["status"] = self.row_status_a(entry)
            return seen["status"] in expected

        try:
            _wait_until(_reached, timeout=timeout, poll=3.0)
        except _WaitTimeoutError:
            pass
        return seen["status"]

    # ---- form ---------------------------------------------------------------------
    def submit_button_label(self) -> str:
        button = self.page.get_by_role("button", name=self.SUBMIT_NAME)
        return button.first.inner_text().strip() if button.count() else ""

    def form_buttons(self) -> list[str]:
        """Visible, enabled button labels of the authoring form."""
        names = []
        for button in self._form().locator("button").all():
            try:
                if button.is_visible() and button.is_enabled():
                    label = button.inner_text().strip()
                    if label:
                        names.append(label)
            except Exception:  # noqa: BLE001 — detached node is not an action
                continue
        return names

    def editing_bar_text(self) -> str:
        for text in self.editbar_texts():
            if text.startswith("Editing"):
                return text
        return ""

    def _rich_ar_iframe(self, key: str) -> str:
        return f'[id="cke_qc-ar-{key}"] iframe[title="editor"]'

    def fill_rich_ar(self, key: str, text: str) -> "TenderWorkflowAdminPage":
        self.fill_iframe_editor(self._rich_ar_iframe(key), text)
        return self

    def rich_text(self, key: str) -> str:
        return self.iframe_editor_text(self._rich_iframe(key)).strip()

    def rich_text_ar(self, key: str) -> str:
        return self.iframe_editor_text(self._rich_ar_iframe(key)).strip()

    def fill_tender_a(self, data: dict) -> "TenderWorkflowAdminPage":
        """Agent B's fill_tender() plus the Arabic rich-text editors (`<key>_ar`)."""
        self.fill_tender(data)
        for key in A_RICH_KEYS:
            if data.get(f"{key}_ar"):
                self.fill_rich_ar(key, data[f"{key}_ar"])
        return self

    def wait_for_rich_text_loaded(self, timeout: float = 20.0) -> None:
        """A reopened record fills its CKEditor bodies after the form renders."""
        try:
            _wait_until(lambda: self.rich_text(K_OVERVIEW) != "", timeout=timeout, poll=0.5)
        except Exception:  # noqa: BLE001 — the caller compares whatever loaded
            pass

    def read_tender(self) -> dict:
        """Every stored value of the open record, keyed like the fill data."""
        self.wait_for_rich_text_loaded()
        values: dict = {}
        for key in A_TEXT_KEYS + A_NUMBER_KEYS:
            values[key] = self.text_value(key)
        for key in A_AR_TEXT_KEYS:
            values[f"{key}_ar"] = self.ar_value(key)
        for key in A_RICH_KEYS:
            values[key] = self.rich_text(key)
            values[f"{key}_ar"] = self.rich_text_ar(key)
        for key in A_DATE_KEYS:
            values[key] = self.date_text(key)
        for key in K_PICKLISTS:
            values[key] = self.picklist_value(key)
        for key in A_FILE_KEYS:
            values[f"{key}_uploaded_as"] = self.stored_file_name(key)
        values["active_status"] = self.active_status_stored()
        return values

    # ---- preview --------------------------------------------------------------------
    def open_preview(self, preview_url: str, expected: list[str], timeout: float = 45.0) -> str:
        """Opens a row's Preview (public page with `qcPreview=`) in THIS signed-in
        context and waits until every `expected` text is shown; returns the body text."""
        self.open(preview_url)
        state = {"text": ""}

        def _shown() -> bool:
            try:
                state["text"] = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001 — mid-render
                return False
            return all(e in state["text"] for e in expected)

        try:
            _wait_until(_shown, timeout=timeout, poll=1.0)
        except _WaitTimeoutError:
            pass
        return state["text"]

    # ---- data -------------------------------------------------------------------------
    @staticmethod
    def a_tender_data(reference: str, title: str, **overrides) -> dict:
        """A complete, valid Agent-A tender (EN + AR incl. rich text, both files,
        Active Status ticked, Status = Published, Closing Date in the future)."""
        if not (reference.startswith(A_QCTEST_PREFIX) and title.startswith(A_QCTEST_PREFIX)):
            raise ValueError(f"disposable tenders must use the {A_QCTEST_PREFIX} namespace")
        data = TenderFieldsAdminPage.default_tender_data(reference, title, A_VALID_PDF)
        data.update({
            K_OPENING: "01/10/2026",
            K_CLOSING: "31/12/2026",
            K_PUBLICATION: "05/10/2026",
            K_PREBID_DATE: "15/10/2026",
            K_ORG: "QCTEST Agent A Organization",
            f"{K_ORG}_ar": "منظمة اختبار آلي",
            K_OVERVIEW: f"{title} overview: disposable automated-test tender.",
            f"{K_OVERVIEW}_ar": "نظرة عامة على مناقصة اختبار آلي.",
            K_FEE_PAYABLE: "QCTEST fee account, Doha",
            f"{K_FEE_PAYABLE}_ar": "حساب رسوم تجريبي، الدوحة",
            K_EMD_PAYABLE: "QCTEST EMD account, Doha",
            f"{K_EMD_PAYABLE}_ar": "حساب تأمين تجريبي، الدوحة",
            "tenderCategory": "Services",
            f"{K_TENDER_DOCUMENT}_stem": "qctest-130952-a-tender-doc",
            f"{K_BOQ}_stem": "qctest-130952-a-boq",
        })
        data.update(overrides)
        return data


class TenderPublicViewA(TenderPublicViewB):
    """Logged-out listing/detail reads for the workflow cases (Agent A)."""

    def card_for(self, code: str) -> dict:
        for card in self.cards():
            if card["href"].endswith(f"tender={code}"):
                return card
        return {}


# --- files (Agent D) ---
# =============================================================================
# Tender Document / BOQ upload helpers for PBI 130952's Control_Panel file
# cases (146160-146167) — cms/tests/tenders/test_tenders_files_control_panel.py.
#
# Reuses Agent B's upload / save-probe / guarded-delete helpers of
# TenderFieldsAdminPage unchanged (nothing is overridden in place) and only adds
# the QCTEST-130952-D- namespace, its own capture-by-diff and its own evidence
# folder. Upload fields (live 2026-10-05, Editor 156488): tenderDocument /
# billOfQuantities, both required, help line "Upload a .pdf no larger than 5 MB.",
# picked through the Documents & Media `selectFileEntry` iframe.
#
# DELETE SAFETY: `delete_own_entry_d()` accepts only a TenderEntryD whose title
# AND reference start with QCTEST-130952-D-, adopted from this test's own capture,
# then runs the single guarded delete above (exact ref + title re-read by code,
# captured id, fully expanded list, exactly one delete link, confirm() must name
# the title). No positional, looping or substring delete exists here.
# =============================================================================
_d_logger = _get_logger("tender_files_admin_page")

D_QCTEST_PREFIX = "QCTEST-130952-D-"


@_dataclass(frozen=True)
class TenderEntryD(TenderCreatedEntry):
    """Identity of a tender an Agent-D test created (title AND ref in the D namespace)."""

    def in_namespace(self) -> bool:
        return self.title.startswith(D_QCTEST_PREFIX) and self.reference.startswith(D_QCTEST_PREFIX)


class TenderFilesAdminPage(TenderFieldsAdminPage):
    """manage-tender Tender Document / BOQ helpers (Agent D). See the section notes above."""

    EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "evidence", "tenders_130952_d")

    def identify_created_d(self, reference: str, title: str, ids_before: set[str]) -> TenderEntryD | None:
        """The ONE new row (id not in `ids_before`, not a real tender code) whose
        Entry cell reads `title` and whose own form reads exactly `reference` +
        `title`. None for zero or several matches. Read-only."""
        if not (reference.startswith(D_QCTEST_PREFIX) and title.startswith(D_QCTEST_PREFIX)):
            raise ValueError(f"{reference!r} / {title!r} are not both in the {D_QCTEST_PREFIX} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].startswith(B_REAL_ENTRY_CODE_PREFIX) and r["title"].strip() == title]
        matches = []
        for row in fresh:
            for attempt in (1, 2):  # one retry: a slow editEntry load must not orphan our record
                try:
                    self.open_entry_en(row["code"])
                    if self.text_value(K_REF) == reference and self.text_value(K_TITLE) == title:
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — an unreadable row is not ours
                    _d_logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            _d_logger.warning("identify_created_d(%r): %s matches among new rows %s", reference, len(matches), fresh)
            return None
        entry = TenderEntryD(title=title, reference=reference, entry_id=matches[0]["entry_id"],
                             code=matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def adopt_d(self, entry: TenderEntryD) -> TenderEntryD:
        if (not isinstance(entry, TenderEntryD) or not entry.in_namespace() or not entry.entry_id
                or not entry.code or entry.code.startswith(B_REAL_ENTRY_CODE_PREFIX)):
            raise ValueError(f"refusing to adopt {entry}: not a captured {D_QCTEST_PREFIX} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def delete_own_entry_d(self, entry: TenderEntryD) -> bool:
        """Deletes exactly this test's captured record through the guarded
        single-record delete, or refuses (False, never raises)."""
        if not isinstance(entry, TenderEntryD) or not entry.in_namespace():
            _d_logger.error("DELETE REFUSED: %r is not a captured %s record", entry, D_QCTEST_PREFIX)
            return False
        if entry.entry_id not in self.owned_entry_ids:
            _d_logger.error("DELETE REFUSED: id of %r was not adopted from this test's capture", entry)
            return False
        return self.delete_disposable_entry(entry)

    def d_leftovers(self) -> list[dict]:
        """Read-only: rows whose title is in the QCTEST-130952-D- namespace."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].startswith(D_QCTEST_PREFIX)]

    # ---- upload outcome -----------------------------------------------------------
    def file_field_value(self, key: str) -> str:
        """The value the form would submit for an upload field (the picked
        fileEntryId; "" when nothing is attached)."""
        return self._form().locator(f'input[name="ObjectField_{key}"]').first.input_value()

    def file_field_invalid(self, key: str) -> bool:
        """True when the form flags the upload field invalid (live 2026-10-05: an
        oversized pick sets `aria-invalid="true"` + `data-qc-oel-invalid`)."""
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return node.get_attribute("aria-invalid") == "true" or node.get_attribute("data-qc-oel-invalid") is not None

    def upload_outcome(self, key: str, settle_s: float = 5.0) -> dict:
        """For a pick that should be REJECTED: after attempt_upload(), waits up to
        `settle_s` for the form to clear the field (live: an oversized pick is
        briefly set, then cleared) and reports
        {value, invalid, field_errors, editbar}. A rejected upload leaves value ""."""
        try:
            _wait_until(lambda: self.file_field_value(key) == "", timeout=settle_s, poll=0.5)
        except _WaitTimeoutError:
            pass
        return {"value": self.file_field_value(key), "invalid": self.file_field_invalid(key),
                "field_errors": self.field_errors(), "editbar": self.editbar_texts()}


# --- publish (Agent C) ---
# =============================================================================
# Manual create / publish / unpublish / Active Status / audit / persistence /
# Reference-Number collision helpers for PBI 130952 cases 146133-146136,
# 146283, 146293 — cms/tests/tenders/test_tenders_publish_control_panel.py.
#
# Thin namespace layer over Agent A's TenderWorkflowAdminPage (nothing above is
# overridden in place): records are `QCTEST-130952-C-<tc>-<stamp>` (title AND
# reference). TenderEntryC subclasses TenderEntryA so Agent A's id-scoped
# run_row_action() / history() / adopt_a() / delete_own_entry() guards apply
# unchanged, but `in_namespace()` accepts ONLY the C prefix.
#
# DELETE SAFETY: identical to Agent A's — only a TenderEntryC captured by this
# test (list-id diff + exact ref/title read back by code), re-read right
# before the click, through the single guarded delete. No positional, looping
# or substring delete exists here.
# =============================================================================
_c_logger = _get_logger("tender_publish_admin_page")

C_QCTEST_PREFIX = "QCTEST-130952-C-"


@_dataclass(frozen=True)
class TenderEntryC(TenderEntryA):
    """Identity of a tender an Agent-C test created (title AND ref in the C namespace)."""

    def in_namespace(self) -> bool:
        return self.title.startswith(C_QCTEST_PREFIX) and self.reference.startswith(C_QCTEST_PREFIX)


class TenderPublishAdminPage(TenderWorkflowAdminPage):
    """manage-tender publish-lifecycle helpers (Agent C). See the section notes above."""

    EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "evidence", "tenders_130952_c")

    @staticmethod
    def c_name(tc_id: str, stamp: str, suffix: str = "") -> str:
        return f"{C_QCTEST_PREFIX}{tc_id}-{stamp}" + (f" {suffix}" if suffix else "")

    def identify_created_c(self, reference: str, title: str, ids_before: set[str]) -> TenderEntryC | None:
        """The ONE new row (id not in `ids_before`, not a real tender code) whose
        Entry cell reads `title` and whose own form reads exactly `reference` +
        `title`. None for zero or several matches. Read-only."""
        if not (reference.startswith(C_QCTEST_PREFIX) and title.startswith(C_QCTEST_PREFIX)):
            raise ValueError(f"{reference!r} / {title!r} are not both in the {C_QCTEST_PREFIX} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].startswith(B_REAL_ENTRY_CODE_PREFIX) and r["title"].strip() == title]
        matches = []
        for row in fresh:
            for attempt in (1, 2):
                try:
                    self.open_entry_en(row["code"])
                    if self.text_value(K_REF) == reference and self.text_value(K_TITLE) == title:
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — an unreadable row is not ours
                    _c_logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            _c_logger.warning("identify_created_c(%r): %s matches among new rows %s", reference, len(matches), fresh)
            return None
        entry = TenderEntryC(title=title, reference=reference, entry_id=matches[0]["entry_id"],
                             code=matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def c_leftovers(self) -> list[dict]:
        """Read-only: rows whose title is in the QCTEST-130952-C- namespace."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].startswith(C_QCTEST_PREFIX)]

    @staticmethod
    def c_tender_data(reference: str, title: str, **overrides) -> dict:
        """A complete, valid Agent-C tender (EN + AR incl. rich text, both files,
        Active Status ticked, Status = Published, Closing Date in the future)."""
        if not (reference.startswith(C_QCTEST_PREFIX) and title.startswith(C_QCTEST_PREFIX)):
            raise ValueError(f"disposable tenders must use the {C_QCTEST_PREFIX} namespace")
        data = TenderFieldsAdminPage.default_tender_data(reference, title, A_VALID_PDF)
        data.update({
            K_OPENING: "01/10/2026",
            K_CLOSING: "31/12/2026",
            K_PUBLICATION: "05/10/2026",
            K_PREBID_DATE: "15/10/2026",
            K_ORG: "QCTEST Agent C Organization",
            f"{K_ORG}_ar": "منظمة اختبار النشر",
            K_OVERVIEW: f"{title} overview: disposable automated-test tender.",
            f"{K_OVERVIEW}_ar": "نظرة عامة على مناقصة اختبار النشر.",
            K_FEE_PAYABLE: "QCTEST C fee account, Doha",
            f"{K_FEE_PAYABLE}_ar": "حساب رسوم تجريبي، الدوحة",
            K_EMD_PAYABLE: "QCTEST C EMD account, Doha",
            f"{K_EMD_PAYABLE}_ar": "حساب تأمين تجريبي، الدوحة",
            "tenderCategory": "Services",
            f"{K_TENDER_DOCUMENT}_stem": "qctest-130952-c-tender-doc",
            f"{K_BOQ}_stem": "qctest-130952-c-boq",
        })
        data.update(overrides)
        return data

    # ---- preview (Load More-aware) ------------------------------------------------
    def open_preview_expanded(self, preview_url: str, expected: str, timeout: float = 45.0) -> str:
        """Opens a row's Preview (public listing with `qcPreview=`) in THIS signed-in
        context, expands every "Load more" page and returns the body text once
        `expected` is shown or the grid stops growing (bounded)."""
        self.open(preview_url)
        cards, button = self.page.locator(TenderPublicViewB.CARD), self.page.locator(TenderPublicViewB.LOAD_MORE)
        try:
            cards.first.wait_for(timeout=int(timeout * 1000))
        except Exception:  # noqa: BLE001 — an empty grid is reported by the caller
            return self.page.locator("body").inner_text()
        for _ in range(30):
            if expected in self.page.locator("body").inner_text():
                break
            if button.count() == 0 or not button.first.is_visible():
                break
            before = cards.count()
            button.first.click()
            try:
                _wait_until(lambda: cards.count() > before, timeout=10.0, poll=0.25)
            except _WaitTimeoutError:
                break
        return self.page.locator("body").inner_text()

    @staticmethod
    def detail_preview_url(entry: TenderEntryC) -> str:
        from config.settings import web_url  # noqa: PLC0415
        return web_url(f"/web/qatar-chamber/tender-details?tender={entry.code}&qcPreview=tenders%3A{entry.entry_id}")

    def open_detail_preview(self, entry: TenderEntryC, expected: str, timeout: float = 45.0) -> str:
        """The detail page in preview mode for the captured record; waits for
        `expected` or the "Tender not found" state, returns the body text."""
        self.open(self.detail_preview_url(entry))
        state = {"text": ""}

        def _settled() -> bool:
            state["text"] = self.page.locator("body").inner_text()
            return expected in state["text"] or "Tender not found" in state["text"]

        try:
            _wait_until(_settled, timeout=timeout, poll=1.0)
        except _WaitTimeoutError:
            pass
        return state["text"]


class TenderPublicViewC(TenderPublicViewA):
    """Logged-out listing/detail reads for the publish cases (Agent C), with
    file-based evidence under reports/evidence/tenders_130952_c/."""

    EVIDENCE_DIR = TenderPublishAdminPage.EVIDENCE_DIR

    def evidence(self, name: str, full_page: bool = True) -> str:
        _os.makedirs(self.EVIDENCE_DIR, exist_ok=True)
        path = _os.path.join(self.EVIDENCE_DIR, _re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "tenders")
        except Exception as exc:  # noqa: BLE001 — evidence only
            _c_logger.warning("evidence %s failed: %r", name, exc)
        return path

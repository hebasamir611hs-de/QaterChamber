"""
cms/pages/laws_regulations/laws_regulations_admin_page.py — LawsRegulationsAdminPage.

PBI 130699 "QC - Business Gateway - 006 - Laws & Regulations", Control_Panel
surface. Composes `ObjectAuthoringPage` (cms/pages/components/
object_authoring_page.py) for the shared editorial state machine; this class
adds the Law Regulation field set, id-scoped (never positional) row handling,
a pinned-account identity guard and a guard-free anonymous probe.

═══════════════════════════════════════════════════════════════════════
THE OBJECT — confirmed live 2026-09-29 (TEST_USER session, qcdev)
  Object Authoring slug `law-regulation`
    -> https://qcdev.ihorizons.com/web/qatar-chamber/manage-law-regulation
  Listed on /object-authoring as "Law Regulation". It is NOT `LawEntry`
  (`manage-law-entry`), which backs the About-us Chamber's Law page.
  Not documented in cms/Content-Admin-Guide.docx.
  REST collection the public page reads: /o/c/lawregulations/scopes/37246
  Public page: /web/qatar-chamber/laws-regulations  (AR: /ar/web/...)
  Real records carry entry codes `QCDEMO-130699-LAWREG-<n>` (e.g.
  `QCDEMO-130699-LAWREG-200` = "Commercial Companies Law", Law Number
  "Law No. 11", Year 2015, Display Order 200, Open Behavior New Tab,
  Active). 24 real published records at probe time. NEVER touch them.
═══════════════════════════════════════════════════════════════════════

REAL FIELD SET — accessible names exactly as rendered on the `/en/` form
(read off the live form's ARIA snapshot; each resolves to exactly one
control):

    'Law Number'              textbox   (ObjectField_lawNumber, required)
    'Law Number — العربية *'  textbox   (#qc-ar-lawNumber, rtl, required)
    'Year'                    spinbutton(ObjectField_year, type=number, required)
    'Law Title'               textbox   (ObjectField_lawTitle, required)
    'Law Title — العربية *'   textbox   (#qc-ar-lawTitle, rtl, required)
    'External URL'            textbox   (ObjectField_externalUrl, required,
                                         NOT bilingual)
    'Open Behavior'           combobox  (picklist, required; options
                                         exactly "Same Tab" / "New Tab";
                                         empty on a new form)
    'Display Order'           spinbutton(ObjectField_displayOrder, required)
    'Active Status'           checkbox  (ObjectField_activeStatus)

  - **Active Status defaults to CHECKED on a new Law Regulation entry**
    (observed live 2026-09-29) — the opposite of the `manage-law-entry`
    default standards.md records. Tests still set it explicitly.
  - Case fields that do NOT exist on this object: a page-level record /
    "Law Card repeatable section" (each law is its OWN entry — there is no
    LawsRegulationsPage object; the public fragment's own source says the
    hero copy is static bilingual strings, "permanently plan-only"), so no
    hero fields, and no page-level "Save and publish the page" action. There
    is also no site-wide audit-log screen on this surface; the per-record
    History trail (actor / action / timestamp) is the audit record.
  - No Law Description, no icon, no attachment field (unlike LawEntry).

FORM ACTIONS ARE ROLE-DEPENDENT (list script, ADO 146490): the submit button
reads "Publish" for a self-approving Editor/Administrator (the workflow
approves their submission on the spot), "Submit for Review" for an Author,
and "Save changes" on a record that is off the website. `SUBMIT_BUTTON_NAME`
matches all of them; `submit_button_label()` reports which one rendered.

SAVE FEEDBACK is a `[data-qc-oel-editbar]` banner rendered AFTER the post-save
redirect (the message is carried in sessionStorage): "Draft saved.",
"Saved and published." (self-approving Editor), "Saved and submitted for
review." (Author), "Your change is with a reviewer. ..." (Author editing a
published record), "Changes saved. The record stays off the website until
you publish it." ⚠ OBSERVED LIVE 2026-09-29 (TEST_USER, Save as Draft on a
NEW entry, 2 runs): the add path reloads the plain manage URL ~5 s after the
click and renders NO banner at all — neither "Draft saved." nor "Arabic
content saved for this record." — although the record AND its Arabic values
were stored (verified by reopening). So callers verify the Arabic by reading
it back, and a test that expects a success message after a create will
surface its absence as a failure. A refused save shows inline `[data-qc-oel-field-error]`
notes under the offending fields (inputs flagged `[data-qc-oel-invalid]`)
plus, for anything not tied to a field, a red bar "This record was not
saved: ...". Required fields are also enforced natively (HTML `required`;
`validationMessage` "Please fill out this field.") BEFORE any request.

LIST QUIRKS (observed live 2026-09-29):
  - Paged at 10 rows by default. `select[data-qc-oel-page-size]` offers
    10/25/50/100/0 (0 = all). This class always switches to ALL.
  - ⚠ Filtering with the list's own Search box (`input[data-qc-oel-q]`)
    leaves the filtered rows' actions dead: History did not expand and
    Delete raised no confirm() and sent no request, reproduced 3 times,
    while the same actions worked on the unfiltered list. This class
    therefore NEVER uses the Search box to reach a row; it shows all rows and
    scopes by the row's own `data-qc-oel-delete="<entryId>"` id. Candidate
    product defect — reported, not filed.
  - Delete now calls POST /o/qc-object-status/trash/<id> and the confirm()
    reads 'Delete "<title>"? It is moved to the Recycle Bin under this list,
    where it can be restored.' (ADO 147215) — it is no longer a hard delete.

DELETE SAFETY (standards.md "Destructive Operations"): the only delete path
here is `delete_disposable_entry(entry)`, which takes a `CreatedEntry` the
SAME test captured at creation, refuses any title outside `QCTEST-130699-`,
and re-reads the row's own title immediately before clicking. There is no
positional, "newest row", looping or title-substring delete in this class.

SESSION GUARD CAVEAT: core/web/session_guard.reauthenticate() silently logs a
dropped session back in as TEST_USER. On a role-pinned test that would turn a
Site Content Editor/Author assertion into a super-admin one without any
error, so every role-pinned test re-reads `signed_in_user()` before each
lifecycle assertion. For the same reason `anonymous_probe()` never goes
through BasePage.open()/is_visible(), which would auto-login an anonymous
context on any `manage-*` URL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from cms.pages.components.object_authoring_page import (
    ObjectAuthoringPage,
    normalize_status,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.license_gate import clear_license_gate
from core.web.overlays import _dismiss_chatbot_launcher

logger = get_logger("laws_regulations_admin_page")

LAW_REGULATION_SLUG = "law-regulation"
MANAGE_PATH = f"/web/qatar-chamber/manage-{LAW_REGULATION_SLUG}"
# Every record this suite creates is titled with this prefix; delete refuses
# anything else.
QCTEST_PREFIX = "QCTEST-130699-"
# A real, published record (read-only reference for the anonymous probe).
REAL_REFERENCE_ENTRY_CODE = "QCDEMO-130699-LAWREG-200"
REAL_REFERENCE_TITLE = "Commercial Companies Law"
REAL_REFERENCE_TITLE_AR = "قانون الشركات التجارية رقم (11) لسنة 2015."

# standards.md "Named CMS User Roles" — the pinned accounts.
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}

AUTH_FAILED_BANNER_TEXT = "Authentication failed"

# Save-feedback banner texts (list script; English session).
MSG_DRAFT_SAVED = "Draft saved."
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
MSG_ARABIC_SAVED = "Arabic content saved for this record."
MSG_ARABIC_NOT_SAVED_FRAGMENT = "its Arabic content"

# List badge for a record whose Active Status is unticked (see row_status()).
STATUS_INACTIVE = "Inactive"
# Server refusal for an off-grid Display Order (observed live 2026-09-30).
MSG_DISPLAY_ORDER_GRID = "Display Order must be 100 or greater and follow the 100-grid"

OPEN_BEHAVIOR_SAME_TAB = "Same Tab"
OPEN_BEHAVIOR_NEW_TAB = "New Tab"


@dataclass(frozen=True)
class CreatedEntry:
    """Identity of a record the CURRENT test created — the only thing the
    delete path accepts. `entry_id` is the row's `data-qc-oel-delete` id."""

    title: str
    entry_id: str


class LawsRegulationsAdminPage(ObjectAuthoringPage):
    # ---- Field labels (see module docstring) --------------------------------
    ARABIC_SUFFIX = " — العربية"
    LAW_NUMBER_LABEL = "Law Number"
    YEAR_LABEL = "Year"
    LAW_TITLE_LABEL = "Law Title"
    EXTERNAL_URL_LABEL = "External URL"
    OPEN_BEHAVIOR_LABEL = "Open Behavior"
    DISPLAY_ORDER_LABEL = "Display Order"
    ACTIVE_STATUS_LABEL = "Active Status"

    # ---- List / feedback locators -------------------------------------------
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    PAGE_SIZE_ALL = "0"
    ENTRY_COUNT = "[data-qc-oel-count]"
    ROW_BY_ID = 'table tbody tr:has(a[data-qc-oel-delete="{entry_id}"])'
    DELETE_LINK_BY_ID = 'a[data-qc-oel-delete="{entry_id}"]'
    HISTORY_ROW = "tr[data-qc-oel-history-row]"
    HISTORY_CELL = "td.qc-oel__history"
    HISTORY_ACTION = ".qc-oel__history-action"
    FEEDBACK_BANNER = "[data-qc-oel-editbar]"
    FIELD_ERROR = "[data-qc-oel-field-error]"
    INVALID_FIELD = "[data-qc-oel-invalid]"
    NO_PERMISSION_FORM = "form[data-qc-oel-no-permission]"
    SUBMIT_BUTTON_NAME = re.compile(
        r"^\s*(Publish|Submit for Review|Save changes|Submit for Publishing)\s*$"
    )
    SAVE_AS_DRAFT_NAME = re.compile(r"^\s*Save as Draft\s*$")
    # Any row action marks a rendered row: which actions a row carries depends
    # on the role (an Author has no Delete on other editors' records).
    LIST_LOADED = ", ".join(
        f"a[data-qc-oel-{name}]"
        for name in ("delete", "history", "approve", "reject", "resubmit", "publish",
                     "unpublish", "archive", "restore", "return", "schedule")
    )

    # Every row action a list can render (object_authoring_page ROW_ACTION_ATTRS
    # plus the trash/untrash pair this build added).
    ROW_ACTION_NAMES = (
        "approve", "reject", "resubmit", "publish", "unpublish", "archive",
        "restore", "return", "schedule", "unschedule", "history", "delete",
        "trash", "untrash", "view",
    )
    DESTRUCTIVE_ROW_ACTIONS = frozenset({"delete", "trash", "untrash"})

    # Measured budget: the entries list re-reads the Object after a save;
    # the post-save redirect + Arabic PUT settle well inside this.
    ARABIC_SAVE_TIMEOUT_S = 30.0

    def __init__(self, page):
        super().__init__(page, LAW_REGULATION_SLUG)

    # =====================================================================
    # Session / identity
    # =====================================================================
    def login_as_role(self, role: str) -> str:
        """Real login as a named role in THIS (auth-free) context. Returns
        "ok", "auth_failed" (Liferay's credentials/lockout banner) or
        "unknown". Never falls back to another account."""
        email, password = cms_role_credentials(role)
        login = CmsLoginPage(self.page)
        login.open_login()
        try:
            login.login(email, password)
            return "ok"
        except Exception:  # noqa: BLE001 — classified below, never swallowed as success
            # CmsLoginPage waits for the Control Menu, which roles without
            # Control Panel access (Author) never render. Liferay's own
            # ThemeDisplay is the sign-in signal; callers still pin the userId.
            try:
                self.page.wait_for_load_state("load")
                if self.signed_in_user()[0]:
                    return "ok"
            except Exception:  # noqa: BLE001 — fall through to banner classification
                pass
            try:
                body = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001
                body = ""
            if AUTH_FAILED_BANNER_TEXT in body:
                return "auth_failed"
            return "unknown"

    def signed_in_user(self) -> tuple[str, str]:
        """(userId, full name) of whoever this browser session is signed in
        as, read from Liferay's own ThemeDisplay — ("", "") when signed out.
        The guard against a silent session_guard re-login as TEST_USER."""
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']"""
        )
        return info[0], info[1]

    # =====================================================================
    # Navigation (interface locale pinned to English — see ObjectAuthoringPage)
    # =====================================================================
    def open_new_form(self) -> "LawsRegulationsAdminPage":
        self.open_new_entry_form(locale="en")
        return self

    def open_list(self) -> "LawsRegulationsAdminPage":
        """Entries list with ALL rows shown (never the Search box — see the
        module docstring's list quirk)."""
        self._locale = "en"
        self.open(self._manage_url(locale="en"))
        self.wait_for(self.LIST_LOADED, first=True, timeout=35000)
        self._show_all_rows()
        return self

    def _show_all_rows(self) -> None:
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() == 0:
            return
        if select.input_value() != self.PAGE_SIZE_ALL:
            select.select_option(self.PAGE_SIZE_ALL)
            total = self.total_entry_count()
            try:
                wait_until(
                    lambda: total is None
                    or self.page.locator(self.ENTRIES_TABLE_ROW).count() >= min(total, 1000),
                    timeout=10.0,
                    poll=0.3,
                    message="entries list did not expand to show every row",
                )
            except WaitTimeoutError:
                logger.warning("page-size ALL did not settle to %s rows", total)
        _dismiss_chatbot_launcher(self.page)

    def total_entry_count(self) -> int | None:
        text = self.page.locator(self.ENTRY_COUNT).first.inner_text()
        match = re.search(r"(\d+)\s*total|of\s*(\d+)", text)
        if not match:
            return None
        return int(match.group(1) or match.group(2))

    def is_list_readable(self) -> bool:
        """The entries table rendered at least one row, and the form did not
        render the no-permission state."""
        return self.has_entries() and self.page.locator(self.NO_PERMISSION_FORM).count() == 0

    # =====================================================================
    # Per-field helpers — every real field (Engineer B reuses these)
    # =====================================================================
    def _textbox(self, label: str):
        return self.page.get_by_role("textbox", name=self.label_pattern(label))

    def _spinbutton(self, label: str):
        return self.page.get_by_role("spinbutton", name=self.label_pattern(label))

    def _combobox(self, label: str):
        return self.page.get_by_role("combobox", name=self.label_pattern(label))

    def _checkbox(self, label: str):
        return self.page.get_by_role("checkbox", name=self.label_pattern(label))

    def law_field_locator(self, label: str):
        """Raw control for a field label (EN label or `label + ARABIC_SUFFIX`)
        — for validation helpers below; tests never touch it directly."""
        for getter in (self._textbox, self._spinbutton, self._combobox, self._checkbox):
            loc = getter(label)
            if loc.count() == 1:
                return loc
        raise AssertionError(f"no unique form control labelled {label!r}")

    # Law Number (EN / AR)
    def fill_law_number(self, value: str) -> "LawsRegulationsAdminPage":
        self._textbox(self.LAW_NUMBER_LABEL).fill(value)
        return self

    def fill_law_number_ar(self, value: str) -> "LawsRegulationsAdminPage":
        self._textbox(self.LAW_NUMBER_LABEL + self.ARABIC_SUFFIX).fill(value)
        return self

    def law_number(self) -> str:
        return self._textbox(self.LAW_NUMBER_LABEL).input_value()

    def law_number_ar(self) -> str:
        return self._textbox(self.LAW_NUMBER_LABEL + self.ARABIC_SUFFIX).input_value()

    # Year
    def fill_year(self, value: str) -> "LawsRegulationsAdminPage":
        self._spinbutton(self.YEAR_LABEL).fill(value)
        return self

    def year(self) -> str:
        return self._spinbutton(self.YEAR_LABEL).input_value()

    # Law Title (EN / AR)
    def fill_law_title(self, value: str) -> "LawsRegulationsAdminPage":
        self._textbox(self.LAW_TITLE_LABEL).fill(value)
        return self

    def fill_law_title_ar(self, value: str) -> "LawsRegulationsAdminPage":
        self._textbox(self.LAW_TITLE_LABEL + self.ARABIC_SUFFIX).fill(value)
        return self

    def law_title(self) -> str:
        return self._textbox(self.LAW_TITLE_LABEL).input_value()

    def law_title_ar(self) -> str:
        return self._textbox(self.LAW_TITLE_LABEL + self.ARABIC_SUFFIX).input_value()

    # External URL (not bilingual)
    def fill_external_url(self, value: str) -> "LawsRegulationsAdminPage":
        self._textbox(self.EXTERNAL_URL_LABEL).fill(value)
        return self

    def external_url(self) -> str:
        return self._textbox(self.EXTERNAL_URL_LABEL).input_value()

    # Open Behavior (picklist combobox)
    def select_open_behavior(self, option: str) -> "LawsRegulationsAdminPage":
        """Opens THIS combobox's own listbox (scoped by its aria-controls,
        never the page's other comboboxes — the list's status/page-size
        selects also render `option` roles) and picks `option`."""
        combobox = self._combobox(self.OPEN_BEHAVIOR_LABEL)
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        choice = self.page.locator(f'[id="{listbox_id}"] [role="option"]:text-is("{option}")')
        choice.wait_for(state="visible", timeout=5000)
        choice.click()
        wait_until(
            lambda: combobox.input_value() == option,
            timeout=5.0,
            poll=0.2,
            message=f"Open Behavior did not take the value {option!r}",
        )
        return self

    def open_behavior(self) -> str:
        return self._combobox(self.OPEN_BEHAVIOR_LABEL).input_value()

    def open_behavior_options(self) -> list[str]:
        combobox = self._combobox(self.OPEN_BEHAVIOR_LABEL)
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        options = self.page.locator(f'[id="{listbox_id}"] [role="option"]')
        options.first.wait_for(state="visible", timeout=5000)
        texts = [t.strip() for t in options.all_inner_texts()]
        self.page.keyboard.press("Escape")
        return texts

    # Display Order
    def fill_display_order(self, value: str) -> "LawsRegulationsAdminPage":
        self._spinbutton(self.DISPLAY_ORDER_LABEL).fill(value)
        return self

    def display_order(self) -> str:
        return self._spinbutton(self.DISPLAY_ORDER_LABEL).input_value()

    # Active Status
    def set_active_status(self, active: bool) -> "LawsRegulationsAdminPage":
        box = self._checkbox(self.ACTIVE_STATUS_LABEL)
        if active:
            box.check()
        else:
            box.uncheck()
        return self

    def active_status(self) -> bool:
        return self._checkbox(self.ACTIVE_STATUS_LABEL).is_checked()

    def fill_law(self, data: dict) -> "LawsRegulationsAdminPage":
        """Fills whichever of these keys `data` carries (None/absent = leave
        the field untouched): law_number, law_number_ar, year, law_title,
        law_title_ar, external_url, open_behavior, display_order,
        active_status."""
        setters = (
            ("law_number", self.fill_law_number),
            ("law_number_ar", self.fill_law_number_ar),
            ("year", self.fill_year),
            ("law_title", self.fill_law_title),
            ("law_title_ar", self.fill_law_title_ar),
            ("external_url", self.fill_external_url),
            ("open_behavior", self.select_open_behavior),
            ("display_order", self.fill_display_order),
            ("active_status", self.set_active_status),
        )
        for key, setter in setters:
            if data.get(key) is not None:
                setter(data[key])
        return self

    def read_law(self) -> dict:
        """Every real field's current value off the open form."""
        return {
            "law_number": self.law_number(),
            "law_number_ar": self.law_number_ar(),
            "year": self.year(),
            "law_title": self.law_title(),
            "law_title_ar": self.law_title_ar(),
            "external_url": self.external_url(),
            "open_behavior": self.open_behavior(),
            "display_order": self.display_order(),
            "active_status": self.active_status(),
        }

    # =====================================================================
    # Validation read-outs (Engineer B)
    # =====================================================================
    def field_errors(self) -> list[str]:
        """Inline refusal notes under fields (`[data-qc-oel-field-error]`)."""
        return [t.strip() for t in self.page.locator(self.FIELD_ERROR).all_inner_texts() if t.strip()]

    def field_error_for(self, label: str) -> str:
        """The inline error note belonging to `label`'s OWN control ("" when
        none): first an error element the control points at through
        aria-describedby, else one inside the control's own wrapper — the
        outermost ancestor that still holds exactly ONE form control. It never
        widens to a wrapper holding a second control (e.g. the Arabic twin) or
        to the form, so another field's note is never attributed here."""
        control = self.law_field_locator(label)
        return control.evaluate(
            """(el, sel) => {
                const ids = (el.getAttribute('aria-describedby') || '').split(/\\s+/).filter(Boolean);
                for (const id of ids) {
                    const node = document.getElementById(id);
                    if (!node) continue;
                    const note = node.matches(sel) ? node : node.querySelector(sel);
                    if (note) return note.innerText.trim();
                }
                const controls = 'input:not([type=hidden]), select, textarea';
                let wrapper = null;
                let node = el.parentElement;
                while (node && node.tagName !== 'FORM' && node.querySelectorAll(controls).length === 1) {
                    wrapper = node;
                    node = node.parentElement;
                }
                if (!wrapper) return '';
                const note = wrapper.querySelector(sel);
                return note ? note.innerText.trim() : '';
            }""",
            self.FIELD_ERROR,
        )

    def invalid_field_count(self) -> int:
        return self.page.locator(self.INVALID_FIELD).count()

    def native_validation_message(self, label: str) -> str:
        """The browser's own constraint message for a field ("" = valid)."""
        return self.law_field_locator(label).evaluate("el => el.validationMessage || ''")

    def refusal_bar_text(self) -> str:
        """Text of the red "This record was not saved: ..." bar, or ""."""
        for text in self.feedback_banners():
            if "not saved" in text:
                return text
        return ""

    def type_into_field(self, label: str, text: str) -> str:
        """Clears `label`'s control and TYPES `text` key by key, returning
        the value the control actually holds afterwards. Needed for the
        number fields (Year, Display Order): `fill()` refuses non-numeric
        text on `type=number`, while a real keystroke lets the browser apply
        its own filter — observed live 2026-09-29 (read-only probe, unsaved
        form): typing '20O4' into Year leaves '204' (the letter keystroke is
        dropped) and typing spaces leaves '' (valueMissing)."""
        control = self.law_field_locator(label)
        control.click()
        control.press("Control+A")
        control.press("Delete")
        if text:
            control.press_sequentially(text)
        return control.input_value()

    def field_value(self, label: str) -> str:
        return self.law_field_locator(label).input_value()

    def is_field_required(self, label: str) -> bool:
        """The control carries HTML `required` / aria-required (the form's
        own "required" marking; the label also shows a trailing ' *')."""
        return bool(self.law_field_locator(label).evaluate(
            "el => el.required || el.getAttribute('aria-required') === 'true'"
        ))

    def is_field_editable(self, label: str) -> bool:
        return self.law_field_locator(label).is_editable()

    def open_behavior_after_free_text(self, text: str) -> str:
        """Types arbitrary `text` into the Open Behavior combobox, blurs it,
        and returns what the control kept. Observed live 2026-09-29 on an
        unsaved form: typed text is discarded on blur (value '') — the
        picklist only takes one of its options."""
        combobox = self._combobox(self.OPEN_BEHAVIOR_LABEL)
        combobox.click()
        combobox.press_sequentially(text)
        self.page.keyboard.press("Escape")
        combobox.press("Tab")
        return combobox.input_value()

    def refusal_evidence(self, label: str) -> dict:
        """Everything the form shows about a refusal, attributed to `label`:
        {redirected, native, inline, bar, all_inline}. `redirected` True
        means the last save went THROUGH (no refusal)."""
        redirected = self.save_redirected()
        requests = list(getattr(self, "last_save_requests", []))
        if redirected:
            return {"redirected": True, "refused": False, "native": "", "inline": "", "bar": "",
                    "all_inline": [], "save_requests": requests}
        # A native message counts only when THIS click's submit attempt fired
        # the browser's `invalid` event on the field — a validationMessage the
        # control already carried before the click is not refusal evidence.
        native = self.native_validation_message(label) if self._fired_invalid(label) else ""
        return {
            "redirected": False,
            "refused": bool(getattr(self, "last_save_refused", False)),
            "native": native,
            "inline": self.field_error_for(label),
            "bar": self.refusal_bar_text(),
            "all_inline": self.field_errors(),
            "save_requests": requests,
        }

    def _fired_invalid(self, label: str) -> bool:
        fired = set(getattr(self, "last_invalid_fields", []))
        if not fired:
            return False
        ident = self.law_field_locator(label).evaluate("el => [el.name || '', el.id || '']")
        return any(i and i in fired for i in ident)

    # =====================================================================
    # Save / submit
    # =====================================================================
    def submit_button_label(self) -> str:
        """Which role-dependent submit label rendered ("" = none)."""
        button = self.page.get_by_role("button", name=self.SUBMIT_BUTTON_NAME)
        if button.count() == 0:
            return ""
        return button.first.inner_text().strip()

    def form_action_labels(self) -> list[str]:
        """Visible, ENABLED form buttons among the lifecycle actions."""
        names = []
        for button in self.page.locator("form button").all():
            try:
                if button.is_visible() and button.is_enabled():
                    label = button.inner_text().strip()
                    if label:
                        names.append(label)
            except Exception:  # noqa: BLE001 — a detached node is simply not an action
                continue
        return names

    def is_save_as_draft_enabled(self) -> bool:
        button = self.page.get_by_role("button", name=self.SAVE_AS_DRAFT_NAME)
        return button.count() > 0 and button.first.is_enabled()

    def save_draft(self) -> "LawsRegulationsAdminPage":
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SAVE_AS_DRAFT_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def submit(self) -> "LawsRegulationsAdminPage":
        """Clicks the role-dependent submit button (Publish / Submit for
        Review / Save changes). Asserts nothing — the caller knows its
        pinned account and asserts the outcome."""
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SUBMIT_BUTTON_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    _DOC_MARK = "__qcLawRegBeforeSave"
    # Requests that WRITE the record: the add form's Liferay action
    # (`edit_info_item`) and the edit path's PUT to the Object's REST
    # collection. Any non-GET request matching this after the click means the
    # save was sent, so the attempt cannot be counted as refused.
    SAVE_REQUEST_PATTERN = re.compile(r"edit_info_item|/o/c/lawregulations")
    # A refusal is confirmed only after this long with no navigation and no
    # save request since the click (bounded; the add path's own reload was
    # observed ~5 s after the click, the refused native path sends nothing).
    REFUSAL_QUIET_WINDOW_S = 6.0
    SAVE_OUTCOME_TIMEOUT_S = 60.0

    def _arm_save_probe(self) -> None:
        """Before the click: plant the document marker, start collecting this
        attempt's `invalid` events (the browser fires them only when THIS
        submit fails interactive validation — the reportValidity() evidence),
        and listen for save requests / main-frame navigation."""
        self._save_requests: list[str] = []
        self._save_responses: list[int] = []
        self._navigated = False

        def _is_save(request) -> bool:
            return request.method != "GET" and bool(self.SAVE_REQUEST_PATTERN.search(request.url))

        def _on_request(request):
            try:
                if _is_save(request):
                    self._save_requests.append(f"{request.method} {request.url}")
            except Exception:  # noqa: BLE001 — a detached request is simply not recorded
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
                window.__qcLawRegInvalid = [];
                if (!window.__qcLawRegInvalidHooked) {{
                    window.__qcLawRegInvalidHooked = true;
                    document.addEventListener('invalid', (e) => {{
                        const t = e.target;
                        window.__qcLawRegInvalid.push(t.name || t.id || '');
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
                except Exception:  # noqa: BLE001 — already detached
                    pass
        self._probe_handlers = (None, None, None)

    def _document_replaced(self) -> bool:
        try:
            return not self.page.evaluate(f"() => Boolean(window.{self._DOC_MARK})")
        except Exception:  # noqa: BLE001 — mid-navigation: not settled yet
            return False

    def _invalid_fields_this_attempt(self) -> list[str]:
        try:
            return list(self.page.evaluate("() => window.__qcLawRegInvalid || []"))
        except Exception:  # noqa: BLE001 — mid-navigation
            return []

    def _refusal_shown(self) -> bool:
        """Refusal evidence produced BY this attempt: an `invalid` event fired
        after the click, an inline field note, or the red bar."""
        try:
            return (
                bool(self._invalid_fields_this_attempt())
                or self.page.locator(self.FIELD_ERROR).count() > 0
                or self.refusal_bar_text() != ""
            )
        except Exception:  # noqa: BLE001 — mid-navigation
            return False

    def _wait_for_save_outcome(self) -> None:
        """A successful save RELOADS the manage page (observed live: an add
        lands on the plain manage URL ~5 s later; an edit on
        `?previewEntry=<code>`). A refusal is confirmed only when BOTH hold:
        this attempt produced refusal evidence (see _refusal_shown) AND, for
        REFUSAL_QUIET_WINDOW_S after the click, there was no main-frame
        navigation and no save request. A pre-existing validationMessage alone
        never counts. No fixed sleep: every branch polls a real signal."""
        from time import monotonic

        started = monotonic()
        state = {"value": ""}

        def _outcome() -> bool:
            if self._document_replaced():
                if self.page.locator(self.LIST_LOADED).count() > 0:
                    state["value"] = "reloaded"
                    return True
                return False
            # The server refuses an edit by answering the save PUT with a 4xx
            # and showing the red bar, so a save request only disproves a
            # refusal while it is unanswered or was accepted (< 400).
            answered = len(self._save_responses) >= len(self._save_requests)
            accepted = any(code < 400 for code in self._save_responses)
            quiet = (
                answered
                and not accepted
                and not self._navigated
                and monotonic() - started >= self.REFUSAL_QUIET_WINDOW_S
            )
            if quiet and self._refusal_shown():
                state["value"] = "refused"
                return True
            return False

        try:
            wait_until(_outcome, timeout=self.SAVE_OUTCOME_TIMEOUT_S, poll=0.5,
                       message="save produced neither a reload nor a confirmed refusal")
        except WaitTimeoutError:
            logger.warning("save outcome did not settle; url=%s requests=%s",
                           self.page.url, self._save_requests)
        finally:
            self._disarm_save_probe()
        self.last_save_reloaded = state["value"] == "reloaded"
        self.last_save_refused = state["value"] == "refused"
        self.last_save_requests = list(self._save_requests)
        self.last_invalid_fields = [] if self.last_save_reloaded else self._invalid_fields_this_attempt()

    def save_redirected(self) -> bool:
        """True when the last save_draft()/submit() reloaded the page — the
        surface's own "the save went through" signal."""
        return bool(getattr(self, "last_save_reloaded", False))

    def save_refused(self) -> bool:
        """True when the last save was CONFIRMED refused (evidence from this
        attempt, and no navigation / save request within the quiet window)."""
        return bool(getattr(self, "last_save_refused", False))

    def feedback_banners(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.FEEDBACK_BANNER).all_inner_texts() if t.strip()]

    def wait_for_feedback(self, expected: str, timeout: float = 20.0) -> bool:
        try:
            wait_until(lambda: any(expected in t for t in self.feedback_banners()),
                       timeout=timeout, poll=0.5, message=f"no banner {expected!r}")
            return True
        except WaitTimeoutError:
            return False

    def wait_for_arabic_saved(self, timeout: float | None = None) -> str:
        """After CREATING a bilingual record the Arabic is PUT a moment after
        the record (Object Authoring guide §5). Returns "saved", the failure
        banner text, or "" when neither banner appeared in time."""
        budget = timeout if timeout is not None else self.ARABIC_SAVE_TIMEOUT_S
        outcome = {"value": ""}

        def _done() -> bool:
            for text in self.feedback_banners():
                if MSG_ARABIC_SAVED in text:
                    outcome["value"] = "saved"
                    return True
                if MSG_ARABIC_NOT_SAVED_FRAGMENT in text:
                    outcome["value"] = text
                    return True
            return False

        try:
            wait_until(_done, timeout=budget, poll=0.5, message="no Arabic-save banner")
        except WaitTimeoutError:
            pass
        return outcome["value"]

    # =====================================================================
    # Rows — always scoped by the captured entry id, never by position
    # =====================================================================
    def rows_with_exact_title(self, title: str) -> list[dict]:
        """Every row whose Entry cell equals `title` EXACTLY, on the fully
        expanded list: [{entry_id, title, status, modified}]."""
        return self.page.evaluate(
            """(t) => [...document.querySelectorAll('table tbody tr')]
                .filter(r => r.querySelector('a[data-qc-oel-delete]'))
                .filter(r => r.querySelector('td') && r.querySelector('td').innerText.trim() === t)
                .map(r => {
                    const tds = r.querySelectorAll('td');
                    return {
                        entry_id: r.querySelector('a[data-qc-oel-delete]').getAttribute('data-qc-oel-delete'),
                        title: tds[0].innerText.trim(),
                        status: tds[1] ? tds[1].innerText.trim() : '',
                        modified: tds[2] ? tds[2].innerText.trim() : '',
                    };
                })""",
            title,
        )

    def entry_titles(self) -> list[str]:
        """Entry-column titles of every row on the expanded list (read-only)."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll('table tbody tr')]
                .filter(r => r.querySelector('a[data-qc-oel-delete]'))
                .map(r => r.querySelector('td').innerText.trim())"""
        )

    def capture_created(self, title: str) -> CreatedEntry:
        """Identity of the record just created with `title`. Call it ONLY
        after checking (via rows_with_exact_title) that no row with this
        title existed before creation — then exactly one row is the new one."""
        self.open_list()
        rows = self.rows_with_exact_title(title)
        if len(rows) != 1:
            raise AssertionError(
                f"expected exactly one row titled {title!r} after creating it, "
                f"found {len(rows)}: {rows}"
            )
        return CreatedEntry(title=title, entry_id=rows[0]["entry_id"])

    def _row(self, entry: CreatedEntry):
        return self.page.locator(self.ROW_BY_ID.format(entry_id=entry.entry_id))

    def row_title(self, entry: CreatedEntry) -> str:
        row = self._row(entry)
        return row.locator("td").first.inner_text().strip() if row.count() == 1 else ""

    def row_status(self, entry: CreatedEntry) -> str:
        """Normalized status of the captured row ("" when the row is gone).

        Returns STATUS_INACTIVE when the badge reads "Inactive" (observed live
        2026-09-30: class qc-oel__badge--withdrawn, tooltip "Inactive. Active
        Status is unticked, so nobody sees it on the website…"). User rule: a
        record is public only when Published AND Active Status is ticked, and
        an unticked record shows this badge — it is deliberately NOT mapped to
        Published (the badge hides the workflow state)."""
        row = self._row(entry)
        if row.count() != 1:
            return ""
        raw = row.locator("td").nth(1).inner_text()
        if " ".join(raw.split()).casefold() == STATUS_INACTIVE.casefold():
            return STATUS_INACTIVE
        return normalize_status(raw)

    def row_modified(self, entry: CreatedEntry) -> str:
        row = self._row(entry)
        return row.locator("td").nth(2).inner_text().strip() if row.count() == 1 else ""

    def row_present(self, entry: CreatedEntry) -> bool:
        return self._row(entry).count() == 1

    def rendered_row_count(self) -> int:
        return self.page.locator(f"{self.ENTRIES_TABLE_ROW}:has({self.LIST_LOADED})").count()

    def is_list_fully_expanded(self) -> bool:
        """True only when the list renders EVERY entry (rendered rows ==
        the list's own total). Absence of a row proves nothing otherwise."""
        total = self.total_entry_count()
        return total is not None and self.rendered_row_count() == total

    def row_actions(self, entry: CreatedEntry) -> list[str]:
        """Which `data-qc-oel-<action>` controls the captured row renders —
        depends on its status AND the signed-in role."""
        row = self._row(entry)
        return [
            name for name in self.ROW_ACTION_NAMES
            if row.locator(f"[data-qc-oel-{name}]").count() > 0
        ]

    def open_entry(self, entry: CreatedEntry) -> "LawsRegulationsAdminPage":
        """Opens the captured record for edit through ITS row's own Edit link
        and remembers its entry code so reopen()/wait_for_status() work."""
        self.open_list()
        row = self._row(entry)
        if row.count() != 1:
            raise AssertionError(f"row for {entry} is not on the list")
        href = row.get_by_role("link", name="Edit").first.get_attribute("href") or ""
        match = re.search(r"editEntry=([^&#]+)", href)
        if not match:
            raise AssertionError(f"row for {entry} has no Edit link with an editEntry code")
        self.open_entry_by_code(match.group(1), locale="en")
        return self

    def editing_bar_text(self) -> str:
        for text in self.feedback_banners():
            if text.startswith("Editing"):
                return text
        return ""

    def run_row_action(self, entry: CreatedEntry, action: str, comment: str = "") -> "LawsRegulationsAdminPage":
        """Clicks one id-scoped row action and accepts every native dialog it
        raises (answering prompts with `comment`). Refuses delete / trash /
        untrash: `delete_disposable_entry()` is the only delete path."""
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(
                f"run_row_action refuses {action!r}; use delete_disposable_entry() — the only delete path"
            )
        control = self._row(entry).locator(f"[data-qc-oel-{action}]")
        if control.count() == 0:
            raise AssertionError(
                f"row {entry} offers no {action!r} action; offered: {self.row_actions(entry)}"
            )

        def _accept(dialog):
            try:
                dialog.accept(comment)
            except Exception:  # noqa: BLE001 — already handled
                pass

        self.page.on("dialog", _accept)
        try:
            control.first.click()
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        return self

    def history(self, entry: CreatedEntry) -> list[dict]:
        """Expands the captured row's History trail and returns
        [{action, who, when, comment}] (oldest first as rendered). [] when the
        record has no history yet."""
        self.open_list()
        self._row(entry).locator("[data-qc-oel-history]").first.click()
        cell = self._row(entry).locator(f"xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        try:
            wait_until(
                lambda: cell.count() == 1 and "Loading" not in cell.inner_text(),
                timeout=15.0, poll=0.5, message="history did not load",
            )
        except WaitTimeoutError:
            return []
        items = cell.locator("li")
        result = []
        for i in range(items.count()):
            item = items.nth(i)

            def _part(sel: str) -> str:
                node = item.locator(sel)
                return node.first.inner_text().strip() if node.count() else ""

            result.append({
                "action": _part(self.HISTORY_ACTION),
                "who": _part(self.HISTORY_WHO),
                "when": _part(self.HISTORY_WHEN),
                "comment": _part(self.HISTORY_COMMENT),
            })
        return result

    def delete_disposable_entry(self, entry: CreatedEntry) -> bool:
        """THE ONLY DELETE PATH. Deletes (moves to the Recycle Bin) exactly
        the captured row, after re-verifying — immediately before the click —
        that the row still carries the captured title and that the title is
        in the disposable `QCTEST-130699-` namespace. Returns True once the
        row is gone from the list; False (never raises) when the row is
        already absent. Raises on any identity mismatch: a mismatch means STOP."""
        if not entry.title.startswith(QCTEST_PREFIX):
            raise ValueError(f"refusing to delete {entry.title!r}: not a {QCTEST_PREFIX} record")
        self.open_list()
        row = self._row(entry)
        if row.count() == 0:
            return False
        live_title = self.row_title(entry)
        if live_title != entry.title or not live_title.startswith(QCTEST_PREFIX):
            raise AssertionError(
                f"STOP: row {entry.entry_id} now reads {live_title!r}, not the captured "
                f"{entry.title!r} — refusing to delete"
            )
        link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
        label = link.get_attribute("data-qc-oel-label") or ""
        if label != entry.title:
            raise AssertionError(
                f"STOP: delete link {entry.entry_id} is labelled {label!r}, not {entry.title!r}"
            )
        dialogs: list[str] = []

        def _accept(dialog):
            dialogs.append(dialog.message)
            if entry.title in dialog.message:
                dialog.accept()
            else:
                dialog.dismiss()

        self.page.on("dialog", _accept)
        try:
            link.click()
            row.wait_for(state="detached", timeout=20000)
        finally:
            self.page.remove_listener("dialog", _accept)
        self.open_list()
        return not self.row_present(entry)

    # =====================================================================
    # Anonymous probe — deliberately bypasses BasePage's session guard
    # =====================================================================
    def anonymous_probe(self, url: str) -> dict:
        """Loads `url` in THIS (must be auth-free) context WITHOUT
        BasePage.open()/is_visible(): both invoke session_guard.reauthenticate(),
        which would log an anonymous context in as TEST_USER on a `manage-*`
        URL and turn a denial check into an admin read. Returns what an
        anonymous visitor actually got."""
        response = self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        try:
            self.page.wait_for_load_state("load", timeout=8000)
        except Exception:  # noqa: BLE001 — `load` never fires on some qcdev pages
            pass
        body = self.page.locator("body").inner_text()
        return {
            "status": response.status if response else None,
            "final_url": self.page.url,
            "body_text": body,
            "html": self.page.content(),
            "signed_in": self.signed_in_user()[0] != "",
            "login_form_shown": self.page.locator(CmsLoginPage.USERNAME_INPUT).count() > 0,
            "authoring_form_present": self.page.get_by_role("button", name=self.SAVE_AS_DRAFT_NAME).count() > 0,
            "entries_table_present": self.page.locator(self.LIST_LOADED).count() > 0,
        }

    @staticmethod
    def manage_url(edit_entry: str | None = None) -> str:
        path = MANAGE_PATH + (f"?editEntry={edit_entry}" if edit_entry else "")
        return control_panel_url(path)

"""
cms/pages/annual_reports/annual_reports_page_admin_page.py —
AnnualReportsPageAdminPage / AnnualReportsPublicView.

Control_Panel Page Object for the **Annual Reports Page** Object Authoring
surface (PBI 130712, "QC - Insights & Media - 004 - Annual Reports") — the
page-level settings object that drives the public page's hero (Eyebrow /
Page Title / Hero Description / Hero Banner) and its Report Archive section
header (Section Badge / Section Title / Section Description):
    https://qcdev.ihorizons.com/web/qatar-chamber/manage-annual-reports-page
The per-report object (`manage-ann-rpt`) lives in annual_report_admin_page.py.

REWORKED 2026-10-04 for the seven-state editorial workflow, the named role
accounts and a TEST_OWNED singleton edit-and-restore model (it used to be
read-only). Everything below was re-read live on 2026-10-04 as the Site
Content Editor (156488), read-only, before any test wrote to the record.

═══════════════════════════════════════════════════════════════════════
THE SINGLETON — READ FIRST
  Exactly ONE record: entry code `QCDEMO-130712-PAGE-MAIN`, entry id 144940,
  PUBLISHED, Active Status ticked. It is the REAL live page content. The
  public fragment reads `/o/c/annualreportspages/scopes/37246?pageSize=1`
  (the first record), so there is no disposable alternative to it.
  Rules this module enforces:
    - never deleted, never unpublished (there is no unpublish/delete method
      here at all);
    - every edit is TEST_OWNED: `snapshot()` captures every field (EN + AR),
      Active Status, the banner file name AND its bytes (sha256) first, and
      `restore()` writes back only what differs, re-publishes, and verifies
      the result from a FRESH open (values + banner bytes + row status);
    - new records on this object are never created by automation (they
      could not be removed again under the no-delete rule).
═══════════════════════════════════════════════════════════════════════

FORM (live 2026-10-04, `/en/` interface). Every control is addressed by its
stable `name` / `id`, never by a fragment-generated id or label text, so the
same locator works in the Arabic interface too:

    key                  EN control                              AR control
    eyebrowLabel         input[name=ObjectField_eyebrowLabel]     #qc-ar-eyebrowLabel
    pageTitle            input[name=ObjectField_pageTitle]        #qc-ar-pageTitle
    heroDescription      textarea[name=ObjectField_heroDescription]  #qc-ar-heroDescription
    sectionBadge         input[name=ObjectField_sectionBadge]     #qc-ar-sectionBadge
    sectionTitle         input[name=ObjectField_sectionTitle]     #qc-ar-sectionTitle
    sectionDescription   textarea[name=ObjectField_sectionDescription] #qc-ar-sectionDescription
    heroBanner           attachment; NOT `required`; help line "Upload a .jpg,.jpeg,.png
                         no larger than 5 MB."; the picker's own config carries
                         extensions [.jpg,.jpeg,.png] and maxFileSize "5"
    activeStatus         checkbox input[name=ObjectField_activeStatus] (ticked), NOT
                         `required`. There is NO separate page "Status" picklist.

  Every EN and AR text control carries the HTML `required` attribute and a
  `data-qc-oel-counter`; NO `maxlength`. The two descriptions are plain
  <textarea>s holding HTML (no CKEditor is mounted on this object), stored
  and served as HTML.
  The AR twins are populated by script a beat after the form renders;
  `open_singleton()` waits for all six before anything is read or typed.

FORM ACTIONS on the published singleton (Editor):
    button[name=status][value="0"]  "Publish" ("As an Editor, what you publish
                                     here goes live straight away.")
    button[name=status][value="2"]  "Save as Draft" — hidden + disabled ("This
                                     record is published. Unpublish it first")
  The edit bar reads: "Editing QCDEMO-130712-PAGE-MAIN (Published). It is
  published. Publish puts your change on the website straight away. ..."
  So an Editor edits the published record in place and Publish re-publishes
  it — no Unpublish (no outage) is needed for any field change.

ROW (entries list): ENTRY / STATUS / LAST MODIFIED / ACTIONS; actions carry
`data-qc-oel-<action>="144940"` (unpublish, history, delete for the Editor).

PUBLIC PAGE (web/pages/annual_reports/annual_reports_page.py): the hero
description and archive description are rendered as HTML inside
`div.qc-ar-hero-desc` / `div.qc-ar-archive-desc`; the banner is passed as the
CSS custom property `--qc-ar-hero-img-url` on `header.qc-ar-hero` (live
2026-10-04 its computed background is only the radial gradient and
`.qc-ar-hero-art` has `background-image: none`).

SESSION GUARD CAVEAT: BasePage.open() can silently log a dropped session back
in as TEST_USER. A role-pinned session therefore navigates WITHOUT that guard
(`open()` below) and tests re-read `signed_in_user()` before asserting.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from time import monotonic

from cms.pages.components.object_authoring_page import (
    STATUS_PUBLISHED,
    ObjectAuthoringPage,
    normalize_status,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url, web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.license_gate import clear_license_gate
from core.web.overlays import _dismiss_chatbot_launcher, dismiss_overlays
from web.pages.annual_reports.annual_reports_page import ANNUAL_REPORTS_PATH, AnnualReportsPage

logger = get_logger("annual_reports_page_admin_page")

SLUG = "annual-reports-page"
SINGLETON_ENTRY_CODE = "QCDEMO-130712-PAGE-MAIN"
SINGLETON_ENTRY_ID = "144940"
SINGLETON_TITLE = SINGLETON_ENTRY_CODE  # back-compat name (the Entry column shows the code)
PUBLIC_PAGE_RECORD_PATH = "/o/c/annualreportspages/"
QCTEST_MARK = "QCTEST-130712"

# standards.md "Named CMS User Roles" — the pinned accounts.
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}
AUTH_FAILED_BANNER_TEXT = "Authentication failed"

# Edit-bar feedback strings (English interface; same wording as every sibling object).
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_DRAFT_SAVED = "Draft saved."
MSG_REQUIRED_FIELDS_BAR = "Please complete the required fields"
# The cases' expected Arabic-content refusal (143827 / 143828).
MSG_ARABIC_REQUIRED_EN = "Arabic content is required."
MSG_ARABIC_REQUIRED_AR = "المحتوى بالعربية مطلوب."

# ---- Back-compat label constants (imported by older modules) -------------
FIELD_EYEBROW_EN = "Eyebrow Label"
FIELD_EYEBROW_AR = "Eyebrow Label — العربية *"
FIELD_PAGE_TITLE_EN = "Page Title"
FIELD_PAGE_TITLE_AR = "Page Title — العربية *"
FIELD_HERO_DESCRIPTION_EN = "Hero Description"
FIELD_HERO_DESCRIPTION_AR = "Hero Description — العربية *"
FIELD_HERO_BANNER = "Hero Banner"
FIELD_SECTION_BADGE_EN = "Section Badge"
FIELD_SECTION_BADGE_AR = "Section Badge — العربية *"
FIELD_SECTION_TITLE_EN = "Section Title"
FIELD_SECTION_TITLE_AR = "Section Title — العربية *"
FIELD_SECTION_DESCRIPTION_EN = "Section Description"
FIELD_SECTION_DESCRIPTION_AR = "Section Description — العربية *"
FIELD_ACTIVE_STATUS = "Active Status"


@dataclass(frozen=True)
class PageField:
    """One bilingual field of the singleton (`name` is the object field key)."""

    key: str
    label: str
    name: str
    rich: bool = False

    @property
    def en_selector(self) -> str:
        return f'form [name="ObjectField_{self.name}"]'

    @property
    def ar_selector(self) -> str:
        return f"#qc-ar-{self.name}"


EYEBROW = PageField("eyebrow", FIELD_EYEBROW_EN, "eyebrowLabel")
PAGE_TITLE = PageField("page_title", FIELD_PAGE_TITLE_EN, "pageTitle")
HERO_DESCRIPTION = PageField("hero_description", FIELD_HERO_DESCRIPTION_EN, "heroDescription", rich=True)
SECTION_BADGE = PageField("section_badge", FIELD_SECTION_BADGE_EN, "sectionBadge")
SECTION_TITLE = PageField("section_title", FIELD_SECTION_TITLE_EN, "sectionTitle")
SECTION_DESCRIPTION = PageField("section_description", FIELD_SECTION_DESCRIPTION_EN, "sectionDescription",
                                rich=True)
FIELDS = (EYEBROW, PAGE_TITLE, HERO_DESCRIPTION, SECTION_BADGE, SECTION_TITLE, SECTION_DESCRIPTION)
HERO_FIELDS = (EYEBROW, PAGE_TITLE, HERO_DESCRIPTION)
ARCHIVE_FIELDS = (SECTION_BADGE, SECTION_TITLE, SECTION_DESCRIPTION)


def unique_copy(file_path: str) -> str:
    """A uniquely named temporary copy of `file_path` (same bytes) — Documents
    & Media de-duplicates / refuses repeated same-name uploads. Every upload
    leaves a file in the site library; this framework never deletes D&M files."""
    import shutil
    import tempfile
    import uuid

    base, ext = os.path.splitext(os.path.basename(file_path))
    folder = os.path.join(tempfile.gettempdir(), "qctest_uploads_130712_page")
    os.makedirs(folder, exist_ok=True)
    target = os.path.join(folder, f"{base}-{uuid.uuid4().hex[:8]}{ext}")
    shutil.copyfile(file_path, target)
    return target


def _accept_beforeunload(dialog) -> None:
    if dialog.type == "beforeunload":
        try:
            dialog.accept()
        except Exception:  # noqa: BLE001 — already handled
            pass


def norm(value) -> str:
    """Whitespace-collapsed string form used for every stored-value comparison."""
    return "" if value is None else " ".join(str(value).split())


class AnnualReportsPageAdminPage(ObjectAuthoringPage):
    """The Annual Reports Page singleton (see module docstring)."""

    SUBMIT_BUTTON = 'form button[type="submit"][name="status"][value="0"]'
    DRAFT_BUTTON = 'form button[type="submit"][name="status"][value="2"]'
    FEEDBACK_BANNER = "[data-qc-oel-editbar]"
    FIELD_ERROR = "[data-qc-oel-field-error]"
    FRAGMENT_ERROR = 'p[id$="-error"].text-danger:not(.sr-only)'
    ROW_BY_ID = 'table tbody tr:has([data-qc-oel-history="{entry_id}"])'
    HISTORY_CELL = "td.qc-oel__history"
    HISTORY_ACTION = ".qc-oel__history-action"
    ROW_ACTION_NAMES = ("approve", "reject", "resubmit", "publish", "unpublish", "archive",
                        "restore", "return", "schedule", "history", "delete")
    ACTIVE_STATUS_CHECKBOX = 'form input[name="ObjectField_activeStatus"][type="checkbox"]'
    BANNER_INPUT = 'form [name="ObjectField_heroBanner"]'
    BANNER_META = ".qc-oel__current-file-meta"
    SAVE_REQUEST_PATTERN = re.compile(r"manage-annual-reports-page|/o/c/annualreportspages|edit_info_item")
    ARABIC_HYDRATED_TIMEOUT_S = 25.0
    REFUSAL_QUIET_WINDOW_S = 6.0
    SAVE_OUTCOME_TIMEOUT_S = 60.0
    _DOC_MARK = "__qcAnnualReportsPageBeforeSave"
    pinned_role: str | None = None

    def __init__(self, page):
        super().__init__(page, SLUG)
        # Back-compat: older call sites reached the state machine via `.authoring`.
        self.authoring = self
        # Leaving an edited-but-unsaved form must never hang on the browser's
        # "leave site?" prompt; every other dialog is left to its own caller.
        page.on("dialog", _accept_beforeunload)

    # =====================================================================
    # Session / identity
    # =====================================================================
    def open(self, url: str) -> None:
        """Role-pinned sessions navigate WITHOUT BasePage's session guard (it
        re-logs an unrecognised session in as TEST_USER, which would silently
        turn a role assertion into a super-admin one)."""
        if not self.pinned_role:
            super().open(url)
            return
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page, grace_ms=1500)

    def login_as_role(self, role: str) -> str:
        """Real login as a named role in THIS (auth-free) context. Returns
        "ok", "auth_failed" or "unknown". Never falls back to another account."""
        email, password = cms_role_credentials(role)
        login = CmsLoginPage(self.page)
        login.open_login()
        try:
            login.login(email, password)
            self.pinned_role = role
            return "ok"
        except Exception:  # noqa: BLE001 — classified below, never treated as success
            try:
                body = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001
                body = ""
            if AUTH_FAILED_BANNER_TEXT in body:
                return "auth_failed"
            try:
                if self.signed_in_user()[0]:
                    self.pinned_role = role
                    return "ok"
            except Exception:  # noqa: BLE001
                pass
            return "unknown"

    def signed_in_user(self) -> tuple[str, str]:
        """(userId, full name) from Liferay's ThemeDisplay — ("", "") signed out."""
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']"""
        )
        return info[0], info[1]

    # =====================================================================
    # Entries list (scoped by the singleton's entry id, never by position)
    # =====================================================================
    def open_list(self) -> "AnnualReportsPageAdminPage":
        self._locale = "en"
        self.open(self._manage_url(locale="en"))
        self.page.locator(self.ROW_BY_ID.format(entry_id=SINGLETON_ENTRY_ID)).first.wait_for(
            state="attached", timeout=40000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entries_list(self, locale: str | None = "en") -> "AnnualReportsPageAdminPage":
        return self.open_list()

    def _row(self):
        return self.page.locator(self.ROW_BY_ID.format(entry_id=SINGLETON_ENTRY_ID))

    def list_row_count(self) -> int:
        """Rows on the entries list that carry any row action (read-only)."""
        return self.page.locator("table tbody tr:has([data-qc-oel-history])").count()

    def singleton_row_status(self) -> str:
        self.open_list()
        row = self._row()
        return normalize_status(row.first.locator("td").nth(1).inner_text()) if row.count() == 1 else ""

    def singleton_row_modified(self) -> str:
        self.open_list()
        row = self._row()
        return row.first.locator("td").nth(2).inner_text().strip() if row.count() == 1 else ""

    def singleton_row_actions(self) -> list[str]:
        self.open_list()
        row = self._row().first
        return [n for n in self.ROW_ACTION_NAMES if row.locator(f"[data-qc-oel-{n}]").count() > 0]

    def singleton_history(self) -> list[dict]:
        """Expands the singleton row's History trail -> [{action, who, when, comment}]."""
        self.open_list()
        self._row().first.locator("[data-qc-oel-history]").first.click(force=True)
        cell = self._row().first.locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        try:
            wait_until(lambda: cell.count() == 1 and "Loading" not in cell.inner_text(),
                       timeout=15.0, poll=0.5, message="history did not load")
        except WaitTimeoutError:
            return []
        items = cell.locator("li")
        out = []
        for i in range(items.count()):
            item = items.nth(i)

            def _part(sel: str) -> str:
                node = item.locator(sel)
                return node.first.inner_text().strip() if node.count() else ""

            out.append({"action": _part(self.HISTORY_ACTION), "who": _part(self.HISTORY_WHO),
                        "when": _part(self.HISTORY_WHEN), "comment": _part(self.HISTORY_COMMENT),
                        "text": item.inner_text().strip()})
        return out

    def run_singleton_row_action(self, action: str, comment: str = "") -> "AnnualReportsPageAdminPage":
        """Only the non-destructive `publish` action is allowed on the singleton
        (used by restore when the record is found Unpublished)."""
        if action != "publish":
            raise ValueError(f"refusing row action {action!r} on the live singleton")
        self.open_list()
        control = self._row().first.locator("[data-qc-oel-publish]")
        if control.count() == 0:
            raise AssertionError(f"the singleton row offers no publish action: {self.singleton_row_actions()}")

        def _accept(dialog):
            try:
                dialog.accept(comment)
            except Exception:  # noqa: BLE001
                pass

        self.page.on("dialog", _accept)
        try:
            control.first.click(force=True)
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        return self

    # =====================================================================
    # Edit form
    # =====================================================================
    def open_singleton(self, locale: str = "en") -> "AnnualReportsPageAdminPage":
        """Opens the singleton's edit form (interface language pinned) and waits
        until all six Arabic twins are populated."""
        url = self._manage_url(edit_entry=SINGLETON_ENTRY_CODE, locale=locale)
        self._entry_code, self._locale = SINGLETON_ENTRY_CODE, locale
        for attempt in (1, 2):
            self.open(url)
            self.page.locator(self.SUBMIT_BUTTON).first.wait_for(state="attached", timeout=40000)
            try:
                # Fully initialised = the edit bar names the record, all six
                # Arabic twins are populated and the banner shows its current file.
                wait_until(self._form_ready, timeout=self.ARABIC_HYDRATED_TIMEOUT_S, poll=0.3,
                           message="the singleton edit form never finished initialising")
                break
            except WaitTimeoutError:
                logger.warning("singleton edit form not initialised (attempt %s): %s", attempt, self._readiness())
                if attempt == 2:
                    raise AssertionError(f"the {SINGLETON_ENTRY_CODE} edit form never finished initialising "
                                         f"(Arabic twins / edit bar): {self._readiness()}")
        _dismiss_chatbot_launcher(self.page)
        return self

    def _readiness(self) -> dict:
        """Initialisation signals of the edit form: every Arabic twin carries
        the script's own `data-qc-ar-ready` marker (set once its stored value
        is loaded — value-independent, so an empty stored AR still counts) and
        the edit bar names the record."""
        try:
            return {"arabic_ready": {f.name: self.page.locator(f.ar_selector).first.get_attribute("data-qc-ar-ready")
                                     is not None for f in FIELDS},
                    "edit_bar": any(SINGLETON_ENTRY_CODE in t for t in self.feedback_banners())}
        except Exception as exc:  # noqa: BLE001
            return {"error": repr(exc)}

    def _form_ready(self) -> bool:
        state = self._readiness()
        ready = state.get("arabic_ready") or {}
        return bool(ready) and all(ready.values()) and bool(state.get("edit_bar"))

    def open_singleton_for_read(self) -> "AnnualReportsPageAdminPage":
        return self.open_singleton()

    def reopen(self) -> "AnnualReportsPageAdminPage":
        return self.open_singleton(self._locale or "en")

    def _arabic_hydrated(self) -> bool:
        return all(self.page.locator(f.ar_selector).first.input_value() for f in FIELDS)

    def open_new_entry_form_readonly(self) -> "AnnualReportsPageAdminPage":
        """Opens the CREATE form (manage page without editEntry) for inspection
        only — callers never submit it (no new record is ever created)."""
        self.open(self._manage_url(locale="en"))
        self._entry_code, self._locale = None, "en"
        self.page.locator(self.SUBMIT_BUTTON).first.wait_for(state="attached", timeout=40000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def _control(self, field: PageField, arabic: bool = False):
        return self.page.locator(field.ar_selector if arabic else field.en_selector).first

    def fill_field(self, field: PageField, value: str, arabic: bool = False) -> "AnnualReportsPageAdminPage":
        control = self._control(field, arabic)
        control.fill(value)
        control.dispatch_event("change")
        return self

    def clear_field(self, field: PageField, arabic: bool = False) -> "AnnualReportsPageAdminPage":
        return self.fill_field(field, "", arabic)

    def field_text(self, field: PageField, arabic: bool = False) -> str:
        return self._control(field, arabic).input_value()

    def field_value(self, field_label: str) -> str:
        """Back-compat label-based read (older modules pass FIELD_* labels)."""
        for field in FIELDS:
            if field_label == field.label:
                return self.field_text(field)
            if field_label.startswith(field.label + " — "):
                return self.field_text(field, arabic=True)
        return super().field_value(field_label)

    def field_native_message(self, field: PageField, arabic: bool = False) -> str:
        return self._control(field, arabic).evaluate("el => el.validationMessage || ''")

    def field_is_required(self, field: PageField, arabic: bool = False) -> bool:
        return bool(self._control(field, arabic).evaluate("el => el.required"))

    def all_values(self) -> dict:
        out = {}
        for field in FIELDS:
            out[field.key] = self.field_text(field)
            out[field.key + "_ar"] = self.field_text(field, arabic=True)
        return out

    # ---- Active Status -------------------------------------------------------
    def active_status_checked(self) -> bool:
        return self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first.is_checked()

    def set_active_status(self, checked: bool) -> "AnnualReportsPageAdminPage":
        box = self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first
        box.check() if checked else box.uncheck()
        return self

    def active_status_is_required(self) -> bool:
        return bool(self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first.evaluate("el => el.required"))

    def status_like_controls(self) -> list[dict]:
        """Every form control whose name/label mentions "status" (read-only
        inspection for the page-Status cases)."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll('form input, form select, form textarea')]
                .filter(e => /status/i.test(e.name || '') || /status/i.test(e.id || ''))
                .map(e => {
                    let box = e; for (let i = 0; i < 6 && box && !box.querySelector('label'); i++) box = box.parentElement;
                    const label = box && box.querySelector('label') ? box.querySelector('label').innerText.trim() : '';
                    return {name: e.name, type: e.type, tag: e.tagName, required: !!e.required,
                            checked: e.type === 'checkbox' ? e.checked : null, value: e.value, label};
                })"""
        )

    def visible_text(self) -> str:
        """Visible text of the whole page (for message searches)."""
        try:
            return " ".join(self.page.locator("body").inner_text().split())
        except Exception:  # noqa: BLE001
            return ""

    def form_labels(self) -> list[str]:
        return [t.strip() for t in self.page.locator("form label").all_inner_texts() if t.strip()]

    # ---- Hero Banner ----------------------------------------------------------
    def banner_file_name(self) -> str:
        """Name of the file stored on the record ("" when none), from the
        field's own "Current file: <name> — pick a file to replace it" placeholder."""
        node = self.page.locator(self.BANNER_INPUT)
        placeholder = (node.first.get_attribute("placeholder") or "") if node.count() else ""
        match = re.match(r"Current file:\s*(.+?)\s+—", placeholder)
        return match.group(1) if match else ""

    def banner_help_text(self) -> str:
        container = self._file_upload_container(FIELD_HERO_BANNER)
        node = container.locator("p", has_text="no larger than")
        return node.first.inner_text().strip() if node.count() else ""

    def banner_download_url(self) -> str:
        meta = self.page.locator(self.BANNER_META)
        if meta.count() == 0:
            return ""
        link = meta.first.get_by_role("link", name="Download")
        href = link.first.get_attribute("href") if link.count() else ""
        return control_panel_url(href) if href else ""

    def banner_bytes(self) -> bytes:
        """Bytes of the stored banner via this session's own cookies (b"" when none)."""
        url = self.banner_download_url()
        if not url:
            return b""
        response = self.page.context.request.get(url)
        return response.body() if response.ok else b""

    def download_banner(self, dest_dir: str) -> str:
        """Saves the stored banner's bytes (TEST_OWNED baseline for a binary
        restore) under its own file name in `dest_dir`; opens the record first."""
        self.open_singleton()
        name = self.banner_file_name()
        data = self.banner_bytes()
        if not name or not data:
            return ""
        path = os.path.join(dest_dir, name)
        with open(path, "wb") as handle:
            handle.write(data)
        return path

    def remove_banner(self) -> "AnnualReportsPageAdminPage":
        """Clicks the field's own "Remove file" (takes effect only on save)."""
        self._file_upload_container(FIELD_HERO_BANNER).get_by_role("button", name="Remove file").click()
        return self

    def banner_pending_name(self) -> str:
        """Filename readout of a NEWLY selected (not yet saved) file."""
        try:
            return self.page.get_by_role("textbox", name=FIELD_HERO_BANNER, exact=True).inner_text().strip()
        except Exception:  # noqa: BLE001
            return ""

    PICKER_FEEDBACK_RE = re.compile(
        r"(valid extension|valid file size|no larger than|exceeds|too large|not supported|not allowed|"
        r"maximum|invalid file|file type)", re.I)

    def _picker_feedback(self, frame) -> str:
        for scope in (frame, self.page):
            try:
                nodes = scope.get_by_text(self.PICKER_FEEDBACK_RE)
                for i in range(min(nodes.count(), 10)):
                    node = nodes.nth(i)
                    text = " ".join((node.inner_text() or "").split())
                    if node.is_visible() and text and not text.startswith("Upload a "):
                        return text
            except Exception:  # noqa: BLE001 — frame detached mid-read
                continue
        return ""

    def _picker_closed(self, timeout: int) -> bool:
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001
            return False

    def close_picker(self) -> None:
        if self._picker_closed(1500):
            return
        self.page.keyboard.press("Escape")
        if self._picker_closed(5000):
            return
        for name in ("Cancel", "Close"):
            button = self.page.get_by_role("button", name=name)
            if button.count():
                try:
                    button.first.click(timeout=5000)
                    break
                except Exception:  # noqa: BLE001
                    continue
        if not self._picker_closed(6000):
            raise AssertionError("the Documents & Media picker would not close")

    PICKER_READY_TIMEOUT_MS = 45000

    def _open_banner_picker(self):
        """Opens the Hero Banner picker and waits for its upload input. The
        picker iframe is a full Documents & Media page (1,400+ library entries)
        and was observed live taking more than 30 s to mount its file input
        under load; one re-open is allowed before giving up."""
        hidden = self.page.get_by_role("textbox", name=f"{FIELD_HERO_BANNER} Select File")
        for attempt in (1, 2):
            hidden.locator("xpath=..").get_by_role("button", name="Select File").click()
            frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
            try:
                frame.locator('input[type="file"]').first.wait_for(state="attached",
                                                                   timeout=self.PICKER_READY_TIMEOUT_MS)
                return frame
            except Exception:  # noqa: BLE001 — re-open once, then fail loudly
                logger.warning("Hero Banner picker input not ready (attempt %s)", attempt)
                self.close_picker()
        raise AssertionError("the Hero Banner picker never showed its upload input")

    def try_banner_upload(self, file_path: str, add_if_accepted: bool = True, timeout: float = 30.0) -> dict:
        """Drives the Hero Banner picker for `file_path` and reports what the
        picker said: {"rejection", "accepted" ("1 of 1" shown), "added" (Add
        clicked and the picker closed), "picker_text"}. Always leaves the
        picker closed."""
        frame = self._open_banner_picker()
        frame.locator('input[type="file"]').set_input_files(file_path)
        result = {"file": os.path.basename(file_path), "rejection": "", "accepted": False, "added": False,
                  "picker_text": ""}

        def _resolved() -> bool:
            rejection = self._picker_feedback(frame)
            if rejection:
                result["rejection"] = rejection
                return True
            if frame.get_by_text("1 of 1").count():
                result["accepted"] = True
                return True
            return False

        try:
            wait_until(_resolved, timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass
        try:
            result["picker_text"] = " ".join(frame.locator("body").evaluate(
                "b => b.innerText || b.textContent || ''").split())[:1500]
        except Exception:  # noqa: BLE001
            pass
        if result["accepted"] and add_if_accepted:
            frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click(timeout=15000)
            result["added"] = self._picker_closed(15000)
            if not result["added"]:
                result["rejection"] = self._picker_feedback(frame) or result["rejection"]
        self.close_picker()
        return result

    def upload_banner(self, file_path: str) -> dict:
        """Uploads `file_path` as the new banner; raises when the picker did not take it."""
        result = self.try_banner_upload(file_path)
        if not (result["accepted"] and result["added"]):
            raise AssertionError(f"the Hero Banner picker did not take {file_path}: {result}")
        return result

    # =====================================================================
    # Save (with an outcome probe — a click alone does not mean saved)
    # =====================================================================
    def submit_button_label(self) -> str:
        button = self.page.locator(self.SUBMIT_BUTTON)
        return button.first.inner_text().strip() if button.count() else ""

    def is_draft_enabled(self) -> bool:
        button = self.page.locator(self.DRAFT_BUTTON)
        return button.count() > 0 and button.first.is_visible() and button.first.is_enabled()

    def submit(self) -> "AnnualReportsPageAdminPage":
        """Clicks the role-dependent submit button ("Publish" for an Editor).
        Asserts nothing; read `outcome()` afterwards."""
        self._arm_probe()
        _dismiss_chatbot_launcher(self.page)
        self.page.locator(self.SUBMIT_BUTTON).first.click()
        self._wait_for_save_outcome()
        return self

    def _visible_texts(self, selector: str) -> list[str]:
        found = self.page.locator(selector)
        out = []
        for i in range(found.count()):
            node = found.nth(i)
            try:
                if node.is_visible():
                    text = " ".join((node.inner_text() or "").split())
                    if text:
                        out.append(text)
            except Exception:  # noqa: BLE001 — node vanished mid-read
                continue
        return out

    def feedback_banners(self) -> list[str]:
        try:
            return self._visible_texts(self.FEEDBACK_BANNER)
        except Exception:  # noqa: BLE001 — mid-navigation
            return []

    def native_invalid_messages(self) -> dict:
        """{control name-or-id: validationMessage} for every form control whose
        validity state is currently invalid. Reads `validity` only — it never
        calls checkValidity(), which would fire `invalid` events and make the
        page render messages of its own.
        NOTE (live 2026-10-04): the Arabic twins and the banner input carry a
        stale custom validity ("Please fill out this field.") from before the
        script hydrated them; it does not block a save, so this reader is
        evidence only, never a precondition."""
        try:
            return dict(self.page.evaluate(
                "() => Object.fromEntries([...document.querySelectorAll('form input, form textarea')]"
                ".filter(e => e.willValidate && e.validity && !e.validity.valid)"
                ".map(e => [(e.name || e.id), e.validationMessage]))"
            ))
        except Exception:  # noqa: BLE001
            return {}

    def field_errors_by_control(self) -> dict:
        """{control key (ObjectField_<name> / qc-ar-<name>): visible inline
        error text} — each visible `[data-qc-oel-field-error]` is attributed to
        the single named control in its nearest enclosing block."""
        try:
            return dict(self.page.evaluate(
                """(sel) => {
                    const out = {};
                    for (const err of document.querySelectorAll(sel)) {
                        if (!err.offsetParent || !(err.innerText || '').trim()) continue;
                        let box = err.parentElement, key = '';
                        for (let i = 0; i < 6 && box && !key; i++, box = box.parentElement) {
                            const ctrls = [...box.querySelectorAll('input, textarea')]
                                .filter(c => (c.name && c.name.startsWith('ObjectField_') && !/_[a-z]{2}_[A-Z]{2}$/.test(c.name))
                                             || (c.id || '').startsWith('qc-ar-'));
                            if (ctrls.length === 1) key = ctrls[0].name || ctrls[0].id;
                            else if (ctrls.length > 1) break;
                        }
                        out[key || '?'] = (out[key || '?'] ? out[key || '?'] + ' | ' : '') + err.innerText.trim();
                    }
                    return out;
                }""",
                self.FIELD_ERROR,
            ))
        except Exception:  # noqa: BLE001
            return {}

    def _arm_probe(self) -> None:
        self._requests: list[str] = []
        self._responses: list[int] = []
        self._bars_before = set(self.feedback_banners())

        def _is_save(request) -> bool:
            return request.method != "GET" and bool(self.SAVE_REQUEST_PATTERN.search(request.url))

        def _on_request(request):
            try:
                if _is_save(request):
                    self._requests.append(f"{request.method} {request.url[:200]}")
            except Exception:  # noqa: BLE001
                pass

        def _on_response(response):
            try:
                if _is_save(response.request):
                    self._responses.append(response.status)
            except Exception:  # noqa: BLE001
                pass

        self._probe_handlers = (_on_request, _on_response)
        self.page.on("request", _on_request)
        self.page.on("response", _on_response)
        self.page.evaluate(
            f"""() => {{
                window.{self._DOC_MARK} = true;
                window.__qcArpInvalid = {{}};
                if (!window.__qcArpHooked) {{
                    window.__qcArpHooked = true;
                    document.addEventListener('invalid', (e) => {{
                        const t = e.target; window.__qcArpInvalid[t.name || t.id || '?'] = t.validationMessage;
                    }}, true);
                }}
            }}"""
        )

    def _disarm_probe(self) -> None:
        on_request, on_response = getattr(self, "_probe_handlers", (None, None))
        for event, handler in (("request", on_request), ("response", on_response)):
            if handler is not None:
                try:
                    self.page.remove_listener(event, handler)
                except Exception:  # noqa: BLE001
                    pass
        self._probe_handlers = (None, None)

    def _document_replaced(self) -> bool:
        try:
            return not self.page.evaluate(f"() => Boolean(window.{self._DOC_MARK})")
        except Exception:  # noqa: BLE001 — mid-navigation
            return False

    def _invalid_this_attempt(self) -> dict:
        try:
            return dict(self.page.evaluate("() => window.__qcArpInvalid || {}"))
        except Exception:  # noqa: BLE001
            return {}

    def _new_bars(self) -> list[str]:
        return [t for t in self.feedback_banners() if t not in getattr(self, "_bars_before", set())]

    def _wait_for_save_outcome(self) -> None:
        """Success = the manage page reloaded (the marker planted on the
        pre-save document is gone) and rendered the form or list again.
        Refusal = no reload and refusal evidence (a new bar, a field error or a
        native `invalid` event) for a quiet window. Never a fixed sleep."""
        started = monotonic()
        state = {"value": ""}
        settled = f"{self.SUBMIT_BUTTON}, table tbody tr"

        def _outcome() -> bool:
            if self._document_replaced():
                if self.page.locator(settled).count() > 0:
                    state["value"] = "reloaded"
                    return True
                return False
            quiet = monotonic() - started >= self.REFUSAL_QUIET_WINDOW_S
            answered = len(self._responses) >= len(self._requests)
            evidence = (bool(self._invalid_this_attempt()) or bool(self._new_bars())
                        or bool(self._visible_texts(self.FIELD_ERROR)))
            if quiet and answered and evidence:
                state["value"] = "refused"
                return True
            return False

        try:
            wait_until(_outcome, timeout=self.SAVE_OUTCOME_TIMEOUT_S, poll=0.5,
                       message="save produced neither a reload nor a confirmed refusal")
        except WaitTimeoutError:
            logger.warning("save outcome did not settle; url=%s requests=%s", self.page.url, self._requests)
        finally:
            self._disarm_probe()
        self.last_reloaded = state["value"] == "reloaded"
        self.last_refused = state["value"] == "refused"
        self.last_requests = list(self._requests)
        self.last_responses = list(self._responses)
        if self.last_reloaded:
            # The post-save edit bar renders a beat after the document.
            try:
                wait_until(lambda: any(t for t in self.feedback_banners() if not t.startswith("Editing")),
                           timeout=15.0, poll=0.5)
            except WaitTimeoutError:
                pass
            self.last_invalid, self.last_new_bars = {}, []
        else:
            self.last_invalid = self._invalid_this_attempt()
            self.last_new_bars = self._new_bars()
        self.last_banners = self.feedback_banners()

    def outcome(self) -> dict:
        """Everything the last submit() showed, for assertions/attachments."""
        reloaded = bool(getattr(self, "last_reloaded", False))
        field_errors = [] if reloaded else self._visible_texts(self.FIELD_ERROR)
        fragment_errors = [] if reloaded else self._visible_texts(self.FRAGMENT_ERROR)
        native_now = {} if reloaded else self.native_invalid_messages()
        errors_by_control = {} if reloaded else self.field_errors_by_control()
        return {
            "reloaded": reloaded,
            "refused": bool(getattr(self, "last_refused", False)),
            "save_requests": list(getattr(self, "last_requests", [])),
            "save_responses": list(getattr(self, "last_responses", [])),
            "native_invalid_events": dict(getattr(self, "last_invalid", {})),
            "native_invalid_now": native_now,
            "new_bars": list(getattr(self, "last_new_bars", [])),
            "banners": list(getattr(self, "last_banners", [])),
            "field_errors": field_errors,
            "errors_by_control": errors_by_control,
            "fragment_errors": fragment_errors,
        }

    @staticmethod
    def refusal_text(outcome: dict) -> str:
        """Every refusal message in an outcome() dict, joined with " | "."""
        parts = (list(outcome["native_invalid_events"].values()) + outcome["new_bars"]
                 + outcome["field_errors"] + outcome["fragment_errors"])
        return " | ".join(dict.fromkeys(p for p in parts if p))

    @staticmethod
    def flagged_controls(outcome: dict) -> set:
        """Controls the refused attempt itself flagged: the browser's own
        `invalid` events during the submit plus visible inline errors."""
        return set(outcome["native_invalid_events"]) | set(outcome["errors_by_control"])

    @staticmethod
    def success_message(outcome: dict, expected: str = MSG_SAVED_AND_PUBLISHED) -> str:
        for text in outcome["banners"]:
            if expected in text:
                return text
        return ""

    # =====================================================================
    # Snapshot / restore (TEST_OWNED)
    # =====================================================================
    def snapshot(self, with_bytes: bool = True) -> dict:
        """Every value a test can touch, read off a FRESH open."""
        self.open_singleton()
        snap = self.all_values()
        snap["active_status"] = self.active_status_checked()
        snap["banner_file"] = self.banner_file_name()
        if with_bytes:
            data = self.banner_bytes()
            snap["banner_sha256"] = hashlib.sha256(data).hexdigest() if data else ""
            snap["banner_size"] = len(data)
        snap["row_status"] = self.singleton_row_status()
        return snap

    @staticmethod
    def text_keys() -> list[str]:
        return [f.key for f in FIELDS] + [f.key + "_ar" for f in FIELDS]

    def differences(self, baseline: dict, current: dict | None = None) -> list[str]:
        current = current or self.snapshot()
        keys = self.text_keys() + ["active_status", "banner_sha256", "row_status"]
        return [k for k in keys if norm(current.get(k)) != norm(baseline.get(k))]

    def restore(self, baseline: dict, banner_path: str = "") -> dict:
        """Writes back every value that differs from `baseline` (text EN + AR,
        Active Status, banner bytes), publishes, re-publishes through the row
        when needed, and verifies everything from a fresh open. Returns
        {"changed": [...], "remaining": [...], "final": snapshot}."""
        current = self.snapshot()
        diffs = self.differences(baseline, current)
        report = {"changed": list(diffs), "remaining": [], "final": current}
        if not diffs:
            return report
        form_diffs = [k for k in diffs if k != "row_status"]
        if form_diffs:
            self.open_singleton()
            for field in FIELDS:
                if field.key in form_diffs:
                    self.fill_field(field, baseline[field.key])
                if field.key + "_ar" in form_diffs:
                    self.fill_field(field, baseline[field.key + "_ar"], arabic=True)
            if "active_status" in form_diffs:
                self.set_active_status(bool(baseline["active_status"]))
            if "banner_sha256" in form_diffs:
                if not banner_path or not os.path.exists(banner_path):
                    raise AssertionError("banner differs from the baseline but no original bytes were captured")
                try:
                    self.upload_banner(banner_path)
                except AssertionError:
                    # Documents & Media can refuse a repeated same-name upload:
                    # retry with a uniquely named copy of the SAME bytes.
                    self.close_picker()
                    self.upload_banner(unique_copy(banner_path))
            self.submit()
            if not self.save_reloaded():
                raise AssertionError(f"restore submit was refused: {self.outcome()}")
        if self.singleton_row_status() != STATUS_PUBLISHED and "publish" in self.singleton_row_actions():
            self.run_singleton_row_action("publish", "QCTEST-130712 restore")
        final = self.snapshot()
        report["final"] = final
        report["remaining"] = self.differences(baseline, final)
        return report

    def save_reloaded(self) -> bool:
        return bool(getattr(self, "last_reloaded", False))

    # ---- Back-compat readers -------------------------------------------------
    def row_status_text(self, title: str | None = None) -> str:  # noqa: ARG002
        return self.singleton_row_status()

    def uploaded_filename(self, field_label: str = FIELD_HERO_BANNER) -> str:  # noqa: ARG002
        return self.banner_file_name()

    @staticmethod
    def manage_url(edit_entry: str | None = None) -> str:
        path = f"/web/qatar-chamber/manage-{SLUG}" + (f"?editEntry={edit_entry}" if edit_entry else "")
        return control_panel_url(path)


class AnnualReportsPublicView(AnnualReportsPage):
    """What an ANONYMOUS visitor sees on /web/qatar-chamber/annual-reports.
    Drive it on a context created with `use_auth_state=False`. Navigates with
    a plain goto (BasePage.open's session guard would log the context in).
    Every load keeps the page-record REST response the fragment itself reads
    (`/o/c/annualreportspages/...`) as network evidence (`page_record`)."""

    def open_public(self, locale: str = "en") -> "AnnualReportsPublicView":
        url = web_url(ANNUAL_REPORTS_PATH, locale=locale)
        captured: list[dict] = []

        def _on_response(response):
            try:
                if PUBLIC_PAGE_RECORD_PATH in response.url and response.request.method == "GET":
                    captured.append({"url": response.url, "status": response.status, "body": response.text()})
            except Exception:  # noqa: BLE001 — evidence only
                pass

        self.page.on("response", _on_response)
        try:
            self.last_response = self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
            clear_license_gate(self.page, url)
            dismiss_overlays(self.page, grace_ms=1500)
            try:
                self.page.locator(self.HERO_TITLE).first.wait_for(state="visible", timeout=40000)
            except Exception:  # noqa: BLE001 — the caller asserts on what rendered
                logger.warning("hero title never rendered on %s", url)
            try:
                wait_until(lambda: bool(captured), timeout=10.0, poll=0.3)
            except WaitTimeoutError:
                pass
        finally:
            self.page.remove_listener("response", _on_response)
        self.network = captured
        return self

    def http_status(self):
        return self.last_response.status if getattr(self, "last_response", None) else None

    def page_record(self) -> dict:
        """The first record of the captured `annualreportspages` response
        ({} when none was captured / parsed)."""
        for item in reversed(getattr(self, "network", [])):
            try:
                items = json.loads(item["body"]).get("items") or []
                return items[0] if items else {}
            except Exception:  # noqa: BLE001
                continue
        return {}

    def network_summary(self) -> str:
        rec = self.page_record()
        keep = {k: rec.get(k) for k in ("id", "externalReferenceCode", "activeStatus", "status", "eyebrowLabel",
                                        "pageTitle", "sectionBadge", "sectionTitle", "dateModified")}
        calls = [f"{c['status']} {c['url']}" for c in getattr(self, "network", [])]
        return f"requests: {calls}\nrecord: {json.dumps(keep, ensure_ascii=False)}"

    def _clean_text(self, selector: str) -> str:
        node = self.page.locator(selector)
        if node.count() == 0:
            return ""
        try:
            # textContent, not innerText: CSS text-transform must not alter the data compared.
            return " ".join((node.first.text_content() or "").split())
        except Exception:  # noqa: BLE001
            return ""

    def eyebrow(self) -> str:
        return self._clean_text(self.EYEBROW)

    def title(self) -> str:
        return self._clean_text(self.HERO_TITLE)

    def hero_desc(self) -> str:
        return self._clean_text(self.HERO_DESC)

    def badge(self) -> str:
        return self._clean_text(self.ARCHIVE_BADGE)

    def section_title(self) -> str:
        return self._clean_text(self.ARCHIVE_TITLE)

    def section_desc(self) -> str:
        return self._clean_text(self.ARCHIVE_DESC)

    def inner_html(self, selector: str) -> str:
        node = self.page.locator(selector)
        return node.first.inner_html() if node.count() else ""

    def rich_structure(self, selector: str) -> dict:
        """What the rich-text container actually renders: headings, lists,
        list items, anchors (href/target/clickable), bold runs, and whether
        any markup leaked as visible text."""
        node = self.page.locator(selector)
        if node.count() == 0:
            return {"present": False}
        return node.first.evaluate(
            """el => {
                const vis = n => { const r = n.getBoundingClientRect(); const s = getComputedStyle(n);
                                   return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
                const text = el.innerText || '';
                return {
                    present: true,
                    headings: [...el.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => ({tag: h.tagName.toLowerCase(),
                               text: h.innerText.trim(), visible: vis(h)})),
                    lists: [...el.querySelectorAll('ul,ol')].map(l => ({tag: l.tagName.toLowerCase(),
                            items: [...l.querySelectorAll(':scope > li')].map(li => li.innerText.trim()),
                            listStyle: getComputedStyle(l).listStyleType, visible: vis(l)})),
                    links: [...el.querySelectorAll('a')].map(a => ({text: a.innerText.trim(), href: a.getAttribute('href'),
                            target: a.getAttribute('target'), visible: vis(a),
                            clickable: (() => { const r = a.getBoundingClientRect();
                                const t = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                                return !!t && (t === a || a.contains(t)); })()})),
                    bold: [...el.querySelectorAll('strong,b')].map(b => ({text: b.innerText.trim(),
                            weight: getComputedStyle(b).fontWeight})),
                    raw_tags_visible: /<\\/?(h[1-6]|ul|ol|li|a|p|strong|b)\\b/i.test(text),
                    text: text.trim(),
                };
            }"""
        )

    def same_markup(self, selector: str, authored_html: str) -> dict:
        """Compares the container's DOM with `authored_html` parsed by the
        same browser (so only real markup differences count)."""
        node = self.page.locator(selector)
        if node.count() == 0:
            return {"equal": False, "rendered": "", "authored": ""}
        return node.first.evaluate(
            """(el, html) => {
                const t = document.createElement('template'); t.innerHTML = html;
                const n = s => s.replace(/\\s+/g, ' ').replace(/>\\s+</g, '><').trim();
                return {equal: n(el.innerHTML) === n(t.innerHTML), rendered: n(el.innerHTML), authored: n(t.innerHTML)};
            }""",
            authored_html,
        )

    def hero_banner_render(self) -> dict:
        """Where (if anywhere) the hero banner actually renders: the CSS custom
        property the fragment sets, every element / pseudo-element inside the
        hero whose computed background-image uses that URL, and <img>s."""
        hero = self.page.locator(self.HERO)
        if hero.count() == 0:
            return {"present": False}
        return hero.first.evaluate(
            """el => {
                const varUrl = (el.style.getPropertyValue('--qc-ar-hero-img-url') || '').trim();
                const m = varUrl.match(/url\\(['"]?([^'")]+)['"]?\\)/);
                const url = m ? m[1] : '';
                const file = url ? decodeURIComponent(url.split('?')[0].split('/').filter(Boolean).slice(-2, -1)[0] || '') : '';
                const uses = [];
                for (const n of [el, ...el.querySelectorAll('*')]) {
                    for (const pseudo of [null, '::before', '::after']) {
                        const bg = getComputedStyle(n, pseudo).backgroundImage || '';
                        if (bg && bg !== 'none' && (bg.includes('/documents/') || (file && bg.includes(file)))) {
                            uses.push({node: n.className || n.tagName, pseudo, bg: bg.slice(0, 300)});
                        }
                    }
                }
                const imgs = [...el.querySelectorAll('img')].map(i => ({src: i.currentSrc || i.src, loaded: i.naturalWidth > 0}));
                return {present: true, var_url: url, file, backgrounds: uses, imgs,
                        hero_bg: getComputedStyle(el).backgroundImage.slice(0, 300)};
            }"""
        )

    def resource_status(self, url: str) -> int | None:
        if not url:
            return None
        absolute = url if url.startswith("http") else web_url(url.split("?")[0]) + ("?" + url.split("?", 1)[1]
                                                                                  if "?" in url else "")
        try:
            return self.page.context.request.get(absolute).status
        except Exception:  # noqa: BLE001
            return None

    def snapshot(self) -> dict:
        return {"http": self.http_status(), "eyebrow": self.eyebrow(), "title": self.title(),
                "hero_desc": self.hero_desc(), "badge": self.badge(), "section_title": self.section_title(),
                "section_desc": self.section_desc()}

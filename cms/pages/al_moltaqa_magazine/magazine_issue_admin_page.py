"""
cms/pages/al_moltaqa_magazine/magazine_issue_admin_page.py —
MagazineIssueAdminPage (+ MagazinePublicView).

Control_Panel Page Object for the per-record **Magazine Issue** Object
Authoring surface (PBI 130710, "QC - Insights & Media - 002 - Al-Moltqa
Magazine"):
    https://qcdev.ihorizons.com/web/qatar-chamber/manage-magazine-issue
Extends `ObjectAuthoringPage` (cms/pages/components/) for the shared editorial
state machine, and follows the patterns proven on PBI 130711
(`cms/pages/publications/publication_admin_page.py`): English-pinned
navigation, a fully expanded list, entry-id-scoped rows, a pinned-account
check, a save-outcome probe and ONE guarded delete path.

REWORKED 2026-10-02 for the seven-state editorial workflow and the
re-provisioned role accounts (standards.md "Named CMS User Roles" and
"Content Editorial Workflow"). The 2026-09-22 notes this file used to carry
were all observed through the super-admin TEST_USER session and are
superseded by the live re-read below.

═══════════════════════════════════════════════════════════════════════
DELETE SAFETY — READ FIRST (a loop delete irreversibly removed 14 real
Publications records; standards.md "Destructive Operations")
  The ENTRY column of this object renders the record's externalReferenceCode
  (QCDEMO-130710-ISSUE-00N for the 7 real issues, a UUID for a new one), NOT
  the Issue Title — so a title can never be matched on the list itself.
  A record's identity is therefore the triple the SAME test captured when it
  created it: (exact QCTEST-130710- title, entry id, entry code). It is
  captured by diffing the list's entry ids before/after the create and then
  opening the ONE new row to read its Issue Title (EN) back.
  `delete_disposable_entry(entry)` refuses (returns False, logs why, never
  raises, never "picks the first") unless ALL of these hold:
    1. the title starts with `QCTEST-130710-`, the code is NOT a real
       `QCDEMO-130710-ISSUE-` code, and an id + code captured at creation
       are supplied;
    2. the record opened by its code still reads that exact Issue Title (EN)
       (re-read immediately before going to the list);
    3. the list is fully expanded (page size "all" AND rendered rows == the
       list's own total);
    4. EXACTLY ONE delete link carries the captured id, its row's Entry cell
       equals the captured code and its `data-qc-oel-label` equals the code;
       re-checked immediately before the click;
    5. the native confirm() names the code (otherwise it is dismissed).
  There is no positional, "newest", looping or substring delete here.
═══════════════════════════════════════════════════════════════════════

LIVE STATE re-read 2026-10-02 (read-only probes, `/en/` form):

  As Site Content Editor (156488) the form reads:
    textbox    "Issue Title (EN)"        required (native `required`)
    textbox    "Issue Title (AR)"        required
    textbox    "Issue Description (EN)"  textarea, NOT required
    textbox    "Issue Description (AR)"  textarea, NOT required
    textbox    "Issue Number"            NOT required
    spinbutton "Page Count" / "Article Count"   NOT required, min -2147483648
    textbox    "dd/mm/yyyy"              Issue Date (the placeholder IS the
                                         accessible name; a hidden
                                         input[type=date] ObjectField_issueDate
                                         carries `required`)
    Issue Cover Image  Select File       accept .jpg,.jpeg,.png,.webp <= 5 MB,
                                         NOT required
    PDF Attachment     Select File       accept .pdf <= 50 MB, required
    combobox   "Active Status"           a Boolean field rendered by a "Select
                                         from List" fragment with NO options and
                                         no relationship URL (live 2026-10-04,
                                         TEST_USER + Editor): empty listbox and
                                         no request on open/typing. The 7 real
                                         issues store `true`; a new issue
                                         cannot be given a value through the
                                         UI (see ACTIVE_STATUS_UNAVAILABLE).
    checkbox   "Open in New Tab"         UNTICKED on a new entry
    button     "Save as Draft" / "Publish"
               ("As an Editor, what you publish here goes live straight away.")
  As Site Content Author (156492) the same form ends in
    button     "Save as Draft" / "Submit for Review"
               ("Entries here are reviewed before they go live.")
  No Cancel/Discard control on the create form; the only "Cancel…" link
  ("Cancel and add a new entry instead") is on the EDIT form. The page's
  right-hand preview iframe (`?qcPreview=magazineissues:<id>`) shows a SAVED
  record and does not follow unsaved typing.

LIST: columns ENTRY / STATUS / LAST MODIFIED / ACTIONS;
`select[data-qc-oel-page-size]` (0 = all), `[data-qc-oel-count]` ("7 total").
Editor rows on a Published issue: Edit / Preview / Unpublish / History /
Delete. Author rows on an issue it does not own: View / Preview / History
only (`data-qc-oel-view`, `data-qc-oel-history`).

There is NO page-level "Al-Moltaqa Magazine Page" object: the Objects nav
(278 `manage-*` links) lists only `manage-magazine-issue` for this PBI
(re-confirmed 2026-10-02). The public page itself is Liferay layout plid 590
(`/al-moltaqa-magazine`) — page layout is off-limits to automation.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from time import monotonic

from cms.pages.components.object_authoring_page import (
    ObjectAuthoringPage,
    normalize_status,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.overlays import _dismiss_chatbot_launcher
from web.pages.al_moltaqa_magazine.al_moltaqa_magazine_page import AlMoltaqaMagazinePage

logger = get_logger("magazine_issue_admin_page")

SLUG = "magazine-issue"
MANAGE_PATH = f"/web/qatar-chamber/manage-{SLUG}"

# The ONLY title namespace any delete / row-action path accepts.
QCTEST_PREFIX = "QCTEST-130710-"
# Entry codes of the 7 real, shared issues — never acted on.
REAL_ENTRY_CODE_PREFIX = "QCDEMO-130710-ISSUE-"

# standards.md "Named CMS User Roles" — the pinned accounts.
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}
AUTH_FAILED_BANNER_TEXT = "Authentication failed"

# The public page's Liferay layout (read anonymously 2026-10-02).
PUBLIC_PAGE_PLID = "590"

# Field labels (live 2026-10-02). Lookups go through label_pattern(), which
# tolerates a trailing " *" / whitespace.
FIELD_ISSUE_TITLE_EN = "Issue Title (EN)"
FIELD_ISSUE_TITLE_AR = "Issue Title (AR)"
FIELD_ISSUE_DESCRIPTION_EN = "Issue Description (EN)"
FIELD_ISSUE_DESCRIPTION_AR = "Issue Description (AR)"
FIELD_ISSUE_NUMBER = "Issue Number"
FIELD_PAGE_COUNT = "Page Count"
FIELD_ARTICLE_COUNT = "Article Count"
FIELD_ISSUE_DATE_LABEL = "Issue Date"
ISSUE_DATE_PLACEHOLDER = "dd/mm/yyyy"
FIELD_ISSUE_DATE = ISSUE_DATE_PLACEHOLDER  # back-compat: the field's accessible name
FIELD_COVER_IMAGE = "Issue Cover Image"
FIELD_PDF_ATTACHMENT = "PDF Attachment"
FIELD_ACTIVE_STATUS = "Active Status"
FIELD_OPEN_IN_NEW_TAB = "Open in New Tab"

# Object field keys (the `ObjectField_<key>` form names).
REQUIRED_FIELD_KEYS = ("issueTitleEN", "issueTitleAR", "issueDate", "pdfAttachment")

SUBMIT_FOR_REVIEW_BUTTON = 'button:has-text("Submit for Review")'
OPEN_OPTIONS_MENU_BUTTON = "Open Options Menu"

# Save-feedback banner texts (editbar, English session) — same wording as the
# sibling objects (standards.md: "Saved and submitted for review.").
MSG_DRAFT_SAVED = "Draft saved."
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
# Delete feedback (editbar string read live 2026-10-04): '"<entry code>" was moved to the Recycle Bin.'
MSG_MOVED_TO_RECYCLE_BIN = '"{code}" was moved to the Recycle Bin.'
STATUS_INACTIVE = "Inactive"

# Root cause re-confirmed live 2026-10-04 as BOTH TEST_USER (20132) and the Site
# Content Editor (156488), read-only: the page's own field spec declares
# activeStatus as businessType "Boolean" (DBType Boolean, listTypeDefinitionId 0),
# but the form renders it with Liferay's "Select from List" fragment, whose input
# config carries type "boolean" and NEITHER `attributes.options` NOR
# `attributes.relationshipURL`. That fragment only fetches when a relationshipURL
# exists and otherwise filters `attributes.options` (undefined -> []), so clicking,
# the toggle button and typing ("a", "Active", "true", "Yes") produce no
# XHR/fetch request at all and an empty listbox; the dropdown never leaves d-none.
ACTIVE_STATUS_UNAVAILABLE = (
    "the 'Active Status' control on manage-magazine-issue is a Boolean object field rendered with a "
    "'Select from List' fragment that has no options and no relationship URL: the list stays empty on "
    "click, on the toggle button and while typing, and no picklist request is ever made - so it cannot be "
    "set through Object Authoring"
)


@dataclass(frozen=True)
class CreatedEntry:
    """Identity of a record the CURRENT test created: its exact QCTEST title,
    its entry id (`data-qc-oel-*` value) and its entry code (Entry cell /
    `editEntry` value)."""

    title: str
    entry_id: str
    code: str
    # The form field whose value IS `title` — Issue Title (EN) unless the case
    # under test empties that field itself (then the unique QCTEST identity
    # lives in Issue Title (AR)).
    key_field: str = FIELD_ISSUE_TITLE_EN


class MagazineIssueAdminPage(ObjectAuthoringPage):
    # ---- List / feedback locators -------------------------------------------
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    PAGE_SIZE_ALL = "0"
    ENTRY_COUNT = "[data-qc-oel-count]"
    DELETE_LINK_BY_ID = 'a[data-qc-oel-delete="{entry_id}"]'
    HISTORY_CELL = "td.qc-oel__history"
    HISTORY_ACTION = ".qc-oel__history-action"
    # The full-width message bar at the TOP of the manage page, above the
    # "<Object> entries" heading (confirmed live 2026-10-04: "Draft saved."
    # renders here after Save as Draft). Success / delete messages are read
    # from this bar, not from a corner toast.
    FEEDBACK_BANNER = "[data-qc-oel-editbar]"
    TOP_MESSAGE = FEEDBACK_BANNER
    TOP_MESSAGE_TIMEOUT_S = 15.0
    FIELD_ERROR = "[data-qc-oel-field-error]"
    AUTHORING_FORM = 'form:has(button:has-text("Save as Draft"))'
    PREVIEW_PANE = "iframe[src*='qcPreview']"
    SUBMIT_BUTTON_NAME = re.compile(
        r"^\s*(Publish|Submit for Review|Save changes|Submit for Publishing)\s*$"
    )
    SAVE_AS_DRAFT_NAME = re.compile(r"^\s*Save as Draft\s*$")
    ROW_ACTION_NAMES = (
        "approve", "reject", "resubmit", "publish", "unpublish", "archive",
        "restore", "return", "schedule", "unschedule", "history", "delete",
        "trash", "untrash", "view",
    )
    DESTRUCTIVE_ROW_ACTIONS = frozenset({"delete", "trash", "untrash"})
    # Any row action marks a rendered row (an Author has no Delete on other
    # accounts' rows, so "a delete link is visible" is not a list signal).
    ID_ATTRS = ("delete", "history", "view", "approve", "reject", "resubmit", "publish",
                "unpublish", "archive", "restore", "return", "schedule")
    LIST_LOADED = ", ".join(f"[data-qc-oel-{name}]" for name in ID_ATTRS)
    SAVE_REQUEST_PATTERN = re.compile(r"edit_info_item|/o/c/magazineissues")
    UPLOAD_REQUEST_PATTERN = re.compile(r"com_liferay_document_library_web_portlet_DLPortlet.*p_p_lifecycle=1")
    PICKER_ERROR = (".alert-danger, .alert-warning, [role='alert'], .text-danger, .invalid-feedback, "
                    ".form-feedback-item, .lfr-dropzone-error, .upload-error")
    REFUSAL_QUIET_WINDOW_S = 6.0
    SAVE_OUTCOME_TIMEOUT_S = 60.0
    BLOCKED_MESSAGE = "Please complete the required fields"
    _DOC_MARK = "__qcMagazineBeforeSave"

    DEFAULT_COVER = "cms/tests/al_moltaqa_magazine/fixtures/valid_cover_1_5mb.jpg"
    DEFAULT_PDF = "cms/tests/al_moltaqa_magazine/fixtures/valid_pdf_4mb.pdf"

    def __init__(self, page):
        super().__init__(page, SLUG)
        self.owned_entry_ids: set[str] = set()
        self.active_status_problem = ""
        self.last_uploaded_name = ""
        # Back-compat: older call sites reached the shared state machine via
        # `.authoring`; it is now this object itself.
        self.authoring = self

    # =====================================================================
    # Session / identity
    # =====================================================================
    def login_as_role(self, role: str) -> str:
        """Real login as a named role in THIS (auth-free) context. Returns
        "ok", "auth_failed" or "unknown". Never falls back to another account."""
        email, password = cms_role_credentials(role)
        login = CmsLoginPage(self.page)
        login.open_login()
        try:
            login.login(email, password)
            return "ok"
        except Exception:  # noqa: BLE001 — classified below, never swallowed as success
            # CmsLoginPage waits for the Control Menu, which an Author never
            # renders; Liferay's ThemeDisplay is the sign-in signal instead.
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
            return "auth_failed" if AUTH_FAILED_BANNER_TEXT in body else "unknown"

    def signed_in_user(self) -> tuple[str, str]:
        """(userId, full name) from Liferay's ThemeDisplay — ("", "") signed out."""
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']"""
        )
        return info[0], info[1]

    # =====================================================================
    # Navigation (interface locale pinned to English)
    # =====================================================================
    def open_new_entry_form(self, locale: str | None = "en") -> "MagazineIssueAdminPage":
        super().open_new_entry_form(locale=locale)
        try:
            self.page.get_by_role("button", name=self.SUBMIT_BUTTON_NAME).first.wait_for(timeout=15000)
        except Exception:  # noqa: BLE001 — callers read submit_button_label() themselves
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entries_list(self, locale: str | None = "en") -> "MagazineIssueAdminPage":
        """Entries list with ALL rows shown (never the list's Search box)."""
        self._locale = locale
        self.open(self._manage_url(locale=locale))
        self.wait_for(self.LIST_LOADED, first=True, timeout=35000)
        self._show_all_rows()
        return self

    def open_list(self) -> "MagazineIssueAdminPage":
        return self.open_entries_list()

    def _show_all_rows(self) -> None:
        # Live 2026-10-02: the pager (and its page-size select) is HIDDEN while
        # the list fits one page; every row is then already rendered, which
        # is_list_fully_expanded() still verifies against the list's own total.
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() == 0 or not select.first.is_visible():
            return
        if select.input_value() != self.PAGE_SIZE_ALL:
            select.select_option(self.PAGE_SIZE_ALL)
        total = self.total_entry_count()
        try:
            wait_until(lambda: total is None or self.rendered_row_count() >= total,
                       timeout=10.0, poll=0.3, message="entries list did not expand to show every row")
        except WaitTimeoutError:
            logger.warning("page-size ALL did not settle to %s rows", total)
        _dismiss_chatbot_launcher(self.page)

    def total_entry_count(self) -> int | None:
        counter = self.page.locator(self.ENTRY_COUNT)
        if counter.count() == 0:
            return None
        match = re.search(r"(\d+)\s*total|of\s*(\d+)", counter.first.inner_text())
        if not match:
            return None
        return int(match.group(1) or match.group(2))

    def rendered_row_count(self) -> int:
        return self.page.locator(f"{self.ENTRIES_TABLE_ROW}:has({self.LIST_LOADED})").count()

    def is_list_fully_expanded(self) -> bool:
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.first.is_visible() and select.input_value() != self.PAGE_SIZE_ALL:
            return False
        total = self.total_entry_count()
        return total is not None and self.rendered_row_count() == total

    # =====================================================================
    # Rows — entry id / code, never title substring, never position
    # =====================================================================
    _ROWS_JS = """(attrs) => [...document.querySelectorAll('table tbody tr')]
        .map(r => {
            const tds = r.querySelectorAll('td');
            let id = '';
            for (const a of attrs) { const n = r.querySelector('[data-qc-oel-' + a + ']');
                                     if (n) { id = n.getAttribute('data-qc-oel-' + a); break; } }
            const del = r.querySelector('a[data-qc-oel-delete]');
            return {
                entry_id: id,
                code: tds[0] ? tds[0].innerText.trim() : '',
                status: tds[1] ? tds[1].innerText.trim() : '',
                modified: tds[2] ? tds[2].innerText.trim() : '',
                delete_id: del ? del.getAttribute('data-qc-oel-delete') : '',
                label: del ? (del.getAttribute('data-qc-oel-label') || '') : '',
            };
        })
        .filter(r => r.entry_id)"""

    def list_rows(self) -> list[dict]:
        """[{entry_id, code, status, modified, delete_id, label}] of every row on
        the current list (read-only inventory)."""
        return self.page.evaluate(self._ROWS_JS, list(self.ID_ATTRS))

    def snapshot_ids(self) -> set[str]:
        """Every entry id on the fully expanded list (read-only)."""
        self.open_entries_list()
        if not self.is_list_fully_expanded():
            raise AssertionError("the Magazine Issue list did not expand to show every row; "
                                 "cannot snapshot entry ids safely")
        return {r["entry_id"] for r in self.list_rows()}

    def issue_title_on_form(self) -> str:
        return self.field_value(FIELD_ISSUE_TITLE_EN)

    def identify_created(self, title: str, ids_before: set[str],
                         key_field: str = FIELD_ISSUE_TITLE_EN) -> CreatedEntry | None:
        """The ONE row whose id was NOT in `ids_before` and whose own form reads
        `key_field` == `title` exactly. None when zero or several match.
        Identity is proven by reading the record back, never by position."""
        if not title.startswith(QCTEST_PREFIX):
            raise ValueError(f"{title!r} is not in the {QCTEST_PREFIX} namespace")
        self.open_entries_list()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before
                 and not r["code"].startswith(REAL_ENTRY_CODE_PREFIX)]
        matches = []
        for row in fresh:
            for attempt in (1, 2):  # one retry: a slow editEntry load must not orphan our record
                try:
                    self.open_entry_by_code(row["code"], locale="en")
                    if self.field_value(key_field) == title:
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — a row that cannot be read is not ours
                    logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            logger.warning("identify_created(%r): %s new matching rows (new rows %s)", title, len(matches), fresh)
            return None
        return self.adopt(CreatedEntry(title=title, entry_id=matches[0]["entry_id"], code=matches[0]["code"],
                                       key_field=key_field))

    def adopt(self, entry: CreatedEntry) -> CreatedEntry:
        if (not entry.title.startswith(QCTEST_PREFIX) or not entry.entry_id or not entry.code
                or entry.code.startswith(REAL_ENTRY_CODE_PREFIX)):
            raise ValueError(f"refusing to adopt {entry}: not a captured {QCTEST_PREFIX} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def _row(self, entry: CreatedEntry):
        return self.page.locator(", ".join(
            f'{self.ENTRIES_TABLE_ROW}:has([data-qc-oel-{a}="{entry.entry_id}"])' for a in self.ID_ATTRS
        ))

    def row_present(self, entry: CreatedEntry) -> bool:
        return self._row(entry).count() >= 1

    def row_code(self, entry: CreatedEntry) -> str:
        row = self._row(entry)
        return row.first.locator("td").first.inner_text().strip() if row.count() else ""

    def row_status(self, entry: CreatedEntry) -> str:
        """Normalized status of the captured row ("" when gone)."""
        row = self._row(entry)
        if row.count() == 0:
            return ""
        raw = row.first.locator("td").nth(1).inner_text()
        if " ".join(raw.split()).casefold() == STATUS_INACTIVE.casefold():
            return STATUS_INACTIVE
        return normalize_status(raw)

    def row_actions(self, entry: CreatedEntry) -> list[str]:
        row = self._row(entry).first
        return [n for n in self.ROW_ACTION_NAMES if row.locator(f"[data-qc-oel-{n}]").count() > 0]

    def row_has_edit_link(self, entry: CreatedEntry) -> bool:
        return self._row(entry).first.get_by_role("link", name="Edit").count() > 0

    def row_preview_href(self, entry: CreatedEntry) -> str:
        link = self._row(entry).first.get_by_role("link", name="Preview")
        href = link.get_attribute("href") if link.count() else ""
        return control_panel_url(href) if href else ""

    def open_entry(self, entry: CreatedEntry) -> "MagazineIssueAdminPage":
        """Opens the captured record's edit form by its code (English-pinned)."""
        self.open_entry_by_code(entry.code, locale="en")
        _dismiss_chatbot_launcher(self.page)
        return self

    def run_row_action(self, entry: CreatedEntry, action: str, comment: str = "") -> list[str]:
        """Clicks one id-scoped row action, accepting every native dialog it
        raises (a confirm() may chain into a prompt()); returns the dialog
        messages. Refuses destructive actions and records this test did not
        capture."""
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(f"run_row_action refuses {action!r}; use delete_disposable_entry()")
        if action != "history":
            if not entry.title.startswith(QCTEST_PREFIX):
                raise ValueError(f"run_row_action refuses {entry}: not a {QCTEST_PREFIX} record")
            if entry.entry_id not in self.owned_entry_ids:
                raise ValueError(f"run_row_action refuses {entry}: id was not captured at creation by this test")
            if self.row_code(entry) != entry.code:
                raise ValueError(f"run_row_action refuses {entry}: the row now reads {self.row_code(entry)!r}")
        control = self._row(entry).first.locator(f"[data-qc-oel-{action}]")
        if control.count() == 0:
            raise AssertionError(f"row {entry} offers no {action!r} action; offered: {self.row_actions(entry)}")
        messages: list[str] = []

        def _accept(dialog):
            messages.append(dialog.message)
            try:
                dialog.accept(comment)
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

    def history(self, entry: CreatedEntry) -> list[dict]:
        """Expands the captured row's History trail (`ul.qc-oel__history-list`,
        inside the table — not a modal) -> [{action, who, when, comment, text}]."""
        self.open_entries_list()
        self._row(entry).first.locator("[data-qc-oel-history]").first.click(force=True)
        cell = self._row(entry).first.locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        try:
            wait_until(lambda: cell.count() == 1 and "Loading" not in cell.inner_text(),
                       timeout=15.0, poll=0.5, message="history did not load")
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
                "text": item.inner_text().strip(),
            })
        return result

    # =====================================================================
    # DELETE — the single guarded path (see module docstring)
    # =====================================================================
    def _delete_preconditions(self, entry: CreatedEntry) -> str:
        """"" when every list-side guard holds on the CURRENT list, else the reason."""
        if not self.is_list_fully_expanded():
            return (f"list is not fully expanded ({self.rendered_row_count()} rendered of "
                    f"{self.total_entry_count()} total) — the target could be off-page")
        links = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
        if links.count() != 1:
            return f"{links.count()} delete links carry id {entry.entry_id} (need exactly 1)"
        rows = [r for r in self.list_rows() if r["delete_id"] == entry.entry_id]
        if len(rows) != 1:
            return f"{len(rows)} rows carry delete id {entry.entry_id}"
        row = rows[0]
        if row["code"] != entry.code:
            return f"row of id {entry.entry_id} shows code {row['code']!r}, not the captured {entry.code!r}"
        if row["label"] != entry.code:
            return f"delete link of id {entry.entry_id} is labelled {row['label']!r}, not {entry.code!r}"
        return ""

    def delete_disposable_entry(self, entry: CreatedEntry, await_message: bool = False) -> bool:
        """Deletes exactly the captured record (title + id + code) or refuses.
        Never raises; returns True only when the row is confirmed gone.
        `await_message=True` waits (bounded) for the top-of-page message after
        the delete and keeps it in `last_delete_banners` (+ a screenshot)."""
        try:
            if (not isinstance(entry.title, str) or not entry.title.startswith(QCTEST_PREFIX)
                    or not entry.entry_id or not entry.code or entry.code.startswith(REAL_ENTRY_CODE_PREFIX)):
                logger.error("DELETE REFUSED: %r is not a captured %s record", entry, QCTEST_PREFIX)
                return False
            # Guard 2: the record behind the code still carries the exact title.
            self.open_entry(entry)
            live_title = self.field_value(entry.key_field)
            if live_title != entry.title:
                logger.error("DELETE REFUSED for %r: the record now reads Issue Title %r", entry, live_title)
                return False
            self.open_entries_list()
            reason = self._delete_preconditions(entry)
            if reason:
                logger.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            reason = self._delete_preconditions(entry)  # re-check immediately before the click
            if reason:
                logger.error("DELETE REFUSED for %r on re-check: %s", entry, reason)
                return False
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                if entry.code in dialog.message or entry.title in dialog.message:
                    dialog.accept()
                else:
                    dialog.dismiss()

            self.page.on("dialog", _on_dialog)
            try:
                link.click(force=True)
                try:
                    link.wait_for(state="detached", timeout=20000)
                except Exception:  # noqa: BLE001 — verified below from a fresh list
                    pass
            finally:
                self.page.remove_listener("dialog", _on_dialog)
            self.last_delete_dialogs = dialogs
            try:
                self.last_delete_banners = (
                    self.top_messages(expected=MSG_MOVED_TO_RECYCLE_BIN.format(code=entry.code),
                                      evidence="after delete") if await_message
                    else self.feedback_banners())
            except Exception:  # noqa: BLE001
                self.last_delete_banners = []
            if not any(entry.code in m or entry.title in m for m in dialogs):
                logger.error("DELETE NOT CONFIRMED for %r: no confirm() named it: %s", entry, dialogs)
                return False
            self.open_entries_list()
            gone = self.is_list_fully_expanded() and not any(
                r["entry_id"] == entry.entry_id for r in self.list_rows()
            )
            if not gone:
                logger.error("delete of %r not confirmed on a fully expanded list", entry)
            else:
                logger.info("deleted %r; dialogs=%s", entry, dialogs)
            return gone
        except Exception as exc:  # noqa: BLE001 — teardown helper, never raises
            logger.error("delete of %r failed: %r — leftover QCTEST data may remain", entry, exc)
            return False

    def find_entry_by_title(self, title: str) -> CreatedEntry | None:
        """Back-compat lookup for callers that did not capture an id at
        creation (the Web-side module): opens every NON-real row and returns
        the ONE whose Issue Title (EN) equals `title` exactly — None for zero
        or several. Identity is read back from each record, never positional."""
        if not title.startswith("QCTEST-"):
            return None
        self.open_entries_list()
        candidates = [r for r in self.list_rows() if not r["code"].startswith(REAL_ENTRY_CODE_PREFIX)]
        matches = []
        for row in candidates:
            try:
                self.open_entry_by_code(row["code"], locale="en")
                if self.issue_title_on_form() == title:
                    matches.append(row)
            except Exception:  # noqa: BLE001
                continue
        if len(matches) != 1:
            return None
        return CreatedEntry(title=title, entry_id=matches[0]["entry_id"], code=matches[0]["code"])

    def delete_entry_by_title(self, title: str, expected_id: str | None = None) -> bool:
        """Back-compat delete. Resolves the ONE record whose Issue Title (EN)
        reads `title` exactly (QCTEST- titles only), checks it against
        `expected_id` when given, then runs the guarded delete. Never raises."""
        try:
            entry = self.find_entry_by_title(title)
            if entry is None or (expected_id and entry.entry_id != expected_id):
                logger.error("DELETE REFUSED: no single verified record titled %r (id %s)", title, expected_id)
                return False
            if not title.startswith(QCTEST_PREFIX):
                # Legacy-format title (Web-side module): same guards, own namespace check.
                return self._legacy_delete(entry)
            self.owned_entry_ids.add(entry.entry_id)
            return self.delete_disposable_entry(entry)
        except Exception as exc:  # noqa: BLE001
            logger.error("delete_entry_by_title(%r) failed: %r", title, exc)
            return False

    def _legacy_delete(self, entry: CreatedEntry) -> bool:
        """Guarded delete for a verified title — restricted to the
        QCTEST-130710- namespace (a legacy `QCTEST-<tc> …` title is refused)
        and carrying the same guards as delete_disposable_entry: exact title
        re-read from the record behind the captured code, full-list + single
        id/code/label check, re-checked immediately before the click, and a
        confirm() that must name the code. Never raises."""
        try:
            if (not isinstance(entry.title, str) or not entry.title.startswith(QCTEST_PREFIX)
                    or not entry.entry_id or not entry.code or entry.code.startswith(REAL_ENTRY_CODE_PREFIX)):
                logger.error("LEGACY DELETE REFUSED: %r is not a captured %s record", entry, QCTEST_PREFIX)
                return False
            self.open_entry(entry)
            live_title = self.field_value(entry.key_field)
            if live_title != entry.title:
                logger.error("LEGACY DELETE REFUSED for %r: the record now reads %r", entry, live_title)
                return False
            self.open_entries_list()
            reason = self._delete_preconditions(entry)
            if reason:
                logger.error("LEGACY DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            reason = self._delete_preconditions(entry)  # re-check immediately before the click
            if reason:
                logger.error("LEGACY DELETE REFUSED for %r on re-check: %s", entry, reason)
                return False
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                dialog.accept() if entry.code in dialog.message else dialog.dismiss()

            self.page.on("dialog", _on_dialog)
            try:
                link.click(force=True)
                try:
                    link.wait_for(state="detached", timeout=20000)
                except Exception:  # noqa: BLE001
                    pass
            finally:
                self.page.remove_listener("dialog", _on_dialog)
            if not any(entry.code in m for m in dialogs):
                logger.error("LEGACY DELETE NOT CONFIRMED for %r: no confirm() named it: %s", entry, dialogs)
                return False
            self.open_entries_list()
            return self.is_list_fully_expanded() and not any(
                r["entry_id"] == entry.entry_id for r in self.list_rows())
        except Exception as exc:  # noqa: BLE001 — teardown helper, never raises
            logger.error("legacy delete of %r failed: %r", entry, exc)
            return False

    _M1 = ("inherited substring/position row targeting is disabled on manage-magazine-issue "
           "(standards.md Destructive Operations) - use the CreatedEntry-scoped method")

    def delete_all_entries_by_title(self, title: str, max_rows: int = 10) -> int:  # noqa: ARG002
        raise NotImplementedError("looping deletes are forbidden (2026-09-28 incident)")

    def newest_entry_code(self) -> str:
        raise NotImplementedError("positional targeting is forbidden (standards.md Destructive Operations)")

    def delete_entry_by_code(self, entry_code: str) -> bool:  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": delete_disposable_entry(entry)")

    def _row_locator(self, title_or_code: str):  # noqa: ARG002
        raise NotImplementedError(self._M1)

    def _run_row_action(self, title_or_code: str, action: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, action)")

    # =====================================================================
    # Legacy title-based queries (verified read-back, used by the Web module)
    # =====================================================================
    def status_for(self, title: str) -> str:
        entry = self.find_entry_by_title(title)
        if entry is None:
            return ""
        self.open_entries_list()
        return self.row_status(entry)

    def row_status_text(self, title: str) -> str:
        return self.status_for(title)

    def row_visible(self, title: str) -> bool:
        return self.find_entry_by_title(title) is not None

    def row_preview_url(self, title: str) -> str:
        entry = self.find_entry_by_title(title)
        if entry is None:
            return ""
        self.open_entries_list()
        return self.row_preview_href(entry)

    def open_entry_by_edit_link(self, title: str) -> "MagazineIssueAdminPage":
        entry = self.find_entry_by_title(title)
        if entry is None:
            raise AssertionError(f"no single Magazine Issue reads Issue Title (EN) == {title!r}")
        return self.open_entry(entry)

    # =====================================================================
    # Fields
    # =====================================================================
    def _form(self):
        return self.page.locator(self.AUTHORING_FORM).first

    def _textbox(self, label: str):
        return self.page.get_by_role("textbox", name=self.label_pattern(label))

    def _spinbutton(self, label: str):
        return self.page.get_by_role("spinbutton", name=self.label_pattern(label))

    def fill_text(self, field_label: str, value: str) -> "MagazineIssueAdminPage":
        self._textbox(field_label).fill(value)
        return self

    def field_value(self, field_label: str) -> str:
        return self._textbox(field_label).input_value()

    def fill_number(self, field_label: str, value: str) -> "MagazineIssueAdminPage":
        self._spinbutton(field_label).fill(value)
        return self

    def number_field_value(self, field_label: str) -> str:
        return self._spinbutton(field_label).input_value()

    def type_into_number(self, field_label: str, text: str) -> "MagazineIssueAdminPage":
        """Types `text` key by key (clearing first) the way a user would —
        `fill()` refuses non-numeric text on input[type=number]."""
        box = self._spinbutton(field_label)
        box.click()
        box.press("Control+A")
        box.press("Delete")
        self.page.keyboard.type(text, delay=20)
        return self

    def _date_box(self):
        return self._form().get_by_placeholder(ISSUE_DATE_PLACEHOLDER)

    def set_issue_date(self, value: str) -> "MagazineIssueAdminPage":
        """`value` dd/mm/yyyy, e.g. "01/09/2026"."""
        box = self._date_box()
        box.click()
        box.press("Control+A")
        box.press("Delete")
        self.page.keyboard.type(value, delay=20)
        box.press("Tab")
        return self

    def issue_date_value(self) -> str:
        return self._date_box().input_value()

    def stored_issue_date(self) -> str:
        """The hidden input[type=date] value (yyyy-mm-dd) the form submits."""
        return self._form().locator('input[name="ObjectField_issueDate"]').input_value()

    def date_field_message(self) -> str:
        """Inline message rendered inside the Issue Date field block ("" when none)."""
        text = self._date_box().evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 6 && c && !/Issue Date/.test(c.innerText); i++) c = c.parentElement;
                       return c ? c.innerText : ''; }"""
        )
        lines = [ln.strip() for ln in text.split("\n")]
        noise = {"Issue Date", "?", "‹", "›", "Today", "Clear", ""}
        return " ".join(ln for ln in lines if ln not in noise and not re.fullmatch(r"[\d\s]+|[A-Z][a-z]{1,2}", ln))

    def set_open_in_new_tab(self, checked: bool) -> "MagazineIssueAdminPage":
        box = self.page.get_by_role("checkbox", name=self.label_pattern(FIELD_OPEN_IN_NEW_TAB))
        box.check() if checked else box.uncheck()
        return self

    def is_open_in_new_tab_checked(self) -> bool:
        return self.page.get_by_role("checkbox", name=self.label_pattern(FIELD_OPEN_IN_NEW_TAB)).is_checked()

    # ---- Active Status (a "select from list" on this object) ----------------
    def _active_status_combobox(self):
        return self.page.get_by_role("combobox", name=self.label_pattern(FIELD_ACTIVE_STATUS))

    ACTIVE_STATUS_QUERIES = ("a", "Active", "true")
    # The fragment debounces typing by 1000 ms before it filters.
    ACTIVE_STATUS_WAIT_S = 3.0

    def _active_status_option_nodes(self, listbox_id: str):
        return self.page.locator(f'[id="{listbox_id}"] li, [id="{listbox_id}"] [role="option"]')

    def active_status_options(self, keep_open: bool = False) -> list[str]:
        """Options the Active Status list offers: opens it with the toggle
        button, then TYPES each of ACTIVE_STATUS_QUERIES into the combobox
        (past the fragment's 1 s debounce) until something is listed. Every
        XHR/fetch answered meanwhile is kept in `active_status_probe` with the
        options and the query that produced them. `keep_open=True` leaves the
        list open on that query so the caller can click an option.
        (Live 2026-10-04: no options and no request, for every query.)"""
        combo = self._active_status_combobox()
        listbox_id = combo.get_attribute("aria-controls")
        options = self._active_status_option_nodes(listbox_id)
        responses: list[str] = []

        def _on_response(response):
            try:
                if response.request.resource_type in ("xhr", "fetch"):
                    responses.append(f"{response.request.method} {response.status} {response.url[:200]}")
            except Exception:  # noqa: BLE001 — diagnostics only
                pass

        def _listed() -> list[str]:
            return [t.strip() for t in options.all_inner_texts() if t.strip()]

        def _await_options() -> None:
            try:
                wait_until(lambda: bool(_listed()), timeout=self.ACTIVE_STATUS_WAIT_S, poll=0.25)
            except WaitTimeoutError:
                pass

        query, texts = "", []
        self.page.on("response", _on_response)
        try:
            self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
            _await_options()
            texts = _listed()
            for candidate in ([] if texts else self.ACTIVE_STATUS_QUERIES):
                combo.fill("")
                combo.press_sequentially(candidate, delay=40)
                _await_options()
                texts = _listed()
                if texts:
                    query = candidate
                    break
        finally:
            self.page.remove_listener("response", _on_response)
            self.active_status_probe = {"options": texts, "query": query,
                                        "queries_tried": list(self.ACTIVE_STATUS_QUERIES), "responses": responses}
            if not keep_open or not texts:
                try:
                    combo.fill("")
                    self.page.keyboard.press("Escape")
                except Exception:  # noqa: BLE001
                    pass
        return texts

    def set_active_status(self, active) -> "MagazineIssueAdminPage":
        """Ticks/sets Active Status. Accepts True/False or an option label.
        Raises AssertionError(ACTIVE_STATUS_UNAVAILABLE + this attempt's probe)
        when the list offers no matching option — never fakes a value."""
        options = self.active_status_options(keep_open=True)
        if isinstance(active, str):
            wanted = [active]
        else:
            wanted = ["True", "Yes", "Active", "true"] if active else ["False", "No", "Inactive", "false"]
        choice = next((o for o in options if o in wanted), None)
        probe = getattr(self, "active_status_probe", {})
        if choice is None:
            try:
                self.page.keyboard.press("Escape")
            except Exception:  # noqa: BLE001
                pass
            raise AssertionError(
                f"{ACTIVE_STATUS_UNAVAILABLE}; this attempt: offered options {options}, queries typed "
                f"{probe.get('queries_tried')}, XHR/fetch responses {probe.get('responses') or 'none'}"
            )
        listbox_id = self._active_status_combobox().get_attribute("aria-controls")
        self._active_status_option_nodes(listbox_id).filter(
            has_text=re.compile(rf"^\s*{re.escape(choice)}\s*$")).first.click()
        stored = self._form().locator('input[name="ObjectField_activeStatus"]').input_value()
        if not stored:
            raise AssertionError(f"picked Active Status {choice!r} but the form's ObjectField_activeStatus "
                                 f"value stayed empty")
        return self

    def try_set_active_status(self, active: bool = True) -> bool:
        """Best effort: records the reason in `active_status_problem` instead
        of raising, so a create can go on and the CMS-side steps still run."""
        try:
            self.set_active_status(active)
            self.active_status_problem = ""
            return True
        except Exception as exc:  # noqa: BLE001 — surfaced by the caller's precondition check
            self.active_status_problem = str(exc)[:400]
            try:
                self.page.keyboard.press("Escape")
            except Exception:  # noqa: BLE001
                pass
            return False

    def active_status_value(self) -> str:
        """What the Active Status control shows on the open form."""
        return self._active_status_combobox().input_value()

    def active_status_stored(self) -> str:
        """The stored value the form loaded (hidden ObjectField_activeStatus,
        falling back to the combobox text): "true" for the 7 real issues."""
        hidden = self._form().locator('input[name="ObjectField_activeStatus"]')
        value = hidden.input_value() if hidden.count() else ""
        return value or self.active_status_value()

    # ---- File uploads --------------------------------------------------------
    @staticmethod
    def _unique_upload_copy(file_path: str, stem: str | None = None) -> str:
        """Documents & Media de-duplicates same-named uploads and eventually
        refuses them (seen on the sibling Publication object), so every upload
        sends a temporary, uniquely named copy of the same bytes. NOTE: every
        upload leaves a file in the site's Documents & Media library; this
        framework never deletes D&M files."""
        import shutil
        import tempfile
        import uuid

        base, ext = os.path.splitext(os.path.basename(file_path))
        folder = os.path.join(tempfile.gettempdir(), "qctest_uploads_130710")
        os.makedirs(folder, exist_ok=True)
        target = os.path.join(folder, f"{stem or base}-{uuid.uuid4().hex[:8]}{ext}")
        shutil.copyfile(file_path, target)
        return target

    @staticmethod
    def _remove_temp(path: str) -> None:
        try:
            os.remove(path)
        except OSError:
            logger.warning("could not remove temp upload copy %s", path)

    def _open_picker(self, field_label: str) -> None:
        hidden = self.page.get_by_role("textbox", name=f"{field_label} Select File")
        hidden.locator("xpath=..").get_by_role("button", name="Select File").click()

    def upload_file(self, field_label: str, file_path: str, stem: str | None = None) -> "MagazineIssueAdminPage":
        """Uploads a uniquely named copy of `file_path` through the field's
        picker, waits for the D&M upload response, then clicks Add until the
        picker closes. `last_uploaded_name` is the name actually sent."""
        upload_path = self._unique_upload_copy(file_path, stem)
        self.last_uploaded_name = os.path.basename(upload_path)
        self._open_picker(field_label)
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        try:
            with self.page.expect_response(
                lambda r: r.request.method == "POST" and bool(self.UPLOAD_REQUEST_PATTERN.search(r.url)),
                timeout=45000,
            ) as upload:
                frame.locator('input[type="file"]').set_input_files(upload_path)
        finally:
            self._remove_temp(upload_path)
        try:
            body = upload.value.text()
        except Exception:  # noqa: BLE001
            body = ""
        if '"success":false' in body.replace(" ", ""):
            raise AssertionError(f"Documents & Media refused the upload of {self.last_uploaded_name} "
                                 f"(HTTP {upload.value.status}, body {body[:160]!r})")
        add = frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT)
        modal = self.page.locator(self.UPLOAD_MODAL_IFRAME)

        def _added() -> bool:
            if modal.count() == 0:
                return True
            try:
                add.click(timeout=3000)
            except Exception:  # noqa: BLE001 — retried until the picker closes
                pass
            return modal.count() == 0

        wait_until(_added, timeout=30.0, poll=1.5, message=f"the {field_label} picker did not close after Add")
        return self

    def attempt_upload(self, field_label: str, file_path: str, response_timeout_ms: int = 20000) -> dict:
        """Tries an upload and reports only hard evidence: {file, status,
        body, success (True/False/None), errors: [picker error texts],
        add_clicked, field_value}. The picker is closed afterwards."""
        upload_path = self._unique_upload_copy(file_path)
        result = {"file": os.path.basename(upload_path), "status": None, "body": "", "success": None,
                  "errors": [], "add_clicked": False}
        self._open_picker(field_label)
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
        except Exception:  # noqa: BLE001 — no upload POST answered: success stays None
            pass
        finally:
            self._remove_temp(upload_path)
        errors = frame.locator(self.PICKER_ERROR)
        try:
            wait_until(lambda: errors.count() > 0 and any(t.strip() for t in errors.all_inner_texts()),
                       timeout=5.0, poll=0.5)
        except WaitTimeoutError:
            pass
        try:
            result["errors"] = [t.strip() for t in errors.all_inner_texts() if t.strip()]
        except Exception:  # noqa: BLE001
            result["errors"] = []
        if result["success"] is True and not result["errors"]:
            try:
                frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click(timeout=10000)
                result["add_clicked"] = True
                try:
                    wait_until(lambda: self.page.locator(self.UPLOAD_MODAL_IFRAME).count() == 0
                               or (errors.count() > 0 and any(t.strip() for t in errors.all_inner_texts())),
                               timeout=10.0, poll=0.5)
                except WaitTimeoutError:
                    pass
                if self.page.locator(self.UPLOAD_MODAL_IFRAME).count():
                    result["errors"] = [t.strip() for t in errors.all_inner_texts() if t.strip()]
            except Exception:  # noqa: BLE001
                pass
        if self.page.locator(self.UPLOAD_MODAL_IFRAME).count():
            self.page.keyboard.press("Escape")
            try:
                self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
            except Exception:  # noqa: BLE001
                logger.warning("upload picker did not close on Escape")
        try:
            result["field_value"] = self.uploaded_filename(field_label)
            result["field_errors"] = self.field_errors()
        except Exception:  # noqa: BLE001
            result["field_value"] = ""
        self.last_upload_attempt = result
        return result

    def upload_file_expect_rejected(self, field_label: str, file_path: str) -> bool:
        """Back-compat: True when the upload did not end up attached to the field."""
        result = self.attempt_upload(field_label, file_path)
        return result["file"] not in (result.get("field_value") or "")

    def uploaded_filename(self, field_label: str) -> str:
        """Name shown in the field's own filename readout (a NEW selection)."""
        return self._textbox(field_label).inner_text().strip()

    def stored_file_name(self, field_label: str) -> str:
        """Persisted file of a reopened record, from the field's own
        "Current file: <name> — pick a file to replace it" placeholder."""
        placeholder = self.current_file_placeholder(field_label)
        match = re.match(r"Current file:\s*(.+?)\s+—", placeholder)
        return match.group(1) if match else ""

    # =====================================================================
    # Form inspection
    # =====================================================================
    def submit_button_label(self) -> str:
        button = self.page.get_by_role("button", name=self.SUBMIT_BUTTON_NAME)
        return button.first.inner_text().strip() if button.count() else ""

    def form_action_labels(self) -> list[str]:
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

    def cancel_controls(self) -> list[str]:
        """Visible Cancel / Discard / Close controls on the authoring form."""
        return self._form().evaluate(
            """(f) => [...f.querySelectorAll('a, button')]
                .filter(e => e.offsetParent !== null)
                .map(e => (e.innerText || e.getAttribute('aria-label') || '').trim())
                .filter(t => /cancel|discard/i.test(t))"""
        )

    def click_cancel_control(self) -> None:
        self._form().locator("a, button").filter(has_text=re.compile(r"cancel|discard", re.I)).first.click()

    def required_markers(self) -> dict:
        """{object field key: True when its label shows a required marker
        (asterisk / reference mark / aria-required)} for the required fields."""
        return self._form().evaluate(
            """(f, keys) => Object.fromEntries(keys.map(k => {
                const input = f.querySelector('[name="ObjectField_' + k + '"]');
                let box = input; for (let i = 0; i < 6 && box && !box.querySelector('label'); i++) box = box.parentElement;
                const label = box ? box.querySelector('label') : null;
                const marked = !!label && (/\\*/.test(label.innerText) ||
                    !!label.querySelector('.reference-mark, [class*=required], abbr, svg[class*=asterisk]'));
                return [k, marked];
            }))""",
            list(REQUIRED_FIELD_KEYS),
        )

    def is_save_as_draft_enabled(self) -> bool:
        button = self.page.get_by_role("button", name=self.SAVE_AS_DRAFT_NAME)
        return button.count() > 0 and button.first.is_enabled()

    def preview_pane_text(self, timeout_ms: int = 15000) -> str:
        """Body text of the page's own preview iframe ("" when none)."""
        if self.page.locator(self.PREVIEW_PANE).count() == 0:
            return ""
        try:
            return self.page.frame_locator(self.PREVIEW_PANE).first.locator("body").inner_text(timeout=timeout_ms)
        except Exception:  # noqa: BLE001
            return ""

    def page_body_text(self) -> str:
        return self.page.locator("body").inner_text()

    # =====================================================================
    # Save / submit (with an outcome probe — a request alone does not mean saved)
    # =====================================================================
    def save_as_draft(self) -> "MagazineIssueAdminPage":
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SAVE_AS_DRAFT_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def publish(self) -> "MagazineIssueAdminPage":
        """Clicks the ROLE-DEPENDENT submit button (Editor: "Publish", Author:
        "Submit for Review"). Asserts nothing — the caller pins the account."""
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SUBMIT_BUTTON_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def submit_for_review(self) -> "MagazineIssueAdminPage":
        return self.publish()

    def submit_blocked(self) -> bool:
        """The last save/submit did NOT go through and showed refusal evidence."""
        if self.save_redirected():
            return False
        return self.save_refused() or self.BLOCKED_MESSAGE in self.page_body_text()

    def _arm_save_probe(self) -> None:
        self._save_requests: list[str] = []
        self._save_responses: list[int] = []
        self._navigated = False
        self._bars_before = set(self._refusal_banners())
        self._field_errors_before = set(self._safe_field_errors())

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
                window.__qcMagInvalid = [];
                window.__qcMagInvalidMsg = {{}};
                if (!window.__qcMagInvalidHooked) {{
                    window.__qcMagInvalidHooked = true;
                    document.addEventListener('invalid', (e) => {{
                        const t = e.target; const k = t.name || t.id || '';
                        window.__qcMagInvalid.push(k); window.__qcMagInvalidMsg[k] = t.validationMessage;
                    }}, true);
                }}
            }}"""
        )

    def _refusal_banners(self) -> list[str]:
        try:
            return [t for t in self.feedback_banners() if "not saved" in t or self.BLOCKED_MESSAGE in t]
        except Exception:  # noqa: BLE001 - mid-navigation
            return []

    def _safe_field_errors(self) -> list[str]:
        try:
            return self.field_errors()
        except Exception:  # noqa: BLE001 - mid-navigation
            return []

    def _new_field_error(self) -> bool:
        return any(t not in getattr(self, "_field_errors_before", set()) for t in self._safe_field_errors())

    def _new_refusal_bar(self) -> bool:
        return any(t not in getattr(self, "_bars_before", set()) for t in self._refusal_banners())

    def _disarm_save_probe(self) -> None:
        on_request, on_navigation, on_response = getattr(self, "_probe_handlers", (None, None, None))
        for event, handler in (("request", on_request), ("framenavigated", on_navigation),
                               ("response", on_response)):
            if handler is not None:
                try:
                    self.page.remove_listener(event, handler)
                except Exception:  # noqa: BLE001
                    pass
        self._probe_handlers = (None, None, None)

    def _document_replaced(self) -> bool:
        try:
            return not self.page.evaluate(f"() => Boolean(window.{self._DOC_MARK})")
        except Exception:  # noqa: BLE001 — mid-navigation
            return False

    def _invalid_fields_this_attempt(self) -> list[str]:
        try:
            return list(self.page.evaluate("() => window.__qcMagInvalid || []"))
        except Exception:  # noqa: BLE001
            return []

    def native_validation_messages(self) -> dict:
        try:
            return dict(self.page.evaluate("() => window.__qcMagInvalidMsg || {}"))
        except Exception:  # noqa: BLE001
            return {}

    def _refusal_shown(self) -> bool:
        try:
            return (bool(self._invalid_fields_this_attempt())
                    or self.page.locator(self.FIELD_ERROR).count() > 0
                    or self.refusal_bar_text() != ""
                    or self.BLOCKED_MESSAGE in self.page_body_text())
        except Exception:  # noqa: BLE001
            return False

    def _wait_for_save_outcome(self) -> None:
        """Success = the manage page reloaded (document replaced) and rendered
        the list or a form. Refusal = refusal evidence from THIS attempt and
        no accepted save + navigation, for a quiet window."""
        started = monotonic()
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
            settled_window = (answered and not self._navigated
                              and monotonic() - started >= self.REFUSAL_QUIET_WINDOW_S)
            if settled_window and not accepted and self._refusal_shown():
                state["value"] = "refused"
                return True
            if settled_window and accepted and (self._new_refusal_bar() or self._new_field_error()):
                state["value"] = "refused"
                return True
            return False

        try:
            wait_until(_outcome, timeout=self.SAVE_OUTCOME_TIMEOUT_S, poll=0.5,
                       message="save produced neither a reload nor a confirmed refusal")
        except WaitTimeoutError:
            logger.warning("save outcome did not settle; url=%s requests=%s responses=%s",
                           self.page.url, self._save_requests, self._save_responses)
        finally:
            self._disarm_save_probe()
        self.last_save_reloaded = state["value"] == "reloaded"
        self.last_save_refused = state["value"] == "refused"
        self.last_save_requests = list(self._save_requests)
        self.last_save_responses = list(self._save_responses)
        self.last_invalid_fields = [] if self.last_save_reloaded else self._invalid_fields_this_attempt()
        self.last_native_messages = {} if self.last_save_reloaded else self.native_validation_messages()

    def save_redirected(self) -> bool:
        return bool(getattr(self, "last_save_reloaded", False))

    def save_refused(self) -> bool:
        return bool(getattr(self, "last_save_refused", False))

    def refusal_evidence(self) -> dict:
        """Everything the last refused attempt showed, for assertions/attachments."""
        return {
            "invalid_fields": list(getattr(self, "last_invalid_fields", [])),
            "native_messages": dict(getattr(self, "last_native_messages", {})),
            "field_errors": self._safe_field_errors(),
            "banners": self._refusal_banners(),
            "blocked_message": self.BLOCKED_MESSAGE in self.page_body_text(),
        }

    def feedback_banners(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.FEEDBACK_BANNER).all_inner_texts() if t.strip()]

    def top_messages(self, timeout: float | None = None, evidence: str = "top-of-page message",
                     expected: str | None = None) -> list[str]:
        """Waits (bounded) for the message bar at the TOP of the page to show a
        success/delete message (see `success_banners`) and returns its text(s);
        [] when none appeared. Attaches a screenshot of the page as it stood,
        as evidence either way."""
        texts = self.success_banners(self.TOP_MESSAGE_TIMEOUT_S if timeout is None else timeout, expected)
        try:
            self.screenshot(evidence)
        except Exception:  # noqa: BLE001 — evidence only
            pass
        return texts

    def _non_refusal_banners(self) -> list[str]:
        return [t for t in self.feedback_banners()
                if not t.startswith("Editing") and "not saved" not in t and self.BLOCKED_MESSAGE not in t]

    def success_banners(self, timeout: float = 15.0, expected: str | None = None) -> list[str]:
        """Post-save banners that are neither the "Editing …" bar nor a refusal
        ("…not saved…" / BLOCKED_MESSAGE). With `expected`, waits for a banner
        CONTAINING that text (the caller asserts on it); returns whatever
        non-refusal banners are shown when the wait ends."""
        def _done() -> bool:
            texts = self._non_refusal_banners()
            return any(expected in t for t in texts) if expected else bool(texts)
        try:
            wait_until(_done, timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass
        return self._non_refusal_banners()

    @staticmethod
    def has_message(banners: list[str], expected: str) -> bool:
        return any(expected in text for text in banners)

    def field_errors(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.FIELD_ERROR).all_inner_texts() if t.strip()]

    def refusal_bar_text(self) -> str:
        for text in self.feedback_banners():
            if "not saved" in text or self.BLOCKED_MESSAGE in text:
                return text
        return ""

    def editing_bar_text(self) -> str:
        for text in self.feedback_banners():
            if text.startswith("Editing"):
                return text
        return ""

    # =====================================================================
    # Data
    # =====================================================================
    def fill_issue(self, data: dict) -> "MagazineIssueAdminPage":
        """Fills whichever keys `data` carries (None/absent = untouched):
        title, title_ar, description, description_ar, issue_number,
        page_count, article_count, issue_date (dd/mm/yyyy), cover_path,
        pdf_path, open_in_new_tab, active_status."""
        for key, label in (("title", FIELD_ISSUE_TITLE_EN), ("title_ar", FIELD_ISSUE_TITLE_AR),
                           ("description", FIELD_ISSUE_DESCRIPTION_EN),
                           ("description_ar", FIELD_ISSUE_DESCRIPTION_AR),
                           ("issue_number", FIELD_ISSUE_NUMBER)):
            if data.get(key) is not None:
                self.fill_text(label, data[key])
        if data.get("page_count") is not None:
            self.fill_number(FIELD_PAGE_COUNT, str(data["page_count"]))
        if data.get("article_count") is not None:
            self.fill_number(FIELD_ARTICLE_COUNT, str(data["article_count"]))
        if data.get("issue_date"):
            self.set_issue_date(data["issue_date"])
        if data.get("cover_path"):
            self.upload_file(FIELD_COVER_IMAGE, data["cover_path"], data.get("cover_stem"))
            data["cover_uploaded_as"] = self.last_uploaded_name
        if data.get("pdf_path"):
            self.upload_file(FIELD_PDF_ATTACHMENT, data["pdf_path"], data.get("pdf_stem"))
            data["pdf_uploaded_as"] = self.last_uploaded_name
        if data.get("open_in_new_tab") is not None:
            self.set_open_in_new_tab(bool(data["open_in_new_tab"]))
        if data.get("active_status") is not None:
            self.try_set_active_status(bool(data["active_status"]))
        return self

    def read_issue(self) -> dict:
        return {
            "title": self.field_value(FIELD_ISSUE_TITLE_EN),
            "title_ar": self.field_value(FIELD_ISSUE_TITLE_AR),
            "description": self.field_value(FIELD_ISSUE_DESCRIPTION_EN),
            "description_ar": self.field_value(FIELD_ISSUE_DESCRIPTION_AR),
            "issue_number": self.field_value(FIELD_ISSUE_NUMBER),
            "page_count": self.number_field_value(FIELD_PAGE_COUNT),
            "article_count": self.number_field_value(FIELD_ARTICLE_COUNT),
            "issue_date": self.issue_date_value(),
            "open_in_new_tab": self.is_open_in_new_tab_checked(),
            "active_status": self.active_status_stored(),
        }

    @classmethod
    def default_data(cls, title: str, **overrides) -> dict:
        if not title.startswith(QCTEST_PREFIX):
            raise ValueError(f"disposable titles must start with {QCTEST_PREFIX}: {title!r}")
        data = {
            "title": title,
            "title_ar": f"{title} عدد المجلة",
            "description": f"{title} disposable automated-test issue description.",
            "description_ar": "وصف عدد تجريبي تم إنشاؤه تلقائيًا.",
            "issue_number": "QCTEST Issue #1",
            "page_count": "10",
            "article_count": "5",
            "issue_date": "01/01/2026",
            "cover_path": cls.DEFAULT_COVER,
            "pdf_path": cls.DEFAULT_PDF,
            "active_status": True,
        }
        data.update(overrides)
        return data

    def create_disposable_entry(self, prefix: str, **overrides) -> dict:
        """Back-compat (Web-side module): opens the create form and fills a
        `QCTEST-<prefix> Magazine Issue` entry with legacy FIELD_* override
        keys (does NOT save)."""
        legacy = {FIELD_ISSUE_TITLE_EN: "title", FIELD_ISSUE_TITLE_AR: "title_ar",
                  FIELD_ISSUE_DESCRIPTION_EN: "description", FIELD_ISSUE_DESCRIPTION_AR: "description_ar",
                  FIELD_ISSUE_NUMBER: "issue_number", "Issue Title (EN) ": "title", "Issue Title (AR) ": "title_ar"}
        mapped = {legacy.get(k, k): v for k, v in overrides.items()}
        if mapped.pop("skip_cover", False):
            mapped["cover_path"] = None
        if mapped.pop("skip_pdf", False):
            mapped["pdf_path"] = None
        if mapped.pop("skip_status", False):
            mapped["active_status"] = None
        title = mapped.pop("title", f"QCTEST-{prefix} Magazine Issue")
        data = {
            "title": title, "title_ar": f"QCTEST-{prefix} عدد المجلة",
            "description": f"QCTEST-{prefix} disposable automated-test issue description.",
            "description_ar": f"QCTEST-{prefix} وصف عدد تجريبي تم إنشاؤه تلقائيًا.",
            "issue_number": f"QCTEST-{prefix}", "cover_path": self.DEFAULT_COVER,
            "pdf_path": self.DEFAULT_PDF, "active_status": True,
        }
        data.update(mapped)
        self.open_new_entry_form()
        self.fill_issue(data)
        data[FIELD_ISSUE_TITLE_EN] = title
        return data

    def publish_disposable_entry(self, prefix: str, **overrides) -> dict:
        data = self.create_disposable_entry(prefix, **overrides)
        self.publish()
        return data

    @staticmethod
    def manage_url(edit_entry: str | None = None) -> str:
        return control_panel_url(MANAGE_PATH + (f"?editEntry={edit_entry}" if edit_entry else ""))


class MagazinePublicView(AlMoltaqaMagazinePage):
    """Read-only extras over the public Page Object, used by the Control_Panel
    module's delivery-surface checks (image resolvability, Read Online /
    Download behaviour, page-level presence of a title). Always driven from a
    fresh LOGGED-OUT context."""

    def find_title(self, title: str) -> dict:
        """Where `title` appears: {"latest": bool, "archive_index": int}. The
        archive is searched through the page's own search box."""
        latest = self.page.locator(self.LATEST_TITLE)
        in_latest = latest.count() > 0 and latest.first.inner_text().strip() == title
        self.search(title)
        index = self.card_index(title)
        return {"latest": in_latest, "archive_index": index}

    def latest_cover_img(self) -> dict:
        return self._img_state(self.page.locator(".qc-ma-latest img").first)

    def card_cover_img(self, index: int) -> dict:
        return self._img_state(self.page.locator(self.CARD).nth(index).locator("img").first)

    @staticmethod
    def _img_state(img) -> dict:
        if img.count() == 0:
            return {"present": False, "src": "", "loaded": False}
        try:
            img.scroll_into_view_if_needed(timeout=5000)
        except Exception:  # noqa: BLE001
            pass
        try:
            wait_until(lambda: img.evaluate("i => i.complete"), timeout=15.0, poll=0.5)
        except WaitTimeoutError:
            pass
        state = img.evaluate("i => ({src: i.currentSrc || i.src || '', w: i.naturalWidth || 0})")
        return {"present": True, "src": state["src"], "loaded": state["w"] > 0}

    def latest_badge_texts(self) -> list:
        return [t.strip() for t in self.latest_badges()]

    def latest_snapshot(self) -> dict:
        return {
            "title": self.latest_title_text().strip(),
            "badges": self.latest_badge_texts(),
            "description": self.latest_desc_text().strip(),
            "meta": " ".join(self.latest_meta_text().split()),
            "actions": [t.strip() for t in self.latest_action_labels()],
        }

    def card_titles_unfiltered(self) -> list:
        self.clear_search()
        return self.card_titles()

    def link_info(self, link) -> dict:
        return {"href": link.get_attribute("href") or "", "target": link.get_attribute("target") or ""}

    def read_online_opens(self, link) -> dict:
        """Clicks a Read Online link. Returns {"new_tab": bool, "url": str,
        "original_url": str}: a popup means a new tab; otherwise the same tab
        navigated."""
        original = self.page.url
        try:
            with self.page.context.expect_page(timeout=10000) as popup_info:
                link.click()
            popup = popup_info.value
            try:
                popup.wait_for_load_state("domcontentloaded", timeout=20000)
            except Exception:  # noqa: BLE001
                pass
            url = popup.url
            still_here = self.page.url == original
            popup.close()
            return {"new_tab": True, "url": url, "original_url": original, "original_kept": still_here}
        except Exception:  # noqa: BLE001 — no popup: same-tab navigation (or nothing)
            try:
                self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:  # noqa: BLE001
                pass
            return {"new_tab": False, "url": self.page.url, "original_url": original, "original_kept": False}

    def download_via(self, link) -> str:
        """Clicks a Download PDF link and returns the suggested file name."""
        with self.page.expect_download(timeout=30000) as info:
            link.click()
        return info.value.suggested_filename

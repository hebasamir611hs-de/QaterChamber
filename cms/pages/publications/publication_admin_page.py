"""
cms/pages/publications/publication_admin_page.py — PublicationAdminPage.

Control_Panel Page Object for the per-record **Publication** Object Authoring
surface (PBI 130711, "QC - Insights & Media - 003 - Publications"):
    https://qcdev.ihorizons.com/web/qatar-chamber/manage-publication
Extends `ObjectAuthoringPage` (cms/pages/components/) for the shared editorial
state machine and follows the patterns proven on PBI 130699
(`cms/pages/laws_regulations/laws_regulations_admin_page.py`): English-pinned
navigation, a fully expanded list, exact-title / id-scoped rows, a pinned
account check and ONE guarded delete path.

═══════════════════════════════════════════════════════════════════════
DELETE SAFETY — READ FIRST (this object lost 14 real records to a loop
delete on 2026-09-27/28; standards.md "Destructive Operations")
  Two delete entry points exist and BOTH go through `_guarded_delete()`:
    - `delete_disposable_entry(entry)` — preferred; takes the CreatedEntry
      (title + entry id) the SAME test captured when it created the record.
    - `delete_entry_by_title(title)` — kept for existing callers; resolves
      the id itself from an exact-title match.
  `_guarded_delete()` refuses (returns False, logs why, never raises, never
  "picks the first") unless ALL of these hold, re-checked immediately before
  the click:
    1. the title starts with `QCTEST-130711-` (review B1; old-format
       "QCTEST-1439xx" rows belong to an external writer) AND an entry id
       captured at creation is supplied (delete_entry_by_title raises without one);
    2. the list is fully expanded (page size "all" AND rendered rows == the
       list's own total), so the target cannot be hiding off-page;
    3. EXACTLY ONE row's Entry cell equals the title exactly (not substring);
    4. that row's delete link carries the expected entry id AND its
       `data-qc-oel-label` equals the title exactly;
    5. the native confirm() names the title (otherwise it is dismissed and the
       delete reports False).
  There is no positional, "newest", looping or substring delete in this
  class, and no `newest_entry_code()` use.
═══════════════════════════════════════════════════════════════════════

LIVE STATE, re-read 2026-09-30 as Site Content Editor (userId 156488) on the
`/en/` form (read-only ARIA snapshot; supersedes the 2026-09-22 notes):

    textbox    "Publication Title"                  (required; NO trailing
                                                      space any more)
    textbox    "Publication Title — العربية *"       (#qc-ar-publicationTitle)
    textbox    "Publication Description"
    textbox    "Publication Description — العربية"   (#qc-ar-publicationDescription)
    combobox   "Publication Type"   picklist, options exactly: Report,
                                     Bulletin, Study, Research Paper, Guides,
                                     White Paper, Manuals, Brochure
    textbox    "dd/mm/yyyy"          Publication Date (the placeholder IS the
                                     accessible name; scoped to the authoring
                                     form because the list's filter panel has
                                     the same placeholder)
    button     "Select File" x2      Cover Image (.jpg/.jpeg/.png <= 5 MB),
                                     File Attachment (.jpg/.jpeg/.png/.doc/
                                     .docx/.xlsx/.pdf <= 5 MB)
    spinbutton "Page Count"
    checkbox   "Active Status"       TICKED by default on a new entry here
    spinbutton "Download Count" / "View Count"
    button     "Save as Draft" / "Publish"   (Editor: "As an Editor, what you
                                     publish here goes live straight away.")

  - **The "Publication Status" combobox no longer exists** (it did on
    2026-09-22). Its job is now the workflow state itself, so
    `set_publication_status()` raises with that explanation instead of
    silently doing nothing.
  - "Publication Type" is a FIXED picklist (Content-Admin-Guide §12). There is
    no "Manage Publication Types" object in the Object Authoring navigation —
    every case built on that surface stays skipped as a requirements conflict.
  - The submit button's label depends on the signed-in role (Publish for a
    self-approving Editor, Submit for Review for an Author, Save changes on a
    record that is off the website). `SUBMIT_BUTTON_NAME` matches all of them.

LIST (live 2026-09-30): columns ENTRY / STATUS / LAST MODIFIED / ACTIONS;
`select[data-qc-oel-page-size]` (0 = all) and `[data-qc-oel-count]`
("17 total"). Row actions carry `data-qc-oel-<action>="<entryId>"`; the
delete link also carries `data-qc-oel-label="<title>"`. At probe time EVERY
row on this object was a leftover test record (QCTEST-*, UUID-titled, or a
"<script>…" injection probe) — no real publication remained.

SAVE FEEDBACK is the `[data-qc-oel-editbar]` banner rendered after the
post-save reload. A save counts as refused only with refusal evidence from
this attempt AND no accepted save request/navigation (see
`_wait_for_save_outcome`) — a request on its own does not mean saved.

SESSION GUARD: core/web/session_guard can re-authenticate a dropped session.
Role-pinned tests re-read `signed_in_user()` before each lifecycle assertion.
"""

from __future__ import annotations

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

logger = get_logger("publication_admin_page")

SLUG = "publication"
MANAGE_PATH = f"/web/qatar-chamber/manage-{SLUG}"

# The ONLY title namespace any delete / row-action path accepts (review B1,
# 2026-10-01). Old-format "QCTEST-1439xx …" rows on this object belong to an
# unknown external writer and must never be touched — hence the PBI-scoped
# prefix, not bare "QCTEST-".
QCTEST_PREFIX = "QCTEST-130711-"

# standards.md "Named CMS User Roles" — the pinned accounts.
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}
AUTH_FAILED_BANNER_TEXT = "Authentication failed"

# Field labels (live 2026-09-30). Lookups go through label_pattern(), which
# tolerates a trailing " *" / whitespace, so these stay correct if the
# required-marker rendering changes again.
FIELD_PUBLICATION_TITLE_EN = "Publication Title"
FIELD_PUBLICATION_TITLE_AR = "Publication Title — العربية"
FIELD_PUBLICATION_DESCRIPTION_EN = "Publication Description"
FIELD_PUBLICATION_DESCRIPTION_AR = "Publication Description — العربية"
FIELD_PUBLICATION_TYPE = "Publication Type"
FIELD_COVER_IMAGE = "Cover Image"
FIELD_FILE_ATTACHMENT = "File Attachment"
FIELD_PAGE_COUNT = "Page Count"
FIELD_ACTIVE_STATUS = "Active Status"
FIELD_DOWNLOAD_COUNT = "Download Count"
FIELD_VIEW_COUNT = "View Count"
# Removed from the form (see module docstring); kept so imports keep resolving.
FIELD_PUBLICATION_STATUS = "Publication Status"

PUBLICATION_DATE_PLACEHOLDER = "dd/mm/yyyy"
SUBMIT_FOR_REVIEW_BUTTON = 'button:has-text("Submit for Review")'
OPEN_OPTIONS_MENU_BUTTON = "Open Options Menu"

PUBLICATION_TYPE_OPTIONS = [
    "Report", "Bulletin", "Study", "Research Paper",
    "Guides", "White Paper", "Manuals", "Brochure",
]

# Save-feedback banner texts (editbar, English session).
MSG_DRAFT_SAVED = "Draft saved."
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
STATUS_INACTIVE = "Inactive"


@dataclass(frozen=True)
class CreatedEntry:
    """Identity of a record the CURRENT test created — what the preferred
    delete path accepts. `entry_id` is the row's `data-qc-oel-delete` id."""

    title: str
    entry_id: str


class PublicationAdminPage(ObjectAuthoringPage):
    # ---- List / feedback locators -------------------------------------------
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    PAGE_SIZE_ALL = "0"
    ENTRY_COUNT = "[data-qc-oel-count]"
    ROW_BY_ID = 'table tbody tr:has(a[data-qc-oel-delete="{entry_id}"])'
    DELETE_LINK_BY_ID = 'a[data-qc-oel-delete="{entry_id}"]'
    HISTORY_CELL = "td.qc-oel__history"
    HISTORY_ACTION = ".qc-oel__history-action"
    FEEDBACK_BANNER = "[data-qc-oel-editbar]"
    FIELD_ERROR = "[data-qc-oel-field-error]"
    INVALID_FIELD = "[data-qc-oel-invalid]"
    AUTHORING_FORM = 'form:has(button:has-text("Save as Draft"))'
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
    # Any row action marks a rendered row — an Author has no Delete on other
    # editors' rows, so "a delete link is visible" is NOT a list-loaded signal.
    LIST_LOADED = ", ".join(
        f"a[data-qc-oel-{name}]"
        for name in ("delete", "history", "approve", "reject", "resubmit", "publish",
                     "unpublish", "archive", "restore", "return", "schedule")
    )
    # Requests that WRITE a record: the add form's Liferay action and the edit
    # path's call to the Object's REST collection.
    SAVE_REQUEST_PATTERN = re.compile(r"edit_info_item|/o/c/publications")
    REFUSAL_QUIET_WINDOW_S = 6.0
    SAVE_OUTCOME_TIMEOUT_S = 60.0
    _DOC_MARK = "__qcPublicationBeforeSave"

    def __init__(self, page):
        super().__init__(page, SLUG)
        # Entry ids THIS page object captured at creation (capture_created /
        # adopt). run_row_action() acts only on these (review m2).
        self.owned_entry_ids: set[str] = set()
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
    def open_new_entry_form(self, locale: str | None = "en") -> "PublicationAdminPage":
        super().open_new_entry_form(locale=locale)
        # Hydration swaps "Submit for Publishing" -> the role's real label and
        # ticks Active Status; wait for the real label before anyone reads it.
        try:
            self.page.get_by_role("button", name=self.SUBMIT_BUTTON_NAME).first.wait_for(timeout=15000)
        except Exception:  # noqa: BLE001 — callers read submit_button_label() themselves
            pass
        return self

    def open_new_form(self) -> "PublicationAdminPage":
        return self.open_new_entry_form()

    def open_entries_list(self, locale: str | None = "en") -> "PublicationAdminPage":
        """Entries list with ALL rows shown. Never uses the list's Search box
        (filtered rows' actions were dead on the sibling Law Regulation list)."""
        self._locale = locale
        self.open(self._manage_url(locale=locale))
        self.wait_for(self.LIST_LOADED, first=True, timeout=35000)
        self._show_all_rows()
        return self

    def open_list(self) -> "PublicationAdminPage":
        return self.open_entries_list()

    def _show_all_rows(self) -> None:
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() == 0:
            return
        if select.input_value() != self.PAGE_SIZE_ALL:
            select.select_option(self.PAGE_SIZE_ALL)
        total = self.total_entry_count()
        try:
            wait_until(
                lambda: total is None or self.rendered_row_count() >= total,
                timeout=10.0, poll=0.3,
                message="entries list did not expand to show every row",
            )
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
        """True only when the page-size select is on ALL and the list renders
        EVERY entry (rendered rows == the list's own total)."""
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.input_value() != self.PAGE_SIZE_ALL:
            return False
        total = self.total_entry_count()
        return total is not None and self.rendered_row_count() == total

    def is_list_readable(self) -> bool:
        return self.has_entries()

    # =====================================================================
    # Rows — exact title / entry id, never substring, never position
    # =====================================================================
    def rows_with_exact_title(self, title: str) -> list[dict]:
        """Every row whose Entry cell equals `title` EXACTLY on the current
        (expanded) list: [{entry_id, title, label, status, modified}]. A row
        without a delete link (Author on someone else's row) reports its id
        from any other row action."""
        return self.page.evaluate(
            """(t) => [...document.querySelectorAll('table tbody tr')]
                .filter(r => r.querySelector('td') && r.querySelector('td').innerText.trim() === t)
                .map(r => {
                    const tds = r.querySelectorAll('td');
                    const del = r.querySelector('a[data-qc-oel-delete]');
                    const hist = r.querySelector('[data-qc-oel-history]');
                    return {
                        entry_id: del ? del.getAttribute('data-qc-oel-delete')
                                      : (hist ? hist.getAttribute('data-qc-oel-history') : ''),
                        title: tds[0].innerText.trim(),
                        label: del ? (del.getAttribute('data-qc-oel-label') || '') : '',
                        status: tds[1] ? tds[1].innerText.trim() : '',
                        modified: tds[2] ? tds[2].innerText.trim() : '',
                    };
                })
                .filter(r => r.entry_id)""",
            title,
        )

    def entry_titles(self) -> list[str]:
        """Entry-column text of every row on the current list (read-only)."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll('table tbody tr')]
                .filter(r => r.querySelector('[data-qc-oel-history], a[data-qc-oel-delete]'))
                .map(r => r.querySelector('td').innerText.trim())"""
        )

    def list_rows(self) -> list[dict]:
        """[{entry_id, title, status, modified}] of every row (read-only
        inventory — e.g. the leftover-QCTEST report)."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll('table tbody tr')]
                .filter(r => r.querySelector('[data-qc-oel-history], a[data-qc-oel-delete]'))
                .map(r => {
                    const tds = r.querySelectorAll('td');
                    const del = r.querySelector('a[data-qc-oel-delete]');
                    const hist = r.querySelector('[data-qc-oel-history]');
                    return {
                        entry_id: del ? del.getAttribute('data-qc-oel-delete') : (hist ? hist.getAttribute('data-qc-oel-history') : ''),
                        title: tds[0].innerText.trim(),
                        status: tds[1] ? tds[1].innerText.trim() : '',
                        modified: tds[2] ? tds[2].innerText.trim() : '',
                    };
                })"""
        )

    def _single_exact_row(self, title: str) -> dict | None:
        rows = self.rows_with_exact_title(title)
        return rows[0] if len(rows) == 1 else None

    def capture_created(self, title: str) -> CreatedEntry:
        """Identity of the record just created with `title`. Call ONLY after
        checking that no row with this title existed before creation."""
        self.open_entries_list()
        rows = self.rows_with_exact_title(title)
        if len(rows) != 1:
            raise AssertionError(
                f"expected exactly one row titled {title!r} after creating it, found {len(rows)}: {rows}"
            )
        return self.adopt(CreatedEntry(title=title, entry_id=rows[0]["entry_id"]))

    def adopt(self, entry: CreatedEntry) -> CreatedEntry:
        """Marks `entry` (captured at creation by the SAME test) as one this
        page object may run row actions on. Refuses other namespaces."""
        if not entry.title.startswith(QCTEST_PREFIX) or not entry.entry_id:
            raise ValueError(f"refusing to adopt {entry}: not a captured {QCTEST_PREFIX} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def _row(self, entry: CreatedEntry):
        return self.page.locator(
            f'{self.ENTRIES_TABLE_ROW}:has([data-qc-oel-delete="{entry.entry_id}"]), '
            f'{self.ENTRIES_TABLE_ROW}:has([data-qc-oel-history="{entry.entry_id}"])'
        )

    def row_present(self, entry: CreatedEntry) -> bool:
        return self._row(entry).count() >= 1

    def row_title(self, entry: CreatedEntry) -> str:
        row = self._row(entry)
        return row.first.locator("td").first.inner_text().strip() if row.count() else ""

    def row_status(self, entry: CreatedEntry) -> str:
        """Normalized status of the captured row ("" when gone). Returns
        STATUS_INACTIVE for an "Inactive" badge (Active Status unticked)."""
        row = self._row(entry)
        if row.count() == 0:
            return ""
        raw = row.first.locator("td").nth(1).inner_text()
        if " ".join(raw.split()).casefold() == STATUS_INACTIVE.casefold():
            return STATUS_INACTIVE
        return normalize_status(raw)

    def row_modified(self, entry: CreatedEntry) -> str:
        row = self._row(entry)
        return row.first.locator("td").nth(2).inner_text().strip() if row.count() else ""

    def row_actions(self, entry: CreatedEntry) -> list[str]:
        row = self._row(entry).first
        return [n for n in self.ROW_ACTION_NAMES if row.locator(f"[data-qc-oel-{n}]").count() > 0]

    def row_has_edit_link(self, entry: CreatedEntry) -> bool:
        """Live 2026-09-30: an Author's row for a record owned by someone else
        renders NO Edit link (the record cannot be opened for editing)."""
        return self._row(entry).first.get_by_role("link", name="Edit").count() > 0

    def row_preview_href(self, entry: CreatedEntry) -> str:
        link = self._row(entry).first.get_by_role("link", name="Preview")
        href = link.get_attribute("href") if link.count() else ""
        return control_panel_url(href) if href else ""

    def open_entry(self, entry: CreatedEntry) -> "PublicationAdminPage":
        """Opens the captured record for edit through ITS row's Edit link
        (English-pinned) and remembers its entry code for reopen()."""
        self.open_entries_list()
        row = self._row(entry)
        if row.count() == 0:
            raise AssertionError(f"row for {entry} is not on the list")
        href = row.first.get_by_role("link", name="Edit").first.get_attribute("href") or ""
        match = re.search(r"editEntry=([^&#]+)", href)
        if not match:
            raise AssertionError(f"row for {entry} has no Edit link with an editEntry code")
        self.open_entry_by_code(match.group(1), locale="en")
        return self

    def run_row_action(self, entry: CreatedEntry, action: str, comment: str = "") -> list[str]:
        """Clicks one id-scoped row action, accepting every native dialog it
        raises; returns the dialog messages. Refuses destructive actions."""
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(f"run_row_action refuses {action!r}; use delete_disposable_entry()")
        if action != "history":
            if not entry.title.startswith(QCTEST_PREFIX):
                raise ValueError(f"run_row_action refuses {entry}: title is not in the {QCTEST_PREFIX} namespace")
            if entry.entry_id not in self.owned_entry_ids:
                raise ValueError(f"run_row_action refuses {entry}: id was not captured at creation by this test")
            if self.row_title(entry) not in (entry.title,):
                raise ValueError(f"run_row_action refuses {entry}: the row now reads {self.row_title(entry)!r}")
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
        return messages

    def history(self, entry: CreatedEntry) -> list[dict]:
        """Expands the captured row's History trail (`ul.qc-oel__history-list`,
        inside the table — not a modal) -> [{action, who, when, comment}]."""
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
    def _delete_preconditions(self, title: str, expected_id: str | None) -> tuple[str | None, str]:
        """Returns (entry_id, "") when every guard holds, else (None, reason)."""
        if not isinstance(title, str) or not title.startswith(QCTEST_PREFIX):
            return None, f"title {title!r} is not in the {QCTEST_PREFIX} namespace"
        if not expected_id:
            return None, "no entry id captured at creation"
        if not self.is_list_fully_expanded():
            return None, (
                f"list is not fully expanded ({self.rendered_row_count()} rendered of "
                f"{self.total_entry_count()} total) — the target could be off-page"
            )
        rows = self.rows_with_exact_title(title)
        if len(rows) != 1:
            return None, f"{len(rows)} rows carry the exact title {title!r} (need exactly 1): {rows}"
        row = rows[0]
        if expected_id is not None and row["entry_id"] != expected_id:
            return None, f"the row titled {title!r} is id {row['entry_id']}, not the captured id {expected_id}"
        if row["label"] != title:
            return None, f"delete link of id {row['entry_id']} is labelled {row['label']!r}, not {title!r}"
        return row["entry_id"], ""

    def _guarded_delete(self, title: str, expected_id: str | None = None) -> bool:
        try:
            if not isinstance(title, str) or not title.startswith(QCTEST_PREFIX):
                logger.error("DELETE REFUSED: title %r is not in the %s namespace", title, QCTEST_PREFIX)
                return False
            self.open_entries_list()
            entry_id, reason = self._delete_preconditions(title, expected_id)
            if entry_id is None:
                logger.error("DELETE REFUSED for %r: %s", title, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry_id))
            if link.count() != 1:
                logger.error("DELETE REFUSED for %r: %s delete links carry id %s", title, link.count(), entry_id)
                return False
            # Re-check immediately before the click.
            recheck_id, reason = self._delete_preconditions(title, entry_id)
            if recheck_id != entry_id:
                logger.error("DELETE REFUSED for %r on re-check: %s", title, reason)
                return False
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                if title in dialog.message:
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
            # Review m1: no confirm() naming the title = no delete we vouch for.
            if not any(title in m for m in dialogs):
                logger.error("DELETE NOT CONFIRMED for %r: no confirm() named it: %s", title, dialogs)
                return False
            self.open_entries_list()
            gone = self.is_list_fully_expanded() and not any(
                r["entry_id"] == entry_id for r in self.rows_with_exact_title(title)
            )
            if not gone:
                logger.error("delete of %r (id %s) not confirmed on a fully expanded list", title, entry_id)
            else:
                logger.info("deleted %r (id %s); dialogs=%s", title, entry_id, dialogs)
            return gone
        except Exception as exc:  # noqa: BLE001 — teardown helper, never raises
            logger.error("delete of %r failed: %r — leftover QCTEST data may remain", title, exc)
            return False

    def delete_disposable_entry(self, entry: CreatedEntry) -> bool:
        """Preferred delete: exactly the captured row (id + exact title)."""
        return self._guarded_delete(entry.title, expected_id=entry.entry_id)

    def delete_entry_by_title(self, title: str, expected_id: str | None = None) -> bool:
        """Review B1 (2026-10-01): a title alone is never enough. `expected_id`
        — the entry id captured when the SAME test created the record — is
        REQUIRED (raises otherwise); then the full `_guarded_delete()` checks
        apply (QCTEST-130711- prefix, fully expanded list, exactly one
        exact-title row with that id and a matching delete label)."""
        if not expected_id:
            raise ValueError(
                f"delete_entry_by_title({title!r}) refused: an entry id captured at creation is required "
                "(use delete_disposable_entry(CreatedEntry))"
            )
        return self._guarded_delete(title, expected_id=expected_id)

    def delete_all_entries_by_title(self, title: str, max_rows: int = 10) -> int:  # noqa: ARG002
        raise NotImplementedError("looping deletes are forbidden on manage-publication (2026-09-28 incident)")

    def newest_entry_code(self) -> str:
        raise NotImplementedError("positional targeting is forbidden (standards.md Destructive Operations)")

    # ---- Review M1 (2026-10-01): every inherited ObjectAuthoringPage row
    # method that resolves its row by a :has-text SUBSTRING (_row_locator,
    # .first) or by position is disabled here. Use the CreatedEntry-scoped
    # equivalents: run_row_action(entry, action), history(entry),
    # delete_disposable_entry(entry).
    _M1 = ("inherited substring/position row targeting is disabled on manage-publication "
           "(review M1) - use the CreatedEntry-scoped method")

    def _row_locator(self, title_or_code: str):  # noqa: ARG002
        raise NotImplementedError(self._M1)

    def _run_row_action(self, title_or_code: str, action: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, action)")

    def approve_entry(self, title_or_code: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, 'approve')")

    def reject_entry(self, title_or_code: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, 'reject')")

    def resubmit_entry(self, title_or_code: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, 'resubmit')")

    def publish_entry(self, title_or_code: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, 'publish')")

    def unpublish_entry(self, title_or_code: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, 'unpublish')")

    def archive_entry(self, title_or_code: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, 'archive')")

    def restore_entry(self, title_or_code: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, 'restore')")

    def return_to_author(self, title_or_code: str, comment: str = ""):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": run_row_action(entry, 'return', comment)")

    def history_entries(self, title_or_code: str):  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": history(entry)")

    def delete_entry_by_code(self, entry_code: str) -> bool:  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": delete_disposable_entry(entry)")

    def row_status_text_by_code(self, entry_code: str) -> str:  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": row_status(entry)")

    def row_visible_by_code(self, entry_code: str) -> bool:  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": row_present(entry)")

    def row_preview_url_by_code(self, entry_code: str) -> str:  # noqa: ARG002
        raise NotImplementedError(self._M1 + ": row_preview_href(entry)")

    def find_entry_code_by_field(self, field_label: str, expected_value: str) -> str:  # noqa: ARG002
        raise NotImplementedError(self._M1)

    # =====================================================================
    # Legacy title-based queries (now exact-title; used by existing tests)
    # =====================================================================
    def row_visible(self, title: str) -> bool:
        return len(self.rows_with_exact_title(title)) > 0

    def row_status_text(self, title: str) -> str:
        """Status of the ONE row titled exactly `title` ("" when none or
        ambiguous)."""
        row = self._single_exact_row(title)
        if row is None:
            return ""
        if " ".join(row["status"].split()).casefold() == STATUS_INACTIVE.casefold():
            return STATUS_INACTIVE
        return normalize_status(row["status"])

    def status_for(self, title: str) -> str:
        self.open_entries_list()
        return self.row_status_text(title)

    def row_entry_id(self, title: str) -> str:
        row = self._single_exact_row(title)
        return row["entry_id"] if row else ""

    def row_last_modified(self, title: str) -> str:
        row = self._single_exact_row(title)
        return row["modified"] if row else ""

    def row_preview_url(self, title: str) -> str:
        entry_id = self.row_entry_id(title)
        return self.row_preview_href(CreatedEntry(title, entry_id)) if entry_id else ""

    def row_entry_numeric_id(self, title: str) -> str:
        """Numeric id from the row's Preview href (`qcPreview=publications%3A<id>`)
        — the id the public `publication-detail?id=` route uses."""
        match = re.search(r"qcPreview=publications%3A(\d+)", self.row_preview_url(title))
        return match.group(1) if match else ""

    def open_entry_by_edit_link(self, title: str) -> "PublicationAdminPage":
        """Opens the ONE row titled exactly `title` (raises when 0 or >1)."""
        self.open_entries_list()
        row = self._single_exact_row(title)
        if row is None:
            raise AssertionError(
                f"cannot open {title!r}: {len(self.rows_with_exact_title(title))} rows carry that exact title"
            )
        return self.open_entry(CreatedEntry(title=title, entry_id=row["entry_id"]))

    # =====================================================================
    # Fields
    # =====================================================================
    def _form(self):
        return self.page.locator(self.AUTHORING_FORM).first

    def _textbox(self, label: str):
        return self.page.get_by_role("textbox", name=self.label_pattern(label))

    def _spinbutton(self, label: str):
        return self.page.get_by_role("spinbutton", name=self.label_pattern(label))

    def fill_text(self, field_label: str, value: str) -> "PublicationAdminPage":
        self._textbox(field_label).fill(value)
        return self

    def field_value(self, field_label: str) -> str:
        return self._textbox(field_label).input_value()

    def fill_number(self, field_label: str, value: str) -> "PublicationAdminPage":
        self._spinbutton(field_label).fill(value)
        return self

    def number_field_value(self, field_label: str) -> str:
        return self._spinbutton(field_label).input_value()

    def type_into_number(self, field_label: str, text: str) -> "PublicationAdminPage":
        """Types `text` key by key into a number box (clearing it first), the
        way a user would — `fill()` refuses non-numeric text on
        input[type=number], so whitespace-only input needs real keystrokes."""
        box = self._spinbutton(field_label)
        box.click()
        box.press("Control+A")
        box.press("Delete")
        self.page.keyboard.type(text, delay=20)
        return self

    @staticmethod
    def _unique_upload_copy(file_path: str) -> str:
        """HEALED 2026-09-30: Documents & Media de-duplicates a same-named
        upload as "name (N).ext" and, after enough runs re-uploading the SAME
        fixture names, refuses further copies (`{"success":false}` — observed
        live for valid_cover_1_5mb.jpg / valid_pdf_4mb.pdf while a uniquely
        named copy of the identical bytes uploaded fine). Every upload
        therefore sends a temporary, uniquely named copy (same bytes, same
        extension, so type/size checks are unaffected).

        NOTE (review m6): every upload - accepted OR later abandoned - leaves a
        file in the site's Documents & Media library. Deleting a Publication
        does NOT delete its cover/attachment files, and this framework never
        deletes Documents & Media files. The local temp copy IS removed right
        after the upload (see upload_file / upload_file_by_field_name)."""
        import os
        import shutil
        import tempfile
        import uuid

        stem, ext = os.path.splitext(os.path.basename(file_path))
        folder = os.path.join(tempfile.gettempdir(), "qctest_uploads_130711")
        os.makedirs(folder, exist_ok=True)
        target = os.path.join(folder, f"{stem}-{uuid.uuid4().hex[:8]}{ext}")
        shutil.copyfile(file_path, target)
        return target

    @staticmethod
    def _remove_temp(path: str) -> None:
        import os

        try:
            os.remove(path)
        except OSError:
            logger.warning("could not remove temp upload copy %s", path)

    def upload_file(self, field_label: str, file_path: str) -> "PublicationAdminPage":
        """Waits for the picker's upload POST response before clicking "Add"
        (the button is clickable before the upload is done, and a click then
        is ignored — tc_144007 flake), uploads a uniquely named copy (see
        `_unique_upload_copy`), and fails clearly if Documents & Media still
        answers `{"success":false}`. `last_uploaded_name` is the name sent."""
        import os

        upload_path = self._unique_upload_copy(file_path)
        self.last_uploaded_name = os.path.basename(upload_path)
        self.last_upload_response = ""
        hidden = self.page.get_by_role("textbox", name=f"{field_label} Select File")
        hidden.locator("xpath=..").get_by_role("button", name="Select File").click()
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
        self.last_upload_response = body
        if '"success":false' in body.replace(" ", ""):
            raise AssertionError(
                f"Documents & Media refused the upload of {self.last_uploaded_name} "
                f"(HTTP {upload.value.status}, body {body[:120]!r})"
            )
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

    # Specific error elements inside the file picker (never its static help text).
    PICKER_ERROR = (".alert-danger, .alert-warning, [role='alert'], .text-danger, .invalid-feedback, "
                    ".form-feedback-item, .lfr-dropzone-error, .upload-error")

    def attempt_upload(self, field_label: str, file_path: str, response_timeout_ms: int = 20000) -> dict:
        """Review M6: tries an upload WITHOUT clicking Add and reports only hard
        evidence: {file, status, body, success (True/False/None when no upload
        POST answered), errors: [texts of specific picker error elements]}.
        An exception or the picker's static help text is never evidence.
        The picker is closed afterwards; nothing is attached or saved."""
        import os

        upload_path = self._unique_upload_copy(file_path)
        result = {"file": os.path.basename(upload_path), "status": None, "body": "", "success": None, "errors": []}
        hidden = self.page.get_by_role("textbox", name=f"{field_label} Select File")
        hidden.locator("xpath=..").get_by_role("button", name="Select File").click()
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
        except Exception:  # noqa: BLE001 — no upload POST answered: recorded as success=None
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
        # Server accepted the file into Documents & Media: the FIELD's own limit
        # may still refuse it at selection time — click Add once and record
        # whether the picker closes (file taken) or shows an error.
        result["add_clicked"] = False
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
            except Exception:  # noqa: BLE001 — recorded as add_clicked False
                pass
        if self.page.locator(self.UPLOAD_MODAL_IFRAME).count() == 0:
            self.last_upload_attempt = result
            return result
        self.page.keyboard.press("Escape")
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
        except Exception:  # noqa: BLE001
            logger.warning("upload picker did not close on Escape")
        self.last_upload_attempt = result
        return result

    def upload_file_expect_rejected(self, field_label: str, file_path: str) -> bool:
        """True when the upload was refused (picker never completed, or the
        field does not show the name actually sent). Compares against
        `last_uploaded_name` because upload_file() sends a renamed copy.
        On a refusal, `last_upload_rejection_text` holds the picker's own text
        (read BEFORE it is closed) and `last_upload_error` the failure."""
        self.last_upload_rejection_text = ""
        self.last_upload_error = ""
        try:
            self.upload_file(field_label, file_path)
        except Exception as exc:  # noqa: BLE001 — a refused upload
            self.last_upload_error = str(exc)[:400]
            if self.page.locator(self.UPLOAD_MODAL_IFRAME).count():
                try:
                    self.last_upload_rejection_text = (
                        self.page.frame_locator(self.UPLOAD_MODAL_IFRAME).locator("body").inner_text(timeout=5000)
                    )
                except Exception:  # noqa: BLE001 — evidence only
                    pass
                self.page.keyboard.press("Escape")
            return True
        try:
            current = self.uploaded_filename(field_label)
        except Exception:  # noqa: BLE001
            return True
        return getattr(self, "last_uploaded_name", "") not in current

    def uploaded_filename(self, field_label: str) -> str:
        return self._textbox(field_label).inner_text().strip()

    def _date_box(self):
        return self._form().get_by_placeholder(PUBLICATION_DATE_PLACEHOLDER)

    def set_publication_date(self, value: str) -> "PublicationAdminPage":
        """`value` dd/mm/yyyy, e.g. "20/09/2026"."""
        box = self._date_box()
        box.click()
        box.press("Control+A")
        box.press("Delete")
        self.page.keyboard.type(value, delay=20)
        return self

    def date_field_message(self) -> str:
        """Inline message the date picker renders inside the Publication Date
        field (live 2026-10-01: "Use dd/mm/yyyy" appears only after an
        invalid entry such as 32/13/2026; absent for a valid date). "" when none."""
        text = self._date_box().evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 5 && c && !/Publication Date/.test(c.innerText); i++) c = c.parentElement;
                       return c ? c.innerText : ''; }"""
        )
        lines = [ln.strip() for ln in text.split("\n")]
        return " ".join(ln for ln in lines if ln and ln not in ("Publication Date", "?"))

    def publication_date_value(self) -> str:
        return self._date_box().input_value()

    def _type_combobox(self):
        return self.page.get_by_role("combobox", name=self.label_pattern(FIELD_PUBLICATION_TYPE))

    def select_publication_type(self, type_label: str) -> "PublicationAdminPage":
        """Opens THIS combobox's own listbox (scoped by aria-controls) and
        picks `type_label`; waits until the control holds it."""
        combobox = self._type_combobox()
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        choice = self.page.locator(f'[id="{listbox_id}"] [role="option"]:text-is("{type_label}")')
        choice.wait_for(state="visible", timeout=5000)
        choice.click()
        wait_until(lambda: combobox.input_value() == type_label, timeout=5.0, poll=0.2,
                   message=f"Publication Type did not take {type_label!r}")
        return self

    def publication_type_value(self) -> str:
        return self._type_combobox().input_value()

    def publication_type_options(self) -> list[str]:
        combobox = self._type_combobox()
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        options = self.page.locator(f'[id="{listbox_id}"] [role="option"]')
        options.first.wait_for(state="visible", timeout=5000)
        texts = [t.strip() for t in options.all_inner_texts()]
        self.page.keyboard.press("Escape")
        return texts

    def set_publication_status(self, status_label: str) -> "PublicationAdminPage":
        raise AssertionError(
            f"set_publication_status({status_label!r}): the 'Publication Status' combobox no longer "
            "exists on manage-publication (live 2026-09-30). The workflow state replaces it — use "
            "publish() as an Editor, or save_as_draft()."
        )

    def set_active_status(self, active: bool) -> "PublicationAdminPage":
        box = self.page.get_by_role("checkbox", name=self.label_pattern(FIELD_ACTIVE_STATUS))
        box.check() if active else box.uncheck()
        return self

    def active_status(self) -> bool:
        return self.page.get_by_role("checkbox", name=self.label_pattern(FIELD_ACTIVE_STATUS)).is_checked()

    def form_field_labels(self) -> list[str]:
        """Accessible names of every textbox/spinbutton/combobox/checkbox in
        the authoring form (e.g. to prove a field such as 'Publication ID'
        is absent)."""
        return self._form().evaluate(
            """(f) => [...f.querySelectorAll('input:not([type=hidden]), textarea, select, [role=textbox], [role=combobox]')]
                .map(e => (e.labels && e.labels[0] ? e.labels[0].innerText : (e.getAttribute('aria-label') || e.placeholder || '')).trim())
                .filter(Boolean)"""
        )

    # =====================================================================
    # Save / submit (with an outcome probe — a PUT alone does not mean saved)
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

    def is_save_as_draft_enabled(self) -> bool:
        button = self.page.get_by_role("button", name=self.SAVE_AS_DRAFT_NAME)
        return button.count() > 0 and button.first.is_enabled()

    def save_as_draft(self) -> "PublicationAdminPage":
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SAVE_AS_DRAFT_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def save_draft(self) -> "PublicationAdminPage":
        return self.save_as_draft()

    def publish(self) -> "PublicationAdminPage":
        """Clicks the role-dependent submit button (Publish / Submit for
        Review / Save changes). Asserts nothing — the caller pins the account."""
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SUBMIT_BUTTON_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def submit(self) -> "PublicationAdminPage":
        return self.publish()

    def submit_for_review(self) -> "PublicationAdminPage":
        """Back-compat name for the role-dependent submit (see publish())."""
        return self.publish()

    BLOCKED_MESSAGE = "Please complete the required fields"

    def submit_blocked(self) -> bool:
        """The last save/submit did NOT go through (no reload) and the form
        showed refusal evidence, or the workflow's required-fields message."""
        if self.save_redirected():
            return False
        return self.save_refused() or self.BLOCKED_MESSAGE in self.page_body_text()

    def page_body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def _arm_save_probe(self) -> None:
        self._save_requests: list[str] = []
        self._save_responses: list[int] = []
        self._navigated = False
        # Review m7: refusal banners already on screen BEFORE this click do not
        # count as this attempt's refusal.
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
                window.__qcPubInvalid = [];
                if (!window.__qcPubInvalidHooked) {{
                    window.__qcPubInvalidHooked = true;
                    document.addEventListener('invalid', (e) => {{
                        const t = e.target; window.__qcPubInvalid.push(t.name || t.id || '');
                    }}, true);
                }}
            }}"""
        )

    def _refusal_banners(self) -> list[str]:
        try:
            return [t for t in self.feedback_banners()
                    if "not saved" in t or self.BLOCKED_MESSAGE in t]
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
            return list(self.page.evaluate("() => window.__qcPubInvalid || []"))
        except Exception:  # noqa: BLE001
            return []

    def _refusal_shown(self) -> bool:
        try:
            return (
                bool(self._invalid_fields_this_attempt())
                or self.page.locator(self.FIELD_ERROR).count() > 0
                or self.refusal_bar_text() != ""
                or self.BLOCKED_MESSAGE in self.page_body_text()
            )
        except Exception:  # noqa: BLE001
            return False

    def _wait_for_save_outcome(self) -> None:
        """Success = the manage page reloaded (document replaced) and rendered
        either the list or a form. Refusal = refusal evidence from THIS
        attempt, no accepted save request, no navigation, for a quiet window."""
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
            # Review m7: the server can answer the save with HTTP 200 and still
            # refuse it - a NEW red bar for this attempt and no navigation.
            # HEALED 2026-10-02: ... or a NEW inline field error after the
            # POST .../validate call (answered 200) — e.g. "Page count must be a
            # positive whole number (1 or greater).".
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

    def save_redirected(self) -> bool:
        return bool(getattr(self, "last_save_reloaded", False))

    def save_refused(self) -> bool:
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

    def success_banners(self, timeout: float = 15.0) -> list[str]:
        """Post-save success banners (not the "Editing …" bar, not a refusal),
        waited for up to `timeout`; [] when none appeared."""
        def _read() -> list[str]:
            return [t for t in self.feedback_banners()
                    if not t.startswith("Editing") and "not saved" not in t]
        try:
            wait_until(lambda: bool(_read()), timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass
        return _read()

    def field_errors(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.FIELD_ERROR).all_inner_texts() if t.strip()]

    def refusal_bar_text(self) -> str:
        for text in self.feedback_banners():
            if "not saved" in text:
                return text
        return ""

    def editing_bar_text(self) -> str:
        for text in self.feedback_banners():
            if text.startswith("Editing"):
                return text
        return ""

    # =====================================================================
    # Preview
    # =====================================================================
    def open_preview(self, entry: CreatedEntry) -> str:
        """Opens the row's own Preview link in this (CMS) session and returns
        the rendered page text. Live 2026-09-30 a Draft preview renders
        "PREVIEW — this record is Draft. Visitors do not see it." plus the
        authored title/description."""
        self.open_entries_list()
        url = self.row_preview_href(entry)
        if not url:
            raise AssertionError(f"row {entry} has no Preview link")
        self.open(url)
        try:
            wait_until(lambda: entry.title in self.page_body_text(), timeout=30.0, poll=1.0)
        except WaitTimeoutError:
            pass
        return self.page_body_text()

    # =====================================================================
    # Locale-neutral form access — for the Arabic-session cases (144080/
    # 144081). standards.md forbids Arabic locators, so these address the
    # controls by their stable name/id attributes instead of labels. The
    # interface locale comes from the URL prefix of THIS browser session
    # (`/ar/...`); no account language preference is ever changed.
    # =====================================================================
    SUBMIT_NON_DRAFT = 'button[type=submit][name=status]:not(:has-text("Save as Draft"))'

    def open_new_entry_form_in_locale(self, locale: str) -> "PublicationAdminPage":
        self.open(self._manage_url(locale=locale))
        self._locale = locale
        self._entry_code = None
        self._form().locator(self.SUBMIT_NON_DRAFT).wait_for(timeout=35000)
        return self

    def open_entry_in_locale(self, entry: CreatedEntry, locale: str) -> "PublicationAdminPage":
        self.open_entries_list()
        href = self._row(entry).first.get_by_role("link", name="Edit").first.get_attribute("href") or ""
        match = re.search(r"editEntry=([^&#]+)", href)
        if not match:
            raise AssertionError(f"row for {entry} has no Edit link")
        self._entry_code = match.group(1)
        self.open(self._manage_url(edit_entry=match.group(1), locale=locale))
        self._locale = locale
        self._form().locator(self.SUBMIT_NON_DRAFT).wait_for(timeout=35000)
        return self

    def interface_language(self) -> str:
        """Liferay's languageId for THIS page view (e.g. "ar_SA", "en_US")."""
        return self.page.evaluate("() => (window.Liferay && Liferay.ThemeDisplay) ? Liferay.ThemeDisplay.getLanguageId() : ''")

    def fill_field_by_name(self, object_field: str, value: str) -> "PublicationAdminPage":
        """`object_field` is the Object field key, e.g. "publicationTitle";
        `object_field + '_ar'` fills the Arabic twin (#qc-ar-<field>)."""
        if object_field.endswith("_ar"):
            self.page.locator(f"#qc-ar-{object_field[:-3]}").fill(value)
        else:
            self._form().locator(f'[name="ObjectField_{object_field}"]').fill(value)
        return self

    def select_type_option_by_index(self, index: int = 0) -> str:
        """Picks the Nth Publication Type option without reading its
        (localised) label; returns the option text."""
        combobox = self._form().locator('input[id$="select-from-list-input"]').first
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        options = self.page.locator(f'[id="{listbox_id}"] [role="option"]')
        options.first.wait_for(state="visible", timeout=5000)
        text = options.nth(index).inner_text().strip()
        options.nth(index).click()
        return text

    def set_publication_date_any_locale(self, value: str) -> "PublicationAdminPage":
        box = self._form().locator('input[id^="qc-dtp-"]').first
        box.click()
        self.page.keyboard.type(value, delay=20)
        return self

    def upload_file_by_field_name(self, object_field: str, file_path: str) -> "PublicationAdminPage":
        """Locale-neutral upload: the field's own picker button, then the
        picker's primary action (its last `.btn-primary`, "Add" in English)."""
        wrapper = self._form().locator(f'[name="ObjectField_{object_field}"]').locator("xpath=..")
        wrapper.locator("button").first.click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        file_path = self._unique_upload_copy(file_path)
        # HEALED 2026-09-30 (tc_144081): "Add" is enabled before the upload
        # completes, and a click then does nothing. Wait for the upload POST's
        # own response (locale-neutral signal) before clicking.
        try:
            with self.page.expect_response(
                lambda r: r.request.method == "POST" and bool(self.UPLOAD_REQUEST_PATTERN.search(r.url)),
                timeout=45000,
            ) as upload:
                frame.locator('input[type="file"]').set_input_files(file_path)
        finally:
            self._remove_temp(file_path)
        try:
            body = upload.value.text()
        except Exception:  # noqa: BLE001
            body = ""
        if '"success":false' in body.replace(" ", ""):
            raise AssertionError(
                f"ENVIRONMENT: Documents & Media refused the upload of {file_path} "
                f"(HTTP {upload.value.status}, body {body[:120]!r}) — qcdev upload failure, not a test fault"
            )
        add = frame.locator("button.btn-primary").last
        modal = self.page.locator(self.UPLOAD_MODAL_IFRAME)

        def _added() -> bool:
            if modal.count() == 0:
                return True
            try:
                add.click(timeout=3000)
            except Exception:  # noqa: BLE001 — retried until the picker closes
                pass
            return modal.count() == 0

        wait_until(_added, timeout=30.0, poll=1.5, message="the file picker did not close after Add")
        wait_until(lambda: self.field_stored_value(object_field) != "", timeout=10.0, poll=0.5,
                   message=f"{object_field} did not take the uploaded file")
        return self

    def field_stored_value(self, object_field: str) -> str:
        """Raw value of the form control `ObjectField_<field>` (a file field
        holds the Documents & Media file id; "" when nothing is attached)."""
        return self._form().locator(f'[name="ObjectField_{object_field}"]').input_value()

    def field_native_message(self, object_field: str) -> str:
        """The browser's own constraint message on `ObjectField_<field>`."""
        return self._form().locator(f'[name="ObjectField_{object_field}"]').evaluate(
            "el => el.validationMessage || ''")

    def form_text(self) -> str:
        """Rendered text of the authoring form (inline messages, attached
        file names) — read-only evidence."""
        form = self._form()
        return form.inner_text() if form.count() else ""

    def control_native_message(self, name_or_id: str) -> str:
        """Browser constraint message of the control whose name OR id is
        `name_or_id` (the AR twins and the type combobox have no name)."""
        control = self._control(name_or_id)
        if control.count() == 0:
            return ""
        return control.first.evaluate("el => el.validationMessage || ''")

    def _control(self, ref: str):
        """Form control whose name or id is `ref`, or whose id ENDS with `ref`
        (the Publication Type combobox id is `fragment-<uuid>-select-from-list-input`)."""
        return self._form().locator(f'[name="{ref}"], [id="{ref}"], input[id$="{ref}"]')

    # Form controls an inline error can belong to (live 2026-10-02).
    _ATTRIBUTABLE_CONTROLS = ('[name^="ObjectField_"]:not([type=hidden]), [id^="qc-ar-"], '
                              'input[id$="select-from-list-input"]')

    def field_errors_by_control(self) -> dict:
        """{control name/id: [texts]} for every inline `[data-qc-oel-field-error]`
        node, attributed to the ONE form control its nearest ancestor contains
        (walking up until an ancestor holds a control; holding two or more =
        unattributed, key ""). Static help text is never such a node.
        HEALED 2026-10-02: this build validates through POST .../validate and
        renders these nodes, often without firing the browser `invalid` event."""
        form = self._form()
        if form.count() == 0:
            return {}
        return form.evaluate(
            """(f, sel) => {
                const out = {};
                for (const err of f.querySelectorAll('[data-qc-oel-field-error]')) {
                    const text = err.innerText.trim();
                    if (!text) continue;
                    let key = '', node = err.parentElement;
                    while (node && node !== f.parentElement) {
                        const ctrls = node.querySelectorAll(sel);
                        if (ctrls.length === 1) { key = ctrls[0].name || ctrls[0].id; break; }
                        if (ctrls.length > 1) { key = ''; break; }
                        node = node.parentElement;
                    }
                    (out[key] = out[key] || []).push(text);
                }
                return out;
            }""",
            self._ATTRIBUTABLE_CONTROLS,
        )

    def field_scoped_error(self, name_or_id: str) -> str:
        """Text of an inline error node that belongs to THIS control only:
        an element its aria-describedby points at, else an error node
        ([data-qc-oel-field-error], [role=alert], .form-feedback-item,
        .invalid-feedback) inside the control's own wrapper - the outermost
        ancestor still holding exactly ONE form control (never widened to a
        sibling field or the form). "" when none (review M4)."""
        control = self._control(name_or_id)
        if control.count() == 0:
            return ""
        return control.first.evaluate(
            """(el) => {
                const sel = '[data-qc-oel-field-error], [role=alert], .form-feedback-item, .invalid-feedback';
                for (const id of (el.getAttribute('aria-describedby') || '').split(/\\s+/).filter(Boolean)) {
                    const n = document.getElementById(id);
                    if (n && n.innerText.trim()) return n.innerText.trim();
                }
                const controls = 'input:not([type=hidden]), select, textarea';
                let wrapper = null, node = el.parentElement;
                while (node && node.tagName !== 'FORM' && node.querySelectorAll(controls).length === 1) {
                    wrapper = node; node = node.parentElement;
                }
                if (!wrapper) return '';
                return [...wrapper.querySelectorAll(sel)].map(n => n.innerText.trim()).filter(Boolean).join(' ');
            }"""
        )

    def invalid_fields_last_attempt(self) -> list[str]:
        """Field names the last submit attempt flagged via the `invalid` event."""
        return list(getattr(self, "last_invalid_fields", []))

    def publish_any_locale(self) -> "PublicationAdminPage":
        """The role-dependent submit button, located without its label text
        (the one form status-submit that is not "Save as Draft")."""
        self._arm_save_probe()
        self._form().locator(self.SUBMIT_NON_DRAFT).first.click()
        self._wait_for_save_outcome()
        return self

    # =====================================================================
    # Interrupted upload (144073) — deterministic network drop
    # =====================================================================
    UPLOAD_REQUEST_PATTERN = re.compile(r"com_liferay_document_library_web_portlet_DLPortlet.*p_p_lifecycle=1")

    def upload_with_network_drop(self, field_label: str, file_path: str) -> dict:
        """Starts a real upload through the field's picker while the upload
        POST (Documents & Media action, observed live 2026-09-30) is aborted
        with `internetdisconnected`, then closes the picker. Returns
        {aborted: [urls], picker_text: str}. Nothing is saved."""
        aborted: list[str] = []

        def _handler(route):
            if route.request.method == "POST":
                aborted.append(route.request.url)
                route.abort("internetdisconnected")
            else:
                route.continue_()

        context = self.page.context
        context.route(self.UPLOAD_REQUEST_PATTERN, _handler)
        picker_text = ""
        try:
            hidden = self.page.get_by_role("textbox", name=f"{field_label} Select File")
            hidden.locator("xpath=..").get_by_role("button", name="Select File").click()
            frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
            frame.locator('input[type="file"]').set_input_files(file_path)
            try:
                wait_until(lambda: bool(aborted), timeout=20.0, poll=0.3, message="upload POST never sent")
                frame.get_by_text("An unexpected error occurred while uploading your file.").wait_for(timeout=15000)
            except Exception:  # noqa: BLE001 — reported through picker_text / aborted
                pass
            picker_text = frame.locator("body").inner_text()
        finally:
            context.unroute(self.UPLOAD_REQUEST_PATTERN)
        self.page.keyboard.press("Escape")
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
        except Exception:  # noqa: BLE001
            logger.warning("upload picker did not close on Escape")
        return {"aborted": aborted, "picker_text": picker_text}

    # =====================================================================
    # Disposable-entry convenience (QCTEST- titles only)
    # =====================================================================
    DEFAULT_COVER = "cms/tests/publications/fixtures/valid_cover_1_5mb.jpg"
    DEFAULT_FILE = "cms/tests/publications/fixtures/valid_pdf_4mb.pdf"

    def fill_publication(self, data: dict) -> "PublicationAdminPage":
        """Fills whichever keys `data` carries (None/absent = untouched):
        title, title_ar, description, description_ar, publication_type,
        publication_date (dd/mm/yyyy), cover_path, file_path, page_count,
        active_status."""
        text_fields = (
            ("title", FIELD_PUBLICATION_TITLE_EN), ("title_ar", FIELD_PUBLICATION_TITLE_AR),
            ("description", FIELD_PUBLICATION_DESCRIPTION_EN),
            ("description_ar", FIELD_PUBLICATION_DESCRIPTION_AR),
        )
        for key, label in text_fields:
            if data.get(key) is not None:
                self.fill_text(label, data[key])
        if data.get("publication_type"):
            self.select_publication_type(data["publication_type"])
        if data.get("publication_date"):
            self.set_publication_date(data["publication_date"])
        if data.get("cover_path"):
            self.upload_file(FIELD_COVER_IMAGE, data["cover_path"])
        if data.get("file_path"):
            self.upload_file(FIELD_FILE_ATTACHMENT, data["file_path"])
        if data.get("page_count") is not None:
            self.fill_number(FIELD_PAGE_COUNT, str(data["page_count"]))
        if data.get("active_status") is not None:
            self.set_active_status(bool(data["active_status"]))
        return self

    def read_publication(self) -> dict:
        return {
            "title": self.field_value(FIELD_PUBLICATION_TITLE_EN),
            "title_ar": self.field_value(FIELD_PUBLICATION_TITLE_AR),
            "description": self.field_value(FIELD_PUBLICATION_DESCRIPTION_EN),
            "description_ar": self.field_value(FIELD_PUBLICATION_DESCRIPTION_AR),
            "publication_type": self.publication_type_value(),
            "publication_date": self.publication_date_value(),
            "page_count": self.number_field_value(FIELD_PAGE_COUNT),
            "active_status": self.active_status(),
        }

    @classmethod
    def default_data(cls, title: str, **overrides) -> dict:
        if not title.startswith(QCTEST_PREFIX):
            raise ValueError(f"disposable titles must start with {QCTEST_PREFIX}: {title!r}")
        data = {
            "title": title,
            "title_ar": f"{title} منشور",
            "description": f"{title} disposable automated-test publication description.",
            "description_ar": "وصف منشور تجريبي تم إنشاؤه تلقائيًا.",
            "publication_type": "Report",
            "publication_date": "01/01/2026",
            "cover_path": cls.DEFAULT_COVER,
            "file_path": cls.DEFAULT_FILE,
            "page_count": "3",
            "active_status": True,
        }
        data.update(overrides)
        return data

    def create_disposable_entry(self, prefix: str, **overrides) -> dict:
        """Back-compat: opens the create form and fills a `QCTEST-<prefix>
        Publication` entry (does NOT save). Legacy FIELD_* keys are honoured."""
        if "status" in overrides:
            raise AssertionError("'status' is gone from the form — use publish()/save_as_draft()")
        legacy = {
            FIELD_PUBLICATION_TITLE_EN: "title", FIELD_PUBLICATION_TITLE_AR: "title_ar",
            FIELD_PUBLICATION_DESCRIPTION_EN: "description",
            FIELD_PUBLICATION_DESCRIPTION_AR: "description_ar",
        }
        mapped = {legacy.get(k, k): v for k, v in overrides.items()}
        if mapped.pop("skip_cover", False):
            mapped["cover_path"] = None
        if mapped.pop("skip_file", False):
            mapped["file_path"] = None
        title = mapped.pop("title", f"{QCTEST_PREFIX}{prefix} Publication")
        data = self.default_data(title, **mapped)
        self.open_new_entry_form()
        self.fill_publication(data)
        data[FIELD_PUBLICATION_TITLE_EN] = title
        return data

    def publish_disposable_entry(self, prefix: str, **overrides) -> dict:
        """create_disposable_entry() + the role's submit (Editor: Publish)."""
        overrides.pop("status", None)
        data = self.create_disposable_entry(prefix, **overrides)
        self.publish()
        return data

    @staticmethod
    def manage_url(edit_entry: str | None = None) -> str:
        path = MANAGE_PATH + (f"?editEntry={edit_entry}" if edit_entry else "")
        return control_panel_url(path)

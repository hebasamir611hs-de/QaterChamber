"""
cms/pages/photo_gallery/gallery_admin_base.py — GalleryAdminPage (core, Agent PA).

Shared Object Authoring base for PBI 130714 ("QC - Insights & Media - 006 -
Photo Gallery") Control_Panel work. Every Photo Gallery object is a
`/web/qatar-chamber/manage-<slug>` page with the SAME seven-state editorial
workflow (see cms/pages/components/object_authoring_page.py), so this class
holds everything that is not object-specific; the per-object Page Objects
(photo_album_admin_page.py, event_category_admin_page.py) only add their
field keys.

Read live 2026-10-05 as Site Content Editor (156488) on qcdev:

  - manage-photo-album (Photo Album, 3 real albums, codes
    QCDEMO-130714-PHOTO_ALBUM-*), manage-event-category (Photo Gallery Event
    Category, 3 real: Institutional / Collaboration / Events, codes
    QCDEMO-130714-EVENT_CATEGORY-*), manage-page-hero (2), manage-uploaded-album
    (0), manage-flickr-album (136, the Documents & Media folders photos come
    from).
  - EN text inputs are `[name="ObjectField_<key>"]`; their Arabic twins are
    `#qc-ar-<key>` (no name). Dates: visible `#qc-dtp-<hiddenId>` (dd/mm/yyyy)
    bound to `input[type=date][name="ObjectField_<key>"]`. Relationship /
    picklist fields: hidden `input[name="ObjectField_<key>"]` id
    `<prefix>-value-input` + `<prefix>-select-from-list-input` text box,
    options `li[role=option]` under `<prefix>-listbox`.
  - activeStatus checkbox is TICKED by default; form buttons are
    `button[name=status]` value 2 "Save as Draft" and value 0 "Publish"
    (Editor) / "Submit for Review" (Author).
  - Entries table: first cell = Entry title (EN), second = status badge;
    every row action carries `data-qc-oel-<action>="<entryId>"` and
    `data-qc-oel-label="<title>"`; the Edit link is `?editEntry=<code>`.
  - Top-of-page messages render in `[data-qc-oel-editbar]`.

DELETE SAFETY (user's standing rule, 14 records were once lost): the only
delete here is `delete_own_entry()`. It accepts only a GalleryEntry whose
title starts with this instance's QCTEST-130714-<agent>- prefix, whose id was
captured at creation by this test (list-id diff + exact title read back by
code), that is NOT a QCDEMO- seeded code, and it re-reads the record and
re-checks the fully expanded list immediately before the click; the native
confirm() is accepted only when it names the captured title. There is no
positional, looping, "first link" or substring delete in this module.
Workflow row actions go through `run_row_action()`, which carries the same
identity guard (History excepted, read-only).

Subclass for your own agent: pass your prefix
(`QCTEST-130714-PB-` etc.) and evidence folder to the constructor; do not
edit this file's methods in place — add a `# --- <AGENT> ---` section.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from time import monotonic

from cms.pages.components.object_authoring_page import ObjectAuthoringPage, normalize_status
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import PROJECT_ROOT, cms_role_credentials, control_panel_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.license_gate import clear_license_gate
from core.web.overlays import _dismiss_chatbot_launcher, dismiss_overlays

_logger = get_logger("gallery_admin_base")

# ---- namespace / roles ------------------------------------------------------
GALLERY_PREFIX_ROOT = "QCTEST-130714-"
REAL_CODE_PREFIXES = ("QCDEMO-",)
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}
AUTH_FAILED_BANNER_TEXT = "Authentication failed"

# ---- top-of-page messages (exact, live 2026-10-05) --------------------------
MSG_DRAFT_SAVED = "Draft saved."
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
MSG_ARABIC_SAVED = "Arabic content saved for this record."
MSG_ARABIC_NOT_SAVED_FRAGMENT = "Arabic content was not"
MSG_BLOCKED_FRAGMENT = "Please complete the required fields"
STATUS_INACTIVE = "Inactive"


@dataclass(frozen=True)
class GalleryEntry:
    """Identity of a record THIS test created (captured right after the save)."""

    title: str
    entry_id: str
    code: str
    prefix: str
    slug: str

    def in_namespace(self) -> bool:
        return (self.prefix.startswith(GALLERY_PREFIX_ROOT) and len(self.prefix) > len(GALLERY_PREFIX_ROOT)
                and self.title.startswith(self.prefix)
                and not any(self.code.startswith(p) for p in REAL_CODE_PREFIXES))


class GalleryAdminPage(ObjectAuthoringPage):
    """Generic manage-<slug> helpers for the Photo Gallery objects."""

    TITLE_KEY = ""  # set by the per-object subclass (the Entry column's EN field)
    FORM = 'form:has([name^="ObjectField_"])'
    SUBMIT_NAME = re.compile(r"^\s*(Publish|Submit for Review|Submit for Publishing)\s*$")
    SAVE_AS_DRAFT_NAME = re.compile(r"^\s*Save as Draft\s*$")
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    ENTRY_COUNT = "[data-qc-oel-count]"
    EDITBAR = "[data-qc-oel-editbar]"
    FIELD_ERROR = "[data-qc-oel-field-error]"
    DELETE_LINK_BY_ID = 'a[data-qc-oel-delete="{entry_id}"]'
    ID_ATTRS = ("delete", "history", "view", "approve", "reject", "resubmit", "publish",
                "unpublish", "archive", "restore", "return", "schedule")
    ROW_ACTION_NAMES = ("view", "approve", "reject", "resubmit", "publish", "unpublish", "archive",
                        "restore", "return", "schedule", "history", "delete")
    DESTRUCTIVE_ROW_ACTIONS = frozenset({"delete", "trash", "untrash"})
    LIST_LOADED = ", ".join(f"[data-qc-oel-{n}]" for n in ID_ATTRS)
    HISTORY_CELL = "td.qc-oel__history"
    HISTORY_ACTION = ".qc-oel__history-action"
    SAVE_REQUEST_PATTERN = re.compile(r"edit_info_item|/o/c/")
    UPLOAD_REQUEST_PATTERN = re.compile(r"com_liferay_document_library_web_portlet_DLPortlet.*p_p_lifecycle=1")
    PICKER_ERROR = (".alert-danger, .alert-warning, [role='alert'], .text-danger, .invalid-feedback, "
                    ".form-feedback-item, .lfr-dropzone-error, .upload-error")
    REFUSAL_QUIET_WINDOW_S = 6.0
    SAVE_OUTCOME_TIMEOUT_S = 90.0
    _DOC_MARK = "__qcGalleryBeforeSave"

    def __init__(self, page, slug: str, prefix: str, evidence_dir: str):
        super().__init__(page, slug)
        if not prefix.startswith(GALLERY_PREFIX_ROOT) or len(prefix) <= len(GALLERY_PREFIX_ROOT):
            raise ValueError(f"prefix {prefix!r} is not a {GALLERY_PREFIX_ROOT}<agent>- namespace")
        self.prefix = prefix
        self.evidence_dir = evidence_dir if os.path.isabs(evidence_dir) else os.path.join(
            str(PROJECT_ROOT), evidence_dir)
        self.owned_entry_ids: set[str] = set()
        self.last_uploaded_name = ""
        self.last_delete_dialogs: list[str] = []
        self.last_delete_messages: list[str] = []
        self.last_row_action_dialogs: list[str] = []
        self.pinned_role: str | None = None

    # ---- session ----------------------------------------------------------------
    def open(self, url: str) -> None:
        """Role-pinned sessions navigate WITHOUT BasePage's session guard: that
        guard re-logs a dropped session in as TEST_USER, which would silently turn
        an Editor/Author step into a super-admin one. Tests re-check the signed-in
        userId before every save instead."""
        if not self.pinned_role:
            super().open(url)
            return
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page, grace_ms=1500)

    def login_as_role(self, role: str) -> str:
        """Real login as `role` in this context: "ok" / "auth_failed" / "unknown"."""
        email, password = cms_role_credentials(role)
        login = CmsLoginPage(self.page)
        login.open_login()
        try:
            login.login(email, password)
            self.pinned_role = role
            return "ok"
        except Exception:  # noqa: BLE001 — classified below (the Author renders no Control Menu)
            try:
                self.page.wait_for_load_state("load")
                if self.signed_in_user()[0]:
                    self.pinned_role = role
                    return "ok"
            except Exception:  # noqa: BLE001
                pass
            try:
                body = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001
                body = ""
            return "auth_failed" if AUTH_FAILED_BANNER_TEXT in body else "unknown"

    def signed_in_user(self) -> tuple[str, str]:
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']"""
        )
        return info[0], info[1]

    # ---- evidence -----------------------------------------------------------------
    def evidence(self, name: str, full_page: bool = True) -> str:
        """PNG under the instance's evidence folder (also attached to Allure)."""
        os.makedirs(self.evidence_dir, exist_ok=True)
        path = os.path.join(self.evidence_dir, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "photo_gallery")
        except Exception as exc:  # noqa: BLE001 — evidence only
            _logger.warning("evidence %s failed: %r", name, exc)
        return path

    # ---- navigation ------------------------------------------------------------------
    def open_create_form_en(self) -> "GalleryAdminPage":
        self.open(self._manage_url(locale="en"))
        self._entry_code = None
        self._locale = "en"
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.wait_for(timeout=90000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entry_en(self, code: str) -> "GalleryAdminPage":
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self._en(self.TITLE_KEY).wait_for(timeout=90000)
        try:
            wait_until(lambda: self.text_value(self.TITLE_KEY) != "", timeout=15.0, poll=0.5)
        except WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_list_all(self) -> "GalleryAdminPage":
        """manage-<slug> with the page-size selector on ALL and every row rendered."""
        self.open(self._manage_url(locale="en"))
        self.wait_for(f"{self.LIST_LOADED}, {self.ENTRY_COUNT}", first=True, timeout=90000)
        try:
            wait_until(lambda: self.total_entry_count() is not None, timeout=20.0, poll=0.3)
        except WaitTimeoutError:
            pass
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.first.is_visible() and select.first.input_value() != "0":
            select.first.select_option("0")
        total = self.total_entry_count()
        try:
            wait_until(lambda: total is None or self.rendered_row_count() >= total, timeout=20.0, poll=0.3)
        except WaitTimeoutError:
            _logger.warning("page-size ALL did not settle to %s rows", total)
        _dismiss_chatbot_launcher(self.page)
        return self

    def total_entry_count(self) -> int | None:
        counter = self.page.locator(self.ENTRY_COUNT)
        if counter.count() == 0:
            return None
        match = re.search(r"(\d+)\s*total", counter.first.inner_text())
        return int(match.group(1)) if match else None

    def rendered_row_count(self) -> int:
        return self.page.locator(f"{self.ENTRIES_TABLE_ROW}:has({self.LIST_LOADED})").count()

    def is_list_fully_expanded(self) -> bool:
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.first.is_visible() and select.first.input_value() != "0":
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
            raise AssertionError(f"the manage-{self.slug} list did not expand to every row; cannot snapshot ids")
        return {r["entry_id"] for r in self.list_rows()}

    def leftovers(self) -> list[dict]:
        """Read-only: rows whose title is in THIS instance's prefix."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].startswith(self.prefix)]

    # ---- identity ------------------------------------------------------------------
    def identify_created(self, title: str, ids_before: set[str]) -> GalleryEntry | None:
        """The ONE new row (id not in `ids_before`, not a seeded QCDEMO- code) whose
        Entry cell reads `title` and whose own form reads exactly `title`. None for
        zero or several matches. Read-only."""
        if not title.startswith(self.prefix):
            raise ValueError(f"{title!r} is not in the {self.prefix} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not any(r["code"].startswith(p) for p in REAL_CODE_PREFIXES)
                 and r["title"].strip() == title]
        matches = []
        for row in fresh:
            for attempt in (1, 2):  # one retry: a slow editEntry load must not orphan our record
                try:
                    self.open_entry_en(row["code"])
                    if self.text_value(self.TITLE_KEY) == title:
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — an unreadable row is not ours
                    _logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            _logger.warning("identify_created(%r): %s matches among new rows %s", title, len(matches), fresh)
            return None
        entry = GalleryEntry(title=title, entry_id=matches[0]["entry_id"], code=matches[0]["code"],
                             prefix=self.prefix, slug=self.slug)
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def adopt(self, entry: GalleryEntry) -> GalleryEntry:
        """Lets a second session (another role / the cleaner) act on a record the
        test captured. Refuses anything outside the namespace or another object."""
        if (not isinstance(entry, GalleryEntry) or not entry.in_namespace() or entry.slug != self.slug
                or not entry.title.startswith(self.prefix) or not entry.entry_id or not entry.code):
            raise ValueError(f"refusing to adopt {entry}: not a captured {self.prefix} manage-{self.slug} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def _check_owned(self, entry: GalleryEntry, what: str) -> None:
        if not isinstance(entry, GalleryEntry) or not entry.in_namespace() or entry.slug != self.slug \
                or not entry.title.startswith(self.prefix):
            raise ValueError(f"{what} refuses {entry}: not a {self.prefix} manage-{self.slug} record")
        if entry.entry_id not in self.owned_entry_ids:
            raise ValueError(f"{what} refuses {entry}: id not captured at creation by this test")

    # ---- rows -------------------------------------------------------------------------
    def _row(self, entry: GalleryEntry):
        return self.page.locator(", ".join(
            f'{self.ENTRIES_TABLE_ROW}:has([data-qc-oel-{a}="{entry.entry_id}"])' for a in self.ID_ATTRS))

    def row_for(self, entry: GalleryEntry) -> dict:
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return rows[0] if len(rows) == 1 else {}

    def row_present(self, entry: GalleryEntry) -> bool:
        return bool(self.row_for(entry))

    def row_status(self, entry: GalleryEntry) -> str:
        """Normalized workflow badge of the captured row ("" when the row is gone)."""
        row = self.row_for(entry)
        if not row:
            return ""
        raw = " ".join(row["status"].split())
        if raw.casefold() == STATUS_INACTIVE.casefold():
            return STATUS_INACTIVE
        return normalize_status(raw)

    def row_status_raw(self, entry: GalleryEntry) -> str:
        return self.row_for(entry).get("status", "")

    def row_actions(self, entry: GalleryEntry) -> list[str]:
        row = self._row(entry).first
        return [n for n in self.ROW_ACTION_NAMES if row.locator(f"[data-qc-oel-{n}]").count() > 0]

    def row_link_labels(self, entry: GalleryEntry) -> list[str]:
        return [t.strip() for t in self._row(entry).first.locator("td").last.locator("a, button")
                .all_inner_texts() if t.strip()]

    def row_has_edit_link(self, entry: GalleryEntry) -> bool:
        return self._row(entry).first.locator('a[href*="editEntry="]').count() > 0

    def row_preview_href(self, entry: GalleryEntry) -> str:
        link = self._row(entry).first.get_by_role("link", name="Preview")
        href = link.first.get_attribute("href") if link.count() else ""
        return (href if href.startswith("http") else control_panel_url(href)) if href else ""

    def run_row_action(self, entry: GalleryEntry, action: str, comment: str = "") -> list[str]:
        """Clicks ONE id-scoped workflow action on a captured record, accepting every
        native confirm()/prompt() (prompts get `comment`); returns the dialog texts.
        Destructive actions are refused (use delete_own_entry())."""
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(f"run_row_action refuses {action!r}; use delete_own_entry()")
        if action != "history":
            self._check_owned(entry, "run_row_action")
            row = self.row_for(entry)
            if not row or row["title"].strip() != entry.title:
                raise ValueError(f"run_row_action refuses {entry}: the row now reads {row}")
        control = self._row(entry).first.locator(f"[data-qc-oel-{action}]")
        if control.count() == 0:
            raise AssertionError(f"row {entry.title!r} offers no {action!r}; offered {self.row_actions(entry)}")
        messages: list[str] = []

        def _accept(dialog):
            messages.append(f"{dialog.type}: {dialog.message}")
            try:
                dialog.accept(comment) if dialog.type == "prompt" else dialog.accept()
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

    def history(self, entry: GalleryEntry) -> list[dict]:
        """Expands the captured row's History -> [{action, who, when, comment, text}]."""
        self.open_list_all()
        self._row(entry).first.locator("[data-qc-oel-history]").first.click(force=True)
        cell = self._row(entry).first.locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        try:
            wait_until(lambda: cell.count() == 1 and "Loading" not in cell.inner_text(), timeout=20.0, poll=0.5)
        except WaitTimeoutError:
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

    def history_cell_text(self, entry: GalleryEntry) -> str:
        cell = self._row(entry).first.locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        return " ".join(cell.inner_text().split()) if cell.count() else ""

    def wait_status(self, entry: GalleryEntry, expected: tuple, timeout: float = 120.0) -> str:
        seen = {"status": ""}

        def _reached() -> bool:
            self.open_list_all()
            seen["status"] = self.row_status(entry)
            return seen["status"] in expected

        try:
            wait_until(_reached, timeout=timeout, poll=3.0)
        except WaitTimeoutError:
            pass
        return seen["status"]

    # ---- guarded delete --------------------------------------------------------------
    def _delete_preconditions(self, entry: GalleryEntry) -> str:
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
        if any(row["code"].startswith(p) for p in REAL_CODE_PREFIXES):
            return f"row {entry.entry_id} has a seeded code {row['code']!r}"
        if row["title"].strip() != entry.title or row["label"].strip() != entry.title:
            return f"row {entry.entry_id} shows {row['title']!r} / label {row['label']!r}, not {entry.title!r}"
        return ""

    def delete_own_entry(self, entry: GalleryEntry) -> bool:
        """Deletes exactly the captured record or refuses (False, never raises)."""
        try:
            try:
                self._check_owned(entry, "delete_own_entry")
            except ValueError as exc:
                _logger.error("DELETE REFUSED: %s", exc)
                return False
            self.open_entry_en(entry.code)
            live = self.text_value(self.TITLE_KEY)
            if live != entry.title:
                _logger.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
                return False
            self.open_list_all()
            reason = self._delete_preconditions(entry)
            if reason:
                _logger.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            reason = self._delete_preconditions(entry)  # re-check immediately before the click
            if reason:
                _logger.error("DELETE REFUSED for %r on re-check: %s", entry, reason)
                return False
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                if entry.title in dialog.message or entry.code in dialog.message:
                    dialog.accept()
                else:
                    dialog.dismiss()

            self.page.on("dialog", _on_dialog)
            try:
                link.click(force=True)
                try:
                    wait_until(lambda: link.count() == 0 or bool(self.editbar_texts()), timeout=20.0, poll=0.5)
                except WaitTimeoutError:  # verified below
                    pass
                try:
                    self.last_delete_messages = self.editbar_texts() + self._safe_field_errors()
                except Exception:  # noqa: BLE001
                    self.last_delete_messages = []
            finally:
                self.page.remove_listener("dialog", _on_dialog)
            self.last_delete_dialogs = dialogs
            if not any(entry.title in m or entry.code in m for m in dialogs):
                _logger.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            gone = self.is_list_fully_expanded() and not self.row_present(entry)
            if gone:
                _logger.info("deleted %r", entry)
            return gone
        except Exception as exc:  # noqa: BLE001
            _logger.error("delete of %r failed: %r", entry, exc)
            return False

    # ---- workflow API (read + guarded transition) -------------------------------------
    _FETCH_JS = """async ([url, method]) => {
        const r = await fetch(url, {method, credentials: 'same-origin',
            headers: {'x-csrf-token': (window.Liferay && Liferay.authToken) || '', 'content-type': 'application/json'}});
        return {status: r.status, body: (await r.text()).slice(0, 2000)};
    }"""

    def transitions(self, entry: GalleryEntry) -> dict:
        """What the signed-in user may do to the captured record, as the manage page's
        own `/o/qc-object-status/transitions/<id>` answers it (read-only)."""
        import json  # noqa: PLC0415
        result = self.page.evaluate(self._FETCH_JS, [f"/o/qc-object-status/transitions/{entry.entry_id}", "GET"])
        try:
            return json.loads(result["body"])
        except ValueError:
            return {"_status": result["status"], "_body": result["body"]}

    def call_transition_directly(self, entry: GalleryEntry, action: str) -> dict:
        """Invokes ONE workflow transition (`publish`, `approve`, ...) straight against
        `/o/qc-object-status/<action>/<id>` — the endpoint the row actions call (live:
        Unpublish = POST /o/qc-object-status/unpublish/<id>) — bypassing the UI, for
        a captured record of this test only. Returns {status, body}."""
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(f"call_transition_directly refuses {action!r}")
        self._check_owned(entry, "call_transition_directly")
        return self.page.evaluate(self._FETCH_JS, [f"/o/qc-object-status/{action}/{entry.entry_id}", "POST"])

    def recycle_bin_items(self) -> list[str]:
        """Read-only: the 'Recycle Bin (n)' section's entry lines on the current list page."""
        bin_ = self.page.locator("[data-qc-oel-trash]")
        if bin_.count() == 0:
            return []
        text = bin_.first.evaluate("el => { el.open = true; return el.innerText; }")
        return [" ".join(t.split()) for t in text.splitlines() if "·" in t]

    # ---- field access -------------------------------------------------------------------
    def _form(self):
        return self.page.locator(self.FORM).first

    def _en(self, key: str):
        return self._form().locator(f'[name="ObjectField_{key}"]:not([type="hidden"])').first

    def _ar(self, key: str):
        return self._form().locator(f'[id="qc-ar-{key}"]').first

    def has_field(self, key: str) -> bool:
        return self._form().locator(f'[name="ObjectField_{key}"]').count() > 0

    def fill_en(self, key: str, value: str) -> "GalleryAdminPage":
        self._en(key).fill(value)
        return self

    def fill_ar(self, key: str, value: str) -> "GalleryAdminPage":
        self._ar(key).fill(value)
        return self

    def text_value(self, key: str) -> str:
        return self._en(key).input_value()

    def ar_value(self, key: str) -> str:
        return self._ar(key).input_value()

    def text_direction(self, key: str, arabic: bool = False) -> dict:
        """{dir attribute, computed direction, text-align} of the EN or AR box."""
        node = self._ar(key) if arabic else self._en(key)
        return node.evaluate(
            "el => ({dir: el.getAttribute('dir') || '', direction: getComputedStyle(el).direction,"
            " align: getComputedStyle(el).textAlign, lang: el.getAttribute('lang') || ''})")

    def fill_number(self, key: str, value: str) -> "GalleryAdminPage":  # type: ignore[override]
        self._en(key).fill(value)
        return self

    def _date_box(self, key: str):
        hidden_id = self._form().locator(f'input[type="date"][name="ObjectField_{key}"]').first.get_attribute("id")
        return self._form().locator(f'[id="qc-dtp-{hidden_id}"]').first

    def set_date(self, key: str, value: str) -> "GalleryAdminPage":
        """`value` dd/mm/yyyy, typed key by key ("" clears)."""
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

    # relationship / picklist ("select from list") fields
    def _picklist_prefix(self, key: str) -> str:
        hidden_id = self._form().locator(
            f'input[type="hidden"][name="ObjectField_{key}"]').first.get_attribute("id")
        return re.sub(r"-value-input$", "", hidden_id or "")

    def picklist_options(self, key: str) -> list[str]:
        """Every option label the select-from-list field offers (opens and closes it)."""
        prefix = self._picklist_prefix(key)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        options = self.page.locator(f'li[role="option"][id^="{prefix}-option-"]')
        toggle.click()
        try:
            options.first.wait_for(state="visible", timeout=10000)
        except Exception:  # noqa: BLE001 — an empty list is a valid answer
            pass
        labels = [(o.get_attribute("data-option-label") or o.inner_text()).strip() for o in options.all()]
        if self.page.locator(f'li[role="option"][id^="{prefix}-option-"]:visible').count():
            toggle.click()
        return labels

    def pick(self, key: str, option_label: str) -> "GalleryAdminPage":
        prefix = self._picklist_prefix(key)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        text_box = self.page.locator(f'[id="{prefix}-select-from-list-input"]')
        option = self.page.locator(f'li[role="option"][id^="{prefix}-option-"]').filter(
            has_text=re.compile(rf"^\s*{re.escape(option_label)}\s*$"))
        toggle.click()
        try:
            option.first.wait_for(state="visible", timeout=8000)
        except Exception:  # noqa: BLE001 — long lists filter as you type
            if text_box.count():
                text_box.first.fill(option_label)
            option.first.wait_for(state="visible", timeout=10000)
        option.first.click()
        hidden = self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]').first
        try:
            wait_until(lambda: hidden.input_value() != "", timeout=5.0, poll=0.25)
        except WaitTimeoutError:
            raise AssertionError(f"picking {option_label!r} in {key} left ObjectField_{key} empty") from None
        if self.page.locator(f'li[role="option"][id^="{prefix}-option-"]:visible').count():
            toggle.click()
        return self

    def picklist_value(self, key: str) -> str:
        """The stored value (id) of a select-from-list field."""
        return self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]').first.input_value()

    def picklist_text(self, key: str) -> str:
        """The label the select-from-list box shows."""
        prefix = self._picklist_prefix(key)
        box = self.page.locator(f'[id="{prefix}-select-from-list-input"]')
        return box.first.input_value() if box.count() else ""

    def set_active_status(self, active: bool) -> "GalleryAdminPage":
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

    def form_labels(self) -> list[str]:
        """Visible field labels of the authoring form, in order."""
        return [" ".join(t.split()) for t in self._form().locator("label:visible").all_inner_texts()
                if t.strip()]

    def form_text(self) -> str:
        return self._form().inner_text()

    def field_block_text(self, key: str) -> str:
        """All text inside one field's block (label, help line, current file, messages)."""
        node = self._form().locator(f'[name="ObjectField_{key}"]').first
        return node.evaluate(
            """el => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !c.querySelector('label'); i++) c = c.parentElement;
                return ((c ? c.innerText : '') + ' ' + (el.value || '')).replace(/\\s+/g, ' ').trim(); }""")

    # ---- uploads --------------------------------------------------------------------------
    def _unique_upload_copy(self, file_path: str, stem: str | None = None) -> str:
        base, ext = os.path.splitext(os.path.basename(file_path))
        folder = os.path.join(tempfile.gettempdir(), "qctest_uploads_130714")
        os.makedirs(folder, exist_ok=True)
        target = os.path.join(folder, f"{stem or base}-{uuid.uuid4().hex[:8]}{ext}")
        shutil.copyfile(file_path, target)
        return target

    def _open_picker(self, key: str) -> None:
        hidden = self._form().locator(f'input[name="ObjectField_{key}"]').first
        hidden.locator("xpath=..").get_by_role("button", name="Select File").click()

    def upload(self, key: str, file_path: str, stem: str | None = None) -> "GalleryAdminPage":
        result = self.attempt_upload(key, file_path, stem)
        if not result.get("attached"):
            raise AssertionError(f"upload of {file_path} into {key} was not attached: {result}")
        return self

    def attempt_upload(self, key: str, file_path: str, stem: str | None = None,
                       response_timeout_ms: int = 60000) -> dict:
        """Uploads a uniquely named copy through the field's Documents & Media picker
        and closes it with Add; returns evidence {file, status, success, errors,
        picker_text, add_clicked, attached, field_text}."""
        upload_path = self._unique_upload_copy(file_path, stem)
        result = {"file": os.path.basename(upload_path), "status": None, "body": "", "success": None,
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
                os.remove(upload_path)
            except OSError:
                pass
        errors = frame.locator(self.PICKER_ERROR)
        try:
            wait_until(lambda: errors.count() > 0 and any(t.strip() for t in errors.all_inner_texts()),
                       timeout=5.0, poll=0.5)
        except WaitTimeoutError:
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
                wait_until(_added, timeout=30.0, poll=1.5)
            except WaitTimeoutError:
                result["errors"] = [t.strip() for t in errors.all_inner_texts() if t.strip()]
        if modal.count():
            result["picker_evidence"] = self.evidence(f"picker_{key}_{result['file']}", full_page=False)
            self.page.keyboard.press("Escape")
            try:
                modal.wait_for(state="detached", timeout=8000)
            except Exception:  # noqa: BLE001
                _logger.warning("upload picker did not close on Escape")
        result["field_text"] = self.field_block_text(key)
        result["attached"] = os.path.splitext(result["file"])[0] in result["field_text"]
        self.last_upload_attempt = result
        return result

    def stored_file_name(self, key: str) -> str:
        """Persisted file of a reopened record ("Current file: <name> (<size>)")."""
        match = re.search(r"Current file:\s*(.+?)\s*(\(|—)", self.field_block_text(key))
        return match.group(1).strip() if match else ""

    # ---- save / publish with an outcome probe -----------------------------------------
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
            except Exception:  # noqa: BLE001 — a detached node is not an action
                continue
        return names

    def click_publish(self) -> "GalleryAdminPage":
        """The role's submit button ("Publish" for the Editor, "Submit for Review" for the Author)."""
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def click_save_as_draft(self) -> "GalleryAdminPage":
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
                window.__qcPgInvalid = []; window.__qcPgInvalidMsg = {{}};
                if (!window.__qcPgHooked) {{
                    window.__qcPgHooked = true;
                    document.addEventListener('invalid', (e) => {{
                        const t = e.target; const k = t.name || t.id || '';
                        window.__qcPgInvalid.push(k); window.__qcPgInvalidMsg[k] = t.validationMessage;
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
            return list(self.page.evaluate("() => window.__qcPgInvalid || []"))
        except Exception:  # noqa: BLE001
            return []

    def _native_messages(self) -> dict:
        try:
            return dict(self.page.evaluate("() => window.__qcPgInvalidMsg || {}"))
        except Exception:  # noqa: BLE001
            return {}

    def _refusal_shown(self) -> bool:
        try:
            return (bool(self._invalid_fields()) or bool(self._safe_field_errors())
                    or any(MSG_BLOCKED_FRAGMENT in t or "not saved" in t for t in self.editbar_texts()))
        except Exception:  # noqa: BLE001
            return False

    def _wait_for_save_outcome(self) -> None:
        started = monotonic()
        state = {"value": ""}
        settled = f"{self.LIST_LOADED}, {self.ENTRY_COUNT}, {self.SAVE_AS_DRAFT_BUTTON}"

        def _outcome() -> bool:
            if self._document_replaced():
                if self.page.locator(settled).count() > 0:
                    state["value"] = "reloaded"
                    return True
                return False
            answered = len(self._save_responses) >= len(self._save_requests)
            accepted = any(code < 400 for code in self._save_responses)
            quiet = answered and not self._navigated and monotonic() - started >= self.REFUSAL_QUIET_WINDOW_S
            if quiet and not accepted and self._refusal_shown():
                state["value"] = "refused"
                return True
            if quiet and accepted and any(t not in self._errors_before for t in self._safe_field_errors()):
                state["value"] = "refused"
                return True
            return False

        try:
            wait_until(_outcome, timeout=self.SAVE_OUTCOME_TIMEOUT_S, poll=0.5)
        except WaitTimeoutError:
            _logger.warning("save outcome did not settle; requests=%s responses=%s",
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
        return [" ".join(t.split()) for t in self.page.locator(self.EDITBAR).all_inner_texts() if t.strip()]

    def editing_bar_text(self) -> str:
        for text in self.editbar_texts():
            if text.startswith("Editing"):
                return text
        return ""

    def field_errors(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.FIELD_ERROR).all_inner_texts() if t.strip()]

    def refusal_evidence(self) -> dict:
        return {
            "invalid_fields": list(getattr(self, "last_invalid_fields", [])),
            "native_messages": dict(getattr(self, "last_native_messages", {})),
            "field_errors": self._safe_field_errors(),
            "editbar": self.editbar_texts(),
            "save_requests": list(getattr(self, "last_save_requests", [])),
            "save_responses": list(getattr(self, "last_save_responses", [])),
        }

    def all_messages_text(self) -> str:
        parts = self.editbar_texts() + self._safe_field_errors()
        parts += [m for m in getattr(self, "last_native_messages", {}).values() if m]
        return " | ".join(parts)

    def success_messages(self, expected: str, timeout: float = 15.0) -> list[str]:
        try:
            wait_until(lambda: any(expected in t for t in self.editbar_texts()), timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass
        return self.editbar_texts()

    def wait_arabic_saved(self, timeout: float = 25.0) -> str:
        """Object Authoring guide §5: on a new record the Arabic is saved a moment
        after the record. Returns MSG_ARABIC_SAVED, a 'NOT saved' note or ""."""
        seen = {"text": ""}

        def _done() -> bool:
            seen["text"] = self.page.locator("body").inner_text()
            return MSG_ARABIC_SAVED in seen["text"] or MSG_ARABIC_NOT_SAVED_FRAGMENT in seen["text"]

        try:
            wait_until(_done, timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            return ""
        return MSG_ARABIC_SAVED if MSG_ARABIC_SAVED in seen["text"] else "the Arabic content was NOT saved"

    def click_unpublish_to_edit_as_draft(self) -> list[str]:
        """The edit bar's "Unpublish to edit as draft" on an open published record of
        THIS test (the open code must be a captured id's code); returns dialog texts."""
        messages: list[str] = []

        def _accept(dialog):
            messages.append(f"{dialog.type}: {dialog.message}")
            try:
                dialog.accept()
            except Exception:  # noqa: BLE001
                pass

        button = self.page.get_by_role("button", name=re.compile(r"Unpublish to edit as draft"))
        self.page.on("dialog", _accept)
        try:
            button.first.click()
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        return messages

    # ---- preview ---------------------------------------------------------------------------
    def open_preview(self, preview_url: str, expected: list[str], timeout: float = 45.0) -> str:
        """Opens a row's Preview (public page with `qcPreview=`) in THIS signed-in
        context and waits until every `expected` text shows; returns the body text."""
        self.open(preview_url)
        state = {"text": ""}

        def _shown() -> bool:
            try:
                state["text"] = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001 — mid-render
                return False
            return all(e in state["text"] for e in expected)

        try:
            wait_until(_shown, timeout=timeout, poll=1.0)
        except WaitTimeoutError:
            pass
        return state["text"]

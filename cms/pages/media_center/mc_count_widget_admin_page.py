"""
cms/pages/media_center/mc_count_widget_admin_page.py — Media Center Count
Widget (`MediaCenterCountWidget`) Object Authoring driver + the public
summary-counts-strip reader, for PBI 130709 (suite 140368, COUNT agent).

LIVE RECON 2026-10-07 (QC Site Content Editor 156488; read-only, nothing saved):

  Manage page  /web/qatar-chamber/manage-media-center-count-widget
    ENTRY column = displayName. Five REAL rows (never edited / unpublished /
    deleted by this module): QCDEMO-130709-COUNT-01..05 = Articles (100),
    Photo Albums (200), Videos (300), Podcast (400), Publications (500), all
    PUBLISHED + Active.
    Fields (EN `ObjectField_<key>`, AR twin `#qc-ar-<key>`):
      displayName*   text, counter "n / 60" (no native maxlength), AR twin*
      contentType*   picklist Articles=articles / Photo Albums=photoAlbums /
                     Videos=videos / Podcast=podcast / Publications=publications
      icon*          attachment, accept .png,.svg, "Upload a .png,.svg no larger than 2 MB."
      unitLabel*     text, counter "n / 30", AR twin*
      displayOrder*  number (min -2147483648 — no native positive-integer rule)
      activeStatus   checkbox
    Editor buttons: "Save as Draft" / "Publish" (the cases' "Submit for
    Review" is the Author label; the Editor's privileged submit is "Publish").
    Typing a 61st character is NOT blocked: the counter turns to "61 / 60" and
    shows "61 characters — the maximum is 60. Shorten it by 1 before saving."
    Preview panel: "Field view (no page renders this Object)".

  Public page  /web/qatar-chamber/media-center (logged out, 200)
    Fragment `section.qc-mc-counts[data-qc-mcc-ready="true"]` renders cards
    `.qc-mc-counts-card` > `.qc-mc-counts-label` / `.qc-mc-counts-value`
    ("<count> <unitLabel>") / `.qc-mc-counts-badge-img` (mask-image url of the
    authored icon). Data: GET /o/c/mediacentercountwidgets/scopes/<groupId>
    (guest) + GET /o/qc-media-center-api/counts. Inactive entries are dropped
    client-side, the rest sorted numerically by displayOrder and then
    **sliced to `data-qc-mcc-max` = 5** (fragment config "maxWidgets": "5").

DELETE SAFETY: `delete_disposable_entry()` deletes ONLY a `CWEntry` this
session captured (list-id diff + exact read-back), whose logical name is in
the QCTEST-130709-CW- namespace, whose stored Display Name starts with
"QCTEST", whose code is not QCDEMO-, re-checked right before the click, and
whose confirm() names the entry. Every inherited unguarded delete is disabled.
"""

from __future__ import annotations

import os as _os
import re as _re
import shutil as _shutil
import tempfile as _tempfile
import uuid as _uuid
from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime
from datetime import timedelta as _timedelta
from datetime import timezone as _timezone

from cms.pages.components.object_authoring_page import normalize_status
from cms.pages.tenders.tender_admin_page import TenderWorkflowAdminPage
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher

logger = get_logger("mc_count_widget_admin_page")

SLUG = "media-center-count-widget"
RESOURCE = "mediacentercountwidgets"
QCTEST_PREFIX = "QCTEST-130709-CW-"
QCTEST_VALUE_PREFIX = "QCTEST"
REAL_CODE_PREFIX = "QCDEMO-"
REAL_WIDGETS = {  # code: (display name, display order) — read-only reference
    "QCDEMO-130709-COUNT-01": ("Articles", 100),
    "QCDEMO-130709-COUNT-02": ("Photo Albums", 200),
    "QCDEMO-130709-COUNT-03": ("Videos", 300),
    "QCDEMO-130709-COUNT-04": ("Podcast", 400),
    "QCDEMO-130709-COUNT-05": ("Publications", 500),
}

ROLE_EDITOR = "Site Content Editor"
ROLE_USER_IDS = {ROLE_EDITOR: "156488"}

MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_DRAFT_SAVED = "Draft saved."
MSG_ARABIC_SAVED = "Arabic content saved for this record."
MSG_ARABIC_REQUIRED = "Arabic content is required."

K_NAME = "displayName"
K_UNIT = "unitLabel"
K_ORDER = "displayOrder"
K_TYPE = "contentType"
K_ICON = "icon"
K_ACTIVE = "activeStatus"

CONTENT_TYPES = ("Articles", "Photo Albums", "Videos", "Podcast", "Publications")
CONTENT_TYPE_KEYS = {"Articles": "articles", "Photo Albums": "photoAlbums", "Videos": "videos",
                     "Podcast": "podcast", "Publications": "publications"}
ICON_LABEL = "Icon"

PUBLIC_PATH = "/web/qatar-chamber/media-center"
SUBSCRIBER_PATH = "/web/qatar-chamber/manage-newsletter-subscriber"
MANAGE_PATH = f"/web/qatar-chamber/manage-{SLUG}"

EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "mc130709", "count")


@_dataclass(frozen=True)
class CWEntry:
    """Identity of ONE count-widget record this session created.

    `logical` is the case's record name (QCTEST-130709-CW-01..04) — the
    object has no title/ERC field, so the stored Display Name (`value`, which
    every case keeps in the "QCTEST" namespace) plus the captured id/code are
    the identity."""

    logical: str
    entry_id: str
    code: str
    value: str

    def in_namespace(self) -> bool:
        return (self.logical.startswith(QCTEST_PREFIX)
                and self.value.strip().upper().startswith(QCTEST_VALUE_PREFIX)
                and bool(self.entry_id) and bool(self.code)
                and not self.code.upper().startswith(REAL_CODE_PREFIX)
                and self.code not in REAL_WIDGETS)


def _evidence_path(name: str) -> str:
    _os.makedirs(EVIDENCE_DIR, exist_ok=True)
    return _os.path.join(EVIDENCE_DIR, _re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")


class McCountWidgetAdminPage(TenderWorkflowAdminPage):
    """`manage-media-center-count-widget` driver on the confirmed-live Object
    Authoring mechanics of TenderFieldsAdminPage/TenderWorkflowAdminPage
    (role login, Load-All list, id-scoped row actions, save-outcome probe,
    `ObjectField_<key>` / `qc-ar-<key>` field access, picklists, uploads)."""

    FORM = 'form:has([name="ObjectField_displayName"])'
    EVIDENCE_DIR = EVIDENCE_DIR
    SAVE_REQUEST_PATTERN = _re.compile(rf"edit_info_item|/o/c/{RESOURCE}")

    _ROWS_FULL_JS = """(attrs) => [...document.querySelectorAll('table tbody tr')].map(r => {
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
                    modified: tds[2] ? tds[2].innerText.trim() : '',
                    delete_id: del ? del.getAttribute('data-qc-oel-delete') : '',
                    label: del ? (del.getAttribute('data-qc-oel-label') || '') : ''};
        }).filter(r => r.entry_id)"""

    def __init__(self, page):
        super().__init__(page)
        self.slug = SLUG

    # ---- navigation -----------------------------------------------------------
    def open_entry_en(self, code: str) -> "McCountWidgetAdminPage":
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self.page.locator(f'{self.FORM} [name="ObjectField_{K_NAME}"]').first.wait_for(
            state="attached", timeout=90000)
        try:
            wait_until(lambda: self.editing_bar_text() != "" and self.text_value(K_ORDER) != "",
                       timeout=20.0, poll=0.5)
        except WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    # ---- list -------------------------------------------------------------------
    def rows_full(self) -> list[dict]:
        return self.page.evaluate(self._ROWS_FULL_JS, list(self.ID_ATTRS))

    def row_of(self, entry: CWEntry) -> dict:
        rows = [r for r in self.rows_full() if r["entry_id"] == entry.entry_id]
        return rows[0] if len(rows) == 1 else {}

    def row_status_of(self, entry: CWEntry) -> str:
        row = self.row_of(entry)
        return normalize_status(row["status"]) if row else ""

    def wait_row_status(self, entry: CWEntry, expected: tuple, timeout: float = 120.0) -> str:
        seen = {"status": ""}

        def _reached() -> bool:
            self.open_list_all()
            seen["status"] = self.row_status_of(entry)
            return seen["status"] in expected

        try:
            wait_until(_reached, timeout=timeout, poll=3.0)
        except WaitTimeoutError:
            pass
        return seen["status"]

    def qctest_rows(self) -> list[dict]:
        """Read-only: rows whose ENTRY text starts with QCTEST (leftover check)."""
        self.open_list_all()
        return [r for r in self.rows_full() if r["title"].strip().upper().startswith(QCTEST_VALUE_PREFIX)]

    # ---- identity / capture --------------------------------------------------------
    def identify_created(self, logical: str, value: str, ids_before: set[str]) -> CWEntry | None:
        """The ONE new row (id not in `ids_before`, not a QCDEMO- code) whose
        ENTRY cell reads `value` and whose own form reads it back exactly."""
        if not logical.startswith(QCTEST_PREFIX) or not value.upper().startswith(QCTEST_VALUE_PREFIX):
            raise ValueError(f"{logical!r}/{value!r} is not a QCTEST-130709-CW- record")
        self.open_list_all()
        fresh = [r for r in self.rows_full() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].upper().startswith(REAL_CODE_PREFIX) and r["title"].strip() == value.strip()]
        matches = []
        for row in fresh:
            for attempt in (1, 2):
                try:
                    self.open_entry_en(row["code"])
                    if self.text_value(K_NAME).strip() == value.strip():
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — an unreadable row is not ours
                    logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            logger.warning("identify_created(%r): %s matches among new rows %s", value, len(matches), fresh)
            return None
        entry = CWEntry(logical=logical, entry_id=matches[0]["entry_id"], code=matches[0]["code"],
                        value=value.strip())
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def new_rows_since(self, ids_before: set[str]) -> list[dict]:
        """Read-only: rows created after `ids_before` (non-QCDEMO)."""
        self.open_list_all()
        return [r for r in self.rows_full() if r["entry_id"] not in ids_before
                and not r["code"].upper().startswith(REAL_CODE_PREFIX)]

    def adopt_cw(self, entry: CWEntry) -> CWEntry:
        if not isinstance(entry, CWEntry) or not entry.in_namespace():
            raise ValueError(f"refusing to adopt {entry}: not a captured QCTEST-130709-CW- record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    # ---- form ------------------------------------------------------------------------
    def fill_widget(self, data: dict) -> "McCountWidgetAdminPage":
        """Keys: displayName(_ar), unitLabel(_ar), contentType (option label),
        displayOrder, icon_file (path), activeStatus (bool). None/absent = untouched."""
        for key in (K_NAME, K_UNIT):
            if data.get(key) is not None:
                self.fill_en(key, str(data[key]))
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, str(data[f"{key}_ar"]))
        if data.get(K_TYPE):
            self.pick(K_TYPE, data[K_TYPE])
        if data.get(K_ORDER) is not None:
            self.fill_number_key(K_ORDER, str(data[K_ORDER]))
        if data.get("icon_file"):
            self.upload(K_ICON, data["icon_file"])
        if data.get(K_ACTIVE) is not None:
            self.set_active_status(bool(data[K_ACTIVE]))
        return self

    ADD_NEW_CONTROL = 'button:visible, a:visible'
    ADD_NEW_RE = _re.compile(r"^\s*\+?\s*Add New", _re.I)

    def add_new_offered(self) -> list[str]:
        """Visible '+ Add New' controls on the manage list (149912: must be none)."""
        texts = [(t or "").strip() for t in self.page.locator(self.ADD_NEW_CONTROL).all_inner_texts()]
        return [t for t in texts if self.ADD_NEW_RE.search(t)]

    def tab_through_content_type(self, presses: int = 2) -> "McCountWidgetAdminPage":
        """149914 retest: click in 'Display Name — العربية', press Tab `presses` times
        (into and out of the Content Type picklist) — real keyboard focus moves."""
        self._ar(K_NAME).click()
        for _ in range(presses):
            self.page.keyboard.press("Tab")
        return self

    def read_widget(self) -> dict:
        return {K_NAME: self.text_value(K_NAME), f"{K_NAME}_ar": self.ar_value(K_NAME),
                K_UNIT: self.text_value(K_UNIT), f"{K_UNIT}_ar": self.ar_value(K_UNIT),
                K_TYPE: self.picklist_value(K_TYPE), K_ORDER: self.text_value(K_ORDER),
                "icon_current": self.stored_file_name(K_ICON), K_ACTIVE: self.active_status_stored()}

    def type_text(self, key: str, text: str, arabic: bool = False) -> "McCountWidgetAdminPage":
        """Select-all + Delete, then TYPE `text` key by key (counter handlers see real keys)."""
        box = self._ar(key) if arabic else self._en(key)
        box.click()
        box.press("Control+A")
        box.press("Delete")
        if text:
            self.page.keyboard.type(text)
        # Leaves the field with blur(), NOT Tab: LIVE 2026-10-08 a Tab out of
        # "Display Name — العربية" lands on the Content Type picklist and that
        # focus alone wipes its value (recorded as a product finding).
        box.evaluate("el => { el.dispatchEvent(new Event('change', {bubbles: true})); el.blur(); }")
        return self

    def field_dir(self, key: str, arabic: bool = False) -> str:
        box = self._ar(key) if arabic else self._en(key)
        return box.evaluate("el => getComputedStyle(el).direction")

    def counter_reading(self, key: str, arabic: bool = False) -> tuple[int, int] | None:
        """(current, limit) of the live "<len> / N" counter under the field."""
        box = self._ar(key) if arabic else self._en(key)
        text = box.evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 4 && c; i++, c = c.parentElement) {
                           const m = (c.innerText || '').match(/(\\d+)\\s*\\/\\s*(\\d+)/); if (m) return m[1] + '/' + m[2]; }
                       return ''; }""")
        if not text:
            return None
        cur, lim = text.split("/")
        return int(cur), int(lim)

    def native_max_length(self, key: str, arabic: bool = False) -> int:
        box = self._ar(key) if arabic else self._en(key)
        return int(box.evaluate("el => el.maxLength"))

    def field_block_text(self, key: str, arabic: bool = False) -> str:
        box = self._ar(key) if arabic else self._en(key)
        return box.evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 4 && c; i++, c = c.parentElement) {
                           if (/\\d+\\s*\\/\\s*\\d+/.test(c.innerText || '')) return c.innerText.replace(/\\s+/g, ' ').trim(); }
                       return (el.parentElement.innerText || '').replace(/\\s+/g, ' ').trim(); }""")

    def content_type_options(self) -> list[str]:
        """Labels the Content Type dropdown offers (opens and closes it)."""
        prefix = self._picklist_prefix(K_TYPE)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        toggle.click()
        option = self.page.locator(f'li[role="option"][id^="{prefix}-option-"]')
        option.first.wait_for(state="visible", timeout=10000)
        labels = [(o.get_attribute("data-option-label") or o.inner_text()).strip() for o in option.all()]
        self.page.keyboard.press("Escape")
        return labels

    def content_type_display_text(self) -> str:
        prefix = self._picklist_prefix(K_TYPE)
        return self.page.locator(f'[id="{prefix}-select-from-list-input"]').first.input_value()

    def form_controls(self) -> list[dict]:
        """Every visible, user-editable control of the entry form with its label."""
        return self._form().evaluate(
            """form => [...form.querySelectorAll('input, select, textarea, [contenteditable="true"]')]
                .filter(el => el.type !== 'hidden' && el.name !== 'q')
                .filter(el => el.offsetParent !== null || el.type === 'checkbox' || el.classList.contains('sr-only')
                              || el.classList.contains('file-upload-input'))
                .map(el => { let c = el.parentElement, label = '';
                    for (let i = 0; i < 7 && c && !label; i++, c = c.parentElement) {
                        const l = c.querySelector('label'); if (l) label = l.innerText.replace(/\\s+/g, ' ').trim(); }
                    return {tag: el.tagName.toLowerCase(), type: el.type || '', name: el.name || '', id: el.id || '',
                            label: label, readonly: !!el.readOnly, disabled: !!el.disabled}; })""")

    def upload_block_text(self, key: str) -> str:  # type: ignore[override]
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return node.evaluate(
            """(el, label) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !(c.innerText || '').includes(label); i++) c = c.parentElement;
                return ((c ? c.innerText : '') + ' ' + (el.value || '')).replace(/\\s+/g, ' ').trim(); }""",
            ICON_LABEL)

    def stored_file_name(self, key: str) -> str:  # type: ignore[override]
        """'Current file: <name> (<size>)' -> <name>. Greedy up to the LAST '(' so a
        Liferay de-duplicated name like 'qctest-cw-icon-2 (1).svg' (2026-10-12) stays whole."""
        match = _re.search(r"Current file:\s*(.+)\s*\(\s*[\d.,]+\s*[KMG]?B\s*\)", self.upload_block_text(key))
        return match.group(1).strip() if match else ""

    def icon_selected_text(self) -> str:
        """The field's own filename readout (`<strong role=textbox aria-label="Icon">`)."""
        node = self._form().locator(f'strong[aria-label="{ICON_LABEL}"]')
        return node.first.inner_text().strip() if node.count() else ""

    @staticmethod
    def _unique_upload_copy(file_path: str, stem: str | None = None) -> str:  # type: ignore[override]
        """Keeps the fixture's REAL file name (the cases assert on it) inside a
        unique temp folder, so parallel copies never collide on disk."""
        folder = _os.path.join(_tempfile.gettempdir(), "qctest_uploads_130709_cw", _uuid.uuid4().hex[:8])
        _os.makedirs(folder, exist_ok=True)
        target = _os.path.join(folder, _os.path.basename(file_path))
        _shutil.copyfile(file_path, target)
        return target

    def editbar_names(self, value: str, status: str) -> bool:
        bar = self.editing_bar_text()
        return value in bar and f"({status})".casefold() in bar.casefold()

    def wait_arabic_saved(self, timeout: float = 20.0) -> bool:
        try:
            wait_until(lambda: MSG_ARABIC_SAVED in self.rendered_body_text()
                       or "Arabic content was not" in self.rendered_body_text(), timeout=timeout, poll=0.5)
            return MSG_ARABIC_SAVED in self.rendered_body_text()
        except WaitTimeoutError:
            return False

    def evidence(self, name: str, full_page: bool = True) -> str:  # type: ignore[override]
        path = _evidence_path(name)
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "mc130709-count")
        except Exception as exc:  # noqa: BLE001 — evidence only
            logger.warning("evidence %s failed: %r", name, exc)
        return path

    # ---- guarded delete -----------------------------------------------------------------
    def _delete_preconditions(self, entry: CWEntry) -> str:  # type: ignore[override]
        if not self.is_list_fully_expanded():
            return f"list not fully expanded ({self.rendered_row_count()} of {self.total_entry_count()})"
        links = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
        if links.count() != 1:
            return f"{links.count()} delete links carry id {entry.entry_id}"
        rows = [r for r in self.rows_full() if r["delete_id"] == entry.entry_id]
        if len(rows) != 1:
            return f"{len(rows)} rows carry delete id {entry.entry_id}"
        row = rows[0]
        if row["code"] != entry.code or row["code"].upper().startswith(REAL_CODE_PREFIX) or row["code"] in REAL_WIDGETS:
            return f"row {entry.entry_id} points at {row['code']!r}, not the captured {entry.code!r}"
        if not row["title"].strip().upper().startswith(QCTEST_VALUE_PREFIX) \
                or row["label"].strip() != row["title"].strip():
            return f"row {entry.entry_id} shows {row['title']!r} / label {row['label']!r} — not a QCTEST value"
        return ""

    def make_identity_deletable(self, entry: CWEntry) -> bool:
        """When a test emptied/changed the Display Name of its OWN captured record
        to something outside the QCTEST namespace (an accepted negative save),
        put a QCTEST value back first so the guarded delete can re-verify it."""
        self.open_entry_en(entry.code)
        current = self.text_value(K_NAME).strip()
        if current.upper().startswith(QCTEST_VALUE_PREFIX):
            return True
        self.open_list_all()
        row = self.row_of(entry)
        if not row or row["code"] != entry.code:
            return False
        self.open_entry_en(entry.code)
        self.fill_en(K_NAME, f"{entry.logical} cleanup")
        self.click_publish()
        if not self.save_went_through():
            self.open_entry_en(entry.code)
            self.click_save_as_draft()
        self.open_entry_en(entry.code)
        return self.text_value(K_NAME).strip().upper().startswith(QCTEST_VALUE_PREFIX)

    def delete_disposable_entry(self, entry: CWEntry) -> bool:  # type: ignore[override]
        """Deletes exactly the captured record or refuses (False, never raises)."""
        try:
            if not isinstance(entry, CWEntry) or not entry.in_namespace() \
                    or entry.entry_id not in self.owned_entry_ids:
                logger.error("DELETE REFUSED: %r is not a captured QCTEST-130709-CW- record", entry)
                return False
            self.open_entry_en(entry.code)
            live = self.text_value(K_NAME).strip()
            if not live.upper().startswith(QCTEST_VALUE_PREFIX):
                logger.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
                return False
            self.open_list_all()
            reason = self._delete_preconditions(entry) or self._delete_preconditions(entry)
            if reason:
                logger.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            row = self.row_of(entry)
            names = [n for n in (row.get("title", "").strip(), entry.code) if n]
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                dialog.accept() if any(n in dialog.message for n in names) else dialog.dismiss()

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
                logger.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            gone = self.is_list_fully_expanded() and not any(
                r["entry_id"] == entry.entry_id for r in self.rows_full())
            if gone:
                self.owned_entry_ids.discard(entry.entry_id)
            return gone
        except Exception as exc:  # noqa: BLE001
            logger.error("delete of %r failed: %r", entry, exc)
            return False

    # ---- inherited tender-specific / unguarded helpers are not valid here ------------------
    def _not_cw(self, *_a, **_k):
        raise NotImplementedError("tender-specific or unguarded helper; use the McCountWidgetAdminPage API")

    fill_tender = fill_tender_a = read_tender = a_tender_data = _not_cw
    identify_created_a = adopt_a = delete_own_entry = a_leftovers = b_leftovers = _not_cw
    row_status_a = wait_status = fill_reference_number = fill_valid_form = _not_cw
    row_status_text_for_reference = upload_tender_document = upload_boq = adopt = _not_cw
    delete_entry_by_code = delete_entry_by_title = delete_all_entries_by_title = _not_cw


def parse_row_modified(text: str) -> _datetime | None:
    """'10/7/2026, 2:45:16 PM' -> naive datetime (None when unparseable)."""
    for fmt in ("%m/%d/%Y, %I:%M:%S %p", "%m/%d/%Y, %H:%M:%S", "%d/%m/%Y, %H:%M"):
        try:
            return _datetime.strptime(" ".join((text or "").split()), fmt)
        except ValueError:
            continue
    return None


def is_current_time(stamp: _datetime | None, tolerance_min: int = 15) -> bool:
    """True when `stamp` is within `tolerance_min` of now, read either as this
    machine's local time or as Qatar time (UTC+3) — the list renders one of them."""
    if stamp is None:
        return False
    now_local = _datetime.now()
    now_qatar = _datetime.now(_timezone.utc).replace(tzinfo=None) + _timedelta(hours=3)
    return any(abs((stamp - n).total_seconds()) <= tolerance_min * 60 for n in (now_local, now_qatar))


# =============================================================================
# Public Media Center summary counts strip — always a fresh LOGGED-OUT context
# =============================================================================
class McCountsPublicView(BasePage):
    """Read-only reads of the public counts strip and its guest data feed."""

    STRIP = "section.qc-mc-counts"
    STRIP_READY = 'section.qc-mc-counts[data-qc-mcc-ready="true"]'

    _READ_JS = """() => {
        const root = document.querySelector('section.qc-mc-counts');
        const vw = document.documentElement.clientWidth;
        if (!root) return {present: false, cards: [], viewport: vw};
        const cards = [...root.querySelectorAll('.qc-mc-counts-card')].map((c, i) => {
            const label = c.querySelector('.qc-mc-counts-label'), value = c.querySelector('.qc-mc-counts-value');
            const img = c.querySelector('.qc-mc-counts-badge-img');
            const badge = c.querySelector('.qc-mc-counts-badge');
            const box = (el) => { if (!el) return {}; const r = el.getBoundingClientRect(), s = getComputedStyle(el);
                return {left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height,
                        scroll_width: el.scrollWidth, client_width: el.clientWidth, scroll_height: el.scrollHeight,
                        client_height: el.clientHeight, overflow: s.overflow, text_overflow: s.textOverflow,
                        white_space: s.whiteSpace, direction: s.direction, text_align: s.textAlign}; };
            const icon = img ? (img.style.maskImage || img.style.webkitMaskImage || '') : '';
            return {index: i, label: label ? label.textContent : '', value: value ? value.textContent : '',
                    icon_url: icon, has_inline_svg: !!(badge && badge.querySelector('svg')),
                    is_link: !!c.closest('a') || !!c.querySelector('a'),
                    label_box: box(label), value_box: box(value), card_box: box(c), badge_box: box(badge)};
        });
        return {present: true, ready: root.getAttribute('data-qc-mcc-ready') === 'true',
                max: root.getAttribute('data-qc-mcc-max'), hidden: root.hidden, dir: root.getAttribute('dir'),
                lang: document.documentElement.getAttribute('lang') || '', cards: cards, viewport: vw,
                page_scroll_width: document.documentElement.scrollWidth,
                list_box: (() => { const l = root.querySelector('.qc-mc-counts-list'); if (!l) return {};
                    const r = l.getBoundingClientRect(); return {left: r.left, right: r.right, width: r.width}; })()};
    }"""

    def open_hub(self, locale: str = "en") -> "McCountsPublicView":
        self.open(web_url(PUBLIC_PATH, locale=locale))
        self.page.locator(self.STRIP).first.wait_for(state="attached", timeout=60000)
        try:
            self.page.locator(self.STRIP_READY).first.wait_for(state="attached", timeout=30000)
            wait_until(lambda: self.read()["cards"] or self.read().get("hidden"), timeout=20.0, poll=0.5)
        except Exception:  # noqa: BLE001 — the caller asserts on read()
            pass
        return self

    def read(self) -> dict:
        return self.page.evaluate(self._READ_JS)

    def scope_group_id(self) -> str:
        return str(self.page.evaluate(
            "() => (window.Liferay && Liferay.ThemeDisplay) ? String(Liferay.ThemeDisplay.getScopeGroupId()) : ''"))

    def guest_entries(self, locale: str = "en") -> list[dict]:
        """What the strip's own data call returns to THIS (logged-out) context."""
        gid = self.scope_group_id() or "37246"
        resp = self.page.request.get(
            web_url(f"/o/c/{RESOURCE}/scopes/{gid}?pageSize=50"),
            headers={"Accept": "application/json", "Accept-Language": "ar-SA" if locale == "ar" else "en-US"})
        if not resp.ok:
            return [{"error": resp.status}]
        out = []
        for item in resp.json().get("items", []):
            ctype = item.get(K_TYPE) or {}
            icon = item.get(K_ICON) or {}
            out.append({"id": str(item.get("id")), "erc": item.get("externalReferenceCode"),
                        "status": (item.get("status") or {}).get("label"),
                        K_NAME: item.get(K_NAME), K_UNIT: item.get(K_UNIT),
                        K_ORDER: item.get(K_ORDER), K_ACTIVE: item.get(K_ACTIVE),
                        K_TYPE: ctype.get("key") if isinstance(ctype, dict) else ctype,
                        "icon_name": icon.get("name") if isinstance(icon, dict) else ""})
        return out

    def counts(self) -> dict:
        resp = self.page.request.get(web_url("/o/qc-media-center-api/counts"), headers={"Accept": "application/json"})
        return resp.json() if resp.ok else {"error": resp.status}

    def poll(self, predicate, timeout: float = 30.0, locale: str = "en") -> tuple[dict, float, bool]:
        """Reloads the hub until `predicate(read())` holds. (state, seconds, held)."""
        started = _datetime.now()
        state = {"value": {}}

        def _ok() -> bool:
            self.open_hub(locale)
            state["value"] = self.read()
            return bool(predicate(state["value"]))

        held = True
        try:
            wait_until(_ok, timeout=timeout, poll=2.0)
        except WaitTimeoutError:
            held = False
        return state["value"], (_datetime.now() - started).total_seconds(), held

    def evidence(self, name: str, full_page: bool = True) -> str:
        path = _evidence_path(name)
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "mc130709-count")
        except Exception as exc:  # noqa: BLE001
            logger.warning("evidence %s failed: %r", name, exc)
        return path

    def strip_evidence(self, name: str) -> str:
        """Screenshot of just the counts strip (falls back to the viewport)."""
        path = _evidence_path(name)
        try:
            strip = self.page.locator(self.STRIP).first
            strip.scroll_into_view_if_needed(timeout=5000)
            strip.screenshot(path=path)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            with open(path, "rb") as handle:
                attach_screenshot(handle.read(), name, "mc130709-count")
        except Exception:  # noqa: BLE001
            return self.evidence(name, full_page=False)
        return path

    # ---- anonymous access probe (no re-authentication path on purpose) -----------------
    def anonymous_probe(self, path: str) -> dict:
        """Loads a staff URL with a raw goto — BasePage.open() would re-authenticate
        a Control-Panel URL, which is exactly what this check must not do."""
        resp = self.page.goto(web_url(path), wait_until="domcontentloaded", timeout=60000)
        try:
            self.page.wait_for_load_state("load", timeout=15000)
        except Exception:  # noqa: BLE001
            pass
        return self.page.evaluate(
            """() => ({url: location.href, title: document.title,
                       signed_in: !!(window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn()),
                       object_fields: document.querySelectorAll('[name^="ObjectField_"]').length,
                       entry_rows: document.querySelectorAll('[data-qc-oel-delete], [data-qc-oel-history], [data-qc-oel-view]').length,
                       entry_count: (document.querySelector('[data-qc-oel-count]') || {innerText: ''}).innerText,
                       emails: (document.body.innerText.match(/[\\w.+-]+@[\\w-]+\\.[\\w.]+/g) || []).slice(0, 20),
                       text: document.body.innerText.replace(/\\s+/g, ' ').slice(0, 600)})""") | {
            "status": resp.status if resp else None}


# =============================================================================
# REAL widget snapshot -> edit -> restore (user approval 2026-10-12, rules 4b)
# =============================================================================
# The public counts strip is FIXED at the five real widgets by design, so the
# public steps of the field cases are verified on a REAL widget inside a
# guarded window: per-record lock -> API snapshot -> (concurrency re-check
# before every edit) -> UI edit(s) as the Editor -> logged-out check ->
# concurrency re-check -> exact restore through the same PUT the authoring
# page sends on Publish -> re-read -> diff (must be empty). Never unpublish,
# never delete. If anyone else changed the record inside the window, STOP and
# report — never overwrite.
import contextlib as _contextlib  # noqa: E402
import json as _json  # noqa: E402

SCOPE_ID = "37246"
REAL_IDS = {"QCDEMO-130709-COUNT-01": "206376", "QCDEMO-130709-COUNT-02": "206396",
            "QCDEMO-130709-COUNT-03": "206416", "QCDEMO-130709-COUNT-04": "206436",
            "QCDEMO-130709-COUNT-05": "206456"}
_PUT_KEYS = ("defaultLanguageId", "externalReferenceCode", "friendlyUrlPath", "friendlyUrlPath_i18n", "id",
             "keywords", "objectEntryFolderExternalReferenceCode", "objectEntryFolderId", "scopeId", "scopeKey",
             "systemProperties", "taxonomyCategoryBriefs", K_ACTIVE, f"{K_NAME}_i18n", K_UNIT, K_NAME, K_ORDER,
             K_ICON, K_TYPE, f"{K_UNIT}_i18n")
VOLATILE_KEYS = ("dateModified", "actions", "creator", "dateCreated")
_LOCK_DIR = _os.path.join(_os.getenv(
    "QC_MC_COUNT_SCRATCH_DIR",
    r"C:\Users\HP\AppData\Local\Temp\claude\d--Qatar-Chamber-QaterChamber-main"
    r"\de2eae66-6f02-4a22-8869-a22476b25d22\scratchpad"), "locks")
EDITOR_USER_ID = "156488"


class ConcurrentChangeError(AssertionError):
    """Someone other than this test changed the real record inside the window."""


def comparable(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in VOLATILE_KEYS}


def record_diff(before: dict, after: dict) -> list[str]:
    a, b = comparable(before), comparable(after)
    return [f"{k}: {_json.dumps(a.get(k), ensure_ascii=False)} -> {_json.dumps(b.get(k), ensure_ascii=False)}"
            for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def real_widget_get(drv: "McCountWidgetAdminPage", code: str) -> dict:
    """Stored state of a real widget (Editor session, read-only GET)."""
    url = f"/o/c/{RESOURCE}/scopes/{SCOPE_ID}/by-external-reference-code/{code}?nestedFields={K_ICON}"
    body = [0, ""]
    for attempt in range(1, 5):
        try:
            drv.page.wait_for_function("() => window.Liferay && Liferay.authToken", timeout=20000)
            body = drv.page.evaluate(
                """async (u) => { const r = await fetch(u, {headers: {'Accept': 'application/json',
                        'x-csrf-token': Liferay.authToken}}); return [r.status, await r.text()]; }""", url)
            if body[0] == 200:
                break
        except Exception as exc:  # noqa: BLE001 — navigation in flight; retried
            logger.warning("real widget GET attempt %s: %r", attempt, exc)
        drv.open_list_all()
    if body[0] != 200:
        raise AssertionError(f"GET {code} returned {body[0]}: {body[1][:200]}")
    data = _json.loads(body[1])
    data.pop("actions", None)
    return data


class RealWidgetWindow:
    """One guarded edit window on ONE real widget (see block comment above)."""

    def __init__(self, drv: "McCountWidgetAdminPage", code: str, tag: str):
        if code not in REAL_IDS:
            raise ValueError(f"{code} is not one of the five real count widgets")
        self.drv, self.code, self.entry_id, self.tag = drv, code, REAL_IDS[code], tag
        self.lock_path = _os.path.join(_LOCK_DIR, f"mc_count_{self.entry_id}.lock")
        self.token = f"COUNT {tag} {_datetime.now().isoformat(timespec='seconds')} pid={_os.getpid()}"
        self.snapshot: dict = {}
        self.last_ours: dict = {}
        self.intended: set = set()   # field names THIS test may have written (marked BEFORE the save)
        self.restore_response = None
        self.diff: list[str] | None = None
        self.files: dict = {}

    # ---- lock ---------------------------------------------------------------
    def _acquire(self, timeout_s: float = 900.0) -> None:
        _os.makedirs(_LOCK_DIR, exist_ok=True)

        def _try() -> bool:
            try:
                fd = _os.open(self.lock_path, _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY)
            except FileExistsError:
                return False
            with _os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(self.token)
            return True

        try:
            wait_until(_try, timeout=timeout_s, poll=3.0)
        except WaitTimeoutError:
            raise TimeoutError(f"{self.lock_path} still held after {timeout_s:.0f}s") from None

    def _mine(self) -> bool:
        try:
            with open(self.lock_path, encoding="utf-8") as handle:
                return handle.read().strip() == self.token
        except OSError:
            return False

    def _release(self) -> None:
        if self._mine():
            _os.remove(self.lock_path)

    def _require(self) -> None:
        if not self._mine():
            raise PermissionError(f"refusing to change {self.code} without holding {self.lock_path}")
        uid = self.drv.signed_in_user()[0]
        if uid != EDITOR_USER_ID:
            raise PermissionError(f"refusing to change {self.code}: session is userId {uid!r}, not the Editor")

    def _save(self, name: str, data) -> str:
        _os.makedirs(EVIDENCE_DIR, exist_ok=True)
        path = _os.path.join(EVIDENCE_DIR, f"{self.tag}_{self.entry_id}_{name}.json")
        with open(path, "w", encoding="utf-8") as handle:
            _json.dump(data, handle, ensure_ascii=False, indent=1, default=str)
        self.files[name] = path
        return path

    # ---- window -------------------------------------------------------------
    def begin(self) -> "RealWidgetWindow":
        self._acquire()
        try:
            self.drv.open_list_all()
            self.snapshot = real_widget_get(self.drv, self.code)
            if str(self.snapshot.get("id")) != self.entry_id \
                    or self.snapshot.get("externalReferenceCode") != self.code:
                raise AssertionError(f"snapshot of {self.code} does not carry id {self.entry_id}")
        except Exception:
            self._release()
            raise
        self.last_ours = self.snapshot
        self._save("snapshot", self.snapshot)
        return self

    def check_untouched(self, when: str) -> None:
        """Re-reads the record; it must equal the last state THIS test produced."""
        current = real_widget_get(self.drv, self.code)
        # A save of ours that landed before after_edit() could record it is
        # not "someone else": diffs on fields we intended to write are ours.
        changed = [d for d in record_diff(self.last_ours, current)
                   if not any(d.startswith(f"{k}:") or d.startswith(f"{k}_") for k in self.intended)]
        if changed:
            self._save(f"concurrent_change_{when}", {"expected": self.last_ours, "found": current, "diff": changed})
            raise ConcurrentChangeError(f"{self.code} was changed by someone else before {when}: {changed}")

    def mark_intent(self, data: dict | None) -> None:
        """Call BEFORE clicking Publish with the keys about to be written."""
        self.intended.update(k.removesuffix("_ar") for k in (data or {}))
        self.intended.update({"status", "dateModified"})

    def before_edit(self) -> None:
        self._require()
        self.check_untouched("edit")

    def after_edit(self) -> None:
        """Records the state THIS test produced, once the workflow has settled
        (a Publish reads "pending" for a few seconds before auto-approval)."""
        state = {"rec": {}}

        def _settled() -> bool:
            state["rec"] = real_widget_get(self.drv, self.code)
            return state["rec"].get("status", {}).get("code") == 0

        try:
            wait_until(_settled, timeout=180.0, poll=5.0)
        except WaitTimeoutError:
            logger.error("%s did not settle to approved after the edit: %s", self.code, state["rec"].get("status"))
        self.last_ours = state["rec"]

    def open_for_edit(self) -> None:
        """Concurrency check, then opens the real record's form."""
        self.before_edit()
        self.drv.open_entry_en(self.code)
        if self.drv.text_value(K_ORDER) == "" and self.drv.text_value(K_NAME) == "":
            raise AssertionError(f"{self.code} form did not load")

    def restore(self) -> list[str]:
        self._require()
        self.check_untouched("restore")
        body = {k: self.snapshot[k] for k in _PUT_KEYS if k in self.snapshot}
        body["status"] = {"code": self.snapshot.get("status", {}).get("code", 0)}
        url = f"/o/c/{RESOURCE}/{self.entry_id}"
        self.drv.page.wait_for_function("() => window.Liferay && Liferay.authToken", timeout=30000)
        result = self.drv.page.evaluate(
            """async ([u, b]) => { const r = await fetch(u, {method: 'PUT', body: JSON.stringify(b),
                    headers: {'Content-Type': 'application/json', 'Accept': 'application/json',
                              'x-csrf-token': Liferay.authToken}});
                return [r.status, (await r.text()).slice(0, 300)]; }""", [url, body])
        self.restore_response = result
        # LIVE 2026-10-12: the PUT passes through the editorial workflow — the
        # record reads "pending" for a few seconds, then the Editor's
        # privileged route approves it. Diff only once the status is back.
        state = {"after": {}}

        def _settled() -> bool:
            state["after"] = real_widget_get(self.drv, self.code)
            return state["after"].get("status", {}).get("code") == self.snapshot.get("status", {}).get("code")

        try:
            wait_until(_settled, timeout=180.0, poll=5.0)
        except WaitTimeoutError:
            logger.error("%s status did not return to %s after restore", self.code, self.snapshot.get("status"))
        after = state["after"]
        self.diff = record_diff(self.snapshot, after)
        self._save("restore_diff", {"put": result, "diff": self.diff, "after": after})
        return self.diff

    def end(self) -> None:
        self._release()


@_contextlib.contextmanager
def real_widget_window(drv: "McCountWidgetAdminPage", code: str, tag: str):
    """Yields a begun RealWidgetWindow; restores in `finally` unless another
    actor changed the record (then it stops and reports, never overwrites)."""
    window = RealWidgetWindow(drv, code, tag).begin()
    try:
        yield window
    finally:
        try:
            diff = window.restore()
            if diff:
                raise AssertionError(f"RESTORE DIFF NOT EMPTY on {code}: {diff} "
                                     f"(see {window.files.get('restore_diff')})")
        finally:
            window.end()

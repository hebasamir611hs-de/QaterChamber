"""
cms/pages/media_center/mc_quick_access_card_admin_page.py — Media Center
Quick Access Card (PBI 130709) Object Authoring Page Object + the logged-out
public "Explore the hub" grid reader.

LIVE RECON 2026-10-07 (Site Content Editor 156488, read-only):
  manage page  /web/qatar-chamber/manage-media-center-quick-access-card
  headless     mediacenterquickaccesscards (qcPreview / save requests)
  fields       ObjectField_cardTitle* (counter 0/100, AR twin #qc-ar-cardTitle*),
               ObjectField_cardDescription* (0/150, AR #qc-ar-cardDescription*),
               ObjectField_icon* (upload, help "Upload a .png,.svg no larger than 2 MB."),
               ObjectField_destinationLink* (text), ObjectField_displayOrder* (number),
               ObjectField_activeStatus (checkbox).
  buttons      Editor: "Save as Draft" / "Publish"; Author: "Save as Draft" /
               "Submit for Review". ENTRY column = cardTitle; delete link carries
               data-qc-oel-label=<cardTitle>.
  real cards   QCDEMO-130709-CARD-01..06 (Photo Gallery 100 ... Request to the
               Media Dept 600) — READ ONLY, never opened for save.
  preview      the panel shows "Field view (no page renders this Object)"; row
               Preview -> /web/qatar-chamber/object-preview?qcPreview=...
  public       /web/qatar-chamber/media-center: div[data-qc-mcqa-grid] >
               a.qc-mc-qa-card[href] (whole card = link, arrow inside it) with
               .qc-mc-qa-title / .qc-mc-qa-cardesc / .qc-mc-qa-tile-img whose
               mask-image URL carries objectEntryExternalReferenceCode=<ERC>.
  workflow     row transitions POST /o/qc-object-status/<action>/<entryId>
               through Liferay.Util.fetch (CSRF token).

The form has no ERC field, so a created card gets a server UUID code. A
disposable card is identified by: list-id diff at creation + exact Card Title
read back by code; its title must start with "QCTEST". The case labels
"QCTEST-130709-QAC-NN" map onto those captured records.

DELETE SAFETY: delete_disposable_entry() deletes ONLY a QacEntry captured by
this session (owned id), title starting with QCTEST, never a QCDEMO- code,
re-read by code right before the click, confirm() must name the title. No
positional, looping or substring delete exists in this module.
"""

import os as _os
import re as _re
from dataclasses import dataclass as _dataclass

from cms.pages.tenders.tender_admin_page import TenderWorkflowAdminPage
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import web_url
from core.utils.logger import get_logger as _get_logger
from core.utils.waits import WaitTimeoutError as _WaitTimeoutError
from core.utils.waits import wait_until as _wait_until
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher

_logger = _get_logger("mc_quick_access_card_admin_page")

SLUG = "media-center-quick-access-card"
RESOURCE = "mediacenterquickaccesscards"
REAL_CODE_PREFIX = "QCDEMO-"
REAL_CODES = tuple(f"QCDEMO-130709-CARD-0{i}" for i in range(1, 7))
QCTEST_TITLE_PREFIX = "QCTEST"

ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_FORM_MANAGER = "Form Manager"
ROLE_MEMBER = "Site Member"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492", ROLE_FORM_MANAGER: "156500",
                 ROLE_MEMBER: "156516"}

MSG_DRAFT_SAVED = "Draft saved."
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
MSG_ARABIC_SAVED = "Arabic content saved for this record."
MSG_ACCESS_DENIED = "Access Denied. You do not have permission to perform this action."
MSG_ACCESS_DENIED_AR = "تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء."
STATUS_INACTIVE = "Inactive"

K_TITLE = "cardTitle"
K_DESC = "cardDescription"
K_ICON = "icon"
K_LINK = "destinationLink"
K_ORDER = "displayOrder"
TEXT_KEYS = (K_TITLE, K_DESC, K_LINK)
AR_KEYS = (K_TITLE, K_DESC)
ICON_LABEL = "Icon"

EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "mc130709", "QAC")


@_dataclass(frozen=True)
class QacEntry:
    """Identity of ONE card this session created (captured, never inferred)."""

    title: str
    entry_id: str
    code: str

    def in_namespace(self) -> bool:
        return (self.title.strip().startswith(QCTEST_TITLE_PREFIX) and bool(self.entry_id) and bool(self.code)
                and not self.code.upper().startswith(REAL_CODE_PREFIX))


def _shot(page, name: str, full_page: bool = True) -> str:
    _os.makedirs(EVIDENCE_DIR, exist_ok=True)
    path = _os.path.join(EVIDENCE_DIR, _re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
    try:
        png = page.screenshot(path=path, full_page=full_page)
        from core.utils.reporting import attach_screenshot  # noqa: PLC0415
        attach_screenshot(png, name, "mc130709")
    except Exception as exc:  # noqa: BLE001 — evidence only
        _logger.warning("evidence %s failed: %r", name, exc)
    return path


class QacAdminPage(TenderWorkflowAdminPage):
    """manage-media-center-quick-access-card driver (reuses the confirmed-live
    role login / Load-All list / save-outcome probe / History of the tender
    driver; every tender-specific identity/delete method is disabled)."""

    FORM = 'form:has([name="ObjectField_cardTitle"])'
    SUBMIT_NAME = _re.compile(r"^\s*(Publish|Submit for Review)\s*$")
    SAVE_REQUEST_PATTERN = _re.compile(rf"edit_info_item|/o/c/{RESOURCE}")
    FORM_SUBMIT_BUTTONS = 'button[type="submit"][name="status"]'  # [0] draft, [-1] publish/submit (any locale)
    PREVIEW_FIELD_VIEW_TAB = "text=/Field view/"
    PREVIEW_HEAD = "text=/Preview — how this record renders/"
    EVIDENCE_DIR = EVIDENCE_DIR

    def __init__(self, page):
        super().__init__(page)
        self.slug = SLUG

    # ---- evidence -------------------------------------------------------------
    def evidence(self, name: str, full_page: bool = True) -> str:  # type: ignore[override]
        return _shot(self.page, name, full_page)

    # ---- navigation -------------------------------------------------------------
    def open_create_form(self, locale: str = "en") -> "QacAdminPage":
        self.open(self._manage_url(locale=locale))
        self._entry_code = None
        self._locale = locale
        self.page.locator(f'{self.FORM} [name="ObjectField_{K_TITLE}"]').first.wait_for(timeout=90000)
        self.page.locator(self.FORM_SUBMIT_BUTTONS).last.wait_for(timeout=30000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_create_form_en(self) -> "QacAdminPage":  # type: ignore[override]
        return self.open_create_form("en")

    def open_entry(self, code: str, locale: str = "en") -> "QacAdminPage":
        self.open(self._manage_url(edit_entry=code, locale=locale))
        self._entry_code = code
        self._locale = locale
        self.page.locator(f'{self.FORM} [name="ObjectField_{K_TITLE}"]').first.wait_for(timeout=90000)
        try:
            _wait_until(lambda: self.text_value(K_TITLE) != "", timeout=15.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entry_en(self, code: str) -> "QacAdminPage":  # type: ignore[override]
        return self.open_entry(code, "en")

    def open_manage_page_raw(self, locale: str = "en") -> "QacAdminPage":
        """Navigates without waiting for the form (permission-denial checks)."""
        self.open(self._manage_url(locale=locale))
        return self

    # ---- page / form state ---------------------------------------------------------
    def manage_page_parts(self) -> dict:
        """Which manage-page parts are present and visible (list, form, preview)."""
        return self.page.evaluate(
            """() => { const vis = e => !!(e && (e.offsetWidth || e.offsetHeight) && !e.closest('[hidden]'));
                const form = document.querySelector('form:has([name="ObjectField_cardTitle"])');
                return {list: [...document.querySelectorAll('table tbody tr')].some(vis),
                        rows: document.querySelectorAll('[data-qc-oel-delete],[data-qc-oel-history]').length,
                        form: vis(form),
                        preview: /Preview\\s+—/.test(document.body.innerText),
                        body: document.body.innerText.slice(0, 3000)}; }""")

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def wait_body_contains(self, texts: tuple, timeout: float = 20.0) -> str:
        state = {"t": ""}

        def _seen() -> bool:
            try:
                state["t"] = self.body_text()
            except Exception:  # noqa: BLE001 — mid-render
                return False
            return any(t in state["t"] for t in texts)

        try:
            _wait_until(_seen, timeout=timeout, poll=0.5)
        except _WaitTimeoutError:
            pass
        return state["t"]

    def form_visible(self) -> bool:
        loc = self.page.locator(self.FORM)
        return loc.count() > 0 and loc.first.is_visible()

    def ar_direction(self, key: str) -> str:
        return self._ar(key).evaluate("el => getComputedStyle(el).direction")

    def counter_limit(self, key: str, arabic: bool = False) -> int | None:
        node = self._ar(key) if arabic else self._en(key)
        text = node.evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 4 && c; i++, c = c.parentElement) {
                           const m = (c.innerText || '').match(/(\\d+)\\s*\\/\\s*(\\d+)/); if (m) return m[2]; }
                       return ''; }""")
        return int(text) if text else None

    def native_max_length(self, key: str, arabic: bool = False) -> int:
        node = self._ar(key) if arabic else self._en(key)
        return int(node.evaluate("el => el.maxLength"))

    def upload_block_text(self, key: str) -> str:  # type: ignore[override]
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return node.evaluate(
            """(el, label) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !(c.innerText || '').includes(label); i++) c = c.parentElement;
                return ((c ? c.innerText : '') + ' ' + (el.value || '') + ' ' + (el.placeholder || ''))
                       .replace(/\\s+/g, ' ').trim(); }""",
            ICON_LABEL)

    def stored_icon_name(self) -> str:
        placeholder = self._form().locator(f'input[name="ObjectField_{K_ICON}"]').first.get_attribute("placeholder") or ""
        match = _re.search(r"Current file:\s*(.+?)\s*(—|\(|$)", placeholder) or \
            _re.search(r"Current file:\s*(.+?)\s*(—|\(|$)", self.upload_block_text(K_ICON))
        return match.group(1).strip() if match else ""

    def icon_field_value(self) -> str:
        return self._form().locator(f'input[name="ObjectField_{K_ICON}"]').first.input_value()

    def _open_picker(self, key: str) -> None:  # type: ignore[override]
        """The field's own Select File button, found by its stable id suffix
        (works on the Arabic interface, where the label is translated)."""
        hidden = self._form().locator(f'input[name="ObjectField_{key}"]').first
        hidden.locator("xpath=..").locator('button[id$="-file-upload-button-label"]').first.click()

    PICKER_ADD_BUTTON = ".item-selector-preview button.btn-primary"  # structural: label is localised

    def upload_any_locale(self, key: str, file_path: str, stem: str | None = None) -> "QacAdminPage":
        """Upload through the picker without any text locator (Arabic interface):
        file input -> upload POST answered -> the preview's primary (Add) button."""
        upload_path = self._unique_upload_copy(file_path, stem)
        self.last_uploaded_name = _os.path.basename(upload_path)
        self._open_picker(key)
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        with self.page.expect_response(
                lambda r: r.request.method == "POST" and bool(self.UPLOAD_REQUEST_PATTERN.search(r.url)),
                timeout=60000):
            frame.locator('input[type="file"]').set_input_files(upload_path)
        modal = self.page.locator(self.UPLOAD_MODAL_IFRAME)

        def _added() -> bool:
            if modal.count() == 0:
                return True
            try:
                frame.locator(self.PICKER_ADD_BUTTON).first.click(timeout=3000)
            except Exception:  # noqa: BLE001 — retried by the poll
                pass
            return modal.count() == 0

        _wait_until(_added, timeout=30.0, poll=1.5, message="the picker did not close after Add")
        _wait_until(lambda: self.icon_field_value() != "", timeout=10.0, poll=0.5,
                    message="the icon field stayed empty after the upload")
        return self

    def clear_number(self, key: str) -> "QacAdminPage":
        self._en(key).fill("")
        return self

    def fill_card(self, data: dict) -> "QacAdminPage":
        """Keys: cardTitle/cardDescription/destinationLink (+ `<key>_ar`),
        displayOrder, activeStatus (bool), icon_file (+ icon_stem). None = untouched."""
        for key in TEXT_KEYS:
            if data.get(key) is not None:
                self.fill_en(key, str(data[key]))
        for key in AR_KEYS:
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, str(data[f"{key}_ar"]))
        if data.get(K_ORDER) is not None:
            self.fill_number_key(K_ORDER, str(data[K_ORDER]))
        if data.get("icon_file") and data.get("icon_any_locale"):
            self.upload_any_locale(K_ICON, data["icon_file"], data.get("icon_stem"))
            data["icon_uploaded_as"] = self.last_uploaded_name
        elif data.get("icon_file"):
            self.upload(K_ICON, data["icon_file"], data.get("icon_stem"))
            data["icon_uploaded_as"] = self.last_uploaded_name
        if data.get("activeStatus") is not None:
            self.set_active_status(bool(data["activeStatus"]))
        return self

    def read_card(self) -> dict:
        values = {key: self.text_value(key) for key in TEXT_KEYS}
        for key in AR_KEYS:
            values[f"{key}_ar"] = self.ar_value(key)
        values[K_ORDER] = self.text_value(K_ORDER)
        values["icon"] = self.stored_icon_name()
        values["activeStatus"] = self.active_status_stored()
        return values

    def click_submit_any_locale(self) -> "QacAdminPage":
        """The form's publish/submit button located by structure (last submit
        button of the form), so it also works on the Arabic interface."""
        self._arm_save_probe()
        self.page.locator(f"{self.FORM} {self.FORM_SUBMIT_BUTTONS}").last.click()
        self._wait_for_save_outcome()
        return self

    def submit_button_text_any(self) -> str:
        return self.page.locator(f"{self.FORM} {self.FORM_SUBMIT_BUTTONS}").last.inner_text().strip()

    def wait_arabic_saved(self, timeout: float = 20.0) -> bool:
        try:
            _wait_until(lambda: MSG_ARABIC_SAVED in self.body_text() or "Arabic content was not" in self.body_text(),
                        timeout=timeout, poll=0.5)
            return MSG_ARABIC_SAVED in self.body_text()
        except _WaitTimeoutError:
            return False

    # ---- identity / capture ---------------------------------------------------------
    def qctest_rows(self) -> list[dict]:
        """Read-only: rows whose ENTRY text starts with QCTEST."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].strip().startswith(QCTEST_TITLE_PREFIX)]

    def identify_created(self, title: str, ids_before: set[str]) -> QacEntry | None:
        if not title.strip().startswith(QCTEST_TITLE_PREFIX):
            raise ValueError(f"{title!r} is not a QCTEST title")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].upper().startswith(REAL_CODE_PREFIX) and r["title"].strip() == title.strip()]
        matches = []
        for row in fresh:
            for attempt in (1, 2):
                try:
                    self.open_entry(row["code"])
                    if self.text_value(K_TITLE).strip() == title.strip():
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — unreadable row is not ours
                    _logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        self.last_identify_matches = [QacEntry(m["title"].strip(), m["entry_id"], m["code"]) for m in matches]
        if len(matches) != 1:
            _logger.warning("identify_created(%r): %s matches among %s", title, len(matches), fresh)
            return None
        entry = QacEntry(matches[0]["title"].strip(), matches[0]["entry_id"], matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def new_rows_since(self, ids_before: set[str]) -> list[dict]:
        """Read-only: rows that did not exist in `ids_before` (refused-save checks)."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["entry_id"] not in ids_before]

    def adopt(self, entry: QacEntry) -> QacEntry:  # type: ignore[override]
        if not isinstance(entry, QacEntry) or not entry.in_namespace():
            raise ValueError(f"refusing to adopt {entry}")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    # ---- rows --------------------------------------------------------------------------
    def row_of(self, entry: QacEntry) -> dict:
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return rows[0] if len(rows) == 1 else {}

    def row_status_of(self, entry: QacEntry) -> str:
        row = self.row_of(entry)
        if not row:
            return ""
        raw = " ".join(row["status"].split())
        if raw.casefold() == STATUS_INACTIVE.casefold():
            return STATUS_INACTIVE
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        return normalize_status(raw)

    def row_modified_text(self, entry: QacEntry) -> str:
        return self._row_a(entry).first.locator("td").nth(2).inner_text().strip()

    def wait_row_status(self, entry: QacEntry, expected: tuple, timeout: float = 120.0) -> str:
        seen = {"status": ""}

        def _reached() -> bool:
            self.open_list_all()
            seen["status"] = self.row_status_of(entry)
            return seen["status"] in expected

        try:
            _wait_until(_reached, timeout=timeout, poll=3.0)
        except _WaitTimeoutError:
            pass
        return seen["status"]

    def run_row_action(self, entry: QacEntry, action: str, comment: str = "") -> list[str]:  # type: ignore[override]
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(f"run_row_action refuses {action!r}; use delete_disposable_entry()")
        if action != "history":
            if not isinstance(entry, QacEntry) or not entry.in_namespace() or entry.entry_id not in self.owned_entry_ids:
                raise ValueError(f"run_row_action refuses {entry}: not a captured QCTEST card")
            row = self.row_of(entry)
            if not row or row["title"].strip() != entry.title:
                raise ValueError(f"run_row_action refuses {entry}: the row now reads {row}")
        return self._click_row_action(entry, action, comment)

    def run_real_row_action(self, ref, action: str, guard: "RealCardGuard") -> list[str]:
        """Unpublish / publish on a REAL card only while `guard` holds its snapshot
        (snapshot -> change -> restore -> diff). Nothing else is allowed."""
        if action not in ("unpublish", "publish"):
            raise ValueError(f"run_real_row_action refuses {action!r}")
        if ref.code not in REAL_CODES or ref.code not in guard.snapshots:
            raise ValueError(f"run_real_row_action refuses {ref}: not a snapshotted real card")
        return self._click_row_action(ref, action, "")

    def _click_row_action(self, entry, action: str, comment: str = "") -> list[str]:
        control = self._row_a(entry).first.locator(f"[data-qc-oel-{action}]")
        if control.count() == 0:
            raise AssertionError(f"row {entry.title!r} offers no {action!r}; offered {self.row_actions(entry)}")
        messages: list[str] = []

        def _accept(dialog):
            messages.append(f"{dialog.type}: {dialog.message}")
            try:
                dialog.accept(comment) if dialog.type == "prompt" else dialog.accept()
            except Exception:  # noqa: BLE001
                pass

        self.page.on("dialog", _accept)
        try:
            control.first.click(force=True)
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        self.last_row_action_dialogs = messages
        return messages

    def forced_transition(self, action: str, entry_id: str) -> dict:
        """POSTs the workflow transition the row action would send, with this
        session's CSRF token, WITHOUT the control being offered -> {status, body}."""
        if action in ("delete", "trash"):
            raise ValueError("forced_transition refuses destructive actions")
        return self.page.evaluate(
            """async ([action, id]) => {
                const doFetch = (window.Liferay && Liferay.Util && Liferay.Util.fetch) ? Liferay.Util.fetch : fetch;
                const r = await doFetch('/o/qc-object-status/' + action + '/' + id, {method: 'POST',
                    headers: {Accept: 'application/json', 'Content-Type': 'application/json'},
                    body: JSON.stringify({comment: ''})});
                return {status: r.status, body: (await r.text()).slice(0, 500)}; }""",
            [action, entry_id])

    def forced_update(self, entry_id: str, payload: dict) -> dict:
        """PATCHes the object entry through the headless API with this session's
        CSRF token (permission probe) -> {status, body}."""
        return self.page.evaluate(
            """async ([res, id, payload]) => {
                const doFetch = (window.Liferay && Liferay.Util && Liferay.Util.fetch) ? Liferay.Util.fetch : fetch;
                const r = await doFetch('/o/c/' + res + '/' + id, {method: 'PATCH',
                    headers: {Accept: 'application/json', 'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)});
                return {status: r.status, body: (await r.text()).slice(0, 500)}; }""",
            [RESOURCE, entry_id, payload])

    # ---- preview -------------------------------------------------------------------------
    def click_row_preview(self, entry: QacEntry) -> "QacAdminPage":
        self._row_a(entry).first.get_by_role("link", name="Preview").first.click()
        return self

    def preview_frame_text(self, expected: tuple = (), timeout: float = 30.0) -> dict:
        """Reads the Preview panel: head text (tabs), and the preview frame's body."""
        state = {"frame_url": "", "frame_text": ""}

        def _read() -> bool:
            for frame in self.page.frames:
                if "qcPreview=" in (frame.url or ""):
                    try:
                        state["frame_url"] = frame.url
                        state["frame_text"] = frame.locator("body").inner_text()
                        state["frame_dir"] = frame.evaluate("() => getComputedStyle(document.body).direction")
                    except Exception:  # noqa: BLE001 — mid-render
                        return False
                    return not expected or any(e in state["frame_text"] for e in expected)
            return False

        try:
            _wait_until(_read, timeout=timeout, poll=1.0)
        except _WaitTimeoutError:
            pass
        state["panel_text"] = self.page.evaluate(
            """() => { const t = document.body.innerText; const i = t.indexOf('Preview —');
                       return i < 0 ? '' : t.slice(i, i + 400); }""")
        return state

    def click_preview_locale(self, locale: str) -> "QacAdminPage":
        self.page.get_by_role("button", name=locale.upper(), exact=True).first.click()
        return self

    def form_labels_and_errors(self) -> dict:
        """Visible field labels and field-level validation messages INSIDE the
        authoring form (object/list headings excluded) + the edit-bar texts."""
        form = self.page.locator(self.FORM).first
        labels = [t.strip() for t in form.locator("label:visible").all_inner_texts() if t.strip()]
        errors = [t.strip() for t in form.locator(
            ".form-feedback-item:visible, .invalid-feedback:visible, .form-feedback-group:visible")
            .all_inner_texts() if t.strip()]
        return {"labels": labels, "field_errors": errors, "bar": self.editbar_texts()}

    ADD_NEW_CONTROL = 'button:visible, a:visible'
    ADD_NEW_RE = _re.compile(r"^\s*\+?\s*Add New", _re.I)

    def add_new_offered(self) -> list[str]:
        """Visible '+ Add New' controls on the manage list (149913: must be none)."""
        texts = [(t or "").strip() for t in self.page.locator(self.ADD_NEW_CONTROL).all_inner_texts()]
        return [t for t in texts if self.ADD_NEW_RE.search(t)]

    # ---- real cards (READ ONLY) -------------------------------------------------------------
    def real_cards(self) -> list[dict]:
        cards = []
        for code in REAL_CODES:
            self.open_entry(code)
            cards.append({"code": code, "title": self.text_value(K_TITLE), "order": int(self.text_value(K_ORDER) or 0),
                          "active": self.active_status_stored() == "true", "link": self.text_value(K_LINK)})
        self.open_list_all()
        for card in cards:
            row = [r for r in self.list_rows() if r["code"] == card["code"]]
            card["status"] = " ".join(row[0]["status"].split()).upper() if row else ""
        return cards

    # ---- guarded delete ---------------------------------------------------------------------
    def _delete_preconditions(self, entry: QacEntry) -> str:  # type: ignore[override]
        if not self.is_list_fully_expanded():
            return f"list not fully expanded ({self.rendered_row_count()} of {self.total_entry_count()})"
        links = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
        if links.count() != 1:
            return f"{links.count()} delete links carry id {entry.entry_id}"
        rows = [r for r in self.list_rows() if r["delete_id"] == entry.entry_id]
        if len(rows) != 1:
            return f"{len(rows)} rows carry delete id {entry.entry_id}"
        row = rows[0]
        if row["code"] != entry.code or row["code"].upper().startswith(REAL_CODE_PREFIX):
            return f"row {entry.entry_id} points at {row['code']!r}, not {entry.code!r}"
        if row["title"].strip() != entry.title or row["label"].strip() != entry.title:
            return f"row {entry.entry_id} shows {row['title']!r} / {row['label']!r}, not {entry.title!r}"
        return ""

    def delete_disposable_entry(self, entry: QacEntry) -> bool:  # type: ignore[override]
        """Deletes exactly the captured card or refuses (False, never raises)."""
        try:
            if not isinstance(entry, QacEntry) or not entry.in_namespace() or entry.entry_id not in self.owned_entry_ids:
                _logger.error("DELETE REFUSED: %r is not a captured QCTEST card", entry)
                return False
            self.open_entry(entry.code)
            live = self.text_value(K_TITLE).strip()
            if live != entry.title:
                _logger.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
                return False
            self.open_list_all()
            reason = self._delete_preconditions(entry) or self._delete_preconditions(entry)
            if reason:
                _logger.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            names = [entry.title, entry.code]
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
            if not any(any(n in m for n in names) for m in dialogs):
                _logger.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            gone = self.is_list_fully_expanded() and not self.row_present(entry)
            if gone:
                self.owned_entry_ids.discard(entry.entry_id)
            return gone
        except Exception as exc:  # noqa: BLE001
            _logger.error("delete of %r failed: %r", entry, exc)
            return False

    # ---- tender helpers are invalid here ------------------------------------------------------
    def _not_qac(self, *_a, **_k):
        raise NotImplementedError("tender-specific helper; use the QacAdminPage API")

    fill_tender = fill_tender_a = read_tender = a_tender_data = _not_qac
    identify_created_a = adopt_a = delete_own_entry = a_leftovers = b_leftovers = _not_qac
    row_status_a = wait_status = fill_reference_number = fill_valid_form = _not_qac
    row_status_text_for_reference = upload_tender_document = upload_boq = _not_qac
    delete_entry_by_code = delete_entry_by_title = delete_all_entries_by_title = _not_qac


class MediaCenterHubView(BasePage):
    """Logged-out reader of the public "Explore the hub" quick-access grid."""

    PATH = "/web/qatar-chamber/media-center"
    GRID = "[data-qc-mcqa-grid]"
    CARD = "a.qc-mc-qa-card"

    _CARDS_JS = """() => [...document.querySelectorAll('[data-qc-mcqa-grid] a.qc-mc-qa-card')].map((a, i) => {
        const q = s => a.querySelector(s); const tile = q('.qc-mc-qa-tile-img');
        const mask = tile ? (tile.style.maskImage || tile.style.webkitMaskImage || getComputedStyle(tile).maskImage || '') : '';
        const m = mask.match(/objectEntryExternalReferenceCode=([^&"')]+)/);
        const u = mask.match(/url\\(["']?([^"')]+)/);
        const title = q('.qc-mc-qa-title'), desc = q('.qc-mc-qa-cardesc'), arrow = q('.qc-mc-qa-arrow-wrap');
        const box = el => { if (!el) return null; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
            return {left: r.left, right: r.right, top: r.top, bottom: r.bottom, w: r.width, h: r.height,
                    sw: el.scrollWidth, cw: el.clientWidth, sh: el.scrollHeight, ch: el.clientHeight,
                    overflow: cs.overflow, text_overflow: cs.textOverflow, clamp: cs.webkitLineClamp,
                    direction: cs.direction, white_space: cs.whiteSpace}; };
        return {index: i, href: a.getAttribute('href') || '', target: a.getAttribute('target') || '',
                title: title ? title.innerText.trim() : '', desc: desc ? desc.innerText.trim() : '',
                erc: m ? decodeURIComponent(m[1]) : '', icon_url: u ? u[1] : '',
                arrow_in_link: !!arrow, card: box(a), title_box: box(title), desc_box: box(desc)}; })"""

    def open_hub(self, locale: str = "en") -> "MediaCenterHubView":
        self.open(web_url(self.PATH, locale=locale))
        try:
            self.page.locator(self.GRID).first.wait_for(state="attached", timeout=60000)
            _wait_until(lambda: self.page.locator(f"{self.GRID} {self.CARD}").count() > 0, timeout=30.0, poll=0.5)
        except Exception:  # noqa: BLE001 — an empty grid is reported by the caller
            pass
        try:  # the icon mask (which carries the card ERC) can be applied after the grid renders
            self.page.locator(self.GRID).first.scroll_into_view_if_needed(timeout=5000)
            _wait_until(lambda: self.page.evaluate(
                "() => [...document.querySelectorAll('[data-qc-mcqa-grid] .qc-mc-qa-tile-img')].every("
                "t => /objectEntryExternalReferenceCode=/.test(t.style.maskImage || t.style.webkitMaskImage || ''))"),
                timeout=15.0, poll=0.5)
        except Exception:  # noqa: BLE001 — callers report missing identities
            pass
        return self

    def cards(self) -> list[dict]:
        return self.page.evaluate(self._CARDS_JS)

    def card_by_erc(self, erc: str) -> dict:
        for card in self.cards():
            if card["erc"] == erc:
                return card
        return {}

    def grid_config(self) -> dict:
        """The fragment's own configuration: card cap and object path."""
        return self.page.evaluate(
            """() => { const r = document.querySelector('[data-qc-mcqa-object]');
                       return r ? {max: r.getAttribute('data-qc-mcqa-max'), object: r.getAttribute('data-qc-mcqa-object'),
                                   rendered: r.querySelectorAll('a.qc-mc-qa-card').length} : {}; }""")

    def delivery_entries(self) -> list[dict]:
        """What the fragment's own anonymous data call returns (evidence only)."""
        return self.page.evaluate(
            """async () => { const g = window.Liferay && Liferay.ThemeDisplay ? Liferay.ThemeDisplay.getScopeGroupId() : '';
                const r = await fetch('/o/c/mediacenterquickaccesscards/scopes/' + g + '?pageSize=50', {headers: {Accept: 'application/json'}});
                const d = r.ok ? await r.json() : {};
                return (d.items || []).map(i => ({code: i.externalReferenceCode, title: i.cardTitle, order: i.displayOrder,
                        active: i.activeStatus, status: i.status && i.status.label})); }""")

    def page_layout(self) -> dict:
        return self.page.evaluate(
            """() => ({hscroll: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
                       dir: document.documentElement.dir || getComputedStyle(document.body).direction,
                       lang: document.documentElement.lang})""")

    def poll(self, predicate, locale: str = "en", timeout: float = 45.0) -> tuple[bool, list[dict], float]:
        """Reloads the hub until predicate(cards) holds -> (held, cards, seconds)."""
        from time import monotonic  # noqa: PLC0415
        started = monotonic()
        state = {"cards": [], "at": 0.0}

        def _check() -> bool:
            # latency = when the page load that shows the state STARTED (rules: budget measured after page load)
            state["at"] = monotonic() - started
            self.open_hub(locale)
            state["cards"] = self.cards()
            return bool(predicate(state["cards"]))

        try:
            _wait_until(_check, timeout=timeout, poll=1.0)
            return True, state["cards"], state["at"]
        except _WaitTimeoutError:
            return False, state["cards"], state["at"]

    def follow_card(self, erc: str, timeout_ms: int = 60000) -> dict:
        """Clicks the card (its arrow sits inside the same link) and reports where
        the browser lands (same tab or a new tab)."""
        link = self.page.locator(f"{self.GRID} {self.CARD}:has(.qc-mc-qa-tile-img[style*='{erc}'])").first
        arrow = link.locator(".qc-mc-qa-arrow-wrap").first
        href = link.get_attribute("href") or ""
        target = link.get_attribute("target") or ""
        _dismiss_chatbot_launcher(self.page)
        if target == "_blank":
            with self.page.context.expect_page(timeout=timeout_ms) as new:
                arrow.click(force=True)
            other = new.value
            try:
                other.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
            except Exception:  # noqa: BLE001
                pass
            return {"href": href, "target": target, "url": other.url, "new_tab": True}
        arrow.scroll_into_view_if_needed()
        try:
            with self.page.expect_navigation(wait_until="domcontentloaded", timeout=timeout_ms):
                arrow.click()  # a real (non-forced) click, as a visitor does
        except Exception:  # noqa: BLE001 — reported by the caller via the URL
            pass
        return {"href": href, "target": target, "url": self.page.url, "new_tab": False}

    def head_status(self, url: str) -> int:
        try:
            return self.page.request.get(url, max_redirects=5, timeout=60000).status
        except Exception:  # noqa: BLE001
            return -1

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _shot(self.page, name, full_page)


# =============================================================================
# REAL CARD guard (user decision 2026-10-12): snapshot -> temporary edit ->
# logged-out public check -> exact restore (PUT, same endpoint the authoring
# page uses on Publish) -> empty diff, on QCDEMO-130709-CARD-01/02 only.
# Concurrency guard (rule 4b): the record is re-read right before every edit
# (must equal the snapshot or the last value THIS test wrote) and right
# before the restore (must equal the last value this test wrote); any other
# difference = another person's change -> no overwrite, NEEDS-DECISION.
# Never unpublishes, never deletes.
# =============================================================================
import json as _json

REAL_EDITABLE = ("QCDEMO-130709-CARD-01", "QCDEMO-130709-CARD-02")
_VOLATILE = ("dateModified", "actions", "creator", "dateCreated")


@_dataclass(frozen=True)
class RealCardRef:
    """A real card under the guard (never a QacEntry: adopt()/delete refuse it)."""

    title: str
    entry_id: str
    code: str


class RealCardConflict(AssertionError):
    """Another person changed the real card during the edit window."""


def _comparable(record: dict) -> dict:
    out = {k: v for k, v in record.items() if k not in _VOLATILE}
    if isinstance(out.get("status"), dict):
        out["status"] = out["status"].get("code")
    return out


def real_diff(before: dict, after: dict) -> list[str]:
    a, b = _comparable(before), _comparable(after)
    return [f"{k}: {_json.dumps(a.get(k), ensure_ascii=False)[:160]} -> {_json.dumps(b.get(k), ensure_ascii=False)[:160]}"
            for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


class RealCardGuard:
    """Holds the snapshot / last-written state of the real cards one test touches.
    `api` is an Editor-signed-in QacAdminPage used only for GET / restore PUT."""

    def __init__(self, api: QacAdminPage):
        self.api = api
        self.snapshots: dict[str, dict] = {}
        self.written: dict[str, dict] = {}
        self.log: list[str] = []

    def get(self, code: str) -> dict:
        if code not in REAL_EDITABLE:
            raise ValueError(f"{code} is not an approved real card")
        body = [0, ""]
        for _ in range(4):
            try:
                self.api.page.wait_for_function("() => window.Liferay && Liferay.authToken", timeout=20000)
                body = self.api.page.evaluate(
                    """async (code) => { const g = Liferay.ThemeDisplay.getScopeGroupId();
                        const r = await fetch('/o/c/mediacenterquickaccesscards/scopes/' + g +
                            '/by-external-reference-code/' + code, {headers: {Accept: 'application/json',
                            'x-csrf-token': Liferay.authToken}});
                        return [r.status, await r.text()]; }""", code)
                if body[0] == 200:
                    break
            except Exception as exc:  # noqa: BLE001 — navigation in flight; retried
                _logger.warning("real GET %s: %r", code, exc)
            self.api.open_manage_page_raw()
        if body[0] != 200:
            raise AssertionError(f"GET {code} returned {body[0]}: {body[1][:200]}")
        data = _json.loads(body[1])
        data.pop("actions", None)
        return data

    def take(self, code: str) -> RealCardRef:
        snap = self.get(code)
        if snap.get("status", {}).get("code") != 0 or not snap.get("activeStatus"):
            raise AssertionError(f"PRECONDITION: {code} is not Published + Active: {snap.get('status')}")
        self.snapshots[code] = snap
        _os.makedirs(EVIDENCE_DIR, exist_ok=True)
        path = _os.path.join(EVIDENCE_DIR, f"snapshot_{code}_{snap['dateModified'].replace(':', '')}.json")
        with open(path, "w", encoding="utf-8") as handle:
            _json.dump(snap, handle, ensure_ascii=False, indent=1)
        self.log.append(f"snapshot {code} -> {path}")
        return RealCardRef(snap["cardTitle"], str(snap["id"]), code)

    def check_before_edit(self, code: str) -> None:
        expected = self.written.get(code, self.snapshots[code])
        diffs = real_diff(expected, self.get(code))
        if diffs:
            raise RealCardConflict(f"NEEDS-DECISION: {code} changed by someone else before the edit: {diffs}")

    def record_written(self, code: str) -> None:
        self.written[code] = self.get(code)

    def restore(self, code: str) -> list[str]:
        """[] when restored with an empty diff; otherwise the problems (no overwrite on conflict)."""
        snap = self.snapshots[code]
        current = self.get(code)
        expected = self.written.get(code, snap)
        foreign = real_diff(expected, current)
        if foreign:
            msg = f"CONFLICT {code}: changed by someone else during the window, NOT restored: {foreign}"
            self.log.append(msg)
            return [msg]
        if real_diff(snap, current):
            body = {k: v for k, v in snap.items() if k not in _VOLATILE}
            body["status"] = {"code": snap.get("status", {}).get("code", 0)}
            result = self.api.page.evaluate(
                """async ([id, b]) => { const r = await fetch('/o/c/mediacenterquickaccesscards/' + id, {
                        method: 'PUT', body: JSON.stringify(b), headers: {'Content-Type': 'application/json',
                        Accept: 'application/json', 'x-csrf-token': Liferay.authToken}});
                    return [r.status, (await r.text()).slice(0, 300)]; }""", [snap["id"], body])
            self.log.append(f"restore PUT {code} -> {result[0]}")
            if int(result[0]) >= 400:
                return [f"restore PUT {code} failed: {result}"]
        diffs = real_diff(snap, self.get(code))
        self.log.append(f"restore diff {code}: {diffs or 'EMPTY'}")
        return [f"{code} differs after restore: {diffs}"] if diffs else []

"""
cms/pages/business_opportunities/opportunity_fields_c_page.py — Agent C section
(PBI 130697, Business Opportunities Control_Panel, field validation).

Kept in its own module (instead of a `# --- C ---` section of the core
opportunity_admin_page.py) because the core class is being written in parallel
by Agent A and a whole-file write there would drop this section. Reuses the
generic, object-agnostic machinery of the Tenders (PBI 130952) fields page —
role login, list/row parsing, save-outcome probe, refusal evidence, date and
upload helpers — re-pointed at `manage-business-opportunity`.

Live recon 2026-10-07 (Site Content Editor, qcdev): the create form's required
fields are Opportunity Title (EN+AR), Country (EN+AR), Company/Organization
Name (EN+AR), Investment Amount, Currency, Banner Image, Opportunity Logo,
Hero Banner, Investment Amount Range, Submitter Name / Entity Type / Location
(EN+AR), Submitted-By Logo, Publish Date, Archive Date, Display Order. Buttons
for the Editor: "Save as Draft" / "Publish".

Every record created here is QCTEST-130697-C-<tc>-<stamp>…; deletion is by
captured entry id + exact title only (hard rule 1).
"""

from __future__ import annotations

import os as _os
import re as _re
from dataclasses import dataclass as _dataclass

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.tenders.tender_admin_page import TenderFieldsAdminPage
from core.utils.logger import get_logger as _get_logger
from core.utils.waits import WaitTimeoutError as _WaitTimeoutError
from core.utils.waits import wait_until as _wait_until
from core.web.overlays import _dismiss_chatbot_launcher
from config.settings import PROJECT_ROOT as _PROJECT_ROOT

_log = _get_logger("opportunity_fields_c_page")

C_QCTEST_PREFIX = "QCTEST-130697-C-"
C_ROLE_EDITOR = "Site Content Editor"
C_EDITOR_USER_ID = "156488"
C_ROLE_AUTHOR = "Site Content Author"
C_AUTHOR_USER_ID = "156492"

K_TITLE = "opportunityTitle"
K_COUNTRY = "country"
K_COMPANY = "companyOrganizationName"
K_AMOUNT = "investmentAmount"
K_CURRENCY = "currency"
K_RANGE = "investmentAmountRange"
K_SUBMITTER = "submitterName"
K_ENTITY = "submitterEntityType"
K_LOCATION = "submittedByLocation"
K_PUBLISH_DATE = "publishDate"
K_ARCHIVE_DATE = "archiveDate"
K_SORT = "displayOrder"
K_IMAGES = ("bannerImage", "opportunityLogo", "heroBanner", "submittedByLogo")
EXISTING_IMAGE = "6th-World-Conference-Arbitration-Eng.png"   # existing Documents & Media root file: picked, never uploaded


@_dataclass(frozen=True)
class BizEntryC:
    title: str
    entry_id: str
    code: str

    def in_namespace(self) -> bool:
        return self.title.strip().startswith(C_QCTEST_PREFIX)


# --- C ---
class BizOppFieldsCPage(TenderFieldsAdminPage):
    """Field-level driver for manage-business-opportunity (Agent C)."""

    FORM = f'form:has(input[name="ObjectField_{K_TITLE}"])'
    SAVE_REQUEST_PATTERN = _re.compile(r"edit_info_item|/o/c/businessopportunit")
    EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "evidence", "130697_c")
    OWN_ENTRY_ID_ATTRS = TenderFieldsAdminPage.ID_ATTRS

    def __init__(self, page):
        # skip TenderAdminPage.__init__ (hard-wired to slug "tender")
        ObjectAuthoringPage.__init__(self, page, "business-opportunity")
        self.owned_entry_ids: set[str] = set()
        self.last_uploaded_name = ""

    # ---- navigation ----------------------------------------------------------
    def open_create_form_en(self) -> "BizOppFieldsCPage":
        self.open(self._manage_url(locale="en"))
        self._entry_code = None
        self._locale = "en"
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.wait_for(timeout=90000)
        self.page.locator(f'{self.FORM} input[name="ObjectField_{K_TITLE}"]').first.wait_for(timeout=60000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entry_en(self, code: str) -> "BizOppFieldsCPage":
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self.page.locator(f'{self.FORM} input[name="ObjectField_{K_TITLE}"]').first.wait_for(timeout=90000)
        try:
            _wait_until(lambda: self.text_value(K_TITLE) != "", timeout=20.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    # ---- images: select an EXISTING library file (no Documents & Media writes) --
    def pick_existing_image(self, key: str, file_name: str = EXISTING_IMAGE) -> "BizOppFieldsCPage":
        hidden = self._form().locator(f'input[name="ObjectField_{key}"]').first
        hidden.locator("xpath=..").get_by_role("button", name="Select File").click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        target = frame.get_by_text(file_name, exact=True).first
        target.wait_for(state="visible", timeout=30000)
        target.click()
        if not self._picker_closed(5000):
            for label in ("Add", "Select", "Choose", "Done"):
                btn = frame.get_by_role("button", name=label)
                if btn.count():
                    try:
                        btn.first.click(timeout=5000)
                        break
                    except Exception:  # noqa: BLE001
                        continue
        if not self._picker_closed(6000):
            try:
                target.dblclick()
            except Exception:  # noqa: BLE001
                pass
        if not self._picker_closed(8000):
            raise AssertionError(f"the picker stayed open after selecting {file_name!r} for {key}")
        return self

    # ---- record data -----------------------------------------------------------
    @staticmethod
    def default_data(title: str, **overrides) -> dict:
        data = {
            K_TITLE: title, f"{K_TITLE}_ar": f"{title} فرصة تجريبية",
            K_COUNTRY: "Qatar", f"{K_COUNTRY}_ar": "قطر",
            K_COMPANY: "QCTEST Company", f"{K_COMPANY}_ar": "شركة تجريبية",
            K_AMOUNT: "1000000", K_CURRENCY: "QAR", K_RANGE: "1M - 5M",
            K_SUBMITTER: "QCTEST Submitter", f"{K_SUBMITTER}_ar": "مقدم تجريبي",
            K_ENTITY: "Company", f"{K_ENTITY}_ar": "شركة",
            K_LOCATION: "Doha", f"{K_LOCATION}_ar": "الدوحة",
            K_PUBLISH_DATE: None, K_ARCHIVE_DATE: None, K_SORT: "100",
            "active_status": True,
            "images": True,
            "sector": "Technology", "investmentType": "Equity", "timeline": "Immediate",
            "riskProfile": "Low", "industryPool": "Technology", "lifecycleStatus": "Published",
            "investmentBrief": "QCTEST brief.", "investmentBrief_ar": "ملخص تجريبي.",
            "heroSummary": "QCTEST hero summary.", "heroSummary_ar": "ملخص البطل تجريبي.",
            "overviewBody": "QCTEST overview.", "overviewBody_ar": "نظرة عامة تجريبية.",
        }
        data.update(overrides)
        return data

    def fill_opportunity(self, data: dict) -> "BizOppFieldsCPage":
        """Fills every key the dict carries; None / absent = left untouched (empty on a new form)."""
        for key in (K_TITLE, K_COUNTRY, K_COMPANY, K_SUBMITTER, K_ENTITY, K_LOCATION,
                    K_CURRENCY, K_RANGE):
            if data.get(key) is not None:
                self.fill_en(key, data[key])
        for key in (K_TITLE, K_COUNTRY, K_COMPANY, K_SUBMITTER, K_ENTITY, K_LOCATION):
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, data[f"{key}_ar"])
        if data.get(K_AMOUNT) is not None:
            self.fill_number_key(K_AMOUNT, data[K_AMOUNT])
        for key in ("sector", "investmentType", "timeline", "riskProfile", "industryPool", "lifecycleStatus"):
            if data.get(key):
                self.pick(key, data[key])
        for key in ("investmentBrief", "heroSummary", "overviewBody"):
            if data.get(key):
                self.fill_rich(key, data[key])
            if data.get(f"{key}_ar"):
                self._fill_rich_ar_robust(key, data[f"{key}_ar"])
        if data.get("images"):
            for key in K_IMAGES:
                self.pick_existing_image(key)
        for key in (K_PUBLISH_DATE, K_ARCHIVE_DATE):
            if data.get(key):
                self.set_date(key, data[key])
        if data.get(K_SORT) is not None:
            self.fill_number_key(K_SORT, data[K_SORT])
        if data.get("active_status") is not None:
            self.set_active_status(bool(data["active_status"]))
        return self

    def _fill_rich_ar_robust(self, key: str, text: str) -> None:
        """Arabic CKEditor mounts lazily; retry the fill while it comes up."""
        sel = f'[id="cke_qc-ar-{key}"] iframe[title="editor"]'
        last = None
        for _ in range(4):
            try:
                self.page.locator(sel).first.wait_for(state="attached", timeout=20000)
                self.fill_iframe_editor(sel, text)
                return
            except Exception as exc:  # noqa: BLE001
                last = exc
                self.page.wait_for_timeout(3000)
        raise last

    def sort_order_validity(self) -> dict:
        return self._en(K_SORT).evaluate(
            "e => ({value: e.value, valueAsNumber: e.valueAsNumber, valid: e.validity.valid, "
            "bad: e.validity.badInput, missing: e.validity.valueMissing, msg: e.validationMessage, "
            "type: e.type, min: e.min, step: e.step})")

    # ---- identity of created rows ------------------------------------------------
    def snapshot_ids(self) -> set[str]:
        self.open_list_all()
        if not self.is_list_fully_expanded():
            raise AssertionError("the list did not expand to show every row; cannot snapshot ids safely")
        return {r["entry_id"] for r in self.list_rows()}

    def c_leftovers(self) -> list[dict]:
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].startswith(C_QCTEST_PREFIX)]

    def identify_created(self, title: str, ids_before: set[str]) -> BizEntryC | None:
        if not title.strip().startswith(C_QCTEST_PREFIX):
            raise ValueError(f"{title!r} is not in the {C_QCTEST_PREFIX} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]]
        # Only rows NOT in the pre-snapshot are candidates. A row whose list title is a real title
        # (not the entry code / GUID) outside our prefix belongs to another agent: skip it unopened.
        candidates = [r for r in fresh
                      if r["title"].strip() in ("", r["code"]) or r["title"].strip().startswith(C_QCTEST_PREFIX)]
        skipped = [f"{r['entry_id']}:{r['title']!r}" for r in fresh if r not in candidates]
        self.last_candidates = [f"{r['entry_id']}:{r['code']}:{r['title']!r}" for r in candidates]
        matches, unreadable = [], []
        for row in candidates:
            for attempt in (1, 2):
                try:
                    self.open_entry_en(row["code"])
                    opened = self.text_value(K_TITLE)
                    if opened == title and opened.startswith(C_QCTEST_PREFIX):
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == 2:
                        unreadable.append(f"{row['entry_id']}:{row['code']}: {exc!r}")
        _log.info("identify_created(%r): candidates=%s skipped-other-agents=%s", title, self.last_candidates, skipped)
        if len(matches) == 1:
            pass
        elif len(matches) > 1 or unreadable:
            raise AssertionError(
                f"identify_created({title!r}): cannot identify the record safely - {len(matches)} matches, "
                f"unreadable candidate rows {unreadable}; candidate rows (id:code:title) {self.last_candidates}. "
                f"A record may exist on qcdev under this title: find it by that title and remove it by hand.")
        else:
            return None   # no new row carries our title: nothing was created
        entry = BizEntryC(title=title, entry_id=matches[0]["entry_id"], code=matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def row_status(self, entry: BizEntryC) -> str:
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return normalize_status(rows[0]["status"]) if len(rows) == 1 else ""

    def row_present(self, entry: BizEntryC) -> bool:
        return any(r["entry_id"] == entry.entry_id for r in self.list_rows())

    # ---- guarded delete (captured id + exact title) ------------------------------
    def _delete_preconditions(self, entry: BizEntryC) -> str:
        if not self.is_list_fully_expanded():
            return f"list not fully expanded ({self.rendered_row_count()} of {self.total_entry_count()})"
        if self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id)).count() != 1:
            return f"not exactly one delete link carries id {entry.entry_id}"
        rows = [r for r in self.list_rows() if r["delete_id"] == entry.entry_id]
        if len(rows) != 1:
            return f"{len(rows)} rows carry delete id {entry.entry_id}"
        row = rows[0]
        if row["code"] != entry.code:
            return f"row {entry.entry_id} points at {row['code']!r}, not {entry.code!r}"
        # the list shows the entry code (GUID) as the row title for new records; the exact title
        # was verified on the opened record immediately before (delete_disposable_entry)
        ok = {entry.title.strip(), entry.code}
        if row["title"].strip() not in ok or row["label"].strip() not in ok:
            return f"row {entry.entry_id} shows {row['title']!r}/{row['label']!r}, not {entry.title!r}/{entry.code!r}"
        return ""

    def delete_disposable_entry(self, entry: BizEntryC) -> bool:
        try:
            if (not entry.in_namespace() or not entry.entry_id or not entry.code
                    or entry.entry_id not in self.owned_entry_ids):
                _log.error("DELETE REFUSED: %r is not a captured %s record", entry, C_QCTEST_PREFIX)
                return False
            self.open_entry_en(entry.code)
            if self.text_value(K_TITLE) != entry.title:
                _log.error("DELETE REFUSED for %r: the record now reads %r", entry, self.text_value(K_TITLE))
                return False
            self.open_list_all()
            reason = self._delete_preconditions(entry)
            if reason:
                _log.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            reason = self._delete_preconditions(entry)
            if reason:
                _log.error("DELETE REFUSED for %r on re-check: %s", entry, reason)
                return False
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                if entry.title.strip() in dialog.message or entry.code in dialog.message:
                    dialog.accept()
                else:
                    dialog.dismiss()

            self.page.on("dialog", _on_dialog)
            try:
                link.click(force=True)
                try:
                    link.wait_for(state="detached", timeout=20000)
                except Exception:  # noqa: BLE001
                    pass
            finally:
                self.page.remove_listener("dialog", _on_dialog)
            self.last_delete_dialogs = dialogs
            if not any(entry.title.strip() in m or entry.code in m for m in dialogs):
                _log.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            return self.is_list_fully_expanded() and not self.row_present(entry)
        except Exception as exc:  # noqa: BLE001
            _log.error("delete of %r failed: %r", entry, exc)
            return False

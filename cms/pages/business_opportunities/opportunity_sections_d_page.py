"""
cms/pages/business_opportunities/opportunity_sections_d_page.py — Agent D section
(PBI 130697, Business Opportunities Control_Panel: Opportunity Sections and
listing Sort Order).

Kept in its own module (instead of a `# --- D ---` section of the core
opportunity_admin_page.py) for the same reason Agent C's module is: the core
class is written in parallel by Agent A and a whole-file write there would drop
this section. Reuses the generic machinery of the Tenders fields page (role
login, list parsing, save-outcome probe, field errors) re-pointed at
`manage-business-opportunity` (parent record) and `manage-opportunity-section`.

Every record created here is QCTEST-130697-D-...; deletion is by captured
entry id + exact title only (hard rule 1). Real records
(QC-BIZOPP-130697-NN, ...-SEC-NN) are never edited.
"""

from __future__ import annotations

import os as _os
import re as _re
from dataclasses import dataclass as _dataclass
from datetime import date as _date, timedelta as _timedelta

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.tenders.tender_admin_page import TenderFieldsAdminPage
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from core.utils.logger import get_logger as _get_logger
from core.utils.waits import WaitTimeoutError as _WaitTimeoutError
from core.utils.waits import wait_until as _wait_until
from core.web.overlays import _dismiss_chatbot_launcher

_log = _get_logger("opportunity_sections_d_page")

D_QCTEST_PREFIX = "QCTEST-130697-D-"
D_ROLE_EDITOR = "Site Content Editor"
D_EDITOR_USER_ID = "156488"
REAL_OPP_CODE_PREFIX = "QC-BIZOPP-130697-"

# manage-business-opportunity keys
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
K_PICKLISTS = ("sector", "investmentType", "timeline", "riskProfile", "industryPool", "lifecycleStatus")
EXISTING_IMAGE = "6th-World-Conference-Arbitration-Eng.png"  # existing D&M root file: picked, never uploaded

# manage-opportunity-section keys
S_TITLE = "sectionTitle"
S_NUMBER = "sectionNumber"
S_ORDER = "displayOrder"
S_PARENT = "r_opportunitySections_c_businessOpportunityId"


def ddmmyyyy(d: _date) -> str:
    return d.strftime("%d/%m/%Y")


@_dataclass(frozen=True)
class DEntry:
    """Captured identity of a record this agent created."""
    title: str
    entry_id: str
    code: str

    def in_namespace(self) -> bool:
        return self.title.strip().startswith(D_QCTEST_PREFIX)


class _DBase(TenderFieldsAdminPage):
    """Generic list / identity / guarded-delete machinery for one D object."""

    SLUG = ""
    TITLE_KEY = ""
    LIST_ROW_TITLE_IS_CODE = False
    EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "evidence", "130697_d")

    def __init__(self, page):
        ObjectAuthoringPage.__init__(self, page, self.SLUG)  # skip the tender-only __init__
        self.owned_entry_ids: set[str] = set()
        self.last_uploaded_name = ""

    # ---- navigation ----------------------------------------------------------
    def open_create_form_en(self):
        self.open(self._manage_url(locale="en"))
        self._entry_code = None
        self._locale = "en"
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.wait_for(timeout=90000)
        self.page.locator(f'{self.FORM} input[name="ObjectField_{self.TITLE_KEY}"]').first.wait_for(timeout=60000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entry_en(self, code: str):
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self.page.locator(f'{self.FORM} input[name="ObjectField_{self.TITLE_KEY}"]').first.wait_for(timeout=90000)
        try:
            _wait_until(lambda: self.text_value(self.TITLE_KEY) != "", timeout=20.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    def pick_existing_image(self, key: str, file_name: str = EXISTING_IMAGE):
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

    # ---- picklists -----------------------------------------------------------------
    def pick_first(self, key: str) -> str:
        """Selects the first option of a picklist and returns its label."""
        prefix = self._picklist_prefix(key)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        toggle.click()
        option = self.page.locator(f'li[role="option"][id^="{prefix}-option-"]').first
        option.wait_for(state="visible", timeout=10000)
        label = option.get_attribute("data-option-label") or ""
        option.click()
        hidden = self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]').first
        _wait_until(lambda: hidden.input_value() != "", timeout=5.0, poll=0.25)
        if self.page.locator(f'li[role="option"][id^="{prefix}-option-"]:visible').count():
            toggle.click()
        return label

    # ---- identity / list -----------------------------------------------------------
    def snapshot_ids(self) -> set[str]:
        self.open_list_all()
        if not self.is_list_fully_expanded():
            raise AssertionError("the list did not expand to show every row; cannot snapshot ids safely")
        return {r["entry_id"] for r in self.list_rows()}

    def d_leftovers(self) -> list[dict]:
        """Read-only: rows whose own title is in the D namespace."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].startswith(D_QCTEST_PREFIX)]

    def identify_created(self, title: str, ids_before: set[str]) -> DEntry | None:
        if not title.strip().startswith(D_QCTEST_PREFIX):
            raise ValueError(f"{title!r} is not in the {D_QCTEST_PREFIX} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]]
        # Only rows NOT in the pre-snapshot are candidates. A row whose list title is a real title
        # (not the entry code) outside our prefix belongs to another agent: skip it unopened.
        # (Section / gallery lists show the code as the title, so those are always opened.)
        candidates = [r for r in fresh
                      if r["title"].strip() in ("", r["code"]) or r["title"].strip().startswith(D_QCTEST_PREFIX)]
        skipped = [f"{r['entry_id']}:{r['title']!r}" for r in fresh if r not in candidates]
        self.last_candidates = [f"{r['entry_id']}:{r['code']}:{r['title']!r}" for r in candidates]
        matches, unreadable = [], []
        for row in candidates:
            for attempt in (1, 2):
                try:
                    self.open_entry_en(row["code"])
                    opened = self.text_value(self.TITLE_KEY)
                    if opened == title and opened.startswith(D_QCTEST_PREFIX):
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
        entry = DEntry(title=title, entry_id=matches[0]["entry_id"], code=matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def adopt(self, entry: DEntry) -> DEntry:
        if not entry.in_namespace() or not entry.entry_id or not entry.code \
                or entry.code.startswith(REAL_OPP_CODE_PREFIX):
            raise ValueError(f"refusing to adopt {entry}: not a captured {D_QCTEST_PREFIX} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def row_status(self, entry: DEntry) -> str:
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return normalize_status(rows[0]["status"]) if len(rows) == 1 else ""

    def row_present(self, entry: DEntry) -> bool:
        return any(r["entry_id"] == entry.entry_id for r in self.list_rows())

    # ---- guarded delete (captured id + exact title + captured code) -------------------
    def _delete_preconditions(self, entry: DEntry) -> str:
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
        if row["code"].startswith(REAL_OPP_CODE_PREFIX):
            return f"row {entry.entry_id} carries a REAL record code {row['code']!r}"
        # The ENTRY column / delete label show the record CODE (not the title) on these objects;
        # the title itself was verified on the opened form immediately before (delete_disposable_entry).
        if row["label"].strip() not in (entry.title.strip(), entry.code):
            return f"row {entry.entry_id} label {row['label']!r} is neither the captured title nor code"
        return ""

    def delete_disposable_entry(self, entry: DEntry) -> bool:
        try:
            if (not entry.in_namespace() or not entry.entry_id or not entry.code
                    or entry.code.startswith(REAL_OPP_CODE_PREFIX)
                    or entry.entry_id not in self.owned_entry_ids):
                _log.error("DELETE REFUSED: %r is not a captured %s record", entry, D_QCTEST_PREFIX)
                return False
            self.open_entry_en(entry.code)
            live = self.text_value(self.TITLE_KEY)
            if live != entry.title:
                _log.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
                return False
            self.open_list_all()
            reason = self._delete_preconditions(entry)
            if reason:
                _log.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            reason = self._delete_preconditions(entry)  # re-check immediately before the click
            if reason:
                _log.error("DELETE REFUSED for %r on re-check: %s", entry, reason)
                return False
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                if entry.code in dialog.message or entry.title.strip() in dialog.message:
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
            if not any(entry.code in m or entry.title.strip() in m for m in dialogs):
                _log.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            return self.is_list_fully_expanded() and not self.row_present(entry)
        except Exception as exc:  # noqa: BLE001
            _log.error("delete of %r failed: %r", entry, exc)
            return False


# --- D --- parent Business Opportunity ---------------------------------------------
class BizOppParentDPage(_DBase):
    """manage-business-opportunity: creates the QCTEST parent record."""

    SLUG = "business-opportunity"
    TITLE_KEY = K_TITLE
    FORM = f'form:has(input[name="ObjectField_{K_TITLE}"])'
    SAVE_REQUEST_PATTERN = _re.compile(r"edit_info_item|/o/c/businessopportunit")

    def pick_label(self, key: str, option_label: str) -> str:
        """Picks an option by label if present, else the first option; returns what was picked."""
        prefix = self._picklist_prefix(key)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        toggle.click()
        options = self.page.locator(f'li[role="option"][id^="{prefix}-option-"]')
        options.first.wait_for(state="visible", timeout=10000)
        labels = [o.get_attribute("data-option-label") or "" for o in options.all()]
        target = options.nth(labels.index(option_label)) if option_label in labels else options.first
        picked = target.get_attribute("data-option-label") or ""
        target.click()
        if self.page.locator(f'li[role="option"][id^="{prefix}-option-"]:visible').count():
            toggle.click()
        self.last_options = {key: labels}
        return picked

    @staticmethod
    def parent_data(title: str, sort_order: str = "100", **overrides) -> dict:
        today = _date.today()
        data = {
            K_TITLE: title, f"{K_TITLE}_ar": f"{title} فرصة تجريبية",
            K_COUNTRY: "Qatar", f"{K_COUNTRY}_ar": "قطر",
            K_COMPANY: "QCTEST Company", f"{K_COMPANY}_ar": "شركة تجريبية",
            K_AMOUNT: "1000000", K_CURRENCY: "QAR", K_RANGE: "USD 1M-5M",
            K_SUBMITTER: "QCTEST Submitter", f"{K_SUBMITTER}_ar": "مقدم تجريبي",
            K_ENTITY: "Company", f"{K_ENTITY}_ar": "شركة",
            K_LOCATION: "Doha", f"{K_LOCATION}_ar": "الدوحة",
            K_PUBLISH_DATE: ddmmyyyy(today - _timedelta(days=1)),
            K_ARCHIVE_DATE: ddmmyyyy(today + _timedelta(days=365)),
            K_SORT: sort_order, "active_status": True,
            "hero": "QCTEST hero summary", "overview": "QCTEST overview body", "brief": "QCTEST investment brief",
        }
        data.update(overrides)
        return data

    def fill_parent(self, data: dict):
        for key in (K_TITLE, K_COUNTRY, K_COMPANY, K_SUBMITTER, K_ENTITY, K_LOCATION, K_CURRENCY, K_RANGE):
            if data.get(key) is not None:
                self.fill_en(key, data[key])
        for key in (K_TITLE, K_COUNTRY, K_COMPANY, K_SUBMITTER, K_ENTITY, K_LOCATION):
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, data[f"{key}_ar"])
        self.fill_number_key(K_AMOUNT, data[K_AMOUNT])
        self.picked = {key: (self.pick_label(key, "Published") if key == "lifecycleStatus" else self.pick_first(key))
                       for key in K_PICKLISTS}
        for key in K_IMAGES:
            self.pick_existing_image(key)
        for key, field in (("brief", "investmentBrief"), ("hero", "heroSummary"), ("overview", "overviewBody")):
            if data.get(key):
                self.fill_rich(field, data[key])
                self.fill_iframe_editor(f'[id="cke_qc-ar-{field}"] iframe[title="editor"]', data[key] + " AR")
        for key in (K_PUBLISH_DATE, K_ARCHIVE_DATE):
            if data.get(key):
                self.set_date(key, data[key])
        self.fill_number_key(K_SORT, data[K_SORT])
        self.set_active_status(bool(data["active_status"]))
        return self


# --- D --- Opportunity Section ------------------------------------------------------
class BizOppSectionDPage(_DBase):
    """manage-opportunity-section. The list's ENTRY column shows the record code
    (not the section title), so identity is captured as (entry id, code, stored title)."""

    SLUG = "opportunity-section"
    TITLE_KEY = S_TITLE
    FORM = f'form:has(input[name="ObjectField_{S_TITLE}"])'
    SAVE_REQUEST_PATTERN = _re.compile(r"edit_info_item|/o/c/opportunitysection")
    RELATION_KEY = S_PARENT

    def pick_parent(self, parent: DEntry, parent_entry_id: str | None = None) -> "BizOppSectionDPage":
        """Selects the QCTEST parent in the Opportunity Sections relationship picker by its
        captured entry id (option value); the option label is the record code."""
        if not parent.in_namespace() or parent.code.startswith(REAL_OPP_CODE_PREFIX):
            raise ValueError(f"refusing to link sections to {parent}: not a QCTEST-D parent")
        pid = parent_entry_id or parent.entry_id
        inp = self.page.locator(f'[id="{self._picklist_prefix(self.RELATION_KEY)}-select-from-list-input"]')
        inp.click()
        inp.fill(parent.code)
        option = self.page.locator(f'li[role="option"][data-option-value="{pid}"]')
        option.first.wait_for(state="visible", timeout=15000)
        if (option.first.get_attribute("data-option-label") or "") != parent.code:
            raise AssertionError("parent picker option does not carry the captured parent code")
        option.first.click()
        hidden = self._form().locator(f'input[type="hidden"][name="ObjectField_{self.RELATION_KEY}"]').first
        _wait_until(lambda: hidden.input_value() == pid, timeout=8.0, poll=0.25)
        return self

    def parent_value(self) -> str:
        return self._form().locator(f'input[type="hidden"][name="ObjectField_{self.RELATION_KEY}"]').first.input_value()

    def parent_label(self) -> str:
        return self._form().locator(
            f'input[type="hidden"][name="ObjectField_{self.RELATION_KEY}-label"]').first.input_value()

    def fill_section(self, title: str, number: str, order: str, active: bool = True,
                     title_ar: str | None = None, parent: DEntry | None = None) -> "BizOppSectionDPage":
        self.fill_en(S_TITLE, title)
        self.fill_ar(S_TITLE, title_ar if title_ar is not None else f"{title} AR")
        self.fill_en(S_NUMBER, number)
        self.fill_number_key(S_ORDER, order)
        self.set_active_status(active)
        if parent is not None:
            self.pick_parent(parent)
        return self

    def read_section(self) -> dict:
        return {
            "title": self.text_value(S_TITLE), "title_ar": self.ar_value(S_TITLE),
            "number": self.text_value(S_NUMBER), "order": self.text_value(S_ORDER),
            "active": self.active_status_stored(), "parent": self.parent_value(),
        }

    def title_input_maxlength(self) -> int:
        return int(self._en(S_TITLE).evaluate("e => e.maxLength"))

    # ---- guarded delete: row identity is the code, title verified on the form ------------
    def _delete_preconditions(self, entry: DEntry) -> str:
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
        if _re.match(r"^QC-BIZOPP-130697-\d\d-SEC-", row["code"]):
            return f"row {entry.entry_id} carries a REAL section code {row['code']!r}"
        if row["label"].strip() not in (entry.title.strip(), entry.code):
            return f"row {entry.entry_id} label {row['label']!r} is neither the captured title nor code"
        return ""

    def delete_disposable_entry(self, entry: DEntry) -> bool:
        try:
            if (not entry.in_namespace() or not entry.entry_id or not entry.code
                    or entry.entry_id not in self.owned_entry_ids):
                _log.error("DELETE REFUSED: %r is not a captured %s section", entry, D_QCTEST_PREFIX)
                return False
            self.open_entry_en(entry.code)
            live = self.text_value(S_TITLE)
            if live != entry.title:
                _log.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
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
                if entry.code in dialog.message or entry.title.strip() in dialog.message:
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
            if not any(entry.code in m or entry.title.strip() in m for m in dialogs):
                _log.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            return self.is_list_fully_expanded() and not self.row_present(entry)
        except Exception as exc:  # noqa: BLE001
            _log.error("delete of %r failed: %r", entry, exc)
            return False

    def identify_created(self, title: str, ids_before: set[str]) -> DEntry | None:
        """Sections: the new row whose own form reads the exact (possibly long) title."""
        return super().identify_created(title, ids_before)

    def d_leftovers(self) -> list[dict]:
        """Read-only: rows whose code is not a real section code and whose id is not in the
        baseline are checked by the caller; returns every non-real row."""
        self.open_list_all()
        return [r for r in self.list_rows() if not _re.match(r"^QC-BIZOPP-130697-\d\d-SEC-", r["code"])]



# --- D --- Project Gallery item (only to give a QCTEST parent a non-empty 03 block) ---------
class BizOppGalleryDPage(BizOppSectionDPage):
    """manage-project-gallery-item: one image child of a QCTEST parent. Never deleted on its
    own — it goes with its (captured) parent when the parent is deleted (cascade)."""

    SLUG = "project-gallery-item"
    TITLE_KEY = "displayOrder"
    FORM = 'form:has(input[name="ObjectField_galleryImage"])'
    SAVE_REQUEST_PATTERN = _re.compile(r"edit_info_item|/o/c/projectgalleryitem")
    RELATION_KEY = "r_projectGalleryItems_c_businessOpportunityId"

    def add_item(self, parent: DEntry, order: str = "100", image: str = EXISTING_IMAGE) -> "BizOppGalleryDPage":
        self.open_create_form_en()
        self.pick_parent(parent)
        self.pick_existing_image("galleryImage", image)
        self.fill_number_key("displayOrder", order)
        self.set_active_status(True)
        self.click_publish()
        return self


# --- D --- public side (reuses the web page objects; real section-nav selectors) -------------
from web.pages.business_opportunities.detail_page import BusinessOpportunityDetailPage as _DetailPO  # noqa: E402
from web.pages.business_opportunities.listing_page import BusinessOpportunitiesListingPage as _ListingPO  # noqa: E402


class BizOppDetailPublicD(_DetailPO):
    """Opportunity Detail, public. The web page object's section-index locators are still the
    TODO guesses (`.qc-bod-index-item`); the live markup (recon 2026-10-07) is
    `a.qc-bod-index-row > span.qc-bod-index-num + span.qc-bod-index-label`, href -> `#qc-bod-<block>`."""

    SECTION_INDEX_ITEM = "a.qc-bod-index-row"
    INDEX_ROWS_JS = """() => [...document.querySelectorAll('a.qc-bod-index-row')].map(a => ({
        num: (a.querySelector('.qc-bod-index-num') || {}).innerText || '',
        label: (a.querySelector('.qc-bod-index-label') || {}).innerText || '',
        href: a.getAttribute('href') || '', visible: !!(a.offsetWidth || a.offsetHeight)}))"""

    def open_detail_by_code(self, code: str, locale: str = "en", wait_s: float = 30.0) -> "BizOppDetailPublicD":
        from config.settings import web_url as _web_url  # noqa: PLC0415
        self.open(_web_url(f"/web/qatar-chamber/business-opportunity?opportunity={code}", locale=locale))
        try:
            self.page.locator("h1.qc-bod-title").first.wait_for(state="visible", timeout=int(wait_s * 1000))
        except Exception:  # noqa: BLE001 — "Opportunity not found" or still loading
            pass
        return self

    def detail_available(self) -> bool:
        return self.page.locator("h1.qc-bod-title").first.is_visible()

    def wait_index(self, timeout: float = 20.0) -> list[dict]:
        try:
            _wait_until(lambda: len(self.index_rows()) > 0, timeout=timeout, poll=0.5)
        except _WaitTimeoutError:
            pass
        return self.index_rows()

    def index_rows(self) -> list[dict]:
        return self.page.evaluate(self.INDEX_ROWS_JS)

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def click_row_and_target_top(self, index: int) -> dict:
        """Clicks the nth nav row; returns where its target block sits after the scroll."""
        row = self.page.locator(self.SECTION_INDEX_ITEM).nth(index)
        href = row.get_attribute("href") or ""
        row.click()
        target_id = href.lstrip("#")
        result = {"href": href, "top": None, "in_view": False}

        def _scrolled() -> bool:
            top = self.page.evaluate(
                "(id) => { const e = document.getElementById(id); return e ? e.getBoundingClientRect().top : null; }",
                target_id)
            result["top"] = top
            vh = self.page.evaluate("() => window.innerHeight")
            result["in_view"] = top is not None and -5 <= top < vh * 0.6
            return result["in_view"]

        try:
            _wait_until(_scrolled, timeout=8.0, poll=0.4)
        except _WaitTimeoutError:
            pass
        return result

    def text_visibility(self, snippet: str) -> dict:
        """Rendered visibility of text (not DOM presence): every element whose own text contains `snippet`,
        with checkVisibility() / non-zero box / inside the nav or not."""
        return self.page.evaluate(
            """(snip) => {
              const norm = t => (t || '').trim();
              const hits = [];
              const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
              while (w.nextNode()) {
                const n = w.currentNode;
                if (!norm(n.nodeValue).includes(snip)) continue;
                const el = n.parentElement, r = el.getBoundingClientRect();
                const shown = el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true}) && r.width > 0 && r.height > 0;
                hits.push({tag: el.tagName, cls: el.className && String(el.className).slice(0, 60),
                           in_nav: !!el.closest('a.qc-bod-index-row'), shown: shown,
                           w: Math.round(r.width), h: Math.round(r.height)});
              }
              return {hits: hits, visible_in_nav: hits.some(h => h.in_nav && h.shown),
                      visible_anywhere: hits.some(h => h.shown)};
            }""", snippet)

    def layout_report(self) -> dict:
        """Overflow facts for the section nav (rule 7: 'UI broken?')."""
        return self.page.evaluate(
            """() => {
              const de = document.documentElement, vw = window.innerWidth;
              const rows = [...document.querySelectorAll('a.qc-bod-index-row')].map(a => {
                const l = a.querySelector('.qc-bod-index-label') || a, r = a.getBoundingClientRect(), lr = l.getBoundingClientRect();
                return {text: l.innerText, rowRight: Math.round(r.right), rowLeft: Math.round(r.left),
                        labelClipped: l.scrollWidth > l.clientWidth + 1, labelRight: Math.round(lr.right),
                        labelHeight: Math.round(lr.height), display: getComputedStyle(a).display,
                        rowVisible: !!(a.offsetWidth || a.offsetHeight)};
              });
              const nav = document.querySelector('aside.qc-bod-index, nav.qc-bod-index-card');
              const nr = nav ? nav.getBoundingClientRect() : null;
              return {viewport: vw, pageScrollWidth: de.scrollWidth, pageOverflowX: de.scrollWidth > vw + 1,
                      navVisible: !!(nav && (nav.offsetWidth || nav.offsetHeight)),
                      navRight: nr ? Math.round(nr.right) : null, rows: rows};
            }""")


class BizOppListingPublicD(_ListingPO):
    """Business Opportunities listing, public: Load More-aware reads."""

    def open_expanded(self, locale: str = "en") -> "BizOppListingPublicD":
        self.open_listing(locale)
        for _ in range(12):
            if not self.is_load_more_visible():
                break
            before = self.card_count()
            self.click_load_more()
            try:
                _wait_until(lambda: self.card_count() > before, timeout=10.0, poll=0.4)
            except _WaitTimeoutError:
                break
        return self

    def default_sort(self) -> str:
        return self.selected_sort_value()

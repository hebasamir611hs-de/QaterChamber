"""
cms/pages/media_center/mc_feed_section_admin_page.py — Media Center Feed
Section (Object `MediaCenterFeedSection`, slug `media-center-feed-section`)
Object Authoring driver + the public Media Center hub's feed-section view,
for PBI 130709 (suite 140368, FEED agent).

LIVE RECON 2026-10-07 (QC Site Content Editor 156488, read-only):

  Form (`ObjectField_<key>` EN, `qc-ar-<key>` AR twin):
    sectionHeading  (text, counter 0/150, AR twin required)  <- ENTRY column
    sectionType     (picklist: News & Press Releases=newsPressReleases,
                     Photo Gallery=photoGallery, Video Gallery=videoGallery)
    eyebrow         (text, counter 0/60, AR twin)
    ctaLabel        (text, counter 0/50, AR twin)
    ctaDestination  (text, no counter)
    displayOrder    (number)
    activeStatus    (checkbox, unticked on a new entry)
  No "number of items previewed" and no "display mode" field exist.
  Editor buttons: "Save as Draft" / "Publish" (Author: "Submit for Review").
  Real rows: QCDEMO-130709-FEED-01..03 (News & press releases / Photo Gallery
  / Video Gallery, Display Order 100/200/300) — NEVER acted on here.

  Public hub (/web/qatar-chamber/media-center): THREE fixed fragments placed
  in the page layout — qc-mc-nf (news), qc-mc-pf (photo), qc-mc-vf (video) —
  each bound to ONE sectionType key (`data-qc-mc?f-section-key`). Each reads
  `/o/c/mediacenterfeedsections/scopes/<group>?pageSize=50` and takes the
  FIRST item whose sectionType matches its key; that item only supplies the
  chrome (eyebrow / heading / CTA label + href). The feed cards come from the
  module endpoints, not from the section record.

DELETE SAFETY (user's standing rule): `delete_disposable_entry()` deletes ONLY
a `FeedEntry` this session captured (list-id diff + exact heading read back by
code) whose heading is in the QCTEST-130709-FS- namespace and whose code is not
QCDEMO-, re-verified immediately before the click; the confirm() must name the
entry. No positional, looping or substring delete exists in this module.
"""

from __future__ import annotations

import contextlib as _contextlib
import json as _json
import os as _os
import re as _re
from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime

from cms.pages.tenders.tender_admin_page import TenderWorkflowAdminPage
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import web_url
from core.utils.logger import get_logger as _get_logger
from core.utils.waits import WaitTimeoutError as _WaitTimeoutError
from core.utils.waits import wait_until as _wait_until
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher, dismiss_overlays

_logger = _get_logger("mc_feed_section_admin_page")

SLUG = "media-center-feed-section"
RESOURCE = "mediacenterfeedsections"
PREFIX = "QCTEST-130709-FS-"
REAL_CODE_PREFIX = "QCDEMO-"
REAL_CODES = ("QCDEMO-130709-FEED-01", "QCDEMO-130709-FEED-02", "QCDEMO-130709-FEED-03")

K_HEADING = "sectionHeading"
K_TYPE = "sectionType"
K_EYEBROW = "eyebrow"
K_CTA_LABEL = "ctaLabel"
K_CTA_DEST = "ctaDestination"
K_ORDER = "displayOrder"
# Added by the 149909 fix (2026-10-13): whole number 1..12 + Grid/Carousel picklist.
K_ITEMS = "itemsPreviewed"
K_MODE = "displayMode"
MODE_GRID = "Grid"
MODE_CAROUSEL = "Carousel"
TEXT_KEYS = (K_HEADING, K_EYEBROW, K_CTA_LABEL, K_CTA_DEST)
AR_KEYS = (K_HEADING, K_EYEBROW, K_CTA_LABEL)

TYPE_NEWS = "News & Press Releases"
TYPE_PHOTO = "Photo Gallery"
TYPE_VIDEO = "Video Gallery"
TYPE_KEYS = {TYPE_NEWS: "newsPressReleases", TYPE_PHOTO: "photoGallery", TYPE_VIDEO: "videoGallery"}

ROLE_EDITOR = "Site Content Editor"
ROLE_USER_IDS = {ROLE_EDITOR: "156488"}
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_ARABIC_SAVED = "Arabic content saved for this record."
MSG_ARABIC_REQUIRED = "Arabic content is required."
MSG_REQUIRED_BLOCK = "Please complete the required fields"

MEDIA_CENTER_PATH = "/web/qatar-chamber/media-center"


@_dataclass(frozen=True)
class FeedEntry:
    """Identity of ONE QCTEST feed section this session created. `heading` is
    the stored Section Heading (the list's ENTRY column)."""

    heading: str
    entry_id: str
    code: str

    def in_namespace(self) -> bool:
        return (self.heading.strip().startswith(PREFIX) and bool(self.entry_id) and bool(self.code)
                and not self.code.upper().startswith(REAL_CODE_PREFIX) and self.code not in REAL_CODES)

    def with_heading(self, heading: str) -> "FeedEntry":
        return FeedEntry(heading=heading, entry_id=self.entry_id, code=self.code)


class McFeedSectionAdminPage(TenderWorkflowAdminPage):
    """`manage-media-center-feed-section` driver. Reuses the confirmed-live
    Object Authoring mechanics of TenderFieldsAdminPage / TenderWorkflowAdminPage
    (role login, Load-All list, id-scoped row actions, save-outcome probe,
    field access by `ObjectField_<key>` / `qc-ar-<key>`, picklists, History);
    every tender-specific identity / data / delete method is overridden or
    disabled below."""

    FORM = 'form:has([name^="ObjectField_"])'
    EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "mc130709", "feed")
    SAVE_REQUEST_PATTERN = _re.compile(rf"edit_info_item|/o/c/{RESOURCE}")

    def __init__(self, page):
        super().__init__(page)
        self.slug = SLUG

    # ---- navigation ----------------------------------------------------------------
    def open_entry_en(self, code: str) -> "McFeedSectionAdminPage":
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self.page.locator(f'{self.FORM} [name="ObjectField_{K_HEADING}"]').first.wait_for(
            state="attached", timeout=90000)
        try:
            _wait_until(lambda: self.text_value(K_HEADING) != "" or self.text_value(K_CTA_DEST) != "",
                        timeout=15.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    # ---- identity -------------------------------------------------------------------
    def leftovers(self) -> list[dict]:
        """Read-only: rows whose ENTRY text is in the QCTEST-130709-FS- namespace."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].strip().startswith(PREFIX)]

    def identify_created(self, heading: str, ids_before: set[str]) -> FeedEntry | None:
        """The ONE new row (id absent before, not QCDEMO-) whose ENTRY cell
        reads `heading` and whose own form reads it back exactly."""
        if not heading.startswith(PREFIX):
            raise ValueError(f"{heading!r} is not in the {PREFIX} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].upper().startswith(REAL_CODE_PREFIX)
                 and r["title"].strip() == heading.strip()]
        matches = []
        for row in fresh:
            for attempt in (1, 2):
                try:
                    self.open_entry_en(row["code"])
                    if self.text_value(K_HEADING).strip() == heading.strip():
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — an unreadable row is not ours
                    _logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            _logger.warning("identify_created(%r): %s matches among %s", heading, len(matches), fresh)
            return None
        entry = FeedEntry(heading=matches[0]["title"].strip(), entry_id=matches[0]["entry_id"],
                          code=matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def new_rows_since(self, ids_before: set[str]) -> list[dict]:
        """Read-only: every row whose id was absent from `ids_before`."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["entry_id"] not in ids_before]

    def adopt(self, entry: FeedEntry) -> FeedEntry:  # type: ignore[override]
        if not isinstance(entry, FeedEntry) or not entry.in_namespace():
            raise ValueError(f"refusing to adopt {entry}: not a captured {PREFIX} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def row_of(self, entry: FeedEntry) -> dict:
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return rows[0] if len(rows) == 1 else {}

    def row_status_of(self, entry: FeedEntry) -> str:
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        row = self.row_of(entry)
        return normalize_status(" ".join(row.get("status", "").split())) if row else ""

    def last_modified_of(self, entry: FeedEntry) -> str:
        """The row's Last modified cell text ("" when the row is gone)."""
        cells = self._row_a(entry).first.locator("td")
        return cells.nth(2).inner_text().strip() if cells.count() > 2 else ""

    def wait_row_status(self, entry: FeedEntry, expected: tuple, timeout: float = 120.0) -> str:
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

    # ---- guarded delete -------------------------------------------------------------
    def _delete_preconditions(self, entry: FeedEntry) -> str:  # type: ignore[override]
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
            return f"row {entry.entry_id} points at {row['code']!r}, not the captured {entry.code!r}"
        if row["title"].strip() != entry.heading.strip() or row["label"].strip() != entry.heading.strip():
            return f"row {entry.entry_id} shows {row['title']!r} / label {row['label']!r}, not {entry.heading!r}"
        return ""

    def delete_disposable_entry(self, entry: FeedEntry) -> bool:  # type: ignore[override]
        """Deletes exactly the captured record or refuses (False, never raises)."""
        try:
            if (not isinstance(entry, FeedEntry) or not entry.in_namespace()
                    or entry.entry_id not in self.owned_entry_ids):
                _logger.error("DELETE REFUSED: %r is not a captured %s record", entry, PREFIX)
                return False
            self.open_entry_en(entry.code)
            live = self.text_value(K_HEADING).strip()
            if live != entry.heading.strip():
                _logger.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
                return False
            self.open_list_all()
            reason = self._delete_preconditions(entry) or self._delete_preconditions(entry)
            if reason:
                _logger.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            names = [n for n in (entry.heading.strip(), entry.code) if n]
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

    def restore_heading(self, entry: FeedEntry) -> bool:
        """If a test's own save emptied/changed the heading of ITS OWN record,
        put the captured heading back (so the guarded delete can re-verify)."""
        try:
            self.open_entry_en(entry.code)
            if self.text_value(K_HEADING).strip() == entry.heading.strip():
                return True
            for key in (K_HEADING, K_EYEBROW, K_CTA_LABEL):
                if not self.text_value(key).strip():
                    self.fill_en(key, entry.heading if key == K_HEADING else "QCTEST restore")
            for key in AR_KEYS:
                if not self.ar_value(key).strip():
                    self.fill_ar(key, "QCTEST استعادة")
            if not self.text_value(K_CTA_DEST).strip():
                self.fill_en(K_CTA_DEST, "/web/qatar-chamber/video-library")
            if not self.text_value(K_ORDER).strip():
                self.fill_en(K_ORDER, "1000")
            self.fill_en(K_HEADING, entry.heading)
            self.click_publish()
            self.open_entry_en(entry.code)
            return self.text_value(K_HEADING).strip() == entry.heading.strip()
        except Exception as exc:  # noqa: BLE001
            _logger.error("restore_heading(%r) failed: %r", entry, exc)
            return False

    # ---- fields ------------------------------------------------------------------------
    def fill_data(self, data: dict) -> "McFeedSectionAdminPage":
        """Fills every key `data` carries (None = untouched): EN text keys,
        `<key>_ar`, `sectionType` (option label), `displayOrder`, `activeStatus`."""
        for key in TEXT_KEYS:
            if data.get(key) is not None:
                self.fill_en(key, str(data[key]))
        for key in AR_KEYS:
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, str(data[f"{key}_ar"]))
        if data.get(K_TYPE):
            self.pick(K_TYPE, data[K_TYPE])
        if data.get(K_ORDER) is not None:
            self.fill_en(K_ORDER, str(data[K_ORDER]))
        if data.get("activeStatus") is not None:
            self.set_active_status(bool(data["activeStatus"]))
        if data.get(K_ITEMS) is not None:
            self.fill_en(K_ITEMS, str(data[K_ITEMS]))
        if data.get(K_MODE):
            self.pick(K_MODE, data[K_MODE])
        return self

    # ---- list ---------------------------------------------------------------------------
    ADD_NEW_CONTROL = 'button:visible, a:visible'
    ADD_NEW_RE = _re.compile(r"^\s*\+?\s*Add New", _re.I)

    def add_new_offered(self) -> list[str]:
        """Visible '+ Add New' controls on the manage list (149911: must be none)."""
        texts = [(t or "").strip() for t in self.page.locator(self.ADD_NEW_CONTROL).all_inner_texts()]
        return [t for t in texts if self.ADD_NEW_RE.search(t)]

    def list_row_codes(self) -> list[str]:
        return [r.get("code", "") for r in self.list_rows()]

    def read_data(self) -> dict:
        values = {key: self.text_value(key) for key in TEXT_KEYS}
        values.update({f"{key}_ar": self.ar_value(key) for key in AR_KEYS})
        values[K_TYPE] = self.picklist_value(K_TYPE)
        values[K_ORDER] = self.text_value(K_ORDER)
        values["activeStatus"] = self.active_status_stored()
        return values

    def wait_arabic_saved(self, timeout: float = 20.0) -> bool:
        """A brand-new record saves its Arabic a moment later (guide §5)."""
        def _seen() -> bool:
            body = self.page.locator("body").inner_text()
            return MSG_ARABIC_SAVED in body or "Arabic content was not" in body
        try:
            _wait_until(_seen, timeout=timeout, poll=0.5)
            return MSG_ARABIC_SAVED in self.page.locator("body").inner_text()
        except _WaitTimeoutError:
            return False

    def ar_direction(self, key: str) -> str:
        return self._ar(key).evaluate("el => getComputedStyle(el).direction")

    def counter_limit(self, key: str) -> int | None:
        """N of the live "<len> / N" counter under the EN field (None = no counter)."""
        text = self._en(key).evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 4 && c; i++, c = c.parentElement) {
                           const m = (c.innerText || '').match(/(\\d+)\\s*\\/\\s*(\\d+)/); if (m) return m[2]; }
                       return ''; }""")
        return int(text) if text else None

    def native_max_length(self, key: str, arabic: bool = False) -> int:
        node = self._ar(key) if arabic else self._en(key)
        return int(node.evaluate("el => el.maxLength"))

    def type_en(self, key: str, value: str) -> "McFeedSectionAdminPage":
        """Clears then TYPES key by key (so a maxlength/JS limiter acts as for a user)."""
        box = self._en(key)
        box.fill("")
        box.type(value, delay=5)
        return self

    def picklist_options(self, key: str = K_TYPE) -> list[str]:
        """Labels of every option the picklist offers (dropdown opened then closed)."""
        prefix = self._picklist_prefix(key)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        toggle.click()
        options = self.page.locator(f'li[role="option"][id^="{prefix}-option-"]')
        options.first.wait_for(state="visible", timeout=10000)
        labels = [(o.get_attribute("data-option-label") or o.inner_text()).strip() for o in options.all()]
        self.page.keyboard.press("Escape")
        return labels

    def form_field_inventory(self) -> list[dict]:
        """Every visible authoring control of the form: {key, label, type}."""
        return self.page.evaluate(
            """(sel) => { const form = document.querySelector(sel); if (!form) return [];
                const out = [];
                for (const el of form.querySelectorAll('input, select, textarea, iframe[title="editor"]')) {
                    if (el.type === 'hidden') continue;
                    const r = el.getBoundingClientRect(); if (!r.width && !r.height) continue;
                    const key = (el.name || '').replace('ObjectField_', '') || el.id || '';
                    let c = el.parentElement, label = '';
                    for (let i = 0; i < 5 && c && !label; i++, c = c.parentElement) {
                        const l = c.querySelector('label'); if (l) label = l.innerText.trim(); }
                    out.push({key: key, label: label, type: el.type || el.tagName.toLowerCase()});
                }
                return out; }""",
            self.FORM)

    def form_text(self) -> str:
        return " ".join(self._form().inner_text().split())

    # ---- tender-specific helpers are not valid here ---------------------------------------
    def _not_feed(self, *_a, **_k):
        raise NotImplementedError("tender-specific helper; use the McFeedSectionAdminPage API")

    fill_tender = fill_tender_a = read_tender = a_tender_data = _not_feed
    identify_created_a = adopt_a = delete_own_entry = a_leftovers = b_leftovers = _not_feed
    row_status_a = wait_status = fill_reference_number = fill_valid_form = _not_feed
    row_status_text_for_reference = upload_tender_document = upload_boq = _not_feed
    delete_entry_by_code = delete_entry_by_title = delete_all_entries_by_title = delete_own_entry_d = _not_feed


class MediaCenterPublicView(BasePage):
    """The public Media Center hub, read in a logged-out context. Feed-section
    chrome is read off the three fixed fragments (see module docstring)."""

    SECTION_SEL = '[data-qc-mcnf-section-object], [data-qc-mcpf-section-object], [data-qc-mcvf-section-object]'

    _SECTIONS_JS = """(sel) => [...document.querySelectorAll(sel)].map((s, i) => {
        const p = ['mcnf', 'mcpf', 'mcvf'].find(x => s.hasAttribute('data-qc-' + x + '-section-object'));
        const q = (a) => s.querySelector('[data-qc-' + p + '-' + a + ']');
        const vis = (el) => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
        const ctas = [...s.querySelectorAll('[data-qc-' + p + '-cta]')];
        const cta = ctas.find(vis) || ctas[0] || null;
        const lbl = cta ? cta.querySelector('[data-qc-' + p + '-cta-label]') : null;
        const r = s.getBoundingClientRect();
        const box = (el) => { if (!el) return null; const b = el.getBoundingClientRect();
            return {width: b.width, left: b.left, right: b.right, scroll_width: el.scrollWidth,
                    client_width: el.clientWidth, direction: getComputedStyle(el).direction,
                    overflow: getComputedStyle(el).overflow, text_overflow: getComputedStyle(el).textOverflow}; };
        return {index: i, fragment: p, key: s.getAttribute('data-qc-' + p + '-section-key'),
                hidden: s.hidden || !vis(s), top: r.top + window.scrollY, dir: s.getAttribute('dir'),
                eyebrow: q('eyebrow') ? q('eyebrow').textContent.trim() : '',
                heading: q('heading') ? q('heading').textContent.trim() : '',
                cta_label: lbl ? lbl.textContent.trim() : '', cta_href: cta ? cta.getAttribute('href') : '',
                cta_box: box(lbl), cta_anchor_box: box(cta),
                cards: s.querySelectorAll('a[class*="-card"], article[class*="-card"]').length,
                viewport: window.innerWidth};
    })"""

    def open_hub(self, locale: str = "en") -> "MediaCenterPublicView":
        self.open(web_url(MEDIA_CENTER_PATH, locale=locale))
        dismiss_overlays(self.page, grace_ms=1500)
        try:
            self.page.wait_for_selector(self.SECTION_SEL, state="attached", timeout=30000)
        except Exception:  # noqa: BLE001 — reported by the readers below
            pass
        return self

    def sections(self) -> list[dict]:
        return self.page.evaluate(self._SECTIONS_JS, self.SECTION_SEL)

    def section_with(self, field: str, value: str) -> dict | None:
        for s in self.sections():
            if " ".join(s.get(field, "").split()) == " ".join(value.split()):
                return s
        return None

    def poll_sections(self, predicate, timeout: float = 40.0, locale: str = "en") -> tuple[bool, list[dict]]:
        """Re-opens the hub until `predicate(sections)` holds or `timeout` passes."""
        seen = {"sections": []}

        def _ok() -> bool:
            self.open_hub(locale)
            try:
                _wait_until(lambda: all(s["eyebrow"] or s["hidden"] for s in self.sections()), timeout=10.0,
                            poll=0.5)
            except _WaitTimeoutError:
                pass
            seen["sections"] = self.sections()
            return bool(predicate(seen["sections"]))

        try:
            _wait_until(_ok, timeout=timeout, poll=2.0)
            return True, seen["sections"]
        except _WaitTimeoutError:
            return False, seen["sections"]

    def lang_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir') || ''")

    def follow_cta(self, section_index: int) -> str:
        """Clicks the visible CTA of the n-th feed section; returns the landing URL."""
        cta = self.page.locator(self.SECTION_SEL).nth(section_index).locator(
            '[data-qc-mcnf-cta]:visible, [data-qc-mcpf-cta]:visible, [data-qc-mcvf-cta]:visible').first
        with self.page.expect_navigation(timeout=60000):
            cta.click()
        return self.page.url

    def evidence(self, path: str, full_page: bool = True) -> str:
        _os.makedirs(_os.path.dirname(path), exist_ok=True)
        try:
            self.page.screenshot(path=path, full_page=full_page)
        except Exception as exc:  # noqa: BLE001 — evidence only
            _logger.warning("public evidence %s failed: %r", path, exc)
        return path


# ===========================================================================
# REAL entries — lock + snapshot -> edit -> restore -> diff (user rule 4b,
# approved by the user 2026-10-12). Never delete, never unpublish.
# ===========================================================================
REAL_IDS = {"QCDEMO-130709-FEED-01": "206621", "QCDEMO-130709-FEED-02": "206629",
            "QCDEMO-130709-FEED-03": "206637"}
_PUT_KEYS = ("externalReferenceCode", "defaultLanguageId", "sectionHeading", "sectionHeading_i18n", "eyebrow",
             "eyebrow_i18n", "ctaLabel", "ctaLabel_i18n", "ctaDestination", "displayOrder", "activeStatus",
             "itemsPreviewed")
_LOCK_DIR = _os.getenv(
    "QC_MC_FEED_SCRATCH_DIR",
    r"C:\Users\HP\AppData\Local\Temp\claude\d--Qatar-Chamber-QaterChamber-main"
    r"\de2eae66-6f02-4a22-8869-a22476b25d22\scratchpad",
)


def comparable(record: dict) -> dict:
    """The authored state of a feed record (volatile keys dropped)."""
    return {
        "externalReferenceCode": record.get("externalReferenceCode"),
        "sectionHeading_i18n": record.get("sectionHeading_i18n"),
        "eyebrow_i18n": record.get("eyebrow_i18n"),
        "ctaLabel_i18n": record.get("ctaLabel_i18n"),
        "ctaDestination": record.get("ctaDestination"),
        "displayOrder": record.get("displayOrder"),
        "sectionType": (record.get("sectionType") or {}).get("key"),
        "activeStatus": record.get("activeStatus"),
        "itemsPreviewed": record.get("itemsPreviewed"),
        "displayMode": (record.get("displayMode") or {}).get("key"),
        "status": (record.get("status") or {}).get("code"),
    }


def record_diff(before: dict, after: dict) -> list[str]:
    a, b = comparable(before), comparable(after)
    return [f"{k}: {_json.dumps(a.get(k), ensure_ascii=False)} -> {_json.dumps(b.get(k), ensure_ascii=False)}"
            for k in a if a.get(k) != b.get(k)]


class RealFeedLock:
    """File lock per real feed record (one writer at a time in this suite)."""

    def __init__(self, entry_id: str):
        self.path = _os.path.join(_LOCK_DIR, "locks", f"mc_feed_{entry_id}.lock")
        self.token = f"FEED {_datetime.now().isoformat(timespec='seconds')} pid={_os.getpid()}"
        self.held = False

    def try_acquire(self) -> bool:
        _os.makedirs(_os.path.dirname(self.path), exist_ok=True)
        try:
            fd = _os.open(self.path, _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY)
        except FileExistsError:
            return False
        with _os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(self.token)
        self.held = True
        return True

    def still_mine(self) -> bool:
        try:
            with open(self.path, encoding="utf-8") as handle:
                return self.held and handle.read().strip() == self.token
        except OSError:
            return False

    def release(self) -> None:
        if self.still_mine():
            _os.remove(self.path)
        self.held = False


@_contextlib.contextmanager
def real_feed_lock(entry_id: str, timeout_s: float = 600.0):
    lock = RealFeedLock(entry_id)
    try:
        _wait_until(lock.try_acquire, timeout=timeout_s, poll=3.0)
    except _WaitTimeoutError:
        raise TimeoutError(f"{lock.path} still held after {timeout_s:.0f}s") from None
    try:
        yield lock
    finally:
        lock.release()


class ConcurrentChangeError(AssertionError):
    """Someone else changed a real record during our window — never overwrite."""

    def __init__(self, code: str, diff: list[str]):
        super().__init__(f"{code} changed by someone else during the test window: {diff}")
        self.code, self.diff = code, diff


class RealFeedSectionAdminPage(McFeedSectionAdminPage):
    """Edits ONE real QCDEMO-130709-FEED-0x record under its lock. Restore
    re-sends the snapshot through the headless PUT the authoring page uses."""

    def __init__(self, page, code: str, lock: RealFeedLock):
        super().__init__(page)
        if code not in REAL_IDS:
            raise ValueError(f"{code!r} is not a real feed entry")
        self.code, self.entry_id, self.lock = code, REAL_IDS[code], lock

    def _require_lock(self) -> None:
        if self.lock is None or not self.lock.still_mine():
            raise PermissionError(f"refusing to change {self.code} without holding its lock")

    def _fetch(self, method: str, body: dict | None = None) -> list:
        self.page.wait_for_function("() => window.Liferay && Liferay.authToken", timeout=30000)
        return self.page.evaluate(
            """async ([m, u, b]) => { const o = {method: m, headers: {'Accept': 'application/json',
                    'Content-Type': 'application/json', 'x-csrf-token': Liferay.authToken}};
                if (b) o.body = JSON.stringify(b);
                const r = await fetch(u, o); return [r.status, await r.text()]; }""",
            [method, f"/o/c/{RESOURCE}/{self.entry_id}", body])

    def api_get(self) -> dict:
        for attempt in range(1, 5):
            try:
                status, text = self._fetch("GET")
                if status == 200:
                    data = _json.loads(text)
                    if data.get("externalReferenceCode") != self.code:
                        raise ValueError(f"id {self.entry_id} is {data.get('externalReferenceCode')}")
                    return data
            except ValueError:
                raise
            except Exception as exc:  # noqa: BLE001 — navigation in flight; retried
                _logger.warning("api_get attempt %s: %r", attempt, exc)
            self.page.wait_for_timeout(2000)
            self.open_list_all()
        raise AssertionError(f"GET {self.code} failed")

    def guard_unchanged(self, expected: dict) -> None:
        """Concurrency guard: the live record must equal `expected`."""
        diff = record_diff(expected, self.api_get())
        if diff:
            raise ConcurrentChangeError(self.code, diff)

    def edit_via_form(self, data: dict, expected_before: dict) -> dict:
        """The case's own steps: Edit -> change fields -> Publish (guarded)."""
        self._require_lock()
        self.open_entry_en(self.code)
        self.guard_unchanged(expected_before)
        self.fill_data(data)
        self._require_lock()
        self.click_publish()
        return {"went_through": self.save_went_through(), "refused": self.save_was_refused(),
                "messages": self.all_messages_text(), "evidence": self.refusal_evidence()}

    def restore_exact(self, snapshot: dict) -> int:
        self._require_lock()
        if snapshot.get("externalReferenceCode") != self.code or str(snapshot.get("id")) != self.entry_id:
            raise AssertionError(f"snapshot is not {self.code}")
        body = {k: snapshot[k] for k in _PUT_KEYS if k in snapshot}
        body["sectionType"] = {"key": (snapshot.get("sectionType") or {}).get("key")}
        if snapshot.get("displayMode"):
            body["displayMode"] = {"key": (snapshot.get("displayMode") or {}).get("key")}
        status, text = self._fetch("PUT", body)
        self.last_restore_response = (status, text[:300])
        _logger.info("%s exact restore PUT -> %s", self.code, status)
        return int(status)

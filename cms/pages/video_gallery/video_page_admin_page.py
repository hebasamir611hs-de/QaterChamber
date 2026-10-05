"""
cms/pages/video_gallery/video_page_admin_page.py — Agent VB page objects for
PBI 130715 (Video Gallery), suite 140374, cases 143018-143040.

Two things live here:

1. `VideoPageSettingsLookupVB` — READ-ONLY discovery of the "Video Library page
   content settings" (Page Title, Hero Background Image, Page Status,
   Created / Last Modified) that cases 143018-143025, 143028, 143029 target.

   LIVE 2026-10-05 (Site Content Editor 156488, /web/qatar-chamber/object-authoring):
     - The index lists NO Video Library page / hero object. Media objects
       present: Photo Album, Photo Gallery Event Category, Photo Gallery Page
       Hero (`manage-page-hero`), Uploaded Photos Album, Flickr Album, Flickr
       Video, Video Category, Video Record, Media Center Hero/Feed/... .
     - `manage-page-hero` ("Photo Gallery Page Hero": pageTitle* +
       qc-ar-pageTitle*, heroBackgroundImage* "Upload a .jpg,.jpeg,.png no
       larger than 2 MB.", activeStatus) holds exactly 2 records, "Photo
       Albums" and "Album details"; its Preview tabs are "Photo Album
       (detail)" / "Photo Albums (listing)" / "Field view" — it renders on the
       Photo pages only, never on /video-library.
     - Video Record / Video Category previews offer only "Video Library
       (listing)"; neither carries a page title / hero image / page status.
     - Public /web/qatar-chamber/video-library: the hero title "Video Library"
       / "مكتبة الفيديوهات" and the background
       `/documents/37246/124058/video-library-hero-band.jpg` are fixed in two
       separate EN/AR page fragments (fragment-a90499bd… / fragment-550d35a7…),
       not bound to any authoring object.
   This class never writes anything; it only reads the index / preview tabs
   and takes evidence screenshots.

2. `VideoCategoryFieldsVB` — field-level helpers for `manage-video-category`,
   subclassing Agent VA's core `VideoCategoryAdminPage` (all session, list,
   save-probe and guarded-delete machinery is VA's; nothing is overridden in
   a way that weakens the DELETE SAFETY rules in video_record_admin_page.py).
   Additions: keystroke Display Order entry (a non-numeric value behaves as
   for a real user), identity capture by the Arabic name for records whose
   English name is blank/whitespace, and a guarded "rename own record into
   the namespace" step so such a record can then go through VA's normal
   guarded delete.

Data namespace: QCTEST-130715-VB- (never another prefix).
"""

from __future__ import annotations

import os as _os
import re

from cms.pages.video_gallery.video_category_admin_page import (
    KC_DISPLAY_ORDER,
    KC_NAME,
    VideoCategoryAdminPage,
)
from cms.pages.video_gallery.video_record_admin_page import (
    REAL_CATEGORY_IDS,
    REAL_CODE_PREFIX,
    VideoDetailsPublicView,
    VideoGalleryEntry,
    VideoLibraryPublicView,
)
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import control_panel_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until

_logger = get_logger("video_page_admin_page_vb")

# --- VB ---
VB_PREFIX = "QCTEST-130715-VB-"
OBJECT_AUTHORING_PATH = "/en/web/qatar-chamber/object-authoring"
PAGE_HERO_SLUG = "page-hero"
PREVIEW_HEADING = "Preview — how this record renders on the site"
VIDEO_PAGE_PATTERN = re.compile(r"video", re.I)
PAGE_SETTINGS_PATTERN = re.compile(r"page|hero|settings|librar", re.I)


class VideoPageSettingsLookupVB(VideoCategoryAdminPage):
    """Read-only lookup for a Video Library page-settings object (see module docstring)."""

    NAV_LINK = "a[href*='/manage-']"
    PREVIEW_TAB = "[data-qc-oel-preview-tab], .qc-oel__preview-tab, .qc-oel__tab"

    def __init__(self, page):
        super().__init__(page, VB_PREFIX)

    def authoring_objects(self) -> list[tuple[str, str]]:
        """[(label, manage path)] of every Object listed on the authoring index."""
        self.open(control_panel_url(OBJECT_AUTHORING_PATH))
        self.page.locator(self.NAV_LINK).first.wait_for(timeout=90000)
        links = self.page.eval_on_selector_all(
            self.NAV_LINK, "els => els.map(e => [e.innerText.trim(), (e.getAttribute('href') || '').split('?')[0]])")
        return sorted({(t, h) for t, h in links if t})

    def video_page_objects(self) -> list[tuple[str, str]]:
        """Objects whose label/path mentions video AND page/hero/settings/library."""
        return [(t, h) for t, h in self.authoring_objects()
                if VIDEO_PAGE_PATTERN.search(t + h) and PAGE_SETTINGS_PATTERN.search(t + h)]

    def preview_panel_text(self, slug: str) -> str:
        """The Preview panel's tab strip text of manage-<slug> (which public pages render it)."""
        self.open(control_panel_url(f"/en/web/qatar-chamber/manage-{slug}"))
        self.page.get_by_text(PREVIEW_HEADING).first.wait_for(timeout=90000)
        try:
            wait_until(lambda: "Field view" in self.rendered_body_text(), timeout=20.0, poll=0.5)
        except WaitTimeoutError:
            pass
        text = self.rendered_body_text()
        start = text.find(PREVIEW_HEADING)
        end = text.find("Previewing", start)
        return " | ".join(ln.strip() for ln in text[start:end if end > start else start + 300].splitlines()
                          if ln.strip())

    def page_hero_rows(self) -> list[dict]:
        """Rows of manage-page-hero (read-only)."""
        self.open(control_panel_url(f"/en/web/qatar-chamber/manage-{PAGE_HERO_SLUG}"))
        self.wait_for(self.LIST_LOADED, first=True, timeout=90000)
        return self.list_rows()

    def page_hero_form_fields(self) -> list[str]:
        return self.page.eval_on_selector_all(
            "form [name^='ObjectField_']", "els => [...new Set(els.map(e => e.name))]")


class VideoCategoryFieldsVB(VideoCategoryAdminPage):
    """manage-video-category field helpers for Agent VB (QCTEST-130715-VB-)."""

    def __init__(self, page):
        super().__init__(page, VB_PREFIX)

    # ---- fields ---------------------------------------------------------------------
    def _display_order_box(self):
        return self._en(KC_DISPLAY_ORDER)

    def set_display_order(self, value: str) -> "VideoCategoryFieldsVB":
        """Types `value` key by key into the number input ("" clears) — "abc" is
        dropped by the browser exactly as for a real user."""
        box = self._display_order_box()
        box.click()
        box.press("Control+A")
        box.press("Delete")
        if value:
            self.page.keyboard.type(str(value), delay=20)
        return self

    def display_order_value(self) -> str:
        return self._display_order_box().input_value()

    def fill_category_vb(self, name: str | None, name_ar: str | None, display_order: str | None,
                         active: bool | None = True) -> "VideoCategoryFieldsVB":
        """None = leave the control untouched (empty on a new form)."""
        if name is not None:
            self.fill_en(KC_NAME, name)
        if name_ar is not None:
            self.fill_ar(KC_NAME, name_ar)
        if display_order is not None:
            self.set_display_order(display_order)
        if active is not None:
            self.set_active_status(active)
        return self

    def edit_bar_status(self) -> str:
        """Status named in the "Editing <name> (<Status>)." bar of the open record."""
        match = re.search(r"\((Draft|Published|Pending Review|Approved|Rejected|Unpublished|Scheduled)\)",
                          self.editing_bar_text())
        return match.group(1) if match else ""

    def form_field_names(self) -> list[str]:
        """Distinct `ObjectField_<key>` names on the open form (what the editor can set)."""
        return self._form().evaluate(
            "f => [...new Set([...f.querySelectorAll('[name^=\"ObjectField_\"]')].map(e => e.name))]")

    def field_error_owners(self) -> list[dict]:
        """[{field, text}] — each inline field error with the ObjectField_<key> /
        qc-ar-<key> control of its nearest enclosing block."""
        try:
            return self.page.evaluate(
                """(sel) => [...document.querySelectorAll(sel)].filter(e => e.innerText.trim()).map(e => {
                    let c = e.parentElement, owners = [];
                    for (let i = 0; i < 6 && c && !owners.length; i++, c = c.parentElement) {
                        owners = [...c.querySelectorAll('[name^="ObjectField_"]:not([type="hidden"]), [id^="qc-ar-"]')]
                            .map(n => n.name || n.id);
                    }
                    return {field: owners.join(','), text: e.innerText.trim()}; })""",
                self.FIELD_ERROR,
            )
        except Exception:  # noqa: BLE001 — mid-navigation
            return []

    def refusal_evidence(self) -> dict:
        evidence = super().refusal_evidence()
        evidence["field_error_owners"] = self.field_error_owners()
        return evidence

    def row_last_modified(self, entry: VideoGalleryEntry) -> str:
        cells = self._row(entry).first.locator("td")
        return cells.nth(2).inner_text().strip() if cells.count() > 2 else ""

    # ---- identity for records whose EN name is blank / whitespace ----------------------
    def identify_created_by_ar(self, ar_marker: str, ids_before: set[str]) -> dict | None:
        """{entry_id, code, stored_name, stored_ar} of the ONE new row whose own
        form reads Arabic name == `ar_marker` (must be in the VB namespace).
        Read-only; adopts the id into `owned_entry_ids`."""
        if not ar_marker.startswith(VB_PREFIX):
            raise ValueError(f"{ar_marker!r} is not in the {VB_PREFIX} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].startswith(REAL_CODE_PREFIX) and r["entry_id"] not in REAL_CATEGORY_IDS]
        matches = []
        for row in fresh:
            try:
                self.open(self._manage_url(edit_entry=row["code"], locale="en"))
                self._en(KC_NAME).wait_for(timeout=90000)
                try:
                    wait_until(lambda: self.ar_value(KC_NAME) != "", timeout=15.0, poll=0.5)
                except WaitTimeoutError:
                    pass
                if self.ar_value(KC_NAME) == ar_marker:
                    matches.append({**row, "stored_name": self.text_value(KC_NAME),
                                    "stored_ar": self.ar_value(KC_NAME)})
            except Exception as exc:  # noqa: BLE001 — unreadable row is not ours
                _logger.warning("could not read new row %s: %r", row, exc)
        if len(matches) != 1:
            _logger.warning("identify_created_by_ar(%r): %s matches among %s", ar_marker, len(matches), fresh)
            return None
        self.owned_entry_ids.add(matches[0]["entry_id"])
        return matches[0]

    def rename_into_namespace(self, found: dict, new_name: str) -> VideoGalleryEntry | None:
        """Gives a captured blank/whitespace-named VB record (from
        identify_created_by_ar) a VB-prefixed English name so VA's guarded
        delete can take it. Every guard re-read right before the save:
        id captured by this test, not real, code matches, Arabic still the VB marker."""
        if (not new_name.startswith(VB_PREFIX) or found["entry_id"] not in self.owned_entry_ids
                or found["code"].startswith(REAL_CODE_PREFIX) or found["entry_id"] in REAL_CATEGORY_IDS
                or not found["stored_ar"].startswith(VB_PREFIX)):
            _logger.error("RENAME REFUSED for %r", found)
            return None
        self.open(self._manage_url(edit_entry=found["code"], locale="en"))
        self._en(KC_NAME).wait_for(timeout=90000)
        try:
            wait_until(lambda: self.ar_value(KC_NAME) != "", timeout=15.0, poll=0.5)
        except WaitTimeoutError:
            pass
        if self.ar_value(KC_NAME) != found["stored_ar"] or self.text_value(KC_NAME) != found["stored_name"]:
            _logger.error("RENAME REFUSED: record %s now reads %r / %r", found["code"],
                          self.text_value(KC_NAME), self.ar_value(KC_NAME))
            return None
        self.fill_en(KC_NAME, new_name)
        if not self.display_order_value():
            self.set_display_order("900")
        self.click_publish()
        if not self.save_went_through():
            _logger.error("RENAME save did not go through: %s", self.refusal_evidence())
            return None
        entry = VideoGalleryEntry(title=new_name, entry_id=found["entry_id"], code=found["code"], prefix=VB_PREFIX)
        return entry


# ---- public reads (logged-out contexts only) --------------------------------------------
VB_EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "evidence", "130715_vb")

_OVERFLOW_JS = """(sels) => {
    const out = []; const vw = document.documentElement.clientWidth;
    for (const s of sels) document.querySelectorAll(s).forEach(el => {
        const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
        out.push({sel: s, text: (el.innerText || '').slice(0, 90),
                  clipped: (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)
                           && (cs.overflow.includes('hidden') || cs.overflowX.includes('hidden')
                               || cs.textOverflow === 'ellipsis' || cs.webkitLineClamp !== 'none'),
                  ellipsis: cs.textOverflow === 'ellipsis', line_clamp: cs.webkitLineClamp,
                  beyond_viewport: r.right > vw + 1 || r.left < -1,
                  width: Math.round(r.width), height: Math.round(r.height), vw: vw}); });
    out.push({sel: 'document', page_hscroll: document.documentElement.scrollWidth > vw + 1,
              scrollWidth: document.documentElement.scrollWidth, vw: vw});
    return out; }"""


def _vb_public_evidence(view, name: str, full_page: bool = True) -> str:
    _os.makedirs(VB_EVIDENCE_DIR, exist_ok=True)
    path = _os.path.join(VB_EVIDENCE_DIR, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
    try:
        png = view.page.screenshot(path=path, full_page=full_page)
        from core.utils.reporting import attach_screenshot  # noqa: PLC0415
        attach_screenshot(png, name, "video_gallery")
    except Exception as exc:  # noqa: BLE001 — evidence only
        _logger.warning("evidence %s failed: %r", name, exc)
    return path


class VideoLibraryPublicViewVB(VideoLibraryPublicView):
    """Logged-out Video Library listing reads for VB (chips, dropdown, cards, layout)."""

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _vb_public_evidence(self, name, full_page)

    def overflow_report(self, selectors: list[str]) -> list[dict]:
        return self.page.evaluate(_OVERFLOW_JS, selectors)

    def hero_state(self) -> dict:
        return {"title": self.hero_title_text().strip(), "background": self.hero_bg_style()}

    def wait_for_categories(self, timeout: float = 15.0) -> list[str]:
        """Chip labels once the chip row has rendered past "All Videos" (or the timeout)."""
        try:
            wait_until(lambda: len(self.chip_texts()) > 1, timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass
        return self.chip_texts()


class VideoDetailsPublicViewVB(VideoDetailsPublicView):
    """Logged-out Video Details reads for VB."""

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _vb_public_evidence(self, name, full_page)

    def overflow_report(self, selectors: list[str]) -> list[dict]:
        return self.page.evaluate(_OVERFLOW_JS, selectors)

    def category_tag_text(self) -> str:
        tag = self.page.locator(self.TAG)
        return tag.first.inner_text().strip() if tag.count() else ""

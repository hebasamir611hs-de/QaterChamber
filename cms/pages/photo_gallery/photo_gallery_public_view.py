"""
cms/pages/photo_gallery/photo_gallery_public_view.py — PhotoGalleryPublicView.

Logged-out reads of the public Photo Albums listing / Album Details pages for
the PBI 130714 Control_Panel cases. Thin layer over the existing public Page
Objects (web/pages/photo_albums/*) — same `qc-pgl-*` / `qc-pgd-*` locators —
adding only what a CMS->public check needs: Load More fully expanded, cards
identified by their `?erc=<code>` href, and the category filter options.
"""

from __future__ import annotations

import os
import re

from config.settings import web_url
from core.web.license_gate import clear_license_gate
from core.web.overlays import dismiss_overlays
from core.utils.waits import WaitTimeoutError, wait_until
from web.pages.photo_albums.album_details_page import ALBUM_DETAILS_PATH, AlbumDetailsPage
from web.pages.photo_albums.photo_albums_listing_page import PhotoAlbumsListingPage

_CARDS_JS = """() => [...document.querySelectorAll('.qc-pgl-card')].map(c => {
    const q = s => c.querySelector(s);
    const img = q('.qc-pgl-cover-img');
    return {href: c.getAttribute('href') || '',
            title: q('.qc-pgl-card-title') ? q('.qc-pgl-card-title').innerText.trim() : '',
            chip: q('.qc-pgl-chip') ? q('.qc-pgl-chip').innerText.trim() : '',
            badge: q('.qc-pgl-badge') ? q('.qc-pgl-badge').innerText.trim() : '',
            cover_src: img ? (img.currentSrc || img.getAttribute('src') || '') : '',
            cover_loaded: img ? (img.complete && img.naturalWidth > 0) : false,
            meta: [...c.querySelectorAll('.qc-pgl-meta-item')].map(m => m.innerText.trim())};
})"""

_DETAIL_JS = """() => {
    const q = s => document.querySelector(s);
    const vis = el => !!el && el.offsetParent !== null && getComputedStyle(el).display !== 'none';
    const boxes = [...document.querySelectorAll('.qc-pgd-box')].map(b => {
        const img = b.querySelector('img');
        const r = b.getBoundingClientRect();
        return {index: b.getAttribute('data-qc-pgd-index'), lead: b.classList.contains('qc-pgd-lead'),
                alt: img ? (img.getAttribute('alt') || '') : '',
                src: img ? (img.currentSrc || img.getAttribute('src') || '') : '', width: r.width};
    });
    return {title: vis(q('.qc-pgd-title')) ? q('.qc-pgd-title').innerText.trim() : '',
            chip: q('.qc-pgd-chip') ? q('.qc-pgd-chip').innerText.trim() : '',
            meta: [...document.querySelectorAll('.qc-pgd-meta-item')].map(m => m.innerText.trim()),
            boxes: boxes,
            empty_text: vis(q('.qc-pgd-empty')) ? q('.qc-pgd-empty').innerText.trim() : '',
            body: document.body.innerText.slice(0, 3000)};
}"""


def _save_evidence(page, evidence_dir: str, name: str) -> str:
    if not evidence_dir:
        return ""
    os.makedirs(evidence_dir, exist_ok=True)
    path = os.path.join(evidence_dir, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
    try:
        png = page.screenshot(path=path, full_page=True)
        from core.utils.reporting import attach_screenshot  # noqa: PLC0415
        attach_screenshot(png, name, "photo_gallery")
    except Exception:  # noqa: BLE001 — evidence only
        pass
    return path


def _plain_open(page, url: str) -> None:
    """Logged-out navigation WITHOUT BasePage's session guard (which could sign
    an anonymous context in as TEST_USER if a login form ever showed)."""
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    clear_license_gate(page, url)
    dismiss_overlays(page, grace_ms=1500)


class PhotoGalleryPublicView(PhotoAlbumsListingPage):
    def __init__(self, page, evidence_dir: str = ""):
        super().__init__(page)
        self.evidence_dir = evidence_dir

    def open(self, url: str) -> None:
        _plain_open(self.page, url)

    def open_listing_all(self, locale: str = "en", max_clicks: int = 40) -> "PhotoGalleryPublicView":
        """Opens the listing and clicks Load More until it disappears or stops growing."""
        self.open_photo_albums(locale)
        try:
            wait_until(lambda: self.card_count() > 0 or self.is_empty_state_visible(), timeout=20.0, poll=0.5)
        except WaitTimeoutError:
            pass
        more = self.page.locator(self.MORE_BTN)
        for _ in range(max_clicks):
            if more.count() == 0 or not more.first.is_visible():
                break
            before = self.card_count()
            more.first.click()
            try:
                wait_until(lambda: self.card_count() > before, timeout=10.0, poll=0.25)
            except WaitTimeoutError:
                break
        return self

    def cards(self) -> list[dict]:
        return self.page.evaluate(_CARDS_JS)

    def card_for(self, code: str) -> dict:
        for card in self.cards():
            match = re.search(r"[?&]erc=([^&#]+)", card["href"])
            if match and match.group(1) == code:
                return card
        return {}

    def has_title(self, title: str) -> bool:
        return any(c["title"] == title for c in self.cards())

    def filter_category_options(self) -> list[str]:
        return [o.strip() for o in self.category_options()]

    def evidence(self, name: str) -> str:
        return _save_evidence(self.page, self.evidence_dir, name)


class PhotoAlbumDetailView(AlbumDetailsPage):
    """Logged-out Album Details reads keyed by the album's code."""

    def __init__(self, page, evidence_dir: str = ""):
        super().__init__(page)
        self.evidence_dir = evidence_dir

    def open_code(self, code: str, locale: str = "en", timeout: float = 30.0) -> dict:
        """Opens `?erc=<code>`; returns {status, found, title, chip, meta, boxes,
        empty_text, body} and never raises on a missing album."""
        url = web_url(f"{ALBUM_DETAILS_PATH}?erc={code}", locale=locale)
        response = self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page, grace_ms=1500)
        try:
            self.page.wait_for_selector(f"{self.TITLE}, {self.EMPTY}", state="visible", timeout=int(timeout * 1000))
        except Exception:  # noqa: BLE001 — reported through the dict
            pass
        info = self.page.evaluate(_DETAIL_JS)
        info["status"] = response.status if response else 0
        info["found"] = bool(info["title"])
        return info

    def evidence(self, name: str) -> str:
        return _save_evidence(self.page, self.evidence_dir, name)

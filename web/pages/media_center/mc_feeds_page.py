"""
web/pages/media_center/mc_feeds_page.py — PBI 130709 Media Center Home Page,
FRONTEND batch 3 (FE-FEEDS): the hub's three feed blocks (News & press
releases, Photo Gallery carousel, Video Gallery), their CTAs, the card ->
detail navigation, and the disposable source-module records the feed cases
need.

LIVE RECON 2026-10-13 (logged-out, 1920x1080, /web/qatar-chamber/media-center):

  News block   section.qc-mc-nf  (data-qc-mcnf-ready="true")
               reads /o/qc-media-center-api/news?groupId=..&limit=4 — the News
               object manage-qcdemo131059-news, newest publicationDate first.
               The fragment takes items[0] as the LEAD and items[1..3] as the
               cards — there is NO Featured logic: "Featured" is only one of
               the article's Category Tags (checkbox) and is rendered as a chip.
               lead  article[data-qc-mcnf-lead]: .qc-mc-nf-chip*, a.qc-mc-nf-lead-title,
                     p.qc-mc-nf-lead-text, .qc-mc-nf-meta-text (date / views / read),
                     a.qc-mc-nf-more ("Read More"), img.qc-mc-nf-img
               cards a.qc-mc-nf-card > h3.qc-mc-nf-card-title (+ date / views)
               CTA   a[data-qc-mcnf-cta] "View All Articles" -> /web/qatar-chamber/news-archive
  Photo block  section.qc-mc-pf — /o/qc-photo-gallery-api/albums?sort=recent&pageSize=12;
               3-wide sliding window; [data-qc-mcpf-prev] / [data-qc-mcpf-next]
               (disabled at the ends — the window stops at total-2), indicator
               [data-qc-mcpf-indicator] "<first visible> / <albums loaded>".
               cards a.qc-mc-pf-card > h3.qc-mc-pf-card-title -> photo-album-details?erc=
               CTA   a[data-qc-mcpf-cta] "View all albums" -> /web/qatar-chamber/photo-gallery
  Video block  section.qc-mc-vf — /o/qc-video-library-api/videos?sort=recent&pageSize=3;
               cards a.qc-mc-vf-card (img.qc-mc-vf-img, .qc-mc-vf-play, .qc-mc-vf-duration,
               h3.qc-mc-vf-card-title) -> video-details?erc=
               CTA   a[data-qc-mcvf-cta] "Watch now" -> /web/qatar-chamber/video-library
  Counts strip section.qc-mc-counts — .qc-mc-counts-card (.qc-mc-counts-label /
               .qc-mc-counts-value "14 stories"), from /o/qc-media-center-api/counts.
  Image error  every feed <img> removes itself on `error` and marks its media
               box data-qc-mc??-img-failed="true" (neutral fill, no image).
  Empty feed   a feed with zero items hides its whole <section> (root.hidden).

Detail pages: news-detail?id=<objectEntryId> (h2.qc-newsd-title),
photo-album-details?erc= (.qc-pgd-title), video-details?erc= (.qc-vdt-title).
Listings: news-archive (a.qc-news-feat-card h2 + a.qc-news-card h3, Load More),
photo-gallery (.qc-pgl-card-title, Load More), video-library (.qc-vll-card-title).

DISPOSABLE DATA (Site Content Editor 156488 only; titles QCTEST-130709-*):
  News     manage-qcdemo131059-news  (driver: SUBS-B's McNewsAdminPage, extended
           here with thumbnail / read time / total views and a guarded Unpublish)
  Album    manage-photo-album        (PBI 130714 driver, re-namespaced here)
  Video    manage-video-record       (PBI 130715 driver, re-namespaced here)
Every delete is by the captured entry id + exact title + code (never by
position); real QCDEMO-* records are never acted on.
"""

from __future__ import annotations

import json as _json
import os as _os
import re as _re
from dataclasses import dataclass as _dataclass
from time import monotonic as _monotonic

from cms.pages.media_center.mc_subscriber_admin_b_page import McNewsAdminPage, NewsEntry
from cms.pages.photo_gallery.gallery_admin_base import GalleryEntry
from cms.pages.photo_gallery.photo_album_admin_page import PhotoAlbumAdminPage
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.video_gallery.video_record_admin_page import (
    DEFAULT_THUMBNAIL as VIDEO_DEFAULT_THUMBNAIL,
    K_CATEGORY_REL,
    K_DESCRIPTION,
    K_DURATION,
    K_PUBLISHED_DATE as VK_PUBLISHED_DATE,
    K_SOURCE_TYPE,
    K_THUMBNAIL,
    K_TITLE as VK_TITLE,
    K_VIDEO_STATUS,
    K_VIDEO_URL,
    K_VIEW_COUNT as VK_VIEW_COUNT,
    SOURCE_EXTERNAL_URL,
    VIDEO_RECORD_SLUG,
    VideoGalleryEntry,
    VideoRecordAdminPage,
)
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import web_url
from core.utils.logger import get_logger as _get_logger
from core.utils.waits import WaitTimeoutError as _WaitTimeoutError
from core.utils.waits import wait_until as _wait_until
from core.web.base_page import BasePage
from core.web.license_gate import clear_license_gate
from core.web.overlays import dismiss_overlays

_logger = _get_logger("mc_feeds_page")

EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "mc130709", "feFeeds")

MEDIA_CENTER_PATH = "/web/qatar-chamber/media-center"
NEWS_LISTING_PATH = "/web/qatar-chamber/news-archive"
PHOTO_LISTING_PATH = "/web/qatar-chamber/photo-gallery"
VIDEO_LISTING_PATH = "/web/qatar-chamber/video-library"
NEWS_DETAIL_PATH = "/web/qatar-chamber/news-detail"
ALBUM_DETAIL_PATH = "/web/qatar-chamber/photo-album-details"
VIDEO_DETAIL_PATH = "/web/qatar-chamber/video-details"

NEWS_API = "/o/qc-media-center-api/news"
COUNTS_API = "/o/qc-media-center-api/counts"
ALBUMS_API = "/o/qc-photo-gallery-api/albums"
VIDEOS_API = "/o/qc-video-library-api/videos"

QCTEST_PREFIX = "QCTEST-130709-"
FEED_PREFIX = "QCTEST-130709-FEED-"   # album / video namespace of this agent

NEWS_IMAGE = _os.path.join(str(_PROJECT_ROOT), "cms", "tests", "home_latest_news", "fixtures",
                           "news_thumbnail.png")
ALBUM_PHOTO_SOURCE = "First_Test_Album_QChamber"
ALBUM_CATEGORY = "Institutional"

EDIT_CONTROL_RE = _re.compile(r"^\s*(edit|add|add new|delete|remove|\+)\s*$", _re.I)


def _norm(text: str | None) -> str:
    return " ".join((text or "").split())


def shot(page, name: str, full_page: bool = True) -> str:
    """PNG evidence under reports/mc130709/feFeeds/ (also attached to Allure)."""
    _os.makedirs(EVIDENCE_DIR, exist_ok=True)
    path = _os.path.join(EVIDENCE_DIR, _re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
    try:
        png = page.screenshot(path=path, full_page=full_page)
        from core.utils.reporting import attach_screenshot  # noqa: PLC0415
        attach_screenshot(png, name, "mc130709_feFeeds")
    except Exception as exc:  # noqa: BLE001 — evidence only
        _logger.warning("evidence %s failed: %r", name, exc)
    return path


# ===========================================================================
# Public hub (logged-out)
# ===========================================================================
class McFeedsPage(BasePage):
    # ---- news block ------------------------------------------------------------
    NEWS = "section.qc-mc-nf"
    NEWS_READY = "section.qc-mc-nf[data-qc-mcnf-ready='true']"
    NEWS_EYEBROW = "[data-qc-mcnf-eyebrow]"
    NEWS_HEADING = "[data-qc-mcnf-heading]"
    NEWS_CTA = "a[data-qc-mcnf-cta]"
    NEWS_CTA_LABEL = "[data-qc-mcnf-cta-label]"
    NEWS_LEAD = "article[data-qc-mcnf-lead]"
    NEWS_LEAD_TITLE = "a.qc-mc-nf-lead-title"
    NEWS_LEAD_TEXT = "p.qc-mc-nf-lead-text"
    NEWS_CHIP = ".qc-mc-nf-chip"
    NEWS_META_TEXT = ".qc-mc-nf-meta-text"
    NEWS_READ_MORE = "a.qc-mc-nf-more"
    NEWS_IMG = "img.qc-mc-nf-img"
    NEWS_LEAD_MEDIA = ".qc-mc-nf-lead-media"
    NEWS_CARD = "a.qc-mc-nf-card"
    NEWS_CARD_TITLE = "h3.qc-mc-nf-card-title"
    NEWS_CARD_MEDIA = ".qc-mc-nf-card-media"
    # ---- photo block -----------------------------------------------------------
    PHOTO = "section.qc-mc-pf"
    PHOTO_READY = "section.qc-mc-pf[data-qc-mcpf-ready='true']"
    PHOTO_CTA = "a[data-qc-mcpf-cta]"
    PHOTO_CTA_LABEL = "[data-qc-mcpf-cta-label]"
    PHOTO_CARD = "a.qc-mc-pf-card"
    PHOTO_CARD_TITLE = "h3.qc-mc-pf-card-title"
    PHOTO_PREV = "[data-qc-mcpf-prev]"
    PHOTO_NEXT = "[data-qc-mcpf-next]"
    PHOTO_INDICATOR = "[data-qc-mcpf-indicator]"
    # ---- video block -----------------------------------------------------------
    VIDEO = "section.qc-mc-vf"
    VIDEO_READY = "section.qc-mc-vf[data-qc-mcvf-ready='true']"
    VIDEO_EYEBROW = "[data-qc-mcvf-eyebrow]"
    VIDEO_HEADING = "[data-qc-mcvf-heading]"
    VIDEO_CTA = "a[data-qc-mcvf-cta]"
    VIDEO_CTA_LABEL = "[data-qc-mcvf-cta-label]"
    VIDEO_CARD = "a.qc-mc-vf-card"
    VIDEO_CARD_TITLE = "h3.qc-mc-vf-card-title"
    VIDEO_CARD_MEDIA = ".qc-mc-vf-card-media"
    VIDEO_IMG = "img.qc-mc-vf-img"
    VIDEO_PLAY = ".qc-mc-vf-play"
    VIDEO_DURATION = ".qc-mc-vf-duration"
    # ---- neighbours / counts ---------------------------------------------------
    SUBSCRIBE_BAND = "section.qc-mc-sub"
    COUNTS_CARD = ".qc-mc-counts-card"
    COUNTS_LABEL = ".qc-mc-counts-label"
    COUNTS_VALUE = ".qc-mc-counts-value"
    COUNTS_READY = "section.qc-mc-counts[data-qc-mcc-ready='true']"
    FEEDS = "section.qc-mc-nf, section.qc-mc-pf, section.qc-mc-vf"

    # ---- navigation -------------------------------------------------------------
    def open(self, url: str) -> None:
        """Logged-out navigation: no session guard (it would sign a visitor in)."""
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page, grace_ms=1500)

    def open_hub(self, locale: str = "en", wait_feeds: bool = True) -> "McFeedsPage":
        self.open(web_url(MEDIA_CENTER_PATH, locale=locale))
        if wait_feeds:
            self.wait_feeds_ready()
        return self

    def wait_feeds_ready(self, timeout_ms: int = 45000) -> None:
        for ready in (self.NEWS_READY, self.PHOTO_READY, self.VIDEO_READY):
            try:
                self.page.locator(ready).first.wait_for(state="attached", timeout=timeout_ms)
            except Exception:  # noqa: BLE001 — a hidden/empty block is reported by its reader
                pass
        try:
            _wait_until(lambda: self.page.locator(f"{self.NEWS} {self.NEWS_LEAD_TITLE}").count() > 0
                        or self.page.locator(self.NEWS).first.evaluate("e => e.hidden"),
                        timeout=20.0, poll=0.3)
        except Exception:  # noqa: BLE001
            pass

    def signed_in(self) -> bool:
        return bool(self.page.evaluate(
            "() => !!(window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())"))

    def evidence(self, name: str, full_page: bool = True) -> str:
        return shot(self.page, name, full_page)

    # ---- news -------------------------------------------------------------------
    def section_rendered(self, section: str) -> bool:
        node = self.page.locator(section).first
        return node.count() > 0 and not node.evaluate("e => e.hidden") and node.is_visible()

    def news_lead(self) -> dict:
        lead = self.page.locator(f"{self.NEWS} {self.NEWS_LEAD}").first
        if lead.count() == 0 or not lead.is_visible():
            return {}
        title = lead.locator(self.NEWS_LEAD_TITLE).first
        more = lead.locator(self.NEWS_READ_MORE).first
        img = lead.locator(self.NEWS_IMG).first
        return {
            "title": _norm(title.inner_text()) if title.count() else "",
            "href": title.get_attribute("href") if title.count() else "",
            "chips": [_norm(t) for t in lead.locator(self.NEWS_CHIP).all_inner_texts()],
            "excerpt": _norm(lead.locator(self.NEWS_LEAD_TEXT).first.inner_text())
            if lead.locator(self.NEWS_LEAD_TEXT).count() else "",
            "meta": [_norm(t) for t in lead.locator(self.NEWS_META_TEXT).all_inner_texts()],
            "read_more": _norm(more.inner_text()) if more.count() else "",
            "read_more_href": more.get_attribute("href") if more.count() else "",
            "img_src": img.get_attribute("src") if img.count() else "",
            "img_loaded": bool(img.evaluate("e => e.complete && e.naturalWidth > 0")) if img.count() else False,
        }

    def news_cards(self) -> list[dict]:
        return self.page.evaluate(
            """(sel) => [...document.querySelectorAll(sel)].map(a => ({
                title: (a.querySelector('h3') || {innerText: ''}).innerText.replace(/\\s+/g, ' ').trim(),
                href: a.getAttribute('href') || '',
                meta: [...a.querySelectorAll('.qc-mc-nf-meta-text')].map(m => m.innerText.trim()),
                img: (a.querySelector('img') || {}).src || ''}))""",
            f"{self.NEWS} {self.NEWS_CARD}")

    def news_titles(self) -> list[str]:
        lead = self.news_lead()
        return ([lead["title"]] if lead.get("title") else []) + [c["title"] for c in self.news_cards()]

    def click_read_more(self) -> None:
        self.page.locator(f"{self.NEWS} {self.NEWS_LEAD} {self.NEWS_READ_MORE}").first.click()

    def click_news_card(self, index: int = 0) -> None:
        self.page.locator(f"{self.NEWS} {self.NEWS_CARD}").nth(index).click()

    # ---- photo carousel ----------------------------------------------------------
    def photo_titles_visible(self) -> list[str]:
        return [_norm(t) for t in self.page.locator(f"{self.PHOTO} {self.PHOTO_CARD_TITLE}").all_inner_texts()]

    def photo_cards(self) -> list[dict]:
        return self.page.evaluate(
            """(sel) => [...document.querySelectorAll(sel)].map(a => ({
                title: (a.querySelector('h3') || {innerText: ''}).innerText.replace(/\\s+/g, ' ').trim(),
                href: a.getAttribute('href') || ''}))""",
            f"{self.PHOTO} {self.PHOTO_CARD}")

    def indicator(self) -> dict:
        node = self.page.locator(f"{self.PHOTO} {self.PHOTO_INDICATOR}").first
        text = _norm(node.inner_text()) if node.count() else ""
        match = _re.search(r"(\d[\d,]*)\s*/\s*(\d[\d,]*)", text)
        return {"text": text,
                "current": int(match.group(1).replace(",", "")) if match else None,
                "total": int(match.group(2).replace(",", "")) if match else None,
                "visible": node.count() > 0 and node.is_visible()}

    def nav_state(self) -> dict:
        prev = self.page.locator(f"{self.PHOTO} {self.PHOTO_PREV}").first
        nxt = self.page.locator(f"{self.PHOTO} {self.PHOTO_NEXT}").first
        return {"prev_present": prev.count() > 0 and prev.is_visible(),
                "prev_disabled": prev.is_disabled() if prev.count() else None,
                "next_present": nxt.count() > 0 and nxt.is_visible(),
                "next_disabled": nxt.is_disabled() if nxt.count() else None}

    def _click_nav(self, selector: str) -> dict:
        before = self.indicator()["text"]
        control = self.page.locator(f"{self.PHOTO} {selector}").first
        control.scroll_into_view_if_needed()
        if control.is_disabled():
            return self.indicator()
        control.click()
        try:
            _wait_until(lambda: self.indicator()["text"] != before, timeout=5.0, poll=0.2)
        except _WaitTimeoutError:
            pass
        return self.indicator()

    def click_next(self) -> dict:
        return self._click_nav(self.PHOTO_NEXT)

    def click_prev(self) -> dict:
        return self._click_nav(self.PHOTO_PREV)

    def force_click(self, which: str) -> dict:
        """Clicks Prev/Next even when disabled (force) — for edge cases that
        need to see what an attempted click does."""
        selector = self.PHOTO_PREV if which == "prev" else self.PHOTO_NEXT
        control = self.page.locator(f"{self.PHOTO} {selector}").first
        control.scroll_into_view_if_needed()
        try:
            control.click(force=True, timeout=5000)
        except Exception as exc:  # noqa: BLE001 — a disabled control may refuse the click
            _logger.info("forced %s click: %r", which, exc)
        return self.indicator()

    def carousel_sequence(self, max_steps: int = 60) -> list[str]:
        """Album titles in carousel order: the at-rest window, then each new
        album revealed by Next until Next is disabled."""
        seen = list(self.photo_titles_visible())
        for _ in range(max_steps):
            if self.nav_state()["next_disabled"] in (True, None):
                break
            self.click_next()
            visible = self.photo_titles_visible()
            if visible:
                seen.append(visible[-1])
        return seen

    def click_album_card(self, index: int = 0) -> None:
        self.page.locator(f"{self.PHOTO} {self.PHOTO_CARD}").nth(index).click()

    # ---- video -------------------------------------------------------------------
    def video_cards(self) -> list[dict]:
        return self.page.evaluate(
            """(sel) => [...document.querySelectorAll(sel)].map(a => ({
                title: (a.querySelector('h3') || {innerText: ''}).innerText.replace(/\\s+/g, ' ').trim(),
                href: a.getAttribute('href') || '',
                img: (a.querySelector('img') || {}).src || ''}))""",
            f"{self.VIDEO} {self.VIDEO_CARD}")

    def video_titles(self) -> list[str]:
        return [c["title"] for c in self.video_cards()]

    def click_video_card(self, index: int = 0) -> None:
        self.page.locator(f"{self.VIDEO} {self.VIDEO_CARD}").nth(index).click()

    # ---- CTAs --------------------------------------------------------------------
    CTA = {"news": (NEWS, NEWS_CTA, NEWS_CTA_LABEL), "photo": (PHOTO, PHOTO_CTA, PHOTO_CTA_LABEL),
           "video": (VIDEO, VIDEO_CTA, VIDEO_CTA_LABEL)}

    def cta(self, block: str) -> dict:
        section, cta, label = self.CTA[block]
        node = self.page.locator(f"{section} {cta}").first
        if node.count() == 0:
            return {"present": False}
        node.scroll_into_view_if_needed()
        return {"present": True, "visible": node.is_visible(), "label": _norm(node.locator(label).first.inner_text()),
                "href": node.get_attribute("href") or ""}

    def click_cta(self, block: str) -> dict:
        """Clicks the block's header CTA; returns the main-document status + URL."""
        section, cta, _ = self.CTA[block]
        node = self.page.locator(f"{section} {cta}").first
        node.scroll_into_view_if_needed()
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=60000) as nav:
            node.click()
        response = nav.value
        dismiss_overlays(self.page, grace_ms=1000)
        status = response.status if response else None
        how = "document"
        if status is None:
            # Liferay's SPA (Senna) swaps the page in without a document
            # response — re-request the landed URL in the same guest context.
            status = self.page.request.get(self.page.url).status
            how = "spa+get"
        return {"status": status, "url": self.page.url, "how": how}

    # ---- media boxes (image failure) ---------------------------------------------
    _MEDIA_JS = """(box) => {
        if (!box) return null;
        const cs = getComputedStyle(box);
        const img = box.querySelector('img');
        const r = box.getBoundingClientRect();
        const kids = [...box.children].map(c => {
            const s = getComputedStyle(c);
            return {tag: c.tagName.toLowerCase(), cls: String(c.className && c.className.baseVal !== undefined
                    ? c.className.baseVal : c.className), visible: s.display !== 'none' && s.visibility !== 'hidden'
                    && c.getBoundingClientRect().width > 0, text: (c.innerText || '').trim().slice(0, 40)}; });
        const pseudo = ['::before', '::after'].map(p => getComputedStyle(box, p))
            .map(s => ({content: s.content, bg: s.backgroundImage}));
        return {
            width: Math.round(r.width), height: Math.round(r.height),
            background_color: cs.backgroundColor, background_image: cs.backgroundImage,
            img_present: !!img,
            img_loaded: !!(img && img.complete && img.naturalWidth > 0),
            img_src: img ? img.getAttribute('src') : '',
            img_broken_attr: !!(img && img.hasAttribute('data-qc-img-broken')),
            failed_attr: [...box.attributes].filter(a => /img-failed/.test(a.name)).map(a => a.name + '=' + a.value),
            children: kids, pseudo: pseudo };
    }"""

    def media_box_state(self, selector: str) -> dict | None:
        node = self.page.locator(selector).first
        if node.count() == 0:
            return None
        node.scroll_into_view_if_needed()
        return node.evaluate(self._MEDIA_JS)

    @staticmethod
    def placeholder_shown(state: dict | None) -> bool:
        """An image-like placeholder: a loaded <img> (fallback asset), a CSS
        background-image, or a visible graphic child (svg/img/icon) — a plain
        colour fill does not count."""
        if not state:
            return False
        if state["img_present"] and state["img_loaded"]:
            return True
        if state["background_image"] and state["background_image"] != "none":
            return True
        if any(p["bg"] not in ("none", "") or (p["content"] not in ("none", "normal", '""', "")) for p in state["pseudo"]):
            return True
        return any(c["visible"] and (c["tag"] in ("svg", "img", "picture") or "placeholder" in c["cls"]
                                     or "fallback" in c["cls"]) for c in state["children"])

    # ---- read-only scan -------------------------------------------------------------
    _EDIT_SCAN_JS = r"""(sel) => {
        const out = [];
        const re = /^\s*(edit|add|add new|delete|remove|new|\+|تعديل|إضافة|حذف)\s*$/i;
        document.querySelectorAll(sel).forEach(sec => {
            sec.querySelectorAll('a, button, [role=button], input, textarea, select, [contenteditable]').forEach(n => {
                const label = ((n.innerText || '') + ' ' + (n.getAttribute('aria-label') || '') + ' '
                               + (n.getAttribute('title') || '')).replace(/\s+/g, ' ').trim();
                const editable = n.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(n.tagName);
                const cls = String(n.className || '');
                const href = n.getAttribute('href') || '';
                if (editable || re.test(label) || /(^|\s)(lfr-|edit|delete|admin|portlet-)/i.test(cls)
                    || /manage-|editEntry|control_panel|p_p_mode=edit/i.test(href))
                    out.push({section: sec.className, tag: n.tagName, label, cls, href,
                              editable, visible: n.getBoundingClientRect().width > 0});
            });
        });
        return out;
    }"""

    def editing_controls(self) -> list[dict]:
        return self.page.evaluate(self._EDIT_SCAN_JS, self.FEEDS)

    def hover_all_cards(self) -> None:
        for sel in (f"{self.NEWS} {self.NEWS_LEAD}", f"{self.NEWS} {self.NEWS_CARD}",
                    f"{self.PHOTO} {self.PHOTO_CARD}", f"{self.VIDEO} {self.VIDEO_CARD}"):
            cards = self.page.locator(sel)
            for i in range(cards.count()):
                try:
                    cards.nth(i).hover(timeout=5000)
                except Exception:  # noqa: BLE001 — hover is best-effort evidence
                    pass

    def page_editing_ui(self) -> dict:
        """Liferay authoring chrome on the current page (a logged-out page has none)."""
        return self.page.evaluate("""() => ({
            control_menu: !!document.querySelector('.control-menu, #ControlMenu, .lfr-control-menu'),
            edit_mode: !!document.querySelector('.lfr-layout-structure-item-topper, [data-qa-id="editMode"], .page-editor'),
            contenteditable: [...document.querySelectorAll('[contenteditable="true"]')].length,
            edit_links: [...document.querySelectorAll('a[href*="editEntry="], a[href*="p_p_mode=edit"], a[href*="manage-"]')]
                         .map(a => a.getAttribute('href')).slice(0, 5)})""")

    # ---- counts --------------------------------------------------------------------
    def count_value(self, label: str = "Articles") -> int | None:
        try:
            self.page.locator(self.COUNTS_READY).first.wait_for(state="attached", timeout=30000)
        except Exception:  # noqa: BLE001
            pass
        cards = self.page.locator(self.COUNTS_CARD)
        for i in range(cards.count()):
            card = cards.nth(i)
            if _norm(card.locator(self.COUNTS_LABEL).first.inner_text()).casefold() == label.casefold():
                match = _re.search(r"\d[\d,]*", card.locator(self.COUNTS_VALUE).first.inner_text())
                return int(match.group(0).replace(",", "")) if match else None
        return None

    def count_value_text(self, label: str = "Articles") -> str:
        cards = self.page.locator(self.COUNTS_CARD)
        for i in range(cards.count()):
            card = cards.nth(i)
            if _norm(card.locator(self.COUNTS_LABEL).first.inner_text()).casefold() == label.casefold():
                return _norm(card.locator(self.COUNTS_VALUE).first.inner_text())
        return ""

    def poll_hub(self, predicate, timeout: float = 120.0, poll: float = 2.0,
                 locale: str = "en") -> tuple[bool, float]:
        """Reloads the hub until predicate(self) holds; returns (held, seconds).
        `seconds` is measured from the call to the START of the reload that
        first satisfied the predicate — page-load time itself is excluded (the
        visitor budget is measured after load)."""
        start = _monotonic()
        mark = {"t": start}

        def _ok() -> bool:
            mark["t"] = _monotonic()
            self.open_hub(locale=locale)
            return bool(predicate(self))

        try:
            _wait_until(_ok, timeout=timeout, poll=poll)
            return True, round(mark["t"] - start, 1)
        except _WaitTimeoutError:
            return False, round(_monotonic() - start, 1)

    # ---- APIs (same-origin, guest) ---------------------------------------------------
    def api_json(self, path: str) -> dict:
        status, text = self.page.evaluate(
            "async (u) => { const r = await fetch(u, {cache: 'no-store'}); return [r.status, await r.text()]; }", path)
        try:
            return {"_status": status, **_json.loads(text)}
        except ValueError:
            return {"_status": status, "_body": text[:300]}

    def news_api(self, limit: int = 50) -> list[dict]:
        data = self.api_json(f"{NEWS_API}?groupId=37246&limit={limit}")
        return [{"erc": i.get("erc"), "id": i.get("id"), "title": i.get("titleEn"),
                 "date": i.get("publicationDate"), "categories": i.get("categoriesEn")}
                for i in data.get("items", [])]

    def counts_api(self) -> dict:
        return self.api_json(COUNTS_API)

    # ---- request interception ----------------------------------------------------------
    def block_url(self, url_part: str) -> list[str]:
        """Aborts every request whose URL contains `url_part`; returns the list
        the handler appends aborted URLs to."""
        aborted: list[str] = []

        def _handler(route):
            aborted.append(route.request.url)
            route.abort()

        self.page.route(lambda u: url_part in u, _handler)
        return aborted

    def fulfil_json(self, url_part: str, transform) -> list[str]:
        """Rewrites the JSON of every response whose URL contains `url_part`
        through `transform(dict) -> dict`."""
        hits: list[str] = []

        def _handler(route):
            response = route.fetch()
            try:
                body = transform(response.json())
            except Exception:  # noqa: BLE001 — pass through unmodified
                route.fulfill(response=response)
                return
            hits.append(route.request.url)
            route.fulfill(response=response, body=_json.dumps(body), headers={**response.headers,
                                                                             "content-type": "application/json"})

        self.page.route(lambda u: url_part in u, _handler)
        return hits


# ===========================================================================
# Public listing + detail pages
# ===========================================================================
class McListingPages(McFeedsPage):
    NEWS_LISTING_READY = "section.qc-news[data-qc-news-ready='true']"
    NEWS_LISTING_TITLES = "a.qc-news-feat-card h2.qc-news-feat-title, a.qc-news-card h3.qc-news-card-title"
    NEWS_LISTING_MORE = "button.qc-news-more"
    NEWS_LISTING_CARD = "a.qc-news-feat-card, a.qc-news-card"
    PHOTO_LISTING_CARD = ".qc-pgl-card"
    PHOTO_LISTING_TITLE = ".qc-pgl-card-title"
    PHOTO_LISTING_STATUS = ".qc-pgl-status"
    PHOTO_LISTING_MORE = ".qc-pgl-more"
    PHOTO_LISTING_EMPTY = ".qc-pgl-empty"
    VIDEO_LISTING_CARD = "a.qc-vll-card"
    VIDEO_LISTING_TITLE = ".qc-vll-card-title"
    VIDEO_LISTING_STATUS = ".qc-vll-status"
    VIDEO_LISTING_MORE = ".qc-vll-more"
    VIDEO_LISTING_EMPTY = ".qc-vll-empty"
    NEWS_DETAIL_TITLE = "h2.qc-newsd-title"
    ALBUM_DETAIL_TITLE = ".qc-pgd-title"
    VIDEO_DETAIL_TITLE = ".qc-vdt-title"

    def _expand(self, card: str, more: str, max_rounds: int = 20) -> None:
        for _ in range(max_rounds):
            button = self.page.locator(more).first
            if button.count() == 0 or not button.is_visible() or button.is_disabled():
                return
            before = self.page.locator(card).count()
            button.click()
            try:
                _wait_until(lambda: self.page.locator(card).count() > before, timeout=15.0, poll=0.3)
            except _WaitTimeoutError:
                return

    def _titles_when_ready(self, card: str, title: str, empty: str | None = None) -> list[str]:
        try:
            _wait_until(lambda: self.page.locator(card).count() > 0
                        or (empty is not None and self.page.locator(empty).first.is_visible()),
                        timeout=40.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        return [_norm(t) for t in self.page.locator(title).all_inner_texts()]

    def news_listing(self) -> list[str]:
        self.open(web_url(NEWS_LISTING_PATH))
        try:
            self.page.locator(self.NEWS_LISTING_READY).first.wait_for(state="attached", timeout=45000)
        except Exception:  # noqa: BLE001
            pass
        self._titles_when_ready(self.NEWS_LISTING_CARD, self.NEWS_LISTING_TITLES)
        self._expand(self.NEWS_LISTING_CARD, self.NEWS_LISTING_MORE)
        return [_norm(t) for t in self.page.locator(self.NEWS_LISTING_TITLES).all_inner_texts()]

    def photo_listing(self) -> dict:
        self.open(web_url(PHOTO_LISTING_PATH))
        self._titles_when_ready(self.PHOTO_LISTING_CARD, self.PHOTO_LISTING_TITLE, self.PHOTO_LISTING_EMPTY)
        self._expand(self.PHOTO_LISTING_CARD, self.PHOTO_LISTING_MORE)
        status = self.page.locator(self.PHOTO_LISTING_STATUS)
        return {"titles": [_norm(t) for t in self.page.locator(self.PHOTO_LISTING_TITLE).all_inner_texts()],
                "status": _norm(status.first.inner_text()) if status.count() else ""}

    def video_listing(self) -> dict:
        self.open(web_url(VIDEO_LISTING_PATH))
        self._titles_when_ready(self.VIDEO_LISTING_CARD, self.VIDEO_LISTING_TITLE, self.VIDEO_LISTING_EMPTY)
        self._expand(self.VIDEO_LISTING_CARD, self.VIDEO_LISTING_MORE)
        status = self.page.locator(self.VIDEO_LISTING_STATUS)
        empty = self.page.locator(self.VIDEO_LISTING_EMPTY)
        return {"titles": [_norm(t) for t in self.page.locator(self.VIDEO_LISTING_TITLE).all_inner_texts()],
                "status": _norm(status.first.inner_text()) if status.count() else "",
                "empty_visible": empty.count() > 0 and empty.first.is_visible(),
                "empty_text": _norm(empty.first.inner_text()) if empty.count() else ""}

    def detail_title(self, kind: str, timeout: float = 30.0) -> str:
        selector = {"news": self.NEWS_DETAIL_TITLE, "album": self.ALBUM_DETAIL_TITLE,
                    "video": self.VIDEO_DETAIL_TITLE}[kind]
        node = self.page.locator(selector).first
        try:
            _wait_until(lambda: node.count() > 0 and _norm(node.inner_text()) != "", timeout=timeout, poll=0.5)
        except _WaitTimeoutError:
            pass
        return _norm(node.inner_text()) if node.count() else ""

    def page_errors(self) -> list[str]:
        return list(getattr(self, "_page_errors", []))

    def watch_page_errors(self) -> None:
        self._page_errors: list[str] = []
        self.page.on("pageerror", lambda e: self._page_errors.append(str(e)[:200]))


# ===========================================================================
# Disposable source-module records (Site Content Editor)
# ===========================================================================
class McFeedsNewsAdmin(McNewsAdminPage):
    """News module driver (SUBS-B's) + thumbnail / read time / total views and a
    guarded single-record Unpublish."""

    UNPUBLISH_BY_ID = '[data-qc-oel-unpublish="{entry_id}"]'

    def fill_feed_article(self, title: str, date_ddmmyyyy: str, categories: tuple[str, ...] = ("Collaboration",),
                          title_ar: str | None = "", body: str | None = None, body_ar: str | None = None,
                          read_time: str = "4", total_views: str = "7", thumbnail: bool = True,
                          active: bool = True) -> "McFeedsNewsAdmin":
        self.fill_en("title", title)
        if title_ar:
            self.fill_ar("title", title_ar)
        self.page.locator(self._rich_iframe("description")).first.wait_for(timeout=30000)
        self.fill_rich("description", body or f"{title} — disposable automated feed article.")
        if body_ar and self.page.locator(self._rich_ar_iframe("description")).count():
            self.fill_rich_ar("description", body_ar)
        for category in categories:
            self.tick_category(category)
        self.upload("image", NEWS_IMAGE, stem="qctest-130709-feed-img")
        if thumbnail:
            self.upload("thumbnail", NEWS_IMAGE, stem="qctest-130709-feed-thumb")
        self.set_date("publicationDate", date_ddmmyyyy)
        if read_time is not None:
            self.fill_number_key("readTime", read_time)
        if total_views is not None:
            self.fill_number_key("totalViews", total_views)
        self.set_active_status(active)
        return self

    def unpublish_own(self, entry: NewsEntry) -> list[str]:
        """Unpublish of exactly the captured QCTEST article (id + title + code re-read)."""
        if not isinstance(entry, NewsEntry) or not entry.in_namespace() or entry.entry_id not in self.owned_entry_ids:
            raise ValueError(f"unpublish refuses {entry!r}: not a captured QCTEST-130709 article")
        self.open_list_all()
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        if len(rows) != 1 or rows[0]["code"] != entry.code or rows[0]["title"].strip() != entry.title:
            raise ValueError(f"unpublish refuses {entry!r}: row reads {rows}")
        control = self.page.locator(self.UNPUBLISH_BY_ID.format(entry_id=entry.entry_id))
        if control.count() != 1:
            raise AssertionError(f"row {entry.title!r} offers {control.count()} Unpublish controls")
        messages: list[str] = []

        def _accept(dialog):
            messages.append(f"{dialog.type}: {dialog.message}")
            try:
                dialog.accept("") if dialog.type == "prompt" else dialog.accept()
            except Exception:  # noqa: BLE001
                pass

        self.page.on("dialog", _accept)
        try:
            control.first.click(force=True)
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        return messages

    def evidence(self, name: str, full_page: bool = True) -> str:
        return shot(self.page, name, full_page)


@_dataclass(frozen=True)
class FeedGalleryEntry(GalleryEntry):
    def in_namespace(self) -> bool:
        return (self.title.startswith(FEED_PREFIX) and self.prefix == FEED_PREFIX
                and not self.code.upper().startswith("QCDEMO-"))


class McFeedsAlbumAdmin(PhotoAlbumAdminPage):
    """manage-photo-album driver re-namespaced to QCTEST-130709-FEED-."""

    def __init__(self, page):  # noqa: D401 — bypasses the 130714 prefix check on purpose
        ObjectAuthoringPage.__init__(self, page, "photo-album")
        self.prefix = FEED_PREFIX
        self.evidence_dir = EVIDENCE_DIR
        self.owned_entry_ids: set[str] = set()
        self.last_uploaded_name = ""
        self.last_delete_dialogs: list[str] = []
        self.last_delete_messages: list[str] = []
        self.last_row_action_dialogs: list[str] = []
        self.pinned_role: str | None = None

    def identify_created(self, title: str, ids_before: set[str]) -> FeedGalleryEntry | None:  # type: ignore[override]
        entry = super().identify_created(title, ids_before)
        return None if entry is None else FeedGalleryEntry(title=entry.title, entry_id=entry.entry_id,
                                                           code=entry.code, prefix=entry.prefix, slug=entry.slug)

    def album_data(self, title: str, date_ddmmyyyy: str) -> dict:
        return {"title": title, "title_ar": f"{title} ألبوم", "published_date": date_ddmmyyyy,
                "category": ALBUM_CATEGORY, "flickr_source": ALBUM_PHOTO_SOURCE, "active": True,
                "cover": NEWS_IMAGE, "cover_stem": "qctest-130709-feed-cover"}

    def evidence(self, name: str, full_page: bool = True) -> str:
        return shot(self.page, name, full_page)


@_dataclass(frozen=True)
class FeedVideoEntry(VideoGalleryEntry):
    def in_namespace(self) -> bool:
        return self.prefix == FEED_PREFIX and self.title.strip().startswith(FEED_PREFIX)


class McFeedsVideoAdmin(VideoRecordAdminPage):
    """manage-video-record driver re-namespaced to QCTEST-130709-FEED-."""

    def __init__(self, page):  # noqa: D401 — bypasses the 130715 prefix check on purpose
        ObjectAuthoringPage.__init__(self, page, VIDEO_RECORD_SLUG)
        self.owner_prefix = FEED_PREFIX
        self.owned_entry_ids: set[str] = set()
        self.last_uploaded_name = ""
        self.evidence_dir = EVIDENCE_DIR

    def identify_created(self, title: str, ids_before: set[str]) -> FeedVideoEntry | None:  # type: ignore[override]
        entry = super().identify_created(title, ids_before)
        return None if entry is None else FeedVideoEntry(title=entry.title, entry_id=entry.entry_id,
                                                         code=entry.code, prefix=entry.prefix)

    @staticmethod
    def video_data(title: str, date_ddmmyyyy: str) -> dict:
        if not title.startswith(FEED_PREFIX):
            raise ValueError(f"disposable videos must use a {FEED_PREFIX} title")
        return {
            VK_TITLE: title,
            f"{VK_TITLE}_ar": f"{title} فيديو تجريبي",
            K_SOURCE_TYPE: SOURCE_EXTERNAL_URL,
            K_VIDEO_URL: "https://vimeo.com/123456789",
            K_THUMBNAIL: VIDEO_DEFAULT_THUMBNAIL,
            f"{K_THUMBNAIL}_stem": "qctest-130709-feed-thumb",
            K_DURATION: "05:12",
            K_DESCRIPTION: f"{title} — disposable automated-test video.",
            f"{K_DESCRIPTION}_ar": "فيديو اختبار آلي مؤقت.",
            VK_PUBLISHED_DATE: date_ddmmyyyy,
            VK_VIEW_COUNT: "0",
            K_VIDEO_STATUS: "Published",
            K_CATEGORY_REL: "Events",
            "active_status": True,
        }

    def evidence(self, name: str, full_page: bool = True) -> str:
        return shot(self.page, name, full_page)

"""
web/pages/media_center/mc_hub_page.py — public Media Center hub (PBI 130709, FE-HUB).

Covers the hub surfaces the FE-HUB cases touch: hero (label, breadcrumb,
search), summary counts strip, quick-access cards, the three feed sections'
vertical order, plus the two pages the hub hands off to (main-menu entry on
the home page, Media Search results) and the five module listings whose
public totals the counts strip must equal.

LOCATORS — harvested live on qcdev 2026-10-13 (fresh logged-out Chromium,
1920x1080, EN + AR) with a scripted DOM probe of the data-qc-* hooks:
  section.qc-mc-hero[data-qc-mch-ready=true]
      h1[data-qc-mch-pagetitle] "Media Center"
      nav[data-qc-mch-crumbs] > a.qc-mc-hero-crumb--home[href=/web/qatar-chamber] "Home"
                              > span.qc-mc-hero-crumb--current "Media Center"
      form[data-qc-mch-form] > input[data-qc-mch-input] + button[data-qc-mch-btn]
      (search hands off to /web/qatar-chamber/media-search?q=<kw>)
  section.qc-mc-counts[data-qc-mcc-ready=true] > [data-qc-mcc-list] > div.qc-mc-counts-card
      span.qc-mc-counts-label (display name) + span.qc-mc-counts-value ("14 stories")
      icon mask url carries objectEntryExternalReferenceCode=QCDEMO-130709-COUNT-0n
      totals come from /o/qc-media-center-api/counts
  section.qc-mc-qa[data-qc-mcqa-ready=true] > [data-qc-mcqa-grid] > a.qc-mc-qa-card
      span.qc-mc-qa-title / span.qc-mc-qa-cardesc / span.qc-mc-qa-arrow-wrap (inside the link)
  feed sections: section.qc-mc-nf (newsPressReleases), section.qc-mc-pf (photoGallery),
      section.qc-mc-vf (videoGallery) — each carries data-qc-mc??-section-key
  Media Search: section.qc-ms[data-qc-ms-ready=true], tabs button[data-qc-ms-type=<key>]
      (.qc-ms-tab-count), p[data-qc-ms-summary] 'N results for "kw"',
      ul[data-qc-ms-list] > li.qc-ms-item > a.qc-ms-card (span.qc-ms-badge, h2.qc-ms-card-title)
  Home main menu: nav.qc-nav > ul.qc-nav-list > li > a.qc-nav-link "Insights & Media"
      (aria-haspopup, aria-controls -> submenu) containing a.qc-nav-link "Media Center".
  Module listings (public totals): news-archive "N articles shown", photo-gallery
      "N albums shown", video-library "N videos shown", podcast badge "N Episodes",
      publications "N publications shown".

The real public URL is /web/qatar-chamber/media-center (the cases' placeholder
"<WEB_BASE_URL>/media-center"); AR /ar/web/qatar-chamber/media-center.

No asserts here — Page Objects expose state; tests assert.
"""

from __future__ import annotations

import json
import os
import re
from time import monotonic

from config.settings import PROJECT_ROOT, web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher

logger = get_logger("mc_hub_page")

HUB_PATH = "/web/qatar-chamber/media-center"
HOME_PATH = "/web/qatar-chamber"
SEARCH_PATH = "/web/qatar-chamber/media-search"
COUNTS_API = "/o/qc-media-center-api/counts"
EVIDENCE_DIR = os.path.join(str(PROJECT_ROOT), "reports", "mc130709", "FE-HUB")

# content type key -> (listing path, regex on the listing's own visible total line)
MODULE_LISTINGS = {
    "articles": ("/web/qatar-chamber/news-archive", r"(\d[\d,]*)\s+articles?\s+shown"),
    "photoAlbums": ("/web/qatar-chamber/photo-gallery", r"(\d[\d,]*)\s+albums?\s+shown"),
    "videos": ("/web/qatar-chamber/video-library", r"(\d[\d,]*)\s+videos?\s+shown"),
    "podcast": ("/web/qatar-chamber/podcast", r"(\d[\d,]*)\s+Episodes?\b"),
    "publications": ("/web/qatar-chamber/publications", r"(\d[\d,]*)\s+publications?\s+shown"),
}
# count-widget icon ERC -> content type key (the strip has no content-type attribute)
SECTION_CLASSES = {"newsPressReleases": "section.qc-mc-nf", "photoGallery": "section.qc-mc-pf",
                   "videoGallery": "section.qc-mc-vf"}


def shot(page, name: str, full_page: bool = True) -> str:
    """Evidence screenshot under reports/mc130709/FE-HUB/ (path returned)."""
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    path = os.path.join(EVIDENCE_DIR, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
    try:
        png = page.screenshot(path=path, full_page=full_page)
        from core.utils.reporting import attach_screenshot  # noqa: PLC0415
        attach_screenshot(png, name, "mc130709_fe_hub")
    except Exception as exc:  # noqa: BLE001 — evidence only
        logger.warning("evidence %s failed: %r", name, exc)
    return path


class MediaCenterHubPage(BasePage):
    # ---- hero -------------------------------------------------------------
    HERO = "section.qc-mc-hero"
    HERO_READY = "section.qc-mc-hero[data-qc-mch-ready=true]"
    HERO_LABEL = "[data-qc-mch-pagetitle]"
    CRUMBS = "nav[data-qc-mch-crumbs]"
    CRUMB_HOME = "nav[data-qc-mch-crumbs] a.qc-mc-hero-crumb--home"
    CRUMB_CURRENT = "nav[data-qc-mch-crumbs] .qc-mc-hero-crumb--current"
    SEARCH_INPUT = "input[data-qc-mch-input]"
    SEARCH_BUTTON = "button[data-qc-mch-btn]"

    # ---- counts strip ------------------------------------------------------
    COUNTS_READY = "section.qc-mc-counts[data-qc-mcc-ready=true]"
    COUNT_CARD = "[data-qc-mcc-list] .qc-mc-counts-card"

    # ---- quick-access cards -------------------------------------------------
    QA_READY = "section.qc-mc-qa[data-qc-mcqa-ready=true]"
    QA_GRID = "[data-qc-mcqa-grid]"
    QA_CARD = "[data-qc-mcqa-grid] a.qc-mc-qa-card"
    QA_CARD_BODY = ".qc-mc-qa-text"
    QA_CARD_ARROW = ".qc-mc-qa-arrow-wrap"

    _COUNTS_JS = r"""() => [...document.querySelectorAll('[data-qc-mcc-list] .qc-mc-counts-card')].map((c, i) => {
        const t = s => { const e = c.querySelector(s); return e ? e.innerText.trim() : ''; };
        const img = c.querySelector('.qc-mc-counts-badge-img');
        const mask = img ? (img.style.maskImage || img.style.webkitMaskImage || '') : '';
        const m = mask.match(/objectEntryExternalReferenceCode=([^&"')]+)/);
        const r = c.getBoundingClientRect();
        return {index: i, label: t('.qc-mc-counts-label'), value: t('.qc-mc-counts-value'),
                erc: m ? decodeURIComponent(m[1]) : '', visible: r.width > 0 && r.height > 0,
                in_link: !!c.closest('a[href]'), has_link: !!c.querySelector('a[href]'),
                onclick: !!(c.onclick || c.getAttribute('onclick')), role: c.getAttribute('role') || '',
                cursor: getComputedStyle(c).cursor}; })"""

    _CARDS_JS = r"""() => [...document.querySelectorAll('[data-qc-mcqa-grid] a.qc-mc-qa-card')].map((a, i) => {
        const q = s => a.querySelector(s); const tile = q('.qc-mc-qa-tile-img');
        const mask = tile ? (tile.style.maskImage || tile.style.webkitMaskImage || '') : '';
        const m = mask.match(/objectEntryExternalReferenceCode=([^&"')]+)/);
        const r = a.getBoundingClientRect();
        return {index: i, href: a.getAttribute('href') || '', target: a.getAttribute('target') || '',
                title: q('.qc-mc-qa-title') ? q('.qc-mc-qa-title').innerText.trim() : '',
                desc: q('.qc-mc-qa-cardesc') ? q('.qc-mc-qa-cardesc').innerText.trim() : '',
                erc: m ? decodeURIComponent(m[1]) : '',
                box: {left: Math.round(r.left), top: Math.round(r.top + scrollY), w: Math.round(r.width),
                      h: Math.round(r.height)}}; })"""

    def open_hub(self, locale: str = "en") -> "MediaCenterHubPage":
        self.open(web_url(HUB_PATH, locale=locale))
        return self.wait_ready()

    def wait_ready(self) -> "MediaCenterHubPage":
        for sel in (self.HERO_READY, self.COUNTS_READY, self.QA_READY):
            self.wait_for(sel, state="attached", timeout=60000)
        try:
            wait_until(lambda: self.page.locator(self.QA_CARD).count() > 0
                       and self.page.locator(self.COUNT_CARD).count() > 0, timeout=30.0, poll=0.5)
        except WaitTimeoutError:
            pass  # an empty strip/grid is reported by the caller
        _dismiss_chatbot_launcher(self.page)
        return self

    def evidence(self, name: str, full_page: bool = True) -> str:
        return shot(self.page, name, full_page)

    def current_url(self) -> str:
        return self.page.url

    def direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.dir || getComputedStyle(document.body).direction")

    # ---- hero -----------------------------------------------------------------
    def hero_label(self) -> str:
        return self.text(self.HERO_LABEL).strip()

    def breadcrumb(self) -> list[str]:
        return [" ".join(t.split()) for t in
                self.page.locator(f"{self.CRUMBS} .qc-mc-hero-crumb").all_inner_texts()]

    def breadcrumb_home_href(self) -> str:
        return self.get_attribute(self.CRUMB_HOME, "href") or ""

    def click_breadcrumb_home(self) -> None:
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
            self.click(self.CRUMB_HOME)

    def search(self, keyword: str) -> "MediaSearchResultsPage":
        self.type(self.SEARCH_INPUT, keyword)
        self.click(self.SEARCH_BUTTON)
        self.page.wait_for_url(re.compile(r"/media-search"), timeout=60000)
        return MediaSearchResultsPage(self.page).wait_ready()

    # ---- counts strip ------------------------------------------------------------
    def count_widgets(self) -> list[dict]:
        widgets = self.page.evaluate(self._COUNTS_JS)
        for w in widgets:
            m = re.match(r"^\s*(\d[\d,]*)\s*(.*)$", w["value"])
            w["number"] = int(m.group(1).replace(",", "")) if m else None
            w["unit"] = m.group(2).strip() if m else ""
        return widgets

    def counts_api(self) -> dict:
        return self.page.evaluate(
            """async (u) => { const r = await fetch(u, {headers: {Accept: 'application/json'}});
                              return r.ok ? await r.json() : {status: r.status}; }""", COUNTS_API)

    def click_count_widget(self, label: str) -> dict:
        """Clicks the widget's icon, name and count; reports navigation signals."""
        card = self.page.locator(self.COUNT_CARD).filter(
            has=self.page.locator(".qc-mc-counts-label", has_text=re.compile(rf"^\s*{re.escape(label)}\s*$")))
        state = {"navigations": 0, "popups": 0}

        def _nav(frame):
            if frame == self.page.main_frame:
                state["navigations"] += 1

        def _popup(_p):
            state["popups"] += 1

        url_before = self.page.url
        card.first.scroll_into_view_if_needed()
        scroll_before = self.page.evaluate("() => window.scrollY")
        pages_before = len(self.page.context.pages)
        self.page.on("framenavigated", _nav)
        self.page.on("popup", _popup)
        try:
            for part in (".qc-mc-counts-badge", ".qc-mc-counts-label", ".qc-mc-counts-value"):
                card.first.locator(part).first.click()
            try:
                self.page.wait_for_event("framenavigated", timeout=2500)
            except Exception:  # noqa: BLE001 — no navigation is the expected outcome
                pass
        finally:
            self.page.remove_listener("framenavigated", _nav)
            self.page.remove_listener("popup", _popup)
        return {"label": label, "found": card.count(), "url_before": url_before, "url_after": self.page.url,
                "navigations": state["navigations"], "popups": state["popups"],
                "new_pages": len(self.page.context.pages) - pages_before,
                "scroll_before": scroll_before, "scroll_after": self.page.evaluate("() => window.scrollY")}

    # ---- quick-access cards --------------------------------------------------------
    def cards(self) -> list[dict]:
        return self.page.evaluate(self._CARDS_JS)

    def _card(self, title: str):
        return self.page.locator(self.QA_CARD).filter(
            has=self.page.locator(".qc-mc-qa-title", has_text=re.compile(rf"^\s*{re.escape(title)}\s*$"))).first

    def follow_card(self, title: str, part: str = "body") -> dict:
        """Clicks the card's body (title/description) or only its arrow and
        reports where the browser lands + the HTTP status of that document."""
        card = self._card(title)
        target = card.locator(self.QA_CARD_ARROW if part == "arrow" else self.QA_CARD_BODY).first
        href = card.get_attribute("href") or ""
        new_tab = (card.get_attribute("target") or "") == "_blank"
        _dismiss_chatbot_launcher(self.page)
        target.scroll_into_view_if_needed()
        status = None
        if new_tab:
            with self.page.context.expect_page(timeout=60000) as info:
                target.click()
            other = info.value
            other.wait_for_load_state("domcontentloaded", timeout=60000)
            return {"title": title, "part": part, "href": href, "new_tab": True, "url": other.url,
                    "status": self._status(other.url)}
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=60000) as nav:
            target.click()
        try:
            response = nav.value
            status = response.status if response else None
        except Exception:  # noqa: BLE001
            status = None
        return {"title": title, "part": part, "href": href, "new_tab": False, "url": self.page.url,
                "status": status if status is not None else self._status(self.page.url)}

    def _status(self, url: str) -> int:
        try:
            return self.page.request.get(url, max_redirects=5, timeout=60000).status
        except Exception:  # noqa: BLE001
            return -1

    def back_to_hub(self, locale: str = "en") -> "MediaCenterHubPage":
        return self.open_hub(locale)

    def page_heading(self) -> str:
        loc = self.page.locator("main h1, #content h1, h1")
        try:
            loc.first.wait_for(state="attached", timeout=30000)
            return " ".join(loc.first.inner_text().split())
        except Exception:  # noqa: BLE001
            return ""

    def page_text_has_not_found(self) -> bool:
        body = self.page.evaluate("() => document.body ? document.body.innerText : ''")
        return bool(re.search(r"\b404\b|not\s+found|page could not be found", body, re.I))

    # ---- sections ----------------------------------------------------------------
    def section_order(self) -> list[dict]:
        """The three feed blocks with their document top offset, top-to-bottom."""
        rows = []
        for key, sel in SECTION_CLASSES.items():
            loc = self.page.locator(sel)
            if not loc.count():
                continue
            box = loc.first.evaluate("e => { const r = e.getBoundingClientRect(); "
                                     "return {top: r.top + scrollY, h: r.height}; }")
            heading = loc.first.locator("h2").first.inner_text() if loc.first.locator("h2").count() else ""
            rows.append({"key": key, "top": round(box["top"]), "height": round(box["h"]), "heading": heading.strip()})
        return sorted(rows, key=lambda r: r["top"])

    # ---- polling helpers for CMS-driven cases ------------------------------------
    def poll_cards(self, predicate, timeout: float = 45.0, locale: str = "en") -> tuple[bool, list[dict], float]:
        started = monotonic()
        state = {"cards": [], "at": 0.0}

        def _check() -> bool:
            state["at"] = monotonic() - started
            self.open_hub(locale)
            state["cards"] = self.cards()
            return bool(predicate(state["cards"]))

        try:
            wait_until(_check, timeout=timeout, poll=1.0)
            return True, state["cards"], state["at"]
        except WaitTimeoutError:
            return False, state["cards"], state["at"]


class HomeMainMenu(BasePage):
    """Home page main menu: Insights & Media -> Media Center."""

    TOP_ITEM = "nav.qc-nav > ul.qc-nav-list > li"
    TOP_LINK = "a.qc-nav-link"
    GROUP = "Insights & Media"
    ENTRY = "Media Center"

    def open_home(self) -> "HomeMainMenu":
        self.open(web_url("/"))
        self.wait_for(f"{self.TOP_ITEM} > {self.TOP_LINK}", first=True, timeout=60000)
        return self

    def _group(self):
        return self.page.locator(self.TOP_ITEM).filter(
            has=self.page.locator(f"> {self.TOP_LINK}", has_text=re.compile(rf"^\s*{re.escape(self.GROUP)}\s*$"))).first

    def open_group(self) -> list[str]:
        """Hovers the group; returns the visible submenu entries."""
        group = self._group()
        group.locator(f"> {self.TOP_LINK}").hover()
        sub = group.locator(".qc-nav-sub").first
        try:
            sub.wait_for(state="visible", timeout=10000)
        except Exception:  # noqa: BLE001 — reported through the returned list
            return []
        return [" ".join(t.split()) for t in sub.locator(self.TOP_LINK).all_inner_texts() if t.strip()]

    def click_entry(self) -> None:
        link = self._group().locator(".qc-nav-sub").first.locator(self.TOP_LINK).filter(
            has_text=re.compile(rf"^\s*{re.escape(self.ENTRY)}\s*$")).first
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
            link.click()

    def evidence(self, name: str, full_page: bool = False) -> str:
        return shot(self.page, name, full_page)


class MediaSearchResultsPage(BasePage):
    READY = "section.qc-ms[data-qc-ms-ready=true]"
    SUMMARY = "p[data-qc-ms-summary]"
    TAB = "button[data-qc-ms-type='{key}']"
    TABS = "nav[data-qc-ms-tabs] button[data-qc-ms-type]"
    ITEM = "ul[data-qc-ms-list] > li.qc-ms-item"
    LOADING = "[data-qc-ms-loading]"

    def wait_ready(self) -> "MediaSearchResultsPage":
        self.wait_for(self.READY, state="attached", timeout=60000)
        self._settle()
        return self

    def _settle(self) -> None:
        try:
            wait_until(lambda: (self.page.locator(self.SUMMARY).count() and
                                self.page.locator(self.SUMMARY).first.inner_text().strip() != "") and
                       not self.page.locator(self.LOADING).first.is_visible(), timeout=30.0, poll=0.5)
        except WaitTimeoutError:
            pass

    def summary(self) -> str:
        return " ".join(self.text(self.SUMMARY).split())

    def total(self) -> int | None:
        m = re.search(r"(\d[\d,]*)", self.summary())
        return int(m.group(1).replace(",", "")) if m else None

    def tabs(self) -> dict:
        return self.page.evaluate(
            """(sel) => Object.fromEntries([...document.querySelectorAll(sel)].map(b => [b.dataset.qcMsType,
                {label: (b.querySelector('.qc-ms-tab-label') || b).innerText.trim(),
                 count: (b.querySelector('.qc-ms-tab-count') || {innerText: ''}).innerText.trim(),
                 active: b.classList.contains('is-active')}]))""", self.TABS)

    def items(self) -> list[dict]:
        return self.page.evaluate(
            """(sel) => [...document.querySelectorAll(sel)].map(li => { const a = li.querySelector('a');
                const b = li.querySelector('.qc-ms-badge'), t = li.querySelector('.qc-ms-card-title');
                return {href: a ? a.getAttribute('href') : '', badge: b ? b.innerText.trim() : '',
                        badge_class: b ? b.className : '', title: t ? t.innerText.trim() : '',
                        dir: t ? getComputedStyle(t).direction : ''}; })""", self.ITEM)

    def select_type(self, key: str) -> "MediaSearchResultsPage":
        before = self.summary()
        self.click(self.TAB.format(key=key))
        try:
            wait_until(lambda: self.summary() != before or
                       self.page.locator(f"{self.TAB.format(key=key)}.is-active").count() > 0, timeout=20.0, poll=0.3)
        except WaitTimeoutError:
            pass
        self._settle()
        return self

    def current_url(self) -> str:
        return self.page.url

    def evidence(self, name: str, full_page: bool = True) -> str:
        return shot(self.page, name, full_page)


class ModuleListingTotals(BasePage):
    """Reads the visible published total on each module's public listing."""

    def total(self, content_type: str) -> dict:
        path, pattern = MODULE_LISTINGS[content_type]
        self.open(web_url(path))
        found = {"text": "", "number": None}

        def _read() -> bool:
            body = self.page.evaluate("() => document.body ? document.body.innerText : ''")
            m = re.search(pattern, body, re.I)
            if m:
                found.update(text=m.group(0), number=int(m.group(1).replace(",", "")))
            return bool(m)

        try:
            wait_until(_read, timeout=45.0, poll=0.5)
        except WaitTimeoutError:
            pass
        found["path"] = path
        found["screenshot"] = shot(self.page, f"listing_total_{content_type}", full_page=False)
        return found


class HubConfigReader:
    """Read-only access to the stored hub configuration through an Editor
    session (same REST resources the authoring pages read). `admin` is an
    Object-Authoring page object already signed in as the Editor."""

    SCOPE = "37246"

    def __init__(self, admin):
        self.admin = admin

    def items(self, resource: str) -> list[dict]:
        page = self.admin.page
        body = [0, ""]
        for _ in range(4):
            try:
                page.wait_for_function("() => window.Liferay && Liferay.authToken", timeout=20000)
                body = page.evaluate(
                    """async (u) => { const r = await fetch(u, {headers: {Accept: 'application/json',
                            'x-csrf-token': Liferay.authToken}}); return [r.status, await r.text()]; }""",
                    f"/o/c/{resource}/scopes/{self.SCOPE}?pageSize=100")
                if body[0] == 200:
                    break
            except Exception as exc:  # noqa: BLE001 — navigation in flight; retried
                logger.warning("config GET %s: %r", resource, exc)
            self.admin.open_manage_page_raw()
        if body[0] != 200:
            raise RuntimeError(f"GET {resource} returned {body[0]}: {body[1][:200]}")
        out = []
        for it in json.loads(body[1]).get("items", []):
            status = it.get("status") or {}
            out.append({**{k: v for k, v in it.items() if k != "actions"},
                        "code": it.get("externalReferenceCode", ""),
                        "status_code": status.get("code") if isinstance(status, dict) else status})
        return out

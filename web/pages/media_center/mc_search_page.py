"""
web/pages/media_center/mc_search_page.py — PBI 130709 (Media Center Home Page),
Batch 3 FRONTEND, agent FE-SEARCH: the global media search.

LIVE RECON 2026-10-13 (logged-out, 1920x1080, qcdev):

  Hub hero (fragment `qc-mc-hero`, /web/qatar-chamber/media-center, AR under
  /ar/web/...): section `.qc-mc-hero[data-qc-mch-ready=true]` carrying
  data-qc-mch-search-url=/web/qatar-chamber/media-search, -search-param=q,
  -min-chars=2. Page label h1 [data-qc-mch-pagetitle]; breadcrumb
  nav[data-qc-mch-crumbs] (Home link .qc-mc-hero-crumb--home, chevron icon,
  current span .qc-mc-hero-crumb--current[aria-current=page]); headline
  [data-qc-mch-headline]; description [data-qc-mch-desc]; background
  [data-qc-mch-bg] (inline background-image, data-qc-mch-bg-loaded);
  form [data-qc-mch-form] (novalidate) with input [data-qc-mch-input]
  (#qc-mc-hero-q) and submit [data-qc-mch-btn] (label [data-qc-mch-btn-label]);
  min-length hint p[data-qc-mch-hint][role=status] (hidden until shown).

  Results page (/web/qatar-chamber/media-search?q=<kw>, fragment `qc-ms`):
  section `.qc-ms[data-qc-ms-ready=true]` (dir attr), input
  [data-qc-ms-input], submit [data-qc-ms-submit]; type filter
  nav[data-qc-ms-tabs] > button.qc-ms-tab[data-qc-ms-type=all|articles|
  photoAlbums|videos|podcast|publications] (.qc-ms-tab-label/.qc-ms-tab-count,
  is-active); summary [data-qc-ms-summary]; states [data-qc-ms-prompt],
  [data-qc-ms-hint], [data-qc-ms-empty] (+ -text), [data-qc-ms-error]
  (+ -text, role=alert), loader [data-qc-ms-loading]; list [data-qc-ms-list]
  > li.qc-ms-item > a.qc-ms-card (badge span.qc-ms-badge.qc-ms-badge--<type>,
  h2.qc-ms-card-title, .qc-ms-card-date); pager [data-qc-ms-pager]
  (button.qc-ms-page). Data comes from GET /o/qc-media-center-api/search
  ?q=&type=&page=&pageSize=10 (the only search request the page makes — the
  route a service-down test intercepts).

  Search sources (API `type` -> Object Authoring slug, live):
    articles     -> manage-qcdemo131059-news   (QCDEMO-131059-NEWS-*)
    photoAlbums  -> manage-photo-album         (QCDEMO-130714-PHOTO_ALBUM-*)
    videos       -> manage-video-record        (QCDEMO-130715-VIDEO-*)
    podcast      -> manage-podcast-episode     (QCDEMO-129387-podcast-episode-*)
    publications -> manage-publication         (QCDEMO-129386-PUB-*)

DISPOSABLE DATA (SearchSourceAdmin): records are created by the Site Content
Editor (156488) through Object Authoring only, titled QCTEST-130709-..., and
deleted only through the inherited guarded delete (captured id + code + exact
title re-read immediately before the click, confirm() must name the title).
No positional, looping or substring delete exists here.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.photo_gallery.gallery_admin_base import REAL_CODE_PREFIXES, GalleryAdminPage
from config.settings import PROJECT_ROOT, web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from core.web.overlays import dismiss_overlays

_logger = get_logger("mc_search_page")

EVIDENCE_DIR = os.path.join(str(PROJECT_ROOT), "reports", "mc130709", "FE-SEARCH")

HUB_PATH = "/web/qatar-chamber/media-center"
SEARCH_PATH = "/web/qatar-chamber/media-search"
SEARCH_API_GLOB = "**/o/qc-media-center-api/search**"

QCTEST_PREFIX = "QCTEST-130709-"

# API type -> (Object Authoring slug, EN title field key)
SOURCES = {
    "articles": ("qcdemo131059-news", "title"),
    "photoAlbums": ("photo-album", "albumTitle"),
    "videos": ("video-record", "videoTitle"),
    "podcast": ("podcast-episode", "episodeTitleEn"),
    "publications": ("publication", "publicationTitle"),
}
TYPE_ORDER = ("articles", "photoAlbums", "videos", "podcast", "publications")

_ARABIC_RE = re.compile(r"[؀-ۿ]")


def has_arabic(text: str) -> bool:
    return bool(_ARABIC_RE.search(text or ""))


def _shot(page, name: str, full_page: bool = True) -> str:
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    path = os.path.join(EVIDENCE_DIR, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
    try:
        png = page.screenshot(path=path, full_page=full_page)
        from core.utils.reporting import attach_screenshot  # noqa: PLC0415
        attach_screenshot(png, name, "media_center")
    except Exception as exc:  # noqa: BLE001 — evidence only
        _logger.warning("evidence %s failed: %r", name, exc)
    return path


# =============================================================================
# Public: Media Center hub hero search
# =============================================================================
class McHeroSearch(BasePage):
    HERO_READY = ".qc-mc-hero[data-qc-mch-ready='true']"
    HERO = ".qc-mc-hero"
    PAGE_LABEL = "[data-qc-mch-pagetitle]"
    CRUMBS = "nav[data-qc-mch-crumbs]"
    HEADLINE = "[data-qc-mch-headline]"
    DESCRIPTION = "[data-qc-mch-desc]"
    BACKGROUND = "[data-qc-mch-bg]"
    FORM = "form[data-qc-mch-form]"
    INPUT = "input[data-qc-mch-input]"
    BUTTON = "button[data-qc-mch-btn]"
    BUTTON_LABEL = "[data-qc-mch-btn-label]"
    HINT = "[data-qc-mch-hint]"
    QA_CARD = "a.qc-mc-qa-card"
    QA_CARD_TITLE = ".qc-mc-qa-title"
    COUNTS = ".qc-mc-counts"

    def open_hub(self, locale: str = "en") -> "McHeroSearch":
        self.open(web_url(HUB_PATH, locale))
        self.wait_for(self.HERO_READY, timeout=45000)
        self.wait_for(self.INPUT, timeout=20000)
        return self

    def is_signed_in(self) -> bool:
        return bool(self.page.evaluate(
            "() => !!(window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())"))

    # ---- reads ---------------------------------------------------------------------
    def hero_facts(self) -> dict:
        try:  # the background photo is applied asynchronously by the fragment script
            self.wait_for(f"{self.BACKGROUND}[data-qc-mch-bg-loaded]", state="attached", timeout=20000)
        except Exception:  # noqa: BLE001 — reported by the caller from the facts below
            pass
        return self.page.evaluate(
            """(s) => {
                const q = (sel) => document.querySelector(sel);
                const txt = (el) => el ? el.textContent.replace(/\\s+/g, ' ').trim() : '';
                const crumbs = q(s.crumbs);
                const items = crumbs ? [...crumbs.querySelectorAll('.qc-mc-hero-crumb')].map(c => ({
                    text: txt(c), tag: c.tagName, href: c.getAttribute('href') || '',
                    current: c.getAttribute('aria-current') || ''})) : [];
                const sep = crumbs ? crumbs.querySelectorAll('.qc-mc-hero-crumb-sep').length : 0;
                const bg = q(s.bg);
                const inp = q(s.input);
                const btn = q(s.button);
                const vis = (el) => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
                return {
                    page_label: txt(q(s.label)), page_label_visible: vis(q(s.label)),
                    crumbs: items, crumb_separators: sep, crumbs_text: txt(crumbs),
                    headline: txt(q(s.headline)), headline_visible: vis(q(s.headline)),
                    description: txt(q(s.desc)), description_visible: vis(q(s.desc)),
                    bg_image: bg ? getComputedStyle(bg).backgroundImage : '',
                    bg_loaded: bg ? (bg.getAttribute('data-qc-mch-bg-loaded') || '') : '',
                    placeholder: inp ? inp.getAttribute('placeholder') || '' : '',
                    input_visible: vis(inp),
                    button_label: txt(q(s.btnLabel)), button_aria: btn ? btn.getAttribute('aria-label') || '' : '',
                    button_visible: vis(btn),
                    html_dir: document.documentElement.dir, html_lang: document.documentElement.lang,
                    hero_dir: (q(s.hero) || {getAttribute: () => ''}).getAttribute('dir') || ''};
            }""",
            {"crumbs": self.CRUMBS, "bg": self.BACKGROUND, "input": self.INPUT, "button": self.BUTTON,
             "label": self.PAGE_LABEL, "headline": self.HEADLINE, "desc": self.DESCRIPTION,
             "btnLabel": self.BUTTON_LABEL, "hero": self.HERO})

    def input_value(self) -> str:
        return self.page.locator(self.INPUT).input_value()

    def input_layout(self) -> dict:
        """Direction / alignment of the field and the button's position against it."""
        return self.page.evaluate(
            """([i, b]) => { const inp = document.querySelector(i); const btn = document.querySelector(b);
                const s = getComputedStyle(inp); const ri = inp.getBoundingClientRect();
                const rb = btn.getBoundingClientRect();
                return {direction: s.direction, text_align: s.textAlign, dir_attr: inp.getAttribute('dir') || '',
                        input_left: ri.left, input_right: ri.right, button_left: rb.left, button_right: rb.right,
                        caret_start: inp.selectionStart, caret_end: inp.selectionEnd,
                        value_length: inp.value.length}; }""",
            [self.INPUT, self.BUTTON])

    def hint(self) -> dict:
        return self.page.evaluate(
            """([h, i]) => { const el = document.querySelector(h); const inp = document.querySelector(i);
                const shown = !!el && !el.hidden && el.getClientRects().length > 0;
                return {shown, text: el ? el.textContent.replace(/\\s+/g, ' ').trim() : '',
                        aria_invalid: inp ? inp.getAttribute('aria-invalid') || '' : '',
                        validation: inp ? inp.validationMessage : ''}; }""",
            [self.HINT, self.INPUT])

    # ---- actions -------------------------------------------------------------------
    def type_keyword(self, text: str) -> "McHeroSearch":
        self.type(self.INPUT, text)
        return self

    def click_search(self) -> None:
        self.click(self.BUTTON)

    def press_enter(self) -> None:
        self.page.locator(self.INPUT).press("Enter")

    def search(self, keyword: str, via: str = "click") -> "McSearchResultsPage":
        """Hero search that is expected to navigate to the results page."""
        self.type_keyword(keyword)
        if via == "enter":
            self.press_enter()
        else:
            self.click_search()
        self.wait_for_url(re.compile(r"/media-search"), timeout=30000)
        return McSearchResultsPage(self.page).wait_ready()

    def submit_expecting_no_navigation(self, keyword: str, via: str = "click",
                                       settle_s: float = 3.0) -> dict:
        """Submits and watches for `settle_s` whether the page navigates or a
        search request leaves; returns {url_before, url_after, search_requests}."""
        requests: list[str] = []

        def _on_request(req):
            if "/media-search" in req.url or "qc-media-center-api/search" in req.url:
                requests.append(req.url)

        url_before = self.page.url
        self.page.on("request", _on_request)
        try:
            self.type_keyword(keyword)
            if via == "enter":
                self.press_enter()
            else:
                self.click_search()
            try:
                # Watch window: Playwright's wait pumps the request/navigation events
                # (a sleep-poll would not); timing out here is the expected outcome.
                self.page.wait_for_url(lambda u: u != url_before, timeout=int(settle_s * 1000))
            except Exception:  # noqa: BLE001 — no navigation within the window
                pass
        finally:
            self.page.remove_listener("request", _on_request)
        return {"url_before": url_before, "url_after": self.page.url, "search_requests": requests}

    def block_search_service(self, status: int = 503) -> list[str]:
        """Simulates the search service being down for THIS browser context only
        (Playwright route interception of the search API — no real outage).
        Returns the live list of intercepted URLs."""
        hits: list[str] = []

        def _down(route):
            hits.append(route.request.url)
            route.fulfill(status=status, content_type="text/plain", body="Service Unavailable")

        self.page.context.route(SEARCH_API_GLOB, _down)
        return hits

    # ---- keyboard ------------------------------------------------------------------
    def reset_focus_to_top(self) -> None:
        dismiss_overlays(self.page)
        # Blurring alone keeps Chrome's sequential-focus starting point on the
        # last focused element; focusing <body> resets it to the document start.
        self.page.evaluate(
            """() => { window.scrollTo(0, 0); if (document.activeElement) document.activeElement.blur();
                const b = document.body; b.setAttribute('tabindex', '-1'); b.focus({preventScroll: true});
                b.removeAttribute('tabindex'); }""")

    def focused(self) -> dict:
        return self.page.evaluate(
            """([qa, counts]) => { const e = document.activeElement; if (!e || e === document.body) return {tag: 'BODY'};
                const s = getComputedStyle(e);
                const outlineW = parseFloat(s.outlineWidth) || 0;
                return {tag: e.tagName, cls: String(e.className || ''), href: e.getAttribute('href') || '',
                        id: e.id || '', text: (e.innerText || e.getAttribute('aria-label') || '').trim().split('\\n')[0],
                        outline: s.outlineStyle + ' ' + s.outlineWidth + ' ' + s.outlineColor,
                        box_shadow: s.boxShadow,
                        indicator: (s.outlineStyle !== 'none' && outlineW > 0) || (s.boxShadow && s.boxShadow !== 'none'
                                    && !/^(rgba\\(0, 0, 0, 0\\) 0px 0px 0px 0px,? ?)+$/.test(s.boxShadow)),
                        in_counts: !!e.closest(counts), is_qa_card: e.matches(qa)}; }""",
            [self.QA_CARD, self.COUNTS])

    def tab_trace(self, max_presses: int = 45, stop_after_cards: bool = True) -> list[dict]:
        """Presses Tab from the top of the page; returns the focus trail."""
        self.reset_focus_to_top()
        trail: list[dict] = []
        cards_total = self.page.locator(self.QA_CARD).count()
        for _ in range(max_presses):
            self.press_key("Tab")
            trail.append(self.focused())
            if stop_after_cards and cards_total and sum(1 for f in trail if f.get("is_qa_card")) >= cards_total:
                break
        return trail

    def quick_access_cards(self) -> list[dict]:
        return self.page.evaluate(
            """([c, t]) => [...document.querySelectorAll(c)].map(a => ({
                title: (a.querySelector(t) || a).textContent.replace(/\\s+/g, ' ').trim(),
                href: a.getAttribute('href') || '', top: a.getBoundingClientRect().top,
                left: a.getBoundingClientRect().left}))""",
            [self.QA_CARD, self.QA_CARD_TITLE])

    def counts_focusables(self) -> int:
        return self.page.evaluate(
            """(c) => { const root = document.querySelector(c); if (!root) return -1;
                return [...root.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')]
                    .filter(e => e.tabIndex >= 0).length; }""",
            self.COUNTS)

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _shot(self.page, name, full_page)


# =============================================================================
# Public: unified search results page
# =============================================================================
class McSearchResultsPage(BasePage):
    READY = ".qc-ms[data-qc-ms-ready='true']"
    ROOT = ".qc-ms"
    INPUT = "input[data-qc-ms-input]"
    SUBMIT = "button[data-qc-ms-submit]"
    TABS = "nav[data-qc-ms-tabs]"
    TAB = "nav[data-qc-ms-tabs] button.qc-ms-tab"
    TAB_BY_TYPE = "nav[data-qc-ms-tabs] button.qc-ms-tab[data-qc-ms-type='{type}']"
    SUMMARY = "[data-qc-ms-summary]"
    EMPTY = "[data-qc-ms-empty]"
    EMPTY_TEXT = "[data-qc-ms-empty-text]"
    ERROR = "[data-qc-ms-error]"
    ERROR_TEXT = "[data-qc-ms-error-text]"
    HINT = "[data-qc-ms-hint]"
    PROMPT = "[data-qc-ms-prompt]"
    LOADING = "[data-qc-ms-loading]"
    ITEM = "[data-qc-ms-list] li.qc-ms-item"
    CARD = "[data-qc-ms-list] li.qc-ms-item a.qc-ms-card"
    PAGER = "[data-qc-ms-pager]"

    def open_query(self, keyword: str, locale: str = "en") -> "McSearchResultsPage":
        from urllib.parse import quote  # noqa: PLC0415
        self.open(web_url(f"{SEARCH_PATH}?q={quote(keyword)}", locale))
        return self.wait_ready()

    def _settled(self) -> bool:
        return bool(self.page.evaluate(
            """(s) => { const v = (sel) => { const e = document.querySelector(sel); return !!e && !e.hidden; };
                if (!document.querySelector(s.ready)) return false;
                if (v(s.loading)) return false;
                return document.querySelectorAll(s.item).length > 0 || v(s.empty) || v(s.error) || v(s.hint) || v(s.prompt); }""",
            {"ready": self.READY, "loading": self.LOADING, "item": self.ITEM, "empty": self.EMPTY,
             "error": self.ERROR, "hint": self.HINT, "prompt": self.PROMPT}))

    def wait_ready(self, timeout: float = 45.0) -> "McSearchResultsPage":
        self.wait_for(self.READY, state="attached", timeout=int(timeout * 1000))
        wait_until(self._settled, timeout=timeout, poll=0.3)
        dismiss_overlays(self.page)
        return self

    def state(self) -> dict:
        return self.page.evaluate(
            """(s) => {
                const q = (sel) => document.querySelector(sel);
                const txt = (el) => el ? el.textContent.replace(/\\s+/g, ' ').trim() : '';
                const shown = (sel) => { const e = q(sel); return !!e && !e.hidden && e.getClientRects().length > 0; };
                const items = [...document.querySelectorAll(s.item)].map(li => {
                    const a = li.querySelector('a.qc-ms-card'); const b = li.querySelector('.qc-ms-badge');
                    const t = li.querySelector('.qc-ms-card-title');
                    const bt = b ? (b.className.match(/qc-ms-badge--(\\w+)/) || [])[1] || '' : '';
                    const ts = t ? getComputedStyle(t) : null; const bs = b ? getComputedStyle(b) : null;
                    return {type: bt, label: txt(b), label_rendered: b ? b.innerText.trim() : '', title: txt(t),
                            href: a ? a.getAttribute('href') || '' : '',
                            title_direction: ts ? ts.direction : '', title_align: ts ? ts.textAlign : '',
                            label_direction: bs ? bs.direction : ''};
                });
                const tabs = [...document.querySelectorAll(s.tab)].map(b => ({
                    type: b.getAttribute('data-qc-ms-type') || '',
                    label: txt(b.querySelector('.qc-ms-tab-label')), count: txt(b.querySelector('.qc-ms-tab-count')),
                    active: b.classList.contains('is-active'), direction: getComputedStyle(b).direction}));
                const root = q(s.root);
                const body = document.body.innerText || '';
                return {url: location.href, html_dir: document.documentElement.dir, html_lang: document.documentElement.lang,
                        root_dir: root ? root.getAttribute('dir') || '' : '',
                        root_direction: root ? getComputedStyle(root).direction : '',
                        input_value: q(s.input) ? q(s.input).value : '',
                        summary: txt(q(s.summary)), tabs: tabs, items: items,
                        empty_shown: shown(s.empty), empty_text: txt(q(s.emptyText)),
                        error_shown: shown(s.error), error_text: txt(q(s.errorText)),
                        hint_shown: shown(s.hint), prompt_shown: shown(s.prompt),
                        pager_pages: [...document.querySelectorAll(s.pager + ' .qc-ms-page')].map(p => p.textContent.trim()),
                        trace_like: /(Exception|Traceback|at\\s+[\\w.$]+\\([\\w]+\\.java:\\d+\\)|stack trace|Internal Server Error)/i.test(body)};
            }""",
            {"item": self.ITEM, "tab": self.TAB, "root": self.ROOT, "input": self.INPUT, "summary": self.SUMMARY,
             "empty": self.EMPTY, "emptyText": self.EMPTY_TEXT, "error": self.ERROR, "errorText": self.ERROR_TEXT,
             "hint": self.HINT, "prompt": self.PROMPT, "pager": self.PAGER})

    def select_tab(self, type_key: str) -> "McSearchResultsPage":
        self.click(self.TAB_BY_TYPE.format(type=type_key))
        wait_until(lambda: self.page.locator(self.TAB_BY_TYPE.format(type=type_key) + ".is-active").count() == 1,
                   timeout=15.0, poll=0.25)
        self.wait_ready()
        return self

    def go_to_page(self, number: int) -> bool:
        """Clicks pager button `number`; False when that page button does not exist."""
        btn = self.page.locator(f"{self.PAGER} .qc-ms-page").filter(has_text=re.compile(rf"^\s*{number}\s*$"))
        if btn.count() == 0:
            return False
        before = [i["href"] for i in self.state()["items"]]
        btn.first.click()
        try:
            wait_until(lambda: self._settled() and [i["href"] for i in self.state()["items"]] != before,
                       timeout=20.0, poll=0.3)
        except WaitTimeoutError:
            return False
        return True

    def find_title(self, title: str, max_pages: int = 30) -> dict | None:
        """Scans the current filter's pages for a result whose title equals `title`."""
        page_no = 1
        while True:
            for item in self.state()["items"]:
                if item["title"] == title:
                    return {**item, "page": page_no}
            page_no += 1
            if page_no > max_pages or not self.go_to_page(page_no):
                return None

    def open_result(self, index: int = 0) -> str:
        selector = f"{self.CARD} >> nth={index}"
        href = self.page.locator(self.CARD).nth(index).get_attribute("href") or ""
        before = self.page.url
        dismiss_overlays(self.page)
        for _attempt in (1, 2):  # a late announcement overlay can swallow the first click
            self.click(selector)
            try:
                # Playwright's own wait (page.url is only refreshed while the sync
                # API is pumping events, so a sleep-poll on it never sees the change).
                self.wait_for_url(lambda u: u != before, timeout=15000)
                break
            except Exception:  # noqa: BLE001 — retried once, then asserted by the caller
                dismiss_overlays(self.page)
        self.page.wait_for_load_state("domcontentloaded")
        return href

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _shot(self.page, name, full_page)


class McResultDetailView(BasePage):
    """Any content detail page a result links to (news / album / video /
    podcast / publication): only the headings are read."""

    HEADINGS = "h1, h2, h3"

    def wait_heading(self, title: str, timeout: float = 45.0) -> bool:
        dismiss_overlays(self.page)
        try:
            wait_until(lambda: title in self.headings(), timeout=timeout, poll=0.5)
            return True
        except WaitTimeoutError:
            return False

    def headings(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator(self.HEADINGS).all_text_contents() if t.strip()]

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _shot(self.page, name, full_page)


# =============================================================================
# CMS: disposable QCTEST-130709-* records in the five search source modules
# =============================================================================
@dataclass(frozen=True)
class SearchEntry:
    """Identity of a record THIS test created (captured right after the save)."""

    title: str
    entry_id: str
    code: str
    prefix: str
    slug: str

    def in_namespace(self) -> bool:
        return (self.title.startswith(QCTEST_PREFIX) and bool(self.entry_id) and bool(self.code)
                and not any(self.code.upper().startswith(p) for p in REAL_CODE_PREFIXES))


class SearchSourceAdmin(GalleryAdminPage):
    """Object Authoring driver for one search source object (`SOURCES` key),
    reusing the proven gallery mechanics (role-pinned login, Load-All list,
    save-outcome probe, upload picker, id-scoped row actions, guarded delete)
    under the QCTEST-130709- namespace."""

    def __init__(self, page, type_key: str):
        slug, title_key = SOURCES[type_key]
        ObjectAuthoringPage.__init__(self, page, slug)
        self.type_key = type_key
        self.TITLE_KEY = title_key
        self.prefix = QCTEST_PREFIX
        self.evidence_dir = EVIDENCE_DIR
        self.owned_entry_ids: set[str] = set()
        self.last_uploaded_name = ""
        self.last_delete_dialogs: list[str] = []
        self.last_delete_messages: list[str] = []
        self.last_row_action_dialogs: list[str] = []
        self.pinned_role = None

    def switch(self, type_key: str) -> "SearchSourceAdmin":
        """Same signed-in page, another source object (owned ids kept)."""
        other = SearchSourceAdmin(self.page, type_key)
        other.pinned_role = self.pinned_role
        other.owned_entry_ids = self.owned_entry_ids
        return other

    # ---- identity (QCTEST-130709 namespace) --------------------------------------------
    def identify_created(self, title: str, ids_before: set[str]) -> SearchEntry | None:  # type: ignore[override]
        if not title.startswith(QCTEST_PREFIX):
            raise ValueError(f"{title!r} is not in the {QCTEST_PREFIX} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not any(r["code"].upper().startswith(p) for p in REAL_CODE_PREFIXES)
                 and r["title"].strip() == title]
        if len(fresh) != 1:
            _logger.warning("identify_created(%r) on %s: %s candidates %s", title, self.slug, len(fresh), fresh)
            return None
        entry = SearchEntry(title=title, entry_id=fresh[0]["entry_id"], code=fresh[0]["code"],
                            prefix=QCTEST_PREFIX, slug=self.slug)
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def _check_owned(self, entry, what: str) -> None:  # type: ignore[override]
        if not isinstance(entry, SearchEntry) or not entry.in_namespace() or entry.slug != self.slug:
            raise ValueError(f"{what} refuses {entry}: not a {QCTEST_PREFIX} manage-{self.slug} record")
        if entry.entry_id not in self.owned_entry_ids:
            raise ValueError(f"{what} refuses {entry}: id not captured at creation by this test")

    def adopt(self, entry):  # type: ignore[override]
        raise NotImplementedError("records are only acted on by the session that created them")

    def title_rows(self, title: str) -> list[dict]:
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].strip() == title]

    # ---- form helpers ----------------------------------------------------------------
    def fill_text(self, key: str, text: str, ar: bool = False) -> "SearchSourceAdmin":
        """Plain textarea or CKEditor-backed field, EN or AR twin."""
        iframe = (f'[id="cke_qc-ar-{key}"] iframe[title="editor"]' if ar
                  else f'div.cke[class*="-ObjectField_{key}"] iframe[title="editor"]')
        try:  # CKEditor mounts its iframe a moment after the form renders
            self.page.locator(iframe).first.wait_for(state="attached", timeout=20000)
        except Exception:  # noqa: BLE001 — a plain textarea field has no editor iframe
            pass
        if self.page.locator(iframe).count():
            self.fill_iframe_editor(iframe, text)
        else:
            (self._ar(key) if ar else self._en(key)).fill(text)
        return self

    def tick_checkbox_label(self, label: str) -> "SearchSourceAdmin":
        box = self._form().get_by_role("checkbox", name=label, exact=True).first
        box.check()
        if not box.is_checked():
            raise AssertionError(f"checkbox {label!r} did not tick")
        return self

    def open_create(self) -> "SearchSourceAdmin":
        self.open_create_form_en()
        self._en(self.TITLE_KEY).wait_for(timeout=60000)
        return self

    # ---- per-type recipes (required fields read live 2026-10-13) ------------------------
    def fill_record(self, data: dict) -> "SearchSourceAdmin":
        t, today = self.type_key, data["date"]
        if t == "articles":
            self.fill_en("title", data["title"]).fill_ar("title", data["title_ar"])
            self.fill_text("description", data.get("description") or "QCTEST-130709 disposable search article.")
            self.fill_text("description", data.get("description_ar") or "QCTEST-130709 مقال اختبار البحث.", ar=True)
            self.tick_checkbox_label(data.get("category", "Trade & Economy"))
            self.upload("image", data["image"], stem="qctest-130709-srch")
            self.set_date("publicationDate", today)
        elif t == "photoAlbums":
            self.fill_en("albumTitle", data["title"]).fill_ar("albumTitle", data["title_ar"])
            self.upload("albumCoverImage", data["image"], stem="qctest-130709-srch")
            self.pick("r_photoAlbums_c_eventCategoryId", "Institutional")  # required (live 2026-10-18)
            # "An album must contain at least one published photo": point the album at an
            # existing Flickr folder record (read-only link; the folder record is untouched).
            self.pick("r_flickrAlbumSource_c_flickrAlbumId", "Second_test_Album_QChamber")  # source of a live album
            self.set_date("publishedDate", today)
        elif t == "videos":
            self.fill_en("videoTitle", data["title"]).fill_ar("videoTitle", data["title_ar"])
            self.pick("videoSourceType", "External URL")                  # required (live 2026-10-18)
            self.pick("r_videoRecords_c_videoCategoryId", "Institutional")   # required (live 2026-10-18)
            self.fill_en("videoUrl", "https://www.youtube.com/watch?v=aqz-KE-bpKQ")  # required for External URL
            self.upload("videoThumbnail", data["image"], stem="qctest-130709-srch")
            self.fill_en("duration", "00:05")
            if data.get("description"):
                self.fill_text("videoDescription", data["description"])
            self.set_date("publishedDate", today)
        elif t == "podcast":
            self.fill_en("episodeTitleEn", data["title"]).fill_en("episodeTitleAr", data["title_ar"])
            self.fill_en("episodeNumber", "9001")
            self.fill_text("descriptionEn", data.get("description", "QCTEST-130709 search episode."))
            self.fill_text("descriptionAr", data.get("description_ar", "QCTEST-130709 حلقة اختبار البحث."))
            self.upload("thumbnailImage", data["image"], stem="qctest-130709-srch")  # .jpg (png refused 2026-10-18)
            self.upload("audioFile", data["audio"], stem="qctest-130709-srch")
            self.fill_en("duration", "00:00:02")                              # HH:MM:SS (live 2026-10-18)
            self.set_date("publishDate", today)
            self.fill_en("exploreMoreUrl", "https://qcdev.ihorizons.com/web/qatar-chamber/podcast")
        elif t == "publications":
            self.fill_en("publicationTitle", data["title"]).fill_ar("publicationTitle", data["title_ar"])
            if data.get("description"):
                self.fill_text("publicationDescription", data["description"])
            self.set_date("publicationDate", today)
            self.pick("publicationType", "Report")                           # required (live 2026-10-18)
            self.upload("coverImage", data["image"], stem="qctest-130709-srch")
            self.upload("fileAttachment", data["document"], stem="qctest-130709-srch")
            self.fill_en("pageCount", "1")
        else:
            raise ValueError(t)
        self.set_active_status(bool(data.get("active", True)))
        return self

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _shot(self.page, name, full_page)

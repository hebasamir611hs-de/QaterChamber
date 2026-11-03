"""
web/pages/news/news_page.py — NewsPage (listing + detail).

Public-website Page Object for PBI 131059 ("QC - Insights & Media - 001 -
News Archive").

URLs, CONFIRMED LIVE 2026-09-24 (header nav: Media Center > News):
  listing  /web/qatar-chamber/news-archive      (AR: /ar/web/qatar-chamber/news-archive)
  detail   /web/qatar-chamber/news-detail?id=N  (AR: /ar/...)
Both are client-rendered from the anonymous JAX-RS module /o/qc-news:
  GET /o/qc-news/list?languageId=en_US|ar_SA&sort=recent|views&page=1&pageSize=500
      -> {items:[{id,title,summary,description,categoryTags,keywordTags,totalViews,
                  publicationDate,readTime,...}], totalCount, hasMore}
  GET /o/qc-news/entry?id=N&languageId=...   (detail)
The detail page keeps a view-counter request open, so it never reaches
`networkidle` — readiness is always an element wait on the rendered content.

Locators (disclosed scripted DOM probe at 1920/768/390, EN + AR):
  listing section.qc-news[data-qc-news-ready=true][data-qc-news-page-size=6]
    header.qc-news-hero > h1.qc-news-hero-title, nav.qc-news-crumbs (home a + svg.qc-news-crumb-sep x2
      + span "Insights & Media" + span.qc-news-crumb-current "News")
    form.qc-news-controls > .qc-news-search input.qc-news-search-input + button.qc-news-search-btn svg,
      .qc-news-cat select.qc-news-select (all|featured|tradeAndEconomy|collaboration),
      .qc-news-sort select.qc-news-select (recent|views), svg.qc-news-chev
    .qc-news-featured > a.qc-news-feat-card (.qc-news-cats > span.qc-news-cat-pill, h2.qc-news-feat-title,
      p.qc-news-feat-summary, .qc-news-meta > span.qc-news-meta-item (svg + span.qc-news-ltr), img.qc-news-feat-img)
    .qc-news-grid > a.qc-news-card (img.qc-news-card-img, h3.qc-news-card-title, .qc-news-meta)
    button.qc-news-more ("Load More" + svg.qc-news-more-ico), p.qc-news-status ("N articles shown")
  detail section.qc-newsd[data-qc-newsd-ready=true]
    h1.qc-newsd-hero-title, nav.qc-newsd-crumbs, img.qc-newsd-img, h2.qc-newsd-title,
    .qc-newsd-meta > span.qc-newsd-cat-pill + span.qc-newsd-meta-item, .qc-newsd-content,
    .qc-newsd-tags > span.qc-newsd-tag, .qc-newsd-share (label + a.qc-newsd-share-btn x4)
"""

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

LISTING_PATH = "/web/qatar-chamber/news-archive"
DETAIL_PATH = "/web/qatar-chamber/news-detail"
API_LIST = "/o/qc-news/list?languageId={lang}&sort=recent&page=1&pageSize=500"

_CONTRAST_JS = """
(el) => {
    const parse = (c) => { const m = c.match(/[0-9.]+/g) || [0, 0, 0, 0]; return [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1]; };
    const lum = (rgb) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                           return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2]); };
    let n = el, bg = null;
    while (n && n.nodeType === 1) { const c = parse(getComputedStyle(n).backgroundColor); if (c[3] > 0) { bg = c; break; } n = n.parentElement; }
    bg = bg || [255, 255, 255, 1];
    const fg = parse(getComputedStyle(el).color), a = fg[3];
    const mix = [0, 1, 2].map((i) => fg[i] * a + bg[i] * (1 - a));
    const l1 = lum(mix), l2 = lum(bg);
    return {ratio: Math.round((Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05) * 100) / 100,
            color: getComputedStyle(el).color, background: "rgb(" + bg.slice(0, 3).join(", ") + ")"};
}
"""


class NewsPage(BasePage):
    # ---- Global chrome ----------------------------------------------------------
    PAGE_BODY = "body"
    HEADER = "header.qc-global-site-header"
    HEADER_ICON_BUTTONS = "header.qc-global-site-header :is(.qc-lang-switcher, .qc-accessibility-btn)"
    FOOTER = ".qc-global-site-footer"
    NAV_NEWS_LINK = "header.qc-global-site-header a.qc-nav-link[href*='news-archive']"
    NAV_MEDIA_PARENT = "header.qc-global-site-header a.qc-nav-link[href*='media-center']"

    # ---- Listing ------------------------------------------------------------------
    ROOT = "section.qc-news"
    READY = "section.qc-news[data-qc-news-ready='true']"
    HERO = "header.qc-news-hero"
    HERO_TITLE = "h1.qc-news-hero-title"
    CRUMBS = "nav.qc-news-crumbs"
    CRUMB_ITEMS = "nav.qc-news-crumbs > :is(a, span)"
    CRUMB_HOME_ICON = "nav.qc-news-crumbs svg.qc-news-crumb-ico"
    CRUMB_SEP = "nav.qc-news-crumbs svg.qc-news-crumb-sep"
    SHELL = ".qc-news-shell"
    CONTROLS = "form.qc-news-controls"
    SEARCH_FIELD = ".qc-news-field.qc-news-search"
    SEARCH_INPUT = "input.qc-news-search-input"
    SEARCH_ICON = ".qc-news-search svg"
    CATEGORY_FIELD = ".qc-news-field.qc-news-cat"
    CATEGORY = ".qc-news-cat select.qc-news-select"
    CATEGORY_CHEV = ".qc-news-cat svg.qc-news-chev"
    SORT_FIELD = ".qc-news-field.qc-news-sort"
    SORT = ".qc-news-sort select.qc-news-select"
    SORT_CHEV = ".qc-news-sort svg.qc-news-chev"
    FEATURED = "a.qc-news-feat-card"
    FEAT_PILL = "a.qc-news-feat-card span.qc-news-cat-pill"
    FEAT_TITLE = "h2.qc-news-feat-title"
    FEAT_SUMMARY = "p.qc-news-feat-summary"
    FEAT_META = "a.qc-news-feat-card .qc-news-meta"
    FEAT_META_ITEM = "a.qc-news-feat-card .qc-news-meta-item"
    FEAT_META_ICON = "a.qc-news-feat-card svg.qc-news-meta-ico"
    FEAT_IMG = "img.qc-news-feat-img"
    FEAT_MEDIA = ".qc-news-feat-media"      # clipping wrapper: carries the visible image radius
    GRID = "[data-qc-news-grid]"
    CARD = "a.qc-news-card"
    CARD_IMG = "a.qc-news-card img.qc-news-card-img"
    CARD_MEDIA = "a.qc-news-card .qc-news-card-media"
    CARD_TITLE = "a.qc-news-card h3.qc-news-card-title"
    CARD_META = "a.qc-news-card .qc-news-meta"
    LOAD_MORE = "button.qc-news-more"
    LOAD_MORE_ICON = "button.qc-news-more svg"
    STATUS = "p.qc-news-status"
    EMPTY = "[data-qc-news-empty]"

    # ---- Detail -------------------------------------------------------------------
    D_READY = "section.qc-newsd[data-qc-newsd-ready='true']"
    D_HERO_TITLE = "h1.qc-newsd-hero-title"
    D_CRUMB_ITEMS = "nav.qc-newsd-crumbs > :is(a, span)"
    D_CRUMB_SEP = "nav.qc-newsd-crumbs svg.qc-newsd-crumb-sep"
    D_ARTICLE = "[data-qc-newsd-article]"
    D_IMG = "img.qc-newsd-img"
    D_MEDIA = "[data-qc-newsd-media]"
    D_TITLE = "h2.qc-newsd-title"
    D_PILL = "span.qc-newsd-cat-pill"
    D_META_ITEM = "span.qc-newsd-meta-item"
    D_META_ICON = "svg.qc-newsd-meta-ico"
    D_CONTENT = "[data-qc-newsd-content]"
    D_BODY_P = "[data-qc-newsd-content] p"
    D_TAG = "span.qc-newsd-tag"
    D_TAGS = "[data-qc-newsd-tags]"
    D_SHARE = "[data-qc-newsd-share]"
    D_SHARE_LABEL = "[data-qc-newsd-share-label]"
    D_SHARE_BTN = "a.qc-newsd-share-btn"
    D_SHARE_ICON = "a.qc-newsd-share-btn svg"
    D_DIVIDER = "[data-qc-newsd-share]"

    # ---- Navigation -------------------------------------------------------------
    def open_listing(self, locale: str = "en") -> "NewsPage":
        self.open(web_url(LISTING_PATH, locale=locale))
        self.wait_listing()
        return self

    def wait_listing(self) -> None:
        self.wait_for(self.READY, state="attached", timeout=30000)
        self.wait_for(self.CARD, first=True, timeout=30000)

    def open_detail(self, article_id: int, locale: str = "en") -> "NewsPage":
        self.open(web_url(f"{DETAIL_PATH}?id={article_id}", locale=locale))
        self.wait_detail()
        return self

    def wait_detail(self) -> None:
        self.wait_for(self.D_READY, state="attached", timeout=30000)
        self.wait_for(self.D_TITLE, timeout=30000)

    def open_featured(self) -> "NewsPage":
        before = self.page.url
        self.click(self.FEATURED)
        self.wait_for_url(lambda u: u != before, timeout=30000)
        self.wait_detail()
        return self

    def go_back(self) -> "NewsPage":
        self.page.go_back()
        self.wait_listing()
        return self

    def reload(self) -> None:
        self.page.reload()

    def navigate_to_listing_via_menu(self) -> bool:
        """Header Media Center > News; returns False when the link is not reachable."""
        if not self.page.locator(self.NAV_NEWS_LINK).count():
            return False
        self.page.locator(self.NAV_MEDIA_PARENT).first.hover()
        link = self.page.locator(self.NAV_NEWS_LINK).first
        link.wait_for(state="visible", timeout=10000)
        before = self.page.url
        link.click()
        self.wait_for_url(lambda u: u != before, timeout=30000)
        self.wait_listing()
        return True

    def enable_dark_mode(self) -> "NewsPage":
        AccessibilityToolsComponent(self.page).enable_dark_mode()
        self.page.wait_for_function(
            "() => document.getAnimations().every((a) => a.playState !== 'running')", timeout=10000)
        return self

    # ---- Listing actions (each waits for the grid to re-render) -------------------
    def _rerender(self, action) -> None:
        before = self.page.evaluate(
            "() => [...document.querySelectorAll('a.qc-news-card, a.qc-news-feat-card')].map(a => a.getAttribute('href')).join('|')"
            " + '#' + ((document.querySelector('p.qc-news-status') || {}).textContent || '')")
        action()
        try:
            self.page.wait_for_function(
                """(b) => ([...document.querySelectorAll('a.qc-news-card, a.qc-news-feat-card')].map(a => a.getAttribute('href')).join('|')
                          + '#' + ((document.querySelector('p.qc-news-status') || {}).textContent || '')) !== b""",
                arg=before, timeout=10000)
        except Exception:  # noqa: BLE001 — an unchanged result set is itself a valid outcome
            pass

    def search(self, text: str) -> None:
        def act():
            self.page.locator(self.SEARCH_INPUT).fill(text)
            self.page.keyboard.press("Enter")
        self._rerender(act)

    def clear_search(self) -> None:
        self.search("")

    def select_category(self, value: str) -> None:
        self._rerender(lambda: self.page.locator(self.CATEGORY).select_option(value))

    def select_sort(self, value: str) -> None:
        self._rerender(lambda: self.page.locator(self.SORT).select_option(value))

    def load_more(self) -> None:
        self._rerender(lambda: self.page.locator(self.LOAD_MORE).click())

    def can_load_more(self) -> bool:
        loc = self.page.locator(self.LOAD_MORE)
        return loc.count() > 0 and loc.first.is_visible() and loc.first.is_enabled()

    def load_all(self, max_rounds: int = 10) -> None:
        for _ in range(max_rounds):
            if not self.can_load_more():
                return
            self.load_more()

    def search_value(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).input_value()

    def open_home(self, locale: str = "en") -> "NewsPage":
        self.open(web_url("/web/qatar-chamber", locale=locale))
        self.wait_for(self.HEADER)
        return self

    def open_card(self, article_id: int) -> "NewsPage":
        """Click the listing card for `article_id` (loading more pages if needed)."""
        sel = f"a[href*='news-detail?id={article_id}']"
        for _ in range(10):
            if self.page.locator(sel).count() or not self.can_load_more():
                break
            self.load_more()
        before = self.page.url
        self.click(sel)
        self.wait_for_url(lambda u: u != before, timeout=30000)
        self.wait_detail()
        return self

    def mark_document(self) -> None:
        self.page.evaluate("() => { window.__qcNoReload = true; }")

    def document_marked(self) -> bool:
        return self.page.evaluate("() => window.__qcNoReload === true")

    # ---- Data ---------------------------------------------------------------------
    def api_items(self, locale: str = "en") -> list:
        lang = "ar_SA" if locale == "ar" else "en_US"
        resp = self.page.request.get(web_url(API_LIST.format(lang=lang)))
        return resp.json().get("items", []) if resp.ok else []

    def listed_ids(self) -> list:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('a.qc-news-feat-card, a.qc-news-card')]
                     .map(a => +(new URL(a.href).searchParams.get('id')))""")

    def card_titles(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.FEAT_TITLE}, {self.CARD_TITLE}").all_inner_texts()]

    def card_facts(self, locator: str = CARD) -> list:
        return self.page.locator(locator).evaluate_all(
            """cards => cards.map(c => { const r = c.getBoundingClientRect();
                const t = c.querySelector('h2, h3');
                return {x: r.x, y: r.y, width: r.width, height: r.height,
                        title: t ? t.innerText.trim() : '', titleRight: t ? t.getBoundingClientRect().right : 0,
                        titleAlign: t ? getComputedStyle(t).textAlign : null, titleDir: t ? getComputedStyle(t).direction : null,
                        meta: [...c.querySelectorAll('.qc-news-meta-item')].map(m => m.innerText.trim()),
                        hasSummary: !!c.querySelector('.qc-news-feat-summary, .qc-news-card-summary, p'),
                        pills: c.querySelectorAll('.qc-news-cat-pill').length,
                        clipped: [...c.querySelectorAll('*')].some(e => e.offsetParent && e.children.length === 0
                                  && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'visible')}; })""")

    # ---- Generic state ------------------------------------------------------------
    def styles(self, locator: str, props, nth: int = 0, pseudo: str = None) -> dict:
        return self.page.locator(locator).nth(nth).evaluate(
            "(e, [props, ps]) => { const c = getComputedStyle(e, ps); const o = {}; props.forEach(p => o[p] = c.getPropertyValue(p).trim()); return o; }",
            [list(props), pseudo])

    def box(self, locator: str, nth: int = 0):
        loc = self.page.locator(locator)
        return loc.nth(nth).bounding_box() if loc.count() > nth else None

    def boxes(self, locator: str) -> list:
        loc = self.page.locator(locator)
        return [loc.nth(i).bounding_box() for i in range(loc.count())]

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def texts(self, locator: str) -> list:
        return [" ".join(t.split()) for t in self.page.locator(locator).all_inner_texts()]

    def text_of(self, locator: str, nth: int = 0) -> str:
        loc = self.page.locator(locator)
        return " ".join(loc.nth(nth).inner_text().split()) if loc.count() > nth else ""

    def attribute(self, locator: str, name: str, nth: int = 0):
        return self.page.locator(locator).nth(nth).get_attribute(name)

    def selected_label(self, locator: str) -> str:
        return self.page.locator(locator).first.evaluate("s => s.options[s.selectedIndex].text")

    def contrast(self, locator: str, nth: int = 0) -> dict:
        return self.page.locator(locator).nth(nth).evaluate(_CONTRAST_JS)

    def current_url(self) -> str:
        return self.page.url

    def document_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.dir")

    def theme(self):
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    def horizontal_overflow_px(self) -> int:
        return self.page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")

    def scroll_width(self) -> int:
        return self.page.evaluate("() => document.documentElement.scrollWidth")

    def scroll_to(self, locator: str) -> None:
        self.page.locator(locator).first.scroll_into_view_if_needed()

    def divider_above_share(self):
        """Any horizontal rule between the keyword tags and the share row:
        an <hr>, the share row's top border, or the tags block's bottom border."""
        return self.page.evaluate(
            """() => { const share = document.querySelector('[data-qc-newsd-share]'); if (!share) return null;
                const c = getComputedStyle(share);
                if (c.borderTopStyle !== 'none' && parseFloat(c.borderTopWidth) > 0)
                    return {how: 'share border-top', width: share.getBoundingClientRect().width, px: c.borderTopWidth, color: c.borderTopColor};
                let prev = share.previousElementSibling;
                if (prev) { const pc = getComputedStyle(prev), r = prev.getBoundingClientRect();
                    if (prev.tagName === 'HR' || (r.height <= 2 && r.width > 200))
                        return {how: prev.tagName.toLowerCase(), width: r.width, px: r.height + 'px',
                                color: pc.backgroundColor !== 'rgba(0, 0, 0, 0)' ? pc.backgroundColor : pc.borderTopColor};
                    if (pc.borderBottomStyle !== 'none' && parseFloat(pc.borderBottomWidth) > 0)
                        return {how: 'border-bottom of ' + prev.className, width: r.width, px: pc.borderBottomWidth, color: pc.borderBottomColor}; }
                return null; }""")

    def white_backgrounds(self, scope: str) -> list:
        return self.page.evaluate(
            """(s) => [...document.querySelectorAll(s + ', ' + s + ' *')].filter(e => e.offsetParent !== null
                       && getComputedStyle(e).backgroundColor === 'rgb(255, 255, 255)')
                       .map(e => e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0]).slice(0, 10)""", scope)

    def tab_until(self, predicate, max_presses: int = 80):
        for i in range(max_presses):
            self.page.keyboard.press("Tab")
            info = self.page.evaluate(
                """() => { const e = document.activeElement; if (!e || e === document.body) return null; const c = getComputedStyle(e);
                    return {cls: String(e.className), tag: e.tagName.toLowerCase(), href: e.getAttribute('href') || '',
                            outlineStyle: c.outlineStyle, outlineWidth: c.outlineWidth, outlineColor: c.outlineColor,
                            focusVisible: e.matches(':focus-visible')}; }""")
            if info and predicate(info):
                return i + 1, info
        return None, None

    def press(self, key: str) -> None:
        self.page.keyboard.press(key)

    def outline_contrast(self) -> float:
        """Contrast of the focused element's outline colour vs the background behind it."""
        return self.page.evaluate(
            """() => { const e = document.activeElement, parse = (c) => (c.match(/[0-9.]+/g) || [0,0,0]).map(Number);
                const lum = (rgb) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                                       return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2]); };
                let n = e.parentElement, bg = [255, 255, 255];
                while (n) { const c = getComputedStyle(n).backgroundColor, v = parse(c); if (!(v.length > 3 && v[3] === 0) && c !== 'transparent') { bg = v; break; } n = n.parentElement; }
                const l1 = lum(parse(getComputedStyle(e).outlineColor)), l2 = lum(bg);
                return Math.round((Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05) * 100) / 100; }""")

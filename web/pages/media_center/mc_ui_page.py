"""
web/pages/media_center/mc_ui_page.py — MediaCenterUiPage.

Public Media Center hub (PBI 130709) seen through its DESIGN / COMPATIBILITY
lens: Figma design-token reads (computed styles + geometry), Light/Dark and
High-Contrast themes, EN/AR (RTL) mirroring, responsive viewports and keyboard
operation of the photo carousel. Read-only: no CMS state is touched and the
public subscribe form is never submitted (FE-SUBS owns it).

Locator extraction (2026-10-13, live qcdev, logged-out, 1920x1080 / 768x1024 /
390x844, EN + AR) — every hub block renders its own stable BEM-style class
family plus `data-qc-*` hooks, and each block flips a `data-*-ready="true"`
flag on its <section> once its client-side fetch has rendered:

    hero      section.qc-mc-hero[data-qc-mch-ready]
    counts    section.qc-mc-counts[data-qc-mcc-ready]     (5 .qc-mc-counts-card)
    explore   section.qc-mc-qa[data-qc-mcqa-ready]        (6 a.qc-mc-qa-card)
    news      section.qc-mc-nf[data-qc-mcnf-ready]        (lead + 3 cards)
    photo     section.qc-mc-pf[data-qc-mcpf-ready]        (carousel, 3 visible)
    video     section.qc-mc-vf[data-qc-mcvf-ready]        (3 cards)
    band      section.qc-mc-sub[data-qc-mcsub-ready]

Page-level section order is read from the Liferay layout-structure wrappers
(`.lfr-layout-structure-item-qc-*`), which carry the fragment key in a class.

Design notes recorded during extraction (asserted by the tests, not here):
  * The body container is not one wrapper: every section has 20px side
    padding and a 1320px max-width shell, and the 64px/48px rhythm comes from
    per-section top/bottom padding. Rendered geometry (x=300, w=1320, 48px
    between shells) is what is compared, which is what Figma specifies.
  * Theme: Dark = `<html data-theme="dark">`, High Contrast =
    `<html class="qc-a11y-contrast">` — both only via the header
    Accessibility-tools panel (AccessibilityToolsComponent, reused).
  * AR URL is `/ar/web/qatar-chamber/media-center` (web_url(locale="ar")).
"""

from __future__ import annotations

import io
from pathlib import Path

import allure

from config.settings import web_url
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent
from web.pages.components.header_component import HeaderComponent

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class MediaCenterUiPage(BasePage):
    PATH = "/web/qatar-chamber/media-center"

    # ── Page-level structure ─────────────────────────────────────────────
    LAYOUT_ITEMS = "[class*='lfr-layout-structure-item-qc-']"
    EXPECTED_SECTION_ORDER = [
        "qc-global-site-header",
        "qc-media-center-hero",
        "qc-media-center-counts",
        "qc-media-center-quick-access",
        "qc-media-center-news-feed",
        "qc-media-center-photo-feed",
        "qc-media-center-video-feed",
        "qc-media-center-subscribe",
        "qc-global-site-footer",
    ]
    READY_SECTIONS = (
        "section.qc-mc-hero[data-qc-mch-ready='true']",
        "section.qc-mc-counts[data-qc-mcc-ready='true']",
        "section.qc-mc-qa[data-qc-mcqa-ready='true']",
        "section.qc-mc-nf[data-qc-mcnf-ready='true']",
        "section.qc-mc-pf[data-qc-mcpf-ready='true']",
        "section.qc-mc-vf[data-qc-mcvf-ready='true']",
        "section.qc-mc-sub[data-qc-mcsub-ready='true']",
    )

    # ── Hero ─────────────────────────────────────────────────────────────
    HERO = "section.qc-mc-hero"
    HERO_BG = ".qc-mc-hero-bg"
    HERO_SCRIM = ".qc-mc-hero-scrim"
    HERO_INNER = ".qc-mc-hero-inner"
    HERO_TOP = ".qc-mc-hero-top"
    HERO_PAGE_LABEL = "h1.qc-mc-hero-pagetitle"
    HERO_CRUMBS = "nav.qc-mc-hero-crumbs"
    HERO_CRUMB_HOME = "a.qc-mc-hero-crumb--home"
    HERO_CRUMB_HOME_LABEL = ".qc-mc-hero-crumb--home .qc-mc-hero-crumb-label"
    HERO_HOME_ICON = "svg.qc-mc-hero-homeico"
    HERO_CRUMB_SEPARATOR_ICON = "svg.qc-mc-hero-chev"
    HERO_CRUMB_CURRENT = ".qc-mc-hero-crumb--current"
    HERO_CENTER = ".qc-mc-hero-center"
    HERO_COPY = ".qc-mc-hero-copy"
    HERO_HEADLINE = "p.qc-mc-hero-headline"
    HERO_DESCRIPTION = "p.qc-mc-hero-desc"
    HERO_SEARCH_FORM = "form.qc-mc-hero-search"
    HERO_SEARCH_INPUT = "input.qc-mc-hero-input"
    HERO_SEARCH_BUTTON = "button.qc-mc-hero-btn"
    HERO_SEARCH_BUTTON_ICON = "svg.qc-mc-hero-btn-ico"
    HERO_SEARCH_BUTTON_LABEL = ".qc-mc-hero-btn-label"

    # ── Summary counts strip ─────────────────────────────────────────────
    COUNTS = "section.qc-mc-counts"
    COUNTS_SHELL = ".qc-mc-counts-shell"
    COUNTS_TEXTURE = ".qc-mc-counts-texture"
    COUNTS_LIST = ".qc-mc-counts-list"
    COUNT_CARD = ".qc-mc-counts-card"
    COUNT_ICON_CHIP = ".qc-mc-counts-badge"
    COUNT_ICON = ".qc-mc-counts-badge-img"
    COUNT_TEXT = ".qc-mc-counts-text"
    COUNT_LABEL = ".qc-mc-counts-label"
    COUNT_VALUE = ".qc-mc-counts-value"

    # ── Explore the hub (quick-access) ───────────────────────────────────
    QA = "section.qc-mc-qa"
    QA_SHELL = ".qc-mc-qa-shell"
    QA_HEAD = ".qc-mc-qa-head"
    QA_EYEBROW = ".qc-mc-qa-eyebrow"
    QA_HEADING = "h2.qc-mc-qa-heading"
    QA_DESCRIPTION = "p.qc-mc-qa-desc"
    QA_GRID = ".qc-mc-qa-grid"
    QA_CARD = "a.qc-mc-qa-card"
    QA_ICON_TILE = ".qc-mc-qa-tile"
    QA_ICON = ".qc-mc-qa-tile-img"
    QA_TITLE = ".qc-mc-qa-title"
    QA_CARD_DESCRIPTION = ".qc-mc-qa-cardesc"
    QA_ARROW = "svg.qc-mc-qa-arrow"

    # ── News & press releases ────────────────────────────────────────────
    NF = "section.qc-mc-nf"
    NF_SHELL = ".qc-mc-nf-shell"
    NF_HEAD = ".qc-mc-nf-head"
    NF_EYEBROW = ".qc-mc-nf-eyebrow"
    NF_HEADING = "h2.qc-mc-nf-heading"
    NF_CTA_HEAD = "a.qc-mc-nf-cta--head"
    NF_CTA_HEAD_ICON = "a.qc-mc-nf-cta--head .qc-mc-nf-cta-ico"
    NF_CTA_FOOT = "a.qc-mc-nf-cta--foot"
    NF_LEAD = "article.qc-mc-nf-lead"
    NF_LEAD_MEDIA = ".qc-mc-nf-lead-media"
    NF_LEAD_IMAGE = ".qc-mc-nf-lead-media img.qc-mc-nf-img"
    NF_LEAD_BODY = ".qc-mc-nf-lead-body"
    NF_LEAD_CHIPS = ".qc-mc-nf-lead .qc-mc-nf-chips"
    NF_LEAD_CHIP = ".qc-mc-nf-lead .qc-mc-nf-chip"
    NF_LEAD_TITLE = "a.qc-mc-nf-lead-title"
    NF_LEAD_EXCERPT = "p.qc-mc-nf-lead-text"
    NF_LEAD_META = ".qc-mc-nf-meta--lead"
    NF_LEAD_META_ITEM = ".qc-mc-nf-meta--lead .qc-mc-nf-meta-item"
    NF_LEAD_META_ICON = ".qc-mc-nf-meta--lead .qc-mc-nf-meta-item svg"
    NF_READ_MORE = "a.qc-mc-nf-more"
    NF_READ_MORE_ICON = ".qc-mc-nf-more-ico"
    NF_READ_MORE_ICON_SVG = ".qc-mc-nf-more-ico svg"
    NF_GRID = ".qc-mc-nf-grid"
    NF_CARD = "a.qc-mc-nf-card"
    NF_CARD_MEDIA = ".qc-mc-nf-card-media"
    NF_CARD_IMAGE = ".qc-mc-nf-card-media img"
    NF_CARD_TITLE = "h3.qc-mc-nf-card-title"
    NF_CARD_META = ".qc-mc-nf-card .qc-mc-nf-meta"
    NF_CARD_META_ITEM = ".qc-mc-nf-card .qc-mc-nf-meta-item"

    # ── Photo Gallery carousel ───────────────────────────────────────────
    PF = "section.qc-mc-pf"
    PF_SHELL = ".qc-mc-pf-shell"
    PF_HEAD = ".qc-mc-pf-head"
    PF_EYEBROW = ".qc-mc-pf-eyebrow"
    PF_HEADING = "h2.qc-mc-pf-heading"
    PF_CTA_HEAD = "a.qc-mc-pf-cta--head"
    PF_CTA_HEAD_ICON = "a.qc-mc-pf-cta--head .qc-mc-pf-cta-ico"
    PF_GRID = ".qc-mc-pf-grid"
    PF_CARD = "a.qc-mc-pf-card"
    PF_CARD_MEDIA = ".qc-mc-pf-card-media"
    PF_CARD_IMAGE = "img.qc-mc-pf-img"
    PF_BADGE = ".qc-mc-pf-badge"
    PF_BADGE_ICON = ".qc-mc-pf-badge svg"
    PF_BADGE_TEXT = ".qc-mc-pf-badge-text"
    PF_CATEGORY_CHIP = ".qc-mc-pf-tag"
    PF_CARD_TITLE = "h3.qc-mc-pf-card-title"
    PF_CARD_META = ".qc-mc-pf-meta"
    PF_CARD_META_ITEM = ".qc-mc-pf-meta-item"
    PF_CONTROLS = "[data-qc-mcpf-controls]"
    PF_PREV = "button[data-qc-mcpf-prev]"
    PF_NEXT = "button[data-qc-mcpf-next]"
    PF_NAV_BUTTONS = "button.qc-mc-pf-nav"
    PF_INDICATOR = "[data-qc-mcpf-indicator]"

    # ── Video Gallery ────────────────────────────────────────────────────
    VF = "section.qc-mc-vf"
    VF_SHELL = ".qc-mc-vf-shell"
    VF_HEAD = ".qc-mc-vf-head"
    VF_EYEBROW = ".qc-mc-vf-eyebrow"
    VF_HEADING = "h2.qc-mc-vf-heading"
    VF_CTA_HEAD = "a.qc-mc-vf-cta--head"
    VF_GRID = ".qc-mc-vf-grid"
    VF_CARD = "a.qc-mc-vf-card"
    VF_CARD_MEDIA = ".qc-mc-vf-card-media"
    VF_CARD_IMAGE = "img.qc-mc-vf-img"
    VF_SCRIM = ".qc-mc-vf-scrim"
    VF_PLAY = ".qc-mc-vf-play"
    VF_DURATION = ".qc-mc-vf-duration"
    VF_CATEGORY_CHIP = ".qc-mc-vf-tag"
    VF_CARD_TITLE = "h3.qc-mc-vf-card-title"
    VF_CARD_META = ".qc-mc-vf-meta"
    VF_CARD_META_ITEM = ".qc-mc-vf-meta-item"

    # ── Subscription band (read-only here) ───────────────────────────────
    SUB = "section.qc-mc-sub"
    SUB_BAND = ".qc-mc-sub-band"
    SUB_GRADIENT = ".qc-mc-sub-gradient"
    SUB_HEADING = "h2.qc-mc-sub-heading"
    SUB_DESCRIPTION = "p.qc-mc-sub-desc"
    SUB_FORM = "form.qc-mc-sub-form"
    SUB_INPUT = "input.qc-mc-sub-input"
    SUB_BUTTON = "button.qc-mc-sub-btn"

    # Hub sections (hero .. band) — the scope for readability/clipping scans.
    HUB_SECTIONS = (HERO, COUNTS, QA, NF, PF, VF, SUB)

    # Every computed-style property any design-token check reads.
    STYLE_PROPS = [
        "display", "width", "height", "paddingTop", "paddingRight", "paddingBottom",
        "paddingLeft", "gap", "rowGap", "columnGap", "borderTopLeftRadius",
        "backgroundColor", "backgroundImage", "backgroundSize", "borderTopWidth",
        "borderTopColor", "color", "fontFamily", "fontSize", "fontWeight", "lineHeight",
        "textAlign", "cursor", "textDecorationLine", "gridTemplateColumns",
        "flexDirection", "objectFit", "backdropFilter", "direction", "opacity",
        "alignItems", "alignSelf", "justifyContent", "outlineStyle", "outlineWidth",
        "outlineColor", "outlineOffset", "boxShadow", "unicodeBidi",
    ]

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)
        self.a11y = AccessibilityToolsComponent(page)

    # ── Navigation ───────────────────────────────────────────────────────
    def open_hub(self, locale: str = "en") -> "MediaCenterUiPage":
        self.open(web_url(self.PATH, locale=locale))
        self.wait_until_rendered()
        return self

    def wait_until_rendered(self, timeout: int = 45000) -> "MediaCenterUiPage":
        """Every hub block fetches client-side; waits for all seven
        `data-*-ready="true"` flags, the hero background image and web
        fonts, so geometry/style reads never see a half-rendered block."""
        for sel in self.READY_SECTIONS:
            self.wait_for(sel, state="attached", timeout=timeout)
        self.page.wait_for_function(
            "(sel) => { const e = document.querySelector(sel);"
            " return !!e && getComputedStyle(e).backgroundImage !== 'none'; }",
            arg=self.HERO_BG, timeout=timeout,
        )
        self.page.wait_for_function("() => document.fonts.status === 'loaded'", timeout=timeout)
        return self

    def switch_language_via_header(self) -> "MediaCenterUiPage":
        """Clicks the real header language switcher ('AR'/'EN') and waits for
        the other locale's hub to render."""
        self.click(self.header.LANGUAGE_SWITCHER)
        self.wait_for_url(lambda url: "/ar/" in url or url.rstrip("/").endswith("/ar"), timeout=60000)
        self.wait_for(self.header.HEADER)
        self.wait_until_rendered()
        return self

    def enable_dark_theme(self) -> "MediaCenterUiPage":
        self.a11y.enable_dark_mode()
        return self

    def enable_high_contrast(self) -> "MediaCenterUiPage":
        self.a11y.enable_high_contrast()
        return self

    def current_url(self) -> str:
        return self.page.url

    # ── Generic design reads ─────────────────────────────────────────────
    def style(self, locator: str, nth: int = 0) -> dict:
        """getComputedStyle subset (STYLE_PROPS) + document-space box
        {x, y, w, h, right, bottom} + text for the nth match of `locator`."""
        return self.page.locator(locator).nth(nth).evaluate(
            """(el, props) => {
                const s = getComputedStyle(el); const r = el.getBoundingClientRect();
                const out = {};
                props.forEach(p => out[p] = s[p]);
                out.box = {x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height,
                           right: r.right + scrollX, bottom: r.bottom + scrollY};
                out.text = (el.innerText || '').trim();
                out.tag = el.tagName.toLowerCase();
                return out;
            }""",
            self.STYLE_PROPS,
        )

    def styles_all(self, locator: str) -> list:
        return [self.style(locator, i) for i in range(self.count(locator))]

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def visible_count(self, locator: str) -> int:
        return self.page.locator(locator).evaluate_all(
            "els => els.filter(e => { const r = e.getBoundingClientRect();"
            " const s = getComputedStyle(e); return r.width > 0 && r.height > 0"
            " && s.visibility !== 'hidden' && s.display !== 'none'; }).length"
        )

    def texts(self, locator: str) -> list:
        return [t.strip() for t in self.page.locator(locator).all_inner_texts()]

    def texts_within(self, locator: str, nth: int, inner: str) -> list:
        """Inner texts of `inner` matches inside the nth `locator` match."""
        return [t.strip() for t in self.page.locator(locator).nth(nth).locator(inner).all_inner_texts()]

    def image_states(self, locator: str, timeout: int = 15000) -> list:
        """Scrolls each <img> into view (lazy loading), waits for it to settle,
        and reports {loaded, natural_width, src} per match."""
        loc = self.page.locator(locator)
        for i in range(loc.count()):
            loc.nth(i).scroll_into_view_if_needed()
        try:
            self.page.wait_for_function(
                "(sel) => Array.from(document.querySelectorAll(sel)).every(i => i.complete)",
                arg=locator, timeout=timeout,
            )
        except Exception:  # noqa: BLE001 — a never-completing image is reported as not loaded below
            pass
        return loc.evaluate_all(
            "els => els.map(i => ({loaded: i.complete && i.naturalWidth > 0,"
            " natural_width: i.naturalWidth, src: (i.currentSrc || i.src || '').slice(0, 120)}))"
        )

    def icon_sources(self, locator: str) -> list:
        """Mask-image icons (counts / quick-access tiles): resolves each
        icon's CSS mask URL and fetches it, so a broken icon (404 / missing
        mask) is reported instead of silently rendering an empty tile."""
        infos = self.page.locator(locator).evaluate_all(
            """els => els.map(e => { const s = getComputedStyle(e); const r = e.getBoundingClientRect();
                const m = (s.webkitMaskImage || s.maskImage || 'none').match(/url\\(["']?([^"')]+)["']?\\)/);
                return {url: m ? m[1] : null, visible: r.width > 0 && r.height > 0 && s.visibility !== 'hidden'}; })"""
        )
        for info in infos:
            info["status"] = None
            if info["url"]:
                try:
                    info["status"] = self.page.request.get(info["url"]).status
                except Exception:  # noqa: BLE001 — unreachable icon is reported as status None
                    info["status"] = None
        return infos

    def focus_first_quick_access_card(self) -> None:
        self.page.locator(self.QA_CARD).first.focus()

    def attribute(self, locator: str, name: str, nth: int = 0):
        return self.page.locator(locator).nth(nth).get_attribute(name)

    def placeholder(self, locator: str) -> str:
        return self.page.locator(locator).get_attribute("placeholder") or ""

    def placeholder_style(self, locator: str) -> dict:
        return self.page.locator(locator).evaluate(
            "el => { const s = getComputedStyle(el, '::placeholder');"
            " return {color: s.color, fontSize: s.fontSize, lineHeight: s.lineHeight,"
            " fontWeight: s.fontWeight, fontFamily: s.fontFamily}; }"
        )

    def document_state(self) -> dict:
        return self.page.evaluate(
            """() => ({dir: document.documentElement.getAttribute('dir') || getComputedStyle(document.documentElement).direction,
                       lang: document.documentElement.lang,
                       theme: document.documentElement.getAttribute('data-theme'),
                       html_class: document.documentElement.className,
                       scroll_width: document.documentElement.scrollWidth,
                       client_width: document.documentElement.clientWidth,
                       body_background: getComputedStyle(document.body).backgroundColor,
                       viewport: [innerWidth, innerHeight]})"""
        )

    def section_order(self) -> list:
        """Fragment keys of the page's top-level layout items, in DOM order."""
        return self.page.locator(self.LAYOUT_ITEMS).evaluate_all(
            """els => els.map(e => { const m = e.className.match(/lfr-layout-structure-item-(qc-[a-z0-9-]+)/);
                                    return m ? m[1] : null; }).filter(Boolean)"""
        )

    def font_loaded(self, family: str = "Cairo") -> bool:
        return self.page.evaluate(
            "(f) => document.fonts.check(`16px ${f}`) && Array.from(document.fonts)"
            ".some(x => x.family.replace(/\"/g,'') === f && x.status === 'loaded')",
            family,
        )

    def icon_direction(self, locator: str, nth: int = 0) -> str:
        """'left' / 'right' — which way an arrow/chevron SVG visually points,
        derived from its rendered geometry (path sampled in user space, CSS
        transform/scaleX flip applied). Arrows: the tip side carries the
        barbs, so it holds more path length; chevrons: the tip side is the
        narrow (single-vertex) side."""
        return self.page.locator(locator).nth(nth).evaluate(
            """(el) => {
                const svg = el.tagName.toLowerCase() === 'svg' ? el : el.querySelector('svg');
                if (!svg) return 'none';
                const pts = [];
                svg.querySelectorAll('path, line, polyline').forEach(p => {
                    if (!p.getTotalLength) return;
                    const L = p.getTotalLength();
                    for (let i = 0; i <= 120; i++) { const q = p.getPointAtLength(L * i / 120); pts.push([q.x, q.y]); }
                });
                if (!pts.length) return 'none';
                const xs = pts.map(p => p[0]);
                const minX = Math.min(...xs), maxX = Math.max(...xs), w = maxX - minX || 1;
                const left = pts.filter(p => p[0] <= minX + 0.3 * w), right = pts.filter(p => p[0] >= maxX - 0.3 * w);
                const spread = a => a.length ? Math.max(...a.map(p => p[1])) - Math.min(...a.map(p => p[1])) : 0;
                let dir;
                const ratio = left.length / Math.max(right.length, 1);
                if (ratio > 1.25) dir = 'left';
                else if (ratio < 0.8) dir = 'right';
                else dir = spread(left) < spread(right) ? 'left' : 'right';
                // CSS mirroring on the svg or any ancestor up to the card
                let flip = false, n = svg;
                for (let i = 0; i < 4 && n; i++, n = n.parentElement) {
                    const t = getComputedStyle(n).transform;
                    if (t && t.startsWith('matrix(')) { const a = parseFloat(t.slice(7)); if (a < 0) flip = !flip; }
                }
                if (flip) dir = dir === 'left' ? 'right' : 'left';
                return dir;
            }"""
        )

    def hover(self, locator: str, nth: int = 0) -> None:
        self.page.locator(locator).nth(nth).hover()

    def move_mouse_away(self) -> None:
        self.page.mouse.move(1, 1)

    def scroll_into_view(self, locator: str, nth: int = 0) -> None:
        self.page.locator(locator).nth(nth).scroll_into_view_if_needed()

    def links_and_roles_inside(self, locator: str, nth: int = 0) -> dict:
        return self.page.locator(locator).nth(nth).evaluate(
            """el => ({tag: el.tagName.toLowerCase(), role: el.getAttribute('role'),
                      tabindex: el.getAttribute('tabindex'), href: el.getAttribute('href'),
                      onclick: el.hasAttribute('onclick') || typeof el.onclick === 'function',
                      inner_links: el.querySelectorAll('a[href]').length,
                      inner_buttons: el.querySelectorAll('button, [role=button], [role=link]').length,
                      closest_link: !!el.closest('a[href]')})"""
        )

    # ── Carousel (photo feed) ────────────────────────────────────────────
    def indicator_text(self) -> str:
        return self.page.locator(self.PF_INDICATOR).inner_text().strip()

    def wait_for_indicator(self, expected_prefix: str, timeout: int = 10000) -> None:
        self.page.wait_for_function(
            "([sel, p]) => { const e = document.querySelector(sel);"
            " return !!e && e.innerText.trim().startsWith(p); }",
            arg=[self.PF_INDICATOR, expected_prefix], timeout=timeout,
        )

    def tab_to_carousel_next(self, max_presses: int = 12) -> bool:
        """Keyboard-only: places focus on the last visible photo card (the
        element immediately before the controls in tab order) and Tabs
        forward until the Next control holds focus."""
        self.page.locator(self.PF_CARD).last.focus()
        return self.press_tab_until_focused(self.PF_NEXT, max_presses=max_presses)

    def focused_element(self) -> dict:
        return self.page.evaluate(
            """() => { const a = document.activeElement; const s = getComputedStyle(a);
                       const bg = getComputedStyle(document.body).backgroundColor;
                       return {cls: typeof a.className === 'string' ? a.className : '',
                               label: a.getAttribute('aria-label'), tag: a.tagName.toLowerCase(),
                               outline_style: s.outlineStyle, outline_width: s.outlineWidth,
                               outline_color: s.outlineColor, box_shadow: s.boxShadow,
                               body_background: bg}; }"""
        )

    def click_next(self) -> None:
        self.click(self.PF_NEXT)

    def is_disabled(self, locator: str) -> bool:
        return self.page.locator(locator).is_disabled()

    # ── Navigation through a quick-access card ───────────────────────────
    def click_quick_access_card(self, title: str) -> dict:
        """Clicks the WHOLE card (its centre point, not the title text) and
        returns where the browser landed + that page's HTTP status."""
        card = self.page.locator(self.QA_CARD).filter(has=self.page.locator(self.QA_TITLE, has_text=title))
        href = card.first.get_attribute("href")
        card.first.scroll_into_view_if_needed()
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=60000) as nav:
            card.first.click()
        resp = nav.value
        return {"href": href, "url": self.page.url, "status": resp.status if resp else None,
                "title": self.page.title()}

    # ── Scans ────────────────────────────────────────────────────────────
    def clipped_or_offscreen_text(self, scopes: tuple = None) -> list:
        """Visible elements with their own text inside `scopes` that either
        overflow the viewport horizontally or are clipped by an overflow box
        WITHOUT an intended ellipsis / line-clamp."""
        scopes = list(scopes or self.HUB_SECTIONS)
        return self.page.evaluate(
            """(scopes) => {
                const out = []; const vw = document.documentElement.clientWidth;
                scopes.forEach(sc => document.querySelectorAll(sc).forEach(root => root.querySelectorAll('*').forEach(el => {
                    const own = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
                    if (!own) return;
                    const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
                    if (r.width === 0 || r.height === 0 || s.visibility === 'hidden') return;
                    if (el.closest('[aria-hidden=true]') || el.closest('.qc-mc-hero-srlabel, .qc-mc-sub-srlabel, .qc-mc-sub-captcha')) return;
                    const intended = s.textOverflow === 'ellipsis' || (s.webkitLineClamp && s.webkitLineClamp !== 'none');
                    const clipsX = ['hidden', 'clip'].includes(s.overflowX) && el.scrollWidth > el.clientWidth + 1;
                    const clipsY = ['hidden', 'clip'].includes(s.overflowY) && el.scrollHeight > el.clientHeight + 2;
                    const off = r.left < -1 || r.right > vw + 1;
                    if (off || ((clipsX || clipsY) && !intended)) {
                        out.push({cls: (typeof el.className === 'string' ? el.className : el.tagName).slice(0, 60),
                                  text: el.textContent.trim().slice(0, 50), left: Math.round(r.left), right: Math.round(r.right),
                                  reason: off ? 'outside viewport' : 'clipped'});
                    }
                })));
                return out;
            }""",
            scopes,
        )

    def arabic_text_found(self, locators: list) -> list:
        """Strings containing Arabic script among the given locators' texts
        (and the two input placeholders when listed)."""
        found = []
        for loc in locators:
            values = []
            if loc in (self.HERO_SEARCH_INPUT, self.SUB_INPUT):
                values = [self.placeholder(loc)]
            else:
                values = self.texts(loc)
            for v in values:
                if any("؀" <= ch <= "ۿ" for ch in v):
                    found.append(f"{loc}: {v[:60]}")
        return found

    def readability_scan(self, scopes: tuple = None, text_min: float = 3.0, icon_min: float = 2.0,
                         field_min: float = 3.0) -> list:
        """Pixel-level readability check inside `scopes`, against ONE full-page
        screenshot (computed colours alone cannot answer it: the hero/band
        paint backgrounds on SIBLING layers and icons are CSS masks).

          * text leaf  : computed text colour (alpha-blended) vs the rendered
                         background = mean of the pixels in the text's own box
                         that are clearly NOT the text colour; >= text_min (3:1).
          * icon (svg / CSS mask): most-contrasting rendered ink pixel vs the
                         box's dominant colour; >= icon_min (2:1) — catches a
                         glyph collapsing into its background (same-colour)
                         without flagging Figma-approved icon tokens.
          * input      : the field (background, or border when >= 1px) vs a
                         6px ring around it; >= field_min (3:1). Placeholder
                         text colours are design tokens and not judged here.
        Disabled controls are skipped (WCAG exempts them). Returns offenders
        only. Pillow is imported lazily (not in requirements.txt)."""
        from PIL import Image

        scopes = list(scopes or self.HUB_SECTIONS)
        _dismiss_chatbot_launcher(self.page)
        items = self.page.evaluate(
            """(scopes) => {
                const out = [];
                scopes.forEach(sc => document.querySelectorAll(sc).forEach(root => root.querySelectorAll('*').forEach(el => {
                    const tag = el.tagName.toLowerCase();
                    const own = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
                    const s = getComputedStyle(el);
                    const isIcon = tag === 'svg' || (s.webkitMaskImage && s.webkitMaskImage !== 'none');
                    const isField = tag === 'input';
                    if (!own && !isIcon && !isField) return;
                    if (el.closest('.qc-mc-hero-srlabel, .qc-mc-sub-srlabel, .qc-mc-sub-captcha, .qc-mc-hero-hint, .qc-mc-sub-message')) return;
                    if (el.disabled || (el.closest('button') && el.closest('button').disabled)) return;
                    if (tag === 'svg' && el.parentElement && el.parentElement.closest('svg')) return;
                    let r = el.getBoundingClientRect();
                    let fs = s;
                    if (isField) {  // a transparent, borderless input: the visible field is its painted container
                        let host = el;
                        for (let i = 0; i < 3 && host && getComputedStyle(host).backgroundColor === 'rgba(0, 0, 0, 0)'
                             && !(parseFloat(getComputedStyle(host).borderTopWidth) > 0); i++) host = host.parentElement;
                        if (host && host !== el) { r = host.getBoundingClientRect(); fs = getComputedStyle(host); }
                    }
                    if (own && !isField) { const rg = document.createRange(); rg.selectNodeContents(el); const rr = rg.getBoundingClientRect(); if (rr.width > 0) r = rr; }
                    if (r.width < 4 || r.height < 4 || s.visibility === 'hidden' || s.display === 'none' || parseFloat(s.opacity) === 0) return;
                    out.push({kind: isField ? 'field' : (own ? 'text' : 'icon'),
                              cls: (typeof el.className === 'string' ? el.className : (el.className.baseVal || tag)).slice(0, 50) || tag,
                              text: own ? el.textContent.trim().slice(0, 40) : (isField ? (el.placeholder || '').slice(0, 40) : '[icon]'),
                              color: s.color, bg: fs.backgroundColor, border: fs.borderTopColor, borderW: parseFloat(fs.borderTopWidth) || 0,
                              x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY),
                              w: Math.round(r.width), h: Math.round(r.height)});
                })));
                return out;
            }""",
            scopes,
        )
        img = Image.open(io.BytesIO(self.page.screenshot(full_page=True))).convert("RGB")
        offenders = []
        for it in items:
            x0, y0 = max(it["x"], 0), max(it["y"], 0)
            x1, y1 = min(it["x"] + it["w"], img.width), min(it["y"] + it["h"], img.height)
            if x1 <= x0 or y1 <= y0:
                continue
            if it["kind"] == "field":
                ring = [img.getpixel((xx, yy)) for xx in range(max(x0 - 6, 0), min(x1 + 6, img.width), 3)
                        for yy in (max(y0 - 6, 0), min(y1 + 5, img.height - 1))]
                ring_col = max(set(ring), key=ring.count) if ring else (0, 0, 0)
                cands = [_css_rgb(it["bg"], ring_col)]
                if it["borderW"] >= 1:
                    cands.append(_css_rgb(it["border"], ring_col))
                ratio = max(_contrast(c, ring_col) for c in cands)
                if ratio < field_min:
                    offenders.append({**_public(it), "against": "#%02X%02X%02X" % ring_col, "ratio": round(ratio, 2)})
                continue
            colors = sorted(img.crop((x0, y0, x1, y1)).getcolors(maxcolors=(x1 - x0) * (y1 - y0) + 1) or [], reverse=True)
            if not colors:
                continue
            total = sum(c for c, _ in colors)
            if it["kind"] == "text":
                # Background = mean of the pixels clearly NOT the text colour (works over
                # gradients/photos too). If (almost) nothing differs from the text colour,
                # the text has collapsed into its background -> bg = fg -> ratio 1.
                fg_guess = _css_rgb(it["color"], colors[0][1])
                far = [(cnt, col) for cnt, col in colors if _dist(col, fg_guess) > 60]
                n_far = sum(cnt for cnt, _ in far)
                if n_far >= total * 0.15:
                    bg = tuple(int(sum(cnt * col[i] for cnt, col in far) / n_far) for i in range(3))
                else:
                    bg = fg_guess
                fg = _css_rgb(it["color"], bg)
                ratio = _contrast(fg, bg)
                if ratio < text_min:
                    offenders.append({**_public(it), "against": "#%02X%02X%02X" % bg, "ratio": round(ratio, 2)})
            else:
                dominant = colors[0][1]
                floor = max(2, int(total * 0.005))
                ratio = max([_contrast(dominant, col) for cnt, col in colors if cnt >= floor] or [1.0])
                if ratio < icon_min:
                    offenders.append({**_public(it), "against": "#%02X%02X%02X" % dominant, "ratio": round(ratio, 2)})
        return offenders

    # ── Evidence ─────────────────────────────────────────────────────────
    def save_evidence(self, name: str, full_page: bool = True, folder: str = "reports/mc130709/FE-UI") -> str:
        out_dir = PROJECT_ROOT / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{name}.png"
        png = self.page.screenshot(full_page=full_page)
        path.write_bytes(png)
        allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
        return str(path)


def _public(it: dict) -> dict:
    return {k: it[k] for k in ("kind", "cls", "text", "x", "y", "w", "h")}


def _dist(a: tuple, b: tuple) -> float:
    return sum((x - y) ** 2 for x, y in zip(a[:3], b[:3])) ** 0.5


def _css_rgb(css: str, over: tuple) -> tuple:
    """'rgb(..)'/'rgba(..)' -> opaque (r, g, b), alpha-blended over `over`."""
    import re
    n = [float(v) for v in re.findall(r"[\d.]+", css or "")]
    if len(n) < 3:
        return tuple(over[:3])
    a = n[3] if len(n) > 3 else 1.0
    return tuple(int(round(n[i] * a + over[i] * (1 - a))) for i in range(3))


def _luminance(rgb: tuple) -> float:
    def ch(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _contrast(a: tuple, b: tuple) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

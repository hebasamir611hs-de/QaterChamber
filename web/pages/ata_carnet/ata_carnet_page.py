"""
web/pages/ata_carnet/ata_carnet_page.py — AtaCarnetPage.

Public-frontend Page Object for PBI 129402 (QC-SVC-003 — ATA Carnet),
`/our-services/ata-carnet` (Arabic: `/ar/our-services/ata-carnet`).

URL NOTE (confirmed live 2026-09-16 with `curl -o /dev/null -w "%{http_code}
%{redirect_url}"`): the short paths handed off in the batch are redirects, not
the canonical page —
    /en/ata-carnet  -> 301 -> /our-services/ata-carnet
    /ata-carnet     -> 302 -> /our-services/ata-carnet
    /ar/ata-carnet  -> 301 -> /ar/our-services/ata-carnet
Both canonical URLs answer 200 and render identical markup to the redirect
sources. This Page Object therefore navigates straight to the canonical path
through `config.settings.web_url()` (which models the Arabic locale as the
`ARABIC_PATH_PREFIX` only, and has no `/en` concept), saving a redirect hop
per navigation. Nothing is hard-coded: the base URL still comes from
`WEB_BASE_URL`.

LOCATOR EXTRACTION — CLI-first, no MCP fallback was needed:

1. `python3 tools/extract_locators.py --url https://qcdev.ihorizons.com/en/ata-carnet --max 60`
   surfaced the interactive layer (header/footer/nav links plus this page's own
   controls), confirming the in-page anchors and CTAs are real `role=link`
   elements:
       get_by_role("link", name="01Overview") / "02Covered Items" /
       "03Eligible Items" / "04Member countries"   (sticky section index)
       get_by_role("link", name="Apply online")     (matches 2 — hero + banner)
       get_by_role("link", name="Verify ATA Carnet")(matches 2 — hero + banner)
   Because both CTAs legitimately render twice (hero and next-step banner),
   they are addressed here through their scoped container classes rather than
   by accessible name, which would be ambiguous (strict-mode violation).

2. The design-token cases address structural, non-interactive wrappers
   (hero, quick-facts strip, section index rows, category cards, fees table,
   next-step banner). The CLI extractor deliberately walks only
   `a,button,input,select,textarea,[role],[data-testid],[aria-label],
   [contenteditable]`, so those wrappers are out of its scope by design. They
   were confirmed — never guessed — with a scoped Playwright `evaluate()` DOM
   probe against the same live URLs at the framework default viewport
   (1920x1080), the same disclosed shell-script fallback already used by
   `chambers_law_page.py` and `org_structure_page.py`. The probe enumerated
   every `qc-*` class on the page and then read `getComputedStyle` +
   `getBoundingClientRect` per candidate. Confirmed structure:

       section.qc-ata-hero
         div.qc-ata-shell > div.qc-ata-hero-grid
           div.qc-ata-hero-copy
             nav.qc-ata-crumbs > a.qc-ata-crumb + span.qc-ata-crumb-sep
             span.qc-ata-eyebrow / h1.qc-ata-title / p.qc-ata-hero-desc
             div.qc-ata-hero-ctas > a.qc-ata-cta.qc-ata-cta-primary
                                    a.qc-ata-cta.qc-ata-cta-ghost
                                      (> span label + svg.qc-ata-cta-icon)
           div.qc-ata-hero-art > img.qc-ata-hero-img
         div.qc-ata-facts > div.qc-ata-fact
             span.qc-ata-fact-icon + div.qc-ata-fact-text
               (span.qc-ata-fact-label / span.qc-ata-fact-value)
       div.qc-ata-layout (grid: 280px 944px)
         aside.qc-ata-index-col > nav.qc-ata-index
           a.qc-ata-index-item > span.qc-ata-index-num + span.qc-ata-index-label
         div.qc-ata-content
           section.qc-ata-section[id=qc-ata-overview|covered|eligible|
                                     countries|fees|hours]
             div.qc-ata-section-head
               span.qc-ata-section-badge / h2.qc-ata-section-title
             div.qc-ata-rt                       (rich-text body)
             div.qc-ata-cards > article.qc-ata-card
               span.qc-ata-card-icon / h3.qc-ata-card-title / p.qc-ata-card-desc
             div.qc-ata-tiles > div.qc-ata-tile
             div.qc-ata-country-search > input.qc-ata-country-input
             div.qc-ata-country-grid > div.qc-ata-country
               span.qc-ata-country-flag + div.qc-ata-country-text
                 (span.qc-ata-country-name / span.qc-ata-country-note)
             div.qc-ata-status                    (live region, see below)
             div.qc-ata-fees
               div.qc-ata-fee-row(.qc-ata-fee-head)
                 div.qc-ata-fee-item + div.qc-ata-fee-amount x2
             div.qc-ata-hours > div.qc-ata-hour
               span.qc-ata-hour-badge / .qc-ata-hour-days / .qc-ata-hour-time
           div.qc-ata-nextstep
             div.qc-ata-nextstep-copy
               span.qc-ata-nextstep-eyebrow / h2.qc-ata-nextstep-heading
             div.qc-ata-nextstep-ctas > a.qc-ata-cta x2

LIVE BEHAVIOUR THAT SHAPES THIS OBJECT:
- The member-countries grid is CLIENT-RENDERED: `.qc-ata-status` holds a
  "Loading…" / "جارٍ التحميل…" live-region label and the `.qc-ata-country`
  tiles appear afterwards (18 tiles live). `open_ata_carnet()` therefore waits
  for the first country tile through the wrapper's explicit wait — never a
  sleep — so an Arabic-content assertion cannot read an empty grid.
- `.qc-ata-status` keeps a zero-size box once the grid has rendered, so its
  text must be read with `text_content()`; `inner_text()` returns "" for a
  non-rendered node. `country_status_text()` exists for exactly that reason.
- Both CTA pairs (hero + next-step banner) are structurally identical, so
  every CTA accessor takes the scope container as an argument instead of
  duplicating a near-identical locator per region.

This object exposes STATE ONLY (computed styles, boxes, texts, geometry) —
every comparison against the case's Figma-verified expected values lives in
the test module, per the Page-Object rules in automation-standards.md.
"""

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

ATA_CARNET_PATH = "/our-services/ata-carnet"


class AtaCarnetPage(BasePage):
    # ---- Global chrome (header / theme) --------------------------------------
    # Confirmed live 2026-09-24: the header toggle is an <a> that routes
    # through /c/portal/update_language and lands on the other locale's URL.
    PAGE_BODY = "body"
    HEADER = "header.qc-global-site-header"
    HEADER_NAV_LINK = "header.qc-global-site-header a.qc-nav-link"
    LANG_TOGGLE = "header.qc-global-site-header a.qc-lang-switcher"

    # ---- Hero ---------------------------------------------------------------
    HERO = ".qc-ata-hero"
    HERO_SHELL = ".qc-ata-hero .qc-ata-shell"
    HERO_GRID = ".qc-ata-hero-grid"
    HERO_COPY = ".qc-ata-hero-copy"
    HERO_ART = ".qc-ata-hero-art"
    HERO_EYEBROW = ".qc-ata-eyebrow"
    HERO_TITLE = ".qc-ata-title"
    HERO_DESC = ".qc-ata-hero-desc"
    HERO_IMG = ".qc-ata-hero-img"
    HERO_CTAS = ".qc-ata-hero-ctas"
    BREADCRUMBS = ".qc-ata-crumbs"
    CRUMB = ".qc-ata-crumb"

    # ---- Quick-facts strip ---------------------------------------------------
    FACTS_STRIP = ".qc-ata-facts"
    FACT = ".qc-ata-fact"
    FACT_ICON = ".qc-ata-fact-icon"
    FACT_LABEL = ".qc-ata-fact-label"
    FACT_VALUE = ".qc-ata-fact-value"

    # ---- Two-column layout: sticky index + content ---------------------------
    LAYOUT = ".qc-ata-layout"
    INDEX_COL = ".qc-ata-index-col"
    INDEX = ".qc-ata-index"
    INDEX_ITEM = ".qc-ata-index-item"
    INDEX_NUM = ".qc-ata-index-num"
    INDEX_LABEL = ".qc-ata-index-label"
    CONTENT = ".qc-ata-content"

    # ---- Sections ------------------------------------------------------------
    SECTION = ".qc-ata-section"
    SECTION_BADGE = ".qc-ata-section-badge"
    SECTION_TITLE = ".qc-ata-section-title"
    SECTION_BODY = ".qc-ata-rt"
    # Body copy inside the six content sections only — SECTION_BODY's first
    # match is the hero's own rich-text wrapper (confirmed live), which is
    # white-on-gradient and must not stand in for "body copy".
    SECTION_RT = ".qc-ata-section .qc-ata-rt"

    # ---- Covered Items: category cards ---------------------------------------
    CARDS = ".qc-ata-cards"
    CARD = ".qc-ata-card"
    CARD_ICON = ".qc-ata-card-icon"
    CARD_TITLE = ".qc-ata-card-title"
    CARD_DESC = ".qc-ata-card-desc"

    # ---- Eligible Items: tiles -----------------------------------------------
    TILES = ".qc-ata-tiles"
    TILE = ".qc-ata-tile"
    TILE_LABEL = ".qc-ata-tile-label"

    # ---- Member countries ----------------------------------------------------
    COUNTRY_GRID = ".qc-ata-country-grid"
    COUNTRY = ".qc-ata-country"
    COUNTRY_NAME = ".qc-ata-country-name"
    COUNTRY_NOTE = ".qc-ata-country-note"
    COUNTRY_STATUS = ".qc-ata-status"

    # ---- Fees table ----------------------------------------------------------
    FEES = ".qc-ata-fees"
    FEE_ROW = ".qc-ata-fee-row"
    FEE_HEAD = ".qc-ata-fee-head"
    FEE_BODY_ROW = ".qc-ata-fee-row:not(.qc-ata-fee-head)"
    FEE_ITEM = ".qc-ata-fee-item"
    FEE_AMOUNT = ".qc-ata-fee-amount"

    # ---- Operating hours -----------------------------------------------------
    HOURS = ".qc-ata-hours"
    HOUR = ".qc-ata-hour"
    HOUR_BADGE = ".qc-ata-hour-badge"

    # ---- Next-step banner ----------------------------------------------------
    NEXTSTEP = ".qc-ata-nextstep"
    NEXTSTEP_EYEBROW = ".qc-ata-nextstep-eyebrow"
    NEXTSTEP_HEADING = ".qc-ata-nextstep-heading"
    NEXTSTEP_CTAS = ".qc-ata-nextstep-ctas"

    # ---- CTAs (same markup in hero and banner — always scoped by caller) -----
    CTA = ".qc-ata-cta"
    CTA_PRIMARY = ".qc-ata-cta-primary"
    CTA_GHOST = ".qc-ata-cta-ghost"
    CTA_ICON = ".qc-ata-cta-icon"

    # ---- Navigation ----------------------------------------------------------
    def open_ata_carnet(self, locale: str = "en") -> "AtaCarnetPage":
        """Open the public ATA Carnet page in `locale` ('en'|'ar').

        Waits for the hero and for the client-rendered member-countries grid
        so that content assertions never race the fetch that populates it
        (see the module docstring's live-behaviour note). Both waits go
        through the BasePage wrapper's explicit waits — no sleep.
        """
        self.open(web_url(ATA_CARNET_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        self.wait_for(self.COUNTRY, first=True)
        return self

    def toggle_language(self) -> "AtaCarnetPage":
        """Click the header language toggle and wait until the browser has
        actually navigated (URL changed) and the other locale's content —
        hero title and client-rendered country grid — has rendered. Reading
        state right after click() would still see the previous locale."""
        before = self.page.url
        self.click(self.LANG_TOGGLE)
        self.wait_for_url(lambda url: url != before, timeout=20000)
        self.wait_for(self.HERO_TITLE)
        self.wait_for(self.COUNTRY, first=True)
        return self

    def enable_dark_mode(self) -> "AtaCarnetPage":
        AccessibilityToolsComponent(self.page).enable_dark_mode()
        return self

    def wait_for_fonts(self) -> "AtaCarnetPage":
        """Wait until every web font (Cairo) has finished loading, so box
        sizes read now match the final render — a late font swap otherwise
        changes text-driven widths between two measurements."""
        self.page.wait_for_function("() => document.fonts.status === 'loaded'", timeout=15000)
        return self

    def scroll_to(self, locator: str, index: int = 0) -> None:
        self.page.locator(locator).nth(index).scroll_into_view_if_needed()

    # ---- Generic state queries (no assertions — tests compare) ---------------
    def language_toggle_label(self) -> str:
        return self.text_of(self.LANG_TOGGLE)

    def theme(self):
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    def is_displayed(self, locator: str, index: int = 0) -> bool:
        """nth-match visibility (BasePage.is_visible targets a single match)."""
        return self.page.locator(locator).nth(index).is_visible()

    def section_in_view(self) -> str | None:
        """id of the first content section whose box intersects the viewport."""
        return self.page.evaluate(
            """(sel) => { const s = [...document.querySelectorAll(sel)].find((e) => {
                    const r = e.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; });
                return s ? s.id : null; }""",
            self.SECTION,
        )

    def boxes(self, locator: str) -> list:
        """box() for every match, plus whether each is actually rendered."""
        return self.page.locator(locator).evaluate_all(
            """
            (els) => els.map((el) => {
                const r = el.getBoundingClientRect();
                return {x: Math.round(r.x * 100) / 100, y: Math.round(r.y * 100) / 100,
                        width: Math.round(r.width * 100) / 100,
                        height: Math.round(r.height * 100) / 100,
                        visible: r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== "hidden"};
            })
            """
        )

    def computed_styles_all(self, locator: str, props: list) -> list:
        return self.page.locator(locator).evaluate_all(
            "(els, props) => els.map((el) => { const s = getComputedStyle(el); const o = {};"
            " for (const p of props) o[p] = s[p]; return o; })",
            props,
        )

    def horizontal_overflow_px(self) -> int:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )

    def overflowing_elements(self) -> list:
        """Up to 5 rendered elements whose right edge passes the viewport."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll("body *")]
                .filter((e) => { const r = e.getBoundingClientRect();
                    return r.width > 0 && r.right > innerWidth + 1 && getComputedStyle(e).visibility !== "hidden"; })
                .slice(0, 5).map((e) => e.tagName.toLowerCase() + "." + String(e.className).trim()
                    + " (right=" + Math.round(e.getBoundingClientRect().right) + "px)")"""
        )

    def clipped_text_elements(self) -> list:
        """Rendered leaf nodes inside the hero/content whose text overflows their box."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll(".qc-ata-hero *, .qc-ata-content *")]
                .filter((e) => e.offsetParent !== null && e.children.length === 0
                    && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== "visible")
                .map((e) => String(e.className) || e.tagName)"""
        )

    def text_contrast(self, locator: str, index: int = 0) -> dict:
        """WCAG contrast ratio of the nth match's text against the first
        solid background found walking up its ancestors (text alpha blended
        over it). ratio=None when a gradient/image background is reached
        first — that pairing is not measurable from computed styles."""
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el) => {
                const parse = (c) => { const m = c.match(/[0-9.]+/g) || [0, 0, 0, 0];
                    return [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1]; };
                const lum = (rgb) => { const f = (v) => { v /= 255;
                    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                    return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2]); };
                const s = getComputedStyle(el);
                let node = el, bg = null, blocker = null;
                while (node && node.nodeType === 1) {
                    const cs = getComputedStyle(node);
                    if (cs.backgroundImage && cs.backgroundImage !== "none") { blocker = cs.backgroundImage; break; }
                    const c = parse(cs.backgroundColor);
                    if (c[3] > 0) { bg = c; break; }
                    node = node.parentElement;
                }
                if (!bg && !blocker) bg = [255, 255, 255, 1];
                const fg = parse(s.color);
                const out = {color: s.color, fontSize: parseFloat(s.fontSize), fontWeight: +s.fontWeight,
                             text: (el.textContent || "").trim().slice(0, 40)};
                if (!bg) return Object.assign(out, {ratio: null, background: blocker});
                const a = fg[3];
                const mix = [0, 1, 2].map((i) => fg[i] * a + bg[i] * (1 - a));
                const l1 = lum(mix), l2 = lum(bg);
                const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
                return Object.assign(out, {ratio: Math.round(ratio * 100) / 100,
                                           background: "rgb(" + bg.slice(0, 3).join(", ") + ")"});
            }
            """
        )

    def relative_luminance(self, css_colour: str) -> float:
        return self.page.evaluate(
            """(c) => { const m = (c.match(/[0-9.]+/g) || [0, 0, 0]).map(Number);
                const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                return 0.2126 * f(m[0]) + 0.7152 * f(m[1]) + 0.0722 * f(m[2]); }""",
            css_colour,
        )

    def computed_style(self, locator: str, props: list, index: int = 0) -> dict:
        """getComputedStyle for `props` on the `index`-th match of `locator`."""
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el, props) => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = s[p];
                return out;
            }
            """,
            props,
        )

    def background_layers(self, locator: str) -> dict:
        """The element's own background-image plus those of its ::before /
        ::after pseudo-elements.

        A decorative wash (the case's radial rgba(196,154,98,0.18) overlay)
        is commonly painted on a pseudo-element rather than the element
        itself, so reading only `backgroundImage` would report a false
        absence. All three layers are returned and the test looks across
        them.
        """
        return self.page.locator(locator).first.evaluate(
            """
            (el) => ({
                element: getComputedStyle(el).backgroundImage,
                before: getComputedStyle(el, "::before").backgroundImage,
                after: getComputedStyle(el, "::after").backgroundImage,
            })
            """
        )

    def box(self, locator: str, index: int = 0) -> dict:
        """Rounded bounding box {x, y, width, height} of the index-th match."""
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el) => {
                const r = el.getBoundingClientRect();
                return {x: Math.round(r.x * 100) / 100,
                        y: Math.round(r.y * 100) / 100,
                        width: Math.round(r.width * 100) / 100,
                        height: Math.round(r.height * 100) / 100};
            }
            """
        )

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def text_of(self, locator: str, index: int = 0) -> str:
        return self.page.locator(locator).nth(index).inner_text().strip()

    def texts_of(self, locator: str) -> list:
        """Every match's text, via text_content() so that nodes which are
        present but not rendered (the countries live region) are still read —
        all_inner_texts() returns '' for those."""
        return [t.strip() for t in self.page.locator(locator).all_text_contents()]

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def document_language(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('lang')")

    def resolved_text_align(self, locator: str, index: int = 0) -> str:
        """Computed `text-align` resolved to a physical side.

        CSS `start`/`end` are logical values: with `direction: rtl`, `start`
        IS the right edge. Returning the physical side lets a test assert
        "left-aligned" / "right-aligned" the way the QA case words it,
        without the test having to re-derive the logical->physical mapping
        (and without a false red on a page that correctly uses logical
        properties — both locales of this page do).
        """
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el) => {
                const s = getComputedStyle(el);
                const rtl = s.direction === "rtl";
                const a = s.textAlign;
                if (a === "start") return rtl ? "right" : "left";
                if (a === "end") return rtl ? "left" : "right";
                return a;
            }
            """
        )

    # ---- Hero ---------------------------------------------------------------
    def hero_content_inset(self) -> dict:
        """Gap in px between the full-bleed hero band and its content shell,
        on each side.

        The case states the hero's padding as "40px/300px". That inset can be
        produced either by real padding on the band or by a centred
        max-width wrapper, and the rendered result is identical — so the
        mechanism-agnostic measured inset is what this returns, rather than
        the `padding` declaration alone (which would report 0 for a correct
        centred-wrapper implementation). The raw `padding` is still available
        through `computed_style(HERO, ["padding"])` when a test wants both.

        Measured against `.qc-ata-shell`, the hero's own content wrapper —
        NOT against `.qc-ata-hero-grid`. Confirmed live: the shell stacks
        three blocks (`.qc-ata-crumbs`, then `.qc-ata-hero-grid`, then
        `.qc-ata-facts`), so a hero->grid measurement would silently fold the
        breadcrumb row and the gap beneath it into the reported "top
        padding" (67.5px instead of the band's real 20px) and would report
        the quick-facts strip as bottom padding.
        """
        return self.page.evaluate(
            """
            ([heroSel, innerSel]) => {
                const hero = document.querySelector(heroSel).getBoundingClientRect();
                const inner = document.querySelector(innerSel).getBoundingClientRect();
                return {
                    top: Math.round((inner.top - hero.top) * 100) / 100,
                    left: Math.round((inner.left - hero.left) * 100) / 100,
                    right: Math.round((hero.right - inner.right) * 100) / 100,
                    bottom: Math.round((hero.bottom - inner.bottom) * 100) / 100,
                };
            }
            """,
            [self.HERO, self.HERO_SHELL],
        )

    # ---- Section index / content column --------------------------------------
    def index_labels(self) -> list:
        return self.texts_of(self.INDEX_LABEL)

    def index_numbers(self) -> list:
        return self.texts_of(self.INDEX_NUM)

    # ---- Sections -------------------------------------------------------------
    def section_badges(self) -> list:
        return self.texts_of(self.SECTION_BADGE)

    def section_titles(self) -> list:
        return self.texts_of(self.SECTION_TITLE)

    def section_bodies(self) -> list:
        return self.texts_of(self.SECTION_BODY)

    def card_titles(self) -> list:
        return self.texts_of(self.CARD_TITLE)

    # ---- Member countries ------------------------------------------------------
    def country_names(self) -> list:
        return self.texts_of(self.COUNTRY_NAME)

    def country_notes(self) -> list:
        return self.texts_of(self.COUNTRY_NOTE)

    def country_status_text(self) -> str:
        """text_content() (not inner_text) — the live region keeps a
        zero-size box after the grid renders, and inner_text() returns ''
        for a node the browser does not lay out."""
        return (self.page.locator(self.COUNTRY_STATUS).first.text_content() or "").strip()

    # ---- Fees table -------------------------------------------------------------
    def fee_item_texts(self) -> list:
        return self.texts_of(self.FEE_ITEM)

    def fee_row_cells(self, row_index: int = 0, head: bool = False) -> list:
        """[{class, x, width, text}] for one fee row's cells, in DOM order.

        The x positions are what a mirroring assertion needs: the same DOM
        order paints left-to-right in English and right-to-left in Arabic,
        so comparing the cells' x values proves the columns actually
        mirrored rather than merely being present.
        """
        selector = self.FEE_HEAD if head else self.FEE_BODY_ROW
        return self.page.locator(selector).nth(row_index).evaluate(
            """
            (row) => Array.from(row.children).map((c) => {
                const r = c.getBoundingClientRect();
                return {class: c.className,
                        x: Math.round(r.x * 100) / 100,
                        width: Math.round(r.width * 100) / 100,
                        text: (c.textContent || "").trim()};
            })
            """
        )

    # ---- Operating hours ---------------------------------------------------------
    def hour_badge_texts(self) -> list:
        return self.texts_of(self.HOUR_BADGE)

    # ---- CTAs ---------------------------------------------------------------------
    def cta_icon_side(self, scope: str, index: int = 0) -> str:
        """Which physical edge of the CTA its arrow icon sits on, resolved to
        the case's own wording: 'leading' / 'trailing' / 'none'.

        Leading = the edge text starts from (left in LTR, right in RTL), so
        the same method answers the English and Arabic cases without the
        test re-deriving direction.
        """
        return self.page.locator(f"{scope} {self.CTA}").nth(index).evaluate(
            """
            (cta, iconSel) => {
                const icon = cta.querySelector(iconSel);
                if (!icon) return "none";
                const c = cta.getBoundingClientRect();
                const i = icon.getBoundingClientRect();
                const iconOnLeft = (i.left + i.width / 2) < (c.left + c.width / 2);
                const rtl = getComputedStyle(cta).direction === "rtl";
                if (rtl) return iconOnLeft ? "trailing" : "leading";
                return iconOnLeft ? "leading" : "trailing";
            }
            """,
            self.CTA_ICON,
        )

    def cta_texts(self, scope: str) -> list:
        return self.texts_of(f"{scope} {self.CTA}")

    def cta_count(self, scope: str) -> int:
        """How many CTAs render inside `scope` (HERO_CTAS / NEXTSTEP_CTAS).

        Exists so a test never has to compose the scoped selector itself —
        the CTA markup is shared between the hero and the banner, so the
        scope+CTA join belongs here with the locators, not at a call site.
        """
        return self.count(f"{scope} {self.CTA}")

    def cta_boxes(self, scope: str) -> list:
        """boxes() of the CTAs inside `scope` (HERO_CTAS / NEXTSTEP_CTAS)."""
        return self.boxes(f"{scope} {self.CTA}")

    def child_box(self, parent: str, child: str, index: int = 0) -> dict:
        """box() of the first `child` inside the index-th `parent` (card
        icon/title/desc, hour badge) — keeps the selector join here."""
        return self.page.locator(parent).nth(index).locator(child).first.evaluate(
            """
            (el) => { const r = el.getBoundingClientRect();
                return {x: Math.round(r.x * 100) / 100, y: Math.round(r.y * 100) / 100,
                        width: Math.round(r.width * 100) / 100, height: Math.round(r.height * 100) / 100}; }
            """
        )

    def cta_style(self, scope: str, props: list, index: int = 0) -> dict:
        return self.computed_style(f"{scope} {self.CTA}", props, index=index)

    # ---- Page-level typography -----------------------------------------------
    def body_font_family(self) -> str:
        """Computed font-family of <body> — the "font family Cairo
        throughout" baseline both locale cases open with."""
        return self.page.evaluate("() => getComputedStyle(document.body).fontFamily")

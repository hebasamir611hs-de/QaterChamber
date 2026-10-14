"""
web/pages/certificate_of_origin/certificate_of_origin_page.py —
CertificateOfOriginPage.

Public-frontend Page Object for PBI 130947 (QC-SVC-005 — Certificate of
Origin Online), `/our-services/certificate-of-origin-online` (Arabic:
`/ar/our-services/certificate-of-origin-online`) — the canonical,
redirect-free paths, verified live. Every URL is built through
`config.settings.web_url()` — no hard-coded host, no hard-coded locale
prefix.

LOCATOR PROVENANCE — CLI-first, no guessed selectors
----------------------------------------------------
1) `python3 tools/extract_locators.py --url
   https://qcdev.ihorizons.com/en/certificate-of-origin-online --max 80`
   (framework default viewport 1920x1080) surfaced the interactive layer:

     get_by_role("link",   name="Certificate of Origin (PDF)")      uniq=1
     get_by_role("link",   name="Download")                         uniq=1
     get_by_role("button", name="Accessibility tools")              uniq=1
     get_by_role("link",   name="Login to COO")                     uniq=2  (hero + banner)
     get_by_role("link",   name="Verify Certificate")               uniq=2  (hero + banner)
     #main-content, #qc-coo-finder-certificateType/productType/exportDestination

   The two hero CTAs are NON-unique by role (the same pair repeats in the
   next-step banner), so they are addressed through their scoped container
   (`.qc-coo-hero-ctas` / `.qc-coo-banner-ctas`) rather than by role, per
   the locator-priority rule "scoped CSS, short and semantic".

2) The page's text/structural layer (hero copy, quick-facts strip, sticky
   index, section badges/headings/intros, info cards, accordion, steps,
   download card, banner) is built from `<p>/<span>/<div>/<h2>/<h3>/<li>`
   elements with no interactive role, which the CLI harvester deliberately
   does not walk. It was therefore confirmed by a scoped DOM probe against
   the same live page at the same viewport (same disclosed fallback pattern
   as `chambers_law_page.py` — a plain Playwright script, NOT the MCP), which
   printed the live `qc-coo-*` class tree:

     section.qc-coo > header.qc-coo-hero
       nav.qc-coo-crumbs > a.qc-coo-crumb
       .qc-coo-hero-grid > .qc-coo-hero-copy
         p.qc-coo-eyebrow / h1.qc-coo-title / .qc-coo-hero-desc
         .qc-coo-hero-ctas > .qc-coo-cta-row > a.qc-coo-cta (x2)
       .qc-coo-facts > .qc-coo-fact (x4)
         span.qc-coo-fact-label + span.qc-coo-fact-value
     .qc-coo-body > .qc-coo-layout
       aside.qc-coo-index-col (position: sticky) > nav.qc-coo-index
         a.qc-coo-index-item[href="#<section id>"][data-qc-coo-index-key]
           span.qc-coo-index-num + span.qc-coo-index-label
           active state = class `is-active` on the <a>
       .qc-coo-content > section.qc-coo-section (ids below)
         .qc-coo-section-head > .qc-coo-section-heading
           span.qc-coo-section-badge + h2.qc-coo-section-title
         .qc-coo-intro
         .qc-coo-cards > article.qc-coo-card
           h3.qc-coo-card-title + .qc-coo-card-desc
         a.qc-coo-pdf-btn
         .qc-coo-accordion > .qc-coo-acc-item (class `is-open` when expanded)
           button.qc-coo-acc-q[aria-expanded]
             span.qc-coo-acc-title + span.qc-coo-acc-sub
           .qc-coo-acc-a   (the expanded answer body)
         ol.qc-coo-steps > li.qc-coo-step
           span.qc-coo-step-num + h3.qc-coo-step-title + .qc-coo-step-desc
         .qc-coo-download
           span.qc-coo-download-title + span.qc-coo-download-sub
           a.qc-coo-download-btn
       .qc-coo-banner
         span.qc-coo-banner-eyebrow + h2.qc-coo-banner-title
         .qc-coo-banner-body + .qc-coo-banner-ctas > a.qc-coo-cta (x2)

   Live section ids, in DOM order: `qc-coo-overview`, `qc-coo-documents`,
   `qc-coo-apply`, `qc-coo-finder`.

3) Dark mode IS reachable without CMS access on this build (unlike the
   Chamber's Law page, where no toggle existed at the time), through the
   site's accessibility widget. That widget is site-wide, not COO-specific,
   so its three locators and the toggle flow now live in
   `web/pages/components/accessibility_tools_component.py` (their full
   extraction provenance is documented there) and this Page Object composes
   the component in as `self.accessibility_tools` rather than declaring them
   again. `enable_dark_mode()` below simply delegates.

LIVE-ENV NOTES (observed, not assumed)
--------------------------------------
- `wait_until="networkidle"` is unusable on this page: the chat widget and
  reCAPTCHA keep polling, and a networkidle wait times out at 30s. The
  wrapper's plain `goto` + an explicit element wait is used instead.
- The announcement overlay / license interstitial are handled globally by
  `BasePage.open()` (core/web/overlays.py, core/web/license_gate.py) — this
  Page Object adds no per-page dismissal of its own.
- The live page renders FOUR index entries and FOUR sections
  (04 "Documents Finder" is live), while PBI 130947 scopes only three. That
  is a product/scope observation reported to the QA Manager; the affected
  test asserts the case's expected three and is expected to fail honestly
  rather than being narrowed to match the build.
"""

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import (
    AccessibilityToolsComponent,
)

# Canonical, redirect-free path (verified live): the shorter
# `/certificate-of-origin-online` answers HTTP 302 -> this path, and the
# Arabic page is the same path under ARABIC_PATH_PREFIX. `web_url()` models
# Arabic through that prefix and has no `/en` concept, so the English call
# correctly takes no prefix at all.
COO_PATH = "/our-services/certificate-of-origin-online"

# Live section ids, in DOM order (confirmed by DOM probe).
SECTION_OVERVIEW = "qc-coo-overview"
SECTION_DOCUMENTS = "qc-coo-documents"
SECTION_APPLY = "qc-coo-apply"


class CertificateOfOriginPage(BasePage):
    # ---- Root / hero -------------------------------------------------------
    ROOT = ".qc-coo"
    HERO = ".qc-coo-hero"
    HERO_COPY = ".qc-coo-hero-copy"
    HERO_EYEBROW = ".qc-coo-eyebrow"
    HERO_TITLE = ".qc-coo-title"
    HERO_DESC = ".qc-coo-hero-desc"
    HERO_CTAS = ".qc-coo-hero-ctas"
    HERO_CTA = ".qc-coo-hero-ctas .qc-coo-cta"

    # ---- Quick-facts strip --------------------------------------------------
    FACTS = ".qc-coo-facts"
    FACT = ".qc-coo-fact"
    FACT_LABEL = ".qc-coo-fact-label"
    FACT_VALUE = ".qc-coo-fact-value"

    # ---- Sticky section index ------------------------------------------------
    INDEX_COL = ".qc-coo-index-col"
    INDEX = ".qc-coo-index"
    INDEX_ITEM = ".qc-coo-index-item"
    INDEX_ITEM_ACTIVE = ".qc-coo-index-item.is-active"
    INDEX_NUM = ".qc-coo-index-num"
    INDEX_LABEL = ".qc-coo-index-label"

    # ---- Content column / sections ---------------------------------------------
    CONTENT = ".qc-coo-content"
    SECTION = ".qc-coo-section"
    SECTION_BADGE = ".qc-coo-section-badge"
    SECTION_TITLE = ".qc-coo-section-title"
    SECTION_INTRO = ".qc-coo-intro"

    # ---- Overview info cards -----------------------------------------------------
    CARDS = ".qc-coo-cards"
    CARD = ".qc-coo-card"
    CARD_TITLE = ".qc-coo-card-title"
    CARD_DESC = ".qc-coo-card-desc"

    # ---- Documents Required ------------------------------------------------------
    PDF_BUTTON = ".qc-coo-pdf-btn"
    ACCORDION = ".qc-coo-accordion"
    ACC_ITEM = ".qc-coo-acc-item"
    ACC_QUESTION = ".qc-coo-acc-q"
    ACC_TITLE = ".qc-coo-acc-title"
    ACC_SUBTITLE = ".qc-coo-acc-sub"
    ACC_ANSWER = ".qc-coo-acc-a"

    # ---- How to Apply steps --------------------------------------------------------
    STEPS = ".qc-coo-steps"
    STEP = ".qc-coo-step"
    STEP_NUM = ".qc-coo-step-num"
    STEP_TITLE = ".qc-coo-step-title"
    STEP_DESC = ".qc-coo-step-desc"

    # ---- Download-the-form card ------------------------------------------------------
    DOWNLOAD_CARD = ".qc-coo-download"
    DOWNLOAD_TITLE = ".qc-coo-download-title"
    DOWNLOAD_SUBTITLE = ".qc-coo-download-sub"
    DOWNLOAD_BUTTON = ".qc-coo-download-btn"

    # ---- Next-step banner ---------------------------------------------------------------
    BANNER = ".qc-coo-banner"
    BANNER_EYEBROW = ".qc-coo-banner-eyebrow"
    BANNER_TITLE = ".qc-coo-banner-title"
    BANNER_BODY = ".qc-coo-banner-body"
    BANNER_CTA = ".qc-coo-banner-ctas .qc-coo-cta"

    def __init__(self, page):
        super().__init__(page)
        self._console_errors = []
        # Site-wide accessibility widget (dark mode lives there) — composed
        # in, not duplicated. See accessibility_tools_component.py.
        self.accessibility_tools = AccessibilityToolsComponent(page)

    # ---- Navigation ------------------------------------------------------------------------
    def open_coo(self, locale: str = "en") -> "CertificateOfOriginPage":
        self.open(web_url(COO_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    # ---- Console diagnostics ------------------------------------------------------------------
    def start_console_capture(self) -> "CertificateOfOriginPage":
        """Must be called BEFORE open_coo() — Playwright only reports console
        output emitted after the listener is attached. Collects both
        `console.error` entries and uncaught page exceptions, which is what
        the case means by 'no console error'."""
        self._console_errors = []
        self.page.on(
            "console",
            lambda msg: self._console_errors.append(
                f"{msg.type}: {msg.text} [{(msg.location or {}).get('url', '')}]"
            )
            if msg.type == "error"
            else None,
        )
        self.page.on(
            "pageerror",
            lambda err: self._console_errors.append(f"pageerror: {err}"),
        )
        return self

    def console_errors(self) -> list:
        return list(self._console_errors)

    # ---- Document-level state -----------------------------------------------------------------
    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def document_lang(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('lang')")

    def theme(self) -> str:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('data-theme')"
        )

    def has_horizontal_scrollbar(self) -> bool:
        scroll_width = self.page.evaluate("() => document.documentElement.scrollWidth")
        client_width = self.page.evaluate("() => document.documentElement.clientWidth")
        return scroll_width > client_width + 1

    # ---- Style / geometry probes ------------------------------------------------------------------
    def computed_style(self, locator: str, props: list, index: int = 0) -> dict:
        """getComputedStyle for one element. `props` are camelCase CSS
        property names (e.g. 'fontFamily', 'lineHeight')."""
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

    def computed_styles_all(self, locator: str, props: list) -> list:
        return self.page.locator(locator).evaluate_all(
            """
            (els, props) => els.map(el => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = s[p];
                return out;
            })
            """,
            props,
        )

    def effective_text_align(self, locator: str, index: int = 0) -> str:
        """Resolves the CSS logical values `start`/`end` against the element's
        own computed `direction`, so an LTR 'start' reads as 'left' and an RTL
        'start' reads as 'right'. The live page sets `text-align: start`
        everywhere; without this resolution a left/right-alignment assertion
        would compare against a value the browser never reports."""
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el) => {
                const s = getComputedStyle(el);
                const rtl = s.direction === 'rtl';
                const map = {start: rtl ? 'right' : 'left', end: rtl ? 'left' : 'right'};
                return map[s.textAlign] || s.textAlign;
            }
            """
        )

    def element_box(self, locator: str, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).bounding_box()

    def is_text_clipped(self, locator: str, index: int = 0) -> bool:
        """True when the element's content overflows its own box horizontally
        (the render-level definition of clipped text)."""
        return self.page.locator(locator).nth(index).evaluate(
            "(el) => el.scrollWidth > el.clientWidth + 1"
        )

    def hero_overflows_container(self) -> bool:
        return self.page.locator(self.HERO).first.evaluate(
            "(el) => el.scrollHeight > el.clientHeight + 1"
        )

    # ---- Hero ----------------------------------------------------------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW).strip()

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_description_text(self) -> str:
        return self.text(self.HERO_DESC).strip()

    def hero_cta_count(self) -> int:
        return self.page.locator(self.HERO_CTA).count()

    def hero_cta_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.HERO_CTA).all_inner_texts()]

    # ---- Quick facts ---------------------------------------------------------------------------------
    def fact_count(self) -> int:
        return self.page.locator(self.FACT).count()

    def fact_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.FACT_LABEL).all_inner_texts()]

    def fact_values(self) -> list:
        return [t.strip() for t in self.page.locator(self.FACT_VALUE).all_inner_texts()]

    def fact_pairs(self) -> list:
        """[(label, value), ...] read left to right in DOM order."""
        return list(zip(self.fact_labels(), self.fact_values()))

    # ---- Sticky index ---------------------------------------------------------------------------------
    def is_index_visible(self) -> bool:
        return self.is_visible(self.INDEX)

    def index_count(self) -> int:
        return self.page.locator(self.INDEX_ITEM).count()

    def index_numerals(self) -> list:
        return [t.strip() for t in self.page.locator(self.INDEX_NUM).all_inner_texts()]

    def index_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.INDEX_LABEL).all_inner_texts()]

    def index_entries(self) -> list:
        """['01 Overview', '02 Documents Required', ...] — numeral and label
        joined with a single space, the reading order the case states them in."""
        return [
            f"{num} {label}"
            for num, label in zip(self.index_numerals(), self.index_labels())
        ]

    def index_column_position(self) -> str:
        return self.computed_style(self.INDEX_COL, ["position"])["position"]

    def active_index_label(self) -> str:
        loc = self.page.locator(self.INDEX_ITEM_ACTIVE)
        if loc.count() == 0:
            return ""
        return loc.first.locator(self.INDEX_LABEL).inner_text().strip()

    def active_index_href(self) -> str:
        loc = self.page.locator(self.INDEX_ITEM_ACTIVE)
        if loc.count() == 0:
            return ""
        return loc.first.get_attribute("href") or ""

    def index_top(self) -> float:
        return self.element_box(self.INDEX)["y"]

    def scroll_section_to_viewport_top(self, section_id: str) -> None:
        """Scrolls so the named section's top edge sits at the top of the
        viewport, then waits — with no sleep — until (a) the window has
        actually settled at that offset and (b) three animation frames have
        elapsed, which is what guarantees the page's scroll-spy handler (and
        any IntersectionObserver delivery) has run for the new position
        before the index is read."""
        self.page.evaluate(
            """
            (id) => {
                const el = document.getElementById(id);
                window.scrollTo({top: el.getBoundingClientRect().top + window.scrollY,
                                 behavior: 'instant'});
            }
            """,
            section_id,
        )
        self.page.wait_for_function(
            """
            (id) => Math.abs(document.getElementById(id).getBoundingClientRect().top) <= 2
            """,
            arg=section_id,
        )
        self.page.evaluate(
            """
            () => new Promise(resolve => {
                requestAnimationFrame(() =>
                    requestAnimationFrame(() =>
                        requestAnimationFrame(() => resolve(true))));
            })
            """
        )

    # ---- Sections (by live section id) -------------------------------------------------------------------
    def _section(self, section_id: str) -> str:
        return f"#{section_id}"

    def section_exists(self, section_id: str) -> bool:
        return self.page.locator(self._section(section_id)).count() > 0

    def section_badge_selector(self, section_id: str) -> str:
        return f"{self._section(section_id)} {self.SECTION_BADGE}"

    def section_title_selector(self, section_id: str) -> str:
        return f"{self._section(section_id)} {self.SECTION_TITLE}"

    def section_intro_selector(self, section_id: str) -> str:
        return f"{self._section(section_id)} {self.SECTION_INTRO}"

    def section_badge_text(self, section_id: str) -> str:
        return self.text(self.section_badge_selector(section_id)).strip()

    def section_title_text(self, section_id: str) -> str:
        return self.text(self.section_title_selector(section_id)).strip()

    def section_intro_text(self, section_id: str) -> str:
        return self.text(self.section_intro_selector(section_id)).strip()

    def scroll_section_into_view(self, section_id: str) -> None:
        self.page.locator(self._section(section_id)).scroll_into_view_if_needed()

    def gap_between_sections(self, first_id: str, second_id: str) -> float:
        """Vertical distance in px between the bottom of one section and the
        top of the next — 0 means they are flush with no blank band."""
        return self.page.evaluate(
            """
            ([a, b]) => {
                const first = document.getElementById(a).getBoundingClientRect();
                const second = document.getElementById(b).getBoundingClientRect();
                return second.top - first.bottom;
            }
            """,
            [first_id, second_id],
        )

    # ---- Overview info cards -------------------------------------------------------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return [t.strip() for t in self.page.locator(self.CARD_TITLE).all_inner_texts()]

    def card_descriptions(self) -> list:
        return [t.strip() for t in self.page.locator(self.CARD_DESC).all_inner_texts()]

    def card_boxes(self) -> list:
        return self.page.locator(self.CARD).evaluate_all(
            "els => els.map(e => { const r = e.getBoundingClientRect();"
            "  return {x: r.x, y: r.y, width: r.width, height: r.height}; })"
        )

    # ---- Documents Required --------------------------------------------------------------------------------
    def pdf_button_label(self) -> str:
        return self.text(self.PDF_BUTTON).strip()

    def is_pdf_button_visible(self) -> bool:
        return self.is_visible(self.PDF_BUTTON)

    def is_accordion_visible(self) -> bool:
        return self.is_visible(self.ACCORDION)

    def accordion_item_count(self) -> int:
        return self.page.locator(self.ACC_ITEM).count()

    def _accordion_item(self, title: str):
        return self.page.locator(
            f'{self.ACC_ITEM}:has({self.ACC_TITLE}:text-is("{title}"))'
        ).first

    def expand_accordion_item(self, title: str) -> None:
        """Clicks the item's question button and waits for the item to report
        expanded (`aria-expanded="true"`) — the product's own state signal,
        not a timer."""
        item = self._accordion_item(title)
        question = item.locator(self.ACC_QUESTION)
        if question.get_attribute("aria-expanded") != "true":
            question.click()
        self.page.wait_for_function(
            """
            (title) => {
                const items = [...document.querySelectorAll('.qc-coo-acc-item')];
                const item = items.find(i => (i.querySelector('.qc-coo-acc-title')
                    || {}).textContent.trim() === title);
                if (!item) return false;
                const q = item.querySelector('.qc-coo-acc-q');
                return q && q.getAttribute('aria-expanded') === 'true';
            }
            """,
            arg=title,
        )

    def is_accordion_item_expanded(self, title: str) -> bool:
        item = self._accordion_item(title)
        return item.locator(self.ACC_QUESTION).get_attribute("aria-expanded") == "true"

    def accordion_item_title_selector(self, title: str) -> str:
        return f'{self.ACC_ITEM}:has({self.ACC_TITLE}:text-is("{title}")) {self.ACC_TITLE}'

    def accordion_item_subtitle_selector(self, title: str) -> str:
        return f'{self.ACC_ITEM}:has({self.ACC_TITLE}:text-is("{title}")) {self.ACC_SUBTITLE}'

    def accordion_item_answer_selector(self, title: str) -> str:
        return f'{self.ACC_ITEM}:has({self.ACC_TITLE}:text-is("{title}")) {self.ACC_ANSWER}'

    def accordion_item_title_text(self, title: str) -> str:
        return self._accordion_item(title).locator(self.ACC_TITLE).inner_text().strip()

    def accordion_item_subtitle_text(self, title: str) -> str:
        return self._accordion_item(title).locator(self.ACC_SUBTITLE).inner_text().strip()

    def accordion_item_answer_text(self, title: str) -> str:
        return self._accordion_item(title).locator(self.ACC_ANSWER).inner_text().strip()

    # ---- How to Apply steps ---------------------------------------------------------------------------------
    def step_count(self) -> int:
        return self.page.locator(self.STEP).count()

    def step_numerals(self) -> list:
        return [t.strip() for t in self.page.locator(self.STEP_NUM).all_inner_texts()]

    def step_titles(self) -> list:
        return [t.strip() for t in self.page.locator(self.STEP_TITLE).all_inner_texts()]

    def step_descriptions(self) -> list:
        return [t.strip() for t in self.page.locator(self.STEP_DESC).all_inner_texts()]

    def step_boxes(self) -> list:
        return self.page.locator(self.STEP).evaluate_all(
            "els => els.map(e => { const r = e.getBoundingClientRect();"
            "  return {x: r.x, y: r.y + window.scrollY, width: r.width,"
            "          height: r.height}; })"
        )

    # ---- Download-the-form card ---------------------------------------------------------------------------------
    def is_download_card_visible(self) -> bool:
        return self.is_visible(self.DOWNLOAD_CARD)

    def download_card_title(self) -> str:
        return self.text(self.DOWNLOAD_TITLE).strip()

    def download_card_subtitle(self) -> str:
        return self.text(self.DOWNLOAD_SUBTITLE).strip()

    def download_button_label(self) -> str:
        return self.text(self.DOWNLOAD_BUTTON).strip()

    def download_card_top(self) -> float:
        return self.page.locator(self.DOWNLOAD_CARD).first.evaluate(
            "el => el.getBoundingClientRect().top + window.scrollY"
        )

    def last_step_bottom(self) -> float:
        return self.page.locator(self.STEP).last.evaluate(
            "el => el.getBoundingClientRect().bottom + window.scrollY"
        )

    # ---- Next-step banner -----------------------------------------------------------------------------------------
    def is_banner_visible(self) -> bool:
        return self.is_visible(self.BANNER)

    def banner_eyebrow_text(self) -> str:
        return self.text(self.BANNER_EYEBROW).strip()

    def banner_title_text(self) -> str:
        return self.text(self.BANNER_TITLE).strip()

    def banner_body_text(self) -> str:
        return self.text(self.BANNER_BODY).strip()

    def banner_cta_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.BANNER_CTA).all_inner_texts()]

    def banner_background_color(self) -> str:
        return self.computed_style(self.BANNER, ["backgroundColor"])["backgroundColor"]

    def banner_surface_colors(self) -> list:
        """Every fully-opaque colour actually painted behind the banner copy,
        as 'rgb(r, g, b)' strings.

        Reading `backgroundColor` alone is not enough here and would be a
        false-green trap: the live build paints the banner with
        `linear-gradient(105deg, rgb(74, 10, 34) 0%, rgb(109, 16, 41) ...)` —
        a background-IMAGE — so `backgroundColor` computes to
        `rgba(0, 0, 0, 0)`, and a "is it dark?" check against that transparent
        value would pass because it parses as black, not because anything dark
        is rendered. This collects the stops from both `background-color` and
        `background-image` and discards fully-transparent entries, so the
        caller asserts against the colours a user actually sees."""
        return self.page.locator(self.BANNER).first.evaluate(
            """
            (el) => {
                const s = getComputedStyle(el);
                const source = `${s.backgroundColor} ${s.backgroundImage}`;
                const out = [];
                const re = /rgba?\\(([^)]+)\\)/g;
                let m;
                while ((m = re.exec(source)) !== null) {
                    const parts = m[1].split(/[,/]/).map(v => parseFloat(v.trim()));
                    const alpha = parts.length > 3 ? parts[3] : 1;
                    if (alpha > 0) {
                        out.push(`rgb(${parts[0]}, ${parts[1]}, ${parts[2]})`);
                    }
                }
                return out;
            }
            """
        )

    def scroll_to_banner(self) -> None:
        self.page.locator(self.BANNER).first.scroll_into_view_if_needed()

    # ---- Site accessibility widget: dark mode -------------------------------------------------------------------------
    def enable_dark_mode(self) -> "CertificateOfOriginPage":
        """Switches the site theme to Dark through the shared accessibility
        widget (see accessibility_tools_component.py) and returns this page so
        the caller keeps its fluent chain."""
        self.accessibility_tools.enable_dark_mode()
        return self

    def is_dark_mode_switch_checked(self) -> bool:
        return self.accessibility_tools.is_dark_mode_switch_checked()

    # ---- 2026-10-07 additions (suite 140380 functional / compatibility cases) -------------------------------
    # Composed only from existing locators and the shared components' public
    # methods (no shared file edited). The language switcher is the header's own
    # `a.qc-lang-switcher` (HeaderComponent.LANGUAGE_SWITCHER), switched with the
    # same wait-on-URL-then-html[lang] pattern ProposalForResearchPage uses.
    LANGUAGE_SWITCHER = "header.qc-global-site-header a.qc-lang-switcher"
    ACC_MARK = ".qc-coo-acc-mark"
    BODY = ".qc-coo-body"
    LAYOUT = ".qc-coo-layout"
    FOOTER = ".qc-global-site-footer"

    def low_contrast_text(self, scope: str = ".qc-coo", normal: float = 4.5, large: float = 3.0) -> list:
        """Visible leaf text under `normal` (or `large`) contrast against the nearest
        opaque background (same algorithm as SectoralCommitteesPage.low_contrast_text)."""
        return self.page.evaluate(
            """([s, NORMAL, LARGE]) => { const parse = c => { const m = c.match(/[0-9.]+/g) || [0,0,0,0]; return [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1]; };
                const lum = r => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                                   return 0.2126 * f(r[0]) + 0.7152 * f(r[1]) + 0.0722 * f(r[2]); };
                const out = [];
                document.querySelectorAll(s + ', ' + s + ' *').forEach(e => {
                    if (!e.offsetParent || e.closest('[aria-hidden="true"], .qc-coo-hero, .qc-coo-banner')) return;
                    const t = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim(); if (!t) return;
                    let n = e, bg = null; while (n && n.nodeType === 1) { const c = parse(getComputedStyle(n).backgroundColor); if (c[3] > 0) { bg = c; break; } n = n.parentElement; }
                    bg = bg || [255, 255, 255, 1]; const st = getComputedStyle(e), fg = parse(st.color), a = fg[3] * parseFloat(st.opacity || 1);
                    const mix = [0, 1, 2].map(i => fg[i] * a + bg[i] * (1 - a)); const l1 = lum(mix), l2 = lum(bg);
                    const r = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
                    const big = parseFloat(st.fontSize) >= 24 || (parseFloat(st.fontSize) >= 18.66 && +st.fontWeight >= 700);
                    if (r < (big ? LARGE : NORMAL)) out.push(String(e.className).split(' ')[0] + " '" + t.slice(0, 25) + "' = " + Math.round(r * 100) / 100);
                }); return out; }""", [scope, normal, large])

    def disable_dark_mode(self) -> "CertificateOfOriginPage":
        """Dark -> Light through the same widget: the Dark Mode switch is a
        toggle, so it is clicked only while checked, then the wait is on
        `<html data-theme>` leaving 'dark'."""
        tools = self.accessibility_tools
        tools.click_accessibility_button()
        self.wait_for(tools.PANEL)
        if tools.is_dark_mode_switch_checked():
            tools.switch_to_dark_mode()
        self.page.wait_for_function("() => document.documentElement.getAttribute('data-theme') !== 'dark'")
        tools.close_panel()
        return self

    def reload_coo(self) -> "CertificateOfOriginPage":
        self.page.reload(wait_until="domcontentloaded")
        self.wait_for(self.HERO_TITLE)
        return self

    def language_switcher_label(self) -> str:
        return self.page.locator(self.LANGUAGE_SWITCHER).first.inner_text().strip()

    def switch_language(self, target: str) -> "CertificateOfOriginPage":
        """target 'ar' | 'en': clicks the header switcher, waits for the URL of the
        same COO page in the target locale, then for html[lang] to flip."""
        self.page.locator(self.LANGUAGE_SWITCHER).first.click()
        expected = web_url(COO_PATH, locale=target).split("?")[0].rstrip("/")
        self.wait_for_url(lambda url: url.split("?")[0].split("#")[0].rstrip("/") == expected, timeout=30000)
        self.page.wait_for_function(
            "(lang) => (document.documentElement.getAttribute('lang') || '').toLowerCase().startsWith(lang)",
            arg=target, timeout=15000)
        self.wait_for(self.HERO_TITLE)
        return self

    def scroll_y(self) -> float:
        return self.page.evaluate("() => window.scrollY")

    def page_height(self) -> float:
        return self.page.evaluate("() => document.documentElement.scrollHeight")

    def click_index_entry(self, label: str) -> None:
        """Clicks the sticky index entry whose label reads `label` and waits until
        the entry carries `is-active` and scrolling has stopped."""
        entry = self.page.locator(f'{self.INDEX_ITEM}:has({self.INDEX_LABEL}:text-is("{label}"))').first
        entry.click()
        self.page.wait_for_function(
            """(label) => [...document.querySelectorAll('.qc-coo-index-item.is-active .qc-coo-index-label')]
                          .some(e => e.textContent.trim() === label)""", arg=label, timeout=15000)
        self.page.evaluate(
            """() => new Promise(res => { let last = -1, still = 0; const tick = () => {
                   if (window.scrollY === last) { if (++still >= 5) return res(true); } else { still = 0; last = window.scrollY; }
                   requestAnimationFrame(tick); }; tick(); })""")

    def section_title_top(self, section_id: str) -> float:
        return self.page.locator(self.section_title_selector(section_id)).first.evaluate(
            "e => e.getBoundingClientRect().top")

    def section_top(self, section_id: str) -> float:
        return self.page.locator(f"#{section_id}").first.evaluate("e => e.getBoundingClientRect().top")

    def index_viewport_top(self) -> float:
        return self.page.locator(self.INDEX).first.evaluate("e => e.getBoundingClientRect().top")

    def accordion_titles(self) -> list:
        return [t.strip() for t in self.page.locator(self.ACC_TITLE).all_inner_texts()]

    def is_accordion_answer_visible(self, title: str) -> bool:
        return self._accordion_item(title).locator(self.ACC_ANSWER).is_visible()

    def accordion_item_open_class(self, title: str) -> bool:
        return "is-open" in (self._accordion_item(title).get_attribute("class") or "").split()

    def accordion_chevron_transform(self, title: str) -> str:
        """Computed transform of the header's chevron svg (the rotation state)."""
        # `.qc-coo-acc-mark` rotates 45deg under `.qc-coo-acc-item.is-open` (page CSS, anonymous GET
        # 2026-10-07: reports/locators/certificate_of_origin/coo_en_anon_20261007.html).
        return self._accordion_item(title).locator(self.ACC_MARK).first.evaluate(
            "e => getComputedStyle(e).transform")

    def collapse_accordion_item(self, title: str) -> None:
        item = self._accordion_item(title)
        question = item.locator(self.ACC_QUESTION)
        if question.get_attribute("aria-expanded") == "true":
            question.click()
        self.page.wait_for_function(
            """(title) => { const i = [...document.querySelectorAll('.qc-coo-acc-item')].find(x =>
                   (x.querySelector('.qc-coo-acc-title') || {}).textContent.trim() === title);
                 return i && i.querySelector('.qc-coo-acc-q').getAttribute('aria-expanded') === 'false'; }""",
            arg=title)
        self.page.wait_for_function("() => document.getAnimations().every(a => a.playState !== 'running')")

    def section_height(self, section_id: str) -> float:
        return self.page.locator(f"#{section_id}").first.bounding_box()["height"]

    def href_of(self, locator: str, index: int = 0) -> str:
        return self.page.locator(locator).nth(index).get_attribute("href") or ""

    def target_of(self, locator: str, index: int = 0) -> str:
        return self.page.locator(locator).nth(index).get_attribute("target") or ""

    def click_expect_popup(self, locator: str, index: int = 0):
        """Clicks and returns the new tab (Playwright Page) the control opens."""
        with self.page.context.expect_page(timeout=20000) as info:
            self.page.locator(locator).nth(index).click()
        popup = info.value
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=30000)
        except Exception:  # noqa: BLE001 — an external destination may never finish loading
            pass
        return popup

    def tab_to(self, locator: str, max_presses: int = 120) -> bool:
        """Presses Tab until the element matching `locator` holds focus."""
        self.page.locator("body").click(position={"x": 1, "y": 1})
        for _ in range(max_presses):
            self.page.keyboard.press("Tab")
            if self.page.locator(locator).first.evaluate("e => e === document.activeElement"):
                return True
        return False

    def focus_indicator(self, locator: str) -> dict:
        return self.page.locator(locator).first.evaluate(
            "e => { const s = getComputedStyle(e); return {outline: s.outlineStyle, width: s.outlineWidth,"
            " shadow: s.boxShadow, visible: e.matches(':focus-visible')}; }")

    def press_enter_expect_popup(self):
        with self.page.context.expect_page(timeout=20000) as info:
            self.page.keyboard.press("Enter")
        return info.value

    def is_enabled_link(self, locator: str, index: int = 0) -> bool:
        return self.page.locator(locator).nth(index).evaluate(
            "e => e.tagName.toLowerCase() === 'a' && !!e.getAttribute('href') && !e.hasAttribute('disabled')"
            " && e.getAttribute('aria-disabled') !== 'true' && getComputedStyle(e).pointerEvents !== 'none'")

    def download_via_button(self):
        """Clicks the download card's button; returns the Playwright Download."""
        with self.page.expect_download(timeout=30000) as info:
            self.page.locator(self.DOWNLOAD_BUTTON).first.click()
        return info.value

    def http_status(self, url: str) -> int:
        return self.page.request.get(url).status

    def boxes(self, locator: str) -> list:
        loc = self.page.locator(locator)
        return [loc.nth(i).bounding_box() for i in range(loc.count())]

    def clipped_text_in(self, scope: str = ".qc-coo") -> list:
        """Visible leaf elements whose text overflows their own box."""
        return self.page.evaluate(
            """(s) => [...document.querySelectorAll(s + ' *')].filter(e => e.offsetParent && e.children.length === 0
                   && e.textContent.trim() && !/sr-only/.test(String(e.className))
                   && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'visible')
                   .map(e => String(e.className) + ' ' + e.textContent.trim().slice(0, 30))""", scope)

    def surface_colors(self, scope: str = ".qc-coo") -> list:
        """Distinct opaque background colours painted inside `scope`."""
        return self.page.evaluate(
            """(s) => [...new Set([document.querySelector(s), ...document.querySelectorAll(s + ' *')]
                   .filter(e => e && e.offsetParent !== null).map(e => getComputedStyle(e).backgroundColor)
                   .filter(c => c && !/rgba\\([^)]*,\\s*0\\)$/.test(c) && c !== 'transparent'))]""", scope)

"""
web/pages/economic_research/economic_research_page.py — EconomicResearchPage.

Public-frontend Page Object for PBI 129407 (QC-SVC-009 — Economic Research),
`/our-services/economic-research` (Arabic: the same path under `/ar`).

Locators EXTRACTED LIVE against qcdev on 2026-09-20, CLI-first via
tools/extract_locators.py plus scripted DOM probes — the Playwright MCP was
not used. The page is a single `section.qc-er` component with a flat `qc-er-*`
class namespace; both content sections carry real ids (`#qc-er-01`,
`#qc-er-02`), so the section locators are id-anchored rather than positional.

Verified live in EN and AR: 2 sections, 2 index items, 4 fact tiles, 3 report
cards, each card with a thumbnail, a `<time>` date, a title, a description and
a "Download PDF" link pointing straight at a `/documents/...pdf` URL.

LIVE FINDINGS reported to the QA Manager rather than absorbed silently:
  * The inferred slug `/our-services/information/economic-research` is wrong —
    this site has no `/information/` segment. Real path below.
  * THERE IS NO REPORT PREVIEW. The library intro copy promises "open any card
    to read its summary, metadata, and key topics before downloading the full
    PDF", but `article.qc-er-card` has no href, no click handler and
    `cursor: auto`; clicking one changes neither the URL nor the DOM. The
    PREVIEW_* constants below therefore have NO live target, and
    open_report_preview() cannot work against the page as shipped.
  * THE SECTION INDEX HAS NO ACTIVE STATE. Neither clicking an index entry nor
    scrolling through the sections adds any class to `.qc-er-index-item` (the
    sibling Economic Consultancy page does apply `is-active`). So
    active_index_entry() has nothing to match.
  * The section badge class is `qc-er-section-eyebrow`, not the `-badge` this
    Page Object was scaffolded with.
  * Dark mode is not a control on this page; it lives in the site-wide
    accessibility tray, which must be opened first.
  * AR renders a horizontal scrollbar that EN does not — same RTL overflow
    seen on Economic Consultancy.
"""

from core.web.base_page import BasePage
from config.settings import web_url

# CONFIRMED live 2026-09-20 (HTTP 200, title "Economic Research - Qatar
# Chamber"). The scaffolded "/our-services/information/..." is not a real path.
PATH = "/our-services/economic-research"

# Section anchor ids in render order — the section index links to these.
SECTION_ANCHORS = ["qc-er-01", "qc-er-02"]


class EconomicResearchPage(BasePage):
    # -- Main menu / navigation ------------------------------------------------
    # The header renders every service link flat, so the Economic Research
    # entry is addressed by its own href rather than by opening "Our Services"
    # first. Those nav hrefs carry the Liferay site prefix /web/qatar-chamber
    # even though the page also resolves at the short path used here.
    MAIN_MENU_OUR_SERVICES = "a.qc-nav-link[href$='/our-services']"
    MAIN_MENU_ECONOMIC_RESEARCH_LINK = "a.qc-nav-link[href$='/our-services/economic-research']"

    # One switcher that flips between the two languages. Its label is the
    # language it switches TO, so only one of these matches at a time.
    LANGUAGE_TOGGLE_AR = "a.qc-lang-switcher:has-text('AR')"
    LANGUAGE_TOGGLE_EN = "a.qc-lang-switcher:has-text('EN')"

    # Dark mode is not a control on this page — it lives in the site-wide
    # accessibility tray (see web/pages/components/accessibility_tools_component.py).
    ACCESSIBILITY_TRAY_OPEN = 'button[aria-label="Accessibility tools"]'
    THEME_TOGGLE = "button.qc-a11y-switch[data-qc-a11y-dark]"

    # -- Hero ---------------------------------------------------------------
    HERO = "header.qc-er-hero"
    HERO_BREADCRUMB = "nav.qc-er-crumbs"
    HERO_BREADCRUMB_HOME_LINK = "a.qc-er-crumb:not(.is-current)"
    HERO_BREADCRUMB_SERVICES_LINK = "a.qc-er-crumb.is-current"
    HERO_EYEBROW = "p.qc-er-eyebrow"
    HERO_TITLE = "h1.qc-er-title"
    HERO_DESCRIPTION = ".qc-er-hero-desc"
    HERO_BANNER_IMAGE = "img.qc-er-hero-img"

    # -- Quick facts strip ----------------------------------------------------
    FACT_TILE = ".qc-er-fact"
    FACT_ICON = ".qc-er-fact-icon"
    FACT_LABEL = ".qc-er-fact-label"
    FACT_VALUE = ".qc-er-fact-value"

    # -- Section index --------------------------------------------------------
    SECTION_INDEX = "nav.qc-er-index"
    SECTION_INDEX_ITEM = "a.qc-er-index-item"
    SECTION_INDEX_NUM = ".qc-er-index-num"
    SECTION_INDEX_LABEL = ".qc-er-index-label"
    # The active-state class the sibling Economic Consultancy page applies.
    # This page applies NOTHING — see the module docstring. Kept named so the
    # gap is explicit rather than hidden inside a selector string.
    SECTION_INDEX_ACTIVE_CLASS = "is-active"

    # -- Sections (2, id-anchored) ---------------------------------------------
    SECTION = "section.qc-er-section"
    # The live class is `-eyebrow`; `-badge` (scaffolded) matches nothing.
    SECTION_BADGE = ".qc-er-section-eyebrow"
    SECTION_TITLE = "h2.qc-er-section-title"
    SECTION_ICON = ".qc-er-section-icon"

    # -- Section 01 (Overview) -------------------------------------------------
    SECTION01 = "#qc-er-01"
    SECTION01_BODY = "#qc-er-01 .qc-er-body-copy"

    # -- Section 02 (Research library) -----------------------------------------
    SECTION02 = "#qc-er-02"
    SECTION02_INTRO = "#qc-er-02 p.qc-er-body-copy"
    REPORT_CARDS = ".qc-er-cards"
    REPORT_CARD = "article.qc-er-card"
    REPORT_CARD_THUMBNAIL = ".qc-er-card-thumb img"
    REPORT_CARD_TITLE = "h3.qc-er-card-title"
    REPORT_CARD_DESCRIPTION = "p.qc-er-card-desc"
    # A <time datetime="YYYY-MM-DD"> element — see report_card_publish_dates()
    # for the human text and report_card_publish_datetimes() for the machine
    # value the ordering assertions should use.
    REPORT_CARD_PUBLISH_DATE = "time.qc-er-card-date"
    # A plain link straight to the PDF (/documents/...pdf), not a button and
    # not a JS download handler.
    REPORT_CARD_DOWNLOAD_BUTTON = "a.qc-er-dl"
    REPORT_CARD_DOWNLOAD_ICON = ".qc-er-dl-icon"

    # -- Report preview view ------------------------------------------------------
    # NOT IMPLEMENTED ON THE LIVE PAGE — see the module docstring. The cards
    # are inert <article> elements with no preview to open. These constants are
    # deliberately left as unresolvable selectors under a qc-er-preview
    # namespace that does not exist, so that a case exercising the preview
    # fails loudly against a real absence instead of silently passing.
    PREVIEW = ".qc-er-preview"
    PREVIEW_TITLE = ".qc-er-preview-title"
    PREVIEW_SUMMARY = ".qc-er-preview-summary"
    PREVIEW_PUBLISH_DATE = ".qc-er-preview-date"
    PREVIEW_DOWNLOAD_ACTION = ".qc-er-preview .qc-er-dl"

    def open_economic_research(self, locale: str = "en") -> "EconomicResearchPage":
        self.open(web_url(PATH, locale=locale))
        return self

    def wait_for_hero(self) -> "EconomicResearchPage":
        self.wait_for(self.HERO_TITLE)
        return self

    def wait_for_library(self) -> "EconomicResearchPage":
        self.wait_for(self.REPORT_CARD, first=True)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("document.documentElement.getAttribute('dir') || getComputedStyle(document.body).direction")

    # -- Hero ------------------------------------------------------------------
    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_description_text(self) -> str:
        return self.text(self.HERO_DESCRIPTION)

    def hero_element_order(self) -> dict:
        return self.page.evaluate(
            """(sel) => {
                const box = (s) => {
                    const el = document.querySelector(s);
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    return {x: r.x, y: r.y, width: r.width, height: r.height};
                };
                return {
                    breadcrumb: box(sel.breadcrumb),
                    eyebrow: box(sel.eyebrow),
                    title: box(sel.title),
                    description: box(sel.description),
                    banner: box(sel.banner),
                };
            }""",
            {
                "breadcrumb": self.HERO_BREADCRUMB,
                "eyebrow": self.HERO_EYEBROW,
                "title": self.HERO_TITLE,
                "description": self.HERO_DESCRIPTION,
                "banner": self.HERO_BANNER_IMAGE,
            },
        )

    def description_metrics(self) -> dict:
        return self.page.evaluate(
            """(sel) => {
                const el = document.querySelector(sel);
                if (!el) return null;
                const style = getComputedStyle(el);
                return {
                    scrollWidth: el.scrollWidth, clientWidth: el.clientWidth,
                    scrollHeight: el.scrollHeight, clientHeight: el.clientHeight,
                    overflowX: style.overflowX, overflowY: style.overflowY,
                };
            }""",
            self.HERO_DESCRIPTION,
        )

    def banner_image_natural_size(self) -> dict:
        """naturalWidth/naturalHeight vs. rendered width/height, used to
        assert the banner is scaled proportionally and not distorted."""
        return self.page.evaluate(
            """(sel) => {
                const el = document.querySelector(sel);
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return {
                    naturalWidth: el.naturalWidth, naturalHeight: el.naturalHeight,
                    renderedWidth: r.width, renderedHeight: r.height,
                };
            }""",
            self.HERO_BANNER_IMAGE,
        )

    # -- Quick facts -------------------------------------------------------------
    def fact_labels(self) -> list[str]:
        return self.page.locator(self.FACT_TILE).locator(self.FACT_LABEL).all_inner_texts()

    def fact_values(self) -> list[str]:
        return self.page.locator(self.FACT_TILE).locator(self.FACT_VALUE).all_inner_texts()

    def fact_tile_count(self) -> int:
        return self.page.locator(self.FACT_TILE).count()

    def fact_tile_has_icon(self, index: int) -> bool:
        return self.page.locator(self.FACT_TILE).nth(index).locator(self.FACT_ICON).count() > 0

    # -- Section index -------------------------------------------------------------
    def index_numerals(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.SECTION_INDEX_NUM).all_inner_texts()]

    def index_labels(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator(self.SECTION_INDEX_LABEL).all_inner_texts()]

    def index_numbers(self) -> list[str]:
        """['01 Overview', '02 Research library'] — numeral and label read as
        SEPARATE nodes and joined with a single space.

        Reading the whole <a> returns a layout- and locale-dependent
        separator ('01
Overview' at 1920px, '01Overview' at 390px), which
        made the same assertion pass on desktop and fail on mobile."""
        return [f"{n} {l}" for n, l in zip(self.index_numerals(), self.index_labels())]

    def section_badge_text(self, section_number: int) -> str:
        return self.page.locator(self.SECTION_BADGE).nth(section_number - 1).inner_text()

    def section_title_text(self, section_number: int) -> str:
        return self.page.locator(self.SECTION_TITLE).nth(section_number - 1).inner_text()

    # -- Section 02 — Research library ----------------------------------------------
    def report_card_count(self) -> int:
        return self.page.locator(self.REPORT_CARD).count()

    def report_card_titles(self) -> list[str]:
        return self.page.locator(self.REPORT_CARD).locator(self.REPORT_CARD_TITLE).all_inner_texts()

    def report_card_descriptions(self) -> list[str]:
        return self.page.locator(self.REPORT_CARD).locator(self.REPORT_CARD_DESCRIPTION).all_inner_texts()

    def report_card_publish_dates(self) -> list[str]:
        """The dates as displayed, e.g. "18 January 2022"."""
        return self.page.locator(self.REPORT_CARD).locator(self.REPORT_CARD_PUBLISH_DATE).all_inner_texts()

    def report_card_publish_datetimes(self) -> list[str]:
        """The machine-readable `datetime` values, e.g. "2022-01-18". Use
        these for ordering assertions — the displayed text is localised and
        sorts differently in AR."""
        return self.page.locator(self.REPORT_CARD).locator(
            self.REPORT_CARD_PUBLISH_DATE
        ).evaluate_all("els => els.map(e => e.getAttribute('datetime'))")

    def report_card_download_urls(self) -> list[str]:
        return self.page.locator(self.REPORT_CARD).locator(
            self.REPORT_CARD_DOWNLOAD_BUTTON
        ).evaluate_all("els => els.map(e => e.getAttribute('href'))")

    def report_card_has_thumbnail(self, index: int) -> bool:
        return self.page.locator(self.REPORT_CARD).nth(index).locator(self.REPORT_CARD_THUMBNAIL).count() > 0

    def report_card_has_download_button(self, index: int) -> bool:
        return self.page.locator(self.REPORT_CARD).nth(index).locator(self.REPORT_CARD_DOWNLOAD_BUTTON).count() > 0

    def open_report_preview(self, index: int) -> "EconomicResearchPage":
        """Clicks a report card and waits for its preview.

        This CANNOT succeed against the page as shipped — the cards are inert
        <article> elements with no preview behind them (see the module
        docstring). The click and the wait are kept exactly as the case
        describes so the failure lands on the missing preview, which is the
        product gap, rather than being hidden by a helper that quietly does
        nothing."""
        self.page.locator(self.REPORT_CARD).nth(index).click()
        self.wait_for(self.PREVIEW_TITLE)
        return self

    def report_preview_is_open(self) -> bool:
        """Non-raising probe for the preview, for cases that assert on its
        absence rather than driving it."""
        return self.page.locator(self.PREVIEW).count() > 0

    def report_card_is_interactive(self, index: int) -> bool:
        """Whether a card actually offers the "open the card" affordance its
        own intro copy promises. False on the page as shipped."""
        return self.page.locator(self.REPORT_CARD).nth(index).evaluate(
            """(el) => Boolean(
                el.getAttribute('href') ||
                el.onclick ||
                el.getAttribute('role') === 'button' ||
                el.tagName === 'A' ||
                getComputedStyle(el).cursor === 'pointer'
            )"""
        )

    # -- Report preview -------------------------------------------------------------
    def preview_title_text(self) -> str:
        return self.text(self.PREVIEW_TITLE)

    def preview_summary_text(self) -> str:
        return self.text(self.PREVIEW_SUMMARY)

    def preview_publish_date_text(self) -> str:
        return self.text(self.PREVIEW_PUBLISH_DATE)

    def preview_download_action_is_visible(self) -> bool:
        return self.is_visible(self.PREVIEW_DOWNLOAD_ACTION)

    # -- Navigation / main menu ---------------------------------------------------------
    def open_home(self, locale: str = "en") -> "EconomicResearchPage":
        self.open(web_url("/", locale=locale))
        return self

    def navigate_via_main_menu(self) -> "EconomicResearchPage":
        self.click(self.MAIN_MENU_OUR_SERVICES)
        self.click(self.MAIN_MENU_ECONOMIC_RESEARCH_LINK)
        self.wait_for_hero()
        return self

    def breadcrumb_home_href(self) -> str:
        """The Home crumb's real href. On this Liferay site that is
        '/web/qatar-chamber', NOT '/' — an expectation of '/' fails against
        the deployed site regardless of timing."""
        return self.get_attribute(self.HERO_BREADCRUMB_HOME_LINK, "href") or ""

    def breadcrumb_services_href(self) -> str:
        return self.get_attribute(self.HERO_BREADCRUMB_SERVICES_LINK, "href") or ""

    def click_breadcrumb_home(self) -> str:
        """Clicks the Home crumb, WAITS for the navigation to land, and
        returns the href it navigated to so the caller asserts against the
        page's own contract instead of a hardcoded path. click() returns on
        dispatch, so without this wait page.url still reads the service
        page."""
        href = self.breadcrumb_home_href()
        self.click(self.HERO_BREADCRUMB_HOME_LINK)
        self.wait_for_url(f"**{href}")
        return href

    def click_breadcrumb_services(self) -> str:
        href = self.breadcrumb_services_href()
        self.click(self.HERO_BREADCRUMB_SERVICES_LINK)
        self.wait_for_url(f"**{href}")
        return href

    def toggle_language(self, target: str) -> "EconomicResearchPage":
        """target: 'ar' | 'en'."""
        self.click(self.LANGUAGE_TOGGLE_AR if target == "ar" else self.LANGUAGE_TOGGLE_EN)
        self.wait_for_hero()
        return self

    def switch_theme(self, theme: str) -> "EconomicResearchPage":
        """theme: 'dark' | 'light'. Dark mode sits behind the site-wide
        accessibility tray, so the tray is opened before its switch is
        clickable — the scaffolded single click would have acted on a hidden
        element."""
        self.click(self.ACCESSIBILITY_TRAY_OPEN)
        self.wait_for(self.THEME_TOGGLE)
        self.click(self.THEME_TOGGLE)
        return self

    def has_horizontal_scrollbar(self) -> bool:
        return self.page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")

    # -- Section index active-state tracking ---------------------------------------------
    def click_index_entry(self, index: int) -> "EconomicResearchPage":
        self.page.locator(self.SECTION_INDEX_ITEM).nth(index).click()
        return self

    def active_index_entry(self) -> str:
        """The highlighted index entry, or "" when none is highlighted.

        Returns "" on the page as shipped: this page applies no active class
        at all, on click or on scroll (verified live 2026-09-20). Returning
        "" rather than raising keeps the caller asserting on the real
        behaviour — an empty active state — instead of on a locator error."""
        active = self.page.locator(
            f"{self.SECTION_INDEX_ITEM}.{self.SECTION_INDEX_ACTIVE_CLASS}"
        )
        return " ".join(active.first.inner_text().split()) if active.count() else ""

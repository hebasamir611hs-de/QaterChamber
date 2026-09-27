"""
web/pages/economic_consultancy/economic_consultancy_page.py — EconomicConsultancyPage.

Public-frontend Page Object for PBI 129406 (QC-SVC-008 — Economic Consultancy),
`/our-services/economic-consultancy` (Arabic: the same path under `/ar`).

Locators EXTRACTED LIVE against qcdev on 2026-09-20, CLI-first via
tools/extract_locators.py plus scripted DOM probes — the Playwright MCP was
not used. The page is a single `section.qc-ec` component with a flat, stable
`qc-ec-*` class namespace, so every locator below is a direct class selector.
Nothing is chained off DOM position except the deliberate per-section helpers,
which index the four sibling `.qc-ec-section` nodes in render order.

Verified live in EN and AR:
  * `.qc-ec-section` = 4, `.qc-ec-fact` = 4, `.qc-ec-index-item` = 4,
    `.qc-ec-faq-item` = 4; info cards = 3, area cards = 4, scope items = 8
    across 2 groups, highlights = 4.
  * AR serves the same class namespace at `/ar/...`, with `html[dir=rtl]` and
    `lang="ar-SA"`.

LIVE FINDINGS reported to the QA Manager rather than absorbed silently:
  * The inferred slug `/our-services/information/economic-consultancy` is
    wrong — this site has no `/information/` segment. Real path below.
  * THE PAGE SHIPS NO CTA. `[class*=cta]` matches zero elements, so there is
    no hero CTA to assert visible. HERO_CTA is kept as a documented
    negative-assertion constant, not a working selector.
  * The section-index active state is `is-active`, not `active` — the
    scaffolded `active_index_entry()` would never have matched anything.
  * The FAQ is an accordion: the item gains `is-open`, the question button
    carries `aria-expanded`, and the answer is hidden by default.
  * Dark mode is not a control on this page; it lives in the site-wide
    accessibility tray, which must be opened first.
"""

from core.web.base_page import BasePage
from config.settings import web_url

# CONFIRMED live 2026-09-20 (HTTP 200, title "Economic Consultancy - Qatar
# Chamber"). The scaffolded "/our-services/information/..." is not a real path.
PATH = "/our-services/economic-consultancy"

# Section anchor ids in render order — the section index links to these.
SECTION_ANCHORS = ["qc-ec-overview", "qc-ec-areas", "qc-ec-scope", "qc-ec-faq"]


class EconomicConsultancyPage(BasePage):
    # -- Main menu / navigation ------------------------------------------------
    # The header renders every service link flat (no hover-expand is needed to
    # reach them), so the Economic Consultancy entry is addressed by its own
    # href rather than by opening "Our Services" first. Those nav hrefs carry
    # the Liferay site prefix /web/qatar-chamber even though the page also
    # resolves at the short path this module navigates to.
    MAIN_MENU_OUR_SERVICES = "a.qc-nav-link[href$='/our-services']"
    MAIN_MENU_ECONOMIC_CONSULTANCY_LINK = "a.qc-nav-link[href$='/our-services/economic-consultancy']"

    # One switcher that flips between the two languages. Its label is the
    # language it switches TO, so the same element backs both constants and
    # only one of them matches at a time.
    LANGUAGE_TOGGLE_AR = "a.qc-lang-switcher:has-text('AR')"
    LANGUAGE_TOGGLE_EN = "a.qc-lang-switcher:has-text('EN')"

    # Dark mode is not a control on this page — it lives in the site-wide
    # accessibility tray (see web/pages/components/accessibility_tools_component.py,
    # which owns the open/switch/done sequence).
    ACCESSIBILITY_TRAY_OPEN = 'button[aria-label="Accessibility tools"]'
    THEME_TOGGLE = "button.qc-a11y-switch[data-qc-a11y-dark]"

    # -- Hero ---------------------------------------------------------------
    HERO = "header.qc-ec-hero"
    HERO_BREADCRUMB = "nav.qc-ec-crumbs"
    HERO_BREADCRUMB_HOME_LINK = "a.qc-ec-crumb:not(.is-current)"
    HERO_BREADCRUMB_SERVICES_LINK = "a.qc-ec-crumb.is-current"
    HERO_EYEBROW = "p.qc-ec-eyebrow"
    HERO_TITLE = "h1.qc-ec-title"
    HERO_DESCRIPTION = ".qc-ec-hero-desc"
    HERO_BANNER_IMAGE = "img.qc-ec-hero-img"
    # NOT PRESENT on the live page — see the module docstring. Kept so that a
    # "no CTA rendered" check resolves to a real count of zero instead of
    # erroring on an unfilled placeholder.
    HERO_CTA = ".qc-ec-hero [class*='cta']"

    # -- Quick facts strip ----------------------------------------------------
    FACT_TILE = ".qc-ec-fact"
    FACT_ICON = ".qc-ec-fact-icon"
    FACT_LABEL = ".qc-ec-fact-label"
    FACT_VALUE = ".qc-ec-fact-value"

    # -- Section index --------------------------------------------------------
    SECTION_INDEX = "nav.qc-ec-index"
    SECTION_INDEX_ITEM = "a.qc-ec-index-item"
    SECTION_INDEX_ACTIVE_CLASS = "is-active"
    SECTION_INDEX_NUM = ".qc-ec-index-num"
    SECTION_INDEX_LABEL = ".qc-ec-index-label"

    # -- Sections (4 siblings, indexed in render order) -----------------------
    SECTION = "section.qc-ec-section"
    SECTION_BADGE = ".qc-ec-section-badge"
    SECTION_TITLE = "h2.qc-ec-section-title"
    SECTION_ICON = ".qc-ec-section-icon"

    # -- Section 01 (Overview) -------------------------------------------------
    # Two .qc-ec-intro blocks render inside this section: the opening body copy
    # and, after the info cards, a secondary paragraph. They share a class, so
    # they are separated by position WITHIN the section rather than by a
    # distinct selector the markup does not provide.
    SECTION01 = "#qc-ec-overview"
    # Both intro blocks are pure CSS, not Playwright ">> nth=" chains, because
    # hero_element_order() and section01_render_order() below resolve these
    # same constants through document.querySelector, which cannot parse
    # Playwright's chaining syntax. The secondary paragraph is the intro that
    # FOLLOWS the info cards; the body is the one that does not.
    SECTION01_BODY = "#qc-ec-overview .qc-ec-intro:not(.qc-ec-cards ~ .qc-ec-intro)"
    SECTION01_SECONDARY_PARAGRAPH = "#qc-ec-overview .qc-ec-cards ~ .qc-ec-intro"
    SECTION01_INFO_CARD = ".qc-ec-cards--info .qc-ec-card"
    SECTION01_INFO_CARD_TITLE = ".qc-ec-card-title"
    SECTION01_INFO_CARD_DESCRIPTION = ".qc-ec-card-desc"
    SECTION01_HIGHLIGHT_LIST = "ul.qc-ec-highlight-list"
    SECTION01_HIGHLIGHT_ITEM = "li.qc-ec-highlight"

    # -- Section 02 (Areas of Economic Consultancy) ----------------------------
    SECTION02_INTRO = "#qc-ec-areas .qc-ec-intro"
    AREA_CARD = ".qc-ec-cards--area .qc-ec-card"
    AREA_CARD_ICON = ".qc-ec-card-icon"
    AREA_CARD_TITLE = ".qc-ec-card-title"
    AREA_CARD_DESCRIPTION = ".qc-ec-card-desc"

    # -- Section 03 (Service Scope & Exclusions) -------------------------------
    SCOPE_INCLUDED_BLOCK = ".qc-ec-scope-group--included"
    SCOPE_INCLUDED_HEADING = ".qc-ec-scope-group--included .qc-ec-scope-head"
    SCOPE_INCLUDED_ITEM = ".qc-ec-scope-group--included .qc-ec-scope-item"
    SCOPE_EXCLUDED_BLOCK = ".qc-ec-scope-group--excluded"
    SCOPE_EXCLUDED_HEADING = ".qc-ec-scope-group--excluded .qc-ec-scope-head"
    SCOPE_EXCLUDED_ITEM = ".qc-ec-scope-group--excluded .qc-ec-scope-item"

    # -- Section 04 (FAQ) -------------------------------------------------------
    FAQ_ITEM = ".qc-ec-faq-item"
    FAQ_QUESTION = "button.qc-ec-faq-q"
    FAQ_ANSWER = ".qc-ec-faq-a"
    FAQ_OPEN_CLASS = "is-open"

    def open_economic_consultancy(self, locale: str = "en") -> "EconomicConsultancyPage":
        self.open(web_url(PATH, locale=locale))
        return self

    def wait_for_hero(self) -> "EconomicConsultancyPage":
        self.wait_for(self.HERO_TITLE)
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
        """Bounding-box Y/X positions for the hero's breadcrumb/eyebrow/title/
        description/banner, used to assert vertical/horizontal ordering
        without a hardcoded pixel expectation."""
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

    def hero_cta_is_visible(self) -> bool:
        return self.is_visible(self.HERO_CTA)

    def description_metrics(self) -> dict:
        """scrollWidth/clientWidth/overflow metrics for the hero description,
        used by is_clipped()-style checks — mirrors legal_consultation_page.py."""
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
    def index_numbers(self) -> list[str]:
        """['01', '02', '03', '04'] — the numeral NODE only.

        Reading the whole <a> returns numeral + label, and the separator is
        layout- and locale-dependent ('01
Overview' at 1920px, '01Overview'
        at 390px, '01نظرة عامة' in AR), so the numerals are read
        from SECTION_INDEX_NUM directly and stay stable across breakpoints
        and locales."""
        return [t.strip() for t in self.page.locator(self.SECTION_INDEX_NUM).all_inner_texts()]

    def index_labels(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator(self.SECTION_INDEX_LABEL).all_inner_texts()]

    def index_entries(self) -> list[str]:
        """['01 Overview', ...] — numeral and label joined with a single
        space, independent of how the two nodes are laid out."""
        return [f"{n} {l}" for n, l in zip(self.index_numbers(), self.index_labels())]

    # -- Sections (generic, by 1-based section number) ------------------------------
    def section_badge_text(self, section_number: int) -> str:
        return self.page.locator(self.SECTION_BADGE).nth(section_number - 1).inner_text()

    def section_title_text(self, section_number: int) -> str:
        return self.page.locator(self.SECTION_TITLE).nth(section_number - 1).inner_text()

    # -- Section 01 --------------------------------------------------------------
    def section01_info_card_titles(self) -> list[str]:
        return self.page.locator(self.SECTION01_INFO_CARD).locator(self.SECTION01_INFO_CARD_TITLE).all_inner_texts()

    def section01_highlight_items(self) -> list[str]:
        return self.page.locator(self.SECTION01_HIGHLIGHT_ITEM).all_inner_texts()

    def section01_render_order(self) -> list[str]:
        """DOM order tag of body/info-cards/secondary-paragraph/highlight-list,
        used to assert the case's required render order without a fixed
        pixel comparison."""
        return self.page.evaluate(
            """(sel) => {
                const nodes = [
                    {name: 'body', el: document.querySelector(sel.body)},
                    {name: 'cards', el: document.querySelector(sel.cards)},
                    {name: 'paragraph', el: document.querySelector(sel.paragraph)},
                    {name: 'highlights', el: document.querySelector(sel.highlights)},
                ].filter(n => n.el);
                nodes.sort((a, b) => a.el.getBoundingClientRect().y - b.el.getBoundingClientRect().y);
                return nodes.map(n => n.name);
            }""",
            {
                "body": self.SECTION01_BODY,
                "cards": self.SECTION01_INFO_CARD,
                "paragraph": self.SECTION01_SECONDARY_PARAGRAPH,
                "highlights": self.SECTION01_HIGHLIGHT_LIST,
            },
        )

    # -- Section 02 ----------------------------------------------------------------
    def area_card_titles(self) -> list[str]:
        return self.page.locator(self.AREA_CARD).locator(self.AREA_CARD_TITLE).all_inner_texts()

    def area_card_descriptions(self) -> list[str]:
        return self.page.locator(self.AREA_CARD).locator(self.AREA_CARD_DESCRIPTION).all_inner_texts()

    def area_card_has_icon(self, index: int) -> bool:
        return self.page.locator(self.AREA_CARD).nth(index).locator(self.AREA_CARD_ICON).count() > 0

    # -- Section 03 ------------------------------------------------------------------
    def scope_included_heading_text(self) -> str:
        return self.text(self.SCOPE_INCLUDED_HEADING)

    def scope_excluded_heading_text(self) -> str:
        return self.text(self.SCOPE_EXCLUDED_HEADING)

    def scope_included_items(self) -> list[str]:
        return self.page.locator(self.SCOPE_INCLUDED_ITEM).all_inner_texts()

    def scope_excluded_items(self) -> list[str]:
        return self.page.locator(self.SCOPE_EXCLUDED_ITEM).all_inner_texts()

    def scope_blocks_are_separate(self) -> bool:
        """True when Included/Excluded render as two distinct block nodes
        rather than one merged list."""
        return (
            self.page.locator(self.SCOPE_INCLUDED_BLOCK).count() > 0
            and self.page.locator(self.SCOPE_EXCLUDED_BLOCK).count() > 0
        )

    # -- Section 04 (FAQ) --------------------------------------------------------------
    def faq_question_texts(self) -> list[str]:
        return self.page.locator(self.FAQ_QUESTION).all_inner_texts()

    def click_faq_question(self, index: int) -> "EconomicConsultancyPage":
        self.click_nth(self.FAQ_QUESTION, index)
        return self

    def faq_answer_is_visible(self, index: int) -> bool:
        return self.page.locator(self.FAQ_ANSWER).nth(index).is_visible()

    def faq_item_is_open(self, index: int) -> bool:
        """Accordion state read from the item's own class, which the answer's
        visibility follows."""
        classes = self.page.locator(self.FAQ_ITEM).nth(index).get_attribute("class") or ""
        return self.FAQ_OPEN_CLASS in classes.split()

    def faq_question_is_expanded(self, index: int) -> bool:
        return self.page.locator(self.FAQ_QUESTION).nth(index).get_attribute("aria-expanded") == "true"

    def hero_cta_count(self) -> int:
        """Zero on the live page — this service page ships no CTA. Exposed so
        a case asserting a CTA fails on a real count rather than on an
        unfilled-locator error."""
        return self.page.locator(self.HERO_CTA).count()

    # -- Navigation / main menu ---------------------------------------------------------
    def open_home(self, locale: str = "en") -> "EconomicConsultancyPage":
        self.open(web_url("/", locale=locale))
        return self

    def navigate_via_main_menu(self) -> "EconomicConsultancyPage":
        self.click(self.MAIN_MENU_OUR_SERVICES)
        self.click(self.MAIN_MENU_ECONOMIC_CONSULTANCY_LINK)
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

    def toggle_language(self, target: str) -> "EconomicConsultancyPage":
        """target: 'ar' | 'en'."""
        self.click(self.LANGUAGE_TOGGLE_AR if target == "ar" else self.LANGUAGE_TOGGLE_EN)
        self.wait_for_hero()
        return self

    def switch_theme(self, theme: str) -> "EconomicConsultancyPage":
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
    def click_index_entry(self, index: int) -> "EconomicConsultancyPage":
        """Clicks the nth (0-based) index entry and waits for the scroll-spy
        to settle the active marker ON THAT ENTRY.

        The entry smooth-scrolls to its section and the `is-active` class is
        applied by a scroll listener, so it lands many frames after click()
        returns — reading the active entry immediately yields the previous
        one."""
        self.click_nth(self.SECTION_INDEX_ITEM, index)
        self.wait_for_class_on_nth(
            self.SECTION_INDEX_ITEM, index, self.SECTION_INDEX_ACTIVE_CLASS
        )
        return self

    def active_index_entry(self) -> str:
        """The index entry currently highlighted. The live class is
        `is-active`, NOT the `active` this method was scaffolded with, which
        matches nothing on the page."""
        return " ".join(
            self.page.locator(
                f"{self.SECTION_INDEX_ITEM}.{self.SECTION_INDEX_ACTIVE_CLASS}"
            ).first.inner_text().split()
        )

    def click_nth(self, locator: str, index: int) -> None:
        self.page.locator(locator).nth(index).click()

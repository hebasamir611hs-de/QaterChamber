"""
web/pages/proposal_for_research/proposal_for_research_page.py — ProposalForResearchPage.

Public-frontend Page Object for PBI 130949 (QC-SVC-010 — Proposal for
Research), `/our-services/proposal-for-research` (Arabic: the same path under
`/ar`).

Locators EXTRACTED LIVE against qcdev on 2026-09-20, CLI-first via
tools/extract_locators.py plus scripted DOM probes — the Playwright MCP was
not used. The page is a single `section.qc-pfr` component with a flat
`qc-pfr-*` class namespace; all three content sections carry real ids
(`#qc-pfr-01`, `#qc-pfr-02`, `#qc-pfr-03`), so section locators are
id-anchored rather than positional.

Verified live in EN and AR: 3 sections, 3 index items, 4 fact tiles, 3
overview cards, 2 service-information guide groups (6 and 4 bullets), and 2
downloadable resources, each a PDF / 200 KB card with a real `download` link.

LIVE FINDINGS reported to the QA Manager rather than absorbed silently:
  * The path recorded in the Phase-1 case text,
    `/en/our-services/information/proposal-for-research`, does not exist.
    There is no `/information/` segment and no `/en` prefix — English is the
    unprefixed default and only Arabic is prefixed (`/ar`). Real path below.
  * THE PAGE SHIPS NO HERO CTA. `[class*=cta]` matches zero elements
    page-wide, and the hero contains no link or button other than the two
    breadcrumbs. HERO_CTA is kept as a documented negative-assertion
    constant, not a working selector.
  * THE SECTION INDEX HAS NO ACTIVE STATE. Neither clicking an index entry
    nor scrolling through the sections adds any class to
    `.qc-pfr-index-item` — the same gap as Economic Research (129407), while
    the sibling Economic Consultancy page (129406) does apply `is-active`.
  * Section 02 has NO body copy — `.qc-pfr-body-copy` exists only in sections
    01 and 03, so section_body_text(2) has nothing to read. Its content is
    the guide groups instead.
  * The hero background is a CSS radial-gradient, not an image; the hero
    artwork is a separate `img.qc-pfr-hero-img`. hero_background_image()
    therefore returns a gradient string, never a url().
  * The section badge class is `qc-pfr-section-eyebrow`, matching Economic
    Research rather than Economic Consultancy's `-badge`.
  * Dark mode is not a control on this page; it lives in the site-wide
    accessibility tray, which must be opened first.
  * AR renders a horizontal scrollbar that EN does not — the same RTL
    overflow seen on 129406 and 129407, so it is site-wide, not per-page.

CONFIRMED AS EXPECTED: no next-step banner renders between the last resource
card and the site footer (`[class*=banner]` = 0), which is what the "no
banner block" check asserts.
"""

from core.web.base_page import BasePage
from config.settings import web_url

# CONFIRMED live 2026-09-20 (HTTP 200, title "Proposal for Research - Qatar
# Chamber"). English is served unprefixed; web_url(..., locale="ar") adds the
# /ar prefix. The "/en/our-services/information/..." path in the Phase-1 case
# text is not a real URL on this site.
PATH = "/our-services/proposal-for-research"

# Section anchor ids in render order — the section index links to these.
SECTION_ANCHORS = ["qc-pfr-01", "qc-pfr-02", "qc-pfr-03"]


class ProposalForResearchPage(BasePage):
    # -- Breadcrumb / Hero ----------------------------------------------------
    BREADCRUMB = "nav.qc-pfr-crumbs"
    BREADCRUMB_ITEM = "a.qc-pfr-crumb"
    BREADCRUMB_HOME_LINK = "a.qc-pfr-crumb:not(.is-current)"
    BREADCRUMB_CURRENT = "a.qc-pfr-crumb.is-current"
    HERO_BLOCK = "header.qc-pfr-hero"
    HERO_EYEBROW = "p.qc-pfr-eyebrow"
    HERO_TITLE = "h1.qc-pfr-title"
    HERO_DESCRIPTION = ".qc-pfr-hero-desc"
    HERO_IMAGE = "img.qc-pfr-hero-img"
    # NOT PRESENT on the live page — see the module docstring. Kept so a "no
    # CTA rendered" check resolves to a real count of zero rather than
    # erroring on an unfilled placeholder. Breadcrumbs are excluded so this
    # does not accidentally match them.
    HERO_CTA = ".qc-pfr-hero a:not(.qc-pfr-crumb), .qc-pfr-hero button"

    # -- Quick facts ------------------------------------------------------------
    FACTS_CONTAINER = ".qc-pfr-facts"
    FACT_TILE = ".qc-pfr-fact"
    FACT_ICON = ".qc-pfr-fact-icon"
    FACT_LABEL = ".qc-pfr-fact-label"
    FACT_VALUE = ".qc-pfr-fact-value"

    # -- Sticky section index ----------------------------------------------------
    INDEX_RAIL = "nav.qc-pfr-index"
    INDEX_ITEM = "a.qc-pfr-index-item"
    INDEX_ITEM_NUM = ".qc-pfr-index-num"
    INDEX_ITEM_LABEL = ".qc-pfr-index-label"
    # The active-state class the sibling Economic Consultancy page applies.
    # This page applies NOTHING, on click or on scroll — see the module
    # docstring. Named so the gap stays visible instead of hiding inside a
    # selector string.
    INDEX_ACTIVE_CLASS = "is-active"
    INDEX_ITEM_ACTIVE = "a.qc-pfr-index-item.is-active"

    # -- Sections (3, id-anchored) ------------------------------------------------
    SECTION = "section.qc-pfr-section"
    # The live class is `-eyebrow`; `-badge` (scaffolded) matches nothing.
    SECTION_BADGE = ".qc-pfr-section-eyebrow"
    SECTION_TITLE = "h2.qc-pfr-section-title"
    SECTION_ICON = ".qc-pfr-section-icon"
    # Sections 01 and 03 only — section 02 carries guide groups instead of
    # body copy, so nth(1) resolves to section 03's copy, not section 02's.
    # See section_body_text()'s docstring.
    SECTION_BODY = ".qc-pfr-body-copy"

    # -- Overview info cards (Section 01) -----------------------------------------
    OVERVIEW_CARDS = ".qc-pfr-cards"
    OVERVIEW_CARD = ".qc-pfr-card"
    OVERVIEW_CARD_ICON = ".qc-pfr-card-icon"
    OVERVIEW_CARD_TITLE = ".qc-pfr-card-title"
    OVERVIEW_CARD_DESCRIPTION = ".qc-pfr-card-desc"

    # -- Service information groups (Section 02) -----------------------------------
    # Each group is a label plus a dotted list whose first entry is an intro
    # paragraph (`.qc-pfr-guide-intro`, marked with an `is-empty` dot) and
    # whose remaining entries are the bullets (`.qc-pfr-guide-item`). The two
    # are distinct classes, so the intro never leaks into the bullet list.
    INFO_GROUPS = ".qc-pfr-guides"
    INFO_GROUP = ".qc-pfr-guide"
    INFO_GROUP_LABEL = "p.qc-pfr-guide-label"
    INFO_GROUP_LIST = ".qc-pfr-guide-list"
    INFO_GROUP_INTRO = ".qc-pfr-guide-intro"
    INFO_GROUP_BULLET = ".qc-pfr-guide-item"
    INFO_GROUP_DOT = ".qc-pfr-guide-dot"

    # -- Downloadable resources (Section 03) ----------------------------------------
    RESOURCE_CARDS = ".qc-pfr-files"
    RESOURCE_CARD = "article.qc-pfr-file"
    RESOURCE_CARD_ICON = ".qc-pfr-file-icon"
    RESOURCE_CARD_TITLE = "h3.qc-pfr-file-title"
    # File type and size share one class inside `.qc-pfr-file-meta`, split by
    # a `.qc-pfr-file-sep`. They are read positionally (0 = type, 1 = size)
    # because the markup gives them no distinguishing attribute.
    RESOURCE_META = "p.qc-pfr-file-meta"
    RESOURCE_META_VALUE = ".qc-pfr-file-metaval"
    RESOURCE_FILE_TYPE = ".qc-pfr-file-metaval >> nth=0"
    RESOURCE_FILE_SIZE = ".qc-pfr-file-metaval >> nth=1"
    # A real link with a `download` attribute pointing at /documents/...pdf,
    # so expect_download() fires on click.
    RESOURCE_DOWNLOAD_BUTTON = "a.qc-pfr-dl"

    # -- Footer / next-step banner (absence checks) -----------------------------------
    # Verified absent on the live page — the check that no banner renders
    # between the last resource card and the footer passes with a count of 0.
    NEXT_STEP_BANNER = ".qc-pfr [class*='banner'], .qc-pfr [class*='next-step']"
    SITE_FOOTER = "footer.qc-global-site-footer"

    # -- Theme toggle --------------------------------------------------------------------
    # Dark mode is not a control on this page — it lives in the site-wide
    # accessibility tray (see web/pages/components/accessibility_tools_component.py).
    ACCESSIBILITY_TRAY_OPEN = 'button[aria-label="Accessibility tools"]'
    THEME_TOGGLE = "button.qc-a11y-switch[data-qc-a11y-dark]"

    # -- Language switcher (header control, labelled AR / EN) -----------------------------
    # One switcher whose label is the language it switches TO, so only one of
    # these matches at a time.
    LANGUAGE_SWITCHER_AR = "a.qc-lang-switcher:has-text('AR')"
    LANGUAGE_SWITCHER_EN = "a.qc-lang-switcher:has-text('EN')"

    def open_proposal_for_research(self, locale: str = "en") -> "ProposalForResearchPage":
        self.open(web_url(PATH, locale=locale))
        return self

    def wait_for_hero(self) -> "ProposalForResearchPage":
        self.wait_for(self.HERO_TITLE)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("document.documentElement.getAttribute('dir') || getComputedStyle(document.body).direction")

    def has_horizontal_scrollbar(self) -> bool:
        return self.page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")

    def computed_style(self, locator: str, properties: list[str]) -> dict:
        """Generic computed-style reader — {property: value} for the given
        locator, used wherever a case names an exact font/color/spacing
        token."""
        return self.page.evaluate(
            """([sel, props]) => {
                const el = document.querySelector(sel);
                if (!el) return null;
                const style = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = style[p];
                return out;
            }""",
            [locator, properties],
        )

    def switch_theme(self, theme: str) -> "ProposalForResearchPage":
        """theme: 'dark' | 'light'. Dark mode sits behind the site-wide
        accessibility tray, so the tray is opened before its switch is
        clickable.

        Opening the tray is IDEMPOTENT: the tray trigger is a toggle, so a
        second switch_theme() call on the same page would have CLOSED an
        already-open tray and hidden the switch it is about to click. The
        tray is therefore opened only when the switch is not already
        visible."""
        if not self.is_visible(self.THEME_TOGGLE):
            self.click(self.ACCESSIBILITY_TRAY_OPEN)
            self.wait_for(self.THEME_TOGGLE)
        self.click(self.THEME_TOGGLE)
        return self

    # -- Breadcrumb --------------------------------------------------------------------
    def breadcrumb_texts(self) -> list[str]:
        return self.page.locator(self.BREADCRUMB_ITEM).all_inner_texts()

    def breadcrumb_home_href(self) -> str | None:
        return self.page.locator(self.BREADCRUMB_HOME_LINK).get_attribute("href")

    # -- Hero --------------------------------------------------------------------------
    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_description_text(self) -> str:
        return self.text(self.HERO_DESCRIPTION)

    def hero_background_image(self) -> str:
        return self.computed_style(self.HERO_BLOCK, ["backgroundImage"])["backgroundImage"]

    def hero_has_cta(self) -> bool:
        """False on the live page — this service page ships no CTA. Counted
        rather than visibility-checked so the answer is a real absence, not a
        "not visible" that an overlay or a broken selector could also
        produce."""
        return self.page.locator(self.HERO_CTA).count() > 0

    # -- Quick facts -------------------------------------------------------------------
    def quick_fact_labels(self) -> list[str]:
        return self.page.locator(self.FACT_TILE).locator(self.FACT_LABEL).all_inner_texts()

    def quick_fact_values(self) -> list[str]:
        return self.page.locator(self.FACT_TILE).locator(self.FACT_VALUE).all_inner_texts()

    # -- Sticky index -----------------------------------------------------------------
    def index_numerals(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.INDEX_ITEM_NUM).all_inner_texts()]

    def index_labels(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator(self.INDEX_ITEM_LABEL).all_inner_texts()]

    def index_entries(self) -> list[str]:
        """['01 Overview', ...] — numeral and label read as SEPARATE nodes and
        joined with a single space.

        Reading the whole <a> returns a layout- and locale-dependent
        separator ('01
Overview' at 1920px, '01نظرة عامة' at 390px in
        AR), so the same expectation passed on desktop and failed on mobile."""
        return [f"{n} {l}" for n, l in zip(self.index_numerals(), self.index_labels())]

    def active_index_entry(self) -> str:
        """The highlighted index entry, or "" when none is highlighted.

        Returns "" on the page as shipped: this page applies no active class
        at all, on click or on scroll (verified live 2026-09-20). Returning
        "" rather than raising keeps the caller asserting on the real
        behaviour — an empty active state — instead of on a locator error."""
        active = self.page.locator(self.INDEX_ITEM_ACTIVE)
        return " ".join(active.first.inner_text().split()) if active.count() else ""

    def scroll_section_into_view(self, section_number: int) -> "ProposalForResearchPage":
        self.page.locator(self.SECTION_TITLE).nth(section_number - 1).scroll_into_view_if_needed()
        return self

    # -- Sections ------------------------------------------------------------------------
    def section_badge_text(self, section_number: int) -> str:
        return self.page.locator(self.SECTION_BADGE).nth(section_number - 1).inner_text()

    def section_title_text(self, section_number: int) -> str:
        return self.page.locator(self.SECTION_TITLE).nth(section_number - 1).inner_text()

    def section_body_text(self, section_number: int) -> str:
        """Body copy of a section, addressed through that section's own id.

        Only sections 01 and 03 have body copy — section 02 carries the guide
        groups instead. Scoping by section id (rather than the scaffolded
        nth(section_number - 1) over all `.qc-pfr-body-copy` nodes) is what
        keeps section 03's copy from being returned when section 02 is asked
        for. Asking for section 02 raises, which is the honest answer."""
        anchor = SECTION_ANCHORS[section_number - 1]
        return self.text(f"#{anchor} {self.SECTION_BODY}")

    def section_has_body_copy(self, section_number: int) -> bool:
        anchor = SECTION_ANCHORS[section_number - 1]
        return self.page.locator(f"#{anchor} {self.SECTION_BODY}").count() > 0

    def section_count(self) -> int:
        return self.page.locator(self.SECTION_TITLE).count()

    # -- Overview info cards (Section 01) ----------------------------------------------
    def overview_card_titles(self) -> list[str]:
        return self.page.locator(self.OVERVIEW_CARD).locator(self.OVERVIEW_CARD_TITLE).all_inner_texts()

    def overview_card_descriptions(self) -> list[str]:
        return self.page.locator(self.OVERVIEW_CARD).locator(self.OVERVIEW_CARD_DESCRIPTION).all_inner_texts()

    # -- Service information groups (Section 02) ---------------------------------------
    def info_group_label(self, group_number: int) -> str:
        return self.page.locator(self.INFO_GROUP).nth(group_number - 1).locator(self.INFO_GROUP_LABEL).inner_text()

    def info_group_intro(self, group_number: int) -> str:
        return self.page.locator(self.INFO_GROUP).nth(group_number - 1).locator(self.INFO_GROUP_INTRO).inner_text()

    def info_group_bullets(self, group_number: int) -> list[str]:
        return self.page.locator(self.INFO_GROUP).nth(group_number - 1).locator(self.INFO_GROUP_BULLET).all_inner_texts()

    # -- Downloadable resources (Section 03) -------------------------------------------
    def resource_card_title(self, index: int) -> str:
        return self.page.locator(self.RESOURCE_CARD).nth(index).locator(self.RESOURCE_CARD_TITLE).inner_text()

    def resource_card_file_type(self, index: int) -> str:
        """The "PDF" half of the card's meta line — the first of two
        same-class values (see RESOURCE_FILE_TYPE)."""
        return self.page.locator(self.RESOURCE_CARD).nth(index).locator(
            self.RESOURCE_META_VALUE
        ).nth(0).inner_text()

    def resource_card_file_size(self, index: int) -> str:
        """The "200 KB" half of the card's meta line."""
        return self.page.locator(self.RESOURCE_CARD).nth(index).locator(
            self.RESOURCE_META_VALUE
        ).nth(1).inner_text()

    def resource_download_urls(self) -> list[str]:
        return self.page.locator(self.RESOURCE_CARD).locator(
            self.RESOURCE_DOWNLOAD_BUTTON
        ).evaluate_all("els => els.map(e => e.getAttribute('href'))")

    def resource_card_button_text(self, index: int) -> str:
        return self.page.locator(self.RESOURCE_CARD).nth(index).locator(self.RESOURCE_DOWNLOAD_BUTTON).inner_text()

    def resource_card_count(self) -> int:
        return self.page.locator(self.RESOURCE_CARD).count()

    # -- Absence / structural checks ---------------------------------------------------
    def next_step_banner_is_present(self) -> bool:
        return self.page.locator(self.NEXT_STEP_BANNER).count() > 0

    def switch_language(self, target: str) -> "ProposalForResearchPage":
        """target: 'ar' | 'en'. Uses the header's own AR/EN switcher control.

        The control is a JS-driven `href="#"` link, and HERO_TITLE exists in
        BOTH locales, so waiting on the hero returned before the navigation
        committed and the caller read the OLD url. The wait is therefore on
        the locale actually taking effect: the target URL, then html[lang]
        flipping to the requested language."""
        self.click(self.LANGUAGE_SWITCHER_AR if target == "ar" else self.LANGUAGE_SWITCHER_EN)
        expected = web_url(PATH, locale=target).split("?")[0].rstrip("/")
        self.wait_for_url(lambda url: url.split("?")[0].rstrip("/") == expected)
        self.page.wait_for_function(
            "(lang) => (document.documentElement.getAttribute('lang') || '')"
            ".toLowerCase().startsWith(lang)",
            arg=target,
            timeout=15000,
        )
        self.wait_for(self.HERO_TITLE)
        return self

    def click_index_entry(self, index: int) -> "ProposalForResearchPage":
        self.page.locator(self.INDEX_ITEM).nth(index).click()
        return self

    def download_resource(self, index: int):
        """Clicks a resource card's Download button and returns the
        Playwright Download object — used to assert filename/size/HTTP
        status without asserting on a fixed byte payload."""
        with self.page.expect_download() as download_info:
            self.page.locator(self.RESOURCE_CARD).nth(index).locator(self.RESOURCE_DOWNLOAD_BUTTON).click()
        return download_info.value

    def gap_between_last_resource_card_and_footer(self) -> float:
        """Vertical gap (px) between the last resource card's bottom edge and
        the site footer's top edge — used by TC-013's "no banner block
        renders between them" check, without asserting a fixed pixel value:
        the test asserts this stays small/consistent instead of the presence
        of a banner-sized gap."""
        return self.page.evaluate(
            """([resourceSel, footerSel]) => {
                const cards = document.querySelectorAll(resourceSel);
                const footer = document.querySelector(footerSel);
                if (!cards.length || !footer) return -1;
                const last = cards[cards.length - 1];
                return footer.getBoundingClientRect().top - last.getBoundingClientRect().bottom;
            }""",
            [self.RESOURCE_CARD, self.SITE_FOOTER],
        )

"""
web/pages/export_reports/export_reports_page.py — ExportReportsPage.

Public-frontend Page Object for PBI 131313 ("QC - Insights & Media - 003 D -
Private Sector Export Reports"), at `/web/qatar-chamber/export-reports`
(AR: `/ar/web/qatar-chamber/export-reports`). The real path was resolved
CLI-first from the live homepage's own rendered nav anchors (same technique
`annual_reports_page.py`'s own module docstring documents for this project's
hover-only Insights & Media nav) — no MCP fallback needed.

Locators: a scripted DOM-class probe (`page.eval_on_selector_all('[class*=qc-]',
...)`) against the live page (CLI-first, 2026-09-22, framework's default
1920x1080 viewport) confirmed the real, stable `qc-er-*` custom classes below.

Confirmed live 2026-09-22 (headless Chromium via Playwright, no MCP):

    header.qc-er-hero > div.qc-er-hero__shell
        nav.qc-er-breadcrumb ("Home" / "Insights & Media")
        span.qc-er-eyebrow ("Insights & Media")
        div.qc-er-hero__copy
            h1.qc-er-hero__title ("Private Sector Export Reports")
            p.qc-er-hero__desc
    section.qc-er-section
        div.qc-er-hd
            span.qc-er-hd__badge ("Quarterly archive")
            h2.qc-er-hd__title ("Find an export report")
            p.qc-er-hd__desc
        div.qc-er-search-wrap > span.qc-er-search__icon, input.qc-er-search__input
        div.qc-er-groups (list of quarter groups, NOT a CSS card grid —
            unlike annual_reports_page.py's flat `.qc-ar-grid`, this page
            groups cards under a per-quarter header)
            div.qc-er-q-group (repeated, one per Quarter+ReportingYear)
                div.qc-er-q-hd
                    span.qc-er-q-badge ("Q4"), span.qc-er-q-name ("Fourth quarter"),
                    span.qc-er-q-period ("October–December 2024")
                div.qc-er-list
                    div.qc-er-card (repeated)
                        div.qc-er-card__thumb (SVG placeholder cover on every
                            REAL live entry — confirmed live no <img> tag
                            exists on any of the 10 real entries; a card
                            built from a DISPOSABLE entry with an uploaded
                            Cover Thumbnail DOES render a real <img>, see
                            test module for the tc_143843 case built on that)
                        div.qc-er-card__body
                            span.qc-er-card__eyebrow ("Q4 · February 2025")
                            h3.qc-er-card__title
                            p.qc-er-card__desc
                            div.qc-er-card__meta ("PDF • 2.4 MB • 20 Pages")
                            div.qc-er-card__footer > div.qc-er-card__actions
                                a.qc-er-card__btn (x2: "View Details" then "Download")
        div.qc-er-more-wrap > button.qc-er-more-btn ("Load More" — confirmed
            live VISIBLE and functional on this environment, unlike
            annual_reports_page.py's always-hidden Load More: 10 real
            published entries span more than one page)

Live data confirmed 2026-09-22 (qcdev, 10 published Export Report entries,
externalReferenceCode QCDEMO-131313-ER-001..010, NO leftover scratch rows —
cleaner than annual_reports' own data set): quarters Q4 2024 down to Q3 2022
(10 consecutive quarters, no gap), newest first. Every real card's meta
line reads "PDF • 2.4 MB • 20 Pages" (identical across all 10) and every
real card's own description reads "Analysis of private-sector exports in
Q<n> <year>, including performance by certificate of origin, destination
markets, and quarterly comparisons." (identical template, year/quarter
substituted) — see test module for the per-case mismatches this produces
against several cases' own literal stated title/description text.

CONFIRMED LIVE MISMATCHES vs. several QA cases' stated wording (not
silently corrected — scripted honestly per Result Integrity, see test
module for the exact per-case disclosure):
  - Search placeholder: real "Search.." (TWO trailing dots) vs. several
    cases' stated "Search." (one dot) — EN and AR ("بحث.." vs "بحث.").
    CONFIRMED via cms/pages/export_reports/export_reports_page_admin_page.py's
    own read of the singleton: there is NO "Search Placeholder" field on
    this object at all (full accessibility-tree enumeration of its edit
    form found none) — the placeholder is hard-coded in the frontend, not
    CMS-driven.
  - Card title: real "Private Sector Exports — Fourth Quarter 2024" (no
    "Report" suffix) vs. tc_143845's stated "...Fourth Quarter 2024 Report".
  - Card description: real "Analysis of private-sector exports in Q4 2024,
    including performance by certificate of origin, destination markets,
    and quarterly comparisons." vs. tc_143846's stated "Export performance
    summary for Qatar's private sector during Q4 2024."
  - No-match search message: real EN "No results match your search." vs.
    tc_143959's stated "No reports match your search."; real AR "لا توجد
    نتائج مطابقة." vs. tc_143967's stated "لا توجد تقارير مطابقة لبحثك."
  - Card meta line ("PDF • 2.4 MB • 20 Pages") and card eyebrow label
    ("Q4 · February 2025") DO match their respective cases' stated values
    exactly — no mismatch there.

Card actions: "View Details" is a real `<a target="_blank">` pointing at
the report's own PDF asset; "Download" is a real `<a>` (no `target`) to the
SAME PDF asset with `&download=true` appended — identical mechanism to
annual_reports_page.py's own confirmed-live finding.
"""

from config.settings import web_url
from core.web.base_page import BasePage

EXPORT_REPORTS_PATH = "/web/qatar-chamber/export-reports"


class ExportReportsPage(BasePage):
    # ---- Hero -------------------------------------------------------------
    HERO = ".qc-er-hero"
    BREADCRUMB = ".qc-er-breadcrumb"
    EYEBROW = ".qc-er-eyebrow"
    HERO_TITLE = ".qc-er-hero__title"
    HERO_DESC = ".qc-er-hero__desc"

    # ---- Archive section ----------------------------------------------------
    SECTION = ".qc-er-section"
    ARCHIVE_BADGE = ".qc-er-hd__badge"
    ARCHIVE_TITLE = ".qc-er-hd__title"
    ARCHIVE_DESC = ".qc-er-hd__desc"
    SEARCH_INPUT = ".qc-er-search__input"

    # ---- Groups / cards -------------------------------------------------------
    GROUPS = ".qc-er-groups"
    GROUP = ".qc-er-q-group"
    GROUP_BADGE = ".qc-er-q-badge"
    GROUP_NAME = ".qc-er-q-name"
    GROUP_PERIOD = ".qc-er-q-period"
    CARD = ".qc-er-card"
    CARD_THUMB = ".qc-er-card__thumb"
    CARD_EYEBROW = ".qc-er-card__eyebrow"
    CARD_TITLE = ".qc-er-card__title"
    CARD_DESC = ".qc-er-card__desc"
    CARD_META = ".qc-er-card__meta"
    CARD_BTN = ".qc-er-card__btn"
    LOAD_MORE = ".qc-er-more-btn"

    # ---- Navigation -----------------------------------------------------
    def open_export_reports(self, locale: str = "en") -> "ExportReportsPage":
        self.open(web_url(EXPORT_REPORTS_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_export_reports_anonymous(self, locale: str = "en") -> "ExportReportsPage":
        """Same navigation, but through `open_anonymous()` — see
        standards.md's "Draft/Unpublish Public-Visibility Checks" rule.
        Callers pass a `page` from a fresh `new_context(use_auth_state=False)`."""
        self.open_anonymous(web_url(EXPORT_REPORTS_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    # ---- Hero queries -----------------------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def breadcrumb_texts(self) -> list:
        return self.page.locator(self.BREADCRUMB).all_inner_texts()

    def eyebrow_text(self) -> str:
        return self.text(self.EYEBROW)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_desc_text(self) -> str:
        return self.text(self.HERO_DESC)

    def hero_title_style(self) -> dict:
        return self.page.locator(self.HERO_TITLE).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {color: cs.color, backgroundColor: cs.backgroundColor}; }"
        )

    def page_background_color(self) -> str:
        return self.page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor")

    def html_dir(self) -> str:
        return self.page.locator("html").get_attribute("dir") or ""

    # ---- Archive section queries --------------------------------------------
    def archive_badge_text(self) -> str:
        return self.text(self.ARCHIVE_BADGE)

    def archive_title_text(self) -> str:
        return self.text(self.ARCHIVE_TITLE)

    def archive_desc_text(self) -> str:
        return self.text(self.ARCHIVE_DESC)

    # ---- Search -------------------------------------------------------------
    def search_placeholder(self) -> str:
        return self.get_attribute(self.SEARCH_INPUT, "placeholder") or ""

    def search(self, term: str) -> "ExportReportsPage":
        self.page.locator(self.SEARCH_INPUT).fill(term)
        self.page.wait_for_timeout(700)  # client-side filter re-render, no navigation to wait_for_url on
        return self

    def clear_search(self) -> "ExportReportsPage":
        self.page.locator(self.SEARCH_INPUT).fill("")
        self.page.wait_for_timeout(700)
        return self

    def search_value(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).input_value()

    # ---- Groups / cards -------------------------------------------------------
    def group_count(self) -> int:
        return self.page.locator(self.GROUP).count()

    def group_badges(self) -> list:
        return self.page.locator(self.GROUP_BADGE).all_inner_texts()

    def group_names(self) -> list:
        return self.page.locator(self.GROUP_NAME).all_inner_texts()

    def group_periods(self) -> list:
        return self.page.locator(self.GROUP_PERIOD).all_inner_texts()

    def group_by_period(self, period: str):
        return self.page.locator(self.GROUP).filter(has=self.page.locator(self.GROUP_PERIOD, has_text=period))

    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return self.page.locator(self.CARD_TITLE).all_inner_texts()

    def card_by_title(self, title: str):
        return self.page.locator(self.CARD).filter(has=self.page.locator(self.CARD_TITLE, has_text=title)).first

    def card_eyebrow(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_EYEBROW).inner_text()

    def card_title(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_TITLE).inner_text()

    def card_desc(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_DESC).inner_text()

    def card_meta(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_META).inner_text()

    def card_has_img_thumb(self, index: int = 0) -> bool:
        return self.page.locator(self.CARD).nth(index).locator(f"{self.CARD_THUMB} img").count() > 0

    def card_thumb_img_src(self, index: int = 0) -> str:
        img = self.page.locator(self.CARD).nth(index).locator(f"{self.CARD_THUMB} img")
        return img.get_attribute("src") or "" if img.count() else ""

    def card_action_labels(self, index: int = 0) -> list:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BTN).all_inner_texts()

    def card_view_details_link(self, index: int = 0):
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BTN).nth(0)

    def card_download_link(self, index: int = 0):
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BTN).nth(1)

    def card_view_details_href(self, index: int = 0) -> str:
        return self.card_view_details_link(index).get_attribute("href") or ""

    def card_download_href(self, index: int = 0) -> str:
        return self.card_download_link(index).get_attribute("href") or ""

    def card_view_details_target(self, index: int = 0) -> str:
        return self.card_view_details_link(index).get_attribute("target") or ""

    def card_btn_box(self, index: int, btn_index: int) -> dict:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BTN).nth(btn_index).bounding_box()

    # ---- Empty / no-results states -----------------------------------------
    def groups_area_text(self) -> str:
        return self.page.locator(self.GROUPS).inner_text()

    def is_groups_area_empty_of_cards(self) -> bool:
        return self.card_count() == 0

    # ---- Load More -----------------------------------------------------------
    def is_load_more_visible(self) -> bool:
        return self.is_visible(self.LOAD_MORE)

    def click_load_more(self) -> "ExportReportsPage":
        self.click(self.LOAD_MORE)
        self.page.wait_for_timeout(700)
        return self

    # ---- Layout / responsive helpers ---------------------------------------
    def has_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > window.innerWidth + 1"
        )

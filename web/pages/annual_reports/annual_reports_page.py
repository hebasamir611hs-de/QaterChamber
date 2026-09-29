"""
web/pages/annual_reports/annual_reports_page.py — AnnualReportsPage.

Public-frontend Page Object for PBI 130712 ("QC - Insights & Media - 004 -
Annual Reports"), at `/web/qatar-chamber/annual-reports`
(AR: `/ar/web/qatar-chamber/annual-reports`). The real path was NOT the
naively-guessed slug set (`/web/qatar-chamber/annual-report(s)` alone 404s
into the site's generic shell) — it was resolved from the live homepage's
own rendered nav anchors (`a[href]` whose text/href matched /report/i),
mirroring photo_albums_listing_page.py's and gm_message_page.py's precedent
for a hover-only nav this project's extractor can't walk on its own.

Locators: a scripted DOM-class probe (`page.eval_on_selector_all('[class*=qc-]',
...)`) against the live page (CLI-first, 2026-09-22, framework's default
1920x1080 viewport) confirmed the real, stable `qc-ar-*` custom classes
below — same technique photo_albums_listing_page.py's `qc-pgl-*` probe and
gm_message_page.py's `qc-gm-*` probe already used, no MCP fallback needed.
`tools/extract_locators.py`'s default anchor/button/input harvest returns
only header/footer chrome plus the search input on this page (confirmed via
one CLI run first) — the page's own hero/archive/card markup is not
`<a>/<button>/<input>` with a distinguishing accessible name of its own, the
same class of page photo_albums/gm_message already document.

Confirmed live 2026-09-22 (headless Chromium via Playwright, no MCP):

    header.qc-ar-hero
        nav.qc-ar-crumbs > a.qc-ar-crumb (Home), a.qc-ar-crumb (current, Insights & Media)
        div.qc-ar-hero-grid > div.qc-ar-hero-copy
            span.qc-ar-eyebrow ("Insights & Media")
            h1.qc-ar-hero-title ("Annual Reports")
            p.qc-ar-hero-desc (hero description paragraph)
            div.qc-ar-hero-art (banner art/background)
    section.qc-ar-archive
        div.qc-ar-archive-top > div.qc-ar-archive-header
            span.qc-ar-archive-badge ("Report archive")
            h2.qc-ar-archive-title ("Institutional reporting by year")
            p.qc-ar-archive-desc (archive description paragraph)
        div.qc-ar-search-wrap > span.qc-ar-search-icon, input.qc-ar-search-input[placeholder="Search.."]
        div.qc-ar-grid (CSS grid; confirmed 3 tracks @1920, 2 @768, 1 @375)
            a.qc-ar-card (repeated)
                div.qc-ar-card-thumb
                div.qc-ar-card-body
                    h3.qc-ar-card-title ("Annual Report <year>")
                    p.qc-ar-card-desc
                    div.qc-ar-card-meta ("PDF • <size> • <n> Pages")
                    div.qc-ar-card-actions
                        a.qc-ar-btn.qc-ar-btn--outline (x2 per card: "View Details" then "Download")
            div.qc-ar-empty (empty-state message; only rendered inside the grid
                when zero cards match)
        button.qc-ar-load-more (confirmed live `hidden`/not-visible on this
            environment — all 6 real published reports fit on a single page,
            see module's "Live data" note below)

Live data set confirmed 2026-09-22 (qcdev, 6 published Annual Report entries
— no more, no fewer; the admin entries list additionally shows 6 unrelated
`UNPUBLISHED` rows with garbage titles like "ddddddddddddddd"/"wwwwwww"
created 2026-09-20, evidently leftover scratch data from an earlier,
interrupted exploration session — NOT touched by this batch, flagged to the
user rather than deleted per this project's destructive-ops confirmation
rule):

    Annual Report 2025 | Annual Report 2024 | Annual Report 2023 |
    Annual Report 2022 | Annual Report 2021 | Annual Report 2020
    (strictly descending by year, left-to-right/top-to-bottom in the grid —
    matches tc_143610's own stated expectation exactly, no substitution
    needed for that case)

Each card's meta line reads "PDF • 2 MB • 20 Pages" (identical across all 6
live entries) — real per-card descriptions differ (see
test_annual_reports_web.py's module docstring for the one used per test,
e.g. the 2024 entry's description is the only one containing the word
"advocacy", used as this environment's real substitute for cases whose own
example search keyword ("sustainability", etc.) does not exist here).

Card actions: "View Details" is a real `<a target="_blank">` pointing at the
report's own PDF asset (opens a new tab/preview, never triggers a file
download itself); "Download" is a real `<a>` (no `target`) to the SAME PDF
asset with `&download=true` appended (triggers a browser file download,
never a preview) — confirmed live via `getAttribute` reads on both anchors
of the same card, no click needed to establish the mechanism.

Empty-state message — CONFIRMED LIVE MISMATCH vs. several QA cases' stated
wording (not silently corrected, scripted honestly per Result Integrity —
see test module for the exact per-case disclosure):
    EN live: "No reports found matching your search."
        (cases 143580/143605 state: "No reports found for the selected search.")
    AR live: "لم يتم العثور على تقارير تطابق بحثك."
        (case 143831 states: "لا توجد تقارير مطابقة لبحثك.")

Load More is confirmed `hidden` on initial load (all 6 published reports
render on a single page) — cases whose own precondition requires Load More
to be interactively clickable (143577's default-state Figma check, 143603's
"reveal more", 143791's rapid-double-click-no-dup, 143796's "exactly one
report hides Load More") are SKIPPED in the test module with that reason,
mirroring photo_albums_listing_page.py's own precedent for the identical
situation.

Mobile viewport (375px) tap targets: each card's "View Details"/"Download"
buttons render at height 36px (confirmed live via `bounding_box()`) — BELOW
the >=44px tap-target minimum tc_143586 states; scripted per the case's own
expectation, expected to fail honestly rather than being loosened to match.
"""

from config.settings import web_url
from core.web.base_page import BasePage

ANNUAL_REPORTS_PATH = "/web/qatar-chamber/annual-reports"


class AnnualReportsPage(BasePage):
    # ---- Hero -------------------------------------------------------------
    HERO = ".qc-ar-hero"
    CRUMBS_NAV = ".qc-ar-crumbs"
    CRUMB = ".qc-ar-crumb"
    EYEBROW = ".qc-ar-eyebrow"
    HERO_TITLE = ".qc-ar-hero-title"
    HERO_DESC = ".qc-ar-hero-desc"
    HERO_ART = ".qc-ar-hero-art"

    # ---- Archive section ----------------------------------------------------
    ARCHIVE = ".qc-ar-archive"
    ARCHIVE_BADGE = ".qc-ar-archive-badge"
    ARCHIVE_TITLE = ".qc-ar-archive-title"
    ARCHIVE_DESC = ".qc-ar-archive-desc"
    SEARCH_INPUT = ".qc-ar-search-input"

    # ---- Grid / cards -------------------------------------------------------
    GRID = ".qc-ar-grid"
    CARD = ".qc-ar-card"
    CARD_THUMB_IMG = ".qc-ar-card-thumb img"
    CARD_TITLE = ".qc-ar-card-title"
    CARD_DESC = ".qc-ar-card-desc"
    CARD_META = ".qc-ar-card-meta"
    CARD_BTN = ".qc-ar-btn"
    EMPTY = ".qc-ar-empty"
    LOAD_MORE = ".qc-ar-load-more"

    # ---- Navigation -----------------------------------------------------
    def open_annual_reports(self, locale: str = "en") -> "AnnualReportsPage":
        self.open(web_url(ANNUAL_REPORTS_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    # ---- Hero / breadcrumb queries -----------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def eyebrow_text(self) -> str:
        return self.text(self.EYEBROW)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_desc_text(self) -> str:
        return self.text(self.HERO_DESC)

    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.CRUMBS_NAV)

    def breadcrumb_texts(self) -> list:
        return self.page.locator(self.CRUMB).all_text_contents()

    def eyebrow_style(self) -> dict:
        return self.page.locator(self.EYEBROW).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def hero_title_style(self) -> dict:
        return self.page.locator(self.HERO_TITLE).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def hero_desc_style(self) -> dict:
        return self.page.locator(self.HERO_DESC).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def breadcrumb_style(self) -> dict:
        return self.page.locator(self.CRUMB).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    # ---- Archive section queries --------------------------------------------
    def archive_badge_text(self) -> str:
        return self.text(self.ARCHIVE_BADGE)

    def archive_title_text(self) -> str:
        return self.text(self.ARCHIVE_TITLE)

    def archive_desc_text(self) -> str:
        return self.text(self.ARCHIVE_DESC)

    def archive_badge_style(self) -> dict:
        return self.page.locator(self.ARCHIVE_BADGE).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def archive_title_style(self) -> dict:
        return self.page.locator(self.ARCHIVE_TITLE).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def archive_desc_style(self) -> dict:
        return self.page.locator(self.ARCHIVE_DESC).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def search_input_style(self) -> dict:
        return self.page.locator(self.SEARCH_INPUT).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {borderWidth: cs.borderWidth, borderColor: cs.borderColor, "
            "borderRadius: cs.borderRadius}; }"
        )

    # ---- Search -------------------------------------------------------------
    def search_placeholder(self) -> str:
        return self.get_attribute(self.SEARCH_INPUT, "placeholder") or ""

    def search(self, term: str) -> "AnnualReportsPage":
        self.type(self.SEARCH_INPUT, term)
        self.page.wait_for_timeout(600)  # client-side filter re-render, no navigation to wait_for_url on
        return self

    def clear_search(self) -> "AnnualReportsPage":
        self.type(self.SEARCH_INPUT, "")
        self.page.wait_for_timeout(600)
        return self

    def search_value(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).input_value()

    def focus_search(self) -> "AnnualReportsPage":
        self.page.locator(self.SEARCH_INPUT).click()
        return self

    def is_search_focused(self) -> bool:
        return self.is_focused(self.SEARCH_INPUT)

    def search_focus_style(self) -> dict:
        return self.page.locator(self.SEARCH_INPUT).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {borderColor: cs.borderColor, outlineStyle: cs.outlineStyle, "
            "boxShadow: cs.boxShadow}; }"
        )

    # ---- Grid / cards -------------------------------------------------------
    def grid_template_columns(self) -> str:
        return self.page.locator(self.GRID).first.evaluate(
            "el => getComputedStyle(el).gridTemplateColumns"
        )

    def grid_column_count(self) -> int:
        return len(self.grid_template_columns().split())

    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return self.page.locator(self.CARD_TITLE).all_text_contents()

    def card_index_by_title(self, title: str) -> int:
        return self.card_titles().index(title)

    def card_desc(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_DESC).inner_text()

    def card_meta(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_META).inner_text()

    def card_action_labels(self, index: int) -> list:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BTN).all_text_contents()

    def card_thumb_src(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_THUMB_IMG).get_attribute("src") or ""

    def hero_background_image(self) -> str:
        return self.page.locator(self.HERO).first.evaluate(
            "el => getComputedStyle(el).backgroundImage"
        )

    def card_view_details_link(self, index: int):
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BTN).nth(0)

    def card_download_link(self, index: int):
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BTN).nth(1)

    def card_view_details_href(self, index: int) -> str:
        return self.card_view_details_link(index).get_attribute("href") or ""

    def card_download_href(self, index: int) -> str:
        return self.card_download_link(index).get_attribute("href") or ""

    def card_view_details_target(self, index: int) -> str:
        return self.card_view_details_link(index).get_attribute("target") or ""

    def card_download_target(self, index: int) -> str:
        return self.card_download_link(index).get_attribute("target") or ""

    def card_title_style(self, index: int = 0) -> dict:
        return self.page.locator(self.CARD_TITLE).nth(index).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def card_desc_style(self, index: int = 0) -> dict:
        return self.page.locator(self.CARD_DESC).nth(index).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def card_meta_style(self, index: int = 0) -> dict:
        return self.page.locator(self.CARD_META).nth(index).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def card_btn_style(self, index: int = 0) -> dict:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BTN).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {backgroundColor: cs.backgroundColor, borderWidth: cs.borderWidth, "
            "borderColor: cs.borderColor, borderRadius: cs.borderRadius, "
            "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

    def card_btn_box(self, index: int, btn_index: int) -> dict:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BTN).nth(btn_index).bounding_box()

    # ---- Empty state --------------------------------------------------------
    def is_empty_state_visible(self) -> bool:
        return self.is_visible(self.EMPTY)

    def empty_text(self) -> str:
        return self.text(self.EMPTY)

    # ---- Load More -----------------------------------------------------------
    def is_load_more_visible(self) -> bool:
        return self.is_visible(self.LOAD_MORE)

    def click_load_more(self) -> "AnnualReportsPage":
        self.click(self.LOAD_MORE)
        self.page.wait_for_timeout(600)
        return self

    def load_more_style(self) -> dict:
        return self.page.locator(self.LOAD_MORE).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {backgroundColor: cs.backgroundColor, borderWidth: cs.borderWidth, "
            "borderColor: cs.borderColor, borderRadius: cs.borderRadius, "
            "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color}; }"
        )

"""
web/pages/al_moltaqa_magazine/al_moltaqa_magazine_page.py — AlMoltaqaMagazinePage.

Public-frontend Page Object for PBI 130710 ("QC - Insights & Media - 002 -
Al-Moltqa Magazine"), at `/web/qatar-chamber/al-moltaqa-magazine` (AR:
`/ar/web/qatar-chamber/al-moltaqa-magazine`). The real path was resolved
CLI-first from the live homepage's own rendered nav anchors (`page.eval_on_selector_all("a", ...)`
against the real Insights & Media dropdown, no MCP fallback needed) — same
technique this project's other Insights & Media Page Objects document.

Locators: a scripted DOM-class probe (`page.eval_on_selector_all('[class*=qc-]', ...)`)
against the live page (CLI-first, 2026-09-22, framework's default 1920x1080
viewport) confirmed the real, stable `qc-ma-*` custom classes below.

Confirmed live 2026-09-22 (headless Chromium via Playwright, no MCP):

    header.qc-ma-hero > div.qc-ma-hero-inner
        h1.qc-ma-hero-title ("Al-Moltaqa Magazine")
        nav.qc-ma-hero-breadcrumb
            a.qc-ma-hero-bc-home ("Home")
            span.qc-ma-hero-bc-sep
            span.qc-ma-hero-bc-current ("Insights & Media" — a plain <span>,
                NOT a link, same class of finding as
                web/pages/publications/publications_page.py's own
                "Insights & Media" breadcrumb segment)
    section.qc-ma-latest > div.qc-ma-latest-inner
        div.qc-ma-latest-cover > img.qc-ma-latest-img
        div.qc-ma-latest-body > div.qc-ma-latest-info
            div.qc-ma-badges
                span.qc-ma-badge.qc-ma-badge--latest ("Latest Issue")
                span.qc-ma-badge.qc-ma-badge--issue-num ("Issue #68")
            h2.qc-ma-latest-title
            p.qc-ma-latest-desc
            div.qc-ma-meta-row (span.qc-ma-meta-item x3, span.qc-ma-meta-sep
                between each — "May 2026" / "48 pages" / "12 Articles")
            div.qc-ma-latest-actions
                a.qc-ma-btn.qc-ma-btn--primary ("Read Online", target=_blank,
                    href resolves to the real PDF asset)
                a.qc-ma-btn.qc-ma-btn--outline ("Download PDF", no target,
                    same href + "&download=true")
    section.qc-ma-archive > div.qc-ma-archive-inner
        div.qc-ma-archive-head > h2.qc-ma-archive-heading ("Magazine Archive")
        div.qc-ma-search
            input.qc-ma-search-input (placeholder "Search.." — TWO trailing
                dots, CONFIRMED LIVE — see mismatch note below)
            button.qc-ma-search-btn
        div.qc-ma-grid > div.qc-ma-card (repeated)
            div.qc-ma-card-cover > img.qc-ma-card-img
            div.qc-ma-card-body > div.qc-ma-card-content-group
                h3.qc-ma-card-title
                p.qc-ma-card-desc
                div.qc-ma-card-meta (month/year, page count, article count)
            div.qc-ma-card-foot > div.qc-ma-card-actions
                a.qc-ma-icon-btn (x2, ICON-ONLY — CONFIRMED LIVE no visible
                    inner text, unlike the Latest Issue card's own
                    qc-ma-btn's real "Read Online"/"Download PDF" text.
                    Real accessible name is on `aria-label`, confirmed live:
                    "Read Online – <card title>" (target=_blank, href
                    resolves to the issue's own PDF, carrying
                    `objectEntryExternalReferenceCode=<admin entry code>`)
                    and "Download PDF – <card title>" (no target, same href
                    + "&download=true") — resolved by aria-label, never by
                    inner text, for these two.
        div.qc-ma-empty (no-results message, class present but not directly
            probed live this session for its exact text)
        div.qc-ma-load-more-wrap > button.qc-ma-load-more ("Load More" —
            CONFIRMED LIVE present in the DOM but HIDDEN with the current 7
            real published entries (1 Latest Issue + 6 Archive cards exactly
            filling the current page size) — same class of finding as
            annual_reports_page.py's own always-hidden Load More.)

CONFIRMED LIVE REAL DATA (2026-09-22, qcdev, 7 published Magazine Issue
entries, externalReferenceCode QCDEMO-130710-ISSUE-001..007, no leftover
scratch rows): Latest Issue = "Economic Magazine" (Issue #68, May 2026, 48
pages, 12 Articles) — matches several cases' own stated Latest-Issue data
exactly. HOWEVER every one of the 6 real Archive cards ALSO carries the
"Issue #68" badge and the identical May 2026 / 48 pages / 12 Articles meta
line — only the Title/Description differ per card ("Industry, Trade &
Growth", "Qatar's Business Outlook", "Connecting Global Markets", "Made in
Qatar", "Digital Business Transformation", "Enterprise & Innovation") — a
confirmed real content-data characteristic of this environment's demo data,
NOT the case-assumed data set (several cases assume a distinct "Issue #67
Trade & Industry Review" Archive entry, which does not exist live). Tests
needing genuinely distinct issue numbers/dates (sort order, Latest-Issue
re-designation, search-by-issue-number) publish their own DISPOSABLE
QCTEST-prefixed issues via MagazineIssueAdminPage rather than relying on
this real static data — mirrors this project's Export Reports/Publications/
Annual Reports precedent. Tests that only need "a" real Archive card's full
element inventory use the real live card at index 0 ("Industry, Trade &
Growth" / badge "Issue #68") instead of the case's own literal "Issue #67
Trade & Industry Review" example — disclosed per-case in the test module,
never silently substituted.

CONFIRMED LIVE MISMATCH vs. several cases' stated wording (not silently
corrected — scripted honestly per Result Integrity):
  - Search placeholder: real "Search.." (TWO trailing dots) vs. several
    cases' stated "Search..." (three dots/ellipsis).
  - The "Insights & Media" breadcrumb segment is a plain <span>, not a link
    — only "Home" is a real, clickable <a> (matches Publications' own
    confirmed finding for the identical breadcrumb component).

No separate "Al-Moltaqa Magazine Page" admin singleton exists (see
cms/pages/al_moltaqa_magazine/magazine_issue_admin_page.py's module
docstring for the exhaustive Objects Home nav search) — every hero/archive-
heading/search-placeholder string on this page is confirmed hard-coded in
the frontend, not CMS-driven. Cases assuming a "Magazine Page" settings
admin surface (Page Title EN/AR save+validation) are SKIPPED in the test
module with that finding, mirroring export_reports_page_admin_page.py's own
"no Search Placeholder field" precedent taken one step further (no
page-level object AT ALL here, not just one missing field on it).
"""

from config.settings import web_url
from core.web.base_page import BasePage

MAGAZINE_PATH = "/web/qatar-chamber/al-moltaqa-magazine"


class AlMoltaqaMagazinePage(BasePage):
    # ---- Hero ---------------------------------------------------------------
    HERO = ".qc-ma-hero"
    HERO_TITLE = ".qc-ma-hero-title"
    BREADCRUMB = ".qc-ma-hero-breadcrumb"
    BC_HOME = ".qc-ma-hero-bc-home"
    BC_CURRENT = ".qc-ma-hero-bc-current"

    # ---- Latest Issue card ----------------------------------------------------
    LATEST = ".qc-ma-latest"
    LATEST_BADGE = ".qc-ma-latest .qc-ma-badge"
    LATEST_BADGE_LATEST = ".qc-ma-badge--latest"
    LATEST_BADGE_ISSUE_NUM = ".qc-ma-badge--issue-num"
    LATEST_TITLE = ".qc-ma-latest-title"
    LATEST_DESC = ".qc-ma-latest-desc"
    LATEST_META_ROW = ".qc-ma-meta-row"
    LATEST_META_ITEM = ".qc-ma-meta-item"
    LATEST_ACTIONS = ".qc-ma-latest-actions"
    LATEST_BTN = ".qc-ma-latest-actions .qc-ma-btn"
    LATEST_READ_ONLINE = ".qc-ma-btn--primary"
    LATEST_DOWNLOAD = ".qc-ma-btn--outline"

    # ---- Archive section ----------------------------------------------------
    ARCHIVE = ".qc-ma-archive"
    ARCHIVE_HEADING = ".qc-ma-archive-heading"
    SEARCH_INPUT = ".qc-ma-search-input"
    GRID = ".qc-ma-grid"
    CARD = ".qc-ma-card"
    CARD_TITLE = ".qc-ma-card-title"
    CARD_DESC = ".qc-ma-card-desc"
    CARD_META = ".qc-ma-card-meta"
    CARD_ACTION = ".qc-ma-icon-btn"
    EMPTY = ".qc-ma-empty"
    LOAD_MORE = ".qc-ma-load-more"

    # ---- Navigation -----------------------------------------------------
    # CONFIRMED LIVE 2026-09-22: this project's shared `.auth/state.json`
    # session (an account whose stored Control Panel/site locale preference
    # is Arabic — see magazine_issue_admin_page.py's own docstring for the
    # identical finding on the admin surface) makes THIS PUBLIC page
    # redirect to /ar/... even when `web_url(..., locale="en")` requests no
    # /ar prefix — an authenticated-session locale-preference coupling, not
    # a per-request one. An explicit `?languageId=<id>` query param
    # (Liferay's own locale-override mechanism) reliably forces the
    # requested language's CONTENT regardless of the session's stored
    # preference (confirmed live: hero/archive/card text all render in the
    # requested language with this param present) — used on every
    # navigation below so a test's outcome never depends on which account
    # last saved a locale preference into the shared auth state file.
    # NOTE: the rendered `<html dir>` attribute was observed to still read
    # "rtl" under this override even with `languageId=en_US`-forced English
    # text (CONFIRMED LIVE) — a real, disclosed quirk of the override path
    # specifically; `html_dir()` is therefore only asserted against in the
    # AR-locale test cases below, never asserted as "ltr" in the EN cases.
    _LANGUAGE_ID = {"en": "en_US", "ar": "ar_SA"}

    def open_magazine(self, locale: str = "en") -> "AlMoltaqaMagazinePage":
        url = web_url(MAGAZINE_PATH, locale=locale) + f"?languageId={self._LANGUAGE_ID[locale]}"
        self.open(url)
        self.wait_for(self.HERO_TITLE)
        return self

    def open_magazine_anonymous(self, locale: str = "en") -> "AlMoltaqaMagazinePage":
        """Same navigation, but through `open_anonymous()` — see
        standards.md's "Draft/Unpublish Public-Visibility Checks" rule.
        Callers pass a `page` from a fresh `new_context(use_auth_state=False)`.
        An anonymous context has no stored locale preference to begin with,
        but the same `languageId` override is applied for consistency."""
        url = web_url(MAGAZINE_PATH, locale=locale) + f"?languageId={self._LANGUAGE_ID[locale]}"
        self.open_anonymous(url)
        self.wait_for(self.HERO_TITLE)
        return self

    # ---- Hero queries -----------------------------------------------------
    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_title_style(self) -> dict:
        return self.page.locator(self.HERO_TITLE).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "textAlign: cs.textAlign}; }"
        )

    def breadcrumb_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.BREADCRUMB).inner_text().split("\n") if t.strip()]

    def is_bc_home_link(self) -> bool:
        return self.page.locator(self.BC_HOME).evaluate("el => el.tagName") == "A"

    def is_bc_current_link(self) -> bool:
        return self.page.locator(self.BC_CURRENT).evaluate("el => el.tagName") == "A"

    def click_bc_home(self) -> None:
        """CONFIRMED LIVE 2026-09-22: a plain `.click()` (via the BasePage
        wrapper) does not navigate — the click resolves as actionable but
        the page never leaves the magazine URL. `force=True` + an explicit
        `expect_navigation()` reliably navigates instead — the same site-
        wide chatbot-launcher pointer-event interception this project's
        Object Authoring surface already documents for its own Edit/Delete
        links (see cms/pages/components/object_authoring_page.py's module
        docstring), reproduced here for a plain public-page anchor."""
        with self.page.expect_navigation(timeout=10000):
            self.page.locator(self.BC_HOME).click(force=True)

    def html_dir(self) -> str:
        return self.page.locator("html").get_attribute("dir") or ""

    # ---- Latest Issue queries -----------------------------------------------
    def is_latest_visible(self) -> bool:
        return self.is_visible(self.LATEST)

    def latest_badges(self) -> list:
        return self.page.locator(self.LATEST_BADGE).all_inner_texts()

    def latest_title_text(self) -> str:
        return self.text(self.LATEST_TITLE)

    def latest_desc_text(self) -> str:
        return self.text(self.LATEST_DESC)

    def latest_meta_text(self) -> str:
        return self.page.locator(self.LATEST_META_ROW).inner_text()

    def latest_action_labels(self) -> list:
        return self.page.locator(self.LATEST_BTN).all_inner_texts()

    def latest_read_online_link(self):
        return self.page.locator(self.LATEST_READ_ONLINE)

    def latest_download_link(self):
        return self.page.locator(self.LATEST_DOWNLOAD)

    # ---- Archive section queries --------------------------------------------
    def archive_heading_text(self) -> str:
        return self.text(self.ARCHIVE_HEADING)

    def search_placeholder(self) -> str:
        return self.get_attribute(self.SEARCH_INPUT, "placeholder") or ""

    def search(self, term: str) -> "AlMoltaqaMagazinePage":
        self.page.locator(self.SEARCH_INPUT).fill(term)
        self.page.wait_for_timeout(700)  # client-side filter re-render, no navigation to wait_for_url on
        return self

    def clear_search(self) -> "AlMoltaqaMagazinePage":
        self.page.locator(self.SEARCH_INPUT).fill("")
        self.page.wait_for_timeout(700)
        return self

    def search_value(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).input_value()

    def focus_search(self) -> "AlMoltaqaMagazinePage":
        self.page.locator(self.SEARCH_INPUT).click()
        return self

    def is_search_focused(self) -> bool:
        return self.page.locator(self.SEARCH_INPUT).evaluate("el => el === document.activeElement")

    # ---- Cards -------------------------------------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return self.page.locator(self.CARD_TITLE).all_inner_texts()

    def card_index(self, title: str) -> int:
        titles = self.card_titles()
        return titles.index(title) if title in titles else -1

    def card_badge(self, index: int = 0) -> str:
        card = self.page.locator(self.CARD).nth(index)
        badge = card.locator("[class*=badge]")
        return badge.first.inner_text() if badge.count() else ""

    def card_title(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_TITLE).inner_text()

    def card_desc(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_DESC).inner_text()

    def card_meta(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_META).inner_text()

    def card_has_img_cover(self, index: int = 0) -> bool:
        return self.page.locator(self.CARD).nth(index).locator("img").count() > 0

    def card_actions(self, index: int = 0):
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_ACTION)

    def card_action_aria_labels(self, index: int = 0) -> list:
        actions = self.card_actions(index)
        return [actions.nth(i).get_attribute("aria-label") or "" for i in range(actions.count())]

    def card_read_online_link(self, index: int = 0):
        return self.card_actions(index).nth(0)

    def card_download_link(self, index: int = 0):
        return self.card_actions(index).nth(1)

    def card_actions_enabled(self, index: int = 0) -> bool:
        actions = self.card_actions(index)
        return all(actions.nth(i).is_enabled() for i in range(actions.count()))

    # ---- Empty / no-results states -----------------------------------------
    def is_empty_visible(self) -> bool:
        return self.is_visible(self.EMPTY)

    def empty_text(self) -> str:
        return self.text(self.EMPTY)

    # ---- Load More -----------------------------------------------------------
    def is_load_more_visible(self) -> bool:
        return self.is_visible(self.LOAD_MORE)

    def click_load_more(self) -> "AlMoltaqaMagazinePage":
        self.click(self.LOAD_MORE)
        self.page.wait_for_timeout(700)
        return self

    # ---- Layout / responsive helpers ---------------------------------------
    def has_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > window.innerWidth + 1"
        )

    def grid_column_count(self) -> int:
        """Approximates the Archive grid's rendered column count by reading
        `getComputedStyle(grid).gridTemplateColumns`'s own space-separated
        track list — used by the desktop/tablet/mobile layout cases instead
        of a fragile pixel-position comparison."""
        tracks = self.page.locator(self.GRID).evaluate(
            "el => getComputedStyle(el).gridTemplateColumns"
        )
        return len([t for t in tracks.split(" ") if t.strip()]) if tracks else 0

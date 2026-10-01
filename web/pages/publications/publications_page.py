"""
web/pages/publications/publications_page.py — PublicationsPage.

Public-frontend Page Object for PBI 130711 ("QC - Insights & Media - 003 -
Publications"), at `/web/qatar-chamber/publications` (AR:
`/ar/web/qatar-chamber/publications`). The real path was resolved CLI-first
from the live homepage's own rendered "Explore Publications" link
(`get_by_role("link", name="Explore Publications")` -> href) — no MCP
fallback needed, same technique this project's sibling Insights & Media
pages document.

Locators: a scripted DOM-class probe (`page.eval_on_selector_all('[class*=qc-]',
...)`) against the live page (CLI-first, 2026-09-22, framework's default
1920x1080 viewport) confirmed the real, stable `qc-imp-*` ("Insights & Media
Publications") custom classes below.

Confirmed live 2026-09-22 (headless Chromium via Playwright, no MCP):

    .qc-imp-hero-inner
        .qc-imp-hero-title ("Publications")
    .qc-imp-crumbs
        a.qc-imp-crumb-home (real <a href="/web/qatar-chamber">, "Home")
        span.qc-imp-crumb-current ("Insights & Media" — CONFIRMED LIVE this
            is a plain <span>, NOT a link/button — no href, no role=link,
            no click handler observed. tc_143983's own stated expected
            result ("both links are clickable" / "click 'Insights & Media'
            ... navigates to the Insights & Media landing page") is
            confirmed FALSE for this half — scripted honestly per Result
            Integrity, not silently dropped; see test module.)
    .qc-imp-body > .qc-imp-shell
        .qc-imp-controls
            .qc-imp-search .qc-imp-search-input (placeholder "Search
                Publications..."; the placeholder's real, AUTHORED color is
                a CSS custom property `--imp-quiet` = #a8a8a7, exactly
                matching tc_143984's stated value — CONFIRMED LIVE this
                project's headless Chromium `getComputedStyle(el,
                "::placeholder")` does NOT resolve a distinct value in this
                harness (returns the INPUT's own regular text color instead,
                reproduced twice) - reading the `--imp-quiet` custom
                property directly (placeholder_color() below) is the
                verified, reliable technique; a bare pseudo-element
                getComputedStyle call would have produced a FALSE bug
                report here.)
            .qc-imp-cat select.qc-imp-select (aria-label "Filter by
                category"; options "All Categories", "Research Papers",
                "Guides", "Reports", "White Papers", "Manuals" — 6 options,
                CONFIRMED LIVE NO "Brochures" option exists on this public
                filter, even though the Object Authoring "Publication Type"
                combobox on the admin side (see publication_admin_page.py)
                DOES list an 8th "Brochure" option, plus "Report"/"Bulletin"/
                "Study" that never surface here at all — a real, confirmed
                content-model gap between the admin Type enum and what the
                public page's category filter/chip strip expose. tc_143981's
                own stated expected chip list includes "Brochures", which
                this environment does not have — scripted honestly, not
                invented.)
            .qc-imp-sort select (options "Latest First"/"Most Downloaded")
        .qc-imp-chipstrip .qc-imp-chips
            .qc-imp-chip[data-type=all|researchPaper|guides|report|
                whitePaper|manuals][aria-pressed] (6 chips: "All
                Publications", "Research Papers", "Guides", "Reports",
                "White Papers", "Manuals" — same missing-"Brochures" gap as
                the category dropdown, confirmed live. Active chip:
                background rgb(145,23,49)/text #FFFFFF; inactive chip text
                rgb(108,108,107) = #6C6C6B, exactly matching tc_143986.)
        .qc-imp-grid
            .qc-imp-card (repeated; 9 real live entries confirmed
                2026-09-22, 8 Published + 1 Draft "Arbitration Best
                Practices" not rendered here)
                .qc-imp-cover > img.qc-imp-cover-img (real cover thumbnail
                    on every real card — no SVG-placeholder path observed
                    on this object, unlike the sibling Export Reports page)
                .qc-imp-card-body
                    .qc-imp-card-top
                        span.qc-imp-badge (Type badge — CONFIRMED LIVE this
                            reads the SINGULAR admin Type value verbatim,
                            e.g. "Report", "Research Paper", "White Paper",
                            never the public filter's own PLURAL category
                            labels — a second, separate confirmed mismatch
                            from the category-dropdown one above, e.g.
                            tc_143988's own stated badge "Research Papers"
                            for a Type=Research Papers record actually
                            renders "Research Paper", singular.)
                        .qc-imp-card-head
                            h3.qc-imp-card-title
                            .qc-imp-meta (LTR-forced spans joined by
                                .qc-imp-meta-dot separators: File Type,
                                File Size, "<n> View", "<n> Download" — no
                                plural "s" at any count, confirmed live at
                                both 3 and 49)
                    .qc-imp-actions
                        a.qc-imp-action (x2: "View Details" -> a REAL
                            internal detail page
                            `/web/qatar-chamber/publication-detail?id=<id>`,
                            same-tab navigation, no `target` attribute
                            (CONFIRMED LIVE — unlike the sibling Export
                            Reports/Annual Reports pages, whose own "View
                            Details" opens a NEW tab straight to the raw PDF;
                            this object's "View Details" is a same-tab
                            navigation to a real, separate detail page that
                            itself renders Type/Title/Date/View-count/
                            Description/its own Download button); "Download"
                            -> the real PDF/cover asset, `target="_blank"`,
                            `&download=true` in the query string, same
                            download mechanism as the sibling pages)
        .qc-imp-empty (shown when the grid is empty — title "No results
            found", hint "We could not find any publication matching your
            search or filters. Try a different keyword or category.",
            "Clear filters" reset link/button — CONFIRMED LIVE EN wording;
            AR: "لا توجد نتائج" / "لم نتمكن من العثور على أي منشور يطابق
            بحثك أو عوامل التصفية. جرّب كلمة مفتاحية أو فئة أخرى." /
            "إعادة تعيين")
        .qc-imp-more (button "Load More" — CONFIRMED LIVE HIDDEN on this
            environment with the current 8 real Published entries: the
            page size is >= 8, so a real >8-entry precondition for
            tc_143987/tc_144062/tc_144063 needs QCTEST- disposable entries
            pushing the Published count past the page's own page-size,
            mirroring export_reports_page.py's own precedent for creating
            disposable data to reach an otherwise-unreachable UI state)
        .qc-imp-status ("<n> publications shown")

Publication Detail page (`/web/qatar-chamber/publication-detail?id=<id>`),
confirmed live via direct navigation: renders "Back to Publications" link,
the Type badge, Title, Publication Date, current View/Download count,
Description, and its own "Download" action — a real, separate page, not an
iframe/embed of the listing.

AR locale confirmed live 2026-09-22: `dir="rtl"`, hero "المنشورات", crumbs
"الرئيسية" / "الرؤى والإعلام", search placeholder "...البحث في المنشورات",
chips ['جميع المنشورات', 'أوراق بحثية', 'إرشادات', 'تقارير', 'أوراق بيضاء',
'أدلة'], empty-state heading "لا توجد نتائج" (matches tc_144082's own stated
Arabic no-match message exactly).
"""

from config.settings import web_url
from core.web.base_page import BasePage

PUBLICATIONS_PATH = "/web/qatar-chamber/publications"


class PublicationsPage(BasePage):
    # ---- Hero / breadcrumb --------------------------------------------------
    HERO_TITLE = ".qc-imp-hero-title"
    CRUMBS = ".qc-imp-crumbs"
    CRUMB_HOME = ".qc-imp-crumb-home"
    CRUMB_CURRENT = ".qc-imp-crumb-current"

    # ---- Controls -----------------------------------------------------------
    SEARCH_INPUT = ".qc-imp-search-input"
    CATEGORY_SELECT = ".qc-imp-cat select"
    SORT_SELECT = ".qc-imp-sort select"
    CHIPS = ".qc-imp-chip"
    ACTIVE_CHIP = '.qc-imp-chip[aria-pressed="true"]'

    # ---- Grid / cards ---------------------------------------------------------
    GRID = ".qc-imp-grid"
    CARD = ".qc-imp-card"
    CARD_COVER_IMG = ".qc-imp-cover-img"
    CARD_BADGE = ".qc-imp-badge"
    CARD_TITLE = ".qc-imp-card-title"
    CARD_META = ".qc-imp-meta"
    CARD_ACTION = ".qc-imp-action"

    # ---- Empty state / Load More ---------------------------------------------
    EMPTY = ".qc-imp-empty"
    EMPTY_TITLE = ".qc-imp-empty-title"
    EMPTY_HINT = ".qc-imp-empty-hint"
    EMPTY_RESET = ".qc-imp-empty-reset"
    LOAD_MORE = ".qc-imp-more"
    STATUS = ".qc-imp-status"

    # ---- Navigation -----------------------------------------------------
    def open_publications(self, locale: str = "en") -> "PublicationsPage":
        self.open(web_url(PUBLICATIONS_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_publications_anonymous(self, locale: str = "en") -> "PublicationsPage":
        """Same navigation, but through `open_anonymous()` — see
        standards.md's "Draft/Unpublish Public-Visibility Checks" rule."""
        self.open_anonymous(web_url(PUBLICATIONS_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    def wait_for_results(self, timeout_ms: int = 30000) -> "PublicationsPage":
        """ADDED 2026-09-30 (PBI 130711 heal): the grid is filled by a client
        fetch after the hero renders, so a card read straight after
        open_publications() can see an EMPTY grid — which makes an
        "is absent" check pass vacuously. Waits until the grid shows at least
        one card OR the empty state."""
        self.page.locator(f"{self.CARD}, {self.EMPTY}").first.wait_for(state="visible", timeout=timeout_ms)
        return self

    # ---- Hero / breadcrumb queries -------------------------------------------
    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_title_style(self) -> dict:
        return self.page.locator(self.HERO_TITLE).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight}; }"
        )

    def breadcrumb_style(self) -> dict:
        return self.page.locator(self.CRUMBS).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight}; }"
        )

    def breadcrumb_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.CRUMBS).inner_text().split("\n") if t.strip()]

    def click_crumb_home(self) -> None:
        self.page.locator(self.CRUMB_HOME).click()

    def is_crumb_current_a_link(self) -> bool:
        """CONFIRMED LIVE this element is a plain <span> — see module
        docstring's tc_143983 mismatch note."""
        tag = self.page.locator(self.CRUMB_CURRENT).evaluate("el => el.tagName")
        return tag.lower() == "a"

    def html_dir(self) -> str:
        return self.page.locator("html").get_attribute("dir") or ""

    # ---- Controls queries -----------------------------------------------------
    def search_placeholder_text(self) -> str:
        return self.get_attribute(self.SEARCH_INPUT, "placeholder") or ""

    def search_placeholder_color(self) -> str:
        """The real, AUTHORED placeholder color, read via the CSS custom
        property the stylesheet actually assigns (`--imp-quiet`) — see
        module docstring: a bare `getComputedStyle(el, '::placeholder')`
        does not resolve distinctly in this headless harness (confirmed
        live, returns the input's own regular text color instead)."""
        return self.page.locator(self.SEARCH_INPUT).evaluate(
            "el => getComputedStyle(el).getPropertyValue('--imp-quiet').trim()"
        )

    def category_label_style(self) -> dict:
        return self.page.locator(self.CATEGORY_SELECT).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, color: cs.color}; }"
        )

    def sort_label_style(self) -> dict:
        return self.page.locator(self.SORT_SELECT).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, color: cs.color}; }"
        )

    def category_options(self) -> list:
        return [o.strip() for o in self.page.locator(self.CATEGORY_SELECT).all_inner_texts()[0].split("\n") if o.strip()]

    def select_category(self, label: str) -> "PublicationsPage":
        self.page.locator(self.CATEGORY_SELECT).select_option(label=label)
        self.page.wait_for_timeout(300)
        return self

    def select_sort(self, label: str) -> "PublicationsPage":
        self.page.locator(self.SORT_SELECT).select_option(label=label)
        self.page.wait_for_timeout(300)
        return self

    def search(self, term: str) -> "PublicationsPage":
        self.page.locator(self.SEARCH_INPUT).fill(term)
        self.page.wait_for_timeout(600)  # client-side filter re-render, no navigation to wait_for_url on
        return self

    def clear_search(self) -> "PublicationsPage":
        self.page.locator(self.SEARCH_INPUT).fill("")
        self.page.wait_for_timeout(600)
        return self

    # ---- Chips ----------------------------------------------------------------
    def chip_texts(self) -> list:
        return self.page.locator(self.CHIPS).all_inner_texts()

    def chip(self, label: str):
        return self.page.locator(self.CHIPS).filter(has_text=label).first

    def click_chip(self, label: str) -> "PublicationsPage":
        self.chip(label).click()
        self.page.wait_for_timeout(500)
        return self

    def active_chip_text(self) -> str:
        return self.page.locator(self.ACTIVE_CHIP).inner_text() if self.page.locator(self.ACTIVE_CHIP).count() else ""

    def chip_style(self, label: str) -> dict:
        chip = self.chip(label)
        return chip.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {backgroundColor: cs.backgroundColor, color: cs.color, fontWeight: cs.fontWeight}; }"
        )

    # ---- Cards ------------------------------------------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return self.page.locator(self.CARD_TITLE).all_inner_texts()

    def card_index(self, title: str) -> int:
        titles = self.card_titles()
        return titles.index(title) if title in titles else -1

    def card_badge(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BADGE).inner_text()

    def card_title(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_TITLE).inner_text()

    def card_meta(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_META).inner_text()

    def card_has_img_cover(self, index: int = 0) -> bool:
        return self.page.locator(self.CARD).nth(index).locator(f"img{self.CARD_COVER_IMG}").count() > 0

    def card_action_labels(self, index: int = 0) -> list:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_ACTION).all_inner_texts()

    def card_view_details_link(self, index: int = 0):
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_ACTION).nth(0)

    def card_download_link(self, index: int = 0):
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_ACTION).nth(1)

    def card_view_details_href(self, index: int = 0) -> str:
        return self.card_view_details_link(index).get_attribute("href") or ""

    def card_download_href(self, index: int = 0) -> str:
        return self.card_download_link(index).get_attribute("href") or ""

    def card_download_target(self, index: int = 0) -> str:
        return self.card_download_link(index).get_attribute("target") or ""

    def card_btn_box(self, index: int, btn_index: int) -> dict:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_ACTION).nth(btn_index).bounding_box()

    # ---- Empty / status ---------------------------------------------------------
    def is_empty_visible(self) -> bool:
        return self.is_visible(self.EMPTY)

    def empty_title_text(self) -> str:
        return self.text(self.EMPTY_TITLE)

    def status_text(self) -> str:
        return self.text(self.STATUS) if self.is_visible(self.STATUS) else ""

    # ---- Load More -----------------------------------------------------------
    def is_load_more_visible(self) -> bool:
        return self.is_visible(self.LOAD_MORE)

    def load_more_style(self) -> dict:
        return self.page.locator(self.LOAD_MORE).first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, color: cs.color}; }"
        )

    def click_load_more(self) -> "PublicationsPage":
        self.click(self.LOAD_MORE)
        self.page.wait_for_timeout(600)
        return self

    def page_background_color(self) -> str:
        return self.page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor")

    # ---- Layout / responsive helpers ---------------------------------------
    def open_detail_by_id(self, entry_id: str, locale: str = "en") -> None:
        """Direct navigation to `/web/qatar-chamber/publication-detail?id=<id>`
        — used by tc_143995 with an id resolved purely from the admin
        Preview link (see PublicationAdminPage.row_entry_numeric_id()),
        never guessed."""
        self.open(web_url(f"/web/qatar-chamber/publication-detail?id={entry_id}", locale=locale))

    def open_detail_by_id_anonymous(self, entry_id: str, locale: str = "en") -> None:
        self.open_anonymous(web_url(f"/web/qatar-chamber/publication-detail?id={entry_id}", locale=locale))

    def detail_page_text(self) -> str:
        return self.page.locator("body").inner_text()

    def has_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > window.innerWidth + 1"
        )

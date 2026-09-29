"""web/pages/global_search/global_search_page.py — GlobalSearchPage.

Page Object for the public Global Advanced Search feature
(PBI 131055 / "QC - 001 - Global Advanced Search", GLOBAL service, Web
platform): the header's search overlay plus the `/search` results page.

The header overlay itself is NOT re-declared here — it belongs to the shared
`HeaderComponent` (`web/pages/components/header_component.py`), which this
object composes. Duplicating those locators into a page folder would be the
exact redundancy the structure & redundancy scan exists to catch.

TOOLING DISCLOSURE
------------------
Every locator and behavioural fact below was read from the SHELL — scoped
Playwright probe scripts run with `python`, reusing `BasePage.open_anonymous()`
so the license-gate/announcement-overlay handling matched the runtime path, at
the framework's default 1920x1080 viewport. `tools/extract_locators.py` alone
was not sufficient for this page: its harvester walks
`a,button,input,select,textarea,[role],[data-testid],[data-test],[aria-label],
[contenteditable]`, and almost everything a search result IS (title link aside)
is a plain `<li>/<div>/<p>` with no role and no label, while the controls the
approved cases look for (filters) are absent from the DOM entirely — a bare
candidate list cannot express "this control does not exist". Same documented
"ambiguous element / state the script can't reach" fallback
`header_component.py` already records, resolved the same way: one extra scoped
DOM read in the shell. **The Playwright MCP was reachable this session and was
NOT used at all.**

LIVE STRUCTURE (qcdev, read-only, 2026-09-23)
---------------------------------------------
`/search?q=<kw>` is served by **Liferay's stock portal-search portlets**, wired
into the page layout in this order:

    #main-content
      .lfr-layout-structure-item-...-search-bar-portlet-searchbarportlet
          -> input.search-bar-keywords-input + a submit button
      .lfr-layout-structure-item-...-customfilterportlet   x3
          -> RENDER NOTHING. Liferay's "Custom Filter" portlet is a
             configuration-only portlet: in view mode it emits an empty
             container. All three fragment divs are empty in the live DOM.
      .lfr-layout-structure-item-...-search-results-portlet-searchresultsportlet
          -> .search-total-label ("68 Results for membership")
             ul#search-results-display-list > li.list-group-item  (one result)
             .pagination-bar (.pagination-results + ul.pagination)

A result `<li>` looks like:

    li.list-group-item.list-group-item-flex
      div.autofit-col            -> span.sticker (thumbnail img, or a Clay
                                    lexicon-icon svg for non-document types)
      div.autofit-col-expand
        section.autofit-section
          div.list-group-title > a          -> the TITLE + its link
          div.search-results-metadata
            p.list-group-subtext   (#1)     -> <strong>Page</strong> · By
                                               <strong>author</strong> · On <date>
            p.list-group-subtext   (#2)     -> the SUMMARY/snippet — PRESENT
                                               ONLY on some result types

**What the approved cases expect and this build does not have** — recorded,
never "fixed" (automation-standards.md, *Result integrity*):

| Case expects | Live build |
|---|---|
| Content Type filter, Category filter, Date Range From/To, Apply, Clear Filters | **No filter UI at all.** The three Custom Filter portlets render empty divs; an exhaustive control inventory of `#main-content` returns only the keyword input, its submit button, the items-per-page dropdown and the pagination controls |
| Content types Page / Event / Publication / Service | Only **`Page`** and **`Document`** are ever emitted as the type label |
| Every result card carries a summary | The second `p.list-group-subtext` (the snippet) exists only for some types. For `q=membership`, all 20 page-1 results are `Document` and have **no** summary |
| A no-results state with ≥1 suggestion | Message only: "No results were found. No results were found that matched the keywords: `<kw>`." — no spelling tip, no browse-category link, no related-keyword links |
| Empty / whitespace-only submit does not execute a search | Both navigate to `/search` — the search IS executed |
| Clicking a result opens its content page | True for `Page` results (`/events?p_l_back_url=…`); a `Document` result's title link opens Liferay's in-portlet asset viewer (`/search?…mvcPath=/view_content.jsp&assetEntryId=…`) |

Locators for the controls this build does not render are written as **real,
resolvable Playwright selectors** (never `TODO`), broad enough to match any
reasonable implementation of the control the case names, so the corresponding
state query honestly returns `0` instead of erroring on an unresolved
constant — the same pattern `faq_page.py` and `keyboard_navigation_page.py`
established.

COUNTING, NOT WAITING
---------------------
Every "does this control exist?" query uses `locator.count()`, not
`BasePage.is_visible()`. `is_visible()` pays a bounded wait per call; with ~6
absent controls across ~10 filter tests that is pure wall-clock spent proving
a negative that is already settled once the results list has rendered. The
tests always assert the live-verifiable half (the search returned results)
BEFORE the contested half, so a red names the real finding instead of dying in
a locator timeout.
"""

from urllib.parse import quote

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.header_component import HeaderComponent

# ── Viewports the Compatibility cases name, verbatim ──────────────────────
DESKTOP_VIEWPORT = (1920, 1080)
TABLET_VIEWPORT = (768, 1024)
MOBILE_VIEWPORT = (375, 812)

# ── Site paths the cases navigate to, by their live slugs ─────────────────
HOME_PATH = "/home"
# Read off the live header nav's own hrefs rather than guessed:
#   About us -> /web/qatar-chamber/about-us   (h1 "About Qatar Chamber")
#   Events   -> /web/qatar-chamber/events     (title "Chamber Events")
# NOTE: the shorter `/chamber-events` slug also resolves but renders a
# "Coming Soon" placeholder — it is NOT the Chamber Events listing page.
ABOUT_US_PATH = "/web/qatar-chamber/about-us"
EVENTS_PATH = "/web/qatar-chamber/events"
SEARCH_PATH = "/search"


class GlobalSearchPage(BasePage):
    """Header search overlay + `/search` results page. No assertions here."""

    # ══════════════════════════════════════════════════════════════════
    # Locators — results page
    # ══════════════════════════════════════════════════════════════════
    RESULTS_PORTLET = ".portlet-search-results"
    RESULTS_BODY = ".portlet-search-results .portlet-body"
    RESULTS_LIST = "#search-results-display-list"
    RESULT_ITEMS = "#search-results-display-list > li"
    TOTAL_LABEL = ".search-total-label"

    # Relative selectors, resolved against ONE result `<li>` — never on their
    # own (every card shares these classes).
    RESULT_TITLE_LINK = ".list-group-title a"
    RESULT_SUBTEXT = "p.list-group-subtext"
    RESULT_TYPE_LABEL = "p.list-group-subtext .subtext-item strong"
    RESULT_THUMBNAIL = ".sticker img"

    # The results page's own (Liferay stock) search bar — distinct from the
    # header overlay input, which belongs to HeaderComponent.
    RESULTS_KEYWORD_INPUT = "input.search-bar-keywords-input"

    # ── Pagination (Liferay's Clay pagination bar) ─────────────────────
    PAGINATION_BAR = ".pagination-bar"
    PAGINATION_RESULTS_TEXT = ".pagination-results"
    PAGINATION_NAV = "ul.pagination"
    # Clay renders the arrows as anchors carrying a `title`; on the first
    # page the Previous arrow is a disabled <div> with the aria-label
    # instead, which is why "is there a clickable Previous?" is a count of
    # the ANCHOR form specifically.
    PAGINATION_NEXT = 'ul.pagination a[title="Next Page"]'
    PAGINATION_PREVIOUS = 'ul.pagination a[title="Previous Page"]'
    PAGINATION_PREVIOUS_DISABLED = 'ul.pagination [aria-disabled="true"][aria-label="Previous Page"]'
    PAGINATION_PAGE_LINKS = 'ul.pagination a[aria-label^="Page "]'
    ENTRIES_PER_PAGE_BUTTON = ".pagination-items-per-page button"

    # ══════════════════════════════════════════════════════════════════
    # Locators — the advanced-filter controls the CASES describe
    # ------------------------------------------------------------------
    # None of these match anything on the live build (see module docstring).
    # They are deliberately broad, intent-named selectors covering the
    # plausible implementations of each control, so a state query returns an
    # honest 0 rather than raising, and so the same tests start passing
    # unchanged the day the filter UI ships.
    # ══════════════════════════════════════════════════════════════════
    FILTERS_PANEL = (
        '[data-qc-search-filters], .search-filters, aside[class*="filter" i], '
        '[class*="search-facet" i], .portlet-search-facet'
    )
    CONTENT_TYPE_FILTER = (
        '[data-qc-filter="content-type"], select[name*="contentType" i], '
        '[aria-label*="content type" i], [class*="content-type-filter" i]'
    )
    CONTENT_TYPE_OPTION = (
        '[data-qc-filter="content-type"] [role="option"], '
        '[data-qc-filter="content-type"] input[type="checkbox"], '
        '[class*="content-type-filter" i] [role="option"], '
        '[class*="content-type-filter" i] input[type="checkbox"]'
    )
    CATEGORY_FILTER = (
        '[data-qc-filter="category"], select[name*="category" i], '
        '[aria-label*="category" i], [class*="category-filter" i]'
    )
    CATEGORY_OPTION = (
        '[data-qc-filter="category"] [role="option"], '
        '[data-qc-filter="category"] input[type="checkbox"], '
        '[class*="category-filter" i] [role="option"], '
        '[class*="category-filter" i] input[type="checkbox"]'
    )
    DATE_RANGE_FROM = (
        '[data-qc-filter="date-from"], input[name*="dateFrom" i], '
        'input[name*="from" i][type="date"], [aria-label*="from" i][type="date"]'
    )
    DATE_RANGE_TO = (
        '[data-qc-filter="date-to"], input[name*="dateTo" i], '
        'input[name*="to" i][type="date"], [aria-label*="to" i][type="date"]'
    )
    APPLY_FILTERS_BUTTON = (
        '[data-qc-filter-apply], button:has-text("Apply"), '
        '[class*="apply-filter" i]'
    )
    CLEAR_FILTERS_BUTTON = (
        '[data-qc-filter-clear], button:has-text("Clear Filters"), '
        'button:has-text("Clear all"), [class*="clear-filter" i]'
    )
    DATE_RANGE_VALIDATION_MESSAGE = (
        '[data-qc-filter-error], [class*="date" i] .form-feedback-item, '
        '[class*="date" i] .invalid-feedback, [class*="date" i][role="alert"]'
    )
    ACTIVE_FILTER_CHIPS = (
        '[data-qc-active-filter], .search-filter-chip, [class*="applied-filter" i]'
    )

    # ── No-results state ──────────────────────────────────────────────
    # Liferay emits its no-results copy as plain text inside the results
    # portlet body (no dedicated element/class), so the message is read from
    # RESULTS_BODY's text. The SUGGESTION selector below is the cases'
    # intent-based one; it matches nothing live.
    NO_RESULTS_MARKERS = ("No results were found",)
    NO_RESULTS_SUGGESTIONS = (
        '[data-qc-search-suggestions], [class*="search-suggestion" i], '
        '[class*="did-you-mean" i], [class*="no-results" i] a, '
        '[class*="spelling" i]'
    )

    # ── Mobile filter affordance (case 141843) ────────────────────────
    MOBILE_FILTERS_TOGGLE = (
        '[data-qc-filters-toggle], button:has-text("Filters"), '
        '[aria-label*="filters" i]'
    )

    # Content-type label values the cases name (Axis: the case's vocabulary,
    # NOT the site's — kept here so the tests read from one place).
    CASE_CONTENT_TYPES = ("Page", "Event", "Publication", "Service")

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)

    # ══════════════════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════════════════
    def open_home(self) -> "GlobalSearchPage":
        return self.open_site_page(HOME_PATH)

    def open_site_page(self, path: str) -> "GlobalSearchPage":
        """Open any public page anonymously and wait for its header.

        Waits on network-idle BEFORE the trailing `wait_for(HEADER)`. The
        `<header>` element is server-rendered, but the search overlay's
        open/close handler binds in script afterwards — and
        `a.qc-search-btn` carries a real `href="/search"`, so a click that
        lands before the handler binds would NAVIGATE instead of opening the
        overlay, and the overlay wait would then time out on a page whose
        overlay is still `hidden`. Same async-mount reasoning (and the same
        fix) `header_component.py` already documents for
        `switch_to_arabic()` / `open_about_us_via_nav()`."""
        self.open_anonymous(web_url(path))
        self.page.wait_for_load_state("networkidle")
        self.wait_for(self.header.HEADER)
        return self

    def open_results_for(self, keyword: str, locale: str = "en") -> "GlobalSearchPage":
        """Go straight to the results page for `keyword`.

        Used by the cases whose step is simply "Search keyword 'events'" —
        the URL the header overlay itself submits to, reached in one
        navigation instead of three. The cases that explicitly name the
        HEADER search bar go through `search_from_header()` instead, so the
        control under test is genuinely exercised."""
        self.open_anonymous(web_url(f"{SEARCH_PATH}?q={quote(keyword)}", locale=locale))
        self.wait_for_results_page()
        return self

    def wait_for_results_page(self) -> "GlobalSearchPage":
        """Wait for the results portlet to render — it holds BOTH the result
        list and the no-results message, so this settles either outcome
        without presuming which one the test expects."""
        self.wait_for(self.RESULTS_BODY, first=True)
        return self

    # ══════════════════════════════════════════════════════════════════
    # Searching through the header overlay
    # ══════════════════════════════════════════════════════════════════
    def open_search_overlay(self) -> "GlobalSearchPage":
        self.header.open_search_overlay()
        return self

    def enter_keyword(self, keyword: str) -> "GlobalSearchPage":
        self.header.type_search_keyword(keyword)
        return self

    def keyword_field_value(self) -> str:
        return self.header.search_keyword_value()

    def submit_search(self, via: str = "button") -> "GlobalSearchPage":
        """Submit the overlay. `via="button"` clicks the Search control,
        `via="enter"` presses Enter in the keyword field — the two
        submission paths case 141874 names. Deliberately does NOT wait for a
        navigation: whether one happens is what 141856/141857 assert."""
        if via == "enter":
            self.header.submit_search_by_enter()
        else:
            self.header.submit_search_by_button()
        return self

    def search_from_header(self, keyword: str, via: str = "button") -> "GlobalSearchPage":
        """Full header-bar search: open the overlay, type, submit, settle on
        the results page. Assumes a public page is already open."""
        self.open_search_overlay()
        self.enter_keyword(keyword)
        self.submit_search(via=via)
        self.wait_for_results_page()
        return self

    def url_after_submit(self, url_before: str, timeout_ms: int = 5000) -> str:
        """Bounded wait for the URL to change after a submit, returning
        whichever URL the browser actually ended on.

        This is a STATE QUERY, not a swallowed failure: the negative cases
        (141856 empty keyword, 141857 whitespace-only) expect *no*
        navigation, so "the wait expired" is a legitimate observation the
        test asserts on, not an error to hide. An explicit bounded wait — no
        `sleep`, and it returns the moment a navigation does happen, so the
        positive path costs nothing."""
        try:
            self.page.wait_for_url(lambda url: url != url_before, timeout=timeout_ms)
        except Exception:  # noqa: BLE001 — "no navigation" is the observation
            pass
        # Settle the DOM either way, so a follow-up `is_on_results_page()`
        # reads the destination rather than a half-swapped document. A no-op
        # when nothing navigated.
        self.page.wait_for_load_state("domcontentloaded")
        return self.page.url

    def is_on_results_page(self) -> bool:
        """True when the browser is on the search RESULTS page — i.e. the
        results portlet actually rendered. A URL check alone is not enough:
        the empty-keyword submit lands on `/search` with no `q` at all."""
        return self.page.locator(self.RESULTS_PORTLET).count() > 0

    def is_search_control_available(self) -> bool:
        """The header magnifier is visible AND the overlay markup exists on
        this page — the two halves of "the search bar is reachable from the
        header here" (case 141837)."""
        return (
            self.header.is_search_button_visible()
            and self.page.locator(self.header.SEARCH_OVERLAY).count() > 0
        )

    def search_control_geometry(self) -> dict | None:
        """Bounding box of the header magnifier, for comparing its position
        across pages (case 141837's "same position/behavior")."""
        box = self.page.locator(self.header.SEARCH_BUTTON).first.bounding_box()
        if not box:
            return None
        return {k: round(v) for k, v in box.items()}

    # ══════════════════════════════════════════════════════════════════
    # Results — state queries
    # ══════════════════════════════════════════════════════════════════
    def result_count(self) -> int:
        return self.page.locator(self.RESULT_ITEMS).count()

    def result_cards(self, limit: int | None = None) -> list[dict]:
        """One dict per rendered result: title / content-type label /
        summary / href / thumbnail presence.

        `summary` is the SECOND `p.list-group-subtext` (Liferay's snippet).
        The first is always the type/author/date metadata line and is never
        reported as a summary — conflating the two would turn a missing
        snippet into a false pass on case 141838."""
        return self.page.locator(self.RESULTS_LIST).evaluate(
            """(list, limit) => {
                const items = Array.from(list.children);
                const slice = limit ? items.slice(0, limit) : items;
                return slice.map(li => {
                    const a = li.querySelector('.list-group-title a');
                    const subs = Array.from(li.querySelectorAll('p.list-group-subtext'));
                    const typeEl = subs[0] ? subs[0].querySelector('.subtext-item strong') : null;
                    const summaryEl = subs[1] || null;
                    return {
                        title: a ? a.innerText.trim() : '',
                        href: a ? a.getAttribute('href') : null,
                        typeLabel: typeEl ? typeEl.innerText.trim() : '',
                        metadata: subs[0] ? subs[0].innerText.trim() : '',
                        summary: summaryEl ? summaryEl.innerText.trim() : '',
                        subtextCount: subs.length,
                        hasThumbnail: !!li.querySelector('.sticker img, .sticker svg'),
                    };
                });
            }""",
            limit,
        ) if self.page.locator(self.RESULTS_LIST).count() else []

    def result_titles(self) -> list[str]:
        return [card["title"] for card in self.result_cards()]

    def content_type_labels(self) -> list[str]:
        return [card["typeLabel"] for card in self.result_cards()]

    def distinct_content_types(self) -> list[str]:
        return sorted({label for label in self.content_type_labels() if label})

    def first_card_of_type(self, type_label: str) -> dict | None:
        for card in self.result_cards():
            if card["typeLabel"] == type_label:
                return card
        return None

    def first_card_of_other_type(self, type_label: str) -> dict | None:
        """First card whose content-type label differs from `type_label` —
        case 141838's "a result card of a different content type"."""
        for card in self.result_cards():
            if card["typeLabel"] and card["typeLabel"] != type_label:
                return card
        return None

    def total_label_text(self) -> str | None:
        loc = self.page.locator(self.TOTAL_LABEL)
        return loc.first.inner_text().strip() if loc.count() else None

    def reported_total(self) -> int | None:
        """Total match count the page reports, read from the pagination bar
        ("Showing 1 to 20 of 68 entries.") and falling back to the total
        label ("68 Results for membership").

        NOTE FOR TESTS: this number is NOT stable across two navigations —
        the live index is continuously re-crawled and 'qatar' was observed
        reporting 267, then 264, then 267 within one minute. Assert
        relationships (>0, page-2 disjoint from page-1), never an equality
        against a literal or against a value captured on a previous page."""
        import re

        pagination = self.page.locator(self.PAGINATION_RESULTS_TEXT)
        if pagination.count():
            match = re.search(r"of\s+([\d,]+)\s+entries", pagination.first.inner_text())
            if match:
                return int(match.group(1).replace(",", ""))
        label = self.total_label_text()
        if label:
            match = re.search(r"([\d,]+)", label)
            if match:
                return int(match.group(1).replace(",", ""))
        return None

    def results_body_text(self) -> str:
        loc = self.page.locator(self.RESULTS_BODY)
        return loc.first.inner_text().strip() if loc.count() else ""

    def results_body_html(self) -> str:
        loc = self.page.locator(self.RESULTS_BODY)
        return loc.first.inner_html() if loc.count() else ""

    def no_results_message(self) -> str | None:
        """The page's no-results copy, or None when results were returned."""
        text = self.results_body_text()
        if any(marker in text for marker in self.NO_RESULTS_MARKERS):
            return text
        return None

    def suggestion_count(self) -> int:
        """Number of suggestion affordances (spelling tip / browse-category
        link / related keyword) the no-results state offers."""
        return self.page.locator(self.NO_RESULTS_SUGGESTIONS).count()

    def first_result_href(self) -> str | None:
        """The first result's title-link `href`, so a test can assert the LINK
        itself and not only where the browser happened to land."""
        link = self.page.locator(self.RESULT_ITEMS).first.locator(self.RESULT_TITLE_LINK)
        return link.get_attribute("href") if link.count() else None

    def click_first_result(self) -> str:
        """Click the first result's title link and settle on the destination.
        Returns the title text that was clicked, so the test can assert the
        destination against it."""
        # AUTOMATION BUG FIX 2026-09-27 (ADO-141880): this used to settle with
        # `wait_for_load_state("networkidle")`, which can return while the
        # ORIGIN document is still current (and on a document-preview
        # destination never fires the way a full page load does), so the
        # test's current_url() read came back as the /search URL and the
        # navigation assertion failed on timing rather than on behaviour.
        # base_page.wait_for_url() is the framework's helper for this hazard.
        link = self.page.locator(self.RESULT_ITEMS).first.locator(self.RESULT_TITLE_LINK)
        title = link.inner_text().strip()
        origin_url = self.page.url
        link.click()
        self.wait_for_url(lambda url: url != origin_url)
        return title

    def page_text_contains(self, needle: str) -> bool:
        """Case-insensitive whole-document text check — used to confirm a
        navigation destination actually displays the item that was clicked."""
        body = self.page.locator("body").inner_text()
        return needle.strip().lower() in body.lower()

    def current_url(self) -> str:
        return self.page.url

    def document_title(self) -> str:
        return self.page.title()

    # ══════════════════════════════════════════════════════════════════
    # Pagination
    # ══════════════════════════════════════════════════════════════════
    def has_pagination(self) -> bool:
        return self.page.locator(self.PAGINATION_NAV).count() > 0

    def pagination_results_text(self) -> str | None:
        loc = self.page.locator(self.PAGINATION_RESULTS_TEXT)
        return loc.first.inner_text().strip() if loc.count() else None

    def page_link_labels(self) -> list[str]:
        loc = self.page.locator(self.PAGINATION_PAGE_LINKS)
        return [loc.nth(i).inner_text().strip() for i in range(loc.count())]

    def entries_per_page_label(self) -> str | None:
        loc = self.page.locator(self.ENTRIES_PER_PAGE_BUTTON)
        return loc.first.inner_text().strip() if loc.count() else None

    def configured_results_per_page(self) -> int | None:
        """The page-size the portlet is configured with, parsed from its own
        "20 Entries" picker — read from the app, never assumed, so case
        141887's "equals the configured Results Per Page" compares against
        the real configuration rather than a hard-coded 20."""
        import re

        label = self.entries_per_page_label()
        if not label:
            return None
        match = re.search(r"(\d+)", label)
        return int(match.group(1)) if match else None

    def has_next_page_link(self) -> bool:
        return self.page.locator(self.PAGINATION_NEXT).count() > 0

    def has_previous_page_link(self) -> bool:
        return self.page.locator(self.PAGINATION_PREVIOUS).count() > 0

    def has_disabled_previous_control(self) -> bool:
        return self.page.locator(self.PAGINATION_PREVIOUS_DISABLED).count() > 0

    # How long a page turn may take before it is reported as a real failure.
    # Bounded and condition-based — see `_turn_page` for why a fixed wait is
    # not used and why `networkidle` alone was not enough.
    PAGE_TURN_TIMEOUT_MS = 30000

    def _turn_page(self, control: str) -> "GlobalSearchPage":
        """Activate a pagination arrow and wait until the results have
        ACTUALLY changed page before returning.

        AUTOMATION BUG FIX 2026-09-28 (ADO-141881 / ADO-141882): these two
        helpers used to click and then wait on `networkidle` only. The
        portlet turns the page with a full navigation to
        `?q=...&delta=20&start=2`, and `networkidle` was satisfied on the
        OLD document — measured live: immediately after the click the URL
        was still `/search?q=qatar`, the pagination line still read
        "Showing 1 to 20 of 275 entries.", "page 2" repeated 17 of page 1's
        20 titles and offered no Previous control; four seconds later the
        URL was `...&start=2`, the line read "Showing 21 to 40 of 271
        entries.", the overlap was 0 and Previous was present. The tests
        were reading page 1 twice, so both symptoms — the repeats and the
        missing Previous — had one cause, and neither was the index churn
        they looked like.

        The wait is on the portlet's OWN rendered page marker (its
        "Showing A to B of N entries." line), so it is a real condition,
        not a sleep, and it tolerates the live re-crawl moving N between two
        requests: only the A-to-B range has to move, which is exactly what a
        page turn changes."""
        before = self.pagination_results_text()
        self.click(control)
        if before is not None:
            self.page.wait_for_function(
                """([selector, previous]) => {
                    const el = document.querySelector(selector);
                    if (!el) return false;
                    const text = (el.textContent || '').trim();
                    return text.length > 0 && text !== previous;
                }""",
                arg=[self.PAGINATION_RESULTS_TEXT, before],
                timeout=self.PAGE_TURN_TIMEOUT_MS,
            )
        self.page.wait_for_load_state("networkidle")
        self.wait_for_results_page()
        return self

    def go_to_next_page(self) -> "GlobalSearchPage":
        return self._turn_page(self.PAGINATION_NEXT)

    def go_to_previous_page(self) -> "GlobalSearchPage":
        return self._turn_page(self.PAGINATION_PREVIOUS)

    # ══════════════════════════════════════════════════════════════════
    # Advanced filters — presence, then use
    # ══════════════════════════════════════════════════════════════════
    def filters_panel_count(self) -> int:
        return self.page.locator(self.FILTERS_PANEL).count()

    def content_type_filter_count(self) -> int:
        return self.page.locator(self.CONTENT_TYPE_FILTER).count()

    def category_filter_count(self) -> int:
        return self.page.locator(self.CATEGORY_FILTER).count()

    def date_range_field_count(self) -> int:
        return (
            self.page.locator(self.DATE_RANGE_FROM).count()
            + self.page.locator(self.DATE_RANGE_TO).count()
        )

    def clear_filters_control_count(self) -> int:
        return self.page.locator(self.CLEAR_FILTERS_BUTTON).count()

    def mobile_filters_toggle_count(self) -> int:
        return self.page.locator(self.MOBILE_FILTERS_TOGGLE).count()

    def active_filter_count(self) -> int:
        """How many filter values are currently applied/selected."""
        chips = self.page.locator(self.ACTIVE_FILTER_CHIPS).count()
        checked = self.page.locator(
            f"{self.CONTENT_TYPE_OPTION}, {self.CATEGORY_OPTION}"
        ).count()
        return chips + checked

    def missing_filter_controls(self) -> list[str]:
        """Names of the filter controls the approved cases require that this
        build does not render — one readable list for the failure message, so
        a red reports the finding instead of a bare locator timeout."""
        checks = {
            "filters panel": self.filters_panel_count(),
            "Content Type filter": self.content_type_filter_count(),
            "Category filter": self.category_filter_count(),
            "Date Range From/To": self.date_range_field_count(),
            "Clear Filters control": self.clear_filters_control_count(),
        }
        return [name for name, count in checks.items() if count == 0]

    @staticmethod
    def _option_with_text(selector_list: str, value: str) -> str:
        """Append `:has-text("<value>")` to EVERY alternative of a
        comma-separated selector list.

        Naively concatenating `f'{LIST}:has-text(...)'` binds the
        pseudo-class to the LAST alternative only, silently leaving the other
        branches unfiltered — a defect that would surface the first day the
        filter UI actually ships."""
        parts = [part.strip() for part in selector_list.split(",") if part.strip()]
        return ", ".join(f'{part}:has-text("{value}")' for part in parts)

    def select_content_type(self, value: str) -> "GlobalSearchPage":
        """Select a Content Type filter value. Only reachable once a test has
        already asserted the control exists."""
        self.click(self._option_with_text(self.CONTENT_TYPE_OPTION, value))
        self.wait_for_results_page()
        return self

    def deselect_content_type(self, value: str) -> "GlobalSearchPage":
        self.click(self._option_with_text(self.CONTENT_TYPE_OPTION, value))
        self.wait_for_results_page()
        return self

    def select_category(self, value: str) -> "GlobalSearchPage":
        self.click(self._option_with_text(self.CATEGORY_OPTION, value))
        self.wait_for_results_page()
        return self

    def deselect_category(self, value: str) -> "GlobalSearchPage":
        self.click(self._option_with_text(self.CATEGORY_OPTION, value))
        self.wait_for_results_page()
        return self

    def set_date_range(self, date_from: str, date_to: str) -> "GlobalSearchPage":
        self.type(self.DATE_RANGE_FROM, date_from)
        self.type(self.DATE_RANGE_TO, date_to)
        return self

    def apply_filters(self) -> "GlobalSearchPage":
        self.click(self.APPLY_FILTERS_BUTTON)
        self.wait_for_results_page()
        return self

    def clear_filters(self) -> "GlobalSearchPage":
        self.click(self.CLEAR_FILTERS_BUTTON)
        self.wait_for_results_page()
        return self

    def date_range_validation_message_count(self) -> int:
        return self.page.locator(self.DATE_RANGE_VALIDATION_MESSAGE).count()

    def result_dates(self) -> list[str]:
        """The date portion of each result's metadata line — what a Date
        Range filter would have to narrow."""
        return [card["metadata"] for card in self.result_cards()]

    # ══════════════════════════════════════════════════════════════════
    # Locale / direction
    # ══════════════════════════════════════════════════════════════════
    def html_lang(self) -> str | None:
        return self.page.evaluate("() => document.documentElement.getAttribute('lang')")

    def document_direction(self) -> str:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('dir') "
            "|| getComputedStyle(document.body).direction"
        )

    def results_list_direction(self) -> str | None:
        loc = self.page.locator(self.RESULTS_LIST)
        if not loc.count():
            return None
        return loc.first.evaluate("el => getComputedStyle(el).direction")

    def results_list_text_align(self) -> str | None:
        loc = self.page.locator(self.RESULTS_LIST)
        if not loc.count():
            return None
        return loc.first.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return cs.textAlign === 'start' "
            "? (cs.direction === 'rtl' ? 'right' : 'left') : cs.textAlign; }"
        )

    @staticmethod
    def _is_arabic(text: str) -> bool:
        return any("؀" <= ch <= "ۿ" for ch in text)

    @staticmethod
    def _is_latin(text: str) -> bool:
        return any(("a" <= ch.lower() <= "z") for ch in text)

    def results_not_in_language(self, language: str) -> list[str]:
        """Result TITLES **and** SUMMARIES that are not in the requested
        language (`"en"` / `"ar"`), as readable `"<field>: <text>"` strings.

        Both fields are checked because the locale-scoping cases (141839
        step 4, 141891 step 4) say "all returned result titles/summaries are
        in <language>, scoped to the <language> content set" — asserting on
        titles alone would silently drop half the stated expectation.

        AUTOMATION BUG FIX 2026-09-27 (ADO-141839): the `en` branch used to
        flag the mere PRESENCE of an Arabic character. That cannot prove
        "these results are not scoped to English", because the offenders it
        reported were BILINGUAL items carrying English AND Arabic in the same
        title/summary — correct English-locale content. It therefore went red
        on correct behaviour. The predicate now flags only items with NO Latin
        text at all, i.e. genuinely Arabic-ONLY content surfacing in an
        English result set, which IS the scoping failure the case describes.
        This is the exact mirror of the `ar` branch, which was already written
        that way; it is a narrowing of a wrong predicate, not a relaxation —
        an Arabic-only title in English results still fails."""
        offenders = []

        def _offends(text: str) -> bool:
            if not text:
                return False
            if language == "en":
                return self._is_arabic(text) and not self._is_latin(text)
            return self._is_latin(text) and not self._is_arabic(text)

        for card in self.result_cards():
            if _offends(card["title"]):
                offenders.append(f"title: {card['title'][:80]}")
            if _offends(card["summary"]):
                offenders.append(f"summary: {card['summary'][:80]}")
        return offenders

    # ══════════════════════════════════════════════════════════════════
    # Layout / responsive
    # ══════════════════════════════════════════════════════════════════
    def layout_metrics(self) -> dict:
        """Viewport vs. document width — the horizontal-overflow check every
        responsive case makes."""
        return self.page.evaluate(
            """() => ({
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                bodyScrollWidth: document.body.scrollWidth,
                innerWidth: window.innerWidth,
            })"""
        )

    def has_horizontal_scroll(self, tolerance_px: int = 1) -> bool:
        metrics = self.layout_metrics()
        return metrics["scrollWidth"] > metrics["clientWidth"] + tolerance_px

    def filters_panel_box(self) -> dict | None:
        """Bounding box of the advanced-filters panel, or None when the build
        renders no such panel (the live state — see module docstring)."""
        loc = self.page.locator(self.FILTERS_PANEL)
        if not loc.count():
            return None
        box = loc.first.bounding_box()
        return {k: round(v) for k, v in box.items()} if box else None

    def results_list_box(self) -> dict | None:
        loc = self.page.locator(self.RESULTS_LIST)
        if not loc.count():
            return None
        box = loc.first.bounding_box()
        return {k: round(v) for k, v in box.items()} if box else None

    def filters_panel_side(self) -> str | None:
        """`"left"` / `"right"` — which side of the result list the filters
        panel sits on. None when either element is absent."""
        panel, results = self.filters_panel_box(), self.results_list_box()
        if not panel or not results:
            return None
        return "left" if panel["x"] < results["x"] else "right"

    def filters_and_results_are_side_by_side(self) -> bool:
        """True when the filters panel and the result list occupy separate
        horizontal columns that also overlap vertically (i.e. genuinely side
        by side, not stacked)."""
        panel, results = self.filters_panel_box(), self.results_list_box()
        if not panel or not results:
            return False
        horizontally_separate = (
            panel["x"] + panel["width"] <= results["x"]
            or results["x"] + results["width"] <= panel["x"]
        )
        vertically_overlapping = (
            panel["y"] < results["y"] + results["height"]
            and results["y"] < panel["y"] + panel["height"]
        )
        return horizontally_separate and vertically_overlapping

    def result_card_boxes(self) -> list[dict]:
        return self.page.locator(self.RESULTS_LIST).evaluate(
            """list => Array.from(list.children).map(li => {
                const r = li.getBoundingClientRect();
                return {x: Math.round(r.x), y: Math.round(r.y),
                        width: Math.round(r.width), height: Math.round(r.height)};
            })"""
        ) if self.page.locator(self.RESULTS_LIST).count() else []

    # AUTOMATION BUG FIX 2026-09-27 (ADO-141841, ADO-141842): an overlap of
    # less than this many CSS pixels is not a layout defect, it is rounding.
    # `result_card_boxes()` rounds x/y/width/height INDEPENDENTLY, so a card
    # ending at y=811.6 (rounded to 812) followed by one starting at y=811.7
    # (also rounded to 812) produced `a.y + a.height > b.y` by 1px on EVERY
    # consecutive pair, reporting a phantom overlap on a list that is
    # verifiably clean. Requiring a real, visible intersection removes the
    # artefact without hiding a genuine overlap.
    OVERLAP_TOLERANCE_PX = 1

    def overlapping_result_cards(self) -> list[tuple[int, int]]:
        """Index pairs of result cards whose rectangles genuinely intersect —
        an overlap in a stacked list is a real layout defect at any width.

        The intersection must exceed `OVERLAP_TOLERANCE_PX` on BOTH axes, so a
        sub-pixel rounding artefact between two adjacent cards is not reported
        (see the constant's comment for the defect this fixes)."""
        boxes = self.result_card_boxes()
        tolerance = self.OVERLAP_TOLERANCE_PX
        overlaps = []
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                horizontal = min(a["x"] + a["width"], b["x"] + b["width"]) - max(
                    a["x"], b["x"]
                )
                vertical = min(a["y"] + a["height"], b["y"] + b["height"]) - max(
                    a["y"], b["y"]
                )
                if horizontal > tolerance and vertical > tolerance:
                    overlaps.append((i, j))
        return overlaps

    def results_stack_in_single_column(self) -> bool:
        """True when every result card shares one left edge and one width —
        the single-column stacking the mobile case requires."""
        boxes = self.result_card_boxes()
        if len(boxes) < 2:
            return True
        lefts = {box["x"] for box in boxes}
        widths = {box["width"] for box in boxes}
        return len(lefts) == 1 and len(widths) == 1

    def truncated_result_titles(self) -> list[str]:
        """Titles whose rendered box is WIDER THAN ITS COLUMN — the "no
        truncated text" half of the tablet case.

        The obvious check (`a.scrollWidth > a.clientWidth`) is useless on
        this markup and was replaced after measuring it: the title anchor is
        `display: inline-block` with `overflow: visible`, so its box always
        grows to fit its text and the two values are ALWAYS equal (measured
        live at 768x1024: 237/237, 103/103, 77/77, 268/268). An assertion
        built on it could never fail — a vacuous pass. Comparing the anchor's
        rendered width against its containing `.list-group-title` column
        instead is a real check: a title too wide for its column is exactly
        the clipping/truncation the case forbids."""
        if not self.page.locator(self.RESULTS_LIST).count():
            return []
        return self.page.locator(self.RESULTS_LIST).evaluate(
            """list => Array.from(list.children).flatMap(li => {
                const holder = li.querySelector('.list-group-title');
                const a = holder ? holder.querySelector('a') : null;
                if (!a) return [];
                const aWidth = a.getBoundingClientRect().width;
                const columnWidth = holder.clientWidth;
                if (!columnWidth) return [];
                return aWidth > columnWidth + 1 ? [a.innerText.trim()] : [];
            })"""
        )

    def undersized_touch_targets(self, minimum_px: int) -> list[dict]:
        """Interactive CONTROLS inside the results region smaller than
        `minimum_px` in either dimension (WCAG 2.5.5's target-size rule — the
        only concrete number behind the mobile case's "controls are large
        enough to tap").

        **Disclosed scope, measured before it was chosen:** result TITLE
        links (`.list-group-title a`) are excluded. At 375x812 every one of
        the 42 links in the results region measures under 44px, and 20 of
        them are those title links — text links whose height is simply the
        text's line-height (26px), which WCAG 2.5.5 itself excepts as inline
        targets constrained by non-target text. Counting them would bury the
        real controls (the 32x32 per-result download action and the
        pagination links) under a wall of text-link rows and make the failure
        message unreadable. The exclusion narrows WHICH elements count as
        "controls", not how small a control may be — the 44px threshold is
        unchanged and the remaining controls are still judged against it."""
        return self.page.evaluate(
            """(args) => {
                const [selector, min] = args;
                const root = document.querySelector(selector);
                if (!root) return [];
                const controls = root.querySelectorAll('a, button, input, select');
                return Array.from(controls).flatMap(el => {
                    if (el.closest('.list-group-title')) return [];  // title text link
                    const r = el.getBoundingClientRect();
                    if (!r.width && !r.height) return [];
                    if (r.width >= min && r.height >= min) return [];
                    return [{
                        label: (el.innerText || el.getAttribute('aria-label') || el.tagName)
                                 .trim().slice(0, 40),
                        className: (el.className || '').toString().slice(0, 40),
                        width: Math.round(r.width),
                        height: Math.round(r.height),
                    }];
                });
            }""",
            [self.RESULTS_PORTLET, minimum_px],
        )

    # ══════════════════════════════════════════════════════════════════
    # Safety / injection
    # ══════════════════════════════════════════════════════════════════
    def capture_dialogs(self) -> list:
        """Register a dialog handler and return the (growing) list of dialog
        messages, so an injection case can prove no `alert()` fired. Dialogs
        are auto-dismissed — an unhandled one would block the page."""
        seen: list[str] = []

        def _handle(dialog):
            seen.append(dialog.message)
            dialog.dismiss()

        self.page.on("dialog", _handle)
        return seen

    def page_errors(self) -> list:
        """Register a pageerror handler and return the (growing) list of
        uncaught JS errors — the "no application error" half of the
        injection case."""
        errors: list[str] = []
        self.page.on("pageerror", lambda exc: errors.append(str(exc)))
        return errors

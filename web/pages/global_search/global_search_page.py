"""
web/pages/global_search/global_search_page.py — GlobalSearchPage.

Public-website Page Object for PBI 131055 ("Global Advanced Search").

Flow CONFIRMED LIVE 2026-09-24 (disclosed scripted Playwright probe):
  header `a.qc-search-btn` (aria-haspopup="dialog") opens the overlay
  `.qc-search-overlay` > form[role=search] > `input.qc-search-overlay__input`
  (+ `button.qc-search-overlay__submit` "Search"); Enter lands on
  `/web/qatar-chamber/search?q=<kw>` (Arabic: `/ar/web/qatar-chamber/search?q=`).

The results page is the stock Liferay Search Results portlet:
  `.portlet-search-results` > `.search-total-label` ("75 Results for …")
  > `ul#search-results-display-list > li.list-group-item`
      `.list-group-title a` (title), `.search-results-metadata .subtext-item strong`
      (first = content type, e.g. "Document", "Page"; AR "الصفحة"),
      summary would be `.list-group-text` / `.search-results-content` (not rendered live).
  No results: `.taglib-empty-result-message-title` ("No results were found.").
Facet/filter portlets (type/category/modified facets) are looked up by their
Liferay portlet ids / facet classes — none are placed on the live page.
"""

from urllib.parse import quote

from config.settings import web_url
from core.web.base_page import BasePage

SEARCH_PATH = "/web/qatar-chamber/search"


class GlobalSearchPage(BasePage):
    HEADER = "header.qc-global-site-header"
    HEADER_SEARCH_BUTTON = "header.qc-global-site-header a.qc-search-btn"
    OVERLAY_INPUT = "input.qc-search-overlay__input"
    RESULTS_PORTLET = ".portlet-search-results"
    TOTAL_LABEL = ".portlet-search-results .search-total-label"
    RESULT = "#search-results-display-list > li"
    RESULT_TITLE = ".list-group-title"
    RESULT_TYPE = ".search-results-metadata .subtext-item strong"
    RESULT_SUMMARY = ".list-group-text, .search-results-content, .search-results-snippet"
    NO_RESULTS = ".portlet-search-results .taglib-empty-result-message-title"
    FACETS = ("[id*='_facet_portlet'], [id*='FacetPortlet'], .search-facet, [class*='facet-'], "
              "[data-qa-id*='facet']")
    FILTER_TOGGLE = "button:has-text('Filter'), [aria-controls*='facet'], [data-toggle='collapse'][href*='facet']"
    SUGGESTIONS = (".portlet-search-results .search-suggested-spelling, .portlet-search-results [class*='suggest'], "
                   ".portlet-search-results a")

    # ---- Navigation -------------------------------------------------------------
    def open_path(self, path: str, locale: str = "en") -> "GlobalSearchPage":
        self.open(web_url(path, locale=locale))
        self.wait_for(self.HEADER_SEARCH_BUTTON, timeout=30000)
        return self

    def search_from_header(self, keyword: str) -> "GlobalSearchPage":
        """Real user flow: click the header icon, type, press Enter, wait for
        the results page to render (results list OR the empty message)."""
        self.click(self.HEADER_SEARCH_BUTTON)
        self.wait_for(self.OVERLAY_INPUT)
        self.type(self.OVERLAY_INPUT, keyword)
        self.page.keyboard.press("Enter")
        self.wait_for_url(lambda u: "search" in u and "q=" in u, timeout=30000)
        self._wait_results()
        return self

    def open_results(self, keyword: str, locale: str = "en") -> "GlobalSearchPage":
        self.open(web_url(f"{SEARCH_PATH}?q={quote(keyword)}", locale=locale))
        self._wait_results()
        return self

    def _wait_results(self) -> None:
        self.page.wait_for_function(
            "() => !!document.querySelector('#search-results-display-list > li, .taglib-empty-result-message-title')",
            timeout=30000,
        )

    # ---- State ------------------------------------------------------------------
    def current_url(self) -> str:
        return self.page.url

    def header_search_box(self):
        return self.page.locator(self.HEADER_SEARCH_BUTTON).first.bounding_box()

    def header_search_facts(self) -> dict:
        return self.page.locator(self.HEADER_SEARCH_BUTTON).first.evaluate(
            "e => ({inHeader: !!e.closest('header'), label: e.getAttribute('aria-label'), popup: e.getAttribute('aria-haspopup')})"
        )

    def results(self) -> list:
        return self.page.locator(self.RESULT).evaluate_all(
            """(items, sel) => items.map(li => {
                const t = li.querySelector(sel.title), ty = li.querySelector(sel.type), s = li.querySelector(sel.summary);
                const r = li.getBoundingClientRect();
                return {title: t ? t.innerText.trim() : "", type: ty ? ty.innerText.trim() : "",
                        summary: s ? s.innerText.trim() : "", x: r.x, y: r.y, width: r.width, height: r.height,
                        titleAlign: t ? getComputedStyle(t).textAlign : null,
                        titleDir: t ? getComputedStyle(t).direction : null,
                        clipped: [...li.querySelectorAll('*')].some(e => e.offsetParent && e.children.length === 0
                                  && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'visible')};
            })""",
            {"title": self.RESULT_TITLE, "type": self.RESULT_TYPE, "summary": self.RESULT_SUMMARY},
        )

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def visible_count(self, locator: str) -> int:
        loc = self.page.locator(locator)
        return sum(1 for i in range(loc.count()) if loc.nth(i).is_visible())

    def text_of(self, locator: str) -> str:
        loc = self.page.locator(locator)
        return loc.first.inner_text().strip() if loc.count() else ""

    def texts(self, locator: str) -> list:
        return [t.strip() for t in self.page.locator(locator).all_inner_texts()]

    def document_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.dir")

    def horizontal_overflow_px(self) -> int:
        return self.page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")

    def results_portlet_box(self):
        return self.page.locator(self.RESULTS_PORTLET).first.bounding_box()

    def tap_targets(self) -> list:
        """Every visible interactive element inside the results portlet with its size."""
        return self.page.locator(f"{self.RESULTS_PORTLET} a, {self.RESULTS_PORTLET} button").evaluate_all(
            """els => els.filter(e => e.offsetParent !== null).map(e => { const r = e.getBoundingClientRect();
                return {text: (e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 30), width: r.width, height: r.height}; })"""
        )

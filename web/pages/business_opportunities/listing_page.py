"""
web/pages/business_opportunities/listing_page.py — BusinessOpportunitiesListingPage.

Public Business Opportunities listing (PBI 130697, plan 137724, suite 140361).

LOCATORS — re-verified live on qcdev 2026-10-12 (Phase-3 W3 run), fresh
UNAUTHENTICATED Chromium context, EN + AR, 1920 / 768 / 390 / 375.

Facts this Page Object relies on (all observed live, not assumed):
- Fragment root `section.qc-bol` (`data-qc-bol-page-size="6"`). EN path
  `/web/qatar-chamber/business-opportunities`; AR `/ar/web/qatar-chamber/
  business-opportunities` (the header switcher lands on the friendly
  `/ar/business-opportunities`).
- Data comes from the public, read-only API `/o/qc-business-opportunities-api`:
  `/lookup?languageId=..` (ALL opportunities, filtered client-side),
  `/lookups?languageId=..` (picklists), `/page?languageId=..` (hero copy).
  `api_*` helpers below read them so tests compare the grid to the real
  records instead of hard-coded seed data.
- Search, chips, filters and sort are all client-side; no request fires on
  Apply. A trending chip is a KEYWORD search (it fills the search box,
  `title="Search for <label>"`), it does not touch the sidebar selects and has
  no active/pressed state.
- The 6 sidebar selects carry `aria-label` = their placeholder text
  ("All Sectors", "All Countries", "Investment Type", "Investment Amount",
  "Timeline", "Risk Profile") — the stable hook used below.
- Load More (`button.qc-bol-more`) and the empty state (`p.qc-bol-empty`)
  are always in the DOM and toggled with the `hidden` attribute.
- There is NO search clear (x) control: the input is `type=search` but the
  native cancel button is suppressed (`appearance:none`).
- Mobile (<= tablet breakpoint): the sidebar collapses to the
  `button.qc-bol-side-head` accordion (`aria-expanded`), inline, not overlay.
"""

from config.settings import web_url
from core.web.base_page import BasePage

PATH = "/web/qatar-chamber/business-opportunities"
API = "/o/qc-business-opportunities-api"

FILTER_KEYS = ("sector", "country", "investment_type", "investment_amount", "timeline", "risk_profile")
TAB_KEYS = ("active", "archive")


class BusinessOpportunitiesListingPage(BasePage):
    ROOT = "section.qc-bol"

    # ---- Hero ---------------------------------------------------------------
    HERO = "header.qc-bol-hero"
    BREADCRUMB_LINK = "a.qc-bol-crumb"
    BREADCRUMB_CURRENT = "a.qc-bol-crumb.is-current"
    HERO_EYEBROW = "p.qc-bol-eyebrow"
    HERO_TITLE = "h1.qc-bol-title"
    HERO_DESCRIPTION = ".qc-bol-hero-desc"
    HERO_IMAGE = "img.qc-bol-hero-img"
    HERO_CTA = "a.qc-bol-cta"
    HERO_CTA_LABEL = "a.qc-bol-cta .qc-bol-cta-label"
    HERO_CTA_ICON = "a.qc-bol-cta svg"

    # ---- Search card ----------------------------------------------------------
    SEARCH_CARD = "form.qc-bol-search-card"
    SEARCH_FIELD = ".qc-bol-field.qc-bol-search"
    SEARCH_INPUT = "input.qc-bol-search-input"
    SEARCH_ICON = "span.qc-bol-search-icon"
    SEARCH_BUTTON = "button.qc-bol-search-btn"
    # No clear control exists live (see docstring) — any of these would count.
    SEARCH_CLEAR_CANDIDATES = (
        ".qc-bol-search [class*='clear'], .qc-bol-search button, "
        ".qc-bol-search [aria-label*='lear' i]"
    )

    # ---- Trending chips -----------------------------------------------------
    TRENDING_LABEL = "span.qc-bol-trending-label"
    TRENDING_CHIP = "button.qc-bol-chip"

    # ---- Sidebar filters ----------------------------------------------------
    FILTERS_SIDE = "aside.qc-bol-side"
    FILTERS_PANEL = "div.qc-bol-side-body"
    FILTERS_TOGGLE = "button.qc-bol-side-head"
    FILTERS_HEADING = "span.qc-bol-side-heading"
    FILTER_LABEL = "span.qc-bol-filter-label"
    APPLY_BUTTON = "button.qc-bol-apply"
    RESET_BUTTON = "button.qc-bol-reset"
    FILTER_SELECTS = ".qc-bol-selects select"
    # DOM order is fixed (main.js builds them in this order); the EN aria-label
    # doubles as the default/placeholder text.
    FILTER_INDEX = {k: i for i, k in enumerate(FILTER_KEYS)}

    # ---- Sort / tabs ----------------------------------------------------------
    SORT_FIELD = "div.qc-bol-sort"
    SORT_DROPDOWN = "select[data-qc-bol-sort]"
    TABS = "div.qc-bol-tabs"
    TAB = "div.qc-bol-tabs button.qc-bol-tab"
    TAB_COUNT = "span.qc-bol-tab-count"
    TAB_ACTIVE_STATE_CLASS = "is-active"

    # ---- Card grid ------------------------------------------------------------
    CARD_GRID = "div.qc-bol-grid"
    CARD = "a.qc-bol-card"
    CARD_BAND = "span.qc-bol-card-band"
    CARD_BANNER_IMG = "img.qc-bol-card-img"
    CARD_TAG = "span.qc-bol-card-cat"
    CARD_TAG_DOT = "span.qc-bol-card-dot"
    CARD_TITLE = "span.qc-bol-card-title"
    CARD_CELL = "span.qc-bol-card-cell"
    CARD_CELL_TEXT = "span.qc-bol-card-cell-text"
    CARD_RULE = "span.qc-bol-card-rule"
    CARD_VIEW_DETAILS_LINK = "span.qc-bol-view"
    CARD_ARROW = "span.qc-bol-card-arrow"
    NO_RESULTS_MESSAGE = "p.qc-bol-empty"
    STATUS = "p.qc-bol-status"

    # ---- Load More ------------------------------------------------------------
    LOAD_MORE_BUTTON = "button.qc-bol-more"

    # ---- Navigation -----------------------------------------------------------
    def open_listing(self, locale: str = "en") -> "BusinessOpportunitiesListingPage":
        self.open(web_url(PATH, locale=locale))
        self.wait_for_ready()
        return self

    def wait_for_ready(self) -> None:
        # main.js sets data-qc-bol-ready once the API data has rendered.
        self.wait_for(f"{self.ROOT}[data-qc-bol-ready='true']", state="attached", timeout=30000)
        self.page.wait_for_function(
            "() => document.querySelector('.qc-bol-card') || !document.querySelector('.qc-bol-empty').hidden",
            timeout=30000,
        )

    def wait_for_grid_change(self, before: list, timeout: int = 5000) -> None:
        """Client-side re-render has no network signal; wait until the title
        list differs from `before` (bounded — an unchanged grid is a valid
        outcome, e.g. a filter that matches everything)."""
        try:
            self.page.wait_for_function(
                "(b) => JSON.stringify([...document.querySelectorAll('.qc-bol-card-title')].map(e=>e.textContent)) !== b",
                arg=__import__("json").dumps(before), timeout=timeout,
            )
        except Exception:  # noqa: BLE001 — unchanged grid is a legitimate result
            pass

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def document_lang(self) -> str:
        return self.page.evaluate("() => document.documentElement.lang")

    def has_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    # ---- Public API (read-only) ---------------------------------------------
    def _api(self, path: str) -> dict:
        resp = self.page.request.get(web_url(API + path))
        assert resp.ok, f"GET {path} -> HTTP {resp.status}"
        return resp.json()

    def api_opportunities(self, language_id: str = "en_US") -> list:
        return self._api(f"/lookup?languageId={language_id}")["items"]

    def api_page(self, language_id: str = "en_US") -> dict:
        return self._api(f"/page?languageId={language_id}")["item"]

    def api_lookups(self, language_id: str = "en_US") -> dict:
        return self._api(f"/lookups?languageId={language_id}")["lookups"]

    @staticmethod
    def is_public_active(item: dict) -> bool:
        return (
            item.get("activeStatus") is True
            and (item.get("lifecycleStatus") or {}).get("key") == "published"
            and not item.get("archived")
        )

    @staticmethod
    def is_public_archived(item: dict) -> bool:
        return item.get("activeStatus") is True and (
            item.get("archived") or (item.get("lifecycleStatus") or {}).get("key") == "archived"
        )

    # ---- Hero -----------------------------------------------------------------
    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW).strip()

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_description_text(self) -> str:
        return self.text(self.HERO_DESCRIPTION).strip()

    def hero_cta_label(self) -> str:
        return self.text(self.HERO_CTA_LABEL).strip()

    def hero_image_loaded(self, timeout: int = 20000) -> bool:
        """The hero illustration is ~1 MB; wait (bounded) for its load event
        before judging it broken."""
        try:
            self.page.wait_for_function(
                "(s) => { const i = document.querySelector(s); return i && i.complete && i.naturalWidth > 0; }",
                arg=self.HERO_IMAGE, timeout=timeout,
            )
        except Exception:  # noqa: BLE001 — judged below
            pass
        return self.page.locator(self.HERO_IMAGE).evaluate(
            "(img) => img.complete === true && img.naturalWidth > 0"
        )

    def click_hero_cta(self) -> None:
        self.click(self.HERO_CTA)

    # ---- Styles / geometry ----------------------------------------------------
    def style(self, locator: str, props: list, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).evaluate(
            "(e, props) => { const c = getComputedStyle(e); const o = {}; for (const p of props) o[p] = c[p]; return o; }",
            props,
        )

    def box(self, locator: str, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).bounding_box()

    def placeholder_color(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).evaluate("(i) => getComputedStyle(i, '::placeholder').color")

    # ---- Search -----------------------------------------------------------
    def search(self, keyword: str, use_button: bool = False) -> "BusinessOpportunitiesListingPage":
        before = self.card_titles()
        self.page.locator(self.SEARCH_INPUT).fill(keyword)
        if use_button:
            self.click(self.SEARCH_BUTTON)
        else:
            self.page.locator(self.SEARCH_INPUT).press("Enter")
        self.wait_for_grid_change(before)
        return self

    def search_input_value(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).input_value()

    def search_placeholder(self) -> str:
        return self.get_attribute(self.SEARCH_INPUT, "placeholder") or ""

    def search_clear_control_count(self) -> int:
        return self.page.locator(self.SEARCH_CLEAR_CANDIDATES).count()

    def no_results_message_text(self) -> str:
        return self.text(self.NO_RESULTS_MESSAGE).strip()

    def is_no_results_message_visible(self) -> bool:
        return self.page.locator(self.NO_RESULTS_MESSAGE).is_visible()

    # ---- Trending chips -----------------------------------------------------
    def trending_chip_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.TRENDING_CHIP).all_inner_texts()]

    def click_trending_chip(self, label: str) -> "BusinessOpportunitiesListingPage":
        before = self.card_titles()
        self.page.locator(self.TRENDING_CHIP, has_text=label).first.click()
        self.wait_for_grid_change(before)
        return self

    def chip_state(self, label: str) -> dict:
        return self.page.locator(self.TRENDING_CHIP, has_text=label).first.evaluate(
            "(c) => ({cls: c.className, pressed: c.getAttribute('aria-pressed'), current: c.getAttribute('aria-current')})"
        )

    # ---- Sidebar filters ----------------------------------------------------
    def _select(self, filter_key: str):
        return self.page.locator(self.FILTER_SELECTS).nth(self.FILTER_INDEX[filter_key])

    def open_filters_panel(self) -> None:
        self.click(self.FILTERS_TOGGLE)
        self.page.wait_for_function(
            "() => document.querySelector('.qc-bol-side-head').getAttribute('aria-expanded') === 'true'"
        )

    def is_filters_panel_open(self) -> bool:
        return self.page.locator(self.FILTERS_PANEL).is_visible()

    def filters_toggle_expanded(self) -> str:
        return self.get_attribute(self.FILTERS_TOGGLE, "aria-expanded")

    def visible_filter_count(self) -> int:
        return self.page.evaluate(
            "() => [...document.querySelectorAll('.qc-bol-selects select')].filter(s => s.offsetParent).length"
        )

    def filter_options(self, filter_key: str) -> list:
        return [t.strip() for t in self._select(filter_key).locator("option").all_inner_texts()]

    def select_filter(self, filter_key: str, label: str) -> None:
        self._select(filter_key).select_option(label=label)

    def selected_filter_value(self, filter_key: str) -> str:
        return self._select(filter_key).evaluate("(s) => s.options[s.selectedIndex].text").strip()

    def selected_filter_values(self) -> dict:
        return {k: self.selected_filter_value(k) for k in FILTER_KEYS}

    def apply_filters(self) -> "BusinessOpportunitiesListingPage":
        before = self.card_titles()
        self.click(self.APPLY_BUTTON)
        self.wait_for_grid_change(before)
        return self

    def reset_filters(self) -> "BusinessOpportunitiesListingPage":
        before = self.card_titles()
        self.click(self.RESET_BUTTON)
        self.wait_for_grid_change(before)
        return self

    # ---- Sort By ------------------------------------------------------------
    def select_sort(self, label: str) -> None:
        before = self.card_titles()
        self.page.locator(self.SORT_DROPDOWN).select_option(label=label)
        self.wait_for_grid_change(before)

    def selected_sort_value(self) -> str:
        return self.page.locator(self.SORT_DROPDOWN).evaluate("(s) => s.options[s.selectedIndex].text").strip()

    def sort_options(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.SORT_DROPDOWN} option").all_inner_texts()]

    # ---- Status tabs --------------------------------------------------------
    def _tab(self, tab_key: str):
        return self.page.locator(self.TAB).nth(TAB_KEYS.index(tab_key))

    def switch_tab(self, tab_key: str) -> "BusinessOpportunitiesListingPage":
        before = self.card_titles()
        self._tab(tab_key).click()
        self.wait_for_class_on_nth(self.TAB, TAB_KEYS.index(tab_key), self.TAB_ACTIVE_STATE_CLASS)
        self.wait_for_grid_change(before)
        return self

    def is_tab_active(self, tab_key: str) -> bool:
        return self.TAB_ACTIVE_STATE_CLASS in (self._tab(tab_key).get_attribute("class") or "")

    def tab_aria_selected(self, tab_key: str) -> str:
        return self._tab(tab_key).get_attribute("aria-selected")

    def tab_count(self, tab_key: str) -> int:
        raw = self._tab(tab_key).locator(self.TAB_COUNT).inner_text()
        return int(raw.strip().strip("()"))

    # ---- Card grid --------------------------------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return [t.strip() for t in self.page.locator(self.CARD_TITLE).all_inner_texts()]

    def card_hrefs(self) -> list:
        return self.page.eval_on_selector_all(self.CARD, "els => els.map(e => e.getAttribute('href'))")

    def card_ercs(self) -> list:
        return [h.split("opportunity=")[-1] for h in self.card_hrefs()]

    def card_tags(self) -> list:
        """Tag text exactly as rendered: '<sector><dot><type>' with the dot
        span's own character (spaces come from the flex gap, not text)."""
        return self.page.eval_on_selector_all(
            self.CARD_TAG, "els => els.map(e => [...e.children].map(c => c.textContent.trim()))"
        )

    def card_cells(self, index: int) -> list:
        return [t.strip() for t in self.page.locator(self.CARD).nth(index).locator(self.CARD_CELL_TEXT).all_inner_texts()]

    def card_cell_icons(self, index: int) -> int:
        return self.page.locator(self.CARD).nth(index).locator(f"{self.CARD_CELL} svg").count()

    def truncated_cell_texts(self) -> list:
        return self.page.eval_on_selector_all(
            self.CARD_CELL_TEXT, "els => els.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent)"
        )

    def card_banner_loaded(self, index: int = 0, timeout: int = 15000) -> bool:
        """Banners are `loading="lazy"`: bring the card into view, then wait
        (bounded) for the decode before judging it broken."""
        img = self.page.locator(self.CARD_BANNER_IMG).nth(index)
        img.scroll_into_view_if_needed()
        try:
            img.evaluate(
                "(img, t) => new Promise((res, rej) => { if (img.complete && img.naturalWidth) return res(); "
                "img.addEventListener('load', () => res(), {once: true}); "
                "img.addEventListener('error', () => rej('error'), {once: true}); setTimeout(() => rej('timeout'), t); })",
                timeout,
            )
        except Exception:  # noqa: BLE001 — judged below
            pass
        return img.evaluate("(img) => img.complete === true && img.naturalWidth > 0")

    def card_index_by_erc(self, erc: str) -> int:
        return self.card_ercs().index(erc)

    def click_view_details_by_title(self, title: str) -> None:
        self.page.locator(self.CARD, has_text=title).first.locator(self.CARD_VIEW_DETAILS_LINK).click()

    def grid_column_count(self) -> int:
        return self.page.locator(self.CARD_GRID).evaluate(
            "(g) => getComputedStyle(g).gridTemplateColumns.split(' ').filter(Boolean).length"
        )

    # ---- Load More ----------------------------------------------------------
    def is_load_more_visible(self) -> bool:
        return self.page.locator(self.LOAD_MORE_BUTTON).is_visible()

    def page_size(self) -> int:
        return int(self.get_attribute(self.ROOT, "data-qc-bol-page-size") or 0)

    def status_text(self) -> str:
        return self.page.locator(self.STATUS).inner_text().strip()

    # ---- Theme -----------------------------------------------------------
    def theme(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

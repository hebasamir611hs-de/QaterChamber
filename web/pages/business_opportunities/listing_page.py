"""
web/pages/business_opportunities/listing_page.py — BusinessOpportunitiesListingPage.

Public-frontend Page Object for PBI 130697 (INVEST — "Submit a Business
Opportunity" / Business Opportunities Listing), sourced from the injected
Azure DevOps suite (plan 137724, suite 140361) handed off by the QA Manager
for Phase 3 scripting.

LOCATORS — CLI-first, verified live 2026-09-22 (qcdev)
------------------------------------------------------------------
Real path resolved via the Liferay nav-items REST API
(`/o/c/navitems/scopes/37246?...`), not a guess:
`/web/qatar-chamber/business-opportunities`. Locators confirmed with
`python tools/extract_locators.py --url <path>` (role/interactive elements)
plus an ad-hoc structural dump (`document.querySelectorAll` class walk,
scripted, not MCP) for the non-interactive containers the extractor's
interactive-only harvest does not surface (hero, card grid, cells). The
real CSS namespace on this fragment is `qc-bol` (Business Opportunities
Listing), not the `qc-bo` guessed originally.

Still unconfirmed (left as TODO(locator), flagged for dev input — see the
batch report): SEARCH_CLEAR_ICON (no clear/x icon rendered in the search
bar at the time of extraction) and LOAD_MORE_SPINNER (no loading-state
class observed; only 4 Active / 2 Archive items exist, never enough to
trigger Load More's loading state during a normal click). TRENDING_CHIP_ACTIVE
uses `.qc-bol-chip.is-active`, mirrored from the confirmed `is-active`
pattern on `.qc-bol-tab` (Active Opportunities tab), not independently
observed on a chip — re-verify once a chip is actually toggled active.
"""

from config.settings import web_url
from core.web.base_page import BasePage

PATH = "/web/qatar-chamber/business-opportunities"

# Sidebar/quick filters, keyed the way every case in this batch names them.
FILTER_KEYS = ("sector", "country", "investment_type", "investment_amount", "timeline", "risk_profile")

# The two Status Tab values this feature always shows.
TAB_KEYS = ("active", "archive")


class BusinessOpportunitiesListingPage(BasePage):
    # ---- Hero ---------------------------------------------------------------
    HERO = "header.qc-bol-hero"  # Listing page hero section container
    HERO_EYEBROW = "p.qc-bol-eyebrow"  # hero eyebrow label ("Global opportunity gateway")
    HERO_TITLE = "h1.qc-bol-title"  # hero page title ("Global Business Opportunities")
    HERO_DESCRIPTION = ".qc-bol-hero-desc"  # hero description text
    HERO_IMAGE = "img.qc-bol-hero-img"  # hero background/banner image
    HERO_CTA = "a.qc-bol-cta"  # hero "Submit Opportunity" CTA button

    # ---- Search bar -----------------------------------------------------------
    SEARCH_INPUT = "input.qc-bol-search-input"  # search keyword input
    SEARCH_CLEAR_ICON = "TODO(locator): search input clear (x) icon — not rendered on the live search bar at extraction time; flag for dev-added data-testid"
    SEARCH_ICON = "span.qc-bol-search-icon"  # search input's leading search icon

    # ---- Trending chips ---------------------------------------------------
    TRENDING_CHIPS_ROW = "span.qc-bol-chips"  # trending chips row container
    TRENDING_CHIP = "button.qc-bol-chip"  # one trending chip (pill) — labels observed: Energy, Infrastructure, Technology, Licensing route, Qatar
    TRENDING_CHIP_ACTIVE = "button.qc-bol-chip.is-active"  # TODO(locator): `is-active` mirrored from the confirmed .qc-bol-tab pattern, not independently observed on a chip — re-verify once a chip is toggled

    # ---- Sidebar filters ----------------------------------------------------
    FILTERS_PANEL = "div.qc-bol-side-body"  # sidebar filters panel/drawer
    FILTERS_TOGGLE = "button.qc-bol-side-head"  # "Refine results" collapsible header (also acts as filters toggle)
    APPLY_BUTTON = "button.qc-bol-apply"  # filters "Apply" button
    RESET_BUTTON = "button.qc-bol-reset"  # filters "Reset" button

    # 6 <select> fields render in DOM order (aria labels confirmed via
    # extract_locators.py: "All Sectors", "All Countries", "Investment Type",
    # "Investment Amount", "Timeline", "Risk Profile") with no stable
    # name/id/data-testid — positional CSS is the highest confirmed tier.
    FILTER_LOCATORS = {
        "sector": ".qc-bol-selects .qc-bol-field:nth-of-type(1) select",  # "All Sectors" dropdown
        "country": ".qc-bol-selects .qc-bol-field:nth-of-type(2) select",  # "All Countries" dropdown
        "investment_type": ".qc-bol-selects .qc-bol-field:nth-of-type(3) select",  # "Investment Type" dropdown
        "investment_amount": ".qc-bol-selects .qc-bol-field:nth-of-type(4) select",  # "Investment Amount" dropdown
        "timeline": ".qc-bol-selects .qc-bol-field:nth-of-type(5) select",  # "Timeline" dropdown
        "risk_profile": ".qc-bol-selects .qc-bol-field:nth-of-type(6) select",  # "Risk Profile" dropdown
    }

    # ---- Sort By ------------------------------------------------------------
    SORT_DROPDOWN = "div.qc-bol-sort select.qc-bol-select-input"  # "Sort opportunities" dropdown

    # ---- Status tabs --------------------------------------------------------
    TAB_LOCATORS = {
        "active": "div.qc-bol-tabs button.qc-bol-tab:nth-of-type(1)",  # "Active Opportunities" tab
        "archive": "div.qc-bol-tabs button.qc-bol-tab:nth-of-type(2)",  # "Archive" tab
    }
    TAB_COUNT_LOCATORS = {
        "active": "div.qc-bol-tabs button.qc-bol-tab:nth-of-type(1) span.qc-bol-tab-count",  # Active tab count badge, e.g. "(4)"
        "archive": "div.qc-bol-tabs button.qc-bol-tab:nth-of-type(2) span.qc-bol-tab-count",  # Archive tab count badge, e.g. "(2)"
    }
    TAB_ACTIVE_STATE_CLASS = "is-active"  # confirmed on the Active Opportunities tab

    # ---- Card grid ------------------------------------------------------------
    CARD_GRID = "div.qc-bol-grid"  # opportunity card grid container
    CARD = "a.qc-bol-card"  # one opportunity card (whole card is a link)
    CARD_BANNER_IMG = "img.qc-bol-card-img"  # card banner image
    CARD_TITLE = "span.qc-bol-card-title"  # card title text
    CARD_TAG = "span.qc-bol-card-cat"  # card Sector x Investment Type tag
    CARD_COUNTRY = "span.qc-bol-card-info span.qc-bol-card-cell:nth-of-type(1)"  # card country cell
    CARD_COUNTRY_ICON = "TODO(locator): card location pin icon — no distinct icon element observed next to the country cell text; flag for dev-added data-testid"
    CARD_AMOUNT = "span.qc-bol-card-info span.qc-bol-card-cell:nth-of-type(2)"  # card investment amount cell
    CARD_VIEW_DETAILS_LINK = "span.qc-bol-view"  # card "View Details" label (the whole `a.qc-bol-card` is the actual click target)
    NO_RESULTS_MESSAGE = "p.qc-bol-empty"  # "No results found." empty-state message

    # ---- Load More ------------------------------------------------------------
    LOAD_MORE_BUTTON = "button.qc-bol-more"  # "Load More" button
    LOAD_MORE_SPINNER = "TODO(locator): Load More loading/spinner state — not observed (only 4 Active / 2 Archive items exist at extraction time, never enough to trigger a visible loading state); flag for dev-added data-testid"

    # ---- Accessibility / theme -------------------------------------------
    # Confirmed live and shared with web/pages/components/accessibility_tools_component.py
    ACCESSIBILITY_TRAY_OPEN = 'button[aria-label="Accessibility tools"]'  # accessibility tray opener
    DARK_MODE_TOGGLE = "button.qc-a11y-switch[data-qc-a11y-dark]"  # dark-mode toggle
    HIGH_CONTRAST_TOGGLE = "button.qc-a11y-switch[data-qc-a11y-contrast]"  # high-contrast toggle

    # ---- Navigation -----------------------------------------------------------
    def open_listing(self, locale: str = "en") -> "BusinessOpportunitiesListingPage":
        self.open(web_url(PATH, locale=locale))
        self.wait_for(self.CARD_GRID, state="visible", timeout=30000)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    # ---- Hero -----------------------------------------------------------------
    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW).strip()

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_description_text(self) -> str:
        return self.text(self.HERO_DESCRIPTION).strip()

    def hero_image_loaded(self) -> bool:
        return self.page.locator(self.HERO_IMAGE).evaluate(
            "(img) => img.complete === true && img.naturalWidth > 0"
        )

    def click_hero_cta(self) -> None:
        self.click(self.HERO_CTA)

    # ---- Search -----------------------------------------------------------
    def search(self, keyword: str) -> "BusinessOpportunitiesListingPage":
        self.type(self.SEARCH_INPUT, keyword)
        self.press_key("Enter")
        return self

    def search_input_value(self) -> str:
        return self.get_attribute(self.SEARCH_INPUT, "value") or ""

    def is_search_clear_icon_visible(self) -> bool:
        return self.is_visible(self.SEARCH_CLEAR_ICON)

    def clear_search(self) -> None:
        self.click(self.SEARCH_CLEAR_ICON)

    def no_results_message_text(self) -> str:
        return self.text(self.NO_RESULTS_MESSAGE).strip()

    def is_no_results_message_visible(self) -> bool:
        return self.is_visible(self.NO_RESULTS_MESSAGE)

    # ---- Trending chips -----------------------------------------------------
    def trending_chip_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.TRENDING_CHIP).all_inner_texts()]

    def click_trending_chip(self, label: str) -> "BusinessOpportunitiesListingPage":
        self.click(f"{self.TRENDING_CHIP}:has-text('{label}')")
        return self

    def active_trending_chip_label(self) -> str:
        return self.text(self.TRENDING_CHIP_ACTIVE).strip()

    # ---- Sidebar filters ----------------------------------------------------
    def open_filters_panel(self) -> None:
        self.click(self.FILTERS_TOGGLE)

    def is_filters_panel_open(self) -> bool:
        return self.is_visible(self.FILTERS_PANEL)

    def filter_options(self, filter_key: str) -> list:
        return [t.strip() for t in self.page.locator(f"{self.FILTER_LOCATORS[filter_key]} option").all_inner_texts()]

    def select_filter(self, filter_key: str, value: str) -> None:
        self.select_option(self.FILTER_LOCATORS[filter_key], label=value)

    def selected_filter_value(self, filter_key: str) -> str:
        loc = self.page.locator(self.FILTER_LOCATORS[filter_key])
        return loc.locator("option:checked").inner_text().strip()

    def apply_filters(self) -> "BusinessOpportunitiesListingPage":
        self.click(self.APPLY_BUTTON)
        return self

    def reset_filters(self) -> "BusinessOpportunitiesListingPage":
        self.click(self.RESET_BUTTON)
        return self

    # ---- Sort By ------------------------------------------------------------
    def select_sort(self, value: str) -> None:
        self.select_option(self.SORT_DROPDOWN, label=value)

    def selected_sort_value(self) -> str:
        return self.page.locator(self.SORT_DROPDOWN).locator("option:checked").inner_text().strip()

    def sort_options(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.SORT_DROPDOWN} option").all_inner_texts()]

    # ---- Status tabs --------------------------------------------------------
    def switch_tab(self, tab_key: str) -> "BusinessOpportunitiesListingPage":
        self.click(self.TAB_LOCATORS[tab_key])
        return self

    def is_tab_active(self, tab_key: str) -> bool:
        classes = self.get_attribute(self.TAB_LOCATORS[tab_key], "class") or ""
        return self.TAB_ACTIVE_STATE_CLASS in classes

    def tab_count(self, tab_key: str) -> str:
        return self.text(self.TAB_COUNT_LOCATORS[tab_key]).strip()

    # ---- Card grid --------------------------------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return [t.strip() for t in self.page.locator(self.CARD_TITLE).all_inner_texts()]

    def card_tags(self) -> list:
        return [t.strip() for t in self.page.locator(self.CARD_TAG).all_inner_texts()]

    def card_countries(self) -> list:
        return [t.strip() for t in self.page.locator(self.CARD_COUNTRY).all_inner_texts()]

    def card_amounts(self) -> list:
        return [t.strip() for t in self.page.locator(self.CARD_AMOUNT).all_inner_texts()]

    def card_country_icon_visible(self, index: int = 0) -> bool:
        return self.is_visible(f"{self.CARD} >> nth={index} >> {self.CARD_COUNTRY_ICON}")

    def card_banner_loaded(self, index: int = 0) -> bool:
        return self.page.locator(self.CARD_BANNER_IMG).nth(index).evaluate(
            "(img) => img.complete === true && img.naturalWidth > 0"
        )

    def click_view_details_by_title(self, title: str) -> None:
        card = self.page.locator(self.CARD, has_text=title)
        card.locator(self.CARD_VIEW_DETAILS_LINK).click()

    # ---- Load More ----------------------------------------------------------
    def click_load_more(self) -> "BusinessOpportunitiesListingPage":
        self.click(self.LOAD_MORE_BUTTON)
        return self

    def is_load_more_visible(self) -> bool:
        return self.is_visible(self.LOAD_MORE_BUTTON)

    def is_load_more_loading(self) -> bool:
        return self.is_visible(self.LOAD_MORE_SPINNER)

    # ---- Accessibility / theme -------------------------------------------
    def open_accessibility_tray(self) -> None:
        self.click(self.ACCESSIBILITY_TRAY_OPEN)

    def toggle_dark_mode(self) -> None:
        self.click(self.DARK_MODE_TOGGLE)

    def is_dark_mode(self) -> bool:
        return "dark" in (self.get_attribute("html", "class") or "")

    def toggle_high_contrast(self) -> None:
        self.click(self.HIGH_CONTRAST_TOGGLE)

    def is_high_contrast(self) -> bool:
        return "high-contrast" in (self.get_attribute("html", "class") or "")

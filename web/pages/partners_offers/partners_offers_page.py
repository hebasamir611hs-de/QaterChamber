"""
web/pages/partners_offers/partners_offers_page.py — PartnersOffersPage.

Public-frontend Page Object for PBI 130720 "QC - Councils, Committees &
Partnerships - 005 - Partners & Offers" — a public offer-listing page under
the Councils, Committees & Partnerships area, with a category filter, an
offer-card grid, "Load More" pagination and an "Offer Details" modal
(header/description/validity+tier/terms/footer, with a "Contract"/"Open
contract" action).

LOCATORS — CLI-first, verified live 2026-09-22 (qcdev)
------------------------------------------------------------------
Real path resolved via the Liferay nav-items REST API
(`/o/c/navitems/scopes/37246?...`): `/web/qatar-chamber/partners-offers`.
An ad-hoc structural dump (scripted `document.querySelectorAll` class walk,
not MCP) confirmed the real CSS namespace is `qc-po__*` (BEM), not the
guessed structure-only placeholders. The Offer Details modal — DOM-present
but empty until opened — was then opened for real
(`button.qc-po__details` click) to confirm its populated header/body/footer
markup, including the "Open contract" link's real target (an attachment
URL opened in a new tab, confirmed via its `target="_blank"` attribute).

The category filter is a custom combobox (`button` + `ul` of `li` options
with a stable `id` per option, `#qc-po-option-0..9`), not a native
`<select>`. `select_category()` therefore drives it the way a user does —
click the trigger button, then click the option by its visible label — and
does NOT use `select_option()`, which assumes a real `<select>` element.
The nine live categories each hold exactly one published offer, so no
zero-offer category exists to reach the per-category empty state without a
CMS authoring write.
"""

from core.web.base_page import BasePage
from config.settings import web_url

PATH = "/web/qatar-chamber/partners-offers"


class PartnersOffersPage(BasePage):
    # ---- Root / hero --------------------------------------------------------
    ROOT = "section.qc-po"
    HERO = "div.qc-po__hero"
    BREADCRUMB = "nav.qc-po__breadcrumb"
    BREADCRUMB_ITEM = "li.qc-po__breadcrumb-item"
    HERO_EYEBROW = "p.qc-po__hero-eyebrow"
    HERO_TITLE = "h1.qc-po__hero-title"
    HERO_DESCRIPTION = "p.qc-po__hero-description"

    # ---- Offers section header ----------------------------------------------
    SECTION_EYEBROW = "p.qc-po__section-eyebrow"
    SECTION_HEADING = "h2.qc-po__section-heading"
    SECTION_DESCRIPTION = "p.qc-po__section-description"

    # ---- Filter bar -----------------------------------------------------------
    # Custom combobox (button + ul/li options), NOT a native <select> —
    # CATEGORY_DROPDOWN resolves the trigger button and select_category()
    # clicks the trigger then the option, as a user does. Options carry
    # stable ids (#qc-po-option-0..9) confirmed live: 0=All Categories, 1=Medical
    # Centers, 2=Hotels and Resorts, 3=Restaurants, 4=Beauty and Fitness,
    # 5=ISP, 6=Retail, 7=Hospitality, 8=Shops, 9=General.
    CATEGORY_DROPDOWN = "button.qc-po__combo-button"
    CATEGORY_OPTION_LIST = "ul.qc-po__combo-list"
    CATEGORY_OPTION = "li.qc-po__combo-option"
    RESET_BUTTON = "button.qc-po__reset"
    FIND_BUTTON = "button.qc-po__find"

    # ---- Offer grid / cards -----------------------------------------------------
    GRID = "div.qc-po__grid"
    CARD = "article.qc-po__card"
    CARD_LOGO = "div.qc-po__logo img.qc-po__logo-image"
    CARD_CATEGORY_LABEL = "p.qc-po__card-category"
    CARD_PARTNER_NAME = "p.qc-po__card-partner"
    CARD_LOCATION = "p.qc-po__card-location"
    CARD_DESCRIPTION_PANEL = "div.qc-po__offer"
    CARD_VALIDITY_ROW = "div.qc-po__validity"
    CARD_TIER_BADGE = "span.qc-po__tier"
    CARD_OFFER_DETAILS_BUTTON = "button.qc-po__details"
    CARD_CONTRACT_BUTTON = "a.qc-po__contract"

    # ---- Load more / empty state -------------------------------------------------
    LOAD_MORE_BUTTON = "button.qc-po__load-more"
    EMPTY_STATE_MESSAGE = "p.qc-po__empty"

    # ---- Offer Details modal ---------------------------------------------------
    # Confirmed by actually opening the modal (button.qc-po__details click),
    # not just present-in-DOM structure — it is empty until opened.
    MODAL_OVERLAY = "div.qc-po__modal-backdrop"
    MODAL_DIALOG = "div.qc-po__modal-dialog"
    MODAL_CLOSE_X = "button.qc-po__modal-close"
    MODAL_HEADER = "div.qc-po__modal-head"
    MODAL_PARTNER_LOGO = "img.qc-po__modal-logo-image"
    MODAL_CATEGORY_LABEL = "div.qc-po__modal-head p.qc-po__card-category"
    MODAL_PARTNER_NAME = "div.qc-po__modal-head p.qc-po__card-partner"
    MODAL_LOCATION = "div.qc-po__modal-head p.qc-po__card-location"
    MODAL_DESCRIPTION_PANEL = "div.qc-po__modal-offer"
    MODAL_VALIDITY_ROW = "div.qc-po__modal-body div.qc-po__validity"
    MODAL_TIER_BADGE = "div.qc-po__modal-body span.qc-po__tier"
    MODAL_TERMS_SECTION = "p.qc-po__modal-terms"
    MODAL_FOOTER = "div.qc-po__modal-actions"
    MODAL_CLOSE_BUTTON = "button.qc-po__modal-secondary"
    MODAL_OPEN_CONTRACT_BUTTON = "a.qc-po__modal-primary"

    # =========================================================================
    # Navigation
    # =========================================================================
    def open_partners_offers(self, locale: str = "en") -> "PartnersOffersPage":
        self.open(web_url(PATH, locale=locale))
        self.wait_for(self.HERO_TITLE, state="visible", timeout=30000)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    # ---- Generic measurement helpers (mirrors the other qc-<page> Page
    # Objects in this suite, e.g. legal_consultation_page.py) ------------------
    def box(self, locator: str, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).bounding_box()

    def computed_style(self, locator: str, props: list, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el, props) => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = s[p];
                return out;
            }
            """,
            props,
        )

    def overflow_metrics(self, locator: str, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el) => {
                const s = getComputedStyle(el);
                return {
                    scrollWidth: el.scrollWidth, clientWidth: el.clientWidth,
                    scrollHeight: el.scrollHeight, clientHeight: el.clientHeight,
                    overflowX: s.overflowX, overflowY: s.overflowY,
                };
            }
            """
        )

    def has_horizontal_scrollbar(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    # =========================================================================
    # Hero
    # =========================================================================
    def breadcrumb_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.BREADCRUMB_ITEM).all_inner_texts()]

    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW).strip()

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_description_text(self) -> str:
        return self.text(self.HERO_DESCRIPTION).strip()

    def hero_background_image(self) -> str:
        return self.computed_style(self.HERO, ["backgroundImage"])["backgroundImage"]

    # =========================================================================
    # Offers section header
    # =========================================================================
    def section_eyebrow_text(self) -> str:
        return self.text(self.SECTION_EYEBROW).strip()

    def section_heading_text(self) -> str:
        return self.text(self.SECTION_HEADING).strip()

    def section_description_text(self) -> str:
        return self.text(self.SECTION_DESCRIPTION).strip()

    # =========================================================================
    # Filter bar
    # =========================================================================
    def dropdown_placeholder_text(self) -> str:
        return self.text(self.CATEGORY_DROPDOWN).strip()

    def select_category(self, label: str) -> "PartnersOffersPage":
        """Open the custom combobox and pick an option by its visible label.

        The control is a `button` + `ul`/`li` listbox, not a `<select>`, so it
        is driven by two clicks exactly as a user drives it.
        """
        self.click(self.CATEGORY_DROPDOWN)
        self.wait_for(self.CATEGORY_OPTION_LIST, state="visible", timeout=10000)
        self.page.locator(self.CATEGORY_OPTION).filter(has_text=label).first.click()
        self.page.wait_for_function(
            "([sel, want]) => document.querySelector(sel)"
            "  && document.querySelector(sel).textContent.trim() === want",
            arg=[self.CATEGORY_DROPDOWN, label],
            timeout=10000,
        )
        return self

    def available_categories(self) -> list:
        """Every option label the combobox offers, in listbox order."""
        return [t.strip() for t in self.page.locator(self.CATEGORY_OPTION).all_inner_texts()]

    OFFERS_API_PATH = "/qc-partners-offers-api/offers"

    def _click_and_await_grid(self, locator: str) -> None:
        """Click a filter-bar control and block until the grid has re-rendered.

        Find and Reset both fire an async request to the offers API and repaint
        the grid from its response. Without this wait a following read of
        cards() races the repaint and sees the PREVIOUS filter's cards.
        """
        with self.page.expect_response(
            lambda r: self.OFFERS_API_PATH in r.url, timeout=20000
        ) as response_info:
            self.click(locator)
        payload = response_info.value.json()
        expected = len(payload.get("items", []))
        self.page.wait_for_function(
            "([cardSel, want]) => document.querySelectorAll(cardSel).length === want",
            arg=[self.CARD, expected],
            timeout=15000,
        )

    def click_find(self) -> "PartnersOffersPage":
        self._click_and_await_grid(self.FIND_BUTTON)
        return self

    def click_reset(self) -> "PartnersOffersPage":
        self._click_and_await_grid(self.RESET_BUTTON)
        return self

    # =========================================================================
    # Offer cards / grid
    # =========================================================================
    def offer_card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def cards(self) -> list:
        """One record per rendered offer card, in DOM (display) order —
        everything the card-content and tier-badge cases assert on, harvested
        in one round-trip so every card is read at the same layout."""
        return self.page.evaluate(
            """
            ([cardSel, logoSel, categorySel, nameSel, locSel, descSel,
              validitySel, tierSel, detailsSel, contractSel]) =>
                Array.from(document.querySelectorAll(cardSel)).map((card) => {
                    const q = (sel) => card.querySelector(sel);
                    const logo = q(logoSel), category = q(categorySel), name = q(nameSel),
                          loc = q(locSel), desc = q(descSel), validity = q(validitySel),
                          tier = q(tierSel), details = q(detailsSel), contract = q(contractSel);
                    return {
                        hasLogo: !!logo,
                        category: category ? category.textContent.trim() : null,
                        partnerName: name ? name.textContent.trim() : null,
                        location: loc ? loc.textContent.trim() : null,
                        description: desc ? desc.textContent.trim() : null,
                        validityText: validity ? validity.textContent.trim() : null,
                        tierLabel: tier ? tier.textContent.trim() : null,
                        hasOfferDetailsAction: !!details,
                        hasContractAction: !!contract,
                    };
                })
            """,
            [
                self.CARD, self.CARD_LOGO, self.CARD_CATEGORY_LABEL, self.CARD_PARTNER_NAME,
                self.CARD_LOCATION, self.CARD_DESCRIPTION_PANEL, self.CARD_VALIDITY_ROW,
                self.CARD_TIER_BADGE, self.CARD_OFFER_DETAILS_BUTTON, self.CARD_CONTRACT_BUTTON,
            ],
        )

    def card_top_positions(self) -> list:
        """Top-left {x, y} of every card, in DOM order — used to derive the
        rendered column count without hard-coding a breakpoint width."""
        return self.page.locator(self.CARD).evaluate_all(
            "els => els.map(el => { const r = el.getBoundingClientRect(); return {x: r.x, y: r.y}; })"
        )

    def grid_column_count(self) -> int:
        """Number of columns in the first row — the count of cards sharing
        the topmost `y` (within a small tolerance for sub-pixel rounding)."""
        positions = self.card_top_positions()
        if not positions:
            return 0
        top_y = min(p["y"] for p in positions)
        return sum(1 for p in positions if abs(p["y"] - top_y) <= 2)

    def click_offer_details(self, index: int) -> "PartnersOffersPage":
        self.page.locator(self.CARD).nth(index).locator(self.CARD_OFFER_DETAILS_BUTTON).click()
        self.wait_for(self.MODAL_DIALOG, state="visible", timeout=15000)
        return self

    def click_offer_details_by_partner(self, partner_name: str) -> "PartnersOffersPage":
        card = self.page.locator(self.CARD).filter(has_text=partner_name)
        card.locator(self.CARD_OFFER_DETAILS_BUTTON).click()
        self.wait_for(self.MODAL_DIALOG, state="visible", timeout=15000)
        return self

    def card_index_by_partner(self, partner_name: str) -> int:
        names = [c["partnerName"] for c in self.cards()]
        return names.index(partner_name)

    # =========================================================================
    # Load more / empty state
    # =========================================================================
    def load_more_is_visible(self) -> bool:
        """True only while 'Load More' is actually actionable.

        The control is not removed once a filter's offers are exhausted — it
        stays in the DOM with the `disabled` attribute set. TC 144371 reads
        "until the control is hidden/disabled", so a disabled control counts
        as exhausted here; reporting it as still available makes callers click
        a dead button.
        """
        button = self.page.locator(self.LOAD_MORE_BUTTON)
        return button.is_visible() and button.is_enabled()

    def click_load_more(self) -> "PartnersOffersPage":
        count_before = self.offer_card_count()
        self.click(self.LOAD_MORE_BUTTON)
        self.page.wait_for_function(
            "([sel, before]) => document.querySelectorAll(sel).length > before",
            arg=[self.CARD, count_before],
            timeout=15000,
        )
        return self

    def empty_state_text(self) -> str:
        return self.text(self.EMPTY_STATE_MESSAGE).strip()

    # =========================================================================
    # Offer Details modal
    # =========================================================================
    def modal_is_open(self) -> bool:
        return self.is_visible(self.MODAL_DIALOG)

    def modal_state(self) -> dict:
        """Structural read of the open modal — header, description, validity
        + tier, terms and footer — everything TC 144352 checks in one place."""
        return self.page.evaluate(
            """
            ([dialogSel, headerSel, logoSel, categorySel, nameSel, locSel,
              closeSel, descSel, validitySel, tierSel, termsSel, footerSel,
              footerCloseSel, openContractSel]) => {
                const dialog = document.querySelector(dialogSel);
                if (!dialog) return null;
                const q = (sel) => dialog.querySelector(sel);
                return {
                    hasHeader: !!q(headerSel),
                    hasLogo: !!q(logoSel),
                    category: q(categorySel) ? q(categorySel).textContent.trim() : null,
                    partnerName: q(nameSel) ? q(nameSel).textContent.trim() : null,
                    location: q(locSel) ? q(locSel).textContent.trim() : null,
                    hasCloseX: !!q(closeSel),
                    description: q(descSel) ? q(descSel).textContent.trim() : null,
                    validityText: q(validitySel) ? q(validitySel).textContent.trim() : null,
                    tierLabel: q(tierSel) ? q(tierSel).textContent.trim() : null,
                    termsText: q(termsSel) ? q(termsSel).textContent.trim() : null,
                    hasFooter: !!q(footerSel),
                    hasFooterCloseButton: !!q(footerCloseSel),
                    hasOpenContractButton: !!q(openContractSel),
                };
            }
            """,
            [
                self.MODAL_DIALOG, self.MODAL_HEADER, self.MODAL_PARTNER_LOGO,
                self.MODAL_CATEGORY_LABEL, self.MODAL_PARTNER_NAME, self.MODAL_LOCATION,
                self.MODAL_CLOSE_X, self.MODAL_DESCRIPTION_PANEL, self.MODAL_VALIDITY_ROW,
                self.MODAL_TIER_BADGE, self.MODAL_TERMS_SECTION, self.MODAL_FOOTER,
                self.MODAL_CLOSE_BUTTON, self.MODAL_OPEN_CONTRACT_BUTTON,
            ],
        )

    def close_modal_via_x(self) -> "PartnersOffersPage":
        self.click(self.MODAL_CLOSE_X)
        self.wait_for(self.MODAL_DIALOG, state="hidden", timeout=10000)
        return self

    def close_modal_via_footer_close(self) -> "PartnersOffersPage":
        self.click(self.MODAL_CLOSE_BUTTON)
        self.wait_for(self.MODAL_DIALOG, state="hidden", timeout=10000)
        return self

    def close_modal_via_overlay(self) -> "PartnersOffersPage":
        # The backdrop spans the whole viewport and the dialog sits at its
        # centre, so a default centre click lands on the dialog. Click a
        # top-left corner point instead — that is dimmed overlay, outside
        # the dialog, which is what the case means by "click the overlay".
        self.page.locator(self.MODAL_OVERLAY).click(position={"x": 10, "y": 10})
        self.wait_for(self.MODAL_DIALOG, state="hidden", timeout=10000)
        return self

    def close_modal_via_escape(self) -> "PartnersOffersPage":
        self.press_key("Escape")
        self.wait_for(self.MODAL_DIALOG, state="hidden", timeout=10000)
        return self

    def open_contract_new_tab(self):
        """Clicks the modal's 'Open contract' button and returns the new
        Page (tab) it opens, per TC 144369's "opens in a new browser tab;
        the modal remains open behind it"."""
        with self.page.context.expect_page() as new_page_info:
            self.click(self.MODAL_OPEN_CONTRACT_BUTTON)
        return new_page_info.value

    # =========================================================================
    # Scroll position (modal-dismiss restoration cases)
    # =========================================================================
    def scroll_y(self) -> float:
        return self.page.evaluate("() => window.scrollY")

    def scroll_card_into_view(self, index: int) -> "PartnersOffersPage":
        self.page.locator(self.CARD).nth(index).scroll_into_view_if_needed()
        return self

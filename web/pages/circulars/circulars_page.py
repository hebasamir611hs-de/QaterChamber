"""
web/pages/circulars/circulars_page.py — CircularsPage.

Public-frontend Page Object for PBI 129408 (QC-SVC-011 — Circulars),
`/circulars` (Arabic: `/ar/circulars`). This section does NOT have the
friendly-URL locale asymmetry other sections carry: the Arabic slug really is
`ARABIC_PATH_PREFIX + /circulars`, confirmed live from the header language
switcher's own href (`update_language?...&redirect=%2Fcirculars&languageId=ar_SA`),
not guessed. The Liferay friendly URL `/web/qatar-chamber/circulars` serves the
same page and is what the main-menu "Our Services" mega-menu links to.

--- CLI-first extraction log (2026-09-17, qcdev, 1920x1080) ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/en/circulars --max 90

    -> get_by_role("button", name="Reset filters")
    -> get_by_role("button", name="Search")
    -> get_by_role("button", name="Latest Circulars" | "Active Circulars"
                   | "Urgent Circulars" | "Archived Circulars")
    -> get_by_role("button", name="Load More")
    -> get_by_role("button", name="Read Circular: <card title>")   (one per card)
    -> get_by_role("link",   name="Download: <card title>")        (one per card)
    -> get_by_role("textbox", name="Search by title, number, authority, keyword")
    -> get_by_role("textbox", name="DD/MM/YY")
    -> get_by_role("textbox", name="Enter Email address")
    -> get_by_role("combobox", name="All Categories…"/"All Authority…")

The extractor only walks a,button,input,select,textarea,[role],[data-testid],
[data-test],[aria-label],[contenteditable], so it cannot surface the fragment's
own wrapper/structural markup (hero, breadcrumb, card internals, modal
regions). Those were confirmed with a scoped Playwright `evaluate()` DOM probe
against the same live page — still CLI/shell, never the Playwright MCP; the
same disclosed fallback pattern chambers_law_page.py documents. The probe found
that this fragment ships a full set of purpose-built `data-qc-cir-*` hooks,
which is the highest locator tier available here (testid-equivalent), so every
constant below is anchored on one wherever the product provides it and only
falls back to a scoped class for repeating card/modal internals:

    section.qc-cir
      header.qc-cir-hero
        nav[data-qc-cir-crumbs] > a.qc-cir-crumb (+ .is-current) / span.qc-cir-crumb-sep
        .qc-cir-hero-copy   p[data-qc-cir-eyebrow] / h1[data-qc-cir-title] / p[data-qc-cir-desc]
        .qc-cir-hero-art    img[data-qc-cir-hero-img]
        form[data-qc-cir-filters]
          label.qc-cir-field.qc-cir-field-kw  span[data-qc-cir-t="fKeyword"] + input[data-qc-cir-kw]
          label.qc-cir-field  span[data-qc-cir-t="fCategory"]  + select[data-qc-cir-cat]
          label.qc-cir-field  span[data-qc-cir-t="fAuthority"] + select[data-qc-cir-auth]
          label.qc-cir-field  span[data-qc-cir-t="fDate"]      + input[data-qc-cir-date]
          .qc-cir-filter-actions  button[data-qc-cir-reset] + button[data-qc-cir-search]
      .qc-cir-body > .qc-cir-layout
        aside.qc-cir-side
          nav[data-qc-cir-states] > button.qc-cir-state[data-qc-cir-state-key=...]
          form[data-qc-cir-sub]  h2[data-qc-cir-t="subTitle"] / p[data-qc-cir-t="subDesc"]
                                 span[data-qc-cir-t="subEmail"] / input[data-qc-cir-sub-email]
                                 button[data-qc-cir-sub-btn] / p[data-qc-cir-sub-msg]
        .qc-cir-main
          h2[data-qc-cir-heading]
          div[data-qc-cir-chips] > button.qc-cir-chip[data-qc-cir-state-key=...]  (<=768px only)
          div[data-qc-cir-list] > article.qc-cir-card[data-qc-cir-id]
            .qc-cir-card-head  .qc-cir-tags(span.qc-cir-num + span.qc-cir-badge.is-published|.is-archived)
                               .qc-cir-date
            h3.qc-cir-card-title / p.qc-cir-card-desc
            .qc-cir-card-foot  .qc-cir-meta(.qc-cir-cell x2: label+value)
                               .qc-cir-actions(a.qc-cir-btn.is-ghost[download] + button.qc-cir-btn.is-primary)
          p[data-qc-cir-status] / button[data-qc-cir-more]
      div[data-qc-cir-modal]
        div[data-qc-cir-scrim] / div[data-qc-cir-dialog][role=dialog][aria-modal=true]
          .qc-cir-dialog-head  div[data-qc-cir-m-tags] / div[data-qc-cir-m-date] / button[data-qc-cir-x]
          h2[data-qc-cir-m-title] / p[data-qc-cir-m-lead]
          p[data-qc-cir-t="fullText"] / div[data-qc-cir-m-body]
          div[data-qc-cir-m-meta] / div[data-qc-cir-m-counts] / div[data-qc-cir-m-file]
          button[data-qc-cir-close]

--- Waiting strategy (no sleeps, no networkidle) ---

`networkidle` is unusable on this site (the chatbot widget polls continuously),
so nothing here waits on a load state. The listing is re-rendered client-side,
and the live DOM semantics were measured rather than assumed:

  * Search / Reset / a sidebar state change **replace** every `article.qc-cir-card`
    node outright (measured: 0 of the previously-tagged nodes survive).
  * Load More **appends** — every previously-tagged node survives and the new
    ones arrive untagged.

`_tag_cards()` stamps a `data-qa-prev` attribute onto the cards currently in
the DOM; `_wait_for_list_replaced()` / `_wait_for_cards_appended()` then poll
with `page.wait_for_function` on that tag. That is a real outcome-based wait on
the thing the test cares about, not a timer and not a load state.

--- Date control ---

`input[data-qc-cir-date]` ships as `type="text"` with the designed
`placeholder="DD/MM/YY"` and swaps itself to `type="date"` (the native picker)
on focus — confirmed live. `set_publish_date()` therefore focuses it first and
then writes the ISO value a `type="date"` input requires.

The DD/MM/YY contract must NOT be asserted as the placeholder once that swap
has happened. The `placeholder` ATTRIBUTE does survive the swap in the DOM,
but a `type="date"` input NEVER RENDERS its placeholder: the browser replaces
the whole editor with its own locale-driven mask, drawn inside a user-agent
shadow root that `el.shadowRoot`, `innerText` and `textContent` all cannot
reach (all three measured empty/null live 2026-09-17). On this host the mask
the user actually sees is `mm/dd/yyyy` — month-first, four-digit year, from
the editor's own `datetimeformat="M/d/yyyy"` — while the attribute still reads
`DD/MM/YY`. Asserting the attribute after focus therefore passes on a string
the user can never see; that is a false green, and it is what this docstring
previously (wrongly) recommended.

So: `date_placeholder()` is legitimate only BEFORE focus, while the control is
still `type="text"` and the placeholder is genuinely painted. After focus use
`date_rendered_format()`, which assembles the visible mask from the rendered
sub-fields via the accessibility tree — the only public Playwright surface
that exposes what the native editor paints. That format is browser/OS-locale
driven and cannot be set by the site.

--- Dark mode ---

Dark mode on this site is a site-wide `data-theme="dark"` attribute driven by
the Accessibility Tools panel's Dark Mode switch (NOT `prefers-color-scheme`:
a Playwright context with `color_scheme="dark"` leaves the page on
`data-theme="light"`, confirmed live). This Page Object composes the existing
`AccessibilityToolsComponent` to drive that switch rather than re-declaring its
locators.
"""

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent
from web.pages.components.header_component import HeaderComponent

CIRCULARS_PATH = "/circulars"
# Liferay friendly URL the main-menu "Our Services" mega-menu actually links to
# (confirmed live from the menu item's own href) — same page, same fragment.
CIRCULARS_FRIENDLY_PATH = "/web/qatar-chamber/circulars"
HOME_PATH = "/web/qatar-chamber"
SERVICES_PATH = "/web/qatar-chamber/our-services"


class CircularsPage(BasePage):
    # ---- Root -------------------------------------------------------------
    SECTION = "section.qc-cir"

    # ---- Hero / breadcrumb -------------------------------------------------
    HERO = "header.qc-cir-hero"
    BREADCRUMB_NAV = "[data-qc-cir-crumbs]"
    BREADCRUMB_LINKS = "[data-qc-cir-crumbs] a.qc-cir-crumb"
    BREADCRUMB_HOME_LINK = "[data-qc-cir-crumbs] a.qc-cir-crumb:not(.is-current)"
    BREADCRUMB_HOME_ICON = "[data-qc-cir-crumbs] a.qc-cir-crumb:not(.is-current) svg"
    BREADCRUMB_SEPARATOR = "[data-qc-cir-crumbs] .qc-cir-crumb-sep"
    BREADCRUMB_CURRENT = "[data-qc-cir-crumbs] a.qc-cir-crumb.is-current"
    HERO_COPY = ".qc-cir-hero-copy"
    HERO_ART = ".qc-cir-hero-art"
    HERO_EYEBROW = "[data-qc-cir-eyebrow]"
    HERO_TITLE = "[data-qc-cir-title]"
    HERO_DESC = "[data-qc-cir-desc]"
    HERO_IMAGE = "[data-qc-cir-hero-img]"

    # ---- Filter bar --------------------------------------------------------
    FILTER_FORM = "[data-qc-cir-filters]"
    FILTER_FIELDS = "[data-qc-cir-filters] > label.qc-cir-field"
    FILTER_ACTIONS = "[data-qc-cir-filters] .qc-cir-filter-actions"
    KEYWORD_LABEL = '[data-qc-cir-t="fKeyword"]'
    KEYWORD_INPUT = "[data-qc-cir-kw]"
    CATEGORY_LABEL = '[data-qc-cir-t="fCategory"]'
    CATEGORY_SELECT = "[data-qc-cir-cat]"
    AUTHORITY_LABEL = '[data-qc-cir-t="fAuthority"]'
    AUTHORITY_SELECT = "[data-qc-cir-auth]"
    DATE_LABEL = '[data-qc-cir-t="fDate"]'
    DATE_INPUT = "[data-qc-cir-date]"
    RESET_BUTTON = "[data-qc-cir-reset]"
    SEARCH_BUTTON = "[data-qc-cir-search]"

    # ---- Sidebar -----------------------------------------------------------
    SIDEBAR = "aside.qc-cir-side"
    STATE_NAV = "[data-qc-cir-states]"
    STATE_BUTTONS = "[data-qc-cir-states] button.qc-cir-state"
    STATE_BUTTON_ACTIVE = "[data-qc-cir-states] button.qc-cir-state.is-active"

    # ---- Email Subscription widget (sidebar) -------------------------------
    # NOTE: this is the CIRCULARS-section subscription widget, NOT the global
    # footer newsletter widget that NewsletterSubscriptionComponent owns
    # (div.qc-footer-newsletter / form.qc-footer-form). Different markup,
    # different copy, different PBI — composing that component here would be
    # wrong, not reuse. Verified live: both render on this page simultaneously.
    SUBSCRIPTION_FORM = "[data-qc-cir-sub]"
    SUBSCRIPTION_ICON = "[data-qc-cir-sub-tile]"
    SUBSCRIPTION_TITLE = '[data-qc-cir-t="subTitle"]'
    SUBSCRIPTION_DESC = '[data-qc-cir-t="subDesc"]'
    SUBSCRIPTION_EMAIL_LABEL = '[data-qc-cir-t="subEmail"]'
    SUBSCRIPTION_EMAIL_INPUT = "[data-qc-cir-sub-email]"
    SUBSCRIPTION_BUTTON = "[data-qc-cir-sub-btn]"

    # ---- Main column / listing ---------------------------------------------
    MAIN_COLUMN = ".qc-cir-main"
    HEADING = "[data-qc-cir-heading]"
    CHIPS = "[data-qc-cir-chips]"
    CHIP_BUTTONS = "[data-qc-cir-chips] button.qc-cir-chip"
    CHIP_ACTIVE = "[data-qc-cir-chips] button.qc-cir-chip.is-active"
    LIST = "[data-qc-cir-list]"
    STATUS = "[data-qc-cir-status]"
    LOAD_MORE_BUTTON = "[data-qc-cir-more]"

    # ---- Card internals (relative to CARD) ---------------------------------
    CARD = "article.qc-cir-card"
    CARD_NUMBER = ".qc-cir-num"
    CARD_BADGE = ".qc-cir-badge"
    CARD_DATE = ".qc-cir-date"
    CARD_TITLE = ".qc-cir-card-title"
    CARD_DESC = ".qc-cir-card-desc"
    CARD_META = ".qc-cir-meta"
    CARD_CELL_LABEL = ".qc-cir-cell-label"
    CARD_CELL_VALUE = ".qc-cir-cell-value"
    CARD_ACTIONS = ".qc-cir-actions"
    CARD_DOWNLOAD_LINK = ".qc-cir-actions a.qc-cir-btn.is-ghost"
    CARD_READ_BUTTON = ".qc-cir-actions button.qc-cir-btn.is-primary"

    # ---- Modal --------------------------------------------------------------
    MODAL = "[data-qc-cir-modal]"
    MODAL_SCRIM = "[data-qc-cir-scrim]"
    MODAL_DIALOG = "[data-qc-cir-dialog]"
    MODAL_TAGS = "[data-qc-cir-m-tags]"
    MODAL_NUMBER = "[data-qc-cir-m-tags] .qc-cir-num"
    MODAL_BADGE = "[data-qc-cir-m-tags] .qc-cir-badge"
    MODAL_DATE = "[data-qc-cir-m-date]"
    MODAL_TITLE = "[data-qc-cir-m-title]"
    MODAL_LEAD = "[data-qc-cir-m-lead]"
    MODAL_FULLTEXT_KICKER = '[data-qc-cir-t="fullText"]'
    MODAL_BODY = "[data-qc-cir-m-body]"
    MODAL_META = "[data-qc-cir-m-meta]"
    MODAL_META_CELLS = "[data-qc-cir-m-meta] .qc-cir-cell"
    MODAL_COUNTS = "[data-qc-cir-m-counts]"
    MODAL_COUNT_CELLS = "[data-qc-cir-m-counts] .qc-cir-cell"
    MODAL_FILE = "[data-qc-cir-m-file]"
    MODAL_FILE_TITLE = "[data-qc-cir-m-file] .qc-cir-file-title"
    MODAL_DOWNLOAD_LINK = "[data-qc-cir-m-file] a.qc-cir-file-dl"
    MODAL_CLOSE_X = "[data-qc-cir-x]"
    MODAL_CLOSE_BUTTON = "[data-qc-cir-close]"

    # ---- Header (composed, never re-declared) ------------------------------
    NAV_OUR_SERVICES_ITEM = (
        'header.qc-global-site-header >> nav.qc-nav >> '
        'ul.qc-nav-list > li.qc-has-children:has(> a.qc-nav-link:text-is("Our Services"))'
    )
    NAV_SUBMENU = ".qc-nav-sub"
    NAV_CIRCULARS_LINK = 'a:text-is("Circulars")'
    # The desktop nav / mobile hamburger pair is owned by HeaderComponent
    # (see `is_desktop_nav_visible()` / `is_mobile_hamburger_visible()` below,
    # which delegate) — deliberately NOT re-declared here.

    # Internal tag used by the list-update waits (see module docstring).
    _PREV_TAG = "data-qa-prev"

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)
        self.accessibility = AccessibilityToolsComponent(page)

    # ==================== Navigation ====================================
    def open_circulars(self, locale: str = "en") -> "CircularsPage":
        self.open(web_url(CIRCULARS_PATH, locale=locale))
        self.wait_for(self.SECTION)
        self.wait_for(self.CARD, first=True)
        return self

    def open_home(self) -> "CircularsPage":
        self.open(web_url(HOME_PATH))
        self.wait_for(self.header.HEADER)
        return self

    def hover_our_services_menu(self) -> "CircularsPage":
        """Expands the header's "Our Services" mega-menu.

        The live top-level "Our Services" item is an `<a href>` — a plain
        click NAVIGATES to the Services landing page instead of expanding the
        dropdown, so hover is the interaction that actually opens it on
        desktop (confirmed live: `.qc-nav-sub` is not visible before hover and
        is visible after). Same idiom as
        ChambersLawPage.open_via_main_menu()."""
        self.page.locator(self.NAV_OUR_SERVICES_ITEM).first.hover()
        self.page.locator(self.NAV_OUR_SERVICES_ITEM).first.locator(
            self.NAV_SUBMENU
        ).wait_for(state="visible")
        return self

    def is_our_services_submenu_expanded(self) -> bool:
        item = self.page.locator(self.NAV_OUR_SERVICES_ITEM).first
        try:
            return item.locator(self.NAV_SUBMENU).is_visible()
        except Exception:  # noqa: BLE001 — mirrors is_visible()'s contract
            return False

    def circulars_link_href_in_menu(self) -> str:
        item = self.page.locator(self.NAV_OUR_SERVICES_ITEM).first
        link = item.locator(self.NAV_SUBMENU).locator(self.NAV_CIRCULARS_LINK).first
        return link.get_attribute("href") or ""

    def click_circulars_in_menu(self) -> "CircularsPage":
        item = self.page.locator(self.NAV_OUR_SERVICES_ITEM).first
        item.locator(self.NAV_SUBMENU).locator(self.NAV_CIRCULARS_LINK).first.click()
        self.wait_for(self.SECTION, timeout=30000)
        self.wait_for(self.CARD, first=True, timeout=30000)
        return self

    def current_url(self) -> str:
        return self.page.url

    # ---- Hero -------------------------------------------------------------
    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW).strip()

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_description_text(self) -> str:
        return self.text(self.HERO_DESC).strip()

    # ---- Breadcrumb -------------------------------------------------------
    def breadcrumb_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.BREADCRUMB_LINKS).all_inner_texts()]

    def breadcrumb_text(self) -> str:
        return self.text(self.BREADCRUMB_NAV).strip()

    def breadcrumb_home_icon_count(self) -> int:
        return self.page.locator(self.BREADCRUMB_HOME_ICON).count()

    def breadcrumb_separator_count(self) -> int:
        return self.page.locator(self.BREADCRUMB_SEPARATOR).count()

    def breadcrumb_hrefs(self) -> list:
        return self.page.locator(self.BREADCRUMB_LINKS).evaluate_all(
            "els => els.map(e => e.getAttribute('href'))"
        )

    def click_breadcrumb_home(self) -> "CircularsPage":
        self._click_and_await_navigation(self.BREADCRUMB_HOME_LINK)
        return self

    def click_breadcrumb_services(self) -> "CircularsPage":
        self._click_and_await_navigation(self.BREADCRUMB_CURRENT)
        return self

    def _click_and_await_navigation(self, locator: str, timeout: int = 30000) -> None:
        """Clicks a link and waits for the URL to ACTUALLY change.

        `wait_for_load_state("domcontentloaded")` is not usable here: the
        current document is already loaded when the click fires, so it returns
        immediately and the caller reads the OLD url (confirmed live — the
        breadcrumb assertions silently compared `/circulars` against itself).
        Waiting on the url predicate is the real outcome; `networkidle` stays
        off the table on this site (chatbot polling)."""
        before = self.page.url
        self.click(locator)
        self.page.wait_for_url(lambda url: url != before, timeout=timeout)
        self.wait_for(self.header.HEADER, timeout=timeout)

    def page_title(self) -> str:
        return self.page.title()

    def go_back_to_circulars(self) -> "CircularsPage":
        """Browser-back to the Circulars page, then make sure the fragment is
        really mounted.

        Measured live: a back-navigation from the home page restores
        `/circulars` from the back-forward cache with the Circulars fragment
        NOT re-initialised (`section.qc-cir` count 0, still 0 seven seconds
        later). That is a page-restore behaviour of the fragment, unrelated to
        the breadcrumb-target case that needs this helper, so the helper
        reloads once when the restored document comes back empty rather than
        hanging on an element that is never going to mount. Nothing is
        asserted about it here — it is a navigation utility, not an
        expectation."""
        self.page.go_back(wait_until="domcontentloaded")
        try:
            self.wait_for(self.SECTION, timeout=8000)
        except Exception:  # noqa: BLE001 — bfcache restore left the fragment unmounted
            self.page.reload(wait_until="domcontentloaded")
            self.wait_for(self.SECTION, timeout=30000)
        self.wait_for(self.CARD, first=True, timeout=30000)
        return self

    # ==================== Language ======================================
    def switch_language(self) -> "CircularsPage":
        """Clicks the header language switcher and waits for the Circulars
        fragment to re-render in the other locale.

        Deliberately does NOT reuse HeaderComponent.switch_to_arabic() —
        that helper waits on `networkidle`, which this site never reaches
        (the chatbot widget polls continuously; see the project's run
        conventions). The locator itself IS the header component's
        (`HeaderComponent.LANGUAGE_SWITCHER`), so nothing is duplicated —
        only the wait is outcome-based here."""
        before = self.document_language()
        self.click(self.header.LANGUAGE_SWITCHER)
        self.page.wait_for_function(
            "prev => document.documentElement.lang && document.documentElement.lang !== prev",
            arg=before,
            timeout=30000,
        )
        self.wait_for(self.SECTION, timeout=30000)
        self.wait_for(self.CARD, first=True, timeout=30000)
        return self

    def language_switcher_label(self) -> str:
        return self.header.language_switcher_label()

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def document_language(self) -> str:
        return self.page.evaluate("() => document.documentElement.lang")

    # ==================== Internal: list-update waits ====================
    def _tag_cards(self) -> None:
        self.page.evaluate(
            "tag => document.querySelectorAll('article.qc-cir-card')"
            ".forEach(c => c.setAttribute(tag, '1'))",
            self._PREV_TAG,
        )

    def _wait_for_list_replaced(self, timeout: int = 20000) -> None:
        """Waits until every card tagged by `_tag_cards()` has left the DOM —
        the measured signature of a Search / Reset / state-filter re-render."""
        self.page.wait_for_function(
            "tag => document.querySelectorAll('article.qc-cir-card[' + tag + ']').length === 0",
            arg=self._PREV_TAG,
            timeout=timeout,
        )

    def _wait_for_cards_appended(self, timeout: int = 20000) -> None:
        """Waits until at least one card that was NOT tagged by `_tag_cards()`
        is in the DOM — the measured signature of a Load More append."""
        self.page.wait_for_function(
            "tag => document.querySelectorAll('article.qc-cir-card:not([' + tag + '])').length > 0",
            arg=self._PREV_TAG,
            timeout=timeout,
        )

    # ==================== Filter bar: actions ============================
    def set_keyword(self, keyword: str) -> "CircularsPage":
        self.type(self.KEYWORD_INPUT, keyword)
        return self

    def select_category(self, label: str) -> "CircularsPage":
        self.select_option(self.CATEGORY_SELECT, label=label)
        return self

    def select_authority(self, label: str) -> "CircularsPage":
        self.select_option(self.AUTHORITY_SELECT, label=label)
        return self

    def focus_date_control(self) -> "CircularsPage":
        """Focusing is what makes the control become the native date picker
        (`type` flips text -> date) — see the module docstring."""
        self.page.locator(self.DATE_INPUT).click()
        self.page.wait_for_function(
            "() => document.querySelector('[data-qc-cir-date]').type === 'date'",
            timeout=10000,
        )
        return self

    def set_publish_date(self, iso_date: str) -> "CircularsPage":
        """`iso_date` is YYYY-MM-DD — the value format a `type="date"` input
        requires. The DD/MM/YY format contract the QA case names is a separate
        question, asserted via `date_rendered_format()` (NOT via the
        placeholder attribute — see the module docstring)."""
        self.focus_date_control()
        self.page.locator(self.DATE_INPUT).fill(iso_date)
        return self

    def click_search(self) -> "CircularsPage":
        self._tag_cards()
        self.click(self.SEARCH_BUTTON)
        self._wait_for_list_replaced()
        return self

    def click_reset(self) -> "CircularsPage":
        self._tag_cards()
        self.click(self.RESET_BUTTON)
        self._wait_for_list_replaced()
        return self

    # ==================== Filter bar: state ==============================
    def keyword_value(self) -> str:
        return self.page.locator(self.KEYWORD_INPUT).input_value()

    def keyword_placeholder(self) -> str:
        return self.page.locator(self.KEYWORD_INPUT).get_attribute("placeholder") or ""

    def date_placeholder(self) -> str:
        """The `placeholder` ATTRIBUTE. Meaningful ONLY while the control is
        still `type="text"`: a `type="date"` input never renders its
        placeholder, so this keeps returning the designed string long after the
        user has stopped being able to see it. Never assert it after
        `focus_date_control()` — use `date_rendered_format()` instead."""
        return self.page.locator(self.DATE_INPUT).get_attribute("placeholder") or ""

    def date_input_type(self) -> str:
        return self.page.locator(self.DATE_INPUT).get_attribute("type") or ""

    def date_rendered_format(self) -> str:
        """The date mask the USER ACTUALLY SEES in the Select Date control —
        the rendered sub-fields joined in the order the browser paints them
        (e.g. "mm/dd/yyyy", or the typed digits once a value is set).

        Mechanism: once the control becomes `type="date"` its editor lives in a
        user-agent shadow root — `el.shadowRoot` is null and both `innerText`
        and `textContent` are empty (measured live 2026-09-17), so no DOM read
        can see the glyphs. Chromium's accessibility tree does expose them: the
        editor node owns one `spinbutton` per sub-field whose text leaf carries
        the painted glyph, separated by `text` nodes carrying the delimiter.

        Returns "" when no native date editor is rendered (control still
        `type="text"`, or a non-Chromium browser). Deliberately not an
        exception, so the caller reports the format gap rather than an error.
        """
        handle = self.page.locator(self.DATE_INPUT).element_handle()
        snapshot = self.page.accessibility.snapshot(
            root=handle, interesting_only=False
        )
        return "".join(
            self._ax_glyph(field) for field in self._date_editor_fields(snapshot)
        )

    @classmethod
    def _date_editor_fields(cls, node) -> list:
        """The children of the first node that DIRECTLY owns the date editor's
        spinbuttons. Anchoring on that node is what keeps the open calendar
        popup — a sibling subtree full of weekday/day-number text — out of the
        assembled mask."""
        if not node:
            return []
        children = node.get("children") or []
        if any(child.get("role") == "spinbutton" for child in children):
            return children
        for child in children:
            found = cls._date_editor_fields(child)
            if found:
                return found
        return []

    @classmethod
    def _ax_glyph(cls, node) -> str:
        """The glyph one editor node paints: a separator's own name, or a
        sub-field's text leaf ("mm" / "dd" / "yyyy" / the typed digits). The
        sub-field's accessible NAME is deliberately ignored — it is the
        localized field label ("Month Month"), not what is on screen."""
        if node.get("role") == "text":
            return node.get("name") or ""
        for child in node.get("children") or []:
            glyph = cls._ax_glyph(child)
            if glyph:
                return glyph
        return ""

    def date_value(self) -> str:
        return self.page.locator(self.DATE_INPUT).input_value()

    def category_value(self) -> str:
        return self.page.locator(self.CATEGORY_SELECT).input_value()

    def authority_value(self) -> str:
        return self.page.locator(self.AUTHORITY_SELECT).input_value()

    def category_selected_label(self) -> str:
        return self._selected_label(self.CATEGORY_SELECT)

    def authority_selected_label(self) -> str:
        return self._selected_label(self.AUTHORITY_SELECT)

    def _selected_label(self, select_locator: str) -> str:
        return self.page.locator(select_locator).evaluate(
            "el => el.options[el.selectedIndex] ? el.options[el.selectedIndex].text.trim() : ''"
        )

    def category_options(self) -> list:
        return self._option_labels(self.CATEGORY_SELECT)

    def authority_options(self) -> list:
        return self._option_labels(self.AUTHORITY_SELECT)

    def _option_labels(self, select_locator: str) -> list:
        return self.page.locator(select_locator).evaluate(
            "el => Array.from(el.options).map(o => o.text.trim())"
        )

    def filter_field_labels(self) -> list:
        return [t.strip() for t in self.page.locator(
            f"{self.FILTER_FIELDS} > .qc-cir-field-label"
        ).all_inner_texts()]

    def reset_control_label(self) -> str:
        return self.page.locator(self.RESET_BUTTON).get_attribute("aria-label") or ""

    def search_button_text(self) -> str:
        return self.text(self.SEARCH_BUTTON).strip()

    def is_filter_form_visible(self) -> bool:
        return self.is_visible(self.FILTER_FORM)

    # ==================== Sidebar state filters ==========================
    def sidebar_state_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.STATE_BUTTONS).all_inner_texts()]

    def active_state_label(self) -> str:
        """Label of the currently-selected state entry.

        Reads the sidebar's own `.is-active` entry at desktop; at <=768px the
        product hides the sidebar nav and renders the same four entries as a
        chip row above the listing, so falls back to the chips' active entry
        there rather than reporting "no selection"."""
        active = self.page.locator(self.STATE_BUTTON_ACTIVE)
        if active.count() and active.first.is_visible():
            return active.first.inner_text().strip()
        chip = self.page.locator(self.CHIP_ACTIVE)
        if chip.count():
            return chip.first.inner_text().strip()
        return ""

    def select_state(self, label: str) -> "CircularsPage":
        self._tag_cards()
        self.page.locator(self.STATE_BUTTONS, has_text=label).first.click()
        self._wait_for_list_replaced()
        return self

    def is_sidebar_visible(self) -> bool:
        return self.is_visible(self.SIDEBAR)

    def chip_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.CHIP_BUTTONS).all_inner_texts()]

    def are_state_filters_reachable(self) -> bool:
        """True when the four state filters are reachable in SOME rendered
        form — the sidebar nav (desktop) or the chip row (<=768px)."""
        if self.is_visible(self.STATE_NAV) and self.page.locator(self.STATE_BUTTONS).count() == 4:
            return True
        return self.is_visible(self.CHIPS) and self.page.locator(self.CHIP_BUTTONS).count() == 4

    # ==================== Email Subscription widget ======================
    def is_subscription_widget_visible(self) -> bool:
        return self.is_visible(self.SUBSCRIPTION_FORM)

    def subscription_title(self) -> str:
        return self.text(self.SUBSCRIPTION_TITLE).strip()

    def subscription_description(self) -> str:
        return self.text(self.SUBSCRIPTION_DESC).strip()

    def subscription_email_label(self) -> str:
        return self.text(self.SUBSCRIPTION_EMAIL_LABEL).strip()

    def subscription_email_placeholder(self) -> str:
        return self.page.locator(self.SUBSCRIPTION_EMAIL_INPUT).get_attribute("placeholder") or ""

    def subscription_button_text(self) -> str:
        return self.text(self.SUBSCRIPTION_BUTTON).strip()

    def subscription_parts_are_unclipped(self) -> bool:
        """True when each of the widget's four parts renders with a non-zero
        box that sits fully inside the widget's own box (1px tolerance) — a
        real "not clipped" check, not a bare visibility check."""
        widget = self.box(self.SUBSCRIPTION_FORM)
        if not widget:
            return False
        for part in (self.SUBSCRIPTION_TITLE, self.SUBSCRIPTION_DESC,
                     self.SUBSCRIPTION_EMAIL_INPUT, self.SUBSCRIPTION_BUTTON):
            b = self.box(part)
            if not b or b["width"] <= 0 or b["height"] <= 0:
                return False
            if b["x"] < widget["x"] - 1 or b["y"] < widget["y"] - 1:
                return False
            if b["x"] + b["width"] > widget["x"] + widget["width"] + 1:
                return False
            if b["y"] + b["height"] > widget["y"] + widget["height"] + 1:
                return False
        return True

    # ==================== Listing ========================================
    def heading_text(self) -> str:
        return self.text(self.HEADING).strip()

    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_numbers(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_NUMBER}").all_inner_texts()]

    def card_titles(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_TITLE}").all_inner_texts()]

    def card_descriptions(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_DESC}").all_inner_texts()]

    def card_badges(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_BADGE}").all_inner_texts()]

    def card_dates(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_DATE}").all_inner_texts()]

    def card_categories(self) -> list:
        return self._card_cell_values(0)

    def card_authorities(self) -> list:
        return self._card_cell_values(1)

    def card_meta_labels(self) -> list:
        """The two meta-cell LABELS on the first card, in render order."""
        return [t.strip() for t in self.page.locator(self.CARD).first
                .locator(self.CARD_CELL_LABEL).all_inner_texts()]

    def _card_cell_values(self, index: int) -> list:
        return self.page.locator(self.CARD).evaluate_all(
            "(cards, i) => cards.map(c => { const v = c.querySelectorAll('.qc-cir-cell-value');"
            " return v[i] ? v[i].textContent.trim() : ''; })",
            index,
        )

    def is_load_more_offered(self) -> bool:
        loc = self.page.locator(self.LOAD_MORE_BUTTON)
        return bool(loc.count()) and loc.first.is_visible()

    def click_load_more(self) -> "CircularsPage":
        self._tag_cards()
        self.click(self.LOAD_MORE_BUTTON)
        self._wait_for_cards_appended()
        return self

    def load_all_pages(self, max_clicks: int = 20) -> int:
        """Clicks Load More until it stops being offered. Returns the number
        of clicks performed. `max_clicks` is a runaway guard only."""
        clicks = 0
        while self.is_load_more_offered() and clicks < max_clicks:
            before = self.card_count()
            self.click_load_more()
            clicks += 1
            if self.card_count() == before:
                break
        return clicks

    def download_link_labels(self) -> list:
        return [t.strip() for t in self.page.locator(
            f"{self.CARD} {self.CARD_DOWNLOAD_LINK} .qc-cir-btn-label"
        ).all_inner_texts()]

    def read_button_labels(self) -> list:
        return [t.strip() for t in self.page.locator(
            f"{self.CARD} {self.CARD_READ_BUTTON} .qc-cir-btn-label"
        ).all_inner_texts()]

    # ==================== Modal ==========================================
    def open_modal_for_card(self, index: int = 0) -> "CircularsPage":
        self.page.locator(self.CARD).nth(index).locator(self.CARD_READ_BUTTON).click()
        self.wait_for(self.MODAL_DIALOG, state="visible", timeout=20000)
        return self

    def is_modal_open(self) -> bool:
        return self.is_visible(self.MODAL_DIALOG)

    def close_modal_with_x(self) -> "CircularsPage":
        self.click(self.MODAL_CLOSE_X)
        self.wait_for(self.MODAL_DIALOG, state="hidden", timeout=20000)
        return self

    def close_modal_with_close_button(self) -> "CircularsPage":
        self.click(self.MODAL_CLOSE_BUTTON)
        self.wait_for(self.MODAL_DIALOG, state="hidden", timeout=20000)
        return self

    def modal_number(self) -> str:
        return self.text(self.MODAL_NUMBER).strip()

    def modal_badge_text(self) -> str:
        return self.text(self.MODAL_BADGE).strip()

    def modal_date(self) -> str:
        return self.text(self.MODAL_DATE).strip()

    def modal_title(self) -> str:
        return self.text(self.MODAL_TITLE).strip()

    def modal_lead(self) -> str:
        return self.text(self.MODAL_LEAD).strip()

    def modal_fulltext_kicker(self) -> str:
        return self.text(self.MODAL_FULLTEXT_KICKER).strip()

    def modal_body_text(self) -> str:
        return self.text(self.MODAL_BODY).strip()

    def modal_meta(self) -> dict:
        return self._cells_to_dict(self.MODAL_META_CELLS)

    def modal_counts(self) -> dict:
        return self._cells_to_dict(self.MODAL_COUNT_CELLS)

    def _cells_to_dict(self, cells_locator: str) -> dict:
        return self.page.locator(cells_locator).evaluate_all(
            "cells => Object.fromEntries(cells.map(c => ["
            " (c.querySelector('.qc-cir-cell-label')||{textContent:''}).textContent.trim(),"
            " (c.querySelector('.qc-cir-cell-value')||{textContent:''}).textContent.trim()]))"
        )

    def is_modal_attachment_card_visible(self) -> bool:
        return self.is_visible(self.MODAL_FILE)

    def modal_attachment_title(self) -> str:
        return self.text(self.MODAL_FILE_TITLE).strip()

    def modal_download_text(self) -> str:
        return self.text(self.MODAL_DOWNLOAD_LINK).strip()

    def modal_download_href(self) -> str:
        return self.page.locator(self.MODAL_DOWNLOAD_LINK).get_attribute("href") or ""

    # The attachment endpoint every Download action (card + modal) points at.
    ATTACHMENT_URL_FRAGMENT = "qc-circulars-api/attachment"

    def trigger_modal_download(self, timeout: int = 30000) -> dict:
        """Clicks the modal's Download action and returns the attachment
        response's real status + delivery headers.

        Measured live rather than assumed: on this build the anchor's empty
        `download` attribute is NOT honoured by Chromium — the click commits a
        NAVIGATION to `/o/qc-circulars-api/attachment?id=<n>` rather than
        emitting a Playwright `download` event, so `expect_download()` just
        times out while the file is in fact being served correctly. Waiting on
        the RESPONSE instead is behaviour-agnostic (it holds whether the build
        downloads or navigates) and proves more than a download event would:
        the endpoint answers 200 with `Content-Disposition: attachment` and the
        file's own content type."""
        with self.page.expect_response(
            lambda r: self.ATTACHMENT_URL_FRAGMENT in r.url, timeout=timeout
        ) as info:
            self.page.locator(self.MODAL_DOWNLOAD_LINK).click()
        response = info.value
        headers = response.headers
        return {
            "status": response.status,
            "url": response.url,
            "content_disposition": headers.get("content-disposition", ""),
            "content_type": headers.get("content-type", ""),
        }

    def modal_download_tap_target(self) -> dict:
        return self.box(self.MODAL_DOWNLOAD_LINK)

    def modal_metrics(self) -> dict:
        """Box + scroll geometry of the dialog, plus the viewport, for the
        responsive cases' "centred / fits / scrollable rather than cut off"
        assertions."""
        return self.page.locator(self.MODAL_DIALOG).evaluate(
            "el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);"
            " return {x: r.x, y: r.y, width: r.width, height: r.height,"
            " overflowY: cs.overflowY, scrollHeight: el.scrollHeight,"
            " clientHeight: el.clientHeight,"
            " viewportWidth: window.innerWidth, viewportHeight: window.innerHeight}; }"
        )

    # ==================== Scroll =========================================
    def scroll_to(self, y: int) -> "CircularsPage":
        self.page.evaluate("y => window.scrollTo(0, y)", y)
        self.page.wait_for_function("y => Math.abs(window.scrollY - y) < 2", arg=y, timeout=10000)
        return self

    def scroll_offset(self) -> int:
        return self.page.evaluate("() => Math.round(window.scrollY)")

    # ==================== Layout / styling =================================
    def box(self, locator: str) -> dict:
        loc = self.page.locator(locator)
        if loc.count() == 0:
            return None
        return loc.first.bounding_box()

    def boxes(self, locator: str) -> list:
        return self.page.locator(locator).evaluate_all(
            "els => els.map(e => { const r = e.getBoundingClientRect();"
            " return {x: r.x, y: r.y, width: r.width, height: r.height}; })"
        )

    def has_horizontal_scrollbar(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
        )

    def computed_style(self, locator: str, props: list) -> dict:
        return self.page.locator(locator).first.evaluate(
            "(el, props) => { const s = getComputedStyle(el); const o = {};"
            " for (const p of props) o[p] = s[p]; return o; }",
            props,
        )

    def theme(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    def badge_style(self) -> dict:
        return self.computed_style(
            f"{self.CARD} {self.CARD_BADGE}", ["backgroundColor", "color"]
        )

    def card_element_rows(self) -> dict:
        """Row geometry of the first card's badge / metadata / actions —
        for the responsive "metadata above actions" and "badge on the
        mirrored side" assertions."""
        return {
            "card": self.box(self.CARD),
            "badge": self.box(f"{self.CARD} {self.CARD_BADGE}"),
            "date": self.box(f"{self.CARD} {self.CARD_DATE}"),
            "meta": self.box(f"{self.CARD} {self.CARD_META}"),
            "actions": self.box(f"{self.CARD} {self.CARD_ACTIONS}"),
        }

    def first_card_parts_within_card(self) -> bool:
        """True when every rendered part of the first card sits inside the
        card's own box (2px tolerance) — i.e. nothing overflows its
        container. Used by the mobile/tablet "no clipped content / no text
        overflowing its container" assertions."""
        card = self.box(self.CARD)
        if not card:
            return False
        for part in (self.CARD_NUMBER, self.CARD_BADGE, self.CARD_DATE, self.CARD_TITLE,
                     self.CARD_DESC, self.CARD_META, self.CARD_ACTIONS):
            b = self.box(f"{self.CARD} {part}")
            if not b or b["width"] <= 0 or b["height"] <= 0:
                return False
            if b["x"] < card["x"] - 2 or b["x"] + b["width"] > card["x"] + card["width"] + 2:
                return False
            if b["y"] < card["y"] - 2 or b["y"] + b["height"] > card["y"] + card["height"] + 2:
                return False
        return True

    def distinct_rows(self, locator: str, tolerance: int = 4) -> int:
        """Number of distinct rows the matched elements occupy (their `y`
        values clustered within `tolerance` px)."""
        rows = []
        for b in self.boxes(locator):
            if not any(abs(b["y"] - r) <= tolerance for r in rows):
                rows.append(b["y"])
        return len(rows)

    def distinct_columns(self, locator: str, tolerance: int = 4) -> int:
        cols = []
        for b in self.boxes(locator):
            if not any(abs(b["x"] - c) <= tolerance for c in cols):
                cols.append(b["x"])
        return len(cols)

    def is_desktop_nav_visible(self) -> bool:
        return self.header.is_desktop_nav_visible()

    def is_mobile_hamburger_visible(self) -> bool:
        return self.header.is_mobile_hamburger_visible()

    # ---- Named boxes (so tests never hold a selector) ----------------------
    def hero_eyebrow_box(self) -> dict:
        return self.box(self.HERO_EYEBROW)

    def hero_title_box(self) -> dict:
        return self.box(self.HERO_TITLE)

    def hero_desc_box(self) -> dict:
        return self.box(self.HERO_DESC)

    def hero_copy_box(self) -> dict:
        return self.box(self.HERO_COPY)

    def hero_art_box(self) -> dict:
        return self.box(self.HERO_ART)

    def heading_box(self) -> dict:
        return self.box(self.HEADING)

    def sidebar_box(self) -> dict:
        return self.box(self.SIDEBAR)

    def main_column_box(self) -> dict:
        return self.box(self.MAIN_COLUMN)

    def subscription_widget_box(self) -> dict:
        return self.box(self.SUBSCRIPTION_FORM)

    def subscription_button_box(self) -> dict:
        return self.box(self.SUBSCRIPTION_BUTTON)

    def state_button_boxes(self) -> list:
        return self.boxes(self.STATE_BUTTONS)

    def filter_field_boxes(self) -> list:
        return self.boxes(self.FILTER_FIELDS)

    def filter_actions_box(self) -> dict:
        return self.box(self.FILTER_ACTIONS)

    def filter_row_geometry(self) -> dict:
        """The four field boxes AND the Reset/Search actions box measured in
        ONE round-trip, so any layout shift BETWEEN two separate measurement
        calls cannot skew a comparison of the pair. Both are read from the
        same synchronous frame of the same document.

        Returns `{"fields": [ {x, y, width, height}, ... ], "actions": {...}}`
        (`actions` is None when the group is absent).

        Design-drift observation (NOT asserted by any case): at 1920x1080 the
        actions group's bottom edge measures ~4px BELOW the inputs' bottom
        edge, even though the product CSS declares
        `.qc-cir-filters { align-items: flex-end }` with matching 44px control
        heights — the two should bottom-align. Recorded here as an open
        observation only; the Azure case claims solely that the six controls
        render on one row."""
        return self.page.evaluate(
            "([fieldSel, actionSel]) => {"
            " const rect = e => { const r = e.getBoundingClientRect();"
            "   return {x: r.x, y: r.y, width: r.width, height: r.height}; };"
            " const fields = Array.from(document.querySelectorAll(fieldSel)).map(rect);"
            " const a = document.querySelector(actionSel);"
            " return {fields: fields, actions: a ? rect(a) : null}; }",
            [self.FILTER_FIELDS, self.FILTER_ACTIONS],
        )

    def card_box(self) -> dict:
        return self.box(self.CARD)

    def load_more_box(self) -> dict:
        return self.box(self.LOAD_MORE_BUTTON)

    def filter_field_row_count(self) -> int:
        return self.distinct_rows(self.FILTER_FIELDS)

    def filter_field_column_count(self) -> int:
        return self.distinct_columns(self.FILTER_FIELDS)

    def card_action_count(self, index: int = 0) -> int:
        """Number of real actions (links + buttons) rendered on a card —
        the live design ships exactly two: Download and Read Circular."""
        return (
            self.page.locator(self.CARD)
            .nth(index)
            .locator(self.CARD_ACTIONS)
            .locator("a, button")
            .count()
        )

    def is_reset_control_visible(self) -> bool:
        return self.is_visible(self.RESET_BUTTON)

    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    # ---- Named computed styles (so tests never hold a selector) ------------
    _SURFACE_PROPS = ["backgroundColor", "color"]

    def page_background_style(self) -> dict:
        return self.computed_style("body", self._SURFACE_PROPS)

    def site_header_style(self) -> dict:
        return self.computed_style(self.header.HEADER, self._SURFACE_PROPS)

    def section_style(self) -> dict:
        return self.computed_style(self.SECTION, self._SURFACE_PROPS)

    def keyword_input_style(self) -> dict:
        return self.computed_style(
            self.KEYWORD_INPUT,
            ["backgroundColor", "color", "borderColor", "borderWidth", "borderStyle"],
        )

    def category_select_style(self) -> dict:
        return self.computed_style(self.CATEGORY_SELECT, self._SURFACE_PROPS)

    def filter_label_style(self) -> dict:
        return self.computed_style(f"{self.FILTER_FIELDS} > .qc-cir-field-label",
                                   self._SURFACE_PROPS)

    def filter_form_direction(self) -> str:
        return self.computed_style(self.FILTER_FORM, ["direction"])["direction"]

    def heading_text_style(self) -> dict:
        return self.computed_style(self.HEADING, ["direction", "textAlign"])

    def subscription_form_direction(self) -> str:
        return self.computed_style(self.SUBSCRIPTION_FORM, ["direction"])["direction"]

    def subscription_input_style(self) -> dict:
        return self.computed_style(self.SUBSCRIPTION_EMAIL_INPUT, self._SURFACE_PROPS)

    def subscription_button_style(self) -> dict:
        return self.computed_style(self.SUBSCRIPTION_BUTTON, self._SURFACE_PROPS)

    def state_button_styles(self) -> list:
        return self.page.locator(self.STATE_BUTTONS).evaluate_all(
            "els => els.map(e => { const s = getComputedStyle(e);"
            " return {backgroundColor: s.backgroundColor, color: s.color}; })"
        )

    def card_surface_style(self) -> dict:
        return self.computed_style(self.CARD, self._SURFACE_PROPS)

    def card_title_style(self) -> dict:
        return self.computed_style(f"{self.CARD} {self.CARD_TITLE}", self._SURFACE_PROPS)

    def card_cell_value_style(self) -> dict:
        return self.computed_style(f"{self.CARD} {self.CARD_CELL_VALUE}", self._SURFACE_PROPS)

    def modal_dialog_style(self) -> dict:
        return self.computed_style(self.MODAL_DIALOG, self._SURFACE_PROPS)

    def modal_region_styles(self) -> dict:
        """Computed surface styles for every readable region of the modal the
        dark-mode case names — title, full text, metadata, counts, attachment
        card — keyed by a human name so the test asserts on intent, not on a
        selector."""
        return {
            "title": self.computed_style(self.MODAL_TITLE, self._SURFACE_PROPS),
            "full_text": self.computed_style(self.MODAL_BODY, self._SURFACE_PROPS),
            "metadata": self.computed_style(
                f"{self.MODAL_META} {self.CARD_CELL_VALUE}", self._SURFACE_PROPS),
            "counts": self.computed_style(
                f"{self.MODAL_COUNTS} {self.CARD_CELL_VALUE}", self._SURFACE_PROPS),
            "attachment": self.computed_style(self.MODAL_FILE, self._SURFACE_PROPS),
        }

    def modal_badge_style(self) -> dict:
        return self.computed_style(self.MODAL_BADGE, self._SURFACE_PROPS)

    # ==================== Dark mode (composed a11y panel) =================
    def enable_dark_mode(self) -> "CircularsPage":
        """Turns the site-wide Dark Mode on through the Accessibility Tools
        panel — the only control that drives it (see module docstring) — and
        waits for `data-theme` to actually flip before returning."""
        self.accessibility.click_accessibility_button()
        self.wait_for(self.accessibility.PANEL, state="visible", timeout=15000)
        if self.accessibility.dark_mode_toggle_state() != "true":
            self.accessibility.switch_to_dark_mode()
        self.page.wait_for_function(
            "() => document.documentElement.getAttribute('data-theme') === 'dark'",
            timeout=15000,
        )
        self.accessibility.close_panel()
        self.wait_for(self.accessibility.PANEL, state="hidden", timeout=15000)
        return self

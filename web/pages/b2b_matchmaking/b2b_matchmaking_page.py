"""
web/pages/b2b_matchmaking/b2b_matchmaking_page.py — B2bMatchmakingPage.

Public-frontend Page Object for PBI 129409 (QC-SVC-012 — B2B Matchmaking),
`/b2b-matchmaking` (Arabic: `/ar/b2b-matchmaking`). Like Circulars, this
section does NOT carry the friendly-URL locale asymmetry other sections have:
the Arabic slug really is `ARABIC_PATH_PREFIX + /b2b-matchmaking`, read live
off the header language switcher's own href
(`update_language?...&redirect=%2Fb2b-matchmaking&languageId=ar_SA`), not
guessed. The Liferay friendly URL `/web/qatar-chamber/b2b-matchmaking` serves
the same page and is what the main-menu link points at.

--- CLI-first extraction log (2026-09-17, qcdev, 1920x1080) ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/en/b2b-matchmaking --max 60

    -> get_by_role("link",   name="Register Your Company")
    -> get_by_role("textbox", name="Company Name")        (the listing filter)
    -> get_by_role("button", name="Reset filters")
    -> get_by_role("button", name="search")
    -> get_by_role("button", name="View company details: <company>")  (per card)
    -> get_by_role("textbox"/"combobox", name="<Registration field> *") (x17)
    -> get_by_role("button", name="Submit Registration")

The extractor only walks a,button,input,select,textarea,[role],[data-testid],
[data-test],[aria-label],[contenteditable], so it cannot surface this
fragment's own wrapper/structural markup (hero, breadcrumb, card internals,
dialog regions). Those were confirmed with scoped Playwright `evaluate()` DOM
probes against the same live page — still CLI/shell, never the Playwright MCP;
the same disclosed fallback pattern circulars_page.py documents. The probes
found four co-operating fragments on this ONE page, each shipping a
purpose-built testid-tier hook set, so every constant below is anchored on one
of those wherever the product provides it:

  section.qc-b2b[data-qc-b2b-api|-page-size|-register-url|-home-url|-services-url]
    header.qc-b2b-hero
      nav[data-qc-b2b-crumbs] > a.qc-b2b-crumb (svg.qc-b2b-crumb-home on the
                                first) / span.qc-b2b-crumb-sep > svg.qc-b2b-crumb-chevron
      .qc-b2b-hero-grid
        .qc-b2b-hero-copy  p[data-qc-b2b-t="eyebrow"] / h1[data-qc-b2b-t="title"]
                           p[data-qc-b2b-t="lede"]
                           a[data-qc-b2b-cta]  svg.qc-b2b-cta-icon
                                               span[data-qc-b2b-t="register"]
        .qc-b2b-hero-art   img.qc-b2b-hero-img[data-qc-b2b-hero-img]
      form.qc-b2b-search[data-qc-b2b-form]
        .qc-b2b-field.qc-b2b-field-name      label[data-qc-b2b-t="fName"]     + input[data-qc-b2b-name]
        .qc-b2b-field.qc-b2b-field-country   label[data-qc-b2b-t="fCountry"]  + select[data-qc-b2b-country]
        .qc-b2b-field.qc-b2b-field-industry  label[data-qc-b2b-t="fIndustry"] + select[data-qc-b2b-industry]
        .qc-b2b-search-actions  button[data-qc-b2b-reset] + button[data-qc-b2b-submit]
    .qc-b2b-results
      p[data-qc-b2b-status]            (count line AND the empty-state message)
      div[data-qc-b2b-grid] > article.qc-b2b-card[data-qc-b2b-id][role=button][tabindex=0]
        .qc-b2b-card-top   .qc-b2b-logo / .qc-b2b-card-head(h3.qc-b2b-card-name
                                                          + p.qc-b2b-card-industry)
        .qc-b2b-card-meta  .qc-b2b-country(.qc-b2b-flag + span)
                           .qc-b2b-meta-end(.qc-b2b-date + .qc-b2b-badge)
      button[data-qc-b2b-more] > span[data-qc-b2b-t="loadMore"]

  section.qc-b2bd  (the Company Details popup — a SIBLING fragment that listens
                    for the listing's `qc-b2b:open` event; opens in place, no
                    navigation, no URL change)
    div[data-qc-b2bd-backdrop] / div[data-qc-b2bd-dialog][role=dialog][aria-modal=true]
      .qc-b2bd-head   h2[data-qc-b2bd-t="heading"] + button.qc-b2bd-x[data-qc-b2bd-close]
      .qc-b2bd-body[data-qc-b2bd-body]   (the scrolling region)
        p[data-qc-b2bd-state] / div[data-qc-b2bd-content]
          .qc-b2bd-company  [data-qc-b2bd-logo] / [data-qc-b2bd-name]
                            [data-qc-b2bd-industry] / [data-qc-b2bd-badge]
          dl[data-qc-b2bd-fields] > .qc-b2bd-field(dt + dd)
          div[data-qc-b2bd-sections] > section.qc-b2bd-section(h3 + p)
      .qc-b2bd-foot  button.qc-b2bd-btn-close[data-qc-b2bd-close]
                     a.qc-b2bd-btn-contact[data-qc-b2bd-contact]

  section.qc-b2bcf[data-qc-b2bcf-root][data-display-mode="dialog"]
                   (the Contact Company webform — also on this page, opened
                    from the popup's Contact action)
    div[data-qc-b2bcf-overlay] > div[data-qc-b2bcf-dialog]
      header  h2[data-qc-b2bcf-title] / p[data-qc-b2bcf-intro] / button[data-qc-b2bcf-close]
      .qc-b2bcf__scroll   (the scrolling region)
        div[data-qc-b2bcf-status] / div[data-qc-b2bcf-done]
        form[data-qc-b2bcf-form][novalidate]
          div[data-qc-b2bcf-company-panel]  p[data-qc-b2bcf-company-title]
              .qc-b2bcf__ro-label + span[data-qc-b2bcf-company-name]
              .qc-b2bcf__ro-label + span[data-qc-b2bcf-company-contact]
              input[type=hidden][data-qc-f="companyName"|"companyContactPerson"]
          fieldset legend[data-qc-b2bcf-legend-you|-address|-reach|-message]
          .qc-field  label.qc-field__label + [data-qc-f="<name>"]
                     + span.qc-field__error[data-qc-e="<name>"]
          div[data-qc-b2bcf-branch="email"|"phone"]   (the conditional block)
          div[data-qc-recaptcha-field] > div.qc-b2bcf__captcha[data-qc-recaptcha]
          button[data-qc-b2bcf-cancel] / button[data-qc-b2bcf-submit]

  section.qc-b2breg[data-qc-b2breg-root]  (the B2B Registration form — ALSO
                    rendered inline on this same page, below the listing)
    [data-qc-b2breg-eyebrow|-title|-intro] / [data-qc-b2breg-status|-done]
    form[data-qc-b2breg-form] > fieldset x5
        legend[data-qc-b2breg-legend-company|-chamber|-contact|-offer|-files]
        .qc-field  label.qc-field__label + [data-qc-f="<name>"]
                   + span.qc-field__error[data-qc-e="<name>"]
        .qc-b2breg__consent-panel  [data-qc-f="privacyPolicyConsent"]
                                   [data-qc-b2breg-consent-text]
                                   div[data-qc-recaptcha-field] (also `hidden`
                                   here — label "Security Check *", 0x0 rect)
        button[data-qc-b2breg-submit]

**`data-qc-f` / `data-qc-e` are NOT unique on this page** — the Contact form
and the Registration form both use them. Every field/error locator below is
therefore scoped to its own root (`[data-qc-b2bcf-root] ...` /
`[data-qc-b2breg-root] ...`) through `_cf_field()` / `_reg_field()`. Resolving
a bare `[data-qc-f="companyName"]` picks the Contact form's HIDDEN input first
and hangs — measured live.

--- Waiting strategy (no sleeps, no networkidle) ---

`networkidle` is unusable on this site (the chatbot widget polls continuously),
so nothing here waits on a load state. The listing re-renders client-side and
the DOM semantics were MEASURED rather than assumed (2026-09-17):

  * Search / Reset **replace** every `article.qc-b2b-card` node outright —
    0 of the previously-tagged nodes survive, even when the same filter is
    re-submitted and the result set is identical.
  * Load More would **append** (untagged nodes arrive alongside the tagged
    ones) — the same pattern circulars_page.py measured. It cannot currently
    be exercised here: see the page-size note below.

`_tag_cards()` stamps `data-qa-prev` on the cards in the DOM;
`_wait_for_grid_replaced()` / `_wait_for_cards_appended()` poll on that tag
with `page.wait_for_function`. Real outcome-based waits, not timers.

--- Live content baseline (qcdev, 2026-09-17) ---

`GET /o/qc-b2b-matchmaking/companies?page=1&pageSize=12` returns
`totalCount: 3, totalPages: 1` — THREE approved companies:

  Helios Solar Qatar        | Qatar   | Energy    | Yousef Al-Mannai / CEO
  Doha Logistics Hub        | Qatar   | Logistics | Fatima Al-Kuwari / Director of Trade
  Nordwind Renewables GmbH  | Germany | Energy    | Katrin Vogel / Head of Partnerships

The fragment's `data-qc-b2b-page-size` is **12**, so `[data-qc-b2b-more]`
renders `hidden` and Load More is never offered in this environment. That is a
DATA precondition, not a locator problem — `is_load_more_offered()` reports it
truthfully and the affected cases are called out in the test module.

--- Dark mode ---

Dark mode is a site-wide `data-theme="dark"` attribute driven by the
Accessibility Tools panel's Dark Mode switch (NOT `prefers-color-scheme`: a
Playwright context with `color_scheme="dark"` leaves the page on
`data-theme="light"`). This Page Object composes the existing
`AccessibilityToolsComponent` rather than re-declaring its locators.

--- reCAPTCHA ---

reCAPTCHA Enterprise is loaded site-wide (`#qc-recaptcha-enterprise-js`).
`QC.recaptcha` renders a checkbox for a checkbox key and leaves the field
hidden for a score key. Re-measured live 2026-09-17 (qcdev, at 1920x1080 and
768x1024): **BOTH** forms' `[data-qc-recaptcha-field]` render `hidden`
(score key — nothing for a visitor to operate). The Registration form's field
does carry the "Security Check *" label, but the element itself is
`<div class="qc-field" data-qc-recaptcha-field hidden>` with
`display: none`, a null `offsetParent` and a 0x0 rect — it is NOT visible.
(An earlier note here claimed the Registration field was visible; that was
wrong, and it is what made `registration_fields_are_untruncated()` count a
deliberately hidden field as a truncated one.) Both forms validate their own
required fields client-side FIRST:
submitting with a blank required field paints the inline
`[data-qc-e="<field>"]` errors and never reaches the CAPTCHA/network.
`captcha_field_state()` reports what is actually rendered; nothing here stubs,
bypasses or fakes a CAPTCHA.
"""

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent
from web.pages.components.header_component import HeaderComponent

B2B_PATH = "/b2b-matchmaking"
# The Liferay friendly URL the main menu links to — same page, same fragments.
B2B_FRIENDLY_PATH = "/web/qatar-chamber/b2b-matchmaking"
HOME_PATH = "/web/qatar-chamber"
SERVICES_PATH = "/web/qatar-chamber/our-services"
# Where the hero CTA points (read off the live anchor's own href).
REGISTRATION_PATH = "/web/qatar-chamber/b2b-registration"


class B2bMatchmakingPage(BasePage):
    # ---- Root -------------------------------------------------------------
    SECTION = "section.qc-b2b"

    # ---- Hero / breadcrumb -------------------------------------------------
    HERO = "header.qc-b2b-hero"
    BREADCRUMB_NAV = "[data-qc-b2b-crumbs]"
    BREADCRUMB_LINKS = "[data-qc-b2b-crumbs] a.qc-b2b-crumb"
    BREADCRUMB_HOME_LINK = "[data-qc-b2b-crumbs] a.qc-b2b-crumb:has(svg.qc-b2b-crumb-home)"
    BREADCRUMB_SERVICES_LINK = (
        "[data-qc-b2b-crumbs] a.qc-b2b-crumb:not(:has(svg.qc-b2b-crumb-home))"
    )
    BREADCRUMB_HOME_ICON = "[data-qc-b2b-crumbs] svg.qc-b2b-crumb-home"
    BREADCRUMB_SEPARATOR = "[data-qc-b2b-crumbs] .qc-b2b-crumb-sep"
    BREADCRUMB_CHEVRON = "[data-qc-b2b-crumbs] svg.qc-b2b-crumb-chevron"

    HERO_GRID = ".qc-b2b-hero-grid"
    HERO_COPY = ".qc-b2b-hero-copy"
    HERO_ART = ".qc-b2b-hero-art"
    # NOTE: `[data-qc-b2b-hero-img]` alone ALSO matches `section.qc-b2b`, which
    # carries the same attribute as a configuration flag — measured live, it
    # resolved to a 1920x929 box. Always qualify with the img tag.
    HERO_IMAGE = "img.qc-b2b-hero-img"
    HERO_EYEBROW = '[data-qc-b2b-t="eyebrow"]'
    HERO_TITLE = '[data-qc-b2b-t="title"]'
    HERO_LEDE = '[data-qc-b2b-t="lede"]'
    CTA = "[data-qc-b2b-cta]"
    CTA_ICON = "[data-qc-b2b-cta] svg.qc-b2b-cta-icon"
    CTA_LABEL = '[data-qc-b2b-t="register"]'

    # ---- Search bar --------------------------------------------------------
    SEARCH_FORM = "[data-qc-b2b-form]"
    SEARCH_FIELDS = "[data-qc-b2b-form] .qc-b2b-field"
    SEARCH_FIELD_LABELS = "[data-qc-b2b-form] .qc-b2b-label"
    NAME_INPUT = "[data-qc-b2b-name]"
    COUNTRY_SELECT = "[data-qc-b2b-country]"
    INDUSTRY_SELECT = "[data-qc-b2b-industry]"
    SEARCH_ACTIONS = ".qc-b2b-search-actions"
    RESET_BUTTON = "[data-qc-b2b-reset]"
    SEARCH_BUTTON = "[data-qc-b2b-submit]"
    SEARCH_BUTTON_LABEL = '[data-qc-b2b-t="search"]'

    # ---- Results -----------------------------------------------------------
    RESULTS = ".qc-b2b-results"
    STATUS = "[data-qc-b2b-status]"
    GRID = "[data-qc-b2b-grid]"
    CARD = "article.qc-b2b-card"
    CARD_LOGO = ".qc-b2b-logo"
    CARD_HEAD = ".qc-b2b-card-head"
    CARD_NAME = ".qc-b2b-card-name"
    CARD_INDUSTRY = ".qc-b2b-card-industry"
    CARD_META = ".qc-b2b-card-meta"
    CARD_COUNTRY = ".qc-b2b-country"
    CARD_FLAG = ".qc-b2b-flag"
    CARD_META_END = ".qc-b2b-meta-end"
    CARD_DATE = ".qc-b2b-date"
    CARD_BADGE = ".qc-b2b-badge"
    LOAD_MORE = "[data-qc-b2b-more]"
    LOAD_MORE_LABEL = '[data-qc-b2b-t="loadMore"]'

    # ---- Company Details popup --------------------------------------------
    DETAILS_BACKDROP = "[data-qc-b2bd-backdrop]"
    DETAILS_DIALOG = "[data-qc-b2bd-dialog]"
    DETAILS_HEADING = '[data-qc-b2bd-t="heading"]'
    DETAILS_BODY = "[data-qc-b2bd-body]"
    DETAILS_CONTENT = "[data-qc-b2bd-content]"
    DETAILS_LOGO = "[data-qc-b2bd-logo]"
    DETAILS_NAME = "[data-qc-b2bd-name]"
    DETAILS_INDUSTRY = "[data-qc-b2bd-industry]"
    DETAILS_BADGE = "[data-qc-b2bd-badge]"
    DETAILS_FIELDS = "[data-qc-b2bd-fields] .qc-b2bd-field"
    DETAILS_FIELD_TERMS = "[data-qc-b2bd-fields] .qc-b2bd-field dt"
    DETAILS_FIELD_VALUES = "[data-qc-b2bd-fields] .qc-b2bd-field dd"
    DETAILS_SECTIONS = "[data-qc-b2bd-sections] .qc-b2bd-section"
    DETAILS_SECTION_HEADS = "[data-qc-b2bd-sections] .qc-b2bd-section h3"
    DETAILS_SECTION_BODIES = "[data-qc-b2bd-sections] .qc-b2bd-section p"
    DETAILS_LINKS = "[data-qc-b2bd-content] a"
    # Two distinct controls share `data-qc-b2bd-close` (the header X and the
    # footer button) — each is addressed by its own class so neither locator
    # is ambiguous.
    DETAILS_CLOSE_X = "button.qc-b2bd-x[data-qc-b2bd-close]"
    DETAILS_CLOSE_BUTTON = "button.qc-b2bd-btn-close[data-qc-b2bd-close]"
    DETAILS_CONTACT_BUTTON = "[data-qc-b2bd-contact]"
    DETAILS_CONTACT_LABEL = '[data-qc-b2bd-t="contact"]'
    DETAILS_CLOSE_LABEL = '[data-qc-b2bd-t="close"]'

    # ---- Contact Company webform ------------------------------------------
    CF_ROOT = "[data-qc-b2bcf-root]"
    CF_OVERLAY = "[data-qc-b2bcf-overlay]"
    CF_DIALOG = "[data-qc-b2bcf-dialog]"
    CF_SCROLL = "[data-qc-b2bcf-root] .qc-b2bcf__scroll"
    CF_TITLE = "[data-qc-b2bcf-title]"
    CF_INTRO = "[data-qc-b2bcf-intro]"
    CF_CLOSE_X = "[data-qc-b2bcf-close]"
    CF_COMPANY_PANEL = "[data-qc-b2bcf-company-panel]"
    CF_COMPANY_PANEL_TITLE = "[data-qc-b2bcf-company-title]"
    CF_COMPANY_NAME_VALUE = "[data-qc-b2bcf-company-name]"
    CF_COMPANY_CONTACT_VALUE = "[data-qc-b2bcf-company-contact]"
    CF_COMPANY_PANEL_LABELS = "[data-qc-b2bcf-company-panel] .qc-b2bcf__ro-label"
    CF_COMPANY_PANEL_EDITABLES = (
        "[data-qc-b2bcf-company-panel] input:not([type='hidden']), "
        "[data-qc-b2bcf-company-panel] textarea, "
        "[data-qc-b2bcf-company-panel] select, "
        "[data-qc-b2bcf-company-panel] [contenteditable='true']"
    )
    CF_LEGENDS = "[data-qc-b2bcf-form] legend"
    CF_FIELDS = "[data-qc-b2bcf-form] .qc-field"
    CF_LABELS = "[data-qc-b2bcf-form] .qc-field__label"
    CF_EMAIL_BRANCH = '[data-qc-b2bcf-branch="email"]'
    CF_PHONE_BRANCH = '[data-qc-b2bcf-branch="phone"]'
    CF_CAPTCHA_FIELD = "[data-qc-b2bcf-root] [data-qc-recaptcha-field]"
    CF_CAPTCHA_WIDGET = "[data-qc-b2bcf-root] .qc-b2bcf__captcha"
    CF_STATUS = "[data-qc-b2bcf-status]"
    CF_DONE = "[data-qc-b2bcf-done]"
    CF_SUBMIT = "[data-qc-b2bcf-submit]"
    CF_CANCEL = "[data-qc-b2bcf-cancel]"

    # ---- B2B Registration form --------------------------------------------
    REG_ROOT = "[data-qc-b2breg-root]"
    REG_FORM = "[data-qc-b2breg-form]"
    REG_EYEBROW = "[data-qc-b2breg-eyebrow]"
    REG_TITLE = "[data-qc-b2breg-title]"
    REG_INTRO = "[data-qc-b2breg-intro]"
    REG_FIELDSETS = "[data-qc-b2breg-form] fieldset"
    REG_LEGENDS = "[data-qc-b2breg-form] legend"
    REG_FIELDS = "[data-qc-b2breg-form] .qc-field"
    REG_LABELS = "[data-qc-b2breg-form] .qc-field__label"
    REG_CAPTCHA_FIELD = "[data-qc-b2breg-root] [data-qc-recaptcha-field]"
    REG_CONSENT_TEXT = "[data-qc-b2breg-consent-text]"
    REG_STATUS = "[data-qc-b2breg-status]"
    REG_DONE = "[data-qc-b2breg-done]"
    REG_SUBMIT = "[data-qc-b2breg-submit]"

    # ---- Header (composed, never re-declared) ------------------------------
    NAV_OUR_SERVICES_ITEM = (
        "header.qc-global-site-header >> nav.qc-nav >> "
        'ul.qc-nav-list > li.qc-has-children:has(> a.qc-nav-link:text-is("Our Services"))'
    )
    NAV_SUBMENU = ".qc-nav-sub"
    NAV_B2B_MATCHMAKING_LINK = 'a:text-is("B2B Matchmaking")'

    # Internal tag used by the grid-update waits (see module docstring).
    _PREV_TAG = "data-qa-prev"

    # Mandatory registration fields, in the order the live form declares them.
    # Mirrors the PBI's field tables; used by fill_registration_form(except=…)
    # so a test names only the field it is deliberately leaving blank.
    REGISTRATION_REQUIRED_TEXT_FIELDS = (
        "companyName",
        "businessOfferFrom",
        "companyProfileUrl",
        "registeredChamberName",
        "chamberEmailForVerification",
        "contactPerson",
        "email",
        "mobileNumber",
        "summaryOfOffer",
        "companyDescription",
        "potentialPartners",
    )
    REGISTRATION_REQUIRED_SELECTS = ("industryType", "whatAreYouLookingFor")

    CONTACT_REQUIRED_TEXT_FIELDS = ("firstName", "lastName", "commentsOrQuestions")
    CONTACT_REQUIRED_SELECTS = ("industryType", "whatAreYouLookingFor")

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)
        self.accessibility = AccessibilityToolsComponent(page)

    # ==================== Navigation ====================================
    def open_b2b_matchmaking(self, locale: str = "en") -> "B2bMatchmakingPage":
        self.open(web_url(B2B_PATH, locale=locale))
        self.wait_for(self.SECTION)
        self.wait_for(self.CARD, first=True, timeout=30000)
        return self

    def open_home(self) -> "B2bMatchmakingPage":
        self.open(web_url(HOME_PATH))
        self.wait_for(self.header.HEADER)
        return self

    def hover_our_services_menu(self) -> "B2bMatchmakingPage":
        """Expands the header's "Our Services" mega-menu.

        The top-level item is an `<a href>` — a plain click NAVIGATES to the
        Services landing page instead of expanding the dropdown, so hover is
        the interaction that opens it on desktop. Same idiom as
        CircularsPage.hover_our_services_menu()."""
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

    def our_services_submenu_labels(self) -> list:
        item = self.page.locator(self.NAV_OUR_SERVICES_ITEM).first
        return [
            t.strip()
            for t in item.locator(self.NAV_SUBMENU).locator("a").all_inner_texts()
        ]

    def b2b_matchmaking_link_count_in_our_services(self) -> int:
        item = self.page.locator(self.NAV_OUR_SERVICES_ITEM).first
        return item.locator(self.NAV_SUBMENU).locator(
            self.NAV_B2B_MATCHMAKING_LINK
        ).count()

    def b2b_matchmaking_link_href_in_our_services(self) -> str:
        item = self.page.locator(self.NAV_OUR_SERVICES_ITEM).first
        link = item.locator(self.NAV_SUBMENU).locator(
            self.NAV_B2B_MATCHMAKING_LINK
        ).first
        return link.get_attribute("href") or ""

    def click_b2b_matchmaking_in_our_services(self) -> "B2bMatchmakingPage":
        item = self.page.locator(self.NAV_OUR_SERVICES_ITEM).first
        item.locator(self.NAV_SUBMENU).locator(
            self.NAV_B2B_MATCHMAKING_LINK
        ).first.click()
        self.wait_for(self.SECTION, timeout=30000)
        self.wait_for(self.CARD, first=True, timeout=30000)
        return self

    def current_url(self) -> str:
        return self.page.url

    def page_title(self) -> str:
        return self.page.title()

    def body_text(self) -> str:
        return self.page.evaluate("() => document.body.innerText")

    def _click_and_await_navigation(self, locator: str, timeout: int = 30000) -> None:
        """Clicks a link and waits for the URL to ACTUALLY change.

        `wait_for_load_state("domcontentloaded")` is not usable here: the
        current document is already loaded when the click fires, so it returns
        immediately and the caller reads the OLD url. Waiting on the url
        predicate is the real outcome; `networkidle` stays off the table on
        this site (chatbot polling)."""
        before = self.page.url
        self.click(locator)
        self.page.wait_for_url(lambda url: url != before, timeout=timeout)
        self.wait_for(self.header.HEADER, timeout=timeout)

    def click_breadcrumb_home(self) -> "B2bMatchmakingPage":
        self._click_and_await_navigation(self.BREADCRUMB_HOME_LINK)
        return self

    def click_breadcrumb_services(self) -> "B2bMatchmakingPage":
        self._click_and_await_navigation(self.BREADCRUMB_SERVICES_LINK)
        return self

    def go_back_to_b2b_matchmaking(self) -> "B2bMatchmakingPage":
        """Browser-back to the B2B page, then make sure the fragment really
        mounted. A bfcache restore can bring the document back with the
        client-rendered fragment un-initialised (the behaviour
        CircularsPage.go_back_to_circulars() documents), so this reloads once
        when the restored document comes back empty rather than hanging on an
        element that will never appear. Nothing is asserted here — it is a
        navigation utility."""
        self.page.go_back(wait_until="domcontentloaded")
        try:
            self.wait_for(self.SECTION, timeout=8000)
        except Exception:  # noqa: BLE001 — bfcache restore left it unmounted
            self.page.reload(wait_until="domcontentloaded")
            self.wait_for(self.SECTION, timeout=30000)
        self.wait_for(self.CARD, first=True, timeout=30000)
        return self

    def click_register_cta(self, timeout: int = 30000) -> "B2bMatchmakingPage":
        """Clicks the hero's 'Register Your Company' CTA and waits for the URL
        to change. Deliberately does NOT wait for the registration form: what
        the CTA actually reaches is exactly what the case under test asserts,
        so the wait must not presuppose it."""
        self._click_and_await_navigation(self.CTA, timeout=timeout)
        return self

    def cta_href(self) -> str:
        return self.page.locator(self.CTA).first.get_attribute("href") or ""

    # ==================== Language ======================================
    def switch_language(self) -> "B2bMatchmakingPage":
        """Clicks the header language switcher and waits for the fragment to
        re-render in the other locale.

        Deliberately does NOT reuse HeaderComponent.switch_to_arabic(): that
        helper waits on `networkidle`, which this site never reaches. The
        locator itself IS the header component's
        (`HeaderComponent.LANGUAGE_SWITCHER`) — only the wait is
        outcome-based here."""
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

    # ==================== Hero / breadcrumb =============================
    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW).strip()

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_lede_text(self) -> str:
        return self.text(self.HERO_LEDE).strip()

    def cta_label_text(self) -> str:
        return self.text(self.CTA_LABEL).strip()

    def cta_icon_count(self) -> int:
        return self.page.locator(self.CTA_ICON).count()

    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def breadcrumb_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.BREADCRUMB_LINKS).all_inner_texts()]

    def breadcrumb_text(self) -> str:
        return self.text(self.BREADCRUMB_NAV).strip()

    def breadcrumb_home_icon_count(self) -> int:
        return self.page.locator(self.BREADCRUMB_HOME_ICON).count()

    def breadcrumb_separator_count(self) -> int:
        return self.page.locator(self.BREADCRUMB_SEPARATOR).count()

    def breadcrumb_chevron_count(self) -> int:
        return self.page.locator(self.BREADCRUMB_CHEVRON).count()

    def breadcrumb_hrefs(self) -> list:
        return self.page.locator(self.BREADCRUMB_LINKS).evaluate_all(
            "els => els.map(e => e.getAttribute('href'))"
        )

    # ==================== Internal: grid-update waits ====================
    def _tag_cards(self) -> None:
        self.page.evaluate(
            "tag => document.querySelectorAll('article.qc-b2b-card')"
            ".forEach(c => c.setAttribute(tag, '1'))",
            self._PREV_TAG,
        )

    def _wait_for_grid_replaced(self, timeout: int = 20000) -> None:
        """Waits until every card tagged by `_tag_cards()` has left the DOM —
        the measured signature of a Search / Reset re-render (holds even when
        the result set is unchanged: the nodes are rebuilt either way)."""
        self.page.wait_for_function(
            "tag => document.querySelectorAll('article.qc-b2b-card[' + tag + ']').length === 0",
            arg=self._PREV_TAG,
            timeout=timeout,
        )

    def _wait_for_cards_appended(self, timeout: int = 20000) -> None:
        """Waits until at least one card that was NOT tagged by `_tag_cards()`
        is in the DOM — the signature of a Load More append."""
        self.page.wait_for_function(
            "tag => document.querySelectorAll('article.qc-b2b-card:not([' + tag + '])').length > 0",
            arg=self._PREV_TAG,
            timeout=timeout,
        )

    # ==================== Search bar: actions ============================
    def set_company_name(self, fragment: str) -> "B2bMatchmakingPage":
        self.type(self.NAME_INPUT, fragment)
        return self

    def select_country(self, label: str) -> "B2bMatchmakingPage":
        self.select_option(self.COUNTRY_SELECT, label=label)
        return self

    def select_industry(self, label: str) -> "B2bMatchmakingPage":
        self.select_option(self.INDUSTRY_SELECT, label=label)
        return self

    def click_search(self) -> "B2bMatchmakingPage":
        self._tag_cards()
        self.click(self.SEARCH_BUTTON)
        self._wait_for_grid_replaced()
        return self

    def click_reset(self) -> "B2bMatchmakingPage":
        self._tag_cards()
        self.click(self.RESET_BUTTON)
        self._wait_for_grid_replaced()
        return self

    # ==================== Search bar: state ==============================
    def company_name_value(self) -> str:
        return self.page.locator(self.NAME_INPUT).first.input_value()

    def company_name_placeholder(self) -> str:
        return self.page.locator(self.NAME_INPUT).first.get_attribute("placeholder") or ""

    def country_value(self) -> str:
        return self.page.locator(self.COUNTRY_SELECT).first.input_value()

    def industry_value(self) -> str:
        return self.page.locator(self.INDUSTRY_SELECT).first.input_value()

    def country_selected_label(self) -> str:
        return self._selected_label(self.COUNTRY_SELECT)

    def industry_selected_label(self) -> str:
        return self._selected_label(self.INDUSTRY_SELECT)

    def _selected_label(self, select_locator: str) -> str:
        return self.page.locator(select_locator).first.evaluate(
            "el => el.selectedIndex >= 0 ? el.options[el.selectedIndex].textContent.trim() : ''"
        )

    def country_options(self) -> list:
        return self._option_labels(self.COUNTRY_SELECT)

    def industry_options(self) -> list:
        return self._option_labels(self.INDUSTRY_SELECT)

    def _option_labels(self, select_locator: str) -> list:
        return self.page.locator(select_locator).first.evaluate(
            "el => Array.from(el.options).map(o => o.textContent.trim())"
        )

    def search_field_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.SEARCH_FIELD_LABELS).all_inner_texts()]

    def search_button_text(self) -> str:
        return self.text(self.SEARCH_BUTTON_LABEL).strip()

    def reset_control_label(self) -> str:
        return self.page.locator(self.RESET_BUTTON).first.get_attribute("aria-label") or ""

    def is_reset_control_visible(self) -> bool:
        return self.is_visible(self.RESET_BUTTON)

    def is_search_form_visible(self) -> bool:
        return self.is_visible(self.SEARCH_FORM)

    # ==================== Results ========================================
    def status_text(self) -> str:
        return self.text(self.STATUS).strip()

    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_names(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_NAME}").all_inner_texts()]

    def card_industries(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_INDUSTRY}").all_inner_texts()]

    def card_countries(self) -> list:
        return self.page.locator(f"{self.CARD} {self.CARD_COUNTRY}").evaluate_all(
            "els => els.map(e => e.textContent.trim())"
        )

    def card_dates(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_DATE}").all_inner_texts()]

    def card_badges(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_BADGE}").all_inner_texts()]

    def card_aria_labels(self) -> list:
        return self.page.locator(self.CARD).evaluate_all(
            "els => els.map(e => e.getAttribute('aria-label'))"
        )

    def is_load_more_offered(self) -> bool:
        """True only when a visitor can actually see and use Load More.

        Measured live: with 3 approved companies and `data-qc-b2b-page-size=12`
        the button carries the `hidden` attribute, so this reports False. It
        deliberately reads the RENDERED state, not the element's presence in
        the DOM — the button is always in the markup."""
        return self.is_visible(self.LOAD_MORE)

    def load_more_label(self) -> str:
        return self.text(self.LOAD_MORE_LABEL).strip()

    def click_load_more(self) -> "B2bMatchmakingPage":
        self._tag_cards()
        self.click(self.LOAD_MORE)
        self._wait_for_cards_appended()
        return self

    def page_size(self) -> int:
        raw = self.page.locator(self.SECTION).first.get_attribute("data-qc-b2b-page-size")
        return int(raw) if raw and raw.isdigit() else 0

    # ==================== Company Details popup ==========================
    def open_card(self, index: int = 0) -> "B2bMatchmakingPage":
        self.page.locator(self.CARD).nth(index).click()
        self.page.locator(self.DETAILS_CONTENT).wait_for(state="visible", timeout=30000)
        return self

    def open_last_card(self) -> "B2bMatchmakingPage":
        return self.open_card(self.card_count() - 1)

    def is_details_popup_open(self) -> bool:
        return self.is_visible(self.DETAILS_DIALOG)

    def details_heading(self) -> str:
        return self.text(self.DETAILS_HEADING).strip()

    def details_company_name(self) -> str:
        return self.text(self.DETAILS_NAME).strip()

    def details_industry(self) -> str:
        return self.text(self.DETAILS_INDUSTRY).strip()

    def details_badge(self) -> str:
        return self.text(self.DETAILS_BADGE).strip()

    def is_details_logo_rendered(self) -> bool:
        """True when the logo slot actually painted something a visitor can
        see — an <img> or the fragment's inline fallback mark — rather than an
        empty box."""
        return self.page.locator(self.DETAILS_LOGO).first.evaluate(
            "el => { const r = el.getBoundingClientRect();"
            " return r.width > 0 && r.height > 0 && el.children.length > 0; }"
        )

    def details_fields(self) -> dict:
        """The popup's cream field panel as `{term: value}` — asserted on
        intent, never on a selector."""
        return self.page.locator(self.DETAILS_FIELDS).evaluate_all(
            "els => Object.fromEntries(els.map(e => ["
            " e.querySelector('dt').textContent.trim(),"
            " e.querySelector('dd').textContent.trim()]))"
        )

    def details_sections(self) -> dict:
        return self.page.locator(self.DETAILS_SECTIONS).evaluate_all(
            "els => Object.fromEntries(els.map(e => ["
            " e.querySelector('h3').textContent.trim(),"
            " (e.querySelector('p') || {textContent: ''}).textContent.trim()]))"
        )

    def details_hyperlinks(self) -> list:
        """Every hyperlink the popup body renders, as `[text, href]` pairs.

        Used by the "company profile hyperlink" assertion: a visitor can only
        follow a link that is actually rendered as an anchor, so this reads
        the anchors rather than any underlying data value."""
        return self.page.locator(self.DETAILS_LINKS).evaluate_all(
            "els => els.map(e => [e.textContent.trim(), e.getAttribute('href')])"
        )

    def details_close_label(self) -> str:
        return self.text(self.DETAILS_CLOSE_LABEL).strip()

    def details_contact_label(self) -> str:
        return self.text(self.DETAILS_CONTACT_LABEL).strip()

    def is_details_close_action_visible(self) -> bool:
        return self.is_visible(self.DETAILS_CLOSE_BUTTON)

    def is_details_contact_action_visible(self) -> bool:
        return self.is_visible(self.DETAILS_CONTACT_BUTTON)

    def close_details_popup(self) -> "B2bMatchmakingPage":
        self.click(self.DETAILS_CLOSE_BUTTON)
        self.page.locator(self.DETAILS_DIALOG).wait_for(state="hidden", timeout=15000)
        return self

    def close_details_popup_with_x(self) -> "B2bMatchmakingPage":
        self.click(self.DETAILS_CLOSE_X)
        self.page.locator(self.DETAILS_DIALOG).wait_for(state="hidden", timeout=15000)
        return self

    def details_dialog_direction(self) -> str:
        return self.computed_style(self.DETAILS_DIALOG, ["direction"])["direction"]

    def details_field_terms(self) -> list:
        return [t.strip() for t in self.page.locator(self.DETAILS_FIELD_TERMS).all_inner_texts()]

    def details_section_headings(self) -> list:
        return [t.strip() for t in self.page.locator(self.DETAILS_SECTION_HEADS).all_inner_texts()]

    # ---- No-reload sentinel -----------------------------------------------
    def plant_no_reload_sentinel(self, token: str = "qa-sentinel") -> "B2bMatchmakingPage":
        """Writes a value onto `window` that only survives while the SAME
        document lives. Reading it back after an interaction proves the page
        was not reloaded — stronger than comparing URLs, which stay equal
        across a same-URL reload."""
        self.page.evaluate("t => { window.__qa_sentinel = t; }", token)
        return self

    def no_reload_sentinel(self) -> str:
        return self.page.evaluate("() => window.__qa_sentinel || ''")

    # ==================== Contact Company webform ========================
    def open_contact_form(self) -> "B2bMatchmakingPage":
        self.click(self.DETAILS_CONTACT_BUTTON)
        self.page.locator(self.CF_DIALOG).wait_for(state="visible", timeout=30000)
        return self

    def is_contact_form_open(self) -> bool:
        return self.is_visible(self.CF_DIALOG)

    def contact_form_title(self) -> str:
        return self.text(self.CF_TITLE).strip()

    def contact_form_legends(self) -> list:
        return [t.strip() for t in self.page.locator(self.CF_LEGENDS).all_inner_texts()]

    def contact_form_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.CF_LABELS).all_inner_texts()]

    def contact_company_panel_title(self) -> str:
        return self.text(self.CF_COMPANY_PANEL_TITLE).strip()

    def contact_company_panel_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.CF_COMPANY_PANEL_LABELS).all_inner_texts()]

    def contact_company_name_shown(self) -> str:
        """The company name the VISITOR SEES in the webform.

        The product renders it as a `<span>` plus a hidden input that carries
        the posted value. This reads the rendered span — asserting the hidden
        input's `value` would assert something no user can see."""
        return self.text(self.CF_COMPANY_NAME_VALUE).strip()

    def contact_company_contact_shown(self) -> str:
        return self.text(self.CF_COMPANY_CONTACT_VALUE).strip()

    def contact_company_panel_editable_count(self) -> int:
        """How many editable controls the 'You are contacting' panel exposes.

        0 means the two pre-filled values cannot be typed into at all — the
        strongest form of the 'read-only, cannot be redirected to a different
        company' expectation."""
        return self.page.locator(self.CF_COMPANY_PANEL_EDITABLES).count()

    def contact_company_panel_control_tags(self) -> list:
        """Tag name + input type of every control inside the company panel, so
        a test can state exactly what the product renders there."""
        return self.page.locator(self.CF_COMPANY_PANEL).first.evaluate(
            "el => Array.from(el.querySelectorAll('input, textarea, select'))"
            ".map(e => [e.tagName.toLowerCase(), e.getAttribute('type') || '',"
            " e.readOnly === true, e.disabled === true])"
        )

    def try_to_edit_contact_company_name(self, text: str) -> "B2bMatchmakingPage":
        """Attempts to change the pre-filled Company Name the way a visitor
        would: click where the value is painted, then type. Nothing is
        asserted here — the test compares the shown value before and after."""
        self._try_to_edit(self.CF_COMPANY_NAME_VALUE, text)
        return self

    def try_to_edit_contact_company_contact(self, text: str) -> "B2bMatchmakingPage":
        self._try_to_edit(self.CF_COMPANY_CONTACT_VALUE, text)
        return self

    def _try_to_edit(self, locator: str, text: str) -> None:
        target = self.page.locator(locator).first
        try:
            target.click(timeout=5000)
        except Exception:  # noqa: BLE001 — a non-interactive node is itself the answer
            pass
        self.page.keyboard.type(text)
        self.page.keyboard.press("Delete")

    # ---- Contact form fields ----------------------------------------------
    def _cf_field(self, name: str) -> str:
        return f"{self.CF_ROOT} [data-qc-f='{name}']"

    def _cf_error(self, name: str) -> str:
        return f"{self.CF_ROOT} [data-qc-e='{name}']"

    def set_contact_field(self, name: str, value: str) -> "B2bMatchmakingPage":
        self.type(self._cf_field(name), value)
        return self

    def select_contact_option(self, name: str, value: str) -> "B2bMatchmakingPage":
        self.select_option(self._cf_field(name), value=value)
        return self

    def contact_field_value(self, name: str) -> str:
        return self.page.locator(self._cf_field(name)).first.input_value()

    def contact_field_label(self, name: str) -> str:
        return self.page.locator(f"{self.CF_ROOT} [data-qc-l='{name}']").first.inner_text().strip()

    def contact_field_error(self, name: str) -> str:
        """The inline validation message a visitor sees under a field, or ''
        when none is shown. Reads the rendered state (`hidden` attribute),
        not merely the element's presence."""
        loc = self.page.locator(self._cf_error(name)).first
        if loc.count() == 0:
            return ""
        return loc.evaluate(
            "el => el.hidden ? '' : (el.textContent || '').trim()"
        )

    def contact_visible_errors(self) -> dict:
        return self.page.locator(f"{self.CF_ROOT} [data-qc-e]").evaluate_all(
            "els => Object.fromEntries(els.filter(e => !e.hidden)"
            ".map(e => [e.getAttribute('data-qc-e'), (e.textContent||'').trim()]))"
        )

    def contact_method_value(self) -> str:
        return self.contact_field_value("preferredMethodOfContact")

    def contact_method_options(self) -> list:
        return self._option_labels(self._cf_field("preferredMethodOfContact"))

    def contact_method_selected_label(self) -> str:
        return self._selected_label(self._cf_field("preferredMethodOfContact"))

    def visible_contact_branch_field_count(self, branch_locator: str) -> int:
        """How many of one conditional branch's `.qc-field` blocks are
        actually rendered.

        `data-qc-b2bcf-branch` is NOT a single wrapper: each value marks TWO
        sibling `.qc-field` divs directly under `div.qc-b2bcf__grid` —
        email = {Email, Confirm Email}, phone = {Phone, Best Time to Call}
        (measured live 2026-09-17, qcdev). Passing either constant to
        `is_visible()` therefore resolved 2 elements, Playwright raised a
        strict-mode violation, and `BasePage.is_visible()` (which never
        throws, by contract) swallowed it into a permanent `False` — the two
        branch predicates below were structurally incapable of returning
        True, so `is True` assertions red-failed a working product and
        `is False` assertions passed without testing anything.

        Counting RENDERED matches answers the real question instead. The
        inactive branch's fields carry the `hidden` attribute and
        `display: none`, so `!e.hidden && e.offsetParent !== null` is the
        same rendered-state test `contact_branch_field_labels()` already
        uses."""
        return self.page.locator(branch_locator).evaluate_all(
            "els => els.filter(e => !e.hidden && e.offsetParent !== null).length"
        )

    def is_contact_email_branch_visible(self) -> bool:
        return self.visible_contact_branch_field_count(self.CF_EMAIL_BRANCH) > 0

    def is_contact_phone_branch_visible(self) -> bool:
        return self.visible_contact_branch_field_count(self.CF_PHONE_BRANCH) > 0

    def contact_branch_field_labels(self) -> list:
        """Labels of the conditional block's currently VISIBLE fields."""
        return self.page.locator(
            f"{self.CF_EMAIL_BRANCH}, {self.CF_PHONE_BRANCH}"
        ).evaluate_all(
            "els => els.filter(e => !e.hidden && e.offsetParent !== null)"
            ".map(e => e.querySelector('.qc-field__label').textContent.trim())"
        )

    def fill_contact_fields(self, values: dict, skip: tuple = ()) -> "B2bMatchmakingPage":
        """Writes `values` ({field name: value}) into the Contact form,
        leaving every name in `skip` untouched/blank. Selects are detected
        from the live control type, so one call handles both."""
        for name, value in values.items():
            if name in skip:
                self.clear_contact_field(name)
                continue
            if self._is_select(self._cf_field(name)):
                self.select_option(self._cf_field(name), value=value)
            else:
                self.type(self._cf_field(name), value)
        return self

    def clear_contact_field(self, name: str) -> "B2bMatchmakingPage":
        locator = self._cf_field(name)
        if self._is_select(locator):
            self.select_option(locator, value="")
        else:
            self.type(locator, "")
        return self

    def _is_select(self, locator: str) -> bool:
        return self.page.locator(locator).first.evaluate(
            "el => el.tagName.toLowerCase() === 'select'"
        )

    def submit_contact_form(self) -> "B2bMatchmakingPage":
        """Clicks Send Request and waits for the form to ACTUALLY respond —
        an inline error appearing, the status banner opening, or the success
        panel replacing the form. No sleep, no load-state wait, and no
        assumption about which outcome is correct."""
        self.click(self.CF_SUBMIT)
        self.page.wait_for_function(
            "() => {"
            " const root = document.querySelector('[data-qc-b2bcf-root]');"
            " if (!root) return false;"
            " const err = Array.from(root.querySelectorAll('[data-qc-e]')).some(e => !e.hidden);"
            " const status = root.querySelector('[data-qc-b2bcf-status]');"
            " const done = root.querySelector('[data-qc-b2bcf-done]');"
            " return err || (status && !status.hidden) || (done && !done.hidden); }",
            timeout=30000,
        )
        return self

    def contact_status_text(self) -> str:
        loc = self.page.locator(self.CF_STATUS).first
        return loc.evaluate("el => el.hidden ? '' : (el.textContent||'').trim()")

    def is_contact_success_shown(self) -> bool:
        return self.page.locator(self.CF_DONE).first.evaluate("el => !el.hidden")

    def cancel_contact_form(self) -> "B2bMatchmakingPage":
        self.click(self.CF_CANCEL)
        self.page.locator(self.CF_DIALOG).wait_for(state="hidden", timeout=15000)
        return self

    # ==================== reCAPTCHA (reported, never solved) =============
    def captcha_field_state(self, form: str = "contact") -> dict:
        """What the CAPTCHA field actually renders on the named form.

        Returns `{present, visible, label, widget_rendered}`. `present` is DOM
        presence, `visible` is what a visitor can reach and operate. Nothing
        here solves, stubs or bypasses the CAPTCHA — it only reports."""
        root = self.CF_CAPTCHA_FIELD if form == "contact" else self.REG_CAPTCHA_FIELD
        loc = self.page.locator(root).first
        if loc.count() == 0:
            return {"present": False, "visible": False, "label": "", "widget_rendered": False}
        return loc.evaluate(
            "el => ({present: true,"
            " visible: !el.hidden && el.offsetParent !== null,"
            " label: (el.querySelector('.qc-field__label')||{textContent:''}).textContent.trim(),"
            " widget_rendered: !!el.querySelector('[data-qc-recaptcha'+ ']') "
            "   && el.querySelector('[data-qc-recaptcha]').childElementCount > 0})"
        )

    def is_recaptcha_script_loaded(self) -> bool:
        return self.page.evaluate(
            "() => !!document.querySelector('#qc-recaptcha-enterprise-js')"
        )

    # ==================== B2B Registration form ==========================
    def is_registration_form_present(self) -> bool:
        return self.page.locator(self.REG_FORM).count() > 0

    def is_registration_form_visible(self) -> bool:
        return self.is_visible(self.REG_FORM)

    def registration_title(self) -> str:
        return self.text(self.REG_TITLE).strip()

    def registration_section_titles(self) -> list:
        return [t.strip() for t in self.page.locator(self.REG_LEGENDS).all_inner_texts()]

    def registration_section_count(self) -> int:
        return self.page.locator(self.REG_FIELDSETS).count()

    def registration_field_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.REG_LABELS).all_inner_texts()]

    def registration_field_names(self) -> list:
        return self.page.locator(f"{self.REG_ROOT} [data-qc-f]").evaluate_all(
            "els => els.map(e => e.getAttribute('data-qc-f'))"
        )

    def registration_mandatory_labels(self) -> list:
        """Labels the product actually MARKS as mandatory — i.e. the visible
        '*' a visitor sees, not an `aria-required` attribute they don't."""
        return self.page.locator(self.REG_LABELS).evaluate_all(
            "els => els.map(e => e.textContent.trim()).filter(t => t.endsWith('*'))"
        )

    def _reg_field(self, name: str) -> str:
        return f"{self.REG_ROOT} [data-qc-f='{name}']"

    def _reg_error(self, name: str) -> str:
        return f"{self.REG_ROOT} [data-qc-e='{name}']"

    def set_registration_field(self, name: str, value: str) -> "B2bMatchmakingPage":
        locator = self._reg_field(name)
        if self._is_select(locator):
            self.select_option(locator, value=value)
        else:
            self.type(locator, value)
        return self

    def check_registration_consent(self) -> "B2bMatchmakingPage":
        self.set_checkbox(self._reg_field("privacyPolicyConsent"), True)
        return self

    def fill_registration_fields(self, values: dict, skip: tuple = ()) -> "B2bMatchmakingPage":
        for name, value in values.items():
            if name in skip:
                locator = self._reg_field(name)
                if self._is_select(locator):
                    self.select_option(locator, value="")
                else:
                    self.type(locator, "")
                continue
            self.set_registration_field(name, value)
        return self

    def registration_field_value(self, name: str) -> str:
        return self.page.locator(self._reg_field(name)).first.input_value()

    def registration_field_error(self, name: str) -> str:
        loc = self.page.locator(self._reg_error(name)).first
        if loc.count() == 0:
            return ""
        return loc.evaluate("el => el.hidden ? '' : (el.textContent || '').trim()")

    def registration_visible_errors(self) -> dict:
        return self.page.locator(f"{self.REG_ROOT} [data-qc-e]").evaluate_all(
            "els => Object.fromEntries(els.filter(e => !e.hidden)"
            ".map(e => [e.getAttribute('data-qc-e'), (e.textContent||'').trim()]))"
        )

    def submit_registration_form(self) -> "B2bMatchmakingPage":
        self.click(self.REG_SUBMIT)
        self.page.wait_for_function(
            "() => {"
            " const root = document.querySelector('[data-qc-b2breg-root]');"
            " if (!root) return false;"
            " const err = Array.from(root.querySelectorAll('[data-qc-e]')).some(e => !e.hidden);"
            " const status = root.querySelector('[data-qc-b2breg-status]');"
            " const done = root.querySelector('[data-qc-b2breg-done]');"
            " return err || (status && !status.hidden) || (done && !done.hidden); }",
            timeout=30000,
        )
        return self

    def registration_status_text(self) -> str:
        loc = self.page.locator(self.REG_STATUS).first
        return loc.evaluate("el => el.hidden ? '' : (el.textContent||'').trim()")

    def is_registration_success_shown(self) -> bool:
        return self.page.locator(self.REG_DONE).first.evaluate("el => !el.hidden")

    # ==================== Scroll =========================================
    def scroll_to(self, y: int) -> "B2bMatchmakingPage":
        self.page.evaluate("y => window.scrollTo(0, y)", y)
        self.page.wait_for_function("y => Math.abs(window.scrollY - y) < 2", arg=y, timeout=10000)
        return self

    def scroll_offset(self) -> int:
        return self.page.evaluate("() => Math.round(window.scrollY)")

    def scroll_to_element(self, locator: str) -> "B2bMatchmakingPage":
        self.page.locator(locator).first.scroll_into_view_if_needed()
        return self

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

    def viewport_size(self) -> dict:
        return self.page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})")

    def distinct_rows(self, locator: str, tolerance: int = 4) -> int:
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

    def grid_column_count(self) -> int:
        """Columns the card grid is actually laid out in — read from the
        resolved `grid-template-columns` track list, which is the layout
        contract itself rather than an inference from however many cards the
        data happens to provide."""
        tracks = self.computed_style(self.GRID, ["gridTemplateColumns"])["gridTemplateColumns"]
        return len([t for t in tracks.split() if t and t != "none"])

    def cards_per_row(self) -> int:
        return self.distinct_columns(self.CARD)

    def card_row_count(self) -> int:
        return self.distinct_rows(self.CARD)

    def search_field_row_count(self) -> int:
        return self.distinct_rows(self.SEARCH_FIELDS)

    def search_field_column_count(self) -> int:
        return self.distinct_columns(self.SEARCH_FIELDS)

    def search_row_geometry(self) -> dict:
        """The three field boxes AND the Reset/Search actions group measured
        in ONE round-trip, so a layout shift between two separate measurement
        calls cannot skew a comparison of the pair."""
        return self.page.evaluate(
            "([fieldSel, actionSel]) => {"
            " const rect = e => { const r = e.getBoundingClientRect();"
            "   return {x: r.x, y: r.y, width: r.width, height: r.height}; };"
            " const fields = Array.from(document.querySelectorAll(fieldSel)).map(rect);"
            " const a = document.querySelector(actionSel);"
            " return {fields: fields, actions: a ? rect(a) : null}; }",
            [self.SEARCH_FIELDS, self.SEARCH_ACTIONS],
        )

    def hero_geometry(self) -> dict:
        """Hero copy column, art column and the banner image itself, measured
        together."""
        return self.page.evaluate(
            "([copySel, artSel, imgSel]) => {"
            " const rect = s => { const e = document.querySelector(s); if (!e) return null;"
            "   const r = e.getBoundingClientRect();"
            "   return {x: r.x, y: r.y, width: r.width, height: r.height}; };"
            " return {copy: rect(copySel), art: rect(artSel), image: rect(imgSel)}; }",
            [self.HERO_COPY, self.HERO_ART, self.HERO_IMAGE],
        )

    def hero_image_size(self) -> dict:
        b = self.box(self.HERO_IMAGE)
        if not b:
            return None
        return {"width": round(b["width"]), "height": round(b["height"])}

    def card_geometry(self, index: int = 0) -> dict:
        """One card's own box plus its logo / name / country / flag / badge —
        used by the RTL mirroring and the no-overflow assertions."""
        return self.page.locator(self.CARD).nth(index).evaluate(
            "el => { const rect = n => { if (!n) return null; const r = n.getBoundingClientRect();"
            "   return {x: r.x, y: r.y, width: r.width, height: r.height}; };"
            " return {card: rect(el), logo: rect(el.querySelector('.qc-b2b-logo')),"
            "  head: rect(el.querySelector('.qc-b2b-card-head')),"
            "  name: rect(el.querySelector('.qc-b2b-card-name')),"
            "  country: rect(el.querySelector('.qc-b2b-country')),"
            "  flag: rect(el.querySelector('.qc-b2b-flag')),"
            "  metaEnd: rect(el.querySelector('.qc-b2b-meta-end')),"
            "  badge: rect(el.querySelector('.qc-b2b-badge'))}; }"
        )

    def card_parts_within_card(self, index: int = 0) -> bool:
        """True when every rendered part of a card sits inside the card's own
        box (2px tolerance) — nothing overflows its container."""
        g = self.card_geometry(index)
        card = g["card"]
        if not card:
            return False
        for key in ("logo", "head", "name", "country", "flag", "metaEnd", "badge"):
            part = g[key]
            if not part or part["width"] <= 0 or part["height"] <= 0:
                return False
            if part["x"] < card["x"] - 2 or part["x"] + part["width"] > card["x"] + card["width"] + 2:
                return False
            if part["y"] < card["y"] - 2 or part["y"] + part["height"] > card["y"] + card["height"] + 2:
                return False
        return True

    def details_dialog_geometry(self) -> dict:
        """The popup's dialog box, its scrolling body, and the viewport — one
        round-trip, so 'fits the viewport' and 'content scrollable' are read
        off the same frame."""
        return self.page.evaluate(
            "([dialogSel, bodySel]) => {"
            " const rect = s => { const e = document.querySelector(s); if (!e) return null;"
            "   const r = e.getBoundingClientRect();"
            "   return {x: r.x, y: r.y, width: r.width, height: r.height}; };"
            " const body = document.querySelector(bodySel);"
            " return {dialog: rect(dialogSel), body: rect(bodySel),"
            "  scrollHeight: body ? body.scrollHeight : 0,"
            "  clientHeight: body ? body.clientHeight : 0,"
            "  overflowY: body ? getComputedStyle(body).overflowY : '',"
            "  viewport: {width: window.innerWidth, height: window.innerHeight}}; }",
            [self.DETAILS_DIALOG, self.DETAILS_BODY],
        )

    def contact_dialog_geometry(self) -> dict:
        return self.page.evaluate(
            "([dialogSel, scrollSel]) => {"
            " const rect = s => { const e = document.querySelector(s); if (!e) return null;"
            "   const r = e.getBoundingClientRect();"
            "   return {x: r.x, y: r.y, width: r.width, height: r.height}; };"
            " const sc = document.querySelector(scrollSel);"
            " return {dialog: rect(dialogSel), scroll: rect(scrollSel),"
            "  scrollHeight: sc ? sc.scrollHeight : 0,"
            "  clientHeight: sc ? sc.clientHeight : 0,"
            "  overflowY: sc ? getComputedStyle(sc).overflowY : '',"
            "  viewport: {width: window.innerWidth, height: window.innerHeight}}; }",
            [self.CF_DIALOG, self.CF_SCROLL],
        )

    def details_field_column_count(self) -> int:
        return self.distinct_columns(self.DETAILS_FIELDS)

    def registration_field_row_count(self) -> int:
        return self.distinct_rows(self.REG_FIELDS)

    def registration_field_column_count(self) -> int:
        return self.distinct_columns(self.REG_FIELDS)

    def registration_truncated_fields(self) -> list:
        """Every RENDERED registration field whose control is clipped by its
        own `.qc-field` wrapper or by the viewport (2px tolerance), as
        `{label, reason, width}` — empty when the form is well-formed.

        Fields the form deliberately does not render (`hidden` attribute /
        no offset parent) are SKIPPED, not failed: their rect is zero
        BECAUSE they are not displayed, which is not truncation. Measured
        live 2026-09-17 (qcdev): field 20 of 21 is
        `<div class="qc-field" data-qc-recaptcha-field hidden>` ("Security
        Check *"), and the previous `fr.width <= 0 -> false` line counted
        exactly that hidden field as clipped, failing a form whose 20
        rendered fields all measured well-formed inside a 768px viewport."""
        return self.page.evaluate(
            "sel => { const vw = document.documentElement.clientWidth;"
            " const label = f => { const l = f.querySelector('.qc-field__label');"
            "   return l ? l.textContent.trim() : (f.getAttribute('class') || 'qc-field'); };"
            " const out = [];"
            " Array.from(document.querySelectorAll(sel)).forEach(f => {"
            "  if (f.hidden || f.offsetParent === null) return;"  # not rendered -> not truncated
            "  const fr = f.getBoundingClientRect();"
            "  const w = Math.round(fr.width);"
            "  if (fr.width <= 0) { out.push({label: label(f), reason: 'zero-width wrapper', width: w}); return; }"
            "  if (fr.left < -2 || fr.right > vw + 2)"
            "   { out.push({label: label(f), reason: 'wrapper outside the viewport', width: w}); return; }"
            "  const c = f.querySelector('input, textarea, select');"
            "  if (!c) return;"
            "  const cr = c.getBoundingClientRect();"
            "  if (!(cr.width > 0 && cr.left >= fr.left - 2 && cr.right <= fr.right + 2))"
            "   { out.push({label: label(f), reason: 'control clipped by its wrapper',"
            "     width: Math.round(cr.width)}); }"
            " });"
            " return out; }",
            self.REG_FIELDS,
        )

    def registration_fields_are_untruncated(self) -> bool:
        """True when no RENDERED registration field's control is clipped by
        its own container or by the viewport — see
        `registration_truncated_fields()` for what is measured and why
        non-rendered fields are skipped."""
        return not self.registration_truncated_fields()

    def is_operable_by_touch(self, locator: str, min_tap_px: int = 24) -> bool:
        """True when a control can be reached and used by a finger: it scrolls
        into view, is visible and enabled, is not covered by another element
        at its own centre point, and offers a tap target of at least
        `min_tap_px` in both dimensions."""
        target = self.page.locator(locator).first
        if target.count() == 0:
            return False
        try:
            target.scroll_into_view_if_needed(timeout=10000)
        except Exception:  # noqa: BLE001 — unreachable is itself the answer
            return False
        return target.evaluate(
            "(el, minPx) => { const r = el.getBoundingClientRect();"
            " if (r.width < minPx || r.height < minPx) return false;"
            " if (el.disabled) return false;"
            " const cx = r.left + r.width / 2, cy = r.top + r.height / 2;"
            " if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) return false;"
            " const top = document.elementFromPoint(cx, cy);"
            " return !!top && (el === top || el.contains(top) || top.contains(el)); }",
            min_tap_px,
        )

    def are_contact_fields_operable_by_touch(self) -> dict:
        """`{field name: operable}` for every mandatory Contact-form control
        plus the conditional block's visible fields and the Submit button."""
        names = list(self.CONTACT_REQUIRED_TEXT_FIELDS) + list(self.CONTACT_REQUIRED_SELECTS) + [
            "preferredMethodOfContact"
        ]
        result = {name: self.is_operable_by_touch(self._cf_field(name)) for name in names}
        result["conditional_block"] = self.is_operable_by_touch(
            f"{self.CF_EMAIL_BRANCH} .qc-field__input"
        )
        result["submit"] = self.is_operable_by_touch(self.CF_SUBMIT)
        return result

    def is_contact_submit_operable_by_touch(self) -> bool:
        return self.is_operable_by_touch(self.CF_SUBMIT)

    # ---- Named boxes (so tests never hold a selector) ----------------------
    def hero_box(self) -> dict:
        return self.box(self.HERO)

    def hero_eyebrow_box(self) -> dict:
        return self.box(self.HERO_EYEBROW)

    def hero_title_box(self) -> dict:
        return self.box(self.HERO_TITLE)

    def hero_copy_box(self) -> dict:
        return self.box(self.HERO_COPY)

    def hero_art_box(self) -> dict:
        return self.box(self.HERO_ART)

    def hero_lede_box(self) -> dict:
        return self.box(self.HERO_LEDE)

    def search_form_box(self) -> dict:
        return self.box(self.SEARCH_FORM)

    def search_actions_box(self) -> dict:
        return self.box(self.SEARCH_ACTIONS)

    def search_button_box(self) -> dict:
        return self.box(self.SEARCH_BUTTON)

    def search_field_boxes(self) -> list:
        return self.boxes(self.SEARCH_FIELDS)

    def grid_box(self) -> dict:
        return self.box(self.GRID)

    def card_box(self, index: int = 0) -> dict:
        boxes = self.boxes(self.CARD)
        return boxes[index] if index < len(boxes) else None

    def load_more_box(self) -> dict:
        return self.box(self.LOAD_MORE)

    # ---- Named computed styles (so tests never hold a selector) ------------
    _SURFACE_PROPS = ["backgroundColor", "color"]

    def page_background_style(self) -> dict:
        return self.computed_style("body", self._SURFACE_PROPS)

    def site_header_style(self) -> dict:
        return self.computed_style(self.header.HEADER, self._SURFACE_PROPS)

    def hero_style(self) -> dict:
        return self.computed_style(self.HERO, self._SURFACE_PROPS)

    def search_form_style(self) -> dict:
        return self.computed_style(
            self.SEARCH_FORM,
            ["backgroundColor", "color", "borderColor", "borderWidth", "borderStyle",
             "borderRadius"],
        )

    def search_label_style(self) -> dict:
        return self.computed_style(self.SEARCH_FIELD_LABELS, self._SURFACE_PROPS)

    def name_input_style(self) -> dict:
        return self.computed_style(
            self.NAME_INPUT, ["backgroundColor", "color", "borderColor"]
        )

    def search_button_style(self) -> dict:
        return self.computed_style(self.SEARCH_BUTTON, self._SURFACE_PROPS)

    def card_style(self) -> dict:
        return self.computed_style(
            self.CARD,
            ["backgroundColor", "color", "borderColor", "borderWidth", "borderStyle",
             "borderRadius"],
        )

    def card_name_style(self) -> dict:
        return self.computed_style(f"{self.CARD} {self.CARD_NAME}", self._SURFACE_PROPS)

    def card_industry_style(self) -> dict:
        return self.computed_style(f"{self.CARD} {self.CARD_INDUSTRY}", self._SURFACE_PROPS)

    def card_country_style(self) -> dict:
        return self.computed_style(f"{self.CARD} {self.CARD_COUNTRY}", self._SURFACE_PROPS)

    def badge_style(self) -> dict:
        return self.computed_style(f"{self.CARD} {self.CARD_BADGE}", self._SURFACE_PROPS)

    def status_style(self) -> dict:
        return self.computed_style(self.STATUS, self._SURFACE_PROPS)

    def search_form_direction(self) -> str:
        return self.computed_style(self.SEARCH_FORM, ["direction"])["direction"]

    def text_alignment(self, which: str) -> dict:
        """`{direction, textAlign}` for a named piece of copy, so an RTL/LTR
        alignment assertion never holds a selector."""
        mapping = {
            "hero_title": self.HERO_TITLE,
            "hero_lede": self.HERO_LEDE,
            "search_label": self.SEARCH_FIELD_LABELS,
            "card_name": f"{self.CARD} {self.CARD_NAME}",
            "card_industry": f"{self.CARD} {self.CARD_INDUSTRY}",
            "status": self.STATUS,
        }
        return self.computed_style(mapping[which], ["direction", "textAlign"])

    def details_region_styles(self) -> dict:
        """Computed surface styles for every readable region of the popup,
        keyed by a human name."""
        return {
            "dialog": self.computed_style(self.DETAILS_DIALOG, self._SURFACE_PROPS),
            "name": self.computed_style(self.DETAILS_NAME, self._SURFACE_PROPS),
            "industry": self.computed_style(self.DETAILS_INDUSTRY, self._SURFACE_PROPS),
            "badge": self.computed_style(self.DETAILS_BADGE, self._SURFACE_PROPS),
            "field_term": self.computed_style(self.DETAILS_FIELD_TERMS, self._SURFACE_PROPS),
            "field_value": self.computed_style(self.DETAILS_FIELD_VALUES, self._SURFACE_PROPS),
            "section_heading": self.computed_style(self.DETAILS_SECTION_HEADS, self._SURFACE_PROPS),
            "section_body": self.computed_style(self.DETAILS_SECTION_BODIES, self._SURFACE_PROPS),
            "close": self.computed_style(self.DETAILS_CLOSE_BUTTON, self._SURFACE_PROPS),
            "contact": self.computed_style(self.DETAILS_CONTACT_BUTTON, self._SURFACE_PROPS),
        }

    def contact_form_region_styles(self) -> dict:
        return {
            "dialog": self.computed_style(self.CF_DIALOG, self._SURFACE_PROPS),
            "title": self.computed_style(self.CF_TITLE, self._SURFACE_PROPS),
            "legend": self.computed_style(self.CF_LEGENDS, self._SURFACE_PROPS),
            "label": self.computed_style(self.CF_LABELS, self._SURFACE_PROPS),
            "input": self.computed_style(
                f"{self.CF_ROOT} .qc-field__input", ["backgroundColor", "color", "borderColor"]
            ),
            "company_panel": self.computed_style(self.CF_COMPANY_PANEL, self._SURFACE_PROPS),
            "conditional_label": self.computed_style(
                f"{self.CF_EMAIL_BRANCH} .qc-field__label", self._SURFACE_PROPS
            ),
            "conditional_input": self.computed_style(
                f"{self.CF_EMAIL_BRANCH} .qc-field__input",
                ["backgroundColor", "color", "borderColor"],
            ),
            "submit": self.computed_style(self.CF_SUBMIT, self._SURFACE_PROPS),
            "cancel": self.computed_style(self.CF_CANCEL, self._SURFACE_PROPS),
        }

    def is_desktop_nav_visible(self) -> bool:
        return self.header.is_desktop_nav_visible()

    def is_mobile_hamburger_visible(self) -> bool:
        return self.header.is_mobile_hamburger_visible()

    # ==================== Dark mode (composed a11y panel) =================
    def enable_dark_mode(self) -> "B2bMatchmakingPage":
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

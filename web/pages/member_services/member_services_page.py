"""web/pages/member_services/member_services_page.py — MemberServicesPage.

Page Object for the public **Member's Services** page
(PBI 129400 / "QC-SVC-001 — Member's Services", SVC service, Web platform):

    EN  https://qcdev.ihorizons.com/web/qatar-chamber/our-services/member-services
    AR  https://qcdev.ihorizons.com/ar/web/qatar-chamber/our-services/member-services

`/web/qatar-chamber/member-services` 302-redirects to the `/our-services/…`
path above (confirmed live, read-only, 2026-09-27), so both spellings reach
the same page; `PAGE_PATH_MARKER` below is what a URL assertion should use.

TOOLING DISCLOSURE
------------------
Every locator, copy string, colour and measurement written into this file was
harvested from the **shell** — `tools/extract_locators.py` plus targeted
Playwright probe scripts run with `python`, at the framework's default
1920x1080 viewport (and at 768x1024 / 375x812 for the responsive readers).
**The Playwright MCP was reachable this session and was NOT used at all.**
Nothing in this batch created, edited, published, unpublished, reordered or
deleted any content on qcdev — the whole batch is strictly read-only.

THE FRAGMENT IS A MASTER-DETAIL SPA, NOT TWO PAGES
--------------------------------------------------
`section.qc-member-services` renders BOTH views into the same document and
toggles their `hidden` attribute:

* `[data-qc-ms-listview]` — the landing/card view (visible on first load)
* `[data-qc-ms-detailview]` — the sidebar + content panel view

Selecting a service sets `location.hash` to that service's key
(`#new-membership`), swaps the two `hidden` flags and RE-RENDERS
`[data-qc-ms-panel]`'s innerHTML client-side. There is **no document
navigation** — `performance.getEntriesByType('navigation').length` stays at 1
and a value stashed on `window` survives the switch (that is exactly what
`navigation_fingerprint()` below reads for #137616's "no full page reload").
A deep link straight to `…/member-services#membership-renewal` opens the
detail view on that service, confirmed live.

The four live service keys, in Display Order, are in `SERVICE_KEYS`.

NO ASSERTIONS LIVE HERE
-----------------------
This object observes and drives only; every assertion is in
`web/tests/member_services/test_member_services_web.py`, per
automation-standards.md. Readers deliberately return an honest `0` / `{}` /
`None` for controls this build does not render (the pattern
`web/pages/faq/faq_page.py` established), so a test asserting on a missing
control fails on its own presence assertion instead of dying in a 30s
locator timeout.
"""

import allure

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import (
    AccessibilityToolsComponent,
)
from web.pages.components.header_component import HeaderComponent

# ── Routes ───────────────────────────────────────────────────────────────
MEMBER_SERVICES_PATH = "/web/qatar-chamber/our-services/member-services"
OUR_SERVICES_PATH = "/web/qatar-chamber/our-services"
HOME_PATH = "/web/qatar-chamber"
# The one stable substring of the page URL across EN, AR and both the
# `/our-services/…` and the short `/member-services` spellings. The site
# normalises the path after a language switch (AR detail URL is
# `/ar/web/qatar-chamber/member-services#…`, and switching AR->EN lands on
# `/our-services/member-services` with NO `/web/qatar-chamber` prefix), so a
# strict full-URL wait would flake — always wait on this marker.
PAGE_PATH_MARKER = "member-services"
HOME_PATH_MARKER = "/web/qatar-chamber"
OUR_SERVICES_PATH_MARKER = "/our-services"

# ── Viewports the compatibility cases name, in their own wording ─────────
# Case data, not a shared breakpoint table (#137647 / #137648 / #137649).
DESKTOP_VIEWPORT = (1920, 1080)
TABLET_VIEWPORT = (768, 1024)
MOBILE_VIEWPORT = (375, 812)

# ── The four live services, in their configured Display Order ────────────
SERVICE_KEYS = (
    "new-membership",
    "membership-renewal",
    "attestation-on-signature",
    "signatory-cancellation",
)
SERVICE_NAMES_EN = (
    "New Membership",
    "Membership Renewal",
    "Attestation on Signature",
    "Signatory Cancellation",
)


class MemberServicesPage(BasePage):
    """Query + drive surface for the public Member's Services page."""

    # ── Fragment root ───────────────────────────────────────────────────
    SECTION = "section.qc-member-services"

    # ── Hero band ───────────────────────────────────────────────────────
    HERO = "[data-qc-ms-hero]"
    HERO_BACKGROUND = "[data-qc-ms-hero-bg]"
    HERO_OVERLAY = f"{SECTION} .qc-ms-hero-overlay"
    HERO_INNER = f"{SECTION} .qc-ms-hero-inner"
    PAGE_TITLE = "[data-qc-ms-page-title]"

    # ── Breadcrumb ──────────────────────────────────────────────────────
    BREADCRUMB = "[data-qc-ms-breadcrumb]"
    BREADCRUMB_HOME_LINK = "[data-qc-ms-home-link]"
    BREADCRUMB_HOME_LABEL = "[data-qc-ms-home-label]"
    BREADCRUMB_HOME_ICON = f"{SECTION} svg.qc-ms-home-ico"
    BREADCRUMB_SEPARATOR = f"{SECTION} svg.qc-ms-crumb-sep"
    BREADCRUMB_CURRENT = "[data-qc-ms-crumb-current]"
    BREADCRUMB_CRUMBS = f"{SECTION} .qc-ms-breadcrumb .qc-ms-crumb"
    # The case (#137621) calls the second crumb a LINK. This build renders it
    # as a plain <span> with no href, so this union selector resolves to 0
    # matches rather than raising — see `breadcrumb_current_is_link()`.
    BREADCRUMB_CURRENT_AS_LINK = f"{SECTION} a.qc-ms-crumb-current, {SECTION} a[data-qc-ms-crumb-current]"

    # ── Shared heading + intro row ──────────────────────────────────────
    CONTENT = f"{SECTION} .qc-ms-content"
    HEADROW = f"{SECTION} .qc-ms-headrow"
    SECTION_HEADING = "[data-qc-ms-heading]"
    INTRO = "[data-qc-ms-intro]"

    # ── List (landing) view ─────────────────────────────────────────────
    LIST_VIEW = "[data-qc-ms-listview]"
    CARDS = "[data-qc-ms-cards]"
    CARD = f"{SECTION} a.qc-ms-card"
    CARD_ICON_TILE = f"{SECTION} .qc-ms-card-ico"
    CARD_NAME = f"{SECTION} .qc-ms-card-name"
    CARD_DESCRIPTION = f"{SECTION} .qc-ms-card-desc"
    CARD_DETAILS_BUTTON = f"{SECTION} .qc-ms-card-cta"
    CARD_DETAILS_LABEL = f"{SECTION} .qc-ms-card-cta > span"
    CARD_DETAILS_ICON = f"{SECTION} .qc-ms-card-cta svg"
    LIST_SUPPORT = "[data-qc-ms-list-support]"
    LIST_SUPPORT_IMAGE = "[data-qc-ms-list-support-img]"

    # ── Detail (master-detail) view ─────────────────────────────────────
    DETAIL_VIEW = "[data-qc-ms-detailview]"
    DETAIL_CONTAINER = f"{SECTION} .qc-ms-detail"
    SIDEBAR = "[data-qc-ms-sidebar]"
    SIDEBAR_TITLE = "[data-qc-ms-all-services]"
    SIDEBAR_LIST = "[data-qc-ms-side-list]"
    SIDEBAR_ITEM = f"{SECTION} a.qc-ms-side-item"
    SIDEBAR_ITEM_SELECTED = f"{SECTION} a.qc-ms-side-item.is-active"
    SIDEBAR_ITEM_UNSELECTED = f"{SECTION} a.qc-ms-side-item:not(.is-active)"
    SIDEBAR_LABEL = f"{SECTION} .qc-ms-side-label"
    SIDEBAR_ICON_TILE = f"{SECTION} .qc-ms-side-ico"
    SIDEBAR_CHEVRON = f"{SECTION} .qc-ms-side-chev"
    SIDEBAR_CHEVRON_ICON = f"{SECTION} .qc-ms-side-chev svg"
    VERTICAL_DIVIDER = f"{SECTION} .qc-ms-vdiv"

    PANEL = "[data-qc-ms-panel]"
    PANEL_TILE = f"{SECTION} .qc-ms-panel-tile"
    PANEL_TITLE = f"{SECTION} .qc-ms-panel-title"
    PANEL_INTRO = f"{SECTION} .qc-ms-panel-intro"
    PANEL_DIVIDER = f"{SECTION} .qc-ms-panel-divider"
    SUBHEADING = f"{SECTION} .qc-ms-subheading"
    RICHTEXT = f"{SECTION} .qc-ms-richtext"
    REQUIRED_DOCS_BLOCK = f"{SECTION} .qc-ms-reqdocs"
    REQUIRED_DOCS_LIST = f"{SECTION} .qc-ms-reqdocs ul"
    REQUIRED_DOCS_ITEM = f"{SECTION} .qc-ms-reqdocs li"
    CTA = f"{SECTION} a.qc-ms-cta"
    CTA_LABEL = f"{SECTION} a.qc-ms-cta > span"
    CTA_ICON = f"{SECTION} a.qc-ms-cta svg"
    DETAIL_SUPPORT = "[data-qc-ms-detail-support]"
    DETAIL_SUPPORT_IMAGE = "[data-qc-ms-detail-support-img]"

    STATUS_LINE = "[data-qc-ms-status]"

    # ── Header surfaces the theme cases name ────────────────────────────
    # Composed from HeaderComponent's own constants wherever one exists, so
    # nothing is duplicated. The profile-icon button #137651 names has NO
    # element on this build — the union below resolves to 0 matches, which
    # is what `profile_icon_button_count()` reports honestly.
    HEADER = HeaderComponent.HEADER
    HEADER_NAV_LINK = f"{HEADER} a.qc-nav-link"
    HEADER_LANGUAGE_CHIP = f"{HEADER} a.qc-lang-switcher"
    PROFILE_ICON_BUTTON = (
        f"{HEADER} a.qc-profile, {HEADER} button.qc-profile, "
        f"{HEADER} [data-qc-profile], {HEADER} .qc-profile-btn"
    )

    # ── Main-menu "Our Services" dropdown (#137614) ─────────────────────
    # Composed from HeaderComponent's own constants — the site header is a
    # shared component object and its locators are never re-declared here.
    NAV_ITEM_WITH_SUBMENU = HeaderComponent.NAV_ITEM_WITH_SUBMENU
    NAV_SUBMENU_PANEL = HeaderComponent.NAV_ITEM_SUBMENU_PANEL
    NAV_SUBMENU_LINK = f"{HeaderComponent.NAV_ITEM_SUBMENU_PANEL} a"

    # ── Copy the CASES name, asserted verbatim by the tests ─────────────
    # These are the CASES' expectations, not necessarily this build's copy
    # (several differ — see the test module's docstring table).
    # DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137662, ADO-137614):
    # case expected 'Membership Services'; delivered build renders
    # "Member's Services". Updated to the build.
    CASE_PAGE_TITLE_EN = "Member's Services"
    CASE_PAGE_TITLE_AR = "خدمات العضوية"
    # DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137614):
    # case expected 'Membership Services' as the 'Our Services' dropdown
    # entry; delivered build renders "Member's Services". Updated to the build.
    CASE_MENU_ITEM_LABEL = "Member's Services"
    CASE_SIDEBAR_TITLE_EN = "All Services"
    # DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137620, ADO-137643):
    # case expected 'كافة الخدمات'; delivered build renders 'جميع الخدمات'.
    # Updated to the build.
    # SCOPE NOTE (ADO-137620): this copy constant is the ONLY thing that was
    # updated for that case. The assertion that follows it — that switching
    # AR->EN keeps the selected service — is deliberately left exactly as
    # written and fully able to fail; see the test's own comment.
    CASE_SIDEBAR_TITLE_AR = "جميع الخدمات"
    CASE_SECTION_HEADING_EN = "Choose the service you need"
    CASE_SECTION_HEADING_AR = "اختر الخدمة التي تحتاجها"
    CASE_BREADCRUMB_HOME = "Home"
    CASE_BREADCRUMB_CURRENT = "Services"
    CASE_DETAILS_BUTTON_LABEL = "Details"
    CASE_SUBHEADINGS_EN = (
        "Who This Service Is For",
        "Required Documents",
        "How to Apply",
    )
    CASE_SUBHEADINGS_AR = (
        # DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137695,
        # ADO-137643): case expected 'الفئات المستفيدة من الخدمة'; delivered
        # build renders 'لمن هذه الخدمة'. Updated to the build.
        "لمن هذه الخدمة",
        "المستندات المطلوبة",
        "كيفية التقديم",
    )
    CASE_SERVICE_NAMES_AR = (
        "العضوية الجديدة",
        "تجديد العضوية",
        "التصديق على التوقيع",
        "إلغاء المفوّض بالتوقيع",
    )
    CASE_MAIN_MENU_LABELS = (
        "About us",
        "Our Services",
        "E-services",
        "Committee",
        "Events",
        "Exhibitions",
        "Media Center",
        "Invest in Qatar",
        "B2B",
        "Contact us",
    )

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)
        self.accessibility = AccessibilityToolsComponent(page)

    # ══════════════════════════════════════════════════════════════════
    # Navigation — always anonymous (see the test module's docstring)
    # ══════════════════════════════════════════════════════════════════
    @allure.step("Open the Member's Services page")
    def open_member_services(self, locale: str = "en") -> "MemberServicesPage":
        """Load the page and wait for the fragment's first client render."""
        self.open_anonymous(web_url(MEMBER_SERVICES_PATH, locale=locale))
        self.wait_for(self.SECTION, first=True)
        self.wait_for_list_render()
        return self

    @allure.step("Open the Member's Services detail view for '{key}'")
    def open_service_detail(
        self, key: str, locale: str = "en"
    ) -> "MemberServicesPage":
        """Deep-link straight into one service's detail view via its hash —
        the fragment reads `location.hash` on mount (confirmed live), so this
        is a real user-reachable entry point, not a test-only shortcut."""
        self.open_anonymous(f"{web_url(MEMBER_SERVICES_PATH, locale=locale)}#{key}")
        self.wait_for(self.SECTION, first=True)
        self.wait_for_detail_render()
        return self

    @allure.step("Request the Member's Services URL without waiting for the fragment")
    def request_member_services_url(self, locale: str = "en") -> "MemberServicesPage":
        """Navigate to the page URL and stop at `domcontentloaded` — WITHOUT
        waiting for the fragment to render. For the unpublished / not-found
        cases, whose entire point is that the fragment may not be served at
        all; waiting for it there would turn an expected absence into a
        30-second timeout instead of a clean assertion."""
        self.open_anonymous(web_url(MEMBER_SERVICES_PATH, locale=locale))
        self.page.wait_for_load_state("domcontentloaded")
        return self

    @allure.step("Open the Qatar Chamber home page")
    def open_home(self, locale: str = "en") -> "MemberServicesPage":
        self.open_anonymous(web_url(HOME_PATH, locale=locale))
        self.wait_for(self.header.HEADER)
        return self

    @allure.step("Expand the 'Our Services' main-menu dropdown")
    def expand_our_services_menu(self) -> "MemberServicesPage":
        """Open the 'Our Services' dropdown.

        DISCLOSED SUBSTITUTION (#137614 step 2): the case says *click* 'Our
        Services'. On this build the top-level entry is a real `<a href>` to
        the Our Services landing page, so a click navigates away instead of
        expanding. The dropdown opens on HOVER (confirmed live), which is
        what this method does; the test records the substitution in its own
        docstring."""
        item = self._our_services_nav_item()
        item.locator("a.qc-nav-link").first.hover()
        item.locator(self.NAV_SUBMENU_PANEL).first.wait_for(
            state="visible", timeout=10000
        )
        return self

    @allure.step("Open Member's Services from the main menu")
    def open_member_services_via_main_menu(self) -> "MemberServicesPage":
        """Home -> 'Our Services' dropdown -> the Member's Services entry."""
        self.expand_our_services_menu()
        link = self._our_services_submenu_link_for_page()
        link.hover()
        link.click()
        self.page.wait_for_url(
            lambda url: PAGE_PATH_MARKER in url, timeout=30000
        )
        self.wait_for(self.SECTION, first=True)
        self.wait_for_list_render()
        return self

    def _our_services_nav_item(self):
        return self.page.locator(self.NAV_ITEM_WITH_SUBMENU).filter(
            has_text="Our Services"
        ).first

    def _our_services_submenu_link_for_page(self):
        """The submenu entry whose href is this page — located by TARGET, not
        by label, because the live label ("Member's Services") differs from
        the label the case states ("Membership Services"). The label itself
        is asserted separately by the test, so locating by href here keeps a
        copy mismatch from turning into a locator timeout."""
        return self._our_services_nav_item().locator(
            f'{self.NAV_SUBMENU_LINK}[href*="{PAGE_PATH_MARKER}"]'
        ).first

    def our_services_submenu_labels(self) -> list:
        item = self._our_services_nav_item()
        return [
            text.strip()
            for text in item.locator(self.NAV_SUBMENU_LINK).all_inner_texts()
        ]

    def is_our_services_submenu_expanded(self) -> bool:
        panel = self._our_services_nav_item().locator(self.NAV_SUBMENU_PANEL).first
        return panel.count() > 0 and panel.is_visible()

    def main_menu_labels(self) -> list:
        return self.header.nav_item_labels()

    # ── Fragment render waits (condition-based, never a sleep) ──────────
    def wait_for_list_render(self, timeout: int = 15000) -> None:
        self.wait_for_condition(
            """() => {
                const root = document.querySelector('section.qc-member-services');
                if (!root) return false;
                const list = root.querySelector('[data-qc-ms-listview]');
                return !!list && !list.hidden
                    && root.querySelectorAll('a.qc-ms-card').length > 0;
            }""",
            timeout=timeout,
        )

    def wait_for_detail_render(self, timeout: int = 15000) -> None:
        self.wait_for_condition(
            """() => {
                const root = document.querySelector('section.qc-member-services');
                if (!root) return false;
                const detail = root.querySelector('[data-qc-ms-detailview]');
                return !!detail && !detail.hidden
                    && !!root.querySelector('.qc-ms-panel-title')
                    && root.querySelectorAll('a.qc-ms-side-item.is-active').length === 1;
            }""",
            timeout=timeout,
        )

    def wait_for_panel_title(self, expected: str, timeout: int = 15000) -> None:
        """Wait until the content panel has finished re-rendering for a named
        service — the fragment replaces `[data-qc-ms-panel]`'s innerHTML, so
        reading straight after a click can catch the previous service."""
        self.wait_for_condition(
            """(expected) => {
                const t = document.querySelector('.qc-ms-panel-title');
                return !!t && t.textContent.trim() === expected;
            }""",
            arg=expected,
            timeout=timeout,
        )

    # ══════════════════════════════════════════════════════════════════
    # Actions
    # ══════════════════════════════════════════════════════════════════
    @allure.step("Click the 'Details' button on the '{key}' service card")
    def click_card_details(self, key: str) -> "MemberServicesPage":
        self.click(f'{self.CARD}[data-qc-ms-key="{key}"]')
        self.wait_for_detail_render()
        return self

    @allure.step("Select '{key}' in the 'All Services' sidebar")
    def select_sidebar_service(self, key: str) -> "MemberServicesPage":
        self.click(f'{self.SIDEBAR_ITEM}[data-qc-ms-key="{key}"]')
        self.wait_for_condition(
            """(key) => {
                const active = document.querySelectorAll('a.qc-ms-side-item.is-active');
                return active.length === 1 && active[0].dataset.qcMsKey === key
                    && !!document.querySelector('.qc-ms-panel-title');
            }""",
            arg=key,
        )
        return self

    @allure.step("Click the service CTA button")
    def click_cta(self, timeout: int = 20000):
        """Click the detail panel's CTA and return the page the visitor ends
        up on.

        The live CTA carries `target="_blank"`, so the destination arrives as
        a Playwright popup. Both outcomes are handled and reported, so the
        tab-behaviour cases (#137639 / #137640) can assert which one actually
        happened rather than being written for one of them:

            {"popup": <Page|None>, "landing_page": <Page>, "opened_new_tab": bool}
        """
        context = self.page.context
        before = len(context.pages)
        try:
            with self.page.expect_popup(timeout=timeout) as popup_info:
                self.click(self.CTA)
            popup = popup_info.value
            popup.wait_for_load_state("domcontentloaded", timeout=timeout)
            return {
                "popup": popup,
                "landing_page": popup,
                "opened_new_tab": True,
                "pages_before": before,
                "pages_after": len(context.pages),
            }
        except Exception:  # noqa: BLE001 — "no popup" is a state the test asserts on
            self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
            return {
                "popup": None,
                "landing_page": self.page,
                "opened_new_tab": False,
                "pages_before": before,
                "pages_after": len(context.pages),
            }

    @allure.step("Click the 'Home' breadcrumb link")
    def click_breadcrumb_home(self) -> "MemberServicesPage":
        # AUTOMATION BUG FIX 2026-09-27 (ADO-137621): this used to be
        # `click()` + `wait_for_load_state("domcontentloaded")`. click()
        # resolves on DISPATCH and wait_for_load_state returns immediately
        # while the ORIGIN document is still current, so the test's
        # `current_url()` read came back as the Member's Services URL and the
        # navigation assertion failed on timing, not on behaviour.
        # base_page.wait_for_url() (core/web/base_page.py) is the framework's
        # documented helper for exactly this hazard.
        self.click(self.BREADCRUMB_HOME_LINK)
        self.wait_for_url(lambda url: PAGE_PATH_MARKER not in url)
        return self

    @allure.step("Click the 'Services' breadcrumb link")
    def click_breadcrumb_current(self) -> "MemberServicesPage":
        """Click the second breadcrumb segment. On this build it is a plain
        `<span>` with no href (see `breadcrumb_current_is_link()`), so the
        click is a no-op — the test asserts the link-ness FIRST so the red
        names the missing link rather than a silent non-navigation."""
        self.click(self.BREADCRUMB_CURRENT)
        return self

    # ── Language ────────────────────────────────────────────────────────
    @allure.step("Switch the site language to Arabic")
    def switch_to_arabic(self) -> "MemberServicesPage":
        self.header.switch_to_arabic()
        self._wait_for_member_services_after_language_switch()
        return self

    @allure.step("Switch the site language to English")
    def switch_to_english(self) -> "MemberServicesPage":
        self.header.switch_to_english()
        self._wait_for_member_services_after_language_switch()
        return self

    def _wait_for_member_services_after_language_switch(self) -> None:
        """The site normalises the URL across a language switch (AR detail is
        `/ar/web/qatar-chamber/member-services#…`; AR->EN lands on
        `/our-services/member-services` with no `/web/qatar-chamber`), so the
        wait is on the marker substring PLUS the fragment's own rendered
        outcome — `HeaderComponent.switch_to_*` only waits on the header
        logo, which is satisfied while this fragment is still re-rendering."""
        self.page.wait_for_url(lambda url: PAGE_PATH_MARKER in url, timeout=30000)
        self.wait_for(self.SECTION, first=True)
        self.wait_for_condition(
            """() => {
                const root = document.querySelector('section.qc-member-services');
                if (!root) return false;
                const list = root.querySelector('[data-qc-ms-listview]');
                const detail = root.querySelector('[data-qc-ms-detailview]');
                if (list && !list.hidden) return root.querySelectorAll('a.qc-ms-card').length > 0;
                if (detail && !detail.hidden) return !!root.querySelector('.qc-ms-panel-title');
                return false;
            }""",
            timeout=15000,
        )

    def language_toggle_label(self) -> str:
        return self.header.language_switcher_label()

    # ── Theme ───────────────────────────────────────────────────────────
    @allure.step("Switch the site appearance to dark mode")
    def enable_dark_mode(self) -> "MemberServicesPage":
        self.accessibility.enable_dark_mode()
        return self

    @allure.step("Switch the site appearance to light mode")
    def enable_light_mode(self) -> "MemberServicesPage":
        """Idempotent counterpart of `enable_dark_mode()`: a fresh anonymous
        context already renders `<html data-theme="light">`, so this returns
        immediately unless a previous step turned dark mode on."""
        if self.current_theme() == "light":
            return self
        self.accessibility.click_accessibility_button()
        self.wait_for(self.accessibility.PANEL)
        if self.accessibility.is_dark_mode_switch_checked():
            self.accessibility.switch_to_dark_mode()
        self.wait_for_condition(
            "() => document.documentElement.getAttribute('data-theme') !== 'dark'"
        )
        self.accessibility.close_panel()
        return self

    def current_theme(self) -> str | None:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('data-theme')"
        )

    # ══════════════════════════════════════════════════════════════════
    # Generic readers (never raise on a missing element)
    # ══════════════════════════════════════════════════════════════════
    def element_count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def computed_style(self, locator: str, properties: tuple, index: int = 0) -> dict:
        """Computed values of `properties` on the `index`-th match. `{}` when
        nothing matches, so the test's own presence assertion fires first."""
        target = self.page.locator(locator)
        if target.count() <= index:
            return {}
        return target.nth(index).evaluate(
            "(el, props) => { const cs = getComputedStyle(el); const out = {};"
            " for (const p of props) out[p] = cs[p]; return out; }",
            list(properties),
        )

    def pseudo_style(
        self, locator: str, pseudo: str, properties: tuple, index: int = 0
    ) -> dict:
        target = self.page.locator(locator)
        if target.count() <= index:
            return {}
        return target.nth(index).evaluate(
            "(el, args) => { const cs = getComputedStyle(el, args.pseudo);"
            " const out = {}; for (const p of args.props) out[p] = cs[p]; return out; }",
            {"pseudo": pseudo, "props": list(properties)},
        )

    def bounding_box(self, locator: str, index: int = 0) -> dict | None:
        target = self.page.locator(locator)
        if target.count() <= index:
            return None
        return target.nth(index).bounding_box()

    def text_of(self, locator: str, index: int = 0) -> str | None:
        target = self.page.locator(locator)
        if target.count() <= index:
            return None
        return target.nth(index).inner_text().strip()

    def texts_of(self, locator: str) -> list:
        return [t.strip() for t in self.page.locator(locator).all_inner_texts()]

    def attribute_of(self, locator: str, name: str, index: int = 0) -> str | None:
        target = self.page.locator(locator)
        if target.count() <= index:
            return None
        return target.nth(index).get_attribute(name)

    def icon_size(self, locator: str, index: int = 0) -> tuple | None:
        box = self.bounding_box(locator, index)
        return (round(box["width"]), round(box["height"])) if box else None

    # ── Document-level state ────────────────────────────────────────────
    def current_url(self) -> str:
        return self.page.url

    def document_direction(self) -> str:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('dir') "
            "|| getComputedStyle(document.body).direction"
        )

    def document_language(self) -> str:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('lang') || ''"
        )

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).first.evaluate(
            "el => getComputedStyle(el).direction"
        )

    def viewport_size(self) -> dict:
        return self.page.evaluate(
            "() => ({width: window.innerWidth, height: window.innerHeight})"
        )

    def has_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > "
            "document.documentElement.clientWidth"
        )

    def horizontal_overflow_report(self) -> dict:
        """Every element whose right edge extends past the document width, as
        `{'docWidth', 'scrollWidth', 'offenders': [{name, left, right}]}`.

        Exists so a responsive failure NAMES the culprit. At 768px the live
        offender is `P.qc-ms-intro` (a hard 536px width that does not shrink,
        overflowing to right=1089) — a real defect in this PBI's own
        fragment. `DIV.grecaptcha-badge` also overflows but is third-party
        chrome; listing both by name stops triage mis-attributing one for the
        other."""
        return self.page.evaluate(
            """() => {
                const docWidth = document.documentElement.clientWidth;
                const offenders = [];
                document.querySelectorAll('*').forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.width > 0 && r.right > docWidth + 1) {
                        const cls = (typeof el.className === 'string' && el.className)
                            ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.')
                            : '';
                        offenders.push({name: el.tagName + cls,
                                        left: Math.round(r.left),
                                        right: Math.round(r.right)});
                    }
                });
                return {docWidth,
                        scrollWidth: document.documentElement.scrollWidth,
                        offenders: offenders.slice(0, 20)};
            }"""
        )

    def fragment_offenders(self) -> list:
        """The overflow offenders that belong to THIS fragment (`qc-ms-*`),
        i.e. the ones this PBI owns — third-party chrome excluded."""
        return [
            offender
            for offender in self.horizontal_overflow_report()["offenders"]
            if "qc-ms-" in offender["name"] or "qc-member-services" in offender["name"]
        ]

    def navigation_fingerprint(self) -> dict:
        """State that survives a client-side view swap but NOT a document
        reload: a marker stashed on `window`, the navigation-entry count and
        the current URL. `stamp_navigation_marker()` plants the marker."""
        return self.page.evaluate(
            """() => ({
                marker: window.__qcMsNavigationMarker || null,
                navigationEntries: performance.getEntriesByType('navigation').length,
                url: location.href,
                hash: location.hash
            })"""
        )

    def stamp_navigation_marker(self) -> "MemberServicesPage":
        self.page.evaluate("() => { window.__qcMsNavigationMarker = 'alive'; }")
        return self

    # ══════════════════════════════════════════════════════════════════
    # Hero band
    # ══════════════════════════════════════════════════════════════════
    def hero_style(self) -> dict:
        return self.computed_style(self.HERO, ("height", "padding"))

    def hero_inner_style(self) -> dict:
        return self.computed_style(self.HERO_INNER, ("padding", "maxWidth"))

    def hero_overlay_gradient(self) -> str | None:
        return self.computed_style(self.HERO_OVERLAY, ("backgroundImage",)).get(
            "backgroundImage"
        )

    def hero_background_image(self) -> str | None:
        return self.computed_style(self.HERO_BACKGROUND, ("backgroundImage",)).get(
            "backgroundImage"
        )

    def hero_box(self) -> dict | None:
        return self.bounding_box(self.HERO)

    def page_title_text(self) -> str | None:
        return self.text_of(self.PAGE_TITLE)

    def page_title_style(self) -> dict:
        return self.computed_style(
            self.PAGE_TITLE,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color", "textAlign"),
        )

    def page_title_box(self) -> dict | None:
        return self.bounding_box(self.PAGE_TITLE)

    # ══════════════════════════════════════════════════════════════════
    # Breadcrumb
    # ══════════════════════════════════════════════════════════════════
    def breadcrumb_texts(self) -> list:
        return self.texts_of(self.BREADCRUMB_CRUMBS)

    def breadcrumb_home_text(self) -> str | None:
        return self.text_of(self.BREADCRUMB_HOME_LABEL)

    def breadcrumb_home_href(self) -> str | None:
        return self.attribute_of(self.BREADCRUMB_HOME_LINK, "href")

    def breadcrumb_home_icon_count(self) -> int:
        return self.element_count(self.BREADCRUMB_HOME_ICON)

    def breadcrumb_separator_icon_count(self) -> int:
        return self.element_count(self.BREADCRUMB_SEPARATOR)

    def breadcrumb_separator_transform(self) -> str | None:
        return self.computed_style(self.BREADCRUMB_SEPARATOR, ("transform",)).get(
            "transform"
        )

    def breadcrumb_current_text(self) -> str | None:
        return self.text_of(self.BREADCRUMB_CURRENT)

    def breadcrumb_current_is_link(self) -> bool:
        """True only when the second crumb is a real anchor with an href."""
        return self.element_count(self.BREADCRUMB_CURRENT_AS_LINK) > 0 or bool(
            self.attribute_of(self.BREADCRUMB_CURRENT, "href")
        )

    def breadcrumb_current_href(self) -> str | None:
        return self.attribute_of(self.BREADCRUMB_CURRENT, "href")

    def breadcrumb_style(self, which: str = "home") -> dict:
        locator = (
            self.BREADCRUMB_HOME_LINK if which == "home" else self.BREADCRUMB_CURRENT
        )
        return self.computed_style(
            locator,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color"),
        )

    def breadcrumb_box(self) -> dict | None:
        return self.bounding_box(self.BREADCRUMB)

    # ══════════════════════════════════════════════════════════════════
    # Heading + intro row
    # ══════════════════════════════════════════════════════════════════
    def content_style(self) -> dict:
        return self.computed_style(self.CONTENT, ("padding", "gap", "display"))

    def headrow_style(self) -> dict:
        return self.computed_style(self.HEADROW, ("gap", "display"))

    def section_heading_text(self) -> str | None:
        return self.text_of(self.SECTION_HEADING)

    def section_heading_style(self) -> dict:
        return self.computed_style(
            self.SECTION_HEADING,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color", "textAlign"),
        )

    def section_heading_box(self) -> dict | None:
        return self.bounding_box(self.SECTION_HEADING)

    def intro_text(self) -> str | None:
        return self.text_of(self.INTRO)

    def intro_style(self) -> dict:
        return self.computed_style(
            self.INTRO,
            (
                "fontFamily",
                "fontSize",
                "fontWeight",
                "lineHeight",
                "color",
                "textAlign",
                "width",
                "maxWidth",
            ),
        )

    def intro_box(self) -> dict | None:
        return self.bounding_box(self.INTRO)

    # ══════════════════════════════════════════════════════════════════
    # List view
    # ══════════════════════════════════════════════════════════════════
    def is_list_view_visible(self) -> bool:
        return self.page.evaluate(
            """() => { const el = document.querySelector('[data-qc-ms-listview]');
                       return !!el && !el.hidden; }"""
        )

    def listview_style(self) -> dict:
        return self.computed_style(
            self.LIST_VIEW, ("display", "flexDirection", "gap")
        )

    def service_card_count(self) -> int:
        return self.element_count(self.CARD)

    def service_card_keys(self) -> list:
        return self.page.locator(self.CARD).evaluate_all(
            "els => els.map(e => e.getAttribute('data-qc-ms-key'))"
        )

    def service_card_names(self) -> list:
        return self.texts_of(self.CARD_NAME)

    def service_card_descriptions(self) -> list:
        return self.texts_of(self.CARD_DESCRIPTION)

    def details_button_labels(self) -> list:
        return self.texts_of(self.CARD_DETAILS_LABEL)

    def cards_container_style(self) -> dict:
        return self.computed_style(self.CARDS, ("display", "gap"))

    def card_style(self, index: int = 0) -> dict:
        return self.computed_style(
            self.CARD,
            (
                "backgroundColor",
                "borderRadius",
                "padding",
                "gap",
                "boxShadow",
                "border",
                "borderImageSource",
                "display",
            ),
            index=index,
        )

    def card_icon_tile_style(self, index: int = 0) -> dict:
        return self.computed_style(
            self.CARD_ICON_TILE,
            ("backgroundColor", "borderRadius", "width", "height"),
            index=index,
        )

    def card_icon_count(self) -> int:
        return self.element_count(f"{self.CARD_ICON_TILE} .qc-ms-ico")

    def card_name_style(self, index: int = 0) -> dict:
        return self.computed_style(
            self.CARD_NAME,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color", "textAlign"),
            index=index,
        )

    def card_description_style(self, index: int = 0) -> dict:
        return self.computed_style(
            self.CARD_DESCRIPTION,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color", "textAlign"),
            index=index,
        )

    def details_button_style(self, index: int = 0) -> dict:
        return self.computed_style(
            self.CARD_DETAILS_BUTTON,
            (
                "fontFamily",
                "fontSize",
                "fontWeight",
                "lineHeight",
                "color",
                "backgroundColor",
                "borderRadius",
                "padding",
                "gap",
                "border",
                "borderColor",
            ),
            index=index,
        )

    def details_button_icon_size(self, index: int = 0) -> tuple | None:
        return self.icon_size(self.CARD_DETAILS_ICON, index)

    def card_box(self, index: int = 0) -> dict | None:
        return self.bounding_box(self.CARD, index)

    def card_boxes(self) -> list:
        return self.page.locator(self.CARD).evaluate_all(
            """els => els.map(e => { const r = e.getBoundingClientRect();
                return {key: e.getAttribute('data-qc-ms-key'),
                        x: Math.round(r.x), y: Math.round(r.y),
                        width: Math.round(r.width), height: Math.round(r.height)}; })"""
        )

    def cards_container_box(self) -> dict | None:
        return self.bounding_box(self.CARDS)

    def card_name_box(self, index: int = 0) -> dict | None:
        return self.bounding_box(self.CARD_NAME, index)

    def card_description_box(self, index: int = 0) -> dict | None:
        return self.bounding_box(self.CARD_DESCRIPTION, index)

    def details_button_box(self, index: int = 0) -> dict | None:
        return self.bounding_box(self.CARD_DETAILS_BUTTON, index)

    def fragment_count(self) -> int:
        """How many Member's Services fragments the response rendered — `0`
        when the page is not served at all (the unpublished / not-found
        cases)."""
        return self.element_count(self.SECTION)

    def list_support_style(self) -> dict:
        return self.computed_style(
            self.LIST_SUPPORT, ("width", "borderRadius", "overflow", "display")
        )

    def list_support_box(self) -> dict | None:
        return self.bounding_box(self.LIST_SUPPORT)

    def list_support_image_src(self) -> str | None:
        return self.attribute_of(self.LIST_SUPPORT_IMAGE, "src")

    def is_list_support_rendered(self) -> bool:
        return self.page.evaluate(
            """() => { const img = document.querySelector('[data-qc-ms-list-support-img]');
                       return !!img && img.complete && img.naturalWidth > 0; }"""
        )

    # ══════════════════════════════════════════════════════════════════
    # Detail view — container, sidebar, divider
    # ══════════════════════════════════════════════════════════════════
    def is_detail_view_visible(self) -> bool:
        return self.page.evaluate(
            """() => { const el = document.querySelector('[data-qc-ms-detailview]');
                       return !!el && !el.hidden; }"""
        )

    def detail_container_style(self) -> dict:
        return self.computed_style(
            self.DETAIL_CONTAINER,
            ("border", "borderRadius", "display", "flexDirection", "gap"),
        )

    def detail_container_box(self) -> dict | None:
        return self.bounding_box(self.DETAIL_CONTAINER)

    def sidebar_style(self) -> dict:
        return self.computed_style(
            self.SIDEBAR, ("width", "display", "border", "borderRadius")
        )

    def sidebar_box(self) -> dict | None:
        return self.bounding_box(self.SIDEBAR)

    def sidebar_title_text(self) -> str | None:
        return self.text_of(self.SIDEBAR_TITLE)

    def sidebar_title_style(self) -> dict:
        return self.computed_style(
            self.SIDEBAR_TITLE,
            (
                "fontFamily",
                "fontSize",
                "fontWeight",
                "lineHeight",
                "color",
                "padding",
            ),
        )

    def sidebar_row_count(self) -> int:
        return self.element_count(self.SIDEBAR_ITEM)

    def sidebar_labels(self) -> list:
        return self.texts_of(self.SIDEBAR_LABEL)

    def sidebar_keys(self) -> list:
        return self.page.locator(self.SIDEBAR_ITEM).evaluate_all(
            "els => els.map(e => e.getAttribute('data-qc-ms-key'))"
        )

    def selected_sidebar_keys(self) -> list:
        return self.page.locator(self.SIDEBAR_ITEM_SELECTED).evaluate_all(
            "els => els.map(e => e.getAttribute('data-qc-ms-key'))"
        )

    def selected_sidebar_count(self) -> int:
        return self.element_count(self.SIDEBAR_ITEM_SELECTED)

    def _sidebar_row_index(self, key: str) -> int | None:
        keys = self.sidebar_keys()
        return keys.index(key) if key in keys else None

    def sidebar_row_style(self, key: str) -> dict:
        index = self._sidebar_row_index(key)
        if index is None:
            return {}
        return self.computed_style(
            self.SIDEBAR_ITEM,
            (
                "backgroundColor",
                "borderLeft",
                "borderRight",
                "borderTop",
                "borderWidth",
                "borderStyle",
                "borderColor",
                "padding",
                "gap",
            ),
            index=index,
        )

    def sidebar_row_label_style(self, key: str) -> dict:
        index = self._sidebar_row_index(key)
        if index is None:
            return {}
        return self.computed_style(
            self.SIDEBAR_LABEL,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color"),
            index=index,
        )

    def sidebar_row_icon_style(self, key: str) -> dict:
        index = self._sidebar_row_index(key)
        if index is None:
            return {}
        return self.computed_style(
            self.SIDEBAR_ICON_TILE,
            ("backgroundColor", "borderRadius", "width", "height"),
            index=index,
        )

    def sidebar_row_box(self, key: str) -> dict | None:
        index = self._sidebar_row_index(key)
        return None if index is None else self.bounding_box(self.SIDEBAR_ITEM, index)

    def sidebar_icon_tile_box(self, index: int = 0) -> dict | None:
        return self.bounding_box(self.SIDEBAR_ICON_TILE, index)

    def sidebar_chevron_count(self) -> int:
        return self.element_count(self.SIDEBAR_CHEVRON_ICON)

    def sidebar_chevron_transform(self) -> str | None:
        return self.computed_style(self.SIDEBAR_CHEVRON, ("transform",)).get("transform")

    def sidebar_chevron_box(self, key: str) -> dict | None:
        index = self._sidebar_row_index(key)
        return None if index is None else self.bounding_box(self.SIDEBAR_CHEVRON, index)

    def vertical_divider_style(self) -> dict:
        return self.computed_style(
            self.VERTICAL_DIVIDER, ("width", "backgroundColor", "display")
        )

    def vertical_divider_box(self) -> dict | None:
        return self.bounding_box(self.VERTICAL_DIVIDER)

    # ══════════════════════════════════════════════════════════════════
    # Detail view — content panel
    # ══════════════════════════════════════════════════════════════════
    def panel_style(self) -> dict:
        return self.computed_style(
            self.PANEL, ("padding", "gap", "display", "flexDirection")
        )

    def panel_box(self) -> dict | None:
        return self.bounding_box(self.PANEL)

    def panel_tile_style(self) -> dict:
        return self.computed_style(
            self.PANEL_TILE, ("backgroundColor", "borderRadius", "width", "height")
        )

    def panel_icon_count(self) -> int:
        return self.element_count(f"{self.PANEL_TILE} .qc-ms-ico")

    def panel_title_text(self) -> str | None:
        return self.text_of(self.PANEL_TITLE)

    def panel_title_style(self) -> dict:
        return self.computed_style(
            self.PANEL_TITLE,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color", "textAlign"),
        )

    def panel_title_box(self) -> dict | None:
        return self.bounding_box(self.PANEL_TITLE)

    def panel_intro_text(self) -> str | None:
        return self.text_of(self.PANEL_INTRO)

    def panel_intro_style(self) -> dict:
        return self.computed_style(
            self.PANEL_INTRO,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color", "textAlign"),
        )

    def panel_intro_box(self) -> dict | None:
        return self.bounding_box(self.PANEL_INTRO)

    def panel_divider_count(self) -> int:
        return self.element_count(self.PANEL_DIVIDER)

    def panel_divider_box(self) -> dict | None:
        return self.bounding_box(self.PANEL_DIVIDER)

    def subheading_texts(self) -> list:
        return self.texts_of(self.SUBHEADING)

    def subheading_box(self, index: int = 0) -> dict | None:
        return self.bounding_box(self.SUBHEADING, index)

    def subheading_style(self, index: int = 0) -> dict:
        return self.computed_style(
            self.SUBHEADING,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color", "textAlign"),
            index=index,
        )

    def subsection_body_text(self, heading: str) -> str | None:
        """The rendered body immediately following a named subsection heading
        — `None` when that heading is not rendered at all (which is exactly
        what the 'empty subsections are hidden' cases assert on)."""
        return self.page.evaluate(
            """(heading) => {
                const headings = [...document.querySelectorAll('.qc-ms-subheading')];
                const match = headings.find(h => h.textContent.trim() === heading);
                if (!match) return null;
                let node = match.nextElementSibling;
                while (node && !node.classList.contains('qc-ms-richtext')
                       && !node.classList.contains('qc-ms-reqdocs')) {
                    if (node.classList.contains('qc-ms-subheading')) return null;
                    node = node.nextElementSibling;
                }
                return node ? node.textContent.trim() : null;
            }""",
            heading,
        )

    def has_subheading(self, heading: str) -> bool:
        return heading in self.subheading_texts()

    def body_text_style(self, index: int = 0) -> dict:
        return self.computed_style(
            self.RICHTEXT,
            ("fontFamily", "fontSize", "fontWeight", "lineHeight", "color", "textAlign"),
            index=index,
        )

    def panel_html(self) -> str | None:
        target = self.page.locator(self.PANEL)
        if target.count() == 0:
            return None
        return target.first.evaluate("el => el.innerHTML")

    def panel_text(self) -> str | None:
        return self.text_of(self.PANEL)

    def page_text(self) -> str:
        return self.page.evaluate("() => document.body.innerText")

    # ── Required Documents dash list ────────────────────────────────────
    def required_documents_items(self) -> list:
        return self.texts_of(self.REQUIRED_DOCS_ITEM)

    def required_documents_count(self) -> int:
        return self.element_count(self.REQUIRED_DOCS_ITEM)

    def required_documents_list_style(self) -> dict:
        return self.computed_style(
            self.REQUIRED_DOCS_LIST, ("display", "gap", "listStyleType")
        )

    def required_documents_item_style(self, index: int = 0) -> dict:
        return self.computed_style(
            self.REQUIRED_DOCS_ITEM,
            (
                "fontFamily",
                "fontSize",
                "fontWeight",
                "lineHeight",
                "color",
                "display",
                "gap",
            ),
            index=index,
        )

    def required_documents_marker_style(self, index: int = 0) -> dict:
        """The `::before` pseudo-element that paints the dash marker."""
        return self.pseudo_style(
            self.REQUIRED_DOCS_ITEM,
            "::before",
            ("content", "width", "height", "backgroundColor"),
            index=index,
        )

    # ── CTA ─────────────────────────────────────────────────────────────
    def cta_count(self) -> int:
        return self.element_count(self.CTA)

    def cta_label(self) -> str | None:
        return self.text_of(self.CTA_LABEL)

    def cta_href(self) -> str | None:
        return self.attribute_of(self.CTA, "href")

    def cta_target(self) -> str | None:
        return self.attribute_of(self.CTA, "target")

    def cta_style(self) -> dict:
        return self.computed_style(
            self.CTA,
            (
                "fontFamily",
                "fontSize",
                "fontWeight",
                "lineHeight",
                "color",
                "backgroundColor",
                "borderRadius",
                "padding",
                "gap",
                "display",
                "width",
            ),
        )

    def cta_icon_size(self) -> tuple | None:
        return self.icon_size(self.CTA_ICON)

    def cta_box(self) -> dict | None:
        return self.bounding_box(self.CTA)

    def cta_icon_is_leading(self) -> bool | None:
        """True when the CTA's arrow icon sits BEFORE its label (the RTL
        arrangement #137643 describes), False when it trails it (LTR),
        `None` when there is no CTA at all."""
        return self.page.evaluate(
            """() => {
                const cta = document.querySelector('a.qc-ms-cta');
                if (!cta) return null;
                const icon = cta.querySelector('svg');
                const label = cta.querySelector('span');
                if (!icon || !label) return null;
                return icon.getBoundingClientRect().x < label.getBoundingClientRect().x;
            }"""
        )

    def cta_icon_transform(self) -> str | None:
        return self.computed_style(self.CTA_ICON, ("transform",)).get("transform")

    # ── Detail supporting image ─────────────────────────────────────────
    def detail_support_style(self) -> dict:
        """NOTE for #137643: the case states the supporting image carries
        `40px 0px 40px 40px` **padding** in Arabic. This build carries that
        inset as a **margin** (`margin: 40px 0px 40px 40px` in AR, mirrored
        to `40px 40px 40px 0px` in EN) with `padding: 0px` — measured live,
        read-only. Both are reported here so the test can assert the real
        carrier and record the discrepancy instead of reding on `padding`."""
        return self.computed_style(
            self.DETAIL_SUPPORT,
            ("margin", "padding", "width", "borderRadius", "overflow", "display"),
        )

    def detail_support_box(self) -> dict | None:
        return self.bounding_box(self.DETAIL_SUPPORT)

    def detail_support_image_src(self) -> str | None:
        return self.attribute_of(self.DETAIL_SUPPORT_IMAGE, "src")

    def is_detail_support_visible(self) -> bool:
        return self.page.evaluate(
            """() => { const el = document.querySelector('[data-qc-ms-detail-support]');
                       return !!el && !el.hidden; }"""
        )

    # ══════════════════════════════════════════════════════════════════
    # Header / chrome surfaces the theme cases name
    # ══════════════════════════════════════════════════════════════════
    def page_background_color(self) -> str:
        return self.page.evaluate(
            "() => getComputedStyle(document.body).backgroundColor"
        )

    def header_background_color(self) -> str | None:
        return self.computed_style(self.HEADER, ("backgroundColor",)).get(
            "backgroundColor"
        )

    def nav_label_color(self) -> str | None:
        return self.computed_style(self.HEADER_NAV_LINK, ("color",)).get("color")

    def language_chip_style(self) -> dict:
        return self.computed_style(
            self.HEADER_LANGUAGE_CHIP, ("backgroundColor", "color")
        )

    def profile_icon_button_count(self) -> int:
        """0 on this build — no profile/avatar control exists in the public
        header (verified live). #137651 names one; the test asserts its
        presence LAST so the eight verifiable dark-mode tokens report first."""
        return self.element_count(self.PROFILE_ICON_BUTTON)

    def profile_icon_button_style(self) -> dict:
        return self.computed_style(
            self.PROFILE_ICON_BUTTON, ("color", "backgroundColor")
        )

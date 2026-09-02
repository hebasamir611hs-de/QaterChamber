"""
web/pages/home_services/home_services_admin_page.py — HomeServicesAdminPage.

PBI 129371 / QC-HOME-003 "Our Services Section" — no Control_Panel-tagged
cases were handed off for this PBI in this batch (all 17 cases carry
Platform=Web only). This file exists only because 2 of those 17 Web-platform
cases have their OWN Arrange step needing an authenticated Site Content
Editor session against the Our Services content-management screen before the
Web-platform assertion can run:
  - TC 135353 — "Set every service card's Active Status to False" then
    confirm the section is absent from the live Home Page.
  - TC 135414 — "Unpublish the Our Services listing page in CMS" then
    confirm the "View All Services" CTA is not rendered.
Exactly the same shape as home_strategic_partners_admin_page.py's TC 136289
chain / home_community_partners_admin_page.py's TC 135811.

STATUS: BLOCKED, not guessed (2026-08-26) — same, already-documented
project-wide blocker as every sibling *_admin_page.py in this tree (commit
2cbbb4c): TEST_USER / TEST_PASSWORD are blank in this machine's .env. The
anonymous /c/portal/login FORM itself is reachable and its locators are
real/confirmed (see the shared web/pages/components/cms_login_page.py this
Page Object composes), but nothing PAST login — the Home Page management
entry point, the Our Services content list, its per-entry Active Status
toggle, and the Our Services listing page's own Publish/Unpublish control —
could be reached this session, and no Playwright MCP fallback is available
in this environment either.

Every locator below is the literal TODO placeholder string (never a
guessed-but-plausible Liferay selector), same convention as every sibling
*_admin_page.py in this tree. Replace only after confirming the real Our
Services content-management screen live — never mark this file "done" by
guessing a plausible-looking Liferay object/fragment-configuration selector.

IMPORTANT — deactivate_all_service_cards() / unpublish_listing_page() are
DESTRUCTIVE and NOT parallel-safe/idempotent by themselves: they mutate the
shared qcdev homepage state every OTHER test in
test_home_services_web.py depends on if run concurrently (pytest-xdist runs
`-n 3` by default per pytest.ini). Whoever fills in the real locators below
MUST also add a matching restore/teardown call (reactivate_all_service_cards(),
republish_listing_page()) in each test's teardown/finally — already wired in
test_home_services_web.py's TC 135353/135414 — and should consider running
these 2 tests alone (`pytest -k 135353 or 135414`) rather than as part of a
parallel full-suite run, until each restore path is confirmed to restore the
exact prior state.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_TODO_PREFIX = "TODO:"


def _todo(what: str) -> str:
    return f"{_TODO_PREFIX} run tools/extract_locators.py (as an authenticated Site Content Editor) against the live Our Services content-management screen and paste the confirmed selector for {what}"


class HomeServicesAdminPage(BasePage):
    # ── Unreachable without an authenticated session this run — see docstring ──
    HOME_PAGE_MANAGEMENT_LINK = _todo("the 'Home Page management' nav item")
    OUR_SERVICES_MANAGEMENT_LINK = _todo("the 'Our Services' content-management entry point")
    SERVICE_CARD_ROW = _todo("one service-card entry row in the Our Services list")
    SERVICE_ACTIVE_STATUS_TOGGLE = _todo("a service-card entry's Active/Inactive control")
    SAVE_BUTTON = _todo("the Our Services management screen's Save button")
    LISTING_PAGE_MANAGEMENT_LINK = _todo("the Our Services LISTING PAGE's own page-management entry point (distinct from the card list)")
    LISTING_PAGE_UNPUBLISH_BUTTON = _todo("the Our Services listing page's Unpublish control")
    LISTING_PAGE_PUBLISH_BUTTON = _todo("the Our Services listing page's Publish control")
    LISTING_PAGE_STATUS_INDICATOR = _todo("the Our Services listing page's Status (Draft/Published) indicator")

    def open_control_panel_home(self) -> "HomeServicesAdminPage":
        self.open(control_panel_url("/group/qatar-chamber"))
        return self

    def navigate_to_our_services_management(self) -> "HomeServicesAdminPage":
        self.click(self.HOME_PAGE_MANAGEMENT_LINK)
        self.click(self.OUR_SERVICES_MANAGEMENT_LINK)
        return self

    def service_card_count(self) -> int:
        return self.page.locator(self.SERVICE_CARD_ROW).count()

    # ── TC 135353 — deactivate / reactivate every service card ───────────
    def deactivate_all_service_cards(self) -> "HomeServicesAdminPage":
        """NOT idempotent/parallel-safe on its own — see module docstring's
        teardown/reactivation warning."""
        rows = self.page.locator(self.SERVICE_CARD_ROW)
        for i in range(rows.count()):
            toggle = rows.nth(i).locator(self.SERVICE_ACTIVE_STATUS_TOGGLE)
            if toggle.is_checked():
                toggle.click()
        self.click(self.SAVE_BUTTON)
        return self

    def reactivate_all_service_cards(self) -> "HomeServicesAdminPage":
        """Teardown counterpart of deactivate_all_service_cards()."""
        rows = self.page.locator(self.SERVICE_CARD_ROW)
        for i in range(rows.count()):
            toggle = rows.nth(i).locator(self.SERVICE_ACTIVE_STATUS_TOGGLE)
            if not toggle.is_checked():
                toggle.click()
        self.click(self.SAVE_BUTTON)
        return self

    # ── TC 135414 — unpublish / republish the Our Services listing page ──
    def navigate_to_listing_page_management(self) -> "HomeServicesAdminPage":
        self.click(self.HOME_PAGE_MANAGEMENT_LINK)
        self.click(self.LISTING_PAGE_MANAGEMENT_LINK)
        return self

    def unpublish_listing_page(self) -> "HomeServicesAdminPage":
        """NOT idempotent/parallel-safe on its own — see module docstring's
        teardown/republish warning."""
        self.click(self.LISTING_PAGE_UNPUBLISH_BUTTON)
        return self

    def republish_listing_page(self) -> "HomeServicesAdminPage":
        """Teardown counterpart of unpublish_listing_page()."""
        self.click(self.LISTING_PAGE_PUBLISH_BUTTON)
        return self

    def listing_page_status_text(self) -> str:
        return self.text(self.LISTING_PAGE_STATUS_INDICATOR)

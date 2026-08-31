"""
web/pages/home_community_partners/home_community_partners_admin_page.py —
HomeCommunityPartnersAdminPage.

PBI 129385 / QC-HOME-009 "Community Partners" — no Control_Panel-tagged
cases were handed off for this PBI in this batch. This file exists only
because TC 135811's own Arrange step
("Deactivate/unpublish all partner entries in the CMS") requires an
authenticated Site Content Editor session to reach the Community Partners
content-management screen, even though TC 135811 itself is tagged
Platform=Web (the assertion is on the public Home Page, in
home_community_partners_page.py / test_home_community_partners_web.py).

STATUS: BLOCKED, not guessed (2026-08-24) — same, already-documented
project-wide blocker as home_featured_event_admin_page.py (commit 2cbbb4c):
TEST_USER / TEST_PASSWORD are blank in this machine's .env. The anonymous
/c/portal/login FORM itself is reachable and its locators are real/
confirmed (see the shared web/pages/components/cms_login_page.py this
Page Object composes), but nothing PAST login — the Home Page management
entry point, the Community Partners content list, and its per-entry
Active/Inactive (unpublish) control — could be reached this session, and no
Playwright MCP fallback is available in this environment either.

Every locator below is the literal TODO placeholder string (never a
guessed-but-plausible Liferay selector), same convention as
home_featured_event_admin_page.py / the `_UNRESOLVED` collection-time
skipif gate in test_home_community_partners_web.py's TC 135811 test.

Replace only after confirming the real Community Partners content-management
screen live — never mark this file "done" by guessing a plausible-looking
Liferay object/fragment-configuration selector.

IMPORTANT — this action is DESTRUCTIVE and NOT parallel-safe/idempotent by
itself: it unpublishes every partner entry, which would break the shared
qcdev homepage state that TC 135808/135812/135815's Web-platform assertions
depend on if run concurrently (pytest-xdist runs `-n 3` by default per
pytest.ini). Whoever fills in the real locators below MUST also add a
matching `reactivate_all_partners()` (or equivalent) call in the test's
teardown/finally, and should consider running TC 135811 alone
(`pytest -k 135811`) rather than as part of a parallel full-suite run, until
that reactivation path is confirmed to restore the exact prior state.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_TODO_PREFIX = "TODO:"


def _todo(what: str) -> str:
    return f"{_TODO_PREFIX} run tools/extract_locators.py (as an authenticated Site Content Editor) against the live Community Partners content-management screen and paste the confirmed selector for {what}"


class HomeCommunityPartnersAdminPage(BasePage):
    # ── Unreachable without an authenticated session this run — see docstring ──
    HOME_PAGE_MANAGEMENT_LINK = _todo("the 'Home Page management' nav item")
    COMMUNITY_PARTNERS_MANAGEMENT_LINK = _todo("the 'Community Partners' content-management entry point")
    PARTNER_ENTRY_ROW = _todo("one partner entry row in the Community Partners list")
    PARTNER_ACTIVE_STATUS_TOGGLE = _todo("a partner entry's Active/Inactive (publish/unpublish) control")
    SAVE_BUTTON = _todo("the Community Partners management screen's Save button")

    def open_control_panel_home(self) -> "HomeCommunityPartnersAdminPage":
        self.open(control_panel_url("/group/qatar-chamber"))
        return self

    def navigate_to_community_partners_management(self) -> "HomeCommunityPartnersAdminPage":
        self.click(self.HOME_PAGE_MANAGEMENT_LINK)
        self.click(self.COMMUNITY_PARTNERS_MANAGEMENT_LINK)
        return self

    def partner_entry_count(self) -> int:
        return self.page.locator(self.PARTNER_ENTRY_ROW).count()

    def deactivate_all_partners(self) -> "HomeCommunityPartnersAdminPage":
        """Sets every partner entry's Active Status control to inactive and
        saves. NOT idempotent/parallel-safe on its own — see the module
        docstring's teardown/reactivation warning."""
        rows = self.page.locator(self.PARTNER_ENTRY_ROW)
        for i in range(rows.count()):
            toggle = rows.nth(i).locator(self.PARTNER_ACTIVE_STATUS_TOGGLE)
            if toggle.is_checked():
                toggle.click()
        self.click(self.SAVE_BUTTON)
        return self

    def reactivate_all_partners(self) -> "HomeCommunityPartnersAdminPage":
        """Teardown counterpart of deactivate_all_partners() — restores the
        shared qcdev demo state for every other test that depends on the
        Community Partners section actually rendering."""
        rows = self.page.locator(self.PARTNER_ENTRY_ROW)
        for i in range(rows.count()):
            toggle = rows.nth(i).locator(self.PARTNER_ACTIVE_STATUS_TOGGLE)
            if not toggle.is_checked():
                toggle.click()
        self.click(self.SAVE_BUTTON)
        return self

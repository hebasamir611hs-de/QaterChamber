"""
web/pages/home_strategic_partners/home_strategic_partners_admin_page.py —
HomeStrategicPartnersAdminPage.

PBI 129391 / QC-HOME-015 "Strategic Partners" — no Control_Panel-tagged
cases were handed off for this PBI in this batch (every one of the 23
cases carries Platform=Web only). This file exists only because 8 of those
23 Web-platform cases have their OWN Arrange step needing an authenticated
Site Content Editor session against the Strategic Partners content-
management screen before the Web-platform assertion can run (ADO TC 136233,
136289, 136291, 136294, 136296, 136300, 136302, 136304) — exactly the same
shape as home_community_partners_admin_page.py's TC 135811.

STATUS: BLOCKED, not guessed (2026-08-26) — same, already-documented
project-wide blocker as home_community_partners_admin_page.py /
home_featured_event_admin_page.py (commit 2cbbb4c): TEST_USER / TEST_PASSWORD
are blank in this machine's .env. The anonymous /c/portal/login FORM itself
is reachable and its locators are real/confirmed (see the shared
web/pages/components/cms_login_page.py this Page Object composes), but
nothing PAST login — the Home Page management entry point, the Strategic
Partners content list, and its per-entry Active Status / Start Date / End
Date / Draft-Save / Publish / Unpublish / Delete controls — could be reached
this session, and no Playwright MCP fallback is available in this
environment either.

Every locator below is the literal TODO placeholder string (never a
guessed-but-plausible Liferay selector), same convention as
home_community_partners_admin_page.py / home_featured_event_admin_page.py.

Replace only after confirming the real Strategic Partners content-management
screen live — never mark this file "done" by guessing a plausible-looking
Liferay object/fragment-configuration selector.

IMPORTANT — deactivate_all_partners()/set_partner_end_date()/
set_partner_start_date() are DESTRUCTIVE and NOT parallel-safe/idempotent by
themselves: they mutate the shared qcdev homepage state that TC 136215-136231's
Web-platform assertions depend on if run concurrently (pytest-xdist runs
`-n 3` by default per pytest.ini). Whoever fills in the real locators below
MUST also add a matching restore/teardown call (reactivate_all_partners(),
restore the original End/Start Date, etc.) in each test's teardown/finally,
mirroring home_community_partners_admin_page.py's reactivate_all_partners()
pattern, and should consider running these 8 tests alone
(`pytest -k 136233 or 136289 or ...`) rather than as part of a parallel
full-suite run, until each restore path is confirmed to restore the exact
prior state.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_TODO_PREFIX = "TODO:"


def _todo(what: str) -> str:
    return f"{_TODO_PREFIX} run tools/extract_locators.py (as an authenticated Site Content Editor) against the live Strategic Partners content-management screen and paste the confirmed selector for {what}"


class HomeStrategicPartnersAdminPage(BasePage):
    # ── Unreachable without an authenticated session this run — see docstring ──
    HOME_PAGE_MANAGEMENT_LINK = _todo("the 'Home Page management' nav item")
    STRATEGIC_PARTNERS_MANAGEMENT_LINK = _todo("the 'Strategic Partners' content-management entry point")
    PARTNER_ENTRY_ROW = _todo("one partner entry row in the Strategic Partners list")
    PARTNER_ACTIVE_STATUS_TOGGLE = _todo("a partner entry's Active/Inactive control")
    PARTNER_START_DATE_FIELD = _todo("a partner entry's Start Date field")
    PARTNER_END_DATE_FIELD = _todo("a partner entry's End Date field")
    PARTNER_LOGO_UPLOAD_FIELD = _todo("a partner entry's Logo Image (EN) upload control")
    NEW_PARTNER_BUTTON = _todo("the 'New Partner' / 'Add Entry' button")
    SAVE_BUTTON = _todo("the Strategic Partners management screen's Save button")
    SAVE_AS_DRAFT_BUTTON = _todo("the entry editor's 'Save as Draft' button")
    PUBLISH_BUTTON = _todo("the entry editor's Publish button")
    UNPUBLISH_BUTTON = _todo("an entry's Unpublish control")
    DELETE_BUTTON = _todo("an entry's Delete control")
    STATUS_INDICATOR = _todo("an entry row's Status (Draft/Published) indicator")

    def open_control_panel_home(self) -> "HomeStrategicPartnersAdminPage":
        self.open(control_panel_url("/group/qatar-chamber"))
        return self

    def navigate_to_strategic_partners_management(self) -> "HomeStrategicPartnersAdminPage":
        self.click(self.HOME_PAGE_MANAGEMENT_LINK)
        self.click(self.STRATEGIC_PARTNERS_MANAGEMENT_LINK)
        return self

    def partner_entry_count(self) -> int:
        return self.page.locator(self.PARTNER_ENTRY_ROW).count()

    # ── TC 136233 / TC 136289 — deactivate all / zero active partners ────
    def deactivate_all_partners(self) -> "HomeStrategicPartnersAdminPage":
        """NOT idempotent/parallel-safe on its own — see module docstring's
        teardown/reactivation warning."""
        rows = self.page.locator(self.PARTNER_ENTRY_ROW)
        for i in range(rows.count()):
            toggle = rows.nth(i).locator(self.PARTNER_ACTIVE_STATUS_TOGGLE)
            if toggle.is_checked():
                toggle.click()
        self.click(self.SAVE_BUTTON)
        return self

    def reactivate_all_partners(self) -> "HomeStrategicPartnersAdminPage":
        """Teardown counterpart of deactivate_all_partners()."""
        rows = self.page.locator(self.PARTNER_ENTRY_ROW)
        for i in range(rows.count()):
            toggle = rows.nth(i).locator(self.PARTNER_ACTIVE_STATUS_TOGGLE)
            if not toggle.is_checked():
                toggle.click()
        self.click(self.SAVE_BUTTON)
        return self

    # ── TC 136291 — exactly one active partner ────────────────────────────
    def deactivate_all_but_first_partner(self) -> "HomeStrategicPartnersAdminPage":
        rows = self.page.locator(self.PARTNER_ENTRY_ROW)
        for i in range(1, rows.count()):
            toggle = rows.nth(i).locator(self.PARTNER_ACTIVE_STATUS_TOGGLE)
            if toggle.is_checked():
                toggle.click()
        self.click(self.SAVE_BUTTON)
        return self

    # ── TC 136294 — expired End Date ──────────────────────────────────────
    def set_first_partner_end_date_to_yesterday(self) -> "HomeStrategicPartnersAdminPage":
        row = self.page.locator(self.PARTNER_ENTRY_ROW).first
        row.locator(self.PARTNER_END_DATE_FIELD).fill("__yesterday__")  # TODO: real date-picker interaction
        self.click(self.SAVE_BUTTON)
        return self

    # ── TC 136296 — future Start Date ─────────────────────────────────────
    def set_first_partner_start_date_to_tomorrow(self) -> "HomeStrategicPartnersAdminPage":
        row = self.page.locator(self.PARTNER_ENTRY_ROW).first
        row.locator(self.PARTNER_START_DATE_FIELD).fill("__tomorrow__")  # TODO: real date-picker interaction
        self.click(self.SAVE_BUTTON)
        return self

    # ── TC 136300 — Draft-only entry stays hidden ─────────────────────────
    def create_draft_partner_entry(self) -> "HomeStrategicPartnersAdminPage":
        self.click(self.NEW_PARTNER_BUTTON)
        # TODO: fill Active=True + in-window Start/End Date fields once real
        # locators are confirmed.
        self.click(self.SAVE_AS_DRAFT_BUTTON)
        return self

    # ── TC 136302 — stale cache after a logo-image publish ────────────────
    def publish_first_partner_logo_change(self, image_path: str) -> "HomeStrategicPartnersAdminPage":
        row = self.page.locator(self.PARTNER_ENTRY_ROW).first
        row.locator(self.PARTNER_LOGO_UPLOAD_FIELD).set_input_files(image_path)
        self.click(self.PUBLISH_BUTTON)
        return self

    # ── TC 136304 — unpublish/delete an in-use partner ─────────────────────
    def unpublish_first_partner(self) -> "HomeStrategicPartnersAdminPage":
        row = self.page.locator(self.PARTNER_ENTRY_ROW).first
        row.locator(self.UNPUBLISH_BUTTON).click()
        return self

    def partner_status_text(self, index: int = 0) -> str:
        return self.page.locator(self.PARTNER_ENTRY_ROW).nth(index).locator(self.STATUS_INDICATOR).inner_text()

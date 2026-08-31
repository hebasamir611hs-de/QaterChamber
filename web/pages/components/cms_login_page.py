"""
web/pages/components/cms_login_page.py — CmsLoginPage.

Cross-page, cross-PBI GLOBAL infrastructure component — every Control_Panel
test needs to log in, so this lives in pages/components/ per this project's
component exception (never duplicated into a page folder), mirroring
header_component.py / footer_component.py etc.

Provenance of the locators below (no live login could be exercised THIS
session — see "Known limitation" at the bottom):

  - LOGIN_PATH, USERNAME_INPUT, PASSWORD_INPUT, and SUBMIT_BUTTON were
    RE-CONFIRMED live on 2026-08-24 via a direct Playwright probe against
    https://qcdev.ihorizons.com/c/portal/login (anonymous/public page, no
    credentials needed to view the login FORM itself):

        python tools/extract_locators.py --url https://qcdev.ihorizons.com/c/portal/login
        -> [role] uniq=1  get_by_role("textbox", name="Password")
        -> [role] uniq=1  get_by_role("button", name="Sign In")

    The extractor's role-based harvest does not surface the username/email
    field (it renders with no accessible name/label the harvester's
    heuristic picks up), so its `id` was confirmed directly instead — a
    disclosed, scoped Playwright script (still CLI/shell, not the
    Playwright MCP) confirmed live:
        `#_com_liferay_login_web_portlet_LoginPortlet_login` exists
        `#_com_liferay_login_web_portlet_LoginPortlet_password` exists
        `#_com_liferay_login_web_portlet_LoginPortlet_loginForm` exists,
            with a `button[type="submit"]` inside it reading "Sign In"

    SUBMIT_BUTTON deliberately scopes by the stable form id + type=submit,
    not the button's own id — this project's git history (commit 2cbbb4c,
    2026-08-18) already found the button's own id carries a randomized
    suffix that changes between page loads.

  - LOGIN_SUCCESS_INDICATOR (`nav[aria-label="Control Menu"]`) is carried
    forward from that SAME prior, real, git-documented confirmation
    (commit 2cbbb4c, 2026-08-18: "confirmed present after a real
    TEST_USER/TEST_PASSWORD login and absent on the anonymous login page"),
    not re-derived fresh here.

Known limitation (2026-08-24, this session): TEST_USER / TEST_PASSWORD /
CONTROL_PANEL_URL are all unset in this machine's .env. This session could
reach and read the anonymous login FORM itself (confirmed live, above) but
could NOT submit a real login or re-observe LOGIN_SUCCESS_INDICATOR
first-hand — no Playwright MCP fallback is available in this environment
either. Every Control_Panel test that needs to actually authenticate is
therefore gated with a runtime `pytest.skip` until real credentials exist
(see test_home_featured_event_control_panel.py). CONTROL_PANEL_URL has been
set to the same host as WEB_BASE_URL (https://qcdev.ihorizons.com) in .env,
restoring the value this project's own git history already confirmed live
(commit 2cbbb4c) — TEST_USER/TEST_PASSWORD were left untouched (never
invent credentials).
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url


class CmsLoginPage(BasePage):
    LOGIN_PATH = "/c/portal/login"
    USERNAME_INPUT = "#_com_liferay_login_web_portlet_LoginPortlet_login"
    PASSWORD_INPUT = "#_com_liferay_login_web_portlet_LoginPortlet_password"
    SUBMIT_BUTTON = '#_com_liferay_login_web_portlet_LoginPortlet_loginForm button[type="submit"]'
    LOGIN_SUCCESS_INDICATOR = 'nav[aria-label="Control Menu"]'  # admin toolbar, authenticated-only

    def open_login(self) -> "CmsLoginPage":
        self.open(control_panel_url(self.LOGIN_PATH))
        return self

    def login(self, username: str, password: str) -> "CmsLoginPage":
        self.type(self.USERNAME_INPUT, username)
        self.type(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")
        return self

    def login_succeeded(self) -> bool:
        return self.is_visible(self.LOGIN_SUCCESS_INDICATOR)

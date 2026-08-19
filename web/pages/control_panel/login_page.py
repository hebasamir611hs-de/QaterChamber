"""
web/pages/control_panel/login_page.py — CmsLoginPage.

Shared Liferay Control Panel login flow — needed by any control_panel-
platform test that must perform (not just silently reuse) a login. ADO Test
Case 134658's Step 1 explicitly asserts "Login succeeds with the restricted
role" — login itself is part of what's being verified, so the test cannot
start pre-authenticated via a cached storageState; it has to drive the real
flow through this Page Object.

STATUS: PARTIALLY VERIFIED (2026-08-18). LOGIN_PATH is confirmed — QA Lead
opened https://qcdev.ihorizons.com/c/portal/login directly against the
restricted test account's expected entry point and confirmed it renders a
plain username/password form, not an AD SSO/ADFS redirect. That resolves
the open question flagged below from background.md.

STATUS UPDATE (2026-08-18, later same day): all 4 field-level locators are
now VERIFIED against the live login form via Playwright (real browser
session, not the stateless CLI extractor — see note below on why).
  - USERNAME_INPUT / PASSWORD_INPUT / SUBMIT_BUTTON were read directly off
    the rendered Liferay LoginPortlet DOM (input ids + form id).
  - SUBMIT_BUTTON deliberately does NOT use the Sign In button's own id —
    that id has a randomized suffix that changed between two page loads in
    the same session (_...rxme vs _...buut). The selector instead scopes by
    type=submit within the login form's stable id
    (_com_liferay_login_web_portlet_LoginPortlet_loginForm), which held
    across reloads.
  - LOGIN_SUCCESS_INDICATOR is the Liferay admin Control Menu nav
    (aria-label="Control Menu") — it only renders in the DOM for an
    authenticated backend/admin session, confirmed present after a real
    TEST_USER/TEST_PASSWORD login and absent on the anonymous login page.

Root cause of the earlier license_activation blocker, now understood: the
"developer mode connection limit" reset is session/cookie-scoped, not
server-wide. A stateless curl request (or a fresh unauthenticated
Playwright context) always re-trips it; only a persistent browser session
that clicks the reset link and then continues navigating in that same
session gets past it. Submitting the login form itself was observed to
trip the limit once too — a second reset-then-retry in the same session
got past that as well. This means the automated suite will very likely hit
this same wall when it runs standalone against qcdev; that is a real,
unresolved dev-mode connection-limit issue on the qcdev instance itself
and needs a fix from whoever administers it, not a workaround in this
Page Object.

  - tools/save_auth.py's login() is still the generic scaffold — it targets
    WEB_BASE_URL with a #username/#password form, was never adapted for
    this project's real flow, and points at the PUBLIC site, not
    CONTROL_PANEL_URL.
  - .claude/context/active/background.md states admin/internal users
    authenticate via AD SSO (ADFS) — that turned out NOT to apply to this
    entry point.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url


class CmsLoginPage(BasePage):
    LOGIN_PATH = "/c/portal/login"  # confirmed live 2026-08-18 — plain form, not SSO
    USERNAME_INPUT = "#_com_liferay_login_web_portlet_LoginPortlet_login"
    PASSWORD_INPUT = "#_com_liferay_login_web_portlet_LoginPortlet_password"
    SUBMIT_BUTTON = (
        '#_com_liferay_login_web_portlet_LoginPortlet_loginForm button[type="submit"]'
    )
    LOGIN_SUCCESS_INDICATOR = 'nav[aria-label="Control Menu"]'  # admin toolbar, authenticated-only

    def open_login(self) -> "CmsLoginPage":
        self.open(control_panel_url(self.LOGIN_PATH))
        return self

    def login(self, username: str, password: str) -> "CmsLoginPage":
        self.type(self.USERNAME_INPUT, username)
        self.type(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
        self.wait_for(self.LOGIN_SUCCESS_INDICATOR)
        return self

    def login_succeeded(self) -> bool:
        return self.is_visible(self.LOGIN_SUCCESS_INDICATOR)

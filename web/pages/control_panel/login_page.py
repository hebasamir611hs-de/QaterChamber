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

The field-level locators (USERNAME_INPUT / PASSWORD_INPUT / SUBMIT_BUTTON /
LOGIN_SUCCESS_INDICATOR) are still UNVERIFIED — confirming the page loads a
plain form is not the same as knowing its real selectors. Nobody has run
tools/extract_locators.py against this page yet:
  - tools/save_auth.py's login() is still the generic scaffold — it targets
    WEB_BASE_URL with a #username/#password form, was never adapted for
    this project's real flow, and points at the PUBLIC site, not
    CONTROL_PANEL_URL.
  - .claude/context/active/background.md states admin/internal users
    authenticate via AD SSO (ADFS) — that turned out NOT to apply to this
    entry point, but re-check per role if a different restricted account
    ends up routed differently.

Locator extraction attempted 2026-08-18 and BLOCKED, not completed: qcdev
is currently serving a Liferay "developer mode connection limit exceeded"
error and server-side redirects /c/portal/login to /c/portal/license_activation.
No login form is being rendered at all in this environment state, so none
of the 4 locators could be extracted or verified, and login could not be
exercised to observe LOGIN_SUCCESS_INDICATOR. This is an infrastructure/
license-limit issue on qcdev itself, not a locator-discovery gap - retry
tools/extract_locators.py once qcdev admin resets the connection limit
(a reset link surfaced in the error page but the token is session-specific,
so a fresh one will be needed at retry time).

Every locator below is the literal placeholder string — never a guessed-but-
plausible selector — precisely so nobody mistakes an unverified value for a
confirmed one. Replace only after confirming the real flow live.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_UNVERIFIED = "TODO: run tools/extract_locators.py against the live login form and paste the confirmed selector here"


class CmsLoginPage(BasePage):
    LOGIN_PATH = "/c/portal/login"  # confirmed live 2026-08-18 — plain form, not SSO
    USERNAME_INPUT = _UNVERIFIED
    PASSWORD_INPUT = _UNVERIFIED
    SUBMIT_BUTTON = _UNVERIFIED
    LOGIN_SUCCESS_INDICATOR = _UNVERIFIED  # visible ONLY after a real successful login

    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"CmsLoginPage.{name} is unverified — the real Control Panel auth flow "
                f"(plain form vs AD SSO) has not been confirmed against live qcdev. "
                f"See this file's module docstring before running any control_panel test."
            )

    def open_login(self) -> "CmsLoginPage":
        self._require_verified(self.LOGIN_PATH, "LOGIN_PATH")
        self.open(control_panel_url(self.LOGIN_PATH))
        return self

    def login(self, username: str, password: str) -> "CmsLoginPage":
        for value, name in (
            (self.USERNAME_INPUT, "USERNAME_INPUT"),
            (self.PASSWORD_INPUT, "PASSWORD_INPUT"),
            (self.SUBMIT_BUTTON, "SUBMIT_BUTTON"),
            (self.LOGIN_SUCCESS_INDICATOR, "LOGIN_SUCCESS_INDICATOR"),
        ):
            self._require_verified(value, name)
        self.type(self.USERNAME_INPUT, username)
        self.type(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
        self.wait_for(self.LOGIN_SUCCESS_INDICATOR)
        return self

    def login_succeeded(self) -> bool:
        self._require_verified(self.LOGIN_SUCCESS_INDICATOR, "LOGIN_SUCCESS_INDICATOR")
        return self.is_visible(self.LOGIN_SUCCESS_INDICATOR)

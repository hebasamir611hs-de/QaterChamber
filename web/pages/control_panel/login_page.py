"""
web/pages/control_panel/login_page.py — CmsLoginPage.

Shared Liferay Control Panel login flow — needed by any control_panel-
platform test that must perform (not just silently reuse) a login. ADO Test
Case 134658's Step 1 explicitly asserts "Login succeeds with the restricted
role" — login itself is part of what's being verified, so the test cannot
start pre-authenticated via a cached storageState; it has to drive the real
flow through this Page Object.

STATUS: UNVERIFIED / BLOCKED. Nobody has automated Control Panel login in
this framework yet:
  - tools/save_auth.py's login() is still the generic scaffold — it targets
    WEB_BASE_URL with a #username/#password form, was never adapted for
    this project's real flow, and points at the PUBLIC site, not
    CONTROL_PANEL_URL. Admin login is very likely a different flow entirely.
  - .claude/context/active/background.md states admin/internal users
    authenticate via AD SSO (ADFS) — "passwords not managed in Liferay for
    SSO users". If that also applies to the restricted test account, this
    may not be a plain username/password form at all, and this Page
    Object's shape (and possibly save_auth.py's) needs to change once
    that's confirmed against the live instance.

Every locator below is the literal placeholder string — never a guessed-but-
plausible selector — precisely so nobody mistakes an unverified value for a
confirmed one. Replace only after confirming the real flow live.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_UNVERIFIED = "TODO: confirm the real Control Panel login flow (plain form vs AD SSO redirect) against live qcdev, then replace"


class CmsLoginPage(BasePage):
    LOGIN_PATH = _UNVERIFIED
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

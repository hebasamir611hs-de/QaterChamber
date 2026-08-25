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

STATUS UPDATE (2026-08-25, QA sub-agent diagnostic, live against qcdev):
resolved the "/c/portal/login renders Coming Soon" blocker reported this
session. Two throwaway Playwright scripts (fresh context vs. authenticated
context, both hitting control_panel_url("/c/portal/login") directly)
confirmed:
  - Fresh/unauthenticated context: LOGIN_PATH redirects (302) to
    /home?...LoginPortlet...&mvcRenderCommandName=/login/login and renders
    the REAL login form (USERNAME_INPUT/PASSWORD_INPUT both present,
    confirmed by screenshot). LOGIN_PATH itself is NOT broken and has not
    moved — no routing regression.
  - Login via that form succeeds normally: right after submit,
    LOGIN_SUCCESS_INDICATOR (Control Menu) AND the Product Menu toggle are
    BOTH present (confirmed screenshot + locator counts).
  - Hitting LOGIN_PATH again in that SAME already-authenticated context
    redirects to an unrelated, unbuilt page (/documents/d/qatar-chamber/
    mandala, title "Coming Soon") — but the Control Menu and Product Menu
    toggle are STILL present in that response. This is Liferay's normal
    "you're already logged in, here's your default redirect target"
    behavior landing on a page that happens not to be built yet on qcdev —
    it is NOT a logged-out state and NOT evidence the login flow is broken.
    Earlier screenshot evidence reading this as a blocker was mistaking an
    authenticated redirect target for a login failure.
  - Conclusion: do not re-hit LOGIN_PATH from an already-authenticated
    context (org_structure_admin_page.py's open_departments_list() already
    avoids this by checking CONTENT_DATA_MENU_ITEM/PRODUCT_MENU_TOGGLE
    before ever calling login() again). LOGIN_SUCCESS_INDICATOR is widened
    below (OR'd with the Product Menu toggle) purely for robustness against
    render-order timing between the two nav elements — not because either
    one was observed missing after a genuine login.

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
    # OR'd with the Product Menu toggle (2026-08-25) — both were confirmed
    # present together right after a real login, but ORing guards against a
    # render-order race between the two nav elements rather than relying on
    # either alone. See STATUS UPDATE above.
    LOGIN_SUCCESS_INDICATOR = 'nav[aria-label="Control Menu"], [data-qa-id="productMenu"]'

    def open_login(self) -> "CmsLoginPage":
        self.open(control_panel_url(self.LOGIN_PATH))
        return self

    def login(self, username: str, password: str) -> "CmsLoginPage":
        self.type(self.USERNAME_INPUT, username)
        self.type(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
        # .first: LOGIN_SUCCESS_INDICATOR legitimately matches BOTH the
        # Control Menu nav AND the Product Menu toggle once logged in
        # (confirmed live 2026-08-25) — BasePage.wait_for()'s bare
        # page.locator(...).wait_for() enforces Playwright strict mode and
        # throws on a 2-element match, so it is called directly here rather
        # than through the generic wrapper (mirrors the same fix already
        # applied in core/web/session_guard.py's reauthenticate()).
        self.page.locator(self.LOGIN_SUCCESS_INDICATOR).first.wait_for(state="visible", timeout=10000)
        return self

    def login_succeeded(self) -> bool:
        try:
            return self.page.locator(self.LOGIN_SUCCESS_INDICATOR).first.is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's never-throws contract
            return False

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

Merged 2026-08-31 with web/pages/control_panel/login_page.py, a duplicate
CmsLoginPage that appeared in a separate control_panel/ tree after a
git merge — standards.md's Automation Structure section already re-confirmed
(2026-08-19) that a separate control_panel/ tree was tried and rejected, so
the duplicate file was removed and its importers repointed here instead of
keeping two. That file carried real, live-tested login diagnostics this one
didn't have first-hand (2026-08-18 and 2026-08-25 sessions against qcdev),
folded into the login()/login_succeeded() logic below:
  - The Sign In button's own id carries a randomized suffix that changes
    between page loads (confirmed two loads, same session: `_...rxme` vs
    `_...buut`) — SUBMIT_BUTTON deliberately scopes by the login form's
    stable id + type=submit instead, not the button's own id.
  - LOGIN_SUCCESS_INDICATOR is OR'd with the Product Menu toggle
    (`[data-qa-id="productMenu"]`) purely for robustness against a
    render-order race between the two nav elements — both were confirmed
    present together right after a real login, not because either one was
    observed missing.
  - Re-hitting LOGIN_PATH from an already-authenticated context redirects to
    an unrelated, unbuilt page ("Coming Soon") while the Control
    Menu/Product Menu toggle stay present — Liferay's normal
    already-logged-in redirect landing on a page qcdev hasn't built yet, not
    a logged-out state. Callers should check login_succeeded() before
    calling login() again rather than assume a fresh call is always safe.
  - Because LOGIN_SUCCESS_INDICATOR can legitimately match both nav elements
    at once, `.first` is required — a bare `page.locator(...).wait_for()`
    enforces Playwright strict mode and throws on a 2-element match.
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
    # CORRECTED 2026-09-28 — this was ADMIN-ONLY and silently broke every
    # non-privileged role login. The previous indicator was
    # `nav[aria-label="Control Menu"], [data-qa-id="productMenu"]`, chosen in
    # 2026-08 when the only account available was the super-admin. The
    # Control Menu is a staff toolbar that Liferay renders only for users
    # with admin-level permissions, so `login()` timed out after a perfectly
    # successful sign-in for anyone else.
    #
    # Measured live 2026-09-28, immediately after a real login on each of the
    # three role accounts:
    #
    #   role                   signedIn  body.signed-in  Control Menu
    #   Site Content Editor    True      True            True
    #   Site Content Author    True      True            FALSE
    #   Site Member (no role)  True      True            FALSE
    #
    # `body.signed-in` is the only one true for every role, so it is the
    # success signal. It is also the right *semantic* signal: the question
    # login() asks is "is a session established", not "is this user an admin".
    LOGIN_SUCCESS_INDICATOR = "body.signed-in"

    # Kept separately because it IS a real, useful signal — just of privilege,
    # not of login. Use has_admin_toolbar() to assert that a role does or does
    # not get the staff toolbar; never to decide whether login worked.
    ADMIN_TOOLBAR_INDICATOR = 'nav[aria-label="Control Menu"], [data-qa-id="productMenu"]'

    def open_login(self) -> "CmsLoginPage":
        self.open(control_panel_url(self.LOGIN_PATH))
        return self

    def login(self, username: str, password: str) -> "CmsLoginPage":
        """Sign in and wait for a session to actually exist. Works for every
        role, privileged or not — see LOGIN_SUCCESS_INDICATOR's note.

        `state="attached"` rather than `"visible"`: the signal is a class on
        <body>, which is a layout element Playwright does not consider
        "visible" in the usual sense. `.first` is kept because BasePage's
        bare locator wait enforces strict mode."""
        self.type(self.USERNAME_INPUT, username)
        self.type(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
        self.page.locator(self.LOGIN_SUCCESS_INDICATOR).first.wait_for(
            state="attached", timeout=15000
        )
        return self

    def login_succeeded(self) -> bool:
        """True when a session exists — for any role. Never raises."""
        try:
            return self.page.locator(self.LOGIN_SUCCESS_INDICATOR).count() > 0
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's never-throws contract
            return False

    def has_admin_toolbar(self) -> bool:
        """True when this session renders Liferay's staff toolbar — a
        PRIVILEGE check, not a login check. Confirmed live 2026-09-28: true
        for Site Content Editor, false for Site Content Author and for a
        site-member-only account. Never raises."""
        try:
            return self.page.locator(self.ADMIN_TOOLBAR_INDICATOR).count() > 0
        except Exception:  # noqa: BLE001
            return False

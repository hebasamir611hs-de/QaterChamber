"""
cms/pages/control_panel/login_page.py — CmsLoginPage.

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

from urllib.parse import quote

from core.web.base_page import BasePage
from core.web.session_guard import _SESSION_OWNER, session_owner, set_session_owner  # noqa: F401
from config.settings import control_panel_url, settings

# `_SESSION_OWNER` (which account each browser page is signed in as) now lives
# in core/web/session_guard.py so reauthenticate() re-logs in as the session's
# owner. Re-exported above as the SAME object: `login_page._SESSION_OWNER[...]`
# in existing callers keeps working. A page nobody signed in on resolves to
# the account its context was built for (session_owner()).


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
    #
    # SUPERSEDED 2026-09-30 — the Control Menu / Product Menu pair above is a
    # PRIVILEGE signal, not a login signal. Liferay renders the staff toolbar
    # only for admin-level users, so login() timed out after a perfectly good
    # sign-in for every other role. Measured live 2026-09-28 (see
    # web/pages/components/cms_login_page.py, which got this fix first):
    #
    #   role                   signedIn  body.signed-in  Control Menu
    #   Site Content Editor    True      True            True
    #   Site Content Author    True      True            FALSE
    #   Site Member (no role)  True      True            FALSE
    #
    # Re-confirmed 2026-09-30 for TEST_USER: body.signed-in, Control Menu and
    # Product Menu all present, so admin callers see no change.
    # `body.signed-in` is the one signal true for every role.
    LOGIN_SUCCESS_INDICATOR = "body.signed-in"

    # Kept separately because it IS a real signal — of privilege. Use
    # has_admin_toolbar() to assert a role does or does not get the staff
    # toolbar; never to decide whether login worked.
    ADMIN_TOOLBAR_INDICATOR = 'nav[aria-label="Control Menu"], [data-qa-id="productMenu"]'

    # HEALED 2026-09-15 (triage of 26 Functional-Low Control_Panel failures,
    # tc_133580 and siblings in test_board_of_directors_control_panel.py —
    # "no live row found for category 'Board Member'" / TimeoutError on
    # role=link[name="Edit"]). Root cause, confirmed live via Playwright MCP
    # against qcdev with the real TEST_USER account: the account's Liferay
    # profile had its OWN persisted UI-language preference set to Arabic
    # (independent of the GUEST_LANGUAGE_ID=en_US cookie already baked into
    # .auth/state.json — that cookie only governs the ANONYMOUS/guest
    # render, not an authenticated user's own account preference, which
    # wins once logged in). Every English-text locator in this project
    # (`role=link[name="Edit"]`, "Preview", "Unpublish", "Delete", etc.)
    # then matched zero elements because the admin surface was actually
    # rendering "تحرير"/"معاينة"/"إلغاء النشر"/"حذف".
    #
    # Confirmed live this session that Liferay's own language switcher
    # (visible on the login page as an "AR" link) hits exactly this
    # `/c/portal/update_language?languageId=<id>&redirect=<url>` endpoint —
    # the same call "My Account > Language" makes. Hitting it with
    # languageId=en_US while authenticated does not just pin the current
    # browser session to English (a URL /en/ prefix on one request does
    # that, but only for that JSESSIONID and only until it expires); it
    # PERSISTS the account's own language preference in Liferay's user
    # profile. Proven live by clearing all cookies, logging back in via the
    # plain (no /en/ prefix) LOGIN_PATH as a completely fresh session, and
    # confirming manage-board-member still rendered English with an "Edit"
    # (not "تحرير") link — i.e. the fix survives a brand-new session, not
    # just the one that called it.
    #
    # Calling this unconditionally on every login() — rather than detecting
    # the rendered language first — is deliberate: it is one cheap extra
    # navigation, has no race condition to get wrong, and makes every
    # automated login deterministic regardless of what a prior manual or
    # automated session last left the shared TEST_USER account's language
    # preference at (this project's test accounts are shared, not
    # per-worker, so a manual QA session clicking "AR" to eyeball the
    # Arabic site can otherwise silently flip every subsequent automated
    # run to Arabic until someone notices).
    UPDATE_LANGUAGE_PATH = "/c/portal/update_language"
    ENGLISH_LANGUAGE_ID = "en_US"
    POST_LOGIN_REDIRECT_PATH = "/home"

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
        self.page.locator(self.LOGIN_SUCCESS_INDICATOR).first.wait_for(state="attached", timeout=15000)
        # Recorded on every successful login (2026-10-13) so a mid-test
        # session drop is repaired as THIS account, not TEST_USER.
        set_session_owner(self.page, username)
        self._force_english_locale()
        return self

    def _force_english_locale(self) -> None:
        """Forces (and persists) the just-authenticated account's UI
        language to English — see the HEALED 2026-09-15 note above. Runs
        AFTER LOGIN_SUCCESS_INDICATOR is already confirmed visible, so this
        is always hitting update_language as an authenticated request (an
        anonymous hit would only move the GUEST_LANGUAGE_ID cookie, not the
        account's own persisted preference — confirmed by that same live
        investigation). Re-confirms LOGIN_SUCCESS_INDICATOR after the
        redirect lands so a broken/blocked update_language call surfaces
        immediately here, at login time, rather than as a confusing
        Arabic-locator failure deep inside an unrelated test later.
        """
        redirect_url = quote(self.POST_LOGIN_REDIRECT_PATH, safe="")
        self.open(
            control_panel_url(
                f"{self.UPDATE_LANGUAGE_PATH}?languageId={self.ENGLISH_LANGUAGE_ID}&redirect={redirect_url}"
            )
        )
        self.page.locator(self.LOGIN_SUCCESS_INDICATOR).first.wait_for(state="attached", timeout=15000)

    def login_succeeded(self) -> bool:
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

    LOGOUT_PATH = "/c/portal/logout"

    def ensure_signed_in_as(
        self, email: str | None = None, password: str | None = None, landing_url: str | None = None
    ) -> "CmsLoginPage":
        """Make the session belong to `email` (TEST_USER when omitted), then
        land on `landing_url`.

        ADDED 2026-09-30. The Page Objects that call this used to log in only
        when the admin toolbar was missing. The default `page` fixture
        pre-loads TEST_USER's storageState, so the toolbar was always there
        and a role test's explicit credentials were never used — its "Site
        Content Author" steps ran as super-admin. This switches accounts only
        when the requested account differs from the page's current one.

        CACHED (2026-10-13): the switch first tries this worker's cached
        session for that account (core.web.browser.load_cached_session, a
        cookie swap from a storageState file younger than 25 min) and only
        logs in for real when there is none -- after which the new session is
        cached for the next test. A cached session that turns out dead is
        repaired by session_guard as the same account (the owner is recorded
        before the first navigation)."""
        from core.web.browser import load_cached_session, save_session_cache

        user = email or settings.test_user
        pwd = password or settings.test_password
        landed = False
        if user != session_owner(self.page):
            # Drop this context's cookies instead of a server-side sign-out
            # (2026-10-12): the `page` fixture carries TEST_USER's SHARED
            # storageState session, and a server-side logout invalidates that
            # session for every other context, worker and tool using
            # .auth/state.json — it signed out the module baselines mid-run and
            # stranded the live GM record in Unpublished twice.
            self.page.context.clear_cookies()
            if load_cached_session(self.page.context, user):
                set_session_owner(self.page, user)
                self.open(landing_url or control_panel_url(self.POST_LOGIN_REDIRECT_PATH))
                landed = bool(landing_url)
                if not self.login_succeeded():
                    self.page.context.clear_cookies()
                    self.open_login().login(user, pwd)
                    save_session_cache(self.page.context, user)
                    landed = False
            else:
                self.open_login().login(user, pwd)
                save_session_cache(self.page.context, user)
            set_session_owner(self.page, user)
        if landing_url and not landed:
            self.open(landing_url)
        if not self.login_succeeded():
            # Only type into a form that is really there (2026-10-12). On a
            # fresh page with no landing_url, login_succeeded() reads
            # about:blank and is always False; an already-signed-in session
            # is then redirected AWAY from LOGIN_PATH (see the 2026-08-25
            # note above), and typing into the missing username field was a
            # 30 s fill/clear timeout (tools/restore_singleton.py --dry-run).
            self.open_login()
            if self._login_form_rendered():
                self.login(user, pwd)
                save_session_cache(self.page.context, user)
            if landing_url:
                self.open(landing_url)
        return self

    def _login_form_rendered(self, timeout_ms: int = 15000) -> bool:
        try:
            self.page.locator(self.USERNAME_INPUT).first.wait_for(state="visible", timeout=timeout_ms)
            return True
        except Exception:  # noqa: BLE001 -- redirected away: already signed in
            return False

    def login_form_visible(self) -> bool:
        """True if the real Liferay LoginPortlet username field is
        currently rendered — used by callers that need to confirm an
        unauthenticated/denied navigation actually landed back on login,
        without reaching into this Page Object's own locator constants."""
        return self.is_visible(self.USERNAME_INPUT)

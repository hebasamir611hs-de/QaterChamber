"""
core/web/session_guard.py — global re-authentication guard for the Liferay
Control Panel's dropped-session behavior on qcdev.

Root cause (confirmed live, 2026-08-24): the qcdev dev instance's session
drops roughly every ~30 seconds under sustained automated traffic. A
license-gate reset (core/web/license_gate.py) alone is not enough once that
happens — clicking the reset link can land back on the Control Panel LOGIN
FORM instead of the originally requested page, because the session backing
that reset was itself invalidated.

Per cms/pages/control_panel/login_page.py's own history, submitting the
login form can itself re-trip the connection limit once — so this retries
the reset+login pair, not just a single login attempt.

SECOND failure mode (confirmed live, 2026-09-17): an expired/invalid
session (e.g. a stale `.auth/state.json` reused across a long gap, no
sustained traffic required at all) hitting a Control Panel URL — e.g.
Object Authoring's `manage-<slug>?editEntry=...` — does NOT render a login
form and does NOT trip the license gate. It silently falls through to the
public site's own generic "Coming Soon" placeholder (or, on some paths,
the plain public Home page) instead, because that URL happens to also
resolve on the public-facing side of the same Liferay instance. Neither
`is_login_form_showing()` nor `license_gate.is_gate_showing()` recognizes
this render, so `reauthenticate()` previously no-op'd and every caller
waiting on admin-only content (e.g. `object_authoring_page.py`'s
`CANCEL_AND_ADD_NEW_LINK` wait) timed out with no recovery attempted at
all — this had been misdiagnosed across multiple sessions as a qcdev
connection-limit/concurrency problem before being isolated with a direct,
single-request, no-concurrency repro. `is_dead_session()` / the dead-session
branch inside `reauthenticate()` below close this gap by first navigating to
the real login URL (forcing the form to render) before the existing
fill/submit/verify loop runs — scoped to known Control-Panel-only paths so
it can never misfire on a legitimately anonymous public-web page load.

This is a session symptom, not a fix for the underlying qcdev-side limit
(that needs whoever administers the qcdev instance — see license_gate.py's
docstring). This module only makes the automated suite recover from it
automatically instead of failing every test that outlives one ~30s window,
or that reuses a session which had simply gone stale between runs.

Wired into the wrapper layer (core/web/base_page.py) alongside
license_gate.py, not into any test or Page Object — every navigation in the
suite is covered by construction.

HEALED 2026-09-15 (triage of a full-run regression on
test_board_of_directors_control_panel.py: 26 Functional-Low Control_Panel
failures, the SAME "no live row found" / role=link[name="Edit"] timeout
symptom the 2026-09-15 fix in cms/pages/control_panel/login_page.py's
CmsLoginPage.login() already healed once — confirmed live by the QA
Manager that the shared TEST_USER account's Liferay UI-language preference
had flipped back to Arabic mid-run, on a SERIAL (`-n 0`, no xdist) run
where the EARLY tests in the run genuinely rendered English and only LATER
tests in that same run saw Arabic).

Root cause: `reauthenticate()` below is the ONLY OTHER code path in this
project that submits the Liferay login form — and it is wired into every
single `BasePage.open()/click()/type()/wait_for()/is_visible()/
click_iframe()` call (see this module's own docstring above and
base_page.py's import of `reauthenticate`), firing automatically whenever
`is_login_form_showing()` is true, i.e. whenever qcdev's own ~30s
session-drop-under-load (documented above) knocks a test back to the login
form mid-run. Until this fix, that path re-logged-in with a bare form
submit and returned straight to `target_url` WITHOUT ever re-asserting
English — the one asymmetry between this path and CmsLoginPage.login()
(which now calls `_force_english_locale()` unconditionally after every
login). A 26-test serial Control_Panel run realistically spans several
minutes under real network/DOM latency, comfortably enough real time for
qcdev's documented ~30s session-drop window to fire at least once — so
`reauthenticate()` firing mid-run, silently, without the English-forcing
step, was a near-certainty for any run of this length, not an edge case.

Live-verified before this fix (Playwright MCP, qcdev, TEST_USER):
  - A completely clean-cookie, single plain-form login (mirroring exactly
    what `reauthenticate()` below does) DOES render English immediately
    after, as long as the account's OWN persisted Liferay profile
    preference is already English at that moment — confirming the
    account-level persistence CmsLoginPage.login()'s own docstring
    describes is real.
  - A stale `GUEST_LANGUAGE_ID=ar_SA` cookie carried into a plain login
    (no explicit `update_language` call) DOES render the immediate
    post-login redirect in Arabic — confirming the guest cookie can win at
    least at that moment, i.e. `reauthenticate()`'s bare re-login is not
    reliably immune to whatever locale state (cookie- or account-level) is
    in effect at the moment qcdev drops the session and this path fires —
    unlike CmsLoginPage.login(), which forces it explicitly every time
    regardless of ambient state.
The fix mirrors `_force_english_locale()`'s exact mechanism (same
`update_language` endpoint, same re-confirm-success-indicator-after
pattern) directly in this module rather than importing CmsLoginPage, to
preserve the existing no-circular-import discipline documented below.
"""

import weakref

from core.utils.logger import get_logger
from config.settings import CMS_ROLE_CREDENTIALS, control_panel_url, settings

logger = get_logger("session_guard")

# Which account each browser page is signed in as. Moved here from
# cms/pages/control_panel/login_page.py (2026-10-13) so reauthenticate() can
# re-login as the session's OWNER; login_page re-exports this same object, so
# `login_page._SESSION_OWNER[...]` keeps working for existing callers.
_SESSION_OWNER: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()

_UNSET = object()


def set_session_owner(page, email: str | None) -> None:
    """Record that `page` is now signed in as `email` (None: signed out)."""
    if email:
        _SESSION_OWNER[page] = email
    else:
        _SESSION_OWNER.pop(page, None)


def sign_out_locally(page) -> None:
    """Sign `page`'s context out WITHOUT a server-side logout: drop its
    cookies and record it as having no owner, so reauthenticate() does not
    quietly sign it back in as anyone. The shared storageState session other
    contexts/workers/tools carry stays alive (2026-10-12 incident)."""
    from core.web.browser import track_context_session  # local import: keep module load light

    page.context.clear_cookies()
    _SESSION_OWNER.pop(page, None)
    track_context_session(page.context, None, None)


def session_owner(page, default=_UNSET):
    """The account `page` is signed in as: the last recorded sign-in on the
    page, else the account its context was built for (core.web.browser),
    else TEST_USER for a context that factory did not build. A context built
    logged-out on purpose has no owner (None) until someone signs in on it."""
    owner = _SESSION_OWNER.get(page)
    if owner:
        return owner
    from core.web.browser import context_session  # local import: keep module load light

    try:
        info = context_session(page.context)
    except Exception:  # noqa: BLE001
        info = None
    if info is not None:
        return info.get("account")
    return settings.test_user if default is _UNSET else default


def credentials_for(email: str | None) -> tuple[str, str] | None:
    """(email, password) for TEST_USER or a configured CMS role account;
    None for anything else -- never a fallback to TEST_USER."""
    if not email:
        return None
    if email == settings.test_user and settings.test_password:
        return settings.test_user, settings.test_password
    for role_email, password in CMS_ROLE_CREDENTIALS.values():
        if role_email and role_email == email and password:
            return role_email, password
    return None

# Liferay's login portlet — same selectors as
# cms/pages/control_panel/login_page.py's CmsLoginPage, verified live
# 2026-08-18. Kept as plain strings here (not an import of CmsLoginPage) to
# avoid a circular import: CmsLoginPage extends BasePage, which is where
# this guard is wired in.
USERNAME_INPUT = "#_com_liferay_login_web_portlet_LoginPortlet_login"
PASSWORD_INPUT = "#_com_liferay_login_web_portlet_LoginPortlet_password"
SUBMIT_BUTTON = (
    '#_com_liferay_login_web_portlet_LoginPortlet_loginForm button[type="submit"]'
)
# OR'd with the Product Menu toggle (2026-08-25) — see
# cms/pages/control_panel/login_page.py's STATUS UPDATE (2026-08-25) for the
# live evidence: both render together after a real login, ORing only guards
# against a render-order race between the two nav elements.
#
# SUPERSEDED 2026-09-30 — mirrors CmsLoginPage.LOGIN_SUCCESS_INDICATOR, which
# moved to `body.signed-in`. The toolbar pair only renders for admin-level
# users, so with the old value is_dead_session() read every signed-in
# NON-admin role (Site Content Author, Content Contributor, Site Member) on a
# manage-<slug> URL as a dead session, and reauthenticate() then silently
# signed the test back in as TEST_USER — every role test ran as admin from
# its first navigation on.
LOGIN_SUCCESS_INDICATOR = "body.signed-in"

# Path markers for URLs that ONLY exist inside the Control Panel / Object
# Authoring surface (never on the public-facing site) — used to scope
# is_dead_session() so it never misfires on a legitimately anonymous
# public-web page load, which never shows Control Menu/Product Menu
# regardless of session state, by design. Deliberately excludes the bare
# "/home" path: confirmed live 2026-09-17 that path alone resolves
# ambiguously to the PUBLIC home page when the session is dead, so it is
# not a reliable Control-Panel-only signal the way "/en/home" (the
# locale-forced admin redirect target used across this suite's Page
# Objects) is.
_CONTROL_PANEL_URL_MARKERS = (
    "/web/qatar-chamber/manage-",
    "/object-authoring",
    "/en/home",
    "/group/control_panel",
)


def _is_control_panel_url(url: str) -> bool:
    return any(marker in (url or "") for marker in _CONTROL_PANEL_URL_MARKERS)


# Mirrors cms/pages/control_panel/login_page.py's CmsLoginPage constants of
# the same name exactly — kept as a local duplicate (not an import) for the
# same no-circular-import reason as the selectors above. English-only: this
# NEVER selects/forces Arabic, only re-asserts English — same constraint
# CmsLoginPage.login() already honors.
UPDATE_LANGUAGE_PATH = "/c/portal/update_language"
ENGLISH_LANGUAGE_ID = "en_US"
POST_LOGIN_REDIRECT_PATH = "/home"


def _force_english_locale(page) -> None:
    """Local mirror of CmsLoginPage._force_english_locale() — see that
    method's own docstring for the full live-verified rationale (persists
    the authenticated account's own Liferay UI-language preference, not
    just the current session/cookie). Called here so `reauthenticate()`
    closes the exact parity gap documented in this module's HEALED
    2026-09-15 note: the two places this project submits the login form
    must both re-assert English, not just one of them."""
    from urllib.parse import quote

    redirect_url = quote(POST_LOGIN_REDIRECT_PATH, safe="")
    page.goto(
        control_panel_url(
            f"{UPDATE_LANGUAGE_PATH}?languageId={ENGLISH_LANGUAGE_ID}&redirect={redirect_url}"
        )
    )
    page.locator(LOGIN_SUCCESS_INDICATOR).first.wait_for(state="attached", timeout=10000)


# How long a CMS page that READS signed out gets to show the signed-in marker
# before it is treated as a dead session (2026-10-12, PBI 129397). A page
# sampled mid-navigation -- e.g. the GM singleton's bare manage URL, which goes
# on to `?editEntry=<code>` after BasePage.open() has already returned at
# `domcontentloaded` -- has no `body` yet, so the zero-wait is_dead_session()
# read it as dead. Only the dead-looking path pays this wait.
DEAD_SESSION_CONFIRM_MS = 5000
# Same budget as base_page.NAV_TIMEOUT_MS (not imported: base_page imports
# this module). Heavy manage pages outgrow Playwright's 30 s default late in
# a run.
_NAV_TIMEOUT_MS = 90000


def _signed_in_marker_appears(page, timeout_ms: int = DEAD_SESSION_CONFIRM_MS) -> bool:
    """True once `body.signed-in` is attached (bounded wait). Never raises."""
    try:
        page.locator(LOGIN_SUCCESS_INDICATOR).first.wait_for(state="attached", timeout=timeout_ms)
        return True
    except Exception:  # noqa: BLE001 — detection must never mask a real failure
        return False


def is_login_form_showing(page) -> bool:
    """Cheap, non-blocking detection — mirrors license_gate.is_gate_showing's
    zero-wait contract."""
    try:
        return page.locator(USERNAME_INPUT).count() > 0
    except Exception:  # noqa: BLE001 — detection must never mask a real failure
        return False


def is_dead_session(page) -> bool:
    """Detects the second failure mode documented in this module's own
    docstring: an expired session on a Control-Panel-only URL that shows
    neither the login form nor the authenticated Control Menu/Product
    Menu — i.e. the public-site fallback render ("Coming Soon" or the
    plain public Home page) that neither this guard's own
    is_login_form_showing() nor license_gate.is_gate_showing() previously
    recognized. Returns False whenever the login form IS showing (that
    case is already handled by the existing is_login_form_showing() path)
    or the URL isn't a known Control-Panel-only path."""
    try:
        if not _is_control_panel_url(page.url):
            return False
        if is_login_form_showing(page):
            return False
        return page.locator(LOGIN_SUCCESS_INDICATOR).count() == 0
    except Exception:  # noqa: BLE001 — detection must never mask a real failure
        return False


def _refresh_cached_state(page, account: str) -> None:
    """Write the recovered session back to the storageState file the context
    came from -- only when that file belongs to `account`, so a role login can
    never overwrite TEST_USER's file. Never raises."""
    try:
        from core.web.browser import context_session, refresh_auth_state

        info = context_session(page.context) or {}
        if info.get("path") and info.get("account") == account:
            refresh_auth_state(page.context, info["path"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("cached auth-state refresh after re-authentication failed: %s", exc)


def reauthenticate(page, target_url: str = None, max_attempts: int = 3) -> bool:
    """Log back in AS THE SESSION'S OWNER (session_owner(); 2026-10-13 --
    previously always TEST_USER, so a dropped role session silently came back
    as super-admin) if the session has dropped, then return to `target_url`. No-op (returns False) if neither
    the login form nor a dead Control-Panel session (see is_dead_session's
    docstring) is detected — mirrors clear_license_gate's contract so
    callers can chain both guards unconditionally.

    An owner that cannot be resolved to credentials (a logged-out-on-purpose
    context, or an unknown account) is NOT re-logged in -- returns False.
    On success the context's cached storageState file is refreshed when that
    file belongs to the same account (core.web.browser.refresh_auth_state).
    Never call this from a test whose subject IS the login/permission flow
    itself (RBAC denial cases use `use_auth_state=False` contexts and drive
    CmsLoginPage directly instead — this guard would defeat that test's
    purpose).

    Returns True when the page was RECOVERED: re-authenticated, or (dead-
    session branch) found to be alive after all and sent back to the target.

    FIXED 2026-10-12 (tools/restore_singleton.py --pbi 129397 timing out on
    `open_entries_list()`, and the gate failures in allure-129397-20261012-
    2120, each preceded by "session re-authentication failed after 3
    attempts" with NO per-attempt line):
      1. A dead-looking page is CONFIRMED first (bounded wait for the
         signed-in marker). The zero-wait read misfired on a page caught
         mid-navigation.
      2. If LOGIN_PATH then renders no form but the page is signed in, the
         session was alive: Liferay redirects an authenticated session away
         from LOGIN_PATH (login_page.py, 2026-08-25). The old loop `break`
         left the page on that redirect target ("Coming Soon", not a CMS
         URL), so the caller's next wait burned its whole budget and
         BasePage.wait_for()'s recovery could not recognise the page. It now
         goes back to the target. Nothing is typed in that case.
    Never navigates to /c/portal/logout. It fills the form only when LOGIN_PATH
    actually renders one, i.e. for an anonymous session -- a signed-in shared
    session is redirected away first -- so a login here cannot replace a
    live shared storageState session.
    """
    dead_session = False
    if not is_login_form_showing(page):
        dead_session = is_dead_session(page)
        if not dead_session:
            return False
        if _signed_in_marker_appears(page):
            logger.info("signed-in marker appeared on %s after a settle — not a dead session", page.url)
            return False

    owner = session_owner(page)
    creds = credentials_for(owner)
    if not creds:
        logger.warning(
            "session dropped but its owner %r has no configured credentials "
            "(logged-out context or unknown account) -- not re-authenticating", owner
        )
        return False
    login_user, login_password = creds

    from core.web.license_gate import clear_license_gate, is_gate_showing  # local import: avoid a cycle at module load

    if dead_session:
        # No login form on the page yet — navigate to the real login URL to
        # force it to render before the fill/submit loop below runs (see
        # is_dead_session's docstring: the page currently showing is the
        # public-site fallback, not a form we can fill in place). Several
        # callers (e.g. base_page.py's wait_for() exception-recovery branch)
        # call reauthenticate(page) with no target_url at all — without
        # capturing where we actually were, a successful login would land on
        # Liferay's generic post-login default page instead of back on the
        # admin URL the caller was originally trying to reach, and the
        # caller's retried wait would fail again immediately.
        from config.settings import control_panel_url  # local import: avoid a cycle at module load

        if not target_url:
            target_url = page.url
        logger.info("dead session detected on %s — navigating to login form", page.url)
        page.goto(control_panel_url("/c/portal/login"))
        page.wait_for_load_state("domcontentloaded")

    reauthenticated = False
    attempted = False
    for attempt in range(1, max_attempts + 1):
        if not is_login_form_showing(page):
            break
        attempted = True
        try:
            page.locator(USERNAME_INPUT).fill(login_user)
            page.locator(PASSWORD_INPUT).fill(login_password)
            page.locator(SUBMIT_BUTTON).click()
            # Submitting the login form can itself re-trip the connection
            # limit (confirmed live, see module docstring) — clear that
            # before waiting on the success indicator, not after.
            if is_gate_showing(page):
                clear_license_gate(page, target_url)
            # .first: the OR'd selector legitimately matches BOTH the
            # Control Menu nav AND the Product Menu toggle button once
            # logged in (confirmed live 2026-08-25) — Playwright strict
            # mode rejects a 2-element match on a bare .wait_for(), which
            # was silently failing every re-authentication attempt.
            page.locator(LOGIN_SUCCESS_INDICATOR).first.wait_for(state="attached", timeout=15000)
            # HEALED 2026-09-15 (see module docstring) — the exact parity
            # gap that let a mid-run session drop silently leave the shared
            # TEST_USER account un-forced to English. Runs AFTER the
            # success indicator is confirmed (an authenticated request,
            # same requirement _force_english_locale() itself documents)
            # and BEFORE returning to target_url, so a caller resuming its
            # own navigation never races an in-flight locale-forcing
            # redirect. Best-effort: a failure here must not turn an
            # otherwise-successful re-authentication into a reported
            # failure — logged and swallowed, same contract every other
            # guard in this module already follows.
            try:
                _force_english_locale(page)
            except Exception as exc:  # noqa: BLE001
                logger.warning("post-reauthentication English-locale re-assert failed: %s", exc)
            reauthenticated = True
            set_session_owner(page, login_user)
            logger.info("session re-authenticated as %s (attempt %s)", login_user, attempt)
            _refresh_cached_state(page, login_user)
        except Exception as exc:  # noqa: BLE001
            logger.warning("re-authentication attempt %s failed: %s", attempt, exc)
            continue

        if target_url:
            # Explicit "domcontentloaded" on the goto itself, not just the
            # wait_for_load_state below it: a bare goto() waits for "load",
            # which never fires on the object-authoring surface (measured
            # 2026-09-09 — see BasePage.open()'s own note), so the
            # post-re-auth re-navigation could burn the full 30s default and
            # throw, turning a SUCCESSFUL session recovery into a test
            # failure.
            page.goto(target_url, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
        break

    if not reauthenticated and not attempted:
        if dead_session and target_url and _signed_in_marker_appears(page, timeout_ms=3000):
            # No form at LOGIN_PATH and the page is signed in: the session was
            # alive (see the docstring). Back to the caller's page, never left
            # on Liferay's post-login landing page.
            logger.warning(
                "no login form at %s and the page is signed in — the session is alive; "
                "returning to %s", page.url, target_url)
            page.goto(target_url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
            return True
        logger.warning("session re-authentication skipped: no login form rendered at %s — nothing typed",
                       page.url)
        return False
    if not reauthenticated:
        logger.warning("session re-authentication failed after %s attempts", max_attempts)
    return reauthenticated

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
"""

from core.utils.logger import get_logger
from config.settings import settings

logger = get_logger("session_guard")

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
LOGIN_SUCCESS_INDICATOR = 'nav[aria-label="Control Menu"], [data-qa-id="productMenu"]'

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


def reauthenticate(page, target_url: str = None, max_attempts: int = 3) -> bool:
    """Log back in with the project's admin test account if the session has
    dropped, then return to `target_url`. No-op (returns False) if neither
    the login form nor a dead Control-Panel session (see is_dead_session's
    docstring) is detected — mirrors clear_license_gate's contract so
    callers can chain both guards unconditionally.

    ONLY uses the shared admin account (settings.test_user/test_password).
    Never call this from a test whose subject IS the login/permission flow
    itself (RBAC denial cases use `use_auth_state=False` contexts and drive
    CmsLoginPage directly instead — this guard would defeat that test's
    purpose).
    """
    dead_session = False
    if not is_login_form_showing(page):
        dead_session = is_dead_session(page)
        if not dead_session:
            return False

    if not settings.test_user or not settings.test_password:
        logger.warning(
            "session dropped but TEST_USER/TEST_PASSWORD are not set — "
            "cannot auto-reauthenticate"
        )
        return False

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
    for attempt in range(1, max_attempts + 1):
        if not is_login_form_showing(page):
            break
        try:
            page.locator(USERNAME_INPUT).fill(settings.test_user)
            page.locator(PASSWORD_INPUT).fill(settings.test_password)
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
            page.locator(LOGIN_SUCCESS_INDICATOR).first.wait_for(state="visible", timeout=15000)
            reauthenticated = True
            logger.info("session re-authenticated (attempt %s)", attempt)
        except Exception as exc:  # noqa: BLE001
            logger.warning("re-authentication attempt %s failed: %s", attempt, exc)
            continue

        if target_url:
            page.goto(target_url)
            page.wait_for_load_state("domcontentloaded")
        break

    if not reauthenticated:
        logger.warning("session re-authentication failed after %s attempts", max_attempts)
    return reauthenticated

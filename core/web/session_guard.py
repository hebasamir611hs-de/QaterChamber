"""
core/web/session_guard.py — global re-authentication guard for the Liferay
Control Panel's dropped-session behavior on qcdev.

Root cause (confirmed live, 2026-08-24): the qcdev dev instance's session
drops roughly every ~30 seconds under sustained automated traffic. A
license-gate reset (core/web/license_gate.py) alone is not enough once that
happens — clicking the reset link can land back on the Control Panel LOGIN
FORM instead of the originally requested page, because the session backing
that reset was itself invalidated.

Per web/pages/control_panel/login_page.py's own history, submitting the
login form can itself re-trip the connection limit once — so this retries
the reset+login pair, not just a single login attempt.

This is a session symptom, not a fix for the underlying qcdev-side limit
(that needs whoever administers the qcdev instance — see license_gate.py's
docstring). This module only makes the automated suite recover from it
automatically instead of failing every test that outlives one ~30s window.

Wired into the wrapper layer (core/web/base_page.py) alongside
license_gate.py, not into any test or Page Object — every navigation in the
suite is covered by construction.
"""

from core.utils.logger import get_logger
from config.settings import settings

logger = get_logger("session_guard")

# Liferay's login portlet — same selectors as
# web/pages/control_panel/login_page.py's CmsLoginPage, verified live
# 2026-08-18. Kept as plain strings here (not an import of CmsLoginPage) to
# avoid a circular import: CmsLoginPage extends BasePage, which is where
# this guard is wired in.
USERNAME_INPUT = "#_com_liferay_login_web_portlet_LoginPortlet_login"
PASSWORD_INPUT = "#_com_liferay_login_web_portlet_LoginPortlet_password"
SUBMIT_BUTTON = (
    '#_com_liferay_login_web_portlet_LoginPortlet_loginForm button[type="submit"]'
)
# OR'd with the Product Menu toggle (2026-08-25) — see
# web/pages/control_panel/login_page.py's STATUS UPDATE (2026-08-25) for the
# live evidence: both render together after a real login, ORing only guards
# against a render-order race between the two nav elements.
LOGIN_SUCCESS_INDICATOR = 'nav[aria-label="Control Menu"], [data-qa-id="productMenu"]'


def is_login_form_showing(page) -> bool:
    """Cheap, non-blocking detection — mirrors license_gate.is_gate_showing's
    zero-wait contract."""
    try:
        return page.locator(USERNAME_INPUT).count() > 0
    except Exception:  # noqa: BLE001 — detection must never mask a real failure
        return False


def reauthenticate(page, target_url: str = None, max_attempts: int = 3) -> bool:
    """Log back in with the project's admin test account if the session has
    dropped, then return to `target_url`. No-op (returns False) if the login
    form is not showing — mirrors clear_license_gate's contract so callers
    can chain both guards unconditionally.

    ONLY uses the shared admin account (settings.test_user/test_password).
    Never call this from a test whose subject IS the login/permission flow
    itself (RBAC denial cases use `use_auth_state=False` contexts and drive
    CmsLoginPage directly instead — this guard would defeat that test's
    purpose).
    """
    if not is_login_form_showing(page):
        return False

    if not settings.test_user or not settings.test_password:
        logger.warning(
            "session dropped (login form showing) but TEST_USER/TEST_PASSWORD "
            "are not set — cannot auto-reauthenticate"
        )
        return False

    from core.web.license_gate import clear_license_gate, is_gate_showing  # local import: avoid a cycle at module load

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

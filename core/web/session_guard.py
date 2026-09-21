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

This is a session symptom, not a fix for the underlying qcdev-side limit
(that needs whoever administers the qcdev instance — see license_gate.py's
docstring). This module only makes the automated suite recover from it
automatically instead of failing every test that outlives one ~30s window.

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

from core.utils.logger import get_logger
from config.settings import control_panel_url, settings

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
    page.locator(LOGIN_SUCCESS_INDICATOR).first.wait_for(state="visible", timeout=10000)


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

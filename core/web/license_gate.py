"""
core/web/license_gate.py — global interstitial handler for the Liferay
"developer mode connection limit" page.

The dev/UAT Liferay instance intermittently answers ANY request with a
license interstitial instead of the requested page:

    URL   : <base>/c/portal/license_activation
    Body  : "Error: You have exceeded the developer mode connection limit.
             Click here to reset all connections."
    Link  : <a href="/c/portal/license?cmd=resetState&resetToken=<uuid>">here</a>

The reset token is regenerated on every hit, so the link can only be
followed live — it cannot be pre-baked into a URL or a fixture.

This module is the ONE place that knows about it. It is wired into the
wrapper layer (core/web/base_page.py), not into any test or Page Object, so
every navigation in the suite is covered by construction and no test carries
site-infrastructure noise. Detection is cheap (a string check on the current
URL plus a zero-wait DOM count), and when the interstitial is absent the
guard is a no-op — nothing to do, nothing logged, no timeout paid.
"""

from core.utils.logger import get_logger
from core.web.overlays import MOUNT_GRACE_MS, dismiss_overlays

logger = get_logger("license_gate")

# The interstitial always lives under this Liferay portal path.
GATE_URL_MARKER = "/c/portal/license"
# The "here" link. Matched on the stable query flag, never the rotating token.
RESET_LINK = 'a[href*="cmd=resetState"]'
# Text fallback, for the case where the same error is rendered in place on a
# normal URL rather than via the license_activation redirect.
GATE_TEXT_MARKER = "developer mode connection limit"

_TARGET_ATTR = "_qc_gate_target_url"


def remember_target(page, url: str) -> None:
    """Record the URL a navigation was aiming at, so the guard can return to
    it after clearing the interstitial. Set by BasePage.open()."""
    setattr(page, _TARGET_ATTR, url)


def _target(page):
    return getattr(page, _TARGET_ATTR, None)


def is_gate_showing(page) -> bool:
    """Cheap, non-blocking detection — no implicit wait is paid on the
    overwhelmingly common healthy-page path."""
    try:
        if GATE_URL_MARKER in page.url:
            return True
        if page.locator(RESET_LINK).count() > 0:
            return True
        return False
    except Exception:  # noqa: BLE001 — detection must never mask a real failure
        return False


def clear_license_gate(page, target_url: str = None, max_attempts: int = 3) -> bool:
    """Clear the interstitial if it is showing, then return to `target_url`
    (or the last URL remembered via remember_target()).

    Returns True if a gate was found and cleared, False if there was nothing
    to do — per the requirement that a missing interstitial is a silent
    no-op, never an error.
    """
    if not is_gate_showing(page):
        return False

    destination = target_url or _target(page)
    cleared = False

    for attempt in range(1, max_attempts + 1):
        if not is_gate_showing(page):
            break
        # The announcement overlay renders on the interstitial too and covers
        # the whole viewport, so it intercepts the reset link. Clear it first
        # or the gate can never be dismissed.
        dismiss_overlays(page, grace_ms=MOUNT_GRACE_MS)
        link = page.locator(RESET_LINK).first
        try:
            link.wait_for(state="attached", timeout=5000)
            link.click(timeout=10000)
            page.wait_for_load_state("domcontentloaded")
            cleared = True
            logger.info("license gate cleared (attempt %s)", attempt)
        except Exception as exc:  # noqa: BLE001
            logger.warning("license gate reset link not clickable: %s", exc)
            break

        if destination:
            page.goto(destination)
            page.wait_for_load_state("domcontentloaded")

    if cleared and is_gate_showing(page):
        logger.warning("license gate still showing after %s attempts", max_attempts)
    return cleared

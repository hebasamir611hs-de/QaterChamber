"""
core/web/overlays.py — global dismissal of site-wide blocking overlays.

Sibling of core/web/license_gate.py: same contract, same wiring point. The
site injects a full-screen announcement modal shortly after every page load:

    root  : #qc-announcement-popup-root.qc-ann-overlay   (z-index 100000,
            full viewport, <html> gets .qc-a11y-scroll-locked)
    card  : div.qc-ann-card[role=dialog][aria-modal=true]
    close : button.qc-ann-close[aria-label="Close"]

It covers the entire viewport, so every click in the suite is intercepted by
it. Measured on the live site: it mounts 66-98ms AFTER page.goto() returns
(it is rendered by client JS, not server-side), so a zero-wait check
straight after navigation races it — hence MOUNT_GRACE_MS below.

Closing it writes NO persistence flag (verified: localStorage holds only
Liferay's LFR_SESSION_STATE_*, and the "Don't show this again" checkbox is
deliberately NOT ticked here, because ticking it would mutate state a test
might be asserting on). It therefore reappears on every navigation, and
dismissal is applied per-navigation rather than once per session.

Registry-driven: adding another blocking overlay is one OVERLAYS entry, not
new logic. Absent overlay == silent no-op, never an error.

Known, deliberately NOT dismissed: #qcChatbot (.qc-chatbot, z-index 9999,
390x645, bottom corner). It is a persistent widget rather than a modal and
does not cover the page; closing it proactively would change page state.
Add it here if it is ever found to intercept a real interaction.
"""

from core.utils.logger import get_logger

logger = get_logger("overlays")

# How long to allow a client-rendered overlay to mount before concluding it
# is absent. Paid only once per navigation, and on this site the overlay
# almost always mounts well inside it, so the wait normally ends early.
MOUNT_GRACE_MS = 1500


class Overlay:
    def __init__(self, name: str, root: str, close: str):
        self.name = name
        self.root = root
        self.close = close


OVERLAYS = [
    Overlay(
        name="announcement",
        root="#qc-announcement-popup-root",
        close="#qc-announcement-popup-root button.qc-ann-close",
    ),
]


def _is_showing(page, overlay: Overlay) -> bool:
    try:
        return page.locator(overlay.root).count() > 0 and page.locator(overlay.root).first.is_visible()
    except Exception:  # noqa: BLE001 — detection must never mask a real failure
        return False


def is_overlay_showing(page) -> bool:
    """Cheap, zero-wait check across the registry."""
    return any(_is_showing(page, o) for o in OVERLAYS)


def dismiss_overlays(page, grace_ms: int = 0) -> bool:
    """Dismiss every registered overlay currently blocking the page.

    `grace_ms` > 0 waits that long for a client-rendered overlay to appear
    before giving up on it — use it right after a navigation. Returns True
    if anything was dismissed.
    """
    dismissed = False

    for overlay in OVERLAYS:
        if grace_ms and not _is_showing(page, overlay):
            try:
                page.locator(overlay.root).first.wait_for(state="visible", timeout=grace_ms)
            except Exception:  # noqa: BLE001 — not shown on this page; nothing to do
                continue

        if not _is_showing(page, overlay):
            continue

        try:
            page.locator(overlay.close).first.click()
            page.locator(overlay.root).first.wait_for(state="hidden", timeout=5000)
            dismissed = True
            logger.info("dismissed overlay: %s", overlay.name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("could not dismiss overlay %s: %s", overlay.name, exc)

    return dismissed

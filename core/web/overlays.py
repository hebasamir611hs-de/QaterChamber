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

CONFIRMED LIVE INTERCEPTING (2026-08-31/09-01, follow-up session investigating
the Business Events admin grid's row-kebab delete flow): #qcChatbot
(.qc-chatbot, launcher button `button.qc-launcher[aria-label="Open chat"]`,
bottom-right corner) DOES intercept a real click — a plain Playwright
`.click()` on a row's Actions kebab button in the Business Events Object
Definition list (Control Panel surface) hung Playwright's full 30s
action-timeout with the error trace repeatedly naming
`<button class="qc-launcher" ...>` as the element "subtree intercepts pointer
events", alongside an invisible reCAPTCHA iframe also intercepting on retry.
This is NOT the announcement modal's full-viewport-cover case the prior note
above assumed — the chat launcher is a small, position:fixed corner widget,
but its own overlay stacking apparently extends over nearby actionable
elements on at least this admin grid's row-actions column when the button is
scrolled into view. Registered below (CHATBOT_LAUNCHER) as a close-by-removal
overlay: `dismiss_overlays()` cannot "close" a chat launcher the way it closes
a modal, so this overlay's `close` is deliberately absent and dismissal is a
DOM-removal fallback instead (see `_dismiss_chatbot_launcher()`) — the widget
reappears on the next navigation regardless, so removing it is the same
per-navigation, no-persisted-state shape as the announcement modal's own
dismissal, not a state mutation that could affect a real assertion. Confirmed
on the Control Panel surface; not yet confirmed to also intercept on the
public web surface, so it is registered for both surfaces rather than
narrowed, pending a case that shows it does NOT matter there.
"""

from core.utils.logger import get_logger

logger = get_logger("overlays")

# How long to allow a client-rendered overlay to mount before concluding it
# is absent. Paid only once per navigation, and on this site the overlay
# almost always mounts well inside it, so the wait normally ends early.
MOUNT_GRACE_MS = 1500


class Overlay:
    def __init__(self, name: str, root: str, close: str, surfaces: tuple = ("web",)):
        self.name = name
        self.root = root
        self.close = close
        # Which delivery surface(s) this overlay can appear on. The mount
        # GRACE is only ever paid on a matching surface: the grace's full
        # cost (MOUNT_GRACE_MS) is paid precisely when the overlay is ABSENT
        # (wait_for runs to timeout), so an overlay scoped to the public
        # site must not tax every Control Panel navigation — that was a
        # guaranteed 1500ms per CMS-test navigation for an overlay that can
        # never appear there (mentor review, 2026-08-18).
        self.surfaces = surfaces


OVERLAYS = [
    Overlay(
        name="announcement",
        root="#qc-announcement-popup-root",
        close="#qc-announcement-popup-root button.qc-ann-close",
        surfaces=("web",),  # public-site announcement — never renders in the Control Panel
    ),
]

# The chat launcher widget — see module docstring's CONFIRMED LIVE
# INTERCEPTING note. Handled OUTSIDE the OVERLAYS registry/Overlay class
# because there is no "close" action for it (it is a persistent launcher
# button, not a dismissible modal) — the fix is removing the DOM node, which
# is safe because it carries no persisted dismissal state and simply
# re-mounts on the next navigation, exactly like the announcement modal.
CHATBOT_LAUNCHER_ROOT = "#qcChatbot"


def _dismiss_chatbot_launcher(page) -> bool:
    try:
        launcher = page.locator(CHATBOT_LAUNCHER_ROOT)
        if launcher.count() == 0:
            return False
        page.evaluate(
            "(sel) => { const el = document.querySelector(sel); if (el) el.remove(); }",
            CHATBOT_LAUNCHER_ROOT,
        )
        logger.info("removed intercepting chat launcher widget: %s", CHATBOT_LAUNCHER_ROOT)
        return True
    except Exception:  # noqa: BLE001 — best-effort only, never masks a real failure
        return False


def _current_surface(page) -> str:
    """Best-effort surface classification.

    CONFIRMED LIVE, 2026-08-25 (qcdev): CONTROL_PANEL_URL and WEB_BASE_URL
    are the IDENTICAL host in this project's .env
    (https://qcdev.ihorizons.com, no distinguishing path prefix). A plain
    `page.url.startswith(control_panel_url)` prefix match therefore matched
    on every page, always classifying as "control_panel" — which meant
    MOUNT_GRACE_MS was never actually paid anywhere (the grace branch below
    is gated on `surface in overlay.surfaces`, and "web" never matched).
    Every navigation raced the announcement overlay's async mount (66-98ms)
    with a zero-wait check and normally lost, leaving clicks to recover only
    through BasePage.click()'s slower exception-driven retry.

    Liferay Control Panel URLs carry their own markers regardless of host —
    `/c/portal/...`, a `p_p_id=` portlet-render query param, or the
    `/control_panel/` path segment (see LIST_URL in
    web/pages/org_structure/org_structure_admin_page.py) — none of which a
    public content page carries. Classify on those instead of the base URL.
    Ambiguous pages (e.g. an authenticated admin browsing plain /home) fall
    through to "web", which is the surface the overlay is actually scoped
    to and the safe default either way.

    CONFIRMED LIVE, 2026-08-25 (second pass, full-suite run): the `p_p_id=`
    marker over-fired on the LOGIN portlet's own redirect URL
    (`/home?p_p_id=com_liferay_login_web_portlet_LoginPortlet_...`) — that
    page IS on the "web" surface (it's where the public-facing announcement
    overlay renders and blocks the username field, confirmed by screenshot),
    not the admin Control Panel, even though it carries a `p_p_id=` query
    param like every Liferay portlet render does. `com_liferay_login_web_portlet_LoginPortlet`
    specifically must classify as "web" — check for it before the generic
    `p_p_id=` marker, not after.
    """
    try:
        url = page.url or ""
        if "com_liferay_login_web_portlet_LoginPortlet" in url:
            return "web"
        if "/c/portal" in url or "p_p_id=" in url or "/control_panel/" in url:
            return "control_panel"
    except Exception:  # noqa: BLE001 — classification must never break dismissal
        pass
    return "web"


def _is_showing(page, overlay: Overlay) -> bool:
    try:
        return page.locator(overlay.root).count() > 0 and page.locator(overlay.root).first.is_visible()
    except Exception:  # noqa: BLE001 — detection must never mask a real failure
        return False


def is_overlay_showing(page) -> bool:
    """Cheap, zero-wait check across the registry (does not include the
    chat launcher — it never fully covers the page, so it is not a
    "something is blocking everything" signal the way the registry's modals
    are)."""
    return any(_is_showing(page, o) for o in OVERLAYS)


def dismiss_overlays(page, grace_ms: int = 0) -> bool:
    """Dismiss every registered overlay currently blocking the page.

    Deliberately does NOT also remove the #qcChatbot launcher on every call
    — this runs on EVERY navigation via BasePage.open(), and removing a
    widget suite-wide on every page for one admin grid's confirmed-live
    interception would be a much bigger behavior change than this session's
    task called for (and could silently break a future test that asserts on
    the launcher itself). Callers with live evidence the launcher is
    actually blocking their own interaction (see
    HomeBusinessEventsAdminPage.delete_row_by_title()) should call
    `_dismiss_chatbot_launcher(page)` directly at that call site instead.

    `grace_ms` > 0 waits that long for a client-rendered overlay to appear
    before giving up on it — use it right after a navigation. Returns True
    if anything was dismissed.
    """
    dismissed = False
    surface = _current_surface(page)

    for overlay in OVERLAYS:
        # Off-surface overlays keep the FREE zero-wait check (safety net in
        # case the surface classification or the overlay's real scope is
        # wrong) but never pay the mount grace — see Overlay.surfaces.
        if grace_ms and surface in overlay.surfaces and not _is_showing(page, overlay):
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

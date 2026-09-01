"""
core/web/base_page.py — BasePage wrapper. The only place raw Playwright is
touched besides browser.py. Self-waiting, self-logging, self-screenshotting —
per the wrapper API table in automation-standards.md. No time.sleep(), no
bare asserts (Page Objects expose state; tests assert).
"""

from core.utils.logger import get_logger, log_action
from core.utils.reporting import attach_screenshot
from core.web.license_gate import clear_license_gate, is_gate_showing, remember_target
from core.web.overlays import MOUNT_GRACE_MS, dismiss_overlays, is_overlay_showing
from core.web.session_guard import is_login_form_showing, reauthenticate
from config.settings import settings

logger = get_logger("base_page")

# Marker for a navigation that is ITSELF the login flow (CmsLoginPage.open_login()
# / the Liferay login portlet's own render/redirect URLs) — same string
# overlays.py's _current_surface() already keys on for the identical reason.
# The login form is expected to be showing on this URL; that is not a dropped
# session, and reauthenticate()'s own login submission must not fire here or
# it races CmsLoginPage.login()'s subsequent type()/click() calls on a page
# that has since navigated away (confirmed live 2026-08-25 — see
# session_guard.py's reentrancy note for the sibling fix in type()).
_LOGIN_FLOW_MARKERS = ("/c/portal/login", "com_liferay_login_web_portlet_LoginPortlet")


def _is_login_flow_url(url: str) -> bool:
    return any(marker in (url or "") for marker in _LOGIN_FLOW_MARKERS)


class BasePage:
    def __init__(self, page):
        self.page = page

    def open(self, url: str) -> None:
        remember_target(self.page, url)
        self.page.goto(url)
        # Site-wide interstitial guard (see core/web/license_gate.py). No-op
        # when the interstitial is absent, which is the normal path.
        clear_license_gate(self.page, url)
        # qcdev's session drops roughly every ~30s under sustained automated
        # traffic (see core/web/session_guard.py) — a reset can land back on
        # the login form. No-op when already authenticated. Skipped when the
        # navigation target IS the login flow itself (see _is_login_flow_url).
        if not _is_login_flow_url(url):
            reauthenticate(self.page, url)
        # Site-wide blocking overlays (see core/web/overlays.py). Client-
        # rendered, so a mount grace is allowed here and only here.
        dismiss_overlays(self.page, grace_ms=MOUNT_GRACE_MS)
        log_action(logger, "open", url)

    def click(self, locator: str) -> None:
        # The session can drop between two calls on this page (open_x() then
        # click(), no wait_for() in between) — check before spending the
        # click's own timeout on a page that's actually the license gate or
        # the login form underneath. Skipped on the login flow's own URL
        # (see _is_login_flow_url) — CmsLoginPage.login() clicking its own
        # submit button while its own form is visible is not a dropped
        # session, and firing reauthenticate() here races login()'s own
        # subsequent calls on a page that has since navigated away
        # (confirmed live 2026-08-25 — same reentrancy bug as type() below).
        on_login_flow = _is_login_flow_url(self.page.url)
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if not on_login_flow and is_login_form_showing(self.page):
            reauthenticate(self.page)
        try:
            self.page.locator(locator).click()
        except Exception:
            # An overlay that mounted late (or reappeared after a click-driven
            # navigation) intercepts the click, OR the session dropped mid-
            # click. Clear whichever applies and retry once before surfacing
            # this as a real failure.
            recovered = dismiss_overlays(self.page)
            recovered = clear_license_gate(self.page) or recovered
            if not on_login_flow:
                recovered = reauthenticate(self.page) or recovered
            if not recovered:
                raise
            self.page.locator(locator).click()
        log_action(logger, "click", locator)

    def type(self, locator: str, text: str) -> None:
        # Same session-drop window as click() — a multi-field form fills
        # several locators in a row, any of which can outlive one ~30s
        # qcdev session window. Skipped on the login flow's own URL (see
        # click()'s comment and _is_login_flow_url) — filling the login
        # form's own username/password fields must not trigger a redundant
        # background reauthenticate() (confirmed live 2026-08-25: it logged
        # in, navigated to an unrelated page, and left this type() call
        # waiting 30s on a username field that no longer existed there).
        on_login_flow = _is_login_flow_url(self.page.url)
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if not on_login_flow and is_login_form_showing(self.page):
            reauthenticate(self.page)
        loc = self.page.locator(locator)
        try:
            loc.clear()
            loc.fill(text)
        except Exception:
            # Same recovery as click(): a late-mounting overlay (or a
            # session drop) can block a fill() the same way it blocks a
            # click() — confirmed live 2026-08-25 (qcdev), the announcement
            # overlay intercepting the login username field caused a bare
            # 30s TimeoutError here with no recovery attempted, because
            # type() previously had no retry path at all. Mirrors click()'s
            # retry exactly rather than inventing a separate one.
            recovered = dismiss_overlays(self.page)
            recovered = clear_license_gate(self.page) or recovered
            if not on_login_flow:
                recovered = reauthenticate(self.page) or recovered
            if not recovered:
                raise
            loc.clear()
            loc.fill(text)
        log_action(logger, "type", locator, text)

    def text(self, locator: str) -> str:
        return self.page.locator(locator).inner_text()

    def is_visible(self, locator: str) -> bool:
        try:
            # An interstitial or a dropped session would make every locator
            # report "not visible", which silently turns a blocked page into
            # a passing negative assertion. Clear both first, then answer
            # honestly.
            if is_gate_showing(self.page):
                clear_license_gate(self.page)
            if is_login_form_showing(self.page):
                reauthenticate(self.page)
            return self.page.locator(locator).is_visible()
        except Exception:  # noqa: BLE001 — never throws, per the wrapper contract
            return False

    def wait_for(self, locator: str, state: str = "visible", timeout: int = 10000, first: bool = False) -> None:
        # Covers click-driven navigation too (the Page Objects wait on an
        # element after every click), not just the explicit open() above.
        #
        # `first`: pass True when the call is only confirming "at least one
        # match rendered" (e.g. a grid that legitimately has >1 row) rather
        # than targeting one specific element — without it, Playwright's
        # strict mode throws on a locator matching more than one element.
        # Kept inside this wrapper (not a raw `.first` at the call site) so
        # every Page Object call still gets the gate/reauth handling below,
        # including the post-recovery retry and the after-wait overlay
        # check — none of that is optional, per this method's own docstring
        # notes on click-driven navigation re-arming interstitials.
        target = self.page.locator(locator).first if first else self.page.locator(locator)
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if is_login_form_showing(self.page):
            reauthenticate(self.page)
        try:
            target.wait_for(state=state, timeout=timeout)
        except Exception:
            # The interstitial or a dropped session can also arrive
            # mid-wait; clear once and retry before surfacing the timeout as
            # a real failure.
            recovered = clear_license_gate(self.page)
            recovered = reauthenticate(self.page) or recovered
            if not recovered:
                raise
            target.wait_for(state=state, timeout=timeout)
        # Checked AFTER the wait, zero-wait: click-driven navigation re-renders
        # the announcement overlay (it stores no dismissal flag), and by the
        # time the awaited element exists the overlay has normally mounted too.
        # Anything that still slips through is caught by click()'s retry.
        if is_overlay_showing(self.page):
            dismiss_overlays(self.page)

    def select_option(self, locator: str, label: str = None, value: str = None) -> None:
        self.page.locator(locator).select_option(label=label, value=value)
        log_action(logger, "select_option", locator, label or value)

    def set_checkbox(self, locator: str, checked: bool) -> None:
        loc = self.page.locator(locator)
        if checked:
            loc.check()
        else:
            loc.uncheck()
        log_action(logger, "set_checkbox", locator, str(checked))

    def upload_file(self, locator: str, file_path: str) -> None:
        self.page.locator(locator).set_input_files(file_path)
        log_action(logger, "upload_file", locator, file_path)

    def press_key(self, key: str) -> None:
        self.page.keyboard.press(key)
        log_action(logger, "press_key", key)

    def is_focused(self, locator: str) -> bool:
        try:
            return self.page.locator(locator).evaluate("el => el === document.activeElement")
        except Exception:  # noqa: BLE001 — never throws, mirrors is_visible's contract
            return False

    def press_tab_until_focused(self, locator: str, max_presses: int = 25) -> bool:
        """Generic keyboard-only reach helper for focus-indicator /
        keyboard-navigation cases: presses Tab up to `max_presses` times,
        returning True as soon as `locator` becomes document.activeElement."""
        for _ in range(max_presses):
            if self.is_focused(locator):
                return True
            self.press_key("Tab")
        return self.is_focused(locator)

    def fill_iframe_editor(self, iframe_locator: str, text: str) -> None:
        """Write into a classic (iframe-based) CKEditor's editable body —
        e.g. `iframe[title="editor"]`. The field's own OUTER wrapper
        (`[role="textbox"][aria-label=...]`) is a non-editable mount point
        only; the real `[contenteditable]` document lives inside this
        iframe and does not exist in the DOM until the wrapper is clicked
        once to force the widget to mount (confirmed live on this project —
        see home_strategic_direction_admin_page.py's PILLAR_DESCRIPTION
        fields for the reproduction). Callers must click the wrapper (or
        otherwise trigger the mount) and wait for the iframe to render
        before calling this. Uses frame_locator (not `.content_frame()` on
        a Locator, which this project's pinned Playwright version does not
        expose) plus a real keyboard select-all + type — never
        `page.evaluate()` into the frame, which would bypass CKEditor's own
        input handling and prove nothing about the real widget."""
        on_login_flow = _is_login_flow_url(self.page.url)
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if not on_login_flow and is_login_form_showing(self.page):
            reauthenticate(self.page)
        body = self.page.frame_locator(iframe_locator).locator("body")
        body.wait_for(state="visible")
        body.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.type(text)
        log_action(logger, "fill_iframe_editor", iframe_locator, text)

    def iframe_editor_text(self, iframe_locator: str) -> str:
        """Read the CURRENT (possibly unsaved) editable text out of a
        classic CKEditor iframe's body — the live counterpart to
        `fill_iframe_editor`. For reading a value that's already been
        SAVED and reloaded, prefer a Page Object's own persisted-value
        read (e.g. from the portlet's embedded field-config JSON) where
        one exists — this method reflects only what's currently rendered
        in the iframe on the open form."""
        return self.page.frame_locator(iframe_locator).locator("body").inner_text()

    def screenshot(self, test_case_id: str = "NO-TC") -> bytes:
        png = self.page.screenshot()
        attach_screenshot(png, test_case_id, settings.project_name)
        return png

    def assert_visible(self, locator: str, test_case_id: str = "NO-TC") -> None:
        if not self.is_visible(locator):
            self.screenshot(test_case_id)
            raise AssertionError(f"expected visible: {locator}")

    def assert_text(self, locator: str, expected: str, test_case_id: str = "NO-TC") -> None:
        actual = self.text(locator)
        if actual != expected:
            self.screenshot(test_case_id)
            raise AssertionError(f"expected text {expected!r} at {locator}, got {actual!r}")

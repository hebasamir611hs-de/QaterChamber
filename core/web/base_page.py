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
        # the login form. No-op when already authenticated.
        reauthenticate(self.page, url)
        # Site-wide blocking overlays (see core/web/overlays.py). Client-
        # rendered, so a mount grace is allowed here and only here.
        dismiss_overlays(self.page, grace_ms=MOUNT_GRACE_MS)
        log_action(logger, "open", url)

    def click(self, locator: str) -> None:
        # The session can drop between two calls on this page (open_x() then
        # click(), no wait_for() in between) — check before spending the
        # click's own timeout on a page that's actually the license gate or
        # the login form underneath.
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if is_login_form_showing(self.page):
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
            recovered = reauthenticate(self.page) or recovered
            if not recovered:
                raise
            self.page.locator(locator).click()
        log_action(logger, "click", locator)

    def type(self, locator: str, text: str) -> None:
        # Same session-drop window as click() — a multi-field form fills
        # several locators in a row, any of which can outlive one ~30s
        # qcdev session window.
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if is_login_form_showing(self.page):
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

    def wait_for(self, locator: str, state: str = "visible", timeout: int = 10000) -> None:
        # Covers click-driven navigation too (the Page Objects wait on an
        # element after every click), not just the explicit open() above.
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if is_login_form_showing(self.page):
            reauthenticate(self.page)
        try:
            self.page.locator(locator).wait_for(state=state, timeout=timeout)
        except Exception:
            # The interstitial or a dropped session can also arrive
            # mid-wait; clear once and retry before surfacing the timeout as
            # a real failure.
            recovered = clear_license_gate(self.page)
            recovered = reauthenticate(self.page) or recovered
            if not recovered:
                raise
            self.page.locator(locator).wait_for(state=state, timeout=timeout)
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

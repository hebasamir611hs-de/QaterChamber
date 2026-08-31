"""
web/pages/home_featured_event/home_featured_event_admin_page.py —
HomeFeaturedEventAdminPage.

PBI 129382 / QC-HOME-006 "Upcoming Featured Event" — Control_Panel-tagged
cases (ADO TC 135653-135657): Pin Configuration screen accessibility, the
Event Selector, the Save success toast (EN/AR), and RTL rendering of the
Pin Configuration form. Sibling of home_featured_event_page.py (the public
Web-platform Page Object for this same PBI).

STATUS: PARTIALLY VERIFIED (2026-08-24). Login itself is real and
CLI-confirmed (see the shared web/pages/components/cms_login_page.py this
Page Object composes) — the anonymous /c/portal/login form is reachable
without credentials. Everything on THIS page (Home Page management
navigation, the Pin Configuration screen, the Event Selector, the Active
Status control, the Save button, the success toast, and the RTL form
layout) is BLOCKED, not guessed: reaching any of it requires an actual
authenticated Site Content Editor session, and this session had no valid
TEST_USER/TEST_PASSWORD to log in with (both are blank in .env — see
cms_login_page.py's docstring) and no Playwright MCP fallback is available
in this environment to step through it interactively either.

Every locator below is the literal TODO placeholder string (never a
guessed-but-plausible selector) — the same convention this project's own
git history already established for exactly this situation (commit
2cbbb4c's predecessor, "_UNVERIFIED" gate; `web/tests/header/
test_accessibility_settings_control_panel.py`'s `_UNRESOLVED` collection-
time skipif gate). test_home_featured_event_control_panel.py's own
`_UNRESOLVED` gate skips every test that touches one of these constants
until a real admin account can extract them for real, per
`tools/extract_locators.py --storage-state .auth/state.json` once
`tools/save_auth.py` has a working Control Panel login to capture.

Replace only after confirming the real Pin Configuration screen live —
never mark this file "done" by guessing a plausible-looking Liferay
fragment-configuration class name.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_TODO_PREFIX = "TODO:"


def _todo(what: str) -> str:
    return f"{_TODO_PREFIX} run tools/extract_locators.py (as an authenticated Site Content Editor) against the live Pin Configuration screen and paste the confirmed selector for {what}"


class HomeFeaturedEventAdminPage(BasePage):
    # ── Unreachable without an authenticated session this run — see docstring ──
    # Every constant below, including the Home Page management entry point's
    # own PATH, is unconfirmed — no real Liferay path/selector is guessed.
    HOME_PAGE_MANAGEMENT_LINK = _todo("the 'Home Page management' nav item")
    UPCOMING_EVENT_PIN_CONFIG_LINK = _todo("the 'Upcoming Event Pin Configuration' entry point")
    PIN_CONFIG_SCREEN = _todo("the Pin Configuration screen's own container")
    EVENT_SELECTOR = _todo("the Event Selector control")
    EVENT_SELECTOR_OPTION = _todo("one Event Selector dropdown option (relative to EVENT_SELECTOR)")
    ACTIVE_STATUS_CONTROL = _todo("the Active Status toggle/checkbox")
    SAVE_BUTTON = _todo("the Pin Configuration screen's Save button")
    SUCCESS_TOAST = _todo("the Liferay generic success toast/notification")
    PIN_CONFIG_FORM = _todo("the Pin Configuration form's own root element (for RTL/direction checks)")

    def open_control_panel_home(self) -> "HomeFeaturedEventAdminPage":
        self.open(control_panel_url("/group/qatar-chamber"))
        return self

    def navigate_to_home_page_management(self) -> "HomeFeaturedEventAdminPage":
        self.click(self.HOME_PAGE_MANAGEMENT_LINK)
        return self

    def open_pin_configuration(self) -> "HomeFeaturedEventAdminPage":
        self.click(self.UPCOMING_EVENT_PIN_CONFIG_LINK)
        self.wait_for(self.PIN_CONFIG_SCREEN)
        return self

    # ── State queries — no asserts, tests do the asserting ──────────────
    def is_pin_config_screen_visible(self) -> bool:
        return self.is_visible(self.PIN_CONFIG_SCREEN)

    def is_event_selector_visible(self) -> bool:
        return self.is_visible(self.EVENT_SELECTOR)

    def is_active_status_control_visible(self) -> bool:
        return self.is_visible(self.ACTIVE_STATUS_CONTROL)

    def open_event_selector(self) -> "HomeFeaturedEventAdminPage":
        self.click(self.EVENT_SELECTOR)
        return self

    def published_event_option_labels(self) -> list:
        options = self.page.locator(self.EVENT_SELECTOR_OPTION)
        return [options.nth(i).inner_text().strip() for i in range(options.count())]

    def select_event(self, label: str) -> "HomeFeaturedEventAdminPage":
        self.click(f'{self.EVENT_SELECTOR_OPTION}:has-text("{label}")')
        return self

    def set_active_status(self, enabled: bool) -> "HomeFeaturedEventAdminPage":
        is_checked = self.page.locator(self.ACTIVE_STATUS_CONTROL).is_checked()
        if is_checked != enabled:
            self.click(self.ACTIVE_STATUS_CONTROL)
        return self

    def click_save(self) -> "HomeFeaturedEventAdminPage":
        self.click(self.SAVE_BUTTON)
        return self

    def is_success_toast_visible(self) -> bool:
        return self.is_visible(self.SUCCESS_TOAST)

    def success_toast_text(self) -> str:
        return self.text(self.SUCCESS_TOAST)

    def pin_config_form_direction(self) -> str:
        return self.page.locator(self.PIN_CONFIG_FORM).evaluate("el => getComputedStyle(el).direction")

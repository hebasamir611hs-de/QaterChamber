"""
web/pages/header/accessibility_settings_page.py — AccessibilitySettingsPage.

Control Panel -> Global Components -> Header Management -> Accessibility
Settings. Backs the GLOBAL-ACCESSIBILITY-TC-* family (PBI 133381,
.claude/qa-baselines/133381.json) and specifically ADO Test Case 134658
(RBAC denial for a role lacking Header Management permission).

LOCATORS ARE UNVERIFIED PLACEHOLDERS — same convention as
web/pages/header/site_header_page.py: never run against live qcdev from
this authoring environment, so never guessed either. SETTINGS_PATH is
included in that: Header Management reads as a custom module built for
this project, not a stock Liferay admin screen, so its URL is not
inferrable — it must come from extract_locators.py / manual navigation by
someone who can actually reach the page (i.e. an admin account, since this
whole feature is about a role that CANNOT reach it).
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_UNVERIFIED = "TODO: run tools/extract_locators.py against the live page and paste the confirmed selector here"


class AccessibilitySettingsPage(BasePage):
    SETTINGS_PATH = _UNVERIFIED
    ACCESS_DENIED_MESSAGE_EN = _UNVERIFIED
    ACCESS_DENIED_MESSAGE_AR = _UNVERIFIED
    ACCESSIBILITY_TOOLS_TOGGLE = _UNVERIFIED
    SETTINGS_FORM = _UNVERIFIED  # presence = the page actually loaded (contrast with Access Denied)

    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"AccessibilitySettingsPage.{name} is an unverified placeholder — run "
                f"tools/extract_locators.py against the live page (as an admin who CAN "
                f"reach it) and replace it before running this test."
            )

    def open_settings(self) -> "AccessibilitySettingsPage":
        self._require_verified(self.SETTINGS_PATH, "SETTINGS_PATH")
        self.open(control_panel_url(self.SETTINGS_PATH))
        return self

    def _denial_locator(self, locale: str = "en") -> str:
        name = "ACCESS_DENIED_MESSAGE_AR" if locale == "ar" else "ACCESS_DENIED_MESSAGE_EN"
        locator = getattr(self, name)
        self._require_verified(locator, name)
        return locator

    def wait_for_denial(self, locale: str = "en", timeout: int = 10000) -> None:
        """Positive ANCHOR for the denial state — call this BEFORE any negative
        assertion (form absent / toggle absent). BasePage.is_visible() is
        zero-wait by design, so asserting `not settings_form_loaded()` straight
        after navigation is a race: it can pass simply because nothing has
        rendered yet. Waiting for the denial message first proves the page
        reached a terminal state, which makes the negatives meaningful."""
        self.wait_for(self._denial_locator(locale), timeout=timeout)

    def access_denied_shown(self, locale: str = "en") -> bool:
        return self.is_visible(self._denial_locator(locale))

    def denial_text(self, locale: str = "en") -> str:
        return self.text(self._denial_locator(locale))

    def settings_form_loaded(self) -> bool:
        self._require_verified(self.SETTINGS_FORM, "SETTINGS_FORM")
        return self.is_visible(self.SETTINGS_FORM)

    def accessibility_toggle_visible(self) -> bool:
        self._require_verified(self.ACCESSIBILITY_TOOLS_TOGGLE, "ACCESSIBILITY_TOOLS_TOGGLE")
        return self.is_visible(self.ACCESSIBILITY_TOOLS_TOGGLE)

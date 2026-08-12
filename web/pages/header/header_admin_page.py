"""
web/pages/header/header_admin_page.py — HeaderAdminPage.

CMS/Control-Panel side shared by both header-widget PBIs: PBI 133380
("QC-GBL-002 — Language Switcher") and PBI 133381 ("QC-GBL-003 —
Accessibility Tools"). Both toggles live under the same Liferay Global
Components -> Header Management screen (mirrors FooterAdminPage's role for
the footer PBI), plus the Accessibility PBI's media-library alt-text
validation, which lives in Liferay's image editor, not the header screen
itself, but is grouped here because both are CMS-only controls this backlog
references and neither has a public-page equivalent to extract from.

Locator status — TODO(locator), disclosed exception (identical to
FooterAdminPage's): this admin UI sits behind Liferay Control Panel
authentication and no credentials were available in this session, so
`tools/extract_locators.py` and the Playwright-MCP fallback could not reach
it (extraction requires either a logged-in session or a `--storage-state`
captured via `tools/save_auth.py`, neither of which exists yet). Every field
constant below is a named placeholder, not a guessed selector.

Once credentials are available: run `tools/save_auth.py` to capture
`.auth/state.json` for a Site Content Editor session, then re-run
`tools/extract_locators.py --url <control-panel-url> --storage-state .auth/state.json`
against the Header Management and Accessibility Settings screens (and the
media-library image editor for the alt-text fields) and replace every
`TODO(locator)` below with the real selector in one pass.
"""

from core.web.base_page import BasePage

CONTROL_PANEL_BASE = "TODO(locator)"  # Liferay Control Panel base URL — needs an authed session


class HeaderAdminPage(BasePage):
    # ---- Entry points (Control Panel navigation) ----------------------
    HEADER_MANAGEMENT_NAV = "TODO(locator)"        # Global Components -> Header Management
    ACCESSIBILITY_SETTINGS_NAV = "TODO(locator)"    # Header Management -> Accessibility Settings
    MEDIA_LIBRARY_NAV = "TODO(locator)"             # Media Library (image editor host)

    # ---- Generic controls ----------------------------------------------
    PUBLISH_BUTTON = "TODO(locator)"
    SAVE_AND_PUBLISH_BUTTON = "TODO(locator)"
    TOAST_MESSAGE = "TODO(locator)"
    ACCESS_DENIED_MESSAGE = "TODO(locator)"

    # ---- Language Switcher (PBI 133380) ---------------------------------
    LANGUAGE_SWITCHER_ENABLED_TOGGLE = "TODO(locator)"

    # ---- Accessibility Tools (PBI 133381) --------------------------------
    ACCESSIBILITY_TOOLS_ENABLED_TOGGLE = "TODO(locator)"

    # ---- Media Library: Image alt text (Accessibility compliance) ------
    IMAGE_UPLOAD_INPUT = "TODO(locator)"
    ALT_TEXT_EN_FIELD = "TODO(locator)"
    ALT_TEXT_AR_FIELD = "TODO(locator)"

    def _error_locator_for(self, field_constant: str) -> str:
        return f"{field_constant} ~ .lfr-form-field-error, {field_constant} ~ .taglib-error"

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def open_header_management(self) -> "HeaderAdminPage":
        self.click(self.HEADER_MANAGEMENT_NAV)
        return self

    def open_accessibility_settings(self) -> "HeaderAdminPage":
        self.click(self.ACCESSIBILITY_SETTINGS_NAV)
        return self

    def open_media_library(self) -> "HeaderAdminPage":
        self.click(self.MEDIA_LIBRARY_NAV)
        return self

    # ------------------------------------------------------------------
    # Generic toggle / field actions
    # ------------------------------------------------------------------
    def set_toggle(self, field_constant: str, active: bool) -> "HeaderAdminPage":
        loc = self.page.locator(field_constant)
        is_on = loc.is_checked()
        if is_on != active:
            self.click(field_constant)
        return self

    def is_toggle_active(self, field_constant: str) -> bool:
        return self.page.locator(field_constant).is_checked()

    def fill_field(self, field_constant: str, value: str) -> "HeaderAdminPage":
        self.type(field_constant, value)
        return self

    def clear_field(self, field_constant: str) -> "HeaderAdminPage":
        self.type(field_constant, "")
        return self

    def upload_image(self, file_path: str) -> "HeaderAdminPage":
        self.page.locator(self.IMAGE_UPLOAD_INPUT).set_input_files(file_path)
        return self

    def field_value(self, field_constant: str) -> str:
        return self.page.locator(field_constant).input_value()

    def field_error_text(self, field_constant: str) -> str:
        return self.text(self._error_locator_for(field_constant))

    def is_field_readonly(self, field_constant: str) -> bool:
        return self.page.locator(field_constant).is_disabled() or bool(
            self.page.locator(field_constant).get_attribute("readonly")
        )

    def is_control_exposed(self, field_constant: str) -> bool:
        return self.is_visible(field_constant)

    # ------------------------------------------------------------------
    # Publish lifecycle
    # ------------------------------------------------------------------
    def click_save_and_publish(self) -> "HeaderAdminPage":
        self.click(self.SAVE_AND_PUBLISH_BUTTON)
        return self

    def click_publish(self) -> "HeaderAdminPage":
        self.click(self.PUBLISH_BUTTON)
        return self

    def toast_message(self) -> str:
        return self.text(self.TOAST_MESSAGE)

    def access_denied_message(self) -> str:
        return self.text(self.ACCESS_DENIED_MESSAGE)

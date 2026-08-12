"""
web/pages/footer/footer_admin_page.py — FooterAdminPage.

CMS/Control-Panel side of PBI 133231: Liferay's Footer Management,
Useful Links Manager, and Social Media Icons Management screens.

Locator status — TODO(locator), disclosed exception:
This admin UI sits behind Liferay authentication (Control Panel login) and
no credentials were available in this session, so `tools/extract_locators.py`
and the Playwright-MCP fallback both could not reach it (extraction requires
either a logged-in session or a `--storage-state` captured via
`tools/save_auth.py`, neither of which exists yet). Per automation-standards.md
("TODO(locator) is only for a genuinely unreachable app") and the task's own
explicit exception, every field constant below is a named placeholder, not a
guessed selector — nothing here was invented as if it were real.

Once credentials are available: run `tools/save_auth.py` to capture
`.auth/state.json` for a Site Content Editor session, then re-run
`tools/extract_locators.py --url <control-panel-url> --storage-state .auth/state.json`
against each of the three admin screens and replace the `TODO(locator)`
strings in FIELDS/CONTROLS below with the real selectors in one pass — do not
re-open this file piecemeal per field.

Field-key design: rather than 55+ one-off methods, each CMS field is a named
constant (a semantic key, e.g. `FOOTER_LOGO_ALT_TEXT_EN`) that indexes into
the `FIELDS` locator table. Tests reference the semantic constant only —
never a raw selector — satisfying "no locators in tests" the same way a
parametrized Page-Object locator (e.g. `footer_link_locator(text)`) does.
"""

from core.web.base_page import BasePage

CONTROL_PANEL_BASE = "TODO(locator)"  # Liferay Control Panel base URL — needs an authed session


class FooterAdminPage(BasePage):
    # ---- Entry points (Control Panel navigation) ----------------------
    FOOTER_MANAGEMENT_NAV = "TODO(locator)"          # Footer Management menu entry
    USEFUL_LINKS_MANAGER_NAV = "TODO(locator)"        # Useful Links Manager menu entry
    SOCIAL_MEDIA_ICONS_MANAGER_NAV = "TODO(locator)"  # Social Media Icons Management menu entry

    # ---- Generic controls ----------------------------------------------
    PUBLISH_BUTTON = "TODO(locator)"
    DRAFT_SAVE_BUTTON = "TODO(locator)"
    PREVIEW_BUTTON = "TODO(locator)"
    UNPUBLISH_BUTTON = "TODO(locator)"
    TOAST_MESSAGE = "TODO(locator)"
    ACCESS_DENIED_MESSAGE = "TODO(locator)"

    # ---- Footer Management: Branding -----------------------------------
    FOOTER_LOGO_IMAGE_UPLOAD = "TODO(locator)"
    FOOTER_LOGO_ALT_TEXT_EN = "TODO(locator)"
    FOOTER_LOGO_ALT_TEXT_AR = "TODO(locator)"
    FOOTER_LOGO_REDIRECT_URL = "TODO(locator)"
    FOOTER_DESCRIPTION_EN = "TODO(locator)"
    FOOTER_DESCRIPTION_AR = "TODO(locator)"

    # ---- Footer Management: Social row label ----------------------------
    SOCIAL_MEDIA_LABEL_EN = "TODO(locator)"
    SOCIAL_MEDIA_LABEL_AR = "TODO(locator)"

    # ---- Footer Management: Nav columns ---------------------------------
    COLUMN_HEADING_EN = "TODO(locator)"
    COLUMN_HEADING_AR = "TODO(locator)"
    COLUMN_NUMBER_DROPDOWN = "TODO(locator)"
    COLUMN_DISPLAY_ORDER = "TODO(locator)"
    COLUMN_ACTIVE_STATUS_TOGGLE = "TODO(locator)"

    # ---- Footer Management: Nav links ------------------------------------
    NAV_LINK_TITLE_EN = "TODO(locator)"
    NAV_LINK_TITLE_AR = "TODO(locator)"
    NAV_LINK_URL = "TODO(locator)"
    NAV_LINK_OPEN_NEW_TAB_TOGGLE = "TODO(locator)"
    NAV_LINK_DISPLAY_ORDER = "TODO(locator)"
    NAV_LINK_ACTIVE_STATUS_TOGGLE = "TODO(locator)"

    # ---- Useful Links Manager: Quick Links -------------------------------
    QUICK_LINKS_COLUMN_HEADING_EN = "TODO(locator)"
    QUICK_LINKS_COLUMN_HEADING_AR = "TODO(locator)"
    QUICK_LINK_TITLE_EN = "TODO(locator)"
    QUICK_LINK_TITLE_AR = "TODO(locator)"
    QUICK_LINK_URL = "TODO(locator)"
    QUICK_LINK_OPEN_NEW_TAB_TOGGLE = "TODO(locator)"
    QUICK_LINK_DISPLAY_ORDER = "TODO(locator)"
    QUICK_LINK_ACTIVE_STATUS_TOGGLE = "TODO(locator)"

    # ---- Social Media Icons Management ------------------------------------
    PLATFORM_NAME = "TODO(locator)"
    SOCIAL_ICON_IMAGE_UPLOAD = "TODO(locator)"
    ICON_ALT_TEXT_EN = "TODO(locator)"
    ICON_ALT_TEXT_AR = "TODO(locator)"
    SOCIAL_REDIRECT_URL = "TODO(locator)"
    SOCIAL_ICON_OPEN_NEW_TAB_FIELD = "TODO(locator)"  # read-only, fixed true (GLOBAL-FOOTER-TC-095)
    SOCIAL_ICON_DISPLAY_ORDER = "TODO(locator)"
    SOCIAL_ICON_ACTIVE_STATUS_TOGGLE = "TODO(locator)"

    # ---- Footer Management: Newsletter --------------------------------------
    NEWSLETTER_HEADING_EN = "TODO(locator)"
    NEWSLETTER_HEADING_AR = "TODO(locator)"
    NEWSLETTER_DESCRIPTION_EN = "TODO(locator)"
    NEWSLETTER_DESCRIPTION_AR = "TODO(locator)"
    EMAIL_PLACEHOLDER_EN = "TODO(locator)"
    EMAIL_PLACEHOLDER_AR = "TODO(locator)"
    SUBSCRIBE_BUTTON_LABEL_EN = "TODO(locator)"
    SUBSCRIBE_BUTTON_LABEL_AR = "TODO(locator)"

    # ---- Footer Management: Copyright bar -----------------------------------
    COPYRIGHT_TEXT_EN = "TODO(locator)"
    COPYRIGHT_TEXT_AR = "TODO(locator)"
    COPYRIGHT_ACTIVE_STATUS_TOGGLE = "TODO(locator)"
    BOTTOM_LINK_TITLE_EN = "TODO(locator)"
    BOTTOM_LINK_TITLE_AR = "TODO(locator)"
    BOTTOM_LINK_URL = "TODO(locator)"
    BOTTOM_LINK_DISPLAY_ORDER = "TODO(locator)"
    BOTTOM_LINK_ACTIVE_STATUS_TOGGLE = "TODO(locator)"

    # Per-field validation error locator is derived from the field's own
    # locator (Liferay renders the message immediately below the field) —
    # no separate constant needed once the real selector lands.
    def _error_locator_for(self, field_constant: str) -> str:
        return f"{field_constant} ~ .lfr-form-field-error, {field_constant} ~ .taglib-error"

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def open_footer_management(self) -> "FooterAdminPage":
        self.click(self.FOOTER_MANAGEMENT_NAV)
        return self

    def open_useful_links_manager(self) -> "FooterAdminPage":
        self.click(self.USEFUL_LINKS_MANAGER_NAV)
        return self

    def open_social_media_icons_management(self) -> "FooterAdminPage":
        self.click(self.SOCIAL_MEDIA_ICONS_MANAGER_NAV)
        return self

    # ------------------------------------------------------------------
    # Generic field actions — field_constant is one of the named
    # locator constants above (never a raw selector at the call site).
    # ------------------------------------------------------------------
    def fill_field(self, field_constant: str, value: str) -> "FooterAdminPage":
        self.type(field_constant, value)
        return self

    def clear_field(self, field_constant: str) -> "FooterAdminPage":
        self.type(field_constant, "")
        return self

    def upload_file(self, field_constant: str, file_path: str) -> "FooterAdminPage":
        self.page.locator(field_constant).set_input_files(file_path)
        return self

    def select_option(self, field_constant: str, value: str) -> "FooterAdminPage":
        self.page.locator(field_constant).select_option(label=value)
        return self

    def set_toggle(self, field_constant: str, active: bool) -> "FooterAdminPage":
        loc = self.page.locator(field_constant)
        is_on = loc.is_checked()
        if is_on != active:
            self.click(field_constant)
        return self

    def field_value(self, field_constant: str) -> str:
        return self.page.locator(field_constant).input_value()

    def field_error_text(self, field_constant: str) -> str:
        return self.text(self._error_locator_for(field_constant))

    def is_field_readonly(self, field_constant: str) -> bool:
        return self.page.locator(field_constant).is_disabled() or bool(
            self.page.locator(field_constant).get_attribute("readonly")
        )

    def is_toggle_exposed(self, field_constant: str) -> bool:
        return self.is_visible(field_constant)

    # ------------------------------------------------------------------
    # Publish lifecycle
    # ------------------------------------------------------------------
    def click_publish(self) -> "FooterAdminPage":
        self.click(self.PUBLISH_BUTTON)
        return self

    def save_draft(self) -> "FooterAdminPage":
        self.click(self.DRAFT_SAVE_BUTTON)
        return self

    def click_preview(self) -> "FooterAdminPage":
        self.click(self.PREVIEW_BUTTON)
        return self

    def click_unpublish(self) -> "FooterAdminPage":
        self.click(self.UNPUBLISH_BUTTON)
        return self

    def toast_message(self) -> str:
        return self.text(self.TOAST_MESSAGE)

    def access_denied_message(self) -> str:
        return self.text(self.ACCESS_DENIED_MESSAGE)

"""
web/pages/components/footer_admin_component.py — FooterAdminComponent.

PBI 129366 / QC-GBL-004 "Site Footer & Social Media Icons" — Control_Panel-
tagged cases (ADO 130977-130987, 130990, 130995): Footer Management (logo,
nav columns, newsletter fields, copyright/bottom-bar links), the Useful
Links Manager (Quick Links column content), and Social Media Icons
Management. Sibling of footer_component.py (the public Web-platform Page
Object for this same PBI). Composes the shared web/pages/components/
cms_login_page.py for the login step, per this task's own instruction (reuse
established from PBI 129390/129382, never re-author login locators).

STATUS: BLOCKED, not guessed (2026-08-25) — same situation this project's own
git history already documented for PBI 129382's HomeFeaturedEventAdminPage
and PBI 129390's Control_Panel cases. Login itself is real and CLI-confirmed
(the shared CmsLoginPage's docstring re-confirmed the anonymous
/c/portal/login form live on 2026-08-24) — everything PAST login on THIS
page (Global Components > Footer Management, the Useful Links Manager, and
Social Media Icons Management screens; every field, toggle, Save button, and
validation message on them) is BLOCKED: TEST_USER/TEST_PASSWORD are both
blank in .env (see cms_login_page.py's docstring) and no Playwright MCP
fallback is available in this environment to step through it interactively
either.

Every locator below is the literal TODO placeholder string (never a
guessed-but-plausible Liferay selector) — the same convention this project's
own git history already established for exactly this situation (commit
2cbbb4c's predecessor "_UNVERIFIED" gate; test_home_featured_event_control_panel.py's
`_UNRESOLVED` collection-time skipif gate, reproduced identically in the
sibling test_footer_control_panel.py). Replace only after a real
authenticated Site Content Editor session confirms the real screens live via
`tools/extract_locators.py --storage-state .auth/state.json` (once
`tools/save_auth.py` has a working Control Panel login to capture) — never
mark this file "done" by guessing a plausible-looking Liferay fragment-
configuration class name.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_TODO_PREFIX = "TODO:"


def _todo(what: str) -> str:
    return f"{_TODO_PREFIX} run tools/extract_locators.py (as an authenticated Site Content Editor) against the live screen and paste the confirmed selector for {what}"


class FooterAdminComponent(BasePage):
    # ── Entry points — unreachable without an authenticated session, see docstring ──
    FOOTER_MANAGEMENT_LINK = _todo("the 'Footer Management' nav item under Global Components")
    FOOTER_MANAGEMENT_SCREEN = _todo("the Footer Management screen's own container")
    USEFUL_LINKS_MANAGER_LINK = _todo("the 'Useful Links Manager' nav item under Global Components")
    USEFUL_LINKS_MANAGER_SCREEN = _todo("the Useful Links Manager screen's own container")
    SOCIAL_ICONS_MANAGEMENT_LINK = _todo("the 'Social Media Icons Management' nav item under Global Components")
    SOCIAL_ICONS_MANAGEMENT_SCREEN = _todo("the Social Media Icons Management screen's own container")

    # ── Shared across every sub-screen ──────────────────────────────────
    SAVE_BUTTON = _todo("the active form's Save button")
    SUCCESS_TOAST = _todo("the Liferay generic success toast/notification")
    REQUIRED_FIELD_ERROR = _todo("the inline required-field validation message")
    URL_FORMAT_ERROR = _todo("the inline invalid-URL-format validation message")

    # ── Footer Management: logo (ADO 130977, 130978) ─────────────────────
    LOGO_UPLOAD_INPUT = _todo("the Footer Logo Image upload control")
    LOGO_ALT_EN_INPUT = _todo("the Logo Alt Text (EN) field")
    LOGO_ALT_AR_INPUT = _todo("the Logo Alt Text (AR) field")
    LOGO_REDIRECT_URL_INPUT = _todo("the Logo Redirect URL field")

    # ── Footer Management: nav columns (ADO 130979, 130980) ──────────────
    ADD_NAV_COLUMN_BUTTON = _todo("the 'Add Column' button")
    NAV_COLUMN_HEADING_EN_INPUT = _todo("a nav column's Heading (EN) field")
    NAV_COLUMN_HEADING_AR_INPUT = _todo("a nav column's Heading (AR) field")
    NAV_COLUMN_NUMBER_INPUT = _todo("a nav column's Column Number field")
    NAV_COLUMN_DISPLAY_ORDER_INPUT = _todo("a nav column's Display Order field")
    NAV_COLUMN_ACTIVE_TOGGLE = _todo("a nav column's Active Status toggle")

    # ── Useful Links Manager: Quick Links (ADO 130981, 130982, 130990) ───
    QUICK_LINKS_HEADING_EN_INPUT = _todo("the Quick Links column Heading (EN) field")
    QUICK_LINKS_HEADING_AR_INPUT = _todo("the Quick Links column Heading (AR) field")
    ADD_QUICK_LINK_BUTTON = _todo("the 'Add Quick Link' button")
    QUICK_LINK_TITLE_EN_INPUT = _todo("a quick link's Title (EN) field")
    QUICK_LINK_TITLE_AR_INPUT = _todo("a quick link's Title (AR) field")
    QUICK_LINK_URL_INPUT = _todo("a quick link's URL field")
    QUICK_LINK_NEW_TAB_TOGGLE = _todo("a quick link's Open in New Tab toggle")
    QUICK_LINK_DISPLAY_ORDER_INPUT = _todo("a quick link's Display Order field")
    QUICK_LINK_ACTIVE_TOGGLE = _todo("a quick link's Active Status toggle")

    # ── Social Media Icons Management (ADO 130983, 130984, 130985) ───────
    ADD_SOCIAL_ICON_BUTTON = _todo("the 'Add Social Icon' button")
    SOCIAL_ICON_PLATFORM_NAME_INPUT = _todo("a social icon's Platform Name field")
    SOCIAL_ICON_IMAGE_UPLOAD_INPUT = _todo("a social icon's Icon Image upload control")
    SOCIAL_ICON_ALT_EN_INPUT = _todo("a social icon's Alt Text (EN) field")
    SOCIAL_ICON_ALT_AR_INPUT = _todo("a social icon's Alt Text (AR) field")
    SOCIAL_ICON_REDIRECT_URL_INPUT = _todo("a social icon's Redirect URL field")
    SOCIAL_ICON_NEW_TAB_TOGGLE = _todo("a social icon's Open in New Tab toggle")
    SOCIAL_ICON_DISPLAY_ORDER_INPUT = _todo("a social icon's Display Order field")
    SOCIAL_ICON_ACTIVE_TOGGLE = _todo("a social icon's Active Status toggle")

    # ── Footer Management: newsletter fields (ADO 130986) ────────────────
    NEWSLETTER_HEADING_EN_INPUT = _todo("the Newsletter Heading (EN) field")
    NEWSLETTER_HEADING_AR_INPUT = _todo("the Newsletter Heading (AR) field")
    NEWSLETTER_DESCRIPTION_EN_INPUT = _todo("the Newsletter Description (EN) field")
    NEWSLETTER_DESCRIPTION_AR_INPUT = _todo("the Newsletter Description (AR) field")
    NEWSLETTER_EMAIL_PLACEHOLDER_EN_INPUT = _todo("the Newsletter Email Placeholder (EN) field")
    NEWSLETTER_EMAIL_PLACEHOLDER_AR_INPUT = _todo("the Newsletter Email Placeholder (AR) field")
    NEWSLETTER_SUBSCRIBE_LABEL_EN_INPUT = _todo("the Newsletter Subscribe Button Label (EN) field")
    NEWSLETTER_SUBSCRIBE_LABEL_AR_INPUT = _todo("the Newsletter Subscribe Button Label (AR) field")

    # ── Footer Management: copyright & bottom bar (ADO 130987) ───────────
    COPYRIGHT_TEXT_EN_INPUT = _todo("the Copyright Text (EN) field")
    COPYRIGHT_TEXT_AR_INPUT = _todo("the Copyright Text (AR) field")
    COPYRIGHT_ACTIVE_TOGGLE = _todo("the Copyright Text Active Status toggle")
    ADD_BOTTOM_BAR_LINK_BUTTON = _todo("the 'Add Bottom Bar Link' button")
    BOTTOM_BAR_LINK_TITLE_INPUT = _todo("a bottom bar link's Title field")
    BOTTOM_BAR_LINK_URL_INPUT = _todo("a bottom bar link's URL field")
    BOTTOM_BAR_LINK_NEW_TAB_TOGGLE = _todo("a bottom bar link's Open in New Tab toggle")
    BOTTOM_BAR_LINK_DISPLAY_ORDER_INPUT = _todo("a bottom bar link's Display Order field")
    BOTTOM_BAR_LINK_ACTIVE_TOGGLE = _todo("a bottom bar link's Active Status toggle")

    # ── Navigation ───────────────────────────────────────────────────────
    def open_control_panel_home(self) -> "FooterAdminComponent":
        self.open(control_panel_url("/group/qatar-chamber"))
        return self

    def navigate_to_footer_management(self) -> "FooterAdminComponent":
        self.click(self.FOOTER_MANAGEMENT_LINK)
        self.wait_for(self.FOOTER_MANAGEMENT_SCREEN)
        return self

    def navigate_to_useful_links_manager(self) -> "FooterAdminComponent":
        self.click(self.USEFUL_LINKS_MANAGER_LINK)
        self.wait_for(self.USEFUL_LINKS_MANAGER_SCREEN)
        return self

    def navigate_to_social_icons_management(self) -> "FooterAdminComponent":
        self.click(self.SOCIAL_ICONS_MANAGEMENT_LINK)
        self.wait_for(self.SOCIAL_ICONS_MANAGEMENT_SCREEN)
        return self

    # ── State queries — no asserts, tests do the asserting ──────────────
    def is_footer_management_screen_visible(self) -> bool:
        return self.is_visible(self.FOOTER_MANAGEMENT_SCREEN)

    def is_useful_links_manager_screen_visible(self) -> bool:
        return self.is_visible(self.USEFUL_LINKS_MANAGER_SCREEN)

    def is_social_icons_management_screen_visible(self) -> bool:
        return self.is_visible(self.SOCIAL_ICONS_MANAGEMENT_SCREEN)

    def is_success_toast_visible(self) -> bool:
        return self.is_visible(self.SUCCESS_TOAST)

    def success_toast_text(self) -> str:
        return self.text(self.SUCCESS_TOAST)

    def is_required_field_error_visible(self) -> bool:
        return self.is_visible(self.REQUIRED_FIELD_ERROR)

    def required_field_error_text(self) -> str:
        return self.text(self.REQUIRED_FIELD_ERROR)

    def is_url_format_error_visible(self) -> bool:
        return self.is_visible(self.URL_FORMAT_ERROR)

    def url_format_error_text(self) -> str:
        return self.text(self.URL_FORMAT_ERROR)

    def click_save(self) -> "FooterAdminComponent":
        self.click(self.SAVE_BUTTON)
        return self

    # ── Footer logo (ADO 130977, 130978) ─────────────────────────────────
    def upload_logo(self, file_path: str, alt_en: str, alt_ar: str, redirect_url: str) -> "FooterAdminComponent":
        self.page.locator(self.LOGO_UPLOAD_INPUT).set_input_files(file_path)
        self.type(self.LOGO_ALT_EN_INPUT, alt_en)
        self.type(self.LOGO_ALT_AR_INPUT, alt_ar)
        self.type(self.LOGO_REDIRECT_URL_INPUT, redirect_url)
        return self

    # ── Nav columns (ADO 130979, 130980, 130995) ──────────────────────────
    def open_add_nav_column_form(self) -> "FooterAdminComponent":
        self.click(self.ADD_NAV_COLUMN_BUTTON)
        return self

    def enter_nav_column_heading_en(self, heading_en: str) -> "FooterAdminComponent":
        self.type(self.NAV_COLUMN_HEADING_EN_INPUT, heading_en)
        return self

    def enter_nav_column_heading_ar(self, heading_ar: str) -> "FooterAdminComponent":
        self.type(self.NAV_COLUMN_HEADING_AR_INPUT, heading_ar)
        return self

    def add_nav_column(self, heading_en: str, heading_ar: str, column_number: str, display_order: str) -> "FooterAdminComponent":
        self.open_add_nav_column_form()
        self.enter_nav_column_heading_en(heading_en)
        self.enter_nav_column_heading_ar(heading_ar)
        self.type(self.NAV_COLUMN_NUMBER_INPUT, column_number)
        self.type(self.NAV_COLUMN_DISPLAY_ORDER_INPUT, display_order)
        return self

    def set_nav_column_display_order(self, display_order: str) -> "FooterAdminComponent":
        self.type(self.NAV_COLUMN_DISPLAY_ORDER_INPUT, display_order)
        return self

    # ── Useful Links Manager / Quick Links (ADO 130981, 130982, 130990) ──
    def set_quick_links_heading(self, heading_en: str, heading_ar: str) -> "FooterAdminComponent":
        self.type(self.QUICK_LINKS_HEADING_EN_INPUT, heading_en)
        self.type(self.QUICK_LINKS_HEADING_AR_INPUT, heading_ar)
        return self

    def open_add_quick_link_form(self) -> "FooterAdminComponent":
        self.click(self.ADD_QUICK_LINK_BUTTON)
        return self

    def enter_quick_link_url(self, url: str) -> "FooterAdminComponent":
        self.type(self.QUICK_LINK_URL_INPUT, url)
        return self

    def add_quick_link(self, title_en: str, title_ar: str, url: str, open_new_tab: bool, display_order: str) -> "FooterAdminComponent":
        self.open_add_quick_link_form()
        self.type(self.QUICK_LINK_TITLE_EN_INPUT, title_en)
        self.type(self.QUICK_LINK_TITLE_AR_INPUT, title_ar)
        self.enter_quick_link_url(url)
        is_checked = self.page.locator(self.QUICK_LINK_NEW_TAB_TOGGLE).is_checked()
        if is_checked != open_new_tab:
            self.click(self.QUICK_LINK_NEW_TAB_TOGGLE)
        self.type(self.QUICK_LINK_DISPLAY_ORDER_INPUT, display_order)
        return self

    # ── Social Media Icons Management (ADO 130983, 130984, 130985) ───────
    def open_add_social_icon_form(self) -> "FooterAdminComponent":
        self.click(self.ADD_SOCIAL_ICON_BUTTON)
        return self

    def add_social_icon(self, platform_name: str, image_path: str, alt_en: str, alt_ar: str,
                         redirect_url: str, open_new_tab: bool, display_order: str) -> "FooterAdminComponent":
        self.open_add_social_icon_form()
        self.type(self.SOCIAL_ICON_PLATFORM_NAME_INPUT, platform_name)
        self.page.locator(self.SOCIAL_ICON_IMAGE_UPLOAD_INPUT).set_input_files(image_path)
        self.type(self.SOCIAL_ICON_ALT_EN_INPUT, alt_en)
        self.type(self.SOCIAL_ICON_ALT_AR_INPUT, alt_ar)
        self.type(self.SOCIAL_ICON_REDIRECT_URL_INPUT, redirect_url)
        is_checked = self.page.locator(self.SOCIAL_ICON_NEW_TAB_TOGGLE).is_checked()
        if is_checked != open_new_tab:
            self.click(self.SOCIAL_ICON_NEW_TAB_TOGGLE)
        self.type(self.SOCIAL_ICON_DISPLAY_ORDER_INPUT, display_order)
        return self

    # ── Newsletter fields (ADO 130986) ────────────────────────────────────
    def set_newsletter_fields(self, heading_en: str, heading_ar: str, description_en: str, description_ar: str,
                               email_placeholder_en: str, email_placeholder_ar: str,
                               subscribe_label_en: str, subscribe_label_ar: str) -> "FooterAdminComponent":
        self.type(self.NEWSLETTER_HEADING_EN_INPUT, heading_en)
        self.type(self.NEWSLETTER_HEADING_AR_INPUT, heading_ar)
        self.type(self.NEWSLETTER_DESCRIPTION_EN_INPUT, description_en)
        self.type(self.NEWSLETTER_DESCRIPTION_AR_INPUT, description_ar)
        self.type(self.NEWSLETTER_EMAIL_PLACEHOLDER_EN_INPUT, email_placeholder_en)
        self.type(self.NEWSLETTER_EMAIL_PLACEHOLDER_AR_INPUT, email_placeholder_ar)
        self.type(self.NEWSLETTER_SUBSCRIBE_LABEL_EN_INPUT, subscribe_label_en)
        self.type(self.NEWSLETTER_SUBSCRIBE_LABEL_AR_INPUT, subscribe_label_ar)
        return self

    # ── Copyright & bottom bar (ADO 130987) ───────────────────────────────
    def set_copyright_text(self, text_en: str, text_ar: str, active: bool = True) -> "FooterAdminComponent":
        self.type(self.COPYRIGHT_TEXT_EN_INPUT, text_en)
        self.type(self.COPYRIGHT_TEXT_AR_INPUT, text_ar)
        is_checked = self.page.locator(self.COPYRIGHT_ACTIVE_TOGGLE).is_checked()
        if is_checked != active:
            self.click(self.COPYRIGHT_ACTIVE_TOGGLE)
        return self

    def add_bottom_bar_link(self, title: str, url: str, open_new_tab: bool, display_order: str) -> "FooterAdminComponent":
        self.click(self.ADD_BOTTOM_BAR_LINK_BUTTON)
        self.type(self.BOTTOM_BAR_LINK_TITLE_INPUT, title)
        self.type(self.BOTTOM_BAR_LINK_URL_INPUT, url)
        is_checked = self.page.locator(self.BOTTOM_BAR_LINK_NEW_TAB_TOGGLE).is_checked()
        if is_checked != open_new_tab:
            self.click(self.BOTTOM_BAR_LINK_NEW_TAB_TOGGLE)
        self.type(self.BOTTOM_BAR_LINK_DISPLAY_ORDER_INPUT, display_order)
        return self

"""
web/pages/home_quick_contact/home_quick_contact_admin_page.py —
HomeQuickContactAdminPage.

PBI 129390 / QC-HOME-014 "Quick Contact Us Section" — Control_Panel-tagged
cases (ADO TC 136480, 136551): the CMS "Contact Us Section Management"
screen's field inventory, and its Arabic/RTL rendering. Sibling of
home_quick_contact_page.py (the public Web-platform Page Object for this
same PBI).

STATUS: BLOCKED (2026-08-25), same real, confirmed limitation already
documented for this project's other Control_Panel Page Objects (see
web/pages/home_featured_event/home_featured_event_admin_page.py,
2026-08-24): login itself is real and CLI-confirmed (see the shared
web/pages/components/cms_login_page.py this Page Object composes) — the
anonymous /c/portal/login form is reachable without credentials. Everything
PAST login on THIS screen (Home Page management navigation, the Contact Us
Section Management screen itself, and every one of its configuration
fields/actions) is BLOCKED, not guessed: reaching it requires an actual
authenticated Site Content Editor session, and TEST_USER/TEST_PASSWORD are
still blank in .env this session (re-confirmed 2026-08-25 — no change since
the 2026-08-24 pass), and no Playwright MCP fallback is available in this
environment to step through it interactively either.

Every locator below is the literal TODO placeholder string (never a
guessed-but-plausible selector) — the same convention this project's own
git history already established for exactly this situation (commit 2cbbb4c's
predecessor "_UNVERIFIED" gate; home_featured_event_admin_page.py's
`_TODO_PREFIX` convention, reproduced here unchanged).

Replace only after confirming the real Contact Us Section Management screen
live — never mark this file "done" by guessing a plausible-looking Liferay
fragment-configuration class name.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_TODO_PREFIX = "TODO:"


def _todo(what: str) -> str:
    return f"{_TODO_PREFIX} run tools/extract_locators.py (as an authenticated Site Content Editor) against the live Contact Us Section Management screen and paste the confirmed selector for {what}"


class HomeQuickContactAdminPage(BasePage):
    # ── Unreachable without an authenticated session this run — see docstring ──
    HOME_PAGE_MANAGEMENT_LINK = _todo("the 'Home Page management' nav item")
    CONTACT_US_SECTION_MANAGEMENT_LINK = _todo("the 'Contact Us Section Management' entry point")
    MANAGEMENT_SCREEN = _todo("the Contact Us Section Management screen's own container")
    SECTION_TAG_HEADING_INPUT = _todo("the Section Tag/Heading (EN) input")
    SECTION_HEADING_AR_INPUT = _todo("the Section Heading (AR) input")
    SECTION_DESCRIPTION_EN_INPUT = _todo("the Section Description (EN) input")
    SECTION_DESCRIPTION_AR_INPUT = _todo("the Section Description (AR) input")
    EMAIL_SUPPORT_ADDRESS_INPUT = _todo("the Email Support Address input")
    TELEPHONE_INPUT = _todo("the Telephone input")
    LOCATION_ADDRESS_EN_INPUT = _todo("the Location Address (EN) input")
    LOCATION_ADDRESS_AR_INPUT = _todo("the Location Address (AR) input")
    MAP_EMBED_URL_INPUT = _todo("the Map Embed URL input")
    INQUIRY_CATEGORY_GRID = _todo("the Inquiry Category grid/list control")
    RECIPIENT_EMAILS_INPUT = _todo("the Recipient Email(s) input")
    BUTTON_LABEL_EN_INPUT = _todo("the Button Label (EN) input")
    BUTTON_LABEL_AR_INPUT = _todo("the Button Label (AR) input")
    SAVE_DRAFT_BUTTON = _todo("the Save Draft action")
    PREVIEW_BUTTON = _todo("the Preview action")
    PUBLISH_BUTTON = _todo("the Publish action")
    UNPUBLISH_BUTTON = _todo("the Unpublish action")
    MANAGEMENT_FORM = _todo("the Management screen's own form/root element (for RTL/direction checks)")

    def open_control_panel_home(self) -> "HomeQuickContactAdminPage":
        self.open(control_panel_url("/group/qatar-chamber"))
        return self

    def navigate_to_home_page_management(self) -> "HomeQuickContactAdminPage":
        self.click(self.HOME_PAGE_MANAGEMENT_LINK)
        return self

    def open_contact_us_section_management(self) -> "HomeQuickContactAdminPage":
        self.click(self.CONTACT_US_SECTION_MANAGEMENT_LINK)
        self.wait_for(self.MANAGEMENT_SCREEN)
        return self

    # ── State queries — no asserts, tests do the asserting ──────────────
    def is_management_screen_visible(self) -> bool:
        return self.is_visible(self.MANAGEMENT_SCREEN)

    def visible_field_map(self) -> dict:
        """Returns a name -> visible bool map of every configuration field
        the case names, for one combined readability check in the test."""
        fields = {
            "section_tag_heading_en": self.SECTION_TAG_HEADING_INPUT,
            "section_heading_ar": self.SECTION_HEADING_AR_INPUT,
            "section_description_en": self.SECTION_DESCRIPTION_EN_INPUT,
            "section_description_ar": self.SECTION_DESCRIPTION_AR_INPUT,
            "email_support_address": self.EMAIL_SUPPORT_ADDRESS_INPUT,
            "telephone": self.TELEPHONE_INPUT,
            "location_address_en": self.LOCATION_ADDRESS_EN_INPUT,
            "location_address_ar": self.LOCATION_ADDRESS_AR_INPUT,
            "map_embed_url": self.MAP_EMBED_URL_INPUT,
            "inquiry_category_grid": self.INQUIRY_CATEGORY_GRID,
            "recipient_emails": self.RECIPIENT_EMAILS_INPUT,
            "button_label_en": self.BUTTON_LABEL_EN_INPUT,
            "button_label_ar": self.BUTTON_LABEL_AR_INPUT,
            "save_draft": self.SAVE_DRAFT_BUTTON,
            "preview": self.PREVIEW_BUTTON,
            "publish": self.PUBLISH_BUTTON,
            "unpublish": self.UNPUBLISH_BUTTON,
        }
        return {name: self.is_visible(loc) for name, loc in fields.items()}

    def management_form_direction(self) -> str:
        return self.page.locator(self.MANAGEMENT_FORM).evaluate("el => getComputedStyle(el).direction")

    def type_into_arabic_field(self, text: str) -> "HomeQuickContactAdminPage":
        self.type(self.SECTION_HEADING_AR_INPUT, text)
        return self

    def arabic_field_value(self) -> str:
        return self.page.locator(self.SECTION_HEADING_AR_INPUT).input_value()

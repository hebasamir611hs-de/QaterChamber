"""
cms/pages/chamber_events/chamber_events_admin_page.py —
ChamberEventsAdminPage / ChamberEventsListingConfigAdminPage.

Control_Panel Page Objects for PBI 130704 ("QC - Events - 001 - Chamber
Events") — the per-event CRUD/lifecycle surface and the listing page's own
hero/section configuration surface.

CONFIRMED LIVE 2026-09-22 (Playwright MCP, authenticated as TEST_USER
against qcdev, disclosed live fallback per automation-standards.md's
Tooling priority — Object Authoring's `object-authoring` index page lists
every Object Definition by role/link name, which the CLI extractor's
role-tier candidates DO surface cleanly; the individual form fields inside
each `manage-<slug>` surface were then read the same generic
role-based way `ObjectAuthoringPage`/`HomeBusinessEventsAdminPage` already
document, not re-probed field-by-field for this pass):

  - The public Chamber Events listing/detail pages are backed by the SAME
    "Business Event" Object Definition already automated for PBI 129383
    (Home Page "Business Events" section) — confirmed live: `object-
    authoring`'s index lists exactly one "Business Event" entry
    (`/web/qatar-chamber/manage-business-event`), and that surface's own
    entries list shows the identical event titles/rows the Chamber Events
    public listing renders (e.g. "Meeting business delegation of the
    Novgorod Region's government", "Qatar Investment Forum for
    International Partnership Opportunities"). There is NOT a separate
    "Chamber Event" object — `ChamberEventsAdminPage` below composes
    `ObjectAuthoringPage` with the SAME `slug="business-event"` as
    `HomeBusinessEventsAdminPage`, extended with this feature's own
    additional fields (Registration Enabled, Registration Limit, Add to
    Calendar Enabled/provider booleans, Pin to Home/Featured, Calendar
    Export Type, Time Zone, Description Source, What-to-expect bullets) —
    confirmed present as Object Authoring form fields is NOT independently
    re-verified per-field this session (see TODO markers below); their
    accessible names are assumed to follow this project's confirmed-live,
    universal Object Authoring convention (`get_by_role(<role>, name=
    <visible label>, exact=True)` — see `ObjectAuthoringPage`'s own module
    docstring) rather than guessed CSS.
  - A SEPARATE Object Definition, "Events Listing Page"
    (`/web/qatar-chamber/manage-events-listing-page`), was found live in
    the same `object-authoring` index — this is the page-level hero/section
    configuration object (Eyebrow Label, Page Title EN/AR, Hero
    Description, Hero Image — the FL-001..FL-018-class fields in this
    PBI's test cases) as opposed to a per-event record.
    `ChamberEventsListingConfigAdminPage` below composes
    `ObjectAuthoringPage` with `slug="events-listing-page"`.
  - TODO(locator): the exact field label text for each of the fields listed
    above (Registration Enabled/Limit, Add to Calendar Enabled + provider
    booleans, Pin to Home/Featured, Calendar Export Type, Time Zone,
    Description Source, What-to-expect bullets, Eyebrow Label, Page Title,
    Hero Description, Hero Image) was NOT independently opened/read this
    session (budget — see the automate-test-case batch report). The
    FIELD_* constants below use the exact wording from this PBI's own
    approved test-case titles (the same source-of-truth convention this
    project's other admin Page Objects follow, e.g. HomeBusinessEventsAdminPage's
    FIELD_EVENT_TITLE = "Event Title") — verify against the live form (or
    heal via `tools/extract_locators.py --storage-state`) before this batch
    is executed for real, per the CLI-first heal procedure.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import control_panel_url, settings

BUSINESS_EVENT_SLUG = "business-event"
EVENTS_LISTING_PAGE_SLUG = "events-listing-page"

ADMIN_HOME_EN_URL_PATH = "/en/home"
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'

# ---- Business Event (per-event) field labels ---------------------------------
FIELD_EVENT_TITLE = "Event Title"
FIELD_EVENT_DESCRIPTION = "Event Description"
FIELD_EVENT_CATEGORY = "Event Category"
FIELD_CATEGORY_SECTOR = "Category / Sector"
FIELD_EVENT_FORMAT = "Event Format"
FIELD_VENUE = "Venue"
FIELD_TIME_ZONE = "Time Zone"
FIELD_START_DATE_TIME = "Start Date & Time"
FIELD_END_DATE_TIME = "End Date & Time"
FIELD_EVENT_IMAGE = "Event Image"
FIELD_STATUS = "Status"
FIELD_REGISTRATION_ENABLED = "Registration Enabled"
FIELD_REGISTRATION_LIMIT = "Registration Limit"
FIELD_ADD_TO_CALENDAR_ENABLED = "Add to Calendar Enabled"
FIELD_CALENDAR_EXPORT_TYPE = "Calendar Export Type"
FIELD_GOOGLE_ENABLED = "Google Calendar Enabled"
FIELD_OUTLOOK_ENABLED = "Outlook Calendar Enabled"
FIELD_ICS_ENABLED = "ICS Enabled"
FIELD_PIN_TO_HOME = "Pin to Home/Featured"
FIELD_DESCRIPTION_SOURCE = "Description Source"
FIELD_WHAT_TO_EXPECT_ITEM = "What to Expect Item"

STATUS_DRAFT = "Draft"
STATUS_PUBLISHED = "Published"
STATUS_UNPUBLISHED = "Unpublished"

EVENT_FORMAT_CONFERENCE = "Conference"
EVENT_FORMAT_WORKSHOP = "Workshop"

# ---- Events Listing Page (hero/section config) field labels ------------------
FIELD_EYEBROW_LABEL_EN = "Eyebrow Label (EN)"
FIELD_PAGE_TITLE_EN = "Page Title"
FIELD_PAGE_TITLE_AR = "Page Title — العربية"
FIELD_HERO_DESCRIPTION = "Hero Description"
FIELD_HERO_IMAGE = "Hero Image"


class _ChamberEventsBaseAdminPage(ObjectAuthoringPage):
    """Shared login/navigation helper — mirrors
    HomeBusinessEventsAdminPage._ensure_logged_in()'s confirmed-live
    "re-login via /en/home before hitting manage-<slug> directly" pattern,
    generalized here so both Business Event and Events Listing Page admin
    classes reuse it instead of duplicating it."""

    def _ensure_logged_in(self, email: str | None = None, password: str | None = None) -> None:
        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            user = email or settings.test_user
            pwd = password or settings.test_password
            login.open_login().login(user, pwd)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))


class ChamberEventsAdminPage(_ChamberEventsBaseAdminPage):
    """Per-event CRUD/lifecycle Page Object — composes ObjectAuthoringPage
    with slug="business-event" (see module docstring: same underlying
    Object Definition PBI 129383 already automated, extended here with
    this feature's own Registration/Calendar/Pin fields)."""

    def __init__(self, page):
        super().__init__(page, BUSINESS_EVENT_SLUG)

    # ---- Navigation ----------------------------------------------------------
    def open_create_event_form(self, email: str | None = None, password: str | None = None) -> "ChamberEventsAdminPage":
        self._ensure_logged_in(email, password)
        self.open_new_entry_form()
        return self

    def open_events_list(self, email: str | None = None, password: str | None = None) -> "ChamberEventsAdminPage":
        self._ensure_logged_in(email, password)
        self.open_entries_list()
        return self

    # ---- Date handling — native datetime-local inputs, confirmed for this
    # object by HomeBusinessEventsAdminPage (same underlying object) --------
    def set_start_date_time(self, iso_value: str) -> "ChamberEventsAdminPage":
        self.page.get_by_role("textbox", name=FIELD_START_DATE_TIME, exact=True).fill(iso_value)
        return self

    def set_end_date_time(self, iso_value: str) -> "ChamberEventsAdminPage":
        self.page.get_by_role("textbox", name=FIELD_END_DATE_TIME, exact=True).fill(iso_value)
        return self

    # ---- Combobox scoping — multi-combobox form, mirrors
    # HomeBusinessEventsAdminPage.select_combobox_option_for_field() ----------
    def select_combobox_option_for_field(self, field_label: str, option_label: str) -> "ChamberEventsAdminPage":
        combobox = self.page.get_by_role("combobox", name=field_label, exact=True)
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        option = self.page.locator(f'#{listbox_id} [role="option"]:text-is("{option_label}")')
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return self

    # ---- Field actions ----------------------------------------------------------
    def fill_event_title(self, value: str, locale_suffix: str = "") -> "ChamberEventsAdminPage":
        label = FIELD_EVENT_TITLE if not locale_suffix else f"{FIELD_EVENT_TITLE} — {locale_suffix}"
        self.fill_text(label, value)
        return self

    def fill_event_description(self, value: str) -> "ChamberEventsAdminPage":
        self.fill_text(FIELD_EVENT_DESCRIPTION, value)
        return self

    def fill_venue(self, value: str, locale_suffix: str = "") -> "ChamberEventsAdminPage":
        label = FIELD_VENUE if not locale_suffix else f"{FIELD_VENUE} — {locale_suffix}"
        self.fill_text(label, value)
        return self

    def select_category_sector(self, label: str) -> "ChamberEventsAdminPage":
        return self.select_combobox_option_for_field(FIELD_CATEGORY_SECTOR, label)

    def select_event_format(self, label: str) -> "ChamberEventsAdminPage":
        return self.select_combobox_option_for_field(FIELD_EVENT_FORMAT, label)

    def select_status(self, label: str) -> "ChamberEventsAdminPage":
        return self.select_combobox_option_for_field(FIELD_STATUS, label)

    def select_calendar_export_type(self, label: str) -> "ChamberEventsAdminPage":
        return self.select_combobox_option_for_field(FIELD_CALENDAR_EXPORT_TYPE, label)

    def set_registration_enabled(self, checked: bool) -> "ChamberEventsAdminPage":
        return self.set_checkbox(FIELD_REGISTRATION_ENABLED, checked)

    def fill_registration_limit(self, value: str) -> "ChamberEventsAdminPage":
        self.fill_number(FIELD_REGISTRATION_LIMIT, value)
        return self

    def set_add_to_calendar_enabled(self, checked: bool) -> "ChamberEventsAdminPage":
        return self.set_checkbox(FIELD_ADD_TO_CALENDAR_ENABLED, checked)

    def set_google_enabled(self, checked: bool) -> "ChamberEventsAdminPage":
        return self.set_checkbox(FIELD_GOOGLE_ENABLED, checked)

    def set_outlook_enabled(self, checked: bool) -> "ChamberEventsAdminPage":
        return self.set_checkbox(FIELD_OUTLOOK_ENABLED, checked)

    def set_ics_enabled(self, checked: bool) -> "ChamberEventsAdminPage":
        return self.set_checkbox(FIELD_ICS_ENABLED, checked)

    def set_pin_to_home(self, checked: bool) -> "ChamberEventsAdminPage":
        return self.set_checkbox(FIELD_PIN_TO_HOME, checked)

    def fill_time_zone(self, value: str) -> "ChamberEventsAdminPage":
        self.fill_text(FIELD_TIME_ZONE, value)
        return self

    def upload_event_image(self, file_path: str) -> "ChamberEventsAdminPage":
        self.upload_file(FIELD_EVENT_IMAGE, file_path)
        return self

    def fill_what_to_expect_item(self, index: int, value: str) -> "ChamberEventsAdminPage":
        self.page.get_by_role(
            "textbox", name=f"{FIELD_WHAT_TO_EXPECT_ITEM} {index}", exact=True
        ).fill(value)
        return self

    # ---- Lifecycle -----------------------------------------------------------
    def publish(self) -> "ChamberEventsAdminPage":
        self.submit_for_publishing()
        return self

    def save_draft(self) -> "ChamberEventsAdminPage":
        self.save_as_draft()
        return self

    def unpublish(self) -> "ChamberEventsAdminPage":
        self.unpublish_to_edit_as_draft()
        return self


class ChamberEventsListingConfigAdminPage(_ChamberEventsBaseAdminPage):
    """Page-level hero/section configuration Page Object — composes
    ObjectAuthoringPage with slug="events-listing-page" (see module
    docstring)."""

    def __init__(self, page):
        super().__init__(page, EVENTS_LISTING_PAGE_SLUG)

    def open_config_form(self, email: str | None = None, password: str | None = None) -> "ChamberEventsListingConfigAdminPage":
        self._ensure_logged_in(email, password)
        self.open_new_entry_form()
        return self

    def open_config_list(self, email: str | None = None, password: str | None = None) -> "ChamberEventsListingConfigAdminPage":
        self._ensure_logged_in(email, password)
        self.open_entries_list()
        return self

    def fill_eyebrow_label_en(self, value: str) -> "ChamberEventsListingConfigAdminPage":
        self.fill_text(FIELD_EYEBROW_LABEL_EN, value)
        return self

    def fill_page_title_en(self, value: str) -> "ChamberEventsListingConfigAdminPage":
        self.fill_text(FIELD_PAGE_TITLE_EN, value)
        return self

    def fill_page_title_ar(self, value: str) -> "ChamberEventsListingConfigAdminPage":
        self.fill_text(FIELD_PAGE_TITLE_AR, value)
        return self

    def fill_hero_description(self, value: str) -> "ChamberEventsListingConfigAdminPage":
        self.fill_rich_text(value)
        return self

    def upload_hero_image(self, file_path: str) -> "ChamberEventsListingConfigAdminPage":
        self.upload_file(FIELD_HERO_IMAGE, file_path)
        return self

    def save_draft(self) -> "ChamberEventsListingConfigAdminPage":
        self.save_as_draft()
        return self

    def publish(self) -> "ChamberEventsListingConfigAdminPage":
        self.submit_for_publishing()
        return self

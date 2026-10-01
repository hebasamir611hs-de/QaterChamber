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

RE-READ LIVE 2026-09-30 (TEST_USER, manage-business-event create form,
read-only — nothing saved). Corrections to the TODO(locator) list above:

  - REQUIRED on submit (asterisked + `required`): Event Title (EN + AR),
    Event Category (combobox: "Chamber Events" / "Global Events" /
    "Test Event"), Event Image / Thumbnail, Event Sector (EN + AR),
    Event Date & Time, Location (EN + AR). A submit that leaves any of them
    empty is refused and writes nothing — so every "publish then check the
    public site" case must fill them, or it can never reach the site.
  - Event Description and What to Expect are CKEditor rich-text fields
    (`ObjectField_eventDescription` / `ObjectField_whatToExpect`), not
    textboxes; there is no "What to Expect Item <n>" control.
  - Category / Sector is a plain bilingual TEXT field, not a combobox.
  - Event Format IS a combobox (Conference, Exhibition, Forum, Investor
    Summit, Networking Event, Panel Discussion, Product Launch, Roadshow,
    Seminar, Trade Show, Webinar, Workshop, Championship).
  - Labels read live: "Event Image / Thumbnail", "ICS Download Enabled",
    "Pin to Home (Featured)".
  - Active Status is present and CHECKED by default on this object (unlike
    manage-law-entry, where it defaults unchecked). Still set explicitly.
  - The submit button read "Publish" for TEST_USER here; the 2026-09-28
    workflow notes record "Submit for Review" for Author and Editor on
    manage-law-entry. SUBMIT_FOR_REVIEW_BUTTON matches either.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import control_panel_url

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
FIELD_EVENT_IMAGE = "Event Image / Thumbnail"
FIELD_STATUS = "Status"
FIELD_REGISTRATION_ENABLED = "Registration Enabled"
FIELD_REGISTRATION_LIMIT = "Registration Limit"
FIELD_ADD_TO_CALENDAR_ENABLED = "Add to Calendar Enabled"
FIELD_CALENDAR_EXPORT_TYPE = "Calendar Export Type"
FIELD_GOOGLE_ENABLED = "Google Calendar Enabled"
FIELD_OUTLOOK_ENABLED = "Outlook Calendar Enabled"
FIELD_ICS_ENABLED = "ICS Download Enabled"
FIELD_PIN_TO_HOME = "Pin to Home (Featured)"
FIELD_DESCRIPTION_SOURCE = "Description Source"
FIELD_WHAT_TO_EXPECT = "What to Expect"
FIELD_EVENT_SECTOR = "Event Sector"
FIELD_EVENT_DATE_TIME = "Event Date & Time"
FIELD_LOCATION = "Location"
FIELD_ACTIVE_STATUS = "Active Status"
AR_SUFFIX = "العربية"

# CKEditor iframes, scoped by the object field's own DOM id; nth=0 is the
# EN editor (the AR one follows it in the same container).
EVENT_DESCRIPTION_EDITOR = 'div[id$="ObjectField_eventDescription"] iframe[title="editor"] >> nth=0'
WHAT_TO_EXPECT_EDITOR = 'div[id$="ObjectField_whatToExpect"] iframe[title="editor"] >> nth=0'

EVENT_CATEGORY_CHAMBER_EVENTS = "Chamber Events"

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
        """Session must belong to `email` — see CmsLoginPage.ensure_signed_in_as()
        (CORRECTED 2026-09-30: this used to skip the login whenever the
        admin toolbar showed, so role tests ran as TEST_USER)."""
        CmsLoginPage(self.page).ensure_signed_in_as(
            email, password, control_panel_url(ADMIN_HOME_EN_URL_PATH)
        )

    def has_admin_toolbar(self) -> bool:
        """Privilege check for the current session — see
        CmsLoginPage.has_admin_toolbar(). Role tests assert on it up front to
        prove they are not running as an admin."""
        return CmsLoginPage(self.page).has_admin_toolbar()


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

    # ---- Entries list is PAGED (10 rows) — filter before any row lookup ----
    # Found live 2026-09-30: manage-business-event holds 16 entries, shown
    # 10 per page, and a freshly published record landed on PAGE 2. Every
    # inherited row lookup reads only the rendered page, so status reads
    # returned "" and teardown deleted nothing — leaving QCTEST records on
    # qcdev. The list's own "Search entries…" box narrows it to the title;
    # the overrides below apply it first.
    ENTRIES_SEARCH_INPUT = 'input[placeholder^="Search entries"]'

    # The search reads an index that lags a fresh save: live 2026-10-01 a
    # draft saved by the Author was not found 5s later, and was found when
    # searched again shortly after. Re-run the search until it shows or the
    # budget runs out — no match is still a valid answer.
    ENTRIES_SEARCH_TIMEOUT_MS = 20000
    ENTRIES_SEARCH_RETRY_MS = 4000

    def filter_entries(self, text: str) -> "ChamberEventsAdminPage":
        box = self.page.locator(self.ENTRIES_SEARCH_INPUT)
        if box.count() == 0:
            return self
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{text}")').first
        waited = 0
        while True:
            box.fill(text)
            box.press("Enter")
            try:
                row.wait_for(state="visible", timeout=self.ENTRIES_SEARCH_RETRY_MS)
                return self
            except Exception:  # noqa: BLE001 — not (yet) found; retry within budget
                waited += self.ENTRIES_SEARCH_RETRY_MS
                if waited >= self.ENTRIES_SEARCH_TIMEOUT_MS:
                    return self

    def row_status_text(self, title: str) -> str:
        self.filter_entries(title)
        return super().row_status_text(title)

    def row_visible(self, title: str) -> bool:
        self.filter_entries(title)
        return super().row_visible(title)

    def open_entry_by_edit_link(self, title: str) -> "ChamberEventsAdminPage":
        self.filter_entries(title)
        super().open_entry_by_edit_link(title)
        return self

    def _run_row_action(self, title_or_code: str, action: str, comment: str = "") -> "ChamberEventsAdminPage":
        # Every row transition (approve/unpublish/publish/...) goes through
        # here — filter first so a row on page 2 is reachable.
        self.filter_entries(title_or_code)
        super()._run_row_action(title_or_code, action, comment)
        return self

    def row_offers_action(self, title: str, action: str) -> bool:
        """Whether the row renders the `data-qc-oel-<action>` control — the
        role-and-status-dependent action set documented on
        ObjectAuthoringPage's row transitions."""
        self.filter_entries(title)
        return self._row_locator(title).locator(f"[{self.ROW_ACTION_ATTRS[action]}]").count() > 0

    def submit_button_label(self) -> str:
        """The form's submit label — "Publish" (read for TEST_USER
        2026-09-30) or "Submit for Review"; see SUBMIT_FOR_REVIEW_BUTTON."""
        return self.page.locator(self.SUBMIT_FOR_REVIEW_BUTTON).first.inner_text().strip()

    def delete_entry_by_title(self, title: str) -> bool:
        try:
            self.filter_entries(title)
        except Exception:  # noqa: BLE001 — teardown keeps the parent's never-raise contract
            pass
        return super().delete_entry_by_title(title)

    def open_events_list(self, email: str | None = None, password: str | None = None) -> "ChamberEventsAdminPage":
        self._ensure_logged_in(email, password)
        self.open_entries_list()
        return self

    # ---- Date handling — native datetime-local inputs, confirmed for this
    # object by HomeBusinessEventsAdminPage (same underlying object) --------
    # CORRECTED 2026-09-30 (read live): the three date fields are no longer
    # reachable as role=textbox. Each is a 1x1, opacity-0 native
    # datetime-local input (name="ObjectField_<field>") behind a visible
    # "dd/mm/yyyy hh:mm" text box with a calendar button. Typing into the
    # visible box — what a user does — was confirmed to update the hidden
    # value ("01/06/2027 09:00" -> "2027-06-01T09:00").
    DATETIME_VISIBLE_INPUT = 'input[placeholder="dd/mm/yyyy hh:mm"]'

    def _type_datetime(self, object_field: str, iso_value: str) -> "ChamberEventsAdminPage":
        """`iso_value` is `YYYY-MM-DDTHH:MM`. Anything that does not parse as
        that (a malformed-value case) is typed through verbatim."""
        from datetime import datetime

        try:
            typed = datetime.strptime(iso_value, "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %H:%M")
        except ValueError:
            typed = iso_value
        hidden = self.page.locator(f'input[name="ObjectField_{object_field}"]')
        box = hidden.locator("xpath=../..").locator(self.DATETIME_VISIBLE_INPUT)
        box.click()
        box.fill("")
        box.press_sequentially(typed)
        box.press("Tab")
        return self

    def set_start_date_time(self, iso_value: str) -> "ChamberEventsAdminPage":
        return self._type_datetime("startDateTime", iso_value)

    def set_end_date_time(self, iso_value: str) -> "ChamberEventsAdminPage":
        return self._type_datetime("endDateTime", iso_value)

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
    def _fill_labelled(self, field_label: str, value: str) -> "ChamberEventsAdminPage":
        """fill_text() with the required-field ` *` tolerated — the AR twins
        of required fields render as e.g. "Event Title — العربية *"
        (read live 2026-09-30), which an exact name never matches."""
        self.page.get_by_role("textbox", name=self.label_pattern(field_label)).fill(value)
        return self

    def fill_event_title(self, value: str, locale_suffix: str = "") -> "ChamberEventsAdminPage":
        label = FIELD_EVENT_TITLE if not locale_suffix else f"{FIELD_EVENT_TITLE} — {locale_suffix}"
        self._fill_labelled(label, value)
        return self

    def fill_event_description(self, value: str) -> "ChamberEventsAdminPage":
        # Rich text (CKEditor iframe), not a textbox — see module docstring.
        self.fill_iframe_editor(EVENT_DESCRIPTION_EDITOR, value)
        return self

    def fill_venue(self, value: str, locale_suffix: str = "") -> "ChamberEventsAdminPage":
        label = FIELD_VENUE if not locale_suffix else f"{FIELD_VENUE} — {locale_suffix}"
        self._fill_labelled(label, value)
        return self

    def select_category_sector(self, label: str) -> "ChamberEventsAdminPage":
        # Plain text field on the live form, not a combobox (read 2026-09-30).
        # Name kept so existing callers resolve.
        self.fill_text(FIELD_CATEGORY_SECTOR, label)
        return self

    def select_event_category(self, label: str = EVENT_CATEGORY_CHAMBER_EVENTS) -> "ChamberEventsAdminPage":
        return self.select_combobox_option_for_field(FIELD_EVENT_CATEGORY, label)

    def fill_event_sector(self, en: str, ar: str) -> "ChamberEventsAdminPage":
        self._fill_labelled(FIELD_EVENT_SECTOR, en)
        self._fill_labelled(f"{FIELD_EVENT_SECTOR} — {AR_SUFFIX}", ar)
        return self

    def fill_location(self, en: str, ar: str) -> "ChamberEventsAdminPage":
        self._fill_labelled(FIELD_LOCATION, en)
        self._fill_labelled(f"{FIELD_LOCATION} — {AR_SUFFIX}", ar)
        return self

    def set_event_date_time(self, iso_value: str) -> "ChamberEventsAdminPage":
        return self._type_datetime("eventDateTime", iso_value)

    def set_active_status(self, checked: bool) -> "ChamberEventsAdminPage":
        return self.set_checkbox(FIELD_ACTIVE_STATUS, checked)

    def fill_required_publish_fields(
        self,
        title: str,
        image_path: str,
        event_date_time: str = "2027-06-01T09:00",
        include_image: bool = True,
        include_category: bool = True,
    ) -> "ChamberEventsAdminPage":
        """Fill every field the live form requires on submit, EXCEPT the EN
        title (callers set it themselves) — so a case that is really about
        one field can still be published and followed to the public site.
        Ticks Active Status: it is the second visibility gate
        (standards.md, "Active Status Is a Precondition...").

        Do not use this in a case whose subject is one of these required
        fields being left empty — pass include_image / include_category
        =False to leave that one out."""
        self.fill_event_title(f"{title} AR", locale_suffix=AR_SUFFIX)
        if include_category:
            self.select_event_category()
        if include_image:
            self.upload_event_image(image_path)
        self.fill_event_sector("QCTEST Sector", "قطاع اختبار")
        self.set_event_date_time(event_date_time)
        self.fill_location("Qatar Chamber, Doha", "غرفة قطر، الدوحة")
        self.set_active_status(True)
        return self

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
        """Uploads a uniquely named copy. Re-uploading a file name that is
        already in Documents & Media fails with "An unexpected error occurred
        while uploading your file" instead of versioning — hit live
        2026-09-30 on the second run with valid_event_image.jpg, and the same
        collision board_of_directors / home_business_events already work
        around. Size and type are unchanged, so the oversize/unsupported
        cases still test what they claim."""
        import shutil
        import tempfile
        import uuid
        from pathlib import Path

        src = Path(file_path)
        dest = Path(tempfile.gettempdir()) / f"{src.stem}_{uuid.uuid4().hex[:12]}{src.suffix}"
        shutil.copy(src, dest)
        self.upload_file(FIELD_EVENT_IMAGE, str(dest))
        return self

    def fill_what_to_expect(self, value: str) -> "ChamberEventsAdminPage":
        """What to Expect is ONE rich-text field (read live 2026-09-30) —
        there is no per-item textbox."""
        self.fill_iframe_editor(WHAT_TO_EXPECT_EDITOR, value)
        return self

    # ---- Lifecycle -----------------------------------------------------------
    def publish(self) -> "ChamberEventsAdminPage":
        self.submit_for_review()
        return self

    def publish_and_confirm(
        self, title: str, email: str | None = None, password: str | None = None
    ) -> "ChamberEventsAdminPage":
        """Submit, then prove the record really landed on Published before a
        caller goes looking for it on the public site. Without this, a
        refused submit (a required field empty) or a Pending Review outcome
        looked exactly like "did not propagate"."""
        self.publish()
        self.open_events_list(email, password)
        status = self.row_status_text(title)
        assert status == STATUS_PUBLISHED, (
            f"{title!r} is {status or 'absent from the list'!r} after submit, "
            f"not {STATUS_PUBLISHED!r} — nothing to look for on the public site"
        )
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

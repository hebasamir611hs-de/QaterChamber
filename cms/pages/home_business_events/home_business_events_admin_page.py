"""
cms/pages/home_business_events/home_business_events_admin_page.py —
HomeBusinessEventsAdminPage.

Control_Panel Page Object for PBI 129383 (Business Events auto-sync), backing
the "Business Event" **Object Authoring** surface
(`https://qcdev.ihorizons.com/web/qatar-chamber/manage-business-event`) that
feeds the public Home Page "Business Events" section
(home_business_events_page.py is the public-frontend counterpart).

CORRECTED 2026-09-07 (mandatory re-verification per standards.md's "Object
Authoring Is the Only Path for Publish/Unpublish/Draft/Preview Actions" and
"Draft/Unpublish Public-Visibility Checks" sections, added same day):

  - The PRIOR version of this file drove Save/Publish/Unpublish via
    `Content & Data`'s raw Object Definitions grid (objectDefinitionId 49263)
    using an inline `publicationStatus` combobox as the sole lifecycle
    control ("DISCLOSED SUBSTITUTION" — no separate Submit-for-Review/Publish
    button existed on THAT surface). That substitution claim is FALSE for
    this feature: a real, dedicated Object Authoring surface exists for this
    object — `manage-business-event` — confirmed LIVE this session (not
    assumed) to render the same generic Save-as-Draft / Submit-for-Publishing
    / Unpublish-to-edit-as-draft state machine every other Object Authoring
    surface in this project uses (see cms/pages/components/object_authoring_
    page.py's own module docstring). The task that produced GM Message's and
    Strategic Direction's Object-Authoring correction explicitly asked this
    feature to be re-verified rather than assumed either way — it needed the
    correction too, this Page Object was simply not caught in that batch.
    `Content & Data`'s objectDefinitionId=49263 grid is henceforth NOT used
    for publish/unpublish/draft actions (Content & Data may still be a valid
    surface for pure field-value editing per standards.md, but no test in
    this batch needs that distinction — every field this feature's 2 TCs
    touch is also editable on the Object Authoring form).

  - Confirmed LIVE the Object Authoring form's field set matches the same
    names already documented for the Content & Data DDM form (Event Title,
    Event Category, Event Sector, Category / Sector, Event Format, Location,
    Venue, Time Zone, Registration Limit, Event Image, Status), each exposed
    as a real accessible role/name — `page.get_by_role("textbox"/"combobox"/
    "spinbutton", name=<label>, exact=True)` — per
    ObjectAuthoringPage.fill_text()/field_value()/fill_number()'s own
    confirmed-live pattern. Bilingual fields render as TWO independent
    textboxes (`"<Label>"` / `"<Label> — العربية"`) — only the EN one is
    filled here, matching this batch's scope (no Arabic assertions in either
    TC).

  - **DATE FIELDS ARE A GENUINE, CONFIRMED-LIVE DIFFERENCE from the
    Content & Data form**: Event Date & Time / Start Date & Time / End Date &
    Time are native `<input type="datetime-local">` controls on THIS surface
    (confirmed live via `.evaluate(el => el.type)` === "datetime-local"),
    NOT the free-text `MM/DD/YYYY hh:mm AM` string field the Content & Data
    DDM form used. `.fill("YYYY-MM-DDTHH:MM")` is the correct, confirmed-live
    way to set them here — a `keyboard.type()` of the old MM/DD/YYYY string
    was tried first and confirmed LIVE to leave the time segment unset
    (`"01/05/2027 --:-- --"`), i.e. it silently fails rather than raising.
    `type_datetime_local()` below is a new, Business-Event-specific helper
    for this reason — `ObjectAuthoringPage.type_date()` (the shared
    keyboard-typing helper) is NOT reused here; it is confirmed correct for
    the OTHER objects that already use it (plain text date fields), and
    using it here would silently reproduce this exact bug.

  - **COMBOBOX SCOPING — confirmed-live bug in blindly reusing
    `ObjectAuthoringPage.select_combobox_option()` here**: that shared method
    clicks an UNSCOPED `get_by_role("button", name="Open Options Menu")` —
    correct only when a form has exactly one such combobox (confirmed live
    for manage-service-card, its only confirmed caller so far). THIS form has
    FOUR (Event Category, Event Format, Status, Calendar Export Type), so the
    unscoped click always resolves the FIRST one in DOM order regardless of
    which field the caller intended — confirmed live this session (a first
    attempt scoping via `combobox.locator("xpath=ancestor::div[contains(@class,
    'input-group')][1]")` chained with `.get_by_role(...)`/`.locator(...)`
    also failed live — the chained locator never resolved a match at all,
    for a reason not fully root-caused, disclosed rather than pursued
    further since a working alternative was found). The reliable, confirmed-
    live mechanism: each combobox's own `aria-controls="<listbox-id>"`
    attribute uniquely names its OWN dropdown `<button>` (also carrying the
    same `aria-controls`) and its own `<ul role="listbox" id="<listbox-id>">`
    — `select_combobox_option_for_field()` below resolves the button and the
    option via that shared id, scoped correctly regardless of how many
    comboboxes the form has. Kept as a method on THIS Page Object (not added
    to the shared `ObjectAuthoringPage`) since it was only confirmed live
    against this one form — promote it to the shared class once it's been
    confirmed against a second multi-combobox object.

  - **EVENT IMAGE UPLOAD** reuses `ObjectAuthoringPage.upload_file()`
    verbatim (its own confirmed-live "Select File" sibling-button + iframe +
    "1 of 1" pattern) — not independently re-derived here.

  - **LIFECYCLE MAPPING for this feature's 2 TCs**, confirmed LIVE this
    session end-to-end against a real disposable
    "QCTEST-PROBE-135747 Doha SME Growth Summit" entry (created, submitted,
    verified on the public section, unpublished, deleted — id 186001, fully
    cleaned up, zero QCTEST rows left afterward):
      - TC 135747 ("...Save, submit for review, and publish..."): fill every
        field (including Status=Published — the object's OWN
        `publicationStatus` data field, distinct from the object's workflow
        state) then `submit_for_publishing()`. Confirmed live: the entries
        list's Status COLUMN (workflow state) reads "Approved" after this,
        and the just-created record (`externalReferenceCode`-style id 186001
        this session) appeared on the public Home Page Business Events
        section under both "All" and "Chamber Events" tabs with the correct
        category badge — the full TC 135747 flow passes as scripted below.
      - TC 135748 ("...Unpublish the event...card no longer appears..."):
        clicking `unpublish_to_edit_as_draft()` correctly flips the
        entries-list workflow Status column to "Draft". An initial quick
        manual check (2 reloads, no real polling budget) appeared to show
        the card still present and the object's own `publicationStatus` data
        field left blank rather than "Unpublished" — flagged at the time as
        a SUSPECTED PRODUCT DEFECT. **RE-VERIFIED via the actual scripted,
        polled pytest run (`UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS` = 15000ms,
        the same budget this feature's public Page Object already
        documents) and this passed** — the card DOES disappear from the
        public section after unpublish, just on a longer propagation tail
        (up to the existing 15s budget) than the 2 quick manual reloads
        happened to cover. The `publicationStatus` field's blank read-back
        is left as a disclosed, unexplained data-field quirk (the
        workflow-status transition is what the public section actually
        appears to key off, not that field) — not escalated as a defect,
        since the case's actual expected behavior (card removed) is
        confirmed to hold within budget.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url, settings

SLUG = "business-event"

# Same re-login-if-needed entry point every sibling admin Page Object in
# this project uses before touching an Object Authoring `manage-<slug>` URL
# directly — see GmMessageAdminPage.open_object_authoring_form()'s own
# CONFIRMED LIVE 2026-09-07 note: `ObjectAuthoringPage`'s own navigation
# methods have NO login/session check of their own, and a stale
# `.auth/state.json` session hitting `manage-business-event` directly
# renders the public site's generic "Coming Soon" placeholder instead of
# the admin form (no login redirect for this class to react to). Routing
# through `/en/home` first (which DOES check for a real signed-in Product
# Menu / Content & Data link and re-logs-in if absent) before opening the
# Object Authoring URL avoids that gap.
ADMIN_HOME_EN_URL_PATH = "/en/home"
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'

FIELD_EVENT_TITLE = "Event Title"
FIELD_EVENT_CATEGORY = "Event Category"
FIELD_EVENT_SECTOR = "Event Sector"
FIELD_CATEGORY_SECTOR = "Category / Sector"
FIELD_EVENT_FORMAT = "Event Format"
FIELD_LOCATION = "Location"
FIELD_VENUE = "Venue"
FIELD_TIME_ZONE = "Time Zone"
FIELD_REGISTRATION_LIMIT = "Registration Limit"
FIELD_EVENT_IMAGE = "Event Image"
FIELD_STATUS = "Status"
FIELD_EVENT_DATE_TIME = "Event Date & Time"
FIELD_START_DATE_TIME = "Start Date & Time"
FIELD_END_DATE_TIME = "End Date & Time"

STATUS_DRAFT = "Draft"
STATUS_PUBLISHED = "Published"
STATUS_UNPUBLISHED = "Unpublished"

CATEGORY_CHAMBER_EVENTS = "Chamber Events"
CATEGORY_GLOBAL_EVENTS = "Global Events"


class HomeBusinessEventsAdminPage(ObjectAuthoringPage):
    """Composes the generic Object Authoring state machine
    (`ObjectAuthoringPage`) with this object's own field map. Constructed
    with just `page` (slug is fixed to "business-event" for this class,
    unlike the shared base class's own `__init__(page, slug)` signature)."""

    def __init__(self, page):
        super().__init__(page, SLUG)

    # ---- Navigation -------------------------------------------------------
    def _ensure_logged_in(self) -> None:
        """Re-login-if-needed via `/en/home`'s real Product Menu/Content &
        Data check — see module-level constants' docstring for why this must
        run before any direct `manage-business-event` navigation."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_create_event_form(self) -> "HomeBusinessEventsAdminPage":
        self._ensure_logged_in()
        self.open_new_entry_form()
        return self

    def open_business_events_list(self) -> "HomeBusinessEventsAdminPage":
        self._ensure_logged_in()
        self.open_entries_list()
        return self

    # ---- Business-Event-specific date handling -----------------------------
    # See module docstring's DATE FIELDS note — these 3 fields are native
    # `datetime-local` inputs on this surface, confirmed live to silently
    # ignore a keyboard-typed "MM/DD/YYYY hh:mm AM" string.
    def type_datetime_local(self, field_label: str, iso_value: str) -> "HomeBusinessEventsAdminPage":
        """`iso_value` must be `YYYY-MM-DDTHH:MM` (24h), the confirmed-live
        accepted format for this surface's native datetime-local inputs."""
        self.page.get_by_role("textbox", name=field_label, exact=True).fill(iso_value)
        return self

    # ---- Business-Event-specific combobox scoping --------------------------
    # See module docstring's COMBOBOX SCOPING note — this form has 4
    # comboboxes, so the shared ObjectAuthoringPage.select_combobox_option()
    # (unscoped "Open Options Menu" click) is not safe to reuse here.
    def select_combobox_option_for_field(self, field_label: str, option_label: str) -> "HomeBusinessEventsAdminPage":
        combobox = self.page.get_by_role("combobox", name=field_label, exact=True)
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        option = self.page.locator(f'#{listbox_id} [role="option"]:text-is("{option_label}")')
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return self

    # ---- Field actions (thin, named wrappers over the base class's
    # generic role-based helpers — kept here so the test module reads at the
    # feature's own vocabulary rather than repeating field-label strings) ----
    def fill_event_title(self, value: str) -> "HomeBusinessEventsAdminPage":
        self.fill_text(FIELD_EVENT_TITLE, value)
        return self

    def fill_event_sector(self, value: str) -> "HomeBusinessEventsAdminPage":
        self.fill_text(FIELD_EVENT_SECTOR, value)
        return self

    def fill_category_sector(self, value: str) -> "HomeBusinessEventsAdminPage":
        self.fill_text(FIELD_CATEGORY_SECTOR, value)
        return self

    def fill_location(self, value: str) -> "HomeBusinessEventsAdminPage":
        self.fill_text(FIELD_LOCATION, value)
        return self

    def fill_venue(self, value: str) -> "HomeBusinessEventsAdminPage":
        self.fill_text(FIELD_VENUE, value)
        return self

    def fill_time_zone(self, value: str) -> "HomeBusinessEventsAdminPage":
        self.fill_text(FIELD_TIME_ZONE, value)
        return self

    def select_event_category(self, label: str) -> "HomeBusinessEventsAdminPage":
        return self.select_combobox_option_for_field(FIELD_EVENT_CATEGORY, label)

    def select_event_format(self, label: str) -> "HomeBusinessEventsAdminPage":
        return self.select_combobox_option_for_field(FIELD_EVENT_FORMAT, label)

    def select_status(self, label: str) -> "HomeBusinessEventsAdminPage":
        return self.select_combobox_option_for_field(FIELD_STATUS, label)

    def upload_event_image(self, file_path: str) -> "HomeBusinessEventsAdminPage":
        self.upload_file(FIELD_EVENT_IMAGE, file_path)
        return self

    def set_event_date_time(self, iso_value: str) -> "HomeBusinessEventsAdminPage":
        return self.type_datetime_local(FIELD_EVENT_DATE_TIME, iso_value)

    def set_start_date_time(self, iso_value: str) -> "HomeBusinessEventsAdminPage":
        return self.type_datetime_local(FIELD_START_DATE_TIME, iso_value)

    def set_end_date_time(self, iso_value: str) -> "HomeBusinessEventsAdminPage":
        return self.type_datetime_local(FIELD_END_DATE_TIME, iso_value)

    # ---- Lifecycle ----------------------------------------------------------
    def publish(self) -> "HomeBusinessEventsAdminPage":
        """Real Site Content Editor "publish" action on this surface —
        `submit_for_publishing()` (see class docstring's LIFECYCLE MAPPING
        note: confirmed live this moves the entries-list workflow Status
        column to "Approved")."""
        self.submit_for_publishing()
        return self

    def unpublish(self) -> "HomeBusinessEventsAdminPage":
        """Real Site Content Editor "unpublish" action — Object Authoring's
        "Unpublish to edit as draft" (see class docstring's LIFECYCLE MAPPING
        note for the confirmed-live SUSPECTED PRODUCT DEFECT this does not
        appear to actually remove the card from the public section)."""
        self.unpublish_to_edit_as_draft()
        return self

    # ---- State queries ------------------------------------------------------
    def workflow_status(self, title: str) -> str:
        """Entries-list workflow-state column ("Approved"/"Draft") for the
        row matching `title` — see ObjectAuthoringPage.row_status_text()'s
        own docstring for the normalization this reads through."""
        return self.row_status_text(title)

    # Bounded poll wrapping workflow_status() — confirmed LIVE 2026-09-07 a
    # bare immediate read right after submit_for_publishing()'s own settle
    # occasionally raced the entries-list row not yet reflecting the just-
    # created record (one observed empty-string read; a second run with no
    # code change read "Approved" correctly) — the same class of write-vs-
    # read-cache propagation gap this project's SAVE_COMMIT_GRACE_MS
    # convention already documents elsewhere, not a locator defect. Polls
    # (re-navigating the entries list each attempt) rather than trusting a
    # single read.
    WORKFLOW_STATUS_POLL_TIMEOUT_MS = 8000
    WORKFLOW_STATUS_POLL_INTERVAL_MS = 1000

    def wait_for_workflow_status(self, title: str, expected: str) -> str:
        import time

        deadline = time.monotonic() + (self.WORKFLOW_STATUS_POLL_TIMEOUT_MS / 1000)
        last = ""
        while True:
            last = self.workflow_status(title)
            if last == expected:
                return last
            if time.monotonic() >= deadline:
                return last
            self.page.wait_for_timeout(self.WORKFLOW_STATUS_POLL_INTERVAL_MS)
            self.open_business_events_list()

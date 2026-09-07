"""
web/pages/home_business_events/home_business_events_admin_page.py —
HomeBusinessEventsAdminPage.

Control_Panel Page Object for PBI 129383 (Business Events auto-sync), backing
the "Business Events" Object Definition entry list/editor (objectDefinitionId
49263, per this session's confirmed live URL — see NAVIGATION note below) that
feeds the public Home Page "Business Events" section (home_business_events_page.py
is the public-frontend counterpart).

REAL, LIVE-VERIFIED FACTS (this session, 2026-08-31, headed Chromium against
qcdev via the Playwright MCP browser — a single, non-parallel session; the
PRIOR blocked attempt's navigation races were reproduced by 4 CONCURRENT
agents sharing one qcdev TEST_USER session, not by anything in this Page
Object's own locators):

NAVIGATION
  - A raw `objectDefinitionId=49263` query param on a bare
    `.../control_panel/manage` URL is NOT enough by itself — Liferay's
    Object Definitions portlet is addressed by a REGENERATING portlet
    INSTANCE id embedded in the URL (`..._ObjectDefinitionsPortlet_<ID>_...`,
    same regeneration behavior already documented in org_structure_admin_page.py
    / gm_message_admin_page.py). Hitting a stale instance id (or the bare
    objectDefinitionId with a DIFFERENT/mismatched instance id left over from
    a previous portlet render) silently serves WHATEVER object definition
    that instance id was last bound to in this session — confirmed live: the
    exact same URL shape that reached "Business Events" once in this session
    served "General Manager Messages" and "Strategic Pillar Cards" content on
    other attempts, with no error, just the wrong page's title. The only
    reliable path is the one gm_message_admin_page.py already established:
    enter via `/en/home`, open the Product Menu, click "Content & Data"
    (`[role="menuitem"]:text-is("Content & Data")` — a real navigating link,
    not a pure accordion toggle; clicking it also renders the flyout's full
    menuitem list including every Object Definition, confirmed live via
    `document.querySelectorAll('[role="menuitem"]')`), then click
    `[role="menuitem"]:text-is("Business Events")`. Do NOT hardcode/reuse a
    captured portlet-instance URL across sessions — BUSINESS_EVENTS_LIST_URL
    below is kept only as a documented artifact of the confirmed shape,
    exactly like GM_MESSAGES_LIST_URL's own precedent.
  - "Add Business Event" is `[data-testid="fdsCreationActionButton"]`
    (already confirmed pre-session, per the task's carried-over exploration)
    — reconfirmed live this session; clicking it opens the same
    `edit_object_entry` form shape as every other Object Definition in this
    project.

CONFIRMED LIVE FORM FIELD MAP (Create Business Event form, English locale)
  Unlike gm_message_admin_page.py's / org_structure_admin_page.py's label-
  proximity `_field_after_label()` xpath (needed there because those forms'
  DOM had duplicate label text nodes), THIS form's fields were mapped via a
  more robust, DIRECTLY confirmed-live mechanism: every field's container is
  a `.form-group[data-field-name=".../ddm$$<fieldName>$<randomToken>$0$$en_US"]`
  that ALSO carries a plain, non-regenerating `data-field-reference="<fieldName>"`
  attribute — `[data-field-reference="eventCategory"]` etc. is unique,
  stable, and does not depend on document order or duplicate-label
  disambiguation at all. Confirmed live (`$$eval` dump of every
  `.form-group[data-field-name]` on the rendered create form) — see
  `_field_container()` below. The per-field random token inside
  `data-field-name` itself (e.g. `eventTitle$7umvHDug`) DOES regenerate
  between page loads (confirmed live: a full-suffix locator that worked in
  one navigation returned a 0-count `input[id$="..."]` match after the next
  "Add Business Event" click) — matching the same regenerating-token
  behavior already documented for GM_NAME/SALUTATION_HEADING in
  gm_message_admin_page.py. `_text_input_by_id_substring()` below is that
  same file's substring-match helper, copied verbatim (a plain `ddm$$<name>`
  substring is stable across reloads; the trailing random token is not).

  Confirmed live field list (label -> `data-field-reference` -> widget type):
    - Event Title       -> eventTitle       -> plain text input
    - Event Category    -> eventCategory    -> custom combobox (button[role="combobox"])
        options confirmed live: "Choose an Option", "Chamber Events", "Global Events"
    - Event Sector      -> eventSector      -> plain text input (free text,
        NOT a picklist/combobox — confirmed live via full outerHTML dump;
        do not assume it shares eventCategory's combobox widget just because
        the task brief called it "sector")
    - Category / Sector -> categorySector   -> plain text input (a SEPARATE,
        also-free-text field from Event Sector — confirmed live as a
        distinct data-field-reference; not yet assigned a role in either TC,
        left unset by these tests, see OPEN QUESTIONS)
    - Event Format      -> eventFormat      -> custom combobox; options
        confirmed live: "Choose an Option", "Conference", "Exhibition",
        "Forum", "Investor Summit", "Networking Event", "Panel Discussion",
        "Product Launch", "Roadshow", "Seminar", "Trade Show", "Webinar",
        "Workshop", "Championship"
    - Event Date & Time -> eventDateTime    -> plain text input, date-picker
        widget attached (see DATE FIELD note below)
    - Start Date & Time -> startDateTime    -> plain text input, same widget
    - End Date & Time   -> endDateTime      -> plain text input, same widget
    - Location          -> location         -> plain text input (free text)
    - Venue             -> venue            -> plain text input (free text)
    - Time Zone         -> timeZone         -> plain text input (free text —
        NOT a tz-name combobox; confirmed live)
    - Description       -> description      -> CKEditor (classic, iframe-based:
        `#cke_<fieldId>` wrapper containing `iframe.cke_wysiwyg_frame`, NOT
        the `[contenteditable="true"]` div style already documented for
        gm_message's Page Content field — a DIFFERENT rich-text widget
        implementation on this same project, confirmed live via outerHTML)
    - Event Description -> eventDescription -> same CKEditor widget
    - What to Expect     -> whatToExpect     -> same CKEditor widget
    - Event Image        -> eventImage       -> file upload (`button:has-text("Select File")`)
    - Registration Limit -> registrationLimit -> plain text input (numeric)
    - Active Status / Add to Calendar Enabled / Google Calendar Enabled /
      ICS Download Enabled / Outlook Calendar Enabled / Pin to Home
      (Featured) / Registration Enabled -> checkboxes (`input[type="checkbox"]`
      inside each field's own `.form-group[data-field-reference="..."]`)
    - Calendar Export Type -> calendarExportType -> custom combobox (options
        not probed — out of scope for both TCs)
    - Status -> publicationStatus -> custom combobox; options confirmed
        live: "Choose an Option", "Draft", "Published", "Unpublished". This
        IS the publish/unpublish control, exactly like gm_message's Status
        field — there is no separate "Submit for Review"/"Publish" button on
        this form (confirmed live: `page.$$eval('button', ...)` on the fully
        rendered create form returned only Save/Cancel plus the per-field
        locale-toggle and date-picker/calendar buttons — no workflow button
        of any kind). TC 135747's "submit for review, publish" step and TC
        135748's "unpublish" step are both satisfied by this ONE combobox,
        matching the disclosed-substitution precedent already recorded in
        gm_message_admin_page.py's own docstring.

  DATE FIELD — confirmed live, format accepted: typing the literal string
  `MM/DD/YYYY hh:mm AM` (e.g. `12/15/2026 10:00 AM`) into
  `startDateTime`/`endDateTime`/`eventDateTime` via `keyboard.type()`
  produces exactly that string back from `input_value()` — the field DOES
  accept plain typed text, not just picker-driven entry.

  OPEN QUESTION — NOT resolved this session, disclosed rather than guessed:
  which of `eventDateTime` vs `startDateTime`/`endDateTime` actually drives
  the public card's single date/time line, and whether `eventDateTime` is
  itself mandatory. Both tests below fill ALL THREE date fields with the
  same future value to avoid depending on the answer, but this should be
  narrowed once a real Save is observed (see SAVE/TOAST note below).

  MANDATORY FIELDS — CONFIRMED LIVE (2026-08-31, follow-up session fixing a
  batch pytest run's failures): a real Save was completed this session
  (see SAVE / TOAST note below for the SAME session's later completion of
  what the ORIGINAL exploration flagged as blocked). The form's real
  required set is LARGER than the original TC scripting assumed — filling
  only Event Title/Category/Sector/Location/Venue/the three date fields
  produces a genuine (not falsely-detected) validation error naming
  whichever of the following was still empty, confirmed live one field at a
  time via direct network capture (create POST does NOT fire until every
  one of these is filled):
    - categorySector ("Category / Sector") — a SEPARATE field from Event
      Sector (see the pre-existing note below); free text, any non-empty
      value accepted (confirmed live with "Trade & Commerce").
    - eventFormat ("Event Format") — the custom combobox; confirmed live
      with "Conference".
    - eventImage ("Event Image") — file upload via the SAME Documents-and-
      Media modal+iframe pattern already confirmed for
      CommunityPartnersAdminPage.upload_partner_logo() (click "Select File"
      -> the modal's own iframe[title="Select File"] -> set_input_files on
      the iframe's OWN input -> click "Add").
  With all three filled (in addition to the previously-scripted fields),
  Save fires a real `POST /o/c/businessevents/scopes/<groupId>` that
  returns 200 and the record appears in the list with an assigned ID and
  Status "Approved"/whatever publicationStatus was set. `is_save_error_shown()`
  / `save_error_text()` were RE-CONFIRMED correct throughout this
  investigation — every banner they matched named a real, genuinely-empty
  mandatory field; they were never a false positive. The original batch's
  "Save reported a validation error" failure was a genuine validation error
  (missing categorySector/eventFormat/eventImage), not a locator-scoping
  defect — see is_save_error_shown()'s own docstring for why the test's
  OWN diagnostic slice looked like a broad-locator bug when it wasn't one.

  SAVE / TOAST — SAVE COMMIT now confirmed live (this follow-up session,
  see MANDATORY FIELDS note above: a real `POST /o/c/businessevents/scopes/
  <groupId>` returning 200, with the record then visible in the list at a
  real assigned ID). The success TOAST/notification element specifically
  was still not confirmed (no toast was actively looked for during this
  follow-up's network-capture-focused verification) — SUCCESS_TOAST below
  remains gated behind `_require_verified()` for that one narrower reason,
  not because Save itself is unverified. The ORIGINAL exploration session's
  own SAVE/TOAST blocker (below, preserved verbatim) was about a
  spontaneous-navigation environment glitch that did not reproduce in this
  follow-up session's several completed Save cycles.

  ORIGINAL SESSION'S SAVE/TOAST NOTE (preserved, not reproduced this
  follow-up session — kept as a disclosed environment finding, not deleted):
  this session hit a REPRODUCIBLE (though not deterministically triggered)
  spontaneous navigation away from this form — confirmed live TWICE,
  independently, landing both times on the SAME unrelated record
  (`externalReferenceCode=QCDEMO-129381-STRATEGIC_PILLAR_CARD-02`, a
  Strategic Pillar Card from a completely different PBI/object definition)
  immediately after an in-form interaction (once after a combobox open +
  Escape-to-dismiss, once after clicking directly into the `startDateTime`
  text input with no Escape involved at all — ruling out Escape alone as
  the trigger; a live isolated re-test of combobox-open + Escape on its own,
  immediately after, did NOT reproduce it). This is consistent with a
  stateful "restore last portlet render target" mechanism in this Liferay
  admin SPA shell that occasionally fires on an unrelated in-form
  interaction — NOT a locator defect in this Page Object (every locator
  used up to that point resolved correctly and uniquely; a direct check of
  the Business Events list immediately after confirmed NO `QCTEST`-prefixed
  record was created by these attempts, so no orphaned test data was left
  behind either). Flagged to the requesting agent as a live environment
  finding, per this contract's mandate to stop and report rather than push
  through with guessed locators for the parts genuinely blocked (the create-
  form FIELD MAP above is real and confirmed; the SAVE COMMIT and its toast
  are not). `SUCCESS_TOAST` and `save()`'s post-save read-back are therefore
  gated behind `_require_verified()` / left as an `_UNVERIFIED` placeholder,
  exactly like gm_message_admin_page.py's own unresolved SUCCESS_TOAST.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

# Confirmed-live artifact only — see NAVIGATION note above. Never navigated
# to directly; always reached via the Product Menu > Content & Data >
# "Business Events" click path (open_business_events_list()).
BUSINESS_EVENTS_LIST_URL = control_panel_url(
    "/en/group/qatar-chamber/~/control_panel/manage"
    "?p_p_id=com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_R5V2"
    "&p_p_lifecycle=0&p_p_state=maximized&p_v_l_s_g_id=37246"
    "&_com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_R5V2_objectDefinitionId=49263"
)

_UNVERIFIED = "TODO: confirm against a real Save this batch could not safely complete (see module docstring's SAVE/TOAST note)"


def _text_input_by_id_substring(*substrings: str) -> str:
    """Copied verbatim from gm_message_admin_page.py's own helper of the
    same name — a DDM text input matched by stable id SUBSTRING(S) rather
    than the regenerating per-field random token. See module docstring."""
    conditions = " and ".join(f'contains(@id, "{s}")' for s in substrings)
    return f'xpath=//input[@type="text" and {conditions}]'


def _field_container(field_reference: str) -> str:
    """The field's own `.form-group` container, addressed by the STABLE,
    non-regenerating `data-field-reference` attribute (see module docstring
    — confirmed live to be unique and independent of document order, unlike
    the label-proximity xpath other Page Objects in this project needed)."""
    return f'[data-field-reference="{field_reference}"]'


class HomeBusinessEventsAdminPage(BasePage):
    # ---- Menu navigation (verbatim pattern from gm_message_admin_page.py) --
    PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
    CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
    BUSINESS_EVENTS_MENU_ITEM = '[role="menuitem"]:text-is("Business Events")'
    ADMIN_HOME_EN_URL_PATH = "/en/home"

    # ---- List screen --------------------------------------------------------
    ADD_EVENT_BUTTON = '[data-testid="fdsCreationActionButton"]'
    LIST_ROW = "table tbody tr"
    # The Event Title column's cell wraps its text in a child
    # `<span class="text-truncate">` (FDS grid's truncation renderer) —
    # confirmed live 2026-09-01 via outerHTML dump:
    # `<td class="cell-eventTitle" ...><span class="...text-truncate">TITLE
    # </span></td>`. Playwright's `:text-is()` matches the SMALLEST element
    # containing the exact text, which is this inner `<span>`, never the
    # `<td>` — so a `td:text-is(title)` selector structurally can never
    # match, at ANY wait length (this is not a render-timing race; a fixed
    # 30s wait reproduced the identical 0-count). See
    # `_row_by_title(title)` below, which every title-scoped row query now
    # goes through.
    _TITLE_CELL_TEXT = 'td.cell-eventTitle span:text-is("{title}")'

    # ---- Create/edit form fields (data-field-reference — see docstring) -----
    EVENT_TITLE = _text_input_by_id_substring("ddm$$eventTitle", "inputValue")
    EVENT_SECTOR = _text_input_by_id_substring("ddm$$eventSector", "inputValue")
    CATEGORY_SECTOR = _text_input_by_id_substring("ddm$$categorySector", "inputValue")
    LOCATION = _text_input_by_id_substring("ddm$$location", "inputValue")
    VENUE = _text_input_by_id_substring("ddm$$venue", "inputValue")
    TIME_ZONE = _text_input_by_id_substring("ddm$$timeZone")
    REGISTRATION_LIMIT = _text_input_by_id_substring("ddm$$registrationLimit")
    EVENT_DATE_TIME = _text_input_by_id_substring("ddm$$eventDateTime")
    START_DATE_TIME = _text_input_by_id_substring("ddm$$startDateTime")
    END_DATE_TIME = _text_input_by_id_substring("ddm$$endDateTime")

    EVENT_CATEGORY_CONTAINER = _field_container("eventCategory")
    EVENT_FORMAT_CONTAINER = _field_container("eventFormat")
    PUBLICATION_STATUS_CONTAINER = _field_container("publicationStatus")
    PIN_TO_HOME_CONTAINER = _field_container("pinToHome")
    EVENT_IMAGE_CONTAINER = _field_container("eventImage")

    # Confirmed-live accepted date format — see module docstring's DATE
    # FIELD note.
    DATE_FORMAT_EXAMPLE = "MM/DD/YYYY hh:mm AM"

    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # Not confirmed this session — see module docstring's SAVE/TOAST note.
    SUCCESS_TOAST = _UNVERIFIED

    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"HomeBusinessEventsAdminPage.{name} is an unverified "
                f"placeholder — a real Save must be observed live and the "
                f"resulting toast/notification locator confirmed before "
                f"this is relied on (see module docstring's SAVE/TOAST note)."
            )

    # ---- Navigation -----------------------------------------------------
    def open_business_events_list(self) -> "HomeBusinessEventsAdminPage":
        """Product Menu > Content & Data > Business Events. Mirrors
        GmMessageAdminPage.open_gm_message_edit_form()'s re-login-if-needed
        pattern and its English-locale entry point (see that method's own
        docstring for why /en/home is used unconditionally, not just on a
        detected AR session)."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(self.CONTENT_DATA_MENU_ITEM) or self.is_visible(self.PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))

        if not self.is_visible(self.CONTENT_DATA_MENU_ITEM):
            self.click(self.PRODUCT_MENU_TOGGLE)
            self.wait_for(self.CONTENT_DATA_MENU_ITEM)
        self.click(self.CONTENT_DATA_MENU_ITEM)
        self.wait_for(self.BUSINESS_EVENTS_MENU_ITEM)
        self.click(self.BUSINESS_EVENTS_MENU_ITEM)
        self.wait_for(self.ADD_EVENT_BUTTON, timeout=20000)
        return self

    def _row_by_title(self, title: str) -> str:
        """The list-screen row whose Event Title cell's own text (the inner
        `<span class="text-truncate">`, not the `<td>` — see `_TITLE_CELL_TEXT`
        above) exactly matches `title`. The single shared primitive behind
        `rows_matching_title()`, `row_for_title()`, and
        `delete_row_by_title()` — all three used a `td:text-is(title)`
        variant that could never match (confirmed live, root-caused
        2026-09-01: see `_TITLE_CELL_TEXT`'s own docstring)."""
        return f'{self.LIST_ROW}:has({self._TITLE_CELL_TEXT.format(title=title)})'

    def open_create_event_form(self) -> "HomeBusinessEventsAdminPage":
        self.click(self.ADD_EVENT_BUTTON)
        self.wait_for(self.EVENT_TITLE, timeout=20000)
        return self

    # ---- Field actions ------------------------------------------------------
    def fill_text_field(self, field_locator: str, value: str) -> "HomeBusinessEventsAdminPage":
        self.type(field_locator, value)
        return self

    def fill_date_field(self, field_locator: str, value: str) -> "HomeBusinessEventsAdminPage":
        """Types `value` (see DATE_FORMAT_EXAMPLE) directly into a date/time
        field WITHOUT pressing Escape afterward — confirmed live this
        session that a spontaneous unrelated-record navigation was
        reproduced once immediately after interacting with this exact field
        (see module docstring's SAVE/TOAST note); callers should chain
        straight into the next field action rather than adding their own
        dismissal keystroke."""
        self.click(field_locator)
        self.page.keyboard.type(value, delay=20)
        return self

    def select_combobox_option(self, container_locator: str, option_label: str) -> "HomeBusinessEventsAdminPage":
        """Open a custom combobox (button[role="combobox"] inside
        `container_locator`) and click the matching option — same widget
        shape as GmMessageAdminPage.select_status(), confirmed live for
        Event Category / Event Format / Status on this form. Deliberately
        does NOT use Escape to dismiss (see module docstring's SAVE/TOAST
        note) — closes only by clicking the target option itself."""
        self.click(f'{container_locator} button[role="combobox"]')
        self.wait_for('[role="listbox"]')
        self.click(f'[role="listbox"] [role="option"]:text-is("{option_label}")')
        return self

    def combobox_value(self, container_locator: str) -> str:
        return self.text(f'{container_locator} button[role="combobox"]').strip()

    # Documents-and-Media picker modal — same shape CommunityPartnersAdminPage
    # documents/confirms live for its own Partner Logo field: a `dialog`
    # containing `iframe[title="Select File"]` with the picker's OWN real
    # `input[type="file"]` inside it, NOT the outer page's field input.
    # Confirmed live THIS session (follow-up, fixing the batch pytest
    # failures) that Event Image needs the identical modal+iframe flow — a
    # direct `set_input_files()` on the outer page's own field input (the
    # form this method previously used) does not populate the field.
    UPLOAD_MODAL_IFRAME = 'iframe[title="Select File"]'
    UPLOAD_MODAL_ADD_BUTTON_TEXT = "Add"

    def upload_event_image(self, file_path: str) -> "HomeBusinessEventsAdminPage":
        """Click Select File, wait for the picker modal's own iframe, set
        the file on the PICKER'S inner input[type=file], then click the
        picker's own "Add" button (uploads AND auto-selects the file for
        the field in one action) — confirmed live this session, same
        pattern as CommunityPartnersAdminPage.upload_partner_logo()."""
        self.click(f'{self.EVENT_IMAGE_CONTAINER} button:has-text("Select File")')
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)
        frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click()
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
        except Exception:
            self.page.wait_for_timeout(1000)
        return self

    def select_status(self, label: str) -> "HomeBusinessEventsAdminPage":
        return self.select_combobox_option(self.PUBLICATION_STATUS_CONTAINER, label)

    def status_value(self) -> str:
        return self.combobox_value(self.PUBLICATION_STATUS_CONTAINER)

    # HEALED (2026-09-01, live-investigating TC 135748's reported "found 0
    # admin rows" failure — reproduced and root-caused this session, NOT the
    # `_row_by_title()` td/span fix, which was re-confirmed correct):
    # `save()`'s PRIOR flat `wait_for_timeout(2000)` treated "the Save button
    # was clicked" as "the record was persisted" — confirmed live this
    # session that BOTH are false signals of a real commit:
    #   - `is_save_error_shown()`'s absence is not proof of success — this
    #     session live-reproduced a genuine failed create (Event Title left
    #     empty, no `externalReferenceCode` ever appearing in the URL) where
    #     `is_save_error_shown()` ALSO returned False (no banner text
    #     rendered in that failure shape either) — the banner check is a
    #     real, correct signal for the field-specific-error shape it was
    #     built for, but is not a general "did this commit" oracle.
    #   - `status_value()` reads the combobox's CURRENT DOM value, i.e.
    #     whatever was selected before Save was clicked, regardless of
    #     whether the POST actually committed — it cannot distinguish "Save
    #     succeeded" from "Save is still in flight/failed silently".
    # CONFIRMED LIVE, this session (two real successful Saves observed):
    # every genuine commit navigates the URL to include
    # `..._externalReferenceCode=<uuid>` (the just-created/edited record's
    # own ERC) — confirmed on two independent creates
    # (`...externalReferenceCode=52866ccd-742f-a58d-daee-477b0b1e4d1e`,
    # `...externalReferenceCode=9fea8061-c67d-2cf1-73ac-584939ddb0e6`).
    # CONFIRMED LIVE the negative case too: a Save attempt with a genuinely
    # empty Event Title left the URL WITHOUT any `externalReferenceCode`
    # param at all — the pre-Save create-form URL and the failed-Save URL
    # are identical in this one respect. `ENTRY_PERSISTED_URL_MARKER` below
    # matches the bare `externalReferenceCode=` substring only (not the
    # `..._ObjectDefinitionsPortlet_R5V2_` prefix), because that portlet
    # instance id REGENERATES per session (see module docstring's NAVIGATION
    # note) and a full-prefix match would silently stop matching on a future
    # session's differently-numbered instance.
    ENTRY_PERSISTED_URL_MARKER = "externalReferenceCode="
    SAVE_COMMIT_TIMEOUT_MS = 8000

    def save(self) -> "HomeBusinessEventsAdminPage":
        self.click(self.SAVE_BUTTON)
        try:
            self.page.wait_for_url(
                lambda url: self.ENTRY_PERSISTED_URL_MARKER in url,
                timeout=self.SAVE_COMMIT_TIMEOUT_MS,
            )
        except Exception:  # noqa: BLE001 — a genuine validation failure (or a
            # slow-but-eventually-successful commit past this budget) never
            # gets this URL marker; let the caller's own
            # is_save_error_shown()/is_entry_persisted() assertions name the
            # real problem instead of raising a raw Playwright timeout here.
            pass
        return self

    def is_entry_persisted(self) -> bool:
        """True once this Save has actually committed server-side — see
        `save()`'s own HEALED docstring entry for why `is_save_error_shown()`
        being False and `status_value()` reading the expected label are BOTH
        insufficient proof of a real commit on their own. Callers creating a
        record should assert this immediately after `save()`, before relying
        on any downstream state (the public-page poll, `rows_matching_title()`,
        etc.) that would otherwise fail several steps later with a much less
        specific error."""
        return self.ENTRY_PERSISTED_URL_MARKER in self.page.url

    def cancel(self) -> "HomeBusinessEventsAdminPage":
        self.click(self.CANCEL_BUTTON)
        return self

    # ---- State queries --------------------------------------------------------
    # Mirrors GmMessageAdminPage.is_save_error_shown()'s confirmed-live signal.
    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    def is_save_error_shown(self) -> bool:
        body_text = self.page.locator("body").inner_text()
        return self.SAVE_ERROR_BANNER_TEXT in body_text or self.INLINE_REQUIRED_TEXT in body_text

    def save_error_text(self) -> str:
        """The real banner/inline text around whichever error string
        matched, mirroring GmMessageAdminPage.save_error_text()'s pattern —
        added 2026-08-31 (this method did not previously exist on this Page
        Object). Live-confirmed this session that
        `SAVE_ERROR_BANNER_TEXT`/`INLINE_REQUIRED_TEXT` correctly resolve to
        the real, field-specific banner ("This form is invalid. Check field
        Category / Sector."/"...Event Format.") on THIS form — the prior
        batch's "entire nav menu" diagnostic came from the CALLING TEST's
        own `body.inner_text()[:300]` debug slice (body's first 300 chars
        happen to fall inside this admin SPA's persistent Product Menu
        panel), not from this Page Object's own error detection, which was
        never actually broad. This method exists so a test's failure
        message names the real offending field instead of re-deriving (or
        mis-deriving) that slice itself."""
        body_text = self.page.locator("body").inner_text()
        idx = body_text.find(self.SAVE_ERROR_BANNER_TEXT)
        if idx == -1:
            idx = body_text.find(self.INLINE_REQUIRED_TEXT)
        return body_text[idx: idx + 120] if idx != -1 else ""

    def is_success_toast_shown(self) -> bool:
        self._require_verified(self.SUCCESS_TOAST, "SUCCESS_TOAST")
        return self.is_visible(self.SUCCESS_TOAST)

    # Safety cap on the delete-all-matches loop below — real duplicate counts
    # observed live have been 1-2 per stuck run; this is generous headroom,
    # not a tuned/expected value.
    MAX_DUPLICATE_DELETE_ATTEMPTS = 10

    def delete_row_by_title(self, title: str) -> bool:
        """Delete EVERY row exactly matching `title` via its own row kebab ->
        Delete -> confirm, mirroring CommunityPartnersAdminPage.delete_row_by_name()'s
        confirmed-live flow on this project's other Object Definition grid.
        Returns True if at least one row was deleted, False if none matched.

        HEALED (2026-08-31, live investigation of both TCs' teardown): the
        prior `_best_effort_delete()` helper in the test module reopened the
        record's EDIT form and clicked a bare `button:has-text("Delete")` —
        confirmed live this session that this resolves to the Event Image
        field's OWN per-file "Delete" button (removes the uploaded image),
        NOT a record-delete action; the edit form has no "Delete" button of
        its own (Save/Cancel only, like every sibling Object Definition
        form in this project) — that prior teardown was a silent no-op that
        never actually deleted the QCTEST record. This method operates on
        the LIST screen's row kebab instead, the real delete entry point,
        confirmed live end-to-end against a real record created this
        session (row 112951, deleted successfully).

        HEALED AGAIN (2026-09-01, root-causing the batch pytest run's
        "STRICT MODE VIOLATION ... resolved to 2 elements" failure on the
        public Business Events section): confirmed live this session that
        the ROOT CAUSE of the accumulating QCTEST-135747 duplicates was THIS
        method only ever deleting the FIRST row matching `title` — the
        original version used `:has-text` (a substring match, not the exact
        match `row_for_title()` already uses elsewhere in this class) AND
        `kebab.first.click()`, so whenever a stranded duplicate from an
        earlier interrupted run already existed alongside the current run's
        own freshly-created row, only ONE of the two ever got deleted per
        call — the other was silently left behind every single run,
        guaranteeing exactly the "2 elements" collision the public-page
        assertion hit. Confirmed live: 3 real leftover QCTEST rows were
        found in the admin grid this session (113026/113270 both titled
        "QCTEST-135747 Doha SME Growth Summit", 113291 titled
        "QCTEST-135748 Doha Trade Facilitation Briefing", the latter still
        Status=Published — a stranded mid-flow record from the overnight
        network-interrupted run, not a THIS-method defect), all three
        deleted successfully via the SAME kebab->Delete->confirm flow
        confirmed below, re-navigating the list between deletes (an
        in-place DOM check right after `confirm.click()` still showed the
        just-deleted row — the grid's delete does not re-render the table
        in place; a fresh `open_business_events_list()` navigation is
        required to observe it gone, confirmed live via repeated navigate +
        query). This method now loops, deleting every EXACT (`:text-is`,
        not substring) match one at a time with a fresh list navigation
        between iterations, until none remain or
        MAX_DUPLICATE_DELETE_ATTEMPTS is hit.

        Also confirmed live this session: the row kebab's OWN click can be
        intercepted by the #qcChatbot launcher widget on this admin grid
        (a real, reproduced 30s Playwright action-timeout naming
        `button.qc-launcher` as the intercepting element) — see
        core/web/overlays.py's module docstring for the disclosed finding.
        `core.web.overlays._dismiss_chatbot_launcher()` is called before
        every kebab click below at THIS call site specifically (deliberately
        not wired into the suite-wide `dismiss_overlays()`, which runs on
        every navigation via BasePage.open() — see that function's own
        docstring for why removing the launcher everywhere would be a much
        bigger behavior change than this one confirmed-live interception
        calls for).

        The loop below also breaks on NO PROGRESS (the matching-row count
        does not decrease between iterations) rather than only ever
        stopping at MAX_DUPLICATE_DELETE_ATTEMPTS — a delete that silently
        no-ops should fail fast, not spend up to 10 full
        `open_business_events_list()` navigations (each with its own 20s
        internal waits) in a test's `finally` block before giving up."""
        from core.web.overlays import _dismiss_chatbot_launcher

        deleted_any = False
        previous_count = None
        for _ in range(self.MAX_DUPLICATE_DELETE_ATTEMPTS):
            self.open_business_events_list()
            row = self.page.locator(self._row_by_title(title))
            current_count = row.count()
            if current_count == 0:
                break
            if previous_count is not None and current_count >= previous_count:
                # A delete attempt ran last iteration but the count didn't
                # drop — the delete is silently no-op'ing (e.g. confirm
                # dialog didn't appear/click), not just "more duplicates
                # than expected". Stop spending navigations on a flow that
                # isn't working rather than looping to the attempt cap.
                break
            previous_count = current_count
            _dismiss_chatbot_launcher(self.page)
            kebab = row.first.locator('button[aria-haspopup="true"]')
            kebab.click()
            # HEALED (2026-09-01, Item 2 wait audit): the kebab menu opening
            # is a real DOM event (the menuitem attaching) — wait on that
            # directly instead of a blind 300ms sleep. Bounded generously
            # above the old fixed value so a slower open still succeeds.
            delete_item = self.page.locator('[role="menuitem"]:visible:has-text("Delete")')
            delete_item.first.wait_for(state="visible", timeout=3000)
            delete_item.first.click()
            confirm = self.page.get_by_role("button", name="Delete")
            confirm.wait_for(state="visible", timeout=5000)
            confirm.click()
            # HEALED (2026-09-01, Item 2 wait audit): the observable signal
            # for "delete committed" is the row disappearing from THIS
            # in-place DOM (before the loop's own fresh navigation even
            # happens) — poll for detachment instead of a blind 1500ms
            # sleep, with the old fixed value kept as the upper-bound
            # timeout, not a mandatory wait.
            try:
                row.first.wait_for(state="detached", timeout=1500)
            except Exception:  # noqa: BLE001 — module docstring already
                # documents that this grid does not always re-render the
                # table in place after a delete; the loop's own next
                # `open_business_events_list()` navigation is the real
                # confirmation, so a lingering-but-stale row here is not
                # itself a failure.
                pass
            deleted_any = True
        return deleted_any

    def rows_matching_title(self, title: str) -> int:
        """Count of list-screen rows whose Event Title cell exactly matches
        `title` — a state query, no wait/assert. Callers should check this
        BEFORE `wait_for(row_for_title(title))`/`click()`: those two
        BasePage calls resolve a NON-`.first` locator (deliberately, so a
        genuine 2-row collision fails loudly instead of silently acting on
        whichever row Playwright's strict mode happens to prefer — see
        `row_for_title()`'s own docstring, HEALED 2026-09-01 entry, for why
        this project chose "fail loud" over `.first`/`unpublish-all`).

        HEALED AGAIN (2026-09-01, root-causing a live-reproduced false 0
        immediately after a just-confirmed-published event): this method's
        `td:text-is(title)` selector could NEVER match, at any wait length —
        see `_TITLE_CELL_TEXT`'s own docstring on `_row_by_title()` for the
        confirmed-live DOM reason (the exact-text match lands on a nested
        `<span class="text-truncate">`, not the `<td>` itself). This was
        NOT a grid-render timing race — a direct live check immediately
        after `open_business_events_list()` returned `td:text-is(...)` = 0
        while the identical row, queried via `span:text-is(...)` scoped to
        `td.cell-eventTitle`, returned 1 in the same instant, and a 2-second
        explicit wait before the OLD selector changed nothing. Delegates to
        `_row_by_title()` now, the same fix applied to `row_for_title()` and
        `delete_row_by_title()` below."""
        return self.page.locator(self._row_by_title(title)).count()

    def row_for_title(self, title: str) -> str:
        """A list-screen row's ID-cell link for the row whose Event Title
        cell matches `title` exactly — for locating a just-created/just-
        edited record to reopen it. `:text-is` (not `:has-text`)
        deliberately avoids the substring-collision risk the task brief
        itself flagged (e.g. an existing "SME Growth & Innovation Summit"
        record substring-matching a "...SME Growth Summit" test title).

        HEALED (2026-09-01, root-causing TC 135748's live-reproduced 15s
        timeout on `admin.wait_for(row_link, timeout=15000)`): the PRIOR
        version, `f'{self.LIST_ROW} a:text-is("{title}")'`, assumed the
        Event Title cell itself was (or contained) an anchor — confirmed
        live this session it is a BARE `<td>` with no `<a>` at all; the
        row's only real anchor is its ID cell's edit link
        (`td.cell-id a`, the exact class CommunityPartnersAdminPage's own
        ROW_ID_LINK precedent already established for this same admin-grid
        family). A direct DOM query confirmed `a:text-is(<any real Event
        Title in the live grid>)` returns 0 matches even for a genuine,
        currently-rendered row — this locator could never resolve for ANY
        title, not just QCTEST ones, which is exactly why
        `wait_for(..., timeout=15000)` ran out the full budget instead of
        finding a stale/wrong element. Scopes the row by its title cell
        (mirrors `delete_row_by_title()`'s own `:has(td:text-is(...))`
        primitive) and returns that row's ID-cell link instead.

        SECOND, DISTINCT ROOT CAUSE (2026-09-01, live-investigating TC
        135748's REPORTED 15s timeout on `admin.wait_for(row_link,
        timeout=15000)` AFTER this `td.cell-id a` heal was already in place
        — the heal above was re-confirmed correct, not the cause this time):
        confirmed live via a direct `td` dump of the real grid that TWO rows
        (115322 and 115365) both carried the EXACT title
        "QCTEST-135748 Doha Trade Facilitation Briefing", both Status
        Published — a stranded duplicate from an earlier run that crashed
        before its own teardown ran (this method's locator has no
        `.first`/`first=True`, deliberately — see `rows_matching_title()`
        above), so `BasePage.wait_for(row_link, timeout=15000)` (called with
        `first=False`) hit a genuine Playwright STRICT MODE violation (2
        elements), not a real 15s search timeout; the `except Exception`
        recovery path (license-gate/reauth clear) can't fix a strict-mode
        violation, so it re-raised, and the surfaced failure text read
        exactly like "row not found within 15s" even though the row(s) were
        present and rendered on page 1 the whole time. Also confirmed live
        this session: the admin grid has NO PAGINATION at the current row
        count (13 rows, one page, next/prev both `disabled`) — a
        newly-created row is NOT sorted onto a later page; pagination was
        ruled out as a cause entirely, do not add pagination-aware searching
        here, it would be dead code against this grid's real behavior.
        FIX: both stray duplicate rows were deleted live (confirmed via a
        fresh `open_business_events_list()` navigation afterward — this
        grid's delete does not re-render in place, per
        `delete_row_by_title()`'s own docstring). The TEST was changed to
        call `rows_matching_title()` and assert exactly 1 match before
        touching `row_for_title()`/`wait_for()`/`click()` at all, so a future
        duplicate fails loudly and immediately with a message naming the
        real problem instead of a misleading phantom timeout — and to call
        `delete_row_by_title(qctest_title)` once BEFORE creating its own
        record, so a crash-before-teardown in one run doesn't strand data
        that poisons the next. `.first`/an "unpublish every matching row"
        loop were deliberately rejected: TC 135748 asserts that unpublishing
        AN event removes it, and silently acting on an arbitrary one of N
        same-titled rows (or unpublishing all of them) would make a pass
        prove nothing about that mechanism — see the test module's own
        updated docstring."""
        return f'{self._row_by_title(title)} td.cell-id a'

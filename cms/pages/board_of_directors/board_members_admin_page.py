"""
web/pages/board_of_directors/board_members_admin_page.py — BoardMembersAdminPage.

Control_Panel Page Object for PBI 129398 (QC-ABOUT-006 — Board of Directors
& General Director), backing the PER-MEMBER admin surface: Content & Data >
"Board Members" — a Liferay Object Definition (objectDefinitionId=80051,
groupId=37246), CONFIRMED LIVE this session (2026-08-25, headless Chromium,
1920x1080, TEST_USER) after 3 full login attempts hit the documented qcdev
congestion issue (session_guard/license_gate retries exhausted twice before
a 3rd attempt succeeded — see the batch report for the timeline; this is the
pre-existing, previously-documented environment flakiness, not new).

This is NOT the same surface as board_of_directors_admin_page.py (that one
is the page-level Liferay fragment config — Members endpoint, Hero banner
URL, etc, no per-member fields). Do not merge the two Page Objects.

CONFIRMED LIVE:
  - Menu path: Content & Data > Board Members (role=menuitem both times) —
    reachable via the sidebar Product Menu, same pattern as
    org_structure_admin_page.py. The rendered LIST URL embeds a per-session
    portlet instance id (this session: ...ObjectDefinitionsPortlet_P3E8...,
    objectDefinitionId=80051) — never hardcode it; always navigate via menu.
  - List view: a flat data grid, 18 rows this session (18 live board
    members). Each row's ID cell (`td.cell-id a`) is itself a direct link
    into the EDIT form for that record
    (`.../object_entries/edit_object_entry?...externalReferenceCode=
    QCDEMO-129398-member-NN`), confirmed live for member-01 (record id
    80191) — clicking it is simpler and more reliable than the kebab menu's
    View item (kebab exists too — one match per row via a generic
    "Actions"/dropdown-toggle button — but the ID-link path was what got
    exercised and confirmed this session; ROW_ACTIONS_KEBAB is documented
    for completeness, not independently exercised).
  - Edit form fields confirmed by LIVE role-based harvest (get_by_role,
    tools/extract_locators.py's JS_HARVEST logic run in-process against the
    real rendered form, member-01's record):
      get_by_role("combobox", name="Chairman")          Member Category (current value shown as its own accessible name — the combobox's name reflects the SELECTED option text, confirmed live: member-01 is the Chairman)
      get_by_role("textbox", name="Detailed Biography") CKEditor rich-text (get_by_role, not a plain textarea)
      get_by_role("textbox", name="Display Order")
      get_by_role("textbox", name="Short Bio")
      get_by_role("textbox", name="Professional Experience Entries")
      get_by_role("button", name="Select File")         Member Photo upload trigger
      get_by_role("button", name="member-01.jpg")        already-uploaded photo chip (Download/Delete buttons nested)
      get_by_role("button", name="Save")
      get_by_role("button", name="Cancel")
  - 7x locale-flag toggle pairs (get_by_test_id("triggerButton")/
    ("triggerText"), each showing "en-us") confirmed present — one per
    bilingual field (Full Name, Position Label, Role Badge Label, Photo Alt
    Text, Short Bio, Detailed Biography, Professional Experience Entries
    per the case inventory), matching cms-profile.md's EN/AR locale model.
    Non-unique on the page (7 matches) — must be scoped to the field's own
    container, not used bare; FIELD_LOCALE_TOGGLE below documents the
    pattern, per-field scoping is done via _field_container().
  - NOT captured by the role harvest this session (below-fold / DDM label
    text without a strong ARIA role, same class of gap
    org_structure_admin_page.py already documented and worked around with a
    text-anchored locator): Full Name (EN/AR), Position Label (EN/AR), Role
    Badge Label (EN/AR), Photo Alt Text (EN/AR), Active Status (checkbox),
    Enable Share Icons (checkbox). These use the SAME `_field_after_label()`
    text-anchor pattern already verified working on this project's other
    DDM-rendered Object Definition form (Departments) rather than guessed
    ids — re-verify the exact anchor tag (input vs [role=textbox]) against
    the live form before first use per field; flagged _NOT_ROLE_CONFIRMED
    below so a coming heal pass knows exactly which constants are the
    weaker tier.
  - Member Category combobox options confirmed present (live dropdown open
    not captured this session — case docs list Chairman of the Board / Vice
    Chairman / Board Member / General Manager as the 4 values, consistent
    with board_of_directors_page.py's confirmed 4 public sections).

ENVIRONMENT NOTE: qcdev's documented login/session congestion (see
core/web/session_guard.py, core/web/license_gate.py) was directly observed
this session — 2 of 3 full navigation attempts failed at the login step
despite session_guard's internal 3x retry, the 3rd succeeded. Tests in this
module inherit BasePage's built-in retry via those two modules; no
additional retry logic belongs here.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
BOARD_MEMBERS_MENU_ITEM = '[role="menuitem"]:text-is("Board Members")'
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'

_NOT_ROLE_CONFIRMED = "text-anchored (DDM label pattern, see org_structure_admin_page.py) — not captured by the live role harvest, re-verify before first use"


def _field_after_label(label: str, tag: str = "input") -> str:
    """Text-anchored locator: the {tag} nearest AFTER the exact visible label
    text. Same pattern as org_structure_admin_page.py's helper — this
    Object Definition's DDM-rendered form shares the same lack of stable
    id/name/for-label wiring on several fields."""
    return f'xpath=//*[normalize-space(text())="{label}"]/following::{tag}[1]'


class BoardMembersAdminPage(BasePage):
    # ---- List screen --------------------------------------------------------
    ADD_BUTTON = '[data-testid="fdsCreationActionButton"]'
    LIST_ROW = "table tbody tr"
    ROW_ID_LINK = "td.cell-id a"
    ROW_ACTIONS_KEBAB = 'button[aria-label="Actions"], button.dropdown-toggle'
    SEARCH_INPUT = 'input[placeholder="Search"], input[type="search"]'
    # 3-dot kebab -> View/Delete/Permissions menu, per the QA Manager's
    # screenshot-confirmed description (module docstring) — the kebab
    # itself is present (confirmed live, ROW_ACTIONS_KEBAB matched 1 per
    # row) but the Delete item text/confirm-dialog flow was NOT
    # independently exercised this session (time-boxed out, same
    # _NOT_ROLE_CONFIRMED caveat as the text-anchored form fields above).
    KEBAB_DELETE_MENU_ITEM = '[role="menuitem"]:text-is("Delete"), li:has-text("Delete") a, button:has-text("Delete")'
    DELETE_CONFIRM_BUTTON = 'button:has-text("Delete"):visible, button:has-text("Yes"):visible'

    # ---- Edit/View form — role-confirmed live -------------------------------
    MEMBER_CATEGORY_COMBOBOX = '[role="combobox"]'
    DETAILED_BIOGRAPHY = '[role="textbox"][aria-label="Detailed Biography"], [aria-label="Detailed Biography"][contenteditable="true"]'
    # No aria-label on this field at all (confirmed live 2026-08-26, unlike
    # Short Bio/Professional Experience which do carry one) — Liferay's DDM
    # id embeds the field's programmatic name instead:
    # "..._ddm$$displayOrder$<hash>$0$$en_US". Match on that substring.
    DISPLAY_ORDER = 'input[id*="ddm$$displayOrder$"]'
    SHORT_BIO = '[role="textbox"][aria-label="Short Bio"], textarea[aria-label="Short Bio"]'
    PROFESSIONAL_EXPERIENCE_ENTRIES = '[role="textbox"][aria-label="Professional Experience Entries"], textarea[aria-label="Professional Experience Entries"]'
    PHOTO_SELECT_FILE_BTN = 'button:has-text("Select File")'
    PHOTO_UPLOADED_CHIP = 'button:has-text(".jpg"), button:has-text(".png")'
    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # ---- Edit/View form — CONFIRMED LIVE 2026-08-26 (member-04, "Board
    # Member" category, ERC QCDEMO-129398-member-04), superseding the
    # earlier _NOT_ROLE_CONFIRMED text-anchored constants below. The
    # `_field_after_label()` xpath helper NEVER resolved these six fields —
    # confirmed root cause this session: xpath's `//` axis does not pierce
    # the shadow root this Object Definition form renders inside, the same
    # boundary `document.querySelectorAll()` also cannot cross. That is why
    # get_by_role()/get_by_text() (which DO pierce shadow DOM) succeeded
    # where raw xpath silently returned zero matches every time.
    #
    # There is NO separate "(EN)"/"(AR)" field pair for Full Name, Position
    # Label, Role Badge Label, or Photo Alt Text — confirmed live via the
    # rendered form and its accessibility snapshot. Each is ONE field with
    # its own locale-toggle button beside it (LOCALE_TOGGLE_BUTTON, 7 pairs
    # total on this form); switching locale re-targets the SAME input, it
    # does not reveal a second one. The FULL_NAME_EN/AR-style constants below
    # were therefore testing a field shape that doesn't exist. Confirmed via
    # accessibility snapshot (interesting_only=False) + a live DOM id dump
    # matching the SAME `ddm$$<camelCase>$<hash>$0$$en_US...` id pattern
    # DISPLAY_ORDER already established as reliable for this form:
    FULL_NAME = 'input[id*="ddm$$fullName$"]'
    POSITION_LABEL = 'input[id*="ddm$$positionLabel$"]'
    ROLE_BADGE_LABEL = 'input[id*="ddm$$roleBadgeLabel$"]'
    PHOTO_ALT_TEXT = 'input[id*="ddm$$photoAltText$"]'
    LOCALE_TOGGLE_BUTTON = '[data-testid="triggerButton"]'

    # ---- Active Status / Enable Share Icons checkboxes — UNCONFIRMED this
    # session, deliberately left as the old text-anchored constants rather
    # than guessed. The accessibility snapshot (interesting_only=False)
    # DID report both as role=checkbox with their exact names ("Active
    # Status", "Enable Share Icons"), but neither `get_by_role("checkbox",
    # name=...)` NOR any DOM query (`input[type=checkbox]`, `[role=checkbox]`,
    # a class/id substring scan) could independently re-locate the same
    # elements as a live Locator in 3 retries — a real reproducible gap
    # between what the snapshot reports and what a Locator can resolve, not
    # explained by shadow-DOM piercing (get_by_role already pierces it, per
    # FULL_NAME above). Do not build a test on FULL_NAME_EN/AR-era
    # `_field_after_label(..., "input")` for these two — it was never
    # confirmed live either. See the batch report for the follow-up this
    # needs (a slower/headed re-probe) before scripting Active Status /
    # Enable Share Icons cases.
    ACTIVE_STATUS_CHECKBOX = _field_after_label("Active Status", "input")
    ENABLE_SHARE_ICONS_CHECKBOX = _field_after_label("Enable Share Icons", "input")

    # ---- Navigation -----------------------------------------------------------
    def open_board_members_list(self) -> "BoardMembersAdminPage":
        """Navigate via Content & Data > Board Members, never a saved/
        hardcoded portlet-instance URL — mirrors
        OrgStructureAdminPage.open_departments_list()'s documented reasoning:
        the rendered list URL embeds a per-session Liferay portlet instance
        id that is regenerated every session and 404s if reused."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url("/home"))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url("/home"))

        if not self.is_visible(CONTENT_DATA_MENU_ITEM):
            self.click(PRODUCT_MENU_TOGGLE)
            self.wait_for(CONTENT_DATA_MENU_ITEM)
        self.click(CONTENT_DATA_MENU_ITEM)
        self.click(BOARD_MEMBERS_MENU_ITEM)
        # LIST_ROW ("table tbody tr") matches all 18 live rows — BasePage.wait_for()
        # resolves through Playwright's strict-mode waitForSelector, which throws
        # on a multi-match locator (confirmed live 2026-08-25) the same way
        # click()/fill() do. Scope to the first row's existence, not the bare
        # multi-row selector.
        self.wait_for(f"{self.LIST_ROW} >> nth=0")
        return self

    def open_member_edit_form_by_row_index(self, index: int = 0) -> "BoardMembersAdminPage":
        """Click the ID-link of the row at `index` (0-based) — confirmed
        live as a direct route into the record's edit form, cheaper than the
        kebab > View path."""
        self.click(f"{self.LIST_ROW} >> nth={index} >> {self.ROW_ID_LINK}")
        self.wait_for(self.SAVE_BUTTON)
        return self

    def open_member_edit_form_by_name(self, full_name: str) -> "BoardMembersAdminPage":
        self.click(f'{self.LIST_ROW}:has-text("{full_name}") >> {self.ROW_ID_LINK}')
        self.wait_for(self.SAVE_BUTTON)
        return self

    def open_new_member_form(self) -> "BoardMembersAdminPage":
        self.click(self.ADD_BUTTON)
        self.wait_for(self.SAVE_BUTTON)
        return self

    # ---- Form actions -----------------------------------------------------------
    def fill_member_form(
        self,
        full_name_en: str = None,
        position_label_en: str = None,
        role_badge_label_en: str = None,
        photo_alt_text_en: str = None,
        short_bio_en: str = None,
        detailed_biography_en: str = None,
        professional_experience_entries: str = None,
        display_order: str = None,
        active_status: bool = None,
        enable_share_icons: bool = None,
    ) -> "BoardMembersAdminPage":
        """EN-locale setters only — see FULL_NAME's docstring: there is no
        separate AR field to fill, AR needs a locale-toggle click first
        (see toggle_locale_for()), out of scope for the fields this batch
        confirmed live."""
        if full_name_en is not None:
            self.type(self.FULL_NAME, full_name_en)
        if position_label_en is not None:
            self.type(self.POSITION_LABEL, position_label_en)
        if role_badge_label_en is not None:
            self.type(self.ROLE_BADGE_LABEL, role_badge_label_en)
        if photo_alt_text_en is not None:
            self.type(self.PHOTO_ALT_TEXT, photo_alt_text_en)
        if short_bio_en is not None:
            self.type(self.SHORT_BIO, short_bio_en)
        if detailed_biography_en is not None:
            self.type(self.DETAILED_BIOGRAPHY, detailed_biography_en)
        if professional_experience_entries is not None:
            self.type(self.PROFESSIONAL_EXPERIENCE_ENTRIES, professional_experience_entries)
        if display_order is not None:
            self.type(self.DISPLAY_ORDER, display_order)
        if active_status is not None:
            self.set_checkbox(self.ACTIVE_STATUS_CHECKBOX, active_status)
        if enable_share_icons is not None:
            self.set_checkbox(self.ENABLE_SHARE_ICONS_CHECKBOX, enable_share_icons)
        return self

    def select_member_category(self, category: str) -> "BoardMembersAdminPage":
        self.click(self.MEMBER_CATEGORY_COMBOBOX)
        self.click(f'[role="option"]:text-is("{category}")')
        return self

    def upload_member_photo(self, file_path: str) -> "BoardMembersAdminPage":
        self.click(self.PHOTO_SELECT_FILE_BTN)
        self.upload_file('input[type="file"]', file_path)
        return self

    def save(self) -> "BoardMembersAdminPage":
        self.click(self.SAVE_BUTTON)
        return self

    def cancel(self) -> "BoardMembersAdminPage":
        self.click(self.CANCEL_BUTTON)
        return self

    # ---- State queries --------------------------------------------------------
    # CONFIRMED LIVE 2026-08-26 (member-04, clearing Full Name then Save):
    # `.alert-danger, [role="alert"]` (the OLD selector) matches NOTHING on
    # this form — it produced 3 confirmed false-positive bugs earlier this
    # session (see the module's CRITICAL LESSON note / batch report). What
    # the form actually renders on a blocked save, confirmed via a raw
    # inner_text() diff before/after clicking Save:
    #   1. An inline per-field message, exact text "This field is required."
    #      appearing directly under the offending field's label.
    #   2. A page-level toast/banner, exact text starting
    #      "This form is invalid. Check field <FieldName>." — this is the
    #      reliable, field-name-agnostic signal used below (a plain text
    #      match, not a CSS class, since no stable class/role was found for
    #      either #1 or #2's container in the harvest).
    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    def is_save_error_shown(self) -> bool:
        body_text = self.page.locator("body").inner_text()
        return self.SAVE_ERROR_BANNER_TEXT in body_text or self.INLINE_REQUIRED_TEXT in body_text

    def save_error_text(self) -> str:
        body_text = self.page.locator("body").inner_text()
        idx = body_text.find(self.SAVE_ERROR_BANNER_TEXT)
        if idx == -1:
            idx = body_text.find(self.INLINE_REQUIRED_TEXT)
        return body_text[idx: idx + 120] if idx != -1 else ""

    def find_row_index_by_category(self, category_text: str, exclude: tuple = ()) -> int:
        """Scan the LIST rows' own rendered text for one that mentions
        `category_text` and none of `exclude` — safer than
        `LIST_ROW:has-text(...) >> nth=0`, which the existing
        `board_member_row` fixture uses and which this session found can
        resolve to the WRONG category (see the batch report: that selector
        landed on the Chairman record, not a true "Board Member", when
        probing this same list) because a row's rendered text is not
        guaranteed to contain only its own category. Returns -1 if none
        matches."""
        rows = self.page.locator(self.LIST_ROW)
        for i in range(rows.count()):
            txt = rows.nth(i).inner_text()
            if category_text in txt and not any(bad in txt for bad in exclude):
                return i
        return -1

    def open_member_edit_form_by_row_index_fresh(self, index: int) -> "BoardMembersAdminPage":
        """Re-navigate to the list fresh, then open the row at `index` —
        used by teardown finalizers so a revert never assumes the form the
        test left open is still there/error-free (cms-profile.md's
        data-hygiene lesson: a finalizer that types into a stale/broken
        page state is exactly what stranded real content mutated earlier
        this session)."""
        self.open_board_members_list()
        return self.open_member_edit_form_by_row_index(index)

    def row_visible(self, full_name: str) -> bool:
        return self.is_visible(f'{self.LIST_ROW}:has-text("{full_name}")')

    def row_count(self) -> int:
        return self.page.locator(self.LIST_ROW).count()

    def delete_member_by_name(self, full_name: str) -> "BoardMembersAdminPage":
        """QCTEST- disposable-record cleanup path (cms-profile.md Test-Data
        Policy): locate the row by name, open its kebab, click Delete,
        confirm. See KEBAB_DELETE_MENU_ITEM's docstring note — not
        independently exercised live this session; if the kebab item text
        differs on a rerun, this is the one locator to heal."""
        row = f'{self.LIST_ROW}:has-text("{full_name}")'
        self.click(f"{row} >> {self.ROW_ACTIONS_KEBAB}")
        self.click(self.KEBAB_DELETE_MENU_ITEM)
        if self.is_visible(self.DELETE_CONFIRM_BUTTON):
            self.click(self.DELETE_CONFIRM_BUTTON)
        return self

    def field_value(self, field_locator: str) -> str:
        return self.page.locator(field_locator).input_value()

"""
cms/pages/home_about_summary/home_about_summary_admin_page.py —
HomeAboutSummaryAdminPage.

Control_Panel Page Object for PBI 129389 (QC-HOME-013 — "About Us Section &
Last Year Achievements Counters", bundled as one Page Object per
standards.md's own note on this row), backing the homepage "About Us"
summary widget (public counterpart: web/pages/home_about_summary/
home_about_summary_page.py).

REAL, LIVE-VERIFIED FACTS (this session, 2026-09-06, Playwright MCP against
qcdev, authenticated via TEST_USER — disclosed fallback per this batch's
instructions, since no admin edit-form locators existed yet for this page
and the CLI extractor needs a reachable, already-authenticated state to
target the right screen):

  - This homepage section is actually backed by TWO separate Liferay Object
    Definitions, both reachable via Product Menu -> Content & Data:
      1. "About Us Sections" (objectDefinitionId=51812) — a SINGLETON list
         (confirmed live: "Showing 1 to 1 of 1 entries"), one row, ID 52157,
         externalReferenceCode `QCDEMO-129389-ABOUT_US_SECTION-01` — this
         ERC is the live, confirmed source of the 129389 PBI number used
         below (no azure-devops MCP tool was available this session to
         resolve the parent PBI via the API; this is real evidence, not a
         guess — see the test module's docstring for the full trail).
         Confirmed live field labels/order: Building Image (Primary/
         Secondary/Tertiary upload buttons), Read More Label (AR/EN), Read
         More URL, Section Description (AR/EN, CKEditor rich-text), Section
         Heading (AR/EN), Section Tag (AR/EN), Years of Experience Badge
         (AR/EN). Save/Cancel only — no Status/Publish field on this form
         (same "no separate Publish action" shape as gm_message_admin_page.py
         and org_structure_admin_page.py).
      2. "About Us Counters" (objectDefinitionId=52004) — a REPEATABLE list,
         confirmed live with 5 rows this session: 4 seeded QCDEMO rows
         (externalReferenceCode `QCDEMO-129389-ABOUT_US_COUNTER-01..04`,
         Display Order 100/200/300/400) plus one extra non-QCDEMO row (ERC
         a bare UUID, Display Order 500) left over from prior exploration —
         NOT touched by this module. This test only ever opens counter
         row 01 (a single, real "counter set" per the case's Step 1
         wording), never the whole list.
         Confirmed live field labels/order on a counter row's edit form:
         Counter Active Status (checkbox), Counter Display Order (text),
         Counter Title (AR/EN), Counter Value (text, e.g. "145 +").
  - Neither form carries a stable id/name/for-label on its visible text
    inputs (same DDM-rendered-form problem already documented in
    gm_message_admin_page.py / org_structure_admin_page.py) — the same
    "label -> nearest following input" xpath pattern (`_field_after_label`,
    copied verbatim from that precedent) is reused here. No ambiguity
    requiring the id-substring fallback was observed live on either form
    this session (unlike GM Name/Salutation Heading on the GM's Message
    form) — plain `_field_after_label` resolved uniquely for every field
    probed.
  - HEALED (2026-09-06, live pytest run against qcdev, this session):
    building the object-entry edit URL from the GENERIC portlet id
    (`com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet`,
    no instance suffix) does NOT resolve to the specific record — it silently
    redirects to the generic Objects app default-folder LISTING screen
    instead (confirmed via a captured failure screenshot: "Objects >
    Default" folder grid, not the About Us Sections edit form). This is the
    SAME regenerating-portlet-instance-id caveat gm_message_admin_page.py's
    own docstring already flags for GM_MESSAGES_LIST_URL (e.g. `_P0O5`/
    `_R6Q1` this session, confirmed different from a prior exploration
    session) — a bare, instance-less URL is not a valid substitute.
    Navigation therefore goes through the real Product Menu -> Content &
    Data -> named menu item -> row ID link path every time (same pattern as
    GmMessageAdminPage.open_gm_message_edit_form()), never a hand-built
    portlet URL.
  - Real Liferay logout confirmed live this session: `GET /c/portal/logout`
    ends the session (Control Menu no longer present afterward); a
    subsequent `GET /c/portal/login` (or any control_panel URL while
    unauthenticated) renders the real login form again. This IS the
    genuine cross-session mechanism the test case's Step 3 ("Log out and
    log back in") requires — not a page reload, and not the fixture's
    normal storageState/session (this test drives a real logout so a real
    re-login is exercised).
  - No dedicated "Publish" action or success toast exists on either form
    (Save/Cancel only, same shape as gm_message_admin_page.py) — this
    module reuses that same disclosed substitution: "Publish succeeds"
    (case Step 1) is verified as "no validation error surfaced after
    Save", and the real verification of persistence is the reopen-and-
    read-back in Step 4, not a literal toast assertion.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

# ---- Confirmed-live Object Definition identifiers -------------------------
# (kept as documented artifacts of the confirmed shape, NOT navigated to
# directly — see module docstring; always reached via the menu.)
ABOUT_US_SECTION_ERC = "QCDEMO-129389-ABOUT_US_SECTION-01"
ABOUT_US_COUNTER_01_ERC = "QCDEMO-129389-ABOUT_US_COUNTER-01"
ABOUT_US_SECTION_RECORD_ID = "52157"  # the one live singleton record
ABOUT_US_COUNTER_01_RECORD_ID = "52165"  # counter row 01 (Display Order 100)

ADMIN_HOME_EN_URL_PATH = "/en/home"  # same locale-forcing entry as gm_message_admin_page.py


def _field_after_label(label: str, tag: str = "input") -> str:
    """Text-anchored locator: the {tag} nearest AFTER the exact visible label
    text — copied verbatim from gm_message_admin_page.py / org_structure_
    admin_page.py's precedent (this DDM-rendered form has the identical
    no-stable-id problem). See those modules' docstrings for the full
    rationale (file-input ambiguity, duplicate-label-node ambiguity) this
    shape guards against."""
    if tag == "input":
        tag = 'input[@type="text"]'
    return f'xpath=(//*[normalize-space(text())="{label}"]/following::{tag}[1])[1]'


class HomeAboutSummaryAdminPage(BasePage):
    # ---- Menu navigation (confirmed live; see module docstring on why a
    # hand-built portlet URL is not a valid substitute) ----------------------
    PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
    CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
    ABOUT_US_SECTIONS_MENU_ITEM = '[role="menuitem"]:text-is("About Us Sections")'
    ABOUT_US_COUNTERS_MENU_ITEM = '[role="menuitem"]:text-is("About Us Counters")'
    ABOUT_US_SECTION_ROW_ID_LINK = f'table tbody a:text-is("{ABOUT_US_SECTION_RECORD_ID}")'
    ABOUT_US_COUNTER_01_ROW_ID_LINK = f'table tbody a:text-is("{ABOUT_US_COUNTER_01_RECORD_ID}")'
    LIST_RENDER_TIMEOUT_MS = 20000  # same measured-live grid-render class as ROW_ID_LINK_RELOAD_TIMEOUT_MS

    # ---- About Us Sections (singleton) edit form fields -------------------
    SECTION_READ_MORE_LABEL_EN = _field_after_label("Read More Label (EN)")
    SECTION_READ_MORE_LABEL_AR = _field_after_label("Read More Label (AR)")
    SECTION_READ_MORE_URL = _field_after_label("Read More URL")
    SECTION_HEADING_EN = _field_after_label("Section Heading (EN)")
    SECTION_HEADING_AR = _field_after_label("Section Heading (AR)")
    SECTION_TAG_EN = _field_after_label("Section Tag (EN)")
    SECTION_TAG_AR = _field_after_label("Section Tag (AR)")
    SECTION_YEARS_BADGE_EN = _field_after_label("Years of Experience Badge (EN)")
    SECTION_YEARS_BADGE_AR = _field_after_label("Years of Experience Badge (AR)")

    # ---- About Us Counters (row 01) edit form fields -----------------------
    COUNTER_ACTIVE_STATUS_CHECKBOX = _field_after_label(
        "Counter Active Status", 'input[type="checkbox"]'
    )
    COUNTER_DISPLAY_ORDER = _field_after_label("Counter Display Order")
    COUNTER_TITLE_EN = _field_after_label("Counter Title (EN)")
    COUNTER_TITLE_AR = _field_after_label("Counter Title (AR)")
    COUNTER_VALUE = _field_after_label("Counter Value")

    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # Same confirmed-live "no stable class/role for either message" signal
    # as gm_message_admin_page.py / board_members_admin_page.py.
    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    # Same confirmed-live save-then-reload grace as gm_message_admin_page.py
    # (SAVE_COMMIT_GRACE_MS) — reused verbatim rather than re-measured, since
    # both forms are the identical Object Entry editor.
    SAVE_COMMIT_GRACE_MS = 2000

    # Confirmed live (this session, first real pytest run): this Object
    # Entry editor's initial render regularly outlasts the wrapper's bare
    # 10s wait_for default (a loading spinner was still visible past 10s in
    # captured failure evidence) — same class of measured, real render
    # latency already documented for ROW_ID_LINK_RELOAD_TIMEOUT_MS /
    # GM_NAME_RELOAD_TIMEOUT_MS in gm_message_admin_page.py. A longer
    # timeout on this one wait, not a locator change.
    FORM_RENDER_TIMEOUT_MS = 20000

    # ---- Navigation ---------------------------------------------------------
    def _open_admin_home(self) -> None:
        """Enter via the explicit English-locale home URL (mirrors
        GmMessageAdminPage.ADMIN_HOME_EN_URL_PATH's own confirmed-live
        rationale) and log in if the session isn't already authenticated."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(self.CONTENT_DATA_MENU_ITEM) or self.is_visible(self.PRODUCT_MENU_TOGGLE)):
            CmsLoginPage(self.page).open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

        if not self.is_visible(self.CONTENT_DATA_MENU_ITEM):
            self.click(self.PRODUCT_MENU_TOGGLE)
            self.wait_for(self.CONTENT_DATA_MENU_ITEM)

    def open_about_us_section_edit_form(self) -> "HomeAboutSummaryAdminPage":
        """Navigate via Content & Data > About Us Sections, then open the
        singleton record's (ID 52157) edit form via its row ID link."""
        self._open_admin_home()
        self.click(self.CONTENT_DATA_MENU_ITEM)
        self.click(self.ABOUT_US_SECTIONS_MENU_ITEM)
        self.wait_for(self.ABOUT_US_SECTION_ROW_ID_LINK, timeout=self.LIST_RENDER_TIMEOUT_MS)
        self.click(self.ABOUT_US_SECTION_ROW_ID_LINK)
        self.wait_for(self.SECTION_HEADING_EN, timeout=self.FORM_RENDER_TIMEOUT_MS)
        return self

    def open_counter_01_edit_form(self) -> "HomeAboutSummaryAdminPage":
        """Navigate via Content & Data > About Us Counters, then open
        counter row 01's (ID 52165) edit form via its row ID link — the one
        "counter set" this test exercises."""
        self._open_admin_home()
        self.click(self.CONTENT_DATA_MENU_ITEM)
        self.click(self.ABOUT_US_COUNTERS_MENU_ITEM)
        self.wait_for(self.ABOUT_US_COUNTER_01_ROW_ID_LINK, timeout=self.LIST_RENDER_TIMEOUT_MS)
        self.click(self.ABOUT_US_COUNTER_01_ROW_ID_LINK)
        self.wait_for(self.COUNTER_VALUE, timeout=self.FORM_RENDER_TIMEOUT_MS)
        return self

    # ---- Field actions ------------------------------------------------------
    def fill_text_field(self, field_locator: str, value: str) -> "HomeAboutSummaryAdminPage":
        self.type(field_locator, value)
        return self

    def field_value(self, field_locator: str) -> str:
        return self.page.locator(field_locator).input_value()

    def save(self) -> "HomeAboutSummaryAdminPage":
        self.click(self.SAVE_BUTTON)
        self.page.wait_for_timeout(self.SAVE_COMMIT_GRACE_MS)
        return self

    def cancel(self) -> "HomeAboutSummaryAdminPage":
        self.click(self.CANCEL_BUTTON)
        return self

    # ---- State queries --------------------------------------------------------
    def is_save_error_shown(self) -> bool:
        body_text = self.page.locator("body").inner_text()
        return self.SAVE_ERROR_BANNER_TEXT in body_text or self.INLINE_REQUIRED_TEXT in body_text

    def save_error_text(self) -> str:
        body_text = self.page.locator("body").inner_text()
        idx = body_text.find(self.SAVE_ERROR_BANNER_TEXT)
        if idx == -1:
            idx = body_text.find(self.INLINE_REQUIRED_TEXT)
        return body_text[idx: idx + 120] if idx != -1 else ""

    # ---- Real cross-session logout (case Step 2/3's actual mechanism) -----
    LOGOUT_PATH = "/c/portal/logout"

    def logout(self) -> "HomeAboutSummaryAdminPage":
        """Confirmed live this session: GET /c/portal/logout ends the
        session (Control Menu no longer present afterward) — the genuine
        cross-session mechanism the case's "Log out and log back in"
        step requires, not a reload."""
        self.open(control_panel_url(self.LOGOUT_PATH))
        return self

    def login_as(self, username: str, password: str) -> "HomeAboutSummaryAdminPage":
        from cms.pages.control_panel.login_page import CmsLoginPage

        CmsLoginPage(self.page).open_login().login(username, password)
        return self

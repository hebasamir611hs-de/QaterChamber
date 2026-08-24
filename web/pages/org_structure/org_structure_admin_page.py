"""
web/pages/org_structure/org_structure_admin_page.py — OrgStructureAdminPage.

Control_Panel Page Object for PBI 129399 (QC-ABOUT-007 — Organizational
Structure), backing the Departments management screen.

REAL, LIVE-VERIFIED FACTS (this session, 2026-08-23, headless Chromium
against qcdev, authenticated via CmsLoginPage / TEST_USER):

  - Content & Data > "Departments" is the admin surface for this feature —
    a Liferay Object Definition (objectDefinitionId=80610, groupId=37246).
    LIST_URL below is the real, confirmed URL (captured from the rendered
    nav link's href, not guessed).
  - The list view is a FLAT data grid (ID / Active Status / Department
    Description (AR) / Department Description (EN) / Department Name (AR) /
    Department Name (EN) / Display Order / ... more columns off-screen to
    the right, not scrolled into view this session). It is NOT a
    drag-reorder tree widget — cases that assume an in-CMS tree/cascade-
    warning UI could not be confirmed (see test module docstring).
  - Clicking "New" opens an Add form (Save/Cancel, class btn-primary on
    Save) whose fields — confirmed by full-page screenshot after an explicit
    networkidle wait (the fields render async; a fixed short wait is not
    enough, hence WAIT_AFTER_NEW_MS below) — are exactly, in this order:
      Active Status (checkbox, no asterisk -> optional)
      Department Description (AR) (textarea, optional)
      Department Description (EN) (textarea, optional)
      Department Name (AR) * (input, required)
      Department Name (EN) * (input, required)
      Display Order * (input, required)
      Parent Department (input — combobox-style, optional)
      Person Name (AR) * (input, required)
      Person Name (EN) * (input, required)
      Person Photo (file input behind a "Select File" button, optional —
        helper text: "Upload a jpg, png no larger than 2 MB")
      Person Title (AR) * (input, required)
      Person Title (EN) * (input, required)
  - These fields are rendered by a dynamic-data-mapping (DDM) form with NO
    stable id/name/for-label wiring on the visible inputs (the only ids
    present belong to hidden portlet plumbing — _...formDate, _...cmd, a
    hidden reCAPTCHA field, etc.) — get_by_label() and #id selectors both
    resolved to nothing. The one mechanism that DID work is exact visible
    label TEXT (confirmed character-for-character via screenshot), used
    below as a text-anchored "label text -> nearest following input/
    textarea" locator. This is a disclosed deviation from the id/data-testid
    priority order in automation-standards.md's Tooling priority, forced by
    the DDM renderer's lack of any stable id/name/aria hook — re-verify if
    the DDM form definition changes field order.
  - NO Page Title (EN/AR), Hero Banner (EN/AR), or page Status
    (Draft/Published) field exists anywhere on this Departments object's
    list or Add form. That page-level content control described in several
    ADO cases (133298-133315) lives on a DIFFERENT admin surface (most
    likely a Site Builder > Pages page for Organizational Structure, or a
    separate Web Content article) that was NOT located this session —
    PAGE_SETTINGS_URL is therefore an explicit unresolved placeholder, not a
    guess.
  - No cascade-deactivation warning dialog, no circular-parent-reference
    error, no duplicate-name error, and no in-app drag-reorder control were
    observed or could be triggered this session (session flakiness — see
    below — cut the exploration short before those specific interactions
    were attempted). Their locators are explicit unresolved placeholders.
  - Dev-environment quirks (announcement popup, developer-mode connection-
    limit interstitial) are already handled globally by BasePage.open() /
    .click() / .wait_for() via core/web/license_gate.py + core/web/
    overlays.py — this Page Object does NOT re-implement that handling.
  - SESSION FLAKINESS OBSERVED: fresh Playwright contexts reusing a saved
    storageState intermittently re-hit the connection-limit interstitial
    or lost the session outright (redirected to the public "Coming Soon"
    404 template) even seconds apart, for reasons beyond the documented
    "cookie-scoped reset" quirk in standards.md. Treat this admin surface
    as network-flaky in this dev environment; tests should tolerate a retry
    at the infra/CI level, not by adding sleeps here.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

LIST_URL = control_panel_url(
    "/group/qatar-chamber/~/control_panel/manage"
    "?p_p_id=com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_J7R0"
    "&p_p_lifecycle=0&p_p_state=maximized&p_v_l_s_g_id=37246"
    "&_com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_J7R0_objectDefinitionId=80610"
)

_UNVERIFIED = "TODO: run tools/extract_locators.py / MCP against the live page and paste the confirmed selector here"


def _field_after_label(label: str, tag: str = "input") -> str:
    """Text-anchored locator: the {tag} nearest AFTER the exact visible label
    text. See module docstring for why id/name/get_by_label all resolved to
    nothing on this DDM-rendered form."""
    return f'xpath=//*[normalize-space(text())="{label}"]/following::{tag}[1]'


class OrgStructureAdminPage(BasePage):
    # ---- Menu navigation (see open_departments_list() docstring) ----------
    PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
    CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
    DEPARTMENTS_MENU_ITEM = '[role="menuitem"]:text-is("Departments")'

    # ---- List screen ------------------------------------------------------
    NEW_BUTTON = 'button:has-text("New")'
    SEARCH_INPUT = 'input[placeholder="Search"], input[type="search"]'
    LIST_ROW = "table tbody tr"

    # ---- Add/Edit form (confirmed field labels, see docstring) -------------
    ACTIVE_STATUS_CHECKBOX = 'input[type="checkbox"]'
    DEPT_DESCRIPTION_AR = _field_after_label("Department Description (AR)", "textarea")
    DEPT_DESCRIPTION_EN = _field_after_label("Department Description (EN)", "textarea")
    DEPT_NAME_AR = _field_after_label("Department Name (AR)")
    DEPT_NAME_EN = _field_after_label("Department Name (EN)")
    DISPLAY_ORDER = _field_after_label("Display Order")
    PARENT_DEPARTMENT = _field_after_label("Parent Department")
    PERSON_NAME_AR = _field_after_label("Person Name (AR)")
    PERSON_NAME_EN = _field_after_label("Person Name (EN)")
    PERSON_PHOTO_SELECT_FILE_BTN = 'button:has-text("Select File")'
    PERSON_PHOTO_INPUT = 'input[type="file"]'
    PERSON_TITLE_AR = _field_after_label("Person Title (AR)")
    PERSON_TITLE_EN = _field_after_label("Person Title (EN)")

    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # ---- Not located this session — explicit placeholders, never guessed --
    PAGE_SETTINGS_URL = _UNVERIFIED  # Page Title / Hero Banner / Status admin surface
    CASCADE_WARNING_DIALOG = _UNVERIFIED
    CASCADE_CONFIRM_BUTTON = _UNVERIFIED
    CIRCULAR_REFERENCE_ERROR = _UNVERIFIED
    DUPLICATE_NAME_ERROR = _UNVERIFIED
    ACCESS_DENIED_MESSAGE_EN = _UNVERIFIED
    ACCESS_DENIED_MESSAGE_AR = _UNVERIFIED

    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"OrgStructureAdminPage.{name} is an unverified placeholder — locate the "
                f"real admin surface / trigger the real UI state and replace it before "
                f"running this test."
            )

    # ---- Navigation ---------------------------------------------------------
    def open_departments_list(self) -> "OrgStructureAdminPage":
        """Navigate via Content & Data > Departments, NOT the saved LIST_URL.

        Confirmed live 2026-08-24 (QA Manager, manual + automated repro):
        LIST_URL embeds a Liferay portlet INSTANCE id
        (...ObjectDefinitionsPortlet_J7R0...) that is randomly regenerated
        per browser session. A URL captured in one session 404s to a
        "Coming Soon" page in the next — this was the dominant cause of the
        Control_Panel suite's failures (not a login/session-drop issue, and
        not network flakiness). Menu navigation is the only path confirmed
        stable across sessions; LIST_URL is kept only as a documented
        artifact of what NOT to navigate to directly.
        """
        # The cached .auth/state.json storageState is not reliable here —
        # qcdev's session drops fast enough (confirmed live 2026-08-24,
        # roughly every ~30s under sustained traffic) that a state file
        # captured earlier is routinely already dead. Rather than trust it,
        # force a real, fresh login every time this is the entry point into
        # the admin flow. Local import: avoids a circular import with
        # CmsLoginPage (itself a BasePage subclass).
        from web.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url("/home"))
        # CmsLoginPage.login_succeeded() checks for the top Control Menu bar,
        # which is unreliable here — confirmed live 2026-08-24: an already-
        # authenticated admin session showing the LEFT Product Menu sidebar
        # (Design / Site Builder / Content & Data / ...) still read as
        # "not logged in" by that check, causing an unneeded re-login that
        # then hit /c/portal/login WHILE already authenticated and landed on
        # a "Coming Soon" placeholder instead of a real login form. The
        # reachability of the admin menu itself (either already expanded or
        # its closed toggle button) is the reliable signal a public visitor
        # never has either way.
        if not (self.is_visible(self.CONTENT_DATA_MENU_ITEM) or self.is_visible(self.PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url("/home"))

        if not self.is_visible(self.CONTENT_DATA_MENU_ITEM):
            self.click(self.PRODUCT_MENU_TOGGLE)
            self.wait_for(self.CONTENT_DATA_MENU_ITEM)
        self.click(self.CONTENT_DATA_MENU_ITEM)
        self.click(self.DEPARTMENTS_MENU_ITEM)
        self.wait_for(self.NEW_BUTTON)
        return self

    def open_new_department_form(self) -> "OrgStructureAdminPage":
        self.click(self.NEW_BUTTON)
        self.wait_for(self.DEPT_NAME_EN)
        return self

    def open_page_settings(self) -> "OrgStructureAdminPage":
        self._require_verified(self.PAGE_SETTINGS_URL, "PAGE_SETTINGS_URL")
        self.open(self.PAGE_SETTINGS_URL)
        return self

    # ---- Add/Edit form actions ----------------------------------------------
    def fill_department_form(
        self,
        name_en: str = None,
        name_ar: str = None,
        person_name_en: str = None,
        person_name_ar: str = None,
        person_title_en: str = None,
        person_title_ar: str = None,
        description_en: str = None,
        description_ar: str = None,
        display_order: str = None,
        parent_department: str = None,
        active_status: bool = None,
    ) -> "OrgStructureAdminPage":
        if name_en is not None:
            self.type(self.DEPT_NAME_EN, name_en)
        if name_ar is not None:
            self.type(self.DEPT_NAME_AR, name_ar)
        if person_name_en is not None:
            self.type(self.PERSON_NAME_EN, person_name_en)
        if person_name_ar is not None:
            self.type(self.PERSON_NAME_AR, person_name_ar)
        if person_title_en is not None:
            self.type(self.PERSON_TITLE_EN, person_title_en)
        if person_title_ar is not None:
            self.type(self.PERSON_TITLE_AR, person_title_ar)
        if description_en is not None:
            self.type(self.DEPT_DESCRIPTION_EN, description_en)
        if description_ar is not None:
            self.type(self.DEPT_DESCRIPTION_AR, description_ar)
        if display_order is not None:
            self.type(self.DISPLAY_ORDER, display_order)
        if parent_department is not None:
            self.type(self.PARENT_DEPARTMENT, parent_department)
        if active_status is not None:
            self.set_checkbox(self.ACTIVE_STATUS_CHECKBOX, active_status)
        return self

    def upload_person_photo(self, file_path: str) -> "OrgStructureAdminPage":
        self.upload_file(self.PERSON_PHOTO_INPUT, file_path)
        return self

    def save(self) -> "OrgStructureAdminPage":
        self.click(self.SAVE_BUTTON)
        return self

    def cancel(self) -> "OrgStructureAdminPage":
        self.click(self.CANCEL_BUTTON)
        return self

    def confirm_cascade_deactivation(self) -> "OrgStructureAdminPage":
        self._require_verified(self.CASCADE_CONFIRM_BUTTON, "CASCADE_CONFIRM_BUTTON")
        self.click(self.CASCADE_CONFIRM_BUTTON)
        return self

    # ---- State queries --------------------------------------------------------
    def is_save_error_shown(self) -> bool:
        return self.is_visible('.alert-danger, [role="alert"]')

    def save_error_text(self) -> str:
        return self.text('.alert-danger, [role="alert"]')

    def is_cascade_warning_shown(self) -> bool:
        self._require_verified(self.CASCADE_WARNING_DIALOG, "CASCADE_WARNING_DIALOG")
        return self.is_visible(self.CASCADE_WARNING_DIALOG)

    def department_row_visible(self, department_name_en: str) -> bool:
        return self.is_visible(f'{self.LIST_ROW}:has-text("{department_name_en}")')

    def field_value(self, field_locator: str) -> str:
        return self.page.locator(field_locator).input_value()

    def is_access_denied_shown(self, locale: str = "en") -> bool:
        name = "ACCESS_DENIED_MESSAGE_AR" if locale == "ar" else "ACCESS_DENIED_MESSAGE_EN"
        locator = getattr(self, name)
        self._require_verified(locator, name)
        return self.is_visible(locator)

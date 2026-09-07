"""
cms/pages/home_services/home_services_admin_page.py — HomeServicesAdminPage.

Control_Panel Page Object for PBI 129371 (QC-HOME-005 — Our Services
Section), backing the "Service Cards" Object Definition entry list/edit
surface reached via Content & Data > "Service Cards"
(objectDefinitionId=47976, groupId=37246, externalReferenceCode
QCDEMO-129371-SERVICE_CARD). Renders the public Home Page's "Services We
Provide" section (`section.qc-home-our-services`) — see
home_services_page.py (web/) for the public-frontend counterpart. A sibling
"Filter Tabs" Object Definition (objectDefinitionId not yet probed) backs
the section's tab strip; this page only exercises the tab a Service Card
gets assigned to (the "Assigned Tab" field on the card itself), not Filter
Tab authoring — no case in this batch requires creating a Filter Tab.

CONFIRMED LIVE THIS SESSION (2026-09-02, headed Chromium via Playwright MCP
against qcdev, existing authenticated admin session):

LIST SCREEN — confirmed live, real rows present (e.g. "New Membership"
Display Order 100, "Membership Renewal" Display Order 200, both Status=
Approved). Column order: Item Selection, ID, Active Status, Assigned Tab,
Display Order, Icon, Image Thumbnail, Redirect URL, Short Description,
Title, Status, Author, Item Actions.

ADD/EDIT FORM — confirmed live field set via `[data-field-reference]`
containers (all 8 unique refs enumerated live, no guessing):
  activeStatus (checkbox), assignedTab (single-select combobox: Membership /
  Legal / E-Services / Information — required), displayOrder (text/number,
  required), icon (file, "Select File", required), imageThumbnail (file,
  "Select File", required), redirectUrl (text, required), shortDescription
  (text, optional), title (text, required). Save/Cancel only — no separate
  Publish/Draft/Submit-for-Review button on this form (see WORKFLOW FINDING
  below).

WORKFLOW FINDING — CONFIRMED live 2026-09-02 (same pattern already
documented for Promotional Banners, PBI 129368 — see
home_promo_banners_admin_page.py): the Add/Edit form's own footer renders
ONLY Save/Cancel, and every existing list row's Status column reads
"Approved" uniformly — the default Liferay Objects behavior for an object
definition with no workflow attached. This directly blocks ADO Test Case
135346 ("Verify that saving the section as Draft in CMS keeps it hidden
from the live Home Page") as literally worded — there is no reachable Draft
precondition state and no Save-as-Draft control to invoke. See this page's
module-level tests file for the disclosed skip.

TAB NAMING NOTE: ADO Test Case 135351 names the target tab "Information
Services". The Assigned Tab combobox's real, confirmed-live option text is
"Information" (matching the public Home Page's own tab label, also
confirmed live: `section.qc-home-our-services .qc-os-tabs [role="tab"]`
reads "All Services" / "Membership" / "Legal" / "E-Services" / "Information"
— no tab literally named "Information Services" exists). Treated as the
case's own shorthand for the live "Information" tab — disclosed here, not
silently invented as a second tab.

Upload flow (Select File -> Documents-and-Media picker modal -> its own
`iframe[title="Select File"]` -> that iframe's own `input[type=file]` ->
picker's own "Add" button) mirrors the CONFIRMED-LIVE working flow already
documented and reused verbatim across this project (e.g.
home_promo_banners_admin_page.py._upload_image()).

TEST-DATA POLICY (cms-profile.md): DISPOSABLE — every fixture created here
carries the project's `QCTEST-` prefix in its Title and is deleted via the
row's own Actions kebab -> Delete -> confirm in a test's `finally` block.
Never mutates the real editorial rows (e.g. "New Membership", "Membership
Renewal", and the other pre-existing service cards).
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
SERVICE_CARDS_MENU_ITEM = '[role="menuitem"]:text-is("Service Cards")'
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'


class HomeServicesAdminPage(BasePage):
    ADMIN_HOME_EN_URL_PATH = "/en/home"

    # ---- List screen ------------------------------------------------------
    ADD_BUTTON = 'button:has-text("New")'
    LIST_ROW = "table tbody tr"
    # Mirrors HomePromoBannersAdminPage.ROW_ID_LINK's own confirmed-live
    # filter: `td a` alone also resolves to multiple links per row here
    # (icon/image download links plus the entry edit link) — filter on the
    # edit-command href.
    ROW_ID_LINK = 'td a[href*="mvcRenderCommandName=%2Fobject_entries%2Fedit_object_entry"]'

    # ---- Edit/Add form ------------------------------------------------------
    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    ACTIVE_STATUS_CONTAINER = '[data-field-reference="activeStatus"]'
    ACTIVE_STATUS_CHECKBOX = f'{ACTIVE_STATUS_CONTAINER} input[type="checkbox"]'
    ASSIGNED_TAB_CONTAINER = '[data-field-reference="assignedTab"]'
    ASSIGNED_TAB_TOGGLE = f'{ASSIGNED_TAB_CONTAINER} button[aria-haspopup="listbox"]'
    DISPLAY_ORDER_CONTAINER = '[data-field-reference="displayOrder"]'
    # Same visible-input-only filter as HomePromoBannersAdminPage.DISPLAY_ORDER_INPUT
    # — the container also renders a hidden `..._edited` tracking input under
    # the same data-field-reference (strict-mode violation on .fill() otherwise).
    DISPLAY_ORDER_INPUT = f'{DISPLAY_ORDER_CONTAINER} input[type="text"]:visible'
    ICON_CONTAINER = '[data-field-reference="icon"]'
    IMAGE_THUMBNAIL_CONTAINER = '[data-field-reference="imageThumbnail"]'
    REDIRECT_URL_CONTAINER = '[data-field-reference="redirectUrl"]'
    REDIRECT_URL_INPUT = f'{REDIRECT_URL_CONTAINER} input[type="text"]'
    SHORT_DESCRIPTION_CONTAINER = '[data-field-reference="shortDescription"]'
    # Confirmed live 2026-09-02 (heal, ADO-135351 rerun): renders as a
    # <textarea>, not `input[type="text"]` like the other single-line text
    # fields on this form (title/redirectUrl) — was silently timing out.
    SHORT_DESCRIPTION_INPUT = f'{SHORT_DESCRIPTION_CONTAINER} textarea'
    TITLE_CONTAINER = '[data-field-reference="title"]'
    TITLE_INPUT = f'{TITLE_CONTAINER} input[type="text"]'

    SELECT_FILE_BUTTON = 'button:has-text("Select File")'
    UPLOAD_MODAL_IFRAME = 'iframe[title="Select File"]'
    UPLOAD_MODAL_ADD_BUTTON_TEXT = "Add"

    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    # Disclosed, unmeasured-for-this-object-specifically save-commit grace —
    # same convention as HomePromoBannersAdminPage.SAVE_COMMIT_GRACE_MS.
    SAVE_COMMIT_GRACE_MS = 2000

    # ---- Navigation -------------------------------------------------------
    def open_service_cards_list(self) -> "HomeServicesAdminPage":
        """Product Menu > Content & Data > Service Cards. Never a cached
        deep-link URL — the rendered list URL embeds a per-session portlet
        instance id (same pattern as every sibling admin Page Object)."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))

        if not self.is_visible(CONTENT_DATA_MENU_ITEM):
            self.click(PRODUCT_MENU_TOGGLE)
            try:
                self.wait_for(CONTENT_DATA_MENU_ITEM, timeout=20000)
            except Exception:
                # Same confirmed-live retry as HomePromoBannersAdminPage's
                # open_promo_banners_list() 2026-09-03 — the Product Menu
                # submenu can intermittently fail to render on the first
                # toggle click; one retry recovers.
                self.click(PRODUCT_MENU_TOGGLE)
                self.wait_for(CONTENT_DATA_MENU_ITEM, timeout=20000)
        self.click(CONTENT_DATA_MENU_ITEM)
        self.wait_for(SERVICE_CARDS_MENU_ITEM)
        self.click(SERVICE_CARDS_MENU_ITEM)
        self.wait_for(self.LIST_ROW, first=True, timeout=20000)
        return self

    def open_new_service_card_form(self) -> "HomeServicesAdminPage":
        self.open_service_cards_list()
        self.click(self.ADD_BUTTON)
        self.wait_for(self.SAVE_BUTTON, timeout=20000)
        self.wait_for(self.TITLE_INPUT, timeout=20000)
        return self

    def open_service_card_edit_form_by_title(self, title: str) -> "HomeServicesAdminPage":
        self.open_service_cards_list()
        self.click(f'{self.LIST_ROW}:has-text("{title}") >> {self.ROW_ID_LINK}')
        self.wait_for(self.SAVE_BUTTON, timeout=20000)
        self.wait_for(self.TITLE_INPUT, timeout=20000)
        return self

    # ---- List state queries -------------------------------------------------
    def row_visible(self, title: str) -> bool:
        return self.is_visible(f'{self.LIST_ROW}:has-text("{title}")')

    def wait_for_row_visible(self, title: str, timeout_ms: int = 20000, poll_ms: int = 500) -> bool:
        """Poll (re-navigating the list each cycle) until the row appears —
        mirrors HomePromoBannersAdminPage.wait_for_row_visible()."""
        import time

        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_service_cards_list()
            if self.row_visible(title):
                return True
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(poll_ms)

    def delete_row_by_title(self, title: str) -> bool:
        """Delete via the row's Actions kebab -> Delete -> confirm. Returns
        False (no-op) if no matching row exists. Mirrors
        HomePromoBannersAdminPage.delete_row_by_alt_text()'s confirmed-live
        kebab/get_by_role flow."""
        row = self.page.locator(f'{self.LIST_ROW}:has-text("{title}")')
        if row.count() == 0:
            return False
        kebab = row.get_by_role("button", name="Actions")
        kebab.first.click()
        delete_item = self.page.locator('[role="menuitem"]:visible:has-text("Delete")')
        delete_item.first.wait_for(state="visible", timeout=5000)
        delete_item.first.click()
        confirm = self.page.get_by_role("button", name="Delete")
        confirm.wait_for(state="visible", timeout=10000)
        confirm.click()
        self.page.wait_for_load_state("networkidle")
        return True

    # ---- Field actions ------------------------------------------------------
    def set_title(self, value: str) -> "HomeServicesAdminPage":
        self.page.locator(self.TITLE_INPUT).fill(value)
        return self

    def set_short_description(self, value: str) -> "HomeServicesAdminPage":
        self.page.locator(self.SHORT_DESCRIPTION_INPUT).fill(value)
        return self

    def set_redirect_url(self, value: str) -> "HomeServicesAdminPage":
        self.page.locator(self.REDIRECT_URL_INPUT).fill(value)
        return self

    def set_display_order(self, value: str) -> "HomeServicesAdminPage":
        self.page.locator(self.DISPLAY_ORDER_INPUT).fill(value)
        return self

    def set_assigned_tab(self, tab_label: str) -> "HomeServicesAdminPage":
        """tab_label must match a real, confirmed-live option text
        (Membership / Legal / E-Services / Information)."""
        self.page.locator(self.ASSIGNED_TAB_TOGGLE).click()
        option = self.page.get_by_role("option", name=tab_label, exact=True)
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return self

    def is_active(self) -> bool:
        return self.page.locator(self.ACTIVE_STATUS_CHECKBOX).is_checked()

    def set_active(self, active: bool) -> "HomeServicesAdminPage":
        self.set_checkbox(self.ACTIVE_STATUS_CHECKBOX, active)
        return self

    def _upload_image(self, container_selector: str, file_path: str) -> None:
        """Confirmed-live working flow, reused verbatim from
        HomePromoBannersAdminPage._upload_image() — see module docstring."""
        self.page.locator(f"{container_selector} {self.SELECT_FILE_BUTTON}").click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)
        frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click()
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
        except Exception:
            self.page.wait_for_timeout(1000)

    def upload_icon(self, file_path: str) -> "HomeServicesAdminPage":
        self._upload_image(self.ICON_CONTAINER, file_path)
        return self

    def upload_image_thumbnail(self, file_path: str) -> "HomeServicesAdminPage":
        self._upload_image(self.IMAGE_THUMBNAIL_CONTAINER, file_path)
        return self

    def _uploaded_filename(self, container_selector: str) -> str:
        container_text = self.page.locator(container_selector).inner_text()
        for line in container_text.splitlines():
            line = line.strip()
            if line and line != "Select File" and "Upload a " not in line and not line.endswith(")"):
                return line
        return ""

    def uploaded_icon_filename(self) -> str:
        return self._uploaded_filename(self.ICON_CONTAINER)

    def uploaded_image_thumbnail_filename(self) -> str:
        return self._uploaded_filename(self.IMAGE_THUMBNAIL_CONTAINER)

    def save(self) -> "HomeServicesAdminPage":
        self.click(self.SAVE_BUTTON)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(self.SAVE_COMMIT_GRACE_MS)
        return self

    def cancel(self) -> "HomeServicesAdminPage":
        self.click(self.CANCEL_BUTTON)
        return self

    def is_save_error_shown(self) -> bool:
        body_text = self.page.locator("body").inner_text()
        return self.SAVE_ERROR_BANNER_TEXT in body_text or self.INLINE_REQUIRED_TEXT in body_text

    def save_error_text(self) -> str:
        body_text = self.page.locator("body").inner_text()
        idx = body_text.find(self.SAVE_ERROR_BANNER_TEXT)
        if idx == -1:
            idx = body_text.find(self.INLINE_REQUIRED_TEXT)
        return body_text[idx: idx + 120] if idx != -1 else ""

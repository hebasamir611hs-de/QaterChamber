"""
cms/pages/home_promo_banners/home_promo_banners_admin_page.py —
HomePromoBannersAdminPage.

Control_Panel Page Object for PBI 129368 (QC-HOME-002 — Promotional Banners
/ Ad Slots), backing the Object Definition entry list/edit surface reached
via Content & Data > "Promotional Banners" (objectDefinitionId=47506,
groupId=37246). Renders the public Home Page's promotional banners carousel
— see home_promo_banners_page.py (web/) for the public-frontend counterpart.

CONFIRMED LIVE THIS SESSION (2026-09-02, headless Chromium via
tools/save_auth.py-captured storageState re-issued this session, against
qcdev) — navigation, list, and add/edit form all independently probed with
throwaway scripts mirroring the pattern already used project-wide (e.g.
home_community_partners_admin_page.py, home_featured_event_admin_page.py):

LIST SCREEN — confirmed live 4 real rows at probe time (47729, 47737,
47745, plus a pre-existing leftover test row 118254 not created by this
session and never touched by it — see teardown note below). Column order:
Item Selection, ID, Active Status, Banner Alt Text (AR), Banner Alt Text
(EN), Banner Image (AR), Banner Image (EN), Banner Image Mobile (AR),
Banner Image Mobile (EN), Display Order, End Date, Open in New Tab,
Redirect URL, Start Date, Status, Author, Item Actions.

ADD/EDIT FORM — confirmed live field set via `[data-field-reference]`
containers (all 12 unique refs enumerated live, no guessing):
  activeStatus (checkbox), bannerAltTextAR* (text), bannerAltTextEN* (text),
  bannerImageAR* (file, "Select File"), bannerImageEN* (file, "Select
  File"), bannerImageMobileAR (file, optional), bannerImageMobileEN (file,
  optional), displayOrder* (text/number), endDate (date picker),
  openInNewTab (checkbox), redirectUrl (text), startDate (date picker).
  Save/Cancel only — no separate Publish/Draft/Submit-for-Review button on
  this form (see WORKFLOW FINDING below).

WORKFLOW FINDING — CONFIRMED PRODUCT/CASE-MISMATCH, not an automation gap:
Configuration > Workflow (Site Administration Workflow screen) lists
"Promotional Banner" as Asset Type with Workflow Assigned = **"No
Workflow"** (confirmed live this session via the Workflow admin screen's
own search, screenshot on file). Every existing list row's Status column
reads "APPROVED" uniformly — the default Liferay Objects behavior for an
object definition with no workflow attached (every entry auto-approves on
Save; there is no Draft/Pending Review/Published/Unpublished state machine
on this object at all). The row-level "Item Actions" kebab confirmed live
exposes only View / Delete / Permissions — no Publish/Unpublish/Submit for
Review action either. This directly blocks ADO Test Cases 135122 (save as
draft), 135123 (submit for review), 135124 (publish from Pending Review),
and 135125 (unpublish) as literally worded — there is no reachable Draft or
Pending Review precondition state to open, and no Publish/Unpublish action
to invoke. See this page's module-level tests file for the disclosed skips
(NOT scripted as passing, NOT force-fit onto the unrelated Active Status
toggle — see that module's docstring for why the home_featured_event
precedent does not transfer here).

Upload flow (Select File -> Documents-and-Media picker modal -> its own
`iframe[title="Select File"]` -> that iframe's own `input[type=file]` ->
picker's own "Add" button) mirrors the CONFIRMED-LIVE working flow already
documented and used by
`home_community_partners_admin_page.py.upload_partner_logo()` — reused
verbatim here since Liferay's Documents-and-Media picker is the same shared
widget across every Object Definition's file field on this project, not a
per-object behavior needing independent re-discovery.

TEST-DATA POLICY (cms-profile.md): DISPOSABLE — every fixture created here
carries the project's `QCTEST-` prefix in its Alt Text (EN) and is deleted
via the row's own Actions kebab -> Delete -> confirm in a test's `finally`
block. Never mutates rows 47729/47737/47745 (real editorial content) or the
pre-existing leftover 118254 (not this suite's row to own).
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
PROMO_BANNERS_MENU_ITEM = '[role="menuitem"]:text-is("Promotional Banners")'
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'


class HomePromoBannersAdminPage(BasePage):
    ADMIN_HOME_EN_URL_PATH = "/en/home"

    # ---- List screen ------------------------------------------------------
    ADD_BUTTON = 'button:has-text("New")'
    LIST_ROW = "table tbody tr"
    # `td a` alone resolves to 5 elements per row (confirmed live 2026-09-02):
    # the actual ID/edit link plus 4 attachment-download links (image AR/EN +
    # mobile AR/EN) and empty anchors on some rows. The edit link is the only
    # one whose href carries `mvcRenderCommandName=%2Fobject_entries%2Fedit_object_entry`
    # — every attachment link instead carries `download=true`. Filter on that.
    ROW_ID_LINK = 'td a[href*="mvcRenderCommandName=%2Fobject_entries%2Fedit_object_entry"]'

    # ---- Edit/Add form ------------------------------------------------------
    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    ACTIVE_STATUS_CONTAINER = '[data-field-reference="activeStatus"]'
    ACTIVE_STATUS_CHECKBOX = f'{ACTIVE_STATUS_CONTAINER} input[type="checkbox"]'
    ALT_TEXT_AR_CONTAINER = '[data-field-reference="bannerAltTextAR"]'
    ALT_TEXT_AR_INPUT = f'{ALT_TEXT_AR_CONTAINER} input[type="text"]'
    ALT_TEXT_EN_CONTAINER = '[data-field-reference="bannerAltTextEN"]'
    ALT_TEXT_EN_INPUT = f'{ALT_TEXT_EN_CONTAINER} input[type="text"]'
    IMAGE_AR_CONTAINER = '[data-field-reference="bannerImageAR"]'
    IMAGE_EN_CONTAINER = '[data-field-reference="bannerImageEN"]'
    IMAGE_MOBILE_AR_CONTAINER = '[data-field-reference="bannerImageMobileAR"]'
    IMAGE_MOBILE_EN_CONTAINER = '[data-field-reference="bannerImageMobileEN"]'
    DISPLAY_ORDER_CONTAINER = '[data-field-reference="displayOrder"]'
    # `[data-field-reference="displayOrder"] input` alone resolves to 2
    # elements — the visible textbox and a hidden `..._edited` tracking
    # input Liferay renders under the same container (confirmed live:
    # strict-mode violation on .fill()). Scope to the visible text input
    # only, matching the type-filtered pattern already used by every other
    # text field on this form (ALT_TEXT_*_INPUT, REDIRECT_URL_INPUT).
    DISPLAY_ORDER_INPUT = f'{DISPLAY_ORDER_CONTAINER} input[type="text"]:visible'
    REDIRECT_URL_CONTAINER = '[data-field-reference="redirectUrl"]'
    REDIRECT_URL_INPUT = f'{REDIRECT_URL_CONTAINER} input[type="text"]'
    # Confirmed live 2026-09-02 (probe script, headless): each date-picker
    # container renders exactly ONE `input[type="text"]` (plus 3 hidden
    # tracking inputs sharing the container) — same single-visible-text-input
    # shape as DISPLAY_ORDER_INPUT, so no :visible qualifier is needed here;
    # the type filter alone is already unique. Accepts MM/DD/YYYY typed
    # directly (confirmed live: fill("12/25/2026") -> input_value()
    # echoes back "12/25/2026", no picker-click required).
    START_DATE_CONTAINER = '[data-field-reference="startDate"]'
    START_DATE_INPUT = f'{START_DATE_CONTAINER} input[type="text"]'
    END_DATE_CONTAINER = '[data-field-reference="endDate"]'
    END_DATE_INPUT = f'{END_DATE_CONTAINER} input[type="text"]'
    DATE_INPUT_FORMAT = "%m/%d/%Y"

    SELECT_FILE_BUTTON = 'button:has-text("Select File")'
    # Same confirmed-live Documents-and-Media picker widget as
    # home_community_partners_admin_page.py.upload_partner_logo() — see
    # module docstring.
    UPLOAD_MODAL_IFRAME = 'iframe[title="Select File"]'
    UPLOAD_MODAL_ADD_BUTTON_TEXT = "Add"

    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    # Disclosed, unmeasured-for-this-object-specifically save-commit grace —
    # same convention as CommunityPartnersAdminPage.SAVE_COMMIT_GRACE_MS /
    # GmMessageAdminPage's own: a real `networkidle` wait first, this fixed
    # margin only covers the write-vs-read-cache gap between the entry POST
    # and the list's own separate read path.
    SAVE_COMMIT_GRACE_MS = 2000

    # ---- Navigation -------------------------------------------------------
    def open_promo_banners_list(self) -> "HomePromoBannersAdminPage":
        """Product Menu > Content & Data > Promotional Banners. Never a
        cached deep-link URL — the rendered list URL embeds a per-session
        portlet instance id that regenerates every session (same pattern as
        every sibling admin Page Object on this project)."""
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
                # Confirmed live 2026-09-03: the Product Menu submenu can
                # intermittently fail to render on the first toggle click
                # (observed even well past the default 10s budget) — one
                # retry (re-click the toggle, wait again) recovers rather
                # than surfacing this as a hard failure on every caller.
                self.click(PRODUCT_MENU_TOGGLE)
                self.wait_for(CONTENT_DATA_MENU_ITEM, timeout=20000)
        self.click(CONTENT_DATA_MENU_ITEM)
        self.wait_for(PROMO_BANNERS_MENU_ITEM)
        self.click(PROMO_BANNERS_MENU_ITEM)
        self.wait_for(self.LIST_ROW, first=True, timeout=20000)
        return self

    def open_new_banner_form(self) -> "HomePromoBannersAdminPage":
        self.open_promo_banners_list()
        self.click(self.ADD_BUTTON)
        self.wait_for(self.SAVE_BUTTON, timeout=20000)
        self.wait_for(self.ALT_TEXT_EN_INPUT, timeout=20000)
        return self

    def open_banner_edit_form_by_alt_text(self, alt_text_en: str) -> "HomePromoBannersAdminPage":
        self.open_promo_banners_list()
        self.click(f'{self.LIST_ROW}:has-text("{alt_text_en}") >> {self.ROW_ID_LINK}')
        self.wait_for(self.SAVE_BUTTON, timeout=20000)
        self.wait_for(self.ALT_TEXT_EN_INPUT, timeout=20000)
        return self

    # ---- List state queries -------------------------------------------------
    def row_visible(self, alt_text_en: str) -> bool:
        return self.is_visible(f'{self.LIST_ROW}:has-text("{alt_text_en}")')

    def wait_for_row_visible(self, alt_text_en: str, timeout_ms: int = 20000, poll_ms: int = 500) -> bool:
        """Poll (re-navigating the list each cycle) until the row appears —
        guards the same write-vs-read-cache lag class SAVE_COMMIT_GRACE_MS
        documents. Mirrors CommunityPartnersAdminPage.wait_for_row_visible()."""
        import time

        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_promo_banners_list()
            if self.row_visible(alt_text_en):
                return True
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(poll_ms)

    def delete_row_by_alt_text(self, alt_text_en: str, max_matches: int = 10) -> bool:
        """Delete via the row's Actions kebab -> Delete -> confirm. Returns
        False (no-op) if no matching row exists, so teardown code can call
        this unconditionally. Mirrors
        CommunityPartnersAdminPage.delete_row_by_name()'s confirmed-live
        kebab/get_by_role flow.

        Always re-navigates to a fresh list first (own
        open_promo_banners_list() call) rather than trusting the caller's
        current DOM. Root-caused live 2026-09-02 (tc_135191 CI failure):
        back-to-back calls in the same test's `finally` block with no
        re-navigation between them let the second call's unscoped
        `get_by_role("button", name="Delete")` resolve the FIRST call's own
        confirm button — already `disabled` post-click and mid-detach as
        that first delete's own page navigation was still landing — causing
        `Locator.click: Timeout 30000ms exceeded`. Re-navigating here
        eliminates the stale-DOM window outright (confirmed live: a fresh
        single-delete probe against an already-elapsed Start/End date-range
        row completed with the confirm button `disabled=False` throughout,
        ruling out the row's own data as a factor).

        LOOPS one row at a time rather than assuming the alt-text is unique.
        Root-caused live 2026-09-02 (tc_135191 follow-up): alt text is not a
        DB-unique key on this object, and earlier failed runs (before the
        re-navigation fix above existed) left duplicate QCTEST- rows behind
        undeleted, so `row.wait_for(state="detached")` on the plural locator
        hit a strict-mode violation. Deleting `.first` and re-querying a
        fresh `open_promo_banners_list()` each iteration is robust to any
        number of leftover matches, self-heals accumulated test-data debt
        instead of just failing on it again, and needs no change to how
        `_create_banner`/callers pass in alt text."""
        deleted_any = False
        for _ in range(max_matches):
            self.open_promo_banners_list()
            row = self.page.locator(f'{self.LIST_ROW}:has-text("{alt_text_en}")')
            count = row.count()
            if count == 0:
                return deleted_any
            target = row.first
            kebab = target.get_by_role("button", name="Actions")
            kebab.first.click()
            delete_item = self.page.locator('[role="menuitem"]:visible:has-text("Delete")')
            delete_item.first.wait_for(state="visible", timeout=5000)
            delete_item.first.click()
            # Scoped to the visible confirm dialog, not a bare page-wide
            # get_by_role("button", name="Delete") — confirmed live a second,
            # normally-hidden `[role="dialog"]` container (class "qc-panel")
            # exists on this list screen even with no dialog open, so an
            # unscoped locator risks matching the wrong/stale "Delete" button.
            confirm = self.page.locator('[role="dialog"]:visible').get_by_role("button", name="Delete")
            confirm.wait_for(state="visible", timeout=10000)
            confirm.click(timeout=15000)
            target.wait_for(state="detached", timeout=15000)
            deleted_any = True
        return deleted_any

    # ---- Field actions ------------------------------------------------------
    def set_alt_text_en(self, value: str) -> "HomePromoBannersAdminPage":
        self.page.locator(self.ALT_TEXT_EN_INPUT).fill(value)
        return self

    def set_alt_text_ar(self, value: str) -> "HomePromoBannersAdminPage":
        self.page.locator(self.ALT_TEXT_AR_INPUT).fill(value)
        return self

    def set_display_order(self, value: str) -> "HomePromoBannersAdminPage":
        self.page.locator(self.DISPLAY_ORDER_INPUT).fill(value)
        return self

    def display_order_value(self) -> str:
        return self.page.locator(self.DISPLAY_ORDER_INPUT).input_value()

    def set_redirect_url(self, value: str) -> "HomePromoBannersAdminPage":
        self.page.locator(self.REDIRECT_URL_INPUT).fill(value)
        return self

    def set_start_date(self, value: str) -> "HomePromoBannersAdminPage":
        """`value` in DATE_INPUT_FORMAT (MM/DD/YYYY) — confirmed live typed
        input is accepted without needing the calendar picker."""
        locator = self.page.locator(self.START_DATE_INPUT)
        locator.fill(value)
        locator.blur()
        return self

    def set_end_date(self, value: str) -> "HomePromoBannersAdminPage":
        locator = self.page.locator(self.END_DATE_INPUT)
        locator.fill(value)
        locator.blur()
        return self

    def row_status_text(self, alt_text_en: str) -> str:
        """Raw inner_text of the matching list row — used to assert the
        Status column (this object's Draft/Pending/APPROVED workflow-state
        surrogate — see module WORKFLOW FINDING) is unchanged by an
        unrelated field edit. Empty string if no matching row."""
        row = self.page.locator(f'{self.LIST_ROW}:has-text("{alt_text_en}")')
        return row.inner_text() if row.count() else ""

    def is_active(self) -> bool:
        return self.page.locator(self.ACTIVE_STATUS_CHECKBOX).is_checked()

    def set_active(self, active: bool) -> "HomePromoBannersAdminPage":
        self.set_checkbox(self.ACTIVE_STATUS_CHECKBOX, active)
        return self

    def _upload_image(self, container_selector: str, file_path: str) -> None:
        """Confirmed-live working flow, reused verbatim from
        CommunityPartnersAdminPage.upload_partner_logo() — see module
        docstring."""
        self.page.locator(f"{container_selector} {self.SELECT_FILE_BUTTON}").click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)
        frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click()
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
        except Exception:
            self.page.wait_for_timeout(1000)

    def upload_banner_image_ar(self, file_path: str) -> "HomePromoBannersAdminPage":
        self._upload_image(self.IMAGE_AR_CONTAINER, file_path)
        return self

    def upload_banner_image_en(self, file_path: str) -> "HomePromoBannersAdminPage":
        self._upload_image(self.IMAGE_EN_CONTAINER, file_path)
        return self

    def _uploaded_filename(self, container_selector: str) -> str:
        container_text = self.page.locator(container_selector).inner_text()
        for line in container_text.splitlines():
            line = line.strip()
            if line and line != "Select File" and "Upload a " not in line and not line.endswith(")"):
                return line
        return ""

    def uploaded_image_en_filename(self) -> str:
        return self._uploaded_filename(self.IMAGE_EN_CONTAINER)

    def uploaded_image_ar_filename(self) -> str:
        return self._uploaded_filename(self.IMAGE_AR_CONTAINER)

    def save(self) -> "HomePromoBannersAdminPage":
        self.click(self.SAVE_BUTTON)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(self.SAVE_COMMIT_GRACE_MS)
        return self

    def cancel(self) -> "HomePromoBannersAdminPage":
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

"""
cms/pages/home_latest_news/home_latest_news_admin_page.py —
HomeLatestNewsAdminPage.

Control_Panel Page Object for PBI 129372 (Home Page "Stay Connected &
Informed" / Latest News section), backing the Object Definition entry
list/create form for "News Articles" reached via Content & Data >
"News Articles" (objectDefinitionId=48649, groupId=37246). Renders the
public Home Page's Latest News cards — see
web/pages/home_latest_news/home_latest_news_page.py (web/) for the public-
frontend counterpart.

CONFIRMED LIVE THIS SESSION (2026-09-02, headless Chromium via a fresh
login re-issuing .auth/cp_admin_state.json this session, against qcdev) —
navigation, list, and Create form all independently probed with throwaway
scripts mirroring the pattern already used project-wide (e.g.
home_promo_banners_admin_page.py):

NAVIGATION — Product Menu > Content & Data > "News Articles" resolves live
to the Object Entries portlet deep link with objectDefinitionId=48649,
p_v_l_s_g_id=37246 (both confirmed by reading the menu item's own href
rather than guessed).

LIST SCREEN — confirmed live 3 real rows at probe time (48759, 48789,
48819) — real editorial content, never mutated by this suite.

CREATE FORM — confirmed live field set via `[data-field-reference]`
containers (all 5 unique refs enumerated live, no guessing):
  activeStatus (checkbox, labelled "Active/Published Status" on the
  rendered form), publicationDate* (text input with a date-picker widget,
  format `__/__/____` i.e. MM/DD/YYYY), thumbnailImage* (file, "Select
  File"), title* (text, TRANSLATABLE — an `en-us` locale-switcher chip sits
  beside the input, unlike bannerAltTextAR/EN's separate-field-per-locale
  pattern on Promotional Banners; "Title EN" in the ADO case maps to the
  default en-US value of this one field), viewCount (text/number,
  optional). Save/Cancel only — no separate Save-as-Draft/Publish/Submit-
  for-Review button on this form (see WORKFLOW FINDING below).

WORKFLOW FINDING — CONFIRMED PRODUCT/CASE-MISMATCH, not an automation gap
(same class of finding already on file for Promotional Banners' TC 135122
in home_promo_banners_admin_page.py, and reached the same way — this is
NOT a re-guess, it's the same live check repeated for this object):
Configuration > Workflow (Site Administration Workflow screen) lists
"News Article" as Asset Type with Workflow Assigned = **"No Workflow"**
(confirmed live this session via the Workflow admin screen's own search).
Every existing list row on this object auto-approves on Save — there is no
Draft/Pending Review/Published/Unpublished state machine on this object at
all. The Create form's own button set was dumped live and is exactly
Save/Cancel — no "Save as Draft" control exists to click. The row-level
"Item Actions" kebab (confirmed live on the list, matching the pattern
already documented for Promotional Banners) exposes only View / Delete /
Permissions — no Publish/Unpublish/Submit-for-Review action either.

IMPORTANT — do NOT read "Active/Published Status" as a substitute Draft
toggle: its underlying field reference is `activeStatus` (a visibility
flag Liferay Objects renders on every object regardless of workflow), not
a second, independent publish-workflow field. ADO Test Case 135279 asserts
`status = Draft` — a workflow status this no-workflow object structurally
cannot hold, permanently APPROVED for every entry. Force-fitting
`activeStatus = False` onto "Draft" would be exactly the false-green class
cms-testing.md catalogues (asserting a proxy value under a different label
than the one the case names). This is reported back as a case-vs-product
mismatch for the QA Manager to resolve — not resolved unilaterally here.
See this page's module-level tests file for the disclosed skip.

TEST-DATA POLICY (cms-profile.md): DISPOSABLE — every fixture created here
(should this ever become runnable) would carry the project's `QCTEST-`
prefix in its Title and be deleted via the row's own Actions kebab ->
Delete -> confirm. Never mutates rows 48759/48789/48819 (real editorial
content).
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
NEWS_ARTICLES_MENU_ITEM = '[role="menuitem"]:has-text("News Articles")'
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'


class HomeLatestNewsAdminPage(BasePage):
    ADMIN_HOME_EN_URL_PATH = "/en/home"

    # ---- List screen ------------------------------------------------------
    ADD_BUTTON = 'button:has-text("New")'
    LIST_ROW = "table tbody tr"
    ROW_ID_LINK = 'td a[href*="mvcRenderCommandName=%2Fobject_entries%2Fedit_object_entry"]'

    # ---- Create/Edit form ---------------------------------------------------
    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # Disclosed, confirmed-live-absent: this Object Definition's form
    # renders ONLY Save/Cancel (no Save-as-Draft) — see module docstring's
    # WORKFLOW FINDING. Kept as a named constant (not inlined) so a future
    # re-probe after a workflow gets attached only needs to update this one
    # line and drop the module-level skip.
    SAVE_AS_DRAFT_BUTTON = 'button:has-text("Save as Draft")'  # TODO(locator): not rendered on qcdev today

    ACTIVE_STATUS_CONTAINER = '[data-field-reference="activeStatus"]'
    ACTIVE_STATUS_CHECKBOX = f'{ACTIVE_STATUS_CONTAINER} input[type="checkbox"]'
    PUBLICATION_DATE_CONTAINER = '[data-field-reference="publicationDate"]'
    PUBLICATION_DATE_INPUT = f'{PUBLICATION_DATE_CONTAINER} input[type="text"]'
    THUMBNAIL_IMAGE_CONTAINER = '[data-field-reference="thumbnailImage"]'
    TITLE_CONTAINER = '[data-field-reference="title"]'
    TITLE_INPUT = f'{TITLE_CONTAINER} input[type="text"]'
    VIEW_COUNT_CONTAINER = '[data-field-reference="viewCount"]'
    VIEW_COUNT_INPUT = f'{VIEW_COUNT_CONTAINER} input[type="text"]'

    SELECT_FILE_BUTTON = 'button:has-text("Select File")'
    # Same confirmed-live Documents-and-Media picker widget reused verbatim
    # from home_promo_banners_admin_page.py._upload_image() — see that
    # module's docstring for the original discovery.
    UPLOAD_MODAL_IFRAME = 'iframe[title="Select File"]'
    UPLOAD_MODAL_ADD_BUTTON_TEXT = "Add"

    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    # Disclosed, unmeasured-for-this-object-specifically save-commit grace —
    # same convention as HomePromoBannersAdminPage.SAVE_COMMIT_GRACE_MS.
    SAVE_COMMIT_GRACE_MS = 2000

    # Confirmed-live accepted date format for the publicationDate field's
    # rendered placeholder (`__/__/____`) — MM/DD/YYYY, no time component
    # (unlike home_business_events' MM/DD/YYYY hh:mm AM date/time fields).
    DATE_FORMAT_EXAMPLE = "MM/DD/YYYY"

    # ---- Navigation -------------------------------------------------------
    def open_news_articles_list(self) -> "HomeLatestNewsAdminPage":
        """Product Menu > Content & Data > News Articles. Never a cached
        deep-link URL — the rendered list URL embeds a per-session portlet
        instance id that regenerates every session (same pattern as every
        sibling admin Page Object on this project)."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))

        if not self.is_visible(CONTENT_DATA_MENU_ITEM):
            self.click(PRODUCT_MENU_TOGGLE)
            self.wait_for(CONTENT_DATA_MENU_ITEM)
        self.click(CONTENT_DATA_MENU_ITEM)
        self.wait_for(NEWS_ARTICLES_MENU_ITEM)
        self.click(NEWS_ARTICLES_MENU_ITEM)
        self.wait_for(self.LIST_ROW, first=True, timeout=20000)
        return self

    def open_new_article_form(self) -> "HomeLatestNewsAdminPage":
        self.open_news_articles_list()
        self.click(self.ADD_BUTTON)
        self.wait_for(self.SAVE_BUTTON, timeout=20000)
        self.wait_for(self.TITLE_INPUT, timeout=20000)
        return self

    def open_article_edit_form_by_title(self, title: str) -> "HomeLatestNewsAdminPage":
        self.open_news_articles_list()
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
            self.open_news_articles_list()
            if self.row_visible(title):
                return True
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(poll_ms)

    def delete_row_by_title(self, title: str) -> bool:
        """Delete via the row's Actions kebab -> Delete -> confirm. Returns
        False (no-op) if no matching row exists, so teardown code can call
        this unconditionally. Mirrors
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
    def set_title(self, value: str) -> "HomeLatestNewsAdminPage":
        self.page.locator(self.TITLE_INPUT).fill(value)
        return self

    def set_publication_date(self, value: str) -> "HomeLatestNewsAdminPage":
        """Types `value` (see DATE_FORMAT_EXAMPLE) directly into the
        publicationDate field — mirrors
        HomeBusinessEventsAdminPage.fill_date_field()'s click+type pattern
        (confirmed-live-safe: no Escape keystroke afterward)."""
        self.click(self.PUBLICATION_DATE_INPUT)
        self.page.keyboard.type(value, delay=20)
        return self

    def is_active(self) -> bool:
        return self.page.locator(self.ACTIVE_STATUS_CHECKBOX).is_checked()

    def set_active(self, active: bool) -> "HomeLatestNewsAdminPage":
        self.set_checkbox(self.ACTIVE_STATUS_CHECKBOX, active)
        return self

    def upload_thumbnail_image(self, file_path: str) -> "HomeLatestNewsAdminPage":
        """Same confirmed-live Documents-and-Media picker flow reused
        verbatim from HomePromoBannersAdminPage._upload_image()."""
        self.page.locator(f"{self.THUMBNAIL_IMAGE_CONTAINER} {self.SELECT_FILE_BUTTON}").click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)
        frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click()
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
        except Exception:
            self.page.wait_for_timeout(1000)
        return self

    def uploaded_thumbnail_filename(self) -> str:
        container_text = self.page.locator(self.THUMBNAIL_IMAGE_CONTAINER).inner_text()
        for line in container_text.splitlines():
            line = line.strip()
            if line and line != "Select File" and "Upload a " not in line and not line.endswith(")"):
                return line
        return ""

    def status_value(self) -> str:
        """TODO(locator): no field/column on this Object Definition
        currently carries a Draft/Approved workflow status (see module
        docstring's WORKFLOW FINDING) — there is nothing live to read yet.
        Left unimplemented (raises) rather than faked so the one caller
        (this page's disclosed-skip test) fails loudly if the skip is ever
        removed without wiring this up first."""
        raise NotImplementedError(
            "status_value() has no confirmed-live locator: the 'News Article' "
            "Object Definition has No Workflow attached, so no field carries a "
            "Draft/Approved status today. Implement this once a workflow (and "
            "therefore a status column/field) is attached on the environment."
        )

    def save(self) -> "HomeLatestNewsAdminPage":
        self.click(self.SAVE_BUTTON)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(self.SAVE_COMMIT_GRACE_MS)
        return self

    def cancel(self) -> "HomeLatestNewsAdminPage":
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

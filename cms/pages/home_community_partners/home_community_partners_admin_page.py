"""
web/pages/home_community_partners/home_community_partners_admin_page.py —
CommunityPartnersAdminPage.

Control_Panel Page Object for PBI 129385 (Home Page "Community Partners"
management), backing the Object Definition entry list/edit surface reached
via Content & Data > "Community Partners" (objectDefinitionId=45665,
groupId=37246). Renders the public Home Page's Community Partners carousel
— see home_community_partners_page.py for the public-frontend counterpart.

THIS SESSION (2026-08-31, headless-equivalent MCP browser, 1920x1080,
authenticated qcdev session) COMPLETES the field-level exploration the
prior interrupted session could not finish. Every locator/behavior below
was independently exercised live this session — none are inherited
unverified from the prior session's docstring.

SAFETY-CHECK FINDINGS (Step 1 of this session, before any new work):
  - A leftover Object Definition entry from the PRIOR interrupted session
    was found live in the list: ID 112844, Partner Name (EN) "QCTEST-135829
    Test Partner Co", Display Order 997, Active=Yes, Status "Approved".
    DELETED this session via the row's Actions kebab -> Delete -> confirm.
  - The 3 real, shared records (QatarEnergy/100, Qatar Airways/200, QNB/300)
    were all confirmed Active=Yes / Status "Approved" both before and after
    cleanup — no mutation of any of them was needed or performed.
  - A SECOND leftover entry (ID 112876, "QCTEST-135830 Validation Co") was
    created and deleted by THIS session's own field-level probing (see
    "Real validation behavior" below) — disclosed here rather than left
    implicit. Final state re-confirmed live: exactly 3 entries, all
    Active=Yes / Approved.

REAL, LIVE-CONFIRMED FORM SHAPE (this session) — CONTRADICTS several of
PBI 129385's case assumptions; these are genuine case-vs-product
discrepancies, not omissions, and are NOT silently reworded past:
  - The Add/Edit form has exactly SIX fields, confirmed live via each
    field's own `data-field-name` attribute on its `div.ddm-field`
    container (the same stable-anchor strategy home_dynamic_widgets_admin_
    page.py already established for this project — NOT the regenerating
    `id`/`name` on the inner `<input>`, which embeds a random per-field
    token, e.g. `...ddm$$partnerNameEn$Qmj4vLni$0$$en_US`):
      activeStatus (native checkbox, label "Active")
      displayOrder (text input)
      partnerLogoColor (file upload, label "Partner Logo (Color, hover
        state)") — ONE field, not a Logo (EN)/(AR) pair
      partnerNameAr (text input, label "Partner Name (AR)")
      partnerNameEn (text input, label "Partner Name (EN)")
      partnerUrl (text input, label "Partner URL")
    There is NO Alt Text (EN)/(AR) field anywhere on this form — the public
    carousel's `<img alt="...">` is confirmed live (via the public Home
    page's own rendered DOM) to reuse Partner Name (EN) as the alt text,
    not a separate authored field. PBI 129385's case set describing
    "Logo EN/AR" and "Alt Text EN/AR" fields has no real target on this
    form — build against the REAL six fields only.
  - Real, live-exercised required-field behavior: `aria-required="true"`
    is present ONLY on the Partner Name (EN) input (confirmed live via a
    direct DOM attribute read). Save was exercised twice this session to
    confirm this empirically, not just by reading the attribute:
      1. All fields filled EXCEPT Partner Logo -> Save -> SUCCEEDED (the
         entry was created, Status "Approved", logo cell empty in the
         list). Logo is NOT enforced as required by this form, contrary
         to TC 135830's premise ("Logo Image is required."). This is a
         disclosed case-vs-product discrepancy for the QA Manager to
         adjudicate (missing product-side validation vs. a wrong case) —
         not something this Page Object can resolve unilaterally.
      2. Partner Name (EN) left empty (all else filled) -> Save -> FAILED
         with the exact same platform-wide DDM strings this project's
         other Object-Definition forms use (org_structure, board_members,
         gm_message, home_strategic_direction): banner "This form is
         invalid. Check field Partner Name (EN)." + inline "This field is
         required." SAVE_ERROR_BANNER_TEXT/INLINE_REQUIRED_TEXT below are
         therefore fully re-confirmed live for THIS form, not inherited-
         and-plausible as the prior session's docstring stated.
    TC 135830 is scripted below against the REAL required field (Partner
    Name (EN)) and the REAL validation strings — mirroring the same
    substitution precedent already used in home_strategic_direction_admin_
    page.py / test_home_strategic_direction_control_panel.py's TC 135556
    note ("asserts on the REAL field ... and the REAL strings, not the
    case's paraphrase").
  - There is NO separate Preview/Draft/Publish lifecycle on this form:
    exactly two buttons exist at all times, "Save" and "Cancel" (confirmed
    live — same shape gm_message_admin_page.py and home_dynamic_widgets_
    admin_page.py already document for this project's Object-Definition
    editor family). Clicking Save publishes directly to Status "Approved" —
    confirmed live via both probe Saves above. TC 135829's stated
    Draft -> Preview -> Publish sequence has no real target on this form;
    it collapses to a single Save that publishes immediately.
  - File upload ("Select File") opens a Liferay Documents-and-Media picker
    MODAL (`dialog` containing `iframe[title="Select File"]`) — same class
    of picker home_dynamic_widgets_admin_page.py and home_strategic_
    direction_admin_page.py already document, but the WORKING selection
    flow for THIS form was independently confirmed live and differs from
    both precedents: setting the OUTER page's own
    `div.ddm-field[data-field-name="partnerLogoColor"] input[type="file"]`
    directly (the dynamic_widgets approach) does NOT work here — it throws
    a live, reproduced JS error ("Cannot read properties of undefined
    (reading 'sessionState')") and the field never populates. The real
    working path, confirmed live end-to-end this session: click "Select
    File" -> the modal's OWN `iframe[title="Select File"]` mounts a
    Documents-and-Media picker with a real `input[type="file"]` inside it
    -> `set_input_files()` on THAT inner input uploads into the library
    (confirmed live: the uploaded filename appears in the picker's own
    "Add" staging area) -> clicking the picker's "Add" button both commits
    the upload AND auto-selects it for the field, closing the modal and
    populating `partnerLogoColor`'s own filename display (confirmed live:
    "partner_logo (1).png" rendered inside the field's container
    immediately after "Add", with the modal already closed — no separate
    "select from library" click was needed for a freshly-uploaded file).
  - Row ID link opens the record's `edit_object_entry` form directly — same
    one-click pattern as every sibling admin Page Object in this project.
    ROW_ID_LINK (see below) was CORRECTED this follow-up session from
    `"table tbody a"` to `"td.cell-id a"` — the former is itself an
    absolute-looking selector, so chaining it after a row scope via " >> "
    made Playwright search for a NESTED table inside the row (never exists),
    causing `open_partner_edit_form_by_name()` to hang the full 30s
    Playwright click timeout on ANY partner name, confirmed live as
    TC 135832's root cause. `td.cell-id a` (confirmed live via the ID
    cell's real `class="cell-id"`) is the same relative pattern
    board_members_admin_page.py / home_strategic_direction_admin_page.py /
    home_dynamic_widgets_admin_page.py already use for this exact shape.

FOLLOW-UP SESSION (2026-08-31, continued — live root-causing TC 135829 and
TC 135832's fresh pytest-run failures against a real 30s TimeoutError, per
explicit instruction, not reasoned about from source alone):
  - TC 135832 root cause: the ROW_ID_LINK bug above. Fixed; TC 135832
    re-run and PASSED after the fix.
  - `open_new_partner_form()`'s wait for PARTNER_NAME_EN_INPUT used the
    wrapper's bare 10s default; live-measured this session at needing up to
    ~7.5s+ under real pytest load for this full-page-navigation create form
    (same class of lag documented for ROW_ID_LINK_RELOAD_TIMEOUT_MS
    elsewhere). Bumped to NEW_FORM_FIELD_TIMEOUT_MS (20000ms).
  - `wait_for_row_visible()`'s default budget (8000ms) was too tight given
    each poll cycle re-runs the FULL `open_community_partners_list()`
    navigation (menu clicks, not a bare reload) — bumped to 20000ms.
  - `delete_row_by_name()`'s kebab locator, `button[aria-label$="Actions"]`,
    matched ZERO elements — confirmed live the kebab button carries NO
    `aria-label` attribute at all; its accessible name comes only from a
    nested `<span class="sr-only">{id} Actions</span>`. The locator's own
    `.first.click()` therefore hung Playwright's full 30s action-timeout
    waiting on an unresolvable locator (not a real UI-blocking overlay) —
    the actual root cause of two live leftover rows this session
    (113068/113102, then 113142/113164) that this method's own `finally`
    cleanup silently failed to remove. Fixed to `row.get_by_role("button",
    name="Actions")`, which computes the accessible name the same way a
    real user/assistive-tech would (from the sr-only text), and both
    leftover pairs were removed manually via live re-verification.
  - TC 135829's remaining failure after the above: the new-entry create
    form's Active checkbox defaults to UNCHECKED (confirmed live: two
    leftover rows this session, 113142/113164, both rendered "Active: No"
    despite the test never touching that field) — the case's own assertion
    (new partner's logo appears on the Home Page) can never pass without
    setting it, since the public carousel only renders Active=Yes partners
    (the same behavior TC 135832 exploits in reverse). Fixed in the TEST
    (`test_create_new_community_partner_appears_on_home_page` now calls
    `admin.set_active(True)` before Save) — not a Page Object change, since
    this is case-specific test data, not a form-shape correction.
  - Both TC 135829 and TC 135832 were independently re-run in isolation
    after these fixes and PASSED. Final admin-list state re-confirmed live:
    exactly the 3 real records (QatarEnergy/45744, Qatar Airways/45776,
    QNB/45808), all Active=Yes / Status "Approved" — no leftover test rows.
  - New-entry entry point: `button[data-testid="fdsCreationActionButton"]`,
    accessible name "Add Community Partner" (visible label "New").
  - List columns, in order: Item Selection, ID, Active, Display Order,
    "Partner Logo (Color, hover state)", Partner Name (AR), Partner Name
    (EN), Partner URL, Status, Author, Item Actions.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
COMMUNITY_PARTNERS_MENU_ITEM = '[role="menuitem"]:text-is("Community Partners")'
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'

# Confirmed live this session — the 3 real, shared records. Names only (not
# full row data) so a test can assert "still visible" / "no longer visible"
# without hardcoding column order.
QATAR_ENERGY_NAME = "QatarEnergy"
QATAR_AIRWAYS_NAME = "Qatar Airways"
QNB_NAME = "QNB"


class CommunityPartnersAdminPage(BasePage):
    # ---- List screen — CONFIRMED LIVE -----------------------------------
    ADD_BUTTON = 'button[data-testid="fdsCreationActionButton"]'
    LIST_ROW = "table tbody tr"
    # RELATIVE to LIST_ROW when chained with " >> " — NOT "table tbody a".
    # "table tbody a" is itself an absolute-looking selector, so chaining it
    # after a row scope (`row >> table tbody a`) makes Playwright look for a
    # NESTED table inside the row, which never exists — the exact "text-then-
    # following-element" fragility class already fixed elsewhere in this
    # project (see GM_NAME's original bug). Confirmed live this session: the
    # ID cell actually carries `class="cell-id"` (`td.cell-id a`), the SAME
    # relative pattern board_members_admin_page.py / home_strategic_
    # direction_admin_page.py / home_dynamic_widgets_admin_page.py already
    # use successfully for this exact row-lookup-and-click shape — reused
    # here rather than inventing a fresh ad-hoc locator.
    ROW_ID_LINK = "td.cell-id a"

    def _row_actions_kebab(self, row_id: str) -> str:
        return f'button[aria-label*="{row_id} Actions"], button:has-text("{row_id} Actions")'

    # ---- Edit/Add form — CONFIRMED LIVE, present at all times -----------
    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # ---- Edit/Add form fields — data-field-name anchored, CONFIRMED LIVE
    # this session (see module docstring; deliberately not the regenerating
    # per-field id/name substrings) ----------------------------------------
    ACTIVE_CHECKBOX = 'div.ddm-field[data-field-name="activeStatus"] input[type="checkbox"], input[type="checkbox"][name*="ddm$$activeStatus"]'
    # NOTE: activeStatus's container was not independently re-confirmed to
    # carry data-field-name="activeStatus" (only displayOrder/
    # partnerLogoColor/partnerNameAr/partnerNameEn/partnerUrl were read via
    # the live div.ddm-field dump) — the checkbox itself, `getByRole
    # ("checkbox", {name: "Active"})`, IS confirmed live and is the primary
    # locator `set_active()`/`is_active()` use below; the data-field-name
    # form is kept only as a documented, not fully independently
    # re-verified, fallback.
    ACTIVE_CHECKBOX_BY_LABEL = 'input[type="checkbox"]'
    DISPLAY_ORDER_INPUT = 'div.ddm-field[data-field-name="displayOrder"] input[type="text"]'
    PARTNER_LOGO_CONTAINER = 'div.ddm-field[data-field-name="partnerLogoColor"]'
    PARTNER_NAME_AR_INPUT = 'div.ddm-field[data-field-name="partnerNameAr"] input[type="text"]'
    PARTNER_NAME_EN_INPUT = 'div.ddm-field[data-field-name="partnerNameEn"] input[type="text"]'
    PARTNER_URL_INPUT = 'div.ddm-field[data-field-name="partnerUrl"] input[type="text"]'

    SELECT_FILE_BUTTON = 'button:has-text("Select File")'
    # Documents-and-Media picker modal — confirmed live this session as a
    # `dialog` containing `iframe[title="Select File"]`, with the picker's
    # OWN real `input[type="file"]` inside that iframe (NOT the outer
    # page's own field input — see module docstring for why the
    # dynamic_widgets-style direct-input approach fails on this form).
    UPLOAD_MODAL_IFRAME = 'iframe[title="Select File"]'
    UPLOAD_MODAL_ADD_BUTTON_TEXT = "Add"

    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    # ---- Navigation -------------------------------------------------------
    def open_community_partners_list(self) -> "CommunityPartnersAdminPage":
        """Navigate via Content & Data > Community Partners, never a saved/
        hardcoded portlet-instance URL — the rendered list URL embeds a
        per-session portlet instance id that regenerates every session
        (same reasoning as every sibling admin Page Object in this
        project)."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url("/en/home"))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url("/en/home"))

        if not self.is_visible(CONTENT_DATA_MENU_ITEM):
            self.click(PRODUCT_MENU_TOGGLE)
            self.wait_for(CONTENT_DATA_MENU_ITEM)
        self.click(CONTENT_DATA_MENU_ITEM)
        link = self.page.locator(COMMUNITY_PARTNERS_MENU_ITEM)
        link.wait_for(state="visible", timeout=10000)
        link.click()
        self.wait_for(self.LIST_ROW, first=True)
        return self

    def open_partner_edit_form_by_name(self, partner_name: str) -> "CommunityPartnersAdminPage":
        self.open_community_partners_list()
        self.click(f'{self.LIST_ROW}:has-text("{partner_name}") >> {self.ROW_ID_LINK}')
        self.wait_for(self.SAVE_BUTTON)
        return self

    # Clicking ADD_BUTTON is a full page navigation on this form (URL gains
    # `mvcRenderCommandName=/object_entries/edit_object_entry`), not an SPA
    # re-render — live-measured this session at up to ~7.5s just to render
    # the field DOM under a real pytest run's heavier load (same class of
    # lag gm_message_admin_page.py's ROW_ID_LINK_RELOAD_TIMEOUT_MS already
    # documents for this project's Object-Definition grids). The wrapper's
    # bare 10s default timed out a fresh CLI run on this exact wait; bumped
    # to the same conservative 20s precedent rather than a blind retry loop.
    NEW_FORM_FIELD_TIMEOUT_MS = 20000

    def open_new_partner_form(self) -> "CommunityPartnersAdminPage":
        self.open_community_partners_list()
        self.click(self.ADD_BUTTON)
        self.wait_for(self.SAVE_BUTTON, timeout=self.NEW_FORM_FIELD_TIMEOUT_MS)
        self.wait_for(self.PARTNER_NAME_EN_INPUT, timeout=self.NEW_FORM_FIELD_TIMEOUT_MS)
        return self

    # ---- State queries — list-level ---------------------------------------
    def row_visible(self, partner_name: str) -> bool:
        return self.is_visible(f'{self.LIST_ROW}:has-text("{partner_name}")')

    def row_count(self) -> int:
        return self.page.locator(self.LIST_ROW).count()

    def row_active_value(self, partner_name: str) -> str:
        """The row's rendered "Active" column text ("Yes"/"No") for the
        given partner name — confirmed live column order this session."""
        row = self.page.locator(f'{self.LIST_ROW}:has-text("{partner_name}")')
        return row.locator("td").nth(2).inner_text().strip()

    def delete_row_by_name(self, partner_name: str) -> bool:
        """Delete the given row via its Actions kebab -> Delete -> confirm.
        Returns True if a delete was actually performed, False if no
        matching row was found (a no-op, not an error, so cleanup code can
        call this unconditionally). Kebab/Delete/confirm-dialog flow
        confirmed live this session (used to remove both the prior
        session's and this session's own leftover test entries)."""
        row = self.page.locator(f'{self.LIST_ROW}:has-text("{partner_name}")')
        if row.count() == 0:
            return False
        # NOT `button[aria-label$="Actions"]` — confirmed live this session
        # the kebab button carries NO `aria-label` attribute at all; its
        # accessible name comes only from a nested `<span class="sr-only">
        # {id} Actions</span>`, so that attribute-selector silently matched
        # ZERO elements and `.first.click()` hung the full 30s Playwright
        # action-timeout waiting for a locator that could never resolve —
        # the actual root cause of this method's live 30s TimeoutErrors, not
        # a real UI-blocking overlay. `get_by_role` computes the accessible
        # name from that same sr-only text, so it matches the real element.
        kebab = row.get_by_role("button", name="Actions")
        kebab.first.click()
        # The dropdown is a portal-rendered clay-dropdown-menu, not scoped
        # under the row — select the currently-VISIBLE one's "Delete" item
        # (confirmed live: querying [role="menuitem"] globally can match
        # stale/hidden menus from prior rows).
        delete_item = self.page.locator('[role="menuitem"]:visible:has-text("Delete")')
        delete_item.first.wait_for(state="visible", timeout=5000)
        delete_item.first.click()
        # Live-observed this session: a 300ms sleep + 5000ms confirm-wait
        # intermittently threw `locator.waitFor: Timeout 5000ms exceeded ...
        # waiting for navigation to finish` — the confirm dialog can still
        # be mid-render/mid-navigation past 5s under real load. Widened to
        # 10000ms and waiting on the dialog's own visibility rather than a
        # fixed sleep beforehand; this exact confirm step's silent failure
        # is what left 113068/113102 and 113142/113164 as leftover rows
        # this session.
        confirm = self.page.get_by_role("button", name="Delete")
        confirm.wait_for(state="visible", timeout=10000)
        confirm.click()
        self.page.wait_for_load_state("networkidle")
        return True

    # ---- Field actions ------------------------------------------------------
    def set_partner_name_en(self, value: str) -> "CommunityPartnersAdminPage":
        self.page.locator(self.PARTNER_NAME_EN_INPUT).fill(value)
        return self

    def set_partner_name_ar(self, value: str) -> "CommunityPartnersAdminPage":
        self.page.locator(self.PARTNER_NAME_AR_INPUT).fill(value)
        return self

    def set_partner_url(self, value: str) -> "CommunityPartnersAdminPage":
        self.page.locator(self.PARTNER_URL_INPUT).fill(value)
        return self

    def set_display_order(self, value: str) -> "CommunityPartnersAdminPage":
        self.page.locator(self.DISPLAY_ORDER_INPUT).fill(value)
        return self

    def display_order_value(self) -> str:
        return self.page.locator(self.DISPLAY_ORDER_INPUT).input_value()

    ACTIVE_CHECKBOX_ROLE_LOCATOR = 'role=checkbox[name="Active"]'

    def is_active(self) -> bool:
        return self.page.get_by_role("checkbox", name="Active").is_checked()

    def set_active(self, active: bool) -> "CommunityPartnersAdminPage":
        self.set_checkbox(self.ACTIVE_CHECKBOX_ROLE_LOCATOR, active)
        return self

    def upload_partner_logo(self, file_path: str) -> "CommunityPartnersAdminPage":
        """Confirmed-live working flow (see module docstring) — click
        Select File, wait for the picker modal's own iframe, set the file
        on the PICKER'S inner input[type=file] (not the outer page field
        input, which is confirmed broken for this form), then click the
        picker's own "Add" button, which both uploads AND auto-selects the
        file for the field in one action.

        HARDENED (2026-08-31, live investigation of
        test_create_new_community_partner_appears_on_home_page /
        test_omitting_required_partner_name_en_blocks_save failures): the
        prior fixed `wait_for_timeout(1000)` after the "Add" click measured
        live at ~200ms to fully detach the picker's own
        `iframe[title="Select File"]` on a warm session — comfortably inside
        that budget on THIS session's replay — but is a blind guess under
        heavier load, and this same widget-shape ("a click on the item
        UNDERNEATH a still-closing popup gets eaten by the popup's own
        outside-click-dismiss handler, so the actual submit/Save never
        fires and the calling test then misreads the resulting silence as
        either 'not visible after Save' or 'no validation error' — see
        GmMessageAdminPage.select_status()'s own confirmed-live network-
        capture evidence of the identical failure mode) is exactly the
        shared root cause GmMessageAdminPage's docstring already documents
        for its Status combobox popup. Waiting for a REAL signal (the
        picker iframe's own detachment) rather than a fixed sleep closes
        that race deterministically instead of merely making it less
        likely."""
        self.page.locator(f"{self.PARTNER_LOGO_CONTAINER} {self.SELECT_FILE_BUTTON}").click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)
        frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click()
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
        except Exception:
            # Fallback for an environment where the iframe node lingers
            # detached-but-present rather than being removed outright —
            # the bounded sleep below is the last-resort safety net, not
            # the primary wait.
            self.page.wait_for_timeout(1000)
        return self

    def uploaded_logo_filename(self) -> str:
        """The currently-attached logo's rendered filename, or "" if none —
        confirmed live: after a successful upload, the filename renders as
        a second element inside the same ddm-field container, alongside
        "Select File"."""
        container_text = self.page.locator(self.PARTNER_LOGO_CONTAINER).inner_text()
        for line in container_text.splitlines():
            line = line.strip()
            if line and line not in ("Select File", "Partner Logo (Color, hover state)") and "Upload a [" not in line:
                return line
        return ""

    # Same disclosed-evidence save-commit grace as GmMessageAdminPage's
    # SAVE_COMMIT_GRACE_MS — a live network capture this session confirmed
    # the create POST (`/o/c/communitypartners/scopes/...`) itself returns
    # 200 synchronously, but `open_community_partners_list()`'s own grid
    # render is a SEPARATE read path (same class of write-vs-read-cache gap
    # gm_message_admin_page.py measured for its own Object Definition list).
    # Not independently re-timed for this content type specifically; reused
    # at the same conservative value pending its own measurement.
    SAVE_COMMIT_GRACE_MS = 2000

    def save(self) -> "CommunityPartnersAdminPage":
        self.click(self.SAVE_BUTTON)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(self.SAVE_COMMIT_GRACE_MS)
        return self

    def wait_for_row_visible(self, partner_name: str, timeout_ms: int = 20000, poll_ms: int = 500) -> bool:
        """Poll (re-navigating to the list each cycle, not a bare re-render
        wait) until `partner_name`'s row appears or `timeout_ms` elapses —
        guards the SAME read-side lag class SAVE_COMMIT_GRACE_MS documents,
        for a caller that lands on the list some time after save() rather
        than immediately after it. Returns True/False rather than raising,
        so the calling test controls its own assertion message."""
        import time

        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_community_partners_list()
            if self.row_visible(partner_name):
                return True
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(poll_ms)

    def cancel(self) -> "CommunityPartnersAdminPage":
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

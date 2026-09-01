"""
web/pages/home_dynamic_widgets/home_dynamic_widgets_admin_page.py —
HomeDynamicWidgetsAdminPage.

Control_Panel Page Object for PBI 129384 (Home Page "Dynamic Widgets" —
Marhaba Guide / B2B Platform / Weather), backing the "Dynamic Widgets"
Object Definition (control-panel menu: Content & Data > Dynamic Widgets)
that drives the `section.qc-home-dynamic-widgets` block on the public Home
page (see home_dynamic_widgets_page.py for the public-frontend counterpart).

REAL, LIVE-VERIFIED FACTS (this session, 2026-08-31, against qcdev):

  - Object Definition menu entry: Content & Data > "Dynamic Widgets"
    (objectDefinitionId=49566, portlet instance id P4D0 this session — the
    instance id regenerates per session/render exactly like
    gm_message_admin_page.py's GM_MESSAGES_LIST_URL note; objectDefinitionId
    itself was CONFIRMED STABLE (49566) across three independent live reads
    in this session — do not add retry/regeneration handling around it).
  - **Root cause of severe, reproducible navigation flakiness this session,
    confirmed live and worth recording**: clicking the "Dynamic Widgets"
    Product-Menu flyout item with `{force: true}` (bypassing Playwright's
    actionability/visibility wait) repeatedly landed on a DIFFERENT,
    currently-visible flyout item instead (Business Events, Community
    Partners, Upcoming Event Pins, Strategic Pillar Cards were all observed
    substituted in) because the flyout was still animating into place at
    click time. Waiting for the link to be `visible` FIRST, then a normal
    (non-forced) `.click()`, resolved to the correct Dynamic Widgets grid
    reliably and repeatedly. `open_dynamic_widgets_list()` below always
    waits for the link's visibility before clicking — never pass
    `force=True` on this navigation.
  - The list is a flat 2-row grid (IDs 49679 and 49711 this session) — NOT
    a per-widget-type list. There is no "widget name"/"type" column in the
    grid (confirmed live: headers are exactly Item Selection, ID, Active
    Status, Display Order, Open in New Tab, Redirect URL, Widget Image
    (AR), Widget Image (EN), Status, Author, Item Actions) and no
    "name"/"title" FIELD on the edit form either — an author cannot tell
    which row is "Marhaba Guide" vs. "B2B Platform" from the admin UI
    alone. The only identifying signal available live is each record's
    `externalReferenceCode` (visible in the row's own edit-form URL, not
    in any rendered UI text): row 49711 is ERC
    `QCDEMO-129384-b2b-verified` (redirect `https://qcci.org`, confirmed
    live to render as the B2B `.qc-dw-card` on the public Home page) — a
    solid, confirmed match for TC 135967 (B2B Platform). Row 49679 is ERC
    `QCDEMO-129384-directory` (redirect `https://www.qatarchamber.com`,
    confirmed live to render as the OTHER `.qc-dw-card`) — this is the
    only other seeded row, so TC 135966 (Marhaba Guide) is mapped onto it
    by elimination, NOT by a confirmed "Marhaba" label anywhere live. This
    is a disclosed, real gap — flag back to the QA Manager for the team to
    confirm the "directory" ERC really is the Marhaba Guide slot before
    trusting this test's identity assumption long-term.
  - Row link: each grid row's ID cell is a real anchor
    (`td.cell-id a`, `data-senna-off="true"` — a real full page load per
    click, no Senna/SPA transition) straight into the record's
    `edit_object_entry` form — same one-click pattern as
    gm_message_admin_page.py's ROW_ID_LINK, no kebab->View round-trip
    needed.
  - **The edit form's real interactive fields render OUTSIDE the classic
    `<form>` element** (the `<form>` itself holds only hidden inputs plus
    the Save/Cancel buttons; the visible DDM fields are React-rendered
    siblings synced into the form's `ddmFormValues` hidden input on
    submit) — confirmed live by dumping the form's own `innerText`
    (empty) vs. the surrounding document (has all field labels). Do not
    scope field locators to `form ...` — anchor them on the page/document
    the way this Page Object does below.
  - **A real, measured async-mount gap**: reading field labels immediately
    after `goto()` (even with `wait_until="load"`) returned an EMPTY field
    set on a fresh navigation in this session; only after
    `wait_until="networkidle"` PLUS an explicit ~2.5s settle returned the
    full field set reliably. `FORM_MOUNT_GRACE_MS` below is that measured
    value, not a blind guess — mirrors the same class of gap
    gm_message_admin_page.py's `SAVE_COMMIT_GRACE_MS` documents for its
    own (different) read-after-write case.
  - Confirmed live field set for BOTH rows (Marhaba/B2B "content" widgets):
    Active Status (native checkbox, NOT the custom combobox GM Message's
    Status field uses), Display Order (ddm-field text input), Open in New
    Tab (native checkbox), Redirect URL (ddm-field text input), Widget
    Image (EN) (ddm-field file upload, `accept=".jpg,.png,.svg"` —
    confirmed live, so the case's `.jpg`/`.png` AND `.svg` fixtures are
    all valid), Widget Image (AR) (same, own file input).
  - Each `ddm-field` container carries a STABLE, non-regenerating
    `data-field-name` attribute (`data-field-name="displayOrder"`,
    `"redirectUrl"`, `"widgetImageEn"`, `"widgetImageAr"` — confirmed live
    on the container `<div class="ddm-field">`, NOT the regenerating
    `id`/`name` on the input itself) — used to scope every ddm-field
    locator below instead of GM Message's id-substring or label-proximity
    approaches; this is a cleaner, more stable locator than either of
    those precedents for this particular form.
  - Active Status / Open in New Tab are native
    `input[type="checkbox"]` — NOT the custom Liferay combobox GM
    Message's Status field required. The checkbox's own `name` attribute
    reliably contains a stable `ddm$$activeStatus` / `ddm$$openInNewTab`
    substring (confirmed live) even though the rest of the name embeds the
    regenerating portlet-instance id and a per-field random token — same
    class of substring-stability GM Message's `_text_input_by_id_substring`
    relies on.
  - **Weather has NO admin surface inside this Object Definition, and no
    Object Definition of its own was found anywhere in the full Content &
    Data menu (confirmed live: the complete menu item list was dumped this
    session and contains no "Weather" entry).** The public Home page's
    Weather card is rendered by a separate `qc-weather-widget` CLIENT
    EXTENSION (confirmed live via an inline HTML comment on the rendered
    page itself: "Weather widget (PBI 129384 / T45): ... rendered by the
    qc-weather-widget Client Extension ... calls the Weather API for Doha")
    — a fundamentally different admin mechanism (Client Extension /
    instance configuration) than an Object Definition entry, and this
    session found no confirmed control-panel screen for it. TC 135968's
    own central assertion — that ITS edit form shows ONLY Active Status +
    Display Order — is also structurally impossible against THIS Object
    Definition, whose schema (Active Status, Display Order, Open in New
    Tab, Redirect URL, both Widget Images) is shared by every row; there
    is no way for one row of one Object Definition to expose fewer fields
    than another. `open_weather_widget_edit_form()` below is therefore a
    disclosed, unverified placeholder — see its own docstring — not a
    real, confirmed locator.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

# Grid rows this session (see module docstring for the ERC-based identity
# mapping and its disclosed uncertainty for Marhaba Guide specifically).
MARHABA_ROW_ID = "49679"  # ERC QCDEMO-129384-directory — mapped by elimination, NOT confirmed by label
B2B_ROW_ID = "49711"  # ERC QCDEMO-129384-b2b-verified — confirmed live (redirects to qcci.org, renders as the B2B card)

_UNVERIFIED = "TODO: no live admin surface found for this widget this session — see module docstring"


class HomeDynamicWidgetsAdminPage(BasePage):
    # ---- Menu navigation ----------------------------------------------------
    ADMIN_HOME_EN_URL_PATH = "/en/home"  # see gm_message_admin_page.py's identical note on forcing EN locale
    PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
    CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
    DYNAMIC_WIDGETS_MENU_ITEM = '[role="menuitem"]:text-is("Dynamic Widgets")'

    # ---- List screen ------------------------------------------------------
    LIST_ROW = "table tbody tr"
    ROW_ID_LINK = 'td.cell-id a'

    def _row_id_link(self, record_id: str) -> str:
        return f'td.cell-id a:text-is("{record_id}")'

    # ---- Async field-mount grace (see module docstring) --------------------
    FORM_MOUNT_GRACE_MS = 2500

    # ---- Edit form fields (data-field-name anchored, see docstring) --------
    ACTIVE_STATUS_CHECKBOX = 'input[type="checkbox"][name*="ddm$$activeStatus"]'
    OPEN_IN_NEW_TAB_CHECKBOX = 'input[type="checkbox"][name*="ddm$$openInNewTab"]'
    DISPLAY_ORDER_INPUT = 'div.ddm-field[data-field-name="displayOrder"] input[type="text"]'
    REDIRECT_URL_INPUT = 'div.ddm-field[data-field-name="redirectUrl"] input[type="text"]'
    WIDGET_IMAGE_EN_CONTAINER = 'div.ddm-field[data-field-name="widgetImageEn"]'
    WIDGET_IMAGE_AR_CONTAINER = 'div.ddm-field[data-field-name="widgetImageAr"]'
    SELECT_FILE_BUTTON = 'button:has-text("Select File")'
    FILE_INPUT = 'input[type="file"]'
    # HEALED (2026-08-31, live investigation against qcdev record 49679,
    # tc_135966/tc_135967): confirmed live, by direct DOM inspection, that
    # clicking SELECT_FILE_BUTTON does NOT open a native OS file chooser —
    # it opens a Liferay Documents-and-Media picker MODAL
    # (`.liferay-modal.show` / `.modal.show`, containing an
    # `iframe[title="Select File"]`) that stays open in the DOM afterward.
    # `upload_widget_image_en/ar()` never goes through that modal's own
    # picker flow — it sets the field's real `input[type="file"]` directly
    # via `upload_file()` (confirmed live: this DOES populate the input's
    # `.files`), but the modal itself is a SEPARATE DOM node with no causal
    # link to the input's change event, so it is left open and covers the
    # rest of the page. Confirmed live, reproduced twice: uploading the EN
    # image this way leaves the modal open, and the immediately-following
    # click on the AR field's OWN "Select File" button (a different,
    # already-visible, already-enabled button) times out because the
    # still-open modal's iframe physically overlaps/intercepts it —
    # Playwright's own trace names the exact intercepting element
    # (`<iframe title="Select File">`). Closing the modal's "Close" button
    # (`aria-label="Close"`, confirmed live present on every such modal)
    # immediately after each upload — before returning control to the
    # caller — was confirmed live to unblock the very next field's click
    # with no other side effect (the just-set input's `.files` is untouched
    # by closing the modal, confirmed live via a fresh `.files.length`
    # read after close).
    UPLOAD_MODAL = '.liferay-modal.show, .modal.show'
    # HARDENED (2026-08-31, live investigation of a tc_135966 failure, this
    # session): the previous `f'{UPLOAD_MODAL} button[...]'` interpolation
    # expanded to the selector LIST `.liferay-modal.show,
    # .modal.show button[aria-label="Close"]` — a bare top-level comma does
    # not distribute a descendant combinator across both terms, so term 1
    # matched the modal CONTAINER itself, not a button inside it. In
    # document order the container sorts before its own descendant button,
    # so `.first` on that list resolved to the container — clicking it
    # never dismisses the modal, which is exactly this session's timeout
    # symptom. `:is(...)` groups the two container alternatives into one
    # compound selector before the descendant combinator applies, so both
    # terms correctly resolve to "a Close button inside whichever modal
    # class matched."
    UPLOAD_MODAL_CLOSE_BUTTON = ':is(.liferay-modal, .modal).show button[aria-label="Close"]'

    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # Mirrors gm_message_admin_page.py / board_members_admin_page.py's
    # confirmed-live plain-text validation-error scan (no stable
    # class/role found for either message on this project's DDM forms).
    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    # Not confirmed live this session (no live Save was exercised against
    # the shared qcdev singleton rows during exploration, to avoid an
    # unrecoverable overwrite before the Page Object existed to restore
    # a captured baseline) — same disclosed-placeholder pattern as
    # gm_message_admin_page.py's SUCCESS_TOAST.
    SAVE_COMMIT_GRACE_MS = 2000

    # ---- Weather — disclosed, unverified placeholder (see docstring) -------
    WEATHER_ADMIN_ENTRY_POINT = _UNVERIFIED

    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"HomeDynamicWidgetsAdminPage.{name} is an unverified placeholder — "
                f"no live control-panel surface for the Weather widget was found this "
                f"session (see module docstring). Confirm the real admin location "
                f"before relying on this."
            )

    # ---- Navigation -----------------------------------------------------
    def open_dynamic_widgets_list(self) -> "HomeDynamicWidgetsAdminPage":
        """Navigate via Content & Data > Dynamic Widgets. Always enters via
        the explicit English-locale home URL first (mirrors
        gm_message_admin_page.py's identical fix for the same qcdev
        AR-locale-persists-into-admin risk).

        CRITICAL: the Dynamic Widgets flyout item must be WAITED for
        (`state="visible"`) before clicking, and must NEVER be clicked with
        `force=True` — see the module docstring's flakiness root-cause note.
        A forced click on a still-animating flyout was confirmed live to
        land on a different, unrelated Object Definition's grid instead."""
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

        link = self.page.locator(self.DYNAMIC_WIDGETS_MENU_ITEM)
        link.wait_for(state="visible", timeout=10000)
        link.click()  # no force=True — see docstring
        # LIST_ROW ("table tbody tr") is only confirming the grid rendered
        # at least one row here — this call never targets a specific row
        # (that's ROW_ID_LINK / _row_id_link()'s job downstream in
        # open_widget_edit_form()). The grid legitimately has 2 seeded rows
        # (Marhaba/directory 49679, B2B 49711 — see module docstring), so
        # a plain `wait_for(LIST_ROW)` throws a Playwright strict-mode
        # violation here (confirmed live). `first=True` tells the shared
        # BasePage.wait_for() wrapper to scope to `.first` internally — it
        # still runs the wrapper's license-gate/reauth checks and the
        # post-wait announcement-overlay dismissal, which a raw
        # `self.page.locator(...).first.wait_for(...)` at this call site
        # would have silently skipped right before the very click-driven
        # navigation this module's docstring flags as its worst flakiness
        # source.
        self.wait_for(self.LIST_ROW, first=True)
        return self

    def open_widget_edit_form(self, record_id: str) -> "HomeDynamicWidgetsAdminPage":
        """Open the given row's edit form via its ID-cell link, then wait
        out the confirmed-live async field-mount gap (FORM_MOUNT_GRACE_MS)
        before any field locator is used — see module docstring."""
        self.open_dynamic_widgets_list()
        self.click(self._row_id_link(record_id))
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(self.FORM_MOUNT_GRACE_MS)
        self.wait_for(self.DISPLAY_ORDER_INPUT)
        return self

    def open_marhaba_edit_form(self) -> "HomeDynamicWidgetsAdminPage":
        """See MARHABA_ROW_ID's docstring note: this row is mapped onto
        Marhaba Guide BY ELIMINATION (the only other seeded row besides the
        confirmed B2B row), not by a live-confirmed "Marhaba" label."""
        return self.open_widget_edit_form(MARHABA_ROW_ID)

    def open_b2b_edit_form(self) -> "HomeDynamicWidgetsAdminPage":
        """Confirmed live: ERC QCDEMO-129384-b2b-verified, redirects to
        qcci.org, renders as the B2B `.qc-dw-card` on the public Home page."""
        return self.open_widget_edit_form(B2B_ROW_ID)

    def open_weather_widget_edit_form(self) -> "HomeDynamicWidgetsAdminPage":
        """Disclosed, unverified — see WEATHER_ADMIN_ENTRY_POINT / module
        docstring. No live control-panel surface for Weather was found this
        session; Weather is rendered by a Client Extension, not an Object
        Definition entry."""
        self._require_verified(self.WEATHER_ADMIN_ENTRY_POINT, "WEATHER_ADMIN_ENTRY_POINT")
        return self  # unreachable — _require_verified always raises

    # ---- Field actions ------------------------------------------------------
    def display_order_value(self) -> str:
        return self.page.locator(self.DISPLAY_ORDER_INPUT).input_value()

    def set_display_order(self, value: str) -> "HomeDynamicWidgetsAdminPage":
        self.page.locator(self.DISPLAY_ORDER_INPUT).fill(value)
        return self

    def redirect_url_value(self) -> str:
        return self.page.locator(self.REDIRECT_URL_INPUT).input_value()

    def set_redirect_url(self, value: str) -> "HomeDynamicWidgetsAdminPage":
        self.page.locator(self.REDIRECT_URL_INPUT).fill(value)
        return self

    def is_active(self) -> bool:
        return self.page.locator(self.ACTIVE_STATUS_CHECKBOX).is_checked()

    def set_active(self, active: bool) -> "HomeDynamicWidgetsAdminPage":
        # Native checkbox wrapped in a custom `.custom-control-label` overlay
        # (confirmed live) — the wrapper's set_checkbox()/Playwright's own
        # check()/uncheck() already auto-resolve to the associated label
        # when the input itself is visually hidden, so no manual label-click
        # workaround is needed here (unlike GM Message's custom combobox,
        # which is NOT a native checkbox and has no such auto-resolution).
        self.set_checkbox(self.ACTIVE_STATUS_CHECKBOX, active)
        return self

    def is_open_in_new_tab(self) -> bool:
        return self.page.locator(self.OPEN_IN_NEW_TAB_CHECKBOX).is_checked()

    def set_open_in_new_tab(self, enabled: bool) -> "HomeDynamicWidgetsAdminPage":
        self.set_checkbox(self.OPEN_IN_NEW_TAB_CHECKBOX, enabled)
        return self

    def _uploaded_filename(self, container_selector: str) -> str:
        """The currently-uploaded file's rendered name, or "" if none —
        confirmed live: an uploaded image renders its own filename as a
        second button inside the same ddm-field container, right after
        "Select File" (e.g. "b2b-verified (1) (7).png")."""
        buttons = self.page.locator(f"{container_selector} button").all_inner_texts()
        for text in buttons:
            text = text.strip()
            if text and text != "Select File" and "." in text:
                return text
        return ""

    def widget_image_en_filename(self) -> str:
        return self._uploaded_filename(self.WIDGET_IMAGE_EN_CONTAINER)

    def widget_image_ar_filename(self) -> str:
        return self._uploaded_filename(self.WIDGET_IMAGE_AR_CONTAINER)

    def _close_upload_modal_if_open(self) -> None:
        """Dismiss the Documents-and-Media "Select File" modal left open by
        SELECT_FILE_BUTTON's own click — see UPLOAD_MODAL's docstring. A
        no-op (never raises) when no such modal is showing, so it is safe
        to call unconditionally after every upload.

        HARDENED (2026-08-31, live investigation of a tc_135966 failure,
        this session): the previous version's `count() > 0 and
        close_button.first.is_visible()` probe ran with NO wait at all —
        a snapshot check the instant this method is entered, immediately
        after upload_file() returns. If the modal is still in the middle of
        mounting/animating open at that exact instant (confirmed plausible:
        this is the SAME class of async client-render gap this module's own
        FORM_MOUNT_GRACE_MS already documents elsewhere on this form), that
        one-shot probe can read `is_visible() == False` on a modal that DOES
        exist and WILL become visible moments later — silently skipping the
        close entirely, then leaving that same modal to intercept a LATER
        click. Conversely, the tc_135966 failure this session was the
        opposite symptom (the wait_for(hidden) after a close click timed
        out) — the unconditional 5s hidden-wait below fires even when
        `is_open` genuinely never confirmed the modal was there, and a
        `.first` in an `if` guard can also true/false differently run to
        run under load. Both directions are fixed the same way: PROBE for
        the modal actually being open (bounded wait, not an instant
        snapshot) before doing anything, skip the close+wait branch
        entirely when the probe finds nothing (never opened for this
        upload), and only wait-for-hidden when a close was actually
        attempted — with an Escape-key fallback (same dismissal pattern
        already used by GmMessageAdminPage.select_status() for an
        analogous detached-popup-close race) before giving up loudly rather
        than silently leaving a stale modal in the DOM."""
        # Keyed on the confirmed-live intercepting element itself
        # (`iframe[title="Select File"]` — named directly in Playwright's own
        # trace, see UPLOAD_MODAL's docstring), not on `.first` of the
        # `.liferay-modal.show, .modal.show` class list: a stale/hidden
        # modal node from a PRIOR upload can otherwise sort first in that
        # list and make the open-probe below time out even while a NEW
        # modal (with its own iframe) is genuinely open, silently skipping
        # the close.
        picker_iframe = self.page.locator('iframe[title="Select File"]')
        try:
            picker_iframe.first.wait_for(state="visible", timeout=3000)
        except Exception:
            return  # never opened for this upload -- nothing to close

        close_button = self.page.locator(self.UPLOAD_MODAL_CLOSE_BUTTON)
        if close_button.count() > 0:
            close_button.first.click()

        try:
            picker_iframe.first.wait_for(state="hidden", timeout=8000)
        except Exception:
            self.page.keyboard.press("Escape")
            picker_iframe.first.wait_for(state="hidden", timeout=5000)

    def upload_widget_image_en(self, file_path: str) -> "HomeDynamicWidgetsAdminPage":
        self.page.locator(f"{self.WIDGET_IMAGE_EN_CONTAINER} {self.SELECT_FILE_BUTTON}").click()
        self.upload_file(f"{self.WIDGET_IMAGE_EN_CONTAINER} {self.FILE_INPUT}", file_path)
        # See UPLOAD_MODAL's docstring: the Select-File modal opened by the
        # click above is left in the DOM and intercepts the NEXT field's
        # click (confirmed live) unless dismissed here.
        self._close_upload_modal_if_open()
        return self

    def upload_widget_image_ar(self, file_path: str) -> "HomeDynamicWidgetsAdminPage":
        self.page.locator(f"{self.WIDGET_IMAGE_AR_CONTAINER} {self.SELECT_FILE_BUTTON}").click()
        self.upload_file(f"{self.WIDGET_IMAGE_AR_CONTAINER} {self.FILE_INPUT}", file_path)
        self._close_upload_modal_if_open()
        return self

    def save(self) -> "HomeDynamicWidgetsAdminPage":
        self.click(self.SAVE_BUTTON)
        # See SAVE_COMMIT_GRACE_MS docstring — a disclosed, GM-Message-style
        # grace value, not yet independently re-measured for THIS object
        # (no live Save was exercised during read-only exploration).
        self.page.wait_for_timeout(self.SAVE_COMMIT_GRACE_MS)
        return self

    def cancel(self) -> "HomeDynamicWidgetsAdminPage":
        self.click(self.CANCEL_BUTTON)
        return self

    def is_save_error_shown(self) -> bool:
        body_text = self.page.locator("body").inner_text()
        return self.SAVE_ERROR_BANNER_TEXT in body_text or self.INLINE_REQUIRED_TEXT in body_text

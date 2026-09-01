"""
web/pages/home_strategic_direction/home_strategic_direction_admin_page.py —
HomeStrategicDirectionAdminPage.

Control_Panel Page Object for PBI 129381 ("Strategic Direction Section" /
Pillar Cards, Home Page), backing the "Strategic Pillar Cards" Object
Definition entry (objectDefinitionId=48938, groupId=37246) — CONFIRMED LIVE
this session (2026-08-31, headless Chromium, 1920x1080, TEST_USER), via a
ONE-PROCESS Python probe script driven through this repo's own framework
(BasePage + CmsLoginPage, sync Playwright, no cross-call state) — see the
batch report for why: an earlier attempt to explore this surface through the
Playwright MCP (separate tool calls per action) produced results that could
not be trusted — clicks/hovers that "timed out" in one MCP call were still
dispatched and resolved mid-navigation during the NEXT call, so several
early observations (wrong object definitions, a spurious AR-locale flip, a
"the environment auto-navigates on its own" theory) were artifacts of that
tool boundary, not real site behavior. All facts in this docstring come from
the single-process probe instead, which is the same execution model this
Page Object itself runs under.

CONFIRMED LIVE:
  - Menu path: Product Menu > Content & Data > "Strategic Pillar Cards"
    (role=menuitem, exact text). Like every other Object Definition entry
    on this project, the rendered list URL embeds a per-session portlet
    instance id (this session: ...ObjectDefinitionsPortlet_B5M0...,
    objectDefinitionId=48938) — never hardcode it; always reach the list via
    the menu link's live `href`, never a saved URL string (confirmed: the
    same instance id 404s once the session's login state changes).
  - Like gm_message_admin_page.py's documented locale-persistence bug,
    visiting ANY page under a `/group/...` URL with no `/en/` locale segment
    (e.g. hovering the parent "Content & Data" menu item, which is itself a
    real link, not just a submenu expander) can flip the whole admin chrome
    to Arabic for the rest of the session. Always enter via the explicit
    English-locale home URL (ADMIN_HOME_EN_URL_PATH) before doing anything
    else, exactly like GmMessageAdminPage.open_gm_message_edit_form().
  - List view: a flat data grid, 3 live rows this session — Strategic Pillar
    Cards is a small, fixed REPEATABLE list (Vision / Mission / Objectives),
    not a singleton like GM Message and not an 18-row roster like Board
    Members. Columns confirmed live (`table thead th`): Item Selection, ID,
    Active Status, Display Order, Pillar Description, Pillar Icon, Pillar
    Title, Status (workflow state, e.g. "APPROVED" — NOT a
    Published/Draft toggle, see below), Author, Item Actions. An "Add"
    button (`[data-testid="fdsCreationActionButton"]`, confirmed count 1)
    opens the same field set as editing an existing row.
  - Confirmed live row identities (ID -> Pillar Title -> icon filename):
      49056 -> "Vision"     -> strategic-pillar-vision (1) (7).svg
      49082 -> "Mission"    -> strategic-pillar-mission (1) (7).svg
      49108 -> "Objectives" -> strategic-pillar-objectives (1) (7).svg
    "Mission" (49082) is the TC 135557 target the case names — confirmed by
    reading its live Pillar Title field value ("Mission") after opening its
    edit form, not merely by row/list text (list column values were
    independently cross-checked against the field's own `input_value()`).
  - Edit/Add form fields confirmed live (record 49082, DOM dump via a real
    Playwright session, same class of no-stable-id DDM problem as every
    other Object Definition form on this project):
      Active Status   — checkbox (ddm-field data-field-name="activeStatus")
      Display Order   — text input, id contains "ddm$$displayOrder$"
      Pillar Description — REQUIRED, rich text; renders as
        `[role="textbox"][aria-label="Pillar Description"]` (same
        role-based pattern board_members_admin_page.py's DETAILED_BIOGRAPHY
        already established for this project's rich-text DDM fields — xpath
        does not reliably resolve it, this widget mounts empty/hidden in the
        raw DOM (`style="visibility:hidden"`) until Playwright's role engine
        forces it, matching the shadow/late-mount behavior documented
        there).
      Pillar Icon     — REQUIRED, file upload; a single `Select File`
        button (confirmed unique on this form — no scoping needed) plus the
        already-uploaded filename text next to it.
      Pillar Title    — REQUIRED, text input, id contains
        "ddm$$pillarTitle$" and "inputValue" (same stable-substring
        approach GM Message/Board Members use for fields with the file-
        input-ambiguity problem `_field_after_label()` already documents).
      Save / Cancel   — the only two buttons on the form.
  - Pillar Description and Pillar Title are the only two bilingual fields
    (2 `[data-testid="triggerButton"]` locale toggles confirmed, one inside
    each field's own `div.ddm-field` ancestor) — Active Status, Display
    Order, and Pillar Icon are NOT localizable. Same
    `field_locale_toggle(label)` ancestor-scoping pattern as
    gm_message_admin_page.py (ddm-field container, not raw `following::`,
    which strict-mode-violates across fields on every DDM form probed on
    this project so far).
  - NO Status combobox (`[data-field-reference="publicationStatus"]`
    confirmed absent, count 0), NO Preview button, NO Publish button
    (confirmed absent by direct button-text scan). This Object Definition
    entry editor exposes Save/Cancel only, exactly like
    gm_message_admin_page.py's confirmed scope note for that form — Save
    IS the publish action; "Active Status" (a plain Yes/No field, list
    column confirmed "Yes" for all 3 live rows) is the only visibility
    control this content type has. TC 135556's "Save as draft -> Preview ->
    Publish" is therefore a DISCLOSED SUBSTITUTION, not a literal 3-step
    pipeline: this batch's test performs Save (with Active Status checked)
    and treats the reloaded record / the live public carousel as the
    "preview"/"publish" evidence, the same substitution GM Message's batch
    already established as this project's convention for object-entry
    forms with no separate publish step.
  - Validation, confirmed live by an actual blocked Save (Pillar Title
    cleared on the real Mission record, Save clicked, error text captured,
    then the field was restored and Save clicked again to confirm the
    record still reads "Mission" — no lasting mutation):
      Page-level banner: "This form is invalid. Check field Pillar Title."
        (a trailing numeric token — a timestamp/nonce — follows the field
        name; assertions below match the STABLE PREFIX, not the full
        string with its nonce)
      Inline message: "This field is required." appears twice — once right
        under the empty Pillar Title's own field-feedback, once inside the
        page banner region.
    IMPORTANT — the QA case text for TC 135562 says the expected message is
    "Section Heading (EN) is required." No field named "Section Heading"
    exists anywhere on this form (confirmed by the full field/label
    inventory above) — the real, confirmed-live required EN text field is
    "Pillar Title". This is flagged as a live discrepancy between the case
    text and the real form in the test module's own docstring; the test
    asserts the REAL confirmed strings above, not the case's paraphrase.
  - Save commit grace: reused SAVE_COMMIT_GRACE_MS = 2000 from
    gm_message_admin_page.py's own measured-live constant (same class of
    Liferay object-entry write/read-cache lag documented there). NOT
    independently re-measured for Strategic Pillar Cards this session —
    disclosed reuse of a sibling content type's confirmed value, same as
    board_members_admin_page.py's own reuse pattern for this project.

PUBLIC-SURFACE COUNTERPART: the Home Page's "Our Strategic Direction"
carousel section is CONFIRMED LIVE server-rendered (all 3 `article.qc-sd-
card` nodes present in the initial HTML response, not client-fetched) —
see home_strategic_direction_page.py for the full selector inventory. Cache/
propagation latency for THIS content type was not independently re-measured
this session — cms-profile.md's Publish/Propagation Latency Budget section
is confirmed only for the Board Members data source (a different, JAX-RS-
backed content type); this batch's tests poll the reloaded Home Page with
the SAME conservative timeout/interval cms-profile.md prescribes as a safety
margin, not a literal re-use of the ~0s Board Members figure.
"""

import re

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
PILLAR_CARDS_MENU_ITEM = '[role="menuitem"][data-title="Strategic Pillar Cards"]'
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'


class HomeStrategicDirectionAdminPage(BasePage):
    # ---- List screen --------------------------------------------------------
    ADD_BUTTON = '[data-testid="fdsCreationActionButton"]'
    LIST_ROW = "table tbody tr"
    ROW_ID_LINK = "td.cell-id a"
    # Kebab -> Delete flow — same shape as BoardMembersAdminPage's
    # (confirmed live: this grid also renders an "Item Actions" column,
    # same fdsCreationActionButton toolbar) but NOT independently exercised
    # live this session (time-boxed, mirrors that Page Object's own
    # disclosed-not-verified note for its equivalent constants) — re-verify
    # the exact kebab/menu-item text before first real use if this heals.
    #
    # HEALED (2026-09-01, live one-process probe against qcdev,
    # objectDefinitionId=48938, tc_135556): confirmed live that repeatedly
    # opening this row's kebab (as the real test's own flow does across its
    # main-flow + teardown calls) leaves BEHIND detached-but-still-in-DOM
    # dropdown menu nodes (`#clay-dropdown-menu-N`, one per prior open) —
    # only the just-opened one is actually visible; the rest are
    # `display:none`/hidden leftovers, not removed from the DOM when the
    # menu closes. An unscoped `[role="menuitem"]:text-is("Delete")` (or
    # either of its two fallback alternatives) therefore strict-mode-
    # violates once more than one kebab open has happened in the same
    # session (probe reproduced this exactly: 4 matches, 3 invisible + 1
    # visible, immediately before this fix). Root-caused and fixed with the
    # SAME `:visible` disambiguation pattern already established in
    # gm_message_admin_page.py's switch_field_to_arabic()/
    # switch_field_to_english() for the identical "duplicate detached menu
    # nodes coexist in DOM" shape — scoping each of the 3 fallback
    # selectors to `:visible` deterministically selects the one real open
    # menu's Delete item (probe-confirmed: count drops from 4 to exactly 1
    # with this fix applied, and the subsequent click + confirm actually
    # removed a real QCTEST row end-to-end).
    ROW_ACTIONS_KEBAB = 'button[aria-label="Actions"], button.dropdown-toggle'
    KEBAB_DELETE_MENU_ITEM = (
        '[role="menuitem"]:text-is("Delete"):visible, '
        'li:has-text("Delete") a:visible, '
        'button:has-text("Delete"):visible'
    )
    DELETE_CONFIRM_BUTTON = 'button:has-text("Delete"):visible, button:has-text("Yes"):visible'
    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # ---- Edit/Add form fields — confirmed live 2026-08-31 (see docstring) --
    PILLAR_TITLE = 'input[id*="ddm$$pillarTitle$"][id*="inputValue"]'
    # CONFIRMED LIVE 2026-08-31 (fix): PILLAR_DESCRIPTION is the CKEditor's
    # OUTER, non-editable mount wrapper (`role="textbox"`, stays
    # `visibility:hidden`/empty forever) — it was never the real editable
    # surface, and a previous session's conclusion that the widget "never
    # mounts" was wrong: the wrapper must be CLICKED ONCE to force Liferay
    # to lazily instantiate the classic (iframe-based) CKEditor. Once
    # clicked, a real `<iframe title="editor">` mounts inside this field's
    # own `div.ddm-field[data-field-name="pillarDescription"]` container,
    # and its `<body>` is a genuine `isContentEditable === true` document
    # (re-verified live via a one-process probe: `frame_locator(...)
    # .locator("body")` resolved, read back the real persisted Mission
    # description, and accepted a real keyboard Ctrl+A + type write —
    # never a page.evaluate() bypass). See BasePage.fill_iframe_editor()/
    # .iframe_editor_text() for the shared wrapper methods this uses.
    PILLAR_DESCRIPTION = '[role="textbox"][aria-label="Pillar Description"]'
    PILLAR_DESCRIPTION_FIELD_CONTAINER = 'div.ddm-field[data-field-name="pillarDescription"]'
    PILLAR_DESCRIPTION_EDITOR_IFRAME = f'{PILLAR_DESCRIPTION_FIELD_CONTAINER} iframe[title="editor"]'
    DISPLAY_ORDER = 'input[id*="ddm$$displayOrder$"]'
    ACTIVE_STATUS_CHECKBOX = 'div.ddm-field[data-field-name="activeStatus"] input[type="checkbox"]'
    PILLAR_ICON_SELECT_FILE = 'button:has-text("Select File")'
    PILLAR_ICON_UPLOAD_INPUT = 'input[type="file"]'

    LOCALE_TOGGLE_BUTTON = '[data-testid="triggerButton"]'

    # ---- Not present on this form — confirmed absent, see docstring -------
    STATUS_COMBOBOX = '[data-field-reference="publicationStatus"]'
    PREVIEW_BUTTON = 'button:has-text("Preview")'
    PUBLISH_BUTTON = 'button:has-text("Publish")'

    # See docstring: same measured-live grace GM Message's batch established
    # for this project's object-entry write/read-cache lag, reused rather
    # than independently re-measured for this content type this session.
    SAVE_COMMIT_GRACE_MS = 2000

    ADMIN_HOME_EN_URL_PATH = "/en/home"

    # ---- Navigation -----------------------------------------------------
    def open_pillar_cards_list(self) -> "HomeStrategicDirectionAdminPage":
        """Navigate via Content & Data > Strategic Pillar Cards, always
        entering through the explicit English-locale home URL first (see
        module docstring — a bare `/group/...` navigation, including just
        hovering the parent "Content & Data" menu item, can flip the whole
        admin session to Arabic for the rest of the run). Reads the menu
        item's live `href` rather than a saved URL string, since the
        embedded portlet instance id regenerates every session."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))

        if not self.is_visible(PILLAR_CARDS_MENU_ITEM):
            self.click(PRODUCT_MENU_TOGGLE)
            try:
                self.wait_for(CONTENT_DATA_MENU_ITEM)
            except Exception:
                # CONFIRMED LIVE (2026-08-31): reproduced twice, single-
                # worker, no xdist contention — a SECOND (or later) call to
                # this method within one test (e.g. a teardown/verification
                # re-open after a blocked Save) can have the toggle click
                # land on a menu that fails to open the first time, timing
                # out here even though the exact same click+wait sequence
                # already succeeded once earlier in the same test/session.
                # One retry (re-click the toggle, wait again) mirrors this
                # wrapper's own established click()/wait_for() single-retry
                # recovery convention (overlay/session-drop) rather than
                # inventing a new pattern — surfaced as a real failure only
                # if the retry also fails.
                self.click(PRODUCT_MENU_TOGGLE)
                self.wait_for(CONTENT_DATA_MENU_ITEM)
        href = self.page.locator(PILLAR_CARDS_MENU_ITEM).get_attribute("href")
        self.open(href)
        self.wait_for(f"{self.LIST_ROW} >> nth=0")
        return self

    def open_pillar_card_edit_form_by_title(self, title: str) -> "HomeStrategicDirectionAdminPage":
        """Open the row whose rendered text mentions `title` (e.g.
        "Mission") — confirmed live: :text-is on the row's own ID-link
        avoids ambiguity, so this scopes to the row's text instead and
        clicks that row's ID link."""
        self.click(f'{self.LIST_ROW}:has-text("{title}") >> {self.ROW_ID_LINK}')
        self.wait_for(self.SAVE_BUTTON)
        return self

    def open_new_pillar_card_form(self) -> "HomeStrategicDirectionAdminPage":
        self.click(self.ADD_BUTTON)
        self.wait_for(self.SAVE_BUTTON)
        return self

    def reopen_pillar_card_by_title_fresh(self, title: str) -> "HomeStrategicDirectionAdminPage":
        """Re-navigate to the list fresh, then open the row for `title` —
        used by teardown/verification steps so a re-check never assumes the
        form the test left open is still in a good state (mirrors
        BoardMembersAdminPage.open_member_edit_form_by_row_index_fresh)."""
        self.open_pillar_cards_list()
        return self.open_pillar_card_edit_form_by_title(title)

    # ---- Field actions ------------------------------------------------------
    def fill_pillar_card_form(
        self,
        pillar_title: str = None,
        pillar_description: str = None,
        display_order: str = None,
        active_status: bool = None,
    ) -> "HomeStrategicDirectionAdminPage":
        if pillar_title is not None:
            self.type(self.PILLAR_TITLE, pillar_title)
        if pillar_description is not None:
            # FIXED 2026-08-31 (see PILLAR_DESCRIPTION's own docstring note):
            # click the wrapper once to force the classic CKEditor to mount
            # its iframe, wait for that iframe to render, then write into
            # its real editable body via the shared BasePage wrapper —
            # never a page.evaluate() bypass.
            self.click(self.PILLAR_DESCRIPTION)
            self.wait_for(self.PILLAR_DESCRIPTION_EDITOR_IFRAME)
            self.fill_iframe_editor(self.PILLAR_DESCRIPTION_EDITOR_IFRAME, pillar_description)
        if display_order is not None:
            self.type(self.DISPLAY_ORDER, display_order)
        if active_status is not None:
            self.set_checkbox(self.ACTIVE_STATUS_CHECKBOX, active_status)
        return self

    # CORRECTED 2026-09-01 (live re-investigation via Playwright MCP, human-
    # interaction pass — see test module's own docstring for the full
    # before/after). The PRIOR conclusion that this modal has "no discoverable
    # way to select/attach an uploaded file" was WRONG — an automation gap in
    # THIS method, not a product defect.
    #
    # PILLAR_ICON_SELECT_FILE opens a Liferay Documents-and-Media "Select
    # File" picker MODAL (`iframe[id*="selectAttachmentEntry_iframe"]`), the
    # same class of stay-open modal home_dynamic_widgets_admin_page.py's
    # UPLOAD_MODAL/_close_upload_modal_if_open() already documents. That part
    # was already correctly handled. What was MISSING: after
    # set_input_files() lands a new file, the modal renders an upload PREVIEW
    # panel (thumbnail + filename + "N of N" counter) with its OWN small
    # toolbar containing an "Add" button
    # (`iframe[title="Select File"] >> role=button[name="Add"]`) — CONFIRMED
    # LIVE this session to be the real, human-discoverable confirm control:
    # clicking it is what actually SELECTS the just-uploaded file into the
    # Pillar Icon field and closes the modal (verified: the field afterward
    # shows the real uploaded filename plus Download/Delete buttons, not the
    # empty "Select File" state). The filename text previously seen in a
    # read-only sidebar was a red herring from probing an EXISTING library
    # item's detail panel, not from this preview toolbar.
    #
    # Also confirmed live, as a secondary path: clicking directly on an
    # EXISTING document's row/card in the grid (not its "Preview" button)
    # also selects it and closes the modal immediately — no "Add" click
    # needed for that path. upload_pillar_icon() always uploads a NEW file,
    # so it always goes through the "Add" confirm step.
    PILLAR_ICON_MODAL_IFRAME = 'iframe[id*="selectAttachmentEntry_iframe"]'
    PILLAR_ICON_MODAL_CLOSE_BUTTON = 'button[aria-label="Close"]'
    PILLAR_ICON_MODAL_ADD_BUTTON = 'button:has-text("Add")'
    # CORRECTED 2026-09-01 (live re-investigation, one-process probe — see
    # this method's own docstring note below): the modal's upload surface is
    # a "Drag & Drop Your Files or Browse to Upload" dropzone
    # (`text=Drag & Drop Your Files or Browse to Upload`), CONFIRMED LIVE to
    # have NO static `<input type="file">` anywhere in its DOM (recursive
    # search across every frame on the page found zero matches inside the
    # modal iframe). Clicking the dropzone instead fires a native OS file
    # dialog directly (CONFIRMED via `page.expect_file_chooser()`), so
    # `BasePage.upload_file()` (`locator(...).set_input_files(...)`) can
    # never find a target here — PILLAR_ICON_UPLOAD_INPUT was a wrong
    # assumption, not a wrong selector; there is no such element to select
    # in the first place. The ORIGINAL bug this fixes: the previous code
    # called `set_input_files()` against `input[type="file"]` at page level
    # with no iframe scoping, which silently matched an unrelated file
    # input elsewhere on the host page (confirmed live: page-level count
    # was 1, but 0 inside the modal iframe) and "succeeded" without ever
    # touching the modal — so the preview panel/"Add" button this method
    # waits for next never appeared, and the 15s wait always timed out.
    PILLAR_ICON_MODAL_DROPZONE = "text=Drag & Drop Your Files or Browse to Upload"

    def upload_pillar_icon(self, file_path: str) -> "HomeStrategicDirectionAdminPage":
        self.click(self.PILLAR_ICON_SELECT_FILE)
        modal_iframe = self.page.locator(self.PILLAR_ICON_MODAL_IFRAME)
        modal_iframe.first.wait_for(state="visible", timeout=8000)
        modal_frame = self.page.frame_locator(self.PILLAR_ICON_MODAL_IFRAME)
        dropzone = modal_frame.locator(self.PILLAR_ICON_MODAL_DROPZONE)
        dropzone.wait_for(state="visible", timeout=8000)
        # CONFIRMED LIVE fix: clicking the dropzone opens the browser's
        # native file-chooser dialog (no in-DOM file input to target with
        # set_input_files()) — intercept it with expect_file_chooser() and
        # feed it the fixture path directly, exactly like a human would pick
        # a file from the OS dialog.
        with self.page.expect_file_chooser(timeout=8000) as fc_info:
            dropzone.click()
        fc_info.value.set_files(file_path)
        # CONFIRMED LIVE: the upload preview panel's own "Add" button is the
        # real select/confirm control for a freshly uploaded file — click
        # it, scoped to the modal's own iframe (never the page-level DOM,
        # which has no such button). Same frame_locator idiom as
        # BasePage.fill_iframe_editor()/.iframe_editor_text() rather than
        # `.content_frame` on a Locator, to match this project's convention.
        add_button = modal_frame.locator(self.PILLAR_ICON_MODAL_ADD_BUTTON)
        add_button.first.wait_for(state="visible", timeout=15000)
        add_button.first.click()
        modal_iframe.first.wait_for(state="hidden", timeout=8000)
        return self

    def pillar_title_value(self) -> str:
        return self.page.locator(self.PILLAR_TITLE).input_value()

    def pillar_description_text(self) -> str:
        """Read the PERSISTED Pillar Description (EN) value straight out of
        the portlet's own embedded field-config JSON in the page HTML,
        rather than the rendered rich-text editor DOM.

        CORRECTED 2026-08-31: an earlier session concluded the CKEditor
        "never mounts" for this field. That was a locator bug, not a real
        CMS defect — the wrapper div this constant addresses
        (`PILLAR_DESCRIPTION`, `role="textbox"`) is CONFIRMED LIVE to be
        the CKEditor's outer, permanently-empty/hidden mount POINT, not the
        editable surface itself. Clicking it once forces Liferay to lazily
        instantiate the real classic (iframe-based) CKEditor
        (`<iframe title="editor">`, mounted inside this field's own
        `div.ddm-field[data-field-name="pillarDescription"]` container);
        that iframe's `<body>` IS a genuine `isContentEditable === true`
        document (re-verified live via `frame_locator(...).locator("body")`
        — see `fill_pillar_card_form()` and `BasePage.fill_iframe_editor()`/
        `.iframe_editor_text()`). Writing now goes through that real path.

        This READ method is kept reading the embedded field-config JSON
        rather than the live iframe body on purpose — it is used for
        POST-SAVE verification after a fresh re-open
        (`reopen_pillar_card_by_title_fresh()`), where the persisted value
        already reflects the saved write and the CKEditor may not even be
        mounted yet (no click has happened on that fresh page). This is
        independent of the write-path fix above, not superseded by it.

        The reliable source of truth is the SAME embedded per-field config
        object Liferay renders into the page's own <script> payload to
        bootstrap the (broken) editor — it carries the field's real
        persisted value regardless of whether the editor mounts:
            "fieldReference":"pillarDescription", ... "value":{"en_US":"<p>...</p>", "ar_SA":"..."}
        This was independently verified to match the live public Home
        Page's server-rendered Mission card text exactly. Extracted via
        regex (DDM-specific string surgery, kept out of BasePage on
        purpose) rather than a JSON parse, since the surrounding blob is
        not valid standalone JSON (it's embedded inline in a larger JS
        object literal).
        """
        html = self.page.content()
        match = re.search(
            r'"fieldReference":"pillarDescription".*?"value":\{([^}]*)\}',
            html,
        )
        if not match:
            return ""
        locale_blob = match.group(1)
        en_match = re.search(r'"en_US":"((?:[^"\\]|\\.)*)"', locale_blob)
        if not en_match:
            return ""
        raw = en_match.group(1)
        # Undo the JS-string escaping Liferay applies (\/ -> /, \" -> ", etc.)
        # and strip the wrapping <p>...</p> the editor stores.
        unescaped = raw.encode("utf-8").decode("unicode_escape") if "\\u" in raw else raw
        unescaped = unescaped.replace('\\/', '/').replace('\\"', '"')
        text = re.sub(r"^<p>|</p>$", "", unescaped).strip()
        return text

    def field_locale_toggle(self, field_data_name: str) -> str:
        """The locale toggle button scoped to the field's OWN
        `div.ddm-field[data-field-name=...]` container — same ancestor-
        scoping fix gm_message_admin_page.py's field_locale_toggle()
        documents (an unscoped `following::`/bare selector strict-mode-
        violates across this form's 2 bilingual fields)."""
        return f'div.ddm-field[data-field-name="{field_data_name}"] {self.LOCALE_TOGGLE_BUTTON}'

    def save(self) -> "HomeStrategicDirectionAdminPage":
        self.click(self.SAVE_BUTTON)
        self.page.wait_for_timeout(self.SAVE_COMMIT_GRACE_MS)
        return self

    def cancel(self) -> "HomeStrategicDirectionAdminPage":
        self.click(self.CANCEL_BUTTON)
        return self

    # ---- State queries --------------------------------------------------------
    # Confirmed live text this session (see docstring) — same signal shape
    # as gm_message_admin_page.py / board_members_admin_page.py.
    SAVE_ERROR_BANNER_PREFIX = "This form is invalid. Check field Pillar Title."
    INLINE_REQUIRED_TEXT = "This field is required."

    def is_save_error_shown(self) -> bool:
        body_text = self.page.locator("body").inner_text()
        return self.SAVE_ERROR_BANNER_PREFIX in body_text or self.INLINE_REQUIRED_TEXT in body_text

    def save_error_text(self) -> str:
        body_text = self.page.locator("body").inner_text()
        idx = body_text.find(self.SAVE_ERROR_BANNER_PREFIX)
        if idx == -1:
            idx = body_text.find(self.INLINE_REQUIRED_TEXT)
        return body_text[idx: idx + 120] if idx != -1 else ""

    def has_status_combobox(self) -> bool:
        """Confirmed absent this session (see docstring) — kept as a live
        state query rather than a hardcoded False so a future re-probe
        (e.g. after a CMS upgrade adds a real Publish pipeline) is
        detectable instead of silently stale."""
        return self.page.locator(self.STATUS_COMBOBOX).count() > 0

    def row_visible(self, title: str) -> bool:
        return self.is_visible(f'{self.LIST_ROW}:has-text("{title}")')

    def delete_pillar_card_by_title(self, title: str) -> "HomeStrategicDirectionAdminPage":
        """QCTEST- disposable-record cleanup path (cms-profile.md Test-Data
        Policy) — mirrors BoardMembersAdminPage.delete_member_by_name().

        CONFIRMED LIVE end-to-end (2026-09-01, one-process probe against
        qcdev, objectDefinitionId=48938): opened a real QCTEST row's kebab,
        clicked Delete via the now-`:visible`-scoped KEBAB_DELETE_MENU_ITEM
        (see that constant's own docstring for the stale-dropdown root
        cause and fix), confirmed the delete dialog, and re-verified via a
        fresh `open_pillar_cards_list()` that the row was actually gone
        from the list afterward — not just that the click resolved."""
        row = f'{self.LIST_ROW}:has-text("{title}")'
        self.click(f"{row} >> {self.ROW_ACTIONS_KEBAB}")
        self.click(self.KEBAB_DELETE_MENU_ITEM)
        if self.is_visible(self.DELETE_CONFIRM_BUTTON):
            self.click(self.DELETE_CONFIRM_BUTTON)
        return self

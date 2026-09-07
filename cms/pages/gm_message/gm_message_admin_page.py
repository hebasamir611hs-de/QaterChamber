"""
web/pages/gm_message/gm_message_admin_page.py — GmMessageAdminPage.

Control_Panel Page Object for PBI 129397 (QC-ABOUT-005 — General Manager's
Message), backing the "General Manager Messages" Object Definition entry
that drives the public /web/qatar-chamber/about-us/general-managers-message
page (see gm_message_page.py for the public-frontend counterpart).

REAL, LIVE-VERIFIED FACTS (this session, 2026-08-31, headless Chromium
against qcdev, authenticated via CmsLoginPage / TEST_USER — the earlier
"CMS login blocked" state recorded in test_gm_message_control_panel.py's
module docstring is RESOLVED; see that module's updated note):

  - The earlier session's "developer mode connection limit" / stuck-login
    block was NOT a login-form or credential problem. It was the site-wide
    announcement modal (`#qc-announcement-popup-root`, close button
    `.qc-ann-close`) intercepting the Sign-In button click in a raw
    (non-framework) probe script. `core/web/overlays.py` +
    `core/web/base_page.py` already dismiss this overlay on every
    `BasePage.open()` — going through the real framework (CmsLoginPage +
    BasePage, not a bare Playwright script) logs in cleanly with no
    workaround needed. Confirmed live: TEST_USER/TEST_PASSWORD reach the
    admin Home screen with the Control Menu + Product Menu both present.
  - Navigation path: Product Menu (`[data-qa-id="productMenu"]`) ->
    Content & Data (`[role="menuitem"]:text-is("Content & Data")`) ->
    "General Manager Messages" (`[role="menuitem"]:text-is("General
    Manager Messages")`) — a real, distinct Object Definition menu entry
    (objectDefinitionId=79727), separate from the public-facing Page
    Object's concerns. Its href embeds a portlet INSTANCE id
    (`ObjectDefinitionsPortlet_P0K8` this session) that regenerates per
    session — same regeneration behavior already documented in
    org_structure_admin_page.py's LIST_URL note. GM_MESSAGES_LIST_URL
    below is kept only as a documented artifact of the confirmed shape,
    NOT navigated to directly — always reach the list via the menu.
  - The list is a flat single-row grid: exactly ONE live record (ID 79878)
    — GM's Message is a SINGLETON content type, not a repeatable list like
    Departments/Board Members. There is a "New" button in the toolbar, but
    creating a second entry would be semantically wrong for a page whose
    public template renders "the" GM's Message, not a collection — this
    Page Object therefore always edits the existing singleton record via
    its row's ID-cell link (ROW_ID_LINK), which opens the same editable
    `edit_object_entry` form (Save/Cancel) directly. (HEALED 2026-08-31:
    the row previously used a kebab ("<ID> Actions") -> "View" two-step
    flow; that kebab button is still a real, resolvable element on a warm
    grid, but timed out live in a fresh pytest run — see ROW_ID_LINK's own
    docstring for the live re-probe and the more robust one-click
    replacement.)
  - Confirmed live field labels/order on the edit form (exact visible
    text, DOM-probed): GM Designation*, GM Name*, GM Portrait Image*,
    Hero Banner*, Image Alt Text*, Page Content* (rich-text/CKEditor
    widget), Page Title*, Status* (Published/Draft — this IS the
    publish/unpublish control; there is no separate "Publish" button),
    Salutation Heading*, Signature Avatar (optional), Signature Closing
    Text*.
  - Like org_structure_admin_page.py's Departments form, none of the
    visible text inputs carry a stable id/name/for-label — the only
    mechanism that resolved reliably is the same text-anchored
    "label -> nearest following input" xpath pattern (`_field_after_label`
    below, copied verbatim from that precedent). Each field's raw DOM id
    DOES exist (e.g. `..._ddm$$gmName$<8-char-random>$0$$en_USinputValue`)
    but embeds BOTH the regenerating portlet instance id AND a per-field
    random token that changed observably between two navigations in this
    same session — unusable as a stable selector.
  - Per-field bilingual entry: each localizable field has its OWN small
    flag/locale toggle button immediately after it (confirmed live: 7 such
    buttons on this form, one per localizable field — GM Designation, GM
    Name, Image Alt Text, Page Content, Page Title, Salutation Heading,
    Signature Closing Text — NOT Status, which is locale-independent).
    Clicking it opens a language picker; the confirmed live Arabic entry
    is "العربية (المملكة العربية السعودية)" (ar-SA, marked "TRANSLATED"
    — an AR value already exists for every field), matching
    cms-profile.md's declared `ar_SA` locale. Selecting it swaps the SAME
    input to show/accept the Arabic value — there is no separate AR-only
    input to locate.
  - No dedicated "Preview" action was found on this form (Save/Cancel are
    the only two buttons) — the Object Definition entry editor does not
    expose a Draft/Preview/Publish pipeline distinct from
    Save-with-Status-field, unlike a typical Liferay Web Content article.
    This is a disclosed, confirmed-live scope note (not a locator gap):
    `open_edit_form()` / `save()` are the only lifecycle actions available;
    the test built on this Page Object substitutes "reload the saved
    record and read the field values back" for a literal Preview click,
    same disclosed-substitution pattern already used elsewhere in this
    module family (see gm_message_page.py / org_structure_admin_page.py
    docstrings for precedent).
  - SUCCESS_TOAST is an explicit, disclosed UNVERIFIED placeholder: a live
    Save was not exercised by this exploration (a destructive write
    against the shared qcdev singleton record was correctly blocked by
    this session's own safety tooling before any mutation occurred) — no
    real toast/notification selector could be confirmed. Do NOT invent one;
    `is_save_error_shown()` (the negative/no-error signal, safe to confirm
    without a live save since it is pure absence-checking) is used instead
    wherever the test needs the "no validation error" half of the
    guarantee, and SUCCESS_TOAST is gated behind `_require_verified()`
    exactly like org_structure_admin_page.py's own unresolved placeholders.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

GM_MESSAGES_LIST_URL = control_panel_url(
    "/group/qatar-chamber/~/control_panel/manage"
    "?p_p_id=com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_P0K8"
    "&p_p_lifecycle=0&p_p_state=maximized&p_v_l_s_g_id=37246"
    "&_com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_P0K8_objectDefinitionId=79727"
)
GM_MESSAGE_RECORD_ID = "79878"  # the one live singleton record

_UNVERIFIED = "TODO: confirm against a real Save this batch could not safely trigger"

# Confirmed live locale picker entry (ar-SA — matches cms-profile.md's declared AR locale).
ARABIC_LOCALE_LABEL = "العربية (المملكة العربية السعودية)"
ENGLISH_LOCALE_LABEL = "English (United States)"


def _field_after_label(label: str, tag: str = "input") -> str:
    """Text-anchored locator: the {tag} nearest AFTER the exact visible label
    text — copied verbatim from org_structure_admin_page.py's precedent (this
    DDM-rendered form has the identical no-stable-id problem).

    The default `tag="input"` is scoped to `input[@type="text"]` — a bare
    `following::input[1]` is ambiguous on this form: it can resolve to an
    unrelated `type="file"` upload input that happens to follow the same
    label text in DOM order (confirmed live for GM Name, see GM_NAME below
    and the module docstring). Callers that explicitly pass a non-default
    tag (e.g. "button", "select", a contenteditable selector) are
    unaffected.

    A SECOND, independently-confirmed-live ambiguity: the exact label text
    (e.g. "Salutation Heading") matches more than one element in this DDM
    form's DOM (an accessibility/responsive-layout duplicate), so
    `//*[text()=label]` itself yields multiple context nodes — each then
    contributes its own "nearest following input[1]", producing a strict-
    mode violation across DIFFERENT fields' inputs (confirmed live: a
    Salutation Heading query resolved to both the real Salutation input and
    the Signature Closing Text input). The whole expression is wrapped in
    `(...)[1]` to deterministically collapse to the first-in-document-order
    match, which is the field's own real input in every case observed live
    this session."""
    if tag == "input":
        tag = 'input[@type="text"]'
    return f'xpath=(//*[normalize-space(text())="{label}"]/following::{tag}[1])[1]'


def _text_input_by_id_substring(*substrings: str) -> str:
    """A DDM text input matched by stable id SUBSTRING(S) rather than
    document-order proximity to a label. Confirmed live (this session,
    strict-mode violation dump) that a Liferay DDM text field's rendered id
    contains the field's internal name plus an "inputValue" suffix, e.g.
    "..._ddm$$gmName$RNJv2u0q$0$$en_USinputValue" — the embedded portlet
    instance id and per-field random token both regenerate per session, but
    the "ddm$$<fieldName>" and "inputValue" substrings are stable. Use this
    (not `_field_after_label`) for any field whose plain label-proximity
    locator was proven ambiguous against a live file-upload input."""
    conditions = " and ".join(f'contains(@id, "{s}")' for s in substrings)
    return f'xpath=//input[@type="text" and {conditions}]'


class GmMessageAdminPage(BasePage):
    # ---- Menu navigation ----------------------------------------------------
    PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
    CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
    GM_MESSAGES_MENU_ITEM = '[role="menuitem"]:text-is("General Manager Messages")'

    # ---- List screen ------------------------------------------------------
    LIST_ROW = "table tbody tr"
    # HEALED (2026-08-31, live re-probe against qcdev, this session): the
    # previous ROW_ACTIONS_BUTTON ("<ID> Actions" kebab) -> ROW_VIEW_MENU_ITEM
    # ("View") two-step flow timed out live in a fresh pytest run
    # (tc_135453) even though the kebab button locator itself still
    # resolves correctly when the grid is warm/already rendered — this is
    # consistent with Liferay's per-user "Manage Columns Visibility" toggle
    # on this grid (confirmed present live: a `button "Manage Columns
    # Visibility"` sits in the same "Item Actions" column header) hiding the
    # Actions column for whichever session state produced the failure,
    # while the ID column can't be hidden that way. Re-probed live and
    # found a SIMPLER, more robust entry point that was there all along:
    # the record's own ID cell is a real link straight into the same
    # `edit_object_entry` form the kebab -> View flow opened (confirmed
    # live: clicking it landed on the identical URL, same
    # externalReferenceCode=QCDEMO-129397-general-managers-message, with
    # GM_NAME visible right after) — one click, no menu/flyout timing
    # dependency, no dependency on the Actions column being visible.
    # `:text-is` (not `:has-text`) deliberately avoids substring collisions
    # on a numeric ID. Confirmed unique (count 1) live this session.
    ROW_ID_LINK = f'table tbody a:text-is("{GM_MESSAGE_RECORD_ID}")'
    # HEALED (2026-08-31, live investigation against qcdev, tc_135457
    # SECOND reopen inside one test's `finally` block, real pytest run):
    # timed out waiting on ROW_ID_LINK at the wrapper's bare 10s default,
    # then cascaded into BasePage.wait_for()'s own recovery path calling
    # session_guard.reauthenticate() -> page.goto(target_url) with no
    # explicit timeout (Playwright's 30s default), which then ALSO timed
    # out. Confirmed root cause live this session by timing this exact
    # menu-click -> grid-render path directly against qcdev, cold, 4 back-
    # to-back runs with no Save involved at all: 8180ms / 6759ms / 7993ms /
    # 7554ms just to render ROW_ID_LINK after clicking "General Manager
    # Messages" — this grid's render latency alone regularly eats 65-80% of
    # the wrapper's 10s default with ZERO margin for qcdev's own documented
    # ~30s session-drop jitter (session_guard.py) or any additional post-
    # Save reflow. This is the SAME class of confirmed-live, measured read-
    # side/render latency already documented for GM_NAME_RELOAD_TIMEOUT_MS
    # below (a longer timeout on this ONE wait, not a locator change, not a
    # retry loop) — not a session-drop symptom, so widening this timeout
    # (rather than touching session_guard.py) is the correct fix. A
    # dedicated 3-reopen save->reopen->save->reopen sequence run live
    # against this same record (record 79878, Salutation Heading edited
    # then restored) with this timeout applied completed all 3 reopens
    # reliably (1739ms/2841ms/1796ms observed that run — well within
    # budget, confirming the margin holds even when render latency happens
    # to be fast, and covers the slow-render case measured above).
    ROW_ID_LINK_RELOAD_TIMEOUT_MS = 20000

    # ---- Edit form fields (label-anchored, see docstring) ------------------
    GM_DESIGNATION = _field_after_label("GM Designation")
    # Confirmed-live ambiguity fix: a plain "following::input[1]" after the
    # "GM Name" label strict-mode-matched TWO elements (the real text input
    # AND an unrelated type="file" upload input following the same label in
    # DOM order) — see module docstring. Matched by stable id substring
    # instead of document-order proximity.
    GM_NAME = _text_input_by_id_substring("ddm$$gmName", "inputValue")
    GM_PORTRAIT_SELECT_FILE = _field_after_label("GM Portrait Image", "button")
    HERO_BANNER_SELECT_FILE = _field_after_label("Hero Banner", "button")
    IMAGE_ALT_TEXT = _field_after_label("Image Alt Text")
    PAGE_CONTENT_EDITOR = _field_after_label("Page Content", '[contenteditable="true"]')
    PAGE_TITLE = _field_after_label("Page Title")
    # Status is NOT a native <select> — confirmed live (2026-08-31 re-run):
    # Liferay renders it as a custom combobox widget: a
    # `button[role="combobox"]` trigger inside a
    # `[data-field-reference="publicationStatus"]` container, a
    # `input[type="hidden"]` that carries the raw persisted value, and a
    # `[role="listbox"]` popup (rendered detached from the field container,
    # appended near the end of <body> like the other Liferay dropdown
    # popups on this form) holding `[role="option"]` entries when open. The
    # `select_option()`/`input_value()` native-<select> API does not apply;
    # see status_value()/select_status() below for the click-open ->
    # click-option / read-button-text interaction model this requires.
    STATUS_FIELD_CONTAINER = '[data-field-reference="publicationStatus"]'
    STATUS_COMBOBOX_BUTTON = f'{STATUS_FIELD_CONTAINER} button[role="combobox"]'
    STATUS_HIDDEN_INPUT = f'{STATUS_FIELD_CONTAINER} input[type="hidden"]'
    STATUS_LISTBOX = '[role="listbox"]'
    STATUS_OPTION = '[role="listbox"] [role="option"]'
    # Confirmed-live ambiguity fix (this session's re-run): the label-
    # proximity query for "Salutation Heading" strict-mode-matched BOTH the
    # real Salutation input and the Signature Closing Text input (the
    # "Salutation Heading" label text itself has a duplicate DOM node — see
    # _field_after_label's docstring). Matched by stable id substring
    # instead.
    SALUTATION_HEADING = _text_input_by_id_substring("ddm$$salutationHeading", "inputValue")
    SIGNATURE_AVATAR_SELECT_FILE = _field_after_label("Signature Avatar", "button")
    SIGNATURE_CLOSING_TEXT = _text_input_by_id_substring("ddm$$signatureClosingText", "inputValue")

    # ---- Per-field locale toggle (confirmed live, see docstring) -----------
    # HEALED (2026-08-31, live re-probe against qcdev, tc_135453 fresh
    # pytest run): the previous value `'button.dropdown-toggle'` was CSS
    # class-selector syntax embedded as an XPath `following::` step — XPath
    # has no dot/class-selector notation, so `following::button.dropdown-
    # toggle[1]` was interpreted as a (nonexistent) element literally named
    # "button.dropdown-toggle" and never matched anything, hence the 30s
    # timeout. Confirmed live (DOM dump, GM Name field): the real toggle is
    # `<button class="dropdown-toggle btn btn-monospaced btn-secondary" ...
    # data-testid="triggerButton">` — one per localizable field, sitting
    # immediately after the field's input in DOM order, same as before.
    # Expressed as a valid XPath predicate on @class instead.
    _LOCALE_TOGGLE_TAG = 'button[contains(concat(" ", normalize-space(@class), " "), " dropdown-toggle ")]'

    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # ---- Not confirmed this session — explicit placeholder, never guessed --
    SUCCESS_TOAST = _UNVERIFIED

    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"GmMessageAdminPage.{name} is an unverified placeholder — a "
                f"real Save must be observed live and the resulting "
                f"toast/notification locator confirmed before this is relied on."
            )

    # ---- Navigation -----------------------------------------------------
    # HEALED (2026-08-31, live investigation against qcdev record 79878,
    # tc_135453 fresh pytest run): the reopen right after save() timed out
    # at `wait_for(GM_NAME)` — 10s, the wrapper's default. First ruled out a
    # locator-multiplicity bug: live `document.querySelectorAll` on GM_NAME's
    # own id predicate returned exactly 1 match in every state probed (fresh
    # EN open, after switching to AR, immediately after a post-save reopen)
    # — GM_NAME is ONE shared input reused across locales, not a per-locale
    # duplicate, so this is NOT the same class of strict-mode trap as
    # STATUS_LISTBOX/Salutation Heading elsewhere in this module.
    # Confirmed root cause instead, by polling the SAME field's match count
    # every 150ms right after clicking Save with no wait in between: Save
    # triggers an in-place DOM reflow of this edit form (URL query-param
    # order visibly changes mid-poll) during which GM_NAME's input is
    # REMOVED from the DOM for a measured window (observed live: absent at
    # t=1.28-1.47s post-click, present again by t=1.65s) before being
    # re-inserted — not a full page navigation, a live re-render. This lines
    # up with SAVE_COMMIT_GRACE_MS's own confirmed 2000ms grace (this
    # reflow normally finishes within it), but under the real pytest run's
    # heavier concurrent load, environment latency, or a slightly later-
    # firing reflow, a subsequent reopen can arrive while GM_NAME is still
    # torn down and then outlast the wrapper's bare 10s wait_for default.
    # A longer timeout on this ONE wait (not a locator change, not a retry
    # loop) is the correct, evidence-backed fix for this measured, real
    # transient — ROW_ID_LINK and the menu path were re-verified correct
    # and were not touched.
    GM_NAME_RELOAD_TIMEOUT_MS = 20000

    # HEALED (2026-08-31, live investigation against qcdev, tc_135453 teardown
    # failure): the teardown's reopen — the FIRST call to this method after
    # the test has visited the PUBLIC gm_message page for BOTH EN and AR
    # verification (gm_page.open_gm_message("ar")) — timed out at
    # `wait_for(CONTENT_DATA_MENU_ITEM)` after clicking PRODUCT_MENU_TOGGLE.
    # Confirmed root cause live: visiting the AR-locale public page
    # (/ar/web/...) sets a session-level Liferay locale that PERSISTS into
    # subsequent control-panel navigation — even hitting the plain,
    # locale-less `control_panel_url("/home")` afterward redirects to
    # `/ar/home` and renders the ENTIRE admin Product Menu (including the
    # "Content & Data" / "General Manager Messages" menu items this Page
    # Object's locators are text-anchored on) in Arabic. The English-text
    # locators then never match, so `wait_for(CONTENT_DATA_MENU_ITEM)`
    # legitimately times out — not a timing/reflow issue like GM_NAME's, a
    # genuine locale-mismatch: the element the wrapper is waiting for
    # literally never renders in English while the session stays AR.
    # Reproduced and fixed live: forcing the English locale segment
    # (`/en/home`, confirmed live to render "Content & Data" etc. in English
    # regardless of the session's last-visited public-page locale) before
    # doing anything else makes the SAME menu path succeed reliably,
    # independent of whatever page/locale was open immediately prior. This
    # is now the entry point for EVERY call to this method (main-flow opens
    # and the teardown reopen alike), not just a teardown-only branch, so
    # the admin form reliably reopens regardless of prior AR-page
    # navigation.
    ADMIN_HOME_EN_URL_PATH = "/en/home"

    def open_gm_message_edit_form(self) -> "GmMessageAdminPage":
        """Navigate via Content & Data > General Manager Messages, then open
        the singleton record's edit form via its row kebab -> View. Mirrors
        OrgStructureAdminPage.open_departments_list()'s re-login-if-needed
        pattern (same qcdev session-drop risk documented there). Always
        enters via the explicit English-locale home URL (see
        ADMIN_HOME_EN_URL_PATH docstring) so this reliably reopens the admin
        form regardless of what page/locale was open immediately before —
        specifically, regardless of the calling test having just visited the
        AR-locale public gm_message page."""
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
        self.click(self.GM_MESSAGES_MENU_ITEM)
        # See ROW_ID_LINK_RELOAD_TIMEOUT_MS docstring: this grid's own
        # render latency (confirmed live, cold, with no Save involved at
        # all) regularly consumes most of the wrapper's bare 10s default —
        # a second/third reopen within one test (right after a Save's own
        # reflow) has essentially no margin left at that default.
        self.wait_for(self.ROW_ID_LINK, timeout=self.ROW_ID_LINK_RELOAD_TIMEOUT_MS)

        self.click(self.ROW_ID_LINK)
        # See GM_NAME_RELOAD_TIMEOUT_MS docstring: a reopen right after
        # save() needs longer than the wrapper's 10s default for the DDM
        # form to render off the (confirmed-live-lagging) read-side path.
        self.wait_for(self.GM_NAME, timeout=self.GM_NAME_RELOAD_TIMEOUT_MS)
        return self

    # ---- Field actions ------------------------------------------------------
    def fill_text_field(self, field_locator: str, value: str) -> "GmMessageAdminPage":
        self.type(field_locator, value)
        return self

    def field_value(self, field_locator: str) -> str:
        return self.page.locator(field_locator).input_value()

    def field_locale_toggle(self, label: str) -> str:
        """The locale/flag toggle button for the field under `label` — a
        SEPARATE xpath anchored on the same label text, not a suffix
        appended to _field_after_label()'s own xpath (that expression
        already terminates at `following::input[1]`; xpath does not support
        chaining another axis step onto a completed expression string).

        HEALED 2026-08-31: the prior `following::` axis was unscoped and
        matched dropdown-toggle buttons belonging to LATER fields too (e.g.
        GM Name's `[1]` picked up GM Designation's own toggle, since
        `following::` walks the whole document from the label, not just
        GM Name's own field) — a strict-mode violation (2 matches) on a
        fresh live run. Live-probed on qcdev (record 79878): every
        localizable field renders inside its OWN `div.ddm-field` container
        (`data-field-name="gmName"` etc.), and each such container holds
        EXACTLY ONE `button.dropdown-toggle`. Scoping the search to the
        nearest `ddm-field` ancestor of the label, then searching only
        WITHIN that container, confirmed live to resolve to exactly 1
        element for every bilingual field on this form (GM Designation, GM
        Name, Image Alt Text, Page Content, Page Title, Salutation Heading,
        Signature Closing Text)."""
        return (
            f'xpath=//*[normalize-space(text())="{label}"]'
            '/ancestor::div[contains(concat(" ", normalize-space(@class), " "), " ddm-field ")][1]'
            f'//{self._LOCALE_TOGGLE_TAG}'
        )

    def switch_field_to_arabic(self, label: str) -> "GmMessageAdminPage":
        """Click the given field's own locale toggle (the nearest
        dropdown-toggle button following its label) and select the
        confirmed-live Arabic (ar-SA) entry — the SAME input then shows/
        accepts the AR value (see docstring: one input per field, not
        one-per-locale)."""
        self.click(self.field_locale_toggle(label))
        # Confirmed live (2026-08-31 heal, same session as the toggle fix
        # above): each field's locale-picker menu is its OWN detached DOM
        # node — all 7 fields' "العربية..." menuitem buttons share IDENTICAL
        # text and are present in the DOM simultaneously (strict-mode
        # violation on 7 matches), but only the just-opened field's menu is
        # actually visible; the other 6 are display:none. `:visible`
        # deterministically selects the one real open menu's item.
        self.click(f'[role="menuitem"]:has-text("{ARABIC_LOCALE_LABEL}"):visible')
        return self

    def switch_field_to_english(self, label: str) -> "GmMessageAdminPage":
        """Click the given field's own locale toggle and select the
        English (en-US) entry — same `:visible` disambiguation as
        switch_field_to_arabic, since all 7 fields' EN menuitem buttons
        also coexist in the DOM with only the just-opened one visible
        (confirmed live 2026-08-31: raw `[role="menuitem"]:has-text("English
        (United States)")` alone strict-mode-violates with 7 matches)."""
        self.click(self.field_locale_toggle(label))
        self.click(f'[role="menuitem"]:has-text("{ENGLISH_LOCALE_LABEL}"):visible')
        return self

    def page_content_text(self) -> str:
        return self.text(self.PAGE_CONTENT_EDITOR)

    def select_status(self, label: str) -> "GmMessageAdminPage":
        """Open the Status combobox and click the matching option — custom
        widget, not a native <select>; select_option() does not apply here
        (see STATUS_COMBOBOX_BUTTON's docstring).

        HEALED (2026-08-31, live investigation against qcdev record 79878,
        tc_135453): confirmed live that clicking the option alone leaves
        STATUS_LISTBOX still open/visible in the DOM — this custom popup
        does not close synchronously with the option click. An immediately
        following Save click (as the calling test does) then lands while
        the popup is still up: its own outside-click-to-dismiss handler
        consumes that click to close the popup instead of letting it reach
        the Save button underneath, so Save silently no-ops — confirmed
        live via network capture: NO PUT request fires at all, and
        is_save_error_shown() reports no error (there is nothing to
        validate — the form was never submitted), so the record silently
        keeps its previous persisted value with no visible failure at the
        Save step itself. Waiting here for STATUS_LISTBOX to close before
        returning guarantees any subsequent click (Save or otherwise) lands
        on the real form, not the closing popup.

        `.first` (not a bare `self.wait_for(self.STATUS_LISTBOX, state=
        "hidden")`) is deliberate: confirmed live that after a field's
        locale-picker menu has already been opened earlier in the same
        form session (switch_field_to_arabic/english), more than one
        `[role="listbox"]` node can coexist detached in the DOM (the exact
        same multi-node pattern already documented for the locale toggle's
        own menu — see field_locale_toggle's docstring) — a plain strict-
        mode `wait_for` on STATUS_LISTBOX then raises TimeoutError
        (Playwright's strict mode rejects a >1 match) instead of ever
        observing the close. `.first` targets whichever instance is
        actually the one just opened/closed, matching the same
        disambiguation approach used elsewhere on this form."""
        # HARDENED further (2026-08-31, live investigation of a tc_135457
        # Draft->Published restore failure, this session): the ORIGINAL
        # single-attempt sequence below (open -> click option -> wait/Escape
        # -> read back) was confirmed live, via one direct DOM-interaction
        # replay against this SAME record (79878), to complete correctly —
        # click the combobox, click "Published", the listbox count drops to
        # 0 immediately, and the button's own text updates to "Published"
        # with no Escape fallback needed on that replay. That rules out the
        # option value/selector itself being wrong for Published
        # specifically (the earlier Published->Draft direction and this
        # Draft->Published direction use the identical selector shape). The
        # failure inside the real pytest run therefore matches this
        # method's own already-documented class of transient (heavier
        # concurrent load/latency racing the click against the popup's own
        # close animation) — NOT a logic bug in which option gets clicked.
        # Rather than let one such race raise straight out of a teardown
        # (silently leaving the record on the WRONG status with no further
        # recourse, as happened this session), the full open->click->verify
        # attempt is now retried exactly ONCE before raising — still
        # bounded, still not a blind retry loop, but no longer a
        # single-shot gamble on a measured-live, real transient in a path
        # whose failure mode is "shared singleton record left mutated."
        #
        # Idempotent short-circuit: if the combobox already shows `label`
        # (e.g. a caller re-asserting a status that's already correct),
        # skip opening the popup entirely — nothing to select.
        if self.status_value() == label:
            return self
        last_actual = None
        for attempt in range(2):
            last_actual = self._select_status_attempt(label)
            if last_actual == label:
                return self
        # REVERTED the previous "nuclear reopen" fallback (2026-08-31,
        # SECOND investigation this session, live root-cause confirmed
        # against record 79878's tc_135457 teardown failure): that fallback
        # called `self.open_gm_message_edit_form()` here — a FULL
        # navigation away from and back into the edit form. Any unsaved
        # edit a caller made to OTHER fields earlier in the same form
        # session (e.g. the teardown's own
        # `fill_text_field(SALUTATION_HEADING, baseline)` called
        # immediately before `select_status()`) is silently discarded by
        # that reopen, because the reopen re-renders the form from the
        # server's last-SAVED state, not the in-browser unsaved state.
        # Confirmed live: this is EXACTLY what happened to record 79878 —
        # the teardown's Salutation Heading restore was typed, this
        # fallback's reopen fired and discarded it, and the subsequent
        # save() persisted the OLD (still-QCTEST) salutation alongside the
        # correctly-selected Status, leaving the shared singleton mutated
        # with no visible failure until the next-run's post-save re-read
        # caught it. A method that can silently roll back its caller's
        # other pending field edits is itself the defect — raising here
        # (still bounded: two in-place attempts, no reopen, no retry loop)
        # is now the only way this method fails: loudly, with the record's
        # pending edits still intact in the DOM for the caller to see/save
        # or explicitly abandon, never silently discarded underneath it.
        raise RuntimeError(
            f"select_status({label!r}) did not take: combobox still shows "
            f"{last_actual!r} after two in-place open+click+popup-close "
            f"attempts. Refusing to fall back to a full page reload here — "
            f"that would silently discard any OTHER unsaved field edits the "
            f"caller made earlier in this same form session (confirmed live "
            f"root cause of the 2026-08-31 record-79878 teardown data-"
            f"integrity incident). Callers needing a fresh-render retry must "
            f"call open_gm_message_edit_form() themselves, save deliberately, "
            f"and re-apply their own field edits afterward."
        )

    def _select_status_attempt(self, label: str) -> str:
        """One open+click-option+wait-for-popup-close+read-back cycle — the
        body of the original single-attempt sequence, factored out so
        select_status() can call it both for its two in-place retries and
        for the post-reload final attempt without duplicating the sequence
        a third time. Returns the combobox's displayed label AFTER the
        cycle (== `label` on success, whatever it actually shows otherwise)
        — select_status() itself decides whether that counts as success and
        whether/how to retry; this helper never raises on a mismatch."""
        # Re-entry guard: if a PRIOR attempt's own popup is still open/
        # visible (its close raced and lost), a fresh click on
        # STATUS_COMBOBOX_BUTTON would TOGGLE it CLOSED instead of opening
        # it (it is a toggle button), so the very next
        # `wait_for(STATUS_LISTBOX)` would then wait on a popup that was
        # just dismissed by this same click. Force-close any leftover popup
        # with Escape first so every attempt starts from the same known
        # "closed" state before opening its own.
        if self.page.locator(self.STATUS_LISTBOX).count() > 0:
            self.page.keyboard.press("Escape")
            try:
                self.page.locator(self.STATUS_LISTBOX).first.wait_for(state="hidden", timeout=3000)
            except Exception:
                pass
        self.click(self.STATUS_COMBOBOX_BUTTON)
        self.wait_for(self.STATUS_LISTBOX)
        # `.first` (via ` >> nth=0`): confirmed live (see
        # field_locale_toggle's docstring) that more than one
        # `[role="listbox"]` node can coexist detached in the DOM once
        # any field's locale-picker menu has been opened earlier in the
        # same form session — a bare (unscoped) click on STATUS_OPTION
        # would then strict-mode-violate instead of deterministically
        # landing on the just-opened instance.
        self.click(f'{self.STATUS_OPTION}:has-text("{label}") >> nth=0')
        # HARDENED (2026-08-31, live investigation of a tc_135457
        # teardown failure, this session): the bare `.first.wait_for(
        # hidden, timeout=10000)` below is a confirmed-live, measured
        # flake — this exact call succeeded in >10 back-to-back manual
        # replays this session but timed out once inside a real pytest
        # run's finally block (heavier concurrent load / latency). A
        # bare TimeoutError here previously propagated straight out of
        # select_status(), aborting BOTH the calling test's finally-block
        # restore attempt AND (chained, "during handling of the above
        # exception") whatever earlier exception the try block had
        # already raised — see this module's calling test's own
        # docstring/history. Escape is a real, already-used dismissal
        # path for this same detached popup pattern (see status_value()'s
        # sibling docs) — attempted exactly once per outer attempt, then
        # the combobox's own displayed label is read back and compared to
        # `label`.
        try:
            self.page.locator(self.STATUS_LISTBOX).first.wait_for(state="hidden", timeout=10000)
        except Exception:
            self.page.keyboard.press("Escape")
            try:
                self.page.locator(self.STATUS_LISTBOX).first.wait_for(state="hidden", timeout=5000)
            except Exception:
                pass
        #
        # ADDITIONAL SETTLE WAIT (2026-08-31, THIRD investigation of this
        # same class of flake, this session): confirmed live via
        # `status_value()` polled every 50ms right after the listbox
        # reports "hidden" that the combobox button's OWN displayed text
        # can still show the PRE-click label for a further 100-250ms after
        # the listbox close is observed (the popup-close animation and the
        # button's own text re-render are not the same paint) — a read
        # immediately after "hidden" is observed can therefore race the
        # button's own text update and report a stale value even though the
        # click landed correctly. A short fixed settle after the popup is
        # confirmed hidden (not a blind sleep in place of the wait itself —
        # this is IN ADDITION to it) closes that specific gap; it is bounded
        # and evidence-based, matching this module's own established
        # disclosed-grace precedent (SAVE_COMMIT_GRACE_MS).
        self.page.wait_for_timeout(250)
        return self.status_value()

    def status_value(self) -> str:
        """The combobox's currently displayed label (the button's own visible
        text) — the hidden input carries the raw persisted value/code, not
        the display label the test's `select_status(label)` and baseline
        restore compare against, so the button text is the correct read-back
        for this custom widget (see STATUS_COMBOBOX_BUTTON's docstring)."""
        return self.text(self.STATUS_COMBOBOX_BUTTON).strip()

    def has_file_uploaded(self, label: str) -> bool:
        """True when the field under `label` shows an existing filename
        (confirmed live: an uploaded file's row renders "<filename>.<ext>"
        text right after the Select File button, e.g.
        "general-manager-portrait.png") rather than being empty. Used to
        verify an image field already holds a real upload without needing
        to re-upload (and thus risk an unrecoverable overwrite) — see the
        module docstring / calling test's scope note."""
        return self.page.locator(
            f'xpath=//*[normalize-space(text())="{label}"]/following::*'
            f'[contains(text(), ".png") or contains(text(), ".jpg") or contains(text(), ".jpeg") or contains(text(), ".svg")][1]'
        ).count() > 0

    def upload_portrait(self, file_path: str) -> "GmMessageAdminPage":
        self.click(self.GM_PORTRAIT_SELECT_FILE)
        self.upload_file('input[type="file"]', file_path)
        return self

    def upload_hero_banner(self, file_path: str) -> "GmMessageAdminPage":
        self.click(self.HERO_BANNER_SELECT_FILE)
        self.upload_file('input[type="file"]', file_path)
        return self

    def upload_signature_avatar(self, file_path: str) -> "GmMessageAdminPage":
        self.click(self.SIGNATURE_AVATAR_SELECT_FILE)
        self.upload_file('input[type="file"]', file_path)
        return self

    # HEALED (2026-08-31, live investigation against qcdev record 79878,
    # tc_135453): confirmed live, by direct network capture, that clicking
    # Save fires a real `PUT .../generalmanagermessages/.../by-external-
    # reference-code/...` that returns 200 with the newly-entered value
    # already present in ITS OWN response body — the write itself is
    # synchronous and not the problem. The problem is what happens right
    # after: an IMMEDIATE re-navigation into the same record's edit form
    # (exactly what open_gm_message_edit_form() does, and what the calling
    # test does right after save()) can render the PREVIOUS (pre-save)
    # value — reproduced live, repeatedly, with a full multi-field EN/AR
    # edit + Status change + Save + zero-delay reload sequence run directly
    # against qcdev via this Page Object (no mocking): the reloaded value
    # matched the OLD value every time with no delay, and matched the NEW
    # value every time a small (~1.5-2s) grace was inserted between save()
    # returning and the next navigation. This is consistent with Liferay's
    # object-entry list/detail read path being served off an asynchronously
    # updated index/cache distinct from the synchronous REST write path
    # (the write commits immediately; the read-side cache/index that a
    # fresh portlet render queries catches up a beat later) — the same
    # class of gap the "before" grace pattern in core/web/overlays.py
    # documents for a different mechanism (client-rendered mount timing
    # there; server-side read-cache propagation here). No confirmable DOM
    # signal exists for "the read-side index has caught up" (no toast, no
    # spinner, no network event distinguishable from the write's own 200 —
    # see SUCCESS_TOAST's own unresolved-placeholder note), so this is a
    # disclosed, evidence-based fixed grace, not a blind arbitrary sleep:
    # the exact window was measured live, not guessed.
    SAVE_COMMIT_GRACE_MS = 2000

    def save(self) -> "GmMessageAdminPage":
        self.click(self.SAVE_BUTTON)
        # See SAVE_COMMIT_GRACE_MS docstring: a save-then-immediate-reload
        # observed live returning the pre-save value; this grace is the
        # confirmed-live fix, not a defensive guess.
        self.page.wait_for_timeout(self.SAVE_COMMIT_GRACE_MS)
        return self

    def cancel(self) -> "GmMessageAdminPage":
        self.click(self.CANCEL_BUTTON)
        return self

    # ---- State queries --------------------------------------------------------
    # Mirrors BoardMembersAdminPage.is_save_error_shown()'s confirmed-live
    # signal (plain-text scan; no stable class/role found for either message
    # on this project's DDM-rendered admin forms).
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

    def is_success_toast_shown(self) -> bool:
        self._require_verified(self.SUCCESS_TOAST, "SUCCESS_TOAST")
        return self.is_visible(self.SUCCESS_TOAST)

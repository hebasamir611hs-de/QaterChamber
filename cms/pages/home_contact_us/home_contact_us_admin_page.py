"""
cms/pages/home_contact_us/home_contact_us_admin_page.py — HomeContactUsAdminPage.

Control_Panel Page Object backing the Home Page "Contact Us" section
(public counterpart renders on the Home page, fragment "QC Home Contact
Us" — confirmed live via the Page Editor's fragment configuration panel,
2026-09-06). Backs 14 injected/approved Test Cases (136508-136572).

REAL, LIVE-VERIFIED FACTS (this session, 2026-09-06, Playwright MCP against
qcdev, authenticated via the persistent MCP browser profile — disclosed
fallback per this batch's instructions: no locators existed yet for this
section and the CLI extractor needs a reachable, already-authenticated,
already-navigated state to target the right screen; navigation here goes
through client-rendered menus/fragment panels the CLI extractor's plain
--url/--scope pass cannot drive):

  - `cms/pages/home_quick_contact/home_quick_contact_admin_page.py` is an
    UNIMPLEMENTED ("Phase 2 ... not yet implemented") stub with a name that
    does NOT match what this feature turned out to be live — nothing there
    was reused. This module is new, in its own `home_contact_us/` folder.

  - This section is backed by TWO SEPARATE live content surfaces, not one
    Object Definition as the task brief assumed:

    1. A Liferay JOURNAL (Web Content) ARTICLE, NOT an Object Definition
       entry — title "Contact Us Section", articleId `53012`, groupId
       `37246`, structure "Contact Us Section" (ddmStructureId `52431`),
       version 1.1 (Approved). Reached via Content & Data -> Web Content
       (search "Contact"), or directly via the confirmed-live edit URL
       (CONTACT_US_ARTICLE_EDIT_URL_PATH below — a Journal article edit URL
       built from a stable `p_p_id=com_liferay_journal_web_portlet_
       JournalPortlet` did NOT exhibit the regenerating-portlet-instance-id
       problem documented for the Object Definitions portlet elsewhere in
       this suite; confirmed live by a direct hit in a fresh navigation
       that rendered the correct article both times). Its own toolbar has
       real `Save as Draft` / `Publish` buttons and an `en-US`/`ar-SA`
       locale switcher — matching the case steps ("Click Save as Draft",
       "Click Save as Draft, then Publish") exactly. No externalReference
       Code is exposed anywhere in this article's own edit-form UI (checked
       live via `input[name*="externalReferenceCode"]` — none rendered),
       so, unlike every other Object-Definition-backed Page Object in this
       suite, there is no ERC-embedded PBI number to read here directly.

       *** LIVE BLOCKER — DISCLOSED, NOT WORKED AROUND ***
       This article's "Fields" panel (where Section Tag/Heading/Email
       Support/Telephone/Location/Recipient Emails/Send Message Button
       Label would be edited) fails to render its field inputs, in BOTH
       en-US and ar-SA locales, confirmed live and reproducibly this
       session:
         - The "Fields" collapsible panel-header button DOES expand
           (`aria-expanded` verified `true` before concluding this, per
           this session's own correction of an earlier false read where
           the panel had actually been toggled back CLOSED by a second
           click).
         - With `aria-expanded=true` confirmed, the panel's own content
           container (`#..._fieldsContent`) contains a `.ddm-form-builder-
           app` mount div that is genuinely EMPTY (`innerHTML` length 0-7,
           whitespace only) in en-US. Switching the toolbar locale to
           ar-SA (`Arabic Language: Translated` picker) and re-checking the
           same mount point after a 1.2s settle showed it EMPTY there too.
         - Console shows two `TypeError: B.map is not a function` /
           `O.map is not a function` traces inside `asset-taglib`'s
           `__liferay__/index.js`, invoked from the React render tree,
           plus two `403` responses on `/api/jsonws/invoke` — both are
           real, reproducible errors on every load of this article's edit
           screen. Whether the `asset-taglib` failure (tag/category
           picker) is itself what aborts the sibling `ddm-form-builder-
           app` render, or the two are independent failures on this one
           screen, was not isolated further given this batch's time
           budget — reported as observed, not diagnosed to root cause.
       Net effect: the actual field-level Page Object locators for the 11
       Test Cases anchored on this article (all except the 3 Inquiry
       Category cases below) COULD NOT be captured live. Per this agent's
       own contract ("never invent selectors as real"), the constants
       below for this form are explicit `TODO(locator)` placeholders, and
       the corresponding tests are written with
       `@pytest.mark.skip(reason=...)` pointing back here — they are
       scripted (structure, markers, AAA shape, traceability) but their
       bodies cannot fill/read real fields until this rendering blocker is
       fixed or a different edit path is confirmed. This is a PRODUCT-SIDE
       observation to report back, not an automation defect to silently
       route around with an invented selector.
       PBI ATTRIBUTION: with no ERC on this article to read, and no Azure
       DevOps MCP tool available this session to resolve the parent PBI via
       API, this module uses `pbi_129390` for the article-backed tests too
       — inferred, NOT confirmed, from the fact that the Inquiry Category
       dropdown rendered by this SAME public Contact Us section is sourced
       from the "Inquiry Categories" Object Definition whose rows do carry
       `QCDEMO-129390-INQCAT-*` (see below), i.e. best-available same-
       feature evidence, not a guess invented from nothing. Disclosed here
       explicitly per this session's own instruction not to silently borrow
       a PBI number.

    2. The "Inquiry Categories" OBJECT DEFINITION (objectDefinitionId
       `52436`), a REPEATABLE list — confirmed live with 11 rows ("Showing
       1 to 11 of 11 entries"), each a seeded QCDEMO row with
       externalReferenceCode `QCDEMO-129390-INQCAT-01` .. `-11` (row 01,
       record ID `52706`, Display Order `100`, Category Label "General
       Inquiry" — the exact row TCs 136534/136538/136569 target). PBI
       129390 is read directly off this ERC (real evidence, not a guess).
       This form's edit screen renders correctly (unlike the article
       above): Active Status (checkbox), Display Order (text input),
       Category Label (text input with its own per-locale en-us/ar-sa
       toggle button, same shape as every other DDM-object-entry form in
       this suite). Confirmed live field names (regenerating random
       token, same caveat as every other Object Entry form here):
       `..._ddm$$displayOrder$<token>$0$$en_US`,
       `..._ddm$$label$<token>$0$$en_US` (+ `...inputValue` visible mirror,
       `data-testid="visibleChangeInput"`). Same id-substring approach as
       `home_business_events_admin_page.py`'s `_text_input_by_id_substring`
       is reused here (`_field_by_name_substring`) since the trailing
       token is confirmed-live NOT stable across reloads.

  - Public rendering (fragment "QC Home Contact Us" on `/en/home`) already
    shows values that match several cases' target values verbatim as
    CURRENT live content (Heading "Connect with Qatar Chamber to Move Your
    Business Forward", Telephone "+974 44559111") — i.e. several of these
    12 "enter a valid value" cases are, on this environment, already
    re-asserting the section's EXISTING seeded value rather than a change.
    Not worked around; each test still performs its own fill + Save action
    per the case's literal steps.

  - DRAFT-VS-PUBLIC CONTRADICTION IN THE CASE TEXT (disclosed, not
    silently resolved either way): 12 of these 14 cases say "Click Save as
    Draft" yet their Expected column also claims the value "renders on
    Home Page" / "reflects on public section" / "appears in public
    dropdown" — a Draft save does not publish. Where the article's Fields
    panel were reachable, this module's tests would assert only authoring-
    side persistence (reopen-and-reread) for the 12 Draft-only cases, and
    would additionally assert the PUBLIC page in a fresh, logged-out
    browser context (never the CMS-authenticated page, per this project's
    own public-page-visibility convention) for the two cases whose steps
    explicitly say "Save as Draft, then Publish" (136546, 136572 — Send
    Message Button Label EN/AR). That public-context assertion is written
    into those two tests' TODO bodies below for when the Fields blocker
    clears; it could not be exercised this session since the fields
    themselves could not be filled.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings

# ---- Confirmed-live identifiers --------------------------------------------
INQUIRY_CATEGORY_01_ERC = "QCDEMO-129390-INQCAT-01"
INQUIRY_CATEGORY_01_RECORD_ID = "52706"
INQUIRY_CATEGORIES_OBJECT_DEFINITION_ID = "52436"

CONTACT_US_SECTION_ARTICLE_ID = "53012"
CONTACT_US_SECTION_GROUP_ID = "37246"
CONTACT_US_SECTION_DDM_STRUCTURE_ID = "52431"

ADMIN_HOME_EN_URL_PATH = "/en/home"  # same locale-forcing entry as every other admin page in this suite

# Confirmed-live direct edit URL for the Journal article — unlike the Object
# Definitions portlet elsewhere in this suite, this p_p_id did NOT exhibit the
# regenerating-instance-id problem in two separate direct hits this session.
# Still reached via the same "always confirm live, never assume" posture —
# kept here as the confirmed shape, not a hardcoded shortcut invented cold.
CONTACT_US_ARTICLE_EDIT_URL_PATH = (
    "/en/group/qatar-chamber/~/control_panel/manage"
    "?p_p_id=com_liferay_journal_web_portlet_JournalPortlet"
    "&p_p_lifecycle=0&p_p_state=maximized"
    "&_com_liferay_journal_web_portlet_JournalPortlet_mvcRenderCommandName=/journal/edit_article"
    f"&_com_liferay_journal_web_portlet_JournalPortlet_articleId={CONTACT_US_SECTION_ARTICLE_ID}"
    f"&_com_liferay_journal_web_portlet_JournalPortlet_groupId={CONTACT_US_SECTION_GROUP_ID}"
    "&_com_liferay_journal_web_portlet_JournalPortlet_version=1.1"
)


def _field_by_name_substring(substring: str, tag: str = "input") -> str:
    """Same id/name-substring approach as home_business_events_admin_page.py's
    `_text_input_by_id_substring` — the trailing random token in these DDM
    field names (`ddm$$<field>$<token>$0$$en_US`) regenerates across reloads;
    a `*=` substring on the stable `ddm$$<field>$` prefix does not."""
    return f'{tag}[name*="{substring}"]'


class HomeContactUsAdminPage(BasePage):
    # ---- Menu navigation (confirmed live) ----------------------------------
    PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
    CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
    INQUIRY_CATEGORIES_MENU_ITEM = '[role="menuitem"]:text-is("Inquiry Categories")'
    INQUIRY_CATEGORY_01_ROW_LINK = f'table tbody a:text-is("{INQUIRY_CATEGORY_01_RECORD_ID}")'
    LIST_RENDER_TIMEOUT_MS = 20000  # same measured-live grid-render class used elsewhere in this suite
    FORM_RENDER_TIMEOUT_MS = 20000

    # ---- Inquiry Category (row 01) edit form fields — CONFIRMED LIVE -------
    # CORRECTED 2026-09-06 (live re-check): the bare name-substring matched
    # BOTH the real visible text input AND a same-named-prefix hidden
    # `..._edited` companion input (Playwright strict-mode violation, 2
    # elements). The visible input is `type="text"`; the `_edited` one is
    # `type="hidden"` — narrowing by `[type="text"]` disambiguates.
    CATEGORY_DISPLAY_ORDER = _field_by_name_substring("ddm$$displayOrder$") + '[type="text"]'
    # CORRECTED 2026-09-06 (live re-check): the field whose `name` attribute
    # matches `ddm$$label$` is a HIDDEN input (type="hidden") — it never
    # matches `[type="text"]`, so the old selector timed out on every run
    # despite the form rendering correctly. The actual visible/editable
    # input has an EMPTY `name` attribute and instead carries
    # `data-testid="visibleChangeInput"` (confirmed live, exactly one match
    # on this form) — same shape called out in the docstring above but not
    # reflected in this selector until now. This was a LOCATOR bug, not a
    # product rendering bug: the Inquiry Category edit form (row 01) opens
    # and renders Active Status / Display Order / Category Label correctly.
    CATEGORY_LABEL_EN = 'input[data-testid="visibleChangeInput"]'
    CATEGORY_LABEL_LOCALE_TOGGLE = 'button:has-text("en-us")'
    CATEGORY_ACTIVE_STATUS_CHECKBOX = 'input[type="checkbox"]'
    CATEGORY_SAVE_BUTTON = 'button:has-text("Save")'
    CATEGORY_CANCEL_BUTTON = 'button:has-text("Cancel")'

    # ---- Contact Us Section article fields — TODO(locator): BLOCKED live,
    # see module docstring's "LIVE BLOCKER" note. Do not treat these as real
    # until the Fields panel render issue is confirmed fixed and the fields
    # are re-extracted live.
    SECTION_TAG_EN = "TODO(locator): Section Tag (EN) — Fields panel does not render, see docstring"
    SECTION_TAG_AR = "TODO(locator): Section Tag (AR) — Fields panel does not render, see docstring"
    SECTION_HEADING_EN = "TODO(locator): Section Heading (EN) — Fields panel does not render, see docstring"
    SECTION_HEADING_AR = "TODO(locator): Section Heading (AR) — Fields panel does not render, see docstring"
    EMAIL_SUPPORT_ADDRESS = "TODO(locator): Email Support Address — Fields panel does not render, see docstring"
    TELEPHONE_NUMBER = "TODO(locator): Telephone Number — Fields panel does not render, see docstring"
    LOCATION_ADDRESS_EN = "TODO(locator): Location Address (EN) — Fields panel does not render, see docstring"
    LOCATION_ADDRESS_AR = "TODO(locator): Location Address (AR) — Fields panel does not render, see docstring"
    FORM_RECIPIENT_EMAILS = "TODO(locator): Form Recipient Email(s) — Fields panel does not render, see docstring"
    SEND_MESSAGE_BUTTON_LABEL_EN = "TODO(locator): Send Message Button Label (EN) — Fields panel does not render, see docstring"
    SEND_MESSAGE_BUTTON_LABEL_AR = "TODO(locator): Send Message Button Label (AR) — Fields panel does not render, see docstring"

    ARTICLE_SAVE_AS_DRAFT_BUTTON = 'button:has-text("Save as Draft")'  # CONFIRMED LIVE
    ARTICLE_PUBLISH_BUTTON = 'button:has-text("Publish")'  # CONFIRMED LIVE
    ARTICLE_FIELDS_PANEL_TOGGLE = 'button:has-text("Fields")'  # CONFIRMED LIVE (panel expands; inputs do not render — see docstring)
    ARTICLE_LOCALE_TOGGLE = 'button:has-text("en-US")'  # CONFIRMED LIVE, toolbar locale switcher

    # ---- Navigation ---------------------------------------------------------
    def _open_admin_home(self) -> None:
        from cms.pages.control_panel.login_page import CmsLoginPage

        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(self.CONTENT_DATA_MENU_ITEM) or self.is_visible(self.PRODUCT_MENU_TOGGLE)):
            CmsLoginPage(self.page).open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

        if not self.is_visible(self.CONTENT_DATA_MENU_ITEM):
            self.click(self.PRODUCT_MENU_TOGGLE)
            self.wait_for(self.CONTENT_DATA_MENU_ITEM)

    def open_inquiry_category_01_edit_form(self) -> "HomeContactUsAdminPage":
        """Content & Data -> Inquiry Categories -> row 01 (ERC
        QCDEMO-129390-INQCAT-01, record 52706) — CONFIRMED LIVE, renders
        correctly (Active Status / Display Order / Category Label)."""
        self._open_admin_home()
        self.click(self.CONTENT_DATA_MENU_ITEM)
        self.click(self.INQUIRY_CATEGORIES_MENU_ITEM)
        self.wait_for(self.INQUIRY_CATEGORY_01_ROW_LINK, timeout=self.LIST_RENDER_TIMEOUT_MS)
        self.click(self.INQUIRY_CATEGORY_01_ROW_LINK)
        self.wait_for(self.CATEGORY_LABEL_EN, timeout=self.FORM_RENDER_TIMEOUT_MS)
        return self

    def open_contact_us_section_article(self) -> "HomeContactUsAdminPage":
        """Direct hit on the confirmed-live Journal article edit URL — see
        module docstring on why this one p_p_id did not need the menu-click
        path other Object Definition portlets in this suite require."""
        self.open(control_panel_url(CONTACT_US_ARTICLE_EDIT_URL_PATH))
        self.wait_for(self.ARTICLE_SAVE_AS_DRAFT_BUTTON, timeout=self.FORM_RENDER_TIMEOUT_MS)
        return self

    # ---- Field actions (Inquiry Category form) ------------------------------
    def fill_text_field(self, field_locator: str, value: str) -> "HomeContactUsAdminPage":
        self.type(field_locator, value)
        return self

    def field_value(self, field_locator: str) -> str:
        return self.page.locator(field_locator).input_value()

    # CORRECTED 2026-09-06 (live re-check): the dropdown this toggle opens
    # renders each locale by its NATIVE display name + region (e.g.
    # "العربية (المملكة العربية السعودية)"), NOT the `ar-sa` code string —
    # `text=ar-sa` never matched, which is why this step timed out on every
    # run despite the dropdown opening correctly. Confirmed live via
    # screenshot: the Arabic (Saudi Arabia) option is a
    # `button[role="menuitem"]` containing the Arabic script text, unique
    # on the page.
    CATEGORY_LABEL_ARABIC_OPTION = 'button[role="menuitem"]:has-text("العربية")'

    def switch_category_label_locale_to_arabic(self) -> "HomeContactUsAdminPage":
        """Opens the Category Label field's own per-field locale dropdown
        and selects Arabic — same per-field (not toolbar-level) locale
        switch shape confirmed live on this Object Entry form."""
        self.click(self.CATEGORY_LABEL_LOCALE_TOGGLE)
        self.wait_for(self.CATEGORY_LABEL_ARABIC_OPTION, first=True)
        self.click(self.CATEGORY_LABEL_ARABIC_OPTION)
        return self

    def save_category(self) -> "HomeContactUsAdminPage":
        self.click(self.CATEGORY_SAVE_BUTTON)
        self.page.wait_for_timeout(2000)
        return self

    def is_save_error_shown(self) -> bool:
        body_text = self.page.locator("body").inner_text()
        return "This field is required." in body_text or "This form is invalid" in body_text

    def save_error_text(self) -> str:
        body_text = self.page.locator("body").inner_text()
        for marker in ("This form is invalid", "This field is required."):
            idx = body_text.find(marker)
            if idx != -1:
                return body_text[idx: idx + 120]
        return ""

    # ---- Field actions (Contact Us Section article) — usable once the
    # Fields-panel blocker clears; Save as Draft / Publish are real today.
    def save_article_as_draft(self) -> "HomeContactUsAdminPage":
        self.click(self.ARTICLE_SAVE_AS_DRAFT_BUTTON)
        self.page.wait_for_timeout(2000)
        return self

    def publish_article(self) -> "HomeContactUsAdminPage":
        self.click(self.ARTICLE_PUBLISH_BUTTON)
        self.page.wait_for_timeout(2000)
        return self

    # ---- Real cross-session logout / re-login (same shape as every other
    # admin page in this suite) ----------------------------------------------
    LOGOUT_PATH = "/c/portal/logout"

    def logout(self) -> "HomeContactUsAdminPage":
        self.open(control_panel_url(self.LOGOUT_PATH))
        return self

    def login_as(self, username: str, password: str) -> "HomeContactUsAdminPage":
        from cms.pages.control_panel.login_page import CmsLoginPage

        CmsLoginPage(self.page).open_login().login(username, password)
        return self

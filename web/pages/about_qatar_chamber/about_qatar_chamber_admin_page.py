"""
web/pages/about_qatar_chamber/about_qatar_chamber_admin_page.py —
AboutQatarChamberAdminPage.

PBI 129392 / QC-ABOUT 001 "About Qatar Chamber" — Control_Panel-tagged cases
(15 in this batch: 134675, 134676, 134679, 134688, 134690, 134691, 134692,
134693, 134694, 134697, 134698, 134701, 134730, 134731, 134736). Sibling of
about_qatar_chamber_page.py (the public Web-platform Page Object for this
same PBI).

STATUS (2026-08-31): UNBLOCKED — TEST_USER/TEST_PASSWORD ARE set in .env this
session (test@liferay.com / qcdev.ihorizons.com) and CLI-confirmed working.
17 of the 23 locators below are now REAL, LIVE-CONFIRMED selectors (harvested
via `python tools/save_auth.py` + `python tools/extract_locators.py`, one
extraction pass per screen state: the Content & Data nav, the entries list,
the entry-edit form, and an interactive DOM-inspection pass for the
Status/CKEditor/upload internals extract_locators.py's static harvest can't
click through). The remaining 6 are confirmed **absent from the real UI**
after exhaustive exploration this session — not "couldn't reach", genuinely
not there — and are left as literal TODO placeholders per the project's own
convention; do not fabricate them. See per-field notes below.

REAL, LIVE-CONFIRMED FACTS (2026-08-31, headless Chromium against qcdev,
authenticated via `.auth/state.json`):

1. NAVIGATION — Content & Data > "About Qatar Chamber Pages" is the admin
   surface: a Liferay Object Definition (objectDefinitionId=77427,
   groupId=37246). Exactly the same portlet-instance-ID-in-URL trap
   documented in org_structure_admin_page.py applies here (the
   `...ObjectDefinitionsPortlet_G1O2...` id in a captured URL is randomly
   regenerated per session) — menu navigation via PRODUCT_MENU_TOGGLE /
   CONTENT_DATA_MENU_ITEM / OBJECT_ENTRIES_NAV_LINK is the only
   session-stable path, confirmed live. `navigate_to_about_page_entry()`
   below mirrors OrgStructureAdminPage.open_departments_list()'s pattern.

2. THE ENTRIES LIST is a data grid with a SINGLE row (ID 77675 this
   session — a singleton Object entry, confirmed by "Showing 1 to 1 of 1
   entries"). ABOUT_PAGE_ENTRY_ROW targets the row's ID-cell link by CSS
   class (`.cell-id a`), not the literal "77675" text, so it survives the ID
   changing if the entry is ever deleted/recreated.

3. THE ENTRY-EDIT SCREEN's real field inventory (confirmed exhaustively via
   `.ddm-field[data-field-name]`, in on-screen order) is EXACTLY:
   Content Image (file upload) / Content Image Alt Text / Hero Banner Alt
   Text / Hero Banner Image (file upload) / Hyperlink Title / Hyperlink URL
   / Page Content (CKEditor rich text) / Status (Draft|Published dropdown)
   / Page Title. This is a DDM-rendered form: every input carries a
   portlet-instance-scoped `id`/`name` (dies with the session, exactly like
   org_structure's Departments form) but ALSO a STABLE, semantic
   `data-field-name` / `data-qa-id` on each field's wrapping `.ddm-field`
   div and a `data-testid="visibleChangeInput"` on each localizable text
   input (non-unique alone — 6 matches — but unique once scoped to its
   field's `data-field-name`). All CSS locators below use that stable
   scoping, never the session-random `id`.

4. **NO SEPARATE PAGE TITLE/CONTENT (AR) FIELDS EXIST.** Each localizable
   field (Page Title, Page Content, Content/Hero alt text, Hyperlink Title)
   has exactly ONE input, plus a per-field language-switcher button
   (`data-testid="triggerButton"`, showing "en-us") that opens a locale
   picker (confirmed: English (United States) DEFAULT, العربية (المملكة
   العربية السعودية) TRANSLATED, plus several NOT TRANSLATED locales). The
   SAME physical input's value swaps to that locale's translation once
   picked — there is no distinct Arabic DOM element. PAGE_TITLE_AR_INPUT /
   PAGE_CONTENT_AR_EDITOR are therefore set to the SAME confirmed locator
   as their EN counterparts; reaching the actual Arabic value requires
   first clicking that field's language-switcher trigger and selecting the
   Arabic locale, which no test below does yet (no locator name for that
   trigger was in the 23 requested — flagging, not fabricating one).

5. **PAGE CONTENT is a CKEditor CLASSIC instance whose editable surface is
   an `<iframe title="editor">` (`iframe.cke_wysiwyg_frame`), not a plain
   `[contenteditable]` on the main document** — confirmed by
   `page.evaluate` (0 same-document `[contenteditable]` nodes, 1 matching
   iframe) and by reading its body text through `page.frame_locator(...)`.
   PAGE_CONTENT_EN_EDITOR / PAGE_CONTENT_AR_EDITOR below are real,
   confirmed selectors for that iframe container (correct for
   `wait_for()` / `is_visible()`). **KNOWN GAP, disclosed not silently
   patched:** `BasePage.type()` / `.text()` call `self.page.locator(...)`,
   and Playwright's `Locator` API does not pierce into an iframe's
   document — only `page.frame_locator(...)` does. `set_page_content_en()`
   / `preview_content_text()` will therefore raise/return empty against
   this iframe locator until `core/web/base_page.py` gains a frame-aware
   variant (e.g. `type_in_frame(frame_selector, body_selector, text)`).
   That is a wrapper-capability gap, not a missing locator, and out of
   scope for this locator-only pass — flagged for a follow-up, not fixed
   here without being asked.

6. **THERE IS NO SEPARATE SAVE-DRAFT / PUBLISH / UNPUBLISH BUTTON.** The
   entry-edit screen's only persistence action is ONE "Save" button
   (confirmed: the full visible-button inventory of this screen is Save,
   Cancel, the Status combobox, the 6 per-field language triggers, and the
   3 upload widgets' Select File/Download/Delete controls — nothing else).
   What is actually published/drafted is controlled by the separate
   **Status** field (a Clay combobox, confirmed options "Choose an
   Option" / "Draft" / "Published"). SAVE_DRAFT_BUTTON and PUBLISH_BUTTON
   therefore both resolve to this SAME real Save button — that is not a
   copy-paste mistake, it is what was observed live. UNPUBLISH_BUTTON has
   NO distinct element to resolve to (see its own TODO note below) — this
   is a Page-Object action-design question (should click_save_draft() /
   click_unpublish() also drive the Status combobox first?), not a locator
   gap, and is intentionally left for a follow-up decision rather than
   silently rewritten here.

7. SUCCESS_TOAST — confirmed live by clicking Save: Liferay's generic
   `.alert.alert-success` banner (checkmark icon, dismissible), same
   pattern as every other Control_Panel admin page in this project.

8. RECORD_STATUS_LABEL — resolved to the Status field's own combobox
   button (`[data-qa-id="pageStatus"] button[role="combobox"]`), whose
   visible text IS the current status ("Published" confirmed live). Doubles
   as the interactive control if a future pass wires up real
   draft/publish/unpublish switching.

9. **CONFIRMED GENUINELY ABSENT — left as literal TODO, not guessed:**
   - HYPERLINK_OPEN_BEHAVIOUR_SELECT — the object's field list (enumerated
     exhaustively above) has ONLY `hyperlinkTitle` and `hyperlinkUrl`; no
     same-tab/new-tab or any other open-behaviour control exists anywhere
     on this screen.
   - AUDIT_LOG_NAV_LINK / AUDIT_LOG_ENTRY_ROW — the entries list row's own
     "Actions" menu (confirmed by opening it) contains exactly View /
     Delete / Permissions — no Audit Log / History entry point exists
     there, in the left nav, or anywhere else checked on the edit screen's
     full button inventory (see point 6).
   - PREVIEW_BUTTON / PREVIEW_PANEL — no page-level Preview action exists.
     The only element matching the text "Preview" anywhere on the
     entry-edit screen is CKEditor's own toolbar icon
     (`#cke_30`, class `cke_button__expand cke_button_disabled` — CONFIRMED
     DISABLED), which is CKEditor's in-editor HTML preview plugin, not a
     live/draft site-preview feature. ADO-134692's "Preview renders
     unpublished draft content without publishing it" scenario has no real
     UI to automate against on this screen this session — this is a
     genuine coverage question for the QA Manager (does this feature exist
     elsewhere, e.g. Site Builder page preview, or was it assumed?), not
     something to be silently invented here.

Every unresolved constant below is still the literal `_todo(...)` string —
never a guessed-but-plausible selector.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url

_TODO_PREFIX = "TODO:"


def _todo(what: str) -> str:
    return (
        f"{_TODO_PREFIX} confirmed ABSENT from the live 'About Qatar Chamber Pages' "
        f"Object entry management screen this session (2026-08-31, exhaustive check "
        f"— see class docstring point 9), not merely unreached: {what}"
    )


class AboutQatarChamberAdminPage(BasePage):
    # ── Navigation (real, confirmed live 2026-08-31 — mirrors
    #    OrgStructureAdminPage's session-stable menu-click pattern; a
    #    captured Object-entries URL embeds a portlet instance id that is
    #    randomly regenerated per session, so it is deliberately NOT saved
    #    as a constant here) ──────────────────────────────────────────────
    PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
    CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
    OBJECT_ENTRIES_NAV_LINK = 'a:has-text("About Qatar Chamber Pages")'

    # ── Entries list screen (real, confirmed live) ───────────────────────
    ABOUT_PAGE_ENTRY_ROW = "table tbody tr .cell-id a"

    # ── Entry-edit screen (real, confirmed live — see docstring points 3-8)
    ENTRY_EDIT_SCREEN = 'form[id$="_fm"]'
    PAGE_TITLE_EN_INPUT = '[data-field-name="pageTitle"] [data-testid="visibleChangeInput"]'
    PAGE_TITLE_AR_INPUT = '[data-field-name="pageTitle"] [data-testid="visibleChangeInput"]'  # see docstring point 4
    PAGE_CONTENT_EN_EDITOR = '[data-qa-id="pageContent"] iframe[title="editor"]'  # see docstring point 5
    PAGE_CONTENT_AR_EDITOR = '[data-qa-id="pageContent"] iframe[title="editor"]'  # see docstring points 4 + 5
    CONTENT_IMAGE_UPLOAD = '[data-field-name="contentImage"] input[type="file"]'
    CONTENT_IMAGE_ALT_TEXT_EN_INPUT = '[data-field-name="contentImageAltText"] [data-testid="visibleChangeInput"]'
    HERO_BANNER_IMAGE_UPLOAD = '[data-field-name="heroBannerImage"] input[type="file"]'
    HERO_BANNER_ALT_TEXT_INPUT = '[data-field-name="heroBannerAltText"] [data-testid="visibleChangeInput"]'
    HYPERLINK_TITLE_INPUT = '[data-field-name="hyperlinkTitle"] [data-testid="visibleChangeInput"]'
    HYPERLINK_URL_INPUT = '[data-field-name="hyperlinkUrl"] [data-testid="visibleChangeInput"]'
    SAVE_DRAFT_BUTTON = 'button:has-text("Save")'  # see docstring point 6 — same button as PUBLISH_BUTTON
    PUBLISH_BUTTON = 'button:has-text("Save")'  # see docstring point 6 — same button as SAVE_DRAFT_BUTTON
    SUCCESS_TOAST = ".alert.alert-success"
    RECORD_STATUS_LABEL = '[data-qa-id="pageStatus"] button[role="combobox"]'

    # ── Confirmed ABSENT this session — literal TODO, never guessed
    #    (see class docstring point 9) ────────────────────────────────────
    HYPERLINK_OPEN_BEHAVIOUR_SELECT = _todo("a hyperlink open-behaviour (same/new tab) control")
    UNPUBLISH_BUTTON = _todo(
        "a distinct Unpublish action — the real workflow is the Status combobox "
        "(RECORD_STATUS_LABEL) set to 'Draft' then the one Save button; needs a "
        "Page-Object action-design decision, not a locator"
    )
    AUDIT_LOG_NAV_LINK = _todo("an Audit Log / History nav entry point")
    AUDIT_LOG_ENTRY_ROW = _todo("an audit log entry row filtered to this page record")
    # ADO-134692 — Preview renders unpublished draft content without publishing it
    PREVIEW_BUTTON = _todo(
        "a page-level Preview action — the only 'Preview' element found is CKEditor's "
        "own disabled toolbar icon inside Page Content, not a site/draft preview"
    )
    PREVIEW_PANEL = _todo("a Preview panel/iframe container that renders draft content")

    def open_control_panel_home(self) -> "AboutQatarChamberAdminPage":
        self.open(control_panel_url("/home"))
        return self

    def navigate_to_about_page_entry(self) -> "AboutQatarChamberAdminPage":
        """Real, confirmed live 2026-08-31 — mirrors
        OrgStructureAdminPage.open_departments_list()'s pattern exactly:
        force control_panel_url("/home"), open the Product Menu if the
        Content & Data item isn't already visible, click through to the
        object's nav item, then into its single entry row."""
        self.open_control_panel_home()
        if not self.is_visible(self.CONTENT_DATA_MENU_ITEM):
            self.click(self.PRODUCT_MENU_TOGGLE)
            self.wait_for(self.CONTENT_DATA_MENU_ITEM)
        self.click(self.CONTENT_DATA_MENU_ITEM)
        self.wait_for(self.OBJECT_ENTRIES_NAV_LINK)
        self.click(self.OBJECT_ENTRIES_NAV_LINK)
        self.wait_for(self.ABOUT_PAGE_ENTRY_ROW)
        self.click(self.ABOUT_PAGE_ENTRY_ROW)
        self.wait_for(self.ENTRY_EDIT_SCREEN)
        return self

    # ── State queries — no asserts, tests do the asserting ──────────────
    def is_entry_edit_screen_visible(self) -> bool:
        return self.is_visible(self.ENTRY_EDIT_SCREEN)

    def is_success_toast_visible(self) -> bool:
        return self.is_visible(self.SUCCESS_TOAST)

    def set_page_title_en(self, value: str) -> "AboutQatarChamberAdminPage":
        self.type(self.PAGE_TITLE_EN_INPUT, value)
        return self

    def set_page_content_en(self, html: str) -> "AboutQatarChamberAdminPage":
        self.type(self.PAGE_CONTENT_EN_EDITOR, html)
        return self

    def set_hyperlink(self, title: str, url: str) -> "AboutQatarChamberAdminPage":
        self.type(self.HYPERLINK_TITLE_INPUT, title)
        self.type(self.HYPERLINK_URL_INPUT, url)
        return self

    def click_publish(self) -> "AboutQatarChamberAdminPage":
        self.click(self.PUBLISH_BUTTON)
        return self

    def click_unpublish(self) -> "AboutQatarChamberAdminPage":
        self.click(self.UNPUBLISH_BUTTON)
        return self

    def click_save_draft(self) -> "AboutQatarChamberAdminPage":
        self.click(self.SAVE_DRAFT_BUTTON)
        return self

    def open_audit_log_for_entry(self) -> "AboutQatarChamberAdminPage":
        self.click(self.AUDIT_LOG_NAV_LINK)
        return self

    def is_audit_log_entry_visible(self) -> bool:
        return self.is_visible(self.AUDIT_LOG_ENTRY_ROW)

    # ── Preview (ADO-134692) — renders unpublished draft content ─────────
    def click_preview(self) -> "AboutQatarChamberAdminPage":
        self.click(self.PREVIEW_BUTTON)
        self.wait_for(self.PREVIEW_PANEL)
        return self

    def is_preview_panel_visible(self) -> bool:
        return self.is_visible(self.PREVIEW_PANEL)

    def preview_content_text(self) -> str:
        return self.text(self.PREVIEW_PANEL)

    def record_status_text(self) -> str:
        return self.text(self.RECORD_STATUS_LABEL)

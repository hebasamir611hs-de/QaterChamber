"""
cms/pages/board_of_directors/board_directory_page_admin_page.py —
BoardDirectoryPageAdminPage.

Control_Panel Page Object for PBI 129398's PAGE-LEVEL admin surface — the
CORRECT surface, per the QA Manager's 2026-09-16 redirect. This supersedes
neither `BoardOfDirectorsAdminPage` (the Liferay Page Design / Fragment
Config panel — that class's own finding, "no Page Title / Hero Banner
upload / per-section Eyebrow-Heading / page Status field exists there," is
STILL CORRECT for that specific surface, unchanged) nor `BoardMembersAdminPage`
(the PER-MEMBER `manage-board-member` surface). This is a THIRD, separate
Object Authoring object — "Board Directory Page" — listed in the Object
Authoring index at `/web/qatar-chamber/manage-board-directory-page`, and it
is where every one of the 26 previously-dropped page-level cases' real
target fields actually live.

CONFIRMED LIVE 2026-09-16 (Playwright MCP, TEST_USER, English locale
forced, 1920x1080, read-only recon only — no Save/Submit/Publish/Unpublish
clicked during this investigation):

Navigation: `/web/qatar-chamber/manage-board-directory-page` — the SAME
Object-Authoring create-form-below-the-entries-table pattern as every other
object on this project (see `ObjectAuthoringPage`'s own module docstring).
Page title confirmed: "Manage: Board Directory Page - Qatar Chamber -
Liferay DXP".

ENTRIES (2 Approved rows in the "Board Directory Page entries" table):
  - `QCDEMO-129398-BOARD_DIRECTORY_PAGE-MAIN` (`MAIN_ENTRY_CODE` below) —
    Page Title = "Board of Directors & General Manager", Page Title AR =
    "أعضاء مجلس الإدارة والمدير العام" — matches
    `BoardOfDirectorsAdminPage.FRAGMENT_ANCHOR_TEXT` and the live public
    page's real `.qc-bod-hero-title` H1 text exactly. CONFIRMED (via both
    this row's own "Preview" link and the in-form Preview pane, banner text
    "PREVIEW — showing a published boarddirectorypages record, exactly as
    visitors see it.") to be the ONE real, live entry that drives the public
    `/web/qatar-chamber/about-us/board-of-directors` page. This is the ONLY
    entry any test in this batch is ever allowed to touch.
  - `e34a6937-436f-8ea9-7442-d5e9d20f10ce` — Page Title = "New Test" (both
    EN and AR fields hold the literal ASCII string "New Test") — a
    CONFIRMED stray/leftover test artifact, not real content. Flagged here
    for the QA Manager's own awareness; NOT deleted or otherwise touched by
    this batch — no delete target was positively confirmed disposable
    (`QCTEST-*`-prefixed or otherwise) per standards.md's "Destructive
    Operations Against qcdev" rule, and resolving/cleaning up an unrelated
    stray entry is out of this batch's scope regardless of that rule.

FIELD SET on the MAIN entry's edit form — CONFIRMED LIVE, every one
resolved via `get_by_role("textbox"/"checkbox", name=<label>, exact=True)`
(same accessible-name pattern as `BoardMembersAdminPage` — this surface
carries no id/name/data-testid hooks either):
    textbox    "Page Title"
    textbox    "Page Title — العربية"
    (file)     "Hero Banner Image" — hidden textbox "Hero Banner Image
               Select File" + sibling "Select File" button, the SAME
               `ObjectAuthoringPage.upload_file()` mechanism as every other
               object's file field on this project — a REAL upload control
               (unlike the Fragment panel's plain text/URL field
               `BoardOfDirectorsAdminPage` documents for the OTHER surface).
    textbox    "Hero Banner Alt Text" / "Hero Banner Alt Text — العربية"
    textbox    "Chairman Section Eyebrow" / "Chairman Section Eyebrow — العربية"
    textbox    "Chairman Section Heading" / "Chairman Section Heading — العربية"
    textbox    "Vice Chairmen Section Eyebrow" / "— العربية"
    textbox    "Vice Chairmen Section Heading" / "— العربية"
    textbox    "Board Members Section Eyebrow" / "— العربية"
    textbox    "Board Members Section Heading" / "— العربية"
    textbox    "General Manager Section Eyebrow" / "— العربية"
    textbox    "General Manager Section Heading" / "— العربية"
    checkbox   "Active" — CONFIRMED CHECKED (True) on the real MAIN entry.

No `maxlength`/`required` HTML attribute was found on ANY of the plain
textboxes above (checked live via `getAttribute()` on the resolved
Playwright locator, specifically for "Page Title"/"Page Title — العربية")
— unlike `OrgStructureAdminPage`'s Photo fields, this object does NOT
silently truncate an over-limit value at the browser level, so a "rejects
>100 chars"-style case's real outcome depends on this surface's own
app-level/server-level validation. `is_save_error_shown()`/
`save_error_text()` below REUSE the exact same 3-mechanism detection
`BoardMembersAdminPage` already confirmed live for this identical Object
Authoring framework (native HTML5 `:invalid` / `[data-qc-oel-field-error]`
app-level rejection / `[data-qc-oel-editbar]` server banner) — this is a
generic, framework-level mechanism, not object-specific, but it was NOT
independently re-exercised live against THIS object's own empty/over-length
fields this session: doing so would require an actual Submit-for-Publishing
mutation of the real MAIN singleton entry, which falls outside this task's
read-only Step-0 recon boundary (an in-session attempt to verify this via a
live mutate-observe-restore probe was itself blocked by the environment's
own safety controls). Each negative-case test below therefore asserts the
QA case's own stated expected result via this shared, already-proven
mechanism — to be confirmed pass/fail on the user's own run, exactly as
"Scripted, not yet executed" means everywhere else in this codebase.

PAGE-LEVEL STATUS: the entries list's own Status column (Draft/Approved) IS
a real, working Object-Authoring Draft->Approved lifecycle control on THIS
surface (Save as Draft / Submit for Publishing / Unpublish — same generic
`ObjectAuthoringPage` state machine already confirmed for
`manage-board-member`) — this CORRECTS the answer for cases 133544/133545
relative to `BoardOfDirectorsAdminPage`'s own (still-accurate, for THAT
surface) "no Status field exists" finding. NOT exercised by this batch: the
MAIN entry IS the real, live, production Board of Directors page's driving
record (confirmed above) — Unpublishing/Drafting it takes the real public
page off the live site, an irreversible-during-the-window production-
visibility flip that standards.md's "Destructive Operations Against qcdev"
rule requires explicit go-ahead for before automating. Not sought or given
this session — see the test module's own BATCH 5 docstring for the explicit
escalation back to the QA Manager.

DROPPED (Hero Banner Image upload cases 133524-133529, NOT scripted here):
the field is a REAL upload control (unlike the Fragment panel), but it
lives ONLY on the MAIN singleton. Unlike Board Member's Member Photo (where
a disposable QCTEST- record can be created, photographed, and then fully
deleted), there is no disposable equivalent for a page-level singleton's
Hero Banner Image, and no original-file binary is available to restore an
exact original value after a destructive re-upload — the same no-revert-
path reasoning `BoardMembersAdminPage`'s own module docstring already
disclosed for Member Photo on an EXISTING record, applied here to a field
with an even larger blast radius (overwriting the REAL live hero image on
the production page, visible to every visitor). Per the QA Manager's
explicit "if you cannot find a safe way to test something without mutating
shared state, drop it" instruction, these 6 cases are dropped with this
evidence rather than attempted.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url, settings

SLUG = "board-directory-page"
MAIN_ENTRY_CODE = "QCDEMO-129398-BOARD_DIRECTORY_PAGE-MAIN"

ADMIN_HOME_EN_URL_PATH = "/en/home"
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'

FIELD_PAGE_TITLE = "Page Title"
FIELD_PAGE_TITLE_AR = "Page Title — العربية"
FIELD_HERO_BANNER_IMAGE = "Hero Banner Image"
FIELD_HERO_BANNER_ALT_TEXT = "Hero Banner Alt Text"
FIELD_HERO_BANNER_ALT_TEXT_AR = "Hero Banner Alt Text — العربية"
FIELD_CHAIRMAN_EYEBROW = "Chairman Section Eyebrow"
FIELD_CHAIRMAN_EYEBROW_AR = "Chairman Section Eyebrow — العربية"
FIELD_CHAIRMAN_HEADING = "Chairman Section Heading"
FIELD_CHAIRMAN_HEADING_AR = "Chairman Section Heading — العربية"
FIELD_VICE_CHAIRMEN_EYEBROW = "Vice Chairmen Section Eyebrow"
FIELD_VICE_CHAIRMEN_EYEBROW_AR = "Vice Chairmen Section Eyebrow — العربية"
FIELD_VICE_CHAIRMEN_HEADING = "Vice Chairmen Section Heading"
FIELD_VICE_CHAIRMEN_HEADING_AR = "Vice Chairmen Section Heading — العربية"
FIELD_BOARD_MEMBERS_EYEBROW = "Board Members Section Eyebrow"
FIELD_BOARD_MEMBERS_EYEBROW_AR = "Board Members Section Eyebrow — العربية"
FIELD_BOARD_MEMBERS_HEADING = "Board Members Section Heading"
FIELD_BOARD_MEMBERS_HEADING_AR = "Board Members Section Heading — العربية"
FIELD_GM_EYEBROW = "General Manager Section Eyebrow"
FIELD_GM_EYEBROW_AR = "General Manager Section Eyebrow — العربية"
FIELD_GM_HEADING = "General Manager Section Heading"
FIELD_GM_HEADING_AR = "General Manager Section Heading — العربية"
FIELD_ACTIVE = "Active"


class BoardDirectoryPageAdminPage(ObjectAuthoringPage):
    """Composes the generic Object Authoring state machine (`ObjectAuthoringPage`)
    with the Board Directory Page object's own field map. Construct with just
    `page` (slug fixed to "board-directory-page")."""

    def __init__(self, page):
        super().__init__(page, SLUG)

    # ---- Validation detection — same 3 mechanisms as BoardMembersAdminPage
    # (identical Object Authoring framework; see this class's own module
    # docstring for the "reused, not independently re-confirmed for THIS
    # object's own fields" disclosure).
    FIELD_ERROR = "[data-qc-oel-field-error]"
    RECORD_NOT_SAVED_BANNER = '[data-qc-oel-editbar]:has-text("This record was not saved")'
    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    def _is_native_validation_blocked(self) -> bool:
        try:
            return bool(
                self.page.evaluate(
                    "() => !!document.querySelector('input:invalid, textarea:invalid, select:invalid')"
                )
            )
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible()'s never-throws contract
            return False

    def is_save_error_shown(self) -> bool:
        body_text = self.page.locator("body").inner_text()
        if self.SAVE_ERROR_BANNER_TEXT in body_text or self.INLINE_REQUIRED_TEXT in body_text:
            return True
        if self.page.locator(self.FIELD_ERROR).count() > 0:
            return True
        if self.is_visible(self.RECORD_NOT_SAVED_BANNER):
            return True
        return self._is_native_validation_blocked()

    def save_error_text(self) -> str:
        if self.page.locator(self.FIELD_ERROR).count() > 0:
            return self.page.locator(self.FIELD_ERROR).first.inner_text()
        if self.is_visible(self.RECORD_NOT_SAVED_BANNER):
            return self.text(self.RECORD_NOT_SAVED_BANNER)
        body_text = self.page.locator("body").inner_text()
        idx = body_text.find(self.SAVE_ERROR_BANNER_TEXT)
        if idx == -1:
            idx = body_text.find(self.INLINE_REQUIRED_TEXT)
        if idx != -1:
            return body_text[idx: idx + 120]
        try:
            return self.page.evaluate(
                "() => { const el = document.querySelector("
                "'input:invalid, textarea:invalid, select:invalid'); "
                "return el ? el.validationMessage : ''; }"
            ) or ""
        except Exception:  # noqa: BLE001
            return ""

    # ---- Navigation ---------------------------------------------------------
    def _ensure_logged_in(self) -> None:
        """Re-login-if-needed — mirrors BoardMembersAdminPage/
        OrgStructureAdminPage's identical pattern."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_main_entry(self) -> "BoardDirectoryPageAdminPage":
        """Opens the confirmed-live MAIN singleton entry (`MAIN_ENTRY_CODE`)
        by its own Entry-column code — the ONE entry this class's tests are
        ever allowed to touch (never the confirmed-stray "New Test" entry,
        never a newly-created one — see module docstring)."""
        self._ensure_logged_in()
        self.open_entry_by_code(MAIN_ENTRY_CODE)
        return self

    # ---- Field actions --------------------------------------------------------
    def set_field(self, field_label: str, value: str) -> "BoardDirectoryPageAdminPage":
        self.fill_text(field_label, value)
        return self

    def get_field(self, field_label: str) -> str:
        return self.field_value(field_label)

    def save(self) -> "BoardDirectoryPageAdminPage":
        """Maps to Object Authoring's "Submit for Publishing" — this surface
        has no single "Save" button, mirroring BoardMembersAdminPage.save()."""
        self.submit_for_publishing()
        return self

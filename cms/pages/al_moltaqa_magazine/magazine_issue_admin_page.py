"""
cms/pages/al_moltaqa_magazine/magazine_issue_admin_page.py —
MagazineIssueAdminPage.

Control_Panel Page Object for the per-record **Magazine Issue** Object
Authoring surface (PBI 130710, "QC - Insights & Media - 002 - Al-Moltqa
Magazine"). Composes `ObjectAuthoringPage` (cms/pages/components/) for the
generic Draft/Preview/Submit-for-Review/Delete state machine, per this
project's "Object Authoring Is the Only Path for Content Operations" rule —
field-level locators/quirks specific to THIS object live here.

Slug resolution (CLI-first, 2026-09-22, authenticated Playwright session via
`.auth/state.json`): read off the Objects Home left-nav panel exposed on any
`manage-<slug>` page (same technique export_report_admin_page.py's own
docstring documents) — confirmed live: `/web/qatar-chamber/manage-magazine-issue`
("Magazine Issue", per-record, page title "Manage: Magazine Issue"), 7 real
entries, externalReferenceCode QCDEMO-130710-ISSUE-001..007, ALL Published,
no leftover scratch rows.

**NO SEPARATE "Al-Moltaqa Magazine Page" ADMIN OBJECT EXISTS** — CONFIRMED
LIVE via an exhaustive read of the Objects Home nav panel's full link list
(278 unique `manage-*` links enumerated, filtered for "magazine"/"page"):
every other Insights & Media sibling PBI in this project (Export Reports,
Annual Reports) exposes a second, page-level singleton object
(`manage-export-report-page`, `manage-annual-reports-page`) alongside its
per-record object — Al-Moltaqa Magazine does NOT; only "Magazine Issue"
appears. This means every hero/archive-heading/search-placeholder string on
the public page (web/pages/al_moltaqa_magazine/al_moltaqa_magazine_page.py)
is confirmed hard-coded in the frontend, not CMS-driven, and any case
assuming a "Magazine Page" settings admin surface (Page Title EN/AR
save/validation — tc_144119/144120/144121/144206/144207/144208) is SKIPPED
in the test module with this exact finding — not a locator gap, a genuinely
absent admin surface.

CMS CHROME LOCALE — CONFIRMED LIVE FINDING: this session's `.auth/state.json`
(logged in as "Alaa Medhat") renders `manage-magazine-issue` with the ENTIRE
portal chrome AND this object's own field labels in ARABIC by default (e.g.
"عنوان العدد (EN)" instead of "Issue Title (EN)") — a real per-account
Control Panel UI-language preference, NOT a locator bug and NOT something
export_report_admin_page.py's own probes hit (that object's field labels
render in English regardless, because — per that class's own docstring —
no Arabic translation was ever authored for ITS Object Definition's field
labels, so it falls back to the English default even under an Arabic portal
chrome). Magazine Issue's Object Definition DOES carry real Arabic field-
label translations, so the same session renders it fully in Arabic. A
"EN"/"AR" content-language toggle button (confirmed-live, immediately above
the entries table) switches the WHOLE page's chrome+labels between the two;
clicking "EN" once per fresh navigation reliably yields the English labels
below (confirmed via a live before/after accessibility-tree snapshot diff).
`_ensure_english_chrome()` performs this on every `open_new_entry_form()` /
`open_entries_list()` call so every FIELD_* constant below (all authored in
English) resolves deterministically regardless of the account's own stored
locale preference.

Field labels — CONFIRMED LIVE via `page.accessibility.snapshot()` of the
mounted create-new form, AFTER clicking "EN":

    textbox    "Issue Title (EN) "           (trailing space IS part of the
                                              real accessible name, same
                                              finding as
                                              export_report_admin_page.py's
                                              own "Report Title " )
    textbox    "Issue Title (AR) "           (trailing space also present)
    textbox    "Issue Description (EN)"      (no trailing space)
    textbox    "Issue Description (AR)"
    textbox    "Issue Number"
    spinbutton "Page Count"
    spinbutton "Article Count"
    textbox    "dd/mm/yyyy"                  (the Issue Date field — CONFIRMED
                                              LIVE its own accessible name IS
                                              its placeholder text, not a
                                              "Issue Date" label; used
                                              directly as the field_label
                                              argument to type_date())
    button     "Select File" (x2: Issue Cover Image, PDF Attachment)
    textbox    "Issue Cover Image Select File" / "Issue Cover Image" (filename
               readout)
    textbox    "PDF Attachment Select File" / "PDF Attachment"
    combobox   "Active Status " (trailing space — CONFIRMED LIVE only ONE
               "Open Options Menu" button exists on this form, unlike
               export_report_admin_page.py's THREE-button ambiguity — no
               Y-bounding-box scoping is strictly required here, but the
               same scoped-xpath option-match technique is reused anyway for
               consistency and because a future field addition could
               reintroduce the ambiguity)
    checkbox   "Open in New Tab" (CONFIRMED LIVE present on the form; default
               state not independently re-verified this session — tc_144152
               asserts on it directly)
    button     "Save as Draft" (CONFIRMED LIVE this stays in ENGLISH even
               under the Arabic-chrome session — a custom Object Authoring
               fragment string, not a Liferay-translated one)
    button     "Submit for Review" (CONFIRMED LIVE this object's own submit
               wording after the EN toggle — matches Export Report's
               "Submit for Review", NOT the QA cases' own literal
               "Publish"/"Unpublish" wording. Per-row actions carry a
               genuine "Unpublish" action too (composed via
               ObjectAuthoringPage.unpublish_to_edit_as_draft(), whose own
               button text is "Unpublish to edit as draft") — the mismatch
               is specifically that there is no single button literally
               labelled "Publish": publishing an issue is
               `set_active_status("Published")` + `submit_for_review()`,
               mirroring export_report_admin_page.py's and
               publication_admin_page.py's identical two-step convention.)

ENTRY COLUMN IS A CODE, NOT THE TITLE — CONFIRMED LIVE 2026-09-22 (checked
fresh per the task's own instruction, since Annual Reports/Export Reports
have this defect and Publications does NOT): the real entries-list Entry
column renders `QCDEMO-130710-ISSUE-00N` (an externalReferenceCode-style
identifier), never the Issue Title — reproduced by reading every row's own
Entry cell text back directly (all 7 real rows show this code pattern, no
row shows a Title string). Every title-based method below therefore
resolves the REAL Entry-column code first via
`ObjectAuthoringPage.find_entry_code_by_field()` (verified by opening the
row and reading its own Issue Title EN back — never a positional/row-order
guess, per standards.md's "Destructive Operations Against qcdev" rule), with
the same newest-row-hint-first-then-verify performance shortcut
export_report_admin_page.py's own `_resolve_code()` already established.

TEST-DATA POLICY (cms-profile.md): every write this class makes is against
a brand-new `QCTEST-`-prefixed DISPOSABLE entry — never one of the 7 real,
shared `QCDEMO-130710-ISSUE-*` rows. `create_disposable_entry()` /
`delete_entry_by_title()` are the create->act->delete-in-finally shape every
mutating test in this batch's Control_Panel/dual-platform module composes.
"""

from core.web.base_page import BasePage
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url

SLUG = "magazine-issue"

FIELD_ISSUE_TITLE_EN = "Issue Title (EN) "  # CONFIRMED LIVE: trailing space is real
FIELD_ISSUE_TITLE_AR = "Issue Title (AR) "
FIELD_ISSUE_DESCRIPTION_EN = "Issue Description (EN)"
FIELD_ISSUE_DESCRIPTION_AR = "Issue Description (AR)"
FIELD_ISSUE_NUMBER = "Issue Number"
FIELD_PAGE_COUNT = "Page Count"
FIELD_ARTICLE_COUNT = "Article Count"
FIELD_ISSUE_DATE = "dd/mm/yyyy"  # CONFIRMED LIVE: the field's own accessible name IS its placeholder
FIELD_COVER_IMAGE = "Issue Cover Image"
FIELD_PDF_ATTACHMENT = "PDF Attachment"
FIELD_ACTIVE_STATUS = "Active Status "
FIELD_OPEN_IN_NEW_TAB = "Open in New Tab"

SUBMIT_FOR_REVIEW_BUTTON = 'button:has-text("Submit for Review")'
OPEN_OPTIONS_MENU_BUTTON = "Open Options Menu"
EN_TOGGLE_BUTTON = "EN"


def _xpath_literal(value: str) -> str:
    """Safe XPath string literal (same helper export_report_admin_page.py
    already uses) — handles a value containing a literal `'` via
    concatenation, the standard XPath 1.0 workaround."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"


class MagazineIssueAdminPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, SLUG)

    # ---- Chrome-locale normalization (see module docstring) -----------------
    def _ensure_english_chrome(self) -> None:
        """Best-effort: click the "EN" content-language toggle if the page
        happens to have loaded in Arabic chrome (this account's stored
        preference — see module docstring). Never raises: if the toggle is
        already English (or absent on a given render), this is a no-op."""
        try:
            btn = self.page.get_by_role("button", name=EN_TOGGLE_BUTTON, exact=True).first
            if btn.is_visible(timeout=2000):
                btn.click(timeout=2000)
                self.page.wait_for_timeout(800)
        except Exception:  # noqa: BLE001 — best-effort chrome normalization only
            pass

    # ---- Navigation (delegates to the shared state machine) ---------------
    def open_new_entry_form(self) -> "MagazineIssueAdminPage":
        self.authoring.open_new_entry_form()
        self._ensure_english_chrome()
        return self

    def open_entries_list(self) -> "MagazineIssueAdminPage":
        self.authoring.open_entries_list()
        self._ensure_english_chrome()
        return self

    # See module docstring's "Entry column is a code, not the title" note.
    def _resolve_code(self, title: str) -> str:
        """Cheap newest-row-hint-first, then fall back to the full,
        verified, non-positional scan — mirrors
        export_report_admin_page.py's own `_resolve_code()` exactly (same
        rationale: the hint is NEVER trusted without reading the row's own
        Issue Title EN back first)."""
        self.authoring.open_entries_list()
        self._ensure_english_chrome()
        hint_code = self.authoring.newest_entry_code()
        if hint_code:
            try:
                self.authoring.open_entry_by_code(hint_code)
                self._ensure_english_chrome()
                if self.page.get_by_role(
                    "textbox", name=FIELD_ISSUE_TITLE_EN, exact=True
                ).input_value() == title:
                    return hint_code
            except Exception:  # noqa: BLE001 — hint failed to verify, fall back below
                pass
        return self.authoring.find_entry_code_by_field(FIELD_ISSUE_TITLE_EN, title)

    def open_entry_by_edit_link(self, title: str) -> "MagazineIssueAdminPage":
        code = self._resolve_code(title)
        if not code:
            raise RuntimeError(
                f"No Magazine Issue entry found with Issue Title (EN) == {title!r} "
                "(resolved via find_entry_code_by_field, not a row-text match)."
            )
        self.authoring.open_entry_by_code(code)
        self._ensure_english_chrome()
        return self

    def delete_entry_by_title(self, title: str) -> bool:
        code = self._resolve_code(title)
        if not code:
            return False
        self.open_entries_list()
        return self.authoring.delete_entry_by_code(code)

    # ---- Field access -------------------------------------------------------
    def fill_text(self, field_label: str, value: str) -> "MagazineIssueAdminPage":
        self.authoring.fill_text(field_label, value)
        return self

    def field_value(self, field_label: str) -> str:
        """Textbox read-back — does NOT resolve Page Count/Article Count
        (those render as `spinbutton`, see number_field_value())."""
        return self.authoring.field_value(field_label)

    def number_field_value(self, field_label: str) -> str:
        return self.page.get_by_role("spinbutton", name=field_label, exact=True).input_value()

    def fill_number(self, field_label: str, value: str) -> "MagazineIssueAdminPage":
        self.authoring.fill_number(field_label, value)
        return self

    def set_issue_date(self, value: str) -> "MagazineIssueAdminPage":
        self.authoring.type_date(FIELD_ISSUE_DATE, value)
        return self

    def issue_date_value(self) -> str:
        return self.page.get_by_role("textbox", name=FIELD_ISSUE_DATE, exact=True).input_value()

    def set_open_in_new_tab(self, checked: bool) -> "MagazineIssueAdminPage":
        self.authoring.set_checkbox(FIELD_OPEN_IN_NEW_TAB, checked)
        return self

    def is_open_in_new_tab_checked(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_OPEN_IN_NEW_TAB, exact=True).is_checked()

    def upload_file(self, field_label: str, file_path: str) -> "MagazineIssueAdminPage":
        self.authoring.upload_file(field_label, file_path)
        return self

    def upload_file_expect_rejected(self, field_label: str, file_path: str) -> bool:
        return self.authoring.upload_file_expect_rejected(field_label, file_path)

    def uploaded_filename(self, field_label: str) -> str:
        return self.authoring.uploaded_filename(field_label)

    def field_length_rejected(self, field_label: str, attempted: str, limit: int) -> bool:
        """OVERRIDDEN (not delegated to `ObjectAuthoringPage.field_length_rejected()`)
        — CONFIRMED LIVE 2026-09-22: the shared base method's submit-time
        fallback branch calls `self.submit_for_publishing()` ("Submit for
        Publishing" wording), which does not exist on this object's real
        form ("Submit for Review") — a live run against
        `test_issue_title_en_200_boundary` reproduced this exactly (30s
        `TimeoutError` on `button:has-text("Submit for Publishing")` after
        the 201-character input was accepted without client-side
        truncation). Reimplemented here with the identical two-branch logic
        but calling THIS object's own `submit_for_review()` in the
        fallback, so the same case is verifiable without inheriting the
        base class's wording mismatch — mirrors the same override already
        applied to `submit_for_review()` itself."""
        self.fill_text(field_label, attempted)
        if len(self.field_value(field_label)) <= limit:
            return True
        self.submit_for_review()
        return self.status_for_current_form() != "Published"

    def status_for_current_form(self) -> str:
        """Best-effort read of the CURRENTLY OPEN form's own persisted
        Active Status, without navigating away — used by
        `field_length_rejected()`'s fallback branch so it never needs a
        title to look up (the record may not even have a resolvable title
        yet if the over-limit fill was on the Title field itself)."""
        try:
            return self.active_status_value()
        except Exception:  # noqa: BLE001 — best-effort; a blocked submit may
            # never have rendered a resolvable Active Status control if the
            # workflow-level rejection banner replaced the form outright.
            return self.BLOCKED_MESSAGE if self.submit_blocked() else "Unknown"

    # ---- Scoped dropdown selection (see module docstring's single-button
    # note — kept scoped anyway for consistency/future-proofing) --------------
    def _select_dropdown_option(self, field_label: str, option_label: str) -> None:
        combo = self.page.get_by_role("combobox", name=field_label, exact=True).first
        combo_box = combo.bounding_box()
        menu_buttons = self.page.get_by_role("button", name=OPEN_OPTIONS_MENU_BUTTON)
        best_index, best_dy = 0, float("inf")
        for i in range(menu_buttons.count()):
            btn_box = menu_buttons.nth(i).bounding_box()
            if btn_box is None:
                continue
            dy = abs(btn_box["y"] - combo_box["y"]) if combo_box else 0
            if dy < best_dy:
                best_dy, best_index = dy, i
        menu_buttons.nth(best_index).click()
        option = self.page.locator(
            f"xpath=//li[@role='option'][normalize-space(text())={_xpath_literal(option_label)}]"
        ).first
        option.wait_for(state="visible", timeout=5000)
        option.click()

    def set_active_status(self, option_label: str) -> "MagazineIssueAdminPage":
        self._select_dropdown_option(FIELD_ACTIVE_STATUS, option_label)
        return self

    def active_status_value(self) -> str:
        combo = self.page.get_by_role("combobox", name=FIELD_ACTIVE_STATUS, exact=True).first
        return combo.evaluate("el => el.value || el.textContent")

    # ---- Lifecycle ------------------------------------------------------------
    def save_as_draft(self) -> "MagazineIssueAdminPage":
        self.authoring.save_as_draft()
        return self

    def submit_for_review(self) -> "MagazineIssueAdminPage":
        """This object's own confirmed-live wording — "Submit for Review",
        not ObjectAuthoringPage's default "Submit for Publishing"."""
        self.click(SUBMIT_FOR_REVIEW_BUTTON)
        self.authoring._wait_for_settle()
        return self

    def publish(self) -> "MagazineIssueAdminPage":
        """Convenience composing the real two-step publish flow this
        object actually exposes (see module docstring's "no single Publish
        button" finding): set the Active Status business field to
        "Published", then submit the workflow action."""
        self.set_active_status("Published")
        self.submit_for_review()
        return self

    BLOCKED_MESSAGE = "Please complete the required fields"

    def submit_blocked(self) -> bool:
        return self.BLOCKED_MESSAGE in self.page.locator("body").inner_text()

    def page_body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def status_for(self, title: str) -> str:
        code = self._resolve_code(title)
        if not code:
            return ""
        return self.authoring.row_status_text_by_code(code)

    def editing_banner_text(self) -> str:
        return self.authoring.editing_banner_text()

    def is_save_as_draft_disabled(self) -> bool:
        return self.authoring.is_save_as_draft_disabled()

    def unpublish_to_edit_as_draft(self) -> "MagazineIssueAdminPage":
        self.authoring.unpublish_to_edit_as_draft()
        return self

    # ---- List / row state (title resolved to its real code first) ----------
    def row_visible(self, title: str) -> bool:
        code = self._resolve_code(title)
        if not code:
            return False
        self.open_entries_list()
        return self.authoring.row_visible_by_code(code)

    def row_status_text(self, title: str) -> str:
        code = self._resolve_code(title)
        if not code:
            return ""
        self.open_entries_list()
        return self.authoring.row_status_text_by_code(code)

    def row_preview_url(self, title: str) -> str:
        code = self._resolve_code(title)
        if not code:
            return ""
        self.open_entries_list()
        return self.authoring.row_preview_url_by_code(code)

    # ---- Disposable-entry convenience (DISPOSABLE per cms-profile.md) -------
    def create_disposable_entry(self, prefix: str, **overrides) -> dict:
        """Creates a brand-new `QCTEST-<prefix>`-titled Magazine Issue entry
        with every mandatory field filled to a safe default (Save as Draft
        only — callers that need it published call publish()/
        submit_for_review() themselves). `overrides` keys are the literal
        FIELD_* string values (or the bare keywords `issue_date`,
        `page_count`, `article_count`, `open_in_new_tab`, `skip_cover`,
        `skip_pdf`, `skip_status` for the non-textbox fields), mirroring
        export_report_admin_page.py's own convention."""
        values = {
            FIELD_ISSUE_TITLE_EN: f"QCTEST-{prefix} Magazine Issue",
            FIELD_ISSUE_TITLE_AR: f"QCTEST-{prefix} عدد المجلة",
            FIELD_ISSUE_DESCRIPTION_EN: f"QCTEST-{prefix} disposable automated-test issue description.",
            FIELD_ISSUE_DESCRIPTION_AR: f"QCTEST-{prefix} وصف عدد تجريبي تم إنشاؤه تلقائيًا.",
            FIELD_ISSUE_NUMBER: f"QCTEST-{prefix}",
        }
        values.update(overrides)
        self.open_new_entry_form()
        for field in (FIELD_ISSUE_TITLE_EN, FIELD_ISSUE_TITLE_AR,
                      FIELD_ISSUE_DESCRIPTION_EN, FIELD_ISSUE_DESCRIPTION_AR,
                      FIELD_ISSUE_NUMBER):
            if field in values:
                self.fill_text(field, values[field])
        if values.get("page_count"):
            self.fill_number(FIELD_PAGE_COUNT, values["page_count"])
        if values.get("article_count"):
            self.fill_number(FIELD_ARTICLE_COUNT, values["article_count"])
        if values.get("issue_date"):
            self.set_issue_date(values["issue_date"])
        if not values.get("skip_cover"):
            self.upload_file(FIELD_COVER_IMAGE, values.get("cover_path", "cms/tests/al_moltaqa_magazine/fixtures/valid_cover_1_5mb.jpg"))
        if not values.get("skip_pdf"):
            self.upload_file(FIELD_PDF_ATTACHMENT, values.get("pdf_path", "cms/tests/al_moltaqa_magazine/fixtures/valid_pdf_4mb.pdf"))
        if values.get("open_in_new_tab") is not None:
            self.set_open_in_new_tab(values["open_in_new_tab"])
        if not values.get("skip_status"):
            self.set_active_status("Published")
        return values

    def publish_disposable_entry(self, prefix: str, **overrides) -> dict:
        values = self.create_disposable_entry(prefix, **overrides)
        self.submit_for_review()
        return values

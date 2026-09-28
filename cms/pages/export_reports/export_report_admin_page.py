"""
cms/pages/export_reports/export_report_admin_page.py — ExportReportAdminPage.

Control_Panel Page Object for the per-record **Export Report** Object
Authoring surface (PBI 131313, "QC - Insights & Media - 003 D - Private
Sector Export Reports"). Composes `ObjectAuthoringPage` (cms/pages/components/)
for the generic Draft/Preview/Submit-for-Review/Delete state machine, per
this project's "Object Authoring Is the Only Path for Content Operations"
rule — field-level locators/quirks specific to THIS object live here.

Slug resolution (CLI-first, 2026-09-22, authenticated Playwright session via
`.auth/state.json`): read off `manage-ann-rpt`'s own "Objects Home"
navigation panel (every `manage-<slug>` page on this Liferay instance lists
every other object's real slug in its own left nav) — same technique
`annual_report_admin_page.py`'s own docstring documents. Confirmed live:
`/web/qatar-chamber/manage-export-report` ("Export Report", per-record) and
`/web/qatar-chamber/manage-export-report-page` ("Export Report Page",
page-level singleton — see `export_reports_page_admin_page.py`). Page
title "Manage: Export Report", 10 real entries, externalReferenceCode
QCDEMO-131313-ER-001..010, ALL Published, no leftover scratch rows (cleaner
than annual_report_admin_page.py's own data set).

Field labels — CONFIRMED LIVE via `page.accessibility.snapshot()` of the
mounted create-new form:

    textbox    "Report Title "                    (EN, required — CONFIRMED
                                                    LIVE trailing space is
                                                    part of the real
                                                    accessible name)
    textbox    "Report Title — العربية *"          (AR, required — trailing
                                                    " *" IS part of the real
                                                    accessible name, same
                                                    finding as
                                                    annual_report_admin_page.py)
    textbox    "Report Description"                (EN, required)
    textbox    "Report Description — العربية"      (AR — CONFIRMED LIVE this
                                                    one does NOT carry a
                                                    trailing " *", unlike
                                                    Report Title AR; not
                                                    independently re-verified
                                                    whether it is still
                                                    server-side required)
    button     "Select File" (x2: Cover Thumbnail, PDF Attachment)
    textbox    "Cover Thumbnail Select File" / "Cover Thumbnail" (filename readout)
    textbox    "PDF Attachment Select File" / "PDF Attachment"
    combobox   "Quarter" (Q1/Q2/Q3/Q4 — CONFIRMED LIVE options, opened via
               its own "Open Options Menu" button, NOT `get_by_role("button",
               name="Open Options Menu").click()` alone: this form renders
               THREE such buttons (Quarter, Publication Month, Active
               Status), so the unscoped click that works on simpler single-
               dropdown objects raises a strict-mode violation here. Scoped
               by Y-bounding-box proximity to the target combobox — see
               `_select_dropdown_option()` below.)
    spinbutton "Reporting Year"
    combobox   "Publication Month" (January..December — CONFIRMED LIVE)
    spinbutton "Publication Year"
    spinbutton "Page Count"
    combobox   "Active Status" (Draft/Published/Unpublished — CONFIRMED
               LIVE; this is the object's own business-status field, NOT
               the workflow Draft/Approved state — mirrors
               `annual_report_admin_page.py`'s identical distinction)
    spinbutton "Display Order" (present on the form; no case in this
               batch exercises it, not modelled as a FIELD_* constant)
    button     "Save as Draft"
    button     "Submit for Review" (CONFIRMED LIVE this object's own submit
               wording, same as Annual Report — NOT ObjectAuthoringPage's
               default "Submit for Publishing")

TEST-DATA POLICY (cms-profile.md): every write this class makes is against
a brand-new `QCTEST-`-prefixed DISPOSABLE entry — never one of the 10 real,
shared `QCDEMO-131313-ER-*` rows. `create_disposable_entry()` /
`delete_entry_by_title()` are the create->act->delete-in-finally shape
every mutating test in this batch's Control_Panel/dual-platform module
composes.
"""

from core.web.base_page import BasePage
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url

SLUG = "export-report"

FIELD_REPORT_TITLE_EN = "Report Title "  # CONFIRMED LIVE: trailing space is real
FIELD_REPORT_TITLE_AR = "Report Title — العربية *"
FIELD_REPORT_DESCRIPTION_EN = "Report Description"
FIELD_REPORT_DESCRIPTION_AR = "Report Description — العربية"
FIELD_COVER_THUMBNAIL = "Cover Thumbnail"
FIELD_QUARTER = "Quarter"
FIELD_REPORTING_YEAR = "Reporting Year"
FIELD_PUBLICATION_MONTH = "Publication Month"
FIELD_PUBLICATION_YEAR = "Publication Year"
FIELD_PAGE_COUNT = "Page Count"
FIELD_PDF_ATTACHMENT = "PDF Attachment"
FIELD_ACTIVE_STATUS = "Active Status"

SUBMIT_FOR_REVIEW_BUTTON = 'button:has-text("Submit for Review")'
OPEN_OPTIONS_MENU_BUTTON = "Open Options Menu"


def _xpath_literal(value: str) -> str:
    """Safe XPath string literal — handles a value containing a literal
    `'` (none of this object's own option labels do, but this stays
    correct if that ever changes) by concatenating single- and
    double-quoted segments, the standard XPath 1.0 workaround (XPath has
    no string-escape syntax of its own)."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"


class ExportReportAdminPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, SLUG)

    # ---- Navigation (delegates to the shared state machine) ---------------
    def open_new_entry_form(self) -> "ExportReportAdminPage":
        self.authoring.open_new_entry_form()
        return self

    def open_entries_list(self) -> "ExportReportAdminPage":
        self.authoring.open_entries_list()
        return self

    # CONFIRMED LIVE 2026-09-22 (live incident during this batch's own
    # verification run — see this class's module-level note in the test
    # module's docstring): this object's own entries-list Entry column
    # renders an internal UUID, NEVER the row's Report Title — reproduced
    # 3 times back to back (a title-based `table tbody tr:has-text(title)`
    # lookup never matches any row, hanging the full click-wait timeout
    # every time, not a propagation lag a retry could paper over). Same
    # class of defect standards.md already documents for
    # manage-strategic-pillar-card. Every title-based method below
    # resolves the REAL Entry-column code first via the shared, verified,
    # non-positional `ObjectAuthoringPage.find_entry_code_by_field()`
    # lookup (opens each existing row's own form and reads its Report
    # Title back, never assumes row order/position — the exact discipline
    # standards.md's "Destructive Operations Against qcdev" incident
    # requires), then delegates to the `_by_code` sibling methods. Slower
    # (one navigation per existing row until a match) than a direct title-
    # column match, but correct; existing test call sites are unaffected
    # since the public method signatures are unchanged.
    def _resolve_code(self, title: str) -> str:
        """Performance note (added after live timing on this batch's own
        verification run — the full find_entry_code_by_field() scan took
        ~30s+ against the 10 real + N QCTEST rows on this object): tries
        the positional "newest row" first as a cheap HINT ONLY — but,
        exactly per standards.md's Destructive Operations rule, NEVER
        trusts that position; it is verified by reading the row's own
        Report Title back before ever being returned/used. Every disposable
        test entry created by this batch IS the newest row at the point its
        own code is resolved (created, then immediately looked up, never
        interleaved with another entry's creation within one test), so this
        hint hits in the common case and turns a ~30s scan into ~2-4s;
        falls back to the full, safe, exhaustive scan whenever the hint
        doesn't match (or no rows exist), which remains fully correct."""
        self.authoring.open_entries_list()
        hint_code = self.authoring.newest_entry_code()
        if hint_code:
            try:
                self.authoring.open_entry_by_code(hint_code)
                if self.page.get_by_role(
                    "textbox", name=FIELD_REPORT_TITLE_EN, exact=True
                ).input_value() == title:
                    return hint_code
            except Exception:  # noqa: BLE001 — hint failed to verify, fall back below
                pass
        return self.authoring.find_entry_code_by_field(FIELD_REPORT_TITLE_EN, title)

    def open_entry_by_edit_link(self, title: str) -> "ExportReportAdminPage":
        code = self._resolve_code(title)
        if not code:
            raise RuntimeError(
                f"No Export Report entry found with Report Title == {title!r} "
                "(resolved via find_entry_code_by_field, not a row-text match)."
            )
        self.authoring.open_entry_by_code(code)
        return self

    def delete_entry_by_title(self, title: str) -> bool:
        code = self._resolve_code(title)
        if not code:
            return False
        # find_entry_code_by_field() leaves the browser on the matched
        # entry's own EDIT page; delete_entry_by_code() needs the LIST page
        # (it queries the row's own delete link).
        self.open_entries_list()
        return self.authoring.delete_entry_by_code(code)

    # ---- Field access -------------------------------------------------------
    def fill_text(self, field_label: str, value: str) -> "ExportReportAdminPage":
        self.authoring.fill_text(field_label, value)
        return self

    def field_value(self, field_label: str) -> str:
        """Textbox read-back — CONFIRMED LIVE this does NOT resolve
        Reporting Year / Publication Year / Page Count (those render as
        `spinbutton`, not `textbox` — ObjectAuthoringPage.field_value()
        queries `role="textbox"` only, a 0-match timeout on a spinbutton
        field). Use number_field_value() for those three instead."""
        return self.authoring.field_value(field_label)

    def number_field_value(self, field_label: str) -> str:
        """Read-back counterpart to fill_number() — Reporting Year,
        Publication Year, and Page Count all render as `spinbutton`, which
        ObjectAuthoringPage.field_value()'s hard-coded `role="textbox"`
        query never matches (CONFIRMED LIVE 2026-09-22 as a 0-match
        timeout before this method was added)."""
        return self.page.get_by_role("spinbutton", name=field_label, exact=True).input_value()

    def fill_number(self, field_label: str, value: str) -> "ExportReportAdminPage":
        self.authoring.fill_number(field_label, value)
        return self

    def upload_file(self, field_label: str, file_path: str) -> "ExportReportAdminPage":
        self.authoring.upload_file(field_label, file_path)
        return self

    def upload_file_expect_rejected(self, field_label: str, file_path: str) -> bool:
        return self.authoring.upload_file_expect_rejected(field_label, file_path)

    def uploaded_filename(self, field_label: str) -> str:
        return self.authoring.uploaded_filename(field_label)

    def field_length_rejected(self, field_label: str, attempted: str, limit: int) -> bool:
        """KNOWN LIMITATION (not fixed here, mirrors annual_report_admin_page.py's
        own identical note): the shared base method's submit-time fallback
        branch calls `self.submit_for_publishing()` (button text "Submit
        for Publishing"), which does not match this object's real "Submit
        for Review" wording. The immediate-readback truncation branch is
        sound and unaffected; only the fallback inherits the mismatch, and
        only if truncation does not fire first."""
        return self.authoring.field_length_rejected(field_label, attempted, limit)

    # ---- Scoped dropdown selection (see module docstring's "Open Options
    # Menu" ambiguity note) ---------------------------------------------------
    def _select_dropdown_option(self, field_label: str, option_label: str) -> None:
        combo = self.page.get_by_role("combobox", name=field_label, exact=True).first
        combo_box = combo.bounding_box()
        menu_buttons = self.page.get_by_role("button", name=OPEN_OPTIONS_MENU_BUTTON)
        best_index, best_dy = 0, float("inf")
        for i in range(menu_buttons.count()):
            btn_box = menu_buttons.nth(i).bounding_box()
            if btn_box is None:
                continue
            dy = abs(btn_box["y"] - combo_box["y"])
            if dy < best_dy:
                best_dy, best_index = dy, i
        menu_buttons.nth(best_index).click()
        # CONFIRMED LIVE 2026-09-22: the real, opened custom dropdown
        # renders its options as `<li role="option">`, but this surface
        # ALSO carries a hidden native `<select>` (the list's own Status
        # filter) whose plain `<option>` elements share the SAME
        # accessibility role/name for any overlapping label (e.g.
        # "Published" is a real option text on both the Active Status
        # field and the filter's Status <select>) — an unscoped
        # `get_by_role("option", name=...)` hits a strict-mode 2-element
        # violation for exactly those overlapping labels. Scoped to the
        # real, visible custom-dropdown `<li>` element only.
        # Exact text match (XPath normalize-space) -- has_text=... alone
        # would substring-match "Published" inside "Unpublished".
        option = self.page.locator(
            f"xpath=//li[@role='option'][normalize-space(text())={_xpath_literal(option_label)}]"
        ).first
        option.wait_for(state="visible", timeout=5000)
        option.click()

    def select_quarter(self, quarter: str) -> "ExportReportAdminPage":
        self._select_dropdown_option(FIELD_QUARTER, quarter)
        return self

    def select_publication_month(self, month: str) -> "ExportReportAdminPage":
        self._select_dropdown_option(FIELD_PUBLICATION_MONTH, month)
        return self

    def set_active_status(self, option_label: str) -> "ExportReportAdminPage":
        self._select_dropdown_option(FIELD_ACTIVE_STATUS, option_label)
        return self

    def quarter_value(self) -> str:
        combo = self.page.get_by_role("combobox", name=FIELD_QUARTER, exact=True).first
        return combo.evaluate("el => el.value || el.textContent")

    def publication_month_value(self) -> str:
        combo = self.page.get_by_role("combobox", name=FIELD_PUBLICATION_MONTH, exact=True).first
        return combo.evaluate("el => el.value || el.textContent")

    # ---- Lifecycle ------------------------------------------------------------
    def save_as_draft(self) -> "ExportReportAdminPage":
        self.authoring.save_as_draft()
        return self

    def submit_for_review(self) -> "ExportReportAdminPage":
        """This object's own confirmed-live wording — "Submit for Review",
        not ObjectAuthoringPage's default "Submit for Publishing"."""
        self.click(SUBMIT_FOR_REVIEW_BUTTON)
        self.authoring._wait_for_settle()
        return self

    BLOCKED_MESSAGE = "Please complete the required fields"
    ARABIC_REQUIRED_MESSAGE = "Arabic content is required."
    UNSUPPORTED_FILE_MESSAGE = "Unsupported file type or size."

    def submit_blocked(self) -> bool:
        return self.BLOCKED_MESSAGE in self.page.locator("body").inner_text()

    def page_body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def status_for(self, title: str) -> str:
        """Reopens the entries list and reads `title`'s own row status —
        mirrors annual_report_admin_page.py's identical status_for()/
        submit_blocked() convention for objects whose Save/Submit redirect
        gives current_status() no `?editEntry=` banner to read afterward."""
        self.open_entries_list()
        return self.row_status_text(title)

    def editing_banner_text(self) -> str:
        return self.authoring.editing_banner_text()

    def is_save_as_draft_disabled(self) -> bool:
        return self.authoring.is_save_as_draft_disabled()

    def unpublish_to_edit_as_draft(self) -> "ExportReportAdminPage":
        self.authoring.unpublish_to_edit_as_draft()
        return self

    # ---- List / row state (title resolved to its real code first — see
    # the Entry-column-is-a-UUID note above open_entry_by_edit_link()) -------
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

    def row_last_modified(self, title: str) -> str:
        code = self._resolve_code(title)
        if not code:
            return ""
        self.open_entries_list()
        return self.page.locator(
            f'table tbody tr:has-text("{code}") td'
        ).nth(2).inner_text()

    # ---- Disposable-entry convenience (DISPOSABLE per cms-profile.md) -------
    def create_disposable_entry(self, prefix: str, **overrides) -> dict:
        """Creates a brand-new `QCTEST-<prefix>`-titled Export Report entry
        with every mandatory field filled to a safe default (Save as Draft
        only — callers that need it published call submit_for_review()
        themselves). `overrides` keys are the literal FIELD_* string values
        (or the bare keywords `quarter`, `reporting_year`, `publication_month`,
        `publication_year`, `page_count`, `skip_cover`, `skip_pdf`,
        `skip_status` for the non-textbox fields), mirroring
        annual_report_admin_page.py's own convention."""
        values = {
            FIELD_REPORT_TITLE_EN: f"QCTEST-{prefix} Export Report",
            FIELD_REPORT_TITLE_AR: f"QCTEST-{prefix} تقرير تصدير",
            FIELD_REPORT_DESCRIPTION_EN: f"QCTEST-{prefix} disposable automated-test report description.",
            FIELD_REPORT_DESCRIPTION_AR: f"QCTEST-{prefix} وصف تقرير تجريبي تم إنشاؤه تلقائيًا.",
        }
        values.update(overrides)
        self.open_new_entry_form()
        for field in (FIELD_REPORT_TITLE_EN, FIELD_REPORT_TITLE_AR,
                      FIELD_REPORT_DESCRIPTION_EN, FIELD_REPORT_DESCRIPTION_AR):
            if field in values:
                self.fill_text(field, values[field])
        if not values.get("skip_cover"):
            self.upload_file(FIELD_COVER_THUMBNAIL, values.get("cover_path", "cms/tests/export_reports/fixtures/valid_cover_1_5mb.jpg"))
        if values.get("quarter"):
            self.select_quarter(values["quarter"])
        if values.get("reporting_year"):
            self.fill_number(FIELD_REPORTING_YEAR, values["reporting_year"])
        if values.get("publication_month"):
            self.select_publication_month(values["publication_month"])
        if values.get("publication_year"):
            self.fill_number(FIELD_PUBLICATION_YEAR, values["publication_year"])
        if values.get("page_count"):
            self.fill_number(FIELD_PAGE_COUNT, values["page_count"])
        if not values.get("skip_pdf"):
            self.upload_file(FIELD_PDF_ATTACHMENT, values.get("pdf_path", "cms/tests/export_reports/fixtures/valid_pdf_4mb.pdf"))
        if not values.get("skip_status"):
            self.set_active_status("Published")
        return values

"""
cms/pages/annual_reports/annual_report_admin_page.py — AnnualReportAdminPage.

Control_Panel Page Object for the per-record **Annual Report** Object
Authoring surface (PBI 130712, "QC - Insights & Media - 004 - Annual
Reports"). Composes `ObjectAuthoringPage` (cms/pages/components/) for the
generic Draft/Preview/Submit-for-Review/Delete state machine, per this
project's standing "Object Authoring Is the Only Path for Content
Operations" rule — field-level locators/quirks specific to THIS object live
here, never duplicated into ObjectAuthoringPage itself.

Slug resolution (CLI-first, 2026-09-22, authenticated Playwright session,
`.auth/state.json` refreshed live this session via a direct CmsLoginPage
flow after the cached one had gone stale): naive guesses
(`manage-annual-report(s)`, `manage-report`, ...) all 404 into the generic
"Coming Soon" shell. The real slug was read off the **Annual Reports Page**
object's own "Objects Home" navigation panel (every object on this Liferay
instance is listed there) — its "Annual Report" entry's real `href` is
`/web/qatar-chamber/manage-ann-rpt`, an abbreviated slug with no discoverable
naming pattern from the object's display name alone. Confirmed live: page
title "Manage: Annual Report", 12 real entries (6 real published
`Annual Report <year>` rows for 2020-2025, PLUS 6 unrelated `UNPUBLISHED`
garbage rows — "ddddddddddddddd", "wwwwwww", etc., created 2026-09-20,
evidently leftover scratch data from an earlier interrupted session; NOT
touched by this batch — flagged to the user, not deleted, per this
project's destructive-ops confirmation rule).

Field labels — CONFIRMED LIVE via a Playwright accessibility-tree snapshot
of the create-new form (`page.accessibility.snapshot()`, not the static
extractor, since these fields only exist inside the mounted form the same
way object_authoring_page.py's own module docstring already documents for
every other Object Authoring surface):

    textbox  "Report Title"                  (EN, required)
    textbox  "Report Title — العربية *"       (AR, required — CONFIRMED LIVE:
                                               only the AR half of each
                                               bilingual pair carries a
                                               literal trailing " *" in its
                                               OWN accessible name; the EN
                                               half does not. This is
                                               required-field content, not
                                               whitespace Playwright's
                                               `exact=True` name matching
                                               trims — dropping it from the
                                               FIELD_* constant produces a
                                               real 0-match `get_by_role()`
                                               timeout, reproduced live
                                               2026-09-22 before this
                                               constant was corrected to
                                               include it.)
    textbox  "Report Description"            (EN, required)
    textbox  "Report Description — العربية *" (AR, required — same trailing
                                               " *" note as Report Title AR)
    button   "Select File" (x2: Cover Image, PDF Attachment)
    textbox  "Report Cover Image Select File" (hidden filename box, EN Cover Image)
    textbox  "Report Cover Image"             (filename readout)
    spinbutton "Publication Year"
    textbox  "dd/mm/yyyy"                    (Publication Date — NO real
                                               accessible label of its own;
                                               the placeholder IS the
                                               computed accessible name,
                                               confirmed live, hence
                                               PUBLICATION_DATE_INPUT below
                                               is a dedicated placeholder
                                               locator, not FIELD_* + fill_text)
    spinbutton "Page Count"
    textbox  "PDF Attachment Select File"
    textbox  "PDF Attachment"
    combobox "Status"                        (the entry's own "Active
                                               Status" business field — NOT
                                               the workflow Draft/Approved
                                               state, which this surface
                                               drives via Save-as-Draft/
                                               Submit-for-Review instead.
                                               CONFLICT: the entries-LIST's
                                               own filter panel ALSO renders
                                               a combobox whose accessible
                                               name normalizes to the same
                                               "Status" string and stays in
                                               the DOM simultaneously with
                                               the create form beneath it —
                                               `get_by_role("combobox",
                                               name="Status")` therefore
                                               matches 2 elements. Resolved
                                               by `.last` (the create form's
                                               own Status field renders
                                               AFTER the list's filter
                                               combobox in DOM order,
                                               confirmed live), never by
                                               `exact=True` alone.)
    button   "Save as Draft"
    button   "Submit for Review"             (CONFIRMED LIVE this object's
                                               submit action reads "Submit
                                               for Review", NOT "Submit for
                                               Publishing" — ObjectAuthoringPage's
                                               own SUBMIT_FOR_PUBLISHING_BUTTON
                                               constant does not match this
                                               surface; overridden below via
                                               submit_for_review() rather
                                               than widening the shared
                                               base class for one object's
                                               own wording.)

TEST-DATA POLICY (cms-profile.md): every write this class makes is against a
brand-new `QCTEST-`-prefixed DISPOSABLE entry created by the test itself —
never one of the 6 real, shared `Annual Report <year>` rows. create_disposable_entry()
and delete_by_title() are the two methods every mutating test in this
batch's Control_Panel/dual-platform module composes for that create->act->
delete-in-finally shape.
"""

from core.web.base_page import BasePage
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url

SLUG = "ann-rpt"

FIELD_REPORT_TITLE_EN = "Report Title"
FIELD_REPORT_TITLE_AR = "Report Title — العربية *"
FIELD_REPORT_DESCRIPTION_EN = "Report Description"
FIELD_REPORT_DESCRIPTION_AR = "Report Description — العربية *"
FIELD_COVER_IMAGE = "Report Cover Image"
FIELD_PUBLICATION_YEAR = "Publication Year"
FIELD_PAGE_COUNT = "Page Count"
FIELD_PDF_ATTACHMENT = "PDF Attachment"

PUBLICATION_DATE_PLACEHOLDER = "dd/mm/yyyy"
SUBMIT_FOR_REVIEW_BUTTON = 'button:has-text("Submit for Review")'


class AnnualReportAdminPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, SLUG)

    # ---- Navigation (delegates to the shared state machine) ---------------
    def open_new_entry_form(self) -> "AnnualReportAdminPage":
        self.authoring.open_new_entry_form()
        return self

    def open_entries_list(self) -> "AnnualReportAdminPage":
        self.authoring.open_entries_list()
        return self

    def open_entry_by_edit_link(self, title: str) -> "AnnualReportAdminPage":
        self.authoring.open_entry_by_edit_link(title)
        return self

    # ---- Field access -------------------------------------------------------
    def fill_text(self, field_label: str, value: str) -> "AnnualReportAdminPage":
        self.authoring.fill_text(field_label, value)
        return self

    def field_value(self, field_label: str) -> str:
        return self.authoring.field_value(field_label)

    def fill_number(self, field_label: str, value: str) -> "AnnualReportAdminPage":
        self.authoring.fill_number(field_label, value)
        return self

    def set_publication_date(self, value: str) -> "AnnualReportAdminPage":
        """`value` e.g. "15/03/2025" (dd/mm/yyyy, per the field's own
        confirmed-live placeholder/accessible-name) — see module docstring
        on why this field is NOT reached via fill_text()/FIELD_*.

        CONFIRMED LIVE (2026-09-22): `get_by_placeholder("dd/mm/yyyy")`
        matches 3 elements on this page — the list filter panel's own
        "Modified from"/"to" date-range inputs share the identical
        placeholder, in addition to the create form's own Publication Date
        field. `.last` resolves to the create form's field (it renders
        after the filter panel in DOM order, same convention already
        applied to set_active_status()'s Status-combobox conflict below)."""
        box = self.page.get_by_placeholder(PUBLICATION_DATE_PLACEHOLDER).last
        box.click()
        self.page.keyboard.type(value, delay=20)
        return self

    def publication_date_value(self) -> str:
        return self.page.get_by_placeholder(PUBLICATION_DATE_PLACEHOLDER).last.input_value()

    def upload_file(self, field_label: str, file_path: str) -> "AnnualReportAdminPage":
        self.authoring.upload_file(field_label, file_path)
        return self

    def upload_file_expect_rejected(self, field_label: str, file_path: str) -> bool:
        return self.authoring.upload_file_expect_rejected(field_label, file_path)

    def uploaded_filename(self, field_label: str) -> str:
        return self.authoring.uploaded_filename(field_label)

    def field_length_rejected(self, field_label: str, attempted: str, limit: int) -> bool:
        return self.authoring.field_length_rejected(field_label, attempted, limit)

    # ---- Active Status combobox (see module docstring's DOM-conflict note) --
    def set_active_status(self, option_label: str) -> "AnnualReportAdminPage":
        """CONFIRMED LIVE (2026-09-22): once the entry-level Status combobox
        is opened, `get_by_role("option", name=..., exact=True)` still
        matches 2 elements (the list's own filter-panel Status dropdown
        renders an identically-labelled option in the DOM even while
        closed) — `.last` resolves to the just-opened entry-field's own
        option, same DOM-order convention as the combobox lookup itself."""
        combo = self.page.get_by_role("combobox", name="Status").last
        combo.click()
        self.page.get_by_role("option", name=option_label, exact=True).last.click()
        return self

    def active_status_value(self) -> str:
        combo = self.page.get_by_role("combobox", name="Status").last
        return combo.input_value() if combo.evaluate("el => el.tagName") == "SELECT" else combo.inner_text()

    # ---- Lifecycle ------------------------------------------------------------
    def save_as_draft(self) -> "AnnualReportAdminPage":
        self.authoring.save_as_draft()
        return self

    def submit_for_review(self) -> "AnnualReportAdminPage":
        """This object's own confirmed-live wording — "Submit for Review",
        not ObjectAuthoringPage's default "Submit for Publishing" (see
        module docstring)."""
        self.click(SUBMIT_FOR_REVIEW_BUTTON)
        self.authoring._wait_for_settle()
        return self

    def current_status(self) -> str:
        return self.authoring.current_status()

    # CONFIRMED LIVE (2026-09-22): both Save as Draft AND Submit for Review
    # on THIS object redirect back to the base `manage-ann-rpt` list/create
    # URL — unlike most other Object Authoring surfaces on this project,
    # there is no `?editEntry=<code>` banner view to read "(approved)"/
    # "(draft)" off afterward, so `current_status()` (which reads that
    # banner) returns "Unknown" here even on a genuinely successful save/
    # publish. status_for()/submit_blocked() below are this object's own
    # reliable status reads, added after reproducing `current_status()`
    # silently returning "Unknown" post-submit live this session.
    BLOCKED_MESSAGE = "Please complete the required fields"

    def submit_blocked(self) -> bool:
        """True if the CURRENT page shows the one, CONFIRMED-LIVE generic
        blocked-submission banner: "Please complete the required fields
        before proceeding with the workflow action for this new record.
        Nothing has been submitted." This banner is confirmed to fire for
        missing-mandatory-TEXT-field violations (e.g. empty Report Title/
        Description) — CONFIRMED LIVE it does NOT fire for every rejection
        this object makes (e.g. Page Count=0, a missing PDF Attachment, and
        a missing Cover Image each show a different, field-specific inline
        message instead, live-reproduced 2026-09-22). Do NOT use this alone
        as the general "was this rejected" signal — see entry_blocked()."""
        return self.BLOCKED_MESSAGE in self.page.locator("body").inner_text()

    def entry_blocked(self, title: str) -> bool:
        """The RELIABLE, general-purpose "was this rejected" signal for
        this object, regardless of which specific validation message fired
        (see submit_blocked()'s own docstring — the generic banner text is
        NOT universal across every field's rejection). True if `title`'s
        row is anything other than "Published" — covers both "never
        created at all" (status_for() returns "") and "already existed as
        Draft, still Draft after a rejected Submit for Review" alike.
        CONFIRMED LIVE this is what actually distinguishes a genuinely
        blocked attempt from one that silently succeeded despite invalid
        data (e.g. tc_143728/tc_143738's own confirmed real product
        defects — see those tests' docstrings)."""
        return self.status_for(title) != "Published"

    def status_for(self, title: str) -> str:
        """Reopens the entries list and reads `title`'s own row status —
        the reliable post-Save/Submit status read for this object (see the
        note above `BLOCKED_MESSAGE`). Returns "" if no row matches (e.g.
        the attempt was blocked before a row was ever created)."""
        self.open_entries_list()
        return self.row_status_text(title)

    def editing_banner_text(self) -> str:
        return self.authoring.editing_banner_text()

    def is_save_as_draft_disabled(self) -> bool:
        return self.authoring.is_save_as_draft_disabled()

    def unpublish_to_edit_as_draft(self) -> "AnnualReportAdminPage":
        self.authoring.unpublish_to_edit_as_draft()
        return self

    # ---- List / row state -----------------------------------------------------
    def row_visible(self, title: str) -> bool:
        return self.authoring.row_visible(title)

    def row_status_text(self, title: str) -> str:
        return self.authoring.row_status_text(title)

    def delete_entry_by_title(self, title: str) -> bool:
        return self.authoring.delete_entry_by_title(title)

    def row_entry_id(self, title: str) -> str:
        return self.authoring.row_entry_id(title)

    def row_preview_url(self, title: str) -> str:
        return self.authoring.row_preview_url(title)

    # ---- Disposable-entry convenience (DISPOSABLE per cms-profile.md) -------
    def create_disposable_entry(self, prefix: str, **overrides) -> dict:
        """Creates a brand-new `QCTEST-<prefix>`-titled Annual Report entry
        with every mandatory field filled to a safe default, then Save as
        Draft (does NOT submit/publish — callers that need it published
        call submit_for_review() themselves afterward). Returns the values
        actually filled, keyed by FIELD_* constant, for round-trip
        assertions. Pass a FIELD_* constant as a keyword (using its
        variable name, e.g. `title_en="..."`.) is NOT how overrides work —
        pass the literal dict key shown below instead (mirrors the
        project's existing `_fill_all_section_fields` pattern's own
        `field_label -> value` shape)."""
        values = {
            FIELD_REPORT_TITLE_EN: f"QCTEST-{prefix} Annual Report",
            FIELD_REPORT_TITLE_AR: f"QCTEST-{prefix} تقرير سنوي",
            FIELD_REPORT_DESCRIPTION_EN: f"QCTEST-{prefix} disposable automated-test report description.",
            FIELD_REPORT_DESCRIPTION_AR: f"QCTEST-{prefix} وصف تقرير تجريبي تم إنشاؤه تلقائيًا.",
        }
        values.update(overrides)
        self.open_new_entry_form()
        for field in (FIELD_REPORT_TITLE_EN, FIELD_REPORT_TITLE_AR,
                      FIELD_REPORT_DESCRIPTION_EN, FIELD_REPORT_DESCRIPTION_AR):
            if field in values:
                self.fill_text(field, values[field])
        return values

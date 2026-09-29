"""
cms/pages/export_reports/export_reports_page_admin_page.py —
ExportReportsPageAdminPage.

Control_Panel Page Object for the **Export Report Page** Object Authoring
surface (PBI 131313) — the page-level settings object driving the hero
(Eyebrow Label/Page Title/Hero Description/Hero Banner) and the archive
section (Section Badge/Section Title/Section Description). Slug confirmed
live: `manage-export-report-page` (page title "Manage: Export Report Page").

CONFIRMED LIVE (2026-09-22, authenticated session): this object's own
entries list carries exactly **one row** — `QCDEMO-131313-PAGE-MAIN`,
Status `PUBLISHED` — a genuine singleton, identical in kind to
`annual_reports_page_admin_page.py`'s own `QCDEMO-130712-PAGE-MAIN`. Every
field on it is therefore LIVE PRODUCTION CONTENT, not disposable test data.

Per this project's destructive-ops rule, this Page Object deliberately
exposes ONLY **read-only** field/value access — never a fill_*/save_*/
unpublish_* method against this singleton, mirroring
`annual_reports_page_admin_page.py`'s identical design. Tests needing "a
valid <field> value is saved and displayed" assert the singleton's
ALREADY-published value (read here) against the live public page's own
rendered text (asserted in web/pages/export_reports/export_reports_page.py)
— a genuine, non-invented verification, without writing anything. Tests
requiring an actual write (empty/whitespace/exceeds-length validation, or
Hero Illustration missing/oversized/unsupported) are SKIPPED in the test
module with this exact reasoning.

Field labels confirmed live via accessibility-tree snapshot of the
(opened, never submitted) `manage-export-report-page?editEntry=QCDEMO-131313-PAGE-MAIN`
edit form:

    textbox "Eyebrow Label"              / "Eyebrow Label — العربية"
    textbox "Page Title"                 / "Page Title — العربية"
    textbox "Hero Description"           / "Hero Description — العربية"
    button  "Select File" -> textbox "Hero Banner Select File" / "Hero Banner"
            (+ a "Remove file" button — CONFIRMED an image IS already
            uploaded on this singleton)
    textbox "Section Badge"              / "Section Badge — العربية"
    textbox "Section Title"              / "Section Title — العربية"
    textbox "Section Description"        / "Section Description — العربية"
    button  "Submit for Publishing" (this object's own confirmed-live
            submit wording DOES match ObjectAuthoringPage's default,
            unlike the per-record "Export Report" object's "Submit for
            Review" — same split as annual_reports_page_admin_page.py vs.
            annual_report_admin_page.py.)

CONFIRMED LIVE DIFFERENCE from annual_reports_page_admin_page.py: none of
this object's own AR fields carry a trailing " *" in their accessible name
(Annual Reports Page's did) — read as plain "Eyebrow Label — العربية" etc.
here, not independently re-verified whether that means they are optional
server-side.

CONFIRMED LIVE — no "Search Placeholder" field exists anywhere on this
object's create/edit form (full accessibility-tree enumeration found the
7 fields above and no others besides the workflow buttons) — the public
page's search-box placeholder text ("Search..") is confirmed hard-coded in
the frontend, not CMS-driven. tc_143913/143914/143915/143916 (Search
Placeholder save/validation) are therefore SKIPPED as unreachable-by-
construction, not a destructive-write gap.
"""

from core.web.base_page import BasePage
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url

SLUG = "export-report-page"
SINGLETON_TITLE = "QCDEMO-131313-PAGE-MAIN"

FIELD_EYEBROW_EN = "Eyebrow Label"
FIELD_EYEBROW_AR = "Eyebrow Label — العربية"
FIELD_PAGE_TITLE_EN = "Page Title"
FIELD_PAGE_TITLE_AR = "Page Title — العربية"
FIELD_HERO_DESCRIPTION_EN = "Hero Description"
FIELD_HERO_DESCRIPTION_AR = "Hero Description — العربية"
FIELD_HERO_BANNER = "Hero Banner"
FIELD_SECTION_BADGE_EN = "Section Badge"
FIELD_SECTION_BADGE_AR = "Section Badge — العربية"
FIELD_SECTION_TITLE_EN = "Section Title"
FIELD_SECTION_TITLE_AR = "Section Title — العربية"
FIELD_SECTION_DESCRIPTION_EN = "Section Description"
FIELD_SECTION_DESCRIPTION_AR = "Section Description — العربية"


class ExportReportsPageAdminPage(BasePage):
    """Read-only by design — see module docstring. Does not compose any of
    ObjectAuthoringPage's write/lifecycle methods on purpose."""

    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, SLUG)

    def open_singleton_for_read(self) -> "ExportReportsPageAdminPage":
        self.authoring.open_entry_by_edit_link(SINGLETON_TITLE)
        return self

    def field_value(self, field_label: str) -> str:
        return self.authoring.field_value(field_label)

    def current_status(self) -> str:
        return self.authoring.current_status()

    def row_status_text(self) -> str:
        return self.authoring.row_status_text(SINGLETON_TITLE)

    def uploaded_filename(self, field_label: str) -> str:
        return self.authoring.uploaded_filename(field_label)

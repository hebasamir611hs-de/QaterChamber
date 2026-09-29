"""
cms/pages/annual_reports/annual_reports_page_admin_page.py —
AnnualReportsPageAdminPage.

Control_Panel Page Object for the **Annual Reports Page** Object Authoring
surface (PBI 130712) — the page-level settings object driving the hero
(Eyebrow/Title/Description/Banner) and the Report Archive section
(Badge/Title/Description). Slug confirmed live: `manage-annual-reports-page`
(page title "Manage: Annual Reports Page").

CONFIRMED LIVE (2026-09-22, authenticated session): this object's own
entries list carries **exactly one row** — `QCDEMO-130712-PAGE-MAIN`,
Status `PUBLISHED` — i.e. it is a genuine **singleton**, the same class of
shared, always-live record this project's other "page settings" objects are
(mirrors home_about_summary's `QCDEMO-129389-ABOUT_US_SECTION-01` singleton,
per that module's own docstring). Every field on it (Eyebrow Label, Page
Title, Hero Description, Hero Banner, Section Badge, Section Title, Section
Description, page Status) is therefore LIVE PRODUCTION CONTENT, not
disposable test data — writing a new value and Publishing it would put
literal `QCTEST-`/boundary-probe text on the real public Annual Reports
page for every visitor until reverted, and because this object is Approved
(published), any edit forces "Unpublish to edit as draft" first, which is
itself a real, momentary content takedown per object_authoring_page.py's own
documented state machine.

Per this project's destructive-ops rule ("never take an irreversible/
content-altering action against real qcdev content without an explicit,
ID-based confirmation"), this Page Object deliberately exposes ONLY
**read-only** field/value access — never a fill_*/save_*/unpublish_* method
against this singleton. Tests needing to verify "a valid <field> value is
saved and displayed" therefore assert the singleton's ALREADY-published
value (read here) matches the live public page's own rendered text (asserted
in web/pages/annual_reports/annual_reports_page.py) — a genuine, non-invented
verification of the real save-and-display behavior, without writing
anything. Tests whose case requires actually AUTHORING a new value (the
empty/whitespace/exceeds-length validation cases) are SKIPPED in the test
module with this exact reasoning, not attempted read-only.

Field labels confirmed live via accessibility-tree snapshot of the (opened,
never submitted) create/edit form:
    textbox "Eyebrow Label"              / "Eyebrow Label — العربية *"
    textbox "Page Title"                 / "Page Title — العربية *"
    textbox "Hero Description"           / "Hero Description — العربية *"
    button  "Select File" -> textbox "Hero Banner Select File" / "Hero Banner"
    textbox "Section Badge"              / "Section Badge — العربية *"
    textbox "Section Title"              / "Section Title — العربية *"
    textbox "Section Description"        / "Section Description — العربية *"
    button  "Save as Draft" / "Submit for Publishing" (this object's own
        confirmed-live submit wording DOES match ObjectAuthoringPage's
        default "Submit for Publishing" — unlike the per-record "Annual
        Report" object's "Submit for Review", see
        annual_report_admin_page.py's own docstring for that distinction.)

Every AR field's own accessible name carries a literal trailing " *" that
the EN half does NOT — real required-field content, not whitespace
`exact=True` matching trims (same finding as annual_report_admin_page.py's
own docstring; reproduced live 2026-09-22 as a 0-match `get_by_role()`
timeout before the FIELD_*_AR constants below were corrected to include it).
"""

from core.web.base_page import BasePage
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url

SLUG = "annual-reports-page"
SINGLETON_TITLE = "QCDEMO-130712-PAGE-MAIN"

FIELD_EYEBROW_EN = "Eyebrow Label"
FIELD_EYEBROW_AR = "Eyebrow Label — العربية *"
FIELD_PAGE_TITLE_EN = "Page Title"
FIELD_PAGE_TITLE_AR = "Page Title — العربية *"
FIELD_HERO_DESCRIPTION_EN = "Hero Description"
FIELD_HERO_DESCRIPTION_AR = "Hero Description — العربية *"
FIELD_HERO_BANNER = "Hero Banner"
FIELD_SECTION_BADGE_EN = "Section Badge"
FIELD_SECTION_BADGE_AR = "Section Badge — العربية *"
FIELD_SECTION_TITLE_EN = "Section Title"
FIELD_SECTION_TITLE_AR = "Section Title — العربية *"
FIELD_SECTION_DESCRIPTION_EN = "Section Description"
FIELD_SECTION_DESCRIPTION_AR = "Section Description — العربية *"


class AnnualReportsPageAdminPage(BasePage):
    """Read-only by design — see module docstring. Does not compose any of
    ObjectAuthoringPage's write/lifecycle methods on purpose."""

    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, SLUG)

    def open_singleton_for_read(self) -> "AnnualReportsPageAdminPage":
        """Opens the one real entry via its own Edit link — read-only,
        never followed by any fill/save/unpublish call."""
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

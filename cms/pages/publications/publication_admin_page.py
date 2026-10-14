"""
cms/pages/publications/publication_admin_page.py — PublicationAdminPage.

Control_Panel Page Object for the per-record **Publication** Object
Authoring surface (PBI 130711, "QC - Insights & Media - 003 -
Publications"). Composes `ObjectAuthoringPage` (cms/pages/components/) for
the shared 7-state workflow (Draft/Pending Review/Rejected/Published/
Unpublished/Archived/Scheduled), per this
project's "Object Authoring Is the Only Path for Content Operations" rule —
field-level locators/quirks specific to THIS object live here.

Slug resolution (CLI-first, 2026-09-22, authenticated Playwright session via
`.auth/state.json`): read off `manage-export-report`'s own "Objects Home"
navigation panel (same technique this project's sibling Insights & Media
admin pages document) — filtering the panel's own "Filter…"-placeholder box
for "Publication" surfaces exactly one match: `manage-publication` ("Manage:
Publication", 9 real entries: 8 Published + 1 real Draft "Arbitration Best
Practices" pre-existing on this environment, NOT created by this session —
left untouched).

**No "Manage Publication Types" admin surface exists on this environment —
CONFIRMED via an exhaustive live search, not assumed.** Several cases in this
batch (tc_144008-144012, tc_144016, tc_144047-144052) describe a dedicated
"Manage Publication Types" screen with its own Name EN/AR fields, Active/
Inactive status, reorder, and audit log — the object nav's own "Filter…" box
was searched for every plausible name ("Publication", "Type", "Category",
"Lookup") and the full alphabetical Objects Home panel was walked end to
end: the ONLY category/lookup-style objects that exist are FAQ Categories,
Inquiry Categories, Partner Categories, Business Event Categories, Photo
Gallery Event Categories, Video Categories, and Useful Link Categories — no
Publication-scoped equivalent. "Publication Type" is, in reality, a plain,
fixed-value **combobox on the Publication entry's own create/edit form**
(`FIELD_PUBLICATION_TYPE` below), not a separately manageable Object
Definition. This is a real precondition mismatch between the case set and
the deployed product, not a locator/coverage gap — every affected case is
SKIPPED in the test module with this exact finding, per Result Integrity
(the feature described genuinely is not deployed/reachable, which is the
documented `skip` condition in automation-standards.md's Definition of Done).

Publication Type combobox options — CONFIRMED LIVE (scoped `li[role="option"]`
read, same technique as `cms/pages/export_reports/export_report_admin_page.py`'s
`_select_dropdown_option`): **Report, Bulletin, Study, Research Paper,
Guides, White Paper, Manuals, Brochure** (8 singular-form options). The
PUBLIC page's own category filter dropdown/quick-filter chips
(`web/pages/publications/publications_page.py`) expose only 6 of these, in
PLURAL form and never singular ("Research Papers", "Guides", "Reports",
"White Papers", "Manuals" — no "Bulletin"/"Study"/"Brochure" anywhere on the
public surface) — a second, independently confirmed content-model gap
between the admin Type enum and the public filter/badge vocabulary; see the
public Page Object's own docstring and the test module for the specific
cases this affects (tc_143981's stated "Brochures" chip does not exist;
tc_143988-class badge-text cases read the singular admin value, not the
plural public category label).

Field labels — CONFIRMED LIVE via `page.accessibility.snapshot()` of the
mounted create-new form:

    textbox    "Publication Title "                 (EN, required — trailing
                                                      space is part of the
                                                      real accessible name,
                                                      same convention as the
                                                      sibling Export/Annual
                                                      Report objects)
    textbox    "Publication Title — العربية *"       (AR, required)
    textbox    "Publication Description"             (EN — OPTIONAL per
                                                      tc_144035's own case)
    textbox    "Publication Description — العربية"   (AR — no trailing " *",
                                                      also optional)
    combobox   "Publication Type "  (Open Options Menu button; see options
                                     list above)
    textbox    "dd/mm/yyyy"          (Publication Date — NO real accessible
                                     label of its own, the placeholder IS
                                     the computed accessible name, same
                                     confirmed-live pattern as
                                     annual_report_admin_page.py's own
                                     PUBLICATION_DATE_PLACEHOLDER; `.last`
                                     resolves the create-form's own field
                                     over the entries-list filter panel's
                                     identically-placeholdered "Modified
                                     from"/"to" range inputs)
    button     "Select File" (x2: Cover Image, File Attachment)
    textbox    "Cover Image Select File" / "Cover Image" (filename readout)
    textbox    "File Attachment Select File" / "File Attachment"
    spinbutton "Page Count "
    combobox   "Publication Status "  (present on the live form but NOT listed
                                      for `Publication` in
                                      cms/Content-Admin-Guide.docx §12 — no
                                      test drives it; see "Guide-listed
                                      fields only" below.)

**Guide-listed fields only (migration 2026-10-01).** Content-Admin-Guide.docx
§12 lists exactly: publicationTitle / publicationDescription (bilingual),
publicationType, publicationDate, coverImage, fileAttachment, activeStatus,
downloadCount / viewCount (auto). `Page Count` and `Publication Status` are
NOT in the guide, so no test sets them; the Page Count cases are BLOCKED in
the test module. If the live form refuses a save without Page Count, that
is a guide-vs-implementation conflict to escalate, not something to fill in.

**Previously reported "Submit clears Type/Status" defect — UNVERIFIED under
the 7-state flow.** A 2026-09-22 note here claimed Submit for Review cleared
Publication Type/Status and kept the record off the public page. It was
observed through the super-admin TEST_USER, and the publish sequence it
used never ticked `Active Status` (which defaults to UNTICKED) — the second
visibility gate alone produces exactly that public-invisibility symptom.
Treat it as unverified; do not cite it as evidence.
    checkbox   "Active Status"       (guide `activeStatus` — the SECOND public
                                     visibility gate; defaults to UNTICKED.
                                     FIELD_ACTIVE_STATUS below.)
    spinbutton "Download Count"      (read-only counters, present on the
    spinbutton "View Count"          form; used as read-back only)
    button     "Save as Draft"
    button     "Submit for Review"   (shared ObjectAuthoringPage
                                     SUBMIT_FOR_REVIEW_BUTTON; the landing
                                     state depends on the signed-in role)

Entry-column check (explicitly required by this batch's task): CONFIRMED
LIVE the entries-list Entry column renders the REAL Publication Title text
on every one of the 9 real rows (e.g. "Qatar Trade Outlook 2026", "Test
Publication") — there is **no UUID-column defect on this object**, unlike
`export_report_admin_page.py`'s own manage-strategic-pillar-card-class
finding. Every title-based lookup method below is the DIRECT, faster
ObjectAuthoringPage title-based path (mirrors annual_report_admin_page.py's
own convention) — the `_resolve_code()`/`find_entry_code_by_field()`
UUID-workaround is deliberately NOT used here, since it isn't needed.

TEST-DATA POLICY (cms-profile.md): every write this class makes is against a
brand-new `QCTEST-`-prefixed DISPOSABLE entry — never one of the 9 real,
shared rows (8 published + the pre-existing "Arbitration Best Practices"
Draft). `create_disposable_entry()` / `publish_disposable_entry()` /
`delete_entry_by_title()` are the create->act->delete-in-finally shape every
mutating test in this batch's Control_Panel/dual-platform module composes.
"""

from core.web.base_page import BasePage
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url

SLUG = "publication"

FIELD_PUBLICATION_TITLE_EN = "Publication Title "  # CONFIRMED LIVE: trailing space is real
FIELD_PUBLICATION_TITLE_AR = "Publication Title — العربية *"
FIELD_PUBLICATION_DESCRIPTION_EN = "Publication Description"
FIELD_PUBLICATION_DESCRIPTION_AR = "Publication Description — العربية"
FIELD_PUBLICATION_TYPE = "Publication Type "
FIELD_COVER_IMAGE = "Cover Image"
FIELD_FILE_ATTACHMENT = "File Attachment"
FIELD_PAGE_COUNT = "Page Count "
FIELD_PUBLICATION_STATUS = "Publication Status "  # NOT in Content-Admin-Guide §12 — unused by tests
FIELD_ACTIVE_STATUS = "Active Status"  # guide §12 `activeStatus`

PUBLICATION_DATE_PLACEHOLDER = "dd/mm/yyyy"
OPEN_OPTIONS_MENU_BUTTON = "Open Options Menu"

# CONFIRMED LIVE 2026-09-22 — the Publication Type combobox's real option
# set (singular forms) vs. the public page's own plural category
# vocabulary (module docstring). "Reports" (public) is not a valid
# Type-combobox option, "Report" is.
PUBLICATION_TYPE_OPTIONS = [
    "Report", "Bulletin", "Study", "Research Paper",
    "Guides", "White Paper", "Manuals", "Brochure",
]


def _xpath_literal(value: str) -> str:
    """Safe XPath string literal — same standard XPath 1.0 workaround as
    export_report_admin_page.py's own helper."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"


class PublicationAdminPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, SLUG)

    # ---- Navigation (delegates to the shared state machine) ---------------
    def open_new_entry_form(self) -> "PublicationAdminPage":
        self.authoring.open_new_entry_form()
        return self

    def open_entries_list(self) -> "PublicationAdminPage":
        self.authoring.open_entries_list()
        return self

    def open_entry_by_edit_link(self, title: str) -> "PublicationAdminPage":
        self.authoring.open_entry_by_edit_link(title)
        return self

    # ---- Field access -------------------------------------------------------
    def fill_text(self, field_label: str, value: str) -> "PublicationAdminPage":
        self.authoring.fill_text(field_label, value)
        return self

    def field_value(self, field_label: str) -> str:
        return self.authoring.field_value(field_label)

    def number_field_value(self, field_label: str) -> str:
        return self.page.get_by_role("spinbutton", name=field_label, exact=True).input_value()

    def fill_number(self, field_label: str, value: str) -> "PublicationAdminPage":
        self.authoring.fill_number(field_label, value)
        return self

    def upload_file(self, field_label: str, file_path: str) -> "PublicationAdminPage":
        self.authoring.upload_file(field_label, file_path)
        return self

    def upload_file_expect_rejected(self, field_label: str, file_path: str) -> bool:
        return self.authoring.upload_file_expect_rejected(field_label, file_path)

    def uploaded_filename(self, field_label: str) -> str:
        return self.authoring.uploaded_filename(field_label)

    def field_length_rejected(self, field_label: str, attempted: str, limit: int) -> bool:
        return self.authoring.field_length_rejected(field_label, attempted, limit)

    def set_publication_date(self, value: str) -> "PublicationAdminPage":
        """`value` e.g. "20/09/2026" (dd/mm/yyyy) — see module docstring on
        why this field is reached via its placeholder, not FIELD_*+fill_text."""
        box = self.page.get_by_placeholder(PUBLICATION_DATE_PLACEHOLDER).last
        box.click()
        self.page.keyboard.type(value, delay=20)
        return self

    def publication_date_value(self) -> str:
        return self.page.get_by_placeholder(PUBLICATION_DATE_PLACEHOLDER).last.input_value()

    # ---- Scoped dropdown selection (Publication Type / Publication Status
    # both share the generic "Open Options Menu" ambiguity ExportReportAdminPage
    # already documents for this exact UI pattern) ---------------------------
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
        option = self.page.locator(
            f"xpath=//li[@role='option'][normalize-space(text())={_xpath_literal(option_label)}]"
        ).first
        option.wait_for(state="visible", timeout=5000)
        option.click()

    def select_publication_type(self, type_label: str) -> "PublicationAdminPage":
        self._select_dropdown_option(FIELD_PUBLICATION_TYPE, type_label)
        return self

    def set_publication_status(self, status_label: str) -> "PublicationAdminPage":
        self._select_dropdown_option(FIELD_PUBLICATION_STATUS, status_label)
        return self

    def publication_type_value(self) -> str:
        combo = self.page.get_by_role("combobox", name=FIELD_PUBLICATION_TYPE, exact=True).first
        return combo.evaluate("el => el.value || el.textContent")

    # ---- Lifecycle ------------------------------------------------------------
    def save_as_draft(self) -> "PublicationAdminPage":
        self.authoring.save_as_draft()
        return self

    def submit_for_review(self) -> "PublicationAdminPage":
        """Delegates to the shared ObjectAuthoringPage.submit_for_review()
        (shared SUBMIT_FOR_REVIEW_BUTTON). Asserts no resulting state: as
        Editor it lands on Published, as Author on Pending Review — the
        caller names the account and asserts accordingly."""
        self.authoring.submit_for_review()
        return self

    def set_active_status(self, checked: bool = True) -> "PublicationAdminPage":
        self.authoring.set_checkbox(FIELD_ACTIVE_STATUS, checked)
        return self

    def active_status_checked(self) -> bool:
        return self.authoring.is_checked(FIELD_ACTIVE_STATUS)

    BLOCKED_MESSAGE = "Please complete the required fields"

    def submit_blocked(self) -> bool:
        return self.BLOCKED_MESSAGE in self.page.locator("body").inner_text()

    def page_body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def status_for(self, title: str) -> str:
        self.open_entries_list()
        return self.authoring.row_status_text(title)

    def editing_banner_text(self) -> str:
        return self.authoring.editing_banner_text()

    def is_save_as_draft_disabled(self) -> bool:
        return self.authoring.is_save_as_draft_disabled()

    def unpublish_to_edit_as_draft(self) -> "PublicationAdminPage":
        self.authoring.unpublish_to_edit_as_draft()
        return self

    # ---- List / row state (Entry column IS the real title — no UUID
    # workaround needed, see module docstring) --------------------------------
    def row_visible(self, title: str) -> bool:
        return self.authoring.row_visible(title)

    def row_status_text(self, title: str) -> str:
        return self.authoring.row_status_text(title)

    def delete_entry_by_title(self, title: str) -> bool:
        return self.authoring.delete_entry_by_title(title)

    def row_entry_id(self, title: str) -> str:
        return self.authoring.row_entry_id(title)

    def row_last_modified(self, title: str) -> str:
        """Entries-list "Last modified" cell (Entry/Status/Last modified/
        Actions — column order per ObjectAuthoringPage's notes)."""
        row = self.page.locator(f'{self.authoring.ENTRIES_TABLE_ROW}:has-text("{title}")')
        if row.count() == 0:
            return ""
        return row.first.locator("td").nth(2).inner_text().strip()

    def history_entries(self, title: str) -> list:
        return self.authoring.history_entries(title)

    def unpublish_entry(self, title: str, comment: str = "") -> "PublicationAdminPage":
        self.authoring.unpublish_entry(title, comment)
        return self

    def row_preview_url(self, title: str) -> str:
        return self.authoring.row_preview_url(title)

    def row_entry_numeric_id(self, title: str) -> str:
        """Extracts the real, system-assigned NUMERIC entry id out of the
        row's own "Preview" link href (`?qcPreview=publications%3A<id>`) —
        CONFIRMED LIVE this is the SAME id the public
        `/web/qatar-chamber/publication-detail?id=<id>` route expects (a
        published record's own "View Details" href uses this exact id
        format, see publications_page.py). Used by tc_143995 to construct a
        Draft record's own direct detail URL purely from a real, UI-exposed
        value — never guessed, never read via an API call (this project's
        cms-profile.md UI-only policy)."""
        import re
        url = self.row_preview_url(title)
        match = re.search(r"qcPreview=publications%3A(\d+)", url)
        return match.group(1) if match else ""

    # ---- Disposable-entry convenience (DISPOSABLE per cms-profile.md) -------
    def create_disposable_entry(self, prefix: str, **overrides) -> dict:
        """Creates a brand-new `QCTEST-<prefix>`-titled Publication entry
        with every mandatory field filled to a safe default (Save as Draft
        only — callers that need it published submit it
        themselves as a named role, or use `publish_disposable_entry()` below). `overrides`
        keys are the literal FIELD_* string values, or the bare keywords
        `publication_type`, `publication_date`, `page_count`, `skip_cover`,
        `skip_file`, `active_status` for the non-textbox fields — mirrors
        export_report_admin_page.py's own convention."""
        values = {
            FIELD_PUBLICATION_TITLE_EN: f"QCTEST-{prefix} Publication",
            FIELD_PUBLICATION_TITLE_AR: f"QCTEST-{prefix} منشور",
            FIELD_PUBLICATION_DESCRIPTION_EN: f"QCTEST-{prefix} disposable automated-test publication description.",
            FIELD_PUBLICATION_DESCRIPTION_AR: f"QCTEST-{prefix} وصف منشور تجريبي تم إنشاؤه تلقائيًا.",
        }
        values.update(overrides)
        self.open_new_entry_form()
        for field in (FIELD_PUBLICATION_TITLE_EN, FIELD_PUBLICATION_TITLE_AR,
                      FIELD_PUBLICATION_DESCRIPTION_EN, FIELD_PUBLICATION_DESCRIPTION_AR):
            if field in values:
                self.fill_text(field, values[field])
        if values.get("publication_type"):
            self.select_publication_type(values["publication_type"])
        if not values.get("skip_cover"):
            self.upload_file(FIELD_COVER_IMAGE, values.get("cover_path", "cms/tests/publications/fixtures/valid_cover_1_5mb.jpg"))
        if values.get("publication_date"):
            self.set_publication_date(values["publication_date"])
        if not values.get("skip_file"):
            self.upload_file(FIELD_FILE_ATTACHMENT, values.get("file_path", "cms/tests/publications/fixtures/valid_pdf_4mb.pdf"))
        if values.get("page_count"):
            self.fill_number(FIELD_PAGE_COUNT, values["page_count"])
        if values.get("active_status") is not None:
            self.set_active_status(bool(values["active_status"]))
        return values

    def publish_disposable_entry(self, prefix: str, **overrides) -> dict:
        """create_disposable_entry() with Active Status ticked + Save as Draft
        + reopen + Submit for Review. Lands on Published ONLY when the signed-in
        account is a Site Content Editor (privileged bypass); as Author it
        lands on Pending Review. The caller pins the account."""
        overrides.setdefault("active_status", True)
        values = self.create_disposable_entry(prefix, **overrides)
        self.save_as_draft()
        title = values[FIELD_PUBLICATION_TITLE_EN]
        self.open_entry_by_edit_link(title)
        self.submit_for_review()
        return values

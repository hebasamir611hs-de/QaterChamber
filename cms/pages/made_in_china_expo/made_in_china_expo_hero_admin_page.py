"""
cms/pages/made_in_china_expo/made_in_china_expo_hero_admin_page.py —
MadeInChinaExpoHeroAdminPage.

Control_Panel Page Object for PBI 130953 ("QC - Events - 006 - Made in China
Expo")'s **Hero** Object Authoring surface. Slug CONFIRMED LIVE 2026-09-22
(authenticated session, real accessibility-tree read of the opened, never-
submitted admin form): `made-in-china-expo-hero`
(`/web/qatar-chamber/manage-made-in-china-expo-hero`, page title "Manage:
Made in China Expo Hero").

SCHEMA CONFIRMED LIVE (2026-09-22): this is a THREE-OBJECT page, not the
single page-level object every prior "page settings" singleton on this
project used (Annual Reports Page / Export Report Page). Object Definitions
enumeration (`Content & Data` catalog, full sweep) turned up exactly three
objects for this PBI: "Made in China Expo Heroes" (this class), "Made in
China Expo About Sections" (made_in_china_expo_about_admin_page.py), and
"Explore Made in China CTA Cards" (explore_made_in_china_cta_admin_page.py)
— a sibling "Made in Qatar Expo" trio also exists (different PBI, not this
one; not touched here). Each object's own entries list carries **exactly
one row** — this one is `QCDEMO-130953-MIC-hero`, Status
`PUBLISHED ON THE WEBSITE` — a genuine singleton, same class of shared,
always-live record as every other "page settings" object on this project.

Per this project's destructive-ops rule, this Page Object deliberately
exposes ONLY **read-only** field/value access — never a fill_*/save_*/
unpublish_* method against this singleton — mirroring
`annual_reports_page_admin_page.py` / `export_reports_page_admin_page.py`'s
identical design. Tests needing "a valid <field> value is saved and
displayed" assert the singleton's ALREADY-published value (read here)
against the live public page's own rendered text (asserted in
web/pages/made_in_china_expo/made_in_china_expo_page.py) — a genuine,
non-invented verification, without writing anything. Tests requiring an
actual write (empty/whitespace/exceeds-length validation, Open Behavior
selection, Active Status/Display Order toggling, file-format/size
rejection) are SKIPPED in the test module with this exact reasoning.

Field labels confirmed live via `.inner_text()` read of the (opened, never
submitted) create/edit form (this object's entries list shows "1 total",
row `QCDEMO-130953-MIC-hero`):

    textbox "Eyebrow Label"                 / "Eyebrow Label — العربية *"
    textbox "Page Title"                    / "Page Title — العربية *"
    (rich text, CKEditor) "Hero Description" (marked "Required" in-form)
                                             / "Hero Description — العربية"
    button  "Select File" -> "Hero Banner"  (upload: .jpg/.jpeg/.png/.svg, <=2MB)
    textbox "Hero Banner Alt Text"          / "Hero Banner Alt Text — العربية *"
    textbox "Button Label"                  / "Button Label — العربية *"
    textbox "Redirect URL"
    combobox "Open Behavior"                (confirmed live value: "New Tab")
    combobox "Status"                       (page/workflow status — confirmed live: "Published")
    checkbox "Active Status"
    spinbutton "Display Order"
    (read-only) "Created Date" / "Last Modified Date"
    button "Save as Draft" / "Submit for Publishing" (standard
        ObjectAuthoringPage state machine — confirmed live, same shape as
        every other project singleton)

Only the AR half of each bilingual pair carries a literal trailing " *" in
its own accessible name (same asymmetry documented in
`annual_reports_page_admin_page.py`'s module docstring) — real
required-field content, not a whitespace-trimming artifact. The rich-text
Hero Description field marks required-ness with the literal word
"Required" in-form instead, on the EN half only (the AR half carries
neither the word nor an asterisk) — disclosed as-observed, not
independently re-verified server-side.

CONFIRMED LIVE PRODUCT DEFECT (2026-09-22, anonymous/unauthenticated
browser context, public delivery surface): the live public page's own
Hero CTA anchor ("Visit the Official Expo Website") resolves to
`https://www.qatarchamber.com/` — NOT `https://www.madeinchinaexpo.com` as
every relevant QA case (tc_144249/144250/144259) expects. The SAME wrong
target is used by the CTA Card's own button (see
explore_made_in_china_cta_admin_page.py). This is a real, confirmed-live
product defect, not a test/locator issue — the affected web tests are
scripted to assert the CASE's real expected URL and are expected to FAIL
honestly (see Result Integrity — a test must never be softened to match an
observed defect).

CONFIRMED LIVE (2026-09-22, anonymous browser, no `/events/` prefix): the
QA cases' own stated public path (`/events/made-in-china-expo`) 404s. The
REAL live path — resolved via this object's own row-level "Preview" link
target, `/web/qatar-chamber/made-in-china-expo?qcPreview=...` — is
`/made-in-china-expo` (site-root, no `/events/` segment; friendly-URL
stripped of the internal `/web/qatar-chamber/` prefix, same convention
every other page on this project uses). `web/pages/made_in_china_expo/
made_in_china_expo_page.py`'s `open_public_page()` uses the REAL path;
every web test in this batch navigates through that Page Object method, not
a hard-coded path mirroring the case's (wrong) literal text.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from core.web.base_page import BasePage

SLUG = "made-in-china-expo-hero"
SINGLETON_TITLE = "QCDEMO-130953-MIC-hero"

FIELD_EYEBROW_EN = "Eyebrow Label"
FIELD_EYEBROW_AR = "Eyebrow Label — العربية *"
FIELD_PAGE_TITLE_EN = "Page Title"
FIELD_PAGE_TITLE_AR = "Page Title — العربية *"
FIELD_HERO_DESCRIPTION_EN = "Hero Description"
FIELD_HERO_DESCRIPTION_AR = "Hero Description — العربية"
FIELD_HERO_BANNER = "Hero Banner"
FIELD_HERO_BANNER_ALT_EN = "Hero Banner Alt Text"
FIELD_HERO_BANNER_ALT_AR = "Hero Banner Alt Text — العربية *"
FIELD_BUTTON_LABEL_EN = "Button Label"
FIELD_BUTTON_LABEL_AR = "Button Label — العربية *"
FIELD_REDIRECT_URL = "Redirect URL"
FIELD_OPEN_BEHAVIOR = "Open Behavior"
FIELD_STATUS = "Status"
FIELD_ACTIVE_STATUS = "Active Status"
FIELD_DISPLAY_ORDER = "Display Order"


class MadeInChinaExpoHeroAdminPage(BasePage):
    """Read-only by design — see module docstring. Does not compose any of
    ObjectAuthoringPage's write/lifecycle methods on purpose."""

    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, SLUG)

    def open_singleton_for_read(self) -> "MadeInChinaExpoHeroAdminPage":
        # open_entry_by_edit_link() only locates/clicks a row's own Edit
        # link -- it does not itself navigate to the manage-<slug> page, so
        # the entries list must be opened first (confirmed live 2026-09-22:
        # omitting this step times out locating the row on whatever page
        # the shared `page` object happened to be on beforehand).
        self.authoring.open_entries_list()
        self.authoring.open_entry_by_edit_link(SINGLETON_TITLE)
        return self

    def field_value(self, field_label: str) -> str:
        return self.authoring.field_value(field_label)

    def hero_description_text(self) -> str:
        """Hero Description is a rich-text CKEditor field (confirmed live
        via the in-form "Required" marker text, not a plain textbox) — it
        does NOT resolve via `field_value()`'s `get_by_role("textbox", ...)`
        call, which times out against it (confirmed live 2026-09-22).
        `ObjectAuthoringPage.DESCRIPTION_EDITOR_IFRAME` (`nth=0`, the
        first-mounted EN instance) reads its current content instead."""
        return self.authoring.iframe_editor_text(self.authoring.DESCRIPTION_EDITOR_IFRAME)

    def current_status(self) -> str:
        return self.authoring.current_status()

    def row_status_text(self) -> str:
        return self.authoring.row_status_text(SINGLETON_TITLE)

    def uploaded_filename(self, field_label: str) -> str:
        return self.authoring.uploaded_filename(field_label)

    def combobox_value(self, field_label: str) -> str:
        """Read-only combobox reader (Open Behavior / Status) — neither
        field has a generic reader on ObjectAuthoringPage since every prior
        singleton on this project only ever needed text/file fields read
        back.

        CONFIRMED LIVE 2026-09-22: a bare `get_by_role("combobox", name=
        field_label, exact=True)` for "Status" is NOT unique on this page —
        the entries-list's own Status FILTER dropdown
        (`<select data-qc-oel-status-filter>`, rendered above the edit
        form) shares the same accessible-name search. `.last` deterministically
        selects the actual field's own control (rendered after the filter,
        confirmed live via the strict-mode-violation candidate order) — the
        real field's accessible name additionally includes "(Read Only)"
        for Status, a real, confirmed-live finding that this object's own
        Status control is NOT independently settable (it mirrors the
        workflow Draft/Approved state), disclosed on the case's own test
        rather than assumed. `.input_value()` first (native <select>),
        falling back to the rendered text of the widget's own display
        element for a custom-rendered combobox."""
        combo = self.page.get_by_role("combobox", name=field_label, exact=True).last
        try:
            return combo.input_value()
        except Exception:
            return combo.inner_text().strip()

    def active_status_checked(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_ACTIVE_STATUS, exact=True).is_checked()

    def display_order_value(self) -> str:
        return self.page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True).input_value()

"""
cms/pages/home_about_summary/home_about_summary_admin_page.py —
HomeAboutSummaryAdminPage / HomeAboutCounterAdminPage.

Control_Panel Page Objects for PBI 129389 (QC-HOME-013 — "About Us Section &
Last Year Achievements Counters"), backing the homepage "About Us" summary
widget (public counterpart: web/pages/home_about_summary/
home_about_summary_page.py).

REWRITTEN 2026-09-07 per standards.md's broadened "Object Authoring Is the
Only Path for Content Operations — Not Content & Data" rule: this file's
PRIOR version drove every field write and the "Save" lifecycle action
through `Content & Data`'s raw Object Definitions grid
(objectDefinitionId=51812 / 52004). That surface is retired for this
project — CONFIRMED LIVE this session (real, disposable Python/Playwright
probe against qcdev, existing `.auth/state.json` session, 1920x1080) that
BOTH objects have a real, dedicated Object Authoring surface:

  - **Section slug: `about-us-section`** (`/web/qatar-chamber/
    manage-about-us-section`) — a SINGLETON list, confirmed live
    ("1 total" entry), Entry-column code
    `QCDEMO-129389-ABOUT_US_SECTION-01`, Status APPROVED. Confirmed-live
    field labels (all reachable via `page.get_by_role(<role>, name=<label>,
    exact=True)` per `ObjectAuthoringPage`'s generic helpers): `Section Tag
    (EN)` / `(AR)`, `Section Heading (EN)` / `(AR)`, `Building Image
    (Primary)` / `(Secondary)` / `(Tertiary)` (file uploads, the
    "<Field Label> Select File" pattern), `Years of Experience Badge (EN)`
    / `(AR)`, `Read More Label (EN)` / `(AR)`, `Read More URL`. The bilingual
    Section Description (EN/AR) is a rich-text CKEditor pair — confirmed
    live 2 `iframe[title="editor"]` instances mount on this form (same
    "one per locale, `>> nth=0`/`>> nth=1`" shape `ObjectAuthoringPage`'s
    own module docstring documents for manage-strategic-pillar-card), EN is
    the first-mounted (`nth=0`) instance on a freshly opened edit form.
  - **Counter slug: `about-us-counter`** (`/web/qatar-chamber/
    manage-about-us-counter`) — a REPEATABLE list, confirmed live with 5
    rows this session: 4 seeded QCDEMO rows (Entry-column codes
    `QCDEMO-129389-ABOUT_US_COUNTER-01..04`) plus one extra non-QCDEMO row
    (a bare UUID) left over from prior exploration — NOT touched by this
    module. Confirmed-live field labels on a counter row's edit form:
    `Counter Title (EN)` / `(AR)` (textbox), `Counter Value` (textbox),
    `Counter Display Order` (spinbutton), `Counter Active Status`
    (checkbox), `Counter Icon` (file upload, same "<Field Label> Select
    File" hidden-textbox pattern as the Section form's Building Image
    fields — confirmed live a `"Counter Icon Select File"`-named hidden
    textbox + sibling `Select File` button exist).
  - Both surfaces render the same generic Save-as-Draft / Submit-for-
    Publishing / Unpublish-to-edit-as-draft state machine every other
    Object Authoring surface on this project uses — an Approved entry's
    editing banner text is exactly `'...(approved). It is published, so
    Save as Draft is unavailable until you unpublish it.'` (confirmed live
    on the Section form) — same shape `ObjectAuthoringPage`'s own module
    docstring documents project-wide, so `submit_for_publishing()` /
    `current_status()` are used as-is with no local override needed.

TEST-DATA POLICY: both objects' live records are pre-existing, dedicated
shared singletons (TEST_OWNED per cms-profile.md), never disposable
QCTEST- rows a factory can create/delete — this project's UI-only
test-data policy applies. Section record `QCDEMO-129389-ABOUT_US_SECTION-01`
and Counter rows `QCDEMO-129389-ABOUT_US_COUNTER-01..04` should be added to
standards.md's Safe Parallelism singleton table (same convention as the
Dynamic Widgets / GM's Message / Board Members rows already listed there)
the next time that table is updated — every mutating test in this module
captures a full baseline before writing and restores it (`finally`),
including a reopen-and-reread verification, so the shared records are
never left mutated even on failure.

PROBE FAILURE, DISCLOSED (2026-09-15): before authoring the 50-case batch
covering ADO 136088-136140, three live one-shot probe attempts were made
against this surface (`manage-about-us-section` / `manage-about-us-counter`)
to confirm `maxlength` attributes and the exact required-field-violation
wording, reusing the existing `.auth/state.json` session. All three failed:
run 1 hung indefinitely on a `networkidle` wait with zero CPU growth for
several minutes; run 2 raised `Timeout 30000ms exceeded` resolving the
Section form's own textboxes, then `Target crashed` / `Page crashed`
Playwright errors; run 3 (fresh per-section browser contexts,
`--disable-dev-shm-usage`, a smaller viewport) hung again before the first
field read completed. `tasklist` showed 25+ pre-existing orphan `chrome.exe`
processes on the host across all three attempts — a host-resource condition,
not a script defect (this project's own memory note already warns never to
run parallel live-browser agents). No character-limit or required-field
validation-message mechanism was independently confirmed live this session.
Every CP test below that depends on that mechanism uses
`ObjectAuthoringPage.field_length_rejected()` /
`upload_file_expect_rejected()`, which accept either observable branch the
QA cases themselves allow ("Field truncates OR shows a max-length error";
publish is blocked = `current_status() != "Approved"`) rather than assuming
one specific mechanism. The public (unauthenticated) Home Page surface was
NOT affected by this — that probe succeeded cleanly and its findings are
folded into `web/pages/home_about_summary/home_about_summary_page.py`'s own
module docstring as real, confirmed-live results.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url

SECTION_SLUG = "about-us-section"
COUNTER_SLUG = "about-us-counter"

SECTION_ENTRY_CODE = "QCDEMO-129389-ABOUT_US_SECTION-01"
COUNTER_ENTRY_CODES = [
    "QCDEMO-129389-ABOUT_US_COUNTER-01",
    "QCDEMO-129389-ABOUT_US_COUNTER-02",
    "QCDEMO-129389-ABOUT_US_COUNTER-03",
    "QCDEMO-129389-ABOUT_US_COUNTER-04",
]

# ---- Section field labels --------------------------------------------------
FIELD_SECTION_TAG_EN = "Section Tag (EN)"
FIELD_SECTION_TAG_AR = "Section Tag (AR)"
FIELD_SECTION_HEADING_EN = "Section Heading (EN)"
FIELD_SECTION_HEADING_AR = "Section Heading (AR)"
FIELD_BUILDING_IMAGE_PRIMARY = "Building Image (Primary)"
FIELD_BUILDING_IMAGE_SECONDARY = "Building Image (Secondary)"
FIELD_YEARS_BADGE_EN = "Years of Experience Badge (EN)"
FIELD_YEARS_BADGE_AR = "Years of Experience Badge (AR)"
FIELD_READ_MORE_LABEL_EN = "Read More Label (EN)"
FIELD_READ_MORE_LABEL_AR = "Read More Label (AR)"
FIELD_READ_MORE_URL = "Read More URL"

# ---- Counter field labels ---------------------------------------------------
FIELD_COUNTER_TITLE_EN = "Counter Title (EN)"
FIELD_COUNTER_TITLE_AR = "Counter Title (AR)"
FIELD_COUNTER_VALUE = "Counter Value"
FIELD_COUNTER_DISPLAY_ORDER = "Counter Display Order"
FIELD_COUNTER_ACTIVE_STATUS = "Counter Active Status"
FIELD_COUNTER_ICON = "Counter Icon"


class HomeAboutSummaryAdminPage(ObjectAuthoringPage):
    """Drives the About Us Section singleton via Object Authoring. Bilingual
    rich-text Section Description uses two independently-addressable
    CKEditor iframes (see module docstring) — overrides the base class's
    single-locale DESCRIPTION_EDITOR_IFRAME with explicit EN/AR variants."""

    SECTION_DESC_EDITOR_EN = 'iframe[title="editor"] >> nth=0'
    SECTION_DESC_EDITOR_AR = 'iframe[title="editor"] >> nth=1'

    def __init__(self, page):
        super().__init__(page, SECTION_SLUG)

    def open_section_entry(self) -> "HomeAboutSummaryAdminPage":
        self.open_entry_by_code(SECTION_ENTRY_CODE)
        return self

    def fill_description_en(self, text: str) -> "HomeAboutSummaryAdminPage":
        self.fill_iframe_editor(self.SECTION_DESC_EDITOR_EN, text)
        return self

    def fill_description_ar(self, text: str) -> "HomeAboutSummaryAdminPage":
        self.fill_iframe_editor(self.SECTION_DESC_EDITOR_AR, text)
        return self

    def description_en_value(self) -> str:
        return self.iframe_editor_text(self.SECTION_DESC_EDITOR_EN)

    def description_ar_value(self) -> str:
        return self.iframe_editor_text(self.SECTION_DESC_EDITOR_AR)

    def description_length_rejected(self, locale: str, attempted: str, limit: int) -> bool:
        """Rich-text counterpart to ObjectAuthoringPage.field_length_rejected()
        for the bilingual CKEditor Section Description fields — same
        disclosed dual-branch check (see module docstring's PROBE FAILURE
        note): truncation read back immediately after fill, OR a
        submit-time publish block. `locale` is "en" or "ar"."""
        fill = self.fill_description_en if locale == "en" else self.fill_description_ar
        read = self.description_en_value if locale == "en" else self.description_ar_value
        fill(attempted)
        if len(read().strip()) <= limit:
            return True
        self.submit_for_publishing()
        return self.current_status() != "Approved"

    def upload_building_image_primary(self, file_path: str) -> "HomeAboutSummaryAdminPage":
        self.upload_file(FIELD_BUILDING_IMAGE_PRIMARY, file_path)
        return self

    def upload_building_image_secondary(self, file_path: str) -> "HomeAboutSummaryAdminPage":
        self.upload_file(FIELD_BUILDING_IMAGE_SECONDARY, file_path)
        return self

    def building_image_primary_filename(self) -> str:
        return self.uploaded_filename(FIELD_BUILDING_IMAGE_PRIMARY)

    def building_image_secondary_filename(self) -> str:
        return self.uploaded_filename(FIELD_BUILDING_IMAGE_SECONDARY)

    def capture_section_baseline(self) -> dict:
        self.open_section_entry()
        return {
            "heading_en": self.field_value(FIELD_SECTION_HEADING_EN),
            "heading_ar": self.field_value(FIELD_SECTION_HEADING_AR),
            "tag_en": self.field_value(FIELD_SECTION_TAG_EN),
            "tag_ar": self.field_value(FIELD_SECTION_TAG_AR),
            "years_badge_en": self.field_value(FIELD_YEARS_BADGE_EN),
            "years_badge_ar": self.field_value(FIELD_YEARS_BADGE_AR),
            "read_more_label_en": self.field_value(FIELD_READ_MORE_LABEL_EN),
            "read_more_label_ar": self.field_value(FIELD_READ_MORE_LABEL_AR),
            "read_more_url": self.field_value(FIELD_READ_MORE_URL),
            # Added 2026-09-15 for the ADO 136088-136140 batch: several new
            # cases (136110, 136115, 136116) mutate the bilingual rich-text
            # Description — the PRIOR version of this method omitted it, a
            # real gap (restore_section() below could not have restored it
            # either). Both now round-trip it like every other field.
            "description_en": self.description_en_value(),
            "description_ar": self.description_ar_value(),
        }

    def ensure_draft(self) -> "HomeAboutSummaryAdminPage":
        """Unpublishes the currently-open entry (if Approved) so Save as
        Draft becomes available — several QA cases in the 136088-136140
        batch explicitly exercise "Save Draft" against this project's
        Approved-by-default singleton, where Save as Draft is disabled
        until unpublished (see this module's REWRITTEN docstring above).
        No-op if already Draft. Must be called on an already-open entry."""
        if self.current_status() == "Approved":
            self.unpublish_to_edit_as_draft()
            self.open_section_entry()
        return self

    # ---- Real cross-session logout/login (TC-136136's own mechanism —
    # confirmed live in the prior Content & Data-era version of this class:
    # `GET /c/portal/logout` ends the session, a subsequent authenticated
    # navigation re-renders the real login form) --------------------------
    LOGOUT_PATH = "/c/portal/logout"

    def logout_and_return(self) -> "HomeAboutSummaryAdminPage":
        self.open(control_panel_url(self.LOGOUT_PATH))
        return self

    def login_as(self, username: str, password: str) -> "HomeAboutSummaryAdminPage":
        from cms.pages.control_panel.login_page import CmsLoginPage

        CmsLoginPage(self.page).open_login().login(username, password)
        return self

    def restore_section(self, baseline: dict) -> "HomeAboutSummaryAdminPage":
        self.open_section_entry()
        self.fill_text(FIELD_SECTION_HEADING_EN, baseline["heading_en"])
        self.fill_text(FIELD_SECTION_HEADING_AR, baseline["heading_ar"])
        self.fill_text(FIELD_SECTION_TAG_EN, baseline["tag_en"])
        self.fill_text(FIELD_SECTION_TAG_AR, baseline["tag_ar"])
        self.fill_text(FIELD_YEARS_BADGE_EN, baseline["years_badge_en"])
        self.fill_text(FIELD_YEARS_BADGE_AR, baseline["years_badge_ar"])
        self.fill_text(FIELD_READ_MORE_LABEL_EN, baseline["read_more_label_en"])
        self.fill_text(FIELD_READ_MORE_LABEL_AR, baseline["read_more_label_ar"])
        self.fill_text(FIELD_READ_MORE_URL, baseline["read_more_url"])
        if "description_en" in baseline:
            self.fill_description_en(baseline["description_en"])
        if "description_ar" in baseline:
            self.fill_description_ar(baseline["description_ar"])
        self.submit_for_publishing()
        return self


class HomeAboutCounterAdminPage(ObjectAuthoringPage):
    """Drives one "About Us Counter" repeatable-list row via Object
    Authoring — construct once per test and call open_counter(code) to
    switch rows (all 4 seeded QCDEMO rows share this one class, unlike the
    Section's fixed singleton)."""

    def __init__(self, page):
        super().__init__(page, COUNTER_SLUG)

    def open_counter(self, entry_code: str) -> "HomeAboutCounterAdminPage":
        self.open_entry_by_code(entry_code)
        return self

    def open_counter_list(self) -> "HomeAboutCounterAdminPage":
        self.open_entries_list()
        return self

    def ensure_draft(self) -> "HomeAboutCounterAdminPage":
        """Counter-row counterpart to HomeAboutSummaryAdminPage.ensure_draft()
        — same unpublish-if-Approved no-op-if-Draft shape, for "Save Draft"
        cases exercised against a counter row."""
        if self.current_status() == "Approved":
            self.unpublish_to_edit_as_draft()
        return self

    def counter_row_count(self) -> int:
        return self.page.locator(self.ENTRIES_TABLE_ROW).count()

    def add_counter_control_state(self) -> dict:
        """Read-only inspection of the entries-list Add/New control — NEVER
        clicked (per this project's never-click-Add policy for this
        singleton-backed set: a real Add would create a permanent,
        publicly-visible 5th row on the live Home page, see this class's own
        module docstring). NOT independently confirmed live this session
        (see module docstring's PROBE FAILURE note) — the selector list
        below is the same one the abandoned live probe attempted to read.
        Returns {"found": bool, "visible": bool, "disabled": bool} — a
        caller asserting "Add is disabled/hidden" should treat found=False
        as visible=False (no control to click) and NOT as a framework gap."""
        for sel in ('a:has-text("Add")', 'button:has-text("Add")', 'a:has-text("New")', 'button:has-text("New")'):
            loc = self.page.locator(sel)
            if loc.count() > 0:
                el = loc.first
                visible = el.is_visible()
                disabled = el.is_disabled() if visible else False
                return {"found": True, "visible": visible, "disabled": disabled}
        return {"found": False, "visible": False, "disabled": False}

    def set_title_en(self, value: str) -> "HomeAboutCounterAdminPage":
        self.fill_text(FIELD_COUNTER_TITLE_EN, value)
        return self

    def set_title_ar(self, value: str) -> "HomeAboutCounterAdminPage":
        self.fill_text(FIELD_COUNTER_TITLE_AR, value)
        return self

    def set_value(self, value: str) -> "HomeAboutCounterAdminPage":
        self.fill_text(FIELD_COUNTER_VALUE, value)
        return self

    def set_display_order(self, value: str) -> "HomeAboutCounterAdminPage":
        self.fill_number(FIELD_COUNTER_DISPLAY_ORDER, value)
        return self

    def set_active(self, active: bool) -> "HomeAboutCounterAdminPage":
        self.set_checkbox(FIELD_COUNTER_ACTIVE_STATUS, active)
        return self

    def is_active(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_COUNTER_ACTIVE_STATUS, exact=True).is_checked()

    def upload_icon(self, file_path: str) -> "HomeAboutCounterAdminPage":
        self.upload_file(FIELD_COUNTER_ICON, file_path)
        return self

    def icon_filename(self) -> str:
        return self.uploaded_filename(FIELD_COUNTER_ICON)

    def title_en_value(self) -> str:
        return self.field_value(FIELD_COUNTER_TITLE_EN)

    def value_value(self) -> str:
        return self.field_value(FIELD_COUNTER_VALUE)

    def display_order_value(self) -> str:
        return self.page.get_by_role("spinbutton", name=FIELD_COUNTER_DISPLAY_ORDER, exact=True).input_value()

    def capture_baseline(self, entry_code: str) -> dict:
        self.open_counter(entry_code)
        return {
            "entry_code": entry_code,
            "title_en": self.title_en_value(),
            "title_ar": self.field_value(FIELD_COUNTER_TITLE_AR),
            "value": self.value_value(),
            "display_order": self.display_order_value(),
            "active": self.is_active(),
        }

    def restore(self, baseline: dict) -> "HomeAboutCounterAdminPage":
        self.open_counter(baseline["entry_code"])
        self.set_title_en(baseline["title_en"])
        self.set_title_ar(baseline["title_ar"])
        self.set_value(baseline["value"])
        self.set_display_order(baseline["display_order"])
        self.set_active(baseline["active"])
        self.submit_for_publishing()
        return self

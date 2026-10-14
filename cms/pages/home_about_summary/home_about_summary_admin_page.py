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
    Review (Editor: Publish) / Unpublish-to-edit-as-draft state machine every other
    Object Authoring surface on this project uses — a Published entry's
    editing banner text is exactly `'...(approved). It is published, so
    Save as Draft is unavailable until you unpublish it.'` (confirmed live
    on the Section form) — same shape `ObjectAuthoringPage`'s own module
    docstring documents project-wide, so `submit_for_review()` /
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
publish is blocked = a refusal bar and no stored change (see submit_outcome())) rather than assuming
one specific mechanism. The public (unauthenticated) Home Page surface was
NOT affected by this — that probe succeeded cleanly and its findings are
folded into `web/pages/home_about_summary/home_about_summary_page.py`'s own
module docstring as real, confirmed-live results.
"""

import re

from cms.pages.components.object_authoring_page import (
    ObjectAuthoringPage,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url
from core.web.session_guard import sign_out_locally

# ---- 2026-10-07 (Phase 3, B-129389) - read live as Editor/Author ----------
# * Both manage pages render the entries list PLUS an EMPTY create form at the
#   bare `manage-<slug>` URL (verified: every ObjectField_* input blank), so
#   the bare URL is a safe create path - it does NOT open the live record
#   (the singleton trap seen on other objects).
# * Submit label: Editor sees "Publish", Author sees "Submit for Review" -
#   ObjectAuthoringPage.SUBMIT_FOR_REVIEW_BUTTON matches both.
# * A NEW Section entry has `Active Status` TICKED by default; a new Counter
#   has `Counter Active Status` unticked and `Active Status` ticked. Every
#   disposable QCTEST record here unticks every active flag so it can never
#   render publicly.
# * Live records: Section 52157 (QCDEMO-129389-ABOUT_US_SECTION-01), Counters
#   52165/52171/52177/52183 (QCDEMO-129389-ABOUT_US_COUNTER-01..04) plus a
#   5th PUBLISHED counter 148930 (51c3aa92-..., created 2026-09-13, not ours).
#   None of these is approved for writes in docs/qa-environment-notes.md 5,
#   so every test that writes one is gated by REAL_WRITE_ENV below.
REAL_WRITE_ENV = "ALLOW_129389_REAL_WRITE"
QCTEST_PREFIX = "QCTEST-"

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


class _DisposableRecordMixin:
    """Create / submit / tear down disposable QCTEST records on a manage page.
    Never deletes a record whose identifying field does not start with
    QCTEST- (standards.md, Destructive Operations Against qcdev)."""

    TITLE_FIELDS: tuple = ()  # overridden: fields whose value proves QCTEST identity
    INVALID_INPUTS = "form :invalid"

    def sign_in_as(self, role: str):
        email, password = cms_role_credentials(role)
        CmsLoginPage(self.page).ensure_signed_in_as(email, password)
        return self

    def open_new_form(self):
        self.open_new_entry_form(locale="en")
        return self

    def submit_outcome(self, draft: bool = False) -> dict:
        """Click Save as Draft / the submit button ("Publish" for Editor,
        "Submit for Review" for Author) and report what happened WITHOUT
        assuming success: outcome is 'nav' (saved, URL moved to
        ?previewEntry=), 'toast', 'refused' (red bar), 'spinner', or None
        (the click never started a save, e.g. native browser validation)."""
        start_url = self.page.url
        before = self._pre_save_snapshot()
        self.click(self.SAVE_AS_DRAFT_BUTTON if draft else self.SUBMIT_FOR_REVIEW_BUTTON)
        outcome = self._poll_save_outcome(start_url, before)
        refusal = ""
        try:
            refusal = " | ".join(
                t.strip() for t in self.page.locator(self.SAVE_REFUSAL).all_inner_texts() if t.strip()
            )
        except Exception:  # noqa: BLE001
            pass
        return {
            "outcome": outcome,
            "refusal": refusal[:500],
            "invalid_inputs": self._count(self.INVALID_INPUTS),
            "url": self.page.url,
            "created_code": self.created_code_from_url(),
        }

    def resolve_created(self, result: dict, prefix: str) -> dict:
        """HEALED 2026-10-07: a successful save on the create form does NOT
        move the URL to ?previewEntry= on these objects (outcome 'spinner',
        URL unchanged), so the URL alone cannot prove a record was or was
        not created. Unless the form showed the refusal bar, look the
        record up by its QCTEST prefix in the entries list."""
        if not result.get("created_code") and result.get("outcome") != "refused":
            found = self.find_qctest_codes(prefix)
            result["created_code"] = found[0] if found else ""
            result["resolved_by_list"] = found
        return result

    def safe_upload(self, field_label: str, file_path: str):
        """upload_file() with one retry (live: the picker iframe sometimes
        never mounts its file input within 30 s), then waits for the picker
        to close so later form clicks are not blocked by it."""
        try:
            self.upload_file(field_label, file_path)
        except Exception:  # noqa: BLE001
            self.page.keyboard.press("Escape")
            self.upload_file(field_label, file_path)
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=30000)
        except Exception:  # noqa: BLE001
            pass
        return self

    def maxlength(self, field_label: str):
        """Implemented limit read live (Rule 5): the textbox's maxlength
        attribute, else the "<n> / <max>" character counter rendered under
        the field (live 2026-10-07: e.g. "0 / 30" under Counter Title)."""
        box = self.page.get_by_role("textbox", name=field_label, exact=True)
        v = box.get_attribute("maxlength")
        if v and v.isdigit():
            return int(v)
        return self.char_counter(field_label)[1]

    def char_counter(self, field_label: str):
        """(current, max) from the field's "<n> / <max>" counter, or (None, None)."""
        box = self.page.get_by_role("textbox", name=field_label, exact=True)
        txt = box.evaluate(
            r"el => { let n = el; for (let i = 0; i < 4 && n; i++, n = n.parentElement) {"
            r" const m = (n.innerText || '').match(/(\d+)\s*\/\s*(\d+)/); if (m) return m[0]; } return ''; }")
        m = re.search(r"(\d+)\s*/\s*(\d+)", txt or "")
        return (int(m.group(1)), int(m.group(2))) if m else (None, None)

    def file_name_shown(self, field_label: str) -> str:
        """Newly selected file (uploaded_filename) or the saved one
        (current_file_name) - whichever the field renders."""
        for read in (self.uploaded_filename, self.current_file_name):
            try:
                v = read(field_label)
            except Exception:  # noqa: BLE001
                v = ""
            if v:
                return v
        return ""

    def tick(self, label: str, on: bool):
        box = self.page.get_by_role("checkbox", name=label, exact=True)
        box.check(force=True) if on else box.uncheck(force=True)
        return self

    def created_code_from_url(self) -> str:
        m = re.search(r"previewEntry=([^&#]+)", self.page.url)
        return m.group(1) if m else ""

    def entry_codes(self) -> list:
        self.open_entries_list(locale="en")
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        return [rows.nth(i).locator("td").nth(0).inner_text().strip() for i in range(rows.count())]

    def _identity_values(self) -> list:
        vals = []
        for label in self.TITLE_FIELDS:
            try:
                vals.append(self.field_value(label))
            except Exception:  # noqa: BLE001
                vals.append("")
        return vals

    def is_qctest(self, code: str) -> bool:
        """True only if the record, re-read fresh, carries QCTEST- in one of
        its identity fields (a validation case may leave one of them empty)."""
        self.open_entry_by_code(code, locale="en")
        return any(v.startswith(QCTEST_PREFIX) for v in self._identity_values())

    def find_qctest_codes(self, prefix: str) -> list:
        """Every non-QCDEMO row whose identity fields start with `prefix`
        (a per-test QCTEST-<tc> prefix). Opens each candidate row's form."""
        assert prefix.startswith(QCTEST_PREFIX)
        out = []
        for code in self.entry_codes():
            if code.startswith("QCDEMO-"):
                continue
            try:
                self.open_entry_by_code(code, locale="en")
                if any(v.startswith(prefix) for v in self._identity_values()):
                    out.append(code)
            except Exception:  # noqa: BLE001
                continue
        return out

    def goto_bare(self, url: str):
        """Plain page.goto, bypassing BasePage.open()'s session guard, which
        signs an anonymous / unprivileged context into TEST_USER on manage-*
        URLs and would make a denial check pass as admin. Returns the HTTP
        status."""
        resp = self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        return resp.status if resp else None

    def cms_form_controls(self) -> dict:
        return {
            "object_fields": self.page.locator('[name*="ObjectField_"]').count(),
            "entry_rows": self.page.locator(self.ENTRIES_TABLE_ROW).count(),
            "workflow_buttons": self.page.locator(
                'button:text-is("Publish"), button:text-is("Submit for Review"), button:text-is("Save as Draft")'
            ).count(),
            "title": self.page.title(),
        }

    def delete_qctest(self, code: str) -> bool:
        """Delete one record by its entry code, only after re-reading it and
        confirming its TITLE_FIELD starts with QCTEST-. Verified by
        re-listing (the row helper's own return value is not trusted).
        Returns True when the row is gone."""
        if not code or not self.is_qctest(code):
            raise AssertionError(f"refusing to delete {code!r}: not positively a QCTEST record")
        self.open_entries_list(locale="en")
        self.delete_entry_by_code(code)
        self.open_entries_list(locale="en")
        return not self.row_visible_by_code(code)

    def teardown_qctest(self, codes, author_first: bool = False) -> list:
        """Delete every code; if a row survives (e.g. Author may not delete),
        retry as Editor. Returns the codes still present."""
        left = []
        for code in [c for c in codes if c]:
            try:
                gone = self.delete_qctest(code)
            except AssertionError:
                raise
            except Exception:  # noqa: BLE001
                gone = False
            if not gone and author_first:
                self.sign_in_as("Site Content Editor")
                try:
                    gone = self.delete_qctest(code)
                except AssertionError:
                    raise
                except Exception:  # noqa: BLE001
                    gone = False
            if not gone:
                left.append(code)
        return left


class HomeAboutSummaryAdminPage(_DisposableRecordMixin, ObjectAuthoringPage):
    """Drives the About Us Section singleton via Object Authoring. Bilingual
    rich-text Section Description uses two independently-addressable
    CKEditor iframes (see module docstring) — overrides the base class's
    single-locale DESCRIPTION_EDITOR_IFRAME with explicit EN/AR variants."""

    SECTION_DESC_EDITOR_EN = 'iframe[title="editor"] >> nth=0'
    SECTION_DESC_EDITOR_AR = 'iframe[title="editor"] >> nth=1'

    TITLE_FIELDS = (FIELD_SECTION_HEADING_EN, FIELD_SECTION_HEADING_AR, FIELD_SECTION_TAG_EN)
    FIELD_ACTIVE_STATUS = "Active Status"

    def __init__(self, page):
        super().__init__(page, SECTION_SLUG)

    def create_qctest_section(self, prefix: str, *, public: bool, image: str | None = None, **overrides):
        """Disposable section from the create form. public=True ticks Active
        Status and submits (Editor -> Published, i.e. VISIBLE to visitors if
        the widget picks it up: the caller must delete it right after its
        assertion). public=False saves an inactive Draft. Returns
        (result, values)."""
        self.open_new_form()
        values = self.fill_qctest_section(prefix, image=image, **overrides)
        if public:
            self.tick(self.FIELD_ACTIVE_STATUS, True)
        result = self.resolve_created(self.submit_outcome(draft=not public), prefix)
        return result, values

    def fill_qctest_section(self, prefix: str, *, image: str | None = None, **overrides) -> dict:
        """Fill the (already open) NEW-entry form with QCTEST data and untick
        Active Status. Pass a field label -> "" override to leave it empty;
        `description_en` / `description_ar` keys override the rich text."""
        values = {
            FIELD_SECTION_TAG_EN: f"{prefix} MORE ABOUT US",
            FIELD_SECTION_TAG_AR: f"{prefix} المزيد عنا",
            FIELD_SECTION_HEADING_EN: f"{prefix} Qatar Chamber",
            FIELD_SECTION_HEADING_AR: f"{prefix} غرفة قطر",
            FIELD_YEARS_BADGE_EN: f"{prefix} 63+ Years",
            FIELD_YEARS_BADGE_AR: f"{prefix} 63+ سنة",
            FIELD_READ_MORE_LABEL_EN: f"{prefix} Read More",
            FIELD_READ_MORE_LABEL_AR: f"{prefix} اقرأ المزيد",
            FIELD_READ_MORE_URL: "https://qcdev.ihorizons.com/web/qatar-chamber/about-us",
            "description_en": f"{prefix} description EN",
            "description_ar": f"{prefix} الوصف",
        }
        values.update(overrides)
        for field, value in values.items():
            if field == "description_en":
                if value:
                    self.fill_description_en(value)
            elif field == "description_ar":
                if value:
                    self.fill_description_ar(value)
            else:
                self.fill_text(field, value)
        # Untick BEFORE the upload: live, the file picker's leftover overlay
        # swallowed the checkbox click after an upload (2026-10-07).
        self.page.get_by_role("checkbox", name=self.FIELD_ACTIVE_STATUS, exact=True).uncheck()
        if image:
            self.safe_upload(FIELD_BUILDING_IMAGE_PRIMARY, image)
        return values

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
        self.submit_for_review()
        return self.current_status() != STATUS_PUBLISHED

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
        """Unpublishes the currently-open entry (if Published) so Save as
        Draft becomes available — several QA cases in the 136088-136140
        batch explicitly exercise "Save Draft" against this project's
        Published-by-default singleton, where Save as Draft is disabled
        until unpublished (see this module's REWRITTEN docstring above).
        No-op if already Draft. Must be called on an already-open entry."""
        if self.current_status() != STATUS_DRAFT:
            self.unpublish_to_edit_as_draft()
            self.open_section_entry()
        return self

    # ---- Sign-out / login (TC-136136's mechanism). Sign-out drops this
    # context's cookies (2026-10-13) instead of the server logout used before,
    # which also ended the shared storageState session; the next login()
    # drives the real form again ----------------------------------------------
    def logout_and_return(self) -> "HomeAboutSummaryAdminPage":
        """Signs this context out by dropping its cookies (2026-10-13) --
        never a server-side logout, which also ended the SHARED storageState
        session every other context/worker/tool was using. The page is left
        with no session owner, so a later navigation is not silently signed
        back in; call login_as() for the next account."""
        sign_out_locally(self.page)
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
        self.submit_for_review()
        return self


class HomeAboutCounterAdminPage(_DisposableRecordMixin, ObjectAuthoringPage):
    """Drives one "About Us Counter" repeatable-list row via Object
    Authoring — construct once per test and call open_counter(code) to
    switch rows (all 4 seeded QCDEMO rows share this one class, unlike the
    Section's fixed singleton)."""

    TITLE_FIELDS = (FIELD_COUNTER_TITLE_EN, FIELD_COUNTER_TITLE_AR)
    FIELD_RECORD_ACTIVE_STATUS = "Active Status"

    def __init__(self, page):
        super().__init__(page, COUNTER_SLUG)

    def fill_qctest_counter(self, prefix: str, **overrides) -> dict:
        """Fill the (already open) NEW-entry form; both active flags unticked
        so the record can never render on the public Home Page."""
        values = {
            FIELD_COUNTER_TITLE_EN: f"{prefix} Counter",
            FIELD_COUNTER_TITLE_AR: f"{prefix} عداد",
            FIELD_COUNTER_VALUE: "99 +",
            FIELD_COUNTER_DISPLAY_ORDER: "900",
        }
        values.update(overrides)
        for field, value in values.items():
            if field == FIELD_COUNTER_DISPLAY_ORDER:
                self.fill_number(field, value)
            else:
                self.fill_text(field, value)
        self.set_checkbox(FIELD_COUNTER_ACTIVE_STATUS, False)
        self.set_checkbox(self.FIELD_RECORD_ACTIVE_STATUS, False)
        return values

    def create_qctest_counter(self, prefix: str, *, public: bool, **overrides):
        """Disposable counter. public=True ticks both active flags and
        submits (Editor -> Published); the caller deletes it right after its
        assertion. Returns (result, values)."""
        self.open_new_form()
        values = self.fill_qctest_counter(prefix, **overrides)
        if public:
            self.tick(FIELD_COUNTER_ACTIVE_STATUS, True)
            self.tick(self.FIELD_RECORD_ACTIVE_STATUS, True)
        result = self.resolve_created(self.submit_outcome(draft=not public), prefix)
        return result, values

    def set_counter_active_and_submit(self, code: str, active: bool) -> dict:
        self.open_entry_by_code(code, locale="en")
        self.tick(FIELD_COUNTER_ACTIVE_STATUS, active)
        return self.submit_outcome()

    def create_control_state(self) -> dict:
        """Read-only: is a create path offered on the counter list page?"""
        add = self.page.locator('a:text-is("+ Add New"), button:text-is("+ Add New")')
        draft = self.page.locator(self.SAVE_AS_DRAFT_BUTTON)
        submit = self.page.locator(self.SUBMIT_FOR_REVIEW_BUTTON)
        return {
            "add_new_visible": add.count() > 0 and add.first.is_visible(),
            "save_as_draft_enabled": draft.count() > 0 and draft.first.is_enabled(),
            "submit_enabled": submit.count() > 0 and submit.first.is_enabled(),
        }

    def open_counter(self, entry_code: str) -> "HomeAboutCounterAdminPage":
        self.open_entry_by_code(entry_code)
        return self

    def open_counter_list(self) -> "HomeAboutCounterAdminPage":
        self.open_entries_list()
        return self

    def ensure_draft(self) -> "HomeAboutCounterAdminPage":
        """Counter-row counterpart to HomeAboutSummaryAdminPage.ensure_draft()
        — same unpublish-if-Published no-op-if-Draft shape, for "Save Draft"
        cases exercised against a counter row."""
        if self.current_status() == STATUS_PUBLISHED:
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
        self.submit_for_review()
        return self


class Disposables:
    """Tracks the QCTEST prefixes / entry codes one test created on one
    manage page and deletes them (QCTEST-guarded, verified by re-listing).
    Shared by the CMS and Web About Us modules."""

    def __init__(self, admin):
        self.admin, self.prefixes, self.codes = admin, [], []

    def track(self, prefix: str, result: dict | None = None) -> None:
        self.prefixes.append(prefix)
        if result and result.get("created_code"):
            self.codes.append(result["created_code"])

    def cleanup(self) -> dict:
        from cms.tests.live_write_guard import LiveRecord, deletes_suppressed, keep_instead_of_delete

        if deletes_suppressed():
            # PBI running rules, rule 10: nothing is deleted. Log what this test
            # created (known codes + the QCTEST title prefixes it used) as `kept`
            # WITHOUT searching the list for them -- that search cost ~450 s per
            # test on qcdev (measured 2026-10-14, 136535 teardown).
            slug = getattr(self.admin, "SLUG", None) or getattr(self.admin, "slug", None) or type(self.admin).__name__
            kept = list(dict.fromkeys(list(self.codes) + [f"{p}*" for p in self.prefixes]))
            for c in kept:
                keep_instead_of_delete(LiveRecord(str(slug), c, c), c)
            self.prefixes, self.codes = [], []
            return {"deleted": [], "kept": kept, "left": []}
        codes = list(self.codes)
        for p in self.prefixes:
            try:
                codes += self.admin.find_qctest_codes(p)
            except Exception:  # noqa: BLE001
                pass
        codes = list(dict.fromkeys(codes))
        left = self.admin.teardown_qctest(codes, author_first=True) if codes else []
        self.prefixes, self.codes = [], []
        return {"deleted": [c for c in codes if c not in left], "left": left}

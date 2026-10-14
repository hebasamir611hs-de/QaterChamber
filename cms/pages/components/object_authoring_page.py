"""
cms/pages/components/object_authoring_page.py — ObjectAuthoringPage.

Shared, per-object-agnostic Control_Panel Page Object for the
`object-authoring` -> `manage-<slug>` editorial lifecycle, documented in
.claude/context/active/standards.md's "Content Editorial Workflow — Seven
States, and the Account Decides the Path" section.

CITATION CORRECTED 2026-09-28. This docstring previously cited a
standards.md section titled "Object Authoring — Draft / Preview / Publish /
Unpublish Lifecycle". **That section never existed** — checked against the
full history of standards.md, it was never written under that name. The
reference nonetheless read as though the two-state Draft/Approved model
below had been independently agreed and written down, when in fact it only
ever lived in this docstring, derived from probing the live site through a
super-admin session. That borrowed authority is a large part of why the
wrong model went unchallenged for weeks: a reader had no obvious reason to
re-derive something standards.md appeared to already mandate. The lifecycle
is now genuinely documented, in the section named above.

Lives under pages/components/ (the plugin's flat shared-component
exception) because the state machine really is generic across every listed
Object — only the slug and field data vary per object. That genericity is
not taken on faith from the phantom section's supposed "Testing
implication" note: it was verified directly on 2026-09-28 across eight
objects (law-entry, news-article, promotional-banner, hero-banner-slide,
publication, about-hero-banner, social-media-icon, strategic-partner),
every one of which renders the same buttons, badges and row actions.

Field-level locators (Title, Banner Alt Text (EN), etc.) stay OUT of this
class — they belong to each object's own admin Page Object (e.g.
HomeLatestNewsAdminPage, HomePromoBannersAdminPage), which composes this
class for its lifecycle cases instead of duplicating the state machine.

SUPERSEDED IN PART 2026-09-28 — READ THIS BEFORE THE 2026-09-03 NOTES BELOW.
=============================================================================
Everything below dated 2026-09-03 was observed through an **admin session**
(`test@liferay.com`). That account is a *privileged submitter*, and the site
runs a real Kaleo editorial workflow (`build-resources/workflow/
qc-editorial-approval.xml`) whose condition node routes privileged submitters
straight past the review step. So the two-state Draft/Approved machine those
notes describe is not the system's behaviour — it is one account's view of it.

Re-verified live 2026-09-28 by walking a single probe record end to end on
manage-law-entry as QC Site Content Author (156492) and QC Site Content Editor
(156488), then cross-checking seven further objects (news-article,
promotional-banner, hero-banner-slide, publication, about-hero-banner,
social-media-icon, strategic-partner). The workflow is GLOBAL, not per-object:
every one of them shows the same buttons, badges and row actions.

What actually changed versus the notes below:

  - The form button reads **"Submit for Review"**, not "Submit for
    Publishing". The old string matches nothing. Toast on success is
    "Saved and submitted for review."
  - The same button lands on DIFFERENT states depending on the account —
    confirmed on one record submitted twice: Author -> "Pending Review"
    (not public), Editor -> "Published" directly. A test that asserts a
    lifecycle outcome without pinning the account is asserting nothing.
  - The entries-table badge reads **PUBLISHED**, not APPROVED.
  - There are seven states, not two: Draft, Pending Review, Rejected,
    Published, Unpublished, Archived, Scheduled. See WORKFLOW_STATUSES.
  - The editing banner CAPITALISES the state — "Editing <title> (Draft).
    Save as Draft or Submit for Review updates this record." The old
    case-sensitive "(draft)"/"(approved)" parsing therefore reported
    "Unknown" even for a plain draft.
  - Unpublish lands on **Unpublished**, a distinct state — NOT Draft. Its
    confirm() says so verbatim. Archive is reachable from Unpublished only;
    Restore returns to Unpublished, not to Published.
  - Row workflow actions (Approve, Reject, Resubmit, Publish, Unpublish,
    Archive, Restore, Return to Author, Schedule, History) each carry a
    stable `data-qc-oel-<action>="<entryId>"` attribute, the same convention
    the pre-existing `data-qc-oel-delete` used. Which ones render depends on
    the row's status AND the signed-in role.
  - Those actions drive NATIVE confirm()/prompt() dialogs, often CHAINED
    (confirm then prompt). Reject and Return to Author raise a prompt whose
    comment reaches the author and is kept in History; Return's is required.
  - Each row has a **History** modal holding the audit trail (actor,
    timestamp, comment) — previously unmodelled, and the best available
    evidence for a workflow assertion.
  - `Active Status` is a real form field and **defaults to unchecked** on a
    new entry. It is a second, independent visibility gate: "Published"
    alone does not put a record in front of a visitor.
  - Saving a Draft skips required-field validation; Submit for Review
    enforces it and refuses with "Please complete the required fields before
    proceeding with the workflow action for <title>. Nothing has been
    submitted." — nothing is written in that case.
  - The entries list's Status filter is built from the statuses actually
    present in the list, not from a fixed vocabulary.

Not yet exercised live: the Scheduled state (status 7) and the Publish action
from Unpublished. Treat those two as unverified until someone walks them.

CONFIRMED LIVE 2026-09-03 (headed-equivalent Chromium via Playwright MCP,
qcdev, existing authenticated admin session) — live end-to-end cycle run
against a real disposable "QCTEST-OBJAUTH-PROBE" News Article entry
(create -> Save as Draft -> Preview banner -> Submit for Publishing ->
edit -> Unpublish to edit as draft -> Delete), plus independent field-set
probes on manage-promotional-banner:

  - `manage-<slug>` with NO `editEntry` query param IS the create-new form,
    rendered directly below the object's own entries table — Save as Draft
    / Submit for Publishing buttons, no separate "Add" control to click
    first.
  - `manage-<slug>?editEntry=<code>` opens an existing entry. A Draft
    entry's banner text is exactly: 'Editing "<title>" (draft). Save as
    Draft or Submit for Publishing updates this record.' with both buttons
    enabled. An Approved/published entry's banner text is exactly:
    'Editing "<title>" (approved). It is published, so Save as Draft is
    unavailable until you unpublish it.', with `Save as Draft` DISABLED, a
    "Cancel and add a new entry instead" link, and an "Unpublish to edit as
    draft" button — CONFIRMED this button only renders after the page has
    re-settled post-navigation (a short, real-condition wait_for is
    required; it is not present in the very first render tick after the
    Edit-link click completes networkidle).
  - Field-level form controls do NOT expose stable ids/classes — Liferay's
    Page Builder fragment framework mints a fresh `fragment-<uuid>-...`
    dom id per page load. `page.get_by_label(...)` was tried FIRST per
    locator-priority and failed live (times out — the visible label text
    is not wired as this framework's accessible label association);
    `page.get_by_role(<role>, name=<visible label text>, exact=True)` DOES
    resolve correctly (confirmed live: Title, Publication Date, Banner Alt
    Text (EN), etc. all match their own rendered accessible name) — used
    throughout this class and every composing admin Page Object's
    Draft/Preview/Publish/Unpublish methods.
  - File-upload fields reuse the SAME "Select File" -> Documents-and-Media
    picker -> "Add" flow already documented project-wide (e.g.
    HomePromoBannersAdminPage._upload_image()) — the one confirmed-live
    difference on THIS surface is the picker iframe carries no `title`
    attribute (the raw-admin surface's picker uses
    `iframe[title="Select File"]`); here it is identified by its `src`
    instead (`iframe[src*="selectFileEntry"]`) — same underlying Liferay
    item-selector widget, different embed context. The "Select File"
    button for a given field is reached by first locating that field's own
    hidden filename textbox (confirmed-live accessible name pattern:
    "<Field Label> Select File", e.g. "Banner Image (EN) Select File") and
    then its sibling button — button and hidden textbox are confirmed-live
    DOM siblings under the same wrapper.
  - Delete: the row's own `Delete` link fires a native browser `confirm()`
    dialog (confirmed live, exact text: 'Delete "<title>"? This cannot be
    undone — Object entries do not go to the recycle bin.') — callers MUST
    register a `page.once("dialog", ...)` accept handler BEFORE clicking,
    mirroring the pattern already used in
    test_org_structure_control_panel.py. The link can also be obscured by
    the site-wide chatbot launcher intercepting pointer events (confirmed
    live) — clicked with `force=True` to bypass that overlay rather than
    fighting it, since Delete's own native-dialog confirm is the real gate
    on the action, not the click itself. Each entry's row delete link
    carries a stable `data-qc-oel-delete="<entryId>"` attribute (confirmed
    live) — used to scope the delete to exactly the row this test created,
    never a same-titled real row.
  - Unpublish similarly fires a native `confirm()` dialog (confirmed live,
    exact text: 'Unpublish "<title>"? It comes off the live site
    immediately and becomes a draft you can keep editing. Publish it again
    when you are ready.') — same `page.once("dialog", ...)` pattern.
  - CORRECTED 2026-09-08 (Hero Banner Slide's "Banner Image" field —
    manage-hero-banner-slide, PBI 129367): the SAME `iframe[src*=
    "selectFileEntry"]` item-selector modal `upload_file()` opens actually
    supports TWO different sub-flows, confirmed live via Playwright MCP —
    (1) `upload_file()`'s own drag-drop-a-NEW-file flow (the "Drag & Drop
    Your Files or Browse to Upload" zone -> "1 of 1" progress -> "Add"
    button), and (2) selecting an EXISTING file already in the library: a
    SINGLE CLICK directly on an existing file's own card (after navigating
    into a folder, e.g. this project's Flickr-import folder — see
    cms-profile.md's "Flickr Pro API" note) selects it and closes the
    modal IMMEDIATELY — no "Add" button, no upload-progress wait. A prior
    session used flow (1) for a field whose real, intended usage on THIS
    project is flow (2) and, combined with several required text fields
    being left unfilled (native HTML5 "Please fill out this field"
    validation silently blocking the Submit button with zero network
    calls — mistaken at the time for a silent product no-op), concluded a
    false product-defect finding. See HeroBannerSlideAdminPage's own
    module docstring for the full corrected evidence trail and
    `select_existing_file_from_library()` below for the real mechanism,
    now used by that field instead of `upload_file()`.
  - The right-hand Preview pane AND the row's own `Preview` link both
    resolve to `/web/qatar-chamber/home?qcPreview=<objecttype>%3A<id>` — a
    real navigation to the live Home page with that specific record pinned
    for preview, NOT a same-page-only iframe render. Confirmed live for
    Service Cards specifically that this preview renders the FULL Home
    page section around that record (Tag/Heading/Description AND the tab
    strip AND the card grid together, not just the one card) — see
    home_services_admin_page.py's updated PREVIEW SURFACE FINDING. Status
    banner text inside that page is exactly:
      - Draft entry: "PREVIEW — showing an unpublished (draft) <objecttype>
        record. Visitors do not see this."
      - Approved entry: "PREVIEW — showing a published <objecttype>
        record, exactly as visitors see it."
"""

import re

from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from config.settings import control_panel_url

logger = get_logger("object_authoring_page")

# Confirmed-live-absent-on-first-render-tick grace: the "Unpublish to edit
# as draft" button/banner needs a real settle after the Edit-link's own
# networkidle before it reliably appears (see module docstring). Kept as
# a real wait_for with this as the upper-bound timeout, not a blind sleep.
APPROVED_BANNER_SETTLE_TIMEOUT_MS = 8000


# ── Workflow status vocabulary ──────────────────────────────────────────
# CONFIRMED LIVE 2026-09-28 by walking the full loop on manage-law-entry as
# Author (156492) then Editor (156488), and cross-checked on seven further
# objects. The entries-table badge renders UPPERCASE; these are the
# normalized forms every reader below returns and every caller compares to.
STATUS_DRAFT = "Draft"
STATUS_PENDING_REVIEW = "Pending Review"
STATUS_REJECTED = "Rejected"
STATUS_PUBLISHED = "Published"
STATUS_UNPUBLISHED = "Unpublished"
STATUS_ARCHIVED = "Archived"
STATUS_SCHEDULED = "Scheduled"
STATUS_UNKNOWN = "Unknown"
# NOT a workflow state (the seven above are). Observed live 2026-10-07 and
# again 2026-10-13: a record PUBLISHED with its own `Active Status` unticked
# badges `INACTIVE` in the entries list and reads "Editing <title>
# (Inactive). Publish saves your changes; the record stays Inactive." on the
# form, with no Unpublish row action. It is the second visibility gate
# (Active Status) showing through the badge, so it is kept OUT of
# WORKFLOW_STATUSES and reported on its own rather than as Unknown. Whether
# that badge is intended is an open question in the 2026-10-08 bug list (B7).
STATUS_INACTIVE = "Inactive"

WORKFLOW_STATUSES = (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_REJECTED,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
    STATUS_ARCHIVED,
    STATUS_SCHEDULED,
)

# Only this one is visible to an anonymous visitor, and only while the
# record's own `Active Status` field is ticked — that checkbox is a second,
# independent gate and it DEFAULTS TO UNCHECKED on a new entry (confirmed
# live 2026-09-28). "Published" alone is NOT sufficient for visitor
# visibility; assert both.
VISITOR_VISIBLE_STATUS = STATUS_PUBLISHED

# Deprecated: this build has no "Approved" badge — it reads "Published".
# Kept so a stale comparison fails loudly at import review rather than
# silently never matching.
STATUS_APPROVED_LEGACY = STATUS_PUBLISHED


def selector_safe_escape(text: str) -> str:
    """re.escape() plus a backslash before every "/", for a pattern handed to a Playwright
    locator (see ObjectAuthoringPage.label_pattern)."""
    return re.escape(text).replace("/", r"\/")


class UploadNotApplied(RuntimeError):
    """The Documents & Media picker closed (or refused) without the field
    showing a file. Raised by ObjectAuthoringPage.upload_file() instead of
    returning as if the upload had worked (2026-10-13)."""


class UploadPickerUnavailable(RuntimeError):
    """The picker never opened -- an environment failure, NOT a rejection.
    Deliberately not an UploadNotApplied, so upload_file_expect_rejected()
    cannot read it as "the server refused the file" (false green)."""


def normalize_status(raw: str) -> str:
    """Map any rendered status badge / banner fragment onto the canonical
    vocabulary above, case- and whitespace-insensitively.

    REPLACES the previous `.strip().capitalize()` normalization, which was
    actively wrong for the only two-word status: `"PENDING REVIEW"
    .capitalize()` yields `"Pending review"`, so a caller comparing against
    `"Pending Review"` could never match no matter how correct the app was.
    Returns STATUS_UNKNOWN (never raises) for anything unrecognized, so an
    unexpected state surfaces as an explicit unknown instead of being
    silently coerced into a neighbouring one."""
    if not raw:
        return STATUS_UNKNOWN
    collapsed = " ".join(raw.strip().split()).casefold()
    for known in WORKFLOW_STATUSES:
        if collapsed == known.casefold():
            return known
    # The legacy build's wording, still possible on an un-migrated object.
    if collapsed == "approved":
        return STATUS_PUBLISHED
    if collapsed == STATUS_INACTIVE.casefold():
        return STATUS_INACTIVE
    return STATUS_UNKNOWN



class ObjectAuthoringPage(BasePage):
    """Drives one Object's `manage-<slug>` page via the object-authoring
    surface. Construct with the object's slug (e.g. "news-article",
    "promotional-banner") — every locator/method below is generic across
    objects per the confirmed-live state machine documented above; only
    the slug (and the field data callers fill in on the object's own admin
    Page Object) varies per object."""

    SAVE_AS_DRAFT_BUTTON = 'button:has-text("Save as Draft")'
    # RENAMED LIVE 2026-09-28 — the form button reads "Submit for Review"
    # on every object sampled (see module docstring). The old
    # "Submit for Publishing" string matches NOTHING on the current build;
    # SUBMIT_FOR_PUBLISHING_BUTTON is kept only as a deprecated alias so
    # existing callers keep resolving, and points at the same real button.
    #
    # CORRECTED 2026-09-30 — the label is not fixed. Read live on
    # manage-business-event as TEST_USER: the submit button reads "Publish",
    # with the helper text "As an Editor, what you publish here goes live
    # straight away." The 2026-09-28 walk above saw "Submit for Review" for
    # Author and Editor on manage-law-entry. Matching only "Submit for Review"
    # timed out on the TEST_USER form, so both labels are matched; `text-is`
    # keeps "Unpublish" out, and the form renders one of the two.
    SUBMIT_FOR_REVIEW_BUTTON = (
        'button[type="submit"]:text-is("Submit for Review"), '
        'button[type="submit"]:text-is("Publish")'
    )
    SUBMIT_FOR_PUBLISHING_BUTTON = SUBMIT_FOR_REVIEW_BUTTON
    # In-flight state of a Save as Draft / Submit for Review / Publish click.
    # CONFIRMED LIVE 2026-10-02 (manage-coo-quick-fact, as Editor): once
    # clicked, both form buttons gain class "disabled" and an inner
    # <span class="loading-animation ...">. The span stays until the save
    # commits, about 50s on qcdev that day, and then the page navigates to
    # `?previewEntry=<uuid>`. Right after the click, before the spinner, the
    # clicked button carries a bare `disabled` attribute. SUBMIT_STARTED
    # (attach) uses both signals. FORM_BUSY (detach) is the spinner only,
    # because a form button can be disabled at rest.
    FORM_BUSY = 'button[type="submit"] .loading-animation'
    SUBMIT_STARTED = (
        f'{FORM_BUSY}, '
        'button[type="submit"][disabled]:text-is("Submit for Review"), '
        'button[type="submit"][disabled]:text-is("Publish"), '
        'button[type="submit"][disabled]:text-is("Save as Draft")'
    )
    # Row-level workflow actions carry a stable `data-qc-oel-<action>="<entryId>"`
    # attribute (confirmed live 2026-09-28 on manage-publication /
    # manage-law-entry / manage-social-media-icon) — the same convention the
    # pre-existing `data-qc-oel-delete` already used. Preferred over text
    # matching: the visible label is localised, the attribute is not.
    ROW_ACTION_ATTRS = {
        "approve": "data-qc-oel-approve",
        "reject": "data-qc-oel-reject",
        "resubmit": "data-qc-oel-resubmit",
        "publish": "data-qc-oel-publish",
        "unpublish": "data-qc-oel-unpublish",
        "archive": "data-qc-oel-archive",
        "restore": "data-qc-oel-restore",
        "return": "data-qc-oel-return",
        "schedule": "data-qc-oel-schedule",
        "history": "data-qc-oel-history",
        "delete": "data-qc-oel-delete",
    }
    # Legacy in-form Unpublish button. CONFIRMED LIVE 2026-09-28: the
    # current build exposes Unpublish as a ROW action (see unpublish_entry())
    # and the in-form button, where present, no longer carries the
    # "to edit as draft" wording — it is matched on the verb alone.
    UNPUBLISH_BUTTON = 'button:has-text("Unpublish")'
    CANCEL_AND_ADD_NEW_LINK = 'a:has-text("Cancel and add a new entry instead")'
    # The page's own banner element (live 2026-10-13): it carries the editing
    # banner in EVERY locale ("Editing ..." and its Arabic render) and in
    # every status, AND the Access Denied note a role that may not edit the
    # record gets instead of the banner. Locale- and role-independent settle.
    EDIT_BAR = "[data-qc-oel-editbar]"
    # The Access Denied note (live 2026-10-13, Site Content Author on a
    # Published GM / About / Chamber Laws record): "Access Denied. You do not
    # have permission to perform this action. "<code>" is Published. Only a
    # Content Editor can change a record once it has reached the website -
    # you can view its status here." Form fields and both submit buttons are
    # disabled. Matched on the English sentence (CMS admin is English-only).
    ACCESS_DENIED_TEXT = "Access Denied"
    ENTRIES_TABLE_ROW = "table tbody tr"

    UPLOAD_MODAL_IFRAME = 'iframe[src*="selectFileEntry"]'
    UPLOAD_MODAL_ADD_BUTTON_TEXT = "Add"
    # 2026-10-13 (PBI 129388 run: 8x set_input_files 30 s timeouts). The Add
    # button is in the DOM at once but disabled until the server-side upload
    # completes; Clay disables by attribute or class, so all three are excluded.
    UPLOAD_MODAL_ADD_ENABLED = (
        'button:has-text("Add"):not([disabled]):not([aria-disabled="true"]):not(.disabled):visible'
    )
    UPLOAD_MODAL_ERROR = '.alert, .form-feedback-item, [role="alert"]'
    UPLOAD_MODAL_CLOSE = (
        '.modal-dialog:has(iframe[src*="selectFileEntry"]) button.close, '
        '.modal-dialog:has(iframe[src*="selectFileEntry"]) [aria-label="close"], '
        '.modal-dialog:has(iframe[src*="selectFileEntry"]) [aria-label="Close"]'
    )
    UPLOAD_PICKER_OPEN_MS = 20000
    UPLOAD_ADD_ENABLED_MS = 60000
    UPLOAD_DETACH_MS = 30000
    UPLOAD_READOUT_MS = 10000
    # Live 2026-10-13: Add is ABSENT (not disabled) until the server-side
    # upload completes, and the first click on it is intermittently ignored.
    UPLOAD_ADD_CLICKS = 3
    UPLOAD_ADD_SETTLE_MS = 6000

    # CKEditor rich-text description field — CONFIRMED LIVE 2026-09-03 against
    # manage-strategic-pillar-card: unlike the raw Object Definitions editor's
    # equivalent field (see home_strategic_direction_admin_page.py's
    # PILLAR_DESCRIPTION note, which needs a click to lazily mount its
    # iframe), THIS surface's `<iframe title="editor">` is already mounted
    # and directly fillable via BasePage.fill_iframe_editor() with no prior
    # click — verified by a live write + read-back round trip. Generic across
    # every object that has a single rich-text field on this surface.
    # HEALED 2026-09-07 (live re-investigation, manage-strategic-pillar-
    # card): a bilingual rich-text field (e.g. Pillar Description) mounts
    # TWO CKEditor iframes matching a bare `iframe[title="editor"]` — one
    # per locale (EN/AR). `:visible` alone did NOT disambiguate them
    # (confirmed live: BOTH report visible per Playwright's own visibility
    # check — unlike the detached-menu-node pattern documented elsewhere in
    # this project, these are two live-rendered CKEditor instances, not one
    # real + hidden leftovers). `>> nth=0` deterministically selects the
    # FIRST-mounted instance, confirmed live to be the default-locale (EN)
    # editor on a freshly opened create/edit form, before any locale toggle
    # is touched — the only state this class's fill_rich_text()/
    # rich_text_value() are used in.
    # RESTORED 2026-09-28 (dropped by the merge; description_editor_iframe()
    # builds per-field selectors from it).
    RICH_TEXT_EDITOR_IFRAME_CSS = 'iframe[title="editor"]'
    DESCRIPTION_EDITOR_IFRAME = 'iframe[title="editor"] >> nth=0'

    def fill_rich_text(self, text: str, field_name: str | None = None) -> "ObjectAuthoringPage":
        self.fill_iframe_editor(self.description_editor_iframe(field_name), text)
        return self

    def rich_text_value(self, field_name: str | None = None) -> str:
        return self.iframe_editor_text(self.description_editor_iframe(field_name))

    def __init__(self, page, slug: str):
        super().__init__(page)
        self.slug = slug
        # RESTORED 2026-09-28 (dropped by the merge). Entry code of whatever
        # record was last opened for edit through this object — set by
        # open_entry_by_code()/open_entry_by_edit_link() so reopen() and
        # wait_for_status() can re-read it from a FRESH navigation instead
        # of trusting a stale, post-save-reflowed DOM.
        self._entry_code: str | None = None
        # Interface locale this object last navigated in ("en"/"ar"/None for
        # "whatever the session happens to be") — see _manage_url().
        self._locale: str | None = None

    # ---- Navigation -----------------------------------------------------
    def _manage_url(
        self, edit_entry: str | None = None, locale: str | None = None
    ) -> str:
        # `locale` RESTORED 2026-09-28 (dropped by the merge). Pinning the
        # interface language matters: an Edit link clicked out of an UNPINNED
        # list inherits whatever locale the session drifted to (ar_SA on the
        # shared qcdev authoring account), against which every English
        # label_pattern() lookup on the form resolves ZERO controls.
        prefix = f"/{locale}" if locale else ""
        path = f"{prefix}/web/qatar-chamber/manage-{self.slug}"
        if edit_entry:
            path += f"?editEntry={edit_entry}"
        return control_panel_url(path)

    def open_new_entry_form(self, locale: str | None = None) -> "ObjectAuthoringPage":
        """`manage-<slug>` with no editEntry param IS the create-new form —
        no separate "Add"/"New" button to click first. Widened to 35000ms
        (from 20000ms) 2026-09-03: manage-promotional-banner's cold first
        render (fresh pytest-launched browser context, first navigation of
        the test) intermittently outlived the original 20s budget live
        this session even though the same URL rendered near-instantly in
        an already-warm, long-lived session — a real page-load latency
        difference on first hit, not a wrong locator (SAVE_AS_DRAFT_BUTTON
        itself was never wrong)."""
        self.open(self._manage_url(locale=locale))
        self._entry_code = None
        self._locale = locale
        self.wait_for(self.SAVE_AS_DRAFT_BUTTON, timeout=35000)
        return self

    def open_entries_list(self, locale: str | None = None) -> "ObjectAuthoringPage":
        """Navigates to `manage-<slug>` and waits on the entries table
        itself (`a[data-qc-oel-delete]`, first match) rather than the
        create-new form's own Save-as-Draft button — teardown only needs
        the list to find/delete a row, not a mounted form, and waiting on
        the wrong signal cost a real 20s timeout live 2026-09-03 when this
        method didn't exist yet and teardown called open_new_entry_form()
        instead.

        Widened to 35000ms (from 20000ms) 2026-09-08, mirroring
        `open_new_entry_form()`'s own identical precedent above: live-
        observed on manage-hero-banner-slide (Hero Banner Slide PBI
        129367's own tc_135010/tc_135018 correction batch) that this exact
        20s budget intermittently timed out on a `finally`-block teardown
        re-check call specifically, under real qcdev load from a
        concurrently-running, unrelated process also mutating this same
        Object's entries table at the time — the entry BEING torn down had
        already been created/deleted correctly by the test's own earlier,
        successful calls to this same method; only this later, redundant
        best-effort re-check call raced the busier table. Not a locator
        bug (`a[data-qc-oel-delete]` itself was never wrong) — a real,
        environment-load-dependent render-latency budget, same class of
        finding as `open_new_entry_form()`'s own note."""
        self._locale = locale
        self.open(self._manage_url(locale=locale))
        # Wait for any entries row, not a Delete link (CORRECTED 2026-10-01):
        # a Site Content Author sees Delete only on rows it owns — live, its
        # first page rendered 10 rows and zero `a[data-qc-oel-delete]`, so
        # this timed out for every non-admin account.
        self.wait_for(self.ENTRIES_TABLE_ROW, first=True, timeout=35000)
        self._show_all_rows()
        return self

    # The entries list pages its rows (live 2026-10-13, manage-law-entry:
    # "Showing 1-10 of 12", "Page 1 of 2"), so a row past the 10th was
    # invisible to every title/code lookup -- a freshly created QCTEST law
    # entry "never appeared in the list" (134877 / 134884). The page-size
    # select offers `value="0"` = all rows; choosing it is a view setting only.
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    PAGER_COUNT = "[data-qc-oel-pager-count]"

    def _show_all_rows(self) -> None:
        size = self.page.locator(self.PAGE_SIZE_SELECT)
        counter = self.page.locator(self.PAGER_COUNT)

        def _whole_list_shown() -> bool:
            # "Showing 1-10 of 12" -> partial; no counter / "1-12 of 12" -> whole.
            text = (counter.first.inner_text() or "").strip() if counter.count() else ""
            match = re.search(r"(\d+)\D+(\d+)\D+?(\d+)\s*$", text)
            return not match or match.group(2) == match.group(3)

        try:
            if size.count() == 0 or _whole_list_shown():
                return  # every row is already on this page (e.g. a singleton list)
            size.first.select_option("0")
            # The re-render is client-side; wait until the pager stops
            # reporting a partial page.
            wait_until(_whole_list_shown, timeout=10, poll=0.25)
        except Exception:  # noqa: BLE001 -- a list without the control shows every row already
            logger.warning("open_entries_list: could not switch the list to show all rows")

    def open_entry_by_edit_link(self, title: str) -> "ObjectAuthoringPage":
        """Opens an existing entry for edit via its row's own `Edit` link
        (never a guessed/reconstructed `editEntry` code) — scoped to the
        row matching `title`. Waits past `networkidle` for the editing
        banner's own "Cancel and add a new entry instead" link — confirmed
        live present in BOTH the Draft and Approved editing banners (see
        module docstring) — since the banner/button set is confirmed to
        lag `networkidle` by a real render tick (the same settle
        `unpublish_to_edit_as_draft()` already guards); without this,
        callers reading `editing_banner_text()` or the Unpublish/Save-as-
        Draft button state right after this call can race that lag.

        Clicks with `force=True` and a retry-after-overlay-dismiss
        fallback — confirmed live 2026-09-03 (tc_135125 rerun) that the
        site-wide chatbot launcher intercepting pointer events (already
        documented for the row Delete link) also blocks this Edit link
        intermittently, causing a bare `.click()` to hang for the full
        30s timeout with no recovery. Mirrors BasePage.click()'s own
        recovery shape since a raw Locator (not a selector string) is
        used here and can't go through that wrapper method directly."""
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')
        edit_link = row.get_by_role("link", name="Edit")
        try:
            edit_link.click(timeout=10000)
        except Exception:
            from core.web.overlays import dismiss_overlays

            dismiss_overlays(self.page)
            edit_link.click(force=True)
        self._wait_for_network_settle()
        self._wait_for_editing_banner()
        # FIX 2026-10-13 ("record None ... never reached Published", 120 s):
        # this path never recorded WHICH record it opened, so reopen() raised
        # inside wait_for_status()'s poll and every poll failed silently. The
        # Edit link lands on `?editEntry=<code>` -- the record's own code.
        match = re.search(r"[?&]editEntry=([^&#]+)", self.page.url)
        if match:
            self._entry_code = match.group(1)
        return self

    def _wait_for_network_settle(self) -> None:
        """Bounded `networkidle` wait with a `load`-state fallback — HEALED
        2026-09-07 (live incident, tc_135966, manage-dynamic-widget): a bare
        `self.page.wait_for_load_state("networkidle")` here previously used
        Playwright's own 30000ms default and hung for the FULL 30s on this
        page, because navigating straight into `?editEntry=<code>` lands
        on a page whose network never technically idles (the same site-wide
        chatbot-widget polling `_wait_for_settle()` already documents for
        the Save/Submit path) — confirmed cross-surface, not idiosyncratic
        to one object, since `_wait_for_settle()` already carried this
        exact finding for a different call site on this same class. Shared
        here so BOTH open_entry_by_edit_link() and open_entry_by_code()
        get the same bounded wait instead of each risking its own 30s
        stall."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            # `load` can also miss 8s on qcdev (observed 2026-10-12: 22 of
            # 129384's tests died here). The caller's own settle signal
            # (_wait_for_editing_banner / the list table) follows and is the
            # real readiness check, so a slow `load` is not fatal here.
            try:
                self.page.wait_for_load_state("load", timeout=8000)
            except Exception:
                pass

    # ---- List state queries ----------------------------------------------
    def row_status_text(self, title: str) -> str:
        """Status cell text, normalized onto the canonical vocabulary via
        `normalize_status()` — e.g. "Draft", "Pending Review", "Published".

        The RAW rendered text differs by object due to per-object CSS
        (`text-transform: uppercase`), which is why it is normalized here
        rather than in each caller. CORRECTED 2026-09-28: this used
        `.capitalize()`, which silently broke the only two-word status
        ("PENDING REVIEW" -> "Pending review"); see `normalize_status()`.
        Returns "" when no row matches, and STATUS_UNKNOWN when a row
        matches but its badge is not a status this class knows."""
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')
        if row.count() == 0:
            return ""
        return normalize_status(row.locator("td").nth(1).inner_text())

    def row_visible(self, title: str) -> bool:
        return self.is_visible(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')

    def has_entries(self) -> bool:
        """True if the entries table has at least one row — CONFIRMED LIVE
        2026-09-07 (org_structure, tc_133288): the bare ENTRIES_TABLE_ROW
        locator (`table tbody tr`) matches every row on any populated
        object, so `BasePage.is_visible(ENTRIES_TABLE_ROW)` throws a
        Playwright strict-mode violation internally; BasePage.is_visible()'s
        own except-and-return-False contract swallows that exception and
        silently reports an ACTUALLY-POPULATED table as invisible. `.count()
        > 0` sidesteps strict mode entirely (it does not require a single
        match) and is the correct, generic way for any caller to assert
        "the list loaded with data" rather than target one specific row."""
        return self.page.locator(self.ENTRIES_TABLE_ROW).count() > 0

    def row_entry_id(self, title: str) -> str:
        """Entry id embedded in the row's own `data-qc-oel-delete`
        attribute — the stable handle this page uses to scope Delete to
        exactly one row (see module docstring)."""
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')
        delete_link = row.locator("a[data-qc-oel-delete]")
        return delete_link.get_attribute("data-qc-oel-delete") or ""

    def row_preview_url(self, title: str) -> str:
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')
        href = row.get_by_role("link", name="Preview").get_attribute("href")
        return control_panel_url(href) if href else ""

    def row_preview_url_by_code(self, entry_code: str) -> str:
        """Same as row_preview_url(), scoped by the row's own Entry-column
        code instead of a title that may not be rendered there (see
        row_status_text_by_code()'s own docstring for why — e.g.
        manage-strategic-pillar-card, whose Entry column shows an
        externalReferenceCode/UUID, never the object's own title field)."""
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{entry_code}")')
        href = row.get_by_role("link", name="Preview").get_attribute("href")
        return control_panel_url(href) if href else ""

    # ---- Entry-code-based lookups — CONFIRMED LIVE 2026-09-03, CORRECTED
    # 2026-09-03 after a real incident (see standards.md's "Destructive
    # Operations Against qcdev — Never Delete by Position or Assumption") ---
    # Every `row_*`/`delete_entry_by_title`/`open_entry_by_edit_link` method
    # above matches a row by `has-text(title)` against the Entry column
    # (`td.qc-oel__cell-title`). That column shows the real Title text on
    # every object independently confirmed live this session (service-card:
    # "New Membership"/"Membership Renewal"/...; promotional-banner;
    # news-article — all 3 render their own real titles) — title-based
    # lookup is CORRECT and UNCHANGED for those objects, do not "fix" what
    # isn't broken there.
    #
    # manage-strategic-pillar-card is the CONFIRMED EXCEPTION: its Entry
    # column instead renders the entry's own externalReferenceCode (a
    # Liferay-autogenerated UUID when none is explicitly set, e.g.
    # "d41f2a28-5dde-5d09-ff81-561bef51e78f") — verified live by creating a
    # real entry, filling Pillar Title with a known string, saving, then
    # reading every `<td>` in its row (4 cells: Entry/Status/Last modified/
    # Actions) AND every link's href/aria-label/title/data-* attribute
    # (including the Delete link's `data-qc-oel-label`, which ALSO carries
    # the externalReferenceCode, never the title) — the Pillar Title text
    # does not appear ANYWHERE in that row's DOM. This is a real per-object
    # Object Definition config difference (this object's own row-rendering
    # "title field" is the externalReferenceCode, not `pillarTitle`), not a
    # locator bug a smarter selector can work around — there is no title
    # text anywhere in this surface's list rows to match against.
    #
    # INCIDENT (2026-09-03): an earlier version of this fix added
    # newest_entry_code(), which assumed "the just-created entry is always
    # the last table row" and was used directly to pick a DELETE target.
    # That positional assumption was wrong at least once in a live run and
    # deleted the real "Objectives" pillar card instead of a disposable
    # QCTEST entry — an irreversible content-loss incident (see
    # standards.md). newest_entry_code() is kept below for READ-ONLY
    # diagnostics only (e.g. logging "what did I just create" for a human to
    # cross-check) — it must NEVER be used, directly or indirectly, to
    # select a delete/unpublish/edit target. find_entry_code_by_field()
    # replaces it for every destructive or state-changing use: it verifies
    # identity by reading the entry's OWN real field value back from its
    # edit form before returning a code, never by row position.
    def newest_entry_code(self) -> str:
        """READ-ONLY DIAGNOSTIC USE ONLY — Entry-column text of whatever row
        currently renders last in the table. Do NOT use this to select a
        target for delete_entry_by_code()/open_entry_by_code()/any other
        mutating call — "last row" is a positional assumption, not a
        verified identity, and a live incident (see standards.md's
        "Destructive Operations Against qcdev") already proved it can pick
        the wrong row and cause an irreversible delete of real content.
        Use find_entry_code_by_field() instead for anything that will be
        acted on."""
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        count = rows.count()
        if count == 0:
            return ""
        return rows.nth(count - 1).locator("td").nth(0).inner_text().strip()

    def find_entry_code_by_field(self, field_label: str, expected_value: str) -> str:
        """VERIFIED (never positional) entry lookup for objects whose Entry
        column does not render the real field value (see class-level note
        above) — e.g. manage-strategic-pillar-card, where the Entry column
        shows an externalReferenceCode/UUID, never the Pillar Title.

        Opens EVERY row's own edit form directly (via that row's own
        Entry-column code as the `editEntry` query value — confirmed live
        this round-trips correctly) and reads `field_label`'s own CURRENT
        value back from the real form field, returning the Entry-column
        code of the first row whose value equals `expected_value` exactly.
        Returns "" if no row matches. This is the only safe way to resolve
        "the entry I just created" on this class of object: it verifies by
        actual content, never by assuming row order/position — per
        standards.md's rule that any identifier backing a delete/mutate
        call must be verified by real ID/title match first. More expensive
        (one navigation per existing row) than title-column matching —
        only use this for objects confirmed NOT to render the real field
        value in their own Entry column; for every other object, the
        existing title-based methods above are faster and already correct."""
        self.open_entries_list()
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        codes = [rows.nth(i).locator("td").nth(0).inner_text().strip() for i in range(rows.count())]
        for code in codes:
            self.open_entry_by_code(code)
            try:
                value = self.page.get_by_role("textbox", name=self.label_pattern(field_label)).input_value()
            except Exception:  # noqa: BLE001 — field may not exist/apply to this row's form state
                continue
            if value == expected_value:
                return code
        return ""

    def row_status_text_by_code(self, entry_code: str) -> str:
        """Same normalized Status-cell read as row_status_text(), scoped by
        the row's own Entry-column code instead of a title that may not be
        rendered there (see class-level note above). Safe to call with any
        code obtained from find_entry_code_by_field() — this method only
        READS, it never selects/acts on a row itself."""
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{entry_code}")')
        if row.count() == 0:
            return ""
        return normalize_status(row.locator("td").nth(1).inner_text())

    def row_actions_by_code(self, entry_code: str) -> set:
        """Workflow row actions (`ROW_ACTION_ATTRS` keys) the row for
        `entry_code` offers the signed-in account right now -- read off the
        stable `data-qc-oel-<action>` attributes, never the localised label.
        Empty when no row matches. Read-only."""
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{entry_code}")').first
        if row.count() == 0:
            return set()
        # The actions cell fills in after the row itself (live 2026-10-13,
        # 134770: a Published row read back with NO actions). History renders
        # on every row in every status, so it marks the cell as filled.
        try:
            row.locator("[data-qc-oel-history]").first.wait_for(state="attached", timeout=5000)
        except Exception:  # noqa: BLE001 -- read whatever rendered
            pass
        return {name for name, attr in self.ROW_ACTION_ATTRS.items()
                if row.locator(f"[{attr}]").count() > 0}

    def row_last_modified(self, title_or_code: str) -> str:
        """The entries list's LAST MODIFIED cell (second resolution, e.g.
        "10/13/2026, 10:40:46 PM") for the row matching `title_or_code`, ""
        when no row matches. Read-only; call on the open entries list."""
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title_or_code}")').first
        if row.count() == 0:
            return ""
        return row.locator("td").nth(2).inner_text().strip()

    def row_statuses(self) -> list[tuple[str, str]]:
        """`(entry text, normalized status)` for EVERY row of the open entries
        list (call after `open_entries_list()`, which shows all rows). The
        status goes through `normalize_status()`, so a Published row whose
        Active Status is unticked reads `STATUS_INACTIVE`, not Published.
        Read-only (added 2026-10-14 for the Chamber's Law card-count cases)."""
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        out = []
        for i in range(rows.count()):
            cells = rows.nth(i).locator("td")
            if cells.count() < 2:
                continue
            out.append((" ".join(cells.nth(0).inner_text().split()),
                        normalize_status(cells.nth(1).inner_text())))
        return out

    def form_field_labels(self) -> list[str]:
        """First line of every `<label>` on the open form page (field labels,
        incl. the AR twins `<label> — العربية *`). Read-only; used to prove a
        field does or does not exist before a case relies on it."""
        texts = self.page.locator("label").all_inner_texts()
        return [t.strip().splitlines()[0].strip() for t in texts if t and t.strip()]

    # Read live 2026-10-14 (manage-general-manager-message): every required
    # control on these forms carries a custom validity message FROM PAGE LOAD
    # ("Hero Banner is required.", "Page Content is required.", "<field>
    # (العربية): Arabic content is required.") even when it is filled, and the
    # Publish button's click handler re-evaluates them before the browser's
    # own constraint check. So a pre-click read says nothing; read this AFTER
    # the Publish click: what is still listed is what blocked the submit (the
    # browser shows it as a bubble -- no red bar, no request).
    _INVALID_CONTROLS_JS = (
        "(sel) => { const b = document.querySelector(sel);"
        " const f = b ? b.form : document.querySelector('form');"
        " if (!f) return [];"
        " return Array.from(f.elements).filter(e => e.willValidate && !e.validity.valid)"
        ".map(e => [e.name || e.id || '', e.validationMessage || 'invalid']); }"
    )
    PUBLISH_STATUS_SUBMIT = 'button[type="submit"][name="status"][value="0"]'

    def invalid_form_controls(self) -> list[tuple[str, str]]:
        """`(name or id, validationMessage)` of every control of the open
        record form that currently fails the browser's constraint check.
        Read-only (no checkValidity() events). Read it right after a Publish
        click -- see the note above for why a pre-click read is meaningless."""
        try:
            pairs = self.page.evaluate(self._INVALID_CONTROLS_JS, self.PUBLISH_STATUS_SUBMIT)
        except Exception:  # noqa: BLE001 -- navigated away: nothing blocked it
            return []
        return [(str(n), str(m)) for n, m in pairs]

    _VISIBLE_FORM_MESSAGES_JS = (
        "() => Array.from(document.querySelectorAll("
        "'.form-feedback-item, .invalid-feedback, .alert, [role=alert]'))"
        ".filter(e => e.offsetParent && e.innerText.trim())"
        ".map(e => e.innerText.trim())"
    )

    def visible_form_messages(self) -> list[str]:
        """Non-empty, VISIBLE validation / alert texts on the page -- what the
        editor actually sees after a refused click (e.g. "Page Content is
        required." under the field, or the site's Arabic guard line).
        Read-only. Added 2026-10-14."""
        try:
            return [str(t) for t in self.page.evaluate(self._VISIBLE_FORM_MESSAGES_JS)]
        except Exception:  # noqa: BLE001 -- navigating
            return []

    def row_visible_by_code(self, entry_code: str) -> bool:
        return self.is_visible(f'{self.ENTRIES_TABLE_ROW}:has-text("{entry_code}")')

    def _wait_for_editing_banner(self) -> None:
        """Settle signal for an entry opened for edit. Multi-record objects
        render a "Cancel and add a new entry instead" link in the editing
        banner; singleton objects (e.g. Chamber Laws Page — "This page holds
        this one record only", observed live 2026-10-12) render the banner
        WITHOUT that link, so waiting on the link alone hangs. Either the
        link or the banner's own "Editing <code>" text marks the form as
        settled."""
        # WIDENED 2026-10-13: the English "Editing <code> (<status>)" text
        # alone timed out on an /ar render (134969), on an `(Inactive)`
        # record, and for a Site Content Author on a Published record, who
        # gets the Access Denied note instead of the banner (134685/134686,
        # 135446/135447, 136377/136378). All three render inside EDIT_BAR.
        banner = self.page.locator(self.CANCEL_AND_ADD_NEW_LINK).or_(
            self.page.get_by_text(re.compile(r"^Editing .+\((Draft|Published|Pending Review|Rejected|Unpublished|Archived|Scheduled|Inactive)\)", re.I))
        ).or_(self.page.locator(self.EDIT_BAR))
        banner.first.wait_for(state="visible", timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS)

    def open_entry_by_code(
        self, entry_code: str, locale: str | None = None
    ) -> "ObjectAuthoringPage":
        """Opens an existing entry for edit by navigating directly to its
        own `?editEntry=<code>` URL — confirmed live this IS the entry's own
        Entry-column code, so this never depends on a row's Edit link/title
        text being resolvable in the first place. Waits the same settle
        this class's open_entry_by_edit_link() already establishes for the
        editing banner's Cancel-and-add-new-entry link. Only ever call this
        with a code obtained from find_entry_code_by_field() (verified) or
        a code already known by the caller to be correct (e.g. one it just
        read straight off a fresh entries list for a different, read-only
        purpose) — never with newest_entry_code()'s positional guess when
        the result will be acted on."""
        self.open(self._manage_url(edit_entry=entry_code, locale=locale))
        self._entry_code = entry_code
        self._locale = locale
        self._wait_for_network_settle()
        self._wait_for_editing_banner()
        return self

    def delete_entry_by_code(self, entry_code: str) -> bool:
        """Best-effort delete scoped by the row's own Entry-column code —
        same `data-qc-oel-delete`-scoped click + never-raises contract as
        delete_entry_by_title() (see that method's own docstring), for
        objects where the Entry column doesn't render the title (see
        class-level note above). CALLERS MUST obtain `entry_code` via
        find_entry_code_by_field() (or another verified, non-positional
        source) — never via newest_entry_code(). This method itself does
        not enforce that (it has no way to know how the caller obtained the
        code), which is exactly why the verification must happen upstream,
        at the point the code is resolved — see the incident documented on
        newest_entry_code()'s own docstring."""
        try:
            row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{entry_code}")')
            entry_id = row.locator("a[data-qc-oel-delete]").get_attribute("data-qc-oel-delete")
            if not entry_id:
                return False
            self.page.once("dialog", lambda d: d.accept())
            self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]').click(force=True)
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(1000)
            return True
        except Exception:  # noqa: BLE001 — best-effort teardown, never raises
            logger.warning("delete_entry_by_code(%r) failed — leftover QCTEST data may remain", entry_code)
            return False

    # ---- Form actions ------------------------------------------------------
    def fill_text(self, field_label: str, value: str) -> "ObjectAuthoringPage":
        self.page.get_by_role("textbox", name=self.label_pattern(field_label)).fill(value)
        return self

    def field_value(self, field_label: str) -> str:
        """Read-back counterpart to fill_text() — CONFIRMED LIVE 2026-09-07
        against manage-general-manager-message: unlike the raw Object
        Definitions editor (Content & Data), THIS surface renders each
        bilingual field as TWO separate, independently-named textboxes
        (e.g. "GM Name" and "GM Name — العربية"), each individually
        addressable via `get_by_role("textbox", name=..., exact=True)` with
        no locale-toggle click needed — pass the AR-suffixed label
        (`"<Field Label> — العربية"`) directly to read/fill the Arabic
        value."""
        return self.page.get_by_role("textbox", name=self.label_pattern(field_label)).input_value()

    def current_status(self) -> str:
        """The record's status parsed out of `editing_banner_text()`, returned
        on the same canonical vocabulary as `row_status_text()` so callers can
        compare against either interchangeably. Only valid on an entry opened
        via `open_entry_by_code()`/`open_entry_by_edit_link()` (i.e. the
        editing banner is present).

        CORRECTED 2026-09-28. The previous implementation matched the two
        literals `"(approved)"` and `"(draft)"` CASE-SENSITIVELY and returned
        "Unknown" for everything else. Both halves were wrong on the current
        build: the banner capitalises the state (confirmed live:
        `Editing <title> (Draft). Save as Draft or Submit for Review updates
        this record.`), so even a plain draft fell through to "Unknown"; and
        five of the seven real states had no branch at all. A caller polling
        for a status it could never read is the failure mode this project has
        already been bitten by — see test_home_business_events_control_panel.py's
        own post-Unpublish poll."""
        text = self.editing_banner_text()
        for status in WORKFLOW_STATUSES:
            if f"({status})".casefold() in text.casefold():
                return status
        if "(approved)" in text.casefold():  # legacy wording, pre-workflow build
            return STATUS_PUBLISHED
        if f"({STATUS_INACTIVE})".casefold() in text.casefold():
            return STATUS_INACTIVE
        # A role that may not edit the record gets the Access Denied note
        # instead of the banner; it still names the status ('"<code>" is
        # Published.'), live 2026-10-13.
        denied = re.search(
            "[\u201d\"] is (" + "|".join(WORKFLOW_STATUSES + (STATUS_INACTIVE,)) + ")\\.",
            text, re.I)
        if denied:
            return normalize_status(denied.group(1))
        return STATUS_UNKNOWN

    def access_denied_note(self) -> str:
        """The Access Denied note shown instead of the editing banner when the
        signed-in role may not change this record (see ACCESS_DENIED_TEXT);
        "" when the record opened editable."""
        bars = self.page.locator(self.EDIT_BAR)
        for i in range(bars.count()):
            text = bars.nth(i).inner_text()
            if self.ACCESS_DENIED_TEXT in text:
                return " ".join(text.split())
        return ""

    def submit_controls_enabled(self) -> dict:
        """{label: enabled} for the form's Liferay `status` submit buttons
        (value 0 = Publish / Submit for Review / Save Changes, 2 = Save as
        Draft), read by attribute so the label's wording never matters."""
        buttons = self.page.locator('button[type="submit"][name="status"]')
        return {buttons.nth(i).inner_text().strip(): buttons.nth(i).is_enabled()
                for i in range(buttons.count())}

    def fill_number(self, field_label: str, value: str) -> "ObjectAuthoringPage":
        self.page.get_by_role("spinbutton", name=self.label_pattern(field_label)).fill(value)
        return self

    def type_date(self, field_label: str, value: str) -> "ObjectAuthoringPage":
        """Clicks the date field then types directly (mirrors the
        confirmed-live-safe pattern already used by every raw-admin date
        field on this project, e.g. HomeLatestNewsAdminPage.set_publication_date())."""
        self.page.get_by_role("textbox", name=self.label_pattern(field_label)).click()
        self.page.keyboard.type(value, delay=20)
        return self

    def set_checkbox(self, field_label: str, checked: bool) -> "ObjectAuthoringPage":  # noqa: D401
        checkbox = self.page.get_by_role("checkbox", name=self.label_pattern(field_label))
        if checked:
            checkbox.check()
        else:
            checkbox.uncheck()
        return self

    def select_combobox_option(self, field_label: str, option_label: str) -> "ObjectAuthoringPage":
        """Confirmed live 2026-09-03 on manage-service-card's "Assigned
        Tab" field: this is a text-input combobox with autocomplete, opened
        via its own "Open Options Menu" button (NOT a single toggle button
        carrying the field's own accessible name, unlike the raw admin
        surface's ASSIGNED_TAB_TOGGLE pattern) — `field_label` is accepted
        for API symmetry with the other fill_*/set_* methods but is not
        itself part of the locator chain; "Open Options Menu" is a
        confirmed-live-generic control label on this surface."""
        self.page.get_by_role("button", name="Open Options Menu").click()
        option = self.page.get_by_role("option", name=option_label, exact=True)
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return self

    def upload_file(self, field_label: str, file_path: str) -> "ObjectAuthoringPage":
        """Uploads `file_path` into the field's Documents & Media picker and
        returns only once the field SHOWS a file; otherwise raises.

        Locates the field's hidden filename textbox by its confirmed-live
        accessible name ("<Field Label> Select File"), then that textbox's
        sibling `Select File` button.

        REWRITTEN 2026-10-13 (PBI 129388 run, 8x `set_input_files` 30 s
        timeouts on the picker's file input):
          1. A picker left open by an earlier step is closed through its own
             dialog close button first (waited `detached`) -- a second picker
             on top of a stale one never got its file input.
          2. The picker iframe is waited `attached` after Select File, with one
             re-click (the click can land before the form's upload script is
             wired -- same pattern as header_admin_component._open_logo_picker).
          3. After `set_input_files` the wait is for the Add button to become
             ENABLED (it is in the DOM at once but disabled until the server
             finishes the upload) -- not for a "1 of 1" text.
          4. After Add, the picker must detach and the field's own readout
             must show a file; else UploadNotApplied. It never returns
             silently on a picker that did nothing.
        CORRECTED 2026-10-13 (live, manage-media-item): Add is not disabled
        while uploading -- it is absent until the upload completes -- and the
        first click on it is intermittently swallowed, so Add is re-clicked
        (bounded, UPLOAD_ADD_CLICKS) while the picker is still open.
        A picker that shows an error (a refused type/size) raises
        UploadNotApplied carrying that error text, so
        upload_file_expect_rejected() still reads a raise as "rejected"."""
        import os

        self._close_stale_upload_picker()
        before = self._upload_readouts(field_label)
        hidden_textbox = self.page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        )
        select_file_button = hidden_textbox.locator("xpath=..").get_by_role(
            "button", name="Select File"
        )
        iframe = self.page.locator(self.UPLOAD_MODAL_IFRAME).first
        for attempt in (0, 1):
            select_file_button.click()
            try:
                iframe.wait_for(state="attached", timeout=self.UPLOAD_PICKER_OPEN_MS)
                break
            except Exception:  # noqa: BLE001 -- one re-click; the second failure surfaces
                if attempt:
                    raise UploadPickerUnavailable(
                        f"{field_label!r}: the file picker did not open after two Select File clicks"
                    ) from None
                self.page.keyboard.press("Escape")
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME).first
        frame.locator('input[type="file"]').set_input_files(file_path)

        add_enabled = frame.locator(self.UPLOAD_MODAL_ADD_ENABLED).first
        refusal = frame.locator(".alert-danger:visible, .has-error .form-feedback-item:visible")

        def _add_ready_or_refused() -> bool:
            return add_enabled.count() > 0 or refusal.count() > 0

        try:
            wait_until(_add_ready_or_refused, timeout=self.UPLOAD_ADD_ENABLED_MS / 1000, poll=0.5)
        except WaitTimeoutError:
            pass
        if add_enabled.count() == 0:
            detail = self._picker_error_text(frame)
            self._close_stale_upload_picker()
            raise UploadNotApplied(
                f"{field_label!r}: the picker never enabled Add for {os.path.basename(file_path)!r}"
                + (f" -- picker says: {detail}" if detail else "")
            )
        # Bounded re-click (live 2026-10-13, manage-media-item "Thumbnail
        # Image"): the FIRST Add click is intermittently swallowed -- Add is
        # rendered and enabled, the click lands, the picker stays open; a
        # second click on the same button closes it in ~0.3 s and applies the
        # file. Escape-and-retry would throw the upload away, so Add is
        # re-clicked while it is still there, at most UPLOAD_ADD_CLICKS times.
        add_button = frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT, exact=True)
        clicks = 0
        closed = False
        for _ in range(self.UPLOAD_ADD_CLICKS):
            try:
                (add_button if add_button.count() else add_enabled).first.click(timeout=5000)
                clicks += 1
            except Exception:  # noqa: BLE001 -- the picker may be detaching under the click
                pass
            if self._picker_closed(self.UPLOAD_ADD_SETTLE_MS):
                closed = True
                break
        if not closed:
            detail = self._picker_error_text(frame)
            self._close_stale_upload_picker()
            raise UploadNotApplied(
                f"{field_label!r}: the picker stayed open after {clicks} Add click(s)"
                + (f" -- picker says: {detail}" if detail else "")
            )

        try:
            wait_until(
                lambda: self._upload_applied(field_label, before),
                timeout=self.UPLOAD_READOUT_MS / 1000,
                poll=0.3,
            )
        except WaitTimeoutError:
            raise UploadNotApplied(
                f"{field_label!r}: the picker closed but the field shows no new file "
                f"(before={before}, after={self._upload_readouts(field_label)})"
            ) from None
        return self

    def _close_stale_upload_picker(self) -> None:
        """Closes an open Documents & Media picker through the dialog's own
        close button (Escape when none renders) and waits for it to detach.
        No-op when no picker is open. Never raises."""
        iframe = self.page.locator(self.UPLOAD_MODAL_IFRAME)
        try:
            if iframe.count() == 0:
                return
            close = self.page.locator(self.UPLOAD_MODAL_CLOSE)
            if close.count():
                close.first.click(timeout=5000)
            else:
                self.page.keyboard.press("Escape")
            iframe.first.wait_for(state="detached", timeout=10000)
        except Exception:  # noqa: BLE001
            logger.warning("a stale file picker did not close cleanly")

    def _picker_error_text(self, frame) -> str:
        try:
            return " ".join(
                t.strip() for t in frame.locator(self.UPLOAD_MODAL_ERROR).all_inner_texts() if t.strip()
            )[:400]
        except Exception:  # noqa: BLE001
            return ""

    def _upload_readouts(self, field_label: str) -> dict:
        """Every place this surface can show a field's file: the base
        `<strong role="textbox">` readout (a newly selected file), the class's
        own uploaded_filename() (subclasses override it, e.g. the footer reads
        the current-file block) and the saved `Current file:` block."""
        out = {}

        def _selected() -> str:
            # Zero-wait: a bare inner_text() on a missing element would burn
            # the 30 s default on every poll.
            box = self.page.get_by_role("textbox", name=self.label_pattern(field_label))
            return box.first.inner_text(timeout=2000) if box.count() else ""

        readers = [("selected", _selected), ("current", lambda: self.current_file_name(field_label))]
        if type(self).uploaded_filename is not ObjectAuthoringPage.uploaded_filename:
            readers.append(("override", lambda: self.uploaded_filename(field_label)))
        for key, read in readers:
            try:
                out[key] = (read() or "").strip()
            except Exception:  # noqa: BLE001 -- a variant without that element
                out[key] = ""
        return out

    def _upload_applied(self, field_label: str, before: dict) -> bool:
        """True when a readout shows a file it did not show before the upload.
        A pre-existing saved file on an edit form does not count."""
        after = self._upload_readouts(field_label)
        return any(v and v != before.get(k, "") for k, v in after.items())

    def upload_file_expect_rejected(self, field_label: str, file_path: str) -> bool:
        """Attempts upload_file() for a file expected to be rejected by
        server-side validation (oversized / unsupported format) and reports
        whether rejection was actually observed.

        NOT independently confirmed live this session — three live probe
        attempts against this project's qcdev instance (see
        home_about_summary_admin_page.py's module docstring for the
        disclosed evidence: `networkidle` timeouts, a `Target crashed` /
        `Page crashed` Playwright error, and 25+ orphan `chrome.exe`
        processes already present on the host before this session's own
        browser was launched) made it impossible to observe which signal
        this surface actually uses for a rejected upload. The two signals
        checked below are inferred from this class's own generic
        upload_file() implementation, not observed:
          1. upload_file() itself raising (the picker's own "Add" flow never
             completes / the upload iframe never detaches for a file the
             server refuses).
          2. the field's own uploaded_filename() readout NOT containing the
             attempted file's basename afterward (still blank or still the
             pre-attempt value).
        Returns False (rejection NOT observed -- the file was silently
        accepted) if neither signal fires; callers must treat False as a
        real, honestly-reported finding (the case's expected rejection did
        not happen), never as a framework gap to route around."""
        import os

        attempted_name = os.path.basename(file_path)
        # Only a picker that took the file and did not apply it counts as a
        # rejection (2026-10-13). A picker that never opened, or any other
        # error, propagates -- reading it as "rejected" was a false green.
        try:
            self.upload_file(field_label, file_path)
        except UploadNotApplied:
            return True
        try:
            current = self.uploaded_filename(field_label)
        except Exception:
            return True
        return attempted_name not in current

    def field_length_rejected(self, field_label: str, attempted: str, limit: int) -> bool:
        """Fills `attempted` (expected to exceed `limit` characters) into a
        plain textbox field and reports whether the over-limit input was
        rejected, per this project's QA cases' own accepted disjunction
        ("Field truncates OR shows a max-length error"). NOT independently
        confirmed live which mechanism this surface uses this session (see
        upload_file_expect_rejected()'s docstring for the same disclosed
        probe-failure evidence) -- checks BOTH branches so either a
        client-side `maxlength` truncation or a submit-time validation block
        satisfies the case:
          1. truncation: the field's OWN value, read back immediately after
             fill (no submit needed), is <= limit characters -- a native
             `maxlength` attribute truncates synchronously on fill.
          2. submit-time block: submit_for_publishing() is attempted and
             current_status() does not become "Approved" afterward.
        Returns True if either signal fired. Callers must NOT loosen this
        further or treat a False return as anything but a real, honestly-
        reported "the over-limit value was accepted" finding.

        KNOWN WEAKNESS (2026-09-30). Until today branch 2 compared with
        "Approved", which the normalized status never equals, so this always
        returned True once truncation failed. It now compares with
        STATUS_PUBLISHED. Branch 2 is still only trustworthy on an entry that
        was OPEN for edit (the editing banner is what current_status() reads).
        On a create-new form a successful submit can land back on an empty
        form with no banner — current_status() is then "Unknown", which also
        reads as "rejected". Callers on create forms should confirm through
        the entries list (row status by title/code) until this has a
        positive "accepted" signal."""
        self.fill_text(field_label, attempted)
        if len(self.field_value(field_label)) <= limit:
            return True
        self.submit_for_publishing()
        return self.current_status() != STATUS_PUBLISHED

    def select_existing_file_from_library(
        self, field_label: str, folder_name: str, file_name: str
    ) -> "ObjectAuthoringPage":
        """Selects an EXISTING file already present in Liferay's Documents &
        Media library, via the SAME item-selector picker `upload_file()`
        opens (`iframe[src*="selectFileEntry"]`) — CONFIRMED LIVE 2026-09-08
        (Hero Banner Slide's "Banner Image" field, PBI 129367) this is the
        REAL, working mechanism for a field whose library is already
        populated (e.g. via this project's Flickr import — see
        cms-profile.md's "Flickr Pro API" note), as opposed to
        `upload_file()`'s drag-drop-a-NEW-file flow, which a prior session
        mistakenly used for this exact field and reported a false
        product-defect finding (see module docstring's CORRECTED note and
        HeroBannerSlideAdminPage's own module docstring for the full
        evidence trail).

        Opens the field's own picker (identical locator chain to
        `upload_file()`), clicks into `folder_name` (top-level folder link
        text, e.g. "Flickr"), then clicks directly on the existing file's
        own name/label (`.card-title`, matched by visible filename text
        within that folder's file listing) to select it.

        HEALED 2026-09-08 (live-diagnosed, tc_135010, two separate live
        incidents against the SAME picker widget):
          1. Clicking the whole `.card-row` container (an earlier version
             of this method) landed on EMPTY whitespace at the row's own
             horizontal center in this framework's real 1920x1080 viewport
             (a "List"-style row lays its filename far left and a Preview
             button far right, with a wide gap between) — the modal never
             closed, nothing was selected. Fixed by clicking the row's own
             `.card-title` element (the filename's real, narrow,
             content-bearing element) instead of the row container.
          2. This picker widget ALSO renders a second, visually different
             "Cards" (thumbnail-grid) layout — confirmed live via a
             screenshot that a video-recording Playwright context (this
             framework's own real per-test default) rendered this file
             picker as a thumbnail grid, not the row/list layout fix #1
             was diagnosed against. In THAT layout, a SINGLE click only
             highlights/selects the card (confirmed live: the hidden
             "Select File" textbox stayed empty and the modal stayed open
             indefinitely after one click) — a SECOND click (or an
             explicit `dblclick()`) is required to confirm and close the
             modal (confirmed live: `dblclick()` on the same `.card-title`
             populated the hidden textbox with the file's real ID and
             closed the modal). Which of the two layouts renders is NOT
             reliably controllable from here (it is this Liferay widget's
             own responsive/session-dependent choice, not something this
             suite's own viewport setting alone determines — both diagnoses
             above used the SAME 1920x1080 default). This method therefore
             clicks once, checks whether the modal is still present, and
             — only if so — clicks the SAME target a second time, which is
             safe for BOTH layouts: layout #1 (row/list) already closed the
             modal on the first click, so the check short-circuits and no
             second click is ever attempted (avoiding an unintended click
             on whatever now sits under the closed modal); layout #2
             (cards) needs, and gets, the second click.

        The filename readout (`uploaded_filename()`) populates shortly
        after the modal closes, asynchronously — this method waits for
        that readout element's own text to become non-empty as the real,
        condition-based signal, with a short bounded fallback wait if the
        wording/timing ever drifts — mirrors `upload_file()`'s own "wait
        for a real signal instead of a blind sleep" convention above."""
        hidden_textbox = self.page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        )
        select_file_button = hidden_textbox.locator("xpath=..").get_by_role(
            "button", name="Select File"
        )
        select_file_button.click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.get_by_role("link", name=folder_name, exact=True).click()
        file_card = frame.locator(".card-row", has_text=file_name).first
        file_card.wait_for(state="visible", timeout=10000)
        file_title = file_card.locator(".card-title").first
        file_title.click()
        modal = self.page.locator(self.UPLOAD_MODAL_IFRAME)
        try:
            modal.wait_for(state="detached", timeout=3000)
        except Exception:
            # Still present after the first click — this is the "Cards"
            # (thumbnail-grid) layout, which only highlights on one click
            # (see docstring's incident #2). One more click on the same,
            # now-highlighted target confirms/selects it.
            try:
                file_title.click()
            except Exception:  # noqa: BLE001 — modal may have closed between the check and this click
                pass
            try:
                modal.wait_for(state="detached", timeout=8000)
            except Exception:
                self.page.wait_for_timeout(1000)
        # Re-queries the readout element FRESH on every poll (never a
        # cached element handle) — HEALED 2026-09-08 (live-observed,
        # tc_135010, second attempt): an earlier version of this wait
        # grabbed a single `element_handle()` up front and polled THAT
        # specific node; if this surface's readout element gets replaced
        # (re-rendered) by the framework's own reactive update after
        # selection rather than mutated in place, that handle goes stale
        # and never reflects the real, current text — timing out silently
        # regardless of how long the wait budget is. `wait_until()` (see
        # core/utils/waits.py) re-runs the predicate itself each poll, so
        # every check re-queries live DOM state.
        try:
            wait_until(
                lambda: bool(self.uploaded_filename(field_label)),
                timeout=8.0,
                poll=0.3,
                message=f"{field_label!r} filename readout stayed empty after selecting {file_name!r}",
            )
        except WaitTimeoutError:
            pass
        return self

    def uploaded_filename(self, field_label: str) -> str:
        """Reads the ACTUAL uploaded filename off the field's own
        filename-readout element — confirmed-live a `<strong role="textbox"
        aria-label="<Field Label>">` sibling of the button+hidden-textbox
        wrapper (`data-placeholder="No file selected."`, empty text content
        before upload, the real filename as its text content after). A
        PRIOR version of this method read `.inner_text()` on the
        grandparent wrapper, which always included the "Select File"
        button's own label text regardless of upload state — a vacuous,
        always-non-empty check that could not have caught a failed upload;
        live-verified 2026-09-03 (before/after probe: `""` -> "promo_banner
        (43).png") that scoping to this exact-named textbox instead fixes
        that. `.input_value()` does NOT apply here (confirmed live: this
        element is a `<strong>`, not a real `<input>`/`<textarea>` —
        Playwright raises "Node is not an <input>..." on that call), hence
        `.inner_text()` on the narrowly-scoped element."""
        return self.page.get_by_role(
            "textbox", name=self.label_pattern(field_label)
        ).inner_text().strip()

    # ---- Lifecycle actions --------------------------------------------------
    def save_as_draft(self) -> "ObjectAuthoringPage":
        start_url = self.page.url
        before = self._pre_save_snapshot()
        self.click(self.SAVE_AS_DRAFT_BUTTON)
        self._wait_for_settle(start_url, before=before)
        return self

    def submit_for_review(self) -> "ObjectAuthoringPage":
        """Click the form's "Submit for Review" button.

        WHAT THIS LANDS ON DEPENDS ON THE SIGNED-IN ACCOUNT — confirmed live
        2026-09-28 on ONE record, submitted twice:
          - as QC Site Content Author (156492) -> "Pending Review", not public;
          - as QC Site Content Editor (156488) -> straight to "Published".
        The editorial workflow routes a *privileged* submitter past the review
        step (Kaleo `qc-editorial-approval.xml`'s condition node). This method
        therefore deliberately does NOT assert a resulting status: the caller
        knows which account it authenticated as and must assert accordingly.
        Callers that want the record live regardless of role should submit and
        then `approve_entry()` as an Editor."""
        start_url = self.page.url
        before = self._pre_save_snapshot()
        self.click(self.SUBMIT_FOR_REVIEW_BUTTON)
        self._wait_for_settle(start_url, before=before)
        return self

    def submit_via(self, button_selector: str) -> "ObjectAuthoringPage":
        """Click a specific form submit control and wait for the same save
        outcome `submit_for_review()` waits for. For callers that must pick
        the control locale-independently (e.g. `button[name="status"]
        [value="0"]`, which is "Publish" in EN and "نشر" in AR — added
        2026-10-12 for PBI 129394's Arabic-UI validation cases). A submit the
        browser blocks natively (an empty `required` control) never starts,
        and this returns after the not-started cap."""
        start_url = self.page.url
        before = self._pre_save_snapshot()
        self.page.locator(button_selector).first.click()
        self._wait_for_settle(start_url, before=before)
        return self

    def submit_via_reading_validity(self, button_selector: str) -> list[tuple[str, str]]:
        """`submit_via()`, returning `invalid_form_controls()` read IMMEDIATELY
        after the click -- before the settle wait.

        Added 2026-10-14 (GM Message 79878, read live with every write
        aborted): with a required control emptied, the Publish click leaves
        that control's own message ("Page Content is required.") as the only
        invalid one, and the browser shows it as a bubble -- but the message
        is cleared again within ~8 s, so a read after the settle misses it.
        The same click ALSO fires the Arabic-twin sync (`PUT /o/c/<object>/
        <id>` built from the STORED record, not from the form), which bumps
        the row's LAST MODIFIED without changing any value -- so on these
        forms LAST MODIFIED is not a persistence signal; the stored value is."""
        start_url = self.page.url
        before = self._pre_save_snapshot()
        shown_before = set(self.visible_form_messages())
        self.page.locator(button_selector).first.click()
        blocked = self.invalid_form_controls()
        # The visible message too, before it can be cleared (same ~8 s):
        # polled for up to 3 s (seen 1.5 s after the click, live 2026-10-14);
        # a save that is not refused simply shows none.
        try:
            wait_until(lambda: bool(set(self.visible_form_messages()) - shown_before), timeout=3, poll=0.25)
        except WaitTimeoutError:
            pass
        self.last_click_messages = [m for m in self.visible_form_messages() if m not in shown_before]
        self._wait_for_settle(start_url, before=before)
        return blocked

    def submit_for_publishing(self) -> "ObjectAuthoringPage":
        """DEPRECATED alias for `submit_for_review()`, kept so the existing
        call sites across the cms/ suite keep resolving. The button has read
        "Submit for Review" since at least 2026-09-28 and the old label
        matches nothing; the name also implies an outcome ("publishing") that
        is only true for a privileged submitter. Prefer submit_for_review()."""
        return self.submit_for_review()

    # ---- Row-level workflow transitions -------------------------------------
    # CONFIRMED LIVE 2026-09-28 (manage-law-entry, one probe record walked
    # Draft -> Pending Review -> Rejected -> Pending Review -> Published ->
    # Unpublished -> Archived -> Unpublished -> Draft, as Author then Editor).
    #
    # Which actions a row offers depends on BOTH its status and the signed-in
    # role. Observed action sets, by status (as Editor):
    #   Draft          : history, delete
    #   Pending Review : approve, reject, schedule, history, delete
    #   Rejected       : resubmit, history, delete
    #   Published      : unpublish, history, delete
    #   Unpublished    : publish, return, archive, schedule, history, delete
    #   Archived       : restore, history, delete
    # An Author sees none of the transition actions on rows it does not own.
    #
    # Every one of these drives NATIVE browser dialogs, not DOM modals, and
    # several CHAIN two of them (a confirm() immediately followed by a
    # prompt()). Observed shapes:
    #   reject  : prompt (comment shown to the author)
    #   return  : prompt (comment REQUIRED)
    #   approve : confirm -> prompt (comment optional)
    #   resubmit: confirm -> prompt (comment optional)
    #   unpublish / archive / restore / delete : confirm only
    # _run_row_action() accepts an arbitrary run of them, so a caller never
    # has to know how many a given action raises.

    def _row_locator(self, title_or_code: str):
        return self.page.locator(
            f'{self.ENTRIES_TABLE_ROW}:has-text("{title_or_code}")'
        ).first

    def _run_row_action(
        self, title_or_code: str, action: str, comment: str = ""
    ) -> "ObjectAuthoringPage":
        """Click one `data-qc-oel-<action>` control on the row matching
        `title_or_code`, accepting every native dialog it raises (answering
        any prompt with `comment`), then wait for the list to settle.

        Scoped by the row's own stable data attribute rather than the visible
        label: the label is localised, the attribute is not."""
        attr = self.ROW_ACTION_ATTRS.get(action)
        if attr is None:
            raise ValueError(
                f"Unknown row action {action!r}. Known: "
                f"{', '.join(sorted(self.ROW_ACTION_ATTRS))}"
            )
        control = self._row_locator(title_or_code).locator(f"[{attr}]")
        if control.count() == 0:
            raise AssertionError(
                f"Row {title_or_code!r} offers no {action!r} action "
                f"([{attr}] is absent). Its current status and the signed-in "
                f"role decide which actions render — read row_status_text() "
                f"and check the role before calling this."
            )

        def _accept(dialog):
            try:
                dialog.accept(comment)
            except Exception:  # noqa: BLE001 — dialog already handled/closed
                pass

        self.page.on("dialog", _accept)
        try:
            # force=True mirrors delete_entry_by_code()'s own rationale: the
            # site-wide chatbot launcher can intercept pointer events over the
            # actions column, and the native confirm() is the real gate on the
            # action, not the click.
            control.first.click(force=True)
            if action == "history":
                # History does not remove its control: it expands an in-table
                # row, so waiting for the control to detach always burned the
                # full 30s cap (review fix 2026-10-04).
                try:
                    self.page.locator(self.HISTORY_LIST).first.wait_for(
                        state="visible", timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS
                    )
                except Exception:  # noqa: BLE001 — history_entries() reports []
                    pass
            else:
                self._wait_for_settle(gone=control.first)
        finally:
            self.page.remove_listener("dialog", _accept)
        return self

    def approve_entry(self, title_or_code: str, comment: str = "") -> "ObjectAuthoringPage":
        """Approve a Pending Review record -> Published. Editor-only."""
        return self._run_row_action(title_or_code, "approve", comment)

    def reject_entry(self, title_or_code: str, comment: str = "") -> "ObjectAuthoringPage":
        """Reject a Pending Review record -> Rejected. Editor-only. The
        comment is shown to the author and recorded in History."""
        return self._run_row_action(title_or_code, "reject", comment)

    def resubmit_entry(self, title_or_code: str, comment: str = "") -> "ObjectAuthoringPage":
        """Resubmit a Rejected record -> Pending Review."""
        return self._run_row_action(title_or_code, "resubmit", comment)

    def publish_entry(self, title_or_code: str, comment: str = "") -> "ObjectAuthoringPage":
        """Publish an Unpublished record -> Published. Editor-only."""
        return self._run_row_action(title_or_code, "publish", comment)

    def unpublish_entry(self, title_or_code: str, comment: str = "") -> "ObjectAuthoringPage":
        """Unpublish a Published record -> Unpublished. Editor-only.

        NOTE the destination: "Unpublished" is its own state, NOT "Draft" —
        the confirm() text says so verbatim ("...and shows as Unpublished").
        Code that polls for "Draft" after unpublishing is asserting the wrong
        thing."""
        return self._run_row_action(title_or_code, "unpublish", comment)

    def archive_entry(self, title_or_code: str, comment: str = "") -> "ObjectAuthoringPage":
        """Archive an Unpublished record -> Archived. Reachable from
        Unpublished only, so a Published record needs unpublish_entry() first."""
        return self._run_row_action(title_or_code, "archive", comment)

    def restore_entry(self, title_or_code: str, comment: str = "") -> "ObjectAuthoringPage":
        """Restore an Archived record -> Unpublished (NOT straight to
        Published — the confirm() text states this)."""
        return self._run_row_action(title_or_code, "restore", comment)

    def return_to_author(self, title_or_code: str, comment: str) -> "ObjectAuthoringPage":
        """Send an Unpublished record back to its author -> Draft. The comment
        is REQUIRED by the surface, so it is a required argument here."""
        if not comment:
            raise ValueError(
                "return_to_author() requires a comment — the surface's own "
                "prompt marks it required."
            )
        return self._run_row_action(title_or_code, "return", comment)

    # History is NOT a modal — CONFIRMED LIVE 2026-09-28. Clicking the row's
    # History action expands an extra row INSIDE the entries table
    # (`td.qc-oel__history`) holding `ul.qc-oel__history-list`, one `li` per
    # workflow move, each with three structured spans. Reading it as a dialog
    # finds nothing.
    HISTORY_LIST = "ul.qc-oel__history-list"
    HISTORY_WHO = ".qc-oel__history-who"
    HISTORY_WHEN = ".qc-oel__history-when"
    HISTORY_COMMENT = ".qc-oel__history-comment"

    def history_entries(self, title_or_code: str) -> list[dict[str, str]]:
        """Expand the row's History and return its audit trail, newest last,
        as `{"who": ..., "when": ..., "comment": ...}` dicts — who moved the
        record, when, and the comment they left.

        This is the strongest evidence available for a workflow assertion:
        it proves a transition was actually recorded, not merely that a badge
        changed. Returns [] (never raises) when the row has no history yet or
        the list does not render."""
        self._run_row_action(title_or_code, "history")
        history_list = self.page.locator(self.HISTORY_LIST).first
        try:
            history_list.wait_for(
                state="visible", timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS
            )
        except Exception:  # noqa: BLE001 — reported as empty, never raised
            logger.warning("History list did not render for %s", title_or_code)
            return []

        entries: list[dict[str, str]] = []
        items = history_list.locator("li")
        for i in range(items.count()):
            item = items.nth(i)

            def _part(selector: str) -> str:
                node = item.locator(selector)
                return node.inner_text().strip() if node.count() else ""

            entries.append(
                {
                    "who": _part(self.HISTORY_WHO),
                    "when": _part(self.HISTORY_WHEN),
                    "comment": _part(self.HISTORY_COMMENT),
                }
            )
        return entries

    SETTLE_OUTCOME_TIMEOUT_MS = 120000
    SAVE_SUCCESS_TOAST = (
        '.alert-success:visible, .toast:visible, [class*="toast"]:visible'
    )
    SAVE_SUCCESS_TEXT = re.compile(r"Saved and submitted for review\.|\bsaved\b|\bpublished\b", re.I)
    SAVE_REFUSAL = (
        '.alert-danger:visible, .form-feedback-item:visible, '
        ':text("Please complete the required fields"):visible'
    )

    def _count(self, selector: str) -> int:
        try:
            return self.page.locator(selector).count()
        except Exception:  # noqa: BLE001 — mid-navigation
            return -1

    def _toast_text(self) -> str:
        try:
            return " ".join(self.page.locator(self.SAVE_SUCCESS_TOAST).all_inner_texts())
        except Exception:  # noqa: BLE001
            return ""

    # Without SUBMIT_STARTED ever seen, the save most likely never fired:
    # wait only this long (the pre-2026-10-02 budget), not the full 120s.
    SETTLE_NOT_STARTED_CAP_MS = 15000

    def _pre_save_snapshot(self) -> dict:
        """Refusal / toast state sampled BEFORE the Save / Submit click (review
        fix 2026-10-04): sampled after it, a refusal rendered synchronously by
        the click was counted as the baseline and never seen as an outcome."""
        return {"refusals": max(self._count(self.SAVE_REFUSAL), 0), "toast": self._toast_text()}

    def _poll_save_outcome(self, start_url: str | None, before: dict | None = None) -> str | None:
        """Poll (in Python, so it survives navigations) for the first save
        outcome: 'nav' | 'toast' | 'refused' | 'spinner'; None on timeout.

        `before` is the pre-click snapshot (_pre_save_snapshot); callers that
        click themselves and pass none get the old post-click sample.
        `start_url` None (those same callers) means any `previewEntry=` URL
        counts as 'nav'."""
        import time
        if before is None:
            before = self._pre_save_snapshot()
        refusals_before = before["refusals"]
        toast_before = before["toast"]
        seen_busy = False
        started = False
        t0 = time.monotonic()
        deadline = t0 + self.SETTLE_OUTCOME_TIMEOUT_MS / 1000
        not_started_deadline = t0 + self.SETTLE_NOT_STARTED_CAP_MS / 1000
        while time.monotonic() < deadline:
            url = self.page.url
            if "previewEntry=" in url and (start_url is None or url != start_url):
                return "nav"
            toast = self._toast_text()
            if toast != toast_before and self.SAVE_SUCCESS_TEXT.search(toast):
                return "toast"
            if self._count(self.SAVE_REFUSAL) > refusals_before:
                return "refused"
            if not started and self._count(self.SUBMIT_STARTED) > 0:
                started = True
            busy = self._count(self.FORM_BUSY)
            if busy > 0:
                seen_busy = True
                started = True
            elif seen_busy and busy == 0:
                return "spinner"
            if not started and time.monotonic() > not_started_deadline:
                return None
            try:
                self.page.wait_for_timeout(300)
            except Exception:  # noqa: BLE001 — page navigating
                time.sleep(0.3)
        return None

    def _wait_for_settle(self, start_url: str | None = None, gone=None, before: dict | None = None) -> None:
        """POSITIVE-signal wait — HEALED 2026-09-14 (Group B triage of
        tc_135184/135185/133294's teardown, evidence: `reports/allure-
        results/`). The PRIOR strategy here (`networkidle` with a `load`
        fallback) was already disclosed by this method's own earlier
        docstring as a KNOWN-BROKEN signal on this page — confirmed live
        2026-09-03 that `networkidle` can fail to fire at all within a
        generous 30s budget (continuous background network activity, e.g.
        the site-wide chatbot widget's own polling, keeps the network
        technically non-idle) — not new information, and every failing
        run's own screenshots showed the underlying Save/Submit action had
        already committed correctly by the time the wait timed out (a
        broken WAIT signal, never a broken SAVE). Replaced with a bounded
        wait for ANY of the generic, confirmed-live DOM markers that signal
        this surface has settled into a real, recognized post-save state —
        whichever one the current object/view actually lands on:
          - the entries table's own row marker (`a[data-qc-oel-delete]`) —
            present when the save returns to/re-renders the entries list;
          - the editing banner's "Cancel and add a new entry instead" link
            (`CANCEL_AND_ADD_NEW_LINK`) — present when the save stays on an
            edit form (Draft OR Approved banner, see class docstring);
          - the create form's own Save as Draft button
            (`SAVE_AS_DRAFT_BUTTON`) — present when the save leaves a fresh
            create form mounted.
        Playwright's own comma-joined selector list resolves the instant
        ANY one of the three appears, which is always true once this page
        has genuinely settled — unlike `networkidle`, which it may never
        reach at all. Falls back to a short, explicitly-capped `load` wait
        (never unbounded) for the rare state that matches none of the
        three (e.g. a genuine validation-error state)."""
        # FIX 2026-10-02/03 (B triage, traces for tc_141047 / tc_140981): the
        # old selector included the create form's own Save as Draft button,
        # which stays attached for the WHOLE in-flight save, and the manage
        # page renders the entries list (with `a[data-qc-oel-delete]`) next to
        # the form. Both matched at once, so the caller navigated away while
        # qcdev was still saving (about 50s that day) and the record was never
        # stored. Neither marker, nor a bare `disabled`, is a settle signal.
        # Now we poll for an OUTCOME, up to SETTLE_OUTCOME_TIMEOUT_MS:
        #   (a) the page navigated to `?previewEntry=` (live 2026-10-02: a
        #       successful Publish lands there) or a success toast appeared;
        #   (b) a refusal bar or a field error appeared that wasn't there
        #       before the save;
        #   (c) fallback: the busy spinner was seen and has gone again.
        # A row action passes `gone` (its own control) and waits for that
        # control to detach instead.
        if gone is not None:
            try:
                gone.wait_for(state="detached", timeout=30000)
            except Exception:  # noqa: BLE001 — explicitly capped, falls through
                logger.warning("_wait_for_settle: row-action control did not detach in 30s")
            self.page.wait_for_timeout(2500)
            return
        outcome = self._poll_save_outcome(start_url, before)
        if outcome == "nav":
            try:
                self.page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:  # noqa: BLE001
                pass
        elif outcome is None:
            logger.warning("_wait_for_settle: no save outcome within %sms", self.SETTLE_OUTCOME_TIMEOUT_MS)
        # Widened from 1500ms to 2500ms 2026-09-03: this is the ONLY settle
        # the write (Save as Draft / Submit for Publishing) gets before a
        # caller may immediately poll the delivery surface (e.g.
        # reload_until_banner_matches) — matches this project's own
        # documented write-vs-read-cache propagation grace convention
        # (SAVE_COMMIT_GRACE_MS = 2000ms elsewhere) rather than a shorter,
        # unmeasured value that raced that propagation gap live this
        # session (Approved status was already correct in the entries
        # list at the time, but the separate delivery-surface read lagged
        # behind it). Kept unchanged by this HEALED pass — only the wait
        # SIGNAL above changed, not this grace period.
        self.page.wait_for_timeout(2500)

    def is_save_as_draft_disabled(self) -> bool:
        return self.page.locator(self.SAVE_AS_DRAFT_BUTTON).is_disabled()

    def editing_banner_text(self) -> str:
        """Raw text of the Editing/status banner shown above the form when
        opened via `editEntry` — callers substring-match this against the
        exact confirmed-live wording in the module docstring."""
        return self.page.locator("body").inner_text()

    def unpublish_to_edit_as_draft(self) -> "ObjectAuthoringPage":
        """Waits for the Unpublish button to actually render (see module
        docstring's settle note) before clicking, and accepts the native
        `confirm()` dialog it fires."""
        self.wait_for(self.UNPUBLISH_BUTTON, timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS)
        self.page.once("dialog", lambda d: d.accept())
        self.page.locator(self.UNPUBLISH_BUTTON).click()
        # BOUNDED 2026-10-13 (134770: a bare networkidle waited its full 30 s
        # default -- the chatbot polling keeps the network busy). The caller
        # proves the transition on a fresh read (wait_for_status /
        # list_status); this only lets the request leave.
        self._wait_for_network_settle()
        self.page.wait_for_timeout(1500)
        return self

    def delete_entry_by_title(self, title: str) -> bool:
        """Best-effort delete via the row's own `Delete` link, scoped by
        its `data-qc-oel-delete` entry id (never a bare same-titled match)
        — accepts the native `confirm()` dialog it fires, and clicks with
        `force=True` since the site-wide chatbot launcher can intercept
        pointer events over this link (see module docstring). Returns
        False (no-op) if no matching row exists. Mirrors the project's
        existing `_best_effort_delete` convention (see standards.md's
        Wait-Strategy Audit / HomeBusinessEventsAdminPage): NEVER raises —
        a teardown hiccup here must not flip an already-passed test body
        to FAILED, which is exactly what happened live 2026-09-03 before
        this method swallowed exceptions (a stale-DOM/timing miss during
        cleanup surfaced as the whole test's failure with a passing body).
        Any exception here is a real, separate leftover-fixture-data
        finding the caller/report should note, not a test failure."""
        try:
            entry_id = self.row_entry_id(title)
            if not entry_id:
                return False
            self.page.once("dialog", lambda d: d.accept())
            delete_link = self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]')
            delete_link.click(force=True)
            # HEALED 2026-09-14 (Group B triage of tc_135184/135185/133294's
            # teardown): replaces the previous, UNBOUNDED
            # `wait_for_load_state("networkidle")` call (no timeout arg at
            # all — Playwright's own 30000ms default) with a POSITIVE,
            # scoped signal: this exact row's own delete-link element
            # detaching from the DOM is the real, verifiable confirmation
            # the delete committed, not a generic (and, on this page,
            # confirmed-broken — see `_wait_for_settle()`'s own docstring)
            # network-quiescence guess. Explicitly capped at 10000ms so a
            # hung teardown wait can never silently consume the whole run.
            try:
                delete_link.wait_for(state="detached", timeout=10000)
            except Exception:  # noqa: BLE001 — real, explicitly-capped fallback, never unbounded
                try:
                    self.page.wait_for_load_state("load", timeout=5000)
                except Exception:  # noqa: BLE001
                    pass
            self.page.wait_for_timeout(1000)
            return True
        except Exception:  # noqa: BLE001 — best-effort teardown, never raises
            logger.warning("delete_entry_by_title(%r) failed — leftover QCTEST data may remain", title)
            return False

    def preview_banner_text(self, preview_url: str) -> str:
        """Navigates directly to the record's own preview URL (row-level
        `Preview` link target) and returns the status-banner text this
        page's PREVIEW mode injects (see module docstring)."""
        self.open(preview_url)
        return self.page.locator('[role="status"]').first.inner_text()

    # ---- RESTORED 2026-09-28 ------------------------------------------------
    # The 2026-09-28 merge resolved this file with "upstream wins". Upstream
    # simply never had the members below, so resolving that way silently
    # deleted API that six modules call (chambers_law x2, about_qatar_chamber,
    # home_latest_news, home_services, chairman_message). Restored verbatim
    # from 3f73561, the last commit that had them. Nothing here overrides an
    # upstream implementation — every one of these is a member upstream lacks.

    def delete_all_entries_by_title(self, title: str, max_rows: int = 10) -> int:
        """Delete EVERY entry whose row matches `title` exactly, one at a
        time, re-reading the list between deletes. Returns how many were
        removed.

        Why this exists (2026-09-10): `delete_entry_by_title()` cannot
        clear duplicates — its `row_entry_id()` builds a plural row
        locator, so with two same-titled rows it raises a strict-mode
        violation, gets swallowed by that method's never-raise contract,
        and silently deletes nothing. Leaving newly-created entries in
        place (the standing test-data instruction) means a re-run of a
        create-case produces exactly that duplicate, which then breaks
        `open_entry_by_edit_link()` for every subsequent run.

        SAFETY — this is the one method here that deletes more than one
        row, so it is deliberately narrow: it refuses any title outside
        the project's disposable `QCTEST-` namespace, and it matches on
        the caller's exact title string, never on position ("newest"/
        "last row"). Real editorial rows can therefore never be reached by
        it, which is what standards.md requires of any multi-row delete on
        a shared environment.
        """
        if not title.startswith("QCTEST-"):
            raise ValueError(
                f"refusing to bulk-delete {title!r}: this method is limited to "
                "the disposable QCTEST- namespace"
            )
        removed = 0
        for _ in range(max_rows):
            self.open_entries_list()
            rows = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')
            if rows.count() == 0:
                return removed
            delete_link = rows.first.locator("a[data-qc-oel-delete]").first
            entry_id = delete_link.get_attribute("data-qc-oel-delete")
            if not entry_id:
                return removed
            self.page.once("dialog", lambda d: d.accept())
            self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]').click(force=True)
            self._wait_for_network_settle()
            removed += 1
        logger.warning(
            "delete_all_entries_by_title(%r) hit the %d-row cap — more leftovers may remain",
            title, max_rows,
        )
        return removed

    def download_current_file(self, field_label: str, dest_path: str) -> str:
        """Downloads the field's CURRENT file to `dest_path` via an
        authenticated request on this same page's context (reuses its
        session cookies — no separate login) — the TEST_OWNED baseline
        capture step for a binary restore. Returns "" (no-op) if the field
        is currently empty."""
        url = self.current_file_download_url(field_label)
        if not url:
            return ""
        response = self.page.context.request.get(url)
        with open(dest_path, "wb") as handle:
            handle.write(response.body())
        return dest_path

    def select_existing_file(
        self, field_label: str, file_name: str, folder: str | None = None
    ) -> "ObjectAuthoringPage":
        """Picks an ALREADY-EXISTING Documents & Media file for an attachment
        field, instead of uploading from disk like `upload_file()` does.

        CONFIRMED LIVE 2026-09-09 (scoped CLI Playwright probe against qcdev,
        manage-law-entry's `Law Icon` field): the same "Select File" button
        opens the same picker iframe, which is a full Documents & Media
        browser — root shows `about-us-hero.png` plus the folders `Flickr`,
        `qatar-chamber-website`, `QC Footer Social Icons` and
        `request-to-media-dept`. Clicking a folder's link navigates into it;
        clicking a FILE's own name **immediately closes the picker and fills
        the field** — there is NO "Add" button step on this path (unlike
        `upload_file()`, whose Add button belongs to the upload flow). Like
        every attachment change on this surface the selection only takes
        effect on Save (guide: "Remove file / Undo remove take effect only on
        save").

        `folder` navigates one level down first; omit it for a root-level
        file. Verified selectable icons live in `QC Footer Social Icons`
        (`qc-social-facebook.svg` … `qc-social-youtube.svg`)."""
        hidden_textbox = self.page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        )
        hidden_textbox.locator("xpath=..").get_by_role(
            "button", name="Select File"
        ).click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        if folder:
            frame.get_by_role("link", name=folder).first.click()
            # The folder navigation is a real page load inside the iframe —
            # wait for the target file itself to render rather than sleeping.
            frame.get_by_text(file_name, exact=True).first.wait_for(
                state="visible", timeout=15000
            )
        frame.get_by_text(file_name, exact=True).first.click()
        # HARDENED 2026-09-09 — the file-name click's effect is INTERMITTENT
        # (both behaviours confirmed live within minutes of each other): it
        # usually closes the picker outright, but it can instead merely
        # SELECT the card and leave the modal open. When that happened,
        # tc_134884's next action (`Submit for Publishing`) failed with
        # `Locator.click: Timeout 30000ms` because the still-open modal
        # overlaid the button — a silent, misleading failure mode, so this
        # method now refuses to return while the picker is still up.
        if not self._picker_closed(4000):
            for label in ("Add", "Select", "Choose", "Done"):
                try:
                    btn = frame.get_by_role("button", name=label)
                    if btn.count():
                        btn.first.click(timeout=8000)
                        break
                except Exception:  # noqa: BLE001 — try the next candidate label
                    continue
        if not self._picker_closed(6000):
            # Last resort: some item-selector builds treat a single click as
            # select-only and require a double-click to commit.
            try:
                frame.get_by_text(file_name, exact=True).first.dblclick()
            except Exception:  # noqa: BLE001 — the assertion below is the real gate
                pass
        if not self._picker_closed(8000):
            raise AssertionError(
                f"the Documents & Media picker stayed open after selecting "
                f"{file_name!r} — refusing to continue, because a still-open "
                "modal silently overlays the form's Save/Publish buttons and "
                "turns the next click into an unexplained 30s timeout"
            )
        return self

    def _file_upload_container(self, field_label: str):
        hidden_textbox = self.page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        )
        return hidden_textbox.locator("xpath=../../..")

    def _picker_closed(self, timeout: int) -> bool:
        """True once no file-picker iframe is attached; False on timeout.
        Counted rather than `wait_for(detached)`, which raises a strict-mode
        violation (read here as "still open") when two pickers are attached."""
        iframes = self.page.locator(self.UPLOAD_MODAL_IFRAME)
        try:
            wait_until(lambda: iframes.count() == 0, timeout=timeout / 1000, poll=0.25)
            return True
        except WaitTimeoutError:
            return False

    def description_editor_iframe(self, field_name: str | None = None) -> str:
        """Locator for a bilingual rich-text field's EN/default-locale
        CKEditor iframe. See DESCRIPTION_EDITOR_IFRAME's own docstring note
        above for the full live investigation. `field_name` is the field's
        own Liferay object-field name (e.g. "messageContent", matching the
        DOM id substring `ObjectField_<fieldName>` confirmed live) — when
        given, returns a locale-safe, reflow-safe locator scoped to that
        field's own container; when omitted, returns the original
        `DESCRIPTION_EDITOR_IFRAME` (`>> nth=0`) unchanged."""
        if field_name:
            return f'div[id*="ObjectField_{field_name}"] {self.RICH_TEXT_EDITOR_IFRAME_CSS}'
        return self.DESCRIPTION_EDITOR_IFRAME

    @staticmethod
    def label_pattern(field_label: str) -> "re.Pattern":
        """Anchored accessible-name matcher tolerant of a required field's
        trailing ` *` (see the note above). Use this instead of
        `exact=True` for every role-based form-field lookup on this
        surface.

        "/" is escaped (2026-10-13, PBI 129388): Playwright serializes the
        pattern as `/source/flags` into its role selector, and re.escape()
        leaves "/" bare, so "Video File / Embed URL" ended the regex early
        ("Error while parsing selector ... unexpected symbol"). A
        backslash-escaped slash means the same thing to Python's re and to Playwright's JS regex."""
        return re.compile(r"^\s*" + selector_safe_escape(field_label) + r"\s*\*?\s*$")

    def current_file_download_url(self, field_label: str) -> str:
        """Absolute URL of the current file's own `Download` link (see class
        docstring above) — "" if no current file is set."""
        meta = self._file_upload_container(field_label).locator(
            ".qc-oel__current-file-meta"
        )
        if meta.count() == 0:
            return ""
        link = meta.get_by_role("link", name="Download")
        if link.count() == 0:
            return ""
        href = link.first.get_attribute("href") or ""
        return control_panel_url(href) if href else ""

    def remove_current_file(self, field_label: str) -> "ObjectAuthoringPage":
        """Clicks this field's own "Remove file" button — confirmed live a
        plain, no-dialog action (unlike row Delete/Unpublish's native
        `confirm()`).

        ⚠ REAL, LIVE-CONFIRMED FINDING (2026-09-07, manage-chamber-laws-page
        Content Image, reproduced twice): `remove_current_file()` followed
        DIRECTLY by `upload_file()` on the SAME still-open form, then
        Submit for Publishing, does **not** persist the new file — a fresh
        re-open after that sequence still shows the OLD file untouched
        (confirmed live via both the admin read-back AND the public
        delivery surface's own document id, which never changed). This is
        a genuine two-step widget quirk, not a locator bug: `remove_current_
        file()` needs its OWN separate save (`save_as_draft()` or
        `submit_for_publishing()`) to actually commit the empty state
        BEFORE a subsequent `upload_file()` on a freshly re-opened form
        will attach correctly. CONFIRMED LIVE this two-phase sequence DOES
        work (`remove_current_file()` -> `save_as_draft()` -> re-open ->
        `upload_file()` -> `submit_for_publishing()`), reproduced twice
        (fresh upload AND restoring the original file's downloaded bytes
        back). A DIRECT replace with no `remove_current_file()` step at all
        (`upload_file()` straight over an existing file, i.e. exactly the
        "Select File only if you want to REPLACE it" wording the widget's
        own on-screen help text uses) is unaffected by this — that path
        was confirmed live to persist correctly in ONE save, no two-phase
        needed. Callers reaching a genuinely EMPTY-field precondition (a
        case that literally requires "no file set") MUST use the two-phase
        sequence; callers simply replacing an existing file should call
        `upload_file()` directly, never through this method first."""
        self._file_upload_container(field_label).get_by_role(
            "button", name="Remove file"
        ).click()
        return self

    # ---- Lifecycle actions --------------------------------------------------

    def file_removal_pending(self, field_label: str) -> bool:
        """True once `remove_current_file()` has been clicked and the removal
        is waiting for the save (live 2026-10-13: the field swaps its "Remove
        file" button for "Undo remove" while `Current file: ...` stays on
        screen -- Remove / Undo remove take effect only on save, per the
        Object Authoring guide). So "the field reads empty" is NOT observable
        before the save; this is the pre-save signal that it will be."""
        return self._file_upload_container(field_label).get_by_role(
            "button", name="Undo remove").first.is_visible()

    def is_checked(self, field_label: str) -> bool:
        """Read-back counterpart to `set_checkbox()` — the class had a
        setter but no reader until 2026-09-09 (PBI 129394 tc_134887/
        tc_134888 needed to capture an `Active Status` baseline before
        flipping it, which is exactly the TEST_OWNED pattern standards.md
        requires for a shared real record)."""
        return self.page.get_by_role(
            "checkbox", name=self.label_pattern(field_label)
        ).is_checked()

    def rendered_body_text(self) -> str:
        """Full rendered text of whatever this object is currently showing --
        used after `preview_banner_text()` to prove the PREVIEW surface
        really renders an unpublished record's text. Lives here so a test
        never has to hold a raw `"body"` selector of its own."""
        return self.page.locator("body").inner_text()

    def spinbutton_value(self, field_label: str) -> str:
        """Read-back counterpart to fill_number() — mirrors field_value()'s
        exact-name-match textbox read, scoped to the spinbutton role instead
        (e.g. "Display Order"). Added 2026-09-08 (PBI 129367, tc_135009):
        no prior caller needed a numeric-field read-back on this surface."""
        return self.page.get_by_role(
            "spinbutton", name=self.label_pattern(field_label)
        ).input_value()

    def current_file_placeholder(self, field_label: str) -> str:
        """Persisted-file signal for a THIRD upload-widget variant this
        class's uploaded_filename()/current_file_name() do not cover —
        CONFIRMED LIVE 2026-09-08 (PBI 129367/tc_135009, manage-hero-
        banner-slide's Banner Image field): on a fresh reopen, this field's
        own `<strong role="textbox">` filename readout (uploaded_filename()'s
        target) stays empty — matching current_file_name()'s own already-
        documented finding for that element on OTHER objects — and this
        field ALSO has no richer `.qc-oel__current-file-meta` block
        (current_file_name()'s target: confirmed live absent here, unlike
        manage-chamber-laws-page/manage-law-entry). The ONLY confirmed-live
        persisted-file signal on THIS variant is the field's own hidden
        `<input type="text" ... placeholder="Current file: <name> — pick a
        file to replace it">`'s placeholder attribute — confirmed live via a
        real create -> Submit for Publishing -> fresh reopen round trip.
        Returns "" if the field has no current file (placeholder text does
        not start with "Current file:")."""
        hidden_textbox = self.page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        )
        placeholder = hidden_textbox.get_attribute("placeholder") or ""
        return placeholder if placeholder.startswith("Current file:") else ""

    @property
    def entry_code(self) -> str:
        """The entry code of whatever record was last opened for edit through
        this object, or "" when none was (e.g. the create-new form).

        Read-only, and public because a test needs the IDENTITY of a record
        it has just created without reconstructing it from a URL by hand --
        PBI 129394's tc_134978 asks whether a Law Entry's ID is
        auto-generated and unique, and this (with the entries list's own
        `row_entry_id()`) is where that identity is actually observable: the
        Law Entry edit FORM renders no ID control at all."""
        return self._entry_code or ""

    # ---- Fresh re-read of the record under edit ---------------------------
    # REAL, LIVE-MEASURED NEED (2026-09-15, PBI 129394): a lifecycle action's
    # own settle proves nothing about the record's committed state. Measured
    # live on manage-chamber-laws-page / manage-law-entry, 3 iterations each:
    #   - "Unpublish to edit as draft" -> status reads Draft in 1.20-1.38s
    #   - "Submit for Publishing"      -> status reads Approved in 27-30s
    # `submit_for_publishing()`'s ~2.5s settle is an order of magnitude short
    # of that, so anything that publishes and then immediately reads the
    # status (or polls the public page on a 20s budget) races a transition
    # that has not happened yet -- and a TEST_OWNED `finally` restore that
    # "publishes and assumes" leaves a real shared record stuck in Draft,
    # which is exactly how one failed test cascaded into three others' broken
    # preconditions. reopen()/wait_for_status() make the commit CHECKED
    # rather than assumed, from a FRESH navigation (never a stale,
    # post-save-reflowed DOM -- see TC 134877's own read-back-race note).

    def wait_for_status(
        self, expected: str, timeout: float = 90.0, poll: float = 3.0
    ) -> "ObjectAuthoringPage":
        """Polls until the record's OWN status reaches `expected`, re-opening
        it fresh on every poll. Raises WaitTimeoutError if it never does --
        a lifecycle action that silently did not commit must fail loudly,
        never be assumed to have worked.

        Both sides go through `normalize_status()` (2026-09-28), which draws a
        deliberate line between two different kinds of change:
          - a RENAME heals itself. The badge that used to read "Approved" now
            reads "Published"; both normalize to Published, so an existing
            `wait_for_status("Approved")` keeps expressing its real intent
            ("wait until this is live") and keeps working.
          - a BEHAVIOUR change stays red. Unpublish now lands on "Unpublished",
            which is NOT "Draft" under any normalization, so a caller waiting
            for Draft after unpublishing still fails — correctly, because that
            is a genuine difference in what the product does, not in what it
            calls things. Do not "fix" such a failure by relabelling it."""
        expected_status = normalize_status(expected)

        def _reached() -> bool:
            return self.reopen().current_status() == expected_status

        wait_until(
            _reached,
            timeout=timeout,
            poll=poll,
            message=(
                f"record {self._entry_code!r} on manage-{self.slug} never "
                f"reached status {expected_status!r}"
                + (f" (caller asked for {expected!r})"
                   if expected_status != expected else "")
            ),
        )
        return self

    def field_count(self, field_label: str) -> int:
        """Count of textboxes whose accessible name EXACTLY matches
        `field_label` — used to verify "exactly one field named X exists"
        cases (e.g. PBI 129393's TC 134787: exactly one Chairman Name field
        and one Chairman Designation field per language, no separate
        signature-block field) without a test ever touching raw Playwright
        (`get_by_role` stays inside this Page Object, never a test body).
        An exact-name match against a DIFFERENT label (e.g. a hypothetical
        separate signature-block field) never counts here, so a result of 1
        already proves both "exists" and "no duplicate/alternate field"."""
        return self.page.get_by_role(
            "textbox", name=self.label_pattern(field_label)
        ).count()

    def current_file_name(self, field_label: str) -> str:
        """Returns "" when the field is genuinely empty (no `Current file:`
        block rendered) — confirmed live to be the correct empty-state signal on
        this variant (see class docstring above), unlike
        `uploaded_filename()`'s own `<strong role="textbox">` scope, which
        stays empty on THIS variant even when a file IS set (that element
        only reflects a NEWLY selected, not-yet-saved file here)."""
        meta = self._file_upload_container(field_label).locator(
            ".qc-oel__current-file-meta"
        )
        if meta.count() == 0:
            return ""
        text = meta.first.inner_text()
        import re

        # HEALED 2026-09-07 (live incident, PBI 129394): Liferay auto-
        # dedupes a same-named re-upload by inserting "(<n>)" INSIDE the
        # filename, before the extension (e.g. "lawbook (4).png") — a
        # non-greedy match up to the FIRST "(" (the original version of
        # this regex) truncated the result to "lawbook" on exactly that
        # filename shape, dropping "(4).png" entirely (reproduced live
        # re-uploading the same fixture file multiple times in one
        # session). The trailing "(<size> KB/MB)" group is always the
        # LAST parenthesised run on the line, so matching greedily up to
        # the last "(" is the correct, reflow-safe boundary regardless of
        # how many "(...)" groups the filename itself contains.
        match = re.search(r"Current file:\s*(.+)\s*\(", text)
        return match.group(1).strip() if match else ""

    def reopen(self) -> "ObjectAuthoringPage":
        """Re-navigates to the record last opened through this object, so
        every read afterwards comes off a freshly rendered form."""
        if not self._entry_code:
            raise AssertionError(
                "reopen() needs a record opened via open_entry_by_code() "
                "first -- there is no entry code to navigate back to."
            )
        # Re-navigates in the SAME pinned locale the record was opened in --
        # a reopen that silently dropped the pin would flip the field labels
        # (and the validation-message language) mid-test.
        return self.open_entry_by_code(self._entry_code, locale=self._locale)

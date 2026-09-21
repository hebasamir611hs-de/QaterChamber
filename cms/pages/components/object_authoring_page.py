"""
cms/pages/components/object_authoring_page.py — ObjectAuthoringPage.

Shared, per-object-agnostic Control_Panel Page Object for the
`object-authoring` -> `manage-<slug>` Draft / Preview / Publish / Unpublish
lifecycle documented in .claude/context/active/standards.md's "Object
Authoring — Draft / Preview / Publish / Unpublish Lifecycle" section
(confirmed live 2026-09-03). Lives under pages/components/ (the plugin's
flat shared-component exception) because the state machine itself is
generic across every listed Object — only the slug and field data vary
per object, per that section's own "Testing implication" note. Field-level
locators (Title, Banner Alt Text (EN), etc.) stay OUT of this class — they
belong to each object's own admin Page Object (e.g.
HomeLatestNewsAdminPage, HomePromoBannersAdminPage), which now composes
this class for its Draft/Preview/Publish/Unpublish cases instead of
duplicating the state machine.

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


class ObjectAuthoringPage(BasePage):
    """Drives one Object's `manage-<slug>` page via the object-authoring
    surface. Construct with the object's slug (e.g. "news-article",
    "promotional-banner") — every locator/method below is generic across
    objects per the confirmed-live state machine documented above; only
    the slug (and the field data callers fill in on the object's own admin
    Page Object) varies per object."""

    SAVE_AS_DRAFT_BUTTON = 'button:has-text("Save as Draft")'
    SUBMIT_FOR_PUBLISHING_BUTTON = 'button:has-text("Submit for Publishing")'
    UNPUBLISH_BUTTON = 'button:has-text("Unpublish to edit as draft")'
    CANCEL_AND_ADD_NEW_LINK = 'a:has-text("Cancel and add a new entry instead")'
    ENTRIES_TABLE_ROW = "table tbody tr"

    UPLOAD_MODAL_IFRAME = 'iframe[src*="selectFileEntry"]'
    UPLOAD_MODAL_ADD_BUTTON_TEXT = "Add"

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
    DESCRIPTION_EDITOR_IFRAME = 'iframe[title="editor"] >> nth=0'

    def fill_rich_text(self, text: str) -> "ObjectAuthoringPage":
        self.fill_iframe_editor(self.DESCRIPTION_EDITOR_IFRAME, text)
        return self

    def rich_text_value(self) -> str:
        return self.iframe_editor_text(self.DESCRIPTION_EDITOR_IFRAME)

    def __init__(self, page, slug: str):
        super().__init__(page)
        self.slug = slug

    # ---- Navigation -----------------------------------------------------
    def _manage_url(self, edit_entry: str | None = None) -> str:
        path = f"/web/qatar-chamber/manage-{self.slug}"
        if edit_entry:
            path += f"?editEntry={edit_entry}"
        return control_panel_url(path)

    def open_new_entry_form(self) -> "ObjectAuthoringPage":
        """`manage-<slug>` with no editEntry param IS the create-new form —
        no separate "Add"/"New" button to click first. Widened to 35000ms
        (from 20000ms) 2026-09-03: manage-promotional-banner's cold first
        render (fresh pytest-launched browser context, first navigation of
        the test) intermittently outlived the original 20s budget live
        this session even though the same URL rendered near-instantly in
        an already-warm, long-lived session — a real page-load latency
        difference on first hit, not a wrong locator (SAVE_AS_DRAFT_BUTTON
        itself was never wrong)."""
        self.open(self._manage_url())
        self.wait_for(self.SAVE_AS_DRAFT_BUTTON, timeout=35000)
        return self

    def open_entries_list(self) -> "ObjectAuthoringPage":
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
        self.open(self._manage_url())
        self.wait_for("a[data-qc-oel-delete]", first=True, timeout=35000)
        return self

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
        self.wait_for(self.CANCEL_AND_ADD_NEW_LINK, timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS)
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
            self.page.wait_for_load_state("load", timeout=8000)

    # ---- List state queries ----------------------------------------------
    def row_status_text(self, title: str) -> str:
        """Normalized (`.strip().capitalize()`) Status cell text — e.g.
        "Draft", "Approved". Confirmed live 2026-09-03: the RAW rendered
        text differs by object due to per-object CSS (`text-transform:
        uppercase` on manage-promotional-banner's Status column reads
        "APPROVED"/"DRAFT" via `.inner_text()`, while manage-news-article's
        equivalent column has no such transform and reads "Approved"/
        "Draft" as-is) — normalizing here keeps every caller's comparison
        (`== "Draft"` / `== "Approved"`) object-agnostic rather than each
        test needing to know its own object's CSS quirk."""
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')
        if row.count() == 0:
            return ""
        return row.locator("td").nth(1).inner_text().strip().capitalize()

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
                value = self.page.get_by_role("textbox", name=field_label, exact=True).input_value()
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
        return row.locator("td").nth(1).inner_text().strip().capitalize()

    def row_visible_by_code(self, entry_code: str) -> bool:
        return self.is_visible(f'{self.ENTRIES_TABLE_ROW}:has-text("{entry_code}")')

    def open_entry_by_code(self, entry_code: str) -> "ObjectAuthoringPage":
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
        self.open(self._manage_url(edit_entry=entry_code))
        self._wait_for_network_settle()
        self.wait_for(self.CANCEL_AND_ADD_NEW_LINK, timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS)
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
        self.page.get_by_role("textbox", name=field_label, exact=True).fill(value)
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
        return self.page.get_by_role("textbox", name=field_label, exact=True).input_value()

    def current_status(self) -> str:
        """"Approved"/"Draft"/"Unknown" parsed out of editing_banner_text()'s
        confirmed-live wording ("...(approved)...")/"...(draft)...") — the
        same normalized vocabulary row_status_text()/row_status_text_by_code()
        already return, so callers can compare against either interchangeably.
        Only valid when called on an entry opened via open_entry_by_code()/
        open_entry_by_edit_link() (i.e. the editing banner is present)."""
        text = self.editing_banner_text()
        if "(approved)" in text:
            return "Approved"
        if "(draft)" in text:
            return "Draft"
        return "Unknown"

    def fill_number(self, field_label: str, value: str) -> "ObjectAuthoringPage":
        self.page.get_by_role("spinbutton", name=field_label, exact=True).fill(value)
        return self

    def type_date(self, field_label: str, value: str) -> "ObjectAuthoringPage":
        """Clicks the date field then types directly (mirrors the
        confirmed-live-safe pattern already used by every raw-admin date
        field on this project, e.g. HomeLatestNewsAdminPage.set_publication_date())."""
        self.page.get_by_role("textbox", name=field_label, exact=True).click()
        self.page.keyboard.type(value, delay=20)
        return self

    def set_checkbox(self, field_label: str, checked: bool) -> "ObjectAuthoringPage":  # noqa: D401
        checkbox = self.page.get_by_role("checkbox", name=field_label, exact=True)
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
        """See module docstring's file-upload note: locates the field's own
        hidden filename textbox by its confirmed-live accessible name
        pattern ("<Field Label> Select File"), then that textbox's sibling
        `Select File` button."""
        hidden_textbox = self.page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        )
        select_file_button = hidden_textbox.locator("xpath=..").get_by_role(
            "button", name="Select File"
        )
        select_file_button.click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)
        # The picker's own upload (set_input_files -> server-side upload ->
        # the file becoming a real, selectable entry) is asynchronous — the
        # "Add" button is present in the DOM immediately but not yet backed
        # by a completed upload. A bare click() right after set_input_files
        # intermittently hung for the full click timeout live 2026-09-03
        # (both here and in an earlier throwaway probe, which needed an
        # explicit ~2s wait between the two steps to pass reliably). Wait
        # for the uploaded file's own "1 of 1" progress/count text to
        # render as the real, condition-based signal instead of a blind
        # sleep; fall back to a short bounded wait if that text's exact
        # wording ever changes rather than hard-failing on a wording drift.
        try:
            frame.get_by_text("1 of 1").wait_for(state="visible", timeout=15000)
        except Exception:
            self.page.wait_for_timeout(2000)
        frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click(timeout=15000)
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
        except Exception:
            self.page.wait_for_timeout(1000)
        return self

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
            "textbox", name=field_label, exact=True
        ).inner_text().strip()

    # ---- Lifecycle actions --------------------------------------------------
    def save_as_draft(self) -> "ObjectAuthoringPage":
        self.click(self.SAVE_AS_DRAFT_BUTTON)
        self._wait_for_settle()
        return self

    def submit_for_publishing(self) -> "ObjectAuthoringPage":
        self.click(self.SUBMIT_FOR_PUBLISHING_BUTTON)
        self._wait_for_settle()
        return self

    def _wait_for_settle(self) -> None:
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
        settle_selector = (
            f'a[data-qc-oel-delete], {self.CANCEL_AND_ADD_NEW_LINK}, {self.SAVE_AS_DRAFT_BUTTON}'
        )
        try:
            self.page.wait_for_selector(settle_selector, state="attached", timeout=15000)
        except Exception:  # noqa: BLE001 — real, explicitly-capped fallback, never unbounded
            try:
                self.page.wait_for_load_state("load", timeout=8000)
            except Exception:  # noqa: BLE001
                pass
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
        self.page.wait_for_load_state("networkidle")
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

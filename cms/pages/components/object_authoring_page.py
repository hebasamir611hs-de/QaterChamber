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
    DESCRIPTION_EDITOR_IFRAME = 'iframe[title="editor"]'

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
        instead."""
        self.open(self._manage_url())
        self.wait_for("a[data-qc-oel-delete]", first=True, timeout=20000)
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
        self.page.wait_for_load_state("networkidle")
        self.wait_for(self.CANCEL_AND_ADD_NEW_LINK, timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS)
        return self

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
        self.page.wait_for_load_state("networkidle")
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
        """Bounded `networkidle` wait with a fallback — confirmed live
        2026-09-03 that `networkidle` can fail to fire at all within a
        generous 30s budget on this page even though `load` fires
        immediately (some continuous background network activity, e.g.
        the site-wide chatbot widget's own polling, keeps the network
        technically non-idle) — a real environment characteristic, not a
        broken save/submit action (the entries list's own status DOES
        update correctly once this method returns). Mirrors the same
        try/except-fallback shape already used by upload_file()'s own
        iframe-detach wait rather than blocking indefinitely on a signal
        this page may never emit."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            self.page.wait_for_load_state("load", timeout=8000)
        # Widened from 1500ms to 2500ms 2026-09-03: on the `networkidle`
        # timeout/fallback path specifically, this is the ONLY settle the
        # write (Save as Draft / Submit for Publishing) gets before a
        # caller may immediately poll the delivery surface (e.g.
        # reload_until_banner_matches) — matches this project's own
        # documented write-vs-read-cache propagation grace convention
        # (SAVE_COMMIT_GRACE_MS = 2000ms elsewhere) rather than a shorter,
        # unmeasured value that raced that propagation gap live this
        # session (Approved status was already correct in the entries
        # list at the time, but the separate delivery-surface read lagged
        # behind it).
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
            self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]').click(force=True)
            self.page.wait_for_load_state("networkidle")
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

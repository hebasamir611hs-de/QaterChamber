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

import re

from core.utils.logger import get_logger
from core.utils.waits import wait_until
from core.web.base_page import BasePage
from config.settings import control_panel_url

logger = get_logger("object_authoring_page")

# Confirmed-live-absent-on-first-render-tick grace: the "Unpublish to edit
# as draft" button/banner needs a real settle after the Edit-link's own
# networkidle before it reliably appears (see module docstring). Kept as
# a real wait_for with this as the upper-bound timeout, not a blind sleep.
APPROVED_BANNER_SETTLE_TIMEOUT_MS = 8000

# Workflow-status labels as rendered by the entries list's STATUS column.
#
# CONFIRMED LIVE 2026-09-10: that column started returning ARABIC labels
# ("مسودة" / "موافق عليه") even on the English page — same request, English
# URL (`/en/manage-<slug>`), English <title>, English column HEADERS
# ("ENTRY", "STATUS", ...), and English form buttons ("Save as Draft",
# "Submit for Publishing"). Only the status VALUES localize, and they
# follow the signed-in user's own account language rather than the page
# locale, so an account whose language preference is Arabic sees an
# otherwise-English screen with Arabic status values.
#
# Reported separately as an environment/UI finding. Normalizing here keeps
# every caller's `== "Draft"` / `== "Approved"` comparison working against
# either account language — the same object-agnostic intent the existing
# `.capitalize()` normalization already had (it was added because some
# objects' CSS uppercases this column). Unknown values pass through
# capitalized and therefore still fail loudly rather than silently mapping
# to a wrong state.
_STATUS_LABEL_TRANSLATIONS = {
    "مسودة": "Draft",
    "موافق عليه": "Approved",
}

# Status BADGE prefixes, matched case-insensitively against the start of the
# cell's text. CONFIRMED LIVE 2026-09-15 (manage-chamber-laws-page): that
# object's STATUS cell renders a second "ON THE WEBSITE" caption glued to the
# badge, and `.inner_text()` returns the pair as ONE run ("APPROVEDON THE
# WEBSITE"), so the previous whole-cell `.capitalize()` produced
# "Approvedon the website" and every `== "Approved"` comparison against
# `row_status_text*()` silently failed on this object. Matching the badge as
# a PREFIX keeps this object-agnostic (cells that carry only the badge are
# unchanged) instead of each caller needing to know its own object's cell
# layout. Anything that matches no badge still passes through capitalized, so
# an unknown value fails loudly rather than mapping to a wrong state.
_STATUS_BADGE_PREFIXES = (
    ("APPROVED", "Approved"),
    ("DRAFT", "Draft"),
    ("موافق عليه", "Approved"),
    ("مسودة", "Draft"),
)


def _normalize_status_label(raw: str) -> str:
    """Status-cell text -> this codebase's English status vocabulary."""
    text = (raw or "").strip()
    if not text:
        return ""
    first_line = text.splitlines()[0].strip()
    if first_line in _STATUS_LABEL_TRANSLATIONS:
        return _STATUS_LABEL_TRANSLATIONS[first_line]
    upper = first_line.upper()
    for badge, normalized in _STATUS_BADGE_PREFIXES:
        if upper.startswith(badge.upper()):
            return normalized
    return first_line.capitalize()


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
    #
    # HEALED FURTHER 2026-09-07 (live incident, PBI 129393/tc_134777,
    # manage-chairman-message-page, Message Content field): the ABOVE
    # nth=0 guarantee is confirmed-live ONLY for a freshly opened form
    # BEFORE any Save/Submit. A real Save as Draft / Submit for Publishing
    # triggers an in-place DOM reflow of this form (see `_wait_for_settle()`
    # below) that re-mounts BOTH iframes — mount ORDER across that reflow
    # is a race, not a guarantee, so `nth=0` can resolve to the AR editor
    # after a Save, causing a write/read-back right after Save to silently
    # target the wrong locale. Reproduced live: tc_134777's
    # fill_rich_text() -> save_as_draft() -> rich_text_value() sequence
    # read back `'\n'` instead of the just-written text.
    #
    # Root-caused live (headless Chromium, qcdev, manage-chairman-message-
    # page): the EN/default-locale editor's own underlying `<textarea>` /
    # CKEditor wrapper DOM id always contains `ObjectField_<fieldName>`
    # (Liferay's own canonical object-field name string, e.g.
    # `ObjectField_messageContent`), while the Arabic instance's own DOM id
    # always contains `qc-ar-<fieldName>` (this site's own custom
    # "qc-oel" Object-Authoring widget naming, e.g. `qc-ar-messageContent`)
    # — BOTH ids are keyed by the field's persistent name, never by mount
    # order, so scoping the iframe search to the EN id substring is immune
    # to the same post-Save reflow race that breaks `nth=0`. Confirmed live
    # unique (count=1) for the Message Content field both on a fresh open
    # and immediately after a real Save as Draft (in-place reflow, no page
    # navigation in between) — the exact tc_134777 sequence.
    #
    # `description_editor_iframe(field_name)` / the `field_name` parameter
    # on fill_rich_text()/rich_text_value() below are the OPT-IN fix: pass
    # the field's own Liferay object-field name (e.g. "messageContent") for
    # a locale-safe, reflow-safe locator. Omitting it preserves the
    # ORIGINAL `nth=0` behavior unchanged, so manage-strategic-pillar-card /
    # manage-general-manager-message (already proven correct under nth=0 in
    # their own confirmed-live usage) are not touched or re-verified here —
    # per this project's Result Integrity rule, a locale-id pattern
    # confirmed on ONE object's field is not silently assumed for others
    # without its own live check.
    RICH_TEXT_EDITOR_IFRAME_CSS = 'iframe[title="editor"]'
    DESCRIPTION_EDITOR_IFRAME = f'{RICH_TEXT_EDITOR_IFRAME_CSS} >> nth=0'

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

    def fill_rich_text(self, text: str, field_name: str | None = None) -> "ObjectAuthoringPage":
        self.fill_iframe_editor(self.description_editor_iframe(field_name), text)
        return self

    def rich_text_value(self, field_name: str | None = None) -> str:
        return self.iframe_editor_text(self.description_editor_iframe(field_name))

    # ---- Field-label matching ------------------------------------------
    # REAL, LIVE-CONFIRMED FIX (2026-09-15, PBI 129394 tc_134884): a
    # REQUIRED field's on-screen asterisk is part of its rendered <label>,
    # and therefore part of its ACCESSIBLE NAME -- so
    # `get_by_role("textbox", name="Law Number - Arabic", exact=True)`
    # matched ZERO elements while the live element's accessible name was
    # "Law Number - Arabic *". Measured live on both of this feature's
    # objects (manage-law-entry and manage-chamber-laws-page): the ENGLISH
    # halves of the bilingual pairs are NOT required (no asterisk) while
    # the ARABIC halves ARE (trailing " *"), so neither a blanket
    # "always add ' *'" nor a blanket "never add it" can be right -- and
    # a third shape exists too (the page object's "Intro Content" renders a
    # separate "Required" badge instead of an asterisk, and its Arabic
    # counterpart carries NO asterisk at all).
    #
    # Matching must therefore be tolerant of an OPTIONAL trailing asterisk
    # while staying ANCHORED, so an English label can never accidentally
    # match its own Arabic counterpart (or any longer label that merely
    # starts with the same words). A `^<label>\s*\*?\s*$` regex passed to
    # `get_by_role(name=...)` does exactly that; `exact=` is ignored by
    # Playwright when `name` is a regex, which is why it is dropped at every
    # call site below rather than left set to a value with no effect.
    #
    # Verified live 2026-09-15 on both objects (uniqueness count == 1 for
    # every field, EN and AR, on manage-chamber-laws-page's Page Title /
    # Intro Heading / Content Image Alt Text / References Heading and
    # manage-law-entry's Law Number / Law Title / Law Description /
    # External Link URL / Display Order / Active Status).
    @staticmethod
    def label_pattern(field_label: str) -> "re.Pattern":
        """Anchored accessible-name matcher tolerant of a required field's
        trailing ` *` (see the note above). Use this instead of
        `exact=True` for every role-based form-field lookup on this
        surface."""
        return re.compile(r"^\s*" + re.escape(field_label) + r"\s*\*?\s*$")

    def __init__(self, page, slug: str):
        super().__init__(page)
        self.slug = slug
        # Entry code of whatever record was last opened for edit through
        # this object -- set by open_entry_by_code()/open_entry_by_edit_link()
        # so reopen()/wait_for_status() can re-read the record from a FRESH
        # navigation instead of trusting a stale, post-save-reflowed DOM.
        self._entry_code: str | None = None
        # Interface locale this object last navigated in ("en"/"ar"/None for
        # "whatever the session happens to be") -- see _manage_url().
        self._locale: str | None = None

    # ---- Navigation -----------------------------------------------------
    # LOCALE PINNING -- REAL, LIVE-MEASURED NEED (2026-09-15, PBI 129394).
    # The unprefixed `/web/qatar-chamber/manage-<slug>` URL renders in
    # WHATEVER LOCALE THE SESSION CURRENTLY HOLDS, and on qcdev the shared
    # authoring account (test@liferay.com) has `ar_SA` as its own Liferay
    # language. Measured live, same storage state, same URL, one run apart:
    #
    #   fresh context -> /web/.../manage-law-entry   -> <html lang="ar-SA">
    #   after visiting /en/web/... once in the same context
    #                 -> /web/.../manage-law-entry   -> <html lang="en-US">
    #
    # That is not cosmetic. The form's field labels ARE the Object's own
    # per-locale labels, so the accessible name every `label_pattern()`
    # lookup resolves against CHANGES with the page locale:
    #
    #   en-US: "Law Number"  "Law Title"  "External Link URL"  "Display Order"
    #   ar-SA: "Law Number (AR)" "Law Title (AR)"
    #          "رابط النص القانوني الخارجي"  "ترتيب العرض"
    #
    # In an ar-SA render `get_by_role("textbox", name=^Law Number$)` resolves
    # ZERO controls (counted live). The page's own `isArabic()` reads
    # `document.documentElement.lang` too, so the same flip decides which
    # language every client-side validation message arrives in.
    #
    # `locale="en"` / `locale="ar"` therefore PINS the render, making both
    # the locators and the message language deterministic instead of
    # inherited. `locale=None` keeps the historic, session-inherited
    # behaviour byte-for-byte, so no existing caller changes.
    def _manage_url(
        self, edit_entry: str | None = None, locale: str | None = None
    ) -> str:
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
        instead."""
        self.open(self._manage_url(locale=locale))
        self._locale = locale
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
        self._wait_for_network_settle()
        self.wait_for(self.CANCEL_AND_ADD_NEW_LINK, timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS)
        # Record the code the Edit link actually landed on, so reopen()/
        # wait_for_status() work after this entry point too.
        try:
            code = self.page.url.split("editEntry=")[1].split("&")[0]
            self._entry_code = code or None
        except Exception:  # noqa: BLE001 — code tracking is best-effort here
            self._entry_code = None
        # ...and the LOCALE it landed in, read off the URL's own prefix. The
        # Edit link is relative, so clicking it from a `/en`-pinned list stays
        # on `/en`; recording that keeps reopen() from silently dropping the
        # pin and flipping every field label mid-test (see _manage_url()).
        try:
            first_segment = self.page.url.split("//", 1)[1].split("/")[1]
            self._locale = first_segment if first_segment in ("en", "ar") else None
        except Exception:  # noqa: BLE001 — locale tracking is best-effort here
            self._locale = None
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
        # WIDENED 2026-09-09 (PBI 129392): the `load` fallback RAISED when
        # `networkidle` also timed out — and `load` never fires at all on
        # this surface (measured: still timing out on a 15s budget), so a
        # page that is perfectly usable could blow up every caller of
        # open_entry_by_code()/open_entry_by_edit_link(). That took out 5 of
        # the 6 About Us tests at once. Same three-tier degrade as
        # `_wait_for_settle()`: this is a settle, not an assertion, so it
        # never raises — callers assert real conditions afterwards.
        for state, budget in (("networkidle", 8000), ("load", 8000), ("domcontentloaded", 8000)):
            try:
                self.page.wait_for_load_state(state, timeout=budget)
                return
            except Exception:  # noqa: BLE001 — fall through to the next-weaker signal
                continue

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
        return _normalize_status_label(row.locator("td").nth(1).inner_text())

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
                value = self.page.get_by_role(
                    "textbox", name=self.label_pattern(field_label)
                ).input_value()
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
        return _normalize_status_label(row.locator("td").nth(1).inner_text())

    def row_visible_by_code(self, entry_code: str) -> bool:
        return self.is_visible(f'{self.ENTRIES_TABLE_ROW}:has-text("{entry_code}")')

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
        self.wait_for(self.CANCEL_AND_ADD_NEW_LINK, timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS)
        return self

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

    def wait_for_status(
        self, expected: str, timeout: float = 90.0, poll: float = 3.0
    ) -> "ObjectAuthoringPage":
        """Polls until the record's OWN status reaches `expected`, re-opening
        it fresh on every poll. Raises WaitTimeoutError if it never does --
        a lifecycle action that silently did not commit must fail loudly,
        never be assumed to have worked."""

        def _reached() -> bool:
            return self.reopen().current_status() == expected

        wait_until(
            _reached,
            timeout=timeout,
            poll=poll,
            message=(
                f"record {self._entry_code!r} on manage-{self.slug} never "
                f"reached status {expected!r}"
            ),
        )
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
        """Fills the field whose accessible name is `field_label`, tolerating
        a required field's trailing ` *` -- see label_pattern()'s note."""
        self.page.get_by_role(
            "textbox", name=self.label_pattern(field_label)
        ).fill(value)
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
        return self.page.get_by_role(
            "textbox", name=self.label_pattern(field_label)
        ).input_value()

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
        self.page.get_by_role(
            "spinbutton", name=self.label_pattern(field_label)
        ).fill(value)
        return self

    def spinbutton_value(self, field_label: str) -> str:
        """Read-back counterpart to fill_number() — mirrors field_value()'s
        exact-name-match textbox read, scoped to the spinbutton role instead
        (e.g. "Display Order"). Added 2026-09-08 (PBI 129367, tc_135009):
        no prior caller needed a numeric-field read-back on this surface."""
        return self.page.get_by_role(
            "spinbutton", name=self.label_pattern(field_label)
        ).input_value()

    def type_date(self, field_label: str, value: str) -> "ObjectAuthoringPage":
        """Clicks the date field then types directly (mirrors the
        confirmed-live-safe pattern already used by every raw-admin date
        field on this project, e.g. HomeLatestNewsAdminPage.set_publication_date())."""
        self.page.get_by_role(
            "textbox", name=self.label_pattern(field_label)
        ).click()
        self.page.keyboard.type(value, delay=20)
        return self

    def set_checkbox(self, field_label: str, checked: bool) -> "ObjectAuthoringPage":  # noqa: D401
        checkbox = self.page.get_by_role(
            "checkbox", name=self.label_pattern(field_label)
        )
        if checked:
            checkbox.check()
        else:
            checkbox.uncheck()
        return self

    def is_checked(self, field_label: str) -> bool:
        """Read-back counterpart to `set_checkbox()` — the class had a
        setter but no reader until 2026-09-09 (PBI 129394 tc_134887/
        tc_134888 needed to capture an `Active Status` baseline before
        flipping it, which is exactly the TEST_OWNED pattern standards.md
        requires for a shared real record)."""
        return self.page.get_by_role(
            "checkbox", name=self.label_pattern(field_label)
        ).is_checked()

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

    def _picker_closed(self, timeout: int) -> bool:
        """True once the file-picker iframe is detached; False on timeout."""
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(
                state="detached", timeout=timeout
            )
            return True
        except Exception:  # noqa: BLE001 — caller decides what to do next
            return False

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

    # ---- File restore (Current file / Preview / Download) -----------------
    # CONFIRMED LIVE 2026-09-07 against manage-chamber-laws-page (Content
    # Image) and manage-law-entry (Law Icon), PBI 129394: unlike the
    # Chairman Portrait / Hero Banner Image fields on manage-chairman-
    # message-page (which expose ONLY "Select File" / "Remove file" — no
    # Download, see ChairmanMessageAdminPage's own docstring, which is why
    # that object's replace/upload-first-time cases stayed disclosed SKIPs),
    # THIS object's upload widget is a DIFFERENT, richer variant: once a
    # file is set, it renders an additional
    # `<div class="qc-oel__current-file-meta">Current file: <name> (<size>)
    # Preview · Download ... Remove file</div>` block — CONFIRMED LIVE a
    # sibling of the plain Liferay `form-group` 3 ancestor-levels above the
    # field's own hidden "<Field Label> Select File" textbox (verified via a
    # live ancestor walk: depth 1-2 = plain wrapper divs, depth 3 =
    # `form-group` and the FIRST ancestor level containing the meta block).
    # This gives a real, verified BINARY restore path this project's other
    # upload-only objects don't have: download the CURRENT file's bytes
    # before mutating, re-upload those same bytes in `finally` — never
    # assumed, always read fresh off the live record immediately before any
    # write, per this project's TEST_OWNED convention.
    def _file_upload_container(self, field_label: str):
        hidden_textbox = self.page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        )
        return hidden_textbox.locator("xpath=../../..")

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
        # WIDENED 2026-09-09 (live, PBI 129394): the `load` fallback is
        # itself unreliable on this surface — measured live today, after a
        # lifecycle action's form POST `domcontentloaded` fires immediately
        # but `load` NEVER fires (still timing out on a 15s budget; some
        # page resource never reaches completion, same class of cause as the
        # chatbot polling that already breaks `networkidle`). Both original
        # branches therefore raised while the action itself had already
        # committed in ~1.1s, turning a successful save/unpublish into a
        # broken test. This is a *settle*, not an assertion: it now degrades
        # through domcontentloaded and never raises, and callers assert the
        # real outcome (status transition / delivery surface) themselves —
        # which is what actually proves the write landed.
        for state, budget in (("networkidle", 8000), ("load", 8000), ("domcontentloaded", 8000)):
            try:
                self.page.wait_for_load_state(state, timeout=budget)
                break
            except Exception:  # noqa: BLE001 — fall through to the next-weaker signal
                continue
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
        `confirm()` dialog it fires.

        FIXED 2026-09-09 (live, PBI 129394 tc_134871/tc_134873): this method
        was the ONLY lifecycle action still calling raw
        `wait_for_load_state("networkidle")` with NO timeout — i.e.
        Playwright's 30s default — while `save_as_draft()` and
        `submit_for_publishing()` had already been migrated to
        `_wait_for_settle()`. `networkidle` never fires on this page (the
        site-wide chatbot widget's polling keeps the network non-idle; see
        `_wait_for_settle`'s own docstring, confirmed live 2026-09-03), so
        every caller of this method burned 30s and then raised
        TimeoutError — AFTER the click had already been dispatched, making a
        successful unpublish look like a broken test and skipping the
        caller's own post-conditions. Reproduced twice live on this batch.
        Now shares the same bounded settle+fallback as its sibling actions.
        """
        self.wait_for(self.UNPUBLISH_BUTTON, timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS)
        self.page.once("dialog", lambda d: d.accept())
        self.page.locator(self.UNPUBLISH_BUTTON).click()
        # Condition-based wait on the real OUTCOME, not a load-state signal —
        # measured live 2026-09-09: the confirm dialog is accepted and the
        # banner reports "(draft)" ~1.1s after the click, while `load` never
        # fires at all on this page. Polling the status is therefore both
        # faster and the only signal that actually proves the unpublish
        # committed.
        wait_until(
            lambda: self.current_status() == "Draft",
            timeout=20.0,
            poll=0.5,
            message=(
                "record status never became Draft after clicking "
                "'Unpublish to edit as draft'"
            ),
        )
        self._wait_for_settle()
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

    def preview_banner_text(self, preview_url: str) -> str:
        """Navigates directly to the record's own preview URL (row-level
        `Preview` link target) and returns the status-banner text this
        page's PREVIEW mode injects (see module docstring)."""
        self.open(preview_url)
        return self.page.locator('[role="status"]').first.inner_text()

    def rendered_body_text(self) -> str:
        """Full rendered text of whatever this object is currently showing --
        used after `preview_banner_text()` to prove the PREVIEW surface
        really renders an unpublished record's text. Lives here so a test
        never has to hold a raw `"body"` selector of its own."""
        return self.page.locator("body").inner_text()

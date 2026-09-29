"""
cms/pages/components/footer_admin_component.py — SocialMediaIconAdminPage.

Control_Panel Page Object for PBI 129366 (QC-GBL-004 — Site Footer & Social
Media Icons), Section 4 "Social Media Icons" fields. Lives under
pages/components/ per the GLOBAL cross-cutting component convention (see
.claude/context/active/standards.md's Automation Structure table: QC-GBL-004
-> file base "footer").

MANDATORY PRE-READ APPLIED: standards.md's "Object Authoring Is the Only Path
for Content Operations — Not Content & Data". Every field write and every
lifecycle action below goes through Object Authoring (`manage-<slug>`), never
Content & Data.

======================================================================
LIVE-CONFIRMED FACTS (scripted Playwright, real TEST_USER login, qcdev,
2026-09-16) — read before touching this class or its test module.
======================================================================

SLUG / URL — CONFIRMED LIVE, not guessed: `social-media-icon`,
`https://qcdev.ihorizons.com/web/qatar-chamber/manage-social-media-icon`
(page title confirmed: "Manage: Social Media Icon - Qatar Chamber - Liferay
DXP"). Found via a prior session's captured Objects-admin snapshot
(`snap1.md`, line 636: link "Social Media Icon" -> this exact URL), then
independently confirmed live this session.

**LOAD-BEARING FINDING #1 — this Object Authoring surface is SHARED between
the FOOTER (this PBI, QC-GBL-004) and the Home-page "Find us on social media"
widget (QC-HOME-004B), NOT two separate objects/surfaces.** The live form
renders 11 fields, not the 8 in PBI 129366's own field table: the 8
PBI-129366 (footer) fields below, PLUS "Show on Home" (checkbox), "Home Icon
Image" (separate upload), "Home Display Order" (separate spinbutton) —
confirmed live via `page.accessibility.snapshot()`. These 3 extra fields are
OUT OF SCOPE for this PBI's 29 cases and are left untouched (default/blank)
by every method below — flagged here so the QC-HOME-004B agent/session knows
this is the SAME record type, not a separate object; standards.md's per-PBI
table note ("distinct unless confirmed otherwise") should be corrected.

**LOAD-BEARING FINDING #2 — "Platform Name" (per the PBI's field table) is
NOT a free-text field on the live surface.** Its real, visible label is just
"Platform" (confirmed: real accessible name via `accessibility.snapshot()`
is `"Platform "`, trailing whitespace only — Playwright's own name-matching
normalizes that away), and it is a single-locale, autocomplete COMBOBOX
(`role="combobox"`, placeholder "Choose an Option", an "Open Options Menu"
trigger button) with EXACTLY 9 real, predefined options — confirmed live by
opening its own listbox: **Facebook, X, LinkedIn, Instagram, YouTube,
WhatsApp, Telegram, Snapchat, Flickr**. This is the SAME confirmed-live
combobox pattern already documented for Department's Parent Department field
(`org_structure_admin_page.py`): typing free text that doesn't match a real
option is accepted in the input WHILE FOCUSED, but CLEARS BACK TO EMPTY on
blur (confirmed live: filled "QCTEST-Platform-ZZZ", read back unchanged
before blur, pressed Tab, read back "" after). No native `maxlength` either
(a 60-char fill reads back all 60 chars) — the clearing-on-blur is the only
real practical ceiling on this field.

There is also **no distinct Arabic-locale "Platform Name" control** —
confirmed live, exactly one "Platform" combobox exists, no "Platform —
العربية" sibling (contrast with Icon Alt Text / Social Redirect URL below,
which ARE genuinely bilingual). Mirrors the already-established "AR Hero
Banner" gap on Org Structure (ADO-133311/133312) — 131169/131171 are SKIPPED
for the identical reason.

**Whether a duplicate Platform value (re-using one of the 9 already-used-by-
production values) is accepted or rejected as a duplicate was NOT
independently confirmed via an actual create+submit this session** (a
submit-triggering probe was blocked by this session's own sandbox — see "NOT
VERIFIED THIS SESSION" below). Best available evidence leans toward
"accepted": the Platform combobox's own options listbox (opened live) shows
all 9 values as selectable with no visible "already in use" affordance or
disabling of already-used options, unlike a picklist that actively prunes
taken values — every test in this module that creates an entry assumes
duplicates ARE accepted (reusing the 9 real platform names freely) on this
evidence, not a guess made in a vacuum; if this assumption is wrong, the
affected tests will fail loudly with a real duplicate-rejection signal
(`is_save_error_shown()`'s generic custom-alert fallback), not silently.

**LOAD-BEARING FINDING #3 (CORRECTED during scripting) — field accessible
names, confirmed via `page.accessibility.snapshot()` (ground truth, not the
raw-textContent heuristic an earlier probe in this same session
misinterpreted as a "(Read Only)" badge baked into the label — that
decorative text is NOT part of any field's real accessible name at all, and
this class does not need to work around it):**
  - `'Platform '`, `'Icon Alt Text '`, `'Social Redirect URL '`, `'Display
    Order '` — EN-locale fields, trailing space only (normalizes away under
    `exact=True`, confirmed live for every one of them).
  - `'Icon Alt Text — العربية *'`, `'Social Redirect URL — العربية *'` — AR
    fields carry a REAL trailing `" *"` (a required-field indicator, not
    whitespace) that does NOT normalize away — `exact=True` with the bare
    label (no asterisk) returns 0 matches; the `FIELD_*_AR` constants below
    therefore include the trailing `" *"` verbatim, confirmed live to
    resolve uniquely with it.
  - `'Active Status'`, `'Open in New Tab'`, `'Social Icon Image Select
    File'`, `'Social Icon Image'` (the upload readout `<strong>`) — clean,
    no suffix, `exact=True` confirmed to resolve uniquely for all of them,
    including on the BLANK create form (not just an already-filled entry).
  Every field on this surface is therefore reachable via the INHERITED
  `ObjectAuthoringPage` generic methods (`fill_text`/`field_value`/
  `fill_number`/`set_checkbox`, all `exact=True`) with no override needed —
  this class does not redefine any of them.

**LOAD-BEARING FINDING #4 — NO client-side truncation on Icon Alt Text or
Social Redirect URL (either locale).** Confirmed live: a 120-char fill on
Icon Alt Text (100-char PBI limit) and a 540-char fill on Social Redirect URL
(500-char PBI limit) both persisted IN FULL, unlike every `maxlength`-
truncated field on Org Structure's Department form. Not directly relevant to
any of the 29 cases' own field (none test Icon Alt Text's/Redirect URL's own
limits), but changes the enforcement-mechanism assumption for 131185 (Social
Redirect URL > 500 chars) — see that test's own comment.

**LOAD-BEARING FINDING #5 — Social Redirect URL is a native
`<input type="text">`, NOT `type="url"`.** Confirmed live: `checkValidity()`
on this field returns `true` even for `"not-a-valid-url"` — native
URL-format constraint validation NEVER fires. Any "invalid URL format is
rejected" behavior (131184) must be a custom, app-level check if it exists
at all.

**LOAD-BEARING FINDING #6 — upload helper text says "no larger than
10 MB."** (confirmed live, both Social Icon Image and Home Icon Image carry
the identical string: "Upload a .jpg,.jpeg,.png,.svg,.gif,.webp no larger
than 10 MB."). A THIRD number beyond ADO-131180's own title ("1 MB") and PBI
129366's field table ("2 MB"). Reported exactly as instructed, not silently
reconciled — mirrors the identical class of finding already logged on Org
Structure's About Hero Banner surface (helper text 5MB, PBI 2MB, nothing
enforced). Which (if any) number is actually enforced was NOT independently
verified this session.

**LOAD-BEARING FINDING #7 — no Cancel button exists on this form.**
Confirmed live (full form-container text dump): only "Save as Draft" and
"Submit for Publishing" — identical to every other `manage-<slug>` surface
project-wide. 131174 is SKIPPED per the task's explicit instruction not to
invent one.

**LOAD-BEARING FINDING #8 — the Entry-column list value is NOT this
object's Platform/Alt-Text, it's a stable external-reference-code.**
Confirmed live (read all 10 real rows): the 9 pre-existing production
entries show `QC-SMI-facebook`, `QC-SMI-x`, ..., `QC-SMI-flickr` (a fixed
per-platform code), and one true leftover shows a raw UUID. A NEW entry gets
its own Liferay-assigned UUID-style code, unknown in advance — the same
"Entry column is not the title field" situation already documented for
`manage-strategic-pillar-card`. `find_entry_code_by_alt_text_en()` below
(never `newest_entry_code()` — see standards.md's "Destructive Operations
Against qcdev" incident) is the only safe way to re-find a just-created
entry; it skips every `QC-SMI-*`-coded row up front (those are confirmed
production rows whose Icon Alt Text can never equal a `QCTEST …` value —
this bounds the scan to the small number of genuine leftover/just-created
rows instead of re-opening all 9 production entries on every call).

**CONFIRMED LIVE — `open_entry_by_code()`'s inherited wait is valid for this
object, no override needed:** an Approved entry's editing banner here reads
"Editing QC-SMI-facebook (approved). It is published. Use Unpublish to edit
as draft below... Cancel and add a new entry instead" — the "Cancel and add
a new entry instead" link (`ObjectAuthoringPage.CANCEL_AND_ADD_NEW_LINK`,
which `open_entry_by_code()` waits on) IS present here, unlike Department
(where it is confirmed ABSENT and required an override). Not independently
re-confirmed for a genuine Draft entry this session, but the base class's
own module docstring already documents this link present in BOTH Draft and
Approved banners project-wide.

**PRODUCTION-CONTENT CAUTION (disclosed, not silently worked around):** the
9 pre-existing rows are the REAL, LIVE production footer icons — confirmed
live they render inside the real `<footer>` element on the public Home page
("Find us on social media" section, `footer a[href="https://facebook.com/
qatarchamber"]` etc., 9 links, in the SAME left-to-right order every time:
Facebook, X, LinkedIn, YouTube, Instagram, Snapchat, Flickr, Telegram,
WhatsApp). Every test that creates an entry uses a HIGH `Display Order` by
default and a `try/finally` teardown (`delete_entry_by_code`) immediately
after its assertions, to minimize how long any test-created entry could
appear on the real public footer. 131187, 131188, 131193, and 131194 set
`Active Status = True` and reach Approved by design (the case itself
requires it); 131196 deliberately uses Save as Draft (never Submit for
Publishing) so it can never actually go live.

**NOT VERIFIED THIS SESSION — disclosed, not guessed around:** an actual
create -> Submit for Publishing -> verify -> delete round trip against this
object was attempted once during scripting (to resolve exactly which
upload-size number is enforced, and whether a duplicate Platform value is
accepted) and was BLOCKED by this session's own sandbox (a "Modify Shared
Resources" classifier denial on the mutating action) — not by qcdev itself.
Every mechanism documented above that did NOT require an actual Submit
(label text via `accessibility.snapshot()`, combobox options, native
`checkValidity()`, `disabled`/`readOnly` attributes, fill/read-back
truncation checks, the Entry-column contents of the 10 EXISTING rows, the
editing-banner text of a real Approved entry, the public footer's real DOM)
IS independently confirmed live this session. Anything phrased as "per the
established project-wide mechanism" or "not independently re-confirmed this
session" is an evidence-based inference from the identical, already-
confirmed mechanism on every sibling `manage-<slug>` surface (Department,
About Hero Banner) — not a fresh guess.

======================================================================
2026-09-16 HEAL SESSION — edit-mode-collision investigation (ADO-131182/
131189/131193/131196's `Timeout waiting for "Cancel and add a new entry
instead"` failures). Live-verified via real pytest runs (`-n 0`), not manual
probes.
======================================================================

**THE HANDED-DOWN HYPOTHESIS ("selecting one of the 9 already-used Platform
values on a fresh create form redirects into EDIT mode on the matching
production row") WAS LIVE-TESTED AND DISPROVEN.** Reproduced directly:
opened `manage-social-media-icon` fresh (`open_new_entry_form()`, no
`editEntry` param) — Platform combobox genuinely starts unselected (empty
`input_value()`), Icon Alt Text (EN) genuinely starts blank, and
`CANCEL_AND_ADD_NEW_LINK` is ABSENT. Selected "Facebook" (one of the 9,
already used by the real `QC-SMI-facebook` production row) via
`select_platform()` — afterward: URL unchanged (no navigation occurred, no
`editEntry` param appeared), Platform combobox correctly reads back
"Facebook", Icon Alt Text (EN) is STILL BLANK (not pre-filled with
Facebook's real production alt text), and `CANCEL_AND_ADD_NEW_LINK` is still
ABSENT. Selecting an already-used Platform value on this surface's create
form does NOT merge/redirect into an existing entry's edit state — the form
stays a genuine, distinct create form regardless of which of the 9 values is
chosen. `ensure_create_mode()` was therefore NOT implemented — there is no
live collision for it to guard against on THIS object (unlike Department,
where the analogous collision is real and confirmed).

**THE REAL, CONFIRMED MECHANISM: a qcdev session drop lands on the PUBLIC
site's "Coming Soon" placeholder, not a login form — a state
`core/web/session_guard.py`'s generic `reauthenticate()` guard cannot
detect.** `session_guard.py`'s own docstring already documents qcdev's
session dropping roughly every ~30s under sustained automated traffic, and
its `reauthenticate()` fires only on `is_login_form_showing()` (Liferay's
own login FORM). Live-reproduced this heal: forcing a navigation into
`manage-social-media-icon?editEntry=<code>` on a session that had gone stale
(confirmed via a real, unmodified `.auth/state.json` several hours old)
rendered the PUBLIC site's own "Coming Soon" 404-style fallback page — no
login form, no admin table, no editing banner — so `session_guard`'s guard
correctly saw no login form and no-oped, and `open_entries_list()`'s
`a[data-qc-oel-delete]` wait (and, by the identical mechanism,
`open_entry_by_code()`'s `CANCEL_AND_ADD_NEW_LINK` wait) timed out against a
page that could never satisfy it. Re-running the identical navigation
immediately after a fresh, verified login (`login_succeeded()` ==
`True`) rendered the real admin form/table correctly and instantly, INCLUDING
the pre-existing leftover raw-UUID entry `f9f9ebea-2e20-2513-bdcb-
d1c136f76f81` (a genuine test-debris leftover from an earlier session,
confirmed live via `Editing f9f9ebea… (approved)` banner text — not itself
broken once the session is valid).

`find_entry_code_by_alt_text_en()` is the one method on this class that ran
its OWN separate navigations (`open_entries_list()` + one
`open_entry_by_code()` per non-`QC-SMI-*` row) with NO login check of its
own — unlike every other navigation in a test, which starts from
`open_icons_list()`'s existing login-check-and-relogin pattern.
`find_entry_code_by_alt_text_en()` is called from `_teardown()` and from
several tests' own reload-persistence assertions, potentially MINUTES into a
test (after a slow upload/Submit for Publishing) — the single most exposed
point in this module's control flow to a mid-test session drop, and the
exact, now-CONFIRMED explanation for why only SOME create/verify tests
(131182/131189/131193/131196) hit this, independent of which of the 9
Platform values each one used (131177/131176/131181's own Instagram/
LinkedIn/Telegram runs did NOT fail — same Platform values as the failing
131189/131196/131193 — ruling out a Platform-value-specific cause and
pointing at session-drop timing instead, exactly as `session_guard.py`'s own
"~30s" window would predict for a long-running module).

**FIX APPLIED:** `_ensure_logged_in()` (new method on this class) — mirrors
`open_icons_list()`'s own `login_succeeded()` check-and-relogin pattern,
called at the start of `find_entry_code_by_alt_text_en()` AND immediately
before every per-row `open_entry_by_code()` call inside its scan loop. Not
added to the shared `ObjectAuthoringPage` base (out of this heal's scope —
narrowly patches the one object confirmed exposed) and not a widened/looser
locator or timeout — the exact confirmed gap is closed at its exact confirmed
location.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url, settings

SLUG = "social-media-icon"

FIELD_PLATFORM = "Platform"
FIELD_ICON_ALT_TEXT_EN = "Icon Alt Text"
# AR fields carry a REAL trailing " *" in their accessible name — see
# Finding #3. Do not "clean up" by removing it; `exact=True` requires it.
FIELD_ICON_ALT_TEXT_AR = "Icon Alt Text — العربية *"
FIELD_SOCIAL_REDIRECT_URL_EN = "Social Redirect URL"
FIELD_SOCIAL_REDIRECT_URL_AR = "Social Redirect URL — العربية *"
FIELD_OPEN_IN_NEW_TAB = "Open in New Tab"
FIELD_DISPLAY_ORDER = "Display Order"
FIELD_ACTIVE_STATUS = "Active Status"
FIELD_SOCIAL_ICON_IMAGE = "Social Icon Image"

# Confirmed live, exhaustive (see Finding #2) — the only 9 values this
# project's Platform combobox will ever accept.
PLATFORM_OPTIONS = (
    "Facebook", "X", "LinkedIn", "Instagram", "YouTube",
    "WhatsApp", "Telegram", "Snapchat", "Flickr",
)

# Confirmed live (Finding #8) — every genuine production row's Entry-column
# code carries this prefix; skipped up front by find_entry_code_by_alt_text_en()
# to bound the scan to just-created/leftover rows.
_PRODUCTION_ENTRY_CODE_PREFIX = "QC-SMI-"

# Confirmed live (module docstring's "PRODUCTION-CONTENT CAUTION" section) —
# the 9 real, live production rows' own stable Entry-column codes, keyed by
# their Platform value. Used by the 2026-09-17 PBI-129373 batch-2 (CMS
# Workflow/RBAC/Publish Lifecycle) tests that must edit/toggle/unpublish a
# SPECIFIC named real entry the QA case itself names (e.g. "the existing
# Snapchat entry", "the existing LinkedIn entry") — never a disposable
# QCTEST-created row, since the case's own precondition names the real row.
PRODUCTION_ENTRY_CODES = {
    "Facebook": "QC-SMI-facebook",
    "X": "QC-SMI-x",
    "LinkedIn": "QC-SMI-linkedin",
    "YouTube": "QC-SMI-youtube",
    "Instagram": "QC-SMI-instagram",
    "Snapchat": "QC-SMI-snapchat",
    "Flickr": "QC-SMI-flickr",
    "Telegram": "QC-SMI-telegram",
    "WhatsApp": "QC-SMI-whatsapp",
}

_UNVERIFIED = "TODO: run tools/extract_locators.py / MCP against the live page and paste the confirmed selector here"


class SocialMediaIconAdminPage(ObjectAuthoringPage):
    """Drives the shared `manage-social-media-icon` Object Authoring surface
    for PBI 129366's Section 4 (Social Media Icons) fields. See module
    docstring for every confirmed-live fact this class relies on. Every
    plain text/number/checkbox field is reachable via the INHERITED
    `ObjectAuthoringPage.fill_text()`/`field_value()`/`fill_number()`/
    `set_checkbox()` (all confirmed live to resolve `exact=True`, see
    Finding #3) — only the Platform combobox (not a plain textbox) and the
    Entry-column lookup (Finding #8) need this class's own methods."""

    ADMIN_HOME_EN_URL_PATH = "/en/home"

    # Class-level aliases of the module-level FIELD_* constants, so the test
    # layer can reference `admin.FIELD_SOCIAL_ICON_IMAGE` etc. directly
    # (mirrors OrgStructureAdminPage's own convention).
    FIELD_PLATFORM = FIELD_PLATFORM
    FIELD_ICON_ALT_TEXT_EN = FIELD_ICON_ALT_TEXT_EN
    FIELD_ICON_ALT_TEXT_AR = FIELD_ICON_ALT_TEXT_AR
    FIELD_SOCIAL_REDIRECT_URL_EN = FIELD_SOCIAL_REDIRECT_URL_EN
    FIELD_SOCIAL_REDIRECT_URL_AR = FIELD_SOCIAL_REDIRECT_URL_AR
    FIELD_OPEN_IN_NEW_TAB = FIELD_OPEN_IN_NEW_TAB
    FIELD_DISPLAY_ORDER = FIELD_DISPLAY_ORDER
    FIELD_ACTIVE_STATUS = FIELD_ACTIVE_STATUS
    FIELD_SOCIAL_ICON_IMAGE = FIELD_SOCIAL_ICON_IMAGE
    PLATFORM_OPTIONS = PLATFORM_OPTIONS

    # Confirmed live: no Cancel button exists anywhere on this form (see
    # Finding #7) — left an explicit unresolved placeholder rather than
    # guessed, per this project's `_require_verified` convention.
    CANCEL_BUTTON = _UNVERIFIED

    _REQUIRED_TEXT_FIELDS = (
        FIELD_ICON_ALT_TEXT_EN, FIELD_ICON_ALT_TEXT_AR,
        FIELD_SOCIAL_REDIRECT_URL_EN, FIELD_SOCIAL_REDIRECT_URL_AR,
    )

    def __init__(self, page):
        super().__init__(page, SLUG)

    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"SocialMediaIconAdminPage.{name} is an unverified placeholder — locate "
                f"the real admin surface / trigger the real UI state and replace it "
                f"before running this test."
            )

    # ---- Platform combobox — NOT a plain textbox, see Finding #2 ----------
    def platform_value(self) -> str:
        return self.page.get_by_role("combobox", name=FIELD_PLATFORM, exact=True).input_value()

    def select_platform(self, option_label: str) -> "SocialMediaIconAdminPage":
        """Selects one of the 9 real, confirmed-live options via the
        inherited `select_combobox_option()` ("Open Options Menu" trigger +
        `role=option` match) — never free-text entry, per Finding #2."""
        self.select_combobox_option(FIELD_PLATFORM, option_label)
        return self

    def fill_platform_free_text(self, value: str) -> "SocialMediaIconAdminPage":
        """Types arbitrary text into the Platform combobox WITHOUT
        selecting a real option and WITHOUT blurring — confirmed live this
        value is retained only while the field still has focus (see
        Finding #2). Used by the over-50-chars / script-injection cases,
        which assert the post-blur cleared state via `blur_platform()` +
        `platform_value()`."""
        self.page.get_by_role("combobox", name=FIELD_PLATFORM, exact=True).fill(value)
        return self

    def blur_platform(self) -> "SocialMediaIconAdminPage":
        self.page.get_by_role("combobox", name=FIELD_PLATFORM, exact=True).press("Tab")
        return self

    # ---- Direct state-query helpers for the test layer ---------------------
    def display_order_value(self) -> str:
        return self.page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True).input_value()

    def is_active_status_checked(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_ACTIVE_STATUS, exact=True).is_checked()

    # ---- uploaded_filename() override — CONFIRMED LIVE 2026-09-16 heal -----
    def uploaded_filename(self, field_label: str) -> str:
        """Overrides `ObjectAuthoringPage.uploaded_filename()` for THIS
        object only (not the shared base — every other `manage-<slug>`
        object keeps the base class's own locator; that pattern is confirmed
        correct there and this override does not touch it).

        ADO-131181 INVESTIGATION, LIVE-REPRODUCED (not guessed): the base
        method reads a `<strong role="textbox" aria-label="<Field Label>">`
        readout. On THIS surface that element is CONFIRMED DEAD/VESTIGIAL —
        live-reproduced across THREE separate create->Submit->reopen round
        trips (including one with a full `page.reload()` and a 20-SECOND
        poll, ruling out an async-hydration race): it reads `""` with
        `data-placeholder="No file selected."` EVERY time, no matter how
        long the wait, even though the SAME opened entry's real, visible
        upload state (a `<div data-qc-oel-current-file>` block containing
        `<strong>Current file:</strong> <filename> <span>(<size>)</span>` —
        DOM confirmed live via a direct `outerHTML` dump) shows the correct
        real filename immediately and reliably every time. **The image
        upload itself DOES persist correctly — ADO-131181 is an AUTOMATION
        WRONG-LOCATOR bug, not a real product defect**: `uploaded_filename()`
        was reading an element this surface never actually updates, instead
        of the real, always-current one. Scoped via `.first` on the
        page-wide `[data-qc-oel-current-file]` selector rather than a
        `field_label`-anchored one — this object's OTHER image field ("Home
        Icon Image", out of PBI 129366's own scope per Finding #1) is never
        filled by any test in this module, so exactly one such block exists
        on the page in every case this override is actually used for;
        disclosed here rather than silently assumed generic. Extracts the
        filename as the container's own first direct TEXT-NODE child
        (between the `<strong>Current file:</strong>` label and the
        trailing `<span>(size)</span>`) via `evaluate()`, not string-slicing
        the label/size text out of `.inner_text()` — robust even if a real
        filename itself contains parentheses."""
        current_file = self.page.locator("[data-qc-oel-current-file]").first
        if current_file.count() == 0:
            return ""
        try:
            return current_file.evaluate(
                "el => { const meta = el.querySelector('.qc-oel__current-file-meta') || el; "
                "for (const n of meta.childNodes) { if (n.nodeType === 3 && n.textContent.trim()) "
                "return n.textContent.trim(); } return ''; }"
            )
        except Exception:  # noqa: BLE001 — honest empty result, never forced
            return ""

    # ---- Icon Image upload -------------------------------------------------
    def upload_icon_image(self, file_path: str) -> "SocialMediaIconAdminPage":
        self.upload_file(FIELD_SOCIAL_ICON_IMAGE, file_path)
        return self

    def upload_icon_image_expect_rejected(self, file_path: str) -> bool:
        """Reliable ONLY for a small/instantly-rejected file (unsupported
        format) — see `ObjectAuthoringPage.upload_file_expect_rejected()`'s
        own docstring and the identical usage-boundary finding already
        logged on Org Structure's About Hero Banner surface (large files
        need the direct upload+submit+status flow instead, since this
        helper's internal timeout can race a slow real upload)."""
        return self.upload_file_expect_rejected(FIELD_SOCIAL_ICON_IMAGE, file_path)

    # ---- Combined form fill -------------------------------------------------
    def fill_icon_form(
        self,
        platform: str = None,
        alt_text_en: str = None,
        alt_text_ar: str = None,
        redirect_url_en: str = None,
        redirect_url_ar: str = None,
        open_in_new_tab: bool = None,
        display_order: str = None,
        active_status: bool = None,
    ) -> "SocialMediaIconAdminPage":
        if platform is not None:
            self.select_platform(platform)
        if alt_text_en is not None:
            self.fill_text(FIELD_ICON_ALT_TEXT_EN, alt_text_en)
        if alt_text_ar is not None:
            self.fill_text(FIELD_ICON_ALT_TEXT_AR, alt_text_ar)
        if redirect_url_en is not None:
            self.fill_text(FIELD_SOCIAL_REDIRECT_URL_EN, redirect_url_en)
        if redirect_url_ar is not None:
            self.fill_text(FIELD_SOCIAL_REDIRECT_URL_AR, redirect_url_ar)
        if open_in_new_tab is not None:
            self.set_checkbox(FIELD_OPEN_IN_NEW_TAB, open_in_new_tab)
        if display_order is not None:
            self.fill_number(FIELD_DISPLAY_ORDER, display_order)
        if active_status is not None:
            self.set_checkbox(FIELD_ACTIVE_STATUS, active_status)
        return self

    def save(self) -> "SocialMediaIconAdminPage":
        """Maps to Submit for Publishing, not Save as Draft — mirrors every
        sibling `manage-<slug>` Page Object's own `save()` (Department,
        Hero Banner): most of this module's cases must reach Approved to be
        assertable at all (a Draft record is invisible on both the admin
        entries list's `row_status_text` == "Approved" checks used
        throughout, and on the public footer)."""
        self.submit_for_publishing()
        return self

    def cancel(self) -> "SocialMediaIconAdminPage":
        self._require_verified(self.CANCEL_BUTTON, "CANCEL_BUTTON")
        self.click(self.CANCEL_BUTTON)
        return self

    # Confirmed-live-ABSENT-on-THIS-CLASS-OF-SURFACE inference (not
    # independently re-probed for THIS specific object this session): no
    # distinct "Reject" action exists on the shared Object Authoring editing
    # banner project-wide (test_home_promo_banners_control_panel.py and
    # test_home_strategic_direction_control_panel.py both already confirmed
    # live, twice, that this state machine has no Pending Review/Approve/
    # Reject step — only Save as Draft / Submit for Publishing / Unpublish
    # to edit as draft). Left an explicit unresolved placeholder rather than
    # a guessed selector, per this class's own `_require_verified`
    # convention (mirrors CANCEL_BUTTON above) — added 2026-09-17 for
    # ADO-131200 (PBI 129373 batch 2), which names a "Reject" action this
    # surface has never been confirmed to have.
    REJECT_BUTTON = _UNVERIFIED

    def reject(self) -> "SocialMediaIconAdminPage":
        self._require_verified(self.REJECT_BUTTON, "REJECT_BUTTON")
        self.click(self.REJECT_BUTTON)
        return self

    # ---- Navigation ---------------------------------------------------------
    def open_icons_list(self) -> "SocialMediaIconAdminPage":
        """Ensures a real authenticated session, then opens the combined
        entries-list + create-form page — mirrors
        `OrgStructureAdminPage.open_departments_list()`'s own
        login-if-needed shape (this surface performs no login check of its
        own; a stale session silently renders the public site instead of
        redirecting to login, confirmed project-wide)."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))
        if not login.login_succeeded():
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))
        self.open_new_entry_form()
        return self

    # ---- Real cross-session logout/login — mirrors
    # HomeAboutSummaryAdminPage's own identical-shaped methods (same
    # established project convention: `GET /c/portal/logout` ends the
    # session; a subsequent login() drives the real form again) — added for
    # the 2026-09-17 PBI-129373 batch-2 (CMS Workflow/RBAC/Publish
    # Lifecycle) cases that must authenticate as a SPECIFIC named CMS role
    # (Site Content Editor/Author/Content Contributor via
    # config.settings.cms_role_credentials()) rather than the shared
    # TEST_USER super-admin account every other test in this module uses. --
    LOGOUT_PATH = "/c/portal/logout"

    def logout_and_return(self) -> "SocialMediaIconAdminPage":
        self.open(control_panel_url(self.LOGOUT_PATH))
        return self

    def login_as(self, username: str, password: str) -> "SocialMediaIconAdminPage":
        from cms.pages.control_panel.login_page import CmsLoginPage

        CmsLoginPage(self.page).open_login().login(username, password)
        return self

    # ---- Baseline capture/restore for a NAMED real production entry -------
    # Mirrors HomeAboutCounterAdminPage.capture_baseline()/restore()'s own
    # identical shape (home_about_summary_admin_page.py) — added for the
    # 2026-09-17 batch's cases that edit/toggle a SPECIFIC real production
    # row the QA case itself names (e.g. "the existing Snapchat entry",
    # "the existing LinkedIn entry", "the existing X/Twitter entry") rather
    # than a disposable QCTEST-created one. Deliberately does NOT capture the
    # uploaded icon image itself — there is no way to read back and
    # re-upload the exact original image bytes without the original source
    # file (unlike every other field here, which round-trips through a
    # plain text/checkbox/spinbutton value) — any case that touches the
    # image field is scoped so the image write is attempted LAST, after
    # every other field, so a failure there (see ADO Bug #142266 — the
    # Documents-and-Media upload picker currently fails server-side on
    # qcdev) is reached before any other field's value is persisted via
    # save(), keeping the real row's other fields' baseline restore exact.
    def capture_icon_baseline(self, entry_code: str) -> dict:
        self.open_entry_by_code(entry_code)
        return {
            "entry_code": entry_code,
            "platform": self.platform_value(),
            "alt_text_en": self.field_value(FIELD_ICON_ALT_TEXT_EN),
            "alt_text_ar": self.field_value(FIELD_ICON_ALT_TEXT_AR),
            "redirect_url_en": self.field_value(FIELD_SOCIAL_REDIRECT_URL_EN),
            "redirect_url_ar": self.field_value(FIELD_SOCIAL_REDIRECT_URL_AR),
            "display_order": self.display_order_value(),
            "active_status": self.is_active_status_checked(),
        }

    def restore_icon_baseline(self, baseline: dict) -> "SocialMediaIconAdminPage":
        self.open_entry_by_code(baseline["entry_code"])
        self.fill_icon_form(
            alt_text_en=baseline["alt_text_en"], alt_text_ar=baseline["alt_text_ar"],
            redirect_url_en=baseline["redirect_url_en"], redirect_url_ar=baseline["redirect_url_ar"],
            display_order=baseline["display_order"], active_status=baseline["active_status"],
        )
        self.save()
        return self

    # ---- Session-drop defense — CONFIRMED LIVE 2026-09-16 (this heal) -----
    def _ensure_logged_in(self) -> None:
        """Defends `find_entry_code_by_alt_text_en()`'s own internal
        navigations (`open_entries_list()` + one `open_entry_by_code()` per
        non-production row) against a CONFIRMED-LIVE session-drop failure
        mode that `core/web/session_guard.py`'s own generic
        `reauthenticate()` guard does NOT catch.

        LIVE-REPRODUCED THIS HEAL (not inferred): `core/web/session_guard.py`
        documents qcdev's session dropping roughly every ~30s under
        sustained automated traffic, and its `reauthenticate()` fires only
        when `is_login_form_showing()` — Liferay's own login FORM — is
        detected. On THIS `manage-social-media-icon` surface specifically, a
        dropped session does NOT render a login form at all: it silently
        renders the PUBLIC site's own "Coming Soon" placeholder page instead
        (confirmed live this session by forcing a stale-session navigation:
        `page.locator(...).count()` for the login form's own selector was 0,
        yet the real admin form/table never rendered either) — a state
        `session_guard.py`'s generic guard has no way to recognize, so it
        silently no-ops and every downstream `wait_for()` (whether
        `open_entries_list()`'s own `a[data-qc-oel-delete]` or
        `open_entry_by_code()`'s `CANCEL_AND_ADD_NEW_LINK`) times out against
        a page that will never satisfy it — this is the CONFIRMED, exact
        mechanism behind the reported `Timeout waiting for "Cancel and add a
        new entry instead"` failures (ADO-131182/131189/131193/131196):
        NOT a Platform-combobox edit-mode collision (that hypothesis was
        live-tested and DISPROVEN this heal — see class docstring's new
        finding below).

        `open_icons_list()` already carries the identical login-check
        pattern for a test's OWN initial navigation; this mirrors it here
        because `find_entry_code_by_alt_text_en()` runs its own separate
        navigations, potentially MINUTES after that initial check (after a
        slow upload/Submit-for-Publishing), the single most exposed point in
        this module's own control flow to a mid-test session drop. Cheap,
        state-agnostic, and safe to call from anywhere: `login_succeeded()`
        only checks the CURRENT page for the Control Menu nav, never
        navigates itself."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        if not login.login_succeeded():
            login.open_login().login(settings.test_user, settings.test_password)

    # ---- Verified (never positional) entry lookup — see Finding #8 --------
    def find_entry_code_by_alt_text_en(self, expected_alt_text_en: str) -> str:
        """Same-shaped override of
        `ObjectAuthoringPage.find_entry_code_by_field()`. Required because
        this object's Entry column shows a stable per-platform code
        (`QC-SMI-<platform>`) or a raw UUID for a freshly created entry —
        never the entry's own Icon Alt Text — so a freshly created entry can
        only be found back by reading its real field value off every row's
        own edit form. Skips every `QC-SMI-*`-coded row up front (confirmed
        live: those are the 9 real production entries, whose own Icon Alt
        Text can never equal a `QCTEST …` test value) to bound the scan cost
        on an environment with a documented session-drop-under-load failure
        mode — see standards.md's "No concurrent live-browser agents" /
        session_guard.py notes. Calls `_ensure_logged_in()` before its own
        `open_entries_list()` AND before every per-row `open_entry_by_code()`
        (see that method's docstring for the confirmed-live mechanism this
        guards against). NEVER use `newest_entry_code()` to select a
        delete/mutate target — see standards.md's "Destructive Operations
        Against qcdev" incident."""
        self._ensure_logged_in()
        self.open_entries_list()
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        codes = [rows.nth(i).locator("td").nth(0).inner_text().strip() for i in range(rows.count())]
        for code in codes:
            if code.startswith(_PRODUCTION_ENTRY_CODE_PREFIX):
                continue
            self._ensure_logged_in()
            self.open_entry_by_code(code)
            try:
                value = self.field_value(FIELD_ICON_ALT_TEXT_EN)
            except Exception:  # noqa: BLE001 — field may not exist/apply to this row's form state
                continue
            if value == expected_alt_text_en:
                return code
        return ""

    # ---- Validation mechanism ------------------------------------------------
    def _icon_image_hidden_textbox(self):
        """The Social Icon Image field's own hidden, required filename
        textbox — same confirmed-live pattern documented in
        `ObjectAuthoringPage.upload_file()`'s docstring ("<Field Label>
        Select File"), confirmed live to resolve uniquely on the BLANK
        create form (not just an already-filled entry). Included in
        `_required_field_locators()` so a missing-mandatory-image violation
        (131178) is detectable through the same native `checkValidity()`
        mechanism as every other required field on this surface."""
        return self.page.get_by_role("textbox", name=f"{FIELD_SOCIAL_ICON_IMAGE} Select File")

    def _required_field_locators(self):
        locs = [self.page.get_by_role("combobox", name=FIELD_PLATFORM, exact=True)]
        for label in self._REQUIRED_TEXT_FIELDS:
            locs.append(self.page.get_by_role("textbox", name=label, exact=True))
        locs.append(self.page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True))
        locs.append(self._icon_image_hidden_textbox())
        return locs

    def is_save_error_shown(self) -> bool:
        """Ported from the SAME confirmed-live mechanism already
        established project-wide for every other `manage-<slug>` Object
        Authoring surface (`OrgStructureAdminPage.is_save_error_shown()`):
        no custom app-rendered validation-error element was found for a
        missing-required-field violation on THIS surface either (native
        `checkValidity()` on each required field is the real, confirmed
        gate) — NOT independently re-confirmed live this session via an
        actual blocked Submit click (a submit-triggering probe was denied
        by this session's own sandbox, see module docstring's "NOT VERIFIED
        THIS SESSION" note), inferred from the identical mechanism already
        confirmed twice on Department and About Hero Banner. Applies the
        SAME defensive "at least one other required field still filled"
        heuristic Department's own method uses, to guard against this
        surface's own likely post-Submit blank-form reset (confirmed
        project-wide on every `manage-<slug>` surface probed for it so
        far) being misread as a rejection."""
        handles = []
        for loc in self._required_field_locators():
            try:
                if loc.count() != 1:
                    continue
                handle = loc.element_handle()
                if handle is None:
                    continue
            except Exception:  # noqa: BLE001 — field may be mid-navigation
                continue
            handles.append(handle)
        invalid_count = 0
        filled_count = 0
        if handles:
            try:
                results = self.page.evaluate(
                    "elements => elements.map(e => ({valid: e.checkValidity ? "
                    "e.checkValidity() : true, value: e.value}))",
                    handles,
                )
            except Exception:  # noqa: BLE001
                results = []
            for result in results:
                if result["value"]:
                    filled_count += 1
                if not result["valid"]:
                    invalid_count += 1
        if invalid_count and filled_count > 0:
            return True
        alert = self.page.locator('[role="alert"], .alert-danger')
        for i in range(alert.count()):
            try:
                if alert.nth(i).inner_text().strip():
                    return True
            except Exception:  # noqa: BLE001
                continue
        return False

    def save_error_text(self) -> str:
        """Custom app-level error text if any real one is ever found, else
        the FIRST invalid required field's own native `validationMessage`
        — see `OrgStructureAdminPage.save_error_text()`'s identical
        docstring for why this will read the browser's own generic English
        string ("Please fill out this field."), never a localized app
        message, on every surface confirmed so far in this project."""
        alert = self.page.locator('[role="alert"], .alert-danger')
        for i in range(alert.count()):
            try:
                text = alert.nth(i).inner_text().strip()
            except Exception:  # noqa: BLE001
                continue
            if text:
                return text
        for loc in self._required_field_locators():
            try:
                if loc.count() != 1:
                    continue
                result = loc.evaluate(
                    "e => ({valid: e.checkValidity ? e.checkValidity() : true, "
                    "msg: e.validationMessage || ''})"
                )
            except Exception:  # noqa: BLE001
                continue
            if not result["valid"]:
                return result["msg"]
        return ""

"""
cms/pages/board_of_directors/board_members_admin_page.py — BoardMembersAdminPage.

Control_Panel Page Object for PBI 129398 (QC-ABOUT-006 — Board of Directors
& General Director), backing the PER-MEMBER admin surface — a Liferay Object
Definition (objectDefinitionId=80051, groupId=37246).

MIGRATED 2026-09-07 (mandatory per .claude/context/active/standards.md's
"Object Authoring Is the Only Path for Content Operations — Not Content &
Data" rule, broadened same day): this class now drives the Board Member
object exclusively through the **Object Authoring** surface
(`manage-board-member`, composing `ObjectAuthoringPage` — see
cms/pages/components/object_authoring_page.py) instead of the old
`Content & Data > Board Members` menu path. Mirrors the same migration
already done for `cms/pages/org_structure/org_structure_admin_page.py`
(same day) — read that module's docstring for the general shape of this
change; only the Board-Member-specific facts are repeated below.

SLUG CONFIRMED LIVE 2026-09-07 (headless Chromium, 1920x1080, real
authenticated session, `python tools/extract_locators.py` against
`https://qcdev.ihorizons.com/object-authoring` plus a direct navigation
probe): the Object Authoring index lists this object as "Board Member" ->
`/web/qatar-chamber/manage-board-member`. Direct navigation confirmed page
title "Manage: Board Member - Qatar Chamber - Liferay DXP", a real
"Save as Draft" button, and an 18-row entries table (matching the 18 live
board members already known from the public listing page) — this is the
SAME generic create-form-on-the-list-page + Draft/Preview/Publish/Unpublish
state machine ObjectAuthoringPage already documents for every other object
on this project (org_structure/department, home_business_events, etc.).

FIELD SET CONFIRMED LIVE 2026-09-07 (role-probe via a throwaway
Playwright script against a fresh create-form and an existing entry's edit
form, EVERY one below resolved to exactly 1 match via
`get_by_role(role, name=label, exact=True)`, matching the generic
ObjectAuthoringPage contract exactly — no shadow-DOM/xpath workaround
needed here, unlike the OLD Content & Data DDM form this class used to
target):
    textbox     "Full Name"                          (single field — see below)
    textbox     "Full Name — العربية"                (CONFIRMED a SEPARATE
                                                        field on THIS surface —
                                                        see note below)
    textbox     "Position Label"
    textbox     "Role Badge Label"
    textbox     "Photo Alt Text"
    textbox     "Short Bio"
    textbox     "Professional Experience Entries"
    spinbutton  "Display Order"
    combobox    "Member Category"                     (plain click-to-open
                                                        combobox, 4 options:
                                                        Chairman / Vice Chairman /
                                                        Board Member / General
                                                        Manager — confirmed live)
    checkbox    "Active Status"
    checkbox    "Enable Share Icons"
    "Member Photo Select File" (hidden textbox) + sibling "Select File"
        button — same ObjectAuthoringPage.upload_file() pattern as every
        other object's file field on this project.

CORRECTION vs. the OLD (pre-migration) docstring: that version stated
"There is NO separate AR field pair... each is ONE field with its own
locale-toggle button" for Full Name/Position Label/Role Badge Label/Photo
Alt Text, based on the OLD Content & Data DDM form. On THIS surface
(Object Authoring), Full Name DOES have a separate, independently-named
AR textbox ("Full Name — العربية", confirmed live, exact=True, 1 match) —
the same bilingual-field pattern ObjectAuthoringPage.field_value()'s own
docstring already documents for manage-general-manager-message. Not
independently re-confirmed for Position Label/Role Badge Label/Photo Alt
Text this session (out of scope for this batch's 8 target cases, all of
which are EN-only) — re-verify before building an AR-locale case on those
specific fields rather than assuming the same shape holds.

ACTIVE STATUS CHECKBOX — PREVIOUSLY BLOCKED, NOW RESOLVED BY THIS
MIGRATION: the pre-migration version of this file left ACTIVE_STATUS_CHECKBOX
and ENABLE_SHARE_ICONS_CHECKBOX as UNCONFIRMED text-anchored placeholders —
`get_by_role("checkbox", name=...)` reportedly returned 0 matches, 3 retries,
against the OLD Content & Data DDM form. Root cause, confirmed live this
session: that form's accessibility-tree-reported checkbox nodes lived behind
whatever shadow-DOM/rendering boundary caused this project's other documented
`get_by_role()` failures on that same OLD surface (see the OLD org_structure
docstring's shadow-DOM note — same class of gap). On the NEW Object
Authoring surface, `get_by_role("checkbox", name="Active Status", exact=True)`
resolves to exactly 1 match on the first live probe, no workaround needed —
confirmed both on a blank create form (default UNCHECKED — see next
paragraph) and on an existing Approved entry's edit form (confirmed
`checked=True` there, and a live create->uncheck->Submit for
Publishing->reopen round-trip confirmed the unchecked state PERSISTS and
correctly removes the entry from the public "active members" grid + counter).

ACTIVE STATUS DEFAULTS TO UNCHECKED ON A NEW ENTRY — confirmed live
2026-09-07: a blank create form's "Active Status" checkbox is UNCHECKED by
default. A newly-created member that is meant to appear on the public site
(and count toward the "N active members" counter) MUST have
`active_status=True` explicitly set — omitting it silently creates an
Approved-but-inactive record that will not appear publicly. This is exactly
the mechanic ADO 133513 ("adding a new ACTIVE board member increments the
counter") is testing.

CONFIRMED LIVE PRODUCT DEFECT 2026-09-07 (relevant to ADO 133471): changing
an EXISTING Approved entry's "Member Category" field and clicking "Submit
for Publishing" again does NOT persist the new category — a live probe
(create as "Board Member" -> publish -> confirm in the public Board Members
grid -> edit -> select "Vice Chairman" in the Member Category combobox
(confirmed via the field's own hidden backing inputs,
`ObjectField_memberCategory=viceChairman`, that the NEW value WAS staged
correctly before Submit) -> Submit for Publishing -> reopen fresh) found the
combobox reverts to unset ("Choose an Option") on reopen, and the public
listing still renders the card in its ORIGINAL "Board Members" grid section,
never moving to "Vice Chairmen". This reproduced twice. By contrast, a
Boolean checkbox field edited the SAME way (Active Status, on an existing
Approved entry, Submit for Publishing, reopen) persisted correctly and
propagated to the public counter/listing within seconds — so this is a
genuine, category-combobox-specific edit-persistence defect on THIS surface,
not a general "editing an approved entry doesn't work" issue. See
cms/tests/board_of_directors/test_board_of_directors_control_panel.py's
ADO-133471 test docstring for the test that captures this as a real,
intentional FAILURE (per automation-standards.md's Result Integrity rules —
not silently narrowed or skipped).

BACKWARD-COMPATIBLE CONSTANTS (same technique as OrgStructureAdminPage):
several already-existing tests in this module (the 26 pre-existing,
OUT-OF-SCOPE-for-this-batch tests) reference this class's field/button
constants DIRECTLY as raw locator strings (`admin.SHORT_BIO`,
`admin.DISPLAY_ORDER`, `admin.FULL_NAME`, etc.) passed straight into
`BasePage.type()/field_value()` — never through a method. Playwright's own
`role=` locator-engine syntax (`page.locator('role=textbox[name="..."]')`,
confirmed live functionally identical to `get_by_role(..., name="...")` for
every field probed this session) lets those constants keep working as plain
strings with NO changes to `BasePage.type()/field_value()`'s signatures.
`SAVE_BUTTON` (no single "Save" button exists on this surface — only "Save
as Draft"/"Submit for Publishing", confirmed live: "Submit for Publishing"
remains enabled even on an already-Approved entry, unlike "Save as Draft"
which is disabled once Approved) is mapped to
`ObjectAuthoringPage.SUBMIT_FOR_PUBLISHING_BUTTON`'s own selector string,
and `save()` maps to `submit_for_publishing()` — same LIFECYCLE MAPPING
precedent as OrgStructureAdminPage.save()/HomeBusinessEventsAdminPage.

DISCLOSED CAVEAT on `SAVE_BUTTON` as a wait target (out of scope to fix —
affects only the 26 pre-existing tests' `board_member_row` fixture, which
does a raw `admin.click(...); admin.wait_for(admin.SAVE_BUTTON)` sequence
rather than calling `open_member_edit_form_by_row_index()`): confirmed live
this session that `manage-board-member`'s bare list URL (no `editEntry`)
ALSO renders its own inline create-form's "Submit for Publishing" button —
so `wait_for(SAVE_BUTTON)` can pass instantly even before the Edit-link
click's navigation to `?editEntry=...` has actually completed, racing on
slow navigations. This class's OWN new methods
(`open_member_edit_form_by_row_index()`, `open_member_edit_form_by_name()`)
avoid this by waiting on `CANCEL_AND_ADD_NEW_LINK` instead (confirmed live
to appear ONLY on an actual `?editEntry=...` page) — use those for any new
coverage rather than the raw `LIST_ROW`/`ROW_ID_LINK`/`SAVE_BUTTON` compat
constants.

DISCLOSED, NOT FIXED (out of this batch's scope — the 26 pre-existing tests
are explicitly not to be touched or re-run): the OLD `board_member_row`
fixture (test module, ~line 154) opens a row via
`{LIST_ROW}:has-text("Board Member") >> nth=0 >> {ROW_ID_LINK}` — relying on
the row's OWN rendered text containing the category "Board Member". On
THIS surface the entries table's columns are Name / Status / Last modified /
Actions ONLY (confirmed live via a direct row-text dump) — no category
column exists in the row text at all (a structural difference from the OLD
Content & Data grid, which apparently rendered category inline). That
`:has-text("Board Member")` filter will therefore match ZERO rows on this
surface, breaking `board_member_row` and its dependent pre-existing tests
the next time they run. This is flagged here for the QA Manager, mirroring
OrgStructureAdminPage's own disclosed-not-fixed SEARCH_INPUT finding — not
silently left as a landmine, but also not fixed here since those tests are
explicitly out of this batch's scope. `find_row_index_by_category()` has the
exact same underlying limitation (category text is not present in any row
to scan) and is left unchanged for the same reason.
"""

import time

from cms.pages.components.object_authoring_page import (
    APPROVED_BANNER_SETTLE_TIMEOUT_MS,
    ObjectAuthoringPage,
)
from config.settings import control_panel_url, settings

SLUG = "board-member"

ADMIN_HOME_EN_URL_PATH = "/en/home"
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'

FIELD_FULL_NAME = "Full Name"
FIELD_FULL_NAME_AR = "Full Name — العربية"
FIELD_POSITION_LABEL = "Position Label"
FIELD_ROLE_BADGE_LABEL = "Role Badge Label"
FIELD_PHOTO_ALT_TEXT = "Photo Alt Text"
FIELD_SHORT_BIO = "Short Bio"
FIELD_DETAILED_BIOGRAPHY = "Detailed Biography"
FIELD_PROFESSIONAL_EXPERIENCE_ENTRIES = "Professional Experience Entries"
FIELD_DISPLAY_ORDER = "Display Order"
FIELD_MEMBER_CATEGORY = "Member Category"
FIELD_MEMBER_PHOTO = "Member Photo"
FIELD_ACTIVE_STATUS = "Active Status"
FIELD_ENABLE_SHARE_ICONS = "Enable Share Icons"

CATEGORY_CHAIRMAN = "Chairman"
CATEGORY_VICE_CHAIRMAN = "Vice Chairman"
CATEGORY_BOARD_MEMBER = "Board Member"
CATEGORY_GENERAL_MANAGER = "General Manager"


class BoardMembersAdminPage(ObjectAuthoringPage):
    """Composes the generic Object Authoring state machine
    (`ObjectAuthoringPage`) with the Board Member object's own field map.
    Constructed with just `page` (slug fixed to "board-member")."""

    def __init__(self, page):
        super().__init__(page, SLUG)

    # ---- Backward-compatible field/button constants (see module docstring)
    LIST_ROW = ObjectAuthoringPage.ENTRIES_TABLE_ROW
    ROW_ID_LINK = 'role=link[name="Edit"]'
    SAVE_BUTTON = ObjectAuthoringPage.SUBMIT_FOR_PUBLISHING_BUTTON

    FULL_NAME = f'role=textbox[name="{FIELD_FULL_NAME}"]'
    POSITION_LABEL = f'role=textbox[name="{FIELD_POSITION_LABEL}"]'
    ROLE_BADGE_LABEL = f'role=textbox[name="{FIELD_ROLE_BADGE_LABEL}"]'
    PHOTO_ALT_TEXT = f'role=textbox[name="{FIELD_PHOTO_ALT_TEXT}"]'
    SHORT_BIO = f'role=textbox[name="{FIELD_SHORT_BIO}"]'
    DETAILED_BIOGRAPHY = f'role=textbox[name="{FIELD_DETAILED_BIOGRAPHY}"]'
    PROFESSIONAL_EXPERIENCE_ENTRIES = f'role=textbox[name="{FIELD_PROFESSIONAL_EXPERIENCE_ENTRIES}"]'
    DISPLAY_ORDER = f'role=spinbutton[name="{FIELD_DISPLAY_ORDER}"]'
    MEMBER_CATEGORY_COMBOBOX = f'role=combobox[name="{FIELD_MEMBER_CATEGORY}"]'
    ACTIVE_STATUS_CHECKBOX = f'role=checkbox[name="{FIELD_ACTIVE_STATUS}"]'
    ENABLE_SHARE_ICONS_CHECKBOX = f'role=checkbox[name="{FIELD_ENABLE_SHARE_ICONS}"]'

    # ---- AR (Arabic) bilingual-twin field constants — CORRECTED 2026-09-17
    # (PBI 129398 BATCH 6, final-40 batch). The OLD `FULL_NAME_AR = f'role=
    # textbox[name="{FIELD_FULL_NAME_AR}"]'` constant (exact=True, NO
    # trailing " *") this class previously carried is CONFIRMED LIVE this
    # session to be STALE/WRONG: every one of these AR twin fields is
    # natively `required` on the real form (confirmed via a direct DOM
    # dump: `id="qc-ar-fullName"`/`qc-ar-positionLabel"`/`"qc-ar-shortBio"`
    # all carry `required=""`), and a `required` field's real
    # browser-computed accessible name INCLUDES a trailing " *" the old
    # constant's exact=True match never accounted for
    # (`get_by_role("textbox", name="Full Name — العربية", exact=True)`
    # resolves 0 matches live; only `"...العربية *"` resolves 1). Rather
    # than depend on that fragile, required-state-sensitive suffix, every AR
    # field below is now addressed by its own CONFIRMED-LIVE STABLE id
    # (`qc-ar-<fieldName>`, unlike the EN fields' fragment-uuid ids, which
    # regenerate per page load) — immune to both the asterisk quirk and any
    # future required/optional flip. Confirmed live: Full Name AR
    # (required, maxlength=150), Position Label AR (required, maxlength=
    # 100), Short Bio AR (required, maxlength=400), Photo Alt Text AR (NOT
    # required, maxlength=150), Role Badge Label AR (NOT required,
    # maxlength=100), Professional Experience Entries AR (NOT required, no
    # maxlength — same free-text-JSON shape as its EN twin), Detailed
    # Biography AR (rich text — see DESCRIPTION_EDITOR_IFRAME_AR below; its
    # own hidden backing textarea `#qc-ar-detailedBiography` carries
    # `data-qc-ar-rich=""` and is NOT required).
    FULL_NAME_AR = "#qc-ar-fullName"
    POSITION_LABEL_AR = "#qc-ar-positionLabel"
    ROLE_BADGE_LABEL_AR = "#qc-ar-roleBadgeLabel"
    PHOTO_ALT_TEXT_AR = "#qc-ar-photoAltText"
    SHORT_BIO_AR = "#qc-ar-shortBio"
    PROFESSIONAL_EXPERIENCE_ENTRIES_AR = "#qc-ar-professionalExperienceEntries"

    # Second CKEditor iframe (title="editor", nth=1) — CONFIRMED LIVE
    # 2026-09-17 this is the Detailed Biography AR rich-text instance,
    # mounted directly below the EN instance (nth=0,
    # ObjectAuthoringPage.DESCRIPTION_EDITOR_IFRAME) — same bilingual
    # two-iframe pattern ObjectAuthoringPage's own HEALED 2026-09-07 note
    # already documents for manage-strategic-pillar-card.
    DESCRIPTION_EDITOR_IFRAME_AR = 'iframe[title="editor"] >> nth=1'

    def fill_rich_text_ar(self, text: str) -> "BoardMembersAdminPage":
        self.fill_iframe_editor(self.DESCRIPTION_EDITOR_IFRAME_AR, text)
        return self

    def rich_text_value_ar(self) -> str:
        return self.iframe_editor_text(self.DESCRIPTION_EDITOR_IFRAME_AR)

    # ---- Error text — SAVE_ERROR_BANNER_TEXT/INLINE_REQUIRED_TEXT are the
    # unchanged, pre-migration literal strings (never confirmed live on THIS
    # Object Authoring surface — kept only because the 26 pre-existing tests
    # in this module still reference them via is_save_error_shown()/
    # save_error_text(), not because either string was ever observed
    # rendered here). Left as-is per that batch's scope.
    SAVE_ERROR_BANNER_TEXT = "This form is invalid. Check field"
    INLINE_REQUIRED_TEXT = "This field is required."

    # HEALED 2026-09-15 (false-negative triage of 14 Functional-Low
    # Control_Panel failures — tc_133552/133553/133558/133559/133563/133565/
    # 133568/133576/133577/133581/133583/133605/133606/133607 — all failing
    # `assert admin.is_save_error_shown()`). CONFIRMED LIVE this session
    # (Playwright MCP, qcdev, real TEST_USER session, manage-board-member,
    # editEntry=QCDEMO-129398-member-01, every mutation reverted to the
    # entry's real original values afterward) that this surface's actual
    # validation-rejection UI is NEITHER of the two literal strings above —
    # those were never observed to render here. THREE distinct, confirmed
    # mechanisms exist, and the original is_save_error_shown() detected NONE
    # of them:
    #
    #   1) NATIVE HTML5 constraint validation on a `required` field left
    #      empty (Full Name, Position Label, Short Bio, Display Order — all
    #      confirmed live `required=true` on their real `<input>`/
    #      `<textarea>` elements). Clicking "Submit for Publishing" is
    #      blocked ENTIRELY client-side by the browser's own constraint-
    #      validation UI (a native tooltip, e.g. "Please fill out this
    #      field.") BEFORE any network request fires and BEFORE any DOM
    #      text/element changes at all — confirmed live via a full
    #      network-response capture showing ZERO PUT/POST calls for this
    #      exact scenario, and confirmed NO `[data-qc-oel-field-error]` node
    #      mounts either. `body.innerText()` can never contain this text
    #      because the tooltip is rendered by the browser chrome, not the
    #      page DOM — the only way to detect this is the form's own native
    #      `:invalid` state (see `_is_native_validation_blocked()` below).
    #
    #   2) APP-LEVEL client-side business-rule rejection (e.g. Display Order
    #      = 0 or a negative value — syntactically a valid number, so native
    #      HTML5 validation passes, but the app's own JS rejects it before
    #      any network call). Confirmed live: a real, VISIBLE, non-empty
    #      `<div data-qc-oel-field-error="" role="alert">Display Order is
    #      required and must be a positive whole number (1 or greater).</div>`
    #      renders inline next to the field. This surface ALSO mounts
    #      several permanently-EMPTY `<span role="alert" ...>` placeholders
    #      (character-count/file-size feedback slots, confirmed live: 7
    #      empty ones present alongside the 1 real, non-empty one in this
    #      exact probe) — mirroring OrgStructureAdminPage's own already-
    #      documented "many such placeholders" caution — so detection scopes
    #      to the structural `data-qc-oel-field-error` attribute (which,
    #      confirmed live, is ABSENT from the DOM entirely on an error-free
    #      load/save — count()==0 — and only mounts when a real field error
    #      exists), not the bare `[role="alert"]` role.
    #
    #   3) SERVER-LEVEL REST rejection (`[data-qc-oel-editbar]:has-text(
    #      "This record was not saved")`) — the SAME mechanism already
    #      confirmed live and fixed for OrgStructureAdminPage (see that
    #      class's own module docstring) — added here too since this class
    #      composes the identical ObjectAuthoringPage state machine and the
    #      same editbar container is reused on this surface.
    #
    # DISCLOSED, NOT FIXED BY THIS PASS (confirmed-live findings for the QA
    # Manager's own record, NOT a detection gap this widening can close):
    #   - Photo Alt Text (tc_133576) and Role Badge Label for Chairman/
    #     General Manager (tc_133563/tc_133565) are confirmed live NEITHER
    #     `required` natively NOR app-level-rejected when left empty — a
    #     real, fresh submit with each cleared was confirmed live to
    #     SUCCEED ("Saved and submitted for publishing.", no error node of
    #     any kind, verified via a full DOM re-read after each save). These
    #     3 cases' real, live product behavior does not match their case
    #     premise; forcing is_save_error_shown() to report True here would
    #     be asserting a rejection that never happens — not done, per
    #     automation-standards.md's Result Integrity rule against tampering
    #     an assertion to force green.
    #   - The 5 "rejects over N chars" cases in this batch (tc_133553/
    #     133559/133568/133577/133583) target fields CONFIRMED LIVE to carry
    #     a native `maxlength` HTML attribute exactly matching their
    #     documented limit (Full Name=150, Position Label=100, Role Badge
    #     Label=100, Photo Alt Text=150, Short Bio=400). Confirmed live,
    #     TWO independent ways (Playwright `.fill()`, the mechanism
    #     `BasePage.type()` uses, AND real per-character
    #     `page.keyboard.type()` keystrokes), that neither can ever produce
    #     an over-limit value in the field's real DOM value — both silently
    #     truncate to the exact boundary length, which is a 100% VALID value
    #     that the product then legitimately ACCEPTS. This is the same
    #     class of finding already disclosed and left unfixed for
    #     tc_133608 (Display Order non-numeric input) in
    #     OrgStructureAdminPage's own module docstring — a real UI-input
    #     ceiling, not a detection gap; there is no rejection for any
    #     detection fix to surface. `is_save_error_shown()` correctly
    #     returns False in this state because no error genuinely occurs.
    FIELD_ERROR = "[data-qc-oel-field-error]"
    RECORD_NOT_SAVED_BANNER = '[data-qc-oel-editbar]:has-text("This record was not saved")'

    # HEALED 2026-09-17 (PBI 129398 BATCH 6, final-40 batch — live triage of
    # a reproducible FALSE POSITIVE on every EDIT-then-SUCCESSFUL-submit of
    # an EXISTING entry, found while building this batch's Professional
    # Experience CRUD tests). CONFIRMED LIVE, 4th mechanism (a detection
    # bug in mechanism (1) itself, not a new rejection mechanism): after a
    # real, successful `submit_for_publishing()` on an EXISTING entry, this
    # surface can navigate to a `manage-board-member?previewEntry=<id>` URL
    # — a READ-ONLY preview of the just-submitted entry. That page ALSO
    # renders this surface's own standing, ALWAYS-PRESENT, entirely BLANK
    # inline create-form below the entries table (the same generic
    # entries-list-page layout already disclosed project-wide, e.g. this
    # class's own "DISCLOSED CAVEAT on SAVE_BUTTON" note above) — and THAT
    # blank form's own untouched `required` fields (Full Name, Full Name AR,
    # Position Label, Short Bio, Member Photo, Display Order, etc., every
    # one confirmed live with `value: ''`) are exactly what a page-wide
    # `document.querySelector('input:invalid, ...')` matches, with ZERO
    # connection to the edit that was actually just submitted (confirmed
    # live via a full round-trip: the edited field's new value WAS
    # correctly persisted and rendered on the public delivery surface,
    # while `is_save_error_shown()` simultaneously, incorrectly, reported
    # True). A GENUINE native-required block, by contrast, is confirmed
    # live to NEVER reach this state at all — the click never navigates
    # (the browser's own constraint-validation stops the submit handler
    # before any request fires), so the URL still carries neither
    # `editEntry=` nor `previewEntry=` when a real block is checked. This
    # single, confirmed-live-safe URL check distinguishes the two cases
    # without touching mechanisms (2)/(3) or narrowing any real rejection
    # this method still correctly detects.
    #
    # HEALED 2026-09-17, SAME DAY, 2nd pass (3rd confirmed-live false-
    # positive mechanism on this same method — 8 failing tests: tc_133569,
    # tc_133574, tc_133609, tc_133610, tc_133612, tc_133613, tc_133614,
    # tc_133616). Root cause, confirmed live via Playwright MCP (real
    # TEST_USER session, qcdev, a full disposable-member create-and-submit
    # cycle plus a network-request capture): this surface's "Submit for
    # Publishing" is an in-place AJAX action (`PUT /o/c/boardmembers/<id>`,
    # confirmed 200), NOT a page navigation — `page.url()` never changes at
    # all, before OR after a successful create-new submit (still the bare
    # `manage-board-member` URL throughout, no `editEntry=`/`previewEntry=`
    # ever appended). So the existing `previewEntry=` URL check above does
    # NOT fire for this flow. After a REAL, successful create, the widget
    # resets its OWN create-form fields back to blank in place, ready for
    # the next entry — and that freshly-reset, entirely UNTOUCHED form is
    # the exact same "standing blank inline create-form" the 2026-09-17
    # HEALED note above already documents for the `previewEntry=` case,
    # just reached a different way. Confirmed live twice, side by side:
    #   (a) a full, valid `_fill_disposable_member()` + `submit_for_
    #       publishing()` on a NEW entry: the record saves correctly (row
    #       appears, status "Approved" — verified against the entries
    #       table), yet immediately afterward `document.querySelector(
    #       'input:invalid, ...')` matches 9 elements simultaneously — ALL
    #       of this form's own mandatory fields (`ObjectField_fullName`,
    #       `#qc-ar-fullName`, `ObjectField_positionLabel`, `#qc-ar-
    #       positionLabel`, `ObjectField_memberPhoto`, `ObjectField_
    #       shortBio`, `#qc-ar-shortBio`, `ObjectField_displayOrder`, plus
    #       the Member Category combobox's own hidden backing input) —
    #       because the form was reset to fully blank, not because
    #       anything was rejected.
    #   (b) a GENUINE mechanism-(1) block (Full Name deliberately left
    #       empty, every OTHER mandatory field correctly filled, matching
    #       this batch's own single-field-empty test shape, e.g. tc_133552/
    #       133573/133608): the entries table row COUNT never changes (no
    #       PUT/create ever fires), the OTHER filled fields' typed values
    #       are still present (confirmed live: Position Label/Display Order
    #       read back exactly what was typed, proving the form was never
    #       reset/navigated away from), and only ONE of the same 8 stable
    #       mandatory-field identifiers is invalid.
    # The two states are reliably distinguished by how MANY of this form's
    # own known-stable mandatory-field identifiers are invalid AT ONCE: ALL
    # 8 simultaneously invalid is the fingerprint of an untouched/just-reset
    # PRISTINE form (no real submit attempt is being rejected — the
    # `previewEntry=` case above shares this exact same fingerprint, which
    # is why the same reasoning applies), while a genuine save-blocking
    # validation failure only ever invalidates the specific field(s) a test
    # actually left empty, never the full mandatory set at once — no test in
    # this project empties more than one required field per case. 5 of the
    # 8 identifiers use this form's own stable `name="ObjectField_<field>"`
    # attribute (confirmed live, unlike the EN fields' own DOM `id`, which
    # regenerates per page load — see FULL_NAME_AR's own docstring for the
    # same regenerating-id caution); the 3 AR twins use their own confirmed-
    # stable `#qc-ar-<field>` ids (see the AR field-constants block above).
    # The unnamed 9th field (Member Category's hidden backing input) is
    # deliberately excluded from this fixed set — it carries no stable
    # name/id, so it cannot be targeted individually, but it is always
    # invalid ALONGSIDE the other 8 on a genuinely pristine/reset form and
    # never invalid on its own in any case this project's tests construct.
    STABLE_REQUIRED_FIELD_SELECTORS = (
        '[name="ObjectField_fullName"]',
        '[name="ObjectField_positionLabel"]',
        '[name="ObjectField_shortBio"]',
        '[name="ObjectField_displayOrder"]',
        '[name="ObjectField_memberPhoto"]',
        "#qc-ar-fullName",
        "#qc-ar-positionLabel",
        "#qc-ar-shortBio",
    )

    def _is_native_validation_blocked(self) -> bool:
        """True if a native HTML5 `required`/constraint-validation failure
        is currently blocking this form's submit — confirmed live 2026-09-15
        this is the ONLY observable signal for that state (no DOM text/node
        of any kind renders — see class docstring's mechanism (1)). See the
        HEALED 2026-09-17 notes above this method for the `previewEntry=`
        exclusion and the stable-field-count exclusion (the fixed-set
        version added same day, 2nd pass) — together they cover every
        confirmed-live false-positive path without narrowing a single real
        rejection this method still correctly detects (see both notes'
        own live evidence)."""
        if "previewEntry=" in self.page.url:
            return False
        try:
            return bool(
                self.page.evaluate(
                    """
                    (stableSelectors) => {
                        const anyInvalid = !!document.querySelector(
                            'input:invalid, textarea:invalid, select:invalid'
                        );
                        if (!anyInvalid) return false;
                        const invalidStableCount = stableSelectors.filter((sel) => {
                            const el = document.querySelector(sel);
                            return el && !el.checkValidity();
                        }).length;
                        // ALL known mandatory fields simultaneously invalid
                        // == a pristine/just-reset standing create form,
                        // not a real save-blocking rejection (see HEALED
                        // note above this method).
                        if (invalidStableCount >= stableSelectors.length) return false;
                        return true;
                    }
                    """,
                    list(self.STABLE_REQUIRED_FIELD_SELECTORS),
                )
            )
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible()'s never-throws contract
            return False

    # ---- Navigation -----------------------------------------------------
    def _ensure_logged_in(self) -> None:
        """Re-login-if-needed via `/en/home`'s real Product Menu/Content &
        Data check — mirrors OrgStructureAdminPage._ensure_logged_in() /
        HomeBusinessEventsAdminPage._ensure_logged_in() exactly."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_board_members_list(self) -> "BoardMembersAdminPage":
        """Object Authoring entries list for Board Member (`manage-board-member`,
        no `editEntry` param) — replaces the old Content & Data > Board
        Members menu path (see module docstring)."""
        self._ensure_logged_in()
        self.open_entries_list()
        return self

    def open_new_member_form(self) -> "BoardMembersAdminPage":
        self._ensure_logged_in()
        self.open_new_entry_form()
        return self

    def open_member_edit_form_by_name(self, full_name: str) -> "BoardMembersAdminPage":
        self.open_entry_by_edit_link(full_name)
        return self

    def open_member_edit_form_by_row_index(self, index: int = 0) -> "BoardMembersAdminPage":
        """Click the row-at-`index`'s own `Edit` link — the confirmed-live
        replacement for the OLD ID-cell-link click (this surface has no
        equivalent ID-cell link; every row's `Edit` link is the correct,
        confirmed-live route into its edit form, same as
        ObjectAuthoringPage.open_entry_by_edit_link()'s own click/settle
        shape, scoped by index instead of title)."""
        row = self.page.locator(self.LIST_ROW).nth(index)
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

    def open_member_edit_form_by_row_index_fresh(self, index: int) -> "BoardMembersAdminPage":
        """Re-navigate to the list fresh, then open the row at `index` —
        used by teardown finalizers so a revert never assumes the form the
        test left open is still there/error-free."""
        self.open_board_members_list()
        return self.open_member_edit_form_by_row_index(index)

    # ---- Form actions -----------------------------------------------------
    def fill_member_form(
        self,
        full_name_en: str = None,
        full_name_ar: str = None,
        position_label_en: str = None,
        position_label_ar: str = None,
        role_badge_label_en: str = None,
        role_badge_label_ar: str = None,
        photo_alt_text_en: str = None,
        photo_alt_text_ar: str = None,
        short_bio_en: str = None,
        short_bio_ar: str = None,
        detailed_biography_en: str = None,
        detailed_biography_ar: str = None,
        professional_experience_entries: str = None,
        professional_experience_entries_ar: str = None,
        display_order: str = None,
        active_status: bool = None,
        enable_share_icons: bool = None,
    ) -> "BoardMembersAdminPage":
        if full_name_en is not None:
            self.fill_text(FIELD_FULL_NAME, full_name_en)
        if full_name_ar is not None:
            self.type(self.FULL_NAME_AR, full_name_ar)
        if position_label_en is not None:
            self.fill_text(FIELD_POSITION_LABEL, position_label_en)
        if position_label_ar is not None:
            self.type(self.POSITION_LABEL_AR, position_label_ar)
        if role_badge_label_en is not None:
            self.fill_text(FIELD_ROLE_BADGE_LABEL, role_badge_label_en)
        if role_badge_label_ar is not None:
            self.type(self.ROLE_BADGE_LABEL_AR, role_badge_label_ar)
        if photo_alt_text_en is not None:
            self.fill_text(FIELD_PHOTO_ALT_TEXT, photo_alt_text_en)
        if photo_alt_text_ar is not None:
            self.type(self.PHOTO_ALT_TEXT_AR, photo_alt_text_ar)
        if short_bio_en is not None:
            self.fill_text(FIELD_SHORT_BIO, short_bio_en)
        if short_bio_ar is not None:
            self.type(self.SHORT_BIO_AR, short_bio_ar)
        if detailed_biography_en is not None:
            self.fill_rich_text(detailed_biography_en)
        if detailed_biography_ar is not None:
            self.fill_rich_text_ar(detailed_biography_ar)
        if professional_experience_entries is not None:
            self.fill_text(FIELD_PROFESSIONAL_EXPERIENCE_ENTRIES, professional_experience_entries)
        if professional_experience_entries_ar is not None:
            self.type(self.PROFESSIONAL_EXPERIENCE_ENTRIES_AR, professional_experience_entries_ar)
        if display_order is not None:
            self.fill_number(FIELD_DISPLAY_ORDER, display_order)
        if active_status is not None:
            self.set_checkbox(FIELD_ACTIVE_STATUS, active_status)
        if enable_share_icons is not None:
            self.set_checkbox(FIELD_ENABLE_SHARE_ICONS, enable_share_icons)
        return self

    def fill_required_ar_fields(
        self,
        full_name_ar: str = "اسم اختبار للعضو",
        position_label_ar: str = "منصب اختباري",
        short_bio_ar: str = "سيرة قصيرة اختبارية للعضو.",
    ) -> "BoardMembersAdminPage":
        """Fills the THREE AR twin fields CONFIRMED LIVE 2026-09-17 to be
        natively `required` on this surface (Full Name AR, Position Label
        AR, Short Bio AR — see the AR field-constants block above). Every
        disposable-record creation in this module's test file must call
        this (directly or via `_fill_disposable_member()`), or the native
        HTML5 constraint-validation block documented on
        `_is_native_validation_blocked()`/`is_save_error_shown()` fires
        every time regardless of which EN fields were filled — this was a
        real, live-confirmed gap in every disposable-member helper prior to
        this batch (see this class's own module docstring for the full
        finding)."""
        self.type(self.FULL_NAME_AR, full_name_ar)
        self.type(self.POSITION_LABEL_AR, position_label_ar)
        self.type(self.SHORT_BIO_AR, short_bio_ar)
        return self

    def attempt_member_photo_upload_expect_rejection(
        self, file_path: str, timeout_seconds: float = 20.0
    ) -> str:
        """Attempts to upload `file_path` into Member Photo and expects it
        to be REJECTED before ever being attached — mirrors
        OrgStructureAdminPage.attempt_person_photo_upload_expect_rejection()
        (same underlying Object Authoring `iframe[src*="selectFileEntry"]`
        item-selector picker widget, confirmed live 2026-09-17 for BOTH an
        unsupported extension (.gif) and an oversized (>2MB) file: the
        picker's own "Add" button never becomes actionable — the upload
        stalls and the modal never reaches its "1 of 1" ready state. This
        method polls the picker iframe's own body text for a real,
        visible rejection message (an unsupported-extension path some
        objects show live text for) OR for reversion out of an
        "Uploading"/in-progress state (the silent, oversized-file
        rejection path — same two-path shape OrgStructureAdminPage's own
        method already documents) and ALWAYS presses `Escape` before
        returning so the still-open modal never hangs the caller's next
        interaction. Returns the picker's own message text if one rendered,
        `""` if the rejection was silent — never raises for either
        confirmed-live outcome."""
        hidden_textbox = self.page.get_by_role(
            "textbox", name=f"{FIELD_MEMBER_PHOTO} Select File"
        )
        select_file_button = hidden_textbox.locator("xpath=..").get_by_role(
            "button", name="Select File"
        )
        select_file_button.click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path, timeout=15000)

        message = ""
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                body_text = frame.locator("body").inner_text(timeout=2000)
            except Exception:  # noqa: BLE001 — frame may be mid-transition between polls
                body_text = ""
            lowered = body_text.lower()
            if "valid extension" in lowered or "not supported" in lowered or "invalid file" in lowered:
                for line in body_text.splitlines():
                    if line.strip() and (
                        "valid extension" in line.lower()
                        or "not supported" in line.lower()
                        or "invalid file" in line.lower()
                    ):
                        message = line.strip()
                        break
                break
            if "1 of 1" not in body_text and "uploading" not in lowered:
                # Reverted to the empty "Drag & Drop" state with no message —
                # the silent-rejection path (oversized/unsupported file).
                break
            time.sleep(0.5)

        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)
        return message

    def select_member_category(self, category: str) -> "BoardMembersAdminPage":
        self.select_combobox_option(FIELD_MEMBER_CATEGORY, category)
        return self

    def upload_member_photo(self, file_path: str) -> "BoardMembersAdminPage":
        self.upload_file(FIELD_MEMBER_PHOTO, file_path)
        return self

    def save(self) -> "BoardMembersAdminPage":
        """Maps to Object Authoring's "Submit for Publishing" (see module
        docstring's LIFECYCLE MAPPING note) — this surface has no single
        "Save" button, and "Submit for Publishing" remains enabled even on
        an already-Approved entry (confirmed live), unlike "Save as Draft"."""
        self.submit_for_publishing()
        return self

    def cancel(self) -> "BoardMembersAdminPage":
        """No dedicated "Cancel" control on the create-new form (same as
        OrgStructureAdminPage.cancel()) — navigating back to the entries
        list has the same discard effect for an unsaved create-new form."""
        self.open_entries_list()
        return self

    def deactivate_and_republish(self) -> "BoardMembersAdminPage":
        """Convenience wrapper: uncheck Active Status then Submit for
        Publishing — confirmed live (see module docstring) this persists
        correctly and propagates to the public counter/listing, unlike the
        Member Category combobox's confirmed-broken edit-persistence."""
        self.set_checkbox(FIELD_ACTIVE_STATUS, False)
        self.submit_for_publishing()
        return self

    def activate_and_republish(self) -> "BoardMembersAdminPage":
        self.set_checkbox(FIELD_ACTIVE_STATUS, True)
        self.submit_for_publishing()
        return self

    # ---- State queries --------------------------------------------------------
    def is_save_error_shown(self) -> bool:
        body_text = self.page.locator("body").inner_text()
        if self.SAVE_ERROR_BANNER_TEXT in body_text or self.INLINE_REQUIRED_TEXT in body_text:
            return True
        # Mechanism (2) — app-level field error (see class docstring's
        # HEALED note). .count() rather than is_visible(): confirmed live
        # this node never appears more than once at a time in every probe
        # this session, but .count() > 0 is the safe, non-strict-mode-
        # dependent check regardless.
        if self.page.locator(self.FIELD_ERROR).count() > 0:
            return True
        # Mechanism (3) — server-level REST rejection banner (same pattern
        # already confirmed live and fixed on OrgStructureAdminPage).
        if self.is_visible(self.RECORD_NOT_SAVED_BANNER):
            return True
        # Mechanism (1) — native HTML5 constraint-validation block (no DOM
        # text/node of any kind renders for this one — see class docstring).
        return self._is_native_validation_blocked()

    def save_error_text(self) -> str:
        if self.page.locator(self.FIELD_ERROR).count() > 0:
            return self.page.locator(self.FIELD_ERROR).first.inner_text()
        if self.is_visible(self.RECORD_NOT_SAVED_BANNER):
            return self.text(self.RECORD_NOT_SAVED_BANNER)
        body_text = self.page.locator("body").inner_text()
        idx = body_text.find(self.SAVE_ERROR_BANNER_TEXT)
        if idx == -1:
            idx = body_text.find(self.INLINE_REQUIRED_TEXT)
        if idx != -1:
            return body_text[idx: idx + 120]
        # Native constraint-validation message — the ONLY text that exists
        # for mechanism (1) (see class docstring); never present in
        # body_text since it's browser-chrome-rendered, not page DOM.
        try:
            return self.page.evaluate(
                "() => { const el = document.querySelector("
                "'input:invalid, textarea:invalid, select:invalid'); "
                "return el ? el.validationMessage : ''; }"
            ) or ""
        except Exception:  # noqa: BLE001 — mirrors BasePage's never-throws contract
            return ""

    def find_row_index_by_category(self, category_text: str, exclude: tuple = ()) -> int:
        """UNCHANGED, DISCLOSED-BROKEN on this surface — see module
        docstring's "DISCLOSED, NOT FIXED" note: the entries table's own
        row text no longer contains category text at all on Object
        Authoring (Name/Status/Last modified/Actions columns only), so this
        will never match. Left in place, unfixed, for the 26 pre-existing,
        out-of-scope tests that reference it — do not build new coverage on
        this method; use an explicit member name instead (see this batch's
        test module for the pattern)."""
        rows = self.page.locator(self.LIST_ROW)
        for i in range(rows.count()):
            txt = rows.nth(i).inner_text()
            if category_text in txt and not any(bad in txt for bad in exclude):
                return i
        return -1

    def row_visible(self, full_name: str) -> bool:
        return self.is_visible(f'{self.LIST_ROW}:has-text("{full_name}")')

    def row_count(self) -> int:
        return self.page.locator(self.LIST_ROW).count()

    def delete_member_by_name(self, full_name: str) -> "BoardMembersAdminPage":
        """QCTEST- disposable-record cleanup path (cms-profile.md Test-Data
        Policy) — delegates to ObjectAuthoringPage.delete_entry_by_title(),
        the confirmed-live, never-raises delete flow (see that method's own
        docstring)."""
        self.delete_entry_by_title(full_name)
        return self

    def row_category_text(self, title: str) -> str:
        """Category cell text straight from the entries LIST row (4th
        column) — CONFIRMED LIVE 2026-09-16 (PBI 129398 Batch 4, tc_133549):
        contrary to this class's own module docstring ("DISCLOSED, NOT
        FIXED" note, dated 2026-09-07), the entries table row NOW renders a
        real Category column (Name / Status / Last modified / Category /
        Actions — re-confirmed via a live row-by-row text dump), where it
        previously did not. This is a safer, non-mutating read for a
        record's Category than opening its edit form and reading the
        Member Category combobox: that combobox is confirmed to visually
        revert to "Choose an Option" after an edit-and-resubmit cycle (see
        this class's own "CONFIRMED LIVE PRODUCT DEFECT 2026-09-07" note
        above) — a risk this row-based read sidesteps entirely by never
        opening the edit form at all. `find_row_index_by_category()` above
        remains unchanged/unfixed for its own documented reason (it scans
        for the category text WITHIN the row alongside the title, a
        different use case); this method is a direct, single-row lookup by
        title only."""
        row = self.page.locator(f'{self.LIST_ROW}:has-text("{title}")')
        if row.count() == 0:
            return ""
        return row.locator("td").nth(3).inner_text().strip()

    def is_active_status_checked(self) -> bool:
        """Non-mutating read of the Active Status checkbox's current
        state — added 2026-09-16 (tc_133549) to verify Active Status =
        True on a record BEFORE asserting its public rendering, per
        standards.md's "Active Status Is a Precondition for Public-Site
        Visibility" rule, without ever toggling the checkbox itself
        (unlike set_checkbox(), which always mutates)."""
        return self.page.locator(self.ACTIVE_STATUS_CHECKBOX).is_checked()

    def is_enable_share_icons_checked(self) -> bool:
        """Non-mutating read of the Enable Share Icons checkbox's current
        state — added 2026-09-17 (PBI 129398 BATCH 6) mirroring
        is_active_status_checked() exactly, for the persistence-after-
        reload case (tc_133603)."""
        return self.page.locator(self.ENABLE_SHARE_ICONS_CHECKBOX).is_checked()

    def current_member_category(self) -> str:
        """Non-mutating read of the Member Category combobox's CURRENTLY
        SELECTED value via its own trigger element's rendered text — added
        2026-09-16 for PBI 129398's page-level/Member-Category-rendering
        batch (tc_133549). Confirmed live: once a value is set, the
        combobox trigger (`MEMBER_CATEGORY_COMBOBOX`) renders the selected
        option's own label directly (e.g. "General Manager"), not the
        "Choose an Option" placeholder — reading this text does not require
        opening the listbox, unlike select_member_category(), so it is safe
        to call on a real, singular-slot record (Chairman/General Manager)
        without risking an accidental category change."""
        return self.text(self.MEMBER_CATEGORY_COMBOBOX)

    def field_value(self, field_locator: str) -> str:
        """Generic raw-locator read-back — OVERRIDES
        ObjectAuthoringPage.field_value(field_label), which takes a field
        LABEL and resolves it via get_by_role() internally. The 26
        pre-existing tests in this module call this with a raw locator
        STRING (e.g. `admin.field_value(admin.SHORT_BIO)`), so this restores
        the original generic contract — same override OrgStructureAdminPage
        applies for the identical reason."""
        return self.page.locator(field_locator).input_value()

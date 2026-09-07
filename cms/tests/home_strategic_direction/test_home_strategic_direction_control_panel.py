"""
cms/tests/home_strategic_direction/test_home_strategic_direction_control_panel.py
— Control_Panel-tagged cases for PBI 129381 ("Strategic Direction Section" /
Pillar Cards, Home Page), scoped to the "Strategic Pillar Cards" Object
Definition (objectDefinitionId=48938, groupId=37246). See
cms/pages/home_strategic_direction/home_strategic_direction_admin_page.py's
module docstring for the full live-verified field/menu/validation inventory
this batch is built on — every locator and confirmed string below traces
back to a real, live, single-process probe run this session (2026-08-31),
NOT to the earlier Playwright-MCP exploration attempt (see that same
docstring for why the MCP attempt's early observations were discarded as
tool-boundary artifacts, not real site behavior).

DISCLOSED SUBSTITUTIONS / DEVIATIONS FROM THE SOURCE CASE TEXT (read before
touching this module):

  CORRECTED 2026-09-07 (per .claude/context/active/standards.md's "Object
  Authoring Is the Only Path for Publish/Unpublish/Draft/Preview Actions"
  and "Draft/Unpublish Public-Visibility Checks — Mandatory Logged-Out
  Context"): TC 135556, TC 135557, and TC 135562 (immediately below) were
  re-verified against Object Authoring (`manage-strategic-pillar-card`,
  `ObjectAuthoringPage`) instead of the raw Content & Data editor
  (`HomeStrategicDirectionAdminPage`), which this file's Batch 2 section
  further down already established is NOT the correct/supported surface for
  lifecycle actions. `HomeStrategicDirectionAdminPage` is still used only to
  establish the authenticated admin session (`open_pillar_cards_list()`)
  before switching to `ObjectAuthoringPage` — its own Save/Cancel-only edit
  form is no longer used for Draft/Preview/Publish/Unpublish on any of these
  three tests.

  1. TC 135556 ("...Save as draft -> Preview the card -> Publish the
     section...") — the notes below (points 1/2 as originally written)
     described the raw Content & Data editor, which is confirmed to have
     ONLY Save/Cancel (no Draft/Preview/Publish pipeline). Object Authoring
     DOES support the case's literal 3-step sequence for a brand-new
     entry — `Save as Draft` -> the entry's own row-level Preview link ->
     `Submit for Publishing` — confirmed live 2026-09-03 (this module's own
     Batch 2 section) and again this pass. This test now drives that REAL
     sequence instead of the earlier Save-only substitution.

  2. TC 135562 ("...Publish is blocked with inline validation error
     'Section Heading (EN) is required.'...") — NO field named "Section
     Heading" exists on EITHER surface (confirmed by a full live field/label
     inventory on the raw editor, and by Object Authoring's own confirmed
     field set — see both Page Objects' docstrings). The real, confirmed
     required EN field on both surfaces is "Pillar Title". Mandatory-field
     ENFORCEMENT/MESSAGING genuinely differs between the two surfaces,
     however (re-verified this pass, see the test's own docstring for the
     detail): the raw Content & Data editor surfaces an explicit custom page
     banner ("This form is invalid. Check field Pillar Title.") plus inline
     "This field is required." text; Object Authoring's Pillar Title control
     is a native-`required` HTML textbox with no equivalent custom banner
     confirmed — this test therefore asserts the BEHAVIOR the case cares
     about (publish is blocked, Mission's persisted title is unchanged), not
     the raw editor's specific banner string, which does not apply to this
     surface.

  3. TC 135557 and TC 135562 both mutate a REAL, shared editorial record
     ("Mission", ID 49082) — cms-profile.md's Test-Data Policy classifies
     this as SNAPSHOT_RESTORE, "prohibited outside an explicit, documented
     exception." This project's own GM Message batch already established
     the in-repo precedent for exactly this situation (a small, fixed,
     non-disposable content type with no dedicated QA-only row available):
     capture the live baseline value(s) before mutating, mutate, assert,
     then restore the baseline in a `finally` block and re-verify the
     restore by re-opening the record fresh. This module follows that same
     precedent as its documented exception, rather than skipping the case
     or inventing a disposable substitute record cms-profile.md's Roles/
     Test-Data sections don't support.

  4. Cache/propagation latency for THIS content type was not independently
     re-measured this session (cms-profile.md's ~0s figure is confirmed
     only for the Board Members JAX-RS data source) — the public-page
     re-checks below poll (reload + re-check) with the same conservative
     default timeout/interval cms-profile.md prescribes as a safety margin,
     never a bare `sleep()`.

Test-data ownership: TC 135556 creates a QCTEST- prefixed disposable record
and deletes it in a fixture teardown (delete_pillar_card_by_title() — see
its own docstring: the kebab->Delete flow was NOT independently exercised
live this session, same disclosed-not-verified status as
BoardMembersAdminPage's equivalent method). TC 135557 and TC 135562 use the
snapshot-restore exception on the real "Mission" record described above.

CONTINUATION (2026-08-31, later this session) — a dropped/interrupted prior
run of this suite against the SAME shared "Mission" record (49082) was
investigated before resuming work. Findings, live-verified:
  - Mission (49082) was CONFIRMED NOT MUTATED. Its Pillar Title ("Mission"),
    Display Order ("200"), and Active Status (True) all read normally, and
    its Pillar Description — independently re-derived from the portlet's
    own embedded field-config JSON (see
    HomeStrategicDirectionAdminPage.pillar_description_text()) — matches
    the live public Home Page's server-rendered Mission card text exactly
    ("To empower Qatar's private sector..."). No dialog was left open
    (confirmed: `[role="dialog"]` present in the DOM but not visible, a
    normal hidden template, not a blocking modal).
  - The earlier appearance of an "empty" description was a READ defect, not
    a data defect: pillar_description_text() previously called
    self.text()/inner_text() on the field's outer `role="textbox"`
    wrapper, which NEVER actually contains the CKEditor's mounted content
    on this form (see next point) — it reads '' whether or not the record
    holds real data. Fixed to read the portlet's own embedded field-config
    JSON instead, which is present in the page HTML regardless of whether
    the editor widget has been clicked to mount yet.

CORRECTED (2026-08-31, later this session still) — the PRIOR conclusion in
this docstring that Pillar Description's CKEditor "never mounts" (a CMS/app
defect) was ITSELF WRONG — a locator bug in our own Page Object, not a
product defect. Live re-investigation found:
  - `PILLAR_DESCRIPTION` (`[role="textbox"][aria-label="Pillar Description"]`)
    is the CKEditor's OUTER, non-editable mount POINT — it stays
    `visibility:hidden`/empty forever, which is exactly why `.type()`
    against it always failed. It was never the editable surface.
  - Clicking that wrapper ONCE forces Liferay to lazily instantiate the
    real classic (iframe-based) CKEditor: a genuine `<iframe title="editor">`
    mounts inside the field's own
    `div.ddm-field[data-field-name="pillarDescription"]` container, and its
    `<body>` IS `isContentEditable === true` — confirmed live via
    `frame_locator(...).locator("body")`, which read back the real
    persisted Mission description and accepted a real keyboard Ctrl+A +
    type write.
  - `HomeStrategicDirectionAdminPage.fill_pillar_card_form()` now clicks the
    wrapper, waits for the iframe, and writes through it (see
    `BasePage.fill_iframe_editor()`). A FULL live cycle was run against the
    real "Mission" record (49082): baseline read -> write via the fixed
    path -> Save -> reopen fresh -> persisted value matched the write ->
    restore to baseline -> Save -> reopen fresh -> persisted value matched
    the baseline exactly. TC 135557's skip is REMOVED — it is no longer
    blocked.
  - `_PILLAR_DESCRIPTION_EDITOR_BLOCKED` and both `@pytest.mark.skip`
    decorators below are removed accordingly.

PRIOR BLOCKER (2026-08-31), NOW RESOLVED (2026-09-01) — a prior session
found `upload_pillar_icon()`'s Documents-and-Media "Select File" picker
modal (`iframe[id*="selectAttachmentEntry_iframe"]`) would upload a new file
into the library but never select/attach it to the (REQUIRED) Pillar Icon
field, leaving Save blocked by "This field is required." and TC 135556
skipped, with genuine uncertainty over whether this was a real product bug
or an automation gap.

A dedicated live, human-interaction investigation (Playwright MCP,
2026-09-01, real qcdev session, real "Add Strategic Pillar Card" form) found
this WAS an automation gap, not a product defect:
  - Clicking directly on an EXISTING library document's row/card (not its
    "Preview" button) DOES select it and close the modal immediately —
    confirmed live: the Pillar Icon field afterward showed the filename plus
    real Download/Delete buttons.
  - For a FRESHLY uploaded file (the actual `upload_pillar_icon()` case),
    the modal renders an upload PREVIEW panel (thumbnail + filename + "N of
    N" counter) with its own small toolbar, which includes an "Add" button
    scoped to that toolbar — CONFIRMED LIVE to be the real confirm control:
    clicking it selects the just-uploaded file into the Pillar Icon field
    and closes the modal (re-verified: field showed "pillar_icon (10).png"
    with Download/Delete controls, the modal iframe detached). The earlier
    session's "no way to select it" conclusion came from reading the
    modal's read-only sidebar metadata for an EXISTING item, never from
    probing this upload-preview toolbar's own controls.
  - `upload_pillar_icon()` is fixed accordingly: it now waits for that
    "Add" button (scoped inside the modal's iframe) after uploading, clicks
    it, and waits for the modal iframe to detach, instead of a plain
    Close-button dismissal that left the field unset.
  - TC 135556's `@pytest.mark.skip` is REMOVED — the create/upload/Save
    path is no longer blocked.
  - `delete_pillar_card_by_title()` remains UNVERIFIED live for the same
    reason as before (disclosed-not-verified, see its own docstring) — this
    fix unblocks TC 135556 reaching Save, but the kebab->Delete teardown
    path itself was not independently re-exercised this session.
  - TC 135562 (empty-Pillar-Title validation) remains independently
    verified passing, unaffected by this fix.
"""

import allure
import pytest

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import (
    HomeStrategicDirectionAdminPage,
)
from web.pages.home_strategic_direction.home_strategic_direction_page import (
    HomeStrategicDirectionPage,
)

QCTEST_TITLE = "QCTEST-Pillar-Card-135556"
QCTEST_DESCRIPTION = (
    "QCTEST disposable pillar card created by automated test TC 135556 — "
    "safe to delete if found stale."
)
PILLAR_ICON_FIXTURE = "web/tests/home_strategic_direction/fixtures/pillar_icon.png"

MISSION_TITLE = "Mission"

# CORRECTED 2026-08-31 (see module docstring's "CORRECTED" section): the
# Pillar Description CKEditor DOES mount — the earlier "never mounts"
# conclusion was a locator bug in our own Page Object (PILLAR_DESCRIPTION
# addressed the CKEditor's outer, permanently-hidden mount wrapper, not its
# real editable iframe body). fill_pillar_card_form() now clicks the
# wrapper, waits for the real `<iframe title="editor">` to mount, and
# writes through BasePage.fill_iframe_editor() — live-verified end to end
# against the real "Mission" record (write -> Save -> reopen -> matches ->
# restore -> Save -> reopen -> matches baseline again). TC 135557 below is
# no longer skipped.
#
# TC 135556's skip is REMOVED (2026-09-01) — see module docstring's
# "PRIOR BLOCKER ... NOW RESOLVED" section: a dedicated live human-
# interaction investigation found the modal's upload-preview toolbar has a
# real "Add" confirm button that selects a freshly uploaded file into the
# Pillar Icon field; upload_pillar_icon() now clicks it. Confirmed NOT a
# product defect.


@allure.label("pbi", "129381")
@allure.label("testcase", "135556")
@allure.title(
    "Verify that a Site Content Editor can create, publish, and see a new pillar card live on the Home Page"
)
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.pbi_129381
@pytest.mark.tc_135556
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_high
@pytest.mark.regression
def test_create_publish_and_verify_new_pillar_card_on_home_page(page, browser):
    # QA-135556 — CORRECTED 2026-09-07 per standards.md's "Object Authoring
    # Is the Only Path for Publish/Unpublish/Draft/Preview Actions": the
    # PRIOR version of this test drove Save (Active Status checked) through
    # `HomeStrategicDirectionAdminPage` (the raw Content & Data editor,
    # confirmed absent any Draft/Preview/Publish pipeline) and substituted
    # "reopen and re-read" for the case's literal "Save as draft -> Preview
    # -> Publish" because that pipeline genuinely does not exist on THAT
    # surface. Re-checked against Object Authoring (`manage-strategic-
    # pillar-card`, confirmed live 2026-09-03 — see this module's own Batch
    # 2 section above): the literal 3-step sequence IS supported there for a
    # brand-new entry — `Save as Draft` -> its own row-level Preview link ->
    # `Submit for Publishing` — so this test now drives the REAL sequence
    # instead of the disclosed substitution.
    #
    # Entry-code note (see ObjectAuthoringPage's own "Entry-code-based
    # lookups" docstring): manage-strategic-pillar-card's Entry column
    # renders an autogenerated externalReferenceCode, never the Pillar
    # Title text — the fixture's own entry code is resolved via the
    # VERIFIED (never positional) find_entry_code_by_field() lookup, per
    # standards.md's "Destructive Operations Against qcdev" rule, same
    # precedent this module's Batch 2 tests (tc_135558 etc.) already
    # established.
    #
    # PUBLIC-PAGE-ANONYMOUS-CONTEXT: the public Home Page check runs in a
    # dedicated, fresh, logged-out browser context (never the CMS admin
    # `page`) so it reflects a real anonymous visitor rather than a
    # still-authenticated CMS session — same pattern as
    # home_featured_event_control_panel.py's TC 135670/135671/135673.
    from core.web.browser import new_context

    admin = HomeStrategicDirectionAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="strategic-pillar-card")
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeStrategicDirectionPage(anon_page)

    entry_code = None
    try:
        # Arrange / Act — Step 1: fill every mandatory field and Save as
        # Draft (the real first step of the literal sequence).
        admin.open_pillar_cards_list()  # establishes the authenticated admin session
        _create_strategic_pillar_card(authoring, QCTEST_TITLE, QCTEST_DESCRIPTION)
        authoring.save_as_draft()

        entry_code = authoring.find_entry_code_by_field("Pillar Title", QCTEST_TITLE)
        assert entry_code, f"could not verify an entry whose Pillar Title reads {QCTEST_TITLE!r}"

        authoring.open_entry_by_code(entry_code)
        assert authoring.current_status() == "Draft", (
            f"fixture card {QCTEST_TITLE!r} does not read Draft status right after Save as Draft"
        )

        # Step 2: Preview the card via its own row-level Preview link — the
        # real, dedicated Preview control this surface exposes (see
        # ObjectAuthoringPage's module docstring). Confirms the PREVIEW
        # banner reads the draft/unpublished wording, i.e. the preview
        # reflects the not-yet-published entry.
        preview_url = authoring.row_preview_url_by_code(entry_code)
        assert preview_url, f"no Preview link found for entry {entry_code!r}"
        preview_text = authoring.preview_banner_text(preview_url)
        assert "PREVIEW" in preview_text and "draft" in preview_text.lower(), (
            f"Preview banner did not read as an unpublished/draft preview: {preview_text!r}"
        )

        # Step 3: Submit for Publishing — the real Publish action.
        authoring.open_entry_by_code(entry_code)
        authoring.submit_for_publishing()

        authoring.open_entry_by_code(entry_code)
        assert authoring.current_status() == "Approved", (
            f"fixture card {QCTEST_TITLE!r} did not reach Approved/Published status after "
            f"Submit for Publishing"
        )
        assert authoring.field_value("Pillar Title") == QCTEST_TITLE

        # Assert: the card is visible in the live public Home Page carousel
        # after a reload (poll, not a bare sleep — see module docstring).
        assert home.reload_until_card_visible(QCTEST_TITLE), (
            f"pillar card {QCTEST_TITLE!r} was published in the admin but never "
            f"appeared in the public Home Page's Strategic Direction carousel"
        )
    finally:
        # Teardown: delete the QCTEST- disposable record via Object
        # Authoring's own verified-by-code delete (never a positional
        # guess — see find_entry_code_by_field()'s docstring).
        authoring.open_entries_list()
        if entry_code:
            authoring.delete_entry_by_code(entry_code)

        # Anon-context cleanup runs LAST, after teardown — same lesson as
        # home_featured_event_control_panel.py's finally blocks: a raw
        # context.close() must never be able to short-circuit the real
        # cleanup.
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 — cleanup must never mask the real result
            pass


@allure.label("pbi", "129381")
@allure.label("testcase", "135557")
@allure.title(
    "Verify that editing an existing published pillar card reflects on the Home Page after cache refresh"
)
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.pbi_129381
@pytest.mark.tc_135557
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.xdist_group("mission_49082")
def test_edit_existing_mission_pillar_card_reflects_on_home_page(page, browser):
    # QA-135557 — CORRECTED 2026-09-07 per standards.md's "Object Authoring
    # Is the Only Path for Publish/Unpublish/Draft/Preview Actions": the
    # edit+publish flow now goes through `manage-strategic-pillar-card`
    # (ObjectAuthoringPage), never the raw Content & Data editor. Mission's
    # own entry code is resolved via the VERIFIED (never positional)
    # find_entry_code_by_field() lookup (its Entry column shows a UUID, not
    # the Pillar Title — see ObjectAuthoringPage's own docstring), same
    # precedent already established for the Batch 2 tests below.
    #
    # Mission is Approved/Published already — CONFIRMED LIVE (see
    # ObjectAuthoringPage's module docstring): an Approved entry's own
    # `Submit for Publishing` button is NOT disabled (only `Save as Draft`
    # is, until Unpublish is clicked), so editing an already-published
    # record's field and clicking `Submit for Publishing` directly IS the
    # correct, real "edit the live record and republish" action here — no
    # Unpublish step needed for this case.
    #
    # SNAPSHOT_RESTORE exception (see module docstring #3): baseline is
    # captured before mutating and restored in `finally`, re-verified by a
    # fresh re-open.
    #
    # PUBLIC-PAGE-ANONYMOUS-CONTEXT: the public Home Page check runs in a
    # dedicated, fresh, logged-out browser context (never the CMS admin
    # `page`) so it reflects a real anonymous visitor rather than a
    # still-authenticated CMS session — same pattern as
    # home_featured_event_control_panel.py's TC 135670/135671/135673.
    from core.web.browser import new_context

    admin = HomeStrategicDirectionAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="strategic-pillar-card")
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeStrategicDirectionPage(anon_page)

    admin.open_pillar_cards_list()  # establishes the authenticated admin session
    mission_code = authoring.find_entry_code_by_field("Pillar Title", MISSION_TITLE)
    assert mission_code, f"could not verify an entry whose Pillar Title reads {MISSION_TITLE!r}"

    authoring.open_entry_by_code(mission_code)
    baseline_status = authoring.current_status()  # "Approved" (baseline)
    baseline_description = authoring.rich_text_value()
    updated_description = (
        "QCTEST-135557 temporary Mission description — automated edit-and-restore "
        "regression check, will be reverted by test teardown."
    )

    try:
        # Act
        authoring.fill_rich_text(updated_description)
        authoring.submit_for_publishing()

        # Assert: admin reload shows the new description, still Approved.
        authoring.open_entry_by_code(mission_code)
        assert authoring.current_status() == "Approved"
        assert authoring.rich_text_value() == updated_description

        # Assert: the public Home Page carousel reflects it after a
        # reload/poll (cache-refresh substitute — see module docstring #4).
        assert home.reload_until_card_description_matches(MISSION_TITLE, updated_description), (
            "Home Page's Mission pillar card description did not update to "
            "the edited value after reload/poll"
        )
    finally:
        # Restore the real, shared "Mission" record to its baseline —
        # SNAPSHOT_RESTORE exception, same precedent as this project's GM
        # Message batch.
        restored = False
        last_description = last_status = None
        for _ in range(3):
            authoring.open_entry_by_code(mission_code)
            current = authoring.rich_text_value()
            if current != baseline_description:
                authoring.fill_rich_text(baseline_description)
            if baseline_status == "Approved":
                authoring.submit_for_publishing()
            else:
                authoring.save_as_draft()
            authoring.open_entry_by_code(mission_code)
            last_description = authoring.rich_text_value()
            last_status = authoring.current_status()
            if last_description == baseline_description and last_status == baseline_status:
                restored = True
                break
        assert restored, (
            "teardown failed to restore Mission's description/status to its "
            f"captured baseline via Object Authoring — real editorial content "
            f"may be left mutated: got description={last_description!r} "
            f"status={last_status!r}, expected description="
            f"{baseline_description!r} status={baseline_status!r}"
        )

        # Anon-context cleanup runs LAST, after the baseline restore — same
        # lesson as home_featured_event_control_panel.py's finally blocks.
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 — cleanup must never mask the real result
            pass


@allure.label("pbi", "129381")
@allure.label("testcase", "135562")
@allure.title("Verify that publishing is blocked when a mandatory field is left empty")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.pbi_129381
@pytest.mark.tc_135562
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.xdist_group("mission_49082")
def test_publish_blocked_when_pillar_title_left_empty(page):
    # QA-135562 — CORRECTED 2026-09-07 per standards.md's "Object Authoring
    # Is the Only Path for Publish/Unpublish/Draft/Preview Actions": the
    # PRIOR version cleared Pillar Title and clicked the raw Content & Data
    # editor's Save button. Re-verified via Object Authoring
    # (`manage-strategic-pillar-card`): clear the required EN title field ->
    # click `Submit for Publishing` (this surface's real publish/persist
    # action) -> assert publishing is BLOCKED, and the record's persisted
    # value is unchanged. Disclosed substitution #2 still applies (no field
    # named "Section Heading" exists on either surface — the real required
    # EN field is "Pillar Title").
    #
    # Mandatory-field enforcement DIFFERS between the two surfaces
    # (discrepancy flagged per this task's own instruction): the raw
    # Content & Data editor surfaces an explicit page banner ("This form is
    # invalid. Check field Pillar Title.") plus inline "This field is
    # required." text. Object Authoring's `fill_text()` targets a
    # `role="textbox"` HTML5 form control that is native-`required` —
    # clicking `Submit for Publishing` with it empty is expected to trigger
    # the BROWSER'S OWN native constraint-validation UI (a native bubble,
    # not a page-rendered banner) and/or simply refuse to navigate away from
    # the form, rather than reproducing the raw editor's own custom banner
    # text verbatim. This test therefore asserts the BEHAVIOR the case
    # actually cares about — publishing is blocked and Mission's persisted
    # Pillar Title is unchanged — rather than asserting the raw editor's
    # specific banner string, which does not apply to this surface.
    #
    # SNAPSHOT_RESTORE exception on the real "Mission" record (module
    # docstring #3); restored defensively in `finally` regardless of
    # outcome, per the case's own instruction.
    admin = HomeStrategicDirectionAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="strategic-pillar-card")

    admin.open_pillar_cards_list()  # establishes the authenticated admin session
    mission_code = authoring.find_entry_code_by_field("Pillar Title", MISSION_TITLE)
    assert mission_code, f"could not verify an entry whose Pillar Title reads {MISSION_TITLE!r}"

    authoring.open_entry_by_code(mission_code)
    baseline_title = authoring.field_value("Pillar Title")
    baseline_status = authoring.current_status()  # "Approved" (baseline)

    try:
        # Act
        authoring.fill_text("Pillar Title", "")
        authoring.submit_for_publishing()

        # Assert: publishing is blocked — the record must NOT have been
        # persisted with an empty Pillar Title. Reopen fresh (never trust
        # the in-page state right after the blocked action) and confirm the
        # title is still the baseline, not empty.
        authoring.open_entry_by_code(mission_code)
        reloaded_title = authoring.field_value("Pillar Title")
        assert reloaded_title == baseline_title, (
            "Mission's Pillar Title was persisted as empty (or something "
            f"other than the baseline) after Submit for Publishing with the "
            f"required field cleared: got {reloaded_title!r}, expected "
            f"{baseline_title!r} — publishing was NOT actually blocked "
            f"server-side via Object Authoring"
        )
        assert authoring.current_status() == baseline_status, (
            "Mission's Status changed despite the blocked publish attempt"
        )
    finally:
        # Defensive restore regardless of outcome, per the case's own
        # instruction — the field is client-side cleared during Act and
        # should never have persisted, but restore explicitly rather than
        # trust that.
        restored = False
        last_title = last_status = None
        for _ in range(3):
            authoring.open_entry_by_code(mission_code)
            current = authoring.field_value("Pillar Title")
            if current != baseline_title:
                authoring.fill_text("Pillar Title", baseline_title)
            if baseline_status == "Approved":
                authoring.submit_for_publishing()
            else:
                authoring.save_as_draft()
            authoring.open_entry_by_code(mission_code)
            last_title = authoring.field_value("Pillar Title")
            last_status = authoring.current_status()
            if last_title == baseline_title and last_status == baseline_status:
                restored = True
                break
        assert restored, (
            "teardown failed to restore Mission's Pillar Title/Status to its "
            f"captured baseline via Object Authoring — real editorial content "
            f"may be left mutated: got title={last_title!r} status={last_status!r}, "
            f"expected title={baseline_title!r} status={baseline_status!r}"
        )


# =============================================================================
# BATCH 2 (2026-09-03) — TC 135558/135559/135560/135561/135563, same PBI 129381
# ("Strategic Direction Section" / Pillar Cards, Home Page).
#
# SURFACE CHANGE FROM THE BATCH ABOVE: the 135556/135557/135562 batch above
# drives `HomeStrategicDirectionAdminPage`, the raw Object Definitions editor
# — confirmed (2026-08-31) to expose Save/Cancel only, no Draft/Preview/
# Publish/Unpublish pipeline. Since then, `.claude/context/active/
# standards.md`'s "Object Authoring — Draft / Preview / Publish / Unpublish
# Lifecycle" section (confirmed live 2026-09-03) mandates that any case
# exercising draft/preview/publish/unpublish drive it through the
# `object-authoring` -> `manage-<slug>` surface instead. This batch's own
# live probe (2026-09-03, one-process Python script via this repo's own
# CmsLoginPage + ObjectAuthoringPage, real qcdev session) CONFIRMED that
# surface exists for THIS object too:
#   - object-authoring's own list page shows an entry "Strategic Pillar
#     Card" linking to `manage-strategic-pillar-card`.
#   - `manage-strategic-pillar-card` list: same 3 real rows as the raw
#     editor (QCDEMO-129381-STRATEGIC_PILLAR_CARD-01/-02/-03 = Vision/
#     Mission/Objectives), all status APPROVED — confirmed by live
#     `table tbody tr` read.
#   - Create-new form (`manage-strategic-pillar-card`, no editEntry) has
#     `Save as Draft` / `Submit for Publishing` (both present, confirmed by
#     role-count), fields: `Pillar Title` (textbox), `Pillar Description`
#     (CKEditor — confirmed live via a real write+read-back round trip that,
#     UNLIKE the raw editor's equivalent field, this surface's
#     `iframe[title="editor"]` is already mounted and directly fillable via
#     `BasePage.fill_iframe_editor()`, no prior click needed — see
#     ObjectAuthoringPage.fill_rich_text()/rich_text_value()), `Display
#     Order` (spinbutton), `Active Status` (checkbox), `Pillar Icon`
#     (upload). No separate "Strategic Direction Section" (heading/intro)
#     Object exists — confirmed by grepping the object-authoring list body
#     for "direction" (only "Strategic Pillar Card"/"Strategic Partner"
#     matched) — so per this batch, "the Strategic Direction section" in
#     each case's step text is this object's own entries (a pillar card),
#     the same granularity TC 135556/135557 above already use.
#
# LIVE RUN RESULT (2026-09-03, xdist -n 3 against qcdev): tc_135558/135559/
# 135560's own test BODIES completed with no assertion failure; each hit a
# 20s timeout in its own `finally` teardown's `open_new_entry_form()`
# re-navigation instead — most likely 3-worker contention against the same
# live admin session (this project's own known constraint against running
# parallel live-browser sessions on qcdev), not a locator defect, since the
# identical navigation had already succeeded earlier in the same test.
# Re-verify teardown in isolation (single worker) before trusting it not to
# leave orphaned QCTEST- entries. tc_135561 failed exactly as designed (see
# its own docstring below). tc_135563 failed with a genuine open finding:
# the row left behind after "abandoning" the unsaved form read an
# APPROVED status with a UUID-looking Entry code rather than the fixture's
# own Pillar Title text — flagged for follow-up, NOT silently patched
# around, since it's unclear yet whether this is (a) fill_text() not
# targeting the field the "Entry" column actually renders, or (b)
# upload_file() on this surface having a real implicit-save side effect.
#
# DISCLOSED SUBSTITUTIONS this batch (read before touching these 5 tests):
#
#   TC 135558 (delete a pillar card removes it from the Home Page) — the
#   case names the real "Objectives" card. Deleting it is unrecoverable
#   (ObjectAuthoringPage's own confirmed-live Delete dialog: "This cannot be
#   undone — Object entries do not go to the recycle bin.") and this
#   project's own VMO batch already classifies destructive delete of real
#   shared content as skip-regardless. This test instead creates a
#   TRANSIENT QCTEST- pillar card (same disposable-fixture precedent TC
#   135556 above already establishes in this exact module), confirms it
#   renders in the public carousel alongside the 3 real cards, deletes it,
#   and asserts the carousel afterward shows exactly the original 3 real
#   titles (Vision/Mission/Objectives) and NOT the deleted QCTEST title —
#   preserving the case's real assertion (delete removes a card from the
#   Home Page) with zero risk to real editorial content. This is
#   distinguished from home_strategic_direction_page.py's own rejection of
#   a *permanent* dedicated test record (VERDICT note in that Page Object's
#   docstring) — that note is about a record left live forever; this one is
#   deleted before the test ends.
#
#   TC 135559 (unpublishing removes it from the Home Page) — same
#   transient-QCTEST pattern: create, Submit for Publishing (Approved),
#   confirm live, then Unpublish via `ObjectAuthoringPage.
#   unpublish_to_edit_as_draft()`, confirm it disappears from the public
#   carousel. Preferred over unpublishing one of the 3 real cards for the
#   same real-content-risk reason as 135558.
#
#   TC 135560 (Save as Draft does not expose changes publicly) — the case's
#   literal steps ("edit the section heading... Save as Draft") assume an
#   EXISTING published record can be re-saved as a draft. Confirmed live
#   (standards.md's Object Authoring section, step 3): an Approved entry's
#   `Save as Draft` button is DISABLED ("unavailable until you unpublish
#   it") — there is no way to re-draft a published entry without first
#   unpublishing it, which itself would remove it from the Home Page (a
#   different action than what this case tests). The case's real intent —
#   draft content is never exposed to public visitors — is instead verified
#   against a BRAND-NEW entry: create it, `save_as_draft()` only (never
#   Submit for Publishing), assert its own status reads "Draft", then load
#   the public Home Page fresh (no admin session assumptions) and assert
#   the new card never renders there at all.
#
#   TC 135561 (Submit for Review does not publish until approved) — the
#   case assumes a review/approval GATE between "submitted" and "published"
#   (an intermediate "Pending Review" status). The confirmed-live state
#   machine (standards.md) has exactly two statuses, Draft and Approved,
#   and exactly one forward action, `Submit for Publishing` — CONFIRMED
#   this batch to move a Draft entry straight to Approved with no
#   intermediate/pending state to observe (no "Pending Review" text found
#   anywhere in the confirmed-live inventory). This is flagged as a
#   case-vs-product discrepancy, the same register as TC 135562's "Section
#   Heading" finding above — the test below asserts the case's own real
#   expectation (public Home Page must NOT show the change immediately
#   after the submit action, before any separate approval step) rather than
#   being softened to match the product's actual immediate-publish
#   behavior. Run live, this is expected to demonstrate the discrepancy
#   directly (the card appears immediately), which is the point: it
#   surfaces the mismatch for triage rather than silently asserting around
#   it.
#
#   TC 135563 (Cancel discards entered data) — the create-new form
#   (`manage-strategic-pillar-card`, no editEntry) has no Cancel button
#   (confirmed-live inventory: only Save as Draft / Submit for Publishing on
#   a fresh create form; "Cancel and add a new entry instead" only renders
#   when editing an ALREADY-APPROVED entry, per standards.md step 3 — not
#   applicable to a brand-new, never-saved entry). "Close the form without
#   saving" is substituted with navigating away from the unsaved create
#   form (reloading `manage-strategic-pillar-card` fresh) without clicking
#   either save action — the real-world equivalent of a user abandoning an
#   unsaved form. Asserts the list's row COUNT and titles are byte-for-byte
#   unchanged before/after (not just the new title's absence), matching the
#   case's own "the previous card list is unchanged" expected result.
#
# Test-data ownership: all 5 tests create their own `QCTEST-` prefixed
# disposable entries via `ObjectAuthoringPage(page, "strategic-pillar-card")`
# and delete them in a `finally` block — none of them mutate the real
# Vision/Mission/Objectives rows.
# =============================================================================


def _create_strategic_pillar_card(authoring: ObjectAuthoringPage, title: str, description: str) -> None:
    """Shared fill sequence for a new Strategic Pillar Card entry on the
    object-authoring surface — does NOT save; caller picks save_as_draft()
    or submit_for_publishing()."""
    authoring.open_new_entry_form()
    authoring.fill_text("Pillar Title", title)
    authoring.fill_rich_text(description)
    authoring.fill_number("Display Order", "998")
    authoring.set_checkbox("Active Status", True)
    authoring.upload_file("Pillar Icon", PILLAR_ICON_FIXTURE)


@allure.label("pbi", "129381")
@allure.label("testcase", "135558")
@allure.title("Verify that deleting a pillar card removes it from the Home Page")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.pbi_129381
@pytest.mark.tc_135558
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_high
@pytest.mark.regression
def test_deleting_a_pillar_card_removes_it_from_the_home_page(page):
    # TC 135558 — Log in as Site Content Editor and open a pillar card ->
    # Delete and confirm -> refresh/reload the Home Page, navigate the
    # carousel fully -> assert the deleted card never appears while the
    # real Vision/Mission/Objectives cards still do. See module docstring's
    # disclosed substitution: a transient QCTEST- card stands in for the
    # case's real "Objectives" card, never the real record.
    admin = HomeStrategicDirectionAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="strategic-pillar-card")
    home = HomeStrategicDirectionPage(page)
    title = "QCTEST-135558-Delete-Pillar-Card"

    entry_code = None
    try:
        admin.open_pillar_cards_list()  # establishes the authenticated admin session
        _create_strategic_pillar_card(authoring, title, "QCTEST-135558 disposable pillar card.")
        authoring.submit_for_publishing()
        # See ObjectAuthoringPage's "Entry-code-based lookups" note: this
        # object's own Entry column renders an autogenerated
        # externalReferenceCode, never the Pillar Title text. Per
        # standards.md's "Destructive Operations Against qcdev" rule
        # (added after a real incident), the code backing a delete must be
        # VERIFIED by reading the real Pillar Title back off each row's own
        # edit form — never assumed by row position (newest_entry_code()
        # is diagnostic-only and must never back a delete/edit target).
        entry_code = authoring.find_entry_code_by_field("Pillar Title", title)
        assert entry_code, f"could not verify an entry whose Pillar Title reads {title!r}"

        assert home.reload_until_card_visible(title), (
            f"fixture card {title!r} never appeared in the public carousel after publishing"
        )

        authoring.open_entries_list()
        deleted = authoring.delete_entry_by_code(entry_code)
        assert deleted, f"delete_entry_by_code({entry_code!r}) found no row to delete"

        home.open_home()
        home.wait_for_carousel()
        assert not home.is_card_visible(title), (
            f"deleted card {title!r} still renders in the public carousel after deletion"
        )
        for real_title in ("Vision", "Mission", "Objectives"):
            assert home.is_card_visible(real_title), (
                f"real pillar card {real_title!r} missing from the carousel after an "
                f"unrelated card's deletion — deletion may have affected more than the "
                f"targeted row"
            )
    finally:
        authoring.open_entries_list()
        if entry_code:
            authoring.delete_entry_by_code(entry_code)


@allure.label("pbi", "129381")
@allure.label("testcase", "135559")
@allure.title("Verify that unpublishing the Strategic Direction section removes it from the Home Page")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.pbi_129381
@pytest.mark.tc_135559
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_high
@pytest.mark.regression
def test_unpublishing_strategic_direction_section_removes_it_from_home_page(page):
    # TC 135559 — Open the section (Published status) -> Unpublish -> status
    # becomes Unpublished with a success toast -> refresh/reload the Home
    # Page -> assert the section no longer renders. See module docstring's
    # disclosed substitution: a transient QCTEST- card stands in for "the
    # section", published then unpublished, never a real Vision/Mission/
    # Objectives row.
    admin = HomeStrategicDirectionAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="strategic-pillar-card")
    home = HomeStrategicDirectionPage(page)
    title = "QCTEST-135559-Unpublish-Section"

    entry_code = None
    try:
        admin.open_pillar_cards_list()
        _create_strategic_pillar_card(authoring, title, "QCTEST-135559 disposable pillar card.")
        authoring.submit_for_publishing()
        # Verified (not positional) lookup — see TC 135558's own note above
        # and standards.md's "Destructive Operations Against qcdev" rule.
        entry_code = authoring.find_entry_code_by_field("Pillar Title", title)
        assert entry_code, f"could not verify an entry whose Pillar Title reads {title!r}"

        assert authoring.row_status_text_by_code(entry_code) == "Approved", (
            f"fixture card {title!r} did not reach Approved/Published status after "
            f"Submit for Publishing"
        )

        assert home.reload_until_card_visible(title), (
            f"fixture card {title!r} never appeared in the public carousel while Approved"
        )

        authoring.open_entry_by_code(entry_code)
        authoring.unpublish_to_edit_as_draft()
        assert authoring.row_status_text_by_code(entry_code) != "Approved", (
            f"fixture card {title!r} still reads Approved/Published after Unpublish"
        )

        home.open_home()
        home.wait_for_carousel()
        assert not home.is_card_visible(title), (
            f"unpublished card {title!r} still renders in the public carousel "
            f"after Unpublish + reload"
        )
    finally:
        authoring.open_entries_list()
        if entry_code:
            authoring.delete_entry_by_code(entry_code)


@allure.label("pbi", "129381")
@allure.label("testcase", "135560")
@allure.title("Verify that saving as draft does not expose changes to public visitors")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.pbi_129381
@pytest.mark.tc_135560
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_high
@pytest.mark.regression
def test_saving_as_draft_does_not_expose_changes_to_public_visitors(page):
    # TC 135560 — Edit made -> Save as Draft (do not publish) -> success
    # toast shown -> load the Home Page as a public visitor -> assert the
    # draft change is not publicly visible. See module docstring's disclosed
    # substitution: since an already-Approved entry's Save as Draft is
    # confirmed-live DISABLED, this exercises a brand-new entry saved as
    # Draft only (never Submit for Publishing) instead of re-drafting an
    # existing published record.
    admin = HomeStrategicDirectionAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="strategic-pillar-card")
    home = HomeStrategicDirectionPage(page)
    title = "QCTEST-135560-Draft-Not-Public"

    entry_code = None
    try:
        admin.open_pillar_cards_list()
        _create_strategic_pillar_card(authoring, title, "QCTEST-135560 draft-only pillar card.")
        authoring.save_as_draft()
        # Verified (not positional) lookup — see TC 135558's own note above
        # and standards.md's "Destructive Operations Against qcdev" rule.
        entry_code = authoring.find_entry_code_by_field("Pillar Title", title)
        assert entry_code, f"could not verify an entry whose Pillar Title reads {title!r}"

        assert authoring.row_status_text_by_code(entry_code) == "Draft", (
            f"fixture card {title!r} does not read Draft status right after Save as Draft"
        )

        home.open_home()
        home.wait_for_carousel()
        assert not home.is_card_visible(title), (
            f"draft-only card {title!r} is visible on the public Home Page before "
            f"ever being published — draft content is being exposed publicly"
        )
    finally:
        authoring.open_entries_list()
        if entry_code:
            authoring.delete_entry_by_code(entry_code)


@allure.label("pbi", "129381")
@allure.label("testcase", "135561")
@allure.title("Verify that submitting for review does not publish until approved")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.pbi_129381
@pytest.mark.tc_135561
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_high
@pytest.mark.regression
def test_submitting_for_review_does_not_publish_until_approved(page):
    # TC 135561 — Change made -> "Submit for Review" -> status becomes
    # Pending Review with a success toast -> load the Home Page as a public
    # visitor before any approval action -> assert the last-published
    # (pre-change) content is still shown, not the pending change.
    #
    # See module docstring's disclosed substitution/discrepancy note: the
    # confirmed-live surface's only forward action is "Submit for
    # Publishing", and it moves a Draft entry straight to Approved with no
    # observed intermediate Pending-Review gate. This test asserts the
    # case's OWN real expectation (not publicly visible immediately after
    # the submit action) rather than being softened to the product's
    # confirmed immediate-publish behavior — if it fails live, that failure
    # itself is the case-vs-product discrepancy this docstring discloses,
    # not a locator bug.
    admin = HomeStrategicDirectionAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="strategic-pillar-card")
    home = HomeStrategicDirectionPage(page)
    title = "QCTEST-135561-Submit-For-Review"

    entry_code = None
    try:
        admin.open_pillar_cards_list()
        _create_strategic_pillar_card(authoring, title, "QCTEST-135561 disposable pillar card.")
        authoring.submit_for_publishing()
        # Verified (not positional) lookup — see TC 135558's own note above
        # and standards.md's "Destructive Operations Against qcdev" rule.
        entry_code = authoring.find_entry_code_by_field("Pillar Title", title)

        home.open_home()
        home.wait_for_carousel()
        assert not home.is_card_visible(title), (
            f"card {title!r} is already visible on the public Home Page immediately "
            f"after Submit for Publishing/Review, before any separate approval step — "
            f"see this module's TC 135561 docstring note: the confirmed-live surface "
            f"has no Pending-Review gate distinct from this case's expectation"
        )
    finally:
        authoring.open_entries_list()
        if entry_code:
            authoring.delete_entry_by_code(entry_code)


@allure.label("pbi", "129381")
@allure.label("testcase", "135563")
@allure.title("Verify that canceling the Add Pillar Card form discards entered data")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129381
@pytest.mark.tc_135563
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_high
@pytest.mark.regression
def test_canceling_add_pillar_card_form_discards_entered_data(page):
    # TC 135563 — Click Add Pillar Card and fill all fields with valid data
    # -> Cancel/close the form without saving -> check the pillar card list
    # -> assert no new pillar card was created and the previous card list is
    # unchanged. See module docstring's disclosed substitution: this create
    # form has no Cancel button (confirmed-live inventory) — closing without
    # saving is exercised by navigating away from the unsaved form instead
    # of clicking Save as Draft/Submit for Publishing.
    admin = HomeStrategicDirectionAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="strategic-pillar-card")
    title = "QCTEST-135563-Cancelled-Card"

    admin.open_pillar_cards_list()
    authoring.open_new_entry_form()
    rows_before = authoring.page.locator(authoring.ENTRIES_TABLE_ROW).all_inner_texts()

    try:
        _create_strategic_pillar_card(authoring, title, "QCTEST-135563 data that must never be saved.")
        # Act: abandon the unsaved form by navigating away instead of saving.
        authoring.open_new_entry_form()

        rows_after = authoring.page.locator(authoring.ENTRIES_TABLE_ROW).all_inner_texts()

        assert not authoring.row_visible(title), (
            f"card {title!r} was created despite the form being abandoned without a save action"
        )
        assert rows_after == rows_before, (
            "the pillar card list changed after abandoning an unsaved Add form — "
            f"before={rows_before!r} after={rows_after!r}"
        )
    finally:
        # Safety net: if the fill/upload sequence turned out to create a
        # real row despite never clicking Save as Draft/Submit for
        # Publishing (see this module's LIVE RUN RESULT note — an open
        # question this batch flags, not silently assumed away), clean it
        # up by a VERIFIED match on this test's own known title — never by
        # row position (see standards.md's "Destructive Operations Against
        # qcdev" rule and newest_entry_code()'s own docstring for why: a
        # positional guess here already caused a real incident once).
        authoring.open_entries_list()
        rows_now = authoring.page.locator(authoring.ENTRIES_TABLE_ROW).all_inner_texts()
        if len(rows_now) > len(rows_before):
            stray_code = authoring.find_entry_code_by_field("Pillar Title", title)
            if stray_code:
                authoring.delete_entry_by_code(stray_code)

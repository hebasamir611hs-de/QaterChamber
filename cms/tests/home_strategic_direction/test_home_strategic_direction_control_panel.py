"""
web/tests/home_strategic_direction/test_home_strategic_direction_control_panel.py
— Control_Panel-tagged cases for PBI 129381 ("Strategic Direction Section" /
Pillar Cards, Home Page), scoped to the "Strategic Pillar Cards" Object
Definition (objectDefinitionId=48938, groupId=37246). See
web/pages/home_strategic_direction/home_strategic_direction_admin_page.py's
module docstring for the full live-verified field/menu/validation inventory
this batch is built on — every locator and confirmed string below traces
back to a real, live, single-process probe run this session (2026-08-31),
NOT to the earlier Playwright-MCP exploration attempt (see that same
docstring for why the MCP attempt's early observations were discarded as
tool-boundary artifacts, not real site behavior).

DISCLOSED SUBSTITUTIONS / DEVIATIONS FROM THE SOURCE CASE TEXT (read before
touching this module):

  1. TC 135556 ("...Save as draft -> Preview the card -> Publish the
     section...") — confirmed live, this Object Definition entry editor has
     ONLY Save/Cancel; there is no Draft/Preview/Publish pipeline, no
     `publicationStatus` combobox (same scope note as
     gm_message_admin_page.py's own confirmed-absent Preview/Publish
     controls). The 3-step lifecycle collapses to: Save (with Active Status
     checked) -> reload the record to confirm the write -> load the live
     Home Page and confirm the card renders in the public carousel. This is
     the SAME class of disclosed substitution already established in this
     project's GM Message batch, not an invented workaround.

  2. TC 135562 ("...Publish is blocked with inline validation error
     'Section Heading (EN) is required.'...") — NO field named "Section
     Heading" exists on this form (confirmed by a full live field/label
     inventory — see the admin Page Object's docstring). The real,
     confirmed-live required EN field the case is almost certainly
     describing is "Pillar Title", and the real confirmed-live validation
     strings are "This form is invalid. Check field Pillar Title." (page
     banner) and "This field is required." (inline). This test clears and
     asserts on the REAL field ("Pillar Title") and the REAL strings, not
     the case's paraphrase — flagging the discrepancy here rather than
     silently coding to text that does not exist on the live form.

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
def test_create_publish_and_verify_new_pillar_card_on_home_page(page):
    # QA-135556 — Log in as Site Content Editor (this project's only
    # provisioned account, TEST_USER, is mapped to "Administrator/general
    # authoring" per cms-profile.md's Roles table — its exact role mapping
    # is unconfirmed, so this is a disclosed assumption, not a confirmed
    # Site Content Editor login) -> Add Pillar Card -> fill all mandatory
    # fields with valid data -> Save (see module docstring's disclosed
    # substitution #1 for why this stands in for "Save as draft -> Preview
    # -> Publish") -> refresh/reload the Home Page -> assert the new pillar
    # card is visible in the live carousel.
    admin = HomeStrategicDirectionAdminPage(page)
    home = HomeStrategicDirectionPage(page)

    try:
        # Arrange / Act
        admin.open_pillar_cards_list()
        admin.open_new_pillar_card_form()
        admin.fill_pillar_card_form(
            pillar_title=QCTEST_TITLE,
            pillar_description=QCTEST_DESCRIPTION,
            display_order="999",
            active_status=True,
        )
        admin.upload_pillar_icon(PILLAR_ICON_FIXTURE)
        admin.save()

        # Assert: the write was not blocked and the record now shows the
        # entered values on reload (the "Preview" substitute).
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error after saving a fully-filled new "
            f"pillar card: {admin.save_error_text()!r}"
        )
        admin.reopen_pillar_card_by_title_fresh(QCTEST_TITLE)
        assert admin.pillar_title_value() == QCTEST_TITLE

        # Assert: the card is visible in the live public Home Page carousel
        # after a reload (poll, not a bare sleep — see module docstring).
        assert home.reload_until_card_visible(QCTEST_TITLE), (
            f"pillar card {QCTEST_TITLE!r} was saved in the admin but never "
            f"appeared in the public Home Page's Strategic Direction carousel"
        )
    finally:
        # Teardown: delete the QCTEST- disposable record (UI-only, per
        # cms-profile.md's current Test-Data Policy) so this test never
        # leaves a permanent card in the live carousel.
        admin.open_pillar_cards_list()
        if admin.row_visible(QCTEST_TITLE):
            admin.delete_pillar_card_by_title(QCTEST_TITLE)


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
def test_edit_existing_mission_pillar_card_reflects_on_home_page(page):
    # QA-135557 — Open the existing "Mission" pillar card (ID 49082,
    # confirmed live) -> change its description -> Save -> reload the Home
    # Page -> assert the public carousel shows the UPDATED description.
    # SNAPSHOT_RESTORE exception (see module docstring #3): baseline is
    # captured before mutating and restored in `finally`, re-verified by a
    # fresh re-open.
    admin = HomeStrategicDirectionAdminPage(page)
    home = HomeStrategicDirectionPage(page)

    admin.open_pillar_cards_list()
    admin.open_pillar_card_edit_form_by_title(MISSION_TITLE)
    baseline_description = admin.pillar_description_text()
    updated_description = (
        "QCTEST-135557 temporary Mission description — automated edit-and-restore "
        "regression check, will be reverted by test teardown."
    )

    try:
        # Act
        admin.fill_pillar_card_form(pillar_description=updated_description)
        admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error editing Mission's description: "
            f"{admin.save_error_text()!r}"
        )

        # Assert: admin reload shows the new description.
        admin.reopen_pillar_card_by_title_fresh(MISSION_TITLE)
        assert admin.pillar_description_text() == updated_description

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
        admin.reopen_pillar_card_by_title_fresh(MISSION_TITLE)
        current = admin.pillar_description_text()
        if current != baseline_description:
            admin.fill_pillar_card_form(pillar_description=baseline_description)
            admin.save()
        admin.reopen_pillar_card_by_title_fresh(MISSION_TITLE)
        assert admin.pillar_description_text() == baseline_description, (
            "teardown failed to restore Mission's description to its "
            "captured baseline — real editorial content may be left mutated"
        )


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
    # QA-135562 — Clear the required EN title field -> click Save (this
    # form's only persist/publish action — see module docstring's
    # disclosed substitution #2 for why "Pillar Title" stands in for the
    # case's "Section Heading (EN)", which does not exist on this form) ->
    # assert Save is BLOCKED with the real confirmed inline validation
    # error, and the record's persisted value is unchanged. SNAPSHOT_RESTORE
    # exception on the real "Mission" record (module docstring #3);
    # restored defensively in `finally` regardless of outcome, per the case's
    # own instruction.
    admin = HomeStrategicDirectionAdminPage(page)

    admin.open_pillar_cards_list()
    admin.open_pillar_card_edit_form_by_title(MISSION_TITLE)
    baseline_title = admin.pillar_title_value()

    try:
        # Act
        admin.fill_pillar_card_form(pillar_title="")
        admin.click(admin.SAVE_BUTTON)
        page.wait_for_timeout(admin.SAVE_COMMIT_GRACE_MS)

        # Assert: Save is blocked with the real, confirmed-live validation
        # strings (see module docstring #2 for why these differ from the
        # case's "Section Heading (EN) is required." paraphrase).
        assert admin.is_save_error_shown(), (
            "clearing the required Pillar Title field and clicking Save did "
            "not surface any validation error — the form may have silently "
            "accepted an empty mandatory field"
        )
        error_text = admin.save_error_text()
        assert admin.SAVE_ERROR_BANNER_PREFIX in error_text or admin.INLINE_REQUIRED_TEXT in error_text, (
            f"validation error text did not match the confirmed-live "
            f"strings: got {error_text!r}"
        )

        # Assert: the record's own persisted value is unchanged — the
        # blocked Save must not have silently committed the empty title.
        admin.reopen_pillar_card_by_title_fresh(MISSION_TITLE)
        assert admin.pillar_title_value() == baseline_title, (
            "Mission's Pillar Title was persisted as empty despite the form "
            "reporting a blocked/invalid Save — publish was NOT actually "
            "blocked server-side"
        )
    finally:
        # Defensive restore regardless of outcome, per the case's own
        # instruction — the field is client-side cleared during Act and
        # should never have persisted, but restore explicitly rather than
        # trust that.
        admin.reopen_pillar_card_by_title_fresh(MISSION_TITLE)
        current = admin.pillar_title_value()
        if current != baseline_title:
            admin.fill_pillar_card_form(pillar_title=baseline_title)
            admin.save()
        admin.reopen_pillar_card_by_title_fresh(MISSION_TITLE)
        assert admin.pillar_title_value() == baseline_title, (
            "teardown failed to restore Mission's Pillar Title to its "
            "captured baseline — real editorial content may be left mutated"
        )

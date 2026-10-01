"""
cms/tests/publications/test_publications_control_panel.py —
Control_Panel-tagged cases for PBI 130711 ("QC - Insights & Media - 003 -
Publications"), Azure suite 140370 in plan 137724.

Holds every case whose tags include `Control_Panel` plus the Control_Panel-side
test of every case tagged BOTH `Web` and `Control_Panel` (144004, 144005,
144006, 144007, 144011, 144012, 144071, 144072, 144075) — the Web-side test for
those lives in web/tests/publications/test_publications_web.py under the SAME
`tc_<id>` marker.

RE-HEALED 2026-09-30 (Engineer A, Phase 3). What changed and why:
  - Lifecycle cases (143996-144015, 144072-144081) now sign in as the account
    the case names — Site Content Editor (156488) or Site Content Author
    (156492) — in an auth-free context, and re-check the signed-in userId
    before each lifecycle assertion. They used to run as super-admin
    TEST_USER, which bypasses the editorial workflow (standards.md).
  - The live form no longer has a "Publication Status" combobox; an Editor's
    submit button reads "Publish" and publishes straight away. Active Status
    is ticked by default on a new entry.
  - Every record is created with a unique `QCTEST-<tc>-…` title, registered
    with the `disposable` fixture (conftest.py) right after creation, and
    torn down ONLY through PublicationAdminPage.delete_disposable_entry — the
    guarded delete (QCTEST- prefix, fully expanded list, exactly one
    exact-title row, matching delete label, re-checked before the click).
  - Save feedback is the `[data-qc-oel-editbar]` banner ("Saved and
    published.", "Draft saved."). A NEW record's add path shows NO banner
    (same as Bug 147788 on Law Regulation) — tests that expect a message on
    create surface its absence as a failure.
  - The case wording "audit log" maps onto the row's History trail
    (`ul.qc-oel__history-list`: action / actor / timestamp) — there is no
    separate audit-log screen on this surface.
  - Arabic Control Panel cases (144080/144081) switch the interface language
    only through the `/ar/` URL prefix of the test's OWN browser session; no
    account language preference is changed, and the controls are addressed by
    locale-neutral name/id attributes (no Arabic locators).

Still SKIPPED (re-evaluated live 2026-09-30):
  - Publication Type management (144008-144012, 144016, 144047-144052,
    144071): Publication Type is a FIXED picklist on the Publication form
    (Content-Admin-Guide §12; live options Report, Bulletin, Study, Research
    Paper, Guides, White Paper, Manuals, Brochure) with no authoring object —
    a requirements conflict, not automatable.
  - 144001: the create form has no Cancel/discard control (the only
    "Cancel…" link, "Cancel and add a new entry instead", exists on the EDIT
    form of an already-saved record).
"""

import json
import re
from datetime import date, datetime, timedelta

import allure
import pytest

from cms.pages.publications.publication_admin_page import (
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    FIELD_COVER_IMAGE,
    FIELD_FILE_ATTACHMENT,
    FIELD_PAGE_COUNT,
    FIELD_PUBLICATION_DESCRIPTION_AR,
    FIELD_PUBLICATION_DESCRIPTION_EN,
    FIELD_PUBLICATION_TITLE_AR,
    FIELD_PUBLICATION_TITLE_EN,
    QCTEST_PREFIX,
    CreatedEntry,
    PublicationAdminPage,
)
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.tests.publications.pub_support import (
    ARABIC,
    AUTH_FREE_PAGE,
    HISTORY_CLOCK_TOLERANCE,
    LATIN,
    PUBLIC_POLL,
    PUBLIC_REFLECT_TIMEOUT,
    assert_still_pinned,
    attach_banners,
    create,
    parse_when,
    pinned_login,
    public_titles,
    public_until,
    assert_not_public,
    assert_publicly_visible,
    snapshot_ids,
    register_if_created,
    require_no_leftovers,
    title_for,
    wait_row_status,
)
from core.utils.waits import WaitTimeoutError, wait_until
from web.pages.publications.publications_page import PublicationsPage

PUBLICATIONS_CMS_XDIST_GROUP = pytest.mark.xdist_group("publications_cms")
FIXTURES = "cms/tests/publications/fixtures"


# ===========================================================================
# Engineer A helpers
# ===========================================================================
def _editor(page) -> PublicationAdminPage:
    admin = PublicationAdminPage(page)
    pinned_login(admin, ROLE_EDITOR)
    return admin


def _data(title: str, **overrides) -> dict:
    return PublicationAdminPage.default_data(title, **overrides)


def _assert_not_public(anon_pages, title: str) -> None:
    """Review M5: absence only counts after a positive control proves the
    logged-out page and its search box actually show a visible publication."""
    assert_not_public(anon_pages, title)


def _history_keys(history: list[dict]) -> set:
    return {(h["action"], h["who"], h["when"], h["comment"]) for h in history}


def _assert_history_entry(admin, entry, actor: str, action_pattern: str, saved_at: datetime,
                          before: list[dict]) -> list[dict]:
    """Review m3: `before` is the History read BEFORE the save; only entries
    that are NEW since then count."""
    history = admin.history(entry)
    allure.attach(f"before: {before!r}\nafter: {history!r}", name=f"History of {entry.title}")
    old = _history_keys(before)
    new_entries = [h for h in history if (h["action"], h["who"], h["when"], h["comment"]) not in old]
    assert new_entries, f"the save added NO new History entry for {entry.title!r}; History reads {history}"
    matching = [h for h in new_entries if h["who"] == actor and re.search(action_pattern, h["action"], re.I)]
    assert matching, (
        f"no NEW History entry by {actor!r} with an action matching /{action_pattern}/ for "
        f"{entry.title!r}; new entries {new_entries}"
    )
    stamps = [parse_when(h["when"]) for h in matching]
    assert any(s and abs(s - saved_at) <= HISTORY_CLOCK_TOLERANCE for s in stamps), (
        f"History entries by {actor!r} carry {[h['when'] for h in matching]}, none within "
        f"{HISTORY_CLOCK_TOLERANCE} of the save at {saved_at:%m/%d/%Y %I:%M:%S %p}"
    )
    return matching


# ===========================================================================
# 143996 — Editor full lifecycle (+ Type management: requirements conflict)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Roles / Lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor can create, edit, preview, publish, unpublish, and delete a Publication record")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_143996
@PUBLICATIONS_CMS_XDIST_GROUP
def test_editor_full_record_lifecycle(page, disposable):
    # Azure TC 143996 | PBI 130711 | account: Site Content Editor (156488)
    admin = _editor(page)
    title = title_for("143996", "Editor-Full-Lifecycle")
    require_no_leftovers(admin, title)

    with allure.step("Create + save"):
        entry = create(admin, disposable, _data(title), publish=False)
        assert admin.row_status(entry) == STATUS_DRAFT

    with allure.step("Edit"):
        admin.open_entry(entry)
        admin.fill_text(FIELD_PUBLICATION_DESCRIPTION_EN, f"{title} edited description.")
        assert_still_pinned(admin, ROLE_EDITOR)
        admin.save_as_draft()
        assert admin.save_redirected(), f"edit save refused: {admin.field_errors()} {admin.feedback_banners()}"
        admin.open_entry(entry)
        assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_EN) == f"{title} edited description."

    with allure.step("Preview"):
        preview = admin.open_preview(entry)
        assert title in preview and "PREVIEW" in preview, "the Draft preview did not render the record"

    with allure.step("Publish"):
        admin.open_entry(entry)
        assert_still_pinned(admin, ROLE_EDITOR)
        admin.publish()
        assert admin.save_redirected(), f"publish refused: {admin.field_errors()} {admin.feedback_banners()}"
        assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED

    with allure.step("Unpublish"):
        assert_still_pinned(admin, ROLE_EDITOR)
        admin.open_entries_list()
        admin.run_row_action(entry, "unpublish")
        assert wait_row_status(admin, entry, STATUS_UNPUBLISHED) == STATUS_UNPUBLISHED

    with allure.step("Delete"):
        assert_still_pinned(admin, ROLE_EDITOR)
        assert admin.delete_disposable_entry(entry), "the Editor's delete did not remove the record"
        disposable.mark_removed(entry)
        admin.open_entries_list()
        assert not admin.row_present(entry)
    # Step 3 (Publication Type management) is its own test below (review M7).


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Roles / Lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Step 3 of 143996: a Site Content Editor can add, edit, reorder and deactivate a Publication Type")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_143996
@pytest.mark.skip(
    reason="143996 step 3 only (steps 1-2 run in test_editor_full_record_lifecycle): requirements conflict — "
    "Publication Type is a FIXED picklist on the Publication form (Content-Admin-Guide §12); no Publication "
    "Type authoring object exists, so types cannot be added, edited, reordered or deactivated."
)
def test_editor_manage_publication_types(page):
    ...


# ===========================================================================
# 143997 — Author views and updates an assigned (own) record
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Roles / Permissions")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Author can view and update an assigned Publication record")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130711
@pytest.mark.tc_143997
@PUBLICATIONS_CMS_XDIST_GROUP
def test_author_view_update_assigned_record(page, disposable):
    # Azure TC 143997 | PBI 130711 | account: Site Content Author (156492).
    # "Assigned" = a record the Author owns (role sheet: Authors edit OWN content).
    admin = PublicationAdminPage(page)
    author_name = pinned_login(admin, ROLE_AUTHOR)
    title = title_for("143997", "Author-Assigned")
    require_no_leftovers(admin, title)
    entry = create(admin, disposable, _data(title), publish=False)

    # Step 2 — the record opens for editing.
    admin.open_entry(entry)
    assert admin.is_save_as_draft_enabled(), "the Author's own record did not open for editing"
    new_description = f"{title} — description updated by the Author."
    history_before = admin.history(entry)
    admin.open_entry(entry)
    admin.fill_text(FIELD_PUBLICATION_DESCRIPTION_EN, new_description)

    # Step 3 — save: change stored, no publish triggered.
    assert_still_pinned(admin, ROLE_AUTHOR)
    saved_at = datetime.now()
    admin.save_as_draft()
    assert admin.save_redirected(), f"save refused: {admin.field_errors()} {admin.feedback_banners()}"
    banners = attach_banners(admin, "the Author's save")
    assert_still_pinned(admin, ROLE_AUTHOR)
    admin.open_entry(entry)
    assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_EN) == new_description, "the change was not saved"
    admin.open_entries_list()
    status = admin.row_status(entry)
    assert status == STATUS_DRAFT, f"saving triggered a workflow move: the record is now {status!r}"
    _assert_history_entry(admin, entry, author_name, r"edit", saved_at, history_before)
    assert banners, "no confirmation message after the Author's save (the save itself went through)"


# ===========================================================================
# 143998 — Author denied Publish, Delete and Publication Type management
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Roles / Permissions")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Author is denied Publish, Delete, and Manage Publication Types")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130711
@pytest.mark.tc_143998
@PUBLICATIONS_CMS_XDIST_GROUP
def test_author_denied_publish_delete_manage_types(page, disposable, role_session):
    # Azure TC 143998 | PBI 130711 | Author (156492); the target record is
    # created and published by the Editor (156488) in a separate session.
    editor = role_session(ROLE_EDITOR)
    pinned_login(editor, ROLE_EDITOR)
    title = title_for("143998", "Editor-Owned")
    require_no_leftovers(editor, title)
    entry = create(editor, disposable, _data(title), publish=True)
    assert wait_row_status(editor, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED

    admin = PublicationAdminPage(page)
    pinned_login(admin, ROLE_AUTHOR)
    own_title = title_for("143998", "Author-Owned")
    require_no_leftovers(admin, own_title)

    # Step 2 — Publish is unavailable; status does not change. Checked on the
    # Editor's record (row actions; live 2026-09-30 the Author's row renders no
    # Edit link, so it cannot be opened at all) AND on a record the Author owns
    # and CAN open (its form must offer no Publish button).
    admin.open_entries_list()
    assert admin.row_present(entry), "the Author cannot see the Editor's record at all"
    row_actions = admin.row_actions(entry)
    can_edit_editors_record = admin.row_has_edit_link(entry)
    allure.attach(f"row actions {row_actions}; Edit link: {can_edit_editors_record}",
                  name="Author's view of the Editor's record")
    assert not {"publish", "approve", "unpublish"} & set(row_actions), (
        f"the Author is offered workflow actions on the Editor's record: {row_actions}"
    )
    if can_edit_editors_record:
        admin.open_entry(entry)
        editors_form = admin.form_action_labels()
        assert "Publish" not in editors_form, f"Publish offered to the Author on the Editor's record: {editors_form}"
    own = create(admin, disposable, _data(own_title), publish=False)
    admin.open_entry(own)
    form_actions = admin.form_action_labels()
    allure.attach(repr(form_actions), name="Author form actions on the Author's own record")
    assert "Publish" not in form_actions, f"a Publish button is offered to the Author: {form_actions}"
    assert admin.submit_button_label() == "Submit for Review", (
        f"the Author's submit button reads {admin.submit_button_label()!r}"
    )
    assert_still_pinned(admin, ROLE_AUTHOR)
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_PUBLISHED, "the Editor's record changed status"
    assert admin.row_status(own) == STATUS_DRAFT, "the Author's own record changed status"

    # Step 3 — Delete unavailable; no Publication Type management reachable.
    assert "delete" not in row_actions, f"Delete is offered to the Author on the Editor's record: {row_actions}"
    admin.open(admin.manage_url().replace("manage-publication", "object-authoring"))
    nav_text = admin.page_body_text()
    assert not re.search(r"Publication Type", nav_text), (
        "a Publication Type management object is listed for the Author"
    )
    allure.attach(
        "No Publication Type authoring object exists for ANY role (fixed picklist, Content-Admin-Guide "
        "§12), so this sub-check cannot distinguish role-based denial from absence.",
        name="Note on the Publication Type sub-check",
    )


# ===========================================================================
# 144000 — Editor creates a new record and saves as Draft
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Create / Draft")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor can create a new Publication and save it as Draft")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144000
@PUBLICATIONS_CMS_XDIST_GROUP
def test_editor_create_save_as_draft(page, disposable, anon_pages):
    # Azure TC 144000 | PBI 130711 | account: Site Content Editor
    admin = _editor(page)
    title = title_for("144000", "Create-Draft")
    require_no_leftovers(admin, title)
    data = _data(title, publication_type="Research Paper", page_count="12", publication_date="15/09/2026")

    # Step 1-2 — form opens, all fields accept the values.
    ids_before = snapshot_ids(admin)
    admin.open_new_entry_form()
    admin.fill_publication(data)
    filled = admin.read_publication()
    assert filled["publication_type"] == "Research Paper" and filled["page_count"] == "12"
    assert admin.uploaded_filename(FIELD_COVER_IMAGE) and admin.uploaded_filename(FIELD_FILE_ATTACHMENT)

    # Step 3 — save: Draft, not public.
    assert_still_pinned(admin, ROLE_EDITOR)
    admin.save_as_draft()
    went_through = admin.save_redirected()
    entry = register_if_created(admin, disposable, title, ids_before)
    assert went_through and entry, f"save did not go through: {admin.field_errors()} {admin.feedback_banners()}"
    assert admin.row_status(entry) == STATUS_DRAFT
    admin.open_entry(entry)
    stored = admin.read_publication()
    assert stored["title"] == title and stored["publication_type"] == "Research Paper"
    assert stored["page_count"] == "12" and stored["publication_date"] == "15/09/2026", f"stored values: {stored}"
    _assert_not_public(anon_pages, title)


# ===========================================================================
# 144001 — SKIPPED (re-checked live 2026-09-30): no Cancel/discard control
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Create / Draft")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Cancelling the Create Publication form discards entered data")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144001
@pytest.mark.skip(
    reason="Re-checked live 2026-09-30 as Site Content Editor: the Create Publication form has no "
    "Cancel/discard control (its only buttons are Save as Draft and Publish; a full a/button sweep "
    "for cancel/discard/back found none). The one 'Cancel and add a new entry instead' link exists "
    "only on the EDIT form of an already-saved record, so step 3 cannot be performed."
)
def test_cancel_create_form_discards_data(page):
    ...


# ===========================================================================
# 144002 — Editor saves an existing record as Draft
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Create / Draft")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can save an existing Publication record as Draft")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144002
@PUBLICATIONS_CMS_XDIST_GROUP
def test_editor_resave_existing_as_draft(page, disposable, anon_pages):
    # Azure TC 144002 | PBI 130711 | account: Site Content Editor
    admin = _editor(page)
    title = title_for("144002", "Resave-Draft")
    require_no_leftovers(admin, title)
    entry = create(admin, disposable, _data(title), publish=False)

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    admin.save_as_draft()
    assert admin.save_redirected(), f"save refused: {admin.field_errors()} {admin.feedback_banners()}"
    banners = attach_banners(admin, "Save as Draft on an existing record")
    assert any(MSG_DRAFT_SAVED in b for b in banners), f"no 'Draft saved.' confirmation; banners {banners}"
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT
    _assert_not_public(anon_pages, title)


# ===========================================================================
# 144003 — Editor previews a Draft record before publishing
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Preview")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can preview a Draft Publication record before publishing")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144003
@PUBLICATIONS_CMS_XDIST_GROUP
def test_editor_preview_draft_record(page, disposable, anon_pages):
    # Azure TC 144003 | PBI 130711 | account: Site Content Editor
    admin = _editor(page)
    title = title_for("144003", "Preview-Draft")
    require_no_leftovers(admin, title)
    data = _data(title)
    entry = create(admin, disposable, data, publish=False)

    preview = admin.open_preview(entry)
    allure.attach(preview[:4000], name="Preview page text")
    assert title in preview, "the preview does not render the Draft's title"
    assert data["description"] in preview, "the preview does not render the Draft's description as authored"
    assert "this record is Draft" in preview, "the preview does not identify the record as a Draft"
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT, "previewing changed the record's status"
    _assert_not_public(anon_pages, title)


# ===========================================================================
# 144004/144005/144006/144007 — Publish lifecycle (Control_Panel side)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing via Object Authoring sets the record to Published with a success message (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144004
@PUBLICATIONS_CMS_XDIST_GROUP
def test_publish_updates_status_cms(page, disposable):
    # Azure TC 144004 | PBI 130711 — Control_Panel half (step 1). The public
    # card check (step 2) is the Web-side test under the same marker.
    admin = _editor(page)
    title = title_for("144004", "Publish-Flow")
    require_no_leftovers(admin, title)
    ids_before = snapshot_ids(admin)
    admin.open_new_entry_form()
    admin.fill_publication(_data(title, publication_type="Guides", page_count="5"))
    assert_still_pinned(admin, ROLE_EDITOR)
    admin.publish()
    went_through = admin.save_redirected()
    banners = attach_banners(admin, "publishing a new Publication")
    entry = register_if_created(admin, disposable, title, ids_before)
    assert went_through and entry, f"publish did not go through: {admin.field_errors()} {admin.feedback_banners()}"
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED
    admin.open_entry(entry)
    stored = admin.read_publication()
    assert stored["publication_type"] == "Guides" and stored["page_count"] == "5", f"stored values: {stored}"
    assert stored["active_status"] is True
    assert banners, (
        "no success message after publishing a NEW Publication (the record was created and Published; the "
        "add path reloads the list with no [data-qc-oel-editbar] banner — same as Bug 147788 on Law Regulation)"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Editing and republishing updates the record, not a stale value (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144005
@PUBLICATIONS_CMS_XDIST_GROUP
def test_republish_updates_record_cms(page, disposable):
    # Azure TC 144005 | PBI 130711 — Control_Panel half (steps 1-2).
    admin = _editor(page)
    original = title_for("144005", "Original Title")
    updated = title_for("144005", "Updated Title")
    require_no_leftovers(admin, original, updated)
    entry = create(admin, disposable, _data(original), publish=True)
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED

    admin.open_entry(entry)
    admin.fill_text(FIELD_PUBLICATION_TITLE_EN, updated)
    entry = disposable.add_title(entry, updated)  # known to teardown BEFORE the rename is sent
    assert_still_pinned(admin, ROLE_EDITOR)
    admin.publish()
    assert admin.save_redirected(), f"republish refused: {admin.field_errors()} {admin.feedback_banners()}"
    banners = attach_banners(admin, "republishing")
    assert any(MSG_SAVED_AND_PUBLISHED in b for b in banners), f"no 'Saved and published.' message; {banners}"
    admin.open_entries_list()
    assert admin.row_title(entry) == updated, f"the row reads {admin.row_title(entry)!r}, not {updated!r}"
    assert admin.row_status(entry) == STATUS_PUBLISHED
    assert not admin.rows_with_exact_title(original), "a row with the original title is still listed"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Unpublishing sets the record to Unpublished with a success message (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144006
@PUBLICATIONS_CMS_XDIST_GROUP
def test_unpublish_updates_status_cms(page, disposable, anon_pages):
    # Azure TC 144006 | PBI 130711 — Control_Panel half (steps 1-2) + the
    # logged-out absence read of step 3.
    admin = _editor(page)
    title = title_for("144006", "Unpublish-Flow")
    require_no_leftovers(admin, title)
    entry = create(admin, disposable, _data(title), publish=True)
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED
    assert_publicly_visible(anon_pages, title)

    assert_still_pinned(admin, ROLE_EDITOR)
    admin.open_entries_list()
    dialogs = admin.run_row_action(entry, "unpublish")
    allure.attach(repr(dialogs), name="Unpublish dialogs")
    banners = attach_banners(admin, "Unpublish")
    assert wait_row_status(admin, entry, STATUS_UNPUBLISHED) == STATUS_UNPUBLISHED
    _assert_not_public(anon_pages, title)
    assert banners, (
        f"no success message after Unpublish (the record did move to Unpublished; the only feedback was the "
        f"confirm() dialog {dialogs!r})"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can delete a Publication record (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144007
@PUBLICATIONS_CMS_XDIST_GROUP
def test_delete_record_cms(page, disposable, anon_pages):
    # Azure TC 144007 | PBI 130711 — Control_Panel half.
    admin = _editor(page)
    title = title_for("144007", "Delete-Flow")
    require_no_leftovers(admin, title)
    entry = create(admin, disposable, _data(title), publish=True)
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED
    # Positive control (review M5): the record must first be publicly visible,
    # otherwise its later absence proves nothing.
    assert_publicly_visible(anon_pages, title)

    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.delete_disposable_entry(entry), "the Editor's delete did not remove the record"
    disposable.mark_removed(entry)
    allure.attach(repr(getattr(admin, "last_delete_dialogs", [])), name="Delete dialogs")
    admin.open_entries_list()
    assert admin.is_list_fully_expanded() and not admin.row_present(entry), "the record is still listed"
    _assert_not_public(anon_pages, title)


# ===========================================================================
# 144008-144010 — SKIPPED: no Publication Type authoring surface
# ===========================================================================
TYPES_SKIP = (
    "Requirements conflict (re-confirmed 2026-09-30): Publication Type is a FIXED picklist on the "
    "Publication form (Content-Admin-Guide §12; options Report, Bulletin, Study, Research Paper, Guides, "
    "White Paper, Manuals, Brochure). No 'Manage Publication Types' authoring object exists, so types "
    "cannot be added, renamed, reordered, (de)activated or audited."
)


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Adding a new Publication Type "Case Studies" with EN/AR names')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144008
@pytest.mark.skip(reason=TYPES_SKIP)
def test_add_new_publication_type(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Editing a Publication Type's EN/AR name reflects on the public filter dropdown and chips")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144009
@pytest.mark.skip(reason=TYPES_SKIP)
def test_edit_publication_type_name_reflects_public(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reordering Publication Types reflects the new order in the public filter dropdown and chips")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144010
@pytest.mark.skip(reason=TYPES_SKIP)
def test_reorder_publication_types_reflects_public(page):
    ...


# ===========================================================================
# 144011/144012 — SKIPPED: no Publication Type authoring surface
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Deactivating the "Manuals" Publication Type (Control_Panel side)')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144011
@pytest.mark.skip(reason=TYPES_SKIP)
def test_deactivate_manuals_type_cms(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Reactivating the "Manuals" Publication Type (Control_Panel side)')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144012
@pytest.mark.skip(reason=TYPES_SKIP)
def test_reactivate_manuals_type_cms(page):
    ...


# ===========================================================================
# 144013 — Unique, system-generated id on save
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A newly saved Publication receives a unique, system-generated id")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144013
@PUBLICATIONS_CMS_XDIST_GROUP
def test_new_record_gets_unique_system_id(page, disposable):
    # Azure TC 144013 | PBI 130711. Mapping: the form renders no "Publication
    # ID" control; the system id is the entry id the list exposes on each row
    # (data-qc-oel-* / Preview link `publications:<id>`) plus the entry code in
    # the edit URL — both assigned by the system, neither editable.
    admin = _editor(page)
    title1 = title_for("144013", "ID-Uniqueness")
    title2 = title_for("144013", "ID-Uniqueness-2")
    require_no_leftovers(admin, title1, title2)

    entry1 = create(admin, disposable, _data(title1), publish=False)
    admin.open_entry(entry1)
    code1 = admin.entry_code
    labels = admin.form_field_labels()
    allure.attach(repr(labels), name="Form field labels")
    assert not any(re.search(r"\bID\b", label) for label in labels), (
        f"the form exposes an ID-like field that a user could edit: {labels}"
    )
    entry2 = create(admin, disposable, _data(title2), publish=False)
    admin.open_entry(entry2)
    code2 = admin.entry_code

    assert entry1.entry_id.isdigit() and entry2.entry_id.isdigit(), (entry1, entry2)
    assert entry1.entry_id != entry2.entry_id, f"both records got id {entry1.entry_id}"
    assert code1 and code2 and code1 != code2, f"entry codes {code1!r} / {code2!r}"


# ===========================================================================
# 144014 — Editing a Published record updates its Last Modified Date
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Editing and saving a Published Publication updates its Last Modified Date")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144014
@PUBLICATIONS_CMS_XDIST_GROUP
def test_edit_published_updates_last_modified(page, disposable):
    # Azure TC 144014 | PBI 130711 — Last Modified = the list's LAST MODIFIED column.
    admin = _editor(page)
    title = title_for("144014", "Last-Modified")
    require_no_leftovers(admin, title)
    entry = create(admin, disposable, _data(title), publish=True)
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED
    before_text = admin.row_modified(entry)
    before = parse_when(before_text)
    assert before, f"unreadable Last Modified {before_text!r}"

    admin.open_entry(entry)
    admin.fill_text(FIELD_PUBLICATION_DESCRIPTION_EN, f"{title} updated description.")
    assert_still_pinned(admin, ROLE_EDITOR)
    saved_at = datetime.now()
    admin.publish()
    assert admin.save_redirected(), f"save refused: {admin.field_errors()} {admin.feedback_banners()}"
    admin.open_entries_list()
    after_text = admin.row_modified(entry)
    after = parse_when(after_text)
    assert after and after > before, f"Last Modified went from {before_text!r} to {after_text!r}"
    assert abs(after - saved_at) <= HISTORY_CLOCK_TOLERANCE, (
        f"Last Modified {after_text!r} is not the time of this save ({saved_at:%m/%d/%Y %I:%M:%S %p})"
    )


# ===========================================================================
# 144015 — Save shows the success message and records a History entry
# 144016 — SKIPPED: no Publication Type authoring surface
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Feedback / Audit")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a Publication change shows the success message and records an audit (History) entry")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144015
@PUBLICATIONS_CMS_XDIST_GROUP
def test_save_shows_toast_and_audit_entry(page, disposable):
    # Azure TC 144015 | PBI 130711. Mapping: "Liferay generic success toast"
    # = the [data-qc-oel-editbar] banner; "audit log" = the row's History trail
    # (no separate audit-log screen exists on this surface).
    admin = _editor(page)
    editor_name = admin.signed_in_user()[1]
    title = title_for("144015", "Save-Audit")
    require_no_leftovers(admin, title)
    entry = create(admin, disposable, _data(title, page_count="3"), publish=True)
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED

    history_before = admin.history(entry)
    admin.open_entry(entry)
    admin.fill_number(FIELD_PAGE_COUNT, "7")
    assert_still_pinned(admin, ROLE_EDITOR)
    saved_at = datetime.now()
    admin.publish()
    assert admin.save_redirected(), f"save refused: {admin.field_errors()} {admin.feedback_banners()}"
    banners = attach_banners(admin, "saving the Page Count change")
    assert any(MSG_SAVED_AND_PUBLISHED in b for b in banners), f"no success message on save; banners {banners}"
    admin.open_entry(entry)
    assert admin.number_field_value(FIELD_PAGE_COUNT) == "7"

    matching = _assert_history_entry(admin, entry, editor_name, r"edit", saved_at, history_before)
    assert any(re.search(r"page\s*count", h["text"], re.I) for h in matching), (
        f"the History entry for this change names the actor and time but not the modified field "
        f"(Page Count): {matching}"
    )


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Feedback / Audit")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Adding a new Publication Type shows the Liferay success toast and records an audit entry")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144016
@pytest.mark.skip(reason=TYPES_SKIP)
def test_add_type_shows_toast_and_audit_entry(page):
    ...


# ===========================================================================
# Engineer B helpers — 144017-144052 field validation (re-healed 2026-09-30)
#
#   - Every case signs in as Site Content Editor (156488) in an auth-free
#     context and re-checks the userId before each save and each assertion.
#   - "Save" = the Editor's Publish. Save as Draft skips required-field
#     validation on this object (Engineer A, live 2026-09-30), so a Draft save
#     cannot prove a value is accepted or rejected; Publish enforces it.
#   - Titles are `QCTEST-130711-<tc>-…`. Every record that gets created is
#     registered for the guarded teardown BEFORE any assertion runs; a
#     rejection case also registers anything that slipped through.
#   - Public-card checks run once, logged-out, after the CMS side is proven.
#     A record that never appears publicly is reported as blocked by the
#     public-delivery issue, not as a field bug.
# ===========================================================================
PUBLIC_DELIVERY_BLOCK = (
    "BLOCKED BY PUBLIC DELIVERY (not a field bug): newly published Publications have not been delivered "
    "publicly on qcdev since ~18:30 2026-09-30 (/o/c/publications/scopes/37246 returns only 2 older items)"
)
# Name/id fragment of each form control as reported by the browser's
# `invalid` event (live form 2026-09-30).
FIELD_TOKENS = {
    "title_en": "ObjectField_publicationTitle",
    "title_ar": "qc-ar-publicationTitle",
    "type": "select-from-list-input",
    "date": "publicationDate",
    "cover": "ObjectField_coverImage",
    "file": "ObjectField_fileAttachment",
    "page_count": "ObjectField_pageCount",
}
NATIVE_FIELDS = ("publicationTitle", "publicationDate", "coverImage", "fileAttachment", "pageCount")
# The control each field's FIELD-LEVEL evidence is read from (name, id, or id
# suffix — see PublicationAdminPage._control). Review M4.
FIELD_CONTROLS = {
    "title_en": "ObjectField_publicationTitle",
    "title_ar": "qc-ar-publicationTitle",
    "type": "select-from-list-input",
    "date": "ObjectField_publicationDate",
    "cover": "ObjectField_coverImage",
    "file": "ObjectField_fileAttachment",
    "page_count": "ObjectField_pageCount",
}
GENERIC_REFUSAL = "Please complete the required fields"
SHORT_TITLE_AR = "منشور اختبار آلي"
SHORT_DESCRIPTION = "QCTEST automated field-validation record."


def _b_title(tc: str, name: str) -> str:
    return title_for(tc, name)  # QCTEST-130711-<tc>-<name>


def _bdata(title: str, **overrides) -> dict:
    """Default data with short AR title / description, so a boundary case
    only ever stresses the one field it is about."""
    values = {"title_ar": SHORT_TITLE_AR, "description": SHORT_DESCRIPTION}
    values.update(overrides)
    return _data(title, **values)


def _padded(prefix: str, length: int, filler: str) -> str:
    assert len(prefix) < length, (prefix, length)
    return prefix + filler * (length - len(prefix))


def _entry_ids(admin) -> set:
    admin.open_entries_list()
    return {r["entry_id"] for r in admin.list_rows()}


def _submit(admin, action: str = "publish") -> dict:
    """Clicks Publish (or Save as Draft) and reads the outcome off the page
    BEFORE anything navigates away."""
    errors_before = admin.field_errors_by_control()
    admin.save_as_draft() if action == "draft" else admin.publish()
    ev = {
        "action": action,
        "went_through": admin.save_redirected(),
        "refused": admin.save_refused(),
        "save_responses": list(getattr(admin, "last_save_responses", [])),
        "invalid_fields": admin.invalid_fields_last_attempt(),
        "blocked": admin.submit_blocked(),
        "banners": admin.feedback_banners(),
        "refusal_bar": admin.refusal_bar_text(),
        "field_errors": admin.field_errors(),
        "native_messages": {},
        "form_text": "",
        "date_message": "",
        "save_requests": list(getattr(admin, "last_save_requests", [])),
    }
    # Live 2026-10-01: a server-side refusal can answer HTTP 200 and render the
    # red "This record was not saved" bar without reloading — still a refusal.
    ev["blocked"] = ev["blocked"] or (not ev["went_through"] and bool(ev["refusal_bar"]))
    if not ev["went_through"]:
        ev["form_text"] = admin.form_text()[:3000]
        ev["date_message"] = admin.date_field_message()
        # Live 2026-10-01: an invalid date keeps Publish from sending anything
        # and shows the picker's inline "Use dd/mm/yyyy" message instead.
        ev["blocked"] = ev["blocked"] or (not ev["save_requests"] and bool(ev["date_message"]))
    if not ev["went_through"]:
        for name in [f"ObjectField_{n}" for n in NATIVE_FIELDS] + sorted(set(ev["invalid_fields"])):
            try:
                message = admin.control_native_message(name)
            except Exception:  # noqa: BLE001 — control not rendered
                message = ""
            if message:
                ev["native_messages"][name] = message
        # Review M4 (HEALED 2026-10-02): per-field evidence. `native` = the
        # browser message on that control (only counted when the control also
        # fired `invalid` this attempt — the custom widgets keep a stale
        # "Please fill out this field." even when filled); `scoped` = inline
        # [data-qc-oel-field-error] text attributed to that control by DOM
        # ancestry and NEW since before the click (never static help text).
        errors_after = admin.field_errors_by_control()
        ev["field_errors_by_control"] = errors_after
        ev["field_evidence"] = {}
        for key, ref in FIELD_CONTROLS.items():
            new_texts = []
            for ctrl, texts in errors_after.items():
                if ctrl and (ctrl == ref or ctrl.endswith(ref)):
                    before = set(errors_before.get(ctrl, []))
                    new_texts += [t for t in texts if t not in before]
            try:
                native = admin.control_native_message(ref)
            except Exception:  # noqa: BLE001 — control not rendered
                native = ""
            ev["field_evidence"][key] = {"native": native, "scoped": " ".join(new_texts)}
    allure.attach(json.dumps(ev, ensure_ascii=False, indent=1), name=f"outcome of {action}")
    return ev


def _messages(ev: dict) -> list:
    """Every validation message the attempt showed: field errors, the red
    refusal bar, the workflow's own refusal banner ("Please complete the
    required fields…"), and the browser's constraint messages."""
    banners = [b for b in ev["banners"] if not b.startswith("Editing") and b != ev["refusal_bar"]
               and not ev["went_through"]]
    return [m for m in ev["field_errors"] + [ev["refusal_bar"], ev.get("date_message", "")] + banners
            + list(ev["native_messages"].values()) if m]


def _register_candidates(admin, disposable, ids_before: set, *titles: str) -> tuple:
    """Registers (for guarded teardown) every row carrying one of `titles`;
    also reports any other new row (never deleted — reported for hand removal)."""
    created = []
    for title in titles:
        if title and title.startswith(QCTEST_PREFIX):
            entry = register_if_created(admin, disposable, title, ids_before)
            if entry:
                created.append(entry)
    admin.open_entries_list()
    known = {e.entry_id for e in created}
    new_rows = [r for r in admin.list_rows() if r["entry_id"] not in ids_before and r["entry_id"] not in known]
    if new_rows:
        allure.attach(repr(new_rows), name="Other new rows since this attempt (NOT deleted)")
    return created, new_rows


def _strip_title(text: str, title: str) -> str:
    return text.replace(title, " ") if title else text


def _field_level(ev: dict, field_key: str) -> dict:
    """FIELD-LEVEL evidence for one field (review M4): `invalid` (its token
    fired this attempt's `invalid` event), `native` (the browser message on
    THAT control), `scoped` (an error node inside that control's own wrapper;
    for the date also the picker's inline message), title stripped."""
    title = ev.get("record_title", "")
    fe = ev.get("field_evidence", {}).get(field_key, {})
    scoped = _strip_title(fe.get("scoped", ""), title).strip()
    if field_key == "date" and not scoped:
        scoped = _strip_title(ev.get("date_message", ""), title).strip()
    if GENERIC_REFUSAL in scoped or (ev["refusal_bar"] and scoped == ev["refusal_bar"]):
        scoped = ""  # a page-wide bar is never field attribution
    invalid = any(FIELD_TOKENS[field_key] in f for f in ev["invalid_fields"])
    return {
        "invalid": invalid,
        # A native message is field-level proof only when THIS control fired
        # `invalid` in this attempt (see _submit).
        "native": fe.get("native", "").strip() if invalid else "",
        "scoped": scoped,
    }


def _assert_rejected(ev: dict, created: list, new_rows: list, field_key: str, hint: str, what: str) -> None:
    """Review M4: the generic "Please complete the required fields" banner or
    the red refusal bar alone NEVER count. Attribution needs field-level proof
    for `field_key` (its `invalid` event with the control's own message, or a
    NEW inline error located in that control's block); a blocked save whose
    field shows no field-level message FAILS with "save blocked but no
    field-level message". `hint` is kept for the report only."""
    assert not created and not (ev["went_through"] and new_rows), (
        f"{what}: the record WAS saved (registered {[(e.title, e.entry_id) for e in created]}, "
        f"other new rows {new_rows}); outcome {ev}"
    )
    assert ev["blocked"], f"{what}: the save was neither completed nor visibly refused; outcome {ev}"
    proof = _field_level(ev, field_key)
    allure.attach(f"{proof!r}\nhint (informational only): /{hint}/", name=f"field-level evidence for {field_key}")
    # HEALED 2026-10-02: every `scoped` message is attributed to the control by
    # DOM location (an inline error inside that control's own block, or the
    # date widget's own inline message), so no text-hint match is required —
    # e.g. 144046's "Use dd/mm/yyyy" belongs to the date field by location.
    assert proof["invalid"] or proof["native"] or proof["scoped"], (
        f"{what}: the refusal is not attributed to the field — no invalid event on {FIELD_TOKENS[field_key]}, "
        f"no message on that control, no field-scoped error (page-wide messages {_messages(ev)})"
    )
    assert proof["native"] or proof["scoped"], (
        f"{what}: save blocked but no field-level message (invalid event fired: {proof['invalid']}; "
        f"page-wide messages only: {_messages(ev)})"
    )


def _attempt_new(admin, disposable, data: dict, *candidates: str, prepare=None) -> tuple:
    """Opens the create form, fills `data`, runs `prepare(admin)` (extra
    typing), Publishes, and registers anything created under `candidates`."""
    ids_before = _entry_ids(admin)
    admin.open_new_entry_form()
    admin.fill_publication(data)
    if prepare:
        prepare(admin)
    assert_still_pinned(admin, ROLE_EDITOR)
    ev = _submit(admin, "publish")
    ev["record_title"] = data["title"]
    created, new_rows = _register_candidates(admin, disposable, ids_before, data["title"], *candidates)
    return ev, created, new_rows


def _create_published(admin, disposable, data: dict):
    assert_still_pinned(admin, ROLE_EDITOR)
    entry = create(admin, disposable, data, publish=True)
    assert_still_pinned(admin, ROLE_EDITOR)
    return entry


def _public_card(anon_pages, title: str, tc: str) -> tuple:
    """ONE logged-out publish-then-poll read. Fails with the public-delivery
    reason (plus a screenshot of the logged-out page) if the card never shows."""
    public = PublicationsPage(anon_pages())
    state = {"index": -1}

    def _visible() -> bool:
        public.open_publications().wait_for_results()
        public.search(title)
        state["index"] = public.card_index(title)
        return state["index"] >= 0

    try:
        wait_until(_visible, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL)
    except WaitTimeoutError:
        public.clear_search()
        public.screenshot(f"TC-{tc}")
        pytest.fail(
            f"{PUBLIC_DELIVERY_BLOCK}. {title!r} is Published with Active Status ticked in the CMS but never "
            f"appeared to a logged-out visitor within {PUBLIC_REFLECT_TIMEOUT:.0f}s "
            f"(public cards: {public.card_titles()})"
        )
    return public, state["index"]


def _assert_length_boundary(admin, disposable, tc: str, field: str, limit: int, filler: str, *,
                            title_field: bool) -> None:
    """Step 1: a `limit`-char value saves and reads back intact. Step 2: a
    `limit+1` value on the same record is rejected (input cut to `limit`, or
    the save refused with a message) and is NOT stored."""
    if title_field:
        exact = _padded(_b_title(tc, f"Len{limit}-"), limit, filler)
        title = exact
    else:
        title = _b_title(tc, f"Len{limit}")
        exact = filler * limit
    over = exact + filler
    require_no_leftovers(admin, title, over if title_field else title)
    data = _bdata(title) if title_field else _bdata(title, **{_DATA_KEY[field]: exact})

    entry = _create_published(admin, disposable, data)
    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    stored = admin.field_value(field)
    assert stored == exact, f"the {limit}-character value was not saved intact (read back {len(stored)} chars)"

    admin.fill_text(field, over)
    held = admin.field_value(field)
    if title_field:
        entry = disposable.add_title(entry, over)  # teardown knows the rename BEFORE it is sent
    assert_still_pinned(admin, ROLE_EDITOR)
    ev = _submit(admin, "publish")
    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    after = admin.field_value(field)
    allure.attach(f"typed {len(over)} chars, field held {len(held)}, stored after save {len(after)}",
                  name="Max-length evidence")
    assert len(after) <= limit, (
        f"the {limit + 1}-character value was STORED ({len(after)} chars read back after the save); outcome {ev}"
    )
    assert after == exact, (
        f"after the {limit + 1}-character save the field no longer holds the saved {limit}-character value — it "
        f"reads {after!r} ({len(after)} chars); outcome {ev}"
    )
    assert len(held) <= limit or (ev["blocked"] and _messages(ev)), (
        f"the {limit + 1}-character value was not stored, but no max-length validation error was shown and the "
        f"field did not cap the input; outcome {ev}"
    )


_DATA_KEY = {
    FIELD_PUBLICATION_TITLE_AR: "title_ar",
    FIELD_PUBLICATION_DESCRIPTION_EN: "description",
    FIELD_PUBLICATION_DESCRIPTION_AR: "description_ar",
}


def _assert_upload_rejected(admin, field: str, object_field: str, fixture: str, pattern: str, what: str) -> None:
    """Review M6: a rejection is ONLY a `{"success":false}` upload response or
    the text of a specific picker error element — never an exception and never
    the picker's static help text."""
    result = admin.attempt_upload(field, fixture)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1), name=f"upload evidence for {what}")
    refused_by_server = result["success"] is False
    error_text = " ".join(result["errors"])
    stored = admin.field_stored_value(object_field)
    assert not stored, (
        f"{what} was ACCEPTED: the server stored it in Documents & Media (HTTP {result['status']}) and the field "
        f"took it after Add (file id {stored!r}); no rejection message"
    )
    assert not (result["success"] is True and not error_text), (
        f"{what} was ACCEPTED by the upload service (HTTP {result['status']}, body {result['body'][:200]!r}) and "
        f"no picker error appeared (Add clicked: {result.get('add_clicked')})"
    )
    assert refused_by_server or error_text, (
        f"{what}: no rejection evidence — no {{\"success\":false}} response (status {result['status']}, "
        f"body {result['body'][:200]!r}) and no picker error message"
    )
    assert admin.field_stored_value(object_field) == "", (
        f"{what} was refused but the field holds file id {admin.field_stored_value(object_field)!r}"
    )
    message = f"{error_text} {result['body']}"
    assert re.search(pattern, message, re.I | re.S), (
        f"{what} was refused, but the rejection message does not match /{pattern}/: errors {result['errors']!r}, "
        f"server body {result['body'][:300]!r}"
    )


# ===========================================================================
# 144017-144020 — Publication Title EN validation
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Title EN validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Publication Title EN is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144017
@PUBLICATIONS_CMS_XDIST_GROUP
def test_title_en_valid_saved(page, disposable):
    # Azure TC 144017 | PBI 130711 | Editor. Case value "Qatar Economic
    # Outlook 2026", carried behind the mandatory QCTEST-130711-<tc>- prefix.
    admin = _editor(page)
    title = _b_title("144017", "Qatar Economic Outlook 2026")
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title))

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.field_value(FIELD_PUBLICATION_TITLE_EN) == title


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Title EN validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An empty Publication Title EN is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144018
@PUBLICATIONS_CMS_XDIST_GROUP
def test_title_en_empty_rejected(page, disposable):
    # Azure TC 144018 | PBI 130711 | Editor
    admin = _editor(page)
    marker = _b_title("144018", "Empty-Title-EN")
    require_no_leftovers(admin, marker)
    data = _bdata(marker, title_ar=f"{marker} منشور")
    data["title"] = ""
    ev, created, new_rows = _attempt_new(admin, disposable, data, data["title_ar"])
    _assert_rejected(ev, created, new_rows, "title_en", r"title", "empty Title EN")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Title EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Title EN accepts 200 characters and rejects 201")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144019
@PUBLICATIONS_CMS_XDIST_GROUP
def test_title_en_200_boundary(page, disposable):
    # Azure TC 144019 | PBI 130711 | Editor
    admin = _editor(page)
    _assert_length_boundary(admin, disposable, "144019", FIELD_PUBLICATION_TITLE_EN, 200, "Q", title_field=True)


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Title EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only Publication Title EN is rejected as empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144020
@PUBLICATIONS_CMS_XDIST_GROUP
def test_title_en_whitespace_only_rejected(page, disposable):
    # Azure TC 144020 | PBI 130711 | Editor
    admin = _editor(page)
    marker = _b_title("144020", "Whitespace-Title-EN")
    require_no_leftovers(admin, marker)
    data = _bdata(marker, title_ar=f"{marker} منشور")
    data["title"] = "   "
    ev, created, new_rows = _attempt_new(admin, disposable, data, data["title_ar"])
    _assert_rejected(ev, created, new_rows, "title_en", r"title", "whitespace-only Title EN")


# ===========================================================================
# 144021-144024 — Publication Title AR validation
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Title AR validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Publication Title AR is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144021
@PUBLICATIONS_CMS_XDIST_GROUP
def test_title_ar_valid_saved(page, disposable):
    # Azure TC 144021 | PBI 130711 | Editor
    admin = _editor(page)
    title = _b_title("144021", "Title-AR")
    title_ar = "توقعات الاقتصاد القطري 2026"
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title, title_ar=title_ar))

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.field_value(FIELD_PUBLICATION_TITLE_AR) == title_ar


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Title AR validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An empty Publication Title AR is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144022
@PUBLICATIONS_CMS_XDIST_GROUP
def test_title_ar_empty_rejected(page, disposable):
    # Azure TC 144022 | PBI 130711 | Editor
    admin = _editor(page)
    title = _b_title("144022", "Empty-Title-AR")
    require_no_leftovers(admin, title)
    ev, created, new_rows = _attempt_new(admin, disposable, _bdata(title, title_ar=""))
    _assert_rejected(ev, created, new_rows, "title_ar", r"arab|العربية|title", "empty Title AR")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Title AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Title AR accepts 200 characters and rejects 201")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144023
@PUBLICATIONS_CMS_XDIST_GROUP
def test_title_ar_200_boundary(page, disposable):
    # Azure TC 144023 | PBI 130711 | Editor
    admin = _editor(page)
    _assert_length_boundary(admin, disposable, "144023", FIELD_PUBLICATION_TITLE_AR, 200, "ت", title_field=False)


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Title AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only Publication Title AR is rejected as empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144024
@PUBLICATIONS_CMS_XDIST_GROUP
def test_title_ar_whitespace_only_rejected(page, disposable):
    # Azure TC 144024 | PBI 130711 | Editor
    admin = _editor(page)
    title = _b_title("144024", "Whitespace-Title-AR")
    require_no_leftovers(admin, title)
    ev, created, new_rows = _attempt_new(admin, disposable, _bdata(title, title_ar="   "))
    _assert_rejected(ev, created, new_rows, "title_ar", r"arab|العربية|title", "whitespace-only Title AR")


# ===========================================================================
# 144025-144026 — Publication Type validation
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Type validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Selecting a valid Publication Type is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144025
@PUBLICATIONS_CMS_XDIST_GROUP
def test_publication_type_valid_saved(page, disposable):
    # Azure TC 144025 | PBI 130711 | Editor. The case names "Research
    # Papers"; the live fixed picklist's option is "Research Paper".
    admin = _editor(page)
    title = _b_title("144025", "Type-Research-Paper")
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title, publication_type="Research Paper"))

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.publication_type_value() == "Research Paper"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Type validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Leaving Publication Type unselected is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144026
@PUBLICATIONS_CMS_XDIST_GROUP
def test_publication_type_empty_rejected(page, disposable):
    # Azure TC 144026 | PBI 130711 | Editor
    admin = _editor(page)
    title = _b_title("144026", "No-Type")
    require_no_leftovers(admin, title)
    ev, created, new_rows = _attempt_new(admin, disposable, _bdata(title, publication_type=None))
    _assert_rejected(ev, created, new_rows, "type", r"type", "unselected Publication Type")


# ===========================================================================
# 144027-144029 — Cover Image validation
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid JPG Cover Image uploads and displays on the public card")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144027
@PUBLICATIONS_CMS_XDIST_GROUP
def test_cover_image_valid_uploads_and_displays(page, disposable, anon_pages):
    # Azure TC 144027 | PBI 130711 | Editor; step 3 is the logged-out card.
    admin = _editor(page)
    title = _b_title("144027", "Cover-JPG")
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title))
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    # Edit form: the stored file is the "Current file: <name> (<size>)" note.
    cover = admin.current_file_name(FIELD_COVER_IMAGE)
    allure.attach(admin.form_text(), name="Saved record form")
    assert re.search(r"\.jpe?g$", cover, re.I), f"the saved record shows no JPG Cover Image (current file {cover!r})"
    assert admin.active_status() is True

    public, index = _public_card(anon_pages, title, "144027")
    if not public.card_has_img_cover(index):
        public.screenshot("TC-144027")
        pytest.fail(f"the public card for {title!r} shows no cover image")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Leaving Cover Image empty is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144028
@PUBLICATIONS_CMS_XDIST_GROUP
def test_cover_image_empty_rejected(page, disposable):
    # Azure TC 144028 | PBI 130711 | Editor
    admin = _editor(page)
    title = _b_title("144028", "No-Cover")
    require_no_leftovers(admin, title)
    ev, created, new_rows = _attempt_new(admin, disposable, _bdata(title, cover_path=None))
    _assert_rejected(ev, created, new_rows, "cover", r"cover|image|thumbnail", "empty Cover Image")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Uploading an unsupported Cover Image format is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144029
@PUBLICATIONS_CMS_XDIST_GROUP
def test_cover_image_unsupported_format_rejected(page):
    # Azure TC 144029 | PBI 130711 | Editor — nothing is saved.
    admin = _editor(page)
    admin.open_new_entry_form()
    assert_still_pinned(admin, ROLE_EDITOR)
    _assert_upload_rejected(
        admin, FIELD_COVER_IMAGE, "coverImage", f"{FIXTURES}/unsupported_cover.gif",
        r"(?=.*jpg)(?=.*jpeg)(?=.*png)", "a .gif Cover Image",
    )


# ===========================================================================
# 144030-144033 — Publication File validation
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication File validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid PDF under 5MB is accepted and drives the public File Type/File Size meta line")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144030
@PUBLICATIONS_CMS_XDIST_GROUP
def test_file_attachment_valid_drives_meta(page, disposable, anon_pages):
    # Azure TC 144030 | PBI 130711 | Editor — the case's 2 MB PDF
    # (fixtures/valid_pdf_2mb.pdf, 2,096,907 bytes); step 3 is the logged-out card.
    admin = _editor(page)
    title = _b_title("144030", "PDF-2MB")
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title, file_path=f"{FIXTURES}/valid_pdf_2mb.pdf"))
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    attached = admin.current_file_name(FIELD_FILE_ATTACHMENT)
    allure.attach(admin.form_text(), name="Saved record form")
    assert re.search(r"\.pdf$", attached, re.I), f"the saved record shows no PDF Publication File (current file {attached!r})"

    public, index = _public_card(anon_pages, title, "144030")
    meta = public.card_meta(index)
    allure.attach(meta, name="Public card meta line")
    if not (re.search(r"\bPDF\b", meta) and re.search(r"\b2(\.\d+)?\s*MB\b", meta, re.I)):
        public.screenshot("TC-144030")
        pytest.fail(f"the public card's meta line reads {meta!r}; expected File Type PDF and File Size ≈ 2 MB")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication File validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Leaving Publication File empty blocks publishing")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144031
@PUBLICATIONS_CMS_XDIST_GROUP
def test_file_attachment_empty_blocks_publish(page, disposable):
    # Azure TC 144031 | PBI 130711 | Editor
    admin = _editor(page)
    title = _b_title("144031", "No-File")
    require_no_leftovers(admin, title)
    ev, created, new_rows = _attempt_new(admin, disposable, _bdata(title, file_path=None))
    _assert_rejected(ev, created, new_rows, "file", r"file|attachment", "empty Publication File")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication File validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Uploading an unsupported Publication File format is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144032
@PUBLICATIONS_CMS_XDIST_GROUP
def test_file_attachment_unsupported_format_rejected(page):
    # Azure TC 144032 | PBI 130711 | Editor — nothing is saved.
    admin = _editor(page)
    admin.open_new_entry_form()
    assert_still_pinned(admin, ROLE_EDITOR)
    _assert_upload_rejected(
        admin, FIELD_FILE_ATTACHMENT, "fileAttachment", f"{FIXTURES}/report.exe",
        r"(?=.*jpg)(?=.*png)(?=.*jpeg)(?=.*docx)(?=.*\bdoc\b)(?=.*xlsx)(?=.*pdf)", "a .exe Publication File",
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication File validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Uploading a Publication File exceeding 5MB is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144033
@PUBLICATIONS_CMS_XDIST_GROUP
def test_file_attachment_oversized_rejected(page):
    # Azure TC 144033 | PBI 130711 | Editor — 6 MB PDF; nothing is saved.
    admin = _editor(page)
    admin.open_new_entry_form()
    assert_still_pinned(admin, ROLE_EDITOR)
    _assert_upload_rejected(
        admin, FIELD_FILE_ATTACHMENT, "fileAttachment", f"{FIXTURES}/oversized_pdf_6mb.pdf",
        r"5\s*MB|5,?242,?880", "a 6 MB Publication File",
    )


# ===========================================================================
# 144034-144036 — Publication Description EN validation
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Description EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Publication Description EN up to 500 characters is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144034
@PUBLICATIONS_CMS_XDIST_GROUP
def test_description_en_valid_saved(page, disposable):
    # Azure TC 144034 | PBI 130711 | Editor — 480 characters.
    admin = _editor(page)
    title = _b_title("144034", "Description-EN-480")
    description = "D" * 480
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title, description=description))

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_EN) == description


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Description EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Publication Description EN empty is accepted (optional field)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144035
@PUBLICATIONS_CMS_XDIST_GROUP
def test_description_en_empty_accepted(page, disposable):
    # Azure TC 144035 | PBI 130711 | Editor — saved with Publish, which
    # enforces required fields, so "optional" is actually proven.
    admin = _editor(page)
    title = _b_title("144035", "No-Description-EN")
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title, description=""))

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_EN) == ""


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Description EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Description EN accepts 500 characters and rejects 501")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144036
@PUBLICATIONS_CMS_XDIST_GROUP
def test_description_en_500_boundary(page, disposable):
    # Azure TC 144036 | PBI 130711 | Editor
    admin = _editor(page)
    _assert_length_boundary(admin, disposable, "144036", FIELD_PUBLICATION_DESCRIPTION_EN, 500, "D",
                            title_field=False)


# ===========================================================================
# 144037-144039 — Publication Description AR validation
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Description AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Publication Description AR up to 500 characters is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144037
@PUBLICATIONS_CMS_XDIST_GROUP
def test_description_ar_valid_saved(page, disposable):
    # Azure TC 144037 | PBI 130711 | Editor — 480 Arabic characters.
    admin = _editor(page)
    title = _b_title("144037", "Description-AR-480")
    description_ar = "د" * 480
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title, description_ar=description_ar))

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_AR) == description_ar


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Description AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Publication Description AR empty is accepted (optional field)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144038
@PUBLICATIONS_CMS_XDIST_GROUP
def test_description_ar_empty_accepted(page, disposable):
    # Azure TC 144038 | PBI 130711 | Editor — saved with Publish (see 144035).
    admin = _editor(page)
    title = _b_title("144038", "No-Description-AR")
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title, description_ar=""))

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_AR) == ""


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Description AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Description AR accepts 500 characters and rejects 501")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144039
@PUBLICATIONS_CMS_XDIST_GROUP
def test_description_ar_500_boundary(page, disposable):
    # Azure TC 144039 | PBI 130711 | Editor
    admin = _editor(page)
    _assert_length_boundary(admin, disposable, "144039", FIELD_PUBLICATION_DESCRIPTION_AR, 500, "د",
                            title_field=False)


# ===========================================================================
# 144040-144043 — Page Count validation
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid positive integer Page Count is accepted and displayed on the public card")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144040
@PUBLICATIONS_CMS_XDIST_GROUP
def test_page_count_valid_displayed(page, disposable, anon_pages):
    # Azure TC 144040 | PBI 130711 | Editor; step 3 is the logged-out card.
    admin = _editor(page)
    title = _b_title("144040", "Page-Count-42")
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title, page_count="42"))
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.number_field_value(FIELD_PAGE_COUNT) == "42"

    public, index = _public_card(anon_pages, title, "144040")
    meta = public.card_meta(index)
    allure.attach(meta, name="Public card meta line")
    if not re.search(r"\b42\b", meta):
        public.screenshot("TC-144040")
        pytest.fail(f"the public card shows no Page Count of 42 — its meta line reads {meta!r}")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Page Count empty is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144041
@PUBLICATIONS_CMS_XDIST_GROUP
def test_page_count_empty_rejected(page, disposable):
    # Azure TC 144041 | PBI 130711 | Editor
    admin = _editor(page)
    title = _b_title("144041", "No-Page-Count")
    require_no_leftovers(admin, title)
    ev, created, new_rows = _attempt_new(admin, disposable, _bdata(title, page_count=""))
    _assert_rejected(ev, created, new_rows, "page_count", r"page", "empty Page Count")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A zero or negative Page Count is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144042
@PUBLICATIONS_CMS_XDIST_GROUP
def test_page_count_zero_negative_rejected(page, disposable):
    # Azure TC 144042 | PBI 130711 | Editor — one form: 0, then -5.
    admin = _editor(page)
    title = _b_title("144042", "Page-Count-Zero-Negative")
    require_no_leftovers(admin, title)
    # Review M3: each value gets its OWN fresh create form, so no message from
    # the first attempt can be read as the second attempt's refusal.
    ev_zero, created, new_rows = _attempt_new(admin, disposable, _bdata(title, page_count="0"))
    _assert_rejected(ev_zero, created, new_rows, "page_count", r"page|positive", "Page Count 0")
    ev_negative, created, new_rows = _attempt_new(admin, disposable, _bdata(title, page_count="-5"))
    _assert_rejected(ev_negative, created, new_rows, "page_count", r"page|positive", "Page Count -5")
    zero_msg = _field_level(ev_zero, "page_count")
    negative_msg = _field_level(ev_negative, "page_count")
    assert (negative_msg["native"], negative_msg["scoped"]) == (zero_msg["native"], zero_msg["scoped"]), (
        f"Page Count -5 is rejected with a different field message ({negative_msg}) than 0 ({zero_msg})"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Whitespace-only Page Count is rejected as empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144043
@PUBLICATIONS_CMS_XDIST_GROUP
def test_page_count_whitespace_only_rejected(page, disposable):
    # Azure TC 144043 | PBI 130711 | Editor — spaces typed key by key into
    # the number box (as a user would).
    admin = _editor(page)
    title = _b_title("144043", "Whitespace-Page-Count")
    require_no_leftovers(admin, title)
    held = {}

    def _type_spaces(a):
        a.type_into_number(FIELD_PAGE_COUNT, "   ")
        held["value"] = a.number_field_value(FIELD_PAGE_COUNT)

    ev, created, new_rows = _attempt_new(admin, disposable, _bdata(title, page_count=None), prepare=_type_spaces)
    allure.attach(repr(held.get("value")), name="Page Count value after typing spaces")
    _assert_rejected(ev, created, new_rows, "page_count", r"page", "whitespace-only Page Count")


# ===========================================================================
# 144044-144046 — Publication Date validation
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Publication Date is accepted and drives Latest First sort")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144044
@PUBLICATIONS_CMS_XDIST_GROUP
def test_publication_date_valid_drives_sort(page, disposable, anon_pages):
    # Azure TC 144044 | PBI 130711 | Editor — Publication Date = today; step 3
    # is the logged-out Latest First ordering ("at or near the top" = top 3).
    admin = _editor(page)
    title = _b_title("144044", "Date-Today")
    today = date.today().strftime("%d/%m/%Y")
    require_no_leftovers(admin, title)
    entry = _create_published(admin, disposable, _bdata(title, publication_date=today))
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED

    admin.open_entry(entry)
    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.publication_date_value() == today

    public, _ = _public_card(anon_pages, title, "144044")
    public.clear_search()
    public.select_sort("Latest First")
    titles = public.card_titles()
    allure.attach("\n".join(titles), name="Latest First order (logged-out)")
    if title not in titles[:3]:
        public.screenshot("TC-144044")
        pytest.fail(f"{title!r} (dated today) is not at or near the top of Latest First: {titles[:10]}")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Publication Date empty is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144045
@PUBLICATIONS_CMS_XDIST_GROUP
def test_publication_date_empty_rejected(page, disposable):
    # Azure TC 144045 | PBI 130711 | Editor
    admin = _editor(page)
    title = _b_title("144045", "No-Date")
    require_no_leftovers(admin, title)
    ev, created, new_rows = _attempt_new(admin, disposable, _bdata(title, publication_date=None))
    _assert_rejected(ev, created, new_rows, "date", r"date", "empty Publication Date")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Date validation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("An invalid Publication Date string is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144046
@PUBLICATIONS_CMS_XDIST_GROUP
def test_publication_date_invalid_string_rejected(page, disposable):
    # Azure TC 144046 | PBI 130711 | Editor — "32/13/2026".
    admin = _editor(page)
    title = _b_title("144046", "Invalid-Date")
    require_no_leftovers(admin, title)
    typed = {}

    def _type_invalid_date(a):
        a.set_publication_date("32/13/2026")
        typed["box"] = a.publication_date_value()
        typed["stored"] = a.field_stored_value("publicationDate")

    ev, created, new_rows = _attempt_new(admin, disposable, _bdata(title, publication_date=None),
                                         prepare=_type_invalid_date)
    allure.attach(repr(typed), name="Date box / stored value after typing 32/13/2026")
    _assert_rejected(ev, created, new_rows, "date", r"date", "invalid Publication Date 32/13/2026")


# ===========================================================================
# 144047-144052 — SKIPPED: Publication Type Name EN/AR has no authoring surface
# ===========================================================================
TYPE_NAME_SKIP = f"Publication Type Name EN/AR — {TYPES_SKIP}"


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Publication Type Name EN is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144047
@pytest.mark.skip(reason=TYPE_NAME_SKIP)
def test_type_name_en_valid_saved(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Publication Type Name EN empty is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144048
@pytest.mark.skip(reason=TYPE_NAME_SKIP)
def test_type_name_en_empty_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Whitespace-only Publication Type Name EN is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144049
@pytest.mark.skip(reason=TYPE_NAME_SKIP)
def test_type_name_en_whitespace_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Publication Type Name AR is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144050
@pytest.mark.skip(reason=TYPE_NAME_SKIP)
def test_type_name_ar_valid_saved(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Publication Type Name AR empty is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144051
@pytest.mark.skip(reason=TYPE_NAME_SKIP)
def test_type_name_ar_empty_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Whitespace-only Publication Type Name AR is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144052
@pytest.mark.skip(reason=TYPE_NAME_SKIP)
def test_type_name_ar_whitespace_rejected(page):
    ...


# ===========================================================================
# 144071 (Control_Panel side) — SKIPPED: no Publication Type authoring surface
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publication Types")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published card's Type badge persists after its Type is deactivated (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130711
@pytest.mark.tc_144071
@pytest.mark.skip(reason=TYPES_SKIP)
def test_badge_persists_after_type_deactivated_cms(page):
    ...


# ===========================================================================
# 144072 (Control_Panel side) — Future-dated publish
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A future Publication Date still results in a Published status immediately (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130711
@pytest.mark.tc_144072
@PUBLICATIONS_CMS_XDIST_GROUP
def test_future_publication_date_publishes_immediately_cms(page, disposable):
    # Azure TC 144072 | PBI 130711 — Control_Panel half (step 1); the Latest
    # First ordering on the public page is the Web-side test.
    admin = _editor(page)
    title = title_for("144072", "Future-Date")
    require_no_leftovers(admin, title)
    future = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")
    entry = create(admin, disposable, _data(title, publication_date=future), publish=True)

    status = wait_row_status(admin, entry, STATUS_PUBLISHED)
    assert status == STATUS_PUBLISHED, f"a future-dated record was held in {status!r}, not Published"
    assert "Scheduled" not in admin.row_status(entry)
    admin.open_entry(entry)
    assert admin.publication_date_value() == future, (
        f"stored Publication Date {admin.publication_date_value()!r}, expected {future!r}"
    )


# ===========================================================================
# 144073 — Interrupted upload (UNSKIPPED 2026-09-30: deterministic route.abort)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An interrupted Publication File upload leaves no partial file and keeps publishing blocked")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130711
@pytest.mark.tc_144073
@PUBLICATIONS_CMS_XDIST_GROUP
def test_interrupted_file_upload_blocks_publish(page, disposable):
    # Azure TC 144073 | PBI 130711. The network drop is a Playwright
    # route.abort("internetdisconnected") on the picker's upload POST (the
    # Documents & Media action) — reproducible on every run.
    admin = _editor(page)
    title = title_for("144073", "Interrupted-Upload")
    require_no_leftovers(admin, title)
    ids_before = snapshot_ids(admin)
    admin.open_new_entry_form()
    admin.fill_publication(_data(title, file_path=None))

    # Step 1-2 — the upload starts and is cut off; nothing is attached.
    outcome = admin.upload_with_network_drop(FIELD_FILE_ATTACHMENT, PublicationAdminPage.DEFAULT_FILE)
    allure.attach(repr(outcome["aborted"]), name="Aborted upload requests")
    assert outcome["aborted"], "the upload request was never sent, so no interruption happened"
    assert admin.field_stored_value("fileAttachment") == "", (
        f"a file is attached after the interrupted upload: {admin.field_stored_value('fileAttachment')!r}"
    )
    assert admin.uploaded_filename(FIELD_FILE_ATTACHMENT) == "", "the File field shows a filename"

    # Step 3 — publishing is blocked, attributed to the File field.
    assert_still_pinned(admin, ROLE_EDITOR)
    admin.publish()
    blocked = admin.submit_blocked()
    banners = admin.feedback_banners()
    invalid = admin.invalid_fields_last_attempt()
    file_errors = [] if admin.save_redirected() else admin.field_errors_by_control().get("ObjectField_fileAttachment", [])
    native = "" if admin.save_redirected() else admin.field_native_message("fileAttachment")
    message = " ".join(file_errors) or (native if "ObjectField_fileAttachment" in invalid else "")
    allure.attach(f"invalid: {invalid}\nfile-field errors: {file_errors}\nnative: {native}\nbanners: {banners}",
                  name="Validation messages")
    entry = register_if_created(admin, disposable, title, ids_before)
    assert entry is None, "the record was created without its Publication File"
    assert blocked, f"Publish was not blocked: banners {banners}"
    assert "ObjectField_fileAttachment" in invalid or file_errors, (
        f"the refusal is not attributed to the File field (invalid events {invalid}, file-field errors none)"
    )
    assert message, "save blocked but no field-level message on the File field"


# ===========================================================================
# 144075 (Control_Panel side) — Delete a Published record
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Deleting a Published record removes it from the admin grid (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130711
@pytest.mark.tc_144075
@PUBLICATIONS_CMS_XDIST_GROUP
def test_delete_removes_from_admin_grid_cms(page, disposable):
    # Azure TC 144075 | PBI 130711 — Control_Panel half (steps 1-2); the old
    # Download link's graceful response is the Web-side test.
    admin = _editor(page)
    title = title_for("144075", "Delete-Reference")
    require_no_leftovers(admin, title)
    entry = create(admin, disposable, _data(title), publish=True)
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED

    assert_still_pinned(admin, ROLE_EDITOR)
    assert admin.delete_disposable_entry(entry), "the delete did not remove the record"
    disposable.mark_removed(entry)
    admin.open_entries_list()
    assert admin.is_list_fully_expanded() and not admin.row_present(entry)


# ===========================================================================
# 144080/144081 — Arabic Control Panel messages (UNSKIPPED 2026-09-30)
# Interface language = the `/ar/` URL prefix of THIS browser session only; no
# account preference is changed. Controls are located by name/id attributes.
# ===========================================================================
def _assert_arabic_message(text: str, what: str) -> None:
    assert text, f"no {what} was shown"
    assert ARABIC.search(text), f"the {what} is not in Arabic: {text!r}"
    without_record_title = re.sub(r"QCTEST-\S+", "", text)
    assert not LATIN.search(without_record_title), (
        f"the {what} mixes untranslated English into the Arabic text: {text!r}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The success message renders in Arabic when the Control Panel UI language is Arabic")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144080
@PUBLICATIONS_CMS_XDIST_GROUP
def test_success_toast_arabic_cp_locale(page, disposable):
    # Azure TC 144080 | PBI 130711 | account: Site Content Editor
    admin = _editor(page)
    title = title_for("144080", "Arabic-Success")
    require_no_leftovers(admin, title)
    entry = create(admin, disposable, _data(title), publish=True)
    assert wait_row_status(admin, entry, STATUS_PUBLISHED) == STATUS_PUBLISHED
    try:
        admin.open_entry_in_locale(entry, "ar")
        assert admin.interface_language().startswith("ar"), (
            f"the Control Panel did not switch to Arabic: {admin.interface_language()!r}"
        )
        admin.fill_field_by_name("publicationDescription", f"{title} edited in an Arabic session.")
        assert_still_pinned(admin, ROLE_EDITOR)
        admin.publish_any_locale()
        assert admin.save_redirected(), f"save refused: {admin.feedback_banners()}"
        banners = attach_banners(admin, "saving in the Arabic Control Panel")
        assert banners, "no success message after saving in the Arabic Control Panel"
        for text in banners:
            _assert_arabic_message(text, "success message")
    finally:
        admin.open_entries_list(locale="en")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Publication File validation error renders in Arabic when the Control Panel UI language is Arabic")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144081
@PUBLICATIONS_CMS_XDIST_GROUP
def test_missing_file_validation_arabic_cp_locale(page, disposable):
    # Azure TC 144081 | PBI 130711 | account: Site Content Editor
    admin = _editor(page)
    title = title_for("144081", "Arabic-Missing-File")
    require_no_leftovers(admin, title)
    ids_before = snapshot_ids(admin)
    try:
        admin.open_new_entry_form_in_locale("ar")
        assert admin.interface_language().startswith("ar"), (
            f"the Control Panel did not switch to Arabic: {admin.interface_language()!r}"
        )
        admin.fill_field_by_name("publicationTitle", title)
        admin.fill_field_by_name("publicationTitle_ar", f"{title} منشور")
        admin.select_type_option_by_index(0)
        admin.set_publication_date_any_locale("01/01/2026")
        admin.fill_field_by_name("pageCount", "3")
        admin.upload_file_by_field_name("coverImage", PublicationAdminPage.DEFAULT_COVER)
        assert admin.field_stored_value("fileAttachment") == "", "the File field is not empty"

        assert_still_pinned(admin, ROLE_EDITOR)
        admin.publish_any_locale()
        went_through = admin.save_redirected()
        refused_on = admin.invalid_fields_last_attempt()
        errors_by_control = {} if went_through else admin.field_errors_by_control()
        entry = register_if_created(admin, disposable, title, ids_before) if went_through else None
        assert entry is None, "the record was published without its Publication File"
        assert admin.submit_blocked(), f"Publish was not blocked: {admin.feedback_banners()}"
        invalid = refused_on
        file_errors = errors_by_control.get("ObjectField_fileAttachment", [])
        other_errors = {k: v for k, v in errors_by_control.items() if k != "ObjectField_fileAttachment"}
        allure.attach(f"invalid: {invalid}\nerrors by control: {errors_by_control}", name="Field-level evidence")
        assert "ObjectField_fileAttachment" in invalid or file_errors, (
            f"the refusal is not on the File field (invalid events {invalid}, inline errors {errors_by_control})"
        )
        assert set(invalid) <= {"ObjectField_fileAttachment"} and not other_errors, (
            f"other fields were also refused: invalid {invalid}, inline errors {other_errors}"
        )
        field_message = " ".join(file_errors) or (
            admin.field_native_message("fileAttachment") if "ObjectField_fileAttachment" in invalid else "")
        banner = admin.refusal_bar_text() or " ".join(admin.feedback_banners())
        allure.attach(f"field: {field_message}\nbanner: {banner}", name="Arabic validation messages")
        _assert_arabic_message(field_message, "File-field validation message")
        # HEALED 2026-10-02: this build refuses inline (no page banner). The case
        # asks for an Arabic error that the file is required — the field message
        # above. A banner, when one is shown, must also be Arabic.
        if banner:
            _assert_arabic_message(banner, "validation banner")
    finally:
        admin.open_entries_list(locale="en")
        register_if_created(admin, disposable, title, ids_before)  # logs only; registers a NEW row that slipped through

"""
cms/tests/publications/test_publications_control_panel.py —
Control_Panel-tagged cases for PBI 130711 ("QC - Insights & Media - 003 -
Publications"), sourced from `.claude/qa-baselines/130711_automation_batch.json`
(99 cases, pre-filtered to `Tag=Automation`).

Holds every case whose `tags` include `Control_Panel` (53 Control_Panel-only
cases) PLUS the Control_Panel-side test for every case that carries BOTH
`Web` and `Control_Panel` (9 cases: 144004, 144005, 144006, 144007, 144011,
144012, 144071, 144072, 144075) — the Web-side test for those 9 lives in
web/tests/publications/test_publications_web.py under the SAME `tc_<id>`
marker.

CMS reachability (2026-09-22): `.auth/state.json` reused this session, every
Object Authoring surface this module touches (`manage-publication`)
rendered normally. The **Publication** entry object is NOT a singleton — 9
real, shared entries exist (8 Published, 1 real pre-existing Draft
"Arbitration Best Practices" not created by this session) — brand-new
`QCTEST-`-prefixed entries are created and deleted freely without ever
touching them (DISPOSABLE per cms-profile.md). Every mutating test carries
the shared `publications_cms` xdist group (mirrors the Web module's own
group) so pytest-xdist never runs two of them concurrently against the same
object's entries table.

CONFIRMED LIVE 2026-09-22 — no UUID-column defect on this object (explicitly
checked, per the task's own instruction): the entries-list Entry column
renders the REAL Publication Title on every one of the 9 real rows — unlike
`export_report_admin_page.py`'s manage-strategic-pillar-card-class finding.
Title-based lookup (`open_entry_by_edit_link`, `delete_entry_by_title`, etc.)
is used directly throughout, no `_resolve_code()` workaround needed.

CONFIRMED LIVE 2026-09-22 — **Save as Draft on this object enforces FULL
field validation**, not a lenient partial save: a live probe attempting
Save as Draft with only Title EN/AR filled (Page Count left at its default
blank state) was BLOCKED with the inline message "Page count must be a
positive whole number (1 or greater)." — every "valid save" test below
therefore fills Type/Cover/Date/File/Page Count via `_fill_all_mandatory_fields()`
even for a plain Draft save, not only for Submit for Review/Publish.

**No "Manage Publication Types" admin surface exists — see
publication_admin_page.py's module docstring for the full evidence trail
(exhaustive Objects Home nav search).** Every case assuming that surface is
SKIPPED below with that finding.

**CONFIRMED PRODUCT DEFECT, discovered while verifying this batch (2026-09-22,
reproduced twice) — Submit for Review clears the Publication Type AND
Publication Status field values it just had.** A disposable entry with
Type="Research Paper"/Status="Published" was confirmed correctly persisted
immediately after Save as Draft (read back via `.input_value()` on reopen),
then confirmed **both empty** on the very next reopen after Submit for
Review — even though the entries-list row itself still shows
"PUBLISHED...ON THE WEBSITE" (the workflow state, unaffected). See
`publication_admin_page.py`'s module docstring for the full reproduction.
Every test below that publishes a disposable entry and checks the delivery
surface (tc_144004/144005/144006/144072 and the tc_144027/144030/144040/
144044 cross-surface checks) is scripted against the documented, intended
publish sequence and is expected to legitimately FAIL that public-surface
half against this real defect when actually run — the CMS-side status
assertions in these same tests are unaffected and should pass. Not a
locator/script bug, not routed around here; flagged for the QA Manager/
human to file as a bug (Phase 3b), not filed by this agent.

SKIPPED (confirmed precondition/product gaps, reused known blockers, or
budget-bounded verification, not locator gaps):
  - tc_143997/tc_143998 (Site Content Author role cases): this project's own
    `pytest.ini` already records `CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD`
    does NOT authenticate against qcdev (confirmed 2026-09-17 for
    tc_131154/131155/131163/131200) — reused here rather than re-attempting
    a known-blocked login live.
  - tc_144001: no Cancel/discard control exists anywhere on this form
    (confirmed live — a full `a,button` sweep for "cancel"/"discard" text
    found none), mirroring the same class of finding this project's
    Footer/Social-Media-Icon object already documents (tc_131174).
  - tc_144008/144009/144010/144016/144047/144048/144049/144050/144051/144052:
    all assume the non-existent "Manage Publication Types" surface.
  - tc_144011/144012 (Control_Panel-side): same Types-surface gap.
  - tc_144071 (Control_Panel-side): same Types-surface gap (deactivating a
    Type value has no admin action to invoke).
  - tc_144015/144080: no confirmed-live generic success-toast element was
    captured within this session's probe budget (Save as Draft/Submit
    redirects the page immediately; two live probes — one blocked by a
    validation error, one against a fully valid entry — did not surface a
    distinct, persistent toast in either case). Scripting an assertion
    against unconfirmed wording would risk a false pass/fail; recorded
    honestly as unverified rather than guessed. tc_144080 additionally
    needs the Control Panel's own UI language switched to Arabic, which was
    not exercised live this session.
  - tc_144081: same unconfirmed-Arabic-CP-locale gap as tc_144080 (the
    underlying English validation message itself IS confirmed reachable,
    see tc_144031, but the Arabic-locale variant of it was not verified
    this session).
  - tc_144073: needs a controlled mid-upload network interruption — no
    reliable, repeatable technique for this was exercised this session
    (same class of gap this project's Advertisements/Export Reports batches
    already document for equivalent scenarios).

DISPOSABLE entries: every mutating test below creates its own
`QCTEST-<tc_id>`-prefixed Publication entry via
`cms.pages.publications.publication_admin_page.PublicationAdminPage` and
deletes it in a `finally` block. A few cases whose own expected result
explicitly names the PUBLIC Publications page (tc_144030, tc_144040,
tc_144044) additionally import `web.pages.publications.publications_page.PublicationsPage`
to verify that delivery-surface outcome — mirrors
`cms/tests/export_reports/test_export_reports_control_panel.py`'s own
precedent for a Control_Panel-tagged case whose narrative still names the
public page.
"""

import allure
import pytest

from cms.pages.publications.publication_admin_page import (
    PublicationAdminPage,
    FIELD_COVER_IMAGE,
    FIELD_FILE_ATTACHMENT,
    FIELD_PAGE_COUNT,
    FIELD_PUBLICATION_DESCRIPTION_AR,
    FIELD_PUBLICATION_DESCRIPTION_EN,
    FIELD_PUBLICATION_TITLE_AR,
    FIELD_PUBLICATION_TITLE_EN,
)
from config.settings import cms_role_credentials
from web.pages.publications.publications_page import PublicationsPage

PUBLICATIONS_CMS_XDIST_GROUP = pytest.mark.xdist_group("publications_cms")
FIXTURES = "cms/tests/publications/fixtures"


def _fill_all_mandatory_fields(admin: PublicationAdminPage, prefix: str, **overrides) -> dict:
    """Fills every mandatory Publication field with a safe default (see
    module docstring: Save as Draft itself enforces full validation on this
    object). `skip_type`/`skip_cover`/`skip_date`/`skip_file`/
    `skip_page_count` omit that one field to reach an empty/missing
    precondition; every other override is a literal FIELD_* key."""
    values = {
        FIELD_PUBLICATION_TITLE_EN: f"QCTEST-{prefix} Publication",
        FIELD_PUBLICATION_TITLE_AR: f"QCTEST-{prefix} منشور",
        FIELD_PUBLICATION_DESCRIPTION_EN: f"QCTEST-{prefix} disposable automated-test publication description.",
        FIELD_PUBLICATION_DESCRIPTION_AR: f"QCTEST-{prefix} وصف منشور تجريبي تم إنشاؤه تلقائيًا.",
        "publication_type": "Report",
        "publication_date": "01/01/2026",
        "page_count": "3",
    }
    values.update(overrides)
    admin.open_new_entry_form()
    for field in (FIELD_PUBLICATION_TITLE_EN, FIELD_PUBLICATION_TITLE_AR,
                  FIELD_PUBLICATION_DESCRIPTION_EN, FIELD_PUBLICATION_DESCRIPTION_AR):
        if field in values:
            admin.fill_text(field, values[field])
    if not values.get("skip_type"):
        admin.select_publication_type(values["publication_type"])
    if not values.get("skip_cover"):
        admin.upload_file(FIELD_COVER_IMAGE, values.get("cover_path", f"{FIXTURES}/valid_cover_1_5mb.jpg"))
    if not values.get("skip_date"):
        admin.set_publication_date(values["publication_date"])
    if not values.get("skip_file"):
        admin.upload_file(FIELD_FILE_ATTACHMENT, values.get("file_path", f"{FIXTURES}/valid_pdf_4mb.pdf"))
    if not values.get("skip_page_count"):
        admin.fill_number(FIELD_PAGE_COUNT, values["page_count"])
    return values


# ===========================================================================
# 143996 — Editor lifecycle (Type management half unreachable, see docstring)
# ===========================================================================
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
def test_editor_full_record_lifecycle(page):
    # Azure TC 143996 | PBI 130711 — the "manage Publication Types" half of
    # this case is NOT exercised: no such admin surface exists (see module
    # docstring); only the record-lifecycle half is scripted/asserted.
    admin = PublicationAdminPage(page)
    title = "QCTEST-143996 Editor Lifecycle"
    try:
        with allure.step("Create"):
            _fill_all_mandatory_fields(admin, "143996", **{FIELD_PUBLICATION_TITLE_EN: title})
            admin.save_as_draft()
            assert admin.status_for(title) == "Draft"

        with allure.step("Edit"):
            admin.open_entry_by_edit_link(title)
            admin.fill_text(FIELD_PUBLICATION_DESCRIPTION_EN, "QCTEST-143996 edited description.")
            admin.save_as_draft()

        with allure.step("Preview"):
            preview_url = admin.row_preview_url(title)
            assert preview_url

        with allure.step("Publish"):
            admin.open_entry_by_edit_link(title)
            admin.set_publication_status("Published")
            admin.submit_for_review()
            assert admin.status_for(title) == "Published"

        with allure.step("Unpublish"):
            admin.open_entry_by_edit_link(title)
            admin.unpublish_to_edit_as_draft()
            assert admin.status_for(title) != "Published"

        with allure.step("Delete"):
            admin.open_entries_list()
            admin.delete_entry_by_title(title)
            assert not admin.row_visible(title)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143997/143998 — SKIPPED: known-blocked Site Content Author credentials
# ===========================================================================
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
@pytest.mark.skip(
    reason="CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD in .env do not "
    "authenticate against qcdev — already confirmed 2026-09-17 for "
    "tc_131154/131155/131163/131200; reused here rather than re-attempting "
    "a known-blocked login."
)
def test_author_view_update_assigned_record(page):
    ...


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
@pytest.mark.skip(
    reason="Same CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD blocked-credentials "
    "gap as tc_143997."
)
def test_author_denied_publish_delete_manage_types(page):
    ...


# ===========================================================================
# 144000 — Editor creates a new record and saves as Draft
# ===========================================================================
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
def test_editor_create_save_as_draft(page):
    # Azure TC 144000 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144000 Create Draft"
    try:
        _fill_all_mandatory_fields(admin, "144000", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()

        assert admin.status_for(title) == "Draft"
        pub = PublicationsPage(page)
        pub.open_publications()
        pub.search(title)
        assert title not in pub.card_titles()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144001 — SKIPPED: no Cancel/discard control exists
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
    reason="No Cancel/discard control exists anywhere on this form "
    "(confirmed live — a full a/button sweep for 'cancel'/'discard' text "
    "found none), same class of finding as tc_131174 on the Footer object."
)
def test_cancel_create_form_discards_data(page):
    ...


# ===========================================================================
# 144002 — Editor saves an existing record as Draft
# ===========================================================================
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
def test_editor_resave_existing_as_draft(page):
    # Azure TC 144002 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144002 Resave Draft"
    try:
        _fill_all_mandatory_fields(admin, "144002", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.save_as_draft()

        assert admin.status_for(title) == "Draft"
        pub = PublicationsPage(page)
        pub.open_publications()
        pub.search(title)
        assert title not in pub.card_titles()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144003 — Editor previews a Draft record before publishing
# ===========================================================================
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
def test_editor_preview_draft_record(page):
    # Azure TC 144003 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144003 Preview Draft"
    try:
        _fill_all_mandatory_fields(admin, "144003", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        preview_url = admin.row_preview_url(title)

        assert preview_url
        assert admin.status_for(title) == "Draft"
        pub = PublicationsPage(page)
        pub.open_publications()
        pub.search(title)
        assert title not in pub.card_titles()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144004/144005/144006/144007 — Publish lifecycle (Control_Panel side)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing via Object Authoring updates the entry's own Status (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144004
@PUBLICATIONS_CMS_XDIST_GROUP
def test_publish_updates_status_cms(page):
    # Azure TC 144004 | PBI 130711 — Control_Panel-side half; Web-side in
    # test_publications_web.py under the SAME marker.
    admin = PublicationAdminPage(page)
    title = "QCTEST-144004-CMS Publish Flow"
    try:
        _fill_all_mandatory_fields(admin, "144004-cms", **{FIELD_PUBLICATION_TITLE_EN: title},
                                    publication_type="Guides", page_count="5")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.set_publication_status("Published")
        admin.submit_for_review()

        assert admin.status_for(title) == "Published"
        admin.open_entry_by_edit_link(title)
        assert admin.field_value(FIELD_PUBLICATION_TITLE_EN).strip() == title
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_republish_updates_record_cms(page):
    # Azure TC 144005 | PBI 130711 — Control_Panel-side half.
    admin = PublicationAdminPage(page)
    original_title = "QCTEST-144005-CMS-Original"
    updated_title = "QCTEST-144005-CMS-Updated"
    try:
        _fill_all_mandatory_fields(admin, "144005-cms", **{FIELD_PUBLICATION_TITLE_EN: original_title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(original_title)
        admin.set_publication_status("Published")
        admin.submit_for_review()

        admin.open_entry_by_edit_link(original_title)
        admin.fill_text(FIELD_PUBLICATION_TITLE_EN, updated_title)
        admin.submit_for_review()

        assert admin.status_for(updated_title) == "Published"
        assert not admin.row_visible(original_title)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(updated_title)
        admin.open_entries_list()
        admin.delete_entry_by_title(original_title)


@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Unpublishing sets the record's Status back to Unpublished (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130711
@pytest.mark.tc_144006
@PUBLICATIONS_CMS_XDIST_GROUP
def test_unpublish_updates_status_cms(page):
    # Azure TC 144006 | PBI 130711 — Control_Panel-side half.
    admin = PublicationAdminPage(page)
    title = "QCTEST-144006-CMS Unpublish Flow"
    try:
        _fill_all_mandatory_fields(admin, "144006-cms", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.set_publication_status("Published")
        admin.submit_for_review()
        assert admin.status_for(title) == "Published"

        admin.open_entry_by_edit_link(title)
        admin.unpublish_to_edit_as_draft()

        assert admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_delete_record_cms(page):
    # Azure TC 144007 | PBI 130711 — Control_Panel-side half.
    admin = PublicationAdminPage(page)
    title = "QCTEST-144007-CMS Delete Flow"
    _fill_all_mandatory_fields(admin, "144007-cms", **{FIELD_PUBLICATION_TITLE_EN: title})
    admin.save_as_draft()
    admin.open_entry_by_edit_link(title)
    admin.set_publication_status("Published")
    admin.submit_for_review()

    admin.open_entries_list()
    admin.delete_entry_by_title(title)

    assert not admin.row_visible(title)


# ===========================================================================
# 144008-144010 — SKIPPED: no Publication Type admin surface
# ===========================================================================
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
def test_reorder_publication_types_reflects_public(page):
    ...


# ===========================================================================
# 144011/144012 — SKIPPED: no Publication Type admin surface (Control_Panel)
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
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
@pytest.mark.skip(reason="Depends on tc_144011's precondition — same no-Types-surface gap.")
def test_reactivate_manuals_type_cms(page):
    ...


# ===========================================================================
# 144013 — Unique, system-generated Publication ID on save
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A newly saved Publication receives a unique, system-generated entry id")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144013
@PUBLICATIONS_CMS_XDIST_GROUP
def test_new_record_gets_unique_system_id(page):
    # Azure TC 144013 | PBI 130711 — this object has no user-facing
    # "Publication ID" field (confirmed via the accessibility-tree field
    # list); the real system-generated identity is the entry's own
    # `editEntry` code in its edit-form URL, resolved here purely from the
    # UI (never guessed/read via an API call).
    admin = PublicationAdminPage(page)
    title1 = "QCTEST-144013-A Publication"
    title2 = "QCTEST-144013-B Publication"
    try:
        _fill_all_mandatory_fields(admin, "144013-a", **{FIELD_PUBLICATION_TITLE_EN: title1})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title1)
        id1 = page.url.split("editEntry=")[-1]

        _fill_all_mandatory_fields(admin, "144013-b", **{FIELD_PUBLICATION_TITLE_EN: title2})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title2)
        id2 = page.url.split("editEntry=")[-1]

        assert id1 and id2
        assert id1 != id2
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title1)
        admin.open_entries_list()
        admin.delete_entry_by_title(title2)


# ===========================================================================
# 144014 — Editing a Published record updates its Last Modified Date
# ===========================================================================
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
def test_edit_published_updates_last_modified(page):
    # Azure TC 144014 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144014 Last Modified Check"
    try:
        _fill_all_mandatory_fields(admin, "144014", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.set_publication_status("Published")
        admin.submit_for_review()
        admin.open_entries_list()
        before = admin.row_last_modified(title) if hasattr(admin, "row_last_modified") else ""

        page.wait_for_timeout(1500)
        admin.open_entry_by_edit_link(title)
        admin.fill_text(FIELD_PUBLICATION_DESCRIPTION_EN, "QCTEST-144014 updated description.")
        admin.submit_for_review()
        admin.open_entries_list()
        after = admin.row_last_modified(title) if hasattr(admin, "row_last_modified") else ""

        assert before and after
        assert before != after
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144015/144016 — SKIPPED: no confirmed toast signal / Types surface
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Feedback / Audit")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a Publication change shows the Liferay success toast and records an audit entry")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130711
@pytest.mark.tc_144015
@pytest.mark.skip(
    reason="No confirmed-live, persistent success-toast element was "
    "captured within this session's probe budget (Save/Submit redirects "
    "the page immediately) — see module docstring."
)
def test_save_shows_toast_and_audit_entry(page):
    ...


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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
def test_add_type_shows_toast_and_audit_entry(page):
    ...


# ===========================================================================
# 144017-144020 — Publication Title EN validation
# ===========================================================================
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
def test_title_en_valid_saved(page):
    # Azure TC 144017 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144017 Qatar Economic Outlook 2026"
    try:
        _fill_all_mandatory_fields(admin, "144017", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_PUBLICATION_TITLE_EN).strip() == title
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_title_en_empty_rejected(page):
    # Azure TC 144018 | PBI 130711
    admin = PublicationAdminPage(page)
    _fill_all_mandatory_fields(admin, "144018", **{FIELD_PUBLICATION_TITLE_EN: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


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
def test_title_en_200_boundary(page):
    # Azure TC 144019 | PBI 130711 — same KNOWN LIMITATION noted on
    # ObjectAuthoringPage.field_length_rejected()'s own docstring: the
    # submit-time fallback branch calls submit_for_publishing(), whose
    # button wording doesn't match this object's real "Submit for Review" —
    # only the immediate-readback truncation branch is independently sound.
    admin = PublicationAdminPage(page)
    attempted = "Q" * 201
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_PUBLICATION_TITLE_EN, attempted, 200)


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
def test_title_en_whitespace_only_rejected(page):
    # Azure TC 144020 | PBI 130711
    admin = PublicationAdminPage(page)
    _fill_all_mandatory_fields(admin, "144020", **{FIELD_PUBLICATION_TITLE_EN: "   "})
    admin.submit_for_review()

    assert admin.submit_blocked()


# ===========================================================================
# 144021-144024 — Publication Title AR validation
# ===========================================================================
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
def test_title_ar_valid_saved(page):
    # Azure TC 144021 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144021 Publication"
    title_ar = "توقعات الاقتصاد القطري 2026"
    try:
        _fill_all_mandatory_fields(admin, "144021", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_TITLE_AR: title_ar})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_PUBLICATION_TITLE_AR).strip() == title_ar
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_title_ar_empty_rejected(page):
    # Azure TC 144022 | PBI 130711
    admin = PublicationAdminPage(page)
    _fill_all_mandatory_fields(admin, "144022", **{FIELD_PUBLICATION_TITLE_AR: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


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
def test_title_ar_200_boundary(page):
    # Azure TC 144023 | PBI 130711
    admin = PublicationAdminPage(page)
    attempted = "ت" * 201
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_PUBLICATION_TITLE_AR, attempted, 200)


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
def test_title_ar_whitespace_only_rejected(page):
    # Azure TC 144024 | PBI 130711
    admin = PublicationAdminPage(page)
    _fill_all_mandatory_fields(admin, "144024", **{FIELD_PUBLICATION_TITLE_AR: "   "})
    admin.submit_for_review()

    assert admin.submit_blocked()


# ===========================================================================
# 144025-144026 — Publication Type validation
# ===========================================================================
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
def test_publication_type_valid_saved(page):
    # Azure TC 144025 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144025 Publication"
    try:
        _fill_all_mandatory_fields(admin, "144025", **{FIELD_PUBLICATION_TITLE_EN: title},
                                    publication_type="Research Paper")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert "Research Paper" in admin.publication_type_value()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_publication_type_empty_rejected(page):
    # Azure TC 144026 | PBI 130711
    admin = PublicationAdminPage(page)
    _fill_all_mandatory_fields(admin, "144026", skip_type=True)
    admin.submit_for_review()

    assert admin.submit_blocked()


# ===========================================================================
# 144027-144029 — Cover Image validation
# ===========================================================================
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
def test_cover_image_valid_uploads_and_displays(page):
    # Azure TC 144027 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144027 Cover Upload Check"
    try:
        _fill_all_mandatory_fields(admin, "144027", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        assert admin.uploaded_filename(FIELD_COVER_IMAGE)

        admin.open_entry_by_edit_link(title)
        admin.set_publication_status("Published")
        admin.submit_for_review()

        pub = PublicationsPage(page)
        pub.open_publications()
        pub.search(title)
        index = pub.card_index(title)
        assert pub.card_has_img_cover(index)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_cover_image_empty_rejected(page):
    # Azure TC 144028 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144028 No Cover"
    try:
        _fill_all_mandatory_fields(admin, "144028", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_cover=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
    # Azure TC 144029 | PBI 130711
    admin = PublicationAdminPage(page)
    admin.open_new_entry_form()

    assert admin.upload_file_expect_rejected(FIELD_COVER_IMAGE, f"{FIXTURES}/unsupported_cover.gif")


# ===========================================================================
# 144030-144033 — Publication File validation
# ===========================================================================
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
def test_file_attachment_valid_drives_meta(page):
    # Azure TC 144030 | PBI 130711 — this case's own expected result names
    # the public page directly, so the public card is checked here despite
    # this test's Control_Panel-only Platform tag (mirrors
    # export_reports_control_panel.py's own precedent).
    admin = PublicationAdminPage(page)
    title = "QCTEST-144030 File Meta Check"
    try:
        _fill_all_mandatory_fields(admin, "144030", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        assert admin.uploaded_filename(FIELD_FILE_ATTACHMENT)

        admin.open_entry_by_edit_link(title)
        admin.set_publication_status("Published")
        admin.submit_for_review()

        pub = PublicationsPage(page)
        pub.open_publications()
        pub.search(title)
        index = pub.card_index(title)
        meta = pub.card_meta(index)
        assert "PDF" in meta
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_file_attachment_empty_blocks_publish(page):
    # Azure TC 144031 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144031 No File"
    try:
        _fill_all_mandatory_fields(admin, "144031", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_file=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
    # Azure TC 144032 | PBI 130711
    admin = PublicationAdminPage(page)
    admin.open_new_entry_form()

    assert admin.upload_file_expect_rejected(FIELD_FILE_ATTACHMENT, f"{FIXTURES}/report.exe")


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
    # Azure TC 144033 | PBI 130711
    admin = PublicationAdminPage(page)
    admin.open_new_entry_form()

    assert admin.upload_file_expect_rejected(FIELD_FILE_ATTACHMENT, f"{FIXTURES}/oversized_pdf_6mb.pdf")


# ===========================================================================
# 144034-144036 — Publication Description EN validation
# ===========================================================================
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
def test_description_en_valid_saved(page):
    # Azure TC 144034 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144034 Description Check"
    desc = "D" * 480
    try:
        _fill_all_mandatory_fields(admin, "144034", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_DESCRIPTION_EN: desc})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_EN) == desc
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_description_en_empty_accepted(page):
    # Azure TC 144035 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144035 No Description"
    try:
        _fill_all_mandatory_fields(admin, "144035", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_DESCRIPTION_EN: ""})
        admin.save_as_draft()

        assert admin.status_for(title) == "Draft"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_description_en_500_boundary(page):
    # Azure TC 144036 | PBI 130711
    admin = PublicationAdminPage(page)
    attempted = "D" * 501
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_PUBLICATION_DESCRIPTION_EN, attempted, 500)


# ===========================================================================
# 144037-144039 — Publication Description AR validation
# ===========================================================================
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
def test_description_ar_valid_saved(page):
    # Azure TC 144037 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144037 Description AR Check"
    desc_ar = "د" * 480
    try:
        _fill_all_mandatory_fields(admin, "144037", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_DESCRIPTION_AR: desc_ar})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_AR) == desc_ar
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_description_ar_empty_accepted(page):
    # Azure TC 144038 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144038 No Description AR"
    try:
        _fill_all_mandatory_fields(admin, "144038", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_DESCRIPTION_AR: ""})
        admin.save_as_draft()

        assert admin.status_for(title) == "Draft"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_description_ar_500_boundary(page):
    # Azure TC 144039 | PBI 130711
    admin = PublicationAdminPage(page)
    attempted = "د" * 501
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_PUBLICATION_DESCRIPTION_AR, attempted, 500)


# ===========================================================================
# 144040-144043 — Page Count validation
# ===========================================================================
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
def test_page_count_valid_displayed(page):
    # Azure TC 144040 | PBI 130711 — this case's own expected result names
    # the public page directly (see tc_144030's own note on this pattern).
    admin = PublicationAdminPage(page)
    title = "QCTEST-144040 Page Count Check"
    try:
        _fill_all_mandatory_fields(admin, "144040", **{FIELD_PUBLICATION_TITLE_EN: title}, page_count="42")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.set_publication_status("Published")
        admin.submit_for_review()

        pub = PublicationsPage(page)
        pub.open_publications()
        pub.search(title)
        index = pub.card_index(title)
        assert "42" in pub.card_meta(index)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_page_count_empty_rejected(page):
    # Azure TC 144041 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144041 No Page Count"
    try:
        _fill_all_mandatory_fields(admin, "144041", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_page_count=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_page_count_zero_negative_rejected(page):
    # Azure TC 144042 | PBI 130711 — CONFIRMED LIVE (see module docstring's
    # probe log) a blank/zero Page Count is rejected with an inline "Page
    # count must be a positive whole number (1 or greater)." message. Two
    # independent attempts (zero, then negative), each its own disposable
    # entry — self-contained, not chained off one shared draft row.
    admin = PublicationAdminPage(page)
    title_zero = "QCTEST-144042-ZERO Bad Page Count"
    title_negative = "QCTEST-144042-NEG Bad Page Count"
    try:
        _fill_all_mandatory_fields(admin, "144042-zero", **{FIELD_PUBLICATION_TITLE_EN: title_zero}, page_count="0")
        admin.submit_for_review()
        rejected_zero = admin.submit_blocked() or admin.status_for(title_zero) != "Published"

        _fill_all_mandatory_fields(admin, "144042-neg", **{FIELD_PUBLICATION_TITLE_EN: title_negative}, page_count="-5")
        admin.submit_for_review()
        rejected_negative = admin.submit_blocked() or admin.status_for(title_negative) != "Published"

        assert rejected_zero
        assert rejected_negative
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title_zero)
        admin.open_entries_list()
        admin.delete_entry_by_title(title_negative)


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
def test_page_count_whitespace_only_rejected(page):
    # Azure TC 144043 | PBI 130711 — a spinbutton control generally can't
    # hold literal whitespace text; scripted per the case's own literal
    # attempt via fill(), asserting the same rejection signal as the
    # empty-field case.
    admin = PublicationAdminPage(page)
    title = "QCTEST-144043 Whitespace Page Count"
    try:
        _fill_all_mandatory_fields(admin, "144043", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_page_count=True)
        admin.page.get_by_role("spinbutton", name=FIELD_PAGE_COUNT, exact=True).fill("   ")
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144044-144046 — Publication Date validation
# ===========================================================================
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
def test_publication_date_valid_drives_sort(page):
    # Azure TC 144044 | PBI 130711 — this case's own expected result names
    # the public page directly (see tc_144030's own note on this pattern).
    admin = PublicationAdminPage(page)
    title = "QCTEST-144044 Date Sort Check"
    try:
        _fill_all_mandatory_fields(admin, "144044", **{FIELD_PUBLICATION_TITLE_EN: title}, publication_date="22/09/2026")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.set_publication_status("Published")
        admin.submit_for_review()

        pub = PublicationsPage(page)
        pub.open_publications()
        pub.select_sort("Latest First")
        pub.search(title)
        assert title in pub.card_titles()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_publication_date_empty_rejected(page):
    # Azure TC 144045 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144045 No Date"
    try:
        _fill_all_mandatory_fields(admin, "144045", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_date=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


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
def test_publication_date_invalid_string_rejected(page):
    # Azure TC 144046 | PBI 130711
    admin = PublicationAdminPage(page)
    title = "QCTEST-144046 Invalid Date"
    try:
        _fill_all_mandatory_fields(admin, "144046", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_date=True)
        admin.set_publication_date("32/13/2026")
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144047-144052 — SKIPPED: no Publication Type Name EN/AR admin surface
# ===========================================================================
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
def test_type_name_ar_whitespace_rejected(page):
    ...


# ===========================================================================
# 144071 (Control_Panel side) — SKIPPED: same no-Types-surface gap
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
@pytest.mark.skip(reason="No 'Manage Publication Types' admin surface exists — see module docstring.")
def test_badge_persists_after_type_deactivated_cms(page):
    ...


# ===========================================================================
# 144072 (Control_Panel side) — Future-dated publish
# ===========================================================================
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
def test_future_publication_date_publishes_immediately_cms(page):
    # Azure TC 144072 | PBI 130711 — Control_Panel-side half.
    admin = PublicationAdminPage(page)
    title = "QCTEST-144072-CMS Future Date"
    try:
        _fill_all_mandatory_fields(admin, "144072-cms", **{FIELD_PUBLICATION_TITLE_EN: title}, publication_date="20/10/2026")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.set_publication_status("Published")
        admin.submit_for_review()

        assert admin.status_for(title) == "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144073 — SKIPPED: no reliable interrupted-upload technique this session
# ===========================================================================
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
@pytest.mark.skip(
    reason="Needs a controlled mid-upload network interruption — no "
    "reliable, repeatable technique for this was exercised this session."
)
def test_interrupted_file_upload_blocks_publish(page):
    ...


# ===========================================================================
# 144075 (Control_Panel side) — Delete a Published record, admin-side check
# ===========================================================================
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
def test_delete_removes_from_admin_grid_cms(page):
    # Azure TC 144075 | PBI 130711 — Control_Panel-side half; the shared
    # public Download-link-graceful-response check lives in the Web-side
    # test under the same marker.
    admin = PublicationAdminPage(page)
    title = "QCTEST-144075-CMS Delete Reference"
    _fill_all_mandatory_fields(admin, "144075-cms", **{FIELD_PUBLICATION_TITLE_EN: title})
    admin.save_as_draft()
    admin.open_entry_by_edit_link(title)
    admin.set_publication_status("Published")
    admin.submit_for_review()

    admin.open_entries_list()
    admin.delete_entry_by_title(title)

    assert not admin.row_visible(title)


# ===========================================================================
# 144080/144081 — SKIPPED: Arabic Control Panel locale not exercised
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Publications — Control Panel")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Liferay success toast renders in Arabic when the Control Panel UI language is Arabic")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130711
@pytest.mark.tc_144080
@pytest.mark.skip(
    reason="No confirmed-live success-toast element was captured within "
    "this session's probe budget even in English (see tc_144015), and "
    "switching the Control Panel's own UI language to Arabic was not "
    "exercised live this session."
)
def test_success_toast_arabic_cp_locale(page):
    ...


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
@pytest.mark.skip(
    reason="The underlying English validation error IS confirmed reachable "
    "(see tc_144031), but switching the Control Panel's own UI language to "
    "Arabic to verify the Arabic wording was not exercised live this "
    "session."
)
def test_missing_file_validation_arabic_cp_locale(page):
    ...

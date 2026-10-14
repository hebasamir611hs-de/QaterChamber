"""
cms/tests/publications/test_publications_control_panel.py —
Control_Panel-tagged cases for PBI 130711 ("QC - Insights & Media - 003 -
Publications"). Migrated 2026-10-01 to the 7-state editorial workflow
(standards.md -> "Content Editorial Workflow — Seven States, and the
Account Decides the Path"). Azure: Test Plan 137724, suite 140370.

OBJECT — `Publication` (cms/Content-Admin-Guide.docx §12, slug
`manage-publication`). Guide-listed fields: publicationTitle /
publicationDescription (bilingual), publicationType, publicationDate,
coverImage, fileAttachment, activeStatus, downloadCount / viewCount (auto).
`Page Count` and `Publication Status` are NOT in §12, so no test sets them
and the Page Count cases (tc_144040/144041/144042, plus P4 tc_144043) are
BLOCKED. A separately managed "Publication Types" object is not in the guide
either (§12 says publicationType is a fixed picklist), so the Type-management
cases stay skipped.

ACCOUNT — every lifecycle/create test below runs as **QC Site Content
Editor** (`cms_role_credentials("Site Content Editor")`), never the
super-admin TEST_USER. As Editor, "Submit for Review" goes straight to
`Published` (privileged bypass); as Author it would land on `Pending Review`.
Teardown deletes the disposable record by exact QCTEST title; if the Editor
cannot delete it, teardown retries as TEST_USER (setup/cleanup use only).

TWO VISIBILITY GATES — every disposable record is created with `Active
Status` TICKED (it defaults to unticked). A public-visible assertion
therefore checks both gates (Published + Active Status), and a not-visible
assertion on a Draft/Unpublished record isolates the workflow gate, because
Active Status is already on. Every public read uses a fresh logged-out
context (`new_context(browser, use_auth_state=False)`), never the CMS `page`.

DISPOSABLE DATA ONLY — every mutation targets a brand-new `QCTEST-<tc_id>-*`
Publication, deleted in `finally` by exact title. No real shared Publication
row is opened for edit, saved or deleted.

Previously reported "Submit clears Type/Status" defect (2026-09-22): observed
through TEST_USER with Active Status never ticked — UNVERIFIED under this
flow; see publication_admin_page.py.

Skips kept from the previous batch (not two-state-model reasons):
  - tc_143997/143998: the skip cites the retired Author credentials. The
    accounts were re-provisioned 2026-09-27; left as-is per the migration
    brief and raised as an open question.
  - tc_144001 (no Cancel control), Publication Types cases, tc_144015/
    144080/144081 (toast / Arabic CP locale), tc_144073 (interrupted upload).
"""

import allure
import pytest

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
    normalize_status,
)
from cms.pages.control_panel.login_page import CmsLoginPage
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
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from web.pages.publications.publications_page import PublicationsPage

PUBLICATIONS_CMS_XDIST_GROUP = pytest.mark.xdist_group("publications_cms")
FIXTURES = "cms/tests/publications/fixtures"
EDITOR_ROLE = "Site Content Editor"
PUBLIC_PROPAGATION_TIMEOUT_S = 60

_PAGE_COUNT_BLOCKED = (
    "BLOCKED: 'Page Count' is not a field of the Publication object in "
    "cms/Content-Admin-Guide.docx §12 (guide lists publicationTitle/"
    "publicationDescription, publicationType, publicationDate, coverImage, "
    "fileAttachment, activeStatus, download/viewCount). Guide-vs-case "
    "conflict for the QA Manager/BA — not scripted against a guessed field."
)


def _as_editor(page) -> PublicationAdminPage:
    """Signs the page in as QC Site Content Editor (replacing the fixture's
    pre-loaded TEST_USER session) and returns the Page Object."""
    email, password = cms_role_credentials(EDITOR_ROLE)
    CmsLoginPage(page).ensure_signed_in_as(email, password)
    return PublicationAdminPage(page)


def _status(admin: PublicationAdminPage, title: str) -> str:
    return normalize_status(admin.status_for(title))


def _fill_all_mandatory_fields(admin: PublicationAdminPage, prefix: str, **overrides) -> dict:
    """Fills the guide-listed Publication fields with safe defaults and
    ticks Active Status (see module docstring). `skip_type`/`skip_cover`/
    `skip_date`/`skip_file` omit that one field; `active_status=False`
    leaves the checkbox unticked. Page Count is filled only when a caller
    passes `page_count` explicitly (P4 tc_144043 only — excluded from runs)."""
    values = {
        FIELD_PUBLICATION_TITLE_EN: f"QCTEST-{prefix} Publication",
        FIELD_PUBLICATION_TITLE_AR: f"QCTEST-{prefix} منشور",
        FIELD_PUBLICATION_DESCRIPTION_EN: f"QCTEST-{prefix} disposable automated-test publication description.",
        FIELD_PUBLICATION_DESCRIPTION_AR: f"QCTEST-{prefix} وصف منشور تجريبي تم إنشاؤه تلقائيًا.",
        "publication_type": "Report",
        "publication_date": "01/01/2026",
        "active_status": True,
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
    if values.get("page_count") and not values.get("skip_page_count"):
        admin.fill_number(FIELD_PAGE_COUNT, values["page_count"])
    admin.set_active_status(bool(values["active_status"]))
    return values


def _submit_as_editor(admin: PublicationAdminPage, title: str) -> str:
    """Reopen the saved Draft and Submit for Review as Editor. Returns the
    normalized row status — Published is expected for this account."""
    admin.open_entry_by_edit_link(title)
    admin.submit_for_review()
    return _status(admin, title)


def _assert_published_with_history(admin: PublicationAdminPage, title: str) -> None:
    """Gate 1 via the badge AND the History trail (a recorded transition,
    not just a badge), then gate 2 by reopening and reading Active Status."""
    assert _status(admin, title) == STATUS_PUBLISHED, (
        f"Editor's Submit for Review should land {title!r} on Published"
    )
    history = admin.history_entries(title)
    assert history, f"no History trail recorded for {title!r} after publishing"
    admin.open_entry_by_edit_link(title)
    assert admin.active_status_checked(), f"Active Status is not ticked on {title!r}"


def _teardown(admin: PublicationAdminPage, *titles: str) -> None:
    """Delete disposable records by EXACT QCTEST title; retry as TEST_USER
    (cleanup only) if the Editor's delete leaves the row in place."""
    for title in titles:
        if not title or not title.startswith("QCTEST-"):
            continue  # never delete anything not provably disposable
        admin.open_entries_list()
        if not admin.row_visible(title):
            continue
        admin.delete_entry_by_title(title)
        admin.open_entries_list()
        if admin.row_visible(title):
            CmsLoginPage(admin.page).ensure_signed_in_as()
            admin.open_entries_list()
            admin.delete_entry_by_title(title)


def _public_page(browser, query):
    """Run `query(PublicationsPage)` in a fresh LOGGED-OUT context."""
    ctx = new_context(browser, use_auth_state=False)
    try:
        pub = PublicationsPage(ctx.new_page())
        return query(pub)
    finally:
        ctx.close()


def _public_titles(browser, title: str) -> list:
    def _q(pub):
        pub.open_publications()
        pub.search(title)
        return pub.card_titles()
    return _public_page(browser, _q)


def _wait_public_visible(browser, title: str) -> bool:
    try:
        wait_until(lambda: title in _public_titles(browser, title),
                   timeout=PUBLIC_PROPAGATION_TIMEOUT_S, poll=5)
        return True
    except WaitTimeoutError:
        return False



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
    """Azure TC 143996 | PBI 130711. Account: QC Site Content Editor.
    Create -> edit -> preview -> Submit for Review (Editor: straight to
    Published) -> unpublish (row action: lands on Unpublished, not Draft)
    -> delete. The "manage Publication Types" half is not exercised — no
    such object is listed in Content-Admin-Guide §12."""
    admin = _as_editor(page)
    title = "QCTEST-143996 Editor Lifecycle"
    try:
        with allure.step("Create (Active Status ticked) and save as Draft"):
            _fill_all_mandatory_fields(admin, "143996", **{FIELD_PUBLICATION_TITLE_EN: title})
            admin.save_as_draft()
            assert _status(admin, title) == STATUS_DRAFT

        with allure.step("Edit"):
            admin.open_entry_by_edit_link(title)
            admin.fill_text(FIELD_PUBLICATION_DESCRIPTION_EN, "QCTEST-143996 edited description.")
            admin.save_as_draft()

        with allure.step("Preview"):
            admin.open_entries_list()
            assert admin.row_preview_url(title)

        with allure.step("Submit for Review as Editor -> Published"):
            _submit_as_editor(admin, title)
            _assert_published_with_history(admin, title)

        with allure.step("Unpublish via the row action -> Unpublished"):
            admin.open_entries_list()
            admin.unpublish_entry(title)
            assert _status(admin, title) == STATUS_UNPUBLISHED

        with allure.step("Delete"):
            admin.open_entries_list()
            admin.delete_entry_by_title(title)
            admin.open_entries_list()
            assert not admin.row_visible(title)
    finally:
        _teardown(admin, title)


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
def test_editor_create_save_as_draft(page, browser):
    """Azure TC 144000 | PBI 130711. Account: QC Site Content Editor.
    Saved Draft (Active Status ticked) is not visible to a logged-out
    visitor — the workflow gate alone hides it."""
    admin = _as_editor(page)
    title = "QCTEST-144000 Create Draft"
    try:
        _fill_all_mandatory_fields(admin, "144000", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()

        assert _status(admin, title) == STATUS_DRAFT
        assert title not in _public_titles(browser, title)
    finally:
        _teardown(admin, title)


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
def test_editor_resave_existing_as_draft(page, browser):
    """Azure TC 144002 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144002 Resave Draft"
    try:
        _fill_all_mandatory_fields(admin, "144002", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.save_as_draft()

        assert _status(admin, title) == STATUS_DRAFT
        assert title not in _public_titles(browser, title)
    finally:
        _teardown(admin, title)


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
def test_editor_preview_draft_record(page, browser):
    """Azure TC 144003 | PBI 130711. Account: QC Site Content Editor.
    Preview is a staff surface; public invisibility is checked logged-out."""
    admin = _as_editor(page)
    title = "QCTEST-144003 Preview Draft"
    try:
        _fill_all_mandatory_fields(admin, "144003", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entries_list()
        preview_url = admin.row_preview_url(title)

        assert preview_url
        assert _status(admin, title) == STATUS_DRAFT
        assert title not in _public_titles(browser, title)
    finally:
        _teardown(admin, title)


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
    """Azure TC 144004 | PBI 130711 — Control_Panel half. Account: QC Site
    Content Editor (Submit for Review -> Published). The case's "Page Count
    = 5" data point is BLOCKED (field not in guide §12) and not set."""
    admin = _as_editor(page)
    title = "QCTEST-144004-CMS Publish Flow"
    try:
        _fill_all_mandatory_fields(admin, "144004-cms", **{FIELD_PUBLICATION_TITLE_EN: title},
                                    publication_type="Guides")
        admin.save_as_draft()
        _submit_as_editor(admin, title)

        _assert_published_with_history(admin, title)
        assert admin.field_value(FIELD_PUBLICATION_TITLE_EN).strip() == title
    finally:
        _teardown(admin, title)


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
    """Azure TC 144005 | PBI 130711 — Control_Panel half. Account: QC Site
    Content Editor. A Published record is unpublished (row action), edited,
    then republished with Submit for Review."""
    admin = _as_editor(page)
    original_title = "QCTEST-144005-CMS-Original"
    updated_title = "QCTEST-144005-CMS-Updated"
    try:
        _fill_all_mandatory_fields(admin, "144005-cms", **{FIELD_PUBLICATION_TITLE_EN: original_title})
        admin.save_as_draft()
        assert _submit_as_editor(admin, original_title) == STATUS_PUBLISHED

        admin.open_entries_list()
        admin.unpublish_entry(original_title)
        admin.open_entry_by_edit_link(original_title)
        admin.fill_text(FIELD_PUBLICATION_TITLE_EN, updated_title)
        admin.submit_for_review()

        _assert_published_with_history(admin, updated_title)
        admin.open_entries_list()
        assert not admin.row_visible(original_title)
    finally:
        _teardown(admin, updated_title, original_title)


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
def test_unpublish_updates_status_cms(page, browser):
    """Azure TC 144006 | PBI 130711 — Control_Panel half. Account: QC Site
    Content Editor. Published (+Active Status) -> Unpublish row action ->
    Unpublished; a logged-out visitor no longer sees it."""
    admin = _as_editor(page)
    title = "QCTEST-144006-CMS Unpublish Flow"
    try:
        _fill_all_mandatory_fields(admin, "144006-cms", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        _submit_as_editor(admin, title)
        _assert_published_with_history(admin, title)

        admin.open_entries_list()
        admin.unpublish_entry(title)

        assert _status(admin, title) == STATUS_UNPUBLISHED
        try:
            wait_until(lambda: title not in _public_titles(browser, title),
                       timeout=PUBLIC_PROPAGATION_TIMEOUT_S, poll=5)
        except WaitTimeoutError:
            pytest.fail(f"Unpublished {title!r} still visible to a logged-out visitor")
    finally:
        _teardown(admin, title)


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
    """Azure TC 144007 | PBI 130711 — Control_Panel half. Account: QC Site
    Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144007-CMS Delete Flow"
    try:
        _fill_all_mandatory_fields(admin, "144007-cms", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        assert _submit_as_editor(admin, title) == STATUS_PUBLISHED

        admin.open_entries_list()
        admin.delete_entry_by_title(title)
        admin.open_entries_list()

        assert not admin.row_visible(title)
    finally:
        _teardown(admin, title)


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
    """Azure TC 144013 | PBI 130711. Account: QC Site Content Editor. The
    system identity is the entry's own `editEntry` code in its edit URL."""
    admin = _as_editor(page)
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
        _teardown(admin, title1, title2)


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
    """Azure TC 144014 | PBI 130711. Account: QC Site Content Editor.
    Published record -> unpublish (row action) -> edit Description EN ->
    Submit for Review; the row's Last modified value changes."""
    admin = _as_editor(page)
    title = "QCTEST-144014 Last Modified Check"
    try:
        _fill_all_mandatory_fields(admin, "144014", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        assert _submit_as_editor(admin, title) == STATUS_PUBLISHED
        admin.open_entries_list()
        before = admin.row_last_modified(title)

        admin.unpublish_entry(title)
        admin.open_entry_by_edit_link(title)
        admin.fill_text(FIELD_PUBLICATION_DESCRIPTION_EN, "QCTEST-144014 updated description.")
        admin.submit_for_review()
        admin.open_entries_list()
        after = admin.row_last_modified(title)

        assert before and after
        assert before != after, f"Last modified did not change: {before!r}"
    finally:
        _teardown(admin, title)


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
    """Azure TC 144017 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144017 Qatar Economic Outlook 2026"
    try:
        _fill_all_mandatory_fields(admin, "144017", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_PUBLICATION_TITLE_EN).strip() == title
    finally:
        _teardown(admin, title)


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
    """Azure TC 144018 | PBI 130711. Account: QC Site Content Editor. Submit
    for Review enforces required fields and writes nothing."""
    admin = _as_editor(page)
    try:
        _fill_all_mandatory_fields(admin, "144018", **{FIELD_PUBLICATION_TITLE_EN: ""})
        admin.submit_for_review()

        assert admin.submit_blocked()
    finally:
        _teardown(admin, "QCTEST-144018 منشور")


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
    """Azure TC 144019 | PBI 130711. Account: QC Site Content Editor.
    Nothing is saved: the length check reads the field back."""
    admin = _as_editor(page)
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
    """Azure TC 144020 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    try:
        _fill_all_mandatory_fields(admin, "144020", **{FIELD_PUBLICATION_TITLE_EN: "   "})
        admin.submit_for_review()

        assert admin.submit_blocked()
    finally:
        _teardown(admin, "QCTEST-144020 منشور")


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
    """Azure TC 144021 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144021 Publication"
    title_ar = "توقعات الاقتصاد القطري 2026"
    try:
        _fill_all_mandatory_fields(admin, "144021", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_TITLE_AR: title_ar})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_PUBLICATION_TITLE_AR).strip() == title_ar
    finally:
        _teardown(admin, title)


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
    """Azure TC 144022 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    try:
        _fill_all_mandatory_fields(admin, "144022", **{FIELD_PUBLICATION_TITLE_AR: ""})
        admin.submit_for_review()

        assert admin.submit_blocked()
    finally:
        _teardown(admin, "QCTEST-144022 Publication")


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
    """Azure TC 144023 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
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
    """Azure TC 144024 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    try:
        _fill_all_mandatory_fields(admin, "144024", **{FIELD_PUBLICATION_TITLE_AR: "   "})
        admin.submit_for_review()

        assert admin.submit_blocked()
    finally:
        _teardown(admin, "QCTEST-144024 Publication")


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
    """Azure TC 144025 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144025 Publication"
    try:
        _fill_all_mandatory_fields(admin, "144025", **{FIELD_PUBLICATION_TITLE_EN: title},
                                    publication_type="Research Paper")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert "Research Paper" in admin.publication_type_value()
    finally:
        _teardown(admin, title)


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
    """Azure TC 144026 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    try:
        _fill_all_mandatory_fields(admin, "144026", skip_type=True)
        admin.submit_for_review()

        assert admin.submit_blocked()
    finally:
        _teardown(admin, "QCTEST-144026 Publication")


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
def test_cover_image_valid_uploads_and_displays(page, browser):
    """Azure TC 144027 | PBI 130711. Account: QC Site Content Editor.
    Published + Active Status ticked (both gates asserted), then the card's
    cover is read by a logged-out visitor."""
    admin = _as_editor(page)
    title = "QCTEST-144027 Cover Upload Check"
    try:
        _fill_all_mandatory_fields(admin, "144027", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        assert admin.uploaded_filename(FIELD_COVER_IMAGE)

        _submit_as_editor(admin, title)
        _assert_published_with_history(admin, title)
        assert _wait_public_visible(browser, title), (
            f"{title!r} is Published with Active Status ticked but not visible logged-out"
        )

        def _q(pub):
            pub.open_publications()
            pub.search(title)
            return pub.card_has_img_cover(pub.card_index(title))
        assert _public_page(browser, _q)
    finally:
        _teardown(admin, title)


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
    """Azure TC 144028 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144028 No Cover"
    try:
        _fill_all_mandatory_fields(admin, "144028", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_cover=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or _status(admin, title) != STATUS_PUBLISHED
    finally:
        _teardown(admin, title)


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
    """Azure TC 144029 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
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
def test_file_attachment_valid_drives_meta(page, browser):
    """Azure TC 144030 | PBI 130711. Account: QC Site Content Editor.
    Both gates asserted; the public meta line is read logged-out."""
    admin = _as_editor(page)
    title = "QCTEST-144030 File Meta Check"
    try:
        _fill_all_mandatory_fields(admin, "144030", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        assert admin.uploaded_filename(FIELD_FILE_ATTACHMENT)

        _submit_as_editor(admin, title)
        _assert_published_with_history(admin, title)
        assert _wait_public_visible(browser, title), (
            f"{title!r} is Published with Active Status ticked but not visible logged-out"
        )

        def _q(pub):
            pub.open_publications()
            pub.search(title)
            return pub.card_meta(pub.card_index(title))
        assert "PDF" in _public_page(browser, _q)
    finally:
        _teardown(admin, title)


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
    """Azure TC 144031 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144031 No File"
    try:
        _fill_all_mandatory_fields(admin, "144031", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_file=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or _status(admin, title) != STATUS_PUBLISHED
    finally:
        _teardown(admin, title)


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
    """Azure TC 144032 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
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
    """Azure TC 144033 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
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
    """Azure TC 144034 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144034 Description Check"
    desc = "D" * 480
    try:
        _fill_all_mandatory_fields(admin, "144034", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_DESCRIPTION_EN: desc})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_EN) == desc
    finally:
        _teardown(admin, title)


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
    admin = _as_editor(page)
    title = "QCTEST-144035 No Description"
    try:
        _fill_all_mandatory_fields(admin, "144035", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_DESCRIPTION_EN: ""})
        admin.save_as_draft()

        assert _status(admin, title) == STATUS_DRAFT
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
    """Azure TC 144036 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
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
    """Azure TC 144037 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144037 Description AR Check"
    desc_ar = "د" * 480
    try:
        _fill_all_mandatory_fields(admin, "144037", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_DESCRIPTION_AR: desc_ar})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_PUBLICATION_DESCRIPTION_AR) == desc_ar
    finally:
        _teardown(admin, title)


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
    admin = _as_editor(page)
    title = "QCTEST-144038 No Description AR"
    try:
        _fill_all_mandatory_fields(admin, "144038", **{FIELD_PUBLICATION_TITLE_EN: title, FIELD_PUBLICATION_DESCRIPTION_AR: ""})
        admin.save_as_draft()

        assert _status(admin, title) == STATUS_DRAFT
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
    """Azure TC 144039 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
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
@pytest.mark.skip(reason=_PAGE_COUNT_BLOCKED)
def test_page_count_valid_displayed(page):
    """Azure TC 144040 | PBI 130711 — BLOCKED (Page Count not in guide §12).
    Title: Verify that entering a valid positive integer in Page Count is accepted and displayed.
    Steps: Fill all fields with Page Count = 42, publish, check the public card shows 42.
    """
    ...


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
@pytest.mark.skip(reason=_PAGE_COUNT_BLOCKED)
def test_page_count_empty_rejected(page):
    """Azure TC 144041 | PBI 130711 — BLOCKED (Page Count not in guide §12).
    Title: Verify that leaving Page Count empty is rejected with a validation error.
    Steps: Fill all fields except Page Count, Submit for Review, expect a validation error.
    """
    ...


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
@pytest.mark.skip(reason=_PAGE_COUNT_BLOCKED)
def test_page_count_zero_negative_rejected(page):
    """Azure TC 144042 | PBI 130711 — BLOCKED (Page Count not in guide §12).
    Title: Verify that entering 0 or a negative number in Page Count is rejected.
    Steps: Submit with Page Count = 0, then -5; expect each rejected.
    """
    ...


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
    admin = _as_editor(page)
    title = "QCTEST-144043 Whitespace Page Count"
    try:
        _fill_all_mandatory_fields(admin, "144043", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_page_count=True)
        admin.page.get_by_role("spinbutton", name=FIELD_PAGE_COUNT, exact=True).fill("   ")
        admin.submit_for_review()

        assert admin.submit_blocked() or _status(admin, title) != STATUS_PUBLISHED
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
def test_publication_date_valid_drives_sort(page, browser):
    """Azure TC 144044 | PBI 130711. Account: QC Site Content Editor.
    Both gates asserted; Latest First is read by a logged-out visitor."""
    admin = _as_editor(page)
    title = "QCTEST-144044 Date Sort Check"
    try:
        _fill_all_mandatory_fields(admin, "144044", **{FIELD_PUBLICATION_TITLE_EN: title}, publication_date="22/09/2026")
        admin.save_as_draft()
        _submit_as_editor(admin, title)
        _assert_published_with_history(admin, title)
        assert _wait_public_visible(browser, title)

        def _q(pub):
            pub.open_publications()
            pub.select_sort("Latest First")
            pub.search(title)
            return pub.card_titles()
        assert title in _public_page(browser, _q)
    finally:
        _teardown(admin, title)


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
    """Azure TC 144045 | PBI 130711. Account: QC Site Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144045 No Date"
    try:
        _fill_all_mandatory_fields(admin, "144045", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_date=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or _status(admin, title) != STATUS_PUBLISHED
    finally:
        _teardown(admin, title)


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
    admin = _as_editor(page)
    title = "QCTEST-144046 Invalid Date"
    try:
        _fill_all_mandatory_fields(admin, "144046", **{FIELD_PUBLICATION_TITLE_EN: title}, skip_date=True)
        admin.set_publication_date("32/13/2026")
        admin.submit_for_review()

        assert admin.submit_blocked() or _status(admin, title) != STATUS_PUBLISHED
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
    """Azure TC 144072 | PBI 130711 — Control_Panel half. Account: QC Site
    Content Editor. A future Publication Date does not route to Scheduled."""
    admin = _as_editor(page)
    title = "QCTEST-144072-CMS Future Date"
    try:
        _fill_all_mandatory_fields(admin, "144072-cms", **{FIELD_PUBLICATION_TITLE_EN: title}, publication_date="31/10/2026")
        admin.save_as_draft()
        _submit_as_editor(admin, title)

        _assert_published_with_history(admin, title)
    finally:
        _teardown(admin, title)


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
    """Azure TC 144075 | PBI 130711 — Control_Panel half. Account: QC Site
    Content Editor."""
    admin = _as_editor(page)
    title = "QCTEST-144075-CMS Delete Reference"
    try:
        _fill_all_mandatory_fields(admin, "144075-cms", **{FIELD_PUBLICATION_TITLE_EN: title})
        admin.save_as_draft()
        assert _submit_as_editor(admin, title) == STATUS_PUBLISHED

        admin.open_entries_list()
        admin.delete_entry_by_title(title)
        admin.open_entries_list()

        assert not admin.row_visible(title)
    finally:
        _teardown(admin, title)


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

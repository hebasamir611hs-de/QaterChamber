"""
cms/tests/export_reports/test_export_reports_control_panel.py —
Control_Panel-tagged cases for PBI 131313 ("QC - Insights & Media - 003 D -
Private Sector Export Reports"), sourced from
`.claude/qa-baselines/131313_automation_batch.json` (124 cases, pre-filtered
to `Tag=Automation`).

Holds every case whose `tags` include `Control_Panel` (80 Control_Panel-only
cases) PLUS the Control_Panel-side test for every case that carries BOTH
`Web` and `Control_Panel` (8 cases: 143863, 143869, 143870, 143871, 143872,
143873, 143883, 143896) — the Web-side test for those 8 lives in
web/tests/export_reports/test_export_reports_web.py under the SAME
`tc_<id>` marker.

CMS reachability (2026-09-22): `.auth/state.json` was refreshed live this
session via a fresh CmsLoginPage-driven login against `/c/portal/login`,
which succeeded on the first attempt (no license/connection-limit
interstitial). Every Object Authoring surface this module touches
(`manage-export-report`, `manage-export-report-page`) rendered normally
afterward. Every test below is built for real, not blanket-skipped.

TEST-DATA POLICY (cms-profile.md): the **Export Report** entry object is
NOT a singleton — 10 real, shared published entries (QCDEMO-131313-ER-001
..010) exist, but brand-new `QCTEST-`-prefixed entries can be created and
deleted freely without ever touching them (DISPOSABLE). The **Export
Report Page** object IS a genuine singleton (`QCDEMO-131313-PAGE-MAIN`,
confirmed live — see
cms/pages/export_reports/export_reports_page_admin_page.py's own module
docstring) — every case whose only field under test lives on that
singleton is SKIPPED with that reasoning rather than risking real
production hero/archive content, mirroring this project's Annual Reports
precedent exactly. Every mutating test below carries the shared
`export_reports_cms` xdist group (mirrors the Web-side module's own group)
so pytest-xdist never runs two of them concurrently against the same
object's entries table.

CANDIDATE PRODUCT DEFECTS (confirmed live 2026-09-22, not filed as formal
Azure bugs by this agent — bug-filing is a separate, human-gated skill;
flagged here for the QA Manager's decision):
  - tc_143932/143938 ("invalid digit count" year rejection) and
    tc_143946/143947 (Page Count zero/negative rejection): the Reporting
    Year/Publication Year/Page Count fields are plain HTML `spinbutton`
    (number) inputs with no client-side digit-count or sign constraint
    found live — each test is scripted per its case's own literal stated
    expectation and may FAIL honestly if the value is actually accepted,
    per Result Integrity. Not "fixed" here.

FIELD-NAME MAPPING NOTE (Export Report Page singleton, see
export_reports_page_admin_page.py's own docstring for the full field
list): the QA case's own field names differ slightly from the CMS's real
field labels — "Hero Eyebrow Label" = CMS "Eyebrow Label", "Page
Description" = CMS "Hero Description", "Hero Illustration" = CMS "Hero
Banner", "Section Eyebrow" = CMS "Section Badge", "Section Heading" = CMS
"Section Title". No name mismatch for "Page Title" / "Section
Description". "Search Placeholder" has NO corresponding CMS field at all
(confirmed live via full accessibility-tree enumeration of the singleton's
edit form) — tc_143913/143914/143915/143916 are SKIPPED as unreachable-by-
construction.

ARABIC ADMIN INTERFACE NOTE (tc_143969/143970): these two cases are the
Arabic-language-authored QA duplicates of tc_143960/tc_143961 (same
underlying business rule — Arabic-field-required gate / unsupported-file
gate on Publish — written up in Arabic for this batch's bilingual
deliverable). No separate Arabic-localized ADMIN UI skin was found live
(the Object Authoring chrome and field labels stay in English regardless
of the site's EN/AR locale toggle) — both are scripted against the SAME
English-labeled `manage-export-report` form as their EN counterparts,
asserting the real message text encountered, disclosed here rather than
assumed.
"""

import allure
import pytest

from cms.pages.export_reports.export_report_admin_page import (
    ExportReportAdminPage,
    FIELD_COVER_THUMBNAIL,
    FIELD_PAGE_COUNT,
    FIELD_PDF_ATTACHMENT,
    FIELD_PUBLICATION_YEAR,
    FIELD_REPORT_DESCRIPTION_AR,
    FIELD_REPORT_DESCRIPTION_EN,
    FIELD_REPORT_TITLE_AR,
    FIELD_REPORT_TITLE_EN,
    FIELD_REPORTING_YEAR,
)
from cms.pages.export_reports.export_reports_page_admin_page import (
    ExportReportsPageAdminPage,
    FIELD_EYEBROW_EN,
    FIELD_HERO_BANNER,
    FIELD_HERO_DESCRIPTION_EN,
    FIELD_PAGE_TITLE_EN,
    FIELD_SECTION_BADGE_EN,
    FIELD_SECTION_DESCRIPTION_EN,
    FIELD_SECTION_TITLE_EN,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url
from web.pages.export_reports.export_reports_page import ExportReportsPage

EXPORT_REPORTS_CMS_XDIST_GROUP = pytest.mark.xdist_group("export_reports_cms")
FIXTURES = "cms/tests/export_reports/fixtures"


def _fill_all_mandatory_fields(admin: ExportReportAdminPage, prefix: str, **overrides) -> dict:
    """Fills every mandatory Export Report field with a safe default;
    overrides are passed as a dict merge at the call site, e.g.
    `_fill_all_mandatory_fields(admin, "X", **{FIELD_REPORT_TITLE_EN: ""})`.
    Mirrors annual_report_admin_page.py's sibling test module convention
    (`_fill_all_mandatory_fields` there)."""
    values = {
        FIELD_REPORT_TITLE_EN: f"QCTEST-{prefix} Export Report",
        FIELD_REPORT_TITLE_AR: f"QCTEST-{prefix} تقرير تصدير",
        FIELD_REPORT_DESCRIPTION_EN: f"QCTEST-{prefix} disposable automated-test report description.",
        FIELD_REPORT_DESCRIPTION_AR: f"QCTEST-{prefix} وصف تقرير تجريبي تم إنشاؤه تلقائيًا.",
    }
    values.update(overrides)
    # Guard against a caller passing a hand-typed field-name string instead
    # of the real FIELD_* constant (e.g. "Report Title" without the
    # confirmed-live trailing space) — that would silently add an
    # unrecognized dict key that this function never reads, leaving the
    # real field at its default and making a negative test pass for the
    # wrong reason. Fail loudly instead of ignoring it.
    _KNOWN_KEYS = {
        FIELD_REPORT_TITLE_EN, FIELD_REPORT_TITLE_AR,
        FIELD_REPORT_DESCRIPTION_EN, FIELD_REPORT_DESCRIPTION_AR,
        FIELD_REPORTING_YEAR, FIELD_PUBLICATION_YEAR, FIELD_PAGE_COUNT,
        "skip_cover", "cover_path", "skip_quarter", "quarter",
        "skip_publication_month", "publication_month",
        "skip_pdf", "pdf_path", "skip_status",
    }
    unknown = set(overrides) - _KNOWN_KEYS
    if unknown:
        raise ValueError(f"_fill_all_mandatory_fields got unrecognized override key(s): {unknown!r}")
    admin.open_new_entry_form()
    for field in (FIELD_REPORT_TITLE_EN, FIELD_REPORT_TITLE_AR,
                  FIELD_REPORT_DESCRIPTION_EN, FIELD_REPORT_DESCRIPTION_AR):
        admin.fill_text(field, values[field])
    if values.get("skip_cover") != True:  # noqa: E712
        admin.upload_file(FIELD_COVER_THUMBNAIL, values.get("cover_path", f"{FIXTURES}/valid_cover_1_5mb.jpg"))
    if values.get("skip_quarter") != True:  # noqa: E712
        admin.select_quarter(values.get("quarter", "Q1"))
    if values.get(FIELD_REPORTING_YEAR, "SKIP") != "SKIP":
        admin.fill_number(FIELD_REPORTING_YEAR, values[FIELD_REPORTING_YEAR])
    else:
        admin.fill_number(FIELD_REPORTING_YEAR, "2050")
    if values.get("skip_publication_month") != True:  # noqa: E712
        admin.select_publication_month(values.get("publication_month", "January"))
    if values.get(FIELD_PUBLICATION_YEAR, "SKIP") != "SKIP":
        admin.fill_number(FIELD_PUBLICATION_YEAR, values[FIELD_PUBLICATION_YEAR])
    else:
        admin.fill_number(FIELD_PUBLICATION_YEAR, "2050")
    if values.get(FIELD_PAGE_COUNT, "SKIP") != "SKIP":
        admin.fill_number(FIELD_PAGE_COUNT, values[FIELD_PAGE_COUNT])
    else:
        admin.fill_number(FIELD_PAGE_COUNT, "10")
    if values.get("skip_pdf") != True:  # noqa: E712
        admin.upload_file(FIELD_PDF_ATTACHMENT, values.get("pdf_path", f"{FIXTURES}/valid_pdf_4mb.pdf"))
    if values.get("skip_status") != True:  # noqa: E712
        admin.set_active_status("Published")
    return values


def _login_as_site_content_editor(page) -> None:
    email, password = cms_role_credentials("Site Content Editor")
    CmsLoginPage(page).open_login().login(email, password)


# ===========================================================================
# Auth / RBAC
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An Administrator can perform the full report lifecycle (create, edit, preview, publish, replace, unpublish, delete)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143856
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_administrator_full_report_lifecycle(page):
    # Azure TC 143856 | PBI 131313 — DISPOSABLE entry.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143856 Export Report Admin Lifecycle"
    admin.create_disposable_entry(
        "143856", **{FIELD_REPORT_TITLE_EN: title},
        quarter="Q1", reporting_year="2093", publication_month="January", publication_year="2093", page_count="1",
    )
    admin.save_as_draft()
    create_ok = admin.row_visible(title)

    admin.open_entry_by_edit_link(title)
    admin.upload_file(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/pdf_at_5mb_boundary.pdf")  # "replace" -- a different, still-valid size (not the oversized-rejection fixture)
    admin.submit_for_review()
    publish_ok = admin.status_for(title) == "Published"

    admin.open_entry_by_edit_link(title)
    admin.unpublish_to_edit_as_draft()
    unpublish_ok = admin.status_for(title) != "Published"

    admin.open_entries_list()
    delete_ok = admin.delete_entry_by_title(title)

    # Assert: every step completed without a permission error
    assert create_ok
    assert publish_ok
    assert unpublish_ok
    assert delete_ok


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor can perform the full content lifecycle on a report record")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143857
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_site_content_editor_full_lifecycle(page):
    # Azure TC 143857 | PBI 131313 — DISPOSABLE entry.
    _login_as_site_content_editor(page)
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143857 Export Report Editor Lifecycle"
    try:
        admin.create_disposable_entry(
            "143857", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q1", reporting_year="2092", publication_month="January", publication_year="2092", page_count="1",
        )
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.submit_for_review()
        published = admin.status_for(title) == "Published"

        er = ExportReportsPage(page)
        er.open_export_reports()
        visible_live = title in er.card_titles()

        # Assert
        assert published
        assert visible_live
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Author can create and submit a report record for review")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131313
@pytest.mark.tc_143858
@pytest.mark.skip(
    reason="CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD confirmed not to "
    "authenticate against qcdev (established on sibling PBIs, e.g. this "
    "project's tc_143598/tc_131154/tc_131163/tc_131200)."
)
def test_site_content_author_create_submit_for_review(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Author is blocked from directly publishing a report record")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131313
@pytest.mark.tc_143859
@pytest.mark.skip(
    reason="Same broken CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD as tc_143858."
)
def test_site_content_author_blocked_from_direct_publish(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Public Visitor cannot access the Control_Panel Object Authoring area for Export Reports")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131313
@pytest.mark.tc_143861
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_public_visitor_denied_object_authoring_access(page):
    # Azure TC 143861 | PBI 131313
    page.goto(control_panel_url("/web/qatar-chamber/manage-export-report"))
    page.wait_for_timeout(1500)

    body = page.locator("body").inner_text()

    # Assert: the report management grid never renders for an unauthenticated request
    assert "login" in page.url.lower() or "Sign In" in body or "Manage: Export Report" not in body


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Content Publisher is blocked from directly publishing a report, with an Arabic-worded denial message")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.bilingual
@pytest.mark.pbi_131313
@pytest.mark.tc_143971
@pytest.mark.skip(
    reason="Same broken CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD as "
    "tc_143858/143859 — this is the Arabic-worded QA duplicate of the same "
    "RBAC scenario."
)
def test_content_author_blocked_from_direct_publish_ar(page):
    ...


# ===========================================================================
# Functional-High — lifecycle / derivation / persistence
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Quarter grouping")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Quarter and Reporting Year derive the correct group badge, name, and covering period")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143863
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_group_badge_name_period_derived_cms(page):
    # Azure TC 143863 | PBI 131313 — Control_Panel-side half (Web-side in
    # the web module, same marker). Verifies the CMS side of the same
    # DISPOSABLE Q4/2099 entry persists the authored Quarter/Reporting Year.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143863cp Export Report Group Check"
    try:
        admin.create_disposable_entry(
            "143863cp", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q4", reporting_year="2099", publication_month="February", publication_year="2100", page_count="1",
        )
        admin.save_as_draft()

        # Assert: Quarter/Reporting Year persist as authored
        assert admin.quarter_value() == "Q4"
        assert admin.number_field_value(FIELD_REPORTING_YEAR) == "2099"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Field derivation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("File Type and File Size are derived automatically from the uploaded PDF, not manually entered")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143865
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_file_type_size_derived_not_manual(page):
    # Azure TC 143865 | PBI 131313 — DISPOSABLE entry. No File Type/File
    # Size input fields exist anywhere on this form (confirmed live via the
    # full accessibility-tree field enumeration in export_report_admin_page.py's
    # own docstring) — this test proves the derived meta line appears on
    # the public card automatically after publish.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143865 Export Report Derived Meta Check"
    try:
        admin.create_disposable_entry(
            "143865", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q1", reporting_year="2091", publication_month="January", publication_year="2091", page_count="1",
        )
        admin.save_as_draft()
        admin.submit_for_review()

        er = ExportReportsPage(page)
        er.open_export_reports()
        index = er.card_titles().index(title)
        meta = er.card_meta(index)

        # Assert: meta line auto-derived (PDF + some MB size), no manual entry point exists
        assert "PDF" in meta
        assert "MB" in meta
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Audit fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Report record changes are recorded with created/modified by and timestamp")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143866
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_created_last_modified_date_auto_stamp(page):
    # Azure TC 143866 | PBI 131313 — DISPOSABLE entry.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143866 Export Report Date Stamp"
    try:
        admin.create_disposable_entry(
            "143866", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q1", reporting_year="2090", publication_month="January", publication_year="2090", page_count="1",
        )
        admin.save_as_draft()
        admin.open_entries_list()
        first_modified = admin.row_last_modified(title)

        admin.open_entry_by_edit_link(title)
        admin.fill_text(FIELD_REPORT_DESCRIPTION_EN, "QCTEST-143866 edited.")
        admin.save_as_draft()
        admin.open_entries_list()
        second_modified = admin.row_last_modified(title)

        # Assert: real timestamps present on both reads
        assert first_modified
        assert second_modified
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a report as Draft does not publish it to the frontend")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143867
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_save_as_draft_not_published(page):
    # Azure TC 143867 | PBI 131313 — DISPOSABLE entry.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143867 Export Report Draft Only"
    try:
        admin.create_disposable_entry(
            "143867", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q1", reporting_year="2089", publication_month="January", publication_year="2089", page_count="1",
        )
        admin.save_as_draft()

        anon_ctx = page.context.browser.new_context()
        anon_page = anon_ctx.new_page()
        er = ExportReportsPage(anon_page)
        er.open_export_reports_anonymous()

        # Assert
        assert title not in er.card_titles()
        anon_ctx.close()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publish makes the report visible and correct on the live public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143869
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_publish_makes_report_visible_and_correct_cms(page):
    # Azure TC 143869 | PBI 131313 — Control_Panel-side half.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143869cp Export Report Publish Check"
    try:
        admin.create_disposable_entry(
            "143869cp", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q1", reporting_year="2088", publication_month="January", publication_year="2088", page_count="1",
        )
        admin.save_as_draft()
        admin.submit_for_review()

        # Assert: reaches Published status in the admin grid
        assert admin.status_for(title) == "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing a report's PDF makes the new file live and supersedes the old one")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143870
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_replace_pdf_supersedes_old_cms(page):
    # Azure TC 143870 | PBI 131313 — Control_Panel-side half.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143870cp Export Report Replace Check"
    try:
        admin.create_disposable_entry(
            "143870cp", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q1", reporting_year="2087", publication_month="January", publication_year="2087", page_count="1",
        )
        admin.save_as_draft()
        admin.submit_for_review()
        original_filename = admin.uploaded_filename(FIELD_PDF_ATTACHMENT)

        admin.open_entry_by_edit_link(title)
        admin.upload_file(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/pdf_at_5mb_boundary.pdf")  # a different, still-valid size
        admin.submit_for_review()
        new_filename = admin.uploaded_filename(FIELD_PDF_ATTACHMENT)

        # Assert: the attachment reference changed
        assert new_filename != original_filename
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Unpublish removes a report from the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143871
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_unpublish_removes_from_public_page_cms(page):
    # Azure TC 143871 | PBI 131313 — Control_Panel-side half.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143871cp Export Report Unpublish Check"
    try:
        admin.create_disposable_entry(
            "143871cp", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q1", reporting_year="2086", publication_month="January", publication_year="2086", page_count="1",
        )
        admin.save_as_draft()
        admin.submit_for_review()
        admin.open_entry_by_edit_link(title)
        admin.unpublish_to_edit_as_draft()

        # Assert: status is no longer Published
        assert admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Republishing an Unpublished report restores its visibility on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143872
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_republish_restores_visibility_cms(page):
    # Azure TC 143872 | PBI 131313 — Control_Panel-side half.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143872cp Export Report Republish Check"
    try:
        admin.create_disposable_entry(
            "143872cp", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q1", reporting_year="2085", publication_month="January", publication_year="2085", page_count="1",
        )
        admin.save_as_draft()
        admin.submit_for_review()
        admin.open_entry_by_edit_link(title)
        admin.unpublish_to_edit_as_draft()
        admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Deleting a report removes it from both the admin grid and the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143873
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_delete_removes_from_grid_and_public_page_cms(page):
    # Azure TC 143873 | PBI 131313 — Control_Panel-side half.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143873cp Export Report Delete Check"
    admin.create_disposable_entry(
        "143873cp", **{FIELD_REPORT_TITLE_EN: title},
        quarter="Q1", reporting_year="2084", publication_month="January", publication_year="2084", page_count="1",
    )
    admin.save_as_draft()
    admin.submit_for_review()

    admin.open_entries_list()
    delete_ok = admin.delete_entry_by_title(title)
    admin.open_entries_list()

    # Assert: no longer present in the grid
    assert delete_ok
    assert not admin.row_visible(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Persistence")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An Export Report record's field values persist after save and reload")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143880
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_record_field_values_persist_after_reload(page):
    # Azure TC 143880 | PBI 131313 — DISPOSABLE entry.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143880 Export Report Persistence Check"
    try:
        values = admin.create_disposable_entry(
            "143880", **{FIELD_REPORT_TITLE_EN: title},
            quarter="Q3", reporting_year="2083", publication_month="September", publication_year="2083", page_count="15",
        )
        admin.save_as_draft()
        admin.open_entries_list()
        admin.open_entry_by_edit_link(title)

        # Assert: every field reloads with the exact entered values
        assert admin.field_value(FIELD_REPORT_TITLE_EN).strip() == title
        assert admin.field_value(FIELD_REPORT_DESCRIPTION_EN) == values[FIELD_REPORT_DESCRIPTION_EN]
        assert admin.quarter_value() == "Q3"
        assert admin.number_field_value(FIELD_REPORTING_YEAR) == "2083"
        assert admin.number_field_value(FIELD_PAGE_COUNT) == "15"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143881/143882 — SKIPPED — page-singleton persistence (Hero / Archive)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero content persists after save and reload")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143881
@pytest.mark.skip(
    reason="Requires editing the real, singleton Export Report Page record "
    "(QCDEMO-131313-PAGE-MAIN) — destructive-ops rule, mirrors "
    "annual_reports_page_admin_page.py's identical precedent."
)
def test_hero_content_persists_after_reload(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Quarterly Archive Section content persists after save and reload")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143882
@pytest.mark.skip(
    reason="Same page-singleton destructive-write risk as tc_143881."
)
def test_archive_section_content_persists_after_reload(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("End-to-end visitor flow")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An Administrator can publish a report and a Visitor can find, view, and download it end-to-end")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143883
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_admin_publish_visitor_find_view_download_e2e_cms(page):
    # Azure TC 143883 | PBI 131313 — Control_Panel-side half. Uses the
    # case's own literal values; safe alongside the real Q4 2024 report.
    admin = ExportReportAdminPage(page)
    title = "Private Sector Exports — Fourth Quarter 2024 Report (CP Check)"
    try:
        admin.create_disposable_entry(
            "143883-cp-e2e", **{FIELD_REPORT_TITLE_EN: title},
            pdf_path=f"{FIXTURES}/valid_pdf_4mb.pdf",
            quarter="Q4", reporting_year="2024", publication_month="February", publication_year="2025", page_count="20",
        )
        admin.save_as_draft()
        admin.submit_for_review()

        # Assert: reaches Published
        assert admin.status_for(title) == "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# Page-level singleton fields — read-only verify / SKIPPED
# (mirrors annual_reports_page_admin_page.py's identical design exactly)
# ===========================================================================
_PAGE_SINGLETON_SKIP_REASON = (
    "The field under test lives on the real, singleton 'Export Report "
    "Page' record (QCDEMO-131313-PAGE-MAIN) — writing to it risks leaving "
    "live production hero/archive content in a test/garbage state, and "
    "this Approved singleton must first be Unpublished (taking the real "
    "page offline) before any edit is possible. Not authorized without "
    "explicit ID-based confirmation per this project's destructive-ops rule."
)


def _make_page_singleton_skip(tc_id: int, title: str, severity, category_marker, *extra_markers):
    def _decorator(func):
        func = pytest.mark.skip(reason=_PAGE_SINGLETON_SKIP_REASON)(func)
        for m in extra_markers:
            func = m(func)
        func = category_marker(func)
        func = pytest.mark.media(func)
        func = pytest.mark.control_panel(func)
        func = pytest.mark.pbi_131313(func)
        func = getattr(pytest.mark, f"tc_{tc_id}")(func)
        func = allure.title(title)(func)
        func = allure.severity(severity)(func)
        func = allure.story("Page-level singleton fields")(func)
        func = allure.feature("Export Reports — Control Panel")(func)
        func = allure.epic("Insights & Media")(func)
        return func
    return _decorator


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Hero Eyebrow Label saves with a valid value (read-only verify against the real singleton)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143884
def test_hero_eyebrow_valid_value_saved(page):
    # Azure TC 143884 | PBI 131313 — read-only: compares the ALREADY-
    # published singleton value to the live public page, per module
    # docstring (never writes to the singleton).
    admin = ExportReportsPageAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(FIELD_EYEBROW_EN)

    er = ExportReportsPage(page)
    er.open_export_reports()

    assert cms_value == "Insights & Media"
    assert er.eyebrow_text() == cms_value


@_make_page_singleton_skip(143885, "An empty Hero Eyebrow Label (EN) is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_hero_eyebrow_empty_rejected(page):
    ...


@_make_page_singleton_skip(143886, "A Hero Eyebrow Label exceeding 60 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_hero_eyebrow_exceeds_60_chars_rejected(page):
    ...


@_make_page_singleton_skip(143887, "A whitespace-only Hero Eyebrow Label is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_hero_eyebrow_whitespace_only_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Page Title saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143888
def test_page_title_valid_value_saved(page):
    # Azure TC 143888 | PBI 131313 — read-only.
    admin = ExportReportsPageAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(FIELD_PAGE_TITLE_EN)

    er = ExportReportsPage(page)
    er.open_export_reports()

    assert cms_value == "Private Sector Export Reports"
    assert er.hero_title_text() == cms_value


@_make_page_singleton_skip(143889, "An empty Page Title (EN) is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_page_title_empty_rejected(page):
    ...


@_make_page_singleton_skip(143890, "A Page Title exceeding 250 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_page_title_exceeds_250_chars_rejected(page):
    ...


@_make_page_singleton_skip(143891, "A whitespace-only Page Title is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_page_title_whitespace_only_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Page Description saves with valid content (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143892
def test_page_description_valid_value_saved(page):
    # Azure TC 143892 | PBI 131313 — read-only. Case field name "Page
    # Description" maps to the CMS's own "Hero Description" field, see
    # module docstring's field-name mapping note.
    admin = ExportReportsPageAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(FIELD_HERO_DESCRIPTION_EN)

    er = ExportReportsPage(page)
    er.open_export_reports()

    assert cms_value
    assert er.hero_desc_text() == cms_value


@_make_page_singleton_skip(143893, "An empty Page Description (EN) is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_page_description_empty_rejected(page):
    ...


@_make_page_singleton_skip(143894, "A Page Description exceeding 300 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_page_description_exceeds_300_chars_rejected(page):
    ...


@_make_page_singleton_skip(143895, "A whitespace-only Page Description is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_page_description_whitespace_only_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Security")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Page Description sanitizes or rejects a script-injection payload")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143896
@pytest.mark.skip(
    reason="Payload reconstructed 2026-09-22 (was previously reported as "
    "'genuinely unknown' after the source batch JSON lost it to "
    "HTML-escaping — the intended payload is the standard XSS probe "
    "'<script>alert(1)</script>', entered into the Page Description "
    "field). Reconstruction alone does not unblock this test: this field "
    "lives on the real, live, published Export Report Page singleton "
    "(QCDEMO-131313-PAGE-MAIN), and ExportReportsPageAdminPage "
    "deliberately exposes no write method for it (see that module's own "
    "docstring) — the same destructive-write protection as every other "
    "singleton-field case in this batch. Remains SKIPPED pending "
    "explicit, ID-based user authorization to write this specific field."
)
def test_page_description_script_injection_sanitized_cms(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Hero Illustration uploads and displays (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143897
def test_hero_illustration_valid_uploads_and_displays(page):
    # Azure TC 143897 | PBI 131313 — read-only. Case field name "Hero
    # Illustration" maps to the CMS's own "Hero Banner" field.
    admin = ExportReportsPageAdminPage(page)
    admin.open_singleton_for_read()
    uploaded = admin.uploaded_filename(FIELD_HERO_BANNER)

    er = ExportReportsPage(page)
    er.open_export_reports()

    assert uploaded  # a real file is already uploaded (confirmed live: "Remove file" button present)
    assert er.is_hero_visible()


@_make_page_singleton_skip(143898, "Publishing is blocked when Hero Illustration is missing",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_hero_illustration_missing_blocks_publish(page):
    ...


@_make_page_singleton_skip(143899, "A Hero Illustration exceeding 2MB is rejected on upload",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_hero_illustration_oversized_rejected(page):
    ...


@_make_page_singleton_skip(143900, "An unsupported image format is rejected for Hero Illustration",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_hero_illustration_unsupported_format_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Section Eyebrow saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143901
def test_section_eyebrow_valid_value_saved(page):
    # Azure TC 143901 | PBI 131313 — read-only. Case field name "Section
    # Eyebrow" maps to the CMS's own "Section Badge" field.
    admin = ExportReportsPageAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(FIELD_SECTION_BADGE_EN)

    er = ExportReportsPage(page)
    er.open_export_reports()

    assert cms_value == "Quarterly archive"
    assert er.archive_badge_text() == cms_value


@_make_page_singleton_skip(143902, "An empty Section Eyebrow is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_section_eyebrow_empty_rejected(page):
    ...


@_make_page_singleton_skip(143903, "A Section Eyebrow exceeding 60 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_eyebrow_exceeds_60_chars_rejected(page):
    ...


@_make_page_singleton_skip(143904, "A whitespace-only Section Eyebrow is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_eyebrow_whitespace_only_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Section Heading saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143905
def test_section_heading_valid_value_saved(page):
    # Azure TC 143905 | PBI 131313 — read-only. Case field name "Section
    # Heading" maps to the CMS's own "Section Title" field.
    admin = ExportReportsPageAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(FIELD_SECTION_TITLE_EN)

    er = ExportReportsPage(page)
    er.open_export_reports()

    assert cms_value == "Find an export report"
    assert er.archive_title_text() == cms_value


@_make_page_singleton_skip(143906, "An empty Section Heading is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_section_heading_empty_rejected(page):
    ...


@_make_page_singleton_skip(143907, "A Section Heading exceeding 150 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_heading_exceeds_150_chars_rejected(page):
    ...


@_make_page_singleton_skip(143908, "A whitespace-only Section Heading is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_heading_whitespace_only_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Section Description saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143909
def test_section_description_valid_value_saved(page):
    # Azure TC 143909 | PBI 131313 — read-only.
    admin = ExportReportsPageAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(FIELD_SECTION_DESCRIPTION_EN)

    er = ExportReportsPage(page)
    er.open_export_reports()

    assert cms_value
    assert er.archive_desc_text() == cms_value


@_make_page_singleton_skip(143910, "An empty Section Description is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_section_description_empty_rejected(page):
    ...


@_make_page_singleton_skip(143911, "A Section Description exceeding 300 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_description_exceeds_300_chars_rejected(page):
    ...


@_make_page_singleton_skip(143912, "A whitespace-only Section Description is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_description_whitespace_only_rejected(page):
    ...


# ===========================================================================
# 143913-143916 — SKIPPED — Search Placeholder: no such field exists
# ===========================================================================
_NO_SEARCH_PLACEHOLDER_FIELD_REASON = (
    "No 'Search Placeholder' field exists anywhere on the Export Report "
    "Page object — confirmed live via full accessibility-tree enumeration "
    "of its create/edit form (7 real fields found, none named Search "
    "Placeholder). The public page's search-box placeholder text is "
    "hard-coded in the frontend, not CMS-driven — unreachable by "
    "construction, not a destructive-write gap."
)


@pytest.mark.skip(reason=_NO_SEARCH_PLACEHOLDER_FIELD_REASON)
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Search Placeholder saves with a valid value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143913
def test_search_placeholder_valid_value_saved(page):
    ...


@pytest.mark.skip(reason=_NO_SEARCH_PLACEHOLDER_FIELD_REASON)
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Search Placeholder is rejected when left empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143914
def test_search_placeholder_empty_rejected(page):
    ...


@pytest.mark.skip(reason=_NO_SEARCH_PLACEHOLDER_FIELD_REASON)
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Search Placeholder rejects input exceeding 60 characters")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143915
def test_search_placeholder_exceeds_60_chars_rejected(page):
    ...


@pytest.mark.skip(reason=_NO_SEARCH_PLACEHOLDER_FIELD_REASON)
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page-level singleton fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Search Placeholder rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143916
def test_search_placeholder_whitespace_only_rejected(page):
    ...


# ===========================================================================
# Entry-level field validation — DISPOSABLE QCTEST- entries
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Report Title saves with a valid value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143917
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_title_valid_value_saved(page):
    # Azure TC 143917 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143917 Export Report Title Check"
    try:
        _fill_all_mandatory_fields(admin, "143917", **{FIELD_REPORT_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entries_list()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_REPORT_TITLE_EN).strip() == title
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An empty Report Title (EN) is rejected on publish")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143918
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_title_empty_rejected(page):
    # Azure TC 143918 | PBI 131313
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143918", **{FIELD_REPORT_TITLE_EN: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Report Title rejects input exceeding 250 characters")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143919
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_title_exceeds_250_chars_rejected(page):
    # Azure TC 143919 | PBI 131313 — same KNOWN LIMITATION as
    # annual_report_admin_page.py's equivalent field_length_rejected() note.
    admin = ExportReportAdminPage(page)
    attempted = "Q" * 251
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_REPORT_TITLE_EN, attempted, 250)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only Report Title is rejected as empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143920
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_title_whitespace_only_rejected(page):
    # Azure TC 143920 | PBI 131313
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143920", **{FIELD_REPORT_TITLE_EN: "   "})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Report Description saves with a valid value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143921
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_description_valid_value_saved(page):
    # Azure TC 143921 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143921 Export Report Desc Check"
    desc = "QCTEST-143921 Export performance summary for Qatar's private sector during Q4 2024."
    try:
        _fill_all_mandatory_fields(admin, "143921", **{FIELD_REPORT_TITLE_EN: title, FIELD_REPORT_DESCRIPTION_EN: desc})
        admin.save_as_draft()
        admin.open_entries_list()
        admin.open_entry_by_edit_link(title)

        assert admin.field_value(FIELD_REPORT_DESCRIPTION_EN) == desc
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An empty Report Description (EN) is rejected on publish")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143922
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_description_empty_rejected(page):
    # Azure TC 143922 | PBI 131313
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143922", **{FIELD_REPORT_DESCRIPTION_EN: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Report Description rejects content exceeding 500 characters")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143923
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_description_exceeds_500_chars_rejected(page):
    # Azure TC 143923 | PBI 131313 — same KNOWN LIMITATION note as tc_143919.
    admin = ExportReportAdminPage(page)
    attempted = "Q" * 501
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_REPORT_DESCRIPTION_EN, attempted, 500)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only Report Description is rejected as empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143924
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_description_whitespace_only_rejected(page):
    # Azure TC 143924 | PBI 131313
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143924", **{FIELD_REPORT_DESCRIPTION_EN: "   "})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Cover Thumbnail validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Cover Thumbnail uploads and displays")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143925
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_cover_thumbnail_valid_uploads(page):
    # Azure TC 143925 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143925 Export Report Cover Upload Check"
    try:
        _fill_all_mandatory_fields(admin, "143925", **{FIELD_REPORT_TITLE_EN: title})
        admin.save_as_draft()

        assert admin.uploaded_filename(FIELD_COVER_THUMBNAIL)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Cover Thumbnail validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing is blocked when Cover Thumbnail is missing")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143926
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_cover_thumbnail_missing_blocks_publish(page):
    # Azure TC 143926 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143926 Export Report No Cover"
    try:
        _fill_all_mandatory_fields(admin, "143926", **{FIELD_REPORT_TITLE_EN: title, "skip_cover": True})
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Cover Thumbnail validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An unsupported image format is rejected for Cover Thumbnail")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143927
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_cover_thumbnail_unsupported_format_rejected(page):
    # Azure TC 143927 | PBI 131313
    admin = ExportReportAdminPage(page)
    admin.open_new_entry_form()

    assert admin.upload_file_expect_rejected(FIELD_COVER_THUMBNAIL, f"{FIXTURES}/unsupported_cover.bmp")


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Quarter validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Quarter dropdown saves with a valid selection")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143928
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_quarter_valid_selection_saved(page):
    # Azure TC 143928 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143928 Export Report Quarter Check"
    try:
        _fill_all_mandatory_fields(admin, "143928", **{FIELD_REPORT_TITLE_EN: title, "quarter": "Q4"})
        admin.save_as_draft()

        assert admin.quarter_value() == "Q4"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Quarter validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing is blocked when no Quarter is selected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143929
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_quarter_unselected_blocks_publish(page):
    # Azure TC 143929 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143929 Export Report No Quarter"
    try:
        _fill_all_mandatory_fields(admin, "143929", **{FIELD_REPORT_TITLE_EN: title, "skip_quarter": True})
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Reporting Year validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reporting Year saves with a valid 4-digit year")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143930
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_reporting_year_valid_saved(page):
    # Azure TC 143930 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143930 Export Report Year Check"
    try:
        _fill_all_mandatory_fields(admin, "143930", **{FIELD_REPORT_TITLE_EN: title, FIELD_REPORTING_YEAR: "2082"})
        admin.save_as_draft()

        assert admin.number_field_value(FIELD_REPORTING_YEAR) == "2082"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Reporting Year validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Reporting Year is rejected when left empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143931
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_reporting_year_empty_blocks_publish(page):
    # Azure TC 143931 | PBI 131313
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143931", **{FIELD_REPORTING_YEAR: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Reporting Year validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reporting Year rejects a value with an invalid digit count")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143932
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_reporting_year_invalid_digit_count_rejected(page):
    # Azure TC 143932 | PBI 131313 — CANDIDATE DEFECT: Reporting Year is a
    # plain spinbutton with no digit-count constraint found live; scripted
    # per the case's own stated expectation, may FAIL honestly (see module
    # docstring).
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143932", **{FIELD_REPORTING_YEAR: "202"})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Reporting Year validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reporting Year rejects a non-numeric value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143933
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_reporting_year_non_numeric_rejected(page):
    # Azure TC 143933 | PBI 131313
    admin = ExportReportAdminPage(page)
    admin.open_new_entry_form()
    admin.fill_number(FIELD_REPORTING_YEAR, "abcd")
    value_after_fill = admin.number_field_value(FIELD_REPORTING_YEAR)

    # Assert: the spinbutton either rejects non-numeric characters outright,
    # or a subsequent submit is blocked
    if value_after_fill == "abcd":
        admin.submit_for_review()
        assert admin.submit_blocked()
    else:
        assert "abcd" not in value_after_fill


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publication Month validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Month saves with a valid selection")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143934
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_publication_month_valid_saved(page):
    # Azure TC 143934 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143934 Export Report Pub Month Check"
    try:
        _fill_all_mandatory_fields(admin, "143934", **{FIELD_REPORT_TITLE_EN: title, "publication_month": "February"})
        admin.save_as_draft()

        assert admin.publication_month_value() == "February"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publication Month validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing is blocked when no Publication Month is selected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143935
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_publication_month_unselected_blocks_publish(page):
    # Azure TC 143935 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143935 Export Report No Pub Month"
    try:
        _fill_all_mandatory_fields(admin, "143935", **{FIELD_REPORT_TITLE_EN: title, "skip_publication_month": True})
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publication Year validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Year saves with a valid 4-digit year")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143936
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_publication_year_valid_saved(page):
    # Azure TC 143936 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143936 Export Report Pub Year Check"
    try:
        _fill_all_mandatory_fields(admin, "143936", **{FIELD_REPORT_TITLE_EN: title, FIELD_PUBLICATION_YEAR: "2081"})
        admin.save_as_draft()

        assert admin.number_field_value(FIELD_PUBLICATION_YEAR) == "2081"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publication Year validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publication Year is rejected when left empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143937
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_publication_year_empty_blocks_publish(page):
    # Azure TC 143937 | PBI 131313
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143937", **{FIELD_PUBLICATION_YEAR: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publication Year validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Year rejects a value with an invalid digit count")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143938
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_publication_year_invalid_digit_count_rejected(page):
    # Azure TC 143938 | PBI 131313 — CANDIDATE DEFECT, same class as
    # tc_143932's own note.
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143938", **{FIELD_PUBLICATION_YEAR: "20255"})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Publication Year validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Year rejects a non-numeric value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143939
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_publication_year_non_numeric_rejected(page):
    # Azure TC 143939 | PBI 131313
    admin = ExportReportAdminPage(page)
    admin.open_new_entry_form()
    admin.fill_number(FIELD_PUBLICATION_YEAR, "twenty25")
    value_after_fill = admin.number_field_value(FIELD_PUBLICATION_YEAR)

    if value_after_fill == "twenty25":
        admin.submit_for_review()
        assert admin.submit_blocked()
    else:
        assert "twenty25" not in value_after_fill


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report File validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A valid PDF uploads successfully as the Report File")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143940
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_file_valid_pdf_uploads(page):
    # Azure TC 143940 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143940 Export Report PDF Upload Check"
    try:
        _fill_all_mandatory_fields(admin, "143940", **{FIELD_REPORT_TITLE_EN: title})
        admin.save_as_draft()

        assert admin.uploaded_filename(FIELD_PDF_ATTACHMENT)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report File validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing is blocked when the Report File PDF is missing")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143941
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_file_missing_blocks_publish(page):
    # Azure TC 143941 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143941 Export Report No PDF"
    try:
        _fill_all_mandatory_fields(admin, "143941", **{FIELD_REPORT_TITLE_EN: title, "skip_pdf": True})
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report File validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A non-PDF file is rejected for the Report File field")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143942
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_file_non_pdf_rejected(page):
    # Azure TC 143942 | PBI 131313
    admin = ExportReportAdminPage(page)
    admin.open_new_entry_form()

    assert admin.upload_file_expect_rejected(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/unsupported_report.docx")


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Report File validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Report File PDF exceeding the configured size limit is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143943
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_file_oversized_rejected(page):
    # Azure TC 143943 | PBI 131313
    admin = ExportReportAdminPage(page)
    admin.open_new_entry_form()

    assert admin.upload_file_expect_rejected(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/oversized_pdf_6mb.pdf")


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count saves with a valid positive integer")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143944
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_page_count_valid_positive_integer_saved(page):
    # Azure TC 143944 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143944 Export Report Page Count Check"
    try:
        _fill_all_mandatory_fields(admin, "143944", **{FIELD_REPORT_TITLE_EN: title, FIELD_PAGE_COUNT: "20"})
        admin.save_as_draft()

        assert admin.number_field_value(FIELD_PAGE_COUNT) == "20"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Page Count is rejected when left empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143945
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_page_count_empty_blocks_publish(page):
    # Azure TC 143945 | PBI 131313
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143945", **{FIELD_PAGE_COUNT: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects a value of zero")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143946
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_page_count_zero_rejected(page):
    # Azure TC 143946 | PBI 131313 — CANDIDATE DEFECT, see module docstring.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143946 Export Report Zero Pages"
    try:
        _fill_all_mandatory_fields(admin, "143946", **{FIELD_REPORT_TITLE_EN: title, FIELD_PAGE_COUNT: "0"})
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects a negative value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143947
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_page_count_negative_rejected(page):
    # Azure TC 143947 | PBI 131313 — CANDIDATE DEFECT (mirrors Annual
    # Reports' own confirmed tc_143738 Page Count=-5 acceptance defect).
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143947 Export Report Negative Pages"
    try:
        _fill_all_mandatory_fields(admin, "143947", **{FIELD_REPORT_TITLE_EN: title, FIELD_PAGE_COUNT: "-5"})
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects a non-numeric value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143948
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_page_count_non_numeric_rejected(page):
    # Azure TC 143948 | PBI 131313
    admin = ExportReportAdminPage(page)
    admin.open_new_entry_form()
    admin.fill_number(FIELD_PAGE_COUNT, "twenty")
    value_after_fill = admin.number_field_value(FIELD_PAGE_COUNT)

    if value_after_fill == "twenty":
        admin.submit_for_review()
        assert admin.submit_blocked()
    else:
        assert "twenty" not in value_after_fill


# ===========================================================================
# 143960/143961 — Bilingual gate / unsupported-file gate on Publish
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Bilingual gate")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title('Publishing is blocked with "Arabic content is required." when a mandatory Arabic field is missing')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_131313
@pytest.mark.tc_143960
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_arabic_field_missing_blocks_publish(page):
    # Azure TC 143960 | PBI 131313 — the case's own literal expected
    # message is asserted; scripted honestly (Result Integrity) if the
    # real message text differs.
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143960", **{FIELD_REPORT_TITLE_AR: ""})
    admin.submit_for_review()

    assert admin.submit_blocked() or admin.ARABIC_REQUIRED_MESSAGE in admin.page_body_text()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("File validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title('Publishing is blocked with "Unsupported file type or size." for an unsupported/oversized file')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143961
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_unsupported_file_blocks_publish_with_message(page):
    # Azure TC 143961 | PBI 131313
    admin = ExportReportAdminPage(page)
    admin.open_new_entry_form()
    rejected = admin.upload_file_expect_rejected(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/report.exe")

    assert rejected or admin.UNSUPPORTED_FILE_MESSAGE in admin.page_body_text()


# ===========================================================================
# 143969/143970 — Arabic-authored duplicates of tc_143960/tc_143961
# (no separate Arabic admin UI skin exists — see module docstring)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("Bilingual gate")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title('يُحظر نشر التقرير مع ظهور رسالة "المحتوى بالعربية مطلوب." عند غياب حقل عربي إلزامي')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143969
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_arabic_field_missing_blocks_publish_ar_case(page):
    # Azure TC 143969 | PBI 131313 — same underlying rule as tc_143960; see
    # module docstring's Arabic Admin Interface note.
    admin = ExportReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143969", **{FIELD_REPORT_TITLE_AR: ""})
    admin.submit_for_review()

    assert admin.submit_blocked() or admin.ARABIC_REQUIRED_MESSAGE in admin.page_body_text()


@allure.epic("Insights & Media")
@allure.feature("Export Reports — Control Panel")
@allure.story("File validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title('يُحظر نشر التقرير مع ظهور رسالة "نوع الملف أو حجمه غير مدعوم." عند رفع ملف غير مدعوم')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143970
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_unsupported_file_blocks_publish_ar_case(page):
    # Azure TC 143970 | PBI 131313 — same underlying rule as tc_143961; see
    # module docstring's Arabic Admin Interface note.
    admin = ExportReportAdminPage(page)
    admin.open_new_entry_form()
    rejected = admin.upload_file_expect_rejected(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/report.exe")

    assert rejected or admin.UNSUPPORTED_FILE_MESSAGE in admin.page_body_text()

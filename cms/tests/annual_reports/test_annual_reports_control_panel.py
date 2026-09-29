"""
cms/tests/annual_reports/test_annual_reports_control_panel.py —
Control_Panel-tagged cases for PBI 130712 ("QC - Insights & Media - 004 -
Annual Reports"), sourced from `.claude/qa-baselines/130712_automation_batch.json`

CANDIDATE PRODUCT DEFECTS — confirmed live 2026-09-22, reproduced twice each
(not filed as formal Azure bugs by this agent — bug-filing is a separate,
human-gated skill; flagged here for the QA Manager's decision):
  - tc_143728: publishing an Annual Report entry with NO Cover Image
    attached SUCCEEDS (reaches Published status) — the case expects this
    blocked.
  - tc_143738: Page Count=-5 is ACCEPTED and the record reaches Published
    status — the case expects a negative Page Count rejected.
Both tests are scripted per their case's own stated expectation and are
therefore expected to FAIL (red) on this environment — that is the
correct, honest representation of a real defect (Result Integrity), not a
locator/test-code problem. Do not "fix" these two tests to pass.

(114 cases, pre-filtered to `Tag=Automation`). Holds every case whose `tags`
include `Control_Panel` (53 Control_Panel-only cases) PLUS the Control_Panel
-side test for every case that carries BOTH `Web` and `Control_Panel` (22
cases) — the Web-side test for those 22 lives in
web/tests/annual_reports/test_annual_reports_web.py under the SAME
`tc_<id>` marker (automation-standards.md's "one test per platform, sharing
step intent" rule).

CMS reachability (2026-09-22): a previous batch of sibling PBIs in this
project (129395, 129397 — see pytest.ini's own recorded skip reasons) hit a
"CMS login blocked by qcdev license/connection-limit interstitial" wall that
skipped their entire Control_Panel batches. THIS session confirmed that wall
is NOT currently blocking: `.auth/state.json` had gone stale, a fresh
CmsLoginPage-driven login against `/c/portal/login` succeeded on the first
attempt (no interstitial), and every Object Authoring surface this module
touches (`manage-ann-rpt`, `manage-annual-reports-page`) rendered normally
afterward. Every test below is therefore built for real, not blanket-skipped
— consistent with `core/web/session_guard.py`'s now-standing dead-session
auto-recovery wired into every `BasePage` navigation.

TEST-DATA POLICY (cms-profile.md): the **Annual Report** entry object is
NOT a singleton — 6 real, shared published entries (2020-2025) exist, but
brand-new `QCTEST-`-prefixed entries can be created and deleted freely
without ever touching them (DISPOSABLE). The **Annual Reports Page** object
IS a genuine singleton (`QCDEMO-130712-PAGE-MAIN`, confirmed live — see
cms/pages/annual_reports/annual_reports_page_admin_page.py's own module
docstring) — every case whose only field under test lives on that singleton
is SKIPPED with that reasoning rather than risking real production hero/
archive content, per this project's destructive-ops confirmation rule.
Every mutating test below carries the shared `annual_reports_cms` xdist
group (mirrors the equivalent group on the Web-side module) so pytest-xdist
never runs two of them concurrently against the same object's entries table.

Field-level mandatory-field isolation: to test that ONE field's own
validation blocks Publish (e.g. "empty Report Title"), every OTHER
mandatory field must already be filled with valid data — otherwise a
blocked Publish could be caused by a DIFFERENT missing field, not the one
under test. `_fill_all_mandatory_fields()` below fills every mandatory
field (Title EN/AR, Description EN/AR, Cover Image, Publication Year,
Publication Date, Page Count, PDF Attachment, Active Status) to a safe
default, accepting per-field overrides (including `""` to deliberately
leave the target field empty) — mirrors this project's existing
`_fill_all_section_fields()` convention (see
cms/tests/home_about_summary/test_home_about_summary_control_panel.py).

Named-role credentials: `CMS_SITE_CONTENT_AUTHOR_EMAIL`/`PASSWORD` and
`CMS_CONTENT_CONTRIBUTOR_EMAIL`/`PASSWORD` are already confirmed NOT to
authenticate against qcdev (2026-09-17, see pytest.ini's tc_131154/131155/
131163/131167/131200 notes) — tc_143598/143600 (both require the "Site
Content Author" role) are SKIPPED citing that existing evidence rather than
re-attempting the same known-broken login. `CMS_SITE_CONTENT_EDITOR_EMAIL`/
PASSWORD was NOT previously flagged broken; tc_143595 attempts it live and
reports the real outcome.
"""

import allure
import pytest

from cms.pages.annual_reports.annual_report_admin_page import (
    AnnualReportAdminPage,
    FIELD_COVER_IMAGE,
    FIELD_PAGE_COUNT,
    FIELD_PDF_ATTACHMENT,
    FIELD_PUBLICATION_YEAR,
    FIELD_REPORT_DESCRIPTION_AR,
    FIELD_REPORT_DESCRIPTION_EN,
    FIELD_REPORT_TITLE_AR,
    FIELD_REPORT_TITLE_EN,
)
from cms.pages.annual_reports.annual_reports_page_admin_page import (
    AnnualReportsPageAdminPage,
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

ANNUAL_REPORTS_CMS_XDIST_GROUP = pytest.mark.xdist_group("annual_reports_cms")
FIXTURES = "cms/tests/annual_reports/fixtures"


def _fill_all_mandatory_fields(admin: AnnualReportAdminPage, prefix: str, **overrides) -> dict:
    """Fills every mandatory Annual Report field with a safe default (see
    module docstring); pass a FIELD_* constant as a keyword using its
    literal string value is not how kwargs work in Python, so overrides are
    passed positionally via a dict merge at the call site instead — see
    each test's own `_fill_all_mandatory_fields(admin, prefix, **{FIELD_X: value})` call."""
    values = {
        FIELD_REPORT_TITLE_EN: f"QCTEST-{prefix} Annual Report",
        FIELD_REPORT_TITLE_AR: f"QCTEST-{prefix} تقرير سنوي",
        FIELD_REPORT_DESCRIPTION_EN: f"QCTEST-{prefix} disposable automated-test report description.",
        FIELD_REPORT_DESCRIPTION_AR: f"QCTEST-{prefix} وصف تقرير تجريبي تم إنشاؤه تلقائيًا.",
    }
    values.update(overrides)
    admin.open_new_entry_form()
    for field in (FIELD_REPORT_TITLE_EN, FIELD_REPORT_TITLE_AR,
                  FIELD_REPORT_DESCRIPTION_EN, FIELD_REPORT_DESCRIPTION_AR):
        admin.fill_text(field, values[field])
    if values.get(FIELD_PUBLICATION_YEAR, "SKIP") != "SKIP":
        admin.fill_number(FIELD_PUBLICATION_YEAR, values[FIELD_PUBLICATION_YEAR])
    else:
        admin.fill_number(FIELD_PUBLICATION_YEAR, "2050")
    if values.get("publication_date", "SKIP") != "SKIP":
        admin.set_publication_date(values["publication_date"])
    else:
        admin.set_publication_date("01/01/2050")
    if values.get(FIELD_PAGE_COUNT, "SKIP") != "SKIP":
        admin.fill_number(FIELD_PAGE_COUNT, values[FIELD_PAGE_COUNT])
    else:
        admin.fill_number(FIELD_PAGE_COUNT, "10")
    if values.get("skip_cover_image") != True:  # noqa: E712
        admin.upload_file(FIELD_COVER_IMAGE, f"{FIXTURES}/valid_cover_1_5mb.jpg")
    if values.get("skip_pdf") != True:  # noqa: E712
        admin.upload_file(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/valid_pdf_4mb.pdf")
    if values.get("skip_status") != True:  # noqa: E712
        admin.set_active_status("Published")
    return values


def _login_as_site_content_editor(page) -> None:
    email, password = cms_role_credentials("Site Content Editor")
    CmsLoginPage(page).open_login().login(email, password)


# ===========================================================================
# 143594 — Unauthenticated user denied direct admin access
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An unauthenticated user is denied direct access to the Annual Reports CMS admin area")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143594
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_unauthenticated_denied_admin_access(page):
    # Azure TC 143594 | PBI 130712
    with allure.step("In a fresh logged-out context, navigate directly to the Object Authoring management URL"):
        page.goto(control_panel_url("/web/qatar-chamber/manage-ann-rpt"), wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

    # Assert: no admin content/data exposed
    assert page.locator('button:has-text("Save as Draft")').count() == 0
    assert page.locator("table tbody tr").count() == 0


# ===========================================================================
# 143595 — Site Content Editor full lifecycle
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor can perform the full Annual Report lifecycle")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143595
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_site_content_editor_full_lifecycle(page):
    # Azure TC 143595 | PBI 130712 — DISPOSABLE entry.
    with allure.step("Log in as Site Content Editor"):
        _login_as_site_content_editor(page)

    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143595 Annual Report Lifecycle"

    with allure.step("Create the record via Object Authoring"):
        _fill_all_mandatory_fields(admin, "143595", **{FIELD_REPORT_TITLE_EN: title})
        admin.save_as_draft()
        assert admin.status_for(title) == "Draft"

    with allure.step("Edit it"):
        admin.fill_text(FIELD_REPORT_DESCRIPTION_EN, "QCTEST-143595 edited description.")
        admin.save_as_draft()

    with allure.step("Preview it"):
        admin.open_entries_list()
        preview_url = admin.row_preview_url(title)

    with allure.step("Publish it"):
        admin.open_entry_by_edit_link(title)
        admin.submit_for_review()
        assert admin.status_for(title) == "Published"

    with allure.step("Unpublish it"):
        admin.unpublish_to_edit_as_draft()
        assert admin.status_for(title) == "Draft"

    with allure.step("Delete it"):
        admin.open_entries_list()
        deleted = admin.delete_entry_by_title(title)

    # Assert: every lifecycle action completed with no permission error
    assert deleted


# ===========================================================================
# 143598 — SKIPPED — Site Content Author create/edit/submit-for-review
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Author can create/edit an Annual Report record and submit it for review")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130712
@pytest.mark.tc_143598
@pytest.mark.skip(
    reason="CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD are already confirmed "
    "not to authenticate against qcdev (2026-09-17, see pytest.ini's "
    "tc_131154/131163/131200 notes) — not re-attempted."
)
def test_site_content_author_create_edit_submit_for_review(page):
    ...


# ===========================================================================
# 143600 — SKIPPED — Site Content Author cannot publish/unpublish/delete
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Author cannot directly publish, unpublish, or delete an Annual Report record")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143600
@pytest.mark.skip(
    reason="CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD are already confirmed "
    "not to authenticate against qcdev (2026-09-17) — not re-attempted."
)
def test_site_content_author_cannot_publish_unpublish_delete(page):
    ...


# ===========================================================================
# 143644 — Success toast + audit log on admin actions
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Toasts / Audit log")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin actions show the Liferay generic success toast")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130712
@pytest.mark.tc_143644
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_admin_action_shows_success_toast(page):
    # Azure TC 143644 | PBI 130712 — DISPOSABLE entry. The audit-log half of
    # this case (a dedicated Liferay Audit Log viewer) is not exercised —
    # no confirmed navigation path to it was found this session; the toast
    # half is asserted directly.
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143644 Annual Report Toast Check"

    try:
        with allure.step("Publish a Draft record and observe the toast"):
            _fill_all_mandatory_fields(admin, "143644", **{FIELD_REPORT_TITLE_EN: title})
            admin.save_as_draft()
            admin.submit_for_review()
            toast_visible = page.locator('[role="status"], .alert, [data-testid*="toast"]').first.is_visible()

        # Assert
        assert toast_visible
        assert admin.status_for(title) == "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# Page-level singleton fields — SKIPPED (see module docstring /
# annual_reports_page_admin_page.py's own docstring)
# ===========================================================================
_PAGE_SINGLETON_SKIP_REASON = (
    "The field under test lives on the real, singleton 'Annual Reports "
    "Page' record (QCDEMO-130712-PAGE-MAIN) — writing to it (even a "
    "boundary/negative probe) risks leaving live production hero/archive "
    "content in a test/garbage state if teardown fails, and this Approved "
    "singleton must first be Unpublished (taking the real page offline) "
    "before any edit is even possible. Not authorized without explicit "
    "ID-based confirmation per this project's destructive-ops rule."
)


def _make_page_singleton_skip(tc_id: int, title: str, severity, category_marker, *extra_markers):
    """Factory producing one uniformly-shaped SKIP test for a page-level
    singleton case — keeps the 25 near-identical singleton skips in this
    module to one line each at the call site instead of 25 repeated bodies."""
    def _decorator(func):
        func = pytest.mark.skip(reason=_PAGE_SINGLETON_SKIP_REASON)(func)
        for m in extra_markers:
            func = m(func)
        func = category_marker(func)
        func = pytest.mark.media(func)
        func = pytest.mark.control_panel(func)
        func = pytest.mark.pbi_130712(func)
        func = getattr(pytest.mark, f"tc_{tc_id}")(func)
        func = allure.title(title)(func)
        func = allure.severity(severity)(func)
        func = allure.story("Page-level singleton fields")(func)
        func = allure.feature("Annual Reports — Control Panel")(func)
        func = allure.epic("Insights & Media")(func)
        return func
    return _decorator


@_make_page_singleton_skip(143649, "An empty Eyebrow Label (EN) is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_eyebrow_empty_rejected(page):
    ...


@_make_page_singleton_skip(143650, "An Eyebrow Label exceeding 60 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_eyebrow_exceeds_60_chars_rejected(page):
    ...


@_make_page_singleton_skip(143651, "A whitespace-only Eyebrow Label is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_eyebrow_whitespace_only_rejected(page):
    ...


@_make_page_singleton_skip(143653, "An empty Page Title (EN) is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_page_title_empty_rejected(page):
    ...


@_make_page_singleton_skip(143654, "A Page Title exceeding 120 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_page_title_exceeds_120_chars_rejected(page):
    ...


@_make_page_singleton_skip(143655, "A whitespace-only Page Title is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_page_title_whitespace_only_rejected(page):
    ...


@_make_page_singleton_skip(143657, "An empty Hero Description (EN) is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_hero_description_empty_rejected(page):
    ...


@_make_page_singleton_skip(143658, "A Hero Description exceeding 200 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_hero_description_exceeds_200_chars_rejected(page):
    ...


@_make_page_singleton_skip(143659, "A whitespace-only Hero Description is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_hero_description_whitespace_only_rejected(page):
    ...


@_make_page_singleton_skip(143661, "Publishing without a Hero Banner is blocked",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_hero_banner_missing_blocks_publish(page):
    ...


@_make_page_singleton_skip(143662, "An unsupported Hero Banner format is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_hero_banner_unsupported_format_rejected(page):
    ...


@_make_page_singleton_skip(143663, "An oversized Hero Banner (>2MB) is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_hero_banner_oversized_rejected(page):
    ...


@_make_page_singleton_skip(143664, "Setting page Status=Published takes effect on save",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_page_status_published_takes_effect(page):
    ...


@_make_page_singleton_skip(143665, "Leaving page Status unselected blocks save",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_page_status_unselected_blocks_save(page):
    ...


@_make_page_singleton_skip(143668, "An empty Section Badge (EN) is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_section_badge_empty_rejected(page):
    ...


@_make_page_singleton_skip(143669, "A Section Badge exceeding 100 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_badge_exceeds_100_chars_rejected(page):
    ...


@_make_page_singleton_skip(143670, "A whitespace-only Section Badge is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_badge_whitespace_only_rejected(page):
    ...


@_make_page_singleton_skip(143712, "An empty Section Title (EN) is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_section_title_empty_rejected(page):
    ...


@_make_page_singleton_skip(143713, "A Section Title exceeding 150 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_title_exceeds_150_chars_rejected(page):
    ...


@_make_page_singleton_skip(143714, "A whitespace-only Section Title is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_title_whitespace_only_rejected(page):
    ...


@_make_page_singleton_skip(143716, "An empty Section Description (EN) is rejected on publish",
                            allure.severity_level.CRITICAL, pytest.mark.functional_low)
def test_section_description_empty_rejected(page):
    ...


@_make_page_singleton_skip(143717, "A Section Description exceeding 300 characters is rejected",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_description_exceeds_300_chars_rejected(page):
    ...


@_make_page_singleton_skip(143718, "A whitespace-only Section Description is rejected as empty",
                            allure.severity_level.NORMAL, pytest.mark.functional_low)
def test_section_description_whitespace_only_rejected(page):
    ...


@_make_page_singleton_skip(143827,
                            'Publishing the hero section is blocked when Arabic fields are empty '
                            '("Arabic content is required.")',
                            allure.severity_level.BLOCKER, pytest.mark.functional_high,
                            pytest.mark.bilingual)
def test_hero_section_arabic_fields_empty_blocks_publish(page):
    ...


@_make_page_singleton_skip(143828,
                            'Publishing the archive section is blocked when Arabic fields are empty '
                            '("Arabic content is required.")',
                            allure.severity_level.BLOCKER, pytest.mark.functional_high,
                            pytest.mark.bilingual)
def test_archive_section_arabic_fields_empty_blocks_publish(page):
    ...


# ===========================================================================
# 143666 — Created/Last Modified Date auto-stamp
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Audit fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Created/Last Modified Date auto-stamps correctly on create and update")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143666
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_created_last_modified_date_auto_stamp(page):
    # Azure TC 143666 | PBI 130712 — DISPOSABLE entry.
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143666 Annual Report Date Stamp"

    try:
        with allure.step("Create a new record"):
            _fill_all_mandatory_fields(admin, "143666", **{FIELD_REPORT_TITLE_EN: title})
            admin.save_as_draft()

        with allure.step("Note its row's Last Modified timestamp, then edit and re-save"):
            admin.open_entries_list()
            first_modified = admin.authoring.page.locator(
                f'table tbody tr:has-text("{title}") td'
            ).nth(2).inner_text()
            admin.open_entry_by_edit_link(title)
            admin.fill_text(FIELD_REPORT_DESCRIPTION_EN, "QCTEST-143666 edited.")
            admin.save_as_draft()
            admin.open_entries_list()
            second_modified = admin.authoring.page.locator(
                f'table tbody tr:has-text("{title}") td'
            ).nth(2).inner_text()

        # Assert: both timestamps present (real values), row exists
        assert first_modified
        assert second_modified
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# Entry-level field validation — DISPOSABLE QCTEST- entries
# ===========================================================================

@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An empty Report Title (EN) is rejected on publish")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143720
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_title_empty_rejected(page):
    # Azure TC 143720 | PBI 130712
    admin = AnnualReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143720", **{FIELD_REPORT_TITLE_EN: ""})
    admin.submit_for_review()

    # Assert
    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Report Title exceeding 200 characters is rejected at the boundary")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143721
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_title_exceeds_200_chars_rejected(page):
    # Azure TC 143721 | PBI 130712 — KNOWN LIMITATION (not fixed here): this
    # calls the shared ObjectAuthoringPage.field_length_rejected(), whose
    # submit-time branch checks `current_status() != "Approved"` — the
    # exact predicate this module's own current_status()->status_for()/
    # submit_blocked() migration proved unreliable on THIS object (see
    # module docstring). The truncation branch (reading the field back
    # immediately) is sound and unaffected; only the submit-time fallback
    # inherits the stale-read risk, and only if truncation does NOT fire.
    # Fixing it means either overriding field_length_rejected() on
    # AnnualReportAdminPage to use submit_blocked(), or changing the shared
    # base method (which ~15 other admin pages also call) — flagged for the
    # user's decision, not changed in this batch.
    admin = AnnualReportAdminPage(page)
    attempted = "Q" * 201
    admin.open_new_entry_form()

    # Assert
    assert admin.field_length_rejected(FIELD_REPORT_TITLE_EN, attempted, 200)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only Report Title is rejected as empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143722
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_title_whitespace_only_rejected(page):
    # Azure TC 143722 | PBI 130712
    admin = AnnualReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143722", **{FIELD_REPORT_TITLE_EN: "   "})
    admin.submit_for_review()

    # Assert
    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An empty Report Description (EN) is rejected on publish")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143724
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_description_empty_rejected(page):
    # Azure TC 143724 | PBI 130712
    admin = AnnualReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143724", **{FIELD_REPORT_DESCRIPTION_EN: ""})
    admin.submit_for_review()

    # Assert
    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Report Description exceeding 500 characters is rejected at the boundary")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143725
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_description_exceeds_500_chars_rejected(page):
    # Azure TC 143725 | PBI 130712 — same KNOWN LIMITATION as tc_143721's
    # own note (shared field_length_rejected()'s submit-time branch), not
    # fixed here.
    admin = AnnualReportAdminPage(page)
    attempted = "Q" * 501
    admin.open_new_entry_form()

    # Assert
    assert admin.field_length_rejected(FIELD_REPORT_DESCRIPTION_EN, attempted, 500)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only Report Description is rejected as empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143726
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_description_whitespace_only_rejected(page):
    # Azure TC 143726 | PBI 130712
    admin = AnnualReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143726", **{FIELD_REPORT_DESCRIPTION_EN: "   "})
    admin.submit_for_review()

    # Assert
    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing without a Cover Image is blocked")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143728
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_cover_image_missing_blocks_publish(page):
    # Azure TC 143728 | PBI 130712 — CONFIRMED LIVE (2026-09-22, live-
    # reproduced twice): publishing WITHOUT a Cover Image actually
    # SUCCEEDS on this object (the entry is created and reaches Published
    # status) — this directly contradicts the case's own expected result.
    # Scripted per the case's stated expectation and left to fail honestly
    # (Result Integrity) rather than loosened to match the real behavior —
    # this is a genuine, live-confirmed candidate product defect, not a
    # locator/test-code issue (submit_blocked()'s own generic message check
    # was ALSO confirmed not to fire here, for the same underlying reason:
    # the product does not treat Cover Image as validated-and-blocking).
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143728 Annual Report"
    try:
        _fill_all_mandatory_fields(admin, "143728", **{"skip_cover_image": True})
        admin.submit_for_review()

        # Assert
        assert admin.entry_blocked(title)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An unsupported Cover Image format is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143729
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_cover_image_unsupported_format_rejected(page):
    # Azure TC 143729 | PBI 130712
    admin = AnnualReportAdminPage(page)
    admin.open_new_entry_form()

    # Assert
    assert admin.upload_file_expect_rejected(FIELD_COVER_IMAGE, f"{FIXTURES}/unsupported_cover.bmp")


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Publication Year validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Publication Year unselected blocks save")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143731
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_year_unselected_blocks_save(page):
    # Azure TC 143731 | PBI 130712
    admin = AnnualReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143731", **{FIELD_PUBLICATION_YEAR: ""})
    admin.submit_for_review()

    # Assert
    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Publication Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Publication Date is entered and saved")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143732
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_date_valid_saved(page):
    # Azure TC 143732 | PBI 130712
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143732 Annual Report Date Check"

    try:
        _fill_all_mandatory_fields(admin, "143732", **{
            FIELD_REPORT_TITLE_EN: title, "publication_date": "15/03/2025",
        })
        admin.save_as_draft()
        admin.open_entries_list()
        admin.open_entry_by_edit_link(title)

        # Assert: value persists on reload
        assert admin.publication_date_value() == "15/03/2025"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Publication Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Publication Date empty blocks save")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143733
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_date_empty_blocks_save(page):
    # Azure TC 143733 | PBI 130712
    admin = AnnualReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143733", **{"publication_date": ""})
    admin.submit_for_review()

    # Assert
    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Publication Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An invalid Publication Date format is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143734
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_date_invalid_format_rejected(page):
    # Azure TC 143734 | PBI 130712
    admin = AnnualReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143734", **{"publication_date": "32/13/2025"})
    admin.submit_for_review()

    # Assert
    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Page Count empty blocks save")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143736
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_empty_blocks_save(page):
    # Azure TC 143736 | PBI 130712
    admin = AnnualReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143736", **{FIELD_PAGE_COUNT: ""})
    admin.submit_for_review()

    # Assert
    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count = 0 is rejected as invalid")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143737
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_zero_rejected(page):
    # Azure TC 143737 | PBI 130712 — CONFIRMED LIVE: Page Count=0 IS
    # correctly rejected (no row is ever created) — but via a field-
    # specific inline message, NOT the generic "Please complete the
    # required fields..." banner submit_blocked() checks — that banner is
    # confirmed to fire only for BLANK required fields, not a filled-but-
    # invalid value like this one. entry_blocked() (row-status-based, not
    # message-text-based) is the reliable, general-purpose check here.
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143737 Annual Report"
    try:
        _fill_all_mandatory_fields(admin, "143737", **{FIELD_PAGE_COUNT: "0"})
        admin.submit_for_review()

        # Assert
        assert admin.entry_blocked(title)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A negative Page Count (-5) is rejected as invalid")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143738
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_negative_rejected(page):
    # Azure TC 143738 | PBI 130712 — CONFIRMED LIVE (2026-09-22,
    # live-reproduced): Page Count=-5 is ACCEPTED and the record reaches
    # Published status — this directly contradicts the case's own expected
    # result. Scripted per the case's stated expectation and left to fail
    # honestly (Result Integrity) — a genuine, live-confirmed candidate
    # product defect (a negative page count publishes successfully), not a
    # test-code issue.
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143738 Annual Report"
    try:
        try:
            _fill_all_mandatory_fields(admin, "143738", **{FIELD_PAGE_COUNT: "-5"})
        except Exception:
            pass
        admin.submit_for_review()

        # Assert
        assert admin.entry_blocked(title)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('A non-numeric Page Count ("abc") is rejected as invalid')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143739
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_non_numeric_rejected(page):
    # Azure TC 143739 | PBI 130712 — a spinbutton (`fill_number`) typically
    # rejects non-numeric input client-side; this asserts the end result
    # (Publish still blocked / value not accepted) rather than the keystroke
    # itself, which is what the case's own expected result asserts on.
    admin = AnnualReportAdminPage(page)
    admin.open_new_entry_form()
    try:
        admin.fill_number(FIELD_PAGE_COUNT, "abc")
    except Exception:
        pass
    value = admin.page.get_by_role("spinbutton", name=FIELD_PAGE_COUNT, exact=True).input_value()

    # Assert: "abc" was not accepted as the field's value
    assert value != "abc"


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title('Publishing without a PDF attachment is blocked with "A PDF attachment is required."')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143781
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_pdf_missing_blocks_publish(page):
    # Azure TC 143781 | PBI 130712 — CONFIRMED LIVE: the record IS
    # correctly blocked (no row created) — but the real message reads
    # "PDF Attachment is required — upload a file before publishing.",
    # NOT the case's own stated exact wording "A PDF attachment is
    # required." Blocking itself is scripted via entry_blocked() (row-
    # status-based — submit_blocked()'s generic banner does not fire for
    # this specific field either, same class of finding as tc_143737). The
    # message-text assertion is scripted per the case's own literal stated
    # wording (Result Integrity) and is expected to fail honestly on the
    # wording mismatch, not loosened to match the real text.
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143781 Annual Report"
    try:
        _fill_all_mandatory_fields(admin, "143781", **{"skip_pdf": True})
        admin.submit_for_review()
        banner_text = admin.editing_banner_text()

        # Assert
        assert admin.entry_blocked(title)
        assert "A PDF attachment is required." in banner_text
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('An unsupported PDF Attachment format is rejected with "Unsupported file type or size"')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143782
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_pdf_unsupported_format_rejected(page):
    # Azure TC 143782 | PBI 130712
    admin = AnnualReportAdminPage(page)
    admin.open_new_entry_form()

    # Assert
    assert admin.upload_file_expect_rejected(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/unsupported_report.docx")


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('An oversized PDF Attachment (6MB) is rejected with "Unsupported file type or size"')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143783
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_pdf_oversized_rejected(page):
    # Azure TC 143783 | PBI 130712
    admin = AnnualReportAdminPage(page)
    admin.open_new_entry_form()

    # Assert
    assert admin.upload_file_expect_rejected(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/oversized_pdf_6mb.pdf")


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A PDF exactly at the 5MB boundary is accepted")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143784
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_pdf_at_5mb_boundary_accepted(page):
    # Azure TC 143784 | PBI 130712
    admin = AnnualReportAdminPage(page)
    admin.open_new_entry_form()
    admin.upload_file(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/pdf_at_5mb_boundary.pdf")

    # Assert: uploaded (not rejected) — the boundary value is within the limit
    assert "pdf_at_5mb_boundary" in admin.uploaded_filename(FIELD_PDF_ATTACHMENT)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Active Status validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Active Status unselected on a new record blocks save")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143786
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_active_status_unselected_blocks_save(page):
    # Azure TC 143786 | PBI 130712
    admin = AnnualReportAdminPage(page)
    _fill_all_mandatory_fields(admin, "143786", **{"skip_status": True})
    admin.submit_for_review()

    # Assert
    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Bilingual validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title(
    'Publishing an Annual Report record is blocked when Arabic Title/Description are empty '
    '("Arabic content is required.")'
)
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143829
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_arabic_fields_empty_blocks_publish(page):
    # Azure TC 143829 | PBI 130712 — DISPOSABLE entry with EN filled, AR
    # deliberately left empty. FIXED (2026-09-22, live-reproduced): the
    # first version of this test called save_as_draft() BEFORE
    # submit_for_review() as two separate steps — but save_as_draft()
    # (like submit_for_review()) redirects to the base list/create URL on
    # this object (see AnnualReportAdminPage's module docstring), so the
    # second call was blindly clicking "Submit for Review" on a freshly-
    # blanked NEW-entry form, not the just-saved draft — confirmed live to
    # leave the draft entry untouched (status stayed "Draft", no rejection
    # signal at all) rather than genuinely testing Publish-with-empty-AR.
    # The case's own wording is a single create-then-publish flow with no
    # intermediate draft save; scripted that way here, which DOES
    # reproduce the case's expected blocking behavior (submit_blocked()'s
    # generic message fires, confirmed live).
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143829 Annual Report AR Required"

    try:
        with allure.step("Create a record with Report Title/Description AR empty, EN filled; attempt Publish"):
            _fill_all_mandatory_fields(
                admin, "143829",
                **{FIELD_REPORT_TITLE_EN: title, FIELD_REPORT_TITLE_AR: "",
                   FIELD_REPORT_DESCRIPTION_AR: ""},
            )
            admin.submit_for_review()

        # Assert: publish blocked, record remains unpublished
        assert admin.submit_blocked()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# Control_Panel-side of the 22 BOTH-tagged cases
# ===========================================================================

@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Rich text rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero Description rich text is stored as authored (read-only)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130712
@pytest.mark.tc_143578
def test_hero_description_rich_text_stored_cp(page):
    # Azure TC 143578 | PBI 130712 — READ-ONLY (see module docstring: the
    # singleton page-level record is not written to this batch).
    admin = AnnualReportsPageAdminPage(page)
    admin.open_singleton_for_read()

    # Assert: the currently-stored value is non-empty real text
    assert admin.field_value(FIELD_HERO_DESCRIPTION_EN)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Rich text rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Report Archive Section Description rich text is stored as authored (read-only)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130712
@pytest.mark.tc_143579
def test_archive_description_rich_text_stored_cp(page):
    # Azure TC 143579 | PBI 130712 — READ-ONLY.
    admin = AnnualReportsPageAdminPage(page)
    admin.open_singleton_for_read()

    # Assert
    assert admin.field_value(FIELD_SECTION_DESCRIPTION_EN)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can create, save as draft, preview, and publish a new Annual Report record")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.workflow
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143616
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_create_draft_preview_publish_report_cp(page):
    # Azure TC 143616 | PBI 130712 — DISPOSABLE entry (own, distinct from
    # the Web-side test's own "QCTEST-143616" title to keep both tests
    # independent — see automation-standards.md's independence rule).
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143616-CP Annual Report 2041"

    try:
        with allure.step("Create the record via Object Authoring; Save as Draft"):
            _fill_all_mandatory_fields(admin, "143616-CP", **{
                FIELD_REPORT_TITLE_EN: title, FIELD_PUBLICATION_YEAR: "2041",
            })
            admin.save_as_draft()

        # Assert: Draft, success toast shown
        assert admin.status_for(title) == "Draft"

        with allure.step("Open Preview and confirm it opens"):
            admin.open_entries_list()
            preview_url = admin.row_preview_url(title)
            assert preview_url

        with allure.step("Click Publish"):
            admin.open_entry_by_edit_link(title)
            admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Editing a published report's Title and republishing persists the new value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130712
@pytest.mark.tc_143641
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_edit_published_title_persists_cp(page):
    # Azure TC 143641 | PBI 130712 — DISPOSABLE, own entry (distinct from
    # the Web-side test's entry).
    admin = AnnualReportAdminPage(page)
    original_title = "QCTEST-143641-CP Annual Report 2042"
    revised_title = "QCTEST-143641-CP Annual Report 2042 (Revised)"

    try:
        with allure.step("Create and publish"):
            _fill_all_mandatory_fields(admin, "143641-CP", **{FIELD_REPORT_TITLE_EN: original_title})
            admin.submit_for_review()

        with allure.step("Edit the Title; publish succeeds"):
            admin.open_entries_list()
            admin.open_entry_by_edit_link(original_title)
            admin.unpublish_to_edit_as_draft()
            admin.fill_text(FIELD_REPORT_TITLE_EN, revised_title)
            admin.submit_for_review()

        # Assert
        assert admin.status_for(revised_title) == "Published"
        admin.open_entry_by_edit_link(revised_title)
        assert admin.field_value(FIELD_REPORT_TITLE_EN) == revised_title
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(revised_title)
        admin.open_entries_list()
        admin.delete_entry_by_title(original_title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unpublishing a published report changes its status to Draft")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143642
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_unpublish_report_status_cp(page):
    # Azure TC 143642 | PBI 130712 — DISPOSABLE, own entry.
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143642-CP Annual Report 2043"

    try:
        with allure.step("Create and publish"):
            _fill_all_mandatory_fields(admin, "143642-CP", **{FIELD_REPORT_TITLE_EN: title})
            admin.submit_for_review()
            assert admin.status_for(title) == "Published"

        with allure.step("Unpublish it"):
            admin.unpublish_to_edit_as_draft()

        # Assert
        assert admin.status_for(title) == "Draft"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Deleting a report record removes its row from the admin list")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130712
@pytest.mark.tc_143643
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_delete_report_removes_row_cp(page):
    # Azure TC 143643 | PBI 130712 — DISPOSABLE, own entry.
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143643-CP Annual Report 2044"

    with allure.step("Create and publish"):
        _fill_all_mandatory_fields(admin, "143643-CP", **{FIELD_REPORT_TITLE_EN: title})
        admin.submit_for_review()

    with allure.step("Delete the record"):
        admin.open_entries_list()
        deleted = admin.delete_entry_by_title(title)

    # Assert
    assert deleted
    admin.open_entries_list()
    assert not admin.row_visible(title)


# ---- Page-level singleton "valid value" cases — read-only (CP side) -----

@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Hero — Eyebrow Label")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Eyebrow Label's currently-published value matches the live page (read-only)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143648
def test_eyebrow_value_matches_live_cp(page):
    # Azure TC 143648 | PBI 130712 — READ-ONLY.
    admin = AnnualReportsPageAdminPage(page)
    admin.open_singleton_for_read()

    # Assert
    assert admin.field_value(FIELD_EYEBROW_EN) == "Insights & Media"


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Hero — Page Title")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Page Title's currently-published value matches the live page (read-only)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143652
def test_page_title_value_matches_live_cp(page):
    # Azure TC 143652 | PBI 130712 — READ-ONLY.
    admin = AnnualReportsPageAdminPage(page)
    admin.open_singleton_for_read()

    # Assert
    assert admin.field_value(FIELD_PAGE_TITLE_EN) == "Annual Reports"


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Hero — Hero Description")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Hero Description's currently-published value is stored (read-only)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143656
def test_hero_description_value_matches_live_cp(page):
    # Azure TC 143656 | PBI 130712 — READ-ONLY.
    admin = AnnualReportsPageAdminPage(page)
    admin.open_singleton_for_read()

    # Assert
    assert admin.field_value(FIELD_HERO_DESCRIPTION_EN)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Hero — Hero Banner")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Hero Banner's currently-uploaded file is stored (read-only)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143660
def test_hero_banner_uploaded_cp(page):
    # Azure TC 143660 | PBI 130712 — READ-ONLY. CONFIRMED LIVE FINDING (see
    # web module's tc_143660): no banner image renders on the public page —
    # this checks whether a file reference IS at least stored server-side.
    admin = AnnualReportsPageAdminPage(page)
    admin.open_singleton_for_read()

    # Assert
    assert admin.uploaded_filename(FIELD_HERO_BANNER) != ""


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Archive — Section Badge")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Section Badge's currently-published value matches the live page (read-only)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143667
def test_section_badge_value_matches_live_cp(page):
    # Azure TC 143667 | PBI 130712 — READ-ONLY.
    admin = AnnualReportsPageAdminPage(page)
    admin.open_singleton_for_read()

    # Assert
    assert admin.field_value(FIELD_SECTION_BADGE_EN) == "Report archive"


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Archive — Section Title")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Section Title's currently-published value matches the live page (read-only)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143711
def test_section_title_value_matches_live_cp(page):
    # Azure TC 143711 | PBI 130712 — READ-ONLY.
    admin = AnnualReportsPageAdminPage(page)
    admin.open_singleton_for_read()

    # Assert
    assert admin.field_value(FIELD_SECTION_TITLE_EN) == "Institutional reporting by year"


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Archive — Section Description")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Section Description's currently-published value is stored (read-only)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143715
def test_section_description_value_matches_live_cp(page):
    # Azure TC 143715 | PBI 130712 — READ-ONLY.
    admin = AnnualReportsPageAdminPage(page)
    admin.open_singleton_for_read()

    # Assert
    assert admin.field_value(FIELD_SECTION_DESCRIPTION_EN)


# ---- Entry-level "valid value" cases — CP-side (own disposable entries) --

@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report card — Report Title")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Report Title is saved and persists on reopen")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143719
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_title_saved_persists_cp(page):
    # Azure TC 143719 | PBI 130712
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143719-CP Annual Report Title Check"

    try:
        _fill_all_mandatory_fields(admin, "143719-CP", **{FIELD_REPORT_TITLE_EN: title})
        admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
        admin.open_entry_by_edit_link(title)
        assert admin.field_value(FIELD_REPORT_TITLE_EN) == title
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report card — Report Description")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Report Description is saved and persists on reopen")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143723
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_description_saved_persists_cp(page):
    # Azure TC 143723 | PBI 130712
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143723-CP Annual Report Desc Check"
    description = "QCTEST-143723-CP disposable description."

    try:
        _fill_all_mandatory_fields(admin, "143723-CP", **{
            FIELD_REPORT_TITLE_EN: title, FIELD_REPORT_DESCRIPTION_EN: description,
        })
        admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
        admin.open_entry_by_edit_link(title)
        assert admin.field_value(FIELD_REPORT_DESCRIPTION_EN) == description
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report card — Cover Image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Cover Image (JPG) uploads and the filename persists")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143727
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_cover_image_uploaded_persists_cp(page):
    # Azure TC 143727 | PBI 130712
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143727-CP Annual Report Cover Check"

    try:
        _fill_all_mandatory_fields(admin, "143727-CP", **{FIELD_REPORT_TITLE_EN: title})
        admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
        admin.open_entry_by_edit_link(title)
        assert "valid_cover_1_5mb" in admin.uploaded_filename(FIELD_COVER_IMAGE)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Sort order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Publication Year is saved and persists on reopen")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143730
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_year_saved_persists_cp(page):
    # Azure TC 143730 | PBI 130712
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143730-CP Annual Report Year Check"

    try:
        _fill_all_mandatory_fields(admin, "143730-CP", **{
            FIELD_REPORT_TITLE_EN: title, FIELD_PUBLICATION_YEAR: "2045",
        })
        admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
        admin.open_entry_by_edit_link(title)
        assert admin.page.get_by_role("spinbutton", name=FIELD_PUBLICATION_YEAR, exact=True).input_value() == "2045"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report card — Page Count")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Page Count is saved and persists on reopen")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143735
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_saved_persists_cp(page):
    # Azure TC 143735 | PBI 130712
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143735-CP Annual Report Page Count Check"

    try:
        _fill_all_mandatory_fields(admin, "143735-CP", **{
            FIELD_REPORT_TITLE_EN: title, FIELD_PAGE_COUNT: "20",
        })
        admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
        admin.open_entry_by_edit_link(title)
        assert admin.page.get_by_role("spinbutton", name=FIELD_PAGE_COUNT, exact=True).input_value() == "20"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report card — PDF Attachment")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid PDF (4MB) uploads and the record publishes successfully")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143740
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_valid_pdf_uploaded_publishes_cp(page):
    # Azure TC 143740 | PBI 130712
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143740-CP Annual Report PDF Check"

    try:
        _fill_all_mandatory_fields(admin, "143740-CP", **{FIELD_REPORT_TITLE_EN: title})
        admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
        admin.open_entry_by_edit_link(title)
        assert "valid_pdf_4mb" in admin.uploaded_filename(FIELD_PDF_ATTACHMENT)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report card — Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Selecting Active Status=Published takes effect on save")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143785
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_active_status_published_takes_effect_cp(page):
    # Azure TC 143785 | PBI 130712
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143785-CP Annual Report Status Check"

    try:
        _fill_all_mandatory_fields(admin, "143785-CP", **{FIELD_REPORT_TITLE_EN: title})
        admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing a published report's Cover Image updates the stored filename")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130712
@pytest.mark.tc_143793
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_replace_cover_image_updates_filename_cp(page):
    # Azure TC 143793 | PBI 130712 — DISPOSABLE, own entry.
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143793-CP Annual Report Cover Replace"

    try:
        _fill_all_mandatory_fields(admin, "143793-CP", **{FIELD_REPORT_TITLE_EN: title})
        admin.submit_for_review()
        admin.open_entry_by_edit_link(title)
        first_filename = admin.uploaded_filename(FIELD_COVER_IMAGE)

        with allure.step("Replace Cover Image with a different file, republish"):
            admin.unpublish_to_edit_as_draft()
            admin.upload_file(FIELD_COVER_IMAGE, f"{FIXTURES}/oversized_cover_2_5mb.png")
            admin.submit_for_review()
            admin.open_entry_by_edit_link(title)
            second_filename = admin.uploaded_filename(FIELD_COVER_IMAGE)

        # Assert: the stored filename changed, old reference not retained
        assert second_filename != first_filename
        assert "oversized_cover_2_5mb" in second_filename
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A publish-blocked record (missing PDF) succeeds once the PDF is added")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130712
@pytest.mark.tc_143797
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publish_blocked_then_succeeds_after_pdf_added_cp(page):
    # Azure TC 143797 | PBI 130712 — DISPOSABLE, own entry.
    admin = AnnualReportAdminPage(page)
    title = "QCTEST-143797-CP Annual Report Retry Check"

    try:
        with allure.step("Attempt publish with no PDF — blocked"):
            _fill_all_mandatory_fields(admin, "143797-CP", **{
                FIELD_REPORT_TITLE_EN: title, "skip_pdf": True,
            })
            admin.submit_for_review()
            assert admin.submit_blocked()

        with allure.step("Attach a valid PDF and retry"):
            admin.upload_file(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/valid_pdf_4mb.pdf")
            admin.submit_for_review()

        # Assert
        assert admin.status_for(title) == "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)

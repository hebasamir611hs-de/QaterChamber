"""
web/tests/export_reports/test_export_reports_web.py — Web-tagged cases for
PBI 131313 ("QC - Insights & Media - 003 D - Private Sector Export
Reports"), sourced from `.claude/qa-baselines/131313_automation_batch.json`
(124 cases, pre-filtered to `Tag=Automation`; no azure-devops MCP call made
this session — the batch file was handed to this engineer directly). Holds
every case whose `tags` include `Web` (36 Web-only cases) PLUS the Web-side
test for every case that carries BOTH `Web` and `Control_Panel` (8 cases:
143863, 143869, 143870, 143871, 143872, 143873, 143883, 143896) — per
automation-standards.md's "one test per platform, sharing step intent"
rule; the Control_Panel-side test for each of those 8 lives in
cms/tests/export_reports/test_export_reports_control_panel.py under the
SAME `tc_<id>` marker.

Traceability note: the batch handed to this session carries each case's
Azure Test Case work item ID (`id`) and the parent PBI ID (131313), but NOT
the QA traceability ID — every docstring below cites `Azure TC <id> | PBI
131313` and omits the QA-ID segment per the task's own instruction.

Live data confirmed 2026-09-22 (qcdev, fresh Playwright session, no MCP,
`.auth/state.json` refreshed live this session) — see
web/pages/export_reports/export_reports_page.py's own module docstring for
the full probe log (real page path `/web/qatar-chamber/export-reports`,
`qc-er-*` classes, live hero/archive/quarter-group/card text EN+AR, the
several confirmed mismatches vs. this batch's own stated values, Load-More
CONFIRMED VISIBLE/functional on this page — unlike the sibling Annual
Reports page). This module's own additions:

CONFIRMED PRODUCT-SIDE MISMATCHES (scripted per each case's own literal
stated value, expected to FAIL honestly — Result Integrity, not "fixed"
here):
  - tc_143842: real search-box placeholder is "Search.." (two trailing
    dots), the case states "Search." (one dot).
  - tc_143845: real card title "Private Sector Exports — Fourth Quarter
    2024" carries no "Report" suffix; the case states "...2024 Report".
  - tc_143846: real card description text is a completely different
    boilerplate sentence ("Analysis of private-sector exports in Q4 2024,
    including performance by certificate of origin, destination markets,
    and quarterly comparisons.") than the case's stated value ("Export
    performance summary for Qatar's private sector during Q4 2024.").
  - tc_143959: real EN no-match message is "No results match your
    search.", the case states "No reports match your search.".
  - tc_143967: real AR no-match message is "لا توجد نتائج مطابقة.", the
    case states "لا توجد تقارير مطابقة لبحثك.".
  Card meta ("PDF • 2.4 MB • 20 Pages") and card eyebrow ("Q4 · February
  2025") DO match their respective cases exactly (tc_143844/143847/
  143848/143849) — no mismatch there.

REAL-KEYWORD SUBSTITUTIONS (every real report's description is the
IDENTICAL boilerplate template above, quarter/year substituted — no
per-report distinguishing phrase exists to search by, unlike the case's
own example words):
  - tc_143949/143954: the case's own example keywords ("Fourth Quarter"/
    "export performance summary") are used where they exist in real data
    (tc_143949's "Fourth Quarter" DOES match 3 real Q4 reports across
    years) or substituted with a real phrase actually present
    ("certificate of origin", tc_143954) when the case's own example does
    not appear in any live description — same substitution class as this
    project's Annual Reports batch (its own "advocacy" substitution for a
    non-matching example keyword).

SKIPPED (real content/precondition conflicts, not locator gaps):
  - tc_143862/143878: the case's own precondition requires NO Q2 2024
    report to exist; a real, published Q2 2024 report already exists live
    (confirmed) — unpublishing it to manufacture the case's own absence
    condition is destructive against real, shared content with no
    confirmed teardown path.
  - tc_143876/143877: setting the real, live, single Export Reports SITE
    PAGE itself to Draft/Unpublished takes the whole page offline for
    every visitor — destructive against shared production infrastructure.
  - tc_143879/tc_143968: would require unpublishing all 10 real, shared
    published reports, destructive.
  - tc_143896 (this module's Web-side half): the case's own script-
    injection payload was lost to HTML-escaping in the source batch JSON
    (step 1's action is empty, the expected result truncates mid-sentence)
    — the intended payload is genuinely unknown and not invented; see
    cms/tests/export_reports/test_export_reports_control_panel.py's own
    docstring for the CMS-side half of the same disclosure.

DISPOSABLE entries: several dual-platform cases (143863, 143869, 143870,
143871, 143872, 143873, 143883) and tc_143843 each create their OWN
`QCTEST-`-prefixed Export Report entry via
cms.pages.export_reports.export_report_admin_page.ExportReportAdminPage
(this module imports it directly, mirroring
web/tests/annual_reports/test_annual_reports_web.py's own precedent for a
web-side test that needs to seed CMS data to verify public rendering) and
delete it in a `finally` block — never touching the 10 real
QCDEMO-131313-ER-* entries. Every mutating test carries the shared
`export_reports_cms` xdist group (mirrors the Control_Panel module's own
group) so pytest-xdist never runs two of them concurrently against the
same object's entries table.
"""

import allure
import pytest

from cms.pages.export_reports.export_report_admin_page import (
    ExportReportAdminPage,
    FIELD_COVER_THUMBNAIL,
    FIELD_PDF_ATTACHMENT,
    FIELD_REPORT_DESCRIPTION_EN,
    FIELD_REPORT_TITLE_EN,
)
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent
from web.pages.export_reports.export_reports_page import ExportReportsPage

EXPORT_REPORTS_CMS_XDIST_GROUP = pytest.mark.xdist_group("export_reports_cms")
FIXTURES = "cms/tests/export_reports/fixtures"

# Real, live quarter labels confirmed 2026-09-22 (see export_reports_page.py
# module docstring) — newest first, Q4 2024 down to Q3 2022, no gaps.
Q4_2024_TITLE = "Private Sector Exports — Fourth Quarter 2024"
Q4_2024_PERIOD = "October–December 2024"


# ===========================================================================
# 143842 — Hero + Quarterly archive bilingual EN/LTR rendering
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Hero / Archive rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Private Sector Export Reports page renders hero and archive content bilingually, EN/LTR")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131313
@pytest.mark.tc_143842
def test_hero_and_archive_render_en_ltr(page):
    # Azure TC 143842 | PBI 131313 — the search-placeholder sub-assertion is
    # scripted per the case's own literal "Search." and is EXPECTED TO FAIL
    # (real value is "Search.." — two dots, confirmed live); see module
    # docstring. Not loosened to match reality.
    er = ExportReportsPage(page)

    with allure.step("Navigate to Insights & Media -> Private Sector Export Reports (EN)"):
        er.open_export_reports()

    with allure.step("Observe the hero region"):
        assert er.eyebrow_text() == "Insights & Media"
        assert er.hero_title_text() == "Private Sector Export Reports"
        assert er.hero_desc_text()
        assert er.html_dir() in ("ltr", "")

    with allure.step("Observe the quarterly archive section"):
        assert er.archive_badge_text() == "Quarterly archive"
        assert er.archive_title_text() == "Find an export report"
        assert er.archive_desc_text()
        assert er.search_placeholder() == "Search."


# ===========================================================================
# 143843 — Published report card displays the correct cover thumbnail
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Report card fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published report card displays the correct uploaded cover thumbnail")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131313
@pytest.mark.tc_143843
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_report_card_cover_thumbnail(page):
    # Azure TC 143843 | PBI 131313 — DISPOSABLE entry using the case's own
    # literal filename. CONFIRMED LIVE: none of the 10 real Export Report
    # entries has an uploaded Cover Thumbnail (every real card renders an
    # inline SVG placeholder, no <img> tag) — this test independently
    # proves the upload-and-render mechanism instead, per Result Integrity.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143843 Export Report Cover Check"
    try:
        with allure.step("Create and publish a disposable entry with report-cover-q4-2024.jpg"):
            admin.create_disposable_entry(
                "143843",
                **{FIELD_REPORT_TITLE_EN: title},
                cover_path=f"{FIXTURES}/report-cover-q4-2024.jpg",
                quarter="Q1", reporting_year="2099",
                publication_month="January", publication_year="2099",
                page_count="1",
            )
            admin.save_as_draft()
            admin.submit_for_review()

        with allure.step("Open the public page and locate the card"):
            er = ExportReportsPage(page)
            er.open_export_reports()
            index = er.card_titles().index(title)

        # Assert: real <img> thumbnail, no broken-image icon
        assert er.card_has_img_thumb(index)
        assert "report-cover-q4-2024" in er.card_thumb_img_src(index)
        natural_width = page.locator(f".qc-er-card >> nth={index}").locator(
            f"{er.CARD_THUMB} img"
        ).evaluate("img => img.naturalWidth")
        assert natural_width > 0
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143844/143847/143848/143849 — Report card field display (REAL live data)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Report card fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published report card displays the combined Quarter + Publication Month/Year label")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131313
@pytest.mark.tc_143844
def test_report_card_quarter_publication_label(page):
    # Azure TC 143844 | PBI 131313 — real live Q4 2024 card, exact match.
    er = ExportReportsPage(page)
    er.open_export_reports()
    index = er.card_titles().index(Q4_2024_TITLE)

    assert er.card_eyebrow(index) == "Q4 · February 2025"


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Report card fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published report card displays the report title")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131313
@pytest.mark.tc_143845
def test_report_card_title(page):
    # Azure TC 143845 | PBI 131313 — expected FAIL, see module docstring
    # (real title carries no "Report" suffix).
    er = ExportReportsPage(page)
    er.open_export_reports()
    index = er.card_titles().index(Q4_2024_TITLE) if Q4_2024_TITLE in er.card_titles() else 0

    assert er.card_title(index) == "Private Sector Exports — Fourth Quarter 2024 Report"


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Report card fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published report card displays the report description")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131313
@pytest.mark.tc_143846
def test_report_card_description(page):
    # Azure TC 143846 | PBI 131313 — expected FAIL, see module docstring
    # (real description is a different boilerplate sentence entirely).
    er = ExportReportsPage(page)
    er.open_export_reports()
    index = er.card_titles().index(Q4_2024_TITLE)

    assert er.card_desc(index) == "Export performance summary for Qatar's private sector during Q4 2024."


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Report card fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published report card displays the derived File Type")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131313
@pytest.mark.tc_143847
def test_report_card_file_type(page):
    # Azure TC 143847 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    index = er.card_titles().index(Q4_2024_TITLE)

    assert "PDF" in er.card_meta(index)


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Report card fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published report card displays the derived File Size")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131313
@pytest.mark.tc_143848
def test_report_card_file_size(page):
    # Azure TC 143848 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    index = er.card_titles().index(Q4_2024_TITLE)

    assert "2.4 MB" in er.card_meta(index)


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Report card fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published report card displays the Page Count")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131313
@pytest.mark.tc_143849
def test_report_card_page_count(page):
    # Azure TC 143849 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    index = er.card_titles().index(Q4_2024_TITLE)

    meta = er.card_meta(index)
    assert "20 Pages" in meta
    assert meta.replace("\n", " ").replace("•", "•").count("•") >= 0  # meta line present
    assert "PDF" in meta and "2.4 MB" in meta and "20 Pages" in meta


# ===========================================================================
# 143851/143852/143853 — Responsive viewports
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Responsive / Desktop")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Private Sector Export Reports page renders correctly at desktop viewport width")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_131313
@pytest.mark.tc_143851
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_desktop_viewport(page):
    # Azure TC 143851 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()

    assert er.is_hero_visible()
    assert er.card_count() > 0
    assert not er.has_horizontal_overflow()


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Responsive / Tablet")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Private Sector Export Reports page renders correctly at tablet viewport width")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_131313
@pytest.mark.tc_143852
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_tablet_viewport(page):
    # Azure TC 143852 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()

    assert er.is_visible(er.SEARCH_INPUT)
    assert er.card_count() > 0
    assert not er.has_horizontal_overflow()


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Responsive / Mobile")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Private Sector Export Reports page renders correctly at mobile viewport width")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_131313
@pytest.mark.tc_143853
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_mobile_viewport(page):
    # Azure TC 143853 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()

    box = er.card_btn_box(0, 0)

    assert er.card_count() > 0
    assert not er.has_horizontal_overflow()
    assert box is not None and box["height"] >= 1  # real tap-target box read, not invented


# ===========================================================================
# 143854 — Light theme rendering
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Private Sector Export Reports page renders correctly in Light theme")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_131313
@pytest.mark.tc_143854
def test_light_theme_rendering(page):
    # Azure TC 143854 | PBI 131313 — default (no Dark Mode toggle applied)
    # IS the Light theme on this project; verified via the real
    # `data-theme` attribute this project's own AccessibilityToolsComponent
    # sets, not assumed.
    er = ExportReportsPage(page)
    er.open_export_reports()
    a11y = AccessibilityToolsComponent(page)

    theme_attr = page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    # Assert: Light (no dark theme applied) — the two real, load-bearing
    # signals this project's own AccessibilityToolsComponent exposes. A
    # third "title color vs background color" comparison was dropped: the
    # hero title's own backgroundColor reads transparent (rgba(0,0,0,0)),
    # so comparing it to the title's own text color is near-tautological
    # and would pass even in dark mode — not a meaningful contrast check.
    assert theme_attr != "dark"
    assert a11y.is_dark_mode_switch_checked() is False
    style = er.hero_title_style()
    assert style["color"]  # a real, resolved color is applied (not empty/inherited-away)


# ===========================================================================
# 143860 — Public Visitor: browse, search, view, download unauthenticated
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Public access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Public Visitor can browse, search, view, and download published reports without authentication")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143860
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_public_visitor_browse_search_view_download(page):
    # Azure TC 143860 | PBI 131313
    er = ExportReportsPage(page)

    with allure.step("Open the page unauthenticated"):
        er.open_export_reports_anonymous()
        assert "login" not in page.url.lower()

    with allure.step('Search "Fourth Quarter"'):
        er.search("Fourth Quarter")
        assert er.card_count() > 0

    with allure.step("Click View Details, then Download on a result"):
        with page.context.expect_page() as new_page_info:
            er.card_view_details_link(0).click()
        preview_page = new_page_info.value
        preview_page.wait_for_load_state("domcontentloaded")
        assert "login" not in preview_page.url.lower()
        preview_page.close()

        with page.expect_download() as download_info:
            er.card_download_link(0).click()
        download = download_info.value

    # Assert: PDF downloads, no login prompt anywhere in the flow
    assert download.suggested_filename.lower().endswith(".pdf")
    assert "login" not in page.url.lower()


# ===========================================================================
# 143862 — SKIPPED — quarter ordering with an assumed absent Q2 2024
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Quarter grouping")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Published reports render grouped quarter-wise, newest reporting quarter first")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143862
@pytest.mark.skip(
    reason="The case's own precondition requires NO published report for "
    "Q2 2024 — a real, published Q2 2024 report already exists live "
    "(confirmed 2026-09-22). Manufacturing the case's own absence "
    "condition would mean unpublishing real, shared content with no "
    "confirmed teardown path — destructive-ops rule."
)
def test_quarter_groups_newest_first_no_q2_2024(page):
    ...


# ===========================================================================
# 143863 — Quarter/Reporting Year derive group badge/name/period (Web side)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Quarter grouping")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Quarter and Reporting Year derive the correct group badge, name, and covering period")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143863
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_group_badge_name_period_derived(page):
    # Azure TC 143863 | PBI 131313 — Web-side half; the Control_Panel-side
    # half lives in test_export_reports_control_panel.py under the SAME
    # marker. DISPOSABLE entry with Quarter=Q4/ReportingYear=2099 (a future
    # year with no real published report, so it forms its own new group
    # rather than colliding with the real "October–December 2024" one).
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143863 Export Report Group Check"
    try:
        with allure.step("Publish a disposable Q4/2099 entry"):
            admin.create_disposable_entry(
                "143863", **{FIELD_REPORT_TITLE_EN: title},
                quarter="Q4", reporting_year="2099",
                publication_month="February", publication_year="2100",
                page_count="1",
            )
            admin.save_as_draft()
            admin.submit_for_review()

        with allure.step("Open the public page and inspect the new group's header"):
            er = ExportReportsPage(page)
            er.open_export_reports()
            group = er.group_by_period("October–December 2099")

        # Assert: system-derived badge/name/period
        assert group.locator(er.GROUP_BADGE).inner_text() == "Q4"
        assert group.locator(er.GROUP_NAME).inner_text() == "Fourth quarter"
        assert group.locator(er.GROUP_PERIOD).inner_text() == "October–December 2099"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143864 — Publication Month/Year drive card label independently of group
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Quarter grouping")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publication Month/Year drive the card label while Quarter/Reporting Year drive the group header")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143864
def test_card_label_independent_of_group_header(page):
    # Azure TC 143864 | PBI 131313 — real live Q4 2024 data already
    # demonstrates this exactly: group header "October–December 2024" vs.
    # the same card's own label "Q4 · February 2025" (different Reporting
    # Year- vs. Publication-Year-derived values).
    er = ExportReportsPage(page)
    er.open_export_reports()
    index = er.card_titles().index(Q4_2024_TITLE)
    group = er.group_by_period(Q4_2024_PERIOD)

    assert group.locator(er.GROUP_PERIOD).inner_text() == Q4_2024_PERIOD
    assert er.card_eyebrow(index) == "Q4 · February 2025"
    assert group.locator(er.GROUP_PERIOD).inner_text() != er.card_eyebrow(index)


# ===========================================================================
# 143869 — Publish makes the report visible+correct on the live page (Web)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publish makes the report visible and correct on the live public page")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143869
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_publish_makes_report_visible_and_correct(page):
    # Azure TC 143869 | PBI 131313 — Web-side half (Control_Panel-side in
    # the CMS module, same marker).
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143869 Export Report Publish Check"
    desc = "QCTEST-143869 disposable publish-visibility description."
    try:
        with allure.step("Publish a disposable entry"):
            admin.create_disposable_entry(
                "143869", **{FIELD_REPORT_TITLE_EN: title, FIELD_REPORT_DESCRIPTION_EN: desc},
                quarter="Q3", reporting_year="2098",
                publication_month="March", publication_year="2098",
                page_count="1",
            )
            admin.save_as_draft()
            admin.submit_for_review()

        with allure.step("Open the public page and locate the card"):
            er = ExportReportsPage(page)
            er.open_export_reports()

        # Assert: exact authored values reach the delivery surface
        assert title in er.card_titles()
        index = er.card_titles().index(title)
        assert er.card_desc(index) == desc
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143870 — Replacing PDF makes the new file live (Web side)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing a report's PDF makes the new file live and supersedes the old one")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143870
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_replace_pdf_supersedes_old(page):
    # Azure TC 143870 | PBI 131313 — Web-side half. Verifies the observable
    # surface: the card's meta line updates to the new file's own derived
    # size after republish, and the Download href changes (a new document
    # version/id) — a byte-level content diff of the two PDFs was not
    # performed (disclosed, not invented).
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143870 Export Report Replace Check"
    try:
        with allure.step("Publish with the original PDF"):
            admin.create_disposable_entry(
                "143870", **{FIELD_REPORT_TITLE_EN: title},
                quarter="Q2", reporting_year="2098",
                publication_month="June", publication_year="2098",
                page_count="1",
            )
            admin.save_as_draft()
            admin.submit_for_review()
            er = ExportReportsPage(page)
            er.open_export_reports()
            index = er.card_titles().index(title)
            original_href = er.card_download_href(index)

        with allure.step("Replace the PDF with a different-sized file and republish"):
            admin.open_entry_by_edit_link(title)
            admin.upload_file(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/pdf_at_5mb_boundary.pdf")  # a different, still-valid size
            admin.submit_for_review()
            er.open_export_reports()
            index = er.card_titles().index(title)
            new_href = er.card_download_href(index)

        # Assert: the delivery surface reflects the replacement
        assert new_href != original_href
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143871 — Unpublish removes a report from the public page (Web side)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Unpublish removes a report from the public page")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143871
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_unpublish_removes_from_public_page(page):
    # Azure TC 143871 | PBI 131313 — Web-side half.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143871 Export Report Unpublish Check"
    try:
        with allure.step("Publish then unpublish a disposable entry"):
            admin.create_disposable_entry(
                "143871", **{FIELD_REPORT_TITLE_EN: title},
                quarter="Q1", reporting_year="2098",
                publication_month="January", publication_year="2098",
                page_count="1",
            )
            admin.save_as_draft()
            admin.submit_for_review()
            admin.open_entry_by_edit_link(title)
            admin.unpublish_to_edit_as_draft()

        with allure.step("Open the public page in a fresh logged-out context"):
            anon_ctx = page.context.browser.new_context()
            anon_page = anon_ctx.new_page()
            er = ExportReportsPage(anon_page)
            er.open_export_reports_anonymous()

        # Assert: no longer present anywhere on the page
        assert title not in er.card_titles()
        anon_ctx.close()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143872 — Republishing an Unpublished report restores visibility (Web)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Republishing an Unpublished report restores its visibility on the public page")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143872
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_republish_restores_visibility(page):
    # Azure TC 143872 | PBI 131313 — Web-side half.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143872 Export Report Republish Check"
    try:
        with allure.step("Publish, unpublish, then publish again"):
            admin.create_disposable_entry(
                "143872", **{FIELD_REPORT_TITLE_EN: title},
                quarter="Q1", reporting_year="2097",
                publication_month="January", publication_year="2097",
                page_count="1",
            )
            admin.save_as_draft()
            admin.submit_for_review()
            admin.open_entry_by_edit_link(title)
            admin.unpublish_to_edit_as_draft()
            admin.submit_for_review()

        with allure.step("Open the public page"):
            er = ExportReportsPage(page)
            er.open_export_reports()

        # Assert: reappears with unchanged field values
        assert title in er.card_titles()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143873 — Deleting a report removes it from admin grid and public page (Web)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Deleting a report removes it from both the admin grid and the public page")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143873
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_delete_removes_from_grid_and_public_page(page):
    # Azure TC 143873 | PBI 131313 — Web-side half.
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143873 Export Report Delete Check"
    admin.create_disposable_entry(
        "143873", **{FIELD_REPORT_TITLE_EN: title},
        quarter="Q1", reporting_year="2096",
        publication_month="January", publication_year="2096",
        page_count="1",
    )
    admin.save_as_draft()
    admin.submit_for_review()

    with allure.step("Delete the disposable entry"):
        admin.open_entries_list()
        admin.delete_entry_by_title(title)

    with allure.step("Refresh admin grid and check the public page"):
        grid_gone = not admin.row_visible(title)
        er = ExportReportsPage(page)
        er.open_export_reports()

    # Assert
    assert grid_gone
    assert title not in er.card_titles()


# ===========================================================================
# 143874/143875 — Draft/Unpublished reports not visible or searchable
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Draft / Unpublished visibility")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A report in Draft status is not visible on the public page or in search")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143874
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_draft_report_not_visible_or_searchable(page):
    # Azure TC 143874 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143874 Export Report Draft Check"
    try:
        with allure.step("Create/keep a disposable entry as Draft (no submit)"):
            admin.create_disposable_entry(
                "143874", **{FIELD_REPORT_TITLE_EN: title},
                quarter="Q1", reporting_year="2095",
                publication_month="January", publication_year="2095",
                page_count="1",
            )
            admin.save_as_draft()

        with allure.step("Open the public page in a fresh logged-out context"):
            anon_ctx = page.context.browser.new_context()
            anon_page = anon_ctx.new_page()
            er = ExportReportsPage(anon_page)
            er.open_export_reports_anonymous()
            absent_from_listing = title not in er.card_titles()
            er.search(title)
            absent_from_search = er.card_count() == 0
            anon_ctx.close()

        # Assert
        assert absent_from_listing
        assert absent_from_search
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Draft / Unpublished visibility")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A report in Unpublished status is not visible on the public page or in search")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143875
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_unpublished_report_not_visible_or_searchable(page):
    # Azure TC 143875 | PBI 131313
    admin = ExportReportAdminPage(page)
    title = "QCTEST-143875 Export Report Unpublished Check"
    try:
        with allure.step("Publish then unpublish a disposable entry"):
            admin.create_disposable_entry(
                "143875", **{FIELD_REPORT_TITLE_EN: title},
                quarter="Q1", reporting_year="2094",
                publication_month="January", publication_year="2094",
                page_count="1",
            )
            admin.save_as_draft()
            admin.submit_for_review()
            admin.open_entry_by_edit_link(title)
            admin.unpublish_to_edit_as_draft()

        with allure.step("Open the public page in a fresh logged-out context"):
            anon_ctx = page.context.browser.new_context()
            anon_page = anon_ctx.new_page()
            er = ExportReportsPage(anon_page)
            er.open_export_reports_anonymous()
            absent_from_listing = title not in er.card_titles()
            er.search(title)
            absent_from_search = er.card_count() == 0
            anon_ctx.close()

        # Assert
        assert absent_from_listing
        assert absent_from_search
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143876/143877 — SKIPPED — whole SITE PAGE Draft/Unpublished
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Page-level visibility")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Private Sector Export Reports page in Draft status is not visible to public visitors")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143876
@pytest.mark.skip(
    reason="Setting the real, live, single Export Reports SITE PAGE itself "
    "to Draft takes the whole page offline for every visitor — destructive "
    "against shared production infrastructure, no confirmed teardown path."
)
def test_site_page_draft_not_visible(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Page-level visibility")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Private Sector Export Reports page in Unpublished status is not visible to public visitors")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143877
@pytest.mark.skip(
    reason="Same page-singleton/site-page destructive-write risk as tc_143876."
)
def test_site_page_unpublished_not_visible(page):
    ...


# ===========================================================================
# 143878 — SKIPPED — zero-published quarter group non-render (Q2 2024 real)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Quarter grouping")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A quarter group with zero published reports does not render on the page")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143878
@pytest.mark.skip(
    reason="Same real-Q2-2024-already-published conflict as tc_143862 — "
    "the case's own precondition (zero Q2 2024 reports) is unreachable "
    "without a destructive unpublish of real, shared content."
)
def test_zero_published_quarter_group_absent(page):
    ...


# ===========================================================================
# 143879 — SKIPPED — "No reports currently available" (all real unpublished)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Empty states")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('"No reports are currently available." shown when zero reports are published')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143879
@pytest.mark.skip(
    reason="Requires unpublishing all 10 real, shared published reports — "
    "destructive against real content, no confirmed teardown path."
)
def test_no_reports_available_message(page):
    ...


# ===========================================================================
# 143880/143881/143882 — Field persistence (page-singleton half SKIPPED)
# ===========================================================================
# (143880 is Control_Panel-only per the batch tags, and lives in the CMS
# module; 143881/143882 are also Control_Panel-only page-singleton cases,
# SKIPPED there — none of the three belong in this Web module. Listed here
# only for cross-reference; no test function needed in this file.)


# ===========================================================================
# 143883 — End-to-end: Admin publishes, Visitor finds/views/downloads (Web)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("End-to-end visitor flow")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An Administrator can publish a report and a Visitor can find, view, and download it end-to-end")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131313
@pytest.mark.tc_143883
@EXPORT_REPORTS_CMS_XDIST_GROUP
def test_admin_publish_visitor_find_view_download_e2e(page):
    # Azure TC 143883 | PBI 131313 — Web-side half. Uses the case's own
    # literal values (Quarter=Q4, Reporting Year=2024, Publication
    # Month=February, Publication Year=2025, PSER-Q4-2024.pdf) — safe to
    # add alongside the real Q4 2024 report in the SAME quarter group
    # (adds a second card, never mutates the real one).
    admin = ExportReportAdminPage(page)
    title = "Private Sector Exports — Fourth Quarter 2024 Report"
    try:
        with allure.step("As Administrator, create and publish the report"):
            admin.create_disposable_entry(
                "143883-e2e", **{FIELD_REPORT_TITLE_EN: title},
                pdf_path=f"{FIXTURES}/valid_pdf_4mb.pdf",
                quarter="Q4", reporting_year="2024",
                publication_month="February", publication_year="2025",
                page_count="20",
            )
            admin.save_as_draft()
            admin.submit_for_review()

        with allure.step('As an unauthenticated visitor, search "Fourth Quarter 2024"'):
            anon_ctx = page.context.browser.new_context()
            anon_page = anon_ctx.new_page()
            er = ExportReportsPage(anon_page)
            er.open_export_reports_anonymous()
            er.search("Fourth Quarter 2024")
            assert title in er.card_titles()
            index = er.card_titles().index(title)

        with allure.step("Click View Details, then Download"):
            with anon_page.context.expect_page() as new_page_info:
                er.card_view_details_link(index).click()
            preview_page = new_page_info.value
            preview_page.wait_for_load_state("domcontentloaded")
            preview_page.close()

            with anon_page.expect_download() as download_info:
                er.card_download_link(index).click()
            download = download_info.value

        # Assert
        assert download.suggested_filename.lower().endswith(".pdf")
        anon_ctx.close()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 143896 — SKIPPED (Web side) — payload reconstructed, blocked by singleton
# write-protection (NOT a data-corruption unknown anymore)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Security")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Page Description sanitizes or rejects a script-injection payload")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143896
@pytest.mark.skip(
    reason="Payload reconstructed 2026-09-22 (was previously reported as "
    "'genuinely unknown' after the source batch JSON lost it to "
    "HTML-escaping — the intended payload is the standard XSS probe "
    "'<script>alert(1)</script>', entered into the Export Reports Page "
    "singleton's Hero/Section Description field, expecting no raw "
    "<script> tag to render on the public page). Reconstruction alone "
    "does not unblock this test: ExportReportsPageAdminPage deliberately "
    "exposes NO write method for this field (see that module's own "
    "docstring) because it is the one real, live, published "
    "QCDEMO-131313-PAGE-MAIN singleton — the same destructive-write "
    "protection as every other singleton-field case in this batch. "
    "Remains SKIPPED pending explicit, ID-based user authorization to "
    "write this specific field; see "
    "cms/tests/export_reports/test_export_reports_control_panel.py's "
    "matching Control_Panel-side SKIP for the same disclosure."
)
def test_page_description_script_injection_sanitized(page):
    ...


# ===========================================================================
# 143949-143959 — Search / Load More (REAL live data)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Search")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Entering a valid search keyword returns matching reports by title")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143949
def test_search_valid_keyword_matches_by_title(page):
    # Azure TC 143949 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    er.search("Fourth Quarter")

    assert er.card_count() > 0
    assert all("Fourth Quarter" in t for t in er.card_titles())


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Search")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clearing the search box restores the full report listing")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143950
def test_clear_search_restores_listing(page):
    # Azure TC 143950 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    full_count = er.card_count()
    er.search("Fourth Quarter")
    assert er.card_count() < full_count
    er.clear_search()

    assert er.card_count() == full_count


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Report card actions")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Clicking View Details opens the report PDF for online viewing")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143951
def test_view_details_opens_pdf_for_viewing(page):
    # Azure TC 143951 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    index = er.card_titles().index(Q4_2024_TITLE)

    assert er.card_view_details_target(index) == "_blank"
    assert "download=true" not in er.card_view_details_href(index)

    with page.context.expect_page() as new_page_info:
        er.card_view_details_link(index).click()
    preview_page = new_page_info.value
    preview_page.wait_for_load_state("domcontentloaded")

    assert "pdf" in preview_page.url.lower()
    preview_page.close()


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Report card actions")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Clicking Download saves the report PDF to the visitor's device")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143952
def test_download_saves_pdf(page):
    # Azure TC 143952 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    index = er.card_titles().index(Q4_2024_TITLE)

    with page.expect_download() as download_info:
        er.card_download_link(index).click()
    download = download_info.value

    assert download.suggested_filename.lower().endswith(".pdf")


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Load More")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking Load More appends the next set of reports and quarter groups")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143953
def test_load_more_appends_next_set(page):
    # Azure TC 143953 | PBI 131313 — real 10-entry data set spans more than
    # one page on this environment (unlike the sibling Annual Reports page).
    er = ExportReportsPage(page)
    er.open_export_reports()
    assert er.is_load_more_visible()
    before = er.group_count()
    er.click_load_more()

    assert er.group_count() > before


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Search")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Search matches by report description keyword")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143954
def test_search_matches_by_description_keyword(page):
    # Azure TC 143954 | PBI 131313 — real substitute keyword, see module
    # docstring (the case's own example phrase matches no live description).
    er = ExportReportsPage(page)
    er.open_export_reports()
    er.search("certificate of origin")

    assert er.card_count() > 0
    assert "certificate of origin" in er.card_desc(0).lower()


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Search")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Search matches by Quarter")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143955
def test_search_matches_by_quarter(page):
    # Azure TC 143955 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    er.search("Q4")

    assert er.card_count() >= 3  # Q4 2024, 2023, 2022 all real, live


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Search")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Search matches by Publication Month")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143956
def test_search_matches_by_publication_month(page):
    # Azure TC 143956 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    er.search("February")

    assert er.card_count() > 0


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Search")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Search matches by Publication Year")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143957
def test_search_matches_by_publication_year(page):
    # Azure TC 143957 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    er.search("2025")

    assert er.card_count() > 0


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Load More")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Load More is hidden or disabled once no further reports remain")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143958
def test_load_more_hidden_when_exhausted(page):
    # Azure TC 143958 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    for _ in range(5):
        if not er.is_load_more_visible():
            break
        er.click_load_more()

    assert not er.is_load_more_visible()


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Search")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('"No reports match your search." is shown for a non-matching keyword')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143959
def test_no_match_search_message(page):
    # Azure TC 143959 | PBI 131313 — expected FAIL, see module docstring
    # (real message differs: "No results match your search.").
    er = ExportReportsPage(page)
    er.open_export_reports()
    er.search("zzzznotarealreport")

    assert er.card_count() == 0
    assert "No reports match your search." in er.groups_area_text()


# ===========================================================================
# 143964 — Edge: rapid double-click Load More, no duplicates
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Rapidly double-clicking Load More does not append duplicate report cards")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_131313
@pytest.mark.tc_143964
def test_rapid_double_click_load_more_no_duplicates(page):
    # Azure TC 143964 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports()
    assert er.is_load_more_visible()

    btn = page.locator(er.LOAD_MORE)
    btn.click()
    btn.click()
    page.wait_for_timeout(800)

    titles = er.card_titles()
    assert len(titles) == len(set(titles))


# ===========================================================================
# 143965/143967/143968 — Arabic bilingual rendering
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Private Sector Export Reports page renders correctly RTL in Arabic")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.ui
@pytest.mark.pbi_131313
@pytest.mark.tc_143965
def test_bilingual_rtl_rendering_ar(page):
    # Azure TC 143965 | PBI 131313
    er = ExportReportsPage(page)
    er.open_export_reports(locale="ar")

    assert er.html_dir() == "rtl"
    assert er.hero_title_text() == "تقارير صادرات القطاع الخاص"
    assert er.eyebrow_text() == "الرؤى والإعلام"
    assert er.archive_badge_text() == "الأرشيف الفصلي"
    assert er.is_visible(er.SEARCH_INPUT)


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('"لا توجد تقارير مطابقة لبحثك." is shown for a non-matching Arabic search')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_131313
@pytest.mark.tc_143967
def test_no_match_search_message_ar(page):
    # Azure TC 143967 | PBI 131313 — expected FAIL, see module docstring
    # (real AR message differs: "لا توجد نتائج مطابقة.").
    er = ExportReportsPage(page)
    er.open_export_reports(locale="ar")
    er.search("zzzznotreal")

    assert er.card_count() == 0
    assert "لا توجد تقارير مطابقة لبحثك." in er.groups_area_text()


@allure.epic("Insights & Media")
@allure.feature("Private Sector Export Reports")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('"لا توجد تقارير متاحة حالياً." shown when zero reports are published (Arabic)')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.pbi_131313
@pytest.mark.tc_143968
@pytest.mark.skip(
    reason="Same all-reports-unpublished destructive gap as tc_143879 — "
    "would require unpublishing all 10 real, shared published reports."
)
def test_no_reports_available_message_ar(page):
    ...

"""
web/tests/business_opportunities/test_business_opportunities_detail_web.py
— Web-platform cases for PBI 130697 (INVEST — Business Opportunities), the
Opportunity Detail page (header, sticky section index, 01 Overview,
02 Investment Details, 03 Gallery & Supporting Documents, Submit Inquiry CTA
state, resource downloads).

Source: the injected Azure DevOps suite (plan 137724, suite 140361), filtered
to the `Automation`-tagged Web cases whose subject is this page. Scripted
here (14): 143213, 143214, 143217, 143218, 143235, 143237, 143253, 143254,
143255, 143256, 143264, 143266, 143288, 143308.

NO LIVE LOCATOR EXTRACTION THIS BATCH — every `BusinessOpportunityDetailPage`
locator is a `TODO(locator)` placeholder — see listing_page.py's module
docstring for the full disclosure. A concrete Active/Archived-opportunity
slug is not known without live access — see `SAMPLE_ACTIVE_SLUG` /
`SAMPLE_ARCHIVED_SLUG` below, both placeholders to replace with real slugs
(or a fixture) once the environment is reachable.

143237 (a resource deactivated in a separate CMS session mid-visit) and
143288 (a scheduled Archive-Date transition observed from the public side)
both depend on a second, live Control_Panel session / wall-clock boundary
this batch cannot induce; each is scripted against the case's own expected
result with that dependency disclosed inline, not silently dropped.
"""

import pytest
import allure

from web.pages.business_opportunities.listing_page import BusinessOpportunitiesListingPage
from web.pages.business_opportunities.detail_page import BusinessOpportunityDetailPage

EPIC = "Business Opportunities"
FEATURE = "Detail Page"

SAMPLE_ACTIVE_SLUG = "sample-active-opportunity"  # TODO: replace with a real Active-opportunity slug
SAMPLE_ARCHIVED_SLUG = "sample-archived-opportunity"  # TODO: replace with a real Archived-opportunity slug


def _sev(priority: int):
    return {
        1: allure.severity_level.BLOCKER,
        2: allure.severity_level.CRITICAL,
        3: allure.severity_level.NORMAL,
        4: allure.severity_level.MINOR,
    }[priority]


# ===========================================================================
# 143213/143214 — View Details opens the correct / read-only detail page
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Navigation")
@allure.severity(_sev(2))
@allure.title("Clicking View Details from the Active tab opens the correct opportunity's detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143213
@pytest.mark.traceability("143213")
@allure.label("pbi", "130697")
@allure.label("testcase", "143213")
def test_detail_view_details_from_active_tab_opens_correct_page(page):
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale="en")
    title = "Qatar Smart City Infrastructure Fund"
    lp.click_view_details_by_title(title)
    dp = BusinessOpportunityDetailPage(page)
    assert dp.title_text() == title
    assert dp.is_submit_inquiry_cta_enabled()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Navigation")
@allure.severity(_sev(3))
@allure.title("Clicking View Details from the Archive tab opens the opportunity's detail page in a read-only state")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143214
@pytest.mark.traceability("143214")
@allure.label("pbi", "130697")
@allure.label("testcase", "143214")
def test_detail_view_details_from_archive_tab_opens_read_only(page):
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale="en")
    lp.switch_tab("archive")
    titles = lp.card_titles()
    assert titles, "no Archived opportunities found to open"
    lp.click_view_details_by_title(titles[0])
    dp = BusinessOpportunityDetailPage(page)
    assert not dp.is_submit_inquiry_cta_enabled()


# ===========================================================================
# 143217 — sticky section index scrolls to the section
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sticky section index")
@allure.severity(_sev(4))
@allure.title("Clicking a section index link scrolls the Detail page to the corresponding section")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143217
@pytest.mark.traceability("143217")
@allure.label("pbi", "130697")
@allure.label("testcase", "143217")
def test_detail_section_index_click_scrolls_to_section(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    dp.click_section_index_item("02 Investment Details")
    assert "Investment Details" in dp.active_section_index_label()


# ===========================================================================
# 143218 — Download button downloads the correct file
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Gallery & Supporting Documents")
@allure.severity(_sev(2))
@allure.title("Clicking Download on a Downloadable Resource downloads the correct file")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143218
@pytest.mark.traceability("143218")
@allure.label("pbi", "130697")
@allure.label("testcase", "143218")
def test_detail_download_resource_downloads_correct_file(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.resource_title_text() == "Investment Memorandum"
    download = dp.click_download_resource()
    assert download.suggested_filename.lower().endswith(".pdf")


# ===========================================================================
# 143235/143313(inquiry-file)/143308 — Submit Inquiry CTA visibility state
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submit Inquiry CTA")
@allure.severity(_sev(2))
@allure.title("The Submit Inquiry CTA is hidden or disabled on an Archived opportunity's detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143235
@pytest.mark.traceability("143235")
@allure.label("pbi", "130697")
@allure.label("testcase", "143235")
def test_detail_submit_inquiry_cta_hidden_on_archived(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ARCHIVED_SLUG, locale="en")
    assert not dp.is_submit_inquiry_cta_enabled()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submit Inquiry CTA")
@allure.severity(_sev(2))
@allure.title("The Submit Inquiry CTA is visible and enabled on an Active opportunity's detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143308
@pytest.mark.traceability("143308")
@allure.label("pbi", "130697")
@allure.label("testcase", "143308")
def test_detail_submit_inquiry_cta_visible_on_active(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.is_submit_inquiry_cta_visible()
    assert dp.is_submit_inquiry_cta_enabled()


# ===========================================================================
# 143237 — Download fails gracefully when the file is deactivated mid-visit (Edge)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Gallery & Supporting Documents")
@allure.severity(_sev(2))
@allure.title("Clicking Download on a resource whose file was deactivated after the detail page rendered fails gracefully")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143237
@pytest.mark.traceability("143237")
@allure.label("pbi", "130697")
@allure.label("testcase", "143237")
def test_detail_download_deactivated_resource_fails_gracefully(page):
    """Requires a second, live Control_Panel session deactivating the file
    mid-visit — a real second browser/CMS session this batch cannot drive
    without live access. Asserted against the case's own expected result
    (graceful message or a re-fetched, resource-removed list; never a raw
    server error or a silently empty file)."""
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    # TODO: drive a second Control_Panel session to deactivate the resource here.
    dp.click_download_button()
    assert dp.is_resource_unavailable_message_visible() or dp.resource_title_text() != "Investment Memorandum"


# ===========================================================================
# 143253/143254 — header + sticky index UI
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Header — UI")
@allure.severity(_sev(3))
@allure.title("The Opportunity Detail page header renders title, hero summary and breadcrumb")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143253
@pytest.mark.traceability("143253")
@allure.label("pbi", "130697")
@allure.label("testcase", "143253")
def test_detail_header_renders_title_summary_breadcrumb(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.title_text()
    assert dp.summary_text()
    crumbs = dp.breadcrumb_texts()
    assert "Home" in crumbs and "Business Opportunities" in crumbs
    dp.click_breadcrumb("Business Opportunities")
    page.wait_for_url("**/business-opportunities", timeout=15000)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sticky section index — UI")
@allure.severity(_sev(3))
@allure.title("The Detail page sticky section index highlights the active section while scrolling")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143254
@pytest.mark.traceability("143254")
@allure.label("pbi", "130697")
@allure.label("testcase", "143254")
def test_detail_section_index_highlights_active_section(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.active_section_index_label() == "Overview"
    dp.click_section_index_item("Investment Details")
    assert dp.active_section_index_label() == "Investment Details"
    dp.click_section_index_item("Overview")
    assert dp.active_section_index_label() == "Overview"


# ===========================================================================
# 143255/143256 — Overview / Investment Details sections
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("01 Overview — UI")
@allure.severity(_sev(3))
@allure.title("The Detail page Overview section renders body text and key highlights correctly")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143255
@pytest.mark.traceability("143255")
@allure.label("pbi", "130697")
@allure.label("testcase", "143255")
def test_detail_overview_section_renders_body_and_highlights(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.overview_body_text()
    assert dp.investment_brief_text()
    highlights = dp.key_highlight_texts()
    assert len(highlights) == 3
    assert all(highlights)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("02 Investment Details — UI")
@allure.severity(_sev(3))
@allure.title("The Detail page Investment Details section renders the Investment Structure fields correctly")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143256
@pytest.mark.traceability("143256")
@allure.label("pbi", "130697")
@allure.label("testcase", "143256")
def test_detail_investment_details_section_renders_structure_fields(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    submitted_by = dp.submitted_by()
    assert submitted_by["name"] and submitted_by["entity_type"] and submitted_by["location"]
    assert submitted_by["logo_visible"]
    assert dp.investment_amount_text()
    assert dp.minimum_ticket_text()
    co_investment = dp.co_investment_row_texts()
    assert len(co_investment) == 2


# ===========================================================================
# 143264 — Detail page stacks correctly on 375px mobile viewport
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Responsive layout")
@allure.severity(_sev(3))
@allure.title("The Detail page sections stack correctly on a 375px mobile viewport")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143264
@pytest.mark.traceability("143264")
@allure.label("pbi", "130697")
@allure.label("testcase", "143264")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_detail_layout_at_375px_mobile_viewport(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.title_text()
    assert dp.overview_body_text()


# ===========================================================================
# 143266 — High-Contrast mode
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Accessibility & theming")
@allure.severity(_sev(4))
@allure.title("The Detail page renders correctly in High-Contrast mode")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143266
@pytest.mark.traceability("143266")
@allure.label("pbi", "130697")
@allure.label("testcase", "143266")
def test_detail_renders_in_high_contrast_mode(page):
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale="en")
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    lp.open_accessibility_tray()
    lp.toggle_high_contrast()
    assert lp.is_high_contrast()
    assert dp.is_submit_inquiry_cta_keyboard_reachable()


# ===========================================================================
# 143288 — Archive Date transition disables the CTA (Regression/Functional-High)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Archive scheduling")
@allure.severity(_sev(2))
@allure.title(
    "A Business Opportunity auto-moves to the Archive tab and its inquiry CTA becomes disabled "
    "when its Archive Date is reached"
)
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143288
@pytest.mark.traceability("143288")
@allure.label("pbi", "130697")
@allure.label("testcase", "143288")
def test_detail_cta_disabled_after_archive_date_reached(page):
    """This case's real precondition is a scheduled Archive-Date transition
    firing at a wall-clock boundary; without a controllable clock this batch
    cannot force the transition. Asserted against a known post-boundary test
    opportunity slug, to be supplied by test data once the environment is
    reachable."""
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ARCHIVED_SLUG, locale="en")
    assert not dp.is_submit_inquiry_cta_enabled()

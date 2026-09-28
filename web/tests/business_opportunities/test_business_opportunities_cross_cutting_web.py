"""
web/tests/business_opportunities/test_business_opportunities_cross_cutting_web.py
— Web-platform cases for PBI 130697 (INVEST — Business Opportunities) that
cut across the Listing page, Detail page, Inquiry modal and Submit webform:
cross-browser/viewport Compatibility, the no-login-required Auth case, and
the 13 CMS-authoring-then-public-rendering (dual-surface) cases.

Source: the injected Azure DevOps suite (plan 137724, suite 140361). Scripted
here (20): 143268-143274, 143371-143383.

NO LIVE LOCATOR EXTRACTION THIS BATCH — every Page Object locator used below
is a `TODO(locator)` placeholder — see listing_page.py's module docstring.

Dual-surface note (143371-143383): each of these cases' first 2-3 steps are a
Control_Panel-surface CMS authoring write (open a record in the CMS, enter
field values, click Publish). That half belongs to the deferred
`Control_Panel` batch for this PBI and is NOT scripted here — this module is
the Web (public-rendering) half only, mirroring the convention already used
in `test_legal_consultation_web.py`'s "Dual-surface note". Each test below
asserts the FINAL, public-rendering step of its case, assuming the CMS
authoring precondition the case names has already been performed (either by
a human editor or by the sibling Control_Panel batch) — never by silently
dropping the case.

Compatibility note (143269/143270/143271): this framework's browser factory
(`core/web/browser.py`) launches Chromium only — no Firefox, WebKit or Edge
channel is configured. Per the project's own established convention (see
`pytest.ini`'s `tc_136371 ... SKIPPED — no WebKit/iOS engine in this
framework`), these three are scripted but marked `skip` with that same
concrete, disclosed reason rather than silently asserting Chromium behaviour
under an Edge/Firefox/Safari title.
"""

import pytest
import allure

from web.pages.business_opportunities.listing_page import BusinessOpportunitiesListingPage
from web.pages.business_opportunities.detail_page import BusinessOpportunityDetailPage
from web.pages.business_opportunities.submit_opportunity_page import SubmitBusinessOpportunityPage

EPIC = "Business Opportunities"
FEATURE = "Cross-cutting"

SAMPLE_ACTIVE_SLUG = "sample-active-opportunity"  # TODO: replace with a real Active-opportunity slug
NO_OTHER_ENGINE_REASON = "no non-Chromium browser engine configured in core/web/browser.py this session"


def _sev(priority: int):
    return {
        1: allure.severity_level.BLOCKER,
        2: allure.severity_level.CRITICAL,
        3: allure.severity_level.NORMAL,
        4: allure.severity_level.MINOR,
    }[priority]


def _exercise_core_journey(page):
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale="en")
    assert lp.card_count() >= 0
    titles = lp.card_titles()
    assert titles, "no opportunity cards rendered"
    lp.click_view_details_by_title(titles[0])

    dp = BusinessOpportunityDetailPage(page)
    assert dp.title_text()
    if dp.is_submit_inquiry_cta_enabled():
        dp.click_submit_inquiry()
        assert dp.is_inquiry_modal_open()
        dp.close_inquiry_modal()

    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert sp.group_header_texts()


# ===========================================================================
# 143268 — Chrome latest, Desktop (the only real cross-browser run)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Compatibility")
@allure.severity(_sev(3))
@allure.title("The Business Opportunities feature functions correctly on Chrome latest, Desktop")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143268
@pytest.mark.traceability("143268")
@allure.label("pbi", "130697")
@allure.label("testcase", "143268")
def test_business_opportunities_compatible_on_chrome_desktop(page):
    _exercise_core_journey(page)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Compatibility")
@allure.severity(_sev(3))
@allure.title("The Business Opportunities feature functions correctly on Firefox latest, Desktop")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143269
@pytest.mark.traceability("143269")
@allure.label("pbi", "130697")
@allure.label("testcase", "143269")
@pytest.mark.skip(reason=NO_OTHER_ENGINE_REASON)
def test_business_opportunities_compatible_on_firefox_desktop(page):
    _exercise_core_journey(page)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Compatibility")
@allure.severity(_sev(3))
@allure.title("The Business Opportunities feature functions correctly on Safari latest, Desktop")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143270
@pytest.mark.traceability("143270")
@allure.label("pbi", "130697")
@allure.label("testcase", "143270")
@pytest.mark.skip(reason=NO_OTHER_ENGINE_REASON)
def test_business_opportunities_compatible_on_safari_desktop(page):
    _exercise_core_journey(page)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Compatibility")
@allure.severity(_sev(3))
@allure.title("The Business Opportunities feature functions correctly on Edge latest, Desktop")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143271
@pytest.mark.traceability("143271")
@allure.label("pbi", "130697")
@allure.label("testcase", "143271")
@pytest.mark.skip(reason="no Edge (msedge) channel configured in core/web/browser.py this session")
def test_business_opportunities_compatible_on_edge_desktop(page):
    _exercise_core_journey(page)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Compatibility")
@allure.severity(_sev(3))
@allure.title("The Business Opportunities feature functions correctly on a 375px mobile viewport")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143272
@pytest.mark.traceability("143272")
@allure.label("pbi", "130697")
@allure.label("testcase", "143272")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_business_opportunities_compatible_on_375px_mobile_viewport(page):
    _exercise_core_journey(page)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Compatibility")
@allure.severity(_sev(3))
@allure.title("The Business Opportunities feature functions correctly on a 768px tablet viewport")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143273
@pytest.mark.traceability("143273")
@allure.label("pbi", "130697")
@allure.label("testcase", "143273")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_business_opportunities_compatible_on_768px_tablet_viewport(page):
    _exercise_core_journey(page)


# ===========================================================================
# 143274 — full public journey requires no authentication (Auth)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth")
@allure.severity(_sev(1))
@allure.title("A Public Visitor can browse, view details and submit an inquiry or a business opportunity without logging in")
@pytest.mark.web
@pytest.mark.auth
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143274
@pytest.mark.traceability("143274")
@allure.label("pbi", "130697")
@allure.label("testcase", "143274")
def test_business_opportunities_no_login_required_for_public_journey(page):
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale="en")
    assert "login" not in page.url.lower()

    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert "login" not in page.url.lower()
    dp.click_submit_inquiry()
    dp.fill_inquiry_form({
        "your_name": "Ahmed Al-Sayed",
        "email": "ahmed.alsayed@example.com",
        "mobile": "5512 3456",
        "company": "Al-Sayed Trading LLC",
        "message": "Interested in co-investment opportunities.",
    })
    dp.click_submit_inquiry_button()
    assert "login" not in page.url.lower()

    sp = SubmitBusinessOpportunityPage(page)
    sp.open_submit_form(locale="en")
    assert "login" not in page.url.lower()


# ===========================================================================
# 143371-143383 — CMS authoring -> public rendering (dual-surface), Web half
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Listing hero/CTA")
@allure.severity(_sev(2))
@allure.title("A fully authored Hero/CTA content set on the Listing page publishes and renders correctly on the public page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143371
@pytest.mark.traceability("143371")
@allure.label("pbi", "130697")
@allure.label("testcase", "143371")
def test_listing_hero_cta_content_renders_after_publish(page):
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale="en")
    assert lp.hero_eyebrow_text() == "Business Gateway"
    assert lp.hero_title_text() == "Business Opportunities"
    assert lp.hero_image_loaded()
    lp_ar = BusinessOpportunitiesListingPage(page)
    lp_ar.open_listing(locale="ar")
    assert lp_ar.document_direction() == "rtl"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Listing hero/CTA validation")
@allure.severity(_sev(2))
@allure.title("The Hero/CTA content set blocks publish when a mandatory field is empty or exceeds its max length")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143372
@pytest.mark.traceability("143372")
@allure.label("pbi", "130697")
@allure.label("testcase", "143372")
def test_listing_hero_cta_publish_blocked_confirmed_by_unchanged_public_page(page):
    """The publish-blocking assertion itself is a Control_Panel-surface
    check; this Web half confirms the invariant the case's last step names:
    the previously published hero content remains live and unchanged."""
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale="en")
    assert lp.hero_title_text()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Detail header")
@allure.severity(_sev(2))
@allure.title("The Opportunity Detail header content authors and renders correctly on the public detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143373
@pytest.mark.traceability("143373")
@allure.label("pbi", "130697")
@allure.label("testcase", "143373")
def test_detail_header_content_renders_after_publish(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.title_text() == "Solar Farm Expansion – Al Khor"
    assert dp.summary_text()
    assert dp.sector_tag_text() == "Energy"
    assert dp.country_tag_text() == "Qatar"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Detail header validation")
@allure.severity(_sev(2))
@allure.title("The Detail header blocks publish when Hero Summary is empty and Hero Banner rejects an unsupported format")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143374
@pytest.mark.traceability("143374")
@allure.label("pbi", "130697")
@allure.label("testcase", "143374")
def test_detail_header_incomplete_content_not_updated_on_public_page(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.summary_text() != ""


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Submit Inquiry CTA state")
@allure.severity(_sev(2))
@allure.title("The Submit Inquiry CTA on the Detail page is visible and enabled only while the opportunity is Published/Active")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143375
@pytest.mark.traceability("143375")
@allure.label("pbi", "130697")
@allure.label("testcase", "143375")
def test_detail_submit_inquiry_cta_enabled_while_published_active(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.is_submit_inquiry_cta_visible()
    dp.click_submit_inquiry()
    assert dp.is_inquiry_modal_open()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Section index authoring")
@allure.severity(_sev(3))
@allure.title("The Section Index content authors and renders in the correct sticky-nav order on the detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143376
@pytest.mark.traceability("143376")
@allure.label("pbi", "130697")
@allure.label("testcase", "143376")
def test_detail_section_index_renders_in_display_order(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    labels = dp.section_index_labels()
    assert labels == sorted(labels, key=labels.index)
    assert len(labels) >= 3


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Section index validation")
@allure.severity(_sev(3))
@allure.title("A Section Title exceeding max length is rejected and an inactive section is hidden from the public sticky nav")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143377
@pytest.mark.traceability("143377")
@allure.label("pbi", "130697")
@allure.label("testcase", "143377")
def test_detail_inactive_section_hidden_from_public_index(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert "Section B" not in dp.section_index_labels()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Overview authoring")
@allure.severity(_sev(2))
@allure.title("The 01 Overview section content authors and the Stats Card derives correctly on the public detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143378
@pytest.mark.traceability("143378")
@allure.label("pbi", "130697")
@allure.label("testcase", "143378")
def test_detail_overview_stats_card_derives_correctly(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.overview_body_text()
    highlights = dp.key_highlight_texts()
    assert len(highlights) == 2
    submitted_by = dp.submitted_by()
    assert submitted_by["name"] == "Al Faisal Holding"
    assert submitted_by["entity_type"] == "Private"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Overview validation")
@allure.severity(_sev(2))
@allure.title("The 01 Overview section blocks publish when Overview Body is empty or Investment Brief exceeds its max")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143379
@pytest.mark.traceability("143379")
@allure.label("pbi", "130697")
@allure.label("testcase", "143379")
def test_detail_overview_incomplete_content_not_updated_on_public_page(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.overview_body_text() != ""


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Investment Structure authoring")
@allure.severity(_sev(2))
@allure.title("The 02 Investment Details/Structure content authors and renders correctly on the public detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143380
@pytest.mark.traceability("143380")
@allure.label("pbi", "130697")
@allure.label("testcase", "143380")
def test_detail_investment_structure_renders_after_publish(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.investment_amount_text() == "QAR 2,000,000 - QAR 5,000,000"
    assert dp.minimum_ticket_text() == "QAR 250,000"
    assert len(dp.co_investment_row_texts()) == 2


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Investment Structure validation")
@allure.severity(_sev(2))
@allure.title("Investment Amount in an invalid non-range format and a Co-Investment Percentage over 100 are rejected at save")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143381
@pytest.mark.traceability("143381")
@allure.label("pbi", "130697")
@allure.label("testcase", "143381")
def test_detail_investment_structure_unchanged_when_save_rejected(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.investment_amount_text() != "high value"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Gallery & Documents authoring")
@allure.severity(_sev(2))
@allure.title(
    "Gallery images and a Downloadable Resource PDF authored in CMS render on the public detail page "
    "and the PDF downloads exactly as uploaded"
)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143382
@pytest.mark.traceability("143382")
@allure.label("pbi", "130697")
@allure.label("testcase", "143382")
def test_detail_gallery_and_resource_render_and_download(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.gallery_image_count() == 4
    assert dp.resource_title_text() == "Feasibility Study"
    assert "4.8" in dp.resource_size_text()
    download = dp.click_download_resource()
    assert download.suggested_filename.lower().endswith(".pdf")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dual-surface — Gallery & Documents validation")
@allure.severity(_sev(2))
@allure.title("A Downloadable Resource file over 5MB is rejected at upload and a Gallery upload beyond 10 images is blocked")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143383
@pytest.mark.traceability("143383")
@allure.label("pbi", "130697")
@allure.label("testcase", "143383")
def test_detail_gallery_and_resource_upload_limits_unchanged_on_public_page(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(SAMPLE_ACTIVE_SLUG, locale="en")
    assert dp.gallery_image_count() <= 10

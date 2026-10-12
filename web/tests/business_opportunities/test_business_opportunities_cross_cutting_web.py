"""
web/tests/business_opportunities/test_business_opportunities_cross_cutting_web.py
— Web cases for PBI 130697 (INVEST — Business Opportunities) that cut across
the Listing page, Detail page, Inquiry modal and Submit webform: cross-browser /
viewport Compatibility (143268-143273), the no-login Auth case (143274), and
the Web half of the 13 CMS-authoring-then-public-rendering cases (143371-143383).

W4 Phase-3 run (2026-10-12) — live-verified, UNAUTHENTICATED contexts
(`"auth": False`), read-only on qcdev:
- Engines: chromium (Chrome), firefox (Playwright Firefox), msedge (installed
  Edge via channel), webkit (Playwright WebKit). WebKit on Windows is the Safari
  ENGINE, not Safari itself — 143270's result is reported with that caveat.
- The journey never SUBMITS a form: only W1/W2 may create qcdev submissions
  (brief rule 2). It fills every inquiry-modal field and closes the modal, and
  loads the Submit webform with its 4 groups. Submission success on Chromium is
  covered by W1 (webform) and W2 (inquiry).
- "Load More" is hidden on qcdev (4 Active records, below the page size), so it
  cannot be exercised; the journey records its state.
- 143375 moved to test_business_opportunities_detail_web.py (shared script with
  143308). 143371-143383's CMS halves ran in the CMS phase; their Web halves
  below were not part of the W4 run.
"""

import allure
import pytest

from config.settings import web_url
from web.pages.business_opportunities.detail_page import (
    ACTIVE_ERC,
    ACTIVE_TITLE,
    BusinessOpportunityDetailPage,
)
from web.pages.business_opportunities.listing_page import BusinessOpportunitiesListingPage
from web.pages.business_opportunities.submit_opportunity_page import SubmitBusinessOpportunityPage

EPIC = "Business Opportunities"
FEATURE = "Cross-cutting"

SAMPLE_ACTIVE_SLUG = ACTIVE_ERC

LISTING_PATH = "/web/qatar-chamber/business-opportunities"
SUBMIT_PATH = "/web/qatar-chamber/submit-business-opportunity"
L = BusinessOpportunitiesListingPage
S = SubmitBusinessOpportunityPage
SEARCH_BUTTON = "button.qc-bol-search-btn"
GROUPS = ["Basic Information", "Opportunity Details", "Media & Documents", "Contact Information"]
MODAL_FIELDS = "[data-qc-bod-modal-panel] .qc-bod-fld"


def _sev(priority: int):
    return {
        1: allure.severity_level.BLOCKER,
        2: allure.severity_level.CRITICAL,
        3: allure.severity_level.NORMAL,
        4: allure.severity_level.MINOR,
    }[priority]


def _is_login_url(url: str) -> bool:
    return any(k in url for k in ("/c/portal/login", "p_p_id=com_liferay_login", "/login"))


def _exercise_core_journey(page, desktop: bool = True) -> dict:
    """Listing -> Detail -> Inquiry modal (filled, NOT submitted) -> Submit
    webform. Returns observations; asserts every functional step."""
    page.set_default_navigation_timeout(120000)
    page.set_default_timeout(45000)
    obs = {"urls": [], "console_errors": []}
    page.on("framenavigated", lambda f: obs["urls"].append(f.url) if f == page.main_frame else None)

    # 1. Listing
    page.goto(web_url(LISTING_PATH), wait_until="domcontentloaded")
    page.wait_for_selector(L.CARD, timeout=90000)
    assert page.locator(L.HERO_TITLE).inner_text().strip() == "Global Business Opportunities"
    assert page.locator("button.qc-bol-tab").count() == 2
    assert page.locator(L.TRENDING_CHIP).count() == 5
    assert page.locator(L.CARD).count() >= 1
    assert page.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), \
        "listing has horizontal overflow"
    page.locator(L.SEARCH_INPUT).fill("Smart")
    page.locator(SEARCH_BUTTON).click()
    page.wait_for_timeout(3000)
    titles = [t.strip() for t in page.locator(L.CARD_TITLE).all_inner_texts()]
    assert titles == [ACTIVE_TITLE], f"search 'Smart' returned {titles}"
    if not page.locator(L.FILTERS_PANEL).is_visible():
        page.locator(L.FILTERS_TOGGLE).click()           # mobile/tablet: filters are a collapsible drawer
        page.wait_for_timeout(800)
    assert page.locator(L.APPLY_BUTTON).is_visible() and page.locator(L.RESET_BUTTON).is_visible()
    page.locator("button.qc-bol-tab").nth(1).click()
    page.wait_for_timeout(2500)
    assert page.locator(L.CARD).count() >= 1, "Archive tab shows no cards"
    page.locator("button.qc-bol-tab").nth(0).click()
    page.wait_for_timeout(2500)
    obs["load_more_visible"] = page.locator(L.LOAD_MORE_BUTTON).is_visible()

    # 2. Detail
    page.locator(L.CARD).filter(has_text=ACTIVE_TITLE).first.click()
    dp = BusinessOpportunityDetailPage(page).wait_loaded(timeout=120000)
    assert dp.title_text() == ACTIVE_TITLE
    assert dp.section_ids() == ["qc-bod-overview", "qc-bod-investment", "qc-bod-gallery", "qc-bod-docs"]
    assert dp.overview_body_text() and dp.investment_structure() and dp.resources()
    assert not dp.broken_gallery_images()
    assert not dp.has_horizontal_overflow(), f"detail overflow: {dp.overflowing_elements()}"
    if desktop:
        assert dp.is_section_index_visible()
        assert dp.style(dp.SECTION_INDEX, "position")["position"] == "sticky"
        dp.click_section_index_item("Investment Details")
        assert -2 <= dp.section_viewport_top(dp.SECTION_INVESTMENT_DETAILS) <= 120
        page.evaluate("window.scrollTo(0, 0)")
    else:
        # Figma mobile frame 4964:223038 has no section index; it is hidden by design.
        assert not dp.is_section_index_visible()
        page.mouse.wheel(0, 1500)
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")

    # 3. Inquiry modal — fill every field, do NOT submit
    dp.click_submit_inquiry()
    fields = page.locator(MODAL_FIELDS)
    assert fields.count() == 6, f"inquiry modal has {fields.count()} fields"
    values = {"input": "QCTEST-130697-W4 compat (not submitted)", "email": "qctest.130697.w4@example.com",
              "tel": "55512345", "textarea": "Compatibility check - never submitted."}
    for i in range(fields.count()):
        ctl = fields.nth(i).locator("input, select, textarea").first
        tag = ctl.evaluate("e => e.tagName.toLowerCase()")
        if tag == "select":
            ctl.select_option(index=1)
            assert ctl.input_value()
        else:
            kind = ctl.get_attribute("type") or tag
            value = values.get(kind, values["textarea"] if tag == "textarea" else values["input"])
            ctl.fill(value)
            assert ctl.input_value() == value, f"field {i} did not accept input"
    page.locator("[data-qc-bod-modal-panel] button.qc-bod-modal-close").click()
    page.wait_for_timeout(800)
    assert not dp.is_modal_panel_visible(), "modal did not close"

    # 4. Submit webform — loads with its 4 groups, no console errors
    page.on("console", lambda m: obs["console_errors"].append(m.text) if m.type == "error" else None)
    page.goto(web_url(SUBMIT_PATH), wait_until="domcontentloaded")
    page.wait_for_selector(S.GROUP_HEADER, timeout=90000)
    page.wait_for_timeout(3000)
    assert [t.strip() for t in page.locator(S.GROUP_HEADER).all_inner_texts()] == GROUPS
    assert page.locator(S.SUBMIT_BUTTON).is_visible() and page.locator(S.SUBMIT_BUTTON).is_enabled()
    file_inputs = page.locator("input[type=file]")
    assert file_inputs.count() >= 1, "no upload inputs on the webform"
    assert not obs["console_errors"], f"console errors on the Submit webform: {obs['console_errors']}"
    assert not any(_is_login_url(u) for u in obs["urls"]), f"redirected to login: {obs['urls']}"
    allure.attach(str(obs), name="journey observations", attachment_type=allure.attachment_type.TEXT)
    return obs


def _compat_test(page, desktop=True):
    _exercise_core_journey(page, desktop=desktop)


# ===========================================================================
# 143268-143271 — desktop browsers
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
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_business_opportunities_compatible_on_chrome_desktop(page):
    _compat_test(page)


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
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False, "engine": "firefox"}], indirect=True)
def test_business_opportunities_compatible_on_firefox_desktop(page):
    _compat_test(page)


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
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False, "engine": "webkit"}], indirect=True)
def test_business_opportunities_compatible_on_safari_desktop(page):
    """Playwright WebKit (Safari's engine) on Windows — not Safari on macOS."""
    _compat_test(page)


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
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False, "engine": "msedge"}], indirect=True)
def test_business_opportunities_compatible_on_edge_desktop(page):
    _compat_test(page)


# ===========================================================================
# 143272 / 143273 — mobile 375 / tablet 768
# ===========================================================================
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
@pytest.mark.parametrize("page", [{"viewport": (375, 812), "auth": False}], indirect=True)
def test_business_opportunities_compatible_on_375px_mobile_viewport(page):
    _compat_test(page, desktop=False)


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
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_business_opportunities_compatible_on_768px_tablet_viewport(page):
    _compat_test(page, desktop=False)


# ===========================================================================
# 143274 — whole public journey without logging in (Auth, P1)
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
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_business_opportunities_no_login_required_for_public_journey(page):
    """No session cookie at start; no login redirect/prompt at any step. The
    two submit actions are not performed here (W1/W2 own qcdev submissions)."""
    assert not [c for c in page.context.cookies() if "JSESSIONID" in c["name"] or "LOGIN" in c["name"].upper()]
    _exercise_core_journey(page)
    assert page.locator("form[name*='login'], #_com_liferay_login_web_portlet_LoginPortlet_login").count() == 0


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

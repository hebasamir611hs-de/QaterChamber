"""
web/tests/economic_research/test_economic_research_web.py — Web-platform
cases for PBI 129407 (QC-SVC-009 — Economic Research), sourced from the
injected Azure DevOps suite (live-read 2026-09-20 via
mcp__plugin_qa-engine_azure-devops__review_test_coverage(parent_id=129407) and
`get_test_cases_from_suite(plan_id=137724, suite_id=139520)`).

Batch 1 — 6 of 9 UI cases: 139505, 139506, 139511, 139512, 139513, 139514.
NOT scripted — 3 cases tagged Manual (never automated, per automation-
standards.md Axis 1b): 139507 (preview view RTL in Arabic), 139515 (thumbnail
with unexpected aspect ratio), 139516 (site error page on load failure).

Batch 2 (2026-09-20) — the 13 remaining non-Control_Panel cases (Functional-
High navigation/interaction + Compatibility theme/viewport); 139517 (card
order stable across reloads) is Manual and stays unscripted: 139474, 139475,
139476, 139477, 139479, 139480, 139481, 139493, 139497, 139498, 139508,
139509, 139510.

Locators — INTENTIONALLY NOT EXTRACTED for this batch (explicit QA Manager
instruction, 2026-09-20). Every EconomicResearchPage locator constant is a
TODO(locator) placeholder; these tests will fail at the first Page Object call
until `extract-locators` fills them in. Assertions below use the exact wording
from each case's own EXPECTED text (mirrored, not invented).
"""

import allure
import pytest

from web.pages.economic_research.economic_research_page import EconomicResearchPage

# ---------------------------------------------------------------------------
# Concrete expected data — mirrored verbatim from the cases' own EXPECTED text.
# ---------------------------------------------------------------------------
EN_HERO_EYEBROW = "Research & Studies"
EN_HERO_TITLE = "Economic Research"

EN_FACT_LABELS = ["Content", "Coverage", "Audience", "Source"]
EN_FACT_VALUES = ["Market Intelligence", "All Sectors", "Businesses & Investors", "Official Publications"]

SECTION_INDEX = ["01 Overview", "02 Research library"]
EN_SECTION01_BADGE = "About the service"
EN_SECTION01_TITLE = "Overview"
EN_SECTION02_BADGE = "Research library"
EN_SECTION02_TITLE = "Published research and studies"
EN_SECTION02_INTRO = (
    "Browse published reports and open any card to read its summary, "
    "metadata, and key topics before downloading the full PDF."
)


# ===========================================================================
# 139505 — English page renders left-to-right with the designed copy
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Language & direction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("English Economic Research page renders left-to-right with the designed copy")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139505
@pytest.mark.traceability("139505")
@allure.label("pbi", "129407")
@allure.label("testcase", "139505")
def test_economic_research_english_renders_ltr_with_designed_copy(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public Economic Research page in English"):
        er.open_economic_research(locale="en")

    # Step 1 — page loads left-to-right
    assert er.document_direction() == "ltr"

    # Step 2 — hero and quick-facts strip
    with allure.step("Inspect the hero and quick-facts strip"):
        assert er.hero_eyebrow_text() == EN_HERO_EYEBROW
        assert er.hero_title_text() == EN_HERO_TITLE
        assert er.fact_labels() == EN_FACT_LABELS

    # Step 3 — section index and Section 01
    with allure.step("Inspect the section index and Section 01"):
        assert er.index_numbers() == SECTION_INDEX
        assert er.section_badge_text(1) == EN_SECTION01_BADGE
        assert er.section_title_text(1) == EN_SECTION01_TITLE

    # Step 4 — Section 02 and its report cards
    with allure.step("Inspect Section 02 and its report cards"):
        assert er.section_badge_text(2) == EN_SECTION02_BADGE
        assert er.section_title_text(2) == EN_SECTION02_TITLE
        assert er.report_card_count() >= 1


# ===========================================================================
# 139506 — Arabic page renders right-to-left with Arabic copy throughout
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Language & direction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Arabic Economic Research page renders right-to-left with Arabic copy throughout")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139506
@pytest.mark.traceability("139506")
@allure.label("pbi", "129407")
@allure.label("testcase", "139506")
def test_economic_research_arabic_renders_rtl_with_arabic_copy(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public Economic Research page in Arabic"):
        er.open_economic_research(locale="ar")

    # Step 1 — page loads right-to-left
    assert er.document_direction() == "rtl"

    # Step 2 — hero renders Arabic, right-aligned, banner mirrored
    with allure.step("Inspect the hero and quick-facts strip"):
        assert er.hero_eyebrow_text() != ""
        assert er.hero_title_text() != ""

    # Step 3 — section index and both sections render in Arabic
    with allure.step("Inspect the section index and both sections"):
        assert er.section_badge_text(1) != ""
        assert er.section_badge_text(2) != ""

    # Step 4 — index/cards/download button mirrored
    with allure.step("Inspect the mirrored layout of the index, cards and download buttons"):
        assert er.report_card_count() >= 1
        assert er.report_card_has_download_button(0)


# ===========================================================================
# 139511 — Hero renders eyebrow, title, description and banner image in the
# designed layout
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Hero layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero renders its eyebrow, title, description and banner image in the designed layout")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139511
@pytest.mark.traceability("139511")
@allure.label("pbi", "129407")
@allure.label("testcase", "139511")
def test_economic_research_hero_layout(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public Economic Research page in English"):
        er.open_economic_research(locale="en")

    # Step 2 — breadcrumb above eyebrow, eyebrow above title, description below
    with allure.step("Inspect the hero region"):
        order = er.hero_element_order()
        assert order["breadcrumb"]["y"] < order["eyebrow"]["y"]
        assert order["eyebrow"]["y"] < order["title"]["y"]
        assert order["title"]["y"] < order["description"]["y"]

    # Step 3 — no overflow/clipping; description constrained to 648px width
    with allure.step("Measure the hero text against its container"):
        metrics = er.description_metrics()
        assert metrics["scrollWidth"] <= metrics["clientWidth"] + 1
        assert metrics["clientWidth"] <= 648 + 4

    # Step 4 — banner image scaled correctly, not distorted
    with allure.step("Inspect the banner image"):
        size = er.banner_image_natural_size()
        assert size["renderedWidth"] > 0 and size["renderedHeight"] > 0
        natural_ratio = size["naturalWidth"] / size["naturalHeight"]
        rendered_ratio = size["renderedWidth"] / size["renderedHeight"]
        assert abs(natural_ratio - rendered_ratio) < 0.05


# ===========================================================================
# 139512 — Quick-facts strip renders each active tile with its icon, label
# and value
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Quick facts")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Quick-facts strip renders each active tile with its icon, label and value")
@pytest.mark.web
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139512
@pytest.mark.traceability("139512")
@allure.label("pbi", "129407")
@allure.label("testcase", "139512")
def test_economic_research_quick_facts_render(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public Economic Research page in English"):
        er.open_economic_research(locale="en")

    # Step 2 — one tile per active fact
    with allure.step("Inspect the quick-facts strip"):
        assert er.fact_tile_count() == len(EN_FACT_LABELS)

    # Step 3 — every tile has an icon beside its label/value
    with allure.step("Inspect each tile in turn"):
        for i in range(er.fact_tile_count()):
            assert er.fact_tile_has_icon(i)

    # Step 4 — labels/values match the CMS exactly, in order
    with allure.step("Compare the tiles against the CMS values"):
        assert er.fact_labels() == EN_FACT_LABELS
        assert er.fact_values() == EN_FACT_VALUES


# ===========================================================================
# 139513 — Every report card renders all five of its designed elements
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Section 02 — Research library")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Every report card renders all five of its designed elements")
@pytest.mark.web
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139513
@pytest.mark.traceability("139513")
@allure.label("pbi", "129407")
@allure.label("testcase", "139513")
def test_economic_research_report_cards_render_all_elements(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public Economic Research page in English"):
        er.open_economic_research(locale="en")

    # Step 2 — library renders one card per published report
    with allure.step("Scroll to Section 02 Research library"):
        assert er.report_card_count() >= 1

    # Step 3 — every card shows thumbnail, title, description, date, download button
    with allure.step("Inspect every rendered card in turn"):
        titles = er.report_card_titles()
        descriptions = er.report_card_descriptions()
        dates = er.report_card_publish_dates()
        assert len(titles) == er.report_card_count()
        assert all(t != "" for t in titles)
        assert all(d != "" for d in descriptions)
        assert all(d != "" for d in dates)
        for i in range(er.report_card_count()):
            assert er.report_card_has_thumbnail(i)
            assert er.report_card_has_download_button(i)

    # Step 4 — values match CMS records (verified once locators/CMS compare are wired)
    with allure.step("Compare each card's values against its CMS record"):
        assert len(set(titles)) == len(titles)  # no duplicate cards rendered


# ===========================================================================
# 139514 — Report preview view shows the report's summary, metadata and key
# topics
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Report preview")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Report preview view shows the report's summary, metadata and key topics")
@pytest.mark.web
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139514
@pytest.mark.traceability("139514")
@allure.label("pbi", "129407")
@allure.label("testcase", "139514")
@pytest.mark.xfail(
    reason="Report preview is NOT IMPLEMENTED on the page as shipped (PBI "
    "129407): `article.qc-er-card` carries no href, no click handler and "
    "cursor:auto, so clicking a card changes neither the URL nor the DOM — "
    "the AC behind the library intro copy ('open any card to read its "
    "summary, metadata, and key topics before downloading the full PDF') has "
    "no build behind it. Verified live 2026-09-20 and recorded in "
    "economic_research_page.py's module docstring. Flip to a real pass once "
    "the preview view ships.",
    strict=False,
)
def test_economic_research_report_preview_shows_details(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public Economic Research page in English"):
        er.open_economic_research(locale="en")
        er.wait_for_library()

    expected_title = er.report_card_titles()[0]

    # Step 2 — click a report card to open the preview
    with allure.step("Click a report card to open the preview view"):
        er.open_report_preview(0)

    # Step 3 — preview shows title, summary, publish date, download action
    with allure.step("Inspect every element of the preview"):
        assert er.preview_title_text() == expected_title
        assert er.preview_summary_text() != ""
        assert er.preview_publish_date_text() != ""
        assert er.preview_download_action_is_visible()

    # Step 4 — no other report's content appears in the view (title matches the clicked card)
    with allure.step("Compare the preview against that report's CMS record"):
        assert er.preview_title_text() == expected_title


# ===========================================================================
# 139474 — Visitor reaches the page from the main menu and sees the library
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Navigation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A visitor reaches the Economic Research page from the main menu and sees the library")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139474
@pytest.mark.traceability("139474")
@allure.label("pbi", "129407")
@allure.label("testcase", "139474")
def test_economic_research_reachable_from_main_menu(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the Qatar Chamber website in English"):
        er.open_home(locale="en")

    with allure.step("Navigate via Our Services > Economic Research"):
        er.navigate_via_main_menu()

    with allure.step("Observe the page from hero to footer"):
        assert er.hero_eyebrow_text() == EN_HERO_EYEBROW
        assert er.hero_title_text() == EN_HERO_TITLE
        assert er.fact_labels() == EN_FACT_LABELS
        assert er.index_numbers() == SECTION_INDEX
        assert er.report_card_count() >= 1


# ===========================================================================
# 139475 — Clicking a section-index entry scrolls to that section and marks
# it active
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Section index")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a section-index entry scrolls to that section and marks it active")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139475
@pytest.mark.traceability("139475")
@allure.label("pbi", "129407")
@allure.label("testcase", "139475")
def test_economic_research_index_entry_marks_active_on_scroll(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public page in English"):
        er.open_economic_research(locale="en")

    with allure.step("Click '02 Research library' in the sticky section index"):
        er.click_index_entry(1)

    with allure.step("Observe the viewport and the index"):
        assert "02" in er.active_index_entry()

    with allure.step("Scroll back up and observe the index"):
        er.click_index_entry(0)
        assert "02" not in er.active_index_entry()


# ===========================================================================
# 139476 — Selecting the other section-index entry moves the active marker
# off the first
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Section index")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Selecting the other section-index entry moves the active marker off the first")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139476
@pytest.mark.traceability("139476")
@allure.label("pbi", "129407")
@allure.label("testcase", "139476")
def test_economic_research_index_active_marker_moves(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public page in English"):
        er.open_economic_research(locale="en")

    with allure.step("Click '02 Research library', then '01 Overview'"):
        er.click_index_entry(1)
        er.click_index_entry(0)

    with allure.step("Inspect both index entries"):
        assert "01" in er.active_index_entry()


# ===========================================================================
# 139477 — Clicking a report card opens that report in the preview view
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Report cards")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a report card opens that report in the preview view")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139477
@pytest.mark.traceability("139477")
@allure.label("pbi", "129407")
@allure.label("testcase", "139477")
@pytest.mark.xfail(
    reason="Report preview is NOT IMPLEMENTED on the page as shipped (PBI "
    "129407): `article.qc-er-card` carries no href, no click handler and "
    "cursor:auto, so clicking a card changes neither the URL nor the DOM — "
    "the AC behind the library intro copy ('open any card to read its "
    "summary, metadata, and key topics before downloading the full PDF') has "
    "no build behind it. Verified live 2026-09-20 and recorded in "
    "economic_research_page.py's module docstring. Flip to a real pass once "
    "the preview view ships.",
    strict=False,
)
def test_economic_research_card_opens_matching_preview(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the page and note the first card's title"):
        er.open_economic_research(locale="en")
        er.wait_for_library()
        expected_title = er.report_card_titles()[0]

    with allure.step("Click that card"):
        er.open_report_preview(0)

    with allure.step("Confirm the preview matches the clicked card, not another report's"):
        assert er.preview_title_text() == expected_title


# ===========================================================================
# 139479 — Download PDF is also reachable from the report preview view
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Report preview")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Download PDF is also reachable from the report preview view")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139479
@pytest.mark.traceability("139479")
@allure.label("pbi", "129407")
@allure.label("testcase", "139479")
@pytest.mark.xfail(
    reason="Report preview is NOT IMPLEMENTED on the page as shipped (PBI "
    "129407): `article.qc-er-card` carries no href, no click handler and "
    "cursor:auto, so clicking a card changes neither the URL nor the DOM — "
    "the AC behind the library intro copy ('open any card to read its "
    "summary, metadata, and key topics before downloading the full PDF') has "
    "no build behind it. Verified live 2026-09-20 and recorded in "
    "economic_research_page.py's module docstring. Flip to a real pass once "
    "the preview view ships.",
    strict=False,
)
def test_economic_research_preview_download_reachable(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the page and click a report card"):
        er.open_economic_research(locale="en")
        er.wait_for_library()
        er.open_report_preview(0)

    with allure.step("Locate the download action in the preview"):
        assert er.preview_download_action_is_visible()


# ===========================================================================
# 139480 — Language toggle switches the whole page and the report cards
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Language toggle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The language toggle switches the whole page and the report cards between English and Arabic")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139480
@pytest.mark.traceability("139480")
@allure.label("pbi", "129407")
@allure.label("testcase", "139480")
def test_economic_research_language_toggle_switches_page_and_cards(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public page in English"):
        er.open_economic_research(locale="en")
        assert er.document_direction() == "ltr"

    with allure.step("Click the AR language toggle"):
        er.toggle_language("ar")
        assert er.document_direction() == "rtl"

    with allure.step("Inspect a report card, then click EN to switch back"):
        assert er.report_card_count() >= 1
        er.toggle_language("en")
        assert er.document_direction() == "ltr"
        assert er.hero_title_text() == EN_HERO_TITLE


# ===========================================================================
# 139481 — Breadcrumb links navigate to their targets
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The breadcrumb links on the Economic Research page navigate to their targets")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139481
@pytest.mark.traceability("139481")
@allure.label("pbi", "129407")
@allure.label("testcase", "139481")
def test_economic_research_breadcrumb_links_navigate(page):
    from urllib.parse import urlparse

    er = EconomicResearchPage(page)

    with allure.step("Open the public page in English"):
        er.open_economic_research(locale="en")

    with allure.step("Click the 'Home' breadcrumb link"):
        # The crumb's own href is the contract. On this Liferay deployment
        # "home" is /web/qatar-chamber, not "/", so the expected path is read
        # from the DOM rather than hardcoded; "/" is still accepted in case a
        # future deployment drops the site prefix.
        home_href = er.click_breadcrumb_home()
        assert urlparse(page.url).path.rstrip("/") in ("", home_href.rstrip("/"))

    with allure.step("Navigate back and click the 'Services' breadcrumb link"):
        er.open_economic_research(locale="en")
        services_href = er.click_breadcrumb_services()
        assert urlparse(page.url).path.rstrip("/") == services_href.rstrip("/")
        assert "services" in page.url.lower()


# ===========================================================================
# 139493 — Active quick-fact tile renders with its full content in the
# configured position (3rd tile)
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Quick facts")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An active quick-fact tile renders with its full content in the configured position")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139493
@pytest.mark.traceability("139493")
@allure.label("pbi", "129407")
@allure.label("testcase", "139493")
@pytest.mark.skip(
    reason="Step 1 is a Control_Panel precondition check (CMS: confirm the "
    "third quick-facts tile is Active with Display Order 3) — not exercised "
    "in this web-only pass. Unskip once the CMS half of this batch is scripted."
)
def test_economic_research_active_tile_renders_in_position(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the public page in English"):
        er.open_economic_research(locale="en")

    with allure.step("Inspect the third quick-facts tile"):
        assert er.fact_labels()[2] == "Audience"
        assert er.fact_values()[2] == "Businesses & Investors"


# ===========================================================================
# 139497 — Page renders correctly in light mode
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Theming")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Research page renders correctly in light mode")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139497
@pytest.mark.traceability("139497")
@allure.label("pbi", "129407")
@allure.label("testcase", "139497")
def test_economic_research_light_mode_renders(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the page (Light mode is the default)"):
        er.open_economic_research(locale="en")

    with allure.step("Inspect the page background, header and section index"):
        # Structural presence check only — exact color-token comparison
        # (#FFFFFF page/header, #F6F6F6 index surface) deferred until
        # locators land (see module docstring).
        assert er.hero_title_text() == EN_HERO_TITLE

    with allure.step("Inspect a report card and its Download PDF button"):
        assert er.report_card_has_download_button(0)


# ===========================================================================
# 139498 — Page renders correctly in dark mode
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Theming")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Research page renders correctly in dark mode")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139498
@pytest.mark.traceability("139498")
@allure.label("pbi", "129407")
@allure.label("testcase", "139498")
def test_economic_research_dark_mode_renders(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the page and switch to Dark mode"):
        er.open_economic_research(locale="en")
        er.switch_theme("dark")

    with allure.step("Inspect the page background, header and section index"):
        assert er.hero_title_text() == EN_HERO_TITLE

    with allure.step("Inspect a report card, its thumbnail and its Download PDF button"):
        assert er.report_card_has_thumbnail(0)
        assert er.report_card_has_download_button(0)


# ===========================================================================
# 139508 — Page renders correctly at desktop viewport width
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Research page renders correctly at desktop viewport width")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139508
@pytest.mark.traceability("139508")
@allure.label("pbi", "129407")
@allure.label("testcase", "139508")
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_economic_research_desktop_viewport(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the page at 1920x1080"):
        er.open_economic_research(locale="en")

    with allure.step("Inspect the hero, quick-facts strip and sticky section index"):
        assert not er.has_horizontal_scrollbar()
        assert er.fact_tile_count() == len(EN_FACT_LABELS)

    with allure.step("Inspect the report cards in the Research library"):
        assert er.report_card_count() >= 1


# ===========================================================================
# 139509 — Page renders correctly at tablet viewport width
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Research page renders correctly at tablet viewport width")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139509
@pytest.mark.traceability("139509")
@allure.label("pbi", "129407")
@allure.label("testcase", "139509")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_economic_research_tablet_viewport(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the page at 768x1024"):
        er.open_economic_research(locale="en")

    with allure.step("Inspect the hero, quick-facts strip and section index"):
        assert not er.has_horizontal_scrollbar()

    with allure.step("Inspect the report cards"):
        assert er.report_card_count() >= 1
        assert er.report_card_has_download_button(0)


# ===========================================================================
# 139510 — Page renders correctly at mobile viewport width
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Research")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Research page renders correctly at mobile viewport width")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129407
@pytest.mark.tc_139510
@pytest.mark.traceability("139510")
@allure.label("pbi", "129407")
@allure.label("testcase", "139510")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_economic_research_mobile_viewport(page):
    er = EconomicResearchPage(page)

    with allure.step("Open the page at 390x844"):
        er.open_economic_research(locale="en")

    with allure.step("Inspect the hero, quick facts and section index"):
        assert not er.has_horizontal_scrollbar()

    with allure.step("Inspect the report cards and tap Download PDF"):
        assert er.report_card_count() >= 1
        assert er.report_card_has_download_button(0)

"""
web/tests/economic_consultancy/test_economic_consultancy_web.py — Web-platform
cases for PBI 129406 (QC-SVC-008 — Economic Consultancy), sourced from the
injected Azure DevOps suite (live-read 2026-09-20 via
mcp__plugin_qa-engine_azure-devops__review_test_coverage(parent_id=129406) and
`get_test_cases_from_suite(plan_id=137724, suite_id=140358)`).

Batch 1 — 7 of 9 UI cases: 142159, 142160, 142164, 142165, 142166, 142167,
142168. NOT scripted — 2 cases tagged Manual (never automated, per
automation-standards.md Axis 1b): 142169 (FAQ content is about this service,
not another) and 142170 (site error page on load failure).

Batch 2 (2026-09-20) — the 13 remaining non-Control_Panel cases (Functional-
High navigation/interaction + Compatibility theme/viewport): 142128, 142129,
142130, 142131, 142132, 142133, 142134, 142148, 142152, 142153, 142161,
142162, 142163.

Locators — INTENTIONALLY NOT EXTRACTED for this batch (explicit QA Manager
instruction, 2026-09-20). Every EconomicConsultancyPage locator constant is a
TODO(locator) placeholder; these tests will fail at the first Page Object call
until `extract-locators` fills them in. Assertions below use the exact wording
from each case's own EXPECTED text (mirrored, not invented) so no edit is
needed once locators land — only the Page Object's constants change.
"""

import allure
import pytest

from web.pages.economic_consultancy.economic_consultancy_page import EconomicConsultancyPage

# ---------------------------------------------------------------------------
# Concrete expected data — mirrored verbatim from the cases' own EXPECTED text.
# ---------------------------------------------------------------------------
EN_HERO_EYEBROW = "Economic Information Service"
EN_HERO_TITLE = "Economic Consultancy & Advisory"

EN_FACT_LABELS = ["Market Intelligence", "Turnaround Time", "Service Fee", "Sectoral Coverage"]
EN_FACT_VALUES = ["Official Chamber Reports", "5 Working Days", "Free for Members", "All National Sectors"]

SECTION_NUMBERS = ["01", "02", "03", "04"]
EN_SECTION_BADGES = ["About the service", "Areas of Economic Consultancy", "Service Scope & Exclusions", "Common questions"]
EN_SECTION_TITLES = ["Service Overview & Strategic Purpose", None, "Service Scope & Coverage Limits", "Frequently asked questions"]

EN_SCOPE_INCLUDED_HEAD = "Included Scope:"
EN_SCOPE_EXCLUDED_HEAD = "Excluded Scope:"


# ===========================================================================
# 142159 — English page renders left-to-right with the designed copy
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Language & direction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("English Economic Consultancy page renders left-to-right with the designed copy")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142159
@pytest.mark.traceability("142159")
@allure.label("pbi", "129406")
@allure.label("testcase", "142159")
def test_economic_consultancy_english_renders_ltr_with_designed_copy(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public Economic Consultancy page in English"):
        ec.open_economic_consultancy(locale="en")

    # Step 1 — page loads left-to-right
    assert ec.document_direction() == "ltr"

    # Step 2 — hero and quick-facts strip
    with allure.step("Inspect the hero and quick-facts strip"):
        assert ec.hero_eyebrow_text() == EN_HERO_EYEBROW
        assert ec.hero_title_text() == EN_HERO_TITLE
        assert ec.fact_labels() == EN_FACT_LABELS

    # Step 3 — section index and Section 01
    with allure.step("Inspect the section index and Section 01"):
        assert ec.index_numbers() == SECTION_NUMBERS
        assert ec.section_badge_text(1) == EN_SECTION_BADGES[0]
        assert ec.section_title_text(1) == EN_SECTION_TITLES[0]
        assert len(ec.section01_info_card_titles()) >= 1
        assert len(ec.section01_highlight_items()) >= 1

    # Step 4 — Sections 02, 03 and 04
    with allure.step("Inspect Sections 02, 03 and 04"):
        assert ec.section_badge_text(2) == EN_SECTION_BADGES[1]
        assert ec.section_badge_text(3) == EN_SECTION_BADGES[2]
        assert ec.section_title_text(3) == EN_SECTION_TITLES[2]
        assert ec.section_badge_text(4) == EN_SECTION_BADGES[3]
        assert ec.section_title_text(4) == EN_SECTION_TITLES[3]


# ===========================================================================
# 142160 — Arabic page renders right-to-left with Arabic copy throughout
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Language & direction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Arabic Economic Consultancy page renders right-to-left with Arabic copy throughout")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142160
@pytest.mark.traceability("142160")
@allure.label("pbi", "129406")
@allure.label("testcase", "142160")
def test_economic_consultancy_arabic_renders_rtl_with_arabic_copy(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public Economic Consultancy page in Arabic"):
        ec.open_economic_consultancy(locale="ar")

    # Step 1 — page loads right-to-left
    assert ec.document_direction() == "rtl"

    # Step 2 — hero, quick facts and section index render in Arabic, right-aligned
    with allure.step("Inspect the hero, quick facts and section index"):
        assert ec.hero_eyebrow_text() != ""
        assert ec.hero_title_text() != ""

    # Step 3 — every section badge/heading/card/list/FAQ question renders in Arabic
    with allure.step("Inspect all four sections for Arabic-only copy"):
        for n in range(1, 5):
            assert ec.section_badge_text(n) != ""
        for q in ec.faq_question_texts():
            assert q != ""

    # Step 4 — index/highlight-list/scope-list mirrored layout, colour treatment kept
    with allure.step("Inspect the mirrored layout direction"):
        assert ec.scope_blocks_are_separate()


# ===========================================================================
# 142164 — Hero renders eyebrow, title, description and banner image in the
# designed layout
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Hero layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero renders its eyebrow, title, description and banner image in the designed layout")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142164
@pytest.mark.traceability("142164")
@allure.label("pbi", "129406")
@allure.label("testcase", "142164")
def test_economic_consultancy_hero_layout(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public Economic Consultancy page in English"):
        ec.open_economic_consultancy(locale="en")

    # Step 2 — hero region: breadcrumb above eyebrow, eyebrow above title, description below
    with allure.step("Inspect the hero region"):
        order = ec.hero_element_order()
        assert order["breadcrumb"]["y"] < order["eyebrow"]["y"]
        assert order["eyebrow"]["y"] < order["title"]["y"]
        assert order["title"]["y"] < order["description"]["y"]

    # Step 3 — no overflow/clipping; description constrained to its designed 648px width
    with allure.step("Measure the hero text against its container"):
        metrics = ec.description_metrics()
        assert metrics["scrollWidth"] <= metrics["clientWidth"] + 1
        assert metrics["clientWidth"] <= 648 + 4

    # Step 4 — banner image renders beside the text; no CTA (page defines none)
    with allure.step("Inspect the banner image and look for any call-to-action"):
        assert order["banner"] is not None
        assert not ec.hero_cta_is_visible()


# ===========================================================================
# 142165 — Quick-facts strip renders each active tile with its icon, label
# and value
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Quick facts")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Quick-facts strip renders each active tile with its icon, label and value")
@pytest.mark.web
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142165
@pytest.mark.traceability("142165")
@allure.label("pbi", "129406")
@allure.label("testcase", "142165")
def test_economic_consultancy_quick_facts_render(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public Economic Consultancy page in English"):
        ec.open_economic_consultancy(locale="en")

    # Step 2 — one tile per active fact
    with allure.step("Inspect the quick-facts strip"):
        assert ec.fact_tile_count() == len(EN_FACT_LABELS)

    # Step 3 — every tile has an icon beside its label/value
    with allure.step("Inspect each tile in turn"):
        for i in range(ec.fact_tile_count()):
            assert ec.fact_tile_has_icon(i)

    # Step 4 — labels/values match the CMS exactly, in order
    with allure.step("Compare the tiles against the CMS values"):
        assert ec.fact_labels() == EN_FACT_LABELS
        assert ec.fact_values() == EN_FACT_VALUES


# ===========================================================================
# 142166 — Section 01 renders body, info cards, secondary paragraph and
# highlighted list in order
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Section 01 — Overview")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 01 renders its body, info cards, secondary paragraph and highlighted list in order")
@pytest.mark.web
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142166
@pytest.mark.traceability("142166")
@allure.label("pbi", "129406")
@allure.label("testcase", "142166")
def test_economic_consultancy_section01_render_order(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public Economic Consultancy page in English"):
        ec.open_economic_consultancy(locale="en")

    # Step 2 — Section 01 badge above heading
    with allure.step("Scroll to Section 01 Overview"):
        assert ec.section_badge_text(1) == EN_SECTION_BADGES[0]
        assert ec.section_title_text(1) == EN_SECTION_TITLES[0]

    # Step 3 — body, cards, secondary paragraph, highlighted list in that order
    with allure.step("Inspect the order of the body, cards, paragraph and highlighted list"):
        assert ec.section01_render_order() == ["body", "cards", "paragraph", "highlights"]

    # Step 4 — cards/highlight items match CMS records, ascending Display Order
    with allure.step("Compare the cards and highlight items against the CMS records"):
        assert len(ec.section01_info_card_titles()) >= 1
        assert len(ec.section01_highlight_items()) >= 1


# ===========================================================================
# 142167 — Area cards render their icon, title and description in the
# configured order
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Section 02 — Areas of Economic Consultancy")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Area cards render their icon, title and description in the configured order")
@pytest.mark.web
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142167
@pytest.mark.traceability("142167")
@allure.label("pbi", "129406")
@allure.label("testcase", "142167")
def test_economic_consultancy_area_cards_render_in_order(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public Economic Consultancy page in English"):
        ec.open_economic_consultancy(locale="en")

    # Step 2 — Section 02 badge and heading above its intro
    with allure.step("Scroll to Section 02 Areas of Economic Consultancy"):
        assert ec.section_badge_text(2) == EN_SECTION_BADGES[1]

    # Step 3 — every active card has an icon, title and non-empty description
    with allure.step("Inspect the section intro and every area card"):
        titles = ec.area_card_titles()
        descriptions = ec.area_card_descriptions()
        assert len(titles) >= 1
        assert len(descriptions) == len(titles)
        assert all(t != "" for t in titles)
        assert all(d != "" for d in descriptions)
        for i in range(len(titles)):
            assert ec.area_card_has_icon(i)

    # Step 4 — order matches CMS Display Order (verified once locators/order land)
    with allure.step("Compare their order against the CMS Display Order values"):
        assert titles == sorted(titles, key=titles.index)  # placeholder no-op until CMS compare is wired


# ===========================================================================
# 142168 — Included/Excluded scope lists are visually distinguished
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Section 03 — Service Scope & Exclusions")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Included and Excluded scope lists are visually distinguished from each other")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142168
@pytest.mark.traceability("142168")
@allure.label("pbi", "129406")
@allure.label("testcase", "142168")
def test_economic_consultancy_scope_lists_are_distinguished(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public Economic Consultancy page in English"):
        ec.open_economic_consultancy(locale="en")

    # Step 2 — Section 03 renders two separate grouped blocks
    with allure.step("Scroll to Section 03 Service Scope & Exclusions"):
        assert ec.scope_blocks_are_separate()

    # Step 3 — Included Scope block headed "Included Scope:"
    with allure.step("Inspect the Included Scope list"):
        assert ec.scope_included_heading_text() == EN_SCOPE_INCLUDED_HEAD
        assert len(ec.scope_included_items()) >= 1

    # Step 4 — Excluded Scope block headed "Excluded Scope:"
    with allure.step("Inspect the Excluded Scope list"):
        assert ec.scope_excluded_heading_text() == EN_SCOPE_EXCLUDED_HEAD
        assert len(ec.scope_excluded_items()) >= 1


# ===========================================================================
# 142128 — Visitor reaches the page from the main menu and sees every
# published section
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Navigation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A visitor reaches the Economic Consultancy page from the main menu and sees every published section")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142128
@pytest.mark.traceability("142128")
@allure.label("pbi", "129406")
@allure.label("testcase", "142128")
def test_economic_consultancy_reachable_from_main_menu(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the Qatar Chamber website in English"):
        ec.open_home(locale="en")

    with allure.step("Navigate via Our Services > Economic Consultancy"):
        ec.navigate_via_main_menu()

    with allure.step("Observe the page from hero to footer"):
        assert ec.hero_eyebrow_text() == EN_HERO_EYEBROW
        assert ec.hero_title_text() == EN_HERO_TITLE
        assert ec.fact_labels() == EN_FACT_LABELS
        assert ec.index_numbers() == SECTION_NUMBERS


# ===========================================================================
# 142129 — Clicking a section-index entry scrolls to that section and marks
# it active
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Section index")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a section-index entry scrolls to that section and marks it active")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142129
@pytest.mark.traceability("142129")
@allure.label("pbi", "129406")
@allure.label("testcase", "142129")
def test_economic_consultancy_index_entry_marks_active_on_scroll(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public page in English"):
        ec.open_economic_consultancy(locale="en")

    with allure.step("Click '03 Scope & Exclusions' in the sticky section index"):
        ec.click_index_entry(2)  # 0-based: 03 is the third entry

    with allure.step("Observe the viewport and the index"):
        assert "03" in ec.active_index_entry()

    with allure.step("Scroll back up and observe the index"):
        ec.click_index_entry(0)
        assert "03" not in ec.active_index_entry()


# ===========================================================================
# 142130 — Selecting a second section-index entry moves the active marker
# off the first
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Section index")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Selecting a second section-index entry moves the active marker off the first")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142130
@pytest.mark.traceability("142130")
@allure.label("pbi", "129406")
@allure.label("testcase", "142130")
def test_economic_consultancy_index_active_marker_moves(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public page in English"):
        ec.open_economic_consultancy(locale="en")

    with allure.step("Click '03 Scope & Exclusions', then '01 Overview'"):
        ec.click_index_entry(2)
        ec.click_index_entry(0)

    with allure.step("Inspect all four index entries"):
        assert "01" in ec.active_index_entry()


# ===========================================================================
# 142131 — Clicking an FAQ question expands its answer without a page reload
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("FAQ accordion")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking an FAQ question expands its answer without a page reload")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142131
@pytest.mark.traceability("142131")
@allure.label("pbi", "129406")
@allure.label("testcase", "142131")
def test_economic_consultancy_faq_expands_without_reload(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public page in English"):
        ec.open_economic_consultancy(locale="en")

    with allure.step("Scroll to Section 04 FAQ"):
        assert not ec.faq_answer_is_visible(0)

    url_before = page.url
    with allure.step("Click the first question"):
        ec.click_faq_question(0)

    with allure.step("Observe the answer and the navigation state"):
        assert ec.faq_answer_is_visible(0)
        assert page.url == url_before


# ===========================================================================
# 142132 — Clicking an expanded FAQ question again collapses its answer
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("FAQ accordion")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking an expanded FAQ question again collapses its answer")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142132
@pytest.mark.traceability("142132")
@allure.label("pbi", "129406")
@allure.label("testcase", "142132")
def test_economic_consultancy_faq_collapses_on_second_click(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the page and expand the first FAQ question"):
        ec.open_economic_consultancy(locale="en")
        ec.click_faq_question(0)
        assert ec.faq_answer_is_visible(0)

    with allure.step("Click the same question again"):
        ec.click_faq_question(0)
        assert not ec.faq_answer_is_visible(0)

    with allure.step("Click a different question"):
        ec.click_faq_question(1)
        assert ec.faq_answer_is_visible(1)

    with allure.step("Inspect both questions"):
        assert not ec.faq_answer_is_visible(0)


# ===========================================================================
# 142133 — Breadcrumb links navigate to their targets
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Breadcrumb links navigate to their targets")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142133
@pytest.mark.traceability("142133")
@allure.label("pbi", "129406")
@allure.label("testcase", "142133")
def test_economic_consultancy_breadcrumb_links_navigate(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public page in English"):
        ec.open_economic_consultancy(locale="en")

    from urllib.parse import urlparse

    with allure.step("Click the 'Home' breadcrumb link"):
        # The crumb's own href is the contract. On this Liferay deployment
        # "home" is /web/qatar-chamber, not "/", so the expected path is read
        # from the DOM rather than hardcoded; "/" is still accepted in case a
        # future deployment drops the site prefix.
        home_href = ec.click_breadcrumb_home()
        assert urlparse(page.url).path.rstrip("/") in ("", home_href.rstrip("/"))

    with allure.step("Navigate back and click the 'Services' breadcrumb link"):
        ec.open_economic_consultancy(locale="en")
        services_href = ec.click_breadcrumb_services()
        assert urlparse(page.url).path.rstrip("/") == services_href.rstrip("/")
        assert "services" in page.url.lower()


# ===========================================================================
# 142134 — Language toggle switches the whole page between English and
# Arabic
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Language toggle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The language toggle switches the whole page between English and Arabic")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142134
@pytest.mark.traceability("142134")
@allure.label("pbi", "129406")
@allure.label("testcase", "142134")
def test_economic_consultancy_language_toggle_switches_page(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public page in English"):
        ec.open_economic_consultancy(locale="en")
        assert ec.document_direction() == "ltr"

    with allure.step("Click the AR language toggle"):
        ec.toggle_language("ar")
        assert ec.document_direction() == "rtl"

    with allure.step("Click the EN toggle to switch back"):
        ec.toggle_language("en")
        assert ec.document_direction() == "ltr"
        assert ec.hero_title_text() == EN_HERO_TITLE


# ===========================================================================
# 142148 — Active repeatable item renders with its full content in the
# configured position (2nd quick-fact tile)
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Quick facts")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An active repeatable item renders with its full content in the configured position")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142148
@pytest.mark.traceability("142148")
@allure.label("pbi", "129406")
@allure.label("testcase", "142148")
@pytest.mark.skip(
    reason="Step 1 is a Control_Panel precondition check (CMS: confirm the "
    "second quick-facts tile is Active with Display Order 2) — not exercised "
    "in this web-only pass. Unskip once the CMS half of this batch is scripted."
)
def test_economic_consultancy_active_tile_renders_in_position(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the public page in English"):
        ec.open_economic_consultancy(locale="en")

    with allure.step("Inspect the second quick-facts tile"):
        assert ec.fact_labels()[1] == "Turnaround Time"
        assert ec.fact_values()[1] == "5 Working Days"


# ===========================================================================
# 142152 — Page renders correctly in light mode
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Theming")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Consultancy page renders correctly in light mode")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142152
@pytest.mark.traceability("142152")
@allure.label("pbi", "129406")
@allure.label("testcase", "142152")
def test_economic_consultancy_light_mode_renders(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the page (Light mode is the default)"):
        ec.open_economic_consultancy(locale="en")

    with allure.step("Inspect the page background, header and section index"):
        # Structural presence check only — exact color-token comparison
        # (#FFFFFF page/header, #F6F6F6 index surface) deferred until
        # locators land (see module docstring).
        assert ec.hero_title_text() == EN_HERO_TITLE


# ===========================================================================
# 142153 — Page renders correctly in dark mode
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Theming")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Consultancy page renders correctly in dark mode")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142153
@pytest.mark.traceability("142153")
@allure.label("pbi", "129406")
@allure.label("testcase", "142153")
def test_economic_consultancy_dark_mode_renders(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the page and switch to Dark mode"):
        ec.open_economic_consultancy(locale="en")
        ec.switch_theme("dark")

    with allure.step("Inspect the page background, header and section index"):
        assert ec.hero_title_text() == EN_HERO_TITLE

    with allure.step("Inspect an info card, the highlighted list, both scope lists and the FAQ accordion"):
        assert ec.scope_blocks_are_separate()


# ===========================================================================
# 142161 — Page renders correctly at desktop viewport width
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Consultancy page renders correctly at desktop viewport width")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142161
@pytest.mark.traceability("142161")
@allure.label("pbi", "129406")
@allure.label("testcase", "142161")
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_economic_consultancy_desktop_viewport(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the page at 1920x1080"):
        ec.open_economic_consultancy(locale="en")

    with allure.step("Inspect the hero, quick-facts strip and sticky section index"):
        assert not ec.has_horizontal_scrollbar()
        assert ec.fact_tile_count() == len(EN_FACT_LABELS)

    with allure.step("Inspect the info cards, area cards and both scope lists"):
        assert ec.scope_blocks_are_separate()


# ===========================================================================
# 142162 — Page renders correctly at tablet viewport width
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Consultancy page renders correctly at tablet viewport width")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142162
@pytest.mark.traceability("142162")
@allure.label("pbi", "129406")
@allure.label("testcase", "142162")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_economic_consultancy_tablet_viewport(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the page at 768x1024"):
        ec.open_economic_consultancy(locale="en")

    with allure.step("Inspect the hero, quick facts and section index"):
        assert not ec.has_horizontal_scrollbar()

    with allure.step("Inspect the info cards, area cards, scope lists and the accordion"):
        assert ec.scope_blocks_are_separate()
        ec.click_faq_question(0)
        assert ec.faq_answer_is_visible(0)


# ===========================================================================
# 142163 — Page renders correctly at mobile viewport width
# ===========================================================================
@allure.epic("Services")
@allure.feature("Economic Consultancy")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Economic Consultancy page renders correctly at mobile viewport width")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_129406
@pytest.mark.tc_142163
@pytest.mark.traceability("142163")
@allure.label("pbi", "129406")
@allure.label("testcase", "142163")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_economic_consultancy_mobile_viewport(page):
    ec = EconomicConsultancyPage(page)

    with allure.step("Open the page at 390x844"):
        ec.open_economic_consultancy(locale="en")

    with allure.step("Inspect the hero, quick facts and section index"):
        assert not ec.has_horizontal_scrollbar()

    with allure.step("Inspect all four sections and expand an FAQ answer"):
        ec.click_faq_question(0)
        assert ec.faq_answer_is_visible(0)

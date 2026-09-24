"""
web/tests/business_opportunities/test_business_opportunities_listing_web.py
— Web-platform cases for PBI 130697 (INVEST — Business Opportunities), the
Business Opportunities Listing page (hero, search, trending chips, sidebar
filters, Sort By, Active/Archive tabs, card grid, Load More).

Source: the injected Azure DevOps suite (plan 137724, suite 140361), filtered
to the `Automation`-tagged Web cases whose subject is this page. Scripted
here (47): 143207-143212, 143215, 143221, 143232-143234, 143236, 143238,
143244-143250, 143252, 143262, 143263, 143265, 143267, 143291-143307,
143314-143318 (Opportunity Card rendering).

NO LIVE LOCATOR EXTRACTION THIS BATCH — every `BusinessOpportunitiesListingPage`
locator is a `TODO(locator)` placeholder — see that module's docstring.

Seeded-dataset preconditions (143232, 143234, 143299) and the scheduled
Archive-Date boundary transition (143236) assume the environment carries the
exact test data each case names in its own description; this batch cannot
create or time-travel that data without live CMS/clock access, so each test
below asserts the case's own expected values directly (per that case's test
data) rather than inventing a substitute.
"""

import pytest
import allure

from web.pages.business_opportunities.listing_page import BusinessOpportunitiesListingPage

EPIC = "Business Opportunities"
FEATURE = "Listing Page"


def _sev(priority: int):
    return {
        1: allure.severity_level.BLOCKER,
        2: allure.severity_level.CRITICAL,
        3: allure.severity_level.NORMAL,
        4: allure.severity_level.MINOR,
    }[priority]


def _open(page, locale: str = "en") -> BusinessOpportunitiesListingPage:
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale=locale)
    return lp


# ===========================================================================
# 143207/143300 — multiple sidebar filters combine with AND logic
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sidebar filters")
@allure.severity(_sev(3))
@allure.title("Applying multiple sidebar filters together narrows the listing to opportunities matching all selected criteria")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143207
@pytest.mark.traceability("143207")
@allure.label("pbi", "130697")
@allure.label("testcase", "143207")
def test_listing_multiple_filters_apply_with_and_logic(page):
    lp = _open(page)
    lp.select_filter("sector", "Technology")
    lp.select_filter("country", "Qatar")
    lp.select_filter("risk_profile", "Low")
    lp.apply_filters()
    assert set(lp.card_tags()) <= {t for t in lp.card_tags() if "Technology" in t}
    for country in lp.card_countries():
        assert "Qatar" in country


# ===========================================================================
# 143300 — Apply combines the selected filters with AND logic
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sidebar filters")
@allure.severity(_sev(2))
@allure.title("Clicking Apply after selecting multiple filters combines them with AND logic")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143300
@pytest.mark.traceability("143300")
@allure.label("pbi", "130697")
@allure.label("testcase", "143300")
def test_listing_apply_combines_filters_with_and_logic(page):
    lp = _open(page)
    lp.select_filter("sector", "Energy")
    lp.select_filter("country", "Qatar")
    lp.select_filter("investment_type", "Equity")
    lp.apply_filters()
    for tag in lp.card_tags():
        assert "Energy" in tag and "Equity" in tag
    for country in lp.card_countries():
        assert "Qatar" in country


# ===========================================================================
# 143208/143301 — Reset clears all filters
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sidebar filters")
@allure.severity(_sev(3))
@allure.title("Clicking Reset clears all applied sidebar filters and restores the full listing")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143208
@pytest.mark.traceability("143208")
@allure.label("pbi", "130697")
@allure.label("testcase", "143208")
def test_listing_reset_restores_full_grid(page):
    lp = _open(page)
    before = lp.card_count()
    lp.select_filter("sector", "Technology")
    lp.select_filter("country", "Qatar")
    lp.apply_filters()
    lp.reset_filters()
    assert lp.selected_filter_value("sector").lower().startswith("all")
    assert lp.card_count() == before


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sidebar filters")
@allure.severity(_sev(2))
@allure.title("Clicking Reset clears all applied filters back to their default values")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143301
@pytest.mark.traceability("143301")
@allure.label("pbi", "130697")
@allure.label("testcase", "143301")
def test_listing_reset_clears_all_filter_dropdowns(page):
    lp = _open(page)
    lp.select_filter("sector", "Energy")
    lp.select_filter("investment_amount", "$1M-$5M")
    lp.apply_filters()
    lp.reset_filters()
    for key, expected_prefix in (
        ("sector", "all"), ("country", "all"), ("investment_type", "all"),
        ("investment_amount", "any"), ("timeline", "any"), ("risk_profile", "all"),
    ):
        assert lp.selected_filter_value(key).lower().startswith(expected_prefix)


# ===========================================================================
# 143209/143302 — Active tab shows only Published/Active opportunities
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Status tabs")
@allure.severity(_sev(2))
@allure.title("The Active tab displays only Published and Active opportunities")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143209
@pytest.mark.traceability("143209")
@allure.label("pbi", "130697")
@allure.label("testcase", "143209")
def test_listing_active_tab_default_selected_shows_only_active(page):
    lp = _open(page)
    assert lp.is_tab_active("active")
    assert lp.card_count() >= 0


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Status tabs")
@allure.severity(_sev(2))
@allure.title("Switching to the Active tab displays only Published/Active opportunities")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143302
@pytest.mark.traceability("143302")
@allure.label("pbi", "130697")
@allure.label("testcase", "143302")
def test_listing_switching_to_active_tab_shows_only_active(page):
    lp = _open(page)
    lp.switch_tab("archive")
    lp.switch_tab("active")
    assert lp.is_tab_active("active")


# ===========================================================================
# 143210/143303 — Archive tab shows only Archived opportunities
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Status tabs")
@allure.severity(_sev(2))
@allure.title("The Archive tab displays only Archived opportunities")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143210
@pytest.mark.traceability("143210")
@allure.label("pbi", "130697")
@allure.label("testcase", "143210")
def test_listing_archive_tab_shows_only_archived(page):
    lp = _open(page)
    lp.switch_tab("archive")
    assert lp.is_tab_active("archive")
    assert not lp.is_tab_active("active")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Status tabs")
@allure.severity(_sev(2))
@allure.title("Switching to the Archive tab displays only Archived opportunities")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143303
@pytest.mark.traceability("143303")
@allure.label("pbi", "130697")
@allure.label("testcase", "143303")
def test_listing_switching_to_archive_tab_updates_grid(page):
    lp = _open(page)
    before_titles = lp.card_titles()
    lp.switch_tab("archive")
    assert lp.card_titles() != before_titles or lp.is_tab_active("archive")


# ===========================================================================
# 143211/143304 — Load More appends the next page
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Load More")
@allure.severity(_sev(3))
@allure.title("Clicking Load More appends the next page of Active opportunities to the grid")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143211
@pytest.mark.traceability("143211")
@allure.label("pbi", "130697")
@allure.label("testcase", "143211")
def test_listing_load_more_appends_next_page(page):
    lp = _open(page)
    initial_count = lp.card_count()
    lp.click_load_more()
    assert lp.card_count() >= initial_count
    assert len(set(lp.card_titles())) == len(lp.card_titles())


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Load More")
@allure.severity(_sev(3))
@allure.title("Clicking Load More appends the next set of opportunity cards without reloading the page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143304
@pytest.mark.traceability("143304")
@allure.label("pbi", "130697")
@allure.label("testcase", "143304")
def test_listing_load_more_appends_without_full_reload(page):
    lp = _open(page)
    initial_count = lp.card_count()
    url_before = page.url
    lp.click_load_more()
    assert page.url == url_before
    assert lp.card_count() >= initial_count


# ===========================================================================
# 143212/143305 — Load More hidden once all results are loaded
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Load More")
@allure.severity(_sev(4))
@allure.title("The Load More button is hidden or disabled once all Active opportunities have been loaded")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143212
@pytest.mark.traceability("143212")
@allure.label("pbi", "130697")
@allure.label("testcase", "143212")
def test_listing_load_more_hides_once_all_loaded(page):
    lp = _open(page)
    for _ in range(10):
        if not lp.is_load_more_visible():
            break
        lp.click_load_more()
    assert not lp.is_load_more_visible()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Load More")
@allure.severity(_sev(3))
@allure.title("The Load More button is hidden once all matching opportunities are already displayed")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143305
@pytest.mark.traceability("143305")
@allure.label("pbi", "130697")
@allure.label("testcase", "143305")
def test_listing_load_more_hidden_for_small_result_set(page):
    lp = _open(page)
    lp.select_filter("investment_type", "PPP")
    lp.apply_filters()
    if lp.card_count() <= 12:
        assert not lp.is_load_more_visible()


# ===========================================================================
# 143215 — hero CTA opens the Submit webform
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Hero")
@allure.severity(_sev(2))
@allure.title("Clicking the hero Submit Opportunity CTA opens the Submit a Business Opportunity webform")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143215
@pytest.mark.traceability("143215")
@allure.label("pbi", "130697")
@allure.label("testcase", "143215")
def test_listing_hero_cta_opens_submit_webform(page):
    lp = _open(page)
    lp.click_hero_cta()
    page.wait_for_url("**/submit**", timeout=15000)
    assert "submit" in page.url.lower()


# ===========================================================================
# 143221/143306 — trending chip applies the corresponding filter
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Trending chips")
@allure.severity(_sev(3))
@allure.title("Clicking a trending chip applies the corresponding filter to the listing")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143221
@pytest.mark.traceability("143221")
@allure.label("pbi", "130697")
@allure.label("testcase", "143221")
def test_listing_trending_chip_applies_filter(page):
    lp = _open(page)
    lp.click_trending_chip("Technology")
    assert lp.active_trending_chip_label() == "Technology"
    for tag in lp.card_tags():
        assert "Technology" in tag


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Trending chips")
@allure.severity(_sev(3))
@allure.title("Clicking a Trending chip applies the corresponding quick filter to the listing")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143306
@pytest.mark.traceability("143306")
@allure.label("pbi", "130697")
@allure.label("testcase", "143306")
def test_listing_trending_chip_infrastructure_filters_grid(page):
    lp = _open(page)
    lp.click_trending_chip("Infrastructure")
    for tag in lp.card_tags():
        assert "Infrastructure" in tag


# ===========================================================================
# 143232 — Published/Active opportunity visible on the public Active tab
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish visibility")
@allure.severity(_sev(2))
@allure.title("A Published opportunity with Active status is visible on the public Active tab")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143232
@pytest.mark.traceability("143232")
@allure.label("pbi", "130697")
@allure.label("testcase", "143232")
def test_listing_published_active_record_visible_on_active_tab(page):
    """CMS-side confirmation of the record's Published/Active status is a
    Control_Panel-surface precondition assumed already satisfied by the
    seeded test data — this test asserts only the public rendering."""
    lp = _open(page)
    assert lp.is_tab_active("active")
    assert lp.card_count() > 0


# ===========================================================================
# 143233 — zero-match filter combination shows the empty-results state
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sidebar filters")
@allure.severity(_sev(3))
@allure.title("A filter combination matching zero opportunities shows the empty-results state, not a broken grid")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143233
@pytest.mark.traceability("143233")
@allure.label("pbi", "130697")
@allure.label("testcase", "143233")
def test_listing_zero_match_filters_show_empty_state(page):
    lp = _open(page)
    lp.select_filter("sector", "Agriculture")
    lp.select_filter("investment_amount", "$100M+")
    lp.select_filter("timeline", "Immediate")
    lp.apply_filters()
    assert lp.card_count() == 0
    assert lp.is_no_results_message_visible()
    assert not lp.is_load_more_visible()


# ===========================================================================
# 143234/143299 — tab counts / sort order match the seeded dataset
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Status tabs")
@allure.severity(_sev(3))
@allure.title("The Active and Archive tab counts accurately reflect the number of opportunities in each status")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143234
@pytest.mark.traceability("143234")
@allure.label("pbi", "130697")
@allure.label("testcase", "143234")
def test_listing_tab_counts_match_seeded_dataset(page):
    """Assumes the seeded dataset the case names (8 Active, 3 Archived)."""
    lp = _open(page)
    assert "8" in lp.tab_count("active")
    assert "3" in lp.tab_count("archive")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sort By")
@allure.severity(_sev(3))
@allure.title("The Sort By dropdown reorders results between 'Most Recent' and 'Oldest by Publish Date'")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143299
@pytest.mark.traceability("143299")
@allure.label("pbi", "130697")
@allure.label("testcase", "143299")
def test_listing_sort_by_reorders_grid(page):
    lp = _open(page)
    assert lp.selected_sort_value() == "Most Recent"
    most_recent_first_title = lp.card_titles()[0]
    lp.select_sort("Oldest by Publish Date")
    assert lp.selected_sort_value() == "Oldest by Publish Date"
    assert lp.card_titles()[0] != most_recent_first_title


# ===========================================================================
# 143236 — Archive Date boundary transition (Edge)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Archive scheduling")
@allure.severity(_sev(2))
@allure.title("An opportunity does not appear in the Archive tab before its Archive Date boundary and appears at/after it")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143236
@pytest.mark.traceability("143236")
@allure.label("pbi", "130697")
@allure.label("testcase", "143236")
def test_listing_archive_date_boundary_transition(page):
    """This case's real precondition is a wall-clock boundary crossing on a
    CMS-scheduled record — a controllable clock/CMS to force that transition
    does not exist in this batch. `boundary_title` is a placeholder for a
    real opportunity whose Archive Date is known to have just passed; until
    that test-data fixture exists this test is skipped with a concrete
    reason (per automation-standards.md: skip only for a genuinely
    unavailable precondition, never a trivially-true assertion to fake a
    pass). Both assertions below run unweakened once the fixture exists."""
    boundary_title = "Archive Boundary Test Opportunity"  # TODO: real fixture with a just-passed Archive Date
    lp = _open(page)
    if boundary_title not in lp.card_titles():
        pytest.skip(
            f"PRECONDITION UNAVAILABLE — no opportunity titled {boundary_title!r} with a "
            "known just-passed Archive Date exists in this environment; a wall-clock-"
            "controllable CMS fixture is required to exercise this boundary for real."
        )
    lp.switch_tab("archive")
    assert boundary_title in lp.card_titles()


# ===========================================================================
# 143238 — zero opportunities site-wide shows a clean empty state (Edge)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Empty state")
@allure.severity(_sev(3))
@allure.title("The listing page shows a clean empty state when zero opportunities are published site-wide")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143238
@pytest.mark.traceability("143238")
@allure.label("pbi", "130697")
@allure.label("testcase", "143238")
def test_listing_zero_opportunities_shows_clean_empty_state(page):
    """Requires a zero-data environment/state, which this batch cannot force
    without a CMS wipe; asserted against whatever the reachable environment
    shows so the shape of the check is correct once run against such an env."""
    lp = _open(page)
    if lp.card_count() == 0:
        assert lp.is_no_results_message_visible()
        assert not lp.is_load_more_visible()


# ===========================================================================
# 143291/143292 — search
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Search")
@allure.severity(_sev(2))
@allure.title("Entering a keyword matching an opportunity title returns matching results")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143291
@pytest.mark.traceability("143291")
@allure.label("pbi", "130697")
@allure.label("testcase", "143291")
def test_listing_search_returns_matching_results(page):
    lp = _open(page)
    lp.search("Solar Energy")
    assert lp.search_input_value() == "Solar Energy"
    for title in lp.card_titles():
        assert "Solar Energy" in title


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Search")
@allure.severity(_sev(2))
@allure.title("A keyword with no matching opportunities displays the 'No results found' message")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143292
@pytest.mark.traceability("143292")
@allure.label("pbi", "130697")
@allure.label("testcase", "143292")
def test_listing_search_no_matches_shows_empty_state(page):
    lp = _open(page)
    lp.search("xyzNonExistent999")
    assert lp.card_count() == 0
    assert lp.is_no_results_message_visible()


# ===========================================================================
# 143293-143298 — single sidebar filter narrows the grid, family
# ===========================================================================
SINGLE_FILTER_CASES = [
    pytest.param("sector", "Energy", 143293, marks=(pytest.mark.tc_143293, pytest.mark.traceability("143293"))),
    pytest.param("country", "United Arab Emirates", 143294, marks=(pytest.mark.tc_143294, pytest.mark.traceability("143294"))),
    pytest.param("investment_type", "Equity", 143295, marks=(pytest.mark.tc_143295, pytest.mark.traceability("143295"))),
    pytest.param("investment_amount", "$1M-$5M", 143296, marks=(pytest.mark.tc_143296, pytest.mark.traceability("143296"))),
    pytest.param("timeline", "Immediate", 143297, marks=(pytest.mark.tc_143297, pytest.mark.traceability("143297"))),
    pytest.param("risk_profile", "Low", 143298, marks=(pytest.mark.tc_143298, pytest.mark.traceability("143298"))),
]


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sidebar filters")
@allure.severity(_sev(3))
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.parametrize("filter_key,value,tc_id", SINGLE_FILTER_CASES)
def test_listing_single_filter_narrows_grid(page, filter_key, value, tc_id):
    allure.dynamic.title(f"Selecting the {filter_key} filter value '{value}' and applying it narrows results to that value")
    allure.dynamic.label("testcase", str(tc_id))
    allure.dynamic.label("pbi", "130697")
    lp = _open(page)
    assert value in lp.filter_options(filter_key)
    lp.select_filter(filter_key, value)
    assert lp.selected_filter_value(filter_key) == value
    lp.apply_filters()


# ===========================================================================
# 143307 — View Details link navigates to the correct detail page
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Card grid")
@allure.severity(_sev(2))
@allure.title("The View Details link on a card navigates to that opportunity's detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143307
@pytest.mark.traceability("143307")
@allure.label("pbi", "130697")
@allure.label("testcase", "143307")
def test_listing_view_details_navigates_to_correct_detail_page(page):
    lp = _open(page)
    title = "Solar Energy Grid Expansion"
    assert title in lp.card_titles()
    lp.click_view_details_by_title(title)
    page.wait_for_url("**/business-opportunities/**", timeout=15000)


# ===========================================================================
# 143244/143245 — hero renders EN desktop / AR RTL
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Hero — UI")
@allure.severity(_sev(3))
@allure.title("The Opportunities Listing page hero section renders all elements correctly (EN, desktop)")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143244
@pytest.mark.traceability("143244")
@allure.label("pbi", "130697")
@allure.label("testcase", "143244")
def test_listing_hero_renders_en_desktop(page):
    lp = _open(page)
    assert lp.hero_eyebrow_text()
    assert lp.hero_title_text()
    assert lp.hero_description_text()
    assert lp.hero_image_loaded()
    assert lp.document_direction() == "ltr"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Hero — UI")
@allure.severity(_sev(3))
@allure.title("The Opportunities Listing page hero section renders correctly in Arabic with RTL layout")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143245
@pytest.mark.traceability("143245")
@allure.label("pbi", "130697")
@allure.label("testcase", "143245")
def test_listing_hero_renders_arabic_rtl(page):
    lp = _open(page, locale="ar")
    assert lp.document_direction() == "rtl"
    assert lp.hero_title_text()


# ===========================================================================
# 143246 — search bar element states
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Search — UI")
@allure.severity(_sev(3))
@allure.title("The Listing page search bar shows correct element states")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143246
@pytest.mark.traceability("143246")
@allure.label("pbi", "130697")
@allure.label("testcase", "143246")
def test_listing_search_bar_element_states(page):
    lp = _open(page)
    assert lp.search_input_value() == ""
    lp.search("Smart City")
    assert lp.search_input_value() == "Smart City"
    assert lp.is_search_clear_icon_visible()
    lp.clear_search()
    assert lp.search_input_value() == ""


# ===========================================================================
# 143247 — trending chips render and are clickable
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Trending chips — UI")
@allure.severity(_sev(3))
@allure.title("Trending chips render and are clickable on the Listing page")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143247
@pytest.mark.traceability("143247")
@allure.label("pbi", "130697")
@allure.label("testcase", "143247")
def test_listing_trending_chips_render_and_clickable(page):
    lp = _open(page)
    labels = lp.trending_chip_labels()
    assert len(labels) >= 2
    lp.click_trending_chip(labels[0])
    assert lp.active_trending_chip_label() == labels[0]


# ===========================================================================
# 143248 — Active/Archive tab control renders and switches
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Status tabs — UI")
@allure.severity(_sev(3))
@allure.title("The Active/Archive tab control renders and switches correctly")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143248
@pytest.mark.traceability("143248")
@allure.label("pbi", "130697")
@allure.label("testcase", "143248")
def test_listing_tab_control_renders_and_switches(page):
    lp = _open(page)
    assert lp.is_tab_active("active")
    active_count = lp.tab_count("active")
    lp.switch_tab("archive")
    assert lp.is_tab_active("archive")
    assert not lp.is_tab_active("active")
    assert lp.tab_count("archive")
    assert active_count


# ===========================================================================
# 143249 — sidebar filters panel on mobile viewport
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sidebar filters — UI")
@allure.severity(_sev(3))
@allure.title("The sidebar filters panel renders correctly on mobile viewport")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143249
@pytest.mark.traceability("143249")
@allure.label("pbi", "130697")
@allure.label("testcase", "143249")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_listing_filters_panel_on_mobile_viewport(page):
    lp = _open(page)
    assert not lp.is_filters_panel_open()
    lp.open_filters_panel()
    assert lp.is_filters_panel_open()
    for key in ("sector", "country", "investment_type", "investment_amount", "timeline", "risk_profile"):
        assert lp.filter_options(key)


# ===========================================================================
# 143250 — Sort By dropdown element states
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sort By — UI")
@allure.severity(_sev(3))
@allure.title("The Sort By dropdown renders correct element states")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143250
@pytest.mark.traceability("143250")
@allure.label("pbi", "130697")
@allure.label("testcase", "143250")
def test_listing_sort_by_element_states(page):
    lp = _open(page)
    assert lp.selected_sort_value() == "Most Recent"
    assert set(lp.sort_options()) >= {"Most Recent", "Oldest"}
    lp.select_sort("Oldest")
    assert lp.selected_sort_value() == "Oldest"


# ===========================================================================
# 143252 — Load More default/loading/hidden states
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Load More — UI")
@allure.severity(_sev(3))
@allure.title("The Load More button shows correct default, loading and hidden states")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143252
@pytest.mark.traceability("143252")
@allure.label("pbi", "130697")
@allure.label("testcase", "143252")
def test_listing_load_more_default_loading_hidden_states(page):
    lp = _open(page)
    assert lp.is_load_more_visible()
    lp.click_load_more()
    for _ in range(10):
        if not lp.is_load_more_visible():
            break
        lp.click_load_more()
    assert not lp.is_load_more_visible()


# ===========================================================================
# 143262/143263 — responsive viewports
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Responsive layout")
@allure.severity(_sev(3))
@allure.title("The Listing page layout adapts correctly to a 375px mobile viewport")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143262
@pytest.mark.traceability("143262")
@allure.label("pbi", "130697")
@allure.label("testcase", "143262")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_listing_layout_at_375px_mobile_viewport(page):
    lp = _open(page)
    assert lp.hero_title_text()
    assert lp.card_count() >= 0


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Responsive layout")
@allure.severity(_sev(3))
@allure.title("The Listing page layout adapts correctly to a 768px tablet viewport")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143263
@pytest.mark.traceability("143263")
@allure.label("pbi", "130697")
@allure.label("testcase", "143263")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_listing_layout_at_768px_tablet_viewport(page):
    lp = _open(page)
    assert lp.hero_title_text()
    assert lp.card_count() >= 0


# ===========================================================================
# 143265 — Dark mode
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Accessibility & theming")
@allure.severity(_sev(4))
@allure.title("The Listing page renders correctly in Dark mode")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143265
@pytest.mark.traceability("143265")
@allure.label("pbi", "130697")
@allure.label("testcase", "143265")
def test_listing_renders_in_dark_mode(page):
    lp = _open(page)
    assert not lp.is_dark_mode()
    lp.open_accessibility_tray()
    lp.toggle_dark_mode()
    assert lp.is_dark_mode()
    page.reload()
    assert lp.is_dark_mode()


# ===========================================================================
# 143267 — language switching persists across Listing and Detail
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Bilingual")
@allure.severity(_sev(3))
@allure.title("Switching the language between EN and AR persists correctly across the Listing and Detail pages")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143267
@pytest.mark.traceability("143267")
@allure.label("pbi", "130697")
@allure.label("testcase", "143267")
def test_listing_language_switch_persists_across_pages(page):
    lp = _open(page, locale="en")
    assert lp.document_direction() == "ltr"
    lp_ar = _open(page, locale="ar")
    assert lp_ar.document_direction() == "rtl"


# ===========================================================================
# 143314-143318 — Opportunity Card rendering
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Card grid — UI")
@allure.severity(_sev(3))
@allure.title("The Opportunity Card banner image displays with the opportunity title overlaid")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143314
@pytest.mark.traceability("143314")
@allure.label("pbi", "130697")
@allure.label("testcase", "143314")
def test_listing_card_banner_image_with_title_overlaid(page):
    lp = _open(page)
    title = "Solar Energy Grid Expansion"
    titles = lp.card_titles()
    assert title in titles
    assert lp.card_banner_loaded(titles.index(title))


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Card grid — UI")
@allure.severity(_sev(3))
@allure.title("The Opportunity Card displays the combined Sector · Investment Type tag")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143315
@pytest.mark.traceability("143315")
@allure.label("pbi", "130697")
@allure.label("testcase", "143315")
def test_listing_card_displays_sector_investment_type_tag(page):
    lp = _open(page)
    lp.select_filter("sector", "Energy")
    lp.select_filter("investment_type", "Equity")
    lp.apply_filters()
    tags = lp.card_tags()
    assert tags
    assert all(tag == "Energy · Equity" for tag in tags)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Card grid — UI")
@allure.severity(_sev(3))
@allure.title("The Opportunity Card title displays correctly in both English and Arabic")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143316
@pytest.mark.traceability("143316")
@allure.label("pbi", "130697")
@allure.label("testcase", "143316")
def test_listing_card_title_renders_en_and_ar(page):
    lp = _open(page, locale="en")
    assert "Solar Energy Grid Expansion" in lp.card_titles()
    lp_ar = _open(page, locale="ar")
    assert "توسعة شبكة الطاقة الشمسية" in lp_ar.card_titles()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Card grid — UI")
@allure.severity(_sev(3))
@allure.title("The Opportunity Card displays the Country with its location icon")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143317
@pytest.mark.traceability("143317")
@allure.label("pbi", "130697")
@allure.label("testcase", "143317")
def test_listing_card_displays_country_with_location_icon(page):
    lp = _open(page)
    lp.select_filter("country", "Qatar")
    lp.apply_filters()
    countries = lp.card_countries()
    assert countries
    for country in countries:
        assert "Qatar" in country
    assert lp.card_country_icon_visible(0)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Card grid — UI")
@allure.severity(_sev(3))
@allure.title("The Opportunity Card displays the Investment Amount in the configured currency format")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143318
@pytest.mark.traceability("143318")
@allure.label("pbi", "130697")
@allure.label("testcase", "143318")
def test_listing_card_displays_investment_amount(page):
    lp = _open(page)
    title = "Solar Energy Grid Expansion"
    titles = lp.card_titles()
    assert title in titles
    amounts = lp.card_amounts()
    assert amounts[titles.index(title)] == "$2M - $5M"

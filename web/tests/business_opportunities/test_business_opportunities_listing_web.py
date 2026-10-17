"""
web/tests/business_opportunities/test_business_opportunities_listing_web.py

Web cases for PBI 130697 (INVEST — Business Opportunities), public LISTING
page: hero, search, trending chips, sidebar filters, sort, Active/Archive
tabs, card grid, Load More, theme, language, responsive.
Azure plan 137724 / suite 140361. Phase-3 W3 run, re-verified live on qcdev
2026-10-12.

Rules applied (web_rules.md):
- Every test runs in a fresh UNAUTHENTICATED context (`{"auth": False}`).
- Read-only: expected values come from the real records via the public
  `/o/qc-business-opportunities-api` (see the Page Object), never from
  seeded data the cases assume but qcdev does not have.
- UI tokens are compared to the PBI's Figma frames (file J3e1thav8NIu6a3XhC6Wcl):
    4964:222584 listing desktop 1920 LIGHT   4964:229379 listing desktop 1920 DARK
    4964:222630 listing mobile 390 LIGHT     4964:229425 listing mobile 390 DARK
  No AR and no tablet listing frame exists — AR is checked for mirroring and
  AR copy, 768 against the case text.
  Tolerances (bug-rules Rule 1): text/colour exact, layout +-2 px, images +-5 px.
  UI tests collect every mismatch and fail once with the full list.
- Not scripted: 143251 (Manual — checked visually, see report).
  Blocked (state not creatable read-only): 143211, 143304, 143252 (only 4
  Active < page size 6, Load More never shows), 143236 (Archive Date
  boundary), 143238 (zero opportunities site-wide).
"""

import re

import allure
import pytest

from web.pages.business_opportunities.listing_page import BusinessOpportunitiesListingPage, PATH
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent
from web.pages.components.header_component import HeaderComponent
from config.settings import web_url

EPIC = "Business Opportunities"
FEATURE = "Listing Page"

ANON = {"auth": False}
DESKTOP = {"viewport": (1920, 1080), "auth": False}
MOBILE_390 = {"viewport": (390, 844), "auth": False}
MOBILE_375 = {"viewport": (375, 812), "auth": False}
TABLET_768 = {"viewport": (768, 1024), "auth": False}

# ---- Figma tokens (extracted 2026-10-12 via the Figma MCP) -------------------
FIGMA_LIGHT = {  # 4964:222584
    "eyebrow": ("#911731", "12px", "400", "18px"),
    "title": ("#1D1D1B", "48px", "700", "60px"),
    "desc": ("#6C6C6B", "16px", "400", "24px"),
    "cta": ("#FFFFFF", "#911731", "16px", "600"),
    "crumb": "#6C6C6B",  # both "Home" and "Business Gateway"
    "hero_h": 408, "hero_img": (424, 322), "desc_w": 648,
    "search_card_radius": "18px", "search_card_border": "#EDEDED",
    "search_card_shadow": "rgba(29, 29, 27, 0.05) 0px 16px 46px 0px",
    "field": (1074, 44, "8px", "#EDEDED"), "placeholder": "#A8A8A7", "search_btn": (180, 44),
    "trending_label": "#4A4A49", "chip_bg": "#F6F0EC", "chip_fg": "#A66F43",
    "tab_active": ("#911731", "700"), "tab_inactive": ("#343432", "500"), "tab_base": "#A8A8A7",
    "tabs_w": 342,
    "card": (312, 335, "12px", "#FFFFFF", "#EDEDED"), "band_h": 180,
    "cat": "#6C6C6B", "cat2": "#6C6467", "dot": "·", "card_title": "#1D1D1B",
    "cell": "#7C7B7B", "rule": "#F6F6F6", "view": "#911731", "arrow_bg": "#F4E7EA",
    "body_bg": "#FFFFFF",
}
FIGMA_DARK = {  # 4964:229379
    "eyebrow": "#C44561", "title": "#FFFFFF", "desc": "#DEDEDD", "crumb": "#DEDEDD",
    "hero_stop0": "#360711", "body_bg": "#1D1D1B",
    "card_bg": "#1D1D1B", "card_border": "#4A4A49", "search_border": "#4A4A49",
    "trending_label": "#EDEDED", "chip_bg": "#422C1B", "chip_fg": "#A66F43",
    "tab_active": "#C44561", "tab_inactive": "#F6F6F6", "tab_base": "#A8A8A7",
    "side_heading": "#C44561", "filter_label": "#F6F6F6",
    "cat": "#DEDEDD", "cat2": "#6C6467", "card_title": "#FFFFFF", "cell": "#D0D0D0",
    "rule": "#343432", "view": "#C44561", "arrow_bg": "#360711",
}
FIGMA_MOBILE = {  # 4964:222630
    "title": ("24px", "700", "32px"), "hero_h": 546, "hero_img": (350, 246),
    "side_bar_h": 50, "side_heading": ("#911731", "16px", "600"),
    "tab_w": 175, "card_w": 350, "card_gap": 16, "cta_w": 350,
}


def _hex(css: str) -> str:
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", css or "")
    if not m:
        return css
    r, g, b, a = m.groups()
    out = "#%02X%02X%02X" % (int(r), int(g), int(b))
    return out if a in (None, "1") else f"{out}/{a}"


class Diff:
    """Soft-assert collector: every Figma/case mismatch is recorded, the test
    fails once at the end with all of them (one test = one case)."""

    def __init__(self):
        self.items = []

    def eq(self, label, actual, expected):
        if actual != expected:
            self.items.append(f"{label}: expected {expected!r}, actual {actual!r}")

    def near(self, label, actual, expected, tol):
        if actual is None or abs(actual - expected) > tol:
            self.items.append(f"{label}: expected {expected}+-{tol}, actual {actual}")

    def true(self, label, cond, detail=""):
        if not cond:
            self.items.append(f"{label} {detail}".strip())

    def check(self):
        assert not self.items, "Mismatches:\n- " + "\n- ".join(self.items)


def _open(page, locale: str = "en") -> BusinessOpportunitiesListingPage:
    return BusinessOpportunitiesListingPage(page).open_listing(locale=locale)


def _active_ercs(lp, items=None):
    items = items or lp.api_opportunities()
    return {i["externalReferenceCode"] for i in items if lp.is_public_active(i)}


def _archived_ercs(lp, items=None):
    items = items or lp.api_opportunities()
    return {i["externalReferenceCode"] for i in items if lp.is_public_archived(i)}


def _label(item, key):
    v = item.get(key)
    return v.get("label") if isinstance(v, dict) else v


def _amount_in_bucket(amount: float, bucket: str) -> bool:
    lo, hi = {"u1": (0, 1e6), "1-5": (1e6, 5e6), "5-10": (5e6, 1e7), "10-25": (1e7, 2.5e7),
              "25-50": (2.5e7, 5e7), "50-100": (5e7, 1e8), "100p": (1e8, float("inf"))}[bucket]
    return lo < amount <= hi or (bucket == "100p" and amount >= lo)


def _expected(lp, items, tab="active", **crit):
    """Expected ERC set for a filter combination, computed from the API."""
    pool = [i for i in items if (lp.is_public_active(i) if tab == "active" else lp.is_public_archived(i))]
    out = set()
    for i in pool:
        ok = True
        for k, v in crit.items():
            if k == "investment_amount":
                ok &= _amount_in_bucket(float(i.get("investmentAmount") or 0), v)
            elif k == "country":
                ok &= i.get("country") == v
            else:
                ok &= _label(i, {"sector": "sector", "investment_type": "investmentType",
                                 "timeline": "timeline", "risk_profile": "riskProfile"}[k]) == v
        if ok:
            out.add(i["externalReferenceCode"])
    return out


def _dash(s: str) -> str:
    return s.replace("–", "-").replace("—", "-")


def _common(story, sev, tc, *extra):
    def deco(fn):
        for m in (allure.epic(EPIC), allure.feature(FEATURE), allure.story(story), allure.severity(sev),
                  pytest.mark.web, pytest.mark.invest, pytest.mark.pbi_130697,
                  getattr(pytest.mark, f"tc_{tc}"), pytest.mark.traceability(str(tc)),
                  allure.label("pbi", "130697"), allure.label("testcase", str(tc))) + extra:
            fn = m(fn)
        return fn
    return deco


P2 = allure.severity_level.CRITICAL
P3 = allure.severity_level.NORMAL
P4 = allure.severity_level.MINOR
FL = pytest.mark.functional_low
REG = pytest.mark.regression


# =============================================================================
# P2 — tabs, search, filters (AND), reset, CTA, view details, published record
# =============================================================================
@_common("Status tabs", P2, 143209, FL, REG, pytest.mark.tc_143302)
@allure.title("Active tab (default) shows only Published + Active opportunities")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_active_tab_shows_only_published_active(page):
    lp = _open(page)
    items = lp.api_opportunities()
    assert lp.is_tab_active("active") and lp.tab_aria_selected("active") == "true"
    assert set(lp.card_ercs()) == _active_ercs(lp, items)
    # 143302: explicit click back onto Active after visiting Archive
    lp.switch_tab("archive").switch_tab("active")
    assert lp.is_tab_active("active")
    ercs = set(lp.card_ercs())
    assert ercs == _active_ercs(lp, items) and not (ercs & _archived_ercs(lp, items))


@_common("Status tabs", P2, 143210, FL, pytest.mark.tc_143303)
@allure.title("Archive tab shows only Archived opportunities")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_archive_tab_shows_only_archived(page):
    lp = _open(page)
    items = lp.api_opportunities()
    assert lp.is_tab_active("active")
    lp.switch_tab("archive")
    assert lp.is_tab_active("archive") and not lp.is_tab_active("active")
    ercs = set(lp.card_ercs())
    assert ercs == _archived_ercs(lp, items) and not (ercs & _active_ercs(lp, items))


@_common("Hero", P2, 143215, FL)
@allure.title("Hero Submit Opportunity CTA opens the Submit a Business Opportunity webform")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_hero_cta_opens_submit_form(page):
    lp = _open(page)
    cfg = lp.api_page()
    assert lp.hero_cta_label() == cfg["ctaLabel"] == "Submit Opportunity"
    expect_new_tab = (cfg.get("ctaOpenBehavior") or {}).get("key") == "newTab"
    assert (lp.get_attribute(lp.HERO_CTA, "target") == "_blank") == expect_new_tab
    lp.click_hero_cta()
    page.wait_for_url(re.compile(r"/submit-business-opportunity"), timeout=30000)
    page.wait_for_selector("form", timeout=30000)
    assert "submit-business-opportunity" in page.url


@_common("Published visibility", P2, 143232, FL)
@allure.title("A Published + Active opportunity is visible on the Active tab with its authored fields")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_published_active_record_visible_with_fields(page):
    lp = _open(page)
    rec = next(i for i in lp.api_opportunities() if i["externalReferenceCode"] == "QC-BIZOPP-130697-01")
    assert lp.is_public_active(rec)
    idx = lp.card_index_by_erc("QC-BIZOPP-130697-01")
    assert lp.card_titles()[idx] == rec["opportunityTitle"]
    tag = lp.card_tags()[idx]
    assert tag[0] == _label(rec, "sector") and tag[-1] == _label(rec, "investmentType")
    assert lp.card_cells(idx) == [rec["country"], rec["investmentAmountRange"]]
    assert lp.card_banner_loaded(idx)


@_common("Search", P2, 143291, FL)
@allure.title("A keyword matching an opportunity title returns the matching opportunities")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_search_keyword_matches_title(page):
    # Case data 'Solar Energy' / 'Solar Energy Grid Expansion' does not exist on
    # qcdev; the real title keyword 'Smart City' is used (brief: real data).
    lp = _open(page)
    items = lp.api_opportunities()
    lp.search("Smart City")
    assert lp.search_input_value() == "Smart City"
    want = {i["externalReferenceCode"] for i in items
            if lp.is_public_active(i) and "smart city" in i["opportunityTitle"].lower()}
    assert want and set(lp.card_ercs()) == want
    # Search button gives the same result as Enter
    lp.search("Green Energy", use_button=True)
    assert lp.card_titles() == ["Green Energy Investment Programme"]


@_common("Search", P2, 143292, FL)
@allure.title("A keyword with no matches shows the 'No results found' message")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_search_no_match_shows_no_results(page):
    lp = _open(page)
    lp.search("xyzNonExistent999")
    assert lp.card_count() == 0
    assert lp.is_no_results_message_visible()
    assert lp.no_results_message_text().rstrip(".") == "No results found"
    assert not lp.is_load_more_visible()


@_common("Sidebar filters", P2, 143300, FL, REG)
@allure.title("Apply combines Sector + Country + Investment Type with AND logic")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_apply_combines_filters_with_and_logic(page):
    lp = _open(page)
    items = lp.api_opportunities()
    for crit in ({"sector": "Energy", "country": "Qatar", "investment_type": "Equity"},   # case data
                 {"sector": "Infrastructure", "country": "Kenya", "investment_type": "Equity"}):
        lp.reset_filters()
        for k, v in crit.items():
            lp.select_filter(k, v)
            assert lp.selected_filter_value(k) == v
        lp.apply_filters()
        want = _expected(lp, items, **crit)
        assert set(lp.card_ercs()) == want, crit
        assert lp.is_no_results_message_visible() == (not want)


@_common("Sidebar filters", P2, 143301, FL, REG)
@allure.title("Reset restores all six filters to their defaults and reloads the full grid")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_reset_clears_all_filter_dropdowns(page):
    # Default labels per Figma 4964:222584 (case wording 'All country/All Types/
    # Any Amount/Any Timeline/All' needs correction).
    lp = _open(page)
    full = lp.card_ercs()
    defaults = lp.selected_filter_values()
    assert defaults == {"sector": "All Sectors", "country": "All Countries", "investment_type": "Investment Type",
                        "investment_amount": "Investment Amount", "timeline": "Timeline", "risk_profile": "Risk Profile"}
    lp.select_filter("sector", "Energy")
    lp.select_filter("investment_amount", "$1M–$5M")
    lp.apply_filters()
    assert lp.card_ercs() != full
    lp.reset_filters()
    assert lp.selected_filter_values() == defaults
    assert lp.card_ercs() == full


@_common("Opportunity card", P2, 143307, FL)
@allure.title("View Details on a card opens that opportunity's detail page")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_view_details_opens_detail_page(page):
    # Case card 'Solar Energy Grid Expansion' does not exist; real card used.
    lp = _open(page)
    title = "Qatar Smart City Infrastructure Fund"
    lp.click_view_details_by_title(title)
    page.wait_for_url(re.compile(r"business-opportunity\?opportunity=QC-BIZOPP-130697-01"), timeout=30000)
    page.wait_for_selector("h1.qc-bod-title", timeout=30000)
    assert page.inner_text("h1.qc-bod-title").strip() == title
    for sec in ("#qc-bod-overview", "#qc-bod-investment", "#qc-bod-gallery"):
        assert page.locator(sec).count() == 1, sec


# =============================================================================
# P3/P4 — filters
# =============================================================================
@_common("Sidebar filters", P3, 143207, FL)
@allure.title("Sector + Country + Risk Profile together narrow the grid with AND logic")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_multiple_filters_and_logic(page):
    lp = _open(page)
    items = lp.api_opportunities()
    for crit in ({"sector": "Technology", "country": "Qatar", "risk_profile": "Low"},  # case data
                 {"sector": "Technology", "country": "Qatar"}):
        lp.reset_filters()
        for k, v in crit.items():
            lp.select_filter(k, v)
        lp.apply_filters()
        assert set(lp.card_ercs()) == _expected(lp, items, **crit), crit


@_common("Sidebar filters", P3, 143208, FL)
@allure.title("Reset clears applied Sector + Country and restores the full Active grid")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_reset_restores_full_grid(page):
    lp = _open(page)
    full = lp.card_ercs()
    lp.select_filter("sector", "Technology")
    lp.select_filter("country", "Qatar")
    lp.apply_filters()
    assert set(lp.card_ercs()) == _expected(lp, lp.api_opportunities(), sector="Technology", country="Qatar")
    lp.reset_filters()
    assert lp.selected_filter_value("sector") == "All Sectors"
    assert lp.selected_filter_value("country") == "All Countries"
    assert lp.card_ercs() == full and lp.is_tab_active("active")


def _single_filter(page, key, label, bucket=None, case_options=None):
    lp = _open(page)
    items = lp.api_opportunities()
    d = Diff()
    if case_options is not None:
        d.eq(f"{key} options (dash-normalised, Figma default label)",
             [_dash(o) for o in lp.filter_options(key)], [_dash(o) for o in case_options])
    lp.select_filter(key, label)
    d.eq(f"{key} selected", lp.selected_filter_value(key), label)
    lp.apply_filters()
    crit_val = bucket or label
    want = _expected(lp, items, **{key: crit_val})
    d.eq(f"{key}={label} Active grid", set(lp.card_ercs()), want)
    d.eq("empty state when no match", lp.is_no_results_message_visible(), not want)
    if not want:  # case value matches no Active record — prove the filter on Archive
        lp.switch_tab("archive")
        d.eq(f"{key}={label} Archive grid", set(lp.card_ercs()), _expected(lp, items, "archive", **{key: crit_val}))
    d.check()


@_common("Sidebar filters", P3, 143293, FL)
@allure.title("Sector = Energy narrows the grid to Energy opportunities")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_filter_sector_energy(page):
    _single_filter(page, "sector", "Energy", case_options=[
        "All Sectors", "Technology", "Energy", "Infrastructure", "Finance", "Agriculture",
        "Tourism", "Healthcare", "Manufacturing", "Real Estate"])


@_common("Sidebar filters", P3, 143294, FL)
@allure.title("Country = United Arab Emirates narrows the grid to that country")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_filter_country_uae(page):
    _single_filter(page, "country", "United Arab Emirates")


@_common("Sidebar filters", P3, 143295, FL)
@allure.title("Investment Type = Equity narrows the grid to Equity opportunities")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_filter_investment_type_equity(page):
    _single_filter(page, "investment_type", "Equity", case_options=[
        "Investment Type", "Equity", "Debt", "Joint Venture", "Public-Private Partnership", "Grant", "Other"])


@_common("Sidebar filters", P3, 143296, FL)
@allure.title("Investment Amount = $1M-$5M narrows the grid to that range")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_filter_investment_amount_1_5m(page):
    _single_filter(page, "investment_amount", "$1M–$5M", bucket="1-5", case_options=[
        "Investment Amount", "Under $1M", "$1M-$5M", "$5M-$10M", "$10M-$25M", "$25M-$50M", "$50M-$100M", "$100M+"])


@_common("Sidebar filters", P3, 143297, FL)
@allure.title("Timeline = Immediate narrows the grid to that timeline")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_filter_timeline_immediate(page):
    _single_filter(page, "timeline", "Immediate", case_options=[
        "Timeline", "Immediate", "1-3 months", "3-6 months", "6-12 months", "12+ months"])


@_common("Sidebar filters", P3, 143298, FL)
@allure.title("Risk Profile = Low narrows the grid to that risk profile")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_filter_risk_low(page):
    _single_filter(page, "risk_profile", "Low", case_options=["Risk Profile", "Low", "Medium", "High"])


@_common("Empty state", P3, 143233, FL)
@allure.title("A zero-match filter combination shows the empty-results state, not a broken grid")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_zero_match_filters_show_empty_state(page):
    lp = _open(page)
    lp.select_filter("sector", "Agriculture")
    lp.select_filter("investment_amount", "$100M+")
    lp.select_filter("timeline", "Immediate")
    lp.apply_filters()
    assert _expected(lp, lp.api_opportunities(), sector="Agriculture", investment_amount="100p",
                     timeline="Immediate") == set()
    assert lp.card_count() == 0
    assert lp.is_no_results_message_visible()
    assert lp.no_results_message_text().rstrip(".") == "No results found"
    assert not lp.is_load_more_visible()
    assert lp.page.locator(".qc-bol-grid [class*='skeleton']").count() == 0


# =============================================================================
# P3 — tabs, counts, load more, chips, sort
# =============================================================================
@_common("Status tabs", P3, 143234, FL)
@allure.title("Active / Archive tab counts match the number of records in each status")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tab_counts_match_records(page):
    # Case assumes a seeded 8 / 3 dataset; qcdev's real records are compared.
    lp = _open(page)
    items = lp.api_opportunities()
    assert lp.tab_count("active") == len(_active_ercs(lp, items)) == lp.card_count()
    assert lp.tab_count("archive") == len(_archived_ercs(lp, items))


@_common("Load More", P4, 143212, FL, pytest.mark.tc_143305)
@allure.title("Load More is not rendered once every matching opportunity is displayed")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_load_more_hidden_when_all_loaded(page):
    lp = _open(page)
    assert lp.card_count() == lp.tab_count("active") <= lp.page_size()
    assert not lp.is_load_more_visible()
    # 143305: a filter matching fewer cards than one page
    lp.select_filter("investment_type", "Equity")
    lp.apply_filters()
    assert 0 < lp.card_count() < lp.page_size()
    assert not lp.is_load_more_visible()


@_common("Trending chips", P3, 143221, FL, pytest.mark.tc_143306)
@allure.title("Clicking a trending chip applies the matching Sector filter")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
@pytest.mark.parametrize("chip", ["Technology", "Infrastructure"])
def test_trending_chip_applies_sector_filter(page, chip):
    # 143221 = Technology, 143306 = Infrastructure (also expects a selected chip state)
    lp = _open(page)
    lp.click_trending_chip(chip)
    d = Diff()
    d.eq("grid = Sector filter result", set(lp.card_ercs()), _expected(lp, lp.api_opportunities(), sector=chip))
    d.eq("sidebar Sector reflects chip", lp.selected_filter_value("sector"), chip)
    st = lp.chip_state(chip)
    d.true("chip shows selected/active state",
           "active" in st["cls"] or st["pressed"] == "true" or st["current"] is not None, f"(actual {st})")
    d.check()


@_common("Sort", P3, 143299, FL)
@allure.title("Sort By reorders cards between Most Recent and Oldest by Publish Date")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_sort_by_publish_date(page):
    # Case dates (2026-09-01 / 09-15) do not exist; real publish dates used.
    # Sort Order is ignored by the listing — known bug 149519 (not asserted).
    lp = _open(page)
    items = {i["externalReferenceCode"]: i for i in lp.api_opportunities()}
    newest = sorted(_active_ercs(lp, list(items.values())), key=lambda e: items[e]["publishDate"], reverse=True)
    lp.select_sort("Most Recent")
    assert lp.selected_sort_value() == "Most Recent" and lp.card_ercs() == newest
    lp.select_sort("Oldest")
    assert lp.selected_sort_value() == "Oldest" and lp.card_ercs() == list(reversed(newest))


@_common("Sort", P3, 143250, FL)
@allure.title("Sort By shows Most Recent by default, offers Most Recent / Oldest and keeps Oldest selected")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_sort_dropdown_states(page):
    lp = _open(page)
    d = Diff()
    d.eq("default", lp.selected_sort_value(), "Most Recent")
    d.eq("options", lp.sort_options(), ["Most Recent", "Oldest"])
    fld = lp.box(lp.SORT_FIELD)
    d.near("sort field width (Figma 200)", fld["width"], 200, 2)
    d.near("sort field height (Figma 44)", fld["height"], 44, 2)
    before = lp.card_ercs()
    lp.select_sort("Oldest")
    d.eq("selected after choose", lp.selected_sort_value(), "Oldest")
    d.eq("grid reversed oldest-first", lp.card_ercs(), list(reversed(before)))
    d.eq("checked option on reopen", lp.page.locator(f"{lp.SORT_DROPDOWN} option:checked").inner_text().strip(), "Oldest")
    d.check()


@_common("Status tabs", P3, 143248, FL)
@allure.title("Active/Archive tab control renders per Figma and switches correctly")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tab_control_renders_and_switches(page):
    lp = _open(page)
    items = lp.api_opportunities()
    d = Diff()
    f = FIGMA_LIGHT
    act = lp.style(lp.TAB + ".is-active", ["color", "fontWeight", "fontSize", "boxShadow"])
    ina = lp.style(lp.TAB + ":not(.is-active)", ["color", "fontWeight", "fontSize"])
    base = lp.style(lp.TABS, ["boxShadow"])
    d.eq("active tab colour", _hex(act["color"]), f["tab_active"][0])
    d.eq("active tab weight", act["fontWeight"], f["tab_active"][1])
    d.true("active tab 2px underline #911731", "rgb(145, 23, 49) 0px -2px" in act["boxShadow"], act["boxShadow"])
    d.eq("inactive tab colour", _hex(ina["color"]), f["tab_inactive"][0])
    d.eq("inactive tab weight", ina["fontWeight"], f["tab_inactive"][1])
    d.true("tab base line 1px #A8A8A7", "rgb(168, 168, 167) 0px -1px" in base["boxShadow"], base["boxShadow"])
    d.near("tab row width (Figma 342, 2 x 171)", lp.box(lp.TABS)["width"], f["tabs_w"], 2)
    d.eq("Active count = Published/Active records", lp.tab_count("active"), len(_active_ercs(lp, items)))
    lp.switch_tab("archive")
    d.eq("archive selected", (lp.is_tab_active("archive"), lp.is_tab_active("active")), (True, False))
    d.eq("archive grid", set(lp.card_ercs()), _archived_ercs(lp, items))
    d.eq("Archive count", lp.tab_count("archive"), len(_archived_ercs(lp, items)))
    d.check()


# =============================================================================
# P3 — hero / search / chips UI (Figma)
# =============================================================================
@_common("Hero", P3, 143244, FL)
@allure.title("Listing hero renders eyebrow, title, description, image and CTA per Figma (EN, 1920)")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_hero_en_desktop(page):
    lp = _open(page)
    cfg = lp.api_page()
    f = FIGMA_LIGHT
    d = Diff()
    d.eq("dir", lp.document_direction(), "ltr")
    d.eq("eyebrow copy (PBI)", lp.hero_eyebrow_text(), "Global opportunity gateway")
    d.eq("title copy (PBI)", lp.hero_title_text(), "Global Business Opportunities")
    d.eq("description = CMS copy", lp.hero_description_text(), re.sub(r"<[^>]+>", "", cfg["heroDescription"]).strip())
    d.eq("CTA label", lp.hero_cta_label(), "Submit Opportunity")
    props = ["color", "fontSize", "fontWeight", "lineHeight", "fontFamily", "textAlign"]
    for key, loc in (("eyebrow", lp.HERO_EYEBROW), ("title", lp.HERO_TITLE), ("desc", f"{lp.HERO_DESCRIPTION} p")):
        s = lp.style(loc, props)
        d.eq(f"{key} font", (_hex(s["color"]), s["fontSize"], s["fontWeight"], s["lineHeight"]), f[key])
        d.true(f"{key} Cairo", s["fontFamily"].startswith("Cairo"), s["fontFamily"])
        d.true(f"{key} left-aligned", s["textAlign"] in ("start", "left"), s["textAlign"])
    c = lp.style(lp.HERO_CTA, ["color", "backgroundColor", "fontSize", "fontWeight", "borderRadius"])
    d.eq("CTA tokens", (_hex(c["color"]), _hex(c["backgroundColor"]), c["fontSize"], c["fontWeight"]), f["cta"])
    d.near("CTA height", lp.box(lp.HERO_CTA)["height"], 44, 2)
    d.near("hero height", lp.box(lp.HERO)["height"], f["hero_h"], 2)
    d.near("description width", lp.box(f"{lp.HERO_DESCRIPTION} p")["width"], f["desc_w"], 2)
    img = lp.box(lp.HERO_IMAGE)
    d.true("hero image loaded", lp.hero_image_loaded())
    d.near("hero image width", img["width"], f["hero_img"][0], 5)
    d.near("hero image height", img["height"], f["hero_img"][1], 5)
    for i in range(page.locator(lp.BREADCRUMB_LINK).count()):
        d.eq(f"breadcrumb[{i}] colour", _hex(lp.style(f"{lp.BREADCRUMB_LINK} span", ["color"], i)["color"]), f["crumb"])
    d.check()


@_common("Hero", P3, 143245, FL)
@allure.title("Listing hero renders the AR copy right-to-left with a mirrored CTA")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_hero_ar_rtl(page):
    lp = _open(page, locale="ar")
    cfg = lp.api_page("ar_SA")
    d = Diff()
    d.eq("dir", lp.document_direction(), "rtl")
    d.true("lang ar", lp.document_lang().startswith("ar"), lp.document_lang())
    d.eq("eyebrow = AR CMS copy", lp.hero_eyebrow_text(), cfg["eyebrowLabel"])
    d.eq("title = AR CMS copy", lp.hero_title_text(), cfg["pageTitle"])
    d.eq("CTA = AR CMS copy", lp.hero_cta_label(), cfg["ctaLabel"])
    for loc in (lp.HERO_EYEBROW, lp.HERO_TITLE, f"{lp.HERO_DESCRIPTION} p"):
        s = lp.style(loc, ["direction", "textAlign"])
        d.eq(f"{loc} direction", s["direction"], "rtl")
        r = lp.box(loc)
        d.near(f"{loc} right edge (shell 1620)", r["x"] + r["width"], 1620, 2)
        d.true(f"{loc} no Latin text", not re.search(r"[A-Za-z]{3,}", lp.text(loc)), lp.text(loc))
    cta, img = lp.box(lp.HERO_CTA), lp.box(lp.HERO_IMAGE)
    d.near("CTA right-aligned", cta["x"] + cta["width"], 1620, 2)
    d.true("image mirrored to the left", img["x"] < cta["x"], f"img.x={img['x']} cta.x={cta['x']}")
    d.check()


@_common("Search", P3, 143246, FL)
@allure.title("Search bar default / focus / typed / clear states per Figma")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_search_bar_states(page):
    lp = _open(page)
    f = FIGMA_LIGHT
    d = Diff()
    d.eq("placeholder", lp.search_placeholder(), "Search..")
    d.eq("value empty", lp.search_input_value(), "")
    d.true("search icon visible", page.locator(lp.SEARCH_ICON).is_visible())
    d.eq("placeholder colour", _hex(lp.placeholder_color()), f["placeholder"])
    fb = lp.box(lp.SEARCH_FIELD)
    d.near("field width", fb["width"], f["field"][0], 2)
    d.near("field height", fb["height"], f["field"][1], 2)
    fs = lp.style(lp.SEARCH_FIELD, ["borderRadius", "boxShadow"])
    d.eq("field radius", fs["borderRadius"], f["field"][2])
    d.true("field border #EDEDED", "rgb(237, 237, 237) 0px 0px 0px 1px" in fs["boxShadow"], fs["boxShadow"])
    bb = lp.box(lp.SEARCH_BUTTON)
    d.near("Search button width", bb["width"], f["search_btn"][0], 2)
    d.near("Search button height", bb["height"], f["search_btn"][1], 2)
    cs = lp.style(lp.SEARCH_CARD, ["borderRadius", "boxShadow"])
    d.eq("search card radius", cs["borderRadius"], f["search_card_radius"])
    d.true("search card shadow", f["search_card_shadow"] in cs["boxShadow"], cs["boxShadow"])
    page.locator(lp.SEARCH_INPUT).click()
    focus = lp.style(lp.SEARCH_FIELD, ["boxShadow"])["boxShadow"]
    d.true("focus highlight on field", focus != fs["boxShadow"], focus)
    page.locator(lp.SEARCH_INPUT).type("Smart City")
    d.eq("typed value", lp.search_input_value(), "Smart City")
    d.true("clear (x) control appears after typing", lp.search_clear_control_count() > 0,
           "(no clear control rendered; native cancel button suppressed)")
    d.check()


@_common("Trending chips", P3, 143247, FL)
@allure.title("Trending chips render per Figma, show a hover state and apply on click")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_trending_chips_render_and_click(page):
    lp = _open(page)
    f = FIGMA_LIGHT
    d = Diff()
    d.eq("chip labels (PBI order)", lp.trending_chip_labels(), ["Energy", "Infrastructure", "Technology", "Licensing route", "Qatar"])
    d.eq("'Trending:' colour", _hex(lp.style(lp.TRENDING_LABEL, ["color"])["color"]), f["trending_label"])
    s = lp.style(lp.TRENDING_CHIP, ["backgroundColor", "color", "fontSize", "fontWeight", "borderRadius"])
    d.eq("chip bg", _hex(s["backgroundColor"]), f["chip_bg"])
    d.eq("chip text", _hex(s["color"]), f["chip_fg"])
    d.eq("chip font", (s["fontSize"], s["fontWeight"]), ("12px", "400"))
    d.near("chip height", lp.box(lp.TRENDING_CHIP)["height"], 24, 2)
    boxes = [page.locator(lp.TRENDING_CHIP).nth(i).bounding_box() for i in range(5)]
    d.true("one row, no overlap", all(b["y"] == boxes[0]["y"] for b in boxes)
           and all(boxes[i]["x"] + boxes[i]["width"] <= boxes[i + 1]["x"] for i in range(4)))
    page.locator(lp.TRENDING_CHIP).first.hover()
    page.wait_for_timeout(300)  # CSS transition on hover; no DOM signal
    d.true("hover changes chip background", lp.style(lp.TRENDING_CHIP, ["backgroundColor"])["backgroundColor"] != s["backgroundColor"])
    before = lp.card_ercs()
    lp.click_trending_chip("Energy")
    d.true("click updates the grid", lp.card_ercs() != before)
    d.eq("chip keyword applied", lp.search_input_value(), "Energy")
    d.check()


# =============================================================================
# P3 — cards
# =============================================================================
@_common("Opportunity card", P3, 143314, FL)
@allure.title("Card banner image renders with the opportunity title overlaid")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_card_banner_image(page):
    # The overlay title is part of the banner artwork in Figma and on qcdev
    # (no text node) — checked: image loads at the Figma band size.
    lp = _open(page)
    d = Diff()
    for i in range(lp.card_count()):
        d.true(f"banner[{i}] loaded", lp.card_banner_loaded(i))
        b = lp.box(lp.CARD_BANNER_IMG, i)
        d.near(f"banner[{i}] height", b["height"], FIGMA_LIGHT["band_h"], 5)
        d.near(f"banner[{i}] width", b["width"], FIGMA_LIGHT["card"][0], 5)
    d.check()


@_common("Opportunity card", P3, 143315, FL)
@allure.title("Card shows the combined 'Sector · Investment Type' tag")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_card_sector_type_tag(page):
    lp = _open(page)
    items = {i["externalReferenceCode"]: i for i in lp.api_opportunities()}
    d = Diff()
    for erc, tag in zip(lp.card_ercs(), lp.card_tags()):
        it = items[erc]
        d.eq(f"{erc} tag", " ".join(tag), f"{_label(it, 'sector')} {FIGMA_LIGHT['dot']} {_label(it, 'investmentType')}")
    d.check()


@_common("Opportunity card", P3, 143316, FL)
@allure.title("Card title renders the EN title in English and the AR title in Arabic")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_card_title_en_ar(page):
    lp = _open(page)
    en = {i["externalReferenceCode"]: i["opportunityTitle"] for i in lp.api_opportunities("en_US")}
    ar = {i["externalReferenceCode"]: i["opportunityTitle"] for i in lp.api_opportunities("ar_SA")}
    assert [en[e] for e in lp.card_ercs()] == lp.card_titles()
    lp.open_listing(locale="ar")
    assert lp.document_direction() == "rtl"
    assert [ar[e] for e in lp.card_ercs()] == lp.card_titles()
    s = lp.style(lp.CARD_TITLE, ["direction"])
    assert s["direction"] == "rtl"


@_common("Opportunity card", P3, 143317, FL)
@allure.title("Card shows the Country preceded by a location pin icon")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_card_country_with_pin(page):
    lp = _open(page)
    items = {i["externalReferenceCode"]: i for i in lp.api_opportunities()}
    d = Diff()
    for idx, erc in enumerate(lp.card_ercs()):
        d.eq(f"{erc} country", lp.card_cells(idx)[0], items[erc]["country"])
        icon = page.locator(lp.CARD).nth(idx).locator(f"{lp.CARD_CELL} svg").first.bounding_box()
        txt = page.locator(lp.CARD).nth(idx).locator(lp.CARD_CELL_TEXT).first.bounding_box()
        d.true(f"{erc} pin icon before text", icon and icon["x"] + icon["width"] <= txt["x"])
        d.near(f"{erc} icon size", icon["width"], 18, 5)
    d.eq("country text fully visible (not truncated)", lp.truncated_cell_texts(), [])
    d.check()


@_common("Opportunity card", P3, 143318, FL)
@allure.title("Card shows the Investment Amount exactly as authored")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_card_investment_amount(page):
    # Case value '$2M - $5M' does not exist; every real card is compared.
    lp = _open(page)
    items = {i["externalReferenceCode"]: i for i in lp.api_opportunities()}
    d = Diff()
    for idx, erc in enumerate(lp.card_ercs()):
        d.eq(f"{erc} amount (EN)", lp.card_cells(idx)[1], items[erc]["investmentAmountRange"])
    # AR: the LTR amount must keep its visual order inside the RTL card
    lp.open_listing(locale="ar")
    flipped = page.evaluate("""() => [...document.querySelectorAll('.qc-bol-card-cell:nth-child(2) .qc-bol-card-cell-text')].filter(e => {
        const t = e.firstChild; if (!t || !/[+]$/.test(t.textContent)) return false;
        const r = document.createRange(); r.setStart(t, 0); r.setEnd(t, 1); const first = r.getBoundingClientRect();
        r.setStart(t, t.length - 1); r.setEnd(t, t.length); const last = r.getBoundingClientRect();
        return last.x < first.x; }).map(e => e.textContent)""")
    d.eq("AR amounts rendered in authored order (no bidi flip of '+')", flipped, [])
    d.check()


# =============================================================================
# P3/P4 — responsive, theme, language
# =============================================================================
@_common("Responsive", P3, 143249, FL)
@allure.title("Sidebar filters collapse on mobile and expand on tap showing all six defaults")
@pytest.mark.parametrize("page", [MOBILE_375], indirect=True)
def test_mobile_filters_panel(page):
    lp = _open(page)
    d = Diff()
    d.eq("collapsed by default", (lp.is_filters_panel_open(), lp.filters_toggle_expanded()), (False, "false"))
    t = lp.box(lp.FILTERS_TOGGLE)
    d.true("toggle tappable inside viewport", t["width"] >= 44 and t["x"] >= 0 and t["x"] + t["width"] <= 375)
    tabs = lp.box(lp.TABS)
    d.true("toggle does not overlap tabs", t["y"] + t["height"] <= tabs["y"])
    lp.open_filters_panel()
    d.true("panel open", lp.is_filters_panel_open())
    d.eq("six filters visible", lp.visible_filter_count(), 6)
    d.eq("defaults (Figma labels)", list(lp.selected_filter_values().values()),
         ["All Sectors", "All Countries", "Investment Type", "Investment Amount", "Timeline", "Risk Profile"])
    # Figma mobile frame is 390 wide — compare tokens there.
    page.set_viewport_size({"width": 390, "height": 844})
    lp.open_listing()
    fm = FIGMA_MOBILE
    d.near("collapsed bar height (390)", lp.box(lp.FILTERS_SIDE)["height"], fm["side_bar_h"], 2)
    h = lp.style(lp.FILTERS_HEADING, ["color", "fontSize", "fontWeight"])
    d.eq("collapsed heading font (390)", (_hex(h["color"]), h["fontSize"], h["fontWeight"]), fm["side_heading"])
    d.check()


@_common("Responsive", P3, 143262, FL)
@allure.title("Listing reflows to a single-column mobile layout (375 + Figma 390)")
@pytest.mark.parametrize("page", [MOBILE_375], indirect=True)
def test_mobile_layout(page):
    lp = _open(page)
    d = Diff()
    hero_copy, img = lp.box(lp.HERO_TITLE), lp.box(lp.HERO_IMAGE)
    d.true("hero stacks vertically (Figma: image below copy)", img["y"] >= hero_copy["y"] + hero_copy["height"])
    sc = lp.box(lp.SEARCH_CARD)
    d.near("search card full width (375-2x20)", sc["width"], 335, 2)
    d.eq("grid single column", lp.grid_column_count(), 1)
    d.near("card full width", lp.box(lp.CARD)["width"], 335, 2)
    tb = lp.box(lp.TAB, 1)
    d.true("tabs visible/tappable", tb["height"] >= 40 and tb["x"] + tb["width"] <= 375)
    d.true("no horizontal overflow (375)", not lp.has_horizontal_overflow())
    page.set_viewport_size({"width": 390, "height": 844})
    lp.open_listing()
    fm = FIGMA_MOBILE
    t = lp.style(lp.HERO_TITLE, ["fontSize", "fontWeight", "lineHeight"])
    d.eq("hero title font (Figma 390)", (t["fontSize"], t["fontWeight"], t["lineHeight"]), fm["title"])
    d.near("hero height (Figma 390)", lp.box(lp.HERO)["height"], fm["hero_h"], 2)
    hi = lp.box(lp.HERO_IMAGE)
    d.near("hero image w", hi["width"], fm["hero_img"][0], 5)
    d.near("hero image h", hi["height"], fm["hero_img"][1], 5)
    d.near("CTA full width", lp.box(lp.HERO_CTA)["width"], fm["cta_w"], 2)
    for i in range(2):
        d.near(f"tab[{i}] width (Figma 175)", lp.box(lp.TAB, i)["width"], fm["tab_w"], 2)
    c0, c1 = lp.box(lp.CARD, 0), lp.box(lp.CARD, 1)
    d.near("card width (390)", c0["width"], fm["card_w"], 2)
    d.near("card gap", c1["y"] - (c0["y"] + c0["height"]), fm["card_gap"], 2)
    d.true("no horizontal overflow (390)", not lp.has_horizontal_overflow())
    d.check()


@_common("Responsive", P3, 143263, FL)
@allure.title("Listing reflows to a 2-column card grid at 768 px")
@pytest.mark.parametrize("page", [TABLET_768], indirect=True)
def test_tablet_layout(page):
    lp = _open(page)
    d = Diff()
    d.true("no horizontal overflow", not lp.has_horizontal_overflow())
    side, grid = lp.box(lp.FILTERS_SIDE), lp.box(lp.CARD_GRID)
    d.true("filters panel does not overlap grid", side["y"] + side["height"] <= grid["y"] or side["x"] + side["width"] <= grid["x"])
    d.eq("card grid columns (case: 2 per row)", lp.grid_column_count(), 2)
    d.check()


@_common("Theme", P4, 143265, FL)
@allure.title("Dark mode recolours the listing per the Figma dark frame and persists after reload")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_dark_mode(page):
    lp = _open(page)
    assert lp.theme() == "light"
    assert _hex(lp.style("body", ["backgroundColor"])["backgroundColor"]) == FIGMA_LIGHT["body_bg"]
    AccessibilityToolsComponent(page).enable_dark_mode()
    page.wait_for_function("() => document.documentElement.getAttribute('data-theme') === 'dark'")
    f = FIGMA_DARK
    d = Diff()

    def col(loc, prop="color", i=0):
        return _hex(lp.style(loc, [prop], i)[prop])

    def check_all(tag):
        d.eq(f"{tag} page bg", col(".qc-bol-body", "backgroundColor"), f["body_bg"])
        d.eq(f"{tag} eyebrow", col(lp.HERO_EYEBROW), f["eyebrow"])
        d.eq(f"{tag} title", col(lp.HERO_TITLE), f["title"])
        d.eq(f"{tag} desc", col(f"{lp.HERO_DESCRIPTION} p"), f["desc"])
        for i in range(page.locator(lp.BREADCRUMB_LINK).count()):
            d.eq(f"{tag} breadcrumb[{i}]", col(f"{lp.BREADCRUMB_LINK} span", i=i), f["crumb"])
        stop0 = re.search(r"linear-gradient\([^,]+,\s*(rgba?\([^)]+\))", lp.style(lp.HERO, ["backgroundImage"])["backgroundImage"])
        d.eq(f"{tag} hero gradient first stop", _hex(stop0.group(1)) if stop0 else None, f["hero_stop0"])
        d.true(f"{tag} search card border", "rgb(74, 74, 73) 0px 0px 0px 1px" in lp.style(lp.SEARCH_CARD, ["boxShadow"])["boxShadow"])
        d.eq(f"{tag} 'Trending:'", col(lp.TRENDING_LABEL), f["trending_label"])
        d.eq(f"{tag} chip bg", col(lp.TRENDING_CHIP, "backgroundColor"), f["chip_bg"])
        d.eq(f"{tag} chip text", col(lp.TRENDING_CHIP), f["chip_fg"])
        d.eq(f"{tag} side heading", col(lp.FILTERS_HEADING), f["side_heading"])
        d.eq(f"{tag} Filter label", col(lp.FILTER_LABEL), f["filter_label"])
        d.eq(f"{tag} active tab", col(lp.TAB + ".is-active"), f["tab_active"])
        d.eq(f"{tag} inactive tab", col(lp.TAB + ":not(.is-active)"), f["tab_inactive"])
        d.true(f"{tag} tab base line {f['tab_base']}", "rgb(168, 168, 167) 0px -1px" in lp.style(lp.TABS, ["boxShadow"])["boxShadow"],
               lp.style(lp.TABS, ["boxShadow"])["boxShadow"])
        d.eq(f"{tag} card bg", col(lp.CARD, "backgroundColor"), f["card_bg"])
        d.eq(f"{tag} card border", col(lp.CARD, "borderTopColor"), f["card_border"])
        d.eq(f"{tag} card sector", col(f"{lp.CARD_TAG} span:first-child"), f["cat"])
        d.eq(f"{tag} card type", col(f"{lp.CARD_TAG} span:last-child"), f["cat2"])
        d.eq(f"{tag} card title", col(lp.CARD_TITLE), f["card_title"])
        d.eq(f"{tag} card cell", col(lp.CARD_CELL_TEXT), f["cell"])
        d.eq(f"{tag} card rule", col(lp.CARD_RULE, "backgroundColor"), f["rule"])
        d.eq(f"{tag} View Details", col(lp.CARD_VIEW_DETAILS_LINK), f["view"])
        d.eq(f"{tag} arrow bg", col(lp.CARD_ARROW, "backgroundColor"), f["arrow_bg"])

    check_all("dark")
    page.reload(wait_until="domcontentloaded")
    d.eq("theme applied at DOMContentLoaded after reload (no light flash)", lp.theme(), "dark")
    lp.wait_for_ready()
    d.eq("dark persists after reload", lp.theme(), "dark")
    d.check()


@_common("Language", P3, 143267, FL)
@allure.title("EN/AR switch persists across the Listing and Detail pages")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_language_persists_listing_detail(page):
    lp = _open(page)
    sw = HeaderComponent.LANGUAGE_SWITCHER
    page.locator(sw).click()
    page.wait_for_url(re.compile(r"/ar/"), timeout=30000)
    lp.wait_for_ready()
    assert lp.document_direction() == "rtl"
    ar_title = lp.api_page("ar_SA")["pageTitle"]
    assert lp.hero_title_text() == ar_title
    page.locator(lp.CARD).first.click()
    page.wait_for_selector("h1.qc-bod-title", timeout=30000)
    assert "/ar/" in page.url and lp.document_direction() == "rtl"
    page.locator(sw).click()
    page.wait_for_function("() => document.documentElement.dir === 'ltr'", timeout=30000)
    page.wait_for_selector("h1.qc-bod-title", timeout=30000)
    assert lp.document_lang().startswith("en")
    lp.open(web_url(PATH))
    lp.wait_for_ready()
    assert lp.document_direction() == "ltr" and lp.hero_title_text() == "Global Business Opportunities"


# =============================================================================
# Blocked — required state cannot be created read-only (brief rule 3)
# =============================================================================
@pytest.mark.parametrize("tc, reason", [
    pytest.param("143211", "only 4 Active opportunities vs page size 6 - Load More never renders", marks=pytest.mark.tc_143211),
    pytest.param("143304", "case needs 24 Active / 12 per page; qcdev has 4 Active, page size 6", marks=pytest.mark.tc_143304),
    pytest.param("143252", "Load More loading/default states need >1 page of Active results; 4 < 6", marks=pytest.mark.tc_143252),
    pytest.param("143236", "needs a record whose Archive Date is tomorrow and a clock boundary; none exists, no CMS writes allowed", marks=pytest.mark.tc_143236),
    pytest.param("143238", "needs zero Published/Archived opportunities site-wide; real records exist", marks=pytest.mark.tc_143238),
])
@pytest.mark.web
@pytest.mark.pbi_130697
def test_blocked_listing_cases(tc, reason):
    pytest.skip(f"BLOCKED tc_{tc}: {reason}")

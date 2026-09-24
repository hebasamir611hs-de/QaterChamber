"""
web/tests/global_search/test_global_search_web.py

Web-platform cases for PBI 131055 ("Global Advanced Search"), suite 140393 —
8 approved Automation cases: 141837, 141838, 141839, 141840, 141841, 141842,
141843, 141891 (141844/141845 are Manual, not here).

Fresh UNAUTHENTICATED context per test; every test collects all deviations
and fails once. The search is always driven through the real header flow
(icon -> overlay input -> Enter) except where only the results layout at a
viewport is under test.

Disclosed readings:
  - "Content-type label" = the first metadata `strong` of a result
    ("Document", "Page"; AR "الصفحة"). "Summary" = a snippet element
    (`.list-group-text` / `.search-results-content`) with non-empty text.
  - Filters/facets = Liferay facet portlets or any facet-class element; a
    mobile "Filters" control = a button/toggle for them. None is placed on the
    live results page, so the filter checks report "not rendered".
  - "Suggestion" on no-results = a spelling suggestion or any link/element in
    the results portlet offering a next step.
  - Locale scoping: EN titles contain no Arabic script; AR titles contain
    Arabic script.
"""

import re

import allure
import pytest

from web.pages.global_search.global_search_page import GlobalSearchPage

PBI = "131055"
ANON = {"auth": False}
ARABIC = re.compile(r"[؀-ۿ]")
TAP = 44.0
PAGES = (("Home", "/web/qatar-chamber"), ("About Us", "/web/qatar-chamber/about-us"),
         ("Chamber Events", "/web/qatar-chamber/events"))

pytestmark = [pytest.mark.web, pytest.mark.pbi_131055, pytest.mark.global_]


class _Check:
    def __init__(self, title):
        self.title, self.deviations = title, []

    def truthy(self, label, condition, expected, actual):
        if not condition:
            self.deviations.append(f"{label}: expected {expected!r}, got {actual!r}")

    def equals(self, label, actual, expected):
        self.truthy(label, actual == expected, expected, actual)

    def missing(self, label, detail):
        self.deviations.append(f"{label}: not rendered on the live page — {detail}")

    def assert_clean(self):
        assert not self.deviations, f"{self.title}: {len(self.deviations)} deviation(s):\n  - " + "\n  - ".join(self.deviations)


def _meta(tc, title, story, severity=allure.severity_level.CRITICAL):
    def deco(fn):
        for d in (allure.label("testcase", tc), allure.label("pbi", PBI), allure.title(title),
                  allure.severity(severity), allure.story(story), allure.feature("Global Advanced Search"),
                  allure.epic("Global")):
            fn = d(fn)
        return fn
    return deco


N = allure.severity_level.NORMAL


def _filters(check: _Check, gs: GlobalSearchPage, where: str):
    if gs.visible_count(gs.FACETS) == 0:
        check.missing(f"filters panel ({where})", "0 facet/filter controls on the results page")


def _layout(check: _Check, gs: GlobalSearchPage, width: int, single_column: bool):
    o = gs.horizontal_overflow_px()
    check.truthy("no horizontal scroll", o <= 0, "0px", f"{o}px")
    res = gs.results()
    check.truthy("result cards rendered", len(res) > 0, "at least one", 0)
    for i in range(len(res) - 1):
        a, b = res[i], res[i + 1]
        check.truthy(f"result {i + 1}/{i + 2} no overlap", a["y"] + a["height"] <= b["y"] + 1, "stacked", (a["y"], b["y"]))
    for i, r in enumerate(res):
        check.truthy(f"result {i + 1} inside the {width}px viewport", r["x"] >= 0 and r["x"] + r["width"] <= width + 1,
                     f"0..{width}", (round(r["x"]), round(r["width"])))
        check.truthy(f"result {i + 1} text not truncated", not r["clipped"], "unclipped", "clipped")
    if single_column:
        check.truthy("results in a single column", len({round(r["x"]) for r in res}) <= 1, "one x position",
                     sorted({round(r["x"]) for r in res}))


# ---------------------------------------------------------------------------
@_meta("141837", "Global search bar is accessible from the header on every page", "Header search")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_141837
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_header_search_on_every_page(page):
    """Azure TC 141837 | PBI 131055 — header search icon present, in the header, at the same position with
    the same behaviour (opens the overlay) on Home, About Us and the Chamber Events listing."""
    check = _Check("TC 141837")
    gs = GlobalSearchPage(page)
    positions = {}
    for name, path in PAGES:
        gs.open_path(path)
        check.truthy(f"{name}: search icon visible in the header", gs.is_visible(gs.HEADER_SEARCH_BUTTON)
                     and gs.header_search_facts()["inHeader"], "visible in header", gs.header_search_facts())
        box = gs.header_search_box()
        positions[name] = (round(box["x"]), round(box["y"])) if box else None
        gs.click(gs.HEADER_SEARCH_BUTTON)
        check.truthy(f"{name}: icon opens the search input", gs.is_visible(gs.OVERLAY_INPUT), "overlay input visible", "hidden")
    check.truthy("same header position on all three pages", len(set(positions.values())) == 1, "identical", positions)
    check.assert_clean()


@_meta("141838", "Each search result displays title, summary and content type", "Results")
@pytest.mark.ui
@pytest.mark.search
@pytest.mark.tc_141838
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_result_card_fields(page):
    """Azure TC 141838 | PBI 131055 — 'membership': first card and a card of a different content type each show
    a non-empty title, a summary and a content-type label."""
    check = _Check("TC 141838")
    gs = GlobalSearchPage(page).open_path("/web/qatar-chamber").search_from_header("membership")
    res = gs.results()
    check.truthy("results listed", len(res) > 0, "at least one", 0)
    if res:
        first = res[0]
        check.truthy("first result title", bool(first["title"]), "non-empty", first["title"])
        check.truthy("first result summary", bool(first["summary"]), "non-empty summary/snippet",
                     f"none (title {first['title']!r}, type {first['type']!r})")
        check.truthy("first result content-type label", bool(first["type"]), "non-empty", first["type"])
        other = next((r for r in res if r["type"] and r["type"] != first["type"]), None)
        if other is None:
            check.truthy("a result of a different content type", False, "a second content type on page 1",
                         f"all {len(res)} results are {sorted({r['type'] for r in res})}")
        else:
            check.truthy("second-type result summary", bool(other["summary"]), "non-empty", other["summary"])
            check.truthy("second-type result title", bool(other["title"]), "non-empty", other["title"])
    check.assert_clean()


@_meta("141839", "Search operates and renders correctly in English (LTR)", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_141839
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_search_english_ltr(page):
    """Azure TC 141839 | PBI 131055 — EN 'training': LTR, left-aligned, filters on the LTR side, English results."""
    check = _Check("TC 141839")
    gs = GlobalSearchPage(page).open_path("/web/qatar-chamber").search_from_header("training")
    check.equals("page direction", gs.document_dir(), "ltr")
    res = gs.results()
    check.truthy("results listed", len(res) > 0, "at least one", 0)
    for i, r in enumerate(res):
        check.truthy(f"result {i + 1} left-aligned LTR", r["titleDir"] == "ltr" and r["titleAlign"] in ("left", "start"),
                     "ltr/left", (r["titleDir"], r["titleAlign"]))
        check.truthy(f"result {i + 1} English (no Arabic script)", not ARABIC.search(r["title"] + r["summary"]),
                     "English", r["title"])
    _filters(check, gs, "EN")
    check.assert_clean()


@_meta("141891", "Search operates and renders correctly in Arabic (RTL)", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_141891
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_search_arabic_rtl(page):
    """Azure TC 141891 | PBI 131055 — AR 'تدريب': RTL, right-aligned, filters on the RTL side, Arabic results."""
    check = _Check("TC 141891")
    gs = GlobalSearchPage(page).open_path("/web/qatar-chamber", locale="ar").search_from_header("تدريب")
    check.truthy("results URL under /ar", "/ar/" in gs.current_url(), "/ar/…/search?q=", gs.current_url())
    check.equals("page direction", gs.document_dir(), "rtl")
    res = gs.results()
    check.truthy("results listed", len(res) > 0, "at least one", 0)
    for i, r in enumerate(res):
        check.truthy(f"result {i + 1} right-aligned RTL", r["titleDir"] == "rtl" and r["titleAlign"] in ("right", "start"),
                     "rtl/right", (r["titleDir"], r["titleAlign"]))
        check.truthy(f"result {i + 1} Arabic", bool(ARABIC.search(r["title"])), "Arabic", r["title"])
    _filters(check, gs, "AR")
    check.assert_clean()


@_meta("141840", "'No results found' state displays a message with suggestions", "No results")
@pytest.mark.ui
@pytest.mark.search
@pytest.mark.tc_141840
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_no_results_state(page):
    """Azure TC 141840 | PBI 131055 — 'zzqcnoresultxx123': zero cards, a no-results message and >= 1 suggestion."""
    check = _Check("TC 141840")
    gs = GlobalSearchPage(page).open_path("/web/qatar-chamber").search_from_header("zzqcnoresultxx123")
    check.equals("zero result cards", len(gs.results()), 0)
    check.truthy("no-results message", gs.count(gs.NO_RESULTS) > 0, "message", gs.text_of(gs.RESULTS_PORTLET)[:120])
    if gs.visible_count(gs.SUGGESTIONS) == 0:
        check.missing("suggestion element", f"portlet shows only {gs.text_of(gs.RESULTS_PORTLET)!r}")
    check.assert_clean()


@_meta("141841", "Results page is responsive on desktop viewport", "Responsive", N)
@pytest.mark.compatibility
@pytest.mark.tc_141841
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_results_desktop(page):
    """Azure TC 141841 | PBI 131055 — 1920x1080 'events': filters and results side by side, no overlap/scroll."""
    check = _Check("TC 141841")
    gs = GlobalSearchPage(page).open_path("/web/qatar-chamber").search_from_header("events")
    _layout(check, gs, 1920, single_column=False)
    _filters(check, gs, "desktop, beside the results")
    check.assert_clean()


@_meta("141842", "Results page is responsive on tablet viewport", "Responsive", N)
@pytest.mark.compatibility
@pytest.mark.tc_141842
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_results_tablet(page):
    """Azure TC 141842 | PBI 131055 — 768x1024 'events': filters collapse/reflow; cards stack cleanly."""
    check = _Check("TC 141842")
    gs = GlobalSearchPage(page).open_path("/web/qatar-chamber").search_from_header("events")
    _layout(check, gs, 768, single_column=True)
    if gs.visible_count(gs.FACETS) == 0 and gs.visible_count(gs.FILTER_TOGGLE) == 0:
        check.missing("filters panel / toggle (tablet)", "0 facet or filter-toggle controls")
    check.assert_clean()


@_meta("141843", "Results page is responsive on mobile viewport", "Responsive", N)
@pytest.mark.compatibility
@pytest.mark.tc_141843
@pytest.mark.parametrize("page", [{"viewport": (375, 812), "auth": False}], indirect=True)
def test_results_mobile(page):
    """Azure TC 141843 | PBI 131055 — 375x812 'events': 'Filters' control, single column, no scroll, tap targets."""
    check = _Check("TC 141843")
    gs = GlobalSearchPage(page).open_path("/web/qatar-chamber").search_from_header("events")
    _layout(check, gs, 375, single_column=True)
    if gs.visible_count(gs.FILTER_TOGGLE) == 0:
        check.missing("mobile 'Filters' control", "no filter button/drawer on the results page")
    small = [t for t in gs.tap_targets() if t["height"] < TAP and t["text"]]
    check.truthy("results controls large enough to tap (>= 44px)", not small, "none below 44px",
                 [f"{t['text']!r} {round(t['width'])}x{round(t['height'])}" for t in small][:10])
    check.assert_clean()

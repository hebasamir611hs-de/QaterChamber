"""
web/tests/news/test_news_web.py

Web-platform cases for PBI 131059 ("QC - Insights & Media - 001 - News
Archive"), suite 140394 — 30 approved Automation cases:
UI 146325-146341, 146345; Compatibility 146346-146351, 146353, 146354;
Bilingual 146367, 146473, 146474, 146479.
Not here (out of scope / Manual): 146342, 146352, 146355, 146366, 146486.

Every test uses a fresh UNAUTHENTICATED context (or its own browser for the
Chrome/Edge/Firefox cases, via the module-local `engine_page` fixture, which
attaches a failure screenshot to Allure itself) and fails once with the full
deviation list.

Design values: the case's own numbers first; values the case names but does
not quantify come from the Figma extract (EN light listing 5397:263592, EN
dark 5397:269207, EN details 5397:263637, EN mobile 390 5397:263728). AR
frames are asserted as RTL mirroring + Arabic copy only.

TEST DATA (reported as notes, never a failure on their own): the Figma sample
content the cases quote — article dates/view counts ('Mar 3, 2026', '2,847'),
the Featured title, the seeded 'QCTEST-131059' articles and the 68-character
title. The product part is still asserted (format, placement, style).
Substitutions (disclosed): the detail cases use article 182442 ("Qatar Chamber
Explores Relations with Turkish EPIAD", Collaboration, dated 2026-03-03, 5
keywords) — the article the cases describe. 146367 uses the published
bilingual Trade Forum article (id 182424, Trade & Economy) in place of the
unseeded 'QCTEST-131059 منتدى التجارة'. Arabic copy is compared with tashkeel
(diacritics, e.g. shadda) removed — 'مميّز' == 'مميز'.
"""

import re

import allure
import pytest

from config.settings import settings
from core.web.design_tokens import hex_to_rgb, px_close
from core.utils.reporting import attach_screenshot, extract_test_case_id
from web.pages.news.news_page import NewsPage

PBI = "131059"
DETAIL_ID = 182442          # Turkish EPIAD / Collaboration / 2026-03-03 / 5 keywords
FEATURED_AR_ID = 182424     # Trade Forum, Trade & Economy (146367 substitution)
D1920 = {"viewport": (1920, 1080), "auth": False}
T768 = {"viewport": (768, 1024), "auth": False}
M390 = {"viewport": (390, 844), "auth": False}
ARABIC = re.compile(r"[؀-ۿ]")
TASHKEEL = re.compile(r"[ً-ْٰ]")
EN_DATE = re.compile(r"^[A-Z][a-z]{2} \d{1,2}, \d{4}$")
EN_VIEWS = re.compile(r"^\d{1,3}(,\d{3})*$")
EN_READ = re.compile(r"^\d+ Min Read$")
TYPO = ("font-family", "font-weight", "font-size", "line-height", "color")
AA = 4.5

pytestmark = [pytest.mark.web, pytest.mark.pbi_131059, pytest.mark.media]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class _Check:
    def __init__(self, title):
        self.title, self.deviations, self.notes = title, [], []

    def truthy(self, label, cond, expected, actual):
        if not cond:
            self.deviations.append(f"{label}: expected {expected!r}, got {actual!r}")

    def equals(self, label, actual, expected):
        self.truthy(label, actual == expected, expected, actual)

    def color(self, label, actual, hex_):
        self.truthy(label, actual == hex_to_rgb(hex_), f"{hex_} ({hex_to_rgb(hex_)})", actual)

    def px(self, label, actual, expected, tol=1.0):
        a = actual if isinstance(actual, str) else (f"{actual:.1f}px" if actual is not None else None)
        self.truthy(label, a is not None and px_close(a, f"{expected}px", tol), f"{expected}px", a)

    def size(self, label, box, w, h, tol=1.0):
        self.truthy(f"{label} size", box is not None and abs(box["width"] - w) <= tol and abs(box["height"] - h) <= tol,
                    f"{w}x{h}", f"{round(box['width'], 1)}x{round(box['height'], 1)}" if box else None)

    def typo(self, label, s, size, weight, line=None, hex_=None):
        self.truthy(f"{label}.font-family", "cairo" in s["font-family"].lower(), "Cairo", s["font-family"])
        self.px(f"{label}.font-size", s["font-size"], size, 0.25)
        self.truthy(f"{label}.font-weight", str(s["font-weight"]) == str(weight), str(weight), s["font-weight"])
        if line is not None:
            self.px(f"{label}.line-height", s["line-height"], line, 0.25)
        if hex_:
            self.color(f"{label}.color", s["color"], hex_)

    def data(self, label, expected, actual):
        if expected != actual:
            self.notes.append(f"TEST DATA — {label}: expected {expected!r}, got {actual!r}")

    def missing(self, label, detail):
        self.deviations.append(f"{label}: not rendered — {detail}")

    def assert_clean(self):
        if self.notes:
            allure.attach("\n".join(self.notes), "notes (test data / assumptions)", allure.attachment_type.TEXT)
        extra = [n for n in self.notes if n.startswith("TEST DATA")]
        assert not self.deviations, (f"{self.title}: {len(self.deviations)} deviation(s):\n  - " + "\n  - ".join(self.deviations)
                                     + ("\n  (reported, not failing) " + "; ".join(extra) if extra else ""))


def _ar(t: str) -> str:
    return TASHKEEL.sub("", t or "").strip()


def _overlap(a, b) -> bool:
    return bool(a and b) and (a["x"] < b["x"] + b["width"] - 1 and b["x"] < a["x"] + a["width"] - 1
                              and a["y"] < b["y"] + b["height"] - 1 and b["y"] < a["y"] + a["height"] - 1)


RING = re.compile(r"(rgba?\([^)]*\)) 0px 0px 0px ([\d.]+)px inset")


def _radius(check, label, s, expected, height=None):
    """9999 ('fully rounded') passes when the radius is >= half the element height."""
    r = s["border-top-left-radius"]
    if expected == 9999 and height:
        val = float(r[:-2]) if r.endswith("px") else (9999.0 if r == "50%" else 0.0)
        check.truthy(f"{label}.border-radius", val >= height / 2 - 0.5, "fully rounded (>= height/2)", r)
    else:
        check.px(f"{label}.border-radius", r, expected, 0.5)


def _border(check, label, s, hex_, width=1):
    """A 1px border may be painted as a CSS border OR an inset box-shadow ring
    (`<color> 0px 0px 0px 1px inset`) — both render the same line."""
    ring = RING.match(s.get("box-shadow") or "")
    if s["border-top-style"] == "solid" and float(s["border-top-width"].rstrip("px") or 0) > 0:
        check.px(f"{label}.border width", s["border-top-width"], width, 0.25)
        check.color(f"{label}.border-color", s["border-top-color"], hex_)
    elif ring:
        check.px(f"{label}.border width (inset ring)", ring.group(2) + "px", width, 0.25)
        check.color(f"{label}.border-color (inset ring)", ring.group(1), hex_)
    else:
        check.truthy(f"{label}.border", False, f"{width}px {hex_}",
                     f"{s['border-top-width']} {s['border-top-style']}, box-shadow {s.get('box-shadow')}")


BORDER = ("border-top-style", "border-top-width", "border-top-color", "border-top-left-radius", "background-color", "box-shadow")


def _no_overflow(check, news):
    o = news.horizontal_overflow_px()
    check.truthy("no horizontal scroll", o <= 0, "0px", f"{o}px")


def _items_by_id(news, locale="en"):
    return {i["id"]: i for i in news.api_items(locale)}


def _matches(item, kw):
    return kw.lower() in (item.get("title", "") + " " + item.get("summary", "") + " " + re.sub("<[^>]+>", " ", item.get("description", ""))).lower()


def _meta(tc, title, story, severity=allure.severity_level.NORMAL):
    def deco(fn):
        for d in (allure.label("testcase", tc), allure.label("pbi", PBI), allure.title(title),
                  allure.severity(severity), allure.story(story), allure.feature("News Archive"),
                  allure.epic("Insights & Media")):
            fn = d(fn)
        return fn
    return deco


C, N, MI = allure.severity_level.CRITICAL, allure.severity_level.NORMAL, allure.severity_level.MINOR


@pytest.fixture
def engine_page(request, playwright_instance):
    """Own browser for this test (engine chromium|firefox, optional channel), unauthenticated,
    1920x1080; collects console errors; attaches a failure screenshot to Allure."""
    cfg = request.param
    kwargs = {"headless": settings.headless}
    if cfg.get("channel"):
        kwargs["channel"] = cfg["channel"]
    browser = getattr(playwright_instance, cfg["engine"]).launch(**kwargs)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    pg = context.new_page()
    pg.console_errors = []
    pg.on("console", lambda m: pg.console_errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: pg.console_errors.append(f"pageerror: {e}"))
    yield pg
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        try:
            attach_screenshot(pg.screenshot(), extract_test_case_id(request.node), settings.project_name, settings.reports_dir)
        except Exception:  # noqa: BLE001
            pass
    context.close()
    browser.close()


# ---------------------------------------------------------------------------
# EN light desktop listing (146325-146329)
# ---------------------------------------------------------------------------
@_meta("146325", "EN light desktop listing hero and breadcrumb match Figma", "Listing UI", MI)
@pytest.mark.ui
@pytest.mark.tc_146325
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_listing_hero_breadcrumb(page):
    """Azure TC 146325 | PBI 131059 — hero 1920x140; 'News & Press Releases' Cairo 30/700/38 #FFFFFF;
    breadcrumb 'Home > Insights & Media > News', home icon 12x12, 2 chevrons, Cairo 14/400/22 #FFFFFF, 6px gap."""
    check = _Check("TC 146325")
    news = NewsPage(page).open_listing()
    check.size("hero", news.box(news.HERO), 1920, 140)
    check.equals("hero title", news.text_of(news.HERO_TITLE), "News & Press Releases")
    check.typo("hero title", news.styles(news.HERO_TITLE, TYPO), 30, 700, 38, "#FFFFFF")
    items = news.texts(news.CRUMB_ITEMS)
    check.equals("breadcrumb items", items, ["Home", "Insights & Media", "News"])
    check.size("breadcrumb home icon", news.box(news.CRUMB_HOME_ICON), 12, 12)
    check.equals("breadcrumb chevrons", news.count(news.CRUMB_SEP), 2)
    for i, label in enumerate(("Home", "Insights & Media", "News")):
        check.typo(f"breadcrumb '{label}'", news.styles(news.CRUMB_ITEMS, TYPO, i), 14, 400, 22, "#FFFFFF")
    check.px("breadcrumb gap", news.styles(news.CRUMBS, ("column-gap",))["column-gap"], 6, 0.5)
    check.assert_clean()


@_meta("146326", "EN light desktop search, category and sort controls match Figma", "Listing UI")
@pytest.mark.ui
@pytest.mark.tc_146326
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_listing_filter_controls(page):
    """Azure TC 146326 | PBI 131059 — filter row 1320 wide, 12px gaps; search 896x44 white 1px #EDEDED r8,
    placeholder 14/400 #A8A8A7, icon 15x15 #911731; category 200x44 'All Categories' 14/400 #343432, chevron
    10x5 #A8A8A7; sort 200x46 'Most Recent' 14/400 #343432, chevron 9x4 #A8A8A7."""
    check = _Check("TC 146326")
    news = NewsPage(page).open_listing()
    row = news.box(news.CONTROLS)
    check.px("filter row width", row["width"] if row else None, 1320)
    s, c, t = news.box(news.SEARCH_FIELD), news.box(news.CATEGORY_FIELD), news.box(news.SORT_FIELD)
    check.px("gap search->category", c["x"] - (s["x"] + s["width"]), 12, 0.5)
    check.px("gap category->sort", t["x"] - (c["x"] + c["width"]), 12, 0.5)
    check.size("search input", news.box(news.SEARCH_FIELD), 896, 44)
    si = news.styles(news.SEARCH_FIELD, BORDER)
    check.color("search fill", si["background-color"], "#FFFFFF")
    _border(check, "search", si, "#EDEDED")
    _radius(check, "search", si, 8)
    check.equals("search placeholder", news.attribute(news.SEARCH_INPUT, "placeholder"), "Search news and press releases...")
    check.typo("search placeholder", news.styles(news.SEARCH_INPUT, TYPO, pseudo="::placeholder"), 14, 400, None, "#A8A8A7")
    check.size("search icon", news.box(news.SEARCH_ICON), 15, 15)
    ic = news.styles(news.SEARCH_ICON, ("color", "stroke"))
    check.truthy("search icon colour", hex_to_rgb("#911731") in (ic["color"], ic["stroke"]), "#911731", ic)
    for name, sel, chev, label, (w, h), (cw, ch) in (
            ("category", news.CATEGORY, news.CATEGORY_CHEV, "All Categories", (200, 44), (10, 5)),
            ("sort", news.SORT, news.SORT_CHEV, "Most Recent", (200, 46), (9, 4))):
        field = news.CATEGORY_FIELD if name == "category" else news.SORT_FIELD
        check.size(f"{name} dropdown", news.box(field), w, h)
        st = {**news.styles(field, BORDER), **news.styles(sel, TYPO)}
        _border(check, name, st, "#EDEDED")
        _radius(check, name, st, 8)
        check.equals(f"{name} label", news.selected_label(sel), label)
        check.typo(f"{name} label", st, 14, 400, None, "#343432")
        check.size(f"{name} chevron", news.box(chev), cw, ch)
        cs = news.styles(chev, ("color", "stroke"))
        check.truthy(f"{name} chevron colour", hex_to_rgb("#A8A8A7") in (cs["color"], cs["stroke"]), "#A8A8A7", cs)
    check.assert_clean()


@_meta("146327", "EN light desktop Featured card matches Figma", "Listing UI")
@pytest.mark.ui
@pytest.mark.tc_146327
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_listing_featured_card(page):
    """Azure TC 146327 | PBI 131059 — Featured first; pills 77x36 / 134x36 #F6F6F6 r6 16/400 #6C6C6B; title
    30/700/38 #343432; summary 18/400/28 #4A4A49; meta date + views + 'N Min Read' 14/400 #6C6C6B, icons
    #A8A8A7; image 640x360 r12."""
    check = _Check("TC 146327")
    news = NewsPage(page).open_listing()
    f, g = news.box(news.FEATURED), news.box(news.GRID)
    check.truthy("Featured above the standard cards", f and g and f["y"] + f["height"] <= g["y"] + 1, "above", (f, g))
    pills = news.texts(news.FEAT_PILL)
    check.equals("Featured pills", pills, ["Featured", "Trade & Economy"])
    for i, (w, h) in enumerate(((77, 36), (134, 36))[:len(pills)]):
        check.size(f"pill '{pills[i]}'", news.box(news.FEAT_PILL, i), w, h)
        st = news.styles(news.FEAT_PILL, BORDER + TYPO, i)
        check.color(f"pill '{pills[i]}' fill", st["background-color"], "#F6F6F6")
        _radius(check, f"pill '{pills[i]}'", st, 6)
        check.typo(f"pill '{pills[i]}'", st, 16, 400, None, "#6C6C6B")
    check.data("Featured title", "Qatar Chamber Hosts International Trade Forum 2026 ...", news.text_of(news.FEAT_TITLE))
    check.typo("Featured title", news.styles(news.FEAT_TITLE, TYPO), 30, 700, 38, "#343432")
    check.typo("Featured summary", news.styles(news.FEAT_SUMMARY, TYPO), 18, 400, 28, "#4A4A49")
    meta = news.texts(news.FEAT_META_ITEM)
    check.truthy("meta date format", len(meta) > 0 and bool(EN_DATE.match(meta[0])), "Mmm D, YYYY", meta[:1])
    check.truthy("meta view count format", len(meta) > 1 and bool(EN_VIEWS.match(meta[1])), "e.g. 2,847", meta[1:2])
    check.truthy("meta read time format", len(meta) > 2 and bool(EN_READ.match(meta[2])), "N Min Read", meta[2:3])
    check.data("meta date / views", ["Mar 3, 2026", "2,847"], meta[:2])
    for i in range(len(meta)):
        check.typo(f"meta item {i + 1}", news.styles(news.FEAT_META_ITEM, TYPO, i), 14, 400, None, "#6C6C6B")
        ic = news.styles(news.FEAT_META_ICON, ("stroke", "color"), i)
        check.truthy(f"meta icon {i + 1} stroke", hex_to_rgb("#A8A8A7") in (ic["stroke"], ic["color"]), "#A8A8A7", ic)
    check.size("Featured image", news.box(news.FEAT_MEDIA), 640, 360)
    _radius(check, "Featured image", news.styles(news.FEAT_MEDIA, BORDER), 12)
    check.assert_clean()


@_meta("146328", "EN light desktop standard card matches Figma and omits Featured-only elements", "Listing UI")
@pytest.mark.ui
@pytest.mark.tc_146328
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_listing_standard_card(page):
    """Azure TC 146328 | PBI 131059 — card 424x338 r12, image 424x240 r10; title 18/700/28 #1D1D1B; meta date +
    views 14/400 #6C6C6B; no summary / read time / pill; 3 per row across 1320px."""
    check = _Check("TC 146328")
    news = NewsPage(page).open_listing()
    check.size("standard card", news.box(news.CARD), 424, 338)
    cs = news.styles(news.CARD, BORDER)
    if cs["background-color"] == "rgba(0, 0, 0, 0)" and cs["border-top-style"] == "none" and cs["box-shadow"] == "none":
        check.notes.append(f"UNMEASURED — card radius 12: the card has no painted surface (transparent, no border/shadow), "
                           f"so its radius ({cs['border-top-left-radius']}) is not observable")
    else:
        _radius(check, "standard card", cs, 12)
    check.size("card image", news.box(news.CARD_MEDIA), 424, 240)
    _radius(check, "card image", news.styles(news.CARD_MEDIA, BORDER), 10)
    check.typo("card title", news.styles(news.CARD_TITLE, TYPO), 18, 700, 28, "#1D1D1B")
    card = news.card_facts()[0]
    check.equals("card meta items", len(card["meta"]), 2)
    check.truthy("card meta = date + views", len(card["meta"]) >= 2 and EN_DATE.match(card["meta"][0]) and EN_VIEWS.match(card["meta"][1]),
                 "date, view count", card["meta"])
    check.data("card meta values", ["Mar 3, 2026", "2,847"], card["meta"][:2])
    check.typo("card meta", news.styles(f"{news.CARD} .qc-news-meta-item", TYPO), 14, 400, None, "#6C6C6B")
    check.truthy("no summary on standard card", not card["hasSummary"], "no summary", "summary present")
    check.truthy("no read time on standard card", not any("Min Read" in m for m in card["meta"]), "no read time", card["meta"])
    check.equals("no category pill on standard card", card["pills"], 0)
    first_row = [c for c in news.card_facts() if abs(c["y"] - card["y"]) < 2]
    check.equals("cards per row", len(first_row), 3)
    check.assert_clean()


@_meta("146329", "EN light desktop grid spacing and Load More match Figma", "Listing UI", MI)
@pytest.mark.ui
@pytest.mark.tc_146329
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_listing_grid_spacing_load_more(page):
    """Azure TC 146329 | PBI 131059 — 1320 content / 300px sides; 48px Featured->grid and row gaps; 40px filter->
    results; Load More 1320x48 white 1px #DEDEDD r9999, icon 15x17, 'Load More' 16/600 #4A4A49, 6px gap; footer
    (#911731) directly below."""
    check = _Check("TC 146329")
    news = NewsPage(page).open_listing()
    check.truthy("Load More present", news.count(news.LOAD_MORE) == 1, "button", 0)
    row = news.box(news.CONTROLS)
    check.px("content width", row["width"], 1320)
    check.px("side padding", row["x"], 300)
    f, g = news.box(news.FEATURED), news.box(news.GRID)
    check.px("gap filter -> results", f["y"] - (row["y"] + row["height"]), 40, 0.5)
    check.px("gap Featured -> grid", g["y"] - (f["y"] + f["height"]), 48, 0.5)
    cards = news.card_facts()
    rows = sorted({round(c["y"]) for c in cards})
    if len(rows) > 1:
        first = [c for c in cards if round(c["y"]) == rows[0]][0]
        check.px("row gap", rows[1] - (first["y"] + first["height"]), 48, 0.5)
    check.size("Load More", news.box(news.LOAD_MORE), 1320, 48)
    lm = news.styles(news.LOAD_MORE, BORDER + TYPO + ("column-gap",))
    check.color("Load More fill", lm["background-color"], "#FFFFFF")
    _border(check, "Load More", lm, "#DEDEDD")
    _radius(check, "Load More", lm, 9999, news.box(news.LOAD_MORE)["height"])
    check.equals("Load More label", news.text_of(news.LOAD_MORE), "Load More")
    check.typo("Load More label", lm, 16, 600, None, "#4A4A49")
    check.size("Load More icon", news.box(news.LOAD_MORE_ICON), 15, 17)
    check.px("Load More icon gap", lm["column-gap"], 6, 0.5)
    lb, ft = news.box(news.LOAD_MORE), news.box(news.FOOTER)
    fbg = news.styles(news.FOOTER, ("background-color", "background-image"))
    check.truthy("footer (#911731) follows below Load More", ft is not None and ft["y"] >= lb["y"] + lb["height"]
                 and ("145, 23, 49" in fbg["background-color"] + fbg["background-image"]), "#911731 footer below", fbg)
    check.assert_clean()


# ---------------------------------------------------------------------------
# EN light desktop details (146330, 146331, 146345)
# ---------------------------------------------------------------------------
@_meta("146330", "EN light desktop News Details header matches Figma", "Details UI")
@pytest.mark.ui
@pytest.mark.tc_146330
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_detail_header(page):
    """Azure TC 146330 | PBI 131059 — hero 'News Details' 30/700 #FFFFFF; image 1320x603 r12; title 48/700/60
    #1D1D1B; pill 'Collaboration' 114x36 #F6F6F6 r6 16/500 #4A4A49; meta date/views/'8 Min Read' 14/400 #6C6C6B,
    icons #A8A8A7."""
    check = _Check("TC 146330")
    news = NewsPage(page).open_detail(DETAIL_ID)
    check.equals("hero title", news.text_of(news.D_HERO_TITLE), "News Details")
    check.typo("hero title", news.styles(news.D_HERO_TITLE, TYPO), 30, 700, None, "#FFFFFF")
    check.size("article image", news.box(news.D_MEDIA), 1320, 603)
    _radius(check, "article image", news.styles(news.D_MEDIA, BORDER), 12)
    check.typo("article title", news.styles(news.D_TITLE, TYPO), 48, 700, 60, "#1D1D1B")
    check.equals("category pill", news.text_of(news.D_PILL), "Collaboration")
    check.size("category pill", news.box(news.D_PILL), 114, 36)
    ps = news.styles(news.D_PILL, BORDER + TYPO)
    check.color("pill fill", ps["background-color"], "#F6F6F6")
    _radius(check, "pill", ps, 6)
    check.typo("pill", ps, 16, 500, None, "#4A4A49")
    meta = news.texts(news.D_META_ITEM)
    check.equals("meta date", meta[0] if meta else None, "Mar 3, 2026")
    check.truthy("meta views format", len(meta) > 1 and bool(EN_VIEWS.match(meta[1])), "N,NNN", meta[1:2])
    check.data("meta view count", "2,847", meta[1] if len(meta) > 1 else None)
    check.equals("meta read time", meta[2] if len(meta) > 2 else None, "8 Min Read")
    for i in range(len(meta)):
        check.typo(f"meta item {i + 1}", news.styles(news.D_META_ITEM, TYPO, i), 14, 400, None, "#6C6C6B")
        ic = news.styles(news.D_META_ICON, ("stroke", "color"), i)
        check.truthy(f"meta icon {i + 1}", hex_to_rgb("#A8A8A7") in (ic["stroke"], ic["color"]), "#A8A8A7", ic)
    check.assert_clean()


@_meta("146331", "EN light desktop News Details body, keyword pills and Social Share match Figma", "Details UI")
@pytest.mark.ui
@pytest.mark.tc_146331
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_detail_body_tags_share(page):
    """Azure TC 146331 | PBI 131059 — body 20/400/30 #4A4A49; pills 36 high white 1px #DEDEDD r9999 14/600
    #4A4A49 ('Qatar' 62x36, 'Economic Planning' 141x36); divider 1320x1 #F6F6F6; 'Social Share:' 16/500
    #4A4A49 + 4 circular 36x36 #EDEDED buttons, icons 16x16 #4A4A49."""
    check = _Check("TC 146331")
    news = NewsPage(page).open_detail(DETAIL_ID)
    check.typo("body text", news.styles(news.D_BODY_P, TYPO), 20, 400, 30, "#4A4A49")
    tags = news.texts(news.D_TAG)
    check.equals("keyword pills", tags, ["Qatar", "Economic Planning", "Consultancy", "Turkey", "Planning"])
    for i, t in enumerate(tags):
        b = news.box(news.D_TAG, i)
        check.px(f"pill '{t}' height", b["height"], 36)
        st = news.styles(news.D_TAG, BORDER + TYPO, i)
        check.color(f"pill '{t}' fill", st["background-color"], "#FFFFFF")
        _border(check, f"pill '{t}'", st, "#DEDEDD")
        _radius(check, f"pill '{t}'", st, 9999, b["height"])
        check.typo(f"pill '{t}'", st, 14, 600, None, "#4A4A49")
        if t in ("Qatar", "Economic Planning"):
            check.size(f"pill '{t}'", b, {"Qatar": 62, "Economic Planning": 141}[t], 36)
    div = news.divider_above_share()
    if div is None:
        check.missing("divider above the Social Share row", "no <hr>, share-row border-top or tags border-bottom")
    else:
        check.px("divider thickness", div["px"], 1, 0.25)
        check.color("divider colour", div["color"], "#F6F6F6")
        check.px("divider width", div["width"], 1320)
    check.equals("share label", news.text_of(news.D_SHARE_LABEL), "Social Share:")
    check.typo("share label", news.styles(news.D_SHARE_LABEL, TYPO), 16, 500, None, "#4A4A49")
    check.equals("share buttons", news.count(news.D_SHARE_BTN), 4)
    for i in range(news.count(news.D_SHARE_BTN)):
        st = news.styles(news.D_SHARE_BTN, BORDER, i)
        check.size(f"share button {i + 1}", news.box(news.D_SHARE_BTN, i), 36, 36)
        check.truthy(f"share button {i + 1} circular", px_close(st["border-top-left-radius"], "18px", 0.5)
                     or st["border-top-left-radius"] in ("50%", "9999px"), "circle", st["border-top-left-radius"])
        check.color(f"share button {i + 1} fill", st["background-color"], "#EDEDED")
        check.size(f"share icon {i + 1}", news.box(news.D_SHARE_ICON, i), 16, 16)
        ic = news.styles(news.D_SHARE_ICON, ("color", "fill", "stroke"), i)
        check.truthy(f"share icon {i + 1} colour", hex_to_rgb("#4A4A49") in ic.values(), "#4A4A49", ic)
    check.assert_clean()


@_meta("146345", "News Details breadcrumb shows exactly Home, Insights & Media, News", "Details UI", MI)
@pytest.mark.ui
@pytest.mark.tc_146345
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_detail_breadcrumb(page):
    """Azure TC 146345 | PBI 131059 — hero 'News Details'; breadcrumb exactly 3 items separated by chevrons."""
    check = _Check("TC 146345")
    news = NewsPage(page).open_detail(DETAIL_ID)
    check.equals("hero title", news.text_of(news.D_HERO_TITLE), "News Details")
    check.equals("breadcrumb items", news.texts(news.D_CRUMB_ITEMS), ["Home", "Insights & Media", "News"])
    check.equals("chevron separators", news.count(news.D_CRUMB_SEP), 2)
    check.assert_clean()


# ---------------------------------------------------------------------------
# Arabic desktop (146332-146334)
# ---------------------------------------------------------------------------
def _rtl(check, news, locs):
    check.equals("html dir", news.document_dir(), "rtl")
    for name, loc in locs:
        s = news.styles(loc, ("direction", "text-align", "font-family"))
        check.truthy(f"{name} right-aligned RTL", s["direction"] == "rtl" and s["text-align"] in ("start", "right"),
                     "rtl/right", (s["direction"], s["text-align"]))
        check.truthy(f"{name} Cairo", "cairo" in s["font-family"].lower(), "Cairo", s["font-family"])


@_meta("146332", "AR light desktop listing header and filter bar render RTL", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146332
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_ar_listing_header_filters(page):
    """Azure TC 146332 | PBI 131059 — /ar: rtl; hero 'الأخبار والبيانات الصحفية' 30/700 #FFFFFF; breadcrumb from
    the right 'الرئيسية' then 'الرؤى والإعلام', chevrons mirrored; search at the right edge with Arabic placeholder,
    category/sort to its left with chevrons on the left; Load More 'تحميل المزيد' 16/600 #4A4A49 1320x48."""
    check = _Check("TC 146332")
    news = NewsPage(page).open_listing(locale="ar")
    _rtl(check, news, (("hero title", news.HERO_TITLE), ("card title", news.CARD_TITLE)))
    check.equals("hero title", news.text_of(news.HERO_TITLE), "الأخبار والبيانات الصحفية")
    check.typo("hero title", news.styles(news.HERO_TITLE, TYPO), 30, 700, None, "#FFFFFF")
    items = news.texts(news.CRUMB_ITEMS)
    check.equals("breadcrumb first two items", items[:2], ["الرئيسية", "الرؤى والإعلام"])
    boxes = news.boxes(news.CRUMB_ITEMS)
    check.truthy("breadcrumb starts at the right", len(boxes) > 1 and boxes[0]["x"] > boxes[1]["x"], "first item rightmost",
                 [round(b["x"]) for b in boxes])
    sep = news.styles(news.CRUMB_SEP, ("transform",))
    check.truthy("breadcrumb chevrons mirrored", sep["transform"].startswith("matrix(-1"), "scaleX(-1)", sep["transform"])
    s, c, t = news.box(news.SEARCH_FIELD), news.box(news.CATEGORY_FIELD), news.box(news.SORT_FIELD)
    check.truthy("search at the right edge, category and sort to its left", s["x"] > c["x"] > t["x"], "search > category > sort (x)",
                 (round(s["x"]), round(c["x"]), round(t["x"])))
    check.equals("search placeholder", news.attribute(news.SEARCH_INPUT, "placeholder"), "البحث في الأخبار والبيانات الصحفية...")
    for name, sel, chev in (("category", news.CATEGORY, news.CATEGORY_CHEV), ("sort", news.SORT, news.SORT_CHEV)):
        sb, cb = news.box(sel), news.box(chev)
        check.truthy(f"{name} chevron on the left", cb["x"] + cb["width"] / 2 < sb["x"] + sb["width"] / 2, "left half", (cb, sb))
    check.equals("category label", news.selected_label(news.CATEGORY), "جميع الفئات")
    check.equals("sort label", news.selected_label(news.SORT), "الأحدث")
    check.equals("Load More label", news.text_of(news.LOAD_MORE), "تحميل المزيد")
    check.typo("Load More label", news.styles(news.LOAD_MORE, TYPO), 16, 600, None, "#4A4A49")
    check.size("Load More", news.box(news.LOAD_MORE), 1320, 48)
    check.assert_clean()


@_meta("146333", "AR light desktop Featured card renders RTL with localized pills and meta", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146333
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_ar_featured_card(page):
    """Azure TC 146333 | PBI 131059 — pills 'مميز' 50x36 / 'التجارة والاقتصاد' 125x36 #F6F6F6 r6 16/400 #6C6C6B;
    title 30/700 #343432, summary 18/400 #4A4A49 right-aligned; Arabic date, views and 'N دقائق قراءة'; Featured and
    standard view counts use the same thousands format."""
    check = _Check("TC 146333")
    news = NewsPage(page).open_listing(locale="ar")
    pills = news.texts(news.FEAT_PILL)
    check.equals("Featured pills (tashkeel-insensitive)", [_ar(p) for p in pills], ["مميز", "التجارة والاقتصاد"])
    for i, (w, h) in enumerate(((50, 36), (125, 36))[:len(pills)]):
        check.size(f"pill {i + 1}", news.box(news.FEAT_PILL, i), w, h)
        st = news.styles(news.FEAT_PILL, BORDER + TYPO)
        check.color(f"pill {i + 1} fill", st["background-color"], "#F6F6F6")
        _radius(check, f"pill {i + 1}", st, 6)
        check.typo(f"pill {i + 1}", st, 16, 400, None, "#6C6C6B")
    _rtl(check, news, (("Featured title", news.FEAT_TITLE), ("Featured summary", news.FEAT_SUMMARY)))
    check.typo("Featured title", news.styles(news.FEAT_TITLE, TYPO), 30, 700, None, "#343432")
    check.typo("Featured summary", news.styles(news.FEAT_SUMMARY, TYPO), 18, 400, None, "#4A4A49")
    meta = news.texts(news.FEAT_META_ITEM)
    check.truthy("Arabic date (e.g. '3 مارس 2026')", len(meta) > 0 and bool(re.fullmatch(r"\d{1,2} [؀-ۿ]+ \d{4}", meta[0])),
                 "D <Arabic month> YYYY", meta[:1])
    check.data("Featured date", "3 مارس 2026", meta[0] if meta else None)
    check.truthy("Arabic read time", len(meta) > 2 and "دقائق قراءة" in meta[2] and "Min Read" not in meta[2], "N دقائق قراءة", meta[2:3])
    std = news.card_facts()[0]["meta"]
    sep = lambda v: "٬" if "٬" in v else ("," if "," in v else "none")  # noqa: E731
    if len(meta) > 1 and len(std) > 1:
        check.equals("same thousands format Featured vs standard", sep(meta[1]), sep(std[1]))
    check.assert_clean()


@_meta("146334", "AR News Details renders RTL with mirrored layout", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146334
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_ar_detail_rtl(page):
    """Azure TC 146334 | PBI 131059 — /ar detail: rtl, title/pill/meta/body right-aligned Cairo; pill at the right
    end ABOVE the title; meta icons mirrored (icon at the right of its text); keyword pills flow right-to-left;
    'Social Share' label at the right, buttons leftwards; no English UI strings."""
    check = _Check("TC 146334")
    news = NewsPage(page).open_detail(DETAIL_ID, locale="ar")
    _rtl(check, news, (("title", news.D_TITLE), ("body", news.D_BODY_P), ("pill", news.D_PILL)))
    art, pill, title = news.box(news.D_ARTICLE), news.box(news.D_PILL), news.box(news.D_TITLE)
    check.truthy("pill at the right end", abs((pill["x"] + pill["width"]) - (art["x"] + art["width"])) <= 2, "right edge",
                 (pill, art))
    check.truthy("pill above the title", pill["y"] + pill["height"] <= title["y"] + 1, "above", (round(pill["y"]), round(title["y"])))
    for i in range(news.count(news.D_META_ITEM)):
        ib, tb = news.box(news.D_META_ICON, i), news.box(f"{news.D_META_ITEM} .qc-newsd-ltr", i)
        if ib and tb:
            check.truthy(f"meta icon {i + 1} mirrored (right of its text)", ib["x"] > tb["x"], "icon right of text", (ib["x"], tb["x"]))
    tags = news.boxes(news.D_TAG)
    check.truthy("keyword pills flow right-to-left", all(tags[i]["x"] > tags[i + 1]["x"] for i in range(len(tags) - 1)
                                                         if abs(tags[i]["y"] - tags[i + 1]["y"]) < 2), "decreasing x", [round(t["x"]) for t in tags])
    lb, bb = news.box(news.D_SHARE_LABEL), news.boxes(news.D_SHARE_BTN)
    check.truthy("share label at the right, buttons leftwards", bb and lb["x"] > max(b["x"] for b in bb), "label rightmost",
                 (round(lb["x"]), [round(b["x"]) for b in bb]))
    ui = [news.text_of(news.D_HERO_TITLE), news.text_of(news.D_SHARE_LABEL), news.text_of(news.D_PILL)] + news.texts(news.D_CRUMB_ITEMS)
    check.truthy("no English UI strings", all(ARABIC.search(t) for t in ui if t), "Arabic", [t for t in ui if t and not ARABIC.search(t)])
    check.assert_clean()


# ---------------------------------------------------------------------------
# Mobile (146335, 146336, 146340)
# ---------------------------------------------------------------------------
@_meta("146335", "EN mobile News listing matches the Figma 390px design", "Mobile UI")
@pytest.mark.ui
@pytest.mark.tc_146335
@pytest.mark.parametrize("page", [M390], indirect=True)
def test_mobile_listing(page):
    """Azure TC 146335 | PBI 131059 — header 390x72; hero 390x124, title 20/700/30 #FFFFFF; side padding 20; search
    350x44; category 167x44 + sort 167x46 side by side, 12px gap; Featured image 350x240, title 16/700/24 #1D1D1B,
    summary 14/400/22 #4A4A49, pills 36 high; standard cards 350x290 (image 350x200); Load More 350x48; no h-scroll."""
    check = _Check("TC 146335")
    news = NewsPage(page).open_listing()
    check.size("header", news.box(news.HEADER), 390, 72)
    check.size("hero", news.box(news.HERO), 390, 124)
    check.typo("hero title", news.styles(news.HERO_TITLE, TYPO), 20, 700, 30, "#FFFFFF")
    row = news.box(news.CONTROLS)
    check.px("page side padding", row["x"], 20)
    check.size("search input", news.box(news.SEARCH_INPUT), 350, 44)
    c, t = news.box(news.CATEGORY), news.box(news.SORT)
    check.size("category", c, 167, 44)
    check.size("sort", t, 167, 46)
    check.truthy("category and sort side by side", abs(c["y"] - t["y"]) <= 2, "same row", (c["y"], t["y"]))
    check.px("category/sort gap", t["x"] - (c["x"] + c["width"]), 12, 0.5)
    check.size("Featured image", news.box(news.FEAT_IMG), 350, 240)
    check.typo("Featured title", news.styles(news.FEAT_TITLE, TYPO), 16, 700, 24, "#1D1D1B")
    check.typo("Featured summary", news.styles(news.FEAT_SUMMARY, TYPO), 14, 400, 22, "#4A4A49")
    for i in range(news.count(news.FEAT_PILL)):
        check.px(f"pill {i + 1} height", news.box(news.FEAT_PILL, i)["height"], 36)
    cards = news.card_facts()
    check.truthy("standard cards single column", len({round(x["x"]) for x in cards}) == 1, "one column", sorted({round(x["x"]) for x in cards}))
    check.size("standard card", news.box(news.CARD), 350, 290)
    check.size("standard card image", news.box(news.CARD_IMG), 350, 200)
    check.size("Load More", news.box(news.LOAD_MORE), 350, 48)
    _no_overflow(check, news)
    check.assert_clean()


@_meta("146336", "EN mobile News Details is single-column without horizontal scroll", "Mobile UI")
@pytest.mark.ui
@pytest.mark.tc_146336
@pytest.mark.parametrize("page", [M390], indirect=True)
def test_mobile_detail(page):
    """Azure TC 146336 | PBI 131059 — image spans the 350px content width; title < 48px and wraps within the width;
    keyword pills wrap; scrollWidth == 390; 4 share buttons each >= 36x36."""
    check = _Check("TC 146336")
    news = NewsPage(page).open_detail(DETAIL_ID)
    img = news.box(news.D_IMG)
    check.px("image width", img["width"] if img else None, 350)
    ts = news.styles(news.D_TITLE, ("font-size",))
    tb = news.box(news.D_TITLE)
    check.truthy("title smaller than 48px", float(ts["font-size"].rstrip("px")) < 48, "< 48px", ts["font-size"])
    check.truthy("title within the width", tb["x"] >= 0 and tb["x"] + tb["width"] <= 391, "inside 390px", tb)
    tags = news.boxes(news.D_TAG)
    check.truthy("keyword pills wrap onto multiple lines", len({round(t["y"]) for t in tags}) > 1, "> 1 line", sorted({round(t["y"]) for t in tags}))
    check.equals("scrollWidth", news.scroll_width(), 390)
    btns = news.boxes(news.D_SHARE_BTN)
    check.equals("share buttons", len(btns), 4)
    for i, b in enumerate(btns):
        check.truthy(f"share button {i + 1} >= 36x36", b["width"] >= 36 and b["height"] >= 36, ">= 36x36", b)
    check.assert_clean()


@_meta("146340", "AR mobile News listing renders RTL at 390px without overflow", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146340
@pytest.mark.parametrize("page", [M390], indirect=True)
def test_ar_mobile_listing(page):
    """Azure TC 146340 | PBI 131059 — /ar 390: rtl; search full width, placeholder right-aligned; category/sort side
    by side; cards single column, titles right-aligned; no h-scroll; 'تحميل المزيد' centred at full width."""
    check = _Check("TC 146340")
    news = NewsPage(page).open_listing(locale="ar")
    check.equals("html dir", news.document_dir(), "rtl")
    row, s = news.box(news.CONTROLS), news.box(news.SEARCH_INPUT)
    check.px("search full width", s["width"], row["width"])
    ph = news.styles(news.SEARCH_INPUT, ("direction", "text-align"), pseudo="::placeholder")
    check.truthy("placeholder right-aligned", ph["direction"] == "rtl" and ph["text-align"] in ("start", "right"), "rtl/right", ph)
    c, t = news.box(news.CATEGORY), news.box(news.SORT)
    check.truthy("category and sort side by side", abs(c["y"] - t["y"]) <= 2, "same row", (c["y"], t["y"]))
    cards = news.card_facts()
    check.truthy("cards single column", len({round(x["x"]) for x in cards}) == 1, "one column", sorted({round(x["x"]) for x in cards}))
    for i, x in enumerate(cards):
        check.truthy(f"card {i + 1} title right-aligned", x["titleDir"] == "rtl" and x["titleAlign"] in ("start", "right"), "rtl/right",
                     (x["titleDir"], x["titleAlign"]))
    _no_overflow(check, news)
    check.equals("Load More label", news.text_of(news.LOAD_MORE), "تحميل المزيد")
    lb = news.box(news.LOAD_MORE)
    check.px("Load More full content width", lb["width"], row["width"])
    check.truthy("Load More label centred", news.styles(news.LOAD_MORE, ("justify-content",))["justify-content"] in ("center", "normal")
                 or news.styles(news.LOAD_MORE, ("text-align",))["text-align"] == "center", "centred",
                 news.styles(news.LOAD_MORE, ("justify-content", "text-align")))
    check.assert_clean()


# ---------------------------------------------------------------------------
# Dark palette (146337-146339)
# ---------------------------------------------------------------------------
def _icon_colour(st):
    return {st.get("color"), st.get("stroke"), st.get("fill")}


@_meta("146337", "EN dark desktop News listing uses the Figma dark palette", "Dark theme")
@pytest.mark.ui
@pytest.mark.tc_146337
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_dark_listing_palette(page):
    """Azure TC 146337 | PBI 131059 — page/header #1D1D1B, header buttons #4A4A49; inputs fill #1D1D1B, 1px
    #4A4A49, label #F6F6F6, placeholder #A8A8A7, search icon #C44561; pills #343432 / text #DEDEDD; Featured
    title #F6F6F6, summary #EDEDED, meta #DEDEDD; card titles #FFFFFF; Load More #1D1D1B, 1px #6C6C6B, label/icon
    #EDEDED."""
    check = _Check("TC 146337")
    news = NewsPage(page).open_listing().enable_dark_mode()
    check.color("page background", news.styles(news.PAGE_BODY, ("background-color",))["background-color"], "#1D1D1B")
    check.color("header background", news.styles(news.HEADER, ("background-color",))["background-color"], "#1D1D1B")
    for i in range(news.count(news.HEADER_ICON_BUTTONS)):
        check.color(f"header button {i + 1} fill", news.styles(news.HEADER_ICON_BUTTONS, ("background-color",), i)["background-color"], "#4A4A49")
    for name, field, sel in (("search", news.SEARCH_FIELD, news.SEARCH_INPUT),
                             ("category", news.CATEGORY_FIELD, news.CATEGORY), ("sort", news.SORT_FIELD, news.SORT)):
        st = news.styles(field, BORDER)
        check.color(f"{name} fill", st["background-color"], "#1D1D1B")
        _border(check, name, st, "#4A4A49")
        if name != "search":
            check.color(f"{name} label", news.styles(sel, ("color",))["color"], "#F6F6F6")
    check.color("search placeholder", news.styles(news.SEARCH_INPUT, ("color",), pseudo="::placeholder")["color"], "#A8A8A7")
    check.truthy("search icon #C44561", hex_to_rgb("#C44561") in _icon_colour(news.styles(news.SEARCH_ICON, ("color", "stroke", "fill"))),
                 "#C44561", news.styles(news.SEARCH_ICON, ("color", "stroke", "fill")))
    for i in range(news.count(news.FEAT_PILL)):
        st = news.styles(news.FEAT_PILL, ("background-color", "color"), i)
        check.color(f"pill {i + 1} fill", st["background-color"], "#343432")
        check.color(f"pill {i + 1} text", st["color"], "#DEDEDD")
    check.color("Featured title", news.styles(news.FEAT_TITLE, ("color",))["color"], "#F6F6F6")
    check.color("Featured summary", news.styles(news.FEAT_SUMMARY, ("color",))["color"], "#EDEDED")
    check.color("Featured meta", news.styles(news.FEAT_META_ITEM, ("color",))["color"], "#DEDEDD")
    for i in range(news.count(news.CARD_TITLE)):
        check.color(f"card title {i + 1}", news.styles(news.CARD_TITLE, ("color",), i)["color"], "#FFFFFF")
    lm = news.styles(news.LOAD_MORE, BORDER + ("color",))
    check.color("Load More fill", lm["background-color"], "#1D1D1B")
    _border(check, "Load More", lm, "#6C6C6B")
    check.color("Load More label", lm["color"], "#EDEDED")
    check.truthy("Load More icon #EDEDED", hex_to_rgb("#EDEDED") in _icon_colour(news.styles(news.LOAD_MORE_ICON, ("color", "stroke", "fill"))),
                 "#EDEDED", news.styles(news.LOAD_MORE_ICON, ("color", "stroke", "fill")))
    check.assert_clean()


@_meta("146338", "AR dark desktop News listing renders RTL with the dark palette", "Dark theme")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146338
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_ar_dark_listing(page):
    """Azure TC 146338 | PBI 131059 — /ar dark: rtl, page #1D1D1B; card titles light on dark with contrast >= 4.5:1,
    meta light grey; nothing dark-on-dark."""
    check = _Check("TC 146338")
    news = NewsPage(page).open_listing(locale="ar").enable_dark_mode()
    check.equals("html dir", news.document_dir(), "rtl")
    check.color("page background", news.styles(news.PAGE_BODY, ("background-color",))["background-color"], "#1D1D1B")
    for sel, name in ((news.CARD_TITLE, "card title"), (news.CARD_META, "card meta"), (news.FEAT_TITLE, "Featured title")):
        for i in range(news.count(sel)):
            c = news.contrast(sel, i)
            check.truthy(f"{name} {i + 1} contrast", c["ratio"] >= AA, f">= {AA}:1", f"{c['ratio']}:1 ({c['color']} on {c['background']})")
    check.assert_clean()


@_meta("146339", "EN dark desktop News Details is legible on the dark palette", "Dark theme")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146339
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_dark_detail_legible(page):
    """Azure TC 146339 | PBI 131059 — dark detail: page #1D1D1B; title/body contrast >= 4.5:1; keyword pills and
    share buttons distinguishable from the background; no element keeps the light #FFFFFF background."""
    check = _Check("TC 146339")
    news = NewsPage(page).open_detail(DETAIL_ID).enable_dark_mode()
    check.color("page background", news.styles(news.PAGE_BODY, ("background-color",))["background-color"], "#1D1D1B")
    for sel, name in ((news.D_TITLE, "title"), (news.D_BODY_P, "body")):
        c = news.contrast(sel)
        check.truthy(f"{name} contrast", c["ratio"] >= AA, f">= {AA}:1", f"{c['ratio']}:1 ({c['color']} on {c['background']})")
    page_bg = hex_to_rgb("#1D1D1B")
    for sel, name in ((news.D_TAG, "keyword pill"), (news.D_SHARE_BTN, "share button")):
        for i in range(news.count(sel)):
            st = news.styles(sel, BORDER, i)
            ring = RING.match(st["box-shadow"] or "")
            visible = st["background-color"] not in (page_bg, "rgba(0, 0, 0, 0)") or (
                st["border-top-style"] != "none" and st["border-top-color"] != page_bg) or bool(ring and ring.group(1) != page_bg)
            check.truthy(f"{name} {i + 1} distinguishable", visible, "own fill or border", st)
    check.equals("elements keeping #FFFFFF background", news.white_backgrounds(news.D_ARTICLE), [])
    check.assert_clean()


# ---------------------------------------------------------------------------
# Keyboard (146341)
# ---------------------------------------------------------------------------
@_meta("146341", "Keyboard focus is visible and operable on the News listing controls", "Accessibility")
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.tc_146341
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_keyboard_focus(page):
    """Azure TC 146341 | PBI 131059 — Tab order search, category, sort, Featured, standard cards, Load More; each
    focused control has an outline >= 2px with >= 3:1 contrast; Enter on the Featured card opens its detail."""
    check = _Check("TC 146341")
    news = NewsPage(page).open_listing()
    order = [("search input", lambda i: "qc-news-search-input" in i["cls"]),
             ("search button", lambda i: "qc-news-search-btn" in i["cls"]),
             ("category", lambda i: i["tag"] == "select"),
             ("sort", lambda i: i["tag"] == "select"),
             ("Featured card", lambda i: "qc-news-feat-card" in i["cls"])]
    got = []
    for name, pred in order:
        n, info = news.tab_until(pred, max_presses=60 if not got else 6)
        got.append(name if n else f"{name} (not reached)")
        if n is None:
            check.truthy(f"Tab reaches {name}", False, "reached in order", got)
            continue
        wide = info["outlineStyle"] != "none" and px_close(info["outlineWidth"], "2px", 0.0) or (
            info["outlineStyle"] != "none" and float(info["outlineWidth"].rstrip("px")) >= 2)
        check.truthy(f"{name} outline >= 2px", info["focusVisible"] and wide, ">= 2px", f"{info['outlineStyle']} {info['outlineWidth']}")
        check.truthy(f"{name} outline contrast >= 3:1", news.outline_contrast() >= 3, ">= 3:1", news.outline_contrast())
        if name == "Featured card":
            featured_href = info["href"]
    n, info = news.tab_until(lambda i: "qc-news-card" in i["cls"] and "feat" not in i["cls"], max_presses=4)
    check.truthy("next Tab reaches the first standard card", n is not None, "standard card", info)
    if n:
        check.truthy("standard card outline >= 2px", info["outlineStyle"] != "none" and float(info["outlineWidth"].rstrip("px")) >= 2,
                     ">= 2px", f"{info['outlineStyle']} {info['outlineWidth']}")
    n, info = news.tab_until(lambda i: "qc-news-more" in i["cls"], max_presses=12)
    check.truthy("Tab reaches Load More after the cards", n is not None, "Load More", info)
    if n:
        check.truthy("Load More outline >= 2px", info["outlineStyle"] != "none" and float(info["outlineWidth"].rstrip("px")) >= 2,
                     ">= 2px", f"{info['outlineStyle']} {info['outlineWidth']}")
    news.open_listing()
    n, info = news.tab_until(lambda i: "qc-news-feat-card" in i["cls"], max_presses=60)
    if n:
        before = news.current_url()
        news.press("Enter")
        try:
            news.wait_for_url(lambda u: u != before and "news-detail" in u, timeout=20000)
        except Exception:  # noqa: BLE001
            pass
        check.truthy("Enter opens the Featured detail", "news-detail" in news.current_url(), "news-detail?id=…", news.current_url())
    check.assert_clean()


# ---------------------------------------------------------------------------
# Compatibility (146346-146351, 146353, 146354)
# ---------------------------------------------------------------------------
@_meta("146346", "News listing renders correctly on a 1920x1080 desktop viewport", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146346
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_desktop_1920(page):
    """Azure TC 146346 | PBI 131059 — Featured then a 3-column grid; no h-scroll; filter bar, cards and Load More
    fully visible with no overlap or clipping."""
    check = _Check("TC 146346")
    news = NewsPage(page).open_listing()
    cards = news.card_facts()
    check.equals("grid columns", len({round(c["x"]) for c in cards}), 3)
    _no_overflow(check, news)
    blocks = {"filter bar": news.box(news.CONTROLS), "Featured": news.box(news.FEATURED), "grid": news.box(news.GRID),
              "Load More": news.box(news.LOAD_MORE)}
    names = list(blocks)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            check.truthy(f"{names[i]}/{names[j]} overlap", not _overlap(blocks[names[i]], blocks[names[j]]), "no overlap", "overlap")
    for i, c in enumerate(cards):
        check.truthy(f"card {i + 1} not clipped", not c["clipped"], "unclipped", "clipped")
    check.assert_clean()


@_meta("146347", "News listing reflows without overflow on a 768x1024 tablet viewport", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146347
@pytest.mark.parametrize("page", [T768], indirect=True)
def test_tablet_768(page):
    """Azure TC 146347 | PBI 131059 — fewer columns than desktop, no overlap/h-scroll; controls within width and
    >= 44px high; search 'Maritime' and Load More work."""
    check = _Check("TC 146347")
    news = NewsPage(page).open_listing()
    _no_overflow(check, news)
    cards = news.card_facts()
    check.truthy("fewer columns than desktop", len({round(c["x"]) for c in cards}) < 3, "< 3", len({round(c["x"]) for c in cards}))
    for i in range(len(cards) - 1):
        check.truthy(f"card {i + 1}/{i + 2} no overlap", not _overlap(cards[i], cards[i + 1]), "no overlap", "overlap")
    for name, sel in (("search", news.SEARCH_INPUT), ("category", news.CATEGORY), ("sort", news.SORT)):
        b = news.box(sel)
        check.truthy(f"{name} inside 768px", b["x"] >= 0 and b["x"] + b["width"] <= 769, "inside", b)
        check.truthy(f"{name} >= 44px high", b["height"] >= 44, ">= 44px", b["height"])
    items = _items_by_id(news)
    news.search("Maritime")
    ids = news.listed_ids()
    check.truthy("search returns results", len(ids) > 0, ">= 1", 0)
    check.truthy("search results all match 'Maritime'", all(_matches(items.get(i, {}), "Maritime") for i in ids), "only matches",
                 [items.get(i, {}).get("title") for i in ids if not _matches(items.get(i, {}), "Maritime")])
    news.clear_search()
    before = len(news.listed_ids())
    news.load_more()
    check.truthy("Load More appends cards", len(news.listed_ids()) > before, f"> {before}", len(news.listed_ids()))
    check.assert_clean()


@_meta("146348", "News listing search, filter and Load More work on a 390x844 mobile viewport", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146348
@pytest.mark.parametrize("page", [M390], indirect=True)
def test_mobile_390_functions(page):
    """Azure TC 146348 | PBI 131059 — search 'Maritime' -> only matches; category 'Trade & Economy' -> only tagged;
    clear both + Load More appends; no h-scroll at any step."""
    check = _Check("TC 146348")
    news = NewsPage(page).open_listing()
    items = _items_by_id(news)
    _no_overflow(check, news)
    news.search("Maritime")
    ids = news.listed_ids()
    check.truthy("search results all match 'Maritime'", ids and all(_matches(items.get(i, {}), "Maritime") for i in ids), "only matches",
                 [items.get(i, {}).get("title") for i in ids])
    _no_overflow(check, news)
    news.clear_search()
    news.select_category("tradeAndEconomy")
    ids = news.listed_ids()
    check.truthy("category results all tagged Trade & Economy", ids and all("tradeAndEconomy" in items.get(i, {}).get("categoryTags", "") for i in ids),
                 "only tagged", [items.get(i, {}).get("categoryTags") for i in ids])
    _no_overflow(check, news)
    news.select_category("all")
    before = len(news.listed_ids())
    news.load_more()
    check.truthy("Load More appends cards", len(news.listed_ids()) > before, f"> {before}", len(news.listed_ids()))
    _no_overflow(check, news)
    check.assert_clean()


def _browser_flow(check: _Check, pg, label: str):
    news = NewsPage(pg).open_listing()
    check.equals(f"{label}: console errors on load", pg.console_errors, [])
    items = _items_by_id(news)
    news.search("Maritime")
    ids = news.listed_ids()
    check.truthy(f"{label}: search results all match 'Maritime'", ids and all(_matches(items.get(i, {}), "Maritime") for i in ids),
                 "only matches", [items.get(i, {}).get("title") for i in ids])
    news.clear_search()
    news.select_sort("views")
    views = [items.get(i, {}).get("totalViews", -1) for i in news.listed_ids()]
    check.truthy(f"{label}: 'Most Viewed' orders by views descending", views == sorted(views, reverse=True), "descending", views)
    news.mark_document()
    before = len(news.listed_ids())
    errors_before = len(pg.console_errors)
    news.load_more()
    check.truthy(f"{label}: Load More appends cards", len(news.listed_ids()) > before, f"> {before}", len(news.listed_ids()))
    check.truthy(f"{label}: no page reload on Load More", news.document_marked(), "same document", "reloaded")
    check.equals(f"{label}: console errors after Load More", pg.console_errors[errors_before:], [])


@_meta("146349", "News listing search, sort and Load More work on Chrome latest", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146349
@pytest.mark.parametrize("engine_page", [{"engine": "chromium", "channel": "chrome"}], indirect=True)
def test_chrome(engine_page):
    """Azure TC 146349 | PBI 131059 — Chrome (channel=chrome), 1920x1080."""
    check = _Check("TC 146349")
    _browser_flow(check, engine_page, "Chrome")
    check.assert_clean()


@_meta("146350", "News listing search, sort and Load More work on Edge latest", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146350
@pytest.mark.parametrize("engine_page", [{"engine": "chromium", "channel": "msedge"}], indirect=True)
def test_edge(engine_page):
    """Azure TC 146350 | PBI 131059 — Edge (channel=msedge), 1920x1080."""
    check = _Check("TC 146350")
    _browser_flow(check, engine_page, "Edge")
    check.assert_clean()


@_meta("146351", "News listing search, sort and Load More work on Firefox latest", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146351
@pytest.mark.parametrize("engine_page", [{"engine": "firefox"}], indirect=True)
def test_firefox(engine_page):
    """Azure TC 146351 | PBI 131059 — Firefox (Playwright firefox), 1920x1080."""
    check = _Check("TC 146351")
    _browser_flow(check, engine_page, "Firefox")
    check.assert_clean()


@_meta("146353", "News listing and detail render correctly in the light theme", "Theme")
@pytest.mark.compatibility
@pytest.mark.tc_146353
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_light_theme(page):
    """Azure TC 146353 | PBI 131059 — listing bg #FFFFFF, body text #343432/#1D1D1B; Featured detail bg #FFFFFF,
    title #1D1D1B; Back keeps the light theme."""
    check = _Check("TC 146353")
    news = NewsPage(page).open_listing()
    check.truthy("light theme", news.theme() in (None, "light"), "light", news.theme())
    check.color("listing background", news.styles(news.PAGE_BODY, ("background-color",))["background-color"], "#FFFFFF")
    for sel, name in ((news.FEAT_TITLE, "Featured title"), (news.CARD_TITLE, "card title")):
        col = news.styles(sel, ("color",))["color"]
        check.truthy(f"{name} colour", col in (hex_to_rgb("#343432"), hex_to_rgb("#1D1D1B")), "#343432 or #1D1D1B", col)
    news.open_featured()
    check.color("detail background", news.styles(news.PAGE_BODY, ("background-color",))["background-color"], "#FFFFFF")
    check.color("detail title", news.styles(news.D_TITLE, ("color",))["color"], "#1D1D1B")
    news.go_back()
    check.truthy("light theme after Back", news.theme() in (None, "light"), "light", news.theme())
    check.color("listing background after Back", news.styles(news.PAGE_BODY, ("background-color",))["background-color"], "#FFFFFF")
    check.assert_clean()


@_meta("146354", "Dark theme persists from the News listing to the detail page", "Theme")
@pytest.mark.compatibility
@pytest.mark.tc_146354
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_dark_theme_persists(page):
    """Azure TC 146354 | PBI 131059 — dark on the listing (#1D1D1B) -> Featured detail opens dark -> still dark after
    reload."""
    check = _Check("TC 146354")
    news = NewsPage(page).open_listing().enable_dark_mode()
    check.color("listing background", news.styles(news.PAGE_BODY, ("background-color",))["background-color"], "#1D1D1B")
    news.open_featured()
    check.equals("detail theme", news.theme(), "dark")
    check.color("detail background", news.styles(news.PAGE_BODY, ("background-color",))["background-color"], "#1D1D1B")
    news.reload()
    news.wait_detail()
    check.equals("theme after reload", news.theme(), "dark")
    check.color("detail background after reload", news.styles(news.PAGE_BODY, ("background-color",))["background-color"], "#1D1D1B")
    check.assert_clean()


# ---------------------------------------------------------------------------
# Bilingual functional (146367, 146473, 146474, 146479)
# ---------------------------------------------------------------------------
@_meta("146367", "Public Visitor can browse, filter and read a published news article in Arabic", "Bilingual", allure.severity_level.BLOCKER)
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.uat
@pytest.mark.tc_146367
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_ar_browse_filter_read(page):
    """Azure TC 146367 | PBI 131059 — /ar -> header Media Center > News -> RTL Arabic titles -> category
    'التجارة والاقتصاد' -> open the Trade Forum article (substitution, see module docstring) -> Arabic detail under /ar
    with Arabic title/body/pill/meta."""
    check = _Check("TC 146367")
    news = NewsPage(page).open_home(locale="ar")
    if not news.navigate_to_listing_via_menu():
        check.truthy("header menu reaches the News listing", False, "Media Center > News link", "not found")
        news.open_listing(locale="ar")
    check.truthy("listing under /ar", "/ar/" in news.current_url(), "/ar/…/news-archive", news.current_url())
    check.equals("html dir", news.document_dir(), "rtl")
    check.truthy("Arabic titles", all(ARABIC.search(t) for t in news.card_titles()), "Arabic", [t for t in news.card_titles() if not ARABIC.search(t)])
    items = _items_by_id(news, "ar")
    news.select_category("tradeAndEconomy")
    check.equals("category label", _ar(news.selected_label(news.CATEGORY)), "التجارة والاقتصاد")
    ids = news.listed_ids()
    check.truthy("only 'التجارة والاقتصاد' articles remain", ids and all("tradeAndEconomy" in items.get(i, {}).get("categoryTags", "") for i in ids),
                 "only tagged", [items.get(i, {}).get("title") for i in ids if "tradeAndEconomy" not in items.get(i, {}).get("categoryTags", "")])
    seeded = [i for i, it in items.items() if "QCTEST-131059" in it.get("title", "")]
    check.data("seeded article 'QCTEST-131059 منتدى التجارة'", "published", "not published" if not seeded else "published")
    target = seeded[0] if seeded else FEATURED_AR_ID
    news.open_card(target)
    check.truthy("detail keeps the /ar prefix", "/ar/" in news.current_url(), "/ar/…", news.current_url())
    check.equals("detail title (AR value)", news.text_of(news.D_TITLE), items.get(target, {}).get("title", "").strip())
    check.truthy("detail body Arabic", bool(ARABIC.search(news.text_of(news.D_CONTENT))), "Arabic", news.text_of(news.D_CONTENT)[:60])
    check.truthy("detail pill Arabic", bool(ARABIC.search(news.text_of(news.D_PILL))), "Arabic", news.text_of(news.D_PILL))
    meta = news.texts(news.D_META_ITEM)
    check.truthy("detail meta Arabic (date and read time)", len(meta) > 2 and ARABIC.search(meta[0]) and "دقائق قراءة" in meta[2],
                 "Arabic date / read time", meta)
    check.assert_clean()


@_meta("146473", "Searching an Arabic keyword on the /ar listing returns Arabic matches", "Bilingual")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_146473
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_ar_keyword_search(page):
    """Azure TC 146473 | PBI 131059 — /ar: type 'غرفة' and submit -> only articles with 'غرفة' in AR title/description,
    shown in Arabic."""
    check = _Check("TC 146473")
    news = NewsPage(page).open_listing(locale="ar")
    items = _items_by_id(news, "ar")
    news.search("غرفة")
    check.equals("search field keeps the Arabic text", news.search_value(), "غرفة")
    news.load_all()
    ids = news.listed_ids()
    check.truthy("results listed", len(ids) > 0, ">= 1", 0)
    check.truthy("every result contains 'غرفة'", all(_matches(items.get(i, {}), "غرفة") for i in ids), "only matches",
                 [items.get(i, {}).get("title") for i in ids if not _matches(items.get(i, {}), "غرفة")])
    check.truthy("results shown in Arabic", all(ARABIC.search(t) for t in news.card_titles()), "Arabic titles",
                 [t for t in news.card_titles() if not ARABIC.search(t)])
    expected = sorted(i for i, it in items.items() if _matches(it, "غرفة"))
    check.equals("all matching articles returned", sorted(set(ids)), expected)
    check.assert_clean()


@_meta("146474", "Dates and read time are localized on the Arabic listing and detail", "Bilingual")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_146474
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_ar_localized_date_readtime(page):
    """Azure TC 146474 | PBI 131059 — article dated 2026-03-03 (id 182442): '3 مارس 2026'; read time 'N دقائق قراءة'
    on the /ar listing and detail, no English 'Min Read'."""
    check = _Check("TC 146474")
    news = NewsPage(page).open_listing(locale="ar")
    facts = {i: f for i, f in zip(news.listed_ids(), news.card_facts("a.qc-news-feat-card, a.qc-news-card"))}
    while DETAIL_ID not in facts and news.can_load_more():
        news.load_more()
        facts = {i: f for i, f in zip(news.listed_ids(), news.card_facts("a.qc-news-feat-card, a.qc-news-card"))}
    listing_meta = facts.get(DETAIL_ID, {}).get("meta", [])
    check.equals("listing date", listing_meta[0] if listing_meta else None, "3 مارس 2026")
    news.open_detail(DETAIL_ID, locale="ar")
    meta = news.texts(news.D_META_ITEM)
    check.equals("detail date", meta[0] if meta else None, "3 مارس 2026")
    check.truthy("detail read time in Arabic", len(meta) > 2 and "دقائق قراءة" in meta[2] and "Min Read" not in meta[2],
                 "N دقائق قراءة", meta[2:3])
    check.assert_clean()


@_meta("146479", "A 68-character title does not break the card layout on desktop and mobile", "Bilingual")
@pytest.mark.edge
@pytest.mark.bilingual
@pytest.mark.tc_146479
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_long_title_layout(page):
    """Azure TC 146479 | PBI 131059 — needs a published article with a 68-character title (EN 'QCTEST-131059-' + 54 x
    'W', AR 68 chars). TEST DATA: skipped with the reason when no such article is published."""
    news = NewsPage(page)
    en = [i for i in news.api_items("en") if len(i.get("title", "")) >= 68]
    ar = [i for i in news.api_items("ar") if len(i.get("title", "")) >= 68]
    if not en and not ar:
        longest = max((len(i.get("title", "")) for i in news.api_items("en")), default=0)
        pytest.skip(f"TEST DATA: no published article with a 68-character title on qcdev (longest EN title: {longest} chars)")
    check = _Check("TC 146479")
    news.open_listing()
    for c in news.card_facts("a.qc-news-feat-card, a.qc-news-card"):
        check.truthy(f"'{c['title'][:20]}' title inside its card", c["titleRight"] <= c["x"] + c["width"] + 1, "inside", c)
    _no_overflow(check, news)
    check.assert_clean()

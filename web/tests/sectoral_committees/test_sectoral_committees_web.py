"""
web/tests/sectoral_committees/test_sectoral_committees_web.py

Web-platform cases for PBI 130716 ("QC - Councils, Committees & Partnerships -
001 - Sectoral Committees and Business Councils"), suite 140375 — 30 approved
Automation cases: 146820-146833, 146835-146839, 146840-146848, 146886, 147044
(146849 is Manual; 146834 is not in the batch).

Page: /web/qatar-chamber/sectoral-committees-and-business-councils (AR: /ar).
Every test uses a fresh UNAUTHENTICATED context (Chrome/Edge/Firefox via the
module-local `engine_page` fixture, which attaches a failure screenshot) and
fails once with the full deviation list. Values are the case's own Figma-
verified numbers; "derived / not extracted" values are unmeasured notes.

Readings (disclosed):
  - "#FFFFFF at N% opacity" = colour alpha x element opacity folded together
    (design_tokens.effective_color).
  - A 1px border may be a CSS border OR an inset box-shadow ring.
  - "Fully rounded" / circle = radius >= half the element height (or 50%).
  - Icon sizes/colours are read from the icon's own <svg> (stroke of its path).
"""

import re

import allure
import pytest

from config.settings import settings
from core.utils.reporting import attach_screenshot, extract_test_case_id
from core.web.design_tokens import effective_color, hex_to_rgb, px_close
from web.pages.sectoral_committees.sectoral_committees_page import SectoralCommitteesPage

PBI = "130716"
D1920 = {"viewport": (1920, 1080), "auth": False}
T768 = {"viewport": (768, 1024), "auth": False}
M390 = {"viewport": (390, 844), "auth": False}
TYPO = ("font-family", "font-weight", "font-size", "line-height", "color", "opacity")
BOX = ("border-top-style", "border-top-width", "border-top-color", "border-top-left-radius", "background-color", "box-shadow",
       "padding-top", "padding-right", "padding-bottom", "padding-left", "row-gap", "column-gap")
RING = re.compile(r"(rgba?\([^)]*\)) 0px 0px 0px ([\d.]+)px inset")
ARABIC = re.compile(r"[؀-ۿ]")
BANKING = "Banking & Investment Committee"

pytestmark = [pytest.mark.web, pytest.mark.pbi_130716, pytest.mark.comm]


# ---------------------------------------------------------------------------
class _Check:
    def __init__(self, title):
        self.title, self.deviations, self.notes = title, [], []

    def truthy(self, label, cond, expected, actual):
        if not cond:
            self.deviations.append(f"{label}: expected {expected!r}, got {actual!r}")

    def equals(self, label, actual, expected):
        self.truthy(label, actual == expected, expected, actual)

    def color(self, label, actual, hex_, alpha=1.0):
        rgb, a = effective_color({"color": actual}) if actual.startswith("rgb") else (actual, 1.0)
        self.truthy(label, rgb == hex_to_rgb(hex_) and abs(a - alpha) <= 0.02,
                    f"{hex_}" + (f" @ {int(alpha * 100)}%" if alpha != 1 else ""), actual)

    def px(self, label, actual, expected, tol=1.0):
        a = actual if isinstance(actual, str) else (f"{actual:.1f}px" if actual is not None else None)
        self.truthy(label, a is not None and px_close(a, f"{expected}px", tol), f"{expected}px", a)

    def size(self, label, box, w, h, tol=1.0):
        self.truthy(f"{label} size", box is not None and (w is None or abs(box["width"] - w) <= tol)
                    and (h is None or abs(box["height"] - h) <= tol),
                    f"{w}x{h}", f"{round(box['width'], 1)}x{round(box['height'], 1)}" if box else None)

    def typo(self, label, s, size, weight, line=None, hex_=None, alpha=1.0):
        self.truthy(f"{label}.font-family", "cairo" in s["font-family"].lower(), "Cairo", s["font-family"])
        self.px(f"{label}.font-size", s["font-size"], size, 0.25)
        self.equals(f"{label}.font-weight", s["font-weight"], str(weight))
        if line is not None:
            self.px(f"{label}.line-height", s["line-height"], line, 0.25)
        if hex_:
            rgb, a = effective_color({"color": s["color"], "opacity": s.get("opacity", "1")})
            self.truthy(f"{label}.color", rgb == hex_to_rgb(hex_) and abs(a - alpha) <= 0.02,
                        f"{hex_}" + (f" @ {int(alpha * 100)}%" if alpha != 1 else ""), f"{s['color']} opacity {s.get('opacity')}")

    def border(self, label, s, hex_, width=1):
        ring = RING.match(s.get("box-shadow") or "")
        if s["border-top-style"] not in ("none", "") and float(s["border-top-width"].rstrip("px") or 0) > 0:
            self.px(f"{label}.border width", s["border-top-width"], width, 0.25)
            self.color(f"{label}.border colour", s["border-top-color"], hex_)
        elif ring:
            self.px(f"{label}.border width (inset ring)", ring.group(2) + "px", width, 0.25)
            self.color(f"{label}.border colour (inset ring)", ring.group(1), hex_)
        else:
            self.truthy(f"{label}.border", False, f"{width}px {hex_}", f"none (box-shadow {s.get('box-shadow')})")

    def radius(self, label, s, expected, height=None):
        r = s["border-top-left-radius"]
        if expected == "circle":
            val = 9999.0 if r == "50%" else (float(r[:-2]) if r.endswith("px") else 0.0)
            self.truthy(f"{label}.radius", height is not None and val >= height / 2 - 0.5, "circle", r)
        else:
            self.px(f"{label}.radius", r, expected, 0.5)

    def icon(self, label, st, w, h, hex_):
        self.size(f"{label}", st, w, h)
        self.truthy(f"{label} stroke", hex_to_rgb(hex_) in (st["stroke"], st["color"]), hex_, {k: st[k] for k in ("stroke", "color")})

    def note(self, text):
        self.notes.append(text)

    def assert_clean(self):
        if self.notes:
            allure.attach("\n".join(self.notes), "notes (unmeasured / test data)", allure.attachment_type.TEXT)
        assert not self.deviations, f"{self.title}: {len(self.deviations)} deviation(s):\n  - " + "\n  - ".join(self.deviations)


def _meta(tc, title, story, severity=allure.severity_level.NORMAL):
    def deco(fn):
        for d in (allure.label("testcase", tc), allure.label("pbi", PBI), allure.title(title),
                  allure.severity(severity), allure.story(story),
                  allure.feature("Sectoral Committees and Business Councils"), allure.epic("Councils, Committees & Partnerships")):
            fn = d(fn)
        return fn
    return deco


C, N = allure.severity_level.CRITICAL, allure.severity_level.NORMAL


def _no_overflow(check, sc):
    o = sc.horizontal_overflow_px()
    check.truthy("no horizontal scroll", o <= 0, "0px", f"{o}px")


def _overlap(a, b):
    return bool(a and b) and (a["x"] < b["x"] + b["width"] - 1 and b["x"] < a["x"] + a["width"] - 1
                              and a["y"] < b["y"] + b["height"] - 1 and b["y"] < a["y"] + a["height"] - 1)


@pytest.fixture
def engine_page(request, playwright_instance):
    """Own browser (engine chromium|firefox, optional channel), unauthenticated 1920x1080; collects console
    errors; attaches a failure screenshot to Allure."""
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
# EN light desktop (146820-146831)
# ---------------------------------------------------------------------------
@_meta("146820", "Page renders hero, Sector Representation, Committee Directory and Continue sections in order", "Layout", C)
@pytest.mark.ui
@pytest.mark.tc_146820
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_section_order(page):
    """Azure TC 146820 | PBI 130716 — header 1920x80, hero 1920x424, then Sector, Directory, Continue panel, footer;
    body #FFFFFF; content column 1320 wide with 300px side padding."""
    check = _Check("TC 146820")
    sc = SectoralCommitteesPage(page).open_page()
    check.size("header", sc.box(sc.HEADER), 1920, 80)
    check.size("hero", sc.box(sc.HERO), 1920, 424)
    order = sc.section_order()
    ys = [y for _, y in order]
    check.truthy("section order hero > sector > directory > continue > footer", None not in ys and ys == sorted(ys),
                 "increasing", order)
    check.color("body background", sc.styles(sc.PAGE_BODY, ("background-color",))["background-color"], "#FFFFFF")
    body = sc.box(sc.BODY)
    check.px("content column width", body["width"], 1320)
    check.px("side padding", body["x"], 300)
    check.assert_clean()


@_meta("146821", "Breadcrumb renders Home and Councils, Committees & Partnerships with the Figma text style", "Hero")
@pytest.mark.ui
@pytest.mark.tc_146821
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_breadcrumb_style(page):
    """Azure TC 146821 | PBI 130716 — row 1320x22 above the eyebrow; 'Home' (12x12 icon) then 'Councils, Committees &
    Partnerships'; Cairo 14/400/22 #FFFFFF; chevron 4x8 stroke #FFFFFF 1.5."""
    check = _Check("TC 146821")
    sc = SectoralCommitteesPage(page).open_page()
    row, eyebrow = sc.box(sc.CRUMBS), sc.box(sc.HERO_EYEBROW)
    check.size("breadcrumb row", row, 1320, 22)
    check.truthy("breadcrumb above the eyebrow", row["y"] + row["height"] <= eyebrow["y"], "above", (row["y"], eyebrow["y"]))
    items = sc.texts(sc.CRUMB_ITEMS)
    check.equals("breadcrumb first two items", items[:2], ["Home", "Councils, Committees & Partnerships"])
    if len(items) > 2:
        check.note(f"breadcrumb has {len(items)} items {items} (Figma shows two levels, PBI adds the page level - A-7)")
    check.size("home icon", sc.box(sc.CRUMB_HOME_ICON), 12, 12)
    for i in range(min(2, sc.count(sc.CRUMB_ITEMS))):
        check.typo(f"crumb '{items[i]}'", sc.styles(sc.CRUMB_ITEMS, TYPO, i), 14, 400, 22, "#FFFFFF")
    sep = sc.icon_styles(sc.CRUMB_SEP)
    check.icon("chevron separator", sep, 4, 8, "#FFFFFF")
    check.px("chevron stroke width", sep["strokeWidth"], 1.5, 0.1)
    check.assert_clean()


@_meta("146822", "Hero banner shows eyebrow, title and subtitle with the Figma typography", "Hero", C)
@pytest.mark.ui
@pytest.mark.tc_146822
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_hero_typography(page):
    """Azure TC 146822 | PBI 130716 — hero 1920x424 padding 300/40; eyebrow 12/400/18 #FFFFFF 50%; title 48/700/60
    #FFFFFF; subtitle 16/400/24 #FFFFFF 70%; 64px vertical gap between text blocks."""
    check = _Check("TC 146822")
    sc = SectoralCommitteesPage(page).open_page()
    check.size("hero", sc.box(sc.HERO), 1920, 424)
    inner = sc.box(sc.HERO_INNER)
    check.px("hero side padding", inner["x"], 300)
    check.equals("eyebrow", sc.text_of(sc.HERO_EYEBROW), "Committees & Business Councils")
    check.typo("eyebrow", sc.styles(sc.HERO_EYEBROW, TYPO), 12, 400, 18, "#FFFFFF", 0.5)
    check.equals("title", sc.text_of(sc.HERO_TITLE), "Sectoral Committees and Business Councils")
    check.typo("title", sc.styles(sc.HERO_TITLE, TYPO), 48, 700, 60, "#FFFFFF")
    check.equals("subtitle", sc.text_of(sc.HERO_SUBTITLE).replace("’", "'"),
                 "Explore Qatar Chamber's sectoral committees, understand their responsibilities, and access the appropriate joining or feedback request.")
    check.typo("subtitle", sc.styles(sc.HERO_SUBTITLE, TYPO), 16, 400, 24, "#FFFFFF", 0.7)
    crumbs, text = sc.box(sc.CRUMBS), sc.box(sc.HERO_TEXT)
    check.px("vertical gap breadcrumb -> hero text", text["y"] - (crumbs["y"] + crumbs["height"]), 64, 1)
    check.assert_clean()


@_meta("146823", "Sector representation section shows eyebrow, heading and body with the Figma styles", "Sections")
@pytest.mark.ui
@pytest.mark.tc_146823
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_sector_section(page):
    """Azure TC 146823 | PBI 130716 — block 1320x96; eyebrow 14/400/22 #911731; heading 36/700/44 #1D1D1B; body
    16/400/24 #6C6C6B."""
    check = _Check("TC 146823")
    sc = SectoralCommitteesPage(page).open_page()
    check.size("text block", sc.box(sc.SECTOR), 1320, 96)
    check.equals("eyebrow", sc.text_of(sc.SECTOR_EYEBROW), "Sector representation")
    check.typo("eyebrow", sc.styles(sc.SECTOR_EYEBROW, TYPO), 14, 400, 22, "#911731")
    check.equals("heading", sc.text_of(sc.SECTOR_HEADING), "Where business insight informs action")
    check.typo("heading", sc.styles(sc.SECTOR_HEADING, TYPO), 36, 700, 44, "#1D1D1B")
    check.equals("body", sc.text_of(sc.SECTOR_BODY).replace("’", "'"),
                 "Sectoral committees bring together business leaders to review market priorities, study sector challenges, "
                 "and submit practical recommendations that support Qatar's private sector.")
    check.typo("body", sc.styles(sc.SECTOR_BODY, TYPO), 16, 400, 24, "#6C6C6B")
    check.assert_clean()


@_meta("146824", "Collapsed Head of Sectoral committees card renders with the Figma layout and colours", "Leadership")
@pytest.mark.ui
@pytest.mark.tc_146824
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_lead_card_collapsed(page):
    """Azure TC 146824 | PBI 130716 — card 1320x100 1px #EDEDED r10 padding 16, collapsed; icon tile 48x48 #911731 r8,
    white 22x20 icon; eyebrow 14/400 #911731; title 16/700 #343432; desc 14/400 #7C7B7B; toggle 24x24 circle #FFFFFF
    stroke #EDEDED, icon 8x8 stroke #A8A8A7."""
    check = _Check("TC 146824")
    sc = SectoralCommitteesPage(page).open_page()
    card = sc.styles(sc.LEAD_CARD, BOX)
    check.size("card", sc.box(sc.LEAD_CARD), 1320, 100)
    check.border("card", card, "#EDEDED")
    check.radius("card", card, 10)
    check.px("card padding", card["padding-top"], 16, 0.5)
    check.equals("collapsed (aria-expanded)", sc.attr(sc.LEAD_HEAD, "aria-expanded"), "false")
    check.equals("leader grid hidden", sc.visible_count(sc.LEADER), 0)
    tile = sc.styles(sc.LEAD_ICON, BOX)
    check.size("icon tile", sc.box(sc.LEAD_ICON), 48, 48)
    check.color("icon tile fill", tile["background-color"], "#911731")
    check.radius("icon tile", tile, 8)
    ic = sc.icon_styles(sc.LEAD_ICON)
    check.size("tile icon", ic, 22, 20)
    check.truthy("tile icon white", hex_to_rgb("#FFFFFF") in (ic["stroke"], ic["color"], ic["fill"]), "#FFFFFF", ic)
    check.equals("eyebrow", sc.text_of(sc.LEAD_EYEBROW), "Leadership directory")
    check.typo("eyebrow", sc.styles(sc.LEAD_EYEBROW, TYPO), 14, 400, None, "#911731")
    check.equals("title", sc.text_of(sc.LEAD_TITLE), "Head of Sectoral committees")
    check.typo("title", sc.styles(sc.LEAD_TITLE, TYPO), 16, 700, None, "#343432")
    check.equals("description", sc.text_of(sc.LEAD_DESC), "View committee leaders and the sectors they represent.")
    check.typo("description", sc.styles(sc.LEAD_DESC, TYPO), 14, 400, None, "#7C7B7B")
    tg, tb = sc.styles(sc.LEAD_TOGGLE, BOX), sc.box(sc.LEAD_TOGGLE)
    check.size("toggle", tb, 24, 24)
    check.radius("toggle", tg, "circle", tb["height"] if tb else None)
    check.color("toggle fill", tg["background-color"], "#FFFFFF")
    check.border("toggle", tg, "#EDEDED")
    check.icon("toggle icon", sc.icon_styles(sc.LEAD_TOGGLE), 8, 8, "#A8A8A7")
    check.assert_clean()


@_meta("146825", "Each leader card in the expanded grid shows Number, Name and Committee/Sector", "Leadership", C)
@pytest.mark.ui
@pytest.mark.tc_146825
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_leader_grid(page):
    """Azure TC 146825 | PBI 130716 — expand the Head card: exactly 12 leader cards; first '01' / 'Rashid Nasser
    Sraiya Al Kaabi' / 'Banking & Investment Committee'; none lacks a number, name or sector (derived, A-8)."""
    check = _Check("TC 146825")
    sc = SectoralCommitteesPage(page).open_page()
    sc.toggle_lead()
    check.equals("expanded (aria-expanded)", sc.attr(sc.LEAD_HEAD, "aria-expanded"), "true")
    leaders = [l for l in sc.leaders() if l["visible"]]
    check.equals("leader cards", len(leaders), 12)
    if leaders:
        check.equals("first leader", (leaders[0]["num"], leaders[0]["name"], leaders[0]["sector"]),
                     ("01", "Rashid Nasser Sraiya Al Kaabi", "Banking & Investment Committee"))
    incomplete = [l for l in leaders if not (l["num"] and l["name"] and l["sector"])]
    check.equals("cards missing number/name/sector", incomplete, [])
    check.assert_clean()


@_meta("146826", "Committee directory shows eyebrow, heading, body and search input with the Figma styles", "Directory")
@pytest.mark.ui
@pytest.mark.tc_146826
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_directory_head_and_search(page):
    """Azure TC 146826 | PBI 130716 — eyebrow 14/400 #911731; heading 'Explore the Committees' 36/700/44 #1D1D1B; body
    16/400/24 #6C6C6B; search 424x44 #FFFFFF 1px #EDEDED r8 padding 12/11; placeholder 14/400 #A8A8A7; icon 15x15
    stroke #A8A8A7."""
    check = _Check("TC 146826")
    sc = SectoralCommitteesPage(page).open_page()
    check.equals("eyebrow", sc.text_of(sc.DIR_EYEBROW), "Committee directory")
    check.typo("eyebrow", sc.styles(sc.DIR_EYEBROW, TYPO), 14, 400, None, "#911731")
    check.equals("heading", sc.text_of(sc.DIR_HEADING), "Explore the Committees")
    check.typo("heading", sc.styles(sc.DIR_HEADING, TYPO), 36, 700, 44, "#1D1D1B")
    check.equals("body", sc.text_of(sc.DIR_BODY), "Open any committee to review its mandate and continue to the relevant request form.")
    check.typo("body", sc.styles(sc.DIR_BODY, TYPO), 16, 400, 24, "#6C6C6B")
    check.size("search input", sc.box(sc.SEARCH), 424, 44)
    field = {**sc.styles(sc.SEARCH_FIELD, BOX)}
    inp = sc.styles(sc.SEARCH, BOX)
    fill = inp["background-color"] if inp["background-color"] != "rgba(0, 0, 0, 0)" else field["background-color"]
    check.color("search fill", fill, "#FFFFFF")
    check.border("search", inp if (inp["border-top-style"] != "none" or RING.match(inp["box-shadow"] or "")) else field, "#EDEDED")
    check.radius("search", inp if inp["border-top-left-radius"] != "0px" else field, 8)
    check.truthy("search padding 12/11", px_close(inp["padding-left"], "12px", 0.5) and px_close(inp["padding-top"], "11px", 0.5),
                 "12px sides / 11px top-bottom", f"{inp['padding-left']} / {inp['padding-top']}")
    check.equals("placeholder", sc.attr(sc.SEARCH, "placeholder"), "Search by committee or sector")
    check.typo("placeholder", sc.styles(sc.SEARCH, TYPO, pseudo="::placeholder"), 14, 400, None, "#A8A8A7")
    check.icon("search icon", sc.icon_styles(sc.SEARCH_ICON), 15, 15, "#A8A8A7")
    check.assert_clean()


@_meta("146827", "Collapsed committee row shows number badge, name, description and toggle with the Figma styles", "Directory", C)
@pytest.mark.ui
@pytest.mark.tc_146827
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_committee_row_collapsed(page):
    """Azure TC 146827 | PBI 130716 — 12 rows 01..12 each 1320x78 collapsed, 1px #EDEDED r10 padding 16, 16px gap;
    row 01 badge 40x40 circle #F4E7EA '01' 18/500 #911731; name 16/700 #343432; desc 14/400 #7C7B7B; toggle 24x24
    circle #FFFFFF stroke #EDEDED icon 8x8 #A8A8A7."""
    check = _Check("TC 146827")
    sc = SectoralCommitteesPage(page).open_page()
    nums = sc.visible_row_nums()
    check.equals("row numbers", nums, [f"{i:02d}" for i in range(1, 13)])
    boxes = sc.boxes(sc.ROW)
    for i, b in enumerate(boxes):
        check.size(f"row {i + 1}", b, 1320, 78)
        check.truthy(f"row {i + 1} collapsed", not sc.row_expanded(i), "collapsed", "expanded")
    for i in range(len(boxes) - 1):
        check.px(f"gap row {i + 1}->{i + 2}", boxes[i + 1]["y"] - (boxes[i]["y"] + boxes[i]["height"]), 16, 0.5)
    row = sc.styles(sc.ROW, BOX)
    check.border("row", row, "#EDEDED")
    check.radius("row", row, 10)
    check.px("row padding", row["padding-top"], 16, 0.5)
    badge, bb = sc.styles(sc.ROW_NUM, BOX + TYPO), sc.box(sc.ROW_NUM)
    check.size("badge", bb, 40, 40)
    check.radius("badge", badge, "circle", bb["height"])
    check.color("badge fill", badge["background-color"], "#F4E7EA")
    check.typo("badge number", badge, 18, 500, None, "#911731")
    check.equals("row 01 name", sc.row_text(0, sc.ROW_TITLE), BANKING)
    check.typo("row name", sc.styles(sc.ROW_TITLE, TYPO), 16, 700, None, "#343432")
    check.equals("row 01 description", sc.row_text(0, sc.ROW_DESC), "Banking, finance, and private investment")
    check.typo("row description", sc.styles(sc.ROW_DESC, TYPO), 14, 400, None, "#7C7B7B")
    tg, tb = sc.styles(sc.ROW_TOGGLE, BOX), sc.box(sc.ROW_TOGGLE)
    check.size("row toggle", tb, 24, 24)
    check.radius("row toggle", tg, "circle", tb["height"])
    check.color("row toggle fill", tg["background-color"], "#FFFFFF")
    check.border("row toggle", tg, "#EDEDED")
    check.icon("row toggle icon", sc.icon_styles(sc.ROW_TOGGLE), 8, 8, "#A8A8A7")
    check.assert_clean()


@_meta("146828", "Expanded committee shows competencies eyebrow, mandate heading and checklist with the Figma styles", "Directory")
@pytest.mark.ui
@pytest.mark.tc_146828
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_committee_row_expanded_styles(page):
    """Azure TC 146828 | PBI 130716 — expand Banking & Investment: panel inside the row (answer block 1288 wide, gap
    20), toggle filled #911731 with white icon; eyebrow 12/400 #911731; heading 16/700 #1D1D1B; items 14/400/22
    #343432 with 12x8 check icon stroke #A66F43."""
    check = _Check("TC 146828")
    sc = SectoralCommitteesPage(page).open_page()
    i = sc.row_index(BANKING)
    sc.toggle_row(i)
    check.truthy("row expanded", sc.row_expanded(i), "expanded", "collapsed")
    panel = sc.row_child_box(i, sc.ROW_PANEL)
    row = sc.boxes(sc.ROW)[i]
    check.truthy("panel inside the row", panel and panel["y"] >= row["y"] and panel["y"] + panel["height"] <= row["y"] + row["height"] + 1,
                 "inside", (panel, row))
    check.px("answer block width", panel["width"] if panel else None, 1288)
    check.px("answer block gap", sc.row_child_styles(i, ".qc-sc-mandate", ("row-gap",))["row-gap"], 20, 0.5)
    tg = sc.row_child_styles(i, "span.qc-sc-toggle", BOX)
    check.color("toggle filled", tg["background-color"], "#911731")
    ic = sc.row_child_icon(i, "span.qc-sc-toggle")
    check.truthy("toggle icon white", hex_to_rgb("#FFFFFF") in (ic["stroke"], ic["color"]), "#FFFFFF", ic)
    check.equals("eyebrow", sc.row_text(i, sc.MANDATE_EYEBROW), "Committee competencies")
    check.typo("eyebrow", sc.row_child_styles(i, sc.MANDATE_EYEBROW, TYPO), 12, 400, None, "#911731")
    check.equals("heading", sc.row_text(i, sc.MANDATE_HEADING), "Mandate and responsibilities")
    check.typo("heading", sc.row_child_styles(i, sc.MANDATE_HEADING, TYPO), 16, 700, None, "#1D1D1B")
    check.typo("checklist item", sc.row_child_styles(i, sc.MANDATE_TEXT, TYPO), 14, 400, 22, "#343432")
    check.icon("check icon", sc.row_child_icon(i, sc.MANDATE_ICON), 12, 8, "#A66F43")
    check.assert_clean()


@_meta("146829", "Banking & Investment Committee mandate checklist lists 11 items", "Directory")
@pytest.mark.ui
@pytest.mark.tc_146829
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_banking_mandate_11_items(page):
    """Azure TC 146829 | PBI 130716 — exactly 11 checklist items with check icons; none empty or duplicated."""
    check = _Check("TC 146829")
    sc = SectoralCommitteesPage(page).open_page()
    i = sc.row_index(BANKING)
    sc.toggle_row(i)
    items = sc.row_mandate_texts(i)
    check.equals("visible checklist items", sc.row_mandate_visible(i), 11)
    check.equals("items", len(items), 11)
    check.equals("empty items", [t for t in items if not t], [])
    check.equals("duplicated items", sorted({t for t in items if items.count(t) > 1}), [])
    check.note(f"first item: {items[0] if items else None!r}; last item: {items[-1] if items else None!r}")
    check.assert_clean()


@_meta("146830", "Continue with Qatar Chamber panel shows eyebrow, heading and body with the Figma styles", "CTA")
@pytest.mark.ui
@pytest.mark.tc_146830
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_cta_panel(page):
    """Azure TC 146830 | PBI 130716 — panel 1320x202 r12 padding 20 gap 16; eyebrow 12/400 #911731; heading 20/700/30
    #1D1D1B; body 14/400/22 #6C6C6B."""
    check = _Check("TC 146830")
    sc = SectoralCommitteesPage(page).open_page()
    panel = sc.styles(sc.CTA, BOX)
    check.size("panel", sc.box(sc.CTA), 1320, 202)
    check.radius("panel", panel, 12)
    check.px("panel padding", panel["padding-top"], 20, 0.5)
    check.px("panel gap", panel["row-gap"], 16, 0.5)
    if sc.count(sc.CTA_EYEBROW):
        check.equals("eyebrow", sc.text_of(sc.CTA_EYEBROW), "Continue with Qatar Chamber")
        check.typo("eyebrow", sc.styles(sc.CTA_EYEBROW, TYPO), 12, 400, None, "#911731")
    else:
        check.truthy("eyebrow 'Continue with Qatar Chamber' rendered", False, "rendered", "not rendered")
    check.equals("heading", sc.text_of(sc.CTA_HEADING), "Choose the appropriate request")
    check.typo("heading", sc.styles(sc.CTA_HEADING, TYPO), 20, 700, 30, "#1D1D1B")
    check.equals("body", sc.text_of(sc.CTA_BODY),
                 "Use the relevant form to join a committee or business council, or to submit a suggestion or complaint.")
    check.typo("body", sc.styles(sc.CTA_BODY, TYPO), 14, 400, 22, "#6C6C6B")
    check.assert_clean()


@_meta("146831", "Each CTA card shows icon tile, title, description and arrow with the Figma styles", "CTA")
@pytest.mark.ui
@pytest.mark.tc_146831
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_cta_cards(page):
    """Azure TC 146831 | PBI 130716 — three side-by-side cards 418x74 #FFFFFF 1px #E3C5CB r10 padding 16 gap 12; icon
    tile 40x40 #E3C5CB r8, icon 15x16 stroke #911731; title 14/700 #1D1D1B; desc 12/400 #7C7B7B; arrow 10x10 stroke
    #E3C5CB at the card end."""
    check = _Check("TC 146831")
    sc = SectoralCommitteesPage(page).open_page()
    boxes = sc.boxes(sc.CTA_CARD)
    check.equals("CTA cards", len(boxes), 3)
    check.truthy("cards side by side", len({round(b["y"]) for b in boxes}) == 1, "one row", [round(b["y"]) for b in boxes])
    for i, b in enumerate(boxes):
        st = sc.styles(sc.CTA_CARD, BOX, i)
        check.size(f"card {i + 1}", b, 418, 74)
        check.color(f"card {i + 1} fill", st["background-color"], "#FFFFFF")
        check.border(f"card {i + 1}", st, "#E3C5CB")
        check.radius(f"card {i + 1}", st, 10)
        check.px(f"card {i + 1} padding", st["padding-top"], 16, 0.5)
        check.px(f"card {i + 1} gap", st["column-gap"], 12, 0.5)
        tile = sc.styles(sc.CTA_ICON, BOX, i)
        check.size(f"card {i + 1} icon tile", sc.box(sc.CTA_ICON, i), 40, 40)
        check.color(f"card {i + 1} icon tile fill", tile["background-color"], "#E3C5CB")
        check.radius(f"card {i + 1} icon tile", tile, 8)
        check.icon(f"card {i + 1} icon", sc.icon_styles(sc.CTA_ICON, i), 15, 16, "#911731")
        check.typo(f"card {i + 1} title", sc.styles(sc.CTA_TITLE, TYPO, i), 14, 700, None, "#1D1D1B")
        check.typo(f"card {i + 1} description", sc.styles(sc.CTA_DESC, TYPO, i), 12, 400, None, "#7C7B7B")
        arrow = sc.icon_styles(sc.CTA_ARROW, i)
        check.icon(f"card {i + 1} arrow", arrow, 10, 10, "#E3C5CB")
        ab = sc.box(sc.CTA_ARROW, i)
        check.truthy(f"card {i + 1} arrow at the card end", ab and ab["x"] + ab["width"] >= b["x"] + b["width"] - 40, "near right edge", ab)
    check.equals("first card title", sc.text_of(sc.CTA_TITLE), "Committee Joining Request")
    check.equals("first card description", sc.text_of(sc.CTA_DESC), "Apply to join a sectoral committee")
    check.note(f"CTA titles live: {sc.texts(sc.CTA_TITLE)} (Figma second title 'Business Council Membership Request' - A-6)")
    check.assert_clean()


# ---------------------------------------------------------------------------
# Bilingual (146832, 146833, 146835-146839, 146886, 147044)
# ---------------------------------------------------------------------------
@_meta("146832", "English page renders left-to-right with English labels throughout", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146832
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_english_ltr(page):
    """Azure TC 146832 | PBI 130716 — EN: dir ltr, text left-aligned, toggles at the right end of rows, English section labels."""
    check = _Check("TC 146832")
    sc = SectoralCommitteesPage(page).open_page()
    check.equals("html dir", sc.document_dir(), "ltr")
    for name, loc in (("hero title", sc.HERO_TITLE), ("sector heading", sc.SECTOR_HEADING), ("row title", sc.ROW_TITLE)):
        st = sc.styles(loc, ("direction", "text-align"))
        check.truthy(f"{name} left-aligned", st["direction"] == "ltr" and st["text-align"] in ("start", "left"), "ltr/left", st)
    row, tg = sc.boxes(sc.ROW)[0], sc.box(sc.ROW_TOGGLE)
    check.truthy("toggle at the right end of the row", tg["x"] > row["x"] + row["width"] / 2, "right half", (tg["x"], row))
    labels = [sc.text_of(sc.SECTOR_EYEBROW), sc.text_of(sc.DIR_EYEBROW), sc.text_of(sc.CTA_EYEBROW) if sc.count(sc.CTA_EYEBROW) else ""]
    check.equals("section labels", labels, ["Sector representation", "Committee directory", "Continue with Qatar Chamber"])
    check.assert_clean()


@_meta("146833", "Arabic page mirrors the layout right-to-left with the Figma AR styles", "Bilingual", C)
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146833
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_arabic_rtl_mirror(page):
    """Azure TC 146833 | PBI 130716 — /ar: dir rtl, right-aligned; breadcrumb 'الرئيسية' rightmost; number badges right;
    toggles left; search icon left; hero title Cairo 40/700/64."""
    check = _Check("TC 146833")
    sc = SectoralCommitteesPage(page).open_page(locale="ar")
    check.equals("html dir", sc.document_dir(), "rtl")
    st = sc.styles(sc.HERO_TITLE, ("direction", "text-align"))
    check.truthy("text right-aligned", st["direction"] == "rtl" and st["text-align"] in ("start", "right"), "rtl/right", st)
    crumbs = sc.boxes(sc.CRUMB_ITEMS)
    check.equals("breadcrumb labels", sc.texts(sc.CRUMB_ITEMS)[:2], ["الرئيسية", "المجالس واللجان والشراكات"])
    check.truthy("'الرئيسية' rightmost", len(crumbs) > 1 and crumbs[0]["x"] > crumbs[1]["x"], "first item rightmost", [round(c["x"]) for c in crumbs])
    row, badge, tg = sc.boxes(sc.ROW)[0], sc.box(sc.ROW_NUM), sc.box(sc.ROW_TOGGLE)
    mid = row["x"] + row["width"] / 2
    check.truthy("number badge on the right", badge["x"] > mid, "right half", badge["x"])
    check.truthy("toggle on the left", tg["x"] < mid, "left half", tg["x"])
    s, ic = sc.box(sc.SEARCH), sc.box(sc.SEARCH_ICON)
    check.truthy("search icon on the left", ic["x"] < s["x"] + s["width"] / 2, "left half", (ic["x"], s))
    check.typo("hero title", sc.styles(sc.HERO_TITLE, TYPO), 40, 700, 64)
    check.assert_clean()


@_meta("146835", "Arabic hero shows the Arabic eyebrow, title and subtitle", "Bilingual", C)
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146835
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_arabic_hero(page):
    """Azure TC 146835 | PBI 130716 — eyebrow 'اللجان ومجالس الأعمال' (12/400 white 50%); title 'اللجان القطاعية ومجالس
    الأعمال'; subtitle starts 'تعرّف على اللجان القطاعية في غرفة قطر'."""
    check = _Check("TC 146835")
    sc = SectoralCommitteesPage(page).open_page(locale="ar")
    check.equals("eyebrow", sc.text_of(sc.HERO_EYEBROW), "اللجان ومجالس الأعمال")
    check.typo("eyebrow", sc.styles(sc.HERO_EYEBROW, TYPO), 12, 400, None, "#FFFFFF", 0.5)
    check.equals("title", sc.text_of(sc.HERO_TITLE), "اللجان القطاعية ومجالس الأعمال")
    sub = sc.text_of(sc.HERO_SUBTITLE)
    check.truthy("subtitle start", sub.startswith("تعرّف على اللجان القطاعية في غرفة قطر"), "starts 'تعرّف على اللجان القطاعية في غرفة قطر'", sub[:50])
    check.assert_clean()


@_meta("146836", "Arabic breadcrumb shows the Arabic labels in right-to-left order", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146836
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_arabic_breadcrumb(page):
    """Azure TC 146836 | PBI 130716 — 'الرئيسية' then 'المجالس واللجان والشراكات' right-to-left, mirror of EN."""
    check = _Check("TC 146836")
    sc = SectoralCommitteesPage(page).open_page(locale="ar")
    check.equals("breadcrumb labels", sc.texts(sc.CRUMB_ITEMS)[:2], ["الرئيسية", "المجالس واللجان والشراكات"])
    xs = [b["x"] for b in sc.boxes(sc.CRUMB_ITEMS)]
    check.truthy("right-to-left order (Home at the far right)", xs == sorted(xs, reverse=True), "decreasing x", [round(x) for x in xs])
    check.assert_clean()


@_meta("146837", "Arabic search placeholder reads 'البحث حسب اللجنة أو القطاع'", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146837
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_arabic_search_placeholder(page):
    """Azure TC 146837 | PBI 130716 — placeholder 'البحث حسب اللجنة أو القطاع' #A8A8A7, right-aligned, icon at the left."""
    check = _Check("TC 146837")
    sc = SectoralCommitteesPage(page).open_page(locale="ar")
    check.equals("search empty", sc.search_value(), "")
    check.equals("placeholder", sc.attr(sc.SEARCH, "placeholder"), "البحث حسب اللجنة أو القطاع")
    ph = sc.styles(sc.SEARCH, ("color", "direction", "text-align"), pseudo="::placeholder")
    check.color("placeholder colour", ph["color"], "#A8A8A7")
    check.truthy("placeholder right-aligned", ph["direction"] == "rtl" and ph["text-align"] in ("start", "right"), "rtl/right", ph)
    s, ic = sc.box(sc.SEARCH), sc.box(sc.SEARCH_ICON)
    check.truthy("search icon at the left", ic["x"] < s["x"] + s["width"] / 2, "left half", ic["x"])
    check.assert_clean()


@_meta("146838", "Arabic mandate panel shows 'اختصاصات اللجنة' and 'الصلاحيات والمسؤوليات'", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146838
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_arabic_mandate_panel(page):
    """Azure TC 146838 | PBI 130716 — expand 'لجنة البنوك والاستثمار': eyebrow 'اختصاصات اللجنة' 12/400 #911731; heading
    'الصلاحيات والمسؤوليات' 16/700 #1D1D1B; 11 Arabic items right-aligned."""
    check = _Check("TC 146838")
    sc = SectoralCommitteesPage(page).open_page(locale="ar")
    i = sc.row_index("لجنة البنوك والاستثمار")
    check.truthy("row 'لجنة البنوك والاستثمار' present", i >= 0, "present", sc.visible_row_titles())
    if i >= 0:
        sc.toggle_row(i)
        check.equals("eyebrow", sc.row_text(i, sc.MANDATE_EYEBROW), "اختصاصات اللجنة")
        check.typo("eyebrow", sc.row_child_styles(i, sc.MANDATE_EYEBROW, TYPO), 12, 400, None, "#911731")
        check.equals("heading", sc.row_text(i, sc.MANDATE_HEADING), "الصلاحيات والمسؤوليات")
        check.typo("heading", sc.row_child_styles(i, sc.MANDATE_HEADING, TYPO), 16, 700, None, "#1D1D1B")
        items = sc.row_mandate_texts(i)
        check.equals("checklist items", len(items), 11)
        check.equals("non-Arabic items", [t for t in items if not ARABIC.search(t)], [])
        st = sc.row_child_styles(i, sc.MANDATE_TEXT, ("direction", "text-align"))
        check.truthy("items right-aligned", st["direction"] == "rtl" and st["text-align"] in ("start", "right"), "rtl/right", st)
    check.assert_clean()


@_meta("146839", "Arabic CTA cards show the three Arabic titles", "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_146839
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_arabic_cta_cards(page):
    """Azure TC 146839 | PBI 130716 — eyebrow 'المتابعة مع غرفة قطر', heading 'اختر الطلب المناسب'; the three Arabic titles
    and descriptions; arrows point left."""
    check = _Check("TC 146839")
    sc = SectoralCommitteesPage(page).open_page(locale="ar")
    check.equals("panel eyebrow", sc.text_of(sc.CTA_EYEBROW) if sc.count(sc.CTA_EYEBROW) else None, "المتابعة مع غرفة قطر")
    check.equals("panel heading", sc.text_of(sc.CTA_HEADING), "اختر الطلب المناسب")
    titles, descs = sc.texts(sc.CTA_TITLE), sc.texts(sc.CTA_DESC)
    check.equals("card titles (any order - A-6)", sorted(titles), sorted(["طلب الانضمام إلى لجنة", "طلب الانضمام إلى مجلس الأعمال", "الاقتراحات والشكاوى"]))
    for d in ("قدّم طلبًا للانضمام إلى إحدى اللجان القطاعية.", "تقدم للانضمام إلى مجلس أعمال", "شارك ملاحظاتك مع غرفة قطر"):
        check.truthy(f"description '{d}'", any(x.startswith(d.rstrip(".")) for x in descs), "present", descs)
    for i in range(sc.count(sc.CTA_ARROW)):
        tf = sc.styles(sc.CTA_ARROW, ("transform",), i)["transform"]
        ab, cb = sc.box(sc.CTA_ARROW, i), sc.box(sc.CTA_CARD, i)
        check.truthy(f"card {i + 1} arrow points left (mirrored, at the left end)",
                     tf.startswith("matrix(-1") and ab["x"] < cb["x"] + cb["width"] / 2, "scaleX(-1) at the left end", (tf, ab["x"]))
    check.assert_clean()


@_meta("146886", "Breadcrumb label follows the site menu structure", "Bilingual")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_146886
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_breadcrumb_follows_menu(page):
    """Azure TC 146886 | PBI 130716 — EN 'Home > Councils, Committees & Partnerships > Sectoral Committees and Business
    Councils' (PBI; Figma shows two levels - A-7); AR 'الرئيسية > المجالس واللجان والشراكات > <AR page name>'; labels equal
    the header menu names."""
    check = _Check("TC 146886")
    sc = SectoralCommitteesPage(page).open_page()
    en = sc.texts(sc.CRUMB_ITEMS)
    check.equals("EN breadcrumb", en, ["Home", "Councils, Committees & Partnerships", "Sectoral Committees and Business Councils"])
    menu = sc.menu_labels()
    check.truthy("EN level 2 equals the menu parent", len(en) > 1 and en[1] == menu["parent"], menu["parent"], en[1:2])
    check.truthy("EN level 3 equals the menu page item", len(en) > 2 and en[2] == menu["page"], menu["page"], en[2:3])
    sc.open_page(locale="ar")
    ar = sc.texts(sc.CRUMB_ITEMS)
    menu_ar = sc.menu_labels()
    check.equals("AR breadcrumb first two", ar[:2], ["الرئيسية", "المجالس واللجان والشراكات"])
    check.truthy("AR breadcrumb has the AR page name", len(ar) > 2 and ar[2] == menu_ar["page"], f"third item '{menu_ar['page']}'", ar)
    check.assert_clean()


@_meta("147044", "Arabic keyword search filters the Arabic committee list", "Bilingual")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_147044
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_arabic_search(page):
    """Azure TC 147044 | PBI 130716 — /ar: type 'الصحة' -> only 'لجنة الصحة' (05) listed."""
    check = _Check("TC 147044")
    sc = SectoralCommitteesPage(page).open_page(locale="ar")
    sc.search("الصحة")
    check.equals("search keeps the Arabic text", sc.search_value(), "الصحة")
    check.equals("visible rows", list(zip(sc.visible_row_nums(), sc.visible_row_titles())), [("05", "لجنة الصحة")])
    check.assert_clean()


# ---------------------------------------------------------------------------
# Compatibility (146840-146848)
# ---------------------------------------------------------------------------
def _browser_flow(check, pg, label, console=True):
    sc = SectoralCommitteesPage(pg).open_page()
    if console:
        check.equals(f"{label}: console errors", pg.console_errors, [])
    for name, loc in (("hero", sc.HERO), ("sector", sc.SECTOR), ("directory", sc.DIRECTORY), ("footer", sc.FOOTER)):
        check.truthy(f"{label}: {name} rendered", sc.box(loc) is not None, "rendered", None)
    _no_overflow(check, sc)
    sc.toggle_lead()
    check.equals(f"{label}: Head card expands to 12 leaders", sc.visible_count(sc.LEADER), 12)
    sc.toggle_lead()
    check.equals(f"{label}: Head card collapses", sc.visible_count(sc.LEADER), 0)
    i = sc.row_index("Health Committee")
    check.truthy(f"{label}: 'Health Committee' row present", i >= 0, "present", sc.visible_row_titles())
    if i >= 0:
        sc.toggle_row(i)
        check.truthy(f"{label}: Health row expands with a checklist", sc.row_expanded(i) and sc.row_mandate_visible(i) > 0,
                     "expanded with items", sc.row_mandate_visible(i))
    sc.search("Health")
    check.equals(f"{label}: search 'Health' shows only Health Committee", sc.visible_row_titles(), ["Health Committee"])


@_meta("146840", "Page and accordions work in Chrome desktop", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146840
@pytest.mark.parametrize("engine_page", [{"engine": "chromium", "channel": "chrome"}], indirect=True)
def test_chrome(engine_page):
    """Azure TC 146840 | PBI 130716 — Chrome (channel=chrome), 1920x1080."""
    check = _Check("TC 146840")
    _browser_flow(check, engine_page, "Chrome")
    check.assert_clean()


@_meta("146841", "Page and accordions work in Edge desktop", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146841
@pytest.mark.parametrize("engine_page", [{"engine": "chromium", "channel": "msedge"}], indirect=True)
def test_edge(engine_page):
    """Azure TC 146841 | PBI 130716 — Edge (channel=msedge), 1920x1080."""
    check = _Check("TC 146841")
    _browser_flow(check, engine_page, "Edge", console=False)
    check.assert_clean()


@_meta("146842", "Page and accordions work in Firefox desktop", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146842
@pytest.mark.parametrize("engine_page", [{"engine": "firefox"}], indirect=True)
def test_firefox(engine_page):
    """Azure TC 146842 | PBI 130716 — Firefox (Playwright firefox), 1920x1080."""
    check = _Check("TC 146842")
    _browser_flow(check, engine_page, "Firefox", console=False)
    check.assert_clean()


@_meta("146843", "Page and accordions work in Safari desktop", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146843
def test_safari():
    """Azure TC 146843 | PBI 130716 — Safari (macOS). Same flow as Chrome; not runnable on this Windows host."""
    pytest.skip("Safari requires macOS")


@_meta("146844", "Page matches the Figma desktop layout at 1920x1080", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146844
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_desktop_1920(page):
    """Azure TC 146844 | PBI 130716 — 1320 column centred (300 sides), hero 424 high; three CTA cards in one row each 418;
    expanding Head + first committee stays inside 1320 with no horizontal scroll."""
    check = _Check("TC 146844")
    sc = SectoralCommitteesPage(page).open_page()
    body = sc.box(sc.BODY)
    check.px("column width", body["width"], 1320)
    check.px("side padding", body["x"], 300)
    check.px("hero height", sc.box(sc.HERO)["height"], 424)
    cards = sc.boxes(sc.CTA_CARD)
    check.truthy("CTA cards in one row", len(cards) == 3 and len({round(c["y"]) for c in cards}) == 1, "3 in a row", cards)
    for i, c in enumerate(cards):
        check.px(f"CTA card {i + 1} width", c["width"], 418)
    sc.toggle_lead()
    sc.toggle_row(0)
    for name, loc in (("leader grid", sc.LEAD_PANEL), ("committee panel", sc.ROW_PANEL)):
        b = sc.box(loc)
        check.truthy(f"{name} inside the 1320 column", b and b["x"] >= body["x"] - 1 and b["x"] + b["width"] <= body["x"] + body["width"] + 1,
                     "inside", b)
    _no_overflow(check, sc)
    check.assert_clean()


@_meta("146845", "Page and accordions work at tablet width 768x1024", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146845
@pytest.mark.parametrize("page", [T768], indirect=True)
def test_tablet_768(page):
    """Azure TC 146845 | PBI 130716 — no h-scroll / overlapping text; toggles >= 24x24; grid and checklist fit; expand Head
    + Banking row and tap a CTA card (navigates)."""
    check = _Check("TC 146845")
    sc = SectoralCommitteesPage(page).open_page()
    _no_overflow(check, sc)
    check.equals("clipped text", sc.clipped_text(), [])
    for i, b in enumerate(sc.boxes(sc.ROW_TOGGLE)):
        check.truthy(f"toggle {i + 1} >= 24x24", b["width"] >= 24 and b["height"] >= 24, ">= 24x24", b)
    sc.toggle_lead()
    grid = sc.box(sc.LEAD_PANEL)
    check.truthy("leader grid fits the viewport", grid and grid["x"] >= 0 and grid["x"] + grid["width"] <= 769, "inside 768", grid)
    i = sc.row_index(BANKING)
    sc.toggle_row(i)
    panel = sc.row_child_box(i, sc.ROW_PANEL)
    check.truthy("checklist fits the viewport", panel and panel["x"] >= 0 and panel["x"] + panel["width"] <= 769, "inside 768", panel)
    _no_overflow(check, sc)
    href = sc.attr(sc.CTA_CARD, "href")
    url = sc.click_cta(0)
    check.truthy("CTA card navigates", href and href.split("?")[0] in url, href, url)
    check.assert_clean()


@_meta("146846", "Page matches the Figma mobile layout at 390x844", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_146846
@pytest.mark.parametrize("page", [M390], indirect=True)
def test_mobile_390(page):
    """Azure TC 146846 | PBI 130716 — header 72 high; hero title 24/700/32; section headings 20/700/30; side padding 20;
    search 350x44 full width; rows 350 wide; CTA panel 350 wide, three stacked cards 324x106."""
    check = _Check("TC 146846")
    sc = SectoralCommitteesPage(page).open_page()
    check.px("header height", sc.box(sc.HEADER)["height"], 72)
    check.typo("hero title", sc.styles(sc.HERO_TITLE, TYPO), 24, 700, 32)
    for name, loc in (("sector heading", sc.SECTOR_HEADING), ("directory heading", sc.DIR_HEADING)):
        check.typo(name, sc.styles(loc, TYPO), 20, 700, 30)
    check.px("side padding", sc.box(sc.SEARCH)["x"], 20)
    check.size("search", sc.box(sc.SEARCH), 350, 44)
    for i, b in enumerate(sc.boxes(sc.ROW)):
        check.px(f"row {i + 1} width", b["width"], 350)
    check.px("CTA panel width", sc.box(sc.CTA)["width"], 350)
    cards = sc.boxes(sc.CTA_CARD)
    check.truthy("CTA cards stacked", len(cards) == 3 and all(cards[k]["y"] + cards[k]["height"] <= cards[k + 1]["y"] + 1 for k in range(2)),
                 "stacked", [round(c["y"]) for c in cards])
    for i, c in enumerate(cards):
        check.size(f"CTA card {i + 1}", c, 324, 106)
    _no_overflow(check, sc)
    check.assert_clean()


@_meta("146847", "Page renders with the Figma light theme colours", "Theme")
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.tc_146847
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_light_theme(page):
    """Azure TC 146847 | PBI 130716 — body #FFFFFF; hero brand fill with white text; accents #911731; borders #EDEDED;
    badges #F4E7EA; body/eyebrow text meets WCAG AA on white."""
    check = _Check("TC 146847")
    sc = SectoralCommitteesPage(page).open_page()
    check.truthy("light theme", sc.theme() in (None, "light"), "light", sc.theme())
    check.color("body background", sc.styles(sc.PAGE_BODY, ("background-color",))["background-color"], "#FFFFFF")
    hero = sc.styles(sc.HERO, ("background-image", "background-color"))
    check.truthy("hero brand fill", "gradient" in hero["background-image"] or hero["background-color"] != "rgba(0, 0, 0, 0)", "brand fill", hero)
    check.color("hero title white", sc.styles(sc.HERO_TITLE, ("color",))["color"], "#FFFFFF")
    check.color("accent (eyebrow)", sc.styles(sc.SECTOR_EYEBROW, ("color",))["color"], "#911731")
    check.border("row border", sc.styles(sc.ROW, BOX), "#EDEDED")
    check.color("badge fill", sc.styles(sc.ROW_NUM, ("background-color",))["background-color"], "#F4E7EA")
    # Scope per the case: eyebrow #911731 and body/heading text on white.
    for name, loc in (("sector eyebrow", sc.SECTOR_EYEBROW), ("sector body", sc.SECTOR_BODY), ("directory body", sc.DIR_BODY),
                      ("sector heading", sc.SECTOR_HEADING), ("directory heading", sc.DIR_HEADING)):
        check.equals(f"{name} below WCAG AA", sc.low_contrast_text(loc), [])
    others = sc.low_contrast_text()
    if others:
        check.note("Outside the case's stated scope — Figma-token text below 4.5:1 on white: " + "; ".join(others))
    check.assert_clean()


@_meta("146848", "Page renders with the Figma dark theme colours", "Theme")
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.tc_146848
@pytest.mark.parametrize("page", [D1920], indirect=True)
def test_dark_theme(page):
    """Azure TC 146848 | PBI 130716 — dark: content #1D1D1B; headings #FFFFFF; body #DEDEDD; eyebrows #C44561; row
    borders #4A4A49; badges #360711 with #C44561 numbers; CTA cards #1D1D1B stroke #530B1B, titles #FFFFFF, desc
    #D0D0D0; expanded panel readable."""
    check = _Check("TC 146848")
    sc = SectoralCommitteesPage(page).open_page().enable_dark_mode()
    check.equals("dark theme", sc.theme(), "dark")
    check.color("content background", sc.styles(sc.PAGE_BODY, ("background-color",))["background-color"], "#1D1D1B")
    for name, loc in (("sector heading", sc.SECTOR_HEADING), ("directory heading", sc.DIR_HEADING)):
        check.color(f"{name}", sc.styles(loc, ("color",))["color"], "#FFFFFF")
    for name, loc in (("sector body", sc.SECTOR_BODY), ("directory body", sc.DIR_BODY)):
        check.color(f"{name}", sc.styles(loc, ("color",))["color"], "#DEDEDD")
    for name, loc in (("sector eyebrow", sc.SECTOR_EYEBROW), ("directory eyebrow", sc.DIR_EYEBROW)):
        check.color(f"{name}", sc.styles(loc, ("color",))["color"], "#C44561")
    check.border("row border", sc.styles(sc.ROW, BOX), "#4A4A49")
    check.border("Head card border", sc.styles(sc.LEAD_CARD, BOX), "#4A4A49")
    badge = sc.styles(sc.ROW_NUM, ("background-color", "color"))
    check.color("badge fill", badge["background-color"], "#360711")
    check.color("badge number", badge["color"], "#C44561")
    for i in range(sc.count(sc.CTA_CARD)):
        st = sc.styles(sc.CTA_CARD, BOX, i)
        check.color(f"CTA card {i + 1} fill", st["background-color"], "#1D1D1B")
        check.border(f"CTA card {i + 1}", st, "#530B1B")
        check.color(f"CTA card {i + 1} title", sc.styles(sc.CTA_TITLE, ("color",), i)["color"], "#FFFFFF")
        check.color(f"CTA card {i + 1} description", sc.styles(sc.CTA_DESC, ("color",), i)["color"], "#D0D0D0")
    sc.toggle_row(0)
    # "Readable, no dark text on dark background": 3:1 floor (the case's own eyebrow token #C44561 on #1D1D1B is 3.51:1).
    check.equals("expanded panel: dark-on-dark text (< 3:1)", sc.low_contrast_text("div.qc-sc-row", 3.0, 3.0), [])
    below_aa = sc.low_contrast_text("div.qc-sc-row")
    if below_aa:
        check.note("Expanded panel text between 3:1 and 4.5:1 (design tokens): " + "; ".join(below_aa))
    check.assert_clean()

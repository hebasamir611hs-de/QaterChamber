"""
web/tests/member_services/test_member_services_web.py

Web-platform cases for PBI 129400 ("QC-SVC-001 — Member's Services"),
10 approved Azure Test Cases tagged Automation from suite 137726
(137619, 137620, 137641, 137643, 137645, 137647-137651).

Every test runs in a fresh UNAUTHENTICATED context (`{"auth": False}`
indirect param) — the cached CMS storageState can carry an Arabic
GUEST_LANGUAGE_ID that would flip the English page under xdist.

Token/design cases collect EVERY deviation into one soft-assert report and
fail once with a readable "element.property expected X got Y" list, so one
run surfaces the full mismatch set. Expected values are copied verbatim
from the approved cases; nothing is loosened beyond `px_close`'s 1px
sub-pixel tolerance.

Measurement conventions (disclosed, applied uniformly):
  - "N px padding" on the hero / content container is measured as the
    EFFECTIVE inset — where the content actually starts relative to the
    block's (or viewport's) edge — because the implementation may realise
    Figma padding as margin + padding. The same applies to the Arabic
    supporting image's "40px 0px 40px 40px" spacing (margin + padding summed
    per side).
  - "Leading"/"before" in the Arabic mirroring case (137643 step 4) is read
    VISUALLY, as the mirror of the English layout: the chevron sits to the
    LEFT of the icon tile, and the CTA arrow sits to the LEFT of its label
    and is horizontally flipped (arrow-up-left).
  - Gradient borders are searched for everywhere a gradient border can be
    painted from (own border-image-source / background-image and both
    pseudo-elements). If no gradient exists in any of them, that is
    reported as a mismatch together with the actual solid border.
"""

import re

import allure
import pytest

from core.web.design_tokens import font_family_contains, hex_to_rgb, px_close, weight_matches
from web.pages.member_services.member_services_page import MemberServicesPage

PBI = "129400"
ANON = {"auth": False}
anonymous = pytest.mark.parametrize("page", [ANON], indirect=True)

EN_HEADING = "Choose the service you need"
EN_SIDEBAR_TITLE = "All Services"
AR_SIDEBAR_TITLE = "كافة الخدمات"
EN_SUBHEADINGS = ["Who This Service Is For", "Required Documents", "How to Apply"]
AR_SUBHEADINGS = ["الفئات المستفيدة من الخدمة", "المستندات المطلوبة", "كيفية التقديم"]
AR_SERVICE_NAMES = ["العضوية الجديدة", "تجديد العضوية", "التصديق على التوقيع", "إلغاء المفوّض بالتوقيع"]

TYPO = ("font-family", "font-weight", "font-size", "line-height", "color")

pytestmark = [pytest.mark.web, pytest.mark.svc, pytest.mark.pbi_129400]


# ---------------------------------------------------------------------------
# Soft-assert token report
# ---------------------------------------------------------------------------

def _rgba(text: str):
    parts = [float(v) for v in re.findall(r"[\d.]+", text)]
    return (int(parts[0]), int(parts[1]), int(parts[2]), parts[3] if len(parts) > 3 else 1.0)


def _parse_gradient(value: str):
    m = re.search(r"linear-gradient\((.*)\)", value or "")
    if not m:
        return None
    inner = m.group(1)
    angle_m = re.match(r"\s*([\d.]+)deg", inner)
    if angle_m:
        angle = float(angle_m.group(1))
    else:
        directions = {"to right": 90.0, "to left": 270.0, "to top": 0.0, "to bottom": 180.0}
        angle = next((a for k, a in directions.items() if inner.strip().startswith(k)), 180.0)
    stops = [(_rgba(c), float(p.rstrip("%")) if p else None)
             for c, p in re.findall(r"(rgba?\([^)]*\))\s*([\d.]+%)?", inner)]
    return angle, stops


class TokenReport:
    """Collects every token deviation; `assert_clean()` fails once with all of them."""

    def __init__(self, title: str):
        self.title = title
        self.errors: list[str] = []
        self.notes: list[str] = []

    def fail(self, name: str, expected, actual) -> None:
        self.errors.append(f"{name} expected {expected} got {actual}")

    def check(self, name: str, ok: bool, expected, actual) -> None:
        if not ok:
            self.fail(name, expected, actual)

    def eq(self, name: str, actual, expected) -> None:
        self.check(name, actual == expected, expected, actual)

    def color(self, name: str, actual: str, hex_color: str) -> None:
        expected = hex_to_rgb(hex_color)
        self.check(name, actual == expected, f"{hex_color} ({expected})", actual)

    def px(self, name: str, actual: str | float, expected: str | float, tol: float = 1.0) -> None:
        a = actual if isinstance(actual, str) else f"{actual:.1f}px"
        e = expected if isinstance(expected, str) else f"{expected}px"
        self.check(name, px_close(a, e, tol), e, a)

    def box_px(self, name: str, props: dict, expected: str) -> None:
        """Shorthand box value like '10px 16px' vs per-side computed props."""
        parts = expected.split()
        t, r, b, l = (parts * 4)[:4] if len(parts) == 1 else (
            (parts[0], parts[1], parts[0], parts[1]) if len(parts) == 2 else
            (parts[0], parts[1], parts[2], parts[1]) if len(parts) == 3 else tuple(parts))
        actual = [props[f"{name.split('.')[-1]}-{s}"] for s in ("top", "right", "bottom", "left")]
        ok = all(px_close(a, e) for a, e in zip(actual, (t, r, b, l)))
        self.check(name, ok, expected, " ".join(actual))

    def typography(self, name: str, s: dict, weight: str, size: str, line_height: str, hex_color: str) -> None:
        self.check(f"{name}.font-family", font_family_contains(s["font-family"], "Cairo"), "Cairo", s["font-family"])
        self.check(f"{name}.font-weight", weight_matches(s["font-weight"], weight), weight, s["font-weight"])
        self.px(f"{name}.font-size", s["font-size"], size)
        self.px(f"{name}.line-height", s["line-height"], line_height)
        self.color(f"{name}.color", s["color"], hex_color)

    def gradient(self, name: str, actual: str, angle: float, stops) -> None:
        """stops: [((r, g, b, a), pos_percent_or_None), ...]"""
        expected_txt = f"linear-gradient({angle}deg, " + ", ".join(
            f"rgba{c}" + (f" {p}%" if p is not None else "") for c, p in stops) + ")"
        parsed = _parse_gradient(actual)
        if not parsed:
            self.fail(name, expected_txt, actual or "none")
            return
        a_angle, a_stops = parsed
        self.check(f"{name}.angle", abs(a_angle - angle) <= 0.5, f"{angle}deg", f"{a_angle}deg")
        if len(a_stops) != len(stops):
            self.fail(f"{name}.stops", expected_txt, actual)
            return
        for i, ((ec, ep), (ac, ap)) in enumerate(zip(stops, a_stops), start=1):
            self.check(f"{name}.stop{i}.color", ac[:3] == ec[:3] and abs(ac[3] - ec[3]) <= 0.01,
                       f"rgba{ec}", f"rgba{ac}")
            if ep is not None:
                self.check(f"{name}.stop{i}.position", ap is not None and abs(ap - ep) <= 0.5,
                           f"{ep}%", f"{ap}%" if ap is not None else "none")

    def gradient_border(self, name: str, sources: dict, angle: float, stops) -> None:
        painted = {k: v for k, v in sources.items() if "gradient" in (v or "")}
        if not painted:
            self.fail(name, f"1px {angle}deg gradient border rgba{stops[0][0]} -> rgba{stops[-1][0]}",
                      f"'{sources['self border']}' (no gradient in border-image-source, "
                      f"background-image, ::before or ::after)")
            return
        key, value = next(iter(painted.items()))
        self.gradient(f"{name}[{key}]", value, angle, stops)

    def note(self, text: str) -> None:
        self.notes.append(text)

    def assert_clean(self) -> None:
        if self.notes:
            allure.attach("\n".join(self.notes), "unmeasured / notes", allure.attachment_type.TEXT)
        if self.errors:
            allure.attach("\n".join(self.errors), "token mismatches", allure.attachment_type.TEXT)
        assert not self.errors, (
            f"{self.title}: {len(self.errors)} mismatch(es):\n  - " + "\n  - ".join(self.errors)
        )


def _aligned(report: TokenReport, ms: MemberServicesPage, locators, direction: str) -> None:
    ok_align = ("start", "left") if direction == "ltr" else ("start", "right")
    for loc in locators:
        s = ms.styles(loc, ("direction", "text-align", "font-family"))
        report.eq(f"{loc}.direction", s["direction"], direction)
        report.check(f"{loc}.text-align", s["text-align"] in ok_align, "/".join(ok_align), s["text-align"])
        report.check(f"{loc}.font-family", font_family_contains(s["font-family"], "Cairo"), "Cairo", s["font-family"])


HERO_GRADIENT = (90.0, [((66, 44, 27, 0.8), 16.0), ((145, 23, 49, 0.8), 84.0)])
CARD_BORDER_LIGHT = (135.0, [((246, 246, 246, 1.0), None), ((233, 219, 208, 1.0), None)])
CARD_BORDER_DARK = (135.0, [((52, 52, 50, 1.0), None), ((83, 56, 34, 1.0), None)])


# ---------------------------------------------------------------------------
# Functional-High — language toggle
# ---------------------------------------------------------------------------

@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Language toggle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Switching EN -> AR via the header toggle renders the page in Arabic, RTL")
@allure.label("pbi", PBI)
@allure.label("testcase", "137619")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.uat
@pytest.mark.tc_137619
@anonymous
def test_language_toggle_en_to_ar(page):
    """Azure TC 137619 | PBI 129400 — EN list view -> 'AR' toggle -> Arabic RTL."""
    report = TokenReport("TC 137619")
    with allure.step("Open the English list view"):
        ms = MemberServicesPage(page).open_list()
        report.eq("heading.text", ms.text(ms.HEADING).strip(), EN_HEADING)

    with allure.step("Click the 'AR' language toggle"):
        report.eq("lang-toggle.label (before)", ms.language_toggle_label(), "AR")
        ms.toggle_language()

    with allure.step("Page renders Arabic RTL; toggle offers 'EN'; Arabic service names in order"):
        report.eq("html.dir", ms.document_dir(), "rtl")
        report.eq("section.dir", ms.root_dir(), "rtl")
        report.eq("lang-toggle.label (after)", ms.language_toggle_label(), "EN")
        report.eq("service names", ms.card_names(), AR_SERVICE_NAMES)
    report.assert_clean()


@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Language toggle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Switching AR -> EN on the detail view restores English LTR and keeps the selected service")
@allure.label("pbi", PBI)
@allure.label("testcase", "137620")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.tc_137620
@anonymous
def test_language_toggle_ar_to_en_keeps_selection(page):
    """Azure TC 137620 | PBI 129400 — AR detail view -> 'EN' toggle -> English LTR,
    same service selected, English subsection headings."""
    report = TokenReport("TC 137620")
    with allure.step("Open the Arabic detail view (New Membership)"):
        ms = MemberServicesPage(page).open_detail(locale="ar")
        report.eq("html.dir (AR)", ms.document_dir(), "rtl")
        report.eq("sidebar title (AR)", ms.side_head_text(), AR_SIDEBAR_TITLE)

    with allure.step("Record the selected service"):
        selected = ms.active_service_key()
        assert selected, "no service is selected in the Arabic sidebar"

    with allure.step("Click the 'EN' language toggle"):
        ms.toggle_language()

    with allure.step("English LTR, 'All Services', same service selected, EN subsection headings"):
        report.eq("html.dir (EN)", ms.document_dir(), "ltr")
        report.check("detail view shown after switch", ms.is_detail_view(), "detail view visible",
                     f"list view visible={ms.is_list_view()} (url={ms.current_url()})")
        if ms.is_visible(ms.SIDE_HEAD):
            report.eq("sidebar title (EN)", ms.side_head_text(), EN_SIDEBAR_TITLE)
        else:
            report.fail("sidebar title (EN)", EN_SIDEBAR_TITLE, "sidebar not rendered")
        report.eq("selected service", ms.active_service_key(), selected)
        report.eq("subsection headings", ms.subheadings() if ms.is_detail_view() else [], EN_SUBHEADINGS)
    report.assert_clean()


# ---------------------------------------------------------------------------
# UI — Figma tokens
# ---------------------------------------------------------------------------

@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Design tokens")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("English page renders LTR and matches the approved Figma tokens")
@allure.label("pbi", PBI)
@allure.label("testcase", "137641")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_137641
@anonymous
def test_en_ltr_figma_tokens(page):
    """Azure TC 137641 | PBI 129400 — EN LTR + Figma tokens for frames 2343:88589
    (listing) and 2343:88607 (New Membership detail)."""
    report = TokenReport("TC 137641")
    ms = MemberServicesPage(page).open_list()

    with allure.step("S1: LTR, left-aligned, Cairo"):
        report.eq("html.dir", ms.document_dir(), "ltr")
        _aligned(report, ms, (ms.HERO_TITLE, ms.HEADING, ms.INTRO, ms.CARD_NAME, ms.CARD_DESC), "ltr")

    with allure.step("S2: hero banner and section heading block"):
        hero, title = ms.box(ms.HERO), ms.box(ms.HERO_TITLE)
        report.px("hero.height", hero["height"], 140)
        report.px("hero.padding-top (effective inset)", title["top"] - hero["top"], 40)
        report.px("hero.padding-left (effective inset)", title["left"] - hero["left"], 300)
        report.gradient("hero.background", ms.styles(ms.HERO_OVERLAY, ("background-image",))["background-image"],
                        *HERO_GRADIENT)
        report.typography("hero-title", ms.styles(ms.HERO_TITLE, TYPO), "Bold", "30px", "38px", "#FFFFFF")
        content = ms.styles(ms.CONTENT, ("padding-top", "padding-bottom", "row-gap"))
        report.px("content.padding-top", content["padding-top"], "64px")
        report.px("content.padding-bottom", content["padding-bottom"], "64px")
        report.px("content.padding-left (effective inset from viewport)", ms.content_box(ms.CONTENT)["left"], 300)
        report.px("content.gap", content["row-gap"], "40px")
        report.typography("heading", ms.styles(ms.HEADING, TYPO), "Bold", "36px", "44px", "#1D1D1B")
        report.typography("intro", ms.styles(ms.INTRO, TYPO), "Medium", "14px", "22px", "#7C7B7B")
        report.px("intro.width", ms.box(ms.INTRO)["width"], 536)
        heading, intro = ms.box(ms.HEADING), ms.box(ms.INTRO)
        report.check("intro placement", intro["left"] >= heading["right"] and intro["top"] < heading["bottom"],
                     "beside the heading", f"heading={heading} intro={intro}")

    with allure.step("S3: service card and Details button"):
        card = ms.styles(ms.CARD, ("background-color", "border-top-left-radius", "padding-top", "padding-right",
                                   "padding-bottom", "padding-left", "column-gap", "box-shadow"))
        report.color("card.background-color", card["background-color"], "#FFFFFF")
        report.px("card.border-radius", card["border-top-left-radius"], "12px")
        report.box_px("card.padding", card, "20px")
        report.px("card.gap", card["column-gap"], "24px")
        report.gradient_border("card.border", ms.gradient_border_sources(ms.CARD), *CARD_BORDER_LIGHT)
        report.eq("card.box-shadow", card["box-shadow"], "rgba(29, 29, 27, 0.1) 0px 5px 80px 0px")
        report.px("cards.gap", ms.styles(ms.CARDS, ("row-gap",))["row-gap"], "12px")
        pill = ms.styles(ms.CARD_CTA, ("border-top-left-radius", "background-color", "border-top-width",
                                       "border-top-style", "border-top-color", "padding-top", "padding-right",
                                       "padding-bottom", "padding-left", "column-gap"))
        report.eq("details.border-radius", pill["border-top-left-radius"], "9999px")
        report.color("details.background-color", pill["background-color"], "#FFFFFF")
        report.eq("details.border", f"{pill['border-top-width']} {pill['border-top-style']}", "1px solid")
        report.color("details.border-color", pill["border-top-color"], "#DEDEDD")
        report.box_px("details.padding", pill, "10px 16px")
        report.px("details.gap", pill["column-gap"], "6px")
        icon = ms.box(ms.CARD_CTA_ICON)
        report.eq("details.icon.size", (round(icon["width"]), round(icon["height"])), (20, 20))

    with allure.step("S4: New Membership detail view content panel"):
        ms.open_service(ms.NEW_MEMBERSHIP)
        det = ms.styles(ms.DETAIL, ("border-top-width", "border-top-style", "border-top-color", "border-top-left-radius"))
        report.eq("detail.border", f"{det['border-top-width']} {det['border-top-style']}", "1px solid")
        report.color("detail.border-color", det["border-top-color"], "#EDEDED")
        report.px("detail.border-radius", det["border-top-left-radius"], "16px")
        detail, side, vdiv = ms.box(ms.DETAIL), ms.box(ms.SIDEBAR), ms.box(ms.VDIVIDER)
        panel, support = ms.box(ms.PANEL), ms.box(ms.DETAIL_SUPPORT)
        report.px("sidebar.width", side["width"], 312)
        report.check("sidebar position", abs(side["left"] - detail["left"]) <= 2, "left edge of the container",
                     f"sidebar.left={side['left']} container.left={detail['left']}")
        report.px("divider.width", vdiv["width"], 1)
        report.color("divider.color", ms.styles(ms.VDIVIDER, ("background-color",))["background-color"], "#EDEDED")
        report.check("sidebar -> divider -> panel order", side["right"] <= vdiv["left"] + 1 <= panel["left"] + 1,
                     "sidebar, divider, panel left-to-right", f"side={side} divider={vdiv} panel={panel}")
        p = ms.styles(ms.PANEL, ("padding-top", "padding-right", "padding-bottom", "padding-left", "row-gap"))
        report.box_px("panel.padding", p, "40px")
        report.px("panel.gap", p["row-gap"], "12px")
        for i in range(ms.count(ms.SUBHEADING)):
            report.typography(f"subheading[{i}]", ms.styles(ms.SUBHEADING, TYPO, nth=i), "Bold", "16px", "24px", "#A66F43")
        for i in range(ms.count(ms.BODY_TEXT)):
            report.typography(f"body[{i}]", ms.styles(ms.BODY_TEXT, TYPO, nth=i), "Medium", "14px", "22px", "#4A4A49")
        for i in range(ms.count(ms.REQ_DOCS_ITEM)):
            dash = ms.styles(ms.REQ_DOCS_ITEM, ("content", "height", "background-color"), pseudo="::before", nth=i)
            report.check(f"required-doc[{i}]::before", dash["content"] not in ("none", "normal", ""),
                         "dash marker", f"content={dash['content']}")
            report.px(f"required-doc[{i}]::before.thickness", dash["height"], "1px")
            report.color(f"required-doc[{i}]::before.color", dash["background-color"], "#A66F43")
        report.px("required-docs.gap", ms.styles(ms.REQ_DOCS_LIST, ("row-gap",))["row-gap"], "4px")
        report.px("support-image.width", support["width"], 312)
        rad = ms.styles(ms.DETAIL_SUPPORT, ("border-top-right-radius", "border-bottom-right-radius"))
        report.px("support-image.border-top-right-radius", rad["border-top-right-radius"], "12px")
        report.px("support-image.border-bottom-right-radius", rad["border-bottom-right-radius"], "12px")
    report.assert_clean()


@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Design tokens")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Arabic page renders RTL with list, sidebar and panel mirrored")
@allure.label("pbi", PBI)
@allure.label("testcase", "137643")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.uat
@pytest.mark.tc_137643
@anonymous
def test_ar_rtl_mirroring(page):
    """Azure TC 137643 | PBI 129400 — AR mirroring against 2327:80393 (Desktop, AR).

    Step 4 "leading"/"before" is read visually as the mirror of English
    (see module docstring)."""
    report = TokenReport("TC 137643")
    ms = MemberServicesPage(page).open_list(locale="ar")

    with allure.step("S1: RTL, right-aligned, Cairo"):
        report.eq("html.dir", ms.document_dir(), "rtl")
        _aligned(report, ms, (ms.HERO_TITLE, ms.HEADING, ms.INTRO, ms.CARD_NAME, ms.CARD_DESC), "rtl")
        report.eq("service names (list)", ms.card_names(), AR_SERVICE_NAMES)

    with allure.step("S2/S3: open a detail view; Arabic labels and mirrored placement"):
        ms.open_service(ms.NEW_MEMBERSHIP)
        report.eq("sidebar title", ms.side_head_text(), AR_SIDEBAR_TITLE)
        report.eq("service names (sidebar)", ms.side_labels(), AR_SERVICE_NAMES)
        report.eq("subsection headings", ms.subheadings(), AR_SUBHEADINGS)
        _aligned(report, ms, (ms.SUBHEADING, ms.BODY_TEXT), "rtl")
        detail, side = ms.box(ms.DETAIL), ms.box(ms.SIDEBAR)
        panel, support = ms.box(ms.PANEL), ms.box(ms.DETAIL_SUPPORT)
        report.check("placement", support["right"] <= panel["left"] + 1 and panel["right"] <= side["left"] + 1,
                     "image left, panel middle, sidebar right",
                     f"image={support['left']:.0f}-{support['right']:.0f} panel={panel['left']:.0f}-"
                     f"{panel['right']:.0f} sidebar={side['left']:.0f}-{side['right']:.0f}")
        report.px("sidebar.width", side["width"], 312)
        report.check("sidebar at right edge", abs(side["right"] - detail["right"]) <= 2, "right edge of container",
                     f"sidebar.right={side['right']} container.right={detail['right']}")
        sp = ms.styles(ms.DETAIL_SUPPORT, [f"{k}-{s}" for k in ("margin", "padding")
                                           for s in ("top", "right", "bottom", "left")])
        eff = [float(sp[f"margin-{s}"].rstrip("px")) + float(sp[f"padding-{s}"].rstrip("px"))
               for s in ("top", "right", "bottom", "left")]
        report.check("support-image spacing (margin+padding)", all(abs(a - e) <= 1 for a, e in zip(eff, (40, 0, 40, 40))),
                     "40px 0px 40px 40px", " ".join(f"{v:g}px" for v in eff))

    with allure.step("S4: selected row border side, row icon order, CTA icon"):
        row = ms.styles(ms.SIDE_ITEM_ACTIVE, ("border-right-width", "border-right-style", "border-right-color",
                                              "border-left-width", "border-left-color"))
        report.eq("selected-row.border-right", f"{row['border-right-width']} {row['border-right-style']}", "1px solid")
        report.color("selected-row.border-right-color", row["border-right-color"], "#911731")
        report.check("selected-row.border-left", row["border-left-width"] == "0px"
                     or row["border-left-color"] != hex_to_rgb("#911731"), "no maroon left border",
                     f"{row['border-left-width']} {row['border-left-color']}")
        for i in range(ms.count(ms.SIDE_ITEM)):
            chev = ms.box(f"{ms.SIDE_ITEM} {ms.SIDE_CHEVRON}", i)
            tile = ms.box(f"{ms.SIDE_ITEM} {ms.SIDE_ICON_TILE}", i)
            report.check(f"row[{i}] icon order", chev["right"] <= tile["left"] + 1,
                         "chevron left of icon tile", f"chevron.left={chev['left']:.0f} tile.left={tile['left']:.0f}")
            tf = ms.styles(f"{ms.SIDE_ITEM} {ms.SIDE_CHEVRON}", ("transform",), nth=i)["transform"]
            report.check(f"row[{i}] chevron direction", tf.startswith("matrix(-1"), "mirrored (chevron-left)", tf)
        icon, label = ms.box(ms.CTA_ICON), ms.box(ms.CTA_LABEL)
        report.eq("cta.icon.size", (round(icon["width"]), round(icon["height"])), (20, 20))
        report.check("cta.icon position", icon["right"] <= label["left"] + 1, "icon left of label (mirrored)",
                     f"icon.left={icon['left']:.0f} label.left={label['left']:.0f}")
        tf = ms.styles(ms.CTA_ICON, ("transform",))["transform"]
        report.check("cta.icon direction", tf.startswith("matrix(-1"), "mirrored (arrow-up-left)", tf)
    report.assert_clean()


@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Design tokens")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Selected sidebar service is visually distinguished from unselected services")
@allure.label("pbi", PBI)
@allure.label("testcase", "137645")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_137645
@anonymous
def test_sidebar_selected_vs_unselected_tokens(page):
    """Azure TC 137645 | PBI 129400 — menu-Hover (2307:74966) vs menu (2307:74961), EN."""
    report = TokenReport("TC 137645")
    ms = MemberServicesPage(page).open_detail(MemberServicesPage.NEW_MEMBERSHIP)

    with allure.step("S1: sidebar and title"):
        report.px("sidebar.width", ms.box(ms.SIDEBAR)["width"], 312)
        report.eq("sidebar.title.text", ms.side_head_text(), EN_SIDEBAR_TITLE)
        head = ms.styles(ms.SIDE_HEAD, TYPO + ("padding-top", "padding-right", "padding-bottom", "padding-left"))
        report.typography("sidebar.title", head, "SemiBold", "18px", "28px", "#1D1D1B")
        report.box_px("sidebar.title.padding", head, "12px 16px")

    row_props = ("background-color", "border-left-width", "border-left-style", "border-left-color",
                 "padding-top", "padding-right", "padding-bottom", "padding-left", "column-gap")
    tile_props = ("width", "height", "background-color", "border-top-left-radius")

    with allure.step("S2: selected row 'New Membership'"):
        report.eq("selected row key", ms.active_service_key(), ms.NEW_MEMBERSHIP)
        row = ms.styles(ms.SIDE_ITEM_ACTIVE, row_props)
        report.color("selected.background-color", row["background-color"], "#F4E7EA")
        report.eq("selected.border-left", f"{row['border-left-width']} {row['border-left-style']}", "1px solid")
        report.color("selected.border-left-color", row["border-left-color"], "#911731")
        report.box_px("selected.padding", row, "16px")
        report.px("selected.gap", row["column-gap"], "12px")
        tile = ms.styles(f"{ms.SIDE_ITEM_ACTIVE} {ms.SIDE_ICON_TILE}", tile_props)
        report.eq("selected.icon-tile.size", (tile["width"], tile["height"]), ("36px", "36px"))
        report.color("selected.icon-tile.background-color", tile["background-color"], "#911731")
        report.px("selected.icon-tile.border-radius", tile["border-top-left-radius"], "6px")
        report.typography("selected.label", ms.styles(f"{ms.SIDE_ITEM_ACTIVE} {ms.SIDE_LABEL}", TYPO),
                          "SemiBold", "14px", "22px", "#911731")

    with allure.step("S3: the three unselected rows"):
        n = ms.count(ms.SIDE_ITEM_INACTIVE)
        report.eq("unselected row count", n, 3)
        maroon = hex_to_rgb("#911731")
        for i in range(n):
            row = ms.styles(ms.SIDE_ITEM_INACTIVE, row_props, nth=i)
            report.eq(f"unselected[{i}].background-color", row["background-color"], "rgba(0, 0, 0, 0)")
            report.check(f"unselected[{i}].border-left", row["border-left-color"] != maroon or row["border-left-width"] == "0px",
                         "no maroon border", f"{row['border-left-width']} {row['border-left-color']}")
            tile = ms.styles(f"{ms.SIDE_ITEM_INACTIVE} {ms.SIDE_ICON_TILE}", tile_props, nth=i)
            report.eq(f"unselected[{i}].icon-tile.size", (tile["width"], tile["height"]), ("36px", "36px"))
            report.color(f"unselected[{i}].icon-tile.background-color", tile["background-color"], "#F6F0EC")
            report.px(f"unselected[{i}].icon-tile.border-radius", tile["border-top-left-radius"], "6px")
            report.typography(f"unselected[{i}].label", ms.styles(f"{ms.SIDE_ITEM_INACTIVE} {ms.SIDE_LABEL}", TYPO, nth=i),
                              "SemiBold", "14px", "22px", "#1D1D1B")

    with allure.step("S4: exactly one selected; 1px #F6F6F6 dividers between rows"):
        report.eq("rows with selected style", ms.active_row_count(), 1)
        report.eq("rows with aria-selected=true", ms.aria_selected_count(), 1)
        rows = ms.styles_all(ms.SIDE_ITEM, ("border-top-width", "border-top-style", "border-top-color"))
        for i, r in enumerate(rows[1:], start=1):
            report.eq(f"row[{i}] divider", f"{r['border-top-width']} {r['border-top-style']}", "1px solid")
            report.color(f"row[{i}] divider color", r["border-top-color"], "#F6F6F6")
    report.assert_clean()


# ---------------------------------------------------------------------------
# Compatibility — viewports
# ---------------------------------------------------------------------------

@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Desktop 1920x1080 layout: list row and detail row per Figma")
@allure.label("pbi", PBI)
@allure.label("testcase", "137647")
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.tc_137647
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_desktop_1920_layout(page):
    """Azure TC 137647 | PBI 129400 — ENV-1 desktop layout at 1920x1080."""
    report = TokenReport("TC 137647")
    ms = MemberServicesPage(page).open_list()

    with allure.step("No horizontal scrollbar"):
        report.check("horizontal overflow", ms.horizontal_overflow_px() <= 0, "0px",
                     f"{ms.horizontal_overflow_px()}px {ms.overflowing_elements()}")

    with allure.step("List view: cards left, 312px image right, 64px/300px container padding"):
        cards, support = ms.box(ms.CARDS), ms.box(ms.LIST_SUPPORT)
        report.check("list row", cards["right"] <= support["left"] and abs(cards["top"] - support["top"]) <= 1,
                     "cards column left of image, same row", f"cards={cards} image={support}")
        report.px("list image.width", support["width"], 312)
        c = ms.styles(ms.CONTENT, ("padding-top", "padding-bottom"))
        cb = ms.content_box(ms.CONTENT)
        report.px("content.padding-top", c["padding-top"], "64px")
        report.px("content.padding-bottom", c["padding-bottom"], "64px")
        report.px("content.padding-left (effective inset from viewport)", cb["left"], 300)
        report.px("content.padding-right (effective inset from viewport)", 1920 - cb["right"], 300)

    with allure.step("Detail view: sidebar | divider | panel | image row; CTA hugs its content"):
        ms.open_service(ms.NEW_MEMBERSHIP)
        side, vdiv, panel, img = (ms.box(x) for x in (ms.SIDEBAR, ms.VDIVIDER, ms.PANEL, ms.DETAIL_SUPPORT))
        report.check("detail row order", side["right"] <= vdiv["left"] + 1 and vdiv["right"] <= panel["left"] + 1
                     and panel["right"] <= img["left"] + 1, "sidebar, divider, panel, image left-to-right",
                     f"side={side['left']:.0f} divider={vdiv['left']:.0f} panel={panel['left']:.0f} image={img['left']:.0f}")
        report.px("sidebar.width", side["width"], 312)
        report.px("divider.width", vdiv["width"], 1)
        report.px("detail image.width", img["width"], 312)
        cta, pc = ms.box(ms.CTA), ms.content_box(ms.PANEL)
        report.check("cta hugs content", cta["width"] < pc["width"] - 20, "narrower than the panel",
                     f"cta={cta['width']:.0f}px panel content={pc['width']:.0f}px")
    report.assert_clean()


@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Tablet 768x1024: no horizontal scroll or clipping; list and detail stay usable")
@allure.label("pbi", PBI)
@allure.label("testcase", "137648")
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.tc_137648
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_tablet_768_integrity(page):
    """Azure TC 137648 | PBI 129400 — ENV-2 responsive integrity at 768x1024."""
    report = TokenReport("TC 137648")
    ms = MemberServicesPage(page).open_list()

    with allure.step("No horizontal scrollbar and no clipped content"):
        report.check("horizontal overflow", ms.horizontal_overflow_px() <= 0, "0px",
                     f"{ms.horizontal_overflow_px()}px, overflowing: {ms.overflowing_elements()}")
        report.eq("clipped text elements", ms.clipped_text_elements(), [])

    with allure.step("All four cards render icon, name, description and Details without overlap"):
        cards = ms.boxes(ms.CARD)
        report.eq("card count", len(cards), 4)
        for i, card in enumerate(cards):
            parts = {name: ms.box(f"{ms.CARD} {sel}", i) for name, sel in
                     (("icon", ms.CARD_ICON_TILE), ("name", ms.CARD_NAME), ("desc", ms.CARD_DESC), ("details", ms.CARD_CTA))}
            for name, b in parts.items():
                report.check(f"card[{i}].{name}", b["width"] > 0 and b["height"] > 0
                             and b["left"] >= card["left"] - 1 and b["right"] <= card["right"] + 1,
                             "visible inside the card", f"{b} card={card}")
            names = list(parts)
            for a in range(len(names)):
                for c in range(a + 1, len(names)):
                    pa, pb = parts[names[a]], parts[names[c]]
                    overlap = (pa["left"] < pb["right"] - 1 and pb["left"] < pa["right"] - 1
                               and pa["top"] < pb["bottom"] - 1 and pb["top"] < pa["bottom"] - 1)
                    report.check(f"card[{i}] {names[a]}/{names[c]} overlap", not overlap, "no overlap", f"{pa} vs {pb}")
        sup, img = ms.box(ms.LIST_SUPPORT), ms.box(ms.LIST_SUPPORT_IMG)
        report.check("list image containment", img["left"] >= sup["left"] - 1 and img["right"] <= sup["right"] + 1,
                     "image inside its container", f"img={img} container={sup}")

    with allure.step("Detail view: sidebar, panel, image visible; headings/body readable; CTA tappable"):
        ms.open_service(ms.NEW_MEMBERSHIP)
        for name, loc in (("sidebar", ms.SIDEBAR), ("panel", ms.PANEL), ("image", ms.DETAIL_SUPPORT)):
            report.check(f"{name} visible", ms.is_visible(loc), "visible", "not visible")
        report.eq("subsection headings", ms.subheadings(), EN_SUBHEADINGS)
        report.check("body text visible", ms.count(ms.BODY_TEXT) > 0 and ms.is_visible(f"{ms.BODY_TEXT} >> nth=0"),
                     "visible", "not visible")
        cta = ms.box(ms.CTA)
        report.check("cta fully visible", ms.is_visible(ms.CTA) and cta["left"] >= 0 and cta["right"] <= 768,
                     "within the 768px viewport", f"{cta}")
        report.check("cta tap target", cta["height"] >= 44, ">= 44px tall", f"{cta['height']:.0f}px")
    report.assert_clean()


@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Mobile 375x812: detail view stacks in one column; CTA full width")
@allure.label("pbi", PBI)
@allure.label("testcase", "137649")
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_137649
@pytest.mark.parametrize("page", [{"viewport": (375, 812), "auth": False}], indirect=True)
def test_mobile_375_stacking(page):
    """Azure TC 137649 | PBI 129400 — ENV-3 against 2327:80203 (Device=Mobile, EN)."""
    report = TokenReport("TC 137649")
    ms = MemberServicesPage(page).open_list()

    with allure.step("No horizontal scrollbar"):
        report.check("horizontal overflow", ms.horizontal_overflow_px() <= 0, "0px",
                     f"{ms.horizontal_overflow_px()}px {ms.overflowing_elements()}")

    with allure.step("New Membership detail: single column, 40px gaps, bordered list first"):
        ms.open_service(ms.NEW_MEMBERSHIP)
        side, panel, img = ms.box(ms.SIDEBAR), ms.box(ms.PANEL), ms.box(ms.DETAIL_SUPPORT)
        report.check("stack order", side["bottom"] <= panel["top"] + 1 and panel["bottom"] <= img["top"] + 1,
                     "All Services, then panel, then image", f"side={side} panel={panel} image={img}")
        report.check("single column", abs(side["left"] - panel["left"]) <= 1 and abs(panel["left"] - img["left"]) <= 1,
                     "same left edge", f"{side['left']:.0f}/{panel['left']:.0f}/{img['left']:.0f}")
        report.px("gap sidebar->panel", panel["top"] - side["bottom"], 40)
        report.px("gap panel->image", img["top"] - panel["bottom"], 40)
        s = ms.styles(ms.SIDEBAR, ("border-top-width", "border-top-style", "border-top-color", "border-top-left-radius"))
        report.eq("all-services.border", f"{s['border-top-width']} {s['border-top-style']}", "1px solid")
        report.color("all-services.border-color", s["border-top-color"], "#EDEDED")
        report.px("all-services.border-radius", s["border-top-left-radius"], "8px")

    with allure.step("All Services shown in full (not a dropdown); CTA stretches full panel width"):
        rows = ms.boxes(ms.SIDE_ITEM)
        report.check("all services rows visible", len(rows) == 4 and all(r["visible"] for r in rows),
                     "4 visible stacked rows", f"{[r['visible'] for r in rows]}")
        report.check("rows stacked", all(rows[i]["bottom"] <= rows[i + 1]["top"] + 1 for i in range(len(rows) - 1)),
                     "vertical list", f"{[round(r['top']) for r in rows]}")
        report.eq("dropdown controls in sidebar", ms.count(ms.SIDEBAR_DROPDOWN), 0)
        cta, pc = ms.box(ms.CTA), ms.content_box(ms.PANEL)
        report.px("cta.width (full panel content width)", cta["width"], pc["width"], tol=2)
    report.assert_clean()


@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Light mode colours match Figma frame 2343:88589")
@allure.label("pbi", PBI)
@allure.label("testcase", "137650")
@pytest.mark.compatibility
@pytest.mark.tc_137650
@anonymous
def test_light_mode_colours(page):
    """Azure TC 137650 | PBI 129400 — ST-16 light mode (site default theme)."""
    report = TokenReport("TC 137650")
    ms = MemberServicesPage(page).open_list()
    report.check("theme", ms.theme() in (None, "light"), "light", ms.theme())
    _theme_colours(report, ms, light=True)
    report.assert_clean()


@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Dark mode colours match Figma frame 2343:96670")
@allure.label("pbi", PBI)
@allure.label("testcase", "137651")
@pytest.mark.compatibility
@pytest.mark.tc_137651
@anonymous
def test_dark_mode_colours(page):
    """Azure TC 137651 | PBI 129400 — ST-17 dark mode via the accessibility widget.

    UNMEASURED: "the profile icon button is #C44561" — the anonymous header
    renders no profile control (live header controls: nav links, language
    chip, Accessibility tools, Search), so there is no element to measure.
    Recorded as a note in the Allure report, not silently passed or failed."""
    report = TokenReport("TC 137651")
    ms = MemberServicesPage(page).open_list()
    light_hero = ms.styles(ms.HERO_OVERLAY, ("background-image",))["background-image"]
    light_footer = ms.styles(ms.FOOTER, ("background-image",))["background-image"]
    ms.enable_dark_mode()
    report.eq("theme", ms.theme(), "dark")
    _theme_colours(report, ms, light=False)
    report.note("profile icon button #C44561: not measurable — no profile control in the anonymous header")
    report.eq("hero gradient unchanged", ms.styles(ms.HERO_OVERLAY, ("background-image",))["background-image"], light_hero)
    report.eq("footer gradient unchanged", ms.styles(ms.FOOTER, ("background-image",))["background-image"], light_footer)
    report.assert_clean()


def _theme_colours(report: TokenReport, ms: MemberServicesPage, light: bool) -> None:
    t = {
        "page": "#FFFFFF" if light else "#1D1D1B",
        "nav": "#1D1D1B" if light else "#FFFFFF",
        "heading": "#1D1D1B" if light else "#FFFFFF",
        "intro": "#7C7B7B" if light else "#D0D0D0",
        "chip_bg": "#EDEDED" if light else "#4A4A49",
        "chip_text": "#6C6C6B" if light else "#DEDEDD",
        "card": "#FFFFFF" if light else "#1D1D1B",
        "tile": "#F6F0EC" if light else "#422C1B",
        "name": "#1D1D1B" if light else "#FFFFFF",
        "desc": "#7C7B7B" if light else "#D0D0D0",
        "pill_bg": "#FFFFFF" if light else "#1D1D1B",
        "pill_border": "#DEDEDD" if light else "#6C6C6B",
    }
    with allure.step("Page background, header and section heading"):
        report.color("page.background-color", ms.styles(ms.PAGE_BODY, ("background-color",))["background-color"], t["page"])
        report.color("header.background-color", ms.styles(ms.HEADER, ("background-color",))["background-color"], t["page"])
        nav_colours = sorted({s["color"] for s in ms.styles_all(ms.HEADER_NAV_LINK, ("color",))})
        for colour in nav_colours:
            report.color("header nav label.color", colour, t["nav"])
        report.color("heading.color", ms.styles(ms.HEADING, ("color",))["color"], t["heading"])
        report.color("intro.color", ms.styles(ms.INTRO, ("color",))["color"], t["intro"])
        chip = ms.styles(ms.LANG_TOGGLE, ("background-color", "color"))
        report.color("language-chip.background-color", chip["background-color"], t["chip_bg"])
        report.color("language-chip.color", chip["color"], t["chip_text"])

    with allure.step("Service card"):
        report.color("card.background-color", ms.styles(ms.CARD, ("background-color",))["background-color"], t["card"])
        report.gradient_border("card.border", ms.gradient_border_sources(ms.CARD),
                               *(CARD_BORDER_LIGHT if light else CARD_BORDER_DARK))
        report.color("icon-tile.background-color", ms.styles(ms.CARD_ICON_TILE, ("background-color",))["background-color"], t["tile"])
        report.color("service-name.color", ms.styles(ms.CARD_NAME, ("color",))["color"], t["name"])
        report.color("short-description.color", ms.styles(ms.CARD_DESC, ("color",))["color"], t["desc"])
        pill = ms.styles(ms.CARD_CTA, ("background-color", "border-top-color"))
        report.color("details.background-color", pill["background-color"], t["pill_bg"])
        report.color("details.border-color", pill["border-top-color"], t["pill_border"])

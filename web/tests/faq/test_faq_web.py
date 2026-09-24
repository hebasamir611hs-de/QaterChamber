"""
web/tests/faq/test_faq_web.py

Web-platform cases for PBI 131052 ("QC - 001 - FAQ Knowledge Base"), suite
140390 — 19 approved Automation cases: 141645-141654 (Figma tokens),
141655/141656 (EN LTR / AR RTL), 141657/141658 (light/dark theme),
141659/141660 (normal/high contrast), 141661-141663 (1920 / 768 / 375).

Every test runs in a fresh UNAUTHENTICATED context and collects every
expected-vs-actual deviation, failing once with the full list.

Token source (QA Manager ruling 2026-09-24): Figma file
J3e1thav8NIu6a3XhC6Wcl, frame 6974:212595 "Lang=EN, View=Desktop,
Darkmode=False". Token names in the cases are resolved from THAT file's
style/fill defs, never from a generic scale:
    display-sm/Bold   = Cairo 700 / 36px / 44px
    Text-md/Regular   = Cairo 400 / 16px / 24px
    Text-md/Semibold  = Cairo 600 / 16px / 24px
    Text-md/Bold      = Cairo 700 / 16px / 24px
    Text-sm/Regular   = Cairo 400 / 14px / 22px (Figma alignment RIGHT)
    fill_658ab2fa = #FFFFFF, fill_11bddc20 = #911731, fill_576dfc44 = #1D1D1B,
    fill_a6c48a10 = #343432, fill_b857e869 = #EDEDED, fill_d9f491bf = #A8A8A7
  Where the case itself states a value (hex/px) and Figma does not contradict
  it (subtext rgba(255,255,255,0.7) and 648px, search pill 9999px radius,
  Load More #4A4A49 label), the case value is used. Values absent from the
  file are recorded as UNMEASURED notes, never guessed.
  TEST DATA (seeded-content) differences — the total question count and the
  first question's text — are reported as notes and never fail a test on
  their own; the product parts of those strings (page size, wording) still
  assert.
  - Figma controls the live build does not render (Search button, "Browse by
    topic" eyebrow, H2, "Select Category" dropdown, "Load More") are looked
    up semantically and reported "not rendered" with the live counterpart.
  - "Legible"/"low-contrast" = WCAG AA (4.5:1 normal, 3:1 large text); text
    on a gradient is measured against its worst-case colour stop.
  - Touch targets: a decorative icon's target is its clickable ancestor.
"""

import re

import allure
import pytest

from core.web.design_tokens import font_family_contains, hex_to_rgb, px_close, weight_matches
from web.pages.faq.faq_page import FaqPage

PBI = "131052"
ANON = {"auth": False}
anonymous = pytest.mark.parametrize("page", [ANON], indirect=True)

DISPLAY_SM = ("36px", "44px")   # display-sm/Bold (Figma 6974:212595)
TEXT_MD = ("16px", "24px")      # Text-md/Regular | Semibold | Bold
TEXT_SM = ("14px", "22px")      # Text-sm/Regular (8715:147919)
AA_NORMAL, AA_LARGE = 4.5, 3.0
TAP = 44.0
TYPO = ("font-family", "font-weight", "font-size", "line-height", "color")
ARABIC = re.compile(r"[؀-ۿ]")

pytestmark = [pytest.mark.web, pytest.mark.pbi_131052]


class _Check:
    """Soft-assert collector; tests end with `check.assert_clean()`."""

    def __init__(self, title: str):
        self.title = title
        self.deviations = []
        self.notes = []

    def truthy(self, label, condition, expected, actual):
        if not condition:
            self.deviations.append(f"{label}: expected {expected!r}, got {actual!r}")

    def equals(self, label, actual, expected):
        self.truthy(label, actual == expected, expected, actual)

    def color(self, label, actual, hex_color):
        self.truthy(label, actual == hex_to_rgb(hex_color), f"{hex_color} ({hex_to_rgb(hex_color)})", actual)

    def type_scale(self, name, s, weight, scale):
        self.truthy(f"{name}.font-family", font_family_contains(s["font-family"]), "Cairo", s["font-family"])
        self.truthy(f"{name}.font-weight", weight_matches(s["font-weight"], weight), weight, s["font-weight"])
        # Computed font-size/line-height are exact CSS values (no sub-pixel noise), so a
        # tight 0.25px tolerance is used — px_close's 1px default would hide 15px vs 14px.
        self.truthy(f"{name}.font-size", px_close(s["font-size"], scale[0], 0.25), scale[0], s["font-size"])
        self.truthy(f"{name}.line-height", px_close(s["line-height"], scale[1], 0.25), scale[1], s["line-height"])

    def missing(self, label, counterpart):
        self.deviations.append(f"{label}: not rendered on the live page — {counterpart}")

    def note(self, text):
        self.notes.append(text)

    def test_data(self, label, expected, actual):
        """Seeded-content difference: reported (note + failure message if the
        test fails for other reasons) but never a failure on its own."""
        if expected != actual:
            self.notes.append(f"TEST DATA — {label}: expected {expected!r}, got {actual!r}")

    def assert_clean(self):
        if self.notes:
            allure.attach("\n".join(self.notes), "notes / unmeasured", allure.attachment_type.TEXT)
        extra = [n for n in self.notes if n.startswith("TEST DATA")]
        assert not self.deviations, (f"{self.title}: {len(self.deviations)} deviation(s):\n  - " + "\n  - ".join(self.deviations)
                                     + ("\n  (reported, not failing) " + "; ".join(extra) if extra else ""))


def _check_contrast(check: _Check, faq: FaqPage, threshold_normal=AA_NORMAL, threshold_large=AA_LARGE):
    for c in faq.visible_text_contrasts():
        large = c["fontSize"] >= 24 or (c["fontSize"] >= 18.66 and c["fontWeight"] >= 700)
        need = threshold_large if large else threshold_normal
        check.truthy(f"contrast {c['el']} '{c['text']}'", c["ratio"] >= need, f">= {need}:1",
                     f"{c['ratio']}:1 ({c['color']} on {c['background']})")


def _is_dark(faq: FaqPage, background: str) -> bool:
    colours = re.findall(r"rgba?\([^)]*\)", background) or [background]
    return all(faq.relative_luminance(c) < 0.2 for c in colours)


def _overlap(a, b) -> bool:
    if not a or not b:
        return False
    return (a["x"] < b["x"] + b["width"] - 1 and b["x"] < a["x"] + a["width"] - 1
            and a["y"] < b["y"] + b["height"] - 1 and b["y"] < a["y"] + a["height"] - 1)


def _no_overflow(check: _Check, faq: FaqPage):
    o = faq.horizontal_overflow_px()
    check.truthy("no horizontal scroll", o <= 0, "0px", f"{o}px {faq.overflowing_elements()}")
    check.equals("no clipped text", faq.clipped_text_elements(), [])


def _no_block_overlap(check: _Check, faq: FaqPage):
    blocks = {"hero": faq.HERO, "search": faq.SEARCH, "categories": faq.CHIPS, "accordion": faq.LIST,
              "pagination": faq.PAGINATION}
    boxes = {n: faq.box(l) for n, l in blocks.items()}
    names = list(boxes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            check.truthy(f"{names[i]}/{names[j]} overlap", not _overlap(boxes[names[i]], boxes[names[j]]),
                         "no overlap", f"{boxes[names[i]]} vs {boxes[names[j]]}")


def _meta(tc: str, title: str, severity, story: str):
    def deco(fn):
        for d in (allure.label("testcase", tc), allure.label("pbi", PBI), allure.title(title),
                  allure.severity(severity), allure.story(story), allure.feature("FAQ Knowledge Base"),
                  allure.epic("Knowledge Base")):
            fn = d(fn)
        return fn
    return deco


N, C = allure.severity_level.NORMAL, allure.severity_level.CRITICAL


# ---------------------------------------------------------------------------
# Figma token cases (141645-141654)
# ---------------------------------------------------------------------------
@_meta("141645", "FAQ hero heading renders with the Figma-verified exact style and text", N, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141645
@anonymous
def test_faq_hero_heading_tokens(page):
    """Azure TC 141645 | PBI 131052 — hero heading 'How can we help?' in display-sm/Bold, white."""
    check = _Check("TC 141645")
    faq = FaqPage(page).open_faq()
    hero_bg = faq.effective_background(faq.HERO)
    check.truthy("hero on a dark background", _is_dark(faq, hero_bg), "dark (every colour stop luminance < 0.2)", hero_bg)
    s = faq.styles(faq.HERO_TITLE, TYPO)
    check.equals("hero heading text", faq.texts(faq.HERO_TITLE)[0], "How can we help?")
    check.type_scale("hero heading", s, "Bold", DISPLAY_SM)
    check.color("hero heading color (fill_658ab2fa, white)", s["color"], "#FFFFFF")
    check.assert_clean()


@_meta("141646", "FAQ hero supporting text renders with the Figma-verified exact style, width and copy", N, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141646
@anonymous
def test_faq_hero_subtext_tokens(page):
    """Azure TC 141646 | PBI 131052 — subtext copy, Text-md/Regular, 648px, rgba(255,255,255,0.7)."""
    check = _Check("TC 141646")
    faq = FaqPage(page).open_faq()
    s = faq.styles(faq.HERO_SUBTITLE, TYPO)
    title, sub = faq.box(faq.HERO_TITLE), faq.box(faq.HERO_SUBTITLE)
    check.truthy("subtext directly below the heading", sub["y"] >= title["y"] + title["height"] - 1, "below", f"{title} / {sub}")
    check.equals("subtext copy", faq.texts(faq.HERO_SUBTITLE)[0],
                 "Find services, events, publications, and information across the website.")
    check.type_scale("subtext", s, "Regular", TEXT_MD)
    check.truthy("subtext width", abs(sub["width"] - 648) <= 1, "648px", f"{sub['width']}px")
    check.equals("subtext color", s["color"], "rgba(255, 255, 255, 0.7)")
    check.assert_clean()


@_meta("141647", "Hero search input pill and Search button render with the Figma-verified exact styling", C, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141647
@anonymous
def test_faq_search_pill_and_button_tokens(page):
    """Azure TC 141647 | PBI 131052 — pill radius 9999px, 1px #EDEDED border, 0 20px 40px shadow; #911731
    'Search' button in Text-md/Semibold white."""
    check = _Check("TC 141647")
    faq = FaqPage(page).open_faq()
    s = faq.styles(faq.SEARCH, ("border-top-left-radius", "border-top-width", "border-top-style", "border-top-color", "box-shadow"))
    check.equals("search pill border-radius", s["border-top-left-radius"], "9999px")
    check.equals("search pill border", f"{s['border-top-width']} {s['border-top-style']}", "1px solid")
    check.color("search pill border color", s["border-top-color"], "#EDEDED")
    check.equals("search pill box-shadow", s["box-shadow"], "rgba(29, 29, 27, 0.1) 0px 20px 40px 0px")
    if faq.role_count("button", "Search"):
        b = faq.role_style("button", TYPO + ("background-color",), name="Search")
        check.color("Search button fill (fill_11bddc20)", b["background-color"], "#911731")
        check.equals("Search button radius (Figma 9999px)",
                     faq.role_style("button", ("border-top-left-radius",), name="Search")["border-top-left-radius"], "9999px")
        check.color("Search button label color", b["color"], "#FFFFFF")
        check.type_scale("Search button label", b, "Semibold", TEXT_MD)
    else:
        check.missing("'Search' button", "the search pill has only an input (placeholder "
                      f"'{faq.placeholder(faq.SEARCH_INPUT)}') and a clear (×) button")
    check.assert_clean()


@_meta("141648", "Breadcrumb renders 'Home > FAQs' with the Figma-verified exact style", N, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141648
@anonymous
def test_faq_breadcrumb_tokens(page):
    """Azure TC 141648 | PBI 131052 — 'Home' link, chevron-right icon, current 'FAQs' crumb, Text-sm/Regular."""
    check = _Check("TC 141648")
    faq = FaqPage(page).open_faq()
    check.equals("Home crumb text", faq.texts(faq.CRUMB_HOME), ["Home"])
    check.equals("Home crumb is a link", faq.tag_of(faq.CRUMB_HOME), "a")
    check.equals("current crumb text", faq.texts(faq.CRUMB_CURRENT), ["FAQs"])
    check.truthy("current crumb is non-clickable", faq.tag_of(faq.CRUMB_CURRENT) not in ("a", "button"),
                 "non-link", faq.tag_of(faq.CRUMB_CURRENT))
    if faq.count(faq.CRUMB_SEP_ICON) == 0:
        check.missing("chevron-right separator icon", f"separator is the text {faq.texts(faq.CRUMB_SEP)}")
    for name, loc in (("Home crumb", faq.CRUMB_HOME), ("FAQs crumb", faq.CRUMB_CURRENT)):
        s = faq.styles(loc, TYPO)
        check.type_scale(name, s, "Regular", TEXT_SM)
        check.color(f"{name} color (fill_658ab2fa)", s["color"], "#FFFFFF")
    check.assert_clean()


@_meta("141649", "'Browse by topic' eyebrow renders with the Figma-verified exact color and text", N, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141649
@anonymous
def test_faq_eyebrow_tokens(page):
    """Azure TC 141649 | PBI 131052 — eyebrow 'Browse by topic', Text-sm/Regular, #911731."""
    check = _Check("TC 141649")
    faq = FaqPage(page).open_faq()
    faq.scroll_to(faq.LIST)
    if faq.text_count("Browse by topic"):
        s = faq.text_style("Browse by topic", TYPO)
        check.type_scale("eyebrow", s, "Regular", TEXT_SM)
        check.color("eyebrow color", s["color"], "#911731")
    else:
        check.missing("'Browse by topic' eyebrow", "no eyebrow above the list; content section starts with the search pill")
    check.assert_clean()


@_meta("141650", "'Frequently asked questions' H2 renders with the Figma-verified exact style", N, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141650
@anonymous
def test_faq_h2_tokens(page):
    """Azure TC 141650 | PBI 131052 — H2 'Frequently asked questions', display-sm/Bold, #1D1D1B."""
    check = _Check("TC 141650")
    faq = FaqPage(page).open_faq()
    if faq.role_count("heading", level=2):
        check.equals("H2 text", faq.role_texts("heading", level=2)[0], "Frequently asked questions")
        s = faq.role_style("heading", TYPO, level=2)
        check.type_scale("H2", s, "Bold", DISPLAY_SM)
        check.color("H2 color", s["color"], "#1D1D1B")
    else:
        check.missing("H2 'Frequently asked questions'", "the only heading in the FAQ section is the hero h1 "
                      f"{faq.texts(faq.HERO_TITLE)}")
    check.assert_clean()


@_meta("141651", "'Select Category' dropdown renders with the Figma-verified exact styling", N, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141651
@anonymous
def test_faq_category_dropdown_tokens(page):
    """Azure TC 141651 | PBI 131052 — 'Select Category' + chevron-down, 8px radius, 1px #EDEDED border."""
    check = _Check("TC 141651")
    faq = FaqPage(page).open_faq()
    if faq.count(faq.DROPDOWN):
        s = faq.styles(faq.DROPDOWN, ("border-top-left-radius", "border-top-width", "border-top-style", "border-top-color"))
        check.equals("dropdown label", faq.texts(faq.DROPDOWN)[0], "Select Category")
        check.equals("dropdown border-radius", s["border-top-left-radius"], "8px")
        check.equals("dropdown border", f"{s['border-top-width']} {s['border-top-style']}", "1px solid")
        check.color("dropdown border color", s["border-top-color"], "#EDEDED")
        p = faq.styles(faq.DROPDOWN, TYPO)
        check.type_scale("dropdown placeholder", p, "Regular", TEXT_SM)
        check.color("dropdown placeholder color (fill_d9f491bf)", p["color"], "#A8A8A7")
    else:
        check.missing("'Select Category' dropdown", f"categories render as a chip tablist {faq.texts(faq.CHIP)}")
    check.assert_clean()


@_meta("141652", "Results count text renders with the Figma-verified exact pattern and color", N, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141652
@anonymous
def test_faq_results_count_tokens(page):
    """Azure TC 141652 | PBI 131052 — 'Showing 1–6 of 12 questions', Text-sm/Regular, #911731.
    Precondition: 12 Published FAQ entries seeded (the count/total is data-dependent)."""
    check = _Check("TC 141652")
    faq = FaqPage(page).open_faq()
    faq.scroll_to(faq.PAGE_INFO)
    list_box, info = faq.box(faq.LIST), faq.box(faq.PAGE_INFO)
    check.truthy("results count above the accordion list", info["y"] + info["height"] <= list_box["y"] + 1,
                 "above the list", f"count y={info['y']}, list y={list_box['y']}")
    text = faq.texts(faq.PAGE_INFO)[0]
    m = re.fullmatch(r"Showing (\d+)\u2013(\d+) of (\d+)(?: questions)?", text)
    # Product: the pattern (page size 6 -> "1–6", trailing "questions").
    check.truthy("results count pattern 'Showing 1–6 of N questions'",
                 bool(re.fullmatch(r"Showing 1\u20136 of \d+ questions", text)), "Showing 1–6 of N questions", text)
    # Test data: the total depends on how many entries are seeded (case assumes 12).
    check.test_data("results count total (seeded entries)", "12", m.group(3) if m else text)
    s = faq.styles(faq.PAGE_INFO, TYPO + ("text-align",))
    check.type_scale("results count", s, "Regular", TEXT_SM)
    check.color("results count color (fill_11bddc20)", s["color"], "#911731")
    check.equals("results count alignment (Figma RIGHT)", faq.resolved_text_align(faq.PAGE_INFO), "right")
    check.assert_clean()


@_meta("141653", "FAQ accordion item question renders with the Figma-verified style and expand icon placement", N, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141653
@anonymous
def test_faq_accordion_question_tokens(page):
    """Azure TC 141653 | PBI 131052 — first question 'What is Made in Qatar Expo?' (seeded entry),
    Text-md/Bold #343432 (fill_a6c48a10), expand icon right-aligned, items collapsed by default.
    The question text itself is seeded content — reported as TEST DATA, not a failure."""
    check = _Check("TC 141653")
    faq = FaqPage(page).open_faq()
    faq.scroll_to(faq.LIST)
    open_items = faq.expanded_question_count()
    check.truthy("items collapsed by default", open_items == 0, "all collapsed",
                 f"{open_items} expanded of {faq.count(faq.QUESTION)}")
    check.test_data("first question text (seeded entry)", "What is Made in Qatar Expo?", faq.texts(faq.QUESTION_LABEL)[0])
    qs = faq.styles(faq.QUESTION_LABEL, TYPO)
    check.type_scale("question", qs, "Bold", TEXT_MD)
    check.color("question color (fill_a6c48a10)", qs["color"], "#343432")
    q, icon = faq.box(faq.QUESTION), faq.box(faq.QUESTION_ICON)
    check.truthy("expand icon right-aligned", icon["x"] > q["x"] + q["width"] / 2, "right half of the row",
                 f"icon x={icon['x']}, row {q['x']}-{q['x'] + q['width']}")
    check.assert_clean()


@_meta("141654", "'Load More' button renders with the Figma-verified pill styling and icon", N, "Figma tokens")
@pytest.mark.ui
@pytest.mark.tc_141654
@anonymous
def test_faq_load_more_tokens(page):
    """Azure TC 141654 | PBI 131052 — 'Load More' pill (9999px, 1px #DEDEDD), left refresh icon, Text-md/Semibold #4A4A49."""
    check = _Check("TC 141654")
    faq = FaqPage(page).open_faq()
    faq.scroll_to(faq.PAGINATION)
    if faq.role_count("button", "Load More"):
        s = faq.role_style("button", TYPO + ("border-top-left-radius", "border-top-width", "border-top-style",
                                              "border-top-color"), name="Load More")
        check.equals("Load More radius", s["border-top-left-radius"], "9999px")
        check.equals("Load More border", f"{s['border-top-width']} {s['border-top-style']}", "1px solid")
        check.color("Load More border color", s["border-top-color"], "#DEDEDD")
        pad = faq.role_style("button", ("padding-top", "padding-right", "padding-bottom", "padding-left"), name="Load More")
        check.equals("Load More padding (Figma 12px 18px)", tuple(pad.values()), ("12px", "18px", "12px", "18px"))
        check.type_scale("Load More label", s, "Semibold", TEXT_MD)
        check.color("Load More label color", s["color"], "#4A4A49")
    else:
        check.missing("'Load More' button", f"numbered pagination {faq.texts(faq.PAGE_BUTTON)} "
                      f"with '{faq.texts(faq.PAGE_INFO)[0]}'")
    check.assert_clean()


# ---------------------------------------------------------------------------
# Bilingual (141655 / 141656)
# ---------------------------------------------------------------------------
def _section_locators(faq: FaqPage) -> dict:
    return {"hero heading": faq.HERO_TITLE, "hero text": faq.HERO_SUBTITLE, "breadcrumb": faq.CRUMB_CURRENT,
            "category": faq.CHIP, "question": faq.QUESTION_LABEL, "results count": faq.PAGE_INFO}


def _figma_sections_missing(check: _Check, faq: FaqPage):
    if not faq.text_count("Browse by topic") and not faq.text_count("تصفح حسب الموضوع"):
        check.missing("'Browse by topic' section", "see TC 141649")
    if not faq.count(faq.DROPDOWN):
        check.missing("category dropdown", "chip tablist instead (see TC 141651)")
    if not faq.role_count("button", "Load More") and not faq.role_count("button", "تحميل المزيد"):
        check.missing("Load More", "numbered pagination instead (see TC 141654)")


@_meta("141655", "FAQ Knowledge Base page renders fully in English (LTR)", C, "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.tc_141655
@anonymous
def test_faq_english_ltr(page):
    """Azure TC 141655 | PBI 131052 — dir=ltr, every section English, left-aligned, Cairo."""
    check = _Check("TC 141655")
    faq = FaqPage(page).open_faq()
    check.equals("html dir", faq.document_dir(), "ltr")
    for name, loc in _section_locators(faq).items():
        for i, text in enumerate(faq.texts(loc)):
            check.truthy(f"{name} {i + 1} English", text and not ARABIC.search(text), "English copy", text)
            check.equals(f"{name} {i + 1} alignment", faq.resolved_text_align(loc, i), "left" if loc != faq.CHIP else "center")
            fam = faq.styles(loc, ("font-family",), i)["font-family"]
            check.truthy(f"{name} {i + 1} Cairo", font_family_contains(fam), "Cairo", fam)
    _figma_sections_missing(check, faq)
    check.assert_clean()


@_meta("141656", "FAQ Knowledge Base page renders fully mirrored in Arabic (RTL)", C, "Bilingual")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.tc_141656
@anonymous
def test_faq_arabic_rtl(page):
    """Azure TC 141656 | PBI 131052 — dir=rtl, Arabic copy right-aligned in Cairo, breadcrumb/dropdown
    chevrons mirrored, accordion icon on the left, no clipped text. (Category chips are centred
    buttons — alignment checked as 'center', the same component styling as EN.)"""
    check = _Check("TC 141656")
    faq = FaqPage(page).open_faq(locale="ar")
    check.equals("html dir", faq.document_dir(), "rtl")
    for name, loc in _section_locators(faq).items():
        for i, text in enumerate(faq.texts(loc)):
            check.truthy(f"{name} {i + 1} Arabic", bool(ARABIC.search(text or "")), "Arabic copy", text)
            check.equals(f"{name} {i + 1} alignment", faq.resolved_text_align(loc, i), "right" if loc != faq.CHIP else "center")
            fam = faq.styles(loc, ("font-family",), i)["font-family"]
            check.truthy(f"{name} {i + 1} Cairo", font_family_contains(fam), "Cairo", fam)
    check.truthy("search placeholder Arabic", bool(ARABIC.search(faq.placeholder(faq.SEARCH_INPUT))), "Arabic",
                 faq.placeholder(faq.SEARCH_INPUT))
    if faq.count(faq.CRUMB_SEP_ICON) == 0:
        check.missing("mirrored breadcrumb chevron", f"separator is the text {faq.texts(faq.CRUMB_SEP)} (see TC 141648)")
    q, icon = faq.box(faq.QUESTION), faq.box(faq.QUESTION_ICON)
    check.truthy("accordion expand icon on the left (mirrored)", icon["x"] + icon["width"] < q["x"] + q["width"] / 2,
                 "left half of the row", f"icon x={icon['x']}, row {q['x']}-{q['x'] + q['width']}")
    check.equals("no clipped Arabic text", faq.clipped_text_elements(), [])
    _figma_sections_missing(check, faq)
    check.assert_clean()


# ---------------------------------------------------------------------------
# Theme (141657 / 141658) and contrast (141659 / 141660)
# ---------------------------------------------------------------------------
_SURFACES = (("search pill", "SEARCH"), ("accordion question row", "QUESTION"), ("category chip", "CHIP"),
             ("pagination button", "PAGE_BUTTON"))


@_meta("141657", "FAQ Knowledge Base page renders correctly under Light theme", N, "Theme")
@pytest.mark.compatibility
@pytest.mark.tc_141657
@anonymous
def test_faq_light_theme(page):
    """Azure TC 141657 | PBI 131052 — light theme (site default): every text node in hero and content
    meets WCAG AA; page background light (no inverted regions)."""
    check = _Check("TC 141657")
    faq = FaqPage(page).open_faq()
    check.truthy("light theme active", faq.theme() in (None, "light"), "light", faq.theme())
    body = faq.styles(faq.PAGE_BODY, ("background-color",))["background-color"]
    check.truthy("page background light", faq.relative_luminance(body) > 0.8, "light", body)
    _check_contrast(check, faq)
    check.assert_clean()


@_meta("141658", "FAQ Knowledge Base page renders correctly under Dark theme", N, "Theme")
@pytest.mark.compatibility
@pytest.mark.tc_141658
@anonymous
def test_faq_dark_theme(page):
    """Azure TC 141658 | PBI 131052 — dark theme via the Accessibility tools widget (transitions
    awaited): every text node meets WCAG AA against its real background, and the FAQ surfaces
    (search pill, question rows, category chips, pagination buttons) adopt dark surfaces — a white
    light-mode surface left on the dark page is recorded as an unstyled region."""
    check = _Check("TC 141658")
    faq = FaqPage(page).open_faq()
    faq.enable_dark_mode()
    check.equals("dark theme active", faq.theme(), "dark")
    body = faq.styles(faq.PAGE_BODY, ("background-color",))["background-color"]
    check.truthy("page background dark", faq.relative_luminance(body) < 0.2, "dark", body)
    _check_contrast(check, faq)
    for name, attr in _SURFACES:
        loc = getattr(faq, attr)
        for i, s in enumerate(faq.styles_all(loc, ("background-color",))):
            bg = s["background-color"]
            if bg == "rgba(0, 0, 0, 0)" or "138, 21, 56" in bg:  # transparent / active maroon chip or page button
                continue
            check.truthy(f"{name} {i + 1} dark surface (no unstyled light region)",
                         faq.relative_luminance(bg) < 0.2, "dark surface", bg)
    check.assert_clean()


@_meta("141659", "FAQ Knowledge Base page renders correctly under Normal contrast", C, "Contrast")
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.tc_141659
@anonymous
def test_faq_normal_contrast(page):
    """Azure TC 141659 | PBI 131052 — default (normal) contrast: the High contrast switch is off,
    <html> carries no qc-a11y-contrast class, and the default palette renders (white page, the
    maroon hero gradient, #1D1D1B question text)."""
    check = _Check("TC 141659")
    faq = FaqPage(page).open_faq()
    state = faq.high_contrast_state()
    check.equals("High contrast switch off", state["switch_checked"], False)
    check.equals("high-contrast class absent", state["active"], False)
    check.color("page background (default palette)", faq.styles(faq.PAGE_BODY, ("background-color",))["background-color"], "#FFFFFF")
    check.truthy("hero keeps its maroon gradient", "gradient" in faq.effective_background(faq.HERO), "gradient",
                 faq.effective_background(faq.HERO))
    check.color("question text (default palette)", faq.styles(faq.QUESTION_LABEL, ("color",))["color"], "#1D1D1B")
    check.assert_clean()


@_meta("141660", "FAQ Knowledge Base page renders correctly under High contrast", C, "Contrast")
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.tc_141660
@anonymous
def test_faq_high_contrast(page):
    """Azure TC 141660 | PBI 131052 — High contrast via the Accessibility tools switch: switch checked,
    <html class="qc-a11y-contrast"> applied, the palette differs from normal, and no low-contrast text
    pairing remains (every text node >= WCAG AA)."""
    check = _Check("TC 141660")
    faq = FaqPage(page).open_faq()
    normal_body = faq.styles(faq.PAGE_BODY, ("background-color", "color"))
    faq.enable_high_contrast()
    state = faq.high_contrast_state()
    check.equals("High contrast switch on", state["switch_checked"], True)
    check.equals("high-contrast class applied", state["active"], True)
    hc_body = faq.styles(faq.PAGE_BODY, ("background-color", "color"))
    check.truthy("high-contrast palette applied", hc_body != normal_body, "palette differs from normal", hc_body)
    _check_contrast(check, faq)
    check.assert_clean()


# ---------------------------------------------------------------------------
# Viewports (141661 / 141662 / 141663)
# ---------------------------------------------------------------------------
@_meta("141661", "FAQ Knowledge Base page renders correctly at Desktop viewport 1920x1080", N, "Responsive layout")
@pytest.mark.compatibility
@pytest.mark.tc_141661
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_faq_desktop_1920(page):
    """Azure TC 141661 | PBI 131052 — no overflow/overlap; search, categories, accordion and
    pagination share one grid column (same left edge and width, +/-2px)."""
    check = _Check("TC 141661")
    faq = FaqPage(page).open_faq()
    _no_overflow(check, faq)
    _no_block_overlap(check, faq)
    search = faq.box(faq.SEARCH)
    for name, loc in (("categories", faq.CHIPS), ("accordion", faq.LIST), ("pagination", faq.PAGINATION)):
        b = faq.box(loc)
        check.truthy(f"{name} aligned with the search bar", abs(b["x"] - search["x"]) <= 2
                     and abs(b["width"] - search["width"]) <= 2, f"x={search['x']}, w={search['width']}",
                     f"x={b['x']}, w={b['width']}")
    if not faq.count(faq.DROPDOWN):
        check.missing("category dropdown", "chip tablist instead (see TC 141651)")
    if not faq.role_count("button", "Load More"):
        check.missing("Load More", "numbered pagination instead (see TC 141654)")
    check.assert_clean()


@_meta("141662", "FAQ Knowledge Base page renders correctly at Tablet viewport 768x1024", N, "Responsive layout")
@pytest.mark.compatibility
@pytest.mark.tc_141662
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_faq_tablet_768(page):
    """Azure TC 141662 | PBI 131052 — reflow without overlap/clipping; Search button, category
    control and accordion icons meet 44x44 (the accordion icon's target is its question button)."""
    check = _Check("TC 141662")
    faq = FaqPage(page).open_faq()
    _no_overflow(check, faq)
    _no_block_overlap(check, faq)
    if faq.role_count("button", "Search"):
        b = faq.role_box("button", "Search")
        check.truthy("Search button 44x44", b["width"] >= TAP and b["height"] >= TAP, ">= 44x44", b)
    else:
        check.missing("Search button (touch target)", "search pill has no Search button (see TC 141647)")
    if faq.count(faq.DROPDOWN):
        b = faq.box(faq.DROPDOWN)
        check.truthy("category dropdown 44x44", b["width"] >= TAP and b["height"] >= TAP, ">= 44x44", b)
    else:
        for i, b in enumerate(faq.boxes(faq.CHIP)):
            check.truthy(f"category chip {i + 1} (live category control) 44x44", b["width"] >= TAP and b["height"] >= TAP,
                         ">= 44x44", f"{b['width']}x{b['height']}")
    for i in range(faq.count(faq.QUESTION_ICON)):
        t = faq.clickable_box(faq.QUESTION_ICON, i)
        check.truthy(f"accordion icon {i + 1} target 44x44", t["width"] >= TAP and t["height"] >= TAP, ">= 44x44",
                     f"{t['tag']} {t['width']}x{t['height']}")
    check.assert_clean()


@_meta("141663", "FAQ Knowledge Base page renders correctly at Mobile viewport 375x667", N, "Responsive layout")
@pytest.mark.compatibility
@pytest.mark.tc_141663
@pytest.mark.parametrize("page", [{"viewport": (375, 667), "auth": False}], indirect=True)
def test_faq_mobile_375(page):
    """Azure TC 141663 | PBI 131052 — stacked, no horizontal scroll or clipping; search input,
    category dropdown and Load More full-width (= the content column) and tappable (>= 44px)."""
    check = _Check("TC 141663")
    faq = FaqPage(page).open_faq()
    _no_overflow(check, faq)
    _no_block_overlap(check, faq)
    blocks = [faq.box(l) for l in (faq.HERO, faq.SEARCH, faq.CHIPS, faq.LIST, faq.PAGINATION)]
    check.truthy("sections stack vertically", all(blocks[i]["y"] + blocks[i]["height"] <= blocks[i + 1]["y"] + 1
                                                  for i in range(len(blocks) - 1)), "each below the previous",
                 [round(b["y"]) for b in blocks])
    column = faq.box(faq.LIST)
    search = faq.box(faq.SEARCH)
    check.truthy("search input full-width", abs(search["width"] - column["width"]) <= 2, f"{column['width']}px",
                 f"{search['width']}px")
    check.truthy("search tappable", search["height"] >= TAP, ">= 44px", search["height"])
    if faq.count(faq.DROPDOWN):
        b = faq.box(faq.DROPDOWN)
        check.truthy("dropdown full-width & tappable", abs(b["width"] - column["width"]) <= 2 and b["height"] >= TAP,
                     f"{column['width']}px x >=44", b)
    else:
        check.missing("category dropdown (full-width)", f"chip tablist, chips {[round(b['width']) for b in faq.boxes(faq.CHIP)]}px wide")
    if faq.role_count("button", "Load More"):
        b = faq.role_box("button", "Load More")
        check.truthy("Load More full-width & tappable", abs(b["width"] - column["width"]) <= 2 and b["height"] >= TAP,
                     f"{column['width']}px x >=44", b)
    else:
        check.missing("Load More (full-width)", "numbered pagination instead (see TC 141654)")
    check.assert_clean()

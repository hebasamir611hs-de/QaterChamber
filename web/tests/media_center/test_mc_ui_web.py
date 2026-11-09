"""
web/tests/media_center/test_mc_ui_web.py — PBI 130709 (Media Center Home Page),
FRONTEND (Web) batch FE-UI: Figma design tokens, Light/Dark, EN/AR RTL,
responsive desktop/tablet/mobile, High-Contrast and keyboard navigation.

All tests run in a FRESH, LOGGED-OUT context (`"auth": False`) against the
public hub (`/web/qatar-chamber/media-center`, AR `/ar/web/...`). Read-only:
no CMS record is touched, the subscribe form is never submitted.

Design values come from the approved Figma frames (scratchpad agentC_figma.json,
figma_verdict.verified=true) as written in each case. Tolerances (bug-rules
Rule 1): text/colour/order exact; layout +/-2px; images +/-5px. Each test
collects EVERY mismatch of its case before asserting, so one run reports the
full design delta of the case instead of stopping at the first one.
"""

import re

import allure
import pytest

from core.web.design_tokens import font_family_contains, hex_to_rgb
from web.pages.media_center.mc_ui_page import MediaCenterUiPage, _contrast

EPIC = "Media Center Home Page (PBI 130709)"
FEATURE = "FE-UI — design tokens, themes, RTL, responsive, keyboard"

DESKTOP = {"auth": False, "viewport": (1920, 1080)}
TABLET = {"auth": False, "viewport": (768, 1024)}
MOBILE_375 = {"auth": False, "viewport": (375, 812)}
MOBILE_390 = {"auth": False, "viewport": (390, 844)}

CONTENT_X = 300      # (1920 - 1320) / 2
CONTENT_W = 1320
P = MediaCenterUiPage

WIDGET_LABELS_EN = ["Articles", "Photo Albums", "Videos", "Podcast", "Publications"]
WIDGET_UNITS_EN = ["stories", "albums", "videos", "episodes", "Pubs"]
WIDGET_LABELS_AR = ["مقالات", "ألبومات صور", "فيديوهات", "بودكاست", "المنشورات"]
QA_TITLES_EN = ["Photo Gallery", "Video Gallery", "Publications", "Al-Moltqa Magazine",
                "Members Directory", "Request to the Media Dept"]
QA_DESCRIPTIONS_EN = [
    "Browse event albums and institutional moments.",
    "Watch interviews, events, and Chamber updates.",
    "Access reports, studies, and official resources.",
    "Explore the Chamber’s business magazine archive.",
    "Connect with Qatar’s business community.",
    "Press kits, interviews, coverage, and inquiries.",
]
EN_DATE = re.compile(r"^[A-Z][a-z]{2} \d{1,2}, \d{4}$")
VIEWS = re.compile(r"^[\d,]+( views?)?$", re.I)
READ_TIME = re.compile(r"^\d+ min read$", re.I)
DURATION = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
PHOTO_BADGE = re.compile(r"^\d+ photos?$")
INDICATOR = re.compile(r"^(\d+)\s*/\s*(\d+)$")


# ── comparison helpers (pure; the Page Object only reads) ────────────────
def _num(v):
    try:
        return float(str(v).replace("px", "").strip())
    except ValueError:
        return None


def _rgba(css: str):
    """'#911731' | 'rgb(..)' | 'rgba(..)' -> (r, g, b, a)."""
    css = css.strip()
    if css.startswith("#"):
        css = hex_to_rgb(css)
    nums = [float(x) for x in re.findall(r"[\d.]+", css)]
    if len(nums) < 3:
        return None
    return (int(nums[0]), int(nums[1]), int(nums[2]), round(nums[3] if len(nums) > 3 else 1.0, 2))


def _color_eq(actual: str, expected: str) -> bool:
    a, e = _rgba(actual or ""), _rgba(expected)
    return a is not None and a[:3] == e[:3] and abs(a[3] - e[3]) <= 0.01


def _gradient(css: str):
    """'linear-gradient(89.6deg, rgba(..) 15.74%, rgba(..) 84.3%)' -> (angle, [(rgba, pct)])."""
    m = re.search(r"linear-gradient\(([-\d.]+)deg,(.*)\)\s*$", css or "")
    if not m:
        return None, []
    stops = re.findall(r"(rgba?\([^)]*\))\s*([\d.]+)%", m.group(2))
    return float(m.group(1)), [(_rgba(c), float(p)) for c, p in stops]


def _right_aligned(st: dict) -> bool:
    ta, d = st["textAlign"], st["direction"]
    return ta in ("right", "-webkit-right") or (ta in ("start", "-webkit-auto") and d == "rtl") \
        or (ta == "end" and d == "ltr")


def _left_aligned(st: dict) -> bool:
    ta, d = st["textAlign"], st["direction"]
    return ta in ("left", "-webkit-left") or (ta in ("start", "-webkit-auto") and d == "ltr") \
        or (ta == "end" and d == "rtl")


def _is_arabic(s: str) -> bool:
    return bool(s) and any("؀" <= c <= "ۿ" for c in s) and not re.search(r"[A-Za-z]", s)


def _norm_quotes(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'")


def _overlap(a: dict, b: dict) -> bool:
    return a["x"] < b["right"] - 0.5 and b["x"] < a["right"] - 0.5 and a["y"] < b["bottom"] - 0.5 \
        and b["y"] < a["bottom"] - 0.5


class Checks:
    """Collects every mismatch of one case, then asserts once."""

    def __init__(self, case: str):
        self.case = case
        self.fails = []

    def ok(self, step, label, cond, actual, expected):
        if not cond:
            self.fails.append(f"[step {step}] {label}: expected {expected}, got {actual}")
        return cond

    def eq(self, step, label, actual, expected):
        return self.ok(step, label, actual == expected, actual, expected)

    def px(self, step, label, actual, expected, tol=2.0):
        a = _num(actual)
        return self.ok(step, label, a is not None and abs(a - expected) <= tol, actual,
                       f"{expected}px (±{tol})")

    def color(self, step, label, actual, expected):
        return self.ok(step, label, _color_eq(actual, expected), actual, expected)

    def typo(self, step, label, st, size, lh=None, weight=None, color=None, family="Cairo"):
        self.px(step, f"{label} font-size", st["fontSize"], size, 0.5)
        if lh is not None:
            self.px(step, f"{label} line-height", st["lineHeight"], lh, 1)
        if weight is not None:
            self.eq(step, f"{label} font-weight", str(st["fontWeight"]), str(weight))
        if color is not None:
            self.color(step, f"{label} color", st["color"], color)
        if family:
            self.ok(step, f"{label} font-family", font_family_contains(st["fontFamily"], family),
                    st["fontFamily"], family)

    def pad(self, step, label, st, t, r, b, l, tol=1):
        got = [st["paddingTop"], st["paddingRight"], st["paddingBottom"], st["paddingLeft"]]
        exp = [t, r, b, l]
        self.ok(step, f"{label} padding", all(abs(_num(g) - e) <= tol for g, e in zip(got, exp)),
                " ".join(got), " ".join(f"{e}px" for e in exp))

    def size(self, step, label, st, w=None, h=None, tol=2.0):
        if w is not None:
            self.px(step, f"{label} width", st["box"]["w"], w, tol)
        if h is not None:
            self.px(step, f"{label} height", st["box"]["h"], h, tol)

    def radius(self, step, label, st, r):
        return self.px(step, f"{label} border-radius", st["borderTopLeftRadius"], r, 0.5)

    def border(self, step, label, st, width, color):
        self.px(step, f"{label} border width", st["borderTopWidth"], width, 0.1)
        self.color(step, f"{label} border color", st["borderTopColor"], color)

    def gradient(self, step, label, css, angle, stops, angle_tol=1.0, pct_tol=1.0):
        a, got = _gradient(css)
        if not self.ok(step, f"{label} gradient", a is not None and len(got) == len(stops), css,
                       f"linear-gradient({angle}deg, {stops})"):
            return
        self.ok(step, f"{label} gradient angle", abs(a - angle) <= angle_tol, f"{a}deg", f"{angle}deg")
        for i, ((gc, gp), (ec, ep)) in enumerate(zip(got, stops)):
            e = _rgba(ec)
            self.ok(step, f"{label} gradient stop {i + 1} colour", gc[:3] == e[:3] and abs(gc[3] - e[3]) <= 0.01,
                    gc, ec)
            self.ok(step, f"{label} gradient stop {i + 1} position", abs(gp - ep) <= pct_tol, f"{gp}%", f"{ep}%")

    def done(self):
        assert not self.fails, f"{self.case}: {len(self.fails)} mismatch(es)\n" + "\n".join(self.fails)


def _hub(page, locale="en") -> MediaCenterUiPage:
    return MediaCenterUiPage(page).open_hub(locale)


def _pill_cta(c: Checks, step, label, st, bg, border_color, text_color, text):
    c.eq(step, f"{label} text", st["text"], text)
    c.color(step, f"{label} background", st["backgroundColor"], bg)
    c.border(step, label, st, 1, border_color)
    c.radius(step, label, st, 9999)
    c.pad(step, label, st, 10, 16, 10, 16)
    c.typo(step, f"{label} label", st, 16, 24, 600, text_color)


# ═════════════════════════════════════════════════════════════════════════
#  Section-content UI cases (TC-003 .. TC-007)
# ═════════════════════════════════════════════════════════════════════════
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149057 — counts strip: five widgets with icon, name and '<count> <unit>'")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149057
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149057_counts_strip_shows_five_widgets(page):
    """MEDIA-MCHUB-TC-003."""
    hub = _hub(page)
    hub.scroll_into_view(P.COUNTS)
    hub.save_evidence("tc149057_counts_strip")
    c = Checks("TC 149057")
    c.eq(1, "widget count", hub.count(P.COUNT_CARD), 5)
    c.eq(2, "widget names", hub.texts(P.COUNT_LABEL), WIDGET_LABELS_EN)
    for i, icon in enumerate(hub.icon_sources(P.COUNT_ICON)):
        c.ok(3, f"widget {i + 1} icon renders", icon["visible"] and icon["status"] == 200, icon, "visible icon, HTTP 200")
    for i, v in enumerate(hub.texts(P.COUNT_VALUE)):
        c.ok(4, f"widget {i + 1} count line", re.match(r"^\d[\d,]*\s+\S+", v) is not None, v, "'<integer >= 0> <unit>'")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149058 — 'Explore the hub': eyebrow, heading, description and six quick-access cards")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149058
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149058_explore_hub_six_cards(page):
    """MEDIA-MCHUB-TC-004."""
    hub = _hub(page)
    hub.scroll_into_view(P.QA)
    hub.save_evidence("tc149058_explore_hub")
    c = Checks("TC 149058")
    c.ok(1, "eyebrow", bool(hub.texts(P.QA_EYEBROW)[0]), hub.texts(P.QA_EYEBROW), "non-empty eyebrow")
    c.eq(1, "heading", hub.texts(P.QA_HEADING)[0], "Everything in one place")
    c.ok(1, "description line", bool(hub.texts(P.QA_DESCRIPTION)[0]), hub.texts(P.QA_DESCRIPTION), "non-empty")
    c.eq(2, "card count", hub.count(P.QA_CARD), 6)
    c.eq(3, "card titles", hub.texts(P.QA_TITLE), QA_TITLES_EN)
    icons = hub.icon_sources(P.QA_ICON)
    for i in range(hub.count(P.QA_CARD)):
        desc = hub.style(P.QA_CARD_DESCRIPTION, i)
        arrow = hub.style(P.QA_ARROW, i)
        c.ok(4, f"card {i + 1} icon", icons[i]["visible"] and icons[i]["status"] == 200, icons[i], "visible icon")
        c.ok(4, f"card {i + 1} one-line description", bool(desc["text"]) and desc["box"]["h"] <= _num(desc["lineHeight"]) + 1,
             f"{desc['text']!r} h={desc['box']['h']}", "single non-empty line")
        c.ok(4, f"card {i + 1} arrow", arrow["box"]["w"] > 0, arrow["box"], "visible arrow")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149059 — News & press releases: header, lead article and three cards")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149059
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149059_news_section_structure(page):
    """MEDIA-MCHUB-TC-005."""
    hub = _hub(page)
    hub.scroll_into_view(P.NF)
    c = Checks("TC 149059")
    c.eq(1, "eyebrow", hub.texts(P.NF_EYEBROW)[0], "Latest updates")
    c.ok(1, "heading", bool(hub.texts(P.NF_HEADING)[0]), hub.texts(P.NF_HEADING), "non-empty heading")
    c.eq(1, "header CTA", hub.texts(P.NF_CTA_HEAD)[0], "View All Articles")
    lead_img = hub.image_states(P.NF_LEAD_IMAGE)
    c.ok(2, "lead image", lead_img and lead_img[0]["loaded"], lead_img, "loaded image")
    chips = hub.texts(P.NF_LEAD_CHIP)
    c.ok(2, "Featured + category chips", len(chips) == 2 and chips[0] == "Featured" and bool(chips[1]), chips,
         "['Featured', <category>]")
    c.ok(2, "lead title", bool(hub.texts(P.NF_LEAD_TITLE)[0]), hub.texts(P.NF_LEAD_TITLE), "non-empty")
    c.ok(2, "lead excerpt", bool(hub.texts(P.NF_LEAD_EXCERPT)[0]), hub.texts(P.NF_LEAD_EXCERPT), "non-empty")
    meta = hub.texts(P.NF_LEAD_META_ITEM)
    c.ok(2, "lead meta (date, views, read time)",
         len(meta) == 3 and EN_DATE.match(meta[0]) and VIEWS.match(meta[1]) and READ_TIME.match(meta[2]),
         meta, "[date, view count, read time]")
    c.eq(2, "Read More link", hub.texts(P.NF_READ_MORE)[0], "Read More")
    c.eq(3, "visible article cards", hub.visible_count(P.NF_CARD), 3)
    imgs = hub.image_states(P.NF_CARD_IMAGE)
    titles = hub.texts(P.NF_CARD_TITLE)
    for i in range(hub.count(P.NF_CARD)):
        card_meta = hub.texts_within(P.NF_CARD, i, ".qc-mc-nf-meta-item")
        c.ok(3, f"card {i + 1} image", i < len(imgs) and imgs[i]["loaded"], imgs[i] if i < len(imgs) else None, "loaded")
        c.ok(3, f"card {i + 1} title", bool(titles[i]), titles[i], "non-empty")
        c.ok(3, f"card {i + 1} date + views", len(card_meta) == 2 and EN_DATE.match(card_meta[0]) and VIEWS.match(card_meta[1]),
             card_meta, "[date, view count]")
    hub.save_evidence("tc149059_news_section")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149060 — Photo Gallery: header, album cards, carousel controls and indicator")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149060
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149060_photo_section_structure(page):
    """MEDIA-MCHUB-TC-006."""
    hub = _hub(page)
    hub.scroll_into_view(P.PF)
    c = Checks("TC 149060")
    c.eq(1, "eyebrow", hub.texts(P.PF_EYEBROW)[0], "In pictures")
    c.ok(1, "heading", bool(hub.texts(P.PF_HEADING)[0]), hub.texts(P.PF_HEADING), "non-empty")
    c.eq(1, "header CTA", hub.texts(P.PF_CTA_HEAD)[0], "View all albums")
    img = hub.image_states(P.PF_CARD_IMAGE)
    c.ok(2, "first card cover image", img and img[0]["loaded"], img[:1], "loaded")
    badge = hub.texts(P.PF_BADGE_TEXT)[0]
    c.ok(2, "photo-count badge", PHOTO_BADGE.match(badge) is not None, badge, "'<n> photos'")
    c.ok(2, "category chip", bool(hub.texts(P.PF_CATEGORY_CHIP)[0]), hub.texts(P.PF_CATEGORY_CHIP)[:1], "non-empty")
    c.ok(2, "title", bool(hub.texts(P.PF_CARD_TITLE)[0]), hub.texts(P.PF_CARD_TITLE)[:1], "non-empty")
    meta = hub.texts_within(P.PF_CARD, 0, P.PF_CARD_META_ITEM)
    c.ok(2, "meta date + views", len(meta) == 2 and EN_DATE.match(meta[0]) and VIEWS.match(meta[1]), meta,
         "[date, view count]")
    c.ok(3, "Previous control", hub.is_visible(P.PF_PREV), hub.is_visible(P.PF_PREV), True)
    c.ok(3, "Next control", hub.is_visible(P.PF_NEXT), hub.is_visible(P.PF_NEXT), True)
    ind = hub.indicator_text() if hub.is_visible(P.PF_INDICATOR) else None
    c.ok(3, "position indicator", ind is not None and INDICATOR.match(ind) is not None, ind, "'<n> / <total>'")
    hub.save_evidence("tc149060_photo_section")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149061 — Video Gallery: header, CTA and cards with play overlay and duration")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149061
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149061_video_section_structure(page):
    """MEDIA-MCHUB-TC-007."""
    hub = _hub(page)
    hub.scroll_into_view(P.VF)
    c = Checks("TC 149061")
    c.eq(1, "eyebrow", hub.texts(P.VF_EYEBROW)[0], "Watch now")
    c.ok(1, "heading", bool(hub.texts(P.VF_HEADING)[0]), hub.texts(P.VF_HEADING), "non-empty")
    c.eq(1, "header CTA", hub.texts(P.VF_CTA_HEAD)[0], "Watch now")
    imgs = hub.image_states(P.VF_CARD_IMAGE)
    durations = hub.texts(P.VF_DURATION)
    chips = hub.texts(P.VF_CATEGORY_CHIP)
    titles = hub.texts(P.VF_CARD_TITLE)
    n = hub.count(P.VF_CARD)
    c.ok(2, "video cards", n >= 1, n, ">= 1")
    for i in range(n):
        play = hub.style(P.VF_PLAY, i)
        meta = hub.texts_within(P.VF_CARD, i, P.VF_CARD_META_ITEM)
        c.ok(2, f"card {i + 1} thumbnail", imgs[i]["loaded"], imgs[i], "loaded")
        c.ok(2, f"card {i + 1} play overlay", play["box"]["w"] > 0, play["box"], "visible")
        c.ok(2, f"card {i + 1} duration badge", DURATION.match(durations[i]) is not None, durations[i], "'mm:ss'")
        c.ok(2, f"card {i + 1} category chip", bool(chips[i]), chips[i], "non-empty")
        c.ok(2, f"card {i + 1} title", bool(titles[i]), titles[i], "non-empty")
        c.ok(2, f"card {i + 1} published date", len(meta) >= 1 and EN_DATE.match(meta[0]) is not None, meta, "[date]")
    hub.save_evidence("tc149061_video_section")
    c.done()


# ═════════════════════════════════════════════════════════════════════════
#  Language / direction (TC-009, TC-010, TC-012)
# ═════════════════════════════════════════════════════════════════════════
EN_TEXT_LOCATORS = [P.HERO_PAGE_LABEL, P.HERO_CRUMBS, P.HERO_HEADLINE, P.HERO_DESCRIPTION, P.HERO_SEARCH_INPUT,
                    P.HERO_SEARCH_BUTTON_LABEL, P.COUNT_LABEL, P.COUNT_VALUE, P.QA_EYEBROW, P.QA_HEADING,
                    P.QA_DESCRIPTION, P.QA_TITLE, P.QA_CARD_DESCRIPTION, P.NF_EYEBROW, P.NF_HEADING, P.NF_CTA_HEAD,
                    P.NF_READ_MORE, P.NF_LEAD_CHIP, P.PF_EYEBROW, P.PF_HEADING, P.PF_CTA_HEAD, P.PF_BADGE_TEXT,
                    P.PF_CATEGORY_CHIP, P.VF_EYEBROW, P.VF_HEADING, P.VF_CTA_HEAD, P.VF_CATEGORY_CHIP,
                    P.SUB_HEADING, P.SUB_DESCRIPTION, P.SUB_INPUT, P.SUB_BUTTON]


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149063 — hub renders LTR in English with English labels in every section")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149063
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149063_english_ltr(page):
    """MEDIA-MCHUB-TC-009."""
    hub = _hub(page)
    hub.save_evidence("tc149063_en_ltr")
    c = Checks("TC 149063")
    doc = hub.document_state()
    c.ok(1, "<html dir>", doc["dir"] != "rtl", doc["dir"], "ltr")
    c.ok(1, "<html lang>", doc["lang"].lower().startswith("en"), doc["lang"], "en*")
    home, cur = hub.style(P.HERO_CRUMB_HOME), hub.style(P.HERO_CRUMB_CURRENT)
    c.eq(2, "breadcrumb text", [home["text"], cur["text"]], ["Home", "Media Center"])
    c.ok(2, "breadcrumb reads left-to-right", home["box"]["x"] < cur["box"]["x"], (home["box"]["x"], cur["box"]["x"]),
         "Home left of Media Center")
    cards = hub.styles_all(P.COUNT_CARD)
    c.ok(2, "first widget at left edge", cards[0]["box"]["x"] == min(x["box"]["x"] for x in cards),
         [round(x["box"]["x"]) for x in cards], "first widget left-most")
    qa = hub.styles_all(P.QA_CARD)
    c.ok(2, "first card at left edge", qa[0]["box"]["x"] == min(x["box"]["x"] for x in qa) and abs(qa[0]["box"]["x"] - CONTENT_X) <= 2,
         [round(x["box"]["x"]) for x in qa], f"first card left-most at x={CONTENT_X}")
    arabic = hub.arabic_text_found(EN_TEXT_LOCATORS)
    c.ok(3, "no Arabic strings", not arabic, arabic, "[]")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149064 — switching to Arabic renders the whole hub RTL with Arabic content")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.uat
@pytest.mark.pbi_130709
@pytest.mark.tc_149064
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149064_arabic_rtl_via_switcher(page):
    """MEDIA-MCHUB-TC-010."""
    hub = _hub(page, "en")
    hub.switch_language_via_header()
    hub.save_evidence("tc149064_ar_rtl")
    c = Checks("TC 149064")
    doc = hub.document_state()
    c.ok(1, "URL after switch", "/ar/" in hub.current_url() and hub.current_url().rstrip("/").endswith("media-center"),
         hub.current_url(), "<WEB_BASE_URL>/ar/.../media-center")
    c.eq(1, "<html dir>", doc["dir"], "rtl")
    c.ok(1, "<html lang>", doc["lang"].lower().startswith("ar"), doc["lang"], "ar*")
    # step 2 — hero
    label, home, cur = hub.style(P.HERO_PAGE_LABEL), hub.style(P.HERO_CRUMB_HOME), hub.style(P.HERO_CRUMB_CURRENT)
    c.ok(2, "page label Arabic", _is_arabic(label["text"]), label["text"], "Arabic")
    c.ok(2, "page label right-aligned (right edge of content)", abs(label["box"]["right"] - (CONTENT_X + CONTENT_W)) <= 2,
         label["box"]["right"], CONTENT_X + CONTENT_W)
    c.eq(2, "breadcrumb text", [home["text"], cur["text"]], ["الرئيسية", "المركز الإعلامي"])
    c.ok(2, "breadcrumb reads right-to-left", home["box"]["x"] > cur["box"]["x"], (home["box"]["x"], cur["box"]["x"]),
         "Home right of Media Center")
    for loc, name in ((P.HERO_HEADLINE, "headline"), (P.HERO_DESCRIPTION, "description")):
        st = hub.style(loc)
        c.ok(2, f"hero {name} Arabic", _is_arabic(st["text"]), st["text"][:50], "Arabic")
        # Figma 5461:196214 centres the AR headline/description; right-aligned or centred are both RTL-correct.
        c.ok(2, f"hero {name} RTL alignment", _right_aligned(st) or st["textAlign"] == "center", st["textAlign"],
             "right (or Figma-centred)")
    # step 3 — counts + quick access
    for loc, name in ((P.COUNT_LABEL, "widget name"), (P.COUNT_VALUE, "unit label"), (P.QA_TITLE, "card title"),
                      (P.QA_CARD_DESCRIPTION, "card description")):
        bad = [t for t in hub.texts(loc) if not _is_arabic(re.sub(r"[\d,٬\s]+", " ", t).strip() or t)]
        c.ok(3, f"{name}s Arabic", not bad, bad, "all Arabic")
    cards = hub.styles_all(P.COUNT_CARD)
    c.ok(3, "first widget at right edge", cards[0]["box"]["x"] == max(x["box"]["x"] for x in cards),
         [round(x["box"]["x"]) for x in cards], "first widget right-most")
    qa = hub.styles_all(P.QA_CARD)
    c.ok(3, "first card at right edge", abs(qa[0]["box"]["right"] - (CONTENT_X + CONTENT_W)) <= 2
         and qa[0]["box"]["x"] == max(x["box"]["x"] for x in qa), [round(x["box"]["x"]) for x in qa], "first card right-most")
    # step 4 — feeds + band
    for loc in (P.NF_EYEBROW, P.NF_HEADING, P.PF_EYEBROW, P.PF_HEADING, P.VF_EYEBROW, P.VF_HEADING,
                P.SUB_HEADING, P.SUB_DESCRIPTION):
        st = hub.style(loc)
        c.ok(4, f"{loc} Arabic", _is_arabic(st["text"]), st["text"][:50], "Arabic")
        c.ok(4, f"{loc} right-aligned", _right_aligned(st), f"{st['textAlign']}/{st['direction']}", "right")
    for loc in (P.NF_CTA_HEAD, P.PF_CTA_HEAD, P.VF_CTA_HEAD, P.SUB_BUTTON):
        t = hub.texts(loc)[0]
        c.ok(4, f"{loc} label Arabic", _is_arabic(t), t, "Arabic")
    ph = hub.placeholder(P.SUB_INPUT)
    c.ok(4, "band placeholder Arabic", _is_arabic(ph), ph, "Arabic")
    sub_in = hub.style(P.SUB_INPUT)
    c.ok(4, "band input right-aligned", _right_aligned(sub_in), f"{sub_in['textAlign']}/{sub_in['direction']}", "right")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149066 — AR: quick-access arrows and carousel controls mirrored for RTL")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_130709
@pytest.mark.tc_149066
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149066_arabic_arrows_and_carousel_mirrored(page):
    """MEDIA-MCHUB-TC-012."""
    hub = _hub(page, "ar")
    hub.scroll_into_view(P.QA)
    c = Checks("TC 149066")
    dirs = [hub.icon_direction(P.QA_ARROW, i) for i in range(hub.count(P.QA_ARROW))]
    c.ok(1, "card arrows point left", dirs and all(d == "left" for d in dirs), dirs, "all 'left'")
    hub.scroll_into_view(P.PF_CONTROLS)
    prev, nxt, ind = hub.style(P.PF_PREV), hub.style(P.PF_NEXT), hub.style(P.PF_INDICATOR)
    c.ok(2, "'Next' on the left, 'Previous' on the right", nxt["box"]["x"] < prev["box"]["x"],
         {"next_x": nxt["box"]["x"], "prev_x": prev["box"]["x"]}, "next_x < prev_x")
    c.eq(2, "position indicator text direction", ind["direction"], "rtl")
    hub.save_evidence("tc149066_ar_controls", full_page=False)
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149070 — count widgets are not links and show no link affordance")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149070
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149070_count_widgets_not_links(page):
    """MEDIA-MCHUB-TC-016."""
    hub = _hub(page)
    hub.scroll_into_view(P.COUNTS)
    c = Checks("TC 149070")
    before = hub.style(P.COUNT_LABEL, 0)
    hub.hover(P.COUNT_CARD, 0)
    card, label = hub.style(P.COUNT_CARD, 0), hub.style(P.COUNT_LABEL, 0)
    c.ok(1, "cursor on hover", card["cursor"] != "pointer" and label["cursor"] != "pointer",
         (card["cursor"], label["cursor"]), "not 'pointer'")
    c.ok(1, "underline on hover", "underline" not in label["textDecorationLine"], label["textDecorationLine"], "none")
    c.ok(1, "no hover colour change", label["color"] == before["color"], label["color"], before["color"])
    hub.save_evidence("tc149070_articles_hover", full_page=False)
    info = hub.links_and_roles_inside(P.COUNT_CARD, 0)
    c.ok(2, "no <a href>", not info["href"] and info["inner_links"] == 0 and not info["closest_link"], info, "no link")
    c.ok(2, "no link/button role or handler", info["role"] not in ("link", "button") and info["inner_buttons"] == 0
         and not info["onclick"], info, "no role/handler")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149072 — photo carousel Previous/Next operable by keyboard, indicator updates")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_130709
@pytest.mark.tc_149072
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149072_carousel_keyboard(page):
    """MEDIA-MCHUB-TC-018."""
    hub = _hub(page)
    hub.scroll_into_view(P.PF)
    start = INDICATOR.match(hub.indicator_text())
    assert start, f"indicator not in '<n> / <total>' form: {hub.indicator_text()!r}"
    total = start.group(2)
    reached = hub.tab_to_carousel_next()
    focus = hub.focused_element()
    hub.save_evidence("tc149072_next_focused", full_page=False)
    assert reached, f"Tab never reached the carousel Next control; focus on {focus}"
    assert focus["outline_style"] != "none" and _num(focus["outline_width"]) > 0, f"no visible focus outline: {focus}"
    hub.press_key("Enter")
    hub.wait_for_indicator("2")
    m = INDICATOR.match(hub.indicator_text())
    assert m and m.group(1) == "2" and m.group(2) == total, f"after Enter: {hub.indicator_text()!r}"
    hub.press_key("Shift+Tab")
    assert hub.is_focused(P.PF_PREV), f"Shift+Tab did not focus Previous: {hub.focused_element()}"
    hub.press_key("Space")
    hub.wait_for_indicator("1")
    m = INDICATOR.match(hub.indicator_text())
    hub.save_evidence("tc149072_back_to_1", full_page=False)
    assert m and m.group(1) == "1" and m.group(2) == total, f"after Space: {hub.indicator_text()!r}"


# ═════════════════════════════════════════════════════════════════════════
#  Responsive (TC-020 .. TC-024, TC-027)
# ═════════════════════════════════════════════════════════════════════════
def _columns(styles: list) -> int:
    return len({round(s["box"]["x"]) for s in styles if s["box"]["w"] > 0})


def _rows(styles: list) -> int:
    return len({round(s["box"]["y"]) for s in styles if s["box"]["w"] > 0})


def _overlaps(styles: list) -> list:
    out = []
    for i in range(len(styles)):
        for j in range(i + 1, len(styles)):
            if _overlap(styles[i]["box"], styles[j]["box"]):
                out.append((i, j))
    return out


def _responsive_hub_layout(page, tc: str, viewport: str):
    hub = _hub(page)
    c = Checks(f"TC {tc}")
    doc = hub.document_state()
    c.ok(1, "no horizontal scrollbar", doc["scroll_width"] <= doc["client_width"],
         f"scrollWidth {doc['scroll_width']} > clientWidth {doc['client_width']}", "scrollWidth <= clientWidth")
    counts, qa = hub.styles_all(P.COUNT_CARD), hub.styles_all(P.QA_CARD)
    if viewport == "desktop":
        c.eq(2, "counts strip: five widgets in one row", (len(counts), _rows(counts)), (5, 1))
        c.ok(2, "quick-access multi-column grid", _columns(qa) >= 2, _columns(qa), ">= 2 columns")
    elif viewport == "tablet":
        c.ok(2, "counts strip wraps to fewer columns", _columns(counts) < 5, _columns(counts), "< 5 columns")
        c.ok(2, "quick-access grid wraps to fewer columns", _columns(qa) < 3, _columns(qa), "< 3 columns")
    else:
        c.ok(2, "counts strip 1-2 columns", _columns(counts) <= 2, _columns(counts), "<= 2 columns")
        c.ok(2, "quick-access 1-2 columns", _columns(qa) <= 2, _columns(qa), "<= 2 columns")
        form, btn = hub.style(P.HERO_SEARCH_FORM), hub.style(P.HERO_SEARCH_BUTTON)
        vw = doc["viewport"][0]
        c.ok(2, "search field fits the width", form["box"]["x"] >= 0 and form["box"]["right"] <= vw,
             form["box"], f"inside 0..{vw}")
        c.ok(2, "Search button inside the field", btn["box"]["x"] >= form["box"]["x"] and btn["box"]["right"] <= form["box"]["right"],
             (btn["box"], form["box"]), "button within field")
    c.ok(2, "no overlapping widgets/cards", not _overlaps(counts) and not _overlaps(qa),
         {"counts": _overlaps(counts), "qa": _overlaps(qa)}, "none")
    clipped = hub.clipped_or_offscreen_text((P.HERO, P.COUNTS, P.QA))
    c.ok(2, "no clipped text", not clipped, clipped, "[]")
    hub.save_evidence(f"tc{tc}_{viewport}_hub_layout")
    nav = hub.click_quick_access_card("Photo Gallery")
    c.ok(3, "Photo Gallery card navigates", "/photo-gallery" in nav["url"] and (nav["status"] or 0) < 400,
         nav, "/photo-gallery, HTTP < 400")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149074 — hub layout responsive at 1920x1080 (desktop)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_130709
@pytest.mark.tc_149074
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149074_hub_layout_desktop(page):
    """MEDIA-MCHUB-TC-020."""
    _responsive_hub_layout(page, "149074", "desktop")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149075 — hub layout responsive at 768x1024 (tablet)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_130709
@pytest.mark.tc_149075
@pytest.mark.parametrize("page", [TABLET], indirect=True)
def test_tc_149075_hub_layout_tablet(page):
    """MEDIA-MCHUB-TC-021."""
    _responsive_hub_layout(page, "149075", "tablet")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149076 — hub layout responsive at 375x812 (mobile)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_130709
@pytest.mark.tc_149076
@pytest.mark.parametrize("page", [MOBILE_375], indirect=True)
def test_tc_149076_hub_layout_mobile(page):
    """MEDIA-MCHUB-TC-022."""
    _responsive_hub_layout(page, "149076", "mobile")


def _responsive_feeds(page, tc: str, viewport: str):
    hub = _hub(page)
    c = Checks(f"TC {tc}")
    doc = hub.document_state()
    c.ok(1, "no horizontal scrollbar", doc["scroll_width"] <= doc["client_width"],
         f"scrollWidth {doc['scroll_width']} > clientWidth {doc['client_width']}", "scrollWidth <= clientWidth")
    media, body = hub.style(P.NF_LEAD_MEDIA), hub.style(P.NF_LEAD_BODY)
    c.ok(2, "lead article stacks (image above text)", body["box"]["y"] >= media["box"]["bottom"] - 1,
         {"media": media["box"], "body": body["box"]}, "text below image")
    nf_cards = hub.styles_all(P.NF_CARD)
    c.ok(2, "news cards reflow below the lead", all(s["box"]["y"] >= body["box"]["bottom"] - 1 for s in nf_cards),
         [round(s["box"]["y"]) for s in nf_cards], "below lead")
    pf_visible = hub.visible_count(P.PF_CARD)
    if viewport == "tablet":
        c.ok(2, "news cards reflow to fewer columns", _columns(nf_cards) < 3, _columns(nf_cards), "< 3 columns")
        c.ok(2, "photo carousel shows fewer cards per view than desktop (3)", pf_visible < 3, pf_visible, "< 3")
        c.ok(2, "video cards wrap", _columns(hub.styles_all(P.VF_CARD)) < 3, _columns(hub.styles_all(P.VF_CARD)), "< 3 columns")
    else:
        c.eq(2, "news cards one column", _columns(nf_cards), 1)
        c.eq(2, "photo carousel shows one card per view", pf_visible, 1)
        vw = doc["viewport"][0]
        for loc, name in ((P.PF_PREV, "Previous"), (P.PF_NEXT, "Next")):
            st = hub.style(loc)
            c.ok(2, f"{name} control usable", st["box"]["w"] >= 24 and st["box"]["h"] >= 24 and 0 <= st["box"]["x"]
                 and st["box"]["right"] <= vw, st["box"], ">= 24x24 inside the viewport")
        c.eq(2, "video cards stack", _columns(hub.styles_all(P.VF_CARD)), 1)
    clipped = hub.clipped_or_offscreen_text((P.NF, P.PF, P.VF))
    c.ok(2, "no clipped text", not clipped, clipped, "[]")
    hub.save_evidence(f"tc{tc}_{viewport}_feeds")
    hub.scroll_into_view(P.PF_NEXT)
    before = hub.indicator_text()
    hub.click_next()
    hub.wait_for_indicator("2")
    after = hub.indicator_text()
    c.ok(3, "Next advances the carousel", INDICATOR.match(after) and INDICATOR.match(after).group(1) == "2",
         f"{before} -> {after}", "'2 / <total>'")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149077 — three content feeds responsive at 768x1024 (tablet)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_130709
@pytest.mark.tc_149077
@pytest.mark.parametrize("page", [TABLET], indirect=True)
def test_tc_149077_feeds_tablet(page):
    """MEDIA-MCHUB-TC-023."""
    _responsive_feeds(page, "149077", "tablet")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149078 — three content feeds responsive at 375x812 (mobile)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_130709
@pytest.mark.tc_149078
@pytest.mark.parametrize("page", [MOBILE_375], indirect=True)
def test_tc_149078_feeds_mobile(page):
    """MEDIA-MCHUB-TC-024."""
    _responsive_feeds(page, "149078", "mobile")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149081 — Arabic hub RTL and responsive at 375x812")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_130709
@pytest.mark.tc_149081
@pytest.mark.parametrize("page", [MOBILE_375], indirect=True)
def test_tc_149081_arabic_mobile(page):
    """MEDIA-MCHUB-TC-027."""
    hub = _hub(page, "ar")
    hub.save_evidence("tc149081_ar_mobile")
    c = Checks("TC 149081")
    doc = hub.document_state()
    c.eq(1, "<html dir>", doc["dir"], "rtl")
    c.ok(1, "no horizontal scrollbar", doc["scroll_width"] <= doc["client_width"],
         f"scrollWidth {doc['scroll_width']} > clientWidth {doc['client_width']}", "scrollWidth <= clientWidth")
    for loc, name in ((P.COUNT_CARD, "counts"), (P.QA_CARD, "quick-access cards"), (P.NF_CARD, "news cards"),
                      (P.PF_CARD, "photo cards"), (P.VF_CARD, "video cards")):
        c.eq(2, f"{name} stacked (one column)", _columns(hub.styles_all(loc)), 1)
    form, sub_in, sub_btn = hub.style(P.SUB_FORM), hub.style(P.SUB_INPUT), hub.style(P.SUB_BUTTON)
    c.ok(2, "band input above button (stacked)", sub_btn["box"]["y"] >= sub_in["box"]["bottom"] - 1,
         (sub_in["box"], sub_btn["box"]), "button below input")
    for loc in (P.QA_HEADING, P.QA_TITLE, P.NF_HEADING, P.NF_LEAD_TITLE, P.NF_CARD_TITLE, P.PF_HEADING, P.PF_CARD_TITLE,
                P.VF_HEADING, P.VF_CARD_TITLE, P.SUB_HEADING):
        st = hub.style(loc)
        c.ok(2, f"{loc} right-aligned", _right_aligned(st), f"{st['textAlign']}/{st['direction']}", "right")
    clipped = hub.clipped_or_offscreen_text()
    c.ok(2, "no clipped Arabic text", not clipped, clipped, "[]")
    c.done()


# ═════════════════════════════════════════════════════════════════════════
#  Themes (TC-028, TC-029, TC-030)
# ═════════════════════════════════════════════════════════════════════════
def _dark_readability(page, tc: str, locale: str):
    hub = _hub(page, locale)
    hub.enable_dark_theme()
    c = Checks(f"TC {tc}")
    doc = hub.document_state()
    c.eq(1, "theme attribute", doc["theme"], "dark")
    c.color(1, "page background switches to the dark palette", doc["body_background"], "#1D1D1B")
    if locale == "ar":
        c.eq(1, "<html dir>", doc["dir"], "rtl")
    hub.save_evidence(f"tc{tc}_{locale}_dark")
    low = hub.readability_scan()
    c.ok(2, "every text/icon/control readable (contrast >= 3:1)", not low, low, "[]")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149082 — hub readable in Dark theme (EN)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_130709
@pytest.mark.tc_149082
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149082_dark_theme_en(page):
    """MEDIA-MCHUB-TC-028."""
    _dark_readability(page, "149082", "en")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149083 — Arabic hub readable in Dark theme")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_130709
@pytest.mark.tc_149083
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149083_dark_theme_ar(page):
    """MEDIA-MCHUB-TC-029."""
    _dark_readability(page, "149083", "ar")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149084 — hub readable in High-Contrast mode, focus visible")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.pbi_130709
@pytest.mark.tc_149084
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149084_high_contrast(page):
    """MEDIA-MCHUB-TC-030."""
    hub = _hub(page)
    hub.enable_high_contrast()
    c = Checks("TC 149084")
    doc = hub.document_state()
    c.ok(1, "high-contrast styling applied", "qc-a11y-contrast" in doc["html_class"], doc["html_class"],
         "html.qc-a11y-contrast")
    hub.save_evidence("tc149084_high_contrast")
    low = hub.readability_scan()
    c.ok(2, "every text/icon/control distinguishable (contrast >= 3:1)", not low, low, "[]")
    for loc, name in ((P.QA_CARD, "quick-access card"), (P.COUNT_CARD, "count widget")):
        st = hub.style(loc)
        ratio = _contrast(_rgba(st["borderTopColor"])[:3], _rgba(doc["body_background"])[:3])
        c.ok(2, f"{name} border visible", _num(st["borderTopWidth"]) >= 1 and ratio >= 3, (st["borderTopWidth"],
             st["borderTopColor"], round(ratio, 2)), ">= 1px, contrast >= 3:1")
    hub.focus_first_quick_access_card()
    for i in range(1, 3):
        hub.press_key("Tab")
        f = hub.focused_element()
        ratio = _contrast(_rgba(f["outline_color"])[:3], _rgba(f["body_background"])[:3]) if f["outline_style"] != "none" else 0
        c.ok(3, f"Tab -> quick-access card {i + 1} focus indicator", "qc-mc-qa-card" in f["cls"] and _num(f["outline_width"]) > 0
             and ratio >= 3, f, "focused card with an outline >= 3:1 against the page")
    hub.save_evidence("tc149084_hc_focus", full_page=False)
    c.done()


# ═════════════════════════════════════════════════════════════════════════
#  Figma design-token cases (TC-285 .. TC-299)
# ═════════════════════════════════════════════════════════════════════════
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149339 — section order and desktop container match Figma 5461:196150")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149339
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149339_figma_section_order_and_container(page):
    """MEDIA-MCHUB-TC-285."""
    hub = _hub(page)
    hub.save_evidence("tc149339_light_en_desktop")
    c = Checks("TC 149339")
    c.eq(1, "section order", hub.section_order(), P.EXPECTED_SECTION_ORDER)
    shells = [hub.style(s) for s in (P.COUNTS_SHELL, P.QA_SHELL, P.NF_SHELL, P.PF_SHELL, P.VF_SHELL, P.SUB_BAND)]
    for s, name in zip(shells, ("counts", "explore", "news", "photo", "video", "band")):
        c.px(2, f"{name} content x (300px side padding, centred)", s["box"]["x"], CONTENT_X)
        c.px(2, f"{name} content width", s["box"]["w"], CONTENT_W)
    hero = hub.style(P.HERO)
    c.px(2, "body top padding (hero -> first section)", shells[0]["box"]["y"] - hero["box"]["bottom"], 64)
    for a, b, name in zip(shells, shells[1:], ("counts->explore", "explore->news", "news->photo", "photo->video", "video->band")):
        c.px(2, f"section gap {name}", b["box"]["y"] - a["box"]["bottom"], 48)
    sub = hub.style(P.SUB)
    c.px(2, "body bottom padding", sub["box"]["bottom"] - shells[-1]["box"]["bottom"], 64)
    for loc in (P.QA_HEADING, P.QA_CARD_DESCRIPTION):
        st = hub.style(loc)
        c.ok(3, f"{loc} font-family", font_family_contains(st["fontFamily"], "Cairo"), st["fontFamily"], "Cairo")
    c.ok(3, "Cairo web font actually loaded (no fallback)", hub.font_loaded("Cairo"), hub.font_loaded("Cairo"), True)
    c.color(4, "page background", hub.document_state()["body_background"], "#FFFFFF")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149340 — hero banner matches Figma 5461:196152")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149340
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149340_figma_hero(page):
    """MEDIA-MCHUB-TC-286."""
    hub = _hub(page)
    hub.save_evidence("tc149340_hero", full_page=False)
    c = Checks("TC 149340")
    hero, top, center, bg, scrim = (hub.style(x) for x in (P.HERO, P.HERO_TOP, P.HERO_CENTER, P.HERO_BG, P.HERO_SCRIM))
    c.px(1, "hero width", hero["box"]["w"], 1920)
    c.px(1, "hero content left inset", top["box"]["x"], CONTENT_X)
    c.px(1, "hero content width", top["box"]["w"], CONTENT_W)
    c.px(1, "hero top padding", top["box"]["y"] - hero["box"]["y"], 40)
    c.px(1, "hero bottom padding", hero["box"]["bottom"] - center["box"]["bottom"], 40)
    c.ok(1, "hero section image (cover)", "url(" in bg["backgroundImage"] and bg["backgroundSize"] == "cover",
         (bg["backgroundImage"][:60], bg["backgroundSize"]), "url(...) / cover")
    c.gradient(1, "hero overlay", scrim["backgroundImage"], 90,
               [("rgba(29,29,27,0.9)", 16), ("rgba(145,23,49,0.9)", 84)])
    label, crumbs = hub.style(P.HERO_PAGE_LABEL), hub.style(P.HERO_CRUMBS)
    home, home_lbl, cur = hub.style(P.HERO_CRUMB_HOME), hub.style(P.HERO_CRUMB_HOME_LABEL), hub.style(P.HERO_CRUMB_CURRENT)
    icon = hub.style(P.HERO_HOME_ICON)
    c.eq(2, "page label text", label["text"], "Media Center")
    c.typo(2, "page label", label, 30, 38, 700, "#FFFFFF")
    c.px(2, "page label left-aligned", label["box"]["x"], CONTENT_X)
    c.ok(2, "breadcrumb on the same row", crumbs["box"]["y"] < label["box"]["bottom"] and crumbs["box"]["bottom"] > label["box"]["y"],
         (label["box"]["y"], crumbs["box"]["y"]), "vertically overlapping rows")
    c.eq(2, "breadcrumb text", [home_lbl["text"], cur["text"]], ["Home", "Media Center"])
    c.size(2, "home icon", icon, 16, 16, 0.5)
    c.eq(2, "separator chevron direction", hub.icon_direction(P.HERO_CRUMB_SEPARATOR_ICON), "right")
    c.typo(2, "breadcrumb 'Home'", home_lbl, 14, 22, 400, "#FFFFFF")
    c.typo(2, "breadcrumb 'Media Center'", cur, 14, 22, 400, "#FFFFFF")
    c.px(2, "breadcrumb item gap", crumbs["gap"], 6, 0.5)
    c.px(2, "home icon-label gap", home["gap"], 6, 0.5)
    head, desc, copy = hub.style(P.HERO_HEADLINE), hub.style(P.HERO_DESCRIPTION), hub.style(P.HERO_COPY)
    c.eq(3, "headline text", _norm_quotes(head["text"]), "Your gateway to Qatar Chamber's official news")
    c.typo(3, "headline", head, 30, 38, 700, "#FFFFFF")
    c.eq(3, "headline centred", head["textAlign"], "center")
    c.px(3, "centred block width", center["box"]["w"], 872)
    c.typo(3, "description", desc, 16, 24, 400, "#FFFFFF")
    c.eq(3, "description centred", desc["textAlign"], "center")
    c.px(3, "description 8px below headline", desc["box"]["y"] - head["box"]["bottom"], 8)
    c.pad(3, "headline block", center, 32, 0, 32, 0)
    form = hub.style(P.HERO_SEARCH_FORM)
    ph = hub.placeholder_style(P.HERO_SEARCH_INPUT)
    c.px(4, "search width", form["box"]["w"], 872)
    c.radius(4, "search", form, 9999)
    c.color(4, "search background", form["backgroundColor"], "#FFFFFF")
    c.border(4, "search", form, 1, "#EDEDED")
    c.pad(4, "search", form, 10, 12, 10, 32)
    c.px(4, "search 24px below description", form["box"]["y"] - desc["box"]["bottom"], 24)
    # ::placeholder reports line-height 'normal'; the rendered placeholder line box is the input's own.
    c.typo(4, "placeholder", {**ph, "lineHeight": hub.style(P.HERO_SEARCH_INPUT)["lineHeight"]}, 14, 22, 400, "#7C7B7B")
    btn, bico, blbl = hub.style(P.HERO_SEARCH_BUTTON), hub.style(P.HERO_SEARCH_BUTTON_ICON), hub.style(P.HERO_SEARCH_BUTTON_LABEL)
    c.color(5, "Search button background", btn["backgroundColor"], "#911731")
    c.radius(5, "Search button", btn, 9999)
    c.pad(5, "Search button", btn, 10, 16, 10, 16)
    c.size(5, "search icon", bico, 20, 20, 0.5)
    c.ok(5, "icon left of label", bico["box"]["right"] <= blbl["box"]["x"], (bico["box"]["x"], blbl["box"]["x"]), "icon first")
    c.eq(5, "button label", blbl["text"], "Search")
    c.typo(5, "button label", blbl, 16, 24, 600, "#FFFFFF")
    c.px(5, "icon-label gap", blbl["box"]["x"] - bico["box"]["right"], 6, 0.5)
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149341 — summary counts strip matches Figma 5461:196154")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149341
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149341_figma_counts_strip(page):
    """MEDIA-MCHUB-TC-287."""
    hub = _hub(page)
    hub.scroll_into_view(P.COUNTS)
    hub.save_evidence("tc149341_counts", full_page=False)
    c = Checks("TC 149341")
    shell, texture, lst = hub.style(P.COUNTS_SHELL), hub.style(P.COUNTS_TEXTURE), hub.style(P.COUNTS_LIST)
    tiles = hub.styles_all(P.COUNT_CARD)
    c.px(1, "strip height", shell["box"]["h"], 182)
    c.pad(1, "strip", shell, 24, 24, 24, 24)
    c.radius(1, "strip", shell, 20)
    c.color(1, "strip base colour", shell["backgroundColor"], "#F6F0EC")
    c.ok(1, "decorative pattern over the base colour", texture["backgroundImage"] != "none", texture["backgroundImage"][:40], "pattern")
    c.eq(1, "five tiles in one row", (len(tiles), _rows(tiles)), (5, 1))
    for a, b in zip(tiles, tiles[1:]):
        c.px(1, "gap between tiles", b["box"]["x"] - a["box"]["right"], 24)
    widths = [t["box"]["w"] for t in tiles]
    c.ok(1, "tiles equal width", max(widths) - min(widths) <= 1, [round(w, 1) for w in widths], "equal")
    c.px(1, "tiles fill the strip (left)", tiles[0]["box"]["x"] - shell["box"]["x"], 24)
    c.px(1, "tiles fill the strip (right)", shell["box"]["right"] - tiles[-1]["box"]["right"], 24)
    t0, chip = tiles[0], hub.style(P.COUNT_ICON_CHIP)
    c.color(2, "tile background", t0["backgroundColor"], "#FFFFFF")
    c.border(2, "tile", t0, 1, "#EDEDED")
    c.radius(2, "tile", t0, 12)
    c.pad(2, "tile", t0, 16, 0, 16, 0)
    c.ok(2, "tile content centred column", t0["flexDirection"] == "column" and t0["alignItems"] == "center",
         (t0["flexDirection"], t0["alignItems"]), "column / center")
    c.px(2, "tile gap", t0["gap"], 8, 0.5)
    c.size(2, "icon chip", chip, 48, 48, 0.5)
    c.radius(2, "icon chip", chip, 9999)
    c.color(2, "icon chip fill", chip["backgroundColor"], "#F6F6F6")
    c.eq(3, "tile order left-to-right", [t["text"].split("\n")[0] for t in sorted(tiles, key=lambda t: t["box"]["x"])],
         WIDGET_LABELS_EN)
    labels, values = hub.styles_all(P.COUNT_LABEL), hub.styles_all(P.COUNT_VALUE)
    for i, (lb, val) in enumerate(zip(labels, values)):
        c.typo(3, f"label {lb['text']}", lb, 16, 24, 700, "#343432")
        c.eq(3, f"label {lb['text']} centred", lb["textAlign"], "center")
        m = re.match(r"^(\d[\d,]*)\s+(.+)$", val["text"])
        c.ok(3, f"count line {i + 1}", m is not None and m.group(2) == WIDGET_UNITS_EN[i], val["text"],
             f"'<live count> {WIDGET_UNITS_EN[i]}'")
        c.typo(3, f"count line {i + 1}", val, 14, 22, 400, "#7C7B7B")
    for i in range(len(tiles)):
        before_tile, before_lbl = hub.style(P.COUNT_CARD, i), hub.style(P.COUNT_LABEL, i)
        hub.hover(P.COUNT_CARD, i)
        tile, lbl = hub.style(P.COUNT_CARD, i), hub.style(P.COUNT_LABEL, i)
        c.ok(4, f"tile {i + 1} hover: no pointer", tile["cursor"] != "pointer" and lbl["cursor"] != "pointer",
             (tile["cursor"], lbl["cursor"]), "not pointer")
        c.ok(4, f"tile {i + 1} hover: no underline", "underline" not in lbl["textDecorationLine"], lbl["textDecorationLine"], "none")
        c.ok(4, f"tile {i + 1} hover: no colour change", lbl["color"] == before_lbl["color"]
             and tile["backgroundColor"] == before_tile["backgroundColor"], (lbl["color"], tile["backgroundColor"]), "unchanged")
    hub.move_mouse_away()
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149342 — 'Explore the hub' section matches Figma 5461:196165/196166")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149342
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149342_figma_explore_hub(page):
    """MEDIA-MCHUB-TC-288."""
    hub = _hub(page)
    hub.scroll_into_view(P.QA)
    hub.save_evidence("tc149342_explore_hub", full_page=False)
    c = Checks("TC 149342")
    eb, hd, ds, head, grid = (hub.style(x) for x in (P.QA_EYEBROW, P.QA_HEADING, P.QA_DESCRIPTION, P.QA_HEAD, P.QA_GRID))
    c.eq(1, "eyebrow text", eb["text"], "Explore the hub")
    c.typo(1, "eyebrow", eb, 14, 22, 400, "#911731")
    c.eq(1, "heading text", hd["text"], "Everything in one place")
    c.typo(1, "heading", hd, 24, 32, 700, "#1D1D1B")
    c.eq(1, "description text", ds["text"], "Move directly to the resource you need, from visual archives to media support.")
    c.typo(1, "description", ds, 14, 22, 400, "#7C7B7B")
    c.px(1, "header 24px above the grid", grid["box"]["y"] - head["box"]["bottom"], 24)
    cards = hub.styles_all(P.QA_CARD)
    c.eq(2, "grid 3 columns x 2 rows", (_columns(cards), _rows(cards)), (3, 2))
    for card in cards:
        c.px(2, "card width", card["box"]["w"], 424)
    c.px(2, "column gap", cards[1]["box"]["x"] - cards[0]["box"]["right"], 24)
    c.px(2, "row gap", cards[3]["box"]["y"] - cards[0]["box"]["bottom"], 24)
    card, tile, title, desc, arrow = (hub.style(x) for x in (P.QA_CARD, P.QA_ICON_TILE, P.QA_TITLE, P.QA_CARD_DESCRIPTION, P.QA_ARROW))
    c.color(3, "card background", card["backgroundColor"], "#FFFFFF")
    c.border(3, "card", card, 1, "#EDEDED")
    c.radius(3, "card", card, 16)
    c.pad(3, "card", card, 24, 24, 24, 24)
    c.px(3, "card gap", card["gap"], 16, 0.5)
    c.size(3, "icon tile", tile, 48, 48, 0.5)
    c.color(3, "icon tile fill", tile["backgroundColor"], "#911731")
    c.radius(3, "icon tile", tile, 8)
    c.ok(3, "icon tile on the left", tile["box"]["x"] < title["box"]["x"], (tile["box"]["x"], title["box"]["x"]), "left of title")
    c.typo(3, "card title", title, 20, 30, 700, "#343432")
    c.typo(3, "card description", desc, 12, 18, 400, "#7C7B7B")
    c.size(3, "arrow icon", arrow, 24, 24, 0.5)
    c.px(3, "arrow at the right end", card["box"]["right"] - arrow["box"]["right"], 24)
    c.eq(3, "arrow points right", hub.icon_direction(P.QA_ARROW), "right")
    c.eq(4, "card titles in grid order", [t for t in hub.texts(P.QA_TITLE)], QA_TITLES_EN)
    c.eq(4, "card descriptions (apostrophe style normalised)", [_norm_quotes(t) for t in hub.texts(P.QA_CARD_DESCRIPTION)],
         [_norm_quotes(t) for t in QA_DESCRIPTIONS_EN])
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149343 — 'News & press releases' feed matches Figma 5461:196174/196176/196196")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149343
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149343_figma_news_feed(page):
    """MEDIA-MCHUB-TC-289."""
    hub = _hub(page)
    hub.scroll_into_view(P.NF)
    hub.save_evidence("tc149343_news_feed")
    c = Checks("TC 149343")
    eb, hd, head, cta = (hub.style(x) for x in (P.NF_EYEBROW, P.NF_HEADING, P.NF_HEAD, P.NF_CTA_HEAD))
    c.eq(1, "eyebrow text", eb["text"], "Latest updates")
    c.typo(1, "eyebrow", eb, 14, 22, 400, "#911731")
    c.eq(1, "heading text", hd["text"], "News & press releases")
    c.typo(1, "heading", hd, 24, 32, 700, "#1D1D1B")
    c.px(1, "CTA at the right end of the header row", cta["box"]["right"], CONTENT_X + CONTENT_W)
    c.ok(1, "CTA on the same row", cta["box"]["y"] >= head["box"]["y"] - 1 and cta["box"]["bottom"] <= head["box"]["bottom"] + 1,
         (cta["box"], head["box"]), "inside header row")
    _pill_cta(c, 2, "'View All Articles'", cta, "#FFFFFF", "#DEDEDD", "#4A4A49", "View All Articles")
    ico = hub.style(P.NF_CTA_HEAD_ICON)
    c.size(2, "CTA arrow icon", ico, 20, 20, 0.5)
    c.px(2, "CTA label-icon gap", cta["gap"], 6, 0.5)
    lead, media, img, body = (hub.style(x) for x in (P.NF_LEAD, P.NF_LEAD_MEDIA, P.NF_LEAD_IMAGE, P.NF_LEAD_BODY))
    grid = hub.style(P.NF_GRID)
    c.px(3, "lead row gap", body["box"]["x"] - media["box"]["right"], 24)
    c.size(3, "lead image", media, 648, 360, 5)
    c.radius(3, "lead image", media, 12)
    c.eq(3, "lead image object-fit", img["objectFit"], "cover")
    c.ok(3, "image left, text right", media["box"]["x"] < body["box"]["x"], (media["box"]["x"], body["box"]["x"]), "image first")
    c.px(3, "text column vertically centred (offset from image centre)",
         (body["box"]["y"] + body["box"]["h"] / 2) - (media["box"]["y"] + media["box"]["h"] / 2), 0)
    c.px(3, "lead 24px below header", lead["box"]["y"] - head["box"]["bottom"], 24)
    c.px(3, "lead 40px above card row", grid["box"]["y"] - lead["box"]["bottom"], 40)
    chips = hub.styles_all(P.NF_LEAD_CHIP)
    c.eq(4, "chips", [x["text"] for x in chips], ["Featured", "Trade & Economy"])
    for ch in chips:
        c.color(4, f"chip '{ch['text']}' background", ch["backgroundColor"], "#F6F6F6")
        c.radius(4, f"chip '{ch['text']}'", ch, 6)
        c.pad(4, f"chip '{ch['text']}'", ch, 6, 8, 6, 8)
        c.typo(4, f"chip '{ch['text']}'", ch, 16, 24, 400, "#6C6C6B")
    if len(chips) == 2:
        c.px(4, "chips 10px apart", chips[1]["box"]["x"] - chips[0]["box"]["right"], 10)
    title, excerpt, meta = hub.style(P.NF_LEAD_TITLE), hub.style(P.NF_LEAD_EXCERPT), hub.style(P.NF_LEAD_META)
    c.typo(4, "lead title", title, 30, 38, 700, "#343432")
    c.typo(4, "excerpt", excerpt, 18, 28, 400, "#4A4A49")
    items = hub.styles_all(P.NF_LEAD_META_ITEM)
    texts = [x["text"] for x in items]
    c.ok(4, "meta = date, view count, read time", len(texts) == 3 and EN_DATE.match(texts[0]) and VIEWS.match(texts[1])
         and READ_TIME.match(texts[2]), texts, "[date, views, read time]")
    for it in items:
        c.typo(4, f"meta '{it['text']}'", it, 14, 22, 400, "#6C6C6B")
        c.px(4, f"meta '{it['text']}' icon gap", it["gap"], 6, 0.5)
    for i in range(hub.count(P.NF_LEAD_META_ICON)):
        c.size(4, f"meta icon {i + 1}", hub.style(P.NF_LEAD_META_ICON, i), 18, 18, 0.5)
    c.px(4, "meta items 16px apart", meta["gap"], 16, 0.5)
    more, more_ico = hub.style(P.NF_READ_MORE), hub.style(P.NF_READ_MORE_ICON)
    c.eq(4, "Read More text", more["text"], "Read More")
    c.typo(4, "Read More", more, 16, 24, 600, "#911731")
    c.size(4, "Read More arrow", more_ico, 20, 20, 0.5)
    c.px(4, "Read More 24px below the text block", more["box"]["y"] - meta["box"]["bottom"], 24)
    cards = hub.styles_all(P.NF_CARD)
    c.eq(5, "three cards in one row", (len(cards), _rows(cards)), (3, 1))
    for a, b in zip(cards, cards[1:]):
        c.px(5, "card gap", b["box"]["x"] - a["box"]["right"], 24)
    for i, card in enumerate(cards):
        cm, ct = hub.style(P.NF_CARD_MEDIA, i), hub.style(P.NF_CARD_TITLE, i)
        c.px(5, f"card {i + 1} width", card["box"]["w"], 424)
        c.px(5, f"card {i + 1} image height", cm["box"]["h"], 240, 5)
        c.radius(5, f"card {i + 1} image", cm, 10)
        c.typo(5, f"card {i + 1} title", ct, 18, 28, 700, "#1D1D1B")
        c.px(5, f"card {i + 1} title 12px below image", ct["box"]["y"] - cm["box"]["bottom"], 12)
        m = hub.texts_within(P.NF_CARD, i, ".qc-mc-nf-meta-item")
        c.ok(5, f"card {i + 1} meta = date + views only", len(m) == 2 and EN_DATE.match(m[0]) and VIEWS.match(m[1]), m,
             "[date, views] (no read time)")
    for i in range(hub.count(P.NF_CARD_META_ITEM)):
        c.typo(5, f"card meta item {i + 1}", hub.style(P.NF_CARD_META_ITEM, i), 14, 22, 400, "#6C6C6B")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149344 — Photo Gallery feed matches Figma 5461:196201/196202")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149344
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149344_figma_photo_feed(page):
    """MEDIA-MCHUB-TC-290."""
    hub = _hub(page)
    hub.scroll_into_view(P.PF)
    hub.save_evidence("tc149344_photo_feed", full_page=False)
    c = Checks("TC 149344")
    eb, hd, head, cta, grid = (hub.style(x) for x in (P.PF_EYEBROW, P.PF_HEADING, P.PF_HEAD, P.PF_CTA_HEAD, P.PF_GRID))
    c.eq(1, "eyebrow text", eb["text"], "In pictures")
    c.typo(1, "eyebrow", eb, 14, 22, 400, "#911731")
    c.eq(1, "heading text", hd["text"], "Photo Gallery")
    c.typo(1, "heading", hd, 24, 32, 700, "#1D1D1B")
    _pill_cta(c, 1, "'View all albums'", cta, "#FFFFFF", "#DEDEDD", "#4A4A49", "View all albums")
    c.ok(1, "CTA arrow-up-right icon", hub.count(P.PF_CTA_HEAD_ICON) == 1, hub.count(P.PF_CTA_HEAD_ICON), 1)
    cards = [hub.style(P.PF_CARD, i) for i in range(hub.count(P.PF_CARD))]
    cards = [x for x in cards if x["box"]["w"] > 0]
    c.eq(2, "three album cards in one row", (len(cards), _rows(cards)), (3, 1))
    for a, b in zip(cards, cards[1:]):
        c.px(2, "card gap", b["box"]["x"] - a["box"]["right"], 24)
    for i, card in enumerate(cards):
        c.px(2, f"card {i + 1} width", card["box"]["w"], 424)
    c.px(2, "cards 24px below header", grid["box"]["y"] - head["box"]["bottom"], 24)
    media, img, badge, bico = (hub.style(x) for x in (P.PF_CARD_MEDIA, P.PF_CARD_IMAGE, P.PF_BADGE, P.PF_BADGE_ICON))
    btxt = hub.style(P.PF_BADGE_TEXT)
    c.px(3, "cover height", media["box"]["h"], 240, 5)
    c.radius(3, "cover", media, 10)
    c.eq(3, "cover object-fit", img["objectFit"], "cover")
    c.pad(3, "cover inner padding", media, 16, 16, 16, 16)
    c.px(3, "badge pinned left", badge["box"]["x"] - media["box"]["x"], 16)
    c.px(3, "badge pinned bottom", media["box"]["bottom"] - badge["box"]["bottom"], 16)
    c.color(3, "badge background", badge["backgroundColor"], "rgba(29,29,27,0.7)")
    c.radius(3, "badge", badge, 6)
    c.pad(3, "badge", badge, 2, 8, 2, 8)
    c.size(3, "badge image icon", bico, 14, 14, 0.5)
    c.ok(3, "badge text", PHOTO_BADGE.match(btxt["text"]) is not None, btxt["text"], "'<n> photos'")
    c.typo(3, "badge text", btxt, 14, 22, 400, "#FFFFFF")
    chip, title, meta = hub.style(P.PF_CATEGORY_CHIP), hub.style(P.PF_CARD_TITLE), hub.style(P.PF_CARD_META)
    c.color(4, "category chip background", chip["backgroundColor"], "#F6F6F6")
    c.radius(4, "category chip", chip, 6)
    c.pad(4, "category chip", chip, 2, 8, 2, 8)
    c.typo(4, "category chip", chip, 14, 22, 500, "#6C6C6B")
    c.typo(4, "title", title, 18, 28, 700, "#1D1D1B")
    c.px(4, "title 4px below the chip", title["box"]["y"] - chip["box"]["bottom"], 4)
    items = hub.texts_within(P.PF_CARD, 0, P.PF_CARD_META_ITEM)
    c.ok(4, "meta = date + view count", len(items) == 2 and EN_DATE.match(items[0]) and VIEWS.match(items[1]), items, "[date, views]")
    c.typo(4, "meta", hub.style(P.PF_CARD_META_ITEM), 14, 22, 400, "#6C6C6B")
    c.px(4, "meta items 16px apart", meta["gap"], 16, 0.5)
    c.ok(5, "previous/next controls + position indicator present (PBI US-003; styling observation only)",
         hub.is_visible(P.PF_PREV) and hub.is_visible(P.PF_NEXT) and hub.is_visible(P.PF_INDICATOR),
         [hub.is_visible(x) for x in (P.PF_PREV, P.PF_NEXT, P.PF_INDICATOR)], "all visible")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149345 — Video Gallery feed matches Figma 5461:196207/196208")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149345
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149345_figma_video_feed(page):
    """MEDIA-MCHUB-TC-291."""
    hub = _hub(page)
    hub.scroll_into_view(P.VF)
    hub.save_evidence("tc149345_video_feed", full_page=False)
    c = Checks("TC 149345")
    eb, hd, cta = (hub.style(x) for x in (P.VF_EYEBROW, P.VF_HEADING, P.VF_CTA_HEAD))
    c.eq(1, "eyebrow text", eb["text"], "Watch now")
    c.typo(1, "eyebrow", eb, 14, 22, 400, "#911731")
    c.eq(1, "heading text", hd["text"], "Video Gallery")
    c.typo(1, "heading", hd, 24, 32, 700, "#1D1D1B")
    _pill_cta(c, 1, "'Watch now' CTA", cta, "#FFFFFF", "#DEDEDD", "#4A4A49", "Watch now")
    cards = hub.styles_all(P.VF_CARD)
    c.eq(2, "three video cards in one row", (len(cards), _rows(cards)), (3, 1))
    for a, b in zip(cards, cards[1:]):
        c.px(2, "card gap", b["box"]["x"] - a["box"]["right"], 24)
    for i, card in enumerate(cards):
        c.px(2, f"card {i + 1} width", card["box"]["w"], 424)
    media, scrim, dur, play = (hub.style(x) for x in (P.VF_CARD_MEDIA, P.VF_SCRIM, P.VF_DURATION, P.VF_PLAY))
    c.size(3, "thumbnail", media, 424, 240, 5)
    c.radius(3, "thumbnail", media, 10)
    c.color(3, "thumbnail dark overlay", scrim["backgroundColor"], "rgba(29,29,27,0.3)")
    c.ok(3, "overlay covers the thumbnail", abs(scrim["box"]["w"] - media["box"]["w"]) <= 1 and abs(scrim["box"]["h"] - media["box"]["h"]) <= 1,
         (scrim["box"], media["box"]), "same box")
    c.ok(3, "duration badge text", DURATION.match(dur["text"]) is not None, dur["text"], "'mm:ss'")
    c.px(3, "duration badge pinned left", dur["box"]["x"] - media["box"]["x"], 16)
    c.px(3, "duration badge pinned bottom", media["box"]["bottom"] - dur["box"]["bottom"], 16)
    c.color(3, "duration badge background", dur["backgroundColor"], "rgba(29,29,27,0.7)")
    c.radius(3, "duration badge", dur, 6)
    c.pad(3, "duration badge", dur, 2, 8, 2, 8)
    c.typo(3, "duration badge", dur, 14, None, 400, "#FFFFFF")
    c.size(3, "play button", play, 64, 64, 2)
    c.radius(3, "play button", play, 9999)
    c.color(3, "play button fill", play["backgroundColor"], "rgba(10,10,10,0.3)")
    c.eq(3, "play button backdrop blur", play["backdropFilter"], "blur(5px)")
    c.px(3, "play button centred (x)", (play["box"]["x"] + play["box"]["w"] / 2) - (media["box"]["x"] + media["box"]["w"] / 2), 0)
    c.px(3, "play button centred (y)", (play["box"]["y"] + play["box"]["h"] / 2) - (media["box"]["y"] + media["box"]["h"] / 2), 0)
    chip, title = hub.style(P.VF_CATEGORY_CHIP), hub.style(P.VF_CARD_TITLE)
    c.color(4, "category chip background", chip["backgroundColor"], "#F6F6F6")
    c.typo(4, "category chip", chip, 14, None, 500, "#6C6C6B")
    c.radius(4, "category chip", chip, 6)
    c.typo(4, "title", title, 18, 28, 700, "#1D1D1B")
    items = hub.texts_within(P.VF_CARD, 0, P.VF_CARD_META_ITEM)
    c.ok(4, "meta = published date only (no view count)", len(items) == 1 and EN_DATE.match(items[0]) is not None, items, "[date]")
    c.typo(4, "meta", hub.style(P.VF_CARD_META_ITEM), 14, None, 400, "#6C6C6B")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149347 — hub sections switch to the Dark-mode tokens (Figma 5461:198874)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149347
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149347_figma_dark_hub(page):
    """MEDIA-MCHUB-TC-293."""
    hub = _hub(page)
    unchanged = (P.HERO_SCRIM, P.HERO_HEADLINE, P.HERO_SEARCH_FORM, P.HERO_SEARCH_BUTTON, P.SUB_GRADIENT,
                 P.SUB_HEADING, P.SUB_DESCRIPTION, P.SUB_INPUT, P.SUB_BUTTON)
    light = {loc: hub.style(loc) for loc in unchanged}
    light_ph = hub.placeholder_style(P.HERO_SEARCH_INPUT)
    hub.enable_dark_theme()
    hub.save_evidence("tc149347_dark_en_desktop")
    c = Checks("TC 149347")
    c.color(1, "page background", hub.document_state()["body_background"], "#1D1D1B")
    shell, tile, chip = hub.style(P.COUNTS_SHELL), hub.style(P.COUNT_CARD), hub.style(P.COUNT_ICON_CHIP)
    c.color(2, "tile background", tile["backgroundColor"], "#1D1D1B")
    c.border(2, "tile", tile, 1, "#4A4A49")
    c.radius(2, "tile", tile, 12)
    c.color(2, "icon chip", chip["backgroundColor"], "#343432")
    c.color(2, "label text", hub.style(P.COUNT_LABEL)["color"], "#F6F6F6")
    c.color(2, "count line text", hub.style(P.COUNT_VALUE)["color"], "#D0D0D0")
    c.color(2, "strip keeps #F6F0EC base", shell["backgroundColor"], "#F6F0EC")
    c.px(2, "strip height", shell["box"]["h"], 182)
    c.color(3, "eyebrow", hub.style(P.QA_EYEBROW)["color"], "#C44561")
    c.color(3, "heading", hub.style(P.QA_HEADING)["color"], "#FFFFFF")
    c.color(3, "description", hub.style(P.QA_DESCRIPTION)["color"], "#D0D0D0")
    card = hub.style(P.QA_CARD)
    c.color(3, "card background", card["backgroundColor"], "#1D1D1B")
    c.border(3, "card", card, 1, "#4A4A49")
    c.radius(3, "card", card, 16)
    c.color(3, "card title", hub.style(P.QA_TITLE)["color"], "#F6F6F6")
    c.color(3, "card description", hub.style(P.QA_CARD_DESCRIPTION)["color"], "#D0D0D0")
    c.color(3, "icon tile", hub.style(P.QA_ICON_TILE)["backgroundColor"], "#911731")
    dark = {loc: hub.style(loc) for loc in unchanged}
    layers = (P.HERO_SCRIM, P.SUB_GRADIENT)  # paint-only layers: text colour/border are not rendered
    for loc in unchanged:
        props = ("backgroundColor", "backgroundImage") if loc in layers else             ("backgroundColor", "backgroundImage", "color", "borderTopColor")
        for prop in props:
            c.ok(4, f"{loc} {prop} unchanged from Light", dark[loc][prop] == light[loc][prop], dark[loc][prop][:80],
                 light[loc][prop][:80])
    c.gradient(4, "hero overlay", dark[P.HERO_SCRIM]["backgroundImage"], 90,
               [("rgba(29,29,27,0.9)", 16), ("rgba(145,23,49,0.9)", 84)])
    c.color(4, "hero text", dark[P.HERO_HEADLINE]["color"], "#FFFFFF")
    c.color(4, "search field", dark[P.HERO_SEARCH_FORM]["backgroundColor"], "#FFFFFF")
    ph = hub.placeholder_style(P.HERO_SEARCH_INPUT)
    c.color(4, "placeholder", ph["color"], "#7C7B7B")
    c.ok(4, "placeholder unchanged from Light", ph["color"] == light_ph["color"], ph["color"], light_ph["color"])
    c.color(4, "Search button", dark[P.HERO_SEARCH_BUTTON]["backgroundColor"], "#911731")
    c.color(4, "band heading", dark[P.SUB_HEADING]["color"], "#FFFFFF")
    c.color(4, "band description", dark[P.SUB_DESCRIPTION]["color"], "#F6F6F6")
    c.color(4, "band input", dark[P.SUB_INPUT]["backgroundColor"], "#FFFFFF")
    c.color(4, "Subscribe button background", dark[P.SUB_BUTTON]["backgroundColor"], "#FFFFFF")
    c.color(4, "Subscribe button label", dark[P.SUB_BUTTON]["color"], "#911731")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149348 — content feeds switch to the Dark-mode tokens (Figma 5461:198874)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149348
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149348_figma_dark_feeds(page):
    """MEDIA-MCHUB-TC-294."""
    hub = _hub(page)
    hub.enable_dark_theme()
    hub.scroll_into_view(P.NF)
    hub.save_evidence("tc149348_dark_feeds")
    c = Checks("TC 149348")
    for loc in (P.NF_EYEBROW, P.PF_EYEBROW, P.VF_EYEBROW):
        c.color(1, f"{loc} colour", hub.style(loc)["color"], "#C44561")
    for loc in (P.NF_HEADING, P.PF_HEADING, P.VF_HEADING):
        c.color(1, f"{loc} colour", hub.style(loc)["color"], "#FFFFFF")
    for loc in (P.NF_CTA_HEAD, P.PF_CTA_HEAD, P.VF_CTA_HEAD):
        st = hub.style(loc)
        c.color(2, f"{loc} background", st["backgroundColor"], "#1D1D1B")
        c.border(2, loc, st, 1, "#6C6C6B")
        c.radius(2, loc, st, 9999)
        c.color(2, f"{loc} label", st["color"], "#EDEDED")
    for ch in hub.styles_all(P.NF_LEAD_CHIP):
        c.color(3, f"lead chip '{ch['text']}' background", ch["backgroundColor"], "#343432")
        c.color(3, f"lead chip '{ch['text']}' text", ch["color"], "#DEDEDD")
    c.color(3, "lead title", hub.style(P.NF_LEAD_TITLE)["color"], "#F6F6F6")
    c.color(3, "excerpt", hub.style(P.NF_LEAD_EXCERPT)["color"], "#EDEDED")
    for it in hub.styles_all(P.NF_LEAD_META_ITEM):
        c.color(3, f"lead meta '{it['text']}'", it["color"], "#DEDEDD")
    c.color(3, "Read More", hub.style(P.NF_READ_MORE)["color"], "#C44561")
    for loc in (P.NF_CARD_TITLE, P.PF_CARD_TITLE, P.VF_CARD_TITLE):
        c.color(4, f"{loc} colour", hub.style(loc)["color"], "#FFFFFF")
    for loc in (P.PF_CATEGORY_CHIP, P.VF_CATEGORY_CHIP):
        st = hub.style(loc)
        c.color(4, f"{loc} background", st["backgroundColor"], "#343432")
        c.color(4, f"{loc} text", st["color"], "#DEDEDD")
    for loc in (P.NF_CARD_META_ITEM, P.PF_CARD_META_ITEM, P.VF_CARD_META_ITEM):
        c.color(4, f"{loc} colour", hub.style(loc)["color"], "#DEDEDD")
    for loc in (P.PF_BADGE, P.VF_DURATION):
        st = hub.style(loc)
        c.color(4, f"{loc} background", st["backgroundColor"], "rgba(29,29,27,0.7)")
        c.color(4, f"{loc} text", st["color"], "#FFFFFF")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149349 — AR hero and counts strip mirrored RTL with the Figma Arabic copy (5461:196214)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_130709
@pytest.mark.tc_149349
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149349_figma_ar_hero_counts(page):
    """MEDIA-MCHUB-TC-295."""
    hub = _hub(page, "ar")
    hub.save_evidence("tc149349_ar_desktop", full_page=False)
    c = Checks("TC 149349")
    doc = hub.document_state()
    c.eq(1, "dir", doc["dir"], "rtl")
    c.ok(1, "lang (primary subtag)", doc["lang"].lower().split("-")[0] == "ar", doc["lang"], "ar")
    for loc in (P.QA_HEADING, P.NF_HEADING, P.QA_EYEBROW, P.NF_EYEBROW):
        st = hub.style(loc)
        c.ok(1, f"{loc} right-aligned", _right_aligned(st), f"{st['textAlign']}/{st['direction']}", "right")
    label = hub.style(P.HERO_PAGE_LABEL)
    c.ok(1, "font remains Cairo", font_family_contains(label["fontFamily"], "Cairo") and hub.font_loaded("Cairo"),
         label["fontFamily"], "Cairo")
    crumbs, home, cur = hub.style(P.HERO_CRUMBS), hub.style(P.HERO_CRUMB_HOME_LABEL), hub.style(P.HERO_CRUMB_CURRENT)
    c.eq(2, "page label text", label["text"], "المركز الإعلامي")
    c.typo(2, "page label", label, 30, 38, None, "#FFFFFF")
    c.px(2, "page label on the right", label["box"]["right"], CONTENT_X + CONTENT_W)
    c.px(2, "breadcrumb on the left", crumbs["box"]["x"], CONTENT_X)
    c.eq(2, "breadcrumb text", [home["text"], cur["text"]], ["الرئيسية", "المركز الإعلامي"])
    c.ok(2, "breadcrumb reads right-to-left", home["box"]["x"] > cur["box"]["x"], (home["box"]["x"], cur["box"]["x"]), "Home right-most")
    c.eq(2, "separator chevron direction", hub.icon_direction(P.HERO_CRUMB_SEPARATOR_ICON), "left")
    c.gradient(2, "hero overlay (mirrored)", hub.style(P.HERO_SCRIM)["backgroundImage"], 90,
               [("rgba(145,23,49,0.9)", 16), ("rgba(29,29,27,0.9)", 84)])
    head = hub.style(P.HERO_HEADLINE)
    c.eq(3, "headline text", head["text"], "بوابتك إلى الأخبار الرسمية لغرفة قطر")
    c.typo(3, "headline", head, 30, 38, 700, "#FFFFFF")
    c.eq(3, "headline centred", head["textAlign"], "center")
    form, inp = hub.style(P.HERO_SEARCH_FORM), hub.style(P.HERO_SEARCH_INPUT)
    c.px(3, "search width", form["box"]["w"], 872)
    c.pad(3, "search (mirrored)", form, 10, 32, 10, 12)
    c.ok(3, "placeholder right-aligned", _right_aligned(inp), f"{inp['textAlign']}/{inp['direction']}", "right")
    c.color(3, "placeholder colour", hub.placeholder_style(P.HERO_SEARCH_INPUT)["color"], "#7C7B7B")
    btn, bico, blbl = hub.style(P.HERO_SEARCH_BUTTON), hub.style(P.HERO_SEARCH_BUTTON_ICON), hub.style(P.HERO_SEARCH_BUTTON_LABEL)
    c.eq(3, "button label", blbl["text"], "بحث")
    c.color(3, "button background", btn["backgroundColor"], "#911731")
    c.radius(3, "button", btn, 9999)
    c.ok(3, "button at the LEFT end of the field", btn["box"]["x"] < inp["box"]["x"], (btn["box"]["x"], inp["box"]["x"]), "left of input")
    c.ok(3, "search icon AFTER the label (left of it in RTL)", bico["box"]["right"] <= blbl["box"]["x"],
         {"icon_x": bico["box"]["x"], "label_x": blbl["box"]["x"]}, "icon left of label")
    tiles = hub.styles_all(P.COUNT_CARD)
    labels = [t["text"].split("\n")[0] for t in sorted(tiles, key=lambda t: -t["box"]["x"])]
    c.eq(4, "widgets read right-to-left", labels, WIDGET_LABELS_AR)
    for i, val in enumerate(hub.styles_all(P.COUNT_VALUE)):
        m = re.match(r"^([\d,٬٠-٩]+)\s+(\S.*)$", val["text"])
        c.ok(4, f"count line {i + 1}", m is not None and _is_arabic(m.group(2)), val["text"], "'<live count> <AR unit>'")
        c.typo(4, f"count line {i + 1}", val, 14, None, 400, "#7C7B7B")
    t0 = tiles[0]
    c.color(4, "tile background", t0["backgroundColor"], "#FFFFFF")
    c.border(4, "tile", t0, 1, "#EDEDED")
    c.radius(4, "tile", t0, 12)
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149351 — hero, counts strip and quick-access stack per the mobile Figma (5461:196278)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130709
@pytest.mark.tc_149351
@pytest.mark.parametrize("page", [MOBILE_390], indirect=True)
def test_tc_149351_figma_mobile_en(page):
    """MEDIA-MCHUB-TC-297."""
    hub = _hub(page)
    hub.save_evidence("tc149351_mobile_en")
    c = Checks("TC 149351")
    inner, top, label, crumbs = (hub.style(x) for x in (P.HERO_INNER, P.HERO_TOP, P.HERO_PAGE_LABEL, P.HERO_CRUMBS))
    c.pad(1, "hero", inner, 32, 20, 32, 20)
    c.px(1, "hero gap", inner["gap"], 32, 0.5)
    c.gradient(1, "hero overlay (vertical)", hub.style(P.HERO_SCRIM)["backgroundImage"], 180,
               [("rgba(145,23,49,0.9)", 22), ("rgba(29,29,27,0.9)", 93)])
    c.eq(1, "page label text", label["text"], "Media Center")
    c.typo(1, "page label", label, 20, 30, 700, "#FFFFFF")
    c.px(1, "page label centred", (label["box"]["x"] + label["box"]["w"] / 2) - 195, 0)
    c.px(1, "breadcrumb centred", (crumbs["box"]["x"] + crumbs["box"]["w"] / 2) - 195, 0)
    c.px(1, "breadcrumb 8px beneath the label", crumbs["box"]["y"] - label["box"]["bottom"], 8)
    c.typo(1, "headline", hub.style(P.HERO_HEADLINE), 20, 30, 700, "#FFFFFF")
    c.typo(1, "description", hub.style(P.HERO_DESCRIPTION), 14, 22, 400, "#FFFFFF")
    form, btn, blbl = hub.style(P.HERO_SEARCH_FORM), hub.style(P.HERO_SEARCH_BUTTON), hub.style(P.HERO_SEARCH_BUTTON_LABEL)
    c.px(2, "search full width", form["box"]["w"], 350)
    c.radius(2, "search", form, 9999)
    c.pad(2, "search", form, 6, 6, 6, 16)
    c.pad(2, "Search button", btn, 9, 14, 9, 14)
    c.typo(2, "Search label", blbl, 14, 22, 600, "#FFFFFF")
    c.color(2, "Search button", btn["backgroundColor"], "#911731")
    hero, shell, qa_shell = hub.style(P.HERO), hub.style(P.COUNTS_SHELL), hub.style(P.QA_SHELL)
    c.px(3, "body top padding", shell["box"]["y"] - hero["box"]["bottom"], 40)
    c.px(3, "body side padding", shell["box"]["x"], 20)
    c.px(3, "section gap", qa_shell["box"]["y"] - shell["box"]["bottom"], 20)
    c.pad(3, "strip", shell, 20, 20, 20, 20)
    c.radius(3, "strip", shell, 20)
    tiles = hub.styles_all(P.COUNT_CARD)
    c.eq(3, "widgets in ONE column", _columns(tiles), 1)
    for a, b in zip(tiles, tiles[1:]):
        c.px(3, "widget gap", b["box"]["y"] - a["box"]["bottom"], 12)
    t0, chip, lb, val = tiles[0], hub.style(P.COUNT_ICON_CHIP), hub.style(P.COUNT_LABEL), hub.style(P.COUNT_VALUE)
    c.ok(3, "widget is a horizontal row (chip left of text)", chip["box"]["right"] <= lb["box"]["x"], (chip["box"]["x"], lb["box"]["x"]), "row")
    c.size(3, "icon chip", chip, 40, 40, 0.5)
    c.radius(3, "icon chip", chip, 9999)
    c.color(3, "icon chip fill", chip["backgroundColor"], "#EDEDED")
    c.px(3, "chip-text gap", lb["box"]["x"] - chip["box"]["right"], 12)
    c.typo(3, "label", lb, 16, 24, 700, "#4A4A49")
    c.ok(3, "label left-aligned", _left_aligned(lb), lb["textAlign"], "left")
    c.ok(3, "count below label", val["box"]["y"] >= lb["box"]["bottom"] - 1, (lb["box"]["y"], val["box"]["y"]), "below")
    c.typo(3, "count", val, 14, 22, 400, "#6C6C6B")
    c.pad(3, "tile", t0, 16, 12, 16, 12)
    c.radius(3, "tile", t0, 12)
    c.color(3, "tile", t0["backgroundColor"], "#FFFFFF")
    c.border(3, "tile", t0, 1, "#EDEDED")
    hd, eb = hub.style(P.QA_HEADING), hub.style(P.QA_EYEBROW)
    c.ok(4, "header text stacked", hd["box"]["y"] >= eb["box"]["bottom"] - 1, (eb["box"]["y"], hd["box"]["y"]), "stacked")
    c.typo(4, "'Everything in one place'", hd, 24, 32, 700, "#1D1D1B")
    cards = hub.styles_all(P.QA_CARD)
    c.eq(4, "six cards in ONE column", (len(cards), _columns(cards)), (6, 1))
    for a, b in zip(cards, cards[1:]):
        c.px(4, "card gap", b["box"]["y"] - a["box"]["bottom"], 12)
    card, tile, title, desc, arrow = (hub.style(x) for x in (P.QA_CARD, P.QA_ICON_TILE, P.QA_TITLE, P.QA_CARD_DESCRIPTION, P.QA_ARROW))
    c.pad(4, "card", card, 16, 16, 16, 16)
    c.radius(4, "card", card, 16)
    c.size(4, "icon tile", tile, 48, 48, 0.5)
    c.color(4, "icon tile", tile["backgroundColor"], "#911731")
    c.typo(4, "card title", title, 16, 24, 700, "#343432")
    c.typo(4, "card description", desc, 12, 18, 400, "#7C7B7B")
    c.ok(4, "arrow at the right end", arrow["box"]["x"] > title["box"]["x"] and hub.icon_direction(P.QA_ARROW) == "right",
         arrow["box"], "right end, pointing right")
    doc = hub.document_state()
    c.ok(5, "no horizontal page scroll", doc["scroll_width"] <= doc["client_width"], doc["scroll_width"], f"<= {doc['client_width']}")
    clipped = hub.clipped_or_offscreen_text()
    c.ok(5, "nothing clipped or overflowing", not clipped, clipped, "[]")
    c.done()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.title("TC 149353 — mobile layout mirrored RTL with the Figma Arabic copy (5461:196344)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_130709
@pytest.mark.tc_149353
@pytest.mark.parametrize("page", [MOBILE_390], indirect=True)
def test_tc_149353_figma_mobile_ar(page):
    """MEDIA-MCHUB-TC-299."""
    hub = _hub(page, "ar")
    hub.save_evidence("tc149353_mobile_ar")
    c = Checks("TC 149353")
    doc = hub.document_state()
    c.eq(1, "dir", doc["dir"], "rtl")
    label, crumbs, head = hub.style(P.HERO_PAGE_LABEL), hub.style(P.HERO_CRUMBS), hub.style(P.HERO_HEADLINE)
    c.eq(1, "page label text", label["text"], "المركز الإعلامي")
    c.typo(1, "page label", label, 20, 30, 700)
    c.px(1, "page label centred", (label["box"]["x"] + label["box"]["w"] / 2) - 195, 0)
    c.ok(1, "breadcrumb centred beneath", crumbs["box"]["y"] >= label["box"]["bottom"] - 1
         and abs((crumbs["box"]["x"] + crumbs["box"]["w"] / 2) - 195) <= 2, crumbs["box"], "centred, below label")
    c.eq(1, "headline text", head["text"], "بوابتك إلى الأخبار الرسمية لغرفة قطر")
    c.typo(1, "headline", head, 20, 30, 700)
    form, btn, inp = hub.style(P.HERO_SEARCH_FORM), hub.style(P.HERO_SEARCH_BUTTON), hub.style(P.HERO_SEARCH_INPUT)
    c.pad(1, "search (mirrored)", form, 6, 16, 6, 6)
    c.eq(1, "button label", hub.texts(P.HERO_SEARCH_BUTTON_LABEL)[0], "بحث")
    c.ok(1, "'بحث' at the LEFT end", btn["box"]["x"] < inp["box"]["x"], (btn["box"]["x"], inp["box"]["x"]), "left of input")
    tiles = hub.styles_all(P.COUNT_CARD)
    c.eq(2, "widgets one column", _columns(tiles), 1)
    chip, lb = hub.style(P.COUNT_ICON_CHIP), hub.style(P.COUNT_LABEL)
    c.ok(2, "icon chip on the RIGHT", chip["box"]["x"] > lb["box"]["x"], (chip["box"]["x"], lb["box"]["x"]), "chip right of label")
    for i, l in enumerate(hub.styles_all(P.COUNT_LABEL)):
        c.typo(2, f"widget label '{l['text']}'", l, 16, None, 700, "#4A4A49")
        c.ok(2, f"widget label '{l['text']}' right-aligned", _right_aligned(l), f"{l['textAlign']}/{l['direction']}", "right")
    cards = hub.styles_all(P.QA_CARD)
    c.eq(2, "quick-access one column", _columns(cards), 1)
    tile, title = hub.style(P.QA_ICON_TILE), hub.style(P.QA_TITLE)
    c.ok(2, "icon tile on the RIGHT", tile["box"]["x"] > title["box"]["x"], (tile["box"]["x"], title["box"]["x"]), "tile right of title")
    c.color(2, "icon tile", tile["backgroundColor"], "#911731")
    c.typo(2, "card title", title, 16, 24, 700, "#343432")
    c.ok(2, "card title right-aligned", _right_aligned(title), f"{title['textAlign']}/{title['direction']}", "right")
    qh = hub.style(P.QA_HEADING)
    c.eq(2, "'كل شيء في مكان واحد' text", qh["text"], "كل شيء في مكان واحد")
    c.typo(2, "'كل شيء في مكان واحد'", qh, 20, 30, 700, "#1D1D1B")
    nh, lt, more = hub.style(P.NF_HEADING), hub.style(P.NF_LEAD_TITLE), hub.style(P.NF_READ_MORE)
    c.eq(3, "news heading text", nh["text"], "الأخبار والبيانات الصحفية")
    c.typo(3, "news heading", nh, 20, 30, 700)
    c.typo(3, "lead title", lt, 18, 28, 700)
    c.ok(3, "lead title right-aligned", _right_aligned(lt), f"{lt['textAlign']}/{lt['direction']}", "right")
    c.eq(3, "'اقرأ المزيد' text", more["text"], "اقرأ المزيد")
    c.color(3, "'اقرأ المزيد' colour", more["color"], "#911731")
    c.eq(3, "'اقرأ المزيد' arrow points left", hub.icon_direction(P.NF_READ_MORE_ICON_SVG), "left")
    for i, ct in enumerate(hub.styles_all(P.NF_CARD_TITLE)):
        c.typo(3, f"news card title {i + 1}", ct, 16, 24, 700)
        c.ok(3, f"news card title {i + 1} right-aligned", _right_aligned(ct), f"{ct['textAlign']}/{ct['direction']}", "right")
    c.ok(4, "no horizontal page scroll in RTL", doc["scroll_width"] <= doc["client_width"], doc["scroll_width"], f"<= {doc['client_width']}")
    clipped = hub.clipped_or_offscreen_text()
    c.ok(4, "nothing clipped", not clipped, clipped, "[]")
    c.done()

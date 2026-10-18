"""
web/tests/home_hero_banner/test_home_hero_banner_web.py — Hero Banner
(PBI 129367 / QC-HOME-001), Web platform, suite 134447.

Scripted 2026-10-18 on the QA lead's request to run every Web case. All reads
are on the public site in a LOGGED-OUT context (`page` param {"auth": False});
nothing is written to qcdev. Selectors come from the live re-read of the same
day (web/pages/home_hero_banner/home_hero_banner_page.py, "RE-READ" note).

Disclosed adaptations (the cases' Description data is example data; the live
real slides are asserted instead):
  - Titles / labels / link targets are the LIVE configured values, read off
    the page, not the cases' sample strings ("Qatar Chamber Welcomes You",
    "/our-services", "24/7 Support").
  - Slide counts: the cases assume 2-3 slides; qcdev has 9 published. Loop and
    navigation checks are done over the real count.
  - Figma has no linked frame for this PBI in the repo, so "per Figma" styling
    is asserted as the case words it (white / bold / maroon pill / left
    aligned / semi-transparent), not as pixel tokens.
  - 135101 blocks the slide image in THIS browser only (route abort); no data
    is touched.
Not scripted here (need real slides unpublished, or a state the CMS form
cannot produce) — reported to the QA lead: 135099 (one active slide),
135102 (zero slides), 135100 (Button 2 Link empty: the form requires it).
"""

import re
import time

import allure
import pytest

from web.pages.home_hero_banner.home_hero_banner_page import (
    ACTIVE_CTA_PRIMARY,
    ACTIVE_CTA_SECONDARY,
    ACTIVE_DOT,
    ACTIVE_PANEL,
    ACTIVE_SUBTITLE,
    ACTIVE_TITLE,
    ARROW_NEXT,
    ARROW_PREV,
    DOT,
    HERO_SECTION,
    SCRIM,
    HomeHeroBannerPage,
)

pytestmark = [pytest.mark.web, pytest.mark.pbi_129367]

ANON = {"auth": False}
DESKTOP = {"auth": False, "viewport": (1920, 1080)}
TABLET = {"auth": False, "viewport": (768, 1024)}
MOBILE = {"auth": False, "viewport": (375, 667)}
IMG_TOL = 5  # bug-rules Rule 1: images ±5 px
LAYOUT_TOL = 2  # layout ±2 px


def _alpha(css_color: str) -> float:
    m = re.match(r"rgba?\(([^)]+)\)", css_color or "")
    if not m:
        return 1.0
    parts = [p.strip() for p in m.group(1).split(",")]
    return float(parts[3]) if len(parts) == 4 else 1.0


def _overlap(a: dict, b: dict) -> bool:
    return not (a["right"] <= b["x"] + LAYOUT_TOL or b["right"] <= a["x"] + LAYOUT_TOL
                or a["bottom"] <= b["y"] + LAYOUT_TOL or b["bottom"] <= a["y"] + LAYOUT_TOL)


def _settled_counters(hero: HomeHeroBannerPage, timeout: float = 15) -> list:
    """The counter values once the count-up animation stops changing."""
    end = time.time() + timeout
    last = hero.counter_values()
    while time.time() < end:
        hero.page.wait_for_timeout(1000)
        now = hero.counter_values()
        if now == last:
            return now
        last = now
    return last


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------
@allure.title("Hero background image renders full-width below the header")
@pytest.mark.ui
@pytest.mark.tc_134988
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_hero_background_image_below_header(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    section, img = hero.box(HERO_SECTION), hero.box("li.qc-hero-slide-active img")
    vw = hero.viewport_width()
    assert section["y"] >= hero.header_bottom() - LAYOUT_TOL, "the hero starts above the header's bottom edge"
    assert hero.active_image_loaded(), "the active slide's background image did not load (broken image)"
    assert abs(img["w"] - vw) <= IMG_TOL, f"background image is {img['w']} px wide, viewport {vw} px (not full-width)"
    scrim = hero.box(SCRIM)
    assert scrim["bgImage"] != "none" or _alpha(scrim["bg"]) > 0, \
        f"no dark overlay on the image (scrim bg {scrim['bg']}, image {scrim['bgImage']})"


@allure.title("Headline renders large, bold, white and left-aligned, at most 3 lines")
@pytest.mark.ui
@pytest.mark.tc_134989
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_headline_position_and_style(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    t = hero.box(ACTIVE_TITLE)
    assert t["text"], "the active slide shows no headline"
    assert t["fw"] >= 700, f"headline weight {t['fw']}, not bold"
    assert t["color"] == "rgb(255, 255, 255)", f"headline colour {t['color']}, not white"
    assert t["ta"] in ("start", "left") and t["dir"] == "ltr", f"headline align {t['ta']} / dir {t['dir']}"
    assert t["x"] < hero.viewport_width() / 2, f"headline starts at x={t['x']}, not on the left"
    lines = round(t["h"] / t["lh"])
    assert lines <= 3, f"headline wraps to {lines} lines (max 3)"


@allure.title("Subtitle renders below the headline in smaller text, at most 4 lines")
@pytest.mark.ui
@pytest.mark.tc_134990
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_subtitle_below_headline(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    t, s = hero.box(ACTIVE_TITLE), hero.box(ACTIVE_SUBTITLE)
    allure.attach(f"subtitle colour {s['color']}, size {s['fs']} px", name="subtitle style",
                  attachment_type=allure.attachment_type.TEXT)
    assert s["text"], "the active slide shows no subtitle"
    assert s["y"] >= t["bottom"] - LAYOUT_TOL, f"subtitle top {s['y']} is not below the headline bottom {t['bottom']}"
    assert s["fs"] < t["fs"], f"subtitle {s['fs']} px is not smaller than the headline {t['fs']} px"
    lines = round(s["h"] / s["lh"])
    assert lines <= 4, f"subtitle wraps to {lines} lines (max 4)"


@allure.title("Achievement Counters render in a row with icon above a number that settles, and a label")
@pytest.mark.ui
@pytest.mark.tc_134991
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_achievement_counters_row(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    page.locator(f"{ACTIVE_PANEL} .qc-hero-counters").first.scroll_into_view_if_needed()
    values = _settled_counters(hero)
    boxes = hero.counter_boxes()
    icons = hero.counter_icon_boxes()
    labels = [b["text"] for b in boxes]
    allure.attach(f"values {values} | labels {labels}", name="counters", attachment_type=allure.attachment_type.TEXT)
    assert len(boxes) >= 3, f"{len(boxes)} counters rendered, expected 3"
    assert max(b["y"] for b in boxes) - min(b["y"] for b in boxes) <= LAYOUT_TOL, "counters are not in one row"
    assert all(i and i["loaded"] for i in icons), f"a counter icon is missing or broken: {icons}"
    assert all(i["icon_bottom"] <= i["value_top"] + LAYOUT_TOL for i in icons), "an icon is not above its number"
    assert all(v and not re.fullmatch(r"0\D*", v) for v in values), f"counter numbers did not settle: {values}"


@allure.title("Slide dots render with an elongated active pill that advances with auto-play")
@pytest.mark.ui
@pytest.mark.tc_134992
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_dot_pill_indicator(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    dots = hero.boxes(DOT)
    active = hero.box(ACTIVE_DOT)
    others = [d for d in dots if abs(d["x"] - active["x"]) > 1]
    img = hero.box(HERO_SECTION)
    assert len(dots) == hero.slide_count() >= 2, "no dot row"
    assert active["w"] > max(d["w"] for d in others), f"active dot {active['w']} px is not elongated"
    assert active["x"] < hero.viewport_width() / 2 and img["y"] < active["y"] < img["bottom"], \
        "the indicator is not at the bottom-left of the image"
    fill = hero.pseudo(ACTIVE_DOT, "::after")
    fill_b = hero.pseudo(ACTIVE_DOT, "::before")
    allure.attach(f"::after {fill} | ::before {fill_b} | dot {active}", name="pill fill styles",
                  attachment_type=allure.attachment_type.TEXT)
    start = hero.active_index()
    page.wait_for_timeout(hero.autoplay_interval_ms() + 1500)
    assert hero.active_index() == start % hero.slide_count() + 1, "the indicator did not move to the next dot"
    own = page.locator(ACTIVE_DOT).first.evaluate(
        "e => { const c = getComputedStyle(e); return {animation: c.animationName, transition: c.transitionDuration}; }")
    animated = any(x["animation"] not in ("none", "", None) or x["transition"] not in ("0s", "", None)
                   for x in (fill, fill_b, own))
    assert animated, f"the active pill has no fill animation/transition (dot {own}, ::after {fill}, ::before {fill_b})"


@allure.title("Next / previous arrows render semi-transparent, vertically centred, with a hover state")
@pytest.mark.ui
@pytest.mark.tc_134993
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_arrows_render_with_hover(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    sec, nxt, prv = hero.box(HERO_SECTION), hero.box(ARROW_NEXT), hero.box(ARROW_PREV)
    centre = sec["y"] + sec["h"] / 2
    for name, a in (("next", nxt), ("previous", prv)):
        assert a["visibility"] == "visible" and a["w"] > 0, f"{name} arrow not visible"
        assert 0 < _alpha(a["bg"]) < 1, f"{name} arrow background {a['bg']} is not semi-transparent"
        assert abs((a["y"] + a["h"] / 2) - centre) <= LAYOUT_TOL, f"{name} arrow is not vertically centred"
    before = nxt["bg"]
    page.hover(ARROW_NEXT)
    page.wait_for_timeout(500)
    after = hero.box(ARROW_NEXT)
    assert (after["bg"], after["opacity"]) != (before, nxt["opacity"]), "no visible hover state on the next arrow"


@allure.title("Primary CTA renders as a solid maroon pill with a white bold label and an arrow icon")
@pytest.mark.ui
@pytest.mark.tc_134994
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_cta_maroon_pill(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    b = hero.box(ACTIVE_CTA_PRIMARY)
    after = hero.pseudo(ACTIVE_CTA_PRIMARY, "::after")
    icon = hero.has_inline_icon(ACTIVE_CTA_PRIMARY) or after["content"] not in ("none", "normal", '""') \
        or after["bgImage"] != "none" or (after["maskImage"] or "none") != "none"
    allure.attach(f"{b} | ::after {after}", name="cta styles", attachment_type=allure.attachment_type.TEXT)
    assert b["text"], "the primary CTA has no label"
    assert b["bg"] == "rgb(145, 23, 49)", f"CTA background {b['bg']} is not the maroon brand colour"
    assert float(b["radius"].rstrip("px") or 0) >= b["h"] / 2 - LAYOUT_TOL, f"CTA radius {b['radius']} is not a pill"
    assert b["color"] == "rgb(255, 255, 255)" and b["fw"] >= 600, f"label {b['color']} / weight {b['fw']}"
    assert icon, "no arrow icon on the CTA"


@allure.title("Home Page hero mirrors for Arabic (RTL)")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_134997
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_hero_rtl_mirroring(page):
    hero = HomeHeroBannerPage(page).open_home_locale("ar")
    vw = hero.viewport_width() / 2
    assert page.evaluate("() => document.documentElement.dir") == "rtl", "the page is not RTL"
    logo, t, s = hero.header_logo_box(), hero.box(ACTIVE_TITLE), hero.box(ACTIVE_SUBTITLE)
    dot, nxt, prv = hero.box(ACTIVE_DOT), hero.box(ARROW_NEXT), hero.box(ARROW_PREV)
    cta = hero.box(ACTIVE_CTA_PRIMARY)
    checks = {
        "logo on the right": logo["x"] > vw,
        "headline RTL on the right": t["dir"] == "rtl" and t["right"] > vw,
        "subtitle RTL": s["dir"] == "rtl",
        "CTA RTL": cta["dir"] == "rtl",
        "indicator bottom-right": dot["x"] > vw,
        "previous arrow mirrored to the right": prv["x"] > vw,
        "next arrow mirrored to the left": nxt["x"] < vw,
    }
    assert all(checks.values()), f"not mirrored: {[k for k, v in checks.items() if not v]}"


@pytest.mark.ui
@pytest.mark.parametrize("page,tc", [
    pytest.param(DESKTOP, 134998, id="134998-desktop", marks=pytest.mark.tc_134998),
    pytest.param(TABLET, 134999, id="134999-tablet", marks=pytest.mark.tc_134999),
], indirect=["page"])
@allure.title("Hero and counters render without overlap or horizontal scroll at the viewport")
def test_hero_viewport(page, tc):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    vw = hero.viewport_width()
    sec = hero.box(HERO_SECTION)
    _settled_counters(hero)
    boxes = hero.counter_boxes()
    assert abs(sec["w"] - vw) <= IMG_TOL, f"hero is {sec['w']} px wide at a {vw} px viewport"
    assert not hero.has_horizontal_scroll(), "the page scrolls horizontally"
    assert all(b["x"] >= -LAYOUT_TOL and b["right"] <= vw + LAYOUT_TOL for b in boxes), "a counter is off-screen"
    assert not any(_overlap(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:]), "counters overlap"
    if tc == 134998:
        assert max(b["y"] for b in boxes) - min(b["y"] for b in boxes) <= LAYOUT_TOL, "counters not in one row"
    else:
        assert all(b["fs"] >= 12 for b in boxes), "counter text below 12 px (not readable)"


@allure.title("At 375 px the counters render below the hero content, in a row of 3, unclipped")
@pytest.mark.ui
@pytest.mark.tc_135000
@pytest.mark.parametrize("page", [MOBILE], indirect=True)
def test_counters_mobile(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    _settled_counters(hero)
    boxes, cta, vw = hero.counter_boxes(), hero.box(ACTIVE_CTA_PRIMARY), hero.viewport_width()
    allure.attach(str([(round(b["x"]), round(b["y"]), round(b["w"])) for b in boxes]), name="counter boxes",
                  attachment_type=allure.attachment_type.TEXT)
    assert not hero.has_horizontal_scroll(), "the page scrolls horizontally"
    assert all(b["y"] >= cta["y"] for b in boxes), "a counter renders above the hero content"
    assert all(b["x"] >= -LAYOUT_TOL and b["right"] <= vw + LAYOUT_TOL for b in boxes), "a counter is clipped"
    assert len(boxes) == 3 and max(b["y"] for b in boxes) - min(b["y"] for b in boxes) <= LAYOUT_TOL, \
        "the 3 counters are not in one row (they stack)"


@allure.title("A logged-out visitor sees the hero and counters without a login prompt")
@pytest.mark.auth
@pytest.mark.tc_135001
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_anonymous_visitor_sees_hero(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    assert hero.active_title(), "no hero headline for a visitor"
    assert hero.counter_boxes(), "no counters for a visitor"
    assert page.locator("#_com_liferay_login_web_portlet_LoginPortlet_login:visible").count() == 0, \
        "a login prompt is shown"


# ---------------------------------------------------------------------------
# navigation
# ---------------------------------------------------------------------------
@allure.title("Next arrow cycles through every slide and loops back to the first")
@pytest.mark.functional_low
@pytest.mark.tc_135004
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_next_loops_to_first(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    n, seen = hero.slide_count(), []
    page.locator(HERO_SECTION).hover()  # keep auto-play from moving the slide under the clicks
    for _ in range(n):
        hero.click(ARROW_NEXT)
        page.wait_for_timeout(500)
        seen.append((hero.active_index(), bool(hero.active_title())))
    assert all(ok for _, ok in seen), f"a blank slide appeared: {seen}"
    assert seen[-1][0] == 1, f"after {n} clicks the slider is on slide {seen[-1][0]}, not slide 1: {seen}"


@allure.title("Previous arrow returns to the previous slide")
@pytest.mark.functional_high
@pytest.mark.tc_135005
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_prev_goes_back(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    page.locator(HERO_SECTION).hover()
    hero.click(ARROW_NEXT)
    page.wait_for_timeout(500)
    on = hero.active_index()
    hero.click(ARROW_PREV)
    page.wait_for_timeout(500)
    assert hero.active_index() == on - 1, f"previous from slide {on} landed on {hero.active_index()}"


@allure.title("Previous arrow from the first slide loops backward to the last")
@pytest.mark.functional_low
@pytest.mark.tc_135006
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_prev_loops_to_last(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    n = hero.slide_count()
    page.locator(HERO_SECTION).hover()
    assert hero.active_index() == 1, "the slider did not start on slide 1"
    hero.click(ARROW_PREV)
    page.wait_for_timeout(500)
    assert hero.active_index() == n, f"previous from slide 1 landed on {hero.active_index()}, not slide {n}"
    assert hero.active_title(), "the last slide is blank"


@pytest.mark.functional_high
@pytest.mark.parametrize("page,which", [
    pytest.param(DESKTOP, "primary", id="135007-button1", marks=pytest.mark.tc_135007),
    pytest.param(DESKTOP, "secondary", id="135008-button2", marks=pytest.mark.tc_135008),
], indirect=["page"])
@allure.title("Clicking a slide CTA navigates to its configured target")
def test_cta_navigates(page, which):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    page.locator(HERO_SECTION).hover()
    sel = ACTIVE_CTA_PRIMARY if which == "primary" else ACTIVE_CTA_SECONDARY
    href = page.locator(sel).first.get_attribute("href") or ""
    assert href, f"the {which} CTA has no target"
    with page.expect_navigation(timeout=30000):
        page.locator(sel).first.click()
    target = re.sub(r"^/(en|ar)(?=/)", "", href).rstrip("/")
    assert page.url.split("?")[0].rstrip("/").endswith(target), f"landed on {page.url}, configured {href}"
    # The case asserts navigation to the CONFIGURED target. Whether that page
    # exists is content (PBI running rules #17), so a 404 is noted, not failed.
    if "404" in page.title() or page.locator("text=/page not found/i").count():
        allure.attach(f"configured target {href} renders 'Page Not Found' ({page.url})",
                      name="content note: target is a 404", attachment_type=allure.attachment_type.TEXT)
        page.screenshot(path=f"reports/manual-exec-129367-{which}-cta-target-404.png")


@allure.title("Auto-play advances to the next slide without interaction")
@pytest.mark.functional_high
@pytest.mark.tc_135011
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_autoplay_advances(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    page.mouse.move(0, 0)
    start = hero.active_index()
    page.wait_for_timeout(hero.autoplay_interval_ms() + 1500)
    assert hero.active_index() == start % hero.slide_count() + 1, "auto-play did not advance the slider"


@allure.title("Next arrow advances to the next slide at once")
@pytest.mark.functional_high
@pytest.mark.tc_135012
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_next_advances(page):
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    page.locator(HERO_SECTION).hover()
    start = hero.active_index()
    hero.click(ARROW_NEXT)
    page.wait_for_timeout(500)
    assert hero.active_index() == start + 1, f"next from slide {start} landed on {hero.active_index()}"


@allure.title("With exactly one active slide the hero is static: no auto-play, arrows or dots")
@pytest.mark.edge
@pytest.mark.tc_135099
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_single_slide_static(page):
    """Precondition (QA lead approval 2026-10-18): every real slide except
    QCDEMO-129367-HERO_BANNER_SLIDE-01 is unpublished by the wrapper
    .claude/qa-runs/phase3-20261015/run_135099.py, which re-publishes them in
    its own `finally`. This test only reads the public page."""
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    end = time.time() + 180  # QA lead: up to 3 minutes for a change to reach visitors
    while page.locator(".qc-hero-panel").count() != 1 and time.time() < end:
        page.wait_for_timeout(5000)
        hero.open_home_locale("en")
    panels = page.locator(".qc-hero-panel").count()
    assert panels == 1, f"precondition: {panels} slides are live, not exactly 1"
    first = hero.active_title()
    page.wait_for_timeout((hero.autoplay_interval_ms() or 6000) + 1500)
    assert page.locator(".qc-hero-panel").count() == 1 and hero.active_title() == first, "the single slide changed"
    visible = lambda sel: page.locator(f"{sel}:visible").count()  # noqa: E731
    assert visible(ARROW_NEXT) == 0 and visible(ARROW_PREV) == 0, "arrows still render for a single slide"
    assert visible(DOT) == 0, "the dot/pill indicator still renders for a single slide"


@allure.title("A failed background image shows a fallback colour, not a broken image")
@pytest.mark.edge
@pytest.mark.tc_135101
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_image_failure_fallback(page):
    """The slide images are blocked in this browser only (route abort)."""
    page.route(re.compile(r".*/documents/.*qc-hero.*"), lambda r: r.abort())
    page.route(re.compile(r".*/documents/37246/0/.*\.(png|jpe?g|webp)(\?.*)?$"), lambda r: r.abort())
    hero = HomeHeroBannerPage(page).open_home_locale("en")
    state = page.evaluate("""() => { const li = document.querySelector('li.qc-hero-slide-active');
        const img = li && li.querySelector('img'); const chain = [];
        for (let e = img; e && e !== document.body; e = e.parentElement) chain.push(getComputedStyle(e).backgroundColor);
        return {loaded: img ? img.complete && img.naturalWidth > 0 : null, alt: img && img.getAttribute('alt'),
                imgVisible: img ? getComputedStyle(img).visibility !== 'hidden' && getComputedStyle(img).display !== 'none' : false,
                chain}; }""")
    page.screenshot(path="reports/manual-exec-129367-135101-image-blocked.png")
    allure.attach(str(state), name="fallback state", attachment_type=allure.attachment_type.TEXT)
    assert state["loaded"] is False, "the image still loaded; the block did not apply"
    fallback = next((c for c in state["chain"] if _alpha(c) > 0), None)
    assert fallback, f"no fallback background colour behind the failed image: {state['chain']}"
    assert not state["imgVisible"] or state["alt"] == "", "a broken-image icon can show (visible img with alt text)"
    assert hero.box(ACTIVE_TITLE)["text"] and hero.box(ACTIVE_CTA_PRIMARY)["text"], "headline / CTA not readable"

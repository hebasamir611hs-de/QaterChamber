"""
web/tests/home_dynamic_widgets/test_home_dynamic_widgets_web.py — PBI 129384
(QC-HOME-008 Dynamic Widgets: Weather, Marhaba Guide, B2B), Web cases of
suite 134455. Cases that need a CMS write live in the Control_Panel module.

REWRITTEN 2026-10-08 (Phase 3):
  - Every test runs as a logged-out visitor (`{"auth": False}`).
  - Cards are identified by their record's external reference code (in the
    image src), never by index: `QCDEMO-129384-directory` is the Marhaba
    Guide card (its image is the "Commercial & Industrial Directory"
    artwork), `QCDEMO-129384-b2b-verified` the B2B Platform card.
  - Geometry is compared to the Figma desktop frame (849:15904, 1920 wide,
    `.claude/qa-runs/129384.figma.json`: widgets row 1320 x 362, gap 24,
    cards 424 x 362, padding 24/20, gap 16, radius 16) at a 1920 viewport,
    with bug-rules Rule 1 tolerances: ±5 px images, ±2 px layout.
  - Weather DATA cases (30°C, "Light Rain", 30°/24°, 27%, 6.25 km/h, Mon-Fri)
    feed the case's own values through the real API response (route-patched)
    so the rendering of exactly those values is asserted, instead of the
    live weather that changes run to run.
  - The Marhaba/B2B cards are, per the PBI ("shall display the configured
    image and URL"), one configured image each; the copy/graphics the UI
    cases list are inside that image. Those cases assert the configured
    image renders and attach it; the copy itself is checked visually
    (manual execution, report §3).
"""

from __future__ import annotations

import json
import re
import time

import allure
import pytest

from config.settings import web_url
from web.pages.home_dynamic_widgets.home_dynamic_widgets_page import HomeDynamicWidgetsPage
from web.tests.home_dynamic_widgets import weather_mock as wm

pytestmark = [pytest.mark.web, pytest.mark.global_, pytest.mark.pbi_129384]

MARHABA = "QCDEMO-129384-directory"
B2B = "QCDEMO-129384-b2b-verified"
FIGMA = {"row_w": 1320, "card_w": 424, "card_h": 362, "gap": 24, "pad_v": 24, "pad_h": 20, "inner_gap": 16,
         "radius": 16, "bg": "rgb(145, 23, 49)"}
LAYOUT_TOL, IMAGE_TOL = 2, 5
ANON = {"auth": False}
PUBLIC_GROUP = pytest.mark.xdist_group("dynamic_widgets_public_row")
ANON_1920 = {"auth": False, "viewport": (1920, 1080)}
FALLBACK_EN = "Weather data unavailable."
FALLBACK_AR = "بيانات الطقس غير متاحة حالياً."


def tc(*ids, viewport=None, engine=None):
    param = {"auth": False}
    if viewport:
        param["viewport"] = viewport
    if engine:
        param["engine"] = engine

    def deco(fn):
        for i in ids:
            fn = getattr(pytest.mark, f"tc_{i}")(fn)
        fn = allure.label("testcase", ",".join(map(str, ids)))(fn)
        fn = allure.label("pbi", "129384")(fn)
        fn = allure.feature("Dynamic Widgets")(fn)
        return pytest.mark.parametrize("page", [param], indirect=True)(fn)
    return deco


def px(v: str) -> float:
    return float(str(v).replace("px", "").split()[0])


def home(page, locale="en") -> HomeDynamicWidgetsPage:
    dw = HomeDynamicWidgetsPage(page)
    dw.open_home_locale(locale)
    dw.scroll_to_section()
    return dw


# ---------------------------------------------------------------------------
# Weather widget — static copy / structure (live API)
# ---------------------------------------------------------------------------
@tc(135921)
def test_weather_title_135921(page):
    dw = home(page)
    assert dw.is_section_visible()
    assert dw.widget_title_text() == "Weather"


@tc(135922)
def test_weather_city_doha_bold_135922(page):
    dw = home(page)
    assert dw.city_text() == "Doha"
    assert int(dw.city_style()["fontWeight"]) >= 700


@tc(135937)
def test_weather_renders_ltr_english_135937(page):
    dw = home(page)
    assert dw.page_direction() == "ltr" and dw.page_lang().startswith("en")
    assert dw.widget_title_text() == "Weather" and dw.city_text() == "Doha"
    assert dw.weather_widget_style()["direction"] == "ltr"


@tc(135936)
def test_weather_renders_rtl_arabic_135936(page):
    dw = home(page, "ar")
    assert dw.page_direction() == "rtl"
    assert dw.widget_title_text() == "الطقس" and dw.city_text() == "الدوحة"
    assert dw.weather_widget_style()["direction"] == "rtl"
    days = dw.forecast_days()
    assert days and all(re.search(r"[؀-ۿ]", d["abbr"] or "") for d in days), days
    assert re.search(r"[؀-ۿ]", dw.condition_text()), dw.condition_text()
    items = dw.row_items()
    weather = next(i for i in items if i["kind"] == "weather")
    assert weather["x"] == max(i["x"] for i in items), "Weather card is not mirrored to the right in RTL"


@tc(135934)
def test_each_forecast_day_has_name_icon_temperature_135934(page):
    dw = home(page)
    days = dw.forecast_days()
    assert days, "no forecast days rendered"
    for d in days:
        assert d["abbr"] and d["hasIcon"] and re.search(r"\d", d["temp"] or ""), d


@tc(135959)
def test_weather_shows_live_api_values_135959(page):
    """The values on the card are the ones the Weather API returned on this load."""
    dw = HomeDynamicWidgetsPage(page)
    captured = {}
    page.on("response", lambda r: captured.setdefault("body", r.text()) if "/o/qc-weather/" in r.url and r.ok else None)
    dw.open_home()
    payload = json.loads(captured["body"])
    allure.attach(captured["body"], name="weather API response", attachment_type=allure.attachment_type.JSON)
    exp = wm.displayed_values(payload)
    assert dw.city_text() == "Doha"
    assert re.sub(r"\D", "", dw.temp_text()) == str(exp["temp"]), (dw.temp_text(), exp)
    assert dw.condition_text().strip().lower() == exp["condition"].lower(), (dw.condition_text(), exp)


# ---------------------------------------------------------------------------
# Weather widget — the case's own values, fed through the real API response
# ---------------------------------------------------------------------------
def mocked_home(page, locale="en", **values) -> HomeDynamicWidgetsPage:
    dw = HomeDynamicWidgetsPage(page)
    dw.route_weather(wm.patch_handler(**values))
    dw.open_home_locale(locale)
    return dw


@tc(135923)
def test_weather_temperature_30_large_numeral_135923(page):
    dw = mocked_home(page, temp=30)
    t = dw.temp_text()
    assert re.fullmatch(r"30\s*(℃|°C)", t), t
    st = dw.temp_style()
    assert int(st["fontWeight"]) >= 700 and px(st["fontSize"]) > px(dw.city_style()["fontSize"]), st


@tc(135924)
def test_weather_condition_light_rain_135924(page):
    dw = mocked_home(page, condition="Light Rain")
    assert dw.condition_text().strip() == "Light Rain"


@tc(135925)
def test_weather_icon_matches_condition_135925(page):
    clear = mocked_home(page, condition="Clear Sky").page.locator(HomeDynamicWidgetsPage.WEATHER_ICON).inner_html()
    page.unroute(wm.URL_PATTERN)
    rain = mocked_home(page, condition="Light Rain").page.locator(HomeDynamicWidgetsPage.WEATHER_ICON).inner_html()
    allure.attach(rain, name="Light Rain icon")
    assert "<svg" in rain and rain != clear, "icon does not change with the condition"
    assert wm.icon_kind(rain) == "cloud-sun", f"Light Rain icon is {wm.icon_kind(rain)!r}; the case expects cloud+sun"


@tc(135926)
def test_weather_high_low_row_135926(page):
    dw = mocked_home(page, high=30, low=24)
    t = dw.highlow_text()
    allure.attach(t, name="rendered high/low (spacing noted, not asserted)")
    assert re.sub(r"\s+", "", t) == "30°-24°", f"high/low reads {t!r}, case expects '30°-24°'"


@tc(135927)
def test_weather_humidity_27_135927(page):
    dw = mocked_home(page, humidity=27)
    assert dw.humidity_text().strip().endswith("27%"), dw.humidity_text()


@tc(135928)
def test_weather_wind_6_25_135928(page):
    dw = mocked_home(page, wind=6.25)
    assert "6.25 km/h" in dw.wind_text(), dw.wind_text()


@tc(135933)
def test_forecast_exactly_five_days_mon_fri_135933(page):
    dw = mocked_home(page, days=["Mon", "Tue", "Wed", "Thu", "Fri"])
    days = [d["abbr"] for d in dw.forecast_days()]
    assert days == ["Mon", "Tue", "Wed", "Thu", "Fri"], days


@tc(136057)
def test_fewer_than_five_forecast_days_136057(page):
    dw = mocked_home(page, keep_days=3)
    days = dw.forecast_days()
    assert len(days) == 3, days
    assert all(d["abbr"] and d["temp"] and d["hasIcon"] for d in days), days
    assert FALLBACK_EN not in dw.weather_text()


# ---------------------------------------------------------------------------
# Weather API failure / timeout / recovery
# ---------------------------------------------------------------------------
@tc(135960)
def test_weather_api_down_fallback_english_135960(page):
    dw = HomeDynamicWidgetsPage(page)
    dw.route_weather(lambda r: r.fulfill(status=503, body="Service Unavailable"))
    dw.open_home_no_wait()
    assert dw.wait_weather_text(FALLBACK_EN), dw.weather_text()
    assert dw.weather_text() == FALLBACK_EN or FALLBACK_EN in dw.weather_text()
    assert "503" not in dw.weather_text() and not dw.has_page_horizontal_overflow()


@tc(135961)
def test_weather_api_down_fallback_arabic_135961(page):
    dw = HomeDynamicWidgetsPage(page)
    dw.route_weather(lambda r: r.fulfill(status=503, body="Service Unavailable"))
    dw.open_home_no_wait("ar")
    assert dw.wait_weather_text(FALLBACK_AR), dw.weather_text()


@tc(136068)
def test_weather_api_401_shows_generic_fallback_136068(page):
    dw = HomeDynamicWidgetsPage(page)
    dw.route_weather(lambda r: r.fulfill(status=401, content_type="application/json",
                                         body='{"error":"invalid api key","code":401,"trace":"at WeatherClient"}'))
    dw.open_home_no_wait()
    assert dw.wait_weather_text(FALLBACK_EN), dw.weather_text()
    text = dw.weather_text().lower()
    assert not any(s in text for s in ("401", "api key", "unauthorized", "trace", "exception")), text


@tc(136058)
def test_weather_api_timeout_shows_fallback_136058(page):
    """The API never answers; the widget must leave the loading state for
    the fallback message within its timeout (read from the client
    extension: see weather_mock.CLIENT_TIMEOUT_S)."""
    dw = HomeDynamicWidgetsPage(page)
    dw.route_weather(lambda r: None)  # never fulfilled: a hung request
    dw.open_home_no_wait()
    assert dw.wait_weather_text(FALLBACK_EN, timeout_ms=int((wm.CLIENT_TIMEOUT_S + 15) * 1000)), (
        f"still loading after {wm.CLIENT_TIMEOUT_S + 15}s: {dw.weather_text()!r}")
    assert not dw.is_weather_loading_placeholder_visible()


@tc(136059)
def test_weather_recovers_after_api_returns_136059(page):
    """First load fails -> fallback; the API comes back; the widget's next
    refresh shows live data with no admin action."""
    dw = HomeDynamicWidgetsPage(page)
    state = {"down": True}

    def handler(route):
        if state["down"]:
            route.fulfill(status=503, body="down")
        else:
            route.continue_()
    dw.route_weather(handler)
    dw.open_home_no_wait()
    assert dw.wait_weather_text(FALLBACK_EN)
    state["down"] = False
    recovered = dw.page.locator(HomeDynamicWidgetsPage.WEATHER_TEMP).first
    try:
        recovered.wait_for(state="visible", timeout=int(wm.CLIENT_REFRESH_S * 1000) + 15000)
        how = "widget refresh cycle"
    except Exception:  # noqa: BLE001 — no in-page refresh: the visitor's next page load is the next cycle
        dw.open_home()
        how = "next page load"
    allure.attach(how, name="recovered via")
    assert re.search(r"\d", dw.temp_text()) and FALLBACK_EN not in dw.weather_text()


@pytest.mark.parametrize("page", [ANON_1920], indirect=True)
@pytest.mark.parametrize("x", [pytest.param(1, marks=pytest.mark.tc_135965, id="135965"),
                               pytest.param(2, marks=pytest.mark.tc_136067, id="136067")])
def test_all_widgets_disabled_section_collapses(page, x):
    """Case: Weather, Marhaba Guide and B2B all Active=False. The image
    widgets' "disabled" state is reproduced on the visitor's page by an empty
    active-widgets feed (what the server returns when none is active) — no
    real record is touched. Weather has no CMS switch (see the Control_Panel
    Weather cases), so it cannot be disabled; the case's expectation is still
    asserted: no widget card, no broken container, neighbours undisturbed."""
    dw = HomeDynamicWidgetsPage(page)
    dw.limit_cards_to(())
    dw.open_home()
    nb = dw.section_neighbours()
    items = dw.row_items()
    dw.section_screenshot(f"reports/manual-exec-129384-{'135965' if x == 1 else '136067'}-all-disabled.png")
    allure.attach(json.dumps({"items": items, "neighbours": nb}, indent=1), name="section with no active widget")
    assert not [i for i in items if i["kind"] == "card"], "a widget card rendered with no active widget"
    assert not dw.has_page_horizontal_overflow()
    assert nb["prev"] and nb["next"] and nb["prev"]["bottom"] <= nb["self"]["top"] + 1 <= nb["next"]["top"] + 1
    assert not dw.is_weather_widget_visible(), "the widgets section is not empty: the Weather card still renders"


@tc(135943)
def test_weather_loading_placeholder_135943(page):
    dw = HomeDynamicWidgetsPage(page)
    assert dw.delay_weather_api_and_reload()


# ---------------------------------------------------------------------------
# Section / cards — content and order
# ---------------------------------------------------------------------------
@tc(135955)
@PUBLIC_GROUP
def test_three_widgets_in_order_english_135955(page):
    dw = home(page)
    items = dw.row_items()
    assert [i["kind"] for i in items] == ["weather", "card", "card"], items
    assert [i["erc"] for i in items[1:]] == [MARHABA, B2B], items
    assert dw.widget_title_text() == "Weather" and re.search(r"\d", dw.temp_text())
    for erc in (MARHABA, B2B):
        info = dw.card_img_info_for_erc(erc)
        assert info["complete"] and info["nw"] > 0, info


@tc(135956)
@PUBLIC_GROUP
def test_three_widgets_arabic_rtl_135956(page):
    en_src = {e: home(page).card_img_info_for_erc(e)["src"] for e in (MARHABA, B2B)}
    dw = home(page, "ar")
    items = dw.row_items()
    assert [i["kind"] for i in items].count("card") == 2 and items[0]["kind"] == "weather"
    xs = [i["x"] for i in items]
    assert xs == sorted(xs, reverse=True), f"row not mirrored RTL: {xs}"
    assert dw.widget_title_text() == "الطقس"
    for e in (MARHABA, B2B):
        info = dw.card_img_info_for_erc(e)
        assert info["complete"] and info["nw"] > 0
        allure.attach(f"EN {en_src[e]}\nAR {info['src']}", name=f"{e} image src")
        assert info["src"] != en_src[e], f"{e}: Arabic page shows the English image"


VISUAL_CASES = [
    pytest.param(MARHABA, "en", marks=[pytest.mark.tc_135940, pytest.mark.tc_136069, pytest.mark.tc_136070,
                                        pytest.mark.tc_136071, pytest.mark.tc_136072, pytest.mark.tc_136073],
                 id="marhaba-en"),
    pytest.param(B2B, "en", marks=[pytest.mark.tc_135941, pytest.mark.tc_136075, pytest.mark.tc_136076,
                                    pytest.mark.tc_136077, pytest.mark.tc_136078, pytest.mark.tc_136079],
                 id="b2b-en"),
    pytest.param(MARHABA, "ar", marks=pytest.mark.tc_136074, id="marhaba-ar"),
    pytest.param(B2B, "ar", marks=pytest.mark.tc_136080, id="b2b-ar"),
]


@pytest.mark.parametrize("page", [ANON_1920], indirect=True)
@pytest.mark.parametrize("erc,locale", VISUAL_CASES)
def test_card_shows_its_configured_image(page, erc, locale):
    """The card renders the record's configured (EN or AR) image, fully
    loaded and uncropped; the screenshot is the evidence for the copy and
    graphics the case lists (verified visually, report §3)."""
    dw = home(page, locale)
    info = dw.card_img_info_for_erc(erc)
    shot = dw.card_screenshot_for_erc(erc, f"reports/manual-exec-129384-{erc.split('-')[-1]}-{locale}.png")
    allure.attach.file(shot, name=f"{erc} {locale}", attachment_type=allure.attachment_type.PNG)
    assert info["complete"] and info["nw"] > 0, info
    if locale == "ar":
        assert dw.page_direction() == "rtl"


# ---------------------------------------------------------------------------
# Geometry vs Figma (1920 viewport, Rule 1 tolerances)
# ---------------------------------------------------------------------------
@tc(135929, viewport=(1920, 1080))
def test_weather_card_height_362_135929(page):
    dw = home(page)
    h = dw.weather_widget_box()["height"]
    assert abs(h - FIGMA["card_h"]) <= LAYOUT_TOL, f"Weather card height {h:.1f} vs Figma 362 (±2)"


@tc(135930, viewport=(1920, 1080))
def test_widget_row_columns_and_gaps_135930(page):
    """Measured under the PBI's own precondition (Weather + the two image
    widgets): qcdev currently also publishes two later widgets (171082,
    171116), so the feed is filtered to the PBI's two on this page only."""
    HomeDynamicWidgetsPage(page).limit_cards_to((MARHABA, B2B))
    dw = home(page)
    items = dw.row_items()
    row = dw.row_box()
    widths = [i["w"] for i in items]
    gaps = [items[k + 1]["x"] - (items[k]["x"] + items[k]["w"]) for k in range(len(items) - 1)]
    allure.attach(f"row={row}\nwidths={widths}\ngaps={gaps}", name="measured")
    assert abs(row["width"] - FIGMA["row_w"]) <= LAYOUT_TOL, f"row width {row['width']:.1f} vs 1320"
    assert all(abs(w - FIGMA["card_w"]) <= LAYOUT_TOL for w in widths), f"column widths {widths} vs 424"
    assert all(abs(g - FIGMA["gap"]) <= LAYOUT_TOL for g in gaps), f"gaps {gaps} vs 24"


@tc(135931, viewport=(1920, 1080))
def test_weather_card_padding_gap_radius_135931(page):
    dw = home(page)
    outer, wrap = dw.weather_widget_style(), dw.weather_wrap_style()
    allure.attach(json.dumps({"outer": outer, "wrap": wrap}, indent=1), name="computed")
    pad = [px(outer["paddingTop"]) + px(wrap["paddingTop"]), px(outer["paddingRight"]) + px(wrap["paddingRight"]),
           px(outer["paddingBottom"]) + px(wrap["paddingBottom"]), px(outer["paddingLeft"]) + px(wrap["paddingLeft"])]
    assert abs(px(outer["borderRadius"]) - FIGMA["radius"]) <= LAYOUT_TOL, outer["borderRadius"]
    assert abs(pad[0] - FIGMA["pad_v"]) <= LAYOUT_TOL and abs(pad[2] - FIGMA["pad_v"]) <= LAYOUT_TOL, f"vertical padding {pad}"
    assert abs(pad[1] - FIGMA["pad_h"]) <= LAYOUT_TOL and abs(pad[3] - FIGMA["pad_h"]) <= LAYOUT_TOL, f"horizontal padding {pad}"
    gaps = dw.page.locator(HomeDynamicWidgetsPage.WEATHER_WRAP).evaluate(
        "w => { const k=[...w.children].map(c=>c.getBoundingClientRect()); return k.slice(1).map((b,i)=>b.top-k[i].bottom); }")
    allure.attach(str(gaps), name="internal vertical gaps")
    assert gaps and all(abs(g - FIGMA["inner_gap"]) <= LAYOUT_TOL for g in gaps), f"internal gaps {gaps} vs 16"


@tc(135932)
def test_weather_card_maroon_background_135932(page):
    dw = home(page)
    assert dw.weather_widget_style()["backgroundColor"] == FIGMA["bg"]


@pytest.mark.parametrize("page", [ANON_1920], indirect=True)
@pytest.mark.parametrize("erc", [pytest.param(MARHABA, marks=pytest.mark.tc_135938, id="135938-marhaba"),
                                 pytest.param(B2B, marks=pytest.mark.tc_135939, id="135939-b2b")])
def test_card_structure_vs_figma(page, erc):
    """Card 424 x 362 (±5, image), radius 16 (±2), image filling the card
    (Figma STRETCH): rendered aspect equals the image's own aspect. Measured
    with the PBI's three widgets only (feed filtered on this page, see 135930)."""
    HomeDynamicWidgetsPage(page).limit_cards_to((MARHABA, B2B))
    dw = home(page)
    box, style, info = dw.card_box_for_erc(erc), dw.card_style_for_erc(erc), dw.card_img_info_for_erc(erc)
    allure.attach(json.dumps({"box": box, "style": style, "img": info}, indent=1), name="measured")
    dw.card_screenshot_for_erc(erc, f"reports/manual-exec-129384-{erc.split('-')[-1]}-structure.png")
    assert abs(box["width"] - FIGMA["card_w"]) <= IMAGE_TOL and abs(box["height"] - FIGMA["card_h"]) <= IMAGE_TOL, box
    assert abs(px(style["borderRadius"]) - FIGMA["radius"]) <= LAYOUT_TOL, style["borderRadius"]
    shown_h_for_natural_aspect = info["w"] * info["nh"] / info["nw"]
    assert info["fit"] == "fill" or abs(shown_h_for_natural_aspect - info["h"]) <= IMAGE_TOL, (
        f"image is cropped ({info['fit']}): natural {info['nw']}x{info['nh']} shown {info['w']:.0f}x{info['h']:.0f}")


# ---------------------------------------------------------------------------
# Interaction / responsive / compatibility
# ---------------------------------------------------------------------------
@tc(135944)
def test_weather_hover_keeps_layout_135944(page):
    dw = home(page)
    before = dw.weather_widget_box()
    dw.hover_weather_widget()
    after = dw.weather_widget_box()
    assert abs(before["width"] - after["width"]) <= LAYOUT_TOL and abs(before["height"] - after["height"]) <= LAYOUT_TOL
    assert not dw.has_page_horizontal_overflow()


@tc(135945, viewport=(375, 812))
def test_widgets_stack_on_mobile_375_135945(page):
    HomeDynamicWidgetsPage(page).limit_cards_to((MARHABA, B2B))  # the PBI's 3 widgets
    dw = home(page)
    items = dw.row_items()
    xs = {round(i["x"]) for i in items}
    ys = sorted(i["y"] for i in items)
    # Mobile order is cards first, Weather last (flex `order`, per the Figma mobile frame).
    assert len(xs) == 1 and all(b - a > 0 for a, b in zip(ys, ys[1:])), f"not a single column: {items}"
    assert all(i["w"] >= 375 - 2 * 24 - 4 for i in items), f"cards not full width: {[i['w'] for i in items]}"
    assert not dw.has_page_horizontal_overflow()


@tc(135946, viewport=(768, 1024))
def test_widgets_reflow_on_tablet_768_135946(page):
    HomeDynamicWidgetsPage(page).limit_cards_to((MARHABA, B2B))  # the PBI's 3 widgets
    dw = home(page)
    items = dw.row_items()
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            A, B = items[a], items[b]
            overlap = not (A["x"] + A["w"] <= B["x"] + 1 or B["x"] + B["w"] <= A["x"] + 1 or
                           A["y"] + A["h"] <= B["y"] + 1 or B["y"] + B["h"] <= A["y"] + 1)
            assert not overlap, f"cards overlap at 768: {A} / {B}"
    assert all(i["x"] >= 0 and i["x"] + i["w"] <= 768 + 1 for i in items), "card cut off at 768"
    assert not dw.has_page_horizontal_overflow()
    dw.section_screenshot("reports/manual-exec-129384-135946-768.png")


def _weather_signature(browser_obj):
    from core.web.browser import new_context
    ctx = new_context(browser_obj, use_auth_state=False, viewport=(1920, 1080))
    try:
        dw = HomeDynamicWidgetsPage(ctx.new_page())
        dw.open_home()
        box = dw.weather_widget_box()
        icon = dw.page.locator(HomeDynamicWidgetsPage.WEATHER_ICON_SVG).first.bounding_box()
        return {"title": dw.widget_title_text(), "city": dw.city_text(), "days": len(dw.forecast_days()),
                "w": round(box["width"]), "h": round(box["height"]),
                "icon": bool(icon and icon["width"] > 0 and icon["height"] > 0)}
    finally:
        ctx.close()


@pytest.mark.tc_135947
@allure.label("testcase", "135947")
def test_weather_same_across_browsers_135947(browser, alt_engine_browser):
    sig = {"chromium": _weather_signature(browser)}
    for engine in ("firefox", "msedge", "webkit"):
        sig[engine] = _weather_signature(alt_engine_browser(engine))
    allure.attach(json.dumps(sig, indent=1), name="per-engine")
    ref = sig["chromium"]
    for engine, s in sig.items():
        assert {k: s[k] for k in ("title", "city", "days", "icon")} == {k: ref[k] for k in ("title", "city", "days", "icon")}, (engine, s)
        assert abs(s["w"] - ref["w"]) <= LAYOUT_TOL and abs(s["h"] - ref["h"]) <= LAYOUT_TOL, (engine, s, ref)


@pytest.mark.tc_135948
@allure.label("testcase", "135948")
def test_weather_icon_renders_chrome_and_safari_135948(browser, alt_engine_browser):
    chrome, safari = _weather_signature(browser), _weather_signature(alt_engine_browser("webkit"))
    assert chrome["icon"] and safari["icon"], {"chrome": chrome, "webkit": safari}


@tc(135949)
def test_widgets_progressive_load_on_slow_3g_135949(page):
    """Chromium network emulation at DevTools "Slow 3G" (400 ms RTT, 400
    kbit/s down, 400 kbit/s up). The row must reserve its space: the boxes
    measured while assets are still loading match the final ones."""
    cdp = page.context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 400,
                                                   "downloadThroughput": 400 * 1024 / 8,
                                                   "uploadThroughput": 400 * 1024 / 8})
    page.set_default_timeout(600000)
    dw = HomeDynamicWidgetsPage(page)
    page.goto(web_url("/home"), wait_until="commit", timeout=600000)
    page.locator(HomeDynamicWidgetsPage.SECTION).wait_for(state="attached", timeout=600000)
    early = dw.row_items()
    # The page's full "load" never completes on Slow 3G inside 10 min (several MB of
    # site assets); the widgets themselves are what the case observes.
    dw.page.locator(HomeDynamicWidgetsPage.WEATHER_WIDGET).wait_for(state="visible", timeout=600000)
    dw.page.locator(HomeDynamicWidgetsPage.CARD).nth(1).wait_for(state="attached", timeout=600000)
    late = dw.row_items()
    allure.attach(json.dumps({"early": early, "late": late}, indent=1), name="row while loading vs loaded")
    assert len(early) == len(late) >= 3
    for a, b in zip(early, late):
        assert abs(a["x"] - b["x"]) <= LAYOUT_TOL and abs(a["w"] - b["w"]) <= LAYOUT_TOL, (a, b)
        assert abs(a["h"] - b["h"]) <= LAYOUT_TOL, f"height shifted while loading: {a['h']} -> {b['h']}"
    for erc in (MARHABA, B2B):
        info = dw.card_img_info_for_erc(erc)
        assert info["complete"] and info["nw"] > 0

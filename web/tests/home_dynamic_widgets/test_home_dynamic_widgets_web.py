"""
web/tests/home_dynamic_widgets/test_home_dynamic_widgets_web.py —
Dynamic Widgets: Weather, Marhaba Guide, B2B (PBI 129384 / QC-HOME-008), Web
platform.

Source: 34 approved, Automation-tagged, UI-category, Web-platform cases handed
off for this PBI (ADO TC 135921-135944, 136069-136080). Control_Panel-tagged
cases for this same PBI are out of scope for this run (see the sibling
test_home_dynamic_widgets_control_panel.py skeleton).

Real-environment findings (full CLI-extraction evidence in this module's
Page Object, home_dynamic_widgets_page.py, whose docstring documents every
live measurement below). Per this batch's Result-integrity instruction, a
real mismatch against the case's literal stated value is scripted to FAIL
HONESTLY rather than silently corrected — with one carved-out judgment call:
the Weather widget's live/dynamic DATA fields (temperature, condition,
high/low, forecast values) are asserted by FORMAT/PRESENCE, not by the
case's literal figures, since the live weather naturally differs run to run.
Two cases (135927, 135928) are explicitly titled "(design-vs-spec gap)" and
are asserted against their literal stated values on purpose (per the task's
explicit instruction), not treated under the live-data carve-out.

  - TC 135921/135922/135933/135934/135937: CONFIRMED LIVE, genuine passes —
    widget title "Weather", city "Doha" in bold, exactly 5 Mon-Fri forecast
    entries each with a name/icon/temperature, and a genuine EN/LTR render
    (`<html lang="en-US" dir="ltr">`).
  - TC 135923/135924/135925/135926/135936: the underlying weather DATA is
    confirmed LIVE and DYNAMIC (36℃, "Clear Sky", "43° - 32°", a sun-only
    icon, Arabic "صحو") — asserted structurally (format/presence), not to
    the case's literal "30", "Light Rain", "30°-24°", or a specific icon
    shape, per the judgment call above. The STATIC pieces of the same cases
    (large/bold numeral styling, an SVG icon actually rendering, Arabic
    static labels "الطقس"/"الدوحة" and translated forecast day names) are
    asserted for real, literal equality.
  - TC 135927/135928 (explicit design-vs-spec gap): humidity is confirmed
    LIVE as "55%" (not the case's literal "27%"); wind speed is confirmed
    LIVE as "2.7 km/h" (not the case's literal "6.25 km/h"). Scripted
    against the case's literal values as explicitly instructed — WILL FAIL
    HONESTLY, not a framework defect.
  - TC 135929/135930/135931: real, measured Figma-token mismatches at the
    1320px viewport — card height computes to ~358.6px (not 362px); the row
    is a fixed 1248px flex container (not 1320px) with 32px gaps (not 24px)
    and ~394.67px columns (not ~424px); the real content box
    (`.weather-wrap`) computes padding 15px/12px/20px (not 24px/20px) and
    has no discrete flex/grid gap token (`gap: normal`, not 16px) — only the
    16px corner radius matches exactly. Scripted to the case's literal
    tokens — WILL FAIL HONESTLY except the radius assertion.
  - TC 135932: CONFIRMED LIVE — the weather widget's background computes to
    rgb(145, 23, 49) (#911731), a genuine dark red/maroon — real, matching
    pass.
  - TC 135938/135939/135940/135941/136069-136080 (Marhaba Guide / B2B
    Platform cards): a REAL, LIVE-CONFIRMED STRUCTURAL GAP — both cards are
    a single `<a class="qc-dw-card"><img class="qc-dw-card-img"></a>` with
    NO other descendant DOM node. Every heading/body/feature-item/CTA/
    footer/logo/badge/seal element these cases describe is baked into the
    single PNG the `<img>` points at, confirmed by walking the live subtree.
    What IS real and asserted: card geometry, `border-radius` (16px, a
    genuine match), the image `src`/`href` (confirms the right image/link),
    and `object-fit` (computes to "cover", not the case's stated "STRETCH").
    Every text/graphic/CTA/footer assertion these cases make is scripted per
    the case's literal expected result via a scoped, never-throwing
    presence check against the real, confirmed-empty subtree — and WILL
    FAIL HONESTLY, reporting a genuine, disclosed content-implementation gap
    (the rich card design was not actually built as real HTML/CSS), not a
    locator defect.
  - TC 136074/136080 (Marhaba/B2B RTL): CONFIRMED LIVE — the 3-widget row
    genuinely mirrors right-to-left under `dir="rtl"` (a real, confirmed
    pass on the row-level x-ordering); the case's specific internal-element
    mirroring claims (logo/badge/seal moving sides) have no live DOM analog
    for the same flat-image reason above and are scripted to FAIL HONESTLY.
  - TC 135943: CONFIRMED LIVE — `.qc-dw-weather` renders a dedicated
    `.qc-weather-card--loading` skeleton node (not blank/broken) while the
    real `/o/qc-weather/v1.0/doha` request is held open via `page.route()` —
    genuine pass.
  - TC 135944: CONFIRMED LIVE — the weather widget's bounding box is
    byte-identical before/after a hover — genuine pass.
"""

import re

import allure
import pytest

from web.pages.home_dynamic_widgets.home_dynamic_widgets_page import HomeDynamicWidgetsPage

PBI = "129384"

EPIC = "GLOBAL"
FEATURE = "Dynamic Widgets (Weather, Marhaba Guide, B2B)"

TEMP_FORMAT_RE = re.compile(r"^\d{1,3}\s*(?:℃|°C)$")   # e.g. "36℃"
HIGHLOW_FORMAT_RE = re.compile(r"^\d{1,3}°\s*-\s*\d{1,3}°$")  # e.g. "43° - 32°"

AR_WIDGET_TITLE = "الطقس"          # "الطقس" — Weather
AR_CITY = "الدوحة"              # "الدوحة" — Doha
AR_FORECAST_ABBRS = [
    "إثنين",   # إثنين — Mon
    "ثلاثاء",  # ثلاثاء — Tue
    "أربعاء",  # أربعاء — Wed
    "خميس",         # خميس — Thu
    "جمعة",         # جمعة — Fri
]


# ── TC 135921 — Weather widget title ────────────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The Weather widget displays the title "Weather"')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135921")
def test_weather_widget_title(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135921 | PBI 129384
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load the Home Page (EN) and scroll to the widgets section"):
        dw.open_home()
        dw.scroll_to_section()

    with allure.step("Read the Weather card header text"):
        title = dw.widget_title_text()

    # Assert
    assert dw.is_section_visible()
    assert title == "Weather", f"expected Weather card header 'Weather', got {title!r}"


# ── TC 135922 — City name "Doha" in bold ────────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('The Weather widget displays the city name "Doha" in bold')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135922")
def test_weather_city_name_bold(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135922 | PBI 129384
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page (EN)"):
        dw.open_home()

    with allure.step("Read the Weather card city label and its computed style"):
        city_text = dw.city_text()
        city_style = dw.city_style()

    # Assert
    assert city_text == "Doha", f"expected city name 'Doha', got {city_text!r}"
    assert city_style["fontWeight"] == "700", f"expected bold (700) city name, got {city_style['fontWeight']!r}"


# ── TC 135923 — Temperature as large numeral with degree unit ──────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Weather widget displays the current temperature as a large numeral with its degree unit")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135923")
def test_weather_temperature_large_numeral_with_unit(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135923 | PBI 129384
    # The temperature is live weather data (confirmed "36℃" at
    # extraction time, not the case's literal "30") — asserted by FORMAT,
    # not the literal figure (see module docstring judgment call). The
    # numeral's LARGE, BOLD styling and the adjacent degree unit are static
    # and asserted literally.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Read the Weather card temperature text and computed style"):
        temp_text = dw.temp_text()
        temp_style = dw.temp_style()

    # Assert
    assert TEMP_FORMAT_RE.match(temp_text), f"expected '<number><degree unit>' format, got {temp_text!r}"
    assert temp_style["fontWeight"] == "700", "expected the temperature to render as a bold, primary numeral"
    assert temp_style["fontSize"] == "64px", f"expected a large (64px) temperature numeral, got {temp_style['fontSize']!r}"


# ── TC 135924 — Weather condition label ─────────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Weather widget displays the current weather condition label")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135924")
def test_weather_condition_label_present(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135924 | PBI 129384
    # Live weather data (confirmed "Clear Sky" at extraction time, not the
    # case's literal "Light Rain") — asserted for real, non-empty presence,
    # not the literal string (see module docstring judgment call).
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Read the Weather card condition label"):
        condition_text = dw.condition_text()

    # Assert
    assert condition_text and condition_text.strip(), "expected a non-empty weather condition label"
    assert "lorem" not in condition_text.lower(), f"expected a real condition label, got {condition_text!r}"


# ── TC 135925 — Weather icon matches condition ──────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Weather widget displays a weather icon matching the current condition")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135925")
def test_weather_icon_matches_condition(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135925 | PBI 129384
    # The icon's shape is condition-driven live data (confirmed a sun-only
    # ray+circle glyph for "Clear Sky", not the case's literal "cloud+sun"
    # combination) — asserted structurally (a real icon renders), not the
    # literal shape, per the module docstring judgment call.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Check the Weather card's condition icon"):
        icon_rendered = dw.is_icon_svg_rendered()

    # Assert
    assert icon_rendered, "expected a real weather-condition icon (SVG) to render"


# ── TC 135926 — High/low temperature row ────────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Weather widget displays the high/low temperature row")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135926")
def test_weather_highlow_row_format(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135926 | PBI 129384
    # Live weather data (confirmed "43° - 32°" at extraction time,
    # not the case's literal "30°-24°") — asserted by FORMAT, not
    # the literal figures (see module docstring judgment call).
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Read the high/low temperature row"):
        highlow_text = dw.highlow_text()

    # Assert
    assert HIGHLOW_FORMAT_RE.match(highlow_text), (
        f"expected a '<high>° - <low>°' format, got {highlow_text!r}"
    )


# ── TC 135927 — Humidity value (explicit design-vs-spec gap) ───────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The Weather widget displays humidity "27%" (design-vs-spec gap)')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135927")
def test_weather_humidity_value(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135927 | PBI 129384
    # Explicit design-vs-spec gap case (per its own title) — scripted per the
    # case's literal expected "27%" as explicitly instructed. Live humidity
    # is confirmed "55%" at extraction time — this assertion is expected to
    # FAIL HONESTLY against that real, disclosed gap, not a framework defect.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Read the humidity value on the secondary metrics row"):
        humidity_text = dw.humidity_text()

    # Assert
    assert humidity_text == "27%", f"expected humidity '27%' per the case's stated spec, got {humidity_text!r}"


# ── TC 135928 — Wind speed value (explicit design-vs-spec gap) ─────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The Weather widget displays wind speed "6.25 km/h" (design-vs-spec gap)')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135928")
def test_weather_wind_speed_value(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135928 | PBI 129384
    # Explicit design-vs-spec gap case (per its own title) — scripted per the
    # case's literal expected "6.25 km/h". Live wind speed is confirmed
    # "2.7 km/h" at extraction time — expected to FAIL HONESTLY, not a
    # framework defect.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Read the wind speed value on the secondary metrics row"):
        wind_text = dw.wind_text()

    # Assert
    assert wind_text == "6.25 km/h", f"expected wind speed '6.25 km/h' per the case's stated spec, got {wind_text!r}"


# ── TC 135929 — Weather card fixed height at 1320px viewport ───────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Weather card renders at the Figma-specified fixed height of 362px")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135929")
@pytest.mark.parametrize("page", [(1320, 900)], indirect=True)
def test_weather_card_fixed_height_at_1320_viewport(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135929 | PBI 129384
    # Real, measured height at 1320px is ~358.6px (see module docstring) —
    # scripted to the case's literal 362px and expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page at a 1320px-wide viewport"):
        dw.open_home()

    with allure.step("Measure the Weather card height"):
        box = dw.weather_widget_box()

    # Assert
    assert round(box["height"]) == 362, f"expected Weather card height 362px, got {box['height']}"


# ── TC 135930 — 3-widget row columns and gaps at 1320px ─────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("3-widget row layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The 3-widget row uses 3 equal ~424px columns with 24px gaps in a 1320px container")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135930")
@pytest.mark.parametrize("page", [(1320, 900)], indirect=True)
def test_three_widget_row_columns_and_gaps(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135930 | PBI 129384
    # Real, measured row is a fixed 1248px flex container with 32px gaps and
    # ~394.67px columns (see module docstring) — scripted to the case's
    # literal tokens and expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page at a 1320px viewport"):
        dw.open_home()

    with allure.step("Measure the row width, column widths, and gap"):
        row_box = dw.row_box()
        row_style = dw.row_style()
        weather_box = dw.weather_widget_box()

    # Assert
    assert round(row_box["width"]) == 1320, f"expected a 1320px total row width, got {row_box['width']}"
    assert round(weather_box["width"]) == 424, f"expected ~424px columns, got {weather_box['width']}"
    assert row_style["gap"] == "24px", f"expected a 24px gap between cards, got {row_style['gap']!r}"


# ── TC 135931 — Weather card padding, gap, and corner radius ───────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Weather card uses the Figma-specified padding, internal gap, and corner radius")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135931")
def test_weather_card_padding_gap_and_radius(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135931 | PBI 129384
    # Real `.weather-wrap` padding computes to 15px/12px/20px (not
    # 24px/20px) with no discrete flex/grid gap (not 16px) — only the 16px
    # corner radius matches exactly (see module docstring). Scripted to the
    # case's literal tokens; expected to FAIL HONESTLY except the radius
    # assertion.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Read the Weather card's box-model and radius"):
        wrap_style = dw.weather_wrap_style()
        widget_style = dw.weather_widget_style()

    # Assert
    assert widget_style["borderRadius"] == "16px", f"expected 16px corner radius, got {widget_style['borderRadius']!r}"
    assert wrap_style["paddingTop"] == "24px" and wrap_style["paddingBottom"] == "24px", (
        f"expected 24px top/bottom padding, got top={wrap_style['paddingTop']!r} bottom={wrap_style['paddingBottom']!r}"
    )
    assert wrap_style["paddingLeft"] == "20px" and wrap_style["paddingRight"] == "20px", (
        f"expected 20px left/right padding, got left={wrap_style['paddingLeft']!r} right={wrap_style['paddingRight']!r}"
    )
    assert wrap_style["gap"] == "16px", f"expected a 16px internal element gap, got {wrap_style['gap']!r}"


# ── TC 135932 — Weather card background color ───────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Weather card renders with a dark red/maroon background color")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135932")
def test_weather_card_background_color(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135932 | PBI 129384
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Read the Weather card's computed background color"):
        widget_style = dw.weather_widget_style()

    # Assert
    assert widget_style["backgroundColor"] == "rgb(145, 23, 49)", (  # #911731
        f"expected a dark red/maroon background (#911731), got {widget_style['backgroundColor']!r}"
    )


# ── TC 135933 — Exactly 5 forecast days (Mon-Fri) ───────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The 5-day forecast row displays exactly 5 days (Mon-Fri)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135933")
def test_forecast_row_exactly_5_days(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135933 | PBI 129384
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Count and read the forecast day entries"):
        count = dw.forecast_day_count()
        days = dw.forecast_days()

    # Assert
    assert count == 5, f"expected exactly 5 forecast day entries, got {count}"
    assert [d["abbr"] for d in days] == ["Mon", "Tue", "Wed", "Thu", "Fri"], (
        f"expected day labels Mon,Tue,Wed,Thu,Fri in order, got {[d['abbr'] for d in days]}"
    )


# ── TC 135934 — Each forecast day shows name, icon, and temperature ────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Each forecast day shows a day name, weather icon, and temperature")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135934")
def test_each_forecast_day_shows_name_icon_and_temperature(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135934 | PBI 129384
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the 'Mon' forecast entry"):
        days = dw.forecast_days()
        mon = next((d for d in days if d["abbr"] == "Mon"), None)

    # Assert
    assert mon is not None, f"expected a 'Mon' forecast entry, got {days}"
    assert mon["abbr"] == "Mon"
    assert mon["hasIcon"], "expected the 'Mon' entry to render a weather icon"
    assert mon["temp"] and mon["temp"].strip(), "expected the 'Mon' entry to render a temperature value"


# ── TC 135936 — Weather widget renders correctly in Arabic (RTL) ───────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Weather widget renders correctly in Arabic (RTL)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.bilingual
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135936")
def test_weather_widget_renders_in_arabic_rtl(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135936 | PBI 129384
    # Static Arabic copy (title/city/forecast day names) is asserted
    # literally; the condition label is live data and asserted only for
    # non-empty Arabic presence (see module docstring judgment call).
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Switch site language to Arabic"):
        dw.open_home_arabic()

    with allure.step("Scroll to the widgets section"):
        dw.scroll_to_section()

    with allure.step("Read the Weather card layout direction and text"):
        page_dir = dw.page_direction()
        title = dw.widget_title_text()
        city = dw.city_text()
        condition = dw.condition_text()
        days = dw.forecast_days()

    # Assert
    assert page_dir == "rtl"
    assert title == AR_WIDGET_TITLE, f"expected Arabic title {AR_WIDGET_TITLE!r}, got {title!r}"
    assert city == AR_CITY, f"expected Arabic city name {AR_CITY!r}, got {city!r}"
    assert condition and condition.strip(), "expected a non-empty Arabic condition label"
    assert [d["abbr"] for d in days] == AR_FORECAST_ABBRS, (
        f"expected Arabic forecast day labels {AR_FORECAST_ABBRS}, got {[d['abbr'] for d in days]}"
    )


# ── TC 135937 — Weather widget renders correctly in English (LTR) ──────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Weather widget renders correctly in English (LTR)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.bilingual
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135937")
def test_weather_widget_renders_in_english_ltr(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135937 | PBI 129384
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page in English"):
        dw.open_home()

    with allure.step("Read the Weather card layout direction and title"):
        page_dir = dw.page_direction()
        page_lang = dw.page_lang()
        title = dw.widget_title_text()

    # Assert
    assert page_dir == "ltr", f"expected an LTR page, got dir={page_dir!r}"
    assert page_lang.startswith("en"), f"expected an English page, got lang={page_lang!r}"
    assert title == "Weather"


# ── TC 135943 — Loading placeholder before API data arrives ────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A loading placeholder displays on the Weather card before API data arrives")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135943")
def test_weather_loading_placeholder_before_api_data(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135943 | PBI 129384
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page with the Weather API response held open"):
        seen_loading = dw.delay_weather_api_and_reload()

    # Assert
    assert seen_loading, "expected a loading placeholder (skeleton) to render before Weather data arrives"


# ── TC 135944 — Hovering the Weather card does not break the layout ────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Weather widget")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Hovering the Weather card does not break the card layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.weather
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135944")
def test_weather_card_hover_does_not_break_layout(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135944 | PBI 129384
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Measure the Weather card, then hover it and re-measure"):
        box_before = dw.weather_widget_box()
        dw.hover_weather_widget()
        box_after = dw.weather_widget_box()

    # Assert
    assert round(box_before["width"]) == round(box_after["width"]), "expected no width shift on hover"
    assert round(box_before["height"]) == round(box_after["height"]), "expected no height shift on hover"
    assert not dw.has_page_horizontal_overflow(), "expected no overflow introduced by the hover state"


# ── TC 135938 — Marhaba Guide card structural dimensions, image, and logo ──
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Marhaba Guide card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Marhaba Guide card renders at the confirmed structural dimensions with its background image and top-left logo")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.marhaba
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135938")
def test_marhaba_card_structural_dimensions_and_logo(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135938 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP: the card is a single <a><img></a> with no
    # separate logo element (see module docstring). Height/object-fit/logo
    # assertions below are scripted to the case's literal claims and are
    # expected to FAIL HONESTLY; only the border-radius genuinely matches.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page at a 1320px viewport"):
        dw.open_home()

    with allure.step("Inspect the Marhaba Guide card (2nd card in the row)"):
        box = dw.card_box(dw.MARHABA_INDEX)
        style = dw.card_style(dw.MARHABA_INDEX)
        object_fit = dw.card_img_object_fit(dw.MARHABA_INDEX)
        has_logo = dw.card_has_descendant(dw.MARHABA_INDEX, "[class*='logo'], svg, [alt*='logo' i]")

    # Assert
    assert round(box["height"]) == 362, f"expected a 362px card height, got {box['height']}"
    assert style["borderRadius"] == "16px", f"expected a 16px corner radius, got {style['borderRadius']!r}"
    assert object_fit == "stretch", f"expected the background image to render as a STRETCH fill, got {object_fit!r}"
    assert has_logo, "expected a separate top-left Qatar Chamber logo element"


# ── TC 135940 — Marhaba Guide card heading ──────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Marhaba Guide card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('The Marhaba Guide card displays the heading "Qatar Chamber Commercial & Industrial Directory"')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.marhaba
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135940")
def test_marhaba_card_heading_text(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135940 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP: no heading DOM node exists on this card (see
    # module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the Marhaba Guide card heading text"):
        has_heading = dw.card_contains_visible_text(
            dw.MARHABA_INDEX, "Qatar Chamber Commercial & Industrial Directory"
        )

    # Assert
    assert has_heading, 'expected the heading "Qatar Chamber Commercial & Industrial Directory" to render'


# ── TC 136069 — Marhaba Guide card body text ────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Marhaba Guide card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The Marhaba Guide card displays the body text "Register your business and complete your profile to get verified."')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.marhaba
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136069")
def test_marhaba_card_body_text(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136069 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the Marhaba Guide card body text"):
        has_body = dw.card_contains_visible_text(
            dw.MARHABA_INDEX, "Register your business and complete your profile to get verified."
        )

    # Assert
    assert has_body, "expected the Marhaba Guide card's body text to render"


# ── TC 136070 — Marhaba Guide card badge graphic ────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Marhaba Guide card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The Marhaba Guide card displays the gold-bordered "Verified by Qatar Chamber" shield badge graphic')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.marhaba
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136070")
def test_marhaba_card_badge_graphic(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136070 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the right side of the Marhaba Guide card for a badge graphic"):
        has_badge = dw.card_has_descendant(
            dw.MARHABA_INDEX, "[class*='badge'], [class*='shield'], svg"
        )

    # Assert
    assert has_badge, 'expected a gold-bordered "Verified by Qatar Chamber" shield badge graphic'


# ── TC 136071 — Marhaba Guide card feature items ────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Marhaba Guide card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The Marhaba Guide card displays the three feature items "Trusted Platform", "Verified Businesses", "Stronger Connections"')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.marhaba
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136071")
def test_marhaba_card_feature_items(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136071 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the feature items row on the Marhaba Guide card"):
        items = ["Trusted Platform", "Verified Businesses", "Stronger Connections"]
        found = [dw.card_contains_visible_text(dw.MARHABA_INDEX, item) for item in items]

    # Assert
    assert all(found), f"expected all three feature items {items} to render, found={found}"


# ── TC 136072 — Marhaba Guide card "JOIN NOW" CTA ───────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Marhaba Guide card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('The Marhaba Guide card displays the "JOIN NOW" CTA button')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.marhaba
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136072")
def test_marhaba_card_join_now_cta(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136072 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the CTA button on the Marhaba Guide card"):
        has_cta = dw.card_contains_visible_text(dw.MARHABA_INDEX, "JOIN NOW")

    # Assert
    assert has_cta, 'expected a "JOIN NOW" CTA button to render on the Marhaba Guide card'


# ── TC 136073 — Marhaba Guide card footer details ───────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Marhaba Guide card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Marhaba Guide card footer displays the website, phone, and social media details")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.marhaba
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136073")
def test_marhaba_card_footer_details(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136073 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the footer row of the Marhaba Guide card"):
        has_website = dw.card_contains_visible_text(dw.MARHABA_INDEX, "www.qatarchamber.com")
        has_phone = dw.card_contains_visible_text(dw.MARHABA_INDEX, "+974 4455 9111")

    # Assert
    assert has_website, "expected the website 'www.qatarchamber.com' to render in the footer"
    assert has_phone, "expected the phone number '+974 4455 9111' to render in the footer"


# ── TC 136074 — Marhaba Guide card renders correctly in Arabic (RTL) ───────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Marhaba Guide card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Marhaba Guide card renders correctly in Arabic (RTL)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.marhaba
@pytest.mark.bilingual
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136074")
def test_marhaba_card_renders_in_arabic_rtl(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136074 | PBI 129384
    # The 3-widget row's RIGHT-TO-LEFT visual mirror is CONFIRMED LIVE and
    # asserted for real; the card's own internal-element mirroring claim
    # (logo moving to top-right) has no live DOM analog (same flat-image gap
    # as TC 135938) and is expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Switch site language to Arabic and load the Home Page"):
        dw.open_home_arabic()

    with allure.step("Read the widgets row's mirrored x-ordering and the Marhaba card's logo element"):
        x_positions = dw.row_children_x_order()
        has_logo = dw.card_has_descendant(dw.MARHABA_INDEX, "[class*='logo'], svg, [alt*='logo' i]")

    # Assert
    assert x_positions[0] > x_positions[1] > x_positions[2], (
        f"expected the row to mirror right-to-left (weather rightmost, then Marhaba, then B2B), got {x_positions}"
    )
    assert has_logo, "expected the Marhaba Guide card's logo to mirror to the top-right in RTL"


# ── TC 135939 — B2B Platform card structural dimensions, image, and pattern ─
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("B2B Platform card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The B2B Platform card renders at the confirmed structural dimensions with its dotted background pattern and top-left logo")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.b2b
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135939")
def test_b2b_card_structural_dimensions_and_pattern(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135939 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP: same single <a><img></a> structure as the
    # Marhaba card (see module docstring) — expected to FAIL HONESTLY except
    # the border-radius assertion.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page at a 1320px viewport"):
        dw.open_home()

    with allure.step("Inspect the B2B Platform card (3rd card in the row)"):
        box = dw.card_box(dw.B2B_INDEX)
        style = dw.card_style(dw.B2B_INDEX)
        object_fit = dw.card_img_object_fit(dw.B2B_INDEX)
        has_pattern_or_logo = dw.card_has_descendant(
            dw.B2B_INDEX, "[class*='dot'], [class*='pattern'], [class*='logo'], svg"
        )

    # Assert
    assert round(box["height"]) == 362, f"expected a 362px card height, got {box['height']}"
    assert style["borderRadius"] == "16px", f"expected a 16px corner radius, got {style['borderRadius']!r}"
    assert object_fit == "stretch", f"expected the background image to render as a STRETCH fill, got {object_fit!r}"
    assert has_pattern_or_logo, "expected a discrete dotted-pattern and/or logo element"


# ── TC 135941 — B2B Platform card heading ───────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("B2B Platform card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('The B2B Platform card displays the heading "Get" / "Verified by Qatar Chamber"')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.b2b
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-135941")
def test_b2b_card_heading_text(page):
    # GLOBAL-DYNAMICWIDGETS-TC-135941 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the B2B Platform card heading text"):
        has_get = dw.card_contains_visible_text(dw.B2B_INDEX, "Get")
        has_verified = dw.card_contains_visible_text(dw.B2B_INDEX, "Verified by Qatar Chamber")

    # Assert
    assert has_get, 'expected the heading line "Get" to render'
    assert has_verified, 'expected the heading line "Verified by Qatar Chamber" to render'


# ── TC 136075 — B2B Platform card body text ─────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("B2B Platform card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The B2B Platform card displays the body text "Register and complete your profile in the Commercial and Industrial Directory."')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.b2b
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136075")
def test_b2b_card_body_text(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136075 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the B2B Platform card body text"):
        has_body = dw.card_contains_visible_text(
            dw.B2B_INDEX, "Register and complete your profile in the Commercial and Industrial Directory."
        )

    # Assert
    assert has_body, "expected the B2B Platform card's body text to render"


# ── TC 136076 — B2B Platform card bullet items ──────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("B2B Platform card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The B2B Platform card displays the three bullet items "Boost Credibility", "Build Trust", "Increase Visibility"')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.b2b
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136076")
def test_b2b_card_bullet_items(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136076 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the bullet items row on the B2B Platform card"):
        items = ["Boost Credibility", "Build Trust", "Increase Visibility"]
        found = [dw.card_contains_visible_text(dw.B2B_INDEX, item) for item in items]

    # Assert
    assert all(found), f"expected all three bullet items {items} to render, found={found}"


# ── TC 136077 — B2B Platform card callout box ───────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("B2B Platform card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The B2B Platform card displays the bordered callout box about the "Verified by Qatar Chamber" tag')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.b2b
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136077")
def test_b2b_card_callout_box(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136077 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the callout box on the B2B Platform card"):
        has_box = dw.card_has_descendant(dw.B2B_INDEX, "[class*='callout'], [class*='border']")
        has_text = dw.card_contains_visible_text(
            dw.B2B_INDEX, 'Look for the "Verified by Qatar Chamber" tag on trusted companies.'
        )

    # Assert
    assert has_box, "expected a bordered callout box element to render"
    assert has_text, 'expected the callout text about the "Verified by Qatar Chamber" tag to render'


# ── TC 136078 — B2B Platform card seal/ribbon graphic ───────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("B2B Platform card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The B2B Platform card displays the maroon verification seal/ribbon graphic")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.b2b
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136078")
def test_b2b_card_seal_graphic(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136078 | PBI 129384
    # REAL, LIVE-CONFIRMED GAP (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the seal/ribbon graphic on the B2B Platform card"):
        has_seal = dw.card_has_descendant(dw.B2B_INDEX, "[class*='seal'], [class*='ribbon'], svg")

    # Assert
    assert has_seal, "expected a maroon verification seal/ribbon graphic element"


# ── TC 136079 — B2B Platform card footer details ────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("B2B Platform card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The B2B Platform card footer displays the tagline, "Register now", and the "qcci.org" link')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.b2b
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136079")
def test_b2b_card_footer_details(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136079 | PBI 129384
    # The card's own href IS real (confirmed https://qcci.org) and asserted
    # literally; the rendered footer text (tagline/"Register now"/"qcci.org"
    # link text) has the same real, live-confirmed gap as the other
    # text-content cases (see module docstring) — expected to FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Load Home Page"):
        dw.open_home()

    with allure.step("Inspect the footer row of the B2B Platform card"):
        href = dw.card_href(dw.B2B_INDEX)
        has_tagline = dw.card_contains_visible_text(dw.B2B_INDEX, "Be Found. Be Trusted. Be Verified.")
        has_register_now = dw.card_contains_visible_text(dw.B2B_INDEX, "Register now")
        has_link_text = dw.card_contains_visible_text(dw.B2B_INDEX, "qcci.org")

    # Assert
    assert href == "https://qcci.org", f"expected the card to link to https://qcci.org, got {href!r}"
    assert has_tagline, 'expected the tagline "Be Found. Be Trusted. Be Verified." to render'
    assert has_register_now, 'expected the text "Register now" to render'
    assert has_link_text, 'expected the link text "qcci.org" to render'


# ── TC 136080 — B2B Platform card renders correctly in Arabic (RTL) ────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("B2B Platform card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The B2B Platform card renders correctly in Arabic (RTL)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.b2b
@pytest.mark.bilingual
@pytest.mark.pbi_129384
@pytest.mark.traceability("GLOBAL-DYNAMICWIDGETS-TC-136080")
def test_b2b_card_renders_in_arabic_rtl(page):
    # GLOBAL-DYNAMICWIDGETS-TC-136080 | PBI 129384
    # The 3-widget row's RIGHT-TO-LEFT visual mirror is CONFIRMED LIVE and
    # asserted for real; the card's own internal-element mirroring claim
    # (seal graphic moving to the left side, callout/footer reflow) has no
    # live DOM analog (same flat-image gap as TC 135939) and is expected to
    # FAIL HONESTLY.
    # Arrange
    dw = HomeDynamicWidgetsPage(page)

    # Act
    with allure.step("Switch site language to Arabic and load the Home Page"):
        dw.open_home_arabic()

    with allure.step("Read the widgets row's mirrored x-ordering and the B2B card's seal element"):
        x_positions = dw.row_children_x_order()
        has_seal = dw.card_has_descendant(dw.B2B_INDEX, "[class*='seal'], [class*='ribbon'], svg")

    # Assert
    assert x_positions[0] > x_positions[1] > x_positions[2], (
        f"expected the row to mirror right-to-left (weather rightmost, then Marhaba, then B2B), got {x_positions}"
    )
    assert has_seal, "expected the B2B Platform card's seal graphic to mirror to the left side in RTL"

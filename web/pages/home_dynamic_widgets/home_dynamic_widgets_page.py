"""
web/pages/home_dynamic_widgets/home_dynamic_widgets_page.py — HomeDynamicWidgetsPage.

PBI 129384 / QC-HOME-008 "Dynamic Widgets (Weather, Marhaba Guide, B2B)" — its
own Home-page section/module folder per active/standards.md's Home-page
sections table. This pass covers the 34 approved, Automation-tagged,
UI-category, Web-platform cases scoped for this batch (ADO TC 135921-135944,
136069-136080). Control_Panel-tagged cases for this same PBI are out of scope
for this run (see the sibling home_dynamic_widgets_admin_page.py skeleton).

--- CLI-first extraction log ---

`tools/extract_locators.py` (the framework's standard shell extractor) finds
ZERO candidates here — it only harvests interactive/labelled elements
(a/button/input/select/textarea/[role]/[data-testid]/[aria-label]), and this
whole section is built from plain <div>/<span>/<img> nodes with no role or
label:

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find weather
    -> # (no interactive/labelled elements found ...)

Resolved the same documented way as home_promo_banners_page.py and
home_strategic_direction_page.py: one additional, disclosed, scoped
Playwright script (still CLI/shell, never the Playwright MCP), reusing
BasePage's own license-gate/overlay guard sequence, to read the live
DOM/computed-style structure. No Playwright MCP call was needed for this
batch — the environment and every element were reachable deterministically
by script.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home, 1920x1080):

    section.qc-home-dynamic-widgets
      div.qc-dw-inner
        div.qc-dw-row                                   (ROW — flex row, 3 equal columns, 32px gap)
          div.qc-dw-weather                              (WEATHER_COL)
            div.widget.tie-weather-widget.qc-weather-widget   (WEATHER_WIDGET)
              div.widget-title.the-global-title            (WEATHER_TITLE — "Weather")
              div.weather-wrap.is-animated                 (WEATHER_WRAP)
                div.weather-icon-and-city
                  div.weather-icon > svg.qc-weather-icon-svg  (WEATHER_ICON — sun/cloud SVG, condition-driven)
                  div.weather-name.the-subtitle              (WEATHER_CITY — "Doha")
                  div.weather-desc                           (WEATHER_DESC — condition label)
                div.weather-todays-stats
                  div.weather-current-temp                   (WEATHER_TEMP — e.g. "36℃")
                  div.weather-more-todays-stats
                    div.weather_highlow                       (WEATHER_HIGHLOW — "43° - 32°")
                    div.weather_humidty                       (WEATHER_HUMIDITY — "55%")
                    div.weather_wind                          (WEATHER_WIND — "2.7 km/h")
                div.weather-forecast.weather_days_5           (FORECAST_DAYS container — exactly 5)
                  div.weather-forecast-day  x5                 (day: abbr + icon + temp)
                    div.weather-icon > svg
                    div.weather-forecast-day-temp
                    div.weather-forecast-day-abbr
          a.qc-dw-card (1st -> www.qatarchamber.com)        (CARDS[0] — "Marhaba Guide" card)
            img.qc-dw-card-img (object-fit: cover)            (only child — no other DOM node)
          a.qc-dw-card (2nd -> qcci.org)                     (CARDS[1] — "B2B Platform" card)
            img.qc-dw-card-img (object-fit: cover)            (only child — no other DOM node)

Before the weather API resolves, `.qc-dw-weather` contains a real, dedicated
loading-skeleton node instead of the widget markup above:

    <div class="qc-dw-weather" data-qc-weather-widget data-qc-weather-init="1">
      <div class="qc-weather-card qc-weather-card--loading" aria-hidden="true"></div>
    </div>

The widget's live data comes from `GET /o/qc-weather/v1.0/doha` (confirmed via
network-request capture) — the extraction script used `page.route()` on that
exact URL to hold the loading state open for TC 135943, per the batch
instruction to assert the Weather widget's *structure* rather than treat live
API data as stable.

Real, CLI-verified findings reported here (per this batch's Result-integrity
instruction: never silently correct a live measurement to match the case —
script to the case's literal stated value and let a real mismatch FAIL
HONESTLY; only weather-DATA fields, which are explicitly live/dynamic, are
asserted structurally instead of to a literal figure):

  - TC 135921/135937: widget title text is exactly "Weather"; EN homepage
    `<html lang="en-US" dir="ltr">` — Web/EN case is a genuine, confirmed pass.
  - TC 135922: city renders "Doha", `font-weight: 700` (bold) — genuine pass.
  - TC 135923: temperature renders as a single text node combining the
    numeral and the "℃" unit glyph (e.g. "36℃") at `font-weight: 700,
    font-size: 64px` — the large primary numeral claim is a genuine structural
    pass; the LITERAL value "30" is live weather data (confirmed **36℃** at
    extraction time) and is asserted by FORMAT (a "number + degree unit"
    regex), not by the case's literal "30", per this batch's judgment call on
    live/dynamic data.
  - TC 135924: condition label is real and non-empty (confirmed **"Clear
    Sky"** at extraction time, not the case's stated "Light Rain" — live
    weather data) — asserted for non-empty presence, not the literal string.
  - TC 135925: the icon is a real inline SVG (`qc-weather-icon-svg`) whose
    internal shape changes with the live condition (confirmed a sun-only
    ray+circle glyph for "Clear Sky", not a cloud+sun combination) — asserted
    structurally (a non-empty SVG renders), not the literal "cloud+sun" shape,
    since the shape is condition-driven live data.
  - TC 135926: high/low renders as `"<hi>° - <lo>°"` (confirmed **"43° -
    32°"**, not the case's stated "30°-24°" — live data) — asserted by a
    "high-degree - low-degree" format regex, not the literal figures.
  - TC 135927 (explicit design-vs-spec gap): humidity is confirmed LIVE as
    **"55%"**, not the case's literal "27%". Per this batch's explicit
    instruction for the two design-vs-spec-flagged cases, this is scripted
    against the case's literal stated "27%" and will FAIL HONESTLY — not
    silently corrected to "55%".
  - TC 135928 (explicit design-vs-spec gap): wind speed is confirmed LIVE as
    **"2.7 km/h"**, not the case's literal "6.25 km/h". Scripted against the
    case's literal "6.25 km/h" for the same reason — FAILS HONESTLY.
  - TC 135929: at a 1320px viewport the weather card measures **394.67 x
    358.6px** (confirmed via `getBoundingClientRect()`), not the case's
    stated 362px height — a real, measured mismatch, scripted to the case's
    literal 362px.
  - TC 135930: at 1320px viewport, `.qc-dw-row` is a fixed **1248px** wide
    flex row (not 1320px) with **32px** gaps (not 24px) and 3 equal
    **394.67px** columns (not ~424px) — real, measured mismatches, scripted
    to the case's literal tokens.
  - TC 135931: `.weather-wrap` (the real internal content box) computes
    padding **15px 12px 20px** (not the case's stated 24px/20px), `gap:
    normal` (`display: block`, not a flex/grid gap — there is no discrete
    16px internal gap token live), and the outer widget's `border-radius` is
    **16px**, which DOES match the case's stated corner radius exactly.
  - TC 135932: CONFIRMED LIVE — the weather widget's background computes to
    `rgb(145, 23, 49)` (**#911731**), a genuine dark red/maroon — a real,
    matching pass (the case only names the color qualitatively, not a hex).
  - TC 135933/135934: CONFIRMED LIVE — exactly 5 forecast-day entries,
    labeled Mon/Tue/Wed/Thu/Fri in that order, each with a day-name text
    node, an inline SVG icon, and a temperature text node — genuine passes.
  - TC 135936: CONFIRMED LIVE (AR, https://qcdev.ihorizons.com/ar/home):
    `<html dir="rtl">`, widget title "الطقس", city "الدوحة" (a genuine,
    stable EN->AR pass — the city name is static site copy, not live data),
    forecast day labels translated ("إثنين", "ثلاثاء", ...), and the
    condition label renders non-empty Arabic text (confirmed "صحو" at
    extraction time — itself live/dynamic data, asserted for
    presence/non-emptiness in Arabic, not a literal string).
  - TC 135943: CONFIRMED LIVE — `.qc-dw-weather` renders a dedicated
    `.qc-weather-card--loading` skeleton node (not a blank/broken layout)
    immediately after `domcontentloaded`, before the
    `/o/qc-weather/v1.0/doha` XHR resolves and replaces it with the real
    widget markup. `delay_weather_api_and_reload()` below holds that XHR open
    with `page.route()` so the test can observe the skeleton deterministically
    (no arbitrary `sleep`).
  - TC 135944: CONFIRMED LIVE — the weather widget's bounding box
    (394.67 x 358.6px) is byte-identical before and after a mouse hover; no
    layout shift, no overflow.
  - TC 135938/135939 (Marhaba / B2B card structure) — a REAL, LIVE-CONFIRMED
    STRUCTURAL GAP, not a scripting choice: both cards are a single
    `<a class="qc-dw-card"><img class="qc-dw-card-img"></a>` with **no other
    descendant DOM node at all** — no separate logo element, no badge/seal
    graphic element, no heading/body/feature-item/CTA/footer text nodes
    anywhere in the live markup. Everything the case describes (heading,
    body copy, feature items, CTA button, footer with website/phone/social
    icons, logo, badge/seal graphic) is baked into the single PNG the `<img>`
    points at — confirmed by walking the full subtree (`el.children.length`
    is 0 on the `<img>`, and the `<a>` has exactly one child). What IS real
    and asserted: the card's bounding box, `border-radius`, the image's `src`
    (confirms which image — "directory...png" for Marhaba, "b2b-verified...
    png" for B2B) and `href` (qatarchamber.com / qcci.org respectively), and
    the image's `object-fit` computed style, which is **"cover"**, not the
    case's stated "STRETCH" fill.
  - TC 135940/135941/136069-136073/136075-136079 (Marhaba/B2B text, graphic,
    and footer content cases) — the SAME real structural gap as above: none
    of the specific text/graphic elements these cases assert on
    (heading, body text, feature items, CTA button, badge/seal graphic,
    footer website/phone/social row) exist as discoverable DOM nodes at all
    — they are pixels inside the single flat PNG. Each is scripted per the
    case's literal expected result (a scoped `get_by_text()` /
    `card_has_descendant()` query against the real, confirmed-empty
    subtree) and will FAIL HONESTLY, reporting a genuine, disclosed
    content-implementation gap — not a locator defect, and not silently
    corrected or skipped.
  - TC 135939 (B2B card structure) also live-confirms a maroon dark-red
    "dotted background pattern" is NOT independently verifiable via DOM (same
    flat-image gap) — asserted only on the real, structural pieces above.
  - TC 136074/136080 (Marhaba/B2B RTL) — CONFIRMED LIVE: the DOM order of the
    3 `.qc-dw-row` children is unchanged between EN and AR, but the row's
    layout genuinely mirrors visually under `dir="rtl"` (EN x-order
    weather(336) -> Marhaba(762) -> B2B(1189); AR x-order
    B2B(335) -> Marhaba(762) -> weather(1189) — a real, confirmed
    right-to-left visual reorder). That row-level mirror is asserted as a
    genuine pass; the case's specific internal-element mirroring claims
    (logo moves top-right, badge/seal graphic moves to the left side, footer
    icon order reverses) have no live DOM analog for the same flat-image
    reason as above, and are scripted to FAIL HONESTLY against the confirmed-
    absent sub-elements.
"""

import threading

from core.web.base_page import BasePage
from config.settings import web_url

# ── Weather-widget live-data API (confirmed via network-request capture) ────
WEATHER_API_URL_PATTERN = "**/o/qc-weather/v1.0/**"


class HomeDynamicWidgetsPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    SECTION = ".qc-home-dynamic-widgets"
    ROW = ".qc-dw-row"
    WEATHER_COL = ".qc-dw-weather"
    WEATHER_LOADING = ".qc-dw-weather .qc-weather-card--loading"
    WEATHER_WIDGET = ".qc-dw-weather .widget"
    WEATHER_TITLE = ".qc-dw-weather .widget-title"
    WEATHER_WRAP = ".weather-wrap"
    WEATHER_CITY = ".weather-name"
    WEATHER_DESC = ".weather-desc"
    WEATHER_TEMP = ".weather-current-temp"
    WEATHER_ICON = ".weather-icon-and-city .weather-icon"
    WEATHER_ICON_SVG = ".weather-icon-and-city .weather-icon svg"
    WEATHER_HIGHLOW = ".weather_highlow"
    WEATHER_HUMIDITY = ".weather_humidty"
    WEATHER_WIND = ".weather_wind"
    FORECAST_DAY = ".weather-forecast-day"
    CARD = ".qc-dw-row a.qc-dw-card"
    CARD_IMG = ".qc-dw-card-img"
    HTML_ROOT = "html"

    # Card row order: index 0 = Marhaba Guide ("Commercial & Industrial
    # Directory" -> qatarchamber.com), index 1 = B2B Platform (-> qcci.org).
    MARHABA_INDEX = 0
    B2B_INDEX = 1

    _STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "color: cs.color, backgroundColor: cs.backgroundColor, fontWeight: cs.fontWeight,"
        "fontSize: cs.fontSize, borderRadius: cs.borderRadius, padding: cs.padding,"
        "paddingTop: cs.paddingTop, paddingRight: cs.paddingRight,"
        "paddingBottom: cs.paddingBottom, paddingLeft: cs.paddingLeft,"
        "gap: cs.gap, display: cs.display, objectFit: cs.objectFit,"
        "direction: cs.direction"
        "}; }"
    )

    def _style(self, locator) -> dict:
        loc = locator if hasattr(locator, "evaluate") else self.page.locator(locator).first
        return loc.evaluate(self._STYLE_JS)

    def _box(self, locator) -> dict | None:
        loc = locator if hasattr(locator, "bounding_box") else self.page.locator(locator).first
        return loc.bounding_box()

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeDynamicWidgetsPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        self.wait_for(self.WEATHER_WIDGET)
        return self

    def open_home_arabic(self) -> "HomeDynamicWidgetsPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        self.wait_for(self.WEATHER_WIDGET)
        return self

    def scroll_to_section(self) -> "HomeDynamicWidgetsPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def page_lang(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("lang")

    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    # ── Row / column geometry ────────────────────────────────────────────
    def row_box(self) -> dict:
        return self._box(self.ROW)

    def row_style(self) -> dict:
        return self._style(self.ROW)

    def row_children_x_order(self) -> list:
        """x-position of each `.qc-dw-row` child, in DOM order — used to
        confirm the visual RTL mirror (see docstring, TC 136074/136080)."""
        return self.page.locator(f"{self.ROW} > *").evaluate_all(
            "els => els.map(el => el.getBoundingClientRect().x)"
        )

    # ── Weather widget ───────────────────────────────────────────────────
    def is_weather_widget_visible(self) -> bool:
        return self.is_visible(self.WEATHER_WIDGET)

    def is_weather_loading_placeholder_visible(self) -> bool:
        return self.is_visible(self.WEATHER_LOADING)

    def weather_widget_box(self) -> dict:
        return self._box(self.WEATHER_WIDGET)

    def weather_widget_style(self) -> dict:
        return self._style(self.WEATHER_WIDGET)

    def weather_wrap_style(self) -> dict:
        return self._style(self.WEATHER_WRAP)

    def widget_title_text(self) -> str:
        return self.text(self.WEATHER_TITLE)

    def city_text(self) -> str:
        return self.text(self.WEATHER_CITY)

    def city_style(self) -> dict:
        return self._style(self.WEATHER_CITY)

    def condition_text(self) -> str:
        return self.text(self.WEATHER_DESC)

    def temp_text(self) -> str:
        return self.text(self.WEATHER_TEMP)

    def temp_style(self) -> dict:
        return self._style(self.WEATHER_TEMP)

    def is_icon_svg_rendered(self) -> bool:
        return self.page.locator(self.WEATHER_ICON_SVG).count() > 0

    def highlow_text(self) -> str:
        return self.text(self.WEATHER_HIGHLOW)

    def humidity_text(self) -> str:
        return self.text(self.WEATHER_HUMIDITY)

    def wind_text(self) -> str:
        return self.text(self.WEATHER_WIND)

    def forecast_day_count(self) -> int:
        return self.page.locator(self.FORECAST_DAY).count()

    def forecast_days(self) -> list:
        return self.page.locator(self.FORECAST_DAY).evaluate_all(
            "els => els.map(el => ({"
            "abbr: el.querySelector('.weather-forecast-day-abbr')?.textContent.trim() || null,"
            "temp: el.querySelector('.weather-forecast-day-temp')?.textContent.trim() || null,"
            "hasIcon: !!el.querySelector('.weather-icon svg')"
            "}))"
        )

    def hover_weather_widget(self) -> None:
        self.page.locator(self.WEATHER_WIDGET).hover()

    def delay_weather_api_and_reload(self) -> bool:
        """Holds the live weather XHR (`/o/qc-weather/v1.0/...`) open on a
        `threading.Event` via Playwright's own `page.route()` interception —
        no `time.sleep()` anywhere on this path. The route handler runs on
        Playwright's own dispatch thread, so blocking it on `release.wait()`
        does not block the main test thread; the main thread instead uses an
        explicit `wait_for(state="visible")` (real wait, no arbitrary delay)
        to confirm the loading skeleton actually rendered, then releases the
        held request so the widget can finish loading normally (TC 135943)."""
        release = threading.Event()

        def _hold_request(route):
            release.wait(timeout=10)
            route.continue_()

        self.page.route(WEATHER_API_URL_PATTERN, _hold_request)
        try:
            self.open_home_partial()
            self.wait_for(self.WEATHER_LOADING, state="visible", timeout=5000)
            seen_loading = self.is_weather_loading_placeholder_visible()
        finally:
            release.set()
            self.page.unroute(WEATHER_API_URL_PATTERN, _hold_request)
        return seen_loading

    def open_home_partial(self) -> None:
        """Like open_home(), but does NOT wait for the widget to finish
        loading — used only by delay_weather_api_and_reload() above, which
        needs to observe the still-loading state."""
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)

    # ── Marhaba Guide / B2B Platform cards ───────────────────────────────
    def card_locator(self, index: int):
        return self.page.locator(self.CARD).nth(index)

    def card_box(self, index: int) -> dict:
        return self._box(self.card_locator(index))

    def card_style(self, index: int) -> dict:
        return self._style(self.card_locator(index))

    def card_img_src(self, index: int) -> str:
        return self.card_locator(index).locator(self.CARD_IMG).get_attribute("src") or ""

    def card_img_object_fit(self, index: int) -> str:
        return self._style(self.card_locator(index).locator(self.CARD_IMG))["objectFit"]

    def card_href(self, index: int) -> str:
        return self.card_locator(index).get_attribute("href") or ""

    def card_contains_visible_text(self, index: int, text: str) -> bool:
        """Bounded, never-throwing text-presence check scoped to one card —
        used to assert the case's literal expected copy. Returns False
        (never raises) when the text genuinely isn't in the live DOM, which
        is the real, confirmed state for the Marhaba/B2B cards (see
        docstring) rather than a locator defect."""
        try:
            return self.card_locator(index).get_by_text(text, exact=False).first.is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible()'s contract
            return False

    def card_has_descendant(self, index: int, css: str) -> bool:
        """True if the card's `<a>` contains any element matching `css`
        besides its single `<img>` — used to assert the case's claimed
        sub-elements (logo, badge/seal graphic, CTA button, footer row)."""
        return self.card_locator(index).locator(css).count() > 0

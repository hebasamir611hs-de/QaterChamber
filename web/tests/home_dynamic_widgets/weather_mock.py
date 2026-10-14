"""Weather API helpers for PBI 129384's web cases.

Read live 2026-10-08 (GET /o/qc-weather/v1.0/doha and
/o/qc-weather-widget/qc-weather.js?v=2, both anonymous):

  - Response contract: {"city", "current": {"temp", "code", "humidity", "wind"},
    "daily": [{"date": "YYYY-MM-DD", "code", "min", "max"}, ...5]}; `code` is a
    WMO weather code (the wrapper proxies Open-Meteo server-side).
  - The widget maps the code to the label/icon client-side (`describe()`):
    0 Clear Sky (sun), 1-2 Partly Cloudy (sun+cloud), 3 Cloudy, 45/48 Fog,
    51-57 Light Rain (cloud+drops), 61-67 Rain, 80-82 Showers, 95+ Thunderstorm.
  - High/low renders "<max>° - <min>°" from daily[0]; humidity "<n>%"; wind
    "<round(w,2)> km/h"; day names from each date's getDay() in the browser.
  - `fetch()` has NO timeout/AbortController and the widget never refreshes
    on a timer: it renders once per page load (and on Senna `endNavigate`).
    Any non-OK response or malformed payload -> the bilingual fallback.

`patch_handler()` fetches the REAL response and overwrites only the fields a
case names, so the rendering of the case's own values is asserted on the
live contract.
"""

from __future__ import annotations

import datetime as _dt
import json

URL_PATTERN = "**/o/qc-weather/v1.0/**"
CLIENT_TIMEOUT_S = 60     # no client timeout exists; this is how long a hung call is observed
CLIENT_REFRESH_S = 0      # no in-page refresh cycle exists

LABEL_TO_CODE = {"Clear Sky": 0, "Partly Cloudy": 2, "Cloudy": 3, "Fog": 45, "Light Rain": 51,
                 "Rain": 61, "Snow": 71, "Showers": 80, "Thunderstorm": 95}
_DAY = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

TEMPLATE = {"city": "Doha", "current": {"temp": 30, "code": 51, "humidity": 27, "wind": 6.25},
            "daily": [{"date": "2026-10-12", "code": 51, "min": 24, "max": 30},
                      {"date": "2026-10-13", "code": 2, "min": 24, "max": 31},
                      {"date": "2026-10-14", "code": 0, "min": 25, "max": 32},
                      {"date": "2026-10-15", "code": 3, "min": 25, "max": 31},
                      {"date": "2026-10-16", "code": 61, "min": 24, "max": 29}]}


def describe(code: int) -> str:
    c = int(code)
    if c == 0:
        return "Clear Sky"
    if c in (1, 2):
        return "Partly Cloudy"
    if c == 3:
        return "Cloudy"
    if c in (45, 48):
        return "Fog"
    if 51 <= c <= 57:
        return "Light Rain"
    if 61 <= c <= 67:
        return "Rain"
    if 71 <= c <= 77:
        return "Snow"
    if 80 <= c <= 82:
        return "Showers"
    if c in (85, 86):
        return "Snow Showers"
    if c >= 95:
        return "Thunderstorm"
    return "Cloudy"


def displayed_values(payload: dict) -> dict:
    cur = payload["current"]
    return {"temp": round(float(cur["temp"])), "condition": describe(cur["code"])}


def _week_from(first_day: str, n: int) -> list[str]:
    today = _dt.date.today()
    start = today + _dt.timedelta(days=(_DAY[first_day] - today.weekday()) % 7)
    return [(start + _dt.timedelta(days=i)).isoformat() for i in range(n)]


def patch(payload: dict, *, temp=None, condition=None, high=None, low=None, humidity=None, wind=None,
          days=None, keep_days=None) -> dict:
    p = json.loads(json.dumps(payload))
    if temp is not None:
        p["current"]["temp"] = temp
    if condition is not None:
        p["current"]["code"] = LABEL_TO_CODE[condition]
    if high is not None:
        p["daily"][0]["max"] = high
    if low is not None:
        p["daily"][0]["min"] = low
    if humidity is not None:
        p["current"]["humidity"] = humidity
    if wind is not None:
        p["current"]["wind"] = wind
    if days:
        for d, iso in zip(p["daily"], _week_from(days[0], len(days))):
            d["date"] = iso
    if keep_days is not None:
        p["daily"] = p["daily"][:keep_days]
    return p


def patch_handler(**values):
    def handler(route):
        try:
            real = route.fetch()
            payload = real.json() if real.ok else TEMPLATE
        except Exception:  # noqa: BLE001 — provider down: the case's values still render from the template
            payload = TEMPLATE
        route.fulfill(status=200, content_type="application/json", body=json.dumps(patch(payload, **values)))
    return handler


def icon_kind(svg_html: str) -> str:
    """Classify the main icon by the glyph parts qc-weather.js composes."""
    h = svg_html.lower()
    sun = "#f6a623" in h and "<circle" in h
    cloud = "m13 34h19" in h
    drops = "qc-ico-drops" in h
    if cloud and sun:
        return "cloud-sun"
    if cloud and drops:
        return "rain"
    if sun:
        return "sun"
    return "cloud" if cloud else "unknown"

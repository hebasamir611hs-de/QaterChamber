"""
web/pages/home_featured_event/home_featured_event_page.py —
HomeFeaturedEventPage.

Web/public Page Object for PBI 129382 (Home Page "Upcoming Event Pins") —
the Home Page's single featured-event card, confirmed live this session
(2026-08-31, Playwright MCP session against `https://qcdev.ihorizons.com`).

CONFIRMED LIVE STRUCTURE
  - `section.qc-home-upcoming-event` — a real, stable CSS class. Client-
    rendered: confirmed live the section exists in the DOM immediately but
    its inner fields (`[data-qc-ue-title]` etc.) are empty until the
    client-side script populates them ~1.5-2s after page load, per the
    task's own carried-over exploration; RELOAD_POLL_* below give that
    margin plus this project's usual safety margin.
  - Card fields: `[data-qc-ue-title]`, `[data-qc-ue-date]`,
    `[data-qc-ue-time]`, `[data-qc-ue-location]`, `[data-qc-ue-media]`
    (an `<a>` whose `href` carries `?id=<eventId>` — confirmed live this is
    the SAME query-string format as the admin's Pinned Event field, and the
    only URL format that resolves to a real event page on this site at
    all — see home_featured_event_admin_page.py's module docstring).
  - VISIBILITY MECHANISM — confirmed live this session: the section is
    NEVER removed from the DOM. When the singleton's Active Status is
    OFF, the section keeps rendering (with all its static heading/label
    text) but gets an inline `style="display:none;"` on the outer
    `section.qc-home-upcoming-event` element itself — its `[data-qc-ue-*]`
    fields also render empty text in that state. `is_section_visible()`
    below checks the ACTUAL rendered visibility (Playwright's own
    `is_visible()`, which already accounts for `display:none`), not mere
    DOM presence — a `locator(...).count() > 0` check would silently pass
    even when the section is Active=No and hidden.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeFeaturedEventPage(BasePage):
    HOME_PATH = "/en/home"

    SECTION = "section.qc-home-upcoming-event"
    TITLE = f'{SECTION} [data-qc-ue-title]'
    DATE = f'{SECTION} [data-qc-ue-date]'
    TIME = f'{SECTION} [data-qc-ue-time]'
    LOCATION = f'{SECTION} [data-qc-ue-location]'
    MEDIA_LINK = f'{SECTION} [data-qc-ue-media]'

    # Client-rendered ~1.5-2s after page load (see module docstring) plus a
    # safety margin, mirrored on the same conservative starting-point
    # pattern already adopted project-wide (HomeBusinessEventsPage etc.)
    # pending a per-endpoint re-measurement.
    RELOAD_POLL_TIMEOUT_MS = 8000
    RELOAD_POLL_INTERVAL_MS = 500
    RENDER_SETTLE_MS = 2000

    def open_home(self) -> "HomeFeaturedEventPage":
        self.open(web_url(self.HOME_PATH))
        self.wait_for(self.SECTION, state="attached")
        # Client-render settle grace — see module docstring.
        self.page.wait_for_timeout(self.RENDER_SETTLE_MS)
        return self

    def is_section_visible(self) -> bool:
        """Real rendered visibility (accounts for the confirmed-live
        `display:none` toggle) — NOT mere DOM presence. See module
        docstring's VISIBILITY MECHANISM note."""
        return self.is_visible(self.SECTION)

    def current_title(self) -> str:
        return self.text(self.TITLE).strip()

    def current_media_href(self) -> str:
        return self.page.locator(self.MEDIA_LINK).get_attribute("href") or ""

    def reload_until(self, predicate, timeout_ms: int | None = None, interval_ms: int | None = None) -> bool:
        """Poll open_home() + predicate(self) until True or timeout —
        mirrors HomeBusinessEventsPage.reload_until()'s shape (poll, never
        a bare sleep)."""
        import time

        timeout_ms = timeout_ms if timeout_ms is not None else self.RELOAD_POLL_TIMEOUT_MS
        interval_ms = interval_ms if interval_ms is not None else self.RELOAD_POLL_INTERVAL_MS
        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home()
            if predicate(self):
                return True
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(interval_ms)

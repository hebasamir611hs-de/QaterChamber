"""
web/pages/home_promo_banners/home_promo_banners_page.py —
HomePromoBannersPage.

Web/public Page Object for PBI 129368 (QC-HOME-002 — Promotional Banners /
Ad Slots) — the Home Page's promotional-banners carousel. Counterpart to
cms/pages/home_promo_banners/home_promo_banners_admin_page.py.

CONFIRMED LIVE STRUCTURE (2026-09-02, headless Chromium against
qcdev's public Home Page, no auth):
  - `section.qc-home-promotional-banners` — real, stable CSS class,
    confirmed visible in the DOM on page load (server-rendered content for
    this coupled/traditional Liferay project per cms-profile.md — not
    client-fetched like the Upcoming Event Pins widget).
  - Carousel structure: `.qc-promo-carousel` > `.qc-promo-viewport` >
    `.qc-promo-track` > repeated `.qc-promo-slide` > `.qc-promo-link` >
    `.qc-promo-img` (an `<img>` whose `alt` attribute carries the banner's
    Banner Alt Text (EN) value — confirmed live this is the reliable way to
    identify a specific banner among the slides, mirroring
    HomeCommunityPartnersPage's own alt-text-keyed lookup for its logo
    carousel).
  - The carousel infinite-loops (confirmed live: slide count observed
    exceeds the distinct active banner count, cloned slides repeat the same
    alt/src pairs for the loop illusion) — `banner_visible(alt_text)` below
    checks for ANY matching slide, not a specific index.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomePromoBannersPage(BasePage):
    HOME_PATH = "/en/home"

    SECTION = "section.qc-home-promotional-banners"
    SLIDE = f"{SECTION} .qc-promo-slide"
    IMG = f"{SECTION} .qc-promo-img"

    # Borrowed from cms-profile.md's ONLY measured propagation budget
    # (~0s / 5s-timeout / 0.5s-interval, Board Members JAX-RS endpoint) —
    # NOT independently re-measured for this content type. Per the
    # profile's own "re-probe before assuming it generalizes" note, this is
    # a disclosed placeholder budget, not a confirmed one for Promotional
    # Banners specifically.
    RELOAD_POLL_TIMEOUT_MS = 5000
    RELOAD_POLL_INTERVAL_MS = 500

    def open_home(self) -> "HomePromoBannersPage":
        self.open(web_url(self.HOME_PATH))
        self.wait_for(self.SECTION, state="attached")
        return self

    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def banner_visible(self, alt_text_en: str) -> bool:
        """True if any carousel slide (including cloned loop slides) renders
        an image whose alt text matches. Uses Playwright's own is_visible()
        (not mere DOM presence) so a banner hidden behind
        Active Status=False is correctly reported absent."""
        try:
            locator = self.page.locator(f'{self.IMG}[alt="{alt_text_en}"]')
            return locator.first.is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's never-throws contract
            return False

    def reload_until(self, predicate, timeout_ms: int | None = None, interval_ms: int | None = None) -> bool:
        """Poll open_home() + predicate(self) until True or timeout — never
        a bare sleep. Mirrors HomeFeaturedEventPage.reload_until()'s shape."""
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

    def reload_until_banner_matches(self, alt_text_en: str, expected_visible: bool,
                                     timeout_ms: int | None = None) -> bool:
        return self.reload_until(
            lambda p: p.banner_visible(alt_text_en) == expected_visible,
            timeout_ms=timeout_ms,
        )

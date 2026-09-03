"""
web/pages/home_services/home_services_page.py — HomeServicesPage.

Web/public Page Object for PBI 129371 (QC-HOME-005 — Our Services Section)
— the Home Page's "Services We Provide" section. Counterpart to
cms/pages/home_services/home_services_admin_page.py.

CONFIRMED LIVE STRUCTURE (2026-09-02, headed Chromium via Playwright MCP
against qcdev's public Home Page, no auth):
  - `section.qc-home-our-services` — real, stable CSS class, confirmed
    present in the DOM on page load.
  - Tab strip: `.qc-os-tabs` (confirmed live class) containing `[role="tab"]`
    elements (`.qc-os-tab`) with real, confirmed-live text content: "All
    Services", "Membership", "Legal", "E-Services", "Information" — no tab
    literally named "Information Services" exists on this environment (see
    home_services_admin_page.py's TAB NAMING NOTE for the ADO-135351
    wording mismatch and how it's handled).
  - Clicking a tab re-renders the section's card list live (confirmed:
    "All Services" shows 8 cards in the DOM; clicking "Information"
    replaces the DOM with only the 2 cards assigned to that tab — this is a
    real client/server round-trip, not a client-side show/hide of a
    pre-rendered full set, so no `display:none` filtering assumption is
    made here).
  - Card structure: `article.qc-os-card` > `.qc-os-card-title` (an `<h3>`
    carrying the card's Title field value) — confirmed live the reliable
    way to identify a specific card among a tab's results.
  - A second, `role="tablist"][aria-label="Select service"]` dot-strip
    (one dot per card, e.g. "Service 1".."Service 8") also lives inside
    `section.qc-home-our-services` but is confirmed live `display:none` at
    both a ~1060px and the framework's 1920x1080 viewport — a mobile-only
    carousel-indicator alternate presentation, not active at Full HD. Not a
    pagination risk for `card_visible()` at this framework's viewport.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeServicesPage(BasePage):
    HOME_PATH = "/en/home"

    SECTION = "section.qc-home-our-services"
    TABLIST = f"{SECTION} .qc-os-tabs"
    TAB = f'{TABLIST} [role="tab"]'
    CARD = f"{SECTION} .qc-os-card"
    CARD_TITLE = f"{CARD} .qc-os-card-title"

    # Borrowed from cms-profile.md's ONLY measured propagation budget
    # (~0s / 5s-timeout / 0.5s-interval, Board Members JAX-RS endpoint) —
    # NOT independently re-measured for this content type. Disclosed
    # placeholder budget, matching HomePromoBannersPage's own note.
    RELOAD_POLL_TIMEOUT_MS = 5000
    RELOAD_POLL_INTERVAL_MS = 500

    def open_home(self) -> "HomeServicesPage":
        self.open(web_url(self.HOME_PATH))
        self.wait_for(self.SECTION, state="attached")
        return self

    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def open_tab(self, tab_label: str) -> "HomeServicesPage":
        """Click a real, confirmed-live tab (e.g. "Information") and wait
        for it to actually become the selected tab before returning.

        Confirmed live (2026-09-02): the tab switch flips `aria-selected`
        on the clicked tab synchronously with the click (client-side), and
        separately re-renders the section's card list (8 cards under "All
        Services" -> 2 under "Information", confirmed live) — that
        re-render may not produce any network activity, so
        `wait_for_load_state("networkidle")` alone can resolve before the
        new card list is actually in the DOM and read the PREVIOUS tab's
        cards. Waiting on `aria-selected="true"` on the target tab is the
        real, confirmed-live signal this framework's assertions rely on.
        """
        tab = self.page.locator(f'{self.TAB}:text-is("{tab_label}")')
        tab.click()
        self.page.locator(f'{self.TAB}:text-is("{tab_label}")[aria-selected="true"]').wait_for(
            state="attached", timeout=10000
        )
        self.page.wait_for_load_state("networkidle")
        return self

    def card_titles(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.CARD_TITLE).all_inner_texts()]

    def card_visible(self, title: str) -> bool:
        try:
            locator = self.page.locator(f'{self.CARD_TITLE}:text-is("{title}")')
            return locator.first.is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's never-throws contract
            return False

    def reload_until(self, predicate, timeout_ms: int | None = None, interval_ms: int | None = None) -> bool:
        """Poll open_home() + predicate(self) until True or timeout — never
        a bare sleep. Mirrors HomePromoBannersPage.reload_until()'s shape."""
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

    def reload_until_card_visible_under_tab(self, tab_label: str, title: str,
                                             expected_visible: bool,
                                             timeout_ms: int | None = None) -> bool:
        def _predicate(p: "HomeServicesPage") -> bool:
            p.open_tab(tab_label)
            return p.card_visible(title) == expected_visible

        return self.reload_until(_predicate, timeout_ms=timeout_ms)

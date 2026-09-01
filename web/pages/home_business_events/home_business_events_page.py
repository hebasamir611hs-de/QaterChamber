"""
web/pages/home_business_events/home_business_events_page.py —
HomeBusinessEventsPage.

Web/public Page Object for PBI 129383 (Business Events auto-sync) — the Home
Page "Business Events" section, confirmed live this session (2026-08-31,
unauthenticated Playwright MCP session against
`https://qcdev.ihorizons.com/en/home`) via a scoped CLI extraction
(`tools/extract_locators.py --scope "[aria-label*='Business event']"`,
followed by a direct outerHTML dump of the section for the parts the
extractor's role-based candidates don't cover, e.g. the pagination dots and
card body structure).

CONFIRMED LIVE STRUCTURE
  - The whole section is `section.qc-home-business-events` — a real, stable
    CSS class (not a `data-testid`, but confirmed unique on the page and
    semantically named, unlike the generic Bootstrap-utility classes seen
    elsewhere on this project's public pages).
  - Category tablist: `[role="tablist"][aria-label="Business event category
    filter"]` with three `role="tab"` buttons: "All" (`data-qc-be-filter="all"`,
    default-active), "Chamber Events" (`data-qc-be-filter="chamberEvents"`),
    "Global Events" (`data-qc-be-filter="globalEvents"`). `get_by_role("tab",
    name="All")` alone is NON-UNIQUE on this page (4 matches confirmed via
    the CLI extractor — other tablists elsewhere reuse the same tab label) —
    every tab locator below is scoped through TABLIST first.
  - Clicking a category tab RE-RENDERS the DOM, not just toggles visibility
    — confirmed live: `.qc-be-card-title` count on the page dropped from 9
    (all cards) to 6 immediately after clicking the "Chamber Events" tab, and
    the surviving 6 titles were exactly the Chamber-Events-tagged cards. A
    plain `.count()` / `.all_text_contents()` on CARD_TITLE after a tab
    click is therefore a correct "what's under this tab" check with no
    `:visible` filtering needed.
  - PAGINATION: `[role="tablist"][aria-label="Business events pages"]`
    (`.qc-be-dots`, one `role="tab"` button per page, `aria-label="Page N"`)
    controls a CSS-transform carousel (`.qc-be-track` `translateX`) — but
    confirmed live, ALL cards for the active tab are already present in the
    DOM simultaneously (`cardCount` was 9 for "All" with the pager showing
    "Page 1/2/3" dots, before any dot was clicked). This means a card-
    presence assertion via `CARD_TITLE`/`card_link_for_id()` does NOT need
    to click through pagination dots to "reach" a later page — the task
    brief's "check all pagination pages" concern is already satisfied by a
    DOM-wide query; the dots only change which cards are scrolled into
    visual view, not which are queryable. Kept PAGE_DOT()/dot count as a
    Page Object method regardless, for a test that wants to assert the
    pager itself, but the presence-check flows below do not depend on it.
  - Each card: `a.qc-be-card` with `href="/web/qatar-chamber/events/event?id=<N>"`,
    containing `.qc-be-card-badges` (`.qc-be-badge--category` /
    `.qc-be-badge--sector` chips), `h3.qc-be-card-title`, and
    `.qc-be-card-meta` date/time/location lines. `CARD_BY_ID()` matches on
    the `?id=` query param (not title substring) to avoid the exact
    collision risk flagged in the task brief (an existing "SME Growth &
    Innovation Summit" record vs. a test-created "...SME Growth Summit"
    title) — confirmed live this session that both a real, pre-existing
    "SME Growth & Innovation Summit" card and event ids are independently
    addressable this way. `CARD_TITLE_EXACT()` is the `:text-is()`
    fallback the brief also called out, for callers that only have a title
    (e.g. immediately after Save, before the created record's id is known
    on the public side).
  - "View all" link: `a.qc-be-viewall[href="/web/qatar-chamber/events"]` —
    the full, non-paginated listing page the task brief also asks to check.
    A separate Page Object for that listing page was NOT built this
    session (out of scope — the DOM-wide-query finding above means neither
    TC's assertions need it to reach a later home-page pagination page);
    VIEW_ALL_LINK is provided so a future test can navigate there directly
    if a card is ever NOT found in the home section's own DOM.

MEASURED (2026-09-01, live against qcdev, single Playwright MCP browser
session, throwaway `QCTEST-PROBE-BE-0901` record — created, published,
confirmed visible, then unpublished, per cms-profile.md's UI-only
teardown policy; the probe record was deleted via the admin list's own
kebab -> Delete -> confirm flow at the end of this session, confirmed zero
matches afterward):
  - Publish -> appearance in this section: first poll (page reload +
    `has_card_with_exact_title()`) already showed the card at **1728ms**
    after Save committed (the URL gained `externalReferenceCode=`) — an
    UPPER BOUND, not resolved any tighter (polling was ~1s-interval by
    design here to avoid corrupting the measurement with extra Playwright
    MCP round-trips; see the sibling admin Page Object's SAVE_COMMIT note
    on why the URL-marker check, not a flat sleep, is the real "committed"
    signal).
  - Unpublish -> removal from this section: first poll after clicking Save
    on Status=Unpublished (plus the same ~500ms settle used for the
    persisted-URL check) already showed the card GONE at **~2.3s total**
    from the Save click — again an UPPER BOUND, not resolved tighter.
  - Both directions are consistent with cms-profile.md's existing Board
    Members finding (near-instant, no intermediate cache observed) — but
    per that file's own explicit warning ("re-probe before assuming it
    generalizes"), this is a SEPARATE, per-content-type measurement, not
    an inference from that other data source.
  - The prior TC 135748 pytest failure ("card still present after 5000ms
    of polling") was NOT reproduced by this live probe at any comparable
    timeout — the live propagation itself is fast. The most likely
    explanation is test-infra/render variance (page-load time under a
    real pytest/browser run, not raw server-side propagation) eating into
    a 5s budget that has almost no margin once the actual ~2s propagation
    is accounted for. `UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS` below widens
    that ONE call site's margin (a ~6.5x multiple over the measured ~2.3s
    upper bound) without touching the shared `RELOAD_POLL_TIMEOUT_MS`
    default, which backs the (unfailing, separately-measured-fast)
    publish-appearance call sites in both TC 135747 and TC 135748's own
    pre-condition check.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeBusinessEventsPage(BasePage):
    HOME_PATH = "/en/home"

    SECTION = "section.qc-home-business-events"
    CATEGORY_TABLIST = f'{SECTION} [role="tablist"][aria-label="Business event category filter"]'
    PAGE_TABLIST = f'{SECTION} [role="tablist"][aria-label="Business events pages"]'
    CARD = f"{SECTION} a.qc-be-card"
    CARD_TITLE = f"{SECTION} .qc-be-card-title"
    CARD_CATEGORY_BADGE = ".qc-be-badge--category"
    CARD_SECTOR_BADGE = ".qc-be-badge--sector"
    VIEW_ALL_LINK = f'{SECTION} a.qc-be-viewall'
    FULL_LISTING_PATH = "/web/qatar-chamber/events"

    # Confirmed-live category filter tab values.
    TAB_ALL = "All"
    TAB_CHAMBER_EVENTS = "Chamber Events"
    TAB_GLOBAL_EVENTS = "Global Events"

    # See module docstring's propagation note. RELOAD_POLL_TIMEOUT_MS backs
    # the publish-appearance call sites (TC 135747, and TC 135748's own
    # pre-unpublish "visible_before" check) — both confirmed live to
    # propagate in ~1.7s or less, so this 5s margin is a safety multiple
    # over an ALREADY-measured-for-this-section figure, not the untested
    # starting guess it was before 2026-09-01.
    RELOAD_POLL_TIMEOUT_MS = 5000
    RELOAD_POLL_INTERVAL_MS = 500

    # UNPUBLISH-SPECIFIC budget (TC 135748's removal poll only) — measured
    # live 2026-09-01 at ~2.3s (upper bound, see module docstring). 15000ms
    # is a ~6.5x safety multiple over that measured figure, sized to absorb
    # the render/page-load variance a real pytest/browser run adds on top
    # of raw server-side propagation (the likely cause of the original 5s
    # timeout's failure, since live propagation alone measured well under
    # 5s). Passed explicitly as `timeout_ms=` at that one call site — does
    # NOT change the shared RELOAD_POLL_TIMEOUT_MS default used elsewhere.
    UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS = 15000

    def open_home(self) -> "HomeBusinessEventsPage":
        self.open(web_url(self.HOME_PATH))
        self.wait_for(self.SECTION)
        return self

    def select_tab(self, tab_label: str) -> "HomeBusinessEventsPage":
        """Click a category tab scoped to CATEGORY_TABLIST — see module
        docstring on why an unscoped `get_by_role("tab", name=...)` is
        non-unique on this page."""
        self.click(f'{self.CATEGORY_TABLIST} [role="tab"]:text-is("{tab_label}")')
        # Re-render, not a pure visibility toggle (see module docstring) —
        # give the DOM swap a brief moment before the caller reads card state.
        self.page.wait_for_timeout(300)
        return self

    def card_titles(self) -> list[str]:
        """All card titles currently in the DOM for whichever tab is active
        — confirmed live to already reflect ALL pages of the active tab's
        results with no pagination-dot click required (see module
        docstring)."""
        return self.page.locator(self.CARD_TITLE).all_text_contents()

    def card_by_id(self, event_id: str):
        """The card `<a>` matching the event's `?id=<event_id>` query param
        — avoids the title-substring collision risk (see module docstring).
        Returns a Playwright Locator (not a bool) so callers can assert on
        count()/is_visible() or drill into its badges."""
        return self.page.locator(f'{self.CARD}[href*="?id={event_id}"]')

    def has_card_with_exact_title(self, title: str) -> bool:
        """`:text-is()` exact-match presence check, for a caller that only
        has the created record's title (not yet its public event id) —
        see module docstring's CARD_TITLE_EXACT note."""
        return self.page.locator(f'{self.CARD_TITLE}:text-is("{title}")').count() > 0

    def card_for_exact_title(self, title: str):
        return self.page.locator(f'{self.CARD}:has(.qc-be-card-title:text-is("{title}"))')

    def category_badge_text_for_title(self, title: str) -> str:
        return self.text(
            f'{self.CARD}:has(.qc-be-card-title:text-is("{title}")) {self.CARD_CATEGORY_BADGE}'
        )

    def reload_until(self, predicate, timeout_ms: int | None = None, interval_ms: int | None = None) -> bool:
        """Poll `open_home()` + `predicate(self)` until it returns True or
        the timeout elapses — the propagation-check shape mandated by
        cms-profile.md (poll, never a bare `sleep()`). Defaults to this
        page's own RELOAD_POLL_* constants (see module docstring's
        propagation note)."""
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

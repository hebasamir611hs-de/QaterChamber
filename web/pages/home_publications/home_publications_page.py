"""
web/pages/home_publications/home_publications_page.py — HomePublicationsPage.

Public/Web Page Object for PBI 129386 (QC-HOME-010 — Publications Section) —
the Home Page's "Explore Our Knowledge Hub" Publications carousel. Built as a
dependency of this PBI's Control_Panel batch (see
cms/tests/home_publications/test_home_publications_control_panel.py, which
must verify the live public effect of a CMS workflow action, never just the
authoring UI — cms-testing.md's dual-surface rule, and
.claude/context/active/standards.md's "Draft/Unpublish Public-Visibility
Checks — Mandatory Logged-Out Context" rule).

CONFIRMED LIVE 2026-09-12 (anonymous/logged-out Playwright session against
`https://qcdev.ihorizons.com/en/home`, 1920x1080 viewport, no storageState —
`python tools/extract_locators.py --find publication` plus a direct DOM dump
via a throwaway Playwright script, CLI-first per automation-standards.md;
Playwright MCP was NOT needed for this investigation):

  - The section is `section.qc-home-publications` (unique; carries
    `data-qc-page-size="5"` and `data-qc-explore-url` attributes). Heading
    "Explore Our Knowledge Hub", tag "Publications", an "Explore
    Publications" link to `/web/qatar-chamber/publications`, a type-filter
    tablist (`role="tablist"[aria-label="Publication type filter"]`, tabs
    "All Publications" (default-active, `data-qc-pub-filter="all"`) /
    "Research Papers" / "Guides" / "Reports" / "White Papers" / "Manuals" /
    "Brochures"), and a swipeable carousel (`div.qc-pub-carousel` >
    `div.qc-pub-track` > one or more `div.qc-pub-page` "pages", up to 5
    cards per page per `data-qc-page-size`) with its OWN separate
    dot-pagination tablist (`role="tablist"[aria-label="Publications
    pages"]`, `button.qc-pub-dot`).
  - CONFIRMED LIVE, LOAD-BEARING: every card, across every carousel
    "page", is already present in the DOM at once (confirmed by counting
    `a.qc-pub-card` unscoped by any one `.qc-pub-page` — 8 seeded cards
    all present simultaneously against a 5-per-page config, i.e. spanning
    both pages) — this is a client-side CSS-transform paging animation, NOT
    a per-page AJAX fetch. A card query scoped to the whole section
    (`SECTION` below) therefore sees every currently publicly-delivered
    entry regardless of which visual page/tab it would land on — exactly
    what TC 134341's own wording ("not present ANYWHERE in the section")
    needs, with no requirement to click through the dot-pagination or the
    type-filter tabs first. A card the CMS never delivers to the public
    feed at all (e.g. a never-published/rejected entry) is therefore
    absent from this query regardless of tab/page state.
  - Each card is `a.qc-pub-card` (opens the underlying PDF document
    directly, `target="_blank"`, href = a Documents & Media download URL
    that itself carries `objectEntryExternalReferenceCode=<code>` as a
    query param). Card body: `h3.qc-pub-card-title` (the publication's
    Title field, rendered verbatim — used below since ADO 134341's own
    wording is about a visible "card" by its content, not this URL param),
    `span.qc-pub-badge` (Publication Type), `img.qc-pub-card-img` (cover
    image, `alt` = the same title text).
  - 8 real seeded publications confirmed present this session (Research
    Paper/Guides/Reports/White Papers/Manuals/Brochures each represented at
    least once, external reference codes `QCDEMO-129386-PUB-00N`) — this
    Page Object's own methods are Title-keyed, so a disposable
    "QCTEST-134341"-prefixed entry is trivially distinguishable from every
    one of them.
  - No project-specific propagation-latency measurement exists yet for this
    object in cms-profile.md — `reload_until()` mirrors the same bounded-poll
    shape (never a bare `sleep()`) other Home Page sections in this project
    already use (e.g. HomeSocialIconsPage.reload_until()), with the same
    conservative default budget until a real measurement is recorded here.
"""

import time

from core.web.base_page import BasePage
from config.settings import web_url


class HomePublicationsPage(BasePage):
    HOME_PATH = "/en/home"

    SECTION = "section.qc-home-publications"
    CARD = f"{SECTION} a.qc-pub-card"
    CARD_TITLE = "h3.qc-pub-card-title"

    # No measured propagation figure exists for this object yet (see module
    # docstring) — conservative default, still a real condition-based poll.
    RELOAD_POLL_TIMEOUT_MS = 15000
    RELOAD_POLL_INTERVAL_MS = 1000

    def open_home(self) -> "HomePublicationsPage":
        self.open(web_url(self.HOME_PATH))
        self.wait_for(self.SECTION)
        return self

    def card_titles(self) -> list[str]:
        """Every publication card's Title text, in rendered (DOM) order,
        across EVERY carousel page/tab at once — see module docstring's
        LOAD-BEARING finding (all pages already render in the DOM
        simultaneously; this is NOT scoped to only the active tab/page)."""
        cards = self.page.locator(self.CARD)
        return [
            cards.nth(i).locator(self.CARD_TITLE).inner_text().strip()
            for i in range(cards.count())
        ]

    def has_card_with_title(self, title: str) -> bool:
        return title in self.card_titles()

    def reload_until(self, predicate, timeout_ms: int | None = None, interval_ms: int | None = None) -> bool:
        """Poll open_home() + predicate(self) until True or the timeout
        elapses — mirrors HomeSocialIconsPage.reload_until()'s identical,
        established shape (a real condition-based poll, never sleep())."""
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

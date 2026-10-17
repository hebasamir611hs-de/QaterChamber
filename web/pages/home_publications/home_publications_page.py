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

ADDED 2026-09-27 (31-case batch, ADO 134370-134401 — Publication Title/
Type/Date/Cover Image/File Attachment/Active Status): `card_badge_text()`/
`card_href()`/`is_card_visible()`/`click_type_tab()` support the dual
Control_Panel+Web Publication Type (134379-134381) and Active Status
(134399-134401) cases. CONFIRMED LIVE this session: the type-filter
tablist (`TYPE_TABLIST`) exposes exactly 6 non-"all" tabs — "Bulletin" and
"Study" (2 of the admin's 8 real `PUBLICATION_TYPE_*` options) have NO
corresponding public tab (see `TYPE_TO_TAB_FILTER`'s own note) — a real,
disclosed scope gap this batch works around by only exercising a type that
DOES have a tab ("Report"/"Guides"), never by inventing one.
"""

import time

from core.web.base_page import BasePage
from config.settings import web_url


class HomePublicationsPage(BasePage):
    HOME_PATH = "/en/home"
    HOME_PATH_LOCALE_NEUTRAL = "/home"

    SECTION = "section.qc-home-publications"
    CARD = f"{SECTION} a.qc-pub-card"
    CARD_TITLE = "h3.qc-pub-card-title"
    CARD_BADGE = "span.qc-pub-badge"
    TYPE_TABLIST = f'{SECTION} [role="tablist"][aria-label="Publication type filter"] [role="tab"]'

    # Control_Panel "Publication Type " combobox option label -> this
    # section's own `data-qc-pub-filter` tab value — CONFIRMED LIVE
    # 2026-09-27 (31-case batch investigation, ADO 134379-134401): the
    # public tablist exposes exactly 6 non-"all" tabs (researchPaper/
    # guides/report/whitePaper/manuals/brochure) for the admin's 8-option
    # Publication Type enum — "Bulletin" and "Study" have NO corresponding
    # public filter tab (a real, disclosed scope gap, not a mapping bug);
    # every case in this batch that needs a real tab uses "Report"/"Guides"
    # only, both of which DO have one.
    TYPE_TO_TAB_FILTER = {
        "Research Paper": "researchPaper",
        "Guides": "guides",
        "Report": "report",
        "White Paper": "whitePaper",
        "Manuals": "manuals",
        "Brochure": "brochure",
    }

    # No measured propagation figure exists for this object yet (see module
    # docstring) — conservative default, still a real condition-based poll.
    RELOAD_POLL_TIMEOUT_MS = 15000
    RELOAD_POLL_INTERVAL_MS = 1000

    def open_home(self, locale: str = "en") -> "HomePublicationsPage":
        """`locale="ar"` navigates `/ar/home` (see `web_url()`'s own
        locale-prefix contract) — `HOME_PATH`'s own literal `/en/home` is
        EN-specific, so the AR variant uses the locale-neutral `/home` path
        instead, letting `web_url()` apply the `/ar` prefix itself (ADDED
        2026-09-27 for the bilingual Title AR/RTL cases, ADO 134375-134378)."""
        if locale == "ar":
            self.open(web_url(self.HOME_PATH_LOCALE_NEUTRAL, locale="ar"))
        else:
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

    def has_card_with_title_containing(self, substring: str) -> bool:
        return any(substring in t for t in self.card_titles())

    def _card_by_title(self, title: str):
        return self.page.locator(self.CARD).filter(has=self.page.locator(f'{self.CARD_TITLE}:text-is("{title}")'))

    def card_badge_text(self, title: str) -> str:
        """The Publication Type badge text rendered on the card matching
        `title` exactly — "" if no such card is present."""
        card = self._card_by_title(title)
        if card.count() == 0:
            return ""
        return card.first.locator(self.CARD_BADGE).inner_text().strip()

    def card_href(self, title: str) -> str:
        card = self._card_by_title(title)
        if card.count() == 0:
            return ""
        return card.first.get_attribute("href") or ""

    def card_image_src(self, title: str) -> str:
        card = self._card_by_title(title)
        if card.count() == 0:
            return ""
        img = card.first.locator("img.qc-pub-card-img")
        return img.get_attribute("src") or "" if img.count() > 0 else ""

    def is_card_visible(self, title: str) -> bool:
        card = self._card_by_title(title)
        return card.count() > 0 and card.first.is_visible()

    def click_type_tab(self, filter_value: str) -> "HomePublicationsPage":
        self.page.locator(f'{self.TYPE_TABLIST}[data-qc-pub-filter="{filter_value}"]').click()
        self.page.wait_for_timeout(800)
        return self

    def reload_until(self, predicate, timeout_ms: int | None = None, interval_ms: int | None = None, locale: str = "en") -> bool:
        """Poll open_home(locale) + predicate(self) until True or the
        timeout elapses — mirrors HomeSocialIconsPage.reload_until()'s
        identical, established shape (a real condition-based poll, never
        sleep())."""
        timeout_ms = timeout_ms if timeout_ms is not None else self.RELOAD_POLL_TIMEOUT_MS
        interval_ms = interval_ms if interval_ms is not None else self.RELOAD_POLL_INTERVAL_MS
        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home(locale=locale)
            if predicate(self):
                return True
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(interval_ms)

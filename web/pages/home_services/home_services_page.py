"""
web/pages/home_services/home_services_page.py — HomeServicesPage.

PBI 129371 / QC-HOME-003 "Our Services Section" — its own Home-page
section/module folder per active/standards.md's Home-page sections table.
This pass covers the 17 approved, Automation-tagged, Web-platform cases
handed off for this PBI (ADO TC 135329-135345, 135353, 135414). No
Control_Panel-tagged case exists in this batch (see the sibling
home_services_admin_page.py, which exists ONLY because TC 135353/135414's
own Arrange step needs an authenticated CMS session — same shape as
home_strategic_partners_admin_page.py's TC 136289/... chain).

--- CLI-first extraction log (2026-08-26, live https://qcdev.ihorizons.com) ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "service"
    -> [role] uniq=1  get_by_role("tablist", name="Service categories")
    -> [role] uniq=1  get_by_role("tab", name="All Services")
    -> [role] uniq=1  get_by_role("tab", name="E-Services")
    -> [role] uniq=1  get_by_role("link", name="View All Services")

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "membership"
    -> [role] uniq=1  get_by_role("tab", name="Membership")
    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "legal"
    -> [role] uniq=1  get_by_role("tab", name="Legal")
    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "information"
    -> [role] uniq=1  get_by_role("tab", name="Information")
    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "read more"
    -> [role] uniq=10  get_by_role("link", name="Read More")  (10 across the WHOLE page —
       only 8 of these are inside this section; other Home sections also use "Read More")

The extractor's role-based harvest surfaced the tablist/tab/CTA-link elements
above but not the section container, badge/heading/description, or the
per-card internals (plain span/h2/p/article/img with no role/label) — the
same documented "ambiguous/unreachable via role" condition already resolved
in home_business_events_page.py / home_quick_contact_page.py. Resolved the
same way: additional, disclosed, scoped Playwright scripts (still CLI/shell,
never the Playwright MCP), reusing BasePage's own license-gate/overlay guard
sequence, to read the live DOM structure, click through the real tab-filter
behavior, and read hrefs/bounding boxes/computed styles.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home, 1920x1080):

    section.qc-home-our-services[data-qc-view-all-url="/web/qatar-chamber/our-services"]  (2026-10-21)
                                 [data-qc-detail-base="/web/qatar-chamber/service-detail?id="]
                                 [data-qc-default-tab="allServices"]
      div.qc-os-inner
        div.qc-os-head
          div.qc-os-head-text
            span.qc-os-tag           "Our Services"                    (TAG)
            h2.qc-os-heading         "Services We Provide"              (HEADING)
            p.qc-os-desc             (description copy)                 (DESCRIPTION)
          a.qc-os-viewall.qc-os-viewall--top  [href="/our-services"]  (2026-10-21)
            span "View All Services"                                    (CTA_TOP)
        div.qc-os-tabs[role=tablist][aria-label="Service categories"]    (TABLIST)
          button.qc-os-tab[data-key="allservices"][role=tab][aria-selected] "All Services" (TAB_ALL)
          button.qc-os-tab[data-key="membership"][role=tab]   "Membership"  (TAB_MEMBERSHIP)
          button.qc-os-tab[data-key="legal"][role=tab]        "Legal"       (TAB_LEGAL)
          button.qc-os-tab[data-key="eservices"][role=tab]    "E-Services"  (TAB_ESERVICES)
          button.qc-os-tab[data-key="information"][role=tab]  "Information" (TAB_INFORMATION)
        div.qc-os-carousel
          div.qc-os-viewport
            div.qc-os-track (flex row — clicking a tab RE-RENDERS this list,
                              it does not hide/show existing cards)
              article.qc-os-card                                        (CARD)
                div.qc-os-card-media
                  img.qc-os-card-img                                    (CARD_IMG)
                  span.qc-os-card-icon > img
                div.qc-os-card-body
                  h3.qc-os-card-title                                   (CARD_TITLE)
                  p.qc-os-card-desc                                     (CARD_DESC)
                  a.qc-os-readmore [href="/web/qatar-chamber/service-detail?id=<N>"]
                    span "Read More"                                    (CARD_READMORE)
        div.qc-os-dots[role=tablist][aria-label="Select service"]  (2026-10-21: visible,
                                                             5 "Services page N" dots
                                                             page the 17-card carousel)
        a.qc-os-viewall.qc-os-viewall--bottom [not visible at 1920x1080]  (CTA_BOTTOM)
        p.qc-os-empty[hidden]  "" (empty-state text — no live filter produces 0 cards)

RE-VERIFIED 2026-10-21 (anonymous context, CLI extractor + scoped probe
scripts — the 2026-08-26 snapshot below this line was stale and has been
replaced):
  - 17 active service cards (was 8), carousel paginated by 5 dots
    (`.qc-os-dots` role=tablist "Select service", buttons "Services page N")
    — off-screen cards are paged into view by clicking a dot.
  - Card data is NOT hardcoded any more. The section renders from the public,
    anonymous JSON the page itself fetches:
        /o/c/servicecards/scopes/<site>?filter=activeStatus eq true...
    each item carries `assignedTab.key` (membership | legal | eServices |
    information | allServices) and `redirectUrl`. `open_home_with_oracle()`
    captures that response during navigation; the expected card set for a
    tab = items whose assignedTab.key matches the tab's `data-key`
    (case-insensitive). Cards assigned to `allServices` (e.g. "Legal
    Consulting", "Private Sector Export Reports") appear only under the All
    Services tab.
  - View All CTA href is now "/our-services"; the section's configured
    target is `data-qc-view-all-url="/web/qatar-chamber/our-services"`.
  - "Legal Consulting" now exists (assignedTab=allServices); its Read More
    points at the external https://www.qatarchamber.com/legal-consulting/
    (same tab, no target=_blank).
  - Information tab's label is "Information" (case says "Information
    Services") — reported as an observation, the tab is selected by data-key.
  - AR: html[dir=rtl]; tab boxes run right-to-left (All Services right-most).
  - A leftover `QCTEST-135400-redirect` card (another run's test data) is
    live under Information — the oracle includes it, so it does not break
    the filter assertions.
"""

from core.web.base_page import BasePage
from config.settings import web_url

_TAB_LOCATORS = {
    "all": '.qc-os-tab[data-key="allservices"]',
    "membership": '.qc-os-tab[data-key="membership"]',
    "legal": '.qc-os-tab[data-key="legal"]',
    "eservices": '.qc-os-tab[data-key="eservices"]',
    "information": '.qc-os-tab[data-key="information"]',
}


class HomeServicesPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    SECTION = "section.qc-home-our-services"
    TAG = ".qc-os-tag"
    HEADING = ".qc-os-heading"
    DESCRIPTION = ".qc-os-desc"
    TABLIST = ".qc-os-tabs"
    TAB_ALL = _TAB_LOCATORS["all"]
    TAB_MEMBERSHIP = _TAB_LOCATORS["membership"]
    TAB_LEGAL = _TAB_LOCATORS["legal"]
    TAB_ESERVICES = _TAB_LOCATORS["eservices"]
    TAB_INFORMATION = _TAB_LOCATORS["information"]
    CTA_TOP = "a.qc-os-viewall--top"
    CTA_BOTTOM = "a.qc-os-viewall--bottom"
    CARD = ".qc-os-card"
    CARD_TITLE = ".qc-os-card-title"
    CARD_DESC = ".qc-os-card-desc"
    CARD_READMORE = ".qc-os-readmore"
    CARD_IMG = ".qc-os-card-img"
    EMPTY_STATE = ".qc-os-empty"
    HTML_ROOT = "html"

    # Generic tab locator (any [role="tab"] under TABLIST) — used by
    # open_tab()/reload_until_card_visible_under_tab() for CMS content-
    # verification checks that need to select a tab by its live label text,
    # as opposed to click_tab()'s fixed TAB_ALL/TAB_MEMBERSHIP/etc. enum.
    TAB = f'{TABLIST} [role="tab"]'

    # Borrowed from cms-profile.md's ONLY measured propagation budget
    # (~0s / 5s-timeout / 0.5s-interval, Board Members JAX-RS endpoint) —
    # NOT independently re-measured for this content type. Disclosed
    # placeholder budget, matching HomePromoBannersPage's own note.
    RELOAD_POLL_TIMEOUT_MS = 5000
    RELOAD_POLL_INTERVAL_MS = 500

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeServicesPage":
        self.open(web_url("/home"))
        return self

    def open_home_arabic(self) -> "HomeServicesPage":
        self.open(web_url("/home", locale="ar"))
        return self

    def scroll_to_section(self) -> "HomeServicesPage":
        self.wait_for(self.SECTION, state="attached")
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    # ── Page-level direction (RTL) ────────────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    # ── Section-level state ───────────────────────────────────────────────
    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def is_section_present(self) -> bool:
        """Existence check (TC 135353's 'absent from the Home Page entirely'
        needs to distinguish 0-matches from present-but-hidden)."""
        return self.page.locator(self.SECTION).count() > 0

    # ── Tag / heading / description ─────────────────────────────────────
    def tag_text(self) -> str:
        return self.text(self.TAG)

    def heading_text(self) -> str:
        return self.text(self.HEADING)

    def description_text(self) -> str:
        return self.text(self.DESCRIPTION)

    def head_text_align(self) -> str:
        return self.page.locator(".qc-os-head-text").evaluate("el => getComputedStyle(el).textAlign")

    # ── Filter tab bar ───────────────────────────────────────────────────
    def is_tablist_visible(self) -> bool:
        return self.is_visible(self.TABLIST)

    def tab_texts(self) -> list:
        return self.page.locator(self.TABLIST).locator('[role="tab"]').all_inner_texts()

    def _tab_locator(self, which: str) -> str:
        return _TAB_LOCATORS[which]

    def is_tab_active(self, which: str = "all") -> bool:
        return self.page.locator(self._tab_locator(which)).get_attribute("aria-selected") == "true"

    def click_tab(self, which: str) -> "HomeServicesPage":
        """Click a filter tab and wait on real signals only: the tab becomes
        aria-selected, then (when the oracle was captured) the re-rendered
        card count settles on the oracle's count. A count that never settles
        is left for the test's own set assertion to report — never masked."""
        self.click(self._tab_locator(which))
        self.wait_for(f'{self._tab_locator(which)}[aria-selected="true"]', state="attached")
        if self.service_cards is not None:
            try:
                self.wait_for_condition(
                    "([sel, n]) => document.querySelectorAll(sel).length === n",
                    arg=[f"{self.SECTION} {self.CARD}", len(self.expected_titles_for_tab(which))],
                )
            except Exception:  # noqa: BLE001 — mismatch is asserted by the test
                pass
        return self

    def tab_x(self, which: str) -> float:
        return self.tab_box(which).get("x", 0.0)

    # ── Anonymous navigation + public data oracle (2026-10-21) ────────────
    service_cards = None
    SERVICE_CARDS_API = "/o/c/servicecards/"

    def open_home_with_oracle(self, locale: str = "en") -> "HomeServicesPage":
        """Logged-out navigation to the Home Page that also captures the
        public, anonymous service-cards JSON the section itself renders from.
        Read-only; never reauthenticates."""
        with self.page.expect_response(
            lambda r: self.SERVICE_CARDS_API in r.url and r.status == 200, timeout=30000
        ) as info:
            self.open_anonymous(web_url("/home", locale=locale))
        self.service_cards = info.value.json().get("items", [])
        self._locale = locale
        return self

    def open_home_settled(self, locale: str = "en") -> "HomeServicesPage":
        """Logged-out Home load for TC 135353 (section absent). Unlike
        `open_home_with_oracle()` it does not wait for the service-cards
        response, which need not fire when the section is correctly absent:
        it waits on the global footer, then a bounded network-idle."""
        self.open_anonymous(web_url("/home", locale=locale))
        self.page.locator("footer.qc-global-site-footer").first.wait_for(state="attached", timeout=30000)
        try:
            self.page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:  # noqa: BLE001 -- upper bound only; footer is the settle anchor
            pass
        return self

    def _oracle_title(self, item: dict) -> str:
        if getattr(self, "_locale", "en") == "ar":
            return (item.get("title_i18n") or {}).get("ar_SA") or item.get("title", "")
        return item.get("title", "")

    def expected_titles_for_tab(self, which: str) -> set:
        """Configured card titles for a tab, from the captured oracle.
        `which` is a _TAB_LOCATORS key ('all', 'membership', 'legal',
        'eservices', 'information')."""
        items = self.service_cards or []
        if which == "all":
            return {self._oracle_title(i).strip() for i in items}
        return {
            self._oracle_title(i).strip()
            for i in items
            if str((i.get("assignedTab") or {}).get("key", "")).lower() == which
        }

    def configured_redirect_url(self, title: str) -> str:
        for item in self.service_cards or []:
            if item.get("title") == title:
                return item.get("redirectUrl", "")
        return ""

    def configured_view_all_url(self) -> str:
        return self.page.locator(self.SECTION).get_attribute("data-qc-view-all-url") or ""

    # ── Card lookup by title / carousel paging ────────────────────────────
    def _card_by_title(self, title: str):
        return self.page.locator(self.CARD).filter(
            has=self.page.locator(f'{self.CARD_TITLE}:text-is("{title}")')
        )

    def is_card_present(self, title: str) -> bool:
        return self._card_by_title(title).count() > 0

    def card_has_parts(self, title: str) -> dict:
        card = self._card_by_title(title).first
        return {
            "icon": card.locator(".qc-os-card-icon img").count() > 0,
            "title": card.locator(self.CARD_TITLE).inner_text().strip(),
            "description": card.locator(self.CARD_DESC).inner_text().strip(),
            "read_more": card.locator(self.CARD_READMORE).count() > 0,
        }

    def card_readmore_href_by_title(self, title: str) -> str:
        return self._card_by_title(title).first.locator(self.CARD_READMORE).get_attribute("href") or ""

    def bring_card_into_view(self, title: str) -> "HomeServicesPage":
        """Page the carousel with its 'Services page N' dots until the card
        sits fully inside the viewport (off-screen Read More links carry
        tabindex=-1). Waits on the card's own box, never a fixed delay."""
        card = self._card_by_title(title).first
        js = (
            "([sel, t]) => { const c = [...document.querySelectorAll(sel)].find("
            "e => e.querySelector('.qc-os-card-title')?.innerText.trim() === t);"
            " if (!c) return false; const r = c.getBoundingClientRect();"
            " return r.left >= 0 && r.right <= window.innerWidth; }"
        )
        dots = self.page.locator(".qc-os-dots .qc-os-dot")
        if self.page.evaluate(js, [self.CARD, title]):
            return self
        for i in range(dots.count()):
            dots.nth(i).click()
            try:
                self.wait_for_condition(js, arg=[self.CARD, title], timeout=3000)
                return self
            except Exception:  # noqa: BLE001 — not on this page, try the next dot
                continue
        card.scroll_into_view_if_needed()
        return self

    def click_card_readmore_by_title(self, title: str) -> None:
        self._card_by_title(title).first.locator(self.CARD_READMORE).click()

    def landed_status(self) -> int:
        """HTTP status of the page the browser landed on — a read-only GET
        from the same (anonymous) context, redirects followed. Catches a
        link that 'navigates' to a 404.

        Sends a regular desktop-Chrome User-Agent: the external
        www.qatarchamber.com WAF answers 403 to any 'HeadlessChrome' UA
        (confirmed 2026-10-21: headless 403, desktop UA 200 for the same
        URL), which says nothing about what a visitor gets."""
        return self.page.request.get(self.page.url, headers={"User-Agent": self.DESKTOP_UA}).status

    DESKTOP_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    )

    def tab_visual_style(self, which: str) -> dict:
        return self.computed_style(
            self._tab_locator(which),
            ["backgroundColor", "color", "borderBottomColor", "borderBottomWidth", "fontWeight", "boxShadow"],
        )

    def clamped_card_descriptions(self) -> list:
        """Descriptions whose content is cut off vertically by more than half
        a line (line-clamp) — sub-line slack is line-height, not truncation."""
        return self.page.locator(self.CARD_DESC).evaluate_all(
            "els => els.filter(e => { const lh = parseFloat(getComputedStyle(e).lineHeight) || 20;"
            " return e.scrollHeight - e.clientHeight > lh / 2; }).map(e => e.innerText)"
        )

    def truncated_card_titles(self) -> list:
        """Card titles whose text overflows their box horizontally (clipped)."""
        return self.page.locator(self.CARD_TITLE).evaluate_all(
            "els => els.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.innerText)"
        )

    # ── "View All Services" CTA ──────────────────────────────────────────
    def is_cta_top_visible(self) -> bool:
        return self.is_visible(self.CTA_TOP)

    def cta_top_text(self) -> str:
        return self.text(self.CTA_TOP)

    def cta_top_href(self) -> str:
        return self.page.locator(self.CTA_TOP).get_attribute("href")

    def click_cta_top(self) -> None:
        self.click(self.CTA_TOP)

    # ── Card grid / carousel ─────────────────────────────────────────────
    def total_card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def _card(self, index: int = 0):
        return self.page.locator(self.CARD).nth(index)

    def card_titles(self) -> list:
        return [t.strip() for t in self.page.locator(self.CARD_TITLE).all_inner_texts()]

    def card_title_text(self, index: int = 0) -> str:
        return self._card(index).locator(self.CARD_TITLE).inner_text()

    def card_readmore_href(self, index: int = 0) -> str:
        return self._card(index).locator(self.CARD_READMORE).get_attribute("href")

    def click_card_readmore(self, index: int = 0) -> None:
        self._card(index).locator(self.CARD_READMORE).click()

    def card_box(self, index: int = 0) -> dict:
        box = self._card(index).bounding_box()
        return box or {}

    def is_empty_state_visible(self) -> bool:
        return self.is_visible(self.EMPTY_STATE)

    # ── Layout probes (responsive / alignment cases) ─────────────────────
    def has_no_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        )

    def head_text_box(self) -> dict:
        return self.page.locator(".qc-os-head-text").bounding_box() or {}

    def tablist_box(self) -> dict:
        return self.page.locator(self.TABLIST).bounding_box() or {}

    def cta_top_box(self) -> dict:
        return self.page.locator(self.CTA_TOP).bounding_box() or {}

    def tab_box(self, which: str = "all") -> dict:
        return self.page.locator(self._tab_locator(which)).bounding_box() or {}

    def no_login_prompt_present(self) -> bool:
        """TC 135332 ('no login prompt') — a generic, page-wide check that no
        password field is rendered anywhere, not scoped to this section."""
        return self.page.locator('input[type="password"]').count() == 0

    # ── CMS content-verification (Control_Panel-driven propagation checks) ──
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

    def card_visible(self, title: str) -> bool:
        try:
            locator = self.page.locator(f'{self.CARD_TITLE}:text-is("{title}")')
            return locator.first.is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's never-throws contract
            return False

    def reload_until(self, predicate, timeout_ms: int | None = None, interval_ms: int | None = None) -> bool:
        """Poll open_home() + predicate(self) until True or timeout — never
        a bare sleep."""
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

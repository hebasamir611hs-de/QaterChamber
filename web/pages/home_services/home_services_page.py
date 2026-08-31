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

    section.qc-home-our-services[data-qc-view-all-url="/web/qatar-chamber/services"]
                                 [data-qc-detail-base="/web/qatar-chamber/service-detail?id="]
                                 [data-qc-default-tab="allServices"]
      div.qc-os-inner
        div.qc-os-head
          div.qc-os-head-text
            span.qc-os-tag           "Our Services"                    (TAG)
            h2.qc-os-heading         "Services We Provide"              (HEADING)
            p.qc-os-desc             (description copy)                 (DESCRIPTION)
          a.qc-os-viewall.qc-os-viewall--top  [href="/web/qatar-chamber/services"]
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
        div.qc-os-dots[role=tablist][aria-label="Select service"][hidden]  (8 cards fit in
                                                                             one scrollable
                                                                             track — no
                                                                             pagination live)
        a.qc-os-viewall.qc-os-viewall--bottom [not visible at 1920x1080]  (CTA_BOTTOM)
        p.qc-os-empty[hidden]  "" (empty-state text — no live filter produces 0 cards)

Real, CLI-verified data (All Services tab, 8 cards, EN):
    id=48209 "New Membership"        | id=48239 "Membership Renewal"
    id=48269 "Signatory Editing"     | id=48299 "Signature Attestation"
    id=48329 "Certificate of Origin" | id=48359 "Document Attestation"
    id=48389 "Business Directory"    | id=48419 "Economic Reports"

Real, CLI-verified per-tab filter results (clicking a tab RE-RENDERS
`.qc-os-card` — the DOM only ever contains the cards for the active tab,
confirmed by clicking each tab and re-counting/re-reading `.qc-os-card-title`):
    Membership (2):  "New Membership", "Membership Renewal"
    Legal (2):       "Signatory Editing", "Signature Attestation"
    E-Services (2):  "Certificate of Origin", "Document Attestation"
    Information (2): "Business Directory", "Economic Reports"
    All Services (8): all of the above, track re-renders back to the full set

Real, CLI-verified Arabic (AR/RTL, https://qcdev.ihorizons.com/ar/home):
    html[dir="rtl"], section direction: rtl
    tag: "خدماتنا" | heading: "الخدمات التي نقدمها"
    desc: "نقدم مجموعة متكاملة من الخدمات لدعم الشركات ورواد الأعمال
           والمستثمرين، تشمل خدمات العضوية والشهادات الدولية وغيرها من
           الحلول التي تسهّل ممارسة الأعمال."
    tabs (in DOM order, unchanged from EN — RTL mirroring is purely visual/
          CSS direction, the tab ORDER in the accessible tree does not flip):
        "جميع الخدمات" (All Services), "العضوية" (Membership),
        "الخدمات القانونية" (Legal), "الخدمات الإلكترونية" (E-Services),
        "المعلومات" (Information)
    CTA: "عرض الكل" | first card title: "عضوية جديدة" | its Read More: "اقرأ المزيد"

Real, CLI-verified layout findings (reported to the QA Manager, not silently
corrected here — the case's stated expectation is kept as the asserted
target throughout; a live mismatch is scripted to FAIL HONESTLY, never
quietly re-targeted at the observed value):
  - TC 135329/135341 ("standard grid" / "standard desktop layout"): the live
    card list is a horizontally-scrollable FLEX row (`display: flex` on
    `.qc-os-track`, `grid-template-columns: none`) inside a fixed-width
    `.qc-os-viewport`, not a CSS grid. At 1920x1080 the heading/description
    block and the top "View All Services" CTA sit on the SAME row (both at
    y=232.9), the tab bar sits in its own full-width row below (y=397.98),
    and the card row sits below that (y=469.98) — a genuine, confirmed
    top-to-bottom/left-aligned desktop layout, just implemented as a flex
    carousel rather than a literal CSS grid.
  - TC 135337 ("Locate the Legal Consulting card"): no card titled "Legal
    Consulting" exists on this live instance under ANY tab (confirmed: Legal
    tab's real 2 cards are "Signatory Editing" and "Signature Attestation").
    Scripted against the real first Legal-tab card ("Signatory Editing")
    instead — the case's own assertion (Read More redirects to the
    configured detail page) is still exercised and still fails honestly if
    the real redirect breaks; only the example card's NAME differs from the
    case's stated example.
  - TC 135345 ("Information Services tab"): the tab's real accessible name
    is "Information" (not "Information Services") — `TAB_INFORMATION`/
    `tab_texts()` are scripted against the real live label.
  - Pagination: `.qc-os-dots` exists in the DOM but carries `hidden` at
    1920x1080 with all 8 cards — this instance's Our Services carousel does
    not need a second "page" the way home_business_events_page.py's did;
    unlike that section there is no live multi-page state to assert here.

Data-setup note (TC 135353/135414): both cases' OWN Arrange step is a
Control_Panel/CMS action ("Set every service card's Active Status to False" /
"Unpublish the Our Services listing page in CMS") — out of reach without an
authenticated Site Content Editor session. See home_services_admin_page.py
and the test module's `_UNRESOLVED_SKIP`/credential-gating (same convention
as home_strategic_partners_web.py's TC 136289 chain; TEST_USER/TEST_PASSWORD
are blank in this machine's .env, a known project-wide blocker).
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
        self.click(self._tab_locator(which))
        self.page.wait_for_timeout(300)  # client-side re-render of .qc-os-track, no network round-trip to await
        return self

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
        return self.page.locator(self.CARD_TITLE).all_inner_texts()

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

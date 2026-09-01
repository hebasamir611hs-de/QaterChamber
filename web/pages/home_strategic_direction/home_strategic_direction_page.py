"""
web/pages/home_strategic_direction/home_strategic_direction_page.py —
HomeStrategicDirectionPage.

Public-frontend counterpart to home_strategic_direction_admin_page.py, for
PBI 129381's Home Page "Strategic Direction Section" (Pillar Cards)
carousel. CONFIRMED LIVE this session (2026-08-31, headless Chromium,
1920x1080, real qcdev Home Page HTML, via the same one-process Python probe
documented in home_strategic_direction_admin_page.py's module docstring):

  - The section is SERVER-RENDERED: all 3 pillar cards' full markup
    (title + description + icon) are present in the initial HTML response
    for the un-authenticated public Home Page — confirmed by reading
    `body.inner_text()`/`inner_html()` right after `page.goto()` with only a
    short settle wait, no client-side fetch/poll needed to see the content.
    Per cms-profile.md's scope note (written for the JAX-RS-backed Board of
    Directors pages), this does NOT generalize automatically to every
    content type on this project — Strategic Pillar Cards' own render path
    was independently confirmed server-side this session, not assumed.
  - Confirmed live selector inventory (exact classes from a real DOM dump):
      .qc-sd-tag          — eyebrow, confirmed text "Strategic Pillars"
      .qc-sd-heading      — h2, confirmed text "Our Strategic Direction"
      .qc-sd-desc         — intro paragraph
      .qc-sd-carousel .qc-sd-stage — the carousel viewport; ALL cards are
        present in the DOM simultaneously (not lazy-inserted per slide),
        the current slide is marked with an `is-active` class on its
        `article.qc-sd-card` — confirmed live, so "visible in the live
        carousel" for automation purposes means "present in
        `.qc-sd-stage`'s DOM", not "has `is-active`" (a new/edited card is
        not guaranteed to be the initially-active slide).
      article.qc-sd-card         — one per pillar
      article.qc-sd-card-title (h3) — confirmed exact text match for
        "Vision" / "Mission" / "Objectives" this session
      article.qc-sd-card-desc p     — the description paragraph
  - Confirmed live pairing with the admin surface: each card's icon <img>
    src embeds `objectEntryExternalReferenceCode=QCDEMO-129381-
    STRATEGIC_PILLAR_CARD-0N`, confirming this public section is driven by
    exactly the admin Object Definition entries documented in
    home_strategic_direction_admin_page.py (ID 49056/49082/49108 ->
    ...-01/-02/-03 respectively) — not a separate/duplicated content source.

VERDICT (2026-09-01, framework-improvement review): a permanent dedicated
"QA-TEST Pillar Card" record was considered as a safer alternative to
mutate-then-restore against the real "Mission" record for TC 135557. NOT
adopted. Reasoning is NOT that the layout is a fixed-N grid (not verified
either way this session — all 3 cards are simply present in
`.qc-sd-stage`'s DOM together, which is consistent with either a fixed or a
variable-length carousel) — the reasoning is that a permanent test record
here would render on the LIVE public Home Page for every real visitor, not
just in a test context, since this section is server-rendered directly
from the Object Definition entries. That is real, user-facing content
pollution regardless of how the carousel happens to size itself, and is
reason enough on its own not to add one. TC 135557 continues to
mutate-then-restore the real Mission record (baseline capture/restore
discipline), per cms-profile.md's TEST_OWNED-vs-real tradeoff — correctness
over convenience.
  - No dedicated "cache refresh" UI action was found or needed to observe a
    change (see the admin Page Object's docstring on propagation) — a plain
    page reload is what this Page Object's poll helper performs.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeStrategicDirectionPage(BasePage):
    SECTION_HEADING = ".qc-sd-heading"
    SECTION_TAG = ".qc-sd-tag"
    CAROUSEL_STAGE = ".qc-sd-stage"
    CARD = "article.qc-sd-card"
    CARD_TITLE = ".qc-sd-card-title"
    CARD_DESC = ".qc-sd-card-desc"

    def open_home(self, locale: str = "en") -> "HomeStrategicDirectionPage":
        self.open(web_url("/", locale=locale))
        return self

    def wait_for_carousel(self) -> "HomeStrategicDirectionPage":
        self.wait_for(f"{self.CAROUSEL_STAGE} >> nth=0")
        return self

    def card_locator_by_title(self, title: str) -> str:
        return f'{self.CARD}:has({self.CARD_TITLE}:text-is("{title}"))'

    def is_card_visible(self, title: str) -> bool:
        return self.is_visible(self.card_locator_by_title(title))

    def card_description(self, title: str) -> str:
        return self.text(f'{self.card_locator_by_title(title)} {self.CARD_DESC}')

    def card_titles(self) -> list:
        return self.page.locator(f"{self.CARD} {self.CARD_TITLE}").all_inner_texts()

    def reload_until_card_description_matches(
        self, title: str, expected_text: str, timeout_ms: int = 5000, interval_ms: int = 500
    ) -> bool:
        """Poll (reload + re-check), never a bare sleep — per
        cms-profile.md's Publish/Propagation Latency Budget guidance
        (measured ~0s for the Board Members data source; not
        independently re-measured for Strategic Pillar Cards this
        session, so the conservative default timeout/interval is used
        rather than assuming the same near-instant figure)."""
        elapsed = 0
        while elapsed <= timeout_ms:
            self.open_home()
            self.wait_for_carousel()
            if self.is_card_visible(title) and self.card_description(title) == expected_text:
                return True
            self.page.wait_for_timeout(interval_ms)
            elapsed += interval_ms
        return False

    def reload_until_card_visible(self, title: str, timeout_ms: int = 5000, interval_ms: int = 500) -> bool:
        elapsed = 0
        while elapsed <= timeout_ms:
            self.open_home()
            self.wait_for_carousel()
            if self.is_card_visible(title):
                return True
            self.page.wait_for_timeout(interval_ms)
            elapsed += interval_ms
        return False

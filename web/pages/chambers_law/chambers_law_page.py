"""
web/pages/chambers_law/chambers_law_page.py — ChambersLawPage.

Public-frontend Page Object for PBI 129394 (QC-ABOUT-003 — Chamber's Law),
`/web/qatar-chamber/about-us/chamber-laws` (Arabic: `/ar/web/qatar-chamber/
about-us/chamber-laws`).

Locators extracted CLI-first via `tools/extract_locators.py` against the live
page (WEB_BASE_URL=https://qcdev.ihorizons.com/) at the framework default
viewport (1920x1080). The CLI harvester only walks
a,button,input,select,textarea,[role],[data-testid],[data-test],[aria-label],
[contenteditable] and correctly surfaced the header/footer/breadcrumb links
and the two card title/CTA links as `role=link`. The custom `qc-cl-*` class
structure below (hero, intro, card internals, breadcrumb) is NOT walked by
the CLI tool (it targets `<article>`/`<p>`/`<span>` wrapper elements with no
interactive role), so it was confirmed via a scoped Playwright `evaluate()`
DOM probe against the same live page instead of guessed — same disclosed
fallback pattern used in org_structure_page.py, minus the MCP (a plain script
sufficed here):

    python tools/extract_locators.py \
      --url https://qcdev.ihorizons.com/web/qatar-chamber/about-us/chamber-laws

    -> get_by_role("link", name="Chamber's Law")  (main nav, About Us submenu)
    -> get_by_role("link", name="Establishment of the Qatar Chamber of Commerce
       and Industry")  (card 1 title link)
    -> get_by_role("link", name="Amending Certain Provisions of Law No. 11 of
       1990")  (card 2 title link)

DOM probe confirmed:
    h1.qc-cl-hero-title / div.qc-cl-hero / div.qc-cl-hero-media / div.qc-cl-hero-overlay
    nav.qc-cl-breadcrumb[aria-label="Breadcrumb"]
      a.qc-cl-crumb.qc-cl-crumb-home[data-qc-cl-home] > span[data-qc-cl-home-label]
      span.qc-cl-crumb.qc-cl-crumb-current[data-qc-cl-current]
    section.qc-cl-intro
      h2.qc-cl-intro-heading / div.qc-cl-intro-body > p (qc-cl-intro-text)
      figure.qc-cl-intro-figure > img.qc-cl-intro-img
    h2.qc-cl-refs-heading
    div.qc-cl-cards
      article.qc-cl-card
        span.qc-cl-card-icon > img.qc-cl-card-icon-img
        div.qc-cl-card-main
          p.qc-cl-card-number
          a.qc-cl-card-title.qc-cl-card-title-link[href][target]
          p.qc-cl-card-desc
        a.qc-cl-card-cta[href][target] > svg.qc-cl-cta-icon + span.qc-cl-cta-label

Live-env note: an "Eid Al-Adha Holiday Notice" announcement modal
(`[aria-label="Close"]`) intercepts pointer events on first load and must be
dismissed before any interaction — `open_chambers_law()` does this.

No dark-mode toggle control exists anywhere on this page or in the
accessibility-tools menu at the time of extraction (confirmed by a DOM probe
for `text=/dark mode/i`, `[class*=dark]`, `[aria-label*="dark" i]` — zero
matches beyond an unrelated CSS class). Cases 134859/134860/134864/134865
(dark-mode rendering) are therefore BLOCKED, not scripted here — see the test
module docstring.
"""

from config.settings import web_url
from core.web.base_page import BasePage

CHAMBERS_LAW_PATH = "/web/qatar-chamber/about-us/chamber-laws"


class ChambersLawPage(BasePage):
    # ---- Hero ------------------------------------------------------------
    HERO = ".qc-cl-hero"
    HERO_OVERLAY = ".qc-cl-hero-overlay"
    HERO_MEDIA = ".qc-cl-hero-media"
    HERO_TITLE = ".qc-cl-hero-title"

    # ---- Breadcrumb --------------------------------------------------------
    BREADCRUMB_NAV = 'nav.qc-cl-breadcrumb[aria-label="Breadcrumb"]'
    BREADCRUMB_HOME_LINK = ".qc-cl-crumb-home"
    BREADCRUMB_HOME_LABEL = "[data-qc-cl-home-label]"
    BREADCRUMB_CURRENT = ".qc-cl-crumb-current"
    BREADCRUMB_ITEMS = ".qc-cl-breadcrumb .qc-cl-crumb"

    # ---- Intro block -------------------------------------------------------
    INTRO_SECTION = ".qc-cl-intro"
    INTRO_HEADING = ".qc-cl-intro-heading"
    INTRO_TEXT = ".qc-cl-intro-body"
    INTRO_FIGURE = ".qc-cl-intro-figure"
    INTRO_IMG = ".qc-cl-intro-img"

    # ---- Official Legal References section ---------------------------------
    REFS_HEADING = ".qc-cl-refs-heading"
    CARDS_CONTAINER = ".qc-cl-cards"
    CARD = ".qc-cl-card"

    # ---- Announcement modal (blocks interaction on first load) -------------
    ANNOUNCEMENT_CLOSE = '[aria-label="Close"]'

    # ---- Navigation ----------------------------------------------------------
    def open_chambers_law(self, locale: str = "en") -> "ChambersLawPage":
        self.open(web_url(CHAMBERS_LAW_PATH, locale=locale))
        self._dismiss_announcement_if_present()
        return self

    def open_via_main_menu(self) -> "ChambersLawPage":
        """Case 134872 — starts from the homepage and drives the real main
        menu (About Us hover-button -> "Chamber's Law" link), confirmed via
        `extract_locators.py` against the live header: both are `role=link`/
        `role=button` with unique accessible names."""
        self.open(web_url("/web/qatar-chamber"))
        self._dismiss_announcement_if_present()
        self.page.get_by_role("button", name="About Qatar Chamber").hover()
        self.page.get_by_role("link", name="Chamber's Law").first.click()
        return self

    def open_broken_url(self) -> "ChambersLawPage":
        """Deliberately-invalid child path under the same section, for the
        standard-error-page case (134982) — mirrors org_structure_page.py's
        disclosed substitution: the environment offers no toggle to make the
        real page's content unavailable, so an unknown child path exercises
        the site's standard not-found handling instead."""
        self.open(web_url(CHAMBERS_LAW_PATH + "-unavailable-content-check"))
        return self

    def _dismiss_announcement_if_present(self) -> None:
        try:
            if self.page.locator(self.ANNOUNCEMENT_CLOSE).count() > 0:
                self.page.locator(self.ANNOUNCEMENT_CLOSE).first.click(timeout=3000)
        except Exception:  # noqa: BLE001 — best-effort dismiss, never fatal
            pass

    # ---- Hero --------------------------------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def is_hero_overlay_visible(self) -> bool:
        return self.is_visible(self.HERO_OVERLAY)

    # ---- Breadcrumb ----------------------------------------------------------
    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.BREADCRUMB_NAV)

    def breadcrumb_home_text(self) -> str:
        return self.text(self.BREADCRUMB_HOME_LABEL)

    def breadcrumb_current_text(self) -> str:
        return self.text(self.BREADCRUMB_CURRENT)

    def breadcrumb_item_count(self) -> int:
        return self.page.locator(self.BREADCRUMB_ITEMS).count()

    def click_breadcrumb_current_ancestor(self) -> None:
        """Clicks the 'About Us' breadcrumb crumb's real anchor, wherever it
        renders (as the crumb itself, or wrapping it), for case 134986.

        CONFIRMED live via a scoped DOM probe against qcdev
        (2026-08-25): `.qc-cl-crumb-current` is a bare
        `<span class="qc-cl-crumb qc-cl-crumb-current" data-qc-cl-current>`
        with NO wrapping or nested `<a>` anywhere in the breadcrumb — only
        the "Home" crumb is an anchor. `tools/extract_locators.py` scoped to
        `nav.qc-cl-breadcrumb` surfaces exactly one link ("Home"). A direct
        `.click()` on the span times out after Playwright's full 30s
        actionability wait (confirmed live) rather than raising immediately,
        because there is nothing wrong with the selector itself — it
        resolves to a real, visible element that simply has no navigation
        behavior wired to it.

        This is therefore a genuine anchor lookup (checks the crumb itself,
        then a wrapping ancestor, then a nested child) so the method
        self-heals for free if the product ever wires a link onto this
        crumb. When no anchor resolves, it raises immediately with a
        specific message instead of clicking the span and eating a 30s
        timeout — turning a silent hang into a one-line diagnosis. The
        underlying case has a real product gap, not a locator bug: the
        terminal breadcrumb crumb is intentionally non-interactive markup
        (standard breadcrumb a11y — you don't link the "you are here" node),
        so 134986 as worded cannot be satisfied on the current live build."""
        candidates = (
            f"a{self.BREADCRUMB_CURRENT}",
            f"{self.BREADCRUMB_CURRENT} a",
            f"a:has({self.BREADCRUMB_CURRENT})",
        )
        for selector in candidates:
            loc = self.page.locator(selector)
            if loc.count() > 0:
                self.click(selector)
                self.page.wait_for_load_state("domcontentloaded")
                return
        raise AssertionError(
            "No anchor found for the 'About Us' breadcrumb crumb "
            f"({self.BREADCRUMB_CURRENT}) — confirmed live to be a bare "
            "<span> with no wrapping/nested <a>; this is a product gap "
            "(the current crumb is not a link), not a missing selector."
        )

    # ---- Intro block ---------------------------------------------------------
    def is_intro_heading_visible(self) -> bool:
        return self.is_visible(self.INTRO_HEADING)

    def intro_heading_text(self) -> str:
        return self.text(self.INTRO_HEADING)

    def intro_text_visible(self) -> bool:
        return self.is_visible(self.INTRO_TEXT)

    def intro_image_alt(self) -> str:
        return self.page.locator(self.INTRO_IMG).get_attribute("alt") or ""

    def is_intro_image_visible(self) -> bool:
        return self.is_visible(self.INTRO_IMG)

    # ---- References section ----------------------------------------------------
    def is_refs_heading_visible(self) -> bool:
        return self.is_visible(self.REFS_HEADING)

    def refs_heading_text(self) -> str:
        return self.text(self.REFS_HEADING)

    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_numbers(self) -> list:
        return self.page.locator(".qc-cl-card-number").all_inner_texts()

    def card_titles(self) -> list:
        return self.page.locator(".qc-cl-card-title").all_inner_texts()

    # ---- Per-card queries (resolved by Law Number text) -------------------------
    def _card(self, law_number: str):
        return self.page.locator(
            f'.qc-cl-card:has(.qc-cl-card-number:text-is("{law_number}"))'
        ).first

    def is_card_visible(self, law_number: str) -> bool:
        try:
            return self._card(law_number).is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's contract
            return False

    def card_title_text(self, law_number: str) -> str:
        return self._card(law_number).locator(".qc-cl-card-title").inner_text()

    def card_desc_text(self, law_number: str) -> str:
        return self._card(law_number).locator(".qc-cl-card-desc").inner_text()

    def card_icon_visible(self, law_number: str) -> bool:
        return self._card(law_number).locator(".qc-cl-card-icon").is_visible()

    def card_cta_count(self, law_number: str) -> int:
        return self._card(law_number).locator(".qc-cl-card-cta").count()

    def card_cta_label(self, law_number: str) -> str:
        return self._card(law_number).locator(".qc-cl-cta-label").inner_text()

    def card_title_href(self, law_number: str) -> str:
        return self._card(law_number).locator(".qc-cl-card-title").get_attribute("href") or ""

    def card_title_target(self, law_number: str) -> str:
        return self._card(law_number).locator(".qc-cl-card-title").get_attribute("target") or ""

    def card_cta_href(self, law_number: str) -> str:
        return self._card(law_number).locator(".qc-cl-card-cta").get_attribute("href") or ""

    def card_cta_target(self, law_number: str) -> str:
        return self._card(law_number).locator(".qc-cl-card-cta").get_attribute("target") or ""

    def card_icon_bounding_box(self, law_number: str) -> dict:
        return self._card(law_number).locator(".qc-cl-card-icon").bounding_box()

    def card_cta_bounding_box(self, law_number: str) -> dict:
        return self._card(law_number).locator(".qc-cl-card-cta").bounding_box()

    def scroll_to_card(self, law_number: str) -> None:
        self._card(law_number).scroll_into_view_if_needed()

    def click_card_cta(self, law_number: str):
        """Clicks a card's CTA and returns the resulting new-tab Page if one
        opened (target=_blank), else None (same-tab navigation)."""
        with self.page.context.expect_page(timeout=5000) as new_page_info:
            self._card(law_number).locator(".qc-cl-card-cta").click()
        try:
            return new_page_info.value
        except Exception:  # noqa: BLE001 — no new tab opened (same-tab nav)
            return None

    # ---- Layout / direction -----------------------------------------------------
    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def has_horizontal_scrollbar(self) -> bool:
        scroll_width = self.page.evaluate("() => document.documentElement.scrollWidth")
        client_width = self.page.evaluate("() => document.documentElement.clientWidth")
        return scroll_width > client_width + 1

    def computed_style(self, locator: str, props: list) -> dict:
        handle = self.page.locator(locator).first
        return handle.evaluate(
            """
            (el, props) => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = s[p];
                return out;
            }
            """,
            props,
        )

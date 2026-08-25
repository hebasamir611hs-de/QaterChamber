"""
web/pages/board_of_directors/board_of_directors_page.py — BoardOfDirectorsPage.

Public-frontend Page Object for PBI 129398 (QC-ABOUT-006 — Board of
Directors & General Director), listing page at
`/web/qatar-chamber/about-us/board-of-directors`.

Locators extracted CLI-first via tools/extract_locators.py (patched with the
license-gate clear used by core/web/license_gate.py — this standalone script
does not go through BasePage) plus a DOM class probe (mirroring
org_structure_page.py's approach) against the live qcdev.ihorizons.com
listing page at the framework's default 1920x1080 viewport, confirming the
real, stable `qc-bod-*` custom classes below:

    python tools/extract_locators.py \
      --url https://qcdev.ihorizons.com/web/qatar-chamber/about-us/board-of-directors

    -> role=link[name="Board of Directors"]  (About Us nav entry, uniq=1)
    -> role=link[name="<member full name>"]  for all 18 profile links, uniq=1

DOM probe confirmed the section/card structure:
    .qc-bod-hero > .qc-bod-hero-inner
        .qc-bod-hero-title            (page title, "Board of Directors & General Manager")
        .qc-bod-breadcrumb > .qc-bod-crumb-home / .qc-bod-crumb-current
    .qc-bod-sections
        .qc-bod-section.qc-bod-section-featured   (Chairman)
            .qc-bod-section-head > .qc-bod-eyebrow, .qc-bod-heading, .qc-bod-counter ("01 Chairman")
            .qc-bod-featured .qc-bod-badge / .qc-bod-name / .qc-bod-bio / .qc-bod-divider / .qc-bod-cta
        .qc-bod-section.qc-bod-section-duo         (Vice Chairmen, 2-col)
            .qc-bod-counter reads "02 Vice Chairmen"; each .qc-bod-duo-card has .qc-bod-position
        .qc-bod-section.qc-bod-section-grid        (Board Members, 3-col)
            .qc-bod-counter reads "14 active members" (dynamic — confirmed live, matches
            the 18 profile links minus chairman/2 vice-chairmen/GM = 14 grid cards)
            each .qc-bod-grid-card carries .qc-bod-eyebrow-sm "Board member"
        .qc-bod-section.qc-bod-section-featured    (General Manager — same featured layout
            as Chairman, badge text "Acting General Manager")

Real member names/URLs (erc=QCDEMO-129398-member-NN) confirmed live via a
scoped Playwright probe, NOT invented. All 18 members (chairman, 2 vice
chairmen, 14 board members, 1 GM) were audited profile-by-profile: EVERY
member on this environment has both a Biography and a Professional
Experience section populated — there is no bio-less or experience-less
member fixture on qcdev. Cases 133442/133446 (whose precondition explicitly
requires a member missing one of those sections) are therefore BLOCKED for
this scoped batch, not silently re-targeted (see the batch report).
"""

from config.settings import web_url
from core.web.base_page import BasePage

BOARD_OF_DIRECTORS_PATH = "/web/qatar-chamber/about-us/board-of-directors"


class BoardOfDirectorsPage(BasePage):
    # ---- Hero / breadcrumb ------------------------------------------------
    PAGE_TITLE = ".qc-bod-hero-title"
    BREADCRUMB = ".qc-bod-breadcrumb"
    BREADCRUMB_HOME_LINK = ".qc-bod-crumb-home"

    # ---- Section chrome (all 4 sections share these class names) ---------
    SECTION_FEATURED = ".qc-bod-section-featured"
    SECTION_DUO = ".qc-bod-section-duo"
    SECTION_GRID = ".qc-bod-section-grid"
    SECTIONS_CONTAINER = ".qc-bod-sections"
    EYEBROW = ".qc-bod-eyebrow"
    HEADING = ".qc-bod-heading"
    COUNTER = ".qc-bod-counter"

    # ---- Chairman / General Manager featured cards ------------------------
    FEATURED_BADGE = ".qc-bod-badge"
    FEATURED_NAME = ".qc-bod-name"
    FEATURED_BIO = ".qc-bod-bio"
    FEATURED_DIVIDER = ".qc-bod-divider"
    FEATURED_CTA = ".qc-bod-cta"

    # ---- Vice Chairmen (2-col) ---------------------------------------------
    DUO_CARD = ".qc-bod-duo-card"
    DUO_POSITION = ".qc-bod-position"

    # ---- Board Members grid (3-col) ----------------------------------------
    GRID_CARD = ".qc-bod-grid-card"
    GRID_EYEBROW_SM = ".qc-bod-eyebrow-sm"

    # ---- Navigation ---------------------------------------------------------
    def open_listing(self, locale: str = "en") -> "BoardOfDirectorsPage":
        self.open(web_url(BOARD_OF_DIRECTORS_PATH, locale=locale))
        return self

    def open_broken_url(self) -> "BoardOfDirectorsPage":
        """Deliberately-invalid path under the same section, for the
        standard-error-page case — mirrors org_structure_page.py's
        open_broken_url() since the environment has no toggle to make the
        real page's content itself unavailable."""
        self.open(web_url(BOARD_OF_DIRECTORS_PATH + "-unavailable-content-check"))
        return self

    # ---- Hero / breadcrumb --------------------------------------------------
    def page_title_text(self) -> str:
        return self.text(self.PAGE_TITLE)

    def is_page_title_visible(self) -> bool:
        return self.is_visible(self.PAGE_TITLE)

    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.BREADCRUMB)

    def breadcrumb_text(self) -> str:
        return self.text(self.BREADCRUMB)

    def breadcrumb_home_text(self) -> str:
        return self.text(self.BREADCRUMB_HOME_LINK)

    def click_breadcrumb_home(self) -> None:
        self.click(self.BREADCRUMB_HOME_LINK)
        try:
            self.page.wait_for_url(lambda url: "board-of-directors" not in url, timeout=15000)
        except Exception:
            pass  # surfaced by the caller's own URL assertion, not swallowed
        self.page.wait_for_load_state("domcontentloaded")

    # ---- Sections -------------------------------------------------------------
    def section_order(self) -> list:
        """Returns the section container class list, top to bottom, as they
        actually render — used to assert the fixed Chairman -> Vice Chairmen
        -> Board Members -> General Manager order regardless of CMS entry
        order."""
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.qc-bod-section')).map(el => {
                if (el.classList.contains('qc-bod-section-featured')) {
                    const heading = el.querySelector('.qc-bod-heading');
                    return heading ? heading.textContent.trim() : 'featured';
                }
                const heading = el.querySelector('.qc-bod-heading');
                return heading ? heading.textContent.trim() : '';
            })
            """
        )

    def is_grid_visible(self) -> bool:
        return self.is_visible(self.SECTION_GRID)

    def section_counter_text(self, heading_text: str) -> str:
        return self.page.locator(
            f'.qc-bod-section:has(.qc-bod-heading:text-is("{heading_text}")) .qc-bod-counter'
        ).first.inner_text()

    def section_eyebrow_text(self, heading_text: str) -> str:
        return self.page.locator(
            f'.qc-bod-section:has(.qc-bod-heading:text-is("{heading_text}")) .qc-bod-eyebrow'
        ).first.inner_text()

    def computed_style(self, locator, props: list) -> dict:
        """Generic Figma-token probe (mirrors org_structure_page.py's
        node_computed_style) restricted to the requested computed-style
        properties of the first match of a BasePage-style string locator."""
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

    # ---- Chairman featured card -------------------------------------------
    def chairman_card_locator(self) -> str:
        return '.qc-bod-section-featured:has(.qc-bod-badge:text-is("Chairman of the Board"))'

    def chairman_name(self) -> str:
        return self.page.locator(f'{self.chairman_card_locator()} .qc-bod-name').inner_text()

    def click_chairman_profile_link(self, member_name: str = None) -> None:
        # The card's decorative full-card stretched-link (tabindex=-1,
        # aria-hidden, over the photo only) can still intercept a click aimed
        # at .qc-bod-cta. `.qc-bod-name a` is a separate, unobstructed real
        # anchor in the card body and is structural (works in every locale,
        # unlike a role=link[name=...] lookup keyed to English text).
        self.click(f'{self.chairman_card_locator()} .qc-bod-name a')
        # Full page navigation to a member profile — qcdev's documented
        # intermittent congestion (see core/web/session_guard.py) can push
        # this past BasePage.wait_for()'s 10s default under sustained load.
        self.wait_for(".qc-bmp-hero-title", timeout=25000)

    def click_first_featured_profile_link(self) -> None:
        """Locale-agnostic Chairman-card click: chairman_card_locator()
        filters on the English badge text "Chairman of the Board", which is
        localized (and therefore absent) on the Arabic page. The Chairman
        section is always the first .qc-bod-section-featured in DOM/section
        order regardless of locale — use that instead for RTL cases."""
        self.click(f'{self.SECTION_FEATURED} >> nth=0 >> .qc-bod-name a')
        # Full page navigation to a member profile — qcdev's documented
        # intermittent congestion (see core/web/session_guard.py) can push
        # this past BasePage.wait_for()'s 10s default under sustained load.
        self.wait_for(".qc-bmp-hero-title", timeout=25000)

    # ---- General Manager featured card -------------------------------------
    def gm_card_locator(self) -> str:
        return '.qc-bod-section-featured:has(.qc-bod-badge:text-is("Acting General Manager"))'

    def gm_badge_text(self) -> str:
        return self.page.locator(f'{self.gm_card_locator()} .qc-bod-badge').inner_text()

    def click_gm_profile_link(self, member_name: str = None) -> None:
        self.click(f'{self.gm_card_locator()} .qc-bod-name a')
        # Full page navigation to a member profile — qcdev's documented
        # intermittent congestion (see core/web/session_guard.py) can push
        # this past BasePage.wait_for()'s 10s default under sustained load.
        self.wait_for(".qc-bmp-hero-title", timeout=25000)

    # ---- Vice Chairmen (2-col) -----------------------------------------------
    def vice_chairman_card_locator(self, position: str) -> str:
        return f'.qc-bod-duo-card:has(.qc-bod-position:text-is("{position}"))'

    def click_vice_chairman_profile_link(self, position: str) -> None:
        target = f'{self.vice_chairman_card_locator(position)} .qc-bod-name a'
        # The Vice Chairmen duo cards sit just below the fold on a fresh
        # listing-page load: Playwright's default actionability scroll
        # brings the target only flush with the viewport's bottom edge
        # (confirmed live: bounding box top/bottom landed at y=1043/1080 on
        # a 1080px-tall viewport), a razor-thin margin an intercepting
        # element or a sub-pixel rendering difference can eat entirely,
        # silently discarding the click (no exception — the click "lands"
        # on whatever else is at that point, not the anchor) while the
        # listing page never navigates. Force a center-of-viewport scroll
        # first so the click always lands well inside safe bounds, the same
        # class of fix as the .qc-bod-cta decorative-overlay dismiss used
        # elsewhere in this file.
        # Use the locator's own evaluate (Playwright's selector engine
        # resolves :text-is()/:has() first) rather than a raw
        # document.querySelector(sel), which cannot parse those
        # Playwright-only pseudo-classes.
        self.page.locator(target).first.evaluate(
            "(el) => el.scrollIntoView({block: 'center', inline: 'nearest'})"
        )
        self.click(target)
        # Full page navigation to a member profile — qcdev's documented
        # intermittent congestion (see core/web/session_guard.py) can push
        # this past BasePage.wait_for()'s 10s default under sustained load.
        self.wait_for(".qc-bmp-hero-title", timeout=25000)

    # ---- Board Members grid --------------------------------------------------
    def grid_card_locator_by_name(self, name: str) -> str:
        # :has-text() (substring) rather than :text-is() (exact) — robust
        # against whitespace/typography differences between the case's
        # transcribed name and the live DOM's exact text node.
        return f'.qc-bod-grid-card:has-text("{name}")'

    def click_grid_card_profile_link(self, member_name: str) -> None:
        self.click(f'{self.grid_card_locator_by_name(member_name)} .qc-bod-name a')
        # Full page navigation to a member profile — qcdev's documented
        # intermittent congestion (see core/web/session_guard.py) can push
        # this past BasePage.wait_for()'s 10s default under sustained load.
        self.wait_for(".qc-bmp-hero-title", timeout=25000)

    def grid_card_bio_text(self, name: str) -> str:
        return self.page.locator(
            f'{self.grid_card_locator_by_name(name)} .qc-bod-bio'
        ).inner_text()

    def grid_card_bio_overflow_state(self, name: str) -> dict:
        """Compares scrollHeight vs clientHeight on the bio element and reads
        its computed text-overflow/-webkit-line-clamp — used to assert
        truncation without breaking card layout (133432)."""
        handle = self.page.locator(
            f'{self.grid_card_locator_by_name(name)} .qc-bod-bio'
        ).first
        return handle.evaluate(
            """
            (el) => {
                const s = getComputedStyle(el);
                return {
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight,
                    lineClamp: s.webkitLineClamp || s.lineClamp || '',
                    textOverflow: s.textOverflow,
                };
            }
            """
        )

    def board_member_names(self) -> list:
        return self.page.locator(f"{self.GRID_CARD} {self.FEATURED_NAME}").all_inner_texts()

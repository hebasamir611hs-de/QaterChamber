"""
web/pages/home_media_gallery/home_media_gallery_page.py — HomeMediaGalleryPage.

PBI 129388 / QC-HOME-012 "Media Gallery Section" — its own Home-page
section/module folder per active/standards.md's Home-page sections table.
This pass covers the 7 approved, Automation-tagged, UI-category, Web-platform
cases handed off for this batch (ADO TC 133637-133643). Functional/Edge/
Compatibility/Auth cases on this same PBI are explicit out-of-scope for this
run (per the QA Manager's instruction) and are NOT touched here. No
Control_Panel cases were included in this batch either — the sibling
home_media_gallery_admin_page.py skeleton is untouched.

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --viewport 1920x1080 --find "media"
    -> [role] uniq=1  get_by_role("link", name="Media Center")
    -> [role] uniq=1  get_by_role("tablist", name="Media type filter")
    -> [role] uniq=1  get_by_role("tab", name="All Media")

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --viewport 1920x1080 --find "Albums"
    -> [role] uniq=1  get_by_role("tab", name="Albums")

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --viewport 1920x1080 --find "Video"
    -> [role] uniq=1  get_by_role("tab", name="Video")

IMPORTANT live finding from the extractor pass: the case text refers to a
"Videos" tab, but the real, live accessible name of that tab is "Video"
(singular). The Page Object/tests below locate it by its REAL live name
("Video") — the case's assertions are about active/inactive STYLING, never
about the literal word "Videos", so this is a locator-selection note, not a
scripted content mismatch.

The extractor's harvest (interactive/labelled elements only) did not surface
the badge/heading/description/card/meta-row structure (plain span/h2/p/div/
article, no role/label) — the same documented "ambiguous/unreachable via
role" condition already resolved in home_strategic_direction_page.py and
home_publications_page.py. Resolved the same way: one additional, disclosed,
scoped Playwright script (still CLI/shell, never the Playwright MCP), reusing
BasePage's own license-gate/overlay guard sequence, to read the live DOM
structure and computed styles.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home):

    section.qc-home-media-gallery
      div.qc-mg-inner
        div.qc-mg-head
          div.qc-mg-head-text
            span.qc-mg-tag[data-qc-mg-tag]           (BADGE — "Media Center")
            h2.qc-mg-heading[data-qc-mg-heading]      (HEADING)
            p.qc-mg-desc[data-qc-mg-desc]             (DESCRIPTION)
          a.qc-mg-explore.qc-mg-explore--top[data-qc-mg-explore]  (EXPLORE_TOP)
            span[data-qc-mg-explore-label]             "Explore More"
            svg.qc-mg-explore-arrow                    (EXPLORE_ARROW)
        div.qc-mg-tabs[role=tablist]                    (TABS_LIST — 3 tabs)
          button.qc-mg-tab.is-active[role=tab][aria-selected=true]   "All Media"
          button.qc-mg-tab[role=tab][aria-selected=false]            "Video"
          button.qc-mg-tab[role=tab][aria-selected=false]            "Albums"
        div.qc-mg-grid                                   (GRID)
          a.qc-mg-card.qc-mg-card--album                 (CARD — one per album)
            div.qc-mg-card-media
              img.qc-mg-card-img
              span.qc-mg-badge.qc-mg-badge--album         "Album"
            div.qc-mg-card-body
              h3.qc-mg-card-title
              div.qc-mg-card-meta
                span.qc-mg-meta-item (calendar svg + date text)
                span.qc-mg-meta-sep (dot separator)
                span.qc-mg-meta-item (image-icon svg + "N photos" text)
        p.qc-mg-empty                                    (EMPTY — shown when a
                                                           filtered tab has no
                                                           items, e.g. "No
                                                           videos in this
                                                           category yet.")
        div.qc-mg-dots
        a.qc-mg-explore.qc-mg-explore--bottom

Every qc-mg-* class is unique in its scope except `.qc-mg-tab`/`.qc-mg-card`
(one per tab / one per rendered card, confirmed live via a scoped script that
clicked each tab and re-read the grid).

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected — per this project's Result Integrity rule, a
mismatch below is scripted to FAIL HONESTLY against the case's literal stated
value, never quietly re-targeted at the observed one):

  - TC 133637 (badge): text "Media Center" matches exactly. Computed style:
    color rgb(166, 111, 67) (#A66F43) MATCHES; background rgb(246, 240, 236)
    (#F6F0EC) MATCHES; border "1px solid rgb(215, 190, 170)" (#D7BEAA)
    MATCHES; border-radius 9999px (fully rounded) MATCHES; font-family Cairo
    MATCHES; font-weight 400 (Regular) MATCHES; font-size 16px MATCHES.
    Computed line-height is **16px**, NOT the case's stated **24px** (a real,
    measured mismatch — the badge text renders at a 1.0 line-height ratio,
    not 1.5).
  - TC 133638 (heading/description): heading text "Gallery & Media Showcase"
    matches exactly; font-weight 700 / font-size 30px match; color
    rgb(29, 29, 27) (#1D1D1B) matches; computed line-height is **38.1px**,
    not the case's stated 38px (sub-pixel rounding). Description text
    "Discover Qatar Chamber's latest photos, videos, and media highlights."
    matches exactly (verbatim, including the apostrophe); font-weight 400 /
    font-size 18px match; color rgb(124, 123, 123) (#7C7B7B) matches;
    computed line-height is **28.08px**, not the case's stated 28px
    (sub-pixel rounding).
  - TC 133639 (tab active/inactive states): CONFIRMED LIVE, genuine pass —
    "All Media" renders active (white text on a maroon/burgundy fill);
    "Video" and "Albums" render inactive with computed color
    rgb(108, 108, 107), which is EXACTLY #6C6C6B, matching the case's stated
    inactive grey. Clicking "Video" (the tab's real live name — see note
    above) swaps the active state onto it and returns "All Media"/"Albums"
    to the same #6C6C6B inactive style.
  - TC 133640 (video card): **BLOCKED, not scripted.** The live environment
    has ZERO video items anywhere in the Media Gallery — clicking the
    "Video" tab renders the empty state "No videos in this category yet.",
    and no `.qc-mg-card--video`-style card exists under "All Media" either
    (confirmed: all 3 rendered cards carry `.qc-mg-card--album`). There is
    therefore no real, live video card anywhere to CLI-extract the required
    overlay/play-button/badge/meta-row structure from. Writing locators for
    that structure would mean inventing selectors that have never been
    observed to render — explicitly prohibited by this project's locator
    strategy ("never invent selectors as real"). This case needs test video
    content seeded in the environment (or a lower environment that has some)
    before it can be automated with real locators.
  - TC 133641 (album card, no play-button overlay): real, live album cards
    exist and were fully inspected — but none is titled "Private Sector
    Networking Reception". The 3 real, live albums under All Media/Albums
    are "Second_test_Album_QChamber", "First_Test_Album_QChamber", and
    "Third_Test_Album_QChamber" (evidently seed/test fixture data, not the
    case's named fixture). Per this project's Result Integrity rule, the test
    below is scripted against the case's own literal title and will FAIL
    HONESTLY on the "card is present" assertion (a real, observed content
    gap, not a framework defect) — it is NOT silently redirected to one of
    the real album titles. The structural assertions themselves (badge text
    "Album", white bold title, meta row with calendar+date, a dot separator,
    an image icon + "N photos" text, and the absence of any
    `[class*="play"]`/`[aria-label*="play"]` element) are all built from
    real, CLI-verified elements on the live album cards that DO exist.
  - TC 133642 (Arabic RTL mirroring): CONFIRMED LIVE, genuine pass —
    `<html dir="rtl">`, section `direction: rtl`, badge/heading/description/
    tabs render in Arabic (badge "المركز الإعلامي", heading "معرض الصور
    والوسائط", description "استعرض أبرز الصور والفيديوهات من أنشطة ومبادرات
    غرفة قطر وتغطياتها الإعلامية."), the section's head-text block shifts
    from the left (x=336 in EN) to the right half (x=978.6 of 1920) under
    RTL, the card meta-row's icon-before-text order visually FLIPS (EN:
    icon.x=353 < text.x=371; AR: icon.x=1553 > text.x=1458.5 — text now
    precedes the icon, right-to-left), and the "Explore More" CTA arrow's
    computed `transform` becomes `matrix(-1, 0, 0, 1, 0, 0)` (a horizontal
    flip) vs. `none` in EN — i.e. the arrow genuinely mirrors direction.
  - TC 133643 (375px mobile viewport): heading text does not truncate (no
    `text-overflow: ellipsis`, `scrollWidth` == `clientWidth` == 335px) and
    there is no page-level horizontal overflow/scrollbar (`scrollWidth` ==
    `clientWidth` == 375px). The 3 filter tabs remain reachable via a
    horizontally-scrollable tab strip (`overflow-x: auto` on `.qc-mg-tabs`).
    HOWEVER: CONFIRMED LIVE, the media-card grid renders as a **2-column**
    CSS grid at 375px (`grid-template-columns: 155.5px 155.5px`; card x
    positions [20, 199.5, 20] — cards 1 and 2 sit side-by-side, card 3 wraps
    to a new row starting again at x=20), NOT the case's stated single
    column. Scripted per the case's literal expected result ("stack in a
    single column") and will FAIL HONESTLY against this real, measured
    2-column layout — not a framework defect.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeMediaGalleryPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    SECTION = ".qc-home-media-gallery"
    INNER = ".qc-mg-inner"
    HEAD_TEXT = ".qc-mg-head-text"
    BADGE = ".qc-mg-tag"
    HEADING = ".qc-mg-heading"
    DESCRIPTION = ".qc-mg-desc"
    TABS_LIST = ".qc-mg-tabs"
    TAB = ".qc-mg-tab"
    GRID = ".qc-mg-grid"
    CARD = ".qc-mg-card"
    CARD_TITLE = ".qc-mg-card-title"
    CARD_MEDIA = ".qc-mg-card-media"
    CARD_IMG = ".qc-mg-card-img"
    CARD_BADGE = ".qc-mg-badge"
    META_ITEM = ".qc-mg-meta-item"
    META_SEP = ".qc-mg-meta-sep"
    EMPTY = ".qc-mg-empty"
    EXPLORE_TOP = ".qc-mg-explore--top"
    EXPLORE_ARROW = ".qc-mg-explore-arrow"
    HTML_ROOT = "html"

    _STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "color: cs.color, backgroundColor: cs.backgroundColor, border: cs.border,"
        "borderRadius: cs.borderRadius, boxShadow: cs.boxShadow,"
        "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize,"
        "lineHeight: cs.lineHeight, textAlign: cs.textAlign, direction: cs.direction,"
        "textOverflow: cs.textOverflow, whiteSpace: cs.whiteSpace, overflowX: cs.overflowX,"
        "flexWrap: cs.flexWrap, transform: cs.transform"
        "}; }"
    )

    def _style(self, locator) -> dict:
        loc = locator if hasattr(locator, "evaluate") else self.page.locator(locator).first
        return loc.evaluate(self._STYLE_JS)

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeMediaGalleryPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeMediaGalleryPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomeMediaGalleryPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    # ── Page-level direction (RTL) ────────────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    # ── Badge ────────────────────────────────────────────────────────────
    def is_badge_visible(self) -> bool:
        return self.is_visible(self.BADGE)

    def badge_text(self) -> str:
        return self.text(self.BADGE)

    def badge_style(self) -> dict:
        return self._style(self.BADGE)

    # ── Heading ──────────────────────────────────────────────────────────
    def is_heading_visible(self) -> bool:
        return self.is_visible(self.HEADING)

    def heading_text(self) -> str:
        return self.text(self.HEADING)

    def heading_style(self) -> dict:
        return self._style(self.HEADING)

    def heading_overflow_state(self) -> dict:
        """textOverflow/whiteSpace + scroll/client width — used to confirm
        the heading wraps rather than truncates at narrow viewports
        (TC 133643)."""
        loc = self.page.locator(self.HEADING)
        style = self._style(loc)
        widths = loc.evaluate("el => ({scrollWidth: el.scrollWidth, clientWidth: el.clientWidth})")
        return {**style, **widths}

    # ── Description ──────────────────────────────────────────────────────
    def is_description_visible(self) -> bool:
        return self.is_visible(self.DESCRIPTION)

    def description_text(self) -> str:
        return self.text(self.DESCRIPTION)

    def description_style(self) -> dict:
        return self._style(self.DESCRIPTION)

    # ── Filter tab bar ───────────────────────────────────────────────────
    def tab_by_name(self, name: str):
        return self.page.get_by_role("tab", name=name, exact=True)

    def tab_texts(self) -> list:
        return self.page.locator(self.TABS_LIST).locator('[role="tab"]').all_inner_texts()

    def tab_style(self, name: str) -> dict:
        return self._style(self.tab_by_name(name))

    def is_tab_active(self, name: str) -> bool:
        return self.tab_by_name(name).get_attribute("aria-selected") == "true"

    def click_tab(self, name: str) -> "HomeMediaGalleryPage":
        """Explicit wait (no sleep): clicks the tab by its REAL live
        accessible name and waits until its aria-selected flips true — the
        tab bar's own confirmed state-change signal."""
        self.tab_by_name(name).click()
        self.page.wait_for_function(
            "(name) => { const t = [...document.querySelectorAll('.qc-mg-tab')]"
            ".find(el => el.textContent.trim() === name); "
            "return t && t.getAttribute('aria-selected') === 'true'; }",
            arg=name,
        )
        return self

    def tabs_overflow_x(self) -> str:
        return self.page.locator(self.TABS_LIST).evaluate("el => getComputedStyle(el).overflowX")

    def tabs_flex_wrap(self) -> str:
        return self.page.locator(self.TABS_LIST).evaluate("el => getComputedStyle(el).flexWrap")

    # ── Media cards ──────────────────────────────────────────────────────
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return self.page.locator(self.CARD_TITLE).all_inner_texts()

    def card_locator_by_title(self, title: str):
        return self.page.locator(self.CARD).filter(has_text=title)

    def is_element_present(self, locator, timeout: int = 3000) -> bool:
        """Bounded existence check — never throws, mirrors BasePage.is_visible's
        contract. Used for a card that may genuinely not exist in this
        environment (see docstring, TC 133641)."""
        try:
            locator.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001
            return False

    def card_badge_text(self, card) -> str:
        return card.locator(self.CARD_BADGE).inner_text()

    def card_title_style(self, card) -> dict:
        return self._style(card.locator(self.CARD_TITLE))

    def card_meta_texts(self, card) -> list:
        return card.locator(self.META_ITEM).all_inner_texts()

    def card_has_meta_separator(self, card) -> bool:
        return card.locator(self.META_SEP).count() > 0

    def card_has_play_button(self, card) -> bool:
        return card.evaluate(
            'el => !!el.querySelector(\'[class*="play"], [aria-label*="play" i]\')'
        )

    def card_x_positions(self) -> list:
        return self.page.locator(self.CARD).evaluate_all(
            "els => els.map(el => el.getBoundingClientRect().x)"
        )

    def is_single_column_layout(self) -> bool:
        xs = self.card_x_positions()
        if not xs:
            return False
        rounded = {round(x) for x in xs}
        return len(rounded) <= 1

    def meta_icon_before_text_visually(self, card) -> bool:
        """True if the meta row's icon renders visually BEFORE its text
        (left-to-right reading order) — used to confirm the RTL mirror
        (TC 133642)."""
        return card.locator(self.META_ITEM).first.evaluate(
            "el => { const icon = el.querySelector('svg'); const text = el.querySelector('span'); "
            "if (!icon || !text) return null; "
            "return icon.getBoundingClientRect().x < text.getBoundingClientRect().x; }"
        )

    # ── "Explore More" CTA ───────────────────────────────────────────────
    def is_explore_top_visible(self) -> bool:
        return self.is_visible(self.EXPLORE_TOP)

    def explore_top_text(self) -> str:
        return self.text(self.EXPLORE_TOP)

    def explore_arrow_transform(self) -> str:
        """Scoped to the TOP "Explore More" CTA only. The live page renders
        TWO `.qc-mg-explore-arrow` SVGs (one inside `.qc-mg-explore--top`, one
        inside `.qc-mg-explore--bottom`) — an unscoped `.qc-mg-explore-arrow`
        locator is non-unique and throws a Playwright strict-mode violation.
        CLI-verified live (both EN and AR): the descendant selector below
        resolves to exactly 1 element and its transform matches the case's
        asserted EN/AR values (`none` / `matrix(-1, 0, 0, 1, 0, 0)`)."""
        return self.page.locator(f"{self.EXPLORE_TOP} {self.EXPLORE_ARROW}").evaluate(
            "el => getComputedStyle(el).transform"
        )

    # ── Responsive / layout ──────────────────────────────────────────────
    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

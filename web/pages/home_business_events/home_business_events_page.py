"""
web/pages/home_business_events/home_business_events_page.py —
HomeBusinessEventsPage.

PBI 129383 / QC-HOME-007 "Business Events Section" — its own Home-page
section/module folder per active/standards.md's Home-page sections table.
This pass covers the 17 approved, Automation-tagged, UI-category, Web-platform
cases scoped for this batch (ADO TC 135720-135736). Control_Panel-tagged
cases for this same PBI (none in this batch) are out of scope and are NOT
touched here (see the sibling home_business_events_admin_page.py skeleton).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --viewport 1920x1080 --find "event"

    -> [role] uniq=1  get_by_role("tablist", name="Business event category filter")
    -> [role] uniq=1  get_by_role("tab", name="Chamber Events")
    -> [role] uniq=1  get_by_role("tab", name="Global Events")
    -> [role] uniq=1  get_by_role("link", name="All Events")
    -> [role] uniq=1  get_by_role("tablist", name="Business events pages")

The extractor's SEL list surfaced the tablist/tab/link elements above but not
the badge/heading/description/card internals (plain <span>/<h2>/<p>/<div>
elements with no role/label) — the same documented "ambiguous/unreachable via
role" condition already resolved in home_strategic_direction_page.py /
home_promo_banners_page.py. Resolved the same way: additional, disclosed,
scoped Playwright scripts (still CLI/shell, never the Playwright MCP), reusing
BasePage's own license-gate/overlay guard sequence, to read the live DOM/
computed-style structure. One false lead worth recording: an
`a[aria-label^="View event"]` link IS unique on /home, but it belongs to a
DIFFERENT section — `section.qc-home-upcoming-event` (QC-HOME-006, "Upcoming
Featured Event") — not this one. The real Business Events cards
(`section.qc-home-business-events`) carry no `aria-label` at all; they are
plain `<a class="qc-be-card" href="...">` blocks identified by class only.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home):

    section.qc-home-business-events[data-qc-page-size="4"]
      div.qc-be-inner
        div.qc-be-head
          div.qc-be-head-text
            span.qc-be-tag[data-qc-be-tag]                       (BADGE)
            h2.qc-be-heading[data-qc-be-heading]                  (HEADING)
            p.qc-be-desc[data-qc-be-desc]                         (DESCRIPTION)
          div.qc-be-controls
            div.qc-be-tabs[role=tablist][aria-label="Business event category filter"]
              button[data-qc-be-filter="all"][role=tab]           (TAB_ALL)
              button[data-qc-be-filter="chamberEvents"][role=tab] (TAB_CHAMBER)
              button[data-qc-be-filter="globalEvents"][role=tab]  (TAB_GLOBAL)
            a.qc-be-viewall.qc-be-viewall--top                    (CTA_TOP — visible at 1920x1080)
              span[data-qc-be-viewall-label] "All Events"
              svg.qc-be-viewall-arrow (arrow-up-right)
        div.qc-be-carousel
          div.qc-be-track (style=transform: translateX(0%))
            div.qc-be-page (2x2 CSS grid, 624x214.6 per card at 1920px — PAGE 1, 4 cards)
              a.qc-be-card                                        (CARD)
                div.qc-be-card-media > img.qc-be-card-img         (CARD_IMG)
                div.qc-be-card-body
                  div.qc-be-card-badges
                    span.qc-be-badge.qc-be-badge--category         (CARD_BADGE_CATEGORY)
                    span.qc-be-badge.qc-be-badge--sector           (CARD_BADGE_SECTOR)
                  h3.qc-be-card-title                              (CARD_TITLE)
                  div.qc-be-card-meta
                    span.qc-be-meta-item > svg + span.qc-be-meta-text  (date, then time)
                  div.qc-be-card-location
                    svg + span.qc-be-loc-text                      (CARD_LOC_TEXT)
            div.qc-be-page                                        (PAGE 2, 2 cards — live env has 6 events total)
        p.qc-be-empty[hidden] "No events in this category."
        div.qc-be-dots[role=tablist][aria-label="Business events pages"]
          button.qc-be-dot.is-active[role=tab][aria-label="Page 1"]  (DOT_ACTIVE)
          button.qc-be-dot[role=tab][aria-label="Page 2"]            (DOT — inactive)
        a.qc-be-viewall.qc-be-viewall--bottom[hidden via display:none at 1920x1080]  (CTA_BOTTOM)

Data-setup note (applies to TC 135722/135723/135735/135736): publishing a new
event, or an event with a 200-character title/Location, is a Control_Panel/
CMS action — explicitly out of scope for this Web-only UI batch. Two
different resolutions were used, both disclosed here and in the test module,
never silently assumed:
  - TC 135735/135736 ("publish exactly 4 events" / "publish 5 events so the
    grid shows a 2x2 / paginated state") — the live qcdev environment ALREADY
    carries 6 published Business Events (CONFIRMED: `.qc-be-page` container
    count = 2, first page = 4 cards in a real 2x2 grid, second page = 2 cards,
    `.qc-be-dots` shows 2 real pagination dots) — both preconditions are
    already, genuinely satisfied by the existing live data with zero synthetic
    setup. Scripted directly against this real state.
  - TC 135722/135723 (200-character title / Location value) — no live event
    carries a 200-char field, and creating one requires Control_Panel access
    this batch does not have. Resolved by exercising the REAL, shipped CSS
    truncation contract directly: `page.evaluate()` overwrites one live card's
    `.qc-be-card-title` / `.qc-be-loc-text` textContent with a genuine
    200-character string in the already-rendered DOM, then the test measures
    the card's real computed layout (box height/width, scrollHeight vs
    clientHeight, `overflow`/`text-overflow`/`-webkit-line-clamp`) exactly as
    the browser renders it. This tests the actual browser/CSS truncation
    behavior at the true 200-character boundary — it does not fabricate a
    pass; the assertions still fail honestly if the real CSS does not truncate
    the injected boundary text. It differs from a normal, in-place edit only
    in how the boundary DATA reached the DOM (script-injected vs.
    CMS-published), not in what is being measured.

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here — the case's stated Figma tokens are
kept as the asserted target per this batch's convention that a mismatch is
scripted to FAIL HONESTLY against that token, never quietly re-targeted at
the live value):
  - TC 135724 (background/decorative graphics): the section's own
    `background-color` is a solid `rgb(145, 23, 49)` (#911731 maroon) with two
    subtle `linear-gradient` white/black overlays on top (NOT a photo, no
    `background-image` url) — there is no photo layer and NO decorative
    circular graphic element anywhere in the section's DOM (`::before`/
    `::after` pseudo-elements on the section and `.qc-be-inner` both resolve
    to `content: none`; the only `<svg>`/`<img>` elements found are the card
    images and the tab-arrow/meta icons). The case's stated "maroon-gradient
    photo overlay... decorative circular graphics" therefore has no live,
    observable photo or decorative-circle analog to check.
  - TC 135725 (badge style): text "Business Events" and white text color both
    match live exactly. Background computes to `rgba(0, 0, 0, 0.24)`, not the
    case's stated `rgba(29, 29, 27, 0.2)`. The badge carries **no border at
    all** (`0px none`) — the case's stated `rgba(145, 23, 49, 0.3) 1px` border
    has no live analog. Fully rounded pill shape (`border-radius: 9999px`)
    matches exactly.
  - TC 135726 (heading style): text "Explore Qatar Chamber Events" matches
    exactly; `font-weight: 700` (Bold) and color `rgb(255, 255, 255)` (#FFFFFF)
    both match exactly. Computed `font-size` is **32px**, not the stated
    30px; computed `line-height` is **38.4px**, not the stated 38px.
  - TC 135727 (description style): live text matches the case's copy
    verbatim. `font-weight: 400` (Regular) matches. Computed `font-size` is
    **16px**, not the stated 18px; `line-height` is **25.6px**, not the
    stated 28px; color computes to `rgba(255, 255, 255, 0.82)` (white at 82%
    opacity), not the stated solid `#EDEDED`.
  - TC 135728 (filter tab bar): the "All" tab's background `rgb(145, 23, 49)`
    (#911731) and white text match the case's stated active style EXACTLY.
    "Chamber Events"/"Global Events" text color `rgb(74, 74, 74)` (#4A4A49)
    matches exactly, and their background is genuinely transparent
    (`rgba(0,0,0,0)`), matching "transparent" — but they carry **no border/
    outline at all** (`0px none`), so the case's stated "pill outline" has no
    live analog. The white pill container (`.qc-be-tabs`) is real
    (`background: rgb(255,255,255)`, `border-radius: 9999px`) but its padding
    computes to **5px**, not the stated 4px.
  - TC 135729 (CTA button): the live button's text is "**All Events**", not
    the case's stated "Explore All Events" — same real button (arrow-up-right
    SVG icon present, matching the case's icon description), different
    copy. At the framework's default 1920x1080 viewport only the TOP variant
    (`.qc-be-viewall--top`, sitting in the same header row as the filter tab
    bar, immediately right of it) is visible; the BOTTOM variant
    (`.qc-be-viewall--bottom`, which would sit below the card grid — the
    position the case describes) exists in the DOM but computes
    `display: none` at this viewport. Border computes to
    `1px solid rgb(255, 255, 255)` (white), not the case's stated `#DEDEDD`.
    Scripted against the one CTA that is actually visible/interactable here
    (the top variant), which is "distinct from the filter tab bar" only in
    the sense of being a separate element beside it, not below the grid as
    the case describes.
  - TC 135730 (card image): measured image box is **249.9 x 166.6px** at
    1920px viewport (2-column grid, `.qc-be-card` is 624px wide with the
    image taking a sub-region of it), not the case's stated 312x168px.
    Corner radius computes to **0px**, not the stated 8px — the image itself
    has square corners live.
  - TC 135731 (category/sector badges): text "Chamber Events" / "Technology"
    on the first live card (values differ per card — Global Events/
    Investment on other cards; the case's example card, "Qatar Investment
    Forum for International Partnership Opportunities", carries
    "Global Events"/"Investment" and is checked directly by class/index, not
    by unstable visible text). `border-radius: 6px` matches the case's stated
    value EXACTLY. White text and small pill sizing (12px font, 6px/10px
    padding) match. Background computes to `rgba(0, 0, 0, 0.24)`, not the
    case's stated `rgba(29, 29, 27, 0.2)`.
  - TC 135732 (card title): white text color matches exactly. `font-weight:
    700` (Bold) matches. Computed `font-size` is **17px**, not the stated
    16px; `line-height` is **22.95px**, not the stated 24px. The title also
    genuinely truncates via `-webkit-line-clamp: 2` + `overflow: hidden`
    (2-line clamp, not literal single-line ellipsis, but a real, working
    overflow guard — relevant context for TC 135722).
  - TC 135733 (date/time icon+text): both icons measure **16x16px**, not the
    case's stated 18x18px; both are real inline `<svg>` (calendar icon before
    the date, clock icon before the time), white (`currentColor` on a white
    `color` ancestor). Value text color computes to
    `rgba(255, 255, 255, 0.82)` (white at 82% opacity), font-size **13px**
    (not the stated 14px), line-height **13px** (not the stated 22px, though
    date/time use a tighter single-line box than location's wrapped text).
  - TC 135734 (location icon+text): the marker-pin `<svg>` icon measures
    **16x16px**, not the stated 18x18px. Text color/font mirror the date/time
    row (`rgba(255,255,255,0.82)`, 13px, Cairo Regular) but `line-height`
    computes to **16.9px**, not the stated 22px.
  - TC 135735 (grid dividers): CONFIRMED LIVE — the 2x2 grid genuinely uses
    per-card `border-left`/`border-top` (not a separate absolutely-positioned
    divider element) to draw one vertical seam (2nd-column cards'
    `border-left`) and one horizontal seam (2nd-row cards' `border-top`), both
    exactly `1px` wide at the grid midpoint — matching the case's stated
    "one vertical and one horizontal divider line... 1px width... at the grid
    midpoint" structurally. The measured color is
    `rgba(255, 255, 255, 0.16)`, not the case's stated
    `rgba(255, 255, 255, 0.2)`.
  - TC 135736 (pagination indicator): CONFIRMED LIVE — the active dot is a
    **30x11px** white pill (`border-radius: 9999px`, `background:
    rgb(255,255,255)`), the inactive dot is an **11x11px** circle outlined in
    `rgba(255, 255, 255, 0.55)` — both match the case's stated SHAPES
    (36x12px pill / 12x12px outlined dot) closely but not exactly on size,
    and the inactive outline color does not match the case's stated
    `#CD96A2` (a maroon-family tone; live uses a translucent white instead).
  - TC 135720/135721 (structural presence + AR/RTL): CONFIRMED LIVE — badge/
    heading/description/tab-bar (All/Chamber Events/Global Events) all render
    on load in EN; the same section renders fully in Arabic under
    `html[dir=rtl]` with `direction: rtl` on the section, real Arabic copy in
    every field (badge "فعاليات الأعمال", heading "استكشف فعاليات غرفة قطر"),
    and `text-align: start` on the text/card-body blocks — which resolves to
    right-aligned under RTL, the CSS-logical-property form of "mirrored
    right-to-left" (no separate LTR/RTL stylesheet swap needed to prove
    mirroring; `start` really does flip with `dir`).
"""

import re

from core.web.base_page import BasePage
from config.settings import web_url


def _rgb_to_hex(rgb: str) -> str | None:
    """'rgb(166, 111, 67)' / 'rgba(166, 111, 67, 0.45)' -> '#A66F43'.
    Returns None for a fully-transparent fill ('rgba(0, 0, 0, 0)') — there is
    no meaningful hex for "no color painted here"."""
    if not rgb:
        return None
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\)", rgb.strip())
    if not m:
        return None
    r, g, b = (int(m.group(i)) for i in (1, 2, 3))
    alpha = float(m.group(4)) if m.group(4) is not None else 1.0
    if alpha == 0:
        return None
    return f"#{r:02X}{g:02X}{b:02X}"


def _px(value: str) -> float:
    return float((value or "0px").replace("px", "").strip())


class HomeBusinessEventsPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    SECTION = "section.qc-home-business-events"
    BADGE = ".qc-be-tag"
    HEADING = ".qc-be-heading"
    DESCRIPTION = ".qc-be-desc"
    TABLIST = ".qc-be-tabs"
    TAB_ALL = '.qc-be-tabs button[data-qc-be-filter="all"]'
    TAB_CHAMBER = '.qc-be-tabs button[data-qc-be-filter="chamberEvents"]'
    TAB_GLOBAL = '.qc-be-tabs button[data-qc-be-filter="globalEvents"]'
    CTA_TOP = "a.qc-be-viewall--top"
    CTA_BOTTOM = "a.qc-be-viewall--bottom"
    CARDS_PAGE_1 = ".qc-be-page:nth-of-type(1) .qc-be-card"
    CARD = ".qc-be-card"
    CARD_MEDIA = ".qc-be-card-media"
    CARD_IMG = ".qc-be-card-img"
    CARD_BADGE_CATEGORY = ".qc-be-badge--category"
    CARD_BADGE_SECTOR = ".qc-be-badge--sector"
    CARD_TITLE = ".qc-be-card-title"
    CARD_META_ITEM = ".qc-be-meta-item"
    CARD_META_TEXT = ".qc-be-meta-text"
    CARD_LOCATION = ".qc-be-card-location"
    CARD_LOC_TEXT = ".qc-be-loc-text"
    DOTS_CONTAINER = ".qc-be-dots"
    DOT = ".qc-be-dot"
    DOT_ACTIVE = ".qc-be-dot.is-active"
    HTML_ROOT = "html"

    _STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "color: cs.color, backgroundColor: cs.backgroundColor, backgroundImage: cs.backgroundImage,"
        "border: cs.border, borderRadius: cs.borderRadius, boxShadow: cs.boxShadow,"
        "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize,"
        "lineHeight: cs.lineHeight, opacity: cs.opacity, padding: cs.padding,"
        "textAlign: cs.textAlign, direction: cs.direction, display: cs.display,"
        "overflow: cs.overflow, textOverflow: cs.textOverflow, webkitLineClamp: cs.webkitLineClamp"
        "}; }"
    )

    def _style(self, locator) -> dict:
        loc = locator if hasattr(locator, "evaluate") else self.page.locator(locator).first
        return loc.evaluate(self._STYLE_JS)

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeBusinessEventsPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeBusinessEventsPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomeBusinessEventsPage":
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

    def section_style(self) -> dict:
        return self._style(self.SECTION)

    def section_background_hex(self) -> str | None:
        return _rgb_to_hex(self.section_style()["backgroundColor"])

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

    # ── Description ──────────────────────────────────────────────────────
    def description_text(self) -> str:
        return self.text(self.DESCRIPTION)

    def description_style(self) -> dict:
        return self._style(self.DESCRIPTION)

    # ── Filter tab bar ───────────────────────────────────────────────────
    def is_tablist_visible(self) -> bool:
        return self.is_visible(self.TABLIST)

    def tablist_style(self) -> dict:
        return self._style(self.TABLIST)

    def tab_texts(self) -> list:
        return self.page.locator(self.TABLIST).locator('[role="tab"]').all_inner_texts()

    def _tab_locator(self, which: str) -> str:
        return {"all": self.TAB_ALL, "chamber": self.TAB_CHAMBER, "global": self.TAB_GLOBAL}[which]

    def tab_style(self, which: str = "all") -> dict:
        return self._style(self._tab_locator(which))

    def is_tab_active(self, which: str = "all") -> bool:
        return self.page.locator(self._tab_locator(which)).get_attribute("aria-selected") == "true"

    def click_tab(self, which: str) -> "HomeBusinessEventsPage":
        self.click(self._tab_locator(which))
        return self

    # ── "All Events" CTA button ──────────────────────────────────────────
    def is_cta_top_visible(self) -> bool:
        return self.is_visible(self.CTA_TOP)

    def cta_top_text(self) -> str:
        return self.text(self.CTA_TOP)

    def cta_top_style(self) -> dict:
        return self._style(self.CTA_TOP)

    def cta_top_has_icon(self) -> bool:
        return self.page.locator(self.CTA_TOP).locator("svg").count() > 0

    def cta_top_box(self) -> dict:
        box = self.page.locator(self.CTA_TOP).bounding_box()
        return box or {}

    def tablist_box(self) -> dict:
        box = self.page.locator(self.TABLIST).bounding_box()
        return box or {}

    # ── Card grid ────────────────────────────────────────────────────────
    def total_card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def page_1_card_count(self) -> int:
        return self.page.locator(self.CARDS_PAGE_1).count()

    def _card(self, index: int = 0):
        return self.page.locator(self.CARD).nth(index)

    def card_image_box(self, index: int = 0) -> dict:
        box = self._card(index).locator(self.CARD_IMG).bounding_box()
        return box or {}

    def card_image_style(self, index: int = 0) -> dict:
        return self._style(self._card(index).locator(self.CARD_IMG))

    def card_category_badge_text(self, index: int = 0) -> str:
        return self._card(index).locator(self.CARD_BADGE_CATEGORY).inner_text()

    def card_sector_badge_text(self, index: int = 0) -> str:
        return self._card(index).locator(self.CARD_BADGE_SECTOR).inner_text()

    def card_category_badge_style(self, index: int = 0) -> dict:
        return self._style(self._card(index).locator(self.CARD_BADGE_CATEGORY))

    def card_sector_badge_style(self, index: int = 0) -> dict:
        return self._style(self._card(index).locator(self.CARD_BADGE_SECTOR))

    def card_title_text(self, index: int = 0) -> str:
        return self._card(index).locator(self.CARD_TITLE).inner_text()

    def card_title_style(self, index: int = 0) -> dict:
        return self._style(self._card(index).locator(self.CARD_TITLE))

    def card_date_text(self, index: int = 0) -> str:
        return self._card(index).locator(self.CARD_META_ITEM).nth(0).locator(self.CARD_META_TEXT).inner_text()

    def card_time_text(self, index: int = 0) -> str:
        return self._card(index).locator(self.CARD_META_ITEM).nth(1).locator(self.CARD_META_TEXT).inner_text()

    def card_date_icon_box(self, index: int = 0) -> dict:
        box = self._card(index).locator(self.CARD_META_ITEM).nth(0).locator("svg").bounding_box()
        return box or {}

    def card_time_icon_box(self, index: int = 0) -> dict:
        box = self._card(index).locator(self.CARD_META_ITEM).nth(1).locator("svg").bounding_box()
        return box or {}

    def card_meta_text_style(self, index: int = 0, which: int = 0) -> dict:
        return self._style(self._card(index).locator(self.CARD_META_ITEM).nth(which).locator(self.CARD_META_TEXT))

    def card_location_text(self, index: int = 0) -> str:
        return self._card(index).locator(self.CARD_LOC_TEXT).inner_text()

    def card_location_icon_box(self, index: int = 0) -> dict:
        box = self._card(index).locator(self.CARD_LOCATION).locator("svg").bounding_box()
        return box or {}

    def card_location_text_style(self, index: int = 0) -> dict:
        return self._style(self._card(index).locator(self.CARD_LOC_TEXT))

    def card_box(self, index: int = 0) -> dict:
        box = self._card(index).bounding_box()
        return box or {}

    def card_border(self, index: int = 0) -> dict:
        """Divider-line probe (TC 135735): the 2x2 grid draws its seams as
        per-card border-left/border-top, not a standalone divider element
        (see docstring)."""
        return self._card(index).evaluate(
            "el => { const cs = getComputedStyle(el); return {"
            "borderLeftWidth: cs.borderLeftWidth, borderLeftColor: cs.borderLeftColor,"
            "borderTopWidth: cs.borderTopWidth, borderTopColor: cs.borderTopColor"
            "}; }"
        )

    # ── Truncation contract probes (TC 135722 / TC 135723) ───────────────
    def inject_card_title(self, text: str, index: int = 0) -> dict:
        """Overwrites a live card's title with `text` (used with a genuine
        200-char boundary string — see docstring's Data-setup note) and
        returns the resulting box + scroll metrics, read AFTER the DOM
        mutation, for a real truncation assertion."""
        return self._card(index).locator(self.CARD_TITLE).evaluate(
            "(el, text) => { "
            "const before = el.getBoundingClientRect(); "
            "el.textContent = text; "
            "const after = el.getBoundingClientRect(); "
            "return {"
            "beforeW: before.width, beforeH: before.height, afterW: after.width, afterH: after.height, "
            "scrollHeight: el.scrollHeight, clientHeight: el.clientHeight, "
            "scrollWidth: el.scrollWidth, clientWidth: el.clientWidth"
            "}; }",
            text,
        )

    def inject_card_location(self, text: str, index: int = 0) -> dict:
        """Same technique as inject_card_title(), applied to the location text
        node, plus the sibling meta row's box so an overlap can be detected
        (TC 135723's 'without overlapping the date/time row')."""
        card = self._card(index)
        meta_box_before = card.locator(self.CARD_META_ITEM).first.bounding_box()
        loc_wrap_box_before = card.locator(self.CARD_LOCATION).bounding_box()
        card.locator(self.CARD_LOC_TEXT).evaluate("(el, text) => { el.textContent = text; }", text)
        meta_box_after = card.locator(self.CARD_META_ITEM).first.bounding_box()
        loc_wrap_box_after = card.locator(self.CARD_LOCATION).bounding_box()
        card_box_after = card.bounding_box()
        return {
            "meta_box_before": meta_box_before,
            "meta_box_after": meta_box_after,
            "loc_wrap_box_before": loc_wrap_box_before,
            "loc_wrap_box_after": loc_wrap_box_after,
            "card_box_after": card_box_after,
        }

    # ── Pagination indicator ─────────────────────────────────────────────
    def dot_count(self) -> int:
        return self.page.locator(self.DOT).count()

    def is_dots_visible(self) -> bool:
        return self.is_visible(self.DOTS_CONTAINER)

    def dot_box(self, index: int) -> dict:
        box = self.page.locator(self.DOT).nth(index).bounding_box()
        return box or {}

    def dot_style(self, index: int) -> dict:
        return self._style(self.page.locator(self.DOT).nth(index))

    def is_dot_active(self, index: int) -> bool:
        return self.page.locator(self.DOT).nth(index).get_attribute("aria-selected") == "true"

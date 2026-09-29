"""
web/pages/home_strategic_direction/home_strategic_direction_page.py —
HomeStrategicDirectionPage.

PBI 129381 / QC-HOME-005 "Strategic Direction Section" — its own Home-page
section/module folder per active/standards.md's Home-page sections table. This
pass covers the 23 approved, Automation-tagged, UI-category, Web-platform
cases scoped for this batch (ADO TC 135515-135537). Control_Panel-tagged
cases for this same PBI are explicit out-of-scope for this run and are NOT
touched here (see the sibling home_strategic_direction_admin_page.py
skeleton).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --viewport 1920x1080

    -> [role] uniq=1  get_by_role("button", name="Previous pillar")
    -> [role] uniq=1  get_by_role("button", name="Next pillar")

The extractor's SEL list (a,button,input,select,textarea,[role],[data-testid],
[data-test],[aria-label],[contenteditable]) surfaced only the two nav-arrow
buttons — the badge, heading, description, pillar card, progress/"peek"
elements, and the decorative mandala graphic are plain <span>/<h2>/<p>/<div>
elements with no role/label, the same documented "ambiguous/unreachable via
role" condition already resolved in home_promo_banners_page.py. Resolved the
same way: one additional, disclosed, scoped Playwright script (still CLI/
shell, never the Playwright MCP), reusing BasePage's own license-gate/overlay
guard sequence, to read the live DOM/computed-style structure.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home):

    section.qc-home-strategic-direction                     (SECTION, position:relative)
      img.qc-home-strategic-direction-img                   (MANDALA — decorative, position:absolute, z-index:0)
      div.qc-sd-inner                                        (INNER — centered, max-width:1248px)
        div.qc-sd-text
          span.qc-sd-tag[data-qc-sd-tag]                     (BADGE)
          h2.qc-sd-heading[data-qc-sd-heading]                (HEADING)
          p.qc-sd-desc[data-qc-sd-desc]                       (DESCRIPTION)
        div.qc-sd-carousel[data-qc-sd-carousel]                (CAROUSEL)
          div.qc-sd-deck
            div.qc-sd-stage[data-qc-sd-stage][aria-live=polite]  (STAGE)
              article.qc-sd-card.is-active                    (ACTIVE_CARD — Vision, first load)
                span.qc-sd-card-icon > img                    (CARD_ICON, relative)
                div.qc-sd-card-body                           (display:contents — no own box)
                  h3.qc-sd-card-title                          (CARD_TITLE, relative)
                  div.qc-sd-card-desc > p                      (CARD_DESC, relative)
              article.qc-sd-card                              -- Mission (opacity:0, position:absolute
              article.qc-sd-card                              -- Objectives   while inactive — NOT
                                                                  display:none/visibility:hidden, so a
                                                                  bare Playwright is_visible() would
                                                                  wrongly report them visible; state
                                                                  queries below read computed opacity)
            div.qc-sd-peek.qc-sd-peek--1[aria-hidden]           (PEEK_1 — decorative stacked-card edge)
            div.qc-sd-peek.qc-sd-peek--2[aria-hidden]           (PEEK_2 — decorative stacked-card edge)
          div.qc-sd-nav[data-qc-sd-nav]
            button.qc-sd-arrow.qc-sd-arrow--prev[aria-label="Previous pillar"]  (ARROW_PREV)
            button.qc-sd-arrow.qc-sd-arrow--next[aria-label="Next pillar"]      (ARROW_NEXT)

Every qc-sd-* class is unique in its scope (single instance of each container,
confirmed live via `page.locator(sel).count()` except `.qc-sd-card`, which has
exactly 3 — the three pillar articles).

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here — the case's stated Figma tokens are
kept as the asserted target per this batch's instruction that they are
"already-confirmed-correct design tokens"; a mismatch below is scripted to
FAIL HONESTLY against that token, never quietly re-targeted at the live
value):
  - TC 135515: the section itself carries NO literal `background-color` —
    it is `rgba(0, 0, 0, 0)` with a `radial-gradient(90% 120% at 100% 0%,
    rgb(249, 242, 236) 0%, rgba(249, 242, 236, ...))` `background-image`
    instead. `section_background_hex()` below resolves the visually-rendered
    token from that gradient's first color stop for a meaningful comparison:
    the real value is **#F9F2EC**, not the case's stated **#F6F0EC** (off by
    3/2/0 on R/G/B) — a small but real, measured mismatch.
  - TC 135516: badge text color #A66F43 matches live EXACTLY
    (`rgb(166, 111, 67)`). Badge background is transparent live (no
    literal #F6F0EC fill on the badge element itself — it just shows the
    section's own background through). Badge border computed
    `rgb(228, 208, 188)` (#E4D0BC) does NOT match the case's stated
    **#D7BEAA** (#D7BEAA = rgb(215, 190, 170)).
  - TC 135517: heading text matches "Our Strategic Direction" exactly.
    font-weight 700 / font-size 30px match; computed line-height is
    **37.5px** (30px * 1.25), not the case's stated 38px. Color
    `rgb(29, 29, 27)` (#1D1D1B) matches exactly.
  - TC 135518: description text matches the case's wording exactly in
    content (the live text renders a typographic right-single-quote U+2019
    in "Chamber's role" rather than a straight apostrophe — same word, a
    cosmetic glyph difference, not a content defect). font-weight 400 /
    font-size 16px match; computed line-height is **25.6px** (16 * 1.6), not
    the stated 24px. Color computed `rgb(108, 108, 107)` (#6C6C6B) does NOT
    match the case's stated **#7C7B7B**.
  - TC 135519: card background #E9DBD0 matches live EXACTLY
    (`rgb(233, 219, 208)`). Border color channel matches #A66F43
    (`rgba(166, 111, 67, 0.45)` — same RGB, rendered at 45% alpha, which the
    case's wording doesn't call out one way or the other). border-radius
    16px matches exactly. Card width computed **508px**, not the case's
    stated 516px.
  - TC 135520: pillar title "Vision" font-weight 700 / font-size 20px match;
    computed line-height is **28px** (20 * 1.4), not the case's stated 30px.
    Color `rgb(166, 111, 67)` (#A66F43) matches exactly.
  - TC 135521: Vision pillar description text matches the case's wording
    exactly, verbatim. font-weight 400 / font-size 14px match; computed
    line-height is 22.4px vs. the case's stated 22px (a sub-pixel rounding
    difference). Color computed `rgb(74, 66, 59)` (#4A423B) does NOT match
    the case's stated **#343432**.
  - TC 135522: nav arrows are circular (`border-radius: 9999px`) and
    opaque-white-filled (`rgb(255, 255, 255)`), matching the case's shape/
    fill description. Measured box is **44x44px**, not the case's stated
    40x40px. Border computed `rgb(228, 208, 188)` (#E4D0BC) does NOT match
    the case's stated **#E9DBD0**.
  - TC 135523/135532: there is NO discrete "N of 3" progress indicator
    anywhere in the live DOM. The only structural candidates are two static
    decorative "peek" strips (`.qc-sd-peek--1`/`--2`) simulating a stacked-
    card deck behind the active card. Their border-radius IS exactly
    `0px 0px 16px 16px` — bottom corners 16px, top corners 0, matching the
    case's stated shape precisely. Their fill colors are
    `rgb(221, 201, 182)` (#DDC9B6) and `rgb(211, 188, 166)` (#D3BCA6) —
    neither matches the case's stated **#D7BEAA** / **#B3845F**. CONFIRMED
    LIVE (clicked Next twice, then once more to wrap back to Vision): these
    two peek strips' color AND width are IDENTICAL before/after every click,
    regardless of which pillar (Vision/Mission/Objectives) is active — they
    do not track position at all. TC 135532's expected "updates 1-of-3 ->
    2-of-3" therefore has no live, observable analog to advance toward;
    scripted per the case's literal expected result and will fail honestly,
    not a framework defect.
  - TC 135524: mandala graphic computed `opacity: 0.3` (30%), not the
    case's stated "~20%". It DOES animate/rotate live
    (`animation-name: qc-sd-star-spin`, confirmed non-"none"). It is
    `position: absolute; z-index: 0` while `.qc-sd-inner` (the real content)
    is a normal in-flow, non-positioned sibling — by CSS stacking rules an
    in-flow block box paints BEFORE (i.e., below) a positioned z-index:0
    sibling, so the graphic is capable of painting over content in any
    region where their boxes overlap. Its own bounding box
    (x:1372-2187, y:64-880 at 1920 width) overflows well past the visible
    section box on the right/top/bottom and only partially overlaps the
    carousel's box — confirmed live that the pillar card and both nav arrows
    remain independently clickable/visible with the graphic present, which
    is the practical, observable form of "not obscuring foreground" scripted
    below (no pixel-level screenshot diff attempted).
  - TC 135525: section padding-top/bottom computed **80px** — matches the
    case's stated value exactly. Effective left/right content gap (measured
    from the section's edge to `.qc-sd-inner`'s edge, at 1920 width) is
    **336px** (section padding-left/right is a bare 16px; the remaining gap
    comes from `.qc-sd-inner`'s own `max-width: 1248px` centered in the
    available width) — not the case's stated 300px.
  - TC 135526: the carousel container (arrow + card + arrow,
    `.qc-sd-carousel`) measures **620px** wide, not the case's stated 636px.
    The visual gap between an arrow and the card is **~12px**
    (`prev` right edge 1008 -> stage left edge 1020 at EN 1920px), not the
    case's stated 20px.
  - TC 135527: pillar icon measures **64x64px**, not the case's stated
    72x72px. Card padding computed `22px 24px` (top/bottom 22px, matching
    neither the case's stated 20px on that axis, though left/right 24px does
    match); the icon-to-text column-gap is `20px` (`gap: 8px 20px` ->
    row-gap 8px / column-gap 20px), not the case's stated single 16px gap.
  - TC 135529: CONFIRMED LIVE — exactly one `.qc-sd-card` carries
    `.is-active` (`opacity: 1`) at any time; the other two are `opacity: 0`
    (still `display:grid`/`visibility:visible`, so a bare
    `Locator.is_visible()` would misreport them as visible — state queries
    below read computed opacity instead, per the docstring's structure
    note). Real, genuine pass.
  - TC 135530/135531: CONFIRMED LIVE — one Next-arrow click moves the active
    card from Vision to Mission; one Previous-arrow click from there returns
    to Vision. Real, genuine pass.
  - TC 135533: CONFIRMED LIVE — each `.qc-sd-card` has a real, non-zero
    `transition: opacity 0.42s, transform 0.42s`, i.e. a real, timed cross-
    fade, not an instant hard-cut. Real, genuine pass.
  - TC 135534: CONFIRMED LIVE (AR, https://qcdev.ihorizons.com/ar/home):
    `<html dir="rtl">`, section `direction: rtl`, badge/heading/description/
    Vision-pillar copy render in Arabic (non-empty, distinct per field), and
    the two-column layout genuinely swaps sides — `.qc-sd-text` moves to
    x=1004 (right half) and `.qc-sd-carousel` moves to x=336 (left half),
    the mirror image of EN's text-left/carousel-right order. One nuance
    NOT asserted as a failure (the case doesn't require it): the Prev/Next
    arrows themselves keep the same left-to-right relative order inside the
    mirrored carousel (Prev still renders left-of-Next) rather than swapping
    icon assignment — noted here for visibility, not scripted as a defect.
  - TC 135535/135536/135537: CONFIRMED LIVE — no horizontal page overflow
    (`document.documentElement.scrollWidth == clientWidth`) at 375x812,
    768x1024, or 1920x1080, and the section/stage render with a real,
    non-zero box at each width.
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


def _first_gradient_stop_hex(background_image: str) -> str | None:
    """Pulls the first rgb()/rgba() color stop out of a CSS
    `background-image` gradient string — the visually-rendered "background
    color" for a section whose own `background-color` is transparent by
    design (see docstring, TC 135515)."""
    m = re.search(r"rgba?\([^)]*\)", background_image or "")
    return _rgb_to_hex(m.group(0)) if m else None


def _px(value: str) -> float:
    return float((value or "0px").replace("px", "").strip())


class HomeStrategicDirectionPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    SECTION = ".qc-home-strategic-direction"
    INNER = ".qc-sd-inner"
    MANDALA = ".qc-home-strategic-direction-img"
    BADGE = ".qc-sd-tag"
    HEADING = ".qc-sd-heading"
    DESCRIPTION = ".qc-sd-desc"
    CAROUSEL = ".qc-sd-carousel"
    STAGE = ".qc-sd-stage"
    CARD = ".qc-sd-card"
    ACTIVE_CARD = ".qc-sd-card.is-active"
    # Relative selectors — always chained off a specific card Locator via
    # `.locator(...)`, never resolved standalone (3 cards share these classes).
    CARD_ICON = ".qc-sd-card-icon"
    CARD_TITLE = ".qc-sd-card-title"
    CARD_DESC = ".qc-sd-card-desc p"
    PEEK_1 = ".qc-sd-peek--1"
    PEEK_2 = ".qc-sd-peek--2"
    ARROW_PREV = ".qc-sd-arrow--prev"
    ARROW_NEXT = ".qc-sd-arrow--next"
    HTML_ROOT = "html"

    _STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "color: cs.color, backgroundColor: cs.backgroundColor, backgroundImage: cs.backgroundImage,"
        "border: cs.border, borderRadius: cs.borderRadius, boxShadow: cs.boxShadow,"
        "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize,"
        "lineHeight: cs.lineHeight, opacity: cs.opacity, padding: cs.padding,"
        "paddingTop: cs.paddingTop, paddingRight: cs.paddingRight,"
        "paddingBottom: cs.paddingBottom, paddingLeft: cs.paddingLeft,"
        "gap: cs.gap, width: cs.width, height: cs.height, animationName: cs.animationName,"
        "transitionDuration: cs.transitionDuration, textAlign: cs.textAlign,"
        "direction: cs.direction, display: cs.display, visibility: cs.visibility,"
        "position: cs.position, zIndex: cs.zIndex"
        "}; }"
    )

    def _style(self, locator) -> dict:
        loc = locator if hasattr(locator, "evaluate") else self.page.locator(locator).first
        return loc.evaluate(self._STYLE_JS)

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeStrategicDirectionPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeStrategicDirectionPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomeStrategicDirectionPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    # ── Page-level direction ─────────────────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    # ── Section background (TC 135515) ───────────────────────────────────
    def section_background_hex(self) -> str | None:
        style = self._style(self.SECTION)
        direct = _rgb_to_hex(style["backgroundColor"])
        if direct:
            return direct
        return _first_gradient_stop_hex(style["backgroundImage"])

    def section_padding(self) -> dict:
        style = self._style(self.SECTION)
        return {
            "top": _px(style["paddingTop"]),
            "right": _px(style["paddingRight"]),
            "bottom": _px(style["paddingBottom"]),
            "left": _px(style["paddingLeft"]),
        }

    def section_content_side_gaps(self) -> dict:
        """Effective left/right gap between the section's own edge and its
        centered `.qc-sd-inner` content box — the real "left/right padding"
        a visitor perceives (see docstring, TC 135525)."""
        section_box = self.page.locator(self.SECTION).bounding_box()
        inner_box = self.page.locator(self.INNER).bounding_box()
        return {
            "left": inner_box["x"] - section_box["x"],
            "right": (section_box["x"] + section_box["width"]) - (inner_box["x"] + inner_box["width"]),
        }

    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def is_badge_visible(self) -> bool:
        return self.is_visible(self.BADGE)

    def is_heading_visible(self) -> bool:
        return self.is_visible(self.HEADING)

    def is_description_visible(self) -> bool:
        return self.is_visible(self.DESCRIPTION)

    def is_active_card_visible(self) -> bool:
        return self.is_visible(self.ACTIVE_CARD)

    def is_carousel_visible(self) -> bool:
        return self.is_visible(self.CAROUSEL)

    # ── Badge ────────────────────────────────────────────────────────────
    def badge_text(self) -> str:
        return self.text(self.BADGE)

    def badge_style(self) -> dict:
        return self._style(self.BADGE)

    # ── Heading ──────────────────────────────────────────────────────────
    def heading_text(self) -> str:
        return self.text(self.HEADING)

    def heading_style(self) -> dict:
        return self._style(self.HEADING)

    # ── Description ──────────────────────────────────────────────────────
    def description_text(self) -> str:
        return self.text(self.DESCRIPTION)

    def description_style(self) -> dict:
        return self._style(self.DESCRIPTION)

    # ── Pillar cards (deck) ──────────────────────────────────────────────
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def active_card_title_text(self) -> str:
        return self.page.locator(self.ACTIVE_CARD).locator(self.CARD_TITLE).inner_text()

    def active_card_description_text(self) -> str:
        return self.page.locator(self.ACTIVE_CARD).locator(self.CARD_DESC).inner_text()

    def active_card_style(self) -> dict:
        return self._style(self.page.locator(self.ACTIVE_CARD))

    def active_card_title_style(self) -> dict:
        return self._style(self.page.locator(self.ACTIVE_CARD).locator(self.CARD_TITLE))

    def active_card_description_style(self) -> dict:
        return self._style(self.page.locator(self.ACTIVE_CARD).locator(self.CARD_DESC))

    def active_card_icon_size(self) -> dict:
        box = self.page.locator(self.ACTIVE_CARD).locator(self.CARD_ICON).bounding_box()
        return {"width": box["width"], "height": box["height"]} if box else {"width": 0, "height": 0}

    def visible_card_titles(self) -> list:
        """Reads computed OPACITY across all 3 cards, not Playwright's own
        is_visible() — the inactive cards are `display:grid;visibility:
        visible;opacity:0` (see docstring), which a bare visibility check
        would misreport as visible."""
        return self.page.locator(self.CARD).evaluate_all(
            "els => els.filter(el => parseFloat(getComputedStyle(el).opacity) > 0)"
            ".map(el => el.querySelector('.qc-sd-card-title')?.textContent || null)"
        )

    def card_transition_duration_seconds(self) -> float:
        raw = self.active_card_style()["transitionDuration"]
        first = raw.split(",")[0].strip()
        return float(first.replace("s", "")) if first.endswith("s") else 0.0

    # ── Nav arrows ───────────────────────────────────────────────────────
    def _arrow_locator(self, which: str) -> str:
        return self.ARROW_NEXT if which == "next" else self.ARROW_PREV

    def is_arrow_visible(self, which: str = "next") -> bool:
        return self.is_visible(self._arrow_locator(which))

    def arrow_style(self, which: str = "next") -> dict:
        return self._style(self._arrow_locator(which))

    def arrow_box_size(self, which: str = "next") -> dict:
        box = self.page.locator(self._arrow_locator(which)).bounding_box()
        return {"width": box["width"], "height": box["height"]} if box else {"width": 0, "height": 0}

    def is_arrow_circular(self, which: str = "next", tolerance: float = 1.0) -> bool:
        style = self.arrow_style(which)
        br = style["borderRadius"].strip()
        if br.endswith("%"):
            return float(br.rstrip("%")) >= 50
        size = self.arrow_box_size(which)
        half = min(size["width"], size["height"]) / 2
        return _px(br) >= half - tolerance

    def arrow_x_position(self, which: str = "next") -> float:
        box = self.page.locator(self._arrow_locator(which)).bounding_box()
        return box["x"] if box else None

    def click_next(self) -> "HomeStrategicDirectionPage":
        self._click_arrow_and_wait_for_change(self.ARROW_NEXT)
        return self

    def click_prev(self) -> "HomeStrategicDirectionPage":
        self._click_arrow_and_wait_for_change(self.ARROW_PREV)
        return self

    def _click_arrow_and_wait_for_change(self, arrow_locator: str) -> None:
        """Explicit wait (no sleep): captures the active card's title BEFORE
        the click, then waits until the active card's title differs — the
        carousel's own confirmed slide-change signal (see docstring)."""
        old_title = self.active_card_title_text()
        self.click(arrow_locator)
        self.page.wait_for_function(
            "(old) => { const t = document.querySelector('.qc-sd-card.is-active .qc-sd-card-title'); "
            "return t && t.textContent !== old; }",
            arg=old_title,
        )

    # ── Progress / "peek" stacked-card indicator ─────────────────────────
    def peek_style(self, index: int) -> dict:
        return self._style(self.PEEK_1 if index == 1 else self.PEEK_2)

    def peek_snapshot(self) -> dict:
        """A comparable snapshot of both peek strips' fill + width — used to
        check whether the "progress indicator" changes across a slide
        transition (see docstring, TC 135523/135532)."""
        p1, p2 = self.peek_style(1), self.peek_style(2)
        return {
            "peek1": (p1["backgroundColor"], p1["width"]),
            "peek2": (p2["backgroundColor"], p2["width"]),
        }

    # ── Decorative mandala background graphic ────────────────────────────
    def mandala_style(self) -> dict:
        return self._style(self.MANDALA)

    def is_mandala_animating(self) -> bool:
        return self.mandala_style()["animationName"].strip().lower() != "none"

    # ── Carousel container geometry ──────────────────────────────────────
    def carousel_box(self) -> dict:
        return self.page.locator(self.CAROUSEL).bounding_box()

    def arrow_to_card_gap(self, which: str = "prev") -> float:
        arrow_box = self.page.locator(self._arrow_locator(which)).bounding_box()
        stage_box = self.page.locator(self.STAGE).bounding_box()
        if not arrow_box or not stage_box:
            return None
        if which == "prev":
            return stage_box["x"] - (arrow_box["x"] + arrow_box["width"])
        return arrow_box["x"] - (stage_box["x"] + stage_box["width"])

    # ── Responsive / layout ──────────────────────────────────────────────
    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def stage_box(self) -> dict:
        return self.page.locator(self.STAGE).bounding_box()

    # ── RTL layout swap (TC 135534) ───────────────────────────────────────
    def text_block_x(self) -> float:
        box = self.page.locator(".qc-sd-text").bounding_box()
        return box["x"] if box else None

    def carousel_x(self) -> float:
        box = self.page.locator(self.CAROUSEL).bounding_box()
        return box["x"] if box else None

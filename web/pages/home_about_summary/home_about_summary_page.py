"""
web/pages/home_about_summary/home_about_summary_page.py — HomeAboutSummaryPage.

PBI 129389 / QC-HOME-013 "About Us Section & Last Year Achievements Counters"
(bundled as one Page Object per active/standards.md's Home-page sections
table — "split later if the PBI is split"). This pass covers the 7 approved,
Automation-tagged, UI-category, Web-platform cases handed off directly for
this PBI (ADO TC 136088, 136089, 136090, 136091, 136093, 136094, 136097).
Functional/Edge/Compatibility/Auth-tagged cases sharing the ABOUT tag on this
same PBI are explicit out-of-scope for this run and are NOT touched here (see
the sibling home_about_summary_admin_page.py skeleton for the still-untouched
Control_Panel side).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --viewport 1920x1080 --max 200

The extractor's SEL list (a,button,input,select,textarea,[role],[data-testid],
[data-test],[aria-label],[contenteditable]) surfaced only one interactive
element inside this section — the "Read More" CTA link — and it came back
NON-UNIQUE (10 "Read More" links site-wide, one per Home-page section
carousel/list). The badge overlay, tag/heading/description block, image
collage, achievements sub-heading, and the 4 counters are plain
<span>/<div>/<img> elements with no role/label — the same documented
"ambiguous/unreachable via role" condition already resolved in
home_strategic_direction_page.py and home_promo_banners_page.py. Resolved the
same way: one additional, disclosed, scoped Playwright script (still CLI/
shell, never the Playwright MCP), reusing BasePage's own license-gate/overlay
guard sequence, to read the live DOM/computed-style/geometry structure and to
scope the "Read More" locator to this section's own container (making it
unique within `.qc-home-about-us`).

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home):

    section.qc-home-about-us                                (SECTION)
      div.qc-about-inner                                     (INNER)
        div.qc-about-media                                   (MEDIA — left half, x=336 EN / x=992 AR)
          div.qc-about-collage                                (COLLAGE)
            div.qc-about-collage-item.qc-about-collage-primary > img   (COLLAGE_PRIMARY — 544x616.5, x=358,y=133)
            div.qc-about-collage-item.qc-about-collage-secondary > img (COLLAGE_SECONDARY — 239x182.5, x=688.6,y=591.4)
          div.qc-about-badge[position:absolute][z-index:3]      (BADGE — overlay, overlaps collage-primary's
                                                                    top-left corner; CONFIRMED LIVE via
                                                                    bounding-box overlap test)
            span.qc-about-badge-num                             (BADGE_NUM — "62+")
            span.qc-about-badge-label                           (BADGE_LABEL — "Years of Experience")
        div.qc-about-content                                  (CONTENT — right half, x=992 EN / x=336 AR)
          span.qc-about-tag                                    (TAG — "MORE ABOUT US")
          h2.qc-about-heading                                  (HEADING — "Qatar Chamber")
          p.qc-about-desc                                      (DESCRIPTION)
          div.qc-about-cta-row
            a.qc-about-readmore[href]                           (READMORE — "Read More" ->
                                                                    /web/qatar-chamber/about-us)
              span.qc-about-readmore-arrow
      div.qc-about-achievements
        h3.qc-about-achievements-title[font-weight:700]         (ACHIEVEMENTS_TITLE — "Last Year Achievements",
                                                                    y=845.9, directly above COUNTERS which
                                                                    starts at y=907.5 — CONFIRMED LIVE, no
                                                                    overlap, ~28px gap)
        div.qc-about-counters[data-qc-about-counters]           (COUNTERS)
          div.qc-about-counter (x4)                             (COUNTER)
            span.qc-about-counter-icon > img                    (COUNTER_ICON — 150x150 SVG, all 4 loaded)
            div.qc-about-counter-text
              span.qc-about-counter-value                       (COUNTER_VALUE — count-up text, see below)
              span.qc-about-counter-label                       (COUNTER_LABEL)

Every qc-about-* class is unique in its scope (single instance of each
container, confirmed live via `page.locator(sel).count()`, except
`.qc-about-collage-item`/`.qc-about-counter`, which have exactly 2 and 4
respectively — the collage images and the 4 achievement counters).

Real, CLI-verified findings from this extraction pass (these cases do not
themselves cite literal Figma pixel/color tokens the way home_strategic_
direction's did — they assert structure/content/behavior — so no
"stated-vs-live mismatch" table is needed here; the one place a genuinely
external "expected" value could differ is the counters' final numbers, see
below):

  - TC 136088: CONFIRMED LIVE — the section renders below the fold with the
    image collage, badge overlay, tag ("MORE ABOUT US"), heading ("Qatar
    Chamber"), description, Read More CTA, and a 4-counter block, all
    simultaneously visible after scrolling into view. Real, genuine pass.
  - TC 136089: CONFIRMED LIVE — exactly 2 collage images
    (`.qc-about-collage-item img`), both `complete === true` with
    `naturalWidth > 0` (no broken-image icon), and their bounding boxes
    genuinely overlap: collage-primary spans x:358-902/y:133-749.5,
    collage-secondary spans x:688.6-928/y:591.4-773.9 — overlapping region
    x:688.6-902/y:591.4-749.5 is non-empty. Real, genuine pass.
  - TC 136090: CONFIRMED LIVE — badge displays "62+" / "Years of Experience",
    `position: absolute; z-index: 3`, and its bounding box
    (x:322-488.8/y:115.3-201.7) overlaps collage-primary's own box
    (x:358-902/y:133-749.5) — a real overlay, not just adjacent placement.
    Real, genuine pass.
  - TC 136091: CONFIRMED LIVE (EN https://qcdev.ihorizons.com/home, AR
    https://qcdev.ihorizons.com/ar/home) — tag/heading/description render in
    the active language with distinct EN/AR text, `<html dir="rtl">` and
    `.qc-home-about-us { direction: rtl }` in AR. Real, genuine pass.
  - TC 136093: CONFIRMED LIVE — "Last Year Achievements" /
    "إنجازات العام الماضي" renders with `font-weight: 700` (bold) and its
    box sits directly above `.qc-about-counters`' box with no overlap. Real,
    genuine pass.
  - TC 136094: CONFIRMED LIVE — all 4 `.qc-about-counter-value` spans read
    literally "0" (padded, e.g. "0 +" / "0K +") the instant the section
    scrolls into view, before any wait; they then animate upward and settle
    (2 consecutive 200ms polls reading the identical string — see
    `wait_for_counters_to_settle()` below) at "145 +" / "70K +" / "210K +" /
    "200 +" for E-Services / Certificates Issued / Documents Attested /
    Business Events respectively. There is no `data-target`/`data-count`
    attribute anywhere on the counter DOM exposing the "configured Counter
    Value" independently of the rendered animation — the live, settled
    render IS the only observable "configured value" available from this
    (Web-only, Control_Panel out of scope this run) surface, so it is kept as
    the asserted target, per this project's established convention of
    scripting the case's literal expected result against the best available
    live signal. Real, genuine pass.
  - TC 136097: CONFIRMED LIVE — AR media/content halves are the true mirror
    of EN (EN: media x=336/content x=992 <-> AR: media x=992/content x=336),
    and `document.documentElement.scrollWidth <= clientWidth` (no horizontal
    clipping) at both EN and AR, 1920x1080. Real, genuine pass.
"""

import re

from core.web.base_page import BasePage
from config.settings import web_url


def _parse_counter_number(text: str) -> int:
    """'145 +' -> 145, '70K +' -> 70000, '62+' -> 62. The live counter text is
    always digits, optional 'K' (thousands) suffix, and a trailing '+' —
    never any other unit on this section (see docstring)."""
    s = text.strip().rstrip("+").strip()
    mult = 1
    if s.upper().endswith("K"):
        mult = 1000
        s = s[:-1].strip()
    s = re.sub(r"[^\d.]", "", s)
    return int(float(s) * mult) if s else 0


def _boxes_overlap(a: dict, b: dict) -> bool:
    """True if two {x,y,w,h} boxes share any area — a real visual overlay/
    overlap, not merely adjacent placement."""
    return not (
        a["x"] + a["w"] <= b["x"]
        or b["x"] + b["w"] <= a["x"]
        or a["y"] + a["h"] <= b["y"]
        or b["y"] + b["h"] <= a["y"]
    )


class HomeAboutSummaryPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    SECTION = ".qc-home-about-us"
    INNER = ".qc-about-inner"
    MEDIA = ".qc-about-media"
    COLLAGE = ".qc-about-collage"
    COLLAGE_ITEM_IMG = ".qc-about-collage-item img"
    COLLAGE_PRIMARY = ".qc-about-collage-primary"
    COLLAGE_SECONDARY = ".qc-about-collage-secondary"
    BADGE = ".qc-about-badge"
    BADGE_NUM = ".qc-about-badge-num"
    BADGE_LABEL = ".qc-about-badge-label"
    CONTENT = ".qc-about-content"
    TAG = ".qc-about-tag"
    HEADING = ".qc-about-heading"
    DESCRIPTION = ".qc-about-desc"
    CTA_ROW = ".qc-about-cta-row"
    READMORE = ".qc-about-readmore"
    ACHIEVEMENTS = ".qc-about-achievements"
    ACHIEVEMENTS_TITLE = ".qc-about-achievements-title"
    COUNTERS = ".qc-about-counters"
    COUNTER = ".qc-about-counter"
    COUNTER_ICON_IMG = ".qc-about-counter-icon img"
    COUNTER_VALUE = ".qc-about-counter-value"
    COUNTER_LABEL = ".qc-about-counter-label"
    HTML_ROOT = "html"

    _STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "color: cs.color, fontWeight: cs.fontWeight, fontSize: cs.fontSize,"
        "position: cs.position, zIndex: cs.zIndex, direction: cs.direction"
        "}; }"
    )

    def _style(self, locator: str) -> dict:
        return self.page.locator(locator).first.evaluate(self._STYLE_JS)

    def _box(self, locator: str) -> dict | None:
        box = self.page.locator(locator).bounding_box()
        if not box:
            return None
        return {"x": box["x"], "y": box["y"], "w": box["width"], "h": box["height"]}

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeAboutSummaryPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeAboutSummaryPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomeAboutSummaryPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    # ── Page-level direction ─────────────────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    # ── Section-level visibility (TC 136088) ─────────────────────────────
    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def is_collage_visible(self) -> bool:
        return self.is_visible(self.COLLAGE)

    def is_badge_visible(self) -> bool:
        return self.is_visible(self.BADGE)

    def is_tag_visible(self) -> bool:
        return self.is_visible(self.TAG)

    def is_heading_visible(self) -> bool:
        return self.is_visible(self.HEADING)

    def is_description_visible(self) -> bool:
        return self.is_visible(self.DESCRIPTION)

    def is_readmore_visible(self) -> bool:
        return self.is_visible(self.READMORE)

    def is_counters_visible(self) -> bool:
        return self.is_visible(self.COUNTERS)

    # ── Image collage (TC 136089) ────────────────────────────────────────
    def collage_image_count(self) -> int:
        return self.page.locator(self.COLLAGE_ITEM_IMG).count()

    def collage_images_loaded(self) -> bool:
        """True only if every collage <img> both finished loading AND
        rendered real pixel dimensions — the genuine "not a broken-image
        icon" signal (a broken image can still be `complete === true` with
        `naturalWidth === 0`)."""
        return self.page.locator(self.COLLAGE_ITEM_IMG).evaluate_all(
            "els => els.length > 0 && els.every(el => el.complete && el.naturalWidth > 0)"
        )

    def collage_images_overlap(self) -> bool:
        primary = self._box(self.COLLAGE_PRIMARY)
        secondary = self._box(self.COLLAGE_SECONDARY)
        if not primary or not secondary:
            return False
        return _boxes_overlap(primary, secondary)

    # ── Badge overlay (TC 136090) ────────────────────────────────────────
    def badge_num_text(self) -> str:
        return self.text(self.BADGE_NUM)

    def badge_label_text(self) -> str:
        return self.text(self.BADGE_LABEL)

    def badge_style(self) -> dict:
        return self._style(self.BADGE)

    def badge_overlaps_collage(self) -> bool:
        badge = self._box(self.BADGE)
        primary = self._box(self.COLLAGE_PRIMARY)
        if not badge or not primary:
            return False
        return _boxes_overlap(badge, primary)

    # ── Tag / heading / description (TC 136091) ──────────────────────────
    def tag_text(self) -> str:
        return self.text(self.TAG)

    def heading_text(self) -> str:
        return self.text(self.HEADING)

    def description_text(self) -> str:
        return self.text(self.DESCRIPTION)

    def media_x(self) -> float | None:
        box = self._box(self.MEDIA)
        return box["x"] if box else None

    def content_x(self) -> float | None:
        box = self._box(self.CONTENT)
        return box["x"] if box else None

    # ── Read More CTA ────────────────────────────────────────────────────
    def readmore_text(self) -> str:
        return self.text(self.READMORE)

    def readmore_href(self) -> str | None:
        return self.page.locator(self.READMORE).get_attribute("href")

    # ── Achievements sub-heading (TC 136093) ─────────────────────────────
    def achievements_title_text(self) -> str:
        return self.text(self.ACHIEVEMENTS_TITLE)

    def achievements_title_style(self) -> dict:
        return self._style(self.ACHIEVEMENTS_TITLE)

    def achievements_title_is_above_counters(self) -> bool:
        title = self._box(self.ACHIEVEMENTS_TITLE)
        counters = self._box(self.COUNTERS)
        if not title or not counters:
            return False
        return (title["y"] + title["h"]) <= counters["y"]

    # ── Counters (TC 136094) ─────────────────────────────────────────────
    def counter_count(self) -> int:
        return self.page.locator(self.COUNTER).count()

    def counter_values(self) -> list:
        return self.page.locator(self.COUNTER_VALUE).evaluate_all(
            "els => els.map(el => el.textContent.trim())"
        )

    def counter_numbers(self) -> list:
        return [_parse_counter_number(v) for v in self.counter_values()]

    def counter_labels(self) -> list:
        return self.page.locator(self.COUNTER_LABEL).evaluate_all(
            "els => els.map(el => el.textContent.trim())"
        )

    def counter_icons_loaded(self) -> bool:
        return self.page.locator(self.COUNTER_ICON_IMG).evaluate_all(
            "els => els.length > 0 && els.every(el => el.complete && el.naturalWidth > 0)"
        )

    def wait_for_counters_to_settle(self, timeout: int = 8000) -> None:
        """Explicit wait, no `sleep()`. There is no discrete DOM state or
        `data-target`/`data-count` attribute exposing the count-up's final
        value (CLI-verified — see docstring), so a fixed-state `wait_for()`
        cannot apply here. Instead, polls all 4 counters' rendered text every
        200ms and resolves as soon as two CONSECUTIVE polls read identical
        values — i.e. the count-up has genuinely stopped moving — never a
        fixed sleep for an arbitrary guessed duration. Mirrors the same
        "no discrete state to hook, observe the real signal instead"
        reasoning already used by home_strategic_direction_page.py's
        `_click_arrow_and_wait_for_change` (there: wait for a value to
        CHANGE; here: wait for a value to STOP changing)."""
        self.page.wait_for_function(
            """() => {
                const vals = Array.from(document.querySelectorAll('.qc-about-counter-value'))
                    .map(el => el.textContent.trim());
                if (vals.length === 0) return false;
                const key = '__qc_about_counter_prev';
                const prev = window[key];
                window[key] = vals;
                return !!prev && JSON.stringify(prev) === JSON.stringify(vals);
            }""",
            timeout=timeout,
            polling=200,
        )

    # ── Responsive / layout ──────────────────────────────────────────────
    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

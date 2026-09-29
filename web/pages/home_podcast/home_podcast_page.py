"""
web/pages/home_podcast/home_podcast_page.py — HomePodcastPage.

PBI 129387 / QC-HOME-011 "Qatar Chamber Podcast Section" — its own Home-page
section/module folder per active/standards.md's Home-page sections table
(MEDIA service — Podcasts are explicitly listed under the MEDIA Service/Module
code). This pass covers the 7 approved, Automation-tagged, UI-category,
Web-platform cases handed off for this PBI (ADO TC 133950-133956).
Control_Panel-tagged cases for this same PBI are out-of-scope for this run
and are NOT touched here (see the sibling home_podcast_admin_page.py
skeleton).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "podcast"

    -> [role] uniq=1  get_by_role("link", name="Qatar Chamber Podcast")

The extractor's interactive-element harvest surfaced only the section's one
uniquely-labelled link — the tag pills, meta row, player controls, and layout
containers are plain <div>/<span>/<button> elements with no distinguishing
role/label at the whole-page scope extract_locators.py resolves against (the
same documented "ambiguous/unreachable via role" condition already resolved
in home_strategic_direction_page.py and language_switcher_component.py).
Resolved the same way: one additional, disclosed, scoped Playwright script
(still CLI/shell, never the Playwright MCP) reusing BasePage's own
license-gate/overlay guard sequence, to read the live DOM structure and
computed styles directly.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home):

    section.qc-home-podcast                                  (SECTION)
      div.qc-pod-bg
        div.qc-pod-bg-image                                    (decorative image)
        div.qc-pod-bg-overlay                                  (BG_OVERLAY — gradient wash)
      div.qc-pod-inner                                          (INNER)
        div.qc-pod-media                                        (MEDIA — thumbnail block)
          a.qc-pod-thumb-link > img.qc-pod-thumb
        div.qc-pod-body                                         (BODY — text/controls block)
          div.qc-pod-head
            div.qc-pod-head-main
              div.qc-pod-tags                                    (TAGS_ROW)
                span.qc-pod-tag ("3 Episodes")                   (TAG, 2 instances)
                span.qc-pod-tag ("Weekly")
              h2.qc-pod-title > a.qc-pod-title-link               (TITLE)
            div.qc-pod-head-actions
              button.qc-pod-portable[aria-label="Open portable player"]
              a.qc-pod-explore.qc-pod-explore--top ("Explore More")  (EXPLORE_TOP)
          p.qc-pod-desc                                          (DESC)
          div.qc-pod-player                                       (PLAYER)
            div.qc-pod-controls
              button.qc-pod-ctrl.qc-pod-back[aria-label="Skip back 15 seconds"]
              button.qc-pod-ctrl.qc-pod-play[aria-label="Play"/"Pause"]
              button.qc-pod-ctrl.qc-pod-fwd[aria-label="Skip forward 15 seconds"]
            span.qc-pod-time ("0:00 / 0:00")                     (TIME)
            div.qc-pod-scrub[role=slider][aria-label="Seek"]     (SCRUB)
              div.qc-pod-scrub-buf / .qc-pod-scrub-fill / .qc-pod-scrub-knob
            div.qc-pod-vol                                       (VOL)
              button.qc-pod-mute[aria-label="Mute"]
              input.qc-pod-vol-range[aria-label="Volume"]
          p.qc-pod-error[role=alert]                             (hidden, 0x0, no error)
          div.qc-pod-meta                                        (META)
            span.qc-pod-meta-item ("Episode 3") + svg (recording icon)
            span.qc-pod-meta-dot
            span.qc-pod-meta-item ("May 10, 2026") + svg (calendar icon)
            span.qc-pod-meta-dot
            span.qc-pod-meta-item ("20 SEC") + svg (clock icon)
            span.qc-pod-meta-dot
            span.qc-pod-meta-item ("12.4K plays") + svg (headphones icon)
          a.qc-pod-explore.qc-pod-explore--bottom ("Explore More")  (EXPLORE_BOTTOM)

Every qc-pod-* class is unique in its scope (single instance per container,
confirmed live via `page.locator(sel).count()`) except `.qc-pod-tag` (2, the
two pill tags) and `.qc-pod-meta-item` (4, the four meta-row entries).

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here — a mismatch below is scripted to FAIL
HONESTLY against the case's literal stated value, per this project's Result
Integrity rule, never quietly re-targeted at the live value):

  - TC 133950 (AR/RTL mirroring): CONFIRMED LIVE (`/ar/home`) — `<html
    dir="rtl">`, section `direction: rtl`. The thumbnail block (`.qc-pod-media`)
    moves from x=376 (left half, EN) to x=1239 (right half, AR); the text/
    controls block (`.qc-pod-body`) moves from x=796 (right half, EN) to
    x=376 (left half, AR) — a full mirror. The player controls' own DOM order
    stays back->play->fwd, but their VISUAL x-order flips: EN reads
    back(x=796) < play(x=844) < fwd(x=904) left-to-right; AR reads
    fwd(x=980) < play(x=1028) < back(x=1088) left-to-right — the exact
    reverse, i.e. the control order IS visually mirrored. AR copy (title,
    description, both tag pills) renders non-empty, distinct Arabic text with
    no visible truncation/overlap. Real, genuine pass.
  - TC 133951 (dark-gradient theme persistence): CONFIRMED LIVE — the
    section's own solid background color GENUINELY CHANGES when the global
    Accessibility-panel Dark Mode toggle is switched on: `rgb(74, 13, 28)`
    (#4A0D1C, maroon) in light mode -> `rgb(29, 29, 27)` (#1D1D1B, the site's
    generic dark-neutral) after toggling. The gradient wash overlay
    (`.qc-pod-bg-overlay`, `linear-gradient(268.8deg, rgba(29,29,27,0.12)
    20%, rgba(29,29,27,0.2) 80%), ...`) is byte-identical before/after — only
    the section's OWN base color is repainted by the global toggle. Scripted
    per the case's literal expected result ("Podcast section's background is
    unchanged"), which will FAIL HONESTLY against this real, observed
    change — not a framework defect.
  - TC 133952 (meta row format): the row's STRUCTURE/styling matches the case
    exactly — 4 items, dot-separated (`.qc-pod-meta-dot`), each preceded by
    an icon in the stated order (recording -> calendar -> clock ->
    headphones), all rendered Cairo Regular (font-weight 400) 14px/22px
    white (`rgb(255, 255, 255)`) — confirmed live via computed style. The
    CONTENT values partially mismatch the case's literal string: live reads
    "Episode 3" (not "Episode 24") and "20 SEC" (not "42 MIN"); "May 10,
    2026" and "12.4K plays" match exactly. Scripted against the case's full
    literal string; will genuinely fail on the two mismatched tokens only.
  - TC 133953 (tag pills styling): style tokens match EXACTLY — Cairo Regular
    14px/22px white text, pill background `rgba(29, 29, 27, 0.4)`, 6px
    border-radius, on BOTH pills. Content: "Weekly" matches exactly; live
    reads "3 Episodes" (not "52 Episodes" — a genuine content mismatch,
    styling unaffected).
  - TC 133954 (Explore More button): CONFIRMED LIVE, full match — pill-shaped
    (`border-radius: 9999px`), white fill (`rgb(255, 255, 255)`), a real 1px
    border (`1px solid rgb(222, 222, 221)`), text "Explore More" exactly,
    Cairo SemiBold (font-weight 600) 16px/24px, color `rgb(74, 74, 73)`
    (#4A4A49) exactly, padding `10px 16px` exactly, and an arrow `<svg>` icon
    child. No mismatch found.
  - TC 133955 (player control icons, idle state): skip-back/skip-forward
    buttons measure 36x36px exactly; the Play button is circular
    (`border-radius: 9999px`), maroon `rgb(145, 23, 49)` (#911731) exactly,
    with a real `box-shadow` glow; the progress bar (`.qc-pod-scrub`) is 8px
    tall with a light-grey track `rgb(237, 237, 237)` (#EDEDED) exactly; the
    time text is Cairo Medium (font-weight 500) 14px/22px white exactly; the
    Mute button (`aria-label="Mute"`, i.e. currently unmuted — showing a
    volume-max-style icon) is present and visible. ONE genuine mismatch:
    in its true IDLE state (before any play interaction) the underlying
    `<audio>` has not preloaded metadata (`readyState: 0`, `duration: NaN`),
    so the time text reads "0:00 / 0:00", not a real duration, at rest —
    the case's literal "0:00 / 0:35 (or actual duration)" implies the total
    duration is already known/shown at idle. Confirmed live that the REAL
    duration is ~20s (`0:00 / 0:20`) and only appears once playback starts
    (`.qc-pod-play` click -> `aria-label` flips to "Pause"). Scripted against
    the idle-state text per the case's literal wording; will genuinely fail
    on this one point.
  - TC 133956 (mobile touch-friendly layout, 375px): CONFIRMED LIVE — skip
    buttons grow from 36x36px (desktop) to 44x44px (mobile); the Play button
    grows from 48x48px to 64x64px; none of Back/Play/Forward overlap at
    375px. ONE genuine mismatch: the volume control (`.qc-pod-vol`, housing
    the Mute button + range slider) is not merely smaller — it is
    `display: none` at 375px, i.e. it does not render at all, so there is no
    "larger tap target" to observe for it. Scripted against the case's
    literal "volume controls have visibly larger tap targets ... than
    desktop"; will genuinely fail on the volume control only.
"""

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent


class HomePodcastPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    HTML_ROOT = "html"
    SECTION = ".qc-home-podcast"
    BG_OVERLAY = ".qc-pod-bg-overlay"
    INNER = ".qc-pod-inner"
    MEDIA = ".qc-pod-media"
    THUMB_LINK = ".qc-pod-thumb-link"
    BODY = ".qc-pod-body"
    TAGS_ROW = ".qc-pod-tags"
    TAG = ".qc-pod-tag"
    TITLE = ".qc-pod-title"
    TITLE_LINK = ".qc-pod-title-link"
    EXPLORE_TOP = ".qc-pod-explore--top"
    EXPLORE_BOTTOM = ".qc-pod-explore--bottom"
    PORTABLE_BUTTON = ".qc-pod-portable"
    DESC = ".qc-pod-desc"
    PLAYER = ".qc-pod-player"
    CONTROLS = ".qc-pod-controls"
    BACK_BUTTON = ".qc-pod-back"
    PLAY_BUTTON = ".qc-pod-play"
    FWD_BUTTON = ".qc-pod-fwd"
    TIME = ".qc-pod-time"
    SCRUB = ".qc-pod-scrub"
    SCRUB_FILL = ".qc-pod-scrub-fill"
    VOL = ".qc-pod-vol"
    MUTE_BUTTON = ".qc-pod-mute"
    VOL_RANGE = ".qc-pod-vol-range"
    META = ".qc-pod-meta"
    META_ITEM = ".qc-pod-meta-item"
    META_TEXT = ".qc-pod-meta-text"
    META_DOT = ".qc-pod-meta-dot"

    _STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "color: cs.color, backgroundColor: cs.backgroundColor, backgroundImage: cs.backgroundImage,"
        "border: cs.border, borderRadius: cs.borderRadius, boxShadow: cs.boxShadow,"
        "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize,"
        "lineHeight: cs.lineHeight, padding: cs.padding, textAlign: cs.textAlign,"
        "direction: cs.direction, display: cs.display"
        "}; }"
    )

    def __init__(self, page):
        super().__init__(page)
        self.a11y = AccessibilityToolsComponent(page)

    def _style(self, locator) -> dict:
        loc = locator if hasattr(locator, "evaluate") else self.page.locator(locator).first
        return loc.evaluate(self._STYLE_JS)

    def _box(self, locator) -> dict:
        loc = locator if hasattr(locator, "bounding_box") else self.page.locator(locator).first
        box = loc.bounding_box()
        return {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]} if box else None

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomePodcastPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomePodcastPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomePodcastPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    # ── Section-level state ──────────────────────────────────────────────
    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    def section_background_color(self) -> str:
        return self._style(self.SECTION)["backgroundColor"]

    def section_overlay_gradient(self) -> str:
        return self._style(self.BG_OVERLAY)["backgroundImage"]

    # ── Global dark-mode toggle (composes AccessibilityToolsComponent) ───
    def enable_dark_mode(self) -> "HomePodcastPage":
        self.a11y.click_accessibility_button()
        self.a11y.switch_to_dark_mode()
        return self

    # ── Tag pills (TC 133953) ────────────────────────────────────────────
    def tag_texts(self) -> list:
        return self.page.locator(self.TAG).all_inner_texts()

    def tag_style(self, index: int = 0) -> dict:
        return self._style(self.page.locator(self.TAG).nth(index))

    # ── Explore More button (TC 133954) ──────────────────────────────────
    def explore_button_text(self, position: str = "top") -> str:
        loc = self.EXPLORE_TOP if position == "top" else self.EXPLORE_BOTTOM
        return self.text(loc)

    def explore_button_style(self, position: str = "top") -> dict:
        loc = self.EXPLORE_TOP if position == "top" else self.EXPLORE_BOTTOM
        return self._style(loc)

    def is_explore_button_visible(self, position: str = "top") -> bool:
        loc = self.EXPLORE_TOP if position == "top" else self.EXPLORE_BOTTOM
        return self.is_visible(loc)

    def has_explore_button_arrow_icon(self, position: str = "top") -> bool:
        loc = self.EXPLORE_TOP if position == "top" else self.EXPLORE_BOTTOM
        return self.page.locator(loc).locator("svg").count() > 0

    # ── Meta row (TC 133952) ─────────────────────────────────────────────
    def meta_item_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.META_ITEM).all_inner_texts()]

    def meta_full_text(self) -> str:
        return " • ".join(self.meta_item_texts())

    def meta_dot_count(self) -> int:
        return self.page.locator(self.META_DOT).count()

    def meta_item_style(self, index: int = 0) -> dict:
        return self._style(self.page.locator(self.META_ITEM).nth(index).locator(self.META_TEXT))

    def meta_item_icon_tag(self, index: int = 0) -> str:
        """First child element's tag name inside a meta item — used to
        confirm an icon (an <svg>) precedes each item's text, per its
        DOM order (recording/calendar/clock/headphones — see docstring)."""
        return self.page.locator(self.META_ITEM).nth(index).locator("svg").first.evaluate("el => el.tagName.toLowerCase()")

    # ── Player controls (TC 133955) ──────────────────────────────────────
    def skip_button_box(self, which: str = "back") -> dict:
        loc = self.BACK_BUTTON if which == "back" else self.FWD_BUTTON
        return self._box(loc)

    def skip_button_aria_label(self, which: str = "back") -> str:
        loc = self.BACK_BUTTON if which == "back" else self.FWD_BUTTON
        return self.page.locator(loc).get_attribute("aria-label")

    def play_button_style(self) -> dict:
        return self._style(self.PLAY_BUTTON)

    def play_button_box(self) -> dict:
        return self._box(self.PLAY_BUTTON)

    def play_button_aria_label(self) -> str:
        return self.page.locator(self.PLAY_BUTTON).get_attribute("aria-label")

    def click_play(self) -> "HomePodcastPage":
        self.click(self.PLAY_BUTTON)
        return self

    def is_play_button_circular(self) -> bool:
        """True for a pill/circle radius token (`50%` or Liferay's common
        `9999px` "fully-rounded" convention — confirmed live on this Play
        button, see docstring)."""
        br = self.play_button_style()["borderRadius"].strip()
        return br.endswith("%") or br == "9999px"

    def scrub_style(self) -> dict:
        return self._style(self.SCRUB)

    def scrub_box(self) -> dict:
        return self._box(self.SCRUB)

    def time_text(self) -> str:
        return self.text(self.TIME)

    def time_style(self) -> dict:
        return self._style(self.TIME)

    def is_mute_button_visible(self) -> bool:
        return self.is_visible(self.MUTE_BUTTON)

    def mute_button_aria_label(self) -> str:
        return self.page.locator(self.MUTE_BUTTON).get_attribute("aria-label")

    def is_volume_control_visible(self) -> bool:
        return self.is_visible(self.VOL)

    def volume_control_box(self) -> dict:
        return self._box(self.VOL)

    def audio_duration_seconds(self) -> float:
        """Reads the underlying <audio> element's real, decoded duration
        (NaN until metadata has loaded — see docstring's TC 133955 finding)."""
        return self.page.evaluate(
            "() => { const a = document.querySelector('audio'); "
            "return a ? a.duration : NaN; }"
        )

    # ── RTL mirroring (TC 133950) ────────────────────────────────────────
    def media_box(self) -> dict:
        return self._box(self.MEDIA)

    def body_box(self) -> dict:
        return self._box(self.BODY)

    def title_text(self) -> str:
        return self.text(self.TITLE)

    def title_style(self) -> dict:
        return self._style(self.TITLE)

    def description_text(self) -> str:
        return self.text(self.DESC)

    def description_style(self) -> dict:
        return self._style(self.DESC)

    def controls_visual_order(self) -> list:
        """['back', 'play', 'fwd'] (or the reverse) ranked by ascending
        on-screen x-position -- the LTR/RTL-agnostic signal used to confirm
        the control order is visually mirrored under RTL (see docstring)."""
        boxes = {
            "back": self.skip_button_box("back"),
            "play": self.play_button_box(),
            "fwd": self.skip_button_box("fwd"),
        }
        return [name for name, _ in sorted(boxes.items(), key=lambda kv: kv[1]["x"])]

    # ── Responsive / layout (TC 133956) ──────────────────────────────────
    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    @staticmethod
    def _boxes_overlap(a: dict, b: dict) -> bool:
        if not a or not b:
            return False
        return not (
            a["x"] + a["width"] <= b["x"]
            or b["x"] + b["width"] <= a["x"]
            or a["y"] + a["height"] <= b["y"]
            or b["y"] + b["height"] <= a["y"]
        )

    def player_controls_overlap(self) -> bool:
        back, play, fwd = self.skip_button_box("back"), self.play_button_box(), self.skip_button_box("fwd")
        return (
            self._boxes_overlap(back, play)
            or self._boxes_overlap(play, fwd)
            or self._boxes_overlap(back, fwd)
        )

"""
web/pages/home_hero_banner/home_hero_banner_page.py — HomeHeroBannerPage.

Public-frontend Page Object for the Home Page's Hero Banner carousel and its
embedded Achievement Counters row (PBI 129367) — see
cms/pages/home_hero_banner/home_hero_banner_admin_page.py for the
Control_Panel counterpart that authors these records, including the full
live-confirmed Object Definition / field mapping this class's selectors are
derived from.

CONFIRMED LIVE (2026-09-08, qcdev /web/qatar-chamber/home — via
browser_evaluate DOM inspection, disclosed Playwright-MCP fallback: this is
a client-hydrated carousel component with no `data-testid` layer, and the
stateless CLI extractor would need the exact same live browser context to
reach the hydrated DOM anyway):

  - `section.qc-home-hero-banner[data-show-counters]` — the hero section
    root; `data-show-counters` mirrors the currently-active slide's own
    "Counters Active Status" field.
  - `.qc-hero-viewport` renders exactly ONE slide's textual overlay
    (`.qc-hero-title`, counters, buttons) at a time — NOT all slides
    simultaneously (confirmed live: exactly one `.qc-hero-title` node
    exists in the DOM at any moment). A separate `ul.qc-hero-slides`
    (`aria-hidden`) holds the background-image layers only and is not a
    reliable source for slide TEXT content.
  - The overlay swaps synchronously (no extra network round trip observed)
    when clicking "Next slide" / "Go to slide N" — confirmed live by
    cycling 5 clicks and reading `.qc-hero-title` after each. A short
    settle (SLIDE_TRANSITION_SETTLE_MS) is kept after each click as a
    real-condition CSS-transition grace, not a wait for content that isn't
    there yet.
  - A fresh, un-clicked page load consistently shows the Display-Order-100
    slide (HERO_BANNER_SLIDE-01) as the initially active one — confirmed
    live twice. Every counter-row read in this class relies on that slide
    staying untouched (its own "Counters Active Status" must remain true —
    see the admin module's docstring).
  - Achievement Counters row: `.qc-hero-counters[data-qc-hero-counters]` >
    `.qc-hero-counter` > `.qc-hero-counter-label` / `.qc-hero-counter-value`
    — confirmed live 1:1 against the "Achievement Counter" object entries
    (each counter's own `<img>` src embeds its
    `objectEntryExternalReferenceCode`). Currently 4 counters render, in
    Display-Order sequence: "Active Members" / "Countries Served" /
    "Service Support" / "statistics".
  - Propagation: this Home Page section follows the same Object-Authoring
    publish-then-render pattern as every other Object Definition on this
    project. cms-profile.md's only DIRECTLY measured budget is the Board
    Members JAX-RS endpoint (~0s, 5s timeout / 0.5s interval poll used
    project-wide as the safety-margin default pending a per-endpoint
    re-measure) — that same poll budget is reused here as the best
    available reference, not an independently re-measured figure for this
    specific endpoint (disclosed per cms-profile.md's own caveat).

CONFIRMED LIVE (2026-09-08, qcdev /web/qatar-chamber/home — tc_135014/135015
investigation):

  - The carousel AUTOPLAYS: `section.qc-home-hero-banner[data-autoplay-
    interval="6000"]` — the initially-active slide silently advances after
    ~6s with no further user interaction. active_slide_entry_code() below
    MUST be read immediately after a fresh open_home() (no intervening
    wait) to reliably observe the true initial slide, which is exactly
    what reload_until_active_slide_matches() does on every poll iteration.
  - `ul.qc-hero-slides > li.qc-hero-slide` (aria-hidden layer, background-
    image only — see the rest of this docstring) carries `aria-hidden` per
    slide and the CURRENTLY active one additionally carries the
    `qc-hero-slide-active` class. Each `<li>`'s own `<img>` `src` embeds
    `objectEntryExternalReferenceCode=<code>` (confirmed live, same
    embedding convention as the Achievement Counters row's own `<img>`
    src — see admin module docstring). Reading this code directly is a
    reliable, title-independent way to identify which of -01/-02 is
    active — unlike `.qc-hero-title` text, which is IDENTICAL between
    -01/-02 by default (see admin module docstring) and therefore cannot
    distinguish them without a temporary fingerprint edit (the technique
    tc_135024's test already uses for a different purpose). This ERC-based
    read needs no such fingerprint.
"""

import re
import time

from core.web.base_page import BasePage
from config.settings import web_url

HERO_SECTION = "section.qc-home-hero-banner"
HERO_TITLE = ".qc-hero-title"
NEXT_SLIDE_BUTTON = 'button[aria-label="Next slide"]'
COUNTERS_WRAPPER = ".qc-hero-counters"
COUNTER_BLOCK = ".qc-hero-counter"
COUNTER_LABEL = ".qc-hero-counter-label"
COUNTER_VALUE = ".qc-hero-counter-value"
ACTIVE_SLIDE_IMG = "li.qc-hero-slide-active img.qc-hero-slide-img"
ENTRY_CODE_PATTERN = re.compile(r"objectEntryExternalReferenceCode=([^&]+)")

# RE-READ LIVE 2026-10-18 (logged-out, EN/AR/375 px; reports in
# .claude/qa-runs/phase3-20261015/hero_dom_1018.json). The overlay is now ONE
# PANEL PER SLIDE, filled client-side by main.js after DOMContentLoaded and
# stacked in one grid cell; only `.qc-hero-panel-active` is shown. Read the
# active slide through it (or the dot with aria-current="true"), never through
# the first `.qc-hero-title` in the DOM. Slides -01 and -02 share their title.
PREV_SLIDE_BUTTON = 'button[aria-label="Previous slide"]'
ARROW_NEXT = ".qc-hero-arrow-next"
ARROW_PREV = ".qc-hero-arrow-prev"
DOT = ".qc-hero-dot"
ACTIVE_DOT = '.qc-hero-dot[aria-current="true"]'
ACTIVE_PANEL = ".qc-hero-panel.qc-hero-panel-active"
ACTIVE_TITLE = f"{ACTIVE_PANEL} .qc-hero-title"
ACTIVE_SUBTITLE = f"{ACTIVE_PANEL} .qc-hero-subtitle"
ACTIVE_CTA_PRIMARY = f"{ACTIVE_PANEL} .qc-hero-btn-primary"
ACTIVE_CTA_SECONDARY = f"{ACTIVE_PANEL} a.qc-hero-btn:not(.qc-hero-btn-primary)"
ACTIVE_SLIDE_LAYER = "li.qc-hero-slide-active"
SCRIM = "li.qc-hero-slide-active .qc-hero-slide-scrim"
PANEL_TITLE = ".qc-hero-panel .qc-hero-title"

_BOX_JS = """e => { const b = e.getBoundingClientRect(); const c = getComputedStyle(e);
  return {x: b.x, y: b.y, w: b.width, h: b.height, right: b.right, bottom: b.bottom,
          color: c.color, bg: c.backgroundColor, bgImage: c.backgroundImage, fw: parseInt(c.fontWeight),
          fs: parseFloat(c.fontSize), lh: parseFloat(c.lineHeight) || parseFloat(c.fontSize) * 1.2,
          ta: c.textAlign, dir: c.direction, radius: c.borderTopLeftRadius, opacity: c.opacity,
          visibility: c.visibility, display: c.display, text: (e.innerText || '').trim()}; }"""

# Confirmed-live: the overlay swap on a Next-slide click is synchronous (no
# extra network fetch observed), but still needs one CSS-transition frame to
# settle before the new `.qc-hero-title` text is stable to read.
SLIDE_TRANSITION_SETTLE_MS = 400

# See module docstring's Propagation note.
PROPAGATION_POLL_TIMEOUT_MS = 5000
PROPAGATION_POLL_INTERVAL_MS = 500


class HomeHeroBannerPage(BasePage):
    def open_home(self) -> "HomeHeroBannerPage":
        self.open(web_url("/home"))
        self.wait_for(HERO_TITLE, timeout=15000)
        return self

    # ---- 2026-10-18 panel model (see the RE-READ note above) ----------------
    def open_home_locale(self, locale: str = "en") -> "HomeHeroBannerPage":
        """Fresh load of /<locale>/home; waits for main.js to mount the active
        panel (the hero is client-rendered after DOMContentLoaded)."""
        self.page.goto(web_url(f"/home?_={int(time.time())}", locale=locale), wait_until="domcontentloaded")
        self.page.locator(ACTIVE_TITLE).first.wait_for(state="visible", timeout=30000)
        return self

    def box(self, selector: str) -> dict:
        return self.page.locator(selector).first.evaluate(_BOX_JS)

    def boxes(self, selector: str) -> list:
        return self.page.locator(selector).evaluate_all(f"els => els.map({_BOX_JS})")

    def pseudo(self, selector: str, which: str = "::after") -> dict:
        return self.page.locator(selector).first.evaluate(
            "(e, w) => { const c = getComputedStyle(e, w); return {content: c.content, bgImage: c.backgroundImage,"
            " maskImage: c.maskImage || c.webkitMaskImage, width: c.width, animation: c.animationName,"
            " transition: c.transitionDuration}; }", which)

    def has_inline_icon(self, selector: str) -> bool:
        return self.page.locator(selector).first.evaluate("e => !!e.querySelector('svg, img, i, [class*=icon]')")

    def header_bottom(self) -> float:
        return self.page.evaluate("() => { const h = document.querySelector('header'); "
                                  "return h ? h.getBoundingClientRect().bottom : 0 }")

    def header_logo_box(self) -> dict:
        return self.box("header img, header [class*=logo]")

    def viewport_width(self) -> int:
        return self.page.evaluate("() => window.innerWidth")

    def has_horizontal_scroll(self) -> bool:
        return self.page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1")

    def slide_count(self) -> int:
        return self.page.locator(DOT).count()

    def active_index(self) -> int:
        """1-based index of the active slide, from the aria-current dot."""
        label = self.page.locator(ACTIVE_DOT).first.get_attribute("aria-label") or ""
        m = re.search(r"(\d+)", label)
        return int(m.group(1)) if m else 0

    def active_title(self) -> str:
        return self.page.locator(ACTIVE_TITLE).first.inner_text().strip()

    def click_prev_slide(self) -> "HomeHeroBannerPage":
        self.click(PREV_SLIDE_BUTTON)
        self.page.wait_for_timeout(SLIDE_TRANSITION_SETTLE_MS)
        return self

    def autoplay_interval_ms(self) -> int:
        return int(self.page.locator(HERO_SECTION).first.get_attribute("data-autoplay-interval") or 0)

    def active_image_loaded(self) -> bool:
        return self.page.locator(f"{ACTIVE_SLIDE_LAYER} img").first.evaluate(
            "i => i.complete && i.naturalWidth > 0")

    def counter_values(self) -> list:
        return [v.strip() for v in self.page.locator(f"{ACTIVE_PANEL} {COUNTER_VALUE}").all_inner_texts()]

    def counter_boxes(self) -> list:
        return self.boxes(f"{ACTIVE_PANEL} {COUNTER_BLOCK}")

    def counter_icon_boxes(self) -> list:
        return self.page.locator(f"{ACTIVE_PANEL} {COUNTER_BLOCK}").evaluate_all(
            "els => els.map(c => { const i = c.querySelector('img'); const v = c.querySelector('.qc-hero-counter-value');"
            " if (!i) return null; const a = i.getBoundingClientRect(), b = v.getBoundingClientRect();"
            " return {icon_bottom: a.bottom, value_top: b.top, loaded: i.complete && i.naturalWidth > 0}; })")

    # ---- Slide carousel ---------------------------------------------------
    def current_slide_title(self) -> str:
        return self.text(HERO_TITLE).strip()

    def click_next_slide(self) -> "HomeHeroBannerPage":
        self.click(NEXT_SLIDE_BUTTON)
        self.page.wait_for_timeout(SLIDE_TRANSITION_SETTLE_MS)
        return self

    def is_title_in_carousel(self, title: str, max_cycles: int = 8) -> bool:
        """Cycles "Next slide" up to `max_cycles` times (bounded — this
        carousel currently renders 4-6 slides total), reading
        `.qc-hero-title` after each, since only the active slide's title
        exists in the DOM at any moment (see module docstring). Stops
        early once a title repeats (cycled back to the start) so a slide
        that genuinely isn't live doesn't cost the full budget."""
        seen_first = None
        for _ in range(max_cycles):
            current = self.current_slide_title()
            if current == title:
                return True
            if seen_first is None:
                seen_first = current
            elif current == seen_first:
                break
            self.click_next_slide()
        return False

    def active_slide_entry_code(self) -> str:
        """The currently-active slide's own objectEntryExternalReferenceCode,
        read straight off the DOM (see module docstring) — title-independent,
        unlike current_slide_title()/is_title_in_carousel() which cannot
        distinguish -01/-02 (identical default titles)."""
        src = self.page.locator(ACTIVE_SLIDE_IMG).first.get_attribute("src") or ""
        match = ENTRY_CODE_PATTERN.search(src)
        return match.group(1) if match else ""

    def reload_until_active_slide_matches(
        self,
        entry_code: str,
        timeout_ms: int = PROPAGATION_POLL_TIMEOUT_MS,
        interval_ms: int = PROPAGATION_POLL_INTERVAL_MS,
    ) -> bool:
        """Poll (reload + immediate read), never a bare sleep — see module
        docstring's autoplay note: each iteration re-opens the Home Page and
        reads active_slide_entry_code() with NO intervening wait, so the
        6s-autoplay window never has a chance to advance past the true
        initial slide before the read happens."""
        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home()
            if self.active_slide_entry_code() == entry_code:
                return True
            if time.monotonic() >= deadline:
                return self.active_slide_entry_code() == entry_code
            self.page.wait_for_timeout(interval_ms)

    def reload_until_title_in_carousel(
        self,
        title: str,
        expected_visible: bool,
        timeout_ms: int = PROPAGATION_POLL_TIMEOUT_MS,
        interval_ms: int = PROPAGATION_POLL_INTERVAL_MS,
    ) -> bool:
        """Poll (reload + cycle-check), never a bare sleep — see module
        docstring's Propagation note, mirrors home_community_partners_page.py's
        reload_until_logo_matches() precedent for this same class of
        publish-then-verify check."""
        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home()
            if self.is_title_in_carousel(title) == expected_visible:
                return True
            if time.monotonic() >= deadline:
                return self.is_title_in_carousel(title) == expected_visible
            self.page.wait_for_timeout(interval_ms)

    # ---- Achievement Counters row (default/first slide only — see docstring) --
    def counter_labels(self) -> list:
        self.wait_for(COUNTERS_WRAPPER, timeout=8000)
        return [label.strip() for label in self.page.locator(COUNTER_LABEL).all_inner_texts()]

    def counter_value_for_label(self, label: str) -> str:
        block = self.page.locator(COUNTER_BLOCK).filter(has_text=label)
        return block.locator(COUNTER_VALUE).first.inner_text().strip()

    def is_counter_visible(self, label: str) -> bool:
        return label in self.counter_labels()

    def reload_until_counter_matches(
        self,
        label: str,
        expected_visible: bool,
        timeout_ms: int = PROPAGATION_POLL_TIMEOUT_MS,
        interval_ms: int = PROPAGATION_POLL_INTERVAL_MS,
    ) -> bool:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home()
            if self.is_counter_visible(label) == expected_visible:
                return True
            if time.monotonic() >= deadline:
                return self.is_counter_visible(label) == expected_visible
            self.page.wait_for_timeout(interval_ms)

    def reload_until_counter_position_matches(
        self,
        label: str,
        expected_index: int,
        timeout_ms: int = PROPAGATION_POLL_TIMEOUT_MS,
        interval_ms: int = PROPAGATION_POLL_INTERVAL_MS,
    ) -> bool:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home()
            labels = self.counter_labels()
            current_index = labels.index(label) if label in labels else -1
            if current_index == expected_index:
                return True
            if time.monotonic() >= deadline:
                return current_index == expected_index
            self.page.wait_for_timeout(interval_ms)

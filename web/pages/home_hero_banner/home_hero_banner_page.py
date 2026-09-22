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

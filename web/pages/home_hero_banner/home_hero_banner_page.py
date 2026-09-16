"""
web/pages/home_hero_banner/home_hero_banner_page.py -- HomeHeroBannerPage.

Public (visitor-facing) Home Page hero slider, PBI 129367 (QC-HOME-001).
Backing object is **HeroBannerSlide** (`manage-hero-banner-slide`), one
entry per slide -- see cms/Content-Admin-Guide.docx section 5 and
HomeHeroBannerAdminPage. Counters shown on a slide come from a separate
`AchievementCounter` object and are out of scope for this class.

CONFIRMED LIVE 2026-09-09 (anonymous Chromium against qcdev /home, scoped
CLI probe -- never the Playwright MCP). DOM shape:

    div.qc-hero-slides
      div.qc-hero-slide[.qc-hero-slide-active][aria-hidden]   one per slide
        div.qc-hero-slide-img / .qc-hero-slide-scrim
    div.qc-hero-panels
      div.qc-hero-panel[.qc-hero-panel-active]                one per slide
        .qc-hero-title
        .qc-hero-subtitle
        .qc-hero-cta-row > a.qc-hero-btn.qc-hero-btn-primary|-secondary

Live at the time of writing: 3 CMS slide entries (all Approved + Active)
and exactly 3 `.qc-hero-slide` / `.qc-hero-panel` nodes rendered, so slide
COUNT and slide TITLES are both reliable signals for "is this slide in the
slider".

**Read titles with `textContent`, not `inner_text()`.** Only the active
panel is visible; the inactive panels are in the DOM but not rendered, so
`inner_text()` returns "" for them and a visibility-based check would
report a slide missing when it is merely not the current one. Every
title/subtitle reader below therefore uses `textContent`.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeHeroBannerPage(BasePage):
    """Public Home Page hero slider."""

    SLIDES_CONTAINER = ".qc-hero-slides"
    SLIDE = ".qc-hero-slide"
    SLIDE_ACTIVE = ".qc-hero-slide-active"
    PANELS_CONTAINER = ".qc-hero-panels"
    PANEL = ".qc-hero-panel"
    TITLE = ".qc-hero-title"
    SUBTITLE = ".qc-hero-subtitle"
    PRIMARY_BTN = ".qc-hero-btn-primary"
    SECONDARY_BTN = ".qc-hero-btn-secondary"

    def open_home(self, locale: str = "en") -> "HomeHeroBannerPage":
        self.open(web_url("/home") if locale == "en" else web_url("/home", locale="ar"))
        return self

    # ---- Slider state ---------------------------------------------------
    def is_slider_visible(self) -> bool:
        return self.is_visible(self.SLIDES_CONTAINER)

    def slide_count(self) -> int:
        return self.page.locator(self.SLIDE).count()

    def panel_count(self) -> int:
        return self.page.locator(self.PANEL).count()

    def slide_titles(self) -> list:
        """All slide titles, INCLUDING non-active panels -- see the module
        docstring on why this uses textContent rather than inner_text()."""
        return self.page.eval_on_selector_all(
            self.TITLE, "els => els.map(e => (e.textContent || '').trim())"
        )

    def slide_subtitles(self) -> list:
        return self.page.eval_on_selector_all(
            self.SUBTITLE, "els => els.map(e => (e.textContent || '').trim())"
        )

    def has_slide_with_title(self, title: str) -> bool:
        """True when any slide in the slider carries `title` (exact match on
        the trimmed textContent)."""
        return any(t == title.strip() for t in self.slide_titles())

    def has_slide_containing(self, needle: str) -> bool:
        """Substring variant -- useful when the CMS value carries trailing
        whitespace or the rendered copy is truncated."""
        return any(needle.strip() in t for t in self.slide_titles())

    def active_slide_title(self) -> str:
        loc = self.page.locator(f"{self.PANEL}.qc-hero-panel-active {self.TITLE}")
        if loc.count() == 0:
            return ""
        return (loc.first.text_content() or "").strip()

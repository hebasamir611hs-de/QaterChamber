"""
web/pages/home_about_summary/home_about_summary_page.py —
HomeAboutSummaryPage.

Public-frontend counterpart to home_about_summary_admin_page.py, for PBI
129389's Home Page "About Us" summary widget (Section + Last Year
Achievements Counters).

CONFIRMED LIVE 2026-09-07 (headless Chromium, 1920x1080, real qcdev Home
Page HTML, un-authenticated context):

  - The section is SERVER-RENDERED: the Section Heading, Tag, Description,
    Years-of-Experience badge, Read More CTA, and every Counter's
    value/label are all present in the initial HTML response for the
    public Home Page — confirmed by reading `body.inner_html()` right
    after `page.goto()` with only a short settle wait, no client-side
    fetch/poll needed. Per cms-profile.md's scope note (written for the
    JAX-RS-backed Board of Directors pages), this does NOT generalize
    automatically to every content type — this section's own render path
    was independently confirmed server-side this session.
  - Confirmed live selector inventory (exact classes from a real DOM dump):
      .qc-about-tag              — eyebrow, confirmed text "MORE ABOUT US"
      .qc-about-heading (h2)     — confirmed text "Qatar Chamber"
      .qc-about-desc             — description rich-text block
      .qc-about-badge-num        — years-of-experience number (e.g. "62+")
      .qc-about-badge-label      — badge label ("Years of Experience")
      .qc-about-readmore         — Read More CTA link
      .qc-about-achievements-title (h3) — "Last Year Achievements"
      .qc-about-counter          — one per counter
      .qc-about-counter-value    — e.g. "0 +"
      .qc-about-counter-label    — e.g. "E-Services"
  - Each counter's icon `<img>` src embeds
    `objectEntryExternalReferenceCode=QCDEMO-129389-ABOUT_US_COUNTER-0N`,
    confirming this public section is driven directly by the same Object
    Authoring entries documented in home_about_summary_admin_page.py — not
    a separate/duplicated content source.
  - No dedicated "cache refresh" UI action was found or needed to observe a
    change (same disclosed finding already documented for
    home_strategic_direction_page.py) — reload_until_heading_matches()
    performs a plain page reload as its poll mechanism, per
    cms-profile.md's Publish/Propagation Latency Budget guidance.

EXTENDED 2026-09-15 for the 50-case ADO 136088-136140 batch (PBI 129389),
CONFIRMED LIVE against this same public, unauthenticated qcdev Home Page
(headless Chromium, real goto(), no auth/session needed — unlike the
Control_Panel admin surface's probe, which failed three times this same
session; see home_about_summary_admin_page.py's module docstring for that
disclosed failure). Real DOM/computed-style findings from this pass:
  - Full section markup: `section.qc-home-about-us[data-show-achievements]`
    wraps `.qc-about-inner` (`.qc-about-media` + `.qc-about-content`) and a
    separate sibling `.qc-about-achievements` block.
  - Image collage: `.qc-about-collage[data-qc-about-collage][data-count]`
    contains exactly 2 `figure.qc-about-collage-item` elements
    (`.qc-about-collage-primary` / `.qc-about-collage-secondary`), each one
    `<img>`. Both images' `naturalWidth`/`naturalHeight` are non-zero
    (confirmed 1280x720 and 1920x1776 live) — no broken-image icons.
  - Badge overlay: `.qc-about-badge[data-qc-about-badge]` wraps
    `.qc-about-badge-num` (confirmed live text "62+") and
    `.qc-about-badge-label` ("Years of Experience") — sits inside
    `.qc-about-media`, alongside (overlaying) the collage.
  - Read More CTA: `.qc-about-cta-row[data-qc-about-cta] > a.qc-about-readmore`
    — confirmed live `href` currently resolves to
    "https://www.qatarchamber.com/about-qatar-chamber/" (the PRODUCTION
    site, not this qcdev instance's own `/web/qatar-chamber/about-us`
    page) — whatever the Section's live Read More URL field holds at
    request time, read via `read_more_href()`, never hard-assumed.
  - Achievements/counters: `.qc-about-achievements` wraps
    `.qc-about-achievements-title` (h3, confirmed live "Last Year
    Achievements") and `.qc-about-counters[data-qc-about-counters]`, which
    holds one `.qc-about-counter` per counter — each with
    `.qc-about-counter-icon > img`, `.qc-about-counter-value`,
    `.qc-about-counter-label`.
  - RTL mirroring (EN vs AR, both desktop 1920x1080, confirmed live):
    `<html dir="ltr">` on EN, `<html dir="rtl">` on AR. `.qc-about-media`
    sits at x=300 (left) / `.qc-about-content` at x=992 (right) under LTR;
    under RTL the two SWAP — media x=992 (right), content x=300 (left) — a
    real, full mirror, not merely a text-direction flip.
  - Responsive (confirmed live, real `document.documentElement`
    scrollWidth vs clientWidth): mobile (375x812) scrollWidth=379 vs
    clientWidth=375 (4px delta — normal scrollbar-gutter rounding, not a
    horizontal-scroll defect); tablet (768x1024) scrollWidth=772 vs
    clientWidth=768 (same 4px delta). `is_no_horizontal_overflow()` below
    treats anything <=10px as "no real overflow" per this confirmed-live
    baseline. Mobile Read More CTA bounding box confirmed live
    {x:20, y:670, width:335, height:50} — comfortably tappable, not
    truncated.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeAboutSummaryPage(BasePage):
    HTML_ROOT = "html"
    SECTION = "section.qc-home-about-us"
    SECTION_MEDIA = ".qc-about-media"
    SECTION_CONTENT = ".qc-about-content"
    SECTION_TAG = ".qc-about-tag"
    SECTION_HEADING = ".qc-about-heading"
    SECTION_DESC = ".qc-about-desc"
    COLLAGE = ".qc-about-collage"
    COLLAGE_ITEMS = ".qc-about-collage-item"
    COLLAGE_ITEM_IMAGES = ".qc-about-collage-item img"
    COLLAGE_PRIMARY_IMAGE = ".qc-about-collage-primary img"
    COLLAGE_SECONDARY_IMAGE = ".qc-about-collage-secondary img"
    BADGE = ".qc-about-badge"
    BADGE_NUM = ".qc-about-badge-num"
    BADGE_LABEL = ".qc-about-badge-label"
    READ_MORE_LINK = ".qc-about-readmore"
    ACHIEVEMENTS = ".qc-about-achievements"
    ACHIEVEMENTS_TITLE = ".qc-about-achievements-title"
    COUNTERS_CONTAINER = ".qc-about-counters"
    COUNTER = ".qc-about-counter"
    COUNTER_ICON_IMAGE = ".qc-about-counter-icon img"
    COUNTER_VALUE = ".qc-about-counter-value"
    COUNTER_LABEL = ".qc-about-counter-label"

    def open_home(self, locale: str = "en") -> "HomeAboutSummaryPage":
        self.open(web_url("/", locale=locale))
        return self

    def wait_for_section(self) -> "HomeAboutSummaryPage":
        self.wait_for(self.SECTION_HEADING)
        return self

    def heading_text(self) -> str:
        return self.text(self.SECTION_HEADING)

    def tag_text(self) -> str:
        return self.text(self.SECTION_TAG)

    def description_text(self) -> str:
        return self.text(self.SECTION_DESC)

    def read_more_href(self) -> str:
        return self.page.locator(self.READ_MORE_LINK).get_attribute("href") or ""

    def counter_labels(self) -> list:
        return self.page.locator(self.COUNTER_LABEL).all_inner_texts()

    def counter_value_by_label(self, label: str) -> str:
        counter = self.page.locator(f'{self.COUNTER}:has({self.COUNTER_LABEL}:text-is("{label}"))')
        return counter.locator(self.COUNTER_VALUE).inner_text()

    def scroll_to_section(self) -> "HomeAboutSummaryPage":
        self.page.locator(self.SECTION_HEADING).scroll_into_view_if_needed()
        return self

    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def is_collage_visible(self) -> bool:
        return self.is_visible(self.COLLAGE)

    def collage_image_count(self) -> int:
        return self.page.locator(self.COLLAGE_ITEM_IMAGES).count()

    def collage_images_loaded(self) -> bool:
        """True if every collage image's own naturalWidth/naturalHeight is
        non-zero (a broken/never-loaded <img> reports 0 for both) — see
        module docstring's confirmed-live naturalWidth readings."""
        imgs = self.page.locator(self.COLLAGE_ITEM_IMAGES)
        count = imgs.count()
        if count == 0:
            return False
        for i in range(count):
            dims = imgs.nth(i).evaluate("el => ({w: el.naturalWidth, h: el.naturalHeight})")
            if not dims["w"] or not dims["h"]:
                return False
        return True

    def is_badge_visible(self) -> bool:
        return self.is_visible(self.BADGE)

    def badge_number_text(self) -> str:
        return self.text(self.BADGE_NUM)

    def badge_label_text(self) -> str:
        return self.text(self.BADGE_LABEL)

    def achievements_title_text(self) -> str:
        return self.text(self.ACHIEVEMENTS_TITLE)

    def counter_count(self) -> int:
        return self.page.locator(self.COUNTER).count()

    def counter_icons_loaded(self) -> bool:
        icons = self.page.locator(self.COUNTER_ICON_IMAGE)
        count = icons.count()
        if count == 0:
            return False
        for i in range(count):
            dims = icons.nth(i).evaluate("el => ({w: el.naturalWidth, h: el.naturalHeight})")
            if not dims["w"] or not dims["h"]:
                return False
        return True

    def is_counter_label_present(self, label: str) -> bool:
        return label in self.counter_labels()

    def page_direction(self) -> str:
        """<html dir="..."> — "ltr"/"rtl", same pattern as
        AboutQatarChamberPage.page_direction() / LanguageSwitcherComponent.
        page_direction()."""
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def media_content_x_positions(self) -> dict:
        """{"media": x, "content": x} bounding-box x of the collage/badge
        column vs. the tag/heading/description/CTA column — LTR: media <
        content; RTL: media > content (confirmed-live full mirror, see
        module docstring)."""
        media_box = self.page.locator(self.SECTION_MEDIA).bounding_box()
        content_box = self.page.locator(self.SECTION_CONTENT).bounding_box()
        return {
            "media": media_box["x"] if media_box else None,
            "content": content_box["x"] if content_box else None,
        }

    def is_media_before_content(self) -> bool:
        """True under LTR (media column left of content column), False
        under a real RTL mirror (see module docstring's confirmed-live
        x-position swap)."""
        positions = self.media_content_x_positions()
        if positions["media"] is None or positions["content"] is None:
            return False
        return positions["media"] < positions["content"]

    def document_overflow_px(self) -> int:
        """scrollWidth - clientWidth on <html> — >0 means real horizontal
        overflow. Confirmed live a harmless ~4px scrollbar-gutter delta at
        both mobile (375px) and tablet (768px) widths (see module
        docstring) — is_no_horizontal_overflow() applies a 10px tolerance
        against that confirmed baseline rather than requiring an exact 0."""
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )

    def is_no_horizontal_overflow(self, tolerance_px: int = 10) -> bool:
        return self.document_overflow_px() <= tolerance_px

    def cta_bounding_box(self) -> dict:
        box = self.page.locator(self.READ_MORE_LINK).bounding_box()
        return box or {}

    def click_read_more(self) -> None:
        self.click(self.READ_MORE_LINK)

    def click_read_more_and_wait(self, timeout_ms: int = 15000) -> None:
        """Clicks the Read More CTA and waits for the resulting navigation
        to settle — bounded, never raises (a genuinely broken/unreachable
        target must still let the caller read page.url afterward rather
        than aborting the test on the wait itself)."""
        self.click_read_more()
        try:
            self.page.wait_for_load_state("load", timeout=timeout_ms)
        except Exception:
            pass

    def is_badge_within_media_bounds(self) -> bool:
        """True if the badge overlay's bounding box sits within (overlays)
        the collage/media column's own bounding box — a 5px tolerance
        absorbs sub-pixel rounding."""
        badge_box = self.page.locator(self.BADGE).bounding_box()
        media_box = self.page.locator(self.SECTION_MEDIA).bounding_box()
        if not (badge_box and media_box):
            return False
        return (
            media_box["x"] - 5 <= badge_box["x"] <= media_box["x"] + media_box["width"] + 5
            and media_box["y"] - 5 <= badge_box["y"] <= media_box["y"] + media_box["height"] + 5
        )

    def is_achievements_title_above_counters(self) -> bool:
        title_box = self.page.locator(self.ACHIEVEMENTS_TITLE).bounding_box()
        counters_box = self.page.locator(self.COUNTERS_CONTAINER).bounding_box()
        if not (title_box and counters_box):
            return False
        return title_box["y"] < counters_box["y"]

    def section_bounding_box(self) -> dict:
        box = self.page.locator(self.SECTION).bounding_box()
        return box or {}

    def reload_until_heading_matches(
        self, expected_text: str, timeout_ms: int = 5000, interval_ms: int = 500
    ) -> bool:
        """Poll (reload + re-check), never a bare sleep — per
        cms-profile.md's Publish/Propagation Latency Budget guidance
        (measured ~0s for the one endpoint independently probed on this
        project; not independently re-measured for this section, so the
        conservative default timeout/interval is used rather than assuming
        the same near-instant figure)."""
        elapsed = 0
        while elapsed <= timeout_ms:
            self.open_home()
            self.wait_for_section()
            if self.heading_text() == expected_text:
                return True
            self.page.wait_for_timeout(interval_ms)
            elapsed += interval_ms
        return False

    def reload_until(self, condition_fn, timeout_ms: int = 5000, interval_ms: int = 500) -> bool:
        """Generic counterpart to reload_until_heading_matches() for a
        caller-supplied condition (e.g. counter order/active-status
        propagation) — same reload-and-poll mechanism, never a bare sleep,
        per cms-profile.md's Publish/Propagation Latency Budget guidance.
        `condition_fn` receives this page object and returns bool."""
        elapsed = 0
        while elapsed <= timeout_ms:
            self.open_home()
            self.wait_for_section()
            if condition_fn(self):
                return True
            self.page.wait_for_timeout(interval_ms)
            elapsed += interval_ms
        return False

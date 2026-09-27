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
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeAboutSummaryPage(BasePage):
    SECTION_TAG = ".qc-about-tag"
    SECTION_HEADING = ".qc-about-heading"
    SECTION_DESC = ".qc-about-desc"
    BADGE_NUM = ".qc-about-badge-num"
    BADGE_LABEL = ".qc-about-badge-label"
    READ_MORE_LINK = ".qc-about-readmore"
    ACHIEVEMENTS_TITLE = ".qc-about-achievements-title"
    COUNTER = ".qc-about-counter"
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

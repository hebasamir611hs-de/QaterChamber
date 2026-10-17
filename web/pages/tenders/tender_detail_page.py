"""
web/pages/tenders/tender_detail_page.py — TenderDetailPage.

Public-frontend Page Object for the eTender detail screen (PBI 130952 pilot
batch INVEST-TENDERS-TC-014..021, 032). Figma node 4747:189877.

CONFIRMED LIVE (2026-09-24, qcdev, browser_evaluate — disclosed Playwright-
MCP fallback, same rationale as tenders_listing_page.py's docstring: no
data-testid layer, plain typography/definition-list containers the CLI
extractor's interactive-element harvest does not surface):

  - Route: `/web/qatar-chamber/tender-details?tender=<TENDER_REF>` — the
    6 seeded tenders on qcdev use refs `QC-TENDER-130952-01` .. `-06`
    (confirmed live off the listing page's own card hrefs).
  - Every one of the 5 content sections (Overview, Tender profile,
    Commercial terms, Before you submit, Tender documents) repeats the
    SAME eyebrow+heading (`.qc-tnd-eyebrow` / `.qc-tnd-sectitle`, wrapped
    in `.qc-tnd-sechead`) and SAME `<dl class="qc-tnd-panel">` >
    `<dt class="qc-tnd-term">` / `<dd class="qc-tnd-desc">` field-pair
    pattern — `field_value()` below is written once and reused across
    TC-016/017/018 rather than one method per card.
  - Live-confirmed copy variance (design vs. spec, exactly as
    INVEST-TENDERS-TC-016 flags): the Key information card's field label
    reads "Work of description" (not "Work description") — verbatim on
    the live DOM.
  - **Live gap vs. INVEST-TENDERS-TC-002's expected result**: this page
    currently renders NO "Submit your eTender" CTA anywhere in the DOM
    (confirmed live — a full-page text/href scan for "etender"/"submit"
    found only the site nav's "eTenders" link, no CTA button/link).
    TC-002 expects the same reusable CTA component (CTL-2) to appear here
    too; `etender_cta_visible()` below reads the real state honestly (it
    returns False on this environment) rather than a locator that would
    silently no-op — the resulting test assertion is expected to FAIL on
    this environment, which is the correct, honest signal (see
    automation-standards.md's Result Integrity section) — not a locator
    defect to "fix" by relaxing the assertion.
"""

from core.web.base_page import BasePage
from config.settings import web_url

BACK_LINK = "a.qc-tnd-back"
CATEGORY_BADGE = ".qc-tnd-badge--cat"
STATUS_BADGE = ".qc-tnd-badge--open"
TITLE = "h1.qc-tnd-title"
ORG = "p.qc-tnd-org"
REF_CARD = ".qc-tnd-refcard"
REF_LABEL = ".qc-tnd-ref-term"
REF_VALUE = ".qc-tnd-ref-value"
PUBLISHED_LINE = ".qc-tnd-ref-pub"

SECTION_HEAD = ".qc-tnd-sechead"
SECTION_EYEBROW = ".qc-tnd-eyebrow"
SECTION_HEADING = ".qc-tnd-sectitle"
FIELD_TERM = "dt.qc-tnd-term"
FIELD_DESC = "dd.qc-tnd-desc"

DOWNLOAD_ROW = ".qc-tnd-file"
DOWNLOAD_CHIP = ".qc-tnd-file-chip"
DOWNLOAD_CTA = ".qc-tnd-file-cta"

DEADLINE_VALUE = "strong.qc-tnd-dl-date"
DEADLINE_SUBTEXT = ".qc-tnd-dl-time"
# "Opening date" / "Pre-bid meeting" rows: <div.qc-tnd-dl-row><dt.qc-tnd-dl-key><dd.qc-tnd-dl-val>
DEADLINE_ROW_KEY = ".qc-tnd-dl-key"

NEED_HELP_TITLE = "strong.qc-tnd-help-title"
NEED_HELP_BODY = ".qc-tnd-help-body"
NEED_HELP_EMAIL = "a.qc-tnd-help-mail"

# See module docstring — no stable class exists for this element because it
# does not currently render; kept as a role/text locator so the test reads
# the real (currently absent) state rather than silently no-op-ing.
ETENDER_CTA_BY_TEXT = "text=Submit your eTender"


class TenderDetailPage(BasePage):
    def open_detail(self, tender_ref: str, locale: str = "en") -> "TenderDetailPage":
        self.open(web_url(f"/web/qatar-chamber/tender-details?tender={tender_ref}", locale=locale))
        self.wait_for(TITLE, timeout=15000)
        return self

    def style_of(self, locator: str, properties: list, first: bool = False) -> dict:
        return self.computed_style(locator, properties, first=first)

    # ---- Header -------------------------------------------------------------
    def back_link_text(self) -> str:
        return self.text(BACK_LINK).strip()

    def category_badge_text(self) -> str:
        return self.text(CATEGORY_BADGE).strip()

    def status_badge_text(self) -> str:
        return self.text(STATUS_BADGE).strip()

    def title_text(self) -> str:
        return self.text(TITLE).strip()

    def reference_value(self) -> str:
        return self.text(REF_VALUE).strip()

    def published_line_text(self) -> str:
        return self.text(PUBLISHED_LINE).strip()

    def etender_cta_visible(self) -> bool:
        return self.is_visible(ETENDER_CTA_BY_TEXT)

    # ---- Section header pattern (reused across 5 cards) --------------------
    def section_header(self, heading_text: str) -> dict:
        headings = self.page.locator(SECTION_HEADING)
        count = headings.count()
        for i in range(count):
            if headings.nth(i).inner_text().strip() == heading_text:
                head = headings.nth(i).locator("xpath=ancestor::*[contains(@class,'qc-tnd-sechead')][1]")
                eyebrow = head.locator(SECTION_EYEBROW).first
                return {"eyebrow": eyebrow.inner_text().strip(), "heading": heading_text}
        raise AssertionError(f"section heading {heading_text!r} not found")

    def section_heading_texts(self) -> list[str]:
        return [t.strip() for t in self.page.locator(SECTION_HEADING).all_inner_texts() if t.strip()]

    def field_value(self, term_text: str) -> str:
        terms = self.page.locator(FIELD_TERM)
        count = terms.count()
        for i in range(count):
            if terms.nth(i).inner_text().strip() == term_text:
                return self.page.locator(FIELD_DESC).nth(i).inner_text().strip()
        raise AssertionError(f"field {term_text!r} not found")

    def field_term_text(self, index: int) -> str:
        return self.page.locator(FIELD_TERM).nth(index).inner_text().strip()

    # ---- Downloads ------------------------------------------------------------
    def download_row_for(self, title_substring: str):
        return self.page.locator(f"{DOWNLOAD_ROW}:has-text('{title_substring}')").first

    # ---- Sidebar --------------------------------------------------------------
    def deadline_value_text(self) -> str:
        return self.text(DEADLINE_VALUE).strip()

    def deadline_subtext_text(self) -> str:
        return self.text(DEADLINE_SUBTEXT).strip()

    def _sidebar_row_key(self, label_text: str):
        keys = self.page.locator(DEADLINE_ROW_KEY)
        for i in range(keys.count()):
            if keys.nth(i).inner_text().strip() == label_text:
                return keys.nth(i)
        raise AssertionError(f"sidebar row {label_text!r} not found")

    def sidebar_row_value(self, label_text: str) -> str:
        key = self._sidebar_row_key(label_text)
        return key.locator("xpath=following-sibling::*[1]").inner_text().strip()

    def sidebar_row_styles(self, label_text: str, properties: list) -> dict:
        """{'label': {...}, 'value': {...}} computed styles for one deadline-card row."""
        key = self._sidebar_row_key(label_text)
        js = "(el, props) => { const s = getComputedStyle(el); const o = {}; props.forEach(p => o[p] = s[p]); return o; }"
        return {
            "label": key.evaluate(js, properties),
            "value": key.locator("xpath=following-sibling::*[1]").evaluate(js, properties),
        }

    def need_help_email_text(self) -> str:
        return self.text(NEED_HELP_EMAIL).strip()

    # ---- RTL --------------------------------------------------------------
    def is_rtl(self) -> bool:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')") == "rtl"

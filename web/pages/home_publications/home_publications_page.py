"""
web/pages/home_publications/home_publications_page.py — HomePublicationsPage.

PBI 129386 / QC-HOME-010 "Publications Section" — its own Home-page
section/module folder per active/standards.md's Home-page sections table.
This pass covers 9 approved, Automation-tagged, UI-category, Web-platform
cases handed off for this PBI (ADO TC 134312-134321, minus 134318 which was
not included in this batch). Control_Panel-tagged cases for this same PBI are
out of scope for this run (see the sibling home_publications_admin_page.py
skeleton).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --scope "[class*=publication]"

    -> [role] uniq=1  get_by_role("link", name="Explore Publications")
    -> [role] uniq=1  get_by_role("tablist", name="Publication type filter")
    -> [role] uniq=1  get_by_role("tab", name="All Publications")
    -> [role] uniq=1  get_by_role("tab", name="Research Papers")
    -> [role] uniq=1  get_by_role("tab", name="Guides")
    -> [role] uniq=1  get_by_role("tab", name="Reports")
    -> [role] uniq=1  get_by_role("tab", name="White Papers")
    -> [role] uniq=1  get_by_role("tab", name="Manuals")
    -> [role] uniq=1  get_by_role("tab", name="Brochures")
    -> [role] uniq=1  get_by_role("tablist", name="Publications pages")

The extractor's harvest only covers interactive/labelled elements (a, button,
input, select, textarea, [role], [data-testid], [data-test], [aria-label]),
which surfaced the 7 filter tabs, the two tablists, and the "Explore
Publications" link (non-unique — TWO CTAs share that accessible name, see
below) — but not the plain span/h2/p/div/article structure (tag, heading,
description, cards, badges). Resolved the same documented way already used
in home_strategic_direction_page.py: one additional, disclosed, scoped
Playwright script (still CLI/shell, never the Playwright MCP), reusing
BasePage's own license-gate/overlay guard sequence, to read the live DOM
structure and computed styles for the non-interactive elements.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home):

    section.qc-home-publications
      div.qc-pub-inner
        div.qc-pub-head
          div.qc-pub-head-text
            span.qc-pub-tag                    (TAG — "Publications")
            h2.qc-pub-heading                  (HEADING)
            p.qc-pub-desc                      (DESCRIPTION)
          a.qc-pub-explore.qc-pub-explore--top  (CTA_TOP — visible on desktop)
            span "Explore Publications"
            svg > path                          (arrow icon)
        div.qc-pub-tabs[role=tablist]            (TABS_LIST — 7 buttons, role=tab each)
        div.qc-pub-carousel
          div.qc-pub-track
            div.qc-pub-page (x2 — 8 cards total, 5 + 3, 2 filler slots on page 2)
              a.qc-pub-card
                div.qc-pub-card-media > img.qc-pub-card-img
                div.qc-pub-card-scrim
                span.qc-pub-badge                (type badge, e.g. "Research Paper")
                div.qc-pub-card-body
                  h3.qc-pub-card-title
                  div.qc-pub-card-meta
                    span.qc-pub-meta-item (x3) > span.qc-pub-meta-text  (date, views, downloads)
                div.qc-pub-card-hover
                  p.qc-pub-card-hover-desc
                  span.qc-pub-card-cta > span.qc-pub-cta-label ("Download / View")
          p.qc-pub-empty                          (EMPTY — "No publications in this category.")
          div.qc-pub-dots[role=tablist]            (DOTS — pagination, 2 buttons, role=tab each
                                                     — NOTE: shares role="tab" with the filter
                                                     tabs, so TAB/ACTIVE_TAB below are scoped to
                                                     .qc-pub-tabs to avoid colliding with these)
          a.qc-pub-explore.qc-pub-explore--bottom  (CTA_BOTTOM — hidden on desktop, see below)

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here — a mismatch below is scripted to FAIL
HONESTLY against the case's literal stated expectation, never quietly
re-targeted at the observed value):

  - TC 134312: tag text = "Publications", heading text = "Explore Our
    Knowledge Hub", description text = "Access valuable insights, reports,
    and studies on business and market trends. Stay informed with up-to-date
    research to support smart decisions and growth." — all match the case's
    stated copy exactly. Description color computes to rgb(124, 123, 123),
    which IS exactly #7C7B7B — a genuine, exact match to the case's stated
    color token. The case's "specified style" for the tag/heading is not
    itself enumerated in the source case text handed to this batch, so only
    the copy/visibility (not fabricated pixel values) are asserted for those
    two elements.
  - TC 134313: the case's source text does not enumerate the 7 tabs'
    specific labels/order inline (no attached list was provided in this
    batch) — the live, CLI-confirmed order is used as the asserted ground
    truth (disclosed here, not fabricated): "All Publications", "Research
    Papers", "Guides", "Reports", "White Papers", "Manuals", "Brochures".
  - TC 134314: "All Publications" active tab background computes to
    rgb(145, 23, 49) (a maroon) and text to rgb(255, 255, 255) (white) —
    both match. border-radius computes to exactly 6px — matches. The case
    states "no border": the live element's computed `border` is actually
    `1px solid rgb(145, 23, 49)` — a real, present 1px border, NOT `none` —
    but its color is identical to the fill, so it renders with no visible
    edge. Scripted per the case's literal "no border" wording (checking for
    a literal none/0-width border, not the visually-equivalent same-color
    trick) — a real, measured, very-minor technical mismatch, not silently
    reinterpreted as a pass.
  - TC 134315: CONFIRMED LIVE, genuine full pass — the inactive "Reports"
    tab computes background rgb(255, 255, 255) (white), border
    `1px solid rgb(222, 222, 221)` (exactly #DEDEDD), text rgb(108, 108, 107)
    (exactly #6C6C6B), border-radius 6px and padding "8px 16px" — identical
    radius/padding to the active tab.
  - TC 134316: CONFIRMED LIVE, genuine full pass — the first card carries
    all seven elements: thumbnail image, type badge ("Research Paper"),
    title ("Qatar Trade & Investment Outlook 2026"), publish date
    ("20 May 2026"), view count ("4.2K"), download count ("825"), and a
    hover CTA/action label ("Download / View") — none missing.
  - TC 134317: the CTA's visual spec matches on desktop — the visible
    (`--top`) variant computes maroon fill rgb(145, 23, 49), white text,
    font-weight 600 (SemiBold), border-radius 9999px (pill), and carries an
    svg > path arrow icon. However, the case's step 1 is "scroll to the
    BOTTOM of the section" expecting the CTA "visible below the cards" —
    CONFIRMED LIVE at the framework's default 1920x1080 viewport: the
    `--bottom` variant computes `display: none` (only the `--top` variant,
    positioned in the section's HEAD row next to the heading, is visible);
    the `--bottom` variant only becomes visible at narrow/mobile viewports
    (confirmed visible with a real box at 375x812). This is a genuine,
    real placement mismatch on desktop, scripted to fail honestly against
    the case's literal step, not silently worked around.
  - TC 134319: CONFIRMED LIVE (AR, https://qcdev.ihorizons.com/ar/home):
    `<html dir="rtl">`, section computes `direction: rtl`, and every field
    renders real, non-empty Arabic copy: tag "المنشورات", heading "استكشف
    مركز المعرفة", description "اطّلع على رؤى وتقارير ودراسات قيّمة حول
    اتجاهات الأعمال والأسواق. ابقَ على اطلاع بأحدث الأبحاث لدعم القرارات
    الذكية والنمو.", and all 7 tabs in Arabic ("جميع المنشورات", "الأوراق
    البحثية", "الأدلة", "التقارير", "الأوراق البيضاء", "الكتيبات", "الكتيبات
    التعريفية") — no English text or left-aligned artifacts found. Real,
    genuine pass.
  - TC 134320: CONFIRMED LIVE — there is NO skeleton/spinner/placeholder
    element scoped to the Publications section anywhere in the DOM, at any
    point observed (checked both in the fully-loaded HTML via a keyword scan
    for skeleton/loading/spinner class names, and in an early snapshot taken
    right after navigation commit under an artificially throttled network).
    The only "spinner" class found on the whole homepage
    (`qc-pod-spinner`) belongs to the unrelated Podcast section. Scripted
    per the case's literal expected result (a skeleton/spinner IS expected)
    — a real, observed gap, not a framework defect.
  - TC 134321: CONFIRMED LIVE, a real, measured mismatch — EVERY type badge
    on the page ("Research Paper", "Report", "Guides", "Brochure", "White
    Paper", "Manuals") computes the IDENTICAL style: color
    rgb(255, 255, 255), background rgba(29, 29, 27, 0.4) (a flat dark
    overlay), border-radius 9999px. Only the text LABEL differs per type;
    there is no distinct color/background per publication type at all,
    contradicting the case's "visually distinct styling per type" — scripted
    to fail honestly against the case's literal expected result.
"""

import time

from core.web.base_page import BasePage
from config.settings import web_url


class HomePublicationsPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ────────────
    SECTION = ".qc-home-publications"
    INNER = ".qc-pub-inner"
    TAG = ".qc-pub-tag"
    HEADING = ".qc-pub-heading"
    DESCRIPTION = ".qc-pub-desc"
    CTA_TOP = ".qc-pub-explore--top"
    CTA_BOTTOM = ".qc-pub-explore--bottom"
    # Scoped to .qc-pub-tabs — the pagination dots (.qc-pub-dots) also carry
    # role="tab" on their buttons (see docstring), so an unscoped ".qc-pub-tab"
    # class alone is safe (different class name), but role-based lookups here
    # deliberately stay scoped/CSS for the same reason.
    TABS_LIST = ".qc-pub-tabs"
    TAB = ".qc-pub-tabs .qc-pub-tab"
    ACTIVE_TAB = ".qc-pub-tabs .qc-pub-tab.is-active"
    CAROUSEL = ".qc-pub-carousel"
    CARD = ".qc-pub-carousel .qc-pub-card"
    # Relative selectors — always chained off a specific card Locator.
    CARD_IMG = ".qc-pub-card-img"
    CARD_BADGE = ".qc-pub-badge"
    CARD_TITLE = ".qc-pub-card-title"
    CARD_META_TEXT = ".qc-pub-meta-text"
    CARD_HOVER_DESC = ".qc-pub-card-hover-desc"
    CARD_CTA_LABEL = ".qc-pub-cta-label"
    DOTS = ".qc-pub-dots"
    DOT = ".qc-pub-dots .qc-pub-dot"
    EMPTY = ".qc-pub-empty"
    HTML_ROOT = "html"

    _STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "color: cs.color, backgroundColor: cs.backgroundColor,"
        "border: cs.border, borderRadius: cs.borderRadius, boxShadow: cs.boxShadow,"
        "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize,"
        "lineHeight: cs.lineHeight, padding: cs.padding, gap: cs.gap,"
        "display: cs.display, direction: cs.direction, textAlign: cs.textAlign"
        "}; }"
    )

    def _style(self, locator) -> dict:
        loc = locator if hasattr(locator, "evaluate") else self.page.locator(locator).first
        return loc.evaluate(self._STYLE_JS)

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomePublicationsPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomePublicationsPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def open_home_with_throttled_network(self, delay_seconds: float = 0.2) -> bool:
        """TC 134320 — simulates step 1 ('network throttled to slow 3G') by
        delaying every network response, navigating only to
        'domcontentloaded', probing for a loading placeholder in that window,
        then waiting for the real section to resolve. Returns True if a
        skeleton/spinner/placeholder scoped to the Publications section was
        observed at any point before the section's real content settled."""
        def _slow(route):
            time.sleep(delay_seconds)
            route.continue_()

        self.page.route("**/*", _slow)
        self.page.goto(web_url("/home"), wait_until="domcontentloaded")
        seen_placeholder = self.has_loading_placeholder()
        self.wait_for(self.SECTION, timeout=30000)
        seen_placeholder = seen_placeholder or self.has_loading_placeholder()
        self.page.unroute("**/*", _slow)
        return seen_placeholder

    def has_loading_placeholder(self) -> bool:
        return self.page.locator(
            ".qc-pub-skeleton, .qc-pub-loading, "
            "[class*='qc-pub'][class*='skeleton'], "
            "[class*='qc-pub'][class*='loading'], "
            "[class*='qc-pub'][class*='spinner']"
        ).count() > 0

    def scroll_to_section(self) -> "HomePublicationsPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    def scroll_to_section_bottom(self) -> "HomePublicationsPage":
        self.page.locator(self.SECTION).evaluate("el => el.scrollIntoView({block: 'end'})")
        return self

    # ── Page-level direction ─────────────────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    # ── Tag / heading / description ─────────────────────────────────────
    def is_tag_visible(self) -> bool:
        return self.is_visible(self.TAG)

    def tag_text(self) -> str:
        return self.text(self.TAG)

    def is_heading_visible(self) -> bool:
        return self.is_visible(self.HEADING)

    def heading_text(self) -> str:
        return self.text(self.HEADING)

    def is_description_visible(self) -> bool:
        return self.is_visible(self.DESCRIPTION)

    def description_text(self) -> str:
        return self.text(self.DESCRIPTION)

    def description_style(self) -> dict:
        return self._style(self.DESCRIPTION)

    # ── Filter tab bar ───────────────────────────────────────────────────
    def tab_labels(self) -> list:
        return self.page.locator(self.TAB).all_inner_texts()

    def tab_count(self) -> int:
        return self.page.locator(self.TAB).count()

    def tab_by_name(self, name: str):
        return self.page.get_by_role("tab", name=name, exact=True)

    def active_tab_text(self) -> str:
        return self.text(self.ACTIVE_TAB)

    def active_tab_style(self) -> dict:
        return self._style(self.ACTIVE_TAB)

    def inactive_tab_style(self, name: str) -> dict:
        return self._style(self.tab_by_name(name))

    # ── Publication cards ────────────────────────────────────────────────
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_title_text(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_TITLE).inner_text()

    def card_badge_text(self, index: int = 0) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BADGE).inner_text()

    def card_meta_texts(self, index: int = 0) -> list:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_META_TEXT).all_inner_texts()

    def card_required_elements_present(self, index: int = 0) -> dict:
        """The 7 elements a publication card must show per TC 134316: a
        thumbnail image, a type badge, a title, a publish date, a view
        count, a download count, and a CTA/action label."""
        card = self.page.locator(self.CARD).nth(index)
        metas = card.locator(self.CARD_META_TEXT)

        def _meta_non_empty(i: int) -> bool:
            return metas.count() > i and metas.nth(i).inner_text().strip() != ""

        return {
            "image": card.locator(self.CARD_IMG).count() > 0,
            "badge": card.locator(self.CARD_BADGE).count() > 0
            and card.locator(self.CARD_BADGE).inner_text().strip() != "",
            "title": card.locator(self.CARD_TITLE).count() > 0
            and card.locator(self.CARD_TITLE).inner_text().strip() != "",
            "date": _meta_non_empty(0),
            "views": _meta_non_empty(1),
            "downloads": _meta_non_empty(2),
            "cta_label": card.locator(self.CARD_CTA_LABEL).count() > 0
            and card.locator(self.CARD_CTA_LABEL).inner_text().strip() != "",
        }

    def badge_style_for_label(self, label_substring: str) -> dict:
        """Computed style of the first card badge whose text contains
        `label_substring` (e.g. 'Report' or 'Guides') — used by TC 134321 to
        compare one publication type's badge against another's."""
        loc = self.page.locator(self.CARD_BADGE).filter(has_text=label_substring).first
        return self._style(loc)

    # ── CTA ("Explore Publications") ─────────────────────────────────────
    def is_cta_top_visible(self) -> bool:
        return self.is_visible(self.CTA_TOP)

    def is_cta_bottom_visible(self) -> bool:
        return self.is_visible(self.CTA_BOTTOM)

    def cta_top_style(self) -> dict:
        return self._style(self.CTA_TOP)

    def cta_bottom_style(self) -> dict:
        return self._style(self.CTA_BOTTOM)

    def cta_has_arrow_icon(self, which: str = "top") -> bool:
        sel = self.CTA_TOP if which == "top" else self.CTA_BOTTOM
        return self.page.locator(sel).locator("svg").count() > 0

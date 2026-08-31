"""
web/pages/home_community_partners/home_community_partners_page.py —
HomeCommunityPartnersPage.

PBI 129385 / QC-HOME-009 "Community Partners" — its own Home-page
section/module folder per active/standards.md's Home-page sections table.
This pass covers 8 approved, Automation-tagged, UI-category, Web-platform
cases handed off directly (ADO TC 135805, 135806, 135807, 135808, 135810,
135811, 135812, 135815). No Control_Panel-tagged cases were handed off for
this PBI in this batch — home_community_partners_admin_page.py stays a
skeleton (see its own docstring for the one Control_Panel-touching
precondition this batch still needed, TC 135811's CMS unpublish step).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --viewport 1920x1080

    -> 40 candidates, none for Community Partners (the section carries no
       interactive/labelled element the extractor's role/testid/id-only
       harvester surfaces — same "ambiguous/unreachable via role" condition
       already documented in home_strategic_direction_page.py and
       home_promo_banners_page.py: the heading, description, and partner
       logos are plain <h2>/<p>/<a><span><img> elements with no role/
       aria-label of their own).
    -> re-ran with --max 200 and --find "partner": zero matches.

Resolved the same way as those precedents: two additional, disclosed, scoped
Playwright scripts (still CLI/shell, never the Playwright MCP), reusing
BasePage's own license-gate/overlay guard sequence, to read the live DOM/
computed-style structure and to sample the marquee's real motion over time.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home):

    section.qc-home-community-partners
      div.qc-partners-inner
        h2.qc-partners-title                          (HEADING — "Community Partners")
        p.qc-partners-subtitle                         (DESCRIPTION — "Trusted by leading organizations across key industries")
        div.qc-partners-marquee.qc-partners-marquee--animated  (MARQUEE)
          div.qc-partners-logos   (STRIP 1 — 6 <a.qc-partner-link><span.qc-partner-logo-wrap><img></a>)
          div.qc-partners-logos   (STRIP 2 — identical 6, duplicated for the CSS seamless-loop marquee technique)

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here — a mismatch below is scripted to FAIL
HONESTLY against the case's stated value, never quietly re-targeted at the
observed value, per this project's established convention):

  - TC 135805 (EN heading typography): live computes font-family "Cairo,
    system-ui, -apple-system, \"Segoe UI\", sans-serif" (Cairo is the primary
    face — matches), font-weight 700 (matches), font-size 36px (matches),
    color rgb(29, 29, 27) = #1D1D1B (matches exactly). Computed line-height
    is **43.2px** (36px * 1.2), not the case's stated 44px. text-align
    computes to **"center"**, not the case's stated "left-aligned" — the
    whole section (badge-less, single centered column) is laid out
    center-aligned in the live build, not left-aligned.
  - TC 135806 (AR mirrored heading): CONFIRMED LIVE (AR,
    https://qcdev.ihorizons.com/ar/home) — `<html dir="rtl">`, section
    `direction: rtl`, heading text is the real Arabic string
    "شركاء المجتمع", same Cairo/700/36px/43.2px/#1D1D1B typography as EN.
    However: (1) text-align computes to **"center"** in AR too, not the
    case's stated "right-aligned"; (2) the partner-logo row's left-to-right
    DOM/visual order (QatarEnergy, Qatar Airways, QNB) is **IDENTICAL** in AR
    to EN — it is NOT reversed. There is also no two-column
    heading/description-vs-carousel split to mirror (this section is one
    centered column top-to-bottom, unlike Strategic Direction's two-column
    layout) — "the layout is a horizontal mirror of the EN layout" has no
    structural analog to satisfy beyond the (already-failing) logo order.
  - TC 135807 (description block position): CONFIRMED LIVE — the
    `<p class="qc-partners-subtitle">` renders directly below the
    `<h2 class="qc-partners-title">` heading in both EN ("Trusted by leading
    organizations across key industries") and AR ("موثوق بها من قبل
    المؤسسات الرائدة في القطاعات الرئيسية"), each in its own language,
    matching this case's expected result with no observed mismatch.
  - TC 135808 (6 real partner logos in a horizontal row): the live qcdev
    instance currently has only **3 unique configured partners** —
    QatarEnergy, Qatar Airways, QNB (confirmed by alt text and by the
    Liferay Documents & Media asset filenames encoded in each `<img src>`,
    e.g. `...objectEntryExternalReferenceCode=QC_CP_QATARENERGY`) — not the
    6 the case's precondition names. Each of those 3 repeats exactly twice
    within a single `.qc-partners-logos` strip (giving 6 `<a>` nodes per
    strip — QatarEnergy/Qatar Airways/QNB/QatarEnergy/Qatar Airways/QNB),
    and the whole 6-node strip is then duplicated once more as a sibling
    `.qc-partners-logos` for the marquee's seamless CSS loop (12 `<a>` nodes
    total in the DOM). The 6 nodes actually rendered in the first strip do
    tile with **no gap or overlap** between consecutive logos (confirmed via
    bounding-box comparison) — that half of the expected result holds; the
    "6 real (i.e., 6 distinct) partner logos" half does not — only 3 are
    distinct.
  - TC 135810 (AR carousel scroll direction mirrors to RTL): measured the
    first `.qc-partners-logos` strip's real `getBoundingClientRect().x`
    twice, 500ms apart (same before/after-sample technique already used by
    `home_social_icons_page.py`'s hover check — there is no discrete "state"
    to `wait_for()` on a continuously-animating CSS transform). EN: x moved
    from 304.20 to 296.73 (delta -7.47, i.e. the strip translates in the
    **negative-x / leftward** direction). AR: x moved from 304.68 to 297.21
    (delta -7.47) — the **same** negative-x/leftward direction, not
    mirrored. The case's expected "logos scroll right-to-left, mirrored from
    the EN direction" implies EN and AR should differ in sign; live, they do
    not.
  - TC 135811 (no empty container when the section doesn't render): this
    case's own Arrange step ("deactivate/unpublish all partner entries in
    the CMS") requires an authenticated Site Content Editor session.
    TEST_USER / TEST_PASSWORD are blank in .env (same, already-documented
    project-wide blocker as home_featured_event_admin_page.py / commit
    2cbbb4c) — no partner could actually be unpublished this session, and no
    Playwright MCP fallback is available either. The Web-platform assertion
    side of this case (does the section still render, is there a leftover
    gap) is fully scriptable and lives here; the CMS-side Arrange step is
    gated in the sibling home_community_partners_admin_page.py /
    test_home_community_partners_web.py (see their docstrings) exactly like
    the established blocked-CMS convention, never guessed.
  - TC 135812 (1920x1080 desktop rendering): CONFIRMED LIVE — the section
    and its marquee render a real, non-zero box at 1920x1080 and
    `document.documentElement.scrollWidth == clientWidth` (no horizontal
    overflow), matching this case's expected result with no observed
    mismatch.
  - TC 135815 (logo alt text): the live qcdev instance has NO partner named
    "Qatar Development Bank" — the 3 real, configured partners are
    QatarEnergy, Qatar Airways, and QNB, and every rendered `<img alt="...">`
    is the bare company name (e.g. `alt="QatarEnergy"`, AR: `alt="قطر
    للطاقة"`) with **no "logo" suffix** at all, unlike the case's stated
    exact value "Qatar Development Bank logo". Scripted per the case's
    literal expected result against the first configured partner's alt text;
    will fail honestly (wrong name AND missing " logo" suffix), not a
    framework defect.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeCommunityPartnersPage(BasePage):
    # ── Locators — real, CLI/script-verified constants (see docstring) ──────
    SECTION = ".qc-home-community-partners"
    INNER = ".qc-partners-inner"
    HEADING = ".qc-partners-title"
    DESCRIPTION = ".qc-partners-subtitle"
    MARQUEE = ".qc-partners-marquee"
    LOGOS_STRIP = ".qc-partners-logos"          # 2 matches live — always scope with .first for "the" strip
    PARTNER_LINK = ".qc-partner-link"
    PARTNER_IMG = "img"
    HTML_ROOT = "html"

    _TEXT_STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize,"
        "lineHeight: cs.lineHeight, color: cs.color, textAlign: cs.textAlign,"
        "direction: cs.direction"
        "}; }"
    )

    def _text_style(self, locator) -> dict:
        loc = locator if hasattr(locator, "evaluate") else self.page.locator(locator).first
        return loc.evaluate(self._TEXT_STYLE_JS)

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeCommunityPartnersPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeCommunityPartnersPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomeCommunityPartnersPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    # ── Page-level / section direction ──────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    # ── Visibility ───────────────────────────────────────────────────────
    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def is_heading_visible(self) -> bool:
        return self.is_visible(self.HEADING)

    def is_description_visible(self) -> bool:
        return self.is_visible(self.DESCRIPTION)

    def is_carousel_visible(self) -> bool:
        return self.is_visible(self.MARQUEE)

    # ── Heading ──────────────────────────────────────────────────────────
    def heading_text(self) -> str:
        return self.text(self.HEADING)

    def heading_style(self) -> dict:
        return self._text_style(self.HEADING)

    # ── Description ──────────────────────────────────────────────────────
    def description_text(self) -> str:
        return self.text(self.DESCRIPTION)

    def description_style(self) -> dict:
        return self._text_style(self.DESCRIPTION)

    # ── Relative position of heading vs. description (TC 135807) ────────
    def heading_box(self) -> dict:
        return self.page.locator(self.HEADING).bounding_box()

    def description_box(self) -> dict:
        return self.page.locator(self.DESCRIPTION).bounding_box()

    def description_renders_below_heading(self) -> bool:
        h, d = self.heading_box(), self.description_box()
        if not h or not d:
            return False
        return d["y"] >= (h["y"] + h["height"])

    # ── Partner logo row (first strip — see docstring's duplication note) ─
    def _first_strip_links(self):
        return self.page.locator(self.LOGOS_STRIP).first.locator(self.PARTNER_LINK)

    def partner_logo_alt_texts(self) -> list:
        """Raw alt texts, in DOM/visual order, from the first
        `.qc-partners-logos` strip (6 nodes live — see docstring; NOT
        deduplicated, since the no-gap/no-overlap check needs every
        rendered node, not just the distinct companies)."""
        links = self._first_strip_links()
        return [
            links.nth(i).locator(self.PARTNER_IMG).get_attribute("alt")
            for i in range(links.count())
        ]

    def unique_partner_names(self) -> list:
        """Distinct partner names, order preserved, deduplicated from
        `partner_logo_alt_texts()` (see docstring: only 3 are distinct live,
        not the 6 named in TC 135808's precondition)."""
        seen, ordered = set(), []
        for alt in self.partner_logo_alt_texts():
            if alt not in seen:
                seen.add(alt)
                ordered.append(alt)
        return ordered

    def partner_logo_srcs(self) -> list:
        """Raw `img[src]` values, in DOM/visual order, from the first strip.
        Language-independent (the same asset file serves EN and AR) — used
        to compare left-to-right partner ORDER across languages without the
        alt text's own EN/AR translation getting in the way (TC 135806)."""
        links = self._first_strip_links()
        return [
            links.nth(i).locator(self.PARTNER_IMG).get_attribute("src")
            for i in range(links.count())
        ]

    def unique_partner_identifiers(self) -> list:
        """Distinct partner identity (by asset src), order preserved — the
        language-independent counterpart of `unique_partner_names()`."""
        seen, ordered = set(), []
        for src in self.partner_logo_srcs():
            if src not in seen:
                seen.add(src)
                ordered.append(src)
        return ordered

    def partner_count(self) -> int:
        return len(self.unique_partner_names())

    def rendered_logo_count(self) -> int:
        """Every logo actually rendered in the first strip (raw, not
        deduplicated) — the literal count of logos on screen."""
        return len(self.partner_logo_alt_texts())

    def first_partner_alt_text(self) -> str:
        alts = self.partner_logo_alt_texts()
        return alts[0] if alts else None

    def partner_logo_boxes(self) -> list:
        links = self._first_strip_links()
        return [links.nth(i).locator(self.PARTNER_IMG).bounding_box() for i in range(links.count())]

    def has_no_gap_or_overlap_between_logos(self) -> bool:
        """Confirms consecutive rendered logos in the first strip neither
        overlap (next left edge >= this right edge) nor leave a visible slot
        empty (a logo with zero width/height)."""
        boxes = self.partner_logo_boxes()
        if len(boxes) < 2:
            return False
        for box in boxes:
            if not box or box["width"] <= 0 or box["height"] <= 0:
                return False
        for prev, nxt in zip(boxes, boxes[1:]):
            if nxt["x"] < (prev["x"] + prev["width"]):
                return False
        return True

    # ── Marquee scroll direction (TC 135810) ─────────────────────────────
    def _logos_strip_x(self) -> float:
        box = self.page.locator(self.LOGOS_STRIP).first.bounding_box()
        return box["x"] if box else None

    def marquee_scroll_delta_x(self, sample_ms: int = 500) -> float:
        """Real, timed before/after sample of the animated strip's own x
        position — the same before/after-transition technique already used
        by home_social_icons_page.py's hover check; there is no discrete
        element STATE to wait_for() on a continuously-animating CSS
        transform, so a short, explicit `wait_for_timeout` is the honest
        way to observe real motion (never a `time.sleep()`)."""
        x0 = self._logos_strip_x()
        self.page.wait_for_timeout(sample_ms)
        x1 = self._logos_strip_x()
        if x0 is None or x1 is None:
            return None
        return x1 - x0

    # ── Responsive / layout (TC 135812) ──────────────────────────────────
    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def section_box(self) -> dict:
        return self.page.locator(self.SECTION).bounding_box()

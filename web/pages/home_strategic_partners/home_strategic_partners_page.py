"""
web/pages/home_strategic_partners/home_strategic_partners_page.py —
HomeStrategicPartnersPage.

PBI 129391 / QC-HOME-015 "Strategic Partners" — its own Home-page
section/module folder per active/standards.md's Home-page sections table.
This pass covers the 15 approved, Automation-tagged, Web-platform cases in
this batch whose Arrange step needs nothing beyond the public Home Page (ADO
TC 136215, 136216, 136217, 136218, 136220, 136221, 136222, 136223, 136224,
136225, 136226, 136227, 136228, 136229, 136231). The remaining 8 cases in
this batch (136233, 136289, 136291, 136294, 136296, 136300, 136302, 136304)
each need an authenticated Site Content Editor session to set up their own
Arrange step (deactivate/reactivate partners, edit Start/End Date, create a
Draft entry, publish a logo change, unpublish/delete an entry) — those live
in the sibling home_strategic_partners_admin_page.py / their gated tests in
test_home_strategic_partners_web.py (see that module's docstring for the
same, already-documented project-wide TEST_USER/TEST_PASSWORD-blank
blocker as home_community_partners_admin_page.py / commit 2cbbb4c).

Every case in this batch's own Tags carries `GLOBAL` (not `EVENT`) as its
Service/Module axis — confirmed directly from the injected case JSON, not
inferred from the "Partners" theme the way home_community_partners_page.py's
docstring had to (that batch's Tags were never separately supplied). Markers
below apply @pytest.mark.global_ accordingly.

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --viewport 1920x1080
    -> 40 candidates, none for Strategic Partners (same "ambiguous/
       unreachable via role" condition already documented in
       home_community_partners_page.py / home_strategic_direction_page.py /
       home_promo_banners_page.py: the heading, subtitle, and partner logos
       are plain <h2>/<p>/<span><img> elements with no role/aria-label of
       their own on the whole-page role/testid/id-only harvest).
    -> re-ran with --find "partner" --max 200: 0 candidates.

Resolved the same way as those precedents: additional, disclosed, scoped
Playwright scripts (still CLI/shell, never the Playwright MCP), reusing
BasePage's own license-gate/overlay guard sequence, to read the live DOM/
computed-style structure directly, sample the marquee's real motion over
time, and toggle dark mode via AccessibilityToolsComponent.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home):

    section.qc-home-strategic-partners
      div.qc-sp-inner
        h2.qc-sp-title                                  ("Strategic Partners")
        p.qc-sp-subtitle                                 ("Trusted by leading organizations across key industries")
        div.qc-sp-marquee.qc-sp-marquee--animated
          div.qc-sp-logos                                 (STRIP 1 — 6 <span.qc-sp-logo-item role=img><img.qc-sp-logo></span>)
          div.qc-sp-logos[aria-hidden="true"]              (STRIP 2 — identical 6, duplicated for the CSS seamless-loop marquee)

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here — a mismatch below is scripted to FAIL
HONESTLY against the case's stated value, never quietly re-targeted at the
observed value, per this project's established convention):

  - TC 136215 (EN heading typography): live computes font-family "Cairo,
    system-ui, -apple-system, \"Segoe UI\", sans-serif" (matches),
    font-weight 700 (matches "Bold"), font-size 36px (matches), color
    rgb(29, 29, 27) = #1D1D1B (matches exactly). Computed line-height is
    **43.2px** (36px * 1.2), not the case's stated 44px.
  - TC 136216 (EN subtitle typography): text matches exactly. font-family
    Cairo (matches), font-weight 400 (matches "Regular"), font-size 18px
    (matches), color rgb(124, 123, 123) = #7C7B7B (matches exactly).
    Computed line-height is **27px**, not the case's stated 28px.
  - TC 136217 (light-mode gradient background): live computes
    `backgroundImage: "none"`, a **plain solid** `rgb(255, 255, 255)`
    background — NOT the case's stated
    `linear-gradient(135deg, #FFFFFF 0%, #F6F6F6 100%)`. No gradient renders
    at all in the light-mode build.
  - TC 136218 (logo tile fixed size + dim opacity): the rendered
    `img.qc-sp-logo` tile is **NOT a fixed 138x48px** across partners — live
    measures QatarEnergy 136.59x47.98px, Qatar Airways 160x48px, QNB
    173.875x47.98px (each logo's own intrinsic aspect ratio, height pinned
    near 48px but width varying with the source image) — the case's "fixed
    size" does not hold for every tile, only the first (QatarEnergy) is
    close to 138 wide (136.59, not exactly 138). The **opacity half of the
    expected result DOES hold**: `img.qc-sp-logo` computes `opacity: 0.6` in
    its default/unhovered state, an exact match.
  - TC 136220 (continuous scroll, no visible pause): before/after real
    `getBoundingClientRect().x` sample of the first `.qc-sp-logos` strip,
    600ms apart, at the framework's default 1920x1080 viewport — consistently
    non-zero across 3 repeated live measurements (-10.10, -10.12, -9.40),
    confirming genuine continuous motion (same before/after-sample technique
    already used by home_community_partners_page.py's
    marquee_scroll_delta_x() — there is no discrete element STATE to
    `wait_for()` on a continuously-animating CSS transform).
  - TC 136221 (AR heading/subtitle + RTL mirror): CONFIRMED LIVE (AR,
    https://qcdev.ihorizons.com/ar/home) — `<html dir="rtl">`, section
    `direction: rtl`, heading text is the real Arabic string
    "شركاء استراتيجيون", subtitle "تحظى غرفة قطر بثقة مؤسسات رائدة في مختلف
    القطاعات الحيوية", both in the same Cairo/#1D1D1B (heading) /
    rgb(124,123,123)=#7C7B7B (subtitle) typography as EN. However: (1)
    `text-align` computes to **"center"** for both heading and subtitle in
    AR, not the case's stated "right-aligned"; (2) the partner-logo row's
    left-to-right scroll DIRECTION is measured **negative-x (leftward) in
    BOTH EN and AR** (EN delta -7.71, AR delta -8.67, same sign) — it is
    NOT mirrored to the opposite (RTL-appropriate) direction, same finding
    already logged for home_community_partners_page.py's TC 135810.
  - TC 136222 (EN alt text): the live qcdev instance's first configured
    partner is "QatarEnergy" (`img[alt="QatarEnergy logo"]`), not "Qatar
    Foundation" — no partner named "Qatar Foundation" exists on this
    instance at all. Scripted per the case's literal stated exact value;
    will fail honestly (wrong company name), not a framework defect.
  - TC 136223 (AR alt text): the case's own expected result gives no
    concrete AR string to compare against ("reads exactly the AR alt text"
    — unlike TC 136222's concrete EN value). Per this project's established
    convention for a case that names a category without a literal value
    (home_community_partners_page.py's TC 135806 AR-heading case), the
    concrete AR string asserted here is the CLI-extraction-CONFIRMED live
    value for the same first partner: `alt="شعار قطر للطاقة"` ("Qatar
    Energy logo" in Arabic) — a real, observed value, never invented.
  - TC 136224 (dark-mode gradient + inverted heading color): toggled via
    AccessibilityToolsComponent.switch_to_dark_mode() (the same global
    Dark Mode switch home_podcast_page.py's TC 133951 already uses). Live
    computes `backgroundImage: "none"`, a **plain solid**
    `rgb(29, 29, 27)` background — NOT the case's stated
    `linear-gradient(135deg, #1D1D1B 0%, #343432 100%)` (same "no gradient
    at all" finding as TC 136217's light-mode counterpart). The **heading
    color half of the expected result DOES hold**: heading color computes
    `rgb(255, 255, 255)` = #FFFFFF exactly in dark mode, an exact match.
    Section width is unchanged between light/dark (dark mode is a
    pure color/style change — confirmed live, matches
    accessibility_tools_component.py's own dark-mode finding that it never
    perturbs layout).
  - TC 136225/136226/136227 (desktop/tablet/mobile viewport rendering):
    CONFIRMED LIVE at all 3 viewports — heading, subtitle, and marquee boxes
    stack top-to-bottom with real vertical gaps between them (no overlap) at
    1920x1080, 768x1024, and 375x812, and
    `document.documentElement.scrollWidth == clientWidth` (no horizontal
    overflow) at every one. At 375x812 the marquee's own animation
    `animationPlayState` was observed **flaky** across repeated live runs
    (sometimes "running" with real motion, sometimes a same-poll 0.0 delta)
    — not reliable enough to assert a non-zero scroll delta at the mobile
    viewport specifically, so TC 136227 asserts the case's own literal
    wording (no horizontal overflow, no text truncation) rather than
    re-asserting motion (already covered, at the stable desktop viewport,
    by TC 136220).
  - TC 136228/136229 (light/dark theme rendering): same underlying findings
    as TC 136217/136224 respectively — light gradient absent (plain solid
    white), dark gradient absent (plain solid dark) but heading text does
    correctly invert to white with no light-background bleed-through
    (confirmed: dark-mode background is NOT rgb(255, 255, 255)).
  - TC 136231 (public visitor sees floating logos — Functional-High /
    Regression / UAT): CONFIRMED LIVE, genuine pass candidate — an
    unauthenticated visitor's Home Page load renders the section, heading
    text "Strategic Partners" in English, and the logo row shows real
    continuous motion (reuses the same stable-at-desktop marquee-delta
    technique as TC 136220).
"""

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent


class HomeStrategicPartnersPage(BasePage):
    # ── Locators — real, CLI/script-verified constants (see docstring) ──────
    HTML_ROOT = "html"
    SECTION = ".qc-home-strategic-partners"
    INNER = ".qc-sp-inner"
    HEADING = ".qc-sp-title"
    SUBTITLE = ".qc-sp-subtitle"
    MARQUEE = ".qc-sp-marquee"
    LOGOS_STRIP = ".qc-sp-logos"          # 2 matches live — always scope with .first for "the" strip
    LOGO_ITEM = ".qc-sp-logo-item"
    LOGO_TILE = "img.qc-sp-logo"          # the rendered visual tile (TC 136218's "logo tile")

    _TEXT_STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize,"
        "lineHeight: cs.lineHeight, color: cs.color, textAlign: cs.textAlign,"
        "direction: cs.direction"
        "}; }"
    )
    _BG_STYLE_JS = "el => { const cs = getComputedStyle(el); return {backgroundImage: cs.backgroundImage, backgroundColor: cs.backgroundColor}; }"

    def __init__(self, page):
        super().__init__(page)
        self.a11y = AccessibilityToolsComponent(page)

    def _text_style(self, locator) -> dict:
        loc = locator if hasattr(locator, "evaluate") else self.page.locator(locator).first
        return loc.evaluate(self._TEXT_STYLE_JS)

    def _bg_style(self, locator) -> dict:
        loc = locator if hasattr(locator, "evaluate") else self.page.locator(locator).first
        return loc.evaluate(self._BG_STYLE_JS)

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeStrategicPartnersPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeStrategicPartnersPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomeStrategicPartnersPage":
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

    def is_subtitle_visible(self) -> bool:
        return self.is_visible(self.SUBTITLE)

    def is_marquee_visible(self) -> bool:
        return self.is_visible(self.MARQUEE)

    # ── Heading ──────────────────────────────────────────────────────────
    def heading_text(self) -> str:
        return self.text(self.HEADING)

    def heading_style(self) -> dict:
        return self._text_style(self.HEADING)

    def heading_box(self) -> dict:
        return self.page.locator(self.HEADING).bounding_box()

    # ── Subtitle ─────────────────────────────────────────────────────────
    def subtitle_text(self) -> str:
        return self.text(self.SUBTITLE)

    def subtitle_style(self) -> dict:
        return self._text_style(self.SUBTITLE)

    def subtitle_box(self) -> dict:
        return self.page.locator(self.SUBTITLE).bounding_box()

    # ── Section background (TC 136217, 136224, 136228, 136229) ──────────
    def section_background_style(self) -> dict:
        return self._bg_style(self.SECTION)

    def section_box(self) -> dict:
        return self.page.locator(self.SECTION).bounding_box()

    # ── Global dark-mode toggle (composes AccessibilityToolsComponent) ───
    def enable_dark_mode(self) -> "HomeStrategicPartnersPage":
        self.a11y.click_accessibility_button()
        self.a11y.switch_to_dark_mode()
        return self

    # ── Partner logo row (first strip — see docstring's duplication note) ─
    def _first_strip_items(self):
        return self.page.locator(self.LOGOS_STRIP).first.locator(self.LOGO_ITEM)

    def partner_logo_alt_texts(self) -> list:
        """Raw `img[alt]` values, in DOM/visual order, from the first
        `.qc-sp-logos` strip (6 nodes live — see docstring; NOT deduplicated,
        matching home_community_partners_page.py's equivalent method)."""
        items = self._first_strip_items()
        return [
            items.nth(i).locator(self.LOGO_TILE).get_attribute("alt")
            for i in range(items.count())
        ]

    def first_partner_alt_text(self) -> str:
        alts = self.partner_logo_alt_texts()
        return alts[0] if alts else None

    def partner_logo_srcs(self) -> list:
        """Raw `img[src]` values, in DOM/visual order, from the first strip —
        language-independent identity, used to compare left-to-right ORDER
        across EN/AR (TC 136221) without the alt text's own translation
        getting in the way."""
        items = self._first_strip_items()
        return [
            items.nth(i).locator(self.LOGO_TILE).get_attribute("src")
            for i in range(items.count())
        ]

    def unique_partner_identifiers(self) -> list:
        seen, ordered = set(), []
        for src in self.partner_logo_srcs():
            if src not in seen:
                seen.add(src)
                ordered.append(src)
        return ordered

    def unique_partner_count(self) -> int:
        return len(self.unique_partner_identifiers())

    def rendered_logo_count(self) -> int:
        return len(self.partner_logo_alt_texts())

    # ── Logo tile size / opacity (TC 136218) ─────────────────────────────
    def first_logo_tile_box(self) -> dict:
        return self.page.locator(self.LOGO_TILE).first.bounding_box()

    def first_logo_tile_opacity(self) -> float:
        opacity = self.page.locator(self.LOGO_TILE).first.evaluate("el => getComputedStyle(el).opacity")
        return float(opacity)

    # ── Marquee scroll direction / motion (TC 136220, 136221, 136231) ────
    def _logos_strip_x(self) -> float:
        box = self.page.locator(self.LOGOS_STRIP).first.bounding_box()
        return box["x"] if box else None

    def marquee_scroll_delta_x(self, sample_ms: int = 600) -> float:
        """Real, timed before/after sample of the animated strip's own x
        position — same before/after-transition technique already used by
        home_community_partners_page.py / home_social_icons_page.py; there is
        no discrete element STATE to wait_for() on a continuously-animating
        CSS transform, so a short, explicit wait_for_timeout is the honest
        way to observe real motion (never a time.sleep())."""
        x0 = self._logos_strip_x()
        self.page.wait_for_timeout(sample_ms)
        x1 = self._logos_strip_x()
        if x0 is None or x1 is None:
            return None
        return x1 - x0

    # ── Responsive / layout (TC 136225, 136226, 136227) ──────────────────
    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def marquee_box(self) -> dict:
        return self.page.locator(self.MARQUEE).bounding_box()

    def heading_and_subtitle_and_marquee_do_not_overlap(self) -> bool:
        """True if the heading, subtitle, and marquee boxes stack top-to-
        bottom with no vertical overlap between consecutive elements — the
        concrete, geometry-based stand-in for "visible without overlap or
        clipping" (TC 136225/136226)."""
        boxes = [self.heading_box(), self.subtitle_box(), self.marquee_box()]
        if any(b is None for b in boxes):
            return False
        for prev, nxt in zip(boxes, boxes[1:]):
            if nxt["y"] < (prev["y"] + prev["height"]):
                return False
        return True

    def has_text_truncation(self, locator: str) -> bool:
        """True if the element's rendered content is wider than its own box
        (a real CSS truncation/ellipsis condition), used for TC 136227's
        "no unintended text truncation" on the narrow mobile viewport."""
        return self.page.locator(locator).evaluate("el => el.scrollWidth > el.clientWidth + 1")

"""
web/pages/vision_mission_objectives/vmo_page.py — VmoPage.

Public-frontend Page Object for PBI 129395 (QC-ABOUT-004 — Vision, Mission,
Objectives), `/web/qatar-chamber/about-us/vision-mission-objectives`.

Locators extracted CLI-first via `tools/extract_locators.py` for the page's
interactive chrome (nav links, footer, subscribe form) — none of that is
this page's subject matter. The page's OWN subject matter (hero, breadcrumb,
intro, and the three Vision/Mission/Objectives section cards) is plain
non-interactive markup (headings, spans, figures) that the CLI extractor
deliberately does NOT harvest (it only walks
a,button,input,select,textarea,[role],[data-testid],[data-test],[aria-label],
[contenteditable] — see org_structure_page.py's docstring for the same,
earlier precedent on this project). Those real class names and structure
were confirmed by a scoped Playwright script (`page.evaluate`, CSS-selector
probe restricted to `[class*=vmo]` etc.) run directly against the live page
at the framework's default 1920x1080 viewport on 2026-08-25 — a shell
script, not the Playwright MCP; the MCP fallback was not needed for this
page. Confirmed structure:

    SECTION.qc-vmo
      DIV.qc-vmo-hero
        DIV.qc-vmo-hero-media / DIV.qc-vmo-hero-overlay
        DIV.qc-vmo-hero-inner
          H1.qc-vmo-hero-title            -> "Vision · Mission · Objectives"
          NAV.qc-vmo-breadcrumb
            A.qc-vmo-crumb.qc-vmo-crumb-home        -> "Home"
            SPAN.qc-vmo-crumb.qc-vmo-crumb-current  -> "About Us"
      DIV.qc-vmo-content
        DIV.qc-vmo-intro
          H2.qc-vmo-intro-heading         -> "Who We Are"
          P.qc-vmo-intro-desc
        DIV.qc-vmo-sections
          ARTICLE.qc-vmo-section.qc-vmo-section--img-end   (Vision, 01)
          ARTICLE.qc-vmo-section.qc-vmo-section--img-start (Mission, 02)
          ARTICLE.qc-vmo-section.qc-vmo-section--img-end   (Objectives, 03)
            DIV.qc-vmo-sec-head
              SPAN.qc-vmo-sec-label     (Vision / Mission / Objectives)
              SPAN.qc-vmo-sec-divider
              SPAN.qc-vmo-sec-num       (01 / 02 / 03)
            DIV.qc-vmo-sec-body
              DIV.qc-vmo-sec-text
                H3.qc-vmo-sec-headline  (uppercase, e.g. "INTERNATIONAL LEADERSHIP")
                P.qc-vmo-sec-sub
                DIV.qc-vmo-sec-rich     (a <ul><li> list for Vision/Objectives,
                                          a bare paragraph for Mission)
              FIGURE.qc-vmo-sec-media
                IMG.qc-vmo-sec-img      (border-radius: 12px)
                FIGCAPTION.qc-vmo-sec-badge   (position:absolute badge overlay)

`--img-end` = image renders on the trailing (right, in LTR) side of the
text column; `--img-start` = image renders on the leading (left, in LTR)
side. Confirmed live mapping: Vision=img-end (image right), Mission=img-start
(image left), Objectives=img-end (image right) — matches the BRD/case's
described alternation exactly (per-section modifier class, not a fixed
odd/even rule, so this stays correct even if a section is reordered/
deactivated).

Real content confirmed live (English):
    Vision      / 01 / "INTERNATIONAL LEADERSHIP"      / bulleted list (3 items)
    Mission     / 02 / "REPRESENT. SUPPORT. ELEVATE."  / single paragraph
    Objectives  / 03 / "FIVE PILLARS OF GROWTH"        / bulleted list (5 items)

Design tokens confirmed live via computed style (see automation-standards.md
Figma-token precedent, org_structure_page.py `node_computed_style`):
    Hero title      : Cairo 700 30px / lineHeight ~38px / color rgb(255,255,255)
    Section label   : Cairo 400 24px / color rgb(124,123,123)
    Section number  : Cairo 700 40px / color rgb(216,211,206)
    Section headline: Cairo 700 26px / text-transform uppercase
    Section image   : border-radius 12px
    Section badge   : position absolute (overlay on the image)
"""

from config.settings import web_url
from core.web.base_page import BasePage

VMO_PATH = "/web/qatar-chamber/about-us/vision-mission-objectives"

SECTION_ORDER = ["Vision", "Mission", "Objectives"]


class VmoPage(BasePage):
    # ---- Hero -------------------------------------------------------------
    HERO = ".qc-vmo-hero"
    HERO_TITLE = ".qc-vmo-hero-title"
    HERO_MEDIA = ".qc-vmo-hero-media"

    # ---- Breadcrumb ---------------------------------------------------------
    BREADCRUMB = ".qc-vmo-breadcrumb"
    BREADCRUMB_HOME = ".qc-vmo-crumb-home"
    BREADCRUMB_CURRENT = ".qc-vmo-crumb-current"

    # ---- Intro --------------------------------------------------------------
    INTRO = ".qc-vmo-intro"
    INTRO_HEADING = ".qc-vmo-intro-heading"
    INTRO_DESC = ".qc-vmo-intro-desc"

    # ---- Sections -------------------------------------------------------------
    SECTIONS_CONTAINER = ".qc-vmo-sections"
    SECTION = ".qc-vmo-section"

    # ---- Navigation -----------------------------------------------------
    def open_vmo(self, locale: str = "en") -> "VmoPage":
        self.open(web_url(VMO_PATH, locale=locale))
        return self

    def open_broken_url(self) -> "VmoPage":
        """Deliberately-invalid child path, for the standard-error-page case
        — mirrors OrgStructurePage.open_broken_url's precedent (no
        environment toggle exists to make the real page's content
        unavailable on demand)."""
        self.open(web_url(VMO_PATH + "-unavailable-content-check"))
        return self

    # ---- Hero / breadcrumb queries ---------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.BREADCRUMB)

    def breadcrumb_home_text(self) -> str:
        return self.text(self.BREADCRUMB_HOME)

    def breadcrumb_current_text(self) -> str:
        return self.text(self.BREADCRUMB_CURRENT)

    # ---- Intro queries ------------------------------------------------------
    def is_intro_visible(self) -> bool:
        return self.is_visible(self.INTRO)

    def intro_heading_text(self) -> str:
        return self.text(self.INTRO_HEADING)

    def intro_desc_text(self) -> str:
        return self.text(self.INTRO_DESC)

    # ---- Section locators / queries ---------------------------------------
    def _section(self, label: str):
        """The `.qc-vmo-section` article whose label span's text equals
        `label` exactly (Vision / Mission / Objectives)."""
        return self.page.locator(
            f'.qc-vmo-section:has(.qc-vmo-sec-label:text-is("{label}"))'
        ).first

    def section_locator(self, label: str) -> str:
        return f'.qc-vmo-section:has(.qc-vmo-sec-label:text-is("{label}"))'

    def section_locator_by_index(self, index: int) -> str:
        """Locale-agnostic section locator by DOM position (Vision=0,
        Mission=1, Objectives=2) — mirrors BoardOfDirectorsPage's
        `click_first_featured_profile_link`/`>> nth=0` precedent
        (board_of_directors_page.py ~189-199) for the same reason: filtering
        on an English label string (`section_locator("Vision")`) never
        matches on the Arabic-rendered page, so any RTL-locale check needs
        an index-based locator instead. Confirmed live via a DOM probe
        against /ar/web/qatar-chamber/about-us/vision-mission-objectives
        (2026-08-25): section order and the `--img-start`/`--img-end`
        modifier classes are unchanged between EN and AR (only the visible
        label text is translated), so index 0 is still Vision in AR.

        Standalone use (as its own locator string, e.g. with
        `page.locator(...)`, `.get_attribute()`) — for chaining a further
        descendant selector onto it (e.g. `f'{x} .qc-vmo-sec-img'`), use
        `section_chain_locator_by_index()` instead: Playwright's `nth=`
        pseudo-class must be followed by another `>>` combinator before a
        plain CSS selector, not just whitespace."""
        return f"{self.SECTION} >> nth={index}"

    def section_chain_locator_by_index(self, index: int) -> str:
        """Same section as `section_locator_by_index()`, pre-suffixed with
        `>>` so a descendant CSS selector can be appended directly
        (`f'{vmo.section_chain_locator_by_index(0)} .qc-vmo-sec-img'`) —
        mirrors board_of_directors_page.py's
        `f'{self.SECTION_FEATURED} >> nth=0 >> .qc-bod-name a'` chaining."""
        return f"{self.SECTION} >> nth={index} >>"

    def section_image_side_by_index(self, index: int) -> str:
        """Same as section_image_side(), but resolved by DOM position
        instead of an English label — see section_locator_by_index()."""
        classes = self.page.locator(self.section_locator_by_index(index)).get_attribute("class") or ""
        if "qc-vmo-section--img-start" in classes:
            return "start"
        if "qc-vmo-section--img-end" in classes:
            return "end"
        return "unknown"

    def is_section_visible(self, label: str) -> bool:
        try:
            return self._section(label).is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's contract
            return False

    def section_count(self) -> int:
        return self.page.locator(self.SECTION).count()

    def visible_section_labels_in_order(self) -> list:
        """All rendered section labels, top-to-bottom DOM order — used to
        assert default ordering (Vision/Mission/Objectives) and renumbering
        after a section is deactivated/reactivated."""
        return self.page.locator(".qc-vmo-sec-label").all_inner_texts()

    def section_number(self, label: str) -> str:
        return self._section(label).locator(".qc-vmo-sec-num").inner_text().strip()

    def section_headline(self, label: str) -> str:
        return self._section(label).locator(".qc-vmo-sec-headline").inner_text()

    def section_subheading(self, label: str) -> str:
        return self._section(label).locator(".qc-vmo-sec-sub").inner_text()

    def section_body_is_bulleted(self, label: str) -> bool:
        return self._section(label).locator(".qc-vmo-sec-rich ul").count() > 0

    def section_bullet_texts(self, label: str) -> list:
        return self._section(label).locator(".qc-vmo-sec-rich li").all_inner_texts()

    def section_paragraph_text(self, label: str) -> str:
        return self._section(label).locator(".qc-vmo-sec-rich").inner_text()

    def section_image_src(self, label: str) -> str:
        return self._section(label).locator(".qc-vmo-sec-img").get_attribute("src")

    def is_section_badge_visible(self, label: str) -> bool:
        return self._section(label).locator(".qc-vmo-sec-badge").count() > 0

    def section_image_side(self, label: str) -> str:
        """'start' (leading/left in LTR) or 'end' (trailing/right in LTR),
        read off the section's own `--img-start` / `--img-end` modifier
        class — never assumed from position index."""
        classes = self._section(label).get_attribute("class") or ""
        if "qc-vmo-section--img-start" in classes:
            return "start"
        if "qc-vmo-section--img-end" in classes:
            return "end"
        return "unknown"

    def section_dom_order_index(self, label: str, container_html: list = None) -> int:
        labels = self.visible_section_labels_in_order()
        return labels.index(label) if label in labels else -1

    # ---- Style probe (Figma-token verification) ----------------------------
    def computed_style(self, locator: str, props: list) -> dict:
        """Generic Figma-token probe, mirrors OrgStructurePage's precedent."""
        handle = self.page.locator(locator).first
        return handle.evaluate(
            """
            (el, props) => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = s[p];
                return out;
            }
            """,
            props,
        )

    def section_style(self, label: str, sub_selector: str, props: list) -> dict:
        loc = f'{self.section_locator(label)} {sub_selector}'
        return self.computed_style(loc, props)

"""
web/pages/about_qatar_chamber/about_qatar_chamber_page.py — AboutQatarChamberPage.

PBI 129392 / QC-ABOUT 001 "About Qatar Chamber" — first automation pass for
this page (no prior coverage in this project; folder created per
active/standards.md's page-per-folder convention, mirroring the sibling
`home_about_summary` naming style but WITHOUT the `home_` prefix since this is
a standalone About-Us-family page, not a Home-page section).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/web/qatar-chamber/about-us --viewport 1920x1080
    -> [role] uniq=1  get_by_role("link", name="Visit Qatar Chamber")
    -> [id]   uniq=1  #main-content -> "About Qatar Chamber Home About Us The Voice of Qatar's Priva..."

Confirms `/web/qatar-chamber/about-us` (reached from the Home page's own
"About Us" summary section Read More CTA, already named on
home_about_summary_page.py) IS the live "About Qatar Chamber" page the whole
case batch describes — not a separate, not-yet-built page. The extractor's
role/id harvest doesn't expose the section's own DOM/CSS structure (no
data-testid, most elements are plain div/h2/h3/ul/ol/img with no role), so —
same documented "ambiguous/unreachable via role" condition already resolved
in every sibling Home-section Page Object — the real structure, computed
styles, and geometry were read via one additional, disclosed, scoped
Playwright script (still CLI/shell, never the Playwright MCP), reusing
BasePage's own license-gate/overlay guard sequence.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/web/qatar-chamber/about-us):

    section.qc-about-page[dir]                                (PAGE)
      div.qc-ap-hero                                            (HERO)
        div.qc-ap-hero-media[style=background-image]            (HERO_MEDIA)
        div.qc-ap-hero-overlay                                   (HERO_OVERLAY — linear-gradient maroon/gold)
        div.qc-ap-hero-inner
          h1.qc-ap-hero-title[data-qc-ap-title]                  (HERO_TITLE — "About Qatar Chamber")
          nav.qc-ap-breadcrumb[data-qc-ap-breadcrumb]             (BREADCRUMB)
            a.qc-ap-crumb-home[data-qc-ap-home]                    (CRUMB_HOME, href="/web/qatar-chamber")
              svg.qc-ap-crumb-home-icon                             (CRUMB_HOME_ICON)
              span[data-qc-ap-home-label]                           (CRUMB_HOME_LABEL — "Home")
            svg.qc-ap-crumb-sep                                    (CRUMB_SEP — chevron, scaleX(-1) under RTL)
            span.qc-ap-crumb-current[data-qc-ap-current]           (CRUMB_CURRENT — "About Us", a <span>, NOT a link)
      div.qc-ap-content                                         (CONTENT)
        div.qc-ap-row                                            (ROW — CSS grid, 1fr 1fr >=992px, 1 col <992px)
          div.qc-ap-intro[data-qc-ap-intro]                        (INTRO — first heading + first paragraph only)
            h2 (or h1/h3, per authored content)                      (INTRO_HEADING)
            p                                                        (INTRO_PARAGRAPH, may contain inline <a>)
          div.qc-ap-media[data-qc-ap-media]                        (MEDIA)
            div.qc-ap-media-panel[aria-hidden]                       (MEDIA_PANEL — pink offset rectangle, decorative)
            figure.qc-ap-media-fig
              img.qc-ap-media-img[data-qc-ap-img]                     (MEDIA_IMG)
        div.qc-ap-body[data-qc-ap-body]                          (BODY — everything AFTER the first paragraph)
          h1/h2/h3/h4                                               (BODY_HEADINGS — pink 56x56 ::before icon chip)
          ul / ol                                                   (BODY_LISTS)
          a                                                         (BODY_LINKS — inline prose links)
        div.qc-ap-cta[data-qc-ap-cta]                             (CTA — optional CMS-configurable hyperlink)
          a.qc-ap-cta-link[data-qc-ap-cta-link]                      (CTA_LINK)
            span.qc-ap-cta-label[data-qc-ap-cta-label]                 (CTA_LABEL)
        p.qc-ap-status[data-qc-ap-status][hidden]                (STATUS — "Loading…", hidden once rendered)

Rendering is entirely client-side (a `<script type="module">` fetches the
single published `aboutqatarchamberpages` Object entry and the shared
`aboutherobanners` entry, then populates the above skeleton) — confirmed live
by reading the page's own inline script. Only a `pageStatus === 'published'`
entry renders; otherwise `root.style.display = 'none'` (AC-7/AC-14) — the
concrete, live mechanism behind cases 134690/134691's "unpublished/draft
content does not appear" expectation, blocked from END-TO-END verification
this run only because reaching CMS to actually flip that status requires
TEST_USER/TEST_PASSWORD, still blank in .env (see the sibling
about_qatar_chamber_admin_page.py / test_about_qatar_chamber_control_panel.py
for the gated CMS half of every Control_Panel-tagged case in this batch).

Real, CLI-verified findings from this extraction pass (reported honestly,
never silently adjusted to match a case's stated expectation):

  - BREADCRUMB IS ONLY 2 ITEMS, not 3. The script hardcodes
    `homeLabelEl.textContent = t('Home', 'الرئيسية')` and
    `currentEl.textContent = t('About Us', 'من نحن')` — there is no third
    "About Qatar Chamber" crumb. `CRUMB_CURRENT` is a plain `<span>`
    (`qc-ap-crumb-current`), not a link — it is NOT clickable. This
    contradicts every case that describes a 3-level
    "Home > About Us > About Qatar Chamber" trail (134670, 134677, 134678,
    134689, 134699, 134744, 134745) and 134745's specific claim that the
    breadcrumb LEAF equals the hero page title — live, the leaf is always
    literally "About Us"/"من نحن", never the page's own title
    ("About Qatar Chamber"/"غرفة قطر"). Scripted per each case's exact stated
    wording regardless; the mismatch is real and will fail honestly.
  - CRUMB_HOME's href is `/web/qatar-chamber`, confirmed live (via
    `page.title()`) to be the SITE HOME PAGE ("Home - Qatar Chamber"), not a
    separate "About Us" landing page. 134699 ("click the 'About Us' entry in
    the breadcrumb -> navigates to the About Us page") cannot be satisfied as
    stated: the only clickable crumb is "Home" (goes to the Home page); the
    "About Us" crumb itself is the non-link CRUMB_CURRENT span. Scripted
    against the literal case wording (click the item reading "About Us")
    honestly, not substituted with the Home link.
  - Main-menu mega-menu reality check (134689): the header's live "About us"
    top-level nav item (`li.qc-has-children:has-text("About us") .qc-nav-sub`,
    HeaderComponent's `NAV_ITEM_WITH_SUBMENU`) lists exactly 6 links —
    Chairman's Message, General Manager's Message, Vision/Mission &
    Objectives, Chamber's Law, Board of Directors & General Manager,
    Organizational Structure — and contains NO "About Qatar Chamber" entry at
    all (confirmed live via the submenu's real `outerHTML`). 134689's own
    step 2 ("the About Us submenu expands and lists 'About Qatar Chamber'")
    does not hold on the live site. `submenu_about_qatar_chamber_link()`
    below is a real, resolvable locator (role=link, name="About Qatar
    Chamber", scoped to the submenu) so the test fails honestly (element not
    found) rather than erroring on a guessed selector.
  - Hero geometry: `.qc-ap-hero` renders 1920x118px live (`min-block-size:
    60px` + `padding-block: 2.5rem` on `.qc-ap-hero-inner`), NOT the 140px
    134669 states — a real, small mismatch. Title/breadcrumb typography DOES
    match exactly: title Cairo 30px/700/38.1px line-height/rgb(255,255,255);
    breadcrumb items Cairo 14px/400/21px line-height/rgb(255,255,255); crumb
    gap computes to the case's stated 6px.
  - Two-column intro row (134671): confirmed live at 1920 desktop —
    `.qc-ap-row` box 1216px wide (not exactly 1320px — `.qc-ap-content`'s own
    max-width IS `var(--container-max-xl, 1320px)` but its 1rem inline
    padding narrows the row itself to 1216px), split into two 596px columns
    (not exactly 648px) with a 24px gap (MATCHES). `.qc-ap-intro` (rich text)
    renders BEFORE `.qc-ap-media` (Content Image) in DOM order and, at LTR,
    in visual x-position too (intro x=352 < media x=972) — matches 134671
    and 134677's "text column before image column" expectation. Rounding is
    honestly reported, not silently corrected.
  - Content Image (134672): renders 548x302px live at 1920 desktop, NOT
    600x330 as stated — `.qc-ap-media-img` uses `inline-size: 92%` of a
    596px column, not a fixed 600px box, so its exact rendered size is
    column-width-dependent, not a fixed token. `border-radius: 16px` DOES
    match. The decorative backing panel (`.qc-ap-media-panel`) renders
    322x332px (not 325x343), `border-radius: 20px` (MATCHES), background
    `rgb(244, 231, 234)` = #F4E7EA (MATCHES the case's stated
    rgb(244,231,234) exactly).
  - Primary heading/paragraph typography (134673): EXACT match live —
    `.qc-ap-intro h2` Cairo 30px/700/38.1px line-height/rgb(145,23,49); `p`
    Cairo 18px/400/28.08px line-height/rgb(52,52,50); heading's own
    `margin-block-end` computes to 12px (MATCHES the case's stated spacing).
  - Section header icon (134674): the "icon button" is a PURE CSS `::before`
    pseudo-element on `.qc-ap-body h2/h3` (`background: var(--_ap-icon-bg)
    center / 22px 22px no-repeat`, `block-size/inline-size: 56px`,
    `border-radius: 50%`) — NOT a real, focusable `<button>` element; there is
    no click target here. Computed live: 56x56px, `border-radius: 50%`,
    background `rgb(244, 231, 234)` (MATCHES the case's stated badge fill);
    heading text itself Cairo 20px/700/rgb(145,23,49) (MATCHES exactly); the
    heading's own `gap: 20px` flex property (MATCHES the case's stated
    "20px apart"). Read via `getComputedStyle(el, '::before')` —
    `body_heading_icon_style()` below — since Playwright cannot locate a
    pseudo-element as its own element.
  - Rich text body (134675, Control_Panel-hybrid): the ALREADY-PUBLISHED live
    content (not authored this run — CMS is blocked, see module docstring)
    already contains real structure matching the case's shape: 2
    `<h3>`s ("The Chamber's competences", "Chamber Constituents" — no
    trailing colon, unlike the case's "Chamber Constituents:"), 2 `<ul>`s + 1
    `<ol>` inside the first section (not "one 3-item bullet + one 3-item
    numbered sub-list" exactly — the live content has MORE list structure
    than the case describes) and 1 more `<ul>` in the second section, plus
    one inline link ("Law No (4)" -> https://www.qatarchamber.com,
    target=_blank) inside the INTRO paragraph. Verified generically (list/
    heading/link PRESENCE and the concrete live inline-link href), not the
    literal "3-item" counts the case's own (blocked) CMS-authoring step would
    have produced.
  - Content Image alt text (134676, Control_Panel-hybrid): live alt =
    "Qatar Chamber of Commerce & Industry building" (`item.contentImageAltText
    || item.pageTitle`, confirmed via the page's own inline script), not the
    case's "Qatar Chamber headquarters building" (that string was never
    authored this run — CMS blocked). Verified generically (alt attribute is
    non-empty and exposed) rather than the literal blocked string.
  - RTL mirroring (134678): confirmed LIVE the opposite of what the case
    states. AR: `.qc-ap-intro` x=972 (RIGHT half), `.qc-ap-media` x=352 (LEFT
    half) — i.e. under `dir="rtl"` the RICH TEXT column sits on the right
    (read FIRST) and the CONTENT IMAGE sits on the left (read SECOND). The
    case states the Content Image should render "before (to the right of)"
    the rich text — live is the reverse. `.qc-about-page` does carry
    `dir="rtl"`; AR body headings ("اختصاصات الغرفة", "أجهزة الغرفة") DO
    render right-aligned (`text-align: start` under `direction: rtl`); the
    breadcrumb separator DOES mirror (`transform: matrix(-1,0,0,1,0,0)` ==
    `scaleX(-1)`). A genuine partial mismatch, reported honestly.
  - Section order (134679, Control_Panel-hybrid): the ALREADY-PUBLISHED
    content happens to already render in the case's exact stated order —
    "The Voice of Qatar's Private Sector" (intro heading) → "The Chamber's
    competences" → "Chamber Constituents" — a genuine, verifiable PASS
    candidate even without performing the CMS-authoring step ourselves.
  - Desktop/tablet/mobile (134680/134681/134682): confirmed live —
    1920 desktop: `.qc-ap-row` renders as two side-by-side 596px columns, no
    horizontal overflow. 768 tablet: the SAME `max-width: 991.98px` media
    query that drives the mobile layout ALSO applies at 768px — `.qc-ap-row`
    collapses to ONE column (not two side-by-side) at this width; no
    horizontal overflow; `.qc-ap-media-img` renders `inline-size: 100%`.
    390 mobile: confirmed `.qc-ap-intro { order: 1 }` / `.qc-ap-media {
    order: 2 }` (text above image, matches the case), image `inline-size:
    100%`, no horizontal overflow.
  - 404 / unavailable page (134742): confirmed live —
    `https://.../web/qatar-chamber/does-not-exist-129392` returns HTTP 404,
    renders a real "Coming Soon" branded error page (title "Coming Soon -
    Qatar Chamber - Liferay DXP"), with the SAME site header AND footer
    intact, no stack trace/raw exception text. A genuine, observed PASS
    candidate for the site's standard-error-page behaviour — used here as the
    concrete stand-in for "page unavailable" since actually unpublishing the
    real page requires the same blocked CMS access.
  - Dark mode (134748/134749/134750/134751): confirmed live via
    AccessibilityToolsComponent's own `DARK_MODE_SWITCH` — clicking it sets
    `<html data-theme="dark">` (this page's own CSS keys off exactly that
    attribute, `html[data-theme='dark'] .qc-about-page`), flips
    `.qc-about-page`'s background to `rgb(29, 29, 27)` (#1D1D1B), and
    re-points every custom property (heading color -> #E08A9C, icon bg ->
    #360711 with a brightened stroke) per the page's own embedded CSS —
    confirmed a real, live, working mechanism, not assumed.
"""

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.header_component import HeaderComponent
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

ABOUT_PATH = "/web/qatar-chamber/about-us"
HOME_URL_PATH = "/web/qatar-chamber"
NOT_FOUND_PATH = "/web/qatar-chamber/does-not-exist-129392"


class AboutQatarChamberPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    PAGE = "section.qc-about-page"
    HTML_ROOT = "html"

    HERO = ".qc-ap-hero"
    HERO_MEDIA = ".qc-ap-hero-media"
    HERO_OVERLAY = ".qc-ap-hero-overlay"
    HERO_INNER = ".qc-ap-hero-inner"
    HERO_TITLE = ".qc-ap-hero-title"

    BREADCRUMB = ".qc-ap-breadcrumb"
    CRUMB_HOME = "[data-qc-ap-home]"
    CRUMB_HOME_ICON = ".qc-ap-crumb-home-icon"
    CRUMB_HOME_LABEL = "[data-qc-ap-home-label]"
    CRUMB_SEP = ".qc-ap-crumb-sep"
    CRUMB_CURRENT = "[data-qc-ap-current]"

    CONTENT = ".qc-ap-content"
    ROW = ".qc-ap-row"
    INTRO = ".qc-ap-intro"
    INTRO_HEADING = ".qc-ap-intro > :is(h1, h2, h3, h4)"
    INTRO_PARAGRAPH = ".qc-ap-intro p"
    INTRO_LINK = ".qc-ap-intro a"

    MEDIA = ".qc-ap-media"
    MEDIA_PANEL = ".qc-ap-media-panel"
    MEDIA_FIG = ".qc-ap-media-fig"
    MEDIA_IMG = ".qc-ap-media-img"

    BODY = ".qc-ap-body"
    BODY_HEADINGS = ".qc-ap-body :is(h1, h2, h3, h4)"
    BODY_LISTS = ".qc-ap-body :is(ul, ol)"
    BODY_UL = ".qc-ap-body ul"
    BODY_OL = ".qc-ap-body ol"
    BODY_LINKS = ".qc-ap-body a"

    CTA = ".qc-ap-cta"
    CTA_LINK = ".qc-ap-cta-link"
    CTA_LABEL = ".qc-ap-cta-label"
    CTA_ARROW = ".qc-ap-cta-arrow"

    STATUS = ".qc-ap-status"

    # 134689 — real, resolvable locator for the case's claimed (but live
    # absent — see docstring) main-menu submenu entry.
    SUBMENU_ABOUT_QATAR_CHAMBER_LINK = (
        'header.qc-global-site-header li.qc-has-children:has-text("About us") '
        '.qc-nav-sub >> role=link[name="About Qatar Chamber"]'
    )
    ABOUT_US_NAV_ITEM = (
        'header.qc-global-site-header nav.qc-nav > ul.qc-nav-list > li > '
        'a.qc-nav-link:has-text("About us")'
    )

    FOOTER = "footer.qc-global-site-footer"

    _STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "fontFamily: cs.fontFamily, fontSize: cs.fontSize, fontWeight: cs.fontWeight,"
        "lineHeight: cs.lineHeight, color: cs.color, textAlign: cs.textAlign}; }"
    )

    def __init__(self, page):
        super().__init__(page)
        # Composed, not re-declared — HeaderComponent already owns the
        # language-switcher/nav-item locators (PBI 129363), and
        # AccessibilityToolsComponent already owns the Dark Mode toggle
        # locator (PBI 129364) — mirroring the same reuse pattern
        # LanguageSwitcherComponent/AccessibilityToolsComponent itself
        # already established for THIS project.
        self.header = HeaderComponent(page)
        self.a11y = AccessibilityToolsComponent(page)

    # ── Navigation ───────────────────────────────────────────────────────
    def open_en(self) -> "AboutQatarChamberPage":
        self.open(web_url(ABOUT_PATH))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_ar(self) -> "AboutQatarChamberPage":
        self.open(web_url(ABOUT_PATH, locale="ar"))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_not_found_path(self) -> int:
        """Navigates to a deliberately non-existent sibling path (134742) and
        returns the real HTTP status code the server answered with."""
        response = self.page.goto(web_url(NOT_FOUND_PATH))
        from core.web.license_gate import clear_license_gate
        from core.web.overlays import dismiss_overlays, MOUNT_GRACE_MS
        clear_license_gate(self.page, web_url(NOT_FOUND_PATH))
        dismiss_overlays(self.page, grace_ms=MOUNT_GRACE_MS)
        self.page.wait_for_load_state("networkidle")
        return response.status if response else 0

    def open_via_main_menu(self) -> "AboutQatarChamberPage":
        """134689: hovers/clicks the header's 'About us' nav item, then
        clicks the (claimed, live-absent — see docstring) submenu entry
        named 'About Qatar Chamber'."""
        self.click(self.ABOUT_US_NAV_ITEM)
        self.wait_for(self.SUBMENU_ABOUT_QATAR_CHAMBER_LINK, timeout=5000)
        self.click(self.SUBMENU_ABOUT_QATAR_CHAMBER_LINK)
        self.page.wait_for_load_state("networkidle")
        return self

    def is_submenu_about_qatar_chamber_link_visible(self) -> bool:
        self.click(self.ABOUT_US_NAV_ITEM)
        return self.is_visible(self.SUBMENU_ABOUT_QATAR_CHAMBER_LINK)

    def click_home_breadcrumb(self) -> "AboutQatarChamberPage":
        self.click(self.CRUMB_HOME)
        self.page.wait_for_load_state("networkidle")
        return self

    def current_url(self) -> str:
        return self.page.url

    def switch_language_via_switcher(self) -> "AboutQatarChamberPage":
        """134695/134696: switches language via the header's own language
        switcher (composed HeaderComponent, not a re-declared locator) and
        waits for the destination About Qatar Chamber page's own hero title
        to render."""
        self.header.switch_to_arabic()
        self.wait_for(self.HERO_TITLE)
        return self

    def switch_language_to_english_via_switcher(self) -> "AboutQatarChamberPage":
        """134696: AR -> EN switch-back, symmetric to switch_language_via_switcher()."""
        self.header.switch_to_english()
        self.wait_for(self.HERO_TITLE)
        return self

    # ── Generic helpers ───────────────────────────────────────────────────
    def _box(self, locator: str) -> dict | None:
        box = self.page.locator(locator).first.bounding_box()
        if not box:
            return None
        return {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]}

    def _style(self, locator: str) -> dict:
        return self.page.locator(locator).first.evaluate(self._STYLE_JS)

    def row_grid_template_columns(self) -> str:
        return self.page.locator(self.ROW).evaluate("el => getComputedStyle(el).gridTemplateColumns")

    def intro_css_order(self) -> int:
        return int(self.page.locator(self.INTRO).evaluate("el => getComputedStyle(el).order"))

    def media_css_order(self) -> int:
        return int(self.page.locator(self.MEDIA).evaluate("el => getComputedStyle(el).order"))

    def media_img_inline_size(self) -> str:
        return self.page.locator(self.MEDIA_IMG).evaluate("el => getComputedStyle(el).inlineSize")

    def page_body_text(self) -> str:
        return self.text("body")

    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def scroll_to_footer(self) -> "AboutQatarChamberPage":
        self.page.locator(self.FOOTER).scroll_into_view_if_needed()
        return self

    def is_footer_visible(self) -> bool:
        return self.is_visible(self.FOOTER)

    def html_text_contains(self, needle: str) -> bool:
        return needle in self.page.locator(self.PAGE).inner_text()

    # ── Hero (134669) ─────────────────────────────────────────────────────
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def hero_box(self) -> dict | None:
        return self._box(self.HERO)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_title_style(self) -> dict:
        return self._style(self.HERO_TITLE)

    def hero_overlay_background_image(self) -> str:
        return self.page.locator(self.HERO_OVERLAY).evaluate("el => getComputedStyle(el).backgroundImage")

    def hero_media_background_image(self) -> str:
        return self.page.locator(self.HERO_MEDIA).evaluate("el => getComputedStyle(el).backgroundImage")

    # ── Breadcrumb (134670, 134677, 134678, 134699, 134744, 134745) ───────
    def is_breadcrumb_home_icon_visible(self) -> bool:
        return self.is_visible(self.CRUMB_HOME_ICON)

    def breadcrumb_item_texts(self) -> list:
        """[home_label, current_label] — the breadcrumb renders exactly 2
        labelled items live (see docstring), not 3."""
        return [self.text(self.CRUMB_HOME_LABEL), self.text(self.CRUMB_CURRENT)]

    def breadcrumb_item_count(self) -> int:
        return len(self.breadcrumb_item_texts())

    def breadcrumb_current_is_link(self) -> bool:
        return self.page.locator(self.CRUMB_CURRENT).evaluate("el => el.tagName.toLowerCase()") == "a"

    def breadcrumb_gap(self) -> str:
        return self.page.locator(self.BREADCRUMB).evaluate("el => getComputedStyle(el).gap")

    def breadcrumb_crumb_style(self) -> dict:
        return self._style(self.CRUMB_CURRENT)

    def breadcrumb_sep_transform(self) -> str:
        return self.page.locator(self.CRUMB_SEP).first.evaluate("el => getComputedStyle(el).transform")

    def breadcrumb_home_href(self) -> str | None:
        return self.page.locator(self.CRUMB_HOME).get_attribute("href")

    # ── Two-column layout (134671, 134677, 134678) ────────────────────────
    def content_box(self) -> dict | None:
        return self._box(self.CONTENT)

    def content_row_box(self) -> dict | None:
        return self._box(self.ROW)

    def intro_box(self) -> dict | None:
        return self._box(self.INTRO)

    def media_box(self) -> dict | None:
        return self._box(self.MEDIA)

    def intro_renders_before_media(self) -> bool:
        """True if the rich-text column sits to the visual LEFT of the
        Content Image column (LTR expectation)."""
        intro = self.intro_box()
        media = self.media_box()
        if not (intro and media):
            return False
        return intro["x"] < media["x"]

    def media_renders_before_intro(self) -> bool:
        """True if the Content Image column sits to the visual RIGHT of the
        rich-text column (134678's stated RTL expectation)."""
        intro = self.intro_box()
        media = self.media_box()
        if not (intro and media):
            return False
        return media["x"] > intro["x"]

    # ── Content Image + decorative panel (134672) ─────────────────────────
    def media_img_box(self) -> dict | None:
        return self._box(self.MEDIA_IMG)

    def media_img_border_radius(self) -> str:
        return self.page.locator(self.MEDIA_IMG).evaluate("el => getComputedStyle(el).borderRadius")

    def media_img_alt(self) -> str | None:
        return self.page.locator(self.MEDIA_IMG).get_attribute("alt")

    def media_panel_box(self) -> dict | None:
        return self._box(self.MEDIA_PANEL)

    def media_panel_style(self) -> dict:
        return self.page.locator(self.MEDIA_PANEL).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {borderRadius: cs.borderRadius, backgroundColor: cs.backgroundColor}; }"
        )

    # ── Primary heading / paragraph typography (134673) ───────────────────
    def intro_heading_text(self) -> str:
        return self.text(self.INTRO_HEADING)

    def intro_heading_style(self) -> dict:
        return self._style(self.INTRO_HEADING)

    def intro_paragraph_style(self) -> dict:
        return self._style(self.INTRO_PARAGRAPH)

    def intro_heading_margin_bottom(self) -> str:
        return self.page.locator(self.INTRO_HEADING).evaluate("el => getComputedStyle(el).marginBottom")

    # ── Section header icon chip (134674, 134746) ──────────────────────────
    def body_heading_texts(self) -> list:
        headings = self.page.locator(self.BODY_HEADINGS)
        return [headings.nth(i).inner_text().strip() for i in range(headings.count())]

    def body_heading_count(self) -> int:
        return self.page.locator(self.BODY_HEADINGS).count()

    def body_heading_icon_style(self, index: int = 0) -> dict:
        """Reads the ::before pseudo-element's computed style — Playwright
        cannot locate a pseudo-element as its own element, so this evaluates
        directly on the real heading node with the `::before` pseudo
        argument to `getComputedStyle` (134674's "56x56 icon" IS this
        pseudo-element, not a real focusable button — see docstring)."""
        return self.page.locator(self.BODY_HEADINGS).nth(index).evaluate(
            "el => { const cs = getComputedStyle(el, '::before'); "
            "return {width: cs.width, height: cs.height, borderRadius: cs.borderRadius, "
            "backgroundColor: cs.backgroundColor}; }"
        )

    def body_heading_text_style(self, index: int = 0) -> dict:
        return self.page.locator(self.BODY_HEADINGS).nth(index).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontSize: cs.fontSize, fontWeight: cs.fontWeight, color: cs.color, "
            "textAlign: cs.textAlign, gap: cs.gap}; }"
        )

    def body_heading_gap(self, index: int = 0) -> str:
        return self.page.locator(self.BODY_HEADINGS).nth(index).evaluate("el => getComputedStyle(el).gap")

    # ── Rich text structure (134675) ───────────────────────────────────────
    def body_list_count(self) -> int:
        return self.page.locator(self.BODY_LISTS).count()

    def has_bullet_list(self) -> bool:
        return self.page.locator(self.BODY_UL).count() > 0

    def has_numbered_list(self) -> bool:
        return self.page.locator(self.BODY_OL).count() > 0

    def inline_link_href(self) -> str | None:
        return self.page.locator(self.INTRO_LINK).first.get_attribute("href")

    def inline_link_target(self) -> str | None:
        return self.page.locator(self.INTRO_LINK).first.get_attribute("target")

    def inline_link_is_visible(self) -> bool:
        return self.is_visible(self.INTRO_LINK)

    # ── Section order (134679, 134700) ─────────────────────────────────────
    def section_heading_order(self) -> list:
        """[intro heading text, *body heading texts] in DOM/visual order —
        the concrete stand-in for "every configured content section appears
        in the configured order"."""
        return [self.intro_heading_text()] + self.body_heading_texts()

    # ── CTA hyperlink (134694, 134730, 134731, 134736, 134741, 134743) ────
    def is_cta_visible(self) -> bool:
        return self.is_visible(self.CTA)

    def cta_label_text(self) -> str:
        return self.text(self.CTA_LABEL)

    def cta_href(self) -> str | None:
        return self.page.locator(self.CTA_LINK).get_attribute("href")

    def cta_target(self) -> str | None:
        return self.page.locator(self.CTA_LINK).get_attribute("target")

    def click_cta_and_get_popup_or_none(self):
        """Clicks the CTA link; returns the new Page if it opened in a new
        tab (target=_blank), else None (same-tab navigation, 134743)."""
        try:
            with self.page.context.expect_page(timeout=4000) as popup_info:
                self.click(self.CTA_LINK)
            return popup_info.value
        except Exception:  # noqa: BLE001 — no new tab opened, same-tab nav
            return None

    def no_anchor_has_empty_or_void_href(self) -> bool:
        """134731/134736: true if every anchor inside the editorial content
        (intro + body + CTA) has a real, non-empty, non-javascript-void
        href — the general regression-guard stand-in for "no empty/broken
        link label/destination", checkable without reproducing the specific
        blocked CMS precondition."""
        hrefs = self.page.locator(f"{self.INTRO_LINK}, {self.BODY_LINKS}, {self.CTA_LINK}").evaluate_all(
            "els => els.map(el => el.getAttribute('href'))"
        )
        return all(h and h.strip() and not h.strip().lower().startswith("javascript:") for h in hrefs)

    # ── Auth / public reachability (134683) ────────────────────────────────
    def is_login_prompt_visible(self) -> bool:
        return self.is_visible('role=dialog[name*="Sign In" i]') or self.is_visible('role=heading[name*="Sign In" i]')

    def are_all_sections_visible(self) -> dict:
        return {
            "hero": self.is_hero_visible(),
            "breadcrumb": self.is_visible(self.BREADCRUMB),
            "intro": self.is_visible(self.INTRO),
            "media": self.is_visible(self.MEDIA),
            "body": self.is_visible(self.BODY),
        }

    # ── Dark mode (134748, 134749, 134750, 134751) ─────────────────────────
    def enable_dark_mode(self, timeout: int = 5000) -> "AboutQatarChamberPage":
        """Opens the accessibility panel (composed AccessibilityToolsComponent,
        no re-declared locator) and toggles Dark Mode, then waits for the
        REAL resulting state (`<html data-theme="dark">`) via
        `wait_for_function` — no `sleep()`/`wait_for_timeout()`, per
        automation-standards.md's explicit-wait rule."""
        self.a11y.click_accessibility_button()
        self.a11y.switch_to_dark_mode()
        self.page.wait_for_function(
            "() => document.documentElement.getAttribute('data-theme') === 'dark'",
            timeout=timeout,
        )
        return self

    def page_background_color(self) -> str:
        return self.page.locator(self.PAGE).evaluate("el => getComputedStyle(el).backgroundColor")

    def is_dark_mode_active(self) -> bool:
        theme = self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        html_class = self.page.evaluate("() => document.documentElement.className") or ""
        return theme == "dark" or "qc-dark" in html_class

    def body_heading_color(self, index: int = 0) -> str:
        return self.page.locator(self.BODY_HEADINGS).nth(index).evaluate("el => getComputedStyle(el).color")

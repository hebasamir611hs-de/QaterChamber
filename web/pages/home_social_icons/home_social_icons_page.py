"""
web/pages/home_social_icons/home_social_icons_page.py — HomeSocialIconsPage.

Public-frontend Page Object for the Home Page "Find us on social media"
widget (PBI 129373, QC-HOME-004B) — `div.qc-home-social`. Follows this
project's established `home_X` naming/module convention (see
`home_about_summary_page.py` / `home_strategic_partners_page.py`), placed in
this already-scaffolded folder rather than under `pages/components/`.

ARCHITECTURE FIX (2026-09-16, this session): created to correct a Page-Object
defect where `web/pages/components/footer_component.py`'s `FooterComponent`
— despite its name/location/docstring all claiming to read the real
`<footer>` — actually resolved to THIS widget's own container
(`div.qc-home-social`), via a heading-text/ancestor walk keyed on this
widget's own heading. `FooterComponent` has since been fixed to genuinely
target the real footer (`ul.qc-footer-social`); this class is the correct,
dedicated home for this widget's own public-visibility assertions —
`cms/tests/components/test_footer_control_panel.py`'s 131188/131194/131196
(PBI-129373/HOME-004B cases) now import THIS class instead.

CONFIRMED LIVE 2026-09-16 (scripted Playwright, real qcdev Home Page HTML,
un-authenticated context):
  - `div.qc-home-social` is a stable, unique (count=1) CSS scope, confirmed
    NOT nested inside `<footer>` (`footer div.qc-home-social` matches 0
    elements) — a genuinely separate container from the real footer.
  - This widget's own heading, exact text "Find us on social media", is
    present on the public Home Page (`web_url("/")`), distinct from the real
    footer's own heading ("Follow Us on Social Media").
  - The 9 real production links inside this container, confirmed hrefs, in
    this FIXED left-to-right order (Facebook, X, LinkedIn, YouTube,
    Instagram, Snapchat, Flickr, Telegram, WhatsApp) — currently IDENTICAL
    to the real footer's own 9 hrefs, since both delivery surfaces are
    driven by the same shared CMS object
    (`cms/pages/components/footer_admin_component.py`'s "LOAD-BEARING
    FINDING #1"):
    `https://facebook.com/qatarchamber`, `https://x.com/qatarchamber`,
    `https://linkedin.com/company/qatarchamber`,
    `https://youtube.com/@qatarchamber`,
    `https://instagram.com/qatarchamber`,
    `https://snapchat.com/add/qatarchamber`,
    `https://www.flickr.com/photos/qatarchamber`,
    `https://t.me/qatarchamber`, `https://wa.me/97444559111`.
  - Each link carries a real accessible name via `aria-label` (e.g.
    `aria-label="Facebook"`), not empty as an earlier, now-corrected
    docstring elsewhere had claimed — not relied upon here regardless, since
    a freshly-created test entry's `aria-label` is still just one of the 9
    fixed Platform values; `href` substring matching remains the only
    reliable per-entry identity signal for a test-created marker.
  - `PRODUCTION_WHATSAPP_HREF` is intentionally NOT redefined here — both
    containers currently render the identical 9 production hrefs, so it is
    imported from `footer_component.py` (single definition) rather than
    duplicated as a second constant for the same real-world value.

NAMED RISK, carried over from
`cms/tests/home_social_icons/test_home_social_icons_control_panel.py`'s own
OPEN QUESTION (not resolved here, flagged for the QA Manager): this shared
CMS object also carries three fields specific to the Home delivery surface —
"Show on Home" (checkbox), "Home Icon Image", "Home Display Order" — distinct
from the base "Display Order" / "Active Status" fields 131188/131194/131196
actually set. Whether this widget only renders an entry that has "Show on
Home" explicitly set (independent of base Display Order / Active Status) was
NOT independently confirmed this session. If so, those three tests' own
positive control (`has_production_icons()`) still passes (the 9 real
production rows already have it set), but their own test-created entry could
be structurally unable to appear in THIS container regardless of the base
field under test — a possible false-green on the NEGATIVE assertions
specifically (131194's "is excluded", 131196's "has no effect"), not
something this fix invents a check for.

EXTENDED 2026-09-17 (PBI 129373, "Frontend UI/Figma rendering" batch — TC
131133/131134/131135/131136/131139/131141/131142/131143/131144/131145/131147;
131146 is Manual-tagged and out of scope, never authored per Axis 1b of the
tag taxonomy). CLI-first extraction: no interactive/labelled-element dump was
useful for the styling assertions these cases need (padding/gap/background/
border/radius/typography/hover are not surfaced by `extract_locators.py`'s
harvest, which targets interactive elements only) — a disclosed, scoped
Playwright script was used instead, the SAME documented fallback pattern
`home_latest_news_page.py` already established for this project (still
CLI/shell, never the Playwright MCP). Confirmed live, anonymous context,
1920x1080, `web_url("/")`, both `en` and `ar`:

  - Real DOM structure inside `div.qc-home-social`:
    `div.qc-social-inner` > `h2.qc-social-title` (heading) +
    `p.qc-social-subtitle` (subtext) + `ul.qc-social-list` (the icon row,
    holding one `li > a` per icon — the `<a>`'s own parent is the `<li>`,
    NOT the row; the row is the `<li>`'s parent `<ul>`).
  - Adjacency to Latest News (TC 131133): `section.qc-home-latest-news`'s
    own bottom edge (`y + height`) is bit-identical to
    `div.qc-home-social`'s top edge in the same unscrolled-page read
    (1730.9375 + 598.03125 == 2328.96875, confirmed both EN and AR) — no
    gap, hence nothing else can render between them. Asserted here via a
    bounding-box comparison (a real computed-geometry check, per this
    project's established pattern in `home_latest_news_page.py`), not a DOM
    sibling-walk (the two sections do not share a direct parent, so a naive
    `nextElementSibling` walk returns nothing even though they are visually
    and structurally adjacent).
  - Container (`div.qc-home-social`) computed style: `padding: 40px 16px`;
    `background-color: rgb(255,255,255)` (solid, `background-image: none`
    — NO gradient); `border-width: 0px` (no border, no `border-image`);
    `border-radius: 0px`. TC 131134's stated Figma values (padding
    `20px 32px`; gradient `#FBF6F8`→`#F6F6F6` background; 1px gradient
    border `#E3C5CB`→`#DEDEDD`; `border-radius: 12px`) do **not** match any
    of the 4 confirmed-live values — a genuine design/implementation gap,
    not a locator problem (this is the same container this Page Object has
    used, confirmed and exercised, since its creation this session).
  - Heading (`h2.qc-social-title`): `font-family` starts with `Cairo`,
    `font-weight: 700`, `font-size: 24px`, `line-height: 28.8px`,
    `color: rgb(145,23,49)` = `#911731` — exact match to TC 131135's stated
    color/weight/size/family; `line-height` does NOT match (case states
    `32px`; confirmed live is `28.8px`, i.e. `1.2×` the font size, not
    `1.333×`).
  - Subtext (`p.qc-social-subtitle`): `font-family` starts with `Cairo`,
    `font-weight: 400`, `font-size: 18px`, `line-height: 27px`,
    `color: rgb(108,108,107)` = `#6C6C6B` — exact match to TC 131136's
    stated color/weight/size/family; `line-height` does NOT match (case
    states `28px`; confirmed live is `27px`).
  - Icon row (`ul.qc-social-list`): `justify-content: flex-end`,
    `gap: 12px` — both match TC 131139's stated values exactly.
    `flex-wrap: wrap` — does NOT match TC 131139's stated `nowrap`. All 3
    row-level properties are count-independent (they hold regardless of how
    many `<li>` children exist), so this is scripted and asserted against
    the row exactly as the case states even though qcdev currently renders
    9 real production icons, not the case's "8 active" precondition.
  - Hover (TC 131147): confirmed live, hovering the first icon `<a>` changes
    `background-color` from `rgb(255,255,255)` to `rgb(145,23,49)`, `color`
    from `rgb(145,23,49)` to `rgb(255,255,255)` (the child `<svg>` inherits
    the same color change via `currentColor`), and applies a small lift
    (`transform: translateY(-2px)`, reported as `matrix(1,0,0,1,0,-2)`) —
    a real, distinct, observable hover state. `cursor: pointer` was already
    true before hover (not a hover-triggered change).
  - RTL (TC 131144) / LTR (TC 131145): `<html dir="rtl">` /
    `computed direction: rtl` confirmed live on `/ar/`; `dir="ltr"` /
    `direction: ltr` confirmed live on `/`. The row's `justify-content:
    flex-end` is a **logical** (writing-mode-relative) value, so under RTL
    it anchors the icon row to the visual LEFT and under LTR to the visual
    RIGHT — exactly TC 131144/131145's own stated expectation (RTL: "row
    anchors to the left ... logical flex-end"; LTR: "icon row is
    right-anchored") — asserted here via a live bounding-box half-of-
    viewport comparison (mirrors `home_latest_news_page.py`'s
    `_horizontal_half()` pattern) rather than re-asserting the static
    numbers captured during this probe, since a fresh run must read the
    real, current position.
  - Click/new-tab (TC 131143): the LinkedIn entry's confirmed live `href`
    is `https://linkedin.com/company/qatarchamber` (no `www.`, hyphen-free
    slug) — TC 131143's own stated target
    (`https://www.linkedin.com/company/qatar-chamber`) differs in both the
    `www.` prefix and the slug's hyphenation. The new-tab MECHANISM (a
    second page opens, the original Home page tab is untouched) is asserted
    unconditionally; the destination URL is compared against the case's
    literal stated URL as a second, independent assertion — so a failure on
    the URL text reads as a content/config mismatch, not a broken
    click-opens-new-tab mechanism.
  - `computed_style()` below is a per-Page-Object copy of the same helper
    already used in `vmo_page.py` / `board_of_directors_page.py` (getComputedStyle
    restricted to requested props) — duplicated rather than factored into a
    shared base, mirroring this project's own established precedent of one
    copy per Page Object rather than a premature shared helper.
  - NOT independently re-confirmed this session (network to qcdev.ihorizons.com
    became unreachable — TCP connect timeouts on both `curl` and Playwright —
    partway through this probe, after the structural/style data above was
    already captured live twice, EN and AR): whether some inner wrapper
    OTHER than `div.qc-home-social` itself (e.g. `.qc-social-inner`) carries
    the Figma-intended gradient/border/radius instead. The container
    measured above is the same `div.qc-home-social` this Page Object has
    used as "the container" since its own creation this session — the
    right element per this Page Object's own established identity — but if
    a future pass finds the Figma-intended box model actually lives one
    level deeper, that is a design-clarification follow-up, not evidence
    this measurement point was wrong.
"""

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.footer_component import PRODUCTION_WHATSAPP_HREF
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

HOME_SOCIAL_HEADING_TEXT = "Find us on social media"
HOME_SOCIAL_CONTAINER = "div.qc-home-social"

# Real, CLI-verified constants (see EXTENDED module docstring, 2026-09-17
# probe) — the section's own internal structure and its immediate
# predecessor section on the Home page.
HTML_ROOT = "html"
LATEST_NEWS_SECTION = "section.qc-home-latest-news"
HOME_SOCIAL_HEADING = f"{HOME_SOCIAL_CONTAINER} h2.qc-social-title"
HOME_SOCIAL_SUBTEXT = f"{HOME_SOCIAL_CONTAINER} p.qc-social-subtitle"
HOME_SOCIAL_ICON_ROW = f"{HOME_SOCIAL_CONTAINER} ul.qc-social-list"


def rgb_to_hex(rgb: str) -> str:
    """Normalize a CSS `rgb(r, g, b)` / `rgba(r, g, b, a)` computed-style
    string (what `getComputedStyle(...).color` etc. always returns — never
    a hex literal) into `#RRGGBB` uppercase, so a QA case's Figma hex value
    can be compared directly against a live computed style."""
    nums = [int(n.strip()) for n in rgb.strip().rstrip(")").split("(")[-1].split(",")[:3]]
    return "#" + "".join(f"{n:02X}" for n in nums)


class HomeSocialIconsPage(BasePage):
    """Read-only query surface over the Home Page "Find us on social media"
    widget (`div.qc-home-social`). No admin/authoring actions — see
    `SocialMediaIconAdminPage`
    (`cms/pages/components/footer_admin_component.py`) for those."""

    def __init__(self, page):
        super().__init__(page)
        # Composed, not re-declared — see `AccessibilityToolsComponent`'s own
        # module docstring (PBI 129364, QC-GBL-003, the site-wide Dark Mode
        # toggle). Added for TC 131152 (batch 4) — this widget has no dark-
        # mode logic of its own, it only needs to read its OWN computed
        # colors after the site-wide toggle fires.
        self.a11y = AccessibilityToolsComponent(page)

    def open_home(self, locale: str = "en") -> "HomeSocialIconsPage":
        """Deliberately uses `BasePage.open_anonymous()`, never `open()` —
        see that method's own docstring: `open()` unconditionally
        reauthenticates on any non-login-flow URL if it detects a login
        form, which would silently re-authenticate an intentionally
        anonymous context (this Page Object's only intended use — see
        standards.md's "Draft/Unpublish Public-Visibility Checks —
        Mandatory Logged-Out Context").

        BUG FIX (2026-09-17, this batch): previously waited on the literal
        English heading text (`HOME_SOCIAL_HEADING_TEXT`), which never
        renders on `locale="ar"` (confirmed live — the Arabic heading is
        "تابعونا على وسائل التواصل الاجتماعي") and would have timed out on
        every Arabic-locale caller (TC 131144). Waits on the locale-agnostic
        container instead — the same fix already applied project-wide for
        this exact class of bug (e.g. `HomeLatestNewsPage.open_home_arabic`)."""
        url = web_url("/", locale=locale)
        self.open_anonymous(url)
        self.wait_for(HOME_SOCIAL_CONTAINER, state="visible")
        # The container being visible does not guarantee the icon LINKS
        # underneath it have mounted yet — wait on the container's own
        # first real link (a condition, not a sleep) before any caller
        # reads `social_icon_hrefs()`, or a same-tick read could see a
        # short/empty link list and fail every test's own positive control.
        self._social_icon_links().first.wait_for(state="visible", timeout=10000)
        return self

    def _social_icon_links(self):
        return self.page.locator(HOME_SOCIAL_CONTAINER).get_by_role("link")

    def social_icon_hrefs(self) -> list:
        """Ordered list of every social icon link's `href`, left to right —
        the ordering IS the frontend's own rendered position, driven by each
        entry's Display Order (see module docstring)."""
        links = self._social_icon_links()
        return [links.nth(i).get_attribute("href") or "" for i in range(links.count())]

    def has_production_icons(self) -> bool:
        """Positive control — confirms the section container was actually
        found and holds real content, so a subsequent "our marker is absent"
        assertion cannot silently pass against an empty/wrong container."""
        return any(PRODUCTION_WHATSAPP_HREF in href for href in self.social_icon_hrefs())

    def has_icon_with_href_marker(self, marker: str) -> bool:
        return any(marker in href for href in self.social_icon_hrefs())

    def index_of_href_marker(self, marker: str) -> int:
        hrefs = self.social_icon_hrefs()
        for i, href in enumerate(hrefs):
            if marker in href:
                return i
        return -1

    def index_of_production_whatsapp(self) -> int:
        hrefs = self.social_icon_hrefs()
        for i, href in enumerate(hrefs):
            if PRODUCTION_WHATSAPP_HREF in href:
                return i
        return -1

    # ── Layout / positioning (TC 131133, 131139, 131144, 131145) ──────────
    def scroll_to_section(self) -> "HomeSocialIconsPage":
        self.page.locator(HOME_SOCIAL_CONTAINER).scroll_into_view_if_needed()
        return self

    def section_bounding_box(self) -> dict:
        return self.page.locator(HOME_SOCIAL_CONTAINER).bounding_box()

    def is_immediately_below_latest_news(self, tolerance_px: float = 2.0) -> bool:
        """TC 131133 — real computed-geometry adjacency check (mirrors the
        established pattern in `home_latest_news_page.py`), NOT a DOM
        sibling-walk: the two sections do not share a direct parent, so
        `nextElementSibling` finds nothing even though they render flush
        against each other (confirmed live — see module docstring). True
        only if Latest News's own bottom edge sits within `tolerance_px` of
        this section's top edge, on the SAME unscrolled page read."""
        latest_news_box = self.page.locator(LATEST_NEWS_SECTION).bounding_box()
        social_box = self.section_bounding_box()
        if not latest_news_box or not social_box:
            return False
        latest_news_bottom = latest_news_box["y"] + latest_news_box["height"]
        return abs(latest_news_bottom - social_box["y"]) <= tolerance_px

    def page_direction(self) -> str:
        return self.page.locator(HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(HOME_SOCIAL_CONTAINER).evaluate("el => getComputedStyle(el).direction")

    def row_bounding_box(self) -> dict:
        return self.page.locator(HOME_SOCIAL_ICON_ROW).bounding_box()

    def _horizontal_half(self, x) -> str:
        """Mirrors `HomeLatestNewsPage._horizontal_half()` — which half of
        the current viewport an x-coordinate falls in."""
        viewport = self.page.viewport_size
        if x is None or not viewport:
            return "unknown"
        return "left_half" if x < viewport["width"] / 2 else "right_half"

    def icon_row_horizontal_position(self) -> str:
        box = self.row_bounding_box()
        return self._horizontal_half(box["x"] if box else None)

    def is_no_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        )

    # ── Text content (TC 131135, 131136, 131144, 131145) ───────────────────
    def heading_text(self) -> str:
        return self.text(HOME_SOCIAL_HEADING).strip()

    def subtext_text(self) -> str:
        return self.text(HOME_SOCIAL_SUBTEXT).strip()

    # ── Computed style (TC 131134, 131135, 131136, 131139) ─────────────────
    def computed_style(self, locator: str, props: list) -> dict:
        """Per-Page-Object copy of the same helper already used in
        `vmo_page.py` / `board_of_directors_page.py` — see EXTENDED module
        docstring for why this is duplicated rather than shared."""
        return self.page.locator(locator).evaluate(
            """(el, props) => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) { out[p] = s[p]; }
                return out;
            }""",
            props,
        )

    def container_style(self) -> dict:
        return self.computed_style(
            HOME_SOCIAL_CONTAINER,
            ["padding", "backgroundImage", "backgroundColor", "borderWidth", "borderRadius"],
        )

    def heading_style(self) -> dict:
        style = self.computed_style(
            HOME_SOCIAL_HEADING,
            ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color", "textAlign"],
        )
        style["colorHex"] = rgb_to_hex(style["color"])
        return style

    def subtext_style(self) -> dict:
        style = self.computed_style(
            HOME_SOCIAL_SUBTEXT,
            ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color", "textAlign"],
        )
        style["colorHex"] = rgb_to_hex(style["color"])
        return style

    def row_style(self) -> dict:
        return self.computed_style(
            HOME_SOCIAL_ICON_ROW,
            ["justifyContent", "gap", "flexWrap"],
        )

    # ── Hover state (TC 131147) ────────────────────────────────────────────
    def _icon_style_snapshot(self, index: int = 0) -> dict:
        link = self._social_icon_links().nth(index)
        return link.evaluate(
            """(el) => {
                const s = getComputedStyle(el);
                return { color: s.color, backgroundColor: s.backgroundColor,
                         transform: s.transform, cursor: s.cursor };
            }"""
        )

    def hover_icon_style_change(self, index: int = 0) -> dict:
        """Hovers the icon at `index` and returns {"before": ..., "after": ...}
        computed-style snapshots — TC 131147's own required evidence (a
        distinct, observable hover state), not merely "hover fires with no
        crash"."""
        before = self._icon_style_snapshot(index)
        self._social_icon_links().nth(index).hover()
        self.wait_for(HOME_SOCIAL_ICON_ROW, state="visible")
        after = self._icon_style_snapshot(index)
        return {"before": before, "after": after}

    # ── Dark mode (TC 131152) ───────────────────────────────────────────────
    def enable_dark_mode(self) -> "HomeSocialIconsPage":
        """Site-wide Dark Mode toggle (composed `AccessibilityToolsComponent`
        — see `__init__`), then a real condition-wait on the resulting
        `<html data-theme="dark">` attribute (the same confirmed-live
        mechanism `AboutQatarChamberPage.enable_dark_mode()` already uses),
        never a `sleep()`."""
        self.a11y.click_accessibility_button()
        self.a11y.switch_to_dark_mode()
        self.page.wait_for_function(
            "() => document.documentElement.getAttribute('data-theme') === 'dark'",
            timeout=5000,
        )
        return self

    def is_dark_mode_active(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('data-theme') === 'dark'"
        )

    # ── Icon-level geometry — overlap/clip check (TC 131140, 131151) ───────
    def icon_bounding_boxes(self) -> list:
        links = self._social_icon_links()
        return [links.nth(i).bounding_box() for i in range(links.count())]

    def has_overlapping_or_clipped_icons(self, viewport_width: int = None) -> bool:
        """True if any two icon links' own boxes overlap each other, or any
        icon box extends outside the current viewport's width — the actual
        "no icon is clipped or overlapping" condition several Figma-mobile
        cases (131140, 131151) state as their expected result, checked via
        real geometry rather than a visual screenshot diff."""
        boxes = [b for b in self.icon_bounding_boxes() if b]
        vw = viewport_width or (self.page.viewport_size or {}).get("width")
        for box in boxes:
            if vw and (box["x"] < -0.5 or box["x"] + box["width"] > vw + 0.5):
                return True
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                overlap_x = a["x"] < b["x"] + b["width"] and b["x"] < a["x"] + a["width"]
                overlap_y = a["y"] < b["y"] + b["height"] and b["y"] < a["y"] + a["height"]
                if overlap_x and overlap_y:
                    return True
        return False

    # ── Click → new tab (TC 131143) ────────────────────────────────────────
    def click_icon_and_capture_new_tab(self, index: int = 0):
        """Clicks the icon at `index` and returns the new page/tab Playwright
        opened for it (`target="_blank"` links), asserting nothing itself —
        the caller compares the new tab's URL and confirms the original
        page's own URL is unchanged, per TC 131143's two distinct
        expectations."""
        with self.page.context.expect_page() as new_page_info:
            self._social_icon_links().nth(index).click()
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded", timeout=10000)
        return new_page

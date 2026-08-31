"""
web/pages/home_social_icons/home_social_icons_page.py — HomeSocialIconsPage.

Home Page section (PBI 129373 / QC-HOME-004B "Social Media Icons") — a widget
distinct from the footer's own social icons (PBI 129366 / QC-GBL-004,
web/pages/components/footer_component.py). Lives in its own home_social_icons/
page folder per automation-standards.md's "Group by page/module" rule.

Locators extracted CLI-first via tools/extract_locators.py against
https://qcdev.ihorizons.com/home at the framework's default viewport
(1920x1080), through the license-gate/announcement-overlay clearing already
wired into BasePage.open():

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home \
        --viewport 1920x1080 --find "facebook"
    -> [role] uniq=2  get_by_role("link", name="Facebook")  ⚠ NON-UNIQUE (matches 2)

The role-based extractor call is ambiguous by design here: this page's social
icons share the exact same aria-label ("Facebook", "LinkedIn", ...) AND the
same `a.qc-social-link` class as the footer's own, unrelated social-icons
component (same class-name collision pattern already documented in
web/pages/components/header_component.py's docstring for its nav mega-menu
duplicate) — the extractor's page-wide get_by_role() uniqueness check cannot
tell the two widgets apart. Resolved the same documented way: one extra
scoped Playwright script (still CLI/shell, not the Playwright MCP) that
reused BasePage.open() for identical license-gate/overlay handling, then read
the real DOM structurally, confirming a single unambiguous container:

    div.qc-home-social                       -- unique widget root (count=1)
      > div.qc-social-inner
        > div.qc-social-panel                -- unique (count=1)
          > div.qc-social-copy
            > h2.qc-social-title              -- unique (count=1) "Find us on social media"
            > p.qc-social-subtitle            -- unique (count=1) "Stay connected..."
          > ul.qc-social-list                 -- unique (count=1)
            > li > a.qc-social-link[aria-label="<Platform>"]   -- 8 items, scoped
              (a.qc-social-link alone resolves to 16 elements site-wide: 8 here
              + 8 in the footer's own component — scoping every icon locator
              under div.qc-home-social, exactly as WIDGET below does, is what
              makes each one unique again)

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here — automation-standards.md's Result
Integrity section):

  - TC-131133 (section order): the widget's own layout-structure item sits at
    index 4 of 16 top-level Home sections, and the sibling immediately before
    it contains the text "Latest News... Stay Connected & Informed...".
    MATCHES the case's expected result exactly.
  - TC-131134 (desktop container): live computed styles on div.qc-social-panel
    are padding "22px 32px" (case expects "20px 32px" — mismatch), gap
    "20px 32px" row/col (case expects a uniform "24px" — mismatch),
    background-image "linear-gradient(90deg, rgba(145, 23, 49, 0.05) 0%,
    rgba(145, 23, 49, 0) 55%), none" (an entirely different colour system
    from the case's #FBF6F8→#F6F6F6 — mismatch), border "1px solid
    rgb(227, 197, 203)" (the rgb() form of #E3C5CB — MATCHES the gradient
    border's first stop exactly, but a plain CSS `border` shorthand can only
    ever expose ONE colour, so whether a genuine two-stop #E3C5CB→#DEDEDD
    gradient border is implemented at all is NOT verifiable via
    getComputedStyle — a real tooling limitation, not a pass), border-radius
    "18px" (case expects "12px" — mismatch).
  - TC-131135 (desktop heading): font-family includes "Cairo" and font-weight
    "700" MATCH; font-size computes "25.6px" (case expects "24px" —
    mismatch) and line-height "30.72px" (case expects "32px" — mismatch);
    color "rgb(145, 23, 49)" (#911731) MATCHES exactly.
  - TC-131136 (desktop subtext): font-weight "400" and font-size "18px"
    MATCH; line-height computes "27px" (case expects "28px" — mismatch);
    color "rgb(108, 108, 107)" (#6C6C6B) MATCHES exactly.
  - TC-131137 (mobile 375px heading): font-weight "700" and font-size "20px"
    MATCH; line-height computes "24px" (case expects "30px" — mismatch);
    color MATCHES.
  - TC-131138 (mobile 375px subtext): font-size stays "18px" — it does NOT
    scale down to the case's stated "14px" at 375px (mismatch); line-height
    computes "27px" (case expects "22px" — mismatch); color MATCHES.
  - TC-131139 (desktop icon row): justify-content "flex-end" MATCHES; gap
    computes "14px" (case expects "12px" — mismatch); flex-wrap computes
    "wrap" (case expects "nowrap" — mismatch, though with 8x58px icons the
    1920px-wide viewport still renders a single row regardless); all 8 icons
    confirmed on one row.
  - TC-131140 (mobile 375px icon row): justify-content "center" MATCHES; gap
    computes "10px" (case expects "12px" — mismatch); flex-wrap "wrap"
    MATCHES; all 8 icons render across two rows of 4 with zero horizontal
    clipping/overlap (every icon's rect stayed inside 0..375px).
  - TC-131141 (order): live DOM order (left-to-right, EN) is Facebook, X,
    LinkedIn, Instagram, YouTube, WhatsApp, Telegram, Snapchat — the case's
    expected first five (Facebook, X/Twitter, LinkedIn, Instagram, YouTube)
    MATCH exactly. Control_Panel/CMS access to inspect or set a literal
    "Display Order 1-5" field is out of scope this run (Control_Panel is a
    separate Platform tag, excluded from this batch); verified against the
    live configured order instead, per the case's own stated fallback. A real
    discrepancy to flag: 8 platforms are live/active, not the 5 the case's
    precondition describes.
  - TC-131142 (inactive icon): all 8 known platforms — including the case's
    own example, Snapchat — currently render as visible/active
    (display:block, visibility:visible, opacity:1) in this environment; none
    is presently configured Active Status=False to observe the negative
    case against. Toggling that flag requires Control_Panel/CMS access,
    out of scope this run — a genuine precondition gap, not a fabricated
    pass. Scripted as a closed-set check against the current live catalog
    (see icon_labels()) instead of the untestable negative scenario.
  - TC-131143 (LinkedIn link): live href is
    "https://linkedin.com/company/qatarchamber" with target="_blank" and
    rel="noopener noreferrer" — the new-tab MECHANISM matches the case, but
    the literal URL differs from the case's stated
    "https://www.linkedin.com/company/qatar-chamber" (no "www.", no hyphen
    in "qatar-chamber") — a real mismatch.
  - TC-131144 / TC-131145 (RTL/LTR): on /ar/home, documentElement dir="rtl",
    the panel and icon list both compute direction:"rtl", heading/subtext
    text-align computes "start" (renders visually right-aligned under RTL),
    list justify-content stays "flex-end", and icon x-positions descend in
    DOM order (Facebook rightmost) — a genuine logical mirror, matching
    TC-131144. On /home (EN, LTR), justify-content is also "flex-end" with
    icon x-positions ascending in DOM order, packing the row to its own right
    edge — matching TC-131145. No clipped/overlapping text or icons observed
    in either language.
  - TC-131147 (hover): comparing the Facebook icon's (and its inner <svg>'s)
    computed opacity/transform/color/background-color/box-shadow immediately
    before vs. ~400ms after a real `page.mouse.move()` onto its center shows
    NO change in any of those properties. `cursor` reads "pointer" both
    before and after — that is the browser's unconditional default cursor
    for an anchor with an href, not a hover-specific affordance. A separate
    probe of :focus-visible (keyboard focus, not mouse hover) DOES show a
    visible ring (box-shadow "rgb(255, 255, 255) 0px 0px 0px 2px,
    rgb(128, 172, 255) 0px 0px 0px 4px"), but that is a different
    interaction than the one this case asks about. No live hover-specific
    visual affordance was found for a mouse hover — a real mismatch, not
    fabricated.
"""

from core.web.base_page import BasePage
from config.settings import web_url

HOME_URL = web_url("/home")
HOME_URL_AR = web_url("/home", locale="ar")

# The 8 platforms currently configured live, in their real DOM (display)
# order — used as the closed-set "only active icons render" proxy for
# TC-131142 (see docstring: no icon is currently toggled Active=False to
# observe the true negative against).
LIVE_ACTIVE_PLATFORMS = [
    "Facebook", "X", "LinkedIn", "Instagram", "YouTube",
    "WhatsApp", "Telegram", "Snapchat",
]


class HomeSocialIconsPage(BasePage):
    # ── Locators — scoped under the unique widget root to avoid the
    #    footer's identically-classed a.qc-social-link collision (see
    #    docstring) ─────────────────────────────────────────────────────
    WIDGET = "div.qc-home-social"
    PANEL = f"{WIDGET} >> div.qc-social-panel"
    HEADING = f"{WIDGET} >> h2.qc-social-title"
    SUBTEXT = f"{WIDGET} >> p.qc-social-subtitle"
    ICON_LIST = f"{WIDGET} >> ul.qc-social-list"
    ICON_LINKS = f"{WIDGET} >> a.qc-social-link"
    ICON_LINK_FACEBOOK = f'{WIDGET} >> a.qc-social-link[aria-label="Facebook"]'
    ICON_LINK_LINKEDIN = f'{WIDGET} >> a.qc-social-link[aria-label="LinkedIn"]'

    def open_home(self) -> "HomeSocialIconsPage":
        self.open(HOME_URL)
        self.wait_for(self.WIDGET)
        return self

    def open_home_arabic(self) -> "HomeSocialIconsPage":
        self.open(HOME_URL_AR)
        self.wait_for(self.WIDGET)
        return self

    # ── Visibility / basic state ────────────────────────────────────────
    def is_widget_visible(self) -> bool:
        return self.is_visible(self.WIDGET)

    def heading_text(self) -> str:
        return self.text(self.HEADING).strip()

    def subtext_text(self) -> str:
        return self.text(self.SUBTEXT).strip()

    # ── Section-order check (TC-131133) ─────────────────────────────────
    def previous_section_text(self) -> str:
        """Text content of the Home-page section immediately BEFORE this
        widget's own layout-structure item — used to confirm it renders
        directly after Latest News with nothing in between."""
        return self.page.locator(self.WIDGET).evaluate(
            "el => { const item = el.closest('[class*=\"lfr-layout-structure-item\"]'); "
            "const parent = item ? item.parentElement : null; "
            "if (!parent) return ''; "
            "const siblings = Array.from(parent.children); "
            "const idx = siblings.indexOf(item); "
            "const prev = idx > 0 ? siblings[idx - 1] : null; "
            "return prev ? (prev.textContent || '').trim() : ''; }"
        )

    # ── Container style (TC-131134) ─────────────────────────────────────
    def container_style(self) -> dict:
        return self.page.locator(self.PANEL).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {padding: cs.padding, gap: cs.gap, backgroundImage: cs.backgroundImage, "
            "borderWidth: cs.borderTopWidth, borderStyle: cs.borderTopStyle, "
            "borderColor: cs.borderTopColor, borderRadius: cs.borderRadius}; }"
        )

    # ── Heading / subtext typography (TC-131135, 131136, 131137, 131138) ─
    def heading_style(self) -> dict:
        return self.page.locator(self.HEADING).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize, "
            "lineHeight: cs.lineHeight, color: cs.color, textAlign: cs.textAlign}; }"
        )

    def subtext_style(self) -> dict:
        return self.page.locator(self.SUBTEXT).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize, "
            "lineHeight: cs.lineHeight, color: cs.color, textAlign: cs.textAlign}; }"
        )

    # ── Page direction (TC-131144, 131145) ──────────────────────────────
    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    # ── Icon row layout (TC-131139, 131140) ─────────────────────────────
    def icon_row_style(self) -> dict:
        return self.page.locator(self.ICON_LIST).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {justifyContent: cs.justifyContent, gap: cs.gap, flexWrap: cs.flexWrap, "
            "direction: cs.direction}; }"
        )

    def icon_count(self) -> int:
        return self.page.locator(self.ICON_LINKS).count()

    def icon_labels(self) -> list:
        """aria-label of each icon, in real DOM (left-to-right source) order."""
        icons = self.page.locator(self.ICON_LINKS)
        return [icons.nth(i).get_attribute("aria-label") for i in range(icons.count())]

    def icon_boxes(self) -> list:
        icons = self.page.locator(self.ICON_LINKS)
        boxes = []
        for i in range(icons.count()):
            box = icons.nth(i).bounding_box()
            if box:
                boxes.append(box)
        return boxes

    def icon_x_positions(self) -> list:
        return [round(b["x"]) for b in self.icon_boxes()]

    def icons_fit_within_viewport(self) -> bool:
        """True if every icon's rect stays fully inside the current
        viewport's width — the no-clipping check for TC-131140/131144."""
        viewport = self.page.viewport_size
        width = viewport["width"] if viewport else None
        if not width:
            return False
        return all(0 <= b["x"] and (b["x"] + b["width"]) <= width for b in self.icon_boxes())

    def icons_do_not_overlap(self) -> bool:
        boxes = self.icon_boxes()
        for i in range(len(boxes)):
            a = boxes[i]
            for j in range(i + 1, len(boxes)):
                b = boxes[j]
                if not (a["x"] + a["width"] <= b["x"] or b["x"] + b["width"] <= a["x"]
                        or a["y"] + a["height"] <= b["y"] or b["y"] + b["height"] <= a["y"]):
                    return False
        return True

    def icons_render_on_single_row(self) -> bool:
        boxes = self.icon_boxes()
        if not boxes:
            return False
        rows = {round(b["y"]) for b in boxes}
        return len(rows) == 1

    # ── Inactive-icon closed-set check (TC-131142) ──────────────────────
    def rendered_platforms_match_live_catalog(self) -> bool:
        """Proxy for "only active icons render": the rendered aria-label set
        equals exactly the currently-known live/active catalog, with no
        duplicates and nothing unexpected. See module docstring — no icon is
        presently toggled Active=False in this environment to verify the
        literal negative case against."""
        labels = self.icon_labels()
        return sorted(labels) == sorted(LIVE_ACTIVE_PLATFORMS) and len(labels) == len(set(labels))

    # ── LinkedIn new-tab click (TC-131143) ───────────────────────────────
    def click_linkedin_in_new_tab(self):
        """Clicks the LinkedIn icon and returns the resulting new tab (Page).
        The original tab (self.page) is left untouched — callers assert its
        URL/visibility separately to confirm it stayed open unchanged."""
        with self.page.context.expect_page() as new_page_info:
            self.click(self.ICON_LINK_LINKEDIN)
        new_page = new_page_info.value
        try:
            new_page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:  # noqa: BLE001 — an external site's own slowness must
            pass            # not fail this test before we even read its URL
        return new_page

    # ── Hover state (TC-131147) ─────────────────────────────────────────
    def _facebook_icon_snapshot(self) -> dict:
        return self.page.locator(self.ICON_LINK_FACEBOOK).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {opacity: cs.opacity, transform: cs.transform, cursor: cs.cursor, "
            "color: cs.color, backgroundColor: cs.backgroundColor, boxShadow: cs.boxShadow}; }"
        )

    def hover_facebook_icon_before_after(self) -> tuple:
        """Returns (before, after) computed-style snapshots of the Facebook
        icon, captured immediately before and ~400ms after a real mouse
        hover onto its center."""
        before = self._facebook_icon_snapshot()
        box = self.page.locator(self.ICON_LINK_FACEBOOK).bounding_box()
        self.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        self.page.wait_for_timeout(400)
        after = self._facebook_icon_snapshot()
        return before, after

"""
web/pages/components/header_component.py — HeaderComponent.

Cross-page GLOBAL component (PBI 129363 / QC-GBL-001 "Site Header") — lives in
pages/components/ per this project's component exception (never duplicated
into a page folder), automation-standards.md's "Page Object / Screen Object
rules".

Locators extracted CLI-first via tools/extract_locators.py against
https://qcdev.ihorizons.com/home at the framework's default viewport
(1920x1080), through the license-gate/announcement-overlay clearing already
wired into BasePage.open():

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home \
        --viewport 1920x1080 --scope "header.qc-global-site-header"
    -> [role] uniq=1  get_by_role("link", name="E-services")  -> "E-services"
    -> [role] uniq=1  get_by_role("button", name="Accessibility tools")
    -> [role] uniq=2  get_by_role("link", name="About us")  (matches inside
       header scope — desktop + hidden mega-menu duplicate; disambiguated
       below by a structural CSS scope instead of the ambiguous role/name)

The scoped extractor call surfaced only 6 unique candidates (the header mixes
a visible top-level nav with a hidden mega-menu sharing the same accessible
names), so the exact structural selectors below were confirmed directly
against the live DOM (header.qc-global-site-header > .qc-header-inner >
nav.qc-nav > ul.qc-nav-list > li > a.qc-nav-link) rather than taken from the
ambiguous extractor rows — the same "ambiguous element" fallback condition
automation-standards.md's Tooling-priority table describes, resolved here by
one extra scoped DOM read rather than the Playwright MCP.

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here):
  - The header's top-level nav (`nav.qc-nav > ul.qc-nav-list > li > a`) has
    11 visible items (About us, Our Services, E-services, Committee, Events,
    Exhibitions, Media Center, Invest in Qatar, B2B, Contact us, FAQs), not
    the 10 ADO #134232/#134233 describe. Scripted per the approved case's
    stated count of 10 anyway — a real mismatch to flag, not to re-judge here.
  - The rendered logo is 138x48 (aspect-ratio-scaled from a 48px-tall image),
    not the case's stated 180x48.
  - The header container's box-shadow computes to "none" on both the
    <header> and .qc-header-inner elements — the case expects
    "0px 0px 14px rgba(0,0,0,0.25)". Background #FFFFFF and padding
    16px 24px DID match (split across <header> and .qc-header-inner
    respectively — see container_style()).
  - Clicking .qc-search-btn does NOT open an in-page overlay: it performs a
    client-side (senna.js) route change to /web/qatar-chamber/search, a
    distinct results page, not a modal over the current page. SEARCH_OVERLAY*
    below are intent-based selectors for the modal the case describes — they
    were never observed live, so is_search_overlay_open() will honestly read
    False against the current implementation.
  - Keyboard Tab from a fresh page load never reaches the logo (or any other
    header element): focus oscillates indefinitely between an invisible
    reCAPTCHA badge iframe and <body>. This is a real, reproducible keyboard-
    navigation defect, not a locator problem — press_tab_until_focused()
    (core/web/base_page.py) will honestly return False within its bounded
    attempt count.

--- Second extraction pass (ADO #134234, #134237, #134239, #134244, #134249 —
5 more cases for the same PBI, unblocked after the user fixed a tagging
conflict in Azure that had put both Automation and Manual on these cases) ---

The scoped extractor call again surfaces only role-based candidates for the
UNIQUE nav items (its uniqueness check runs page.get_by_role() against the
WHOLE page, not the --scope container, so items that share an accessible
name with the hidden mega-menu duplicate — About us, Our Services, Committee,
B2B, Contact us — report as non-unique even though the structural chain
below already disambiguates them). It also cannot see decorative icon
elements (svg/i with no role/label — the harvester's SEL list only walks
a,button,input,select,textarea,[role],[data-testid],[data-test],
[aria-label],[contenteditable]), which is exactly what the chevron-affordance
and collapsed-dropdown cases need to inspect. Both conditions are the
documented "ambiguous element" / "state the script can't reach" fallback in
automation-standards.md's Tooling-priority table — resolved the same way as
the first pass's LOGO_IMAGE fix: one extra scoped Playwright script (still
CLI/shell, not the Playwright MCP) that reused BasePage.open() for identical
license-gate/overlay handling, then read the header's real DOM structurally:

    header.qc-global-site-header > nav.qc-nav > ul.qc-nav-list > li
        .qc-has-children          -- 3 of the 11 items have a sub-menu
            > a.qc-nav-link > svg.qc-chevron   (the chevron-down affordance)
            > .qc-nav-sub                       (the mega-menu panel itself)
        :not(.qc-has-children)     -- the other 8 items: no svg.qc-chevron

Real, CLI-verified findings from this second pass (reported, not silently
corrected):
  - Of the 11 top-level nav items, exactly 3 (About us, Our Services, B2B)
    carry `li.qc-has-children` and render an `svg.qc-chevron` beside their
    label; the other 8 (E-services, Committee, Events, Exhibitions, Media
    Center, Invest in Qatar, Contact us, FAQs) render no chevron at all —
    matches ADO #134234's expected behaviour exactly (a genuine PASS
    candidate, unlike most of this PBI's cases).
  - Each `.qc-has-children` item's `.qc-nav-sub` panel is `display: none`
    before any hover/focus interaction — matches ADO #134249's expected
    behaviour exactly. IMPORTANT flakiness note found while extracting: a
    freshly-launched Chromium context's default cursor position (0, 0)
    registered as an incidental hover on the first `.qc-has-children` item
    ("About us") and left its panel open at read time — a false "not
    collapsed" reading with no test interaction at all. Confirmed reproducible
    by moving the mouse away first (`page.mouse.move(960, 900)`, a point well
    below the header) versus not — is_nav_submenu_collapsed_before_interaction()
    below always parks the cursor there first so the read isn't polluted by
    whatever the browser's initial cursor position happens to be.
  - The logo's alt text is genuinely bilingual and reachable via the language
    switcher: EN alt = "Qatar Chamber", AR alt = "غرفة قطر" (confirmed live
    after switch_to_arabic()). Its rendered size is unchanged by language
    (138x48 in both, per the first pass's already-documented 138-vs-180
    mismatch) — same box, mirrored to the right edge under the RTL layout.
  - The language switcher (`a.qc-lang-switcher`) live style: 32x32px,
    border-radius 8px (both MATCH ADO #134239's stated values), label "AR"
    (MATCHES), font-family includes "Cairo" (MATCHES) at 14px (MATCHES) —
    but background-color computes to rgb(247, 248, 249) (#F7F8F9) not the
    case's stated #EDEDED, font-weight computes to 500 (Medium) not the
    "Regular" (400) the case implies, and color computes to
    rgb(107, 108, 126) not the case's stated #6C6C6B. A genuine partial
    mismatch — scripted per the case's exact stated values regardless.
  - Client-side (senna.js) nav-link navigation is measurably async: reading
    the header's nav/logo state immediately after the initial `<header>`
    element re-appears (a bare `wait_for(HEADER)`) intermittently reads an
    empty/transitional header (0 nav items, blank logo alt) even though the
    same read after `page.wait_for_load_state("networkidle")` reliably reads
    the full, correct header on the destination page. open_about_us_via_nav()
    / open_contact_us_via_nav() below wait on network-idle before the
    trailing wait_for(HEADER) for this reason — a real timing characteristic
    of this site's client-side routing, not a flaky test.
"""

from core.web.base_page import BasePage
from config.settings import web_url

HOME_URL = web_url("/home")


class HeaderComponent(BasePage):
    # Locators — named constants, scoped under the header via Playwright's
    # ">>" locator-chaining syntax (still a single string, compatible with
    # BasePage's page.locator(locator) wrapper API).
    HEADER = "header.qc-global-site-header"
    HEADER_INNER = f"{HEADER} >> .qc-header-inner"
    LOGO = f"{HEADER} >> a.qc-logo"
    # a.qc-logo contains TWO <img>s live: the real logo (data-qc-logo-img,
    # real alt text) and a hidden dark-mode-only variant
    # (class="qc-logo-dark-only", aria-hidden="true") that shares the same
    # "img" tag — a bare "img" locator hits Playwright strict mode (2
    # matches). Scoped to the real one via its own data attribute, found
    # only after the first run hit that strict-mode violation live.
    LOGO_IMAGE = f"{HEADER} >> a.qc-logo img[data-qc-logo-img]"
    NAV = f"{HEADER} >> nav.qc-nav"
    # Direct-child chain (ul.qc-nav-list > li > a.qc-nav-link) intentionally
    # excludes the nested mega-menu items (li .qc-nav-sub a.qc-nav-link),
    # which share the same class and several accessible names (About us,
    # Our Services, etc.) as their top-level parents.
    NAV_TOP_LEVEL_ITEMS = f"{HEADER} >> nav.qc-nav > ul.qc-nav-list > li > a.qc-nav-link"
    LANGUAGE_SWITCHER = f"{HEADER} >> a.qc-lang-switcher"
    ACCESSIBILITY_BUTTON = f'{HEADER} >> role=button[name="Accessibility tools"]'
    SEARCH_BUTTON = f"{HEADER} >> a.qc-search-btn"

    # ── Second pass: nav sub-menu affordance / dropdown collapse state ──
    # `.qc-has-children` marks the 3 of 11 top-level items that carry a
    # mega-menu (About us, Our Services, B2B) — confirmed live, see docstring.
    NAV_ITEM_WITH_SUBMENU = f"{NAV} >> ul.qc-nav-list > li.qc-has-children"
    NAV_ITEM_WITHOUT_SUBMENU = f"{NAV} >> ul.qc-nav-list > li:not(.qc-has-children)"
    # Relative selectors, chained off a specific item locator (`.first`) via
    # `.locator(...)` in the methods below — never resolved on their own,
    # since several items share these classes.
    NAV_ITEM_CHEVRON_ICON = "svg.qc-chevron"
    NAV_ITEM_SUBMENU_PANEL = ".qc-nav-sub"
    # Built off NAV_TOP_LEVEL_ITEMS (the direct-child chain that already
    # excludes the nested mega-menu's same-named links) via Playwright's
    # `:has-text()` pseudo-class — still one plain locator string, no new
    # chaining mechanism.
    NAV_LINK_ABOUT_US = f'{NAV_TOP_LEVEL_ITEMS}:has-text("About us")'
    NAV_LINK_CONTACT_US = f'{NAV_TOP_LEVEL_ITEMS}:has-text("Contact us")'

    # Intent-based only — never matched on the live site (see docstring).
    # Written as real, resolvable Playwright selectors (not TODO placeholders)
    # for the modal the case describes, so the test fails honestly rather
    # than erroring on an unresolved constant.
    SEARCH_OVERLAY = '[role="dialog"]:has(input)'
    SEARCH_OVERLAY_INPUT = '[role="dialog"] input[type="search"], [role="dialog"] input[type="text"]'
    SEARCH_OVERLAY_SUBMIT = (
        '[role="dialog"] button[type="submit"], '
        '[role="dialog"] [aria-label*="search" i], '
        '[role="dialog"] button:has-text("Search")'
    )

    def open_home(self) -> "HeaderComponent":
        self.open(HOME_URL)
        self.wait_for(self.HEADER)
        return self

    # ── State queries — no asserts, tests do the asserting ──────────────
    def is_header_visible(self) -> bool:
        return self.is_visible(self.HEADER)

    def container_style(self) -> dict:
        """Merges the two DOM layers that make up the visible header
        container: <header> carries background-color/box-shadow, its
        .qc-header-inner child carries the flex row/padding (see docstring
        for the live values found)."""
        outer = self.page.locator(self.HEADER).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {backgroundColor: cs.backgroundColor, boxShadow: cs.boxShadow}; }"
        )
        inner = self.page.locator(self.HEADER_INNER).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {display: cs.display, flexDirection: cs.flexDirection, padding: cs.padding}; }"
        )
        return {**outer, **inner}

    def logo_size(self) -> dict:
        box = self.page.locator(self.LOGO_IMAGE).bounding_box()
        return {"width": round(box["width"]), "height": round(box["height"])} if box else {}

    def is_logo_leftmost(self) -> bool:
        logo_box = self.page.locator(self.LOGO).bounding_box()
        if not logo_box:
            return False
        other_lefts = [logo_box["x"] + logo_box["width"]]
        for loc in (self.NAV_TOP_LEVEL_ITEMS, self.LANGUAGE_SWITCHER, self.SEARCH_BUTTON):
            box = self.page.locator(loc).first.bounding_box()
            if box:
                other_lefts.append(box["x"])
        return all(logo_box["x"] <= x for x in other_lefts)

    def nav_item_labels(self) -> list:
        items = self.page.locator(self.NAV_TOP_LEVEL_ITEMS)
        return [items.nth(i).inner_text().strip() for i in range(items.count())]

    def nav_item_count(self) -> int:
        return self.page.locator(self.NAV_TOP_LEVEL_ITEMS).count()

    def nav_item_font_styles(self) -> list:
        """One {fontFamily, fontSize, color} dict per top-level nav item, in
        left-to-right order — used to verify uniform styling across items
        (the case gives no concrete hex/font value to assert against)."""
        items = self.page.locator(self.NAV_TOP_LEVEL_ITEMS)
        styles = []
        for i in range(items.count()):
            styles.append(items.nth(i).evaluate(
                "el => { const cs = getComputedStyle(el); "
                "return {fontFamily: cs.fontFamily, fontSize: cs.fontSize, color: cs.color}; }"
            ))
        return styles

    def is_utility_cluster_rightmost(self) -> bool:
        """Language switcher + icon buttons (accessibility, search) all sit
        to the right of every nav item — mirrors case step 5."""
        nav_items = self.page.locator(self.NAV_TOP_LEVEL_ITEMS)
        nav_rights = [nav_items.nth(i).bounding_box()["x"] + nav_items.nth(i).bounding_box()["width"]
                      for i in range(nav_items.count())]
        if not nav_rights:
            return False
        utility_lefts = []
        for loc in (self.LANGUAGE_SWITCHER, self.ACCESSIBILITY_BUTTON, self.SEARCH_BUTTON):
            box = self.page.locator(loc).first.bounding_box()
            if box:
                utility_lefts.append(box["x"])
        return bool(utility_lefts) and min(utility_lefts) >= max(nav_rights)

    def is_language_switcher_visible(self) -> bool:
        return self.is_visible(self.LANGUAGE_SWITCHER)

    def is_search_button_visible(self) -> bool:
        return self.is_visible(self.SEARCH_BUTTON)

    def is_accessibility_button_visible(self) -> bool:
        return self.is_visible(self.ACCESSIBILITY_BUTTON)

    def open_search(self) -> "HeaderComponent":
        self.click(self.SEARCH_BUTTON)
        return self

    def is_search_overlay_open(self) -> bool:
        return self.is_visible(self.SEARCH_OVERLAY)

    def is_search_overlay_input_visible(self) -> bool:
        return self.is_visible(self.SEARCH_OVERLAY_INPUT)

    def is_search_overlay_submit_visible(self) -> bool:
        return self.is_visible(self.SEARCH_OVERLAY_SUBMIT)

    def focus_logo_via_tab(self, max_presses: int = 30) -> bool:
        return self.press_tab_until_focused(self.LOGO, max_presses=max_presses)

    def is_logo_focus_indicator_visible(self) -> bool:
        """True only if the logo is BOTH the focused element AND rendering a
        visible focus indicator (outline or box-shadow) — a focus indicator
        style that exists but never receives focus is not a passing case."""
        if not self.is_focused(self.LOGO):
            return False
        style = self.page.locator(self.LOGO).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {outlineStyle: cs.outlineStyle, outlineWidth: cs.outlineWidth, boxShadow: cs.boxShadow}; }"
        )
        has_outline = style["outlineStyle"] not in ("none", "") and style["outlineWidth"] != "0px"
        has_box_shadow = style["boxShadow"] not in ("none", "")
        return has_outline or has_box_shadow

    # ── Nav sub-menu chevron affordance / collapsed state (ADO #134234, #134249) ──
    def nav_item_with_submenu_shows_chevron(self) -> bool:
        """True if the first nav item configured WITH a sub-menu renders a
        visible chevron-down icon beside its label."""
        item = self.page.locator(self.NAV_ITEM_WITH_SUBMENU).first
        chevron = item.locator(self.NAV_ITEM_CHEVRON_ICON)
        return chevron.count() > 0 and chevron.first.is_visible()

    def nav_item_without_submenu_has_no_chevron(self) -> bool:
        """True if the first nav item configured with NO sub-menu renders no
        chevron icon at all."""
        item = self.page.locator(self.NAV_ITEM_WITHOUT_SUBMENU).first
        return item.locator(self.NAV_ITEM_CHEVRON_ICON).count() == 0

    def is_nav_submenu_collapsed_before_interaction(self) -> bool:
        """True if the first nav item WITH a sub-menu keeps its dropdown
        panel not rendered/visible before any hover/focus. Parks the cursor
        away from the header first — a leftover/default cursor position can
        register as an incidental hover and falsely open the panel before the
        test ever interacts with it (found live extracting this locator; see
        module docstring)."""
        self.page.mouse.move(960, 900)
        item = self.page.locator(self.NAV_ITEM_WITH_SUBMENU).first
        submenu = item.locator(self.NAV_ITEM_SUBMENU_PANEL)
        return submenu.count() > 0 and not submenu.first.is_visible()

    # ── Logo size/alt per language (ADO #134237) ────────────────────────
    def logo_alt_text(self) -> str:
        return self.page.locator(self.LOGO_IMAGE).get_attribute("alt")

    def switch_to_arabic(self) -> "HeaderComponent":
        """Clicks the language switcher and waits for the AR home page's
        header to fully render. Waits on network-idle before the trailing
        wait_for(HEADER) — this site's client-side nav is measurably async
        (see module docstring); a bare wait_for(HEADER) can read a
        transitional, half-mounted header."""
        self.click(self.LANGUAGE_SWITCHER)
        self.page.wait_for_load_state("networkidle")
        self.wait_for(self.LOGO_IMAGE)
        return self

    def switch_to_english(self) -> "HeaderComponent":
        """Symmetric counterpart to switch_to_arabic() — added for PBI 129392
        (QC-ABOUT 001, ADO #134696's AR->EN switch-back case). Reuses the SAME
        LANGUAGE_SWITCHER locator (its href/label flip automatically once the
        active locale is Arabic; confirmed live: switcher reads label "EN"
        with an `update_language?...languageId=en_US` href on an AR page) —
        no new locator declared. Same network-idle wait rationale as
        switch_to_arabic()."""
        self.click(self.LANGUAGE_SWITCHER)
        self.page.wait_for_load_state("networkidle")
        self.wait_for(self.LOGO_IMAGE)
        return self

    # ── Language switcher exact styling (ADO #134239) ───────────────────
    def language_switcher_label(self) -> str:
        return self.page.locator(self.LANGUAGE_SWITCHER).inner_text().strip()

    def language_switcher_style(self) -> dict:
        loc = self.page.locator(self.LANGUAGE_SWITCHER)
        box = loc.bounding_box()
        style = loc.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {borderRadius: cs.borderRadius, backgroundColor: cs.backgroundColor, "
            "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize, color: cs.color}; }"
        )
        size = {"width": round(box["width"]), "height": round(box["height"])} if box else {}
        return {**size, **style}

    # ── Cross-page header persistence (ADO #134244) ─────────────────────
    def open_about_us_via_nav(self) -> "HeaderComponent":
        """Navigates to the About Us page via the header's own "About us"
        nav link (rather than a guessed URL slug). Waits on network-idle
        before the trailing wait_for(HEADER) — see switch_to_arabic()'s
        docstring for why."""
        self.click(self.NAV_LINK_ABOUT_US)
        self.page.wait_for_load_state("networkidle")
        self.wait_for(self.HEADER)
        return self

    def open_contact_us_via_nav(self) -> "HeaderComponent":
        """Navigates to the Contact Us page via the header's own "Contact us"
        nav link. See open_about_us_via_nav()'s docstring for the
        network-idle wait rationale."""
        self.click(self.NAV_LINK_CONTACT_US)
        self.page.wait_for_load_state("networkidle")
        self.wait_for(self.HEADER)
        return self

    def header_fingerprint(self) -> dict:
        """Composite snapshot of the header's rendering — layout, nav
        labels, logo, and language-switcher label — for comparing it
        identically across pages. Composed from the existing state-query
        methods rather than re-reading the DOM."""
        return {
            "container_style": self.container_style(),
            "nav_labels": self.nav_item_labels(),
            "logo_alt": self.logo_alt_text(),
            "logo_size": self.logo_size(),
            "language_switcher_label": self.language_switcher_label(),
        }

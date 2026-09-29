"""
web/pages/components/language_switcher_component.py — LanguageSwitcherComponent.

Cross-page GLOBAL component (PBI 129365 / QC-GBL-002 "Language Switcher") —
lives in pages/components/ per this project's component exception (never
duplicated into a page folder), automation-standards.md's "Page Object /
Screen Object rules".

HeaderComponent-reuse decision: the language switcher button itself
(`a.qc-lang-switcher`), the Accessibility icon, the Search icon, the logo, and
the top-level nav items are ALL already named constants on
web/pages/components/header_component.py (PBI 129363's Page Object) — that
class extracted and disambiguated them first. Re-declaring the same selector
strings here would be exactly the "duplicated locator constants for the same
element across objects" defect the structure & redundancy scan checks for.
This is nonetheless a distinct Page Object for a distinct PBI (per the
one-class-per-component rule), so it does not import/extend HeaderComponent
directly either — it COMPOSES one (`self.header = HeaderComponent(page)`) and
reads its public locator constants (`self.header.LANGUAGE_SWITCHER`, etc.)
rather than duplicating or inlining them. Everything this component owns
outright (the RTL/LTR body-content locators: the "Our Services" cards section
and its "View All" CTA) is new for this PBI and lives here as its own named
constants.

Locators — CLI-first extraction log:

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home \
        --viewport 1920x1080 --scope "header.qc-global-site-header"

First run of this exact command returned ZERO candidates — not an ambiguous-
element case but a real framework bug found live: unlike BasePage.open(),
tools/extract_locators.py had no path to clear the dev-instance license-gate
interstitial (core/web/license_gate.py) or the announcement overlay
(core/web/overlays.py) before harvesting, and qcdev answered the plain goto()
with the license_activation interstitial instead of /home (confirmed via a
raw Playwright script: page.url resolved to
".../c/portal/license_activation", header count 0). Fixed in
tools/extract_locators.py itself (two changes, disclosed, not silent):
  1. inserts the project root onto sys.path (the script's own directory is
     what Python puts on sys.path[0], not the cwd it's launched from) so
     `from core.web...` resolves;
  2. imports core.web.license_gate / core.web.overlays defensively (a project
     without them just no-ops) and runs the identical clear-gate /
     dismiss-overlay sequence BasePage.open() runs, right after goto().
Re-run after the fix returned 14 real candidates, confirming the header's
already-extracted constants are still correct and current:
    [role] uniq=37  get_by_role("link", name="AR") -> "AR"  NON-UNIQUE (37)
    [role] uniq=1   get_by_role("button", name="Accessibility tools")
    [role] uniq=3   get_by_role("link", name="Search") -> "Search" NON-UNIQUE
The "AR" role/name candidate is non-unique for the same documented reason
HeaderComponent's docstring already gives (extract_locators.py's uniqueness
check runs page.get_by_role() against the WHOLE page, not the --scope
container passed to the harvester) — confirming, not contradicting, that
HeaderComponent's structural selector (`header.qc-global-site-header >>
a.qc-lang-switcher`) is still the right disambiguated choice to reuse as-is.
A second run also fixed a pre-existing extractor crash unrelated to this
PBI's locators: printing the "⚠ NON-UNIQUE" glyph raised UnicodeEncodeError
on a default-cp1252 Windows console. Fixed by reconfiguring stdout to UTF-8
defensively at the top of main() — a no-op on already-UTF-8 terminals.

extract_locators.py harvests interactive/labelled ELEMENTS for selector
picking — it does not (and per its own docstring is not meant to) report
bounding boxes, computed CSS, or <html> attributes, which is exactly what the
RTL/LTR mirroring cases (#134435, #134436) and the icon-cluster ordering case
(#134428) need to verify. That data was confirmed live via one additional
scoped Playwright script (still CLI/shell, never the Playwright MCP) that
reuses the SAME core.web.license_gate / core.web.overlays guards as
BasePage.open() before reading the page — the identical "extra scoped script"
fallback path HeaderComponent's docstring already documents for its own
ambiguous/unreachable-by-harvester cases. Real, CLI-verified findings from
that pass (reported, not silently adjusted):
  - Icon cluster (EN, LTR, viewport 1920x1080): language switcher
    x=1760/y=24/32x32, Accessibility button x=1800/32x32, Search button
    x=1840/32x32 — the switcher IS left of both, matching ADO #134428's
    stated order exactly. Label = "AR" (matches). Size 32x32 (matches).
    computed background-color = rgb(247, 248, 249) (#F7F8F9), NOT the case's
    stated #EDEDED — the same background-color mismatch
    header_component.py's own docstring already logged for ADO #134239 on
    this identical element; scripted per #134428's exact stated value
    regardless (a real, honestly-reported mismatch, not silently corrected).
  - EN home (`/home`): <html dir="ltr" lang="en-US">; body computed
    {direction: "ltr", textAlign: "start"}. Nav item x-positions strictly
    INCREASE left-to-right (About us x=427 ... FAQs x=1460); logo box
    x=48 (left half of a 1920px viewport); "Our Services" cards
    (`.qc-os-card`, 8 of them) x-positions strictly increase (336, 654,
    972 ... 2562); its "View All Services" CTA (`.qc-os-viewall`) sits at
    x=1411 (right half) — a fully LTR-flowing page, matching #134435.
  - AR home (`web_url("/home", locale="ar")` -> `/ar/home`): <html
    dir="rtl" lang="ar-SA">; body computed {direction: "rtl", textAlign:
    "start"} — "start" is direction's LOGICAL value (renders left under ltr,
    right under rtl; confirmed identical string on both languages, the
    direction flip is what makes it render mirrored, not a literal
    "left"/"right" string flip). Nav item x-positions strictly DECREASE
    (item 0 "من نحن" x=1451 down to item 10 "الأسئلة الشائعة" x=350) — a
    full mirror of the EN order, not merely flipped text; logo box moves to
    x=1734 (right half); language switcher now reads "EN" at x=128 (left
    half — the whole utility cluster relocated). Services cards mirror too
    (x=1290 down to x=-936, decreasing); the CTA moves to x=336 (left half).
    Matches ADO #134436 exactly.
  - No `.breadcrumb` element exists anywhere on the live homepage (breadcrumbs
    render on inner pages, not Home) — the case's "breadcrumbs" example is
    treated as "if present" per its own step wording; this component checks
    the elements that ARE present on Home (nav, logo, service cards, CTA
    button) as the concrete stand-in evidence for "body content ... flow".
"""

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.header_component import HeaderComponent


class LanguageSwitcherComponent(BasePage):
    # Locators this component owns outright (new for this PBI). Everything
    # already named on HeaderComponent (the switcher button itself, the
    # Accessibility/Search icons, the logo, the nav items) is read via
    # `self.header` below instead of being re-declared here — see the
    # HeaderComponent-reuse note in the module docstring.
    HTML_ROOT = "html"
    SERVICES_SECTION = "section.qc-home-our-services"
    SERVICES_CARDS = f"{SERVICES_SECTION} .qc-os-card"
    SERVICES_VIEW_ALL_BUTTON = f"{SERVICES_SECTION} .qc-os-viewall"

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "LanguageSwitcherComponent":
        """Loads the homepage with English active (the site's default
        locale, no path prefix)."""
        self.header.open_home()
        return self

    def open_home_arabic(self) -> "LanguageSwitcherComponent":
        """Loads the homepage directly on the Arabic locale
        (`web_url("/home", locale="ar")` -> `/ar/home`), rather than clicking
        the switcher first — the case's own step is "load the homepage with
        Arabic active", not "switch to Arabic from an English page"."""
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.header.HEADER)
        return self

    # ── Language switcher visibility / position / styling (ADO #134428) ──
    def is_language_switcher_visible(self) -> bool:
        return self.header.is_language_switcher_visible()

    def language_switcher_label(self) -> str:
        return self.header.language_switcher_label()

    def language_switcher_box(self) -> dict:
        box = self.page.locator(self.header.LANGUAGE_SWITCHER).bounding_box()
        return {"width": round(box["width"]), "height": round(box["height"])} if box else {}

    def language_switcher_background_color(self) -> str:
        return self.page.locator(self.header.LANGUAGE_SWITCHER).evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )

    def is_language_switcher_left_of_accessibility_and_search(self) -> bool:
        """True if the language switcher sits to the left of BOTH the
        Accessibility icon and the maroon Search icon in the header's
        top-right cluster (ADO #134428's stated order)."""
        switcher_box = self.page.locator(self.header.LANGUAGE_SWITCHER).bounding_box()
        accessibility_box = self.page.locator(self.header.ACCESSIBILITY_BUTTON).bounding_box()
        search_box = self.page.locator(self.header.SEARCH_BUTTON).bounding_box()
        if not (switcher_box and accessibility_box and search_box):
            return False
        return switcher_box["x"] < accessibility_box["x"] and switcher_box["x"] < search_box["x"]

    # ── Page-level LTR/RTL state (ADO #134435, #134436) ─────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def page_language(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("lang")

    def body_text_flow(self) -> dict:
        """{direction, textAlign} computed on <body>. NOTE: textAlign reads
        the CSS logical value "start" on BOTH languages live (not a literal
        "left"/"right" string) -- it is `direction` that flips between the
        two languages and makes "start" render left under ltr / right under
        rtl. Read both together; direction is what actually distinguishes
        the two cases here (see module docstring)."""
        return self.page.evaluate(
            "() => { const cs = getComputedStyle(document.body); "
            "return {direction: cs.direction, textAlign: cs.textAlign}; }"
        )

    def nav_item_x_positions(self) -> list:
        items = self.page.locator(self.header.NAV_TOP_LEVEL_ITEMS)
        positions = []
        for i in range(items.count()):
            box = items.nth(i).bounding_box()
            if box:
                positions.append(box["x"])
        return positions

    def nav_items_flow_direction(self) -> str:
        """"ltr" if nav item x-positions strictly increase left-to-right,
        "rtl" if they strictly decrease (a full mirror), else "mixed"."""
        return self._flow_direction(self.nav_item_x_positions())

    def logo_box(self) -> dict:
        box = self.page.locator(self.header.LOGO).bounding_box()
        return {"x": box["x"], "width": box["width"]} if box else {}

    def logo_horizontal_position(self) -> str:
        """"left_half" or "right_half" of the current viewport -- the
        standard/start position under LTR is the left half; RTL mirrors the
        logo to the right half (ADO #134435/#134436)."""
        box = self.page.locator(self.header.LOGO).bounding_box()
        return self._horizontal_half(box["x"] if box else None)

    # ── Body content flow: services cards + CTA (ADO #134435, #134436) ──
    def services_card_x_positions(self) -> list:
        cards = self.page.locator(self.SERVICES_CARDS)
        positions = []
        for i in range(cards.count()):
            box = cards.nth(i).bounding_box()
            if box:
                positions.append(box["x"])
        return positions

    def services_cards_flow_direction(self) -> str:
        """"ltr" if the service cards' x-positions strictly increase
        left-to-right, "rtl" if they strictly decrease (mirrored), else
        "mixed". No `.breadcrumb` exists on the live homepage (see module
        docstring) -- these repeating cards plus the CTA button below are
        this component's concrete stand-in for the case's "cards, buttons"
        body-content-flow check."""
        return self._flow_direction(self.services_card_x_positions())

    def services_view_all_button_horizontal_position(self) -> str:
        """"left_half" or "right_half" of the viewport -- the "View All
        Services" CTA sits on the right in LTR and mirrors to the left in
        RTL (ADO #134435/#134436)."""
        box = self.page.locator(self.SERVICES_VIEW_ALL_BUTTON).first.bounding_box()
        return self._horizontal_half(box["x"] if box else None)

    # ── Internal helpers (state-derivation only, no asserts) ────────────
    def _horizontal_half(self, x) -> str:
        viewport = self.page.viewport_size
        if x is None or not viewport:
            return "unknown"
        return "left_half" if x < viewport["width"] / 2 else "right_half"

    @staticmethod
    def _flow_direction(xs: list) -> str:
        if len(xs) < 2:
            return "mixed"
        if all(xs[i] < xs[i + 1] for i in range(len(xs) - 1)):
            return "ltr"
        if all(xs[i] > xs[i + 1] for i in range(len(xs) - 1)):
            return "rtl"
        return "mixed"

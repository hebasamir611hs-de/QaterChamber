"""
web/pages/components/accessibility_tools_component.py — AccessibilityToolsComponent.

Cross-page GLOBAL component (PBI 129364 / QC-GBL-003 "Accessibility Tools") —
lives in pages/components/ per this project's component exception (never
duplicated into a page folder), automation-standards.md's "Page Object /
Screen Object rules". Batch A (11 cases) built the panel/icon core; batch B
(11 more cases, this addendum) extends the SAME class with mobile viewport,
dark mode, high contrast (incl. a real axe-core WCAG audit), RTL-mirroring,
and keyboard-focus-indicator coverage — no locator or method already present
from batch A is re-declared.

--- Batch B — CLI-first extraction log (all via one-off scoped Playwright
scripts reusing core.web.license_gate / core.web.overlays, the same
"ambiguous element / can't-reach-by-harvester" fallback path documented in
the batch-A log below — extract_locators.py's static-DOM harvest cannot
observe any of these post-interaction/viewport-dependent states either) ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home \
        --viewport 375x812 --scope "header.qc-global-site-header"
    -> confirms the SAME ACCESSIBILITY_BUTTON/LANGUAGE_SWITCHER constants
       already on HeaderComponent resolve unchanged at the mobile viewport —
       no new locator needed for the icon itself, only new STATE reads
       (bounding boxes, scroll width) at that viewport, gathered via the
       scoped script below since the extractor does not report geometry.

Real, CLI-verified findings from this pass (reported, not silently adjusted):
  - Mobile viewport 375x812 (ADO #134629): accessibility icon box
    {x:286.3, y:24, width:32, height:32} — MATCHES the 32x32 container: the
    language switcher sits at {x:246.3 .. 278.3}, the icon at x=286.3, an
    ~8px gap, no overlap. `document.documentElement.scrollWidth` (375) ==
    `clientWidth` (375) both before AND after opening the panel — no
    horizontal overflow at any point (ADO #134631).
  - Mobile panel layout (ADO #134631): panel box {x:0, y:480, width:375,
    height:332} — full viewport width, stacked below the header, no
    clipping. All 6 real tool controls (see batch-A finding: Dark Mode +
    Done beyond the 4 named ones) render fully inside 0..375 on the x-axis:
    Dark Mode/High Contrast switches stack vertically (x=311, width=44);
    Zoom Out/Zoom In sit side-by-side (x=20/width=164.5 and x=190.5/
    width=164.5, summing to the full 355px content width); Reset/Done sit
    side-by-side at the bottom (x=20 and x=291.8) — a genuinely adapted,
    non-clipped mobile layout, not a naive unscaled desktop one.
  - High Contrast toggle (ADO #134632, #134661, #134662): clicking it adds
    class `qc-a11y-contrast` to `<html>` (confirmed via
    `document.documentElement.className`, NOT a body/data attribute) and
    flips `<body>`'s computed background-color from rgb(255,255,255) to
    rgb(0,0,0) with color rgb(255,255,255) — applied with ZERO navigation
    (read immediately after the click, no `page.goto`/reload occurred).
    Confirmed to survive a REAL full navigation (`page.goto` to
    `/web/qatar-chamber/contact-us`, a distinct second page, not a client-
    route change): `qc-a11y-contrast` is still present and body bg is still
    rgb(0,0,0) on the destination page — a genuine, verified persistence
    mechanism (session/cookie-backed, not merely in-memory JS state a
    fresh navigation would wipe), matching ADO #134661 step 4's "persistent
    config, not one-page" expectation exactly. Confirmed identically on the
    Arabic homepage (`dir="rtl"` unaffected by the toggle) for ADO #134662.
  - A real axe-core WCAG audit (axe-playwright-python, scoped to the
    `color-contrast` rule only) against the EN homepage with High Contrast
    active returned exactly **0 violations** — a genuine, observed PASS
    candidate for ADO #134632, not an assumed one.
  - Dark Mode toggle (ADO #134665, #134666) works differently from High
    Contrast: it does NOT add an `<html>` class. Instead it directly flips
    computed styles: `<header>` background rgb(255,255,255) ->
    rgb(29,29,27); the accessibility icon's own background rgb(247,248,249)
    -> rgb(42,42,40) (close in value to the new header bg) — but its
    `border-color` changes from rgb(231,231,237) (light mode) to
    rgba(255,255,255,0.12) (a light/white-ish translucent tone), which is
    the concrete mechanism that keeps the icon visually distinguishable
    against the new dark header, not a background-color contrast alone.
    `.qc-a11y-panel`'s own background matches the new header bg
    (rgb(29,29,27)). Of the 4 NAMED controls (ADO #134665's own literal "4
    controls" wording — see batch-A's #134630 finding that the panel
    actually renders 6; same coverage flag applies here, not re-litigated),
    text colors against the dark panel read: High Contrast switch
    rgb(255,255,255) on rgb(124,123,123); Zoom In/Out rgb(255,255,255) on
    rgb(29,29,27); Reset rgb(255,255,255) on a TRANSPARENT own background
    (rgba(0,0,0,0)) — which resolves visually to the panel's own dark
    background, confirmed live, not assumed. All 4 read genuinely legible
    (white text, never the same tone as their effective background).
  - RTL utility-cluster mirroring (ADO #134636, #134666): on the Arabic
    homepage the header's 3-icon cluster reads (left-to-right, viewport
    1920): search x=48, accessibility x=88, language switcher x=128 — the
    EXACT reverse order of the LTR reading (switcher x=1760 < accessibility
    x=1800 < search x=1840, already logged in HeaderComponent's own
    docstring for ADO #134239/#134428) — a genuine full mirror, not merely
    repositioned. Toggling Dark Mode on the Arabic page changes NEITHER
    `dir` (`rtl`, unchanged) nor the accessibility icon's x-position (88
    before and after) — dark mode is a pure color/style change, it does not
    perturb RTL layout, confirming ADO #134666's "stays in mirrored RTL
    position" expectation.
  - Zoom In / Zoom Out (ADO #134634): distinct accessible labels confirmed
    live via `inner_text()` — "Zoom in" and "Zoom out" respectively (already
    distinct per the panel structure in the batch-A log); both render
    `is_enabled() == True` on a fresh page load, no prior interaction.
  - Reset persistence (ADO #134635): after activating High Contrast AND
    clicking Zoom In once (zoom value read "110%", confirming the click
    genuinely took effect), then closing the panel (`.qc-a11y-close`) and
    reopening it via the header icon, the Reset button reads
    `is_visible() == True` and `is_enabled() == True` unchanged — a real,
    observed result, not assumed from its pre-interaction state alone.

HeaderComponent-reuse decision: the accessibility icon button itself
(`ACCESSIBILITY_BUTTON`), the language switcher, the search icon, and the nav
items are ALL already named constants on web/pages/components/header_component.py
(PBI 129363's Page Object) -- that class extracted and disambiguated them
first. Re-declaring the same selector strings here would be exactly the
"duplicated locator constants for the same element across objects" defect the
structure & redundancy scan checks for. This component therefore composes
HeaderComponent (`self.header = HeaderComponent(page)`), the same pattern
LanguageSwitcherComponent already established for PBI 129365, rather than
re-declaring or subclassing it. Everything this component owns outright (the
accessibility panel opened by that button, and every control inside it) is
new for this PBI and lives here as its own named constants.

Locators -- CLI-first extraction log:

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home \
        --scope "header.qc-global-site-header"
    -> [role] uniq=1  get_by_role("button", name="Accessibility tools")
       (already on HeaderComponent.ACCESSIBILITY_BUTTON -- reused, not
       re-declared; see HeaderComponent-reuse note above)

tools/extract_locators.py harvests the page as it loads, never after an
interaction -- it cannot see the accessibility PANEL at all, because the
panel does not exist in the DOM (or is not "visible": zero-size / display:none)
until the accessibility button is clicked. This is the documented "state the
script can't reach deterministically" fallback condition
(automation-standards.md's Tooling-priority table), resolved the same way
HeaderComponent's and LanguageSwitcherComponent's docstrings already
document: one additional scoped Playwright script (still CLI/shell, never the
Playwright MCP) that reuses BasePage.open()'s exact license-gate/overlay guard
sequence (core.web.license_gate, core.web.overlays), clicks the already-
confirmed ACCESSIBILITY_BUTTON, and reads the resulting DOM structurally:

    button[aria-label="Accessibility tools"].qc-accessibility-btn (header)
      -> click ->
    html.qc-a11y-panel-open
    div.qc-a11y-panel[role="dialog"][aria-label="Accessibility"]
        > div.qc-a11y-panel-header
            > span.qc-a11y-panel-title-group > span.qc-a11y-panel-title ("Accessibility")
            > button.qc-a11y-close[aria-label="Close"]
        > p.qc-a11y-panel-subtitle ("Adjust dark mode, contrast and page zoom.")
        > div.qc-a11y-row  (label "Dark mode")
            > button.qc-a11y-switch[data-qc-a11y-dark][role="switch"][aria-checked="false"]
        > div.qc-a11y-row  (label "High contrast")
            > button.qc-a11y-switch[data-qc-a11y-contrast][role="switch"][aria-checked="false"]
        > div.qc-a11y-row  (label "Zoom", value span.qc-a11y-zoom-value "100%")
            > div.qc-a11y-zoom-group
                > button[data-qc-a11y-zoom-out] ("Zoom out")
                > button[data-qc-a11y-zoom-in] ("Zoom in")
        > div.qc-a11y-footer
            > button.qc-a11y-reset[data-qc-a11y-reset] ("Reset")
            > button.qc-a11y-done[data-qc-a11y-done] ("Done")

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here):
  - The panel renders SIX interactive tool controls, not the four named
    across ADO #134482/#134630 (High Contrast, Zoom In, Zoom Out,
    Reset/Normal View): it ALSO renders a "Dark mode" toggle (the first row,
    ABOVE High Contrast) and a "Done" button (in the footer, beside Reset).
    #134630 states the panel opens with "exactly 4 controls ... no overlap"
    -- panel_tool_control_count() honestly counts all 6, so a test asserting
    the literal "exactly 4" will genuinely fail. Scripted per the case's
    stated number anyway, mirroring how header_component.py's own
    nav_item_count()/logo_size() are scripted per their cases' stated
    (and separately proven wrong) values.
  - The case's "Reset/Normal View" (#134488) renders live as a single button
    labelled "Reset" only -- no separate "Normal View" label exists. The
    case's own "/" wording already anticipates this naming variance, so this
    is NOT scripted as a mismatch; RESET_BUTTON is used as-is.
  - The High Contrast toggle (`role="switch"`) reads `aria-checked="false"`
    on first panel-open, before any interaction -- an off/default state,
    matching ADO #134486's expected result exactly.
  - The Zoom In/Zoom Out buttons and the Reset button all render with no
    `disabled` attribute (Playwright's `is_enabled()` reads True for all
    three) -- matching ADO #134487/#134488 exactly.
  - Clicking the header's accessibility ICON a second time (not the panel's
    own Close/Done buttons) DOES toggle the panel closed: `html.qc-a11y-panel-open`
    is removed and `.qc-a11y-panel` becomes not-visible (confirmed via
    `is_visible()`) -- matching ADO #134483 exactly. The panel element itself
    stays in the DOM (`page.locator(PANEL).count()` reads 1 both before and
    after), it is only hidden -- no duplicate/orphaned panel node is created
    by repeated open/close, which is the concrete, honest stand-in this
    component uses for ADO #134484's "no broken/duplicate panel markup"
    check (see panel_dom_instance_count() and the #134484 simulation note
    below).
  - Clicking the icon itself fires ZERO new network requests (confirmed via
    a `page.on("request", ...)` listener across the click, on an already-
    loaded page) -- the open/close TOGGLE is a pure client-side class/
    attribute flip. BUT the panel's behavior is genuinely backed by two
    separate, real, lazily-cacheable script+style bundles fetched during the
    INITIAL page load, before any click:
    `/o/qc-accessibility-tools/qc-accessibility.{js,css}` and
    `/o/qc-a11y-keyboard/qc-a11y-keyboard.{js,css}`. Blocking exactly these
    two bundles (via `page.route`, registered before `open_home()`) is a
    genuine, literal, reproducible way to simulate ADO #134484's "blocked
    script" precondition -- confirmed live:
      * 4 real `net::ERR_FAILED` console errors fire during the page LOAD
        (from the blocked resource fetches), NOT from the click itself.
      * With those bundles blocked, clicking the accessibility button
        afterward is a genuine no-op: `.qc-a11y-panel` never mounts at all
        (0 DOM nodes, confirmed via `panel_dom_instance_count()`) -- not a
        partial/broken panel, no panel at all. The button itself stays
        visible and clickable and throws nothing new at click-time.
    start_open_failure_simulation() therefore blocks these two real bundle
    paths (not a generic "a11y"/"accessib" substring guess), and the test
    asserts the case's literal wording precisely: the ICON CLICK itself
    introduces zero NEW console messages (measured as a delta after the
    click, since the 4 real errors are a page-load-time side effect of the
    simulated precondition, not of the click action) and the icon remains
    visible/unchanged -- while separately, honestly reporting that the
    panel does NOT open under this precondition and that blocking real
    resources (not a no-op) is what produced it.
  - At viewport 1366x768 (ADO #134628's stated desktop viewport), the
    accessibility button reads: box 32x32 (MATCHES), border-radius 8px
    (MATCHES), background-color rgb(247, 248, 249) (#F7F8F9) -- NOT the
    case's stated #EDEDED (the identical mismatch header_component.py's and
    language_switcher_component.py's own docstrings already log for this
    exact same header utility-cluster color), and computed padding "0px" --
    NOT the case's stated "10px" (a genuine, separate mismatch, honestly
    reported, not silently adjusted).
  - Keyboard Tab from a fresh page load hits the SAME reCAPTCHA-badge-
    iframe/<body> oscillation trap header_component.py's docstring already
    documents for the logo (ADO #134246) -- but here it is NON-DETERMINISTIC,
    not a consistent block: repeated live runs (both solo, `-n0`, and under
    the default `-n 3` parallel workers) show the accessibility button
    SOMETIMES reached within 40 Tab presses and sometimes not (observed 2
    fails / 1 pass across 3 solo re-runs, plus a pass under the default
    parallel run) -- a real, disclosed flakiness characteristic of this
    reCAPTCHA trap's timing (likely dependent on the badge iframe's own
    internal JS readiness relative to each Tab press), not a flaw in
    focus_accessibility_button_via_tab() or its bounded-wait contract. This
    is DIFFERENT from the logo's case, which is documented as consistently
    unreachable -- do not assume the two behave identically; report exactly
    what is observed on each run.
"""

from axe_playwright_python.sync_playwright import Axe

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.header_component import HeaderComponent


class AccessibilityToolsComponent(BasePage):
    # Locators this component owns outright (new for this PBI). The
    # accessibility BUTTON itself is read via `self.header.ACCESSIBILITY_BUTTON`
    # instead of being re-declared here -- see the HeaderComponent-reuse note
    # in the module docstring.
    PANEL = ".qc-a11y-panel"
    PANEL_CLOSE_BUTTON = f"{PANEL} >> button.qc-a11y-close"
    DARK_MODE_SWITCH = f"{PANEL} >> button.qc-a11y-switch[data-qc-a11y-dark]"
    HIGH_CONTRAST_SWITCH = f"{PANEL} >> button.qc-a11y-switch[data-qc-a11y-contrast]"
    HIGH_CONTRAST_ROW_LABEL = f'{PANEL} >> div.qc-a11y-row:has(button[data-qc-a11y-contrast]) >> .qc-a11y-row-label'
    ZOOM_OUT_BUTTON = f"{PANEL} >> button[data-qc-a11y-zoom-out]"
    ZOOM_IN_BUTTON = f"{PANEL} >> button[data-qc-a11y-zoom-in]"
    ZOOM_VALUE = f"{PANEL} >> .qc-a11y-zoom-value"
    RESET_BUTTON = f"{PANEL} >> button.qc-a11y-reset"
    DONE_BUTTON = f"{PANEL} >> button.qc-a11y-done"

    # The 4 controls ADO #134482/#134630 name explicitly.
    NAMED_CONTROL_LOCATORS = (HIGH_CONTRAST_SWITCH, ZOOM_IN_BUTTON, ZOOM_OUT_BUTTON, RESET_BUTTON)
    # EVERY distinct interactive tool control the live panel actually renders
    # (includes Dark Mode + Done -- see module docstring's #134630 finding).
    ALL_TOOL_CONTROL_LOCATORS = (DARK_MODE_SWITCH, HIGH_CONTRAST_SWITCH, ZOOM_OUT_BUTTON,
                                  ZOOM_IN_BUTTON, RESET_BUTTON, DONE_BUTTON)

    # Batch B: a real, distinct second content page -- confirmed live via the
    # header's own "Contact us" nav link's `href` (see module docstring).
    # Reached by direct URL, not HeaderComponent.NAV_LINK_CONTACT_US (that
    # locator is anchored to the English text "Contact us" -- unusable, and a
    # violation of this project's RTL rule, "never locate by visible Arabic
    # text", under the Arabic locale ADO #134662 needs).
    CONTACT_US_PATH = "/web/qatar-chamber/contact-us"

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)
        self._console_messages = []
        self._blocked_request_count = 0

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "AccessibilityToolsComponent":
        self.header.open_home()
        return self

    def open_home_arabic(self) -> "AccessibilityToolsComponent":
        """Loads the homepage directly on the Arabic locale
        (`web_url("/home", locale="ar")` -> `/ar/home`) -- mirrors
        LanguageSwitcherComponent.open_home_arabic()'s pattern for its own PBI
        (ADO #134636, #134666)."""
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.header.HEADER)
        return self

    def open_second_content_page(self, locale: str = "en") -> "AccessibilityToolsComponent":
        """Navigates to a real, distinct second content page (Contact Us) by
        direct URL -- confirms a toggled setting (e.g. High Contrast) is
        genuinely persistent across a real navigation, not merely in-memory
        state a fresh page load would wipe (ADO #134661, #134662)."""
        self.open(web_url(self.CONTACT_US_PATH, locale=locale))
        self.wait_for(self.header.HEADER)
        return self

    def current_url(self) -> str:
        return self.page.url

    # ── Icon visibility / position (ADO #134481, #134628) ───────────────
    def is_accessibility_button_visible(self) -> bool:
        return self.header.is_accessibility_button_visible()

    def is_accessibility_button_in_utility_cluster(self) -> bool:
        """True if the accessibility button sits in the same header row
        (same y-position, small tolerance) as the language switcher and
        search icon -- the concrete, position-based stand-in for ADO
        #134481's "next to search icon and EN/AR toggle" step."""
        a11y_box = self.page.locator(self.header.ACCESSIBILITY_BUTTON).bounding_box()
        lang_box = self.page.locator(self.header.LANGUAGE_SWITCHER).bounding_box()
        search_box = self.page.locator(self.header.SEARCH_BUTTON).bounding_box()
        if not (a11y_box and lang_box and search_box):
            return False
        ys = [a11y_box["y"], lang_box["y"], search_box["y"]]
        return max(ys) - min(ys) < 5

    def accessibility_button_box_and_style(self) -> dict:
        """{width, height, padding, borderRadius, backgroundColor} of the
        rendered accessibility button -- used for ADO #134628's exact
        desktop-viewport style check."""
        loc = self.page.locator(self.header.ACCESSIBILITY_BUTTON)
        box = loc.bounding_box()
        style = loc.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {padding: cs.padding, borderRadius: cs.borderRadius, backgroundColor: cs.backgroundColor}; }"
        )
        size = {"width": round(box["width"]), "height": round(box["height"])} if box else {}
        return {**size, **style}

    # ── Open / close the panel (ADO #134482, #134483) ───────────────────
    def click_accessibility_button(self) -> "AccessibilityToolsComponent":
        self.click(self.header.ACCESSIBILITY_BUTTON)
        return self

    def is_panel_open(self) -> bool:
        return self.is_visible(self.PANEL)

    def panel_dom_instance_count(self) -> int:
        """Number of `.qc-a11y-panel` nodes in the DOM, regardless of
        visibility -- stays 1 across repeated open/close (see module
        docstring); more than 1 would indicate duplicated/orphaned panel
        markup (ADO #134484)."""
        return self.page.locator(self.PANEL).count()

    # ── Named-control presence (ADO #134482) ─────────────────────────────
    def are_named_controls_visible(self) -> dict:
        return {
            "high_contrast": self.is_visible(self.HIGH_CONTRAST_SWITCH),
            "zoom_in": self.is_visible(self.ZOOM_IN_BUTTON),
            "zoom_out": self.is_visible(self.ZOOM_OUT_BUTTON),
            "reset": self.is_visible(self.RESET_BUTTON),
        }

    # ── High Contrast toggle (ADO #134486) ──────────────────────────────
    def is_high_contrast_toggle_visible(self) -> bool:
        return self.is_visible(self.HIGH_CONTRAST_SWITCH)

    def high_contrast_toggle_state(self) -> str:
        return self.page.locator(self.HIGH_CONTRAST_SWITCH).get_attribute("aria-checked")

    def high_contrast_row_label_text(self) -> str:
        return self.page.locator(self.HIGH_CONTRAST_ROW_LABEL).inner_text().strip()

    # ── Zoom In / Zoom Out buttons (ADO #134487) ─────────────────────────
    def is_zoom_in_visible(self) -> bool:
        return self.is_visible(self.ZOOM_IN_BUTTON)

    def is_zoom_out_visible(self) -> bool:
        return self.is_visible(self.ZOOM_OUT_BUTTON)

    def is_zoom_in_enabled(self) -> bool:
        return self.page.locator(self.ZOOM_IN_BUTTON).is_enabled()

    def is_zoom_out_enabled(self) -> bool:
        return self.page.locator(self.ZOOM_OUT_BUTTON).is_enabled()

    # ── Reset / Normal View control (ADO #134488) ────────────────────────
    def is_reset_visible(self) -> bool:
        return self.is_visible(self.RESET_BUTTON)

    def is_reset_enabled(self) -> bool:
        return self.page.locator(self.RESET_BUTTON).is_enabled()

    # ── Exactly-4-controls / no-overlap (ADO #134630) ────────────────────
    def panel_tool_control_count(self) -> int:
        """Count of visible tool controls among ALL_TOOL_CONTROL_LOCATORS
        (6 live) -- see module docstring's #134630 finding: the case states
        the panel opens with exactly 4."""
        return sum(1 for loc in self.ALL_TOOL_CONTROL_LOCATORS if self.is_visible(loc))

    def named_controls_have_no_overlap(self) -> bool:
        """True if none of the 4 named controls' (High Contrast, Zoom In,
        Zoom Out, Reset) bounding boxes overlap each other."""
        boxes = []
        for loc in self.NAMED_CONTROL_LOCATORS:
            box = self.page.locator(loc).bounding_box()
            if box:
                boxes.append(box)
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if self._boxes_overlap(boxes[i], boxes[j]):
                    return False
        return True

    @staticmethod
    def _boxes_overlap(a: dict, b: dict) -> bool:
        return not (
            a["x"] + a["width"] <= b["x"] or b["x"] + b["width"] <= a["x"]
            or a["y"] + a["height"] <= b["y"] or b["y"] + b["height"] <= a["y"]
        )

    # ── Simulated panel-open failure (ADO #134484) ───────────────────────
    # The two real, distinct script+style bundles the live site fetches
    # during initial page load to back the accessibility panel and its
    # keyboard-nav companion feature (confirmed live -- see module
    # docstring). Blocking exactly these is a genuine, literal way to
    # produce ADO #134484's "blocked script" precondition, not a guess.
    A11Y_SCRIPT_BUNDLE_PATTERNS = ("**/o/qc-accessibility-tools/**", "**/o/qc-a11y-keyboard/**")

    def start_open_failure_simulation(self) -> "AccessibilityToolsComponent":
        """Genuine simulation of ADO #134484's precondition ("blocked
        script/network stall"): aborts the two real accessibility-feature
        script/style bundles (A11Y_SCRIPT_BUNDLE_PATTERNS) and records every
        console message. MUST be called before open_home() -- both the
        bundles and the routes only take effect on requests issued after
        registration, and the bundles are fetched during the INITIAL page
        load, not on click (see module docstring).

        Confirmed live: blocking them fires 4 real `net::ERR_FAILED` console
        errors DURING THE LOAD (before any click), and the panel
        subsequently never mounts at all when the icon is clicked. Use
        console_message_count() to snapshot a baseline right after
        open_home(), then console_error_count_since(baseline) after the
        click, to measure errors the CLICK ITSELF introduces -- separately
        from the load-time errors this simulation deliberately causes."""
        self._console_messages = []
        self._blocked_request_count = 0
        self.page.on("console", lambda msg: self._console_messages.append((msg.type, msg.text)))

        def _abort(route):
            self._blocked_request_count += 1
            route.abort()

        for pattern in self.A11Y_SCRIPT_BUNDLE_PATTERNS:
            self.page.route(pattern, _abort)
        return self

    def console_message_count(self) -> int:
        return len(self._console_messages)

    def console_error_count_since(self, baseline_count: int) -> int:
        """Count of `error`-type console messages recorded AFTER
        `baseline_count` messages had already been seen -- isolates errors
        caused by an action (e.g. the icon click) from ones already present
        beforehand (e.g. this simulation's own load-time blocked-resource
        errors, or pre-existing site noise)."""
        return sum(1 for msg_type, _ in self._console_messages[baseline_count:] if msg_type == "error")

    def blocked_request_count(self) -> int:
        return self._blocked_request_count

    # ── Keyboard focus (ADO #134490) ─────────────────────────────────────
    def focus_accessibility_button_via_tab(self, max_presses: int = 40) -> bool:
        return self.press_tab_until_focused(self.header.ACCESSIBILITY_BUTTON, max_presses=max_presses)

    def accessibility_button_outline_style(self) -> dict:
        """{outlineStyle, outlineWidth, boxShadow} of the accessibility
        button, read regardless of focus state -- factored out of
        is_accessibility_button_focus_indicator_visible() so ADO #134633 can
        read and compare the UNFOCUSED style against the focused one (the
        case's own "distinguishable from unfocused state" wording), not just
        assert a bare bool."""
        return self.page.locator(self.header.ACCESSIBILITY_BUTTON).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {outlineStyle: cs.outlineStyle, outlineWidth: cs.outlineWidth, boxShadow: cs.boxShadow}; }"
        )

    def is_accessibility_button_focus_indicator_visible(self) -> bool:
        """True only if the accessibility button is BOTH the focused element
        AND rendering a visible focus indicator (outline or box-shadow) --
        mirrors HeaderComponent.is_logo_focus_indicator_visible()'s
        contract."""
        if not self.is_focused(self.header.ACCESSIBILITY_BUTTON):
            return False
        style = self.accessibility_button_outline_style()
        has_outline = style["outlineStyle"] not in ("none", "") and style["outlineWidth"] != "0px"
        has_box_shadow = style["boxShadow"] not in ("none", "")
        return has_outline or has_box_shadow

    def activate_focused_accessibility_button_via_keyboard(self) -> bool:
        """Presses Enter on the currently-focused accessibility button and
        reports whether the panel opened as a result. Only meaningful when
        focus_accessibility_button_via_tab() returned True first; never
        throws (bounded wait, mirrors is_visible()'s never-throws contract)."""
        self.press_key("Enter")
        try:
            self.page.locator(self.PANEL).wait_for(state="visible", timeout=3000)
        except Exception:  # noqa: BLE001 — never throws, mirrors is_visible()'s contract
            return False
        return self.is_panel_open()

    # ── Batch B ═══════════════════════════════════════════════════════════

    # ── Mobile viewport: icon (ADO #134629) ──────────────────────────────
    def is_accessibility_button_overlapping_language_switcher(self) -> bool:
        """True if the accessibility icon's box overlaps the language
        switcher's box -- reuses _boxes_overlap() (already established for
        the panel's named-controls overlap check, ADO #134630)."""
        a11y_box = self.page.locator(self.header.ACCESSIBILITY_BUTTON).bounding_box()
        lang_box = self.page.locator(self.header.LANGUAGE_SWITCHER).bounding_box()
        if not (a11y_box and lang_box):
            return False
        return self._boxes_overlap(a11y_box, lang_box)

    # ── Mobile viewport: panel layout (ADO #134631) ──────────────────────
    def has_page_horizontal_overflow(self) -> bool:
        """True if the document is wider than the viewport (would produce a
        horizontal scrollbar) -- confirmed live at 375x812 to read False both
        with the panel closed and open (see module docstring)."""
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def panel_controls_fit_within_viewport(self) -> bool:
        """True if every visible tool control's box (ALL_TOOL_CONTROL_LOCATORS
        -- all 6 live controls, see batch-A's #134630 finding) sits fully
        within the current viewport's horizontal bounds -- the concrete,
        geometry-based stand-in for "no ... clipped controls" on a narrow
        mobile viewport."""
        viewport = self.page.viewport_size
        if not viewport:
            return False
        for loc in self.ALL_TOOL_CONTROL_LOCATORS:
            if not self.is_visible(loc):
                continue
            box = self.page.locator(loc).bounding_box()
            if not box:
                continue
            if box["x"] < 0 or box["x"] + box["width"] > viewport["width"]:
                return False
        return True

    # ── High Contrast: activation, persistence, WCAG audit (ADO #134632,
    #    #134661, #134662) ───────────────────────────────────────────────
    def activate_high_contrast(self) -> "AccessibilityToolsComponent":
        self.click(self.HIGH_CONTRAST_SWITCH)
        return self

    def is_high_contrast_active(self) -> bool:
        """True if `<html>` carries the `qc-a11y-contrast` class -- the real,
        CLI-confirmed mechanism the toggle uses (NOT a body/data attribute;
        see module docstring), read via `document.documentElement.className`
        rather than a `page.locator("html")` constant (kept out of the
        locator table -- "html" is not a feature-specific element)."""
        class_name = self.page.evaluate("() => document.documentElement.className") or ""
        return "qc-a11y-contrast" in class_name

    def page_background_color(self) -> str:
        return self.page.evaluate("() => getComputedStyle(document.body).backgroundColor")

    def run_color_contrast_audit(self) -> list:
        """Runs a REAL axe-core accessibility audit (axe-playwright-python),
        scoped to the `color-contrast` rule only, against the page's CURRENT
        state -- call after activate_high_contrast() for ADO #134632. Returns
        the raw list of violation dicts (each carries 'id'/'impact'/'nodes');
        an empty list is a genuine, observed 0-violations result, never
        assumed (confirmed live: 0 violations on the EN homepage with High
        Contrast active -- see module docstring)."""
        axe = Axe()
        results = axe.run(self.page, options={"runOnly": {"type": "rule", "values": ["color-contrast"]}})
        return results.response["violations"]

    # ── Zoom In / Zoom Out labels (ADO #134634) ──────────────────────────
    def zoom_in_label(self) -> str:
        return self.page.locator(self.ZOOM_IN_BUTTON).inner_text().strip()

    def zoom_out_label(self) -> str:
        return self.page.locator(self.ZOOM_OUT_BUTTON).inner_text().strip()

    # ── Reset persistence across state changes (ADO #134635) ─────────────
    def click_zoom_in(self) -> "AccessibilityToolsComponent":
        self.click(self.ZOOM_IN_BUTTON)
        return self

    def zoom_value_text(self) -> str:
        return self.page.locator(self.ZOOM_VALUE).inner_text().strip()

    def close_panel(self) -> "AccessibilityToolsComponent":
        self.click(self.PANEL_CLOSE_BUTTON)
        return self

    # ── RTL utility-cluster mirroring (ADO #134636, #134666) ─────────────
    def utility_cluster_x_positions(self) -> dict:
        switcher = self.page.locator(self.header.LANGUAGE_SWITCHER).bounding_box()
        accessibility = self.page.locator(self.header.ACCESSIBILITY_BUTTON).bounding_box()
        search = self.page.locator(self.header.SEARCH_BUTTON).bounding_box()
        return {
            "language_switcher": switcher["x"] if switcher else None,
            "accessibility": accessibility["x"] if accessibility else None,
            "search": search["x"] if search else None,
        }

    def is_utility_cluster_mirrored_rtl(self) -> bool:
        """True if the 3-icon utility cluster (language switcher,
        accessibility icon, search icon) reads in the fully mirrored RTL
        order search < accessibility < switcher (left-to-right) -- the exact
        reverse of the LTR order switcher < accessibility < search already
        confirmed live in header_component.py's own docstring (ADO #134239/
        #134428) -- while still sharing the SAME header row (reuses
        is_accessibility_button_in_utility_cluster()'s y-alignment check), so
        a genuinely dropped/stray LTR-leftover element would fail this too."""
        positions = self.utility_cluster_x_positions()
        xs = (positions["search"], positions["accessibility"], positions["language_switcher"])
        if any(x is None for x in xs):
            return False
        return self.is_accessibility_button_in_utility_cluster() and xs[0] < xs[1] < xs[2]

    # ── Dark Mode: activation, icon/panel legibility (ADO #134665, #134666) ──
    def switch_to_dark_mode(self) -> "AccessibilityToolsComponent":
        self.click(self.DARK_MODE_SWITCH)
        return self

    def dark_mode_toggle_state(self) -> str:
        return self.page.locator(self.DARK_MODE_SWITCH).get_attribute("aria-checked")

    def header_background_color(self) -> str:
        """Reads via HeaderComponent.container_style() (composed, not
        re-declared) -- the same background-color source ADO #134665/#134666
        need to confirm the icon still contrasts against."""
        return self.header.container_style()["backgroundColor"]

    def accessibility_button_border_color(self) -> str:
        """Confirmed live to be the actual mechanism that keeps the icon
        distinguishable in dark mode: border-color shifts from
        rgb(231,231,237) (light) to rgba(255,255,255,0.12) (dark) even
        though the icon's own background stays close in value to the new
        header background -- see module docstring."""
        return self.page.locator(self.header.ACCESSIBILITY_BUTTON).evaluate(
            "el => getComputedStyle(el).borderColor"
        )

    def accessibility_button_x_position(self):
        box = self.page.locator(self.header.ACCESSIBILITY_BUTTON).bounding_box()
        return box["x"] if box else None

    def panel_direction(self) -> str:
        return self.page.locator(self.PANEL).evaluate("el => getComputedStyle(el).direction")

    def named_controls_legible_against_panel_background(self) -> bool:
        """True if every one of the 4 NAMED controls (High Contrast, Zoom In,
        Zoom Out, Reset -- ADO #134665's own literal "4 controls" wording;
        see batch-A's #134630 finding that the live panel actually renders 6,
        same coverage flag applies here) reads a text color genuinely
        distinct from its EFFECTIVE background -- falling back to the
        panel's own background when a control's own background is
        transparent (confirmed live for the Reset button, which renders on a
        transparent background that visually resolves to the panel's dark
        background). This is a real, honest "not the same tone" signal, NOT
        a WCAG contrast-ratio calculation -- that is #134632's dedicated axe
        audit (run_color_contrast_audit())."""
        panel_bg = self.page.locator(self.PANEL).evaluate("el => getComputedStyle(el).backgroundColor")
        transparent = ("rgba(0, 0, 0, 0)", "transparent")
        for loc in self.NAMED_CONTROL_LOCATORS:
            style = self.page.locator(loc).evaluate(
                "el => { const cs = getComputedStyle(el); "
                "return {color: cs.color, backgroundColor: cs.backgroundColor}; }"
            )
            if style["color"] in transparent:
                return False
            effective_bg = style["backgroundColor"] if style["backgroundColor"] not in transparent else panel_bg
            if style["color"] == effective_bg:
                return False
        return True

"""
web/pages/header/accessibility_page.py — AccessibilityPage.

Public-facing header Accessibility Tools icon + panel (PBI 133381
"QC-GBL-003 — Accessibility Tools"). Same header, same PBI-header context as
LanguageSwitcherPage — kept as its own module per automation-standards.md
("one class per page/screen/component"): the switcher and the accessibility
widget are two distinct business objects that merely happen to render in the
same `<header>` row.

Locators extracted CLI-first via tools/extract_locators.py:

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --scope header

which returned the accessibility icon itself as a unique role candidate
(`get_by_role("button", name="Accessibility tools")`) but the CLI hit the
same "developer mode connection limit" redirect (disclosed in
footer_page.py / language_switcher_page.py) before it could harvest the
*panel* markup, because the panel only exists in the DOM after the icon is
clicked — a stateful, post-interaction element the one-shot extractor
script can't reach. Per automation-standards.md's fallback rule, the panel
was inspected via the disclosed Playwright-MCP fallback: after following
the one-time reset link, the icon was clicked and the resulting
`div.qc-a11y-panel` was read via `browser_evaluate` (scoped outerHTML):

    header button.qc-accessibility-btn[aria-label="Accessibility tools"]  - icon (32x32, header row)
    div.qc-a11y-panel[role="dialog"][aria-label="Accessibility"]          - panel root
    button.qc-a11y-close[aria-label="Close"]                             - panel close (X)
    button[data-qc-a11y-dark][role="switch"]                             - "Dark mode" toggle
    button[data-qc-a11y-contrast][role="switch"]                         - "High contrast" toggle
    span[data-qc-a11y-zoom-value]                                        - current zoom %, e.g. "100%"
    button[data-qc-a11y-zoom-out]                                        - "Zoom out" (−)
    button[data-qc-a11y-zoom-in]                                         - "Zoom in" (+)
    button.qc-a11y-reset[data-qc-a11y-reset]                             - "Reset"
    button.qc-a11y-done[data-qc-a11y-done]                               - "Done"

Confirmed live behaviour (no page reload, instant, all via the disclosed
MCP interaction — never a naive full-DOM dump):
  - Clicking `[data-qc-a11y-contrast]` toggles `aria-checked` and adds/removes
    the `qc-a11y-contrast` class on `<html>` (body background flips to
    rgb(0,0,0) with the class applied) — no `data-theme` change.
  - Clicking `[data-qc-a11y-zoom-in]`/`-zoom-out` steps the zoom value text by
    10 percentage points (100% -> 110%) and mirrors the same ratio into an
    inline CSS custom property on `<html>`: `--qc-a11y-zoom-scale`.
  - Clicking `.qc-a11y-reset` clears both the contrast class and the zoom
    style var back to defaults in place, no navigation.
  - No dedicated accessibility-state entry was found in `localStorage`/
    `sessionStorage`/`document.cookie` in this dev build (only an unrelated
    `LFR_SESSION_STATE_*` key and a `qcTheme=light` cookie) — flagged here so
    the cross-page-persistence assertions (TC-011) are honest about what is
    actually observable in this build, not asserted against a state store
    that doesn't exist.

Assumption disclosed per GLOBAL-ACCESSIBILITY-TC-001's own expected result
("exact icon glyph is structurally present but not verified pixel-for-pixel"):
this Page Object asserts on the stable DOM hooks above, never on the SVG
glyph's path data.

No TODO(locator) remains for anything on the public icon/panel — every
element the approved cases reference on the live widget was reachable and
resolved to a real, unique selector.
"""

from config.settings import web_url
from core.web.base_page import BasePage

HOME_URL = web_url("/home")


class AccessibilityPage(BasePage):
    # ---- Structure -----------------------------------------------------
    HEADER = "header.qc-global-site-header"
    ICON = 'header button.qc-accessibility-btn[aria-label="Accessibility tools"]'

    # ---- Panel ------------------------------------------------------------
    PANEL = 'div.qc-a11y-panel[role="dialog"]'
    PANEL_CLOSE = "button.qc-a11y-close"
    DARK_MODE_SWITCH = "[data-qc-a11y-dark]"
    HIGH_CONTRAST_SWITCH = "[data-qc-a11y-contrast]"
    ZOOM_VALUE = "[data-qc-a11y-zoom-value]"
    ZOOM_OUT_BUTTON = "[data-qc-a11y-zoom-out]"
    ZOOM_IN_BUTTON = "[data-qc-a11y-zoom-in]"
    RESET_BUTTON = "button.qc-a11y-reset"
    DONE_BUTTON = "button.qc-a11y-done"

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def open_home(self, url: str = HOME_URL) -> "AccessibilityPage":
        self.open(url)
        self.wait_for(self.HEADER)
        return self

    def navigate_via_header_link(self, link_text: str) -> "AccessibilityPage":
        self.click(f'header a.qc-nav-link:has-text("{link_text}")')
        self.wait_for(self.HEADER)
        return self

    # ------------------------------------------------------------------
    # Icon
    # ------------------------------------------------------------------
    def is_icon_visible(self) -> bool:
        return self.is_visible(self.ICON)

    def click_icon(self) -> "AccessibilityPage":
        self.click(self.ICON)
        return self

    def icon_style(self) -> dict:
        return self.page.locator(self.ICON).evaluate(
            "el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); "
            "return {width: r.width, height: r.height, padding: cs.padding, "
            "borderRadius: cs.borderRadius, backgroundColor: cs.backgroundColor}; }"
        )

    def focus_icon_via_tab(self) -> bool:
        return self.press_tab_until_focused(self.ICON)

    def is_icon_focused(self) -> bool:
        return self.is_focused(self.ICON)

    def icon_outline_on_focus(self) -> str:
        return self.page.locator(self.ICON).evaluate(
            "el => { const cs = getComputedStyle(el); return cs.outlineStyle + ' ' + cs.outlineWidth + ' ' + cs.boxShadow; }"
        )

    def icon_overlaps_switcher(self, switcher_locator: str = "header a.qc-lang-switcher") -> bool:
        return self.page.locator(self.ICON).evaluate(
            "(el, sel) => { const a = el.getBoundingClientRect(); const b = document.querySelector(sel).getBoundingClientRect(); "
            "return !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom); }",
            switcher_locator,
        )

    # ------------------------------------------------------------------
    # Panel
    # ------------------------------------------------------------------
    def is_panel_open(self) -> bool:
        return self.is_visible(self.PANEL)

    def close_panel_via_close_button(self) -> "AccessibilityPage":
        self.click(self.PANEL_CLOSE)
        return self

    def close_panel_via_done(self) -> "AccessibilityPage":
        self.click(self.DONE_BUTTON)
        return self

    def panel_control_count(self) -> int:
        """Counts the panel's interactive controls that map to the case's
        '4 required controls' — High Contrast, Zoom In, Zoom Out, Reset —
        by their stable data-qc-a11y-* hooks (excludes Close/Done/Dark
        mode, which are extra controls this dev build renders beyond the
        4 the case enumerates; see the module docstring)."""
        selectors = [self.HIGH_CONTRAST_SWITCH, self.ZOOM_IN_BUTTON, self.ZOOM_OUT_BUTTON, self.RESET_BUTTON]
        return sum(1 for sel in selectors if self.is_visible(sel))

    def is_panel_no_horizontal_overflow(self) -> bool:
        return self.page.locator(self.PANEL).evaluate(
            "el => el.scrollWidth <= el.clientWidth + 1"
        )

    # ------------------------------------------------------------------
    # High contrast
    # ------------------------------------------------------------------
    def is_high_contrast_active(self) -> bool:
        return self.page.locator(self.HIGH_CONTRAST_SWITCH).get_attribute("aria-checked") == "true"

    def click_high_contrast(self) -> "AccessibilityPage":
        self.click(self.HIGH_CONTRAST_SWITCH)
        return self

    def body_background_color(self) -> str:
        return self.page.evaluate("() => getComputedStyle(document.body).backgroundColor")

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------
    def zoom_value_text(self) -> str:
        return self.text(self.ZOOM_VALUE)

    def zoom_scale(self) -> float:
        style = self.page.evaluate("() => document.documentElement.style.getPropertyValue('--qc-a11y-zoom-scale')")
        return float(style) if style else 1.0

    def click_zoom_in(self) -> "AccessibilityPage":
        self.click(self.ZOOM_IN_BUTTON)
        return self

    def click_zoom_out(self) -> "AccessibilityPage":
        self.click(self.ZOOM_OUT_BUTTON)
        return self

    def is_zoom_in_enabled(self) -> bool:
        return self.page.locator(self.ZOOM_IN_BUTTON).is_enabled()

    def is_zoom_out_enabled(self) -> bool:
        return self.page.locator(self.ZOOM_OUT_BUTTON).is_enabled()

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------
    def click_reset(self) -> "AccessibilityPage":
        self.click(self.RESET_BUTTON)
        return self

    def is_reset_enabled(self) -> bool:
        return self.page.locator(self.RESET_BUTTON).is_enabled()

    # ------------------------------------------------------------------
    # DOM-reload marker (proves "no page reload" across an interaction chain)
    # ------------------------------------------------------------------
    def set_dom_marker(self) -> str:
        return self.page.evaluate(
            "() => { const m = 'qc-a11y-marker-' + Date.now() + '-' + Math.random(); "
            "document.documentElement.setAttribute('data-qc-marker', m); return m; }"
        )

    def dom_marker(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('data-qc-marker')")

    # ------------------------------------------------------------------
    # RTL
    # ------------------------------------------------------------------
    def is_rtl(self) -> bool:
        return self.page.evaluate("() => document.documentElement.dir === 'rtl'")

    def icon_bounding_x(self) -> float:
        return self.page.locator(self.ICON).evaluate("el => el.getBoundingClientRect().x")

    def switcher_bounding_x(self, switcher_locator: str = "header a.qc-lang-switcher") -> float:
        return self.page.locator(switcher_locator).evaluate("el => el.getBoundingClientRect().x")

    # ------------------------------------------------------------------
    # Contrast audit (WCAG 2.1 AA) — requires axe-playwright-python.
    # See requirements.txt / test module docstring: this dependency is NOT
    # installed in this authoring session (disclosed), so this method is
    # scripted against the documented API (docs.pamelafox.github.io/
    # axe-playwright-python) but has not been import-checked here.
    # ------------------------------------------------------------------
    def run_contrast_audit(self) -> dict:
        from axe_playwright_python.sync_playwright import Axe

        axe = Axe()
        results = axe.run(self.page, options={"runOnly": {"type": "rule", "values": ["color-contrast"]}})
        return results.response

    def contrast_violation_count(self) -> int:
        response = self.run_contrast_audit()
        return len(response.get("violations", []))

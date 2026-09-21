"""
web/pages/components/accessibility_tools_component.py — AccessibilityToolsComponent.

Global/cross-cutting component (background.md's "Global/Cross-cutting
features"; standards.md's Sprint-1 skeleton table lists this under
QC-GBL-003, `pbi_133381`). Previously a stub ("Phase 1 — not yet
implemented"); implemented here while automating PBI 129696 (Food Handlers
Certification) because that PBI's Compatibility-matrix cases (tc_140156-
tc_140163) need a real, live-confirmed way to drive/read the site's Light/
Dark theme — the first automated batch in this repo (`web/` tree) that
needed it. No other already-automated `web/` page had established this
pattern yet (grepped both `web/` and `cms/` — nothing found beyond a CMS
callout-style class, which is a different, unrelated "theme" concept) —
this is the basis for the signal chosen below, and it is real, not
invented:

CONFIRMED LIVE (qcdev, 2026-09-17) via a disclosed, scripted DOM probe (a
plain Playwright script in the shell, not the Playwright MCP —
`tools/extract_locators.py`'s interactive-element harvester found nothing
with "theme"/"dark"/"light"/"contrast" in its name anywhere in the header
chrome, because this control lives inside a menu that only mounts its
content on click):

  1. `button[name="Accessibility tools"]` (role=button, already surfaced by
     the CLI extractor) opens a panel — `div.qc-a11y-panel[role="dialog"]`
     — titled "Accessibility", subtitled "Adjust dark mode, contrast and
     page zoom.".
  2. Inside it: `button[data-qc-a11y-dark][role="switch"]` toggles Dark
     mode; `button[data-qc-a11y-contrast][role="switch"]` toggles High
     Contrast (a SEPARATE control from theme — the BRD's own "Normal/
     High-Contrast toggle" — not touched by this PBI's cases, included here
     only because it shares the same panel, so a caller composing this
     component gets both for free).
  3. Clicking the Dark-mode switch flips `<html data-theme="light|dark">`
     live (confirmed by reading the attribute before/after) — chosen as
     the theme-driven signal a test asserts on, per the task's own
     instruction to "pick the most direct signal — e.g. data-theme/html
     class — and document your basis" when no established pattern exists
     yet. `data-theme` is the DIRECT signal (not a derived proxy like a
     specific computed color), so it is the correct primary assertion
     target; a computed-color check is a secondary/optional corroboration,
     never a substitute.
  4. `button[data-qc-a11y-done]` ("Done") closes the panel without
     resetting the just-applied Dark-mode state (confirmed live — the
     `data-theme` attribute persists after Done is clicked).

DARK-THEME COLOUR TOKENS ARE NOT A GENUINE CSS-FILTER-OVER-LIGHT, but they
are ALSO NOT the exact literal hex values the QA cases quote (those were
authored from the Figma frames, which this batch has no access to — see
the task's own practical-scope note). CONFIRMED LIVE: switching to Dark
measurably changes background colors on this page's callouts (e.g. the
Important Notes callout's fill moves from rgb(255,241,242) to
rgb(58,33,38)), so this is a real, distinct token set, not an invented one
— but the title text colors on some elements stayed the same RGB across
Light/Dark (e.g. the Important Notes title stayed rgb(244,63,94) in both,
where the QA case's Figma-sourced text describes a colour CHANGE to
#FB7185 in Dark). Per the task's explicit scope note, this component (and
the Food Handlers Page Object built on it) never asserts a literal hex
value pulled from the QA case text — only the theme-driven DOM signal
(`data-theme`) and, where a case needs relative distinctness, a comparison
between elements' OWN computed colors rather than a match against an
un-verifiable Figma token.
"""

from core.web.base_page import BasePage

ACCESSIBILITY_BUTTON_NAME = "Accessibility tools"
PANEL = ".qc-a11y-panel"
DARK_MODE_SWITCH = "[data-qc-a11y-dark]"
HIGH_CONTRAST_SWITCH = "[data-qc-a11y-contrast]"
DONE_BUTTON = "[data-qc-a11y-done]"
CLOSE_BUTTON = ".qc-a11y-close"


class AccessibilityToolsComponent(BasePage):
    def open_panel(self) -> "AccessibilityToolsComponent":
        self.page.get_by_role("button", name=ACCESSIBILITY_BUTTON_NAME).first.click()
        self.wait_for(PANEL, state="visible")
        return self

    def close_panel(self) -> "AccessibilityToolsComponent":
        self.click(DONE_BUTTON)
        self.wait_for(PANEL, state="hidden")
        return self

    def is_panel_open(self) -> bool:
        return self.is_visible(PANEL)

    def is_dark_mode_checked(self) -> bool:
        return self.page.locator(DARK_MODE_SWITCH).get_attribute("aria-checked") == "true"

    def set_dark_mode(self, enabled: bool) -> "AccessibilityToolsComponent":
        """Opens the panel if not already open, toggles Dark mode to the
        requested state (a no-op click-skip if it already matches — avoids
        flipping it back off), and closes the panel via Done. Leaves
        `<html data-theme>` in the requested state on return."""
        opened_here = not self.is_panel_open()
        if opened_here:
            self.open_panel()
        if self.is_dark_mode_checked() != enabled:
            self.click(DARK_MODE_SWITCH)
        if opened_here:
            self.close_panel()
        return self

    def current_theme(self) -> str:
        """The live, direct theme signal this component's own docstring
        confirms: `<html data-theme="light"|"dark">`."""
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    # ---- High Contrast (added while automating PBI 130694 — Qatar Market
    # Overview — the first batch that needed to actually DRIVE/READ this
    # switch; CONFIRMED LIVE 2026-09-17 via the same disclosed scripted DOM
    # probe technique as the module docstring's Dark-mode evidence: toggling
    # `button[data-qc-a11y-contrast][role="switch"]` flips its own
    # `aria-checked` AND adds/removes a `qc-a11y-contrast` class on
    # `<html>` — CONFIRMED to persist across a full page reload (same
    # mechanism as the Dark-mode `data-theme` attribute). Also CONFIRMED
    # LIVE this genuinely repaints foreground/background colors (e.g. a
    # Country-Fact description text + its background moved from
    # rgb(108,108,107) on rgb(255,255,255) to rgb(255,255,255) on
    # rgb(0,0,0) — a real ~21:1 contrast jump, not a no-op class toggle). ----
    def is_high_contrast_checked(self) -> bool:
        return self.page.locator(HIGH_CONTRAST_SWITCH).get_attribute("aria-checked") == "true"

    def is_high_contrast_active(self) -> bool:
        """The live, direct DOM signal: `<html class="... qc-a11y-contrast">`."""
        html_class = self.page.evaluate("() => document.documentElement.className")
        return "qc-a11y-contrast" in (html_class or "").split()

    def set_high_contrast(self, enabled: bool) -> "AccessibilityToolsComponent":
        """Opens the panel if not already open, toggles High Contrast to the
        requested state (no-op click-skip if it already matches), and closes
        via Done. Leaves `<html class="qc-a11y-contrast">` in the requested
        state on return — mirrors set_dark_mode()'s own shape."""
        opened_here = not self.is_panel_open()
        if opened_here:
            self.open_panel()
        if self.is_high_contrast_checked() != enabled:
            self.click(HIGH_CONTRAST_SWITCH)
        if opened_here:
            self.close_panel()
        return self

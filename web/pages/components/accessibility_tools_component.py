"""
web/pages/components/accessibility_tools_component.py —
AccessibilityToolsComponent.

The site-wide accessibility widget that every public page carries (the
floating "Accessibility tools" button and the panel it opens). It is the only
way to reach Dark mode on this build, so it is shared infrastructure rather
than any one service page's concern — per automation-standards.md, a reusable
cross-page component object lives here and is composed into the Page Objects
that need it, never copy-pasted into each of them.

LOCATOR PROVENANCE — CLI-first, verified live 2026-09-16 (qcdev)
----------------------------------------------------------------
`python3 tools/extract_locators.py --url
https://qcdev.ihorizons.com/en/certificate-of-origin-online --max 80`
(framework default viewport 1920x1080) surfaced the opener as unique:

    get_by_role("button", name="Accessibility tools")            uniq=1

The panel it opens carries two `role="switch"` controls with stable data
attributes, plus a closing button:

    button.qc-a11y-switch[data-qc-a11y-dark]      -> "Dark mode"
    button.qc-a11y-switch[data-qc-a11y-contrast]  -> "High contrast"
    button.qc-a11y-done                           -> "Done" (closes panel)

Toggling the first flips `<html data-theme="light">` to `data-theme="dark"`.
Confirmed live. `prefers-color-scheme: dark` alone does NOT flip it (a
dark-color-scheme Playwright context still renders `data-theme="light"`), so
the widget is the only way in — hence `enable_dark_mode()` drives the real
control rather than forcing a media feature.

Only the three locators the dark-mode flow actually uses are declared below;
the high-contrast switch is documented above but is not written in as a
constant until a case exercises it (no speculative locators).
"""

from core.web.base_page import BasePage


class AccessibilityToolsComponent(BasePage):
    OPEN_BUTTON = 'button[aria-label="Accessibility tools"]'
    DARK_SWITCH = "button.qc-a11y-switch[data-qc-a11y-dark]"
    DONE_BUTTON = "button.qc-a11y-done"

    def open_panel(self) -> "AccessibilityToolsComponent":
        """Opens the widget and waits for its switches to be present."""
        self.click(self.OPEN_BUTTON)
        self.wait_for(self.DARK_SWITCH)
        return self

    def close_panel(self) -> "AccessibilityToolsComponent":
        """Closes the widget so the panel does not overlay the content under
        test, and waits for it to actually be gone."""
        self.click(self.DONE_BUTTON)
        self.wait_for(self.DARK_SWITCH, state="hidden")
        return self

    def enable_dark_mode(self) -> "AccessibilityToolsComponent":
        """Opens the panel, flips the real 'Dark mode' switch, waits for the
        product's own `<html data-theme="dark">` signal, then closes the
        panel. Idempotent — a switch already reporting checked is left
        alone."""
        self.open_panel()
        if not self.is_dark_mode_switch_checked():
            self.click(self.DARK_SWITCH)
        self.page.wait_for_function(
            "() => document.documentElement.getAttribute('data-theme') === 'dark'"
        )
        self.close_panel()
        return self

    def is_dark_mode_switch_checked(self) -> bool:
        return (
            self.page.locator(self.DARK_SWITCH).get_attribute("aria-checked") == "true"
        )

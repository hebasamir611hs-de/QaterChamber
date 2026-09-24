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

The high-contrast switch is now exercised (PBI 131052 FAQ, TC 141659/141660)
and declared as CONTRAST_SWITCH. Confirmed live 2026-09-24 on
/web/qatar-chamber/faq: toggling it adds the `qc-a11y-contrast` class to
<html> (data-theme stays as-is) and the page repaints white-on-black.
"""

from core.web.base_page import BasePage


class AccessibilityToolsComponent(BasePage):
    OPEN_BUTTON = 'button[aria-label="Accessibility tools"]'
    DARK_SWITCH = "button.qc-a11y-switch[data-qc-a11y-dark]"
    DONE_BUTTON = "button.qc-a11y-done"
    CONTRAST_SWITCH = "button.qc-a11y-switch[data-qc-a11y-contrast]"
    HIGH_CONTRAST_CLASS = "qc-a11y-contrast"

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

    def enable_high_contrast(self) -> "AccessibilityToolsComponent":
        """Opens the panel, flips the real 'High contrast' switch, waits for
        the product's own `<html class="qc-a11y-contrast">` signal, then
        closes the panel. Idempotent — a switch already checked is left
        alone."""
        self.open_panel()
        if not self.is_high_contrast_switch_checked():
            self.click(self.CONTRAST_SWITCH)
        self.page.wait_for_function(
            "(cls) => document.documentElement.classList.contains(cls)", arg=self.HIGH_CONTRAST_CLASS
        )
        self.close_panel()
        return self

    def is_high_contrast_switch_checked(self) -> bool:
        return (
            self.page.locator(self.CONTRAST_SWITCH).get_attribute("aria-checked") == "true"
        )

    def is_high_contrast_active(self) -> bool:
        return self.page.evaluate(
            "(cls) => document.documentElement.classList.contains(cls)", self.HIGH_CONTRAST_CLASS
        )

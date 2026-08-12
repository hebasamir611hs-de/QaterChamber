"""
web/tests/header/test_accessibility_web.py — Accessibility Tools,
Web (public site) surface (PBI 133381, "QC-GBL-003").

Structural split (2026-08-11, per .claude/context/active/standards.md ->
"Automation Structure - Project Deviation from the Plugin Default"): this
module holds every Web-tagged GLOBAL-ACCESSIBILITY-TC-* case. The sibling
Control_Panel-tagged cases live in test_accessibility_control_panel.py in
this same folder. Two cases (TC-013, TC-014) are tagged BOTH Web and
Control_Panel — see that module's docstring for the split rationale.

Every test still carries:
  - its QA traceability ID (`@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-xxx")`)
  - the Axis B backlog marker `@pytest.mark.pbi_133381` + `allure.label("pbi", PBI)`
  - one marker per tag axis actually present on its source case.

Known dev-build discrepancy (disclosed, not "fixed" mid-automation per
automation-standards.md's "Healing touches locators, never the expected
result"): the live panel (`div.qc-a11y-panel`) actually renders 6 controls —
Dark mode, High contrast, Zoom value, Zoom out, Zoom in, Reset, Done — while
the approved cases (TC-003, TC-004, TC-013/014) describe exactly 4 (High
Contrast, Zoom In, Zoom Out, Reset/Normal View). `AccessibilityPage.
panel_control_count()` counts only those 4 named hooks, matching the case's
literal wording; the extra Dark-mode/Done controls are real elements this
Page Object also exposes (`DARK_MODE_SWITCH`, `DONE_BUTTON`) but that no
case currently asserts against. This is a review-gate note for the QA
Manager/qa-engineer, not something silently patched here.

TC-005's WCAG contrast audit and TC-032's "CSS-variable-override
unsupported" / TC-033's "panel fails to open" edge cases are documented
per-test with their own scripting caveats (axe-playwright-python is not a
pinned dependency yet — see requirements.txt and this module's TC-005 test
— and TC-032/033 script a best-effort harness simulation since neither
condition is naturally reachable on the live dev build).

CMS/Control-Panel steps needed as Arrange preconditions go through
`HeaderAdminPage`, whose field constants are `TODO(locator)` placeholders
(disclosed, CMS-only exception — see header_admin_page.py's docstring).

First executed 2026-08-11 (14 passed / 4 failed / 3 broken). Triage of that
run and the heals applied to this module are recorded per-test; the two
NEEDS_INVESTIGATION items (TC-001's expected icon background, TC-029's zoom
range) are still open and left failing on purpose rather than fitted to
whatever the dev build happens to return.
"""

import allure
import pytest

from web.pages.header.accessibility_page import AccessibilityPage
from web.pages.header.header_admin_page import HeaderAdminPage

PBI = "133381"

# TC-013/TC-014 drive the Liferay Control Panel through HeaderAdminPage, whose
# 15 field constants are all still `TODO(locator)` placeholders because no
# authenticated CMS session was ever available (CONTROL_PANEL_URL, TEST_USER
# and TEST_PASSWORD are all empty in .env, and .auth/state.json does not
# exist). Before this marker they failed as *broken* with a misleading
# Playwright CSS error ('Unexpected token "TODO(" while parsing css selector')
# on a blank about:blank page — noise that looked like a product failure.
# Skipping states the real situation: blocked on credentials, zero coverage.
# Remove this marker once tools/save_auth.py can capture a CMS session and
# extract-locators has filled HeaderAdminPage in.
CMS_BLOCKED_REASON = (
    "Blocked: Liferay Control Panel locators are TODO(locator) placeholders — "
    "needs CMS credentials (CONTROL_PANEL_URL/TEST_USER/TEST_PASSWORD in .env) "
    "then tools/save_auth.py + extract-locators. These two CRITICAL cases "
    "currently provide NO coverage."
)


@allure.epic("Accessibility Tools")
@allure.feature("UI")
@allure.story("Verify that the accessibility tools icon appears in the site header on desktop")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the accessibility tools icon appears in the site header on desktop")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-001")
@pytest.mark.parametrize("page", [(1366, 768)], indirect=True)
def test_tc001_verify_accessibility_icon_appears_in_header_on_desktop(page):
    """GLOBAL-ACCESSIBILITY-TC-001 — Verify that the accessibility tools icon appears in the site header on desktop"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)

    # Act
    with allure.step("Load the homepage at 1366x768 desktop viewport"):
        a11y.open_home()
    with allure.step("Observe the accessibility icon"):
        style = a11y.icon_style()

    # Assert
    assert a11y.is_icon_visible()
    assert round(style["width"]) == 32 and round(style["height"]) == 32
    assert style["backgroundColor"] in ("rgb(237, 237, 237)", "rgba(237, 237, 237, 1)")


@allure.epic("Accessibility Tools")
@allure.feature("UI")
@allure.story("Verify that the accessibility tools icon renders correctly on a mobile viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the accessibility tools icon renders correctly on a mobile viewport")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-002")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_tc002_verify_accessibility_icon_renders_correctly_on_mobile_viewport(page):
    """GLOBAL-ACCESSIBILITY-TC-002 — Verify that the accessibility tools icon renders correctly on a mobile viewport"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)

    # Act
    with allure.step("Load the homepage at 375x812 mobile viewport"):
        a11y.open_home()

    # Assert — visible, not clipped/overlapping the switcher, still 32x32
    assert a11y.is_icon_visible()
    assert a11y.icon_overlaps_switcher() is False
    style = a11y.icon_style()
    assert round(style["width"]) == 32 and round(style["height"]) == 32


@allure.epic("Accessibility Tools")
@allure.feature("UI")
@allure.story("Verify that clicking the accessibility icon opens a panel with all 4 required controls on desktop")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that clicking the accessibility icon opens a panel with all 4 required controls on desktop")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-003")
def test_tc003_verify_clicking_icon_opens_panel_with_4_controls_desktop(page):
    """GLOBAL-ACCESSIBILITY-TC-003 — Verify that clicking the accessibility icon opens a panel with all 4 required controls on desktop"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()

    # Act
    with allure.step("Click the accessibility icon"):
        a11y.click_icon()

    # Assert — High Contrast, Zoom In, Zoom Out, Reset all present, no overlap
    assert a11y.is_panel_open()
    assert a11y.panel_control_count() == 4


@allure.epic("Accessibility Tools")
@allure.feature("UI")
@allure.story("Verify that the accessibility panel layout adapts correctly on a mobile viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the accessibility panel layout adapts correctly on a mobile viewport")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-004")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_tc004_verify_accessibility_panel_layout_adapts_on_mobile_viewport(page):
    """GLOBAL-ACCESSIBILITY-TC-004 — Verify that the accessibility panel layout adapts correctly on a mobile viewport"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()

    # Act
    with allure.step("Click the accessibility icon"):
        a11y.click_icon()

    # Assert — all 4 controls visible, no horizontal scroll/clipping
    assert a11y.is_panel_open()
    assert a11y.panel_control_count() == 4
    assert a11y.is_panel_no_horizontal_overflow()


@allure.epic("Accessibility Tools")
@allure.feature("UI")
@allure.story("Verify that the High Contrast theme meets WCAG 2.1 AA color contrast ratios")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the High Contrast theme meets WCAG 2.1 AA color contrast ratios")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-005")
def test_tc005_verify_high_contrast_theme_meets_wcag_21_aa_contrast_ratios(page):
    """GLOBAL-ACCESSIBILITY-TC-005 — Verify that the High Contrast theme meets WCAG 2.1 AA color contrast ratios

    NOTE — dependency disclosure: this assertion requires `axe-playwright-python`
    (added to requirements.txt as a new dependency by this batch — see
    AccessibilityPage.run_contrast_audit()'s docstring). It is NOT installed in
    this authoring session, so this test is scripted against the package's
    documented sync API (https://pamelafox.github.io/axe-playwright-python/usage/)
    but has not been import-checked here; `pip install -r requirements.txt` must
    run before this test can execute.
    """
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()
    a11y.click_icon()

    # Act
    with allure.step("Activate High Contrast"):
        a11y.click_high_contrast()
    with allure.step("Run an automated color-contrast audit (axe-core, WCAG 2.1 AA)"):
        violations = a11y.contrast_violation_count()

    # Assert
    assert a11y.is_high_contrast_active() is True
    assert violations == 0


@allure.epic("Accessibility Tools")
@allure.feature("UI")
@allure.story("Verify that the accessibility icon shows a visible focus indicator when reached via keyboard Tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the accessibility icon shows a visible focus indicator when reached via keyboard Tab")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-006")
def test_tc006_verify_icon_shows_visible_focus_indicator_via_keyboard_tab(page):
    """GLOBAL-ACCESSIBILITY-TC-006 — Verify that the accessibility icon shows a visible focus indicator when reached via keyboard Tab"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()

    # Act
    with allure.step("Press Tab repeatedly until focus reaches the accessibility icon"):
        reached = a11y.focus_icon_via_tab()
    with allure.step("Observe the icon's outline while focused"):
        outline = a11y.icon_outline_on_focus()

    # Assert
    assert reached is True
    assert a11y.is_icon_focused() is True
    assert outline.strip() != "none 0px none"


@allure.epic("Accessibility Tools")
@allure.feature("UI")
@allure.story("Verify that Zoom In (+) and Zoom Out (−) buttons render enabled with correct icons/labels by default")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Zoom In (+) and Zoom Out (−) buttons render enabled with correct icons/labels by default")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-007")
def test_tc007_verify_zoom_in_out_buttons_render_enabled_by_default(page):
    """GLOBAL-ACCESSIBILITY-TC-007 — Verify that Zoom In (+) and Zoom Out (−) buttons render enabled with correct icons/labels by default"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()

    # Act
    with allure.step("Open the accessibility panel on a fresh page load"):
        a11y.click_icon()

    # Assert
    assert a11y.is_zoom_in_enabled() is True
    assert a11y.is_zoom_out_enabled() is True
    assert a11y.zoom_value_text() == "100%"


@allure.epic("Accessibility Tools")
@allure.feature("UI")
@allure.story("Verify that the Reset/Normal View button renders enabled regardless of current contrast/zoom state")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Reset/Normal View button renders enabled regardless of current contrast/zoom state")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-008")
def test_tc008_verify_reset_button_renders_enabled_regardless_of_state(page):
    """GLOBAL-ACCESSIBILITY-TC-008 — Verify that the Reset/Normal View button renders enabled regardless of current contrast/zoom state"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()
    a11y.click_icon()

    # Act / Assert — default state
    with allure.step("Observe Reset/Normal View at default state"):
        assert a11y.is_reset_enabled() is True

    with allure.step("Activate High Contrast and Zoom In once"):
        a11y.click_high_contrast()
        a11y.click_zoom_in()

    # Assert — still enabled
    assert a11y.is_reset_enabled() is True


@allure.epic("Accessibility Tools")
@allure.feature("UI")
@allure.story("Verify that the header icon-button row mirrors correctly in Arabic (RTL) layout")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the header icon-button row mirrors correctly in Arabic (RTL) layout")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-009")
def test_tc009_verify_header_icon_row_mirrors_correctly_in_arabic_rtl(page):
    """GLOBAL-ACCESSIBILITY-TC-009 — Verify that the header icon-button row mirrors correctly in Arabic (RTL) layout"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)

    # Act
    with allure.step("Switch site language to Arabic and load the page"):
        a11y.open_home("https://qcdev.ihorizons.com/ar/home")

    # Assert — RTL header, icon + switcher mirrored consistently
    assert a11y.is_rtl() is True
    assert a11y.is_icon_visible()


@allure.epic("Accessibility Tools")
@allure.feature("Functional-High")
@allure.story("Verify that a visitor can open the accessibility panel, apply High Contrast, zoom in, zoom out, and reset — all in real time without a page reload")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a visitor can open the accessibility panel, apply High Contrast, zoom in, zoom out, and reset — all in real time without a page reload")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-010")
def test_tc010_verify_full_panel_journey_applies_in_real_time_no_reload(page):
    """GLOBAL-ACCESSIBILITY-TC-010 — Verify that a visitor can open the accessibility panel, apply High Contrast, zoom in, zoom out, and reset — all in real time without a page reload"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()
    marker = a11y.set_dom_marker()

    # Act
    with allure.step("Click the accessibility icon"):
        a11y.click_icon()
    with allure.step("Click High Contrast"):
        a11y.click_high_contrast()
    with allure.step("Click Zoom In (+) once"):
        a11y.click_zoom_in()
        zoom_after_in = a11y.zoom_scale()
    with allure.step("Click Zoom Out (−) once"):
        a11y.click_zoom_out()
        zoom_after_out = a11y.zoom_scale()
    with allure.step("Click Reset/Normal View"):
        a11y.click_reset()

    # Assert
    assert a11y.dom_marker() == marker  # no reload occurred throughout
    assert zoom_after_in > 1.0
    assert zoom_after_out < zoom_after_in
    assert a11y.is_high_contrast_active() is False
    assert a11y.zoom_scale() == 1.0


@allure.epic("Accessibility Tools")
@allure.feature("Functional-High")
@allure.story("Verify that accessibility settings persist across page navigation within the same browser session")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that accessibility settings persist across page navigation within the same browser session")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-011")
def test_tc011_verify_accessibility_settings_persist_across_page_navigation(page):
    """GLOBAL-ACCESSIBILITY-TC-011 — Verify that accessibility settings persist across page navigation within the same browser session

    NOTE — disclosed live observation: no dedicated accessibility-state
    key was found in localStorage/sessionStorage/cookies on the live dev
    build (see accessibility_page.py's docstring); this assertion is
    scripted per the case's expected result and will honestly fail if the
    running build indeed does not persist state across navigation — that
    is a real product signal to surface, not to be weakened here.
    """
    allure.dynamic.label("pbi", PBI)
    # Arrange — Page A at default state
    a11y = AccessibilityPage(page)
    a11y.open_home()
    a11y.click_icon()

    # Act
    with allure.step("Activate High Contrast on Page A"):
        a11y.click_high_contrast()
    with allure.step("Click Zoom In (+) once on Page A"):
        a11y.click_zoom_in()
        zoom_a = a11y.zoom_scale()
    with allure.step("Navigate to Page B via a header link"):
        a11y.navigate_via_header_link("About us")

    # Assert — Page B already shows the same state
    assert a11y.is_high_contrast_active() is True
    assert a11y.zoom_scale() == zoom_a


@allure.epic("Accessibility Tools")
@allure.feature("Functional-High")
@allure.story("Verify that a keyboard-only visitor can operate the entire accessibility panel using only Tab, Enter and Space")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a keyboard-only visitor can operate the entire accessibility panel using only Tab, Enter and Space")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-012")
def test_tc012_verify_keyboard_only_visitor_can_operate_entire_panel(page):
    """GLOBAL-ACCESSIBILITY-TC-012 — Verify that a keyboard-only visitor can operate the entire accessibility panel using only Tab, Enter and Space"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()

    # Act
    with allure.step("Tab to the accessibility icon, then press Enter"):
        a11y.focus_icon_via_tab()
        a11y.press_key("Enter")
    with allure.step("Tab to High Contrast, then press Space"):
        a11y.press_tab_until_focused(AccessibilityPage.HIGH_CONTRAST_SWITCH)
        a11y.press_key("Space")
    with allure.step("Tab to Zoom In, then press Enter"):
        a11y.press_tab_until_focused(AccessibilityPage.ZOOM_IN_BUTTON)
        a11y.press_key("Enter")
        zoom_after_in = a11y.zoom_scale()
    with allure.step("Tab to Reset, then press Enter"):
        a11y.press_tab_until_focused(AccessibilityPage.RESET_BUTTON)
        a11y.press_key("Enter")

    # Assert — zero mouse interaction throughout
    assert zoom_after_in > 1.0
    assert a11y.is_high_contrast_active() is False
    assert a11y.zoom_scale() == 1.0


@allure.epic("Accessibility Tools")
@allure.feature("Functional-High")
@allure.story("Verify that enabling the Accessibility Tools widget in CMS makes the icon appear on the frontend after cache refresh")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that enabling the Accessibility Tools widget in CMS makes the icon appear on the frontend after cache refresh")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-013")
@pytest.mark.skip(reason=CMS_BLOCKED_REASON)
def test_tc013_verify_enabling_accessibility_widget_in_cms_shows_icon_after_cache_refresh(page):
    """GLOBAL-ACCESSIBILITY-TC-013 — Verify that enabling the Accessibility Tools widget in CMS makes the icon appear on the frontend after cache refresh"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    admin = HeaderAdminPage(page)
    admin.open_accessibility_settings()

    # Act
    with allure.step("Toggle Accessibility Tools Enabled to True and Save and Publish"):
        admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, True)
        admin.click_save_and_publish()
    with allure.step("Load a public page after cache refresh"):
        a11y.open_home()

    # Assert
    assert a11y.is_icon_visible()


@allure.epic("Accessibility Tools")
@allure.feature("Functional-High")
@allure.story("Verify that disabling the Accessibility Tools widget in CMS hides the icon from the frontend after cache refresh")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling the Accessibility Tools widget in CMS hides the icon from the frontend after cache refresh")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-014")
@pytest.mark.skip(reason=CMS_BLOCKED_REASON)
def test_tc014_verify_disabling_accessibility_widget_in_cms_hides_icon_after_cache_refresh(page):
    """GLOBAL-ACCESSIBILITY-TC-014 — Verify that disabling the Accessibility Tools widget in CMS hides the icon from the frontend after cache refresh"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — setting confirmed True beforehand
    a11y = AccessibilityPage(page)
    admin = HeaderAdminPage(page)
    admin.open_accessibility_settings()
    admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, True)
    admin.click_save_and_publish()

    # Act
    with allure.step("Toggle Accessibility Tools Enabled to False and Save and Publish"):
        admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, False)
        admin.click_save_and_publish()
    with allure.step("Load a public page after cache refresh"):
        a11y.open_home()

    # Assert
    assert a11y.is_icon_visible() is False


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that clicking the accessibility icon again while the panel is open closes the panel")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that clicking the accessibility icon again while the panel is open closes the panel")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-026")
def test_tc026_verify_clicking_icon_again_while_panel_open_closes_panel(page):
    """GLOBAL-ACCESSIBILITY-TC-026 — Verify that clicking the accessibility icon again while the panel is open closes the panel"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()
    a11y.click_icon()
    assert a11y.is_panel_open()

    # Act
    with allure.step("Click the accessibility icon a second time"):
        a11y.click_icon()

    # Assert
    assert a11y.is_panel_open() is False


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that clicking High Contrast again while active reverts the site to the default theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that clicking High Contrast again while active reverts the site to the default theme")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-027")
def test_tc027_verify_clicking_high_contrast_again_reverts_default_theme(page):
    """GLOBAL-ACCESSIBILITY-TC-027 — Verify that clicking High Contrast again while active reverts the site to the default theme"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()
    a11y.click_icon()
    a11y.click_high_contrast()
    assert a11y.is_high_contrast_active() is True
    marker = a11y.set_dom_marker()

    # Act
    with allure.step("Click the High Contrast toggle again"):
        a11y.click_high_contrast()

    # Assert — instant revert, no page reload
    assert a11y.is_high_contrast_active() is False
    assert a11y.dom_marker() == marker


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that clicking Zoom In (+) three times consecutively increases font size cumulatively by three increments")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that clicking Zoom In (+) three times consecutively increases font size cumulatively by three increments")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-028")
def test_tc028_verify_zoom_in_three_times_increases_cumulatively(page):
    """GLOBAL-ACCESSIBILITY-TC-028 — Verify that clicking Zoom In (+) three times consecutively increases font size cumulatively by three increments"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()
    a11y.click_icon()
    assert a11y.zoom_scale() == 1.0

    # Act
    with allure.step("Click Zoom In (+) three times"):
        a11y.click_zoom_in()
        level1 = a11y.zoom_scale()
        a11y.click_zoom_in()
        level2 = a11y.zoom_scale()
        a11y.click_zoom_in()
        level3 = a11y.zoom_scale()

    # Assert — each step strictly larger than the last
    assert level1 > 1.0
    assert level2 > level1
    assert level3 > level2


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that clicking Zoom Out (−) three times consecutively decreases font size cumulatively by three increments")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that clicking Zoom Out (−) three times consecutively decreases font size cumulatively by three increments")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-029")
def test_tc029_verify_zoom_out_three_times_decreases_cumulatively(page):
    """GLOBAL-ACCESSIBILITY-TC-029 — Verify that clicking Zoom Out (−) three times consecutively decreases font size cumulatively by three increments"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()
    a11y.click_icon()
    assert a11y.zoom_scale() == 1.0

    # Act
    with allure.step("Click Zoom Out (−) three times"):
        a11y.click_zoom_out()
        level1 = a11y.zoom_scale()
        a11y.click_zoom_out()
        level2 = a11y.zoom_scale()
        a11y.click_zoom_out()
        level3 = a11y.zoom_scale()

    # Assert — each step strictly smaller than the last
    assert level1 < 1.0
    assert level2 < level1
    assert level3 < level2


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that Reset/Normal View reverts a combined High Contrast + multi-increment zoom state to default in a single click")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Reset/Normal View reverts a combined High Contrast + multi-increment zoom state to default in a single click")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-030")
def test_tc030_verify_reset_reverts_combined_contrast_zoom_state_in_one_click(page):
    """GLOBAL-ACCESSIBILITY-TC-030 — Verify that Reset/Normal View reverts a combined High Contrast + multi-increment zoom state to default in a single click"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    a11y = AccessibilityPage(page)
    a11y.open_home()
    a11y.click_icon()

    # Act
    with allure.step("Activate High Contrast"):
        a11y.click_high_contrast()
    with allure.step("Click Zoom In (+) twice"):
        a11y.click_zoom_in()
        a11y.click_zoom_in()
    marker = a11y.set_dom_marker()
    with allure.step("Click Reset/Normal View"):
        a11y.click_reset()

    # Assert — single action, no reload
    assert a11y.is_high_contrast_active() is False
    assert a11y.zoom_scale() == 1.0
    assert a11y.dom_marker() == marker


@allure.epic("Accessibility Tools")
@allure.feature("Edge")
@allure.story("Verify that High Contrast falls back gracefully to the default theme on a browser without CSS variable override support")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that High Contrast falls back gracefully to the default theme on a browser without CSS variable override support")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-032")
def test_tc032_verify_high_contrast_falls_back_gracefully_without_css_var_support(page):
    """GLOBAL-ACCESSIBILITY-TC-032 — Verify that High Contrast falls back gracefully to the default theme on a browser without CSS variable override support

    NOTE — scripting caveat: the live dev build's browser (Chromium) always
    supports CSS custom properties, so "CSS variable override unsupported"
    cannot be reached by simply loading the real site. This is scripted as
    a best-effort harness simulation — an init script that neutralizes
    `CSSStyleDeclaration.prototype.setProperty` for the `--qc-a11y-*`
    namespace before the page's scripts run — rather than invented as a
    real, verified environment. Disclosed per the task's instruction to
    author the test even where the precondition needs simulation.
    """
    allure.dynamic.label("pbi", PBI)
    # Arrange — neutralize CSS custom-property overrides before page scripts run
    page.add_init_script(
        "(() => { const orig = CSSStyleDeclaration.prototype.setProperty; "
        "CSSStyleDeclaration.prototype.setProperty = function(name, ...rest) { "
        "if (String(name).startsWith('--qc-a11y')) return; return orig.call(this, name, ...rest); }; })();"
    )
    console_errors = []
    page.on("pageerror", lambda exc: console_errors.append(str(exc)))
    a11y = AccessibilityPage(page)
    a11y.open_home()
    a11y.click_icon()

    # The homepage throws 2 page errors of its OWN on every load, unrelated to
    # this widget (the Our Services carousel queries .qc-os-arrow--prev/--next,
    # which are commented out of the markup, so prevBtn/nextBtn are null —
    # confirmed 2026-08-11 on a clean load with no init script and reported as
    # a separate product bug). This test is about High Contrast's fallback, so
    # it baselines whatever the page already threw and asserts only that the
    # High Contrast click itself adds nothing new. Asserting `== []` outright
    # made this test fail for a defect in a different component.
    errors_before_click = list(console_errors)

    # Act
    with allure.step("Click High Contrast"):
        a11y.click_high_contrast()

    # Assert — the fallback itself throws nothing new, no partially-applied styling
    new_errors = [e for e in console_errors if e not in errors_before_click]
    assert new_errors == []


@allure.epic("Accessibility Tools")
@allure.feature("Edge")
@allure.story("Verify that the accessibility icon remains visible with no broken UI if the panel fails to open")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the accessibility icon remains visible with no broken UI if the panel fails to open")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-033")
def test_tc033_verify_icon_remains_visible_if_panel_fails_to_open(page):
    """GLOBAL-ACCESSIBILITY-TC-033 — Verify that the accessibility icon remains visible with no broken UI if the panel fails to open

    NOTE — scripting caveat: forcing the panel component itself to fail is
    not naturally reachable on the live dev build without a test-harness
    hook the app doesn't expose; this is scripted as a best-effort
    simulation (removing the panel node the instant it's inserted, via a
    MutationObserver installed by an init script) rather than invented as
    a verified real failure mode. Disclosed per the task's instruction.

    The observer target is `document`, NOT `document.documentElement`: an
    init script runs before the document element exists, so observing
    `document.documentElement` threw "parameter 1 is not of type 'Node'",
    the observer was never installed, the panel opened normally, and this
    test failed on 2026-08-11 asserting a simulation that never ran.
    `document` is a Node and is already available at init-script time.
    Verified: with this target the panel node is removed on insert while the
    icon stays visible and the header keeps its layout.
    """
    allure.dynamic.label("pbi", PBI)
    # Arrange — force the panel to be removed the instant it mounts
    page.add_init_script(
        "(() => { new MutationObserver((muts) => { "
        "document.querySelectorAll('.qc-a11y-panel').forEach(p => p.remove()); "
        "}).observe(document, {childList: true, subtree: true}); })();"
    )
    a11y = AccessibilityPage(page)
    a11y.open_home()

    # Act
    with allure.step("Click the accessibility icon"):
        a11y.click_icon()

    # Assert — icon remains visible and clickable, no broken layout
    assert a11y.is_icon_visible()
    assert a11y.is_panel_open() is False

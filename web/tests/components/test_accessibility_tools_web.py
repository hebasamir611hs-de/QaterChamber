"""
web/tests/components/test_accessibility_tools_web.py — Accessibility Tools
(PBI 129364 / QC-GBL-003), Web platform.

Source: batch A of 22 total approved, Automation-tagged UI cases for this
PBI -- the 11 cases handed off for this pass (ADO #134481, #134482, #134483,
#134484, #134486, #134487, #134488, #134489, #134490, #134628, #134630).
Batch B (11 more cases, APPENDED below) covers ADO #134629, #134631, #134632,
#134633, #134634, #134635, #134636, #134661, #134662, #134665, #134666 --
mobile viewport, WCAG contrast audit, keyboard focus-indicator, RTL
mirroring, and Dark Mode/High Contrast rendering. All 22 are Platform=Web ->
this one module (test_accessibility_tools_web.py); no Control_Panel-tagged
cases are in scope for this PBI's batches (the stub
test_accessibility_tools_control_panel.py stays untouched).

Batch B dependency note: this batch adds axe-playwright-python==0.1.8 back to
requirements.txt (previously removed 2026-08-18 pending "the commit that
actually adds the contrast-audit test" -- ADO #134632, this one) for
run_color_contrast_audit()'s real axe-core WCAG check.

Batch B coverage flag (reported, NOT resolved here -- same authority boundary
as batch A's flag): ADO #134665 states the panel opens with "4 controls",
the same literal count #134630 already states and that batch-A's own
extraction already found to be 6 live (Dark Mode + Done, beyond High
Contrast/Zoom In/Zoom Out/Reset). #134665 is scripted per its own 4 named
controls (NAMED_CONTROL_LOCATORS) rather than re-deriving/re-flagging this
independently -- same near-duplicate-analysis-pass pattern, not merged.

Real, CLI-verified findings from batch B's extraction (see the Page Object's
docstring for the full log): mobile viewport 375x812 renders the icon at
32x32 with no overlap and no horizontal page overflow, and the panel adapts
(full-width, stacked/paired controls, all within 0..375px) with no clipping
(#134629, #134631) -- genuine PASS candidates. High Contrast adds
`qc-a11y-contrast` to `<html>`, applies with zero navigation, and -- verified
via a REAL full page navigation, not a client-route change -- persists onto
a second, distinct content page (#134661, #134662). A real axe-core audit
scoped to `color-contrast` returned 0 violations with High Contrast active
(#134632) -- a genuine, observed PASS, not an assumed one. Dark Mode changes
computed styles directly (header/icon/panel backgrounds go dark) without an
`<html>` class, and keeps the icon distinguishable via a border-color shift
to a light/translucent tone rather than a background-color contrast alone;
RTL position and `dir` are both unaffected by toggling Dark Mode (#134665,
#134666). The header's 3-icon utility cluster mirrors into the EXACT reverse
x-order under Arabic (#134636, #134666). Zoom In/Zoom Out render distinct
labels ("Zoom in"/"Zoom out") and enabled by default (#134634); Reset stays
visible/enabled after activating High Contrast and Zoom In, then closing and
reopening the panel (#134635).

Coverage flag (reported, NOT resolved here -- a QA coverage judgement above
this skill's authority): ADO #134481/#134628 and #134482/#134630 read as
near-duplicate coverage from two separate analysis passes on this PBI (the
task brief says this pattern repeats in batch B too). Both pairs are
automated below as distinct, separately-traceable tests -- neither merged,
skipped, nor silently deduplicated.

Real, CLI-verified findings from extraction (see the Page Object's docstring
for the full log): the accessibility icon and panel are genuinely present
and functional on the live site -- the icon toggles the panel open AND
closed on repeated clicks (#134483 is a genuine PASS candidate), the panel's
open/close fires zero network requests (a real finding directly relevant to
#134484 -- see that test's own comment), the High Contrast toggle starts
`aria-checked="false"` (matches #134486), Zoom In/Zoom Out/Reset all render
enabled (matches #134487/#134488). Two real mismatches against the cases'
stated numbers: the panel actually renders SIX tool controls (adds a "Dark
mode" toggle above High Contrast, and a "Done" button beside Reset), not the
four #134482/#134630 name -- #134630's "exactly 4" assertion is scripted
per its exact stated number and will honestly fail against the live count of
6; and at 1366x768 the accessibility button's computed padding is "0px", not
#134628's stated "10px" (background-color also reads #F7F8F9, not #EDEDED --
the same header-utility-cluster mismatch already logged against ADO #134239
and #134428 on this identical color, for the identical element, in this
project's Header and Language Switcher automation).

#134484 (open-panel failure simulation): the live panel is genuinely backed
by two separate script/style bundles fetched during the INITIAL page load
(/o/qc-accessibility-tools/*, /o/qc-a11y-keyboard/*), not on click. Blocking
exactly those two real bundles is a literal, reproducible way to produce
this case's "blocked script" precondition -- confirmed live: it fires 4 real
net::ERR_FAILED console errors during the load, and the panel subsequently
never mounts at all (0 DOM nodes) when the icon is clicked afterward; the
icon itself stays visible and the click introduces zero NEW console errors
of its own. The test asserts exactly that: a genuine block occurred, the
click itself stayed clean, the icon remained intact, and no partial/broken
panel markup rendered.

#134489 (CMS precondition): step 1 ("in CMS, set Accessibility Tools Enabled
= False and publish") is a Control_Panel precondition on this Platform=Web-
only case. No CMS credentials are configured this pass (TEST_USER/
TEST_PASSWORD are empty in .env), AND -- unlike ADO #134428 on the Language
Switcher PBI, where the given precondition (Enabled=True) already matched
the live, observable state -- here the given precondition (Enabled=False)
does NOT match live reality: the accessibility icon IS currently visible/
enabled on qcdev (confirmed by #134481 below). The "disabled" state genuinely
cannot be produced from the Web surface alone, and asserting "icon not
visible" against the current, enabled state would not test the CMS-disable
behaviour at all -- it would just always fail for an unrelated reason, or
duplicate #134481's own assertion if scripted the other way. Per the task's
explicit instruction ("say so and script what you honestly can, don't
fabricate the CMS action"), this case is marked `skip` with a concrete reason
rather than asserting anything -- an honest "pending environment/precondition",
never an invented result (automation-standards.md's Result-integrity rule).

#134490 (keyboard focus): checked directly, not assumed. Tab from a fresh
page load hits the same reCAPTCHA-badge-iframe/<body> oscillation trap
header_component.py's docstring documents for the logo (ADO #134246) -- but
here it is NON-DETERMINISTIC: repeated live re-runs of this exact test
(solo and under the default parallel workers) show the accessibility icon
reached within 40 Tab presses on SOME runs and not on others (2 fail / 1
pass across 3 solo re-runs; passed once under the default `-n 3` run
reported below). This is a real, disclosed flakiness in the live site's
keyboard-nav trap, not a defect in the test -- report whichever outcome an
actual run observes, never assume it mirrors the logo's consistently-blocked
behaviour.
"""

import uuid

import allure
import pytest

from cms.pages.components.qctest_record_admin import PNG_FIXTURE as QCTEST_PNG, StrategicPartnerQctest
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent
from web.pages.home_strategic_partners.home_strategic_partners_page import StrategicPartnersPage

PBI = "129364"

# ADO-134509 / 134510 -- the case's own EN alt text and its Arabic counterpart.
IMAGE_ALT_EN = "Qatar Chamber headquarters building"
IMAGE_ALT_AR = "مبنى المقر الرئيسي لغرفة قطر"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Accessibility icon visible on page load")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The accessibility icon is displayed in the site header on page load")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134481")
def test_accessibility_icon_displayed_in_header_on_page_load(page):
    # ADO-134481 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Navigate to the homepage (EN)"):
        a11y.open_home()

    with allure.step("Observe the header utility row for the accessibility icon"):
        is_visible = a11y.is_accessibility_button_visible()
        in_utility_cluster = a11y.is_accessibility_button_in_utility_cluster()

    # Assert
    assert a11y.header.is_header_visible()
    assert is_visible, "expected the accessibility icon (wheelchair/person-in-circle glyph) visible in the header"
    assert in_utility_cluster, "expected the accessibility icon next to the search icon and EN/AR toggle"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Opening the accessibility panel")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking the accessibility icon opens the accessibility panel")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134482")
def test_clicking_accessibility_icon_opens_panel_with_controls(page):
    # ADO-134482 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("On the homepage, click the accessibility icon"):
        a11y.open_home()
        a11y.click_accessibility_button()

    with allure.step("Read the resulting panel's controls"):
        panel_open = a11y.is_panel_open()
        controls = a11y.are_named_controls_visible()

    # Assert
    assert panel_open, "expected the accessibility panel to open"
    assert controls["high_contrast"], "expected a High Contrast toggle in the panel"
    assert controls["zoom_in"], "expected a Zoom In (+) control in the panel"
    assert controls["zoom_out"], "expected a Zoom Out (-) control in the panel"
    assert controls["reset"], "expected a Reset/Normal View control in the panel"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Closing the accessibility panel")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking the accessibility icon a second time closes the panel")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134483")
def test_clicking_accessibility_icon_again_closes_panel(page):
    # ADO-134483 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the panel"):
        a11y.open_home()
        a11y.click_accessibility_button()
        panel_open_after_first_click = a11y.is_panel_open()

    with allure.step("Click the accessibility icon again"):
        a11y.click_accessibility_button()

    with allure.step("Read whether the panel closed and the icon remains visible"):
        panel_open_after_second_click = a11y.is_panel_open()
        icon_still_visible = a11y.is_accessibility_button_visible()

    # Assert
    assert panel_open_after_first_click, "precondition: the panel must be open before testing the close toggle"
    assert not panel_open_after_second_click, "expected the panel to close on a second icon click"
    assert icon_still_visible, "expected the accessibility icon to remain visible after closing the panel"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Resilience if the panel fails to open")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The accessibility panel does not produce broken UI if it fails to open")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134484")
def test_accessibility_panel_no_broken_ui_on_open_failure(page):
    # ADO-134484 | PBI 129364
    # Real, reproducible interpretation (see module docstring): the live
    # panel is genuinely backed by two script/style bundles fetched during
    # the INITIAL page load (/o/qc-accessibility-tools/*,
    # /o/qc-a11y-keyboard/*), not on click. Blocking exactly those two real
    # bundles IS a literal, honest way to produce this case's "blocked
    # script" precondition -- confirmed live: it fires 4 real
    # net::ERR_FAILED console errors during the LOAD (before any click), and
    # the panel subsequently never mounts when the icon is clicked. The
    # assertions below therefore separate "errors caused by this
    # precondition's load-time script block" (expected, and disclosed) from
    # "errors caused by the click action itself" (must be zero, per the
    # case's literal wording) -- and independently confirm the icon itself
    # and the DOM stay clean (no partial/broken panel markup).
    # Arrange
    a11y = AccessibilityToolsComponent(page)
    a11y.start_open_failure_simulation()

    # Act
    with allure.step("Load the homepage with the real accessibility script/style bundles blocked"):
        a11y.open_home()
        console_baseline = a11y.console_message_count()

    with allure.step("Click the accessibility icon"):
        a11y.click_accessibility_button()

    with allure.step("Read console errors introduced by the click, and panel/icon DOM state"):
        console_errors_from_click = a11y.console_error_count_since(console_baseline)
        blocked_requests = a11y.blocked_request_count()
        panel_open = a11y.is_panel_open()
        panel_instances = a11y.panel_dom_instance_count()
        icon_still_visible = a11y.is_accessibility_button_visible()

    # Assert
    assert blocked_requests > 0, (
        "expected the simulated precondition to have genuinely blocked the accessibility "
        "script/style bundles (a no-op block would not honestly simulate a failure)"
    )
    assert console_errors_from_click == 0, (
        "expected the icon CLICK itself to register with no NEW JS console error "
        "(load-time errors from the simulated blocked script are a separate, disclosed precondition effect)"
    )
    assert icon_still_visible, "expected the accessibility icon to remain visible/unchanged"
    assert not panel_open, (
        "finding: with its script/style bundle genuinely blocked, the panel does not open at all -- "
        "see module docstring"
    )
    assert panel_instances == 0, "expected no partial/broken panel markup to render when its script is blocked"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("High Contrast toggle renders")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The High Contrast toggle control renders inside the accessibility panel")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134486")
def test_high_contrast_toggle_renders_in_panel(page):
    # ADO-134486 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the panel"):
        a11y.open_home()
        a11y.click_accessibility_button()

    with allure.step("Read the High Contrast toggle's visibility, label, and state"):
        is_visible = a11y.is_high_contrast_toggle_visible()
        label = a11y.high_contrast_row_label_text()
        state = a11y.high_contrast_toggle_state()

    # Assert
    assert is_visible, "expected a High Contrast toggle visible in the panel"
    assert label == "High contrast"
    assert state == "false", "expected the High Contrast toggle in an off/default state"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Zoom In / Zoom Out buttons render")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Zoom In (+) and Zoom Out (-) buttons render inside the accessibility panel")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134487")
def test_zoom_in_and_zoom_out_buttons_render_in_panel(page):
    # ADO-134487 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the panel"):
        a11y.open_home()
        a11y.click_accessibility_button()

    with allure.step("Read the Zoom In / Zoom Out buttons' visibility and enabled state"):
        zoom_in_visible = a11y.is_zoom_in_visible()
        zoom_out_visible = a11y.is_zoom_out_visible()
        zoom_in_enabled = a11y.is_zoom_in_enabled()
        zoom_out_enabled = a11y.is_zoom_out_enabled()

    # Assert
    assert zoom_in_visible, "expected a Zoom In (+) button visible in the panel"
    assert zoom_out_visible, "expected a Zoom Out (-) button visible in the panel"
    assert zoom_in_enabled
    assert zoom_out_enabled


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Reset/Normal View control renders")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Reset/Normal View control renders inside the accessibility panel")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134488")
def test_reset_normal_view_control_renders_in_panel(page):
    # ADO-134488 | PBI 129364
    # Live label reads "Reset" only (no separate "Normal View" string) -- the
    # case's own "/" wording anticipates this naming variance; not scripted
    # as a mismatch (see module/Page-Object docstring).
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the panel"):
        a11y.open_home()
        a11y.click_accessibility_button()

    with allure.step("Read the Reset/Normal View control's visibility and enabled state"):
        is_visible = a11y.is_reset_visible()
        is_enabled = a11y.is_reset_enabled()

    # Assert
    assert is_visible, "expected a Reset/Normal View control visible in the panel"
    assert is_enabled


# ── CMS-disable cases (134489, 134508) — reversible write on record 45370 ──
A11Y_SETTING_GROUP = "accessibility_header_config_singleton"
A11Y_SETTING = {
    "slug": "accessibility-header-configuration",
    "plural": "accessibilityheaderconfigurations",
    "code": "8f47e8e3-fcc8-a55f-845a-87b59c92c88f",  # entry 45370, the one live setting
    "label": "Accessibility Tools Enabled",
    "api_field": "accessibilityToolsEnabled",
}
PUBLIC_PROPAGATION_S = 180  # poll budget before a finding (QA lead, 2026-10)


def _poll_public(predicate, timeout: float = PUBLIC_PROPAGATION_S, poll: float = 10.0) -> bool:
    from core.utils.waits import WaitTimeoutError, wait_until

    try:
        wait_until(predicate, timeout=timeout, poll=poll)
        return True
    except WaitTimeoutError:
        return False


def _assert_icon_removed_after_cms_disable(page, real_records) -> None:
    a11y = AccessibilityToolsComponent(page)

    with allure.step("Baseline (logged out): the accessibility icon renders in the header"):
        a11y.open_home_anonymous()
        assert a11y.wait_accessibility_button_visible(), (
            "baseline failed: the icon is not on the public header before the CMS change")

    with allure.step("CMS: Accessibility Settings -> Accessibility Tools Enabled = False -> Publish"):
        item = real_records.change(**A11Y_SETTING, value=False)
        assert item["before"] is True, f"precondition: stored value was {item['before']!r}, expected True"
        assert item["workflow_status"] == "approved", item["workflow_status"]

    with allure.step("Clear cache / refresh the public site (logged out), polled up to 3 min"):
        def _icon_gone() -> bool:
            a11y.open_home_anonymous()
            return not a11y.is_accessibility_button_visible()

        gone = _poll_public(_icon_gone)
        allure.attach(page.screenshot(full_page=False), name="public header after disable",
                      attachment_type=allure.attachment_type.PNG)

    assert gone, "the accessibility icon still renders on the public header 3 min after disabling it in CMS"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Accessibility icon hidden when disabled in CMS")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The accessibility icon does not render when accessibility tools are disabled in CMS")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134489")
@pytest.mark.tc_134489
@pytest.mark.xdist_group(A11Y_SETTING_GROUP)
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_accessibility_icon_hidden_when_disabled_in_cms(page, real_records):
    """ADO-134489 | PBI 129364.

    Precondition (QA lead instruction 2026-10-21, reversible real write):
    the ONE site-wide AccessibilityHeaderConfiguration record (id 45370,
    `8f47e8e3-...`) gets Accessibility Tools Enabled = False, submitted in
    place on the saved TEST_USER session (admin; its Publish goes live
    directly -- the Site Content Editor login was locked that day; this is a
    config precondition, not a workflow-role case). Snapshot + screenshot
    first; `real_records` restores True and verifies it in teardown. The
    public read is a fresh logged-out context (`page`)."""
    _assert_icon_removed_after_cms_disable(page, real_records)


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Keyboard focusability of header interactive elements")
@allure.severity(allure.severity_level.MINOR)
@allure.title("All header interactive elements including the accessibility icon are keyboard-focusable")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134490")
def test_header_elements_including_accessibility_icon_are_keyboard_focusable(page):
    # ADO-134490 | PBI 129364
    # Real finding (see module docstring): Tab from a fresh page load hits
    # the same reCAPTCHA-badge/body oscillation trap header_component.py
    # documents for the logo (ADO #134246), but here NON-DETERMINISTICALLY --
    # observed both reached and not-reached across repeated live runs.
    # Scripted per the case's stated expected result regardless; whichever
    # way this run lands is a legitimate, honestly-observed result, not a
    # flaw in the test itself.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Load the homepage"):
        a11y.open_home()

    with allure.step("Press Tab repeatedly until focus reaches the accessibility icon"):
        reached = a11y.focus_accessibility_button_via_tab()

    with allure.step("Read the focus indicator, and whether Enter/Space activates the icon"):
        focus_indicator_visible = a11y.is_accessibility_button_focus_indicator_visible() if reached else False
        activatable_via_keyboard = a11y.activate_focused_accessibility_button_via_keyboard() if reached else False

    # Assert
    assert reached, "keyboard Tab never reached the accessibility icon"
    assert focus_indicator_visible, "expected a visible focus outline on the accessibility icon"
    assert activatable_via_keyboard, "expected the accessibility icon to be activatable with Enter/Space"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Accessibility icon visible on desktop viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The accessibility tools icon appears in the site header on desktop")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134628")
@pytest.mark.parametrize("page", [(1366, 768)], indirect=True)
def test_accessibility_icon_appears_in_header_on_desktop(page):
    # ADO-134628 | PBI 129364 — near-duplicate coverage of ADO-134481, more
    # specific (named desktop viewport 1366x768); automated as its own
    # distinct case per the task's coverage-flag instruction, not merged.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Load a public page at desktop viewport 1366x768"):
        a11y.open_home()

    with allure.step("Locate the header row containing the language switcher"):
        header_visible = a11y.header.is_header_visible()
        language_switcher_visible = a11y.header.is_language_switcher_visible()

    with allure.step("Observe the accessibility icon's box and style"):
        icon_visible = a11y.is_accessibility_button_visible()
        box_and_style = a11y.accessibility_button_box_and_style()

    # Assert
    assert header_visible, "expected the header to render at 1366x768"
    assert language_switcher_visible, "expected the language switcher visible alongside the icon-button row"
    assert icon_visible, "expected the accessibility icon visible in the icon-button container"
    assert box_and_style["width"] == 32
    assert box_and_style["height"] == 32
    assert box_and_style["padding"] == "10px"
    assert box_and_style["borderRadius"] == "8px"
    assert box_and_style["backgroundColor"] == "rgb(237, 237, 237)"  # #EDEDED


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Panel renders exactly 4 controls on desktop, no overlap")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking the accessibility icon opens a panel with all 4 required controls on desktop")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134630")
def test_clicking_accessibility_icon_opens_panel_with_exactly_4_controls_on_desktop(page):
    # ADO-134630 | PBI 129364 — near-duplicate coverage of ADO-134482, more
    # specific ("exactly 4 controls ... no overlap"); automated as its own
    # distinct case per the task's coverage-flag instruction, not merged.
    # Real finding (see module/Page-Object docstring): the live panel
    # renders 6 tool controls (adds a Dark Mode toggle and a Done button),
    # not 4 -- this test's "exactly 4" assertion is scripted per the case's
    # exact stated number and will honestly fail against the live count.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Load a public page (desktop) and click the accessibility icon"):
        a11y.open_home()
        a11y.click_accessibility_button()

    with allure.step("Read the resulting panel's control count and overlap"):
        panel_open = a11y.is_panel_open()
        controls = a11y.are_named_controls_visible()
        control_count = a11y.panel_tool_control_count()
        no_overlap = a11y.named_controls_have_no_overlap()

    # Assert
    assert panel_open, "expected the accessibility panel to open"
    assert controls["high_contrast"] and controls["zoom_in"] and controls["zoom_out"] and controls["reset"], (
        "expected all 4 named controls (High Contrast, Zoom In, Zoom Out, Reset/Normal View) visible"
    )
    assert control_count == 4, (
        f"expected exactly 4 controls in the panel, found {control_count} "
        "(finding: the panel also renders a Dark Mode toggle and a Done button — see module docstring)"
    )
    assert no_overlap, "expected the 4 named controls fully visible with no overlap"


# ═══════════════════════════════════════════════════════════════════════════
# Batch B — ADO #134629, #134631, #134632, #134633, #134634, #134635,
# #134636, #134661, #134662, #134665, #134666. See module docstring for the
# batch-B extraction log and coverage flag.
# ═══════════════════════════════════════════════════════════════════════════


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Accessibility icon renders on a mobile viewport")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The accessibility tools icon renders correctly on a mobile viewport")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134629")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_accessibility_icon_renders_correctly_on_mobile_viewport(page):
    # ADO-134629 | PBI 129364
    # Real finding (see Page-Object docstring): at 375x812 the icon box is
    # 32x32 with an ~8px gap to the language switcher -- no overlap.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Load the homepage at mobile viewport 375x812"):
        a11y.open_home()

    with allure.step("Observe the header row for the accessibility icon"):
        header_visible = a11y.header.is_header_visible()
        icon_visible = a11y.is_accessibility_button_visible()
        box_and_style = a11y.accessibility_button_box_and_style()
        overlapping_language_switcher = a11y.is_accessibility_button_overlapping_language_switcher()

    # Assert
    assert header_visible, "expected the header to render at the mobile viewport"
    assert icon_visible, "expected the accessibility icon visible at the mobile viewport, not clipped"
    assert not overlapping_language_switcher, "expected no overlap with the language switcher"
    assert box_and_style["width"] == 32
    assert box_and_style["height"] == 32


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Accessibility panel layout adapts on a mobile viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The accessibility panel layout adapts correctly on a mobile viewport")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134631")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_accessibility_panel_layout_adapts_on_mobile_viewport(page):
    # ADO-134631 | PBI 129364
    # Real finding (see Page-Object docstring): the panel renders full-width
    # (375px), stacked/paired controls, all 6 real controls (see batch-A's
    # #134630 finding) fit within 0..375px on the x-axis -- no horizontal
    # overflow with the panel open or closed.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Load the homepage at mobile viewport 375x812 and open the panel"):
        a11y.open_home()
        a11y.click_accessibility_button()

    with allure.step("Read the panel's layout, control visibility, and page overflow"):
        panel_open = a11y.is_panel_open()
        controls = a11y.are_named_controls_visible()
        controls_fit = a11y.panel_controls_fit_within_viewport()
        has_overflow = a11y.has_page_horizontal_overflow()

    # Assert
    assert panel_open, "expected the accessibility panel to open at the mobile viewport"
    assert all(controls.values()), "expected all named controls visible, adapted for mobile width"
    assert controls_fit, "expected every visible control's box to fit fully within the mobile viewport"
    assert not has_overflow, "expected no horizontal scroll on the mobile viewport with the panel open"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("High Contrast meets WCAG 2.1 AA contrast ratios")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The High Contrast theme meets WCAG 2.1 AA color contrast ratios")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134632")
def test_high_contrast_theme_meets_wcag_contrast_ratios(page):
    # ADO-134632 | PBI 129364
    # Real axe-core audit (axe-playwright-python==0.1.8, re-added to
    # requirements.txt for this exact test -- see requirements.txt and module
    # docstring), scoped to the `color-contrast` rule only. Confirmed live: 0
    # violations on the EN homepage with High Contrast active.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the panel"):
        a11y.open_home()
        a11y.click_accessibility_button()

    with allure.step("Activate High Contrast"):
        a11y.activate_high_contrast()
        theme_applied = a11y.is_high_contrast_active()
        background_color = a11y.page_background_color()

    with allure.step("Run an automated color-contrast (axe-core) audit on the resulting page"):
        violations = a11y.run_color_contrast_audit()

    # Assert
    assert theme_applied, "expected High Contrast to switch the page to its dark/high-contrast theme"
    assert background_color == "rgb(0, 0, 0)", "expected a dark background under High Contrast"
    assert violations == [], (
        f"expected 0 color-contrast violations under High Contrast, found "
        f"{len(violations)}: {[v['id'] for v in violations]}"
    )


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Keyboard focus indicator on the accessibility icon")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The accessibility icon shows a visible focus indicator when reached via keyboard Tab")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134633")
def test_accessibility_icon_shows_visible_focus_indicator_via_keyboard_tab(page):
    # ADO-134633 | PBI 129364
    # Same reCAPTCHA-badge/body oscillation trap ADO-134490 (batch A) and
    # HeaderComponent's logo case document -- NON-DETERMINISTIC reachability
    # here (see both docstrings). This test is scripted for real regardless,
    # and asserts a DISTINCT thing from #134490: the outline itself, by
    # comparing the button's unfocused-baseline style against its focused
    # style, not just whether Tab reached it.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Load the homepage and read the icon's unfocused baseline style"):
        a11y.open_home()
        baseline_style = a11y.accessibility_button_outline_style()

    with allure.step("Press Tab repeatedly until focus reaches the accessibility icon"):
        reached = a11y.focus_accessibility_button_via_tab()

    with allure.step("Read the icon's focused style and focus-indicator visibility"):
        focused_style = a11y.accessibility_button_outline_style() if reached else None
        focus_indicator_visible = a11y.is_accessibility_button_focus_indicator_visible() if reached else False

    # Assert
    assert reached, "keyboard Tab never reached the accessibility icon"
    assert focus_indicator_visible, "expected a visible focus outline/indicator on the accessibility icon"
    assert focused_style != baseline_style, (
        "expected the focused outline state to be visibly distinguishable from the unfocused default state"
    )


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Zoom In / Zoom Out default state")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Zoom In (+) and Zoom Out (−) buttons render enabled with correct icons/labels by default")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134634")
def test_zoom_in_and_zoom_out_buttons_enabled_with_correct_labels_by_default(page):
    # ADO-134634 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the panel on a fresh page load"):
        a11y.open_home()
        a11y.click_accessibility_button()

    with allure.step("Read the Zoom In / Zoom Out buttons' enabled state and labels"):
        zoom_in_enabled = a11y.is_zoom_in_enabled()
        zoom_out_enabled = a11y.is_zoom_out_enabled()
        zoom_in_label = a11y.zoom_in_label()
        zoom_out_label = a11y.zoom_out_label()

    # Assert
    assert zoom_in_enabled, "expected the Zoom In (+) button enabled by default"
    assert zoom_out_enabled, "expected the Zoom Out (−) button enabled by default"
    assert zoom_in_label != zoom_out_label, "expected distinct labels/icons for Zoom In and Zoom Out"
    assert "in" in zoom_in_label.lower()
    assert "out" in zoom_out_label.lower()


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Reset/Normal View control stays enabled across state changes")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Reset/Normal View button renders enabled regardless of current contrast/zoom state")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134635")
def test_reset_button_enabled_regardless_of_contrast_and_zoom_state(page):
    # ADO-134635 | PBI 129364
    # Real finding (see Page-Object docstring): after activating High
    # Contrast and clicking Zoom In once (zoom value read "110%"), closing
    # and reopening the panel, Reset still reads visible/enabled.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the panel at default state"):
        a11y.open_home()
        a11y.click_accessibility_button()
        reset_visible_default = a11y.is_reset_visible()
        reset_enabled_default = a11y.is_reset_enabled()

    with allure.step("Activate High Contrast and Zoom In once"):
        a11y.activate_high_contrast()
        a11y.click_zoom_in()
        zoom_value_after = a11y.zoom_value_text()

    with allure.step("Close and re-open the panel, then read the Reset button"):
        a11y.close_panel()
        a11y.click_accessibility_button()
        reset_visible_after = a11y.is_reset_visible()
        reset_enabled_after = a11y.is_reset_enabled()

    # Assert
    assert reset_visible_default and reset_enabled_default, "expected Reset visible/enabled at default state"
    assert zoom_value_after != "100%", "expected the Zoom In click to genuinely change the zoom value"
    assert reset_visible_after, "expected Reset still visible after Contrast+Zoom changes and a panel reopen"
    assert reset_enabled_after, "expected Reset still enabled after Contrast+Zoom changes and a panel reopen"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Header icon row mirrors correctly in Arabic (RTL)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The header icon-button row mirrors correctly in Arabic (RTL) layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134636")
def test_header_icon_button_row_mirrors_correctly_in_arabic_rtl(page):
    # ADO-134636 | PBI 129364
    # Real finding (see Page-Object docstring): the 3-icon utility cluster
    # (language switcher, accessibility icon, search icon) reads in the EXACT
    # reverse x-order under Arabic vs. English -- a genuine full mirror.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Load the homepage with Arabic active (RTL)"):
        a11y.open_home_arabic()

    with allure.step("Observe the header's icon-button row"):
        header_visible = a11y.header.is_header_visible()
        mirrored = a11y.is_utility_cluster_mirrored_rtl()
        positions = a11y.utility_cluster_x_positions()

    # Assert
    assert header_visible, "expected the RTL header to render"
    assert mirrored, (
        f"expected the utility cluster mirrored (search < accessibility < switcher), got {positions}"
    )


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("English site renders correctly with High Contrast active")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The English site renders correctly while High Contrast is active")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134661")
@pytest.mark.parametrize("page", [(1366, 768)], indirect=True)
def test_english_site_renders_correctly_with_high_contrast_active(page):
    # ADO-134661 | PBI 129364
    # Real finding (see Page-Object docstring): High Contrast applies with
    # zero navigation, and -- confirmed via a REAL page.goto to a second,
    # distinct content page, not a client-route change -- persists onto it.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the homepage in English at 1366x768"):
        a11y.open_home()
        url_before_toggle = a11y.current_url()

    with allure.step("Open the panel and activate High Contrast"):
        a11y.click_accessibility_button()
        a11y.activate_high_contrast()
        url_after_toggle = a11y.current_url()
        applied_on_first_page = a11y.is_high_contrast_active()
        background_on_first_page = a11y.page_background_color()

    with allure.step("Navigate to a second content page without turning High Contrast off"):
        a11y.open_second_content_page(locale="en")
        applied_on_second_page = a11y.is_high_contrast_active()
        background_on_second_page = a11y.page_background_color()

    # Assert
    assert url_after_toggle == url_before_toggle, "expected activating High Contrast to cause no navigation"
    assert applied_on_first_page, "expected High Contrast applied site-wide on the first page"
    assert background_on_first_page == "rgb(0, 0, 0)"
    assert applied_on_second_page, "expected High Contrast to persist onto a second, distinct content page"
    assert background_on_second_page == "rgb(0, 0, 0)", "expected the same dark-theme fidelity on the second page"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Arabic site renders correctly with High Contrast active")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Arabic site renders correctly while High Contrast is active")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134662")
@pytest.mark.parametrize("page", [(1366, 768)], indirect=True)
def test_arabic_site_renders_correctly_with_high_contrast_active(page):
    # ADO-134662 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the homepage in Arabic (RTL) at 1366x768"):
        a11y.open_home_arabic()
        mirrored_before = a11y.is_utility_cluster_mirrored_rtl()

    with allure.step("Open the panel and activate High Contrast"):
        a11y.click_accessibility_button()
        a11y.activate_high_contrast()
        applied_on_first_page = a11y.is_high_contrast_active()
        background_on_first_page = a11y.page_background_color()

    with allure.step("Confirm RTL is unchanged, then navigate to a second content page"):
        mirrored_after_contrast = a11y.is_utility_cluster_mirrored_rtl()
        a11y.open_second_content_page(locale="ar")
        applied_on_second_page = a11y.is_high_contrast_active()

    # Assert
    assert mirrored_before, "expected the RTL utility cluster mirrored before any toggle"
    assert applied_on_first_page, "expected High Contrast applied on the Arabic homepage"
    assert background_on_first_page == "rgb(0, 0, 0)"
    assert mirrored_after_contrast, "expected RTL mirroring unchanged after activating High Contrast"
    assert applied_on_second_page, "expected High Contrast to persist onto a second Arabic content page"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Dark Mode rendering in English")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The accessibility tools icon and panel render correctly in dark mode in English")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134665")
def test_accessibility_icon_and_panel_render_correctly_in_dark_mode_english(page):
    # ADO-134665 | PBI 129364
    # Scripted per the case's own literal "4 controls" wording (High
    # Contrast, Zoom In, Zoom Out, Reset) -- the real live count is 6 (see
    # batch-A's #134630 finding, and module docstring's coverage flag); not
    # re-derived or merged with #134630 here.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the homepage (EN, desktop) in light mode"):
        a11y.open_home()
        icon_visible_light = a11y.is_accessibility_button_visible()
        header_bg_light = a11y.header_background_color()

    with allure.step("Open the panel and switch to Dark Mode"):
        a11y.click_accessibility_button()
        a11y.switch_to_dark_mode()
        dark_state = a11y.dark_mode_toggle_state()
        header_bg_dark = a11y.header_background_color()
        icon_visible_dark = a11y.is_accessibility_button_visible()

    with allure.step("Inspect the panel's 4 named controls against the dark background"):
        controls = a11y.are_named_controls_visible()
        controls_legible = a11y.named_controls_legible_against_panel_background()

    # Assert
    assert icon_visible_light, "expected the icon visible in light mode"
    assert dark_state == "true", "expected the Dark Mode toggle to report an active/checked state"
    assert header_bg_dark != header_bg_light, "expected the header background to genuinely change in dark mode"
    assert icon_visible_dark, "expected the icon to remain visible/distinguishable against the dark header"
    assert all(controls.values()), "expected all 4 named controls visible in the dark panel"
    assert controls_legible, "expected each of the 4 named controls legible against the dark panel background"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Dark Mode rendering in Arabic")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The accessibility tools icon and panel render correctly in dark mode in Arabic")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.traceability("ADO-134666")
def test_accessibility_icon_and_panel_render_correctly_in_dark_mode_arabic(page):
    # ADO-134666 | PBI 129364
    # Real finding (see Page-Object docstring): toggling Dark Mode on the
    # Arabic page changes neither `dir` nor the icon's x-position -- dark
    # mode is a pure color/style change, RTL layout is unaffected.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the homepage (AR, desktop) in light mode"):
        a11y.open_home_arabic()
        icon_x_before = a11y.accessibility_button_x_position()

    with allure.step("Open the panel and switch to Dark Mode"):
        a11y.click_accessibility_button()
        a11y.switch_to_dark_mode()
        icon_x_after = a11y.accessibility_button_x_position()
        header_bg_dark = a11y.header_background_color()
        icon_visible_dark = a11y.is_accessibility_button_visible()
        panel_direction = a11y.panel_direction()

    with allure.step("Inspect the panel's controls against the dark background, RTL-aligned"):
        controls_legible = a11y.named_controls_legible_against_panel_background()

    # Assert
    assert icon_visible_dark, "expected the icon visible against the dark header"
    assert icon_x_after == icon_x_before, "expected the icon to stay in its mirrored RTL position after dark mode"
    assert header_bg_dark != "rgb(255, 255, 255)", "expected the header background to genuinely darken"
    assert panel_direction == "rtl", "expected the panel aligned per RTL"
    assert controls_legible, "expected the panel's controls legible against the dark background"


# ═══════════════════════════════════════════════════════════════════════════
# Batch C (2026-10-21) — ADO #134502-#134510, #134524-#134530, #134637-#134639,
# #134653-#134657, #134660, #134663, #134664, #134667, #134668 (28 cases,
# Web only). Every test runs in an ANONYMOUS context ({"auth": False}) — a
# public visitor, never the cached CMS session. Live mechanics these tests
# rely on are logged in the Page Object's "Batch C" block (zoom = the
# `--qc-a11y-zoom-scale` CSS variable, 0.1 per click, 80%..140%; state in
# sessionStorage + the `qcTheme` cookie; Reset also returns dark mode to
# light). Theme/contrast are asserted on the document (`data-theme`,
# `qc-a11y-contrast`), never on a switch's aria-checked alone.
# ═══════════════════════════════════════════════════════════════════════════

ANON = {"auth": False}
ANON_DESKTOP_1366 = {"auth": False, "viewport": (1366, 768)}
ANON_MOBILE_390 = {"auth": False, "viewport": (390, 844)}

DEFAULT_ROOT_FONT_PX = 16.0     # <html> font-size at default zoom (measured live)
DEFAULT_ZOOM_SCALE = 1.0
ZOOM_STEP = 0.1                 # one product zoom increment (100% -> 110%)
HIGH_CONTRAST_BACKGROUND = "rgb(0, 0, 0)"
DEFAULT_BACKGROUND = "rgb(255, 255, 255)"
LAYOUT_TOLERANCE_PX = 2         # bug-rules.md Rule 1 — layout (non-image) tolerance
FULL_WALK_MAX_PRESSES = 300     # Contact Us ring measured at 77 presses
KEYBOARD_HIGHLIGHT_LABEL = "Keyboard Navigation Highlight"


def _step(scale: float, steps: int) -> float:
    return round(scale + steps * ZOOM_STEP, 2)


def _axe_summary(violations: list) -> list:
    """Failing node selector + axe's own contrast message, for the report."""
    return [f"{n['target']}: {(n.get('any') or [{}])[0].get('message', '')[:120]}"
            for v in violations for n in v["nodes"]]


def _boxes_shifted(before: dict, after: dict, tol: int) -> list:
    """Names of layout boxes whose x/y/width/height moved by more than `tol`."""
    shifted = []
    pairs = [("header", before["header"], after["header"]), ("main", before["main"], after["main"]),
             ("footer", before["footer"], after["footer"])]
    pairs += [(f"section[{i}].{b['cls']}", b, a)
              for i, (b, a) in enumerate(zip(before["sections"], after["sections"]))]
    for name, b, a in pairs:
        if b is None or a is None:
            shifted.append(f"{name} (missing)")
            continue
        if any(abs(b[k] - a[k]) > tol for k in ("x", "y", "width", "height")):
            shifted.append(f"{name}: {b} -> {a}")
    return shifted


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("High Contrast applies in real time")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that activating High Contrast applies the high-contrast theme site-wide in real time")
@allure.label("pbi", PBI)
@allure.label("testcase", "134502")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.pbi_129364
@pytest.mark.tc_134502
@pytest.mark.traceability("ADO-134502")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_high_contrast_applies_site_wide_in_real_time_without_reload(page):
    # ADO-134502 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()
    a11y.mark_document()

    # Act
    with allure.step("Open the accessibility panel"):
        a11y.open_panel()
        panel_open = a11y.is_panel_open()

    with allure.step("Click the High Contrast toggle"):
        a11y.activate_high_contrast()
        contrast_active = a11y.is_high_contrast_active()
        background = a11y.page_background_color()
        text_color = a11y.body_text_color()

    with allure.step("Observe that no page reload / navigation occurred"):
        same_document = a11y.is_same_document_since_mark()

    # Assert
    assert panel_open, "expected the accessibility panel to open"
    assert contrast_active, "expected <html> to carry qc-a11y-contrast immediately after the click"
    assert background == HIGH_CONTRAST_BACKGROUND, f"expected a dark background, got {background}"
    assert text_color != background, f"expected high-contrast text against the background, got {text_color}"
    assert same_document, "expected no page reload / navigation when toggling High Contrast"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Zoom In increases text size")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that clicking Zoom In increases page text size by one increment without reload")
@allure.label("pbi", PBI)
@allure.label("testcase", "134503")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.pbi_129364
@pytest.mark.tc_134503
@pytest.mark.traceability("ADO-134503")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_zoom_in_increases_text_size_by_one_increment_without_reload(page):
    # ADO-134503 | PBI 129364 — the case's 16px -> 18px is an "e.g."; the
    # oracle is "one defined increment" = one product zoom step (live: +10%,
    # 16px -> 17.6px).
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Open the accessibility panel"):
        a11y.open_panel()
        a11y.mark_document()

    with allure.step("Note the current base font size"):
        font_before = a11y.root_font_size_px()
        scale_before = a11y.zoom_scale()

    with allure.step("Click Zoom In (+) once"):
        a11y.click_zoom_in()
        font_after = a11y.root_font_size_px()
        scale_after = a11y.zoom_scale()
        same_document = a11y.is_same_document_since_mark()

    # Assert
    assert font_after > font_before, f"expected the base font size to grow, {font_before}px -> {font_after}px"
    assert scale_after == _step(scale_before, 1), (
        f"expected exactly one zoom increment, scale {scale_before} -> {scale_after}"
    )
    assert same_document, "expected no page reload on Zoom In"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Zoom Out decreases text size")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that clicking Zoom Out decreases page text size by one increment without reload")
@allure.label("pbi", PBI)
@allure.label("testcase", "134504")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.pbi_129364
@pytest.mark.tc_134504
@pytest.mark.traceability("ADO-134504")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_zoom_out_decreases_text_size_by_one_increment_without_reload(page):
    # ADO-134504 | PBI 129364 — "e.g. 14px" in the case; live one step is
    # -10% (16px -> 14.4px).
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Open the accessibility panel"):
        a11y.open_panel()
        a11y.mark_document()

    with allure.step("Note the current base font size"):
        font_before = a11y.root_font_size_px()
        scale_before = a11y.zoom_scale()

    with allure.step("Click Zoom Out (-) once"):
        a11y.click_zoom_out()
        font_after = a11y.root_font_size_px()
        scale_after = a11y.zoom_scale()
        same_document = a11y.is_same_document_since_mark()

    # Assert
    assert font_after < font_before, f"expected the base font size to shrink, {font_before}px -> {font_after}px"
    assert scale_after == _step(scale_before, -1), (
        f"expected exactly one zoom decrement, scale {scale_before} -> {scale_after}"
    )
    assert same_document, "expected no page reload on Zoom Out"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Reset restores defaults")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that Reset/Normal View restores default font size and contrast")
@allure.label("pbi", PBI)
@allure.label("testcase", "134505")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.pbi_129364
@pytest.mark.tc_134505
@pytest.mark.traceability("ADO-134505")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_reset_restores_default_font_size_and_contrast(page):
    # ADO-134505 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()
    font_default = a11y.root_font_size_px()

    # Act
    with allure.step("Apply High Contrast and click Zoom In twice"):
        a11y.open_panel()
        a11y.mark_document()
        a11y.activate_high_contrast()
        a11y.click_zoom_in()
        a11y.click_zoom_in()
        contrast_applied = a11y.is_high_contrast_active()
        scale_zoomed = a11y.zoom_scale()

    with allure.step("Click Reset/Normal View"):
        a11y.click_reset()
        contrast_after_reset = a11y.is_high_contrast_active()
        font_after_reset = a11y.root_font_size_px()
        scale_after_reset = a11y.zoom_scale()
        same_document = a11y.is_same_document_since_mark()

    # Assert
    assert contrast_applied, "precondition: High Contrast must be applied"
    assert scale_zoomed == _step(DEFAULT_ZOOM_SCALE, 2), f"expected two zoom increments, got scale {scale_zoomed}"
    assert not contrast_after_reset, "expected Reset to revert to the default (non-high-contrast) theme"
    assert font_after_reset == font_default, f"expected base font {font_default}px after Reset, got {font_after_reset}px"
    assert scale_after_reset == DEFAULT_ZOOM_SCALE
    assert same_document, "expected no page reload on Reset"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Settings persist across navigation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that accessibility settings persist across page navigation within the same browser session")
@allure.label("pbi", PBI)
@allure.label("testcase", "134506")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.pbi_129364
@pytest.mark.tc_134506
@pytest.mark.traceability("ADO-134506")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_accessibility_settings_persist_to_about_us_in_same_session(page):
    # ADO-134506 | PBI 129364 — About Us opened by its direct path (a real
    # full navigation): HeaderComponent.NAV_LINK_ABOUT_US is stale, "About
    # Us" is now a mega-menu button (see Page-Object Batch C note).
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Enable High Contrast and Zoom In once on the homepage"):
        a11y.enable_high_contrast()
        a11y.open_panel()
        a11y.click_zoom_in()
        a11y.close_panel()
        contrast_home = a11y.is_high_contrast_active()
        font_home = a11y.root_font_size_px()

    with allure.step("Navigate to About Us without closing the browser"):
        a11y.open_about_us()
        url_about = a11y.current_url()
        contrast_about = a11y.is_high_contrast_active()
        font_about = a11y.root_font_size_px()

    # Assert
    assert contrast_home, "expected High Contrast applied on the homepage"
    assert font_home > DEFAULT_ROOT_FONT_PX, f"expected an increased font size on the homepage, got {font_home}px"
    assert "about-us" in url_about, f"expected the About Us page, got {url_about}"
    assert contrast_about, "expected High Contrast still applied on About Us"
    assert font_about == font_home, f"expected the increased font size ({font_home}px) on About Us, got {font_about}px"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Keyboard reachability (WCAG 2.1 AA)")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that all interactive elements on a page are reachable and operable via Tab-key keyboard navigation (WCAG 2.1 AA)")
@allure.label("pbi", PBI)
@allure.label("testcase", "134507")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.pbi_129364
@pytest.mark.tc_134507
@pytest.mark.traceability("ADO-134507")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_all_interactive_elements_reachable_and_operable_via_tab_on_contact_us(page):
    """ADO-134507 | PBI 129364 — Contact Us (buttons, links, form). The walk
    must CLOSE the focus ring (no trap, no truncated prefix) before any
    "every element" assertion means anything. Form inputs draw their focus
    ring on the wrapping div (:focus-within) — credited by
    focus_audit_walk() only when the wrapper's style actually changes on
    focus. Note: the footer newsletter input is the subject of existing
    Azure bug #147180 (no focus indicator) — if it is the only offender,
    that is the known bug, not a new finding."""
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_second_content_page(locale="en")
    clickable_before = a11y.clickable_element_keys()

    # Act
    with allure.step("Press Tab repeatedly through the entire page"):
        walk = a11y.focus_audit_walk(FULL_WALK_MAX_PRESSES)
        clickable_after = a11y.clickable_element_keys()

    with allure.step("Open the accessibility panel via keyboard and Tab through its controls"):
        a11y.blur_active_element()
        icon_reached = a11y.focus_accessibility_button_via_tab()
        panel_opened = a11y.activate_focused_accessibility_button_via_keyboard() if icon_reached else False
        hc_focused = a11y.focus_panel_control_via_tab(a11y.HIGH_CONTRAST_SWITCH) if panel_opened else False
        if hc_focused:
            a11y.press_key("Space")
        hc_activated = a11y.is_high_contrast_active()
        zoom_in_focused = a11y.focus_panel_control_via_tab(a11y.ZOOM_IN_BUTTON) if panel_opened else False
        if zoom_in_focused:
            a11y.press_key("Enter")
        scale_after_zoom_in = a11y.zoom_scale()
        zoom_out_focused = a11y.focus_panel_control_via_tab(a11y.ZOOM_OUT_BUTTON) if panel_opened else False
        if zoom_out_focused:
            a11y.press_key("Enter")
        scale_after_zoom_out = a11y.zoom_scale()
        reset_focused = a11y.focus_panel_control_via_tab(a11y.RESET_BUTTON) if panel_opened else False
        if reset_focused:
            a11y.press_key("Enter")
        contrast_after_reset = a11y.is_high_contrast_active()
        scale_after_reset = a11y.zoom_scale()

    # Assert
    stops = [s for s in walk["stops"] if s and not s["isBody"]]
    assert walk["completed"], (
        f"focus ring never closed in {walk['presses']} presses — focus trapped or walk truncated"
    )
    focus_keys = {s["key"] for s in stops}
    stable_clickable = [k for k in clickable_before if k in clickable_after]
    skipped = [k for k in stable_clickable if k not in focus_keys]
    assert not skipped, f"{len(skipped)} interactive element(s) never reached by Tab: {skipped[:10]}"
    no_indicator = [f"{s['tag']}.{s['className'][:40]} '{s['text'][:20]}'"
                    for s in stops if s["tag"] != "iframe" and not s.get("indicated")]
    assert not no_indicator, f"{len(no_indicator)} focus stop(s) show no visible focus indicator: {no_indicator}"
    order = {"header": 0, "main": 1, "footer": 2}
    regions = [order[s["region"]] for s in stops[:-1] if s.get("region") in order]
    assert regions == sorted(regions), "expected a logical Tab order: header -> main content -> footer"
    assert icon_reached, "keyboard Tab never reached the accessibility icon"
    assert panel_opened, "expected Enter on the focused icon to open the panel"
    assert hc_focused and hc_activated, "expected High Contrast focusable and activatable with Space"
    assert zoom_in_focused and scale_after_zoom_in == _step(DEFAULT_ZOOM_SCALE, 1), (
        f"expected Zoom In focusable and activatable with Enter (scale {scale_after_zoom_in})"
    )
    assert zoom_out_focused and scale_after_zoom_out == DEFAULT_ZOOM_SCALE, (
        f"expected Zoom Out focusable and activatable with Enter (scale {scale_after_zoom_out})"
    )
    assert reset_focused and not contrast_after_reset and scale_after_reset == DEFAULT_ZOOM_SCALE, (
        "expected Reset focusable and activatable with Enter, restoring default contrast and zoom"
    )


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Accessibility icon hidden when disabled in CMS")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling the accessibility widget in CMS removes it from the frontend after cache refresh")
@allure.label("pbi", PBI)
@allure.label("testcase", "134508")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.pbi_129364
@pytest.mark.tc_134508
@pytest.mark.traceability("ADO-134508")
@pytest.mark.xdist_group(A11Y_SETTING_GROUP)
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_disabling_widget_in_cms_removes_icon_from_frontend(page, real_records):
    """ADO-134508 | PBI 129364. Same reversible real write on record 45370
    as 134489 (see that test): set Enabled = False, publish, then reload
    the public site logged out until the cache refreshes (<= 3 min)."""
    _assert_icon_removed_after_cms_disable(page, real_records)


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Image alt text (EN)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an image published with valid bilingual alt text renders the correct alt attribute on the EN frontend page")
@allure.label("pbi", PBI)
@allure.label("testcase", "134509")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129364
@pytest.mark.tc_134509
@pytest.mark.traceability("ADO-134509")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_image_alt_text_renders_on_english_page(page, qctest_records):
    """ADO-134509 | PBI 129364.

    Precondition (QA lead decision 2026-10-21): the image is a disposable
    `QCTEST-134509-partner-*` Strategic Partner record (the Home carousel
    renders its logo with the record's own Logo Alt Text), created and
    Published + Active through Object Authoring as TEST_USER (admin; Publish
    goes live directly -- the Editor login was refused that day) and deleted
    in teardown. The public read is a fresh logged-out context (`page`). The
    logo is matched by its record code in `src`, never by alt alone."""
    marker = f"QCTEST-134509-partner-{uuid.uuid4().hex[:6]}"
    admin = StrategicPartnerQctest(qctest_records.page)
    partners = StrategicPartnersPage(page)

    with allure.step("In CMS, publish an image with Alt Text (EN/AR) -- QCTEST partner, Active"):
        code = qctest_records.create(admin, {
            "name": (marker, f"{marker} شريك"),
            "alt": (IMAGE_ALT_EN, IMAGE_ALT_AR),
            "order": "9900",
            "active": True,
            "logo_en": QCTEST_PNG,
            "logo_ar": QCTEST_PNG,
        }, marker)
        admin.open_code(code)
        stored = {"alt_en": admin.value("alt"), "alt_ar": admin.value("alt", locale="ar"),
                  "active": admin.flag("active")}
        badge = admin.row_badge(code)

    with allure.step("Load the corresponding page (Home) in EN locale, logged out"):
        alts = partners.poll_record_logo(code, locale="en")

    with allure.step("Inspect the image element's alt attribute"):
        allure.attach(f"record={code} stored={stored} badge={badge} rendered_alts={alts}",
                      name="134509 evidence", attachment_type=allure.attachment_type.TEXT)

    # Assert
    assert stored == {"alt_en": IMAGE_ALT_EN, "alt_ar": IMAGE_ALT_AR, "active": True}, stored
    assert badge == "PUBLISHED", f"expected the QCTEST image record Published, list badge reads {badge!r}"
    assert alts, f"the QCTEST image (record {code}) never rendered on the EN Home page within 3 min"
    assert alts == [IMAGE_ALT_EN], f"EN alt attribute(s) rendered: {alts!r}"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Image alt text (AR)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the same image renders the correct Arabic alt attribute on the AR frontend page")
@allure.label("pbi", PBI)
@allure.label("testcase", "134510")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129364
@pytest.mark.tc_134510
@pytest.mark.traceability("ADO-134510")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_image_alt_text_renders_on_arabic_page(page, qctest_records):
    """ADO-134510 | PBI 129364. Same disposable-record precondition as
    ADO-134509 (its own `QCTEST-134510-partner-*` record, so the case runs on
    its own); read on the AR Home page, logged out."""
    marker = f"QCTEST-134510-partner-{uuid.uuid4().hex[:6]}"
    admin = StrategicPartnerQctest(qctest_records.page)
    partners = StrategicPartnersPage(page)

    with allure.step("Precondition: the image published with EN + AR alt text (QCTEST partner, Active)"):
        code = qctest_records.create(admin, {
            "name": (marker, f"{marker} شريك"),
            "alt": (IMAGE_ALT_EN, IMAGE_ALT_AR),
            "order": "9900",
            "active": True,
            "logo_en": QCTEST_PNG,
            "logo_ar": QCTEST_PNG,
        }, marker)
        admin.open_code(code)
        stored_ar = admin.value("alt", locale="ar")

    with allure.step("Load the corresponding page in AR locale, logged out"):
        alts = partners.poll_record_logo(code, locale="ar")
        direction = partners.page_direction()

    with allure.step("Inspect the image element's alt attribute"):
        allure.attach(f"record={code} stored_ar={stored_ar!r} dir={direction} rendered_alts={alts}",
                      name="134510 evidence", attachment_type=allure.attachment_type.TEXT)

    # Assert
    assert stored_ar == IMAGE_ALT_AR, f"Arabic alt text stored as {stored_ar!r}"
    assert direction == "rtl", f"expected the AR page in RTL, html dir={direction!r}"
    assert alts, f"the QCTEST image (record {code}) never rendered on the AR Home page within 3 min"
    assert alts == [IMAGE_ALT_AR], f"AR alt attribute(s) rendered: {alts!r}"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("High Contrast toggles off")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that High Contrast can be toggled off after being toggled on (inverse control state)")
@allure.label("pbi", PBI)
@allure.label("testcase", "134524")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134524
@pytest.mark.traceability("ADO-134524")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_high_contrast_can_be_toggled_off_after_on(page):
    # ADO-134524 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Open the accessibility panel"):
        a11y.open_panel()
        panel_open = a11y.is_panel_open()

    with allure.step("Click High Contrast to enable it"):
        a11y.activate_high_contrast()
        contrast_on = a11y.is_high_contrast_active()

    with allure.step("Click High Contrast again to disable it"):
        a11y.activate_high_contrast()
        contrast_after_second_click = a11y.is_high_contrast_active()
        background = a11y.page_background_color()

    # Assert
    assert panel_open
    assert contrast_on, "expected the high-contrast theme to apply"
    assert not contrast_after_second_click, "expected the page to revert to the default theme without Reset"
    assert background == DEFAULT_BACKGROUND, f"expected the default background, got {background}"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Zoom In upper limit")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that repeated Zoom In clicks stop increasing font size once the maximum zoom level is reached")
@allure.label("pbi", PBI)
@allure.label("testcase", "134525")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134525
@pytest.mark.traceability("ADO-134525")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_repeated_zoom_in_plateaus_at_maximum(page):
    # ADO-134525 | PBI 129364 — live maximum is 140% (22.4px) after 4 clicks.
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()
    a11y.open_panel()
    a11y.start_console_capture()
    console_baseline = a11y.console_message_count()

    # Act
    with allure.step("Click Zoom In repeatedly (10 times)"):
        sizes = [a11y.root_font_size_px()]
        for _ in range(10):
            a11y.click_zoom_in()
            sizes.append(a11y.root_font_size_px())
        overflow = a11y.has_page_horizontal_overflow()
        console_errors = a11y.console_error_count_since(console_baseline)

    # Assert
    assert all(b >= a for a, b in zip(sizes, sizes[1:])), f"font size must never shrink while zooming in: {sizes}"
    assert sizes[-1] > sizes[0], f"expected the font size to increase incrementally: {sizes}"
    assert sizes[-1] == sizes[-2] == sizes[-3], f"expected the font size to plateau at a maximum: {sizes}"
    assert not overflow, "expected no layout breakage (horizontal overflow) at maximum zoom"
    assert console_errors == 0, f"expected no console error while zooming, got {console_errors}"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("High Contrast rapid double-click")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that rapidly double-clicking the High Contrast toggle does not leave the UI in an inconsistent state")
@allure.label("pbi", PBI)
@allure.label("testcase", "134527")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_129364
@pytest.mark.tc_134527
@pytest.mark.traceability("ADO-134527")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_high_contrast_rapid_double_click_settles_consistently(page):
    # ADO-134527 | PBI 129364 — a double-click registers two clicks, so the
    # consistent final state is OFF; the document state must agree with the
    # switch and with itself (one class token, no console error).
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()
    a11y.open_panel()
    a11y.start_console_capture()
    console_baseline = a11y.console_message_count()

    # Act
    with allure.step("Double-click the High Contrast toggle in rapid succession"):
        a11y.double_click_high_contrast()
        contrast_active = a11y.is_high_contrast_active()
        switch_checked = a11y.is_high_contrast_switch_checked()
        class_tokens = a11y.high_contrast_class_token_count()
        console_errors = a11y.console_error_count_since(console_baseline)

    # Assert
    assert contrast_active == switch_checked, (
        f"inconsistent state: document high-contrast={contrast_active}, switch checked={switch_checked}"
    )
    assert not contrast_active, "expected an even number of registered clicks (2) to leave High Contrast off"
    assert class_tokens <= 1, f"expected no duplicate qc-a11y-contrast class, found {class_tokens}"
    assert console_errors == 0, f"expected no console error, got {console_errors}"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Keyboard Navigation Highlight ON")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that enabling the keyboard navigation highlight shows a visible focus indicator on interactive elements")
@allure.label("pbi", PBI)
@allure.label("testcase", "134528")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134528
@pytest.mark.traceability("ADO-134528")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_keyboard_navigation_highlight_on_shows_enhanced_focus(page):
    # ADO-134528 | PBI 129364 — the live panel's rows are "Dark mode",
    # "High contrast", "Zoom"; no Keyboard Navigation Highlight toggle was
    # found at extraction. Asserted per the case; the remaining steps cannot
    # run without the toggle, so its presence is checked first.
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Open the accessibility panel"):
        a11y.open_panel()
        row_labels = a11y.panel_row_labels()
        toggle_present = a11y.is_keyboard_highlight_toggle_present()

    assert toggle_present, (
        f"expected a '{KEYBOARD_HIGHLIGHT_LABEL}' toggle in the panel; rows found: {row_labels}"
    )
    initial_state = a11y.keyboard_highlight_toggle_state()

    with allure.step("Enable the Keyboard Navigation Highlight toggle"):
        a11y.click_keyboard_highlight_toggle()
        state_after_enable = a11y.keyboard_highlight_toggle_state()

    with allure.step("Close the panel and Tab to the first 3 interactive elements"):
        a11y.close_panel()
        a11y.blur_active_element()
        focused = a11y.tab_sequence(3)

    # Assert
    assert initial_state == "false", "expected the toggle OFF by default"
    assert state_after_enable == "true", "expected the toggle ON after enabling"
    assert all(d and d["hasVisibleFocusIndicator"] for d in focused), (
        f"expected an enhanced focus outline on each of the first 3 elements: {focused}"
    )
    outlines = {(d["outlineStyle"], d["outlineWidth"], d["outlineColor"], d["boxShadow"]) for d in focused}
    assert len(outlines) == 1, f"expected the same enhanced outline on every element, got {outlines}"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Keyboard Navigation Highlight OFF")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that disabling the keyboard navigation highlight reverts interactive elements to the default browser focus outline")
@allure.label("pbi", PBI)
@allure.label("testcase", "134529")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134529
@pytest.mark.traceability("ADO-134529")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_keyboard_navigation_highlight_off_reverts_to_default_focus(page):
    # ADO-134529 | PBI 129364 — same missing-toggle note as ADO-134528.
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Open the accessibility panel with the highlight toggle ON"):
        a11y.open_panel()
        row_labels = a11y.panel_row_labels()
        toggle_present = a11y.is_keyboard_highlight_toggle_present()

    assert toggle_present, (
        f"expected a '{KEYBOARD_HIGHLIGHT_LABEL}' toggle in the panel; rows found: {row_labels}"
    )

    with allure.step("Record the enhanced focus style with the toggle ON"):
        if a11y.keyboard_highlight_toggle_state() != "true":
            a11y.click_keyboard_highlight_toggle()
        a11y.close_panel()
        a11y.blur_active_element()
        style_on = a11y.tab_sequence(1)[0]

    with allure.step("Turn the toggle OFF, close the panel and Tab to the first element"):
        a11y.open_panel()
        a11y.click_keyboard_highlight_toggle()
        state_off = a11y.keyboard_highlight_toggle_state()
        a11y.close_panel()
        a11y.blur_active_element()
        style_off = a11y.tab_sequence(1)[0]

    # Assert
    assert state_off == "false", "expected the toggle to switch OFF"
    assert style_on["key"] == style_off["key"], "expected the same first element to be focused both times"
    assert (style_off["outlineStyle"], style_off["outlineWidth"], style_off["boxShadow"]) != (
        style_on["outlineStyle"], style_on["outlineWidth"], style_on["boxShadow"]
    ), "expected the baseline focus outline, not the enhanced indicator, with the toggle OFF"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Reset clears persisted state")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that Reset restores contrast and zoom to site defaults and clears the persisted session state")
@allure.label("pbi", PBI)
@allure.label("testcase", "134530")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129364
@pytest.mark.tc_134530
@pytest.mark.traceability("ADO-134530")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_reset_restores_defaults_and_clears_persisted_session_state(page):
    # ADO-134530 | PBI 129364 — the case's 150% needs 5 Zoom In clicks at
    # the live 10% step; the live maximum measured at extraction is 140%.
    # The whole flow still runs at whatever zoom is reached, and the 150%
    # expectation is asserted LAST so the Reset/reload checks are reported
    # on their own merits.
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Set contrast to High and zoom to 150%, confirm values persist"):
        a11y.enable_high_contrast()
        a11y.open_panel()
        for _ in range(5):
            a11y.click_zoom_in()
        a11y.close_panel()
        a11y.reload()
        contrast_persisted = a11y.is_high_contrast_active()
        scale_persisted = a11y.zoom_scale()

    with allure.step("Open the accessibility panel"):
        a11y.open_panel()
        panel_contrast_checked = a11y.is_high_contrast_switch_checked()
        panel_zoom_text = a11y.zoom_value_text()

    with allure.step("Click Reset to Default"):
        a11y.click_reset()
        contrast_after_reset = a11y.is_high_contrast_active()
        scale_after_reset = a11y.zoom_scale()
        panel_contrast_after_reset = a11y.is_high_contrast_switch_checked()
        panel_zoom_after_reset = a11y.zoom_value_text()

    with allure.step("Reload the page"):
        a11y.reload()
        contrast_after_reload = a11y.is_high_contrast_active()
        scale_after_reload = a11y.zoom_scale()
        persisted_after_reload = a11y.has_persisted_customization()

    with allure.step("Reopen the accessibility panel"):
        a11y.open_panel()
        panel_contrast_reopened = a11y.is_high_contrast_switch_checked()
        panel_zoom_reopened = a11y.zoom_value_text()

    # Assert
    assert contrast_persisted, "expected High Contrast to persist across a reload"
    assert panel_contrast_checked, "expected the panel to show High Contrast active"
    assert not contrast_after_reset and scale_after_reset == DEFAULT_ZOOM_SCALE, (
        "expected Reset to revert contrast and zoom immediately"
    )
    assert not panel_contrast_after_reset and panel_zoom_after_reset == "100%", (
        f"expected the panel controls to update to default, got contrast="
        f"{panel_contrast_after_reset}, zoom={panel_zoom_after_reset}"
    )
    assert not contrast_after_reload and scale_after_reload == DEFAULT_ZOOM_SCALE, (
        "expected default contrast and 100% zoom after reload"
    )
    assert not persisted_after_reload, "expected no residual persisted override after Reset + reload"
    assert not panel_contrast_reopened and panel_zoom_reopened == "100%", (
        "expected the reopened panel to show default / 100%"
    )
    assert panel_zoom_text == "150%" and scale_persisted == 1.5, (
        f"expected 150% zoom to be settable and persist, observed {panel_zoom_text} (scale {scale_persisted})"
    )


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Full happy-path journey without reload")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a visitor can open the accessibility panel, apply High Contrast, zoom in, zoom out, and reset — all in real time without a page reload")
@allure.label("pbi", PBI)
@allure.label("testcase", "134637")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.accessibility
@pytest.mark.uat
@pytest.mark.pbi_129364
@pytest.mark.tc_134637
@pytest.mark.traceability("ADO-134637")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_full_accessibility_journey_applies_in_real_time_without_reload(page):
    # ADO-134637 | PBI 129364 — "all 4 controls" checked as the 4 NAMED
    # controls being visible (the panel renders 6; see #134630 note).
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Load a public page and note the DOM load marker"):
        a11y.open_home()
        a11y.mark_document()
        font_default = a11y.root_font_size_px()

    with allure.step("Click the accessibility icon"):
        a11y.open_panel()
        controls = a11y.are_named_controls_visible()
        same_doc_open = a11y.is_same_document_since_mark()

    with allure.step("Click High Contrast"):
        a11y.activate_high_contrast()
        contrast_on = a11y.is_high_contrast_active()
        background_on = a11y.page_background_color()
        same_doc_contrast = a11y.is_same_document_since_mark()

    with allure.step("Click Zoom In (+) once"):
        a11y.click_zoom_in()
        font_zoom_in = a11y.root_font_size_px()
        same_doc_zoom_in = a11y.is_same_document_since_mark()

    with allure.step("Click Zoom Out (-) once"):
        a11y.click_zoom_out()
        font_zoom_out = a11y.root_font_size_px()
        same_doc_zoom_out = a11y.is_same_document_since_mark()

    with allure.step("Click Reset/Normal View"):
        a11y.click_reset()
        contrast_after_reset = a11y.is_high_contrast_active()
        font_after_reset = a11y.root_font_size_px()
        same_doc_reset = a11y.is_same_document_since_mark()

    # Assert
    assert all(controls.values()), f"expected all 4 named controls visible: {controls}"
    assert same_doc_open, "no page reload expected on opening the panel"
    assert contrast_on and background_on == HIGH_CONTRAST_BACKGROUND, "expected the high-contrast theme instantly"
    assert same_doc_contrast, "no page reload expected on High Contrast"
    assert font_zoom_in > font_default, f"expected Zoom In to grow the font ({font_default} -> {font_zoom_in})"
    assert same_doc_zoom_in, "no page reload expected on Zoom In"
    assert font_zoom_out < font_zoom_in and font_zoom_out == font_default, (
        f"expected Zoom Out to step back to default ({font_zoom_in} -> {font_zoom_out})"
    )
    assert same_doc_zoom_out, "no page reload expected on Zoom Out"
    assert not contrast_after_reset and font_after_reset == font_default, "expected Reset to restore defaults"
    assert same_doc_reset, "no page reload expected anywhere in the journey"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Settings persist across header-link navigation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that accessibility settings persist across page navigation within the same browser session")
@allure.label("pbi", PBI)
@allure.label("testcase", "134638")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134638
@pytest.mark.traceability("ADO-134638")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_accessibility_settings_persist_via_header_link_navigation(page):
    # ADO-134638 | PBI 129364 — Page A = homepage, Page B = Contact Us via
    # the header's own "Contact Us" link.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Load Page A"):
        a11y.open_home()
        contrast_default = a11y.is_high_contrast_active()
        scale_default = a11y.zoom_scale()

    with allure.step("Open panel and activate High Contrast"):
        a11y.open_panel()
        a11y.activate_high_contrast()
        contrast_a = a11y.is_high_contrast_active()

    with allure.step("Click Zoom In (+) once"):
        a11y.click_zoom_in()
        font_a = a11y.root_font_size_px()
        a11y.close_panel()

    with allure.step("Navigate to Page B via a header link"):
        a11y.header.open_contact_us_via_nav()
        url_b = a11y.current_url()
        contrast_b = a11y.is_high_contrast_active()
        font_b = a11y.root_font_size_px()
        panel_open_b = a11y.is_panel_open()

    # Assert
    assert not contrast_default and scale_default == DEFAULT_ZOOM_SCALE, "expected Page A at default state"
    assert contrast_a, "expected High Contrast applied on Page A"
    assert font_a > DEFAULT_ROOT_FONT_PX, f"expected an increased font on Page A, got {font_a}px"
    assert "contact-us" in url_b, f"expected Page B (Contact Us), got {url_b}"
    assert contrast_b, "expected Page B to show High Contrast already active"
    assert font_b == font_a, f"expected the same increased font on Page B ({font_a}px), got {font_b}px"
    assert not panel_open_b, "expected no need to reopen the panel (settings applied without it)"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Keyboard-only operation of the panel")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a keyboard-only visitor can operate the entire accessibility panel using only Tab, Enter and Space")
@allure.label("pbi", PBI)
@allure.label("testcase", "134639")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.accessibility
@pytest.mark.uat
@pytest.mark.pbi_129364
@pytest.mark.tc_134639
@pytest.mark.traceability("ADO-134639")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_keyboard_only_visitor_operates_entire_panel(page):
    # ADO-134639 | PBI 129364 — zero mouse interaction after page load. The
    # header Tab path can hit the reCAPTCHA-badge trap documented on
    # ADO-134490; no programmatic-focus fallback is used.
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Press Tab until focus reaches the accessibility icon, then press Enter"):
        icon_reached = a11y.focus_accessibility_button_via_tab()
        panel_opened = a11y.activate_focused_accessibility_button_via_keyboard() if icon_reached else False

    with allure.step("Tab to High Contrast and press Space"):
        hc_focused = a11y.focus_panel_control_via_tab(a11y.HIGH_CONTRAST_SWITCH) if panel_opened else False
        if hc_focused:
            a11y.press_key("Space")
        contrast_on = a11y.is_high_contrast_active()

    with allure.step("Tab to Zoom In (+) and press Enter"):
        zoom_in_focused = a11y.focus_panel_control_via_tab(a11y.ZOOM_IN_BUTTON) if panel_opened else False
        if zoom_in_focused:
            a11y.press_key("Enter")
        scale_zoomed = a11y.zoom_scale()

    with allure.step("Tab to Reset/Normal View and press Enter"):
        reset_focused = a11y.focus_panel_control_via_tab(a11y.RESET_BUTTON) if panel_opened else False
        if reset_focused:
            a11y.press_key("Enter")
        contrast_after_reset = a11y.is_high_contrast_active()
        scale_after_reset = a11y.zoom_scale()

    # Assert
    assert icon_reached, "keyboard Tab never reached the accessibility icon"
    assert panel_opened, "expected Enter on the focused icon to open the panel"
    assert hc_focused, "expected Tab to move focus to the High Contrast toggle"
    assert contrast_on, "expected Space on High Contrast to switch the theme to high-contrast"
    assert zoom_in_focused, "expected Tab to move focus to Zoom In"
    assert scale_zoomed == _step(DEFAULT_ZOOM_SCALE, 1), f"expected one zoom increment, got scale {scale_zoomed}"
    assert reset_focused, "expected Tab to move focus to Reset"
    assert not contrast_after_reset and scale_after_reset == DEFAULT_ZOOM_SCALE, (
        "expected Reset (Enter) to restore font size and contrast to default"
    )


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Closing the panel via the icon")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that clicking the accessibility icon again while the panel is open closes the panel")
@allure.label("pbi", PBI)
@allure.label("testcase", "134653")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134653
@pytest.mark.traceability("ADO-134653")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_clicking_icon_again_closes_panel_with_no_residual_overlay(page):
    # ADO-134653 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Open the accessibility panel by clicking the icon"):
        a11y.open_panel()
        controls = a11y.are_named_controls_visible()

    with allure.step("Click the accessibility icon a second time"):
        a11y.click_accessibility_button()
        panel_open = a11y.is_panel_open()
        open_class_present = a11y.is_panel_open_class_present()
        icon_visible = a11y.is_accessibility_button_visible()

    # Assert
    assert all(controls.values()), f"expected the panel open with all 4 named controls: {controls}"
    assert not panel_open, "expected the panel to close on the second icon click"
    assert not open_class_present, "expected no residual open-panel overlay state on <html>"
    assert icon_visible


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("High Contrast reverse action")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that clicking High Contrast again while active reverts the site to the default theme")
@allure.label("pbi", PBI)
@allure.label("testcase", "134654")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134654
@pytest.mark.traceability("ADO-134654")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_clicking_high_contrast_again_reverts_to_default_theme(page):
    # ADO-134654 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Activate High Contrast"):
        a11y.open_panel()
        a11y.activate_high_contrast()
        contrast_on = a11y.is_high_contrast_active()
        background_on = a11y.page_background_color()
        a11y.mark_document()

    with allure.step("Click the High Contrast toggle again"):
        a11y.activate_high_contrast()
        contrast_off = a11y.is_high_contrast_active()
        background_off = a11y.page_background_color()
        same_document = a11y.is_same_document_since_mark()

    # Assert
    assert contrast_on and background_on == HIGH_CONTRAST_BACKGROUND, "expected the high-contrast theme applied"
    assert not contrast_off, "expected the site to revert to the default theme"
    assert background_off == DEFAULT_BACKGROUND, f"expected the default background, got {background_off}"
    assert same_document, "expected no page reload"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Zoom In accumulates")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that clicking Zoom In (+) three times consecutively increases font size cumulatively by three increments")
@allure.label("pbi", PBI)
@allure.label("testcase", "134655")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134655
@pytest.mark.traceability("ADO-134655")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_zoom_in_three_times_accumulates_three_increments(page):
    # ADO-134655 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Open the panel at default zoom level (Level 0)"):
        a11y.open_panel()
        a11y.mark_document()
        sizes = [a11y.root_font_size_px()]
        scales = [a11y.zoom_scale()]

    with allure.step("Click Zoom In (+) three times"):
        for _ in range(3):
            a11y.click_zoom_in()
            sizes.append(a11y.root_font_size_px())
            scales.append(a11y.zoom_scale())
        same_document = a11y.is_same_document_since_mark()

    # Assert
    assert scales[0] == DEFAULT_ZOOM_SCALE, f"expected Level 0 at start, got scale {scales[0]}"
    assert sizes[1] > sizes[0] and sizes[2] > sizes[1] and sizes[3] > sizes[2], (
        f"expected each click to increase the font size: {sizes}"
    )
    assert scales == [_step(DEFAULT_ZOOM_SCALE, i) for i in range(4)], f"expected Levels 0..3, got {scales}"
    assert same_document, "expected each click to apply without a page reload"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Zoom Out accumulates")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that clicking Zoom Out (−) three times consecutively decreases font size cumulatively by three increments")
@allure.label("pbi", PBI)
@allure.label("testcase", "134656")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134656
@pytest.mark.traceability("ADO-134656")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_zoom_out_three_times_accumulates_three_decrements(page):
    # ADO-134656 | PBI 129364 — live minimum measured at extraction is 80%
    # (reached after 2 clicks); asserted per the case's Level -3.
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Open the panel at default zoom level (Level 0)"):
        a11y.open_panel()
        a11y.mark_document()
        sizes = [a11y.root_font_size_px()]
        scales = [a11y.zoom_scale()]

    with allure.step("Click Zoom Out (−) three times"):
        for _ in range(3):
            a11y.click_zoom_out()
            sizes.append(a11y.root_font_size_px())
            scales.append(a11y.zoom_scale())
        same_document = a11y.is_same_document_since_mark()

    # Assert
    assert scales[0] == DEFAULT_ZOOM_SCALE, f"expected Level 0 at start, got scale {scales[0]}"
    assert same_document, "expected each click to apply without a page reload"
    assert sizes[1] < sizes[0] and sizes[2] < sizes[1] and sizes[3] < sizes[2], (
        f"expected each click to decrease the font size (Levels -1, -2, -3): {sizes}px, scales {scales}"
    )


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Reset reverts a compound state")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Reset/Normal View reverts a combined High Contrast + multi-increment zoom state to default in a single click")
@allure.label("pbi", PBI)
@allure.label("testcase", "134657")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134657
@pytest.mark.traceability("ADO-134657")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_reset_reverts_high_contrast_and_level_2_zoom_in_one_click(page):
    # ADO-134657 | PBI 129364
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()
    font_default = a11y.root_font_size_px()

    # Act
    with allure.step("Activate High Contrast"):
        a11y.open_panel()
        a11y.activate_high_contrast()
        contrast_on = a11y.is_high_contrast_active()

    with allure.step("Click Zoom In (+) twice (reaching Level 2)"):
        a11y.click_zoom_in()
        a11y.click_zoom_in()
        scale_level_2 = a11y.zoom_scale()
        a11y.mark_document()

    with allure.step("Click Reset/Normal View"):
        a11y.click_reset()
        contrast_after = a11y.is_high_contrast_active()
        scale_after = a11y.zoom_scale()
        font_after = a11y.root_font_size_px()
        same_document = a11y.is_same_document_since_mark()

    # Assert
    assert contrast_on, "expected High Contrast applied"
    assert scale_level_2 == _step(DEFAULT_ZOOM_SCALE, 2), f"expected Level 2, got scale {scale_level_2}"
    assert not contrast_after, "expected the default theme after a single Reset"
    assert scale_after == DEFAULT_ZOOM_SCALE and font_after == font_default, (
        f"expected Level 0 after a single Reset (scale {scale_after}, font {font_after}px)"
    )
    assert same_document, "expected no page reload"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Resilience if the panel fails to open")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the accessibility icon remains visible with no broken UI if the panel fails to open")
@allure.label("pbi", PBI)
@allure.label("testcase", "134660")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134660
@pytest.mark.traceability("ADO-134660")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_icon_stays_visible_with_no_broken_ui_when_panel_fails(page):
    # ADO-134660 | PBI 129364 — same real harness as ADO-134484: the two
    # live accessibility bundles are blocked before load, so the panel
    # component genuinely fails to render.
    # Arrange
    a11y = AccessibilityToolsComponent(page)
    a11y.start_open_failure_simulation()

    # Act
    with allure.step("Load a public page with the panel-rendering component forced to fail"):
        a11y.open_home()
        header_visible = a11y.header.is_header_visible()
        icon_visible_before = a11y.is_accessibility_button_visible()
        console_baseline = a11y.console_message_count()

    with allure.step("Click the accessibility icon"):
        a11y.click_accessibility_button()
        panel_open = a11y.is_panel_open()
        panel_nodes = a11y.panel_dom_instance_count()
        open_class_present = a11y.is_panel_open_class_present()
        overflow = a11y.has_page_horizontal_overflow()
        console_errors_from_click = a11y.console_error_count_since(console_baseline)
        icon_visible_after = a11y.is_accessibility_button_visible()

    # Assert
    assert a11y.blocked_request_count() > 0, "the failure harness must genuinely block the panel bundles"
    assert header_visible and icon_visible_before, "expected the page and header to load with the icon visible"
    assert not panel_open and panel_nodes == 0, "expected the panel not to open, with no partial panel markup"
    assert not open_class_present, "expected no blank overlay / open-panel state"
    assert not overflow, "expected no broken layout"
    assert console_errors_from_click == 0, "expected no error surfaced by the click itself"
    assert icon_visible_after, "expected the icon to remain visible and clickable"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("High Contrast does not alter layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that High Contrast changes colour only and does not alter page layout at desktop width")
@allure.label("pbi", PBI)
@allure.label("testcase", "134663")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134663
@pytest.mark.traceability("ADO-134663")
@pytest.mark.parametrize("page", [ANON_DESKTOP_1366], indirect=True)
def test_high_contrast_changes_colour_only_not_layout_at_desktop(page):
    # ADO-134663 | PBI 129364 — content-rich page = EN homepage at 1366x768.
    # Geometry compared within the bug-rules.md layout tolerance (±2 px).
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Note header, main sections and footer positions in the default theme"):
        layout_default = a11y.layout_snapshot()

    with allure.step("Activate High Contrast on the same page"):
        a11y.enable_high_contrast()
        contrast_on = a11y.is_high_contrast_active()

    with allure.step("Re-measure positions, order and spacing, and check horizontal overflow"):
        layout_contrast = a11y.layout_snapshot()
        overflow = a11y.has_page_horizontal_overflow()

    # Assert
    assert contrast_on, "expected High Contrast applied"
    assert layout_default["sections"], "expected the main content to expose measurable sections"
    assert [s["cls"] for s in layout_contrast["sections"]] == [s["cls"] for s in layout_default["sections"]], (
        "expected the same section/column order under High Contrast"
    )
    shifted = _boxes_shifted(layout_default, layout_contrast, LAYOUT_TOLERANCE_PX)
    assert not shifted, f"expected no reflow under High Contrast (±{LAYOUT_TOLERANCE_PX}px): {shifted}"
    assert not overflow, "expected no horizontal scrollbar under High Contrast"


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("High Contrast at mobile width, EN + AR")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that High Contrast renders correctly at mobile viewport width in both languages")
@allure.label("pbi", PBI)
@allure.label("testcase", "134664")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134664
@pytest.mark.traceability("ADO-134664")
@pytest.mark.parametrize("page", [ANON_MOBILE_390], indirect=True)
def test_high_contrast_renders_at_mobile_width_in_both_languages(page):
    # ADO-134664 | PBI 129364 — legibility judged by a real axe-core
    # color-contrast audit of the whole page with the panel open.
    # Arrange
    a11y = AccessibilityToolsComponent(page)

    # Act
    with allure.step("Open the homepage in English at 390x844 and activate High Contrast"):
        a11y.open_home()
        a11y.enable_high_contrast()
        a11y.open_panel()
        en_contrast = a11y.is_high_contrast_active()
        en_violations = a11y.run_color_contrast_audit()
        en_overflow = a11y.has_page_horizontal_overflow()

    with allure.step("Repeat in Arabic"):
        a11y.open_home_arabic()
        a11y.enable_high_contrast()
        a11y.open_panel()
        ar_contrast = a11y.is_high_contrast_active()
        ar_direction = a11y.document_direction()
        ar_panel_direction = a11y.panel_direction()
        ar_violations = a11y.run_color_contrast_audit()
        ar_overflow = a11y.has_page_horizontal_overflow()

    # Assert
    assert en_contrast, "expected High Contrast on the English mobile layout"
    assert en_violations == [], f"EN: illegible content under High Contrast: {_axe_summary(en_violations)}"
    assert ar_contrast, "expected High Contrast on the Arabic mobile layout"
    assert ar_direction == "rtl" and ar_panel_direction == "rtl", "expected the Arabic view to keep RTL"
    assert ar_violations == [], f"AR: illegible content under High Contrast: {_axe_summary(ar_violations)}"
    assert not en_overflow and not ar_overflow, (
        f"expected no horizontal scrollbar (EN={en_overflow}, AR={ar_overflow})"
    )


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("Panel operable in dark mode at mobile width, EN + AR")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the accessibility panel remains operable in dark mode at mobile viewport width")
@allure.label("pbi", PBI)
@allure.label("testcase", "134667")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134667
@pytest.mark.traceability("ADO-134667")
@pytest.mark.parametrize("page", [ANON_MOBILE_390], indirect=True)
def test_panel_operable_in_dark_mode_at_mobile_width_both_languages(page):
    # ADO-134667 | PBI 129364 — Reset also returns dark mode to light (live
    # behaviour), so dark mode is re-enabled for the Arabic pass.
    # Arrange
    a11y = AccessibilityToolsComponent(page)
    results = {}

    # Act
    for locale in ("en", "ar"):
        with allure.step(f"[{locale.upper()}] Open the homepage at 390x844 in dark mode"):
            a11y.open_home() if locale == "en" else a11y.open_home_arabic()
            a11y.enable_dark_mode()
            dark_active = a11y.is_dark_mode_active()
            icon_visible = a11y.is_accessibility_button_visible()

        with allure.step(f"[{locale.upper()}] Open the panel and inspect all four controls"):
            a11y.open_panel()
            controls = a11y.are_named_controls_visible()
            fit = a11y.panel_controls_fit_within_viewport()
            no_overlap = a11y.named_controls_have_no_overlap()
            violations = a11y.run_panel_named_controls_contrast_audit()
            panel_direction = a11y.panel_direction()

        with allure.step(f"[{locale.upper()}] Tap Zoom In and then Reset"):
            font_before = a11y.root_font_size_px()
            a11y.click_zoom_in()
            font_zoomed = a11y.root_font_size_px()
            a11y.click_reset()
            font_reset = a11y.root_font_size_px()

        results[locale] = {
            "dark": dark_active, "icon": icon_visible, "controls": all(controls.values()), "fit": fit,
            "no_overlap": no_overlap, "violations": _axe_summary(violations),
            "direction": panel_direction, "zoomed": font_zoomed > font_before, "reset": font_reset == font_before,
        }

    # Assert
    for locale, r in results.items():
        assert r["dark"] and r["icon"], f"{locale}: expected dark mode with the icon visible: {r}"
        assert r["controls"] and r["fit"] and r["no_overlap"], f"{locale}: expected 4 unclipped, non-overlapping controls: {r}"
        assert r["violations"] == [], f"{locale}: panel controls not legible against the dark background: {r}"
        assert r["zoomed"] and r["reset"], f"{locale}: expected Zoom In then Reset to operate in dark mode: {r}"
    assert results["en"]["direction"] == "ltr" and results["ar"]["direction"] == "rtl", (
        f"expected the Arabic panel mirrored for RTL: {results}"
    )


@allure.epic("GLOBAL")
@allure.feature("Accessibility Tools")
@allure.story("High Contrast requested while dark mode is on")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that requesting High Contrast while dark mode is active produces one deterministic, legible theme")
@allure.label("pbi", PBI)
@allure.label("testcase", "134668")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134668
@pytest.mark.traceability("ADO-134668")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_high_contrast_over_dark_mode_is_deterministic_and_legible(page):
    # ADO-134668 | PBI 129364 — no winner is asserted; coherence, legibility
    # (axe color-contrast, whole page incl. the open panel), determinism
    # across a reload, and a single-click Reset of contrast + zoom. Dark
    # mode's state after Reset is left to the site (case wording).
    # Arrange
    a11y = AccessibilityToolsComponent(page).open_home()

    # Act
    with allure.step("Switch the site to dark mode"):
        a11y.enable_dark_mode()
        dark_on = a11y.is_dark_mode_active()

    with allure.step("Open the panel and activate High Contrast while dark mode is on"):
        a11y.enable_high_contrast()
        a11y.open_panel()
        state_1 = (a11y.is_dark_mode_active(), a11y.is_high_contrast_active(),
                   a11y.page_background_color(), a11y.body_text_color())

    with allure.step("Inspect background, text, links, buttons and the panel for legibility"):
        violations = a11y.run_color_contrast_audit()

    with allure.step("Reload without changing either setting"):
        a11y.reload()
        state_2 = (a11y.is_dark_mode_active(), a11y.is_high_contrast_active(),
                   a11y.page_background_color(), a11y.body_text_color())

    with allure.step("Click Reset / Normal View"):
        a11y.open_panel()
        a11y.click_reset()
        contrast_after_reset = a11y.is_high_contrast_active()
        scale_after_reset = a11y.zoom_scale()

    # Assert
    assert dark_on, "expected dark mode on (<html data-theme='dark'>)"
    assert state_1[1], "expected High Contrast applied on top of dark mode"
    assert state_1[2] != state_1[3], f"expected one coherent theme, background {state_1[2]} vs text {state_1[3]}"
    assert violations == [], f"expected every element legible, axe violations: {_axe_summary(violations)}"
    assert state_2 == state_1, f"expected the combined state to render identically after reload: {state_1} vs {state_2}"
    assert not contrast_after_reset and scale_after_reset == DEFAULT_ZOOM_SCALE, (
        "expected a single Reset to clear High Contrast and any zoom"
    )

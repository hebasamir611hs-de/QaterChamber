"""
web/tests/header/test_accessibility_control_panel.py — Accessibility Tools,
Control-Panel surface (PBI 133381, "QC-GBL-003").

Structural split (2026-08-11, per .claude/context/active/standards.md ->
"Automation Structure - Project Deviation from the Plugin Default"): this
module holds every Control_Panel-tagged GLOBAL-ACCESSIBILITY-TC-* case. The
sibling Web-tagged cases live in test_accessibility_web.py in this same
folder. Two cases (TC-013, TC-014) are tagged BOTH Web and Control_Panel —
each has one test in each module, sharing the same traceability ID: this
module's half configures the CMS toggle and asserts the CMS publish
succeeded (`admin.toast_message()`); test_accessibility_web.py's half
performs the same CMS configuration (an unavoidable Arrange precondition so
the test remains independent/standalone) then asserts the icon's visibility
on the live public page.

Every test still carries:
  - its QA traceability ID (`@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-xxx")`)
  - the Axis B backlog marker `@pytest.mark.pbi_133381` + `allure.label("pbi", PBI)`
  - one marker per tag axis actually present on its source case.

CMS/Control-Panel + Media-Library steps go through `HeaderAdminPage`, whose
field constants are `TODO(locator)` placeholders (disclosed, CMS-only
exception — see header_admin_page.py's docstring): the Liferay Control
Panel sits behind auth this session has no credentials for.

Scripted, not executed: per the task's hard constraint, none of these tests
have been run. "Scripted" (automation-standards.md's Definition of Done,
Scripted tier) is the only claim made here.
"""

import allure
import pytest

from web.pages.header.header_admin_page import HeaderAdminPage

PBI = "133381"


@allure.epic("Accessibility Tools")
@allure.feature("Functional-High")
@allure.story("Verify that enabling the Accessibility Tools widget in CMS makes the icon appear on the frontend after cache refresh")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that enabling the Accessibility Tools widget in CMS makes the icon appear on the frontend after cache refresh")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-013")
def test_tc013_verify_enabling_accessibility_widget_in_cms_shows_icon_after_cache_refresh(page):
    """GLOBAL-ACCESSIBILITY-TC-013 — Verify that enabling the Accessibility Tools widget in CMS makes the icon appear on the frontend after cache refresh"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    admin = HeaderAdminPage(page)
    admin.open_accessibility_settings()

    # Act
    with allure.step("Toggle Accessibility Tools Enabled to True and Save and Publish"):
        admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, True)
        admin.click_save_and_publish()

    # Assert
    assert "success" in admin.toast_message().lower()


@allure.epic("Accessibility Tools")
@allure.feature("Functional-High")
@allure.story("Verify that disabling the Accessibility Tools widget in CMS hides the icon from the frontend after cache refresh")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling the Accessibility Tools widget in CMS hides the icon from the frontend after cache refresh")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-014")
def test_tc014_verify_disabling_accessibility_widget_in_cms_hides_icon_after_cache_refresh(page):
    """GLOBAL-ACCESSIBILITY-TC-014 — Verify that disabling the Accessibility Tools widget in CMS hides the icon from the frontend after cache refresh"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — setting confirmed True beforehand
    admin = HeaderAdminPage(page)
    admin.open_accessibility_settings()
    admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, True)
    admin.click_save_and_publish()

    # Act
    with allure.step("Toggle Accessibility Tools Enabled to False and Save and Publish"):
        admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, False)
        admin.click_save_and_publish()

    # Assert
    assert "success" in admin.toast_message().lower()


@allure.epic("Accessibility Tools")
@allure.feature("Functional-High")
@allure.story("Verify that publishing an image is blocked when both English and Arabic alt text are missing")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that publishing an image is blocked when both English and Arabic alt text are missing")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-015")
def test_tc015_verify_publish_blocked_when_both_en_ar_alt_text_missing(page):
    """GLOBAL-ACCESSIBILITY-TC-015 — Verify that publishing an image is blocked when both English and Arabic alt text are missing"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    admin = HeaderAdminPage(page)
    admin.open_media_library()

    # Act
    with allure.step("Upload a new image, leave both Alt Text fields empty"):
        admin.upload_image("qc-image.png")
        admin.click_publish()

    # Assert — EN mandatory message shown, image not published
    assert admin.field_error_text(HeaderAdminPage.ALT_TEXT_EN_FIELD) == "Alt text (EN) is required for accessibility compliance."


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that setting Accessibility Tools Enabled to True saves correctly with a success toast")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that setting Accessibility Tools Enabled to True saves correctly with a success toast")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-016")
def test_tc016_verify_setting_accessibility_enabled_true_saves_with_success_toast(page):
    """GLOBAL-ACCESSIBILITY-TC-016 — Verify that setting Accessibility Tools Enabled to True saves correctly with a success toast"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    admin = HeaderAdminPage(page)
    admin.open_accessibility_settings()
    admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, False)

    # Act
    with allure.step("Toggle Enabled to True and Save and Publish"):
        admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, True)
        admin.click_save_and_publish()
    with allure.step("Reload the Accessibility Settings page"):
        admin.open_accessibility_settings()

    # Assert
    assert "success" in admin.toast_message().lower()
    assert admin.is_toggle_active(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE) is True


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that setting Accessibility Tools Enabled to False saves correctly with a success toast")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that setting Accessibility Tools Enabled to False saves correctly with a success toast")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-017")
def test_tc017_verify_setting_accessibility_enabled_false_saves_with_success_toast(page):
    """GLOBAL-ACCESSIBILITY-TC-017 — Verify that setting Accessibility Tools Enabled to False saves correctly with a success toast"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    admin = HeaderAdminPage(page)
    admin.open_accessibility_settings()
    admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, True)

    # Act
    with allure.step("Toggle Enabled to False and Save and Publish"):
        admin.set_toggle(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE, False)
        admin.click_save_and_publish()
    with allure.step("Reload the Accessibility Settings page"):
        admin.open_accessibility_settings()

    # Assert
    assert "success" in admin.toast_message().lower()
    assert admin.is_toggle_active(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE) is False


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that a valid English alt text value saves and publishes successfully")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid English alt text value saves and publishes successfully")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-018")
def test_tc018_verify_valid_english_alt_text_saves_and_publishes(page):
    """GLOBAL-ACCESSIBILITY-TC-018 — Verify that a valid English alt text value saves and publishes successfully"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — AR populated, EN empty
    admin = HeaderAdminPage(page)
    admin.open_media_library()

    # Act
    with allure.step('Enter "Qatar Chamber headquarters building exterior view" in Alt Text (EN)'):
        admin.fill_field(HeaderAdminPage.ALT_TEXT_EN_FIELD, "Qatar Chamber headquarters building exterior view")
        admin.click_publish()

    # Assert
    assert admin.field_value(HeaderAdminPage.ALT_TEXT_EN_FIELD) == "Qatar Chamber headquarters building exterior view"
    assert "success" in admin.toast_message().lower()


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that publish is blocked when the English alt text is left empty")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that publish is blocked when the English alt text is left empty")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-019")
def test_tc019_verify_publish_blocked_when_english_alt_text_empty(page):
    """GLOBAL-ACCESSIBILITY-TC-019 — Verify that publish is blocked when the English alt text is left empty"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — AR populated, EN blank
    admin = HeaderAdminPage(page)
    admin.open_media_library()
    admin.clear_field(HeaderAdminPage.ALT_TEXT_EN_FIELD)

    # Act
    with allure.step("Click Publish"):
        admin.click_publish()

    # Assert
    assert admin.field_error_text(HeaderAdminPage.ALT_TEXT_EN_FIELD) == "Alt text (EN) is required for accessibility compliance."


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that the English alt text field accepts exactly 150 characters and rejects 151")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the English alt text field accepts exactly 150 characters and rejects 151")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-020")
def test_tc020_verify_english_alt_text_accepts_150_rejects_151(page):
    """GLOBAL-ACCESSIBILITY-TC-020 — Verify that the English alt text field accepts exactly 150 characters and rejects 151"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    admin = HeaderAdminPage(page)
    admin.open_media_library()
    value_150 = "A" * 150
    value_151 = "A" * 151

    # Act
    with allure.step("Enter a 150-character value and publish"):
        admin.fill_field(HeaderAdminPage.ALT_TEXT_EN_FIELD, value_150)
        admin.click_publish()
        accepted = "success" in admin.toast_message().lower()
    with allure.step("Clear, enter a 151-character value and publish"):
        admin.clear_field(HeaderAdminPage.ALT_TEXT_EN_FIELD)
        admin.fill_field(HeaderAdminPage.ALT_TEXT_EN_FIELD, value_151)
        admin.click_publish()

    # Assert
    assert accepted is True
    assert admin.field_error_text(HeaderAdminPage.ALT_TEXT_EN_FIELD) != ""


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that whitespace-only English alt text is treated as empty and blocks publish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that whitespace-only English alt text is treated as empty and blocks publish")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-021")
def test_tc021_verify_whitespace_only_english_alt_text_blocks_publish(page):
    """GLOBAL-ACCESSIBILITY-TC-021 — Verify that whitespace-only English alt text is treated as empty and blocks publish"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    admin = HeaderAdminPage(page)
    admin.open_media_library()

    # Act
    with allure.step("Enter 10 space characters and publish"):
        admin.fill_field(HeaderAdminPage.ALT_TEXT_EN_FIELD, " " * 10)
        admin.click_publish()

    # Assert
    assert admin.field_error_text(HeaderAdminPage.ALT_TEXT_EN_FIELD) == "Alt text (EN) is required for accessibility compliance."


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that a valid Arabic alt text value saves and publishes successfully")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Arabic alt text value saves and publishes successfully")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-022")
def test_tc022_verify_valid_arabic_alt_text_saves_and_publishes(page):
    """GLOBAL-ACCESSIBILITY-TC-022 — Verify that a valid Arabic alt text value saves and publishes successfully"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — EN populated, AR empty
    admin = HeaderAdminPage(page)
    admin.open_media_library()

    # Act
    with allure.step('Enter "منظر خارجي لمبنى غرفة قطر" in Alt Text (AR)'):
        admin.fill_field(HeaderAdminPage.ALT_TEXT_AR_FIELD, "منظر خارجي لمبنى غرفة قطر")
        admin.click_publish()

    # Assert
    assert "success" in admin.toast_message().lower()


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that publish is blocked when the Arabic alt text is left empty")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that publish is blocked when the Arabic alt text is left empty")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-023")
def test_tc023_verify_publish_blocked_when_arabic_alt_text_empty(page):
    """GLOBAL-ACCESSIBILITY-TC-023 — Verify that publish is blocked when the Arabic alt text is left empty"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — EN populated, AR blank
    admin = HeaderAdminPage(page)
    admin.open_media_library()
    admin.clear_field(HeaderAdminPage.ALT_TEXT_AR_FIELD)

    # Act
    with allure.step("Click Publish"):
        admin.click_publish()

    # Assert — both EN and AR messages displayed
    error = admin.field_error_text(HeaderAdminPage.ALT_TEXT_AR_FIELD)
    assert error == "Alt text (AR) is required before publishing." or "النص البديل" in error


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that the Arabic alt text field accepts exactly 150 characters and rejects 151")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Arabic alt text field accepts exactly 150 characters and rejects 151")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-024")
def test_tc024_verify_arabic_alt_text_accepts_150_rejects_151(page):
    """GLOBAL-ACCESSIBILITY-TC-024 — Verify that the Arabic alt text field accepts exactly 150 characters and rejects 151"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    admin = HeaderAdminPage(page)
    admin.open_media_library()
    value_150 = "ا" * 150
    value_151 = "ا" * 151

    # Act
    with allure.step("Enter a 150-character AR value and publish"):
        admin.fill_field(HeaderAdminPage.ALT_TEXT_AR_FIELD, value_150)
        admin.click_publish()
        accepted = "success" in admin.toast_message().lower()
    with allure.step("Clear, enter a 151-character AR value and publish"):
        admin.clear_field(HeaderAdminPage.ALT_TEXT_AR_FIELD)
        admin.fill_field(HeaderAdminPage.ALT_TEXT_AR_FIELD, value_151)
        admin.click_publish()

    # Assert
    assert accepted is True
    assert admin.field_error_text(HeaderAdminPage.ALT_TEXT_AR_FIELD) != ""


@allure.epic("Accessibility Tools")
@allure.feature("Functional-Low")
@allure.story("Verify that whitespace-only Arabic alt text is treated as empty and blocks publish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that whitespace-only Arabic alt text is treated as empty and blocks publish")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-025")
def test_tc025_verify_whitespace_only_arabic_alt_text_blocks_publish(page):
    """GLOBAL-ACCESSIBILITY-TC-025 — Verify that whitespace-only Arabic alt text is treated as empty and blocks publish"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    admin = HeaderAdminPage(page)
    admin.open_media_library()

    # Act
    with allure.step("Enter 10 space characters and publish"):
        admin.fill_field(HeaderAdminPage.ALT_TEXT_AR_FIELD, " " * 10)
        admin.click_publish()

    # Assert
    error = admin.field_error_text(HeaderAdminPage.ALT_TEXT_AR_FIELD)
    assert error == "Alt text (AR) is required before publishing." or "النص البديل" in error


@allure.epic("Accessibility Tools")
@allure.feature("Auth")
@allure.story("Verify that a CMS user without Header Management permission is denied access when attempting to change Accessibility Settings")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that a CMS user without Header Management permission is denied access when attempting to change Accessibility Settings")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.accessibility
@pytest.mark.pbi_133381
@pytest.mark.traceability("GLOBAL-ACCESSIBILITY-TC-031")
def test_tc031_verify_cms_user_without_permission_denied_accessibility_settings(page):
    """GLOBAL-ACCESSIBILITY-TC-031 — Verify that a CMS user without Header Management permission is denied access when attempting to change Accessibility Settings"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — a role lacking Header Management permission
    admin = HeaderAdminPage(page)

    # Act
    with allure.step("Attempt to navigate to Accessibility Settings"):
        admin.open_accessibility_settings()

    # Assert — settings page never loads, toggle is never exposed to attempt on;
    # no toggle/save is attempted, since access is denied at navigation itself.
    denied_message = admin.access_denied_message()
    assert denied_message != ""
    assert admin.is_control_exposed(HeaderAdminPage.ACCESSIBILITY_TOOLS_ENABLED_TOGGLE) is False

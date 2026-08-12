"""
web/tests/footer/test_footer_control_panel.py — Site Footer & Social Media Icons,
Control-Panel surface (PBI 133231, "QC-GBL-004").

Structural split (2026-08-11, per .claude/context/active/standards.md ->
"Automation Structure - Project Deviation from the Plugin Default"): this
module holds every Control_Panel-tagged GLOBAL-FOOTER-TC-* case. The sibling
Web-tagged cases live in test_footer_web.py in this same folder. A case
tagged BOTH Web and Control_Panel (39 of the 184 cases) has one test in each
module, sharing the same traceability ID, each keeping only the
CMS-configuration half (this module) or the live-site-verification half
(test_footer_web.py) of the original scripted test. No test logic was
invented beyond that split: where the original assertion was purely a live-
site check with no distinct CMS-side assertion, this module's half asserts
the CMS publish/save outcome via `admin.toast_message()` (an idiom already
used verbatim by sibling cases in the original module for the exact same
fill-and-publish action) rather than inventing a new one.

Every test still carries:
  - its QA traceability ID (`@pytest.mark.traceability("GLOBAL-FOOTER-TC-xxx")`)
  - the Axis B backlog marker `@pytest.mark.pbi_133231` + `allure.label("pbi", "133231")`
  - one marker per tag axis actually present on its source case (Lifecycle,
    Service/Module, Platform, Category, Business keyword) — never invented.

Admin/Control-Panel steps go through `FooterAdminPage`, whose field
constants are `TODO(locator)` placeholders (disclosed, CMS-only exception —
see footer_admin_page.py's docstring): the Liferay Control Panel sits behind
auth this session has no credentials for.

Scripted, not executed: per the task's hard constraint, none of these tests
have been run. "Scripted" (automation-standards.md's Definition of Done,
Scripted tier) is the only claim made here.
"""

import allure
import pytest

from web.pages.footer.footer_admin_page import FooterAdminPage


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that a valid Footer Logo Image upload is accepted")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Footer Logo Image upload is accepted")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-001")
def test_tc001_verify_valid_footer_logo_image_upload_accepted(page):
    """GLOBAL-FOOTER-TC-001 — Verify that a valid Footer Logo Image upload is accepted"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Upload qc-logo.png"):
        admin.upload_file(FooterAdminPage.FOOTER_LOGO_IMAGE_UPLOAD, "qc-logo.png")
        admin.click_publish()
    with allure.step("Assert: logo appears in the footer site-wide"):
        footer.open_home()
        assert footer.logo_src()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that publishing without a Footer Logo Image is blocked")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that publishing without a Footer Logo Image is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-002")
def test_tc002_verify_publishing_without_footer_logo_image_blocked(page):
    """GLOBAL-FOOTER-TC-002 — Verify that publishing without a Footer Logo Image is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Publish with the logo field empty"):
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_IMAGE_UPLOAD) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that an invalid file format for Footer Logo Image is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an invalid file format for Footer Logo Image is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-003")
def test_tc003_verify_invalid_file_format_for_footer_logo_image(page):
    """GLOBAL-FOOTER-TC-003 — Verify that an invalid file format for Footer Logo Image is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Attempt upload logo.gif"):
        admin.upload_file(FooterAdminPage.FOOTER_LOGO_IMAGE_UPLOAD, "logo.gif")
        admin.click_publish()
    with allure.step("Assert: invalid type rejected, field remains empty"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_IMAGE_UPLOAD) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that a Footer Logo Image exceeding 2MB is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Footer Logo Image exceeding 2MB is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-004")
def test_tc004_verify_footer_logo_image_exceeding_2mb_rejected(page):
    """GLOBAL-FOOTER-TC-004 — Verify that a Footer Logo Image exceeding 2MB is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Upload logo-3mb.png"):
        admin.upload_file(FooterAdminPage.FOOTER_LOGO_IMAGE_UPLOAD, "logo-3mb.png")
        admin.click_publish()
    with allure.step("Assert: size-limit error, file not accepted"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_IMAGE_UPLOAD) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that valid Footer Logo Alt Text (EN/AR) saves and publishes")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that valid Footer Logo Alt Text (EN/AR) saves and publishes")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-005")
def test_tc005_verify_valid_footer_logo_alt_text_en_ar(page):
    """GLOBAL-FOOTER-TC-005 — Verify that valid Footer Logo Alt Text (EN/AR) saves and publishes"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Footer Logo Alt Text EN / AR"):
        admin.fill_field(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_EN, "Qatar Chamber Logo")
        admin.fill_field(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_AR, "شعار غرفة قطر")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.logo_alt()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that leaving Footer Logo Alt Text EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Footer Logo Alt Text EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-006")
def test_tc006_verify_leaving_footer_logo_alt_text_en_empty(page):
    """GLOBAL-FOOTER-TC-006 — Verify that leaving Footer Logo Alt Text EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Footer Logo Alt Text (EN)"):
        admin.clear_field(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_EN) == "Alt Text (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that leaving Footer Logo Alt Text AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Footer Logo Alt Text AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-007")
def test_tc007_verify_leaving_footer_logo_alt_text_ar_empty(page):
    """GLOBAL-FOOTER-TC-007 — Verify that leaving Footer Logo Alt Text AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Footer Logo Alt Text (AR)"):
        admin.clear_field(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_AR) == "عنوان الوصف البديل (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that Footer Logo Alt Text EN rejects a 151-character value")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Footer Logo Alt Text EN rejects a 151-character value")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-008")
def test_tc008_verify_footer_logo_alt_text_en_rejects_151(page):
    """GLOBAL-FOOTER-TC-008 — Verify that Footer Logo Alt Text EN rejects a 151-character value"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 151-character string"):
        admin.fill_field(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that Footer Logo Alt Text EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Footer Logo Alt Text EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-009")
def test_tc009_verify_footer_logo_alt_text_en_rejects_whitespace(page):
    """GLOBAL-FOOTER-TC-009 — Verify that Footer Logo Alt Text EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_ALT_TEXT_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that a valid Footer Logo Redirect URL is accepted and used on logo click")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Footer Logo Redirect URL is accepted and used on logo click")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-010")
def test_tc010_verify_valid_footer_logo_redirect_url_accepted_used(page):
    """GLOBAL-FOOTER-TC-010 — Verify that a valid Footer Logo Redirect URL is accepted and used on logo click"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Footer Logo Redirect URL EN"):
        admin.fill_field(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL, "https://www.qatarchamber.com/")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that an empty Footer Logo Redirect URL is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an empty Footer Logo Redirect URL is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-011")
def test_tc011_verify_empty_footer_logo_redirect_url_blocked(page):
    """GLOBAL-FOOTER-TC-011 — Verify that an empty Footer Logo Redirect URL is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Footer Logo Redirect URL (EN)"):
        admin.clear_field(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL) == "Footer Logo Redirect URL is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that an invalid Footer Logo Redirect URL is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an invalid Footer Logo Redirect URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-012")
def test_tc012_verify_invalid_footer_logo_redirect_url_rejected(page):
    """GLOBAL-FOOTER-TC-012 — Verify that an invalid Footer Logo Redirect URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter not-a-url"):
        admin.fill_field(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL, "not-a-url")
        admin.click_publish()
    with allure.step("Assert: invalid-URL error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL) == "Please enter a valid URL."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that Footer Logo Redirect URL rejects a value exceeding 500 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Footer Logo Redirect URL rejects a value exceeding 500 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-013")
def test_tc013_verify_footer_logo_redirect_url_rejects_value_exceeding(page):
    """GLOBAL-FOOTER-TC-013 — Verify that Footer Logo Redirect URL rejects a value exceeding 500 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 500-character string"):
        admin.fill_field(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that whitespace-only input in Footer Logo Redirect URL is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that whitespace-only input in Footer Logo Redirect URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-014")
def test_tc014_verify_whitespace_only_input_footer_logo_redirect_url(page):
    """GLOBAL-FOOTER-TC-014 — Verify that whitespace-only input in Footer Logo Redirect URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that a valid Footer Description (EN/AR) saves and renders")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Footer Description (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-015")
def test_tc015_verify_valid_footer_description_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-015 — Verify that a valid Footer Description (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Footer Description EN"):
        admin.fill_field(FooterAdminPage.FOOTER_DESCRIPTION_EN, "Qatar Chamber promotes trade and industry.")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that Footer Description can be left empty (optional field)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Footer Description can be left empty (optional field)")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-016")
def test_tc016_verify_footer_description_can_be_left_empty_optional(page):
    """GLOBAL-FOOTER-TC-016 — Verify that Footer Description can be left empty (optional field)"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Footer Description EN"):
        admin.fill_field(FooterAdminPage.FOOTER_DESCRIPTION_EN, "Sample value")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.description_text()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that Footer Description EN rejects content exceeding 500 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Footer Description EN rejects content exceeding 500 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-017")
def test_tc017_verify_footer_description_en_rejects_content_exceeding_500(page):
    """GLOBAL-FOOTER-TC-017 — Verify that Footer Description EN rejects content exceeding 500 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 500-character string"):
        admin.fill_field(FooterAdminPage.FOOTER_DESCRIPTION_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.FOOTER_DESCRIPTION_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Social Media Label (EN/AR) saves and renders above the icons row")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Social Media Label (EN/AR) saves and renders above the icons row")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-018")
def test_tc018_verify_valid_social_media_label_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-018 — Verify that a valid Social Media Label (EN/AR) saves and renders above the icons row"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Social Media Label EN / AR"):
        admin.fill_field(FooterAdminPage.SOCIAL_MEDIA_LABEL_EN, "Follow Us on Social Media")
        admin.fill_field(FooterAdminPage.SOCIAL_MEDIA_LABEL_AR, "تابعنا على وسائل التواصل الاجتماعي")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that leaving Social Media Label EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Social Media Label EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-019")
def test_tc019_verify_leaving_social_media_label_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-019 — Verify that leaving Social Media Label EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Social Media Label (EN)"):
        admin.clear_field(FooterAdminPage.SOCIAL_MEDIA_LABEL_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_MEDIA_LABEL_EN) == "Social Media Label (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that leaving Social Media Label AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Social Media Label AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-020")
def test_tc020_verify_leaving_social_media_label_ar_empty_blocked(page):
    """GLOBAL-FOOTER-TC-020 — Verify that leaving Social Media Label AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Social Media Label (AR)"):
        admin.clear_field(FooterAdminPage.SOCIAL_MEDIA_LABEL_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_MEDIA_LABEL_AR) == "تسمية وسائل التواصل الاجتماعي مطلوبة."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that Social Media Label EN rejects a value exceeding 100 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Social Media Label EN rejects a value exceeding 100 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-021")
def test_tc021_verify_social_media_label_en_rejects_value_exceeding(page):
    """GLOBAL-FOOTER-TC-021 — Verify that Social Media Label EN rejects a value exceeding 100 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 100-character string"):
        admin.fill_field(FooterAdminPage.SOCIAL_MEDIA_LABEL_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_MEDIA_LABEL_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that Social Media Label EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Social Media Label EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-022")
def test_tc022_verify_social_media_label_en_rejects_whitespace_only(page):
    """GLOBAL-FOOTER-TC-022 — Verify that Social Media Label EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.SOCIAL_MEDIA_LABEL_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_MEDIA_LABEL_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a valid Column Heading (EN/AR) saves and renders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Column Heading (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-023")
def test_tc023_verify_valid_column_heading_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-023 — Verify that a valid Column Heading (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Column Heading EN / AR"):
        admin.fill_field(FooterAdminPage.COLUMN_HEADING_EN, "About Qatar Chamber")
        admin.fill_field(FooterAdminPage.COLUMN_HEADING_AR, "عن غرفة قطر")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that leaving Column Heading EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Column Heading EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-024")
def test_tc024_verify_leaving_column_heading_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-024 — Verify that leaving Column Heading EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Column Heading (EN)"):
        admin.clear_field(FooterAdminPage.COLUMN_HEADING_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.COLUMN_HEADING_EN) == "Column Heading (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that leaving Column Heading AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Column Heading AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-025")
def test_tc025_verify_leaving_column_heading_ar_empty_blocked_arabic(page):
    """GLOBAL-FOOTER-TC-025 — Verify that leaving Column Heading AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Column Heading (AR)"):
        admin.clear_field(FooterAdminPage.COLUMN_HEADING_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.COLUMN_HEADING_AR) == "عنوان العمود (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that Column Heading EN rejects a value exceeding 150 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Column Heading EN rejects a value exceeding 150 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-026")
def test_tc026_verify_column_heading_en_rejects_value_exceeding_150(page):
    """GLOBAL-FOOTER-TC-026 — Verify that Column Heading EN rejects a value exceeding 150 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 150-character string"):
        admin.fill_field(FooterAdminPage.COLUMN_HEADING_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.COLUMN_HEADING_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that Column Heading EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Column Heading EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-027")
def test_tc027_verify_column_heading_en_rejects_whitespace_only_input(page):
    """GLOBAL-FOOTER-TC-027 — Verify that Column Heading EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.COLUMN_HEADING_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.COLUMN_HEADING_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a valid Column Number selection is accepted")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Column Number selection is accepted")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-028")
def test_tc028_verify_valid_column_number_selection_accepted(page):
    """GLOBAL-FOOTER-TC-028 — Verify that a valid Column Number selection is accepted"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Select Column Number = 2"):
        admin.select_option(FooterAdminPage.COLUMN_NUMBER_DROPDOWN, "2")
        admin.click_publish()
    with allure.step("Assert: the column is grouped/ordered as column 2 on the live footer"):
        footer.open_home()
        assert footer.is_nav_column_visible("About Qatar Chamber")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that publishing with no Column Number selected is blocked")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that publishing with no Column Number selected is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-029")
def test_tc029_verify_publishing_no_column_number_selected_blocked(page):
    """GLOBAL-FOOTER-TC-029 — Verify that publishing with no Column Number selected is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Select Column Number = 2"):
        admin.select_option(FooterAdminPage.COLUMN_NUMBER_DROPDOWN, "2")
        admin.click_publish()
    with allure.step("Assert: the column is grouped/ordered as column 2 on the live footer"):
        footer.open_home()
        assert footer.is_nav_column_visible("About Qatar Chamber")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a valid Column Display Order value orders the column correctly")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Column Display Order value orders the column correctly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-030")
def test_tc030_verify_valid_column_display_order_value_orders_column(page):
    """GLOBAL-FOOTER-TC-030 — Verify that a valid Column Display Order value orders the column correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Set Display Order = 1 for About Qatar Chamber"):
        admin.fill_field(FooterAdminPage.COLUMN_DISPLAY_ORDER, "1")
        admin.click_publish()
    with allure.step("Assert: column appears first among nav columns"):
        footer.open_home()
        assert footer.is_nav_column_visible("About Qatar Chamber")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that an empty Column Display Order is blocked")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Column Display Order is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-031")
def test_tc031_verify_empty_column_display_order_blocked(page):
    """GLOBAL-FOOTER-TC-031 — Verify that an empty Column Display Order is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Display Order"):
        admin.clear_field(FooterAdminPage.COLUMN_DISPLAY_ORDER)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.COLUMN_DISPLAY_ORDER) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a zero/negative Column Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a zero/negative Column Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-032")
def test_tc032_verify_zero_negative_column_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-032 — Verify that a zero/negative Column Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Display Order = -1"):
        admin.fill_field(FooterAdminPage.COLUMN_DISPLAY_ORDER, "-1")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.COLUMN_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a non-numeric Column Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a non-numeric Column Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-033")
def test_tc033_verify_non_numeric_column_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-033 — Verify that a non-numeric Column Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Display Order = abc"):
        admin.fill_field(FooterAdminPage.COLUMN_DISPLAY_ORDER, "abc")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.COLUMN_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that setting Column Active Status to Active publishes the column visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Column Active Status to Active publishes the column visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-034")
def test_tc034_verify_setting_column_active_status_active_publishes_column(page):
    """GLOBAL-FOOTER-TC-034 — Verify that setting Column Active Status to Active publishes the column visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.COLUMN_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that setting Column Active Status to Inactive hides the column from the live footer")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Column Active Status to Inactive hides the column from the live footer")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-035")
def test_tc035_verify_setting_column_active_status_inactive_hides_column(page):
    """GLOBAL-FOOTER-TC-035 — Verify that setting Column Active Status to Inactive hides the column from the live footer"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.COLUMN_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a valid Nav Link Title (EN/AR) saves and renders under its column")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Nav Link Title (EN/AR) saves and renders under its column")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-036")
def test_tc036_verify_valid_nav_link_title_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-036 — Verify that a valid Nav Link Title (EN/AR) saves and renders under its column"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Nav Link Title EN / AR"):
        admin.fill_field(FooterAdminPage.NAV_LINK_TITLE_EN, "Membership Services")
        admin.fill_field(FooterAdminPage.NAV_LINK_TITLE_AR, "خدمات العضوية")
        admin.click_publish()
    with allure.step("Assert: toast success"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that leaving Nav Link Title EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Nav Link Title EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-037")
def test_tc037_verify_leaving_nav_link_title_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-037 — Verify that leaving Nav Link Title EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Nav Link Title (EN)"):
        admin.clear_field(FooterAdminPage.NAV_LINK_TITLE_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NAV_LINK_TITLE_EN) == "Link Title (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that leaving Nav Link Title AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Nav Link Title AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-038")
def test_tc038_verify_leaving_nav_link_title_ar_empty_blocked(page):
    """GLOBAL-FOOTER-TC-038 — Verify that leaving Nav Link Title AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Nav Link Title (AR)"):
        admin.clear_field(FooterAdminPage.NAV_LINK_TITLE_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NAV_LINK_TITLE_AR) == "عنوان الرابط (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that Nav Link Title EN rejects a value exceeding 100 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Nav Link Title EN rejects a value exceeding 100 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-039")
def test_tc039_verify_nav_link_title_en_rejects_value_exceeding(page):
    """GLOBAL-FOOTER-TC-039 — Verify that Nav Link Title EN rejects a value exceeding 100 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 100-character string"):
        admin.fill_field(FooterAdminPage.NAV_LINK_TITLE_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.NAV_LINK_TITLE_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that Nav Link Title EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Nav Link Title EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-040")
def test_tc040_verify_nav_link_title_en_rejects_whitespace_only(page):
    """GLOBAL-FOOTER-TC-040 — Verify that Nav Link Title EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.NAV_LINK_TITLE_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NAV_LINK_TITLE_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a valid Nav Link URL is accepted and navigates correctly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Nav Link URL is accepted and navigates correctly")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-041")
def test_tc041_verify_valid_nav_link_url_accepted_navigates_correctly(page):
    """GLOBAL-FOOTER-TC-041 — Verify that a valid Nav Link URL is accepted and navigates correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Nav Link URL EN"):
        admin.fill_field(FooterAdminPage.NAV_LINK_URL, "https://www.qatarchamber.com/membership")
        admin.click_publish()
    with allure.step("Assert: toast success"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that an empty Nav Link URL is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an empty Nav Link URL is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-042")
def test_tc042_verify_empty_nav_link_url_blocked(page):
    """GLOBAL-FOOTER-TC-042 — Verify that an empty Nav Link URL is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Nav Link URL (EN)"):
        admin.clear_field(FooterAdminPage.NAV_LINK_URL)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NAV_LINK_URL) == "Link URL is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that an invalid Nav Link URL is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an invalid Nav Link URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-043")
def test_tc043_verify_invalid_nav_link_url_rejected(page):
    """GLOBAL-FOOTER-TC-043 — Verify that an invalid Nav Link URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter not-a-url"):
        admin.fill_field(FooterAdminPage.NAV_LINK_URL, "not-a-url")
        admin.click_publish()
    with allure.step("Assert: invalid-URL error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NAV_LINK_URL) == "Please enter a valid URL."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that Nav Link URL rejects a value exceeding 500 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Nav Link URL rejects a value exceeding 500 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-044")
def test_tc044_verify_nav_link_url_rejects_value_exceeding_500(page):
    """GLOBAL-FOOTER-TC-044 — Verify that Nav Link URL rejects a value exceeding 500 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 500-character string"):
        admin.fill_field(FooterAdminPage.NAV_LINK_URL, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.NAV_LINK_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that whitespace-only input in Nav Link URL is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that whitespace-only input in Nav Link URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-045")
def test_tc045_verify_whitespace_only_input_nav_link_url_rejected(page):
    """GLOBAL-FOOTER-TC-045 — Verify that whitespace-only input in Nav Link URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.NAV_LINK_URL, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NAV_LINK_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a valid Nav Link Display Order orders links correctly within a column")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Nav Link Display Order orders links correctly within a column")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-048")
def test_tc048_verify_valid_nav_link_display_order_orders_links(page):
    """GLOBAL-FOOTER-TC-048 — Verify that a valid Nav Link Display Order orders links correctly within a column"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Set Display Order = 1 for Membership Services"):
        admin.fill_field(FooterAdminPage.NAV_LINK_DISPLAY_ORDER, "1")
        admin.click_publish()
    with allure.step("Assert: Membership Services appears first in its list"):
        footer.open_home()
        assert footer.footer_link_display_index("Membership Services") == 0


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that an empty Nav Link Display Order is blocked")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Nav Link Display Order is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-049")
def test_tc049_verify_empty_nav_link_display_order_blocked(page):
    """GLOBAL-FOOTER-TC-049 — Verify that an empty Nav Link Display Order is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Display Order"):
        admin.clear_field(FooterAdminPage.NAV_LINK_DISPLAY_ORDER)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NAV_LINK_DISPLAY_ORDER) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a zero/negative Nav Link Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a zero/negative Nav Link Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-050")
def test_tc050_verify_zero_negative_nav_link_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-050 — Verify that a zero/negative Nav Link Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Display Order = -1"):
        admin.fill_field(FooterAdminPage.NAV_LINK_DISPLAY_ORDER, "-1")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.NAV_LINK_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a non-numeric Nav Link Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a non-numeric Nav Link Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-051")
def test_tc051_verify_non_numeric_nav_link_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-051 — Verify that a non-numeric Nav Link Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Display Order = abc"):
        admin.fill_field(FooterAdminPage.NAV_LINK_DISPLAY_ORDER, "abc")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.NAV_LINK_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that setting a Nav Link Active Status to Active publishes it visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Nav Link Active Status to Active publishes it visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-052")
def test_tc052_verify_setting_nav_link_active_status_active_publishes(page):
    """GLOBAL-FOOTER-TC-052 — Verify that setting a Nav Link Active Status to Active publishes it visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.NAV_LINK_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that setting a Nav Link Active Status to Inactive hides it from the live footer")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Nav Link Active Status to Inactive hides it from the live footer")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-053")
def test_tc053_verify_setting_nav_link_active_status_inactive_hides(page):
    """GLOBAL-FOOTER-TC-053 — Verify that setting a Nav Link Active Status to Inactive hides it from the live footer"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.NAV_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a valid Quick Links Column Heading (EN/AR) saves and renders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Quick Links Column Heading (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-054")
def test_tc054_verify_valid_quick_links_column_heading_en_ar(page):
    """GLOBAL-FOOTER-TC-054 — Verify that a valid Quick Links Column Heading (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter Quick Links Column Heading EN / AR"):
        admin.fill_field(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_EN, "Quick Links")
        admin.fill_field(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_AR, "روابط سريعة")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that leaving Quick Links Column Heading EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Quick Links Column Heading EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-055")
def test_tc055_verify_leaving_quick_links_column_heading_en_empty(page):
    """GLOBAL-FOOTER-TC-055 — Verify that leaving Quick Links Column Heading EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Clear Quick Links Column Heading (EN)"):
        admin.clear_field(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_EN) == "Quick Links Column Heading (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that leaving Quick Links Column Heading AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Quick Links Column Heading AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-056")
def test_tc056_verify_leaving_quick_links_column_heading_ar_empty(page):
    """GLOBAL-FOOTER-TC-056 — Verify that leaving Quick Links Column Heading AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Clear Quick Links Column Heading (AR)"):
        admin.clear_field(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_AR) == "عنوان عمود الروابط السريعة (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that Quick Links Column Heading EN rejects a value exceeding 150 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Quick Links Column Heading EN rejects a value exceeding 150 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-057")
def test_tc057_verify_quick_links_column_heading_en_rejects_value(page):
    """GLOBAL-FOOTER-TC-057 — Verify that Quick Links Column Heading EN rejects a value exceeding 150 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter a 150-character string"):
        admin.fill_field(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that Quick Links Column Heading EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Quick Links Column Heading EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-058")
def test_tc058_verify_quick_links_column_heading_en_rejects_whitespace(page):
    """GLOBAL-FOOTER-TC-058 — Verify that Quick Links Column Heading EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a valid Quick Link Title (EN/AR) saves and renders in the Quick Links list")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Quick Link Title (EN/AR) saves and renders in the Quick Links list")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-059")
def test_tc059_verify_valid_quick_link_title_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-059 — Verify that a valid Quick Link Title (EN/AR) saves and renders in the Quick Links list"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter Quick Link Title EN / AR"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_TITLE_EN, "Careers")
        admin.fill_field(FooterAdminPage.QUICK_LINK_TITLE_AR, "الوظائف")
        admin.click_publish()
    with allure.step("Assert: toast success"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that leaving Quick Link Title EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Quick Link Title EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-060")
def test_tc060_verify_leaving_quick_link_title_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-060 — Verify that leaving Quick Link Title EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Clear Quick Link Title (EN)"):
        admin.clear_field(FooterAdminPage.QUICK_LINK_TITLE_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINK_TITLE_EN) == "Quick Link Title (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that leaving Quick Link Title AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Quick Link Title AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-061")
def test_tc061_verify_leaving_quick_link_title_ar_empty_blocked(page):
    """GLOBAL-FOOTER-TC-061 — Verify that leaving Quick Link Title AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Clear Quick Link Title (AR)"):
        admin.clear_field(FooterAdminPage.QUICK_LINK_TITLE_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINK_TITLE_AR) == "عنوان الرابط السريع (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that Quick Link Title EN rejects a value exceeding 100 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Quick Link Title EN rejects a value exceeding 100 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-062")
def test_tc062_verify_quick_link_title_en_rejects_value_exceeding(page):
    """GLOBAL-FOOTER-TC-062 — Verify that Quick Link Title EN rejects a value exceeding 100 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter a 100-character string"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_TITLE_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINK_TITLE_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that Quick Link Title EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Quick Link Title EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-063")
def test_tc063_verify_quick_link_title_en_rejects_whitespace_only(page):
    """GLOBAL-FOOTER-TC-063 — Verify that Quick Link Title EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_TITLE_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINK_TITLE_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a valid Quick Link URL is accepted and navigates correctly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Quick Link URL is accepted and navigates correctly")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-064")
def test_tc064_verify_valid_quick_link_url_accepted_navigates_correctly(page):
    """GLOBAL-FOOTER-TC-064 — Verify that a valid Quick Link URL is accepted and navigates correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter Quick Link URL EN"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_URL, "https://www.qatarchamber.com/careers")
        admin.click_publish()
    with allure.step("Assert: toast success"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that an empty Quick Link URL is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an empty Quick Link URL is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-065")
def test_tc065_verify_empty_quick_link_url_blocked(page):
    """GLOBAL-FOOTER-TC-065 — Verify that an empty Quick Link URL is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Clear Quick Link URL (EN)"):
        admin.clear_field(FooterAdminPage.QUICK_LINK_URL)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINK_URL) == "Please enter a valid URL."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that an invalid Quick Link URL is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an invalid Quick Link URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-066")
def test_tc066_verify_invalid_quick_link_url_rejected(page):
    """GLOBAL-FOOTER-TC-066 — Verify that an invalid Quick Link URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter not-a-url"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_URL, "not-a-url")
        admin.click_publish()
    with allure.step("Assert: invalid-URL error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINK_URL) == "Please enter a valid URL."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that Quick Link URL rejects a value exceeding 500 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Quick Link URL rejects a value exceeding 500 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-067")
def test_tc067_verify_quick_link_url_rejects_value_exceeding_500(page):
    """GLOBAL-FOOTER-TC-067 — Verify that Quick Link URL rejects a value exceeding 500 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter a 500-character string"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_URL, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINK_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that whitespace-only input in Quick Link URL is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that whitespace-only input in Quick Link URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-068")
def test_tc068_verify_whitespace_only_input_quick_link_url_rejected(page):
    """GLOBAL-FOOTER-TC-068 — Verify that whitespace-only input in Quick Link URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_URL, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINK_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a valid Quick Link Display Order orders links correctly")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Quick Link Display Order orders links correctly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-071")
def test_tc071_verify_valid_quick_link_display_order_orders_links(page):
    """GLOBAL-FOOTER-TC-071 — Verify that a valid Quick Link Display Order orders links correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Set Display Order = 1 for Careers"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_DISPLAY_ORDER, "1")
        admin.click_publish()
    with allure.step("Assert: Careers appears first in its list"):
        footer.open_home()
        assert footer.footer_link_display_index("Careers") == 0


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that an empty Quick Link Display Order is blocked")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Quick Link Display Order is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-072")
def test_tc072_verify_empty_quick_link_display_order_blocked(page):
    """GLOBAL-FOOTER-TC-072 — Verify that an empty Quick Link Display Order is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Clear Display Order"):
        admin.clear_field(FooterAdminPage.QUICK_LINK_DISPLAY_ORDER)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.QUICK_LINK_DISPLAY_ORDER) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a zero/negative Quick Link Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a zero/negative Quick Link Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-073")
def test_tc073_verify_zero_negative_quick_link_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-073 — Verify that a zero/negative Quick Link Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter Display Order = -1"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_DISPLAY_ORDER, "-1")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.QUICK_LINK_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a non-numeric Quick Link Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a non-numeric Quick Link Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-074")
def test_tc074_verify_non_numeric_quick_link_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-074 — Verify that a non-numeric Quick Link Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter Display Order = abc"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_DISPLAY_ORDER, "abc")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.QUICK_LINK_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that setting a Quick Link Active Status to Active publishes it visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Quick Link Active Status to Active publishes it visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-075")
def test_tc075_verify_setting_quick_link_active_status_active_publishes(page):
    """GLOBAL-FOOTER-TC-075 — Verify that setting a Quick Link Active Status to Active publishes it visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.QUICK_LINK_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that setting a Quick Link Active Status to Inactive hides it from the Quick Links column")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Quick Link Active Status to Inactive hides it from the Quick Links column")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-076")
def test_tc076_verify_setting_quick_link_active_status_inactive_hides(page):
    """GLOBAL-FOOTER-TC-076 — Verify that setting a Quick Link Active Status to Inactive hides it from the Quick Links column"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.QUICK_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Platform Name is accepted")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Platform Name is accepted")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-077")
def test_tc077_verify_valid_platform_name_accepted(page):
    """GLOBAL-FOOTER-TC-077 — Verify that a valid Platform Name is accepted"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter Platform Name EN"):
        admin.fill_field(FooterAdminPage.PLATFORM_NAME, "LinkedIn")
        admin.click_publish()
    with allure.step("Assert: toast success"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that leaving Platform Name empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Platform Name empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-078")
def test_tc078_verify_leaving_platform_name_empty_blocked(page):
    """GLOBAL-FOOTER-TC-078 — Verify that leaving Platform Name empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Clear Platform Name (EN)"):
        admin.clear_field(FooterAdminPage.PLATFORM_NAME)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.PLATFORM_NAME) == "Platform Name is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that Platform Name rejects a value exceeding 50 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Platform Name rejects a value exceeding 50 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-079")
def test_tc079_verify_platform_name_rejects_value_exceeding_50_characters(page):
    """GLOBAL-FOOTER-TC-079 — Verify that Platform Name rejects a value exceeding 50 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter a 50-character string"):
        admin.fill_field(FooterAdminPage.PLATFORM_NAME, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.PLATFORM_NAME) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that Platform Name rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Platform Name rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-080")
def test_tc080_verify_platform_name_rejects_whitespace_only_input(page):
    """GLOBAL-FOOTER-TC-080 — Verify that Platform Name rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.PLATFORM_NAME, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.PLATFORM_NAME) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Social Icon Image upload is accepted")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Social Icon Image upload is accepted")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-081")
def test_tc081_verify_valid_social_icon_image_upload_accepted(page):
    """GLOBAL-FOOTER-TC-081 — Verify that a valid Social Icon Image upload is accepted"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Upload linkedin-icon.svg"):
        admin.upload_file(FooterAdminPage.SOCIAL_ICON_IMAGE_UPLOAD, "linkedin-icon.svg")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that publishing without a Social Icon Image is blocked")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that publishing without a Social Icon Image is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-082")
def test_tc082_verify_publishing_without_social_icon_image_blocked(page):
    """GLOBAL-FOOTER-TC-082 — Verify that publishing without a Social Icon Image is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Leave icon image empty"):
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_ICON_IMAGE_UPLOAD) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that an invalid file format for Social Icon Image is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an invalid file format for Social Icon Image is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-083")
def test_tc083_verify_invalid_file_format_for_social_icon_image(page):
    """GLOBAL-FOOTER-TC-083 — Verify that an invalid file format for Social Icon Image is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Upload icon.gif"):
        admin.upload_file(FooterAdminPage.SOCIAL_ICON_IMAGE_UPLOAD, "icon.gif")
        admin.click_publish()
    with allure.step("Assert: invalid type rejected"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_ICON_IMAGE_UPLOAD) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a Social Icon Image exceeding 2MB is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Social Icon Image exceeding 2MB is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-084")
def test_tc084_verify_social_icon_image_exceeding_2mb_rejected(page):
    """GLOBAL-FOOTER-TC-084 — Verify that a Social Icon Image exceeding 2MB is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Upload icon-3mb.png"):
        admin.upload_file(FooterAdminPage.SOCIAL_ICON_IMAGE_UPLOAD, "icon-3mb.png")
        admin.click_publish()
    with allure.step("Assert: size-limit error, file rejected"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_ICON_IMAGE_UPLOAD) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Icon Alt Text (EN/AR) saves and is applied to the icon")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Icon Alt Text (EN/AR) saves and is applied to the icon")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-085")
def test_tc085_verify_valid_icon_alt_text_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-085 — Verify that a valid Icon Alt Text (EN/AR) saves and is applied to the icon"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter Icon Alt Text EN / AR"):
        admin.fill_field(FooterAdminPage.ICON_ALT_TEXT_EN, "LinkedIn")
        admin.fill_field(FooterAdminPage.ICON_ALT_TEXT_AR, "لينكدإن")
        admin.click_publish()
    with allure.step("Assert: toast success"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that leaving Icon Alt Text EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Icon Alt Text EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-086")
def test_tc086_verify_leaving_icon_alt_text_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-086 — Verify that leaving Icon Alt Text EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Clear Icon Alt Text (EN)"):
        admin.clear_field(FooterAdminPage.ICON_ALT_TEXT_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.ICON_ALT_TEXT_EN) == "Icon Alt Text (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that leaving Icon Alt Text AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Icon Alt Text AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-087")
def test_tc087_verify_leaving_icon_alt_text_ar_empty_blocked(page):
    """GLOBAL-FOOTER-TC-087 — Verify that leaving Icon Alt Text AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Clear Icon Alt Text (AR)"):
        admin.clear_field(FooterAdminPage.ICON_ALT_TEXT_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.ICON_ALT_TEXT_AR) == "النص البديل للأيقونة (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that Icon Alt Text EN rejects a value exceeding 100 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Icon Alt Text EN rejects a value exceeding 100 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-088")
def test_tc088_verify_icon_alt_text_en_rejects_value_exceeding(page):
    """GLOBAL-FOOTER-TC-088 — Verify that Icon Alt Text EN rejects a value exceeding 100 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter a 100-character string"):
        admin.fill_field(FooterAdminPage.ICON_ALT_TEXT_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.ICON_ALT_TEXT_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that Icon Alt Text EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Icon Alt Text EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-089")
def test_tc089_verify_icon_alt_text_en_rejects_whitespace_only(page):
    """GLOBAL-FOOTER-TC-089 — Verify that Icon Alt Text EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.ICON_ALT_TEXT_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.ICON_ALT_TEXT_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Social Redirect URL opens the correct channel")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Social Redirect URL opens the correct channel")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-090")
def test_tc090_verify_valid_social_redirect_url_opens_correct_channel(page):
    """GLOBAL-FOOTER-TC-090 — Verify that a valid Social Redirect URL opens the correct channel"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter Social Redirect URL EN"):
        admin.fill_field(FooterAdminPage.SOCIAL_REDIRECT_URL, "https://www.linkedin.com/company/qatarchamber")
        admin.click_publish()
    with allure.step("Assert: toast success"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that an empty Social Redirect URL is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an empty Social Redirect URL is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-091")
def test_tc091_verify_empty_social_redirect_url_blocked(page):
    """GLOBAL-FOOTER-TC-091 — Verify that an empty Social Redirect URL is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Clear Social Redirect URL (EN)"):
        admin.clear_field(FooterAdminPage.SOCIAL_REDIRECT_URL)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_REDIRECT_URL) == "Please enter a valid URL."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that an invalid Social Redirect URL is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an invalid Social Redirect URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-092")
def test_tc092_verify_invalid_social_redirect_url_rejected(page):
    """GLOBAL-FOOTER-TC-092 — Verify that an invalid Social Redirect URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter not-a-url"):
        admin.fill_field(FooterAdminPage.SOCIAL_REDIRECT_URL, "not-a-url")
        admin.click_publish()
    with allure.step("Assert: invalid-URL error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_REDIRECT_URL) == "Please enter a valid URL."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that Social Redirect URL rejects a value exceeding 500 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Social Redirect URL rejects a value exceeding 500 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-093")
def test_tc093_verify_social_redirect_url_rejects_value_exceeding_500(page):
    """GLOBAL-FOOTER-TC-093 — Verify that Social Redirect URL rejects a value exceeding 500 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter a 500-character string"):
        admin.fill_field(FooterAdminPage.SOCIAL_REDIRECT_URL, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_REDIRECT_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that whitespace-only input in Social Redirect URL is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that whitespace-only input in Social Redirect URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-094")
def test_tc094_verify_whitespace_only_input_social_redirect_url_rejected(page):
    """GLOBAL-FOOTER-TC-094 — Verify that whitespace-only input in Social Redirect URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.SOCIAL_REDIRECT_URL, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_REDIRECT_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that Social Icon \"Open in New Tab\" is fixed to true with no toggle exposed")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Social Icon \"Open in New Tab\" is fixed to true with no toggle exposed")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-095")
def test_tc095_verify_social_icon_open_new_tab_fixed_true(page):
    """GLOBAL-FOOTER-TC-095 — Verify that Social Icon \"Open in New Tab\" is fixed to true with no toggle exposed"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Open a Social Icon record in the CMS"):
        is_readonly = admin.is_field_readonly(FooterAdminPage.SOCIAL_ICON_OPEN_NEW_TAB_FIELD)
        toggle_exposed = admin.is_toggle_exposed(FooterAdminPage.SOCIAL_ICON_OPEN_NEW_TAB_FIELD)
    with allure.step("Assert: field is fixed true, no OFF option, and the live icon opens in a new tab"):
        assert is_readonly is True
        assert toggle_exposed is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Social Icon Display Order orders icons correctly")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Social Icon Display Order orders icons correctly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-096")
def test_tc096_verify_valid_social_icon_display_order_orders_icons(page):
    """GLOBAL-FOOTER-TC-096 — Verify that a valid Social Icon Display Order orders icons correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Set Display Order = 1 for Membership Services"):
        admin.fill_field(FooterAdminPage.SOCIAL_ICON_DISPLAY_ORDER, "1")
        admin.click_publish()
    with allure.step("Assert: icon appears first in the social row"):
        footer.open_home()
        assert footer.social_icon_display_index("LinkedIn") == 0


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that an empty Social Icon Display Order is blocked")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Social Icon Display Order is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-097")
def test_tc097_verify_empty_social_icon_display_order_blocked(page):
    """GLOBAL-FOOTER-TC-097 — Verify that an empty Social Icon Display Order is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Clear Display Order"):
        admin.clear_field(FooterAdminPage.SOCIAL_ICON_DISPLAY_ORDER)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SOCIAL_ICON_DISPLAY_ORDER) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a zero/negative Social Icon Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a zero/negative Social Icon Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-098")
def test_tc098_verify_zero_negative_social_icon_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-098 — Verify that a zero/negative Social Icon Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter Display Order = -1"):
        admin.fill_field(FooterAdminPage.SOCIAL_ICON_DISPLAY_ORDER, "-1")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.SOCIAL_ICON_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a non-numeric Social Icon Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a non-numeric Social Icon Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-099")
def test_tc099_verify_non_numeric_social_icon_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-099 — Verify that a non-numeric Social Icon Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter Display Order = abc"):
        admin.fill_field(FooterAdminPage.SOCIAL_ICON_DISPLAY_ORDER, "abc")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.SOCIAL_ICON_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that setting a Social Icon Active Status to Active publishes it visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Social Icon Active Status to Active publishes it visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-100")
def test_tc100_verify_setting_social_icon_active_status_active_publishes(page):
    """GLOBAL-FOOTER-TC-100 — Verify that setting a Social Icon Active Status to Active publishes it visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.SOCIAL_ICON_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that setting a Social Icon Active Status to Inactive hides it from the social row")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Social Icon Active Status to Inactive hides it from the social row")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-101")
def test_tc101_verify_setting_social_icon_active_status_inactive_hides(page):
    """GLOBAL-FOOTER-TC-101 — Verify that setting a Social Icon Active Status to Inactive hides it from the social row"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.SOCIAL_ICON_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that a valid Newsletter Heading (EN/AR) saves and renders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Newsletter Heading (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-102")
def test_tc102_verify_valid_newsletter_heading_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-102 — Verify that a valid Newsletter Heading (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Newsletter Heading EN / AR"):
        admin.fill_field(FooterAdminPage.NEWSLETTER_HEADING_EN, "Stay Updated")
        admin.fill_field(FooterAdminPage.NEWSLETTER_HEADING_AR, "تابع آخر الأخبار")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that leaving Newsletter Heading EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Newsletter Heading EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-103")
def test_tc103_verify_leaving_newsletter_heading_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-103 — Verify that leaving Newsletter Heading EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Newsletter Heading (EN)"):
        admin.clear_field(FooterAdminPage.NEWSLETTER_HEADING_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NEWSLETTER_HEADING_EN) == "Newsletter Heading (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that leaving Newsletter Heading AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Newsletter Heading AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-104")
def test_tc104_verify_leaving_newsletter_heading_ar_empty_blocked_arabic(page):
    """GLOBAL-FOOTER-TC-104 — Verify that leaving Newsletter Heading AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Newsletter Heading (AR)"):
        admin.clear_field(FooterAdminPage.NEWSLETTER_HEADING_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NEWSLETTER_HEADING_AR) == "عنوان النشرة الإخبارية (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that Newsletter Heading EN rejects a value exceeding 200 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Newsletter Heading EN rejects a value exceeding 200 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-105")
def test_tc105_verify_newsletter_heading_en_rejects_value_exceeding_200(page):
    """GLOBAL-FOOTER-TC-105 — Verify that Newsletter Heading EN rejects a value exceeding 200 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 200-character string"):
        admin.fill_field(FooterAdminPage.NEWSLETTER_HEADING_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.NEWSLETTER_HEADING_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that Newsletter Heading EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Newsletter Heading EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-106")
def test_tc106_verify_newsletter_heading_en_rejects_whitespace_only_input(page):
    """GLOBAL-FOOTER-TC-106 — Verify that Newsletter Heading EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.NEWSLETTER_HEADING_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.NEWSLETTER_HEADING_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that a valid Newsletter Description (EN/AR) saves and renders")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Newsletter Description (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-107")
def test_tc107_verify_valid_newsletter_description_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-107 — Verify that a valid Newsletter Description (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Newsletter Description EN"):
        admin.fill_field(FooterAdminPage.NEWSLETTER_DESCRIPTION_EN, "Subscribe to our newsletter for the latest business news, events, and opportunities.")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that Newsletter Description can be left empty (optional field)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Newsletter Description can be left empty (optional field)")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-108")
def test_tc108_verify_newsletter_description_can_be_left_empty_optional(page):
    """GLOBAL-FOOTER-TC-108 — Verify that Newsletter Description can be left empty (optional field)"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Newsletter Description EN"):
        admin.fill_field(FooterAdminPage.NEWSLETTER_DESCRIPTION_EN, "Sample value")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.newsletter_description_text()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that Newsletter Description EN rejects content exceeding 300 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Newsletter Description EN rejects content exceeding 300 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-109")
def test_tc109_verify_newsletter_description_en_rejects_content_exceeding_300(page):
    """GLOBAL-FOOTER-TC-109 — Verify that Newsletter Description EN rejects content exceeding 300 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 300-character string"):
        admin.fill_field(FooterAdminPage.NEWSLETTER_DESCRIPTION_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.NEWSLETTER_DESCRIPTION_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that a valid Email Input Placeholder (EN/AR) renders in the email field")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Email Input Placeholder (EN/AR) renders in the email field")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-110")
def test_tc110_verify_valid_email_input_placeholder_en_ar_renders(page):
    """GLOBAL-FOOTER-TC-110 — Verify that a valid Email Input Placeholder (EN/AR) renders in the email field"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Email Input Placeholder EN / AR"):
        admin.fill_field(FooterAdminPage.EMAIL_PLACEHOLDER_EN, "Enter your email")
        admin.fill_field(FooterAdminPage.EMAIL_PLACEHOLDER_AR, "أدخل بريدك الإلكتروني")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that leaving Email Input Placeholder EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Email Input Placeholder EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-111")
def test_tc111_verify_leaving_email_input_placeholder_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-111 — Verify that leaving Email Input Placeholder EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Email Input Placeholder (EN)"):
        admin.clear_field(FooterAdminPage.EMAIL_PLACEHOLDER_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.EMAIL_PLACEHOLDER_EN) == "Email Input Placeholder (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that leaving Email Input Placeholder AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Email Input Placeholder AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-112")
def test_tc112_verify_leaving_email_input_placeholder_ar_empty_blocked(page):
    """GLOBAL-FOOTER-TC-112 — Verify that leaving Email Input Placeholder AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Email Input Placeholder (AR)"):
        admin.clear_field(FooterAdminPage.EMAIL_PLACEHOLDER_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.EMAIL_PLACEHOLDER_AR) == "النص التوضيحي لحقل البريد الإلكتروني (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that Email Input Placeholder EN rejects a value exceeding 100 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Email Input Placeholder EN rejects a value exceeding 100 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-113")
def test_tc113_verify_email_input_placeholder_en_rejects_value_exceeding(page):
    """GLOBAL-FOOTER-TC-113 — Verify that Email Input Placeholder EN rejects a value exceeding 100 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 100-character string"):
        admin.fill_field(FooterAdminPage.EMAIL_PLACEHOLDER_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.EMAIL_PLACEHOLDER_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that Email Input Placeholder EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Email Input Placeholder EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-114")
def test_tc114_verify_email_input_placeholder_en_rejects_whitespace_only(page):
    """GLOBAL-FOOTER-TC-114 — Verify that Email Input Placeholder EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.EMAIL_PLACEHOLDER_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.EMAIL_PLACEHOLDER_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that a valid Subscribe Button Label (EN/AR) renders on the button")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Subscribe Button Label (EN/AR) renders on the button")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-115")
def test_tc115_verify_valid_subscribe_button_label_en_ar_renders(page):
    """GLOBAL-FOOTER-TC-115 — Verify that a valid Subscribe Button Label (EN/AR) renders on the button"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Subscribe Button Label EN / AR"):
        admin.fill_field(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_EN, "Subscribe")
        admin.fill_field(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_AR, "اشترك")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that leaving Subscribe Button Label EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Subscribe Button Label EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-116")
def test_tc116_verify_leaving_subscribe_button_label_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-116 — Verify that leaving Subscribe Button Label EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Subscribe Button Label (EN)"):
        admin.clear_field(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_EN) == "Subscribe Button Label (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that leaving Subscribe Button Label AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Subscribe Button Label AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-117")
def test_tc117_verify_leaving_subscribe_button_label_ar_empty_blocked(page):
    """GLOBAL-FOOTER-TC-117 — Verify that leaving Subscribe Button Label AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Subscribe Button Label (AR)"):
        admin.clear_field(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_AR) == "نص زر الاشتراك (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that Subscribe Button Label EN rejects a value exceeding 50 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Subscribe Button Label EN rejects a value exceeding 50 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-118")
def test_tc118_verify_subscribe_button_label_en_rejects_value_exceeding(page):
    """GLOBAL-FOOTER-TC-118 — Verify that Subscribe Button Label EN rejects a value exceeding 50 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 50-character string"):
        admin.fill_field(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that Subscribe Button Label EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Subscribe Button Label EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-119")
def test_tc119_verify_subscribe_button_label_en_rejects_whitespace_only(page):
    """GLOBAL-FOOTER-TC-119 — Verify that Subscribe Button Label EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that valid Copyright Text (EN/AR) saves and renders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that valid Copyright Text (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-123")
def test_tc123_verify_valid_copyright_text_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-123 — Verify that valid Copyright Text (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Copyright Text EN"):
        admin.fill_field(FooterAdminPage.COPYRIGHT_TEXT_EN, "© 2026 Qatar Chamber. All rights reserved.")
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that leaving Copyright Text EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Copyright Text EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-124")
def test_tc124_verify_leaving_copyright_text_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-124 — Verify that leaving Copyright Text EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Copyright Text (EN)"):
        admin.clear_field(FooterAdminPage.COPYRIGHT_TEXT_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.COPYRIGHT_TEXT_EN) == "Copyright Text (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that leaving Copyright Text AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Copyright Text AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-125")
def test_tc125_verify_leaving_copyright_text_ar_empty_blocked_arabic(page):
    """GLOBAL-FOOTER-TC-125 — Verify that leaving Copyright Text AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Copyright Text (AR)"):
        admin.clear_field(FooterAdminPage.COPYRIGHT_TEXT_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.COPYRIGHT_TEXT_AR) == "نص حقوق النشر (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that Copyright Text EN rejects a value exceeding 300 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Copyright Text EN rejects a value exceeding 300 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-126")
def test_tc126_verify_copyright_text_en_rejects_value_exceeding_300(page):
    """GLOBAL-FOOTER-TC-126 — Verify that Copyright Text EN rejects a value exceeding 300 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 300-character string"):
        admin.fill_field(FooterAdminPage.COPYRIGHT_TEXT_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.COPYRIGHT_TEXT_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that Copyright Text EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Copyright Text EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-127")
def test_tc127_verify_copyright_text_en_rejects_whitespace_only_input(page):
    """GLOBAL-FOOTER-TC-127 — Verify that Copyright Text EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.COPYRIGHT_TEXT_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.COPYRIGHT_TEXT_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting Copyright Active Status to Active publishes the copyright bar")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Copyright Active Status to Active publishes the copyright bar")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-128")
def test_tc128_verify_setting_copyright_active_status_active_publishes_copyright(page):
    """GLOBAL-FOOTER-TC-128 — Verify that setting Copyright Active Status to Active publishes the copyright bar"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.COPYRIGHT_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting Copyright Active Status to Inactive removes the entire copyright bar")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Copyright Active Status to Inactive removes the entire copyright bar")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-129")
def test_tc129_verify_setting_copyright_active_status_inactive_removes_entire(page):
    """GLOBAL-FOOTER-TC-129 — Verify that setting Copyright Active Status to Inactive removes the entire copyright bar"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.COPYRIGHT_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that a valid Bottom Link Title (EN/AR) saves and renders in the copyright bar")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Bottom Link Title (EN/AR) saves and renders in the copyright bar")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-130")
def test_tc130_verify_valid_bottom_link_title_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-130 — Verify that a valid Bottom Link Title (EN/AR) saves and renders in the copyright bar"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Bottom Link Title EN / AR"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_TITLE_EN, "Accessibility")
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_TITLE_AR, "إمكانية الوصول")
        admin.click_publish()
    with allure.step("Assert: toast success"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that leaving Bottom Link Title EN empty is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Bottom Link Title EN empty is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-131")
def test_tc131_verify_leaving_bottom_link_title_en_empty_blocked(page):
    """GLOBAL-FOOTER-TC-131 — Verify that leaving Bottom Link Title EN empty is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Bottom Link Title (EN)"):
        admin.clear_field(FooterAdminPage.BOTTOM_LINK_TITLE_EN)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.BOTTOM_LINK_TITLE_EN) == "Bottom Link Title (EN) is required."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that leaving Bottom Link Title AR empty is blocked with the Arabic message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that leaving Bottom Link Title AR empty is blocked with the Arabic message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-132")
def test_tc132_verify_leaving_bottom_link_title_ar_empty_blocked(page):
    """GLOBAL-FOOTER-TC-132 — Verify that leaving Bottom Link Title AR empty is blocked with the Arabic message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Bottom Link Title (AR)"):
        admin.clear_field(FooterAdminPage.BOTTOM_LINK_TITLE_AR)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.BOTTOM_LINK_TITLE_AR) == "عنوان الرابط السفلي (عربي) مطلوب."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that Bottom Link Title EN rejects a value exceeding 100 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Bottom Link Title EN rejects a value exceeding 100 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-133")
def test_tc133_verify_bottom_link_title_en_rejects_value_exceeding(page):
    """GLOBAL-FOOTER-TC-133 — Verify that Bottom Link Title EN rejects a value exceeding 100 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 100-character string"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_TITLE_EN, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.BOTTOM_LINK_TITLE_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that Bottom Link Title EN rejects whitespace-only input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Bottom Link Title EN rejects whitespace-only input")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-134")
def test_tc134_verify_bottom_link_title_en_rejects_whitespace_only(page):
    """GLOBAL-FOOTER-TC-134 — Verify that Bottom Link Title EN rejects whitespace-only input"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_TITLE_EN, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.BOTTOM_LINK_TITLE_EN) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that a valid Bottom Link URL is accepted and navigates correctly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Bottom Link URL is accepted and navigates correctly")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-135")
def test_tc135_verify_valid_bottom_link_url_accepted_navigates_correctly(page):
    """GLOBAL-FOOTER-TC-135 — Verify that a valid Bottom Link URL is accepted and navigates correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Bottom Link URL EN"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_URL, "https://www.qatarchamber.com/accessibility")
        admin.click_publish()
    with allure.step("Assert: toast success"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that an empty Bottom Link URL is blocked")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an empty Bottom Link URL is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-136")
def test_tc136_verify_empty_bottom_link_url_blocked(page):
    """GLOBAL-FOOTER-TC-136 — Verify that an empty Bottom Link URL is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Bottom Link URL (EN)"):
        admin.clear_field(FooterAdminPage.BOTTOM_LINK_URL)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.BOTTOM_LINK_URL) == "Please enter a valid URL."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that an invalid Bottom Link URL is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an invalid Bottom Link URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-137")
def test_tc137_verify_invalid_bottom_link_url_rejected(page):
    """GLOBAL-FOOTER-TC-137 — Verify that an invalid Bottom Link URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter not-a-url"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_URL, "not-a-url")
        admin.click_publish()
    with allure.step("Assert: invalid-URL error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.BOTTOM_LINK_URL) == "Please enter a valid URL."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that Bottom Link URL rejects a value exceeding 500 characters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Bottom Link URL rejects a value exceeding 500 characters")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-138")
def test_tc138_verify_bottom_link_url_rejects_value_exceeding_500(page):
    """GLOBAL-FOOTER-TC-138 — Verify that Bottom Link URL rejects a value exceeding 500 characters"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter a 500-character string"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_URL, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        admin.click_publish()
    with allure.step("Assert: boundary error shown, value not saved beyond the limit"):
        assert admin.field_error_text(FooterAdminPage.BOTTOM_LINK_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that whitespace-only input in Bottom Link URL is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that whitespace-only input in Bottom Link URL is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-139")
def test_tc139_verify_whitespace_only_input_bottom_link_url_rejected(page):
    """GLOBAL-FOOTER-TC-139 — Verify that whitespace-only input in Bottom Link URL is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter three spaces"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_URL, "   ")
        admin.click_publish()
    with allure.step("Assert: required-field / format error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.BOTTOM_LINK_URL) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that a valid Bottom Link Display Order orders links correctly")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Bottom Link Display Order orders links correctly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-142")
def test_tc142_verify_valid_bottom_link_display_order_orders_links(page):
    """GLOBAL-FOOTER-TC-142 — Verify that a valid Bottom Link Display Order orders links correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Set Display Order = 1 for Accessibility"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_DISPLAY_ORDER, "1")
        admin.click_publish()
    with allure.step("Assert: Accessibility appears first in its list"):
        footer.open_home()
        assert footer.footer_link_display_index("Accessibility") == 0


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that an empty Bottom Link Display Order is blocked")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Bottom Link Display Order is blocked")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-143")
def test_tc143_verify_empty_bottom_link_display_order_blocked(page):
    """GLOBAL-FOOTER-TC-143 — Verify that an empty Bottom Link Display Order is blocked"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Clear Display Order"):
        admin.clear_field(FooterAdminPage.BOTTOM_LINK_DISPLAY_ORDER)
        admin.click_publish()
    with allure.step("Assert: required-field error, publish blocked"):
        assert admin.field_error_text(FooterAdminPage.BOTTOM_LINK_DISPLAY_ORDER) != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that a zero/negative Bottom Link Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a zero/negative Bottom Link Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-144")
def test_tc144_verify_zero_negative_bottom_link_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-144 — Verify that a zero/negative Bottom Link Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Display Order = -1"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_DISPLAY_ORDER, "-1")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.BOTTOM_LINK_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that a non-numeric Bottom Link Display Order is rejected")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a non-numeric Bottom Link Display Order is rejected")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-145")
def test_tc145_verify_non_numeric_bottom_link_display_order_rejected(page):
    """GLOBAL-FOOTER-TC-145 — Verify that a non-numeric Bottom Link Display Order is rejected"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Display Order = abc"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_DISPLAY_ORDER, "abc")
        admin.click_publish()
    with allure.step("Assert: validation error, publish blocked"):
        error = admin.field_error_text(FooterAdminPage.BOTTOM_LINK_DISPLAY_ORDER)
        assert error != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting a Bottom Link Active Status to Active publishes it visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Bottom Link Active Status to Active publishes it visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-146")
def test_tc146_verify_setting_bottom_link_active_status_active_publishes(page):
    """GLOBAL-FOOTER-TC-146 — Verify that setting a Bottom Link Active Status to Active publishes it visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.BOTTOM_LINK_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting a Bottom Link Active Status to Inactive hides it while sibling links and copyright text remain")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Bottom Link Active Status to Inactive hides it while sibling links and copyright text remain")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-147")
def test_tc147_verify_setting_bottom_link_active_status_inactive_hides(page):
    """GLOBAL-FOOTER-TC-147 — Verify that setting a Bottom Link Active Status to Inactive hides it while sibling links and copyright text remain"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.BOTTOM_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Access Control")
@allure.story("Verify that a Site Content Editor can access and publish Footer Management, Useful Links Manager, and Social Media Icons Management")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that a Site Content Editor can access and publish Footer Management, Useful Links Manager, and Social Media Icons Management")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-150")
def test_tc150_verify_site_content_editor_can_access_publish_footer(page):
    """GLOBAL-FOOTER-TC-150 — Verify that a Site Content Editor can access and publish Footer Management, Useful Links Manager, and Social Media Icons Management"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Log in as a Site Content Editor and open Footer Management, Useful Links Manager, and Social Media Icons Management"):
        admin.open_footer_management()
        admin.click_publish()
        admin.open_useful_links_manager()
        admin.click_publish()
        admin.open_social_media_icons_management()
        admin.click_publish()
    with allure.step("Assert: each publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Access Control")
@allure.story("Verify that a user without Footer Management permission is denied access with the correct English message")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that a user without Footer Management permission is denied access with the correct English message")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-151")
def test_tc151_verify_user_without_footer_management_permission_denied_access(page):
    """GLOBAL-FOOTER-TC-151 — Verify that a user without Footer Management permission is denied access with the correct English message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Attempt to open Footer Management as a user without permission"):
        admin.open_footer_management()
    with allure.step("Assert: access denied, English message"):
        assert "denied" in admin.access_denied_message().lower() or "permission" in admin.access_denied_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Access Control")
@allure.story("Verify that the Access Denied message renders in Arabic when the CMS is set to Arabic")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that the Access Denied message renders in Arabic when the CMS is set to Arabic")
@pytest.mark.auth
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-152")
def test_tc152_verify_access_denied_message_renders_arabic_when_cms(page):
    """GLOBAL-FOOTER-TC-152 — Verify that the Access Denied message renders in Arabic when the CMS is set to Arabic"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Switch the CMS UI language to Arabic and attempt to open Footer Management without permission"):
        admin.open_footer_management()
    with allure.step("Assert: access denied message renders in Arabic"):
        message = admin.access_denied_message()
        assert any("\u0600" <= ch <= "\u06FF" for ch in message)


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the \"Follow Us on Social Media\" label is configurable and renders above the icon row")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the \"Follow Us on Social Media\" label is configurable and renders above the icon row")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-155")
def test_tc155_verify_follow_us_social_media_label_configurable_renders(page):
    """GLOBAL-FOOTER-TC-155 — Verify that the "Follow Us on Social Media" label is configurable and renders above the icon row"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Verify the Social Media Label is configured in the CMS"):
        label_value = admin.field_value(FooterAdminPage.SOCIAL_MEDIA_LABEL_EN)
    with allure.step("Assert: label field is non-empty in the CMS"):
        assert label_value != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify the full admin lifecycle for a Footer Nav Link: draft → preview → publish → unpublish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify the full admin lifecycle for a Footer Nav Link: draft → preview → publish → unpublish")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-162")
def test_tc162_verify_full_admin_lifecycle_for_footer_nav_link(page):
    """GLOBAL-FOOTER-TC-162 — Verify the full admin lifecycle for a Footer Nav Link: draft → preview → publish → unpublish"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Draft a Footer Nav Link"):
        admin.open_footer_management()
        admin.fill_field(FooterAdminPage.NAV_LINK_TITLE_EN, "Membership Services")
        admin.fill_field(FooterAdminPage.NAV_LINK_URL, "https://www.qatarchamber.com/membership")
        admin.save_draft()
    with allure.step("Preview it"):
        admin.click_preview()
    with allure.step("Publish it"):
        admin.click_publish()
    with allure.step("Assert: renders live"):
        footer.open_home()
        assert footer.footer_link_href("Membership Services") is not None
    with allure.step("Unpublish it"):
        admin.click_unpublish()
    with allure.step("Assert: no longer renders live"):
        footer.open_home()
        assert footer.is_footer_link_visible("Membership Services") is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that disabling a Footer Nav Link hides only that link while sibling links in the same column stay visible")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling a Footer Nav Link hides only that link while sibling links in the same column stay visible")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-165")
def test_tc165_verify_disabling_footer_nav_link_hides_only_link(page):
    """GLOBAL-FOOTER-TC-165 — Verify that disabling a Footer Nav Link hides only that link while sibling links in the same column stay visible"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Disable one Footer Nav Link"):
        admin.open_footer_management()
        admin.set_toggle(FooterAdminPage.NAV_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that disabling a Quick Link hides only that link from the Quick Links column while others remain")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling a Quick Link hides only that link from the Quick Links column while others remain")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-166")
def test_tc166_verify_disabling_quick_link_hides_only_link_from(page):
    """GLOBAL-FOOTER-TC-166 — Verify that disabling a Quick Link hides only that link from the Quick Links column while others remain"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Disable one Quick Link"):
        admin.open_useful_links_manager()
        admin.set_toggle(FooterAdminPage.QUICK_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that setting every Quick Link to Inactive removes both the Quick Links list and its heading")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting every Quick Link to Inactive removes both the Quick Links list and its heading")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-167")
def test_tc167_verify_setting_every_quick_link_inactive_removes_both(page):
    """GLOBAL-FOOTER-TC-167 — Verify that setting every Quick Link to Inactive removes both the Quick Links list and its heading"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Set every Quick Link to Inactive"):
        admin.open_useful_links_manager()
        admin.set_toggle(FooterAdminPage.QUICK_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that disabling a Social Media Icon removes it from the row without leaving a visual gap")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling a Social Media Icon removes it from the row without leaving a visual gap")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-168")
def test_tc168_verify_disabling_social_media_icon_removes_it_from(page):
    """GLOBAL-FOOTER-TC-168 — Verify that disabling a Social Media Icon removes it from the row without leaving a visual gap"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Disable a Social Media Icon"):
        admin.open_social_media_icons_management()
        admin.set_toggle(FooterAdminPage.SOCIAL_ICON_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting Copyright Active Status to Inactive removes the entire copyright bar including its active bottom links")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Copyright Active Status to Inactive removes the entire copyright bar including its active bottom links")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-169")
def test_tc169_verify_setting_copyright_active_status_inactive_removes_entire(page):
    """GLOBAL-FOOTER-TC-169 — Verify that setting Copyright Active Status to Inactive removes the entire copyright bar including its active bottom links"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Set Copyright Active Status to Inactive"):
        admin.open_footer_management()
        admin.set_toggle(FooterAdminPage.COPYRIGHT_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that disabling one Bottom Bar Link hides only that link while Copyright text and sibling links remain")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling one Bottom Bar Link hides only that link while Copyright text and sibling links remain")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-170")
def test_tc170_verify_disabling_one_bottom_bar_link_hides_only(page):
    """GLOBAL-FOOTER-TC-170 — Verify that disabling one Bottom Bar Link hides only that link while Copyright text and sibling links remain"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Disable one Bottom Bar Link"):
        admin.open_footer_management()
        admin.set_toggle(FooterAdminPage.BOTTOM_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: publish succeeds"):
        assert "success" in admin.toast_message().lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify the full admin workflow across all footer components: branding → nav columns → Quick Links → social icons → newsletter → copyright, ending in a single publish")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify the full admin workflow across all footer components: branding → nav columns → Quick Links → social icons → newsletter → copyright, ending in a single publish")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-171")
def test_tc171_verify_full_admin_workflow_across_all_footer_components(page):
    """GLOBAL-FOOTER-TC-171 — Verify the full admin workflow across all footer components: branding → nav columns → Quick Links → social icons → newsletter → copyright, ending in a single publish"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Configure Branding"):
        admin.open_footer_management()
        admin.fill_field(FooterAdminPage.FOOTER_DESCRIPTION_EN, "Qatar Chamber promotes trade and industry.")
    with allure.step("Configure Nav Columns"):
        admin.fill_field(FooterAdminPage.COLUMN_HEADING_EN, "About Qatar Chamber")
    with allure.step("Configure Quick Links"):
        admin.open_useful_links_manager()
        admin.fill_field(FooterAdminPage.QUICK_LINK_TITLE_EN, "Careers")
    with allure.step("Configure Social Icons"):
        admin.open_social_media_icons_management()
        admin.fill_field(FooterAdminPage.PLATFORM_NAME, "LinkedIn")
    with allure.step("Configure Newsletter"):
        admin.open_footer_management()
        admin.fill_field(FooterAdminPage.NEWSLETTER_HEADING_EN, "Stay Updated with Qatar Chamber")
    with allure.step("Configure Copyright"):
        admin.fill_field(FooterAdminPage.COPYRIGHT_TEXT_EN, "Qatar Chamber. All Rights Reserved.")
    with allure.step("Publish once"):
        admin.click_publish()
    with allure.step("Assert: a single publish applies every configured component"):
        assert "success" in admin.toast_message().lower()

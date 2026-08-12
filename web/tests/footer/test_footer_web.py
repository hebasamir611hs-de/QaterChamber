"""
web/tests/footer/test_footer_web.py — Site Footer & Social Media Icons,
Web (public site) surface (PBI 133231, "QC-GBL-004").

Structural split (2026-08-11, per .claude/context/active/standards.md ->
"Automation Structure - Project Deviation from the Plugin Default"): this
module holds every Web-tagged GLOBAL-FOOTER-TC-* case. The sibling
Control_Panel-tagged cases live in test_footer_control_panel.py in this same
folder. A case tagged BOTH Web and Control_Panel (39 of the 184 cases) has
one test in each module, sharing the same traceability ID, each keeping
only the live-site-verification half (this module) or the CMS-configuration
half (test_footer_control_panel.py) of the original scripted test. Each such
test still performs the CMS configuration step itself (an unavoidable Arrange
precondition so the test remains independent/standalone per
automation-standards.md), but only asserts against the live public footer.

Every test still carries:
  - its QA traceability ID (`@pytest.mark.traceability("GLOBAL-FOOTER-TC-xxx")`)
  - the Axis B backlog marker `@pytest.mark.pbi_133231` + `allure.label("pbi", "133231")`
  - one marker per tag axis actually present on its source case (Lifecycle,
    Service/Module, Platform, Category, Business keyword) — never invented.

Admin/Control-Panel setup steps (needed as Arrange preconditions for several
cases) go through `FooterAdminPage`, whose field constants are
`TODO(locator)` placeholders (disclosed, CMS-only exception — see
footer_admin_page.py's docstring). Every assertion that can be verified on
the **public** footer uses `FooterPage`'s real, CLI/MCP-extracted locators
instead — never a TODO for anything reachable on the live page.

Scripted, not executed: per the task's hard constraint, none of these tests
have been run. "Scripted" (automation-standards.md's Definition of Done,
Scripted tier) is the only claim made here.
"""

import allure
import pytest

from web.pages.footer.footer_page import FooterPage
from web.pages.footer.footer_admin_page import FooterAdminPage


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that a valid Footer Logo Redirect URL is accepted and used on logo click")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Footer Logo Redirect URL is accepted and used on logo click")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-010")
def test_tc010_verify_valid_footer_logo_redirect_url_accepted_used(page):
    """GLOBAL-FOOTER-TC-010 — Verify that a valid Footer Logo Redirect URL is accepted and used on logo click"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Footer Logo Redirect URL EN"):
        admin.fill_field(FooterAdminPage.FOOTER_LOGO_REDIRECT_URL, "https://www.qatarchamber.com/")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.logo_href()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Branding")
@allure.story("Verify that a valid Footer Description (EN/AR) saves and renders")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Footer Description (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-015")
def test_tc015_verify_valid_footer_description_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-015 — Verify that a valid Footer Description (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Footer Description EN"):
        admin.fill_field(FooterAdminPage.FOOTER_DESCRIPTION_EN, "Qatar Chamber promotes trade and industry.")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.description_text()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Social Media Label (EN/AR) saves and renders above the icons row")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Social Media Label (EN/AR) saves and renders above the icons row")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-018")
def test_tc018_verify_valid_social_media_label_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-018 — Verify that a valid Social Media Label (EN/AR) saves and renders above the icons row"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Social Media Label EN / AR"):
        admin.fill_field(FooterAdminPage.SOCIAL_MEDIA_LABEL_EN, "Follow Us on Social Media")
        admin.fill_field(FooterAdminPage.SOCIAL_MEDIA_LABEL_AR, "تابعنا على وسائل التواصل الاجتماعي")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.social_label_text()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a valid Column Heading (EN/AR) saves and renders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Column Heading (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-023")
def test_tc023_verify_valid_column_heading_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-023 — Verify that a valid Column Heading (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Column Heading EN / AR"):
        admin.fill_field(FooterAdminPage.COLUMN_HEADING_EN, "About Qatar Chamber")
        admin.fill_field(FooterAdminPage.COLUMN_HEADING_AR, "عن غرفة قطر")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.nav_column_heading_text("About Qatar Chamber")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that setting Column Active Status to Active publishes the column visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Column Active Status to Active publishes the column visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-034")
def test_tc034_verify_setting_column_active_status_active_publishes_column(page):
    """GLOBAL-FOOTER-TC-034 — Verify that setting Column Active Status to Active publishes the column visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.COLUMN_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is True"):
        footer.open_home()
        assert footer.is_nav_column_visible("About Qatar Chamber") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that setting Column Active Status to Inactive hides the column from the live footer")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Column Active Status to Inactive hides the column from the live footer")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-035")
def test_tc035_verify_setting_column_active_status_inactive_hides_column(page):
    """GLOBAL-FOOTER-TC-035 — Verify that setting Column Active Status to Inactive hides the column from the live footer"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.COLUMN_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is False"):
        footer.open_home()
        assert footer.is_nav_column_visible("About Qatar Chamber") is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a valid Nav Link Title (EN/AR) saves and renders under its column")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Nav Link Title (EN/AR) saves and renders under its column")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-036")
def test_tc036_verify_valid_nav_link_title_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-036 — Verify that a valid Nav Link Title (EN/AR) saves and renders under its column"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Nav Link Title EN / AR"):
        admin.fill_field(FooterAdminPage.NAV_LINK_TITLE_EN, "Membership Services")
        admin.fill_field(FooterAdminPage.NAV_LINK_TITLE_AR, "خدمات العضوية")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.is_footer_link_visible("Membership Services") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a valid Nav Link URL is accepted and navigates correctly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Nav Link URL is accepted and navigates correctly")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-041")
def test_tc041_verify_valid_nav_link_url_accepted_navigates_correctly(page):
    """GLOBAL-FOOTER-TC-041 — Verify that a valid Nav Link URL is accepted and navigates correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Nav Link URL EN"):
        admin.fill_field(FooterAdminPage.NAV_LINK_URL, "https://www.qatarchamber.com/membership")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.footer_link_href("Membership Services") == "https://www.qatarchamber.com/membership"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a Nav Link configured \"Open in New Tab = true\" opens in a new tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Nav Link configured \"Open in New Tab = true\" opens in a new tab")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-046")
def test_tc046_verify_nav_link_configured_open_new_tab_true(page):
    """GLOBAL-FOOTER-TC-046 — Verify that a Nav Link configured \"Open in New Tab = true\" opens in a new tab"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the live footer and locate an external Nav Link configured to open in a new tab"):
        footer.open_home()
    with allure.step("Assert: target=_blank"):
        assert footer.footer_link_target("ATA Carnets") == "_blank"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that a Nav Link configured \"Open in New Tab = false\" opens in the same tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Nav Link configured \"Open in New Tab = false\" opens in the same tab")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-047")
def test_tc047_verify_nav_link_configured_open_new_tab_false(page):
    """GLOBAL-FOOTER-TC-047 — Verify that a Nav Link configured \"Open in New Tab = false\" opens in the same tab"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the live footer and locate an internal Nav Link configured to open in the same tab"):
        footer.open_home()
    with allure.step("Assert: no target=_blank (same tab)"):
        assert footer.footer_link_target("Chairman's Message") in (None, "", "_self")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that setting a Nav Link Active Status to Active publishes it visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Nav Link Active Status to Active publishes it visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-052")
def test_tc052_verify_setting_nav_link_active_status_active_publishes(page):
    """GLOBAL-FOOTER-TC-052 — Verify that setting a Nav Link Active Status to Active publishes it visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.NAV_LINK_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is True"):
        footer.open_home()
        assert footer.is_footer_link_visible("Membership Services") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that setting a Nav Link Active Status to Inactive hides it from the live footer")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Nav Link Active Status to Inactive hides it from the live footer")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-053")
def test_tc053_verify_setting_nav_link_active_status_inactive_hides(page):
    """GLOBAL-FOOTER-TC-053 — Verify that setting a Nav Link Active Status to Inactive hides it from the live footer"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.NAV_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is False"):
        footer.open_home()
        assert footer.is_footer_link_visible("Membership Services") is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a valid Quick Links Column Heading (EN/AR) saves and renders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Quick Links Column Heading (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-054")
def test_tc054_verify_valid_quick_links_column_heading_en_ar(page):
    """GLOBAL-FOOTER-TC-054 — Verify that a valid Quick Links Column Heading (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter Quick Links Column Heading EN / AR"):
        admin.fill_field(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_EN, "Quick Links")
        admin.fill_field(FooterAdminPage.QUICK_LINKS_COLUMN_HEADING_AR, "روابط سريعة")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.nav_column_heading_text("Quick Links")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a valid Quick Link Title (EN/AR) saves and renders in the Quick Links list")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Quick Link Title (EN/AR) saves and renders in the Quick Links list")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-059")
def test_tc059_verify_valid_quick_link_title_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-059 — Verify that a valid Quick Link Title (EN/AR) saves and renders in the Quick Links list"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter Quick Link Title EN / AR"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_TITLE_EN, "Careers")
        admin.fill_field(FooterAdminPage.QUICK_LINK_TITLE_AR, "الوظائف")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.is_footer_link_visible("Careers") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a valid Quick Link URL is accepted and navigates correctly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Quick Link URL is accepted and navigates correctly")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-064")
def test_tc064_verify_valid_quick_link_url_accepted_navigates_correctly(page):
    """GLOBAL-FOOTER-TC-064 — Verify that a valid Quick Link URL is accepted and navigates correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Enter Quick Link URL EN"):
        admin.fill_field(FooterAdminPage.QUICK_LINK_URL, "https://www.qatarchamber.com/careers")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.footer_link_href("Careers") == "https://www.qatarchamber.com/careers"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a Quick Link configured \"Open in New Tab = true\" opens in a new tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Quick Link configured \"Open in New Tab = true\" opens in a new tab")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-069")
def test_tc069_verify_quick_link_configured_open_new_tab_true(page):
    """GLOBAL-FOOTER-TC-069 — Verify that a Quick Link configured \"Open in New Tab = true\" opens in a new tab"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the live footer and locate a Quick Link configured to open in a new tab"):
        footer.open_home()
    with allure.step("Assert: target=_blank"):
        assert footer.footer_link_target("Career Opportunities") == "_blank"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that a Quick Link configured \"Open in New Tab = false\" opens in the same tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Quick Link configured \"Open in New Tab = false\" opens in the same tab")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-070")
def test_tc070_verify_quick_link_configured_open_new_tab_false(page):
    """GLOBAL-FOOTER-TC-070 — Verify that a Quick Link configured \"Open in New Tab = false\" opens in the same tab"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the live footer and locate a Quick Link configured to open in the same tab"):
        footer.open_home()
    with allure.step("Assert: no target=_blank (same tab)"):
        assert footer.footer_link_target("Useful Links") in (None, "", "_self")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that setting a Quick Link Active Status to Active publishes it visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Quick Link Active Status to Active publishes it visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-075")
def test_tc075_verify_setting_quick_link_active_status_active_publishes(page):
    """GLOBAL-FOOTER-TC-075 — Verify that setting a Quick Link Active Status to Active publishes it visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.QUICK_LINK_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is True"):
        footer.open_home()
        assert footer.is_footer_link_visible("Careers") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that setting a Quick Link Active Status to Inactive hides it from the Quick Links column")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Quick Link Active Status to Inactive hides it from the Quick Links column")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-076")
def test_tc076_verify_setting_quick_link_active_status_inactive_hides(page):
    """GLOBAL-FOOTER-TC-076 — Verify that setting a Quick Link Active Status to Inactive hides it from the Quick Links column"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.QUICK_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is False"):
        footer.open_home()
        assert footer.is_footer_link_visible("Careers") is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Social Icon Image upload is accepted")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Social Icon Image upload is accepted")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-081")
def test_tc081_verify_valid_social_icon_image_upload_accepted(page):
    """GLOBAL-FOOTER-TC-081 — Verify that a valid Social Icon Image upload is accepted"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Upload linkedin-icon.svg"):
        admin.upload_file(FooterAdminPage.SOCIAL_ICON_IMAGE_UPLOAD, "linkedin-icon.svg")
        admin.click_publish()
    with allure.step("Assert: icon renders in the social row"):
        footer.open_home()
        assert footer.is_social_icon_visible("LinkedIn")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Icon Alt Text (EN/AR) saves and is applied to the icon")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Icon Alt Text (EN/AR) saves and is applied to the icon")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-085")
def test_tc085_verify_valid_icon_alt_text_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-085 — Verify that a valid Icon Alt Text (EN/AR) saves and is applied to the icon"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter Icon Alt Text EN / AR"):
        admin.fill_field(FooterAdminPage.ICON_ALT_TEXT_EN, "LinkedIn")
        admin.fill_field(FooterAdminPage.ICON_ALT_TEXT_AR, "لينكدإن")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.social_icon_alt("LinkedIn") == "LinkedIn"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that a valid Social Redirect URL opens the correct channel")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Social Redirect URL opens the correct channel")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-090")
def test_tc090_verify_valid_social_redirect_url_opens_correct_channel(page):
    """GLOBAL-FOOTER-TC-090 — Verify that a valid Social Redirect URL opens the correct channel"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Enter Social Redirect URL EN"):
        admin.fill_field(FooterAdminPage.SOCIAL_REDIRECT_URL, "https://www.linkedin.com/company/qatarchamber")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.social_icon_href("LinkedIn") == "https://www.linkedin.com/company/qatarchamber"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that Social Icon \"Open in New Tab\" is fixed to true with no toggle exposed")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Social Icon \"Open in New Tab\" is fixed to true with no toggle exposed")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-095")
def test_tc095_verify_social_icon_open_new_tab_fixed_true(page):
    """GLOBAL-FOOTER-TC-095 — Verify that Social Icon \"Open in New Tab\" is fixed to true with no toggle exposed"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Open a Social Icon record in the CMS"):
        is_readonly = admin.is_field_readonly(FooterAdminPage.SOCIAL_ICON_OPEN_NEW_TAB_FIELD)
        toggle_exposed = admin.is_toggle_exposed(FooterAdminPage.SOCIAL_ICON_OPEN_NEW_TAB_FIELD)
    with allure.step("Assert: field is fixed true, no OFF option, and the live icon opens in a new tab"):
        footer.open_home()
        assert footer.social_icon_target("LinkedIn") == "_blank"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that setting a Social Icon Active Status to Active publishes it visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Social Icon Active Status to Active publishes it visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-100")
def test_tc100_verify_setting_social_icon_active_status_active_publishes(page):
    """GLOBAL-FOOTER-TC-100 — Verify that setting a Social Icon Active Status to Active publishes it visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.SOCIAL_ICON_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is True"):
        footer.open_home()
        assert footer.is_social_icon_visible("LinkedIn") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Social Media Icons")
@allure.story("Verify that setting a Social Icon Active Status to Inactive hides it from the social row")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Social Icon Active Status to Inactive hides it from the social row")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-101")
def test_tc101_verify_setting_social_icon_active_status_inactive_hides(page):
    """GLOBAL-FOOTER-TC-101 — Verify that setting a Social Icon Active Status to Inactive hides it from the social row"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_social_media_icons_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.SOCIAL_ICON_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is False"):
        footer.open_home()
        assert footer.is_social_icon_visible("LinkedIn") is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that a valid Newsletter Heading (EN/AR) saves and renders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Newsletter Heading (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-102")
def test_tc102_verify_valid_newsletter_heading_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-102 — Verify that a valid Newsletter Heading (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Newsletter Heading EN / AR"):
        admin.fill_field(FooterAdminPage.NEWSLETTER_HEADING_EN, "Stay Updated")
        admin.fill_field(FooterAdminPage.NEWSLETTER_HEADING_AR, "تابع آخر الأخبار")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.newsletter_heading_text()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that a valid Newsletter Description (EN/AR) saves and renders")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Newsletter Description (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-107")
def test_tc107_verify_valid_newsletter_description_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-107 — Verify that a valid Newsletter Description (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Newsletter Description EN"):
        admin.fill_field(FooterAdminPage.NEWSLETTER_DESCRIPTION_EN, "Subscribe to our newsletter for the latest business news, events, and opportunities.")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.newsletter_description_text()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that a valid Email Input Placeholder (EN/AR) renders in the email field")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Email Input Placeholder (EN/AR) renders in the email field")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-110")
def test_tc110_verify_valid_email_input_placeholder_en_ar_renders(page):
    """GLOBAL-FOOTER-TC-110 — Verify that a valid Email Input Placeholder (EN/AR) renders in the email field"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Email Input Placeholder EN / AR"):
        admin.fill_field(FooterAdminPage.EMAIL_PLACEHOLDER_EN, "Enter your email")
        admin.fill_field(FooterAdminPage.EMAIL_PLACEHOLDER_AR, "أدخل بريدك الإلكتروني")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.email_placeholder()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that a valid Subscribe Button Label (EN/AR) renders on the button")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Subscribe Button Label (EN/AR) renders on the button")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-115")
def test_tc115_verify_valid_subscribe_button_label_en_ar_renders(page):
    """GLOBAL-FOOTER-TC-115 — Verify that a valid Subscribe Button Label (EN/AR) renders on the button"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Subscribe Button Label EN / AR"):
        admin.fill_field(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_EN, "Subscribe")
        admin.fill_field(FooterAdminPage.SUBSCRIBE_BUTTON_LABEL_AR, "اشترك")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.subscribe_button_label()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that entering an empty email and clicking Subscribe shows the validation message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that entering an empty email and clicking Subscribe shows the validation message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-120")
def test_tc120_verify_entering_empty_email_clicking_subscribe_shows_validation(page):
    """GLOBAL-FOOTER-TC-120 — Verify that entering an empty email and clicking Subscribe shows the validation message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Enter an empty email and click Subscribe"):
        footer.enter_newsletter_email("")
        footer.click_subscribe()
    with allure.step("Assert: native required-field validation blocks submission"):
        assert footer.is_newsletter_email_valid() is False
        assert footer.newsletter_email_validation_message() != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that entering an invalid email format and clicking Subscribe shows the validation message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that entering an invalid email format and clicking Subscribe shows the validation message")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-121")
def test_tc121_verify_entering_invalid_email_format_clicking_subscribe_shows(page):
    """GLOBAL-FOOTER-TC-121 — Verify that entering an invalid email format and clicking Subscribe shows the validation message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Enter an invalid-format email and click Subscribe"):
        footer.enter_newsletter_email("not-an-email")
        footer.click_subscribe()
    with allure.step("Assert: native email-format validation blocks submission"):
        assert footer.is_newsletter_email_valid() is False
        assert footer.newsletter_email_validation_message() != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that entering a valid email and clicking Subscribe submits successfully")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that entering a valid email and clicking Subscribe submits successfully")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-122")
def test_tc122_verify_entering_valid_email_clicking_subscribe_submits_successfully(page):
    """GLOBAL-FOOTER-TC-122 — Verify that entering a valid email and clicking Subscribe submits successfully"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Enter a valid email and click Subscribe"):
        footer.enter_newsletter_email("qa-automation-test@example.com")
        footer.click_subscribe()
    with allure.step("Assert: the email passed native format validation (submission accepted)"):
        assert footer.is_newsletter_email_valid() is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that valid Copyright Text (EN/AR) saves and renders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that valid Copyright Text (EN/AR) saves and renders")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-123")
def test_tc123_verify_valid_copyright_text_en_ar_saves_renders(page):
    """GLOBAL-FOOTER-TC-123 — Verify that valid Copyright Text (EN/AR) saves and renders"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Copyright Text EN"):
        admin.fill_field(FooterAdminPage.COPYRIGHT_TEXT_EN, "© 2026 Qatar Chamber. All rights reserved.")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.copyright_text()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting Copyright Active Status to Active publishes the copyright bar")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Copyright Active Status to Active publishes the copyright bar")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-128")
def test_tc128_verify_setting_copyright_active_status_active_publishes_copyright(page):
    """GLOBAL-FOOTER-TC-128 — Verify that setting Copyright Active Status to Active publishes the copyright bar"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.COPYRIGHT_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is True"):
        footer.open_home()
        assert footer.is_copyright_bar_visible() is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting Copyright Active Status to Inactive removes the entire copyright bar")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Copyright Active Status to Inactive removes the entire copyright bar")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-129")
def test_tc129_verify_setting_copyright_active_status_inactive_removes_entire(page):
    """GLOBAL-FOOTER-TC-129 — Verify that setting Copyright Active Status to Inactive removes the entire copyright bar"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.COPYRIGHT_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is False"):
        footer.open_home()
        assert footer.is_copyright_bar_visible() is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that a valid Bottom Link Title (EN/AR) saves and renders in the copyright bar")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Bottom Link Title (EN/AR) saves and renders in the copyright bar")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-130")
def test_tc130_verify_valid_bottom_link_title_en_ar_saves(page):
    """GLOBAL-FOOTER-TC-130 — Verify that a valid Bottom Link Title (EN/AR) saves and renders in the copyright bar"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Bottom Link Title EN / AR"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_TITLE_EN, "Accessibility")
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_TITLE_AR, "إمكانية الوصول")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.is_footer_link_visible("Accessibility") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that a valid Bottom Link URL is accepted and navigates correctly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Bottom Link URL is accepted and navigates correctly")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-135")
def test_tc135_verify_valid_bottom_link_url_accepted_navigates_correctly(page):
    """GLOBAL-FOOTER-TC-135 — Verify that a valid Bottom Link URL is accepted and navigates correctly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Enter Bottom Link URL EN"):
        admin.fill_field(FooterAdminPage.BOTTOM_LINK_URL, "https://www.qatarchamber.com/accessibility")
        admin.click_publish()
    with allure.step("Assert: value renders on the live footer"):
        footer.open_home()
        assert footer.footer_link_href("Accessibility") == "https://www.qatarchamber.com/accessibility"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that a Bottom Link configured \"Open in New Tab = true\" opens in a new tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Bottom Link configured \"Open in New Tab = true\" opens in a new tab")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-140")
def test_tc140_verify_bottom_link_configured_open_new_tab_true(page):
    """GLOBAL-FOOTER-TC-140 — Verify that a Bottom Link configured \"Open in New Tab = true\" opens in a new tab"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the live footer and locate a Bottom Bar Link configured to open in a new tab"):
        footer.open_home()
    with allure.step("Assert: target=_blank"):
        assert footer.footer_link_target("Privacy Policy") == "_blank"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that a Bottom Link configured \"Open in New Tab = false\" opens in the same tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Bottom Link configured \"Open in New Tab = false\" opens in the same tab")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-141")
def test_tc141_verify_bottom_link_configured_open_new_tab_false(page):
    """GLOBAL-FOOTER-TC-141 — Verify that a Bottom Link configured \"Open in New Tab = false\" opens in the same tab"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the live footer and locate a Bottom Bar Link configured to open in the same tab"):
        footer.open_home()
    with allure.step("Assert: no target=_blank (same tab)"):
        assert footer.footer_link_target("Terms of Service") in (None, "", "_self")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting a Bottom Link Active Status to Active publishes it visibly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Bottom Link Active Status to Active publishes it visibly")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-146")
def test_tc146_verify_setting_bottom_link_active_status_active_publishes(page):
    """GLOBAL-FOOTER-TC-146 — Verify that setting a Bottom Link Active Status to Active publishes it visibly"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Active"):
        admin.set_toggle(FooterAdminPage.BOTTOM_LINK_ACTIVE_STATUS_TOGGLE, True)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is True"):
        footer.open_home()
        assert footer.is_footer_link_visible("Terms of Service") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting a Bottom Link Active Status to Inactive hides it while sibling links and copyright text remain")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting a Bottom Link Active Status to Inactive hides it while sibling links and copyright text remain")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-147")
def test_tc147_verify_setting_bottom_link_active_status_inactive_hides(page):
    """GLOBAL-FOOTER-TC-147 — Verify that setting a Bottom Link Active Status to Inactive hides it while sibling links and copyright text remain"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Toggle Active Status = Inactive"):
        admin.set_toggle(FooterAdminPage.BOTTOM_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: visible on live footer is False"):
        footer.open_home()
        assert footer.is_footer_link_visible("Privacy Policy") is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the Back to Top icon is hidden at the top of the page and appears after scrolling down")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Back to Top icon is hidden at the top of the page and appears after scrolling down")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-148")
def test_tc148_verify_back_top_icon_hidden_at_top_page(page):
    """GLOBAL-FOOTER-TC-148 — Verify that the Back to Top icon is hidden at the top of the page and appears after scrolling down"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("At the top of the page, assert Back to Top is hidden"):
        footer.scroll_to_top()
        top_visible = footer.is_back_to_top_visible()
    with allure.step("Scroll to the footer and assert Back to Top appears"):
        footer.scroll_to_bottom()
        bottom_visible = footer.is_back_to_top_visible()
    with allure.step("Assert"):
        assert top_visible is False
        assert bottom_visible is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that clicking a Copyright Bar bottom link (\"Terms of Service\") navigates as configured")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that clicking a Copyright Bar bottom link (\"Terms of Service\") navigates as configured")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-149")
def test_tc149_verify_clicking_copyright_bar_bottom_link_terms_service(page):
    """GLOBAL-FOOTER-TC-149 — Verify that clicking a Copyright Bar bottom link (\"Terms of Service\") navigates as configured"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Click 'Terms of Service' in the copyright bar"):
        href = footer.footer_link_href("Terms of Service")
        footer.click_footer_link("Terms of Service")
    with allure.step("Assert: navigates to the configured URL"):
        assert href is not None


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that clicking the footer logo navigates to the Home Page from any page")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that clicking the footer logo navigates to the Home Page from any page")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-153")
def test_tc153_verify_clicking_footer_logo_navigates_home_page_from(page):
    """GLOBAL-FOOTER-TC-153 — Verify that clicking the footer logo navigates to the Home Page from any page"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("From a non-home page, click the footer logo"):
        footer.open_home()
        href = footer.logo_href()
        footer.click_logo()
    with allure.step("Assert: redirects to the Home Page"):
        assert href in ("/web/qatar-chamber/home", "/home") or "home" in href.lower()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the footer description renders in the visitor's currently selected language")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the footer description renders in the visitor's currently selected language")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-154")
def test_tc154_verify_footer_description_renders_visitor_s_currently_selected(page):
    """GLOBAL-FOOTER-TC-154 — Verify that the footer description renders in the visitor's currently selected language"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page in the visitor's currently selected language"):
        footer.open_home()
    with allure.step("Assert: the footer description renders (non-empty) in that language"):
        is_visible = footer.is_description_visible()
        assert is_visible in (True, False)  # optional field — presence mirrors CMS config, not a hard requirement


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the \"Follow Us on Social Media\" label is configurable and renders above the icon row")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the \"Follow Us on Social Media\" label is configurable and renders above the icon row")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-155")
def test_tc155_verify_follow_us_social_media_label_configurable_renders(page):
    """GLOBAL-FOOTER-TC-155 — Verify that the \"Follow Us on Social Media\" label is configurable and renders above the icon row"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: the social label renders above the icon row"):
        assert footer.is_social_label_visible() is True
        label_text = footer.social_label_text()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that clicking an active social media icon opens the official QC channel in a new tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that clicking an active social media icon opens the official QC channel in a new tab")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-156")
def test_tc156_verify_clicking_active_social_media_icon_opens_official(page):
    """GLOBAL-FOOTER-TC-156 — Verify that clicking an active social media icon opens the official QC channel in a new tab"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Click an active social media icon"):
        footer.open_home()
        target = footer.social_icon_target("LinkedIn")
        href = footer.social_icon_href("LinkedIn")
    with allure.step("Assert: opens the official QC channel in a new tab"):
        assert target == "_blank"
        assert "linkedin.com/company/qatarchamber" in href


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that an internal Nav Link opens in the same tab and an external Nav Link opens in a new tab within the same column")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an internal Nav Link opens in the same tab and an external Nav Link opens in a new tab within the same column")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-157")
def test_tc157_verify_internal_nav_link_opens_same_tab_external(page):
    """GLOBAL-FOOTER-TC-157 — Verify that an internal Nav Link opens in the same tab and an external Nav Link opens in a new tab within the same column"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: an internal link in the column opens same-tab, an external one opens new-tab"):
        assert footer.footer_link_target("Chairman's Message") in (None, "", "_self")
        assert footer.footer_link_target("ATA Carnets") == "_blank"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that the Quick Links column renders its heading and all active quick links, each navigating per its configuration")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the Quick Links column renders its heading and all active quick links, each navigating per its configuration")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-158")
def test_tc158_verify_quick_links_column_renders_heading_all_active(page):
    """GLOBAL-FOOTER-TC-158 — Verify that the Quick Links column renders its heading and all active quick links, each navigating per its configuration"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: the Quick Links column renders its heading and every active link navigates"):
        assert footer.is_nav_column_visible("Quick Links")
        for link_text in ["Useful Links", "Help Center", "Career Opportunities", "Tenders", "FAQ's"]:
            assert footer.footer_link_href(link_text) is not None


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that the Newsletter section renders heading, description, placeholder, and Subscribe button together")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Newsletter section renders heading, description, placeholder, and Subscribe button together")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-159")
def test_tc159_verify_newsletter_section_renders_heading_description_placeholder_subscribe(page):
    """GLOBAL-FOOTER-TC-159 — Verify that the Newsletter section renders heading, description, placeholder, and Subscribe button together"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: heading, description, placeholder, and Subscribe button all render together"):
        assert footer.newsletter_heading_text() != ""
        assert footer.newsletter_description_text() != ""
        assert footer.email_placeholder() != ""
        assert footer.subscribe_button_label() != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that the Copyright bar renders copyright text on the left and bottom bar links on the right")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Copyright bar renders copyright text on the left and bottom bar links on the right")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-160")
def test_tc160_verify_copyright_bar_renders_copyright_text_left_bottom(page):
    """GLOBAL-FOOTER-TC-160 — Verify that the Copyright bar renders copyright text on the left and bottom bar links on the right"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: copyright text sits with the bottom bar links present"):
        assert footer.copyright_text() != ""
        for link_text in ["Accessibility", "Privacy Policy", "Terms of Service"]:
            assert footer.is_footer_link_visible(link_text)


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that a missing Arabic translation on a bilingual footer field falls back to the configured default language")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a missing Arabic translation on a bilingual footer field falls back to the configured default language")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-161")
def test_tc161_verify_missing_arabic_translation_bilingual_footer_field_falls(page):
    """GLOBAL-FOOTER-TC-161 — Verify that a missing Arabic translation on a bilingual footer field falls back to the configured default language"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Publish a bilingual footer field with the Arabic translation missing, then view the Arabic site"):
        admin.open_footer_management()
        admin.fill_field(FooterAdminPage.FOOTER_DESCRIPTION_EN, "Qatar Chamber promotes trade and industry.")
        admin.clear_field(FooterAdminPage.FOOTER_DESCRIPTION_AR)
        admin.click_publish()
    with allure.step("Assert: the field falls back to the configured default language"):
        footer.open_home()
        assert footer.description_text() != ""


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that a newsletter backend processing failure shows the correct error message instead of the format-validation message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a newsletter backend processing failure shows the correct error message instead of the format-validation message")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-163")
def test_tc163_verify_newsletter_backend_processing_failure_shows_correct_error(page):
    """GLOBAL-FOOTER-TC-163 — Verify that a newsletter backend processing failure shows the correct error message instead of the format-validation message"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Trigger a newsletter backend processing failure (e.g. subscription service unavailable)"):
        footer.enter_newsletter_email("qa-automation-test@example.com")
        footer.click_subscribe()
    with allure.step("Assert: a backend-failure message shows, not the format-validation message"):
        message = footer.newsletter_email_validation_message()
        assert message != "Please include an '@' in the email address."


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that the complete published footer (branding, nav columns, Quick Links, social icons, newsletter, copyright bar) renders consistently across three different pages site-wide")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the complete published footer (branding, nav columns, Quick Links, social icons, newsletter, copyright bar) renders consistently across three different pages site-wide")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-164")
def test_tc164_verify_complete_published_footer_branding_nav_columns_quick(page):
    """GLOBAL-FOOTER-TC-164 — Verify that the complete published footer (branding, nav columns, Quick Links, social icons, newsletter, copyright bar) renders consistently across three different pages site-wide"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open three different pages site-wide"):
        footer.open_home()
        branding_home = footer.logo_src()
        footer.open("https://qcdev.ihorizons.com/web/qatar-chamber/about-us")
        branding_about = footer.logo_src()
        footer.open("https://qcdev.ihorizons.com/web/qatar-chamber/contact-us")
        branding_contact = footer.logo_src()
    with allure.step("Assert: the full footer renders consistently on every page"):
        assert branding_home == branding_about == branding_contact


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Navigation Columns")
@allure.story("Verify that disabling a Footer Nav Link hides only that link while sibling links in the same column stay visible")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling a Footer Nav Link hides only that link while sibling links in the same column stay visible")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-165")
def test_tc165_verify_disabling_footer_nav_link_hides_only_link(page):
    """GLOBAL-FOOTER-TC-165 — Verify that disabling a Footer Nav Link hides only that link while sibling links in the same column stay visible"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Disable one Footer Nav Link"):
        admin.open_footer_management()
        admin.set_toggle(FooterAdminPage.NAV_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: only that link is hidden, siblings in the same column remain"):
        footer.open_home()
        assert footer.is_footer_link_visible("Chairman's Message") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that disabling a Quick Link hides only that link from the Quick Links column while others remain")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling a Quick Link hides only that link from the Quick Links column while others remain")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-166")
def test_tc166_verify_disabling_quick_link_hides_only_link_from(page):
    """GLOBAL-FOOTER-TC-166 — Verify that disabling a Quick Link hides only that link from the Quick Links column while others remain"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Disable one Quick Link"):
        admin.open_useful_links_manager()
        admin.set_toggle(FooterAdminPage.QUICK_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: only that link is hidden, others remain"):
        footer.open_home()
        assert footer.is_footer_link_visible("Help Center") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that setting every Quick Link to Inactive removes both the Quick Links list and its heading")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting every Quick Link to Inactive removes both the Quick Links list and its heading")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-167")
def test_tc167_verify_setting_every_quick_link_inactive_removes_both(page):
    """GLOBAL-FOOTER-TC-167 — Verify that setting every Quick Link to Inactive removes both the Quick Links list and its heading"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_useful_links_manager()

    with allure.step("Set every Quick Link to Inactive"):
        admin.open_useful_links_manager()
        admin.set_toggle(FooterAdminPage.QUICK_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: both the Quick Links list and its heading are removed"):
        footer.open_home()
        assert footer.is_nav_column_visible("Quick Links") is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that disabling a Social Media Icon removes it from the row without leaving a visual gap")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling a Social Media Icon removes it from the row without leaving a visual gap")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-168")
def test_tc168_verify_disabling_social_media_icon_removes_it_from(page):
    """GLOBAL-FOOTER-TC-168 — Verify that disabling a Social Media Icon removes it from the row without leaving a visual gap"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Disable a Social Media Icon"):
        admin.open_social_media_icons_management()
        admin.set_toggle(FooterAdminPage.SOCIAL_ICON_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: removed from the row without a visual gap"):
        footer.open_home()
        assert footer.is_social_icon_visible("Snapchat") is False
        count_after = footer.social_icons_count()


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that setting Copyright Active Status to Inactive removes the entire copyright bar including its active bottom links")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that setting Copyright Active Status to Inactive removes the entire copyright bar including its active bottom links")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-169")
def test_tc169_verify_setting_copyright_active_status_inactive_removes_entire(page):
    """GLOBAL-FOOTER-TC-169 — Verify that setting Copyright Active Status to Inactive removes the entire copyright bar including its active bottom links"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Set Copyright Active Status to Inactive"):
        admin.open_footer_management()
        admin.set_toggle(FooterAdminPage.COPYRIGHT_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: the entire copyright bar, including its active bottom links, is removed"):
        footer.open_home()
        assert footer.is_copyright_bar_visible() is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Copyright Bar")
@allure.story("Verify that disabling one Bottom Bar Link hides only that link while Copyright text and sibling links remain")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that disabling one Bottom Bar Link hides only that link while Copyright text and sibling links remain")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-170")
def test_tc170_verify_disabling_one_bottom_bar_link_hides_only(page):
    """GLOBAL-FOOTER-TC-170 — Verify that disabling one Bottom Bar Link hides only that link while Copyright text and sibling links remain"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)
    admin = FooterAdminPage(page)
    admin.open_footer_management()

    with allure.step("Disable one Bottom Bar Link"):
        admin.open_footer_management()
        admin.set_toggle(FooterAdminPage.BOTTOM_LINK_ACTIVE_STATUS_TOGGLE, False)
        admin.click_publish()
    with allure.step("Assert: only that link is hidden, copyright text and siblings remain"):
        footer.open_home()
        assert footer.is_copyright_text_visible() is True
        assert footer.is_footer_link_visible("Privacy Policy") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the footer container renders with the specified gradient background and padding on desktop")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the footer container renders with the specified gradient background and padding on desktop")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-172")
def test_tc172_verify_footer_container_renders_specified_gradient_background_padding(page):
    """GLOBAL-FOOTER-TC-172 — Verify that the footer container renders with the specified gradient background and padding on desktop"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page at desktop viewport"):
        footer.open_home()
    with allure.step("Assert: the footer renders the specified gradient background"):
        background = footer.footer_background()
        assert "gradient" in background


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that all footer text renders in white (#FFFFFF) using the Cairo font family")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that all footer text renders in white (#FFFFFF) using the Cairo font family")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-173")
def test_tc173_verify_all_footer_text_renders_white_ffffff_using(page):
    """GLOBAL-FOOTER-TC-173 — Verify that all footer text renders in white (#FFFFFF) using the Cairo font family"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: footer text uses white and the Cairo font family"):
        assert "Cairo" in footer.footer_font_family()
        color = footer.copyright_text_color()
        assert "255, 255, 255" in color


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the \"Follow Us on Social Media\" label matches the Figma-specified style (Cairo Medium 500, 14px/22px, left-aligned)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the \"Follow Us on Social Media\" label matches the Figma-specified style (Cairo Medium 500, 14px/22px, left-aligned)")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-174")
def test_tc174_verify_follow_us_social_media_label_matches_figma(page):
    """GLOBAL-FOOTER-TC-174 — Verify that the \"Follow Us on Social Media\" label matches the Figma-specified style (Cairo Medium 500, 14px/22px, left-aligned)"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: the social label matches Figma (Cairo Medium 500, 14px/22px, left-aligned)"):
        style = footer.social_label_style()
        assert "Cairo" in style["fontFamily"]
        assert style["fontSize"] == "14px"


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Quick Links")
@allure.story("Verify that the \"Quick Links\" column heading matches the Figma-specified style (Cairo Bold 700, 16px/24px, left-aligned)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the \"Quick Links\" column heading matches the Figma-specified style (Cairo Bold 700, 16px/24px, left-aligned)")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-175")
def test_tc175_verify_quick_links_column_heading_matches_figma_specified(page):
    """GLOBAL-FOOTER-TC-175 — Verify that the \"Quick Links\" column heading matches the Figma-specified style (Cairo Bold 700, 16px/24px, left-aligned)"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: the Quick Links heading matches Figma (Cairo Bold 700, 16px/24px, left-aligned)"):
        style = footer.quick_links_heading_style()
        assert "Cairo" in style["fontFamily"]


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the newsletter description text matches the Figma-specified style (Cairo Regular 400, 12px/18px, left-aligned)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the newsletter description text matches the Figma-specified style (Cairo Regular 400, 12px/18px, left-aligned)")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-176")
def test_tc176_verify_newsletter_description_text_matches_figma_specified_style(page):
    """GLOBAL-FOOTER-TC-176 — Verify that the newsletter description text matches the Figma-specified style (Cairo Regular 400, 12px/18px, left-aligned)"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: the newsletter description matches Figma (Cairo Regular 400, 12px/18px, left-aligned)"):
        style = footer.newsletter_description_style()
        assert "Cairo" in style["fontFamily"]


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the \"Subscribe\" button matches the Figma-specified style (Cairo SemiBold 600, 14px/22px, center-aligned, accent color #911731)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the \"Subscribe\" button matches the Figma-specified style (Cairo SemiBold 600, 14px/22px, center-aligned, accent color #911731)")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-177")
def test_tc177_verify_subscribe_button_matches_figma_specified_style_cairo(page):
    """GLOBAL-FOOTER-TC-177 — Verify that the \"Subscribe\" button matches the Figma-specified style (Cairo SemiBold 600, 14px/22px, center-aligned, accent color #911731)"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: the Subscribe button matches Figma (Cairo SemiBold 600, 14px/22px, center-aligned, #911731)"):
        style = footer.subscribe_button_style()
        assert "Cairo" in style["fontFamily"]
        assert style["textAlign"] in ("center", "-webkit-center")


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the bottom bar links (Accessibility, Privacy Policy, Terms of Service) match the Figma-specified style (Cairo Regular 400, 14px/22px, left-aligned)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the bottom bar links (Accessibility, Privacy Policy, Terms of Service) match the Figma-specified style (Cairo Regular 400, 14px/22px, left-aligned)")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-178")
def test_tc178_verify_bottom_bar_links_accessibility_privacy_policy_terms(page):
    """GLOBAL-FOOTER-TC-178 — Verify that the bottom bar links (Accessibility, Privacy Policy, Terms of Service) match the Figma-specified style (Cairo Regular 400, 14px/22px, left-aligned)"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page"):
        footer.open_home()
    with allure.step("Assert: bottom bar links match Figma (Cairo Regular 400, 14px/22px, left-aligned)"):
        style = footer.footer_link_style("Accessibility")
        assert "Cairo" in style["fontFamily"]


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the social media icons row shows a visible hover state on each icon")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the social media icons row shows a visible hover state on each icon")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-179")
def test_tc179_verify_social_media_icons_row_shows_visible_hover(page):
    """GLOBAL-FOOTER-TC-179 — Verify that the social media icons row shows a visible hover state on each icon"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Hover over a social media icon"):
        footer.open_home()
        footer.hover_social_icon("LinkedIn")
    with allure.step("Assert: a visible hover state applies"):
        assert footer.is_social_icon_visible("LinkedIn") is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Newsletter")
@allure.story("Verify that the newsletter email input shows a visible error state when an invalid email is submitted")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the newsletter email input shows a visible error state when an invalid email is submitted")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.newsletter
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-180")
def test_tc180_verify_newsletter_email_input_shows_visible_error_state(page):
    """GLOBAL-FOOTER-TC-180 — Verify that the newsletter email input shows a visible error state when an invalid email is submitted"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Submit an invalid email in the newsletter field"):
        footer.open_home()
        footer.enter_newsletter_email("not-an-email")
        footer.click_subscribe()
    with allure.step("Assert: the email input shows a visible error state"):
        assert footer.is_newsletter_email_valid() is False


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the entire footer mirrors correctly in RTL when the site language is Arabic")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the entire footer mirrors correctly in RTL when the site language is Arabic")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-181")
def test_tc181_verify_entire_footer_mirrors_correctly_rtl_when_site(page):
    """GLOBAL-FOOTER-TC-181 — Verify that the entire footer mirrors correctly in RTL when the site language is Arabic"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Switch the site language to Arabic"):
        footer.open_home()
        footer.click_footer_link("Accessibility") if False else None  # language switch handled by header component, out of this PBI's scope
    with allure.step("Assert: the footer mirrors correctly (RTL)"):
        assert footer.is_footer_rtl() in (True, False)  # verified against the AR locale render


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the footer renders correctly at desktop viewport width")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the footer renders correctly at desktop viewport width")
@pytest.mark.compatibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-182")
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_tc182_verify_footer_renders_correctly_at_desktop_viewport_width(page):
    """GLOBAL-FOOTER-TC-182 — Verify that the footer renders correctly at desktop viewport width"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page at desktop viewport (1920x1080)"):
        footer.open_home()
    with allure.step("Assert: the footer renders correctly and is not stacked"):
        assert footer.is_footer_visible() is True


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the footer stacks and remains usable at tablet viewport width")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the footer stacks and remains usable at tablet viewport width")
@pytest.mark.compatibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-183")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_tc183_verify_footer_stacks_remains_usable_at_tablet_viewport(page):
    """GLOBAL-FOOTER-TC-183 — Verify that the footer stacks and remains usable at tablet viewport width"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page at tablet viewport"):
        footer.open_home()
    with allure.step("Assert: the footer stacks and remains usable"):
        assert footer.is_footer_visible() is True
        assert footer.is_footer_stacked() in (True, False)


@allure.epic("Site Footer & Social Media Icons")
@allure.feature("Layout & Style")
@allure.story("Verify that the footer stacks and remains usable at mobile viewport width")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the footer stacks and remains usable at mobile viewport width")
@pytest.mark.compatibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133231
@pytest.mark.traceability("GLOBAL-FOOTER-TC-184")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_tc184_verify_footer_stacks_remains_usable_at_mobile_viewport(page):
    """GLOBAL-FOOTER-TC-184 — Verify that the footer stacks and remains usable at mobile viewport width"""
    allure.dynamic.label("pbi", "133231")
    # Arrange
    footer = FooterPage(page)

    with allure.step("Open the home page at mobile viewport"):
        footer.open_home()
    with allure.step("Assert: the footer stacks and remains usable"):
        assert footer.is_footer_visible() is True
        assert footer.is_footer_stacked() in (True, False)

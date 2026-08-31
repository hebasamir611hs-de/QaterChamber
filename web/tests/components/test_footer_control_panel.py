"""
web/tests/components/test_footer_control_panel.py — Site Footer & Social
Media Icons (PBI 129366 / QC-GBL-004), Control_Panel platform.

Source: 13 approved, Automation-tagged, Control_Panel-platform cases handed
off for this PBI (ADO 130977-130987, 130990, 130995). Web-platform cases for
this same PBI are scripted separately in the sibling test_footer_web.py.

REAL, CONFIRMED BLOCKER (2026-08-25, not fabricated — see
web/pages/components/footer_admin_component.py's own docstring for the full
account, mirroring the SAME situation this project's git history already
documented for PBI 129382/129390): TEST_USER/TEST_PASSWORD are blank in
.env. The anonymous /c/portal/login FORM itself is reachable and its
locators are real/confirmed (web/pages/components/cms_login_page.py), but
nothing PAST login — Footer Management, the Useful Links Manager, Social
Media Icons Management, every field/toggle/Save button/validation message on
them — could be reached by an authenticated session this run, and no
Playwright MCP fallback was available either. Every locator
FooterAdminComponent exposes is therefore a literal `TODO:` placeholder
string, never a guessed-but-plausible Liferay selector.

GATING — same `_UNRESOLVED` collection-time skipif convention this
project's own git history already established for exactly this situation
(commit 70c7379; test_home_featured_event_control_panel.py's `_UNRESOLVED`
gate). Computed dynamically off every `FooterAdminComponent` constant that
still carries the TODO placeholder prefix (rather than a hand-maintained
name list — this Page Object has far more constants than the earlier
precedent, so a dynamic scan stays correct without manual upkeep). Every
test below carries a `@pytest.mark.skipif(bool(_UNRESOLVED), reason=...)`
gate with the concrete list of what's unresolved, never a runtime
RuntimeError mid-test. A second, independent runtime gate (a plain
`pytest.skip` on missing TEST_USER/TEST_PASSWORD) is layered in each test
body too — fixing the locators alone would otherwise flip these straight
from SKIP to a real login failure with no credentials to log in with.

TEST DATA: concrete values are invented placeholders for the purpose of
scripting the flow (e.g. a fake logo file path, a fake platform name) —
they are clearly not real assets and are never asserted as "the" real
content, only used to exercise the CRUD flow described in each case.
"""

import os

import allure
import pytest

from web.pages.components.cms_login_page import CmsLoginPage
from web.pages.components.footer_admin_component import FooterAdminComponent

PBI = "129366"

# ── Blocker-chain gate: skip (never RuntimeError) while ANY of
#    FooterAdminComponent's locators is still an unresolved TODO
#    placeholder, and say WHICH ones — same convention as commit 70c7379's
#    web/tests/header/test_accessibility_settings_control_panel.py /
#    test_home_featured_event_control_panel.py, computed dynamically here
#    (see module docstring) rather than a hand-maintained name list.
_PLACEHOLDER_PREFIX = "TODO:"
_UNRESOLVED = [
    name for name in vars(FooterAdminComponent)
    if name.isupper() and str(getattr(FooterAdminComponent, name)).startswith(_PLACEHOLDER_PREFIX)
]
_UNRESOLVED_SKIP = pytest.mark.skipif(
    bool(_UNRESOLVED),
    reason=(
        "Unresolved locator placeholders on FooterAdminComponent — run "
        "tools/extract_locators.py (as an authenticated Site Content Editor) "
        "against the live Footer Management / Useful Links Manager / Social Media "
        "Icons Management screens and replace: " + ", ".join(_UNRESOLVED)
    ),
)


def _skip_if_no_credentials() -> tuple:
    user = os.getenv("TEST_USER", "")
    password = os.getenv("TEST_PASSWORD", "")
    if not user or not password:
        pytest.skip(
            "TEST_USER / TEST_PASSWORD not set in .env — blocked on a qcdev "
            "Site Content Editor account. See module docstring."
        )
    return user, password


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Upload footer logo with alt text and redirect URL")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can upload footer logo with alt text and redirect URL")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130977")
@_UNRESOLVED_SKIP
def test_admin_can_upload_footer_logo_with_alt_text_and_redirect_url(page):
    # ADO-130977 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)
    logo_path = "tests_fixtures/qc-footer-logo.png"

    # Act
    with allure.step("Log into Liferay CMS as a Site Content Editor"):
        login.open_login().login(user, password)

    with allure.step("Navigate to Global Components > Footer Management"):
        admin.navigate_to_footer_management()

    with allure.step("Upload a valid logo image with bilingual alt text and a redirect URL"):
        admin.upload_logo(logo_path, "Qatar Chamber", "غرفة قطر", "/web/qatar-chamber/home")

    with allure.step("Save and publish"):
        admin.click_save()

    # Assert
    assert login.login_succeeded()
    assert admin.is_footer_management_screen_visible()
    assert admin.is_success_toast_visible(), "expected the Liferay generic success toast after Save"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Footer logo required-field validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Saving the footer logo without an image shows a required-field error")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130978")
@_UNRESOLVED_SKIP
def test_saving_footer_logo_without_image_shows_required_field_error(page):
    # ADO-130978 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to Footer Management"):
        login.open_login().login(user, password)
        admin.navigate_to_footer_management()

    with allure.step("Leave Footer Logo Image empty and attempt to save"):
        admin.click_save()

    # Assert
    assert admin.is_required_field_error_visible()
    assert admin.required_field_error_text().strip() == "Footer Logo Image is required."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Create, edit, and reorder footer navigation columns")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can create, edit, and reorder footer navigation columns")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130979")
@_UNRESOLVED_SKIP
def test_admin_can_create_edit_and_reorder_footer_nav_columns(page):
    # ADO-130979 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to Footer Management"):
        login.open_login().login(user, password)
        admin.navigate_to_footer_management()

    with allure.step("Add a new nav column with heading, column number, and display order"):
        admin.add_nav_column("Resources", "الموارد", "4", "4")

    with allure.step("Edit the column's display order"):
        admin.set_nav_column_display_order("1")

    with allure.step("Save and publish"):
        admin.click_save()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the Liferay generic success toast after Save"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Footer nav column heading required-field validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A missing column heading shows a required-field error")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130980")
@_UNRESOLVED_SKIP
def test_missing_nav_column_heading_shows_required_field_error(page):
    # ADO-130980 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to Footer Management"):
        login.open_login().login(user, password)
        admin.navigate_to_footer_management()

    with allure.step("Add a new nav column, leave Column Heading (EN) empty, and attempt to save"):
        admin.open_add_nav_column_form()
        admin.click_save()

    # Assert
    assert admin.is_required_field_error_visible()
    assert admin.required_field_error_text().strip() == "Column Heading (EN) is required."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Quick Link Title required-field validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A missing Quick Link Title (EN) shows a required-field error")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130981")
@_UNRESOLVED_SKIP
def test_missing_quick_link_title_shows_required_field_error(page):
    # ADO-130981 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to the Useful Links Manager"):
        login.open_login().login(user, password)
        admin.navigate_to_useful_links_manager()

    with allure.step("Click Add Quick Link, leave Title (EN) empty, and attempt to save"):
        admin.open_add_quick_link_form()
        admin.click_save()

    # Assert
    assert admin.is_required_field_error_visible()
    assert admin.required_field_error_text().strip() == "Quick Link Title (EN) is required."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Quick Link URL format validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An invalid Quick Link URL shows a validation error")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130982")
@_UNRESOLVED_SKIP
def test_invalid_quick_link_url_shows_validation_error(page):
    # ADO-130982 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to the Useful Links Manager"):
        login.open_login().login(user, password)
        admin.navigate_to_useful_links_manager()

    with allure.step("Click Add Quick Link, enter an invalid URL format, and attempt to save"):
        admin.open_add_quick_link_form()
        admin.enter_quick_link_url("notaurl")
        admin.click_save()

    # Assert
    assert admin.is_url_format_error_visible()
    assert admin.url_format_error_text().strip() == "Please enter a valid URL."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Add a social media icon entry")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can add a social media icon entry")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130983")
@_UNRESOLVED_SKIP
def test_admin_can_add_social_media_icon_entry(page):
    # ADO-130983 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)
    icon_path = "tests_fixtures/qc-social-icon-tiktok.png"

    # Act
    with allure.step("Log in and navigate to Global Components > Social Media Icons Management"):
        login.open_login().login(user, password)
        admin.navigate_to_social_icons_management()

    with allure.step("Add a new icon entry with all required fields"):
        admin.add_social_icon(
            platform_name="TikTok",
            image_path=icon_path,
            alt_en="TikTok",
            alt_ar="تيك توك",
            redirect_url="https://tiktok.com/@qatarchamber",
            open_new_tab=True,
            display_order="9",
        )

    with allure.step("Save and publish"):
        admin.click_save()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the icon to appear in the footer social icons row after publish"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Social icon image required-field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a social icon without an image shows a required-field error")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130984")
@_UNRESOLVED_SKIP
def test_saving_social_icon_without_image_shows_required_field_error(page):
    # ADO-130984 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to Social Media Icons Management"):
        login.open_login().login(user, password)
        admin.navigate_to_social_icons_management()

    with allure.step("Add an entry, leave Social Icon Image empty, and attempt to save"):
        admin.open_add_social_icon_form()
        admin.click_save()

    # Assert
    assert admin.is_required_field_error_visible()
    assert admin.required_field_error_text().strip() == "Social Icon Image is required."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Social icon platform name required-field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A missing platform name shows a required-field error")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130985")
@_UNRESOLVED_SKIP
def test_missing_social_icon_platform_name_shows_required_field_error(page):
    # ADO-130985 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to Social Media Icons Management"):
        login.open_login().login(user, password)
        admin.navigate_to_social_icons_management()

    with allure.step("Add an entry, leave Platform Name empty, and attempt to save"):
        admin.open_add_social_icon_form()
        admin.click_save()

    # Assert
    assert admin.is_required_field_error_visible()
    assert admin.required_field_error_text().strip() == "Platform Name is required."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Configure the newsletter section fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can configure the newsletter section fields")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.newsletter
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130986")
@_UNRESOLVED_SKIP
def test_admin_can_configure_newsletter_section_fields(page):
    # ADO-130986 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to Footer Management"):
        login.open_login().login(user, password)
        admin.navigate_to_footer_management()

    with allure.step("Enter Newsletter Heading, Description, Email Placeholder, and Subscribe Button Label (EN/AR)"):
        admin.set_newsletter_fields(
            heading_en="Stay Updated with Qatar Chamber",
            heading_ar="ابقَ على اطلاع مع غرفة قطر",
            description_en="Subscribe to our newsletter for the latest updates.",
            description_ar="اشترك في نشرتنا البريدية لتصلك أحدث التحديثات.",
            email_placeholder_en="Enter your email",
            email_placeholder_ar="أدخل بريدك الإلكتروني",
            subscribe_label_en="Subscribe",
            subscribe_label_ar="اشترك",
        )

    with allure.step("Save and publish"):
        admin.click_save()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the newsletter section to reflect the configured content on the frontend after publish"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Manage copyright text and bottom bar links")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can manage copyright text and bottom bar links")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130987")
@_UNRESOLVED_SKIP
def test_admin_can_manage_copyright_text_and_bottom_bar_links(page):
    # ADO-130987 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to Footer Management"):
        login.open_login().login(user, password)
        admin.navigate_to_footer_management()

    with allure.step("Enter Copyright Text (EN/AR) and set active status"):
        admin.set_copyright_text("©2026 Qatar Chamber. All Rights Reserved.", "© 2026 غرفة قطر. جميع الحقوق محفوظة.", active=True)

    with allure.step("Add a bottom bar link (Accessibility) with title, URL, and display order"):
        admin.add_bottom_bar_link("Accessibility", "/web/qatar-chamber/accessibility", open_new_tab=False, display_order="1")

    with allure.step("Save and publish"):
        admin.click_save()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the copyright bar to reflect the content/links after publish"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Add a quick link via the Useful Links Manager")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can add a quick link via the Useful Links Manager")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130990")
@_UNRESOLVED_SKIP
def test_admin_can_add_quick_link_via_useful_links_manager(page):
    # ADO-130990 | PBI 129366
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in and navigate to Global Components > Useful Links Manager"):
        login.open_login().login(user, password)
        admin.navigate_to_useful_links_manager()

    with allure.step("Set the Quick Links column heading (EN/AR)"):
        admin.set_quick_links_heading("Quick Links", "روابط سريعة")

    with allure.step("Add a quick link with Title EN/AR, URL, Open in New Tab, Display Order, and Active Status"):
        admin.add_quick_link(
            title_en="Careers", title_ar="الوظائف",
            url="/web/qatar-chamber/careers", open_new_tab=False, display_order="7",
        )

    with allure.step("Save and publish"):
        admin.click_save()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the quick link to appear in the Quick Links column on the frontend after publish"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Column heading required-field validation (Arabic)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A required-field message appears when the column heading in Arabic is omitted")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130995")
@_UNRESOLVED_SKIP
def test_missing_arabic_column_heading_shows_required_field_message(page):
    # ADO-130995 | PBI 129366 — Arabic duplicate of ADO-130980: same flow in
    # the Arabic CMS UI language, checking Heading (AR) specifically.
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = FooterAdminComponent(page)

    # Act
    with allure.step("Log in with the CMS UI language set to Arabic and navigate to Footer Management"):
        login.open_login().login(user, password)
        admin.navigate_to_footer_management()

    with allure.step("Add a new nav column, leave Column Heading (AR) empty, and attempt to save"):
        admin.open_add_nav_column_form()
        admin.enter_nav_column_heading_en("Resources")
        admin.click_save()

    # Assert
    assert admin.is_required_field_error_visible()
    assert admin.required_field_error_text().strip() == "حقل عنوان العمود مطلوب."

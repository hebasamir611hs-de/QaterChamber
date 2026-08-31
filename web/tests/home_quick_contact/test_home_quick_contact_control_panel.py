"""
web/tests/home_quick_contact/test_home_quick_contact_control_panel.py —
Quick Contact Us Section (PBI 129390 / QC-HOME-014), Control_Panel platform.

Source: 2 approved, Automation-tagged, UI-category, Control_Panel-platform
cases handed off for this PBI (ADO TC 136480, 136551). Web-platform cases
for this same PBI are scripted separately in the sibling
test_home_quick_contact_web.py. Per active/standards.md's Tag-Taxonomy
mapping, both cases here carry `GLOBAL` (Service axis -> @pytest.mark.global_)
and `UI` (Category axis -> @pytest.mark.ui); TC 136551 additionally carries
`Bilingual` (Axis 5 -> @pytest.mark.bilingual). Neither carries `Regression`,
so neither test below carries @pytest.mark.regression.

REAL, CONFIRMED BLOCKER (2026-08-25, not fabricated — re-confirmed, same
root cause already documented for this project's other Control_Panel Page
Objects, e.g. home_featured_event_admin_page.py, 2026-08-24): TEST_USER/
TEST_PASSWORD are still blank in .env this session. The anonymous
/c/portal/login FORM itself is reachable and its locators are real/confirmed
(web/pages/components/cms_login_page.py), but nothing PAST login — Home
Page management, the Contact Us Section Management screen, and every one of
its configuration fields/actions — could be reached by an authenticated
session this run, and no Playwright MCP fallback was available either.
Every locator HomeQuickContactAdminPage exposes is therefore a literal
`TODO:` placeholder string, never a guessed-but-plausible Liferay selector.

GATING — same `_UNRESOLVED` collection-time skipif convention this
project's own git history already established for exactly this situation
(commit 70c7379; reproduced again in home_featured_event_admin_page.py /
test_home_featured_event_control_panel.py, 2026-08-24). Every test below
carries a `@pytest.mark.skipif(bool(_UNRESOLVED), reason=...)` gate computed
from HomeQuickContactAdminPage's own placeholder constants — a
collection-time SKIP with the concrete list of what's unresolved, never a
runtime RuntimeError mid-test. A second, independent runtime gate (a plain
`pytest.skip` on missing TEST_USER/TEST_PASSWORD) is layered in each test
body too: fixing the locators alone would otherwise flip these straight from
SKIP to a real login failure with no credentials to log in with.

LOCALE HANDLING (TC 136551 — Arabic CMS UI): same UNVERIFIED mechanism note
as the home_featured_event_admin_page.py precedent — whether a Playwright
context `locale` actually drives the Control Panel's OWN display language
(vs. Liferay following the authenticated user account's stored language
preference) has NOT been confirmed against live qcdev. Verify during locator
extraction; if account-preference wins, replace the context-locale mechanism
below with an explicit in-app language switch once
HomeQuickContactAdminPage exposes one.
"""

import os

import allure
import pytest

from web.pages.components.cms_login_page import CmsLoginPage
from web.pages.home_quick_contact.home_quick_contact_admin_page import HomeQuickContactAdminPage

PBI = "129390"

# ── Blocker-chain gate: skip (never RuntimeError) while ANY of
#    HomeQuickContactAdminPage's locators is still an unresolved TODO
#    placeholder, and say WHICH ones — same convention as commit 70c7379's
#    web/tests/header/test_accessibility_settings_control_panel.py.
_PLACEHOLDER_PREFIX = "TODO:"
_UNRESOLVED = [
    f"{cls.__name__}.{name}"
    for cls, names in (
        (HomeQuickContactAdminPage, (
            "HOME_PAGE_MANAGEMENT_LINK", "CONTACT_US_SECTION_MANAGEMENT_LINK", "MANAGEMENT_SCREEN",
            "SECTION_TAG_HEADING_INPUT", "SECTION_HEADING_AR_INPUT", "SECTION_DESCRIPTION_EN_INPUT",
            "SECTION_DESCRIPTION_AR_INPUT", "EMAIL_SUPPORT_ADDRESS_INPUT", "TELEPHONE_INPUT",
            "LOCATION_ADDRESS_EN_INPUT", "LOCATION_ADDRESS_AR_INPUT", "MAP_EMBED_URL_INPUT",
            "INQUIRY_CATEGORY_GRID", "RECIPIENT_EMAILS_INPUT", "BUTTON_LABEL_EN_INPUT",
            "BUTTON_LABEL_AR_INPUT", "SAVE_DRAFT_BUTTON", "PREVIEW_BUTTON", "PUBLISH_BUTTON",
            "UNPUBLISH_BUTTON", "MANAGEMENT_FORM",
        )),
    )
    for name in names
    if str(getattr(cls, name)).startswith(_PLACEHOLDER_PREFIX)
]
_UNRESOLVED_SKIP = pytest.mark.skipif(
    bool(_UNRESOLVED),
    reason=(
        "Unresolved locator placeholders on HomeQuickContactAdminPage — run "
        "tools/extract_locators.py (as an authenticated Site Content Editor) "
        "against the live Contact Us Section Management screen and replace: " + ", ".join(_UNRESOLVED)
    ),
)

_AR_LOCALE_PARAM = {"locale": "ar-QA", "timezone_id": "Asia/Qatar"}


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
@allure.feature("Quick Contact Us Section")
@allure.story("CMS Contact Us Section Management screen field inventory")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The CMS Contact Us Section Management screen renders all configuration fields")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136480")
@_UNRESOLVED_SKIP
def test_management_screen_renders_all_configuration_fields(page):
    # ADO-136480 | PBI 129390
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = HomeQuickContactAdminPage(page)

    # Act
    with allure.step("Log into Liferay CMS as a Site Content Editor"):
        login.open_login().login(user, password)

    with allure.step("Navigate to Home Page management -> Contact Us Section Management"):
        admin.navigate_to_home_page_management()
        admin.open_contact_us_section_management()

    with allure.step("Read the visibility of every configuration field and action"):
        fields = admin.visible_field_map()

    # Assert
    assert login.login_succeeded()
    assert admin.is_management_screen_visible()
    missing = [name for name, visible in fields.items() if not visible]
    assert not missing, f"expected all configuration fields/actions visible, missing: {missing}"


@allure.epic("GLOBAL")
@allure.feature("Quick Contact Us Section")
@allure.story("CMS Management screen Arabic/RTL rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Contact Us Section Management screen renders correctly in Arabic in the CMS")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136551")
@_UNRESOLVED_SKIP
@pytest.mark.parametrize("page", [_AR_LOCALE_PARAM], indirect=True)
def test_management_screen_renders_correctly_in_arabic(page):
    # ADO-136551 | PBI 129390
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = HomeQuickContactAdminPage(page)

    # Act
    with allure.step("Switch the Liferay CMS UI locale to Arabic and log in"):
        login.open_login().login(user, password)

    with allure.step("Open Contact Us Section Management"):
        admin.navigate_to_home_page_management()
        admin.open_contact_us_section_management()

    with allure.step("Inspect field label/help-text language, RTL alignment, and Arabic input acceptance"):
        direction = admin.management_form_direction()
        admin.type_into_arabic_field("قسم تواصل معنا")
        arabic_value = admin.arabic_field_value()

    # Assert
    assert admin.is_management_screen_visible()
    assert direction == "rtl", "expected the Management screen to render right-to-left in Arabic"
    assert arabic_value == "قسم تواصل معنا", "expected the field to accept and retain real Arabic input"

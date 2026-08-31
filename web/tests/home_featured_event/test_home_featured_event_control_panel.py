"""
web/tests/home_featured_event/test_home_featured_event_control_panel.py —
Upcoming Featured Event (PBI 129382 / QC-HOME-006), Control_Panel platform.

Source: 5 approved, Automation-tagged, UI-category, Control_Panel-platform
cases handed off for this PBI (ADO TC 135653-135657). Web-platform cases for
this same PBI are scripted separately in the sibling
test_home_featured_event_web.py. Per active/standards.md's Tag-Taxonomy
mapping, every case here carries `EVENT` (Service axis ->
@pytest.mark.event) and `UI` (Category axis -> @pytest.mark.ui); TC 135656
and TC 135657 additionally carry `Bilingual` (Axis 5 -> @pytest.mark.bilingual).
None of the 5 carry `Regression`, so no test below carries
@pytest.mark.regression.

REAL, CONFIRMED BLOCKER (2026-08-24, not fabricated — see
web/pages/home_featured_event/home_featured_event_admin_page.py's own
docstring for the full account): TEST_USER/TEST_PASSWORD are blank in
.env. The anonymous /c/portal/login FORM itself is reachable and its
locators are real/confirmed (web/pages/components/cms_login_page.py), but
nothing PAST login — Home Page management, the Pin Configuration screen,
the Event Selector, the Active Status control, Save, the success toast,
and the RTL form layout — could be reached by an authenticated session
this run, and no Playwright MCP fallback was available either. Every
locator HomeFeaturedEventAdminPage exposes is therefore a literal `TODO:`
placeholder string, never a guessed-but-plausible Liferay selector.

GATING — same `_UNRESOLVED` collection-time skipif convention this
project's own git history already established for exactly this situation
(commit 70c7379, "move placeholder gate to collection-time skipif" —
web/tests/header/test_accessibility_settings_control_panel.py /
web/pages/header/accessibility_settings_page.py; that page/test pair was
later removed as a duplicate tree per active/standards.md's "Automation
Structure" section, 2026-08-19, but the convention itself was
re-confirmed to stand and is reproduced here under the current
per-page-folder file-suffix layout). Every test below carries a
`@pytest.mark.skipif(bool(_UNRESOLVED), reason=...)` gate computed from
HomeFeaturedEventAdminPage's own placeholder constants — a collection-time
SKIP with the concrete list of what's unresolved, never a runtime
RuntimeError mid-test. A second, independent runtime gate (a plain
`pytest.skip` on missing TEST_USER/TEST_PASSWORD) is layered in each test
body too: fixing the locators alone would otherwise flip these straight
from SKIP to a real login failure with no credentials to log in with.

LOCALE HANDLING (TC 135656 EN-toast's AR counterpart, TC 135657 RTL): same
UNVERIFIED mechanism note as the accessibility-settings precedent —
whether a Playwright context `locale` actually drives the Control Panel's
OWN display language (vs. Liferay following the authenticated user
account's stored language preference) has NOT been confirmed against live
qcdev. Verify during locator extraction; if account-preference wins,
replace the context-locale mechanism below with an explicit in-app
language switch once HomeFeaturedEventAdminPage exposes one.

TEST DATA: the case text does not name a concrete event to select for TC
135655/135656 (unlike the Web-platform cases, which pin "Meeting business
delegation of the Novgorod Region's government" — see the sibling
test_home_featured_event_web.py). That same title is reused here as the
concrete event selected in the Save-flow tests, since it is the only
real, confirmed event title available anywhere in this PBI's material —
not invented fresh for this file.

EXACT SUCCESS-TOAST COPY is not asserted verbatim in EN/AR (only
visibility + non-empty text) — the case only specifies "the standard
Liferay generic success toast appears," with no literal quoted string,
and this session has no live access to read Liferay's actual generic
success message in either language. Replace with an exact-copy assertion
once a real authenticated pass reads it.
"""

import os

import allure
import pytest

from web.pages.components.cms_login_page import CmsLoginPage
from web.pages.home_featured_event.home_featured_event_admin_page import HomeFeaturedEventAdminPage

PBI = "129382"

# Event title reused from the sibling Web-platform module's concrete pinned
# event (see module docstring's TEST DATA note) — not invented fresh here.
SELECTED_EVENT_TITLE = "Meeting business delegation of the Novgorod Region's government"

# ── Blocker-chain gate: skip (never RuntimeError) while ANY of
#    HomeFeaturedEventAdminPage's locators is still an unresolved TODO
#    placeholder, and say WHICH ones — same convention as commit 70c7379's
#    web/tests/header/test_accessibility_settings_control_panel.py.
_PLACEHOLDER_PREFIX = "TODO:"
_UNRESOLVED = [
    f"{cls.__name__}.{name}"
    for cls, names in (
        (HomeFeaturedEventAdminPage, (
            "HOME_PAGE_MANAGEMENT_LINK", "UPCOMING_EVENT_PIN_CONFIG_LINK", "PIN_CONFIG_SCREEN",
            "EVENT_SELECTOR", "EVENT_SELECTOR_OPTION", "ACTIVE_STATUS_CONTROL", "SAVE_BUTTON",
            "SUCCESS_TOAST", "PIN_CONFIG_FORM",
        )),
    )
    for name in names
    if str(getattr(cls, name)).startswith(_PLACEHOLDER_PREFIX)
]
_UNRESOLVED_SKIP = pytest.mark.skipif(
    bool(_UNRESOLVED),
    reason=(
        "Unresolved locator placeholders on HomeFeaturedEventAdminPage — run "
        "tools/extract_locators.py (as an authenticated Site Content Editor) "
        "against the live Pin Configuration screen and replace: " + ", ".join(_UNRESOLVED)
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


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Pin Configuration screen accessibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Upcoming Event Pin Configuration screen is accessible from Home Page management in the Liferay CMS")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135653")
@_UNRESOLVED_SKIP
def test_pin_configuration_screen_accessible_from_home_page_management(page):
    # EVENT-FEATUREDEVENT-TC-135653 | PBI 129382
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = HomeFeaturedEventAdminPage(page)

    # Act
    with allure.step("Log into Liferay CMS as a Site Content Editor"):
        login.open_login().login(user, password)

    with allure.step("Navigate to Home Page management"):
        admin.navigate_to_home_page_management()

    with allure.step("Open Upcoming Event Pin Configuration"):
        admin.open_pin_configuration()

    # Assert
    assert login.login_succeeded()
    assert admin.is_pin_config_screen_visible()
    assert admin.is_event_selector_visible()
    assert admin.is_active_status_control_visible()


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Event Selector published-events list")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Event Selector displays a list of all published events")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135654")
@_UNRESOLVED_SKIP
def test_event_selector_shows_all_published_events(page):
    # EVENT-FEATUREDEVENT-TC-135654 | PBI 129382
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = HomeFeaturedEventAdminPage(page)

    # Act
    with allure.step("Log into Liferay CMS as a Site Content Editor"):
        login.open_login().login(user, password)

    with allure.step("Open the Pin Configuration screen"):
        admin.navigate_to_home_page_management()
        admin.open_pin_configuration()

    with allure.step("Click to open the Event Selector"):
        admin.open_event_selector()
        labels = admin.published_event_option_labels()

    # Assert
    assert labels, "expected at least one Published event option in the Event Selector"
    assert all(label.strip() for label in labels), "a returned option had a blank label"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Save success toast — English")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Liferay generic success toast displays in English after saving the Pin Configuration")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135655")
@_UNRESOLVED_SKIP
def test_save_success_toast_displays_in_english(page):
    # EVENT-FEATUREDEVENT-TC-135655 | PBI 129382
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = HomeFeaturedEventAdminPage(page)

    # Act
    with allure.step("Set CMS UI language to English (default) and log in"):
        login.open_login().login(user, password)

    with allure.step("Open the Pin Configuration screen"):
        admin.navigate_to_home_page_management()
        admin.open_pin_configuration()

    with allure.step(f"Select a published event ('{SELECTED_EVENT_TITLE}') and set Active Status to enabled"):
        admin.select_event(SELECTED_EVENT_TITLE)
        admin.set_active_status(True)

    with allure.step("Click Save"):
        admin.click_save()

    # Assert
    assert admin.is_success_toast_visible(), "expected the Liferay generic success toast after Save"
    assert admin.success_toast_text().strip(), "expected non-empty toast text (exact copy unconfirmed — see docstring)"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Save success toast — Arabic")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Liferay generic success toast displays in Arabic after saving the Pin Configuration")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135656")
@_UNRESOLVED_SKIP
@pytest.mark.parametrize("page", [_AR_LOCALE_PARAM], indirect=True)
def test_save_success_toast_displays_in_arabic(page):
    # EVENT-FEATUREDEVENT-TC-135656 | PBI 129382
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = HomeFeaturedEventAdminPage(page)

    # Act
    with allure.step("Set CMS UI language to Arabic and log in"):
        login.open_login().login(user, password)

    with allure.step("Open the Pin Configuration screen"):
        admin.navigate_to_home_page_management()
        admin.open_pin_configuration()

    with allure.step(f"Select a published event ('{SELECTED_EVENT_TITLE}') and set Active Status to enabled"):
        admin.select_event(SELECTED_EVENT_TITLE)
        admin.set_active_status(True)

    with allure.step("Click Save"):
        admin.click_save()

    # Assert
    assert admin.is_success_toast_visible(), "expected the Liferay generic success toast after Save"
    assert admin.success_toast_text().strip(), "expected non-empty toast text (exact copy unconfirmed — see docstring)"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Pin Configuration form RTL rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Pin Configuration screen renders correctly in RTL when the CMS language is Arabic")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135657")
@_UNRESOLVED_SKIP
@pytest.mark.parametrize("page", [_AR_LOCALE_PARAM], indirect=True)
def test_pin_configuration_form_renders_rtl_in_arabic(page):
    # EVENT-FEATUREDEVENT-TC-135657 | PBI 129382
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = HomeFeaturedEventAdminPage(page)

    # Act
    with allure.step("Set CMS UI language to Arabic and log in"):
        login.open_login().login(user, password)

    with allure.step("Open the Pin Configuration screen"):
        admin.navigate_to_home_page_management()
        admin.open_pin_configuration()

    with allure.step("Inspect field label alignment and form layout direction"):
        direction = admin.pin_config_form_direction()

    # Assert
    assert admin.is_pin_config_screen_visible()
    assert direction == "rtl", "expected the Pin Configuration form to render right-to-left in Arabic"

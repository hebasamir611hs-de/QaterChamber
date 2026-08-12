"""
web/tests/header/test_language_switcher_control_panel.py — Language Switcher,
Control-Panel surface (PBI 133380, "QC-GBL-002").

Structural split (2026-08-11, per .claude/context/active/standards.md ->
"Automation Structure - Project Deviation from the Plugin Default"): this
module holds every Control_Panel-tagged GLOBAL-LANGUAGESWITCHER-TC-* case
(TC-020 .. TC-022). The sibling Web-tagged cases live in
test_language_switcher_web.py in this same folder. No case in this backlog
is tagged both Web and Control_Panel, so every case here has exactly one
test, moved verbatim (no content changes) from the original merged module.
(TC-020 is tagged Control_Panel only per its source case even though its
own assertion also checks the public homepage — that classification is the
source case's, not re-judged here.)

Every test still carries:
  - its QA traceability ID (`@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-xxx")`)
  - the Axis B backlog marker `@pytest.mark.pbi_133380` + `allure.label("pbi", PBI)`
  - one marker per tag axis actually present on its source case.

CMS/Control-Panel steps go through `HeaderAdminPage`, whose field constants
are `TODO(locator)` placeholders (disclosed, CMS-only exception — see
header_admin_page.py's docstring): the Liferay Control Panel sits behind
auth this session has no credentials for.

Scripted, not executed: per the task's hard constraint, none of these tests
have been run. "Scripted" (automation-standards.md's Definition of Done,
Scripted tier) is the only claim made here.
"""

import allure
import pytest

from web.pages.header.language_switcher_page import LanguageSwitcherPage
from web.pages.header.header_admin_page import HeaderAdminPage

PBI = "133380"


@allure.epic("Language Switcher")
@allure.feature("Functional-Low")
@allure.story("Verify that a Site Content Editor can enable the language switcher via the CMS header configuration")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Editor can enable the language switcher via the CMS header configuration")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-020")
def test_tc020_verify_editor_can_enable_switcher_via_cms_header_configuration(page):
    """GLOBAL-LANGUAGESWITCHER-TC-020 — Verify that a Site Content Editor can enable the language switcher via the CMS header configuration"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    admin = HeaderAdminPage(page)
    admin.open_header_management()

    with allure.step('Enable the "Language Switcher" toggle and save'):
        admin.set_toggle(HeaderAdminPage.LANGUAGE_SWITCHER_ENABLED_TOGGLE, True)
        admin.click_save_and_publish()
    with allure.step("Assert: switcher is now visible on the public homepage"):
        switcher.open_home()
        assert switcher.is_switcher_visible()


@allure.epic("Language Switcher")
@allure.feature("Functional-Low")
@allure.story("Verify that the language switcher's enabled toggle state persists after saving and reopening the CMS configuration")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the language switcher's enabled toggle state persists after saving and reopening the CMS configuration")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-021")
def test_tc021_verify_switcher_enabled_toggle_persists_after_save_reopen(page):
    """GLOBAL-LANGUAGESWITCHER-TC-021 — Verify that the language switcher's enabled toggle state persists after saving and reopening the CMS configuration"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    admin = HeaderAdminPage(page)
    admin.open_header_management()

    with allure.step('Enable the "Language Switcher" toggle and save'):
        admin.set_toggle(HeaderAdminPage.LANGUAGE_SWITCHER_ENABLED_TOGGLE, True)
        admin.click_save_and_publish()
    with allure.step("Navigate away, then reopen the header configuration"):
        admin.open_media_library()
        admin.open_header_management()

    # Assert
    assert admin.is_toggle_active(HeaderAdminPage.LANGUAGE_SWITCHER_ENABLED_TOGGLE) is True


@allure.epic("Language Switcher")
@allure.feature("Functional-Low")
@allure.story("Verify that a non-Editor role cannot access the language switcher's CMS configuration")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that a non-Editor role cannot access the language switcher's CMS configuration")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.control_panel
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-022")
def test_tc022_verify_non_editor_role_cannot_access_switcher_cms_configuration(page):
    """GLOBAL-LANGUAGESWITCHER-TC-022 — Verify that a non-Editor role cannot access the language switcher's CMS configuration"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — a Site Content Author session (no Global Components permission)
    admin = HeaderAdminPage(page)

    # Act
    with allure.step("Attempt to navigate to the Global Components header configuration screen"):
        admin.open_header_management()

    # Assert
    assert admin.access_denied_message() != ""
    assert admin.is_control_exposed(HeaderAdminPage.LANGUAGE_SWITCHER_ENABLED_TOGGLE) is False

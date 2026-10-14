"""
cms/tests/global_search/test_global_search_control_panel.py

PBI 131055 (Global Advanced Search) — Control_Panel cases, scripted 2026-10-01
from .claude/qa-runs/phase3_131055_cp_batch.json (21 automate; 141888 is
Manual and not scripted).

The cases need a "Global Search configuration screen" (Results Per Page,
Indexed Content Types, Available Filters, Re-index Schedule, Trigger
Re-index). No project document names it. Step 1 of every test logs in as
TEST_USER (the cases' "Administrator") and calls
GlobalSearchConfigPage.locate(), which checks Liferay's Instance Settings,
System Settings and Search admin screens.

  - Not found -> the test fails at step 1 with
    "Global Search configuration screen not found: checked <list>" and a
    screenshot. That is the expected outcome if the feature was never built.
  - Found -> functional tests stop before the first Save / Re-index (not
    approved: brief v2) and fail, naming the URL and fields found. The four
    Auth cases continue, non-mutating: as Author / Editor they open that URL
    and assert the refusal positively (signed in, the case's denial text, no
    editable field, no save control).

Nothing in this module saves configuration or starts a re-index.
"""

import allure
import pytest

from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.global_search.global_search_admin_page import GlobalSearchConfigPage
from config.settings import cms_role_credentials, settings
from core.web.browser import new_context

_NO_AUTH = {"auth": False}
_DENIED = {"en": "Access Denied.", "ar": "تم رفض الوصول."}


def _locate_as_admin(page):
    """Step 1 for every case: sign in as TEST_USER and find the screen. Fails
    with the list of candidates checked when it does not exist."""
    login_page = CmsLoginPage(page)
    login_page.open_login().login(settings.test_user, settings.test_password)
    assert login_page.login_succeeded(), "TEST_USER login did not reach a signed-in page"
    config = GlobalSearchConfigPage(page)
    with allure.step("Locate the Global Search configuration screen (Administrator)"):
        found = config.locate()
        allure.attach(config.screenshot_png(), name="last candidate checked",
                      attachment_type=allure.attachment_type.PNG)
        allure.attach("\n".join(found.checked), name="candidates checked",
                      attachment_type=allure.attachment_type.TEXT)
    lost = [c for c in found.checked if "signed_in=False" in c]
    if not found.found and lost:
        pytest.fail("Inconclusive — TEST_USER session lost at: " + "; ".join(lost))
    if not found.found:
        pytest.fail("Global Search configuration screen not found: checked " + "; ".join(found.checked))
    return found


def _stop_before_unapproved_write(found, next_step: str) -> None:
    pytest.fail(
        f"Global Search configuration screen found at {found.found_url} (fields: {found.found_fields}). "
        f"The next step ({next_step!r}) saves search configuration or re-indexes. Brief v2 does not "
        "approve that, so scripting stops here. Report the URL and fields to the QA Manager."
    )


def _assert_role_denied(page, browser, role: str, locale: str) -> None:
    admin_context = new_context(browser, use_auth_state=False)
    try:
        found = _locate_as_admin(admin_context.new_page())
    finally:
        admin_context.close()

    login_page = CmsLoginPage(page)
    with allure.step(f"Log in as {role}"):
        login_page.open_login().login(*cms_role_credentials(role))
        assert login_page.login_succeeded(), f"{role} login did not reach a signed-in page"

    config = GlobalSearchConfigPage(page)
    url = found.found_url
    if locale == "ar":
        url = url.replace("/group/", "/ar/group/", 1)
    with allure.step(f"Open the configuration screen as {role} ({locale}) — access is refused"):
        config.open_url(url)
        allure.attach(config.screenshot_png(), name=f"{role} view", attachment_type=allure.attachment_type.PNG)
        assert config.signed_in(), f"{role} is no longer signed in — a signed-out page proves nothing"
        assert config.body_contains(_DENIED[locale]), (
            f"expected the case's denial text {_DENIED[locale]!r} for {role}; page title {page.title()!r}"
        )
        assert not config.editable_target_fields(), f"{role} can edit search configuration fields"
        assert not config.save_control_present(), f"a save control is available to {role}"


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that a Site Content Author is denied access to search configuration (EN) (ADO-141846)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.pbi_131055
@pytest.mark.tc_141846
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_site_content_author_is_denied_access_to_search(page, browser):
    """ADO 141846 (P1). Accounts: TEST_USER (the cases' "Administrator") to
    locate the screen; then Site Content Author via cms_role_credentials() for the denial.

    Steps (Azure):
      1. Log into Liferay CMS as Site Content Author (EN locale) -> Login succeeds as Site Content Author
      2. Navigate/attempt to navigate to the Global Search configuration screen -> Access is blocked with message 'Access Denied.'; configuration screen is not opened or fields are not editable
      3. Attempt to change a configuration value and save -> Save action is not available/executed; no configuration is changed
    """
    _assert_role_denied(page, browser, "Site Content Author", "en")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that saving search configuration displays the EN success toast (ADO-141853)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.regression
@pytest.mark.pbi_131055
@pytest.mark.tc_141853
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_saving_search_configuration_displays_the_en_success_toast(page):
    """ADO 141853 (P2). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Log into Liferay CMS as Administrator (EN locale) -> Login succeeds
      2. Navigate to the Global Search configuration screen -> Configuration screen loads with current values
      3. Set Results Per Page to 15 -> Value 15 entered in Results Per Page
      4. Click Save/Publish -> Toast 'Your request completed successfully.' is displayed; configuration is persisted (value 15 shown on reload)

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Navigate to the Global Search configuration screen")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that all search configuration changes are recorded in the audit log (ADO-141854)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_131055
@pytest.mark.tc_141854
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_all_search_configuration_changes_are_recorded_in_the_audit(page):
    """ADO 141854 (P2). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Log in as Administrator -> Login succeeds
      2. Change Results Per Page from 10 to 20 and save -> Configuration saved, toast shown
      3. Navigate to the Audit Log module -> Audit Log module loads
      4. Locate the most recent entry for this configuration change -> A new entry is present showing the acting Administrator, 'Results Per Page' changed from 10 to 20, and a timestamp matching the save action

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Change Results Per Page from 10 to 20 and save")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that a valid Results Per Page value is accepted and saved (ADO-141862)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141862
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_valid_results_per_page_value_is_accepted_and_saved(page):
    """ADO 141862 (P2). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration as Administrator -> Configuration screen visible with current value
      2. Enter 20 in Results Per Page -> Value 20 entered
      3. Click Save -> Save succeeds; toast shown; value 20 is persisted

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Enter 20 in Results Per Page")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that an empty Results Per Page value is rejected (ADO-141863)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141863
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_an_empty_results_per_page_value_is_rejected(page):
    """ADO 141863 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen visible with current value
      2. Clear the Results Per Page field -> Field is empty
      3. Click Save -> Validation error shown ('Results Per Page is required'); save is blocked; previous value is retained

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Clear the Results Per Page field")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that a Results Per Page value of zero is rejected (ADO-141864)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141864
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_results_per_page_value_of_zero_is_rejected(page):
    """ADO 141864 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen visible with current value
      2. Enter 0 in Results Per Page -> Value 0 entered
      3. Click Save -> Validation error shown ('must be a positive integer'); save is blocked; previous value is retained

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Enter 0 in Results Per Page")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that a negative Results Per Page value is rejected (ADO-141865)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141865
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_negative_results_per_page_value_is_rejected(page):
    """ADO 141865 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen visible with current value
      2. Enter -5 in Results Per Page -> Value -5 entered
      3. Click Save -> Validation error shown ('must be a positive integer'); save is blocked; previous value is retained

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Enter -5 in Results Per Page")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that a non-numeric Results Per Page value is rejected (ADO-141866)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141866
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_non_numeric_results_per_page_value_is_rejected(page):
    """ADO 141866 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen visible with current value
      2. Enter 'abc' in Results Per Page -> Value 'abc' entered (or field rejects non-numeric input on keystroke)
      3. Click Save -> Validation error shown ('must be a numeric value'); save is blocked; previous value is retained

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Enter 'abc' in Results Per Page")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that a saved Results Per Page value persists after reload (ADO-141867)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141867
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_saved_results_per_page_value_persists_after_reload(page):
    """ADO 141867 (P2). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen loads
      2. Enter 25 in Results Per Page and click Save -> Save succeeds; toast shown
      3. Reload/re-navigate to the configuration screen -> Results Per Page still shows 25 after reload

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Enter 25 in Results Per Page and click Save")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that the administrator can define Indexed Content Types and they take effect (ADO-141868)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141868
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_administrator_can_define_indexed_content_types_and_they_take(page):
    """ADO 141868 (P2). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen loads
      2. Select Pages, Events, Publications, and Services in Indexed Content Types -> All four values selected
      3. Click Save -> Save succeeds; selection persisted
      4. Search a keyword known to match each of the four types -> Public search continues to return matches for all four content types

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Select Pages, Events, Publications, and Services in Indexed Content Types")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that Indexed Content Types cannot be saved empty (ADO-141869)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141869
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_indexed_content_types_cannot_be_saved_empty(page):
    """ADO 141869 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen loads with current selections
      2. Deselect all values in Indexed Content Types -> All values deselected
      3. Click Save -> Validation error shown ('at least one content type is required'); save is blocked; previous selection retained

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Deselect all values in Indexed Content Types")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that the administrator can define Available Filters and they take effect on the results page (ADO-141870)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141870
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_administrator_can_define_available_filters_and_they_take(page):
    """ADO 141870 (P2). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen loads
      2. Select Type, Category, and Date Range in Available Filters -> All three values selected
      3. Click Save -> Save succeeds; selection persisted
      4. Search a keyword on the public site and inspect the filters panel -> Results page shows Type, Category, and Date Range filter controls

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Select Type, Category, and Date Range in Available Filters")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that Available Filters cannot be saved empty (ADO-141871)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141871
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_available_filters_cannot_be_saved_empty(page):
    """ADO 141871 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen loads with current selections
      2. Deselect all values in Available Filters -> All values deselected
      3. Click Save -> Validation error shown ('at least one filter is required'); save is blocked; previous selection retained

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Deselect all values in Available Filters")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that a valid Re-index Schedule is accepted and saved (ADO-141872)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141872
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_valid_re_index_schedule_is_accepted_and_saved(page):
    """ADO 141872 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen loads
      2. Set Re-index Schedule to 'Daily at 02:00' -> Schedule value entered
      3. Click Save -> Save succeeds; toast shown; schedule value persisted

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Set Re-index Schedule to 'Daily at 02:00'")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that an invalid Re-index Schedule value is rejected (ADO-141873)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141873
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_an_invalid_re_index_schedule_value_is_rejected(page):
    """ADO 141873 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration -> Configuration screen loads
      2. Enter 'every blueday' in Re-index Schedule -> Invalid value entered
      3. Click Save -> Validation error shown ('invalid schedule format'); save is blocked; previous schedule value retained

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Enter 'every blueday' in Re-index Schedule")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that the administrator can manually trigger a re-index (ADO-141883)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131055
@pytest.mark.tc_141883
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_administrator_can_manually_trigger_a_re_index(page):
    """ADO 141883 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Navigate to Global Search configuration as Administrator -> Configuration screen loads
      2. Click 'Trigger Re-index' -> Re-index job starts; a running/in-progress indicator is shown
      3. Wait for the job to complete -> Job completes; a completion indicator/timestamp is shown

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "Click 'Trigger Re-index'")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that adding a new content type becomes filterable once indexed (ADO-141889)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_131055
@pytest.mark.tc_141889
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_adding_a_new_content_type_becomes_filterable_once_indexed(page):
    """ADO 141889 (P3). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. Confirm 'Circulars' is not currently a selectable Content Type filter value on the public results page -> 'Circulars' is absent from the filter option list
      2. As Administrator, add 'Circulars' to Indexed Content Types and save -> New content type is added and saved in configuration
      3. Trigger/await re-indexing to complete -> Re-index job completes
      4. Search a keyword and inspect the Content Type filter options -> 'Circulars' now appears as a selectable Content Type filter value, and selecting it returns Circulars-type results

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "As Administrator, add 'Circulars' to Indexed Content Types and save")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("Verify that a Site Content Editor is denied access to search configuration (EN) (ADO-141890)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.pbi_131055
@pytest.mark.tc_141890
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_site_content_editor_is_denied_access_to_search(page, browser):
    """ADO 141890 (P1). Accounts: TEST_USER (the cases' "Administrator") to
    locate the screen; then Site Content Editor via cms_role_credentials() for the denial.

    Steps (Azure):
      1. Log into Liferay CMS as Site Content Editor (EN locale) -> Login succeeds as Site Content Editor
      2. Navigate/attempt to navigate to the Global Search configuration screen -> Access is blocked with message 'Access Denied.'; configuration screen is not opened or fields are not editable
      3. Attempt to change a configuration value and save -> Save action is not available/executed; no configuration is changed
    """
    _assert_role_denied(page, browser, "Site Content Editor", "en")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("التحقق من أنه يُرفض وصول Site Content Author إلى إعدادات البحث (AR) (ADO-141892)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.pbi_131055
@pytest.mark.tc_141892
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_site_content_author_denied_search_configuration_ar(page, browser):
    """ADO 141892 (P1). Accounts: TEST_USER (the cases' "Administrator") to
    locate the screen; then Site Content Author via cms_role_credentials() for the denial.

    Steps (Azure):
      1. تسجيل الدخول إلى نظام Liferay CMS بحساب Site Content Author (واجهة عربية) -> تسجيل الدخول ينجح كـSite Content Author
      2. محاولة الانتقال إلى شاشة إعدادات البحث العام -> يُرفض الوصول برسالة 'تم رفض الوصول.'؛ لا تُفتح شاشة الإعدادات أو تكون الحقول غير قابلة للتعديل
      3. محاولة تغيير قيمة إعداد وحفظها -> لا يتوفر/ينفَّذ إجراء الحفظ؛ لا يتغير أي إعداد
    """
    _assert_role_denied(page, browser, "Site Content Author", "ar")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("التحقق من أنه تظهر رسالة نجاح الحفظ باللغة العربية عند حفظ إعدادات البحث (ADO-141893)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.regression
@pytest.mark.pbi_131055
@pytest.mark.tc_141893
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_search_configuration_save_shows_ar_success_toast(page):
    """ADO 141893 (P2). Account: TEST_USER (the case's "Administrator").

    Steps (Azure):
      1. تسجيل الدخول إلى Liferay CMS كمسؤول (واجهة عربية) -> تسجيل الدخول ينجح
      2. الانتقال إلى شاشة إعدادات البحث العام -> تُحمَّل شاشة الإعدادات بالقيم الحالية
      3. تعيين عدد النتائج لكل صفحة إلى 15 -> إدخال القيمة 15 في حقل عدد النتائج لكل صفحة
      4. الضغط على حفظ/نشر -> تظهر رسالة 'تمت معالجة طلبك بنجاح.'؛ يتم حفظ الإعداد (تظهر القيمة 15 بعد إعادة التحميل)

    Step 1 (reach the configuration screen) runs live. The remaining steps save
    site search configuration or trigger a re-index, which brief v2 does NOT
    approve. If the screen exists, the test stops before them and fails with the
    URL found, rather than pass on steps it never ran.
    """
    found = _locate_as_admin(page)
    _stop_before_unapproved_write(found, "الانتقال إلى شاشة إعدادات البحث العام")


@allure.epic("Global")
@allure.feature("Global Advanced Search — CMS configuration")
@allure.title("التحقق من أنه يُرفض وصول Site Content Editor إلى إعدادات البحث (AR) (ADO-141894)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.pbi_131055
@pytest.mark.tc_141894
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_site_content_editor_denied_search_configuration_ar(page, browser):
    """ADO 141894 (P1). Accounts: TEST_USER (the cases' "Administrator") to
    locate the screen; then Site Content Editor via cms_role_credentials() for the denial.

    Steps (Azure):
      1. تسجيل الدخول إلى نظام Liferay CMS بحساب Site Content Editor (واجهة عربية) -> تسجيل الدخول ينجح كـSite Content Editor
      2. محاولة الانتقال إلى شاشة إعدادات البحث العام -> يُرفض الوصول برسالة 'تم رفض الوصول.'؛ لا تُفتح شاشة الإعدادات أو تكون الحقول غير قابلة للتعديل
      3. محاولة تغيير قيمة إعداد وحفظها -> لا يتوفر/ينفَّذ إجراء الحفظ؛ لا يتغير أي إعداد
    """
    _assert_role_denied(page, browser, "Site Content Editor", "ar")

"""
web/tests/header/test_accessibility_settings_control_panel.py

ADO Test Case 134658: "Verify that a CMS user without Header Management
permission is denied access when attempting to change Accessibility
Settings."

PBI: NO-PBI. Earlier draft carried @pytest.mark.pbi_133381, inferred only
from PBI 133381's baseline (.claude/qa-baselines/133381.json) having the
same Auth-category count (=1) as this case — circumstantial, never
confirmed via the ADO parent-work-item link. Per automate-test-case's own
rule ("if no backlog ID is resolvable, write NO-PBI ... never guess an
ID"), the pbi_* marker is removed and no traceability marker is applied
either, since the local <SERVICE>-<FEATURE>-TC-<NNN> case_id would depend
on that same unconfirmed PBI link. The ADO work item id (134658) itself
IS confirmed (screenshot review, 2026-08-17) and is referenced by number
in this docstring and the Allure title/feature — that is the only
traceability claim being made until the real PBI/case_id is confirmed.

Tags confirmed live from ADO (screenshot, 2026-08-17): Accessibility,
Ai_MCP_Injected, Auth, Automation, Control_Panel, GLOBAL, Regression, UAT.
Every pytest marker this test needs was already registered in pytest.ini —
no marker changes were required for this file.

BLOCKED on two prerequisites, neither fixable by writing more test code:
  1. A dedicated qcdev test account with a role lacking Header Management
     permission. Credentials expected in .env as TEST_USER_RESTRICTED /
     TEST_PASSWORD_RESTRICTED — neither the account nor these keys exist
     yet. The test below SKIPS (not fails) while they're absent.
  2. A confirmed Control Panel login flow — see
     web/pages/control_panel/login_page.py's module docstring: this has
     never been verified against live qcdev, and may involve AD SSO rather
     than a plain form.

Steps mirror the ADO case exactly: one restricted-role login, no second
privileged account — the case never asserts a permitted user's positive
path, so scope stops at the denial.
"""

import os

import allure
import pytest

from web.pages.control_panel.login_page import CmsLoginPage
from web.pages.header.accessibility_settings_page import AccessibilitySettingsPage

EXPECTED_ACCESS_DENIED_EN = "Access Denied. You do not have permission to perform this action."
EXPECTED_ACCESS_DENIED_AR = "تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء."


@allure.epic("Global")
@allure.feature("Header Management")
@allure.story("Accessibility Settings — permission enforcement")
@allure.severity(allure.severity_level.CRITICAL)  # P1 in ADO — RBAC/permission bypass (standards.md)
@allure.title("CMS user without Header Management permission is denied access to Accessibility Settings (ADO-134658)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.accessibility
def test_restricted_role_denied_accessibility_settings(page):
    # NO-PBI — see module docstring. No pbi_* marker applied: no confirmed
    # backlog parent-link. Do not add one back without a real ADO link.
    restricted_user = os.getenv("TEST_USER_RESTRICTED", "")
    restricted_password = os.getenv("TEST_PASSWORD_RESTRICTED", "")
    if not restricted_user or not restricted_password:
        pytest.skip(
            "TEST_USER_RESTRICTED / TEST_PASSWORD_RESTRICTED not set in .env — blocked "
            "on a qcdev test account with a role lacking Header Management permission. "
            "See module docstring."
        )

    login_page = CmsLoginPage(page)
    settings_page = AccessibilitySettingsPage(page)

    with allure.step("Log into the CMS with a role lacking Header Management permission"):
        login_page.open_login().login(restricted_user, restricted_password)
        assert login_page.login_succeeded()

    with allure.step("Navigate to Global Components > Header Management > Accessibility Settings"):
        settings_page.open_settings()

    with allure.step("Access Denied is shown in both languages and the settings form does not load"):
        assert settings_page.access_denied_shown(locale="en")
        assert settings_page.text(settings_page.ACCESS_DENIED_MESSAGE_EN) == EXPECTED_ACCESS_DENIED_EN
        assert settings_page.access_denied_shown(locale="ar")
        assert settings_page.text(settings_page.ACCESS_DENIED_MESSAGE_AR) == EXPECTED_ACCESS_DENIED_AR
        assert not settings_page.settings_form_loaded()

    with allure.step("The toggle control is not present — no way to attempt a save"):
        assert not settings_page.accessibility_toggle_visible()

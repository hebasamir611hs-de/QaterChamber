"""
web/tests/components/test_accessibility_tools_control_panel.py

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

BLOCKED on a CHAIN of prerequisites (mentor review, 2026-08-18) — each is a
separate owned item; resolving one does NOT unblock the test:
  1. TEST_USER_RESTRICTED / TEST_PASSWORD_RESTRICTED — a qcdev account with
     a role lacking Header Management permission. Does not exist yet.
  2. AccessibilitySettingsPage placeholders (SETTINGS_PATH, denial-message
     and form locators) — extraction requires an ADMIN account that CAN
     reach the page (the restricted account by definition cannot). This is
     a second, independent dependency: provisioning the restricted account
     alone would previously have flipped this test from SKIP to
     RuntimeError mid-run. The module-level skipif below makes the whole
     chain explicit instead.
  3. CmsLoginPage field locators — LOGIN_PATH is confirmed live
     (2026-08-18, plain form at /c/portal/login, not SSO); the field
     selectors still need extraction.

AUTH ISOLATION (fix for the storageState false-PASS hazard): this test's
subject IS the login/permission flow, so its context must NOT auto-load the
cached admin storageState — a pre-authenticated admin session would make
the "denied" assertion meaningless. It opts out via the page fixture's
indirect param {"auth": False}.

LOCALE HANDLING: the Control Panel renders in ONE display language at a
time, so a single session cannot assert the EN and the AR denial message
back-to-back (the original draft did exactly that and would have failed
even against a fully correct RBAC implementation). The case is therefore
parametrized per display locale with a fresh browser context per locale.
UNVERIFIED mechanism note: whether a Playwright context `locale` actually
drives the Control Panel display language (vs. Liferay following the user
account's language preference) has NOT been confirmed against live qcdev —
verify during locator extraction, and if account-preference wins, replace
the context-locale mechanism with an explicit in-app language switch here.

Steps mirror the ADO case exactly: one restricted-role login, no second
privileged account — the case never asserts a permitted user's positive
path, so scope stops at the denial.
"""

import os

import allure
import pytest

from web.pages.components.cms_login_page import CmsLoginPage
from web.pages.components.accessibility_tools_admin_component import AccessibilitySettingsPage

EXPECTED_ACCESS_DENIED = {
    "en": "Access Denied. You do not have permission to perform this action.",
    "ar": "تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء.",
}

# ── Blocker-chain gate: skip (never RuntimeError) while ANY prerequisite is
#    unresolved, and say WHICH ones, so provisioning one dependency doesn't
#    surprise-error the run on the next. Placeholder constants all share the
#    "TODO:" prefix convention (see the page objects).
_PLACEHOLDER_PREFIX = "TODO:"
_UNRESOLVED = [
    f"{cls.__name__}.{name}"
    for cls, names in (
        (AccessibilitySettingsPage,
         ("SETTINGS_PATH", "ACCESS_DENIED_MESSAGE_EN", "ACCESS_DENIED_MESSAGE_AR",
          "ACCESSIBILITY_TOOLS_TOGGLE", "SETTINGS_FORM")),
        (CmsLoginPage,
         ("USERNAME_INPUT", "PASSWORD_INPUT", "SUBMIT_BUTTON", "LOGIN_SUCCESS_INDICATOR")),
    )
    for name in names
    if str(getattr(cls, name)).startswith(_PLACEHOLDER_PREFIX)
]

_LOCALE_PARAMS = {
    "en": {"auth": False, "locale": "en-US", "timezone_id": "Asia/Qatar"},
    "ar": {"auth": False, "locale": "ar-QA", "timezone_id": "Asia/Qatar"},
}


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
@pytest.mark.skipif(
    bool(_UNRESOLVED),
    reason=(
        "Unverified locator placeholders — run tools/extract_locators.py (as an "
        "admin who CAN reach the page) and replace: " + ", ".join(_UNRESOLVED)
    ),
)
@pytest.mark.parametrize(
    "page, display_locale",
    [
        pytest.param(_LOCALE_PARAMS["en"], "en", id="display-en"),
        pytest.param(_LOCALE_PARAMS["ar"], "ar", id="display-ar"),
    ],
    indirect=["page"],
)
def test_restricted_role_denied_accessibility_settings(page, display_locale):
    # NO-PBI — see module docstring. No pbi_* marker applied: no confirmed
    # backlog parent-link. Do not add one back without a real ADO link.
    restricted_user = os.getenv("TEST_USER_RESTRICTED", "")
    restricted_password = os.getenv("TEST_PASSWORD_RESTRICTED", "")
    if not restricted_user or not restricted_password:
        pytest.skip(
            "TEST_USER_RESTRICTED / TEST_PASSWORD_RESTRICTED not set in .env — blocked "
            "on a qcdev test account with a role lacking Header Management permission. "
            "See module docstring (blocker chain item 1)."
        )

    login_page = CmsLoginPage(page)
    settings_page = AccessibilitySettingsPage(page)

    with allure.step(f"Log into the CMS with a role lacking Header Management permission ({display_locale} display)"):
        login_page.open_login().login(restricted_user, restricted_password)
        assert login_page.login_succeeded()

    with allure.step("Navigate to Global Components > Header Management > Accessibility Settings"):
        settings_page.open_settings()

    with allure.step(f"Access Denied is shown ({display_locale}) — anchor wait before any negative assertion"):
        settings_page.wait_for_denial(locale=display_locale)
        assert settings_page.denial_text(locale=display_locale) == EXPECTED_ACCESS_DENIED[display_locale]

    with allure.step("The settings form did not load and the toggle is absent — no way to attempt a save"):
        # Safe ONLY because wait_for_denial() proved the page reached its
        # terminal denied state above; these are zero-wait checks by design.
        assert not settings_page.settings_form_loaded()
        assert not settings_page.accessibility_toggle_visible()

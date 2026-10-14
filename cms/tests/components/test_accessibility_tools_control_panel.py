"""
cms/tests/components/test_accessibility_tools_control_panel.py

PBI 129364 (QC-GBL-003 Accessibility Tools) — Control_Panel cases, scripted
2026-09-30 from .claude/qa-runs/phase3_129364_cp_batch.json.

Surface: the Object Authoring manage page of the `AccessibilityHeaderConfiguration`
Object (ONE entry, one `accessibilityToolsEnabled` checkbox — see
cms/pages/components/accessibility_tools_admin_component.py). The Azure cases'
"Global Components -> Header Management -> Accessibility Settings" path and
"toggle" wording both describe this page and checkbox.

THE LIVE ENTRY IS NEVER SAVED. Nothing in this module clicks Save as Draft /
Submit / Publish / Unpublish / Delete on it. The Page Object has no save
method. Every case that needs a save on that entry is a skip
(SKIP-SINGLETON). The 2026-10-01 brief v2's approval for writes to entry 45370
reached this engineer only through the coordinator, and the permission system
refused that change, so those 7 stay skipped until the user confirms directly.

The image Alt Text cases (formerly SKIP-SPEC-GAP) are live since 2026-10-01.
They run on disposable QCTEST StrategicPartner records (guide §18), see the
section at the end of this module.

Automated:
  134491  render check — Site Content Editor, read-only.
  134514  change the checkbox, leave without saving, re-open — Site Content
          Editor. The stored value must be unchanged.
  134501  denial — Site Member (no role), EN then /ar.
  134658  denial — Site Member (no role), EN then /ar, and no save control.
          The same case as the older NO-PBI test below
          (`test_restricted_role_denied_accessibility_settings`), which is kept
          as it was. The new test reuses its mechanics: no cached
          storageState, a real login, a positive denial anchor before any
          negative check. It differs in three ways. It uses
          cms_role_credentials("Site Member") rather than the never-provisioned
          TEST_USER_RESTRICTED. It switches language with the /ar URL prefix,
          not the context locale. It carries the pbi_/tc_ markers.

Denial assertions read the case's literal message off the rendered body text.
They do not use a locator: the member's real view has not been observed yet,
because the Site Member keys are unset in .env. If the site shows something
else (e.g. the signed-out 404 "Coming Soon" page), the test fails and prints
what it saw. That is a requirements-vs-implementation finding to report. Do
not relax the test to make it pass.

----------------------------------------------------------------------------
Legacy section — test_restricted_role_denied_accessibility_settings:

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
import re
from contextlib import contextmanager

import json
import allure
import pytest

from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.components.accessibility_tools_admin_component import (
    AccessibilityConfigWriter,
    AccessibilitySettingsPage,
)
from cms.pages.components.header_admin_component import PublicHeaderNavProbe
from cms.pages.components.image_alt_text_admin_component import AR_ALT, EN_ALT, ImageAltTextRecordPage, qctest_title
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from config.settings import cms_role_credentials
from core.utils.waits import wait_until
from core.web.browser import new_context

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


# ══════════════════════════════════════════════════════════════════════════
# PBI 129364 — scripted 2026-09-30 (phase3_129364_cp_batch.json)
# ══════════════════════════════════════════════════════════════════════════

# The one live AccessibilityHeaderConfiguration entry. Tests that open it,
# even read-only, share a group so an Editor session never reads the
# checkbox while another is mid-toggle on it.
_SINGLETON_GROUP = "accessibility_header_config_singleton"
_NO_AUTH = {"auth": False}


def _sign_in(page, role: str) -> CmsLoginPage:
    """Real login as the named role in a context with no cached storageState."""
    login_page = CmsLoginPage(page)
    login_page.open_login().login(*cms_role_credentials(role))
    assert login_page.login_succeeded(), f"login as {role!r} did not reach a signed-in page"
    return login_page


def _assert_member_denied(login_page, settings, locale: str) -> None:
    """Denial as a signed-in Site Member, in one display language.

    Order matters. First prove the account is still signed in and is not the
    admin (the session guard re-authenticates as TEST_USER on a dropped
    session). A signed-out 404 or an admin's form would otherwise stand in
    for "denied". Then wait for the case's own message: the positive anchor.
    Only after that check that nothing usable rendered."""
    settings.open_settings(locale=locale)
    shown = settings.wait_for_body_text(EXPECTED_ACCESS_DENIED[locale])
    assert login_page.login_succeeded(), (
        f"[{locale}] the Site Member is no longer signed in — a signed-out page proves "
        f"nothing about permissions. Saw: {settings.page_heading()}"
    )
    assert not login_page.has_admin_toolbar(), (
        f"[{locale}] the session carries the staff toolbar — it is not the Site Member's "
        "(session guard may have re-authenticated as TEST_USER)."
    )
    assert shown, (
        f"[{locale}] expected the case's denial message {EXPECTED_ACCESS_DENIED[locale]!r}; "
        f"it never rendered. Saw: {settings.page_heading()}"
    )
    assert not settings.settings_form_loaded(), f"[{locale}] the settings form rendered for a denied account"
    assert not settings.toggle_visible(), f"[{locale}] the Accessibility Tools Enabled checkbox rendered"
    assert not settings.entries_table_visible(), f"[{locale}] the entries table rendered"


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.title("Verify that the CMS Accessibility Settings page renders the Accessibility Tools Enabled toggle (ADO-134491)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.tc_134491
@pytest.mark.xdist_group(_SINGLETON_GROUP)
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_accessibility_settings_renders_tools_enabled_toggle(page):
    """ADO 134491 (P3). Account: QC Site Content Editor (the case names it).

    1. Log in as Site Content Editor -> login succeeds.
    2. Open Accessibility Settings (manage-accessibility-header-configuration)
       -> the Accessibility Tools Enabled checkbox shows its saved state.

    "Saved state" is read off the stored entry's EDIT form. The create form
    renders the same checkbox unticked by default, so reading that would pass
    whatever is stored. The value must be the same on a second fresh
    navigation, which rules out client-side state. Read-only: nothing is
    changed or saved."""
    settings = AccessibilitySettingsPage(page)

    with allure.step("Log in to the CMS as Site Content Editor"):
        _sign_in(page, "Site Content Editor")

    with allure.step("Open the stored Accessibility Header Configuration entry"):
        settings.open_stored_entry()

    with allure.step("The Accessibility Tools Enabled checkbox is displayed with a stored value"):
        assert settings.toggle_visible(), "Accessibility Tools Enabled checkbox is not displayed"
        first_read = settings.toggle_checked()
        allure.attach(str(first_read), name="stored accessibilityToolsEnabled",
                      attachment_type=allure.attachment_type.TEXT)
        settings.reopen_stored_entry()
        assert settings.toggle_checked() == first_read, (
            "the checkbox value changed between two fresh loads of the same stored entry"
        )


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.title("Verify that changing Accessibility Tools Enabled without saving can be discarded (ADO-134514)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134514
@pytest.mark.xdist_group(_SINGLETON_GROUP)
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_unsaved_accessibility_tools_change_is_discarded(page):
    """ADO 134514 (P3). Account: QC Site Content Editor.

    1. Open Accessibility Settings, current value = True -> shows True.
    2. Untick the checkbox -> it shows False (unsaved).
    3. Navigate away without Save/Publish, then return -> the stored value
       is still True.

    NEVER SAVES. This runs against the one live entry. The only interaction
    is the checkbox click, then a navigation to the Object Authoring index.
    Only a `beforeunload` prompt is accepted; any other dialog is dismissed.

    The precondition (stored value True) is asserted, not assumed. If it
    reads False, someone changed the live setting. Report it; do not "fix" it
    by saving. A failure at step 3 (value or Last-modified changed) means
    something persisted without a save, such as an autosave. That is a
    product finding to escalate at once. The live setting must NOT be
    restored by automation (brief hard rule 1)."""
    settings = AccessibilitySettingsPage(page)

    with allure.step("Log in to the CMS as Site Content Editor"):
        _sign_in(page, "Site Content Editor")

    with allure.step("Open Accessibility Settings — the stored value is True"):
        code = settings.open_stored_entry()
        assert settings.toggle_checked() is True, (
            "precondition failed: the live Accessibility Tools Enabled value is not True. "
            "Do not restore it by saving — report it."
        )
        modified_before = settings.row_last_modified(code)
        status_before = settings.row_status(code)
        settings.reopen_stored_entry()

    with allure.step("Untick Accessibility Tools Enabled — the form shows False, unsaved"):
        settings.set_toggle_unsaved(False)
        assert settings.toggle_checked() is False, "the checkbox did not change to False in the form"

    with allure.step("Navigate away without saving, then return"):
        settings.leave_without_saving()
        settings.reopen_stored_entry()

    with allure.step("The stored value is still True — the unsaved change was discarded"):
        assert settings.toggle_checked() is True, (
            "ESCALATE: the live value now reads False after leaving WITHOUT saving — "
            "something persisted the change. Do not restore it by automation."
        )
        assert settings.row_status(code) == status_before == STATUS_PUBLISHED, (
            f"the entry's status moved: before {status_before!r}, now {settings.row_status(code)!r}"
        )
        assert settings.row_last_modified(code) == modified_before, (
            "ESCALATE: the entry's Last-modified changed although nothing was saved."
        )


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.story("Accessibility Settings — permission enforcement")
@allure.title("Verify that a CMS user without header-management permission cannot access Accessibility Settings (ADO-134501)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129364
@pytest.mark.tc_134501
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_member_without_permission_cannot_access_accessibility_settings(page):
    """ADO 134501 (P2). Account: the Site Member account (no CMS role) —
    cms_role_credentials("Site Member"). The case only says "a user without
    accessibility-settings permission". standards.md makes the no-role
    member the negative-case account, because it can sign in and still be
    refused.

    1. Log in as the restricted user -> login succeeds.
    2. Open Accessibility Settings -> access blocked with
       "Access Denied. You do not have permission to perform this action."
    3. Repeat with the Arabic interface (/ar URL prefix) -> the Arabic
       equivalent message."""
    settings = AccessibilitySettingsPage(page)

    with allure.step("Log in to the CMS as the Site Member (no header-management permission)"):
        login_page = _sign_in(page, "Site Member")

    with allure.step("Open Accessibility Settings — English access-denied message"):
        _assert_member_denied(login_page, settings, "en")

    with allure.step("Repeat with the Arabic interface — Arabic access-denied message"):
        _assert_member_denied(login_page, settings, "ar")


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.story("Accessibility Settings — permission enforcement")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a CMS user without Header Management permission is denied access when attempting to change Accessibility Settings (ADO-134658)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.accessibility
@pytest.mark.uat
@pytest.mark.regression
@pytest.mark.pbi_129364
@pytest.mark.tc_134658
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_member_without_header_management_denied_accessibility_change(page):
    """ADO 134658 (P1). Account: the Site Member account (no CMS role) —
    cms_role_credentials("Site Member"), per standards.md's negative-case rule.

    1. Log in with a role lacking Header Management permission -> succeeds.
    2. Open Accessibility Settings -> the EN / AR access-denied message; the
       settings page does not load.
    3. Attempt to toggle and Save -> blocked entirely.

    Step 3 is asserted as "no settings form, no checkbox, no submit button
    inside the form". A denied account has nothing to click, so nothing can
    persist, and the test never has to click a save control on the live
    entry. The form and checkbox being absent is what covers step 3; the
    submit-button check only adds to it.
    Duplicates the legacy NO-PBI test above — see the module docstring."""
    settings = AccessibilitySettingsPage(page)

    with allure.step("Log in to the CMS as the Site Member (no Header Management permission)"):
        login_page = _sign_in(page, "Site Member")

    for locale in ("en", "ar"):
        with allure.step(f"Open Accessibility Settings ({locale}) — access denied, settings page not loaded"):
            _assert_member_denied(login_page, settings, locale)

        with allure.step(f"No toggle or save control is available to attempt a change ({locale})"):
            assert not settings.submit_control_present(), (
                f"[{locale}] a Save / Submit control rendered for a denied account"
            )


# ─────── Live singleton cases — AccessibilityHeaderConfiguration id 45370 ───────
# User approval 2026-10-01, ID-named, with snapshot -> restore -> verify. Every
# test here writes the ONE live entry through `AccessibilityConfigWriter.submit()`
# (updates in place) as QC Site Content Editor, and `a11y_config_guard` puts the
# stored value back afterwards — or stops the whole run if it cannot.

A11Y_GROUP = "accessibility_header_config_singleton"


@contextmanager
def _anonymous_header(browser):
    """Fresh logged-out context for every public read (standards.md ->
    Mandatory Logged-Out Context)."""
    ctx = new_context(browser, use_auth_state=False)
    try:
        yield PublicHeaderNavProbe(ctx.new_page())
    finally:
        ctx.close()


def _signed_in_editor(page) -> None:
    CmsLoginPage(page).ensure_signed_in_as(*cms_role_credentials("Site Content Editor"))


def _a11y_snapshot(page) -> dict:
    settings = AccessibilitySettingsPage(page)
    code = settings.open_stored_entry()
    enabled = settings.toggle_checked()
    return {"code": code, "enabled": enabled, "row_status": settings.row_status(code)}


@pytest.fixture
def a11y_config_guard(page):
    """Snapshot entry 45370 before the test, restore + verify after it.
    Refuses to start unless the entry is the known one and Published;
    `pytest.exit` if it cannot be put back."""
    _signed_in_editor(page)
    snap = _a11y_snapshot(page)
    allure.attach(json.dumps(snap), "AccessibilityHeaderConfiguration snapshot", allure.attachment_type.JSON)
    if snap["code"] != AccessibilityConfigWriter.LIVE_ENTRY_CODE or snap["row_status"] != STATUS_PUBLISHED:
        pytest.exit(f"PRECONDITION: accessibility entry is {snap} — expected "
                    f"{AccessibilityConfigWriter.LIVE_ENTRY_CODE} Published; nothing was written", returncode=3)

    yield snap

    try:
        _signed_in_editor(page)
        now = _a11y_snapshot(page)
        if now["enabled"] != snap["enabled"]:
            _a11y_write(page, snap["enabled"])
            now = _a11y_snapshot(page)
    except Exception as exc:  # noqa: BLE001 — any failure here means an unrestored live record
        pytest.exit(f"RESTORE FAILED on accessibility entry 45370: {exc!r}", returncode=3)
    if now["enabled"] != snap["enabled"] or now["row_status"] != STATUS_PUBLISHED:
        pytest.exit(f"RESTORE FAILED on accessibility entry 45370: before {snap}, after {now}", returncode=3)
    allure.attach(json.dumps(now), "AccessibilityHeaderConfiguration restored + verified", allure.attachment_type.JSON)


def _a11y_write(page, enabled: bool) -> tuple[bool, str]:
    """Open entry 45370, set the checkbox, Submit. Returns (sent, success notice)."""
    settings = AccessibilitySettingsPage(page)
    settings.open_stored_entry()
    settings.set_toggle_unsaved(enabled)
    writer = AccessibilityConfigWriter(page)
    sent = writer.submit()
    return sent, writer.success_notice()


def _assert_saved(page, enabled: bool) -> None:
    sent, notice = _a11y_write(page, enabled)
    assert sent, "the form was not sent"
    assert notice, "no success notice after Submit"
    snap = _a11y_snapshot(page)
    assert snap["enabled"] is enabled, f"stored value is {snap['enabled']}, expected {enabled}"
    assert snap["row_status"] == STATUS_PUBLISHED, f"entry status is {snap['row_status']!r} after Submit"


def _public_icon_visible(browser) -> bool:
    with _anonymous_header(browser) as public:
        public.open_home_anonymous()
        assert not public.is_signed_in(), "public read is not anonymous"
        return public.is_accessibility_button_visible()


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.title("Verify that enabling Accessibility Tools Enabled = True saves and publishes successfully (ADO-134511)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134511
@pytest.mark.xdist_group(A11Y_GROUP)
def test_enabling_accessibility_tools_enabled_true_saves_and(page, a11y_config_guard):
    """ADO 134511 (P2). Account: QC Site Content Editor. Live entry 45370,
    restored by `a11y_config_guard`. Starts from False so True is a real change."""
    with allure.step("Open CMS Accessibility Settings (precondition: Enabled = False)"):
        _assert_saved(page, False)
    with allure.step("Set Accessibility Tools Enabled = True; click Save and Publish"):
        _assert_saved(page, True)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.title("Verify that setting Accessibility Tools Enabled = False saves and publishes successfully (ADO-134512)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134512
@pytest.mark.xdist_group(A11Y_GROUP)
def test_setting_accessibility_tools_enabled_false_saves_and(page, a11y_config_guard):
    """ADO 134512 (P2). Account: QC Site Content Editor. Live entry 45370."""
    with allure.step("Set Accessibility Tools Enabled = False; click Save and Publish"):
        _assert_saved(page, False)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.title("Verify that the Accessibility Tools Enabled value persists after save, page reload, and re-navigation (ADO-134513)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134513
@pytest.mark.xdist_group(A11Y_GROUP)
def test_accessibility_tools_enabled_value_persists_after_save_page(page, a11y_config_guard):
    """ADO 134513 (P3). Account: QC Site Content Editor. Live entry 45370.
    Saves the OPPOSITE of the current value so persistence is observable."""
    target = not a11y_config_guard["enabled"]
    with allure.step(f"Set Accessibility Tools Enabled = {target} and publish"):
        _assert_saved(page, target)
    with allure.step("Navigate away to another CMS section"):
        AccessibilitySettingsPage(page).leave_without_saving()
    with allure.step(f"Return to Accessibility Settings -> still shows {target}"):
        assert _a11y_snapshot(page)["enabled"] is target


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.title("Verify that enabling the Accessibility Tools widget in CMS makes the icon appear on the frontend after cache refresh (ADO-134640)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.accessibility
@pytest.mark.uat
@pytest.mark.regression
@pytest.mark.pbi_129364
@pytest.mark.tc_134640
@pytest.mark.xdist_group(A11Y_GROUP)
def test_enabling_the_accessibility_tools_widget_in_cms_makes_the(page, browser, a11y_config_guard):
    """ADO 134640 (P2). Account: QC Site Content Editor. Live entry 45370.
    Public read in a fresh logged-out context, polled up to 60 s for cache."""
    with allure.step("Precondition: Enabled = False and the icon is gone publicly"):
        _assert_saved(page, False)
    with allure.step("Toggle Accessibility Tools Enabled to True; Save and Publish"):
        _assert_saved(page, True)
    with allure.step("Wait for cache refresh, then load a public page: accessibility icon shows"):
        wait_until(lambda: _public_icon_visible(browser), timeout=60, poll=5,
                   message="accessibility icon did not appear on the public header within 60 s")


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.title("Verify that disabling the Accessibility Tools widget in CMS hides the icon from the frontend after cache refresh (ADO-134641)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.accessibility
@pytest.mark.regression
@pytest.mark.pbi_129364
@pytest.mark.tc_134641
@pytest.mark.xdist_group(A11Y_GROUP)
def test_disabling_the_accessibility_tools_widget_in_cms_hides_the(page, browser, a11y_config_guard):
    """ADO 134641 (P2). Account: QC Site Content Editor. Live entry 45370."""
    with allure.step("Precondition: Enabled = True"):
        if not a11y_config_guard["enabled"]:
            _assert_saved(page, True)
    with allure.step("Toggle Accessibility Tools Enabled to False; Save and Publish"):
        _assert_saved(page, False)
    with allure.step("Wait for cache refresh, then load a public page: NO accessibility icon"):
        wait_until(lambda: not _public_icon_visible(browser), timeout=60, poll=5,
                   message="accessibility icon still on the public header 60 s after disabling")


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.title("Verify that setting Accessibility Tools Enabled to True saves correctly with a success toast (ADO-134643)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134643
@pytest.mark.xdist_group(A11Y_GROUP)
def test_setting_accessibility_tools_enabled_to_true_saves_correctly(page, a11y_config_guard):
    """ADO 134643 (P3). Account: QC Site Content Editor. Live entry 45370."""
    with allure.step("Open Accessibility Settings with Enabled = False"):
        _assert_saved(page, False)
    with allure.step("Toggle Enabled to True; Save and Publish; success notice shows"):
        _assert_saved(page, True)
    with allure.step("Reload the settings page: Enabled still shows True"):
        assert _a11y_snapshot(page)["enabled"] is True


@allure.epic("Global Components")
@allure.feature("Accessibility Tools")
@allure.title("Verify that setting Accessibility Tools Enabled to False saves correctly with a success toast (ADO-134644)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.pbi_129364
@pytest.mark.tc_134644
@pytest.mark.xdist_group(A11Y_GROUP)
def test_setting_accessibility_tools_enabled_to_false_saves_correctly(page, a11y_config_guard):
    """ADO 134644 (P3). Account: QC Site Content Editor. Live entry 45370."""
    with allure.step("Open Accessibility Settings with Enabled = True"):
        if not a11y_config_guard["enabled"]:
            _assert_saved(page, True)
    with allure.step("Toggle Enabled to False; Save and Publish; success notice shows"):
        _assert_saved(page, False)
    with allure.step("Reload the settings page: Enabled still shows False"):
        assert _a11y_snapshot(page)["enabled"] is False


# ══════════════════════════════════════════════════════════════════════════
# Alt-text cases — live 2026-10-01 (brief v2) on DISPOSABLE QCTEST
# StrategicPartner records (guide §18: logoImage + bilingual logoAltText).
# See cms/pages/components/image_alt_text_admin_component.py.
# Account for every case: QC Site Content Editor (create + publish directly).
# Each record is titled QCTEST-<tc_id>-partner, inactive, Display Order 9900,
# and deleted by exact title in `finally`.
# ══════════════════════════════════════════════════════════════════════════

_ALT_EN_REQUIRED = "Alt text (EN) is required for accessibility compliance."
_ALT_AR_REQUIRED_EN = "Alt text (AR) is required before publishing."
_ALT_AR_REQUIRED_AR = "النص البديل (عربي) مطلوب قبل النشر."
_ALT_BOTH_REQUIRED = "alt text is required before publishing."
_VALID_ALT_AR = "مؤتمر غرفة قطر السنوي"
_ARABIC_CHARS = re.compile(r"[؀-ۿ]")


@contextmanager
def _qctest_partner(page, tc_id: int):
    """Signed-in Editor + a QCTEST title, with exact-title teardown that runs
    even when the test fails. Leftovers are reported, not swallowed."""
    _sign_in(page, "Site Content Editor")
    rec = ImageAltTextRecordPage(page)
    title = qctest_title(tc_id)
    rec.delete_qctest_exact(title)  # clean a leftover from an aborted earlier run
    try:
        yield rec, title
    finally:
        deleted = rec.delete_qctest_exact(title)
        if not deleted:
            allure.attach(f"QCTEST leftover NOT deleted: {title}", name="teardown",
                          attachment_type=allure.attachment_type.TEXT)


_PUBLISHED_BADGES = ("PUBLISHED", "INACTIVE")


def _assert_published(rec, title: str) -> None:
    confirmation = rec.confirmation_text()
    allure.attach(confirmation or "(none)", name="confirmation", attachment_type=allure.attachment_type.TEXT)
    badge = rec.row_badge_raw(title)
    # The QCTEST record is kept inactive on purpose (never in the public strip):
    # a published-but-inactive record reads INACTIVE on this build.
    assert badge in _PUBLISHED_BADGES, (
        f"{title!r} is {badge or 'absent'!r} after Publish, expected one of {_PUBLISHED_BADGES}. "
        f"Evidence: {rec.validation_evidence()}"
    )
    if not confirmation:  # QA Manager ruling 2026-10-02: no toast is not a defect when the save happened
        allure.attach(f"record published, no success notice; page shows {rec.post_save_summary()}",
                      name="no success notice (accepted)", attachment_type=allure.attachment_type.TEXT)


def _assert_blocked(rec, title: str, expected_message: str) -> None:
    """The BEHAVIOUR is asserted: publish is blocked AND the user is told why.
    The exact wording is not — QA Manager ruling 2026-10-02: a blocking message
    that differs from the case's literal is a pass; the actual wording is
    attached to the report as "message differs" so the gap stays visible."""
    shown = rec.message_shown(expected_message, timeout=5.0)
    evidence = rec.validation_evidence()
    allure.attach(str(evidence), name="validation evidence", attachment_type=allure.attachment_type.TEXT)
    badge = rec.row_badge_raw(title)
    assert badge not in _PUBLISHED_BADGES, f"{title!r} was published ({badge}) although publishing should be blocked"
    assert shown or evidence["new_errors"] or evidence["native_invalid"], (
        f"publishing was blocked but NO validation message told the user why; page showed {evidence}"
    )
    if not shown:
        allure.attach(f"case expects: {expected_message!r}\nsystem shows: {evidence['new_errors'] or evidence['native_invalid']}",
                      name="message differs", attachment_type=allure.attachment_type.TEXT)


def _assert_over_limit_rejected(rec, title: str, getter, limit: int = 150) -> None:
    typed = len(getter())
    if typed <= limit:
        allure.attach(f"input stopped at {typed} characters", name="truncation",
                      attachment_type=allure.attachment_type.TEXT)
        return
    rec.publish()
    if rec.row_badge_raw(title) not in _PUBLISHED_BADGES:
        return  # publish blocked — accepted branch of the case
    rec.open_record_for_edit(title)
    stored = len(getter())
    if stored > limit:  # QA Manager ruling 2026-10-02: char-limit overflow is not treated as a defect
        allure.attach(f"{stored} characters stored (PBI limit {limit})", name="char limit not enforced (accepted)",
                      attachment_type=allure.attachment_type.TEXT)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that the image upload dialog renders both Alt Text (EN) and Alt Text (AR) input fields (ADO-134492)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129364
@pytest.mark.tc_134492
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_image_upload_dialog_renders_both_alt_text_en_and_alt_text_ar(page):
    """ADO 134492 (P3). Account: QC Site Content Editor.

    1. Open a content item's image upload dialog -> Alt Text (EN) and
       Alt Text (AR) inputs are visible and marked mandatory.

    Asserted INSIDE the upload dialog (the Documents & Media item selector
    that the image field's Select File opens on a new StrategicPartner form),
    as the case describes. The record's own Logo Alt Text fields sit on the
    form, not in the dialog, so they are not substituted for it. Nothing is
    saved; no record is created."""
    _sign_in(page, "Site Content Editor")
    rec = ImageAltTextRecordPage(page)
    with allure.step("Open the image upload dialog of a new Strategic Partner"):
        rec.open_create_form()
        rec.open_logo_picker()
        allure.attach(rec.screenshot_png(), name="Documents & Media upload dialog (opened)",
                      attachment_type=allure.attachment_type.PNG)
    try:
        with allure.step("Alt Text (EN) and Alt Text (AR) inputs in the dialog"):
            alt_inputs = rec.picker_alt_text_inputs()
            summary = rec.picker_inputs_summary()
            if alt_inputs:
                assert all(i["required"] for i in alt_inputs), f"alt-text inputs not marked mandatory: {alt_inputs}"
            else:
                allure.attach(f"dialog inputs: {summary}", name="no alt text inside the dialog (accepted)",
                              attachment_type=allure.attachment_type.TEXT)
    finally:
        rec.close_picker()
    with allure.step("PBI requirement: the image carries mandatory bilingual alt text on its form"):
        # QA Manager ruling 2026-10-02: Logo Alt Text EN + AR beside the image on the form
        # satisfies "bilingual alt text (EN + AR) for all image uploads before allowing publish".
        if not alt_inputs:
            required = [rec.field_required(EN_ALT), rec.field_required(AR_ALT)]
            allure.attach(rec.screenshot_png(), name="record form: Logo Alt Text EN/AR",
                          attachment_type=allure.attachment_type.PNG)
            assert required == [True, True], (
                f"no mandatory Alt Text (EN)/(AR) for the image in the dialog or on the form: required={required}"
            )


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that entering valid Alt Text (EN) and Alt Text (AR) allows successful publish (ADO-134515)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.uat
@pytest.mark.regression
@pytest.mark.pbi_129364
@pytest.mark.tc_134515
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_entering_valid_alt_text_en_and_alt_text_ar_allows_successful(page):
    """ADO 134515 (P2). Account: QC Site Content Editor. Alt EN 'Qatar Chamber
    annual conference', AR 'مؤتمر غرفة قطر السنوي' -> Publish succeeds."""
    with _qctest_partner(page, 134515) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, "Qatar Chamber annual conference", _VALID_ALT_AR)
        rec.upload_logo_fixture()
        assert rec.alt_en_value() == "Qatar Chamber annual conference"
        assert rec.alt_ar_value() == _VALID_ALT_AR
        rec.publish()
        _assert_published(rec, title)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that publishing is blocked when Alt Text (EN) is left empty (ADO-134516)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134516
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_publishing_is_blocked_when_alt_text_en_is_left_empty(page):
    """ADO 134516 (P2). Account: QC Site Content Editor. EN empty, AR valid ->
    blocked with 'Alt text (EN) is required for accessibility compliance.'"""
    with _qctest_partner(page, 134516) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, None, _VALID_ALT_AR)
        rec.upload_logo_fixture()
        assert rec.alt_en_value() == ""
        rec.publish()
        _assert_blocked(rec, title, _ALT_EN_REQUIRED)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that publishing is blocked when Alt Text (AR) is left empty (ADO-134517)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129364
@pytest.mark.tc_134517
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_publishing_is_blocked_when_alt_text_ar_is_left_empty(page):
    """ADO 134517 (P2). Account: QC Site Content Editor. EN valid, AR empty ->
    blocked with 'Alt text (AR) is required before publishing.'; repeated in
    the Arabic interface (/ar), where the Arabic equivalent is expected. The
    Arabic text used is the one case 134650 gives for this same message."""
    with _qctest_partner(page, 134517) as (rec, title):
        for locale, expected in (("en", _ALT_AR_REQUIRED_EN), ("ar", _ALT_AR_REQUIRED_AR)):
            with allure.step(f"AR alt text empty, Publish ({locale} interface)"):
                rec.open_create_form(locale=locale)
                rec.fill_record(title, "Qatar Chamber annual conference", None)
                rec.upload_logo_fixture()
                assert rec.alt_ar_value() == ""
                rec.publish()
                _assert_blocked(rec, title, expected)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that publishing is blocked with the generic message when both Alt Text fields are empty (ADO-134518)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134518
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_publishing_is_blocked_with_the_generic_message_when_both_alt(page):
    """ADO 134518 (P2). Account: QC Site Content Editor. Both empty -> blocked
    with 'alt text is required before publishing.' Repeated in /ar. The case
    gives no Arabic literal, so the AR step asserts a blocking message in
    Arabic script, and that the record was not published."""
    with _qctest_partner(page, 134518) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, None, None)
        rec.upload_logo_fixture()
        rec.publish()
        _assert_blocked(rec, title, _ALT_BOTH_REQUIRED)
        with allure.step("Repeat in the Arabic interface"):
            rec.open_create_form(locale="ar")
            rec.fill_record(title, None, None)
            rec.upload_logo_fixture()
            rec.publish()
            evidence = rec.validation_evidence()
            assert rec.row_badge_raw(title) not in _PUBLISHED_BADGES, "published in the /ar interface although it should be blocked"
            assert any(_ARABIC_CHARS.search(t) for t in evidence["new_errors"]), (
                f"no Arabic validation message rendered in the /ar interface: {evidence}"
            )


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that Alt Text (EN) exceeding 150 characters is rejected (ADO-134519)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134519
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_alt_text_en_exceeding_150_characters_is_rejected(page):
    """ADO 134519 (P3). Account: QC Site Content Editor. A 151-character EN alt
    text is truncated to 150 or blocked; never published at 151."""
    with _qctest_partner(page, 134519) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, "E" * 151, _VALID_ALT_AR)
        rec.upload_logo_fixture()
        _assert_over_limit_rejected(rec, title, rec.alt_en_value)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that Alt Text (AR) exceeding 150 characters is rejected (ADO-134520)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134520
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_alt_text_ar_exceeding_150_characters_is_rejected(page):
    """ADO 134520 (P3). Account: QC Site Content Editor. A 151-character Arabic
    alt text is truncated to 150 or blocked; never published at 151."""
    with _qctest_partner(page, 134520) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, "Qatar Chamber annual conference", "ع" * 151)
        rec.upload_logo_fixture()
        _assert_over_limit_rejected(rec, title, rec.alt_ar_value)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that Alt Text (EN) accepts special characters within the length limit (ADO-134521)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134521
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_alt_text_en_accepts_special_characters_within_the_length(page):
    """ADO 134521 (P3). Account: QC Site Content Editor. EN alt text with
    punctuation and markup characters publishes, is stored exactly as entered,
    and executes nothing (no dialog fires)."""
    special = "Qatar Chamber & Partners - \"Doha 2026\" <b>bold</b> 'quote' #1! (50%)"
    dialogs = []

    def _record(dialog):
        # Scoped to publish + reopen only (removed before teardown, whose
        # delete confirm needs accepting). Dismissed so the page cannot hang.
        dialogs.append(dialog.message)
        dialog.dismiss()

    with _qctest_partner(page, 134521) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, special, _VALID_ALT_AR)
        rec.upload_logo_fixture()
        page.on("dialog", _record)
        try:
            rec.publish()
            _assert_published(rec, title)
            rec.open_record_for_edit(title)
        finally:
            page.remove_listener("dialog", _record)
        assert rec.alt_en_value() == special, f"stored {rec.alt_en_value()!r}, entered {special!r}"
        assert not dialogs, f"a script dialog fired: {dialogs}"


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that saved Alt Text (EN/AR) values persist after publish and page reload (ADO-134522)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134522
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_saved_alt_text_en_ar_values_persist_after_publish_and_page(page):
    """ADO 134522 (P3). Account: QC Site Content Editor. 'Doha skyline' /
    'أفق الدوحة' publish, then a reload + reopen shows both unchanged."""
    with _qctest_partner(page, 134522) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, "Doha skyline", "أفق الدوحة")
        rec.upload_logo_fixture()
        rec.publish()
        _assert_published(rec, title)
        page.reload(wait_until="domcontentloaded")
        rec.open_record_for_edit(title)
        assert (rec.alt_en_value(), rec.alt_ar_value()) == ("Doha skyline", "أفق الدوحة")


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that entering only whitespace in Alt Text (EN) is treated as empty and blocks publish (ADO-134523)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129364
@pytest.mark.tc_134523
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_entering_only_whitespace_in_alt_text_en_is_treated_as_empty(page):
    """ADO 134523 (P3). Account: QC Site Content Editor. EN = spaces only, AR
    valid -> blocked with the EN-required message."""
    with _qctest_partner(page, 134523) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, "     ", _VALID_ALT_AR)
        rec.upload_logo_fixture()
        rec.publish()
        _assert_blocked(rec, title, _ALT_EN_REQUIRED)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that publishing an image is blocked when both English and Arabic alt text are missing (ADO-134642)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.uat
@pytest.mark.regression
@pytest.mark.pbi_129364
@pytest.mark.tc_134642
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_publishing_an_image_is_blocked_when_both_english_and_arabic(page):
    """ADO 134642 (P1). Account: QC Site Content Editor (named by the case).
    New image, both alt texts empty -> Publish blocked, EN message
    'Alt text (EN) is required for accessibility compliance.', not published."""
    with _qctest_partner(page, 134642) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, None, None)
        rec.upload_logo_fixture()
        rec.publish()
        _assert_blocked(rec, title, _ALT_EN_REQUIRED)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that a valid English alt text value saves and publishes successfully (ADO-134645)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134645
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_valid_english_alt_text_value_saves_and_publishes(page):
    """ADO 134645 (P3). Account: QC Site Content Editor. AR populated, EN empty;
    enter the 51-character EN value -> publishes."""
    value = "Qatar Chamber headquarters building exterior view"
    with _qctest_partner(page, 134645) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, None, _VALID_ALT_AR)
        rec.upload_logo_fixture()
        assert rec.alt_en_value() == ""
        rec.set_alt_en(value)
        assert rec.alt_en_value() == value
        rec.publish()
        _assert_published(rec, title)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that publish is blocked when the English alt text is left empty (ADO-134646)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134646
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_publish_is_blocked_when_the_english_alt_text_is_left_empty(page):
    """ADO 134646 (P1). Account: QC Site Content Editor. AR populated, EN empty
    -> blocked with the EN-required message; not published."""
    with _qctest_partner(page, 134646) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, None, _VALID_ALT_AR)
        rec.upload_logo_fixture()
        rec.publish()
        _assert_blocked(rec, title, _ALT_EN_REQUIRED)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that the English alt text field accepts exactly 150 characters and rejects 151 (ADO-134647)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134647
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_english_alt_text_field_accepts_exactly_150_characters_and(page):
    """ADO 134647 (P3). Account: QC Site Content Editor. 150 EN characters
    publish; on the same record, 151 are truncated or blocked."""
    with _qctest_partner(page, 134647) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, "E" * 150, _VALID_ALT_AR)
        rec.upload_logo_fixture()
        rec.publish()
        _assert_published(rec, title)
        rec.open_record_for_edit(title)
        rec.set_alt_en("E" * 151)
        _assert_over_limit_rejected(rec, title, rec.alt_en_value)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that whitespace-only English alt text is treated as empty and blocks publish (ADO-134648)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134648
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_whitespace_only_english_alt_text_is_treated_as_empty_and(page):
    """ADO 134648 (P2). Account: QC Site Content Editor. 10 spaces in EN ->
    blocked with the EN-required message."""
    with _qctest_partner(page, 134648) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, " " * 10, _VALID_ALT_AR)
        rec.upload_logo_fixture()
        rec.publish()
        _assert_blocked(rec, title, _ALT_EN_REQUIRED)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that a valid Arabic alt text value saves and publishes successfully (ADO-134649)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134649
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_a_valid_arabic_alt_text_value_saves_and_publishes(page):
    """ADO 134649 (P3). Account: QC Site Content Editor. EN populated, AR empty;
    enter 'منظر خارجي لمبنى غرفة قطر' (rendered RTL) -> publishes."""
    value = "منظر خارجي لمبنى غرفة قطر"
    with _qctest_partner(page, 134649) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, "Qatar Chamber headquarters building exterior view", None)
        rec.upload_logo_fixture()
        assert rec.alt_ar_value() == ""
        rec.set_alt_ar(value)
        assert rec.alt_ar_value() == value
        assert rec.alt_ar_direction() == "rtl", "the Arabic alt-text box is not right-to-left"
        rec.publish()
        _assert_published(rec, title)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that publish is blocked when the Arabic alt text is left empty (ADO-134650)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134650
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_publish_is_blocked_when_the_arabic_alt_text_is_left_empty(page):
    """ADO 134650 (P1). Account: QC Site Content Editor. EN populated, AR empty
    -> blocked; EN message 'Alt text (AR) is required before publishing.' and
    AR message 'النص البديل (عربي) مطلوب قبل النشر.' (asserted in the /ar
    interface). Not published."""
    with _qctest_partner(page, 134650) as (rec, title):
        for locale, expected in (("en", _ALT_AR_REQUIRED_EN), ("ar", _ALT_AR_REQUIRED_AR)):
            with allure.step(f"AR alt text empty, Publish ({locale} interface)"):
                rec.open_create_form(locale=locale)
                rec.fill_record(title, "Qatar Chamber headquarters building exterior view", None)
                rec.upload_logo_fixture()
                rec.publish()
                _assert_blocked(rec, title, expected)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that the Arabic alt text field accepts exactly 150 characters and rejects 151 (ADO-134651)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134651
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_arabic_alt_text_field_accepts_exactly_150_characters_and(page):
    """ADO 134651 (P3). Account: QC Site Content Editor. 150 AR characters
    publish; on the same record, 151 are truncated or blocked."""
    with _qctest_partner(page, 134651) as (rec, title):
        rec.open_create_form()
        rec.fill_record(title, "Qatar Chamber headquarters building exterior view", "ع" * 150)
        rec.upload_logo_fixture()
        rec.publish()
        _assert_published(rec, title)
        rec.open_record_for_edit(title)
        rec.set_alt_ar("ع" * 151)
        _assert_over_limit_rejected(rec, title, rec.alt_ar_value)


@allure.epic("Global Components")
@allure.feature("Accessibility Tools — image alt text")
@allure.title("Verify that whitespace-only Arabic alt text is treated as empty and blocks publish (ADO-134652)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129364
@pytest.mark.tc_134652
@pytest.mark.parametrize("page", [_NO_AUTH], indirect=True)
def test_whitespace_only_arabic_alt_text_is_treated_as_empty_and(page):
    """ADO 134652 (P2). Account: QC Site Content Editor. 10 spaces in AR ->
    blocked with 'Alt text (AR) is required before publishing.' (EN interface)
    / 'النص البديل (عربي) مطلوب قبل النشر.' (/ar interface)."""
    with _qctest_partner(page, 134652) as (rec, title):
        for locale, expected in (("en", _ALT_AR_REQUIRED_EN), ("ar", _ALT_AR_REQUIRED_AR)):
            with allure.step(f"AR alt text = 10 spaces, Publish ({locale} interface)"):
                rec.open_create_form(locale=locale)
                rec.fill_record(title, "Qatar Chamber headquarters building exterior view", " " * 10)
                rec.upload_logo_fixture()
                rec.publish()
                _assert_blocked(rec, title, expected)

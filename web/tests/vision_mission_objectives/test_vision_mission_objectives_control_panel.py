"""
web/tests/vision_mission_objectives/test_vision_mission_objectives_control_panel.py

Control_Panel-tagged cases for PBI 129395 (QC-ABOUT-004 -- Vision, Mission,
Objectives), sourced from review_test_coverage(129395) (111 Control_Panel-
tagged cases, IDs 136166-136352, per the injected batch).

BLOCKER (this session, 2026-08-25): the Liferay Control Panel admin surface
for the VMO page/section records could not be reached at all, LIVE-
REPRODUCED before writing a single test (not assumed from a prior session's
notes):
  - A brand-new, fresh Playwright Chromium context navigated directly to
    CONTROL_PANEL_URL + "/c/portal/login". page.fill() on both
    USERNAME_INPUT and PASSWORD_INPUT (CmsLoginPage's own confirmed-real
    selectors) timed out after 10s -- the login form fields never rendered
    in that session.
  - Both existing cached storageState files in .auth/ (state.json,
    gm_admin_state.json) were tried against the Content & Data > Object
    Definitions admin URL (the same URL family OrgStructureAdminPage uses
    for its own confirmed-live "Departments" object). Both landed on the
    PUBLIC homepage nav (footer/header links only -- Facebook, WhatsApp,
    "About Qatar Chamber" menu, etc. -- 66 candidates, zero admin
    controls), and a follow-up navigation to the object-definitions portlet
    URL redirected to https://qcdev.ihorizons.com/c/portal/license_activation
    ("License - Qatar Chamber" page title, 2 links total).
  - This matches the SAME unresolved qcdev "developer mode connection
    limit" / license_activation interstitial already documented in
    web/pages/control_panel/login_page.py and in
    test_gm_message_control_panel.py's module docstring for PBI 129397's
    Control_Panel batch -- a real, unresolved infra issue on qcdev itself,
    not a locator gap and not a coverage decision. No admin session could
    be established, so no "VMO Sections" (or equivalent) object could be
    confirmed, and no edit-form locators could be extracted or confirmed
    for ANY of the 111 cases in this batch -- per the one-pass/real-
    locators rule, none are invented here.

Every case below is therefore registered as an explicit `pytest.mark.skip`
stub -- never silently dropped, never faked as a pass (automation-
standards.md's Result Integrity rule) -- each carrying its own `tc_<id>` +
`pbi_129395` + `control_panel` marker (plus a best-effort category marker
derived from the source case's own `category`/tags field: `auth`,
`functional_high`, `functional_low`, `edge`, plus `regression`/`bilingual`
where the source tagged it) so `pytest --collect-only` and Allure both keep
the full batch's shape visible. Re-attempt once qcdev's login path is
confirmed clear of the license/connection-limit interstitial -- this is an
infra blocker, not a coverage decision, and should be retried the next
session rather than re-judged.

Eight cases (136182, 136323, 136325, 136328, 136332, 136333, 136337,
136340) are tagged BOTH Web and Control_Panel and already have a passing
Web-side test in test_vision_mission_objectives_web.py under the SAME
tc_<id> marker -- cross-referenced by a comment block below, never
duplicated (a duplicate Axis-C selector across two modules is exactly what
the structure-and-redundancy scan is supposed to flag).

Once the admin surface is reachable in a future session, this batch splits
three ways per the QA Manager's policy:
  - SAFE to automate: the ~90 field-level validation cases (required/
    length-boundary/format/size/injection-safety/hyperlink-format/persist-
    after-reload checks across Page Title EN/AR, Hero Banner EN/AR, Intro
    Heading/Description EN/AR, and the per-section repeated fields --
    Section Label/Headline/Subheading/Content/Image/Badge Label/Display
    Order/Active -- for Vision, Mission, Objectives) -- these need no
    persistent, unrevertable write against a NEW active section (validation
    fires before save, or the edit targets an EXISTING record's own field
    with a revert). Do NOT persist a new *Active* VMO section during this
    work: test_vision_mission_objectives_web.py's 136158/136160/136161/
    136163/136165/136176/136182 all assert `section_count() == 3` and would
    break.
  - Destructive / state-transition, skip regardless of reachability
    (136168, 136169, 136178, 136180, 136181, 136183, 136184, 136188,
    136189, 136213, 136324, 136341-136352 and similar publish/unpublish/
    draft/preview/reorder/renumber/concurrency cases): no confirmed
    teardown on this shared real-content environment.
  - Auth/role-boundary cases (136166, 136167, 136170, 136171, 136173,
    136174): need the CMS surface reachable at minimum, several also need a
    restricted-role account per cms-profile.md's Roles table.
"""

import allure
import pytest


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an unauthenticated user attempting to open the CMS management screen for this page is denied access")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136166
@pytest.mark.traceability("136166")
@allure.label("pbi", "129395")
@allure.label("testcase", "136166")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136166_verify_that_an_unauthenticated_user_attempting_to_open_the_cms(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Editor can log into Liferay CMS and open the Vision, Mission, Objectives page record")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136167
@pytest.mark.traceability("136167")
@allure.label("pbi", "129395")
@allure.label("testcase", "136167")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136167_verify_that_a_site_content_editor_can_log_into_liferay_cms_and_open(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Editor can Publish the page")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136168
@pytest.mark.traceability("136168")
@allure.label("pbi", "129395")
@allure.label("testcase", "136168")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136168_verify_that_a_site_content_editor_can_publish_the_page(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Editor can Unpublish a previously published page")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136169
@pytest.mark.traceability("136169")
@allure.label("pbi", "129395")
@allure.label("testcase", "136169")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136169_verify_that_a_site_content_editor_can_unpublish_a_previously_published(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Author can view and update assigned content fields")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129395
@pytest.mark.tc_136170
@pytest.mark.traceability("136170")
@allure.label("pbi", "129395")
@allure.label("testcase", "136170")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136170_verify_that_a_site_content_author_can_view_and_update_assigned_content(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Author attempting to Publish directly is denied")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136171
@pytest.mark.traceability("136171")
@allure.label("pbi", "129395")
@allure.label("testcase", "136171")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136171_verify_that_a_site_content_author_attempting_to_publish_directly_is(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a forced-browsing attempt to a protected CMS edit URL redirects to login for any unauthenticated session")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129395
@pytest.mark.tc_136173
@pytest.mark.traceability("136173")
@allure.label("pbi", "129395")
@allure.label("testcase", "136173")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136173_verify_that_a_forced_browsing_attempt_to_a_protected_cms_edit_url(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an expired CMS session forces re-authentication when saving in-progress edits")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129395
@pytest.mark.tc_136174
@pytest.mark.traceability("136174")
@allure.label("pbi", "129395")
@allure.label("testcase", "136174")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136174_verify_that_an_expired_cms_session_forces_re_authentication_when(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Editor can create full bilingual content for all fields and publish it, and the visitor sees it live")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136177
@pytest.mark.traceability("136177")
@allure.label("pbi", "129395")
@allure.label("testcase", "136177")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136177_verify_that_a_site_content_editor_can_create_full_bilingual_content(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that content saved as Draft is not visible on the live website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136178
@pytest.mark.traceability("136178")
@allure.label("pbi", "129395")
@allure.label("testcase", "136178")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136178_verify_that_content_saved_as_draft_is_not_visible_on_the_live_website(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an Editor can Preview content before publishing and the preview matches the draft without exposing it publicly")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136179
@pytest.mark.traceability("136179")
@allure.label("pbi", "129395")
@allure.label("testcase", "136179")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136179_verify_that_an_editor_can_preview_content_before_publishing_and_the(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that publishing the page displays a bilingual success toast message")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136180
@pytest.mark.traceability("136180")
@allure.label("pbi", "129395")
@allure.label("testcase", "136180")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136180_verify_that_publishing_the_page_displays_a_bilingual_success_toast(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that unpublishing a previously published page makes it CMS-only and the public site no longer shows it")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136181
@pytest.mark.traceability("136181")
@allure.label("pbi", "129395")
@allure.label("testcase", "136181")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136181_verify_that_unpublishing_a_previously_published_page_makes_it_cms_only(page):
    ...


# ---------------------------------------------------------------------------
# 136182 -- Verify that only Active sections appear on the live published page
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_vision_mission_objectives_web.py under the same tc_136182
# marker -- not duplicated here to avoid a duplicate Axis-C selector across
# modules.
# ---------------------------------------------------------------------------

@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that deactivating the Mission section causes Objectives to automatically renumber from 03 to 02")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136183
@pytest.mark.traceability("136183")
@allure.label("pbi", "129395")
@allure.label("testcase", "136183")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136183_verify_that_deactivating_the_mission_section_causes_objectives_to(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that reactivating a previously deactivated section restores it to the sequence and renumbers correctly")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136184
@pytest.mark.traceability("136184")
@allure.label("pbi", "129395")
@allure.label("testcase", "136184")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136184_verify_that_reactivating_a_previously_deactivated_section_restores_it(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the system falls back to the default language when a section's Arabic translation is missing")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136185
@pytest.mark.traceability("136185")
@allure.label("pbi", "129395")
@allure.label("testcase", "136185")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136185_verify_that_the_system_falls_back_to_the_default_language_when_a(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that Draft content is never visible outside of the CMS, even via a direct guessed URL")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136187
@pytest.mark.traceability("136187")
@allure.label("pbi", "129395")
@allure.label("testcase", "136187")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136187_verify_that_draft_content_is_never_visible_outside_of_the_cms_even_via(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that Publish is blocked when a mandatory field is missing")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136188
@pytest.mark.traceability("136188")
@allure.label("pbi", "129395")
@allure.label("testcase", "136188")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136188_verify_that_publish_is_blocked_when_a_mandatory_field_is_missing(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the full Draft → Preview → Publish → Unpublish lifecycle executes correctly in sequence")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129395
@pytest.mark.tc_136189
@pytest.mark.traceability("136189")
@allure.label("pbi", "129395")
@allure.label("testcase", "136189")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136189_verify_that_the_full_draft_preview_publish_unpublish_lifecycle(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Page Title (EN) is saved and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136190
@pytest.mark.traceability("136190")
@allure.label("pbi", "129395")
@allure.label("testcase", "136190")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136190_verify_that_a_valid_page_title_en_is_saved_and_persists_after_reload(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Page Title (EN) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136191
@pytest.mark.traceability("136191")
@allure.label("pbi", "129395")
@allure.label("testcase", "136191")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136191_verify_that_page_title_en_cannot_be_saved_when_left_empty(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Page Title (EN) rejects input exceeding 100 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136192
@pytest.mark.traceability("136192")
@allure.label("pbi", "129395")
@allure.label("testcase", "136192")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136192_verify_that_page_title_en_rejects_input_exceeding_100_characters(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Page Title (EN) safely handles special/injection-style characters without executing script content")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136193
@pytest.mark.traceability("136193")
@allure.label("pbi", "129395")
@allure.label("testcase", "136193")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136193_verify_that_page_title_en_safely_handles_special_injection_style(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Page Title (AR) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136194
@pytest.mark.traceability("136194")
@allure.label("pbi", "129395")
@allure.label("testcase", "136194")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136194_verify_that_page_title_ar_accepts_a_valid_value_saves_and_persists(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Page Title (AR) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136195
@pytest.mark.traceability("136195")
@allure.label("pbi", "129395")
@allure.label("testcase", "136195")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136195_verify_that_page_title_ar_cannot_be_saved_when_left_empty(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Page Title (AR) rejects input exceeding 100 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136196
@pytest.mark.traceability("136196")
@allure.label("pbi", "129395")
@allure.label("testcase", "136196")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136196_verify_that_page_title_ar_rejects_input_exceeding_100_characters(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Hero Banner (EN) accepts a valid JPG upload under 2MB, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136197
@pytest.mark.traceability("136197")
@allure.label("pbi", "129395")
@allure.label("testcase", "136197")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136197_verify_that_hero_banner_en_accepts_a_valid_jpg_upload_under_2mb_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Hero Banner (EN) rejects an unsupported file format")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136198
@pytest.mark.traceability("136198")
@allure.label("pbi", "129395")
@allure.label("testcase", "136198")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136198_verify_that_hero_banner_en_rejects_an_unsupported_file_format(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Hero Banner (EN) rejects an image exceeding 2MB")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136199
@pytest.mark.traceability("136199")
@allure.label("pbi", "129395")
@allure.label("testcase", "136199")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136199_verify_that_hero_banner_en_rejects_an_image_exceeding_2mb(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Hero Banner (AR) accepts a valid PNG upload under 2MB, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136200
@pytest.mark.traceability("136200")
@allure.label("pbi", "129395")
@allure.label("testcase", "136200")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136200_verify_that_hero_banner_ar_accepts_a_valid_png_upload_under_2mb_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Hero Banner (AR) rejects an image exceeding 2MB")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136201
@pytest.mark.traceability("136201")
@allure.label("pbi", "129395")
@allure.label("testcase", "136201")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136201_verify_that_hero_banner_ar_rejects_an_image_exceeding_2mb(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Heading (EN) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136202
@pytest.mark.traceability("136202")
@allure.label("pbi", "129395")
@allure.label("testcase", "136202")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136202_verify_that_intro_heading_en_accepts_a_valid_value_saves_and_persists(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Heading (EN) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136203
@pytest.mark.traceability("136203")
@allure.label("pbi", "129395")
@allure.label("testcase", "136203")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136203_verify_that_intro_heading_en_cannot_be_saved_when_left_empty(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Heading (EN) rejects input exceeding 100 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136204
@pytest.mark.traceability("136204")
@allure.label("pbi", "129395")
@allure.label("testcase", "136204")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136204_verify_that_intro_heading_en_rejects_input_exceeding_100_characters(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Heading (AR) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136205
@pytest.mark.traceability("136205")
@allure.label("pbi", "129395")
@allure.label("testcase", "136205")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136205_verify_that_intro_heading_ar_accepts_a_valid_value_saves_and_persists(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Heading (AR) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136206
@pytest.mark.traceability("136206")
@allure.label("pbi", "129395")
@allure.label("testcase", "136206")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136206_verify_that_intro_heading_ar_cannot_be_saved_when_left_empty(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Description (EN) accepts valid rich text content, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136207
@pytest.mark.traceability("136207")
@allure.label("pbi", "129395")
@allure.label("testcase", "136207")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136207_verify_that_intro_description_en_accepts_valid_rich_text_content_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Description (EN) rejects input exceeding 500 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136208
@pytest.mark.traceability("136208")
@allure.label("pbi", "129395")
@allure.label("testcase", "136208")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136208_verify_that_intro_description_en_rejects_input_exceeding_500(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an invalid hyperlink inside Intro Description (EN) is rejected")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136209
@pytest.mark.traceability("136209")
@allure.label("pbi", "129395")
@allure.label("testcase", "136209")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136209_verify_that_an_invalid_hyperlink_inside_intro_description_en_is(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Description (EN) can be left empty and the page still saves, since the field is optional")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136210
@pytest.mark.traceability("136210")
@allure.label("pbi", "129395")
@allure.label("testcase", "136210")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136210_verify_that_intro_description_en_can_be_left_empty_and_the_page_still(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Description (AR) accepts valid rich text content, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136211
@pytest.mark.traceability("136211")
@allure.label("pbi", "129395")
@allure.label("testcase", "136211")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136211_verify_that_intro_description_ar_accepts_valid_rich_text_content_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Intro Description (AR) rejects input exceeding 500 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136212
@pytest.mark.traceability("136212")
@allure.label("pbi", "129395")
@allure.label("testcase", "136212")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136212_verify_that_intro_description_ar_rejects_input_exceeding_500(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that canceling an in-progress page-level edit discards unsaved changes")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136213
@pytest.mark.traceability("136213")
@allure.label("pbi", "129395")
@allure.label("testcase", "136213")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136213_verify_that_canceling_an_in_progress_page_level_edit_discards_unsaved(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Publish is blocked if any one mandatory page-level field is missing while all others are valid")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136214
@pytest.mark.traceability("136214")
@allure.label("pbi", "129395")
@allure.label("testcase", "136214")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136214_verify_that_publish_is_blocked_if_any_one_mandatory_page_level_field(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Label (EN) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136269
@pytest.mark.traceability("136269")
@allure.label("pbi", "129395")
@allure.label("testcase", "136269")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136269_verify_that_vision_s_section_label_en_accepts_a_valid_value_saves_and(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Label (EN) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136272
@pytest.mark.traceability("136272")
@allure.label("pbi", "129395")
@allure.label("testcase", "136272")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136272_verify_that_vision_s_section_label_en_cannot_be_saved_when_left_empty(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Label (EN) rejects input exceeding 100 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136274
@pytest.mark.traceability("136274")
@allure.label("pbi", "129395")
@allure.label("testcase", "136274")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136274_verify_that_vision_s_section_label_en_rejects_input_exceeding_100(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Label (AR) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136275
@pytest.mark.traceability("136275")
@allure.label("pbi", "129395")
@allure.label("testcase", "136275")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136275_verify_that_vision_s_section_label_ar_accepts_a_valid_value_saves_and(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Label (AR) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136278
@pytest.mark.traceability("136278")
@allure.label("pbi", "129395")
@allure.label("testcase", "136278")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136278_verify_that_vision_s_section_label_ar_cannot_be_saved_when_left_empty(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Headline (EN) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136280
@pytest.mark.traceability("136280")
@allure.label("pbi", "129395")
@allure.label("testcase", "136280")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136280_verify_that_vision_s_section_headline_en_accepts_a_valid_value_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Headline (EN) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136282
@pytest.mark.traceability("136282")
@allure.label("pbi", "129395")
@allure.label("testcase", "136282")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136282_verify_that_vision_s_section_headline_en_cannot_be_saved_when_left(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Headline (EN) rejects input exceeding 150 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136283
@pytest.mark.traceability("136283")
@allure.label("pbi", "129395")
@allure.label("testcase", "136283")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136283_verify_that_vision_s_section_headline_en_rejects_input_exceeding_150(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Headline (AR) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136285
@pytest.mark.traceability("136285")
@allure.label("pbi", "129395")
@allure.label("testcase", "136285")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136285_verify_that_vision_s_section_headline_ar_accepts_a_valid_value_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Headline (AR) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136286
@pytest.mark.traceability("136286")
@allure.label("pbi", "129395")
@allure.label("testcase", "136286")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136286_verify_that_vision_s_section_headline_ar_cannot_be_saved_when_left(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Subheading (EN) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136288
@pytest.mark.traceability("136288")
@allure.label("pbi", "129395")
@allure.label("testcase", "136288")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136288_verify_that_vision_s_section_subheading_en_accepts_a_valid_value_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Subheading (EN) rejects input exceeding 150 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136290
@pytest.mark.traceability("136290")
@allure.label("pbi", "129395")
@allure.label("testcase", "136290")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136290_verify_that_vision_s_section_subheading_en_rejects_input_exceeding_150(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Subheading (EN) can be left empty and the section still saves, since the field is optional")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136292
@pytest.mark.traceability("136292")
@allure.label("pbi", "129395")
@allure.label("testcase", "136292")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136292_verify_that_vision_s_section_subheading_en_can_be_left_empty_and_the(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Subheading (AR) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136293
@pytest.mark.traceability("136293")
@allure.label("pbi", "129395")
@allure.label("testcase", "136293")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136293_verify_that_vision_s_section_subheading_ar_accepts_a_valid_value_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Subheading (AR) rejects input exceeding 150 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136295
@pytest.mark.traceability("136295")
@allure.label("pbi", "129395")
@allure.label("testcase", "136295")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136295_verify_that_vision_s_section_subheading_ar_rejects_input_exceeding_150(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Content (EN) accepts a valid bulleted list, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136297
@pytest.mark.traceability("136297")
@allure.label("pbi", "129395")
@allure.label("testcase", "136297")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136297_verify_that_vision_s_section_content_en_accepts_a_valid_bulleted_list(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Content (EN) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136299
@pytest.mark.traceability("136299")
@allure.label("pbi", "129395")
@allure.label("testcase", "136299")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136299_verify_that_vision_s_section_content_en_cannot_be_saved_when_left(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Content (EN) rejects input exceeding 5000 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136301
@pytest.mark.traceability("136301")
@allure.label("pbi", "129395")
@allure.label("testcase", "136301")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136301_verify_that_vision_s_section_content_en_rejects_input_exceeding_5000(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an invalid hyperlink inside Vision's Section Content (EN) is rejected")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136303
@pytest.mark.traceability("136303")
@allure.label("pbi", "129395")
@allure.label("testcase", "136303")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136303_verify_that_an_invalid_hyperlink_inside_vision_s_section_content_en_is(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Content (AR) accepts a valid bulleted list, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136305
@pytest.mark.traceability("136305")
@allure.label("pbi", "129395")
@allure.label("testcase", "136305")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136305_verify_that_vision_s_section_content_ar_accepts_a_valid_bulleted_list(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Content (AR) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136306
@pytest.mark.traceability("136306")
@allure.label("pbi", "129395")
@allure.label("testcase", "136306")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136306_verify_that_vision_s_section_content_ar_cannot_be_saved_when_left(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Content (AR) rejects input exceeding 5000 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136308
@pytest.mark.traceability("136308")
@allure.label("pbi", "129395")
@allure.label("testcase", "136308")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136308_verify_that_vision_s_section_content_ar_rejects_input_exceeding_5000(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Image accepts a valid JPG upload under 2MB, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136309
@pytest.mark.traceability("136309")
@allure.label("pbi", "129395")
@allure.label("testcase", "136309")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136309_verify_that_vision_s_section_image_accepts_a_valid_jpg_upload_under(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Image rejects an unsupported file format")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136310
@pytest.mark.traceability("136310")
@allure.label("pbi", "129395")
@allure.label("testcase", "136310")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136310_verify_that_vision_s_section_image_rejects_an_unsupported_file_format(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Image rejects an image exceeding 2MB")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136311
@pytest.mark.traceability("136311")
@allure.label("pbi", "129395")
@allure.label("testcase", "136311")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136311_verify_that_vision_s_section_image_rejects_an_image_exceeding_2mb(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Section Image can be left empty and the section still saves, since the field is optional")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136312
@pytest.mark.traceability("136312")
@allure.label("pbi", "129395")
@allure.label("testcase", "136312")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136312_verify_that_vision_s_section_image_can_be_left_empty_and_the_section(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Image Badge Label (EN) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136313
@pytest.mark.traceability("136313")
@allure.label("pbi", "129395")
@allure.label("testcase", "136313")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136313_verify_that_vision_s_image_badge_label_en_accepts_a_valid_value_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Image Badge Label (EN) rejects input exceeding 50 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136314
@pytest.mark.traceability("136314")
@allure.label("pbi", "129395")
@allure.label("testcase", "136314")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136314_verify_that_vision_s_image_badge_label_en_rejects_input_exceeding_50(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Image Badge Label (EN) can be left empty and the section still saves, since the field is optional")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136315
@pytest.mark.traceability("136315")
@allure.label("pbi", "129395")
@allure.label("testcase", "136315")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136315_verify_that_vision_s_image_badge_label_en_can_be_left_empty_and_the(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Image Badge Label (AR) accepts a valid value, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136316
@pytest.mark.traceability("136316")
@allure.label("pbi", "129395")
@allure.label("testcase", "136316")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136316_verify_that_vision_s_image_badge_label_ar_accepts_a_valid_value_saves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Image Badge Label (AR) rejects input exceeding 50 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136317
@pytest.mark.traceability("136317")
@allure.label("pbi", "129395")
@allure.label("testcase", "136317")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136317_verify_that_vision_s_image_badge_label_ar_rejects_input_exceeding_50(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Display Order accepts a valid unique positive integer, saves, and persists after reload")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136318
@pytest.mark.traceability("136318")
@allure.label("pbi", "129395")
@allure.label("testcase", "136318")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136318_verify_that_vision_s_display_order_accepts_a_valid_unique_positive(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Display Order rejects a value that duplicates another section's Display Order")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136319
@pytest.mark.traceability("136319")
@allure.label("pbi", "129395")
@allure.label("testcase", "136319")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136319_verify_that_vision_s_display_order_rejects_a_value_that_duplicates(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Display Order rejects zero")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136320
@pytest.mark.traceability("136320")
@allure.label("pbi", "129395")
@allure.label("testcase", "136320")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136320_verify_that_vision_s_display_order_rejects_zero(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Display Order rejects a negative value")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136321
@pytest.mark.traceability("136321")
@allure.label("pbi", "129395")
@allure.label("testcase", "136321")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136321_verify_that_vision_s_display_order_rejects_a_negative_value(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Vision's Display Order rejects a non-numeric value")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136322
@pytest.mark.traceability("136322")
@allure.label("pbi", "129395")
@allure.label("testcase", "136322")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136322_verify_that_vision_s_display_order_rejects_a_non_numeric_value(page):
    ...


# ---------------------------------------------------------------------------
# 136323 -- Verify that setting Vision's Active status to Active makes it visible on the published page, and the value persists after reload
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_vision_mission_objectives_web.py under the same tc_136323
# marker -- not duplicated here to avoid a duplicate Axis-C selector across
# modules.
# ---------------------------------------------------------------------------

@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that setting Vision's Active status to Inactive hides it from the published page while it remains editable in CMS")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136324
@pytest.mark.traceability("136324")
@allure.label("pbi", "129395")
@allure.label("testcase", "136324")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136324_verify_that_setting_vision_s_active_status_to_inactive_hides_it_from(page):
    ...


# ---------------------------------------------------------------------------
# 136325 -- Verify that all Mission section fields (label, headline, subheading, content, image, badge label, display order 2, active) can be saved and published as a complete valid set
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_vision_mission_objectives_web.py under the same tc_136325
# marker -- not duplicated here to avoid a duplicate Axis-C selector across
# modules.
# ---------------------------------------------------------------------------

@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Mission's Section Headline (AR) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136326
@pytest.mark.traceability("136326")
@allure.label("pbi", "129395")
@allure.label("testcase", "136326")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136326_verify_that_mission_s_section_headline_ar_cannot_be_saved_when_left(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Mission's Section Content (EN) rejects input exceeding 5000 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136327
@pytest.mark.traceability("136327")
@allure.label("pbi", "129395")
@allure.label("testcase", "136327")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136327_verify_that_mission_s_section_content_en_rejects_input_exceeding_5000(page):
    ...


# ---------------------------------------------------------------------------
# 136328 -- Verify that Mission's Section Content renders as a single paragraph on the frontend, matching its configured content type
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_vision_mission_objectives_web.py under the same tc_136328
# marker -- not duplicated here to avoid a duplicate Axis-C selector across
# modules.
# ---------------------------------------------------------------------------

@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Mission's Section Image rejects an image exceeding 2MB")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136329
@pytest.mark.traceability("136329")
@allure.label("pbi", "129395")
@allure.label("testcase", "136329")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136329_verify_that_mission_s_section_image_rejects_an_image_exceeding_2mb(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Mission's Display Order accepts the value 2 as unique and valid")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136330
@pytest.mark.traceability("136330")
@allure.label("pbi", "129395")
@allure.label("testcase", "136330")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136330_verify_that_mission_s_display_order_accepts_the_value_2_as_unique_and(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Mission's Image Badge Label (AR) rejects input exceeding 50 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136331
@pytest.mark.traceability("136331")
@allure.label("pbi", "129395")
@allure.label("testcase", "136331")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136331_verify_that_mission_s_image_badge_label_ar_rejects_input_exceeding_50(page):
    ...


# ---------------------------------------------------------------------------
# 136332 -- Verify that Mission's configured Section Image renders on the left side of the section, per its distinct alternation configuration
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_vision_mission_objectives_web.py under the same tc_136332
# marker -- not duplicated here to avoid a duplicate Axis-C selector across
# modules.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 136333 -- Verify that all Objectives section fields (label, headline, subheading, content, image, badge label, display order 3, active) can be saved and published as a complete valid set
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_vision_mission_objectives_web.py under the same tc_136333
# marker -- not duplicated here to avoid a duplicate Axis-C selector across
# modules.
# ---------------------------------------------------------------------------

@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Objectives' Section Label (EN) cannot be saved when left empty")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136334
@pytest.mark.traceability("136334")
@allure.label("pbi", "129395")
@allure.label("testcase", "136334")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136334_verify_that_objectives_section_label_en_cannot_be_saved_when_left(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Objectives' Section Headline (EN) rejects input exceeding 150 characters")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136335
@pytest.mark.traceability("136335")
@allure.label("pbi", "129395")
@allure.label("testcase", "136335")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136335_verify_that_objectives_section_headline_en_rejects_input_exceeding_150(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Objectives' Display Order rejects a value that duplicates Vision's Display Order")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136336
@pytest.mark.traceability("136336")
@allure.label("pbi", "129395")
@allure.label("testcase", "136336")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136336_verify_that_objectives_display_order_rejects_a_value_that_duplicates(page):
    ...


# ---------------------------------------------------------------------------
# 136337 -- Verify that Objectives' Section Content supports a bulleted list matching the "Five Pillars of Growth" structure
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_vision_mission_objectives_web.py under the same tc_136337
# marker -- not duplicated here to avoid a duplicate Axis-C selector across
# modules.
# ---------------------------------------------------------------------------

@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Objectives' Image Badge Label (EN) safely handles special/injection-style characters without executing script content")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136338
@pytest.mark.traceability("136338")
@allure.label("pbi", "129395")
@allure.label("testcase", "136338")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136338_verify_that_objectives_image_badge_label_en_safely_handles_special(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Objectives' Section Image rejects an unsupported file format")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129395
@pytest.mark.tc_136339
@pytest.mark.traceability("136339")
@allure.label("pbi", "129395")
@allure.label("testcase", "136339")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136339_verify_that_objectives_section_image_rejects_an_unsupported_file(page):
    ...


# ---------------------------------------------------------------------------
# 136340 -- Verify that Objectives' configured Section Image renders on the right side of the section, per its distinct alternation configuration
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_vision_mission_objectives_web.py under the same tc_136340
# marker -- not duplicated here to avoid a duplicate Axis-C selector across
# modules.
# ---------------------------------------------------------------------------

@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that deactivating the Vision section (the first section) correctly renumbers Mission and Objectives to 01 and 02")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136341
@pytest.mark.traceability("136341")
@allure.label("pbi", "129395")
@allure.label("testcase", "136341")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136341_verify_that_deactivating_the_vision_section_the_first_section(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that deactivating two sections (Mission and Objectives) leaves only Vision, renumbered to 01")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136342
@pytest.mark.traceability("136342")
@allure.label("pbi", "129395")
@allure.label("testcase", "136342")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136342_verify_that_deactivating_two_sections_mission_and_objectives_leaves(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that reactivating a deactivated section re-inserts it at the position matching its configured Display Order and triggers a second renumbering")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136343
@pytest.mark.traceability("136343")
@allure.label("pbi", "129395")
@allure.label("testcase", "136343")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136343_verify_that_reactivating_a_deactivated_section_re_inserts_it_at_the(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that an image embedded inside Section Content (rich text) renders correctly alongside the separate Section Image upload without conflict")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136344
@pytest.mark.traceability("136344")
@allure.label("pbi", "129395")
@allure.label("testcase", "136344")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136344_verify_that_an_image_embedded_inside_section_content_rich_text_renders(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that a missing Arabic translation for a mandatory section field falls back to the default language without breaking the rest of the Arabic page")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136345
@pytest.mark.traceability("136345")
@allure.label("pbi", "129395")
@allure.label("testcase", "136345")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136345_verify_that_a_missing_arabic_translation_for_a_mandatory_section_field(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that closing a Preview without publishing leaves the underlying Draft content intact when the record is reopened")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136346
@pytest.mark.traceability("136346")
@allure.label("pbi", "129395")
@allure.label("testcase", "136346")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136346_verify_that_closing_a_preview_without_publishing_leaves_the_underlying(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that rapidly double-clicking the Publish button does not create a duplicate publish action or duplicate success toast")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136347
@pytest.mark.traceability("136347")
@allure.label("pbi", "129395")
@allure.label("testcase", "136347")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136347_verify_that_rapidly_double_clicking_the_publish_button_does_not_create(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that a network drop during the Publish action does not leave the page in a partially-published or corrupted state")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136348
@pytest.mark.traceability("136348")
@allure.label("pbi", "129395")
@allure.label("testcase", "136348")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136348_verify_that_a_network_drop_during_the_publish_action_does_not_leave(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the same mandatory-field validation rule (empty Section Headline) behaves identically across all three repeated section instances")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136349
@pytest.mark.traceability("136349")
@allure.label("pbi", "129395")
@allure.label("testcase", "136349")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136349_verify_that_the_same_mandatory_field_validation_rule_empty_section(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that unpublishing the page while the Main Menu link still points to it results in a graceful fallback, not a broken navigation link")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136350
@pytest.mark.traceability("136350")
@allure.label("pbi", "129395")
@allure.label("testcase", "136350")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136350_verify_that_unpublishing_the_page_while_the_main_menu_link_still(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the page behaves correctly when all three sections are deactivated simultaneously")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136351
@pytest.mark.traceability("136351")
@allure.label("pbi", "129395")
@allure.label("testcase", "136351")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136351_verify_that_the_page_behaves_correctly_when_all_three_sections_are(page):
    ...


@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the system behaves correctly when two admins concurrently attempt to save conflicting Display Order values for different sections")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129395
@pytest.mark.tc_136352
@pytest.mark.traceability("136352")
@allure.label("pbi", "129395")
@allure.label("testcase", "136352")
@pytest.mark.skip(reason='Requires an authenticated Liferay Control Panel session against the "VMO Sections" / VMO page-settings admin object to exercise this field-level check live -- blocked this session by the same qcdev "developer mode connection limit" / license_activation interstitial documented in web/pages/control_panel/login_page.py and reproduced fresh here (see module docstring): a brand-new Playwright session hitting /c/portal/login never rendered the login form fields (fill() timed out before the interstitial cleared), and both cached storageState files (.auth/state.json, .auth/gm_admin_state.json) landed on the public homepage/license_activation page instead of the admin surface, so no admin edit-form locators could be extracted or confirmed for this case. This is an infra blocker, not a coverage decision -- retry once qcdev\'s login path is confirmed clear.')
def test_vmo_cp_136352_verify_that_the_system_behaves_correctly_when_two_admins_concurrently(page):
    ...


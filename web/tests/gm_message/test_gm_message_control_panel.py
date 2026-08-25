"""
web/tests/gm_message/test_gm_message_control_panel.py — Control_Panel-tagged
cases for PBI 129397 (QC-ABOUT-005 — General Manager's Message) from the
priority batch (see test_gm_message_web.py's module docstring for the full
ID-range context).

Every case here is a `Both` (Control_Panel + Web) case whose CMS-authoring
step this batch could not perform: no stable, extracted locators exist yet
for the GM's Message custom-widget edit form inside the Liferay Control
Panel (this batch's scope, per explicit instruction, is Web/public-facing
verification first), and several of these actions are destructive against
the shared qcdev.ihorizons.com environment (publish/unpublish/draft-state
changes) with no confirmed teardown path.

Per the user's explicit instruction, these are SKIPPED with a concrete
reason rather than blocking the batch — never silently dropped, never faked
as a pass (automation-standards.md's Result Integrity rule). Where the
case's PUBLIC-FACING half can be verified standalone against already-
published content without the CMS write, that verification already exists
as a passing test in test_gm_message_web.py and is cross-referenced below
instead of being duplicated here.

SECOND PASS (2026-08-25) — full Control_Panel batch for PBI 129397.
review_test_coverage(129397) tags exactly 147 cases `Control_Panel`; the 5
above were already scripted as skip stubs by the prior pass and are left
untouched. This pass attempted, per the QA Manager's policy, to automate the
remaining 142 as real field-validation / persistence / permission-denial
checks against the Liferay CMS admin edit form for the GM's Message custom
widget (policy explicitly allows this: required-field, char-limit, upload
format/size, injection-safety, save-verify-revert, and non-mutating Auth
denial checks are all SAFE categories).

That attempt was blocked by a live, reproduced environment failure, not a
locator gap: qcdev.ihorizons.com's "developer mode connection limit"
interstitial (`/c/portal/license_activation`) intercepted every login
attempt this session, including a direct Playwright login through
CmsLoginPage's own confirmed-real selectors, and its own "reset all
connections" link did not clear it (click timed out; the login form never
rendered afterward). This is the SAME unresolved qcdev infrastructure issue
already flagged in web/pages/control_panel/login_page.py's docstring
("...the automated suite will very likely hit this same wall when it runs
standalone against qcdev; that is a real, unresolved dev-mode
connection-limit issue on the qcdev instance itself and needs a fix from
whoever administers it, not a workaround in this Page Object"). No
authenticated admin session could be established at all this session, so no
edit-form locators could be extracted or confirmed for ANY of the 142 cases
— per the one-pass/real-locators rule, none are invented here.

All 142 are therefore registered below as explicit `pytest.mark.skip`
stubs — never silently dropped — each carrying its own `tc_<id>` +
`pbi_129397` + `control_panel` marker (plus a best-effort category marker
derived from the source case's own `category`/tags field: `auth`,
`functional_high`, `functional_low`, `edge`, `ui`, `bilingual`,
`dataintegrity`, `regression` where the source tagged it `Regression`) so
`pytest --collect-only` and Allure both keep the full 147-case gap visible.
Re-attempt once qcdev's login path is confirmed clear of the license/
connection-limit interstitial — this is an infra blocker, not a coverage
decision, and should be retried the next session rather than re-judged.
"""

import allure
import pytest


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("CMS authoring workflow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site Content Editor can author, preview, and publish the complete bilingual GM's Message record end-to-end")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_136383
@pytest.mark.skip(
    reason="Requires the full Site Content Editor authoring workflow "
    "(EN/AR field entry, Hero Banner + Portrait image upload, Save as "
    "Draft, Preview, Publish) against the GM's Message custom widget's "
    "admin edit form. No stable locators for that edit form were extracted "
    "in this batch — this batch's scope is the Web/public-facing "
    "verification priority per explicit instruction, and authoring one "
    "would need either a confirmed Control Panel edit URL or an "
    "interactive Playwright-MCP exploration disclosed as a fallback, "
    "neither of which was exercised here."
)
def test_gm_message_editor_authors_previews_publishes_end_to_end(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Draft/Published visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Draft GM's Message content is not visible to a Public Visitor")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_136384
@pytest.mark.skip(
    reason="Requires saving a new/edited version of the GM's Message "
    "record as Draft (without publishing) via the Control Panel — a CMS "
    "write this batch could not perform (no confirmed admin edit-form "
    "locators). The always-true half of this guarantee (the public page "
    "currently serves real, non-blank published content, never a raw "
    "draft artifact) is covered by "
    "test_gm_message_public_visitor_reads_full_page_en/_ar in "
    "test_gm_message_web.py."
)
def test_gm_message_draft_content_not_visible_to_visitor(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Publish / Unpublish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Unpublishing the GM's Message page removes it from the live site")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_136385
@pytest.mark.skip(
    reason="Requires unpublishing the live, shared GM's Message record via "
    "the Control Panel — a destructive action against the shared "
    "qcdev.ihorizons.com environment (other suites may be reading this "
    "page concurrently) with no confirmed republish/teardown path "
    "available to this batch. Skipped rather than risking the page's "
    "availability for other in-flight automation."
)
def test_gm_message_unpublish_removes_from_live_site(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Entering the GM Name once updates both the Portrait Caption and the Signature Block identically")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_136386
@pytest.mark.skip(
    reason="Requires editing the GM Name field via the Control Panel and "
    "republishing to observe the propagated change — a CMS write this "
    "batch could not perform (no confirmed admin edit-form locators). The "
    "read-only half of this guarantee — that the CURRENTLY published GM "
    "Name renders identically in both the Portrait Caption and the "
    "Signature Block — is already covered (and passing) as "
    "test_gm_message_name_designation_consistency in "
    "test_gm_message_web.py; only the write-then-republish propagation "
    "step is skipped here."
)
def test_gm_message_name_edit_propagates_to_both_locations(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Editing GM Name on an already-published page updates both the Portrait Caption and Signature Block only after republish")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136453
@pytest.mark.skip(
    reason="Requires editing the GM Name field, confirming the LIVE page "
    "still shows the OLD name before Publish, then republishing and "
    "confirming both locations update together — a multi-step CMS write "
    "this batch could not perform (no confirmed admin edit-form "
    "locators). The steady-state read-only half (current published name "
    "identical in both locations) is already covered by "
    "test_gm_message_name_designation_consistency in "
    "test_gm_message_web.py; the edit/save-pending/republish sequence "
    "itself is skipped here."
)
def test_gm_message_name_edit_pending_then_republish_updates_both(page):
    ...


# ---------------------------------------------------------------------------
# Remaining Control_Panel-tagged cases for PBI 129397 (142 cases, sourced
# verbatim from review_test_coverage(129397)'s Control_Panel-tagged subset).
#
# BLOCKED this session -- see _CMS_LOGIN_BLOCKED below for the concrete,
# live-reproduced reason. Every case is still registered here (never
# silently dropped) as an explicit skip stub carrying its own tc_<id> +
# pbi_129397 + control_panel markers, per automation-standards.md's Result
# Integrity rule. Re-attempt once qcdev's login path is confirmed clear of
# the license/connection-limit interstitial.
# ---------------------------------------------------------------------------

_CMS_LOGIN_BLOCKED = (
    "CMS admin authoring workflow blocked this session: "
    "qcdev.ihorizons.com's \"developer mode connection limit\" "
    "interstitial (/c/portal/license_activation) intercepted the login "
    "request and did not clear after following its own reset link "
    "(confirmed live, 2026-08-25: attempted a fresh Playwright login via "
    "CmsLoginPage's real selectors, reset-link click timed out, login "
    "form never rendered). No authenticated admin session could be "
    "established to reach the GM's Message custom widget's edit form, so "
    "no real locators exist for it -- per the one-pass/real-locators "
    "rule, none are invented here. This is the same unresolved qcdev dev- "
    "mode connection-limit issue flagged in "
    "web/pages/control_panel/login_page.py's docstring, not a new gap "
    "introduced by this batch. "
)

@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Editor can create, edit, preview, publish, and unpublish the GM's Message record (ADO-135445)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_135445
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_editor_can_create_edit_preview_publish_and_135445(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author can view and update assigned GM's Message content but cannot publish directly (ADO-135446)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_135446
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_author_can_view_and_update_assigned_gms_135446(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author attempting to force a Publish action via a direct workflow call is denied with the standard Access Denied message (ADO-135447)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135447
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_author_attempting_to_force_a_publish_action_135447(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Public Visitor cannot access the GM's Message CMS edit URL directly (forced browsing) (ADO-135448)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_135448
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_public_visitor_cannot_access_the_gms_message_cms_edit_135448(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a logged-in CMS user without any assigned role on the GM's Message content receives Access Denied when opening the record (ADO-135450)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135450
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_loggedin_cms_user_without_any_assigned_role_on_the_135450(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Editor can author, preview, and publish the complete bilingual GM's Message record end-to-end (ADO-135453)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135453
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_editor_can_author_preview_and_publish_the_135453(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Editor is blocked from publishing when the Arabic Page Title is missing (ADO-135454)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135454
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_editor_is_blocked_from_publishing_when_the_135454(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that unpublishing the GM's Message page removes it from the live website while the record remains editable in CMS (ADO-135456)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129397
@pytest.mark.tc_135456
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_unpublishing_the_gms_message_page_removes_it_from_the_135456(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Draft content saved but not yet published is never visible on the public website (ADO-135457)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129397
@pytest.mark.tc_135457
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_draft_content_saved_but_not_yet_published_is_never_135457(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that updating the GM Name field once and republishing updates both the portrait caption and the signature block consistently (ADO-135458)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.dataintegrity
@pytest.mark.pbi_129397
@pytest.mark.tc_135458
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_updating_the_gm_name_field_once_and_republishing_updates_135458(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (EN) accepts a valid value up to the 100-character limit and saves (ADO-135459)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135459
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_en_accepts_a_valid_value_up_to_135459(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (EN) is rejected when left empty (ADO-135460)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135460
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_en_is_rejected_when_left_empty_135460(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (EN) is rejected when it exceeds 100 characters (ADO-135461)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135461
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_en_is_rejected_when_it_exceeds_100_135461(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (AR) accepts a valid Arabic value up to 100 characters and saves (ADO-135462)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135462
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_ar_accepts_a_valid_arabic_value_up_135462(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (AR) is rejected with the Arabic-specific message when left empty (ADO-135463)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135463
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_ar_is_rejected_with_the_arabicspecific_message_135463(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (AR) is rejected when it exceeds 100 characters (ADO-135464)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135464
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_ar_is_rejected_when_it_exceeds_100_135464(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid JPG Hero Banner image under 2MB uploads successfully (ADO-135465)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135465
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_jpg_hero_banner_image_under_2mb_uploads_successfully_135465(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported Hero Banner image format is rejected (ADO-135466)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135466
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_unsupported_hero_banner_image_format_is_rejected_135466(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Hero Banner image exceeding 2MB is rejected with the exact bilingual error message (ADO-135467)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135467
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_hero_banner_image_exceeding_2mb_is_rejected_with_the_135467(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Hero Banner image exactly at the 2MB boundary is accepted (ADO-135468)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135468
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_hero_banner_image_exactly_at_the_2mb_boundary_is_135468(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (EN) accepts a valid value up to 150 characters (ADO-135469)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135469
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_en_accepts_a_valid_value_up_135469(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (EN) is rejected when left empty (ADO-135470)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135470
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_en_is_rejected_when_left_empty_135470(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (EN) is rejected when it exceeds 150 characters (ADO-135471)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135471
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_en_is_rejected_when_it_exceeds_135471(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (AR) accepts a valid Arabic value up to 150 characters (ADO-135472)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135472
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_ar_accepts_a_valid_arabic_value_135472(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (AR) is rejected when left empty (ADO-135473)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135473
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_ar_is_rejected_when_left_empty_135473(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Portrait Image in PNG format under 2MB uploads successfully (ADO-135474)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135474
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_gm_portrait_image_in_png_format_under_2mb_135474(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported GM Portrait Image format (SVG) is rejected (ADO-135475)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135475
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_unsupported_gm_portrait_image_format_svg_is_rejected_135475(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Portrait Image exceeding 2MB is rejected (ADO-135476)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135476
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_portrait_image_exceeding_2mb_is_rejected_135476(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (EN) accepts a valid value and saves correctly (ADO-135477)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135477
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_en_accepts_a_valid_value_and_saves_135477(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (EN) is rejected when left empty (ADO-135478)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135478
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_en_is_rejected_when_left_empty_135478(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (EN) is rejected when it exceeds 100 characters (ADO-135479)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135479
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_en_is_rejected_when_it_exceeds_100_135479(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (AR) accepts a valid Arabic value and saves correctly (ADO-135480)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135480
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_ar_accepts_a_valid_arabic_value_and_135480(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (AR) is rejected when left empty (ADO-135481)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135481
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_ar_is_rejected_when_left_empty_135481(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Designation (EN) accepts a valid value and saves correctly (ADO-135482)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135482
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_en_accepts_a_valid_value_and_saves_135482(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Designation (EN) is rejected when left empty (ADO-135483)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135483
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_en_is_rejected_when_left_empty_135483(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Designation (AR) accepts a valid Arabic value and saves correctly (ADO-135484)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135484
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_ar_accepts_a_valid_arabic_value_and_135484(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (EN) accepts a valid value up to 150 characters (ADO-135485)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135485
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_en_accepts_a_valid_value_up_to_135485(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (EN) is rejected when left empty (ADO-135486)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135486
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_en_is_rejected_when_left_empty_135486(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (EN) is rejected when it exceeds 150 characters (ADO-135487)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135487
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_en_is_rejected_when_it_exceeds_150_135487(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (AR) accepts a valid Arabic value up to 150 characters (ADO-135488)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135488
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_ar_accepts_a_valid_arabic_value_up_135488(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) accepts valid rich text with headings, paragraphs, bullets, and inline links (ADO-135489)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135489
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_en_accepts_valid_rich_text_with_headings_135489(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) is rejected when left empty (ADO-135490)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135490
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_en_is_rejected_when_left_empty_135490(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) is rejected when it exceeds 5000 characters (ADO-135491)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135491
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_en_is_rejected_when_it_exceeds_5000_135491(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (AR) accepts valid Arabic rich text and saves correctly (ADO-135492)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135492
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_ar_accepts_valid_arabic_rich_text_and_135492(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (AR) is rejected when left empty (ADO-135493)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135493
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_ar_is_rejected_when_left_empty_135493(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (EN) accepts a valid value up to 50 characters (ADO-135494)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135494
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_en_accepts_a_valid_value_up_135494(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (EN) is rejected when left empty (ADO-135495)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135495
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_en_is_rejected_when_left_empty_135495(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (EN) is rejected when it exceeds 50 characters (ADO-135496)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135496
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_en_is_rejected_when_it_exceeds_135496(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (AR) accepts a valid Arabic value up to 50 characters (ADO-135497)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135497
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_ar_accepts_a_valid_arabic_value_135497(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Avatar image uploads successfully as an optional field (ADO-135498)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135498
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_signature_avatar_image_uploads_successfully_as_an_optional_135498(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that the record saves successfully when the optional Signature Avatar is left blank (ADO-135499)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135499
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_the_record_saves_successfully_when_the_optional_signature_avatar_135499(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported Signature Avatar format is rejected even though the field is optional (ADO-135500)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135500
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_unsupported_signature_avatar_format_is_rejected_even_though_the_135500(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Published makes the record visible on the live website (ADO-135501)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135501
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_setting_status_to_published_makes_the_record_visible_on_135501(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Draft keeps the record CMS-only and invisible on the live website (ADO-135502)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135502
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_setting_status_to_draft_keeps_the_record_cmsonly_and_135502(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid hyperlink URL entered in the message content is saved and rendered as a working link (ADO-135503)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135503
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_hyperlink_url_entered_in_the_message_content_is_135503(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an invalid hyperlink URL is rejected with the exact validation message (ADO-135504)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135504
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_invalid_hyperlink_url_is_rejected_with_the_exact_validation_135504(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that entering the GM Name once and saving reflects into both the portrait caption preview and the signature block preview without re-entry (ADO-135505)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.dataintegrity
@pytest.mark.pbi_129397
@pytest.mark.tc_135505
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_entering_the_gm_name_once_and_saving_reflects_into_135505(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that all field values are retained after saving as Draft and reloading the record (ADO-135506)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135506
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_all_field_values_are_retained_after_saving_as_draft_135506(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a name/designation mismatch between the portrait caption and signature block is visibly detectable if content is authored inconsistently (ADO-135508)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.dataintegrity
@pytest.mark.pbi_129397
@pytest.mark.tc_135508
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_namedesignation_mismatch_between_the_portrait_caption_and_signature_block_135508(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that republishing a page immediately after unpublishing restores it to the live site correctly (ADO-135509)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135509
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_republishing_a_page_immediately_after_unpublishing_restores_it_to_135509(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Publish is blocked when the GM Portrait Image field is left in an invalid state (upload failed) (ADO-135511)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135511
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_publish_is_blocked_when_the_gm_portrait_image_field_135511(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that rapidly double-clicking Publish does not create a duplicate publish action or duplicate audit log entry (ADO-135512)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135512
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_rapidly_doubleclicking_publish_does_not_create_a_duplicate_publish_135512(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Portrait Image sized exactly 1 byte over the 2MB limit is rejected while exactly-2MB is accepted (ADO-135513)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135513
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_portrait_image_sized_exactly_1_byte_over_the_135513(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that the system handles two admin sessions editing the same GM's Message Draft record concurrently without silent data loss (ADO-135514)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135514
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_the_system_handles_two_admin_sessions_editing_the_same_135514(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unauthenticated user is denied direct access to the CMS edit screen for the GM's Message page (ADO-136375)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136375
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_unauthenticated_user_is_denied_direct_access_to_the_cms_136375(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Editor has full lifecycle controls for the GM's Message page (ADO-136376)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136376
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_editor_has_full_lifecycle_controls_for_the_136376(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author can edit assigned GM's Message content but cannot publish directly (ADO-136377)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136377
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_author_can_edit_assigned_gms_message_content_136377(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author is denied when attempting to publish the GM's Message page directly (ADO-136378)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136378
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_author_is_denied_when_attempting_to_publish_136378(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a user with no CMS permission is denied access when opening the GM's Message page record (ADO-136379)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136379
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_user_with_no_cms_permission_is_denied_access_when_136379(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an expired admin session forces re-authentication during GM's Message editing (ADO-136380)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136380
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_expired_admin_session_forces_reauthentication_during_gms_message_editing_136380(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a role change mid-session is reflected on the next permission-checked action (ADO-136381)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136381
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_role_change_midsession_is_reflected_on_the_next_permissionchecked_136381(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Preview shows exact content without publishing the page (ADO-136389)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136389
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_preview_shows_exact_content_without_publishing_the_page_136389(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that publishing the GM's Message page records an audit log entry (ADO-136390)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136390
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_publishing_the_gms_message_page_records_an_audit_log_136390(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Draft to Preview to Publish lifecycle continuity is preserved across multiple editing sessions (ADO-136391)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136391
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_draft_to_preview_to_publish_lifecycle_continuity_is_preserved_136391(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Editor can publish content submitted by a Site Content Author (ADO-136392)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136392
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_editor_can_publish_content_submitted_by_a_136392(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that republishing the GM's Message page updates the existing live page without creating a duplicate record (ADO-136393)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136393
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_republishing_the_gms_message_page_updates_the_existing_live_136393(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Page Title (EN) is saved and persists after reload (ADO-136394)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136394
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_page_title_en_is_saved_and_persists_after_136394(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty Page Title (EN) is rejected on save (ADO-136395)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136395
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_empty_page_title_en_is_rejected_on_save_136395(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Page Title (EN) exceeding 100 characters is rejected (ADO-136396)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136396
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_en_exceeding_100_characters_is_rejected_136396(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (EN) sanitizes script injection input (ADO-136397)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136397
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_en_sanitizes_script_injection_input_136397(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Page Title (AR) is saved, renders RTL, and persists after reload (ADO-136398)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136398
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_page_title_ar_is_saved_renders_rtl_and_136398(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Page Title (AR) exceeding 100 characters is rejected (ADO-136399)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136399
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_ar_exceeding_100_characters_is_rejected_136399(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Salutation Heading (EN) is saved and persists after reload (ADO-136400)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136400
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_salutation_heading_en_is_saved_and_persists_after_136400(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty Salutation Heading (EN) is rejected on save (ADO-136401)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136401
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_empty_salutation_heading_en_is_rejected_on_save_136401(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Salutation Heading (EN) exceeding 150 characters is rejected (ADO-136402)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136402
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_en_exceeding_150_characters_is_rejected_136402(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (EN) sanitizes embedded HTML tags (ADO-136403)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136403
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_en_sanitizes_embedded_html_tags_136403(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Salutation Heading (AR) is saved, renders RTL, and persists after reload (ADO-136404)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136404
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_salutation_heading_ar_is_saved_renders_rtl_and_136404(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Salutation Heading (AR) exceeding 150 characters is rejected (ADO-136405)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136405
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_ar_exceeding_150_characters_is_rejected_136405(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Name (EN) is saved and persists after reload (ADO-136406)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136406
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_gm_name_en_is_saved_and_persists_after_136406(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty GM Name (EN) is rejected on save (ADO-136407)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136407
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_empty_gm_name_en_is_rejected_on_save_136407(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Name (EN) exceeding 100 characters is rejected (ADO-136408)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136408
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_en_exceeding_100_characters_is_rejected_136408(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (EN) sanitizes embedded HTML tags (ADO-136409)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136409
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_en_sanitizes_embedded_html_tags_136409(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Name (AR) is saved, renders RTL, and persists after reload (ADO-136410)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136410
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_gm_name_ar_is_saved_renders_rtl_and_136410(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Name (AR) exceeding 100 characters is rejected (ADO-136411)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136411
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_ar_exceeding_100_characters_is_rejected_136411(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Designation (EN) is saved and persists after reload (ADO-136412)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136412
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_gm_designation_en_is_saved_and_persists_after_136412(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty GM Designation (EN) is rejected on save (ADO-136413)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136413
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_empty_gm_designation_en_is_rejected_on_save_136413(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Designation (EN) exceeding 100 characters is rejected (ADO-136414)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136414
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_en_exceeding_100_characters_is_rejected_136414(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Designation (EN) sanitizes script injection input (ADO-136415)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136415
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_en_sanitizes_script_injection_input_136415(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Designation (AR) is saved, renders RTL, and persists after reload (ADO-136416)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136416
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_gm_designation_ar_is_saved_renders_rtl_and_136416(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Designation (AR) exceeding 100 characters is rejected (ADO-136417)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136417
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_ar_exceeding_100_characters_is_rejected_136417(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that valid rich-text Page Content (EN) with headings, bullets, and a link is saved and persists (ADO-136418)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136418
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_richtext_page_content_en_with_headings_bullets_and_136418(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that empty Page Content (EN) is rejected on save (ADO-136419)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136419
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_empty_page_content_en_is_rejected_on_save_136419(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) exceeding 5000 characters is rejected (ADO-136420)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136420
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_en_exceeding_5000_characters_is_rejected_136420(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) sanitizes script injection within the rich text editor (ADO-136421)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136421
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_en_sanitizes_script_injection_within_the_rich_136421(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that valid rich-text Page Content (AR) is saved, renders RTL/bidi correctly, and persists (ADO-136422)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136422
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_richtext_page_content_ar_is_saved_renders_rtlbidi_136422(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (AR) exceeding 5000 characters is rejected (ADO-136423)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136423
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_ar_exceeding_5000_characters_is_rejected_136423(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Closing Text (EN) is saved and persists after reload (ADO-136424)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136424
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_signature_closing_text_en_is_saved_and_persists_136424(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty Signature Closing Text (EN) is rejected on save (ADO-136425)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136425
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_empty_signature_closing_text_en_is_rejected_on_save_136425(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Signature Closing Text (EN) exceeding 50 characters is rejected (ADO-136426)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136426
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_en_exceeding_50_characters_is_rejected_136426(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (EN) sanitizes script injection input (ADO-136427)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136427
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_en_sanitizes_script_injection_input_136427(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Closing Text (AR) is saved, renders RTL, and persists after reload (ADO-136428)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136428
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_signature_closing_text_ar_is_saved_renders_rtl_136428(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Signature Closing Text (AR) exceeding 50 characters is rejected (ADO-136429)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136429
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_ar_exceeding_50_characters_is_rejected_136429(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Hero Banner (EN) image uploads, saves, and persists (ADO-136430)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136430
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_hero_banner_en_image_uploads_saves_and_persists_136430(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported Hero Banner (EN) file format is rejected (ADO-136431)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136431
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_unsupported_hero_banner_en_file_format_is_rejected_136431(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a missing Hero Banner (EN) is rejected on save/publish (ADO-136432)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136432
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_missing_hero_banner_en_is_rejected_on_savepublish_136432(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Hero Banner (AR) image uploads, saves, and persists per language (ADO-136433)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136433
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_hero_banner_ar_image_uploads_saves_and_persists_136433(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Portrait (EN) image uploads, saves, and persists (ADO-136434)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136434
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_gm_portrait_en_image_uploads_saves_and_persists_136434(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported GM Portrait (EN) file format is rejected (ADO-136435)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136435
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_unsupported_gm_portrait_en_file_format_is_rejected_136435(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a missing GM Portrait Image (EN) is rejected on save/publish (ADO-136436)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136436
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_missing_gm_portrait_image_en_is_rejected_on_savepublish_136436(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Portrait Image (AR) uploads, saves, and persists per language (ADO-136437)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136437
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_gm_portrait_image_ar_uploads_saves_and_persists_136437(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Avatar (EN) image uploads, saves, and persists (ADO-136438)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136438
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_signature_avatar_en_image_uploads_saves_and_persists_136438(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported Signature Avatar (EN) file format is rejected (ADO-136439)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136439
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_unsupported_signature_avatar_en_file_format_is_rejected_136439(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that the page saves and publishes successfully with no Signature Avatar uploaded (ADO-136440)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136440
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_the_page_saves_and_publishes_successfully_with_no_signature_136440(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Avatar (AR) uploads, saves, and persists per language (ADO-136441)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136441
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_signature_avatar_ar_uploads_saves_and_persists_per_136441(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that valid Image Alt Text (EN) is saved, exposed in HTML, and persists (ADO-136442)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136442
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_image_alt_text_en_is_saved_exposed_in_136442(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that empty Image Alt Text (EN) is rejected on save (ADO-136443)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136443
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_empty_image_alt_text_en_is_rejected_on_save_136443(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (EN) exceeding 150 characters is rejected (ADO-136444)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136444
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_en_exceeding_150_characters_is_rejected_136444(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that valid Image Alt Text (AR) is saved and persists per language (ADO-136445)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136445
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_image_alt_text_ar_is_saved_and_persists_136445(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid hyperlink URL is saved and persists in the message body (ADO-136446)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136446
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_valid_hyperlink_url_is_saved_and_persists_in_the_136446(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an invalid hyperlink URL is rejected on save (ADO-136447)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136447
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_invalid_hyperlink_url_is_rejected_on_save_136447(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content saves successfully with no hyperlinks present (ADO-136448)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136448
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_saves_successfully_with_no_hyperlinks_present_136448(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Draft stores the record without publishing (ADO-136449)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136449
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_setting_status_to_draft_stores_the_record_without_publishing_136449(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Published makes the page live and shows a bilingual success toast (ADO-136450)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136450
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_setting_status_to_published_makes_the_page_live_and_136450(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Unpublish removes the page from the live site but keeps it editable (ADO-136451)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136451
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_setting_status_to_unpublish_removes_the_page_from_the_136451(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that canceling an in-progress edit discards unsaved changes (ADO-136452)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136452
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_canceling_an_inprogress_edit_discards_unsaved_changes_136452(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author's field update to assigned GM's Message content is stored pending Editor publish (ADO-136454)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136454
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_site_content_authors_field_update_to_assigned_gms_message_136454(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that publishing is blocked when the Arabic title is missing while Arabic is enabled (ADO-136456)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136456
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_publishing_is_blocked_when_the_arabic_title_is_missing_136456(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an image exceeding 2MB is rejected with the exact stated message (ADO-136457)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136457
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_exceeding_2mb_is_rejected_with_the_exact_stated_136457(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an image exactly at the 2MB boundary is accepted (ADO-136458)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136458
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_exactly_at_the_2mb_boundary_is_accepted_136458(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a text field exactly at its maximum character limit is accepted (ADO-136459)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136459
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_text_field_exactly_at_its_maximum_character_limit_is_136459(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an interrupted Publish action does not leave the page in a partially-published state (ADO-136461)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136461
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_interrupted_publish_action_does_not_leave_the_page_in_136461(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that the outcome is deterministic when two Site Content Editors save the same GM's Message record concurrently (ADO-136462)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136462
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_the_outcome_is_deterministic_when_two_site_content_editors_136462(page):
    ...


"""
cms/tests/components/test_footer_control_panel.py

Control_Panel-tagged cases for PBI 129366 (QC-GBL-004 — Site Footer & Social
Media Icons), Section 4 "Social Media Icons" — the 29 ADO cases 131168-131196
handed down directly (Azure `get_test_cases_from_suite` was deliberately NOT
called this session per explicit instruction — a prior attempt stalled on
that call's payload size). No automation existed for this feature before this
module (confirmed: both this file and
`cms/pages/components/footer_admin_component.py` were placeholder stubs).

MANDATORY PRE-READS APPLIED: `.claude/context/active/standards.md`'s "Object
Authoring Is the Only Path for Content Operations — Not Content & Data"
(every field write/lifecycle action here goes through Object Authoring,
`manage-social-media-icon`, never Content & Data) and "Draft/Unpublish
Public-Visibility Checks — Mandatory Logged-Out Context" (every public-footer
read below uses a fresh `new_context(browser, use_auth_state=False)`, never
the CMS-authenticated `page`).

See `cms/pages/components/footer_admin_component.py`'s own module docstring
for the FULL live-confirmed trail this module depends on — summarized here
only where it changes how a specific case is written:

  - Slug/URL: `manage-social-media-icon` (confirmed live page title "Manage:
    Social Media Icon").
  - "Platform Name" (PBI) is a real, single-locale COMBOBOX labeled just
    "Platform" with exactly 9 fixed options (Facebook, X, LinkedIn,
    Instagram, YouTube, WhatsApp, Telegram, Snapchat, Flickr) — NOT free
    text, NOT bilingual. 131169/131171 (AR Platform Name) are SKIPPED: no
    distinct AR control exists to test (confirmed live).
  - No Cancel button exists on this form (confirmed live: only "Save as
    Draft" / "Submit for Publishing") — 131174 is SKIPPED per the task's own
    instruction not to invent one.
  - Social Redirect URL is a native `type="text"` input, not `type="url"` —
    native browser validation can NEVER catch an invalid URL FORMAT
    (confirmed live: `checkValidity()` returns `true` even for
    `"not-a-valid-url"`). 131184 is written per the case's intended
    (rejected) behavior and is EXPECTED TO LEGITIMATELY FAIL unless a custom
    app-level check exists that this session could not independently trigger
    (a submit-triggering probe was blocked by this session's own sandbox —
    see the Page Object's own "NOT VERIFIED THIS SESSION" note).
  - Icon Alt Text / Social Redirect URL carry NO client-side truncation on
    this surface (confirmed live: 120-char and 540-char fills both persist
    in full) — unlike Org Structure's Department form. 131185 (Social
    Redirect URL > 500 chars) is therefore written as a real save-attempt
    assertion, not a truncation assertion — also disclosed as possibly
    failing if the limit is unenforced server-side.
  - Upload helper text says "no larger than 10 MB" (confirmed live) — a
    THIRD number beyond ADO-131180's own title ("1 MB") and PBI 129366's
    field table ("2 MB"). 131180 is written against the PBI's 2MB figure
    using a 2.5MB fixture (exceeds all three candidate numbers) and is
    disclosed as possibly failing/passing depending on which (if any) number
    the server actually enforces — none of the three was independently
    re-confirmed as the real enforced limit this session.
  - The admin entries-list "Entry" column shows a stable per-platform code
    (`QC-SMI-<platform>`) for the 9 real production rows, or a raw UUID for
    a freshly created entry — NEVER the Icon Alt Text or Platform value
    directly. Every test that must re-find its own created entry uses
    `find_entry_code_by_alt_text_en()` (verified by field content, never by
    row position — see standards.md's "Destructive Operations Against
    qcdev" incident) plus the inherited `*_by_code()` methods.

PRODUCTION-CONTENT CAUTION: the 9 pre-existing rows are the REAL, LIVE
production footer icons. Every test that creates an entry uses a high
`Display Order` and wraps its body in `try/finally` with an immediate
`delete_entry_by_code()` teardown, to minimize how long any test-created
entry could appear on the real public footer. 131187, 131188, 131193, and
131194 set `Active Status = True` and reach Approved by design (the case
itself requires it) — these are the tests most likely to (briefly) affect
the real public footer if run; 131196 deliberately uses `Save as Draft`
(never Submit for Publishing) so it can never actually go live, even with
Active=True.

TEST DATA: every created record's Icon Alt Text (EN) carries a
`uuid4().hex[:8]` suffix (`_unique_alt_text_en()`) — this is the field
`find_entry_code_by_alt_text_en()` searches on — collisions with the 9 real
production entries or a prior run's leftovers are avoided by construction,
mirroring this project's established `_unique_*` convention (see Org
Structure's `_unique_en_dept_name()`/`_unique_ar_dept_name()` docstrings for
the collision incident that convention was healed from).

======================================================================
BATCH 2 ADDED 2026-09-17 — PBI 129373 (QC-HOME-004B), "CMS Workflow/RBAC/
Publish Lifecycle" (route-automation hand-off, batch 2 of 4): ADO cases
131148, 131153-131157, 131159-131164, 131167, 131197, 131200, 131202, 131203.
======================================================================

  - 131148 is EXCLUDED (not authored): its own tags carry `Manual`, not
    `Automation` — a purely visual preview-vs-live comparison, per Axis 1b
    ("Manual cases are never authored as tests").
  - Verified by grep before writing anything (per the hand-off's own
    instruction): NONE of the other 16 case IDs existed anywhere in this
    framework already — the hand-off's claim that 131159-131164 were
    already automated by a prior session did not hold up; nothing was
    duplicated.
  - Appended here (not to `cms/tests/home_social_icons/test_home_social_icons_control_panel.py`,
    which is a deliberate empty stub — see its own module docstring) because
    this shared `manage-social-media-icon` surface's Control_Panel/
    pbi_129373 tests already live in this one module — one module per
    page+platform, not a second one for the same shared surface.
  - NEW BLOCKER, confirmed live 2026-09-17 (independent of ADO Bug #142266
    below): `CMS_SITE_CONTENT_AUTHOR_EMAIL`/`PASSWORD` and
    `CMS_CONTENT_CONTRIBUTOR_EMAIL`/`PASSWORD` in `.env` do NOT authenticate
    against qcdev — both attempts render Liferay's own "Authentication
    failed due to incorrect credentials or account lockout." error.
    `CMS_SITE_CONTENT_EDITOR_EMAIL`/`PASSWORD` DOES work (confirmed same
    session, same mechanism) — this is isolated to the Author/Contributor
    accounts specifically, a credential/environment gap, not a login-flow or
    locator defect. No prior test in this framework had ever exercised
    either of these two roles live before this batch (confirmed via grep).
    Blocks 131154, 131155, 131163, 131167, 131200 at their own Step 1 —
    written per the case's real intent and left to fail there honestly,
    never invented around.
  - ADO Bug #142266 (filed this session, real PRODUCT bug, independently
    reproduced): the Documents-and-Media icon-image upload picker fails
    server-side ("An unexpected error occurred while uploading your file")
    — blocks every case here whose Arrange step must create/edit an entry
    with the mandatory Social Icon Image: 131153, 131154, 131157, 131159,
    131160, 131163, 131197, 131200, 131202.
  - CONFIRMED LIVE 2026-09-17 (fresh anonymous context, no login attempt at
    all): forced-browsing directly to `manage-social-media-icon` renders the
    PUBLIC site's own "Coming Soon" placeholder, NOT a redirect to the CMS
    login form and NOT the admin form — the same mechanism this file's own
    "2026-09-16 HEAL SESSION" note already documents for a mid-session
    session drop. 131156's own expected result ("redirected to the CMS
    login page") is therefore written per the case's literal intent and
    expected to legitimately FAIL against the real product, not weakened.
  - 131160/131161/131162/131164 name SPECIFIC real production entries
    (X/Twitter, Snapchat, LinkedIn) — `PRODUCTION_ENTRY_CODES` +
    `capture_icon_baseline()`/`restore_icon_baseline()` (new methods on
    `SocialMediaIconAdminPage`) capture-then-restore each one in `finally`,
    mirroring `HomeAboutCounterAdminPage.capture_baseline()`/`restore()`'s
    identical established pattern, plus a shared `xdist_group` so none of
    them race each other. 131160's own image-replace step is deliberately
    attempted FIRST, before any other field write, so the (expected, per
    Bug #142266) failure there leaves the real row's other fields provably
    untouched.
  - 131203 is registered as an explicit `skip`, not attempted: its own
    precondition ("Ensure exactly one icon entry is Published + Active=True"
    before deleting it) requires deactivating/deleting 8 of the 9 REAL
    production social icons on qcdev with no confirmed teardown/restoration
    path — a destructive-operations authorization gap (see this project's
    own "Destructive Operations Against qcdev" incident), not a coverage or
    locator gap. Flagged for the QA Manager rather than attempted.
  - 131157 (session-expiry) and 131202 (interrupted-publish) use
    deterministic proxies rather than waiting on a real timeout/network
    flake: `page.context.clear_cookies()` and `page.context.set_offline(True)`
    respectively, applied immediately before the Save/Publish click.
  - 131200 names a "Reject" action this surface has never been confirmed to
    have (see `SocialMediaIconAdminPage.REJECT_BUTTON`/`reject()` — an
    explicit unresolved placeholder, not a guessed selector).
"""

import os
import re
import uuid

import allure
import pytest

from cms.pages.components.footer_admin_component import (
    PRODUCTION_ENTRY_CODES,
    SocialMediaIconAdminPage,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials
from core.web.browser import new_context
from web.pages.home_social_icons.home_social_icons_page import HomeSocialIconsPage

FIXTURES_SMI = os.path.join(os.path.dirname(__file__), "..", "home_social_icons", "fixtures")
FIXTURES_ORG_STRUCTURE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "web", "tests", "org_structure", "fixtures"
)

ICON_PNG_VALID = os.path.join(FIXTURES_SMI, "icon_500kb.png")
ICON_SVG_VALID = os.path.join(FIXTURES_SMI, "icon_200kb.svg")
ICON_OVERSIZED = os.path.join(FIXTURES_SMI, "icon_2_5mb.png")
ICON_UNSUPPORTED_FORMAT = os.path.join(FIXTURES_ORG_STRUCTURE, "photo.bmp")

_NO_AR_SPECIFIC_PLATFORM_CONTROL = (
    "The Platform field (PBI 129366's \"Platform Name\") is confirmed live to be a "
    "SINGLE-LOCALE combobox with exactly 9 fixed options (Facebook, X, LinkedIn, "
    "Instagram, YouTube, WhatsApp, Telegram, Snapchat, Flickr) — no distinct "
    "AR-locale \"Platform Name\" control exists anywhere on this surface (confirmed "
    "live: exactly one \"Platform\" combobox, no \"Platform — العربية\" sibling, unlike "
    "the genuinely bilingual Icon Alt Text / Social Redirect URL fields on the same "
    "form). Writing a test here would re-assert the exact same control the EN-locale "
    "case already covers — a duplicate test body, not a real additional verification "
    "(same precedent as Org Structure's AR Hero Banner gap, ADO-133311/133312)."
)

_NO_CANCEL_BUTTON = (
    "Confirmed live: this form's only two buttons are \"Save as Draft\" and \"Submit "
    "for Publishing\" — no Cancel button/link exists anywhere on the create form "
    "(same confirmed-live finding as every other manage-<slug> Object Authoring "
    "surface in this project: Department, About Hero Banner). Not invented per this "
    "task's explicit instruction."
)


def _admin(page):
    return SocialMediaIconAdminPage(page)


def _unique_alt_text_en(base: str) -> str:
    """Fresh per-invocation Icon Alt Text (EN) value — the field
    `find_entry_code_by_alt_text_en()` searches the entries list by. See
    module docstring's TEST DATA note."""
    return f"QCTEST {base} {uuid.uuid4().hex[:8]}"


def _unique_redirect_url(platform_path: str) -> str:
    """A syntactically-valid, collision-free Redirect URL whose own unique
    suffix doubles as a public-footer identity marker (matched by `href`
    substring on the anonymous-context checks below, since Social Redirect
    URL becomes the rendered footer link's own `href` — confirmed live via a
    prior session's public Home Page snapshot)."""
    return f"https://{platform_path}.example.com/qctest-{uuid.uuid4().hex[:8]}"


def _teardown(admin, alt_text_en: str) -> None:
    """Best-effort teardown, scoped by re-finding the entry via its own real
    field value (never by position) — mirrors
    `ObjectAuthoringPage.delete_entry_by_code()`'s own never-raises
    contract."""
    try:
        code = admin.find_entry_code_by_alt_text_en(alt_text_en)
        if code:
            admin.delete_entry_by_code(code)
    except Exception:  # noqa: BLE001 — best-effort teardown, never raises
        pass


_ACCESS_DENIED_EN = "Access Denied. You do not have permission to perform this action."
_ACCESS_DENIED_AR = "تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء."

_LAST_ICON_DELETE_BLOCKED = (
    "131203's own precondition (\"Ensure exactly one icon entry is Published + "
    "Active=True\" before deleting it) requires deactivating/deleting 8 of the 9 REAL "
    "production social icons on qcdev, with no confirmed teardown/restoration path — a "
    "destructive-operations authorization gap (standards.md's \"Destructive Operations "
    "Against qcdev\" incident already on record for this project), not a coverage or "
    "locator gap. Requires an explicit, ID-based human confirmation before any such "
    "irreversible change to real qcdev content is attempted — flagged to the QA Manager, "
    "not invented around."
)


def _login_as(page, role: str) -> SocialMediaIconAdminPage:
    """Logs out any cached admin session first (mirrors
    `home_about_summary_admin_page.py`'s own established `logout_and_return()`
    + `login_as()` sequence — `CmsLoginPage`'s own docstring documents that
    hitting the login path while ALREADY authenticated redirects to an
    unrelated page instead of rendering the real login form), then drives
    the real login flow for the named CMS role via
    `config.settings.cms_role_credentials()` — never the shared TEST_USER
    admin account every other test in this module uses, per standards.md's
    "Named CMS User Roles" convention for Auth-scoped/role-named cases."""
    admin = _admin(page)
    admin.logout_and_return()
    admin.login_as(*cms_role_credentials(role))
    return admin


# Public-frontend checks below (131188/131194/131196) use `HomeSocialIconsPage`
# (web/pages/home_social_icons/home_social_icons_page.py) rather than raw
# locators inline in this CMS test module, per standards.md's "no locators in
# tests" rule. These 3 cases are PBI-129373/HOME-004B ("Find us on social
# media" Home widget) cases, so this is the container their own intent
# actually needs — see that Page Object's own docstring for the confirmed-live
# container/href trail. ARCHITECTURE FIX 2026-09-16: previously imported
# `FooterComponent` (web/pages/components/footer_component.py), which despite
# its name actually resolved to this SAME Home-widget container (a Page-Object
# defect, now fixed so `FooterComponent` genuinely targets the real
# `<footer>`) — these 3 tests' own assertions/expected results are unchanged,
# only the import/class rewired to the correctly-named component. Every check
# also has a POSITIVE CONTROL (`HomeSocialIconsPage.has_production_icons()`)
# against a real production href, guarding against a false green from an
# empty/wrong container per cms-testing.md's false-green catalogue (flagged
# in review).


# ─────────────────────── Platform Name (Groups 1) ──────────────────────────

@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a valid English Platform Name saves correctly (ADO-131168)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129373
@pytest.mark.tc_131168
@pytest.mark.traceability("GLOBAL-FOOTER-TC-001")
def test_valid_platform_name_en_saves(page):
    admin = _admin(page)
    alt_en = _unique_alt_text_en("Facebook")
    try:
        with allure.step("Create a new icon, selecting Platform = Facebook, fill all other mandatory fields"):
            admin.open_icons_list()
            admin.fill_icon_form(
                platform="Facebook",
                alt_text_en=alt_en, alt_text_ar="فيسبوك تجريبي",
                redirect_url_en=_unique_redirect_url("facebook"),
                redirect_url_ar=_unique_redirect_url("facebook-ar"),
                display_order="9000", active_status=False,
            )
            admin.upload_icon_image(ICON_PNG_VALID)
        with allure.step("Submit for Publishing — the entry reaches Approved"):
            admin.save()
        with allure.step("Verify via the entries list"):
            code = admin.find_entry_code_by_alt_text_en(alt_en)
            assert code, "created entry was not found back by its own Icon Alt Text (EN)"
            assert admin.row_status_text_by_code(code) == "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a valid Arabic Platform Name saves correctly (ADO-131169)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131169
@pytest.mark.traceability("GLOBAL-FOOTER-TC-002")
@pytest.mark.skip(reason=_NO_AR_SPECIFIC_PLATFORM_CONTROL)
def test_valid_platform_name_ar_saves(page):
    pass


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that leaving the English Platform Name empty blocks save with a mandatory-field error (ADO-131170)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131170
@pytest.mark.traceability("GLOBAL-FOOTER-TC-003")
def test_empty_platform_name_en_blocks_save(page):
    # Written per the PBI's exact specified message ("Platform Name is
    # required."). CONFIRMED LIVE project-wide (Org Structure's identical
    # finding, re-verified here via the same native-checkValidity mechanism
    # — see the Page Object's is_save_error_shown()/save_error_text()): this
    # class of surface renders NO app-level bilingual message for a
    # required-field violation, only the browser's own generic English
    # string ("Please fill out this field."). This assertion is expected to
    # legitimately FAIL against the real product — the correct, honest
    # outcome per this project's convention, not weakened to match the
    # native string.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("NoPlatform")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            alt_text_en=alt_en, alt_text_ar="بدون منصة",
            redirect_url_en=_unique_redirect_url("noplat"),
            redirect_url_ar=_unique_redirect_url("noplat-ar"),
            display_order="9000", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        assert admin.is_save_error_shown()
        assert admin.save_error_text() == "Platform Name is required."
    finally:
        # Precautionary — Hero Banner's own precedent (Mandatory=No fields
        # sometimes save despite an expected rejection) means this MAY have
        # actually created a real entry if the rejection doesn't reproduce.
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that leaving the Arabic Platform Name empty blocks save with a mandatory-field error (ADO-131171)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131171
@pytest.mark.traceability("GLOBAL-FOOTER-TC-004")
@pytest.mark.skip(reason=_NO_AR_SPECIFIC_PLATFORM_CONTROL)
def test_empty_platform_name_ar_blocks_save(page):
    pass


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a Platform Name exceeding 50 characters is rejected (ADO-131172)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131172
@pytest.mark.traceability("GLOBAL-FOOTER-TC-005")
def test_platform_name_over_50_chars_rejected(page):
    # HEALED PREMISE, not a truncation trap: Platform is a picklist
    # combobox with exactly 9 real options (confirmed live), not a
    # maxlength-limited free-text field. Typing a 55-char string is
    # accepted WHILE FOCUSED (confirmed live) but CLEARS BACK TO EMPTY on
    # blur, since it matches none of the 9 real options — the real,
    # confirmed-live enforcement mechanism satisfying "an over-limit
    # Platform Name is rejected". No entry is created; no teardown needed.
    admin = _admin(page)
    admin.open_icons_list()
    over_limit_value = "Q" * 55
    admin.fill_platform_free_text(over_limit_value)
    with allure.step("Value is accepted while the field is still focused"):
        assert admin.platform_value() == over_limit_value
    with allure.step("On blur, the non-matching over-limit value is cleared (rejected)"):
        admin.blur_platform()
        assert admin.platform_value() == ""


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that special/script-injection characters entered in Platform Name are safely handled (ADO-131173)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131173
@pytest.mark.traceability("GLOBAL-FOOTER-TC-006")
def test_platform_name_script_characters_handled_safely(page):
    # Same confirmed-live mechanism as 131172: a script/HTML payload matches
    # none of the 9 real Platform options and is cleared on blur — nothing
    # unsafe can ever reach a saved value on this field. No entry is
    # created; no teardown needed.
    admin = _admin(page)
    admin.open_icons_list()
    payload = "<script>window.__qctest_xss=1</script>"
    dialogs = []
    page.on("dialog", lambda d: dialogs.append(d) or d.dismiss())
    admin.fill_platform_free_text(payload)
    admin.blur_platform()
    assert admin.platform_value() == ""
    assert dialogs == []


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that clicking Cancel on the icon form discards entered Platform Name changes (ADO-131174)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131174
@pytest.mark.traceability("GLOBAL-FOOTER-TC-007")
@pytest.mark.skip(reason=_NO_CANCEL_BUTTON)
def test_cancel_discards_platform_name_changes(page):
    pass


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a saved Platform Name persists after reload (ADO-131175)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131175
@pytest.mark.traceability("GLOBAL-FOOTER-TC-008")
def test_platform_name_persists_after_reload(page):
    admin = _admin(page)
    alt_en = _unique_alt_text_en("X-Persist")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="X",
            alt_text_en=alt_en, alt_text_ar="اكس تجريبي",
            redirect_url_en=_unique_redirect_url("x"),
            redirect_url_ar=_unique_redirect_url("x-ar"),
            display_order="9001", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        admin.open_entry_by_code(code)
        assert admin.platform_value() == "X"
    finally:
        _teardown(admin, alt_en)


# ────────────────────── Social Icon Image (Group 2) ────────────────────────

@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that uploading a valid PNG icon image within the size limit saves correctly (ADO-131176)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129373
@pytest.mark.tc_131176
@pytest.mark.traceability("GLOBAL-FOOTER-TC-009")
def test_valid_png_icon_image_saves(page):
    admin = _admin(page)
    alt_en = _unique_alt_text_en("LinkedIn-PNG")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="LinkedIn",
            alt_text_en=alt_en, alt_text_ar="لينكد ان تجريبي",
            redirect_url_en=_unique_redirect_url("linkedin"),
            redirect_url_ar=_unique_redirect_url("linkedin-ar"),
            display_order="9002", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        assert admin.row_status_text_by_code(code) == "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that uploading a valid SVG icon image within the size limit saves correctly (ADO-131177)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131177
@pytest.mark.traceability("GLOBAL-FOOTER-TC-010")
def test_valid_svg_icon_image_saves(page):
    admin = _admin(page)
    alt_en = _unique_alt_text_en("Instagram-SVG")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Instagram",
            alt_text_en=alt_en, alt_text_ar="انستغرام تجريبي",
            redirect_url_en=_unique_redirect_url("instagram"),
            redirect_url_ar=_unique_redirect_url("instagram-ar"),
            display_order="9003", active_status=False,
        )
        admin.upload_icon_image(ICON_SVG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        assert admin.row_status_text_by_code(code) == "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that leaving Icon Image empty blocks save with a mandatory-field error (ADO-131178)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131178
@pytest.mark.traceability("GLOBAL-FOOTER-TC-011")
def test_empty_icon_image_blocks_save(page):
    # Same disclosed native-message caveat as 131170 — expected to
    # legitimately fail the exact-message assertion against the real
    # product; the rejection ITSELF (is_save_error_shown()) is the part
    # this project's convention treats as the load-bearing check.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("NoImage")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="YouTube",
            alt_text_en=alt_en, alt_text_ar="بدون صورة",
            redirect_url_en=_unique_redirect_url("noimage"),
            redirect_url_ar=_unique_redirect_url("noimage-ar"),
            display_order="9000", active_status=False,
        )
        admin.save()
        assert admin.is_save_error_shown()
        assert admin.save_error_text() == "Social Icon Image is required."
    finally:
        # Precautionary — Org Structure's own precedent (Mandatory=No fields
        # sometimes save despite an expected rejection) means this MAY have
        # actually created a real entry if the rejection doesn't reproduce.
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that uploading an unsupported image format is rejected (ADO-131179)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131179
@pytest.mark.traceability("GLOBAL-FOOTER-TC-012")
def test_unsupported_icon_image_format_rejected(page):
    # .bmp is confirmed live NOT in this surface's own accepted-format list
    # (helper text: ".jpg,.jpeg,.png,.svg,.gif,.webp") — reusing the
    # existing tiny org_structure `photo.bmp` fixture (cross-page fixture
    # reuse for the same literal file is an established, accepted pattern
    # on this project). `upload_icon_image_expect_rejected()` is reliable
    # for this small/instant-rejection case (see its own docstring for the
    # documented large-file unreliability that does NOT apply here).
    admin = _admin(page)
    admin.open_icons_list()
    rejected = admin.upload_icon_image_expect_rejected(ICON_UNSUPPORTED_FORMAT)
    assert rejected


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that uploading an icon image exceeding 1 MB is rejected (ADO-131180)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131180
@pytest.mark.traceability("GLOBAL-FOOTER-TC-013")
def test_oversized_icon_image_rejected(page):
    # DISCREPANCY, reported not silently resolved: ADO-131180's own title
    # says "exceeding 1 MB"; PBI 129366's field table says max "2 MB"; the
    # LIVE form's own helper text (confirmed this session) says "no larger
    # than 10 MB" -- three different numbers. This test uses a 2.5MB fixture
    # (exceeds all three candidate limits) against the PBI's 2MB figure as
    # the most authoritative source. Whether ANY of the three numbers is
    # actually enforced server-side was NOT independently re-verified this
    # session (a submit-triggering probe was blocked by this session's own
    # sandbox) -- this assertion may legitimately fail if the real enforced
    # limit is 10MB (or if nothing is enforced at all, mirroring the
    # identical class of finding already logged on Org Structure's About
    # Hero Banner surface). Uses the DIRECT upload+submit+status flow, not
    # upload_icon_image_expect_rejected() (confirmed project-wide unreliable
    # for a multi-MB file — see that method's own docstring).
    admin = _admin(page)
    alt_en = _unique_alt_text_en("Oversized")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="WhatsApp",
            alt_text_en=alt_en, alt_text_ar="حجم كبير",
            redirect_url_en=_unique_redirect_url("oversized"),
            redirect_url_ar=_unique_redirect_url("oversized-ar"),
            display_order="9000", active_status=False,
        )
        admin.upload_icon_image(ICON_OVERSIZED)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        if code:
            admin.open_entry_by_code(code)
            allure.attach(
                page.screenshot(full_page=True),
                name=f"ADO-131180 evidence — entry {code} after oversized (2.5MB) upload + Submit",
                attachment_type=allure.attachment_type.PNG,
            )
        with allure.step("The oversized file is rejected — the entry does not reach Approved"):
            assert code == "" or admin.row_status_text_by_code(code) != "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a saved icon image persists after reload (ADO-131181)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131181
@pytest.mark.traceability("GLOBAL-FOOTER-TC-014")
def test_icon_image_persists_after_reload(page):
    admin = _admin(page)
    alt_en = _unique_alt_text_en("Telegram-Image")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Telegram",
            alt_text_en=alt_en, alt_text_ar="تيليجرام تجريبي",
            redirect_url_en=_unique_redirect_url("telegram"),
            redirect_url_ar=_unique_redirect_url("telegram-ar"),
            display_order="9004", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        admin.open_entry_by_code(code)
        allure.attach(
            page.screenshot(full_page=True),
            name=f"ADO-131181 evidence — entry {code} reopened after reload/reopen",
            attachment_type=allure.attachment_type.PNG,
        )
        assert "icon_500kb" in admin.uploaded_filename(admin.FIELD_SOCIAL_ICON_IMAGE)
    finally:
        _teardown(admin, alt_en)


# ─────────────────────── Social Redirect URL (Group 3) ─────────────────────

@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a valid Platform URL saves correctly (ADO-131182)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129373
@pytest.mark.tc_131182
@pytest.mark.traceability("GLOBAL-FOOTER-TC-015")
def test_valid_redirect_url_saves(page):
    admin = _admin(page)
    alt_en = _unique_alt_text_en("Snapchat-URL")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Snapchat",
            alt_text_en=alt_en, alt_text_ar="سناب شات تجريبي",
            redirect_url_en=_unique_redirect_url("snapchat"),
            redirect_url_ar=_unique_redirect_url("snapchat-ar"),
            display_order="9005", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        assert admin.row_status_text_by_code(code) == "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that leaving Platform URL empty blocks save with a mandatory-field error (ADO-131183)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131183
@pytest.mark.traceability("GLOBAL-FOOTER-TC-016")
def test_empty_redirect_url_blocks_save(page):
    # Per the PBI's own configured message for this field ("Please enter a
    # valid URL."). Expected to legitimately fail against the real native
    # English message, same disclosed class of finding as 131170/131178.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("NoURL")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Flickr",
            alt_text_en=alt_en, alt_text_ar="بدون رابط",
            redirect_url_ar=_unique_redirect_url("nourl-ar"),
            display_order="9000", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        assert admin.is_save_error_shown()
        assert admin.save_error_text() == "Please enter a valid URL."
    finally:
        # Precautionary — same rationale as 131170/131178's finally blocks.
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that an invalid URL format is rejected with the configured error message (ADO-131184)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131184
@pytest.mark.traceability("GLOBAL-FOOTER-TC-017")
def test_invalid_url_format_rejected(page):
    # CONFIRMED LIVE this session: Social Redirect URL is a native
    # `type="text"` input, NOT `type="url"` -- the browser's own
    # `checkValidity()` NEVER catches an invalid URL format on this field
    # (confirmed: returns valid=true even for "not-a-valid-url"). This
    # assertion is written per the case's intended (rejected) behavior and
    # is EXPECTED TO LEGITIMATELY FAIL unless a custom, app-level
    # format-validation check exists that this session could not trigger (a
    # submit-triggering probe was blocked by this session's own sandbox) --
    # not weakened to match the confirmed absence of native validation.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("BadURL")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Facebook",
            alt_text_en=alt_en, alt_text_ar="رابط غير صالح",
            redirect_url_en="not-a-valid-url",
            redirect_url_ar="رابط-غير-صالح",
            display_order="9000", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        assert admin.is_save_error_shown()
        assert admin.save_error_text() == "Please enter a valid URL."
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a Platform URL exceeding 500 characters is rejected (ADO-131185)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131185
@pytest.mark.traceability("GLOBAL-FOOTER-TC-018")
def test_redirect_url_over_500_chars_rejected(page):
    # UNLIKE Org Structure's Department form, this field carries NO native
    # `maxlength` (confirmed live: a 540-char fill persists in full, not
    # truncated) -- so this IS a real save-attempt assertion, not a
    # truncation assertion. `is_save_error_shown()` can only detect this via
    # its generic custom-alert fallback (native checkValidity() has no
    # length constraint on a plain type="text" field) -- disclosed as
    # possibly failing if the 500-char limit is unenforced server-side.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("LongURL")
    over_limit_url = "https://example.com/" + ("q" * 500)
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="X",
            alt_text_en=alt_en, alt_text_ar="رابط طويل",
            redirect_url_en=over_limit_url,
            redirect_url_ar=_unique_redirect_url("longurl-ar"),
            display_order="9000", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        assert admin.is_save_error_shown()
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a saved Platform URL persists after reload (ADO-131186)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131186
@pytest.mark.traceability("GLOBAL-FOOTER-TC-019")
def test_redirect_url_persists_after_reload(page):
    admin = _admin(page)
    alt_en = _unique_alt_text_en("URLPersist")
    redirect_url_en = _unique_redirect_url("urlpersist")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="LinkedIn",
            alt_text_en=alt_en, alt_text_ar="استمرارية الرابط",
            redirect_url_en=redirect_url_en,
            redirect_url_ar=_unique_redirect_url("urlpersist-ar"),
            display_order="9006", active_status=False,
        )
        admin.upload_icon_image(ICON_SVG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        admin.open_entry_by_code(code)
        assert admin.field_value(admin.FIELD_SOCIAL_REDIRECT_URL_EN) == redirect_url_en
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that an icon cannot be published while Active=True but its Platform URL is invalid (ADO-131187)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.workflow
@pytest.mark.pbi_129373
@pytest.mark.tc_131187
@pytest.mark.traceability("GLOBAL-FOOTER-TC-020")
def test_active_true_with_invalid_url_cannot_publish(page):
    # PRODUCTION-CONTENT CAUTION (see module docstring): Active=True is
    # required by the case itself. Display Order is set to a very high
    # value (last position) and the entry is deleted in `finally`
    # immediately after the one assertion, to minimize any window where an
    # invalid-URL icon could appear on the real public footer if this
    # surface does NOT actually enforce the rule under test (confirmed
    # live: native checkValidity() cannot catch this — see 131184's own
    # docstring) — expected to possibly fail, not weakened to force a pass.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("InvalidURLActive")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Flickr",
            alt_text_en=alt_en, alt_text_ar="رابط غير صالح ونشط",
            redirect_url_en="not-a-valid-url",
            redirect_url_ar="رابط-غير-صالح",
            display_order="9999", active_status=True,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        with allure.step("The entry with an invalid URL does not reach Approved despite Active=True"):
            assert code == "" or admin.row_status_text_by_code(code) != "Approved"
    finally:
        _teardown(admin, alt_en)


# ─────────────────────────── Display Order (Group 4) ───────────────────────

@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a valid positive Display Order value saves and reflects the icon's frontend position (ADO-131188)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129373
@pytest.mark.tc_131188
@pytest.mark.traceability("GLOBAL-FOOTER-TC-021")
def test_valid_display_order_reflects_frontend_position(page, browser):
    # PRODUCTION-CONTENT CAUTION (see module docstring): Active=True AND
    # Display Order="1" is required by the case itself to observe a
    # frontend position effect — this is the test in this module most
    # likely to visibly (if briefly) affect the real public Home widget's
    # rendered order. Wrapped tightly in try/finally with an immediate
    # teardown right after the one frontend read. Uses the anonymous-context
    # rule (standards.md) for the public-page read.
    #
    # Scoped to the CONFIRMED-LIVE "Find us on social media" Home-page widget
    # container (see `HomeSocialIconsPage`, `div.qc-home-social` — NOT the
    # real `<footer>`; this case is PBI-129373/HOME-004B) rather than a bare
    # `[href*="qctest-"]` selector — the latter would be trivially non-empty
    # for our own test-created link regardless of whether it is in the right
    # container at all, never actually exercising the ordering claim (flagged
    # in review). CONFIRMED LIVE (read-only `display_order_value()` probe
    # against the real QC-SMI-facebook/QC-SMI-x/QC-SMI-whatsapp entries,
    # this session): rendered order DOES track each entry's own Display
    # Order value (Facebook=100, X=200, WhatsApp=900 — the exact
    # left-to-right render order) — this is real evidence the field drives
    # position, not an assumption. Display Order="1" here is below every
    # production value checked (100-900), so our entry is expected to render
    # at index 0; the assertion below is kept at the weaker, still fully
    # justified "before WhatsApp" (rather than "== 0") since only 3 of the 9
    # real entries' own values were independently checked this session.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("PositionCheck")
    redirect_url_en = _unique_redirect_url("positioncheck")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Facebook",
            alt_text_en=alt_en, alt_text_ar="فحص الموضع",
            redirect_url_en=redirect_url_en,
            redirect_url_ar=_unique_redirect_url("positioncheck-ar"),
            display_order="1", active_status=True,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        assert admin.row_status_text_by_code(code) == "Approved"

        marker = redirect_url_en.split("qctest-")[1]
        anon_ctx = new_context(browser, use_auth_state=False)
        anon_page = anon_ctx.new_page()
        try:
            home_widget = HomeSocialIconsPage(anon_page)
            home_widget.open_home()
            with allure.step("Positive control: the real production icons are present in this container"):
                assert home_widget.has_production_icons()
            with allure.step("The new icon (Display Order=1) appears before WhatsApp's real, later-ordered icon"):
                our_index = home_widget.index_of_href_marker(marker)
                whatsapp_index = home_widget.index_of_production_whatsapp()
                assert our_index != -1
                assert our_index < whatsapp_index
        finally:
            anon_ctx.close()
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a Display Order value of zero is rejected (ADO-131189)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131189
@pytest.mark.traceability("GLOBAL-FOOTER-TC-022")
def test_display_order_zero_rejected(page):
    # Native `min`/`max` on this spinbutton are confirmed live to be
    # `-2147483648`/`2147483647` (does not encode "must be positive"),
    # mirroring Org Structure's identical DISPLAY ORDER finding — a real
    # server-side rejection (if any) was NOT independently re-verified this
    # session (submit-triggering probes were blocked by this session's own
    # sandbox). Written per the PBI's stated business rule.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("ZeroOrder")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Instagram",
            alt_text_en=alt_en, alt_text_ar="ترتيب صفر",
            redirect_url_en=_unique_redirect_url("zeroorder"),
            redirect_url_ar=_unique_redirect_url("zeroorder-ar"),
            display_order="0", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code == "" or admin.row_status_text_by_code(code) != "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a negative Display Order value is rejected (ADO-131190)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131190
@pytest.mark.traceability("GLOBAL-FOOTER-TC-023")
def test_display_order_negative_rejected(page):
    admin = _admin(page)
    alt_en = _unique_alt_text_en("NegativeOrder")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="YouTube",
            alt_text_en=alt_en, alt_text_ar="ترتيب سلبي",
            redirect_url_en=_unique_redirect_url("negorder"),
            redirect_url_ar=_unique_redirect_url("negorder-ar"),
            display_order="-5", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        if code:
            admin.open_entry_by_code(code)
            allure.attach(
                page.screenshot(full_page=True),
                name=f"ADO-131190 evidence — entry {code} after negative (-5) Display Order + Submit",
                attachment_type=allure.attachment_type.PNG,
            )
        assert code == "" or admin.row_status_text_by_code(code) != "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a non-numeric Display Order value is rejected (ADO-131191)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131191
@pytest.mark.traceability("GLOBAL-FOOTER-TC-024")
def test_display_order_non_numeric_rejected(page):
    # Display Order is confirmed live a native `type="number"` spinbutton
    # (same as Org Structure's Department form) — Playwright's own `.fill()`
    # RAISES for a non-numeric string on this input type ("Cannot type text
    # into input[type=number]") rather than producing an in-app rejection.
    # Inferred from the identical, already-confirmed mechanism on Org
    # Structure's Display Order field (same native input type, confirmed
    # live for THIS object too via its own `type="number"` attribute) —
    # not independently re-typed into a live submit this session. No entry
    # is created; no teardown needed.
    admin = _admin(page)
    admin.open_icons_list()
    # `match=` anchors on the EXACT confirmed-live Playwright error string
    # for this mechanism ("Cannot type text into input[type=number]", per
    # org_structure_admin_page.py's own TC-048 finding on the identical
    # native input type) — a looser pattern (e.g. matching on "fill") would
    # also match an unrelated locator-timeout message and let this test
    # pass for the wrong reason (flagged in review).
    with pytest.raises(Exception, match=re.escape("input[type=number]")):
        admin.fill_number(admin.FIELD_DISPLAY_ORDER, "abc")


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a saved Display Order value persists after reload (ADO-131192)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131192
@pytest.mark.traceability("GLOBAL-FOOTER-TC-025")
def test_display_order_persists_after_reload(page):
    admin = _admin(page)
    alt_en = _unique_alt_text_en("OrderPersist")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="WhatsApp",
            alt_text_en=alt_en, alt_text_ar="استمرارية الترتيب",
            redirect_url_en=_unique_redirect_url("orderpersist"),
            redirect_url_ar=_unique_redirect_url("orderpersist-ar"),
            display_order="42", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        admin.open_entry_by_code(code)
        assert admin.display_order_value() == "42"
    finally:
        _teardown(admin, alt_en)


# ─────────────────────────── Active Status (Group 5) ───────────────────────

@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that setting Active Status = True on a new entry saves correctly (ADO-131193)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_129373
@pytest.mark.tc_131193
@pytest.mark.traceability("GLOBAL-FOOTER-TC-026")
def test_active_status_true_saves(page):
    # PRODUCTION-CONTENT CAUTION: Active=True + Approved is required by the
    # case itself. Verified purely on the ADMIN side (re-opening the entry
    # and reading the checkbox back) rather than also round-tripping through
    # the public footer, to keep this test's live-content exposure as short
    # as possible — Display Order is set to the highest value in this
    # module's own range, and teardown is immediate.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("ActiveTrue")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Telegram",
            alt_text_en=alt_en, alt_text_ar="نشط",
            redirect_url_en=_unique_redirect_url("activetrue"),
            redirect_url_ar=_unique_redirect_url("activetrue-ar"),
            display_order="9998", active_status=True,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        admin.open_entry_by_code(code)
        assert admin.is_active_status_checked() is True
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that setting Active Status = False on a new entry saves correctly and excludes it once published (ADO-131194)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_129373
@pytest.mark.tc_131194
@pytest.mark.traceability("GLOBAL-FOOTER-TC-027")
def test_active_status_false_excludes_from_public_footer(page, browser):
    # SAFE by design: Active=False should never render publicly regardless
    # of Approved status, so this test cannot itself add a visible icon to
    # the real public Home widget. Anonymous-context read per standards.md's
    # mandatory rule. PBI-129373/HOME-004B case — asserts against the Home
    # widget container (`HomeSocialIconsPage`), not the real `<footer>` (see
    # module docstring's ARCHITECTURE FIX note).
    admin = _admin(page)
    alt_en = _unique_alt_text_en("ActiveFalse")
    redirect_url_en = _unique_redirect_url("activefalse")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="Snapchat",
            alt_text_en=alt_en, alt_text_ar="غير نشط",
            redirect_url_en=redirect_url_en,
            redirect_url_ar=_unique_redirect_url("activefalse-ar"),
            display_order="9997", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        assert admin.row_status_text_by_code(code) == "Approved"

        marker = redirect_url_en.split("qctest-")[1]
        anon_ctx = new_context(browser, use_auth_state=False)
        anon_page = anon_ctx.new_page()
        try:
            home_widget = HomeSocialIconsPage(anon_page)
            home_widget.open_home()
            with allure.step("Positive control: the real production icons are present in this container"):
                assert home_widget.has_production_icons()
            with allure.step("The Active=False icon is excluded from the public Home widget"):
                assert not home_widget.has_icon_with_href_marker(marker)
        finally:
            anon_ctx.close()
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a saved Active Status toggle persists after reload (ADO-131195)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129373
@pytest.mark.tc_131195
@pytest.mark.traceability("GLOBAL-FOOTER-TC-028")
def test_active_status_persists_after_reload(page):
    # Uses Active=False (the toggle value under test only needs to persist,
    # not be observed publicly) to keep this test's live-content exposure
    # to zero.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("TogglePersist")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="X",
            alt_text_en=alt_en, alt_text_ar="استمرارية الحالة",
            redirect_url_en=_unique_redirect_url("togglepersist"),
            redirect_url_ar=_unique_redirect_url("togglepersist-ar"),
            display_order="9000", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        admin.open_entry_by_code(code)
        assert admin.is_active_status_checked() is False
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that Active Status = True has no frontend effect while the entry's workflow status is not Published (ADO-131196)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.workflow
@pytest.mark.pbi_129373
@pytest.mark.tc_131196
@pytest.mark.traceability("GLOBAL-FOOTER-TC-029")
def test_active_true_draft_has_no_frontend_effect(page, browser):
    # SAFE by design: deliberately uses Save as Draft (never Submit for
    # Publishing), so this entry can NEVER actually reach the real public
    # Home widget regardless of Active=True — mirrors ObjectAuthoringPage's
    # own confirmed-live Preview-banner wording ("Visitors do not see this")
    # for every Draft record project-wide. Anonymous-context read per
    # standards.md's mandatory rule. PBI-129373/HOME-004B case — asserts
    # against the Home widget container (`HomeSocialIconsPage`), not the real
    # `<footer>` (see module docstring's ARCHITECTURE FIX note).
    #
    # NAMED, DISCLOSED RISK (not independently verified this session): this
    # test's own `find_entry_code_by_alt_text_en()` call opens EVERY
    # non-`QC-SMI-*` row via `open_entry_by_code()`, which waits on
    # `CANCEL_AND_ADD_NEW_LINK`. That link IS confirmed present on this
    # object's APPROVED editing banner (see the Page Object's own docstring)
    # but was NOT independently re-confirmed on a genuine DRAFT entry of
    # THIS object specifically — all 10 real existing rows are Approved, so
    # there was no live Draft row to check read-only. If it turns out to be
    # absent on this object's Draft banner (unlike the base class's own
    # project-wide note that it is present in both), this test would fail on
    # `assert code` and the created Draft entry would be left behind
    # (`_teardown()` calls the same lookup and would fail the same way) —
    # flagged here as a named risk against this specific test, not silently
    # presented as covered.
    admin = _admin(page)
    alt_en = _unique_alt_text_en("ActiveDraft")
    redirect_url_en = _unique_redirect_url("activedraft")
    try:
        admin.open_icons_list()
        admin.fill_icon_form(
            platform="LinkedIn",
            alt_text_en=alt_en, alt_text_ar="نشط ومسودة",
            redirect_url_en=redirect_url_en,
            redirect_url_ar=_unique_redirect_url("activedraft-ar"),
            display_order="1", active_status=True,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save_as_draft()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        assert admin.row_status_text_by_code(code) == "Draft"

        marker = redirect_url_en.split("qctest-")[1]
        anon_ctx = new_context(browser, use_auth_state=False)
        anon_page = anon_ctx.new_page()
        try:
            home_widget = HomeSocialIconsPage(anon_page)
            home_widget.open_home()
            with allure.step("Positive control: the real production icons are present in this container"):
                assert home_widget.has_production_icons()
            with allure.step("Active=True has no frontend effect while the entry is still Draft"):
                assert not home_widget.has_icon_with_href_marker(marker)
        finally:
            anon_ctx.close()
    finally:
        _teardown(admin, alt_en)


# ═══════════════════════ Batch 2 — CMS Workflow/RBAC/Publish Lifecycle ═════
# PBI 129373, ADO 131148/131153-131157/131159-131164/131167/131197/131200/
# 131202/131203. See module docstring's "BATCH 2 ADDED 2026-09-17" section
# for the full blocker trail (credential failures, ADO Bug #142266, the
# confirmed-live forced-browsing finding, and the destructive-ops skip).
# 131148 excluded (Manual tag, not authored).

@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a Site Content Editor can access and publish the Social Media Icons section directly (ADO-131153)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131153")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129373
@pytest.mark.tc_131153
@pytest.mark.traceability("GLOBAL-FOOTER-TC-030")
def test_site_content_editor_can_access_and_publish_directly(page):
    # Named-role login per this case's own Step 1 ("Log in to CMS as Site
    # Content Editor") — every other test in this module uses the shared
    # TEST_USER super-admin account instead, but this is an Auth-category
    # case whose own subject IS the named role (standards.md's "Named CMS
    # User Roles").
    admin = _login_as(page, "Site Content Editor")
    alt_en = _unique_alt_text_en("EditorDirectPublish")
    try:
        with allure.step("Navigate to Home Page -> Social Media Icons Section; add/edit controls are enabled"):
            admin.open_new_entry_form()
            assert admin.is_visible(admin.SAVE_AS_DRAFT_BUTTON)
            assert admin.is_visible(admin.SUBMIT_FOR_PUBLISHING_BUTTON)
        with allure.step("Configure a new icon entry and click Publish"):
            # BLOCKED by ADO Bug #142266 (see module docstring) — the
            # mandatory Social Icon Image upload fails server-side.
            admin.fill_icon_form(
                platform="Flickr",
                alt_text_en=alt_en, alt_text_ar="ناشر مباشر",
                redirect_url_en=_unique_redirect_url("editordirect"),
                redirect_url_ar=_unique_redirect_url("editordirect-ar"),
                display_order="9000", active_status=False,
            )
            admin.upload_icon_image(ICON_PNG_VALID)
            admin.save()
        with allure.step("Entry publishes immediately — no additional approval step required"):
            code = admin.find_entry_code_by_alt_text_en(alt_en)
            assert code, "created entry was not found back by its own Icon Alt Text (EN)"
            assert admin.row_status_text_by_code(code) == "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a Site Content Author can access the section but cannot publish directly (ADO-131154)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131154")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.pbi_129373
@pytest.mark.tc_131154
@pytest.mark.traceability("GLOBAL-FOOTER-TC-031")
def test_site_content_author_can_access_but_cannot_publish_directly(page):
    # BLOCKED — see module docstring's "NEW BLOCKER" note: Site Content
    # Author's .env credentials do not authenticate live against qcdev
    # (confirmed 2026-09-17). Written per the case's own real intent and
    # left to fail honestly at Step 1, not invented around.
    with allure.step("Log in to CMS as Site Content Author"):
        admin = _login_as(page, "Site Content Author")
    alt_en = _unique_alt_text_en("AuthorNoDirect")
    try:
        with allure.step("Navigate to Home Page -> Social Media Icons Section; add/edit controls are enabled"):
            admin.open_new_entry_form()
        with allure.step("Configure a new icon entry and attempt to Publish"):
            admin.fill_icon_form(
                platform="Telegram",
                alt_text_en=alt_en, alt_text_ar="مؤلف بدون نشر مباشر",
                redirect_url_en=_unique_redirect_url("authornodirect"),
                redirect_url_ar=_unique_redirect_url("authornodirect-ar"),
                display_order="9000", active_status=False,
            )
            admin.upload_icon_image(ICON_PNG_VALID)
            admin.save()
        with allure.step("Only Submit for Review is effective — entry moves to Pending Review, not Published"):
            # Independent, second reason this may legitimately fail even
            # past the credential blocker: this project has already twice
            # confirmed live (test_home_promo_banners_control_panel.py,
            # test_home_strategic_direction_control_panel.py) that this
            # Object Authoring state machine has no separate Pending Review
            # status — only Draft/Approved.
            code = admin.find_entry_code_by_alt_text_en(alt_en)
            assert code
            assert admin.row_status_text_by_code(code) == "Pending review"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a user without Site Content Editor/Author role is denied access to the Social Media Icons section (ADO-131155)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131155")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129373
@pytest.mark.tc_131155
@pytest.mark.traceability("GLOBAL-FOOTER-TC-032")
def test_role_without_editor_author_assignment_denied_access(page):
    # BLOCKED — see module docstring's "NEW BLOCKER" note: Content
    # Contributor's .env credentials do not authenticate live against
    # qcdev (confirmed 2026-09-17). Content Contributor is this project's
    # lowest-privilege named role (standards.md's Named CMS User Roles
    # table) — the natural choice for "a role with no assignment to this
    # section", per that same section's "pick the role whose expected
    # privilege level matches the scenario" guidance; the case does not
    # name one explicitly.
    with allure.step("Log in with a role that has no assignment to the Home Page Social Media Icons section"):
        admin = _login_as(page, "Content Contributor")
    with allure.step("Attempt to navigate to Home Page -> Social Media Icons Section"):
        admin.open_new_entry_form()
    with allure.step("Access Denied is shown; no section content is exposed"):
        # A second, independent reason this may legitimately fail even past
        # the credential blocker: this exact surface is confirmed LIVE
        # (module docstring) to render the PUBLIC "Coming Soon" placeholder
        # for an unauthenticated/denied session, not an "Access Denied"
        # message — written per the case's literal expected result, not
        # weakened to match the confirmed-different real behavior.
        body_text = page.locator("body").inner_text()
        assert (_ACCESS_DENIED_EN in body_text) or (_ACCESS_DENIED_AR in body_text)
        assert not admin.is_visible(admin.SAVE_AS_DRAFT_BUTTON)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that an unauthenticated user forced-browsing directly to the CMS Social Media Icons management URL is redirected to login (ADO-131156)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131156")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.pbi_129373
@pytest.mark.tc_131156
@pytest.mark.traceability("GLOBAL-FOOTER-TC-033")
def test_unauthenticated_forced_browsing_redirects_to_login(page):
    admin = _admin(page)
    with allure.step("Ensure no active CMS session (log out)"):
        admin.logout_and_return()
    with allure.step("Enter the direct URL to the Home Page Social Media Icons CMS management screen"):
        admin.open_anonymous(admin._manage_url())
    with allure.step("User is redirected to the CMS login page; the management screen is never rendered"):
        # CONFIRMED LIVE 2026-09-17 (module docstring): this surface instead
        # renders the PUBLIC site's own "Coming Soon" placeholder for an
        # unauthenticated request — the same mechanism this file's own
        # "2026-09-16 HEAL SESSION" note documents for a mid-session drop.
        # Written per the case's literal expected result and expected to
        # legitimately FAIL against the real product, not weakened to match
        # the confirmed-different real behavior.
        login = CmsLoginPage(page)
        assert page.locator(login.USERNAME_INPUT).count() > 0, (
            "expected a redirect to the real CMS login form — got the public "
            "'Coming Soon' placeholder instead (confirmed live, see module docstring)"
        )
        assert not admin.is_visible(admin.SAVE_AS_DRAFT_BUTTON)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that an Editor's expired session during editing prompts re-authentication without silently discarding in-progress work (ADO-131157)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131157")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.pbi_129373
@pytest.mark.tc_131157
@pytest.mark.traceability("GLOBAL-FOOTER-TC-034")
def test_editor_session_expiry_during_editing_prompts_reauth(page):
    # Deterministic proxy for "wait for the session to expire per configured
    # timeout" (module docstring) — `page.context.clear_cookies()` right
    # before Save, rather than an actual multi-minute real timeout.
    admin = _login_as(page, "Site Content Editor")
    alt_en = _unique_alt_text_en("SessionExpiry")
    try:
        with allure.step("Open the Add Icon form"):
            admin.open_new_entry_form()
        with allure.step("Enter field values"):
            # BLOCKED by ADO Bug #142266 (see module docstring) before the
            # session-expiry mechanism under test is even reached.
            admin.fill_icon_form(
                platform="WhatsApp",
                alt_text_en=alt_en, alt_text_ar="انتهاء الجلسة",
                redirect_url_en=_unique_redirect_url("sessionexpiry"),
                redirect_url_ar=_unique_redirect_url("sessionexpiry-ar"),
                display_order="9000", active_status=False,
            )
            admin.upload_icon_image(ICON_PNG_VALID)
        with allure.step("Session expires (simulated via a real cookie-clear)"):
            page.context.clear_cookies()
        with allure.step("Click Save"):
            admin.save()
        with allure.step("User is prompted to re-authenticate; the save neither silently succeeds nor silently discards data unexplained"):
            login = CmsLoginPage(page)
            assert page.locator(login.USERNAME_INPUT).count() > 0, (
                "expected a re-authentication prompt after the dropped session's Save "
                "click — see the confirmed-different 'Coming Soon' mechanism in the "
                "module docstring if this fails for that reason instead"
            )
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that an Editor can add a new social icon and see it appear on the live Home page after publishing (ADO-131159)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131159")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129373
@pytest.mark.tc_131159
@pytest.mark.traceability("GLOBAL-FOOTER-TC-035")
def test_editor_adds_new_icon_appears_live_after_publish(page, browser):
    admin = _login_as(page, "Site Content Editor")
    alt_en = _unique_alt_text_en("YouTubeNew")
    redirect_url_en = _unique_redirect_url("youtubenew")
    try:
        with allure.step("Navigate to Home Page -> Social Media Icons Section and click Add"):
            admin.open_new_entry_form()
        with allure.step("Fill Platform=YouTube, upload icon, Platform URL, Display Order=6, Active=True"):
            # BLOCKED by ADO Bug #142266 (see module docstring).
            admin.fill_icon_form(
                platform="YouTube",
                alt_text_en=alt_en, alt_text_ar="يوتيوب جديد",
                redirect_url_en=redirect_url_en,
                redirect_url_ar=_unique_redirect_url("youtubenew-ar"),
                display_order="6", active_status=True,
            )
            admin.upload_icon_image(ICON_PNG_VALID)
        with allure.step("Click Publish — Liferay success toast shown; entry status becomes Published"):
            admin.save()
            code = admin.find_entry_code_by_alt_text_en(alt_en)
            assert code
            assert admin.row_status_text_by_code(code) == "Approved"
        with allure.step("Load the live Home page — YouTube icon appears in the section"):
            # Presence-only, not an exact index=5 assertion — this session
            # independently confirmed only 3 of the 9 real entries' own
            # Display Order values (see this file's tc_131188 comment); a
            # precise position claim beyond "present" is not justified here.
            marker = redirect_url_en.split("qctest-")[1]
            anon_ctx = new_context(browser, use_auth_state=False)
            anon_page = anon_ctx.new_page()
            try:
                home_widget = HomeSocialIconsPage(anon_page)
                home_widget.open_home()
                assert home_widget.has_production_icons()
                assert home_widget.has_icon_with_href_marker(marker)
            finally:
                anon_ctx.close()
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that an Editor can edit an existing icon's image, URL, and order and see the change reflected live (ADO-131160)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131160")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129373
@pytest.mark.tc_131160
@pytest.mark.traceability("GLOBAL-FOOTER-TC-036")
@pytest.mark.xdist_group("smi_production_rows")
def test_editor_edits_existing_icon_image_url_order(page, browser):
    admin = _login_as(page, "Site Content Editor")
    entry_code = PRODUCTION_ENTRY_CODES["X"]
    baseline = admin.capture_icon_baseline(entry_code)
    new_redirect_url = _unique_redirect_url("xtwitter-edit")
    try:
        with allure.step('Open the existing "X/Twitter" entry for edit'):
            admin.open_entry_by_code(entry_code)
            assert admin.platform_value() == "X"
        with allure.step("Replace the icon image, change Platform URL, change Display Order to 1"):
            # Image write attempted FIRST, in isolation, before any other
            # field: this is the confirmed-BLOCKED step (ADO Bug #142266 —
            # see module docstring). No other field is touched/saved before
            # this, so the real production row is provably unmutated when
            # (as expected) this raises.
            admin.upload_icon_image(ICON_SVG_VALID)
            admin.fill_icon_form(redirect_url_en=new_redirect_url, display_order="1")
            admin.save()
        with allure.step("Success toast shown; entry re-published with updated values"):
            assert admin.current_status() == "Approved"
        with allure.step("Live Home page: X/Twitter renders at the new position, new image, new URL"):
            marker = new_redirect_url.split("qctest-")[1]
            anon_ctx = new_context(browser, use_auth_state=False)
            anon_page = anon_ctx.new_page()
            try:
                home_widget = HomeSocialIconsPage(anon_page)
                home_widget.open_home()
                assert home_widget.has_production_icons()
                assert home_widget.has_icon_with_href_marker(marker)
            finally:
                anon_ctx.close()
    finally:
        admin.restore_icon_baseline(baseline)
        admin.open_entry_by_code(entry_code)
        assert admin.field_value(admin.FIELD_SOCIAL_REDIRECT_URL_EN) == baseline["redirect_url_en"], (
            "Teardown restore did not persist: X/Twitter Social Redirect URL (EN)"
        )


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that toggling an icon's Active Status to False removes it from the live Home page after publishing (ADO-131161)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131161")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129373
@pytest.mark.tc_131161
@pytest.mark.traceability("GLOBAL-FOOTER-TC-037")
@pytest.mark.xdist_group("smi_production_rows")
def test_editor_toggles_existing_icon_inactive_removes_from_live(page, browser):
    admin = _login_as(page, "Site Content Editor")
    entry_code = PRODUCTION_ENTRY_CODES["Snapchat"]
    baseline = admin.capture_icon_baseline(entry_code)
    try:
        with allure.step('Open the existing "Snapchat" entry — Active = True precondition'):
            # Arrange (not itself asserted as the case's outcome): forces
            # the case's own stated precondition regardless of any other
            # test's leftover state, so this test never depends on
            # execution order (standards.md's independent/idempotent rule).
            admin.open_entry_by_code(entry_code)
            if not admin.is_active_status_checked():
                admin.fill_icon_form(active_status=True)
                admin.save()
                admin.open_entry_by_code(entry_code)
            assert admin.is_active_status_checked() is True
        with allure.step("Toggle Active Status to False and click Publish"):
            admin.fill_icon_form(active_status=False)
            admin.save()
        with allure.step("Snapchat icon no longer appears in the Home page section; other active icons remain"):
            anon_ctx = new_context(browser, use_auth_state=False)
            anon_page = anon_ctx.new_page()
            try:
                home_widget = HomeSocialIconsPage(anon_page)
                home_widget.open_home()
                assert home_widget.has_production_icons()
                assert not home_widget.has_icon_with_href_marker("snapchat.com/add/qatarchamber")
            finally:
                anon_ctx.close()
    finally:
        admin.restore_icon_baseline(baseline)
        admin.open_entry_by_code(entry_code)
        assert admin.is_active_status_checked() == baseline["active_status"], (
            "Teardown restore did not persist: Snapchat Active Status"
        )


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that toggling a previously inactive icon's Active Status back to True restores it on the live Home page (ADO-131162)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131162")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129373
@pytest.mark.tc_131162
@pytest.mark.traceability("GLOBAL-FOOTER-TC-038")
@pytest.mark.xdist_group("smi_production_rows")
def test_editor_toggles_existing_inactive_icon_active_restores_on_live(page, browser):
    admin = _login_as(page, "Site Content Editor")
    entry_code = PRODUCTION_ENTRY_CODES["Snapchat"]
    baseline = admin.capture_icon_baseline(entry_code)
    try:
        with allure.step('Open the existing "Snapchat" entry (Active = False) — precondition'):
            # Same self-contained-precondition rationale as tc_131161 above
            # — never depends on that (or any other) test's own side effect.
            admin.open_entry_by_code(entry_code)
            if admin.is_active_status_checked():
                admin.fill_icon_form(active_status=False)
                admin.save()
                admin.open_entry_by_code(entry_code)
            assert admin.is_active_status_checked() is False
        with allure.step("Toggle Active Status to True and click Publish"):
            admin.fill_icon_form(active_status=True)
            admin.save()
        with allure.step("Snapchat icon reappears in the Home page section at its configured Display Order"):
            anon_ctx = new_context(browser, use_auth_state=False)
            anon_page = anon_ctx.new_page()
            try:
                home_widget = HomeSocialIconsPage(anon_page)
                home_widget.open_home()
                assert home_widget.has_production_icons()
                assert home_widget.has_icon_with_href_marker("snapchat.com/add/qatarchamber")
            finally:
                anon_ctx.close()
    finally:
        admin.restore_icon_baseline(baseline)
        admin.open_entry_by_code(entry_code)
        assert admin.is_active_status_checked() == baseline["active_status"], (
            "Teardown restore did not persist: Snapchat Active Status"
        )


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that an Author-drafted icon becomes live only after Editor approval and publish (ADO-131163)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131163")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129373
@pytest.mark.tc_131163
@pytest.mark.traceability("GLOBAL-FOOTER-TC-039")
def test_author_drafted_icon_live_only_after_editor_approval(page):
    # BLOCKED — see module docstring's "NEW BLOCKER" note: Site Content
    # Author's .env credentials do not authenticate live against qcdev.
    # Also independent of that: this project has already twice confirmed
    # live that this state machine has no separate Pending Review/Approve
    # step. Written per the case's own real intent, left to fail honestly.
    with allure.step('Log in as Site Content Author; add a "Flickr" entry and click "Submit for Review"'):
        admin = _login_as(page, "Site Content Author")
    alt_en = _unique_alt_text_en("FlickrDraftApproval")
    try:
        admin.open_new_entry_form()
        # BLOCKED by ADO Bug #142266 (see module docstring).
        admin.fill_icon_form(
            platform="Flickr",
            alt_text_en=alt_en, alt_text_ar="فليكر بانتظار المراجعة",
            redirect_url_en=_unique_redirect_url("flickrapproval"),
            redirect_url_ar=_unique_redirect_url("flickrapproval-ar"),
            display_order="9000", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        with allure.step("Entry saves with status Pending Review; no toast implying publish"):
            code = admin.find_entry_code_by_alt_text_en(alt_en)
            assert code
            assert admin.row_status_text_by_code(code) == "Pending review"
        with allure.step("Log out; log in as Site Content Editor"):
            admin.logout_and_return()
            admin.login_as(*cms_role_credentials("Site Content Editor"))
        with allure.step("Locate the Pending Review entry and click Approve, then Publish"):
            admin.open_entry_by_code(code)
            admin.save()
        with allure.step("Flickr icon now appears on the live Home page"):
            assert admin.row_status_text_by_code(code) == "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that an Editor can unpublish an icon and it is removed from the live page while retained in the CMS (ADO-131164)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131164")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129373
@pytest.mark.tc_131164
@pytest.mark.traceability("GLOBAL-FOOTER-TC-040")
@pytest.mark.xdist_group("smi_production_rows")
def test_editor_unpublishes_icon_removed_live_retained_in_cms(page, browser):
    admin = _login_as(page, "Site Content Editor")
    entry_code = PRODUCTION_ENTRY_CODES["LinkedIn"]
    baseline = admin.capture_icon_baseline(entry_code)
    try:
        with allure.step('Open the existing "LinkedIn" entry — status Published'):
            admin.open_entry_by_code(entry_code)
            assert admin.current_status() == "Approved"
        with allure.step("Click Unpublish"):
            admin.unpublish_to_edit_as_draft()
        with allure.step("LinkedIn icon no longer appears live"):
            anon_ctx = new_context(browser, use_auth_state=False)
            anon_page = anon_ctx.new_page()
            try:
                home_widget = HomeSocialIconsPage(anon_page)
                home_widget.open_home()
                assert home_widget.has_production_icons()
                assert not home_widget.has_icon_with_href_marker("linkedin.com/company/qatarchamber")
            finally:
                anon_ctx.close()
        with allure.step("Return to CMS: entry still exists, status Unpublished, record retained (not deleted)"):
            admin.open_entry_by_code(entry_code)
            assert admin.current_status() == "Draft"
            assert admin.row_visible_by_code(entry_code)
    finally:
        with allure.step("Teardown: republish LinkedIn back to Approved"):
            admin.restore_icon_baseline(baseline)  # fills baseline values + submit_for_publishing()
            admin.open_entry_by_code(entry_code)
            assert admin.current_status() == "Approved", "Teardown restore did not republish LinkedIn"


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a CMS user without permission cannot persist changes to a social icon entry even via a direct action (ADO-131167)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131167")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129373
@pytest.mark.tc_131167
@pytest.mark.traceability("GLOBAL-FOOTER-TC-041")
def test_role_without_permission_cannot_persist_change_via_direct_action(page):
    # BLOCKED — see module docstring's "NEW BLOCKER" note: Content
    # Contributor's .env credentials do not authenticate live. Written per
    # the case's own intent regardless: this surface has no separate
    # "hidden UI" bypass — the direct form action IS this same Save button
    # — so the "direct action" the case names is this same click.
    with allure.step("Log in to CMS with a role lacking Social Media Icons permissions"):
        admin = _login_as(page, "Content Contributor")
    entry_code = PRODUCTION_ENTRY_CODES["Facebook"]
    baseline = admin.capture_icon_baseline(entry_code)
    attempted_url = _unique_redirect_url("contributor-bypass-attempt")
    try:
        with allure.step("Attempt to trigger a save/publish action on an icon entry"):
            admin.open_entry_by_code(entry_code)
            admin.fill_icon_form(redirect_url_en=attempted_url)
            admin.save()
        with allure.step("The action is rejected with Access Denied"):
            body_text = page.locator("body").inner_text()
            assert (_ACCESS_DENIED_EN in body_text) or (_ACCESS_DENIED_AR in body_text)
        with allure.step("The entry's stored data is unchanged from before the attempt"):
            reread = admin.capture_icon_baseline(entry_code)
            assert reread["redirect_url_en"] == baseline["redirect_url_en"]
    finally:
        admin.restore_icon_baseline(baseline)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a Draft-status icon with Active Status = True is not displayed on the frontend (ADO-131197)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131197")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131197
@pytest.mark.traceability("GLOBAL-FOOTER-TC-042")
def test_draft_icon_active_true_not_displayed_on_frontend(page, browser):
    admin = _login_as(page, "Site Content Editor")
    alt_en = _unique_alt_text_en("DraftActiveTrue")
    redirect_url_en = _unique_redirect_url("draftactivetrue")
    try:
        with allure.step("Create an icon entry, Active Status = True, Save only (leave in Draft)"):
            admin.open_new_entry_form()
            # BLOCKED by ADO Bug #142266 (see module docstring).
            admin.fill_icon_form(
                platform="Instagram",
                alt_text_en=alt_en, alt_text_ar="مسودة نشطة",
                redirect_url_en=redirect_url_en,
                redirect_url_ar=_unique_redirect_url("draftactivetrue-ar"),
                display_order="9000", active_status=True,
            )
            admin.upload_icon_image(ICON_PNG_VALID)
            admin.save_as_draft()
        with allure.step("Confirm the entry's status in CMS: Draft, Active = True"):
            code = admin.find_entry_code_by_alt_text_en(alt_en)
            assert code
            assert admin.row_status_text_by_code(code) == "Draft"
            admin.open_entry_by_code(code)
            assert admin.is_active_status_checked() is True
        with allure.step("Icon is absent from the live page"):
            marker = redirect_url_en.split("qctest-")[1]
            anon_ctx = new_context(browser, use_auth_state=False)
            anon_page = anon_ctx.new_page()
            try:
                home_widget = HomeSocialIconsPage(anon_page)
                home_widget.open_home()
                assert home_widget.has_production_icons()
                assert not home_widget.has_icon_with_href_marker(marker)
            finally:
                anon_ctx.close()
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that a Rejected icon entry does not appear on the frontend (ADO-131200)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131200")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131200
@pytest.mark.traceability("GLOBAL-FOOTER-TC-043")
def test_rejected_icon_entry_not_on_frontend(page):
    # BLOCKED — see module docstring's "NEW BLOCKER" note: Site Content
    # Author's .env credentials do not authenticate live. Independently,
    # this surface has never been confirmed to have a "Reject" action at
    # all (see SocialMediaIconAdminPage.REJECT_BUTTON/reject() — an
    # explicit unresolved placeholder, not a guessed selector) — a second,
    # separate reason this would fail even past the credential blocker.
    with allure.step('As Author, submit a new "Telegram" entry for review'):
        admin = _login_as(page, "Site Content Author")
    alt_en = _unique_alt_text_en("TelegramRejected")
    try:
        admin.open_new_entry_form()
        # BLOCKED by ADO Bug #142266 (see module docstring).
        admin.fill_icon_form(
            platform="Telegram",
            alt_text_en=alt_en, alt_text_ar="تيليجرام مرفوض",
            redirect_url_en=_unique_redirect_url("telegramrejected"),
            redirect_url_ar=_unique_redirect_url("telegramrejected-ar"),
            display_order="9000", active_status=False,
        )
        admin.upload_icon_image(ICON_PNG_VALID)
        admin.save()
        code = admin.find_entry_code_by_alt_text_en(alt_en)
        assert code
        assert admin.row_status_text_by_code(code) == "Pending review"

        with allure.step("As Editor, open the Pending Review entry and click Reject"):
            admin.logout_and_return()
            admin.login_as(*cms_role_credentials("Site Content Editor"))
            admin.open_entry_by_code(code)
            admin.reject()  # raises: REJECT_BUTTON is an unresolved placeholder (see docstring)
        with allure.step("Telegram icon does not appear anywhere on the live Home page"):
            assert admin.row_status_text_by_code(code) != "Approved"
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that an interrupted publish action does not leave a corrupted or partially-saved icon entry (ADO-131202)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131202")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131202
@pytest.mark.traceability("GLOBAL-FOOTER-TC-044")
def test_interrupted_publish_does_not_leave_corrupted_entry(page):
    # Deterministic proxy for "interrupt the network connection" (module
    # docstring) — `page.context.set_offline(True)` right before the
    # Publish click, rather than an unscriptable real network flake.
    admin = _login_as(page, "Site Content Editor")
    alt_en = _unique_alt_text_en("InterruptedPublish")
    try:
        with allure.step("Open Add Icon form and complete all mandatory fields"):
            admin.open_new_entry_form()
            # BLOCKED by ADO Bug #142266 (see module docstring) before the
            # interrupted-publish mechanism under test is even reached.
            admin.fill_icon_form(
                platform="Snapchat",
                alt_text_en=alt_en, alt_text_ar="نشر منقطع",
                redirect_url_en=_unique_redirect_url("interruptedpublish"),
                redirect_url_ar=_unique_redirect_url("interruptedpublish-ar"),
                display_order="9000", active_status=False,
            )
            admin.upload_icon_image(ICON_PNG_VALID)
        with allure.step("Click Publish and immediately interrupt the network connection"):
            page.context.set_offline(True)
            try:
                page.locator(admin.SUBMIT_FOR_PUBLISHING_BUTTON).click(timeout=5000)
            except Exception:  # noqa: BLE001 — the interruption itself is expected to abort this click
                pass
            page.wait_for_timeout(1000)
        with allure.step("Restore connectivity and check the entry's state in the CMS list"):
            page.context.set_offline(False)
            code = admin.find_entry_code_by_alt_text_en(alt_en)
        with allure.step("Entry either does not exist, or exists in a consistent pre-publish (Draft) state"):
            assert code == "" or admin.row_status_text_by_code(code) in ("Draft", "")
    finally:
        _teardown(admin, alt_en)


@allure.epic("Global Components")
@allure.feature("Site Footer & Social Media Icons")
@allure.title("Verify that deleting the last active icon entry hides the section gracefully with no layout break (ADO-131203)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131203")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131203
@pytest.mark.traceability("GLOBAL-FOOTER-TC-045")
@pytest.mark.skip(reason=_LAST_ICON_DELETE_BLOCKED)
def test_deleting_last_active_icon_hides_section_gracefully(page):
    pass

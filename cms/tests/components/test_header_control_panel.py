"""
cms/tests/components/test_header_control_panel.py

Control_Panel cases for PBI 129363 (QC-GBL-001 — Site Header): the 25 Azure
cases in `.claude/qa-runs/phase3_129363_cp_batch.json`, each carried into its
`tc_<id>` marker. Case titles/steps are verbatim from Azure. No QA traceability
IDs were supplied with the batch, so none is applied (none invented).

Objects (cms/Content-Admin-Guide.docx §3), both via Object Authoring:
  - HeaderConfiguration — ONE entry, `QCDEMO-129363-HEADER-CONFIG-DEFAULT`, the
    real live header. Written ONLY under the user's ID-named approval of
    2026-10-01 (engineer brief v2: logo, alt text EN/AR, logo redirect URL,
    save as draft, submit for review, update, unpublish) and ONLY by tests
    holding `header_config_guard`: snapshot before the first write, restore as
    Site Content Editor in the finalizer (also on failure), re-read and verify,
    `pytest.exit("RESTORE FAILED …")` when verification fails. All of them share
    `xdist_group("header_config_singleton")`. Delete / archive stay refused by
    the Page Object. Uploaded logo files (QCTEST-134270-logo.png and, if the
    picker wrongly accepts it, QCTEST-134272-logo.jpg) remain in Documents &
    Media — deletion is not approved.
  - NavItem — every automated case works on disposable `QCTEST-<tc_id>-*`
    items only (displayOrder 9900 unless the case dictates a value, relative
    URL `/web/qatar-chamber/qctest-<tc_id>-*`). The `qctest_nav_items` fixture
    pre-cleans and tears them down by EXACT label + entry id every run, and
    errors the test in teardown if any survive (a published+active survivor
    sits in the real public menu).

Accounts: lifecycle cases run as **QC Site Content Editor** (the workflow's
privileged submitter: Submit -> Published directly), via
`cms_role_credentials("Site Content Editor")`. The denial case runs as the
**site member** (no role). TEST_USER is never used.

Public visibility is read in a fresh `new_context(browser, use_auth_state=False)`
and only after both gates are asserted: row status Published AND Active Status
ticked on a fresh reopen. Absence cases first prove presence (positive
propagation control) in the same run.

All NavItem-creating tests share `xdist_group("header_navitem_qctest")`: they
all write into the one real menu.

See `cms/pages/components/header_admin_component.py` for the live-confirmed
locator trail (unmeasured public-render latency: 60s bound).

v2 (2026-10-01): no test is skipped. HEALED 134303/134308: on `?editEntry=`
the form writes with a fetch `PUT /o/c/navitems/<id>` (no edit_info_item
POST), and a Published + inactive record's banner reads "(Inactive)" — both
now handled (`_is_form_write`, `_assert_both_gates`). Header-config restore
mechanics (approve / publish row actions, re-pointing the logo at its D&M
file) were NOT exercised live before scripting.

Case-vs-live notes (reported to the QA Manager; assertions still follow the
case):
  - 134290 expects "Arabic label is required before publishing."; the live form
    blocks with the browser's native "Please fill out this field.".
  - 134294 expects "Please enter a valid URL."; the live field error reads
    "Nav Item URL is not a valid URL — start it with https:// …".
  - 134300 dictates Display Order = 5 and expects the 5th slot; under the
    guide's model (multiples of 100, lowest first, real top-level items at
    100…) 5 sorts FIRST. Mirrored literally; expected to fail on a correct build.
  - 134301: Display Order's native min is -2147483648, so -1/0 are not refused
    client-side; server behaviour unobserved.
  - 134289 "Text entered RTL": the AR box computed `direction: ltr` live.
  - 134297/134299 are built on the live form's `Nav Item Level` (1/2/3) and
    free-text `Parent Menu`, fields the guide does not list.
  - 134266/134267: the case's "nav item edit" has no counterpart on
    HeaderConfiguration; the edit made is Logo Alt Text (EN).
  - 134254/134304: the case's nav-item change is made on disposable QCTEST
    NavItems; the live HeaderConfiguration is only opened.
"""

import json
import os
import re
import time
from contextlib import contextmanager

import allure
import pytest

from cms.pages.components.header_admin_component import (
    HeaderConfigurationAdminPage,
    NavItemAdminPage,
    PublicHeaderNavProbe,
)
from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED, ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials
from core.utils.waits import wait_until
from core.web.browser import new_context
from cms.tests.live_write_guard import LiveRecord, deletes_suppressed, keep_instead_of_delete, log_live_write

PBI = "129363"
NAV_GROUP = "header_navitem_qctest"
SAFE_ORDER = "9900"

HC_GROUP = "header_config_singleton"
HC_CODE = HeaderConfigurationAdminPage.LIVE_ENTRY_CODE
NAV_RECORD = LiveRecord("nav-item", "QCTEST-*", "QCTEST nav items")
HC_RECORD = LiveRecord("header-configuration", HeaderConfigurationAdminPage.LIVE_ENTRY_CODE, "Header Configuration")
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
# Generated by tools/fixture_factory.py (never hand-added).
LOGO_PNG_500KB = os.path.join(FIXTURES, "QCTEST-134270-logo.png")
LOGO_JPG_3MB = os.path.join(FIXTURES, "QCTEST-134272-logo.jpg")


# ───────────────────────────── helpers / fixtures ─────────────────────────────

# PBI running rules, rule 10 (2026-10-14): under QC_ALLOW_LIVE_SINGLETON_WRITES=1
# nothing is deleted, so a QCTEST item from an earlier run may still be in the
# list. Labels then carry a per-run suffix so "exactly one row with this label"
# stays true.
_RUN_SUFFIX = time.strftime("%m%d%H%M") if deletes_suppressed() else ""


def _label(tc_id: int, short: str) -> str:
    return f"QCTEST-{tc_id}-{short}" + (f"-{_RUN_SUFFIX}" if _RUN_SUFFIX else "")


def _url(tc_id: int, short: str) -> str:
    return f"/web/qatar-chamber/qctest-{tc_id}-{short.lower()}"


def _href_fragment(tc_id: int, short: str) -> str:
    return f"qctest-{tc_id}-{short.lower()}"


def _as_editor(page) -> NavItemAdminPage:
    """Sign the page in as QC Site Content Editor (never TEST_USER)."""
    CmsLoginPage(page).ensure_signed_in_as(*cms_role_credentials("Site Content Editor"))
    return NavItemAdminPage(page)


@contextmanager
def _anonymous_header(browser):
    """Fresh logged-out context for every public read (standards.md ->
    Mandatory Logged-Out Context)."""
    ctx = new_context(browser, use_auth_state=False)
    try:
        yield PublicHeaderNavProbe(ctx.new_page())
    finally:
        ctx.close()


@pytest.fixture
def qctest_nav_items(page):
    """Register disposable nav-item labels; each is pre-cleaned on
    registration and torn down (reverse order: children before parents) after
    the test. Survivors fail the teardown loudly."""
    labels: list[str] = []
    nav = NavItemAdminPage(page)
    keep = deletes_suppressed()

    def register(label: str) -> str:
        if not keep:
            survivors = nav.teardown_label(label)  # crash leftovers from a prior run
            assert not survivors, f"could not pre-clean leftover {label!r}: {survivors}"
        labels.append(label)
        return label

    yield register

    if keep:
        # Rule 10: nothing is deleted. Each QCTEST item is logged as kept, and an
        # ACTIVE one is switched off first so it leaves the real public menu.
        _as_editor(page)
        for label in reversed(labels):
            try:
                for row in nav.entries_with_label(label):
                    nav.open_by_code(row["entry_code"])
                    if nav.active_checked():
                        log_live_write(NAV_RECORD, f"{label}: Active Status", False, None, action="publish",
                                       note="switch the QCTEST nav item off (kept, not deleted)")
                        nav.set_active(False)
                        nav.submit()
                    keep_instead_of_delete(NAV_RECORD, f"{label} ({row['entry_code']})")
            except Exception as exc:  # noqa: BLE001 -- reported
                allure.attach(repr(exc), f"could not switch off / log {label}", allure.attachment_type.TEXT)
        return

    survivors = {}
    for label in reversed(labels):
        left = nav.teardown_label(label)
        if left:
            survivors[label] = left
    if survivors:
        pytest.fail(f"QCTEST nav items survived teardown (still in the menu list): {survivors}")


def _assert_both_gates(nav: NavItemAdminPage, code: str, active: bool) -> None:
    """Gate 1 (workflow) and gate 2 (Active Status), read from the reopened
    record. HEALED 2026-10-01: a Published record with Active Status off shows
    "(Inactive)" in its banner (and "INACTIVE" in the list) on this build, so
    the expected banner state is "Published" when active and "Inactive" when
    not — `current_status()` maps "Inactive" to Unknown and could never match."""
    nav.wait_for_banner_status(code, "Published" if active else "Inactive")
    assert nav.active_checked() is active, f"{code}: Active Status did not persist as {active}"


@pytest.fixture
def header_config_guard(page):
    """Snapshot -> yield -> restore -> verify for the LIVE HeaderConfiguration
    (user's ID-named approval 2026-10-01, engineer brief v2 rules 1-3).

    Snapshot: every restorable field + workflow field + Active Status, read
    from a freshly reopened form, as Site Content Editor. Refuses to start
    unless the entry is Published. Finalizer (runs on failure too): signs back
    in as Editor, restores, re-reads; one retry; an unverified restore stops
    the WHOLE run with pytest.exit."""
    CmsLoginPage(page).ensure_signed_in_as(*cms_role_credentials("Site Content Editor"))
    header_config = HeaderConfigurationAdminPage(page)
    snap = header_config.snapshot()
    allure.attach(json.dumps(snap, ensure_ascii=False, indent=1), "HeaderConfiguration snapshot",
                  allure.attachment_type.JSON)
    if snap["row_status"] != STATUS_PUBLISHED:
        pytest.exit(f"PRECONDITION: {HC_CODE} is {snap['row_status']!r} before this test touched it — "
                    "nothing was written; investigate before running header-config tests", returncode=3)

    yield snap

    try:
        CmsLoginPage(page).ensure_signed_in_as(*cms_role_credentials("Site Content Editor"))
    except Exception as exc:  # noqa: BLE001 — no Editor session means no restore; stop the run
        pytest.exit(f"RESTORE FAILED on {HC_CODE}: cannot sign in as Editor: {exc!r}", returncode=3)
    diff = header_config.restore(snap)
    if diff:
        diff = header_config.restore(snap)
    if diff:
        pytest.exit(f"RESTORE FAILED on {HC_CODE}: {diff}", returncode=3)
    verified = header_config.snapshot()
    allure.attach(json.dumps(verified, ensure_ascii=False, indent=1), "HeaderConfiguration restored + verified",
                  allure.attachment_type.JSON)


# ═════════════════════════════ Auth ═══════════════════════════════════════════

@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a Site Content Editor with header-management permission can access and publish header changes (ADO-134254)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134254")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134254
@pytest.mark.xdist_group(NAV_GROUP)
def test_editor_can_access_and_publish_header_changes(page, qctest_nav_items):
    """Account: QC Site Content Editor. "Header Management" on this build is
    the two header objects; the case's "modify a nav item and click Publish" is
    done on a disposable QCTEST NavItem (inactive, so it never reaches the
    public menu) — no write to the live HeaderConfiguration is needed."""
    nav = _as_editor(page)
    header_config = HeaderConfigurationAdminPage(page)
    label_en = qctest_nav_items(_label(134254, "PUB"))

    with allure.step("Log into Liferay CMS as Site Content Editor — Editor gains access to Header Management"):
        header_config.open_live_entry()
        assert header_config.authoring_control_count() > 0, "no Save/Submit controls on the header configuration"
        nav.open_create_form()
        assert nav.authoring_control_count() > 0, "no Save/Submit controls on the navigation items form"

    with allure.step("Navigate to Header Management -> a nav item"):
        nav.fill_nav_item(label_en, "عنصر للنشر", _url(134254, "pub"), SAFE_ORDER, active=False)
        assert nav.save_draft(), "the form was not sent"
        row = nav.wait_for_single_entry(label_en)

    with allure.step("Modify a nav item and click Publish"):
        nav.open_by_code(row["entry_code"])
        nav.fill_nav_item(label_en, "عنصر معدل للنشر", _url(134254, "pub"), SAFE_ORDER, active=False)
        assert nav.submit(), "the form was not sent"
        notice = nav.success_notice()

    with allure.step("Publish action succeeds; Liferay generic success toast displays"):
        assert notice, "no success notice after Publish"
        _assert_both_gates(nav, row["entry_code"], active=False)


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a CMS user without header-management permission is denied access to publish (ADO-134255)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134255")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134255
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True, ids=["site-member"])
def test_user_without_header_permission_is_denied(page):
    """Account: site member with NO role (`cms_role_credentials("Site Member")`)
    — the standards' negative-case account, so the refusal is proven for a user
    who CAN sign in, not for a broken login. Non-mutating: the live
    HeaderConfiguration is only navigated to."""
    login = CmsLoginPage(page)
    header_config = HeaderConfigurationAdminPage(page)

    with allure.step("Log into Liferay CMS as a user without header-management permission"):
        login.open_login().login(*cms_role_credentials("Site Member"))
        assert login.login_succeeded(), "site-member sign-in did not complete"

    with allure.step("Attempt to navigate to Header Management"):
        header_config.open_manage_page_for_any_role()

    with allure.step("Action is blocked with the Access Denied message"):
        assert login.login_succeeded(), (
            "session is no longer signed in on the denied page — a signed-out "
            "404 would prove nothing about permissions"
        )
        assert header_config.authoring_control_count() == 0, "Save/Submit controls rendered for a no-role user"
        assert not header_config.entries_table_rendered(), "header entries list rendered for a no-role user"
        assert header_config.access_denied_shown(), (
            f"expected {HeaderConfigurationAdminPage.ACCESS_DENIED_TEXT!r} on the denied page"
        )


# ═════════════════════════ Workflow (HeaderConfiguration) ════════════════════

@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that an admin can save a header configuration as Draft (ADO-134266)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134266")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129363
@pytest.mark.tc_134266
@pytest.mark.xdist_group(HC_GROUP)
def test_save_header_configuration_as_draft(page, header_config_guard):
    """Account: QC Site Content Editor. Writes the live entry under the
    2026-10-01 approval; `header_config_guard` restores and verifies it. On a
    Published entry Save as Draft is disabled (live), so the entry is
    unpublished first. The case's "nav item edit" has no counterpart on
    HeaderConfiguration; the edit made is the Logo Alt Text (EN)."""
    header_config = HeaderConfigurationAdminPage(page)
    marker = "QCTEST-134266 Qatar Chamber"

    with allure.step("Log into CMS as Site Content Editor; navigate to Header Management"):
        header_config.open_live_entry()
        assert header_config.banner_status_raw() == "Published"

    with allure.step("Make an edit"):
        header_config.unpublish()
        header_config.wait_for_banner_status(HC_CODE, "Unpublished")
        header_config.set_alt_en(marker)

    with allure.step("Click Save as Draft"):
        assert header_config.save_draft(), "the form was not sent"
        notice = header_config.success_notice()

    with allure.step("Configuration saves with status Draft; Liferay generic success toast displays"):
        assert notice, "no success notice after Save as Draft"
        header_config.wait_for_banner_status(HC_CODE, "Draft")
        assert header_config.alt_en() == marker


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that an admin can preview a header configuration before publishing (ADO-134267)")
@allure.severity(allure.severity_level.MINOR)
@allure.label("pbi", PBI)
@allure.label("testcase", "134267")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129363
@pytest.mark.tc_134267
@pytest.mark.xdist_group(HC_GROUP)
def test_preview_header_configuration_before_publishing(page, browser, header_config_guard):
    """Account: QC Site Content Editor. Precondition built under the approval:
    unpublish -> edit Logo Alt Text (EN) -> Save as Draft. Preview is a staff
    surface, so "without publishing it" is proven separately in a logged-out
    context."""
    header_config = HeaderConfigurationAdminPage(page)
    marker = "QCTEST-134267 Preview Logo"

    with allure.step("Precondition: a Draft header configuration"):
        header_config.unpublish()
        header_config.wait_for_banner_status(HC_CODE, "Unpublished")
        header_config.set_alt_en(marker)
        assert header_config.save_draft(), "the form was not sent"
        header_config.wait_for_banner_status(HC_CODE, "Draft")

    with allure.step("Click Preview"):
        header_config.open(header_config.preview_url())

    with allure.step("Preview renders the configured header as it will appear live, without publishing it"):
        assert "PREVIEW" in header_config.rendered_body_text(), "no preview banner on the preview page"
        assert header_config.preview_shows_logo_alt(marker), "preview header does not render the draft logo alt text"
        with _anonymous_header(browser) as public:
            public.open_home_anonymous()
            assert not public.is_signed_in()
            assert public.logo_alt() != marker, "the draft value is visible to anonymous visitors"


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that an admin can submit a header configuration for review (ADO-134268)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134268")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129363
@pytest.mark.tc_134268
@pytest.mark.xdist_group(HC_GROUP)
def test_submit_header_configuration_for_review(page, header_config_guard):
    """Accounts: QC Site Content Editor builds the Draft (unpublish -> Save as
    Draft); QC Site Content AUTHOR submits — only a non-privileged submitter
    lands on Pending Review (an Editor's submit publishes directly). The
    guard signs back in as Editor and restores (approve -> Published)."""
    header_config = HeaderConfigurationAdminPage(page)

    with allure.step("Precondition: a Draft configuration (as Editor)"):
        header_config.unpublish()
        header_config.wait_for_banner_status(HC_CODE, "Unpublished")
        assert header_config.save_draft(), "the form was not sent"
        header_config.wait_for_banner_status(HC_CODE, "Draft")

    with allure.step("From a Draft configuration, click Submit for Review (as Author)"):
        CmsLoginPage(page).ensure_signed_in_as(*cms_role_credentials("Site Content Author"))
        header_config.open_live_entry()
        assert header_config.submit(), "the form was not sent"
        notice = header_config.success_notice()

    with allure.step("Configuration status changes to Submitted/Pending Review; success toast displays"):
        assert notice, "no success notice after Submit for Review"
        header_config.wait_for_banner_status(HC_CODE, "Pending Review", "Submitted for Review")


# ═════════════════════════ Logo fields (HeaderConfiguration) ═════════════════

@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a valid Logo Image (PNG, 500KB) uploads successfully (ADO-134270)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134270")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134270
@pytest.mark.skip(reason="ON HOLD 2026-10-03 (QA Manager): the live logo qc-logo (2) (9).png is not in the Documents & Media library the picker searches, so the original cannot be restored after the upload; the user is verifying this manually.")
@pytest.mark.xdist_group(HC_GROUP)
def test_valid_logo_image_png_uploads(page, header_config_guard):
    """Account: QC Site Content Editor. Uploads the 512000-byte fixture
    `QCTEST-134270-logo.png` under a UNIQUE name per run
    (`QCTEST-134270-logo-<timestamp>.png`, see unique_upload_name) — the file
    stays in Documents & Media (deletion not approved). Before any write the
    test proves, read-only, that the ORIGINAL logo is findable by name in the
    picker, because the guard's restore re-points the logo at it."""
    header_config = HeaderConfigurationAdminPage(page)
    original_logo = header_config_guard["logo"]
    upload_name = HeaderConfigurationAdminPage.unique_upload_name("QCTEST-134270-logo", ".png")
    allure.attach(upload_name, "Uploaded file name", allure.attachment_type.TEXT)

    with allure.step("Open Header Management; prove the original logo can be re-selected (restore path)"):
        header_config.open_live_entry()
        assert original_logo and header_config.library_has_logo(original_logo), (
            f"original logo {original_logo!r} not selectable in the picker — not writing"
        )

    with allure.step("Click Logo Image upload; select a valid 500KB PNG file — file selected shows preview"):
        header_config.open_live_entry()
        header_config.upload_logo_named(LOGO_PNG_500KB, upload_name, "image/png")
        assert upload_name.rsplit(".", 1)[0] in header_config.selected_logo_name()

    with allure.step("Save"):
        assert header_config.submit(), "the form was not sent"
        notice = header_config.success_notice()
        feedback = header_config.validation_feedback()

    with allure.step("Upload succeeds; no validation error; Liferay success toast displays"):
        assert notice, f"no success notice (form said: {feedback!r})"
        assert not feedback, f"validation error shown: {feedback!r}"
        header_config.open_live_entry()
        assert upload_name.rsplit(".", 1)[0] in header_config.logo_file_name()


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a Logo Image exceeding 2MB or in an unsupported format is rejected (ADO-134272)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134272")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129363
@pytest.mark.tc_134272
@pytest.mark.xdist_group(HC_GROUP)
def test_oversized_or_unsupported_logo_image_rejected(page, header_config_guard):
    """Account: QC Site Content Editor. A 3 MB .jpg (fixture
    `QCTEST-134272-logo.jpg`, offered under a unique name per run) is both over
    the field's 2 MB limit and outside its ".png,.svg" types. The picker's Add
    is NEVER clicked and the record is never saved; the guard verifies the
    entry is untouched."""
    header_config = HeaderConfigurationAdminPage(page)
    upload_name = HeaderConfigurationAdminPage.unique_upload_name("QCTEST-134272-logo", ".jpg")
    allure.attach(upload_name, "Offered file name", allure.attachment_type.TEXT)

    with allure.step("Open Header Management"):
        header_config.open_live_entry()

    with allure.step("Attempt to upload a 3MB .jpg file"):
        verdict = header_config.upload_logo_expect_rejected(LOGO_JPG_3MB, upload_name, "image/jpeg")
        allure.attach(json.dumps(verdict, ensure_ascii=False), "Picker verdict", allure.attachment_type.JSON)

    with allure.step("Upload rejected; validation error for unsupported format or > 2MB displays"):
        assert verdict["rejected"], f"the 3MB .jpg was accepted by the Logo Image picker: {verdict}"
        assert verdict["message"], "rejected without any error message"


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a valid Logo Alt Text (EN) of 50 characters saves correctly (ADO-134273)")
@allure.severity(allure.severity_level.MINOR)
@allure.label("pbi", PBI)
@allure.label("testcase", "134273")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134273
@pytest.mark.xdist_group(HC_GROUP)
def test_valid_logo_alt_text_en_50_chars_saves(page, header_config_guard):
    """Account: QC Site Content Editor. Update of the Published entry; the
    guard restores the original alt text."""
    header_config = HeaderConfigurationAdminPage(page)
    value = ("QCTEST-134273-" + "A" * 50)[:50]
    assert len(value) == 50

    with allure.step("Open Header Management; enter a 50-char string in Logo Alt Text EN"):
        header_config.open_live_entry()
        header_config.set_alt_en(value)
        assert header_config.alt_en() == value

    with allure.step("Save"):
        assert header_config.submit(), "the form was not sent"

    with allure.step("Save succeeds; value persisted"):
        assert header_config.success_notice(), "no success notice"
        header_config.open_live_entry()
        assert header_config.alt_en() == value


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a valid Logo Alt Text (AR) saves correctly and renders RTL in the CMS field (ADO-134277)")
@allure.severity(allure.severity_level.MINOR)
@allure.label("pbi", PBI)
@allure.label("testcase", "134277")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134277
@pytest.mark.xdist_group(HC_GROUP)
def test_valid_logo_alt_text_ar_saves_rtl(page, header_config_guard):
    """Account: QC Site Content Editor. The RTL check runs BEFORE the save, so
    a non-RTL field fails the test without writing. Arabic asserted as data."""
    header_config = HeaderConfigurationAdminPage(page)
    value = "شعار غرفة قطر اختبار"

    with allure.step("Open Header Management; enter Arabic text in Logo Alt Text AR — rendered RTL"):
        header_config.open_live_entry()
        header_config.set_alt_ar(value)
        assert header_config.alt_ar_direction() == "rtl", "Logo Alt Text (AR) does not render right-to-left"

    with allure.step("Save"):
        assert header_config.submit(), "the form was not sent"

    with allure.step("Save succeeds; value persisted"):
        assert header_config.success_notice(), "no success notice"
        header_config.open_live_entry()
        assert header_config.alt_ar() == value


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a valid Logo Redirect URL saves correctly (ADO-134281)")
@allure.severity(allure.severity_level.MINOR)
@allure.label("pbi", PBI)
@allure.label("testcase", "134281")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134281
@pytest.mark.xdist_group(HC_GROUP)
def test_valid_logo_redirect_url_saves(page, header_config_guard):
    """Account: QC Site Content Editor. A real, working relative page is used so
    the live logo link never points anywhere broken during the window."""
    header_config = HeaderConfigurationAdminPage(page)
    value = "/web/qatar-chamber/about-us"

    with allure.step("Open Header Management; enter a valid URL in Logo Redirect URL"):
        header_config.open_live_entry()
        header_config.set_redirect_url(value)

    with allure.step("Save"):
        assert header_config.submit(), "the form was not sent"

    with allure.step("Save succeeds; value persisted"):
        assert header_config.success_notice(), "no success notice"
        header_config.open_live_entry()
        assert header_config.redirect_url() == value


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that an invalid Logo Redirect URL is rejected (ADO-134282)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134282")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129363
@pytest.mark.tc_134282
@pytest.mark.xdist_group(HC_GROUP)
def test_invalid_logo_redirect_url_rejected(page, header_config_guard):
    """Account: QC Site Content Editor. If the invalid value is (wrongly)
    accepted, the guard restores the original."""
    header_config = HeaderConfigurationAdminPage(page)

    with allure.step("Enter 'not a url' in Logo Redirect URL"):
        header_config.open_live_entry()
        header_config.set_redirect_url("not a url")

    with allure.step("Click Save"):
        header_config.submit()
        feedback = header_config.validation_feedback()

    with allure.step("Save blocked; message: 'Please enter a valid URL.' displays"):
        header_config.open_live_entry()
        assert header_config.redirect_url() == header_config_guard["redirect_url"], "the invalid URL was saved"
        assert "Please enter a valid URL." in feedback, f"form said: {feedback!r}"


# ═════════════════════════ NavItem — field validation ════════════════════════

@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a valid Nav Item Label (EN) of 20 characters saves correctly (ADO-134285)")
@allure.severity(allure.severity_level.MINOR)
@allure.label("pbi", PBI)
@allure.label("testcase", "134285")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134285
@pytest.mark.xdist_group(NAV_GROUP)
def test_valid_nav_item_label_en_20_chars_saves(page, qctest_nav_items):
    """Account: QC Site Content Editor. Saved as Draft + inactive, so the item
    never reaches the public menu."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134285, "LBL-20"))
    assert len(label_en) == 20, "test data must be exactly 20 characters"

    with allure.step("Open Header Management -> Add Nav Item; enter a 20-char label in Nav Item Label EN"):
        nav.open_create_form()
        nav.fill_nav_item(label_en, "عنصر اختبار", _url(134285, "lbl"), SAFE_ORDER, active=False)

    with allure.step("Save"):
        assert nav.save_draft(), "the form was not sent"

    with allure.step("Save succeeds; label persisted"):
        row = nav.wait_for_single_entry(label_en)
        assert row["status"] == STATUS_DRAFT
        nav.open_by_code(row["entry_code"])
        assert nav.label_en_value() == label_en


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a valid Nav Item Label (AR) saves correctly (ADO-134289)")
@allure.severity(allure.severity_level.MINOR)
@allure.label("pbi", PBI)
@allure.label("testcase", "134289")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134289
@pytest.mark.xdist_group(NAV_GROUP)
def test_valid_nav_item_label_ar_saves(page, qctest_nav_items):
    """Account: QC Site Content Editor. Draft + inactive. The Arabic value is
    asserted as data (English-only locator rule)."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134289, "AR"))
    label_ar = "قائمة اختبار عربية"

    with allure.step("Enter Arabic text in Nav Item Label AR — text entered RTL"):
        nav.open_create_form()
        nav.fill_nav_item(label_en, label_ar, _url(134289, "ar"), SAFE_ORDER, active=False)
        assert nav.label_ar_direction() == "rtl", "Nav Item Label AR does not render right-to-left"

    with allure.step("Save"):
        assert nav.save_draft(), "the form was not sent"

    with allure.step("Save succeeds; label persisted"):
        row = nav.wait_for_single_entry(label_en)
        nav.open_by_code(row["entry_code"])
        assert nav.label_ar_value() == label_ar


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a nav item with a missing Arabic label is blocked before publish (ADO-134290)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134290")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134290
@pytest.mark.xdist_group(NAV_GROUP)
def test_missing_arabic_label_blocks_publish(page, qctest_nav_items):
    """Account: QC Site Content Editor. Every other field is valid, so a block
    can only come from the empty AR label. Active is unticked so an
    unexpected acceptance never reaches the public menu."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134290, "NOAR"))

    with allure.step("Add a nav item with a valid EN label but empty AR label"):
        nav.open_create_form()
        nav.fill_nav_item(label_en, "", _url(134290, "noar"), SAFE_ORDER, active=False)

    with allure.step("Click Publish"):
        nav.submit()
        feedback = nav.validation_feedback()

    with allure.step("Publish blocked; 'Arabic label is required before publishing.' displays"):
        assert nav.entries_with_label(label_en) == [], "the item was saved despite the empty Arabic label"
        assert "Arabic label is required before publishing." in feedback, f"form said: {feedback!r}"


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a valid Nav Item URL saves correctly (ADO-134293)")
@allure.severity(allure.severity_level.MINOR)
@allure.label("pbi", PBI)
@allure.label("testcase", "134293")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134293
@pytest.mark.xdist_group(NAV_GROUP)
def test_valid_nav_item_url_saves(page, qctest_nav_items):
    """Account: QC Site Content Editor. Draft + inactive. URL is a relative
    path, as guide §3 requires."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134293, "URL"))
    url = _url(134293, "url")

    with allure.step("Enter a valid URL in Nav Item URL"):
        nav.open_create_form()
        nav.fill_nav_item(label_en, "رابط اختبار", url, SAFE_ORDER, active=False)

    with allure.step("Save"):
        assert nav.save_draft(), "the form was not sent"

    with allure.step("Save succeeds; URL persisted"):
        row = nav.wait_for_single_entry(label_en)
        nav.open_by_code(row["entry_code"])
        assert nav.url_value() == url


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that an invalid Nav Item URL is rejected (ADO-134294)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134294")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129363
@pytest.mark.tc_134294
@pytest.mark.xdist_group(NAV_GROUP)
def test_invalid_nav_item_url_rejected(page, qctest_nav_items):
    """Account: QC Site Content Editor. Save path = the submit button (Save as
    Draft skips required-field validation). Active unticked."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134294, "BADURL"))

    with allure.step("Enter an invalid URL string in Nav Item URL"):
        nav.open_create_form()
        nav.fill_nav_item(label_en, "رابط غير صالح", "not a valid url", SAFE_ORDER, active=False)

    with allure.step("Click Save"):
        nav.submit()
        feedback = nav.validation_feedback()

    with allure.step("Save blocked; 'Please enter a valid URL.' displays"):
        assert nav.entries_with_label(label_en) == [], "the item was saved with an invalid URL"
        assert "Please enter a valid URL." in feedback, f"form said: {feedback!r}"


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that configuring a 4th navigation depth level is blocked (ADO-134297)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134297")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.navigation
@pytest.mark.pbi_129363
@pytest.mark.tc_134297
@pytest.mark.xdist_group(NAV_GROUP)
def test_fourth_navigation_depth_blocked(page, qctest_nav_items):
    """Account: QC Site Content Editor. Built against the live form's own
    `Nav Item Level` (1/2/3) and `Parent Item` fields on a disposable QCTEST
    chain L1 -> L2 -> L3, all Published but INACTIVE (never in the public
    menu). The 4th-level attempt picks L3 as parent; the Level options stop at
    3, so Level is left unset."""
    nav = _as_editor(page)
    l1 = qctest_nav_items(_label(134297, "L1"))
    l2 = qctest_nav_items(_label(134297, "L2"))
    l3 = qctest_nav_items(_label(134297, "L3"))
    l4 = qctest_nav_items(_label(134297, "L4"))

    with allure.step("Precondition: an existing Level 3 item (L1 -> L2 -> L3)"):
        parent = None
        for label, level in ((l1, "1"), (l2, "2"), (l3, "3")):
            nav.open_create_form()
            nav.fill_nav_item(label, "مستوى اختبار", _url(134297, label[-2:]), SAFE_ORDER, active=False)
            nav.select_level(level)
            if parent:
                nav.select_parent_item(parent)
            assert nav.submit(), f"{label}: the form was not sent"
            _assert_both_gates(nav, nav.wait_for_single_entry(label)["entry_code"], active=False)
            parent = label

    with allure.step("Attempt to add a child item beneath the Level 3 item"):
        nav.open_create_form()
        nav.fill_nav_item(l4, "مستوى رابع", _url(134297, "l4"), SAFE_ORDER, active=False)
        nav.select_parent_item(l3)
        nav.submit()
        feedback = nav.validation_feedback()

    with allure.step("Action blocked; 'Maximum navigation depth of 3 levels reached.' displays"):
        assert nav.entries_with_label(l4) == [], "a 4th-level item was saved"
        assert "Maximum navigation depth of 3 levels reached." in feedback, f"form said: {feedback!r}"


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a Level 2 item without a Parent Menu is blocked before publish (ADO-134299)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134299")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129363
@pytest.mark.tc_134299
@pytest.mark.xdist_group(NAV_GROUP)
def test_level_2_without_parent_blocked(page, qctest_nav_items):
    """Account: QC Site Content Editor. Live form: `Nav Item Level` = 2, both
    `Parent Menu` (free text) and `Parent Item` (relationship) left empty,
    Active unticked so an unexpected acceptance never reaches the menu."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134299, "L2NOPARENT"))

    with allure.step("Set Nav Item Level = 2, leave Parent Menu empty"):
        nav.open_create_form()
        nav.fill_nav_item(label_en, "مستوى ثاني", _url(134299, "l2"), SAFE_ORDER, active=False)
        nav.select_level("2")
        nav.set_parent_menu("")

    with allure.step("Click Publish"):
        nav.submit()
        feedback = nav.validation_feedback()

    with allure.step("Publish blocked; a Parent Menu message displays (wording recorded, rule 17)"):
        allure.attach(feedback, "form feedback (expected: 'Parent Menu is required for Level 2 and Level 3 items.')",
                      allure.attachment_type.TEXT)
        assert nav.entries_with_label(label_en) == [], "the Level 2 item was saved without a parent"
        assert feedback.strip(), "nothing was saved, but no validation message showed"


# ═════════════════════════ NavItem — order & visibility ══════════════════════

@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a valid positive Display Order value saves and reorders the nav item (ADO-134300)")
@allure.severity(allure.severity_level.MINOR)
@allure.label("pbi", PBI)
@allure.label("testcase", "134300")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134300
@pytest.mark.xdist_group(NAV_GROUP)
def test_positive_display_order_reorders_nav_item(page, browser, qctest_nav_items):
    """Account: QC Site Content Editor (Submit -> Published).

    DATA CHANGE (QA Manager decision, 2026-10-03): the case dictates Display
    Order = 5, but live top-level items are numbered 100, 200, … so 5 sorts
    FIRST. The case's intent — the item lands in the 5th top-level slot — is
    kept: the test reads the live Display Orders of the items now in slots 4
    and 5 (read-only) and uses their midpoint (e.g. 400/500 -> 450).
    Published + active by necessity (the case asserts the public position);
    torn down immediately after the assertion."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134300, "SLOT5"))
    fragment = _href_fragment(134300, "slot5")

    with allure.step("Read the live Display Orders of the 4th and 5th top-level items"):
        with _anonymous_header(browser) as public:
            public.open_home_anonymous()
            top = public.top_level_labels()
        assert len(top) >= 5, f"fewer than 5 top-level items: {top}"
        order_4, order_5 = nav.display_order_of(top[3]), nav.display_order_of(top[4])
        assert order_5 - order_4 >= 2, f"no free value between {top[3]}={order_4} and {top[4]}={order_5}"
        midpoint = str((order_4 + order_5) // 2)
        allure.attach(f"{top[3]}={order_4}, {top[4]}={order_5}, used {midpoint}", "Display Order data",
                      allure.attachment_type.TEXT)

    with allure.step(f"Set Display Order = {midpoint} on a nav item"):
        nav.open_create_form()
        nav.fill_nav_item(label_en, "ترتيب اختبار", _url(134300, "slot5"), midpoint, active=True)

    with allure.step("Save (publish)"):
        assert nav.submit(), "the form was not sent"
        row = nav.wait_for_single_entry(label_en)
        _assert_both_gates(nav, row["entry_code"], active=True)
        assert nav.display_order_value() == midpoint

    with allure.step("Nav item repositions to the 5th display slot on the frontend after publish"):
        with _anonymous_header(browser) as public:
            assert public.wait_for_link(fragment, present=True), "item never appeared in the public header"
            assert not public.is_signed_in()
            assert public.top_level_position_of(fragment) == 5, (
                f"top-level order is {public.top_level_labels()}"
            )


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that Display Order rejects non-numeric, negative, and zero values (ADO-134301)")
@allure.severity(allure.severity_level.MINOR)
@allure.label("pbi", PBI)
@allure.label("testcase", "134301")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_129363
@pytest.mark.tc_134301
@pytest.mark.xdist_group(NAV_GROUP)
def test_display_order_rejects_non_numeric_negative_zero(page, qctest_nav_items):
    """Account: QC Site Content Editor. Three attempts on fresh create forms,
    every other field valid, Active unticked. An attempt that is NOT blocked
    creates a row; it is removed before the next attempt so each check starts
    clean, and every outcome is asserted at the end."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134301, "ORD"))
    outcome: dict[str, dict] = {}

    def attempt(key: str, value: str, by_keys: bool) -> None:
        nav.open_create_form()
        # Letters cannot be fill()ed into a type=number input (confirmed live),
        # so 'abc' is typed key-by-key the way a user would enter it.
        nav.fill_nav_item(label_en, "ترتيب غير صالح", _url(134301, "ord"),
                          None if by_keys else value, active=False)
        if by_keys:
            nav.type_display_order_keys(value)
        nav.submit()
        feedback = nav.validation_feedback()
        saved = nav.entries_with_label(label_en) != []
        if saved:
            nav.teardown_label(label_en)
        outcome[key] = {"saved": saved, "feedback": feedback}

    with allure.step("Enter 'abc' in Display Order, Save"):
        attempt("abc", "abc", by_keys=True)
    with allure.step("Enter -1 in Display Order, Save"):
        attempt("-1", "-1", by_keys=False)
    with allure.step("Enter 0 in Display Order, Save"):
        attempt("0", "0", by_keys=False)

    with allure.step("Save blocked each time; non-numeric error; the same positive-number error for -1 and 0"):
        assert not outcome["abc"]["saved"] and outcome["abc"]["feedback"], f"'abc': {outcome['abc']}"
        assert not outcome["-1"]["saved"] and outcome["-1"]["feedback"], f"-1: {outcome['-1']}"
        assert not outcome["0"]["saved"] and outcome["0"]["feedback"], f"0: {outcome['0']}"
        assert outcome["-1"]["feedback"] == outcome["0"]["feedback"], (
            f"-1 and 0 should show the same positive-number error: {outcome}"
        )


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a nav item with Active Status = True displays on the frontend (ADO-134302)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134302")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134302
@pytest.mark.xdist_group(NAV_GROUP)
def test_active_nav_item_displays_on_frontend(page, browser, qctest_nav_items):
    """Account: QC Site Content Editor (Submit -> Published). Both gates are
    asserted before the anonymous read."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134302, "ON"))
    fragment = _href_fragment(134302, "on")

    with allure.step("Set Active Status = True on a nav item"):
        nav.open_create_form()
        nav.fill_nav_item(label_en, "عنصر نشط", _url(134302, "on"), SAFE_ORDER, active=True)

    with allure.step("Publish — publish succeeds"):
        assert nav.submit(), "the form was not sent"
        row = nav.wait_for_single_entry(label_en)
        _assert_both_gates(nav, row["entry_code"], active=True)

    with allure.step("Open the public site — nav item is visible in the frontend header"):
        with _anonymous_header(browser) as public:
            assert public.wait_for_link(fragment, present=True), "active published item is not in the public header"
            assert not public.is_signed_in()


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a nav item with Active Status = False does not appear on the frontend while other items remain visible (ADO-134303)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134303")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.navigation
@pytest.mark.regression
@pytest.mark.pbi_129363
@pytest.mark.tc_134303
@pytest.mark.xdist_group(NAV_GROUP)
def test_inactive_nav_item_hidden_others_remain(page, browser, qctest_nav_items):
    """Account: QC Site Content Editor. The disposable item is first proven
    visible (positive propagation control), then deactivated; "others remain"
    is checked against the real top-level labels captured before the run."""
    nav = _as_editor(page)
    label_en = qctest_nav_items(_label(134303, "OFF"))
    fragment = _href_fragment(134303, "off")

    with _anonymous_header(browser) as public:
        public.open_home_anonymous()
        baseline = public.top_level_labels()
    assert baseline, "could not read the public header's real top-level items"

    with allure.step("Precondition: the item is Published + Active and visible"):
        nav.open_create_form()
        nav.fill_nav_item(label_en, "عنصر غير نشط", _url(134303, "off"), SAFE_ORDER, active=True)
        assert nav.submit(), "the form was not sent"
        row = nav.wait_for_single_entry(label_en)
        code = row["entry_code"]
        _assert_both_gates(nav, code, active=True)
        with _anonymous_header(browser) as public:
            assert public.wait_for_link(fragment, present=True), "positive control: item never appeared"

    with allure.step("Set Active Status = False on the nav item, leaving all others Active = True"):
        nav.open_by_code(code)
        nav.set_active(False)

    with allure.step("Publish — publish succeeds"):
        assert nav.submit(), "the form was not sent"
        _assert_both_gates(nav, code, active=False)

    with allure.step("Open the public site header — the disabled item is absent; all other items remain"):
        with _anonymous_header(browser) as public:
            assert public.wait_for_link(fragment, present=False), "inactive item is still in the public header"
            assert not public.is_signed_in()
            now = public.top_level_labels()
            missing = [label for label in baseline if label not in now]
            assert not missing, f"real nav items disappeared: {missing}"


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that an admin can update a previously published header configuration (ADO-134304)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134304")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.workflow
@pytest.mark.pbi_129363
@pytest.mark.tc_134304
@pytest.mark.xdist_group(NAV_GROUP)
def test_update_published_header_configuration(page, browser, qctest_nav_items):
    """Account: QC Site Content Editor. The case's change is a NAV ITEM's
    Display Order, so it is made on two disposable QCTEST items (A 9800, B 9900,
    Published + Active — briefly in the real menu, after every real item); the
    live HeaderConfiguration is only opened to confirm it is Published."""
    nav = _as_editor(page)
    header_config = HeaderConfigurationAdminPage(page)
    item_a = qctest_nav_items(_label(134304, "A"))
    item_b = qctest_nav_items(_label(134304, "B"))
    frag_a, frag_b = _href_fragment(134304, "a"), _href_fragment(134304, "b")

    with allure.step("Open an already-Published header configuration"):
        header_config.open_live_entry()
        assert header_config.banner_status_raw() == "Published"

    with allure.step("Precondition: two published, active nav items, A before B"):
        codes = {}
        for label, order, short in ((item_a, "9800", "a"), (item_b, "9900", "b")):
            nav.open_create_form()
            nav.fill_nav_item(label, "ترتيب " + short, _url(134304, short), order, active=True)
            assert nav.submit(), f"{label}: the form was not sent"
            codes[label] = nav.wait_for_single_entry(label)["entry_code"]
            _assert_both_gates(nav, codes[label], active=True)
        with _anonymous_header(browser) as public:
            assert public.wait_until_ordered(frag_a, frag_b), "positive control: A is not before B publicly"

    with allure.step("Edit a nav item's Display Order"):
        nav.open_by_code(codes[item_a])
        nav.fill_nav_item(item_a, "ترتيب a", _url(134304, "a"), "9950", active=True)

    with allure.step("Click Update"):
        assert nav.submit(), "the form was not sent"
        notice = nav.success_notice()

    with allure.step("Update succeeds; success toast displays; new order reflected after cache refresh"):
        assert notice, "no success notice after Update"
        _assert_both_gates(nav, codes[item_a], active=True)
        with _anonymous_header(browser) as public:
            assert public.wait_until_ordered(frag_b, frag_a), "A did not move after B in the public header"


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that an admin can unpublish a header configuration (ADO-134305)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134305")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.workflow
@pytest.mark.pbi_129363
@pytest.mark.tc_134305
@pytest.mark.xdist_group(HC_GROUP)
def test_unpublish_header_configuration(page, browser, header_config_guard):
    """Account: QC Site Content Editor. Unpublishes the LIVE header (approved
    2026-10-01), asserts the public header changed in a logged-out context,
    then re-publishes IMMEDIATELY (brief v2 rule 4); the guard verifies."""
    header_config = HeaderConfigurationAdminPage(page)
    with _anonymous_header(browser) as public:
        public.open_home_anonymous()
        baseline_src = public.logo_src()
    assert baseline_src, "could not read the public logo before unpublishing"

    try:
        with allure.step("Open a Published header configuration; click Unpublish"):
            header_config.open_live_entry()
            assert header_config.banner_status_raw() == "Published"
            header_config.unpublish()

        with allure.step("Status changes to Unpublished; header reverts on the frontend"):
            header_config.wait_for_banner_status(HC_CODE, "Unpublished")
            with _anonymous_header(browser) as public:
                reverted = public.wait_for_logo(lambda p: p.logo_src() != baseline_src)
            assert reverted, "public header still shows the configured logo after Unpublish"
    finally:
        with allure.step("Re-publish immediately"):
            if header_config.offers_row_action("publish"):
                header_config.publish()


@allure.epic("Global Components")
@allure.feature("Site Header")
@allure.title("Verify that a nav item whose parent is disabled does not render an orphaned child on the frontend (ADO-134308)")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", PBI)
@allure.label("testcase", "134308")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.navigation
@pytest.mark.pbi_129363
@pytest.mark.tc_134308
@pytest.mark.xdist_group(NAV_GROUP)
def test_disabled_parent_hides_orphaned_child(page, browser, qctest_nav_items):
    """Account: QC Site Content Editor. A disposable QCTEST parent (level 1)
    and child (level 2, Parent Item = that parent) — never a real item. Both are
    first proven visible; then the parent is deactivated. Teardown removes the
    child before the parent. Parent-Item picker mechanics are unverified by a
    click-through (see the Page Object)."""
    nav = _as_editor(page)
    parent = qctest_nav_items(_label(134308, "PARENT"))
    child = qctest_nav_items(_label(134308, "CHILD"))
    parent_frag = _href_fragment(134308, "parent")
    child_frag = _href_fragment(134308, "child")

    with allure.step("Precondition: Level 1 parent and its Level 2 child, both Published + Active"):
        nav.open_create_form()
        nav.fill_nav_item(parent, "أب اختبار", _url(134308, "parent"), SAFE_ORDER, active=True)
        nav.select_level("1")
        assert nav.submit(), "the form was not sent"
        parent_row = nav.wait_for_single_entry(parent)
        _assert_both_gates(nav, parent_row["entry_code"], active=True)

        nav.open_create_form()
        nav.fill_nav_item(child, "ابن اختبار", _url(134308, "child"), "100", active=True)
        nav.select_level("2")
        nav.select_parent_item(parent)
        assert nav.submit(), "the form was not sent"
        child_row = nav.wait_for_single_entry(child)
        _assert_both_gates(nav, child_row["entry_code"], active=True)

        with _anonymous_header(browser) as public:
            assert public.wait_for_link(parent_frag, present=True), "positive control: parent never appeared"
            assert public.link_count_to(child_frag) > 0, "positive control: child not rendered under its parent"

    with allure.step("Set the Level 1 parent's Active Status = False while its Level 2 child remains Active = True"):
        nav.open_by_code(parent_row["entry_code"])
        nav.set_active(False)

    with allure.step("Publish"):
        assert nav.submit(), "the form was not sent"
        _assert_both_gates(nav, parent_row["entry_code"], active=False)
        nav.open_by_code(child_row["entry_code"])
        assert nav.active_checked(), "child's Active Status changed — precondition broken"

    with allure.step("Open the public site header — neither the disabled parent nor its orphaned child renders"):
        with _anonymous_header(browser) as public:
            assert public.wait_for_link(parent_frag, present=False), "disabled parent still renders"
            assert not public.is_signed_in()
            assert public.link_count_to(child_frag) == 0, "orphaned child renders without its parent"


# ═════════════════════ Phase 3 (2026-10-14) — Manual-tagged cases, scripted ═══
# Scripted from the Azure case text (suite 134311). Same accounts and records
# as above: the live HeaderConfiguration only under `header_config_guard`
# (snapshot -> restore -> verify), nav-item work on per-run QCTEST items.
# Every possibly-persisting click is logged first (PBI running rules, rule 10).
# Message WORDING is recorded, never asserted (rule 17); the proof of a refusal
# is that nothing was stored.

def _p3_marks(tc: int, *extra):
    def deco(fn):
        for m in reversed(("control_panel", "global_", "pbi_129363", f"tc_{tc}") + extra):
            fn = getattr(pytest.mark, m)(fn)
        fn = allure.label("pbi", PBI)(fn)
        fn = allure.label("testcase", str(tc))(fn)
        return allure.feature("Site Header")(allure.epic("Global Components")(fn))
    return deco


def _hc_empty_refused(page, tc: int, field: str, setter: str, value: str = "") -> None:
    """Live HeaderConfiguration: put `value` (empty / spaces) in `field`, click
    Publish; the stored value must be unchanged (the guard restores either way)."""
    hc = HeaderConfigurationAdminPage(page)
    hc.open_live_entry()
    before = {"alt_en": hc.alt_en(), "alt_ar": hc.alt_ar(), "redirect_url": hc.redirect_url()}
    key = {"set_alt_en": "alt_en", "set_alt_ar": "alt_ar", "set_redirect_url": "redirect_url"}[setter]
    with allure.step(f"Set {field} to {value!r} and click Publish"):
        getattr(hc, setter)(value)
        log_live_write(HC_RECORD, field, value, tc, action="attempt",
                       note="Publish with the field empty/blank; expected REFUSED (guard restores)")
        sent = hc.submit()
        feedback = hc.validation_feedback() if not sent else ""
    with allure.step("Reopen: the stored value is unchanged"):
        hc.open_live_entry()
        after = {"alt_en": hc.alt_en(), "alt_ar": hc.alt_ar(), "redirect_url": hc.redirect_url()}
    allure.attach(json.dumps({"sent": sent, "feedback": feedback, "before": before, "after": after},
                             ensure_ascii=False, indent=1), "outcome (wording not asserted)",
                  allure.attachment_type.JSON)
    assert after[key] == before[key], (f"FINDING: Publish with {field} = {value!r} was ACCEPTED "
                                       f"(stored {after[key]!r}; the guard restores it)")
    assert not sent or feedback, "the form was sent but nothing changed and no message showed"


@allure.title("Verify that publishing a nav item label change reflects on the frontend after cache refresh (ADO-134269)")
@_p3_marks(134269, "functional_high", "regression")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134269_published_label_reflects_on_frontend(page, browser, qctest_nav_items):
    """QCTEST item, Published + Active (briefly in the real menu, last place),
    relabelled; switched off at the end by the fixture (rule 10: kept)."""
    nav = _as_editor(page)
    item = qctest_nav_items(_label(134269, "OLD"))
    new_label = item.replace("-OLD", "-NEWLABEL")
    frag = _href_fragment(134269, "lbl")
    with allure.step("Precondition: a Published, Active QCTEST nav item"):
        nav.open_create_form()
        nav.fill_nav_item(item, "تسمية قديمة", _url(134269, "lbl"), "9990", active=True)
        log_live_write(NAV_RECORD, item, "create (active)", 134269, action="create")
        assert nav.submit(), "the form was not sent"
        code = nav.wait_for_single_entry(item)["entry_code"]
        _assert_both_gates(nav, code, active=True)
    with allure.step(f"Edit the label to {new_label!r} and click Publish"):
        nav.open_by_code(code)
        nav.fill_nav_item(new_label, "تسمية جديدة", _url(134269, "lbl"), "9990", active=True)
        log_live_write(NAV_RECORD, new_label, "relabel (active)", 134269, action="publish")
        assert nav.submit(), "the form was not sent"
        qctest_nav_items(new_label)  # switched off + logged at teardown
    with allure.step("Public header (logged out) shows the new label after the cache refresh"):
        with _anonymous_header(browser) as public:
            def _shows() -> bool:
                public.open_home_anonymous()
                links = public.page.locator(public.NAV_LINKS)
                return any(frag in (links.nth(i).get_attribute("href") or "")
                           and new_label in links.nth(i).inner_text() for i in range(links.count()))
            try:
                wait_until(_shows, timeout=180, poll=10, message="new label never reached the public header")
                shown = True
            except Exception:  # noqa: BLE001
                shown = False
    assert shown, f"the public header does not show {new_label!r} within 3 minutes"


@allure.title("Verify that leaving Logo Image empty is rejected on publish (ADO-134271)")
@_p3_marks(134271, "functional_high")
@pytest.mark.xdist_group(HC_GROUP)
def test_134271_logo_image_empty_rejected(page, header_config_guard):
    hc = HeaderConfigurationAdminPage(page)
    hc.open_live_entry()
    original = hc.logo_file_name()
    assert original, "precondition: the live header has no logo"
    with allure.step("Remove the Logo Image and click Publish"):
        # The Page Object refuses file removal (2026-10-01 approval scope). The
        # PBI running rules (2026-10-13/14, rule 10) allow test writes on real
        # records; header_config_guard snapshots and restores the logo.
        ObjectAuthoringPage.remove_current_file(hc, hc.FIELD_LOGO_IMAGE)
        pending = hc.file_removal_pending(hc.FIELD_LOGO_IMAGE)
        log_live_write(HC_RECORD, "Logo Image", "", 134271, action="attempt",
                       note=f"Publish with the logo removed (was {original!r}); guard restores")
        sent = hc.submit()
        feedback = hc.validation_feedback() if not sent else ""
    hc.open_live_entry()
    stored = hc.logo_file_name()
    allure.attach(json.dumps({"pending": pending, "sent": sent, "feedback": feedback, "stored": stored,
                              "original": original}, ensure_ascii=False), "outcome", allure.attachment_type.JSON)
    assert pending, "precondition: Remove file did not register"
    assert stored == original, f"FINDING: Publish with no Logo Image was ACCEPTED (stored {stored!r})"


@allure.title("Verify that leaving Logo Alt Text (EN) empty is rejected (ADO-134274)")
@_p3_marks(134274, "functional_high")
@pytest.mark.xdist_group(HC_GROUP)
def test_134274_logo_alt_en_empty_rejected(page, header_config_guard):
    _hc_empty_refused(page, 134274, "Logo Alt Text (EN)", "set_alt_en")


@allure.title("Verify that leaving Logo Alt Text (AR) empty is rejected (ADO-134278)")
@_p3_marks(134278, "functional_high", "bilingual")
@pytest.mark.xdist_group(HC_GROUP)
def test_134278_logo_alt_ar_empty_rejected(page, header_config_guard):
    _hc_empty_refused(page, 134278, "Logo Alt Text (AR)", "set_alt_ar")


@allure.title("Verify that Logo Alt Text (EN) containing only spaces is rejected as empty (ADO-134276)")
@_p3_marks(134276, "functional_low")
@pytest.mark.xdist_group(HC_GROUP)
def test_134276_logo_alt_en_spaces_rejected(page, header_config_guard):
    _hc_empty_refused(page, 134276, "Logo Alt Text (EN)", "set_alt_en", "     ")


@allure.title("Verify that Logo Alt Text (AR) containing only spaces is rejected as empty (ADO-134280)")
@_p3_marks(134280, "functional_low", "bilingual")
@pytest.mark.xdist_group(HC_GROUP)
def test_134280_logo_alt_ar_spaces_rejected(page, header_config_guard):
    _hc_empty_refused(page, 134280, "Logo Alt Text (AR)", "set_alt_ar", "     ")


@allure.title("Verify that Logo Redirect URL containing only spaces is rejected as empty (ADO-134284)")
@_p3_marks(134284, "functional_low")
@pytest.mark.xdist_group(HC_GROUP)
def test_134284_logo_redirect_spaces_rejected(page, header_config_guard):
    _hc_empty_refused(page, 134284, "Logo Redirect URL", "set_redirect_url", "     ")


def _nav_refused(page, qctest_nav_items, tc: int, short: str, label_en, label_ar: str) -> None:
    nav = _as_editor(page)
    marker = qctest_nav_items(_label(tc, short))
    en = marker if label_en is None else label_en
    with allure.step(f"Add a nav item: EN {en!r}, AR {label_ar!r} (Active off); click Publish"):
        nav.open_create_form()
        # The Page Object refuses a non-QCTEST label, so the form is filled with
        # the QCTEST marker first and the case's EN value is typed over it.
        nav.fill_nav_item(marker, label_ar, _url(tc, short.lower()), SAFE_ORDER, active=False)
        if en != marker:
            nav._textbox(nav.FIELD_LABEL_EN).fill(en)
        log_live_write(NAV_RECORD, marker, f"EN={en!r} AR={label_ar!r}", tc, action="attempt",
                       note="expected REFUSED")
        sent = nav.submit()
        feedback = nav.validation_feedback() if not sent else ""
    rows = nav.entries_with_label(en) if en.strip() else []
    allure.attach(json.dumps({"sent": sent, "feedback": feedback, "rows": rows}, ensure_ascii=False),
                  "outcome (wording not asserted)", allure.attachment_type.JSON)
    assert not sent, f"FINDING: the nav item was saved (rows {rows})"
    assert feedback.strip(), "nothing was saved, but no validation message showed"


@allure.title("Verify that leaving Nav Item Label (EN) empty is rejected (ADO-134286)")
@_p3_marks(134286, "functional_high")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134286_nav_label_en_empty_rejected(page, qctest_nav_items):
    _nav_refused(page, qctest_nav_items, 134286, "NOEN", "", "عنصر بدون إنجليزي")


@allure.title("Verify that Nav Item Label (EN) containing only spaces is rejected as empty (ADO-134288)")
@_p3_marks(134288, "functional_low")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134288_nav_label_en_spaces_rejected(page, qctest_nav_items):
    _nav_refused(page, qctest_nav_items, 134288, "SPEN", "     ", "عنصر مسافات")


@allure.title("Verify that Nav Item Label (AR) containing only spaces is rejected as empty (ADO-134292)")
@_p3_marks(134292, "functional_high", "bilingual")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134292_nav_label_ar_spaces_rejected(page, qctest_nav_items):
    _nav_refused(page, qctest_nav_items, 134292, "SPAR", None, "     ")


def _create_level(nav, label: str, level: str, parent, tc: int, short: str) -> dict:
    nav.open_create_form()
    nav.fill_nav_item(label, f"مستوى {level}", _url(tc, short), SAFE_ORDER, active=False)
    nav.select_level(level)
    if parent:
        nav.set_parent_menu(parent)
        try:
            nav.select_parent_item(parent)
        except Exception as exc:  # noqa: BLE001 -- the relationship picker is evidence only
            allure.attach(repr(exc), f"Parent Item picker for {label}", allure.attachment_type.TEXT)
    log_live_write(NAV_RECORD, label, f"level {level}, parent {parent!r} (inactive)", tc, action="create")
    sent = nav.submit()
    feedback = nav.validation_feedback() if not sent else ""
    rows = nav.entries_with_label(label)
    return {"sent": sent, "feedback": feedback, "rows": rows}


@allure.title("Verify that Nav Item Level accepts 1, 2 and 3 with correct Parent Menu enforcement (ADO-134296)")
@_p3_marks(134296, "functional_high")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134296_levels_1_2_3_with_parents(page, qctest_nav_items):
    nav = _as_editor(page)
    l1, l2, l3 = (qctest_nav_items(_label(134296, s)) for s in ("L1", "L2", "L3"))
    out = {"L1": _create_level(nav, l1, "1", None, 134296, "l1")}
    out["L2"] = _create_level(nav, l2, "2", l1, 134296, "l2")
    out["L3"] = _create_level(nav, l3, "3", l2, 134296, "l3")
    allure.attach(json.dumps(out, ensure_ascii=False, indent=1), "outcome", allure.attachment_type.JSON)
    for lvl, res in out.items():
        assert res["sent"] and len(res["rows"]) == 1, f"{lvl} item did not save: {res}"


@allure.title("Verify that Parent Menu accepts a valid selection for a Level 2 item (ADO-134298)")
@_p3_marks(134298, "functional_low")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134298_level2_valid_parent_saves(page, qctest_nav_items):
    nav = _as_editor(page)
    parent, child = qctest_nav_items(_label(134298, "P")), qctest_nav_items(_label(134298, "C"))
    p = _create_level(nav, parent, "1", None, 134298, "p")
    c = _create_level(nav, child, "2", parent, 134298, "c")
    allure.attach(json.dumps({"parent": p, "child": c}, ensure_ascii=False, indent=1), "outcome",
                  allure.attachment_type.JSON)
    assert p["sent"] and len(p["rows"]) == 1, f"parent did not save: {p}"
    assert c["sent"] and len(c["rows"]) == 1, f"Level 2 item with a valid parent did not save: {c}"


@allure.title("Verify that concurrent conflicting edits from two admins cause no silent data loss (ADO-134309)")
@_p3_marks(134309, "edge")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134309_concurrent_edits_no_silent_loss(page, browser, qctest_nav_items):
    """Two Editor sessions (separate contexts) on ONE inactive QCTEST item:
    A changes the EN label, B changes the Display Order; A publishes, then B.
    No silent data loss = A's label survives, or B is refused / warned."""
    nav = _as_editor(page)
    item = qctest_nav_items(_label(134309, "CONC"))
    nav.open_create_form()
    nav.fill_nav_item(item, "تعديل متزامن", _url(134309, "conc"), SAFE_ORDER, active=False)
    log_live_write(NAV_RECORD, item, "create (inactive)", 134309, action="create")
    assert nav.submit(), "precondition item was not saved"
    code = nav.wait_for_single_entry(item)["entry_code"]
    label_a = qctest_nav_items(item + "-A")
    ctx_b = new_context(browser, role="Site Content Editor")
    try:
        nav_b = NavItemAdminPage(ctx_b.new_page())
        CmsLoginPage(nav_b.page).ensure_signed_in_as(*cms_role_credentials("Site Content Editor"))
        nav.open_by_code(code)
        nav_b.open_by_code(code)
        nav.fill_nav_item(label_a, "تعديل متزامن", _url(134309, "conc"), SAFE_ORDER, active=False)
        nav_b.fill_nav_item(item, "تعديل متزامن", _url(134309, "conc"), "9950", active=False)
        log_live_write(NAV_RECORD, item, "A: label, B: order 9950", 134309, action="publish")
        sent_a = nav.submit()
        sent_b = nav_b.submit()
        b_said = nav_b.validation_feedback() + " | " + nav_b.success_notice()
    finally:
        ctx_b.close()
    nav.open_by_code(code)
    final = {"label": nav.label_en_value(), "order": nav.display_order_value()}
    allure.attach(json.dumps({"sent_a": sent_a, "sent_b": sent_b, "b_said": b_said, "final": final},
                             ensure_ascii=False, indent=1), "outcome", allure.attachment_type.JSON)
    assert sent_a, "Admin A's publish did not go through"
    lost_a = final["label"] != label_a
    warned = bool(re.search(r"conflict|modified|changed by|another user|تعارض", b_said, re.I)) or not sent_b
    assert not lost_a or warned, (f"silent data loss: A's label {label_a!r} was overwritten by B's save "
                                  f"with no warning (final {final})")


@allure.title("Verify that the CMS Header Management screen displays all field-level controls (ADO-134247)")
@_p3_marks(134247, "ui")
def test_134247_header_screen_displays_controls(page):
    _as_editor(page)
    hc = HeaderConfigurationAdminPage(page)
    hc.open_live_entry()
    hc_labels = hc.form_field_labels()
    hc_controls = hc.submit_controls_enabled()
    nav = NavItemAdminPage(page)
    nav.open_create_form()
    nav_labels = nav.form_field_labels()
    allure.attach(json.dumps({"header config": hc_labels, "controls": hc_controls, "nav item": nav_labels},
                             ensure_ascii=False, indent=1), "screens", allure.attachment_type.JSON)
    need_hc = ["Logo Image", "Logo Alt Text (EN)", "Logo Alt Text (AR)", "Logo Redirect URL"]
    need_nav = ["Nav Item Label EN", "Nav Item Label AR", "Nav Item URL", "Display Order", "Nav Item Level",
                "Parent Menu", "Active Status"]
    missing = [n for n in need_hc if not any(lbl.startswith(n) for lbl in hc_labels)] + [
        n for n in need_nav if not any(lbl.startswith(n) for lbl in nav_labels)]
    assert not missing, f"fields missing from Header Management: {missing}"
    assert hc_controls, "no Save as Draft / Publish controls rendered"


@allure.title("Verify that reordering nav items via the CMS list updates their Display Order values (ADO-134310)")
@_p3_marks(134310, "functional_low")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134310_reorder_via_list_updates_display_order(page, qctest_nav_items):
    """The case drags a row in the list. The list is read for a drag/reorder
    control; without one the case fails on the missing control (the Display
    Order field per item is the only ordering route) -- decided at bug review."""
    nav = _as_editor(page)
    nav.open_full_list()
    handles = page.locator('[draggable="true"], .drag-handle, [data-qc-oel-reorder], .lexicon-icon-drag').count()
    allure.attach(str(handles), "drag/reorder controls in the nav item list", allure.attachment_type.TEXT)
    assert handles > 0, "the nav item list renders no drag/reorder control (Display Order is edited per item)"


# ═════════════ Character limits (QA lead 2026-10-14: the PBI limit is binding) ═
# limit + 1 characters, then the stored value is read back: it must be refused
# or cut to the PBI limit. Same-form failures → ONE bug per form.

def _hc_over_limit(page, tc: int, field: str, setter: str, value: str, limit: int) -> None:
    hc = HeaderConfigurationAdminPage(page)
    hc.open_live_entry()
    maxlength = hc._textbox(field).get_attribute("maxlength")
    key = {"set_alt_en": "alt_en", "set_alt_ar": "alt_ar", "set_redirect_url": "redirect_url"}[setter]
    with allure.step(f"Type {len(value)} characters in {field} and click Publish"):
        getattr(hc, setter)(value)
        log_live_write(HC_RECORD, field, f"<{len(value)} chars>", tc, action="attempt",
                       note=f"over the PBI limit {limit}; the guard restores")
        sent = hc.submit()
        feedback = hc.validation_feedback() if not sent else ""
    hc.open_live_entry()
    stored = {"alt_en": hc.alt_en, "alt_ar": hc.alt_ar, "redirect_url": hc.redirect_url}[key]()
    allure.attach(json.dumps({"pbi_limit": limit, "typed": len(value), "maxlength": maxlength, "sent": sent,
                              "feedback": feedback, "stored_length": len(stored)}, ensure_ascii=False),
                  "char limit (PBI)", allure.attachment_type.JSON)
    assert len(stored) <= limit or "QCTEST" not in stored, (
        f"{field} accepted {len(stored)} characters; the PBI limit is {limit} (maxlength attribute: {maxlength})")


@allure.title("Verify that Logo Alt Text (EN) rejects input exceeding 150 characters (ADO-134275)")
@_p3_marks(134275, "functional_low")
@pytest.mark.xdist_group(HC_GROUP)
def test_134275_logo_alt_en_over_150(page, header_config_guard):
    _hc_over_limit(page, 134275, "Logo Alt Text (EN)", "set_alt_en", ("QCTEST-134275 " + "x" * 151)[:151], 150)


@allure.title("Verify that Logo Alt Text (AR) rejects input exceeding 150 characters (ADO-134279)")
@_p3_marks(134279, "functional_low", "bilingual")
@pytest.mark.xdist_group(HC_GROUP)
def test_134279_logo_alt_ar_over_150(page, header_config_guard):
    _hc_over_limit(page, 134279, "Logo Alt Text (AR)", "set_alt_ar", ("QCTEST-134279 " + "ع" * 151)[:151], 150)


@allure.title("Verify that Logo Redirect URL rejects input exceeding 500 characters (ADO-134283)")
@_p3_marks(134283, "functional_low")
@pytest.mark.xdist_group(HC_GROUP)
def test_134283_logo_redirect_over_500(page, header_config_guard):
    url = ("https://qcdev.ihorizons.com/web/qatar-chamber/QCTEST-134283-" + "x" * 501)[:501]
    _hc_over_limit(page, 134283, "Logo Redirect URL", "set_redirect_url", url, 500)


def _nav_over_limit(page, qctest_nav_items, tc: int, field: str, limit: int, value: str) -> None:
    """Inactive QCTEST nav item with `field` = limit + 1 characters; Publish;
    the stored value must be refused or cut to the PBI limit."""
    nav = _as_editor(page)
    marker = qctest_nav_items(_label(tc, "LIMIT"))
    nav.open_create_form()
    nav.fill_nav_item(marker, "حد الحروف", _url(tc, "limit"), SAFE_ORDER, active=False)
    box = nav._textbox(field)
    maxlength = box.get_attribute("maxlength")
    box.fill(value)
    typed_value = box.input_value()
    typed = len(typed_value)
    log_live_write(NAV_RECORD, marker, f"{field} = <{len(value)} chars>", tc, action="create",
                   note=f"over the PBI limit {limit} (inactive)")
    sent = nav.submit()
    feedback = nav.validation_feedback() if not sent else ""
    stored = ""
    label_en = typed_value if field == nav.FIELD_LABEL_EN else marker
    rows = nav.entries_with_label(label_en) if sent else []
    if rows:
        nav.open_by_code(rows[0]["entry_code"])
        stored = nav._textbox(field).input_value()
        if field == nav.FIELD_LABEL_EN:
            qctest_nav_items(stored)  # logged as kept at teardown
    allure.attach(json.dumps({"pbi_limit": limit, "typed": len(value), "field kept after typing": typed,
                              "maxlength": maxlength, "sent": sent, "feedback": feedback,
                              "stored_length": len(stored)}, ensure_ascii=False),
                  "char limit (PBI)", allure.attachment_type.JSON)
    assert len(stored) <= limit, (
        f"{field} accepted {len(stored)} characters; the PBI limit is {limit} (maxlength attribute: {maxlength})")


@allure.title("Verify that Nav Item Label (EN) rejects input exceeding 100 characters (ADO-134287)")
@_p3_marks(134287, "functional_low")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134287_nav_label_en_over_100(page, qctest_nav_items):
    _nav_over_limit(page, qctest_nav_items, 134287, NavItemAdminPage.FIELD_LABEL_EN, 100,
                    (_label(134287, "LONG") + "-" + "x" * 101)[:101])


@allure.title("Verify that Nav Item Label (AR) rejects input exceeding 100 characters (ADO-134291)")
@_p3_marks(134291, "functional_low", "bilingual")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134291_nav_label_ar_over_100(page, qctest_nav_items):
    _nav_over_limit(page, qctest_nav_items, 134291, NavItemAdminPage.FIELD_LABEL_AR, 100,
                    ("QCTEST " + "ع" * 101)[:101])


@allure.title("Verify that Nav Item URL rejects input exceeding 500 characters (ADO-134295)")
@_p3_marks(134295, "functional_low")
@pytest.mark.xdist_group(NAV_GROUP)
def test_134295_nav_url_over_500(page, qctest_nav_items):
    _nav_over_limit(page, qctest_nav_items, 134295, NavItemAdminPage.FIELD_URL, 500,
                    ("/web/qatar-chamber/qctest-134295-" + "x" * 501)[:501])

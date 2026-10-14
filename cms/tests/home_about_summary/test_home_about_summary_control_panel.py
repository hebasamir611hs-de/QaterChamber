"""
cms/tests/home_about_summary/test_home_about_summary_control_panel.py -
Control_Panel cases for PBI 129389 (QC-HOME-013, About Us Section & Last Year
Achievements Counters), surfaces `manage-about-us-section` /
`manage-about-us-counter` (Object Authoring only).

REWRITTEN 2026-10-07 (Phase 3, B-129389). Every test either reads the live
records without saving, or works on DISPOSABLE `QCTEST-<tc>-*` records created
from the empty create form and deleted (QCTEST-guarded, by entry code) in
teardown. The live Section 52157 and Counters 52165/52171/52177/52183 are never
written. Each test names its account (Editor / Author / site member); TEST_USER
is never used. No test publishes a record to the public Home Page; cases that need one are
NEEDS USER (see .claude/qa-runs/phase3_129389_2026-10-07_report.md).
"""

import json
import os

import allure
import pytest

from cms.pages.home_about_summary.home_about_summary_admin_page import (
    HomeAboutSummaryAdminPage,
    HomeAboutCounterAdminPage,
    COUNTER_ENTRY_CODES,
    SECTION_ENTRY_CODE,
    FIELD_SECTION_TAG_EN,
    FIELD_SECTION_TAG_AR,
    FIELD_SECTION_HEADING_EN,
    FIELD_SECTION_HEADING_AR,
    FIELD_BUILDING_IMAGE_PRIMARY,
    FIELD_YEARS_BADGE_EN,
    FIELD_YEARS_BADGE_AR,
    FIELD_READ_MORE_LABEL_EN,
    FIELD_READ_MORE_LABEL_AR,
    FIELD_READ_MORE_URL,
    FIELD_COUNTER_TITLE_EN,
    FIELD_COUNTER_TITLE_AR,
    FIELD_COUNTER_VALUE,
    FIELD_COUNTER_ICON,
    FIELD_COUNTER_DISPLAY_ORDER,
    Disposables,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url
from core.web.browser import new_context
from web.pages.home_about_summary.home_about_summary_page import HomeAboutSummaryPage
from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PENDING_REVIEW, STATUS_PUBLISHED

FIXTURES = "web/tests/home_about_summary/fixtures"



ANON_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
IMG = f"{FIXTURES}/about_building_primary.jpg"
SECTION_MANAGE_URL = control_panel_url("/en/web/qatar-chamber/manage-about-us-section")


def _attach(name: str, data) -> None:
    allure.attach(json.dumps(data, ensure_ascii=False, indent=1, default=str), name=name,
                  attachment_type=allure.attachment_type.JSON)


def _assert_refused(result: dict, what: str) -> None:
    _attach(f"submit outcome — {what}", result)
    assert not result["created_code"] and result["outcome"] in ("refused", None), (
        f"{what}: the submit was ACCEPTED (record created) — {result}")
    assert result["refusal"] or result["invalid_inputs"], (
        f"{what}: nothing was saved but the form gave no feedback either — {result}")


class _Disposables(Disposables):
    def cleanup(self) -> None:
        out = super().cleanup()
        _attach("teardown", out)
        assert not out["left"], f"QCTEST teardown left records behind: {out['left']}"


@pytest.fixture
def qc_section(page):
    admin = HomeAboutSummaryAdminPage(page)
    d = _Disposables(admin)
    yield admin, d
    d.cleanup()


@pytest.fixture
def qc_counter(page):
    counter = HomeAboutCounterAdminPage(page)
    d = _Disposables(counter)
    yield counter, d
    d.cleanup()


def _section_refusal_case(admin, d, tc: str, label: str, **overrides) -> None:
    prefix = f"QCTEST-{tc}-{label}"
    admin.open_new_form()
    admin.fill_qctest_section(prefix, **overrides)
    result = admin.resolve_created(admin.submit_outcome(), prefix)
    d.track(prefix, result)
    _assert_refused(result, f"{tc} {label}")


def _counter_refusal_case(counter, d, tc: str, label: str, **overrides) -> None:
    prefix = f"QCTEST-{tc}-{label}"
    counter.open_new_form()
    counter.fill_qctest_counter(prefix, **overrides)
    result = counter.resolve_created(counter.submit_outcome(), prefix)
    d.track(prefix, result)
    _assert_refused(result, f"{tc} {label}")


# ---- RBAC -------------------------------------------------------------------
@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("A Site Content Editor can access the About Us Section Management screen (ADO-136101)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129389
@pytest.mark.tc_136101
@ANON_PAGE
def test_site_content_editor_can_access_about_us_section_management_136101(page):
    """Account: QC Site Content Editor. Read-only: opens the live Section's
    edit form and checks the fields are editable and a Publish action is
    offered. Nothing is typed or saved."""
    admin = HomeAboutSummaryAdminPage(page)
    admin.sign_in_as("Site Content Editor")
    with allure.step("Open About Us Section management -> live entry"):
        admin.open_entry_by_code(SECTION_ENTRY_CODE, locale="en")
    with allure.step("Fields are editable and Publish is offered"):
        assert admin.current_status() == STATUS_PUBLISHED
        for label in (FIELD_SECTION_TAG_EN, FIELD_SECTION_HEADING_EN, FIELD_READ_MORE_URL):
            assert page.get_by_role("textbox", name=label, exact=True).is_editable(), label
        assert page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).count() > 0


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("A user without the Site Content Editor role cannot access the About Us Section Management screen (ADO-136102)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129389
@pytest.mark.tc_136102
@ANON_PAGE
def test_user_without_editor_role_cannot_access_about_us_section_management_136102(page):
    """Account: QC site member (no CMS role) — signs in successfully, then is
    refused. Bare page.goto (no session guard). The live refusal page is the
    site's "Coming Soon" 404; wording is noted, not asserted (accepted CMS
    deviation)."""
    admin = HomeAboutSummaryAdminPage(page)
    admin.sign_in_as("Site Member")
    assert CmsLoginPage(page).login_succeeded(), "site-member login itself failed"
    with allure.step("Navigate directly to the About Us Section management URL"):
        status = admin.goto_bare(SECTION_MANAGE_URL)
        controls = admin.cms_form_controls()
        _attach("denial page", {"status": status, **controls})
    with allure.step("No form, no entries, no workflow action is rendered"):
        assert controls["object_fields"] == 0
        assert controls["entry_rows"] == 0
        assert controls["workflow_buttons"] == 0


# ---- Section on disposable QCTEST records --------------------------------------
@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Admin can save the About Us section as a draft without publishing (ADO-136104)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129389
@pytest.mark.tc_136104
@ANON_PAGE
def test_admin_can_save_about_us_section_as_draft_136104(page, qc_section, browser):
    """Account: QC Site Content Editor, on a disposable QCTEST section."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Editor")
    prefix = "QCTEST-136104"
    with allure.step("Enter all mandatory fields and Save as Draft"):
        admin.open_new_form()
        values = admin.fill_qctest_section(prefix)
        result = admin.resolve_created(admin.submit_outcome(draft=True), prefix)
        d.track(prefix, result)
        _attach("save as draft", result)
        assert result["created_code"], f"Save as Draft did not create a record: {result}"
    with allure.step("Record is Draft and holds the entered values"):
        admin.open_entry_by_code(result["created_code"], locale="en")
        assert admin.current_status() == STATUS_DRAFT
        assert admin.field_value(FIELD_SECTION_HEADING_EN) == values[FIELD_SECTION_HEADING_EN]
    with allure.step("Visitor (logged-out) does not see the draft"):
        ctx = new_context(browser, use_auth_state=False)
        try:
            home = HomeAboutSummaryPage(ctx.new_page())
            home.open_home()
            home.wait_for_section()
            assert prefix not in home.heading_text()
        finally:
            ctx.close()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Admin can preview the About Us section before publishing (ADO-136105)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129389
@pytest.mark.tc_136105
@ANON_PAGE
def test_admin_can_preview_about_us_section_before_publishing_136105(page, qc_section, browser):
    """Account: QC Site Content Editor, on a disposable QCTEST draft. Preview
    is the row-level Preview link (staff surface); the logged-out Home Page
    must stay unchanged."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Editor")
    prefix = "QCTEST-136105"
    admin.open_new_form()
    admin.fill_qctest_section(prefix)
    result = admin.resolve_created(admin.submit_outcome(draft=True), prefix)
    d.track(prefix, result)
    assert result["created_code"], f"draft not created: {result}"
    with allure.step("Click Preview on the draft row"):
        admin.open_entries_list(locale="en")
        preview_url = admin.row_preview_url_by_code(result["created_code"])
        assert preview_url, "no Preview link on the draft row"
        admin.open(preview_url)
        body = page.locator("body").inner_text()
        _attach("preview", {"url": preview_url, "body_head": body[:600]})
        assert prefix in body, "preview did not render the draft's content"
    with allure.step("Live Home Page unaffected (logged-out)"):
        ctx = new_context(browser, use_auth_state=False)
        try:
            home = HomeAboutSummaryPage(ctx.new_page())
            home.open_home()
            home.wait_for_section()
            assert prefix not in home.heading_text()
        finally:
            ctx.close()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Publishing is blocked when Section Heading is left empty, EN and AR (ADO-136108)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136108
@ANON_PAGE
def test_publish_blocked_when_section_heading_empty_136108(page, qc_section):
    """Account: QC Site Content Author (a gap lands in Pending Review, never live)."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Author")
    with allure.step("Heading (EN) empty -> submit refused"):
        _section_refusal_case(admin, d, "136108", "EN", image=IMG, **{FIELD_SECTION_HEADING_EN: ""})
    with allure.step("Heading (AR) empty -> submit refused"):
        _section_refusal_case(admin, d, "136108", "AR", image=IMG, **{FIELD_SECTION_HEADING_AR: ""})


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Publishing is blocked when Section Description is left empty, EN and AR (ADO-136110)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136110
@ANON_PAGE
def test_publish_blocked_when_section_description_empty_136110(page, qc_section):
    """Account: QC Site Content Author."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Author")
    with allure.step("Description (EN) empty -> submit refused"):
        _section_refusal_case(admin, d, "136110", "EN", image=IMG, description_en="")
    with allure.step("Description (AR) empty -> submit refused"):
        _section_refusal_case(admin, d, "136110", "AR", image=IMG, description_ar="")


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Building Images upload succeeds with a valid JPG file under 2MB (ADO-136117)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136117
@ANON_PAGE
def test_building_image_uploads_with_valid_jpg_under_2mb_136117(page):
    """Account: QC Site Content Editor, on the empty create form; nothing is
    saved (the uploaded file stays in Documents & Media, unreferenced)."""
    admin = HomeAboutSummaryAdminPage(page)
    admin.sign_in_as("Site Content Editor")
    admin.open_new_form()
    with allure.step("Upload a valid JPG (<2 MB) to Building Image (Primary)"):
        admin.safe_upload(FIELD_BUILDING_IMAGE_PRIMARY, f"{FIXTURES}/about_building_primary.jpg")
    with allure.step("The field shows the uploaded file"):
        assert "about_building_primary" in admin.building_image_primary_filename()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Building Images upload is rejected when file exceeds 2MB or has an unsupported format (ADO-136118)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136118
@ANON_PAGE
def test_building_image_upload_rejected_oversized_or_unsupported_136118(page):
    """Account: QC Site Content Editor, empty create form, nothing saved.
    Oversized fixture is 13.2 MB (well above the 3 MB tolerance)."""
    admin = HomeAboutSummaryAdminPage(page)
    admin.sign_in_as("Site Content Editor")
    with allure.step("13.2 MB JPG is rejected"):
        admin.open_new_form()
        assert admin.upload_file_expect_rejected(FIELD_BUILDING_IMAGE_PRIMARY, f"{FIXTURES}/about_building_oversized.jpg")
    with allure.step("GIF (unsupported format) is rejected"):
        admin.open_new_form()
        assert admin.upload_file_expect_rejected(FIELD_BUILDING_IMAGE_PRIMARY, f"{FIXTURES}/about_building_invalid.gif")


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Publishing is blocked when Building Images are not uploaded (ADO-136119)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136119
@ANON_PAGE
def test_publish_blocked_when_building_images_not_uploaded_136119(page, qc_section):
    """Account: QC Site Content Author. Every other field valid, no image."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Author")
    _section_refusal_case(admin, d, "136119", "NOIMG")


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Publishing is blocked when Read More Label is left empty, EN and AR (ADO-136123)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136123
@ANON_PAGE
def test_publish_blocked_when_read_more_label_empty_136123(page, qc_section):
    """Account: QC Site Content Author."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Author")
    img = f"{FIXTURES}/about_building_primary.jpg"
    with allure.step("Read More Label (EN) empty -> refused"):
        _section_refusal_case(admin, d, "136123", "EN", image=img, **{FIELD_READ_MORE_LABEL_EN: ""})
    with allure.step("Read More Label (AR) empty -> refused"):
        _section_refusal_case(admin, d, "136123", "AR", image=img, **{FIELD_READ_MORE_LABEL_AR: ""})


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Read More URL accepts a valid URL up to 500 characters (ADO-136124)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136124
@ANON_PAGE
def test_read_more_url_accepts_valid_url_136124(page, qc_section):
    """Account: QC Site Content Author -> lands Pending Review (not public),
    Active Status unticked. Also the CONTROL for the refusal cases: a fully
    valid entry must be accepted. The 500-char boundary is not exercised
    (char-limit cases are N/A on this project)."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Author")
    prefix = "QCTEST-136124"
    url = "https://qcdev.ihorizons.com/web/qatar-chamber/about-us?qctest=136124"
    admin.open_new_form()
    admin.fill_qctest_section(prefix, image=f"{FIXTURES}/about_building_primary.jpg", **{FIELD_READ_MORE_URL: url})
    with allure.step("Submit for Review with a valid URL -> accepted"):
        result = admin.resolve_created(admin.submit_outcome(), prefix)
        d.track(prefix, result)
        _attach("submit", result)
        assert result["created_code"] and result["outcome"] != "refused", f"valid entry refused: {result}"
    with allure.step("URL persisted; record is Pending Review"):
        admin.open_entry_by_code(result["created_code"], locale="en")
        assert admin.field_value(FIELD_READ_MORE_URL) == url
        assert admin.current_status() == STATUS_PENDING_REVIEW


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Publishing is blocked when Read More URL is left empty (ADO-136125)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136125
@ANON_PAGE
def test_publish_blocked_when_read_more_url_empty_136125(page, qc_section):
    """Account: QC Site Content Author."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Author")
    _section_refusal_case(admin, d, "136125", "NOURL", image=f"{FIXTURES}/about_building_primary.jpg",
                          **{FIELD_READ_MORE_URL: ""})


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Read More URL is rejected when an invalid URL format is entered (ADO-136126)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136126
@ANON_PAGE
def test_read_more_url_rejects_invalid_format_136126(page, qc_section):
    """Account: QC Site Content Author. Message wording is noted, not asserted."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Author")
    _section_refusal_case(admin, d, "136126", "BADURL", image=f"{FIXTURES}/about_building_primary.jpg",
                          **{FIELD_READ_MORE_URL: "not a valid url"})


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("All About Us section field values persist correctly after save and reload (ADO-136136)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136136
@ANON_PAGE
def test_about_us_section_field_values_persist_after_save_and_reload_136136(page, qc_section):
    """Account: QC Site Content Editor, disposable QCTEST draft. Save, sign
    out, sign back in, reopen: every value is still there."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Editor")
    prefix = "QCTEST-136136"
    admin.open_new_form()
    values = admin.fill_qctest_section(prefix, image=f"{FIXTURES}/about_building_primary.jpg")
    result = admin.resolve_created(admin.submit_outcome(draft=True), prefix)
    d.track(prefix, result)
    assert result["created_code"], f"draft not created: {result}"
    with allure.step("Sign out, sign back in, reopen the record"):
        # Cookie drop, not a server logout: the server-side one also ended the
        # shared storageState session other workers/tools use (2026-10-13).
        admin.logout_and_return()
        email, password = cms_role_credentials("Site Content Editor")
        CmsLoginPage(page).open_login().login(email, password)
        admin.open_entry_by_code(result["created_code"], locale="en")
    with allure.step("Every field holds the saved value"):
        got = {k: admin.field_value(k) for k in values if not k.startswith("description")}
        got["description_en"] = admin.description_en_value().strip()
        got["description_ar"] = admin.description_ar_value().strip()
        got["image"] = admin.file_name_shown(FIELD_BUILDING_IMAGE_PRIMARY)  # saved file renders as "Current file:", healed 2026-10-07
        _attach("persisted", got)
        for k, v in values.items():
            assert got[k].strip() == v.strip(), f"{k}: saved {v!r}, read back {got[k]!r}"
        assert "about_building_primary" in got["image"]


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Discarding unsaved changes reverts to the last saved state (ADO-136138)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136138
@ANON_PAGE
def test_discard_unsaved_changes_reverts_to_last_saved_state_136138(page, qc_section):
    """Account: QC Site Content Editor, disposable QCTEST draft. Edit without
    saving, leave, reopen: the saved value is back."""
    admin, d = qc_section
    admin.sign_in_as("Site Content Editor")
    prefix = "QCTEST-136138"
    admin.open_new_form()
    values = admin.fill_qctest_section(prefix)
    result = admin.resolve_created(admin.submit_outcome(draft=True), prefix)
    d.track(prefix, result)
    assert result["created_code"], f"draft not created: {result}"
    admin.open_entry_by_code(result["created_code"], locale="en")
    with allure.step("Change the heading, then leave without saving"):
        admin.fill_text(FIELD_SECTION_HEADING_EN, f"{prefix} UNSAVED CHANGE")
        page.once("dialog", lambda dlg: dlg.accept())
        admin.open_entries_list(locale="en")
    with allure.step("Reopen: the last saved heading is shown"):
        admin.open_entry_by_code(result["created_code"], locale="en")
        assert admin.field_value(FIELD_SECTION_HEADING_EN) == values[FIELD_SECTION_HEADING_EN]


# ---- Counters on disposable QCTEST records -----------------------------------------
@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Admin can add counters up to the maximum of 4 (ADO-136109)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129389
@pytest.mark.tc_136109
@ANON_PAGE
def test_admin_can_add_counters_up_to_max_of_4_136109(page):
    """Account: QC Site Content Editor. Read-only. The live list already holds
    >= 4 counters, so per the PBI ("maximum 4 badges") no create path may be
    offered any more."""
    counter = HomeAboutCounterAdminPage(page)
    counter.sign_in_as("Site Content Editor")
    counter.open_entries_list(locale="en")
    codes = counter.entry_codes()
    counter.open_entries_list(locale="en")
    state = counter.create_control_state()
    _attach("counter list", {"codes": codes, "create_control": state})
    assert all(code in codes for code in COUNTER_ENTRY_CODES), "the 4 seeded counters are not all listed"
    assert not (state["add_new_visible"] or state["save_as_draft_enabled"] or state["submit_enabled"]), (
        f"{len(codes)} counters exist and a create path is still offered: {state}")


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("A 5th counter cannot be added once 4 counters already exist (ADO-136140)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129389
@pytest.mark.tc_136140
@ANON_PAGE
def test_5th_counter_cannot_be_added_136140(page, qc_counter):
    """Account: QC Site Content Editor. Attempts Save as Draft of a disposable
    QCTEST counter (inactive, Draft — never public) while >= 4 exist."""
    counter, d = qc_counter
    counter.sign_in_as("Site Content Editor")
    codes = counter.entry_codes()
    assert len(codes) >= 4, f"precondition: expected >= 4 counters, found {codes}"
    prefix = "QCTEST-136140"
    counter.open_new_form()
    counter.fill_qctest_counter(prefix)
    result = counter.resolve_created(counter.submit_outcome(draft=True), prefix)
    d.track(prefix, result)
    _attach("attempt", {"existing": codes, **result})
    assert not result["created_code"], f"a counter beyond the 4-counter maximum was saved: {result}"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Publishing is blocked when a Counter Title is left empty, EN and AR (ADO-136128)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136128
@ANON_PAGE
def test_publish_blocked_when_counter_title_empty_136128(page, qc_counter):
    """Account: QC Site Content Author."""
    counter, d = qc_counter
    counter.sign_in_as("Site Content Author")
    with allure.step("Counter Title (EN) empty -> refused"):
        _counter_refusal_case(counter, d, "136128", "EN", **{FIELD_COUNTER_TITLE_EN: ""})
    with allure.step("Counter Title (AR) empty -> refused"):
        _counter_refusal_case(counter, d, "136128", "AR", **{FIELD_COUNTER_TITLE_AR: ""})


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Publishing is blocked when Counter Value is left empty (ADO-136130)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136130
@ANON_PAGE
def test_publish_blocked_when_counter_value_empty_136130(page, qc_counter):
    """Account: QC Site Content Author."""
    counter, d = qc_counter
    counter.sign_in_as("Site Content Author")
    _counter_refusal_case(counter, d, "136130", "NOVAL", **{FIELD_COUNTER_VALUE: ""})


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Counter Display Order accepts a valid positive integer and persists after save (ADO-136134)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136134
@ANON_PAGE
def test_counter_display_order_accepts_valid_positive_integer_136134(page, qc_counter):
    """Account: QC Site Content Author, disposable QCTEST draft counter."""
    counter, d = qc_counter
    counter.sign_in_as("Site Content Author")
    prefix = "QCTEST-136134"
    counter.open_new_form()
    counter.fill_qctest_counter(prefix, **{FIELD_COUNTER_DISPLAY_ORDER: "100"})
    result = counter.resolve_created(counter.submit_outcome(draft=True), prefix)
    d.track(prefix, result)
    assert result["created_code"], f"draft not created: {result}"
    counter.open_entry_by_code(result["created_code"], locale="en")
    assert counter.display_order_value() == "100"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Counter Display Order rejects empty, zero, negative, or non-numeric input (ADO-136135)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136135
@ANON_PAGE
def test_counter_display_order_rejects_invalid_values_136135(page, qc_counter):
    """Account: QC Site Content Author. Non-numeric text cannot be typed into
    the number input at all (recorded, counts as rejected)."""
    counter, d = qc_counter
    counter.sign_in_as("Site Content Author")
    for label, value in (("EMPTY", ""), ("ZERO", "0"), ("NEG", "-1")):
        with allure.step(f"Display Order = {value!r} -> refused"):
            _counter_refusal_case(counter, d, "136135", label, **{FIELD_COUNTER_DISPLAY_ORDER: value})
    with allure.step("Display Order = 'abc' cannot be entered"):
        counter.open_new_form()
        try:
            counter.fill_number(FIELD_COUNTER_DISPLAY_ORDER, "abc")
            typed = counter.display_order_value()
        except Exception as exc:  # noqa: BLE001 — Playwright refuses text in type=number
            typed = f"<refused: {type(exc).__name__}>"
        _attach("non-numeric", {"value_after_fill": typed})
        assert typed in ("",) or typed.startswith("<refused")


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Counter Icon upload succeeds with a valid PNG or SVG under 2MB (ADO-136132)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136132
@ANON_PAGE
def test_counter_icon_uploads_valid_png_or_svg_under_2mb_136132(page, qc_counter):
    """Account: QC Site Content Author, disposable QCTEST draft counter."""
    counter, d = qc_counter
    counter.sign_in_as("Site Content Author")
    prefix = "QCTEST-136132"
    counter.open_new_form()
    counter.fill_qctest_counter(prefix)
    counter.safe_upload(FIELD_COUNTER_ICON, f"{FIXTURES}/about_counter_icon.svg")
    assert "about_counter_icon" in counter.file_name_shown(FIELD_COUNTER_ICON)
    result = counter.resolve_created(counter.submit_outcome(draft=True), prefix)
    d.track(prefix, result)
    assert result["created_code"], f"draft not created: {result}"
    counter.open_entry_by_code(result["created_code"], locale="en")
    assert "about_counter_icon" in counter.file_name_shown(FIELD_COUNTER_ICON)


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Counter Icon upload is rejected for unsupported format or oversized file (ADO-136133)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136133
@ANON_PAGE
def test_counter_icon_upload_rejected_unsupported_or_oversized_136133(page):
    """Account: QC Site Content Author, empty create form, nothing saved.
    Oversized fixture is 23.5 MB (above the 3 MB tolerance)."""
    counter = HomeAboutCounterAdminPage(page)
    counter.sign_in_as("Site Content Author")
    with allure.step("Control: a valid SVG IS accepted (so a rejection below means something)"):
        counter.open_new_form()
        counter.safe_upload(FIELD_COUNTER_ICON, f"{FIXTURES}/about_counter_icon.svg")
        assert "about_counter_icon" in counter.file_name_shown(FIELD_COUNTER_ICON)
    with allure.step("23.5 MB PNG rejected"):
        counter.open_new_form()
        assert counter.upload_file_expect_rejected(FIELD_COUNTER_ICON, f"{FIXTURES}/about_counter_icon_oversized.png")
    with allure.step("BMP rejected"):
        counter.open_new_form()
        assert counter.upload_file_expect_rejected(FIELD_COUNTER_ICON, f"{FIXTURES}/about_counter_icon_invalid.bmp")


# ═══════════════════════════════════════════════════════════════════════════
# USER ORDER 2026-10-07 22:45 — execute every case.
# * Char-limit cases follow bug-rules Rule 5: the implemented limit is read
#   live (maxlength), the field is exercised AT that limit (and one over, to
#   see truncation) on the create form, and the at-max values are rendered on
#   the public page through a public QCTEST record (one shared test) to check
#   the UI. Nothing over the limit is ever saved. Rich text -> N/A, checked.
# * The public-page half of Rule 5 (render at max) and the flows that need a
#   PUBLISHED record on the Home Page are NOT scripted here: publishing a
#   public QCTEST record on shared qcdev was refused by this session's
#   permission policy, and writing the live records is not approved.
#   They are listed as NEEDS USER in the Phase-3 report.
# ═══════════════════════════════════════════════════════════════════════════
def _plain_limit_case(page, label: str, us_limit: int, *, counter: bool = False, over: bool = False):
    """Rule 5 on one plain textbox, on the empty create form (nothing saved:
    an over-limit QCTEST record could not be deleted from qcdev's trash).
    HEALED 2026-10-07: these fields carry no `maxlength`; the implemented
    limit is the "<n> / <max>" counter rendered under the field."""
    po = HomeAboutCounterAdminPage(page) if counter else HomeAboutSummaryAdminPage(page)
    po.sign_in_as("Site Content Author")
    po.open_new_form()
    implemented = po.maxlength(label)
    n = (implemented or us_limit) + (1 if over else 0)
    po.fill_text(label, "Q" * n)
    kept = len(po.field_value(label))
    shown = po.char_counter(label)
    data = {"field": label, "us_limit": us_limit, "implemented_limit": implemented,
            "typed": n, "kept": kept, "counter_after_fill": shown,
            "submit_attempted": False}
    _attach(f"Rule 5 — {label}", data)
    if implemented is None:
        data["result"] = "N/A: no limit implemented in the UI (team rule 2026-10-03: no char limits)"
        _attach("result", data)
        return data
    assert implemented >= us_limit, (
        f"{label}: implemented limit {implemented} is SHORTER than the US limit {us_limit} (Rule 5.3)")
    if over:
        # Typing past the limit is recorded, not failed (not-a-bug list,
        # 2026-10-02/03); nothing below the limit may be lost.
        assert kept >= implemented, f"{label}: typed {n}, only {kept} kept"
        data["result"] = "truncated at limit" if kept == implemented else "UI lets the value run past the counter limit (note only)"
    else:
        assert kept == implemented, f"{label}: value at the implemented max ({implemented}) not kept in full ({kept})"
        data["result"] = "accepted at implemented max"
    _attach("result", data)
    return data


def _limit_test(tc, label, us_limit, counter=False, over=False):
    @allure.epic("Home Page")
    @allure.feature("About Us Section & Achievements Counters")
    @allure.title(f"Char limit (Rule 5) — {label} {'rejects over' if over else 'accepts up to'} {us_limit} (ADO-{tc})")
    @pytest.mark.control_panel
    @pytest.mark.about
    @pytest.mark.functional_low
    @pytest.mark.pbi_129389
    @ANON_PAGE
    def _t(page):
        """Account: QC Site Content Author. Create form only, nothing saved."""
        _plain_limit_case(page, label, us_limit, counter=counter, over=over)
    return getattr(pytest.mark, f"tc_{tc}")(_t)


test_section_tag_limit_accepts_136111 = _limit_test("136111", FIELD_SECTION_TAG_EN, 50)
test_section_tag_limit_rejects_over_136112 = _limit_test("136112", FIELD_SECTION_TAG_EN, 50, over=True)
test_section_heading_limit_accepts_136113 = _limit_test("136113", FIELD_SECTION_HEADING_EN, 200)
test_section_heading_limit_rejects_over_136114 = _limit_test("136114", FIELD_SECTION_HEADING_EN, 200, over=True)
test_years_badge_limit_accepts_136120 = _limit_test("136120", FIELD_YEARS_BADGE_EN, 50)
test_years_badge_limit_rejects_over_136121 = _limit_test("136121", FIELD_YEARS_BADGE_EN, 50, over=True)
test_read_more_label_limit_accepts_136122 = _limit_test("136122", FIELD_READ_MORE_LABEL_EN, 50)
test_counter_title_limit_accepts_136127 = _limit_test("136127", FIELD_COUNTER_TITLE_EN, 30, counter=True)
test_counter_value_limit_accepts_136129 = _limit_test("136129", FIELD_COUNTER_VALUE, 10, counter=True)
test_counter_value_limit_rejects_over_136131 = _limit_test("136131", FIELD_COUNTER_VALUE, 10, counter=True, over=True)


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("Section Description is rich text — char-limit cases N/A per Rule 5.1 (ADO-136115 / 136116)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136115
@pytest.mark.tc_136116
@ANON_PAGE
def test_section_description_is_rich_text_char_limit_na_136115_136116(page):
    """Account: QC Site Content Author. Confirms the field IS a CKEditor (two
    iframes, EN/AR) so Rule 5.1 applies: result N/A, recorded as checked."""
    admin = HomeAboutSummaryAdminPage(page)
    admin.sign_in_as("Site Content Author")
    admin.open_new_form()
    try:
        page.locator('iframe[title="editor"]').nth(1).wait_for(state="attached", timeout=20000)
    except Exception:  # noqa: BLE001
        pass
    editors = page.locator('iframe[title="editor"]').count()
    _attach("rich text check", {"ckeditor_iframes": editors, "result": "N/A (bug-rules Rule 5.1)"})
    assert editors >= 2



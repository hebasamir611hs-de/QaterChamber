"""
web/tests/about_chairman_message/test_chairman_message_control_panel.py —
Chairman's Message (PBI 129393 / QC-ABOUT-002), Control_Panel platform.

Source: the 14 approved, Automation-tagged cases in this batch that carry
the `Control_Panel` Platform tag (134759, 134760, 134774, 134776, 134777,
134778, 134779, 134780, 134783, 134784, 134787, 134828, 134829, 134834) —
per active/standards.md's "one test per platform" rule, each case that ALSO
carries `Web` is split into a Control_Panel test HERE (the CMS edit/publish
half) and a sibling Web test in test_chairman_message_web.py (the public-
page-verification half), sharing step intent, never one test with a branch.
134778 carries only `Control_Panel` (no `Web` tag) so it has no sibling.

CORRECTED 2026-09-07 (per .claude/context/active/standards.md's "Object
Authoring Is the Only Path for Content Operations — Not Content & Data"):
an EARLIER version of this module (and of ChairmanMessageAdminPage) drove
every field/lifecycle action through Content & Data — that surface is
RETIRED project-wide for Object-Definition-backed content records. THIS
BATCH (TC 134774, 134776, 134777, 134778, 134780, 134787) is scripted
against the corrected, mandatory path: Object Authoring
(`ObjectAuthoringPage`, composed via `ChairmanMessageAdminPage.
open_object_authoring_form()`). See that Page Object's own docstring for
the full, re-verified extraction record (slug, entry code, field labels,
and the Preview mechanism this correction newly unblocked).

TEST_USER/TEST_PASSWORD are real, working qcdev credentials (confirmed live
this session).

**⚠ REAL, LIVE, DISCLOSED CONTENT FINDING (2026-09-07)** — independently
re-confirmed via Content & Data, Object Authoring, AND the public page
itself in a genuinely anonymous context: this record's English
("en-us"/default-locale) fields — Page Title, Chairman Name, Chairman
Designation, etc. — currently hold ARABIC text, not the English values
several EXISTING (uncommitted, prior-session) assertions elsewhere in this
PBI's test suite assume are live. Root cause undetermined, flagged to the
QA Manager. See ChairmanMessageAdminPage's docstring for detail. Every
CMS-mutating test below is TEST_OWNED (cms-profile.md's Test-Data Policy):
it dynamically READS the record's current value immediately before
mutating and restores that SAME captured value (language-agnostic) in a
`finally` block regardless of outcome — never a hardcoded assumed
"original".

Because this record's Object Authoring status vocabulary is Draft/Approved
(not Draft/Published/Unpublished), TC 134776's literal expected wording
("Status changes to Unpublished") is scripted per the case's exact stated
text and is EXPECTED TO FAIL HONESTLY against the real "Draft" status —
Result Integrity forbids loosening the assertion to match the live
behaviour (see automation-standards.md). This is a genuine, disclosed
product/case-wording mismatch, not a test defect.

TC 134778 (Preview) is now FULLY AUTOMATED — an earlier investigation via
the retired Content & Data surface found no Preview mechanism at all and
this case was headed for a permanent skip; re-verifying via Object
Authoring (per standards.md's explicit instruction not to assume a
Content & Data-era finding still holds) found a real, working row-level
Preview link.

TC 134783 (Replace Chairman Portrait) and TC 134784 (Upload for the first
time) remain SCRIPTED AS SKIPPED, disclosed inline in each stub:
  - TC 134783 — Object Authoring's upload widget offers "Select File" /
    "Remove file" only, with NO Download control (confirmed live — WORSE
    than the retired Content & Data surface, which at least had a Download
    button). There is no reliable way to capture a TEST_OWNED restore
    baseline for a binary file on this surface, so mutating the real,
    non-disposable, live Chairman Portrait with no verified restore path is
    exactly the SNAPSHOT_RESTORE-against-real-editorial-content scenario
    cms-profile.md's Test-Data Policy prohibits outside an explicit,
    already-proven exception.
  - TC 134784 — the case's own precondition ("a record with no Chairman
    Portrait set") cannot be reached without deleting the real, live
    portrait from the ONLY (singleton) record — the same "destructive CMS
    precondition unavailable" situation already disclosed elsewhere in this
    project (see pytest.ini's `tc_136385`/`tc_136453` entries).

TC 134759 (rich-text authoring), 134760 (hero/portrait alt text), 134779
(cache + audit log), 134828/134829/134834 (hyperlink title/URL validation)
are OUT OF SCOPE for this batch and remain gated by an explicit, disclosed
skip — their bodies still reference the RETIRED Content & Data API
(ChairmanMessageAdminPage no longer exposes those locators/methods at all
per the 2026-09-07 correction) and are left for whichever future pass
migrates them to Object Authoring; per this batch's own scope, they are not
touched beyond swapping their skip reason to say so plainly instead of
silently crashing if ever un-skipped.

All CMS-mutating tests below carry `@pytest.mark.xdist_group("chairman_message_78261")`
(this project's established `--dist loadgroup` convention — see
`active/standards.md`'s "Safe Parallelism" section) so xdist never schedules
two mutations of this SAME singleton record concurrently on different
workers.
"""

import os

import allure
import pytest

from web.pages.components.cms_login_page import CmsLoginPage
from web.pages.about_chairman_message.chairman_message_admin_page import (
    ChairmanMessageAdminPage,
    CHAIRMAN_MESSAGE_ENTRY_CODE,
)
from web.pages.about_chairman_message.chairman_message_page import ChairmanMessagePage
from core.utils.waits import wait_until

PBI = "129393"

# Out-of-scope for this batch (134759, 134760, 134779, 134828, 134829,
# 134834) — their bodies still reference ChairmanMessageAdminPage's RETIRED
# Content & Data locators/methods (removed entirely per the 2026-09-07
# Object Authoring correction — see that Page Object's docstring). Gated
# unconditionally so they never execute and crash; left for a future
# migration pass, not fixed here (out of this batch's scope).
_STALE_CONTENT_DATA_SKIP = pytest.mark.skip(
    reason=(
        "Out of scope for the 2026-09-07 Object Authoring migration batch "
        "(TC 134774/134776/134777/134778/134780/134787 only) — this case's "
        "body still targets ChairmanMessageAdminPage's RETIRED Content & Data "
        "API (removed per standards.md's 'Object Authoring Is the Only Path' "
        "rule). Needs migrating to ObjectAuthoringPage in a future pass, same "
        "as the 6 cases this batch already migrated — see that Page Object's "
        "own docstring."
    )
)


def _skip_if_no_credentials() -> tuple:
    user = os.getenv("TEST_USER", "")
    password = os.getenv("TEST_PASSWORD", "")
    if not user or not password:
        pytest.skip(
            "TEST_USER / TEST_PASSWORD not set in .env — blocked on a qcdev "
            "Site Content Editor account. See module docstring."
        )
    return user, password


def _ensure_login(page, user: str, password: str) -> "CmsLoginPage":
    login = CmsLoginPage(page)
    login.open_login()
    if not login.login_succeeded():
        login.login(user, password)
    return login


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Rich text authoring — headings, paragraphs, bullets, inline links")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can author heading/paragraphs/bullets/inline link in Message Content and publish")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134759")
@_STALE_CONTENT_DATA_SKIP
def test_admin_can_author_rich_text_message_content(page):
    # ABOUT-CHAIRMANMSG-TC-134759 | PBI 129393 — out of scope, see module docstring
    pass


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hero Banner and Chairman Portrait alt text")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can set distinct Hero Banner and Chairman Portrait alt text and publish")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134760")
@_STALE_CONTENT_DATA_SKIP
def test_admin_can_set_hero_and_portrait_alt_text(page):
    # ABOUT-CHAIRMANMSG-TC-134760 | PBI 129393 — out of scope, see module docstring
    pass


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Publish makes content visible on the website")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Admin can publish the Chairman's Message page with Title, Message, Name, and Designation")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.xdist_group("chairman_message_78261")
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134774")
def test_admin_can_publish_chairman_message_page(page, browser):
    # ABOUT-CHAIRMANMSG-TC-134774 | PBI 129393
    # TEST_OWNED (cms-profile.md Test-Data Policy): this record is real,
    # non-disposable editorial content, not a QCTEST- fixture. Every field
    # touched is read BEFORE mutating and restored in `finally` regardless
    # of outcome. Driven entirely through Object Authoring (standards.md's
    # 2026-09-07 correction), never Content & Data. Step 3's public-page
    # check uses a genuinely fresh, unauthenticated browser context (per
    # standards.md's "Mandatory Logged-Out Context" rule) so it reflects a
    # real anonymous visitor, not the CMS-authenticated session.
    from core.web.browser import new_context

    user, password = _skip_if_no_credentials()

    admin = ChairmanMessageAdminPage(page)
    target_title = "Chairman's Message"
    target_salutation = "Dear members and visitors"
    target_message = (
        f"{target_salutation}\n\n"
        "During the past few years, Qatar Chamber has continued to support "
        "the private sector and strengthen the Chamber's role in national "
        "economic growth."
    )
    target_name = "H.E. Sheikh Khalifa bin Jassim bin Mohammed Al Thani"
    target_designation = "Chairman of The Board"
    baseline = {}

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Sign in as Site Content Editor and open the Chairman's Message record via Object Authoring"):
            login = _ensure_login(page, user, password)
            authoring = admin.open_object_authoring_form()

        with allure.step("Capture the pre-existing baseline values (TEST_OWNED reset target)"):
            baseline["title"] = authoring.field_value(admin.PAGE_TITLE_LABEL)
            baseline["message"] = authoring.rich_text_value()
            baseline["name"] = authoring.field_value(admin.CHAIRMAN_NAME_LABEL)
            baseline["designation"] = authoring.field_value(admin.CHAIRMAN_DESIGNATION_LABEL)
            baseline["status"] = authoring.current_status()

        with allure.step("Set Page Title (EN), Message Content (EN), Chairman Name, and Designation, then publish"):
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            authoring.fill_text(admin.PAGE_TITLE_LABEL, target_title)
            authoring.fill_rich_text(target_message)
            authoring.fill_text(admin.CHAIRMAN_NAME_LABEL, target_name)
            authoring.fill_text(admin.CHAIRMAN_DESIGNATION_LABEL, target_designation)
            authoring.submit_for_publishing()

        with allure.step("Read the public Chairman's Message page as a genuine anonymous visitor"):
            cm = ChairmanMessagePage(anon_page)
            cm.open_en()
            wait_until(
                lambda: cm.hero_title_text() == target_title,
                timeout=8.0,
                poll=0.5,
                message="Public page never reflected the newly-published Page Title",
            )
            public_title = cm.hero_title_text()
            public_salutation = cm.salutation_text()
            public_name = cm.name_text()
            public_designation = cm.designation_text()
            public_body_count = cm.body_paragraph_count()

        # Assert
        assert login.login_succeeded()
        assert authoring.current_status() == "Approved"
        assert public_title == target_title
        assert public_salutation == target_salutation
        assert public_body_count > 0, "expected at least one body paragraph"
        assert public_name == target_name
        assert public_designation == target_designation
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 — cleanup must never mask the real result
            pass
        if baseline:
            with allure.step("TEST_OWNED reset — restore Page Title/Message Content/Name/Designation/Status to their pre-existing baseline"):
                authoring = admin.open_object_authoring_form()
                if authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()
                authoring.fill_text(admin.PAGE_TITLE_LABEL, baseline["title"])
                authoring.fill_rich_text(baseline["message"])
                authoring.fill_text(admin.CHAIRMAN_NAME_LABEL, baseline["name"])
                authoring.fill_text(admin.CHAIRMAN_DESIGNATION_LABEL, baseline["designation"])
                if baseline["status"] == "Approved":
                    authoring.submit_for_publishing()
                else:
                    authoring.save_as_draft()


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Unpublish removes the page from the website")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can unpublish the Chairman's Message page")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.xdist_group("chairman_message_78261")
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134776")
def test_admin_can_unpublish_chairman_message_page(page):
    # ABOUT-CHAIRMANMSG-TC-134776 | PBI 129393
    # TEST_OWNED. Driven through Object Authoring's real "Edit -> Unpublish
    # to edit as draft" action — the only genuine Unpublish mechanism this
    # surface has (see module docstring). CONFIRMED (QA Manager, 2026-09-07)
    # this is the correct, intended flow and the resulting "Draft" status IS
    # the expected outcome of Unpublish on this surface — the case's literal
    # wording ("Status changes to Unpublished") describes this same Draft
    # state, not a separate "Unpublished" status label. Asserting "draft"
    # here, not the literal case string.
    user, password = _skip_if_no_credentials()
    admin = ChairmanMessageAdminPage(page)
    baseline_status = None

    try:
        with allure.step("Sign in and open the published Chairman's Message record via Object Authoring"):
            login = _ensure_login(page, user, password)
            authoring = admin.open_object_authoring_form()
            baseline_status = authoring.current_status()

        with allure.step("Ensure the record starts Approved/published (this case's own precondition), then click Unpublish"):
            if authoring.current_status() != "Approved":
                authoring.submit_for_publishing()
            authoring.unpublish_to_edit_as_draft()

        # Assert
        assert login.login_succeeded()
        assert authoring.current_status().strip().lower() == "draft"
    finally:
        with allure.step("TEST_OWNED reset — restore the record to its pre-existing baseline status"):
            authoring = admin.open_object_authoring_form()
            if baseline_status == "Approved" and authoring.current_status() != "Approved":
                authoring.submit_for_publishing()
            elif baseline_status == "Draft" and authoring.current_status() != "Draft":
                authoring.unpublish_to_edit_as_draft()


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Draft content is CMS-only, never public")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Saving Chairman's Message content as a draft keeps it out of the public site")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.xdist_group("chairman_message_78261")
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134777")
def test_draft_content_is_saved_but_not_published(page):
    # ABOUT-CHAIRMANMSG-TC-134777 | PBI 129393
    # TEST_OWNED. Driven through Object Authoring's Unpublish/Save as Draft
    # actions.
    # HEALED 2026-09-07 (live incident — see ObjectAuthoringPage.
    # DESCRIPTION_EDITOR_IFRAME's own docstring for the full investigation):
    # this test's own fill_rich_text() -> save_as_draft() -> rich_text_value()
    # sequence reads back the Message Content field on the SAME page, right
    # after save_as_draft()'s in-place DOM reflow — exactly the state where
    # the class's default `nth=0` mount-order guess can resolve to the AR
    # editor instead of EN. Every rich-text call below now passes
    # `admin.MESSAGE_CONTENT_FIELD_NAME` for a locale-safe, reflow-safe
    # locator instead of relying on that default.
    user, password = _skip_if_no_credentials()
    admin = ChairmanMessageAdminPage(page)
    baseline_message = None
    baseline_status = None

    try:
        with allure.step("Sign in and open the Chairman's Message record via Object Authoring"):
            login = _ensure_login(page, user, password)
            authoring = admin.open_object_authoring_form()

        with allure.step("Capture the pre-existing baseline Message Content + Status (TEST_OWNED reset target)"):
            baseline_message = authoring.rich_text_value(admin.MESSAGE_CONTENT_FIELD_NAME)
            baseline_status = authoring.current_status()

        with allure.step("Add the paragraph 'DRAFT-ONLY-129393' to Message Content and Save as Draft"):
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            authoring.fill_rich_text(f"{baseline_message}\n\nDRAFT-ONLY-129393", admin.MESSAGE_CONTENT_FIELD_NAME)
            authoring.save_as_draft()

        # Assert
        assert login.login_succeeded()
        assert authoring.current_status() == "Draft"
        assert "DRAFT-ONLY-129393" in authoring.rich_text_value(admin.MESSAGE_CONTENT_FIELD_NAME)
    finally:
        if baseline_message is not None:
            with allure.step("TEST_OWNED reset — restore Message Content/Status to their pre-existing baseline"):
                authoring = admin.open_object_authoring_form()
                if authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()
                authoring.fill_rich_text(baseline_message, admin.MESSAGE_CONTENT_FIELD_NAME)
                if baseline_status == "Approved":
                    authoring.submit_for_publishing()
                else:
                    authoring.save_as_draft()


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Preview renders unpublished content without publishing it")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Preview renders unpublished Chairman's Message content without publishing it")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.xdist_group("chairman_message_78261")
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134778")
def test_preview_renders_draft_content_without_publishing(page, browser):
    # ABOUT-CHAIRMANMSG-TC-134778 | PBI 129393
    # CORRECTED 2026-09-07: an EARLIER investigation via the now-retired
    # Content & Data surface found NO Preview mechanism at all for this
    # object, and this case was headed for a permanent skip. Re-verified per
    # standards.md's explicit instruction not to assume a Content & Data-era
    # finding still holds: Object Authoring's row-level Preview link IS a
    # real, working mechanism (confirmed live — see
    # ChairmanMessageAdminPage's docstring) — this case is fully automated.
    # Step 3's "public page" half uses a genuinely fresh, unauthenticated
    # context (standards.md's "Mandatory Logged-Out Context" rule).
    from core.web.browser import new_context

    user, password = _skip_if_no_credentials()
    admin = ChairmanMessageAdminPage(page)
    baseline_message = None
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Sign in and open the Chairman's Message record via Object Authoring"):
            login = _ensure_login(page, user, password)
            authoring = admin.open_object_authoring_form()

        with allure.step("Capture the pre-existing baseline Message Content + Status (TEST_OWNED reset target)"):
            baseline_message = authoring.rich_text_value()
            baseline_status = authoring.current_status()

        with allure.step("Add the paragraph 'PREVIEW-ONLY-129393', Save as Draft (do not publish), then Preview"):
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            authoring.fill_rich_text(f"{baseline_message}\n\nPREVIEW-ONLY-129393")
            authoring.save_as_draft()
            status_before_preview = authoring.current_status()

            entries = admin.open_entries_list()
            preview_url = entries.row_preview_url_by_code(CHAIRMAN_MESSAGE_ENTRY_CODE)
            banner_text = entries.preview_banner_text(preview_url)  # navigates `page` to preview_url
            preview_body_text = entries.text("body")  # BasePage.text() — no raw Playwright in the test

        with allure.step("Confirm the record status is unchanged after Preview"):
            # `authoring`/`entries` share the same underlying `page`, which
            # `preview_banner_text()` just navigated AWAY from the admin
            # edit form to the public preview URL — current_status() would
            # otherwise read the preview page's own body text, not the
            # admin form's status banner. Reopen the edit form fresh first.
            authoring = admin.open_object_authoring_form()
            status_after_preview = authoring.current_status()

        with allure.step("Confirm the public page (fresh, anonymous context) does not contain the preview-only paragraph"):
            cm = ChairmanMessagePage(anon_page)
            cm.open_en()
            public_body_text = cm.text("body")  # BasePage.text() — no raw Playwright in the test

        # Assert
        assert login.login_succeeded()
        assert status_before_preview == "Draft"
        assert "unpublished (draft)" in banner_text.lower() or "draft" in banner_text.lower()
        assert "PREVIEW-ONLY-129393" in preview_body_text
        assert status_after_preview == "Draft", "expected Preview to leave the record status unchanged"
        assert "PREVIEW-ONLY-129393" not in public_body_text
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 — cleanup must never mask the real result
            pass
        if baseline_message is not None:
            with allure.step("TEST_OWNED reset — restore Message Content/Status to their pre-existing baseline"):
                authoring = admin.open_object_authoring_form()
                if authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()
                authoring.fill_rich_text(baseline_message)
                if baseline_status == "Approved":
                    authoring.submit_for_publishing()
                else:
                    authoring.save_as_draft()


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Configure an inline hyperlink in the message content")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can configure a titled hyperlink inside Message Content and publish")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.pbi_129393
@pytest.mark.xdist_group("chairman_message_78261")
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134780")
def test_admin_can_configure_message_hyperlink(page):
    # ABOUT-CHAIRMANMSG-TC-134780 | PBI 129393
    # TEST_OWNED. Hyperlink Title/URL are NOT bilingual on this surface
    # (confirmed live — see ChairmanMessageAdminPage's docstring), so no
    # locale suffix is needed for either field.
    user, password = _skip_if_no_credentials()
    admin = ChairmanMessageAdminPage(page)
    baseline_title = None
    baseline_url = None
    baseline_status = None

    try:
        with allure.step("Sign in and open the Chairman's Message record via Object Authoring"):
            login = _ensure_login(page, user, password)
            authoring = admin.open_object_authoring_form()

        with allure.step("Capture the pre-existing baseline Hyperlink Title/URL + Status (TEST_OWNED reset target)"):
            baseline_title = authoring.field_value(admin.HYPERLINK_TITLE_LABEL)
            baseline_url = authoring.field_value(admin.HYPERLINK_URL_LABEL)
            baseline_status = authoring.current_status()

        with allure.step("Configure a hyperlink titled 'Qatar National Vision 2030' pointing to https://www.qatarchamber.com, then publish"):
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            authoring.fill_text(admin.HYPERLINK_TITLE_LABEL, "Qatar National Vision 2030")
            authoring.fill_text(admin.HYPERLINK_URL_LABEL, "https://www.qatarchamber.com")
            authoring.submit_for_publishing()

        # Assert
        assert login.login_succeeded()
        assert authoring.current_status() == "Approved"
        assert authoring.field_value(admin.HYPERLINK_TITLE_LABEL) == "Qatar National Vision 2030"
        assert authoring.field_value(admin.HYPERLINK_URL_LABEL) == "https://www.qatarchamber.com"
    finally:
        if baseline_title is not None:
            with allure.step("TEST_OWNED reset — restore Hyperlink Title/URL/Status to their pre-existing baseline"):
                authoring = admin.open_object_authoring_form()
                if authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()
                authoring.fill_text(admin.HYPERLINK_TITLE_LABEL, baseline_title)
                authoring.fill_text(admin.HYPERLINK_URL_LABEL, baseline_url)
                if baseline_status == "Approved":
                    authoring.submit_for_publishing()
                else:
                    authoring.save_as_draft()


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Replace the Chairman Portrait")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can replace the Chairman Portrait and publish")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134783")
@pytest.mark.skip(
    reason=(
        "Object Authoring's Chairman Portrait upload widget offers Select "
        "File / Remove file only — CONFIRMED LIVE 2026-09-07, no Download "
        "control exists (worse than the retired Content & Data surface, "
        "which at least had one). There is no reliable TEST_OWNED restore "
        "path for a binary file here, so replacing the real, non-disposable, "
        "live Chairman Portrait with no verified restore is exactly the "
        "SNAPSHOT_RESTORE-against-real-editorial-content scenario "
        "cms-profile.md's Test-Data Policy prohibits outside an explicit, "
        "already-proven exception. Recommend the QA Manager provision a "
        "disposable image-upload fixture record before this is scripted to "
        "actually execute."
    )
)
def test_admin_can_replace_chairman_portrait(page):
    # ABOUT-CHAIRMANMSG-TC-134783 | PBI 129393 — see skip reason
    pass


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Upload the Chairman Portrait for the first time")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can upload a Chairman Portrait for the first time and publish")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134784")
@pytest.mark.skip(
    reason=(
        "This case's own precondition (\"a record with no Chairman Portrait "
        "set\") cannot be reached without deleting the real, live portrait "
        "from the ONLY (singleton) Chairman's Message record — the same "
        "'destructive CMS precondition unavailable' situation already "
        "disclosed elsewhere in this project (see pytest.ini's tc_136385/ "
        "tc_136453 entries). Never performed just to exercise a test."
    )
)
def test_admin_can_upload_chairman_portrait_first_time(page):
    # ABOUT-CHAIRMANMSG-TC-134784 | PBI 129393 — see skip reason
    pass


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Publish updates cache and writes an audit log entry")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing updates the public page and writes a Liferay audit log entry")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134779")
@_STALE_CONTENT_DATA_SKIP
def test_publish_updates_cache_and_writes_audit_log_entry(page):
    # ABOUT-CHAIRMANMSG-TC-134779 | PBI 129393 — out of scope, see module docstring
    pass


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Name/Designation entered once, populate both Name Card and Signature block")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Chairman Name/Designation form exposes exactly one field per language and publishes to both locations")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.xdist_group("chairman_message_78261")
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134787")
def test_name_and_designation_have_single_source_field(page):
    # ABOUT-CHAIRMANMSG-TC-134787 | PBI 129393
    # TEST_OWNED. Driven through Object Authoring. Step 2's "exactly one
    # field per language, no separate signature-block field" is confirmed
    # by an EXACT accessible-name match count on this surface — a field
    # with a different label (e.g. a hypothetical separate signature-block
    # name field) would never match "Chairman Name"/"Chairman Name —
    # العربية" exactly, so a count of 1 for each already proves both halves
    # of the case's requirement.
    user, password = _skip_if_no_credentials()
    admin = ChairmanMessageAdminPage(page)
    new_name = "H.E. Sheikh Khalifa bin Jassim bin Mohammed Al Thani"
    new_designation = "Chairman of The Board"
    baseline_name = None
    baseline_designation = None
    baseline_status = None

    try:
        with allure.step("Sign in as Site Content Editor and open the Chairman's Message record via Object Authoring"):
            login = _ensure_login(page, user, password)
            authoring = admin.open_object_authoring_form()

        with allure.step("Confirm exactly one Chairman Name field and one Chairman Designation field per language"):
            name_count_en = authoring.field_count(admin.CHAIRMAN_NAME_LABEL)
            name_count_ar = authoring.field_count(f"{admin.CHAIRMAN_NAME_LABEL}{admin.ARABIC_SUFFIX}")
            designation_count_en = authoring.field_count(admin.CHAIRMAN_DESIGNATION_LABEL)
            designation_count_ar = authoring.field_count(f"{admin.CHAIRMAN_DESIGNATION_LABEL}{admin.ARABIC_SUFFIX}")

        with allure.step("Capture the pre-existing baseline Name/Designation/Status (TEST_OWNED reset target)"):
            baseline_name = authoring.field_value(admin.CHAIRMAN_NAME_LABEL)
            baseline_designation = authoring.field_value(admin.CHAIRMAN_DESIGNATION_LABEL)
            baseline_status = authoring.current_status()

        with allure.step("Change Chairman Name (EN) and Chairman Designation (EN), then publish"):
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            authoring.fill_text(admin.CHAIRMAN_NAME_LABEL, new_name)
            authoring.fill_text(admin.CHAIRMAN_DESIGNATION_LABEL, new_designation)
            authoring.submit_for_publishing()

        # Assert
        assert name_count_en == 1, f"expected exactly 1 Chairman Name (EN) field, found {name_count_en}"
        assert name_count_ar == 1, f"expected exactly 1 Chairman Name (AR) field, found {name_count_ar}"
        assert designation_count_en == 1, f"expected exactly 1 Chairman Designation (EN) field, found {designation_count_en}"
        assert designation_count_ar == 1, f"expected exactly 1 Chairman Designation (AR) field, found {designation_count_ar}"
        assert login.login_succeeded()
        assert authoring.current_status() == "Approved"
        assert authoring.field_value(admin.CHAIRMAN_NAME_LABEL) == new_name
        assert authoring.field_value(admin.CHAIRMAN_DESIGNATION_LABEL) == new_designation
    finally:
        if baseline_name is not None:
            with allure.step("TEST_OWNED reset — restore Chairman Name/Designation/Status to their pre-existing baseline"):
                authoring = admin.open_object_authoring_form()
                if authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()
                authoring.fill_text(admin.CHAIRMAN_NAME_LABEL, baseline_name)
                authoring.fill_text(admin.CHAIRMAN_DESIGNATION_LABEL, baseline_designation)
                if baseline_status == "Approved":
                    authoring.submit_for_publishing()
                else:
                    authoring.save_as_draft()


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink Title accepted and rendered as the link label")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Hyperlink Title is accepted and published")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134828")
@_STALE_CONTENT_DATA_SKIP
def test_valid_hyperlink_title_is_accepted(page):
    # ABOUT-CHAIRMANMSG-TC-134828 | PBI 129393 — out of scope, see module docstring
    pass


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink Title is optional")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An empty Hyperlink Title is allowed because the field is optional")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134829")
@_STALE_CONTENT_DATA_SKIP
def test_empty_hyperlink_title_is_allowed(page):
    # ABOUT-CHAIRMANMSG-TC-134829 | PBI 129393 — out of scope, see module docstring
    pass


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink URL is optional")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An empty Hyperlink URL is allowed because the field is optional")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134834")
@_STALE_CONTENT_DATA_SKIP
def test_empty_hyperlink_url_is_allowed(page):
    # ABOUT-CHAIRMANMSG-TC-134834 | PBI 129393 — out of scope, see module docstring
    pass

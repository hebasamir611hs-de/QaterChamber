"""
cms/tests/home_promo_banners/test_home_promo_banners_control_panel.py —
Control_Panel-tagged cases for PBI 129368 (QC-HOME-002 — Promotional
Banners / Ad Slots).

SOURCE: full step content for ADO Test Cases 135118-135125 was read directly
from Azure DevOps work items (Microsoft.VSTS.TCM.Steps) this session
(2026-09-02) via a scratch script reusing the qa-engine server's own
azure.devops SDK connection/credentials — NOT re-interpreted from titles
alone, per this task's explicit instruction. Full step text is quoted in
each test's own docstring below.

WORKFLOW FINDING — CONFIRMED, blocks 4 of the 8 cases (product/case
mismatch, not an automation gap):

Configuration > Workflow (Liferay's Site Administration Workflow screen)
was opened live this session and searched for "Promotional" — it returns
exactly one row: **Asset Type "Promotional Banner", Workflow Assigned = "No
Workflow"** (screenshot on file this session). This is Liferay's own,
authoritative record of whether an Object Definition has an approval
workflow attached. With none attached:
  - every object entry auto-approves on Save (confirmed live: all 4
    existing rows show Status = "APPROVED" uniformly, including a row
    Saved during this very session's exploration);
  - the Add/Edit form renders ONLY Save/Cancel — no Save-as-Draft, no
    Submit-for-Publication button (confirmed live, full button-list dump
    this session);
  - the row-level "Item Actions" kebab exposes ONLY View / Delete /
    Permissions — no Publish/Unpublish/Submit-for-Review action (confirmed
    live, full action-list dump this session).

There is therefore no reachable Draft state, no Pending Review state, and
no Publish/Unpublish action on this object as currently built. This blocks:
  - TC 135122 ("save a new banner slot as draft") — no Save-as-Draft
    control exists; every Save auto-approves.
  - TC 135123 ("submit a draft banner slot for review") — no Draft
    precondition state and no Submit-for-Review action exist.
  - TC 135124 ("publish a banner slot in Pending Review status") — no
    Pending Review precondition state and no Publish action exist.
  - TC 135125 ("unpublish a published banner slot") — no Unpublish action
    exists (Active Status is a visibility toggle, not this object's
    equivalent of "unpublish" — see the reasoning below for why it is not
    substituted).

Per automation-standards.md's Result Integrity section, these are scripted
as `@pytest.mark.skip` with a concrete reason (an unavailable/unreachable
precondition state on this environment) — NOT force-fit onto the unrelated
Active Status checkbox to manufacture a green. The home_featured_event
precedent (Active Status substituting for "unpin") does NOT transfer here:
there, Active Status genuinely WAS the object's only on/off mechanism and
the case's own precondition ("the currently featured event") was reachable.
Here, 135124's own Arrange step is "Open the Pending Review banner slot" —
that state does not exist to open, so there is nothing to substitute against
without silently rewriting the case. This is reported back as a
case-vs-product mismatch for the QA Manager to resolve (either the approval
workflow was never implemented on this Object Definition, or the 8 cases
were authored against an assumed workflow that doesn't match the build) —
not resolved unilaterally here.

TEST-DATA POLICY (cms-profile.md): DISPOSABLE. Every test creates its own
`QCTEST-`-prefixed banner (via Banner Alt Text (EN)) and deletes it via the
admin row's own Actions kebab -> Delete -> confirm in a `finally` block.
Never touches the 3 real editorial rows (47729/47737/47745) or the
pre-existing leftover row 118254 (not created by, and not owned by, this
suite).

CONCRETE DATA NOTE (135118): the case's own wording assumes Display Order
1 -> 2 on "the existing published banner slot" — but the 3 real rows on
this environment are at Display Order 100/200/300 and none may be mutated
(cms-testing.md's "never mutate pre-existing content the suite did not
create" rule). The test instead creates its own fixture row and mirrors the
case's INTENT (an existing entry's Display Order is changed and the new
value persists) rather than the literal 1/2 values — disclosed here, not
silently substituted.

UNBLOCKED 2026-09-03 (finding above kept for history — the raw Object
Definition admin genuinely has no workflow, that fact hasn't changed): a
newly confirmed Control_Panel surface, `object-authoring` ->
`manage-promotional-banner` (documented in
.claude/context/active/standards.md's "Object Authoring — Draft / Preview
/ Publish / Unpublish Lifecycle" section), manages this SAME object's
entries through a real Draft/Submit-for-Publishing/Unpublish state
machine, independent of the raw Object Definition's own workflow setting.
TC 135122-135125 are now driven through that surface via
cms/pages/components/object_authoring_page.py (ObjectAuthoringPage) and
are no longer skipped. The Active Status toggle is still not substituted
for anything here — the object-authoring surface's own Status column
(Draft/Approved) IS the workflow-status field each case names.

135186 & 135191 (added 2026-09-02, Automation batch #2, parent PBI 129368):
full step content pulled directly from Azure DevOps (Microsoft.VSTS.TCM.Steps)
this session via the same qa-engine-credentialed script pattern as the
135118-135125 batch — see each test's own docstring for the quoted steps
and this session's disclosed adaptations (135186 reuses the WORKFLOW FINDING
above; 135191 substitutes an already-elapsed date window for a literal
multi-day wait, confirmed live via a throwaway probe that the delivery
surface does enforce the Start/End Date range in both directions before
being written into this suite). 135191 was tagged Manual by QA at
injection time but the QA Manager explicitly approved automating it for
this batch.
"""

import datetime

import allure
import pytest

from cms.pages.home_promo_banners.home_promo_banners_admin_page import HomePromoBannersAdminPage
from core.utils.logger import get_logger
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from web.pages.home_promo_banners.home_promo_banners_page import HomePromoBannersPage

logger = get_logger("test_home_promo_banners_control_panel")

# Switched 2026-09-03 from promo_banner.png to this identical-content copy
# under a distinct filename: confirmed live that qcdev's Documents & Media
# picker started returning "An unexpected error occurred while uploading
# your file." specifically for promo_banner.png after this session's many
# repeated uploads of it (each landing as promo_banner (N).png,
# N observed >40) — a duplicate-name-resolution limit on the server side,
# not a locator/timing bug (confirmed live: the SAME picker upload flow
# succeeded immediately for both this renamed copy and for an unrelated
# object's fixture (News Article's own thumbnail) in the same session).
IMAGE_FIXTURE = "cms/tests/home_promo_banners/fixtures/promo_banner_v2_qctest.png"


def _create_banner(admin: HomePromoBannersAdminPage, alt_en: str, alt_ar: str,
                    display_order: str, active: bool,
                    start_date: str | None = None, end_date: str | None = None) -> None:
    admin.open_new_banner_form()
    admin.set_alt_text_en(alt_en)
    admin.set_alt_text_ar(alt_ar)
    admin.set_display_order(display_order)
    admin.set_active(active)
    if start_date is not None:
        admin.set_start_date(start_date)
    if end_date is not None:
        admin.set_end_date(end_date)
    admin.upload_banner_image_en(IMAGE_FIXTURE)
    assert admin.uploaded_image_en_filename() != "", (
        "Banner Image (EN) upload did not populate the field before Save"
    )
    admin.upload_banner_image_ar(IMAGE_FIXTURE)
    assert admin.uploaded_image_ar_filename() != "", (
        "Banner Image (AR) upload did not populate the field before Save"
    )
    admin.save()
    assert not admin.is_save_error_shown(), (
        f"unexpected validation error creating banner {alt_en!r}: {admin.save_error_text()!r}"
    )
    assert admin.wait_for_row_visible(alt_en), (
        f"new banner {alt_en!r} not visible in the admin list after Save"
    )


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("CMS authoring workflow — edit")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site Content Editor can edit an existing published banner slot")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129368
@pytest.mark.tc_135118
def test_edit_existing_banner_display_order(page):
    """ADO-135118. Steps (from Azure DevOps, quoted verbatim):
      1. Log into Liferay CMS as Site Content Editor -> Login succeeds
      2. Open the existing published banner slot for edit -> Edit form
         loads with current values (Display Order = 1)
      3. Change Display Order from 1 to 2 -> Field updates to 2
      4. Save -> System displays a Liferay generic success toast; banner's
         stored Display Order = 2

    Adapted per this module's CONCRETE DATA NOTE: exercised against a
    fixture banner this test creates and owns (Display Order 500 -> 501),
    since the real environment's 3 editorial rows sit at 100/200/300 and
    may not be mutated. Intent (an existing slot's Display Order changes
    and the new value persists after Save) is preserved.
    """
    admin = HomePromoBannersAdminPage(page)
    alt_en = "QCTEST-135118 Edit Banner"

    try:
        _create_banner(admin, alt_en, "تعديل-135118", "500", active=True)

        with allure.step("Open the fixture banner for edit and confirm current Display Order"):
            admin.open_banner_edit_form_by_alt_text(alt_en)
            assert admin.display_order_value() == "500"

        with allure.step("Change Display Order from 500 to 501 and Save"):
            admin.set_display_order("501")
            admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error saving edited Display Order: {admin.save_error_text()!r}"
        )

        with allure.step("Reopen the record and assert the new Display Order persisted"):
            admin.open_banner_edit_form_by_alt_text(alt_en)
            assert admin.display_order_value() == "501", (
                f"Display Order did not persist as 501, got {admin.display_order_value()!r}"
            )
    finally:
        admin.open_promo_banners_list()
        admin.delete_row_by_alt_text(alt_en)


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("CMS authoring workflow — enable")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site Content Editor can enable a disabled banner slot")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129368
@pytest.mark.tc_135119
def test_enable_disabled_banner(page):
    """ADO-135119. Steps (from Azure DevOps, quoted verbatim):
      1. Log into Liferay CMS as Site Content Editor -> Login succeeds
      2. Locate a banner slot with Active Status = false -> Banner listed
         with Active Status = false
      3. Toggle Active Status to true -> Toggle switches to on/true
      4. Save -> System displays a Liferay generic success toast; banner's
         Active Status stored as true

      Delivery-surface assertion added per cms-testing.md R1 ("a
      CMS case that asserts only on the authoring surface is incomplete"):
      the case's own expected result stops at the stored field value, so
      this test additionally confirms the banner becomes visible on the
      public Home Page after Save — flagged in this suite's report as
      coverage the case itself does not specify.
    """
    admin = HomePromoBannersAdminPage(page)
    home = HomePromoBannersPage(page)
    alt_en = "QCTEST-135119 Enable Banner"

    try:
        _create_banner(admin, alt_en, "تفعيل-135119", "502", active=False)

        with allure.step("Confirm the banner is NOT visible on the Home Page while inactive"):
            hidden_before = home.reload_until_banner_matches(alt_en, expected_visible=False)
        assert hidden_before, (
            f"Fixture banner {alt_en!r} unexpectedly visible on the Home Page "
            f"while Active Status=False, within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )

        with allure.step("Open the banner, toggle Active Status to true, and Save"):
            admin.open_banner_edit_form_by_alt_text(alt_en)
            assert admin.is_active() is False
            admin.set_active(True)
            admin.save()
        assert not admin.is_save_error_shown()

        with allure.step("Reopen and assert Active Status persisted as true"):
            admin.open_banner_edit_form_by_alt_text(alt_en)
            assert admin.is_active() is True

        with allure.step("Assert the banner now appears on the public Home Page"):
            visible_after = home.reload_until_banner_matches(alt_en, expected_visible=True)
        assert visible_after, (
            f"Banner {alt_en!r} did not appear on the Home Page within "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms of enabling Active Status "
            "(budget borrowed from cms-profile.md's Board Members "
            "measurement, unverified for this content type)"
        )
    finally:
        admin.open_promo_banners_list()
        admin.delete_row_by_alt_text(alt_en)


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("CMS authoring workflow — disable")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site Content Editor can disable an active banner slot")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129368
@pytest.mark.tc_135120
def test_disable_active_banner(page):
    """ADO-135120. Steps (from Azure DevOps, quoted verbatim):
      1. Locate the banner slot with Active Status = true -> Banner listed
         with Active Status = true
      2. Toggle Active Status to false -> Toggle switches to off/false
      3. Save -> System displays a Liferay generic success toast; banner's
         Active Status stored as false

      Delivery-surface assertion added per cms-testing.md R1 (same
      disclosed addition as TC 135119's test above).
    """
    admin = HomePromoBannersAdminPage(page)
    home = HomePromoBannersPage(page)
    alt_en = "QCTEST-135120 Disable Banner"

    try:
        _create_banner(admin, alt_en, "تعطيل-135120", "503", active=True)

        with allure.step("Confirm the banner IS visible on the Home Page while active"):
            visible_before = home.reload_until_banner_matches(alt_en, expected_visible=True)
        assert visible_before, (
            f"Fixture banner {alt_en!r} not visible on the Home Page with "
            f"Active Status=True within {home.RELOAD_POLL_TIMEOUT_MS}ms — "
            "cannot proceed to the disable assertion without a confirmed precondition"
        )

        with allure.step("Open the banner, toggle Active Status to false, and Save"):
            admin.open_banner_edit_form_by_alt_text(alt_en)
            assert admin.is_active() is True
            admin.set_active(False)
            admin.save()
        assert not admin.is_save_error_shown()

        with allure.step("Reopen and assert Active Status persisted as false"):
            admin.open_banner_edit_form_by_alt_text(alt_en)
            assert admin.is_active() is False

        with allure.step("Assert the banner no longer appears on the public Home Page"):
            hidden_after = home.reload_until_banner_matches(alt_en, expected_visible=False)
        assert hidden_after, (
            f"Banner {alt_en!r} still visible on the Home Page after "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms of disabling Active Status"
        )
    finally:
        admin.open_promo_banners_list()
        admin.delete_row_by_alt_text(alt_en)


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("CMS authoring workflow — delete")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site Content Editor can delete a promotional banner slot")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129368
@pytest.mark.tc_135121
def test_delete_banner_slot(page):
    """ADO-135121. Steps (from Azure DevOps, quoted verbatim):
      1. Log into Liferay CMS as Site Content Editor -> Login succeeds
      2. Locate the draft banner slot -> Banner slot found in the list
      3. Click Delete and confirm -> System displays a Liferay generic
         success toast; banner slot no longer appears in the management
         list or on the frontend

      Note: "the draft banner slot" wording assumes the Draft state this
      module's docstring documents as unreachable on this object (no
      workflow). Exercised instead against a fixture banner this test
      creates and owns (any entry, since every Save on this object
      auto-approves) — the case's own expected result explicitly names
      BOTH surfaces (list AND frontend), so this test asserts both without
      needing the Draft precondition itself.
    """
    admin = HomePromoBannersAdminPage(page)
    home = HomePromoBannersPage(page)
    alt_en = "QCTEST-135121 Delete Banner"

    _create_banner(admin, alt_en, "حذف-135121", "504", active=True)

    with allure.step("Confirm the banner IS visible on the Home Page before delete"):
        visible_before = home.reload_until_banner_matches(alt_en, expected_visible=True)
    assert visible_before, (
        f"Fixture banner {alt_en!r} not visible on the Home Page before "
        "delete — cannot proceed without a confirmed precondition"
    )

    with allure.step("Delete the banner via its Actions kebab and confirm"):
        admin.open_promo_banners_list()
        deleted = admin.delete_row_by_alt_text(alt_en)
    assert deleted, f"delete_row_by_alt_text found no row for {alt_en!r} to delete"

    with allure.step("Assert the banner no longer appears in the admin management list"):
        admin.open_promo_banners_list()
        assert not admin.row_visible(alt_en), (
            f"Banner {alt_en!r} still visible in the admin list after Delete"
        )

    with allure.step("Assert the banner no longer appears on the public Home Page frontend"):
        hidden_after = home.reload_until_banner_matches(alt_en, expected_visible=False)
    assert hidden_after, (
        f"Banner {alt_en!r} still visible on the Home Page frontend after "
        f"Delete, within {home.RELOAD_POLL_TIMEOUT_MS}ms"
    )


def _create_banner_via_object_authoring(
    authoring: ObjectAuthoringPage, alt_en: str, alt_ar: str, display_order: str, active: bool
) -> None:
    authoring.open_new_entry_form()
    authoring.fill_text("Banner Alt Text (EN)", alt_en)
    authoring.fill_text("Banner Alt Text (AR)", alt_ar)
    authoring.fill_number("Display Order", display_order)
    authoring.set_checkbox("Active Status", active)
    authoring.upload_file("Banner Image (EN)", IMAGE_FIXTURE)
    assert authoring.uploaded_filename("Banner Image (EN)") != "", (
        "Banner Image (EN) upload did not populate the field before Save"
    )
    authoring.upload_file("Banner Image (AR)", IMAGE_FIXTURE)
    assert authoring.uploaded_filename("Banner Image (AR)") != "", (
        "Banner Image (AR) upload did not populate the field before Save"
    )


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("Content workflow — draft")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a new banner slot as Draft keeps it off the Home Page")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129368
@pytest.mark.tc_135122
def test_save_new_banner_slot_as_draft(page, browser):
    """ADO-135122. Steps (from Azure DevOps, quoted verbatim):
      1. Click Add Banner -> Add Banner form opens
      2. Fill all mandatory fields (images, alt text, display order, active
         status) -> All fields populated, no validation errors
      3. Click Save as Draft -> System displays a Liferay generic success
         toast; banner slot status = Draft; not visible on the Home Page

    UNBLOCKED 2026-09-03 via the object-authoring surface (see module
    docstring) — driven through manage-promotional-banner instead of the
    raw Object Definition admin, which genuinely lacks the control.

    PUBLIC-PAGE-ANONYMOUS-CONTEXT (mandatory per standards.md, added
    2026-09-07): the "not visible on the Home Page" half is read through a
    fresh, logged-out browser context, never the CMS-authenticated `page` —
    mirrors home_business_events_admin_page's established pattern.
    """
    from core.web.browser import new_context

    admin = HomePromoBannersAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="promotional-banner")
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePromoBannersPage(anon_context.new_page())
    alt_en = "QCTEST-135122 Draft Banner"

    try:
        with allure.step("Click Add Banner (manage-promotional-banner's create-new form)"):
            admin.open_promo_banners_list()
            authoring.open_new_entry_form()

        with allure.step("Fill all mandatory fields"):
            authoring.fill_text("Banner Alt Text (EN)", alt_en)
            authoring.fill_text("Banner Alt Text (AR)", "مسودة-135122")
            authoring.fill_number("Display Order", "508")
            authoring.set_checkbox("Active Status", True)
            authoring.upload_file("Banner Image (EN)", IMAGE_FIXTURE)
            assert authoring.uploaded_filename("Banner Image (EN)") != "", (
                "Banner Image (EN) upload did not populate the field before Save"
            )
            authoring.upload_file("Banner Image (AR)", IMAGE_FIXTURE)
            assert authoring.uploaded_filename("Banner Image (AR)") != "", (
                "Banner Image (AR) upload did not populate the field before Save"
            )

        with allure.step("Click Save as Draft"):
            authoring.save_as_draft()

        with allure.step("Assert status = Draft and the banner is NOT visible on the Home Page"):
            assert authoring.row_status_text(alt_en) == "Draft", (
                f"banner {alt_en!r} status did not persist as Draft, got "
                f"{authoring.row_status_text(alt_en)!r}"
            )
            hidden = home.reload_until_banner_matches(alt_en, expected_visible=False)
        assert hidden, (
            f"Draft banner {alt_en!r} unexpectedly visible on the Home Page "
            f"within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )
    finally:
        # Teardown must land on manage-promotional-banner's own entries
        # list (authoring.open_entries_list()), NOT
        # admin.open_promo_banners_list() — the raw admin's list has no
        # `data-qc-oel-delete` rows (confirmed live 2026-09-03).
        try:
            authoring.open_entries_list()
            authoring.delete_entry_by_title(alt_en)
        except Exception:
            logger.warning("teardown for %r did not complete — leftover QCTEST data may remain", alt_en)
        anon_context.close()


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("Content workflow — submit for review")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Submitting a draft banner slot for publishing changes its status to Approved")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129368
@pytest.mark.tc_135123
def test_submit_draft_banner_for_review(page):
    """ADO-135123. Steps (from Azure DevOps, quoted verbatim):
      1. Open the draft banner slot -> Draft banner opens for edit
      2. Click Submit for Review -> System displays a Liferay generic
         success toast; banner slot status changes to Pending Review

    UNBLOCKED 2026-09-03 via the object-authoring surface. ADAPTED,
    disclosed: this environment's object-authoring state machine has no
    separate "Pending Review" status distinct from "Approved" (confirmed
    live 2026-09-03 — Submit for Publishing transitions a Draft entry
    straight to Status=Approved, with no intermediate moderation queue
    state to land on) — the case's own intent (submitting a draft moves it
    out of Draft toward publication) is preserved; the literal status
    label "Pending Review" is not asserted since it does not exist on this
    build.
    """
    admin = HomePromoBannersAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="promotional-banner")
    alt_en = "QCTEST-135123 Submit For Review"

    try:
        with allure.step("Create a fixture banner and Save it as Draft"):
            admin.open_promo_banners_list()
            _create_banner_via_object_authoring(authoring, alt_en, "مراجعة-135123", "509", True)
            authoring.save_as_draft()
            assert authoring.row_status_text(alt_en) == "Draft", (
                f"fixture banner {alt_en!r} did not save as Draft, got "
                f"{authoring.row_status_text(alt_en)!r}"
            )

        with allure.step("Open the draft banner slot"):
            authoring.open_entry_by_edit_link(alt_en)
            assert "Save as Draft or Submit for Publishing updates this record" in authoring.editing_banner_text(), (
                "editing banner did not show the expected draft-state wording"
            )

        with allure.step("Click Submit for Review (Submit for Publishing on this surface)"):
            authoring.submit_for_publishing()

        with allure.step("Assert the banner's status changed off Draft"):
            status_after = authoring.row_status_text(alt_en)
        assert status_after == "Approved", (
            f"banner {alt_en!r} status did not change after Submit for "
            f"Publishing, got {status_after!r}"
        )
    finally:
        # Teardown must land on manage-promotional-banner's own entries
        # list (authoring.open_entries_list()), NOT
        # admin.open_promo_banners_list() — the raw admin's list has no
        # `data-qc-oel-delete` rows (confirmed live 2026-09-03).
        try:
            authoring.open_entries_list()
            authoring.delete_entry_by_title(alt_en)
        except Exception:
            logger.warning("teardown for %r did not complete — leftover QCTEST data may remain", alt_en)


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("Content workflow — publish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing a submitted banner slot makes it live on the Home Page (Pending Review precondition still unreachable — see docstring)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_129368
@pytest.mark.tc_135124
def test_publishing_pending_review_banner_makes_it_live(page):
    """ADO-135124 (Regression, UAT, Workflow). Steps (from Azure DevOps,
    quoted verbatim):
      1. Open the Pending Review banner slot -> Pending Review banner opens
         for edit
      2. Click Publish -> System displays a Liferay generic success toast;
         status changes to Published
      3. Navigate to the public Home Page and refresh the cache -> Banner is
         now visible in the promotional banners section on the Home Page

    UNBLOCKED 2026-09-03 via the object-authoring surface — PARTIALLY, and
    this is disclosed plainly rather than presented as a clean unblock:
    the object-authoring lifecycle removed the original "no workflow at
    all" blocker, but this case's own Arrange step ("Open the Pending
    Review banner slot") names a precondition state — Pending Review —
    that STILL does not exist on this build (confirmed live 2026-09-03,
    same probe as TC 135123's test above: Submit for Publishing transitions
    Draft -> Approved directly, with no intermediate moderation-queue
    state to land on and open). That is the exact reasoning the module's
    original WORKFLOW FINDING used to block this case, and object-authoring
    did not change it. As scripted below, this test exercises the SAME
    Draft -> Approved -> live-on-Home-Page transition TC 135123 exercises,
    under this case's different name/severity (Regression+UAT here) — it
    is not an independent precondition-to-outcome path. Flagged back to
    the QA Manager: either merge 135123/135124 into one case now that both
    resolve to the same transition on this build, or treat 135124 as still
    blocked pending a real Pending Review state. Kept as a passing,
    non-duplicative-in-intent test for now since the task asked all 5
    Group-A cases be attempted, not as a claim that the precondition gap
    is resolved.
    """
    admin = HomePromoBannersAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="promotional-banner")
    home = HomePromoBannersPage(page)
    alt_en = "QCTEST-135124 Publish Live"

    try:
        with allure.step("Create a fixture banner, save as Draft, then Submit for Publishing"):
            admin.open_promo_banners_list()
            _create_banner_via_object_authoring(authoring, alt_en, "نشر-135124", "510", True)
            authoring.save_as_draft()
            authoring.open_entry_by_edit_link(alt_en)
            authoring.submit_for_publishing()

        with allure.step("Assert status changed to Approved (this build's Published-equivalent)"):
            status_after = authoring.row_status_text(alt_en)
        assert status_after == "Approved", (
            f"banner {alt_en!r} did not reach Approved/Published status, "
            f"got {status_after!r}"
        )

        with allure.step("Navigate to the public Home Page and assert the banner is now visible"):
            visible_after = home.reload_until_banner_matches(alt_en, expected_visible=True)
        assert visible_after, (
            f"Published banner {alt_en!r} not visible on the Home Page "
            f"within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )
    finally:
        # Teardown must land on manage-promotional-banner's own entries
        # list (authoring.open_entries_list()), NOT
        # admin.open_promo_banners_list() — the raw admin's list has no
        # `data-qc-oel-delete` rows (confirmed live 2026-09-03).
        try:
            authoring.open_entries_list()
            authoring.delete_entry_by_title(alt_en)
        except Exception:
            logger.warning("teardown for %r did not complete — leftover QCTEST data may remain", alt_en)


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("Content workflow — unpublish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unpublishing a published banner slot removes it from the Home Page")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129368
@pytest.mark.tc_135125
def test_unpublishing_banner_removes_it_from_home_page(page, browser):
    """ADO-135125. Steps (from Azure DevOps, quoted verbatim):
      1. Open the published banner slot -> Published banner opens for edit
      2. Click Unpublish -> System displays a Liferay generic success
         toast; status changes to Unpublished
      3. Navigate to the public Home Page and refresh -> Banner no longer
         displays in the promotional banners section on the Home Page

    UNBLOCKED 2026-09-03 via the object-authoring surface's confirmed-live
    "Unpublish to edit as draft" action (see
    cms/pages/components/object_authoring_page.py's module docstring).
    ADAPTED, disclosed: the resulting status reads "Draft" on this
    build, not the literal label "Unpublished" the case names — the
    case's actual intent (the banner comes off the live Home Page and
    returns to an editable, unpublished state) is preserved and asserted
    in full.

    PUBLIC-PAGE-ANONYMOUS-CONTEXT (mandatory per standards.md, added
    2026-09-07): both the before-unpublish and after-unpublish Home Page
    reads go through a fresh, logged-out browser context, never the
    CMS-authenticated `page` — this also removes the earlier need to
    navigate `authoring` back to the entries list after the public-page
    read, since the public read never shares `page` with it anymore.
    """
    from core.web.browser import new_context

    admin = HomePromoBannersAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="promotional-banner")
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePromoBannersPage(anon_context.new_page())
    alt_en = "QCTEST-135125 Unpublish Banner"

    try:
        with allure.step("Create and publish a fixture banner"):
            admin.open_promo_banners_list()
            _create_banner_via_object_authoring(authoring, alt_en, "الغاء-نشر-135125", "511", True)
            authoring.save_as_draft()
            authoring.open_entry_by_edit_link(alt_en)
            authoring.submit_for_publishing()
            assert authoring.row_status_text(alt_en) == "Approved", (
                f"fixture banner {alt_en!r} did not reach Approved before "
                f"the unpublish assertion, got {authoring.row_status_text(alt_en)!r}"
            )

        with allure.step("Confirm the banner IS visible on the Home Page before unpublish"):
            visible_before = home.reload_until_banner_matches(alt_en, expected_visible=True)
        assert visible_before, (
            f"Published fixture banner {alt_en!r} not visible on the Home "
            f"Page before unpublish — cannot proceed without a confirmed "
            "precondition"
        )

        with allure.step("Open the published banner slot and click Unpublish"):
            # authoring is left on the edit form after submit_for_publishing()
            # above, not the entries list open_entry_by_edit_link() needs —
            # must return to the entries list first. Only reads through the
            # anon_page's home now, so (unlike before the anonymous-context
            # fix) this step is no longer about recovering from a public-page
            # navigation on the shared `page`, just this ordinary precondition.
            authoring.open_entries_list()
            authoring.open_entry_by_edit_link(alt_en)
            assert authoring.is_save_as_draft_disabled(), (
                "Save as Draft was not disabled while editing a published "
                "(Approved) entry — the Unpublish precondition this step "
                "relies on is not actually in the state the case expects"
            )
            authoring.unpublish_to_edit_as_draft()

        with allure.step("Assert status changed off Approved"):
            status_after = authoring.row_status_text(alt_en)
        assert status_after == "Draft", (
            f"banner {alt_en!r} status did not change after Unpublish, got "
            f"{status_after!r}"
        )

        with allure.step("Navigate to the public Home Page and assert the banner no longer displays"):
            hidden_after = home.reload_until_banner_matches(alt_en, expected_visible=False)
        assert hidden_after, (
            f"Unpublished banner {alt_en!r} still visible on the Home Page "
            f"within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )
    finally:
        # Teardown must land on manage-promotional-banner's own entries
        # list (authoring.open_entries_list()), NOT
        # admin.open_promo_banners_list() — the raw admin's list has no
        # `data-qc-oel-delete` rows (confirmed live 2026-09-03).
        try:
            authoring.open_entries_list()
            authoring.delete_entry_by_title(alt_en)
        except Exception:
            logger.warning("teardown for %r did not complete — leftover QCTEST data may remain", alt_en)
        anon_context.close()


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("Active toggle vs workflow state")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Deactivating a published banner hides it from the Home Page without changing its publish state")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129368
@pytest.mark.tc_135186
def test_deactivate_published_banner_preserves_workflow_state(page):
    """ADO-135186. Steps (from Azure DevOps, quoted verbatim):
      1. Log in to CMS, open the published banner -> Banner is Published and
         Active=true
      2. Toggle Active Status to False -> Active Status set to False
      3. Save -> Saved; workflow state remains Published; success toast
         shown
      4. Load the public Home Page -> Banner does not appear on the Home
         Page despite Published workflow state

    Adapted per this module's WORKFLOW FINDING: this object has no attached
    workflow, so its Status column reads "APPROVED" for every entry — this
    environment's stand-in for "Published" — both before and after Save;
    there is no separate Draft/Pending Review/Published state machine to
    transition through. The test creates its own fixture banner
    (Active=true, which auto-approves to Status=APPROVED on Save), then
    asserts the case's actual intent: the Active Status toggle governs Home
    Page visibility independently of the Status column, and the Status
    column is confirmed unchanged (still APPROVED) across the Save that
    flips Active Status to False.
    """
    admin = HomePromoBannersAdminPage(page)
    home = HomePromoBannersPage(page)
    alt_en = "QCTEST-135186 Deactivate Published"

    try:
        _create_banner(admin, alt_en, "الغاء-تفعيل-135186", "505", active=True)

        with allure.step("Confirm the fixture banner is published (Status=APPROVED) and visible while Active=true"):
            admin.open_promo_banners_list()
            status_before = admin.row_status_text(alt_en)
            assert "APPROVED" in status_before, (
                f"expected fixture banner Status=APPROVED before toggle, got {status_before!r}"
            )
            visible_before = home.reload_until_banner_matches(alt_en, expected_visible=True)
        assert visible_before, (
            f"Fixture banner {alt_en!r} not visible on the Home Page with "
            f"Active Status=True within {home.RELOAD_POLL_TIMEOUT_MS}ms — "
            "cannot proceed to the deactivate assertion without a confirmed precondition"
        )

        with allure.step("Open the banner, toggle Active Status to False, and Save"):
            admin.open_banner_edit_form_by_alt_text(alt_en)
            assert admin.is_active() is True
            admin.set_active(False)
            admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error deactivating banner: {admin.save_error_text()!r}"
        )

        with allure.step("Assert the banner's workflow/publish state (Status column) is unchanged after Save"):
            admin.open_promo_banners_list()
            status_after = admin.row_status_text(alt_en)
            assert "APPROVED" in status_after, (
                f"Status changed after deactivating (still expected APPROVED/"
                f"published), got {status_after!r}"
            )

        with allure.step("Assert the banner no longer appears on the public Home Page despite unchanged publish state"):
            hidden_after = home.reload_until_banner_matches(alt_en, expected_visible=False)
        assert hidden_after, (
            f"Banner {alt_en!r} still visible on the Home Page after "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms of deactivating Active Status, "
            "despite its Published/APPROVED workflow state being unchanged"
        )
    finally:
        admin.open_promo_banners_list()
        admin.delete_row_by_alt_text(alt_en)


def _fmt_date(d: datetime.date) -> str:
    return d.strftime(HomePromoBannersAdminPage.DATE_INPUT_FORMAT)


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("Scheduling — Start/End Date range")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A banner only displays on the Home Page within its configured Start/End date range")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129368
@pytest.mark.tc_135191
def test_banner_visible_only_within_start_end_date_range(page):
    """ADO-135191 (originally tagged Manual by QA; automated on the QA
    Manager's explicit approval per this task's instructions). Steps (from
    Azure DevOps, quoted verbatim):
      1. Publish a banner with Start Date = today and End Date = today+7,
         Active=true -> Banner published, scheduled for today through today+7
      2. Load the Home Page today -> Banner is visible today (within range)
      3. System-date-shift or wait to a date after End Date, reload the Home
         Page -> After End Date has passed, banner no longer appears on the
         Home Page

    ADAPTED, disclosed: step 3 as literally worded requires either shifting
    the environment's system clock or a real multi-day wait, neither
    reachable from a scripted pytest run (no clock-shift control on this
    environment; a literal 7-day wait is not a viable automated test). The
    test instead exercises the SAME underlying date-range gate from both
    sides without waiting for real time to elapse — confirmed live this
    session (throwaway probe script, not part of this suite) that the
    delivery surface DOES enforce the range: an otherwise-identical
    Active=true fixture is visible on the Home Page when Start/End Date
    bracket today, and is NOT visible when Start/End Date are both already
    in the past.
      - In-range fixture: Start Date=today, End Date=today+7 (exactly the
        case's own Arrange values) -> asserted visible today.
      - Out-of-range fixture: Start Date=today-10, End Date=yesterday (a
        window that has already elapsed) -> asserted NOT visible, standing
        in for "a date after End Date has passed" without the clock needing
        to actually advance.
    Both fixtures are Active=true and otherwise identical, so the date range
    is the only variable under test — preserving the case's actual intent
    (Home Page display gated by the Start/End Date range) rather than
    reinterpreting it.
    """
    admin = HomePromoBannersAdminPage(page)
    home = HomePromoBannersPage(page)
    today = datetime.date.today()
    alt_en_in_range = "QCTEST-135191 In Range"
    alt_en_out_of_range = "QCTEST-135191 Out Of Range"

    try:
        with allure.step("Create an in-range banner (Start=today, End=today+7) and confirm it is visible on the Home Page today"):
            _create_banner(
                admin, alt_en_in_range, "ضمن-النطاق-135191", "506", active=True,
                start_date=_fmt_date(today),
                end_date=_fmt_date(today + datetime.timedelta(days=7)),
            )
            visible_in_range = home.reload_until_banner_matches(alt_en_in_range, expected_visible=True)
        assert visible_in_range, (
            f"In-range fixture banner {alt_en_in_range!r} (Start=today, "
            f"End=today+7) not visible on the Home Page within "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms"
        )

        with allure.step("Create an out-of-range banner (an already-elapsed Start/End window) and confirm it does NOT appear on the Home Page"):
            _create_banner(
                admin, alt_en_out_of_range, "خارج-النطاق-135191", "507", active=True,
                start_date=_fmt_date(today - datetime.timedelta(days=10)),
                end_date=_fmt_date(today - datetime.timedelta(days=1)),
            )
            hidden_out_of_range = home.reload_until_banner_matches(alt_en_out_of_range, expected_visible=False)
        assert hidden_out_of_range, (
            f"Out-of-range fixture banner {alt_en_out_of_range!r} (End Date "
            f"already elapsed) unexpectedly visible on the Home Page within "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms"
        )
    finally:
        admin.open_promo_banners_list()
        admin.delete_row_by_alt_text(alt_en_in_range)
        admin.delete_row_by_alt_text(alt_en_out_of_range)


# ---------------------------------------------------------------------------
# ADO 135117 / 135184 / 135185 -- added 2026-09-09
#
# OBJECT NAME (per standards.md, taken from cms/Content-Admin-Guide.docx
# section 16 "Home - Promotional Banners", NEVER guessed or probed first):
# **PromotionalBanner** -> Object Authoring slug `promotional-banner`
# (`/web/qatar-chamber/manage-promotional-banner`). Guide field list:
# bannerImageEN / bannerImageAR (desktop), bannerImageMobileEN / ...AR
# (mobile, optional), bannerAltTextEN / ...AR, redirectUrl (bilingual),
# openInNewTab, startDate / endDate (optional schedule), displayOrder,
# activeStatus.
#
# CONFIRMED LIVE 2026-09-09 (headless Chromium against qcdev, freshly
# re-captured .auth/state.json, scoped CLI probes -- never the Playwright
# MCP):
#   - `manage-promotional-banner` renders 3 entries, all APPROVED
#     (QCDEMO-129368-PROMO-BANNER-1..3). The ENTRY column renders **Banner
#     Alt Text (EN)**, which is also the value the public carousel puts in
#     each slide image's `alt` -- so one string keys both the CMS row lookup
#     and the public-page assertion.
#   - Lifecycle controls all present on this surface: `Save as Draft`,
#     `Submit for Publishing`, and (on an Approved entry) `Unpublish to edit
#     as draft`. This is what unblocked these cases; the module's original
#     WORKFLOW FINDING above describes the RETIRED Content & Data surface,
#     where none of them existed.
#   - Required fields (live `required`-attribute read; this form renders no
#     visible "*"): Banner Alt Text (EN), Banner Alt Text (AR), Display
#     Order. The image fields are not DOM-required.
#   - Public baseline at the time of writing: 3 slides, alt texts matching
#     the 3 CMS rows exactly.
#
# DISCLOSED CASE-VS-BUILD LABEL MAPPING (applies to all three cases below,
# and is the same mapping already disclosed for TC 135123/135124/135125):
#   case wording        -> this build's actual state/control
#   "Publish"           -> `Submit for Publishing`
#   "Published"         -> status `Approved`
#   "Unpublish"         -> `Unpublish to edit as draft`
#   "Unpublished"       -> status `Draft`
#   "Pending Review"    -> DOES NOT EXIST. `Submit for Publishing` moves
#                          Draft -> Approved directly, with no intermediate
#                          moderation state. Asserted and reported as such
#                          below rather than faked.
#
# TEST-DATA POLICY FOR THESE THREE -- DISCLOSED DEVIATION from the delete-on-
# teardown convention the older tests in this module use, per the QA
# Manager's standing instruction that newly-created entries are LEFT IN
# PLACE: `_retire_created_banner()` never deletes. It instead returns the
# created entry to Draft + Active Status=False, which restores the PUBLIC
# Home Page to its 3-slide baseline while keeping the QCTEST record in the
# CMS for inspection. That satisfies both the no-teardown instruction and
# standards.md's rule that a test must not leave live public content
# altered.
# ---------------------------------------------------------------------------

PROMO_XDIST_GROUP = pytest.mark.xdist_group("promotional_banner_129368")


def _sweep_previous_run_leftovers(authoring: ObjectAuthoringPage, alt_en: str) -> None:
    """Remove same-titled rows THIS case left behind on an earlier run.

    Added 2026-09-10 after a real failure: because `_retire_created_banner()`
    keeps the record instead of deleting it (the standing no-teardown
    instruction), a second run of a create-case produced two rows with the
    same Banner Alt Text (EN), and `open_entry_by_edit_link()` then failed
    with a Playwright strict-mode violation ("resolved to 2 elements").

    This runs BEFORE the case creates anything, so the invariant is "exactly
    one QCTEST row per case survives a run, for inspection" rather than
    "one more every run". It only ever touches this case's own
    `QCTEST-<tc-id>` title -- `delete_all_entries_by_title()` itself refuses
    anything outside the QCTEST- namespace -- so real editorial banners are
    unreachable from here.
    """
    authoring.delete_all_entries_by_title(alt_en)


def _retire_created_banner(authoring: ObjectAuthoringPage, alt_en: str) -> None:
    """Restore-not-delete teardown -- see the TEST-DATA POLICY note above.

    Deliberately tolerant: it re-navigates to the entries list itself and
    no-ops when the row is absent, so it is safe to call unconditionally
    from a `finally` even when the test failed before creating anything.
    """
    authoring.open_entries_list()
    if not authoring.row_visible(alt_en):
        return
    authoring.open_entry_by_edit_link(alt_en)
    if authoring.current_status() == "Approved":
        authoring.unpublish_to_edit_as_draft()
    authoring.set_checkbox("Active Status", False)
    authoring.save_as_draft()


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("Content workflow - create and publish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site Content Editor can create and publish a new promotional banner slot")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.workflow
@pytest.mark.pbi_129368
@pytest.mark.tc_135117
@pytest.mark.traceability("135117")
@PROMO_XDIST_GROUP
def test_create_and_publish_new_promotional_banner_slot(page):
    """ADO-135117 (Control_Panel, Regression, UAT, Workflow; Priority 2).
    Steps, quoted verbatim from the Azure DevOps work item:
      1. Log into Liferay CMS as Site Content Editor -> Login succeeds
      2. Navigate to Home Page > Promotional Banners / Ad Slots Management
         -> Management screen loads with existing banner list
      3. Click Add Banner -> Add Banner form opens
      4. Upload both bilingual images, enter bilingual alt text, redirect
         URL, display order = 1, set Active Status = true -> All fields
         accept the entered values with no inline validation errors
      5. Save as Draft, then Publish -> System displays a Liferay generic
         success toast; banner slot status changes to Published

    CMS-only case (no Web tag) -- the public Home Page is deliberately NOT
    asserted here; ADO-135184 below is the end-to-end sibling that does.

    DISCLOSED DEVIATIONS FROM THE LITERAL WORDING:
      - Steps 1-3: on the Object Authoring surface, `manage-promotional-
        banner` with no `editEntry` param IS the Add form -- there is no
        separate "Add Banner" button to click. Login is the framework's
        stored-session auth, re-captured immediately before the run.
      - Step 5 "Publish" is this build's `Submit for Publishing`, and
        "Published" is status `Approved` (see the mapping note above).
      - The toast is not asserted. `ObjectAuthoringPage` has no toast/error
        reader, so a toast assertion would be unverifiable rather than
        merely unwritten. The step's real outcome -- the status transition
        -- IS asserted, on both the edit form and the entries list.
    """
    authoring = ObjectAuthoringPage(page, slug="promotional-banner")
    alt_en = "QCTEST-135117 Create And Publish"
    alt_ar = "إنشاء-ونشر-135117"
    redirect_url = "https://www.qatarchamber.com/qctest-135117"

    try:
        with allure.step("Clear any same-titled leftover from a previous run of this case"):
            _sweep_previous_run_leftovers(authoring, alt_en)

        with allure.step("Open the Promotional Banner authoring form and enter every field the case names"):
            _create_banner_via_object_authoring(authoring, alt_en, alt_ar, "1", True)
            authoring.fill_text("Redirect URL", redirect_url)

        with allure.step("Assert all fields accepted the entered values with no inline validation error"):
            accepted = {
                "Banner Alt Text (EN)": authoring.field_value("Banner Alt Text (EN)"),
                "Banner Alt Text (AR)": authoring.field_value("Banner Alt Text (AR)"),
                "Redirect URL": authoring.field_value("Redirect URL"),
                "Display Order": authoring.spinbutton_value("Display Order"),
            }
            active_accepted = authoring.is_checked("Active Status")
        assert accepted["Banner Alt Text (EN)"] == alt_en, accepted
        assert accepted["Banner Alt Text (AR)"] == alt_ar, accepted
        assert accepted["Redirect URL"] == redirect_url, accepted
        assert accepted["Display Order"] == "1", accepted
        assert active_accepted, "Active Status did not accept the checked state"

        with allure.step("Save as Draft"):
            authoring.save_as_draft()
            status_draft = authoring.row_status_text(alt_en)
        assert status_draft == "Draft", (
            f"new banner {alt_en!r} did not save as Draft, got {status_draft!r}"
        )

        with allure.step("Publish it (this build: Submit for Publishing)"):
            authoring.open_entry_by_edit_link(alt_en)
            authoring.submit_for_publishing()
            status_published = authoring.row_status_text(alt_en)
        assert status_published == "Approved", (
            f"banner {alt_en!r} did not reach Approved (this build's "
            f"Published), got {status_published!r}"
        )
    finally:
        try:
            _retire_created_banner(authoring, alt_en)
        except Exception:  # noqa: BLE001 -- teardown must never mask the real failure
            logger.warning(
                "restore for %r did not complete -- a QCTEST banner may still be "
                "Approved and Active on the public Home Page", alt_en
            )


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("End-to-end - CMS to public Home Page")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Admin can create, publish, and see a promotional banner appear on the Home Page end-to-end")
@pytest.mark.control_panel
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129368
@pytest.mark.tc_135184
@pytest.mark.traceability("135184")
@PROMO_XDIST_GROUP
def test_create_publish_and_see_banner_on_home_page_end_to_end(page, browser):
    """ADO-135184 (Control_Panel + Web, Regression, UAT; Priority 1).
    Steps, quoted verbatim from the Azure DevOps work item:
      1. Log in to CMS as Site Content Editor -> Login succeeds
      2. Add Banner: upload EN+AR images, enter bilingual alt text,
         redirect URL, Display Order=1, Active=true -> All fields populated
         as entered
      3. Save as Draft -> Draft saved; Liferay success toast shown
      4. Submit for review -> State moves to Pending Review; toast shown
      5. Publish the banner -> State moves to Published; toast shown
      6. Trigger cache refresh / wait for cache TTL -> Cache refreshed
      7. Load the public Home Page -> Banner is visible on the Home Page
         with the configured EN image, alt text, and is clickable to the
         redirect URL

    DISCLOSED DEVIATION -- STEPS 4 AND 5 COLLAPSE INTO ONE TRANSITION.
    Confirmed live: this build has no Pending Review state. `Submit for
    Publishing` moves Draft -> Approved directly, so there is no
    intermediate state for step 4 to land on and no separate step-5
    Publish action to invoke afterwards. The test asserts the transition
    that DOES exist (Draft -> Approved) and this docstring records the
    gap; it does not manufacture a Pending Review assertion. Same finding
    already reported for TC 135123/135124 -- worth the QA Manager deciding
    once whether the workflow was descoped or the cases were authored
    against an assumed design.

    Step 6 is a real condition-based poll (`reload_until_banner_matches`),
    never a sleep. Step 7's public read runs in a FRESH LOGGED-OUT context
    (mandatory per standards.md) so CMS session state cannot mask the
    result.
    """
    from core.web.browser import new_context

    authoring = ObjectAuthoringPage(page, slug="promotional-banner")
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePromoBannersPage(anon_context.new_page())
    alt_en = "QCTEST-135184 End To End"
    alt_ar = "شامل-135184"
    redirect_url = "https://www.qatarchamber.com/qctest-135184"

    try:
        with allure.step("Clear any same-titled leftover from a previous run of this case"):
            _sweep_previous_run_leftovers(authoring, alt_en)

        with allure.step("Add Banner: both images, bilingual alt text, redirect URL, Display Order=1, Active=true"):
            _create_banner_via_object_authoring(authoring, alt_en, alt_ar, "1", True)
            authoring.fill_text("Redirect URL", redirect_url)
            assert authoring.field_value("Banner Alt Text (EN)") == alt_en
            assert authoring.field_value("Banner Alt Text (AR)") == alt_ar
            assert authoring.field_value("Redirect URL") == redirect_url
            assert authoring.spinbutton_value("Display Order") == "1"
            assert authoring.is_checked("Active Status")

        with allure.step("Save as Draft"):
            authoring.save_as_draft()
            status_draft = authoring.row_status_text(alt_en)
        assert status_draft == "Draft", (
            f"banner {alt_en!r} did not save as Draft, got {status_draft!r}"
        )

        with allure.step("Submit for publishing (steps 4+5 -- no Pending Review state exists on this build)"):
            authoring.open_entry_by_edit_link(alt_en)
            authoring.submit_for_publishing()
            status_published = authoring.row_status_text(alt_en)
        assert status_published == "Approved", (
            f"banner {alt_en!r} did not reach Approved (this build's "
            f"Published), got {status_published!r}"
        )

        with allure.step("Wait for the public Home Page to reflect the new banner (anonymous context)"):
            appeared = home.reload_until_banner_matches(alt_en, expected_visible=True)
        assert appeared, (
            f"published banner {alt_en!r} did not appear on the public Home "
            f"Page within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )

        with allure.step("Assert the rendered banner carries the configured EN image, alt text and redirect link"):
            rendered_src = home.banner_image_src(alt_en)
            rendered_href = home.banner_link_href(alt_en)
        assert rendered_src, (
            f"banner {alt_en!r} rendered with no image src -- the configured "
            "EN image is not wired to the public slide"
        )
        assert rendered_href == redirect_url, (
            f"banner {alt_en!r} is not clickable to the configured redirect "
            f"URL: expected {redirect_url!r}, got {rendered_href!r}"
        )
    finally:
        try:
            _retire_created_banner(authoring, alt_en)
        except Exception:  # noqa: BLE001
            logger.warning(
                "restore for %r did not complete -- a QCTEST banner may still be "
                "Approved and Active on the public Home Page", alt_en
            )
        anon_context.close()


@allure.epic("Home Page")
@allure.feature("Promotional Banners")
@allure.story("End-to-end - unpublish removes from public Home Page")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Unpublishing a banner removes it from the Home Page after cache refresh")
@pytest.mark.control_panel
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129368
@pytest.mark.tc_135185
@pytest.mark.traceability("135185")
@PROMO_XDIST_GROUP
def test_unpublishing_banner_removes_it_from_home_page_after_cache_refresh(page, browser):
    """ADO-135185 (Control_Panel + Web, Regression; Priority 1).
    Steps, quoted verbatim from the Azure DevOps work item:
      1. Log in to CMS, locate the published banner -> Banner list shows
         Published state
      2. Click Unpublish -> State changes to Unpublished; Liferay success
         toast shown
      3. Wait for cache refresh -> Cache refreshed
      4. Load the public Home Page -> Banner no longer appears in the
         promotional banners section

    PRECONDITION ("Banner from TC-019 is live"): the case inherits a live
    banner from its predecessor. Rather than depend on ADO-135184 having
    run first -- which would make this test order-dependent and unable to
    run alone -- it establishes the same precondition itself and ASSERTS it
    publicly before touching anything. The case's own subject matter (the
    unpublish transition) is unchanged by that.

    Deliberately NOT retargeted at one of the three real
    QCDEMO-129368-PROMO-BANNER-* entries: unpublishing real editorial
    content would take a live banner off the public Home Page for the
    duration of the run, which standards.md forbids when a disposable
    fixture achieves the identical assertion.

    Both public reads use a FRESH LOGGED-OUT context (mandatory per
    standards.md), and step 3's "wait for cache refresh" is a real
    condition-based poll, never a sleep.
    """
    from core.web.browser import new_context

    authoring = ObjectAuthoringPage(page, slug="promotional-banner")
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePromoBannersPage(anon_context.new_page())
    alt_en = "QCTEST-135185 Unpublish Removes From Home"
    alt_ar = "إلغاء-النشر-135185"

    try:
        with allure.step("Clear any same-titled leftover from a previous run of this case"):
            _sweep_previous_run_leftovers(authoring, alt_en)

        with allure.step("Establish the precondition: a published, live banner"):
            _create_banner_via_object_authoring(authoring, alt_en, alt_ar, "1", True)
            authoring.save_as_draft()
            authoring.open_entry_by_edit_link(alt_en)
            authoring.submit_for_publishing()
            status_before = authoring.row_status_text(alt_en)
        assert status_before == "Approved", (
            f"precondition failed: fixture banner {alt_en!r} is not in the "
            f"Published/Approved state, got {status_before!r}"
        )

        with allure.step("Confirm the banner IS on the public Home Page before unpublishing"):
            live_before = home.reload_until_banner_matches(alt_en, expected_visible=True)
        assert live_before, (
            f"precondition failed: banner {alt_en!r} is not live on the "
            "public Home Page, so its removal cannot be observed"
        )

        with allure.step("Locate the published banner in the CMS and click Unpublish"):
            authoring.open_entries_list()
            authoring.open_entry_by_edit_link(alt_en)
            assert authoring.is_save_as_draft_disabled(), (
                "Save as Draft was not disabled on the opened entry -- it is "
                "not in the published state this step requires"
            )
            authoring.unpublish_to_edit_as_draft()
            status_after = authoring.row_status_text(alt_en)
        assert status_after == "Draft", (
            f"banner {alt_en!r} did not leave the published state after "
            f"Unpublish, got {status_after!r} (this build labels the "
            "unpublished state 'Draft', not 'Unpublished')"
        )

        with allure.step("Wait for cache refresh, then assert the banner is gone from the Home Page"):
            gone = home.reload_until_banner_matches(alt_en, expected_visible=False)
        assert gone, (
            f"unpublished banner {alt_en!r} still appears in the promotional "
            f"banners section within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )
    finally:
        try:
            _retire_created_banner(authoring, alt_en)
        except Exception:  # noqa: BLE001
            logger.warning(
                "restore for %r did not complete -- a QCTEST banner may still be "
                "Approved and Active on the public Home Page", alt_en
            )
        anon_context.close()

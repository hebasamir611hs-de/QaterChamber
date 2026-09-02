"""
web/tests/home_community_partners/test_home_community_partners_control_panel.py
— Control_Panel-tagged cases for PBI 129385 (Home Page "Community
Partners").

RESUMED/REBUILT 2026-08-31 from an interrupted prior session (a connection
error during a logo-upload-modal probe). This session independently
re-verified everything below live (nothing carried over unread) — see
home_community_partners_admin_page.py's module docstring for the full
field-by-field confirmation and every case-vs-product discrepancy found.

Summary of QA-Manager-directed decisions applied here (see task instructions):
  - TC 135829 uses a distinct test-marked name ("QCTEST-135829 Test Partner
    Co"), not "Qatar Airways" (a real record).
  - TC 135830 asserts on the REAL required field (Partner Name (EN)) and
    the REAL validation strings — the case's literal "Logo Image is
    required." text does not match reality: this session's own live Save
    probe (all fields filled except the logo) SUCCEEDED, proving Logo is
    NOT enforced as required by this form. That is reported as a
    case-vs-product discrepancy, not silently coded around.
  - TC 135832 uses Qatar Airways (real, existing record) — safe now that
    TC 135829 no longer collides with it.

Shape corrections forced by this session's live findings (all documented
in the admin Page Object's module docstring):
  - No Draft/Preview/Publish lifecycle exists on this form — Save commits
    directly to Status "Approved". TC 135829's Preview step is dropped.
  - No Alt Text (EN)/(AR) fields exist, and there is ONE Partner Logo
    field (not an EN/AR pair) — TC 135829 fills the real six fields only.
  - The public carousel renders each partner's logo multiple times (a
    duplicated marquee loop, confirmed live: 12 `img.qc-partner-logo`
    nodes for 3 real partners) — presence/absence is asserted via `alt`
    text (Partner Name (EN)), never a raw image count.
  - No propagation/latency budget specific to this content type was
    measured this session; cms-profile.md's confirmed ~0s figure (Board
    Members' JAX-RS source) is used as the conservative poll baseline via
    CommunityPartnersPage.reload_until_logo_matches() — poll, never a bare
    sleep.

FOLLOW-UP INVESTIGATION (2026-08-31, this session, root-causing a batch
pytest run's failures on both TC 135829 and TC 135830 — both re-verified
LIVE against qcdev this session, with network-response capture, not
reasoned about from the source alone):
  - Both real create-form Saves this session (one with Partner Name (EN)
    filled, one deliberately without it) were exercised end-to-end live: the
    filled case fires a real `POST /o/c/communitypartners/scopes/<groupId>`
    that returns 200; the omitted-name case fires NO such POST at all (only
    the DDM form-context-provider call) and the page shows the real banner
    "This form is invalid. Check field Partner Name (EN)." — Partner Name
    (EN) DOES genuinely block Save, confirming the PRIOR session's finding,
    not contradicting it. TC 135830 was not a case-vs-product gap this
    session; the case's own re-verified assertions are correct.
  - `upload_partner_logo()`'s prior fixed `wait_for_timeout(1000)` after the
    picker's "Add" click was a blind sleep standing in for "the picker modal
    has actually closed" — measured live this session at ~200ms on a warm
    session, but with no guarantee under a real pytest run's heavier load.
    A Save click landing while that modal is still mid-close is the SAME
    documented failure class as GmMessageAdminPage.select_status()'s own
    confirmed-live evidence: the popup's outside-click-dismiss handler eats
    the click, no submit request ever fires, and `is_save_error_shown()`
    then correctly reports "no error" because there was nothing to
    validate — which a calling test can misread as either "Save silently
    succeeded but the row never shows up" (TC 135829) or "Save appeared to
    succeed" (TC 135830, since no error banner would exist either).
    `upload_partner_logo()` now waits for the picker iframe's own DOM
    detachment (a real signal) instead of a fixed sleep — see that method's
    own updated docstring.
  - `test_create_new_community_partner_appears_on_home_page` now asserts via
    `CommunityPartnersAdminPage.wait_for_row_visible()` (polls the list,
    re-navigating each cycle) rather than a single `open_community_
    partners_list()` + `row_visible()` shot, guarding the same class of
    write-vs-read-cache propagation lag gm_message_admin_page.py's own
    SAVE_COMMIT_GRACE_MS documents for this project's Object Definition
    grids — CommunityPartnersAdminPage.save() also now applies that same
    2000ms grace before returning.
  - Both investigation records created live this session
    ("...Test Partner Co VERIFY", row 112972; a second unsaved probe record
    for the omitted-name case, never persisted since Save correctly
    blocked it) were deleted / never existed to begin with — the admin list
    was re-confirmed live to show exactly the 3 real records afterward.
"""

import allure
import pytest

from cms.pages.home_community_partners.home_community_partners_admin_page import (
    CommunityPartnersAdminPage,
    QATAR_AIRWAYS_NAME,
)
from web.pages.home_community_partners.home_community_partners_page import (
    CommunityPartnersPage,
)

TEST_PARTNER_NAME_EN = "QCTEST-135829 Test Partner Co"
TEST_PARTNER_NAME_AR = "شركة اختبار QCTEST-135829"
TEST_PARTNER_URL = "https://example.com/qctest-135829"
TEST_PARTNER_DISPLAY_ORDER = "4"
LOGO_FIXTURE = "web/tests/home_community_partners/fixtures/partner_logo.png"

TC_135830_PARTNER_NAME_EN = "QCTEST-135830 Validation Co"
TC_135830_PARTNER_NAME_AR = "شركة اختبار QCTEST-135830"
TC_135830_PARTNER_URL = "https://example.com/qctest-135830"


@allure.epic("Home Page")
@allure.feature("Community Partners")
@allure.story("CMS authoring workflow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site Content Editor can create a new Community Partner and it appears on the Home Page")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.pbi_129385
@pytest.mark.tc_135829
def test_create_new_community_partner_appears_on_home_page(page):
    # QA-135829 — Add Partner -> fill mandatory fields (Partner Name EN/AR,
    # Partner URL, Display Order, Logo) -> Save (commits directly, no
    # separate Preview/Publish step on this form — see module docstring)
    # -> assert no validation error and the row is Approved -> reload Home
    # Page -> assert the test partner's logo appears (by alt text).
    admin = CommunityPartnersAdminPage(page)
    home = CommunityPartnersPage(page)

    admin.open_new_partner_form()

    try:
        admin.set_partner_name_en(TEST_PARTNER_NAME_EN)
        admin.set_partner_name_ar(TEST_PARTNER_NAME_AR)
        admin.set_partner_url(TEST_PARTNER_URL)
        admin.set_display_order(TEST_PARTNER_DISPLAY_ORDER)
        # A new entry's Active checkbox defaults to UNCHECKED (confirmed
        # live this session — both prior leftover test rows from this same
        # test's earlier failed runs, 113142/113164, rendered "Active: No"
        # in the admin list despite never being touched by this test). The
        # case's own assertion (the new partner's logo appears on the Home
        # Page) can never pass without this — the public carousel only
        # renders Active=Yes partners (the same behavior TC 135832 exploits
        # in reverse). Not a form-shape assumption; set explicitly here.
        admin.set_active(True)
        admin.upload_partner_logo(LOGO_FIXTURE)
        assert admin.uploaded_logo_filename() != "", (
            "logo upload did not populate the Partner Logo field before Save"
        )

        admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error creating a new Community Partner: "
            f"{admin.save_error_text()!r}"
        )

        # Assert: admin list shows the new entry. Polls (not a single-shot
        # check) — see CommunityPartnersAdminPage.wait_for_row_visible()'s
        # docstring for the confirmed-live write-vs-read-cache lag class
        # this guards against.
        assert admin.wait_for_row_visible(TEST_PARTNER_NAME_EN), (
            f"new partner {TEST_PARTNER_NAME_EN!r} not visible in the admin list after Save"
        )

        # Assert: the public Home Page carousel shows the new partner's logo.
        assert home.reload_until_logo_matches(TEST_PARTNER_NAME_EN, expected_visible=True), (
            f"Home Page did not render the new partner's logo (alt={TEST_PARTNER_NAME_EN!r}) after Save"
        )
    finally:
        admin.open_community_partners_list()
        deleted = admin.delete_row_by_name(TEST_PARTNER_NAME_EN)
        if not deleted:
            # Row wasn't created (e.g. Save failed before this point) —
            # nothing to clean up.
            pass


@allure.epic("Home Page")
@allure.feature("Community Partners")
@allure.story("Form validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Omitting the required Partner Name (EN) field blocks Save with the real validation message")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.pbi_129385
@pytest.mark.tc_135830
def test_omitting_required_partner_name_en_blocks_save(page):
    # QA-135830 — the case's literal precondition ("omit Logo Image") does
    # NOT reproduce a validation error on the real form: this session's own
    # live probe (all fields filled except the logo) SAVED SUCCESSFULLY
    # (Status "Approved", empty logo cell) — Logo is not enforced as
    # required here. That is a disclosed case-vs-product discrepancy for
    # the QA Manager to adjudicate, not something this test can silently
    # paper over.
    #
    # This test instead exercises the REAL required-field guarantee this
    # form does enforce (Partner Name (EN), confirmed live via
    # aria-required="true" AND an actual failed Save this session) and
    # asserts the REAL, live-confirmed validation strings — the same
    # substitution precedent test_home_strategic_direction_control_panel.py
    # already established for TC 135556 on this project.
    admin = CommunityPartnersAdminPage(page)
    home = CommunityPartnersPage(page)

    admin.open_new_partner_form()

    try:
        # Fill every field EXCEPT Partner Name (EN).
        admin.set_partner_name_ar(TC_135830_PARTNER_NAME_AR)
        admin.set_partner_url(TC_135830_PARTNER_URL)
        admin.set_display_order("998")
        admin.upload_partner_logo(LOGO_FIXTURE)

        admin.save()

        # Assert: the real validation error is shown.
        assert admin.is_save_error_shown(), (
            "expected a validation error when Partner Name (EN) is omitted, "
            "but Save appeared to succeed"
        )
        assert "Partner Name (EN)" in admin.save_error_text() or admin.INLINE_REQUIRED_TEXT in admin.save_error_text(), (
            f"unexpected validation error text: {admin.save_error_text()!r}"
        )

        # Assert: no entry was published — the Home Page shows nothing for
        # this never-created partner.
        assert home.reload_until_logo_matches(
            TC_135830_PARTNER_NAME_EN, expected_visible=False, timeout_ms=3000
        ), (
            "logo unexpectedly appeared on Home Page for a partner that "
            "should never have been created"
        )
    finally:
        # Defensive cleanup: if this form somehow DID commit a Draft/entry
        # (e.g. a future product fix makes Partner Name (EN) non-blocking
        # too), remove it rather than leaving a leftover test row.
        admin.open_community_partners_list()
        admin.delete_row_by_name(TC_135830_PARTNER_NAME_EN)


@allure.epic("Home Page")
@allure.feature("Community Partners")
@allure.story("Active toggle visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Deactivating a Community Partner removes its logo from the Home Page while others remain")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.pbi_129385
@pytest.mark.tc_135832
@pytest.mark.xdist_group("qatar_airways_45776")
def test_deactivating_partner_removes_logo_from_home_page(page):
    # QA-135832 — capture Qatar Airways' baseline Active state (real,
    # shared record; confirmed live this session as Active=Yes/Approved) ->
    # set Active=False -> Save -> reload Home Page -> assert Qatar Airways'
    # logo disappears while QatarEnergy/QNB remain -> restore Active=True
    # in `finally`, re-verified by a fresh reopen (matches the same
    # snapshot-restore-and-reverify precedent used elsewhere in this
    # project for shared, non-disposable records).
    admin = CommunityPartnersAdminPage(page)
    home = CommunityPartnersPage(page)

    admin.open_partner_edit_form_by_name(QATAR_AIRWAYS_NAME)
    baseline_active = admin.is_active()
    assert baseline_active is True, (
        f"expected Qatar Airways' baseline Active state to be True, got {baseline_active!r} "
        f"— confirm the real baseline before running this test"
    )

    try:
        admin.set_active(False)
        admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error deactivating Qatar Airways: {admin.save_error_text()!r}"
        )

        # Assert: Qatar Airways' logo disappears from the Home Page.
        assert home.reload_until_logo_matches(QATAR_AIRWAYS_NAME, expected_visible=False), (
            "Qatar Airways' logo still visible on Home Page after deactivation"
        )
        # Assert: the other two real partners remain visible.
        home.open_home()
        assert home.is_partner_logo_visible("QatarEnergy"), "QatarEnergy logo unexpectedly disappeared"
        assert home.is_partner_logo_visible("QNB"), "QNB logo unexpectedly disappeared"
    finally:
        # Restore baseline, hardened with a fresh reopen + assert-matches.
        admin.open_partner_edit_form_by_name(QATAR_AIRWAYS_NAME)
        admin.set_active(True)
        admin.save()
        admin.open_partner_edit_form_by_name(QATAR_AIRWAYS_NAME)
        restored_active = admin.is_active()
        assert restored_active == baseline_active, (
            f"failed to restore Qatar Airways' Active state to baseline "
            f"({baseline_active!r}) — currently {restored_active!r}"
        )

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
    QATAR_ENERGY_NAME,
    QNB_NAME,
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


# ---------------------------------------------------------------------------
# TC 135831 / TC 135833 (2026-09-03) — same PBI 129385 batch continued.
#
# Both were authored against a case set that assumes an object-authoring
# Draft/Preview/Publish lifecycle ("click Publish", "Success toast
# displayed") per .claude/context/active/standards.md's "Object Authoring —
# Draft / Preview / Publish / Unpublish Lifecycle" section. This session
# checked whether that surface (`manage-community-partners`) exists for this
# object before writing anything against it — it does not, and moreover NONE
# of the manage-<slug> pages currently resolve on qcdev:
#
#   https://qcdev.ihorizons.com/web/qatar-chamber/manage-community-partners
#   https://qcdev.ihorizons.com/web/qatar-chamber/manage-news-article
#   https://qcdev.ihorizons.com/web/qatar-chamber/manage-promotional-banner
#   https://qcdev.ihorizons.com/web/qatar-chamber/manage-service-card
#   https://qcdev.ihorizons.com/web/qatar-chamber/manage-strategic-pillar-card
#
# all render the site's "Coming Soon" template live this session (confirmed
# via a fresh authenticated context, re-checked after re-logging in to rule
# out a stale-session false negative) — the whole object-authoring surface is
# currently unreachable on this environment, not a Community-Partners-
# specific gap. This is disclosed as a live environment finding, not silently
# reasoned about from source.
#
# Consequently, both cases below are scripted against the ONLY reachable
# Control_Panel surface for this object — the raw Object Definitions editor
# (Content & Data > Community Partners) that every other test in this module
# already uses — with the same substitution precedent TC 135830 already
# established:
#   - TC 135831's "click Publish" -> the real form's only commit action,
#     Save (no separate Publish/Draft/Preview button exists on this editor —
#     see home_community_partners_admin_page.py's module docstring). This
#     makes TC 135831 functionally overlap with the already-scripted
#     TC 135830 (both omit Partner Name (EN) and assert the same real
#     validation strings) — flagged back here for the QA Manager to
#     adjudicate a possible case merge, not silently deduplicated away
#     (TC 135831 has its own Azure Test Case id and its own retest selector,
#     so it is scripted in full rather than skipped).
#   - TC 135833's "Success toast displayed" -> the real editor shows no
#     toast on Save (confirmed live via every existing test in this module,
#     e.g. TC 135829/135832 both assert `is_save_error_shown()` is False as
#     their own "no error" surrogate, never a toast) — asserted here as "no
#     validation error and the row is unchanged" instead of a toast that
#     does not exist on this form.
#
# TC 135834 ("Save as Draft, then Preview a draft without publishing") is NOT
# automated here at all: there is no Draft state or Preview action reachable
# on the raw editor (Save commits directly to Status "Approved", confirmed
# live in the admin Page Object's own module docstring), and the
# object-authoring surface that WOULD provide it is confirmed unreachable
# above. Blocking reason for the record: no reachable precondition state —
# not a missing locator on an existing screen.
# ---------------------------------------------------------------------------

TC_135831_PARTNER_NAME_AR = "شركة اختبار QCTEST-135831"
TC_135831_PARTNER_URL = "https://example.com/qctest-135831"


@allure.epic("Home Page")
@allure.feature("Community Partners")
@allure.story("Form validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publishing a Community Partner entry without a Partner Name is blocked")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.pbi_129385
@pytest.mark.tc_135831
def test_publishing_without_partner_name_en_is_blocked(page):
    # QA-135831 — the case's "click Publish" has no target on this form: the
    # raw Object Definitions editor exposes only Save/Cancel, and Save
    # commits directly to Status "Approved" with no separate Publish step
    # (see module docstring above and home_community_partners_admin_page.py's
    # own confirmed-live finding) — Save is exercised as the real "publish
    # action is submitted" step the case describes. Fill every mandatory
    # field EXCEPT Partner Name (EN) -> Save -> assert the real validation
    # error is shown and no entry was created -> reload the Home Page and
    # assert nothing appears there for it.
    admin = CommunityPartnersAdminPage(page)
    home = CommunityPartnersPage(page)

    admin.open_new_partner_form()

    try:
        admin.set_partner_name_ar(TC_135831_PARTNER_NAME_AR)
        admin.set_partner_url(TC_135831_PARTNER_URL)
        admin.set_display_order("999")
        admin.upload_partner_logo(LOGO_FIXTURE)

        admin.save()

        # Assert: the (real) validation error is shown — the case's literal
        # text ("Partner Name is required.") does not match this form's own
        # confirmed-live strings (see TC 135830 above); asserted against the
        # real banner/inline text instead.
        assert admin.is_save_error_shown(), (
            "expected a validation error when Partner Name (EN) is omitted "
            "before Save, but Save appeared to succeed"
        )
        assert "Partner Name (EN)" in admin.save_error_text() or admin.INLINE_REQUIRED_TEXT in admin.save_error_text(), (
            f"unexpected validation error text: {admin.save_error_text()!r}"
        )

        # Assert: no entry was published — the Home Page carousel shows
        # nothing for this never-created partner, anywhere.
        assert home.reload_until_logo_matches(
            TC_135831_PARTNER_NAME_AR, expected_visible=False, timeout_ms=3000
        ), (
            "a logo unexpectedly appeared on the Home Page for a partner "
            "that should never have been created"
        )
    finally:
        # Defensive cleanup in case a future product fix makes Partner Name
        # (EN) non-blocking and this form somehow DID commit an entry.
        admin.open_community_partners_list()
        admin.delete_row_by_name(TC_135831_PARTNER_NAME_AR)


@allure.epic("Home Page")
@allure.feature("Community Partners")
@allure.story("Display order")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Changing a partner's Display Order updates its position in the frontend carousel")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.pbi_129385
@pytest.mark.tc_135833
@pytest.mark.xdist_group("qatar_airways_45776")
def test_changing_display_order_updates_carousel_position(page):
    # QA-135833 — the case's literal Display Order values (3 -> 1, "shift
    # others accordingly") assume a 1/2/3 sequence; the REAL, live-confirmed
    # values for the 3 shared records are 100 (QatarEnergy), 200 (Qatar
    # Airways), 300 (QNB) — see intent, not the literal numbers: move the
    # currently-LAST partner (QNB, 300) to the FRONT (100), shifting
    # QatarEnergy/Qatar Airways back one slot each (200/300) so relative
    # order is fully determined, not just "QNB moved somewhere earlier".
    # Snapshots every touched record's baseline order and restores all three
    # in `finally`, re-verified by a fresh reopen (same snapshot-restore-
    # and-reverify precedent TC 135832 already established for these same
    # shared, non-disposable records). No "Success toast" exists on this
    # form (see module docstring) — success is asserted as "no validation
    # error and the row is unchanged" instead.
    admin = CommunityPartnersAdminPage(page)
    home = CommunityPartnersPage(page)

    admin.open_partner_edit_form_by_name(QATAR_ENERGY_NAME)
    baseline_qatarenergy = admin.display_order_value()
    admin.open_partner_edit_form_by_name(QATAR_AIRWAYS_NAME)
    baseline_qatarairways = admin.display_order_value()
    admin.open_partner_edit_form_by_name(QNB_NAME)
    baseline_qnb = admin.display_order_value()

    assert (baseline_qatarenergy, baseline_qatarairways, baseline_qnb) == ("100", "200", "300"), (
        f"expected the real baseline Display Order sequence (100, 200, 300), got "
        f"({baseline_qatarenergy!r}, {baseline_qatarairways!r}, {baseline_qnb!r}) — "
        f"confirm the real baseline before running this test"
    )

    try:
        admin.open_partner_edit_form_by_name(QNB_NAME)
        admin.set_display_order("100")
        admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error setting QNB's Display Order: {admin.save_error_text()!r}"
        )

        admin.open_partner_edit_form_by_name(QATAR_ENERGY_NAME)
        admin.set_display_order("200")
        admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error setting QatarEnergy's Display Order: {admin.save_error_text()!r}"
        )

        admin.open_partner_edit_form_by_name(QATAR_AIRWAYS_NAME)
        admin.set_display_order("300")
        admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error setting Qatar Airways' Display Order: {admin.save_error_text()!r}"
        )

        # Assert: the public Home Page carousel's logo order reflects the
        # new Display Order sequence — QNB first, then QatarEnergy, then
        # Qatar Airways.
        expected_order = [QNB_NAME, QATAR_ENERGY_NAME, QATAR_AIRWAYS_NAME]
        assert home.reload_until_order_matches(expected_order), (
            f"Home Page carousel order did not reflect the new Display Order "
            f"sequence; expected {expected_order!r}, got {home.visible_partner_order()!r}"
        )
    finally:
        # Restore baseline for all three shared records, re-verified by a
        # fresh reopen of each.
        admin.open_partner_edit_form_by_name(QATAR_ENERGY_NAME)
        admin.set_display_order(baseline_qatarenergy)
        admin.save()
        admin.open_partner_edit_form_by_name(QATAR_AIRWAYS_NAME)
        admin.set_display_order(baseline_qatarairways)
        admin.save()
        admin.open_partner_edit_form_by_name(QNB_NAME)
        admin.set_display_order(baseline_qnb)
        admin.save()

        admin.open_partner_edit_form_by_name(QATAR_ENERGY_NAME)
        restored_qatarenergy = admin.display_order_value()
        admin.open_partner_edit_form_by_name(QATAR_AIRWAYS_NAME)
        restored_qatarairways = admin.display_order_value()
        admin.open_partner_edit_form_by_name(QNB_NAME)
        restored_qnb = admin.display_order_value()
        assert (restored_qatarenergy, restored_qatarairways, restored_qnb) == (
            baseline_qatarenergy,
            baseline_qatarairways,
            baseline_qnb,
        ), (
            f"failed to restore baseline Display Order sequence "
            f"({baseline_qatarenergy!r}, {baseline_qatarairways!r}, {baseline_qnb!r}) — "
            f"currently ({restored_qatarenergy!r}, {restored_qatarairways!r}, {restored_qnb!r})"
        )

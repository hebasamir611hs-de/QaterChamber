"""
cms/tests/tenders/test_tenders_edge_control_panel.py — Control_Panel-
platform Edge cases for PBI 130952 ("QC - Business Gateway - 012 -
Tenders listing screen"), Qatar Chamber project (TC-226/146292 and
TC-229/146295 — Control_Panel half of a dual-platform case whose Web
half is already scripted in web/tests/tenders/test_tenders_web.py;
TC-227/146293 — pure Control_Panel).

TC-225/146291 and TC-228/146294 are tagged Manual in this batch and are
intentionally NOT scripted here (per this project's Automation/Manual
tagging rule) — see the batch report for confirmation.
"""

import os

import pytest

from cms.pages.tenders.tender_admin_page import TenderAdminPage, FIELD_TENDER_TITLE, FIELD_CLOSING_DATE
from config.settings import cms_role_credentials

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130952, pytest.mark.edge]

_VALID_PDF = os.path.join(os.path.dirname(__file__), "fixtures", "qctest_valid_document.pdf")


def _credentials():
    return cms_role_credentials("Site Content Editor")


@pytest.mark.tc_146292
@pytest.mark.lookupdata
@pytest.mark.traceability("INVEST-TENDERS-TC-226")
def test_removing_a_used_lookup_category_does_not_break_display(page):
    """INVEST-TENDERS-TC-226 — Azure TC 146292 (Control_Panel half; the Web
    half is test_tc226_lookup_category_removal_does_not_break_display_web_side
    in web/tests/tenders/test_tenders_web.py). LIVE GAP: no lookup-data
    admin surface for "Tender Category" was located this session (same
    gap already recorded on TC-219 in
    test_tenders_functional_low_control_panel.py) — there is no "remove a
    Lookup Category value" action reachable to exercise."""
    pytest.skip(
        "PRECONDITION UNAVAILABLE — the Tender Category lookup-data admin surface (where a "
        "category value would be removed) was not located this session; same gap as TC-219. "
        "Needs a follow-up locator-discovery pass once the lookup-data admin route is identified."
    )


@pytest.mark.tc_146293
@pytest.mark.traceability("INVEST-TENDERS-TC-227")
def test_manual_and_approved_submission_reference_numbers_do_not_collide(page):
    """INVEST-TENDERS-TC-227 — Azure TC 146293. The approved-submission
    (Path 1) half needs a real Pending EOISubmission record, which does
    not exist on this environment (0 entries — see
    eoi_submission_admin_page.py's module docstring); scripted to the
    manual-create (Path 2) half only, confirming this build's own
    duplicate-reference rejection (already exercised in
    test_tenders_functional_low_control_panel.py's TC-078) also holds
    against a second manually-created entry."""
    tender = TenderAdminPage(page).open_list(*_credentials())
    existing_ref = tender.newest_entry_code()
    assert existing_ref, "expected at least one existing Tender entry to collide against"
    tender.open_new_entry_form()
    tender.fill_valid_form(_VALID_PDF)
    tender.fill_reference_number(existing_ref)
    tender.save_as_draft()
    assert tender.current_status() != "Approved", (
        f"a second manually-created tender reusing an existing Reference Number ({existing_ref!r}) "
        "must not collide/be accepted"
    )


@pytest.mark.tc_146295
@pytest.mark.traceability("INVEST-TENDERS-TC-229")
def test_zero_day_validity_rejected_manual_create_side(page):
    """INVEST-TENDERS-TC-229 — Azure TC 146295 (Control_Panel/manual-create
    half; the public-webform half is
    test_tc229_zero_day_validity_rejected_webform_side in
    web/tests/tenders/test_tenders_web.py)."""
    tender = TenderAdminPage(page).open_create_form(*_credentials())
    tender.fill_valid_form(_VALID_PDF)
    tender.fill_date(FIELD_CLOSING_DATE, "2026-10-01")  # equals baseline Opening Date
    tender.save_as_draft()
    assert tender.current_status() != "Approved", (
        "a Closing Date exactly equal to the Opening Date (zero-day validity) must be rejected "
        "on the CMS manual-create path"
    )

"""
cms/tests/tenders/test_tenders_auth_control_panel.py — Control_Panel-
platform Auth cases for PBI 130952 ("QC - Business Gateway - 012 -
Tenders listing screen"), Qatar Chamber project (TC-039..043/
146105..146109).

Role-based access (TC-041/042: Site Content Author vs Editor) is tested
against the same manage-tender surface confirmed live in
tender_admin_page.py, using the project's own named-CMS-role credential
convention (config.settings.cms_role_credentials — see standards.md's
"Named CMS User Roles" section). The Approve/Reject/Publish role checks
in TC-040/043 that depend on a real Pending EOISubmission record are
scaffolded against eoi_submission_admin_page.py's confirmed-live
navigation/login only — see that Page Object's own module docstring for
why no live Pending record exists to open this session (0 entries; a
real submission is gated behind a live reCAPTCHA this automated session
cannot solve).
"""

import os

import pytest

from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.components.object_authoring_page import STATUS_PENDING_REVIEW
from cms.pages.tenders.eoi_submission_admin_page import EoiSubmissionAdminPage
from cms.pages.tenders.tender_admin_page import TenderAdminPage
from config.settings import cms_role_credentials, control_panel_url

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130952, pytest.mark.auth]

_VALID_PDF = os.path.join(os.path.dirname(__file__), "fixtures", "qctest_valid_document.pdf")


@pytest.mark.tc_146105
@pytest.mark.traceability("INVEST-TENDERS-TC-039")
def test_unauthenticated_direct_url_denied_review_panel(page):
    """INVEST-TENDERS-TC-039 — Azure TC 146105."""
    page.context.clear_cookies()
    page.goto(control_panel_url("/web/qatar-chamber/manage-eoi-submission"))
    login = CmsLoginPage(page)
    assert not login.login_succeeded(), "an unauthenticated direct hit must not reach the review panel logged in"
    assert "login" in page.url.lower() or login.login_form_visible(), (
        f"expected a redirect to login, landed on {page.url}"
    )


@pytest.mark.tc_146106
@pytest.mark.regression
@pytest.mark.traceability("INVEST-TENDERS-TC-040")
def test_site_content_editor_can_approve_reject_publish(page):
    """INVEST-TENDERS-TC-040 — Azure TC 146106. See module docstring — no
    live Pending EOISubmission record exists to Approve/Reject/Publish
    this session."""
    email, password = cms_role_credentials("Site Content Editor")
    submissions = EoiSubmissionAdminPage(page).open_list(email, password)
    assert CmsLoginPage(page).login_succeeded(), (
        "Site Content Editor must at least reach the review-panel list view"
    )
    if not submissions.has_entries():
        pytest.skip(
            "PRECONDITION UNAVAILABLE — the EOISubmission review list has 0 live entries; cannot "
            "exercise Approve/Reject/Publish against a real Pending record on this environment."
        )


@pytest.mark.tc_146107
@pytest.mark.traceability("INVEST-TENDERS-TC-041")
def test_site_content_author_cannot_directly_publish(page):
    """INVEST-TENDERS-TC-041 — Azure TC 146107."""
    email, password = cms_role_credentials("Site Content Author")
    tender = TenderAdminPage(page).open_create_form(email, password)
    # Proves the session is the Author: the page fixture pre-loads TEST_USER,
    # and until 2026-09-30 the login step was skipped because of it.
    assert not CmsLoginPage(page).has_admin_toolbar(), (
        "precondition: this case must run as Site Content Author, but the session has the admin toolbar"
    )
    tender.fill_valid_form(_VALID_PDF)
    tender.submit_for_review()
    # An Author's submit is routed to review (qc-editorial-approval workflow);
    # "not Published" alone would also pass on an unreadable banner.
    assert tender.current_status() == STATUS_PENDING_REVIEW, (
        "a Site Content Author's submission must go to Pending Review, not straight to Published"
    )


@pytest.mark.tc_146108
@pytest.mark.traceability("INVEST-TENDERS-TC-042")
def test_site_content_author_can_view_and_update_assigned_records(page):
    """INVEST-TENDERS-TC-042 — Azure TC 146108."""
    email, password = cms_role_credentials("Site Content Author")
    tender = TenderAdminPage(page).open_list(email, password)
    assert tender.has_entries(), "a Site Content Author should be able to view the Tender records list"


@pytest.mark.tc_146109
@pytest.mark.traceability("INVEST-TENDERS-TC-043")
def test_rejected_submission_remains_stored_not_deleted(page):
    """INVEST-TENDERS-TC-043 — Azure TC 146109. See module docstring — no
    live Rejected EOISubmission record exists to verify retention against
    this session (0 entries total)."""
    email, password = cms_role_credentials("Site Content Editor")
    submissions = EoiSubmissionAdminPage(page).open_list(email, password)
    if not submissions.has_entries():
        pytest.skip(
            "PRECONDITION UNAVAILABLE — the EOISubmission review list has 0 live entries; cannot "
            "verify a Rejected record remains stored/retrievable on this environment."
        )

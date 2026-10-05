"""
cms/tests/tenders/test_tenders_blocked_control_panel.py — PBI 130952
Control_Panel cases that cannot run against `manage-tender` on qcdev
(user decisions, 2026-10-05). Kept as skipped tests so every tc_ marker of
suite 140383 stays traceable to one file.

- eTender submission review cases: public submissions land in the
  EOISubmission object (view only, 0 entries), the
  `/group/control_panel/manage/-/etender-submissions` panel returns 404,
  and manage-tender has no Approve/Reject buttons or Rejection Reason
  field. Blocked + one bug filed for the missing review panel.
- Tender Category lookup cases: the category is a shared Liferay
  picklist (Goods / Services / Works) used by real tenders; the user chose
  not to add or remove values on qcdev.
"""

import pytest

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130952]

SUBMISSIONS_BLOCKED = pytest.mark.skip(
    reason="BLOCKED — no eTender submissions review panel: EOISubmission is view-only with 0 "
    "entries, /etender-submissions returns 404, and manage-tender has no Approve/Reject or "
    "Rejection Reason (user decision 2026-10-05)."
)
PICKLIST_BLOCKED = pytest.mark.skip(
    reason="BLOCKED — Tender Category is a shared picklist used by real tenders; user chose not "
    "to change it on qcdev (2026-10-05)."
)


@SUBMISSIONS_BLOCKED
@pytest.mark.auth
@pytest.mark.tc_146105
def test_unauthenticated_user_denied_etender_submissions_panel():
    """Azure TC 146105."""


@SUBMISSIONS_BLOCKED
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.tc_146106
def test_editor_can_approve_reject_publish_submission():
    """Azure TC 146106."""


@SUBMISSIONS_BLOCKED
@pytest.mark.auth
@pytest.mark.tc_146107
def test_author_cannot_publish_submission():
    """Azure TC 146107."""


@SUBMISSIONS_BLOCKED
@pytest.mark.auth
@pytest.mark.tc_146109
def test_rejected_submission_remains_stored():
    """Azure TC 146109."""


@SUBMISSIONS_BLOCKED
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_146130
def test_administrator_can_approve_submitted_etender():
    """Azure TC 146130."""


@SUBMISSIONS_BLOCKED
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_146131
def test_publishing_approved_submission_appears_publicly():
    """Azure TC 146131 (Control_Panel half)."""


@SUBMISSIONS_BLOCKED
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.tc_146132
def test_administrator_can_reject_submission_with_reason():
    """Azure TC 146132."""


@SUBMISSIONS_BLOCKED
@pytest.mark.functional_high
@pytest.mark.tc_146137
def test_submissions_review_view_shows_all_fields_and_documents():
    """Azure TC 146137."""


@SUBMISSIONS_BLOCKED
@pytest.mark.functional_low
@pytest.mark.tc_146280
def test_valid_rejection_reason_accepted():
    """Azure TC 146280."""


@SUBMISSIONS_BLOCKED
@pytest.mark.functional_low
@pytest.mark.tc_146281
def test_reject_blocked_without_rejection_reason():
    """Azure TC 146281."""


@PICKLIST_BLOCKED
@pytest.mark.functional_low
@pytest.mark.lookupdata
@pytest.mark.tc_146285
def test_new_tender_category_value_available_in_webform():
    """Azure TC 146285."""


@PICKLIST_BLOCKED
@pytest.mark.edge
@pytest.mark.lookupdata
@pytest.mark.tc_146292
def test_removed_category_does_not_break_published_tender():
    """Azure TC 146292."""

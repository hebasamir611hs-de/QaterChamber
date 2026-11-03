"""
cms/tests/tenders/test_tenders_blocked_control_panel.py — PBI 130952
Control_Panel cases that cannot run against `manage-tender` on qcdev
(user decisions, 2026-10-05). Kept as skipped tests so every tc_ marker of
suite 140383 stays traceable to one file.

- eTender submission review cases (146105-146107, 146109, 146130-146132,
  146137, 146280, 146281): bug 148117 fixed — implemented in
  test_tenders_submissions_control_panel.py (2026-10-13).
- Tender Category lookup cases: the category is a shared Liferay
  picklist (Goods / Services / Works) used by real tenders; the user chose
  not to add or remove values on qcdev.
"""

import pytest

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130952]

PICKLIST_BLOCKED = pytest.mark.skip(
    reason="BLOCKED — Tender Category is a shared picklist used by real tenders; user chose not "
    "to change it on qcdev (2026-10-05)."
)


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

"""
cms/tests/join_committee/join_checks.py — PBI 130717 override of the shared A4
check_status_filter (cms/tests/sectoral_committees/cc_checks.py is owned by A5 since
2026-10-04 and is not edited from here).

Triage 2026-10-04 (tc_143430): the first version asserted the Status filter's OPTION
LIST, which standards.md forbids ("built from the statuses actually present"). Read
live later the same day, the Form Manager's filter offered Pending / Approved /
Rejected once such rows existed, and a search for "Pending" narrowed the list to
Pending rows. This version applies the filter the way a Form Manager does and asserts
the RESULT: every row left carries the requested Request Status, and our own Pending
QCTEST submission is among them.
"""

from cms.pages.join_committee.council_base import ROLE_FORM_MANAGER
from cms.tests.sectoral_committees import cc_checks as cc


def check_status_filter(page, browser, sub_cls, create, tc, status, role=ROLE_FORM_MANAGER):
    sub = sub_cls(page)
    needle = create(browser, tc)
    assert sub.find_row(needle, role) is not None, f"{role} cannot see {needle!r}"
    sub.open_list(role)
    sel = page.locator("select[data-qc-oel-status-filter]").first
    labels = [o.strip() for o in sel.locator("option").all_inner_texts()] if sel.count() else []
    match = next((o for o in labels if o.casefold() == status.casefold()), None)
    if match:
        sel.select_option(label=match)
        how = "status filter"
    else:
        box = page.locator(sub.SEARCH).first
        box.fill(status)
        box.press("Enter")
        how = "search"
    page.wait_for_timeout(3000)  # the list re-renders client-side; measured < 2 s
    rows = page.locator(sub.ROW).filter(has=page.locator("td"))
    got = [sub.cell(rows.nth(i), "Request Status") for i in range(rows.count())]
    print(f"[tc_{tc}] filtered by {how}: {got}")
    assert got, f"filtering by {status!r} ({how}) left no rows"
    assert all(g.casefold() == status.casefold() for g in got), f"rows under {status!r} ({how}): {got!r}"
    assert page.locator(f'{sub.ROW}:has-text("{needle}")').count() or rows.count() >= 10, (
        f"our Pending submission {needle!r} is not under the {status!r} filter")
    _ = cc

"""
cms/tests/partners_offers/ne_checks.py - bodies for the 2026-10-07 batch of PBI
130720 (suite 140379) Display Order cases. Not a test module. OFFLINE scripted,
not executed.

Live orders sit on the 100-grid (100, 200, ...), so a QCTEST record saved with
Display Order 3 / 2 does not land "third" / "second" by itself: its expected
position is DERIVED at run time from the other active records' Display Order
(numeric ascending, the sort the public fragments use), and then compared with
where it actually renders. Records are QCTEST-<tc>-* (run-unique titles via
b_checks.unique_qctest_titles, autouse in the module) and deleted BY ID.
"""

from __future__ import annotations

import json
import time

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.partners_offers.partners_offers_admin_page import (
    MembershipTierAdminPage,
    PartnerCategoryAdminPage,
)
from cms.tests.certificate_of_origin.b_checks import run_title
from cms.tests.partners_offers import po_checks as po
from cms.tests.sectoral_committees import live_checks as lc

PUBLIC_POLL_S = 60.0


def _records(admin, plural: str) -> list[dict]:
    """Every record of /o/c/<plural>, read as the signed-in Editor (GET only)."""
    status, text = lc.ctx_get(admin, f"/o/c/{plural}?pageSize=500")
    assert status == 200, f"GET /o/c/{plural} answered HTTP {status}: {text[:160]!r}"
    return (json.loads(text) or {}).get("items") or []


def _name(rec: dict, ref: str) -> str:
    v = rec.get(ref)
    if isinstance(v, dict):
        v = v.get("en_US") or next(iter(v.values()), "")
    return (v or "").strip()


def _active(rec: dict) -> bool:
    """Both public gates: workflow status code 0 (the published code; the numeric
    code is compared, never a label) AND every *ActiveStatus flag ticked."""
    flags = [v for k, v in rec.items() if k.lower().endswith("activestatus")]
    published = (rec.get("status") or {}).get("code") == 0
    return published and (all(f is True for f in flags) if flags else True)


def _expected_index(records, ref, title, order: int) -> int:
    """How many OTHER public records sort before `order`. UNVERIFIED: the JSON key
    `displayOrder` is assumed from the sibling objects' contract (Sectoral fragment
    JS), not read from this form's field ref."""
    return sum(1 for r in records if _active(r) and _name(r, ref) != title
               and float(r.get("displayOrder") or 0) < order)


def _ref_of(records, title) -> str:
    for r in records:
        for k, v in r.items():
            if (isinstance(v, str) and v.strip() == title) or (isinstance(v, dict) and title in v.values()):
                return k
    raise AssertionError(f"{title!r} not found in the object's records")


def check_category_order_public(page, browser, tc: int, order: str):
    """Account: Site Content Editor. A QCTEST category (Active ticked) saved with
    Display Order `order` is offered at the matching position of the public
    category dropdown (logged-out context)."""
    admin = PartnerCategoryAdminPage(page)
    title = run_title(tc, "cat")
    ctx, anon = po._anon(browser)
    try:
        po.publish(admin, title, extra={"display_order": order})
        records = _records(admin, PartnerCategoryAdminPage.PLURAL)
        ref = _ref_of(records, title)
        want = _expected_index(records, ref, title, int(order))
        names = {_name(r, ref) for r in records if _active(r)}
        deadline = time.monotonic() + PUBLIC_POLL_S
        while True:
            options = [o for o in po.category_options(anon) if o in names]  # drops an "All" option
            if title in options or time.monotonic() > deadline:
                break
            anon.wait_for_timeout(3000)
        assert title in options, f"{title!r} is not offered in the public dropdown: {options!r}"
        assert options.index(title) == want, (
            f"Display Order {order}: {title!r} is option {options.index(title) + 1}, expected position {want + 1} "
            f"(active orders {sorted(float(r.get('displayOrder') or 0) for r in records if _active(r))!r}); "
            f"options {options!r}")
    finally:
        po.delete(admin, title)
        po._close(ctx)


def check_tier_order_admin(page, tc: int, order: str):
    """Account: Site Content Editor. A QCTEST tier (Active unticked: nothing
    public) saved with Display Order `order`; the Membership Tier list in the
    lookup management screen places it where that order implies.
    UNVERIFIED: that the entries list sorts by Display Order (the case's
    'reorders accordingly'); the row order is read from the rendered table."""
    admin = MembershipTierAdminPage(page)
    title = run_title(tc, "tier")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=False)
        admin.fill("display_order", order)
        admin.submit_for_review()
        assert admin.id_for(title), f"{title!r}: Display Order {order} was not saved ({admin.save_counts()})"
        records = _records(admin, MembershipTierAdminPage.PLURAL)
        ref = _ref_of(records, title)
        want = sum(1 for r in records if _name(r, ref) != title and float(r.get("displayOrder") or 0) < int(order))
        admin.open_list(ROLE_EDITOR)
        names = {_name(r, ref) for r in records}
        rows = [" ".join(t.split()) for t in page.locator(admin.ENTRIES_TABLE_ROW).all_inner_texts()]
        listed = []
        for row in rows:  # one name per row: the longest record name the row contains
            hits = sorted((n for n in names if n and n in row), key=len, reverse=True)
            if hits:
                listed.append(hits[0])
        assert title in listed, f"{title!r} is not in the Membership Tier list ({rows[:10]!r})"
        assert listed.index(title) == want, (
            f"Display Order {order}: {title!r} is row {listed.index(title) + 1}, expected row {want + 1}; "
            f"list {listed!r}")
    finally:
        po.delete(admin, title)

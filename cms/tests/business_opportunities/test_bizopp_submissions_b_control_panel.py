"""
cms/tests/business_opportunities/test_bizopp_submissions_b_control_panel.py —
PBI 130697 (Business Opportunities), Azure suite 140361 in plan 137724:
Opportunity Submissions review, Opportunity Inquiries review, roles.
Re-scripted 2026-10-13 by ready-bug retest agent C (data prefix QCTEST-R30-C-)
after the fix for bug 149526 built the review actions.

What exists live (2026-10-13, see opportunity_submissions_admin_page.py):
  - Public intake works (HTTP 200 + reference). Records are created as
    "Website Visitor" (bug 149529 fix).
  - manage-opportunity-submission: columns Reference / Opportunity / Company /
    Email / Status (Pending|Approved|Rejected) / Submission date; row actions
    Approve (confirm) / Reject (prompt, reason required) / History.
  - manage-opportunity-inquiry: columns Reference / Inquirer / Email / Company /
    Opportunity / Status / Submission date; Mark In Progress -> Mark Completed /
    Close; History.
  - Reviewer role = Form Manager (user decision 2026-10-07).

Data: module fixtures create TWO QCTEST submissions (one to approve, one to
reject) and FOUR QCTEST inquiries through the public forms (logged out). Every
review click is guarded to OUR row (exact QCTEST name in the row, confirm must
name the row's ERC). Nothing is deleted: records stay as QCTEST rows (RULES:
prefer leaving over deleting). No real row is ever acted on.

Duplicates share one test with a tc_ marker per ID (brief rule 12).
"""

from __future__ import annotations

import json
import re as _re
from datetime import datetime
from pathlib import Path

import allure
import pytest

from cms.pages.business_opportunities.opportunity_submissions_admin_page import (
    INQUIRY_SLUG,
    OBJECT_LABELS,
    QCTEST_PREFIX,
    ROLE_ADMIN,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_FORM_MANAGER,
    ROLE_USER_IDS,
    SUBMISSION_SLUG,
    OpportunityReviewAdminPage,
    PublicOpportunityInquiryForm,
    PublicOpportunitySubmissionForm,
)
from core.web.browser import new_context

STAMP = datetime.now().strftime("%m%d%H%M%S")
FIXTURES = Path(__file__).resolve().parent / "fixtures"
IMAGE = str(FIXTURES / "b_qctest_banner.jpg")
PDF = str(FIXTURES / "b_qctest_document.pdf")
QCTEST_EMAIL = "qctest-r32-n@example.com"
# A real, Active opportunity used only as the target of the inquiry modal (never edited).
INQUIRY_TARGET_CODE = "QC-BIZOPP-130697-04"

EPIC = "Business Gateway"
FEATURE = "Business Opportunities — Submissions & Inquiries review (Control Panel)"
BASE_MARKS = (pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130697)
pytestmark = [*BASE_MARKS, pytest.mark.xdist_group("bizopp_cms_b")]

NO_MAILBOX = ("BLOCKED — the email subject/body is the point of this case and there is no mailbox access. "
              "The intake step itself now works (HTTP 200 + reference number, see tc_143395 / tc_143391), "
              "but the admin notification email cannot be read.")


# ===========================================================================
# Fixtures
# ===========================================================================
def _auth_free_page(browser):
    ctx = new_context(browser, use_auth_state=False)
    return ctx, ctx.new_page()


def _signed_in(browser, role):
    ctx, page = _auth_free_page(browser)
    admin = OpportunityReviewAdminPage(page)
    outcome = admin.login_as_role(role)
    return ctx, admin, outcome


@pytest.fixture(scope="module")
def qctest_intake(browser):
    """ONE QCTEST submission + ONE QCTEST inquiry through the public forms, located
    by captured entry id and exact name; never deleted (RULES ready30)."""
    data: dict = {"submission": {}, "inquiry": {}, "cleanup": []}
    sub_name = f"{QCTEST_PREFIX}SUB-{STAMP}"
    inq_name = f"{QCTEST_PREFIX}INQ-{STAMP}"
    inq_company = f"{QCTEST_PREFIX}Company-{STAMP}"

    ctx, admin, _ = _signed_in(browser, ROLE_FORM_MANAGER)
    try:
        admin.open_manage(SUBMISSION_SLUG)
        sub_before = set(admin.entry_ids())
    finally:
        ctx.close()

    ctx, page = _auth_free_page(browser)  # logged-out visitor
    try:
        sub = PublicOpportunitySubmissionForm(page).open_form().fill_qctest(sub_name, IMAGE, PDF, QCTEST_EMAIL).submit()
        data["submission"] = {"name": sub_name, "outcome": sub,
                              "public_evidence": OpportunityReviewAdminPage(page).evidence("intake_public_submission")}
        inq = (PublicOpportunityInquiryForm(page).open_modal(INQUIRY_TARGET_CODE)
               .fill_qctest(inq_name, QCTEST_EMAIL, inq_company, "QCTEST R32 agent N inquiry.").submit())
        data["inquiry"] = {"name": inq_name, "company": inq_company, "outcome": inq,
                           "public_evidence": OpportunityReviewAdminPage(page).evidence("intake_public_inquiry")}
    finally:
        ctx.close()

    ctx, admin, _ = _signed_in(browser, ROLE_FORM_MANAGER)
    try:
        for kind, slug in (("submission", SUBMISSION_SLUG), ("inquiry", INQUIRY_SLUG)):
            item = data[kind]
            if item["outcome"].get("id"):
                admin.wait_for_entry(slug, item["outcome"]["id"])
            else:
                admin.open_manage(slug)
            item["headers"] = admin.list_headers()
            ids = admin.entry_ids()
            candidates = ([item["outcome"]["id"]] if item["outcome"].get("id")
                          else [i for i in ids if i not in sub_before]) if item["outcome"]["success"] else []
            for entry_id in candidates:
                if entry_id not in ids:
                    continue
                admin.open_manage(slug)
                view = admin.view_entry(entry_id)
                if admin.entry_name(view) == item["name"]:
                    item.update(id=entry_id, view=view)
                    item["view_evidence"] = admin.evidence(f"FormManager_{slug}_view_{entry_id}")
                    admin.open_manage(slug)
                    item["row"] = admin.row_by_id(entry_id)
                    break
            item.setdefault("row", None)
            item.setdefault("view", {"fields": {}, "lines": [], "controls": {}})
            item["list_evidence"] = admin.evidence(f"FormManager_{slug}_list")
        # Does either QCTEST item show up in the OTHER list? (cross-landing check, by id)
        admin.open_manage(INQUIRY_SLUG)
        data["submission"]["in_inquiry_list"] = data["submission"].get("id", "-") in admin.entry_ids()
        admin.open_manage(SUBMISSION_SLUG)
        data["inquiry"]["in_submission_list"] = data["inquiry"].get("id", "-") in admin.entry_ids()
    finally:
        ctx.close()
    allure.attach(json.dumps(data, indent=2, ensure_ascii=False), name="QCTEST intake (live)",
                  attachment_type=allure.attachment_type.JSON)

    yield data
    # No deletion (RULES ready30: leave QCTEST records rather than delete).


@pytest.fixture(scope="module")
def extra_intake(browser):
    """One more QCTEST submission (to approve) and three QCTEST inquiries, created
    logged out; ids come from the POST response (verified on the row by name)."""
    out: dict = {}
    ctx, page = _auth_free_page(browser)
    try:
        name = f"{QCTEST_PREFIX}SUBA-{STAMP}"
        res = PublicOpportunitySubmissionForm(page).open_form().fill_qctest(name, IMAGE, PDF, QCTEST_EMAIL).submit()
        out["sub_approve"] = {"name": name, "outcome": res, "id": res.get("id")}
        for n in (1, 2, 3, 4, 5):  # inq4: 143282 (Administrator), inq5: 143280 (own inquiry)
            name = f"{QCTEST_PREFIX}INQ{n}-{STAMP}"
            res = (PublicOpportunityInquiryForm(page).open_modal(INQUIRY_TARGET_CODE)
                   .fill_qctest(name, QCTEST_EMAIL, f"{QCTEST_PREFIX}Company-{STAMP}", f"QCTEST R32 N inquiry {n}.")
                   .submit())
            out[f"inq{n}"] = {"name": name, "outcome": res, "id": res.get("id")}
    finally:
        ctx.close()
    allure.attach(json.dumps(out, indent=2, ensure_ascii=False), name="QCTEST extra intake",
                  attachment_type=allure.attachment_type.JSON)
    for key, item in out.items():
        assert item["outcome"]["success"] and item["id"], f"Precondition: public intake for {key} failed: {item}"
    return out


@pytest.fixture(scope="module")
def reviewer(browser):
    """ONE signed-in Form Manager session (the reviewer role) for the module."""
    ctx, admin, outcome = _signed_in(browser, ROLE_FORM_MANAGER)
    assert outcome == "ok", f"Precondition: the Form Manager could not sign in ({outcome})"
    admin.open_manage(SUBMISSION_SLUG)
    user_id = admin.signed_in_user()[0]
    assert user_id == ROLE_USER_IDS[ROLE_FORM_MANAGER], (
        f"Precondition: signed in as user {user_id!r}, not the Form Manager ({ROLE_USER_IDS[ROLE_FORM_MANAGER]})")
    yield admin
    ctx.close()


@pytest.fixture(scope="module")
def rejected_sub(reviewer, qctest_intake):
    """Reject the intake submission: first with an EMPTY reason (must be refused), then with a reason."""
    item = qctest_intake["submission"]
    assert item.get("id"), "Precondition: the QCTEST submission was not located"
    empty = reviewer.review_action(SUBMISSION_SLUG, item["id"], "Reject", item["name"], reason="")
    empty_ev = reviewer.evidence("reject_empty_reason_result")
    with_reason = reviewer.review_action(SUBMISSION_SLUG, item["id"], "Reject", item["name"], reason=REJECT_REASON)
    reason_ev = reviewer.evidence("reject_with_reason_row")
    data = {"item": {k: item[k] for k in ("name", "id")}, "empty": empty, "with_reason": with_reason,
            "evidence": [empty_ev, reason_ev]}
    allure.attach(json.dumps(data, indent=2, ensure_ascii=False, default=str), name="reject (live)",
                  attachment_type=allure.attachment_type.JSON)
    return data


@pytest.fixture(scope="module")
def approved_sub(reviewer, extra_intake):
    item = extra_intake["sub_approve"]
    res = reviewer.review_action(SUBMISSION_SLUG, item["id"], "Approve", item["name"])
    ev = reviewer.evidence("approve_row")
    data = {"item": item, "approve": res, "evidence": ev}
    allure.attach(json.dumps(data, indent=2, ensure_ascii=False, default=str), name="approve (live)",
                  attachment_type=allure.attachment_type.JSON)
    return data


# ===========================================================================
# Live: intake lands in the panel (P2) — 143395
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission intake")
@allure.title("A new public Opportunity Submission appears in the Opportunity Submissions panel as Pending")
@pytest.mark.functional_low
@pytest.mark.tc_143395
def test_new_public_submission_appears_pending(qctest_intake):
    item = qctest_intake["submission"]
    outcome = item["outcome"]
    assert outcome["success"] and outcome["reference"], (
        f"Step 1: the submission did not complete — POST /submissions answered HTTP {outcome['http']}, "
        f"the form shows {outcome['message']!r} (expected the success screen with a reference number)")
    assert item.get("id"), f"Step 2: {item['name']!r} was not found in manage-{SUBMISSION_SLUG} (Form Manager)"
    assert not item["in_inquiry_list"], f"Step 2: the submission (id {item['id']}) also shows in manage-{INQUIRY_SLUG}"
    stored_status = item["view"]["fields"].get("Submission Status")
    assert stored_status == "Pending", f"Step 2: the stored Submission Status is {stored_status!r}, not Pending"
    creator = item["view"]["fields"].get("Creator")
    assert creator == "Website Visitor", (
        f"Step 2: the logged-out visitor's submission is recorded with Creator {creator!r}, not the guest "
        f"'Website Visitor' (bug 149529)")
    row = item["row"] or {}
    problems = []
    row_text = " ".join(row.get("cells", []))
    if "pending" not in row_text.lower():
        problems.append(f"the list row shows status {row.get('cells', ['', '?'])[1]!r} (the workflow status), "
                        f"not 'Pending' — the Submission Status 'Pending' is visible only in the View modal")
    if item["name"] not in row_text:
        problems.append(f"the list row identifies the entry by its ERC {row.get('cells', ['?'])[0]!r}; no submitter "
                        f"/ opportunity details (name {item['name']!r}, company, contact) are shown "
                        f"(columns {item['headers']})")
    assert not problems, "Step 2: " + "; ".join(problems) + f". Evidence: {item['list_evidence']}"


# ===========================================================================
# Live: Submission review permissions (P1) — 143277
# User decision 2026-10-13 (bug 149527 closed Not a Bug): per the PBI 130697 Permissions
# table the Site Content Editor MAY open and review opportunity submissions; the Site
# Content Author must be denied.
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Roles")
@allure.title("The Site Content Editor can open and review submissions; the Site Content Author is denied")
@pytest.mark.auth
@pytest.mark.tc_143277
def test_editor_denied_submission_review(browser, qctest_intake):
    """Name kept for traceability; asserts the PBI permission table (user decision 2026-10-13).
    Read-only: the Editor's review actions are checked as offered, nothing is clicked."""
    own_id = qctest_intake["submission"].get("id")
    assert own_id, "Precondition: the QCTEST submission was not located"
    observed: dict = {}
    for role in (ROLE_EDITOR, ROLE_AUTHOR):
        ctx, page = _auth_free_page(browser)
        try:
            admin = OpportunityReviewAdminPage(page)
            assert admin.login_as_role(role) == "ok", f"Step 1: the {role} could not sign in"
            http = admin.open_manage(SUBMISSION_SLUG)
            user_id = admin.signed_in_user()[0]
            assert user_id == ROLE_USER_IDS[role], f"signed in as {user_id!r}, not the {role}"
            body = admin.body_text()
            observed[role] = {
                "http": http,
                "access_denied": "Access Denied" in body,
                "rows": len(admin.entry_ids()),
                "own_row_actions": ((admin.wait_for_entry(SUBMISSION_SLUG, own_id, tries=3) or {}).get("actions")
                                    if role == ROLE_EDITOR else None),
                "evidence": admin.evidence(f"143277_{role.replace(' ', '_')}_manage_opportunity_submission"),
            }
        finally:
            ctx.close()
    allure.attach(json.dumps(observed, indent=2), name="Submission access by role (live)",
                  attachment_type=allure.attachment_type.JSON)
    ed, au = observed[ROLE_EDITOR], observed[ROLE_AUTHOR]
    assert not ed["access_denied"] and ed["rows"], f"Step 2: the Editor cannot open the submission list: {ed}"
    assert ed["own_row_actions"] and {"View", "Approve", "Reject"} <= set(ed["own_row_actions"]), (
        f"Step 3: the Editor is not offered View / Approve / Reject on the Pending QCTEST row: {ed}")
    assert au["access_denied"] and not au["rows"], f"Step 4: the Site Content Author is not denied: {au}"


# ===========================================================================
# Live: inquiry list columns (P2) — 143391
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Inquiry review")
@allure.title("The Inquiry panel list shows Inquirer Name, Email, Company, Opportunity, Status and Date")
@pytest.mark.functional_low
@pytest.mark.tc_143391
def test_inquiry_list_columns(qctest_intake):
    item = qctest_intake["inquiry"]
    outcome = item["outcome"]
    assert outcome["success"], (f"Precondition: the public inquiry POST answered HTTP {outcome['http']}, the modal "
                                f"shows {outcome['message']!r}")
    assert item.get("id"), f"Step 2: {item['name']!r} was not found in manage-{INQUIRY_SLUG} (Form Manager)"
    assert not item["in_submission_list"], f"the inquiry (id {item['id']}) also shows in manage-{SUBMISSION_SLUG}"
    headers = item["headers"]
    # Healed 2026-10-13 (ready30 C): the fix for bug 149528 labels the Inquirer Name column "INQUIRER".
    expected = {"Inquirer Name": ("name", "inquirer"), "Email": ("email",), "Company": ("company",),
                "Opportunity": ("opportunity",), "Status": ("status",), "Date": ("date",)}
    missing = [h for h, keys in expected.items() if not any(k in t.lower() for t in headers for k in keys)]
    row_text = " ".join((item["row"] or {}).get("cells", []))
    absent = [v for v in (item["name"], QCTEST_EMAIL, item["company"], INQUIRY_TARGET_CODE, "Pending")
              if v.lower() not in row_text.lower()]
    assert not (missing or absent), (
        f"Step 2: the list columns are {headers!r} (missing {missing!r}); our inquiry's row reads {row_text!r} and "
        f"lacks {absent!r} (those values — Inquiry Status {item['view']['fields'].get('Inquiry Status')!r} — are "
        f"visible only in the View modal). Evidence: {item['list_evidence']}")


# ===========================================================================
# Submission review (live since the fix for bug 149526, 2026-10-13)
# ===========================================================================
REJECT_REASON = "QCTEST R32 N Duplicate submission"
MSG_REASON_REQUIRED = "A rejection reason is required."
MSG_APPROVED = "The opportunity submission has been approved."
MSG_REJECTED = "The opportunity submission has been rejected."


def _notice_has(result: dict, text: str) -> bool:
    return any(text in n for n in result.get("notices", [])) or any(text in d for d in result.get("dialogs", []))


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Approving a Pending submission sets it Approved / eligible to publish (and notifies the submitter)")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143226
@pytest.mark.tc_143396
def test_approve_pending_submission(approved_sub):
    """143226 (QC Admin Reviewer) and 143396 — run as the Form Manager.
    NOTE: the submitter-notification email step (143226) is NOT verified — no mailbox access."""
    res = approved_sub["approve"]
    assert res["offered"], f"Step 2: no Approve action on the Pending QCTEST row (actions {res['actions']})"
    assert any(d.startswith("confirm") for d in res["dialogs"]), f"Step 2: Approve asked no confirmation: {res['dialogs']}"
    assert _notice_has(res, MSG_APPROVED), f"Step 3: no {MSG_APPROVED!r} message (seen {res['notices']} / {res['dialogs']})"
    assert OpportunityReviewAdminPage.row_status(res["row"]) == "APPROVED", (
        f"Step 3: the row status is {OpportunityReviewAdminPage.row_status(res['row'])!r}, not Approved. "
        f"Evidence: {approved_sub['evidence']}")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Rejecting a Pending submission with a reason sets it Rejected and stores the reason")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143198
@pytest.mark.tc_143227
@pytest.mark.tc_143398
def test_reject_submission_with_reason(rejected_sub, reviewer):
    """143198 / 143227 / 143398.
    NOTE: the rejection-email step (143227, 143398) is NOT verified — no mailbox access."""
    res = rejected_sub["with_reason"]
    assert res["offered"], f"Step 2: no Reject action on the Pending QCTEST row (actions {res['actions']})"
    assert _notice_has(res, MSG_REJECTED), f"Step 3: no {MSG_REJECTED!r} message (seen {res['notices']} / {res['dialogs']})"
    assert OpportunityReviewAdminPage.row_status(res["row"]) == "REJECTED", (
        f"Step 3: the row status is {OpportunityReviewAdminPage.row_status(res['row'])!r}, not Rejected")
    view = reviewer.view_entry(rejected_sub["item"]["id"])
    reviewer.open_manage(SUBMISSION_SLUG)
    assert any(REJECT_REASON in line for line in view["lines"]), (
        f"Step 4: the View dialog does not show the Rejection Reason {REJECT_REASON!r}: {view['fields']}")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Rejecting a submission without a Rejection Reason is blocked and it stays Pending")
@pytest.mark.functional_low
@pytest.mark.tc_143199
@pytest.mark.tc_143399
def test_reject_without_reason_blocked(rejected_sub):
    res = rejected_sub["empty"]
    assert res["offered"], f"Step 2: no Reject action on the Pending QCTEST row (actions {res['actions']})"
    assert _notice_has(res, MSG_REASON_REQUIRED), (
        f"Step 3: an empty reason was not refused with {MSG_REASON_REQUIRED!r} (dialogs {res['dialogs']}, "
        f"notices {res['notices']})")
    assert OpportunityReviewAdminPage.row_status(res["row"]) == "PENDING", (
        f"Step 4: after an empty-reason Reject the row is {OpportunityReviewAdminPage.row_status(res['row'])!r}, not Pending")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Approving a Pending submission publishes it as a Business Opportunity in the Active tab")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_143285
def test_approve_publishes_business_opportunity(browser, approved_sub):
    """Healed 2026-10-14 (ready32 N, bug 150023 fix): Approve (Form Manager) is followed by the
    Editor's "Publish as Opportunity", which creates the Business Opportunity pre-filled from the
    submission as a Draft. The final Publish -> public Active tab step needs the editor to add
    the investment range / hero banner / archive date by hand and is not automated here."""
    assert OpportunityReviewAdminPage.row_status(approved_sub["approve"]["row"]) == "APPROVED", "Precondition: not Approved"
    name = approved_sub["item"]["name"]
    ctx, admin, _ = _signed_in(browser, ROLE_EDITOR)
    try:
        res = admin.publish_as_opportunity(approved_sub["item"]["id"], name)
        ev = admin.evidence("143285_business_opportunity_from_submission")
    finally:
        ctx.close()
    allure.attach(json.dumps({k: v for k, v in res.items() if k != "body"}, indent=2, ensure_ascii=False),
                  name="publish as opportunity (live)", attachment_type=allure.attachment_type.JSON)
    assert "editEntry=QC-BO-FROM-" in res["url"], (
        f"Step 4: 'Publish as Opportunity' did not open a Business Opportunity created from the submission "
        f"(url {res['url']!r}, dialogs {res['dialogs']}, POST {res['posts']}, actions {res.get('actions')}). Evidence: {ev}")
    assert res["title_value"] == name, (
        f"Step 4: the new Business Opportunity is not pre-filled with the submission title "
        f"(Opportunity Title {res['title_value']!r}, expected {name!r}). Evidence: {ev}")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("A rejected submission stays stored (not deleted) with status Rejected")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.tc_143286
def test_rejected_submission_kept(rejected_sub, reviewer):
    reviewer.open_manage(SUBMISSION_SLUG)
    row = reviewer.row_by_id(rejected_sub["item"]["id"])
    assert row, f"Step 3: the rejected submission {rejected_sub['item']['id']} is no longer listed"
    assert OpportunityReviewAdminPage.row_status(row) == "REJECTED", f"Step 3: row status {row['cells']}"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("A rejected submission creates no Business Opportunity record and no public card")
@pytest.mark.functional_low
@pytest.mark.tc_143400
def test_rejected_submission_creates_no_record(browser, rejected_sub):
    """Implemented 2026-10-15 (ready32 N): Approve -> "Publish as Opportunity" now exists (bug 150023),
    so absence after Reject is meaningful. Checked as the Editor (who is offered the action):
    the Rejected row offers no "Publish as Opportunity" and no QC-BO-FROM-<erc> record exists."""
    assert OpportunityReviewAdminPage.row_status(rejected_sub["with_reason"]["row"]) == "REJECTED", "Precondition"
    ctx, admin, _ = _signed_in(browser, ROLE_EDITOR)
    try:
        admin.open_manage(SUBMISSION_SLUG)
        row = admin.row_by_id(rejected_sub["item"]["id"])
        ev1 = admin.evidence("143400_rejected_row_actions_editor")
        records = admin.opportunity_record_titles()
        ev2 = admin.evidence("143400_records_after_reject")
    finally:
        ctx.close()
    assert row, f"Precondition: the rejected submission is not listed for the Editor. Evidence: {ev1}"
    erc = row["cells"][0]
    assert "Publish as Opportunity" not in row["actions"], (
        f"Step 2: the Rejected submission offers 'Publish as Opportunity' (row actions {row['actions']}). Evidence: {ev1}")
    assert f"QC-BO-FROM-{erc}" not in records and rejected_sub["item"]["name"] not in records, (
        f"Step 3: a Business Opportunity record exists for the rejected submission ({erc}). Evidence: {ev2}")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Rejecting an already Approved submission is blocked as an invalid transition")
@pytest.mark.edge
@pytest.mark.tc_143243
@pytest.mark.xfail(strict=False, reason="USER DECISION (2026-10-13): an Approved row offering Reject is NOT a bug; "
                   "kept as written for traceability, expected to fail while the product allows Approved -> Rejected.")
def test_reject_approved_submission_blocked(approved_sub, reviewer):
    """Read-only check: the Approved row must not offer Reject (nothing is clicked).
    NOTE: the QA owner decided the Approved -> Reject offer is acceptable (not a bug), hence xfail."""
    reviewer.open_manage(SUBMISSION_SLUG)
    row = reviewer.row_by_id(approved_sub["item"]["id"])
    assert OpportunityReviewAdminPage.row_status(row) == "APPROVED", f"Precondition: row {row}"
    ev = reviewer.evidence("143243_approved_row_actions")
    assert "Reject" not in row["actions"], (
        f"Step 2: the Approved submission still offers Reject (row actions {row['actions']}) — Approved -> Rejected "
        f"is not a transition in the PBI's Status Workflow (Pending -> Approved / Rejected). Evidence: {ev}")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("An Approved submission can be published as a live Business Opportunity")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143397
def test_publish_approved_submission(browser, approved_sub):
    """Healed 2026-10-14 (ready32 N, bug 150023 fix): the action is offered to the Editor /
    Administrator (who publish site content), not to the Form Manager; checked as the Administrator."""
    ctx, admin, _ = _signed_in(browser, ROLE_ADMIN)
    try:
        admin.open_manage(SUBMISSION_SLUG)
        row = admin.row_by_id(approved_sub["item"]["id"])
        ev = admin.evidence("143397_approved_row_actions_admin")
    finally:
        ctx.close()
    assert row and "Publish as Opportunity" in row["actions"], (
        f"Step 2: the Approved submission offers no 'Publish as Opportunity' action to the Administrator "
        f"(row {row}). Evidence: {ev}")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Approving a submission records actor, action and timestamp in the History / Audit Log")
@pytest.mark.functional_low
@pytest.mark.tc_143401
def test_approve_recorded_in_history(approved_sub, reviewer):
    text = reviewer.history_text(SUBMISSION_SLUG, approved_sub["item"]["id"])
    ev = reviewer.evidence("143401_history_approve")
    assert "FormsManager" in text.replace(" ", "") and "approved" in text, (
        f"Step 3: History does not show the Form Manager's approval: {text!r}. Evidence: {ev}")
    assert _re.search(r"\d{1,4}[/.-]\d{1,2}[/.-]\d{2,4}\D{1,5}\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}T?\s*\d{1,2}:\d{2}", text), (
        f"Step 3: no date + time in History: {text!r}")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Rejecting a submission records the action and reason in the History / Audit Log")
@pytest.mark.functional_low
@pytest.mark.tc_143402
def test_reject_recorded_in_history(rejected_sub, reviewer):
    text = reviewer.history_text(SUBMISSION_SLUG, rejected_sub["item"]["id"])
    ev = reviewer.evidence("143402_history_reject")
    assert "rejected" in text and REJECT_REASON in text, (
        f"Step 3: History does not show the rejection and its reason: {text!r}. Evidence: {ev}")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Direct create-and-publish works; Approve again on an Approved submission is blocked")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143405
def test_direct_publish_and_reapprove_blocked(approved_sub, reviewer):
    """NOTE: judges STEP 4 ONLY (Approve not offered again on an Approved submission). Steps 1-3
    (direct create + publish of a record) are NOT run here (record-form flow, Agent A's suite)."""
    reviewer.open_manage(SUBMISSION_SLUG)
    row = reviewer.row_by_id(approved_sub["item"]["id"])
    assert OpportunityReviewAdminPage.row_status(row) == "APPROVED", f"Precondition: row {row}"
    assert "Approve" not in row["actions"], f"Step 4: Approve is offered again on an Approved submission: {row['actions']}"


# ===========================================================================
# Inquiry review — run as the Form Manager (the reviewer role)
# ===========================================================================
def _inquiry_step(reviewer, item, title, expected_status, step):
    res = reviewer.review_action(INQUIRY_SLUG, item["id"], title, item["name"])
    ev = reviewer.evidence(f"inquiry_{item['id']}_{title.replace(' ', '_')}")
    assert res["offered"], f"{step}: no {title!r} action on the QCTEST inquiry row (actions {res.get('actions')})"
    status = OpportunityReviewAdminPage.row_status(res["row"])
    assert status == expected_status, (
        f"{step}: after {title!r} the row reads {status!r}, not {expected_status!r} (dialogs {res['dialogs']}, "
        f"writes {res['writes']}). Evidence: {ev}")
    return res


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Inquiry review")
@allure.title("An inquiry moves Pending -> In-progress, and the status persists after reload")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143392
@pytest.mark.tc_143224
@pytest.mark.tc_143394
def test_inquiry_pending_to_in_progress(reviewer, extra_intake):
    """143392 / 143224 (P3 twin) and 143394 (P3, persists after a full reload)."""
    item = extra_intake["inq1"]
    _inquiry_step(reviewer, item, "Mark In Progress", "IN-PROGRESS", "Step 2")
    reviewer.page.reload(wait_until="load")
    reviewer.open_manage(INQUIRY_SLUG)
    assert OpportunityReviewAdminPage.row_status(reviewer.row_by_id(item["id"])) == "IN-PROGRESS", "Step 3: not persisted"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Inquiry review")
@allure.title("An inquiry moves In-progress -> Completed/Closed")
@pytest.mark.functional_low
@pytest.mark.tc_143393
@pytest.mark.tc_143225
def test_inquiry_in_progress_to_completed(reviewer, extra_intake):
    item = extra_intake["inq2"]
    _inquiry_step(reviewer, item, "Mark In Progress", "IN-PROGRESS", "Precondition")
    _inquiry_step(reviewer, item, "Mark Completed", "COMPLETED", "Step 2")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Inquiry review")
@allure.title("An inquiry progresses Pending -> In-progress -> Completed/Closed with each step persisted")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.tc_143287
def test_inquiry_full_status_workflow(reviewer, extra_intake):
    item = extra_intake["inq3"]
    reviewer.open_manage(INQUIRY_SLUG)
    assert OpportunityReviewAdminPage.row_status(reviewer.row_by_id(item["id"])) == "PENDING", "Step 1: not Pending"
    _inquiry_step(reviewer, item, "Mark In Progress", "IN-PROGRESS", "Step 2")
    _inquiry_step(reviewer, item, "Close", "CLOSED", "Step 3")


# ===========================================================================
# Roles
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Roles")
@allure.title("A QC Admin Reviewer (Form Manager) can review/update inquiries and approve/reject submissions")
@pytest.mark.auth
@pytest.mark.tc_143280
def test_qc_admin_reviewer_access(reviewer, approved_sub, extra_intake):
    """Azure TC 143280, run as the Form Manager (user decision 2026-10-07). Step 4 (Approve) is the
    approve_sub fixture's live Approve; step 2 (update an inquiry status) is done here on a fresh inquiry."""
    for slug in (INQUIRY_SLUG, SUBMISSION_SLUG):
        reviewer.open_manage(slug)
        assert reviewer.signed_in_user()[0] == ROLE_USER_IDS[ROLE_FORM_MANAGER], "not signed in as the Form Manager"
        assert reviewer.list_heading_visible(), f"Step 3: the Form Manager cannot open manage-{slug}"
    assert OpportunityReviewAdminPage.row_status(approved_sub["approve"]["row"]) == "APPROVED", "Step 4: Approve failed"
    item = extra_intake["inq5"]  # its own Pending inquiry, stepped here (not relying on 143392)
    _inquiry_step(reviewer, item, "Mark In Progress", "IN-PROGRESS", "Step 2")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Roles")
@allure.title("An Administrator has full access across Opportunity Management, Inquiry and Submission review")
@pytest.mark.auth
@pytest.mark.tc_143282
def test_administrator_full_access(browser, qctest_intake, extra_intake):
    """Azure TC 143282, run as TEST_USER (the Administrator, user decision 2026-10-07).
    Read-only: Publish and the review actions are checked as offered; nothing is clicked."""
    ctx, page = _auth_free_page(browser)
    try:
        admin = OpportunityReviewAdminPage(page)
        assert admin.login_as_role(ROLE_ADMIN) != "auth_failed", "Step 1: TEST_USER could not sign in"
        authoring = admin.authoring_access()
        admin.evidence("Administrator_manage_business_opportunity")
        admin.open_manage(INQUIRY_SLUG)
        inq_row = admin.row_by_id(extra_intake["inq4"]["id"]) or {}  # own Pending inquiry (not shared with 143287)
        admin.evidence("Administrator_manage_opportunity_inquiry")
        admin.open_manage(SUBMISSION_SLUG)
        sub_ids = admin.entry_ids()
        sub_actions = sorted({a for r in admin.list_rows() for a in r["actions"]})
        admin.evidence("Administrator_manage_opportunity_submission")
    finally:
        ctx.close()
    allure.attach(json.dumps({"authoring": authoring, "inq_row": inq_row, "sub_actions": sub_actions}, indent=2),
                  name="Administrator access (live)", attachment_type=allure.attachment_type.JSON)
    assert "Publish" in authoring["form_buttons"] and {"publish", "unpublish"} & set(authoring["row_actions"]), (
        f"Step 2: Opportunity Management offers no Publish to the Administrator: {authoring}")
    assert inq_row, "Step 3: the Administrator does not see the QCTEST inquiry"
    assert {"Mark In Progress", "Mark Completed", "Close"} & set(inq_row.get("actions", [])), (
        f"Step 3: no inquiry status action for the Administrator: {inq_row.get('actions')}")
    assert sub_ids and {"approve", "reject"} <= set(sub_actions), (
        f"Step 4: no Approve/Reject for the Administrator on submissions (row action attrs {sub_actions})")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Notifications")
@allure.title("A new inquiry sends the admin 'New Opportunity Inquiry — {{reference_number}}' email (EN/AR)")
@pytest.mark.functional_low
@pytest.mark.tc_143403
@pytest.mark.skip(reason=NO_MAILBOX)
def test_inquiry_admin_notification_email():
    """Azure TC 143403."""


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Notifications")
@allure.title("A new submission sends the admin 'New Business Opportunity Submission — {{reference_number}}' email (EN/AR)")
@pytest.mark.functional_low
@pytest.mark.tc_143404
@pytest.mark.skip(reason=NO_MAILBOX)
def test_submission_admin_notification_email():
    """Azure TC 143404."""

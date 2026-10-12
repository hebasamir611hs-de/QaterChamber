"""
cms/tests/business_opportunities/test_bizopp_submissions_b_control_panel.py —
PBI 130697 (Business Opportunities), Azure suite 140361 in plan 137724:
Opportunity Submissions review, Opportunity Inquiries review, roles.
Re-run by Agent H on 2026-10-12 (data prefix QCTEST-130697-H-).

What exists live (2026-10-12, see opportunity_submissions_admin_page.py):
  - The public intake WORKS again: POST /o/qc-business-opportunities-api/
    submissions and /inquiries answer HTTP 200 with a reference number. A
    submission lands in `manage-opportunity-submission`, an inquiry in
    `manage-opportunity-inquiry`.
  - Both lists are still "(view only)" Object Authoring lists. Columns are
    ENTRY (ERC UUID) / STATUS (workflow, "PUBLISHED") / LAST MODIFIED / ACTIONS;
    the business status ("Pending") shows only in the read-only View modal.
  - The Form Manager (the cases' "QC Admin Reviewer", user decision) gets only
    View (+ Preview on submissions). No Approve / Reject / Rejection Reason /
    status control / History exists for any role; TEST_USER additionally gets
    Unpublish + Delete, the Editor Unpublish.

So:
  - A module fixture creates ONE QCTEST-130697-H- submission and ONE inquiry
    through the public forms (logged out), locates each by captured entry id
    and verifies the exact name in its View modal; it deletes both at the end,
    as TEST_USER, through `guarded_delete()` (exact name + id + ERC re-checked
    immediately before the click, native confirm accepted only if it names
    that ERC). Nothing else is ever deleted, and no real row is acted on.
  - 143395 / 143391 / 143277 run live and assert the case as written.
  - Every Approve / Reject / status-change case evaluates the live review
    surface (lists + the View modal of our own QCTEST rows) as the Form
    Manager: while no review control exists the case is skipped as BLOCKED
    with the exact reason; if a review control ever appears the case FAILS
    loudly asking to be scripted against it (never runs guessed steps).
  - 143282 runs as TEST_USER (the "Administrator"); 143403 / 143404 are
    email-content cases (no mailbox).

Duplicates share one test with a tc_ marker per ID (brief rule 12).
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import allure
import pytest

from cms.pages.business_opportunities.opportunity_submissions_admin_page import (
    INQUIRY_SLUG,
    OBJECT_LABELS,
    QCTEST_PREFIX,
    REVIEW_ROW_ATTRS,
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_FORM_MANAGER,
    ROLE_USER_IDS,
    SUBMISSION_SLUG,
    OpportunityReviewAdminPage,
    PublicOpportunityInquiryForm,
    PublicOpportunitySubmissionForm,
    _evidence_dir,
)
from core.web.browser import new_context

STAMP = datetime.now().strftime("%m%d%H%M%S")
FIXTURES = Path(__file__).resolve().parent / "fixtures"
IMAGE = str(FIXTURES / "b_qctest_banner.jpg")
PDF = str(FIXTURES / "b_qctest_document.pdf")
QCTEST_EMAIL = "qctest.130697.h@example.com"
# A real, Active opportunity used only as the target of the inquiry modal (never edited).
INQUIRY_TARGET_CODE = "QC-BIZOPP-130697-04"

EPIC = "Business Gateway"
FEATURE = "Business Opportunities — Submissions & Inquiries review (Control Panel)"
BASE_MARKS = (pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130697)
pytestmark = [*BASE_MARKS, pytest.mark.xdist_group("bizopp_cms_b")]

NO_MAILBOX = ("BLOCKED — the email subject/body is the point of this case and there is no mailbox access. "
              "The intake step itself now works (HTTP 200 + reference number, see tc_143395 / tc_143391), "
              "but the admin notification email cannot be read.")
# View-modal buttons that are not review controls (the close icon renders as one glyph).
NON_REVIEW_BUTTONS = {"Close", "close", "×"}


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
    by captured entry id and exact name; guarded-deleted as TEST_USER at the end."""
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
               .fill_qctest(inq_name, QCTEST_EMAIL, inq_company, "QCTEST Agent H inquiry.").submit())
        data["inquiry"] = {"name": inq_name, "company": inq_company, "outcome": inq,
                           "public_evidence": OpportunityReviewAdminPage(page).evidence("intake_public_inquiry")}
    finally:
        ctx.close()

    ctx, admin, _ = _signed_in(browser, ROLE_FORM_MANAGER)
    try:
        for kind, slug in (("submission", SUBMISSION_SLUG), ("inquiry", INQUIRY_SLUG)):
            item = data[kind]
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

    ctx, admin, _ = _signed_in(browser, ROLE_ADMIN)
    try:
        for kind, slug in (("submission", SUBMISSION_SLUG), ("inquiry", INQUIRY_SLUG)):
            item = data[kind]
            if item.get("id"):
                result = admin.guarded_delete(slug, item["id"], item["name"])
                data["cleanup"].append({"kind": kind, "id": item["id"], "name": item["name"], "result": result})
            elif item.get("outcome", {}).get("success"):
                data["cleanup"].append({"kind": kind, "id": None, "name": item["name"],
                                        "result": "NOT deleted: created but not located by id"})
    finally:
        ctx.close()
    os.makedirs(_evidence_dir(), exist_ok=True)
    with open(os.path.join(_evidence_dir(), f"cleanup_{STAMP}.json"), "w", encoding="utf-8") as fh:
        json.dump(data["cleanup"], fh, indent=2, ensure_ascii=False)
    allure.attach(json.dumps(data["cleanup"], indent=2), name="QCTEST cleanup", attachment_type=allure.attachment_type.JSON)


@pytest.fixture(scope="module")
def review_surface(browser, qctest_intake):
    """Read-only live survey of the review surface as the Form Manager (the reviewer role)."""
    survey = _survey(browser, ROLE_FORM_MANAGER, qctest_intake)
    allure.attach(json.dumps(survey, indent=2, ensure_ascii=False), name="review surface (live)",
                  attachment_type=allure.attachment_type.JSON)
    return survey


def _survey(browser, role: str, intake: dict) -> dict:
    ctx, page = _auth_free_page(browser)
    survey: dict = {"role": role, "intake": {k: {"http": intake[k]["outcome"].get("http"),
                                                  "success": intake[k]["outcome"].get("success"),
                                                  "reference": intake[k]["outcome"].get("reference"),
                                                  "id": intake[k].get("id")} for k in ("submission", "inquiry")}}
    try:
        admin = OpportunityReviewAdminPage(page)
        survey["login"] = admin.login_as_role(role)
        for slug, kind in ((SUBMISSION_SLUG, "submission"), (INQUIRY_SLUG, "inquiry")):
            http = admin.open_manage(slug)
            info = {
                "http": http,
                "user_id": admin.signed_in_user()[0],
                "list_heading": admin.list_heading_visible(),
                "total": admin.total_entries(),
                "headers": admin.list_headers(),
                "nav": admin.nav_entry(OBJECT_LABELS[slug]),
                "controls": admin.review_controls(),
                "evidence": admin.evidence(f"{role.split()[0]}_review_surface_{slug}"),
            }
            own_id = intake[kind].get("id")
            if own_id:
                info["own_row"] = admin.row_by_id(own_id)
                view = admin.view_entry(own_id)
                info["own_view_controls"] = view["controls"]
                info["own_view_status"] = view["fields"].get("Submission Status" if kind == "submission" else "Inquiry Status")
                info["own_view_evidence"] = admin.evidence(f"{role.split()[0]}_own_{kind}_{own_id}_view")
            survey[slug] = info
        for slug in (SUBMISSION_SLUG, INQUIRY_SLUG):
            survey[slug]["native_content_data"] = admin.open_native_entries(slug)
            admin.evidence(f"{role.split()[0]}_native_content_data_{slug}")
    finally:
        ctx.close()
    return survey


def _review_controls_found(info: dict) -> list[str]:
    c = info["controls"]
    found = [f"row action {a}" for a in c["row_actions"]] + [f"button {b}" for b in c["buttons"]]
    found += [f"field {f}" for f in c["fields"]] + (["authoring form"] if c["authoring_forms"] else [])
    row = info.get("own_row") or {}
    found += [f"own-row action {a}" for a in row.get("actions", [])
              if a.lower() not in ("view", "preview") and a.lower() in REVIEW_ROW_ATTRS + ("approve", "reject", "edit", "status")]
    vc = info.get("own_view_controls") or {}
    found += [f"View-modal button {b}" for b in vc.get("buttons", []) if b not in NON_REVIEW_BUTTONS]
    found += [f"View-modal input {i}" for i in vc.get("inputs", [])]
    return found


def _blocked_unless_review(survey: dict, slugs: tuple[str, ...], what: str) -> None:
    """Skip BLOCKED with the exact live reason, or fail if review controls now exist."""
    allure.attach(json.dumps({s: survey[s] for s in slugs}, indent=2, ensure_ascii=False),
                  name="review surface for this case", attachment_type=allure.attachment_type.JSON)
    appeared = {s: _review_controls_found(survey[s]) for s in slugs}
    appeared = {s: v for s, v in appeared.items() if v}
    if appeared:
        pytest.fail(f"Review controls now exist ({appeared}) — this case must now be scripted against them; "
                    f"it is not run on guessed steps.")
    parts = []
    for s in slugs:
        info = survey[s]
        row = info.get("own_row") or {}
        parts.append(
            f"manage-{s}: {'view only' if info['nav'].get('view_only') else 'list'}, {info['total']} entries, "
            f"columns {info['headers']}, own QCTEST row actions {row.get('actions')}, own row View modal = read-only "
            f"(status {info.get('own_view_status')!r}, buttons {info.get('own_view_controls', {}).get('buttons')}, "
            f"no editable input); native Content & Data for the {survey['role']}: {info['native_content_data']}")
    intake = "; ".join(f"public {k} intake HTTP {v['http']} ({'reference ' + repr(v['reference']) if v['success'] else 'failed'}"
                       f", entry id {v['id']})" for k, v in survey["intake"].items())
    pytest.skip(
        f"BLOCKED — {what}. Live in this run as the {survey['role']}: {intake}. Review controls found = none "
        f"({'; '.join(parts)}). Bug candidate: no Approve / Reject / Rejection Reason / status control on the "
        f"review surface."
    )


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
# Live: Editor denied Submission review (P1) — 143277
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Roles")
@allure.title("A Site Content Editor without Submission review permission is denied the Submission review screen")
@pytest.mark.auth
@pytest.mark.tc_143277
def test_editor_denied_submission_review(browser, qctest_intake):
    ctx, page = _auth_free_page(browser)
    try:
        admin = OpportunityReviewAdminPage(page)
        assert admin.login_as_role(ROLE_EDITOR) == "ok", "Step 1: the Site Content Editor could not sign in"
        http = admin.open_manage(SUBMISSION_SLUG)
        user_id = admin.signed_in_user()[0]
        assert user_id == ROLE_USER_IDS[ROLE_EDITOR], f"signed in as {user_id!r}, not the Editor"
        own_id = qctest_intake["submission"].get("id")
        observed = {
            "object_authoring_nav_entry": admin.nav_entry(OBJECT_LABELS[SUBMISSION_SLUG]),
            "direct_url_http": http,
            "direct_url_list_heading": admin.list_heading_visible(),
            "direct_url_total_entries": admin.total_entries(),
            "rows_exposed": len(admin.list_rows()),
            "own_qctest_row_actions": (admin.row_by_id(own_id) or {}).get("actions") if own_id else None,
        }
        evidence = admin.evidence("143277_editor_direct_url_manage_opportunity_submission")
        if own_id:
            view = admin.view_entry(own_id)
            observed["own_qctest_view_shows_name"] = admin.entry_name(view) == qctest_intake["submission"]["name"]
            admin.evidence("143277_editor_view_own_qctest_submission")
        observed["liferay_product_menu_link"] = admin.has_product_menu_link("Opportunity Submissions")
        observed["native_content_data_view"] = admin.open_native_entries(SUBMISSION_SLUG)
        admin.evidence("143277_editor_native_content_data_view")
    finally:
        ctx.close()
    allure.attach(json.dumps(observed, indent=2), name="Editor access (live)",
                  attachment_type=allure.attachment_type.JSON)
    problems = []
    if observed["object_authoring_nav_entry"]["present"]:
        problems.append("Step 2: the Object Authoring navigation shows the 'Opportunity Submission' entry "
                        f"({'view only' if observed['object_authoring_nav_entry']['view_only'] else 'editable'})")
    if observed["direct_url_list_heading"]:
        problems.append(f"Step 3: direct URL /web/qatar-chamber/manage-{SUBMISSION_SLUG} returns HTTP "
                        f"{observed['direct_url_http']} with the 'Opportunity Submission entries' list "
                        f"({observed['direct_url_total_entries']} total) instead of an access-denied page")
    if observed["liferay_product_menu_link"]:
        problems.append("Step 2: the Liferay product menu lists 'Opportunity Submissions'")
    if observed["native_content_data_view"] != "denied":
        problems.append(f"Step 3: the native Content & Data view is {observed['native_content_data_view']!r}, not denied")
    if observed["rows_exposed"]:
        problems.append(f"Step 4: {observed['rows_exposed']} submission row(s) exposed (row actions on our QCTEST row: "
                        f"{observed['own_qctest_row_actions']}; its View modal shows the full record: "
                        f"{observed.get('own_qctest_view_shows_name')})")
    assert not problems, "\n".join(problems) + f"\nEvidence: {evidence}"


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
    expected = ("Name", "Email", "Company", "Opportunity", "Status", "Date")
    missing = [h for h in expected if not any(h.lower() in t.lower() for t in headers)]
    row_text = " ".join((item["row"] or {}).get("cells", []))
    absent = [v for v in (item["name"], QCTEST_EMAIL, item["company"], INQUIRY_TARGET_CODE, "Pending")
              if v.lower() not in row_text.lower()]
    assert not (missing or absent), (
        f"Step 2: the list columns are {headers!r} (missing {missing!r}); our inquiry's row reads {row_text!r} and "
        f"lacks {absent!r} (those values — Inquiry Status {item['view']['fields'].get('Inquiry Status')!r} — are "
        f"visible only in the View modal). Evidence: {item['list_evidence']}")


# ===========================================================================
# Submission review — blocked while no review control / no Pending submission
# ===========================================================================
def _submission_case(survey, what):
    _blocked_unless_review(survey, (SUBMISSION_SLUG,), what)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Approving a Pending submission sets it Approved / eligible to publish (and notifies the submitter)")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143226
@pytest.mark.tc_143396
def test_approve_pending_submission(review_surface):
    """143226 (QC Admin Reviewer) and 143396 (Administrator) — run as the Form Manager; email part not verifiable."""
    _submission_case(review_surface, "Approve a Pending submission")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Rejecting a Pending submission with a reason sets it Rejected and stores the reason")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143198
@pytest.mark.tc_143227
@pytest.mark.tc_143398
def test_reject_submission_with_reason(review_surface):
    """143198 / 143227 / 143398 — email part (143227, 143398) not verifiable."""
    _submission_case(review_surface, "Reject a Pending submission with a Rejection Reason")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Rejecting a submission without a Rejection Reason is blocked and it stays Pending")
@pytest.mark.functional_low
@pytest.mark.tc_143199
@pytest.mark.tc_143399
def test_reject_without_reason_blocked(review_surface):
    _submission_case(review_surface, "Reject with an empty Rejection Reason")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Approving a Pending submission publishes it as a Business Opportunity in the Active tab")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_143285
def test_approve_publishes_business_opportunity(review_surface):
    _submission_case(review_surface, "Approve (with confirmation) and publish as a Business Opportunity")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("A rejected submission stays stored (not deleted) with status Rejected")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.tc_143286
def test_rejected_submission_kept(review_surface):
    _submission_case(review_surface, "Reject with a reason, then confirm the record is still stored")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("A rejected submission creates no Business Opportunity record and no public card")
@pytest.mark.functional_low
@pytest.mark.tc_143400
def test_rejected_submission_creates_no_record(review_surface):
    _submission_case(review_surface, "Reject with reason 'Duplicate submission', then search records / public listing")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Rejecting an already Approved submission is blocked as an invalid transition")
@pytest.mark.edge
@pytest.mark.tc_143243
def test_reject_approved_submission_blocked(review_surface):
    _submission_case(review_surface, "Reject a submission that is already Approved")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("An Approved submission can be published as a live Business Opportunity")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143397
def test_publish_approved_submission(review_surface):
    _submission_case(review_surface, "Publish as Opportunity from an Approved submission")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Approving a submission records actor, action and timestamp in the History / Audit Log")
@pytest.mark.functional_low
@pytest.mark.tc_143401
def test_approve_recorded_in_history(review_surface):
    _submission_case(review_surface, "Approve a submission and read its History")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Rejecting a submission records the action and reason in the History / Audit Log")
@pytest.mark.functional_low
@pytest.mark.tc_143402
def test_reject_recorded_in_history(review_surface):
    _submission_case(review_surface, "Reject a submission with a reason and read its History")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submission review")
@allure.title("Direct create-and-publish works; Approve again on an Approved submission is blocked")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143405
def test_direct_publish_and_reapprove_blocked(review_surface):
    """Steps 1-3 (direct create + publish of a record) are the record-form flow Agent A covers;
    the case's own point (step 4, Approve again on an Approved submission) has no surface."""
    _submission_case(review_surface, "Approve again on an already Approved submission (step 4)")


# ===========================================================================
# Inquiry review — blocked while no status control / no Pending inquiry
# ===========================================================================
def _inquiry_case(survey, what):
    _blocked_unless_review(survey, (INQUIRY_SLUG,), what)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Inquiry review")
@allure.title("An inquiry moves Pending -> In-progress, and the status persists after reload")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143392
@pytest.mark.tc_143224
@pytest.mark.tc_143394
def test_inquiry_pending_to_in_progress(review_surface):
    """143392 / 143224 (P3 twin) and 143394 (P3, persists after a full reload)."""
    _inquiry_case(review_surface, "Change a Pending inquiry's status to In-progress and reload")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Inquiry review")
@allure.title("An inquiry moves In-progress -> Completed/Closed")
@pytest.mark.functional_low
@pytest.mark.tc_143393
@pytest.mark.tc_143225
def test_inquiry_in_progress_to_completed(review_surface):
    _inquiry_case(review_surface, "Change an In-progress inquiry's status to Completed/Closed")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Inquiry review")
@allure.title("An inquiry progresses Pending -> In-progress -> Completed/Closed with each step persisted")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.tc_143287
def test_inquiry_full_status_workflow(review_surface):
    _inquiry_case(review_surface, "Walk an inquiry through Pending -> In-progress -> Completed/Closed")


# ===========================================================================
# Accounts / mailbox gaps
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Roles")
@allure.title("A QC Admin Reviewer (Form Manager) can review/update inquiries and approve/reject submissions")
@pytest.mark.auth
@pytest.mark.tc_143280
def test_qc_admin_reviewer_access(review_surface):
    """Azure TC 143280, run as the Form Manager (user decision 2026-10-07)."""
    s = review_surface
    assert s["login"] == "ok", f"Step 1: the Form Manager could not sign in ({s['login']})"
    for slug in (INQUIRY_SLUG, SUBMISSION_SLUG):
        assert s[slug]["user_id"] == ROLE_USER_IDS[ROLE_FORM_MANAGER], f"signed in as {s[slug]['user_id']!r}"
        assert s[slug]["list_heading"], f"Steps 2-3: the Form Manager cannot open manage-{slug} (HTTP {s[slug]['http']})"
    _blocked_unless_review(s, (INQUIRY_SLUG, SUBMISSION_SLUG),
                           "Judged: step 1 (sign-in), step 3 and the list part of step 2 (both lists open). Steps 2 (update "
                           "an inquiry status) and 4 (Approve a submission) cannot be performed")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Roles")
@allure.title("An Administrator has full access across Opportunity Management, Inquiry and Submission review")
@pytest.mark.auth
@pytest.mark.tc_143282
def test_administrator_full_access(browser, qctest_intake):
    """Azure TC 143282, run as TEST_USER (the Administrator, user decision 2026-10-07).
    Read-only: Publish availability is checked, nothing is published."""
    survey = _survey(browser, ROLE_ADMIN, qctest_intake)
    ctx, page = _auth_free_page(browser)
    try:
        admin = OpportunityReviewAdminPage(page)
        assert admin.login_as_role(ROLE_ADMIN) != "auth_failed", "Step 1: TEST_USER could not sign in"
        authoring = admin.authoring_access()
        admin.evidence("Administrator_manage_business_opportunity")
    finally:
        ctx.close()
    survey["opportunity_management"] = authoring
    allure.attach(json.dumps(survey, indent=2), name="Administrator access (live)",
                  attachment_type=allure.attachment_type.JSON)
    assert survey["login"] == "ok", f"Step 1: login outcome {survey['login']!r}"
    assert "Publish" in authoring["form_buttons"] and {"publish", "unpublish"} & set(authoring["row_actions"]), (
        f"Step 2: Opportunity Management offers no Publish to the Administrator: {authoring}")
    for slug in (INQUIRY_SLUG, SUBMISSION_SLUG):
        assert survey[slug]["list_heading"], f"Steps 3-4: manage-{slug} does not open for the Administrator"
    _blocked_unless_review(survey, (INQUIRY_SLUG, SUBMISSION_SLUG),
                           "Steps 1-2 judged (Publish is offered in Opportunity Management; not performed). "
                           "Steps 3 (update an inquiry status) and 4 (Approve/Reject) cannot be performed on the "
                           "review surface; the native Liferay Content & Data view lists the rows for this account "
                           "but is not used (user decision: no Content & Data workaround)")


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

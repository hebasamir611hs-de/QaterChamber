"""
cms/tests/tenders/test_tenders_submissions_control_panel.py — PBI 130952,
eTender Submissions review panel (bug 148117 fix). Azure suite 140383.

Implements the 10 cases that were skip-stubs in
test_tenders_blocked_control_panel.py (SUBMISSIONS_BLOCKED).

Screen (confirmed live 2026-10-13, see eoi_submission_admin_page.py):
/web/qatar-chamber/manage-eoi-submission — View / Preview / Approve / Reject /
History per row; Reject prompts for a required reason; Approve creates ONE
Draft tender on /manage-tender, which is where "Publish" lives (dev design,
bug 148117 comment 2026-10-11).

Data: each test files its OWN anonymous public submission named
QCTEST-R32-T2-<stamp>-<tc> (e-mail qctest-r32-t2@example.com) through the
webform's intake endpoint. Every click is guarded to that one row. Nothing is
deleted: submissions stay Pending/Approved/Rejected; generated tenders stay
Draft.

Disclosed deviations from the case wording:
  - 146106/146130 "Publish becomes available": checked on the Draft tender the
    approval creates (Publish button present on its edit form) — there is no
    Publish action on the submission row by design.
  - 146130 "generic Liferay success toast (MSG-3)": the panel shows its own
    confirmation; the test asserts that confirmation and attaches its text.
  - 146132 "no rejection e-mail was sent": no mailbox access for the
    example.com address — NOT verified, recorded in the report.
  - 146131 publishes a QCTEST tender publicly; it runs only when
    QCTEST_ALLOW_PUBLIC_PUBLISH=1 (the publish step was refused by this
    session's permission policy on 2026-10-13).
"""

from __future__ import annotations

import os
from datetime import datetime

import allure
import pytest

from cms.pages.tenders.eoi_submission_admin_page import (
    DOC_LABELS,
    LEGACY_PANEL_PATH,
    LIST_PATH,
    MSG_APPROVED,
    MSG_REASON_REQUIRED,
    MSG_REJECTED,
    QCTEST_PREFIX,
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    VIEWER_FIELD_LABELS,
    EoiSubmission,
    EoiSubmissionAdminPage,
    submit_public_etender,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import control_panel_url, settings
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130952,
              pytest.mark.xdist_group("tenders_submissions_t2")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
STAMP = datetime.now().strftime("%m%d%H%M%S")

EDITOR = (os.getenv("CMS_SITE_CONTENT_EDITOR_EMAIL", ""), os.getenv("CMS_SITE_CONTENT_EDITOR_PASSWORD", ""))
AUTHOR = (os.getenv("CMS_SITE_CONTENT_AUTHOR_EMAIL", ""), os.getenv("CMS_SITE_CONTENT_AUTHOR_PASSWORD", ""))
ADMIN = (settings.test_user, settings.test_password)

REASON = "Missing Establishment Card details"


def _title(tc: str, suffix: str = "") -> str:
    return f"{QCTEST_PREFIX}{STAMP}-{tc}{suffix}"


@pytest.fixture
def public_submit(playwright_instance):
    """Files anonymous public eTender submissions (logged-out request context)."""
    ctx = playwright_instance.request.new_context()
    created: list[EoiSubmission] = []

    def _make(tc: str, suffix: str = "") -> EoiSubmission:
        sub = submit_public_etender(ctx, _title(tc, suffix))
        created.append(sub)
        return sub

    yield _make
    allure.attach("\n".join(f"{s.title} id={s.entry_id}" for s in created) or "none",
                  name="QCTEST submissions created (left in place, not deleted)")
    ctx.dispose()


@pytest.fixture
def extra_pages(browser):
    contexts = []

    def _make(auth: bool = False):
        ctx = new_context(browser) if auth else new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


def _panel(page, who) -> EoiSubmissionAdminPage:
    panel = EoiSubmissionAdminPage(page)
    panel.open_list(*who)
    return panel


def _en_value(text: str) -> str:
    """Bilingual fields render as 'ar_SA: ...
en_US: ...' in the viewer."""
    for line in (text or "").splitlines():
        if line.startswith("en_US:"):
            return line.split(":", 1)[1].strip()
    return (text or "").strip()


def _wait_row(panel: EoiSubmissionAdminPage, sub: EoiSubmission) -> None:
    def _seen() -> bool:
        if panel.row_present(sub):
            return True
        panel.reload_list()
        return panel.row_present(sub)
    try:
        wait_until(_seen, timeout=60.0, poll=3.0)
    except WaitTimeoutError:
        raise AssertionError(f"submission {sub.title} (id {sub.entry_id}) never listed on {LIST_PATH}") from None


def _generated_draft_tender(page, sub: EoiSubmission) -> dict | None:
    """Read-only lookup of the Draft tender an approval created (title = org name)."""
    from cms.pages.tenders.tender_admin_page import TenderFieldsAdminPage  # noqa: PLC0415
    tenders = TenderFieldsAdminPage(page)
    tenders.open_list_all()
    rows = [r for r in tenders.list_rows() if r["title"] == sub.title]
    return rows[0] if len(rows) == 1 else ({"duplicates": rows} if rows else None)


def _publish_button_on(page, code: str) -> bool:
    from cms.pages.tenders.tender_admin_page import TenderFieldsAdminPage  # noqa: PLC0415
    tenders = TenderFieldsAdminPage(page)
    tenders.open_entry_en(code)
    return page.get_by_role("button", name=TenderFieldsAdminPage.SUBMIT_NAME).first.is_visible()


# ===========================================================================
@pytest.mark.auth
@pytest.mark.tc_146105
@AUTH_FREE_PAGE
def test_unauthenticated_user_denied_etender_submissions_panel(page, public_submit):
    """Azure TC 146105 — logged-out direct URL is denied / sent to login, no data exposed."""
    sub = public_submit("146105")
    login = CmsLoginPage(page)
    for path in (LEGACY_PANEL_PATH, LIST_PATH):
        page.goto(control_panel_url(path))
        page.wait_for_load_state("load")
        body = page.locator("body").inner_text()
        denied = (login.login_form_visible() or "Access Denied" in body or "Not Found" in body
                  or "/c/portal/login" in page.url or "sign-in" in page.url.lower()
                  or path not in page.url)  # redirected away from the panel (live: /home)
        assert denied, f"{path}: logged-out visitor was neither denied nor redirected to login ({page.url})"
        assert sub.title not in body, f"{path}: submission data exposed to a logged-out visitor"
        assert page.locator("[data-qc-oel-view]").count() == 0, f"{path}: review rows rendered for a visitor"


@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.tc_146106
@AUTH_FREE_PAGE
def test_editor_can_approve_reject_publish_submission(page, public_submit):
    """Azure TC 146106 — Site Content Editor: Approve available -> Publish becomes
    available (on the generated Draft tender); Reject with reason available."""
    to_approve = public_submit("146106", "-A")
    to_reject = public_submit("146106", "-R")
    panel = _panel(page, EDITOR)
    _wait_row(panel, to_approve)
    _wait_row(panel, to_reject)

    assert panel.row_status(to_approve) == STATUS_PENDING
    assert panel.has_action(to_approve, "approve"), "Approve not offered on a Pending submission"
    assert panel.has_action(to_reject, "reject"), "Reject not offered on a Pending submission"

    panel.approve(to_approve)
    assert MSG_APPROVED in panel.success_text(), f"approve confirmation missing: {panel.success_text()!r}"
    panel.reload_list()
    assert panel.row_status(to_approve) == STATUS_APPROVED

    panel.reject(to_reject, REASON)
    assert MSG_REJECTED in panel.success_text(), f"reject confirmation missing: {panel.success_text()!r}"
    panel.reload_list()
    assert panel.row_status(to_reject) == STATUS_REJECTED

    draft = _generated_draft_tender(page, to_approve)
    assert draft and "code" in draft, f"approval did not create exactly one Draft tender: {draft}"
    assert draft["status"].upper() == "DRAFT", draft
    assert _publish_button_on(page, draft["code"]), "Publish is not available on the approved submission's tender"


@pytest.mark.auth
@pytest.mark.tc_146107
@AUTH_FREE_PAGE
def test_author_cannot_publish_submission(page, public_submit, extra_pages):
    """Azure TC 146107 — Site Content Author: no review/publish action in the UI,
    and a direct (non-UI) status transition is refused server-side."""
    sub = public_submit("146107")
    author = _panel(page, AUTHOR)
    assert author.access_denied() or not author.any_row_rendered(), "Author sees the submissions review list"
    assert not author.row_present(sub), "Author can see the Submitted eTender row"
    assert page.locator("[data-qc-oel-approve], [data-qc-oel-publish]").count() == 0, \
        "Approve/Publish action rendered for the Author"

    status = author.api_patch_status(sub, "approved")
    allure.attach(str(status), name="Author direct PATCH status")
    assert status >= 400, f"server accepted the Author's direct status transition (HTTP {status})"

    editor = EoiSubmissionAdminPage(extra_pages())
    editor.open_list(*EDITOR)
    _wait_row(editor, sub)
    assert editor.row_status(sub) == STATUS_PENDING, "submission status changed after the Author's direct attempt"


@pytest.mark.auth
@pytest.mark.tc_146109
@AUTH_FREE_PAGE
def test_rejected_submission_remains_stored(page, public_submit):
    """Azure TC 146109 — rejected record stays listed with its reason."""
    sub = public_submit("146109")
    panel = _panel(page, EDITOR)
    _wait_row(panel, sub)
    panel.reject(sub, REASON)
    panel.reload_list()
    assert panel.row_present(sub), "rejected submission disappeared from the list"
    assert panel.row_status(sub) == STATUS_REJECTED
    panel.filter_status("rejected")
    assert panel.row_present(sub), "rejected submission missing under the Rejected filter"
    fields = panel.view(sub)
    assert _en_value(fields.get("Rejection Reason")) == REASON, f"stored reason: {fields.get('Rejection Reason')!r}"


@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_146130
@AUTH_FREE_PAGE
def test_administrator_can_approve_submitted_etender(page, public_submit):
    """Azure TC 146130 — Approve -> Approved, success confirmation, Publish available."""
    sub = public_submit("146130")
    panel = _panel(page, EDITOR)
    _wait_row(panel, sub)
    panel.approve(sub)
    message = panel.success_text()
    allure.attach(message, name="approve confirmation (case expects MSG-3 generic toast)")
    assert MSG_APPROVED in message, f"no success confirmation after Approve: {message!r}"
    panel.reload_list()
    assert panel.row_status(sub) == STATUS_APPROVED
    draft = _generated_draft_tender(page, sub)
    assert draft and "code" in draft, f"approval did not create exactly one Draft tender: {draft}"
    assert _publish_button_on(page, draft["code"]), "Publish action not available after approval"


@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_146131
@AUTH_FREE_PAGE
@pytest.mark.skipif(os.getenv("QCTEST_ALLOW_PUBLIC_PUBLISH") != "1",
                    reason="BLOCKED — publishes a QCTEST tender publicly on qcdev; the publish step was refused "
                           "by the session permission policy (2026-10-13). Set QCTEST_ALLOW_PUBLIC_PUBLISH=1 to run.")
def test_publishing_approved_submission_appears_publicly(page, public_submit, extra_pages):
    """Azure TC 146131 — publish the approved submission's tender; public detail
    shows the submitted values. The tender is unpublished again afterwards."""
    from cms.pages.tenders.tender_admin_page import (  # noqa: PLC0415
        K_HELP_EMAIL, K_OVERVIEW, K_PUBLICATION, TenderFieldsAdminPage, TenderPublicViewB)
    sub = public_submit("146131")
    panel = _panel(page, EDITOR)
    _wait_row(panel, sub)
    panel.approve(sub)
    draft = _generated_draft_tender(page, sub)
    assert draft and "code" in draft, f"approval did not create exactly one Draft tender: {draft}"
    tenders = TenderFieldsAdminPage(page)
    tenders.open_entry_en(draft["code"])
    tenders.fill_rich(K_OVERVIEW, f"{sub.title} overview")
    tenders.set_date(K_PUBLICATION, datetime.now().strftime("%d/%m/%Y"))
    tenders.fill_en(K_HELP_EMAIL, sub.values["submitterContactEmail"])
    tenders.set_active_status(True)
    tenders.click_publish()
    try:
        visitor = TenderPublicViewB(extra_pages())
        visitor.open_detail(draft["code"])
        text = visitor.detail_text()
        for key in ("organizationName", "organizationAddress", "workDescription", "preBidMeetingAddress"):
            assert sub.values[key] in text, f"public detail lacks submitted {key}={sub.values[key]!r}"
    finally:
        tenders.open_list_all()
        tenders.unpublish_entry(draft["code"])


@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.tc_146132
@AUTH_FREE_PAGE
def test_administrator_can_reject_submission_with_reason(page, public_submit):
    """Azure TC 146132 — Administrator rejects with a reason -> Rejected, reason stored.
    The "no rejection e-mail" check is not automatable here (no mailbox access)."""
    sub = public_submit("146132")
    panel = _panel(page, ADMIN)
    _wait_row(panel, sub)
    panel.reject(sub, REASON)
    assert MSG_REJECTED in panel.success_text()
    panel.reload_list()
    assert panel.row_status(sub) == STATUS_REJECTED
    status, body = panel.api_get(sub)
    assert status == 200 and body.get("rejectionReason") == REASON, f"stored reason: {body.get('rejectionReason')!r}"
    allure.attach("NOT VERIFIED: rejection e-mail absence (no mailbox access to qctest-r32-t2@example.com)",
                  name="email check")


@pytest.mark.functional_high
@pytest.mark.tc_146137
@AUTH_FREE_PAGE
def test_submissions_review_view_shows_all_fields_and_documents(page, public_submit):
    """Azure TC 146137 — the review view shows every field group and the BOQ /
    tender / additional documents are downloadable — as the Site Content Editor
    (the reviewer role the fix targets)."""
    sub = public_submit("146137")
    panel = _panel(page, EDITOR)
    _wait_row(panel, sub)
    fields = panel.view(sub)
    missing = [label for label in VIEWER_FIELD_LABELS if label not in fields]
    assert not missing, f"review view lacks fields: {missing}"
    assert sub.title in fields["Organization Name"]
    links = panel.viewer_document_links()
    results = {label: panel.download_status(links.get(label, "")) if links.get(label) else None for label in DOC_LABELS}
    allure.attach(repr(results), name="document links")
    broken = {k: v for k, v in results.items()
              if not v or v["status"] != 200 or "pdf" not in v["content_type"].lower()}
    assert not broken, f"documents not downloadable from the review screen: {broken}"


@pytest.mark.functional_low
@pytest.mark.tc_146280
@AUTH_FREE_PAGE
def test_valid_rejection_reason_accepted(page, public_submit):
    """Azure TC 146280 — a valid reason is accepted and stored."""
    sub = public_submit("146280")
    panel = _panel(page, EDITOR)
    _wait_row(panel, sub)
    reason = f"QCTEST valid reason {STAMP}"
    panel.reject(sub, reason)
    assert MSG_REJECTED in panel.success_text()
    panel.reload_list()
    assert panel.row_status(sub) == STATUS_REJECTED
    assert _en_value(panel.view(sub).get("Rejection Reason")) == reason


@pytest.mark.functional_low
@pytest.mark.tc_146281
@AUTH_FREE_PAGE
def test_reject_blocked_without_rejection_reason(page, public_submit):
    """Azure TC 146281 — blank reason -> blocked with a validation error."""
    sub = public_submit("146281")
    panel = _panel(page, EDITOR)
    _wait_row(panel, sub)
    panel.reject(sub, "")
    assert any(MSG_REASON_REQUIRED in m for m in panel.dialog_messages), \
        f"no validation error for a blank reason: {panel.dialog_messages}"
    panel.reload_list()
    assert panel.row_status(sub) == STATUS_PENDING, "submission changed state although the reason was blank"

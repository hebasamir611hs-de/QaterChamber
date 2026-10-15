"""
cms/pages/tenders/eoi_submission_admin_page.py — eTender Submissions review
panel (PBI 130952, bug 148117 fix, qc-tenders 1.0.9).

CONFIRMED LIVE 2026-10-13 (qcdev, Playwright scripts, Site Content Editor /
Administrator / Site Content Author / Form Manager):

  - `/web/qatar-chamber/manage-eoi-submission` IS the eTender Submissions
    review panel. Rows: `[data-qc-oel-body] tr`, title cell
    `td.qc-oel__cell-title` (= Organization name EN), status badge in the 2nd
    cell (PENDING / APPROVED / REJECTED). Row actions carry the entry id:
    `[data-qc-oel-view|approve|reject|history="<id>"]`.
  - Approve -> native confirm `Approve: "<title>"?`; Reject -> native prompt
    `Reject "<title>". Enter the reason (required):`; an empty reason raises
    the alert "A rejection reason is required." and nothing is saved.
  - Confirmations (alert): "The eTender submission has been approved. A draft
    tender with its details is now on Manage: Tender - complete it and publish
    it." / "The eTender submission has been rejected."
  - View opens a read-only dialog `[data-qc-oel-viewer]` (<dt>/<dd> pairs);
    documents are <a> links inside <dd>. For the Administrator they are real
    `/documents/...download=true` links; for the Site Content Editor the
    server returns `link.href = /c/portal/login` (no file permission).
  - Status filter `select[data-qc-oel-status-filter]` (pending / approved /
    rejected).
  - Site Content Author: the page renders "Access Denied" and GET
    /o/c/eoisubmissions/<id> answers 404.
  - Approve creates ONE Draft tender on /manage-tender titled with the
    submission's Organization name; publishing it stays an editorial step.

Public submissions are created through the webform's own anonymous intake
POST /o/qc-tenders-api/submissions (multipart) — see `submit_public_etender`.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import control_panel_url
from core.utils.waits import WaitTimeoutError, wait_until

EOI_SUBMISSION_SLUG = "eoi-submission"
LIST_PATH = "/web/qatar-chamber/manage-eoi-submission"
LEGACY_PANEL_PATH = "/group/control_panel/manage/-/etender-submissions"
PUBLIC_INTAKE_PATH = "/o/qc-tenders-api/submissions"
API_ENTRY_PATH = "/o/c/eoisubmissions/{entry_id}"
ADMIN_HOME_EN_URL_PATH = "/en/home"

QCTEST_PREFIX = "QCTEST-R32-T2-"
QCTEST_EMAIL = "qctest-r32-t2@example.com"

ROW = "[data-qc-oel-body] tr"
ROW_TITLE = "td.qc-oel__cell-title"
ACTION_ATTR = "[data-qc-oel-{action}=\"{entry_id}\"]"
PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
STATUS_FILTER = "select[data-qc-oel-status-filter]"
VIEWER = "[data-qc-oel-viewer]"
VIEWER_OPEN = "[data-qc-oel-viewer]:not([hidden])"
VIEWER_BODY = "[data-qc-oel-viewer-body]"
VIEWER_CLOSE = "[data-qc-oel-viewer] .qc-oel__viewer-x"
SUCCESS_ALERT = ".alert, [role=alert]"
ACCESS_DENIED_TEXT = "Access Denied"

STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"

MSG_APPROVED = ("The eTender submission has been approved. A draft tender with its details is now on "
                "Manage: Tender - complete it and publish it.")
MSG_REJECTED = "The eTender submission has been rejected."
MSG_REASON_REQUIRED = "A rejection reason is required."

DOC_LABELS = ("Bill Of Quantities", "Tender Document", "Additional Documents")
# Every webform field group, as the viewer labels them.
VIEWER_FIELD_LABELS = (
    "Organization Name", "Submitter Contact Email", "Commercial Registration Number",
    "Computer Registration Number", "Establishment Card Number", "Organization Address", "Street Address",
    "City", "Zip Postal Code", "Country", "Opening Date", "Closing Date", "General Technical Evaluation Allowed",
    "Tender Fee", "Fee Payable To", "Tender Fee Exemption Allowed", "Emd Amount", "Emd Payable To",
    "Payment Mode", "Tender Category", "Tender Type", "Tender Classification", "Product Category",
    "Tender Location", "Item Wise Technical Evaluation Allowed", "Work Description", "Pre Bid Meeting Date",
    "Pre Bid Meeting Address", "Pre Bid Meeting City", "Prequalification Approval Date",
    "Should Allow Nda Tender", "Bid Validity Days", "Submission Status", "Rejection Reason",
) + DOC_LABELS

FIXTURES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "tests", "tenders", "fixtures")


@dataclass
class EoiSubmission:
    entry_id: str
    title: str
    values: dict = field(default_factory=dict)

    def in_namespace(self) -> bool:
        return self.title.startswith(QCTEST_PREFIX)


def submission_payload(title: str) -> dict:
    """One complete, valid webform submission (values the public form offers)."""
    return {
        "organizationName": title, "organizationNameAr": f"اختبار {title}",
        "submitterContactEmail": QCTEST_EMAIL, "commercialRegistrationNumber": "12345",
        "computerRegistrationNumber": "67890", "establishmentCardNumber": "11-222",
        "organizationAddress": "QCTEST Addr", "organizationAddressAr": "عنوان تجريبي",
        "streetAddress": "QCTEST Street", "streetAddressAr": "شارع تجريبي",
        "city": "Doha", "cityAr": "الدوحة", "zipPostalCode": "00000", "country": "qatar",
        "openingDate": "2026-11-01", "closingDate": "2026-12-31", "generalTechnicalEvaluationAllowed": "yes",
        "tenderFee": "100", "feePayableTo": "QCTEST Payee", "tenderFeeExemptionAllowed": "no",
        "emdAmount": "200", "emdPayableTo": "QCTEST EMD", "paymentMode": "online",
        "tenderCategory": "goods", "tenderType": "openTender", "tenderClassification": "supply",
        "productCategory": "computerHW", "tenderLocation": "qatar", "itemWiseTechnicalEvaluationAllowed": "no",
        "workDescription": f"QCTEST work description {title}", "preBidMeetingDate": "2026-11-10",
        "preBidMeetingAddress": "QCTEST meeting", "preBidMeetingCity": "Doha", "preBidMeetingZipPostalCode": "",
        "prequalificationApprovalDate": "2026-11-05", "shouldAllowNdaTender": "no", "bidValidityDays": "30",
        "privacyPolicyConsent": "true", "recaptchaToken": "", "website": "",
    }


def submit_public_etender(request_context, title: str) -> EoiSubmission:
    """Anonymous public submission through the webform's own intake endpoint.

    The webform UI cannot be used: its client validation still requires a
    `privacyPolicyConsent` checkbox the markup no longer renders, so Submit
    always stops at "Please correct the highlighted fields." (2026-10-13)."""
    if not title.startswith(QCTEST_PREFIX):
        raise ValueError(f"{title!r} is not a {QCTEST_PREFIX} record")

    def _pdf(name: str) -> dict:
        with open(os.path.join(FIXTURES, name), "rb") as fh:
            return {"name": name, "mimeType": "application/pdf", "buffer": fh.read()}

    multipart = submission_payload(title)
    multipart["billOfQuantities"] = _pdf("tender_qctest_boq_800kb.pdf")
    multipart["tenderDocument"] = _pdf("tender_qctest_tender_doc_1_2mb.pdf")
    multipart["additionalDocuments"] = _pdf("qctest_valid_document.pdf")
    response = request_context.post(control_panel_url(PUBLIC_INTAKE_PATH), multipart=multipart,
                                    headers={"Accept-Language": "en-US"}, timeout=90000)
    body = response.json() if response.ok else {}
    if body.get("status") != "success" or not body.get("id"):
        raise AssertionError(f"public eTender intake refused {title}: HTTP {response.status} {response.text()[:300]}")
    return EoiSubmission(entry_id=str(body["id"]), title=title, values=submission_payload(title))


class EoiSubmissionAdminPage(ObjectAuthoringPage):
    def __init__(self, page):
        super().__init__(page, EOI_SUBMISSION_SLUG)
        self.dialog_messages: list[str] = []

    # ---- session / navigation ---------------------------------------------
    def sign_in(self, email: str | None = None, password: str | None = None) -> "EoiSubmissionAdminPage":
        CmsLoginPage(self.page).ensure_signed_in_as(email, password, control_panel_url(ADMIN_HOME_EN_URL_PATH))
        return self

    def open_list(self, email: str | None = None, password: str | None = None) -> "EoiSubmissionAdminPage":
        if email:
            self.sign_in(email, password)
        self.open(control_panel_url(LIST_PATH))
        try:
            self.page.locator(f"{ROW}, :text('{ACCESS_DENIED_TEXT}')").first.wait_for(timeout=60000)
        except Exception:  # noqa: BLE001 — an empty/denied page is read by the caller
            return self
        # The list pages 10 rows at a time; show every row so ours is reachable.
        size = self.page.locator(PAGE_SIZE_SELECT)
        if size.count() and size.first.is_visible() and size.first.input_value() != "0":
            size.first.select_option("0")
            self.page.wait_for_function(
                "() => !document.querySelector('[data-qc-oel-page-next]') || "
                "document.querySelector('[data-qc-oel-pager]').hidden || "
                "document.querySelectorAll('[data-qc-oel-body] tr').length > 10", timeout=15000)
        return self

    def access_denied(self) -> bool:
        return ACCESS_DENIED_TEXT in self.page.locator("body").inner_text()

    def signed_in_email(self) -> str:
        return self.page.evaluate(
            "() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())"
            " ? String(Liferay.ThemeDisplay.getUserEmailAddress ? Liferay.ThemeDisplay.getUserEmailAddress() : '')"
            " : ''")

    # ---- rows --------------------------------------------------------------
    def _row(self, sub: EoiSubmission):
        return self.page.locator(ROW, has=self.page.locator(ACTION_ATTR.format(action="view", entry_id=sub.entry_id)))

    def _guard(self, sub: EoiSubmission):
        """Every action runs on the ONE row of our own QCTEST record."""
        if not sub.in_namespace():
            raise ValueError(f"refusing to act on non-QCTEST submission {sub}")
        row = self._row(sub)
        if row.count() != 1:
            raise AssertionError(f"expected exactly one row for submission id {sub.entry_id}, found {row.count()}")
        title = row.locator(ROW_TITLE).inner_text().strip()
        if title != sub.title:
            raise AssertionError(f"row {sub.entry_id} reads {title!r}, expected our {sub.title!r}")
        return row

    def row_present(self, sub: EoiSubmission) -> bool:
        return self._row(sub).count() == 1

    def row_status(self, sub: EoiSubmission) -> str:
        return self._guard(sub).locator("td").nth(1).inner_text().strip().upper()

    def row_actions(self, sub: EoiSubmission) -> list[str]:
        return [t.strip() for t in self._guard(sub).locator("td.qc-oel__cell-action a").all_inner_texts()]

    def any_row_rendered(self) -> bool:
        return self.page.locator(ROW, has=self.page.locator("[data-qc-oel-view]")).count() > 0

    def filter_status(self, value: str) -> "EoiSubmissionAdminPage":
        self.select_option(STATUS_FILTER, value=value)
        return self

    def status_filter_options(self) -> list[str]:
        return self.page.locator(f"{STATUS_FILTER} option").evaluate_all("l => l.map(o => o.value)")

    # ---- review actions ----------------------------------------------------
    def _run(self, sub: EoiSubmission, action: str, prompt_text: str | None) -> "EoiSubmissionAdminPage":
        row = self._guard(sub)
        self.dialog_messages = []

        def _on_dialog(dialog):
            self.dialog_messages.append(dialog.message)
            if dialog.type == "prompt":
                dialog.accept(prompt_text or "")
            else:
                dialog.accept()

        self.page.on("dialog", _on_dialog)
        try:
            row.locator(ACTION_ATTR.format(action=action, entry_id=sub.entry_id)).click()
            try:
                wait_until(lambda: self._outcome_seen(action), timeout=20.0, poll=0.3)
            except WaitTimeoutError:
                pass
        finally:
            self.page.remove_listener("dialog", _on_dialog)
        return self

    def _outcome_seen(self, action: str) -> bool:
        if any(MSG_REASON_REQUIRED in m for m in self.dialog_messages):
            return True
        expected = MSG_APPROVED if action == "approve" else MSG_REJECTED
        return expected in self.success_text()

    def approve(self, sub: EoiSubmission) -> "EoiSubmissionAdminPage":
        return self._run(sub, "approve", None)

    def reject(self, sub: EoiSubmission, reason: str) -> "EoiSubmissionAdminPage":
        return self._run(sub, "reject", reason)

    def has_action(self, sub: EoiSubmission, action: str) -> bool:
        return self._guard(sub).locator(ACTION_ATTR.format(action=action, entry_id=sub.entry_id)).count() == 1

    def success_text(self) -> str:
        try:
            return " | ".join(t.strip() for t in self.page.locator(SUCCESS_ALERT).all_inner_texts() if t.strip())
        except Exception:  # noqa: BLE001
            return ""

    def reload_list(self) -> "EoiSubmissionAdminPage":
        return self.open_list()

    # ---- read-only viewer --------------------------------------------------
    def view(self, sub: EoiSubmission) -> dict[str, str]:
        row = self._guard(sub)
        row.locator(ACTION_ATTR.format(action="view", entry_id=sub.entry_id)).click()
        self.wait_for(f"{VIEWER_OPEN} {VIEWER_BODY} dt", first=True, timeout=30000)
        pairs = self.page.locator(f"{VIEWER_OPEN} {VIEWER_BODY}").evaluate(
            """b => { const o = {}; const dts = b.querySelectorAll('dt');
                     dts.forEach(dt => { const dd = dt.nextElementSibling; o[dt.innerText.trim()] = dd ? dd.innerText.trim() : ''; });
                     return o; }""")
        return pairs

    def viewer_document_links(self) -> dict[str, str]:
        return self.page.locator(f"{VIEWER_OPEN} {VIEWER_BODY}").evaluate(
            """b => { const o = {}; b.querySelectorAll('dt').forEach(dt => { const dd = dt.nextElementSibling;
                     const a = dd && dd.querySelector('a'); if (a) o[dt.innerText.trim()] = a.getAttribute('href'); });
                     return o; }""")

    def close_viewer(self) -> "EoiSubmissionAdminPage":
        self.click(VIEWER_CLOSE)
        return self

    def download_status(self, href: str) -> dict:
        response = self.page.request.get(control_panel_url(href) if href.startswith("/") else href,
                                         max_redirects=0, timeout=60000)
        return {"href": href, "status": response.status, "content_type": response.headers.get("content-type", ""),
                "location": response.headers.get("location", "")}

    # ---- REST (session-bound) ---------------------------------------------
    def _csrf(self) -> str:
        return self.page.evaluate("() => (window.Liferay && Liferay.authToken) || ''")

    def api_get(self, sub: EoiSubmission) -> tuple[int, dict]:
        response = self.page.request.get(control_panel_url(API_ENTRY_PATH.format(entry_id=sub.entry_id)),
                                         headers={"x-csrf-token": self._csrf()})
        try:
            return response.status, response.json()
        except Exception:  # noqa: BLE001
            return response.status, {}

    def api_patch_status(self, sub: EoiSubmission, status_key: str) -> int:
        """Direct (non-UI) status transition attempt on OUR record — used to
        prove the server refuses it for a role without review rights."""
        if not sub.in_namespace():
            raise ValueError(f"refusing to PATCH non-QCTEST submission {sub}")
        response = self.page.request.patch(
            control_panel_url(API_ENTRY_PATH.format(entry_id=sub.entry_id)),
            data={"submissionStatus": {"key": status_key}},
            headers={"x-csrf-token": self._csrf(), "Content-Type": "application/json"})
        return response.status

    @staticmethod
    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

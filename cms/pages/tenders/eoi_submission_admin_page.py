"""
cms/pages/tenders/eoi_submission_admin_page.py — EoiSubmissionAdminPage.

Control_Panel Page Object for PBI 130952's public-webform review/approval
flow ("Path 1" in this PBI's own case wording — Submitted -> Approve/
Reject -> Publish). Backs the Auth cases (TC-039..043/146105..146109) and
the Functional-High/Functional-Low Approve/Reject/Publish/audit-log cases
(TC-064..071/146130..146137, TC-214/215/146280..146281).

CONFIRMED LIVE 2026-09-24 (Playwright MCP, authenticated as TEST_USER
against qcdev, disclosed live fallback — same rationale as
tender_admin_page.py's module docstring):

  - The public "Submit your eTender" webform's real backing Object
    Definition is "EOISubmission" (`/web/qatar-chamber/manage-eoi-
    submission`, slug "eoi-submission") — confirmed live: `object-
    authoring`'s index lists exactly this entry (plus a sibling "EOI
    Submission Document" object for its file attachments), and this is
    the ONLY Object Definition whose name plausibly matches "Expression
    of Interest" (the webform's own reusable-CTA naming convention
    already documented in submit_etender_form_page.py's module
    docstring). There is no separate object literally named "Tender
    Submission" or "eTender Submissions" anywhere in the index.
  - `manage-eoi-submission` currently shows ZERO entries on this
    environment (confirmed live: entries table renders 0 rows) — no
    public visitor has ever completed a real submission through this
    webform on qcdev. This means the Approve/Reject/Publish button set,
    the review-panel's exact field layout, and the audit-log entry
    format could NOT be independently observed this session: there is
    no live "Submitted"/"Pending" record to open. Seeding one requires
    a full, real 36-field webform submission (confirmed field set in
    submit_etender_form_page.py's own module docstring) gated behind a
    live reCAPTCHA this automated session cannot solve — the exact same
    gate that already blocks TC-058/059/060/221 from completing
    end-to-end (see that Page Object's own TODO note on
    success_banner_visible()/success_reference_number()).

TODO(locator): every method below beyond navigation/login is a
best-effort placeholder, NOT independently confirmed against a real
Submitted/Pending record — there is no such record on this environment to
read from. Heal via `tools/extract_locators.py --storage-state` (or the
Playwright MCP) against a real Pending EOISubmission entry once one
exists (either a real visitor submission lands on qcdev, or the
reCAPTCHA gate is bypassed/mocked for this environment) — do not treat
these as confirmed-live locators until that happens. This mirrors this
project's own established precedent for a page nobody could reach yet
(see ChamberEventsAdminPage's own TODO(locator) block in its module
docstring) rather than guessing and asserting a fabricated selector as
real.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import control_panel_url, settings

EOI_SUBMISSION_SLUG = "eoi-submission"

ADMIN_HOME_EN_URL_PATH = "/en/home"
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'

STATUS_SUBMITTED = "Submitted"
STATUS_APPROVED = "Approved"
STATUS_REJECTED = "Rejected"
STATUS_PUBLISHED = "Published"

# TODO(locator): button/field labels below are the case's OWN wording
# (this PBI's approved test-case titles, e.g. "Approve"/"Reject"/
# "Publish"/"Rejection Reason") — not independently confirmed against a
# real record's review form, per module docstring. Confirmed-live once a
# real Submitted entry exists to open.
BUTTON_APPROVE = "Approve"
BUTTON_REJECT = "Reject"
BUTTON_PUBLISH = "Publish"
FIELD_REJECTION_REASON = "Rejection Reason"


class EoiSubmissionAdminPage(ObjectAuthoringPage):
    def __init__(self, page):
        super().__init__(page, EOI_SUBMISSION_SLUG)

    def _ensure_logged_in(self, email: str | None = None, password: str | None = None) -> None:
        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            user = email or settings.test_user
            pwd = password or settings.test_password
            login.open_login().login(user, pwd)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_list(self, email: str | None = None, password: str | None = None) -> "EoiSubmissionAdminPage":
        """Real, confirmed-live navigation/login even though the list
        itself has zero rows on this environment (see module docstring)."""
        self._ensure_logged_in(email, password)
        self.open(control_panel_url(f"/web/qatar-chamber/manage-{self.slug}"))
        return self

    # ---- TODO(locator) — see module docstring: no live record to open ------
    def open_entry(self, entry_reference: str) -> "EoiSubmissionAdminPage":
        return self.open_entry_by_edit_link(entry_reference)

    def approve(self) -> "EoiSubmissionAdminPage":
        self.click(f'button:has-text("{BUTTON_APPROVE}")')
        return self

    def reject(self, reason: str) -> "EoiSubmissionAdminPage":
        self.fill_text(FIELD_REJECTION_REASON, reason)
        self.click(f'button:has-text("{BUTTON_REJECT}")')
        return self

    def publish(self) -> "EoiSubmissionAdminPage":
        self.click(f'button:has-text("{BUTTON_PUBLISH}")')
        return self

    def reject_button_disabled_for_empty_reason(self) -> bool:
        return self.page.locator(f'button:has-text("{BUTTON_REJECT}")').is_disabled()

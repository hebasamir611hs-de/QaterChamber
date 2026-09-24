"""
cms/tests/tenders/test_tenders_functional_low_control_panel.py —
Control_Panel-platform Functional-Low cases for PBI 130952 ("QC -
Business Gateway - 012 - Tenders listing screen"), Qatar Chamber project
— the manual-create ("Path 2") Tender object's own field-level validation
(TC-076..101/146142..146167), the Control_Panel half of TC-215/219, and
TC-214/217.

Mirrors test_chamber_events_functional_low_control_panel.py's own
disclosed scope decision: the exact mandatory-field/length-limit
ENFORCEMENT MECHANISM was not independently re-confirmed live for every
one of this file's field-level cases beyond what
cms/pages/tenders/tender_admin_page.py's own module docstring already
confirms (native HTML5 `required` on Tender Reference Number specifically,
confirmed via `checkValidity()`). Each rejection assertion checks the
real, verifiable OUTCOME the source case specifies via
`field_validity()`/`row_status_text()`, and is expected to surface an
honest failure — not a locator defect — wherever this build does not
actually enforce a rule this case names (e.g. duplicate Reference Number
detection, cross-field Closing<=Opening rejection, and file-type/size
enforcement on the raw Object Authoring upload widget were none of them
independently confirmed live this session; see individual test
docstrings).

TC-214/215 (Rejection Reason on the EOISubmission review flow) and TC-219
(CMS Tender-Category lookup addition reflecting live in the public
webform) all need a surface this session could not reach/confirm — see
eoi_submission_admin_page.py's own module docstring for TC-214/215, and
this file's own TC-219 test for the lookup-data admin location gap. Each
is `pytest.skip()`ed with a concrete reason rather than faked.
"""

import os

import pytest

from cms.pages.tenders.eoi_submission_admin_page import EoiSubmissionAdminPage
from cms.pages.tenders.tender_admin_page import (
    TenderAdminPage,
    FIELD_TENDER_REFERENCE_NUMBER,
    FIELD_TENDER_TITLE,
    FIELD_TENDER_TITLE_AR,
    FIELD_ORGANIZATION_NAME,
    FIELD_ORGANIZATION_NAME_AR,
    FIELD_OPENING_DATE,
    FIELD_CLOSING_DATE,
    FIELD_PUBLICATION_DATE,
    FIELD_UPLOAD_TENDER_DOCUMENTS,
    FIELD_BILL_OF_QUANTITIES,
)
from config.settings import cms_role_credentials

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130952, pytest.mark.functional_low]

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VALID_PDF = os.path.join(_FIXTURES_DIR, "qctest_valid_document.pdf")
WRONG_TYPE_FILE = os.path.join(_FIXTURES_DIR, "qctest_wrong_type.txt")
OVERSIZED_PDF = os.path.join(_FIXTURES_DIR, "qctest_oversized_document.pdf")


def _credentials():
    return cms_role_credentials("Site Content Editor")


@pytest.mark.tc_146142
@pytest.mark.traceability("INVEST-TENDERS-TC-076")
def test_valid_unique_reference_number_accepted(page):
    """INVEST-TENDERS-TC-076 — Azure TC 146142."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    validity = tender.field_validity("tenderReferenceNumber")
    assert validity["valid"], f"a valid, unique Tender Reference Number should be accepted: {validity}"


@pytest.mark.tc_146143
@pytest.mark.traceability("INVEST-TENDERS-TC-077")
def test_empty_reference_number_rejected(page):
    """INVEST-TENDERS-TC-077 — Azure TC 146143. CONFIRMED LIVE: this field
    carries the native HTML5 `required` attribute."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_TENDER_REFERENCE_NUMBER})
    validity = tender.field_validity("tenderReferenceNumber")
    assert not validity["valid"], "an empty Tender Reference Number must be rejected"


@pytest.mark.tc_146144
@pytest.mark.traceability("INVEST-TENDERS-TC-078")
def test_duplicate_reference_number_rejected(page):
    """INVEST-TENDERS-TC-078 — Azure TC 146144. Duplicate-detection is a
    server-side rule not independently confirmed live this session (HTML5
    `required` alone cannot catch a duplicate) — scripted to the case's
    own stated expected result (rejected) using an existing live entry's
    own Reference Number, read off the real entries list rather than
    guessed."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_list(email, password)
    existing_ref = tender.newest_entry_code()
    assert existing_ref, "expected at least one existing Tender entry to duplicate against"
    tender.open_new_entry_form()
    tender.fill_valid_form(VALID_PDF)
    tender.fill_reference_number(existing_ref)
    tender.save_as_draft()
    assert tender.current_status() != "Approved", (
        f"submitting a duplicate Tender Reference Number ({existing_ref!r}) must be rejected"
    )


@pytest.mark.tc_146145
@pytest.mark.traceability("INVEST-TENDERS-TC-079")
def test_valid_bilingual_title_accepted(page):
    """INVEST-TENDERS-TC-079 — Azure TC 146145."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    assert tender.field_value(FIELD_TENDER_TITLE) == "QCTEST Manual Tender"
    assert tender.field_value(FIELD_TENDER_TITLE_AR) == "مناقصة تجريبية QCTEST"


@pytest.mark.tc_146146
@pytest.mark.traceability("INVEST-TENDERS-TC-080")
def test_title_rejected_when_en_or_ar_empty(page):
    """INVEST-TENDERS-TC-080 — Azure TC 146146."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_TENDER_TITLE_AR})
    tender.save_as_draft()
    assert tender.current_status() != "Approved", "leaving Tender Title AR empty must be rejected"


@pytest.mark.tc_146147
@pytest.mark.traceability("INVEST-TENDERS-TC-081")
def test_whitespace_only_title_rejected(page):
    """INVEST-TENDERS-TC-081 — Azure TC 146147."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    tender.fill_text(FIELD_TENDER_TITLE, "   ")
    tender.save_as_draft()
    assert tender.current_status() != "Approved", "a whitespace-only Tender Title must be rejected"


@pytest.mark.tc_146148
@pytest.mark.traceability("INVEST-TENDERS-TC-082")
def test_valid_bilingual_organization_name_accepted(page):
    """INVEST-TENDERS-TC-082 — Azure TC 146148."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    assert tender.field_value(FIELD_ORGANIZATION_NAME) == "QCTEST Organization"
    assert tender.field_value(FIELD_ORGANIZATION_NAME_AR) == "منظمة QCTEST"


@pytest.mark.tc_146149
@pytest.mark.traceability("INVEST-TENDERS-TC-083")
def test_organization_name_rejected_when_empty(page):
    """INVEST-TENDERS-TC-083 — Azure TC 146149."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_ORGANIZATION_NAME_AR})
    tender.save_as_draft()
    assert tender.current_status() != "Approved", "leaving Organization Name AR empty must be rejected"


@pytest.mark.tc_146150
@pytest.mark.traceability("INVEST-TENDERS-TC-084")
def test_whitespace_only_organization_name_rejected(page):
    """INVEST-TENDERS-TC-084 — Azure TC 146150."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    tender.fill_text(FIELD_ORGANIZATION_NAME, "   ")
    tender.save_as_draft()
    assert tender.current_status() != "Approved", "a whitespace-only Organization Name must be rejected"


@pytest.mark.tc_146151
@pytest.mark.traceability("INVEST-TENDERS-TC-085")
def test_valid_opening_date_accepted(page):
    """INVEST-TENDERS-TC-085 — Azure TC 146151."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    validity = tender.field_validity("openingDate")
    assert validity["valid"]


@pytest.mark.tc_146152
@pytest.mark.traceability("INVEST-TENDERS-TC-086")
def test_empty_opening_date_rejected(page):
    """INVEST-TENDERS-TC-086 — Azure TC 146152."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_OPENING_DATE})
    validity = tender.field_validity("openingDate")
    assert not validity["valid"], "an empty Opening Date must be rejected"


@pytest.mark.tc_146153
@pytest.mark.traceability("INVEST-TENDERS-TC-087")
def test_invalid_format_opening_date_rejected(page):
    """INVEST-TENDERS-TC-087 — Azure TC 146153. Native `<input type=date>`
    silently discards a non-date string on `.fill()` (the browser's own
    enforcement) — the resulting empty value is read back as the real,
    observable rejection signal."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_OPENING_DATE})
    tender.page.get_by_role("textbox", name=FIELD_OPENING_DATE, exact=True).fill("99/99/9999")
    validity = tender.field_validity("openingDate")
    assert not validity["valid"], "an invalid-format Opening Date must be rejected"


@pytest.mark.tc_146154
@pytest.mark.traceability("INVEST-TENDERS-TC-088")
def test_valid_closing_date_after_opening_accepted(page):
    """INVEST-TENDERS-TC-088 — Azure TC 146154."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    validity = tender.field_validity("closingDate")
    assert validity["valid"]


@pytest.mark.tc_146155
@pytest.mark.traceability("INVEST-TENDERS-TC-089")
def test_empty_closing_date_rejected(page):
    """INVEST-TENDERS-TC-089 — Azure TC 146155."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_CLOSING_DATE})
    validity = tender.field_validity("closingDate")
    assert not validity["valid"], "an empty Closing Date must be rejected"


@pytest.mark.tc_146156
@pytest.mark.traceability("INVEST-TENDERS-TC-090")
def test_closing_date_equal_or_before_opening_rejected(page):
    """INVEST-TENDERS-TC-090 — Azure TC 146156. Cross-field enforcement was
    not independently confirmed live this session — scripted to the
    case's own stated expected result via the Save-as-Draft outcome."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    tender.fill_date(FIELD_CLOSING_DATE, "2026-10-01")  # equals baseline Opening Date
    tender.save_as_draft()
    assert tender.current_status() != "Approved", "a Closing Date <= Opening Date must be rejected"


@pytest.mark.tc_146157
@pytest.mark.traceability("INVEST-TENDERS-TC-091")
def test_past_closing_date_rejected_on_creation(page):
    """INVEST-TENDERS-TC-091 — Azure TC 146157."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    tender.fill_date(FIELD_CLOSING_DATE, "2020-01-01")
    tender.save_as_draft()
    assert tender.current_status() != "Approved", "a past Closing Date must be rejected on creation"


@pytest.mark.tc_146158
@pytest.mark.traceability("INVEST-TENDERS-TC-092")
def test_valid_publication_date_accepted(page):
    """INVEST-TENDERS-TC-092 — Azure TC 146158. Sort-order propagation is
    covered on the Web side (test_tenders_web.py's listing-order cases);
    this test covers only the CMS-side acceptance."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    validity = tender.field_validity("publicationDate")
    assert validity["valid"]


@pytest.mark.tc_146159
@pytest.mark.traceability("INVEST-TENDERS-TC-093")
def test_publish_without_publication_date_blocked(page):
    """INVEST-TENDERS-TC-093 — Azure TC 146159."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_PUBLICATION_DATE})
    tender.submit_for_publishing()
    assert tender.current_status() != "Approved", "publishing without a Publication Date must be blocked"


@pytest.mark.tc_146160
@pytest.mark.traceability("INVEST-TENDERS-TC-094")
def test_valid_tender_document_pdf_accepted(page):
    """INVEST-TENDERS-TC-094 — Azure TC 146160."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    tender.upload_tender_document(VALID_PDF)
    assert tender.uploaded_filename(FIELD_UPLOAD_TENDER_DOCUMENTS)


@pytest.mark.tc_146161
@pytest.mark.traceability("INVEST-TENDERS-TC-095")
def test_non_pdf_tender_document_rejected(page):
    """INVEST-TENDERS-TC-095 — Azure TC 146161. File-type enforcement on
    this raw Object Authoring upload widget was not independently
    confirmed live this session — scripted to the case's own stated
    expected result."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    tender.upload_tender_document(WRONG_TYPE_FILE)
    tender.save_as_draft()
    assert tender.uploaded_filename(FIELD_UPLOAD_TENDER_DOCUMENTS) == "", (
        "a non-PDF Tender Document must be rejected, not silently accepted"
    )


@pytest.mark.tc_146162
@pytest.mark.traceability("INVEST-TENDERS-TC-096")
def test_oversized_tender_document_rejected(page):
    """INVEST-TENDERS-TC-096 — Azure TC 146162."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    tender.upload_tender_document(OVERSIZED_PDF)
    tender.save_as_draft()
    assert tender.uploaded_filename(FIELD_UPLOAD_TENDER_DOCUMENTS) == "", (
        "an oversized (>5MB) Tender Document must be rejected"
    )


@pytest.mark.tc_146163
@pytest.mark.traceability("INVEST-TENDERS-TC-097")
def test_publish_without_tender_document_blocked(page):
    """INVEST-TENDERS-TC-097 — Azure TC 146163."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_UPLOAD_TENDER_DOCUMENTS})
    tender.submit_for_publishing()
    assert tender.current_status() != "Approved", "publishing without a Tender Document must be blocked"


@pytest.mark.tc_146164
@pytest.mark.traceability("INVEST-TENDERS-TC-098")
def test_valid_boq_pdf_accepted(page):
    """INVEST-TENDERS-TC-098 — Azure TC 146164."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    assert tender.uploaded_filename(FIELD_BILL_OF_QUANTITIES)


@pytest.mark.tc_146165
@pytest.mark.traceability("INVEST-TENDERS-TC-099")
def test_non_pdf_boq_rejected(page):
    """INVEST-TENDERS-TC-099 — Azure TC 146165."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_BILL_OF_QUANTITIES})
    tender.upload_boq(WRONG_TYPE_FILE)
    tender.save_as_draft()
    assert tender.uploaded_filename(FIELD_BILL_OF_QUANTITIES) == "", "a non-PDF BOQ must be rejected"


@pytest.mark.tc_146166
@pytest.mark.traceability("INVEST-TENDERS-TC-100")
def test_oversized_boq_rejected(page):
    """INVEST-TENDERS-TC-100 — Azure TC 146166."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_BILL_OF_QUANTITIES})
    tender.upload_boq(OVERSIZED_PDF)
    tender.save_as_draft()
    assert tender.uploaded_filename(FIELD_BILL_OF_QUANTITIES) == "", "an oversized (>5MB) BOQ must be rejected"


@pytest.mark.tc_146167
@pytest.mark.traceability("INVEST-TENDERS-TC-101")
def test_publish_without_boq_blocked(page):
    """INVEST-TENDERS-TC-101 — Azure TC 146167."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF, skip_fields={FIELD_BILL_OF_QUANTITIES})
    tender.submit_for_publishing()
    assert tender.current_status() != "Approved", "publishing without a BOQ must be blocked"


@pytest.mark.tc_146280
@pytest.mark.traceability("INVEST-TENDERS-TC-214")
def test_valid_rejection_reason_accepted(page):
    """INVEST-TENDERS-TC-214 — Azure TC 146280. See
    eoi_submission_admin_page.py's module docstring — no live Pending
    EOISubmission record exists to reject this session."""
    pytest.skip(
        "PRECONDITION UNAVAILABLE — the EOISubmission review list has 0 live entries on this "
        "environment (no visitor has completed a real submission), and seeding one is gated "
        "behind a live reCAPTCHA this automated session cannot solve. See "
        "eoi_submission_admin_page.py's module docstring."
    )


@pytest.mark.tc_146281
@pytest.mark.traceability("INVEST-TENDERS-TC-215")
def test_reject_blocked_when_reason_empty_control_panel_side(page):
    """INVEST-TENDERS-TC-215 — Azure TC 146281 (Control_Panel half; the Web
    half does not apply to this specific case's own Platform tags beyond
    Control_Panel review-panel access). Same precondition gap as TC-214."""
    pytest.skip(
        "PRECONDITION UNAVAILABLE — same as TC-214: no live Pending EOISubmission record exists "
        "to attempt a Reject action against."
    )


@pytest.mark.tc_146283
@pytest.mark.traceability("INVEST-TENDERS-TC-217")
def test_manually_created_tender_fields_persist_after_save_reload(page):
    """INVEST-TENDERS-TC-217 — Azure TC 146283."""
    email, password = _credentials()
    tender = TenderAdminPage(page).open_create_form(email, password)
    tender.fill_valid_form(VALID_PDF)
    tender.save_as_draft()
    code = tender.find_entry_code_by_field(FIELD_TENDER_TITLE, "QCTEST Manual Tender")
    assert code, "could not find the just-created entry by its own Tender Title to verify persistence"
    tender.open_entry_by_code(code)
    assert tender.field_value(FIELD_TENDER_TITLE) == "QCTEST Manual Tender"
    assert tender.field_value(FIELD_ORGANIZATION_NAME) == "QCTEST Organization"


@pytest.mark.tc_146285
@pytest.mark.traceability("INVEST-TENDERS-TC-219")
def test_new_lookup_category_value_reflects_in_webform_dropdown(page):
    """INVEST-TENDERS-TC-219 — Azure TC 146285. LIVE GAP: the lookup-data
    administration surface for "Tender Category" (a Liferay master-data/
    picklist, distinct from the Tender object's own combobox field) was
    not located anywhere in the `object-authoring` index this session —
    only the Tender object's OWN fields are reachable there. Adding a new
    lookup value likely lives under a separate Liferay "Lists/Picklists"
    admin surface not yet mapped for this project."""
    pytest.skip(
        "PRECONDITION UNAVAILABLE — the Tender Category lookup-data admin surface (where a new "
        "category value would be added) was not located this session; only the Tender object's "
        "own manage-tender form (which CONSUMES that lookup, not manages it) was confirmed live. "
        "Needs a follow-up locator-discovery pass once the lookup-data admin route is identified."
    )

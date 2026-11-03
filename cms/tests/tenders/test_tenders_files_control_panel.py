"""
cms/tests/tenders/test_tenders_files_control_panel.py —
Control_Panel Tender Document / BOQ cases for PBI 130952 ("QC - Business
Gateway - 012 - Tenders listing screen"), Azure plan 137724 / suite 140383, on
the `manage-tender` Object Authoring surface (manual-create path).

Covers 146160-146167:
  - 146160 / 146164  a valid PDF (<= 5 MB) is stored and downloadable from the
                     public detail page;
  - 146161 / 146165  a non-PDF (.docx / .xlsx) is rejected with a file-type error;
  - 146162 / 146166  a 6 MB PDF is rejected with a size error;
  - 146163 / 146167  Publish without the file is blocked.

Pattern (PBI 130712 / 130710 editorial-workflow rework):
  - Every case runs as the Site Content Editor (156488) in an auth-free
    context; the signed-in userId is re-checked before each Publish. The
    cases name no role — the Editor owns the full content lifecycle; its
    submit button reads "Publish" (direct to Published).
  - The four upload-rejection cases run on an UNSAVED create form: nothing is
    created. The two publish-blocked cases fill a complete, otherwise-valid
    form (the missing file is the only gap), click Publish and require
    (a) refusal evidence pointing at the field and (b) NO record created.
  - Records are disposable: Reference Number and Tender Title both start
    `QCTEST-130952-D-<tc>-<stamp>`. Identity (ref + title + entry id + code)
    is captured right after creation by diffing the list's entry ids; the
    teardown deletes only that captured record through the guarded delete.
    The 15 real tenders (codes QC-TENDER-130952-NN) are never touched.
  - Public checks: the stored Active Status is verified first (re-opened
    record), then a fresh logged-out context opens the detail page and
    downloads the file anonymously (status 200, real PDF, same byte size).
  - Wording-only differences (the rejection works, only the message differs
    from the case) PASS and are recorded as a LOW wording finding (Allure +
    reports/evidence/tenders_130952_d/wording_findings.jsonl).

Data (case literal -> fixture; uploaded as uniquely named copies because
Documents & Media refuses a second upload of the same file name):
  tender_doc.pdf 1.2MB   -> fixtures/tender_qctest_tender_doc_1_2mb.pdf
  tender_doc.docx        -> fixtures/tender_qctest_tender_doc.docx
  tender_doc_6mb.pdf     -> fixtures/tender_qctest_tender_doc_6mb.pdf
  boq.pdf 800KB          -> fixtures/tender_qctest_boq_800kb.pdf
  boq.xlsx               -> fixtures/tender_qctest_boq.xlsx
  boq_6mb.pdf            -> fixtures/tender_qctest_boq_6mb.pdf
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.tenders.tender_admin_page import (
    B_MSG_BOQ_REQUIRED,
    B_MSG_SAVED_AND_PUBLISHED,
    B_MSG_TENDER_DOC_REQUIRED,
    B_ROLE_EDITOR,
    B_ROLE_USER_IDS,
    D_QCTEST_PREFIX,
    K_BOQ,
    K_REF,
    K_TENDER_DOCUMENT,
    K_TITLE,
    TenderEntryD,
    TenderFilesAdminPage,
    TenderPublicViewB,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130952,
              pytest.mark.functional_low, pytest.mark.xdist_group("tenders_cms_files_d")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
DOC_PDF = os.path.join(FIXTURES, "tender_qctest_tender_doc_1_2mb.pdf")
DOC_DOCX = os.path.join(FIXTURES, "tender_qctest_tender_doc.docx")
DOC_6MB = os.path.join(FIXTURES, "tender_qctest_tender_doc_6mb.pdf")
BOQ_PDF = os.path.join(FIXTURES, "tender_qctest_boq_800kb.pdf")
BOQ_XLSX = os.path.join(FIXTURES, "tender_qctest_boq.xlsx")
BOQ_6MB = os.path.join(FIXTURES, "tender_qctest_boq_6mb.pdf")
STAMP = datetime.now().strftime("%m%d%H%M%S")

PUBLISH_CONFIRM_TIMEOUT = 120.0
PUBLIC_REFLECT_TIMEOUT = 5.0   # cms-profile.md: poll 5 s @ 0.5 s
PUBLIC_POLL = 0.5
FILE_TYPE_PATTERN = r"type|extension|\.pdf|pdf|format|not allowed|unsupported|valid"
FILE_SIZE_PATTERN = r"size|large|exceed|\d+\s*MB"
WORDING_LOG = os.path.join(TenderFilesAdminPage.EVIDENCE_DIR, "wording_findings.jsonl")


def _ref(tc_id: str) -> str:
    return f"{D_QCTEST_PREFIX}{tc_id}-{STAMP}"


def _title(tc_id: str, suffix: str) -> str:
    return f"{D_QCTEST_PREFIX}{tc_id}-{STAMP} {suffix}"


def _data(tc_id: str, suffix: str, **overrides) -> dict:
    """A complete, valid tender: both PDFs, Active Status ticked, Status =
    Published, Closing Date in the future, Publication Date today."""
    data = TenderFilesAdminPage.default_tender_data(
        _ref(tc_id), _title(tc_id, suffix), DOC_PDF, publicationDate=date.today().strftime("%d/%m/%Y"))
    data[K_BOQ] = BOQ_PDF
    data[f"{K_TENDER_DOCUMENT}_stem"] = "tender_doc"
    data[f"{K_BOQ}_stem"] = "boq"
    data.update(overrides)
    return data


# ===========================================================================
# Fixtures
# ===========================================================================
class DisposableRegistry:
    def __init__(self):
        self._entries: dict[str, TenderEntryD] = {}

    @property
    def entries(self) -> list[TenderEntryD]:
        return list(self._entries.values())

    def track(self, entry: TenderEntryD) -> TenderEntryD:
        if not isinstance(entry, TenderEntryD) or not entry.in_namespace():
            raise ValueError(f"{entry} is not a {D_QCTEST_PREFIX} record")
        self._entries[entry.entry_id] = entry
        return entry


@pytest.fixture
def disposable(browser):
    """Deletes ONLY the records the test registered at creation (guarded delete),
    from a TEST_USER context. Anything it cannot remove fails the teardown loudly."""
    registry = DisposableRegistry()
    yield registry
    if not registry.entries:
        return
    ctx = new_context(browser)
    outcome, failures = [], []
    try:
        cleaner = TenderFilesAdminPage(ctx.new_page())
        for entry in registry.entries:
            label = f"{entry.title!r} ref {entry.reference!r} (id {entry.entry_id}, code {entry.code})"
            try:
                cleaner.open_list_all()
                if not cleaner.row_present(entry):
                    if cleaner.is_list_fully_expanded():
                        outcome.append(f"already gone: {label}")
                    else:
                        failures.append(f"{label}: not found and the list is NOT fully expanded")
                    continue
                cleaner.adopt_d(entry)
                if cleaner.delete_own_entry_d(entry):
                    outcome.append(f"removed {label}")
                else:
                    failures.append(f"NOT removed {label}: guarded delete refused/failed (see log)")
            except Exception as exc:  # noqa: BLE001 — collected below
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def anon_page(browser):
    """A fresh logged-out context for the public read."""
    ctx = new_context(browser, use_auth_state=False)
    yield ctx.new_page()
    ctx.close()


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def _editor(page) -> TenderFilesAdminPage:
    admin = TenderFilesAdminPage(page)
    outcome = admin.login_as_role(B_ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip("PRECONDITION: Liferay refused the .env credentials for 'Site Content Editor'")
    if outcome != "ok":
        pytest.fail("login as 'Site Content Editor' neither succeeded nor showed Liferay's refusal banner")
    admin.open_list_all()
    user_id, _ = admin.signed_in_user()
    if user_id != B_ROLE_USER_IDS[B_ROLE_EDITOR]:
        pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not 156488")
    return admin


def _pinned(admin: TenderFilesAdminPage) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == B_ROLE_USER_IDS[B_ROLE_EDITOR], (
        f"the session is now userId {user_id!r}, not the pinned Site Content Editor (156488)")


def _register(admin, disposable, data: dict, ids_before: set) -> TenderEntryD | None:
    try:
        entry = admin.identify_created_d(data[K_REF], data[K_TITLE], ids_before)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001 — registration must not mask the result
        allure.attach(repr(exc), name=f"registration of {data[K_REF]!r} failed")
        return None


def _record_wording(tc_id: str, field: str, expected: str, shown: str, evidence_png: str) -> None:
    finding = {"tc": tc_id, "field": field, "expected": expected, "shown": shown, "screenshot": evidence_png}
    allure.attach(json.dumps(finding, ensure_ascii=False, indent=1), name="LOW wording finding (block works)")
    os.makedirs(os.path.dirname(WORDING_LOG), exist_ok=True)
    with open(WORDING_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False) + "\n")


def _attempt_publish(admin, data: dict, tc_id: str, what: str) -> dict:
    """Fills a NEW form from `data` and clicks Publish."""
    admin.open_create_form_en()
    admin.fill_tender(data)
    _pinned(admin)
    admin.click_publish()
    shot = admin.evidence(f"{tc_id}_{what}_after_publish")
    return {"went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
            "evidence": admin.refusal_evidence(), "messages": admin.all_messages_text(), "screenshot": shot}


def _create_published(admin, disposable, data: dict, tc_id: str) -> TenderEntryD:
    """Creates + publishes one tender, registers it for teardown, THEN asserts."""
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt_publish(admin, data, tc_id, "create")
        if result["went_through"]:
            result["success_messages"] = admin.success_messages(B_MSG_SAVED_AND_PUBLISHED, 10.0)
    finally:
        entry = _register(admin, disposable, data, ids_before)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"create {data[K_REF]!r}")
    assert result.get("went_through"), (
        f"Publishing {data[K_TITLE]!r} did not go through: {result.get('evidence')} | {result.get('messages')}")
    assert entry is not None, f"{data[K_REF]!r} went through but is not identifiable as exactly one NEW record"
    return entry


def _wait_published(admin, entry: TenderEntryD) -> None:
    seen = {"status": ""}

    def _reached() -> bool:
        admin.open_list_all()
        seen["status"] = admin.row_status(entry)
        return seen["status"] == STATUS_PUBLISHED

    try:
        wait_until(_reached, timeout=PUBLISH_CONFIRM_TIMEOUT, poll=3.0)
    except WaitTimeoutError:
        pass
    assert seen["status"] == STATUS_PUBLISHED, f"{entry.title!r} never reached Published (last {seen['status']!r})"


def _require_active_status(admin, entry: TenderEntryD) -> None:
    admin.open_entry_en(entry.code)
    stored = admin.active_status_stored()
    allure.attach(f"stored Active Status: {stored!r}", name="Active Status precondition")
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title!r} stores Active Status {stored!r}; "
                    f"the public step was not run")


def _assert_stored_file(admin, entry: TenderEntryD, key: str, uploaded_as: str) -> None:
    admin.open_entry_en(entry.code)
    stored = admin.stored_file_name(key)
    allure.attach(f"uploaded as {uploaded_as!r}; stored {stored!r}", name=f"{key} stored file")
    assert os.path.splitext(uploaded_as)[0] in stored, (
        f"the reopened record stores {key} {stored!r}, but {uploaded_as!r} was uploaded "
        f"(field block: {admin.upload_block_text(key)!r})")


def _assert_downloadable(anon_page, entry: TenderEntryD, row_label: str, fixture: str) -> None:
    """Logged-out detail page shows a `row_label` file row whose link downloads the same PDF."""
    view = TenderPublicViewB(anon_page)
    state = {"rows": []}

    def _shown() -> bool:
        view.open_detail(entry.code)
        state["rows"] = [r for r in view.file_rows() if row_label.lower() in r["text"].lower()]
        return bool(state["rows"] and state["rows"][0]["hrefs"])

    try:
        wait_until(_shown, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL)
    except (WaitTimeoutError, Exception):  # noqa: BLE001 — asserted below with the evidence
        pass
    view.screenshot(f"detail files {row_label}")
    assert state["rows"] and state["rows"][0]["hrefs"], (
        f"DELIVERY: the logged-out detail page of {entry.title!r} shows no {row_label!r} download: "
        f"{view.file_rows() if view.page.locator(view.FILE_ROW).count() else 'no file rows'}")
    got = view.url_status(state["rows"][0]["hrefs"][-1])
    allure.attach(json.dumps(got, indent=1), name=f"{row_label} anonymous download")
    assert got["status"] == 200 and got["is_pdf"], f"the {row_label} download is not a PDF: {got}"
    assert got["size"] == os.path.getsize(fixture), (
        f"downloaded {got['size']} bytes, uploaded {os.path.getsize(fixture)} bytes")


def _assert_upload_rejected(admin, tc_id: str, key: str, fixture: str, what: str,
                            kind_pattern: str, kind: str) -> dict:
    """Unsaved create form: the file must NOT be attached and a rejection must be shown.
    Rejection works but wording differs -> passes + LOW wording finding."""
    admin.open_create_form_en()
    result = admin.attempt_upload(key, fixture)
    result["outcome"] = admin.upload_outcome(key)
    shot = admin.evidence(f"{tc_id}_after_{what}_upload")
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"{what} upload attempt")
    # The rejection message itself quotes the file name, so "attached" is judged by
    # the value the form would submit, not by the field's text.
    assert result["outcome"]["value"] == "", (
        f"PRODUCT: the {what} was accepted — the form would submit fileEntry "
        f"{result['outcome']['value']!r} for {key}: {result['field_text']!r}; screenshot {shot}")
    shown = " | ".join(result["errors"] + result["outcome"]["field_errors"])
    assert shown or result["success"] is False, (
        f"the {what} was not attached, but no rejection message was shown at all: {result}; screenshot {shot}")
    if not re.search(kind_pattern, shown, re.I):
        _record_wording(tc_id, what, kind, shown or result.get("picker_text", ""),
                        result.get("picker_evidence") or shot)
    return result


def _assert_publish_blocked(admin, disposable, data: dict, tc_id: str, what: str,
                            field_pattern: str, expected_message: str) -> dict:
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt_publish(admin, data, tc_id, what)
    finally:
        entry = _register(admin, disposable, data, ids_before)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"refusal evidence ({what})")
    if entry is not None:
        admin.open_list_all()
        pytest.fail(f"PRODUCT: Publish with {what} was NOT blocked — a record was created "
                    f"(status {admin.row_status(entry)!r}, entry id {entry.entry_id}); "
                    f"screenshot {result.get('screenshot')}")
    assert not result.get("went_through") and result.get("refused"), (
        f"Publish with {what} was neither refused with validation evidence nor saved: {result}")
    blob = json.dumps(result["evidence"], ensure_ascii=False)
    assert re.search(field_pattern, blob, re.I), (
        f"Publish was refused, but the validation evidence does not point at {what}: {result['evidence']}")
    if expected_message not in result["messages"]:
        _record_wording(tc_id, what, expected_message, result["messages"], result["screenshot"])
    return result


# ===========================================================================
# Tender Document (146160-146163)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Document")
@allure.title("A valid Tender Document PDF (1.2MB) is stored and downloadable from the detail page")
@pytest.mark.tc_146160
def test_valid_tender_document_pdf_accepted(page, disposable, anon_page):
    """Azure TC 146160 | Site Content Editor (156488)."""
    # Arrange
    admin = _editor(page)
    data = _data("146160", "Tender Document upload")
    # Act
    entry = _create_published(admin, disposable, data, "146160")
    # Assert
    _assert_stored_file(admin, entry, K_TENDER_DOCUMENT, data[f"{K_TENDER_DOCUMENT}_uploaded_as"])
    _wait_published(admin, entry)
    _require_active_status(admin, entry)
    _assert_downloadable(anon_page, entry, "Tender document", DOC_PDF)


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Document")
@allure.title("A non-PDF Tender Document (.docx) is rejected with a file-type error")
@pytest.mark.tc_146161
def test_non_pdf_tender_document_rejected(page):
    """Azure TC 146161 | unsaved form, nothing created."""
    admin = _editor(page)
    _assert_upload_rejected(admin, "146161", K_TENDER_DOCUMENT, DOC_DOCX, "tender_doc.docx",
                            FILE_TYPE_PATTERN, "a file-type error")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Document")
@allure.title("An oversized Tender Document (6MB PDF) is rejected with a size error")
@pytest.mark.tc_146162
def test_oversized_tender_document_rejected(page):
    """Azure TC 146162 | unsaved form, nothing created."""
    admin = _editor(page)
    _assert_upload_rejected(admin, "146162", K_TENDER_DOCUMENT, DOC_6MB, "tender_doc_6mb.pdf",
                            FILE_SIZE_PATTERN, "a size error")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Document")
@allure.title("Publishing (manual path) without a Tender Document is blocked")
@pytest.mark.tc_146163
def test_publish_without_tender_document_blocked(page, disposable):
    """Azure TC 146163 | complete form minus the Tender Document; no record may be created."""
    admin = _editor(page)
    _assert_publish_blocked(admin, disposable, _data("146163", "No Tender Document", tenderDocument=None),
                            "146163", "no Tender Document", r"tenderDocument|Tender Documents",
                            B_MSG_TENDER_DOC_REQUIRED)


# ===========================================================================
# Bill of Quantities (146164-146167)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("BOQ")
@allure.title("A valid BOQ PDF (800KB) is stored and downloadable from the detail page")
@pytest.mark.tc_146164
def test_valid_boq_pdf_accepted(page, disposable, anon_page):
    """Azure TC 146164 | Site Content Editor (156488)."""
    admin = _editor(page)
    data = _data("146164", "BOQ upload")
    entry = _create_published(admin, disposable, data, "146164")
    _assert_stored_file(admin, entry, K_BOQ, data[f"{K_BOQ}_uploaded_as"])
    _wait_published(admin, entry)
    _require_active_status(admin, entry)
    _assert_downloadable(anon_page, entry, "Bill of Quantities", BOQ_PDF)


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("BOQ")
@allure.title("A non-PDF BOQ (.xlsx) is rejected with a file-type error")
@pytest.mark.tc_146165
def test_non_pdf_boq_rejected(page):
    """Azure TC 146165 | unsaved form, nothing created."""
    admin = _editor(page)
    _assert_upload_rejected(admin, "146165", K_BOQ, BOQ_XLSX, "boq.xlsx", FILE_TYPE_PATTERN, "a file-type error")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("BOQ")
@allure.title("An oversized BOQ (6MB PDF) is rejected with a size error")
@pytest.mark.tc_146166
def test_oversized_boq_rejected(page):
    """Azure TC 146166 | unsaved form, nothing created."""
    admin = _editor(page)
    _assert_upload_rejected(admin, "146166", K_BOQ, BOQ_6MB, "boq_6mb.pdf", FILE_SIZE_PATTERN, "a size error")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("BOQ")
@allure.title("Publishing (manual path) without a BOQ is blocked")
@pytest.mark.tc_146167
def test_publish_without_boq_blocked(page, disposable):
    """Azure TC 146167 | complete form minus the BOQ; no record may be created."""
    admin = _editor(page)
    _assert_publish_blocked(admin, disposable, _data("146167", "No BOQ", billOfQuantities=None),
                            "146167", "no BOQ", r"billOfQuantities|Bill of Quantities", B_MSG_BOQ_REQUIRED)

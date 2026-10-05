"""
cms/tests/tenders/test_tenders_fields_control_panel.py —
Control_Panel field-validation cases for PBI 130952 ("QC - Business Gateway -
012 - Tenders listing screen"), Azure plan 137724 / suite 140383, on the
`manage-tender` Object Authoring surface (manual-create path).

Covers 146142-146159 (Reference Number, bilingual Tender Title, Organization
Name, Opening / Closing / Publication Date) and the CMS half of 146295 (Closing
Date == Opening Date; the public-webform half lives in
web/tests/tenders/test_tenders_web.py under the same tc marker). The Tender
Document / BOQ cases 146160-146167 live in test_tenders_files_control_panel.py.
Supersedes the pre-workflow test_tenders_functional_low_control_panel.py.

Pattern (PBI 130712 / 130710 editorial-workflow rework):
  - Every case runs as the Site Content Editor (156488) in an auth-free
    context; the signed-in userId is re-checked before each save. The
    cases name no role — the Editor owns the full content lifecycle. The
    Editor's submit button reads "Publish" (direct to Published).
  - "Save" in a required/invalid-value case = the Editor's Publish: Save as
    Draft skips required-field validation (standards.md), so it cannot prove
    a value is accepted or rejected. Every rejection case fills a complete,
    otherwise-valid form so the field under test is the only invalid one, and
    requires (a) refusal evidence, (b) NO record created.
  - Records are disposable: Reference Number `QCTEST-130952-B-<tc>-<stamp>…`
    and Tender Title `QCTEST-130952-B-<tc>-<stamp> …`. Identity (ref + title +
    entry id + code) is captured right after creation by diffing the list's
    entry ids; teardown deletes only that captured record through the
    guarded delete. The 15 real tenders are never touched.
  - Public checks: stored Active Status is verified first (re-opened record),
    then a fresh logged-out context polls the listing/detail (cms-profile.md
    budget 5 s @ 0.5 s once the CMS shows Published).
  - Wording-only differences (the block works, only the message differs from
    the case) PASS and are recorded as a low-priority wording finding
    (attached to Allure and appended to
    reports/evidence/tenders_130952_b/wording_findings.jsonl).

Substitutions disclosed (case literal -> what runs):
  - Reference `QC-ET-2026-099` -> `QCTEST-130952-B-146142-<stamp>-QC-ET-2026-099`.
  - Duplicate reference `QC-ET-2026-041` (146144) -> the test first creates its
    OWN tender with `QCTEST-130952-B-146144-<stamp>-QC-ET-2026-041`, then tries
    a second tender with the same reference (never collides with real data).
  - Titles keep the case literal as a suffix after the QCTEST prefix.
  - 146154 (valid Opening 20/08/2026, Closing 18/09/2026): run as written
    first; both dates are now in the past (today 2026-10-05) — if the save is
    refused for a past date, it is retried once with the same dates +1 year
    and that is reported.
  - 146156 / 146295 (relational rule): run with 20/08/2027 / 15/08/2027 so a
    past-date rule cannot be the reason for the refusal.
  - Every record carries valid Tender Document / BOQ PDFs
    (fixtures/tender_qctest_tender_doc_1_2mb.pdf, tender_qctest_boq_800kb.pdf),
    uploaded as uniquely named copies.

SKIPPED: 146291, 146294 — tagged Manual, not automated.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.tenders.tender_admin_page import (
    B_MSG_SAVED_AND_PUBLISHED,
    B_QCTEST_PREFIX,
    B_ROLE_EDITOR,
    B_ROLE_USER_IDS,
    K_BOQ,
    K_CLOSING,
    K_OPENING,
    K_ORG,
    K_PUBLICATION,
    K_REF,
    K_TITLE,
    TenderCreatedEntry,
    TenderFieldsAdminPage,
    TenderPublicViewB,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130952,
              pytest.mark.xdist_group("tenders_cms_fields_b")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
DOC_PDF = os.path.join(FIXTURES, "tender_qctest_tender_doc_1_2mb.pdf")
BOQ_PDF = os.path.join(FIXTURES, "tender_qctest_boq_800kb.pdf")
STAMP = datetime.now().strftime("%m%d%H%M%S")
TODAY = date.today()

PUBLISH_CONFIRM_TIMEOUT = 120.0
PUBLIC_REFLECT_TIMEOUT = 5.0   # cms-profile.md: poll 5 s @ 0.5 s
PUBLIC_POLL = 0.5
MANUAL_SKIP = pytest.mark.skip(reason="Manual case — not automated")
WORDING_LOG = os.path.join(TenderFieldsAdminPage.EVIDENCE_DIR, "wording_findings.jsonl")


def _ref(tc_id: str, suffix: str = "") -> str:
    return f"{B_QCTEST_PREFIX}{tc_id}-{STAMP}" + (f"-{suffix}" if suffix else "")


def _title(tc_id: str, suffix: str = "Tender") -> str:
    return f"{B_QCTEST_PREFIX}{tc_id}-{STAMP} {suffix}"


def _dmy(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _data(tc_id: str, **overrides) -> dict:
    data = TenderFieldsAdminPage.default_tender_data(_ref(tc_id), _title(tc_id), DOC_PDF,
                                                     publicationDate=_dmy(TODAY))
    data[K_BOQ] = BOQ_PDF
    data.update(overrides)
    return data


# ===========================================================================
# Fixtures
# ===========================================================================
class DisposableRegistry:
    def __init__(self):
        self._entries: dict[str, TenderCreatedEntry] = {}

    @property
    def entries(self) -> list[TenderCreatedEntry]:
        return list(self._entries.values())

    def track(self, entry: TenderCreatedEntry) -> TenderCreatedEntry:
        if not entry.in_namespace():
            raise ValueError(f"{entry} is not a {B_QCTEST_PREFIX} record")
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
        cleaner = TenderFieldsAdminPage(ctx.new_page())
        for entry in registry.entries:
            label = f"{entry.title!r} ref {entry.reference!r} (id {entry.entry_id}, code {entry.code})"
            try:
                cleaner.open_list_all()
                if not cleaner.row_present(entry):
                    (outcome if cleaner.is_list_fully_expanded() else failures).append(
                        f"already gone: {label}" if cleaner.is_list_fully_expanded()
                        else f"{label}: not found and the list is NOT fully expanded")
                    continue
                cleaner.adopt(entry)
                if cleaner.delete_disposable_entry(entry):
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
def anon_pages(browser):
    """Fresh logged-out contexts for every public read; `viewport` optional."""
    contexts = []

    def _make(viewport: tuple | None = None):
        ctx = new_context(browser, viewport=viewport, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def _editor(page) -> TenderFieldsAdminPage:
    admin = TenderFieldsAdminPage(page)
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


def _pinned(admin: TenderFieldsAdminPage) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == B_ROLE_USER_IDS[B_ROLE_EDITOR], (
        f"the session is now userId {user_id!r}, not the pinned Site Content Editor (156488)")


def _register(admin, disposable, reference: str, title: str, ids_before: set) -> TenderCreatedEntry | None:
    try:
        entry = admin.identify_created(reference, title, ids_before)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001 — registration must not mask the result
        allure.attach(repr(exc), name=f"registration of {reference or title!r} failed")
        return None


def _record_wording(tc_id: str, field: str, expected: str, shown: str, evidence_png: str) -> None:
    finding = {"tc": tc_id, "field": field, "expected": expected, "shown": shown, "screenshot": evidence_png}
    allure.attach(json.dumps(finding, ensure_ascii=False, indent=1), name="LOW wording finding (block works)")
    os.makedirs(os.path.dirname(WORDING_LOG), exist_ok=True)
    with open(WORDING_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False) + "\n")


def _attempt(admin, data: dict, tc_id: str, what: str, before_publish=None) -> dict:
    """Fills a NEW form, optionally runs `before_publish(admin)`, clicks Publish."""
    admin.open_create_form_en()
    admin.fill_tender(data)
    if before_publish:
        before_publish(admin)
    _pinned(admin)
    admin.click_publish()
    shot = admin.evidence(f"{tc_id}_{what}_after_publish")
    return {"went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
            "evidence": admin.refusal_evidence(), "messages": admin.all_messages_text(), "screenshot": shot}


def _create(admin, disposable, data: dict, tc_id: str) -> TenderCreatedEntry:
    """Creates + publishes one tender, registers it for teardown, THEN asserts."""
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, data, tc_id, "create")
        admin.create_messages = admin.success_messages(B_MSG_SAVED_AND_PUBLISHED, 10.0) \
            if result["went_through"] else []
    finally:
        entry = _register(admin, disposable, data[K_REF] or "", data[K_TITLE] or "", ids_before)
    allure.attach(repr(result), name=f"create {data[K_REF]!r}")
    assert result.get("went_through"), (
        f"Publishing {data[K_TITLE]!r} did not go through: {result.get('evidence')} | {result.get('messages')}")
    assert entry is not None, f"{data[K_REF]!r} went through but is not identifiable as exactly one NEW record"
    return entry


def _assert_blocked(admin, disposable, data: dict, tc_id: str, what: str, field_pattern: str,
                    expected_kind: str | None = None, kind_pattern: str | None = None,
                    before_publish=None) -> dict:
    """Publish must be refused with validation evidence pointing at the field and NO
    record may be created. When `kind_pattern` is given (e.g. a uniqueness or
    relational message) and the refusal works but the message does not match, the
    case passes and a LOW wording finding is recorded."""
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, data, tc_id, what, before_publish)
    finally:
        entry = _register(admin, disposable, data[K_REF] or "", data[K_TITLE] or "", ids_before)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"refusal evidence ({what})")
    if entry is not None:
        admin.open_list_all()
        pytest.fail(f"PRODUCT: Publish with {what} was NOT blocked — a record was created "
                    f"(status {admin.row_status(entry)!r}, entry id {entry.entry_id}, stored title "
                    f"{entry.title!r}); screenshot {result.get('screenshot')}")
    assert not result.get("went_through") and result.get("refused"), (
        f"Publish with {what} was neither refused with validation evidence nor saved: {result}")
    blob = json.dumps(result["evidence"], ensure_ascii=False)
    assert re.search(field_pattern, blob, re.I), (
        f"Publish was refused, but the validation evidence does not point at {what}: {result['evidence']}")
    if kind_pattern and not re.search(kind_pattern, result["messages"], re.I):
        _record_wording(tc_id, what, expected_kind or kind_pattern, result["messages"], result["screenshot"])
    return result


def _wait_published(admin, entry: TenderCreatedEntry) -> str:
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
    return seen["status"]


def _require_active_status(admin, entry: TenderCreatedEntry) -> None:
    admin.open_entry_en(entry.code)
    stored = admin.active_status_stored()
    allure.attach(f"stored Active Status: {stored!r}", name="Active Status precondition")
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title!r} stores Active Status {stored!r}; "
                    f"the public step was not run")


def _public_card(anon_pages, entry: TenderCreatedEntry, locale: str = "en") -> tuple[TenderPublicViewB, dict, int]:
    view = TenderPublicViewB(anon_pages())
    state = {"index": -1}

    def _check() -> bool:
        view.open_listing_all(locale)
        state["index"] = view.card_index_by_href_code(entry.code)
        return state["index"] >= 0

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL)
    except WaitTimeoutError:
        view.screenshot("public listing at timeout")
        pytest.fail(f"DELIVERY: {entry.title!r} (code {entry.code}) never appeared on the logged-out listing")
    return view, view.cards()[state["index"]], state["index"]


def _published_and_public(admin, entry, anon_pages, locale: str = "en"):
    _wait_published(admin, entry)
    _require_active_status(admin, entry)
    return _public_card(anon_pages, entry, locale)


# ===========================================================================
# Tender Reference Number (146142-146144)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Reference Number")
@allure.title("A valid, unique Tender Reference Number is accepted on manual create")
@pytest.mark.functional_low
@pytest.mark.tc_146142
def test_valid_unique_reference_number_accepted(page, disposable):
    # Azure TC 146142 | Site Content Editor (156488)
    admin = _editor(page)
    reference = _ref("146142", "QC-ET-2026-099")
    entry = _create(admin, disposable, _data("146142", tenderReferenceNumber=reference), "146142")
    admin.open_entry_en(entry.code)
    stored = admin.text_value(K_REF)
    assert stored == reference, f"Reference Number stored as {stored!r}, not {reference!r}"
    assert any(B_MSG_SAVED_AND_PUBLISHED in m for m in admin.create_messages), (
        f"no {B_MSG_SAVED_AND_PUBLISHED!r} after the save: {admin.create_messages}")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Reference Number")
@allure.title("Leaving the Tender Reference Number empty is rejected")
@pytest.mark.functional_low
@pytest.mark.tc_146143
def test_empty_reference_number_rejected(page, disposable):
    # Azure TC 146143 | identity carried by the title (ref is empty)
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("146143", tenderReferenceNumber=""), "146143",
                    "an empty Tender Reference Number", r"tenderReferenceNumber|Reference Number")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Reference Number")
@allure.title("A duplicate Tender Reference Number is rejected")
@pytest.mark.functional_low
@pytest.mark.tc_146144
def test_duplicate_reference_number_rejected(page, disposable):
    # Azure TC 146144 | the "existing" reference is this test's own first tender
    admin = _editor(page)
    reference = _ref("146144", "QC-ET-2026-041")
    _create(admin, disposable, _data("146144", tenderReferenceNumber=reference,
                                     tenderTitle=_title("146144", "Original")), "146144")
    duplicate = _data("146144", tenderReferenceNumber=reference, tenderTitle=_title("146144", "Duplicate"))
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, duplicate, "146144", "duplicate_reference")
    finally:
        second = None
        try:
            # identify the possible second record by its unique TITLE (the ref is shared)
            admin.open_list_all()
            fresh = [r for r in admin.list_rows() if r["entry_id"] not in ids_before]
            if fresh:
                second = admin.identify_created("", duplicate[K_TITLE], ids_before)
                if second:
                    disposable.track(second)
        except Exception as exc:  # noqa: BLE001
            allure.attach(repr(exc), name="duplicate registration failed")
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name="duplicate attempt")
    if second is not None:
        pytest.fail(f"PRODUCT: a second tender with the duplicate Reference Number {reference!r} was created "
                    f"(entry id {second.entry_id}); expected a uniqueness error. Screenshot {result.get('screenshot')}")
    assert not result.get("went_through") and result.get("refused"), (
        f"the duplicate-reference publish was neither refused nor saved: {result}")
    if not re.search(r"already|unique|exist|duplicate|in use", result["messages"], re.I):
        _record_wording("146144", "duplicate Tender Reference Number", "a uniqueness error",
                        result["messages"], result["screenshot"])


# ===========================================================================
# Tender Title (146145-146147)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Title")
@allure.title("A valid bilingual Tender Title is accepted and both languages render on detail")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_146145
def test_valid_bilingual_title_accepted(page, disposable, anon_pages):
    # Azure TC 146145 | EN "Port Equipment Supply", AR equivalent
    admin = _editor(page)
    title_en = _title("146145", "Port Equipment Supply")
    title_ar = f"{B_QCTEST_PREFIX}146145-{STAMP} توريد معدات الموانئ"
    entry = _create(admin, disposable, _data("146145", tenderTitle=title_en, tenderTitle_ar=title_ar), "146145")
    admin.open_entry_en(entry.code)
    stored = (admin.text_value(K_TITLE), admin.ar_value(K_TITLE))
    assert stored == (title_en, title_ar), f"stored titles {stored!r}"
    _published_and_public(admin, entry, anon_pages)
    detail = TenderPublicViewB(anon_pages())
    shown_en = detail.open_detail(entry.code, "en").detail_header()["title"]
    detail.screenshot("146145 detail EN")
    shown_ar = detail.open_detail(entry.code, "ar").detail_header()["title"]
    detail.screenshot("146145 detail AR")
    assert shown_en == title_en, f"EN detail title reads {shown_en!r}"
    assert shown_ar == title_ar, f"AR detail title reads {shown_ar!r}"


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Title")
@allure.title("Leaving Tender Title (AR) empty with EN filled is rejected")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_146146
def test_empty_arabic_title_rejected(page, disposable):
    # Azure TC 146146
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("146146", tenderTitle_ar=""), "146146",
                    "an empty Tender Title (AR)", r"qc-ar-tenderTitle|Tender Title|العربية|Arabic")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Tender Title")
@allure.title("A whitespace-only Tender Title is rejected as empty")
@pytest.mark.functional_low
@pytest.mark.tc_146147
def test_whitespace_title_rejected(page, disposable):
    # Azure TC 146147 | identity carried by the reference number
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("146147", tenderTitle="   "), "146147",
                    "a whitespace-only Tender Title (EN)", r"tenderTitle|Tender Title")


# ===========================================================================
# Organization Name (146148-146150)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Organization Name")
@allure.title("A valid bilingual Organization Name is accepted")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_146148
def test_valid_bilingual_organization_accepted(page, disposable):
    # Azure TC 146148 | "Qatar Digital Services Authority" / AR
    admin = _editor(page)
    org_en, org_ar = "Qatar Digital Services Authority", "هيئة قطر للخدمات الرقمية"
    entry = _create(admin, disposable, _data("146148", organizationName=org_en, organizationName_ar=org_ar),
                    "146148")
    admin.open_entry_en(entry.code)
    stored = (admin.text_value(K_ORG), admin.ar_value(K_ORG))
    assert stored == (org_en, org_ar), f"stored Organization Name {stored!r}"


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Organization Name")
@allure.title("Leaving Organization Name (EN) empty is rejected")
@pytest.mark.functional_low
@pytest.mark.tc_146149
def test_empty_organization_rejected(page, disposable):
    # Azure TC 146149
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("146149", organizationName=""), "146149",
                    "an empty Organization Name (EN)", r"organizationName|Organization Name")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Organization Name")
@allure.title("A whitespace-only Organization Name is rejected")
@pytest.mark.functional_low
@pytest.mark.tc_146150
def test_whitespace_organization_rejected(page, disposable):
    # Azure TC 146150
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("146150", organizationName="   "), "146150",
                    "a whitespace-only Organization Name (EN)", r"organizationName|Organization Name")


# ===========================================================================
# Opening / Closing / Publication Date (146151-146159, 146295)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Opening Date")
@allure.title("A valid Opening Date (20/08/2026) is stored and shown on the card and detail")
@pytest.mark.functional_low
@pytest.mark.tc_146151
def test_valid_opening_date_accepted(page, disposable, anon_pages):
    # Azure TC 146151
    admin = _editor(page)
    entry = _create(admin, disposable, _data("146151", openingDate="20/08/2026"), "146151")
    admin.open_entry_en(entry.code)
    assert (admin.date_stored(K_OPENING), admin.date_text(K_OPENING)) == ("2026-08-20", "20/08/2026"), (
        f"Opening Date stored {admin.date_stored(K_OPENING)!r} / shown {admin.date_text(K_OPENING)!r}")
    view, card, _ = _published_and_public(admin, entry, anon_pages)
    assert card["dates"].get("Opens") == "20 Aug 2026", f"card dates {card['dates']}"
    text = view.open_detail(entry.code).detail_text()
    view.screenshot("146151 detail")
    assert re.search(r"Opening date\s+20 Aug 2026", text), "the detail page does not show 'Opening date 20 Aug 2026'"


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Opening Date")
@allure.title("An empty Opening Date is rejected")
@pytest.mark.functional_low
@pytest.mark.tc_146152
def test_empty_opening_date_rejected(page, disposable):
    # Azure TC 146152
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("146152", openingDate=None), "146152",
                    "an empty Opening Date", r"openingDate|Opening Date")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Opening Date")
@allure.title("An invalid-format Opening Date (32/13/2026) is rejected")
@pytest.mark.functional_low
@pytest.mark.tc_146153
def test_invalid_opening_date_rejected(page, disposable):
    # Azure TC 146153 | rejected = save blocked AND nothing stored; an invalid-date
    # message is the expected wording (missing -> LOW wording finding).
    admin = _editor(page)
    typed = {}

    def _type_invalid(a):
        a.set_date(K_OPENING, "32/13/2026")
        typed.update(box=a.date_text(K_OPENING), stored=a.date_stored(K_OPENING), inline=a.date_block_text(K_OPENING))

    result = _assert_blocked(admin, disposable, _data("146153", openingDate=None), "146153",
                             "an invalid Opening Date 32/13/2026", r"openingDate|Opening Date|date",
                             before_publish=_type_invalid)
    allure.attach(repr(typed), name="Opening Date after typing 32/13/2026")
    shown = f"{typed.get('inline', '')} | {result['messages']}"
    if not re.search(r"invalid|valid date|format|dd/mm/yyyy", shown, re.I):
        _record_wording("146153", "invalid Opening Date", "a format validation error", shown, result["screenshot"])


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Closing Date")
@allure.title("A valid Closing Date later than the Opening Date is accepted")
@pytest.mark.functional_low
@pytest.mark.tc_146154
def test_valid_closing_date_accepted(page, disposable):
    # Azure TC 146154 | Opening 20/08/2026, Closing 18/09/2026 as written; see module docstring.
    admin = _editor(page)
    literal = _data("146154", openingDate="20/08/2026", closingDate="18/09/2026")
    ids_before = admin.snapshot_ids()
    first = {}
    try:
        first = _attempt(admin, literal, "146154", "literal_dates")
    finally:
        entry = _register(admin, disposable, literal[K_REF], literal[K_TITLE], ids_before)
    allure.attach(json.dumps(first, ensure_ascii=False, indent=1, default=str), name="literal dates attempt")
    expected = ("2026-08-20", "2026-09-18")
    if entry is None:
        assert not first.get("went_through"), "the literal-date save went through but no record is identifiable"
        if not re.search(r"past|future|today|earlier", first.get("messages", ""), re.I):
            pytest.fail(f"PRODUCT: a valid Closing Date (18/09/2026 > Opening 20/08/2026) was refused for a reason "
                        f"other than a past-date rule: {first.get('evidence')} | {first.get('messages')}")
        allure.attach("literal dates are now in the past and were refused by the past-date rule; retrying +1 year",
                      name="date substitution")
        shifted = _data("146154", openingDate="20/08/2027", closingDate="18/09/2027")
        expected = ("2027-08-20", "2027-09-18")
        entry = _create(admin, disposable, shifted, "146154")
    admin.open_entry_en(entry.code)
    stored = (admin.date_stored(K_OPENING), admin.date_stored(K_CLOSING))
    assert stored == expected, f"Opening/Closing stored as {stored!r}, expected {expected!r}"


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Closing Date")
@allure.title("An empty Closing Date is rejected")
@pytest.mark.functional_low
@pytest.mark.tc_146155
def test_empty_closing_date_rejected(page, disposable):
    # Azure TC 146155
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("146155", closingDate=None), "146155",
                    "an empty Closing Date", r"closingDate|Closing Date")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Closing Date")
@allure.title("A Closing Date equal to or earlier than the Opening Date is rejected")
@pytest.mark.functional_low
@pytest.mark.tc_146156
def test_closing_not_after_opening_rejected(page, disposable):
    # Azure TC 146156 | equal, then earlier (2027 dates so no past-date rule interferes)
    admin = _editor(page)
    # Both variants always run; failures are collected so the report covers each.
    relational = r"after|later|greater|before|earlier|opening"
    failures = []
    for label, closing in (("EQUAL", "20/08/2027"), ("EARLIER", "15/08/2027")):
        try:
            _assert_blocked(admin, disposable,
                            _data("146156", tenderReferenceNumber=_ref("146156", label),
                                  tenderTitle=_title("146156", f"Closing {label}"),
                                  openingDate="20/08/2027", closingDate=closing),
                            "146156", f"Closing Date {label.lower()} vs Opening Date (20/08/2027 / {closing})",
                            r"closingDate|Closing Date|openingDate|date",
                            expected_kind="a relational (Closing after Opening) error", kind_pattern=relational)
        except (AssertionError, pytest.fail.Exception) as exc:
            failures.append(f"[{label}] {exc}")
    assert not failures, "\n".join(failures)


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Closing Date")
@allure.title('A past Closing Date is rejected on creation ("past dates not allowed")')
@pytest.mark.functional_low
@pytest.mark.tc_146157
def test_past_closing_date_rejected(page, disposable):
    # Azure TC 146157 | Closing = yesterday, Opening a month earlier
    admin = _editor(page)
    yesterday = TODAY - timedelta(days=1)
    _assert_blocked(admin, disposable,
                    _data("146157", openingDate=_dmy(yesterday - timedelta(days=30)), closingDate=_dmy(yesterday)),
                    "146157", f"a past Closing Date ({_dmy(yesterday)})", r"closingDate|Closing Date|date",
                    expected_kind='"past dates not allowed"', kind_pattern=r"past dates not allowed")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Publication Date")
@allure.title("A valid Publication Date is accepted and drives the listing sort order")
@pytest.mark.functional_low
@pytest.mark.tc_146158
def test_publication_date_drives_sort_order(page, disposable, anon_pages):
    # Azure TC 146158 | Publication Date = today (newest) with an Opening Date OLDER than
    # every live tender: if the listing sorts by Publication Date (newest first) the card
    # comes before every tender published earlier; an opening-date sort would put it last.
    admin = _editor(page)
    entry = _create(admin, disposable, _data("146158", openingDate="01/07/2026", publicationDate=_dmy(TODAY)),
                    "146158")
    admin.open_entry_en(entry.code)
    assert admin.date_stored(K_PUBLICATION) == TODAY.isoformat(), (
        f"Publication Date stored as {admin.date_stored(K_PUBLICATION)!r}")
    view, _, index = _published_and_public(admin, entry, anon_pages)
    cards = view.cards()
    view.screenshot("146158 listing")
    detail = TenderPublicViewB(anon_pages())
    published = []
    for card in cards[: index + 3]:
        code = card["href"].split("tender=")[-1]
        line = detail.open_detail(code).detail_header()["published"]
        published.append((card["title"][:50], line))
    allure.attach("\n".join(f"{i}: {t} | {p}" for i, (t, p) in enumerate(published)), name="cards vs Published line")
    mine = datetime.strptime(TODAY.isoformat(), "%Y-%m-%d").date()
    out_of_order = []
    for i, (title, line) in enumerate(published[:index]):
        match = re.search(r"(\d{1,2} \w{3} \d{4})", line)
        if match and datetime.strptime(match.group(1), "%d %b %Y").date() < mine:
            out_of_order.append(f"#{i} {title!r} ({line})")
    assert not out_of_order, (
        f"the tender published {TODAY:%d %b %Y} is card #{index}, after tenders published EARLIER: {out_of_order} "
        f"— the listing is not ordered by Publication Date (newest first)")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Publication Date")
@allure.title("Publishing without a Publication Date is blocked")
@pytest.mark.functional_low
@pytest.mark.tc_146159
def test_publish_without_publication_date_blocked(page, disposable):
    # Azure TC 146159
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("146159", publicationDate=None), "146159",
                    "no Publication Date", r"publicationDate|Publication Date")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Tenders — Control Panel")
@allure.story("Closing Date")
@allure.title("A Closing Date exactly equal to the Opening Date is rejected on CMS manual create")
@pytest.mark.edge
@pytest.mark.tc_146295
def test_zero_day_validity_rejected_cms(page, disposable):
    # Azure TC 146295 (CMS half) | Opening = Closing (2027 so no past-date rule interferes)
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("146295", openingDate="20/08/2027", closingDate="20/08/2027"),
                    "146295", "Closing Date equal to Opening Date (zero-day validity)",
                    r"closingDate|Closing Date|openingDate|date",
                    expected_kind="a relational (Closing after Opening) error",
                    kind_pattern=r"after|later|greater|before|earlier|opening")


# ===========================================================================
# Manual cases
# ===========================================================================
@pytest.mark.edge
@pytest.mark.tc_146291
@allure.title("Two admins approving the same Pending submission concurrently (Manual)")
@MANUAL_SKIP
def test_concurrent_approve_manual():
    ...


@pytest.mark.edge
@pytest.mark.tc_146294
@allure.title("Tender Document/BOQ deleted from storage before admin review (Manual)")
@MANUAL_SKIP
def test_file_missing_before_review_manual():
    ...

"""
cms/tests/business_opportunities/test_bizopp_fields_c_control_panel.py —
Control_Panel field-validation cases for PBI 130697 (Business Opportunities),
Azure plan 137724 / suite 140361, on `manage-business-opportunity` (Agent C).

Cases: 143200 (Publish Date accepted), 143201 (Publish blocked, empty Publish
Date), 143203 (Save/Publish blocked, empty Archive Date), 143205 (valid numeric
Sort Order), 143206 (empty / non-numeric Sort Order blocked). 143241 is
Manual-tagged and not automated.

Pattern: PBI 130952 Tenders (fields). Site Content Editor (156488) in an
auth-free context; the Editor's submit button is "Publish". Save as Draft skips
required-field validation, so "Save" in a rejection case = the Editor's Publish.
Every rejection case fills an otherwise complete, valid form so the field under
test is the only invalid one. Records are QCTEST-130697-C-<tc>-<stamp> …,
captured by id + code and removed by the guarded delete.

Substitutions disclosed:
  - 143200: the title says "future" but description/steps say today: run with
    today's date (steps), as written.
  - 143205: Sort Order 5 -> 100 (100-grid rule, hard rule 3).
  - Images use an existing Documents & Media file (picked, nothing uploaded).
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta

import allure
import pytest

from cms.pages.business_opportunities.opportunity_fields_c_page import (
    C_EDITOR_USER_ID,
    C_QCTEST_PREFIX,
    C_AUTHOR_USER_ID,
    C_ROLE_AUTHOR,
    C_ROLE_EDITOR,
    K_ARCHIVE_DATE,
    K_PUBLISH_DATE,
    K_SORT,
    BizEntryC,
    BizOppFieldsCPage,
)
from cms.pages.business_opportunities.opportunity_sections_d_page import BizOppListingPublicD
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130697,
              pytest.mark.xdist_group("bizopp_fields_c")]

STAMP = datetime.now().strftime("%m%d%H%M%S")
TODAY = date.today()
ARCHIVE = TODAY + timedelta(days=60)
WORDING_LOG = os.path.join(BizOppFieldsCPage.EVIDENCE_DIR, "wording_findings.jsonl")


def _dmy(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _title(tc: str) -> str:
    return f"{C_QCTEST_PREFIX}{tc}-{STAMP} Opportunity"


def _data(tc: str, **over) -> dict:
    base = {"publishDate": _dmy(TODAY), "archiveDate": _dmy(ARCHIVE)}
    base.update(over)
    return BizOppFieldsCPage.default_data(_title(tc), **base)


class Registry:
    def __init__(self):
        self.entries: list[BizEntryC] = []

    def track(self, entry: BizEntryC) -> BizEntryC:
        if not entry.in_namespace():
            raise ValueError(f"{entry} is not a {C_QCTEST_PREFIX} record")
        self.entries.append(entry)
        return entry


@pytest.fixture
def disposable(browser):
    reg = Registry()
    yield reg
    if not reg.entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    out, failures = [], []
    try:
        cleaner = BizOppFieldsCPage(ctx.new_page())
        cleaner.login_as_role(C_ROLE_EDITOR)
        for e in reg.entries:
            label = f"{e.title!r} (id {e.entry_id}, code {e.code})"
            try:
                cleaner.open_list_all()
                if not cleaner.row_present(e):
                    (out if cleaner.is_list_fully_expanded() else failures).append(f"gone/unknown: {label}")
                    continue
                cleaner.owned_entry_ids.add(e.entry_id)
                (out if cleaner.delete_disposable_entry(e) else failures).append(f"{label}")
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(out + ["FAILED: " + f for f in failures]) or "none", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def anon_pages(browser):
    ctxs = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        ctxs.append(ctx)
        return ctx.new_page()

    yield _make
    for c in ctxs:
        try:
            c.close()
        except Exception:  # noqa: BLE001
            pass


AUTH_FREE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)


def _login(page, role: str = C_ROLE_EDITOR, user_id: str = C_EDITOR_USER_ID) -> BizOppFieldsCPage:
    admin = BizOppFieldsCPage(page)
    outcome = "unknown"
    for _ in range(3):
        outcome = admin.login_as_role(role)
        if outcome == "ok":
            break
        page.wait_for_timeout(5000)
    if outcome != "ok":
        pytest.skip(f"PRECONDITION: {role} login outcome {outcome!r}")
    admin.open_list_all()
    uid, _ = admin.signed_in_user()
    if uid != user_id:
        pytest.skip(f"PRECONDITION: {role} signs in as {uid!r}, not {user_id}")
    return admin


def _editor(page) -> BizOppFieldsCPage:
    return _login(page, C_ROLE_EDITOR, C_EDITOR_USER_ID)


def _wording(tc: str, field: str, expected: str, shown: str, png: str) -> None:
    f = {"tc": tc, "field": field, "expected": expected, "shown": shown, "screenshot": png}
    allure.attach(json.dumps(f, ensure_ascii=False, indent=1), name="LOW wording finding")
    os.makedirs(os.path.dirname(WORDING_LOG), exist_ok=True)
    with open(WORDING_LOG, "a", encoding="utf-8") as h:
        h.write(json.dumps(f, ensure_ascii=False) + "\n")


def _attempt(admin: BizOppFieldsCPage, data: dict, tc: str, what: str) -> dict:
    for attempt in (1, 2, 3):   # shared Editor account: other agents' sessions can interrupt the form
        try:
            admin.open_create_form_en()
            admin.fill_opportunity(data)
            break
        except Exception as exc:  # noqa: BLE001
            allure.attach(repr(exc), name=f"fill attempt {attempt} failed")
            if attempt == 3:
                raise
            if admin.signed_in_user()[0] != C_EDITOR_USER_ID:
                admin.login_as_role(C_ROLE_EDITOR)
    shot_before = admin.evidence(f"{tc}_{what}_filled")
    admin.click_publish()
    shot = admin.evidence(f"{tc}_{what}_after_publish")
    return {"went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
            "evidence": admin.refusal_evidence(), "messages": admin.all_messages_text(),
            "screenshot": shot, "filled_screenshot": shot_before}


def _register(admin, disposable, title: str, ids_before: set) -> BizEntryC | None:
    """Identify + track the record this attempt created. Never swallows: an identification failure
    is logged with the candidate rows (so the record can be found) and re-raised."""
    try:
        entry = admin.identify_created(title, ids_before)
    except Exception as exc:  # noqa: BLE001
        cands = getattr(admin, "last_candidates", [])
        allure.attach(f"{exc!r}\ncandidate rows (id:code:title): {cands}", name=f"IDENTIFICATION FAILED for {title!r}")
        raise
    return disposable.track(entry) if entry else None


def _assert_blocked(admin, disposable, data: dict, tc: str, what: str, field_pattern: str,
                    message_pattern: str, expected_kind: str) -> dict:
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, data, tc, what)
    finally:
        entry = _register(admin, disposable, data["opportunityTitle"], ids_before)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"refusal evidence ({what})")
    if entry is not None:
        pytest.fail(f"PRODUCT: Publish with {what} was NOT blocked - a record was created "
                    f"(id {entry.entry_id}); screenshot {result.get('screenshot')}")
    assert not result.get("went_through") and result.get("refused"), (
        f"Publish with {what} was neither refused with validation evidence nor saved: {result}")
    blob = json.dumps(result["evidence"], ensure_ascii=False)
    assert re.search(field_pattern, blob, re.I), (
        f"refused, but the validation evidence does not point at {what}: {result['evidence']}")
    if not re.search(message_pattern, result["messages"], re.I):
        _wording(tc, what, expected_kind, result["messages"], result["screenshot"])
    return result


DRAFT_FINDINGS: list[dict] = []   # what "Save as Draft" did with the empty field, per role


def _draft_probe(admin, disposable, data: dict, tc: str, what: str, role: str, check_key: str) -> dict:
    """Clicks Save as Draft on an otherwise complete form whose `check_key` field is empty and reports
    exactly what happened: was a draft record created, and what is stored in the empty field."""
    ids_before = admin.snapshot_ids()
    result: dict = {}
    entry = None
    try:
        for attempt in (1, 2, 3):
            try:
                admin.open_create_form_en()
                admin.fill_opportunity(data)
                break
            except Exception as exc:  # noqa: BLE001
                allure.attach(repr(exc), name=f"draft fill attempt {attempt} failed")
                if attempt == 3:
                    raise
        admin.evidence(f"{tc}_{role.split()[-1]}_draft_filled")
        admin.click_save_as_draft()
        shot = admin.evidence(f"{tc}_{role.split()[-1]}_draft_after_save")
        result = {"role": role, "went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
                  "messages": admin.all_messages_text(), "evidence": admin.refusal_evidence(), "screenshot": shot}
    finally:
        entry = _register(admin, disposable, data["opportunityTitle"], ids_before)
    result["role"] = role
    result["record_created"] = entry is not None
    if entry is not None:
        result["entry_id"], result["code"] = entry.entry_id, entry.code
        admin.open_entry_en(entry.code)
        result["stored_value_of_empty_field"] = admin.text_value(check_key)
        admin.open_list_all()
        result["row_status"] = admin.row_status(entry)
    DRAFT_FINDINGS.append({"tc": tc, "what": what, **result})
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"Save as Draft ({role}, {what})")
    return result


def _draft_problem(res: dict, what: str) -> str | None:
    if res["record_created"]:
        return (f"{res['role']}: Save as Draft with {what} SAVED a record (id {res['entry_id']}, status "
                f"{res.get('row_status')!r}, stored value of the empty field {res.get('stored_value_of_empty_field')!r}); "
                f"the case says it is 'not saved'. Screenshot {res['screenshot']}")
    return None


def _author_draft(anon_pages, disposable, data: dict, tc: str, what: str, check_key: str):
    """Same Save-as-Draft probe as the Site Content Author, in its own fresh context. Returns (result, note)."""
    author = BizOppFieldsCPage(anon_pages())
    outcome = author.login_as_role(C_ROLE_AUTHOR)
    if outcome != "ok":
        return None, f"Author login outcome {outcome!r}"
    uid, _ = author.signed_in_user()
    if uid != C_AUTHOR_USER_ID:
        return None, f"Author credentials sign in as {uid!r}, not {C_AUTHOR_USER_ID}"
    try:
        author.open_list_all()
        if not author.is_list_fully_expanded():
            return None, "Author cannot open / fully expand the entries list (needed for safe id capture)"
    except Exception as exc:  # noqa: BLE001
        return None, f"Author cannot open the entries list: {exc!r}"
    return _draft_probe(author, disposable, data, tc, what, C_ROLE_AUTHOR, check_key), ""


def _create(admin, disposable, data: dict, tc: str) -> BizEntryC:
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, data, tc, "create")
    finally:
        entry = _register(admin, disposable, data["opportunityTitle"], ids_before)
    allure.attach(repr(result), name="create result")
    assert result.get("went_through"), (
        f"Publish did not go through: {result.get('evidence')} | {result.get('messages')}")
    assert entry is not None, "publish went through but the new record is not identifiable as exactly one NEW row"
    return entry


# ===========================================================================
@pytest.mark.tc_143200
@pytest.mark.functional_low
@pytest.mark.regression
@AUTH_FREE
def test_tc_143200_publish_date_accepted(page, disposable):
    """Publish Date = today is accepted and persisted (as the Editor)."""
    admin = _editor(page)
    entry = _create(admin, disposable, _data("143200"), "143200")
    admin.open_entry_en(entry.code)
    stored = (admin.date_text(K_PUBLISH_DATE), admin.date_stored(K_PUBLISH_DATE))
    allure.attach(repr(stored), name="stored Publish Date")
    assert stored == (_dmy(TODAY), TODAY.isoformat()), f"Publish Date not persisted: {stored}"
    admin.evidence("143200_reopened")


@pytest.mark.tc_143201
@pytest.mark.functional_low
@pytest.mark.regression
@AUTH_FREE
def test_tc_143201_publish_blocked_empty_publish_date(page, disposable):
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("143201", publishDate=None), "143201",
                    "empty Publish Date", r"publishDate|Publish Date", r"Publish Date.*required|required",
                    "mandatory-field validation message")


@pytest.mark.tc_143203
@pytest.mark.functional_low
@pytest.mark.regression
@AUTH_FREE
def test_tc_143203_save_blocked_empty_archive_date(page, disposable, anon_pages):
    """Publish AND Save as Draft (Editor, then Author) with an empty Archive Date: all must be blocked."""
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("143203", archiveDate=None), "143203",
                    "empty Archive Date", r"archiveDate|Archive Date", r"Archive Date.*required|required",
                    "mandatory-field validation message")
    problems = []
    res = _draft_probe(admin, disposable,
                       _data("143203", archiveDate=None) | {"opportunityTitle": _title("143203") + " DRAFT-EDITOR"},
                       "143203", "empty Archive Date", C_ROLE_EDITOR, K_ARCHIVE_DATE)
    problems.append(_draft_problem(res, "an empty Archive Date"))
    author_data = _data("143203", archiveDate=None) | {"opportunityTitle": _title("143203") + " DRAFT-AUTHOR"}
    author_res, note = _author_draft(anon_pages, disposable, author_data, "143203", "empty Archive Date", K_ARCHIVE_DATE)
    if author_res is None:
        allure.attach(note, name="Author Save as Draft not exercisable")
    else:
        problems.append(_draft_problem(author_res, "an empty Archive Date"))
    problems = [p for p in problems if p]
    assert not problems, "PRODUCT: Publish is blocked, but " + " | ".join(problems)


@pytest.mark.tc_143205
@pytest.mark.functional_low
@pytest.mark.regression
@AUTH_FREE
def test_tc_143205_valid_sort_order_accepted(page, disposable, anon_pages):
    """Case literal 5 -> 100 (100-grid rule). Step 3 also says the card grid reflects the ordering relative
    to other opportunities: a second QCTEST record (Sort Order 200) is published with a NEWER Publish Date, so a
    Publish-Date-ordered listing and a Sort-Order-ordered listing give opposite answers."""
    admin = _editor(page)
    entry = _create(admin, disposable, _data("143205", displayOrder="100", publishDate=_dmy(TODAY - timedelta(days=2))),
                    "143205")
    admin.open_entry_en(entry.code)
    stored = admin.text_value(K_SORT)
    active = admin.active_status_stored()
    allure.attach(f"sort={stored!r} active={active!r}", name="stored values")
    assert stored == "100", f"Sort Order not persisted: {stored!r}"
    assert active == "true", f"Active Status stored {active!r}; public step not run"
    admin.open_list_all()
    assert admin.row_status(entry) == STATUS_PUBLISHED, "record is not Published"

    other_title = f"{C_QCTEST_PREFIX}143205-B-{STAMP} Opportunity"
    other = _create(admin, disposable, _data("143205", displayOrder="200", opportunityTitle=other_title,
                                             publishDate=_dmy(TODAY)), "143205B")
    admin.open_entry_en(other.code)
    assert (admin.text_value(K_SORT), admin.active_status_stored()) == ("200", "true"), "second record not stored as set"
    admin.open_list_all()
    assert admin.row_status(other) == STATUS_PUBLISHED, "second record is not Published"

    holder = {}

    def _both_listed() -> bool:
        view = BizOppListingPublicD(anon_pages())   # fresh unauthenticated context each poll
        view.open_expanded("en")
        holder["view"], holder["titles"] = view, view.card_titles()
        return entry.title in holder["titles"] and other_title in holder["titles"]

    try:
        wait_until(_both_listed, timeout=60.0, poll=2.0)
    except WaitTimeoutError:
        pass
    titles, view = holder["titles"], holder["view"]
    allure.attach("\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles)), name="public listing order")
    try:
        os.makedirs(BizOppFieldsCPage.EVIDENCE_DIR, exist_ok=True)
        png = view.page.screenshot(path=os.path.join(BizOppFieldsCPage.EVIDENCE_DIR, "143205_public_listing_anon.png"),
                                   full_page=False)
        allure.attach(png, name="public listing (anonymous)", attachment_type=allure.attachment_type.PNG)
    except Exception:  # noqa: BLE001
        pass
    assert entry.title in titles and other_title in titles, (
        f"PRODUCT: Published/Active QCTEST records missing from the public listing: "
        f"{[t for t in (entry.title, other_title) if t not in titles]}")
    pos_a, pos_b = titles.index(entry.title), titles.index(other_title)
    assert pos_a < pos_b, (
        f"PRODUCT: the card grid does not reflect Sort Order. Record A has Sort Order 100 (Publish Date "
        f"{_dmy(TODAY - timedelta(days=2))}), record B has Sort Order 200 (Publish Date {_dmy(TODAY)}); the listing "
        f"shows B (position {pos_b + 1}) before A (position {pos_a + 1}), i.e. it follows Publish Date newest-first, "
        f"not Sort Order. Default sort: {view.default_sort()!r}")


@pytest.mark.tc_143206
@pytest.mark.functional_low
@pytest.mark.regression
@AUTH_FREE
def test_tc_143206_sort_order_empty_or_non_numeric_blocked(page, disposable, anon_pages):
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("143206", displayOrder=None), "143206",
                    "empty Sort Order", r"displayOrder|Display Order|Sort Order", r"required",
                    "mandatory-field validation message")
    # 'abc' into a type=number control: Playwright fill() refuses non-numeric text, so type it key by key
    ids_before = admin.snapshot_ids()
    data = _data("143206", displayOrder=None)
    data["opportunityTitle"] = data["opportunityTitle"] + " abc"
    result = {}
    try:
        admin.open_create_form_en()
        admin.fill_opportunity(data)
        box = admin._en(K_SORT)
        box.click()
        admin.page.keyboard.type("abc", delay=30)
        validity = admin.sort_order_validity()
        allure.attach(json.dumps(validity), name="Sort Order after typing 'abc'")
        discarded = validity.get("value", "") == ""
        allure.attach(
            f"The type=number Sort Order control "
            f"{'DISCARDED the letters: its value is still empty' if discarded else 'kept ' + repr(validity.get('value'))}"
            f" -> the 'abc' step cannot really be entered; it degenerates to the empty case "
            f"(type={validity.get('type')!r}, min={validity.get('min')!r}, step={validity.get('step')!r}).",
            name="OBSERVATION: 'abc' cannot be entered")
        admin.click_publish()
        shot = admin.evidence("143206_abc_after_publish")
        result = {"went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
                  "evidence": admin.refusal_evidence(), "messages": admin.all_messages_text(), "validity": validity}
    finally:
        entry = _register(admin, disposable, data["opportunityTitle"], ids_before)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name="abc refusal evidence")
    if entry is not None:
        pytest.fail(f"PRODUCT: Sort Order 'abc' was NOT blocked - record created (id {entry.entry_id}); {shot}")
    assert result["refused"] and not result["went_through"], f"'abc' not refused: {result}"
    assert re.search(r"displayOrder", json.dumps(result["evidence"]), re.I), (
        f"refusal does not point at Sort Order: {result['evidence']}")
    if not re.search(r"numeric|number|valid|format", result["messages"], re.I):
        _wording("143206", "Sort Order 'abc'", "numeric-format validation error", result["messages"], shot)

    # User decision 2026-10-07: the number input discarding letters is fine -> 143206 Passed. The Save as Draft
    # behaviour with an empty Sort Order is recorded as an observation only (not asserted).
    res = _draft_probe(admin, disposable,
                       _data("143206", displayOrder=None) | {"opportunityTitle": _title("143206") + " DRAFT-EDITOR"},
                       "143206", "empty Sort Order", C_ROLE_EDITOR, K_SORT)
    author_data = _data("143206", displayOrder=None) | {"opportunityTitle": _title("143206") + " DRAFT-AUTHOR"}
    author_res, note = _author_draft(anon_pages, disposable, author_data, "143206", "empty Sort Order", K_SORT)
    if author_res is None:
        allure.attach(note, name="Author Save as Draft not exercisable")
    allure.attach(f"Editor draft saved a record: {res['record_created']}; Author: "
                  f"{author_res['record_created'] if author_res else note}", name="OBSERVATION Save as Draft")


@pytest.mark.tc_143241
@pytest.mark.skip(reason="Manual case - not automated (archive-boundary concurrency edge)")
def test_tc_143241_archive_boundary_concurrency_manual():
    pass

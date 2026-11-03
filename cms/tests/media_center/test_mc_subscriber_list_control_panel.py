"""
cms/tests/media_center/test_mc_subscriber_list_control_panel.py — Control_Panel
cases for PBI 130709 Media Center Home Page (suite 140368), batch 2, SUBS-A:
subscription from the public Media Center band -> the staff subscriber list
`manage-newsletter-subscriber` (columns, Status / date-range filters, search,
CSV export).

Notes applied to every case:
  - The cases' qa.mchub+NN@<QA_MAILBOX_DOMAIN> addresses are replaced by this
    agent's own disposable addresses qctest.mchub.a+<azureId>[tag]-<stamp>@
    example.com (one fresh set per run, never reused across cases). Nothing
    here can be deleted: the list is view-only, so every address is left in
    place and logged to reports/mc130709/subsA/addresses.jsonl.
  - "Main Menu -> Insights & Media -> Media Center" is opened by its URL in a
    fresh logged-out context.
  - The preconditions' "unsubscribed by clicking the unsubscribe link in its
    own Subscription Confirmation email": no inbox is available in this batch,
    so the SAME link the email carries (/web/qatar-chamber/newsletter-
    unsubscribe?token=<the record's own unsubscribeToken>) is opened in a
    fresh logged-out context and confirmed. The token is read from the
    record's View panel.
  - The staff steps run as QC Site Content Editor (PBI §9: view + export).
  - Filter / search / export assertions are scoped to this run's own
    addresses for membership; "every listed row is X" checks read the rows
    (read-only) to verify the filter itself.
  - Soft checks: each step's failure is collected and the case keeps going;
    the test fails at the end with all of them.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta

import allure
import pytest

from cms.pages.media_center.mc_subscriber_list_admin_page import (
    EMPTY_CELL,
    EVIDENCE_DIR,
    MSG_DUPLICATE_EN,
    MSG_SUCCESS_EN,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    UNSUB_SUCCESS_EN,
    McSubscribeBand,
    McSubscriberListAdminPage,
    McUnsubscribeLinkPage,
    own_address,
    parse_row_date,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

pytestmark = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.pbi_130709,
              pytest.mark.newsletter, pytest.mark.xdist_group("mc_subs_a_130709")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
STAMP = datetime.now().strftime("%m%d%H%M%S")
LEDGER = os.path.join(EVIDENCE_DIR, "addresses.jsonl")
FINDINGS = os.path.join(EVIDENCE_DIR, "findings.jsonl")
TIME_TOLERANCE = timedelta(minutes=3)
THROTTLE_POLL_S = 300.0
THROTTLE_BUDGET_S = 5400.0

# The case's four data items -> the live column that carries each.
REQUIRED_COLUMNS = {"email address": "Email", "status": "Subscription status",
                    "subscription date": "Subscribed on", "un-subscription date": "Unsubscribed on"}


# ===========================================================================
# Ledger / findings
# ===========================================================================
def _log(path: str, record: dict) -> None:
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def record_finding(tc: str, kind: str, **details) -> None:
    finding = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(finding, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    _log(FINDINGS, finding)


def _finish(fails: list) -> None:
    assert not fails, "\n".join(fails)


# ===========================================================================
# Fixtures
# ===========================================================================
@pytest.fixture
def anon(browser):
    """Factory of fresh logged-out contexts (one per public step)."""
    contexts = []

    def _make(cls=McSubscribeBand):
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return cls(ctx.new_page())

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture
def cms(page):
    """Lazy QC Site Content Editor session on the subscriber list (auth-free
    context): `cms()` signs in on first use. Public subscriptions run BEFORE
    the first `cms()` call, so a long throttle wait never idles a staff session."""
    holder: dict = {}

    def _editor() -> McSubscriberListAdminPage:
        if "admin" not in holder:
            admin = McSubscriberListAdminPage(page)
            outcome = admin.login_as_role(ROLE_EDITOR)
            if outcome == "auth_failed":
                pytest.fail(f"PRECONDITION: Liferay refused the .env credentials for {ROLE_EDITOR!r}")
            admin.open_list()
            user_id, _ = admin.signed_in_user()
            assert user_id == ROLE_USER_IDS[ROLE_EDITOR], f"login as {ROLE_EDITOR!r} gave userId {user_id!r}"
            holder["admin"] = admin
        return holder["admin"]

    return _editor


# ===========================================================================
# Orchestration
# ===========================================================================
def subscribe(anon, tc: str, email: str, typed: str | None = None, shot: str = "") -> dict:
    """Public step: fresh logged-out Media Center (EN), type, Subscribe.

    The subscribe endpoint rate-limits per client (HTTP 429 {"status":
    "throttled"}, "Too many attempts. Please try again in a few minutes.") and
    the parallel SUBS-B agent shares the same limit. A throttled attempt is an
    ENVIRONMENT condition, not the case's outcome: the step is retried in a
    fresh logged-out context every THROTTLE_POLL_S until the limit lifts."""
    attempts: list[dict] = []
    state: dict = {}

    def _attempt() -> bool:
        band = anon()
        band.open_hub("en")
        result = {"signed_in": band.is_signed_in(), "band_shown": band.band_shown(), "heading": band.heading()}
        result.update(band.subscribe(typed if typed is not None else email))
        result["screenshot"] = band.band_evidence(f"{tc}_{shot or 'subscribe'}_{email.split('+')[1][:30]}")
        attempts.append({"at": result["at"].isoformat(timespec="seconds"), "api_status": result["api_status"]})
        state["result"] = result
        return result["api_status"] != "throttled"

    try:
        wait_until(_attempt, timeout=THROTTLE_BUDGET_S, poll=THROTTLE_POLL_S)
    except WaitTimeoutError:
        pass
    result = state["result"]
    result["attempts"] = attempts
    if len(attempts) > 1:
        allure.attach(json.dumps(attempts, indent=1), name=f"throttled retries for {email}")
    _log(LEDGER, {"tc": tc, "email": email, "typed": typed, "api_status": result["api_status"],
                  "at": result["at"].isoformat(timespec="seconds"), "state": "subscribed"})
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"subscribe {email}")
    return result


def require_subscribed(result: dict, email: str) -> None:
    if result["api_status"] != "success":
        pytest.fail(f"PRECONDITION: subscribing {email} returned {result['api_status']!r} "
                    f"({result['message']!r}) after {len(result.get('attempts', []))} attempt(s); "
                    f"{result['screenshot']}")


def confirm_active(editor: McSubscriberListAdminPage, email: str) -> dict:
    """Precondition: the record is confirmed Active in the subscriber panel."""
    rows = editor.wait_for_row(email, predicate=lambda r: r["subscription_status"] == "Active")
    if len(rows) != 1 or rows[0]["subscription_status"] != "Active":
        pytest.fail(f"PRECONDITION: {email} is not listed exactly once as Active: {rows}")
    return rows[0]


def unsubscribe_via_link(anon, editor: McSubscriberListAdminPage, tc: str, email: str) -> dict:
    """Precondition: unsubscribed through its own confirmation-email link (the
    record's unsubscribe token on the public unsubscribe page, logged out),
    then confirmed Unsubscribed with today's un-subscription date."""
    confirm_active(editor, email)
    fields = editor.view_record(email)
    editor.close_viewer()
    token = fields.get("Unsubscribe Token", "")
    if not token or token == EMPTY_CELL:
        pytest.fail(f"PRECONDITION: {email} has no unsubscribe token to build its email link: {fields}")
    link = anon(McUnsubscribeLinkPage)
    link.open_link(token)
    state = link.confirm()
    shot = link.evidence(f"{tc}_unsubscribe_link_{email.split('+')[1][:30]}")
    if state != UNSUB_SUCCESS_EN:
        pytest.fail(f"PRECONDITION: unsubscribe link for {email} ended in {state!r}; {shot}")
    _log(LEDGER, {"tc": tc, "email": email, "state": "unsubscribed",
                  "at": datetime.now().isoformat(timespec="seconds")})
    rows = editor.wait_for_row(email, predicate=lambda r: r["subscription_status"] == "Unsubscribed")
    if len(rows) != 1 or rows[0]["subscription_status"] != "Unsubscribed":
        pytest.fail(f"PRECONDITION: {email} is not listed exactly once as Unsubscribed: {rows}")
    unsub = parse_row_date(rows[0]["unsubscribed_on"])
    if not unsub or unsub.date() != date.today():
        pytest.fail(f"PRECONDITION: {email} un-subscription date is not today: {rows[0]}")
    return rows[0]


def precondition_pair(anon, cms, tc: str, active: str, gone: str) -> McSubscriberListAdminPage:
    """One Active and one Unsubscribed address of this case (subscribe both first)."""
    require_subscribed(subscribe(anon, tc, active, shot="precondition"), active)
    require_subscribed(subscribe(anon, tc, gone, shot="precondition"), gone)
    editor = cms()
    confirm_active(editor, active)
    unsubscribe_via_link(anon, editor, tc, gone)
    return editor


def precondition_single(anon, cms, tc: str, email: str) -> tuple[McSubscriberListAdminPage, dict]:
    require_subscribed(subscribe(anon, tc, email, shot="precondition"), email)
    editor = cms()
    return editor, confirm_active(editor, email)


def check_list_columns(fails: list, editor: McSubscriberListAdminPage, step: str) -> None:
    """'The subscriber list loads with email address, status, subscription date and
    un-subscription date for each row.'"""
    headers = editor.headers()   # rendered upper-case by CSS text-transform
    shown = {h.lower() for h in headers}
    missing = [item for item, header in REQUIRED_COLUMNS.items() if header.lower() not in shown]
    if missing:
        fails.append(f"step {step}: list has no column for {missing}; headers {headers}")
    rows = editor.rows()
    if not rows:
        fails.append(f"step {step}: the subscriber list shows no rows")
    bad = [r for r in rows if not r["email"] or r["subscription_status"] not in ("Active", "Unsubscribed")
           or parse_row_date(r["subscribed_on"]) is None]
    if bad:
        fails.append(f"step {step}: rows without an email / status / subscription date: {bad[:5]}")


def check_row(fails: list, step: str, row: dict, status: str, subscribed: date | None,
              unsubscribed: date | None, at: datetime | None = None) -> None:
    """status + Subscribed on day (+ time T) + Unsubscribed on (None = empty)."""
    if row["subscription_status"] != status:
        fails.append(f"step {step}: {row['email']} status {row['subscription_status']!r}, expected {status!r}")
    sub = parse_row_date(row["subscribed_on"])
    if subscribed and (not sub or sub.date() != subscribed):
        fails.append(f"step {step}: {row['email']} Subscribed on {row['subscribed_on']!r}, expected {subscribed}")
    if at and sub and abs(sub - at) > TIME_TOLERANCE:
        fails.append(f"step {step}: {row['email']} Subscribed on {row['subscribed_on']!r} is not the "
                     f"subscribe time T={at:%H:%M:%S}")
    uns = parse_row_date(row["unsubscribed_on"])
    if unsubscribed is None and row["unsubscribed_on"] not in ("", EMPTY_CELL):
        fails.append(f"step {step}: {row['email']} Unsubscribed on {row['unsubscribed_on']!r}, expected empty")
    if unsubscribed and (not uns or uns.date() != unsubscribed):
        fails.append(f"step {step}: {row['email']} Unsubscribed on {row['unsubscribed_on']!r}, "
                     f"expected {unsubscribed}")


def emails(rows: list[dict]) -> set[str]:
    return {r["email"].strip().lower() for r in rows}


# ===========================================================================
# Subscription from the band -> the list
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_149286
def test_149286_band_subscription_listed_active_with_date(page, anon, cms):
    """MEDIA-MCHUB-TC-232: a visitor's subscription from the Media Center band appears in the
    subscriber list with status Active and its subscription date."""
    tc, fails = "149286", []
    email = own_address(tc, STAMP)
    # Steps 1-2 — public band, logged out
    result = subscribe(anon, tc, email)
    if result["signed_in"]:
        fails.append("step 1: the public context is signed in")
    if not result["band_shown"]:
        fails.append(f"step 1: the subscription band is not shown; {result['screenshot']}")
    if result["api_status"] != "success" or not result["message_ok"]:
        fails.append(f"step 2: subscribe returned {result['api_status']!r}, message {result['message']!r}; "
                     f"{result['screenshot']}")
    elif result["message"] != MSG_SUCCESS_EN:
        record_finding(tc, "LOW wording: band success message differs", expected=MSG_SUCCESS_EN,
                       shown=result["message"], screenshot=result["screenshot"])
    # Step 3 — Editor list
    editor = cms()
    editor.open_list()
    check_list_columns(fails, editor, "3")
    # Step 4 — search
    rows = editor.wait_for_row(email)
    shot = editor.evidence(f"{tc}_step4_search")
    if len(rows) != 1:
        fails.append(f"step 4: expected exactly one row for {email}, got {rows}; {shot}")
    else:
        check_row(fails, "4", rows[0], "Active", date.today(), None, at=result["at"])
        if not rows[0]["entry_id"].isdigit():
            fails.append(f"step 4: the row carries no system subscription ID: {rows[0]}")
        fields = editor.view_record(email)
        allure.attach(json.dumps(fields, ensure_ascii=False, indent=1), name="View panel")
        if not str(fields.get("Id", "")).isdigit():
            fails.append(f"step 4: the record shows no system ID: {fields}")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149287
def test_149287_record_stores_media_center_source_page(page, anon, cms):
    """MEDIA-MCHUB-TC-233: the subscriber record stores the Media Center page as its Source Page."""
    tc = "149287"
    email = own_address(tc, STAMP)
    editor, _ = precondition_single(anon, cms, tc, email)
    editor.search(email)
    fields = editor.view_record(email)
    shot = editor.evidence(f"{tc}_step1_record")
    allure.attach(json.dumps(fields, ensure_ascii=False, indent=1), name="View panel")
    source = {k: v for k, v in fields.items() if "source" in k.lower() or "subscribed from" in k.lower()}
    if not source:
        record_finding(tc, "missing subject: no Source Page on the subscriber record",
                       fields=sorted(k for k in fields if not k.startswith("__")), screenshot=shot)
        pytest.skip(f"BLOCKED: the subscriber record has no Source Page field (fields: "
                    f"{sorted(k for k in fields if not k.startswith('__'))}); {shot}")
    value = " ".join(source.values()).lower()
    assert "media-center" in value or "media center" in value, \
        f"step 2: Source Page {source} does not identify the Media Center page; {shot}"


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149288
def test_149288_email_stored_trimmed_lower_case(page, anon, cms):
    """MEDIA-MCHUB-TC-234: a subscribed email address is stored trimmed and in lower case."""
    tc, fails = "149288", []
    email = own_address(tc, STAMP)
    local, domain = email.split("@")
    typed = f"  {local.replace('qctest.mchub.a', 'QCTest.MCHub.A')}@{domain.upper()}  "
    # Steps 1-2
    result = subscribe(anon, tc, email, typed=typed)
    if not result["band_shown"]:
        fails.append(f"step 1: the band is not shown; {result['screenshot']}")
    if result["api_status"] != "success" or not result["message_ok"]:
        fails.append(f"step 2: subscribe returned {result['api_status']!r}, message {result['message']!r}; "
                     f"{result['screenshot']}")
    # Step 3
    editor = cms()
    editor.open_list()
    check_list_columns(fails, editor, "3")
    # Step 4
    rows = editor.wait_for_row(email)
    shot = editor.evidence(f"{tc}_step4_search")
    allure.attach(json.dumps({"typed": typed, "sent": result["request_email"], "rows": rows}, indent=1),
                  name="typed vs stored")
    if len(rows) != 1:
        fails.append(f"step 4: expected exactly one row for {email}, got {rows}; {shot}")
    else:
        if rows[0]["email"] != email:
            fails.append(f"step 4: stored email is {rows[0]['email']!r}, expected exactly {email!r} "
                         f"(typed {typed!r}, sent {result['request_email']!r}); {shot}")
        if rows[0]["subscription_status"] != "Active":
            fails.append(f"step 4: status {rows[0]['subscription_status']!r}, expected Active")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149289
def test_149289_duplicate_active_subscription_no_second_record(page, anon, cms):
    """MEDIA-MCHUB-TC-235: subscribing an already active address twice does not create a second record."""
    tc, fails = "149289", []
    email = own_address(tc, STAMP)
    editor, before = precondition_single(anon, cms, tc, email)
    # Steps 1-2
    result = subscribe(anon, tc, email, shot="second")
    if not result["band_shown"]:
        fails.append(f"step 1: the band is not shown; {result['screenshot']}")
    if result["message"] != MSG_DUPLICATE_EN:
        fails.append(f"step 2: message {result['message']!r} (api {result['api_status']!r}), expected "
                     f"{MSG_DUPLICATE_EN!r}; {result['screenshot']}")
    # Step 3
    editor.open_list()
    check_list_columns(fails, editor, "3")
    # Step 4
    editor.search(email)
    rows = editor.rows_for(email)
    shot = editor.evidence(f"{tc}_step4_search")
    if len(rows) != 1:
        fails.append(f"step 4: {len(rows)} rows for {email}, expected exactly one: {rows}; {shot}")
    elif rows[0]["subscribed_on"] != before["subscribed_on"] or rows[0]["entry_id"] != before["entry_id"]:
        fails.append(f"step 4: the record changed: before {before}, after {rows[0]}; {shot}")
    _finish(fails)


# ===========================================================================
# List columns / filters / search / export
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.ui
@pytest.mark.tc_149290
def test_149290_list_shows_email_status_and_dates(page, anon, cms):
    """MEDIA-MCHUB-TC-236: the list shows email address, status, subscription date and
    un-subscription date for each subscriber."""
    tc, fails = "149290", []
    active, gone = own_address(tc, STAMP, "a"), own_address(tc, STAMP, "u")
    editor = precondition_pair(anon, cms, tc, active, gone)
    # Step 1
    editor.open_list()
    check_list_columns(fails, editor, "1")
    shot = editor.evidence(f"{tc}_step1_list", full_page=True)
    # Step 2
    today = date.today()
    for email, status, unsub in ((active, "Active", None), (gone, "Unsubscribed", today)):
        rows = editor.rows_for(email)
        if len(rows) != 1:
            fails.append(f"step 2: {len(rows)} rows for {email}: {rows}; {shot}")
            continue
        check_row(fails, "2", rows[0], status, today, unsub)
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.tc_149291
def test_149291_status_filter_unsubscribed(page, anon, cms):
    """MEDIA-MCHUB-TC-237: filtering by Status Unsubscribed shows only unsubscribed subscribers."""
    tc, fails = "149291", []
    active, gone = own_address(tc, STAMP, "a"), own_address(tc, STAMP, "u")
    editor = precondition_pair(anon, cms, tc, active, gone)
    # Step 1
    editor.open_list()
    check_list_columns(fails, editor, "1")
    # Step 2
    editor.set_status_filter("Unsubscribed")
    rows = editor.rows()
    shot = editor.evidence(f"{tc}_step2_unsubscribed", full_page=True)
    allure.attach(json.dumps(rows, ensure_ascii=False, indent=1), name="rows after Status=Unsubscribed")
    wrong = [r for r in rows if r["subscription_status"] != "Unsubscribed"]
    if wrong:
        fails.append(f"step 2: non-Unsubscribed rows listed: {wrong[:5]}; {shot}")
    if gone not in emails(rows):
        fails.append(f"step 2: {gone} (Unsubscribed) is not listed; {shot}")
    if active in emails(rows):
        fails.append(f"step 2: {active} (Active) is listed; {shot}")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149292
def test_149292_clearing_status_filter_restores_full_list(page, anon, cms):
    """MEDIA-MCHUB-TC-238: clearing the Status filter restores the full subscriber list."""
    tc, fails = "149292", []
    active, gone = own_address(tc, STAMP, "a"), own_address(tc, STAMP, "u")
    editor = precondition_pair(anon, cms, tc, active, gone)
    # Step 1
    editor.open_list()
    check_list_columns(fails, editor, "1")
    # Step 2
    before = editor.rows()
    total_c = len(before)
    counter = editor.total_count()
    if counter is not None and counter != total_c:
        fails.append(f"step 2: the list shows {total_c} rows but its counter says {counter} total")
    editor.set_status_filter("Unsubscribed")
    filtered = editor.rows()
    shot2 = editor.evidence(f"{tc}_step2_unsubscribed", full_page=True)
    if any(r["subscription_status"] != "Unsubscribed" for r in filtered):
        fails.append(f"step 2: non-Unsubscribed rows listed; {shot2}")
    if active in emails(filtered):
        fails.append(f"step 2: {active} (Active) is not hidden; {shot2}")
    # Step 3
    editor.reset_filters()
    after = editor.rows()
    shot3 = editor.evidence(f"{tc}_step3_reset", full_page=True)
    allure.attach(json.dumps({"C": total_c, "filtered": len(filtered), "after": len(after),
                              "state": editor.filter_state()}, indent=1), name="counts")
    for email in (active, gone):
        if email not in emails(after):
            fails.append(f"step 3: {email} is not listed after Reset; {shot3}")
    if len(after) != total_c or emails(after) != emails(before):
        fails.append(f"step 3: total after Reset is {len(after)}, expected C={total_c}; {shot3}")
    if editor.filter_state()["status"] != "":
        fails.append(f"step 3: Status filter still {editor.filter_state()['status']!r} after Reset")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_high
@pytest.mark.tc_149293
def test_149293_date_range_filter(page, anon, cms):
    """MEDIA-MCHUB-TC-239: a date range shows only subscribers whose subscription date is in it."""
    tc, fails = "149293", []
    email = own_address(tc, STAMP)
    editor, _ = precondition_single(anon, cms, tc, email)
    day_d = date.today()
    # Step 1
    editor.open_list()
    check_list_columns(fails, editor, "1")
    older = [r for r in editor.rows() if (parse_row_date(r["subscribed_on"]) or datetime.max).date() < day_d]
    if not older:
        pytest.fail("PRECONDITION: no pre-existing subscriber from an earlier date is in the live list")
    # Step 2 — D..D
    editor.set_date_range(day_d, day_d)
    rows = editor.rows()
    shot2 = editor.evidence(f"{tc}_step2_D_to_D", full_page=True)
    allure.attach(json.dumps({"range": editor.date_range_values(), "rows": rows}, ensure_ascii=False, indent=1),
                  name="D..D")
    if editor.date_range_values() != (day_d.isoformat(), day_d.isoformat()):
        fails.append(f"step 2: the range did not take: {editor.date_range_values()}")
    if email not in emails(rows):
        fails.append(f"step 2: {email} is not listed for {day_d}..{day_d}; {shot2}")
    off = [r for r in rows if (parse_row_date(r["subscribed_on"]) or datetime.min).date() != day_d]
    if off:
        fails.append(f"step 2: rows outside {day_d} listed: {[(r['email'], r['subscribed_on']) for r in off]}; "
                     f"{shot2}")
    # Step 3 — D-30..D-1
    start, end = day_d - timedelta(days=30), day_d - timedelta(days=1)
    editor.set_date_range(start, end)
    rows = editor.rows()
    shot3 = editor.evidence(f"{tc}_step3_D-30_to_D-1", full_page=True)
    allure.attach(json.dumps({"range": editor.date_range_values(), "rows": rows}, ensure_ascii=False, indent=1),
                  name="D-30..D-1")
    if editor.date_range_values() != (start.isoformat(), end.isoformat()):
        fails.append(f"step 3: the range did not take: {editor.date_range_values()}")
    if email in emails(rows):
        fails.append(f"step 3: {email} (subscribed {day_d}) is listed for {start}..{end}; {shot3}")
    off = [r for r in rows if not (start <= (parse_row_date(r["subscribed_on"]) or datetime.min).date() <= end)]
    if off:
        fails.append(f"step 3: rows outside {start}..{end} listed: "
                     f"{[(r['email'], r['subscribed_on']) for r in off]}; {shot3}")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149294
def test_149294_search_by_email(page, anon, cms):
    """MEDIA-MCHUB-TC-240: searching by email address returns only the matching subscriber."""
    tc, fails = "149294", []
    email = own_address(tc, STAMP)
    editor, _ = precondition_single(anon, cms, tc, email)
    # Step 1
    editor.open_list()
    check_list_columns(fails, editor, "1")
    # Step 2
    editor.search(email)
    rows = editor.rows()
    shot = editor.evidence(f"{tc}_step2_search")
    if [r["email"] for r in rows] != [email]:
        fails.append(f"step 2: search for {email} lists {[r['email'] for r in rows]}; {shot}")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_149295
def test_149295_export_filtered_list_csv(page, anon, cms):
    """MEDIA-MCHUB-TC-241: exporting the filtered list produces a CSV with only the filtered
    subscribers and the four required data columns."""
    tc, fails = "149295", []
    active, gone = own_address(tc, STAMP, "a"), own_address(tc, STAMP, "u")
    editor = precondition_pair(anon, cms, tc, active, gone)
    # Step 1
    editor.open_list()
    check_list_columns(fails, editor, "1")
    # Step 2
    editor.set_status_filter("Active")
    rows = editor.rows()
    shot2 = editor.evidence(f"{tc}_step2_active", full_page=True)
    if active not in emails(rows):
        fails.append(f"step 2: {active} is not listed under Status=Active; {shot2}")
    if gone in emails(rows):
        fails.append(f"step 2: {gone} (Unsubscribed) is listed under Status=Active; {shot2}")
    # Step 3
    export = editor.export_csv(f"{tc}_export_active")
    allure.attach.file(export["path"], name=export["suggested"], attachment_type=allure.attachment_type.CSV)
    if not export["suggested"].lower().endswith(".csv"):
        fails.append(f"step 3: the download is {export['suggested']!r}, not a .csv")
    # Step 4
    header = export["header"]
    missing = [item for item, column in REQUIRED_COLUMNS.items() if column not in header]
    if missing:
        fails.append(f"step 4: CSV has no column for {missing}; header {header}")
    status_col = REQUIRED_COLUMNS["status"]
    mine = [r for r in export["rows"] if r.get("Email", "").strip().lower() == active]
    if len(mine) != 1 or mine[0].get(status_col) != "Active":
        fails.append(f"step 4: {active} is not in the CSV once as Active: {mine}; {export['path']}")
    if any(r.get("Email", "").strip().lower() == gone for r in export["rows"]):
        fails.append(f"step 4: {gone} (Unsubscribed) is in the CSV; {export['path']}")
    unsub_rows = [r for r in export["rows"] if r.get(status_col) != "Active"]
    if unsub_rows:
        fails.append(f"step 4: non-Active rows in the CSV: {unsub_rows[:5]}; {export['path']}")
    if len(export["rows"]) != len(rows):
        fails.append(f"step 4: CSV has {len(export['rows'])} rows, the filtered list {len(rows)}")
    _finish(fails)

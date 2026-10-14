"""
cms/tests/media_center/test_mc_subscriber_admin_control_panel.py — PBI 130709
Media Center Home Page, Control_Panel batch 2 (suite 140368, SUBS-B):
manual unsubscribe by the Administrator, its History trail, reactivation of a
previously unsubscribed address, role access to `manage-newsletter-subscriber`
(PBI §9 governs), and 149285 (a news edit reflected in the hub news feed).

DATA RULES
  - Every subscriber is OUR OWN `qctest.mchub.b+<tc>-<stamp>@example.com`,
    created from the logged-out Media Center band (no inbox checks in this
    batch). Real subscribers are never edited, unsubscribed or deleted.
    Teardown deletes ONLY those exact addresses (TEST_USER, guarded delete).
  - "Administrator" = TEST_USER (user decision 2026-10-07); every other role
    signs in with its own named account and the session id is re-checked.
  - 149299's precondition ("unsubscribed through the link in its own
    confirmation email") is reached with the Administrator's manual
    Unsubscribe instead — there is no inbox in this batch; the record state
    the case needs (Unsubscribed, today's date) is the same.
  - 149285: the hub feed (fragment qc-mc-nf) reads /o/qc-media-center-api/news,
    whose items are entries of the **News** object (manage-qcdemo131059-news,
    QCDEMO-131059-NEWS-*). The case's URL `manage-news-article` is the Home
    "Latest News" object, which the hub never reads, so the disposable
    QCTEST-130709 article is authored in the feed's real source module (the
    "news module" the batch rules name); the discrepancy is recorded.

Public reads: fresh logged-out contexts only.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime

import allure
import pytest

from cms.pages.media_center.mc_subscriber_admin_b_page import (
    CASE_NEWS_PATH,
    EVIDENCE_DIR,
    MSG_ACCESS_DENIED,
    MSG_SAVED_AND_PUBLISHED,
    MSG_SUBSCRIBED,
    NEWS_SLUG,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_FORM_MANAGER,
    ROLE_MEMBER,
    ROLE_USER_IDS,
    McHubPublicView,
    McNewsAdminPage,
    McSubscriberAdminPage,
    NewsEntry,
    parse_list_date,
    subscriber_email,
)
from core.web.browser import new_context

STAMP = datetime.now().strftime("%m%d%H%M")
FINDINGS = os.path.join(EVIDENCE_DIR, "findings.jsonl")
DOWNLOADS = os.path.join(EVIDENCE_DIR, "downloads")
TIME_TOLERANCE_S = 180
EXPECTED_COLUMNS = ("Email", "Subscription status", "Subscribed on", "Unsubscribed on")

COMMON = [pytest.mark.pbi_130709, pytest.mark.control_panel, pytest.mark.media, pytest.mark.newsletter,
          pytest.mark.xdist_group("mc_subsB_130709")]


def marks(*extra):
    def _wrap(fn):
        for m in COMMON + list(extra):
            fn = m(fn)
        return fn
    return _wrap


# ===========================================================================
# Findings / evidence
# ===========================================================================
def record(tc: str, kind: str, **details) -> None:
    item = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(item, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(FINDINGS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")


def needs_decision(tc: str, question: str, **details) -> None:
    record(tc, "NEEDS-DECISION", question=question, **details)
    pytest.skip(f"NEEDS-DECISION: {question}")


def finish(tc: str, fails: list[str]) -> None:
    if fails:
        record(tc, "FAILED", fails=fails)
        pytest.fail("\n".join(fails))
    record(tc, "PASSED")


def near(stamp_text: str, moment: datetime) -> bool:
    parsed = parse_list_date(stamp_text)
    return parsed is not None and abs((parsed - moment).total_seconds()) <= TIME_TOLERANCE_S


def headers_ok(headers: list[str]) -> list[str]:
    return [c for c in EXPECTED_COLUMNS if not any(h.casefold() == c.casefold() for h in headers)]


# ===========================================================================
# Sessions + subscriber registry (teardown deletes our own addresses only)
# ===========================================================================
class Subs:
    def __init__(self, browser):
        self.browser = browser
        self.contexts = []
        self.emails: list[str] = []
        self._admin: McSubscriberAdminPage | None = None

    def _ctx(self):
        ctx = new_context(self.browser, use_auth_state=False)
        self.contexts.append(ctx)
        return ctx

    def visitor(self) -> McHubPublicView:
        view = McHubPublicView(self._ctx().new_page())
        view.open_hub()
        if view.signed_in():
            pytest.fail("PRECONDITION: the public context is signed in")
        return view

    def admin(self) -> McSubscriberAdminPage:
        if self._admin is None:
            self._admin = McSubscriberAdminPage(self._ctx().new_page())
            self._admin.login_admin()
        return self._admin

    def role(self, role: str) -> McSubscriberAdminPage:
        drv = McSubscriberAdminPage(self._ctx().new_page())
        outcome = drv.login_as_role(role)
        if outcome == "auth_failed":
            pytest.fail(f"PRECONDITION: Liferay refused the .env credentials for {role!r}")
        return drv

    def require_role(self, drv: McSubscriberAdminPage, role: str) -> None:
        user_id, name = drv.signed_in_user()
        if user_id != ROLE_USER_IDS[role]:
            pytest.fail(f"PRECONDITION: session is userId {user_id!r} ({name}), not {role!r} "
                        f"({ROLE_USER_IDS[role]}) — role outcome not asserted")

    def subscribe(self, tc: str, label: str = "") -> tuple[str, dict, datetime]:
        """Precondition: subscribe a fresh address from the logged-out band."""
        email = subscriber_email(tc + (f"-{label}" if label else ""), STAMP)
        view = self.visitor()
        started = datetime.now()
        result = view.subscribe(email)
        if result.get("ok"):
            self.emails.append(email)
        shot = view.evidence(f"{tc}_band_subscribe_{label or 'pre'}")
        record(tc, "subscribe (info)", email=email, result=result, screenshot=shot)
        if not result.get("ok"):
            pytest.fail(f"PRECONDITION: band subscription of {email} failed "
                        f"(throttled={result.get('throttled')}): {result}")
        return email, result, started

    def confirm_active(self, tc: str, email: str) -> dict:
        admin = self.admin()
        row = admin.wait_row(email, lambda r: r["subscription_status"] == "Active", timeout=90.0)
        if row.get("subscription_status") != "Active":
            shot = admin.evidence(f"{tc}_precondition_not_active")
            pytest.fail(f"PRECONDITION: {email} is not listed Active in the subscriber panel: {row}; {shot}")
        return row

    def close(self):
        for ctx in self.contexts:
            try:
                ctx.close()
            except Exception:  # noqa: BLE001
                pass


def _teardown_subscribers(browser, emails: list[str]) -> list[str]:
    if not emails:
        return []
    ctx = new_context(browser, use_auth_state=False)
    done, failures = [], []
    try:
        admin = McSubscriberAdminPage(ctx.new_page())
        admin.login_admin()
        for email in emails:
            (done if admin.delete_own(email) else failures).append(email)
    finally:
        ctx.close()
    lines = [f"deleted {e}" for e in done] + [f"NOT deleted {e}" for e in failures]
    allure.attach("\n".join(lines) or "nothing", name="subscriber teardown")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(os.path.join(EVIDENCE_DIR, "teardown.log"), "a", encoding="utf-8") as fh:
        fh.write(f"[{datetime.now().isoformat(timespec='seconds')}]\n  " + "\n  ".join(lines) + "\n")
    return failures


@pytest.fixture
def subs(browser):
    sessions = Subs(browser)
    yield sessions
    sessions.close()
    failures = _teardown_subscribers(browser, sessions.emails)
    if failures:
        record("teardown", "LEFTOVER", emails=failures)


# ===========================================================================
# 149296 — Administrator manual unsubscribe
# ===========================================================================
@marks(pytest.mark.functional_high, pytest.mark.regression, pytest.mark.uat, pytest.mark.tc_149296)
def test_149296_admin_manually_unsubscribes(subs):
    """MEDIA-MCHUB-TC-242: the Administrator (TEST_USER) sets a subscriber to
    Unsubscribed; the record shows Unsubscribed with the un-subscription date."""
    tc, fails = "149296", []
    email, _, _ = subs.subscribe(tc)
    subs.confirm_active(tc, email)
    admin = subs.admin()

    with allure.step("1. Open the subscriber panel as Administrator"):
        admin.open_list()
        missing = headers_ok(admin.column_headers())
        admin.search(email)
        row = admin.rows_for(email)
        shot1 = admin.evidence(f"{tc}_step1_list")
        if missing:
            fails.append(f"step 1: list lacks columns {missing}: {admin.column_headers()}; {shot1}")
        if len(row) != 1 or not row[0]["visible"]:
            fails.append(f"step 1: {email} not listed once: {row}; {shot1}")

    with allure.step("2. The manual unsubscribe action is available"):
        if not row or not ({"reject", "unsubscribe"} & set(row[0]["actions"])):
            pytest.fail(f"step 2: no Unsubscribe action on {email}: {row}; {shot1}")

    with allure.step("3. Unsubscribe and save — the success toast is shown"):
        result = admin.unsubscribe(email)
        shot3 = admin.evidence(f"{tc}_step3_after_unsubscribe")
        record(tc, "unsubscribe (info)", result=result, screenshot=shot3)
        toast = [s for s in result["seen"] if re.search(r"success|unsubscribed|saved|updated", s, re.I)]
        if not toast:
            fails.append(f"step 3: no success toast after the manual unsubscribe "
                         f"(dialogs {result['dialogs']}, nodes seen {result['seen']}); {shot3}")

    with allure.step("4. Filter Status = Unsubscribed"):
        admin.open_list()
        admin.filter_status("Unsubscribed")
        admin.search(email)
        row4 = admin.rows_for(email)
        shot4 = admin.evidence(f"{tc}_step4_filter_unsubscribed")
        if len(row4) != 1 or not row4[0]["visible"]:
            fails.append(f"step 4: {email} not listed under Status=Unsubscribed: {row4}; {shot4}")
        else:
            r = row4[0]
            if r["subscription_status"] != "Unsubscribed":
                fails.append(f"step 4: status reads {r['subscription_status']!r}, not 'Unsubscribed'; {shot4}")
            if not near(r["unsubscribed_on"], result["clicked_at"]):
                fails.append(f"step 4: Un-subscription date {r['unsubscribed_on']!r} is not today at T "
                             f"({result['clicked_at']:%m/%d/%Y %I:%M:%S %p}); {shot4}")
    finish(tc, fails)


# ===========================================================================
# 149298 — manual unsubscribe is audit-logged (History trail)
# ===========================================================================
@marks(pytest.mark.functional_high, pytest.mark.tc_149298)
def test_149298_manual_unsubscribe_is_audit_logged(subs):
    """MEDIA-MCHUB-TC-244: the manual unsubscribe is recorded with a timestamp
    and the acting Administrator (judged by the record's History trail)."""
    tc, fails = "149298", []
    email, _, _ = subs.subscribe(tc)
    subs.confirm_active(tc, email)
    admin = subs.admin()
    admin_name = admin.signed_in_user()[1]

    with allure.step("1. Open the subscriber panel as Administrator"):
        admin.open_list()
        missing = headers_ok(admin.column_headers())
        shot1 = admin.evidence(f"{tc}_step1_list")
        if missing:
            fails.append(f"step 1: list lacks columns {missing}; {shot1}")

    with allure.step("2. Set the address to Unsubscribed at time T"):
        result = admin.unsubscribe(email)
        row = admin.wait_row(email, lambda r: r["subscription_status"] == "Unsubscribed", timeout=60.0)
        shot2 = admin.evidence(f"{tc}_step2_unsubscribed")
        if row.get("subscription_status") != "Unsubscribed":
            pytest.fail(f"step 2: the record does not show Unsubscribed: {row}; {shot2}")

    with allure.step("3. Open the History of the address"):
        trail = admin.history(email)
        shot3 = admin.evidence(f"{tc}_step3_history")
        record(tc, "history (info)", trail=trail, admin=admin_name, screenshot=shot3)
        hits = [h for h in trail
                if any(c["field"].strip() == "Active Subscription" and c["before"].strip() == "true"
                       and c["after"].strip() == "false" for c in h["changes"])]
        if not hits:
            fails.append(f"step 3: no History entry records Active -> Unsubscribed: {trail}; {shot3}")
        else:
            h = hits[0]
            if h["who"].strip() != admin_name.strip():
                fails.append(f"step 3: History actor {h['who']!r} is not the Administrator {admin_name!r}; {shot3}")
            if not near(h["when"], result["clicked_at"]):
                fails.append(f"step 3: History time {h['when']!r} is not T "
                             f"({result['clicked_at']:%m/%d/%Y %I:%M:%S %p}); {shot3}")
    finish(tc, fails)


# ===========================================================================
# 149299 — re-subscription reactivates the same record
# ===========================================================================
@marks(pytest.mark.edge, pytest.mark.tc_149299)
def test_149299_resubscribe_reactivates_same_record(subs):
    """MEDIA-MCHUB-TC-245: a previously unsubscribed address that subscribes
    again is reactivated on the same record with a new subscription date."""
    tc, fails = "149299", []
    email, _, _ = subs.subscribe(tc)
    row0 = subs.confirm_active(tc, email)
    t0 = parse_list_date(row0["subscribed_on"])
    admin = subs.admin()
    admin.open_list()
    pre = admin.unsubscribe(email)  # substitute for the email link (no inbox in this batch)
    row_u = admin.wait_row(email, lambda r: r["subscription_status"] == "Unsubscribed", timeout=60.0)
    if row_u.get("subscription_status") != "Unsubscribed" or not near(row_u.get("unsubscribed_on", ""),
                                                                     pre["clicked_at"]):
        pytest.fail(f"PRECONDITION: {email} not Unsubscribed with today's date: {row_u}")
    entry_id_before = row_u["entry_id"]
    record(tc, "precondition (info)", t0=str(t0), unsubscribed=row_u,
           note="unsubscribed via the Administrator's manual Unsubscribe, not the email link (no inbox)")

    with allure.step("1. Open the logged-out Media Center page — the band is shown"):
        view = subs.visitor()
        if not view.band_visible():
            fails.append(f"step 1: subscription band not shown; {view.evidence(f'{tc}_step1_band')}")

    with allure.step("2. Subscribe the same address again"):
        t1 = datetime.now()
        result = view.subscribe(email)
        shot2 = view.evidence(f"{tc}_step2_resubscribe")
        record(tc, "resubscribe (info)", result=result, screenshot=shot2)
        if not result.get("ok") or MSG_SUBSCRIBED not in result.get("text", ""):
            fails.append(f"step 2: no success confirmation on re-subscription: {result}; {shot2}")

    with allure.step("3-4. Editor opens the subscriber panel and searches the address"):
        editor = subs.role(ROLE_EDITOR)
        editor.open_list()
        subs.require_role(editor, ROLE_EDITOR)
        missing = headers_ok(editor.column_headers())
        editor.search(email)
        rows = editor.rows_for(email)
        shot4 = editor.evidence(f"{tc}_step4_editor_search")
        if missing:
            fails.append(f"step 3: list lacks columns {missing}; {shot4}")
        if len(rows) != 1:
            fails.append(f"step 4: {len(rows)} rows for {email} (expected one reactivated record): {rows}; {shot4}")
        else:
            r = rows[0]
            if r["entry_id"] != entry_id_before:
                fails.append(f"step 4: the row id changed {entry_id_before} -> {r['entry_id']} (new record); {shot4}")
            if r["subscription_status"] != "Active":
                fails.append(f"step 4: status {r['subscription_status']!r}, not Active; {shot4}")
            t_new = parse_list_date(r["subscribed_on"])
            if t_new is None or (t0 is not None and t_new <= t0) or not near(r["subscribed_on"], t1):
                fails.append(f"step 4: Subscription Date {r['subscribed_on']!r} is not T1 "
                             f"({t1:%m/%d/%Y %I:%M:%S %p}; T0 {t0}); {shot4}")
    finish(tc, fails)


# ===========================================================================
# 149328 — Editor can view and export
# ===========================================================================
@marks(pytest.mark.auth, pytest.mark.tc_149328)
def test_149328_editor_views_and_exports(subs):
    """MEDIA-MCHUB-TC-274: the Site Content Editor opens the subscriber list and exports it."""
    tc, fails = "149328", []
    email, _, _ = subs.subscribe(tc)
    subs.confirm_active(tc, email)
    editor = subs.role(ROLE_EDITOR)

    with allure.step("1. Editor opens the subscriber panel; the test address is visible"):
        editor.open_list()
        subs.require_role(editor, ROLE_EDITOR)
        missing = headers_ok(editor.column_headers())
        rows = editor.rows_for(email)
        shot1 = editor.evidence(f"{tc}_step1_editor_list")
        if missing:
            fails.append(f"step 1: list lacks columns {missing}; {shot1}")
        if len(rows) != 1:
            fails.append(f"step 1: {email} not listed once for the Editor: {rows}; {shot1}")

    with allure.step("2. Export (CSV)"):
        export = editor.export_csv(DOWNLOADS)
        shot2 = editor.evidence(f"{tc}_step2_export")
        record(tc, "export (info)", file=export.get("path"), filename=export.get("filename"),
               head=export.get("text", "")[:400], screenshot=shot2)
        if not export["button"]:
            fails.append(f"step 2: no Export CSV action for the Editor; {shot2}")
        elif email not in export.get("text", ""):
            fails.append(f"step 2: the CSV ({export.get('filename')}) does not contain {email}; {shot2}")
    finish(tc, fails)


# ===========================================================================
# 149329 — Editor cannot manually unsubscribe
# ===========================================================================
@marks(pytest.mark.auth, pytest.mark.tc_149329)
def test_149329_editor_cannot_unsubscribe(subs):
    """MEDIA-MCHUB-TC-275: the Site Content Editor cannot manually unsubscribe a subscriber."""
    tc, fails = "149329", []
    email, _, _ = subs.subscribe(tc)
    subs.confirm_active(tc, email)
    editor = subs.role(ROLE_EDITOR)

    with allure.step("1. Editor opens the subscriber panel"):
        editor.open_list()
        subs.require_role(editor, ROLE_EDITOR)
        missing = headers_ok(editor.column_headers())
        editor.search(email)
        rows = editor.rows_for(email)
        shot1 = editor.evidence(f"{tc}_step1_editor_list")
        if missing:
            fails.append(f"step 1: list lacks columns {missing}; {shot1}")
        if len(rows) != 1:
            pytest.fail(f"step 1: {email} not listed once for the Editor: {rows}; {shot1}")

    with allure.step("2. Attempt to set it to Unsubscribed (UI action, else the direct update request)"):
        ui_action = "reject" in rows[0]["actions"] or "Unsubscribe" in rows[0]["links"]
        clicked = editor.click_token_unsubscribe(email) if ui_action else {"present": False}
        shot2 = editor.evidence(f"{tc}_step2_attempt")
        editor.open_list()
        mid = editor.rows_for(email)
        if mid and mid[0]["subscription_status"] == "Active":
            attempt = editor.api_set_active(email, False)
        else:
            attempt = {"status": 0, "body": "skipped — UI action already changed the record"}
        record(tc, "editor unsubscribe attempt (info)", ui_action=ui_action, row=rows[0], ui=clicked,
               after_ui=mid, api=attempt, screenshot=shot2)
        if ui_action and mid and mid[0]["subscription_status"] != "Active":
            fails.append(f"step 2: the Editor's Unsubscribe action WENT THROUGH (record now "
                         f"{mid[0]['subscription_status']}); dialogs {clicked.get('dialogs')}; {shot2}")
        elif ui_action and not clicked.get("access_denied"):
            fails.append(f"step 2: the Editor is offered Unsubscribe and the attempt is not refused with "
                         f"{MSG_ACCESS_DENIED!r}: {clicked}; {shot2}")
        if attempt["status"] and attempt["status"] < 400:
            fails.append(f"step 2: the direct update request as Editor was ACCEPTED "
                         f"(HTTP {attempt['status']}: {attempt['body'][:160]}); {shot2}")

    with allure.step("3. Reload — still Active with no Un-subscription Date"):
        editor.open_list()
        subs.require_role(editor, ROLE_EDITOR)
        editor.search(email)
        after = editor.rows_for(email)
        shot3 = editor.evidence(f"{tc}_step3_reload")
        if len(after) != 1 or after[0]["subscription_status"] != "Active":
            fails.append(f"step 3: the record is no longer Active: {after}; {shot3}")
        elif parse_list_date(after[0]["unsubscribed_on"]) is not None:
            fails.append(f"step 3: an Un-subscription Date was set: {after[0]['unsubscribed_on']!r}; {shot3}")
        record(tc, "inbox (info)", note="Unsubscribe Confirmation email not checked — no inbox in this batch")
    finish(tc, fails)


# ===========================================================================
# 149332 / 149334 / 149336 — roles without subscriber permission
# ===========================================================================
def _assert_refused(subs: Subs, tc: str, role: str) -> None:
    fails = []
    email, _, _ = subs.subscribe(tc)
    subs.confirm_active(tc, email)
    drv = subs.role(role)
    with allure.step(f"Sign in as {role} and open the subscriber panel"):
        probe = drv.access_probe()
        shot = drv.evidence(f"{tc}_{role.replace(' ', '_')}_subscriber_panel")
        record(tc, "access probe (info)", role=role, probe=probe, screenshot=shot)
        if probe["signed_in_user"][0] != ROLE_USER_IDS[role]:
            pytest.fail(f"PRECONDITION: session is {probe['signed_in_user']}, not {role}; {shot}")
        if email in probe["emails_on_page"] or probe["subscriber_rows"]:
            fails.append(f"{role} sees subscriber data ({probe['subscriber_rows']} rows; "
                         f"test address shown: {email in probe['emails_on_page']}); {shot}")
        if not probe["access_denied_exact"]:
            fails.append(f"{role} is not refused with {MSG_ACCESS_DENIED!r}: {probe['denial_lines']}; {shot}")
    finish(tc, fails)


@marks(pytest.mark.auth, pytest.mark.tc_149332)
def test_149332_author_has_no_subscriber_access(subs):
    """MEDIA-MCHUB-TC-278: the Site Content Author cannot open the list and sees no subscriber emails."""
    _assert_refused(subs, "149332", ROLE_AUTHOR)


@marks(pytest.mark.auth, pytest.mark.tc_149334)
def test_149334_form_manager_has_no_subscriber_access(subs):
    """MEDIA-MCHUB-TC-280: the Form Manager cannot view Media Center subscriber email addresses."""
    _assert_refused(subs, "149334", ROLE_FORM_MANAGER)


@marks(pytest.mark.auth, pytest.mark.tc_149336)
def test_149336_site_member_has_no_subscriber_access(subs):
    """MEDIA-MCHUB-TC-282: a signed-in site member with no role cannot see subscriber email addresses."""
    _assert_refused(subs, "149336", ROLE_MEMBER)


# ===========================================================================
# 149285 — news edit in its own module reflected in the hub news feed
# ===========================================================================
NEWS_TITLE = "QCTEST-130709 Feed article"
NEWS_TITLE_EDITED = "QCTEST-130709 Feed article edited"
NEWS_TITLE_AR = "QCTEST-130709 مقال الخلاصة"
FEED_WAIT_S = 180.0
NEWS_IMAGE = "cms/tests/home_latest_news/fixtures/news_thumbnail.png"


@pytest.fixture
def news(browser):
    """(editor driver, registry) — every captured QCTEST article is deleted after."""
    ctx = new_context(browser, use_auth_state=False)
    drv = McNewsAdminPage(ctx.new_page(), slug=NEWS_SLUG)
    if drv.login_as_role(ROLE_EDITOR) == "auth_failed":
        pytest.fail("PRECONDITION: Liferay refused the Site Content Editor credentials")
    registry: dict = {"entry": None, "title": ""}
    yield drv, registry
    entry: NewsEntry | None = registry["entry"]
    if entry is not None:
        ok = False
        try:
            drv.open_list_all()
            current = drv.row_title_of(entry) or registry["title"]
            ok = drv.delete_disposable(entry, current)
        except Exception as exc:  # noqa: BLE001
            record("149285", "teardown error", error=repr(exc))
        record("149285", "teardown (info)", entry=entry.__dict__, deleted=ok)
        if not ok:
            record("149285", "LEFTOVER", entry=entry.__dict__)
    ctx.close()


@marks(pytest.mark.functional_high, pytest.mark.workflow, pytest.mark.tc_149285)
def test_149285_news_edit_reflected_in_feed(news, browser):
    """MEDIA-MCHUB-TC-231: editing a news article in its own module is reflected
    in the Media Center news feed (Editor publishes, Active ticked)."""
    tc, fails = "149285", []
    drv, registry = news
    record(tc, "case-vs-build (info)",
           note=f"case step 2 names {CASE_NEWS_PATH} (Home Latest News object); the hub feed reads the "
                f"News object manage-{NEWS_SLUG} (/o/qc-media-center-api/news) — article authored there")
    drv.open_list_all()
    if drv.signed_in_user()[0] != ROLE_USER_IDS[ROLE_EDITOR]:
        pytest.fail(f"PRECONDITION: session is {drv.signed_in_user()}, not the Editor")
    leftovers = [r for r in drv.list_rows() if r["title"].strip() in (NEWS_TITLE, NEWS_TITLE_EDITED)]
    if leftovers:
        pytest.fail(f"PRECONDITION: QCTEST article(s) from an earlier run still exist: {leftovers}")
    ids_before = drv.snapshot_ids()

    with allure.step("Precondition: create QCTEST-130709 article Published + Active (Editor)"):
        drv.open_create_form()
        drv.fill_article(NEWS_TITLE, NEWS_TITLE_AR, "QCTEST-130709 feed article body.",
                         "QCTEST-130709 نص مقال الخلاصة.", date.today().strftime("%d/%m/%Y"),
                         category="Collaboration", image=NEWS_IMAGE)
        drv.click_publish()
        created_msgs = drv.success_messages("Arabic content saved", timeout=20.0)
        shot0 = drv.evidence(f"{tc}_pre_create")
        entry = drv.identify_created(NEWS_TITLE, ids_before)
        if entry is None:
            pytest.fail(f"PRECONDITION: the QCTEST article was not created: {drv.refusal_evidence()} "
                        f"{created_msgs}; {shot0}")
        registry.update(entry=entry, title=NEWS_TITLE)
        status = drv.row_status_raw_of(entry)
        if status.upper() != "PUBLISHED":
            pytest.fail(f"PRECONDITION: the QCTEST article is {status!r}, not PUBLISHED; {shot0}")

    view_ctx = new_context(browser, use_auth_state=False)
    try:
        view = McHubPublicView(view_ctx.new_page())
        with allure.step("1. Logged-out Media Center — the feed shows the QCTEST article"):
            shown, titles = view.poll_news_feed(lambda t: NEWS_TITLE in t, timeout=FEED_WAIT_S)
            shot1 = view.evidence(f"{tc}_step1_feed")
            if view.signed_in():
                pytest.fail("PRECONDITION: public context is signed in")
            if not shown:
                api = view.news_api_items()
                needs_decision(tc, "The published + Active QCTEST-130709 article (today's publication date) does "
                                   "not surface in the hub news feed; reaching that surface would need real "
                                   "content changed — how should 149285 be verified?",
                               feed=titles, api=api, screenshot=shot1)

        with allure.step("2. Edit the title in the news module and publish"):
            drv.open_entry_en(entry.code)
            drv.fill_en("title", NEWS_TITLE_EDITED)
            drv.click_publish()
            msgs = drv.success_messages(MSG_SAVED_AND_PUBLISHED, timeout=20.0)
            shot2 = drv.evidence(f"{tc}_step2_edit_published")
            drv.open_list_all()
            registry["title"] = drv.row_title_of(entry) or registry["title"]
            status2 = drv.row_status_raw_of(entry)
            # The case asks for "the toast", not a wording: the Liferay generic
            # success toast ("Your request completed successfully.") or the
            # tool's "Saved and published." both satisfy it.
            toast = [m for m in msgs if MSG_SAVED_AND_PUBLISHED in m or "completed successfully" in m]
            record(tc, "edit toast (info)", messages=msgs)
            if not toast:
                fails.append(f"step 2: no success toast after the edit: {msgs}; {shot2}")
            if status2.upper() != "PUBLISHED":
                fails.append(f"step 2: badge reads {status2!r}, not PUBLISHED; {shot2}")
            if registry["title"] != NEWS_TITLE_EDITED:
                pytest.fail(f"step 2: the edit did not save (title {registry['title']!r}); {shot2}")

        with allure.step("3. Reload the logged-out Media Center — the feed shows the edited title"):
            shown3, titles3 = view.poll_news_feed(lambda t: NEWS_TITLE_EDITED in t and NEWS_TITLE not in t,
                                                  timeout=FEED_WAIT_S)
            shot3 = view.evidence(f"{tc}_step3_feed_edited")
            if not shown3:
                fails.append(f"step 3: the feed does not show {NEWS_TITLE_EDITED!r} within {FEED_WAIT_S:.0f}s: "
                             f"{titles3}; {shot3}")
    finally:
        view_ctx.close()
    finish(tc, fails)

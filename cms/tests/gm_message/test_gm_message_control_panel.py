"""
UPDATE 2026-10-13 (P3/P4 batch -- user decision, read this first): with
QC_ALLOW_LIVE_SINGLETON_WRITES=1 the write guard below OPENS for this
module's real singleton (cms/tests/live_write_guard.py): tests write test
data to it, never delete anything, log every persisted write to
reports/live-writes-20261013.jsonl, and leave the record Published. Without
the variable nothing changes (NOT APPLICABLE). Only this batch's test cases
open it (live_write_guard.P34_BATCH_TCS); P1/P2 tests stay NOT APPLICABLE.
P1/P2 RERUN 2026-10-13 (user decision, supersedes that last clause): the
rerun ids (live_write_guard.P12_BATCH_TCS) open it too, plus the real About
Hero Banner rows; their writes are logged first, nothing is deleted (QCTEST
rows are kept and logged), and a record left Unpublished / Draft / Pending
Review is re-published in `finally` (cms/tests/live_end_published.py).
The P3/P4 cases are scripted OFFLINE, not yet executed -- search for
"P3/P4 BATCH".

UPDATE 2026-10-13 (user decision -- read this first): automation no longer
writes to the real singleton 79878. Every case that needs a saved / published
/ unpublished change calls cms.tests.live_write_guard.
block_live_singleton_write() right before its first persisting step and is
reported NOT APPLICABLE (never skipped, never mutating). Refusal cases still
run and stop at once (stop_unless_refused()) when the refusal is not seen.
The module snapshot/restore fixture and the per-test status gate below are
NO LONGER WIRED (engine kept in cms/tests/singleton_baseline.py and
gm_message_singleton.py). Notes below about restores are history.

UPDATE 2026-10-12 (restore-once): tests no longer restore 79878 in their
`finally`. The record is captured once before the first GM_GROUP test and
restored + verified once after the last (`_singleton_baseline`, see
cms/tests/singleton_baseline.py and gm_message_singleton.py); a killed run is
healed by the next run or by `python tools/restore_singleton.py --pbi 129397`.
Older docstrings below that describe a per-test "finally-restore" are history.

UPDATE 2026-10-12 (Phase-3 batch, read this first): the 78 cases listed in
.claude/qa-runs/phase3-20261012/129397.todo.json are no longer stubs -- they
are scripted against Object Authoring (see the helper block below the
imports) and NOT yet executed. The remaining `pytest.mark.skip` stubs are
outside that batch. The historical notes below describe the earlier state.

cms/tests/gm_message/test_gm_message_control_panel.py — Control_Panel-tagged
cases for PBI 129397 (QC-ABOUT-005 — General Manager's Message) from the
priority batch (see test_gm_message_web.py's module docstring for the full
ID-range context).

Every case here is a `Both` (Control_Panel + Web) case whose CMS-authoring
step this batch could not perform: no stable, extracted locators exist yet
for the GM's Message custom-widget edit form inside the Liferay Control
Panel (this batch's scope, per explicit instruction, is Web/public-facing
verification first), and several of these actions are destructive against
the shared qcdev.ihorizons.com environment (publish/unpublish/draft-state
changes) with no confirmed teardown path.

Per the user's explicit instruction, these are SKIPPED with a concrete
reason rather than blocking the batch — never silently dropped, never faked
as a pass (automation-standards.md's Result Integrity rule). Where the
case's PUBLIC-FACING half can be verified standalone against already-
published content without the CMS write, that verification already exists
as a passing test in test_gm_message_web.py and is cross-referenced below
instead of being duplicated here.

SECOND PASS (2026-08-25) — full Control_Panel batch for PBI 129397.
review_test_coverage(129397) tags exactly 147 cases `Control_Panel`; the 5
above were already scripted as skip stubs by the prior pass and are left
untouched. This pass attempted, per the QA Manager's policy, to automate the
remaining 142 as real field-validation / persistence / permission-denial
checks against the Liferay CMS admin edit form for the GM's Message custom
widget (policy explicitly allows this: required-field, char-limit, upload
format/size, injection-safety, save-verify-revert, and non-mutating Auth
denial checks are all SAFE categories).

That attempt was blocked by a live, reproduced environment failure, not a
locator gap: qcdev.ihorizons.com's "developer mode connection limit"
interstitial (`/c/portal/license_activation`) intercepted every login
attempt this session, including a direct Playwright login through
CmsLoginPage's own confirmed-real selectors, and its own "reset all
connections" link did not clear it (click timed out; the login form never
rendered afterward). This is the SAME unresolved qcdev infrastructure issue
already flagged in cms/pages/control_panel/login_page.py's docstring
("...the automated suite will very likely hit this same wall when it runs
standalone against qcdev; that is a real, unresolved dev-mode
connection-limit issue on the qcdev instance itself and needs a fix from
whoever administers it, not a workaround in this Page Object"). No
authenticated admin session could be established at all this session, so no
edit-form locators could be extracted or confirmed for ANY of the 142 cases
— per the one-pass/real-locators rule, none are invented here.

All 142 are therefore registered below as explicit `pytest.mark.skip`
stubs — never silently dropped — each carrying its own `tc_<id>` +
`pbi_129397` + `control_panel` marker (plus a best-effort category marker
derived from the source case's own `category`/tags field: `auth`,
`functional_high`, `functional_low`, `edge`, `ui`, `bilingual`,
`dataintegrity`, `regression` where the source tagged it `Regression`) so
`pytest --collect-only` and Allure both keep the full 147-case gap visible.
Re-attempt once qcdev's login path is confirmed clear of the license/
connection-limit interstitial — this is an infra blocker, not a coverage
decision, and should be retried the next session rather than re-judged.
"""

import allure
import pytest

from cms.pages.gm_message.gm_message_admin_page import GmMessageAdminPage
from web.pages.gm_message.gm_message_page import GM_MESSAGE_PATH, GmMessagePage
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED


# ===========================================================================
# PHASE-3 BATCH 2026-10-12 -- shared scenario helpers for the 78 cases in
# .claude/qa-runs/phase3-20261012/129397.todo.json (Azure title/steps = the
# oracle). Every case below drives the ONE live singleton record (79878,
# `QCDEMO-129397-general-managers-message`) through Object Authoring only.
#
# TEST_OWNED contract (user decision 2026-10-12 -- restore ONCE per run):
#   * the module fixture `_singleton_baseline` (cms/tests/singleton_baseline.py,
#     record adapter in gm_message_singleton.py) captures the FULL record --
#     EN/AR text, Page Content HTML, attachment bytes, Active Status, workflow
#     status -- to reports/backups/129397_gm_message_<stamp>/ before the first
#     GM_GROUP test, heals from an interrupted run's snapshot first, and
#     restores + verifies by re-read ONCE after the last one.
#   * per test, `_singleton_gate` only normalises the STATUS back to
#     Published (approve / publish -- no field writes). Tests do not restore;
#     `_snapshot()` is a runtime read of the values a test compares against,
#     never an assumed original.
#   * killed run: python tools/restore_singleton.py --pbi 129397
# Wait budget: the gate's status step + main path fit @timeout(300).
# Product rulings applied (memory / bug-rules): message WORDING, a missing
# success toast, and 404/"Coming Soon" instead of "Access Denied" are not
# bugs -- the behaviour is asserted, the wording is attached as a note.
# Upload size: accepting <= 3 MB is acceptable; > 3 MB accepted is a bug.
# ===========================================================================
import time as _time
from pathlib import Path as _Path

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_UNKNOWN,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.gm_message.gm_message_admin_page import GM_MESSAGE_ENTRY_CODE
from config.settings import cms_role_credentials
from core.utils.logger import get_logger
from core.utils.waits import wait_until
from core.web.browser import new_context
from tools.fixture_factory import make_bmp, make_gif, make_jpg, make_pdf, make_png, make_svg
from cms.tests.gm_message.gm_message_singleton import (
    norm_html as _norm_html,
    read_state as _read_state,
    same_file as _same_file,
)
from cms.tests.singleton_baseline import (
    drive_to_editable,
    drive_to_published,
    list_status,
)
from cms.tests.live_end_published import leave_published
from cms.tests.live_write_guard import block_live_singleton_write, log_live_write, stop_unless_refused

_log = get_logger("test_gm_message_control_panel")

GM_GROUP = pytest.mark.xdist_group("gm_message_79878")
# NOT WIRED (user decision 2026-10-13): the module baseline fixture
# (`module_baseline_fixture(build_baseline)`) and the per-test status gate
# (`singleton_gate("gm_message_79878")`) both WRITE to 79878 -- the gate
# approves / publishes before every test, the fixture restores at module end.
# No test writes to the record any more, so neither is attached.
GM_RECORD = "GM Message 79878 (QCDEMO-129397-general-managers-message)"
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_NO_ROLE = "Site Member"  # signed-in account with no authoring role

A = GmMessageAdminPage  # label constants live on the Page Object
AR = A.AR_SUFFIX
PUBLISH_WAIT = 90.0
DRAFT_WAIT = 30.0
REFLECT_WAIT = 60.0
MB = 1024 * 1024
SIZE_TOLERANCE = 3 * MB  # user ruling 2026-10-07
# Seconds of the 300s timeout NOT given to the main path: the gate's status
# precondition (one publish, ~30-90 s) runs before `_snapshot()` starts the
# clock, plus context teardown. pytest-timeout on Windows uses the thread
# method and hard-exits on expiry (no `finally`), so every wait in the main
# path is capped by this deadline.
TIMEOUT_RESERVE = 110.0
_DEADLINE = {"t": None}
NON_PUBLISHED = (STATUS_DRAFT, "Unpublished", STATUS_PENDING_REVIEW, STATUS_UNKNOWN)


def _attach(name: str, body) -> None:
    try:
        allure.attach(str(body), name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:  # noqa: BLE001
        pass


# ---- runtime read (the snapshot/restore engine lives in gm_message_singleton.py)
def _budget(wanted: float) -> float:
    """`wanted`, capped by the main-path deadline; raises once it is spent."""
    if _DEADLINE["t"] is None:
        return wanted
    left = _DEADLINE["t"] - _time.monotonic()
    if left <= 0:
        raise AssertionError("main-path time budget spent")
    return max(5.0, min(wanted, left))


def _snapshot(page, tmp_path=None, files=(), writes=(), budget: float = 300) -> dict:
    """RUNTIME read of the singleton's current values -- what this test
    compares against. It restores nothing: the module fixture restores the
    captured baseline once, at module end. `writes` / `files` = keys the test
    relies on; each must be readable before any mutation, or the test fails
    without touching the record. `tmp_path` is accepted for call-site
    compatibility (attachment bytes now live in the module snapshot).
    `budget` = the test's own @timeout (P3/P4 batch 2026-10-13: 480)."""
    _DEADLINE["t"] = _time.monotonic() + budget - TIMEOUT_RESERVE
    snap = _read_state(A(page))
    _attach("current values (runtime read)", snap)
    if snap["status"] != STATUS_PUBLISHED:
        pytest.fail(
            f"Precondition: GM Message 79878 must be Published before this test "
            f"is exercised; it is {snap['status']!r} (no status gate runs any "
            "more -- user decision 2026-10-13). Not mutating."
        )
    missing = [k for k in tuple(writes) + tuple(f"file:{f}" for f in files) if snap.get(k) is None]
    if missing:
        pytest.fail(f"Precondition: no readable value for {missing} (VERIFY-LIVE label / "
                    "editor token?) -- not mutating the live record.")
    return snap


# ---- sessions / public reads ----------------------------------------------
def _role_session(browser, role: str):
    """FRESH context signed in as `role` -- never TEST_USER, never `page`.

    Open EVERY role session a test needs BEFORE its first mutation of 79878
    (2026-10-12): a login that fails after an Unpublish / Submit strands the
    shared record mid-workflow, and the next test's gate inherits it."""
    context = new_context(browser, use_auth_state=False)
    role_page = context.new_page()
    email, password = cms_role_credentials(role)
    CmsLoginPage(role_page).open_login().login(email, password)
    return context, role_page


def _anon(browser):
    context = new_context(browser, use_auth_state=False)
    return context, GmMessagePage(context.new_page())


def _close(*contexts) -> None:
    for ctx in contexts:
        try:
            if ctx is not None:
                ctx.close()
        except Exception:  # noqa: BLE001
            pass


def _public_shows(public, check, locale="en", timeout=REFLECT_WAIT) -> bool:
    """Polls the PUBLIC page (anonymous context) until `check(public)` holds."""
    def _probe() -> bool:
        public.open_gm_message(locale=locale)
        try:
            return bool(check(public))
        except Exception:  # noqa: BLE001 -- element absent this render
            return False

    try:
        wait_until(_probe, timeout=_budget(timeout), poll=5)
        return True
    except Exception:  # noqa: BLE001
        return False


def _workflow_list(admin):
    """Fresh entries-list read for singleton_baseline's workflow driver."""
    return lambda: admin.open_list("en")


def _editable(authoring):
    """Published -> editable through the documented ROW transition (Unpublish,
    confirm accepted, verified by a fresh list read), then the form is
    reopened; returns the same object.

    CHANGED 2026-10-12: this used the in-form `unpublish_to_edit_as_draft()`,
    whose bare `networkidle` wait (30 s default) never settles on this
    surface. In tc_136383 it raised AFTER the Unpublish had committed, which
    left 79878 Unpublished (allure-129397-20261012-2120)."""
    if authoring.current_status() == STATUS_PUBLISHED:
        admin = A(authoring.page)
        # Logged BEFORE the click (user decision 2026-10-13: every live write).
        log_live_write(GM_RECORD, "<workflow>", "Unpublished", None, action="unpublish",
                       note="make the form editable (row Unpublish)")
        drive_to_editable(_workflow_list(admin), GM_MESSAGE_ENTRY_CODE, budget=_budget(PUBLISH_WAIT))
        authoring.reopen()
    return authoring


def _publish(admin, authoring) -> str:
    """Submit the form, then FINISH the move to Published on the documented
    transition. Returns the status read from a fresh entries list.

    The form submit commits this test's field writes and runs the form's
    own validation. It is NOT enough on an UNPUBLISHED record: there it
    saves but leaves the status Unpublished. Live 2026-10-12, tc_136386:
    "Editing ... (Unpublished) ... last modified 21:27" after the submit,
    and 79878 was stranded. Any status short of Published is driven on
    through singleton_baseline.drive_to_published(), the path the module
    baseline uses:
      * Unpublished -> the row's `data-qc-oel-publish`, with the
        confirm()/prompt() chain accepted;
      * Pending Review -> approve;
      * Draft -> Submit for Review.
    Each step is verified on a fresh list read. A row action publishes the
    STORED version, so the submit above must stay: it is what stores the
    test's edits."""
    log_live_write(GM_RECORD, "<form submit>", "fields entered by the test", None, action="publish",
                   note="form Submit, then documented transitions to Published")
    admin.submit_publish(authoring)
    status = _drive_published(admin)
    authoring.reopen()  # callers keep using `authoring` on a fresh form
    return status


def _drive_published(admin) -> str:
    """After a form submit: Published via the documented transitions (fresh
    list read first; returns at once if already Published; the path taken is
    attached by drive_to_published)."""
    log_live_write(GM_RECORD, "<workflow>", STATUS_PUBLISHED, None, action="publish",
                   note="documented transitions to Published (no-op when already Published)")
    return drive_to_published(
        _workflow_list(admin), GM_MESSAGE_ENTRY_CODE,
        lambda: admin.submit_publish(admin.open_record("en")),
        budget=_budget(PUBLISH_WAIT),
    )


def _gm_end_published(admin, tc: str):
    """P1/P2 RERUN 2026-10-13 (user decision): `finally` -- 79878 back to
    Published when this test's write gate opened (Unpublished -> row action
    `[data-qc-oel-publish]`; Pending Review -> approve; verified on a fresh
    list read; logged first). See cms/tests/live_end_published.py."""
    return leave_published(GM_RECORD, _workflow_list(admin), GM_MESSAGE_ENTRY_CODE,
                           lambda: admin.submit_publish(admin.open_record("en")), tc)


def _save_draft(authoring) -> str:
    log_live_write(GM_RECORD, "<form>", STATUS_DRAFT, None, action="save-draft", note="Save as Draft")
    authoring.save_as_draft()
    authoring.wait_for_status(STATUS_DRAFT, timeout=_budget(DRAFT_WAIT))
    return authoring.current_status()


def _marker(tc: str, what: str) -> str:
    return f"QCTEST-{tc}-{what}"


_PUBLIC_GETTER = {
    A.LABEL_PAGE_TITLE: lambda p: p.title_text(),
    A.LABEL_SALUTATION: lambda p: p.salutation_text(),
    A.LABEL_GM_NAME: lambda p: p.portrait_name_text(),
    A.LABEL_DESIGNATION: lambda p: p.portrait_designation_text(),
    A.LABEL_CLOSING: lambda p: p.signature_regards_text(),
    A.LABEL_ALT_TEXT: lambda p: p.portrait_alt_text(),
}


# ---- field-type helpers (ONE per type, called by every case) --------------
def _text_valid(page, browser, tc: str, label: str, value: str, locale: str = "en",
                public_check: bool = False) -> None:
    """Valid text: accepted, persists on a fresh reopen; for AR (or when
    `public_check`) the published public page shows it (AR: RTL)."""
    field = label + (AR if locale == "ar" else "")
    block_live_singleton_write(GM_RECORD, f"publish of {field!r} = {value!r}")
    current = _snapshot(page, writes=(field,))
    admin = A(page)
    anon_ctx = None
    try:
        if current.get(field) == value:
            # Restore-once (2026-10-12): state carries over between cases.
            with allure.step(f"Interim write: {field!r} already reads {value!r}"):
                _attach("note", "field already held the case's value; interim QCTEST value saved first")
                authoring = _editable(admin.open_record("en"))
                authoring.fill_text(field, _marker(tc, "INTERIM"))
                _publish(admin, authoring)
        with allure.step(f"Enter {value!r} in {field!r} and publish"):
            authoring = _editable(admin.open_record("en"))
            authoring.fill_text(field, value)
            status = _publish(admin, authoring)
        assert status == STATUS_PUBLISHED, f"publish did not commit ({status!r})"
        with allure.step("Reload the CMS record"):
            stored = admin.open_record("en").field_value(field)
        assert stored == value, f"{field!r} reads {stored!r} after reload, expected {value!r}"
        if locale == "ar" or public_check:
            anon_ctx, public = _anon(browser)
            getter = _PUBLIC_GETTER[label]
            with allure.step(f"Public {locale.upper()} page (anonymous) shows the value"):
                shown = _public_shows(public, lambda p: getter(p).strip() == value.strip(), locale)
                seen = getter(public) if shown else public.page_text()[:500]
            assert shown, f"public {locale} page does not show {value!r}; saw {seen!r}"
            if locale == "ar":
                assert public.document_direction() == "rtl", "AR page is not rendered RTL"
    finally:
        _close(anon_ctx)


def _text_empty_rejected(page, tc: str, label: str, locale: str = "en",
                         expected_msg: str = "") -> None:
    """Empty required text: Save/Publish refused, nothing persisted, record
    still Published. Wording is attached as a note, not asserted."""
    field = label + (AR if locale == "ar" else "")
    snap = _snapshot(page, writes=(field,))
    admin = A(page)
    with allure.step(f"Clear {field!r} and click Publish / Submit for Review"):
        authoring = admin.open_record("en")
        authoring.fill_text(field, "")
        native_before = admin.native_validation_message(field)  # client-side refusal, read BEFORE the click
        log_live_write(GM_RECORD, field, "", tc, action="attempt",
                       note="Publish with the field empty; expected REFUSED")
        admin.submit_publish(authoring)
        native = admin.native_validation_message(field) or native_before
        refusal = admin.refusal_text()
        _attach("validation shown (wording is a note, not an assertion)",
                f"expected: {expected_msg or 'required-field error'}\n"
                f"native: {native!r}\nbar: {refusal!r}")
    with allure.step("Reopen the record: nothing persisted"):
        after = admin.open_record("en")
        stored, status = after.field_value(field), after.current_status()
    stop_unless_refused(stored == snap[field] and status == STATUS_PUBLISHED, GM_RECORD,
                        f"Publish with an empty {field!r}",
                        {"native": native, "refusal": refusal, "stored": stored, "status": status})
    assert native or refusal, f"no validation error shown for an empty {field!r}"
    assert stored == snap[field], (
        f"empty {field!r} was persisted: reads {stored!r}, baseline {snap[field]!r}"
    )
    assert status == STATUS_PUBLISHED, f"record status changed to {status!r}"


def _content_html_valid(page, browser, tc: str, html: str, locale: str,
                        must_contain: tuple, public_check: bool = True) -> None:
    """Valid rich text: formatting persists on reopen and renders publicly."""
    block_live_singleton_write(GM_RECORD, f"publish of Page Content ({locale.upper()})")
    _snapshot(page, writes=(f"content_{locale}",))
    admin = A(page)
    anon_ctx = None
    try:
        with allure.step(f"Author Page Content ({locale.upper()}) rich text and publish"):
            authoring = _editable(admin.open_record("en"))
            admin.set_page_content_html(html, locale)
            status = _publish(admin, authoring)
        assert status == STATUS_PUBLISHED, f"publish did not commit ({status!r})"
        with allure.step("Reload the record and read the stored HTML"):
            admin.open_record("en")
            stored = admin.page_content_html(locale)
            _attach("stored html", stored)
        missing = [m for m in must_contain if m not in stored]
        assert not missing, f"formatting lost on reload: {missing} absent from {stored!r}"
        if public_check:
            anon_ctx, public = _anon(browser)
            with allure.step(f"Public {locale.upper()} page renders the formatting"):
                shown = _public_shows(public, lambda p: all(m in p.body_html() for m in must_contain), locale)
                body = public.body_html()
            assert shown, f"public body lacks {must_contain}: {body[:600]!r}"
            if locale == "ar":
                assert public.document_direction() == "rtl", "AR page is not RTL"
    finally:
        _close(anon_ctx)


def _content_html_rejected(page, tc: str, html: str, locale: str = "en", expected_msg: str = "") -> None:
    """Invalid / empty rich text: refused, stored HTML unchanged."""
    snap = _snapshot(page, writes=(f"content_{locale}",))
    admin = A(page)
    with allure.step(f"Set Page Content ({locale.upper()}) to {html!r} and Publish"):
        authoring = admin.open_record("en")
        admin.set_page_content_html(html, locale)
        log_live_write(GM_RECORD, f"Page Content ({locale.upper()})", html, tc, action="attempt",
                       note="Publish with invalid / empty rich text; expected REFUSED")
        admin.submit_publish(authoring)
        refusal = admin.refusal_text()
        _attach("validation shown (wording is a note)",
                f"expected: {expected_msg or 'required-field error'}\nbar: {refusal!r}")
    with allure.step("Reopen: nothing persisted"):
        after = admin.open_record("en")
        stored, status = admin.page_content_html(locale), after.current_status()
    stop_unless_refused(
        _norm_html(stored) == _norm_html(snap[f"content_{locale}"]) and status == STATUS_PUBLISHED,
        GM_RECORD, f"Publish with Page Content ({locale.upper()}) = {html!r}",
        {"refusal": refusal, "stored": stored[:200], "status": status})
    assert refusal, f"no validation error for Page Content ({locale}) = {html!r}"
    assert _norm_html(stored) == _norm_html(snap[f"content_{locale}"]), (
        f"rejected Page Content was persisted: {stored!r}"
    )
    assert status == STATUS_PUBLISHED, f"record status changed to {status!r}"


def _fixture(tmp_path, name: str, size: int):
    maker = {".jpg": make_jpg, ".png": make_png, ".gif": make_gif, ".pdf": make_pdf,
             ".svg": make_svg, ".bmp": make_bmp}[_Path(name).suffix]
    path = _Path(tmp_path) / name
    path.write_bytes(maker(size))
    return str(path)


def _upload_valid(page, browser, tmp_path, tc: str, label: str, name: str, size: int,
                  public_locale: str | None = None) -> None:
    """Valid image: uploads, persists on reopen; optionally the public page
    in `public_locale` serves it. Original bytes are restored once, at module
    end, from the module snapshot."""
    block_live_singleton_write(GM_RECORD, f"publish of a new {label!r} ({name})")
    _snapshot(page, tmp_path, files=(label,))
    admin = A(page)
    anon_ctx = None
    path = _fixture(tmp_path, name, size)
    try:
        with allure.step(f"Upload {name} ({size // 1024} KB) as {label!r} and publish"):
            authoring = _editable(admin.open_record("en"))
            log_live_write(GM_RECORD, label, name, None, action="upload", note=f"{size} bytes, then publish")
            authoring.upload_file(label, path)
            refusal = admin.refusal_text()
            status = _publish(admin, authoring)
        assert not refusal, f"valid upload showed an error: {refusal!r}"
        assert status == STATUS_PUBLISHED, f"publish did not commit ({status!r})"
        with allure.step("Reload the record"):
            current = admin.open_record("en").current_file_name(label)
        assert _same_file(current, name), f"{label!r} holds {current!r}, expected {name!r}"
        if public_locale:
            anon_ctx, public = _anon(browser)
            stem = _Path(name).stem
            src = (lambda p: p.hero_image_src()) if A.LABEL_HERO in label else (lambda p: p.portrait_image_src())
            with allure.step(f"Public {public_locale.upper()} page serves the uploaded image"):
                shown = _public_shows(public, lambda p: stem in src(p), public_locale)
                seen = src(public)
            assert shown, f"public {public_locale} image src {seen!r} is not {name!r}"  # VERIFY-LIVE: src carries file name
            if A.LABEL_PORTRAIT in label:
                assert public.is_portrait_card_visible(), "portrait card (maroon) not rendered"
    finally:
        _close(anon_ctx)


def _upload_rejected(page, tmp_path, tc: str, label: str, name: str, size: int,
                     expected_msg: str = "", size_case: bool = False) -> None:
    """Oversize / wrong-format image: rejected at the picker; nothing is
    saved. Size cases follow the 3 MB tolerance ruling: if the case's own
    2-3 MB file is accepted that is noted, and a 3.2 MB file MUST be refused."""
    snap = _snapshot(page, writes=(f"file:{label}",))
    admin = A(page)
    authoring = admin.open_record("en")
    with allure.step(f"Attempt to upload {name} ({size / MB:.1f} MB) as {label!r}"):
        rejected = authoring.upload_file_expect_rejected(label, _fixture(tmp_path, name, size))
        _attach("rejection shown (wording is a note)",
                f"expected: {expected_msg or 'format error'}\nbar: {admin.refusal_text()!r}")
    if size_case and not rejected and size <= SIZE_TOLERANCE:
        _attach("note", f"{size / MB:.1f} MB accepted -- within the 3 MB tolerance ruling, not a bug")
        with allure.step("Over-tolerance check: a 3.2 MB file must be refused"):
            authoring = admin.open_record("en")
            big = _Path(name).stem + "-3_2mb" + _Path(name).suffix
            rejected = authoring.upload_file_expect_rejected(
                label, _fixture(tmp_path, big, int(3.2 * MB)))
    assert rejected, f"{label!r} accepted a file it must refuse ({name})"
    with allure.step("Reopen without saving: the stored image is unchanged"):
        after = admin.open_record("en")
        current, status = after.current_file_name(label), after.current_status()
    assert _same_file(current, snap[f"file:{label}"] or ""), f"{label!r} changed to {current!r}"
    assert status == STATUS_PUBLISHED, f"record status changed to {status!r}"


def _upload_missing_rejected(page, tmp_path, tc: str, label: str, interrupted: bool = False) -> None:
    """Required image left empty: Publish refused; image unchanged.

    REWRITTEN 2026-10-14 (fix pass 5), the 134713/134717 pattern:
      * `Remove file` only takes effect on save, so the field cannot read
        empty before the click; the pending removal ("Undo remove" shown) is
        the precondition.
      * the refusal on this form is the browser's own constraint check -- the
        Publish click handler re-evaluates every required control and the
        browser blocks the submit with a bubble (no red bar, no request). It
        is read AFTER the click (`invalid_form_controls()`); a pre-click read
        is meaningless because every attachment control carries "<label> is
        required." from page load (read live 2026-10-14).
      * persistence is the proof: the stored file is unchanged on a fresh
        read. LAST MODIFIED is evidence only -- the click's Arabic-twin sync
        PUT (built from the STORED record) bumps it with nothing changed
        (read live 2026-10-14 with every write aborted).
      * if the CMS ACCEPTS the empty image, the previous file is re-attached
        at once (logged; the existing Documents & Media file, else its
        downloaded bytes), the record is left Published, and the test fails
        with the FINDING."""
    snap = _snapshot(page, tmp_path, files=(label,))
    original = snap[f"file:{label}"] or ""
    admin = A(page)
    before_mod = admin.open_list("en").row_last_modified(GM_MESSAGE_ENTRY_CODE)
    authoring = admin.open_record("en")
    backup = authoring.download_current_file(label, str(_Path(tmp_path) / (original or "original.bin")))
    if interrupted:
        # An interrupted upload cannot be produced deterministically; the
        # resulting state (field left empty) is reproduced with Remove file.
        _attach("note", "interrupted upload modelled as an emptied field (Remove file)")
    with _gm_end_published(admin, tc):
        with allure.step(f"Remove {label!r} (pending: 'Undo remove' shown) and click Publish"):
            assert admin.can_remove_file(label), f"precondition: {label!r} offers no Remove file"
            authoring.remove_current_file(label)
            pending = authoring.file_removal_pending(label)
            log_live_write(GM_RECORD, label, "", tc, action="attempt",
                           note=f"Publish with {label!r} removed (was {original!r}); expected REFUSED")
            blocked = authoring.submit_via_reading_validity(admin.PUBLISH_SUBMIT)
            shown = list(dict.fromkeys(authoring.last_click_messages + authoring.visible_form_messages()))
            refusal = admin.refusal_text()
            _attach("refusal shown (wording is a note, not an assertion)",
                    {"bar": refusal, "visible messages": shown,
                     "blocked controls right after the click": blocked})
        with allure.step("Reopen: the image is still set"):
            after = admin.open_record("en")
            current, status = after.current_file_name(label), after.current_status()
            after_mod = admin.open_list("en").row_last_modified(GM_MESSAGE_ENTRY_CODE)
        evidence = {"bar": refusal, "shown": shown, "blocked": blocked, "stored": current, "status": status,
                    "last_modified": [before_mod, after_mod]}
        _attach("read back", evidence)
        # LAST MODIFIED is evidence only: the click's Arabic-twin sync PUT
        # bumps it without changing a value (submit_via_reading_validity).
        accepted = not _same_file(current, original)
        restored = None
        if accepted:
            with allure.step(f"CMS accepted the empty {label!r}: put {original!r} back at once"):
                block_live_singleton_write(GM_RECORD, f"restore of {label!r} after an accepted removal")
                authoring = admin.open_record("en")
                log_live_write(GM_RECORD, label, original, tc, action="upload",
                               note="restore the previous file after the CMS accepted an empty required image")
                try:
                    authoring.select_existing_file(label, original)
                except Exception:  # noqa: BLE001 -- not pickable: upload the downloaded bytes
                    authoring = admin.open_record("en")
                    authoring.upload_file(label, backup)
                admin.submit_publish(authoring)
                _drive_published(admin)
                restored = _same_file(admin.open_record("en").current_file_name(label), original)
                _attach("restore", {"restored": restored, "file": original, "bytes": backup})
        stop_unless_refused(not accepted, GM_RECORD, f"Publish with {label!r} removed", evidence,
                            restored=restored)
        label_blocked = [m for m in shown if label.lower() in m.lower()] or [
            m for _, m in blocked if label.lower() in m.lower()]
        assert pending, "precondition: Remove file did not register (no 'Undo remove' shown)"
        assert refusal or label_blocked, (
            f"no required-image error when {label!r} is empty (blocked controls: {blocked})"
        )
        assert status == STATUS_PUBLISHED, f"record status changed to {status!r}"


def _content_empty_rejected(page, tc: str, locale: str = "en") -> None:
    """Page Content (`locale`) left EMPTY: Publish refused, stored HTML and the
    row's LAST MODIFIED unchanged. Added 2026-10-14 (fix pass 5) for 135490 /
    135493 / 136419 (`_content_html_rejected` is unchanged for 135504).

    Read live 2026-10-14: the clear DOES apply (getData() == '' and the
    posted `ObjectField_pageContent_en_US` twin empties), and r2 2026-10-13
    saved nothing (LAST MODIFIED 22:01:01 < the 22:01:33 attempt). The
    refusal is the browser's constraint check after the Publish click
    ("Page Content is required."), shown as a bubble, not a red bar -- the
    old helper read only the bar. LAST MODIFIED is evidence only: the same
    click fires an Arabic-twin sync PUT built from the STORED record, which
    bumps it with nothing changed (read live 2026-10-14, writes aborted). If the CMS ACCEPTS the empty content, the
    previous HTML is written back at once (logged), the record is left
    Published, and the test fails with the FINDING."""
    key = f"content_{locale}"
    snap = _snapshot(page, writes=(key,))
    admin = A(page)
    before_mod = admin.open_list("en").row_last_modified(GM_MESSAGE_ENTRY_CODE)
    with _gm_end_published(admin, tc):
        with allure.step(f"Clear Page Content ({locale.upper()}) and click Publish"):
            authoring = admin.open_record("en")
            # Cleared like a user (click, Ctrl+A, Delete): setData("") does
            # not trigger the site's Arabic guard (read live 2026-10-14).
            admin.clear_page_content_like_a_user(locale)
            applied = admin.page_content_html(locale)
            log_live_write(GM_RECORD, f"Page Content ({locale.upper()})", "", tc, action="attempt",
                           note="Publish with the rich text emptied; expected REFUSED")
            blocked = authoring.submit_via_reading_validity(admin.PUBLISH_SUBMIT)
            shown = list(dict.fromkeys(authoring.last_click_messages + authoring.visible_form_messages()))
            refusal = admin.refusal_text()
            _attach("refusal shown (wording is a note, not an assertion)",
                    {"editor data after the clear": applied, "bar": refusal, "visible messages": shown,
                     "blocked controls right after the click": blocked})
        with allure.step("Reopen: nothing persisted"):
            after = admin.open_record("en")
            stored, status = admin.page_content_html(locale), after.current_status()
            after_mod = admin.open_list("en").row_last_modified(GM_MESSAGE_ENTRY_CODE)
        evidence = {"bar": refusal, "shown": shown, "blocked": blocked, "stored": stored[:200], "status": status,
                    "last_modified": [before_mod, after_mod]}
        _attach("read back", evidence)
        # LAST MODIFIED is evidence only: the click's Arabic-twin sync PUT
        # bumps it without changing a value (submit_via_reading_validity).
        accepted = _norm_html(stored) != _norm_html(snap[key])
        restored = None
        if accepted:
            with allure.step(f"CMS accepted the empty Page Content ({locale.upper()}): put it back at once"):
                block_live_singleton_write(GM_RECORD, f"restore of Page Content ({locale.upper()})")
                authoring = admin.open_record("en")
                admin.set_page_content_html(snap[key], locale)
                log_live_write(GM_RECORD, f"Page Content ({locale.upper()})", "<the HTML read before the test>",
                               tc, action="publish", note="restore after the CMS accepted an empty value")
                admin.submit_publish(authoring)
                _drive_published(admin)
                admin.open_record("en")
                restored = _norm_html(admin.page_content_html(locale)) == _norm_html(snap[key])
                _attach("restore", {"restored": restored})
        stop_unless_refused(not accepted, GM_RECORD, f"Publish with Page Content ({locale.upper()}) empty",
                            evidence, restored=restored)
        content_msgs = [m for m in shown if "page content" in m.lower()] or [
            m for _, m in blocked if "page content" in m.lower()]
        assert applied == "", f"precondition: the editor still holds {applied[:80]!r} after the clear"
        assert refusal or content_msgs, (
            f"no validation error for Page Content ({locale}) = '' "
            f"(visible: {shown}; blocked controls: {blocked})"
        )
        assert status == STATUS_PUBLISHED, f"record status changed to {status!r}"


def _script_injection(page, browser, tc: str, field: str) -> None:
    """`<script>` in a field: stripped/escaped (or refused) -- never executes."""
    payload = "<script>alert(1)</script>"
    block_live_singleton_write(GM_RECORD, f"publish of a <script> payload in {field}")
    _snapshot(page, writes=("content_en" if field == "content" else field,))
    admin = A(page)
    anon_ctx = None
    try:
        with allure.step(f"Enter {payload} in {field} and publish"):
            # An accepted, sanitised save is a valid outcome of this case.
            authoring = _editable(admin.open_record("en"))
            if field == "content":
                admin.set_page_content_html(f"<p>{_marker(tc, 'BODY')}</p>{payload}", "en")
            else:
                authoring.fill_text(field, f"{_marker(tc, 'T')} {payload}")
            admin.submit_publish(authoring)
            refused = bool(admin.refusal_text())
        if refused:
            _attach("note", "save refused outright -- acceptable per the case")
            return
        _drive_published(admin)  # a submit on an Unpublished record stays Unpublished
        if field == "content":
            admin.open_record("en")
            stored = admin.page_content_html("en")
            assert "<script" not in stored.lower(), f"script tag stored verbatim: {stored!r}"
        anon_ctx, public = _anon(browser)
        dialogs = public.watch_dialogs()
        with allure.step("Open the public page as a visitor: the script never runs"):
            shown = _public_shows(public, lambda p: _marker(tc, "") in p.page_text())
            html = public.body_html() if field == "content" else public.title_text()
        assert shown, "the published value never reached the public page"
        assert not dialogs, f"injected script executed on the public page: {dialogs}"
        if field == "content":
            assert "<script" not in html.lower(), "script element rendered in the body"
    finally:
        _close(anon_ctx)


# ---- RBAC helpers -----------------------------------------------------------
def _denied_direct_url(page, browser, tc: str, role: str | None) -> None:
    """Anonymous (role=None) or no-role account opening the edit URL: login /
    denial / not-found, never the form or the record's content."""
    ctx = None
    with allure.step("Read the record's GM Name (admin, read-only) to detect exposure"):
        secret = A(page).open_record("en").field_value(A.LABEL_GM_NAME)
    try:
        if role is None:
            ctx = new_context(browser, use_auth_state=False)
            who_page = ctx.new_page()
        else:
            ctx, who_page = _role_session(browser, role)
        admin = A(who_page)
        with allure.step(f"As {role or 'an anonymous visitor'}, open the GM Message edit URL directly"):
            admin.open_manage_url_raw("en")
            rendered = admin.form_renders_within(20000)
            body = admin.body_text()
            _attach("page shown (wording is a note)", body[:800])
        assert not rendered, "the edit form rendered for an unauthorized user"
        assert secret and secret not in body, "the record's content is exposed to an unauthorized user"
    finally:
        _close(ctx)


def _author_cannot_publish(browser, tc: str, inspect_fields: bool = True) -> None:
    """Author: fields editable (if requested), no direct Publish control on
    the form or the row, status unchanged. Read-only on the record."""
    ctx = None
    try:
        ctx, author_page = _role_session(browser, ROLE_AUTHOR)
        admin = A(author_page)
        with allure.step("As Site Content Author, open the GM Message record"):
            authoring = admin.open_record("en")
            before = authoring.current_status()
            # Live 2026-10-13: on the PUBLISHED record the Author gets an
            # Access Denied note instead of the editing banner ("Only a
            # Content Editor can change a record once it has reached the
            # website"), every field and both submit buttons disabled.
            denied = authoring.access_denied_note()
            _attach("what the Author sees", {"status": before, "access_denied": denied,
                                             "submit controls": authoring.submit_controls_enabled()})
        if inspect_fields:
            assert admin.is_field_editable(A.LABEL_GM_NAME), (
                "FINDING -- the Site Content Author cannot edit the PUBLISHED GM Message record "
                f"(status read {before!r}); the case expects view + update. The product shows: "
                f"{denied or '(no Access Denied note; GM Name not editable)'}"
            )
        with allure.step("Inspect the form for a direct Publish control"):
            form_publish = admin.has_direct_publish_control()
        with allure.step("Inspect the row's workflow actions"):
            admin.open_list("en")
            actions = admin.row_actions()
            _attach("row actions offered to the Author", sorted(actions))
        assert not form_publish, "the Author sees a direct Publish control on the form"
        # 2026-10-13: an offered publish/approve/unpublish row action IS the
        # finding; it is never clicked (user decision 2026-10-13).
        stop_unless_refused(not actions & {"publish", "approve", "unpublish"}, GM_RECORD,
                            "the Author's row workflow actions", sorted(actions))
        # REMOVED 2026-10-13: the former "attempt the Publish row action
        # directly" click. On the Published singleton it proved little (the
        # row `publish` action renders only on Unpublished rows for any role),
        # and a click that could succeed must never be made on 79878. The
        # absent form/row publish controls above carry the denial.
        after = admin.open_record("en").current_status()
        assert after == before, f"status changed from {before!r} to {after!r}"
    finally:
        _close(ctx)


def _author_submits_change(page, browser, tc: str, editor_publishes: bool) -> None:
    """Author edits Page Content and submits -> Pending Review (not live);
    the Editor sees it and (optionally) publishes it live."""
    block_live_singleton_write(GM_RECORD, "Author submit of a Page Content change")
    _snapshot(page, writes=("content_en",))
    marker = _marker(tc, "AUTHOR-EDIT")
    with _gm_end_published(A(page), tc):
        a_ctx = e_ctx = anon_ctx = None
        try:
            # Both role logins happen BEFORE the Author's submit mutates 79878.
            a_ctx, author_page = _role_session(browser, ROLE_AUTHOR)
            e_ctx, editor_page = _role_session(browser, ROLE_EDITOR)
            author = A(author_page)
            with allure.step("As Site Content Author, edit Page Content (EN) and submit"):
                # No Unpublish: an Author has no publishing rights, so it edits
                # the Published record in place and submits it for review.
                authoring = author.open_record("en")
                assert not author.has_direct_publish_control(), "Author sees a direct Publish control"
                assert author.has_publish_submit(), "no Submit for Review control renders for the Author"
                author.set_page_content_html(f"<p>{marker}</p>", "en")
                # The Author's submit stores a Pending Review version of 79878.
                log_live_write(GM_RECORD, "Page Content (EN)", f"<p>{marker}</p>", tc, action="publish",
                               note="Site Content Author Submit for Review (lands Pending Review; "
                                    "re-published in finally)")
                author.submit_publish(authoring)
                status = author.open_record("en").current_status()
            assert status in (STATUS_PENDING_REVIEW, STATUS_DRAFT), (
                f"Author's change landed on {status!r}; expected Pending Review/Draft (not Published)"
            )
            anon_ctx, public = _anon(browser)
            assert not _public_shows(public, lambda p: marker in p.body_text(), timeout=20), (
                "the Author's unpublished change is visible to visitors"
            )
            editor = A(editor_page)
            with allure.step("As Site Content Editor, open the same record"):
                editor.open_record("en")
                seen = editor.page_content_html("en")
            assert marker in seen, "the Editor does not see the Author's pending change"
            if editor_publishes:
                with allure.step("Editor publishes the change"):
                    listing = editor.open_list("en")
                    log_live_write(GM_RECORD, "<workflow>", STATUS_PUBLISHED, tc, action="publish",
                                   note="Site Content Editor approves / publishes the Author's change")
                    if "approve" in editor.row_actions():
                        listing.approve_entry(GM_MESSAGE_ENTRY_CODE, comment=marker)
                    else:
                        editor.submit_publish(editor.open_record("en"))
                    editor.open_record("en").wait_for_status(STATUS_PUBLISHED, timeout=_budget(PUBLISH_WAIT))
                assert _public_shows(public, lambda p: marker in p.body_text()), (
                    "the Editor-published change is not visible to a Public Visitor"
                )
        finally:
            _close(anon_ctx, a_ctx, e_ctx)


# ---- lifecycle helpers --------------------------------------------------------
def _draft_not_public(page, browser, tc: str) -> None:
    """Save as Draft: status Draft; visitors never see the draft value."""
    block_live_singleton_write(GM_RECORD, "unpublish + Save as Draft of Salutation Heading")
    _snapshot(page, writes=(A.LABEL_SALUTATION,))
    admin = A(page)
    marker = _marker(tc, "DRAFT")
    anon_ctx = None
    try:
        with allure.step("Edit Salutation Heading and Save as Draft"):
            authoring = _editable(admin.open_record("en"))
            authoring.fill_text(A.LABEL_SALUTATION, marker)
            status = _save_draft(authoring)
        assert status == STATUS_DRAFT, f"record is {status!r}, expected Draft"
        anon_ctx, public = _anon(browser)
        with allure.step("Open the public page as a visitor"):
            leaked = _public_shows(public, lambda p: marker in p.page_text(), timeout=30)
        assert not leaked, "Draft content is visible on the live site"
    finally:
        _close(anon_ctx)


def _publish_visible(page, browser, tc: str, role: str | None = ROLE_EDITOR) -> None:
    """Publish: status Published and the new value is visible to visitors."""
    block_live_singleton_write(GM_RECORD, "publish of Salutation Heading")
    _snapshot(page, writes=(A.LABEL_SALUTATION,))
    marker = _marker(tc, "LIVE")
    ctx = anon_ctx = None
    try:
        ctx, who = _role_session(browser, role) if role else (None, page)
        admin = A(who)
        with allure.step(f"As {role or 'admin'}, edit Salutation Heading and Publish"):
            authoring = _editable(admin.open_record("en"))
            authoring.fill_text(A.LABEL_SALUTATION, marker)
            status = _publish(admin, authoring)
        assert status == STATUS_PUBLISHED, f"record is {status!r}, expected Published"
        anon_ctx, public = _anon(browser)
        assert _public_shows(public, lambda p: p.salutation_text().strip() == marker), (
            "published content is not visible to a Public Visitor"
        )
    finally:
        _close(anon_ctx, ctx)


def _unpublish_removes(page, browser, tc: str) -> None:
    """Editor Unpublish: off the live site, record still editable."""
    block_live_singleton_write(GM_RECORD, "Editor Unpublish")
    snap = _snapshot(page, writes=(A.LABEL_GM_NAME,))
    ctx = anon_ctx = None
    try:
        ctx, editor_page = _role_session(browser, ROLE_EDITOR)
        admin = A(editor_page)
        with allure.step("As Site Content Editor, Unpublish the Published record"):
            authoring = admin.open_record("en")
            authoring.unpublish_to_edit_as_draft()
            status = admin.open_record("en").current_status()
        assert status != STATUS_PUBLISHED, f"record is still {status!r} after Unpublish"
        anon_ctx, public = _anon(browser)
        name = snap.get(A.LABEL_GM_NAME) or ""
        with allure.step("As a Public Visitor, open the page"):
            gone = _public_shows(public, lambda p: name not in p.page_text())
        assert gone, "unpublished GM Message content is still served on the live site"
        with allure.step("The record stays editable in the CMS"):
            authoring = admin.open_record("en")
            editable = admin.is_field_editable(A.LABEL_GM_NAME) and not authoring.is_save_as_draft_disabled()
        assert editable, "the unpublished record is not editable"
    finally:
        _close(anon_ctx, ctx)


def _preview_url(admin) -> str:
    return admin.open_list("en").row_preview_url_by_code(GM_MESSAGE_ENTRY_CODE)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("CMS authoring workflow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site Content Editor can author, preview, and publish the complete bilingual GM's Message record end-to-end")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_136383
@pytest.mark.traceability("136383")
@allure.label("pbi", "129397")
@allure.label("testcase", "136383")
@GM_GROUP
@pytest.mark.timeout(300)
def test_gm_message_editor_authors_previews_publishes_end_to_end(page, browser, tmp_path):
    # Every bilingual field + both images + alt text, as Site Content Editor.
    values = {
        A.LABEL_PAGE_TITLE: "QCTEST-136383 General Manager's Message",
        A.LABEL_SALUTATION: "QCTEST-136383 Dear members and visitors,",
        A.LABEL_GM_NAME: "QCTEST-136383 Ahmed Al-Kuwari",
        A.LABEL_DESIGNATION: "QCTEST-136383 Acting General Manager",
        A.LABEL_CLOSING: "QCTEST-136383 Best Regards,",
        A.LABEL_ALT_TEXT: "QCTEST-136383 General Manager portrait",
        A.LABEL_PAGE_TITLE + AR: "QCTEST-136383 رسالة المدير العام",
        A.LABEL_SALUTATION + AR: "QCTEST-136383 أعزاءنا الأعضاء والزوار،",
        A.LABEL_GM_NAME + AR: "QCTEST-136383 أحمد الكواري",
        A.LABEL_DESIGNATION + AR: "QCTEST-136383 المدير العام بالإنابة",
        A.LABEL_CLOSING + AR: "QCTEST-136383 مع خالص التقدير،",
        A.LABEL_ALT_TEXT + AR: "QCTEST-136383 صورة المدير العام",
    }
    content = {"en": "<p>QCTEST-136383 message body.</p>", "ar": "<p>QCTEST-136383 نص الرسالة.</p>"}
    block_live_singleton_write(GM_RECORD, "unpublish, save draft and publish every field")
    _snapshot(page, tmp_path, files=(A.LABEL_HERO, A.LABEL_PORTRAIT),
                     writes=(*values, "content_en", "content_ar"))
    ctx = anon_ctx = None
    try:
        ctx, editor_page = _role_session(browser, ROLE_EDITOR)
        admin = A(editor_page)
        with allure.step("Enter every EN+AR field and upload Hero Banner + GM Portrait"):
            authoring = _editable(admin.open_record("en"))
            for label, value in values.items():
                authoring.fill_text(label, value)
            for loc, html in content.items():
                admin.set_page_content_html(html, loc)
            authoring.upload_file(A.LABEL_HERO, _fixture(tmp_path, "qctest-hero.jpg", 400 * 1024))
            authoring.upload_file(A.LABEL_PORTRAIT, _fixture(tmp_path, "qctest-portrait.png", 300 * 1024))
            accepted = {label: authoring.field_value(label) for label in values}
        assert accepted == values, f"fields did not accept the entered values: {accepted}"
        with allure.step("Save as Draft, then Preview: content shown, still unpublished"):
            _save_draft(authoring)
            preview = (authoring.open(_preview_url(admin)) or authoring).rendered_body_text()
            status = admin.open_record("en").current_status()
        assert values[A.LABEL_SALUTATION] in preview, "Preview does not render the entered content"
        assert status != STATUS_PUBLISHED, f"record went live before Publish ({status!r})"
        with allure.step("Publish"):
            status = _publish(admin, admin.open_record("en"))
        assert status == STATUS_PUBLISHED, f"record is {status!r} after Publish"
        anon_ctx, public = _anon(browser)
        with allure.step("Public Visitor sees all content (EN, then AR)"):
            en_ok = _public_shows(public, lambda p: all(values[l] in p.page_text() for l in (
                A.LABEL_PAGE_TITLE, A.LABEL_SALUTATION, A.LABEL_GM_NAME, A.LABEL_DESIGNATION, A.LABEL_CLOSING)))
            en_alt = public.portrait_alt_text()
            ar_ok = _public_shows(public, lambda p: values[A.LABEL_GM_NAME + AR] in p.page_text(), "ar")
        assert en_ok, "not all entered EN content is visible live"
        assert ar_ok, "the entered AR content is not visible live"
        assert en_alt == values[A.LABEL_ALT_TEXT], f"portrait alt is {en_alt!r}"  # VERIFY-LIVE: alt applies to portrait
    finally:
        _close(anon_ctx, ctx)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Draft/Published visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Draft GM's Message content is not visible to a Public Visitor")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_136384
@pytest.mark.traceability("136384")
@allure.label("pbi", "129397")
@allure.label("testcase", "136384")
@GM_GROUP
@pytest.mark.timeout(300)
def test_gm_message_draft_content_not_visible_to_visitor(page, browser, tmp_path):
    _draft_not_public(page, browser, "136384")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Publish / Unpublish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Unpublishing the GM's Message page removes it from the live site")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_136385
@pytest.mark.traceability("136385")
@allure.label("pbi", "129397")
@allure.label("testcase", "136385")
@GM_GROUP
@pytest.mark.timeout(300)
def test_gm_message_unpublish_removes_from_live_site(page, browser, tmp_path):
    _unpublish_removes(page, browser, "136385")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Entering the GM Name once updates both the Portrait Caption and the Signature Block identically")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_136386
@pytest.mark.traceability("136386")
@allure.label("pbi", "129397")
@allure.label("testcase", "136386")
@GM_GROUP
@pytest.mark.timeout(300)
def test_gm_message_name_edit_propagates_to_both_locations(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "publish of GM Name / GM Designation")
    _snapshot(page, writes=(A.LABEL_GM_NAME, A.LABEL_DESIGNATION))
    admin = A(page)
    name, desig = "Ahmed Al-Kuwari", "Acting General Manager"
    anon_ctx = None
    try:
        with allure.step("Enter GM Name / GM Designation once and Publish"):
            authoring = _editable(admin.open_record("en"))
            authoring.fill_text(A.LABEL_GM_NAME, name)
            authoring.fill_text(A.LABEL_DESIGNATION, desig)
            accepted = (authoring.field_value(A.LABEL_GM_NAME), authoring.field_value(A.LABEL_DESIGNATION))
            status = _publish(admin, authoring)
        assert accepted == (name, desig), f"values not accepted: {accepted}"
        assert status == STATUS_PUBLISHED, f"record is {status!r} after Publish"
        anon_ctx, public = _anon(browser)
        with allure.step("Public page: Portrait Caption and Signature Block"):
            live = _public_shows(public, lambda p: p.portrait_name_text().strip() == name)
            caption = (public.portrait_name_text().strip(), public.portrait_designation_text().strip())
            signature = (public.signature_name_text().strip(), public.signature_designation_text().strip())
        assert live and caption == (name, desig), f"Portrait Caption shows {caption}"
        assert signature == caption, f"Signature Block {signature} differs from Portrait Caption {caption}"
    finally:
        _close(anon_ctx)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Editing GM Name on an already-published page updates both the Portrait Caption and Signature Block only after republish")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136453
@pytest.mark.traceability("136453")
@allure.label("pbi", "129397")
@allure.label("testcase", "136453")
@GM_GROUP
@pytest.mark.timeout(300)
def test_gm_message_name_edit_pending_then_republish_updates_both(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "precondition publish of GM Name")
    _snapshot(page, writes=(A.LABEL_GM_NAME,))
    admin = A(page)
    old, new = "Ahmed Al-Kuwari", "Khalid Al-Emadi"
    anon_ctx = None
    try:
        anon_ctx, public = _anon(browser)
        both = lambda value: (lambda p: p.portrait_name_text().strip() == value  # noqa: E731
                              and p.signature_name_text().strip() == value)
        with allure.step(f"Precondition: publish GM Name {old!r}; both locations show it"):
            authoring = _editable(admin.open_record("en"))
            authoring.fill_text(A.LABEL_GM_NAME, old)
            _publish(admin, authoring)
        assert _public_shows(public, both(old)), f"precondition: live page does not show {old!r} in both places"
        with allure.step(f"Edit GM Name to {new!r} and save without publishing"):
            authoring = _editable(admin.open_record("en"))
            authoring.fill_text(A.LABEL_GM_NAME, new)
            _save_draft(authoring)
        assert not _public_shows(public, lambda p: new in p.page_text(), timeout=30), (
            "the unpublished name reached the live page"
        )
        with allure.step("Publish"):
            status = _publish(admin, admin.open_record("en"))
        assert status == STATUS_PUBLISHED, f"record is {status!r} after Publish"
        assert _public_shows(public, both(new)), (
            f"Portrait Caption and Signature Block do not both show {new!r} after republish"
        )
        assert old not in public.page_text(), f"a stale {old!r} remains on the page"
    finally:
        _close(anon_ctx)


# ---------------------------------------------------------------------------
# Remaining Control_Panel-tagged cases for PBI 129397 (142 cases, sourced
# verbatim from review_test_coverage(129397)'s Control_Panel-tagged subset).
#
# BLOCKED this session -- see _CMS_LOGIN_BLOCKED below for the concrete,
# live-reproduced reason. Every case is still registered here (never
# silently dropped) as an explicit skip stub carrying its own tc_<id> +
# pbi_129397 + control_panel markers, per automation-standards.md's Result
# Integrity rule. Re-attempt once qcdev's login path is confirmed clear of
# the license/connection-limit interstitial.
# ---------------------------------------------------------------------------

_CMS_LOGIN_BLOCKED = (
    "CMS admin authoring workflow blocked this session: "
    "qcdev.ihorizons.com's \"developer mode connection limit\" "
    "interstitial (/c/portal/license_activation) intercepted the login "
    "request and did not clear after following its own reset link "
    "(confirmed live, 2026-08-25: attempted a fresh Playwright login via "
    "CmsLoginPage's real selectors, reset-link click timed out, login "
    "form never rendered). No authenticated admin session could be "
    "established to reach the GM's Message custom widget's edit form, so "
    "no real locators exist for it -- per the one-pass/real-locators "
    "rule, none are invented here. This is the same unresolved qcdev dev- "
    "mode connection-limit issue flagged in "
    "cms/pages/control_panel/login_page.py's docstring, not a new gap "
    "introduced by this batch. "
)

@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Editor can create, edit, preview, publish, and unpublish the GM's Message record (ADO-135445)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_135445
@pytest.mark.traceability("135445")
@allure.label("pbi", "129397")
@allure.label("testcase", "135445")
@GM_GROUP
@pytest.mark.timeout(300)
def test_site_content_editor_can_create_edit_preview_publish_and_135445(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Editor unpublish / edit / publish / unpublish")
    _snapshot(page, writes=(A.LABEL_SALUTATION,))
    marker = _marker("135445", "EDITOR")
    ctx = anon_ctx = None
    try:
        ctx, editor_page = _role_session(browser, ROLE_EDITOR)
        admin = A(editor_page)
        with allure.step("As Site Content Editor, open the record (edit mode)"):
            authoring = _editable(admin.open_record("en"))
            assert admin.is_field_editable(A.LABEL_SALUTATION), "record did not open in edit mode"
        with allure.step("Edit Salutation Heading, save the draft and Preview it"):
            authoring.fill_text(A.LABEL_SALUTATION, marker)
            _save_draft(authoring)
            preview_text = (authoring.open(_preview_url(admin)) or authoring).rendered_body_text()
        assert marker in preview_text, "Preview does not render the edited content"
        with allure.step("Publish"):
            status = _publish(admin, admin.open_record("en"))
        assert status == STATUS_PUBLISHED, f"record is {status!r} after Publish"
        anon_ctx, public = _anon(browser)
        assert _public_shows(public, lambda p: p.salutation_text().strip() == marker), "publish not live"
        with allure.step("Unpublish"):
            admin.open_record("en").unpublish_to_edit_as_draft()
        assert _public_shows(public, lambda p: marker not in p.page_text()), (
            "the page is still served on the live site after Unpublish"
        )
    finally:
        _close(anon_ctx, ctx)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author can view and update assigned GM's Message content but cannot publish directly (ADO-135446)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_135446
@pytest.mark.traceability("135446")
@allure.label("pbi", "129397")
@allure.label("testcase", "135446")
@GM_GROUP
@pytest.mark.timeout(300)
def test_site_content_author_can_view_and_update_assigned_gms_135446(page, browser, tmp_path):
    # Author: editable + no direct Publish, then the save lands short of
    # Published (Draft or Pending Review -- the account decides the path).
    _author_cannot_publish(browser, "135446")
    _author_submits_change(page, browser, "135446", editor_publishes=False)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author attempting to force a Publish action via a direct workflow call is denied with the standard Access Denied message (ADO-135447)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135447
@pytest.mark.traceability("135447")
@allure.label("pbi", "129397")
@allure.label("testcase", "135447")
@GM_GROUP
@pytest.mark.timeout(300)
def test_site_content_author_attempting_to_force_a_publish_action_135447(page, browser, tmp_path):
    _author_cannot_publish(browser, "135447", inspect_fields=False)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Public Visitor cannot access the GM's Message CMS edit URL directly (forced browsing) (ADO-135448)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_135448
@pytest.mark.traceability("135448")
@allure.label("pbi", "129397")
@allure.label("testcase", "135448")
@GM_GROUP
@pytest.mark.timeout(300)
def test_public_visitor_cannot_access_the_gms_message_cms_edit_135448(page, browser, tmp_path):
    _denied_direct_url(page, browser, "135448", None)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a logged-in CMS user without any assigned role on the GM's Message content receives Access Denied when opening the record (ADO-135450)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135450
@pytest.mark.traceability("135450")
@allure.label("pbi", "129397")
@allure.label("testcase", "135450")
@GM_GROUP
@pytest.mark.timeout(300)
def test_loggedin_cms_user_without_any_assigned_role_on_the_135450(page, browser, tmp_path):
    _denied_direct_url(page, browser, "135450", ROLE_NO_ROLE)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("CMS authoring workflow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Editor can author, preview, and publish the complete bilingual GM's Message record end-to-end (ADO-135453)")
@allure.label("pbi", "129397")
@allure.label("testcase", "135453")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135453
@pytest.mark.xdist_group("gm_message_79878")
def test_site_content_editor_can_author_preview_and_publish_the_135453(page, browser):
    """ADO-135453. NOTE (2026-08-31): the `_CMS_LOGIN_BLOCKED` condition this
    module's other stubs still carry was diagnosed and is NOT a login/
    credential problem — see GmMessageAdminPage's module docstring. Going
    through the real framework (CmsLoginPage + BasePage, which already
    dismiss the site's announcement overlay on every navigation) logs in
    cleanly; the earlier block was an artifact of a raw, non-framework probe
    script that bypassed that handling. Only THIS case is unblocked here —
    the other 140+ stubs in this module were sourced from a different,
    wider batch and are left untouched (out of this task's scope).

    CORRECTED 2026-09-07 (per standards.md's "Object Authoring Is the Only
    Path for Content Operations"): this test previously
    drove Status via Content & Data's generic `publicationStatus` combobox +
    Save button. That is NOT the correct/supported lifecycle surface — a
    genuinely different, richer Object Authoring mechanism exists
    (`manage-general-manager-message`, confirmed live 2026-09-07) with its
    own "Save as Draft" / "Submit for Publishing" commit actions and an
    "Unpublish to edit as draft" button. This test now drives the entire
    author -> preview -> publish flow through `ObjectAuthoringPage`
    (GmMessageAdminPage.open_object_authoring_form()), never Content & Data,
    for any step that changes Draft/Publish state.

    Scope notes, disclosed per automation-standards.md's Result Integrity
    rule (never invent a selector/assertion to force green):
      - GM's Message is a SINGLETON record (ID 79878 / entry code
        QCDEMO-129397-general-managers-message) — there is exactly one live
        row, also asserted verbatim (name/salutation/body) by several
        already-passing tests in test_gm_message_web.py. Per
        cms-profile.md's TEST_OWNED policy (a dedicated row reset to a
        known baseline, not "restore whatever it was"), this test captures
        the record's CURRENT field values as that baseline, edits with
        concrete QCTEST-prefixed bilingual data mirroring the case, and
        ALWAYS restores the captured baseline in a `finally` block — never
        leaving the shared singleton mutated even on failure.
      - The record starts Approved/Published — Object Authoring's own
        editing banner confirms Save as Draft is unavailable on an approved
        entry until "Unpublish to edit as draft" is clicked first. Step 1's
        authoring therefore goes: open entry -> Unpublish to edit as draft
        -> fill AR fields -> fill EN fields -> Submit for Publishing (the
        real "Publish" commit on this surface).
      - Hero Banner / GM Portrait / Signature Avatar are NOT re-uploaded —
        same disclosed rationale as before (no confirmed download-then-
        reupload round trip exists to safely restore the original binary;
        cms-profile.md's Test-Data Policy prohibits an unrecoverable
        overwrite). This test instead asserts the images already present on
        the record are valid, non-empty uploads via
        GmMessageAdminPage.has_file_uploaded() through the Content & Data
        surface (a pure read, not a lifecycle action, so using that surface
        here is fine).
      - Object Authoring's own right-hand Preview pane / row Preview link
        (see ObjectAuthoringPage's module docstring) is the real, dedicated
        Preview control this surface exposes — Step 2 ("Preview matches
        entered data") is verified here by reopening the record via
        `open_entry_by_code()` immediately after Submit for Publishing and
        reading the field values back, the same close proxy this test
        already used, now on the correct surface.
      - PUBLIC-PAGE-ANONYMOUS-CONTEXT: Step 4's public-page reads (both EN
        and AR) run in a dedicated, fresh, logged-out browser context
        (never the CMS-authenticated `page`), matching this project's
        established convention (see test_home_featured_event_control_panel.py)
        so they reflect a real anonymous visitor rather than a
        still-authenticated CMS session.
    """
    from core.web.browser import new_context

    admin = GmMessageAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    gm_page = GmMessagePage(anon_page)

    qctest_name_en = "QCTEST-135453 Mr. Ali Saeed Busherbak Al Mansoori"
    qctest_salutation_en = "QCTEST-135453 Dear members and visitors,"
    qctest_closing_en = "QCTEST-135453 Best Regards,"
    # Arabic QCTEST values keep the ASCII "QCTEST-135453" marker (still
    # searchable/greppable for cleanup) prefixed onto real Arabic text so the
    # field is genuinely exercised in AR, not just re-saving the EN string.
    qctest_name_ar = "QCTEST-135453 السيد علي سعيد بوشهبك المنصوري"
    qctest_salutation_ar = "QCTEST-135453 أعزاءنا الأعضاء والزوار،"

    with allure.step("Open the GM's Message record via Object Authoring"):
        authoring = admin.open_object_authoring_form()

    # Assert: Hero Banner / GM Portrait Image already hold real, valid
    # uploads (the safe half of Step 1's image-upload guarantee — see
    # docstring for why these are not re-uploaded). Read via the Content &
    # Data surface's own field-presence check (a pure read, not a lifecycle
    # action) BEFORE any unsaved Object Authoring edit begins — navigating
    # away mid-edit (even for a pure read on a different surface) discards
    # the in-browser unsaved form state, confirmed live this session (an
    # earlier version of this test lost its just-typed GM Name edit this
    # way, re-reading the OLD value back after this exact navigation).
    admin.open_gm_message_edit_form()
    assert admin.has_file_uploaded("GM Portrait Image")
    assert admin.has_file_uploaded("Hero Banner")

    try:
        authoring = admin.open_object_authoring_form()

        with allure.step('Unpublish to edit as draft (this record starts Approved — Save as Draft is disabled until unpublished)'):
            block_live_singleton_write(GM_RECORD, "unpublish, edit EN/AR fields and publish")
            authoring.unpublish_to_edit_as_draft()

        assert authoring.current_status() == "Draft"

        with allure.step("Enter AR field values (GM Name, Salutation Heading)"):
            authoring.fill_text("GM Name — العربية", qctest_name_ar)
            authoring.fill_text("Salutation Heading — العربية", qctest_salutation_ar)

        # Assert: AR fields accept the new input.
        assert authoring.field_value("GM Name — العربية") == qctest_name_ar
        assert authoring.field_value("Salutation Heading — العربية") == qctest_salutation_ar

        with allure.step("Enter EN field values"):
            authoring.fill_text("GM Name", qctest_name_en)
            authoring.fill_text("Salutation Heading", qctest_salutation_en)
            authoring.fill_text("Signature Closing Text", qctest_closing_en)

        # Assert: EN fields accept the new input (Step 1's "all fields accept input").
        assert authoring.field_value("GM Name") == qctest_name_en
        assert authoring.field_value("Salutation Heading") == qctest_salutation_en
        assert authoring.field_value("Signature Closing Text") == qctest_closing_en

        with allure.step("Submit for Review (this surface's real Publish action)"):
            authoring.submit_for_publishing()

        # Assert: Step 3 — Publish succeeds, status is Approved again.
        assert authoring.current_status() == STATUS_PUBLISHED

        with allure.step("Reopen the record and read EN + AR field values back (Preview/persistence check)"):
            authoring = admin.open_object_authoring_form()
            reloaded_name_en = authoring.field_value("GM Name")
            reloaded_name_ar = authoring.field_value("GM Name — العربية")
            reloaded_salutation_en = authoring.field_value("Salutation Heading")
            reloaded_salutation_ar = authoring.field_value("Salutation Heading — العربية")
            reloaded_closing_en = authoring.field_value("Signature Closing Text")

        # Assert: Publish persisted exactly what was entered in BOTH languages
        # (Step 2's "Preview matches entered data in both languages").
        assert reloaded_name_en == qctest_name_en
        assert reloaded_salutation_en == qctest_salutation_en
        assert reloaded_closing_en == qctest_closing_en
        assert reloaded_name_ar == qctest_name_ar
        assert reloaded_salutation_ar == qctest_salutation_ar

        with allure.step("Load the public GM's Message page as a visitor (EN) and confirm the authored content is live"):
            gm_page.open_gm_message(locale="en")

        # Assert: Step 4 (EN) — the public page reflects what was authored.
        assert gm_page.signature_name_text() == qctest_name_en
        assert gm_page.salutation_text() == qctest_salutation_en

        with allure.step("Load the public GM's Message page as a visitor (AR) and confirm the authored content is live"):
            gm_page.open_gm_message(locale="ar")

        # Assert: Step 4 (AR) — the public page reflects what was authored,
        # in Arabic, with RTL layout.
        dir_attr = anon_page.evaluate("() => document.documentElement.getAttribute('dir')")
        assert dir_attr == "rtl"
        assert gm_page.signature_name_text() == qctest_name_ar
        assert gm_page.salutation_text() == qctest_salutation_ar
    finally:
        # No per-test restore: 79878 is restored ONCE at module end by the
        # `_singleton_baseline` fixture (user decision 2026-10-12).
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 — cleanup must never mask the real result
            pass


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Editor is blocked from publishing when the Arabic Page Title is missing (ADO-135454)")
@allure.label("pbi", "129397")
@allure.label("testcase", "135454")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135454
@pytest.mark.xdist_group("gm_message_79878")
def test_site_content_editor_is_blocked_from_publishing_when_the_135454(page):
    """ADO-135454. Same baseline-capture -> try -> assert -> finally-restore
    structure as tc_135453/tc_135457 against the SAME shared singleton
    record (79878).

    CONFIRMED PRODUCT DEFECT (reported by the QA Manager from a live manual
    repro, 2026-09-03): clearing the Arabic Page Title and Saving does NOT
    block the save as the case requires -- it succeeds, and the Arabic Page
    Title field is silently auto-filled with the English Page Title's own
    content instead of being left blank or rejected. That is worse than the
    case's own framing (a validation gate) and is asserted here as the
    case's literal, correct-behavior expectation (Publish/Save is blocked,
    record remains at its prior baseline) -- this test is expected to FAIL
    loudly against the live defect rather than being written to match the
    defect as if it were spec (automation-standards.md Result Integrity).

    Scope note: only the Arabic Page Title is cleared (the case's own Step 1
    names only this field); every other field is left untouched.
    """
    admin = GmMessageAdminPage(page)

    with allure.step("Open the GM's Message record in the Control Panel"):
        admin.open_gm_message_edit_form()

    from core.utils.reporting import attach_screenshot
    from config.settings import settings

    with allure.step("Clear the Arabic Page Title, leave every other field as-is, and click Save"):
        admin.switch_field_to_arabic("Page Title")
        admin.fill_text_field(admin.PAGE_TITLE, "")
        admin.switch_field_to_english("Page Title")
        # Confirmed live defect (docstring): this Save is NOT refused -- it
        # succeeds and auto-fills the AR title. A click known to succeed on
        # the real record is never made (user decision 2026-10-13).
        block_live_singleton_write(
            GM_RECORD, "Save with an empty AR Page Title -- known to succeed (confirmed defect)")
        admin.save()

    with allure.step("Capture bug evidence #1: form state immediately after Save (no validation error surfaced)"):
        attach_screenshot(page.screenshot(full_page=True), "135454", settings.project_name)

    with allure.step("Capture bug evidence #2: reopen the record and show the Arabic Page Title was silently auto-filled instead of blocked/left blank"):
        admin.open_gm_message_edit_form()
        admin.switch_field_to_arabic("Page Title")
        attach_screenshot(page.screenshot(full_page=True), "135454", settings.project_name)
        reloaded_title_ar = admin.field_value(admin.PAGE_TITLE)
        admin.switch_field_to_english("Page Title")

    # Correct-behavior assertion (case's Step 1): Publish/Save must be
    # blocked with the bilingual gate's error message, and the record
    # must remain unchanged (not silently saved with a blank/auto-filled
    # Arabic title). Expected to FAIL against the confirmed live defect
    # above -- report as a product bug, not an automation bug, once
    # this failure is observed.
    assert admin.is_save_error_shown() and reloaded_title_ar == "", (
        "Expected the bilingual publish gate to block Save when the "
        "Arabic Page Title is blank, but no validation error was shown "
        "at all -- confirmed live defect: the field is instead silently "
        f"auto-filled with {reloaded_title_ar!r} (the English Page "
        "Title's own content) rather than being left blank or rejected."
    )


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that unpublishing the GM's Message page removes it from the live website while the record remains editable in CMS (ADO-135456)")
@allure.label("pbi", "129397")
@allure.label("testcase", "135456")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129397
@pytest.mark.tc_135456
@pytest.mark.xdist_group("gm_message_79878")
def test_unpublishing_the_gms_message_page_removes_it_from_the_135456(page):
    """ADO-135456. Same baseline-capture -> try -> assert -> finally-restore
    structure as tc_135453/tc_135457/tc_135454 against the SAME shared
    singleton record (79878).

    Disclosed mechanism substitution (GmMessageAdminPage's own module
    docstring): this form has no separate "Unpublish" button -- the Status
    field IS the publish/unpublish control (Published/Draft). Step 1 is
    therefore scripted as select_status("Draft") + Save, the confirmed real
    mechanism, not a literal "Unpublish" click that does not exist here.

    Disclosed, expected-to-FAIL assertion for Step 2: the case's literal
    expectation is that the public page becomes a 404/redirect once
    unpublished. tc_135457 (this same module, same shared record) already
    confirmed live that the product instead renders the page shell normally
    with the content area BLANK for a non-Published record, not a 404/
    redirect. Per Result Integrity, this test asserts the case's own literal
    wording rather than silently substituting the known real behavior --
    a failure here reproduces that same already-confirmed defect, it is not
    a new automation bug.
    """
    admin = GmMessageAdminPage(page)
    gm_page = GmMessagePage(page)

    with allure.step("Open the GM's Message record in the Control Panel"):
        admin.open_gm_message_edit_form()

    with allure.step('As Editor, open the Published record and click Unpublish (Status -> "Draft" + Save, the confirmed real mechanism)'):
        admin.select_status("Draft")
        block_live_singleton_write(GM_RECORD, "Status -> Draft + Save (unpublish)")
        admin.save()

    # Assert: Step 1 -- status changes to Unpublished (Draft) with no
    # validation error.
    assert not admin.is_save_error_shown(), admin.save_error_text()
    assert admin.status_value() == "Draft"

    with allure.step("As a visitor, navigate to the page URL"):
        from config.settings import web_url

        target_url = web_url(GM_MESSAGE_PATH, locale="en")
        response = page.goto(target_url)

    # Assert: Step 2 -- case's literal expectation (404/redirect).
    # EXPECTED TO FAIL against the confirmed-live defect documented
    # above (page renders 200 with a blank content area instead).
    status_code = response.status if response else None
    redirected = bool(response) and response.url != target_url
    assert status_code == 404 or redirected or status_code in (301, 302, 303, 307, 308), (
        "AZDO (see tc_135457, same confirmed defect): unpublishing "
        "record 79878 should make the public page 404/redirect, but it "
        f"instead returned status {status_code!r} at the same URL with "
        "the content area rendered blank rather than being taken down."
    )

    with allure.step("As Editor, reopen the record in CMS"):
        admin.open_gm_message_edit_form()

    # Assert: Step 3 -- content is still present and editable.
    assert admin.field_value(admin.GM_NAME) != ""


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Draft/Published visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that Draft content saved but not yet published is never visible on the public website (ADO-135457)")
@allure.label("pbi", "129397")
@allure.label("testcase", "135457")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129397
@pytest.mark.tc_135457
# Added 2026-10-12: this case mutates 79878 but carried no group, so under
# --dist loadgroup it could run beside the module restore on another worker.
@GM_GROUP
def test_draft_content_saved_but_not_yet_published_is_never_135457(page, browser):
    """ADO-135457. Modeled closely on
    test_site_content_editor_can_author_preview_and_publish_the_135453's
    baseline-capture -> try -> assert -> finally-restore structure against
    the SAME shared singleton record (79878 / entry code
    QCDEMO-129397-general-managers-message).

    CORRECTED 2026-09-07 (per standards.md's "Object Authoring Is the Only
    Path for Publish/Unpublish/Draft/Preview Actions" AND "Draft/Unpublish
    Public-Visibility Checks — Mandatory Logged-Out Context"): this test
    previously drove the Draft save via Content & Data's `publicationStatus`
    combobox + generic Save button, and its prior "renders blank" finding
    was itself reached partly through that wrong navigation path — per the
    standard's own instruction to re-verify rather than treat a
    wrong-surface finding as final. This session's re-verification through
    the REAL, supported Object Authoring surface
    (`manage-general-manager-message` -> "Unpublish to edit as draft" ->
    edit -> "Save as Draft", never "Submit for Publishing") produced a
    DIFFERENT, reproducible result: the public page does NOT render blank —
    it renders the DRAFT TEXT ITSELF. That is a confirmed, real product
    defect (draft/unpublished content leaking directly to an anonymous
    public visitor), not the earlier "blank content" symptom, which was a
    test/navigation artifact of driving the wrong surface.

    This test now asserts the CORRECT, spec-required behavior — a public
    visitor must never see Draft/unpublished content at all (per this
    project's documented business rule) — and is EXPECTED TO FAIL against
    the live, confirmed defect (draft content visible to the public) rather
    than being written to match the defect as if it were spec
    (automation-standards.md's Result Integrity rule).

    Draft-mechanism confirmation (Object Authoring, confirmed live
    2026-09-07 via Playwright MCP against qcdev, existing authenticated
    session): opening the Approved singleton record's edit form
    (`manage-general-manager-message?editEntry=QCDEMO-129397-general-managers-message`)
    shows an "Unpublish to edit as draft" button (native `confirm()` dialog
    on click, per ObjectAuthoringPage's own convention); after unpublishing,
    "Save as Draft" becomes enabled and is the correct "saved as Draft, not
    yet published" action for this case's Step 1 — "Submit for Publishing"
    is deliberately NEVER clicked in this test's main flow (that would
    publish the QCTEST text, defeating the point of the case).

    Scope notes (same disclosed-substitution pattern as tc_135453):
      - Only the Salutation Heading (EN) field is edited (the case's own
        Step 1 names only "the salutation heading text"), keeping the
        mutation minimal against the shared singleton.
      - Step 2 is verified on the EN public page only (the case does not
        call out AR-specific behavior), reusing GmMessagePage.salutation_text()
        already proven live by tc_135453.
      - Baseline capture/restore covers the Salutation Heading value AND the
        lifecycle Status (captured BEFORE any change, restored in `finally`
        regardless of pass/fail — Submit for Publishing IS used in the
        teardown to return the record to its Approved/Published baseline)
        so the shared record is never left in Draft or holding the QCTEST
        text.
      - PUBLIC-PAGE-ANONYMOUS-CONTEXT: Step 2's public-page reads (the
        pre-change control read and the post-Draft-save read) run in a
        dedicated, fresh, logged-out browser context (never the
        CMS-authenticated `page`), matching this project's established
        convention (see test_home_featured_event_control_panel.py) so they
        reflect a real anonymous visitor rather than a still-authenticated
        CMS session.
    """
    from core.web.browser import new_context

    admin = GmMessageAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    gm_page = GmMessagePage(anon_page)

    qctest_draft_salutation_en = "QCTEST-135457 Draft-only salutation, not yet published,"

    with allure.step("Open the GM's Message record via Object Authoring"):
        authoring = admin.open_object_authoring_form()

    with allure.step("Read the currently PUBLISHED salutation from the public page (pre-change control), fresh logged-out context"):
        gm_page.open_gm_message(locale="en")
        published_salutation_before = gm_page.salutation_text()

    try:
        with allure.step('As Editor, unpublish to edit as draft, edit the Salutation Heading, and Save as Draft (never Submit for Review)'):
            block_live_singleton_write(GM_RECORD, "unpublish + Save as Draft of Salutation Heading")
            authoring.unpublish_to_edit_as_draft()
            authoring.fill_text("Salutation Heading", qctest_draft_salutation_en)
            authoring.save_as_draft()

        # CONFIRMED LIVE 2026-09-07: `save_as_draft()`'s click navigates the
        # page to a `?previewEntry=...` URL (not `?editEntry=...`), where
        # `field_value()`'s same-named textbox no longer resolves the same
        # way — a bare read right after `save_as_draft()` returns "" even
        # though the value WAS persisted. Reopening the entry via
        # `open_entry_by_code()` (the confirmable, non-in-page-state read
        # this module already established for the Content & Data path) is
        # the correct way to verify the persisted value/status here too.
        authoring = admin.open_object_authoring_form()

        # Assert: Step 1 -- the record saves as Draft with the new
        # salutation, via the confirmed-real Object Authoring mechanism.
        assert authoring.current_status() == "Draft"
        assert authoring.field_value("Salutation Heading") == qctest_draft_salutation_en

        with allure.step("As a visitor, reload the public GM's Message page (fresh logged-out context)"):
            gm_page.open_gm_message(locale="en")

        # CORRECTED assertion (2026-09-07): the business rule is "Draft/
        # Unpublished content is never visible publicly" — assert the
        # public page does NOT show the draft text. This is the correct,
        # spec-required expectation and is EXPECTED TO FAIL against the
        # confirmed live defect (the draft salutation IS what renders
        # publicly — see docstring for the live repro via Object
        # Authoring's "Unpublish to edit as draft" + "Save as Draft" path,
        # read back through a fresh anonymous browser context).
        current_public_salutation = gm_page.salutation_text()
        assert current_public_salutation != qctest_draft_salutation_en, (
            "CONFIRMED PRODUCT DEFECT: the public GM's Message page shows "
            f"the unpublished Draft salutation text ({qctest_draft_salutation_en!r}) "
            "directly to an anonymous visitor while the record is saved as "
            "Draft (unpublished) via Object Authoring's real 'Unpublish to "
            "edit as draft' + 'Save as Draft' mechanism — never Submit for Review. This violates the documented business rule that "
            "Draft/Unpublished content is never visible publicly. Read via "
            "a fresh, logged-out browser context (never the CMS-authenticated "
            "session), confirming this is a real anonymous-visitor-facing "
            "leak, not a CMS-preview artifact."
        )
    finally:
        # No per-test restore: 79878 is restored ONCE at module end by the
        # `_singleton_baseline` fixture (user decision 2026-10-12).
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 — cleanup must never mask the real result
            pass


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that updating the GM Name field once and republishing updates both the portrait caption and the signature block consistently (ADO-135458)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.dataintegrity
@pytest.mark.uat
@pytest.mark.pbi_129397
@pytest.mark.tc_135458
@pytest.mark.xdist_group("gm_message_79878")
@pytest.mark.timeout(300)
def test_updating_the_gm_name_field_once_and_republishing_updates_135458(page, browser):
    """ADO-135458. Single-source-of-truth acceptance point: the GM Name field
    feeds both the public Portrait Caption and the Signature Block.

    P1/P2 RERUN 2026-10-13 (user decision): migrated off the retired
    Content & Data form (CLAUDE.md #4) onto Object Authoring, through the
    module's own logged helpers -- `_editable` (row Unpublish, logged) and
    `_publish` (form submit + documented transitions to Published, logged).
    The public check uses a fresh logged-out context (CLAUDE.md #9). Runs
    only with QC_ALLOW_LIVE_SINGLETON_WRITES=1 (else NOT APPLICABLE); 79878
    is re-published in `finally`; nothing is deleted."""
    block_live_singleton_write(GM_RECORD, "publish of a new GM Name")
    _snapshot(page, writes=(A.LABEL_GM_NAME,))
    admin = A(page)
    qctest_name_en = "QCTEST-135458 Mr. Ali Saeed Busherbak Al Mansoori"
    anon_ctx = None
    with _gm_end_published(admin, "135458"):
        try:
            with allure.step("As Editor, open the Published record and change the GM Name field to a new value"):
                authoring = _editable(admin.open_record("en"))
                authoring.fill_text(A.LABEL_GM_NAME, qctest_name_en)
                accepted = authoring.field_value(A.LABEL_GM_NAME)
            # Assert: Step 1 -- the field accepts the new value.
            assert accepted == qctest_name_en, f"GM Name reads {accepted!r} after entry"
            with allure.step("Publish the change"):
                status = _publish(admin, authoring)
            # Assert: Step 2 -- the save went through (record Published again).
            assert status == STATUS_PUBLISHED, f"record is {status!r} after Publish"
            anon_ctx, public = _anon(browser)
            with allure.step("As a visitor, reload the public page"):
                live = _public_shows(public, lambda p: p.portrait_name_text().strip() == qctest_name_en)
                caption = public.portrait_name_text().strip()
                signature = public.signature_name_text().strip()
            # Assert: Step 3 -- both locations show the new GM Name identically.
            assert live and caption == qctest_name_en, f"Portrait Caption shows {caption!r}"
            assert signature == qctest_name_en, f"Signature Block shows {signature!r}"
            assert caption == signature
        finally:
            _close(anon_ctx)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (EN) accepts a valid value up to the 100-character limit and saves (ADO-135459)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135459
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_en_accepts_a_valid_value_up_to_135459(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (EN) is rejected when left empty (ADO-135460)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135460
@pytest.mark.traceability("135460")
@allure.label("pbi", "129397")
@allure.label("testcase", "135460")
@GM_GROUP
@pytest.mark.timeout(300)
def test_page_title_en_is_rejected_when_left_empty_135460(page, browser, tmp_path):
    _text_empty_rejected(page, "135460", A.LABEL_PAGE_TITLE, locale="en", expected_msg='"Page title is required."')


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (EN) is rejected when it exceeds 100 characters (ADO-135461)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135461
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_en_is_rejected_when_it_exceeds_100_135461(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (AR) accepts a valid Arabic value up to 100 characters and saves (ADO-135462)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135462
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_ar_accepts_a_valid_arabic_value_up_135462(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (AR) is rejected with the Arabic-specific message when left empty (ADO-135463)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135463
@pytest.mark.traceability("135463")
@allure.label("pbi", "129397")
@allure.label("testcase", "135463")
@GM_GROUP
@pytest.mark.timeout(300)
def test_page_title_ar_is_rejected_with_the_arabicspecific_message_135463(page, browser, tmp_path):
    _text_empty_rejected(page, "135463", A.LABEL_PAGE_TITLE, locale="ar", expected_msg='"Arabic title is required." / "العنوان العربي مطلوب."')


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (AR) is rejected when it exceeds 100 characters (ADO-135464)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135464
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_ar_is_rejected_when_it_exceeds_100_135464(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid JPG Hero Banner image under 2MB uploads successfully (ADO-135465)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135465
@pytest.mark.traceability("135465")
@allure.label("pbi", "129397")
@allure.label("testcase", "135465")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_jpg_hero_banner_image_under_2mb_uploads_successfully_135465(page, browser, tmp_path):
    _upload_valid(page, browser, tmp_path, "135465", A.LABEL_HERO, "hero-banner.jpg", int(1.5 * MB))


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported Hero Banner image format is rejected (ADO-135466)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135466
@pytest.mark.traceability("135466")
@allure.label("pbi", "129397")
@allure.label("testcase", "135466")
@GM_GROUP
@pytest.mark.timeout(480)
def test_unsupported_hero_banner_image_format_is_rejected_135466(page, browser, tmp_path):
    _upload_rejected(page, tmp_path, "135466", A.LABEL_HERO, "hero-banner.gif", 300 * 1024,
                     expected_msg="format-not-supported error")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Hero Banner image exceeding 2MB is rejected with the exact bilingual error message (ADO-135467)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135467
@pytest.mark.traceability("135467")
@allure.label("pbi", "129397")
@allure.label("testcase", "135467")
@GM_GROUP
@pytest.mark.timeout(300)
def test_hero_banner_image_exceeding_2mb_is_rejected_with_the_135467(page, browser, tmp_path):
    _upload_rejected(page, tmp_path, "135467", A.LABEL_HERO, "hero-banner-3mb.jpg", 3 * MB, expected_msg='"Image size must not exceed 2 MB." / "يجب ألا يتجاوز حجم الصورة 2 ميغابايت."', size_case=True)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Hero Banner image exactly at the 2MB boundary is accepted (ADO-135468)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135468
@pytest.mark.traceability("135468")
@allure.label("pbi", "129397")
@allure.label("testcase", "135468")
@GM_GROUP
@pytest.mark.timeout(480)
def test_hero_banner_image_exactly_at_the_2mb_boundary_is_135468(page, browser, tmp_path):
    # No Save step in the case: picker acceptance only, nothing is saved.
    _p34_picker_accepts(page, tmp_path, "135468", A.LABEL_HERO, "hero-banner-2mb.jpg", 2 * MB)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (EN) accepts a valid value up to 150 characters (ADO-135469)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135469
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_en_accepts_a_valid_value_up_135469(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (EN) is rejected when left empty (ADO-135470)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135470
@pytest.mark.traceability("135470")
@allure.label("pbi", "129397")
@allure.label("testcase", "135470")
@GM_GROUP
@pytest.mark.timeout(300)
def test_image_alt_text_en_is_rejected_when_left_empty_135470(page, browser, tmp_path):
    _text_empty_rejected(page, "135470", A.LABEL_ALT_TEXT, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (EN) is rejected when it exceeds 150 characters (ADO-135471)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135471
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_en_is_rejected_when_it_exceeds_135471(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (AR) accepts a valid Arabic value up to 150 characters (ADO-135472)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135472
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_ar_accepts_a_valid_arabic_value_135472(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (AR) is rejected when left empty (ADO-135473)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135473
@pytest.mark.traceability("135473")
@allure.label("pbi", "129397")
@allure.label("testcase", "135473")
@GM_GROUP
@pytest.mark.timeout(300)
def test_image_alt_text_ar_is_rejected_when_left_empty_135473(page, browser, tmp_path):
    _text_empty_rejected(page, "135473", A.LABEL_ALT_TEXT, locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Portrait Image in PNG format under 2MB uploads successfully (ADO-135474)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135474
@pytest.mark.traceability("135474")
@allure.label("pbi", "129397")
@allure.label("testcase", "135474")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_gm_portrait_image_in_png_format_under_2mb_135474(page, browser, tmp_path):
    _upload_valid(page, browser, tmp_path, "135474", A.LABEL_PORTRAIT, "gm-portrait.png", 800 * 1024)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported GM Portrait Image format (SVG) is rejected (ADO-135475)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135475
@pytest.mark.traceability("135475")
@allure.label("pbi", "129397")
@allure.label("testcase", "135475")
@GM_GROUP
@pytest.mark.timeout(480)
def test_unsupported_gm_portrait_image_format_svg_is_rejected_135475(page, browser, tmp_path):
    _upload_rejected(page, tmp_path, "135475", A.LABEL_PORTRAIT, "gm-portrait.svg", 50 * 1024,
                     expected_msg="format-not-supported error")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Portrait Image exceeding 2MB is rejected (ADO-135476)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135476
@pytest.mark.traceability("135476")
@allure.label("pbi", "129397")
@allure.label("testcase", "135476")
@GM_GROUP
@pytest.mark.timeout(300)
def test_gm_portrait_image_exceeding_2mb_is_rejected_135476(page, browser, tmp_path):
    _upload_rejected(page, tmp_path, "135476", A.LABEL_PORTRAIT, "gm-portrait-2_8mb.jpg", int(2.8 * MB), expected_msg='"Image size must not exceed 2 MB." / "يجب ألا يتجاوز حجم الصورة 2 ميغابايت."', size_case=True)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (EN) accepts a valid value and saves correctly (ADO-135477)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135477
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_en_accepts_a_valid_value_and_saves_135477(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (EN) is rejected when left empty (ADO-135478)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135478
@pytest.mark.traceability("135478")
@allure.label("pbi", "129397")
@allure.label("testcase", "135478")
@GM_GROUP
@pytest.mark.timeout(300)
def test_gm_name_en_is_rejected_when_left_empty_135478(page, browser, tmp_path):
    _text_empty_rejected(page, "135478", A.LABEL_GM_NAME, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (EN) is rejected when it exceeds 100 characters (ADO-135479)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135479
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_en_is_rejected_when_it_exceeds_100_135479(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (AR) accepts a valid Arabic value and saves correctly (ADO-135480)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135480
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_ar_accepts_a_valid_arabic_value_and_135480(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (AR) is rejected when left empty (ADO-135481)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135481
@pytest.mark.traceability("135481")
@allure.label("pbi", "129397")
@allure.label("testcase", "135481")
@GM_GROUP
@pytest.mark.timeout(300)
def test_gm_name_ar_is_rejected_when_left_empty_135481(page, browser, tmp_path):
    _text_empty_rejected(page, "135481", A.LABEL_GM_NAME, locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Designation (EN) accepts a valid value and saves correctly (ADO-135482)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135482
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_en_accepts_a_valid_value_and_saves_135482(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Designation (EN) is rejected when left empty (ADO-135483)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135483
@pytest.mark.traceability("135483")
@allure.label("pbi", "129397")
@allure.label("testcase", "135483")
@GM_GROUP
@pytest.mark.timeout(300)
def test_gm_designation_en_is_rejected_when_left_empty_135483(page, browser, tmp_path):
    _text_empty_rejected(page, "135483", A.LABEL_DESIGNATION, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Designation (AR) accepts a valid Arabic value and saves correctly (ADO-135484)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135484
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_ar_accepts_a_valid_arabic_value_and_135484(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (EN) accepts a valid value up to 150 characters (ADO-135485)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135485
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_en_accepts_a_valid_value_up_to_135485(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (EN) is rejected when left empty (ADO-135486)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135486
@pytest.mark.traceability("135486")
@allure.label("pbi", "129397")
@allure.label("testcase", "135486")
@GM_GROUP
@pytest.mark.timeout(300)
def test_salutation_heading_en_is_rejected_when_left_empty_135486(page, browser, tmp_path):
    _text_empty_rejected(page, "135486", A.LABEL_SALUTATION, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (EN) is rejected when it exceeds 150 characters (ADO-135487)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135487
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_en_is_rejected_when_it_exceeds_150_135487(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (AR) accepts a valid Arabic value up to 150 characters (ADO-135488)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135488
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_ar_accepts_a_valid_arabic_value_up_135488(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) accepts valid rich text with headings, paragraphs, bullets, and inline links (ADO-135489)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135489
@pytest.mark.traceability("135489")
@allure.label("pbi", "129397")
@allure.label("testcase", "135489")
@GM_GROUP
@pytest.mark.timeout(300)
def test_page_content_en_accepts_valid_rich_text_with_headings_135489(page, browser, tmp_path):
    html = "<h3>QCTEST-135489 Heading</h3><p>QCTEST-135489 first paragraph.</p><ul><li>Item one</li><li>Item two</li><li>Item three</li></ul><p>Second paragraph with <a href=\"https://www.qatarchamber.com/\">an inline link</a>.</p>"
    _content_html_valid(page, browser, "135489", html, "en", ("<h3>", "<ul>", "<li>Item three</li>", "<a href=\"https://www.qatarchamber.com/\""))


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) is rejected when left empty (ADO-135490)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135490
@pytest.mark.traceability("135490")
@allure.label("pbi", "129397")
@allure.label("testcase", "135490")
@GM_GROUP
@pytest.mark.timeout(300)
def test_page_content_en_is_rejected_when_left_empty_135490(page, browser, tmp_path):
    _content_empty_rejected(page, "135490", locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) is rejected when it exceeds 5000 characters (ADO-135491)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135491
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_en_is_rejected_when_it_exceeds_5000_135491(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (AR) accepts valid Arabic rich text and saves correctly (ADO-135492)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135492
@pytest.mark.traceability("135492")
@allure.label("pbi", "129397")
@allure.label("testcase", "135492")
@GM_GROUP
@pytest.mark.timeout(300)
def test_page_content_ar_accepts_valid_arabic_rich_text_and_135492(page, browser, tmp_path):
    html = "<p dir=\"rtl\">QCTEST-135492 رسالة المدير العام إلى الأعضاء.</p><ul><li>البند الأول</li><li>البند الثاني</li></ul><p dir=\"rtl\">لمزيد من المعلومات زوروا <a href=\"https://www.qatarchamber.com/\">Qatar Chamber</a>.</p>"
    _content_html_valid(page, browser, "135492", html, "ar", ("البند الثاني", "<ul>", ">Qatar Chamber</a>"))


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (AR) is rejected when left empty (ADO-135493)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135493
@pytest.mark.traceability("135493")
@allure.label("pbi", "129397")
@allure.label("testcase", "135493")
@GM_GROUP
@pytest.mark.timeout(300)
def test_page_content_ar_is_rejected_when_left_empty_135493(page, browser, tmp_path):
    _content_empty_rejected(page, "135493", locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (EN) accepts a valid value up to 50 characters (ADO-135494)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135494
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_en_accepts_a_valid_value_up_135494(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (EN) is rejected when left empty (ADO-135495)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135495
@pytest.mark.traceability("135495")
@allure.label("pbi", "129397")
@allure.label("testcase", "135495")
@GM_GROUP
@pytest.mark.timeout(300)
def test_signature_closing_text_en_is_rejected_when_left_empty_135495(page, browser, tmp_path):
    _text_empty_rejected(page, "135495", A.LABEL_CLOSING, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (EN) is rejected when it exceeds 50 characters (ADO-135496)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135496
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_en_is_rejected_when_it_exceeds_135496(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (AR) accepts a valid Arabic value up to 50 characters (ADO-135497)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135497
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_ar_accepts_a_valid_arabic_value_135497(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Avatar image uploads successfully as an optional field (ADO-135498)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135498
@pytest.mark.traceability("135498")
@allure.label("pbi", "129397")
@allure.label("testcase", "135498")
@GM_GROUP
@pytest.mark.timeout(900)
def test_valid_signature_avatar_image_uploads_successfully_as_an_optional_135498(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "upload + Save of a Signature Avatar (PNG, 200 KB)", tc_id="135498")
    _p34_avatar_valid(page, browser, tmp_path, "135498", "avatar-135498.png", 200 * 1024)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that the record saves successfully when the optional Signature Avatar is left blank (ADO-135499)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135499
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_the_record_saves_successfully_when_the_optional_signature_avatar_135499(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported Signature Avatar format is rejected even though the field is optional (ADO-135500)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135500
@pytest.mark.traceability("135500")
@allure.label("pbi", "129397")
@allure.label("testcase", "135500")
@GM_GROUP
@pytest.mark.timeout(480)
def test_unsupported_signature_avatar_format_is_rejected_even_though_the_135500(page, browser, tmp_path):
    _p34_avatar_rejected(page, tmp_path, "135500", "avatar.bmp", 200 * 1024)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Published makes the record visible on the live website (ADO-135501)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135501
@pytest.mark.traceability("135501")
@allure.label("pbi", "129397")
@allure.label("testcase", "135501")
@GM_GROUP
@pytest.mark.timeout(300)
def test_setting_status_to_published_makes_the_record_visible_on_135501(page, browser, tmp_path):
    # Success toast wording/presence is a note, not an assertion (QA ruling).
    _publish_visible(page, browser, "135501", role=ROLE_EDITOR)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Draft keeps the record CMS-only and invisible on the live website (ADO-135502)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135502
@pytest.mark.traceability("135502")
@allure.label("pbi", "129397")
@allure.label("testcase", "135502")
@GM_GROUP
@pytest.mark.timeout(300)
def test_setting_status_to_draft_keeps_the_record_cmsonly_and_135502(page, browser, tmp_path):
    _draft_not_public(page, browser, "135502")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid hyperlink URL entered in the message content is saved and rendered as a working link (ADO-135503)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135503
@pytest.mark.traceability("135503")
@allure.label("pbi", "129397")
@allure.label("testcase", "135503")
@GM_GROUP
@pytest.mark.timeout(900)
def test_valid_hyperlink_url_entered_in_the_message_content_is_135503(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Page Content hyperlink save", tc_id="135503")
    _p34_content_link(page, browser, "135503", QC_URL)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an invalid hyperlink URL is rejected with the exact validation message (ADO-135504)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_135504
@pytest.mark.traceability("135504")
@allure.label("pbi", "129397")
@allure.label("testcase", "135504")
@GM_GROUP
@pytest.mark.timeout(300)
def test_invalid_hyperlink_url_is_rejected_with_the_exact_validation_135504(page, browser, tmp_path):
    _content_html_rejected(page, "135504", '<p><a href="not-a-valid-url">QCTEST-135504</a></p>',
                           expected_msg='"Please enter a valid URL." / "يرجى إدخال رابط صالح."')


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that entering the GM Name once and saving reflects into both the portrait caption preview and the signature block preview without re-entry (ADO-135505)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.dataintegrity
@pytest.mark.pbi_129397
@pytest.mark.tc_135505
@pytest.mark.traceability("135505")
@allure.label("pbi", "129397")
@allure.label("testcase", "135505")
@GM_GROUP
@pytest.mark.timeout(300)
def test_entering_the_gm_name_once_and_saving_reflects_into_135505(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "unpublish + Save as Draft of GM Name")
    _snapshot(page, writes=(A.LABEL_GM_NAME,))
    admin = A(page)
    marker = _marker("135505", "NAME")
    with allure.step("Enter GM Name (EN) once, save the draft and Preview"):
        authoring = _editable(admin.open_record("en"))
        assert authoring.field_count(A.LABEL_GM_NAME) == 1, "more than one GM Name (EN) entry point"
        authoring.fill_text(A.LABEL_GM_NAME, marker)
        _save_draft(authoring)
        url = _preview_url(admin)
        preview = GmMessagePage(page)
        preview.open(url)
        caption, signature = preview.portrait_name_text().strip(), preview.signature_name_text().strip()
    assert caption == marker, f"preview Portrait Caption shows {caption!r}"
    assert signature == marker, f"preview Signature Block shows {signature!r}"


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that all field values are retained after saving as Draft and reloading the record (ADO-135506)")
@allure.label("pbi", "129397")
@allure.label("testcase", "135506")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_135506
@pytest.mark.xdist_group("gm_message_79878")
def test_all_field_values_are_retained_after_saving_as_draft_135506(page):
    """ADO-135506. Same baseline-capture -> try -> assert -> finally-restore
    structure as tc_135453/tc_135457/tc_135454/tc_135456 against the SAME
    shared singleton record (79878) — the `_CMS_LOGIN_BLOCKED` condition
    this module's other stubs still carry was diagnosed and resolved (see
    tc_135453's own docstring); only this one case is unblocked here.

    Case's Step 1 ("Complete all mandatory fields with valid data and click
    Save as Draft") + Step 2 ("Navigate away and reopen; every field — EN/AR
    text, both images, dropdown status — displays the exact previously
    entered values"), scripted against this form's real, confirmed-live
    mechanics (see GmMessageAdminPage's module docstring):
      - "Save as Draft" == select_status("Draft") + save() (this form has no
        separate Save-as-Draft button; Status IS the publish/draft control).
      - "Navigate away and reopen" == open_gm_message_edit_form() again,
        which always re-enters via the admin home/menu path, a real
        navigation away from and back into the record.
      - EN + AR text fields exercised: GM Name and Salutation Heading (the
        two fields already proven bilingual-toggle-safe by tc_135453,
        avoiding re-deriving new locators for this pass).
      - Both images: verified via `has_file_uploaded()` (the safe,
        non-destructive read of "field holds a real upload") rather than
        re-uploading — re-uploading risks an unrecoverable overwrite with no
        confirmed revert path (cms-profile.md's Test-Data Policy), same
        disclosed substitution already used by tc_135453 for Step 1's image
        guarantee.
      - Dropdown status: asserted via `status_value()` reading back "Draft"
        after the reopen.
      - Baseline (GM Name EN/AR, Salutation Heading EN/AR, Status) is
        captured BEFORE any change and restored in a `finally` block
        regardless of pass/fail, so the shared singleton is never left
        mutated.
    """
    admin = GmMessageAdminPage(page)

    qctest_name_en = "QCTEST-135506 Mr. Ali Saeed Busherbak Al Mansoori"
    qctest_salutation_en = "QCTEST-135506 Dear members and visitors,"
    qctest_name_ar = "QCTEST-135506 السيد علي سعيد بوشهبك المنصوري"
    qctest_salutation_ar = "QCTEST-135506 أعزاءنا الأعضاء والزوار،"

    with allure.step("Open the GM's Message record in the Control Panel"):
        admin.open_gm_message_edit_form()

    with allure.step("Enter AR field values (GM Name, Salutation Heading)"):
        admin.switch_field_to_arabic("GM Name")
        admin.fill_text_field(admin.GM_NAME, qctest_name_ar)
        admin.switch_field_to_arabic("Salutation Heading")
        admin.fill_text_field(admin.SALUTATION_HEADING, qctest_salutation_ar)

    # Assert: AR fields accept the new input (before Save, so a
    # post-reload failure is unambiguous — persistence, not entry).
    assert admin.field_value(admin.GM_NAME) == qctest_name_ar
    assert admin.field_value(admin.SALUTATION_HEADING) == qctest_salutation_ar

    with allure.step("Switch back to EN and enter EN field values"):
        admin.switch_field_to_english("GM Name")
        admin.switch_field_to_english("Salutation Heading")
        admin.fill_text_field(admin.GM_NAME, qctest_name_en)
        admin.fill_text_field(admin.SALUTATION_HEADING, qctest_salutation_en)

    # Assert: EN fields accept the new input (same pre-Save diagnostic
    # purpose as the AR asserts above).
    assert admin.field_value(admin.GM_NAME) == qctest_name_en
    assert admin.field_value(admin.SALUTATION_HEADING) == qctest_salutation_en

    with allure.step('Set Status to "Draft" and click Save (this form\'s "Save as Draft")'):
        admin.select_status("Draft")
        block_live_singleton_write(GM_RECORD, "Status -> Draft + Save of EN/AR values")
        admin.save()

    # Assert: Step 1 -- save succeeds with no validation error.
    assert not admin.is_save_error_shown(), admin.save_error_text()

    with allure.step("Navigate away and reopen the record"):
        admin.open_gm_message_edit_form()

    # Assert: Step 2 -- every field (EN/AR text, both images, dropdown
    # status) displays the exact previously entered values.
    assert admin.field_value(admin.GM_NAME) == qctest_name_en
    assert admin.field_value(admin.SALUTATION_HEADING) == qctest_salutation_en

    admin.switch_field_to_arabic("GM Name")
    assert admin.field_value(admin.GM_NAME) == qctest_name_ar
    admin.switch_field_to_arabic("Salutation Heading")
    assert admin.field_value(admin.SALUTATION_HEADING) == qctest_salutation_ar
    admin.switch_field_to_english("GM Name")
    admin.switch_field_to_english("Salutation Heading")

    assert admin.has_file_uploaded("GM Portrait Image")
    assert admin.has_file_uploaded("Hero Banner")

    assert admin.status_value() == "Draft"


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a name/designation mismatch between the portrait caption and signature block is visibly detectable if content is authored inconsistently (ADO-135508)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.dataintegrity
@pytest.mark.pbi_129397
@pytest.mark.tc_135508
@pytest.mark.traceability("135508")
@allure.label("pbi", "129397")
@allure.label("testcase", "135508")
@GM_GROUP
@pytest.mark.timeout(480)
def test_namedesignation_mismatch_between_the_portrait_caption_and_signature_block_135508(page, browser):
    # Account: TEST_USER (the module's `page`) -- the case is about what the
    # visitor page shows for two authored values, not a workflow path.
    #
    # PRECONDITION READ FIRST (2026-10-14): the case needs the portrait caption
    # and the signature block to carry their OWN GM Name / GM Designation
    # fields. Live, the Object Authoring form renders ONE `GM Name` and ONE
    # `GM Designation` (+ AR twins); the signature block has only Signature
    # Closing Text and Signature Avatar. When no separate signature pair
    # exists, a mismatch cannot be authored at all: the test records the
    # field list plus the public page (both blocks render the one stored
    # value) and stops as NOT APPLICABLE BEFORE any write.
    admin = A(page)
    anon_ctx = None
    with allure.step("Open the GM Message record and locate the portrait and signature "
                     "GM Name / GM Designation fields"):
        authoring = admin.open_record("en")
        labels = authoring.form_field_labels()
        _attach("form field labels", labels)
        english = [label for label in labels if AR.strip() not in label]
        sig_name = next((label for label in english if "signature" in label.lower()
                         and "name" in label.lower()), None)
        sig_desig = next((label for label in english if "signature" in label.lower()
                          and "designation" in label.lower()), None)
        counts = {A.LABEL_GM_NAME: authoring.field_count(A.LABEL_GM_NAME),
                  A.LABEL_DESIGNATION: authoring.field_count(A.LABEL_DESIGNATION)}
        _attach("portrait/signature field discovery",
                {"signature name": sig_name, "signature designation": sig_desig, "controls": counts})

    if not (sig_name and sig_desig):
        try:
            anon_ctx, public = _anon(browser)
            with allure.step("Public page (anonymous): both blocks render the ONE stored value"):
                public.open_gm_message(cache_bust=True)
                shown = {
                    "portrait": (public.portrait_name_text().strip(), public.portrait_designation_text().strip()),
                    "signature": (public.signature_name_text().strip(),
                                  public.signature_designation_text().strip()),
                }
                stored = (authoring.field_value(A.LABEL_GM_NAME), authoring.field_value(A.LABEL_DESIGNATION))
                _attach("stored vs public", {"stored (name, designation)": stored, **shown})
        finally:
            _close(anon_ctx)
        pytest.fail(
            "NOT APPLICABLE -- the GM Message object has no separate signature GM Name / GM "
            f"Designation fields (form controls: {counts}; no signature name/designation label among "
            f"{english}). The portrait caption and the signature block both render the single stored "
            f"value (public: {shown}), so the case's mismatch cannot be authored. Nothing was written. "
            "Requirements-vs-implementation question for the QA Manager / BA.",
            pytrace=False,
        )

    # A separate signature pair exists -- run the case as written.
    block_live_singleton_write(GM_RECORD, "publish of two different GM Name / Designation pairs",
                               tc_id="135508")
    _snapshot(page, budget=480)  # precondition: 79878 Published (fails without writing)
    portrait = (_marker("135508", "PORTRAIT-NAME"), _marker("135508", "PORTRAIT-DESIGNATION"))
    signature = (_marker("135508", "SIGNATURE-NAME"), _marker("135508", "SIGNATURE-DESIGNATION"))
    with _gm_end_published(admin, "135508"):
        try:
            with allure.step("Author the portrait and the signature GM Name / Designation with two "
                             "different values and Publish"):
                authoring = _editable(admin.open_record("en"))
                for label, value in ((A.LABEL_GM_NAME, portrait[0]), (A.LABEL_DESIGNATION, portrait[1]),
                                     (sig_name, signature[0]), (sig_desig, signature[1])):
                    log_live_write(GM_RECORD, f"{label} (EN)", value, "135508", action="write",
                                   note=f"old value {authoring.field_value(label)!r}")
                    authoring.fill_text(label, value)
                status = _publish(admin, authoring)
            anon_ctx, public = _anon(browser)
            with allure.step("Public page (anonymous): both blocks show the values as entered"):
                def _both_shown() -> bool:
                    public.open_gm_message(cache_bust=True)
                    try:
                        return (public.portrait_name_text().strip() == portrait[0]
                                and public.signature_name_text().strip() == signature[0])
                    except Exception:  # noqa: BLE001 -- block absent on this load
                        return False

                try:
                    wait_until(_both_shown, timeout=_budget(PUBLISH_WAIT * 2), poll=5)
                    live = True
                except Exception:  # noqa: BLE001 -- asserted below
                    live = False
                shown_portrait = (public.portrait_name_text().strip(),
                                  public.portrait_designation_text().strip())
                shown_signature = (public.signature_name_text().strip(),
                                   public.signature_designation_text().strip())
                _attach("public", {"portrait": shown_portrait, "signature": shown_signature})
        finally:
            _close(anon_ctx)
    assert status == STATUS_PUBLISHED, f"record is {status!r} after Publish"
    assert live, (f"the public page never showed both authored values (portrait {shown_portrait}, "
                  f"signature {shown_signature})")
    assert shown_portrait == portrait, f"Portrait Caption shows {shown_portrait}, expected {portrait}"
    assert shown_signature == signature, f"Signature Block shows {shown_signature}, expected {signature}"


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that republishing a page immediately after unpublishing restores it to the live site correctly (ADO-135509)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135509
@pytest.mark.traceability("135509")
@allure.label("pbi", "129397")
@allure.label("testcase", "135509")
@GM_GROUP
@pytest.mark.timeout(480)
def test_republishing_a_page_immediately_after_unpublishing_restores_it_to_135509(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Editor Unpublish then immediate Publish", tc_id="135509")
    _p34_republish_after_unpublish(page, browser, "135509")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Publish is blocked when the GM Portrait Image field is left in an invalid state (upload failed) (ADO-135511)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135511
@pytest.mark.traceability("135511")
@allure.label("pbi", "129397")
@allure.label("testcase", "135511")
@GM_GROUP
@pytest.mark.timeout(300)
def test_publish_is_blocked_when_the_gm_portrait_image_field_135511(page, browser, tmp_path):
    _upload_missing_rejected(page, tmp_path, "135511", A.LABEL_PORTRAIT, interrupted=True)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that rapidly double-clicking Publish does not create a duplicate publish action or duplicate audit log entry (ADO-135512)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135512
@pytest.mark.traceability("135512")
@allure.label("pbi", "129397")
@allure.label("testcase", "135512")
@GM_GROUP
@pytest.mark.timeout(480)
def test_rapidly_doubleclicking_publish_does_not_create_a_duplicate_publish_135512(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Editor Unpublish, then a double-clicked Publish", tc_id="135512")
    _p34_double_click_publish(page, browser, "135512")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Portrait Image sized exactly 1 byte over the 2MB limit is rejected while exactly-2MB is accepted (ADO-135513)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135513
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_portrait_image_sized_exactly_1_byte_over_the_135513(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that the system handles two admin sessions editing the same GM's Message Draft record concurrently without silent data loss (ADO-135514)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135514
@pytest.mark.traceability("135514")
@allure.label("pbi", "129397")
@allure.label("testcase", "135514")
@GM_GROUP
@pytest.mark.timeout(900)
def test_the_system_handles_two_admin_sessions_editing_the_same_135514(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "two concurrent Editor sessions saving", tc_id="135514")
    _p34_concurrent_edit(page, browser, "135514")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unauthenticated user is denied direct access to the CMS edit screen for the GM's Message page (ADO-136375)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136375
@pytest.mark.traceability("136375")
@allure.label("pbi", "129397")
@allure.label("testcase", "136375")
@GM_GROUP
@pytest.mark.timeout(300)
def test_unauthenticated_user_is_denied_direct_access_to_the_cms_136375(page, browser, tmp_path):
    _denied_direct_url(page, browser, "136375", None)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Editor has full lifecycle controls for the GM's Message page (ADO-136376)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136376
@pytest.mark.traceability("136376")
@allure.label("pbi", "129397")
@allure.label("testcase", "136376")
@GM_GROUP
@pytest.mark.timeout(300)
def test_site_content_editor_has_full_lifecycle_controls_for_the_136376(page, browser, tmp_path):
    ctx = None
    try:
        ctx, editor_page = _role_session(browser, ROLE_EDITOR)
        admin = A(editor_page)
        with allure.step("As Site Content Editor, open the GM Message record"):
            authoring = admin.open_record("en")
            status = authoring.current_status()
            editable = admin.is_field_editable(A.LABEL_GM_NAME)
            unpublish = "Unpublish" in authoring.editing_banner_text()
        with allure.step("Inspect the row: Preview and Unpublish are offered"):
            listing = admin.open_list("en")
            actions = admin.row_actions()
            preview = listing.row_preview_url_by_code(GM_MESSAGE_ENTRY_CODE)
            _attach("row actions", sorted(actions))
        assert status == STATUS_PUBLISHED, f"precondition: record is {status!r}"
        assert editable, "Edit: the Editor cannot edit the record"
        assert preview, "Preview: no preview link for the record"
        assert unpublish or "unpublish" in actions, "Unpublish: no control for the Editor"
        # Publish is the form's Submit for Review (an Editor's submit publishes).
        admin.open_record("en")
        assert admin.has_publish_submit(), "Publish: no submit control"
    finally:
        _close(ctx)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author can edit assigned GM's Message content but cannot publish directly (ADO-136377)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136377
@pytest.mark.traceability("136377")
@allure.label("pbi", "129397")
@allure.label("testcase", "136377")
@GM_GROUP
@pytest.mark.timeout(300)
def test_site_content_author_can_edit_assigned_gms_message_content_136377(page, browser, tmp_path):
    _author_cannot_publish(browser, "136377")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author is denied when attempting to publish the GM's Message page directly (ADO-136378)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136378
@pytest.mark.traceability("136378")
@allure.label("pbi", "129397")
@allure.label("testcase", "136378")
@GM_GROUP
@pytest.mark.timeout(300)
def test_site_content_author_is_denied_when_attempting_to_publish_136378(page, browser, tmp_path):
    _author_cannot_publish(browser, "136378", inspect_fields=False)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a user with no CMS permission is denied access when opening the GM's Message page record (ADO-136379)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136379
@pytest.mark.traceability("136379")
@allure.label("pbi", "129397")
@allure.label("testcase", "136379")
@GM_GROUP
@pytest.mark.timeout(300)
def test_user_with_no_cms_permission_is_denied_access_when_136379(page, browser, tmp_path):
    _denied_direct_url(page, browser, "136379", ROLE_NO_ROLE)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an expired admin session forces re-authentication during GM's Message editing (ADO-136380)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136380
@pytest.mark.traceability("136380")
@allure.label("pbi", "129397")
@allure.label("testcase", "136380")
@GM_GROUP
@pytest.mark.timeout(480)
def test_expired_admin_session_forces_reauthentication_during_gms_message_editing_136380(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Unpublish + expired-session Save attempt", tc_id="136380")
    _p34_expired_session(page, browser, "136380")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a role change mid-session is reflected on the next permission-checked action (ADO-136381)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136381
@pytest.mark.traceability("136381")
@allure.label("pbi", "129397")
@allure.label("testcase", "136381")
@GM_GROUP
@pytest.mark.timeout(480)
def test_role_change_midsession_is_reflected_on_the_next_permissionchecked_136381(page, browser, tmp_path):
    # Hard stop: the permission revocation is shared role configuration,
    # never opened by QC_ALLOW_LIVE_SINGLETON_WRITES (see the helper).
    _p34_role_change_mid_session(page, browser, "136381")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Preview shows exact content without publishing the page (ADO-136389)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136389
@pytest.mark.traceability("136389")
@allure.label("pbi", "129397")
@allure.label("testcase", "136389")
@GM_GROUP
@pytest.mark.timeout(300)
def test_preview_shows_exact_content_without_publishing_the_page_136389(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "unpublish + Save as Draft of Page Content")
    _snapshot(page, writes=("content_en",))
    marker = _marker("136389", "PREVIEW")
    ctx = anon_ctx = None
    try:
        ctx, editor_page = _role_session(browser, ROLE_EDITOR)
        admin = A(editor_page)
        with allure.step("Edit Page Content and Preview (no publish)"):
            authoring = _editable(admin.open_record("en"))
            admin.set_page_content_html(f"<p>{marker}</p>", "en")
            _save_draft(authoring)
            preview = (authoring.open(_preview_url(admin)) or authoring).rendered_body_text()
        assert marker in preview, "Preview does not render the new content exactly"
        with allure.step("Close preview: status not Published, visitors do not see the edit"):
            status = admin.open_record("en").current_status()
            anon_ctx, public = _anon(browser)
            leaked = _public_shows(public, lambda p: marker in p.page_text(), timeout=30)
        # Object Authoring needs Unpublish before a draft edit, so the prior
        # live page is offline meanwhile (guide §4) -- the case's "old content
        # still live" is noted, the not-published guarantee is asserted.
        _attach("note", "previewing a draft on this surface requires Unpublish first (guide §4)")
        assert status != STATUS_PUBLISHED, f"Preview published the record ({status!r})"
        assert not leaked, "previewed (unpublished) content is visible on the live site"
    finally:
        _close(anon_ctx, ctx)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that publishing the GM's Message page records an audit log entry (ADO-136390)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136390
@pytest.mark.traceability("136390")
@allure.label("pbi", "129397")
@allure.label("testcase", "136390")
@GM_GROUP
@pytest.mark.timeout(480)
def test_publishing_the_gms_message_page_records_an_audit_log_136390(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Editor publish of Salutation Heading (audit)", tc_id="136390")
    _p34_publish_audit(page, browser, "136390")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Draft to Preview to Publish lifecycle continuity is preserved across multiple editing sessions (ADO-136391)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136391
@pytest.mark.traceability("136391")
@allure.label("pbi", "129397")
@allure.label("testcase", "136391")
@GM_GROUP
@pytest.mark.timeout(300)
def test_draft_to_preview_to_publish_lifecycle_continuity_is_preserved_136391(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "two-session draft then publish")
    _snapshot(page, writes=(A.LABEL_SALUTATION, A.LABEL_CLOSING))
    part1, part2 = _marker("136391", "SESSION1"), _marker("136391", "SESSION2")
    c1 = c2 = anon_ctx = None
    try:
        c1, p1 = _role_session(browser, ROLE_EDITOR)
        # Session 2 signs in now, BEFORE session 1 mutates the record -- it is
        # still a separate session that never saw session 1's edit.
        c2, p2 = _role_session(browser, ROLE_EDITOR)
        with allure.step("Session 1: partial content, Save as Draft, log out"):
            first = A(p1)
            authoring = _editable(first.open_record("en"))
            authoring.fill_text(A.LABEL_SALUTATION, part1)
            _save_draft(authoring)
        _close(c1)
        c1 = None
        second = A(p2)
        with allure.step("Session 2: reopen -- the draft values are present"):
            authoring = second.open_record("en")
            kept = authoring.field_value(A.LABEL_SALUTATION)
        assert kept == part1, f"draft value lost between sessions: {kept!r}"
        with allure.step("Complete the remaining field and Publish"):
            authoring.fill_text(A.LABEL_CLOSING, part2)
            status = _publish(second, authoring)
        assert status == STATUS_PUBLISHED, f"record is {status!r} after Publish"
        anon_ctx, public = _anon(browser)
        assert _public_shows(public, lambda p: p.salutation_text().strip() == part1
                             and p.signature_regards_text().strip() == part2), (
            "published page lacks the combined content from both sessions"
        )
    finally:
        _close(anon_ctx, c1, c2)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Editor can publish content submitted by a Site Content Author (ADO-136392)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136392
@pytest.mark.traceability("136392")
@allure.label("pbi", "129397")
@allure.label("testcase", "136392")
@GM_GROUP
@pytest.mark.timeout(300)
def test_site_content_editor_can_publish_content_submitted_by_a_136392(page, browser, tmp_path):
    _author_submits_change(page, browser, "136392", editor_publishes=True)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that republishing the GM's Message page updates the existing live page without creating a duplicate record (ADO-136393)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136393
@pytest.mark.traceability("136393")
@allure.label("pbi", "129397")
@allure.label("testcase", "136393")
@GM_GROUP
@pytest.mark.timeout(300)
def test_republishing_the_gms_message_page_updates_the_existing_live_136393(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "republish of Page Content")
    _snapshot(page, writes=("content_en",))
    admin = A(page)
    with allure.step("Note the live record's ID and the entries count"):
        admin.open_list("en")
        rows_before = admin.entries_row_count()
        code_before = admin.open_record("en").entry_code()
    with allure.step("Edit Page Content and Publish again"):
        authoring = _editable(admin.open_record("en"))
        admin.set_page_content_html(f"<p>{_marker('136393', 'REPUBLISH')}</p>", "en")
        status = _publish(admin, authoring)
    assert status == STATUS_PUBLISHED, f"republish did not commit ({status!r})"
    with allure.step("Re-check the ID and that no duplicate was created"):
        admin.open_list("en")
        rows_after = admin.entries_row_count()
        code_after = admin.open_record("en").entry_code()
    assert code_after == code_before, f"record ID changed {code_before!r} -> {code_after!r}"
    assert rows_after == rows_before, f"entries {rows_before} -> {rows_after}: a duplicate was created"


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Page Title (EN) is saved and persists after reload (ADO-136394)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136394
@pytest.mark.traceability("136394")
@allure.label("pbi", "129397")
@allure.label("testcase", "136394")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_page_title_en_is_saved_and_persists_after_136394(page, browser, tmp_path):
    _text_valid(page, browser, "136394", A.LABEL_PAGE_TITLE, "General Manager's Message", locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty Page Title (EN) is rejected on save (ADO-136395)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136395
@pytest.mark.traceability("136395")
@allure.label("pbi", "129397")
@allure.label("testcase", "136395")
@GM_GROUP
@pytest.mark.timeout(300)
def test_empty_page_title_en_is_rejected_on_save_136395(page, browser, tmp_path):
    _text_empty_rejected(page, "136395", A.LABEL_PAGE_TITLE, locale="en", expected_msg='"Page title is required."')


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Page Title (EN) exceeding 100 characters is rejected (ADO-136396)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136396
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_en_exceeding_100_characters_is_rejected_136396(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Title (EN) sanitizes script injection input (ADO-136397)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136397
@pytest.mark.traceability("136397")
@allure.label("pbi", "129397")
@allure.label("testcase", "136397")
@GM_GROUP
@pytest.mark.timeout(300)
def test_page_title_en_sanitizes_script_injection_input_136397(page, browser, tmp_path):
    _script_injection(page, browser, "136397", A.LABEL_PAGE_TITLE)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Page Title (AR) is saved, renders RTL, and persists after reload (ADO-136398)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136398
@pytest.mark.traceability("136398")
@allure.label("pbi", "129397")
@allure.label("testcase", "136398")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_page_title_ar_is_saved_renders_rtl_and_136398(page, browser, tmp_path):
    _text_valid(page, browser, "136398", A.LABEL_PAGE_TITLE, 'رسالة المدير العام', locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Page Title (AR) exceeding 100 characters is rejected (ADO-136399)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136399
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_title_ar_exceeding_100_characters_is_rejected_136399(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Salutation Heading (EN) is saved and persists after reload (ADO-136400)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136400
@pytest.mark.traceability("136400")
@allure.label("pbi", "129397")
@allure.label("testcase", "136400")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_salutation_heading_en_is_saved_and_persists_after_136400(page, browser, tmp_path):
    _text_valid(page, browser, "136400", A.LABEL_SALUTATION, 'Dear members and visitors,', locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty Salutation Heading (EN) is rejected on save (ADO-136401)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136401
@pytest.mark.traceability("136401")
@allure.label("pbi", "129397")
@allure.label("testcase", "136401")
@GM_GROUP
@pytest.mark.timeout(300)
def test_empty_salutation_heading_en_is_rejected_on_save_136401(page, browser, tmp_path):
    _text_empty_rejected(page, "136401", A.LABEL_SALUTATION, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Salutation Heading (EN) exceeding 150 characters is rejected (ADO-136402)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136402
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_en_exceeding_150_characters_is_rejected_136402(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Salutation Heading (EN) sanitizes embedded HTML tags (ADO-136403)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136403
@pytest.mark.traceability("136403")
@allure.label("pbi", "129397")
@allure.label("testcase", "136403")
@GM_GROUP
@pytest.mark.timeout(480)
def test_salutation_heading_en_sanitizes_embedded_html_tags_136403(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Salutation Heading = <b>Dear</b> members", tc_id="136403")
    _p34_markup_case(page, browser, "136403", A.LABEL_SALUTATION, "salutation", "<b>Dear</b> members", "html")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Salutation Heading (AR) is saved, renders RTL, and persists after reload (ADO-136404)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136404
@pytest.mark.traceability("136404")
@allure.label("pbi", "129397")
@allure.label("testcase", "136404")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_salutation_heading_ar_is_saved_renders_rtl_and_136404(page, browser, tmp_path):
    _text_valid(page, browser, "136404", A.LABEL_SALUTATION, 'أعزاءنا الأعضاء والزوار،', locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Salutation Heading (AR) exceeding 150 characters is rejected (ADO-136405)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136405
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_salutation_heading_ar_exceeding_150_characters_is_rejected_136405(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Name (EN) is saved and persists after reload (ADO-136406)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136406
@pytest.mark.traceability("136406")
@allure.label("pbi", "129397")
@allure.label("testcase", "136406")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_gm_name_en_is_saved_and_persists_after_136406(page, browser, tmp_path):
    _text_valid(page, browser, "136406", A.LABEL_GM_NAME, 'Ahmed Al-Kuwari', locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty GM Name (EN) is rejected on save (ADO-136407)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136407
@pytest.mark.traceability("136407")
@allure.label("pbi", "129397")
@allure.label("testcase", "136407")
@GM_GROUP
@pytest.mark.timeout(300)
def test_empty_gm_name_en_is_rejected_on_save_136407(page, browser, tmp_path):
    _text_empty_rejected(page, "136407", A.LABEL_GM_NAME, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Name (EN) exceeding 100 characters is rejected (ADO-136408)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136408
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_en_exceeding_100_characters_is_rejected_136408(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Name (EN) sanitizes embedded HTML tags (ADO-136409)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136409
@pytest.mark.traceability("136409")
@allure.label("pbi", "129397")
@allure.label("testcase", "136409")
@GM_GROUP
@pytest.mark.timeout(480)
def test_gm_name_en_sanitizes_embedded_html_tags_136409(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "GM Name = <b>Ahmed</b>", tc_id="136409")
    _p34_markup_case(page, browser, "136409", A.LABEL_GM_NAME, "name", "<b>Ahmed</b>", "html")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Name (AR) is saved, renders RTL, and persists after reload (ADO-136410)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136410
@pytest.mark.traceability("136410")
@allure.label("pbi", "129397")
@allure.label("testcase", "136410")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_gm_name_ar_is_saved_renders_rtl_and_136410(page, browser, tmp_path):
    _text_valid(page, browser, "136410", A.LABEL_GM_NAME, 'أحمد الكواري', locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Name (AR) exceeding 100 characters is rejected (ADO-136411)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136411
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_name_ar_exceeding_100_characters_is_rejected_136411(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Designation (EN) is saved and persists after reload (ADO-136412)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136412
@pytest.mark.traceability("136412")
@allure.label("pbi", "129397")
@allure.label("testcase", "136412")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_gm_designation_en_is_saved_and_persists_after_136412(page, browser, tmp_path):
    _text_valid(page, browser, "136412", A.LABEL_DESIGNATION, 'Acting General Manager', locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty GM Designation (EN) is rejected on save (ADO-136413)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136413
@pytest.mark.traceability("136413")
@allure.label("pbi", "129397")
@allure.label("testcase", "136413")
@GM_GROUP
@pytest.mark.timeout(300)
def test_empty_gm_designation_en_is_rejected_on_save_136413(page, browser, tmp_path):
    _text_empty_rejected(page, "136413", A.LABEL_DESIGNATION, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Designation (EN) exceeding 100 characters is rejected (ADO-136414)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136414
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_en_exceeding_100_characters_is_rejected_136414(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that GM Designation (EN) sanitizes script injection input (ADO-136415)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136415
@pytest.mark.traceability("136415")
@allure.label("pbi", "129397")
@allure.label("testcase", "136415")
@GM_GROUP
@pytest.mark.timeout(480)
def test_gm_designation_en_sanitizes_script_injection_input_136415(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "GM Designation = img onerror payload", tc_id="136415")
    _p34_markup_case(page, browser, "136415", A.LABEL_DESIGNATION, "designation",
                     "<img src=x onerror=alert(1)>", "script")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Designation (AR) is saved, renders RTL, and persists after reload (ADO-136416)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136416
@pytest.mark.traceability("136416")
@allure.label("pbi", "129397")
@allure.label("testcase", "136416")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_gm_designation_ar_is_saved_renders_rtl_and_136416(page, browser, tmp_path):
    _text_valid(page, browser, "136416", A.LABEL_DESIGNATION, 'المدير العام بالإنابة', locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a GM Designation (AR) exceeding 100 characters is rejected (ADO-136417)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136417
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_gm_designation_ar_exceeding_100_characters_is_rejected_136417(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that valid rich-text Page Content (EN) with headings, bullets, and a link is saved and persists (ADO-136418)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136418
@pytest.mark.traceability("136418")
@allure.label("pbi", "129397")
@allure.label("testcase", "136418")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_richtext_page_content_en_with_headings_bullets_and_136418(page, browser, tmp_path):
    html = "<h3>QCTEST-136418 Heading</h3><p>QCTEST-136418 first paragraph.</p><ul><li>Item one</li><li>Item two</li><li>Item three</li></ul><p>Second paragraph with <a href=\"https://www.qatarchamber.com/\">an inline link</a>.</p>"
    _content_html_valid(page, browser, "136418", html, "en", ("<h3>", "<ul>", "<li>Item three</li>", "<a href=\"https://www.qatarchamber.com/\""))


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that empty Page Content (EN) is rejected on save (ADO-136419)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136419
@pytest.mark.traceability("136419")
@allure.label("pbi", "129397")
@allure.label("testcase", "136419")
@GM_GROUP
@pytest.mark.timeout(300)
def test_empty_page_content_en_is_rejected_on_save_136419(page, browser, tmp_path):
    _content_empty_rejected(page, "136419", locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) exceeding 5000 characters is rejected (ADO-136420)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136420
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_en_exceeding_5000_characters_is_rejected_136420(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (EN) sanitizes script injection within the rich text editor (ADO-136421)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136421
@pytest.mark.traceability("136421")
@allure.label("pbi", "129397")
@allure.label("testcase", "136421")
@GM_GROUP
@pytest.mark.timeout(300)
def test_page_content_en_sanitizes_script_injection_within_the_rich_136421(page, browser, tmp_path):
    _script_injection(page, browser, "136421", "content")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that valid rich-text Page Content (AR) is saved, renders RTL/bidi correctly, and persists (ADO-136422)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136422
@pytest.mark.traceability("136422")
@allure.label("pbi", "129397")
@allure.label("testcase", "136422")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_richtext_page_content_ar_is_saved_renders_rtlbidi_136422(page, browser, tmp_path):
    html = "<p dir=\"rtl\">QCTEST-136422 رسالة المدير العام إلى الأعضاء.</p><ul><li>البند الأول</li><li>البند الثاني</li></ul><p dir=\"rtl\">لمزيد من المعلومات زوروا <a href=\"https://www.qatarchamber.com/\">Qatar Chamber</a>.</p>"
    _content_html_valid(page, browser, "136422", html, "ar", ("البند الثاني", "<ul>", ">Qatar Chamber</a>"))


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content (AR) exceeding 5000 characters is rejected (ADO-136423)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136423
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_ar_exceeding_5000_characters_is_rejected_136423(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Closing Text (EN) is saved and persists after reload (ADO-136424)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136424
@pytest.mark.traceability("136424")
@allure.label("pbi", "129397")
@allure.label("testcase", "136424")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_signature_closing_text_en_is_saved_and_persists_136424(page, browser, tmp_path):
    _text_valid(page, browser, "136424", A.LABEL_CLOSING, 'Best Regards,', locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an empty Signature Closing Text (EN) is rejected on save (ADO-136425)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136425
@pytest.mark.traceability("136425")
@allure.label("pbi", "129397")
@allure.label("testcase", "136425")
@GM_GROUP
@pytest.mark.timeout(300)
def test_empty_signature_closing_text_en_is_rejected_on_save_136425(page, browser, tmp_path):
    _text_empty_rejected(page, "136425", A.LABEL_CLOSING, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Signature Closing Text (EN) exceeding 50 characters is rejected (ADO-136426)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136426
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_en_exceeding_50_characters_is_rejected_136426(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Signature Closing Text (EN) sanitizes script injection input (ADO-136427)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136427
@pytest.mark.traceability("136427")
@allure.label("pbi", "129397")
@allure.label("testcase", "136427")
@GM_GROUP
@pytest.mark.timeout(480)
def test_signature_closing_text_en_sanitizes_script_injection_input_136427(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Signature Closing Text = img onerror payload", tc_id="136427")
    _p34_markup_case(page, browser, "136427", A.LABEL_CLOSING, "closing",
                     "<img src=x onerror=alert(1)>", "script")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Closing Text (AR) is saved, renders RTL, and persists after reload (ADO-136428)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136428
@pytest.mark.traceability("136428")
@allure.label("pbi", "129397")
@allure.label("testcase", "136428")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_signature_closing_text_ar_is_saved_renders_rtl_136428(page, browser, tmp_path):
    _text_valid(page, browser, "136428", A.LABEL_CLOSING, 'مع خالص التقدير،', locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Signature Closing Text (AR) exceeding 50 characters is rejected (ADO-136429)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136429
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_signature_closing_text_ar_exceeding_50_characters_is_rejected_136429(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Hero Banner (EN) image uploads, saves, and persists (ADO-136430)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136430
@pytest.mark.traceability("136430")
@allure.label("pbi", "129397")
@allure.label("testcase", "136430")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_hero_banner_en_image_uploads_saves_and_persists_136430(page, browser, tmp_path):
    _upload_valid(page, browser, tmp_path, "136430", A.LABEL_HERO, "qctest-hero-500kb.jpg", 500 * 1024)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported Hero Banner (EN) file format is rejected (ADO-136431)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136431
@pytest.mark.traceability("136431")
@allure.label("pbi", "129397")
@allure.label("testcase", "136431")
@GM_GROUP
@pytest.mark.timeout(300)
def test_unsupported_hero_banner_en_file_format_is_rejected_136431(page, browser, tmp_path):
    _upload_rejected(page, tmp_path, "136431", A.LABEL_HERO, "qctest-hero.pdf", 200 * 1024)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a missing Hero Banner (EN) is rejected on save/publish (ADO-136432)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136432
@pytest.mark.traceability("136432")
@allure.label("pbi", "129397")
@allure.label("testcase", "136432")
@GM_GROUP
@pytest.mark.timeout(300)
def test_missing_hero_banner_en_is_rejected_on_savepublish_136432(page, browser, tmp_path):
    _upload_missing_rejected(page, tmp_path, "136432", A.LABEL_HERO)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Hero Banner (AR) image uploads, saves, and persists per language (ADO-136433)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136433
@pytest.mark.traceability("136433")
@allure.label("pbi", "129397")
@allure.label("testcase", "136433")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_hero_banner_ar_image_uploads_saves_and_persists_136433(page, browser, tmp_path):
    _upload_valid(page, browser, tmp_path, "136433", A.LABEL_HERO + AR, "qctest-hero-ar-500kb.png", 500 * 1024, public_locale="ar")  # VERIFY-LIVE: AR attachment label


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Portrait (EN) image uploads, saves, and persists (ADO-136434)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136434
@pytest.mark.traceability("136434")
@allure.label("pbi", "129397")
@allure.label("testcase", "136434")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_gm_portrait_en_image_uploads_saves_and_persists_136434(page, browser, tmp_path):
    _upload_valid(page, browser, tmp_path, "136434", A.LABEL_PORTRAIT, "qctest-portrait-800kb.png", 800 * 1024, public_locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported GM Portrait (EN) file format is rejected (ADO-136435)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136435
@pytest.mark.traceability("136435")
@allure.label("pbi", "129397")
@allure.label("testcase", "136435")
@GM_GROUP
@pytest.mark.timeout(300)
def test_unsupported_gm_portrait_en_file_format_is_rejected_136435(page, browser, tmp_path):
    _upload_rejected(page, tmp_path, "136435", A.LABEL_PORTRAIT, "qctest-portrait.gif", 200 * 1024)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a missing GM Portrait Image (EN) is rejected on save/publish (ADO-136436)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136436
@pytest.mark.traceability("136436")
@allure.label("pbi", "129397")
@allure.label("testcase", "136436")
@GM_GROUP
@pytest.mark.timeout(300)
def test_missing_gm_portrait_image_en_is_rejected_on_savepublish_136436(page, browser, tmp_path):
    _upload_missing_rejected(page, tmp_path, "136436", A.LABEL_PORTRAIT)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid GM Portrait Image (AR) uploads, saves, and persists per language (ADO-136437)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136437
@pytest.mark.traceability("136437")
@allure.label("pbi", "129397")
@allure.label("testcase", "136437")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_gm_portrait_image_ar_uploads_saves_and_persists_136437(page, browser, tmp_path):
    _upload_valid(page, browser, tmp_path, "136437", A.LABEL_PORTRAIT + AR, "qctest-portrait-ar-800kb.jpg", 800 * 1024, public_locale="ar")  # VERIFY-LIVE: AR attachment label


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Avatar (EN) image uploads, saves, and persists (ADO-136438)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136438
@pytest.mark.traceability("136438")
@allure.label("pbi", "129397")
@allure.label("testcase", "136438")
@GM_GROUP
@pytest.mark.timeout(900)
def test_valid_signature_avatar_en_image_uploads_saves_and_persists_136438(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "upload + Save of a Signature Avatar (JPG, 200 KB)", tc_id="136438")
    _p34_avatar_valid(page, browser, tmp_path, "136438", "avatar-136438.jpg", 200 * 1024)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an unsupported Signature Avatar (EN) file format is rejected (ADO-136439)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136439
@pytest.mark.traceability("136439")
@allure.label("pbi", "129397")
@allure.label("testcase", "136439")
@GM_GROUP
@pytest.mark.timeout(480)
def test_unsupported_signature_avatar_en_file_format_is_rejected_136439(page, browser, tmp_path):
    _p34_avatar_rejected(page, tmp_path, "136439", "avatar-136439.bmp", 200 * 1024)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that the page saves and publishes successfully with no Signature Avatar uploaded (ADO-136440)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136440
@pytest.mark.traceability("136440")
@allure.label("pbi", "129397")
@allure.label("testcase", "136440")
@GM_GROUP
@pytest.mark.timeout(480)
def test_the_page_saves_and_publishes_successfully_with_no_signature_136440(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Publish with an empty Signature Avatar (removed first if set)", tc_id="136440")
    _p34_publish_without_avatar(page, browser, "136440")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid Signature Avatar (AR) uploads, saves, and persists per language (ADO-136441)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136441
@pytest.mark.traceability("136441")
@allure.label("pbi", "129397")
@allure.label("testcase", "136441")
@GM_GROUP
@pytest.mark.timeout(900)
def test_valid_signature_avatar_ar_uploads_saves_and_persists_per_136441(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "upload + Save of an AR Signature Avatar (PNG, 200 KB)", tc_id="136441")
    _p34_avatar_valid(page, browser, tmp_path, "136441", "avatar-ar-136441.png", 200 * 1024, locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that valid Image Alt Text (EN) is saved, exposed in HTML, and persists (ADO-136442)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136442
@pytest.mark.traceability("136442")
@allure.label("pbi", "129397")
@allure.label("testcase", "136442")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_image_alt_text_en_is_saved_exposed_in_136442(page, browser, tmp_path):
    _text_valid(page, browser, "136442", A.LABEL_ALT_TEXT, 'Qatar Chamber General Manager Ahmed Al-Kuwari portrait', locale="en", public_check=True)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that empty Image Alt Text (EN) is rejected on save (ADO-136443)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136443
@pytest.mark.traceability("136443")
@allure.label("pbi", "129397")
@allure.label("testcase", "136443")
@GM_GROUP
@pytest.mark.timeout(300)
def test_empty_image_alt_text_en_is_rejected_on_save_136443(page, browser, tmp_path):
    _text_empty_rejected(page, "136443", A.LABEL_ALT_TEXT, locale="en")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Image Alt Text (EN) exceeding 150 characters is rejected (ADO-136444)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136444
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_image_alt_text_en_exceeding_150_characters_is_rejected_136444(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that valid Image Alt Text (AR) is saved and persists per language (ADO-136445)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136445
@pytest.mark.traceability("136445")
@allure.label("pbi", "129397")
@allure.label("testcase", "136445")
@GM_GROUP
@pytest.mark.timeout(300)
def test_valid_image_alt_text_ar_is_saved_and_persists_136445(page, browser, tmp_path):
    _text_valid(page, browser, "136445", A.LABEL_ALT_TEXT, 'صورة المدير العام لغرفة قطر', locale="ar")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a valid hyperlink URL is saved and persists in the message body (ADO-136446)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136446
@pytest.mark.traceability("136446")
@allure.label("pbi", "129397")
@allure.label("testcase", "136446")
@GM_GROUP
@pytest.mark.timeout(900)
def test_valid_hyperlink_url_is_saved_and_persists_in_the_136446(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "Page Content hyperlink https://www.qcci.org save", tc_id="136446")
    _p34_content_link(page, browser, "136446", QCCI_URL, stub_destination=True)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an invalid hyperlink URL is rejected on save (ADO-136447)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136447
@pytest.mark.traceability("136447")
@allure.label("pbi", "129397")
@allure.label("testcase", "136447")
@GM_GROUP
@pytest.mark.timeout(480)
def test_invalid_hyperlink_url_is_rejected_on_save_136447(page, browser, tmp_path):
    _p34_content_bad_link(page, "136447")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that Page Content saves successfully with no hyperlinks present (ADO-136448)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136448
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_page_content_saves_successfully_with_no_hyperlinks_present_136448(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Draft stores the record without publishing (ADO-136449)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136449
@pytest.mark.traceability("136449")
@allure.label("pbi", "129397")
@allure.label("testcase", "136449")
@GM_GROUP
@pytest.mark.timeout(300)
def test_setting_status_to_draft_stores_the_record_without_publishing_136449(page, browser, tmp_path):
    _draft_not_public(page, browser, "136449")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Published makes the page live and shows a bilingual success toast (ADO-136450)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136450
@pytest.mark.traceability("136450")
@allure.label("pbi", "129397")
@allure.label("testcase", "136450")
@GM_GROUP
@pytest.mark.timeout(300)
def test_setting_status_to_published_makes_the_page_live_and_136450(page, browser, tmp_path):
    # Success toast wording/presence is a note, not an assertion (QA ruling).
    _publish_visible(page, browser, "136450", role=ROLE_EDITOR)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that setting Status to Unpublish removes the page from the live site but keeps it editable (ADO-136451)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136451
@pytest.mark.traceability("136451")
@allure.label("pbi", "129397")
@allure.label("testcase", "136451")
@GM_GROUP
@pytest.mark.timeout(300)
def test_setting_status_to_unpublish_removes_the_page_from_the_136451(page, browser, tmp_path):
    _unpublish_removes(page, browser, "136451")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that canceling an in-progress edit discards unsaved changes (ADO-136452)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136452
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_canceling_an_inprogress_edit_discards_unsaved_changes_136452(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a Site Content Author's field update to assigned GM's Message content is stored pending Editor publish (ADO-136454)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129397
@pytest.mark.tc_136454
@pytest.mark.traceability("136454")
@allure.label("pbi", "129397")
@allure.label("testcase", "136454")
@GM_GROUP
@pytest.mark.timeout(300)
def test_site_content_authors_field_update_to_assigned_gms_message_136454(page, browser, tmp_path):
    _author_submits_change(page, browser, "136454", editor_publishes=False)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that publishing is blocked when the Arabic title is missing while Arabic is enabled (ADO-136456)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.bilingual
@pytest.mark.pbi_129397
@pytest.mark.tc_136456
@pytest.mark.traceability("136456")
@allure.label("pbi", "129397")
@allure.label("testcase", "136456")
@GM_GROUP
@pytest.mark.timeout(300)
def test_publishing_is_blocked_when_the_arabic_title_is_missing_136456(page, browser, tmp_path):
    # Every other field stays at its (complete) baseline; only the AR title is blank.
    _text_empty_rejected(page, "136456", A.LABEL_PAGE_TITLE, locale="ar", expected_msg='"Arabic title is required." / "العنوان العربي مطلوب."')


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an image exceeding 2MB is rejected with the exact stated message (ADO-136457)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136457
@pytest.mark.traceability("136457")
@allure.label("pbi", "129397")
@allure.label("testcase", "136457")
@GM_GROUP
@pytest.mark.timeout(300)
def test_image_exceeding_2mb_is_rejected_with_the_exact_stated_136457(page, browser, tmp_path):
    _upload_rejected(page, tmp_path, "136457", A.LABEL_HERO, "hero-banner-2_3mb.jpg", int(2.3 * MB), expected_msg='"Image size must not exceed 2 MB." / "يجب ألا يتجاوز حجم الصورة 2 ميغابايت."', size_case=True)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an image exactly at the 2MB boundary is accepted (ADO-136458)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136458
@pytest.mark.traceability("136458")
@allure.label("pbi", "129397")
@allure.label("testcase", "136458")
@GM_GROUP
@pytest.mark.timeout(480)
def test_image_exactly_at_the_2mb_boundary_is_accepted_136458(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "upload + Save of a 2,097,152-byte Hero Banner", tc_id="136458")
    with _p34_end_published(page, "136458"):  # 79878 is always left Published
        _upload_valid(page, browser, tmp_path, "136458", A.LABEL_HERO, _unique_name("hero-2mb-exact.jpg"), 2 * MB)


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that a text field exactly at its maximum character limit is accepted (ADO-136459)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136459
@pytest.mark.skip(reason=_CMS_LOGIN_BLOCKED)
def test_text_field_exactly_at_its_maximum_character_limit_is_136459(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that an interrupted Publish action does not leave the page in a partially-published state (ADO-136461)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136461
@pytest.mark.traceability("136461")
@allure.label("pbi", "129397")
@allure.label("testcase", "136461")
@GM_GROUP
@pytest.mark.timeout(900)
def test_interrupted_publish_action_does_not_leave_the_page_in_136461(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "interrupted then retried Editor publish", tc_id="136461")
    _p34_interrupted_publish(page, browser, "136461")


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.title("Verify that the outcome is deterministic when two Site Content Editors save the same GM's Message record concurrently (ADO-136462)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136462
@pytest.mark.traceability("136462")
@allure.label("pbi", "129397")
@allure.label("testcase", "136462")
@GM_GROUP
@pytest.mark.timeout(900)
def test_the_outcome_is_deterministic_when_two_site_content_editors_136462(page, browser, tmp_path):
    block_live_singleton_write(GM_RECORD, "two concurrent Editor sessions saving", tc_id="136462")
    _p34_concurrent_edit(page, browser, "136462")


# ===========================================================================
# P3/P4 BATCH -- 2026-10-13 (scripted OFFLINE, NOT executed): the 25 cases of
# .claude/qa-runs/phase3-20261012/129397.p34.todo.json (case text = oracle),
# replacing their former skip stubs above.
#
# USER DECISION 2026-10-13 (P3/P4 batch only): these cases MAY write test
# data to the REAL singleton 79878 (QCDEMO-129397-general-managers-message)
# -- ONLY when the run sets QC_ALLOW_LIVE_SINGLETON_WRITES=1; without it
# block_live_singleton_write() reports them NOT APPLICABLE, unchanged.
# Nothing is ever deleted (no delete action; "Remove file" only where the case
# itself needs an empty optional field -- 136440). Every persisted write is
# logged BEFORE its click to reports/live-writes-20261013.jsonl for the
# user's manual cleanup. Every writing case leaves 79878 Published.
#
# Accounts: TEST_USER (`page`) for plain field / upload cases (module
# convention; no permission is asserted); QC Site Content Editor (fresh
# context) for every lifecycle, audit, session and concurrency case. Public
# checks: a fresh logged-out context. Wording / toasts are attached, never
# asserted (bug-rules).
# ===========================================================================
import hashlib as _hashlib
import re as _re
import uuid as _uuid
from contextlib import contextmanager as _contextmanager

P34_BUDGET = 480  # = the tests' @timeout
# Fix pass 7 (2026-10-14): the avatar, hyperlink, interrupted-publish and
# concurrency helpers sign in extra sessions, unpublish, save, poll the public
# page and re-publish; 480 s left the main path 370 s, too tight. Their tests
# carry @timeout(900) -- the marker and this budget must stay equal, since a
# pytest-timeout hard exit on Windows skips the `finally` that re-publishes.
P34_LONG_BUDGET = 900
QC_URL = "https://www.qatarchamber.com"
QCCI_URL = "https://www.qcci.org"
CONFLICT_RE = _re.compile(r"conflict|modified by another|has been (changed|updated)|newer version|stale", _re.I)
ROLE_CONFIG_DESC = (
    "Liferay role 'QC Site Content Editor' permission set (shared role configuration, "
    "not a content record)"
)


def _run_marker(tc: str) -> str:
    """`QCTEST-<tc>-<run>` -- unique per run, so a rerun never finds the
    previous run's value already in place (a no-op save would pass or fail
    for the wrong reason). `_strip_qctest` still removes older runs' text."""
    return f"QCTEST-{tc}-{_uuid.uuid4().hex[:6]}"


def _unique_name(name: str) -> str:
    """`<stem>-<run><ext>`: an upload no earlier run (or D&M dedupe) can match."""
    return f"{_Path(name).stem}-{_uuid.uuid4().hex[:6]}{_Path(name).suffix}"


def _lw(tc: str, field: str, value, action: str, note: str = "") -> None:
    log_live_write(GM_RECORD, field, value, tc, action=action, note=note)


def _p34_restore_published(page, tc: str) -> str:
    """Best effort: drive 79878 back to Published (documented transitions,
    logged first). Returns "" on success, else the problem."""
    try:
        admin = A(page)
        status = list_status(_workflow_list(admin), GM_MESSAGE_ENTRY_CODE)
        if status != STATUS_PUBLISHED:
            _lw(tc, "<workflow>", STATUS_PUBLISHED, "publish", f"end state: leave 79878 Published (was {status})")
            drive_to_published(_workflow_list(admin), GM_MESSAGE_ENTRY_CODE,
                               lambda: admin.submit_publish(admin.open_record("en")),
                               budget=PUBLISH_WAIT * 2)
        return ""
    except Exception as exc:  # noqa: BLE001 -- reported by the caller
        _attach("END STATE NOT RESTORED -- check GM Message 79878 by hand", repr(exc))
        _log.error("tc_%s: 79878 not left Published: %r", tc, exc)
        return repr(exc)


@_contextmanager
def _p34_end_published(page, tc: str):
    """Wraps a writing case: 79878 is always driven back to Published. A
    failed restore never masks the case's own failure; on a passing case it
    fails the test (the live page is not Published)."""
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        problem = _p34_restore_published(page, tc)
        if problem and not failed:
            raise AssertionError(f"the case passed but GM Message 79878 was not left Published: {problem}")


def _strip_qctest(html: str, tc: str) -> str:
    """Drops earlier runs' `<p>...QCTEST-<tc>...</p>` paragraphs, so a rerun
    does not stack test paragraphs on the live record."""
    return _re.sub(rf"<p[^>]*>(?:(?!</p>).)*QCTEST-{tc}(?:(?!</p>).)*</p>\s*", "", html or "", flags=_re.S)


def _p34_public_content(public) -> dict:
    return {
        "title": public.title_text().strip(),
        "name": public.portrait_name_text().strip(),
        "designation": public.portrait_designation_text().strip(),
        "salutation": public.salutation_text().strip(),
        "body": public.body_text().strip(),
    }


# ---- uploads ---------------------------------------------------------------
def _p34_picker_accepts(page, tmp_path, tc: str, label: str, name: str, size: int) -> None:
    """The picker accepts the file with no size / format error. The case has
    no Save step, so nothing is saved: the form is left without saving."""
    snap = _snapshot(page, writes=(f"file:{label}",), budget=P34_BUDGET)
    admin = A(page)
    path = _fixture(tmp_path, name, size)
    with allure.step(f"Upload {name} ({size} bytes) as {label!r}"):
        authoring = admin.open_record("en")
        rejected = authoring.upload_file_expect_rejected(label, path)
        refusal = admin.refusal_text()
        _attach("picker outcome (wording is a note)", {"rejected": rejected, "refusal": refusal})
    with allure.step("Leave the form without saving: the stored image is unchanged"):
        current = admin.open_record("en").current_file_name(label)
    assert not rejected, f"{label!r} refused a file of exactly {size} bytes ({name})"
    assert not _re.search(r"size|حجم", refusal or "", _re.I), f"a size error was shown: {refusal!r}"
    assert _same_file(current, snap[f"file:{label}"] or ""), f"{label!r} changed to {current!r} without a Save"


def _p34_avatar_valid(page, browser, tmp_path, tc: str, name: str, size: int, locale: str = "en") -> None:
    """Optional Signature Avatar: uploads, Save (publish), persists on reopen,
    and the public `locale` page's signature block shows it instead of the
    default placeholder. `signatureAvatar` is ONE non-localized field
    (liferay-context.md): an AR case needs an AR control, which is checked
    BEFORE anything is written."""
    _snapshot(page, budget=P34_LONG_BUDGET)
    admin = A(page)
    name = _unique_name(name)
    field = A.LABEL_AVATAR + (AR if locale == "ar" else "")
    admin.open_record("en")
    if not admin.has_file_field(field):
        pytest.fail(
            f"FINDING -- the GM Message form renders no {field!r} attachment control. "
            "signatureAvatar is a single non-localized attachment (liferay-context.md), so a "
            f"{locale.upper()}-specific avatar cannot be configured as the case requires. "
            "Nothing was written.", pytrace=False)
    path = _fixture(tmp_path, name, size)
    anon_ctx = None
    with _p34_end_published(page, tc):
        try:
            with allure.step(f"Upload {name} ({size // 1024} KB) as {field!r} and click Save"):
                authoring = _editable(admin.open_record("en"))
                _lw(tc, field, name, "upload", "case step 1, then Save (publish)")
                authoring.upload_file(field, path)
                refusal = admin.refusal_text()
                status = _publish(admin, authoring)
            assert not refusal, f"the valid avatar upload showed an error: {refusal!r}"
            assert status == STATUS_PUBLISHED, f"the save did not commit ({status!r})"
            with allure.step("Reload the record"):
                admin.open_record("en")
                current = admin.current_file_name_or_empty(field)
            assert _same_file(current, name), f"{field!r} holds {current!r}, expected {name!r}"
            anon_ctx, public = _anon(browser)
            # FIX PASS 7 (2026-10-14): the avatar is served by a FIELD-keyed
            # endpoint (`/o/qc-newsletter/gm-asset?field=signatureAvatar`), so
            # the file name is never in `src` (the old `stem in src` check
            # could not pass). Proof that THIS upload displays: the visitor's
            # <img> decoded (naturalWidth > 0), the default icon is gone, and
            # the bytes the endpoint serves anonymously are the uploaded file.
            want = _hashlib.sha256(_Path(path).read_bytes()).hexdigest()
            seen = {}

            def _shows_upload(p) -> bool:
                info = p.signature_avatar_image()
                seen.clear()
                seen.update(info, default_icon=p.signature_avatar_has_default_icon())
                if not info["present"] or not info["src"]:
                    return False
                resp = p.page.context.request.get(info["src"])
                body = resp.body() if resp.ok else b""
                seen.update(http=resp.status, content_type=resp.headers.get("content-type", ""),
                            served_bytes=len(body), served_sha256=_hashlib.sha256(body).hexdigest(),
                            uploaded_bytes=size, uploaded_sha256=want)
                return seen["served_sha256"] == want

            with allure.step(f"View the published {locale.upper()} page: the signature block shows the avatar"):
                shown = _public_shows(public, _shows_upload, locale)
            _attach("public signature avatar (anonymous visitor)", seen)
            assert seen.get("present"), f"the {locale} signature block renders no avatar <img>: {seen}"
            assert not seen.get("default_icon"), "the default placeholder still shows instead of the uploaded avatar"
            assert seen.get("complete") and seen.get("natural_width", 0) > 0, (
                f"the avatar <img> did not load in the visitor's browser: {seen}")
            assert seen.get("http") == 200 and str(seen.get("content_type", "")).startswith("image/"), (
                f"the avatar endpoint does not serve an image: {seen}")
            assert shown, f"the {locale} signature block serves an image that is not the uploaded {name!r}: {seen}"
        finally:
            _close(anon_ctx)


def _p34_avatar_rejected(page, tmp_path, tc: str, name: str, size: int) -> None:
    """Unsupported avatar format: refused at the picker, nothing saved."""
    _snapshot(page, budget=P34_BUDGET)
    admin = A(page)
    label = A.LABEL_AVATAR
    authoring = admin.open_record("en")
    before = admin.current_file_name_or_empty(label)
    with allure.step(f"Attempt to upload {name} as {label!r}"):
        rejected = authoring.upload_file_expect_rejected(label, _fixture(tmp_path, name, size))
        _attach("rejection shown (wording is a note)", admin.refusal_text())
    with allure.step("Reopen without saving: the avatar is unchanged"):
        after = admin.open_record("en")
        current, status = admin.current_file_name_or_empty(label), after.current_status()
    assert rejected, f"{label!r} accepted an unsupported file ({name})"
    assert _same_file(current, before), f"{label!r} changed from {before!r} to {current!r}"
    assert status == STATUS_PUBLISHED, f"record status changed to {status!r}"


def _p34_publish_without_avatar(page, browser, tc: str) -> None:
    """136440: Signature Avatar empty + every mandatory field filled ->
    Publish succeeds; the live page shows the default placeholder. An avatar
    left by an earlier case is removed first (the case requires the field
    empty) -- logged, then saved on its own (two-phase remove, see
    ObjectAuthoringPage.remove_current_file)."""
    _snapshot(page, budget=P34_BUDGET)
    admin = A(page)
    label = A.LABEL_AVATAR
    anon_ctx = None
    with _p34_end_published(page, tc):
        try:
            authoring = _editable(admin.open_record("en"))
            current = admin.current_file_name_or_empty(label)
            if current:
                with allure.step(f"Precondition: Signature Avatar holds {current!r} -- remove it and save"):
                    _lw(tc, label, f"removed {current}", "remove-file", "case precondition: the avatar must be empty")
                    authoring.remove_current_file(label)
                    _save_draft(authoring)
                    authoring = admin.open_record("en")
            with allure.step("Leave Signature Avatar empty, all other mandatory fields filled, click Publish"):
                _lw(tc, "<form>", "Publish with Signature Avatar empty", "publish", "case step 1")
                admin.submit_publish(authoring)
                refusal = admin.refusal_text()
                status = _drive_published(admin)
            with allure.step("Reload the record"):
                admin.open_record("en")
                stored = admin.current_file_name_or_empty(label)
            assert not refusal, f"Publish without an avatar was refused: {refusal!r}"
            assert status == STATUS_PUBLISHED, f"the record is {status!r} after Publish"
            assert stored == "", f"Signature Avatar is not empty: {stored!r}"
            anon_ctx, public = _anon(browser)
            with allure.step("The live page shows the default placeholder in the signature block"):
                placeholder = _public_shows(public, lambda p: p.signature_avatar_has_default_icon())
            assert placeholder, "the default (gold circle) placeholder is not shown in the signature block"
        finally:
            _close(anon_ctx)


# ---- rich-text hyperlinks ----------------------------------------------------
def _p34_content_link(page, browser, tc: str, url: str, stub_destination: bool = False) -> None:
    """A hyperlink in Page Content (EN): saved, stored on reload, rendered on
    the published page with the configured target, and clickable.

    `stub_destination` (fix pass 7, 2026-10-14, TC 136446): the case's own
    URL https://www.qcci.org is unreachable from the test network (curl times
    out after 20 s; bug-verification-p3-20261013.md row 7), so a real click
    never commits a navigation there. The visitor context answers that host
    locally (the dynamic-widgets `anon` fixture's precedent): the click is
    then proved to navigate to the configured URL, in the tab its `target`
    says, without depending on a third-party site being up."""
    snap = _snapshot(page, writes=("content_en",), budget=P34_LONG_BUDGET)
    admin = A(page)
    text = f"{_run_marker(tc)} link"
    link = f'<p><a href="{url}">{text}</a></p>'
    anon_ctx = None
    with _p34_end_published(page, tc):
        try:
            with allure.step(f"Insert a hyperlink to {url} into Page Content (EN) and click Save"):
                authoring = _editable(admin.open_record("en"))
                admin.set_page_content_html(_strip_qctest(snap["content_en"], tc) + link, "en")
                _lw(tc, "Page Content (EN)", link + " appended", "publish", "case step 1")
                admin.submit_publish(authoring)
                refusal = admin.refusal_text()
                status = _drive_published(admin)
            with allure.step("Reload the record"):
                admin.open_record("en")
                stored = admin.page_content_html("en")
            assert not refusal, f"the save was refused: {refusal!r}"
            assert status == STATUS_PUBLISHED, f"the save did not publish ({status!r})"
            assert f'href="{url}"' in stored, f"the link is not stored: {stored[-400:]!r}"
            anon_ctx, public = _anon(browser)
            with allure.step("View the published page: the link is retained and targeted"):
                shown = _public_shows(public, lambda p: p.body_link(url)["count"] > 0)
                info = public.body_link(url)
            _attach("rendered link", info)
            assert shown, f"the published page has no link to {url}"
            assert info["href"].rstrip("/") == url.rstrip("/"), f"the link targets {info['href']!r}"
            assert info["text"] == text, f"the link label reads {info['text']!r}"
            if stub_destination:
                host = _re.escape(url.split("://", 1)[1].split("/", 1)[0].removeprefix("www."))
                anon_ctx.route(_re.compile(rf"https?://(www\.)?{host}(/.*)?$"),
                               lambda r: r.fulfill(status=200, content_type="text/html",
                                                   body="<html><body>QCTEST external target</body></html>"))
                _attach("note", f"{url} is unreachable from the test network; the visitor context answers it "
                                "locally, so the click proves the navigation target, not the third-party site")
            with allure.step("Click the link"):
                went = public.follow_body_link(url)
            _attach("click outcome (configured open behaviour = the anchor's target)", {**went, "target": info["target"]})
            assert went["url"] and "general-managers-message" not in went["url"], (
                f"clicking the link did not navigate away: {went}")
            if stub_destination:
                assert went["url"].rstrip("/") == url.rstrip("/"), f"the click navigated to {went['url']!r}, not {url}"
            assert went["new_tab"] == (info["target"] == "_blank"), (
                f"the link opened {'a new tab' if went['new_tab'] else 'in the same tab'} but its "
                f"configured target is {info['target']!r}")
        finally:
            _close(anon_ctx)


def _p34_content_bad_link(page, tc: str) -> None:
    """136447: a hyperlink with target "not-a-url" in Page Content is refused
    on Save ("Please enter a valid URL." -- wording attached) and nothing is
    stored. Inserted through CKEditor's data API (the editor's own Link
    dialog is VERIFY-LIVE); the save is the form's Publish control on the
    Published record, as every GM refusal case does."""
    snap = _snapshot(page, writes=("content_en",), budget=P34_BUDGET)
    admin = A(page)
    bad = f'<p><a href="not-a-url">{_run_marker(tc)} bad link</a></p>'
    with allure.step('Insert a hyperlink with target "not-a-url" inside Page Content and click Save'):
        authoring = admin.open_record("en")
        admin.set_page_content_html(_strip_qctest(snap["content_en"], tc) + bad, "en")
        _lw(tc, "Page Content (EN)", bad + " appended", "attempt", "case step 1: expected to be REFUSED")
        admin.submit_publish(authoring)
        refusal = admin.refusal_text()
        _attach("validation shown (expected 'Please enter a valid URL.'; wording is a note)", refusal)
    with allure.step("Reopen: nothing persisted"):
        after = admin.open_record("en")
        stored, status = admin.page_content_html("en"), after.current_status()
    stop_unless_refused('href="not-a-url"' not in stored and status == STATUS_PUBLISHED, GM_RECORD,
                        'Save with a "not-a-url" hyperlink in Page Content',
                        {"refusal": refusal, "status": status})
    assert refusal, 'no "Please enter a valid URL." error was displayed'
    assert 'href="not-a-url"' not in stored, "the invalid link was stored"
    assert status == STATUS_PUBLISHED, f"record status changed to {status!r}"


# ---- sanitization --------------------------------------------------------------
def _p34_markup_case(page, browser, tc: str, label: str, key: str, value: str, kind: str) -> None:
    """`value` saved in `label` (EN) renders on the live page with the markup
    stripped / escaped: kind "html" -> no <b>/<strong> element and no raw tag
    text; kind "script" -> no element with an onerror handler, no injected
    <img>, and no dialog fired. A refused save is reported as a finding (the
    case expects the save to go through)."""
    snap = _snapshot(page, writes=(label,), budget=P34_BUDGET)
    admin = A(page)
    anon_ctx = None
    with _p34_end_published(page, tc):
        try:
            anon_ctx, public = _anon(browser)
            if snap[label] == value:
                # A rerun: the field already holds the case's value, so the
                # live page would never change. An interim QCTEST value is
                # published first (logged), as _text_valid does.
                interim = _run_marker(tc)
                with allure.step(f"Interim write: {label} already reads {value!r}"):
                    authoring = _editable(admin.open_record("en"))
                    authoring.fill_text(label, interim)
                    _lw(tc, f"{label} (EN)", interim, "publish", "interim value (rerun)")
                    admin.submit_publish(authoring)
                    _drive_published(admin)
                _public_shows(public, lambda p: any(interim in t for t in p.field_nodes_text(key)))
            dialogs = public.watch_dialogs()
            with allure.step("The live page before the change"):
                public.open_gm_message("en")
                before = public.field_nodes_html(key)
            with allure.step(f"Enter {value!r} in {label} (EN) and click Save"):
                authoring = _editable(admin.open_record("en"))
                authoring.fill_text(label, value)
                _lw(tc, f"{label} (EN)", value, "publish", "case step 1")
                admin.submit_publish(authoring)
                refusal = admin.refusal_text()
                status = _drive_published(admin)
            assert not refusal, (
                f"FINDING: the save was refused ({refusal!r}); the case expects {value!r} to be saved "
                "and rendered sanitized")
            assert status == STATUS_PUBLISHED, f"the save did not publish ({status!r})"
            with allure.step("Open the live page as a visitor"):
                reached = _public_shows(public, lambda p: p.field_nodes_html(key) != before)
                html, texts = public.field_nodes_html(key), public.field_nodes_text(key)
                onerror = public.onerror_node_count()
            _attach("rendered field", {"html": html, "text": texts, "onerror_nodes": onerror, "dialogs": dialogs})
            assert reached, f"the saved {label} never reached the live page"
            if kind == "html":
                assert not public.field_nodes_have_markup(key, ("b", "strong")), (
                    f"the embedded tags were rendered as bold markup: {html}")
                assert not any("<b>" in t or "</b>" in t for t in texts), f"raw tag text is displayed: {texts}"
                plain = _re.sub(r"<[^>]+>", "", value).strip()
                assert any(plain in t for t in texts), f"the sanitized text {plain!r} is not displayed: {texts}"
            else:
                assert not dialogs, f"the injected script executed: {dialogs}"
                assert onerror == 0, f"{onerror} element(s) with an onerror handler rendered on the page"
                assert not public.field_nodes_have_markup(key, ("img", "script")), (
                    f"the injected element was rendered as markup: {html}")
        finally:
            _close(anon_ctx)


# ---- lifecycle / audit / session / concurrency -----------------------------------
def _p34_republish_after_unpublish(page, browser, tc: str) -> None:
    """135509: Unpublish (offline), then Publish again at once (live, all the
    original content intact). As Site Content Editor."""
    snap = _snapshot(page, writes=(A.LABEL_GM_NAME,), budget=P34_BUDGET)
    e_ctx = anon_ctx = None
    with _p34_end_published(page, tc):
        try:
            e_ctx, editor_page = _role_session(browser, ROLE_EDITOR)
            editor = A(editor_page)
            anon_ctx, public = _anon(browser)
            with allure.step("Before: the live page as a visitor"):
                live = _public_shows(public, lambda p: bool(p.title_text().strip()))
                before = _p34_public_content(public)
            assert live, "precondition: the GM Message page is not live"
            with allure.step("As Site Content Editor, Unpublish the live record"):
                _lw(tc, "<workflow>", "Unpublished", "unpublish", "case step 1")
                drive_to_editable(_workflow_list(editor), GM_MESSAGE_ENTRY_CODE, budget=_budget(PUBLISH_WAIT))
            name = snap[A.LABEL_GM_NAME]
            offline = _public_shows(public, lambda p: name not in p.page_text())
            with allure.step("Immediately click Publish again on the same record"):
                _lw(tc, "<workflow>", STATUS_PUBLISHED, "publish", "case step 2")
                editor.open_list("en").publish_entry(GM_MESSAGE_ENTRY_CODE, comment=f"QCTEST-{tc} republish")
                editor.open_record("en").wait_for_status(STATUS_PUBLISHED, timeout=_budget(PUBLISH_WAIT))
                status = list_status(_workflow_list(editor), GM_MESSAGE_ENTRY_CODE)
            restored = _public_shows(public, lambda p: _p34_public_content(p) == before)
            after = _p34_public_content(public)
            _attach("public content before / after", {"before": before, "after": after})
            assert offline, "the page did not go offline after Unpublish"
            assert status == STATUS_PUBLISHED, f"the record is {status!r} after Publish"
            assert restored, f"the republished page differs from the original: {after} vs {before}"
        finally:
            _close(anon_ctx, e_ctx)


def _is_publish_entry(entry: dict) -> bool:
    blob = " ".join(str(v) for v in entry.values()).casefold()
    return ("publish" in blob or "approv" in blob) and "unpublish" not in blob


def _p34_double_click_publish(page, browser, tc: str) -> None:
    """135512: two rapid clicks on Publish -> published exactly once; the
    History trail (the record's audit of workflow moves) gains ONE publish.
    The Liferay audit portlet rows are attached as supporting evidence."""
    _snapshot(page, budget=P34_BUDGET)
    admin = A(page)
    e_ctx = None
    with _p34_end_published(page, tc):
        try:
            e_ctx, editor_page = _role_session(browser, ROLE_EDITOR)
            editor = A(editor_page)
            with allure.step("Precondition: the record is Unpublished, so its row offers Publish"):
                _lw(tc, "<workflow>", "Unpublished", "unpublish", "precondition: a Publish control to click")
                drive_to_editable(_workflow_list(editor), GM_MESSAGE_ENTRY_CODE, budget=_budget(PUBLISH_WAIT))
            with allure.step("Before: History trail and audit rows"):
                hist_before = editor.open_list("en").history_entries(GM_MESSAGE_ENTRY_CODE)
                admin.open_list("en")
                entry_id = admin.row_entry_id()
                audit_before = admin.audit_rows_for(entry_id)
            with allure.step("Click Publish twice in rapid succession"):
                _lw(tc, "<workflow>", STATUS_PUBLISHED, "publish", "case step 1: double-click")
                editor.open_list("en")
                editor.double_click_row_action("publish", comment=f"QCTEST-{tc} double-click")
                editor.open_record("en").wait_for_status(STATUS_PUBLISHED, timeout=_budget(PUBLISH_WAIT))
                status = list_status(_workflow_list(editor), GM_MESSAGE_ENTRY_CODE)
            with allure.step("After: History trail and audit rows"):
                hist_after = editor.open_list("en").history_entries(GM_MESSAGE_ENTRY_CODE)
                audit_after = admin.audit_rows_for(entry_id)
            new_hist = hist_after[len(hist_before):]
            publishes = [h for h in new_hist if _is_publish_entry(h)]
            _attach("new History entries", new_hist)
            _attach("new audit rows (supporting)", audit_after[: max(len(audit_after) - len(audit_before), 0)])
            assert status == STATUS_PUBLISHED, f"the record is {status!r} after the double click"
            assert len(publishes) == 1, f"expected ONE publish event, the History recorded {len(publishes)}: {new_hist}"
        finally:
            _close(e_ctx)


def _p34_publish_audit(page, browser, tc: str) -> None:
    """136390: an Editor publish leaves an audit entry with the Editor's
    identity, the action and a timestamp -- read on the row's History trail
    (strongest evidence, standards.md) and on the Liferay audit portlet."""
    _snapshot(page, writes=(A.LABEL_SALUTATION,), budget=P34_BUDGET)
    admin = A(page)
    marker = f"{_run_marker(tc)} audit"
    e_ctx = None
    with _p34_end_published(page, tc):
        try:
            e_ctx, editor_page = _role_session(browser, ROLE_EDITOR)
            editor = A(editor_page)
            with allure.step("Before: History trail, audit rows, the Editor's user id"):
                hist_before = editor.open_list("en").history_entries(GM_MESSAGE_ENTRY_CODE)
                editor_id = editor.current_user_id()
                admin.open_list("en")
                entry_id = admin.row_entry_id()
                audit_before = admin.audit_rows_for(entry_id)
            with allure.step("As Site Content Editor, publish a change to the GM's Message page"):
                authoring = _editable(editor.open_record("en"))
                authoring.fill_text(A.LABEL_SALUTATION, marker)
                _lw(tc, "Salutation Heading (EN)", marker, "publish", "case step 1")
                status = _publish(editor, authoring)
            assert status == STATUS_PUBLISHED, f"the publish did not commit ({status!r})"
            with allure.step("Open the audit log for this page record"):
                hist_after = editor.open_list("en").history_entries(GM_MESSAGE_ENTRY_CODE)
                audit_after = admin.audit_rows_for(entry_id)
            new_hist = hist_after[len(hist_before):]
            new_audit = audit_after[: max(len(audit_after) - len(audit_before), 0)]
            _attach("new History entries", new_hist)
            _attach("new audit rows", new_audit)
            publishes = [h for h in new_hist if _is_publish_entry(h)]
            assert publishes, f"no new Published entry in the record's History: {new_hist}"
            newest = publishes[-1]
            by_editor = ("editor" in " ".join(newest.values()).casefold()
                         or any(r[0] == editor_id for r in new_audit))
            assert by_editor, f"the publish entry does not identify the Editor (user {editor_id}): {newest}, {new_audit}"
            assert newest.get("when"), f"the publish entry carries no timestamp: {newest}"  # VERIFY-LIVE: format
        finally:
            _close(e_ctx)


def _p34_expired_session(page, browser, tc: str) -> None:
    """136380: the Editor's session expires mid-edit (this context's cookies
    cleared -- never a server logout); Save asks for re-authentication and
    the unsaved change is not committed."""
    snap = _snapshot(page, writes=(A.LABEL_SALUTATION,), budget=P34_BUDGET)
    marker = f"{_run_marker(tc)} unsaved after expiry"
    e_ctx = None
    with _p34_end_published(page, tc):
        try:
            e_ctx, editor_page = _role_session(browser, ROLE_EDITOR)
            editor = A(editor_page)
            with allure.step("Log in as Site Content Editor and open the GM's Message edit form"):
                authoring = _editable(editor.open_record("en"))
                loaded = authoring.field_value(A.LABEL_SALUTATION)
            assert loaded == snap[A.LABEL_SALUTATION], f"the form loaded {loaded!r}, not the current value"
            with allure.step("Edit, force-expire the session, then click Save"):
                authoring.fill_text(A.LABEL_SALUTATION, marker)
                e_ctx.clear_cookies()
                _lw(tc, "Salutation Heading (EN)", marker, "attempt",
                    "case step 2: session expired -- expected NOT to be committed")
                editor.click_publish_control()
                reauth = editor.reauth_prompt_shown()
                _attach("page after the expired-session Save", {"url": editor.page.url, "body": editor.body_text()[:600]})
            with allure.step("Fresh read of the record (admin session)"):
                stored = A(page).open_record("en").field_value(A.LABEL_SALUTATION)
            assert reauth, "the user was not prompted to re-authenticate after the session expired"
            assert stored != marker, "the unsaved change was committed without a valid session"
        finally:
            _close(e_ctx)


def _p34_role_change_mid_session(page, browser, tc: str) -> None:
    """136381: the Editor's session is open; an Administrator would then
    revoke the Editor role's publish permission. That revocation changes
    SHARED Liferay role configuration (every session using the account),
    which is outside the four records the user approved on 2026-10-13, and no
    Roles-admin locators have been extracted. The step is a hard stop
    ("BLOCKED -- user decision needed") the opt-in variable cannot open."""
    e_ctx = None
    try:
        e_ctx, editor_page = _role_session(browser, ROLE_EDITOR)
        editor = A(editor_page)
        with allure.step("The Editor's session is open on the GM's Message record"):
            editor.open_record("en")
            editor.open_list("en")
            actions = sorted(editor.row_actions())
            _attach("row actions offered to the Editor before the change", actions)
        with allure.step("An Administrator revokes the Editor's publish permission (separate session)"):
            # Not NOT-APPLICABLE: the case is executable once the user decides.
            # The opt-in variable never reaches this line's outcome.
            pytest.fail(
                f"BLOCKED -- user decision needed (tc_{tc}): revoking the publish permission of "
                f"{ROLE_CONFIG_DESC} edits shared Liferay role configuration -- not one of the 4 "
                "records approved for live writes on 2026-10-13, and it affects every session on "
                "the Editor account -- and no Roles-admin locators have been extracted. "
                f"Editor row actions before the change: {actions}",
                pytrace=False,
            )
    finally:
        _close(e_ctx)


def _p34_interrupted_publish(page, browser, tc: str) -> None:
    """136461: Publish with the request cut before it completes -> status
    unchanged, nothing partial stored or visible; a retry publishes it all."""
    _snapshot(page, writes=(A.LABEL_SALUTATION,), budget=P34_LONG_BUDGET)
    marker = f"{_run_marker(tc)} interrupted publish"
    e_ctx = anon_ctx = None
    with _p34_end_published(page, tc):
        try:
            e_ctx, editor_page = _role_session(browser, ROLE_EDITOR)
            editor = A(editor_page)
            anon_ctx, public = _anon(browser)
            with allure.step("Precondition: the record is editable; note its status"):
                _editable(editor.open_record("en"))
                prior = list_status(_workflow_list(editor), GM_MESSAGE_ENTRY_CODE)
            with allure.step("As Site Content Editor, click Publish and cut the network before the toast"):
                authoring = editor.open_record("en")
                authoring.fill_text(A.LABEL_SALUTATION, marker)
                _lw(tc, "Salutation Heading (EN)", marker, "attempt",
                    "case step 1: request cut -- expected NOT to complete")
                cut = editor.submit_publish_with_network_cut()
                _attach("write requests cut (method, url)", cut)
            assert cut, ("AUTOMATION -- no write request to this site was cut, so the interruption was not "
                         "simulated; nothing is concluded about the product")
            with allure.step("After reconnecting: the record's status and stored value"):
                after = list_status(_workflow_list(editor), GM_MESSAGE_ENTRY_CODE)
                stored = editor.open_record("en").field_value(A.LABEL_SALUTATION)
                leaked = _public_shows(public, lambda p: marker in p.page_text(), timeout=20)
                history = editor.open_list("en").history_entries(GM_MESSAGE_ENTRY_CODE)[-5:]
            _attach("after the cut", {"prior": prior, "status": after, "stored salutation": stored,
                                      "visible to a visitor": leaked, "last History entries": history})
            assert after == prior, f"FINDING -- the status moved from {prior!r} to {after!r} on an interrupted publish"
            assert stored != marker, (
                f"FINDING -- every write request was cut ({len(cut)}), yet the change is stored: {stored!r}")
            assert not leaked, "FINDING -- content from the interrupted publish is visible to a visitor"
            with allure.step("Retry Publish"):
                authoring = editor.open_record("en")
                authoring.fill_text(A.LABEL_SALUTATION, marker)
                _lw(tc, "Salutation Heading (EN)", marker, "publish", "case step 3: retry")
                status = _publish(editor, authoring)
            assert status == STATUS_PUBLISHED, f"the retried publish did not commit ({status!r})"
            assert _public_shows(public, lambda p: p.salutation_text().strip() == marker), (
                "the page does not reflect the full intended content after the retry")
        finally:
            _close(anon_ctx, e_ctx)


def _p34_concurrent_edit(page, browser, tc: str) -> None:
    """135514 / 136462: two Site Content Editor sessions (the one Editor
    account, two independent browser contexts -- only one Editor account
    exists, disclosed in the report) open the same record. One saves a Page
    Content change while the other's form is still stale; the stale session
    then saves a different field.

    135514: A edits Page Title (unsaved), B edits Page Content and saves, A
    saves -> B's change must survive, or A must see a conflict warning. The
    case names a DRAFT record: the record is made editable (Unpublish) and
    then saved as Draft with no field change, and both saves are "Save as
    Draft" (the Draft record's own save).
    136462: A changes Page Content and clicks Save (the form's Publish /
    Submit control, status value 0), B (stale) changes GM Designation and
    clicks Save. Its expected result is "record the actual system
    behaviour" -- the test passes once the first save is VERIFIED stored and
    the end state is classified; the outcome is attached and reported.

    REWRITTEN 2026-10-14 (fix pass 7). The 2026-10-13 run's "silent data
    loss" was an automation fault: History held NO Page Content edit for the
    first save, i.e. it never reached the server (bug-verification-p3 row
    2). Now: the first form's CKEditor is READY before setData and holds the
    marker before the click; the click reads validity right after it; and a
    fresh read in the admin session must show the marker (bounded poll)
    BEFORE the stale save is made. If it never does, the test stops with
    "AUTOMATION --" and makes no stale save."""
    stale_label = A.LABEL_PAGE_TITLE if tc == "135514" else A.LABEL_DESIGNATION
    draft_case = tc == "135514"
    _snapshot(page, writes=("content_en", stale_label), budget=P34_LONG_BUDGET)
    run = _run_marker(tc)
    content_marker = f"{run} content by the first save"
    stale_value = f"{run} stale-session {stale_label}"
    save_kind = "save-draft" if draft_case else "publish"
    admin = A(page)
    a_ctx = b_ctx = None
    with _p34_end_published(page, tc):
        try:
            # Both sessions open BEFORE the first write.
            a_ctx, a_page = _role_session(browser, ROLE_EDITOR)
            b_ctx, b_page = _role_session(browser, ROLE_EDITOR)
            session_a, session_b = A(a_page), A(b_page)
            stale, first = (session_a, session_b) if tc == "135514" else (session_b, session_a)
            with allure.step("Precondition: the record is editable" + (" and in Draft" if draft_case else "")):
                pre_form = _editable(session_a.open_record("en"))
                if draft_case:
                    _lw(tc, "<form>", STATUS_DRAFT, "save-draft", "precondition: a Draft record (no field change)")
                    pre_form.save_as_draft()
                pre_status = list_status(_workflow_list(admin), GM_MESSAGE_ENTRY_CODE)
            _attach("record status the two sessions edit", pre_status)
            if draft_case and pre_status != STATUS_DRAFT:
                _attach("note", f"Save as Draft left the record {pre_status!r}, not Draft -- the concurrency "
                                "steps below run on that state")
            with allure.step("Both sessions open the same record"):
                stale_form = stale.open_record("en")
                stale.page_content_html_or_none("en")
                first_form = first.open_record("en")
                first_before = first.page_content_html_or_none("en")
                seen = (stale_form.field_value(stale_label), first_form.field_value(stale_label))
            assert first_before is not None, "AUTOMATION -- the first session's Page Content editor never became ready"
            assert seen[0] == seen[1], f"the two sessions do not see the same values: {seen}"
            with allure.step(f"Stale session edits {stale_label} (not saved yet)"):
                stale_form.fill_text(stale_label, stale_value)
            with allure.step("First session edits Page Content and saves"):
                first.set_page_content_html(_strip_qctest(first_before, tc) + f"<p>{content_marker}</p>", "en")
                assert content_marker in first.page_content_html("en"), (
                    "AUTOMATION -- the first session's editor does not hold the new paragraph")
                _lw(tc, "Page Content (EN)", f"<p>{content_marker}</p> appended", save_kind, "first session's save")
                if draft_case:
                    first_form.save_as_draft()
                    blocked = []
                else:
                    blocked = first_form.submit_via_reading_validity(A.PUBLISH_SUBMIT)
                first_refusal = first.refusal_text()
                _attach("first save", {"blocked controls": blocked, "refusal": first_refusal,
                                       "messages": first_form.visible_form_messages(), "url": first.page.url})
            with allure.step("Gate: a fresh read (admin session) shows the first save stored"):
                stored_first = {"html": ""}

                def _first_stored() -> bool:
                    admin.open_record("en")
                    stored_first["html"] = admin.page_content_html_or_none("en") or ""
                    return content_marker in stored_first["html"]

                try:
                    wait_until(_first_stored, timeout=_budget(90), poll=10)
                    landed = True
                except Exception:  # noqa: BLE001 -- answered below
                    landed = False
                _attach("History after the first save",
                        admin.open_list("en").history_entries(GM_MESSAGE_ENTRY_CODE)[-4:])
            if not landed:
                pytest.fail(
                    f"AUTOMATION -- the first session's Page Content save is not stored (fresh read, 90 s): "
                    f"blocked={blocked}, refusal={first_refusal!r}, stored tail={stored_first['html'][-300:]!r}. "
                    "The stale save was NOT made; nothing is concluded about concurrency.", pytrace=False)
            with allure.step(f"Stale session saves its {stale_label} change"):
                _lw(tc, f"{stale_label} (EN)", stale_value, save_kind, "stale session's save")
                if draft_case:
                    stale_form.save_as_draft()
                    stale_blocked = []
                else:
                    stale_blocked = stale_form.submit_via_reading_validity(A.PUBLISH_SUBMIT)
                stale_said = " ".join([stale.refusal_text(), *stale_form.visible_form_messages(),
                                       stale.body_text()[:1500]])
                warned = bool(CONFLICT_RE.search(stale_said))
            with allure.step("Fresh read of the record"):
                admin.open_record("en")
                stored_content = admin.page_content_html_or_none("en") or ""
                stored_field = admin.open_record("en").field_value(stale_label)
                history = admin.open_list("en").history_entries(GM_MESSAGE_ENTRY_CODE)[-6:]
            first_kept = content_marker in stored_content
            stale_applied = stored_field == stale_value
            if first_kept and stale_applied:
                outcome = "both changes kept (field-level merge)"
            elif warned:
                outcome = "conflict / stale-data warning shown to the stale session"
            elif not stale_applied:
                outcome = "stale save not applied, no warning"
            else:
                outcome = "last write wins: the stale save discarded the first save's Page Content, no warning"
            _attach("outcome", {"outcome": outcome, "first_save_kept": first_kept, "stale_save_applied": stale_applied,
                                "conflict_warning": warned, "stale_blocked": stale_blocked,
                                "stale_field_stored": stored_field, "stored_content_tail": stored_content[-400:],
                                "History (last 6)": history})
            _log.info("tc_%s concurrency outcome: %s", tc, outcome)
            assert not first_refusal, f"the first session's save was refused: {first_refusal!r}"
            if tc == "135514":
                assert first_kept or warned, (
                    f"FINDING -- {outcome}: Session B's Page Content change (verified stored by a fresh read "
                    "before Session A saved) is gone after Session A's stale save, and no conflict warning "
                    f"was shown. Stored {stale_label}: {stored_field!r}")
        finally:
            _close(a_ctx, b_ctx)

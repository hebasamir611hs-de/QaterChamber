"""
cms/tests/annual_reports/test_annual_reports_control_panel.py —
Control_Panel-tagged cases for PBI 130712 ("QC - Insights & Media - 004 -
Annual Reports"), Azure suite 140371 in plan 137724.

Holds every Control_Panel case about the per-record **Annual Report** object
(`manage-ann-rpt`), including the Control_Panel-side test of every case
tagged BOTH `Web` and `Control_Panel` (the Web-side test lives in
web/tests/annual_reports/ under the SAME `tc_<id>` marker). The page-level
"Annual Reports Page" singleton cases (hero / archive section,
`manage-annual-reports-page`) live in test_annual_reports_page_control_panel.py.

REWORKED 2026-10-04 for the seven-state editorial workflow and the
re-provisioned role accounts (standards.md "Named CMS User Roles" and
"Content Editorial Workflow"), following the approved PBI 130710 pattern
(commit 3d35745):
  - Every case runs as the account it names — Site Content Editor (156488)
    or Site Content Author (156492) — in an auth-free context
    (`AUTH_FREE_PAGE`); the signed-in userId is re-checked before each
    lifecycle step. TEST_USER is used only by the `disposable` teardown, to
    delete the test's OWN record. Cases that name no role run as the Editor
    (the role that owns the full content lifecycle).
  - The Editor's submit button reads "Publish" and publishes directly; the
    Author's reads "Submit for Review" (-> Pending Review). Unpublish is the
    row action `data-qc-oel-unpublish` and lands on UNPUBLISHED (not Draft).
    "Audit log" maps onto the row's History trail (no separate audit-log
    screen exists on this surface for these roles).
  - Success / delete messages are read from the top-of-page edit bar and
    asserted by exact text.
  - "Save" in a required-field / invalid-value case is the Editor's Publish:
    Save as Draft deliberately skips required-field validation
    (standards.md), so it cannot prove a value is accepted or rejected.
  - Records are disposable `QCTEST-130712-<tc>-<stamp> …` reports. Identity
    (title + entry id + code) is captured right after creation by diffing the
    list's ids and reading the new record back; teardown deletes only that
    captured record (see the Page Object's DELETE SAFETY notes). The 6 real
    reports and the 6 unrelated UNPUBLISHED scratch rows are never touched.
  - Active Status gates public visibility (standards.md). Every public check
    first verifies the stored Active Status (`_require_active_status`) and
    fails with that product finding when it is not stored as ticked. (Live
    2026-10-04: the control changed mid-run from an option-less "Select from
    List" — publishes then landed INACTIVE — to a checkbox ticked by default.)
  - The public grid shows a page of cards sorted by Publication Year and
    hides older years behind Load More; the public view reveals every card
    before any presence/absence check.
  - Public checks use a fresh logged-out context and the propagation budget
    (cms-profile.md: poll 5 s @ 0.5 s) once the CMS reports the new state.

Substitutions disclosed (case literal -> what runs):
  - "Annual Report 2026" / "Annual Report 2025" / "Annual Report 2025
    (Revised)" titles -> `QCTEST-130712-<tc>-<stamp> Annual Report 2026` etc.
    (the case's literal is kept as the visible suffix; a bare "Annual Report
    2025" would collide with the real 2025 report).
  - cover.bmp / report.docx / 6MB PDF / 4MB PDF -> uniquely named copies of
    the fixtures in cms/tests/annual_reports/fixtures (Documents & Media
    refuses repeated same-name uploads).
  - "PDF of exactly 5.00MB" -> annual_report_qctest_pdf_exactly_5mb.pdf,
    5,242,880 bytes (the older pdf_at_5mb_boundary.pdf is 22 bytes OVER 5 MiB).

SKIPPED:
  - 143721, 143725: field character-limit cases, QA decision (run 2026-10-04).
  - 143792, 143795: tagged Manual — not automated.
"""

from __future__ import annotations

import os
import re
from datetime import datetime

import allure
import pytest

from cms.pages.annual_reports.annual_report_admin_page import (
    ACTIVE_STATUS_UNAVAILABLE,
    FIELD_COVER_IMAGE,
    FIELD_PAGE_COUNT,
    FIELD_PDF_ATTACHMENT,
    FIELD_PUBLICATION_YEAR,
    FIELD_REPORT_DESCRIPTION_AR,
    FIELD_REPORT_DESCRIPTION_EN,
    FIELD_REPORT_TITLE_AR,
    FIELD_REPORT_TITLE_EN,
    MSG_ARABIC_REQUIRED,
    MSG_DRAFT_SAVED,
    MSG_MOVED_TO_RECYCLE_BIN,
    MSG_PDF_REQUIRED,
    MSG_SAVED_AND_PUBLISHED,
    MSG_SUBMITTED_FOR_REVIEW,
    MSG_UNSUPPORTED_FILE,
    QCTEST_PREFIX,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    STATUS_INACTIVE,
    AnnualReportAdminPage,
    AnnualReportPublicView,
    CreatedEntry,
)
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

PBI = "130712"
ANNUAL_REPORTS_CMS_XDIST_GROUP = pytest.mark.xdist_group("annual_reports_cms")
AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
FIXTURES = "cms/tests/annual_reports/fixtures"
STAMP = datetime.now().strftime("%m%d%H%M%S")

# A publish was measured at 27-30 s to reach Published on a sibling object.
PUBLISH_CONFIRM_TIMEOUT = 120.0
# cms-profile.md "Publish / Propagation Latency Budget" and the cases: poll 5 s @ 0.5 s.
PUBLIC_REFLECT_TIMEOUT = 5.0
PUBLIC_POLL = 0.5

FIELD_LENGTH_SKIP = pytest.mark.skip(
    reason="field character-limit case skipped by QA decision (run 2026-10-04)")
MANUAL_SKIP = pytest.mark.skip(reason="Manual case — not automated")
NOT_PUBLIC_ACTIONS = {"publish", "approve", "unpublish", "delete"}


def _title(tc_id: str, suffix: str = "") -> str:
    """`QCTEST-130712-<tc>-<stamp>[ suffix]` — the only namespace any delete accepts."""
    return f"{QCTEST_PREFIX}{tc_id}-{STAMP}" + (f" {suffix}" if suffix else "")


def _data(title: str, **overrides) -> dict:
    return AnnualReportAdminPage.default_data(title, **overrides)


# ===========================================================================
# Fixtures
# ===========================================================================
class DisposableRegistry:
    """Records this test created (captured identity). Only these are deleted."""

    def __init__(self):
        self._entries: dict[str, CreatedEntry] = {}
        self._removed: set[str] = set()

    @property
    def entries(self) -> list[CreatedEntry]:
        return [e for eid, e in self._entries.items() if eid not in self._removed]

    def track(self, entry: CreatedEntry) -> CreatedEntry:
        if not entry.title.startswith(QCTEST_PREFIX):
            raise ValueError(f"{entry.title!r} is not a {QCTEST_PREFIX} record")
        self._entries[entry.entry_id] = entry
        return entry

    def mark_removed(self, entry: CreatedEntry) -> None:
        self._removed.add(entry.entry_id)


@pytest.fixture
def disposable(browser):
    """Deletes ONLY the records the test registered at creation, through the
    guarded delete, from a TEST_USER context (cleanup only, never an
    assertion). Anything it cannot remove fails the teardown loudly."""
    registry = DisposableRegistry()
    yield registry
    if not registry.entries:
        return
    ctx = new_context(browser)  # TEST_USER storageState — cleanup of the test's own record only
    outcome, failures = [], []
    try:
        cleaner = AnnualReportAdminPage(ctx.new_page())
        for entry in registry.entries:
            label = f"{entry.title} (id {entry.entry_id}, code {entry.code})"
            try:
                cleaner.open_entries_list()
                if not cleaner.row_present(entry):
                    if cleaner.is_list_fully_expanded():
                        outcome.append(f"already gone: {label}")
                    else:
                        failures.append(f"{label}: not found and the list is NOT fully expanded")
                    continue
                cleaner.adopt(entry)
                if cleaner.delete_disposable_entry(entry):
                    outcome.append(f"removed {label}")
                else:
                    failures.append(f"NOT removed {label}: guarded delete refused/failed (see log)")
            except Exception as exc:  # noqa: BLE001 — collected and raised below
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read (standards.md)."""
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture
def role_pages(browser):
    """Extra auth-free pages for a second account in the same test."""
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
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
def _login(page, role: str) -> tuple[AnnualReportAdminPage, str]:
    """Signs in as `role` in this auth-free context; skips (never falls back)
    when the account cannot sign in or is not the pinned one."""
    admin = AnnualReportAdminPage(page)
    outcome = admin.login_as_role(role)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}'")
    if outcome != "ok":
        pytest.fail(f"login as '{role}' neither succeeded nor showed Liferay's refusal banner")
    admin.open_entries_list()
    user_id, name = admin.signed_in_user()
    if user_id != ROLE_USER_IDS[role]:
        pytest.skip(f"PRECONDITION: '{role}' credentials sign in as userId {user_id!r}, "
                    f"not the pinned {ROLE_USER_IDS[role]}")
    return admin, name


def _editor(page) -> AnnualReportAdminPage:
    return _login(page, ROLE_EDITOR)[0]


def _pinned(admin: AnnualReportAdminPage, role: str) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == ROLE_USER_IDS[role], (
        f"the session is now userId {user_id!r}, not the pinned {role} ({ROLE_USER_IDS[role]}) — it dropped "
        f"and was re-authenticated as another account, so nothing from here on is attributable to {role}"
    )


def _register(admin, disposable, key_value: str, ids_before: set,
              key_field: str = FIELD_REPORT_TITLE_EN) -> CreatedEntry | None:
    """Registers for teardown the ONE new record whose `key_field` reads
    `key_value`. Never raises (registration must not mask the test result)."""
    try:
        entry = admin.identify_created(key_value, ids_before, key_field)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001
        allure.attach(repr(exc), name=f"registration of {key_value!r} failed")
        return None


def _create(admin, disposable, data: dict, publish: bool, role: str = ROLE_EDITOR) -> CreatedEntry:
    """Creates one report (publish=True -> the role's submit button, else Save
    as Draft), registers whatever got created for teardown, THEN asserts.
    `admin.create_banners` holds the banners shown right after the save."""
    ids_before = admin.snapshot_ids()
    went_through, diagnostics, entry = False, "", None
    expected = (MSG_DRAFT_SAVED if not publish
                else MSG_SUBMITTED_FOR_REVIEW if role == ROLE_AUTHOR else MSG_SAVED_AND_PUBLISHED)
    try:
        admin.open_new_entry_form()
        admin.fill_report(data)
        _pinned(admin, role)
        admin.publish() if publish else admin.save_as_draft()
        went_through = admin.save_redirected()
        diagnostics = f"evidence {admin.refusal_evidence()}, banners {admin.feedback_banners()}"
        admin.create_banners = admin.top_messages(8.0, evidence=f"after creating {data['title']}",
                                                  expected=expected) if went_through else []
    finally:
        entry = _register(admin, disposable, data["title"], ids_before)
    allure.attach("\n".join(admin.create_banners) or "(none)", name=f"top-of-page message after creating "
                                                                       f"{data['title']}")
    assert went_through, f"creating {data['title']!r} did not go through: {diagnostics}"
    assert entry is not None, f"{data['title']!r} went through but is not identifiable as exactly one NEW record"
    return entry


def _wait_status_any(admin, entry: CreatedEntry, expected: tuple, timeout: float = PUBLISH_CONFIRM_TIMEOUT) -> str:
    seen = {"status": ""}

    def _reached() -> bool:
        admin.open_entries_list()
        seen["status"] = admin.row_status(entry)
        return seen["status"] in expected

    try:
        wait_until(_reached, timeout=timeout, poll=3.0)
    except WaitTimeoutError:
        pass
    return seen["status"]


def _wait_status(admin, entry: CreatedEntry, expected: str, timeout: float = PUBLISH_CONFIRM_TIMEOUT) -> str:
    return _wait_status_any(admin, entry, (expected,), timeout)


def _assert_published(admin, entry: CreatedEntry, actor: str = "Test Editor") -> None:
    """Waits for the row to read PUBLISHED. A published report whose Active
    Status is not stored reads INACTIVE instead; that is reported as the
    product finding it is (with the History evidence of the publish)."""
    status = _wait_status_any(admin, entry, (STATUS_PUBLISHED, STATUS_INACTIVE))
    if status == STATUS_INACTIVE:
        trail = _history(admin, entry)
        actions =[f"{h['action']} ({h['who']})" for h in trail]
        approved = any(h["who"] == actor and re.search(r"publish|approv", h["action"], re.I) for h in trail)
        pytest.fail(
            f"PRODUCT: after Publish the report's status reads {STATUS_INACTIVE!r}, not {STATUS_PUBLISHED!r}. "
            f"History {'records' if approved else 'does NOT record'} the publish by {actor!r} "
            f"(trail, newest first: {actions}). Active Status as recorded by THIS run's set attempt: "
            f"{admin.active_status_problem or 'no problem was recorded when it was set (cause not established)'}."
        )
    assert status == STATUS_PUBLISHED, f"the report never reached {STATUS_PUBLISHED!r} (last status {status!r})"


def _history(admin, entry: CreatedEntry) -> list[dict]:
    """The row's History trail, newest first — only items that name an action
    (the trail also renders empty nested list items)."""
    trail = [h for h in admin.history(entry) if h["action"].strip()]
    allure.attach("\n".join(repr(h) for h in trail) or "(empty)", name=f"History of {entry.title}")
    return trail


def _history_has(admin, entry: CreatedEntry, actor: str, pattern: str) -> list[dict]:
    return [h for h in _history(admin, entry)
            if h["who"] == actor and re.search(pattern, h["action"] or h["text"], re.I)]


def _require_active_status(admin, entry: CreatedEntry) -> None:
    """User rule + standards.md: Active Status must be stored as ticked before
    ANY public check. Fails (product finding) when it is not."""
    admin.open_entry(entry)
    stored = admin.active_status_stored()
    allure.attach(f"stored Active Status: {stored!r}\nset attempt: {admin.active_status_problem or 'ok'}",
                  name="Active Status precondition")
    if stored != "true":
        pytest.fail(
            f"PRECONDITION NOT MET — PRODUCT: {entry.title!r} stores Active Status {stored!r}, not 'true', so it "
            f"cannot be shown publicly. Cause: {admin.active_status_problem or ACTIVE_STATUS_UNAVAILABLE}. "
            f"The public-page step was not run (Active Status must be ticked before any public check)."
        )


def _public_until(anon_pages, predicate, message: str, locale: str = "en") -> AnnualReportPublicView:
    """Publish-then-poll on the delivery surface in ONE logged-out context."""
    view = AnnualReportPublicView(anon_pages())

    def _check() -> bool:
        view.open_reports_anonymous(locale)
        return bool(predicate(view))

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL, message=message)
    except WaitTimeoutError:
        view.screenshot("public page at timeout")
        pytest.fail(f"{message} within {PUBLIC_REFLECT_TIMEOUT:.0f}s (cards {view.card_titles_clean()})")
    return view


def _visible_publicly(anon_pages, title: str, locale: str = "en") -> tuple[AnnualReportPublicView, int]:
    view = _public_until(anon_pages, lambda v: v.card_index(title) >= 0,
                         f"DELIVERY: {title!r} never became visible to a logged-out visitor", locale)
    return view, view.card_index(title)


def _assert_not_public(anon_pages, title: str, locale: str = "en") -> None:
    """Absence that cannot pass vacuously: the page must render the real
    cards (positive control) before `title` is required absent from the grid
    and from the page's own search."""
    view = AnnualReportPublicView(anon_pages()).open_reports_anonymous(locale)
    cards = view.card_titles_clean()
    if not cards:
        pytest.fail(f"cannot prove {title!r} is absent: the logged-out page shows no report cards")
    control = cards[0]
    if control not in view.search_titles(control):
        pytest.fail(f"positive control failed: visible card {control!r} is not found through the public search box")
    assert title not in view.card_titles_clean(), f"{title!r} is still on the logged-out grid"
    found = view.search_titles(title)
    assert title not in found, f"searching {title!r} on the public page still returns it: {found}"


def _assert_not_public_within_budget(anon_pages, title: str) -> None:
    _public_until(anon_pages, lambda v: v.card_index(title) < 0,
                  f"{title!r} was still visible to a logged-out visitor")
    _assert_not_public(anon_pages, title)


def _messages_contain(admin, expected: str) -> bool:
    return expected in admin.visible_messages_text() or expected in admin.page_body_text()


# QA decision 2026-10-04: when the block/rejection itself works and ONLY the
# message wording differs from the case, the case passes and the wording is
# tracked as a low-priority bug — recorded here as evidence, not failed on.
WORDING_BUG_ARABIC_REQUIRED = "148073"   # 143827 / 143828 / 143829
WORDING_BUG_PDF_REQUIRED = "148074"      # 143781 / 143797
WORDING_BUG_UNSUPPORTED_PDF = "148075"   # 143782


def _check_wording(expected: str, shown: str, bug: str | None, failure: str) -> None:
    """Exact-text check; with a known wording bug the mismatch is attached, not failed."""
    if expected in shown:
        return
    if bug:
        allure.attach(f"Known wording bug {bug}: expected {expected!r}, shown {shown!r}",
                      name="message wording (known bug)")
        return
    pytest.fail(failure)


def _assert_blocked(admin, disposable, data: dict, what: str, key_field: str = FIELD_REPORT_TITLE_EN,
                    expect_in_evidence: str | None = None, expected_message: str | None = None,
                    wording_bug: str | None = None) -> dict:
    """Fills a NEW form with `data`, clicks the Editor's Publish, and requires
    the attempt to be refused with validation evidence and NO record created.
    Anything created is registered for teardown first."""
    ids_before = admin.snapshot_ids()
    redirected, blocked, evidence, entry, messages = False, False, {}, None, ""
    try:
        admin.open_new_entry_form()
        admin.fill_report(data)
        _pinned(admin, ROLE_EDITOR)
        admin.publish()
        redirected = admin.save_redirected()
        blocked = admin.submit_blocked()
        evidence = admin.refusal_evidence()
        messages = admin.visible_messages_text()
        admin.screenshot(f"after Publish with {what}")
        allure.attach(f"{evidence}\nmessages: {messages}", name=f"refusal evidence ({what})")
    finally:
        key_value = data["title"] if key_field == FIELD_REPORT_TITLE_EN else data["title_ar"]
        entry = _register(admin, disposable, key_value, ids_before, key_field)
    if entry is not None:
        admin.open_entries_list()
        status = admin.row_status(entry)
        pytest.fail(f"PRODUCT: Publish was NOT blocked with {what} — a record was created "
                    f"(status {status!r}, entry id {entry.entry_id}); expected the publish to be blocked")
    assert blocked and not redirected, (
        f"Publish with {what} was neither refused with validation evidence nor saved: "
        f"redirected={redirected}, evidence={evidence}"
    )
    if expect_in_evidence:
        assert re.search(expect_in_evidence, repr(evidence), re.I), (
            f"Publish was refused, but the validation evidence does not point at {what}: {evidence}"
        )
    if expected_message and not _messages_contain(admin, expected_message):
        _check_wording(
            expected_message, messages, wording_bug,
            f"Publish with {what} was blocked, but the message {expected_message!r} the case requires is not "
            f"shown; what the page showed instead: {messages or '(no text message — only the browser’s native '}"
            f"{'' if messages else 'required-field bubble: ' + repr(evidence.get('native_messages'))})",
        )
    return evidence


def _publish_and_find(admin, disposable, anon_pages, data: dict):
    """Creates + publishes (Editor), waits for Published, verifies Active
    Status, then finds the report on the public page -> (entry, view, index)."""
    entry = _create(admin, disposable, data, publish=True)
    _assert_published(admin, entry)
    assert admin.has_message(admin.create_banners, MSG_SAVED_AND_PUBLISHED), (
        f"no {MSG_SAVED_AND_PUBLISHED!r} message after publishing {data['title']!r}: {admin.create_banners}"
    )
    _require_active_status(admin, entry)
    view, index = _visible_publicly(anon_pages, data["title"])
    return entry, view, index


def _no_permission_error(banners: list[str]) -> list[str]:
    return [b for b in banners if re.search(r"permission|not allowed|denied|forbidden", b, re.I)]


def _parse_stamp(text: str) -> datetime | None:
    for fmt in ("%m/%d/%Y, %I:%M:%S %p", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y, %H:%M:%S", "%d/%m/%Y, %H:%M:%S",
                "%m/%d/%Y, %I:%M %p", "%b %d, %Y, %I:%M:%S %p", "%b %d, %Y, %I:%M %p"):
        try:
            return datetime.strptime(" ".join(text.split()), fmt)
        except ValueError:
            continue
    return None


# ===========================================================================
# 143594 / 143595 / 143598 / 143600 — Auth / RBAC
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An unauthenticated user is denied direct access to the Annual Reports CMS admin area")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143594
def test_unauthenticated_denied_admin_access(page):
    # Azure TC 143594 | PBI 130712 | account: none (fresh logged-out context).
    admin = AnnualReportAdminPage(page)
    served = admin.open_manage_anonymously()
    admin.screenshot("logged-out manage-ann-rpt")
    allure.attach(repr(served), name="what a logged-out visitor is served")

    # "no admin content or data is exposed"
    assert not served["signed_in"], f"the fresh context is unexpectedly signed in: {served}"
    assert not served["authoring_form"] and served["entry_rows"] == 0 and not served["real_titles_exposed"], (
        f"admin content is exposed to a logged-out visitor: form={served['authoring_form']}, "
        f"rows={served['entry_rows']}, real titles {served['real_titles_exposed']}"
    )
    # "the user is redirected to the CMS login page"
    assert served["login_form"], (
        f"access is denied, but the visitor is NOT redirected to the CMS login page: the URL stays "
        f"{served['url']} (HTTP {served['status']}, page title {served['title']!r}) and shows: "
        f"{served['body_excerpt'][:200]!r}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor can perform the full Annual Report lifecycle")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143595
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_site_content_editor_full_lifecycle(page, disposable):
    # Azure TC 143595 | PBI 130712 | account: Site Content Editor (156488).
    admin, editor_name = _login(page, ROLE_EDITOR)
    title = _title("143595", "Lifecycle")
    banners_seen: list[str] = []

    # Step 2 — create (Save as Draft).
    entry = _create(admin, disposable, _data(title), publish=False)
    banners_seen += admin.create_banners
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT, f"new record status {admin.row_status(entry)!r}, not Draft"

    # Step 3a — edit.
    admin.open_entry(entry)
    edited = f"{title} edited description."
    admin.fill_text(FIELD_REPORT_DESCRIPTION_EN, edited)
    _pinned(admin, ROLE_EDITOR)
    admin.save_as_draft()
    assert admin.save_redirected(), f"the Editor's edit was refused: {admin.refusal_evidence()}"
    banners_seen += admin.success_banners(expected=MSG_DRAFT_SAVED)
    admin.open_entry(entry)
    assert admin.field_value(FIELD_REPORT_DESCRIPTION_EN) == edited, "the edit was not stored"

    # Step 3b — preview (row Preview link, rendered for the signed-in Editor).
    admin.open_entries_list()
    preview_url = admin.row_preview_href(entry)
    assert preview_url, f"no Preview action on the Editor's row: {admin.row_link_labels(entry)}"
    preview_text = admin.open_preview(preview_url, [title])
    admin.screenshot("143595 preview")
    assert title in preview_text, f"the Preview page does not render the draft report {title!r}"

    # Step 3c — publish.
    admin.open_entry(entry)
    _pinned(admin, ROLE_EDITOR)
    admin.publish()
    assert admin.save_redirected(), f"Publish was refused: {admin.refusal_evidence()}"
    banners_seen += admin.success_banners(expected=MSG_SAVED_AND_PUBLISHED)
    _assert_published(admin, entry, editor_name)

    # Step 3d — unpublish (row action) -> Unpublished.
    admin.open_entries_list()
    _pinned(admin, ROLE_EDITOR)
    dialogs = admin.run_row_action(entry, "unpublish")
    banners_seen += admin.top_messages(evidence="143595 unpublish")
    assert _wait_status(admin, entry, STATUS_UNPUBLISHED, 60.0) == STATUS_UNPUBLISHED, (
        f"after Unpublish the status reads {admin.row_status(entry)!r} (dialogs {dialogs})"
    )

    # Step 3e — delete (guarded, as the Editor).
    _pinned(admin, ROLE_EDITOR)
    deleted = admin.delete_disposable_entry(entry, await_message=True)
    banners_seen += getattr(admin, "last_delete_banners", [])
    assert deleted, "the Editor's delete did not remove the record"
    disposable.mark_removed(entry)

    allure.attach("\n".join(banners_seen), name="messages across the lifecycle")
    assert not _no_permission_error(banners_seen), f"a permission error was shown: {_no_permission_error(banners_seen)}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Author can create and edit an Annual Report record and submit it for review")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130712
@pytest.mark.tc_143598
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_site_content_author_create_edit_submit_for_review(page, disposable):
    # Azure TC 143598 | PBI 130712 | account: Site Content Author (156492).
    admin, _ = _login(page, ROLE_AUTHOR)
    title = _title("143598", "Author")

    # Create (Save as Draft) as the Author.
    entry = _create(admin, disposable, _data(title), publish=False, role=ROLE_AUTHOR)
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT, f"the Author's new record reads {admin.row_status(entry)!r}"

    # Edit its fields.
    admin.open_entry(entry)
    edited = f"{title} edited by the Author."
    admin.fill_text(FIELD_REPORT_DESCRIPTION_EN, edited)
    admin.fill_number(FIELD_PAGE_COUNT, "12")
    form_actions = admin.form_action_labels()
    allure.attach(repr(form_actions), name="Author form actions")
    assert admin.submit_button_label() == "Submit for Review", (
        f"the Author's submit button reads {admin.submit_button_label()!r}, not 'Submit for Review'"
    )

    # Submit for review -> Pending Review.
    _pinned(admin, ROLE_AUTHOR)
    admin.submit_for_review()
    assert admin.save_redirected(), f"the Author's Submit for Review was refused: {admin.refusal_evidence()}"
    banners = admin.top_messages(evidence="143598 submit", expected=MSG_SUBMITTED_FOR_REVIEW)
    status = _wait_status_any(admin, entry, (STATUS_PENDING_REVIEW, STATUS_PUBLISHED, STATUS_INACTIVE), 60.0)
    assert status == STATUS_PENDING_REVIEW, f"after the Author's Submit for Review the status reads {status!r}"
    admin.open_entry(entry)
    stored = admin.read_report()
    assert stored["description"] == edited and stored["page_count"] == "12", f"the Author's edits were not stored: {stored}"
    _history(admin, entry)  # evidence only — the case does not ask for an audit entry
    assert admin.has_message(banners, MSG_SUBMITTED_FOR_REVIEW), (
        f"no {MSG_SUBMITTED_FOR_REVIEW!r} message after the Author's Submit for Review: {banners}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Author cannot directly publish, unpublish, or delete an Annual Report record")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143600
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_site_content_author_cannot_publish_unpublish_delete(page, disposable, role_pages):
    # Azure TC 143600 | PBI 130712 | accounts: Site Content Author (156492) under
    # test; the Site Content Editor (156488, separate context) publishes the
    # target record first. Publish is checked on the Author's own Draft;
    # Unpublish and Delete on the Editor's Published record.
    editor, _ = _login(role_pages(), ROLE_EDITOR)
    published_title = _title("143600", "Editor published")
    published = _create(editor, disposable, _data(published_title), publish=True)
    published_status = _wait_status_any(editor, published, (STATUS_PUBLISHED, STATUS_INACTIVE))
    assert published_status in (STATUS_PUBLISHED, STATUS_INACTIVE), (
        f"precondition: the Editor's record never reached Published (status {published_status!r})"
    )

    author, _ = _login(page, ROLE_AUTHOR)
    own_title = _title("143600", "Author draft")
    own = _create(author, disposable, _data(own_title), publish=False, role=ROLE_AUTHOR)

    # Publish — the Author's own Draft offers no Publish (form or row).
    author.open_entry(own)
    form_actions = author.form_action_labels()
    author.open_entries_list()
    own_row_actions = author.row_actions(own)
    # Unpublish / Delete — the Editor's Published record.
    _pinned(author, ROLE_AUTHOR)
    pub_row_actions = author.row_actions(published)
    pub_row_labels = author.row_link_labels(published)
    pub_status_seen_by_author = author.row_status(published)
    allure.attach(f"Author form actions on own Draft: {form_actions}\nown Draft row actions: {own_row_actions}\n"
                  f"Editor-published row actions seen by the Author: {pub_row_actions} / {pub_row_labels}",
                  name="Author's available actions")
    author.screenshot("143600 Author list")

    assert "Publish" not in form_actions, f"the Author's form offers Publish: {form_actions}"
    assert not {"publish", "approve"} & set(own_row_actions), (
        f"the Author's own Draft row offers a publish action: {own_row_actions}"
    )
    assert "unpublish" not in pub_row_actions, f"the Author is offered Unpublish on a Published record: {pub_row_actions}"
    assert "delete" not in pub_row_actions, f"the Author is offered Delete on a Published record: {pub_row_actions}"
    # The record's state does not change.
    editor.open_entries_list()
    assert editor.row_status(published) == published_status, (
        f"the Published record's state changed to {editor.row_status(published)!r}"
    )
    assert pub_status_seen_by_author == published_status, (
        f"the Author sees the record as {pub_status_seen_by_author!r}, the Editor as {published_status!r}"
    )


# ===========================================================================
# 143616 / 143641 / 143642 / 143643 / 143644 / 143666 — content lifecycle
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An admin can create, save as draft, preview and publish a new Annual Report, and it appears live")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.workflow
@pytest.mark.pbi_130712
@pytest.mark.tc_143616
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_create_draft_preview_publish_report_cp(page, disposable, anon_pages):
    # Azure TC 143616 | PBI 130712 | account: Site Content Editor (156488).
    admin, editor_name = _login(page, ROLE_EDITOR)
    title = _title("143616", "Annual Report 2026")
    data = _data(title, publication_year="2026", publication_date="01/03/2026", page_count="15")

    # Step 1 — Save as Draft: Draft, success message, History records the create.
    entry = _create(admin, disposable, data, publish=False)
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT, f"status is {admin.row_status(entry)!r}, not Draft"
    assert admin.has_message(admin.create_banners, MSG_DRAFT_SAVED), (
        f"no {MSG_DRAFT_SAVED!r} message after Save as Draft: {admin.create_banners}"
    )
    created_trail = _history(admin, entry)
    assert any(h["who"] == editor_name for h in created_trail), f"History records no create by {editor_name!r}"

    # Step 2 — Preview renders the entered content.
    admin.open_entries_list()
    preview_url = admin.row_preview_href(entry)
    assert preview_url, "the row offers no Preview action"
    preview_text = admin.open_preview(preview_url, [title, data["description"]])
    admin.screenshot("143616 preview")
    missing = [v for v in (title, data["description"]) if v not in preview_text]
    assert not missing, f"Preview does not show the entered content: missing {missing}"

    # Step 3 — Publish: Published, success message, History records the publish.
    admin.open_entry(entry)
    _pinned(admin, ROLE_EDITOR)
    admin.publish()
    assert admin.save_redirected(), f"Publish was refused: {admin.refusal_evidence()}"
    banners = admin.top_messages(evidence="143616 publish", expected=MSG_SAVED_AND_PUBLISHED)
    _assert_published(admin, entry, editor_name)
    assert _history_has(admin, entry, editor_name, r"publish|approv"), "History records no publish by the Editor"
    assert admin.has_message(banners, MSG_SAVED_AND_PUBLISHED), f"no {MSG_SAVED_AND_PUBLISHED!r} message: {banners}"

    # Step 4 — live within 5 s, above 2025.
    _require_active_status(admin, entry)
    view, index = _visible_publicly(anon_pages, title)
    cards = view.card_titles_clean()
    assert "Annual Report 2025" in cards, f"the real 2025 card is missing from the grid: {cards}"
    assert index < cards.index("Annual Report 2025"), (
        f"the 2026 report is not listed above 2025 (descending order): {cards}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Editing a published report's Title and republishing shows the new value live, not the stale one")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130712
@pytest.mark.tc_143641
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_edit_published_title_persists_cp(page, disposable, anon_pages):
    # Azure TC 143641 | PBI 130712 | account: Site Content Editor (156488).
    admin, editor_name = _login(page, ROLE_EDITOR)
    original = _title("143641", "Annual Report 2025")
    revised = f"{original} (Revised)"
    entry = _create(admin, disposable, _data(original, publication_year="2025"), publish=True)
    _assert_published(admin, entry, editor_name)
    trail_before = len(_history(admin, entry))

    # Step 1 — change Report Title EN and publish.
    admin.open_entry(entry)
    admin.fill_text(FIELD_REPORT_TITLE_EN, revised)
    _pinned(admin, ROLE_EDITOR)
    admin.publish()
    went_through = admin.save_redirected()
    banners = admin.top_messages(evidence="143641 republish", expected=MSG_SAVED_AND_PUBLISHED) if went_through else []
    admin.open_entry(entry)
    stored_title = admin.field_value(FIELD_REPORT_TITLE_EN)
    if stored_title == revised:
        entry = disposable.track(entry.retitled(revised))
    assert went_through, f"the republish was refused: {admin.refusal_evidence()}"
    assert stored_title == revised, f"the new title was not stored (form reads {stored_title!r})"
    _assert_published(admin, entry, editor_name)
    trail_after = _history(admin, entry)
    assert len(trail_after) > trail_before and trail_after[0]["who"] == editor_name, (
        f"History records no new entry by {editor_name!r} for the edit (before {trail_before} items, now {trail_after})"
    )
    assert admin.has_message(banners, MSG_SAVED_AND_PUBLISHED), f"no {MSG_SAVED_AND_PUBLISHED!r} message: {banners}"

    # Step 2 — live shows the new title; the old one is gone.
    _require_active_status(admin, entry)
    view, _ = _visible_publicly(anon_pages, revised)
    assert original not in view.card_titles_clean(), f"the stale title {original!r} is still displayed"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unpublishing a published report removes it from the live page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143642
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_unpublish_report_status_cp(page, disposable, anon_pages):
    # Azure TC 143642 | PBI 130712 | account: Site Content Editor (156488).
    admin, editor_name = _login(page, ROLE_EDITOR)
    title = _title("143642", "Annual Report")
    entry = _create(admin, disposable, _data(title), publish=True)
    _assert_published(admin, entry, editor_name)
    # Precondition: the report really is public before it is unpublished.
    _require_active_status(admin, entry)
    _visible_publicly(anon_pages, title)

    # Step 1 — Unpublish -> Unpublished, message, History.
    admin.open_entries_list()
    _pinned(admin, ROLE_EDITOR)
    dialogs = admin.run_row_action(entry, "unpublish")
    banners = admin.top_messages(evidence="143642 unpublish")
    allure.attach(f"dialogs {dialogs}\ntop-of-page message {banners}", name="Unpublish feedback")
    assert _wait_status(admin, entry, STATUS_UNPUBLISHED, 60.0) == STATUS_UNPUBLISHED
    assert _history_has(admin, entry, editor_name, r"unpublish"), "History records no Unpublish by the Editor"

    # Step 2 — gone from the grid and from search within the budget.
    _assert_not_public_within_budget(anon_pages, title)
    assert banners, f"no success message after Unpublish (dialogs {dialogs})"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Deleting a report removes it from the live page and its PDF link no longer resolves")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130712
@pytest.mark.tc_143643
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_delete_report_removes_row_cp(page, disposable, anon_pages):
    # Azure TC 143643 | PBI 130712 | account: Site Content Editor (156488).
    # "Audit log records the deletion": the row (and its History) is gone after
    # the delete and no audit-log screen is reachable for this role — that half
    # is not observable here and is reported, not assumed.
    admin, editor_name = _login(page, ROLE_EDITOR)
    title = _title("143643", "Annual Report")
    entry, view, index = _publish_and_find(admin, disposable, anon_pages, _data(title))
    pdf_view_url = view.card_view_details_href(index)
    pdf_download_url = view.card_download_href(index)
    before = view.url_status(pdf_view_url)
    allure.attach(f"View Details {pdf_view_url}\nDownload {pdf_download_url}\nbefore delete {before}",
                  name="PDF URL copied before the delete")
    assert before["status"] == 200, f"precondition: the live PDF link does not resolve before the delete: {before}"

    # Step 1 — delete.
    _pinned(admin, ROLE_EDITOR)
    deleted = admin.delete_disposable_entry(entry, await_message=True)
    banners = getattr(admin, "last_delete_banners", [])
    allure.attach(f"dialogs {getattr(admin, 'last_delete_dialogs', [])}\nmessage {banners}", name="delete feedback")
    assert deleted, "the Editor's delete did not remove the record"
    disposable.mark_removed(entry)
    expected_message = MSG_MOVED_TO_RECYCLE_BIN.format(label=title)
    allure.attach("No audit-log screen is reachable for the Site Content Editor and the row's History goes with "
                  "the row, so 'audit log records the deletion' is not observable here.", name="audit log")

    # Step 2 — gone from the grid; the old PDF URL no longer resolves.
    _assert_not_public_within_budget(anon_pages, title)
    after = AnnualReportPublicView(anon_pages()).url_status(pdf_view_url)
    allure.attach(repr(after), name="old PDF URL after the delete")
    assert admin.has_message(banners, expected_message), (
        f"no {expected_message!r} message after the delete; shown: {banners}"
    )
    assert not (after["status"] == 200 and after["is_pdf"]), (
        f"the old PDF URL still resolves to the PDF after the record was deleted (HTTP {after['status']}, "
        f"{after['content_type']}, {after['size']} bytes): {pdf_view_url}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Toasts / Audit log")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing a Draft shows the success message and is recorded in the audit (History) trail")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_130712
@pytest.mark.tc_143644
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_admin_action_shows_success_toast(page, disposable):
    # Azure TC 143644 | PBI 130712 | account: Site Content Editor (156488).
    # "Generic success toast" = the top-of-page edit bar; "audit log" = History.
    admin, editor_name = _login(page, ROLE_EDITOR)
    title = _title("143644", "Toast")
    entry = _create(admin, disposable, _data(title), publish=False)

    admin.open_entry(entry)
    _pinned(admin, ROLE_EDITOR)
    published_at = datetime.now()
    admin.publish()
    assert admin.save_redirected(), f"Publish was refused: {admin.refusal_evidence()}"
    banners = admin.top_messages(evidence="143644 publish", expected=MSG_SAVED_AND_PUBLISHED)
    _assert_published(admin, entry, editor_name)

    publishes = _history_has(admin, entry, editor_name, r"publish|approv")
    assert admin.has_message(banners, MSG_SAVED_AND_PUBLISHED), (
        f"no {MSG_SAVED_AND_PUBLISHED!r} message right after Publish; shown: {banners}"
    )
    assert publishes, f"the History trail has no publish entry by {editor_name!r}"
    assert all(h["when"] for h in publishes), f"the publish entry carries no timestamp: {publishes}"
    allure.attach(f"published at (client clock) {published_at:%Y-%m-%d %H:%M:%S}\n{publishes}",
                  name="publish audit entry")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Audit fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Created / Last Modified Date auto-stamp correctly on create and update")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143666
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_created_last_modified_date_auto_stamp(page, disposable):
    # Azure TC 143666 | PBI 130712 | account: Site Content Editor (156488).
    # Created Date = the History trail's create entry; Last Modified = the
    # list's LAST MODIFIED column (the form shows neither).
    admin, editor_name = _login(page, ROLE_EDITOR)
    title = _title("143666", "Date Stamp")
    entry = _create(admin, disposable, _data(title), publish=False)

    admin.open_entries_list()
    modified_1 = admin.row_modified(entry)
    trail_1 = _history(admin, entry)
    created_1 = trail_1[-1] if trail_1 else {}
    assert modified_1 and _parse_stamp(modified_1), f"no parsable Last Modified after create: {modified_1!r}"
    assert created_1.get("when"), f"no Created Date (History create entry) after create: {trail_1}"

    # Step 2 — edit and save.
    wait_until(lambda: datetime.now().second != 59, timeout=2.0, poll=0.2)  # not straddling a minute edge
    admin.open_entry(entry)
    admin.fill_text(FIELD_REPORT_DESCRIPTION_EN, f"{title} edited.")
    _pinned(admin, ROLE_EDITOR)
    admin.save_as_draft()
    assert admin.save_redirected(), f"the edit save was refused: {admin.refusal_evidence()}"
    admin.open_entries_list()
    modified_2 = admin.row_modified(entry)
    trail_2 = _history(admin, entry)
    created_2 = trail_2[-1] if trail_2 else {}
    allure.attach(f"after create: modified {modified_1!r}, created {created_1}\n"
                  f"after edit:   modified {modified_2!r}, created {created_2}\nfull trail {trail_2}",
                  name="date stamps")

    t1, t2 = _parse_stamp(modified_1), _parse_stamp(modified_2)
    assert t2 and t2 > t1, f"Last Modified did not move forward on edit: {modified_1!r} -> {modified_2!r}"
    assert created_2.get("when") == created_1.get("when"), (
        f"Created Date changed on edit: {created_1.get('when')!r} -> {created_2.get('when')!r}"
    )
    assert len(trail_2) > len(trail_1) and trail_2[0]["when"], (
        f"the audit (History) trail has no entry for the edit: {trail_2}"
    )


# ===========================================================================
# Report Title / Description (143719-143726, 143829)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Report Title is saved and displayed on the card")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143719
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_title_saved_persists_cp(page, disposable, anon_pages):
    # Azure TC 143719 | PBI 130712 | account: Site Content Editor (156488).
    admin = _editor(page)
    title = _title("143719", "Annual Report 2025")
    _, view, index = _publish_and_find(admin, disposable, anon_pages,
                                       _data(title, title_ar=f"{title} التقرير السنوي 2025"))
    assert view.card_titles_clean()[index] == title, f"card title reads {view.card_titles_clean()[index]!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An empty Report Title (EN) is rejected on publish")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143720
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_title_empty_rejected(page, disposable):
    # Azure TC 143720 | PBI 130712 | account: Site Content Editor. The unique
    # QCTEST identity is carried by the AR title, since Title EN is emptied.
    admin = _editor(page)
    data = {**_data(_title("143720")), "title": "", "title_ar": _title("143720", "AR")}
    _assert_blocked(admin, disposable, data, "an empty Report Title (EN)", key_field=FIELD_REPORT_TITLE_AR,
                    expect_in_evidence=r"reportTitle|Report Title|required")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143721
@allure.title("A Report Title exceeding 200 characters is rejected at the boundary")
@FIELD_LENGTH_SKIP
def test_report_title_exceeds_200_chars_rejected(page):
    ...


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Title validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only Report Title is rejected as empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143722
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_title_whitespace_only_rejected(page, disposable):
    # Azure TC 143722 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    data = {**_data(_title("143722")), "title": "   ", "title_ar": _title("143722", "AR")}
    _assert_blocked(admin, disposable, data, "a whitespace-only Report Title", key_field=FIELD_REPORT_TITLE_AR,
                    expect_in_evidence=r"reportTitle|Report Title")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Report Description is saved and displayed on the card")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143723
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_description_saved_persists_cp(page, disposable, anon_pages):
    # Azure TC 143723 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    description = ("A consolidated QCTEST overview of the Chamber's institutional performance, key initiatives "
                   "and business engagement during the reporting year.")
    description_ar = "نظرة عامة تجريبية موحدة على أداء الغرفة المؤسسي ومبادراتها الرئيسية خلال سنة التقرير."
    assert len(description) <= 500 and len(description_ar) <= 500
    _, view, index = _publish_and_find(admin, disposable, anon_pages,
                                       _data(_title("143723"), description=description,
                                             description_ar=description_ar))
    shown = view.card_desc(index).strip()
    assert shown == description, f"card description reads {shown!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An empty Report Description (EN) is rejected on publish")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143724
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_description_empty_rejected(page, disposable):
    # Azure TC 143724 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("143724"), description=""), "an empty Report Description (EN)",
                    expect_in_evidence=r"reportDescription|Description|required")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143725
@allure.title("A Report Description exceeding 500 characters is rejected at the boundary")
@FIELD_LENGTH_SKIP
def test_report_description_exceeds_500_chars_rejected(page):
    ...


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Report Description validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only Report Description is rejected as empty")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143726
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_description_whitespace_only_rejected(page, disposable):
    # Azure TC 143726 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("143726"), description="   "),
                    "a whitespace-only Report Description",
                    expect_in_evidence=r"reportDescription|Description")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Bilingual")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title('Publishing an Annual Report with empty Arabic Title/Description is blocked ("Arabic content is required.")')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143829
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_report_arabic_fields_empty_blocks_publish(page, disposable):
    # Azure TC 143829 | PBI 130712 | account: Site Content Editor.
    # Step 1 — "Record created in Draft": Save as Draft with AR empty.
    admin = _editor(page)
    title = _title("143829")
    entry = _create(admin, disposable, _data(title, title_ar="", description_ar=""), publish=False)
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT, f"the AR-empty record reads {admin.row_status(entry)!r}"

    # Step 2 — Publish is blocked with the Arabic-content message.
    # Live 2026-10-04: the edit form PRE-FILLS an empty Arabic box with the
    # English text (display fallback), so the Arabic boxes are emptied again
    # before Publish to keep the case's precondition (AR empty, EN filled).
    admin.open_entry(entry)
    prefilled = {"title_ar": admin.field_value(FIELD_REPORT_TITLE_AR),
                 "description_ar": admin.field_value(FIELD_REPORT_DESCRIPTION_AR)}
    allure.attach(repr(prefilled), name="Arabic boxes as loaded on the Draft")
    admin.fill_text(FIELD_REPORT_TITLE_AR, "")
    admin.fill_text(FIELD_REPORT_DESCRIPTION_AR, "")
    assert admin.field_value(FIELD_REPORT_TITLE_AR) == "" and admin.field_value(FIELD_REPORT_DESCRIPTION_AR) == ""
    _pinned(admin, ROLE_EDITOR)
    admin.publish()
    redirected, evidence, messages = admin.save_redirected(), admin.refusal_evidence(), admin.visible_messages_text()
    admin.screenshot("143829 after Publish")
    allure.attach(f"{evidence}\nmessages: {messages}", name="Publish with empty Arabic fields")
    status = _wait_status_any(admin, entry, (STATUS_PUBLISHED, STATUS_INACTIVE, STATUS_DRAFT), 20.0)
    assert status not in (STATUS_PUBLISHED, STATUS_INACTIVE), (
        f"PRODUCT: Publish was NOT blocked with empty Arabic fields — the record reads {status!r}"
    )
    assert not redirected, f"the Publish went through (page reloaded) though the record stayed {status!r}"
    _check_wording(
        MSG_ARABIC_REQUIRED, messages, WORDING_BUG_ARABIC_REQUIRED,
        f"Publish was blocked, but not with {MSG_ARABIC_REQUIRED!r}; shown instead: "
        f"{messages or 'only the browser’s native required-field bubble ' + repr(evidence['native_messages'])}",
    )


# ===========================================================================
# Cover Image (143727-143729, 143793)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Cover Image (JPG) is uploaded and displayed on the card")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143727
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_cover_image_uploaded_persists_cp(page, disposable, anon_pages):
    # Azure TC 143727 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    data = _data(_title("143727"), cover_stem="cover_143727")
    entry, view, index = _publish_and_find(admin, disposable, anon_pages, data)
    img = view.card_cover_img(index)
    allure.attach(repr(img), name="card cover image")
    stem = os.path.splitext(data["cover_uploaded_as"])[0]
    assert img["present"] and img["loaded"], f"the card image does not render: {img}"
    assert stem in img["src"], f"the card renders {img['src']!r}, not the uploaded {data['cover_uploaded_as']!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing without a Cover Image is blocked")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143728
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_cover_image_missing_blocks_publish(page, disposable):
    # Azure TC 143728 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("143728"), cover_path=None), "no Cover Image",
                    expect_in_evidence=r"reportCoverImage|Cover")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An unsupported Cover Image format (BMP) is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143729
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_cover_image_unsupported_format_rejected(page, disposable):
    # Azure TC 143729 | PBI 130712 | account: Site Content Editor. Nothing is saved.
    admin = _editor(page)
    admin.open_new_entry_form()
    admin.fill_report({"title": _title("143729")})
    result = admin.attempt_upload(FIELD_COVER_IMAGE, f"{FIXTURES}/unsupported_cover.bmp")
    admin.screenshot("143729 after the BMP upload attempt")
    allure.attach(repr(result), name="cover.bmp upload attempt")
    attached = result["file"] in (result.get("field_value") or "")
    shown = " ".join(result["errors"] + result.get("field_errors", []) + [result.get("picker_text", "")])
    assert not attached, f"cover.bmp was attached as the Cover Image: {result}"
    assert re.search(r"type|format|extension|not (allowed|supported)|invalid", shown, re.I), (
        f"cover.bmp was not attached, but no unsupported-file-type message was shown: {result}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing a published report's Cover Image fully removes the old image reference on delivery")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130712
@pytest.mark.tc_143793
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_replace_cover_image_updates_filename_cp(page, disposable, anon_pages):
    # Azure TC 143793 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    title = _title("143793")
    data = _data(title, cover_stem="cover_143793_old")
    entry, view, index = _publish_and_find(admin, disposable, anon_pages, data)
    old_src = view.card_cover_img(index)["src"]

    # Step 1-2 — replace the cover and publish.
    admin.open_entry(entry)
    admin.upload_file(FIELD_COVER_IMAGE, admin.DEFAULT_COVER, "cover_143793_new")
    new_cover = admin.last_uploaded_name
    _pinned(admin, ROLE_EDITOR)
    admin.publish()
    assert admin.save_redirected(), f"the replacement save was refused: {admin.refusal_evidence()}"
    banners = admin.top_messages(evidence="143793 republish", expected=MSG_SAVED_AND_PUBLISHED)
    _assert_published(admin, entry)
    admin.open_entry(entry)
    assert admin.stored_file_name(FIELD_COVER_IMAGE) == new_cover, "the replacement cover was not stored"
    assert admin.has_message(banners, MSG_SAVED_AND_PUBLISHED), f"no {MSG_SAVED_AND_PUBLISHED!r} message: {banners}"

    # Step 3 — only the new image; the old one is not reachable.
    stem = os.path.splitext(new_cover)[0]
    state = {}

    def _new_image(v) -> bool:
        i = v.card_index(title)
        if i < 0:
            return False
        state.update(v.card_cover_img(i))
        return stem in state.get("src", "")

    view2 = _public_until(anon_pages, _new_image, f"DELIVERY: the card never showed the replacement cover {new_cover!r}")
    old = view2.url_status(old_src)
    allure.attach(f"new card image {state}\nold image URL {old_src}\nold URL now {old}", name="cover images")
    assert state["loaded"], f"the replacement cover does not render (broken image): {state}"
    assert old_src.split("?")[0] not in state["src"], "the card still points at the old image"
    assert not (old["status"] == 200 and old["content_type"].startswith("image/")), (
        f"the old cover image is still served at its previous URL (HTTP {old['status']}, {old['content_type']}, "
        f"{old['size']} bytes): {old_src}"
    )


# ===========================================================================
# Publication Year / Date (143730-143734)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Sort order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Publication Year (2025) saves and drives the card's sort position")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143730
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_year_saved_persists_cp(page, disposable, anon_pages):
    # Azure TC 143730 | PBI 130712 | account: Site Content Editor.
    # "Alongside other years" = the 6 real reports (2020-2025).
    admin = _editor(page)
    title = _title("143730", "Annual Report 2025")
    entry, view, index = _publish_and_find(admin, disposable, anon_pages,
                                           _data(title, publication_year="2025", publication_date="15/03/2025"))
    admin.open_entry(entry)
    assert admin.number_field_value(FIELD_PUBLICATION_YEAR) == "2025", "Publication Year 2025 was not stored"
    cards = view.card_titles_clean()
    allure.attach(repr(cards), name="public card order")
    assert "Annual Report 2024" in cards, f"the real 2024 card is missing: {cards}"
    assert index < cards.index("Annual Report 2024"), (
        f"the 2025 report sits below 2024 — not in its descending-order position: {cards}"
    )
    newer = [i for i, t in enumerate(cards) if re.search(r"Annual Report (20[3-9]\d|202[6-9])\b", t)]
    assert all(i < index for i in newer), f"a newer-year card sits below the 2025 report: {cards}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Publication Year validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Publication Year unselected blocks save")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143731
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_year_unselected_blocks_save(page, disposable):
    # Azure TC 143731 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("143731"), publication_year=None),
                    "no Publication Year", expect_in_evidence=r"publicationYear|Publication Year")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Publication Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Publication Date is entered, saved and persists on reload")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143732
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_date_valid_saved(page, disposable):
    # Azure TC 143732 | PBI 130712 | account: Site Content Editor. 2025-03-15
    # is entered as 15/03/2025 (the field's own dd/mm/yyyy format).
    admin = _editor(page)
    entry = _create(admin, disposable, _data(_title("143732"), publication_date="15/03/2025"), publish=False)
    admin.open_entry(entry)
    shown, stored = admin.publication_date_value(), admin.stored_publication_date()
    assert stored == "2025-03-15" and shown == "15/03/2025", (
        f"Publication Date did not persist as 2025-03-15 on reload: form shows {shown!r}, stored {stored!r}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Publication Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Publication Date empty blocks save")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143733
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_date_empty_blocks_save(page, disposable):
    # Azure TC 143733 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("143733"), publication_date=None),
                    "no Publication Date", expect_in_evidence=r"publicationDate|Publication Date|date")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Publication Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An invalid Publication Date (32/13/2025) is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143734
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publication_date_invalid_format_rejected(page, disposable):
    # Azure TC 143734 | PBI 130712 | account: Site Content Editor. Rejected =
    # the save is blocked AND an invalid-date message is shown; a stored
    # (coerced) date is a product failure.
    admin = _editor(page)
    title = _title("143734")
    ids_before = admin.snapshot_ids()
    redirected, message, evidence, stored_on_form = False, "", {}, ""
    try:
        admin.open_new_entry_form()
        admin.fill_report(_data(title, publication_date=None))
        admin.set_publication_date("32/13/2025")
        message = admin.date_field_message()
        stored_on_form = admin.stored_publication_date()
        allure.attach(f"typed 32/13/2025 -> box {admin.publication_date_value()!r}, stored {stored_on_form!r}, "
                      f"message {message!r}", name="Publication Date after typing")
        _pinned(admin, ROLE_EDITOR)
        admin.publish()
        redirected = admin.save_redirected()
        evidence = admin.refusal_evidence()
        admin.screenshot("143734 after Publish")
    finally:
        entry = _register(admin, disposable, title, ids_before)
    if entry is not None:
        admin.open_entry(entry)
        pytest.fail(f"PRODUCT: Save with Publication Date 32/13/2025 was NOT blocked — a record was created "
                    f"storing {admin.stored_publication_date()!r} (form shows {admin.publication_date_value()!r})")
    assert not redirected and admin.submit_blocked(), f"Save with 32/13/2025 was not refused: {evidence}"
    date_error = bool(re.search(r"invalid|valid date|dd/mm/yyyy", message, re.I)) or any(
        re.search(r"invalid|valid date", m or "", re.I) for m in evidence.get("native_messages", {}).values())
    assert date_error, (
        f"the save was blocked, but no invalid-date message was shown (inline {message!r}; the browser only "
        f"reported {evidence.get('native_messages')})"
    )


# ===========================================================================
# Page Count (143735-143739)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Page Count (20) is saved and displayed as 20 Pages")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143735
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_saved_persists_cp(page, disposable, anon_pages):
    # Azure TC 143735 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    _, view, index = _publish_and_find(admin, disposable, anon_pages, _data(_title("143735"), page_count="20"))
    meta = " ".join(view.card_meta(index).split())
    assert "20 Pages" in meta, f"the card meta line reads {meta!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Page Count empty blocks save")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143736
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_empty_blocks_save(page, disposable):
    # Azure TC 143736 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("143736"), page_count=None), "an empty Page Count",
                    expect_in_evidence=r"pageCount|Page Count")


def _page_count_rejected(admin, disposable, tc_id: str, value: str) -> None:
    """Page Count = `value` must be refused on save with a positive-integer
    message and must not be stored."""
    title = _title(tc_id)
    ids_before = admin.snapshot_ids()
    redirected, evidence, messages = False, {}, ""
    try:
        admin.open_new_entry_form()
        admin.fill_report(_data(title, page_count=value))
        _pinned(admin, ROLE_EDITOR)
        admin.publish()
        redirected = admin.save_redirected()
        evidence = admin.refusal_evidence()
        messages = admin.visible_messages_text()
        admin.screenshot(f"{tc_id} after Publish with Page Count {value}")
        allure.attach(f"{evidence}\nmessages: {messages}", name=f"Page Count = {value}")
    finally:
        entry = _register(admin, disposable, title, ids_before)
    if entry is not None:
        admin.open_entry(entry)
        stored = admin.number_field_value(FIELD_PAGE_COUNT)
        admin.open_entries_list()
        pytest.fail(f"PRODUCT: Page Count = {value} was NOT rejected — the record was saved with Page Count "
                    f"{stored!r} (status {admin.row_status(entry)!r}); expected a positive-integer validation error")
    assert not redirected and admin.submit_blocked(), f"Save with Page Count = {value} was not refused: {evidence}"
    assert re.search(r"positive|greater than|at least|minimum|must be", messages, re.I) or re.search(
        r"greater than or equal|must be", repr(evidence.get("native_messages")), re.I), (
        f"Page Count = {value} was refused, but without a positive-integer message: {messages or evidence}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count = 0 is rejected as invalid")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143737
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_zero_rejected(page, disposable):
    # Azure TC 143737 | PBI 130712 | account: Site Content Editor
    _page_count_rejected(_editor(page), disposable, "143737", "0")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A negative Page Count (-5) is rejected as invalid")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143738
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_negative_rejected(page, disposable):
    # Azure TC 143738 | PBI 130712 | account: Site Content Editor
    _page_count_rejected(_editor(page), disposable, "143738", "-5")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A non-numeric Page Count (abc) is rejected as invalid")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143739
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_page_count_non_numeric_rejected(page, disposable):
    # Azure TC 143739 | PBI 130712 | account: Site Content Editor. A number
    # input that refuses the keystrokes is a rejection; the value must never
    # be held or stored, and a held value must block the save.
    admin = _editor(page)
    title = _title("143739")
    ids_before = admin.snapshot_ids()
    held, redirected, evidence = "", False, {}
    try:
        admin.open_new_entry_form()
        admin.fill_report(_data(title, page_count=None))
        admin.type_into_number(FIELD_PAGE_COUNT, "abc")
        held = admin.number_field_value(FIELD_PAGE_COUNT)
        allure.attach(f"typed 'abc' -> field holds {held!r}", name="Page Count after typing")
        _pinned(admin, ROLE_EDITOR)
        admin.publish()
        redirected = admin.save_redirected()
        evidence = admin.refusal_evidence()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    if entry is not None:
        admin.open_entry(entry)
        stored = admin.number_field_value(FIELD_PAGE_COUNT)
        assert "abc" not in stored, f"PRODUCT: Page Count persisted {stored!r}"
        pytest.fail(f"PRODUCT: the save with Page Count 'abc' was NOT blocked — the record was created with "
                    f"Page Count {stored!r}")
    assert held != "abc", "Page Count accepted the non-numeric text 'abc'"
    assert not redirected and admin.submit_blocked(), f"the save was not refused: {evidence}"


# ===========================================================================
# PDF Attachment (143740, 143781-143784, 143797)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid PDF (4MB) is uploaded and the record publishes successfully")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143740
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_valid_pdf_uploaded_publishes_cp(page, disposable, anon_pages):
    # Azure TC 143740 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    data = _data(_title("143740"), pdf_stem="report_143740")
    entry, view, index = _publish_and_find(admin, disposable, anon_pages, data)
    downloaded = view.download_via(view.card_download_link(index))
    expected_size = os.path.getsize(admin.DEFAULT_PDF)
    allure.attach(f"{downloaded}\nuploaded {data['pdf_uploaded_as']} ({expected_size} bytes)", name="download")
    assert downloaded["head"] == b"%PDF-", f"the download is not a PDF: {downloaded}"
    assert downloaded["size"] == expected_size, (
        f"the downloaded file ({downloaded['size']} bytes) does not match the uploaded PDF ({expected_size} bytes)"
    )
    assert os.path.splitext(data["pdf_uploaded_as"])[0] in downloaded["name"], (
        f"the downloaded file is {downloaded['name']!r}, not the uploaded {data['pdf_uploaded_as']!r}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title('Publishing without a PDF attachment is blocked with "A PDF attachment is required."')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130712
@pytest.mark.tc_143781
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_pdf_missing_blocks_publish(page, disposable):
    # Azure TC 143781 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("143781"), pdf_path=None), "no PDF Attachment",
                    expect_in_evidence=r"pdfAttachment|PDF", expected_message=MSG_PDF_REQUIRED,
                    wording_bug=WORDING_BUG_PDF_REQUIRED)


def _pdf_upload_rejected(admin, tc_id: str, fixture: str, what: str, wording_bug: str | None = None) -> None:
    admin.open_new_entry_form()
    admin.fill_report({"title": _title(tc_id)})
    result = admin.attempt_upload(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/{fixture}")
    admin.screenshot(f"{tc_id} after the {what} upload attempt")
    allure.attach(repr(result), name=f"{what} upload attempt")
    attached = result["file"] in (result.get("field_value") or "")
    shown = " | ".join(result["errors"] + result.get("field_errors", []) + [result.get("field_block_text", ""),
                                                                            result.get("picker_text", "")])
    assert not attached, f"the {what} was attached as the PDF Attachment: {result}"
    assert result["errors"] or result.get("field_errors") or result.get("picker_text"), (
        f"the {what} was not attached, but no rejection message was shown at all: {result}"
    )
    _check_wording(
        MSG_UNSUPPORTED_FILE, shown, wording_bug,
        f"the {what} was not attached, but the message {MSG_UNSUPPORTED_FILE!r} the case requires was not shown; "
        f"shown instead: {result['errors'] or result.get('field_errors') or '(nothing)'}; upload response "
        f"success={result['success']} HTTP {result['status']} body {result['body'][:200]!r}",
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('An unsupported PDF Attachment format (.docx) is rejected with "Unsupported file type or size."')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143782
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_pdf_unsupported_format_rejected(page):
    # Azure TC 143782 | PBI 130712 | account: Site Content Editor. Nothing is saved.
    _pdf_upload_rejected(_editor(page), "143782", "unsupported_report.docx", "report.docx",
                         wording_bug=WORDING_BUG_UNSUPPORTED_PDF)


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('An oversized PDF Attachment (6MB) is rejected with "Unsupported file type or size."')
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143783
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_pdf_oversized_rejected(page):
    # Azure TC 143783 | PBI 130712 | account: Site Content Editor. Nothing is saved.
    _pdf_upload_rejected(_editor(page), "143783", "oversized_pdf_6mb.pdf", "6MB PDF")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A PDF exactly at the 5MB boundary is accepted")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143784
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_pdf_at_5mb_boundary_accepted(page, disposable):
    # Azure TC 143784 | PBI 130712 | account: Site Content Editor.
    boundary = f"{FIXTURES}/annual_report_qctest_pdf_exactly_5mb.pdf"
    assert os.path.getsize(boundary) == 5 * 1024 * 1024, "fixture is not exactly 5 MiB"
    admin = _editor(page)
    title = _title("143784")
    data = _data(title, pdf_path=None)
    ids_before = admin.snapshot_ids()
    result, entry, accepted = {}, None, False
    try:
        admin.open_new_entry_form()
        admin.fill_report(data)
        result = admin.attempt_upload(FIELD_PDF_ATTACHMENT, boundary)
        allure.attach(repr(result), name="5 MiB PDF upload attempt")
        accepted = result["file"] in (result.get("field_value") or "")
        if accepted:
            _pinned(admin, ROLE_EDITOR)
            admin.publish()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    assert accepted, f"the PDF of exactly 5.00 MB was NOT accepted by the upload: {result}"
    assert admin.save_redirected() and entry is not None, f"Publish did not succeed: {admin.refusal_evidence()}"
    _assert_published(admin, entry)


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A previously publish-blocked record succeeds once its missing PDF is added")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130712
@pytest.mark.tc_143797
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_publish_blocked_then_succeeds_after_pdf_added_cp(page, disposable, anon_pages):
    # Azure TC 143797 | PBI 130712 | account: Site Content Editor.
    admin = _editor(page)
    title = _title("143797")
    data = _data(title, pdf_path=None)
    ids_before = admin.snapshot_ids()
    first_blocked, first_messages, first_evidence, retried = False, "", {}, False
    try:
        admin.open_new_entry_form()
        admin.fill_report(data)
        _pinned(admin, ROLE_EDITOR)
        admin.publish()
        first_blocked = admin.submit_blocked() and not admin.save_redirected()
        first_messages, first_evidence = admin.visible_messages_text(), admin.refusal_evidence()
        admin.screenshot("143797 first publish attempt")
        if first_blocked:
            # Step 2-3 — attach a valid PDF on the same form and retry.
            admin.upload_file(FIELD_PDF_ATTACHMENT, admin.DEFAULT_PDF, "report_143797")
            _pinned(admin, ROLE_EDITOR)
            admin.publish()
            retried = admin.save_redirected()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    allure.attach(f"first attempt blocked={first_blocked}, messages={first_messages!r}, evidence={first_evidence}",
                  name="first publish attempt (no PDF)")
    assert first_blocked, f"PRODUCT: Publish without a PDF was NOT blocked (record {entry})"
    assert retried and entry is not None, f"the retry with a PDF attached did not publish: {admin.refusal_evidence()}"
    _assert_published(admin, entry)
    _require_active_status(admin, entry)
    _visible_publicly(anon_pages, title)
    _check_wording(
        MSG_PDF_REQUIRED, first_messages, WORDING_BUG_PDF_REQUIRED,
        f"the first Publish was blocked, but not with {MSG_PDF_REQUIRED!r}; shown instead: "
        f"{first_messages or 'only the browser’s native bubble ' + repr(first_evidence.get('native_messages'))}",
    )


# ===========================================================================
# Active Status (143785, 143786)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Selecting Active Status takes effect and the record appears live")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143785
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_active_status_published_takes_effect_cp(page, disposable, anon_pages):
    # Azure TC 143785 | PBI 130712 | account: Site Content Editor. The case's
    # "Active Status=Published" = the record's Active Status set to active,
    # saved with the Editor's Publish.
    admin = _editor(page)
    title = _title("143785")
    data = _data(title, active_status=None)
    ids_before = admin.snapshot_ids()
    selected, problem = False, ""
    try:
        admin.open_new_entry_form()
        admin.fill_report(data)
        selected = admin.try_set_active_status(True)
        problem = admin.active_status_problem
        allure.attach(f"selected={selected}\n{getattr(admin, 'active_status_probe', {})}\n{problem}",
                      name="Active Status selection (network evidence)")
        admin.screenshot("143785 Active Status")
        _pinned(admin, ROLE_EDITOR)
        admin.publish()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    assert selected, f"PRODUCT: Active Status could not be selected: {problem}"
    assert admin.save_redirected() and entry is not None, f"the save did not go through: {admin.refusal_evidence()}"
    _assert_published(admin, entry)
    _require_active_status(admin, entry)
    _visible_publicly(anon_pages, title)


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Annual Reports — Control Panel")
@allure.story("Active Status")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leaving Active Status unselected on a new record blocks save")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130712
@pytest.mark.tc_143786
@ANNUAL_REPORTS_CMS_XDIST_GROUP
def test_active_status_unselected_blocks_save(page, disposable):
    # Azure TC 143786 | PBI 130712 | account: Site Content Editor. Active
    # Status is deliberately left unticked (the case is about it being unset).
    admin = _editor(page)
    # Live: the checkbox is TICKED by default, so it is unticked explicitly.
    _assert_blocked(admin, disposable, _data(_title("143786"), active_status=False), "Active Status unselected",
                    expect_in_evidence=r"activeStatus|Active Status")


# ===========================================================================
# Manual cases (registered, not automated)
# ===========================================================================
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130712
@pytest.mark.tc_143792
@allure.title("Deleting a report whose PDF link is open in another tab degrades gracefully")
@MANUAL_SKIP
def test_delete_with_pdf_open_in_other_tab_degrades_gracefully(page):
    ...


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130712
@pytest.mark.tc_143795
@allure.title("An interrupted publish (network drop) leaves the record in its prior state")
@MANUAL_SKIP
def test_interrupted_publish_leaves_prior_state(page):
    ...

"""
cms/tests/al_moltaqa_magazine/test_al_moltaqa_magazine_control_panel.py —
Control_Panel-tagged cases for PBI 130710 ("QC - Insights & Media - 002 -
Al-Moltqa Magazine"), Azure suite 140369 in plan 137724.

Holds every case whose tags include `Control_Panel`, including the
Control_Panel-side test of every case tagged BOTH `Web` and `Control_Panel`
(the Web-side test lives in web/tests/al_moltaqa_magazine/ under the SAME
`tc_<id>` marker). 144112 is tagged Manual and has no script.

REWORKED 2026-10-02 for the seven-state editorial workflow and the
re-provisioned role accounts (standards.md "Named CMS User Roles" and
"Content Editorial Workflow"):
  - Every case runs as the account it names — Site Content Editor (156488)
    or Site Content Author (156492) — in an auth-free context
    (`AUTH_FREE_PAGE`), and the signed-in userId is re-checked before each
    lifecycle step. TEST_USER is used only by the `disposable` teardown, to
    delete the test's OWN record.
  - The Editor's submit button reads "Publish" and publishes directly; the
    Author's reads "Submit for Review". Unpublish is the row action
    `data-qc-oel-unpublish` and lands on UNPUBLISHED (not Draft). Workflow
    moves are evidenced by the row's History trail.
  - Records are disposable `QCTEST-130710-<tc>-<stamp>` issues. The Entry
    column of this object shows the externalReferenceCode, not the title, so
    a record's identity (title + entry id + code) is captured right after
    creation by diffing the list's ids and reading the new record's title
    back; teardown deletes only that captured record (see the Page Object's
    DELETE SAFETY notes).
  - Active Status gates public visibility (standards.md). On this object the
    Active Status control is a "select from list" with NO options, so it
    cannot be ticked through Object Authoring. Every public check first
    verifies the stored Active Status (`_require_active_status`) and fails
    with that product finding when it is not stored as ticked.
  - Public checks use a fresh logged-out context and the case's propagation
    budget (cms-profile.md: poll 5 s, 0.5 s interval) once the CMS reports the
    new state.

Substitutions disclosed (case literal -> what runs):
  - "QCTEST-MAG-2xx" titles -> unique `QCTEST-130710-<tc>-<stamp> …` titles;
    literal display values the cases name ("Economic Magazine", "المجلة
    الاقتصادية", "Issue #69", the description text) are kept as the visible
    suffix/value where they would otherwise collide with the real issues.
  - 144116 "issue A dated 01/04/2026" -> 01/06/2026: the real issues are dated
    May 2026, so an April issue can never be the Latest Issue; C keeps
    01/07/2026, preserving A-older-than-C.
  - File names (cover_208.jpg, issue211.pdf, …) -> uniquely named copies of
    the fixtures (Documents & Media refuses repeated same-name uploads).

SKIPPED / GATED:
  - 144128, 144132, 144212, 144216: field-length limitation cases, skipped by
    QA decision 2026-10-02.
  - 144118: would take the REAL shared public page (layout plid 590) offline;
    gated behind QC_ALLOW_MAGAZINE_PAGE_OUTAGE=590 (standards.md
    Destructive-Precondition rule 5) — and even then there is no Object
    Authoring control for a page-level status.
  - 144119-144121, 144206-144208: no "Al-Moltaqa Magazine Page" settings
    object exists (re-confirmed 2026-10-02: the Objects nav lists only
    manage-magazine-issue for this PBI).
"""

from __future__ import annotations

import os
import re
from datetime import datetime

import allure
import pytest

from cms.pages.al_moltaqa_magazine.magazine_issue_admin_page import (
    ACTIVE_STATUS_UNAVAILABLE,
    STATUS_INACTIVE,
    FIELD_ARTICLE_COUNT,
    FIELD_COVER_IMAGE,
    FIELD_ISSUE_DESCRIPTION_EN,
    FIELD_ISSUE_TITLE_AR,
    FIELD_ISSUE_TITLE_EN,
    FIELD_PAGE_COUNT,
    FIELD_PDF_ATTACHMENT,
    MSG_DRAFT_SAVED,
    MSG_MOVED_TO_RECYCLE_BIN,
    MSG_SAVED_AND_PUBLISHED,
    MSG_SUBMITTED_FOR_REVIEW,
    PUBLIC_PAGE_PLID,
    QCTEST_PREFIX,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    CreatedEntry,
    MagazineIssueAdminPage,
    MagazinePublicView,
)
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

PBI = "130710"
MAGAZINE_CMS_XDIST_GROUP = pytest.mark.xdist_group("al_moltaqa_magazine_cms")
AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
FIXTURES = "cms/tests/al_moltaqa_magazine/fixtures"
STAMP = datetime.now().strftime("%m%d%H%M%S")

# A publish was measured at 27-30 s to reach Published on a sibling object.
PUBLISH_CONFIRM_TIMEOUT = 120.0
# cms-profile.md "Publish / Propagation Latency Budget" and the cases: poll 5 s @ 0.5 s.
PUBLIC_REFLECT_TIMEOUT = 5.0
PUBLIC_POLL = 0.5

FIELD_LENGTH_SKIP = pytest.mark.skip(reason="Field-length limitation case skipped by QA decision 2026-10-02")
NO_PAGE_OBJECT_REASON = (
    "BLOCKED (re-confirmed live 2026-10-02 as Site Content Editor): no 'Al-Moltaqa Magazine Page' settings "
    "object exists — the Objects nav (278 manage-* links) lists only manage-magazine-issue for this PBI, so "
    "there is no Page Title EN/AR field to save or validate. The hero title is rendered by the page itself."
)
OUTAGE_APPROVED = os.getenv("QC_ALLOW_MAGAZINE_PAGE_OUTAGE", "") == PUBLIC_PAGE_PLID


def _title(tc_id: str, suffix: str = "") -> str:
    """`QCTEST-130710-<tc>-<stamp>[ suffix]` — the only namespace any delete accepts."""
    return f"{QCTEST_PREFIX}{tc_id}-{STAMP}" + (f" {suffix}" if suffix else "")


def _data(title: str, **overrides) -> dict:
    return MagazineIssueAdminPage.default_data(title, **overrides)


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
        cleaner = MagazineIssueAdminPage(ctx.new_page())
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


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def _login(page, role: str) -> tuple[MagazineIssueAdminPage, str]:
    """Signs in as `role` in this auth-free context; skips (never falls back)
    when the account cannot sign in or is not the pinned one."""
    admin = MagazineIssueAdminPage(page)
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


def _editor(page) -> MagazineIssueAdminPage:
    return _login(page, ROLE_EDITOR)[0]


def _pinned(admin: MagazineIssueAdminPage, role: str) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == ROLE_USER_IDS[role], (
        f"the session is now userId {user_id!r}, not the pinned {role} ({ROLE_USER_IDS[role]}) — it dropped "
        f"and was re-authenticated as another account, so nothing from here on is attributable to {role}"
    )


def _register(admin, disposable, key_value: str, ids_before: set,
              key_field: str = FIELD_ISSUE_TITLE_EN) -> CreatedEntry | None:
    """Registers for teardown the ONE new record whose `key_field` reads
    `key_value`. Never raises (registration must not mask the test result)."""
    try:
        entry = admin.identify_created(key_value, ids_before, key_field)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001
        allure.attach(repr(exc), name=f"registration of {key_value!r} failed")
        return None


def _create(admin, disposable, data: dict, publish: bool, role: str = ROLE_EDITOR) -> CreatedEntry:
    """Creates one issue (publish=True -> the role's submit button, else Save as
    Draft), registers whatever got created for teardown, THEN asserts.
    `admin.create_banners` holds the banners shown right after the save."""
    ids_before = admin.snapshot_ids()
    went_through, diagnostics, entry = False, "", None
    expected = (MSG_DRAFT_SAVED if not publish
                else MSG_SUBMITTED_FOR_REVIEW if role == ROLE_AUTHOR else MSG_SAVED_AND_PUBLISHED)
    try:
        admin.open_new_entry_form()
        admin.fill_issue(data)
        _pinned(admin, role)
        admin.publish() if publish else admin.save_as_draft()
        went_through = admin.save_redirected()
        diagnostics = f"evidence {admin.refusal_evidence()}, banners {admin.feedback_banners()}"
        admin.create_banners = admin.success_banners(8.0, expected=expected) if went_through else []
    finally:
        entry = _register(admin, disposable, data["title"], ids_before)
    assert went_through, f"creating {data['title']!r} did not go through: {diagnostics}"
    assert entry is not None, f"{data['title']!r} went through but is not identifiable as exactly one NEW record"
    return entry


def _wait_status(admin, entry: CreatedEntry, expected: str, timeout: float = PUBLISH_CONFIRM_TIMEOUT) -> str:
    seen = {"status": ""}

    def _reached() -> bool:
        admin.open_entries_list()
        seen["status"] = admin.row_status(entry)
        return seen["status"] == expected

    try:
        wait_until(_reached, timeout=timeout, poll=3.0)
    except WaitTimeoutError:
        pass
    return seen["status"]


def _assert_published(admin, entry: CreatedEntry, actor: str = "Test Editor") -> None:
    """Waits for the row to read PUBLISHED. On this object a published issue
    whose Active Status is not stored reads INACTIVE instead; that is reported
    as the product finding it is (with the History evidence of the publish)."""
    status = _wait_status_any(admin, entry, (STATUS_PUBLISHED, STATUS_INACTIVE))
    if status == STATUS_INACTIVE:
        # Live 2026-10-02: History records the Editor's publish as the workflow
        # transition "Approved", immediately followed by "Deactivated".
        trail = admin.history(entry)
        allure.attach(repr(trail), name=f"History of {entry.title}")
        actions = [f"{h['action']} ({h['who']})" for h in trail]
        approved = any(h["who"] == actor and re.search(r"publish|approv", h["action"], re.I) for h in trail)
        deactivated = any(re.search(r"deactivat", h["action"], re.I) for h in trail)
        pytest.fail(
            f"PRODUCT: after Publish the issue's status reads {STATUS_INACTIVE!r}, not {STATUS_PUBLISHED!r}. "
            f"History {'records' if approved else 'does NOT record'} the publish by {actor!r}"
            f"{' and then an automatic Deactivated' if deactivated else ''} (trail, newest first: {actions}). "
            f"Active Status as recorded by THIS run's set attempt: "
            f"{admin.active_status_problem or 'no problem was recorded when it was set (cause not established)'}."
        )
    assert status == STATUS_PUBLISHED, f"the issue never reached {STATUS_PUBLISHED!r} (last status {status!r})"


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


def _history_has(admin, entry: CreatedEntry, actor: str, pattern: str) -> list[dict]:
    history = admin.history(entry)
    allure.attach(repr(history), name=f"History of {entry.title}")
    return [h for h in history if h["who"] == actor and re.search(pattern, h["action"] or h["text"], re.I)]


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


def _public_until(anon_pages, predicate, message: str, locale: str = "en") -> MagazinePublicView:
    """Publish-then-poll on the delivery surface in ONE logged-out context."""
    view = MagazinePublicView(anon_pages())

    def _check() -> bool:
        view.open_magazine_anonymous(locale)
        return bool(predicate(view))

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL, message=message)
    except WaitTimeoutError:
        pytest.fail(f"{message} within {PUBLIC_REFLECT_TIMEOUT:.0f}s (latest {view.latest_title_text()!r}, "
                    f"cards {view.card_titles()})")
    return view


def _visible_publicly(anon_pages, title: str, locale: str = "en") -> tuple[MagazinePublicView, dict]:
    where = {}

    def _found(view) -> bool:
        where.update(view.find_title(title))
        return where["latest"] or where["archive_index"] >= 0

    view = _public_until(anon_pages, _found, f"DELIVERY: {title!r} never became visible to a logged-out visitor",
                         locale)
    return view, where


def _assert_not_public(anon_pages, title: str, locale: str = "en") -> None:
    """Absence that cannot pass vacuously: the page must render, and a
    POSITIVE control (a visible real card) must be findable through the same
    search box before `title` is searched and required absent."""
    view = MagazinePublicView(anon_pages()).open_magazine_anonymous(locale)
    cards = view.card_titles()
    if not cards:
        pytest.fail(f"cannot prove {title!r} is absent: the logged-out page shows no archive cards")
    control = cards[0]
    view.search(control)
    if control not in view.card_titles():
        pytest.fail(f"positive control failed: visible card {control!r} is not found through the public search box")
    where = view.find_title(title)
    assert not where["latest"] and where["archive_index"] < 0, (
        f"{title!r} is visible to a logged-out visitor (latest={where['latest']}, "
        f"archive index={where['archive_index']})"
    )


def _assert_not_public_within_budget(anon_pages, title: str) -> None:
    gone = {"ok": False}

    def _absent(view) -> bool:
        where = view.find_title(title)
        gone["ok"] = not where["latest"] and where["archive_index"] < 0
        return gone["ok"]

    _public_until(anon_pages, _absent, f"{title!r} was still visible to a logged-out visitor")
    _assert_not_public(anon_pages, title)


def _assert_blocked(admin, disposable, data: dict, what: str, action: str = "publish",
                    key_field: str = FIELD_ISSUE_TITLE_EN, expect_in_evidence: str | None = None) -> dict:
    """Fills a NEW form with `data`, clicks Publish (Editor) or Save as Draft,
    and requires the attempt to be refused with validation evidence and NO
    record created. Anything created is registered for teardown first."""
    ids_before = admin.snapshot_ids()
    redirected, blocked, evidence, entry = False, False, {}, None
    try:
        admin.open_new_entry_form()
        admin.fill_issue(data)
        _pinned(admin, ROLE_EDITOR)
        admin.publish() if action == "publish" else admin.save_as_draft()
        redirected = admin.save_redirected()
        blocked = admin.submit_blocked()
        evidence = admin.refusal_evidence()
        allure.attach(repr(evidence), name=f"refusal evidence ({what})")
    finally:
        entry = _register(admin, disposable, data[{FIELD_ISSUE_TITLE_EN: "title",
                                                   FIELD_ISSUE_TITLE_AR: "title_ar"}[key_field]],
                          ids_before, key_field)
    if entry is not None:
        admin.open_entries_list()
        status = admin.row_status(entry)
        pytest.fail(f"PRODUCT: {action} was NOT blocked with {what} — a record was created "
                    f"(status {status!r}, code {entry.code})")
    assert blocked and not redirected, (
        f"{action} with {what} was neither refused with validation evidence nor saved: "
        f"redirected={redirected}, evidence={evidence}"
    )
    if expect_in_evidence:
        text = repr(evidence)
        assert re.search(expect_in_evidence, text, re.I), (
            f"{action} was refused, but the validation evidence does not point at {what}: {evidence}"
        )
    return evidence


def _observe_publish_with_value(admin, disposable, tc_id: str, field: str, attempted: str, what: str) -> dict:
    """EXTRA OBSERVATION (never changes pass/fail): the case says "Click Save",
    which is Save as Draft — and Save as Draft skips required checks
    (standards.md). This also tries Publish with the same value on a SEPARATE
    disposable record and attaches what happened. Anything created is
    registered for teardown first."""
    title = _title(tc_id, "publish-observation")
    result = {"title": title, "value": attempted, "publish_blocked": None, "record_created": False,
              "stored": "", "status": "", "evidence": {}, "error": ""}
    try:
        ids_before = admin.snapshot_ids()
        try:
            admin.open_new_entry_form()
            admin.fill_issue(_data(title))
            admin.fill_number(field, attempted)
            _pinned(admin, ROLE_EDITOR)
            admin.publish()
            result["publish_blocked"] = admin.submit_blocked()
            result["evidence"] = admin.refusal_evidence()
        finally:
            entry = _register(admin, disposable, title, ids_before)
        if entry is not None:
            result["record_created"] = True
            admin.open_entry(entry)
            result["stored"] = admin.number_field_value(field)
            admin.open_entries_list()
            result["status"] = admin.row_status(entry)
    except Exception as exc:  # noqa: BLE001 — observation only, never the verdict
        result["error"] = repr(exc)[:400]
    verdict = ("BLOCKED" if result["publish_blocked"] and not result["record_created"]
               else "NOT blocked (record created)" if result["record_created"] else "inconclusive")
    allure.attach(f"Publish with {what}: {verdict}\n{result}", name=f"OBSERVATION - Publish with {what}")
    return result


def _assert_saved_value_rejected(admin, disposable, data: dict, field: str, attempted: str, what: str,
                                 tc_id: str | None = None) -> None:
    """Number-field cases: Save (as Draft) with `attempted` must be refused
    with a validation error and the value must not be persisted. With
    `tc_id`, Publish with the same value is also attempted and attached as an
    observation (it does not change the verdict)."""
    ids_before = admin.snapshot_ids()
    redirected, evidence, entry = False, {}, None
    try:
        admin.open_new_entry_form()
        admin.fill_issue(data)
        admin.fill_number(field, attempted)
        _pinned(admin, ROLE_EDITOR)
        admin.save_as_draft()
        redirected = admin.save_redirected()
        blocked_now = admin.submit_blocked()
        evidence = admin.refusal_evidence()
        allure.attach(repr(evidence), name=f"refusal evidence ({what})")
    finally:
        entry = _register(admin, disposable, data["title"], ids_before)
    if tc_id:
        _observe_publish_with_value(admin, disposable, tc_id, field, attempted, what)
    if entry is not None:
        admin.open_entry(entry)
        stored = admin.number_field_value(field)
        pytest.fail(f"PRODUCT: Save was NOT blocked for {what} — a Draft was created storing {field} = {stored!r} "
                    f"(code {entry.code}); expected a positive-integer validation error")
    assert blocked_now and not redirected, f"Save with {what} was not refused: evidence {evidence}"


# ===========================================================================
# 144101 / 144102 — Site Content Author
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Roles / Permissions")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Author can view and update an assigned magazine issue and save it as Draft")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130710
@pytest.mark.tc_144101
@MAGAZINE_CMS_XDIST_GROUP
def test_author_view_update_issue_as_draft(page, disposable):
    # Azure TC 144101 | PBI 130710 | account: Site Content Author (156492).
    # "Assigned issue" = an issue the Author owns (role sheet: Authors edit OWN content).
    admin, _ = _login(page, ROLE_AUTHOR)
    title = _title("144101")
    entry = _create(admin, disposable, _data(title), publish=False, role=ROLE_AUTHOR)

    # Step 2 — the issue opens in edit mode with all fields populated.
    admin.open_entry(entry)
    opened = admin.read_issue()
    allure.attach(repr(opened), name="opened values")
    assert opened["title"] == title and opened["title_ar"] and opened["description"] and opened["issue_number"], (
        f"the Author's issue did not open with its fields populated: {opened}"
    )
    assert admin.is_save_as_draft_enabled(), "Save as Draft is not available on the Author's own issue"

    # Step 3 — update Description EN.
    new_description = f"Updated by Author {title}"
    admin.fill_text(FIELD_ISSUE_DESCRIPTION_EN, new_description)
    assert admin.field_value(FIELD_ISSUE_DESCRIPTION_EN) == new_description

    # Step 4 — Save as Draft: Draft, success message, no Publish for this role.
    _pinned(admin, ROLE_AUTHOR)
    admin.save_as_draft()
    assert admin.save_redirected(), f"the Author's save was refused: {admin.refusal_evidence()}"
    banners = admin.success_banners(expected=MSG_DRAFT_SAVED)
    allure.attach("\n".join(admin.feedback_banners()) or "(none)", name="banners after the Author's save")
    _pinned(admin, ROLE_AUTHOR)
    admin.open_entry(entry)
    assert admin.field_value(FIELD_ISSUE_DESCRIPTION_EN) == new_description, "the update was not stored"
    form_actions = admin.form_action_labels()
    assert "Publish" not in form_actions, f"a Publish action is offered to the Author: {form_actions}"
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT, f"status is {admin.row_status(entry)!r}, not Draft"
    row_actions = admin.row_actions(entry)
    assert not {"publish", "approve", "unpublish"} & set(row_actions), (
        f"workflow publish actions are offered to the Author: {row_actions}"
    )
    assert admin.has_message(banners, MSG_DRAFT_SAVED), (
        f"no {MSG_DRAFT_SAVED!r} message after the Author's Save as Draft (the save itself went through); "
        f"non-refusal banners shown: {banners}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Roles / Permissions")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Author cannot publish a magazine issue")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130710
@pytest.mark.tc_144102
@MAGAZINE_CMS_XDIST_GROUP
def test_author_cannot_publish_issue(page, disposable, anon_pages):
    # Azure TC 144102 | PBI 130710 | account: Site Content Author (156492).
    admin, _ = _login(page, ROLE_AUTHOR)
    title = _title("144102")
    entry = _create(admin, disposable, _data(title), publish=False, role=ROLE_AUTHOR)

    # Step 2 — the Draft issue opens.
    admin.open_entry(entry)
    assert admin.issue_title_on_form() == title

    # Step 3 — no Publish control; status stays Draft; not public.
    form_actions = admin.form_action_labels()
    allure.attach(repr(form_actions), name="Author form actions")
    assert "Publish" not in form_actions, f"a Publish button is offered to the Author: {form_actions}"
    assert admin.submit_button_label() == "Submit for Review", (
        f"the Author's submit button reads {admin.submit_button_label()!r}"
    )
    _pinned(admin, ROLE_AUTHOR)
    admin.open_entries_list()
    row_actions = admin.row_actions(entry)
    assert not {"publish", "approve"} & set(row_actions), f"row publish actions offered to the Author: {row_actions}"
    assert admin.row_status(entry) == STATUS_DRAFT, f"status is {admin.row_status(entry)!r}, not Draft"
    _require_active_status(admin, entry)
    _assert_not_public(anon_pages, title)


# ===========================================================================
# 144104-144111 — Editor lifecycle
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Create / Draft")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor can create a new magazine issue in Object Authoring")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144104
@MAGAZINE_CMS_XDIST_GROUP
def test_editor_create_new_issue_save_as_draft(page, disposable):
    # Azure TC 144104 | PBI 130710 | account: Site Content Editor (156488)
    admin = _editor(page)
    title = _title("144104", "Autumn Trade Digest")
    data = _data(title, title_ar="ملخص التجارة الخريفي", issue_number="QCTEST-MAG-201",
                 description="Autumn Trade Digest — QCTEST disposable issue.",
                 description_ar="ملخص التجارة الخريفي — عدد تجريبي.",
                 issue_date="01/09/2026", page_count="32", article_count="8",
                 cover_stem="cover_201", pdf_stem="201")
    ids_before = admin.snapshot_ids()
    entry = None
    try:
        # Step 2 — Create New form: all fields empty, mandatory markers visible.
        admin.open_new_entry_form()
        empty = admin.read_issue()
        markers = admin.required_markers()
        allure.attach(f"{empty}\nrequired markers: {markers}", name="fresh form")
        filled_before = {k: v for k, v in empty.items() if k not in ("open_in_new_tab", "active_status") and v}
        assert not filled_before, f"the Create New form is not empty: {filled_before}"

        # Step 3 — every value populates without truncation.
        admin.fill_issue(data)
        filled = admin.read_issue()
        expected = {k: data[k] for k in ("title", "title_ar", "description", "description_ar", "issue_number",
                                         "page_count", "article_count", "issue_date")}
        mismatched = {k: (filled[k], v) for k, v in expected.items() if filled[k] != v}
        assert not mismatched, f"values did not populate as entered (got, want): {mismatched}"
        assert data["cover_uploaded_as"] in admin.uploaded_filename(FIELD_COVER_IMAGE)
        assert data["pdf_uploaded_as"] in admin.uploaded_filename(FIELD_PDF_ATTACHMENT)

        # Step 4 — Save as Draft.
        _pinned(admin, ROLE_EDITOR)
        admin.save_as_draft()
        went_through = admin.save_redirected()
        # The success message renders in the bar at the TOP of the page.
        banners = admin.top_messages(evidence="144104", expected=MSG_DRAFT_SAVED) if went_through else []
        allure.attach("\n".join(banners) or "(none)", name="top-of-page message after Save as Draft")
    finally:
        entry = _register(admin, disposable, title, ids_before)
    assert went_through and entry, f"Save as Draft did not create the issue: {admin.refusal_evidence()}"
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT, f"status is {admin.row_status(entry)!r}, not Draft"
    assert all(markers.values()), f"mandatory markers are not shown for every required field: {markers}"
    assert admin.has_message(banners, MSG_DRAFT_SAVED), (
        f"no {MSG_DRAFT_SAVED!r} message at the top of the page after Save as Draft on a new issue (the issue "
        f"itself was created); non-refusal banners shown: {banners}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Edit")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can edit an existing magazine issue")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144105
@MAGAZINE_CMS_XDIST_GROUP
def test_editor_edit_existing_issue(page, disposable):
    # Azure TC 144105 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144105")
    entry = _create(admin, disposable, _data(title, page_count="32"), publish=False)

    admin.open_entry(entry)
    assert admin.number_field_value(FIELD_PAGE_COUNT) == "32"
    admin.fill_number(FIELD_PAGE_COUNT, "36")
    assert admin.number_field_value(FIELD_PAGE_COUNT) == "36"
    _pinned(admin, ROLE_EDITOR)
    admin.save_as_draft()  # the Draft record's "Save"
    assert admin.save_redirected(), f"the edit save was refused: {admin.refusal_evidence()}"
    banners = admin.success_banners(expected=MSG_DRAFT_SAVED)
    allure.attach("\n".join(admin.feedback_banners()) or "(none)", name="banners after the edit save")
    admin.open_entry(entry)
    assert admin.number_field_value(FIELD_PAGE_COUNT) == "36", "Page Count 36 did not persist on reopen"
    assert admin.has_message(banners, MSG_DRAFT_SAVED), (
        f"no {MSG_DRAFT_SAVED!r} message after saving the edit (the edit itself was stored); "
        f"non-refusal banners shown: {banners}"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Draft / Unpublish visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A magazine issue saved as Draft does not appear on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144106
@MAGAZINE_CMS_XDIST_GROUP
def test_draft_issue_absent_from_public_page_cms(page, disposable, anon_pages):
    # Azure TC 144106 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144106")
    entry = _create(admin, disposable, _data(title), publish=False)

    admin.open_entry(entry)
    _pinned(admin, ROLE_EDITOR)
    admin.save_as_draft()
    assert admin.save_redirected(), f"Save as Draft was refused: {admin.refusal_evidence()}"
    banners = admin.success_banners(expected=MSG_DRAFT_SAVED)
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT, f"status is {admin.row_status(entry)!r}, not Draft"
    assert admin.has_message(banners, MSG_DRAFT_SAVED), f"no {MSG_DRAFT_SAVED!r} message after Save as Draft: {banners}"
    _require_active_status(admin, entry)
    _assert_not_public(anon_pages, title)


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Preview")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Preview shows draft content without affecting the live public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144107
@MAGAZINE_CMS_XDIST_GROUP
def test_preview_shows_draft_without_affecting_live(page, disposable, anon_pages):
    # Azure TC 144107 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144107", "Autumn Trade Digest")
    entry = _create(admin, disposable, _data(title), publish=True)
    _assert_published(admin, entry)

    # Step 1 — unsaved Title EN change in the edit form.
    admin.open_entry(entry)
    edited = f"{title} (Preview Edit)"
    admin.fill_text(FIELD_ISSUE_TITLE_EN, edited)
    assert admin.field_value(FIELD_ISSUE_TITLE_EN) == edited

    # Step 2 — Preview shows the unsaved title. The form offers no Preview
    # button of its own; the page's preview pane is the only in-form preview.
    preview = admin.preview_pane_text()
    allure.attach(preview[:2000] or "(no preview pane)", name="preview pane")
    assert edited in preview, (
        "Preview does not show the unsaved title: the edit form has no Preview action, and the page's preview "
        f"pane renders the SAVED record only (pane present: {bool(preview)})"
    )

    # Step 3 — the live page still shows the published title.
    _require_active_status(admin, entry)
    view, _ = _visible_publicly(anon_pages, title)
    assert edited not in view.card_titles() and view.latest_title_text().strip() != edited


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Delete")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can delete a magazine issue")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144110
@MAGAZINE_CMS_XDIST_GROUP
def test_editor_delete_issue(page, disposable):
    # Azure TC 144110 | PBI 130710 | account: Site Content Editor. Located by
    # its captured id + code and confirmed by its exact title, never by position.
    admin = _editor(page)
    title = _title("144110")
    entry = _create(admin, disposable, _data(title), publish=False)

    # Steps 1-2 — identity confirmed by id/code/title and the QCTEST- pattern.
    admin.open_entry(entry)
    assert admin.issue_title_on_form() == title and title.startswith(QCTEST_PREFIX)

    # Step 3 — delete (the guarded path) as the Editor.
    _pinned(admin, ROLE_EDITOR)
    deleted = admin.delete_disposable_entry(entry, await_message=True)
    allure.attach(f"dialogs {getattr(admin, 'last_delete_dialogs', [])}\n"
                  f"top-of-page message {getattr(admin, 'last_delete_banners', [])}", name="delete feedback")
    assert deleted, "the Editor's delete did not remove the issue"
    disposable.mark_removed(entry)

    # Step 4 — the listing no longer has it.
    admin.open_entries_list()
    assert admin.is_list_fully_expanded()
    assert not admin.row_present(entry)
    assert entry.code not in [r["code"] for r in admin.list_rows()]
    expected_message = MSG_MOVED_TO_RECYCLE_BIN.format(code=entry.code)
    assert admin.has_message(getattr(admin, "last_delete_banners", []), expected_message), (
        f"no {expected_message!r} message at the top of the page after the delete; non-refusal banners shown: "
        f"{getattr(admin, 'last_delete_banners', [])} (dialogs {getattr(admin, 'last_delete_dialogs', [])})"
    )


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Create / Draft")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Discarding changes while creating a new magazine issue does not save the record")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130710
@pytest.mark.tc_144111
@pytest.mark.skip(reason="Discard/Cancel control not required currently — QA decision 2026-10-04")
@MAGAZINE_CMS_XDIST_GROUP
def test_discard_new_issue_not_saved(page, disposable):
    # Azure TC 144111 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144111")
    ids_before = admin.snapshot_ids()
    controls = []
    try:
        admin.open_new_entry_form()
        admin.fill_issue({"issue_number": "QCTEST-MAG-202", "title": title})
        controls = admin.cancel_controls()
        allure.attach(repr(controls), name="Cancel/Discard controls on the create form")
        if controls:
            admin.click_cancel_control()
            banners = admin.success_banners(5.0)
            assert not banners, f"a save confirmation appeared after Discard/Cancel: {banners}"
    finally:
        entry = _register(admin, disposable, title, ids_before)
    assert controls, "the Create New form offers no Discard/Cancel control (only Save as Draft and Publish)"
    assert entry is None, f"Discard/Cancel still created the record (code {entry.code if entry else ''})"


# ===========================================================================
# 144108/144109/144115/144116/144117/144118 — Publish lifecycle
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing a magazine issue makes it visible as the Latest Issue on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144108
@MAGAZINE_CMS_XDIST_GROUP
def test_publish_updates_status_cms(page, disposable, anon_pages):
    # Azure TC 144108 | PBI 130710 | account: Site Content Editor (publishes directly)
    admin, editor_name = _login(page, ROLE_EDITOR)
    title = _title("144108", "Autumn Trade Digest")
    data = _data(title, issue_date="05/09/2026", issue_number="Issue #201")
    entry = _create(admin, disposable, data, publish=False)

    # Step 1-2 — open the Draft and Publish.
    admin.open_entry(entry)
    _pinned(admin, ROLE_EDITOR)
    admin.publish()
    assert admin.save_redirected(), f"Publish was refused: {admin.refusal_evidence()}"
    banners = admin.success_banners(expected=MSG_SAVED_AND_PUBLISHED)
    allure.attach("\n".join(admin.feedback_banners()) or "(none)", name="banners after Publish")
    _assert_published(admin, entry)
    assert _history_has(admin, entry, editor_name, r"publish|approv"), "History records no Publish by the Editor"
    assert any(MSG_SAVED_AND_PUBLISHED in b for b in banners), f"no 'Saved and published.' message: {banners}"

    # Step 3 — Latest Issue card on the public page.
    _require_active_status(admin, entry)
    view = _public_until(anon_pages, lambda v: v.latest_title_text().strip() == title,
                         f"DELIVERY: the Latest Issue card never showed {title!r}")
    latest = view.latest_snapshot()
    allure.attach(repr(latest), name="Latest Issue card")
    assert data["issue_number"] in latest["badges"], f"badge missing: {latest['badges']}"
    assert latest["description"] == data["description"], latest
    assert "September 2026" in latest["meta"] and "10 pages" in latest["meta"], latest
    assert latest["actions"] == ["Read Online", "Download PDF"], latest


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unpublishing a magazine issue removes it from the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144109
@MAGAZINE_CMS_XDIST_GROUP
def test_unpublish_updates_status_cms(page, disposable, anon_pages):
    # Azure TC 144109 | PBI 130710 | account: Site Content Editor
    admin, editor_name = _login(page, ROLE_EDITOR)
    title = _title("144109")
    entry = _create(admin, disposable, _data(title), publish=True)
    _assert_published(admin, entry)
    # Precondition: the issue really is public before it is unpublished.
    _require_active_status(admin, entry)
    _visible_publicly(anon_pages, title)

    # Step 2 — Unpublish (row action) -> Unpublished, not Draft.
    admin.open_entries_list()
    _pinned(admin, ROLE_EDITOR)
    dialogs = admin.run_row_action(entry, "unpublish")
    banners = admin.top_messages(evidence="144109")
    allure.attach(f"dialogs {dialogs}\ntop-of-page message {banners}", name="Unpublish feedback")
    assert _wait_status(admin, entry, STATUS_UNPUBLISHED, 60.0) == STATUS_UNPUBLISHED
    assert _history_has(admin, entry, editor_name, r"unpublish"), "History records no Unpublish by the Editor"

    # Step 3 — gone from the public page within the budget.
    _assert_not_public_within_budget(anon_pages, title)
    assert banners, f"no success message after Unpublish (dialogs {dialogs})"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published magazine issue persists after a page reload")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130710
@pytest.mark.tc_144115
@MAGAZINE_CMS_XDIST_GROUP
def test_published_issue_persists_after_reload_cms(page, disposable, anon_pages):
    # Azure TC 144115 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144115")
    data = _data(title, page_count="40")
    entry = _create(admin, disposable, data, publish=True)
    _assert_published(admin, entry)
    assert admin.has_message(admin.create_banners, MSG_SAVED_AND_PUBLISHED), (
        f"no {MSG_SAVED_AND_PUBLISHED!r} message after publishing the new issue: {admin.create_banners}"
    )

    _require_active_status(admin, entry)
    view, where = _visible_publicly(anon_pages, title)
    before = view.card_meta(where["archive_index"]) if where["archive_index"] >= 0 else view.latest_meta_text()
    view.open_magazine_anonymous()
    after_where = view.find_title(title)
    assert after_where["latest"] or after_where["archive_index"] >= 0, "the issue vanished after a reload"
    after = (view.card_meta(after_where["archive_index"]) if after_where["archive_index"] >= 0
             else view.latest_meta_text())
    assert " ".join(before.split()) == " ".join(after.split()), (before, after)

    admin.open_entry(entry)
    stored = admin.read_issue()
    assert stored["title"] == title and stored["page_count"] == "40", stored


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publishing a newer issue re-designates it as Latest Issue and moves the previous one to the Archive")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130710
@pytest.mark.tc_144116
@MAGAZINE_CMS_XDIST_GROUP
def test_publish_newer_redesignates_latest_cms(page, disposable, anon_pages):
    # Azure TC 144116 | PBI 130710 | account: Site Content Editor.
    # A dated 01/06/2026 (case: 01/04/2026 — see module docstring), C 01/07/2026.
    admin = _editor(page)
    title_a, title_c = _title("144116", "Issue A"), _title("144116", "Issue C")
    entry_a = _create(admin, disposable, _data(title_a, issue_date="01/06/2026"), publish=True)
    _assert_published(admin, entry_a)

    # Step 1 — A is the Latest Issue.
    _require_active_status(admin, entry_a)
    _public_until(anon_pages, lambda v: v.latest_title_text().strip() == title_a,
                  f"DELIVERY: issue A {title_a!r} never became the Latest Issue")

    # Step 2 — publish C.
    entry_c = _create(admin, disposable, _data(title_c, issue_date="01/07/2026"), publish=True)
    _assert_published(admin, entry_c)
    assert admin.has_message(admin.create_banners, MSG_SAVED_AND_PUBLISHED), (
        f"no {MSG_SAVED_AND_PUBLISHED!r} message after publishing issue C: {admin.create_banners}"
    )

    # Step 3 — C is Latest; A is the first Archive card.
    _require_active_status(admin, entry_c)
    view = _public_until(anon_pages, lambda v: v.latest_title_text().strip() == title_c,
                         f"DELIVERY: issue C {title_c!r} never became the Latest Issue")
    cards = view.card_titles_unfiltered()
    assert cards and cards[0] == title_a, f"issue A is not the first Archive card: {cards[:3]}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Draft / Unpublish visibility")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A draft magazine issue does not appear anywhere on the public Al-Moltaqa Magazine page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130710
@pytest.mark.tc_144117
@MAGAZINE_CMS_XDIST_GROUP
def test_draft_issue_absent_everywhere_cms(page, disposable, anon_pages):
    # Azure TC 144117 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144117")
    entry = _create(admin, disposable, _data(title, issue_date="01/10/2026"), publish=False)
    admin.open_entries_list()
    assert admin.row_status(entry) == STATUS_DRAFT

    _require_active_status(admin, entry)
    view = MagazinePublicView(anon_pages()).open_magazine_anonymous()
    assert view.is_latest_visible() and view.card_count() > 0, "the public page did not load normally"
    _assert_not_public(anon_pages, title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Al-Moltaqa Magazine page itself is not publicly reachable when unpublished")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130710
@pytest.mark.tc_144118
@pytest.mark.skipif(
    not OUTAGE_APPROVED,
    reason=(
        "GATED pending explicit user approval: this case must set the REAL, shared Al-Moltaqa Magazine page "
        f"(Liferay layout plid {PUBLIC_PAGE_PLID}, /al-moltaqa-magazine) to Unpublished, taking it off the "
        "public site. standards.md 'Destructive-Precondition Tests' rule 5 requires an ID-named approval; set "
        f"QC_ALLOW_MAGAZINE_PAGE_OUTAGE={PUBLIC_PAGE_PLID} to run."
    ),
)
def test_magazine_page_unreachable_when_unpublished(page):
    # Azure TC 144118 | PBI 130710. Even with the approval there is no Object
    # Authoring control for a page-level status (no page settings object), and
    # page layout is off-limits to automation (standards.md).
    pytest.skip(f"BLOCKED: no Object Authoring control sets the status of layout plid {PUBLIC_PAGE_PLID}; "
                f"page layout is off-limits to automation. {NO_PAGE_OBJECT_REASON}")


# ===========================================================================
# 144119-144121 / 144206-144208 — page settings (no such object)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Page Title EN is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144119
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_en_valid_saved_displayed(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Page Title EN rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144120
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_en_empty_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Title EN rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144121
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_en_whitespace_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings — Bilingual")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Page Title AR is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144206
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_ar_valid_saved_displayed(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings — Bilingual")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Page Title AR rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144207
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_ar_empty_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings — Bilingual")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Title AR rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144208
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_ar_whitespace_rejected(page):
    ...


# ===========================================================================
# Field cases — public display (Editor publishes, then the delivery surface)
# ===========================================================================
def _publish_and_find(admin, disposable, anon_pages, data: dict, locale: str = "en",
                      public_title: str | None = None):
    """Creates + publishes (Editor), waits for Published, verifies Active
    Status, then finds the issue on the public page -> (entry, view, where)."""
    entry = _create(admin, disposable, data, publish=True)
    _assert_published(admin, entry)
    assert admin.has_message(admin.create_banners, MSG_SAVED_AND_PUBLISHED), (
        f"no {MSG_SAVED_AND_PUBLISHED!r} message after publishing {data['title']!r}: {admin.create_banners}"
    )
    _require_active_status(admin, entry)
    view, where = _visible_publicly(anon_pages, public_title or data["title"], locale)
    return entry, view, where


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Number validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Issue Number is saved and displayed as the badge on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144122
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_number_valid_saved_displayed(page, disposable, anon_pages):
    # Azure TC 144122 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    data = _data(_title("144122"), issue_number="Issue #69")
    _, view, where = _publish_and_find(admin, disposable, anon_pages, data)
    badge = view.latest_badge_texts() if where["latest"] else [view.card_badge(where["archive_index"])]
    assert "Issue #69" in [b.strip() for b in badge], f"the issue's badge reads {badge}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Number validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Number rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144123
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_number_empty_rejected(page, disposable):
    # Azure TC 144123 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144123"), issue_number=""), "an empty Issue Number",
                    expect_in_evidence=r"issueNumber|Issue Number")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Number validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Number rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144124
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_number_whitespace_rejected(page, disposable):
    # Azure TC 144124 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144124"), issue_number="   "),
                    "a whitespace-only Issue Number", expect_in_evidence=r"issueNumber|Issue Number")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Issue Title EN is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144125
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_en_valid_saved_displayed(page, disposable, anon_pages):
    # Azure TC 144125 | PBI 130710 | account: Site Content Editor.
    # "Economic Magazine" is a REAL issue's title, so the disposable title ends with it.
    admin = _editor(page)
    title = _title("144125", "Economic Magazine")
    _, view, where = _publish_and_find(admin, disposable, anon_pages, _data(title))
    shown = view.latest_title_text().strip() if where["latest"] else view.card_title(where["archive_index"]).strip()
    assert shown == title, f"card title reads {shown!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title EN validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Issue Title EN rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144126
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_en_empty_rejected(page, disposable):
    # Azure TC 144126 | PBI 130710 | account: Site Content Editor. The unique
    # QCTEST identity is carried by Title AR, since Title EN is the field emptied.
    admin = _editor(page)
    data = {**_data(_title("144126")), "title": "", "title_ar": _title("144126", "AR")}
    _assert_blocked(admin, disposable, data, "an empty Issue Title EN", key_field=FIELD_ISSUE_TITLE_AR,
                    expect_in_evidence=r"issueTitleEN|Title \(EN\)|required")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Title EN rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144127
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_en_whitespace_rejected(page, disposable):
    # Azure TC 144127 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    data = {**_data(_title("144127")), "title": "   ", "title_ar": _title("144127", "AR")}
    _assert_blocked(admin, disposable, data, "a whitespace-only Issue Title EN", key_field=FIELD_ISSUE_TITLE_AR)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144128
@allure.title("Issue Title EN accepts exactly 200 characters and rejects 201 characters")
@FIELD_LENGTH_SKIP
def test_issue_title_en_200_boundary(page):
    ...


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Issue Description EN is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144129
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_en_valid_saved_displayed(page, disposable, anon_pages):
    # Azure TC 144129 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    desc = ("Al-Moltaqa Magazine Issue 68 covers Qatar's Q1 2026 economic outlook, trade statistics, "
            "and member spotlights.")
    _, view, where = _publish_and_find(admin, disposable, anon_pages, _data(_title("144129"), description=desc))
    shown = view.latest_desc_text().strip() if where["latest"] else view.card_desc(where["archive_index"]).strip()
    assert shown == desc, f"card description reads {shown!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description EN validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Issue Description EN rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144130
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_en_empty_rejected(page, disposable):
    # Azure TC 144130 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144130"), description=""), "an empty Issue Description EN",
                    expect_in_evidence=r"issueDescriptionEN|Description")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Description EN rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144131
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_en_whitespace_rejected(page, disposable):
    # Azure TC 144131 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144131"), description="   "),
                    "a whitespace-only Issue Description EN")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144132
@allure.title("Issue Description EN accepts exactly 1000 characters and rejects 1001 characters")
@FIELD_LENGTH_SKIP
def test_issue_description_en_1000_boundary(page):
    ...


# ===========================================================================
# 144133-144135 — Cover Image
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid JPG Cover Image is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144133
@MAGAZINE_CMS_XDIST_GROUP
def test_cover_image_valid_saved_displayed(page, disposable, anon_pages):
    # Azure TC 144133 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    data = _data(_title("144133"), cover_stem="cover_208")
    entry = _create(admin, disposable, data, publish=True)
    _assert_published(admin, entry)
    admin.open_entry(entry)
    stored = admin.stored_file_name(FIELD_COVER_IMAGE)
    assert stored == data["cover_uploaded_as"], f"stored cover {stored!r}, uploaded {data['cover_uploaded_as']!r}"

    _require_active_status(admin, entry)
    view, where = _visible_publicly(anon_pages, data["title"])
    img = view.latest_cover_img() if where["latest"] else view.card_cover_img(where["archive_index"])
    allure.attach(repr(img), name="card cover image")
    stem = os.path.splitext(data["cover_uploaded_as"])[0]
    assert img["present"] and img["loaded"], f"the card image does not render: {img}"
    assert stem in img["src"], f"the card renders {img['src']!r}, not the uploaded {data['cover_uploaded_as']!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A magazine issue cannot be published without a Cover Image")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144134
@MAGAZINE_CMS_XDIST_GROUP
def test_cover_image_empty_blocks_publish(page, disposable):
    # Azure TC 144134 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144134"), cover_path=None), "no Cover Image",
                    expect_in_evidence=r"issueCoverImage|Cover")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Cover Image rejects a non-image file format")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144135
@MAGAZINE_CMS_XDIST_GROUP
def test_cover_image_non_image_format_rejected(page, disposable):
    # Azure TC 144135 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144135")
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        admin.open_new_entry_form()
        admin.fill_issue(_data(title, cover_path=None))
        result = admin.attempt_upload(FIELD_COVER_IMAGE, f"{FIXTURES}/notes.txt")
        allure.attach(repr(result), name="notes.txt upload attempt")
        _pinned(admin, ROLE_EDITOR)
        admin.save_as_draft()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    attached = result["file"] in (result.get("field_value") or "")
    assert not attached, f"notes.txt was attached as the Cover Image: {result}"
    assert result["success"] is False or result["errors"] or result.get("field_errors"), (
        f"notes.txt was not attached, but no format validation error was shown: {result}"
    )
    if entry is not None:
        admin.open_entry(entry)
        assert not admin.stored_file_name(FIELD_COVER_IMAGE), "a cover file was stored after the rejected upload"


# ===========================================================================
# 144136-144138 — Issue Date
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Issue Date is saved and reflected in the issue's meta on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144136
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_date_valid_saved_reflected(page, disposable, anon_pages):
    # Azure TC 144136 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    data = _data(_title("144136"), issue_date="01/05/2026")
    _, view, where = _publish_and_find(admin, disposable, anon_pages, data)
    meta = view.latest_meta_text() if where["latest"] else view.card_meta(where["archive_index"])
    assert "May 2026" in meta, f"meta row reads {meta!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A magazine issue cannot be published without an Issue Date")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144137
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_date_empty_blocks_publish(page, disposable):
    # Azure TC 144137 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144137"), issue_date=None), "no Issue Date",
                    expect_in_evidence=r"issueDate|Issue Date|date")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Date rejects an invalid date format")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144138
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_date_invalid_format_rejected(page, disposable):
    # Azure TC 144138 | PBI 130710 | account: Site Content Editor.
    # "Click Save" is Save as Draft, and Save as Draft deliberately skips
    # required-field checks (standards.md "Content Editorial Workflow"), so a
    # Draft MAY be created here. The invalid date counts as REJECTED when the
    # inline invalid-date error is shown AND no date is stored; it fails only
    # when a non-empty (coerced) Issue Date is stored or no error is shown.
    admin = _editor(page)
    title = _title("144138")
    ids_before = admin.snapshot_ids()
    redirected, message, evidence, stored_on_form = False, "", {}, ""
    try:
        admin.open_new_entry_form()
        admin.fill_issue(_data(title, issue_date=None))
        admin.set_issue_date("32/13/2026")
        message = admin.date_field_message()
        stored_on_form = admin.stored_issue_date()
        allure.attach(f"typed 32/13/2026 -> box {admin.issue_date_value()!r}, stored "
                      f"{stored_on_form!r}, message {message!r}", name="Issue Date after typing")
        _pinned(admin, ROLE_EDITOR)
        admin.save_as_draft()
        redirected = admin.save_redirected()
        evidence = admin.refusal_evidence()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    date_error = bool(re.search(r"dd/mm/yyyy|invalid", message, re.I)) or bool(
        re.search(r"issueDate|Issue Date", repr(evidence), re.I))
    if entry is not None:
        admin.open_entry(entry)
        stored, shown = admin.stored_issue_date(), admin.issue_date_value()
        allure.attach(f"Draft {entry.code} created (Save as Draft skips required checks); stored Issue Date "
                      f"{stored!r}, form shows {shown!r}", name="stored Issue Date on the Draft")
        if stored or shown:
            pytest.fail(f"PRODUCT: Issue Date 32/13/2026 was not rejected — the Draft stores Issue Date "
                        f"{stored!r} (form shows {shown!r}; inline message was {message!r})")
        assert date_error, (f"32/13/2026 left no Issue Date stored, but no invalid-date error was shown "
                            f"(inline message {message!r}, evidence {evidence})")
        return
    assert not redirected and admin.submit_blocked(), f"Save with 32/13/2026 was not refused: {evidence}"
    assert date_error, f"no invalid-date error was shown: message {message!r}, evidence {evidence}"


# ===========================================================================
# 144139-144143 — Page Count
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Page Count is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144139
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_valid_saved_displayed(page, disposable, anon_pages):
    # Azure TC 144139 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _, view, where = _publish_and_find(admin, disposable, anon_pages, _data(_title("144139"), page_count="48"))
    meta = view.latest_meta_text() if where["latest"] else view.card_meta(where["archive_index"])
    assert "48 pages" in meta, f"meta row reads {meta!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144140
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_empty_rejected(page, disposable):
    # Azure TC 144140 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144140"), page_count=None), "an empty Page Count",
                    expect_in_evidence=r"pageCount|Page Count|page")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects a value of zero")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144141
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_zero_rejected(page, disposable):
    # Azure TC 144141 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_saved_value_rejected(admin, disposable, _data(_title("144141")), FIELD_PAGE_COUNT, "0",
                                 "Page Count = 0", tc_id="144141")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects a negative value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144142
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_negative_rejected(page, disposable):
    # Azure TC 144142 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_saved_value_rejected(admin, disposable, _data(_title("144142")), FIELD_PAGE_COUNT, "-5",
                                 "Page Count = -5", tc_id="144142")


def _non_numeric_case(admin, disposable, tc_id: str, field: str, text: str) -> None:
    """Non-numeric count: the case accepts keystroke-level rejection; the value
    must never be held or persisted, and a typed value must block the save."""
    title = _title(tc_id)
    ids_before = admin.snapshot_ids()
    data = _data(title, **({"page_count": None} if field == FIELD_PAGE_COUNT else {"article_count": None}))
    held, redirected = "", False
    try:
        admin.open_new_entry_form()
        admin.fill_issue(data)
        admin.type_into_number(field, text)
        held = admin.number_field_value(field)
        allure.attach(f"typed {text!r} -> field holds {held!r}", name=f"{field} after typing")
        _pinned(admin, ROLE_EDITOR)
        admin.save_as_draft()
        redirected = admin.save_redirected()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    if held == text:
        assert not redirected and admin.submit_blocked(), (
            f"{field} accepted {text!r} and the save was not blocked with a number-format error"
        )
    if entry is not None:
        admin.open_entry(entry)
        stored = admin.number_field_value(field)
        assert text not in stored, f"{field} persisted {stored!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects a non-numeric value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144143
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_non_numeric_rejected(page, disposable):
    # Azure TC 144143 | PBI 130710 | account: Site Content Editor
    _non_numeric_case(_editor(page), disposable, "144143", FIELD_PAGE_COUNT, "abc")


# ===========================================================================
# 144144-144148 — Article Count
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Article Count is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144144
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_valid_saved_displayed(page, disposable, anon_pages):
    # Azure TC 144144 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _, view, where = _publish_and_find(admin, disposable, anon_pages, _data(_title("144144"), article_count="12"))
    meta = view.latest_meta_text() if where["latest"] else view.card_meta(where["archive_index"])
    assert "12 Articles" in meta, f"meta row reads {meta!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Article Count rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144145
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_empty_rejected(page, disposable):
    # Azure TC 144145 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144145"), article_count=None), "an empty Article Count",
                    expect_in_evidence=r"articleCount|Article Count|article")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Article Count rejects a value of zero")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144146
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_zero_rejected(page, disposable):
    # Azure TC 144146 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_saved_value_rejected(admin, disposable, _data(_title("144146")), FIELD_ARTICLE_COUNT, "0",
                                 "Article Count = 0", tc_id="144146")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Article Count rejects a negative value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144147
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_negative_rejected(page, disposable):
    # Azure TC 144147 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_saved_value_rejected(admin, disposable, _data(_title("144147")), FIELD_ARTICLE_COUNT, "-3",
                                 "Article Count = -3", tc_id="144147")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Article Count rejects a non-numeric value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144148
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_non_numeric_rejected(page, disposable):
    # Azure TC 144148 | PBI 130710 | account: Site Content Editor
    _non_numeric_case(_editor(page), disposable, "144148", FIELD_ARTICLE_COUNT, "xyz")


# ===========================================================================
# 144149-144153 — PDF Attachment / Open in New Tab
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A valid PDF attachment is saved and usable via Read Online and Download PDF")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144149
@MAGAZINE_CMS_XDIST_GROUP
def test_pdf_attachment_valid_usable(page, disposable, anon_pages):
    # Azure TC 144149 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    data = _data(_title("144149"), pdf_stem="issue211", open_in_new_tab=True)
    ids_before = admin.snapshot_ids()
    try:
        admin.open_new_entry_form()
        admin.fill_issue(data)
        shown = admin.uploaded_filename(FIELD_PDF_ATTACHMENT)
        _pinned(admin, ROLE_EDITOR)
        admin.publish()
        went_through = admin.save_redirected()
    finally:
        entry = _register(admin, disposable, data["title"], ids_before)
    assert data["pdf_uploaded_as"] in shown, f"the field shows {shown!r}, not {data['pdf_uploaded_as']!r}"
    assert went_through and entry, f"publishing did not go through: {admin.refusal_evidence()}"
    _assert_published(admin, entry)

    _require_active_status(admin, entry)
    view, where = _visible_publicly(anon_pages, data["title"])
    stem = os.path.splitext(data["pdf_uploaded_as"])[0]
    read = view.latest_read_online_link() if where["latest"] else view.card_read_online_link(where["archive_index"])
    opened = view.read_online_opens(read)
    allure.attach(repr(opened), name="Read Online")
    assert opened["new_tab"] and stem in opened["url"], f"Read Online did not open the PDF in a new tab: {opened}"
    view.open_magazine_anonymous()
    where = view.find_title(data["title"])
    download = (view.latest_download_link() if where["latest"]
                else view.card_download_link(where["archive_index"]))
    name = view.download_via(download)
    assert stem in name and name.endswith(".pdf"), f"Download PDF saved {name!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A magazine issue cannot be published without a PDF attachment")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144150
@MAGAZINE_CMS_XDIST_GROUP
def test_pdf_attachment_empty_blocks_publish(page, disposable):
    # Azure TC 144150 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144150"), pdf_path=None), "no PDF Attachment",
                    expect_in_evidence=r"pdfAttachment|PDF")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing is blocked when the PDF Attachment is an invalid (non-PDF) file")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144151
@MAGAZINE_CMS_XDIST_GROUP
def test_pdf_attachment_invalid_format_blocks_publish(page, disposable):
    # Azure TC 144151 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144151")
    ids_before = admin.snapshot_ids()
    result, redirected, evidence = {}, False, {}
    try:
        admin.open_new_entry_form()
        admin.fill_issue(_data(title, pdf_path=None))
        result = admin.attempt_upload(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/issue211.docx")
        allure.attach(repr(result), name="issue211.docx upload attempt")
        _pinned(admin, ROLE_EDITOR)
        admin.publish()
        redirected = admin.save_redirected()
        evidence = admin.refusal_evidence()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    flagged = (result["file"] not in (result.get("field_value") or "")) or bool(result["errors"])
    assert flagged, f"issue211.docx was accepted into the PDF field without any format flag: {result}"
    if entry is not None:
        admin.open_entries_list()
        pytest.fail(f"PRODUCT: Publish was NOT blocked with a .docx PDF Attachment — status "
                    f"{admin.row_status(entry)!r}")
    assert not redirected and admin.submit_blocked(), f"Publish was not refused: {evidence}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Open in New Tab")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Open in New Tab defaults to True and Read Online opens the PDF in a new browser tab")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144152
@MAGAZINE_CMS_XDIST_GROUP
def test_open_in_new_tab_defaults_true(page, disposable, anon_pages):
    # Azure TC 144152 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144152")
    admin.open_new_entry_form()
    default = admin.is_open_in_new_tab_checked()
    assert default is True, f"Open in New Tab defaults to {default} on a new issue, not True"

    data = _data(title)  # Open in New Tab left untouched
    entry = _create(admin, disposable, data, publish=True)
    _assert_published(admin, entry)
    _require_active_status(admin, entry)
    view, where = _visible_publicly(anon_pages, title)
    read = view.latest_read_online_link() if where["latest"] else view.card_read_online_link(where["archive_index"])
    opened = view.read_online_opens(read)
    assert opened["new_tab"] and opened["original_kept"], f"Read Online did not open a new tab: {opened}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Open in New Tab")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Setting Open in New Tab to False persists and is honored by Read Online")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144153
@MAGAZINE_CMS_XDIST_GROUP
def test_open_in_new_tab_false_persists(page, disposable, anon_pages):
    # Azure TC 144153 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144153")
    entry = _create(admin, disposable, _data(title, open_in_new_tab=True), publish=False)

    # Step 2 — set False and Save.
    admin.open_entry(entry)
    admin.set_open_in_new_tab(False)
    _pinned(admin, ROLE_EDITOR)
    admin.save_as_draft()
    assert admin.save_redirected(), f"the save was refused: {admin.refusal_evidence()}"
    banners = admin.success_banners(expected=MSG_DRAFT_SAVED)
    admin.open_entry(entry)
    assert admin.is_open_in_new_tab_checked() is False, "Open in New Tab = False did not persist"
    assert admin.has_message(banners, MSG_DRAFT_SAVED), f"no {MSG_DRAFT_SAVED!r} message after the save: {banners}"

    # Step 3 — publish; Read Online opens in the same tab.
    admin.open_entry(entry)
    admin.publish()
    assert admin.save_redirected(), f"Publish was refused: {admin.refusal_evidence()}"
    _assert_published(admin, entry)
    _require_active_status(admin, entry)
    view, where = _visible_publicly(anon_pages, title)
    read = view.latest_read_online_link() if where["latest"] else view.card_read_online_link(where["archive_index"])
    opened = view.read_online_opens(read)
    allure.attach(repr(opened), name="Read Online")
    assert not opened["new_tab"], f"Read Online opened a NEW tab although Open in New Tab = False: {opened}"


# ===========================================================================
# 144199/144200 — Replace files on a Published issue (Edge)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing the Cover Image on a published issue updates the public page without breaking display")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130710
@pytest.mark.tc_144199
@MAGAZINE_CMS_XDIST_GROUP
def test_replace_cover_image_propagates(page, disposable, anon_pages):
    # Azure TC 144199 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144199")
    entry = _create(admin, disposable, _data(title, cover_stem="cover_208"), publish=True)
    _assert_published(admin, entry)

    # Step 2 — replace the cover and save (a Published record's save is Publish).
    admin.open_entry(entry)
    admin.upload_file(FIELD_COVER_IMAGE, admin.DEFAULT_COVER, "cover_208_v2")
    new_cover = admin.last_uploaded_name
    _pinned(admin, ROLE_EDITOR)
    admin.publish()
    assert admin.save_redirected(), f"the replacement save was refused: {admin.refusal_evidence()}"
    banners = admin.success_banners(expected=MSG_SAVED_AND_PUBLISHED)
    _assert_published(admin, entry)
    admin.open_entry(entry)
    assert admin.stored_file_name(FIELD_COVER_IMAGE) == new_cover, "the replacement cover was not stored"
    assert admin.has_message(banners, MSG_SAVED_AND_PUBLISHED), (
        f"no {MSG_SAVED_AND_PUBLISHED!r} message after saving the replacement cover: {banners}"
    )

    # Step 3 — the public card shows the new image.
    _require_active_status(admin, entry)
    stem = os.path.splitext(new_cover)[0]
    state = {}

    def _new_image(view) -> bool:
        where = view.find_title(title)
        if not where["latest"] and where["archive_index"] < 0:
            return False
        state.update(view.latest_cover_img() if where["latest"] else view.card_cover_img(where["archive_index"]))
        return stem in state.get("src", "")

    _public_until(anon_pages, _new_image, f"DELIVERY: the card never showed the replacement cover {new_cover!r}")
    assert state["loaded"], f"the replacement cover does not render (broken image): {state}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing the PDF attachment on a published issue propagates the new file")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130710
@pytest.mark.tc_144200
@MAGAZINE_CMS_XDIST_GROUP
def test_replace_pdf_attachment_propagates(page, disposable, anon_pages):
    # Azure TC 144200 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title = _title("144200")
    entry = _create(admin, disposable, _data(title, pdf_stem="issue211", open_in_new_tab=True), publish=True)
    _assert_published(admin, entry)

    admin.open_entry(entry)
    admin.upload_file(FIELD_PDF_ATTACHMENT, admin.DEFAULT_PDF, "issue211_v2")
    new_pdf = admin.last_uploaded_name
    _pinned(admin, ROLE_EDITOR)
    admin.publish()
    assert admin.save_redirected(), f"the replacement save was refused: {admin.refusal_evidence()}"
    banners = admin.success_banners(expected=MSG_SAVED_AND_PUBLISHED)
    _assert_published(admin, entry)
    admin.open_entry(entry)
    assert admin.stored_file_name(FIELD_PDF_ATTACHMENT) == new_pdf, "the replacement PDF was not stored"
    assert admin.has_message(banners, MSG_SAVED_AND_PUBLISHED), (
        f"no {MSG_SAVED_AND_PUBLISHED!r} message after saving the replacement PDF: {banners}"
    )

    _require_active_status(admin, entry)
    stem = os.path.splitext(new_pdf)[0]
    hrefs = {}

    def _new_file(view) -> bool:
        where = view.find_title(title)
        if not where["latest"] and where["archive_index"] < 0:
            return False
        link = view.latest_read_online_link() if where["latest"] else view.card_read_online_link(where["archive_index"])
        hrefs["read"] = view.link_info(link)["href"]
        return stem in hrefs["read"]

    view = _public_until(anon_pages, _new_file, f"DELIVERY: Read Online never pointed at {new_pdf!r}")
    where = view.find_title(title)
    download = view.latest_download_link() if where["latest"] else view.card_download_link(where["archive_index"])
    name = view.download_via(download)
    assert stem in name, f"Download PDF saved {name!r}, not the replacement {new_pdf!r}"


# ===========================================================================
# 144209-144216 — Arabic fields
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Issue Title AR is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144209
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_ar_valid_saved_displayed(page, disposable, anon_pages):
    # Azure TC 144209 | PBI 130710 | account: Site Content Editor.
    # The case's "المجلة الاقتصادية" is kept as the visible suffix of a unique AR title.
    admin = _editor(page)
    title_ar = f"{_title('144209')} المجلة الاقتصادية"
    data = _data(_title("144209"), title_ar=title_ar)
    _, view, where = _publish_and_find(admin, disposable, anon_pages, data, locale="ar", public_title=title_ar)
    shown = view.latest_title_text().strip() if where["latest"] else view.card_title(where["archive_index"]).strip()
    assert shown == title_ar, f"the Arabic card title reads {shown!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title AR validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Issue Title AR rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144210
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_ar_empty_rejected(page, disposable):
    # Azure TC 144210 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144210"), title_ar=""), "an empty Issue Title AR",
                    expect_in_evidence=r"issueTitleAR|Title \(AR\)|required")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Title AR rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144211
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_ar_whitespace_rejected(page, disposable):
    # Azure TC 144211 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144211"), title_ar="   "), "a whitespace-only Issue Title AR")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144212
@allure.title("Issue Title AR accepts exactly 200 characters and rejects 201 characters")
@FIELD_LENGTH_SKIP
def test_issue_title_ar_200_boundary(page):
    ...


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Issue Description AR is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144213
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_ar_valid_saved_displayed(page, disposable, anon_pages):
    # Azure TC 144213 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    title_ar = f"{_title('144213')} عدد"
    desc_ar = "يغطي هذا العدد التوقعات الاقتصادية لدولة قطر وإحصاءات التجارة وأبرز الأعضاء."
    data = _data(_title("144213"), title_ar=title_ar, description_ar=desc_ar)
    _, view, where = _publish_and_find(admin, disposable, anon_pages, data, locale="ar", public_title=title_ar)
    shown = view.latest_desc_text().strip() if where["latest"] else view.card_desc(where["archive_index"]).strip()
    assert shown == desc_ar, f"the Arabic card description reads {shown!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description AR validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Issue Description AR rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144214
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_ar_empty_rejected(page, disposable):
    # Azure TC 144214 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144214"), description_ar=""), "an empty Issue Description AR",
                    expect_in_evidence=r"issueDescriptionAR|Description")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Description AR rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144215
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_ar_whitespace_rejected(page, disposable):
    # Azure TC 144215 | PBI 130710 | account: Site Content Editor
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data(_title("144215"), description_ar="   "),
                    "a whitespace-only Issue Description AR")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144216
@allure.title("Issue Description AR accepts exactly 1000 characters and rejects 1001 characters")
@FIELD_LENGTH_SKIP
def test_issue_description_ar_1000_boundary(page):
    ...

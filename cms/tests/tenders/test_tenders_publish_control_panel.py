"""
cms/tests/tenders/test_tenders_publish_control_panel.py —
Control_Panel manual-create / publish / unpublish / Active Status / audit /
persistence / Reference-Number collision cases for PBI 130952 ("QC - Business
Gateway - 012 - Tenders listing screen"), Azure suite 140383 in plan 137724,
on the `manage-tender` Object Authoring surface (`/web/qatar-chamber/manage-tender`).

Cases: 146133, 146134, 146135, 146136, 146283, 146293.

Pattern (PBI 130710 / 130712, commits 3d35745 / d422936):
  - Every case runs as a pinned named role in an auth-free context
    (`AUTH_FREE_PAGE`): Site Content Editor (156488) publishes directly
    ("Publish" -> "Saved and published."); Site Content Author (156492)
    submits for review ("Submit for Review" -> Pending Review). The signed-in
    userId is re-checked before every save. TEST_USER is used only by the
    `disposable` teardown, to delete the test's OWN record.
  - Seven-state workflow; Unpublish is the row action `data-qc-oel-unpublish`
    and lands on UNPUBLISHED (not Draft).
  - Public visibility = workflow PUBLISHED + Active Status ticked (standards.md)
    and, observed live on this object, Status (pageStatus) = Published and a
    Closing Date not past. Every public check first re-opens the record to
    verify the STORED Active Status, then reads the listing in a fresh
    logged-out context with Load More expanded.
  - Disposable `QCTEST-130952-C-<tc>-<stamp>` tenders (title AND reference);
    identity (title + ref + entry id + code) captured right after creation;
    teardown deletes only that captured record through the guarded delete.
    The 15 real tenders (codes QC-TENDER-130952-NN…) are never acted on.

Substitutions disclosed (case wording -> what runs):
  - 146133 "Administrator" -> Site Content Editor (the privileged publishing
    role). The super-admin TEST_USER bypasses the workflow, so standards.md
    forbids asserting a lifecycle outcome through it.
  - 146134 "audit log" -> the row's in-table History trail (actor, timestamp,
    action, comment) — the only audit surface these roles can reach on
    manage-tender. Approve / Reject act on Author-submitted (Pending Review)
    tenders; Publish / Unpublish are the Editor's row actions.
  - 146293 "Path 1 produces QC-ET-2026-041" -> no public submission creates a
    manage-tender record (the webform stores into EOISubmission), so the
    first record is an Editor-created tender with Status = Approved carrying
    `QCTEST-130952-C-146293-<stamp>-QC-ET-2026-041`.

NOT SCRIPTED: 146285, 146292 — Tender Category is a Liferay Picklist
administered at Control Panel > Picklists ("Tender Category", CUSTOM), not on
manage-tender; adding/deactivating a value changes shared real master data.
Reported to the QA Manager as Out-of-scope pending the user's decision.
"""

from __future__ import annotations

import re
from datetime import datetime
from time import monotonic

import allure
import pytest

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_REJECTED,
    STATUS_UNPUBLISHED,
)
from cms.pages.tenders.tender_admin_page import (
    A_MSG_ARABIC_SAVED,
    A_MSG_DRAFT_SAVED,
    A_MSG_SAVED_AND_PUBLISHED,
    A_MSG_SUBMITTED_FOR_REVIEW,
    A_ROLE_AUTHOR,
    A_ROLE_EDITOR,
    A_ROLE_USER_IDS,
    A_STATUS_INACTIVE,
    C_QCTEST_PREFIX,
    K_REF,
    K_TITLE,
    TenderEntryC,
    TenderPublicViewC,
    TenderPublishAdminPage,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import settings
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
TENDERS_CMS_C_GROUP = pytest.mark.xdist_group("tenders_cms_c")
STAMP = datetime.now().strftime("%m%d%H%M%S")

# A publish was measured at 27-30 s to reach Published on a sibling object.
PUBLISH_CONFIRM_TIMEOUT = 120.0
# cms-profile.md measured ~0 s on a JAX-RS source only; this listing was never
# measured, so the poll is bounded at 30 s and the observed latency attached.
PUBLIC_REFLECT_TIMEOUT = 30.0
PUBLIC_POLL = 1.0

EPIC = "Business Gateway"
FEATURE = "Tenders — Control Panel (publish lifecycle)"


def _ref(tc_id: str, suffix: str = "") -> str:
    return TenderPublishAdminPage.c_name(tc_id, STAMP) + (f"-{suffix}" if suffix else "")


def _title(tc_id: str, suffix: str) -> str:
    return TenderPublishAdminPage.c_name(tc_id, STAMP, suffix)


def _data(tc_id: str, suffix: str, ref_suffix: str = "", **overrides) -> dict:
    return TenderPublishAdminPage.c_tender_data(_ref(tc_id, ref_suffix), _title(tc_id, suffix), **overrides)


# ===========================================================================
# Fixtures
# ===========================================================================
class DisposableRegistry:
    """Records this test created (captured identity). Only these are deleted."""

    def __init__(self):
        self._entries: dict[str, TenderEntryC] = {}

    @property
    def entries(self) -> list[TenderEntryC]:
        return list(self._entries.values())

    def track(self, entry: TenderEntryC) -> TenderEntryC:
        if not isinstance(entry, TenderEntryC) or not entry.in_namespace():
            raise ValueError(f"{entry} is not a {C_QCTEST_PREFIX} record")
        self._entries[entry.entry_id] = entry
        return entry


@pytest.fixture
def disposable(browser):
    """Deletes ONLY the records the test registered at creation, through the
    guarded single-record delete, from a TEST_USER context (cleanup of the
    test's own record only). Anything it cannot remove fails the teardown."""
    registry = DisposableRegistry()
    yield registry
    if not registry.entries:
        return
    # TEST_USER, signed in fresh (the shared storageState file can be stale) —
    # used for cleanup of the test's own records only.
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        cleaner_page = ctx.new_page()
        CmsLoginPage(cleaner_page).open_login().login(settings.test_user, settings.test_password)
        cleaner = TenderPublishAdminPage(cleaner_page)
        for entry in registry.entries:
            label = f"{entry.title} (ref {entry.reference}, id {entry.entry_id}, code {entry.code})"
            try:
                cleaner.open_list_all()
                if not cleaner.row_present(entry):
                    if cleaner.is_list_fully_expanded():
                        outcome.append(f"already gone: {label}")
                    else:
                        failures.append(f"{label}: not found and the list is NOT fully expanded")
                    continue
                cleaner.adopt_a(entry)
                if cleaner.delete_own_entry(entry):
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


def _context_factory(browser):
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    return contexts, _make


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read (standards.md)."""
    contexts, make = _context_factory(browser)
    yield make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture
def role_pages(browser):
    """Extra auth-free pages for a second account in the same test."""
    contexts, make = _context_factory(browser)
    yield make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def _login(page, role: str) -> TenderPublishAdminPage:
    """Signs in as `role` in this auth-free context; skips (never falls back)
    when the account cannot sign in or is not the pinned one."""
    admin = TenderPublishAdminPage(page)
    outcome = admin.login_as_role(role)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}'")
    if outcome != "ok":
        pytest.fail(f"login as '{role}' neither succeeded nor showed Liferay's refusal banner")
    admin.open_list_all()
    user_id, _ = admin.signed_in_user()
    if user_id != A_ROLE_USER_IDS[role]:
        pytest.skip(f"PRECONDITION: '{role}' credentials sign in as userId {user_id!r}, "
                    f"not the pinned {A_ROLE_USER_IDS[role]}")
    return admin


def _pinned(admin: TenderPublishAdminPage, role: str) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == A_ROLE_USER_IDS[role], (
        f"the session is now userId {user_id!r}, not the pinned {role} ({A_ROLE_USER_IDS[role]})")


def _register(admin, disposable, data: dict, ids_before: set) -> TenderEntryC | None:
    """Registers for teardown the ONE new record reading `data`'s ref + title.
    Never raises (registration must not mask the test result)."""
    try:
        entry = admin.identify_created_c(data[K_REF], data[K_TITLE], ids_before)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001
        allure.attach(repr(exc), name=f"registration of {data[K_TITLE]!r} failed")
        return None


def _wait_arabic_saved(admin) -> str:
    """Object Authoring guide §5: wait (bounded) for the Arabic-save message."""
    seen = {"text": ""}

    def _done() -> bool:
        seen["text"] = admin.rendered_body_text()
        return A_MSG_ARABIC_SAVED in seen["text"] or "Arabic content was not" in seen["text"]

    try:
        wait_until(_done, timeout=25.0, poll=0.5)
    except WaitTimeoutError:
        return ""
    return A_MSG_ARABIC_SAVED if A_MSG_ARABIC_SAVED in seen["text"] else "the Arabic content was NOT saved"


def _create(admin, disposable, data: dict, publish: bool, role: str = A_ROLE_EDITOR) -> TenderEntryC:
    """Creates one tender (publish=True -> the role's submit button, else Save
    as Draft), registers whatever got created for teardown, THEN asserts.
    `admin.create_banners` holds the edit-bar messages shown after the save."""
    ids_before = admin.snapshot_ids()
    went_through, diagnostics, banners, arabic = False, {}, [], ""
    expected = (A_MSG_DRAFT_SAVED if not publish
                else A_MSG_SUBMITTED_FOR_REVIEW if role == A_ROLE_AUTHOR else A_MSG_SAVED_AND_PUBLISHED)
    try:
        admin.open_create_form_en()
        admin.fill_tender_a(data)
        _pinned(admin, role)
        admin.click_publish() if publish else admin.click_save_as_draft()
        went_through = admin.save_went_through()
        diagnostics = admin.refusal_evidence()
        if went_through:
            banners = admin.success_messages(expected, timeout=15.0)
            arabic = _wait_arabic_saved(admin)
        admin.evidence(f"{data[K_TITLE]} after {'submit' if publish else 'draft'}")
    finally:
        entry = _register(admin, disposable, data, ids_before)
    admin.create_banners = banners
    allure.attach("\n".join(banners) or "(none)", name=f"edit-bar after creating {data[K_TITLE]}")
    allure.attach(arabic or "(no Arabic-save message within 25 s)", name="Arabic content save")
    assert went_through, f"creating {data[K_TITLE]!r} as {role} did not go through: {diagnostics}"
    assert entry is not None, f"{data[K_TITLE]!r} went through but is not identifiable as exactly one NEW record"
    return entry


def _has(banners: list[str], expected: str) -> bool:
    return any(expected in b for b in banners)


def _history(admin, entry: TenderEntryC) -> list[dict]:
    trail = admin.history(entry)
    allure.attach("\n".join(repr(h) for h in trail) or admin.history_cell_text(entry) or "(empty)",
                  name=f"History of {entry.title}")
    return trail


def _require_active_status(admin, entry: TenderEntryC) -> None:
    """User rule + standards.md: Active Status must be STORED as ticked before
    ANY public check (re-opens the record)."""
    admin.open_entry_en(entry.code)
    stored = admin.active_status_stored()
    page_status = admin.picklist_value("pageStatus")
    allure.attach(f"stored Active Status: {stored!r}\nstored Status: {page_status!r}",
                  name="public-visibility preconditions")
    if stored != "true":
        admin.evidence(f"{entry.title} stored Active Status {stored}")
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title!r} stores Active Status {stored!r}, not 'true'; "
                    f"the public-page step was not run")


def _public_until(anon_pages, predicate, message: str, locale: str = "en") -> tuple[TenderPublicViewC, float]:
    """Publish-then-poll on the delivery surface in ONE logged-out context."""
    view = TenderPublicViewC(anon_pages())
    started = monotonic()

    def _check() -> bool:
        view.open_listing_all(locale)
        return bool(predicate(view))

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL, message=message)
    except WaitTimeoutError:
        view.evidence(f"public listing at timeout {message[:60]}")
        pytest.fail(f"{message} within {PUBLIC_REFLECT_TIMEOUT:.0f}s "
                    f"(cards: {[c['title'] for c in view.cards()]})")
    latency = monotonic() - started
    allure.attach(f"{latency:.1f}s", name="observed public-listing latency")
    return view, latency


def _visible_publicly(anon_pages, entry: TenderEntryC) -> dict:
    view, _ = _public_until(anon_pages, lambda v: bool(v.card_for(entry.code)),
                            f"DELIVERY: {entry.title!r} never appeared on the logged-out tenders listing")
    return view.card_for(entry.code)


def _assert_not_public(anon_pages, entry: TenderEntryC, within_budget: bool = True) -> None:
    """Absence that cannot pass vacuously: the listing must render real cards
    (positive control) before `entry` is required absent."""
    if within_budget:
        _public_until(anon_pages, lambda v: not v.card_for(entry.code) and len(v.cards()) > 0,
                      f"{entry.title!r} was still on the logged-out tenders listing")
    view = TenderPublicViewC(anon_pages()).open_listing_all()
    cards = view.cards()
    view.evidence(f"public listing checked for {entry.title}")
    assert cards, f"cannot prove {entry.title!r} is absent: the logged-out listing shows no tender cards"
    assert not view.card_for(entry.code), f"{entry.title!r} is on the logged-out tenders listing"
    assert entry.title not in [c["title"] for c in cards], f"a card titled {entry.title!r} is on the listing"


# ===========================================================================
# 146133 — Path 2: manual create, draft, preview, publish, public listing
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Manual create and publish (Path 2)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An Administrator can manually create and publish a tender without a public submission (Path 2)")
@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_130952
@pytest.mark.tc_146133
@TENDERS_CMS_C_GROUP
def test_manual_create_draft_preview_publish(page, anon_pages, disposable):
    # Azure TC 146133 | PBI 130952 | account: Site Content Editor (156488).
    admin = _login(page, A_ROLE_EDITOR)
    data = _data("146133", "Manual Path 2 tender")

    # Steps 1-2 — full field set (Tender Document + BOQ), Save as Draft -> Draft.
    entry = _create(admin, disposable, data, publish=False)
    assert _has(admin.create_banners, A_MSG_DRAFT_SAVED), f"no {A_MSG_DRAFT_SAVED!r}: {admin.create_banners}"
    status = admin.wait_status(entry, (STATUS_DRAFT,), timeout=30.0)
    assert status == STATUS_DRAFT, f"after Save as Draft the row reads {admin.row_status_raw(entry)!r}, not DRAFT"

    # Step 3 — Preview renders correctly. A preview defect is recorded and the
    # Publish step still runs, so one run reports both outcomes.
    defects = []
    preview_url = admin.row_preview_href(entry)
    assert preview_url, f"the draft row offers no Preview link: {admin.row_link_labels(entry)}"
    text = admin.open_preview_expanded(preview_url, data[K_TITLE])
    admin.evidence("146133 preview of the draft (listing, Load More expanded)")
    assert "PREVIEW" in text, f"the Preview page carries no PREVIEW banner: {text[:300]!r}"
    if data[K_TITLE] not in text:
        banner = text.splitlines()[0] if text else ""
        detail_text = admin.open_detail_preview(entry, data[K_TITLE])
        admin.evidence("146133 preview of the draft (detail page)")
        defects.append(
            f"PRODUCT: the row Preview of the Draft ({preview_url}) shows the banner {banner!r} but does not render "
            f"the record (title absent after expanding Load More); the detail page in preview mode "
            f"({admin.detail_preview_url(entry)}) shows "
            f"{'Tender not found' if 'Tender not found' in detail_text else detail_text[:200]!r}")

    # Step 4 — Publish -> appears on the public listing with the entered data.
    admin.open_entry_en(entry.code)
    _pinned(admin, A_ROLE_EDITOR)
    admin.click_publish()
    banners = admin.success_messages(A_MSG_SAVED_AND_PUBLISHED) if admin.save_went_through() else []
    admin.evidence("146133 after publish")
    assert admin.save_went_through(), f"Publish of the draft did not go through: {admin.refusal_evidence()}"
    assert _has(banners, A_MSG_SAVED_AND_PUBLISHED), f"Publish showed {banners}, not {A_MSG_SAVED_AND_PUBLISHED!r}"
    status = admin.wait_status(entry, (STATUS_PUBLISHED, A_STATUS_INACTIVE), timeout=PUBLISH_CONFIRM_TIMEOUT)
    assert status == STATUS_PUBLISHED, f"after Publish the row reads {admin.row_status_raw(entry)!r}"
    _require_active_status(admin, entry)

    card = _visible_publicly(anon_pages, entry)
    allure.attach(repr(card), name="public card")
    mismatches = {k: (card.get(k), v) for k, v in {
        "title": data[K_TITLE], "ref": data[K_REF], "org": data["organizationName"],
        "badge": data["tenderCategory"]}.items() if card.get(k) != v}
    assert not mismatches, f"the public card does not show the entered data (shown, entered): {mismatches}"

    detail = TenderPublicViewC(anon_pages()).open_detail(entry.code)
    body = detail.detail_text()
    detail.evidence("146133 public detail")
    expected_texts = [data[K_TITLE], data[K_REF], data["organizationName"], data["workDescription"],
                      data["tenderType"], data["tenderClassification"], data["productCategory"],
                      data["organizationAddress"], data["preBidMeetingAddress"], data["needHelpContactEmail"],
                      data["feePayableTo"], data["emdPayableTo"]]
    missing = [t for t in expected_texts if t not in body]
    assert not missing, f"the public detail page does not show these entered values: {missing}"
    state = {"files": []}

    def _files_shown() -> bool:
        state["files"] = detail.file_rows()
        return len(state["files"]) >= 2 and all(f["hrefs"] for f in state["files"])

    try:
        wait_until(_files_shown, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL)
    except WaitTimeoutError:
        detail.evidence("146133 public detail without file rows")
        defects.append(f"DELIVERY: the logged-out detail page shows Tender Document / BOQ rows {state['files']} "
                       f"(expected two rows with download links); 'Tender documents' section on the page: "
                       f"{'Tender documents' in detail.detail_text()}")
    assert not defects, "; ".join(defects)


# ===========================================================================
# 146134 — every lifecycle action is recorded (History = audit log)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Audit trail")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Every Approve/Reject/Publish/Unpublish/manual-create action is recorded in the audit log")
@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.functional_high
@pytest.mark.pbi_130952
@pytest.mark.tc_146134
@TENDERS_CMS_C_GROUP
def test_lifecycle_actions_recorded_in_history(page, role_pages, disposable):
    # Azure TC 146134 | PBI 130952 | accounts: Site Content Author (156492) creates
    # and submits; Site Content Editor (156488) approves / rejects / unpublishes /
    # publishes. Status = Submitted keeps both records off the public listing
    # (Active Status stays ticked: an unticked record's badge reads INACTIVE).
    author = _login(page, A_ROLE_AUTHOR)
    _, author_name = author.signed_in_user()
    first = _create(author, disposable, _data("146134", "Approve then unpublish", ref_suffix="1",
                                              pageStatus="Submitted"),
                    publish=True, role=A_ROLE_AUTHOR)
    assert _has(author.create_banners, A_MSG_SUBMITTED_FOR_REVIEW), author.create_banners
    second = _create(author, disposable, _data("146134", "Reject", ref_suffix="2", pageStatus="Submitted"),
                     publish=True, role=A_ROLE_AUTHOR)
    for entry in (first, second):
        status = author.wait_status(entry, (STATUS_PENDING_REVIEW,), timeout=60.0)
        assert status == STATUS_PENDING_REVIEW, (
            f"the Author's Submit for Review left {entry.title!r} at {author.row_status_raw(entry)!r}")

    editor = _login(role_pages(), A_ROLE_EDITOR)
    _, editor_name = editor.signed_in_user()
    for entry in (first, second):
        editor.adopt_a(entry)
    editor.open_list_all()
    offered = editor.row_actions(first)
    allure.attach(repr(offered), name="Editor's actions on a Pending Review tender")
    assert {"approve", "reject"} <= set(offered), f"a Pending Review row offers the Editor {offered}"

    reason = "QCTEST rejection: Missing Establishment Card details"
    steps = [(first, "approve", "QCTEST approve", (STATUS_PUBLISHED,)),
             (second, "reject", reason, (STATUS_REJECTED,)),
             (first, "unpublish", "QCTEST unpublish", (STATUS_UNPUBLISHED,)),
             (first, "publish", "QCTEST publish again", (STATUS_PUBLISHED,))]
    for entry, action, comment, expected in steps:
        editor.open_list_all()
        _pinned(editor, A_ROLE_EDITOR)
        dialogs = editor.run_row_action(entry, action, comment)
        allure.attach("\n".join(dialogs) or "(no dialog)", name=f"dialogs of {action} on {entry.title}")
        status = editor.wait_status(entry, expected + (A_STATUS_INACTIVE,), timeout=PUBLISH_CONFIRM_TIMEOUT)
        if status not in expected:
            editor.evidence(f"146134 {action} left {status}")
        assert status in expected, (
            f"{action} on {entry.title!r} left the row at {editor.row_status_raw(entry)!r}, expected {expected}")
    editor.evidence("146134 list after the transitions")

    def _recorded(trail, actor, pattern):
        return [h for h in trail if actor and h["who"] == actor
                and re.search(pattern, h["action"] or h["text"], re.I) and h["when"]]

    trail_first = _history(editor, first)
    editor.evidence("146134 history approve-unpublish-publish")
    trail_second = _history(editor, second)
    editor.evidence("146134 history reject")
    missing = []
    for label, trail, actor, pattern in (
            ("manual create / submit by the Author", trail_first, author_name, r"submit|creat"),
            ("approve by the Editor", trail_first, editor_name, r"approv"),
            ("unpublish by the Editor", trail_first, editor_name, r"unpublish"),
            ("publish by the Editor", trail_first, editor_name, r"(?<!un)publish"),
            ("reject by the Editor", trail_second, editor_name, r"reject")):
        if not _recorded(trail, actor, pattern):
            missing.append(label)
    assert not missing, (
        f"History does not record (actor + timestamp + action) for: {missing}. Author {author_name!r}, "
        f"Editor {editor_name!r}. First tender: {trail_first}; second tender: {trail_second}")
    rejected = _recorded(trail_second, editor_name, r"reject")
    assert any(reason in (h["comment"] + h["text"]) for h in rejected), (
        f"the rejection reason {reason!r} is not stored in History: {rejected}")


# ===========================================================================
# 146135 — Unpublish removes the tender from the public listing
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish / unpublish")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Unpublishing a Published tender removes it from the public listing")
@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130952
@pytest.mark.tc_146135
@TENDERS_CMS_C_GROUP
def test_unpublish_removes_tender_from_listing(page, anon_pages, disposable):
    # Azure TC 146135 | PBI 130952 | account: Site Content Editor (156488).
    admin = _login(page, A_ROLE_EDITOR)
    entry = _create(admin, disposable, _data("146135", "Unpublish"), publish=True)
    assert _has(admin.create_banners, A_MSG_SAVED_AND_PUBLISHED), admin.create_banners
    status = admin.wait_status(entry, (STATUS_PUBLISHED, A_STATUS_INACTIVE), timeout=PUBLISH_CONFIRM_TIMEOUT)
    assert status == STATUS_PUBLISHED, f"after Publish the row reads {admin.row_status_raw(entry)!r}"
    _require_active_status(admin, entry)
    _visible_publicly(anon_pages, entry)  # precondition: a live tender

    admin.open_list_all()
    _pinned(admin, A_ROLE_EDITOR)
    dialogs = admin.run_row_action(entry, "unpublish", "QCTEST unpublish")
    allure.attach("\n".join(dialogs) or "(no dialog)", name="unpublish dialogs")
    status = admin.wait_status(entry, (STATUS_UNPUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    admin.evidence("146135 after unpublish")
    assert status == STATUS_UNPUBLISHED, f"after Unpublish the row reads {admin.row_status_raw(entry)!r}"
    _assert_not_public(anon_pages, entry)


# ===========================================================================
# 146136 — Active Status gates the public listing, independent of Published
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A tender's Active Status must be enabled for it to reach the public listing")
@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.functional_high
@pytest.mark.pbi_130952
@pytest.mark.tc_146136
@TENDERS_CMS_C_GROUP
def test_active_status_gates_public_listing(page, anon_pages, disposable):
    # Azure TC 146136 | PBI 130952 | account: Site Content Editor (156488).
    admin = _login(page, A_ROLE_EDITOR)

    # Step 1 — Publish with Active Status unchecked -> NOT on the public listing.
    entry = _create(admin, disposable, _data("146136", "Active Status gate", active_status=False), publish=True)
    status = admin.wait_status(entry, (STATUS_PUBLISHED, A_STATUS_INACTIVE), timeout=PUBLISH_CONFIRM_TIMEOUT)
    allure.attach(f"row status after Publish with Active Status unticked: {admin.row_status_raw(entry)!r}",
                  name="workflow badge")
    assert status in (STATUS_PUBLISHED, A_STATUS_INACTIVE), (
        f"Publish did not complete: the row reads {admin.row_status_raw(entry)!r}")
    admin.open_entry_en(entry.code)
    admin.evidence("146136 reopened record - stored Active Status")
    assert admin.active_status_stored() == "false", (
        f"Active Status was saved as {admin.active_status_stored()!r} although it was unticked")
    defects = []
    try:
        _assert_not_public(anon_pages, entry, within_budget=False)
    except AssertionError as exc:
        defects.append(f"PRODUCT (step 1): Published with Active Status stored 'false' but still public: {exc}")

    # Step 2 — enable Active Status -> it now appears.
    admin.open_entry_en(entry.code)
    admin.set_active_status(True)
    _pinned(admin, A_ROLE_EDITOR)
    admin.click_publish()
    banners = admin.success_messages(A_MSG_SAVED_AND_PUBLISHED) if admin.save_went_through() else []
    admin.evidence("146136 after ticking Active Status")
    assert admin.save_went_through(), f"saving Active Status = ticked did not go through: {admin.refusal_evidence()}"
    assert _has(banners, A_MSG_SAVED_AND_PUBLISHED), f"the save showed {banners}"
    status = admin.wait_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    assert status == STATUS_PUBLISHED, f"after ticking Active Status the row reads {admin.row_status_raw(entry)!r}"
    _require_active_status(admin, entry)
    _visible_publicly(anon_pages, entry)
    assert not defects, "; ".join(defects)


# ===========================================================================
# 146283 — persistence after Save -> reload
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Persistence")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A manually created tender's field values persist correctly after Save and reload")
@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.functional_low
@pytest.mark.pbi_130952
@pytest.mark.tc_146283
@TENDERS_CMS_C_GROUP
def test_manual_tender_values_persist_after_reload(page, disposable):
    # Azure TC 146283 | PBI 130952 | account: Site Content Editor (156488).
    # Non-default picklist values throughout so a silently defaulted field
    # cannot pass the comparison.
    admin = _login(page, A_ROLE_EDITOR)
    data = _data("146283", "Persistence", tenderCategory="Works", tenderType="Limited",
                 tenderClassification="Multi-stage", productCategory="Marine Works", tenderLocation="Oman",
                 tenderFeeExemptionAllowed="Yes", paymentMode="Offline", generalTechnicalEvaluationAllowed="No",
                 itemWiseTechnicalEvaluationAllowed="Yes", pageStatus="Approved", tenderFee="750",
                 emdAmount="15000", active_status=True)
    entry = _create(admin, disposable, data, publish=False)
    assert _has(admin.create_banners, A_MSG_DRAFT_SAVED), admin.create_banners

    admin.open_entry_en(entry.code)  # reload the record from a fresh navigation
    stored = admin.read_tender()
    admin.evidence("146283 reopened draft")
    allure.attach("\n".join(f"{k}: {v!r}" for k, v in stored.items()), name="stored values after reload")
    expected = {k: v for k, v in data.items() if k in stored}
    expected["active_status"] = "true"
    for key in ("tenderDocument", "billOfQuantities"):
        if f"{key}_uploaded_as" in data:
            expected[f"{key}_uploaded_as"] = data[f"{key}_uploaded_as"]
    diffs = {k: (v, stored[k]) for k, v in expected.items() if str(stored[k]).strip() != str(v).strip()}
    assert not diffs, f"values not retained exactly after Save as Draft -> reload (entered, stored): {diffs}"


# ===========================================================================
# 146293 — the same Reference Number cannot be reused
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Reference Number uniqueness")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A manually created tender (Path 2) cannot reuse the Reference Number of a Path-1 tender")
@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.edge
@pytest.mark.pbi_130952
@pytest.mark.tc_146293
@TENDERS_CMS_C_GROUP
def test_duplicate_reference_number_blocked(page, disposable):
    # Azure TC 146293 | PBI 130952 | account: Site Content Editor (156488).
    # Path-1 stand-in (module docstring): an Editor-created tender with Status =
    # Approved carrying the reused reference. Active Status unticked keeps both
    # records off the public listing.
    admin = _login(page, A_ROLE_EDITOR)
    reference = _ref("146293", "QC-ET-2026-041")
    first = _create(admin, disposable,
                    TenderPublishAdminPage.c_tender_data(reference, _title("146293", "Path 1 stand-in"),
                                                         pageStatus="Approved", active_status=False),
                    publish=True)
    assert first.reference == reference

    duplicate = TenderPublishAdminPage.c_tender_data(reference, _title("146293", "Path 2 duplicate"),
                                                     active_status=False)
    ids_before = admin.snapshot_ids()
    entry, evidence = None, {}
    try:
        admin.open_create_form_en()
        admin.fill_tender_a(duplicate)
        _pinned(admin, A_ROLE_EDITOR)
        admin.click_publish()
        evidence = {"went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
                    "messages": admin.all_messages_text(), **admin.refusal_evidence()}
        admin.evidence("146293 duplicate reference attempt")
    finally:
        entry = _register(admin, disposable, duplicate, ids_before)
    allure.attach(repr(evidence), name="duplicate-reference attempt")
    if entry is not None:
        admin.open_list_all()
        pytest.fail(f"PRODUCT: a second tender reusing Reference Number {reference!r} was created "
                    f"(row status {admin.row_status_raw(entry)!r}, entry id {entry.entry_id}); expected the "
                    f"uniqueness validation to block it. Messages shown: {evidence.get('messages')!r}")
    assert evidence.get("refused") and not evidence.get("went_through"), (
        f"the duplicate was neither created nor refused with validation evidence: {evidence}")

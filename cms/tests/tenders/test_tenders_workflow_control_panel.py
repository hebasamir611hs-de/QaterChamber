"""
cms/tests/tenders/test_tenders_workflow_control_panel.py —
Control_Panel workflow / auth / publish / persistence / collision cases for
PBI 130952 ("QC - Business Gateway - 012 - Tenders listing screen"), Azure
suite 140383 in plan 137724, on the `manage-tender` Object Authoring surface
(`/web/qatar-chamber/manage-tender`, slug "tender").

Replaces the outdated test_tenders_auth_control_panel.py,
test_tenders_functional_high_control_panel.py and
test_tenders_edge_control_panel.py (commit 07cc3b8, written before the
editorial-workflow rework). Field-validation cases live in Agent B's
test_tenders_fields_control_panel.py.

Pattern (PBI 130710 / 130712, commits 3d35745 / d422936):
  - Every case runs as the account it names — Site Content Editor (156488)
    or Site Content Author (156492) — in an auth-free context
    (`AUTH_FREE_PAGE`); the signed-in userId is re-checked before each save.
    TEST_USER is used only by the `disposable` teardown, to delete the test's
    OWN record. Cases that name no role run as the Editor.
  - Seven-state workflow: the Editor's button reads "Publish" and publishes
    directly; the Author's reads "Submit for Review" (-> Pending Review).
    Unpublish is the row action `data-qc-oel-unpublish` and lands on
    UNPUBLISHED. "Audit log" maps onto the row's History trail (no separate
    audit-log screen exists on this surface for these roles).
  - Success messages are read from the top-of-page edit bar, exact text.
  - Records are disposable `QCTEST-130952-A-<tc>-<stamp>` tenders (title AND
    reference). Identity (title + ref + entry id + code) is captured right
    after creation by diffing the list ids and reading the new record back;
    teardown deletes only that captured record through the guarded delete.
    The 15 real tenders (codes QC-TENDER-130952-NN…) are never acted on.
  - Public visibility needs workflow PUBLISHED + Active Status ticked
    (standards.md) and, observed live on this object, Status (pageStatus) =
    Published and a Closing Date not past. Every public check first verifies
    the STORED Active Status by re-opening the record, then reads the
    listing from a fresh logged-out context (Load More expanded).

Substitutions disclosed (case wording -> what runs):
  - 146108 "assigned" tender -> a tender the Author OWNS (standards.md role
    sheet: Author edits/deletes its own content via Owner); "a tender NOT
    assigned" -> a QCTEST tender the Editor created (never a real tender, so
    a permission gap cannot alter real content).

Cases 146133-146136, 146283 and 146293 moved to Agent C's
test_tenders_publish_control_panel.py (2026-10-05).

NOT SCRIPTED (out of scope for manage-tender — reported to the QA Manager):
146105, 146106, 146107, 146109, 146130, 146131, 146132, 146137, 146280,
146281 (eTender SUBMISSION review: submissions are stored in EOISubmission,
a view-only object with no Approve/Reject/Rejection-Reason UI; the
`/group/control_panel/manage/-/etender-submissions` URL returns 404 even
signed in) and 146285, 146292 (Tender Category lookup: a Liferay picklist,
not a manage-tender record; editing it changes shared master data).
"""

from __future__ import annotations

from datetime import datetime
from time import monotonic

import allure
import pytest

from cms.pages.tenders.tender_admin_page import (
    A_MSG_ARABIC_SAVED,
    A_MSG_DRAFT_SAVED,
    A_MSG_SAVED_AND_PUBLISHED,
    A_MSG_SUBMITTED_FOR_REVIEW,
    A_QCTEST_PREFIX,
    A_ROLE_AUTHOR,
    A_ROLE_EDITOR,
    A_ROLE_USER_IDS,
    K_REF,
    K_TITLE,
    K_WORK_DESCRIPTION,
    TenderEntryA,
    TenderPublicViewA,
    TenderWorkflowAdminPage,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
TENDERS_CMS_A_GROUP = pytest.mark.xdist_group("tenders_cms_a")
STAMP = datetime.now().strftime("%m%d%H%M%S")

# A publish was measured at 27-30 s to reach Published on a sibling object.
PUBLISH_CONFIRM_TIMEOUT = 120.0
# cms-profile.md measured ~0 s on a JAX-RS source only; this listing is
# server-rendered and was never measured, so the poll is bounded at 30 s and
# the observed latency is attached to the report.
PUBLIC_REFLECT_TIMEOUT = 30.0
PUBLIC_POLL = 1.0

EPIC = "Business Gateway"
FEATURE = "Tenders — Control Panel (workflow)"


def _ref(tc_id: str, suffix: str = "") -> str:
    return TenderWorkflowAdminPage.a_name(tc_id, STAMP) + (f"-{suffix}" if suffix else "")


def _title(tc_id: str, suffix: str) -> str:
    return TenderWorkflowAdminPage.a_name(tc_id, STAMP, suffix)


def _data(tc_id: str, suffix: str, ref_suffix: str = "", **overrides) -> dict:
    return TenderWorkflowAdminPage.a_tender_data(_ref(tc_id, ref_suffix), _title(tc_id, suffix), **overrides)


# ===========================================================================
# Fixtures
# ===========================================================================
class DisposableRegistry:
    """Records this test created (captured identity). Only these are deleted."""

    def __init__(self):
        self._entries: dict[str, TenderEntryA] = {}

    @property
    def entries(self) -> list[TenderEntryA]:
        return list(self._entries.values())

    def track(self, entry: TenderEntryA) -> TenderEntryA:
        if not entry.in_namespace():
            raise ValueError(f"{entry} is not a {A_QCTEST_PREFIX} record")
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
    ctx = new_context(browser)  # TEST_USER storageState — cleanup only
    outcome, failures = [], []
    try:
        cleaner = TenderWorkflowAdminPage(ctx.new_page())
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


def _contexts(browser):
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    return contexts, _make


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read (standards.md)."""
    contexts, make = _contexts(browser)
    yield make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture
def role_pages(browser):
    """Extra auth-free pages for a second account in the same test."""
    contexts, make = _contexts(browser)
    yield make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def _login(page, role: str) -> TenderWorkflowAdminPage:
    """Signs in as `role` in this auth-free context; skips (never falls back)
    when the account cannot sign in or is not the pinned one."""
    admin = TenderWorkflowAdminPage(page)
    outcome = admin.login_as_role(role)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}'")
    admin.open_list_all()
    if outcome != "ok" and not admin.signed_in_user()[0]:
        # The Author never renders the Control Menu the login wrapper waits for;
        # ThemeDisplay on the manage page is the sign-in signal.
        pytest.fail(f"login as '{role}' neither succeeded nor showed Liferay's refusal banner")
    user_id, _ = admin.signed_in_user()
    if user_id != A_ROLE_USER_IDS[role]:
        pytest.skip(f"PRECONDITION: '{role}' credentials sign in as userId {user_id!r}, "
                    f"not the pinned {A_ROLE_USER_IDS[role]}")
    return admin


def _pinned(admin: TenderWorkflowAdminPage, role: str) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == A_ROLE_USER_IDS[role], (
        f"the session is now userId {user_id!r}, not the pinned {role} ({A_ROLE_USER_IDS[role]}) — "
        f"nothing from here on is attributable to {role}"
    )


def _register(admin, disposable, data: dict, ids_before: set) -> TenderEntryA | None:
    """Registers for teardown the ONE new record reading `data`'s ref + title.
    Never raises (registration must not mask the test result)."""
    try:
        entry = admin.identify_created_a(data[K_REF], data[K_TITLE], ids_before)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001
        allure.attach(repr(exc), name=f"registration of {data[K_TITLE]!r} failed")
        return None


def _wait_arabic_saved(admin) -> str:
    """Object Authoring guide §5: on a new record the Arabic is saved a moment
    after the record — wait (bounded) for its message before navigating away."""
    seen = {"text": ""}

    def _done() -> bool:
        seen["text"] = admin.rendered_body_text()
        return A_MSG_ARABIC_SAVED in seen["text"] or "Arabic content was not" in seen["text"]

    try:
        wait_until(_done, timeout=25.0, poll=0.5)
    except WaitTimeoutError:
        return ""
    return A_MSG_ARABIC_SAVED if A_MSG_ARABIC_SAVED in seen["text"] else "the Arabic content was NOT saved"


def _create(admin, disposable, data: dict, publish: bool, role: str = A_ROLE_EDITOR) -> TenderEntryA:
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


def _history(admin, entry: TenderEntryA) -> list[dict]:
    trail = admin.history(entry)
    allure.attach("\n".join(repr(h) for h in trail) or admin.history_cell_text(entry) or "(empty)",
                  name=f"History of {entry.title}")
    return trail


def _require_active_status(admin, entry: TenderEntryA) -> None:
    """User rule + standards.md: Active Status must be STORED as ticked before
    ANY public check (re-opens the record)."""
    admin.open_entry_en(entry.code)
    stored = admin.active_status_stored()
    page_status = admin.picklist_value("pageStatus")
    allure.attach(f"stored Active Status: {stored!r}\nstored Status: {page_status!r}",
                  name="public-visibility preconditions")
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title!r} stores Active Status {stored!r}, not 'true'; "
                    f"the public-page step was not run")


def _public_until(anon_pages, predicate, message: str, locale: str = "en") -> tuple[TenderPublicViewA, float]:
    """Publish-then-poll on the delivery surface in ONE logged-out context;
    returns the view and the observed latency in seconds."""
    view = TenderPublicViewA(anon_pages())
    started = monotonic()

    def _check() -> bool:
        view.open_listing_all(locale)
        return bool(predicate(view))

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL, message=message)
    except WaitTimeoutError:
        view.screenshot("public listing at timeout")
        pytest.fail(f"{message} within {PUBLIC_REFLECT_TIMEOUT:.0f}s "
                    f"(cards: {[c['title'] for c in view.cards()]})")
    latency = monotonic() - started
    allure.attach(f"{latency:.1f}s", name="observed public-listing latency")
    return view, latency


def _visible_publicly(anon_pages, entry: TenderEntryA) -> dict:
    view, _ = _public_until(anon_pages, lambda v: bool(v.card_for(entry.code)),
                            f"DELIVERY: {entry.title!r} never appeared on the logged-out tenders listing")
    return view.card_for(entry.code)


def _assert_not_public(anon_pages, entry: TenderEntryA, within_budget: bool = True) -> None:
    """Absence that cannot pass vacuously: the listing must render real cards
    (positive control) before `entry` is required absent."""
    if within_budget:
        _public_until(anon_pages, lambda v: not v.card_for(entry.code) and len(v.cards()) > 0,
                      f"{entry.title!r} was still on the logged-out tenders listing")
    view = TenderPublicViewA(anon_pages()).open_listing_all()
    cards = view.cards()
    assert cards, f"cannot prove {entry.title!r} is absent: the logged-out listing shows no tender cards"
    assert not view.card_for(entry.code), f"{entry.title!r} is on the logged-out tenders listing"
    assert entry.title not in [c["title"] for c in cards], f"a card titled {entry.title!r} is on the listing"


# ===========================================================================
# 146108 — Auth: Author edits its own tender, not another's
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Author can view and update its own tender records, not others'")
@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.auth
@pytest.mark.pbi_130952
@pytest.mark.tc_146108
@TENDERS_CMS_A_GROUP
def test_author_updates_own_tender_not_others(page, role_pages, disposable):
    # Azure TC 146108 | PBI 130952 | accounts: Site Content Author (156492); the
    # "not assigned" tender is created by the Site Content Editor (156488).
    author = _login(page, A_ROLE_AUTHOR)

    # Step 1 — open an assigned (own) draft tender, edit a field, save.
    own = _create(author, disposable, _data("146108", "Author own draft"), publish=False, role=A_ROLE_AUTHOR)
    assert _has(author.create_banners, A_MSG_DRAFT_SAVED), f"no {A_MSG_DRAFT_SAVED!r}: {author.create_banners}"
    author.open_list_all()
    assert author.row_has_edit_link(own), (
        f"the Author's OWN draft offers no Edit link; row actions {author.row_link_labels(own)}")
    new_value = f"{own.title} edited by the Author"
    author.open_entry_en(own.code)
    author.fill_en(K_WORK_DESCRIPTION, new_value)
    _pinned(author, A_ROLE_AUTHOR)
    author.click_save_as_draft()
    banners = author.success_messages(A_MSG_DRAFT_SAVED) if author.save_went_through() else author.editbar_texts()
    author.evidence("146108 author saved own draft")
    assert author.save_went_through(), f"the Author could not save its own draft: {author.refusal_evidence()}"
    assert _has(banners, A_MSG_DRAFT_SAVED), f"saving the Author's own draft showed {banners}"
    author.open_entry_en(own.code)
    assert author.text_value(K_WORK_DESCRIPTION) == new_value, (
        f"the Author's edit did not persist: Work Description reads {author.text_value(K_WORK_DESCRIPTION)!r}")

    # Step 2 — a tender NOT assigned to this Author: edit must be blocked.
    editor = _login(role_pages(), A_ROLE_EDITOR)
    other_data = _data("146108", "Editor owned draft", ref_suffix="EDITOR")
    other = _create(editor, disposable, other_data, publish=False, role=A_ROLE_EDITOR)
    author.adopt_a(other)
    author.open_list_all()
    labels, actions = author.row_link_labels(other), author.row_actions(other)
    allure.attach(f"labels {labels}\nactions {actions}", name="Author's row actions on the Editor's tender")
    list_offers_edit = author.row_has_edit_link(other) or "delete" in actions

    # Forced browsing: open the other tender's edit URL directly and try to save.
    attempt = {"form": False, "went_through": False, "evidence": {}}
    try:
        author.open_entry_en(other.code)
        attempt["form"] = True
        author.fill_en(K_WORK_DESCRIPTION, f"{other.title} changed by the Author")
        author.click_save_as_draft()
        attempt["went_through"] = author.save_went_through()
        attempt["evidence"] = {"editbar": author.editbar_texts(), **author.refusal_evidence()}
    except Exception as exc:  # noqa: BLE001 — no editable form is itself the block
        attempt["evidence"] = {"error": repr(exc)[:300]}
    author.evidence("146108 author forced edit of editor tender")
    allure.attach(repr(attempt), name="Author forced edit attempt")
    editor.open_entry_en(other.code)
    stored = editor.text_value(K_WORK_DESCRIPTION)
    assert stored == other_data[K_WORK_DESCRIPTION], (
        f"PRODUCT: the Author changed a tender it does not own (opened by its edit URL): Work Description now "
        f"reads {stored!r}; attempt {attempt}")
    assert not attempt["went_through"], (
        f"PRODUCT: the Author's Save as Draft on a tender it does not own was accepted (page reloaded) "
        f"although the stored value did not change: {attempt}")
    # User rule: the block itself works (server 403, nothing stored) — UI-only
    # gaps around it are recorded as low-priority findings, not failed on.
    # Live 2026-10-05: the Author's row on the Editor's DRAFT offers "Edit"
    # (real published tenders show "View"), the form is editable, and the
    # refusal reads "This record was not saved: • Forbidden".
    findings = []
    if list_offers_edit:
        findings.append(f"Author's list offers Edit/Delete on a tender it does not own: labels {labels}, "
                        f"actions {actions}")
    refusal = " ".join(attempt["evidence"].get("editbar") or [])
    if attempt["form"] and "Forbidden" in refusal:
        findings.append(f"the refusal message is the raw {refusal!r} (no permission wording)")
    allure.attach("\n".join(findings) or "none", name="LOW-priority findings (block works)")

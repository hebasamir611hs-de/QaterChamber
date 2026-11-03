"""
cms/tests/useful_links/test_useful_links_page_auth_control_panel.py

Auth, Control_Panel cases for PBI 130702 (Useful Links) in the page-level
batch. All three are Category-shaped ("create a Category", "edit an existing
Category's title"), so they drive the Useful Link Category object — ONLY on
disposable QCTEST-130702- categories each test creates itself (an Author can
only edit records it owns, and no real category is ever edited or deleted).

ACCOUNTS: each case signs in as the named role in an auth-free context
(standards.md "Named CMS User Roles"). If the role cannot sign in, the case
is skipped with the reason — never re-pointed at TEST_USER.

CLEANUP (delete safety): only the record THIS test run created is ever
deleted. Its title is run-unique (QCTEST-130702-<tc>-<token> ...), the row
is found by that EXACT title, must be the single such row, must carry the
entry id captured at creation, and its title cell + Delete-link label are
re-read immediately before clicking that row's own link. No positional
selection (.first/.nth/loops) is used anywhere on the delete path. The
delete runs in the creating role's session first, then (identical checks)
in the default session — where, because the role's form never stores a
Display Order (product defect, see the batch report), the test's own record
is first given a valid Display Order so the Recycle-Bin move is accepted.
"""

from __future__ import annotations

import time

import allure
import pytest

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
)
from cms.pages.useful_links.useful_links_page_admin_page import (
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    CreatedEntry,
    UsefulLinkCategoryAuthoring,
    UsefulLinksPublicView,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

PBI = "130702"
AUTH_FREE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)


def _run_token() -> str:
    """Per-run suffix: a leftover from an interrupted run must never be
    adopted (it was not created by THIS test run), so every run creates and
    deletes its own uniquely-titled record."""
    return str(int(time.time()))[-7:]


def _case(tc_id: str, title: str, severity=allure.severity_level.NORMAL, extra=()):
    def wrap(fn):
        fn = allure.title(title)(fn)
        fn = allure.severity(severity)(fn)
        fn = allure.epic("Business Gateway")(fn)
        fn = allure.feature("Useful Links")(fn)
        fn = allure.story("Useful Links (CMS) - role access")(fn)
        fn = allure.label("pbi", PBI)(fn)
        fn = allure.label("testcase", tc_id)(fn)
        for mark in (pytest.mark.control_panel, pytest.mark.links, pytest.mark.auth,
                     pytest.mark.pbi_130702, getattr(pytest.mark, f"tc_{tc_id}"),
                     pytest.mark.traceability(tc_id), pytest.mark.xdist_group("useful_links_qctest_categories"),
                     *extra):
            fn = mark(fn)
        return fn
    return wrap


def _sign_in_or_skip(category: UsefulLinkCategoryAuthoring, role: str) -> None:
    result = category.login_as_role(role)
    if result != "ok":
        pytest.skip(
            f"BLOCKED (environment): the {role} account in .env could not sign in ({result}). "
            ".env still carries the retired *@xyz.com logins that standards.md records as locked out; "
            f"set the {role} keys to the 2026-09-27 account (userId {ROLE_USER_IDS[role]})."
        )
    assert category.signed_in_user()[0] == ROLE_USER_IDS[role], f"signed in, but not as the {role}"


def _create_category(category: UsefulLinkCategoryAuthoring, title: str, publish: bool,
                     number: str, display_order: str) -> CreatedEntry:
    # Object validation rules: Category Number is a zero-padded "01".."09";
    # Display Order is >= 100 on the 100-grid. (A 4-digit 9800 was observed
    # live to arrive at the server as "no value" - see the batch report.)
    category.open_list()
    assert category.rows_with_exact_title(title) == [], f"leftover {title!r} exists — resolve by hand first"
    category.open_new_form()
    category.fill_category(number=number, eyebrow="QCTEST role check", eyebrow_ar="QCTEST فحص",
                           title=title, title_ar="QCTEST فئة", display_order=display_order, active=True)
    bound_to = category.display_order_control_name()
    category.submit() if publish else category.save_draft()
    report = f"Display Order control bound to {bound_to!r}; " + category.message_report()
    allure.attach(report, name=f"create {title}", attachment_type=allure.attachment_type.TEXT)
    category.open_list()
    rows = category.rows_with_exact_title(title)
    assert len(rows) == 1, f"creating {title!r} did not produce exactly one row ({rows}); save said: {report}"
    return CreatedEntry(title, rows[0]["entry_id"])


def _cleanup(category: UsefulLinkCategoryAuthoring, browser, entry: CreatedEntry | None) -> None:
    """Deletes ONLY the record this test created (exact QCTEST title + the
    entry id captured at creation, both re-verified right before the click).
    First in the creating role's own session (the owner always has Delete on
    its own row); only if that session cannot, in the default authenticated
    session, with the identical identity checks."""
    if entry is None:
        return
    with allure.step(f"Cleanup: delete the QCTEST category this test created ({entry.title})"):
        try:
            if category.delete_disposable(entry):
                return
        except AssertionError as exc:
            if str(exc).startswith("STOP"):
                raise
            allure.attach(str(exc), name="owner-session delete", attachment_type=allure.attachment_type.TEXT)
        context = new_context(browser)
        try:
            admin = UsefulLinkCategoryAuthoring(context.new_page())
            try:
                deleted = admin.delete_disposable(entry)
            except AssertionError as exc:
                if str(exc).startswith("STOP") or "Display Order" not in str(exc):
                    raise
                # The role's form never stored a Display Order on this record
                # (see UsefulLinkCategoryAuthoring.display_order_control_name),
                # so the trash call's validation refuses it. Give THIS test's
                # own record a valid value from the admin form, then delete.
                allure.attach(str(exc), name="delete refused", attachment_type=allure.attachment_type.TEXT)
                assert admin.repair_display_order(entry, "100"), f"could not repair {entry} for deletion"
                deleted = admin.delete_disposable(entry)
            assert deleted, f"cleanup failed: {entry}"
        finally:
            context.close()


def _public_categories(browser) -> list[str]:
    context = new_context(browser, use_auth_state=False)
    try:
        return UsefulLinksPublicView(context.new_page()).open_public("en").category_titles()
    finally:
        context.close()


@AUTH_FREE
@_case("140691", "Verify that a Site Content Editor has full CRUD and publish/unpublish rights on Useful Links content",
       extra=(pytest.mark.uat,))
def test_140691_editor_can_create_edit_publish_category(page, browser):
    category = UsefulLinkCategoryAuthoring(page)
    _sign_in_or_skip(category, ROLE_EDITOR)
    title = f"QCTEST-130702-140691-{_run_token()} Editor Category"
    edited = title + " Edited"
    entry = None
    try:
        with allure.step("Open the Useful Links category authoring surface"):
            category.open_new_form()
            editable = category.form_is_editable()
        assert editable, "Category creation controls are read-only for the Site Content Editor"
        with allure.step("Create a Category and publish it"):
            entry = _create_category(category, title, publish=True, number="09", display_order="800")
        with allure.step("Edit the category title and publish again"):
            category.open_created(entry)
            category.fill_title(edited)
            category.submit()
            category.open_list()
            rows = category.rows_with_exact_title(edited)
            entry = CreatedEntry(edited, entry.entry_id) if rows else entry
            status = category.row_status_by_id(entry.entry_id)
        with allure.step("Confirm the category is live for an anonymous visitor"):
            try:
                wait_until(lambda: edited in _public_categories(browser), timeout=40.0, poll=4.0)
                live = True
            except WaitTimeoutError:
                live = False
        assert rows, "the edited category title did not save"
        assert status == STATUS_PUBLISHED, f"category status after Publish: {status!r}"
        assert live, "the published category is not visible on the public Useful Links page"
    finally:
        _cleanup(category, browser, entry)


@AUTH_FREE
@_case("140692", "Verify that a Site Content Author can edit assigned Useful Links content")
def test_140692_author_can_edit_own_category_title(page, browser):
    category = UsefulLinkCategoryAuthoring(page)
    _sign_in_or_skip(category, ROLE_AUTHOR)
    title = f"QCTEST-130702-140692-{_run_token()} Author Category"
    edited = title + " Edited"
    entry = None
    try:
        with allure.step("Open the Useful Links category surface and create an own (assigned) category"):
            entry = _create_category(category, title, publish=False, number="08", display_order="700")
        with allure.step("Edit the category's title"):
            category.open_created(entry)
            editable = category.form_is_editable()
            category.fill_title(edited)
            bound_to = category.display_order_control_name()
            category.submit()
            edit_report = f"Display Order control bound to {bound_to!r}; " + category.message_report()
            allure.attach(edit_report, name="edit save outcome", attachment_type=allure.attachment_type.TEXT)
            category.open_list()
            rows = category.rows_with_exact_title(edited)
            if rows:
                entry = CreatedEntry(edited, entry.entry_id)
            status = category.row_status_by_id(entry.entry_id)
        assert editable, "the Author has no edit rights on its own category"
        assert rows, f"the Author's title edit was not saved: {edit_report}"
        assert status in (STATUS_DRAFT, STATUS_PENDING_REVIEW), (
            f"expected the Author's edit saved as Draft/Pending Review, got {status!r}"
        )
    finally:
        _cleanup(category, browser, entry)


@AUTH_FREE
@_case("140693", "Verify that a Site Content Author cannot publish Useful Links content directly",
       extra=(pytest.mark.regression,))
def test_140693_author_cannot_publish_category_directly(page, browser):
    category = UsefulLinkCategoryAuthoring(page)
    _sign_in_or_skip(category, ROLE_AUTHOR)
    title = f"QCTEST-130702-140693-{_run_token()} Author Publish Attempt"
    entry = None
    try:
        with allure.step("Edit a Category (own disposable category, saved as draft first)"):
            entry = _create_category(category, title, publish=False, number="07", display_order="600")
            category.open_created(entry)
            label = category.submit_button_label()
        with allure.step("Attempt to click Publish"):
            category.submit()
            category.open_list()
            status = category.row_status_by_id(entry.entry_id)
        with allure.step("Confirm nothing went live for an anonymous visitor"):
            public = _public_categories(browser)
        assert label != "Publish", "the Author is offered a direct Publish button"
        assert status == STATUS_PENDING_REVIEW, f"expected routing to Pending Review, got {status!r}"
        assert title not in public, "the Author's category went live without review"
    finally:
        _cleanup(category, browser, entry)

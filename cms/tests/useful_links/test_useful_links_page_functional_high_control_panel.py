"""
cms/tests/useful_links/test_useful_links_page_functional_high_control_panel.py

Functional-High, Control_Panel case for PBI 130702 (Useful Links),
page-level object:
  140697  publishing is blocked end-to-end when a mandatory field is empty

ACCOUNT: the case names the Site Content Editor, so it signs in as that
named role in an auth-free context (standards.md "Named CMS User Roles") —
never TEST_USER. If that account cannot sign in, the case cannot run here
and is skipped with the reason; it is never re-pointed at another account.

TEST_OWNED on the real singleton 109803: snapshot first, restore in finally.
"""

from __future__ import annotations

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.useful_links.useful_links_page_admin_page import (
    PAGE_TITLE,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    UsefulLinksPageAdminPage,
)

PBI = "130702"


def _case(tc_id: str, title: str, severity=allure.severity_level.NORMAL, extra=()):
    def wrap(fn):
        fn = allure.title(title)(fn)
        fn = allure.severity(severity)(fn)
        fn = allure.epic("Business Gateway")(fn)
        fn = allure.feature("Useful Links")(fn)
        fn = allure.story("Useful Links Page (CMS) - publish validation")(fn)
        fn = allure.label("pbi", PBI)(fn)
        fn = allure.label("testcase", tc_id)(fn)
        for mark in (pytest.mark.control_panel, pytest.mark.links, pytest.mark.functional_high,
                     pytest.mark.pbi_130702, getattr(pytest.mark, f"tc_{tc_id}"),
                     pytest.mark.traceability(tc_id), pytest.mark.xdist_group("useful_links_page_109803"),
                     *extra):
            fn = mark(fn)
        return fn
    return wrap


def _sign_in_or_skip(admin: UsefulLinksPageAdminPage, role: str) -> None:
    result = admin.login_as_role(role)
    if result != "ok":
        pytest.skip(
            f"BLOCKED (environment): the {role} account in .env could not sign in ({result}). "
            ".env still carries the retired *@xyz.com logins that standards.md records as locked out; "
            "set CMS_SITE_CONTENT_EDITOR_EMAIL/PASSWORD to the 2026-09-27 account (userId 156488)."
        )


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@_case("140697", "Verify that publishing is blocked end-to-end when a mandatory field is left empty",
       extra=(pytest.mark.regression,))
def test_140697_publish_blocked_when_page_title_empty(page):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    _sign_in_or_skip(admin, ROLE_EDITOR)
    try:
        with allure.step("Log in as Site Content Editor, open Object Authoring for Useful Links"):
            assert admin.signed_in_user()[0] == ROLE_USER_IDS[ROLE_EDITOR], "not signed in as the Editor"
            status_before = admin.singleton_row_status()
            baseline = admin.snapshot()
            assert baseline["page_title"], "precondition: editor did not open with current values"
        with allure.step("Clear the Page Title field entirely"):
            admin.clear_field(PAGE_TITLE)
            assert admin.field_text(PAGE_TITLE) == ""
        with allure.step("Click Publish (EN context)"):
            admin.submit()
            en = {"reloaded": admin.save_reloaded(), "refusal": admin.refusal_text(),
                  "native": admin.field_native_message(PAGE_TITLE), "report": admin.message_report()}
        with allure.step("Repeat in the Arabic interface"):
            admin.open_singleton(locale="ar")
            admin.clear_field(PAGE_TITLE)
            admin.submit()
            ar = {"reloaded": admin.save_reloaded(), "refusal": admin.refusal_text(),
                  "native": admin.field_native_message(PAGE_TITLE), "report": admin.message_report()}
        with allure.step("Re-read status and stored title"):
            assert admin.signed_in_user()[0] == ROLE_USER_IDS[ROLE_EDITOR], "session was swapped mid-test"
            status_after = admin.singleton_row_status()
            admin.open_singleton()
            stored = admin.field_text(PAGE_TITLE)
        allure.attach(f"EN: {en['report']}\nAR: {ar['report']}", name="messages",
                      attachment_type=allure.attachment_type.TEXT)
        assert not en["reloaded"] and not ar["reloaded"], "Publish was not blocked with an empty Page Title"
        assert status_after == status_before, f"status changed {status_before!r} -> {status_after!r}"
        assert stored == baseline["page_title"], f"partial publish: stored title is {stored!r}"
        assert "Page title is required." in f"{en['refusal']} {en['native']}", (
            f"EN: expected 'Page title is required.'; got refusal={en['refusal']!r} native={en['native']!r}"
        )
        assert "عنوان الصفحة مطلوب." in f"{ar['refusal']} {ar['native']}", (
            f"AR: expected 'عنوان الصفحة مطلوب.'; got refusal={ar['refusal']!r} native={ar['native']!r}"
        )
    finally:
        if baseline is not None:
            # Nested so a failed content restore can never skip re-publishing 109803.
            try:
                admin.restore_text_and_description(baseline)
            finally:
                assert admin.ensure_published() == STATUS_PUBLISHED

"""
cms/tests/useful_links/test_useful_links_page_edge_control_panel.py

Edge, Control_Panel cases for PBI 130702 (Useful Links), page-level batch:
  140786  bilingual fallback of a Category title (disposable QCTEST category)
  140787  a Draft Useful Links page is invisible to a logged-out visitor
          (OUTAGE-GATED: real singleton 109803, see the functional_low module)

ACCOUNT: default authenticated session (TEST_USER, treated as an Editor by
this build) — neither case names a role.

140786 DATA: the case's title "Test Fallback Category" is used behind the
project's mandatory disposable prefix ("QCTEST-130702-140786 Test Fallback
Category") so the record is provably test-created and can be deleted under
the never-delete-by-position rule. It is published + active (it must be, to
be visible), so it appears on the real public page for the test's duration,
and is deleted in `finally` after an identity re-check.
"""

from __future__ import annotations

import os

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.useful_links.useful_links_page_admin_page import (
    SINGLETON_ENTRY_ID,
    CreatedEntry,
    UsefulLinkCategoryAuthoring,
    UsefulLinksPageAdminPage,
    UsefulLinksPublicView,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

PBI = "130702"
SINGLETON_GROUP = pytest.mark.xdist_group("useful_links_page_109803")
CATEGORY_GROUP = pytest.mark.xdist_group("useful_links_qctest_categories")
OUTAGE_APPROVED = os.getenv("QC_ALLOW_USEFUL_LINKS_PAGE_OUTAGE", "") == SINGLETON_ENTRY_ID
requires_outage_approval = pytest.mark.skipif(
    not OUTAGE_APPROVED,
    reason=(
        "BLOCKED pending explicit user approval: this case must set the REAL Useful Links page "
        "(UsefulLinksPage 109803) to Draft, taking it off the public site. standards.md rule 5 of "
        "'Destructive-Precondition Tests Must Use Disposable Test Data' requires an ID-named user "
        "approval; set QC_ALLOW_USEFUL_LINKS_PAGE_OUTAGE=109803 to run."
    ),
)


def _case(tc_id: str, title: str, severity=allure.severity_level.NORMAL, extra=()):
    def wrap(fn):
        fn = allure.title(title)(fn)
        fn = allure.severity(severity)(fn)
        fn = allure.epic("Business Gateway")(fn)
        fn = allure.feature("Useful Links")(fn)
        fn = allure.story("Useful Links Page (CMS) - edge cases")(fn)
        fn = allure.label("pbi", PBI)(fn)
        fn = allure.label("testcase", tc_id)(fn)
        for mark in (pytest.mark.control_panel, pytest.mark.links, pytest.mark.edge,
                     pytest.mark.pbi_130702, getattr(pytest.mark, f"tc_{tc_id}"),
                     pytest.mark.traceability(tc_id), *extra):
            fn = mark(fn)
        return fn
    return wrap


def _poll_public(browser, predicate, locale: str = "en", timeout: float = 40.0) -> dict:
    context = new_context(browser, use_auth_state=False)
    observed = {}
    try:
        view = UsefulLinksPublicView(context.new_page())

        def _check() -> bool:
            view.open_public(locale)
            observed.update(status=view.http_status(), visible=view.is_content_visible(),
                            title=view.title(), categories=view.category_titles(), body=view.body_text())
            return bool(predicate(view))

        try:
            wait_until(_check, timeout=timeout, poll=3.0)
            observed["matched"] = True
        except WaitTimeoutError:
            observed["matched"] = False
    finally:
        context.close()
    return observed


FALLBACK_TITLE = "QCTEST-130702-140786 Test Fallback Category"


@_case("140786", "Verify that a missing translation falls back to the default language instead of rendering blank",
       extra=(pytest.mark.bilingual, pytest.mark.web, CATEGORY_GROUP))
def test_140786_missing_arabic_category_title_falls_back_to_english(page, browser):
    category = UsefulLinkCategoryAuthoring(page)
    created: CreatedEntry | None = None
    try:
        with allure.step("Precondition: no category with this QCTEST title exists yet"):
            category.open_list()
            assert category.rows_with_exact_title(FALLBACK_TITLE) == [], (
                f"a leftover {FALLBACK_TITLE!r} already exists — resolve it by hand before rerunning"
            )
        with allure.step(f"Publish a Category with Title EN = {FALLBACK_TITLE!r} and Title AR left blank"):
            category.open_new_form()
            category.fill_category(number="06", eyebrow="QCTEST fallback", eyebrow_ar="QCTEST تجربة",
                                   title=FALLBACK_TITLE, title_ar="", display_order="900", active=True)
            category.submit()
            outcome = category.message_report()
            category.open_list()
            rows = category.rows_with_exact_title(FALLBACK_TITLE)
            if len(rows) == 1:
                created = CreatedEntry(FALLBACK_TITLE, rows[0]["entry_id"])
        allure.attach(outcome, name="save outcome", attachment_type=allure.attachment_type.TEXT)
        assert created is not None, (
            f"the category did not save with only the EN title populated (Title AR blank): {outcome}"
        )
        with allure.step("Confirm the category is Published with an empty Arabic title"):
            status = category.row_status_by_id(created.entry_id)
            category.open_created(created)
            stored_ar = category.title_ar_value()
        assert status == STATUS_PUBLISHED, f"category status {status!r}"
        assert stored_ar == "", f"precondition: Arabic title is not blank ({stored_ar!r})"
        with allure.step("Load the public page in the Arabic locale in a fresh logged-out context"):
            public = _poll_public(browser, lambda v: FALLBACK_TITLE in v.category_titles(), locale="ar")
        assert public["matched"], (
            "AR page does not show the English title as a fallback for the blank Arabic title; "
            f"category headers seen: {public.get('categories')}"
        )
    finally:
        if created is not None:
            with allure.step("Cleanup: delete the QCTEST category this test created (identity re-verified)"):
                assert category.delete_disposable(created), f"cleanup failed for {created}"


@requires_outage_approval
@_case("140787", "Verify that a Draft/Unpublished Useful Links page is not visible to a logged-out visitor",
       allure.severity_level.CRITICAL, extra=(pytest.mark.regression, pytest.mark.web, SINGLETON_GROUP))
def test_140787_draft_page_not_visible_to_logged_out_visitor(page, browser):
    # "Set the Useful Links page status to Draft" is driven through the
    # record's own Status picklist (pageStatus) — the field literally named
    # Status on the page record and the gate the public fragment keys on.
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    try:
        with allure.step("Snapshot the published singleton"):
            baseline = admin.snapshot()
            published_title = baseline["page_title"]
        with allure.step("Set the Useful Links page status to Draft in the CMS"):
            admin.open_singleton()
            admin.select_page_status("Draft")
            admin.submit()
            admin.open_singleton()
            page_status = admin.page_status()
        with allure.step("Navigate directly to the page URL in a fresh context with no CMS login"):
            public = _poll_public(browser, lambda v: not v.is_content_visible())
        assert page_status == "draft", f"page status is {page_status!r}, expected draft"
        assert public["matched"], (
            f"the Draft page content is visible to an anonymous visitor: title={public.get('title')!r}"
        )
        assert published_title not in (public.get("title") or ""), "Draft content rendered to the visitor"
    finally:
        if baseline is not None:
            # Nested so a failed content restore can never skip re-publishing 109803.
            try:
                with allure.step("TEST_OWNED reset: restore the singleton's content and page status"):
                    admin.restore_text_and_description(baseline)
            finally:
                with allure.step("TEST_OWNED reset: leave the singleton Published"):
                    assert admin.ensure_published() == STATUS_PUBLISHED

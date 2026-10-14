"""
cms/tests/components/test_footer_phase3_control_panel.py -- the open
Control_Panel cases of PBI 129366 (QC-GBL-004, Site Footer), suite 134446,
scripted 2026-10-14 (Phase 3) on the forms read live that day
(cms/pages/components/footer_phase3_admin_page.py). The older module
test_footer_management_control_panel.py is placeholder-gated and carries no
tc_ marks; it is not touched.

Cases: 130988 / 130996 (P1, a user without publish permission is refused,
EN / AR interface), 130978 (footer logo required), 130979 (navigation column
create / edit / reorder), 130995 (AR column heading required). 130982 (invalid
Quick Link URL) is recorded Passed under rule 17 without a test.

PBI running rules: test data may be written to real records, nothing is
deleted (QCTEST columns are kept, inactive), every possibly-persisting click
is logged first, and the real Footer Configuration is left Published with
its previous values. Message wording is recorded, not asserted (rule 17).
"""

from __future__ import annotations

import time

import allure
import pytest

from cms.pages.components.disposable_object_admin import ROLE_AUTHOR, ROLE_EDITOR
from cms.pages.components.footer_phase3_admin_page import (
    FOOTER_CONFIG_CODE,
    FooterConfigForm,
    FooterNavColumnForm,
)
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.tests.live_write_guard import LiveRecord, keep_instead_of_delete, log_live_write
from cms.tests.singleton_baseline import drive_to_published, list_status

PBI = "129366"
CONFIG_REC = LiveRecord("footer-configuration", FOOTER_CONFIG_CODE, "Footer Configuration")
COLUMN_REC = LiveRecord("footer-navigation-column", "QCTEST-*", "QCTEST footer navigation columns")
RUN = time.strftime("%m%d%H%M")
GROUP = pytest.mark.xdist_group("footer_129366")
ACCESS_DENIED_EN = "Access Denied"
ACCESS_DENIED_AR = "تم رفض الوصول"


def _marks(tc: int, *extra):
    def deco(fn):
        for m in reversed(("control_panel", "global_", "pbi_129366", f"tc_{tc}") + extra):
            fn = getattr(pytest.mark, m)(fn)
        fn = allure.label("pbi", PBI)(fn)
        return allure.feature("Site Footer")(allure.epic("Global Components")(fn))
    return deco


def _attach(name: str, data) -> None:
    try:
        allure.attach(str(data), name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:  # noqa: BLE001
        pass


def _config(page, role: str = ROLE_EDITOR) -> FooterConfigForm:
    form = FooterConfigForm(page)
    form.sign_in(role)
    return form


def _config_list(form):
    def _go():
        form.open_entries_list(locale="en")
        return form
    return _go


def _leave_config_published(page, tc: str) -> str:
    """As the Editor: drive the real Footer Configuration back to Published."""
    form = _config(page, ROLE_EDITOR)
    status = list_status(_config_list(form), FOOTER_CONFIG_CODE)
    if status != STATUS_PUBLISHED:
        log_live_write(CONFIG_REC, "<workflow>", STATUS_PUBLISHED, tc, action="publish",
                       note=f"leave the real footer Published (was {status!r})")

        def _submit():
            form.open_entry_by_code(FOOTER_CONFIG_CODE, locale="en")
            form.submit_via(form.STATUS_SUBMIT)

        drive_to_published(_config_list(form), FOOTER_CONFIG_CODE, _submit)
        status = list_status(_config_list(form), FOOTER_CONFIG_CODE)
    return status


def _unprivileged_publish(page, tc: str, locale: str, denied_text: str) -> None:
    """Author (no publish right) opens the real Footer Configuration, changes
    Logo Alt Text (EN) to a QCTEST value and clicks the submit. Expected:
    refused with Access Denied, nothing stored. The Editor reads the stored
    value afterwards and puts the previous value back."""
    editor = _config(page, ROLE_EDITOR)
    editor.open_entry_by_code(FOOTER_CONFIG_CODE, locale="en")
    before = editor.value("logo_alt", "en")
    marker = f"QCTEST-{tc} author change"
    form = _config(page, ROLE_AUTHOR)
    with allure.step(f"As Site Content Author ({locale.upper()} interface) open Footer Configuration"):
        form.open_entry_by_code(FOOTER_CONFIG_CODE, locale=locale)
        note, controls = form.access_denied_note(), form.submit_controls_enabled()
        page.screenshot(path=f"reports/footer-{tc}-author-{locale}.png")
    outcome = {"denied note": note, "controls": controls, "before": before}
    try:
        if not note and any(controls.values()):
            with allure.step(f"Change Logo Alt Text (EN) to {marker!r} and click the enabled submit"):
                form.fill("logo_alt", marker, "en")
                log_live_write(CONFIG_REC, "Logo Alt Text (EN)", marker, tc, action="attempt",
                               note="Author submit on the real footer; expected REFUSED (restored after)")
                form.submit_via(form.STATUS_SUBMIT)
                outcome["messages after click"] = form.visible_form_messages()
                # The refusal renders as a red bar above the entries list
                # ("This record was not saved: Access Denied ..."), read live
                # 2026-10-14 (reports/footer-130988-author-en-after.png).
                import re as _re
                body = page.locator("body").inner_text()
                m = _re.search(r".{0,120}(Access Denied|تم رفض الوصول)[\s\S]{0,250}", body)
                outcome["bar"] = m.group(0) if m else form.refusal_text()
                page.screenshot(path=f"reports/footer-{tc}-author-{locale}-after.png")
        editor = _config(page, ROLE_EDITOR)
        outcome["status after"] = list_status(_config_list(editor), FOOTER_CONFIG_CODE)
        editor.open_entry_by_code(FOOTER_CONFIG_CODE, locale="en")
        outcome["stored after"] = editor.value("logo_alt", "en")
    finally:
        try:
            editor = _config(page, ROLE_EDITOR)
            editor.open_entry_by_code(FOOTER_CONFIG_CODE, locale="en")
            if editor.value("logo_alt", "en") != before:
                log_live_write(CONFIG_REC, "Logo Alt Text (EN)", before, tc, action="publish",
                               note="restore the value read before the test")
                editor.fill("logo_alt", before, "en")
                editor.submit_via(editor.STATUS_SUBMIT)
        except Exception as exc:  # noqa: BLE001
            _attach(f"RESTORE PROBLEM -- set Footer Logo Alt Text (EN) back to {before!r} by hand", repr(exc))
        outcome["end status"] = _leave_config_published(page, tc)
        _attach("outcome", outcome)
    said = " ".join([note, outcome.get("bar", "")] + list(outcome.get("messages after click", [])))
    published_by_author = outcome.get("stored after") == marker and outcome.get("status after") == STATUS_PUBLISHED
    assert not published_by_author, (f"FINDING: the Site Content Author PUBLISHED a change to the live footer "
                                     f"(Logo Alt Text EN = {marker!r}, status Published); restored after")
    assert outcome.get("stored after") == before, f"the Author's change was stored: {outcome}"
    assert denied_text in said or not any(controls.values()), (
        f"nothing was stored, but no '{denied_text}' message showed and the submit was enabled ({outcome})")


@allure.title("Verify that an admin without permission cannot publish footer configuration (ADO-130988)")
@_marks(130988, "auth", "regression")
@GROUP
def test_130988_unprivileged_user_cannot_publish_footer(page):
    _unprivileged_publish(page, "130988", "en", ACCESS_DENIED_EN)


@allure.title("Arabic access-denied message when an unauthorized user publishes footer configuration (ADO-130996)")
@_marks(130996, "auth", "bilingual")
@GROUP
def test_130996_unprivileged_user_denied_arabic(page):
    _unprivileged_publish(page, "130996", "ar", ACCESS_DENIED_AR)


@allure.title("Verify that saving the footer logo without an image shows a required-field error (ADO-130978)")
@_marks(130978, "functional_high")
@GROUP
def test_130978_footer_logo_required(page):
    form = _config(page)
    label = form.spec("logo").label
    form.open_entry_by_code(FOOTER_CONFIG_CODE, locale="en")
    original = form.current_file_name(label)
    assert original, "precondition: the live footer has no logo"
    stored = original
    try:
        with allure.step("Remove the Footer Logo Image and submit"):
            form.remove_current_file(label)
            pending = form.file_removal_pending(label)
            log_live_write(CONFIG_REC, label, "", "130978", action="attempt",
                           note=f"submit with the logo removed (was {original!r}); expected REFUSED")
            blocked = form.submit_via_reading_validity(form.STATUS_SUBMIT)
            shown = list(dict.fromkeys(getattr(form, "last_click_messages", []) + form.visible_form_messages()))
        form.open_entry_by_code(FOOTER_CONFIG_CODE, locale="en")
        stored, status = form.current_file_name(label), form.current_status()
        _attach("outcome (wording not asserted)", {"pending": pending, "blocked": blocked, "shown": shown,
                                                   "stored": stored, "status": status, "original": original})
        assert pending, "precondition: Remove file did not register"
        assert stored == original, f"FINDING: the footer saved with no logo (now {stored!r})"
        assert blocked or shown, "nothing was saved, but no validation message showed"
    finally:
        if stored != original:
            try:
                form.open_entry_by_code(FOOTER_CONFIG_CODE, locale="en")
                log_live_write(CONFIG_REC, label, original, "130978", action="upload",
                               note="re-select the logo the footer held before the test")
                form.select_existing_file(label, original)
                form.submit_via(form.STATUS_SUBMIT)
            except Exception as exc:  # noqa: BLE001
                _attach(f"LOGO RESTORE PROBLEM -- re-select {original!r} on the footer by hand", repr(exc))
        _leave_config_published(page, "130978")


def _column_form(page) -> FooterNavColumnForm:
    form = FooterNavColumnForm(page)
    form.sign_in(ROLE_EDITOR)
    return form


@allure.title("Verify that admin can create, edit, and reorder footer navigation columns (ADO-130979)")
@_marks(130979, "functional_high", "regression")
@GROUP
def test_130979_create_edit_reorder_nav_column(page):
    form = _column_form(page)
    heading = f"QCTEST-130979-{RUN} column"
    try:
        with allure.step("Add a column: heading EN/AR, column number 9, display order 9900, Active off; Publish"):
            form.open_new_entry_form(locale="en")
            form.fill("heading", heading, "en")
            form.fill("heading", f"QCTEST-130979-{RUN} عمود", "ar")
            form.fill("number", "9")
            form.fill("order", "9900")
            form.set_flag("active", False)
            log_live_write(COLUMN_REC, heading, "create (inactive)", "130979", action="create")
            blocked = form.submit_via_reading_validity(form.STATUS_SUBMIT)
        form.open_entries_list(locale="en")
        created = form.row_visible(heading)
        assert created, f"the column was not created (blocked {blocked})"
        with allure.step("Edit its display order to 9901 and Publish"):
            form.open_entry_by_edit_link(heading)
            form.fill("order", "9901")
            log_live_write(COLUMN_REC, heading, "display order 9901", "130979", action="publish")
            blocked2 = form.submit_via_reading_validity(form.STATUS_SUBMIT)
        form.open_entries_list(locale="en")
        form.open_entry_by_edit_link(heading)
        stored = {"heading": form.value("heading", "en"), "heading_ar": form.value("heading", "ar"),
                  "number": form.value("number"), "order": form.value("order"), "status": form.current_status()}
        _attach("outcome", {"blocked": [blocked, blocked2], "stored": stored})
        assert stored["heading"] == heading and stored["number"] == "9", f"fields not saved: {stored}"
        assert stored["order"] == "9901", f"display order did not update: {stored}"
    finally:
        keep_instead_of_delete(COLUMN_REC, heading, "130979")


@allure.title("Required-field message when the Arabic column heading is omitted (ADO-130995)")
@_marks(130995, "functional_high", "bilingual")
@GROUP
def test_130995_ar_column_heading_required(page):
    form = _column_form(page)
    heading = f"QCTEST-130995-{RUN} no AR"
    with allure.step("Add a column with the Arabic heading empty; Publish"):
        form.open_new_entry_form(locale="en")
        form.fill("heading", heading, "en")
        form.fill("heading", "", "ar")
        form.fill("number", "9")
        form.fill("order", "9900")
        form.set_flag("active", False)
        log_live_write(COLUMN_REC, heading, "create with AR heading empty", "130995", action="attempt",
                       note="expected REFUSED")
        blocked = form.submit_via_reading_validity(form.STATUS_SUBMIT)
        shown = list(dict.fromkeys(getattr(form, "last_click_messages", []) + form.visible_form_messages()))
        page.screenshot(path="reports/footer-130995-ar-heading.png")
    form.open_entries_list(locale="en")
    saved = form.row_visible(heading)
    _attach("outcome (wording not asserted)", {"blocked": blocked, "shown": shown, "saved": saved})
    if saved:
        keep_instead_of_delete(COLUMN_REC, heading, "130995")
    assert not saved, "FINDING: the column saved without an Arabic heading"
    assert blocked or shown, "nothing was saved, but no validation message showed"

"""
cms/tests/live_status_cases.py -- the "Status dropdown offers and stores
Draft / Published" case shape, shared by three REAL singleton records
(user decision 2026-10-13, P3/P4 batch -- see cms/tests/live_write_guard.py):

    About Qatar Chamber Page  134737 / 134738   (`pageStatus` picklist)
    Chairman Message Page     134835 / 134836   (`publishStatus` picklist)
    Chamber Laws Page         134937 / 134938   (`pageStatus` picklist)

WHAT "Status" MEANS HERE. The cases name the record's own Status DROPDOWN --
the object's Picklist field (liferay-context.md: `pageStatus` /
`publishStatus`, options Draft / Published[ / Unpublished]) -- NOT the
Kaleo workflow badge. The picklist is what is selected, saved and re-read.
The workflow status is only driven so the form is editable (a Published
record must be unpublished first, guide section 4) and so the record is
left live.

"Click Save" = the form's Publish / Submit for Review control (status=0),
the module convention: Save as Draft skips validation and would move the
workflow to Draft. On an Unpublished record that submit stores the fields
and leaves the workflow Unpublished (GM incident 2026-10-12), so the end
state is driven through the documented row transitions
(singleton_baseline.drive_to_published).

END STATE (user decision 2026-10-13): every case leaves the record with the
picklist = Published AND the workflow = Published -- a status change is
allowed, a deletion never is. Every persisted step is logged BEFORE its
click to reports/live-writes-20261013.jsonl (log_live_write).

The CALLER must open the write gate first
(`block_live_singleton_write(<record>, ..., tc_id=...)`) -- without
`QC_ALLOW_LIVE_SINGLETON_WRITES=1` the case is NOT APPLICABLE before
anything here runs. `status_draft_case` / `status_published_case` are in
test_cms_conventions.py's write-call list for exactly that reason.

Account: the caller passes Page Objects bound to a Site Content Editor
session (privileged -- its transitions land without a review step).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import allure

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED, STATUS_UNPUBLISHED
from cms.tests.live_write_guard import log_live_write
from cms.tests.singleton_baseline import drive_to_editable, drive_to_published, list_status

DRAFT = "Draft"
PUBLISHED = "Published"
WORKFLOW_BUDGET = 150.0  # s -- one unpublish or one publish, verified on a fresh list read


@dataclass
class PicklistRecord:
    """One real singleton, as the Status cases need it."""

    record: str                       # *_RECORD text naming the approved entry code
    entry_code: str
    form: Any                         # PO: page_status_value / pick_page_status
    open_form: Callable[[], Any]      # opens the record's edit form; returns the authoring page
    save: Callable[[Any], dict]       # clicks Save (status=0) on it; {"refusal": str, "success": str}
    open_list: Callable[[], Any]      # the entries list (ObjectAuthoringPage)
    budget: float = WORKFLOW_BUDGET


def _attach(name: str, body) -> None:
    try:
        allure.attach(str(body), name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:  # noqa: BLE001
        pass


def _ensure_editable(rec: PicklistRecord, tc: str) -> None:
    """Published -> Unpublished (row action, verified) so the form can be
    edited. Logged before the click."""
    if list_status(rec.open_list, rec.entry_code) == STATUS_PUBLISHED:
        log_live_write(rec.record, "<workflow>", STATUS_UNPUBLISHED, tc, action="unpublish",
                       note="make the form editable (guide section 4)")
        drive_to_editable(rec.open_list, rec.entry_code, budget=rec.budget)


def _save_status(rec: PicklistRecord, tc: str, value: str, note: str) -> dict:
    """Select `value` in the Status picklist, click Save, re-open, re-read."""
    _ensure_editable(rec, tc)
    authoring = rec.open_form()
    # One open of the list: read every option, pick, verify (status_picklist.py).
    options = rec.form.pick_page_status(value)
    chosen = rec.form.page_status_value()
    log_live_write(rec.record, "Status (picklist)", value, tc, action="status", note=note)
    said = rec.save(authoring)
    rec.open_form()
    out = {"options": options, "chosen": chosen, "said": said, "stored": rec.form.page_status_value()}
    _attach(f"Status -> {value} ({note})", out)
    return out


def _leave_published(rec: PicklistRecord, tc: str) -> None:
    """End state: picklist Published, then workflow Published.

    The workflow republish ALWAYS runs, whatever the picklist step did
    (2026-10-13: the picklist read raised first and the republish never ran,
    which left Chairman / About / Chamber Laws Unpublished three times). A
    picklist problem is re-raised only after the record is live again."""
    picklist_problem = None
    try:
        rec.open_form()
        if rec.form.page_status_value() != PUBLISHED:
            _save_status(rec, tc, PUBLISHED, "end state: leave the record Published")
    except Exception as exc:  # noqa: BLE001 -- re-raised after the republish
        picklist_problem = exc
    if list_status(rec.open_list, rec.entry_code) != STATUS_PUBLISHED:
        log_live_write(rec.record, "<workflow>", STATUS_PUBLISHED, tc, action="publish",
                       note="end state: leave the record Published")
        drive_to_published(rec.open_list, rec.entry_code, lambda: rec.save(rec.open_form()),
                           budget=rec.budget)
    if picklist_problem is not None:
        raise picklist_problem


def _with_end_state(rec: PicklistRecord, tc: str, body: Callable[[], None]) -> None:
    """Runs `body`, then ALWAYS restores the Published end state. A failing
    end state never masks the case's own failure; on a passing case it fails
    the test (the record is not live)."""
    problem = None
    try:
        body()
    finally:
        with allure.step("End state: picklist Published + workflow Published"):
            try:
                _leave_published(rec, tc)
            except Exception as exc:  # noqa: BLE001 -- reported below / attached
                problem = exc
                _attach("END STATE NOT RESTORED -- check the record by hand", repr(exc))
    if problem is not None:
        raise AssertionError(f"the case passed but the record was not left Published: {problem!r}")


def status_draft_case(rec: PicklistRecord, tc: str, exact_options: bool) -> None:
    """Steps: open the record (Status dropdown available) -> select Draft,
    Save (the dropdown lists [exactly] Draft and Published; Draft selected
    and saved, no refusal) -> reload: Status reads Draft."""

    def body() -> None:
        with allure.step("Open the Status dropdown (record made editable), select Draft, click Save"):
            out = _save_status(rec, tc, DRAFT, "case step 2")
            options = out["options"]
        _attach("Status options offered", options)
        with allure.step("Reload the record"):
            rec.open_form()
            stored = rec.form.page_status_value()
        if exact_options:
            assert sorted(options) == sorted([DRAFT, PUBLISHED]), (
                f"the Status dropdown must list exactly Draft and Published; it lists {options}")
        else:
            missing = [o for o in (DRAFT, PUBLISHED) if o not in options]
            assert not missing, f"the Status dropdown does not list {missing}; it lists {options}"
        assert out["chosen"] == DRAFT, f"selecting Draft left the dropdown on {out['chosen']!r}"
        assert not out["said"].get("refusal"), f"the save was refused: {out['said']['refusal']!r}"
        _attach("success message (wording/toast is a note, not asserted)", out["said"].get("success"))
        assert stored == DRAFT, f"after reload Status reads {stored!r}, expected 'Draft'"

    _with_end_state(rec, tc, body)


def status_published_case(rec: PicklistRecord, tc: str) -> None:
    """Steps: open the record with Status currently Draft (established here,
    logged, if it is not) -> select Published, Save (selected and saved, no
    refusal) -> reload: Status reads Published."""

    def body() -> None:
        with allure.step("Precondition: the record opens with Status Draft"):
            rec.open_form()
            if rec.form.page_status_value() != DRAFT:
                _save_status(rec, tc, DRAFT, "precondition: Status Draft")
            rec.open_form()
            before = rec.form.page_status_value()
        assert before == DRAFT, f"precondition: Status reads {before!r}, not Draft -- not continuing"
        with allure.step("Open the Status dropdown, select Published, click Save"):
            out = _save_status(rec, tc, PUBLISHED, "case step 2")
        with allure.step("Reload the record"):
            rec.open_form()
            stored = rec.form.page_status_value()
        assert out["chosen"] == PUBLISHED, f"selecting Published left the dropdown on {out['chosen']!r}"
        assert not out["said"].get("refusal"), f"the save was refused: {out['said']['refusal']!r}"
        _attach("success message (wording/toast is a note, not asserted)", out["said"].get("success"))
        assert stored == PUBLISHED, f"after reload Status reads {stored!r}, expected 'Published'"

    _with_end_state(rec, tc, body)

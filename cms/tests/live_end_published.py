"""
cms/tests/live_end_published.py -- leave a REAL record Published after a test
that was allowed to write to it (user decision 2026-10-13, P1/P2 rerun).

A test that unpublishes a real record, or sets it to Draft, must re-publish it
in `finally`. `leave_published(...)` wraps the test body and, ONLY when the
write gate opened for that record in this test
(`live_write_guard.gate_opened()`), drives the record back to Published
through the documented transitions (`singleton_baseline.drive_to_published`):

    Unpublished    -> the row action `[data-qc-oel-publish]` (confirm chain accepted)
    Pending Review -> the row's approve
    Draft          -> `submit_draft()` (the form's Submit for Review / Publish)

each verified on a FRESH entries-list read, then re-read once more here. The
re-publish is logged with `log_live_write()` BEFORE the first click. A record
already Published is only read. Nothing is ever deleted.

A failed re-publish never masks the test's own failure; on a passing test it
fails the test (the live record is not Published -- check it by hand).

Nothing here is a newsletter: newsletter approve / publish / send stays NOT
APPLICABLE elsewhere.
"""

from __future__ import annotations

from contextlib import contextmanager

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.tests.live_write_guard import gate_opened, log_live_write
from cms.tests.singleton_baseline import drive_to_published, list_status

REPUBLISH_BUDGET = 150.0


def _attach(name: str, body) -> None:
    try:
        import allure

        allure.attach(str(body), name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:  # noqa: BLE001 -- reporting must never mask anything
        pass


def republish(record, open_list, entry_code: str, submit_draft, tc=None,
              budget: float = REPUBLISH_BUDGET) -> str:
    """Drive `entry_code` back to Published (logged first) and PROVE it on a
    fresh entries-list read. Returns the final status."""
    status = list_status(open_list, entry_code)
    if status == STATUS_PUBLISHED:
        return status
    log_live_write(record, "<workflow>", STATUS_PUBLISHED, tc, action="publish",
                   note=f"finally: re-publish from {status!r} (Unpublished -> row action "
                        "[data-qc-oel-publish]; documented transitions, verified)")
    drive_to_published(open_list, entry_code, submit_draft, budget=budget)
    final = list_status(open_list, entry_code)
    if final != STATUS_PUBLISHED:
        raise AssertionError(f"{entry_code!r} reads {final!r} after the re-publish, not Published")
    return final


@contextmanager
def leave_published(record, open_list, entry_code: str, submit_draft, tc=None,
                    budget: float = REPUBLISH_BUDGET):
    """Wraps a writing test body; see the module docstring. `open_list()`
    navigates to and returns the entries list (an ObjectAuthoringPage);
    `submit_draft()` submits the record's form from Draft."""
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        if gate_opened(record):
            problem = ""
            try:
                republish(record, open_list, entry_code, submit_draft, tc, budget)
            except Exception as exc:  # noqa: BLE001 -- reported below
                problem = repr(exc)
                _attach(f"END STATE NOT RESTORED -- re-publish {entry_code} by hand", problem)
            if problem and not failed:
                raise AssertionError(
                    f"the case passed but {entry_code} was not left Published: {problem}")

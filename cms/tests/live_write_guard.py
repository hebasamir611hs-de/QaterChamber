"""
cms/tests/live_write_guard.py -- the one place that decides whether automation
may write to a REAL singleton record, and the log of every write it makes.

USER DECISION (2026-10-13, P1/P2 batch) -- the DEFAULT
------------------------------------------------------
Automation does not write to any real singleton record. A singleton object
holds exactly one record ("This page holds this one record only"), and the
About Hero Banner object renders no create form, so no disposable QCTEST
record can exist on it. A case that needs a SAVED / PUBLISHED / UNPUBLISHED
change on such a record is reported as NOT APPLICABLE -- never skipped, never
mutating.

USER DECISION (2026-10-13, P3/P4 batch) -- the OPT-IN
-----------------------------------------------------
With the environment variable `QC_ALLOW_LIVE_SINGLETON_WRITES=1`, tests MAY
write test data to FOUR named real singleton records, and nothing else:

    GM Message 79878              QCDEMO-129397-general-managers-message
    Chairman Message Page 78261   QCDEMO-129393-chairmans-message
    About Qatar Chamber Page      QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY
    Chamber Laws Page             QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY

* NOTHING is ever deleted under the opt-in. The user cleans the test data by
  hand, so EVERY persisted write is logged first, as one JSON line, to
  `reports/live-writes-20261013.jsonl` (`log_live_write()`).
* The gate opens only for a test of THIS batch (`P34_BATCH_TCS`, the 38
  Azure ids of the P3/P4 todo files -- the tc id passed, else the trailing
  id of the test's name) AND a description that names one of the four entry
  codes above. [Widened for the P1/P2 rerun and the hero rows -- see the
  next section.] A P1/P2 test, or a test whose name carries no batch id, stays
  NOT APPLICABLE with the variable set (fails closed): those tests do not
  log their field writes. Every other record -- the About Hero Banner rows
  (`about-us`, `chairman-message`, `chamber-laws`), the hero QCTEST create
  path, any future singleton -- stays NOT APPLICABLE whatever the variable
  says. (The hero create helpers continue past this call when the create
  form is missing; opening the gate for them would type a QCTEST key into
  the LIVE hero row -- the singleton-manage-page trap.)
* Select a run by `-m tc_<id>` (the batch's ids) when the variable is set;
  the batch restriction above is the backstop, not the plan.

USER DECISION (2026-10-13, P1/P2 rerun) -- the opt-in WIDENED
-------------------------------------------------------------
Nothing is Not Applicable because of a real-record write any more. With
`QC_ALLOW_LIVE_SINGLETON_WRITES=1` the gate ALSO opens for the 84 P1/P2
rerun ids (`P12_BATCH_TCS`, from
.claude/qa-runs/phase3-20261012/p12_rerun_ids.json) and for THREE more real
records -- the About Hero Banner rows (object `about-hero-banner`):

    QCDEMO-ABOUT-HERO-about-us
    QCDEMO-ABOUT-HERO-chairman-message
    QCDEMO-ABOUT-HERO-chamber-laws

Same rules: NOTHING is deleted (`deletes_suppressed()` is True under the
opt-in -- a disposable QCTEST row is LEFT and logged with action `kept`),
every persisted write is logged BEFORE its click, and a test that unpublishes
or sets Draft on a real record re-publishes it in `finally`
(cms/tests/live_end_published.py: Unpublished -> the row action
`[data-qc-oel-publish]`, verified on a fresh entries-list read). The hero
QCTEST CREATE path stays closed whatever the variable says
(`refuse_hero_create()`): on qcdev the create form is hidden and the manage
page opens the LIVE row instead (incident 183176). Newsletter
approve / publish / send stays NOT APPLICABLE (its own guard, unchanged).

Calls
-----
* `block_live_singleton_write(desc, note="", tc_id=None)` -- placed
  IMMEDIATELY BEFORE the first step that would persist anything to the real
  record (Save as Draft, Submit for Review / Publish, Unpublish, a row
  workflow action, a file replace that saves). Default: fails the test with a
  message starting "NOT APPLICABLE -- singleton record ...", which triage
  maps to Not Applicable. Opted-in AND an approved record AND a batch test
  case: logs a `gate-opened` line and returns, so the test continues and
  writes.

* `log_live_write(record, field, value, tc_id, action="write", note="")` --
  called right BEFORE each click that can persist something (pytest-timeout
  on Windows hard-exits without `finally`, so a line written after the click
  could be lost). `action` names the kind of write: `save-draft`,
  `publish`, `unpublish`, `status`, `upload`, `remove-file`, `create`,
  `attempt` (a click the case expects to be REFUSED -- logged in case the
  refusal fails and the value is stored).

* `stop_unless_refused(refused, desc, what, evidence)` -- for tests whose
  whole point is a REFUSED save. Unchanged by the opt-in.

`cms/tests/test_cms_conventions.py` checks statically that, in the singleton
test modules, every write call has a guard or a refusal stop earlier in the
same function, and checks the opt-in behaviour of this file.

Nothing here touches the browser.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from dataclasses import dataclass
from pathlib import Path

import pytest

DECISION = "user decision 2026-10-13"
NOT_APPLICABLE_PREFIX = "NOT APPLICABLE -- singleton record"
FINDING_PREFIX = "FINDING -- refusal not observed on singleton record"

OPT_IN_ENV = "QC_ALLOW_LIVE_SINGLETON_WRITES"
ROOT = Path(__file__).resolve().parents[2]
# One log per run day (PBI running rules, rule 10: reports/live-writes-*.jsonl).
LOG_PATH = ROOT / "reports" / f"live-writes-{_dt.date.today():%Y%m%d}.jsonl"


@dataclass(frozen=True)
class LiveRecord:
    """A record the log can name: Object Authoring slug + entry code."""

    slug: str
    code: str
    title: str = ""


# The ONLY records the opt-in opens (user decision 2026-10-13: the four
# singletons for the P3/P4 batch, plus the three About Hero Banner rows for
# the P1/P2 rerun).
APPROVED_RECORDS = (
    LiveRecord("general-manager-message", "QCDEMO-129397-general-managers-message", "GM Message 79878"),
    LiveRecord("chairman-message-page", "QCDEMO-129393-chairmans-message", "Chairman Message Page 78261"),
    LiveRecord("about-qatar-chamber-page", "QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY",
               "About Qatar Chamber Page"),
    LiveRecord("chamber-laws-page", "QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY", "Chamber Laws Page"),
    LiveRecord("about-hero-banner", "QCDEMO-ABOUT-HERO-about-us", "About Hero Banner row about-us"),
    LiveRecord("about-hero-banner", "QCDEMO-ABOUT-HERO-chairman-message",
               "About Hero Banner row chairman-message"),
    LiveRecord("about-hero-banner", "QCDEMO-ABOUT-HERO-chamber-laws", "About Hero Banner row chamber-laws"),
)


# The P3/P4 batch the opt-in covers (user decision 2026-10-13) -- a literal,
# never read from the qa-runs todo files at runtime (CI may not have them).
P34_BATCH_TCS = frozenset({
    # PBI 129397 -- GM Message
    "135466", "135468", "135475", "135498", "135500", "135503", "135509", "135512", "135514",
    "136380", "136381", "136390", "136403", "136409", "136415", "136427", "136438", "136439",
    "136440", "136441", "136446", "136447", "136458", "136461", "136462",
    # PBI 129392 -- About Qatar Chamber
    "134731", "134733", "134736", "134737", "134738",
    # PBI 129393 -- Chairman's Message
    "134829", "134831", "134834", "134835", "134836",
    # PBI 129394 -- Chamber's Law
    "134937", "134938", "134974",
})

# The P1/P2 rerun the opt-in ALSO covers (user decision 2026-10-13) -- the 84
# ids of .claude/qa-runs/phase3-20261012/p12_rerun_ids.json, as a literal.
P12_BATCH_TCS = frozenset({
    # PBI 129384 -- Home Dynamic Widgets
    "135953", "136061",
    # PBI 129388 -- Home Media Gallery
    "133654", "133657", "133662", "133666", "133676", "133678", "133688",
    # PBI 129392 -- About Qatar Chamber
    "134685", "134686", "134691", "134692", "134693", "134697", "134710", "134711", "134713",
    "134717",
    # PBI 129393 -- Chairman's Message
    "134770", "134779", "134793", "134821",
    # PBI 129394 -- Chamber's Law
    "134850", "134851", "134868", "134871", "134873", "134874", "134875", "134877", "134882",
    "134883", "134884", "134885", "134886", "134887", "134888", "134897", "134899", "134900",
    "134901", "134902", "134940", "134941", "134942", "134943", "134944", "134945", "134948",
    "134949", "134952", "134953", "134956", "134957", "134960", "134961", "134964", "134965",
    "134968", "134969", "134971", "134972", "134973", "134975", "134976", "134977", "134987",
    # PBI 129397 -- GM Message
    "135446", "135447", "135458", "135490", "135493", "135504", "135508", "135511", "136377",
    "136378", "136419", "136432", "136436",
    # PBI 129566 -- Newsletter (no CMS test exists for these three)
    "134616", "134617", "134620",
})

# Every test case the opt-in opens the gate for.
OPT_IN_BATCH_TCS = P34_BATCH_TCS | P12_BATCH_TCS

# (current test, record code) pairs whose gate opened in this process -- read
# by gate_opened(), so a `finally` re-publishes only a record THIS test was
# allowed to write.
_OPENED: set = set()


def live_writes_opted_in() -> bool:
    """True when `QC_ALLOW_LIVE_SINGLETON_WRITES=1` is set for this run."""
    return os.environ.get(OPT_IN_ENV, "").strip() == "1"


def deletes_suppressed() -> bool:
    """True under the opt-in: NOTHING is deleted (user decision 2026-10-13),
    not even a disposable QCTEST row. Without the variable the existing
    QCTEST teardown is unchanged."""
    return live_writes_opted_in()


def approved_record(desc) -> LiveRecord | None:
    """The approved record a description / LiveRecord names, else None."""
    if isinstance(desc, LiveRecord):
        return next((r for r in APPROVED_RECORDS if r.code == desc.code), None)
    text = str(desc or "")
    return next((r for r in APPROVED_RECORDS if r.code in text), None)


def _as_record(record) -> LiveRecord:
    if isinstance(record, LiveRecord):
        return record
    return approved_record(record) or LiveRecord("?", str(record or ""), str(record or ""))


def _current_test() -> str:
    return os.environ.get("PYTEST_CURRENT_TEST", "").rsplit(" (", 1)[0]


def _tc_from_test(nodeid: str) -> str:
    """Best effort: the trailing 6-digit Azure id most test names carry."""
    import re

    found = re.findall(r"(?<!\d)(1[3-4]\d{4})(?!\d)", nodeid or "")
    return found[-1] if found else ""


def log_live_write(record, field: str, value, tc_id, action: str = "write", note: str = "") -> dict:
    """Appends ONE self-contained JSON line describing a persisted (or
    possibly-persisted) write. Opened in append mode, flushed and closed per
    line, so a hard-killed run keeps every line written before the kill.
    Never raises: a logging problem must not hide the test's own result, but
    it is reported on stderr."""
    rec = _as_record(record)
    entry = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "tc": str(tc_id or _tc_from_test(_current_test())),
        "object_slug": rec.slug,
        "record_code": rec.code,
        "record": rec.title,
        "action": action,
        "field": field,
        "value": value if isinstance(value, (str, int, float, bool, type(None))) else repr(value),
        "note": note,
        "test": _current_test(),
        "worker": os.environ.get("PYTEST_XDIST_WORKER", "main"),
        "opted_in": live_writes_opted_in(),
    }
    try:
        path = Path(LOG_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            fh.flush()
    except Exception as exc:  # noqa: BLE001 -- reported, never masks the result
        import sys

        print(f"[live_write_guard] could not write {LOG_PATH}: {exc!r}", file=sys.stderr)
    try:
        import allure

        allure.attach(json.dumps(entry, ensure_ascii=False, indent=1), name=f"live write: {field}",
                      attachment_type=allure.attachment_type.JSON)
    except Exception:  # noqa: BLE001
        pass
    return entry


def block_live_singleton_write(record_desc: str, note: str = "", tc_id=None) -> None:
    """Default: fails the test as NOT APPLICABLE -- the next step would write
    to the real singleton `record_desc`. `note` adds what was already
    observed (e.g. permission problems found before this point).

    Opted in (`QC_ALLOW_LIVE_SINGLETON_WRITES=1`) AND `record_desc` names one
    of APPROVED_RECORDS AND the test case is in P34_BATCH_TCS: logs a
    `gate-opened` line and returns, so the test goes on and writes. The test
    itself logs each write with `log_live_write()`."""
    record = approved_record(record_desc)
    tc = str(tc_id or _tc_from_test(_current_test()))
    in_batch = tc in OPT_IN_BATCH_TCS
    if live_writes_opted_in() and record is not None and in_batch:
        batch = "P3/P4 batch" if tc in P34_BATCH_TCS else "P1/P2 rerun"
        log_live_write(record, "<write gate>", note, tc, action="gate-opened",
                       note=f"{OPT_IN_ENV}=1 ({DECISION}, {batch})")
        _OPENED.add((_current_test(), record.code))
        return
    message = (
        f"{NOT_APPLICABLE_PREFIX} {record_desc}: a successful save would write to real site "
        "content and no disposable record can exist on a one-record object "
        f"({DECISION})"
    )
    if live_writes_opted_in() and record is None:
        message += (f"\n{OPT_IN_ENV}=1 is set, but this record is not one of the seven the user "
                    "approved for live writes -- the opt-in does not open it.")
    elif live_writes_opted_in() and not in_batch:
        message += (f"\n{OPT_IN_ENV}=1 is set, but test case {tc or '(no id)'} is not in the "
                    "P3/P4 batch or the P1/P2 rerun the user approved -- the opt-in does not open it.")
    if note:
        message += f"\nObserved before this point: {note}"
    pytest.fail(message, pytrace=False)


def gate_opened(record_desc) -> bool:
    """True when block_live_singleton_write() opened the gate for
    `record_desc` in the CURRENT test -- a `finally` re-publishes only a
    record this test was allowed to write."""
    record = approved_record(record_desc)
    return record is not None and (_current_test(), record.code) in _OPENED


def keep_instead_of_delete(record, title: str, tc_id=None, note: str = "") -> bool:
    """Teardown gate for a disposable QCTEST row. Under the opt-in: logs a
    `kept` line naming `title` and returns True -- the caller must NOT
    delete. Otherwise returns False and the caller's existing exact-title
    QCTEST delete runs as before."""
    if not deletes_suppressed():
        return False
    log_live_write(record, "<disposable row>", title, tc_id, action="kept",
                   note=note or f"left for manual cleanup -- nothing is deleted under {OPT_IN_ENV}=1 "
                                f"({DECISION})")
    return True


def refuse_hero_create(record_desc: str, note: str = "") -> None:
    """The About Hero Banner QCTEST CREATE path: ALWAYS NOT APPLICABLE, opt-in
    or not. On qcdev the create form is hidden and the manage page opens the
    LIVE hero row instead, so a create helper that carried on would type a
    QCTEST key into the real row (singleton-manage-page trap, incident
    183176). A case that needs a saved hero row runs on the REAL row through
    block_live_singleton_write() instead."""
    message = (
        f"{NOT_APPLICABLE_PREFIX} {record_desc}: no empty create form for a disposable QCTEST "
        f"hero row, and the create path never writes to the live row ({DECISION})"
    )
    if note:
        message += f"\nObserved before this point: {note}"
    pytest.fail(message, pytrace=False)


def stop_unless_refused(refused: bool, record_desc: str, what: str, evidence=None,
                        restored: bool | None = None) -> None:
    """For refusal cases: after the single click the case expects to be
    refused, stop at once when no refusal was observed. Nothing after this
    point runs, so nothing else is written to the real record.

    `restored` (added 2026-10-14): the caller already put the previous value
    back (logged) and re-read it -- True when the re-read matched, False when
    it did not. None keeps the original "check by hand" wording."""
    if refused:
        return
    if restored is None:
        tail = "The attempted value may now be stored -- check the record by hand before the next run."
    elif restored:
        tail = "The previous value was put back (logged) and re-read intact."
    else:
        tail = ("The previous value was put back (logged) but did NOT re-read intact -- "
                "check the record by hand before the next run.")
    pytest.fail(
        f"{FINDING_PREFIX} {record_desc}: {what} was NOT refused "
        f"(evidence: {evidence!r}). The test stops here so nothing else is written "
        f"to the real record ({DECISION}). {tail}",
        pytrace=False,
    )

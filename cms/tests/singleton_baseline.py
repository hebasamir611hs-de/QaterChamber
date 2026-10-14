"""
cms/tests/singleton_baseline.py -- capture a live singleton record ONCE per PBI
run, restore it ONCE at the end.

WHY THIS EXISTS (user decision 2026-10-12)
------------------------------------------
The singleton modules (GM Message 79878, About Qatar Chamber, Chairman's
Message 78261) used to restore the live record in every test's `finally`:
unpublish -> write back -> republish -> re-read, ~1 min each, with retry
loops. That doubled the cost of every case and was the suspected source of
runs hanging in teardown. The decision: a test mutates the record and leaves
it; the record is restored ONCE, at the end of the module.

THE CONTRACT
------------
* **Module start** (before any singleton test runs):
    1. If a snapshot from an interrupted run exists (state not "restored") and
       the live record differs from it, restore from THAT snapshot first.
       A killed run therefore heals at the start of the next one.
    2. Capture a full baseline -- every EN/AR text field, rich-text HTML,
       attachment bytes (downloaded via the record's own Download link),
       Active Status where the form has one, and the workflow status -- into
       `reports/backups/<pbi>_<slug>_<YYYYMMDD-HHMM>/snapshot.json` (+ files).
       The JSON is written only after every file is on disk, with
       state="in_progress".
* **Each singleton test**: a status-only precondition -- approve a Pending
  Review version, or publish an Unpublished/Draft one -- so every case still
  starts from a Published record. No field is written back. If that status
  step is refused (a failed test left a required field empty), the record is
  restored from the module snapshot once, then the test runs.
* **Module end**: one restore pass from the snapshot, then a fresh re-read.
  A mismatch is attached to Allure and raised. Only a verified re-read flips
  the snapshot to state="restored".
* **A killed run**: `python tools/restore_singleton.py --pbi <pbi>` performs
  the same restore from the latest unrestored snapshot.

XDIST
-----
The module fixture is reached only through `singleton_gate()` -- an autouse,
function-scoped fixture that pulls it in for tests carrying the singleton's
own `xdist_group`. Under `--dist loadgroup` that group runs on ONE worker, so
exactly one worker snapshots and restores. A test from the same module in a
different group (disposable QCTEST rows) never triggers it, and so never
races the restore on another worker.

TIMEOUTS
--------
pytest-timeout covers setup + teardown by default, so the module snapshot
would run inside the first test's budget and the restore inside the last
test's. On Windows the thread method hard-exits with no `finally`. The
module fixture therefore swaps the running item's timer for a dedicated
budget while it captures / restores (`pytest_timeout_set_timer` /
`pytest_timeout_cancel_timer` hooks), then re-arms the test's own timeout.
If the hard limit still fires, the snapshot on disk stays "in_progress" and
the next run (or the CLI) restores from it.

WORKFLOW (fixed 2026-10-12, PBI 129397 incident)
-----------------------------------------------
Status is driven ONLY through the documented seven-state transitions
(standards.md "Content Editorial Workflow"), read back from a FRESH
entries-list read: `drive_to_published()` / `drive_to_editable()`. The old
path clicked the form's Publish/Submit control on an UNPUBLISHED record and
waited 90 s for a status that control never produces -- the GM record had
to be published by hand. Unpublished -> the row's `data-qc-oel-publish`
action (confirm/prompt chain accepted, comment RESTORE_COMMENT). Fields are
written only when they differ, and only after the record is editable.

SESSION
-------
`ensure_cms_session()` lands on a CMS-only page and checks `body.signed-in`
(waiting briefly for it -- a document caught mid-navigation has no body yet).
A stale TEST_USER storageState (~2 h after tools/save_auth.py) reads as
signed out; it re-authenticates ONCE as TEST_USER before failing, with a
message that names tools/save_auth.py. Nothing here ever signs out: a
server logout kills the SHARED storageState session for every context.

READ-ONLY (`--dry-run`)
-----------------------
`SingletonBaseline.read_only = True` makes every write path (apply, restore,
mark, precondition, capture) raise, and the session check refuses to fill
the login form -- a dry-run reads, it never types.
"""

from __future__ import annotations

import datetime as _dt
import importlib
import json
import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from cms.pages.components.object_authoring_page import (
    STATUS_ARCHIVED,
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_REJECTED,
    STATUS_UNPUBLISHED,
)
from core.utils.logger import get_logger

_log = get_logger("singleton_baseline")

ROOT = Path(__file__).resolve().parents[2]
BACKUP_ROOT = ROOT / "reports" / "backups"
SNAPSHOT_FILE = "snapshot.json"

STATE_IN_PROGRESS = "in_progress"
STATE_RESTORED = "restored"
STATE_RESTORE_FAILED = "restore_failed"
_UNRESTORED = (STATE_IN_PROGRESS, STATE_RESTORE_FAILED)

VERIFY_TIMEOUT = 60.0  # fresh re-read may lag a publish by a few seconds
VERIFY_POLL = 5.0
SETUP_BUDGET = 600  # s -- heal + capture (incl. attachment downloads)
TEARDOWN_BUDGET = 900  # s -- one restore pass per record + verify
RESTORE_COMMENT = "QA automation restore"  # answers every workflow prompt()
WORKFLOW_STEP_TIMEOUT = 60.0  # s -- one transition to show on a fresh list read
WORKFLOW_POLL = 5.0
GATE_WORKFLOW_BUDGET = 100.0  # s -- per-test status step; fits the tests' reserve
RESTORE_WORKFLOW_BUDGET = 300.0  # s -- module-end / CLI status step

# PBI -> "module:factory". The factory returns a SingletonBaseline. Used by
# tools/restore_singleton.py, which must not import test modules.
REGISTRY = {
    "129392": "cms.tests.about_qatar_chamber.about_singleton:build_baseline",
    "129393": "cms.tests.chairman_message.chairman_singleton:build_baseline",
    "129397": "cms.tests.gm_message.gm_message_singleton:build_baseline",
}

_ACTIVE: dict = {}  # pbi -> SingletonBaseline while its module is running
_CURRENT_ITEM: dict = {}  # test module name -> the item currently executing


def _attach(name: str, body) -> None:
    try:
        import allure

        text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False, indent=1, default=str)
        allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:  # noqa: BLE001 -- reporting never masks a result
        pass


def copy_with_name(src: Path, name: str) -> str:
    """A temp copy of a snapshot file under its ORIGINAL file name, so a
    re-upload keeps the same stem (Liferay dedupes it as `name (n).ext`)."""
    folder = Path(tempfile.mkdtemp(prefix="qc_singleton_restore_"))
    dest = folder / name
    shutil.copyfile(src, dest)
    return str(dest)


# ---------------------------------------------------------------------------
# Record adapter -- one per live record, implemented next to its test module
# ---------------------------------------------------------------------------
class RecordAdapter:
    """One live record. Subclasses implement `read`, `apply`, `diff` (and,
    for attachments, `download_files`). Values in the state dict must be
    JSON-serialisable; keys starting with "_" are bookkeeping, and a target
    value of None means "not readable on this form -- do not compare"."""

    key: str = ""  # stable id inside snapshot.json, e.g. "gm_message_79878"
    title: str = ""  # human label for reports
    per_test_precondition: bool = True  # status-normalise before every test
    read_only: bool = False  # set by SingletonBaseline; prepare() must not type then

    def prepare(self, page) -> None:
        """Sign the page in as this record's restore account (default:
        whatever the context already holds). When `self.read_only`, it must
        not fill any form -- use ensure_cms_session(..., allow_login=False)."""

    def read(self, page) -> dict:
        raise NotImplementedError

    def download_files(self, page, state: dict, dest: Path) -> dict:
        """{state_key: path relative to the snapshot dir} of downloaded bytes."""
        return {}

    def apply(self, page, target: dict, files_dir: Path) -> None:
        raise NotImplementedError

    def same(self, key: str, have, want) -> bool:
        """Per-key comparison; override for HTML / file-name keys."""
        return have == want

    def changed_keys(self, actual: dict, target: dict) -> list:
        return [key for key, want in target.items()
                if not key.startswith("_") and want is not None
                and not self.same(key, actual.get(key), want)]

    def diff(self, actual: dict, target: dict) -> list:
        return [f"{key}: have {str(actual.get(key))[:120]!r} want {str(target[key])[:120]!r}"
                for key in self.changed_keys(actual, target)]

    def ensure_ready(self, page) -> None:
        """Status-only precondition (no field writes); raise if impossible."""


# ---------------------------------------------------------------------------
# Snapshot bookkeeping
# ---------------------------------------------------------------------------
def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, path)


class SingletonBaseline:
    def __init__(self, pbi: str, slug: str, adapters, before_start=None, read_only: bool = False):
        self.pbi = str(pbi)
        self.slug = slug
        self.adapters = list(adapters)
        self.before_start = before_start  # optional hook (legacy marker migration)
        self.snapshot_dir: Path | None = None
        self.read_only = read_only  # tools/restore_singleton.py --dry-run
        # Optional `hook(page, exc, step)` called while the page is still on
        # the failing step, before restore() folds the error into its diff
        # (tools/restore_singleton.py --debug-screenshot). None under pytest.
        self.on_step_error = None

    def _step_error(self, page, exc: BaseException, step: str) -> None:
        if self.on_step_error is None:
            return
        try:
            self.on_step_error(page, exc, step)
        except Exception as hook_exc:  # noqa: BLE001 -- diagnostics never mask the result
            _log.warning("on_step_error hook failed: %r", hook_exc)

    def _writable(self, operation: str) -> None:
        if self.read_only:
            raise RuntimeError(
                f"PBI {self.pbi}: {operation} refused -- this baseline is READ-ONLY (--dry-run)")

    def _prepare(self, adapter, page) -> None:
        adapter.read_only = self.read_only
        adapter.prepare(page)

    # ---- discovery ---------------------------------------------------------
    def snapshot_dirs(self) -> list:
        if not BACKUP_ROOT.exists():
            return []
        prefix = f"{self.pbi}_{self.slug}_"
        found = [p for p in BACKUP_ROOT.iterdir()
                 if p.is_dir() and p.name.startswith(prefix) and (p / SNAPSHOT_FILE).exists()]
        return sorted(found, key=lambda p: p.name)

    def latest_unrestored(self) -> Path | None:
        pending = [p for p in self.snapshot_dirs()
                   if _read_json(p / SNAPSHOT_FILE).get("state") in _UNRESTORED]
        if len(pending) > 1:
            _log.warning("several unrestored snapshots for PBI %s: %s -- using the newest",
                         self.pbi, [p.name for p in pending])
        return pending[-1] if pending else None

    def _new_dir(self) -> Path:
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M")
        base = BACKUP_ROOT / f"{self.pbi}_{self.slug}_{stamp}"
        path, n = base, 2
        while path.exists():
            path = base.with_name(f"{base.name}-{n}")
            n += 1
        path.mkdir(parents=True)
        return path

    def mark(self, snapshot_dir: Path, state: str, **extra) -> None:
        self._writable(f"marking the snapshot {state!r}")
        path = snapshot_dir / SNAPSHOT_FILE
        data = _read_json(path)
        data["state"] = state
        data.setdefault("history", []).append(
            {"at": _dt.datetime.now().isoformat(timespec="seconds"), "state": state, **extra})
        _write_json(path, data)

    # ---- capture -----------------------------------------------------------
    def capture(self, page) -> Path:
        self._writable("capture")
        folder = self._new_dir()
        records = {}
        try:
            for adapter in self.adapters:
                self._prepare(adapter, page)
                state = adapter.read(page)
                files = adapter.download_files(page, state, folder / "files" / adapter.key)
                state["_files"] = {k: (folder / "files" / adapter.key / v).relative_to(folder).as_posix()
                                   for k, v in files.items()}
                records[adapter.key] = state
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)  # no JSON = never a heal source
            raise
        _write_json(folder / SNAPSHOT_FILE, {
            "pbi": self.pbi, "slug": self.slug, "state": STATE_IN_PROGRESS,
            "created": _dt.datetime.now().isoformat(timespec="seconds"),
            "records": records,
        })
        self.snapshot_dir = folder
        _attach(f"singleton baseline captured -> {folder.name}", records)
        _log.info("singleton baseline for PBI %s captured to %s", self.pbi, folder)
        return folder

    # ---- diff / restore ----------------------------------------------------
    def current_diff(self, page, snapshot_dir: Path) -> dict:
        records = _read_json(snapshot_dir / SNAPSHOT_FILE)["records"]
        out = {}
        for adapter in self.adapters:
            if adapter.key in records:
                self._prepare(adapter, page)
                out[adapter.key] = adapter.diff(adapter.read(page), records[adapter.key])
        return out

    def _restore_one(self, page, adapter, target: dict, snapshot_dir: Path) -> list:
        """ONE apply pass, then a fresh re-read (polled briefly). Returns the
        remaining diff ([] == verified)."""
        from core.utils.waits import wait_until

        self._writable(f"restoring {adapter.title}")
        self._prepare(adapter, page)
        if not adapter.diff(adapter.read(page), target):
            return []
        adapter.apply(page, target, snapshot_dir)
        last = {"diff": ["not re-read"]}

        self._prepare(adapter, page)

        def _matches() -> bool:
            last["diff"] = adapter.diff(adapter.read(page), target)
            return not last["diff"]

        try:
            wait_until(_matches, timeout=VERIFY_TIMEOUT, poll=VERIFY_POLL)
        except Exception:  # noqa: BLE001 -- the remaining diff is the evidence
            pass
        return last["diff"]

    def restore(self, page, snapshot_dir: Path | None = None, reason: str = "module end") -> None:
        self._writable("restore")
        snapshot_dir = snapshot_dir or self.snapshot_dir
        if snapshot_dir is None:
            raise AssertionError(f"PBI {self.pbi}: no snapshot to restore from")
        records = _read_json(snapshot_dir / SNAPSHOT_FILE)["records"]
        problems = {}
        for adapter in self.adapters:
            if adapter.key not in records:
                continue
            try:
                diff = self._restore_one(page, adapter, records[adapter.key], snapshot_dir)
            except Exception as exc:  # noqa: BLE001 -- keep restoring the other records
                self._step_error(page, exc, f"restore {adapter.title}")
                diff = [f"restore raised: {exc!r} at {getattr(page, 'url', '?')}"]
            if diff:
                problems[adapter.key] = diff
        if problems:
            self.mark(snapshot_dir, STATE_RESTORE_FAILED, reason=reason, problems=problems)
            detail = (f"SINGLETON RESTORE FAILED ({reason}) for PBI {self.pbi} from "
                      f"{snapshot_dir}.\nThe live record(s) are OFF their captured baseline. "
                      f"Run: python tools/restore_singleton.py --pbi {self.pbi} "
                      f"--snapshot \"{snapshot_dir}\"\n"
                      + json.dumps(problems, ensure_ascii=False, indent=1))
            _log.error(detail)
            _attach(f"SINGLETON RESTORE FAILED - PBI {self.pbi}", detail)
            raise AssertionError(detail)
        self.mark(snapshot_dir, STATE_RESTORED, reason=reason)
        _attach(f"singleton restored and verified ({reason})", str(snapshot_dir))
        _log.info("PBI %s singleton(s) restored from %s (%s)", self.pbi, snapshot_dir, reason)

    # ---- module lifecycle --------------------------------------------------
    def start(self, page) -> Path:
        if self.before_start is not None:
            self.before_start(self)
        interrupted = self.latest_unrestored()
        if interrupted is not None:
            diff = self.current_diff(page, interrupted)
            _attach(f"interrupted snapshot found: {interrupted.name}", diff)
            if any(diff.values()):
                self.restore(page, interrupted, reason="heal at start of the next run")
            else:
                self.mark(interrupted, STATE_RESTORED, reason="record already matched at next run start")
        return self.capture(page)

    def precondition(self, page) -> None:
        """Status-only normalisation before each singleton test; one full
        restore from the module snapshot if the status step is refused."""
        self._writable("the per-test precondition")
        for adapter in self.adapters:
            if not adapter.per_test_precondition:
                continue
            try:
                adapter.ensure_ready(page)
                continue
            except Exception as exc:  # noqa: BLE001 -- fall back to the snapshot once
                _attach(f"precondition refused on {adapter.title} -- restoring from snapshot", repr(exc))
            records = _read_json(self.snapshot_dir / SNAPSHOT_FILE)["records"]
            diff = self._restore_one(page, adapter, records[adapter.key], self.snapshot_dir)
            if diff:
                raise AssertionError(
                    f"precondition: {adapter.title} could not be brought back to a usable state "
                    f"(snapshot {self.snapshot_dir.name}): {diff}")


def active(pbi: str) -> SingletonBaseline | None:
    return _ACTIVE.get(str(pbi))


def load(pbi: str) -> SingletonBaseline:
    """The registered baseline for `pbi` (used by the CLI)."""
    target = REGISTRY.get(str(pbi))
    if not target:
        raise KeyError(f"no singleton baseline registered for PBI {pbi}; known: {sorted(REGISTRY)}")
    module, factory = target.split(":")
    return getattr(importlib.import_module(module), factory)()


# ---------------------------------------------------------------------------
# CMS session -- detect a signed-out page, re-authenticate ONCE (Problem: a
# stale TEST_USER storageState silently broke module fixtures ~2 h after
# tools/save_auth.py)
# ---------------------------------------------------------------------------
SIGNED_IN_SETTLE_MS = 5000  # see cms_signed_in()


def cms_signed_in(page, settle_ms: int = SIGNED_IN_SETTLE_MS) -> bool:
    """`body.signed-in` present (true for every CMS role, see CmsLoginPage)
    and no login form on the page. Never raises.

    Waits up to `settle_ms` for the marker first (2026-10-12): the GM
    singleton's bare manage URL goes on to `?editEntry=<code>` after
    `domcontentloaded`, and a zero-wait read of that half-loaded document
    reported "signed out" (allure-129397-20261012-2120) and sent a live
    session to the login page."""
    from cms.pages.control_panel.login_page import CmsLoginPage

    try:
        if settle_ms:
            try:
                page.locator(CmsLoginPage.LOGIN_SUCCESS_INDICATOR).first.wait_for(
                    state="attached", timeout=settle_ms)
            except Exception:  # noqa: BLE001 -- genuinely signed out: answered below
                pass
        return (page.locator(CmsLoginPage.LOGIN_SUCCESS_INDICATOR).count() > 0
                and page.locator(CmsLoginPage.USERNAME_INPUT).count() == 0)
    except Exception:  # noqa: BLE001
        return False


def ensure_cms_session(page, landing_url: str, allow_login: bool = True) -> None:
    """Land on `landing_url` (a CMS-only page) as TEST_USER.

    1. Navigate. With `allow_login`, BasePage.open() runs the session guard,
       which already re-authenticates a visible login form / dead session.
    2. Still signed out (login form, "Sign In", public fallback page)? Sign in
       ONCE as TEST_USER through the login page -- only if the form really
       renders (an already-signed-in session is redirected AWAY from it, and
       typing into the missing field was the dry-run's 30 s fill/clear crash).
    3. Still signed out -> fail, naming tools/save_auth.py.

    `allow_login=False` (read-only / --dry-run): a raw navigation, no guard,
    nothing typed -- a signed-out page fails straight away.

    NEVER signs anyone out (2026-10-12): no /c/portal/logout, no
    CmsLoginPage.ensure_signed_in_as(). The context carries TEST_USER's SHARED
    storageState session; a server logout kills it for every other context,
    worker and tool (it stranded 79878 in Unpublished twice). The one login
    path below types only when LOGIN_PATH renders a form, i.e. for an
    anonymous session -- a live one is redirected away from it. Enforced by
    cms/tests/test_cms_conventions.py::test_singleton_engine_never_logs_out."""
    from cms.pages.control_panel.login_page import CmsLoginPage
    from config.settings import settings

    login = CmsLoginPage(page)
    if allow_login:
        login.open(landing_url)
    else:
        page.goto(landing_url, wait_until="domcontentloaded", timeout=90000)
    if cms_signed_in(page):
        return
    if not allow_login:
        raise AssertionError(
            f"CMS session is signed out (or behind the license / login gate) at {page.url} "
            "and this run is READ-ONLY, so the "
            "login form is not filled. Refresh the saved session (python tools/save_auth.py) "
            "and run again.")
    _log.warning("CMS session signed out at %s -- re-authenticating once as TEST_USER", page.url)
    login.open_login()
    try:
        page.locator(CmsLoginPage.USERNAME_INPUT).first.wait_for(state="visible", timeout=15000)
        form_shown = True
    except Exception:  # noqa: BLE001 -- redirected away: the session is already valid
        form_shown = False
    if form_shown:
        login.login(settings.test_user, settings.test_password)
    login.open(landing_url)
    if not cms_signed_in(page):
        raise AssertionError(
            f"CMS session is signed out at {page.url} even after one TEST_USER re-login. "
            "Check TEST_USER/TEST_PASSWORD in .env, refresh the saved session with "
            "python tools/save_auth.py, and check qcdev is up (license / login gate).")


# ---------------------------------------------------------------------------
# Workflow driver -- documented transitions only, verified by a fresh
# entries-list read (standards.md "Content Editorial Workflow")
# ---------------------------------------------------------------------------
# status -> (row action, ObjectAuthoringPage method) on the way to Published
_TO_PUBLISHED = {
    STATUS_PENDING_REVIEW: ("approve", "approve_entry"),
    STATUS_UNPUBLISHED: ("publish", "publish_entry"),
    STATUS_REJECTED: ("resubmit", "resubmit_entry"),
    STATUS_ARCHIVED: ("restore", "restore_entry"),
}
# status -> row action on the way to an EDITABLE state
_TO_EDITABLE = {
    STATUS_PUBLISHED: ("unpublish", "unpublish_entry"),
    STATUS_PENDING_REVIEW: ("approve", "approve_entry"),
    STATUS_ARCHIVED: ("restore", "restore_entry"),
}
EDITABLE_STATUSES = (STATUS_DRAFT, STATUS_UNPUBLISHED, STATUS_REJECTED)


class _Budget:
    def __init__(self, seconds: float, what: str):
        import time

        self._time = time
        self.end = time.monotonic() + seconds
        self.what = what

    def left(self, cap: float) -> float:
        remaining = self.end - self._time.monotonic()
        if remaining <= 0:
            raise AssertionError(f"{self.what}: workflow time budget spent")
        return max(1.0, min(cap, remaining))


def list_status(open_list, entry_code: str) -> str:
    """The record's status from a FRESH entries-list read. `open_list()`
    navigates and returns the ObjectAuthoringPage showing the list."""
    lister = open_list()
    status = lister.row_status_text_by_code(entry_code)
    if not status:
        raise AssertionError(f"no entries-list row for {entry_code!r} on manage-{lister.slug}")
    return status


def _row_step(open_list, entry_code: str, status: str, action: str, method: str, comment: str) -> None:
    lister = open_list()
    offered = lister.row_actions_by_code(entry_code)
    if action not in offered:
        raise AssertionError(
            f"{entry_code!r} is {status!r} but its row offers {sorted(offered)}, not {action!r} -- "
            "the signed-in account lacks this transition (role decides the row actions)")
    _log.info("workflow: %s is %s -> row action %r", entry_code, status, action)
    getattr(lister, method)(entry_code, comment=comment)


def _await_move(open_list, entry_code: str, before: str, budget: _Budget, step: str) -> str:
    from core.utils.waits import wait_until

    seen = {"status": before}

    def _moved() -> bool:
        seen["status"] = list_status(open_list, entry_code)
        return seen["status"] != before

    try:
        wait_until(_moved, timeout=budget.left(WORKFLOW_STEP_TIMEOUT), poll=WORKFLOW_POLL)
    except AssertionError:
        raise
    except Exception as exc:  # noqa: BLE001 -- WaitTimeoutError: report the stuck state
        raise AssertionError(
            f"{step}: {entry_code!r} stayed {before!r} on a fresh entries-list read") from exc
    return seen["status"]


def drive_to_published(open_list, entry_code: str, submit_draft, comment: str = RESTORE_COMMENT,
                       budget: float = RESTORE_WORKFLOW_BUDGET, max_steps: int = 4) -> str:
    """Bring the record to Published through the documented transitions,
    one at a time, each verified by a fresh entries-list read:

        Pending Review -> approve | Unpublished -> publish (row action)
        Rejected -> resubmit      | Archived -> restore (-> Unpublished)
        Draft -> `submit_draft()` (the form's Submit for Review; a privileged
                 account lands on Published, otherwise Pending Review, which
                 the next pass approves)

    Scheduled / unknown states raise -- they need a human. Every row action
    accepts the whole confirm()/prompt() chain, answering prompts with
    `comment`. Returns the final status (always Published)."""
    clock = _Budget(budget, f"drive {entry_code!r} to Published")
    status = list_status(open_list, entry_code)
    path = [status]
    for _ in range(max_steps):
        if status == STATUS_PUBLISHED:
            break
        if status in _TO_PUBLISHED:
            action, method = _TO_PUBLISHED[status]
            _row_step(open_list, entry_code, status, action, method, comment)
        elif status == STATUS_DRAFT:
            action = "submit for review"
            _log.info("workflow: %s is Draft -> form Submit for Review", entry_code)
            submit_draft()
        else:
            raise AssertionError(
                f"{entry_code!r} is {status!r}: no automatic path to Published (Scheduled / "
                f"unknown states need a human). Row offers "
                f"{sorted(open_list().row_actions_by_code(entry_code))}")
        status = _await_move(open_list, entry_code, status, clock, action)
        path.append(status)
    if status != STATUS_PUBLISHED:
        raise AssertionError(f"{entry_code!r} did not reach Published; path {path}")
    _attach(f"workflow: {entry_code} -> Published", " -> ".join(path))
    return status


def drive_to_editable(open_list, entry_code: str, comment: str = RESTORE_COMMENT,
                      budget: float = RESTORE_WORKFLOW_BUDGET, max_steps: int = 3) -> str:
    """Bring the record to a state its form can be edited in (Draft,
    Unpublished, Rejected): Published -> unpublish; Pending Review ->
    approve (then unpublish); Archived -> restore. Verified by a fresh
    entries-list read after every step. Returns the editable status."""
    clock = _Budget(budget, f"make {entry_code!r} editable")
    status = list_status(open_list, entry_code)
    path = [status]
    for _ in range(max_steps):
        if status in EDITABLE_STATUSES:
            break
        if status not in _TO_EDITABLE:
            raise AssertionError(
                f"{entry_code!r} is {status!r}: no automatic path to an editable state")
        action, method = _TO_EDITABLE[status]
        _row_step(open_list, entry_code, status, action, method, comment)
        status = _await_move(open_list, entry_code, status, clock, action)
        path.append(status)
    if status not in EDITABLE_STATUSES:
        raise AssertionError(f"{entry_code!r} did not reach an editable state; path {path}")
    return status


# ---------------------------------------------------------------------------
# pytest-timeout: give capture / restore their own budget
# ---------------------------------------------------------------------------
def _item_timeout_settings(item):
    try:
        import pytest_timeout

        settings = pytest_timeout._get_item_settings(item)
    except Exception:  # noqa: BLE001 -- plugin absent / API changed: leave timers alone
        return None
    if not settings.timeout or settings.timeout <= 0 or settings.func_only:
        return None  # no protocol-wide timer is running on this item
    return settings


def _swap_timer(item, seconds: float | None) -> bool:
    """Replace the item's running pytest-timeout timer with one of `seconds`
    (None = the item's own configured timeout). False when not applicable."""
    settings = _item_timeout_settings(item) if item is not None else None
    if settings is None:
        return False
    hook = item.config.pluginmanager.hook
    try:
        hook.pytest_timeout_cancel_timer(item=item)
        if seconds is not None:
            settings = settings._replace(timeout=seconds)
        hook.pytest_timeout_set_timer(item=item, settings=settings)
        return True
    except Exception:  # noqa: BLE001
        return False


@contextmanager
def _session(browser):
    from core.web.browser import new_context

    context = new_context(browser)
    try:
        yield context.new_page()
    finally:
        try:
            context.close()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Fixture factories -- assign the results to module globals in the test module
# ---------------------------------------------------------------------------
def module_baseline_fixture(build):
    """Module-scoped fixture `_singleton_baseline`: start() before the first
    singleton test, restore() after the last. Never autouse -- it is pulled
    in only by `singleton_gate()`."""

    @pytest.fixture(scope="module", name="_singleton_baseline")
    def _singleton_baseline(request, browser):
        baseline = build()
        module = request.module.__name__
        item = _CURRENT_ITEM.get(module)
        swapped = _swap_timer(item, SETUP_BUDGET)
        try:
            with _session(browser) as pg:
                baseline.start(pg)
        finally:
            if swapped:
                _swap_timer(item, None)  # the test gets its own full budget back
        _ACTIVE[baseline.pbi] = baseline
        try:
            yield baseline
        finally:
            _ACTIVE.pop(baseline.pbi, None)
            _swap_timer(_CURRENT_ITEM.get(module), TEARDOWN_BUDGET)
            with _session(browser) as pg:
                baseline.restore(pg, reason="module end")

    return _singleton_baseline


def singleton_gate(group: str):
    """Autouse fixture `_singleton_gate`: for a test in xdist_group `group`,
    pull in the module baseline and run the status-only precondition on the
    test's own `page` (when it uses one). Other tests pass straight through."""

    @pytest.fixture(autouse=True, name="_singleton_gate")
    def _singleton_gate(request):
        _CURRENT_ITEM[request.module.__name__] = request.node
        marker = request.node.get_closest_marker("xdist_group")
        name = (marker.args[0] if marker and marker.args else (marker.kwargs.get("name") if marker else None))
        if name != group:
            yield None
            return
        baseline = request.getfixturevalue("_singleton_baseline")
        if "page" in request.fixturenames:
            gate_page = request.getfixturevalue("page")
            # The status step gets its own budget (Windows' thread timeout
            # hard-exits with no `finally`): a slow publish must not eat the
            # test's main-path time and kill it mid-mutation.
            swapped = _swap_timer(request.node, SETUP_BUDGET)
            try:
                baseline.precondition(gate_page)
            finally:
                if swapped:
                    _swap_timer(request.node, None)
        yield baseline

    return _singleton_gate


_SLUG_RE = re.compile(r"[^A-Za-z0-9]+")


def slugify(text: str) -> str:
    """Folder-safe name. An Arabic twin label ("<Label> — العربية") keeps an
    `_ar` suffix, so the EN and AR attachments never share a folder."""
    base = _SLUG_RE.sub("_", text).strip("_").lower() or "file"
    return base + "_ar" if re.search(r"[؀-ۿ]", text) else base  # Arabic block

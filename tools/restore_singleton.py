#!/usr/bin/env python3
"""
restore_singleton.py -- restore a live singleton record from the module-level
snapshot its test module captured, when a run was killed before the module-end
restore could run (pytest-timeout hard-exit, closed terminal, crash).

Same code path as the module fixture (cms/tests/singleton_baseline.py + the
PBI's record adapter): one apply pass per record, then a fresh re-read; the
snapshot is marked "restored" only when the re-read matches.

    python tools/restore_singleton.py --list                       # all registered PBIs, offline
    python tools/restore_singleton.py --pbi 129397 --list          # one PBI's snapshots, offline
    python tools/restore_singleton.py --pbi 129397 --dry-run       # print the live diff, write nothing
    python tools/restore_singleton.py --pbi 129397                 # latest UNRESTORED snapshot
    python tools/restore_singleton.py --pbi 129392 --snapshot reports/backups/129392_about_qatar_chamber_20261012-1730
    python tools/restore_singleton.py --pbi 129397 --debug-screenshot reports/debug   # screenshot + URL on a timeout

Registered: 129392 About Qatar Chamber (page record + about-us hero row),
129393 Chairman's Message (78261 + chairman-message hero row),
129397 GM Message (79878).

WRITE GATE (user decision 2026-10-13)
-------------------------------------
Automation no longer writes to real singleton records, and the test modules
no longer wire the snapshot/restore engine. A restore is itself a live write,
so the writing path now REFUSES unless it is asked for explicitly:

    python tools/restore_singleton.py --pbi 129397 --i-understand-this-writes-live

Read-only paths (--list, --dry-run) need no flag.

RULES
-----
* NEVER run this while a pytest session (or any other agent) is driving
  qcdev -- it writes to the same live record the tests mutate (CLAUDE.md:
  one agent at a time against qcdev).
* It prints the live diff BEFORE writing anything; `--dry-run` stops there.
  `--dry-run` is strictly READ-ONLY (2026-10-12): the baseline is built with
  read_only=True, so every write path raises, the snapshot is never marked,
  and the session check never fills the login form -- a stale saved session
  fails with "run tools/save_auth.py" instead of typing into the CMS.
* Status is restored through the documented workflow transitions only
  (e.g. Unpublished -> the row's Publish action), verified by a fresh
  entries-list read -- see singleton_baseline.drive_to_published().
* It restores content records only (Object Authoring). It never deletes a
  record and never touches fragments or page layout.
* Credentials come from .env (TEST_USER; the Chairman adapter signs in as the
  Site Content Editor via cms_role_credentials()).
* It NEVER signs out (no /c/portal/logout anywhere on its path): the context
  loads the SHARED .auth/state.json session, and a server logout would sign
  out every other context, worker and tool using it. Enforced by
  cms/tests/test_cms_conventions.py::test_singleton_engine_never_logs_out.
* `--debug-screenshot PATH` (a .png file, or a directory): when a step times
  out, save a viewport screenshot of the page AS IT IS at that moment and
  print its URL. The URL alone tells "stranded off the manage page" apart
  from "on the page, element never rendered".
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

# Run as a script, so sys.path[0] is tools/ -- add the project root (same
# bootstrap as tools/save_auth.py); importing config.settings loads .env.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cms.tests import singleton_baseline as sb  # noqa: E402


def _print_snapshots(pbi: str) -> None:
    baseline = sb.load(pbi)
    dirs = baseline.snapshot_dirs()
    print(f"PBI {pbi} ({baseline.slug}): {len(dirs)} snapshot(s) under {sb.BACKUP_ROOT}")
    for d in dirs:
        data = json.loads((d / sb.SNAPSHOT_FILE).read_text(encoding="utf-8"))
        print(f"  {d.name:<55} state={data.get('state')!s:<15} records={sorted(data.get('records', {}))}")


def _forbid_login_fill() -> None:
    """--dry-run: the wrapper layer's session guard (BasePage -> session_guard
    .reauthenticate) would otherwise TYPE TEST_USER's credentials if the
    session dropped mid-read. Replace it, for this process only, with a check
    that refuses instead -- a dry-run never fills a form."""
    from core.web import base_page, session_guard

    def _refuse(page, target_url=None, max_attempts=3):  # noqa: ARG001 -- same signature
        if session_guard.is_login_form_showing(page) or session_guard.is_dead_session(page):
            raise RuntimeError(
                "--dry-run: the CMS session is signed out (or behind the license / login gate) "
                f"at {page.url}; refusing to fill the login form. Run python tools/save_auth.py, "
                "then retry.")
        return False

    base_page.reauthenticate = _refuse


def _is_timeout(exc: BaseException | None) -> bool:
    """A Playwright TimeoutError, a core.utils.waits.WaitTimeoutError, or an
    error raised FROM one (drive_to_published wraps its wait in an
    AssertionError) -- walked through __cause__ / __context__."""
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        if type(exc).__name__ in ("TimeoutError", "WaitTimeoutError") or "budget spent" in str(exc):
            return True
        exc = exc.__cause__ or exc.__context__
    return False


class _TimeoutScreenshot:
    """`SingletonBaseline.on_step_error` hook for --debug-screenshot: on a
    timed-out step, save the page as it is right now and print its URL."""

    def __init__(self, target: str, pbi: str):
        path = Path(target)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if path.suffix.lower() != ".png":  # a directory
            stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            path = path / f"restore_{pbi}_{stamp}.png"
        self.base = path
        self.saved: list[Path] = []

    def _next_path(self) -> Path:
        if not self.saved:
            return self.base
        return self.base.with_name(f"{self.base.stem}-{len(self.saved) + 1}{self.base.suffix}")

    def __call__(self, page, exc: BaseException, step: str) -> None:
        if not _is_timeout(exc):
            return
        url = getattr(page, "url", "?")
        target = self._next_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            page.screenshot(path=str(target), timeout=15000)
            self.saved.append(target)
            print(f"[debug-screenshot] {step}: {type(exc).__name__} at {url}\n"
                  f"[debug-screenshot] saved {target}", file=sys.stderr)
        except Exception as shot_exc:  # noqa: BLE001 -- page/context may be gone
            print(f"[debug-screenshot] {step}: {type(exc).__name__} at {url} "
                  f"(screenshot failed: {shot_exc!r})", file=sys.stderr)


def _resolve_snapshot(baseline, given: str | None) -> Path:
    if given:
        path = Path(given)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if not (path / sb.SNAPSHOT_FILE).exists():
            sys.exit(f"no {sb.SNAPSHOT_FILE} in {path}")
        return path
    latest = baseline.latest_unrestored()
    if latest is None:
        sys.exit(f"PBI {baseline.pbi}: no unrestored snapshot -- nothing to do "
                 "(pass --snapshot <dir> to restore from a specific one)")
    return latest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pbi", help=f"registered PBI: {', '.join(sorted(sb.REGISTRY))}")
    parser.add_argument("--snapshot", help="snapshot directory (default: latest unrestored for --pbi)")
    parser.add_argument("--list", action="store_true", help="list snapshots and their state (offline)")
    parser.add_argument("--dry-run", action="store_true", help="print the live diff only; write nothing")
    parser.add_argument("--headed", action="store_true", help="show the browser")
    parser.add_argument("--i-understand-this-writes-live", dest="writes_live", action="store_true",
                        help="required for any run that may WRITE to the live record "
                             "(user decision 2026-10-13); not needed for --list / --dry-run")
    parser.add_argument("--debug-screenshot", metavar="PATH",
                        help="on a step timeout, save a screenshot (PATH = .png file or directory) "
                             "and print the page URL")
    args = parser.parse_args()

    if args.list:
        for pbi in ([args.pbi] if args.pbi else sorted(sb.REGISTRY)):
            _print_snapshots(pbi)
        return 0
    if not args.pbi:
        parser.error("--pbi is required (or use --list)")
    if not args.dry_run and not args.writes_live:
        print("REFUSED: this restore WRITES to a live singleton record on qcdev, and automation no "
              "longer writes to real singletons (user decision 2026-10-13). Use --dry-run to see the "
              "diff, or add --i-understand-this-writes-live to write anyway.", file=sys.stderr)
        return 2

    baseline = sb.load(args.pbi)
    baseline.read_only = args.dry_run
    shooter = _TimeoutScreenshot(args.debug_screenshot, args.pbi) if args.debug_screenshot else None
    baseline.on_step_error = shooter
    if args.dry_run:
        _forbid_login_fill()
    snapshot = _resolve_snapshot(baseline, args.snapshot)
    print(f"PBI {args.pbi}: {'DRY RUN (read-only) against' if args.dry_run else 'restoring from'} {snapshot}")

    from playwright.sync_api import sync_playwright

    from core.web.browser import launch_browser, new_context

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False) if args.headed else launch_browser(pw)
        context = new_context(browser)
        page = context.new_page()
        try:
            diff = baseline.current_diff(page, snapshot)
            print("live diff vs snapshot:")
            print(json.dumps(diff, ensure_ascii=False, indent=1))
            if args.dry_run:
                print("--dry-run: nothing written")
                return 0
            if not any(diff.values()):
                baseline.mark(snapshot, sb.STATE_RESTORED, reason="CLI: record already matched")
                print("record(s) already match the snapshot -- marked restored")
                return 0
            baseline.restore(page, snapshot, reason="CLI tools/restore_singleton.py")
            print("restored and verified by fresh re-read -- snapshot marked restored")
            return 0
        except Exception as exc:  # noqa: BLE001 -- incl. Playwright TimeoutError from the diff read
            if shooter is not None:
                shooter(page, exc, "CLI")  # no-op unless it is a timeout
            print(f"{type(exc).__name__}: {exc}\n(page was at {page.url})", file=sys.stderr)
            return 1
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    sys.exit(main())

"""
tools/restore_chamber_laws_page.py -- restore the live Chamber Laws Page
singleton (QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY, PBI 129394) AND its hero
row (AboutHeroBanner QCDEMO-ABOUT-HERO-chamber-laws) from their backups, and
verify both by a fresh re-read.

    python tools/restore_chamber_laws_page.py           # restore + verify
    python tools/restore_chamber_laws_page.py --check   # compare only, no writes

Use it when a test run was killed before the module-end restore fixture in
cms/tests/chambers_law/test_chambers_law_control_panel.py could fire. Source
of truth: reports/backups/chamber_laws_page_20261012/snapshot.json +
content_image.png, and reports/backups/chamber_laws_hero_20261012/ (written
by the test module before its first hero write; when it does not exist the
hero row was never written and is skipped). Signs in with the saved TEST_USER session
(.auth/state.json; re-authenticates if it has expired).

Exit codes: 0 = record matches the backup; 1 = differences remain;
2 = refused (a writing run without --i-understand-this-writes-live).

WRITE GATE (user decision 2026-10-13)
-------------------------------------
Automation no longer writes to real singleton records, and the test modules
no longer wire the snapshot/restore engine. A restore is itself a live write,
so the writing path now REFUSES unless it is asked for explicitly:

    python tools/restore_chamber_laws_page.py  --i-understand-this-writes-live

Read-only paths (--check) need no flag.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright  # noqa: E402

from cms.pages.chambers_law.chambers_law_admin_page import ChambersLawAdminPage  # noqa: E402
from cms.pages.chambers_law.page_record_backup import (  # noqa: E402
    hero_diff,
    hero_snapshot_exists,
    hero_snapshot_state,
    read_hero_state,
    restore_hero_with_retries,
    read_page_state,
    restore_with_retries,
    snapshot_state,
    state_diff,
)
from core.web.browser import launch_browser, new_context  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="compare only, write nothing")
    parser.add_argument("--i-understand-this-writes-live", dest="writes_live", action="store_true",
                        help="required for a run that may WRITE to the live records (user decision 2026-10-13)")
    args = parser.parse_args()
    if not args.check and not args.writes_live:
        print("REFUSED: this restore WRITES to live singleton records on qcdev, and automation no "
              "longer writes to real singletons (user decision 2026-10-13). Use --check to compare, "
              "or add --i-understand-this-writes-live to write anyway.", file=sys.stderr)
        return 2

    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        context = new_context(browser)
        try:
            admin = ChambersLawAdminPage(context.new_page())

            def _diff() -> list:
                diff = state_diff(read_page_state(admin), snapshot_state())
                if hero_snapshot_exists():
                    diff += hero_diff(read_hero_state(admin), hero_snapshot_state())
                return diff

            diff = _diff()
            if not hero_snapshot_exists():
                print("(no hero snapshot on disk -- the hero row was never written; skipped)")
            if not diff:
                print("OK: the Chamber Laws Page record (and hero row) match the backup.")
                return 0
            print("Differences from the backup: " + " | ".join(diff))
            if args.check:
                return 1
            errors = restore_with_retries(admin) + restore_hero_with_retries(admin)
            if errors:
                print("RESTORE FAILED: " + " | ".join(errors))
                return 1
            diff = _diff()
            if diff:
                print("Still different after restore: " + " | ".join(diff))
                return 1
            print("RESTORED: the record (and hero row) now match the backup (verified by re-read).")
            return 0
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    sys.exit(main())

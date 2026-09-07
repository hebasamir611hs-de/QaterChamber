#!/usr/bin/env python3
"""
tools/clear_reports.py — delete the generated report artifacts under reports/.

    python tools/clear_reports.py              # everything (results, report, evidence)
    python tools/clear_reports.py --results    # allure-results only
    python tools/clear_reports.py --report     # allure-report only
    python tools/clear_reports.py --evidence   # screenshots/videos/traces only
    python tools/clear_reports.py --dry-run    # show what would go, delete nothing

Stdlib only — runnable before `pip install -r requirements.txt`. Deletes
strictly inside the reports directory; a REPORTS_DIR pointing elsewhere is
refused rather than followed.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

TARGETS = {
    "results": ["allure-results"],
    "report": ["allure-report"],
    "evidence": ["screenshots", "videos", "traces"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear generated report artifacts.")
    parser.add_argument("--results", action="store_true", help="allure-results only")
    parser.add_argument("--report", action="store_true", help="allure-report only")
    parser.add_argument("--evidence", action="store_true", help="screenshots/videos/traces only")
    parser.add_argument("--dry-run", action="store_true", help="list targets, delete nothing")
    parser.add_argument(
        "--reports-dir",
        default=os.getenv("REPORTS_DIR", "reports"),
        help="reports root (default: $REPORTS_DIR or ./reports)",
    )
    args = parser.parse_args()

    project_root = Path.cwd().resolve()
    reports_root = Path(args.reports_dir).resolve()
    # Guard: only ever delete inside the project. A REPORTS_DIR of '/' or
    # '../..' would otherwise hand rmtree the whole tree.
    if reports_root == project_root or project_root not in reports_root.parents:
        print(f"refusing to clear '{reports_root}' — it is not a folder inside {project_root}", file=sys.stderr)
        return 2

    selected = [k for k in ("results", "report", "evidence") if getattr(args, k)] or list(TARGETS)
    names = [name for key in selected for name in TARGETS[key]]

    if not reports_root.exists():
        print(f"nothing to do — {reports_root} does not exist")
        return 0

    removed, missing = [], []
    for name in names:
        path = reports_root / name
        if not path.exists():
            missing.append(name)
            continue
        if args.dry_run:
            removed.append(name)
            continue
        shutil.rmtree(path, ignore_errors=True)
        removed.append(name)

    verb = "would remove" if args.dry_run else "removed"
    print(f"{verb}: {', '.join(removed) if removed else '(nothing)'}")
    if missing:
        print(f"absent already: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

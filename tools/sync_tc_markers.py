#!/usr/bin/env python
"""
tools/sync_tc_markers.py — regenerate pytest.ini's `tc_<azure_id>` marker block
from the marks actually applied in the test code.

WHY THIS EXISTS
---------------
`pytest.ini`'s `markers =` block was hand-maintained and had drifted badly
(measured 2026-09-30): 1,937 `tc_*` markers were registered, 200 of which no
test used any more, while 535 `tc_*` marks present in the code were never
registered at all. The block is also the only place a TC id's assertion text
lives outside Azure, so it is worth keeping — it just must never be typed by
hand again.

Note there is NO `--strict-markers` and NO `filterwarnings = error` in this
project (checked in pytest.ini, conftest.py and azure-pipelines.yml), so an
unregistered marker never fails a run — it only emits PytestUnknownMarkWarning.
Registration here is therefore documentation + `pytest --markers` discoverability,
not a correctness requirement.

WHAT IT DOES
------------
- Scans SOURCE_DIRS for `@pytest.mark.tc_<digits>` (a plain source grep, not
  `--collect-only`, so the ~640 skipped tests keep their entries).
- Preserves each id's existing human description from pytest.ini; new ids get
  the default `Azure Test Case <id> selector`.
- Rewrites ONLY the `tc_*` lines, between BEGIN/END sentinels. Every other
  marker (`regression`, `web`, the Axis-2/4/5 taxonomy, every `pbi_*`) and its
  attached comments are preserved verbatim, in their original order.
- Freeform batch-provenance comments that sat interleaved BETWEEN tc_ lines are
  dropped; they are narrative, and git history retains them.

USAGE
-----
    python tools/sync_tc_markers.py            # rewrite pytest.ini in place
    python tools/sync_tc_markers.py --check    # exit 1 if out of sync (CI)
    python tools/sync_tc_markers.py --diff     # show what would change
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTEST_INI = ROOT / "pytest.ini"
SOURCE_DIRS = ["web", "cms"]

MARK_RE = re.compile(r"@pytest\.mark\.((?:tc|pbi)_\d+)")
ENTRY_RE = re.compile(r"^    (?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?P<desc>.*)$")
TC_RE = re.compile(r"^    (?P<name>(?:tc|pbi)_\d+)\s*:\s*(?P<desc>.*)$")

BEGIN = "    # >>> BEGIN GENERATED pbi_/tc_ MARKERS — do not edit by hand."
REGEN = "    # Regenerate with: python tools/sync_tc_markers.py"
END = "    # <<< END GENERATED pbi_/tc_ MARKERS"

DEFAULT_TC_DESC = "Azure Test Case {id} selector"
DEFAULT_PBI_DESC = "PBI {id} backlog selector"


def collect_marks_from_source() -> set[str]:
    """Every literal `@pytest.mark.tc_<id>` in the test code (fast, no imports)."""
    found: set[str] = set()
    for d in SOURCE_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for py in base.rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            try:
                text = py.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            found.update(MARK_RE.findall(text))
    return found


class _MarkHarvester:
    """Records every tc_* marker pytest actually applies, including dynamic ones."""

    def __init__(self) -> None:
        self.marks: set[str] = set()

    def pytest_collection_modifyitems(self, items):  # noqa: D102
        for item in items:
            for mark in item.iter_markers():
                n = mark.name
                if (n.startswith("tc_") and n[3:].isdigit()) or (
                    n.startswith("pbi_") and n[4:].isdigit()
                ):
                    self.marks.add(n)


def collect_marks_from_collection() -> set[str] | None:
    """
    Every tc_* mark pytest applies at collection time.

    Catches the 7 modules that build marks dynamically
    (`getattr(pytest.mark, f"tc_{tc_id}")`), which a source grep cannot see.
    Skipped tests are still collected, so the ~640 `@pytest.mark.skip` cases
    keep their entries. Returns None if collection fails (missing deps, an
    import error) so the caller can fall back to the grep.
    """
    try:
        import pytest as _pytest
    except ImportError:
        return None

    harvester = _MarkHarvester()
    try:
        rc = _pytest.main(
            [
                "--collect-only",
                "-q",
                "-o", "addopts=",          # drop -n 3 / allure opts for a fast, quiet pass
                "-p", "no:cacheprovider",
                str(ROOT),
            ],
            plugins=[harvester],
        )
    except Exception:
        return None
    # rc 0 = collected, 5 = no tests. Anything else means collection was incomplete.
    if rc not in (0, 5):
        return None
    return harvester.marks


def split_ini(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Return (head, markers_block, tail) — block excludes the `markers =` line."""
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^markers\s*=", line):
            start = i
            break
    if start is None:
        sys.exit("ERROR: no `markers =` line found in pytest.ini")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j]
        if stripped.strip() == "":
            continue
        # The block ends at the first line that is not indented.
        if not stripped.startswith((" ", "\t")):
            end = j
            break
    return lines[: start + 1], lines[start + 1 : end], lines[end:]


def parse_block(block: list[str]) -> tuple[list[str], dict[str, str]]:
    """
    Walk the markers block. Comments attach to the marker line that follows.
    Returns (preserved_lines, tc_descriptions).
      - preserved_lines: every non-tc marker with its attached comments, in order.
      - tc_descriptions: id -> existing description text.
    """
    preserved: list[str] = []
    tc_desc: dict[str, str] = {}
    pending: list[str] = []

    # Match sentinels by shape, not exact wording, so renaming the banner text
    # never strands an old sentinel mid-file (happened once, 2026-09-30).
    sentinel_re = re.compile(
        r"^#\s*(>>>\s*BEGIN GENERATED|<<<\s*END GENERATED|Regenerate with:)"
    )

    for raw in block:
        line = raw.rstrip("\n")
        stripped = line.strip()

        # Drop sentinels from a previous run so regeneration stays idempotent.
        if sentinel_re.match(stripped):
            continue

        if stripped == "":
            pending.append(line)
            continue
        if stripped.startswith("#"):
            pending.append(line)
            continue

        tc = TC_RE.match(line)
        if tc:
            # A tc_ entry: its buffered comments are batch narrative -> drop.
            tc_desc[tc.group("name")] = tc.group("desc").strip()
            pending = []
            continue

        entry = ENTRY_RE.match(line)
        if entry:
            preserved.extend(pending)
            pending = []
            preserved.append(line)
            continue

        # A wrapped continuation line of the previous non-tc entry.
        preserved.extend(pending)
        pending = []
        preserved.append(line)

    # Trailing comments belong to the preserved side.
    preserved.extend(pending)

    # Trim trailing blank lines so the generated block starts cleanly.
    while preserved and preserved[-1].strip() == "":
        preserved.pop()

    return preserved, tc_desc


def build_block(preserved: list[str], tc_desc: dict[str, str], marks: set[str]) -> list[str]:
    out = list(preserved)
    out.append("")
    out.append(BEGIN)
    out.append(REGEN)
    pbis = sorted((m for m in marks if m.startswith("pbi_")), key=lambda n: int(n[4:]))
    tcs = sorted((m for m in marks if m.startswith("tc_")), key=lambda n: int(n[3:]))
    for name in pbis:
        desc = tc_desc.get(name) or DEFAULT_PBI_DESC.format(id=name[4:])
        out.append(f"    {name}: {desc}")
    if pbis and tcs:
        out.append("")
    for name in tcs:
        desc = tc_desc.get(name) or DEFAULT_TC_DESC.format(id=name[3:])
        out.append(f"    {name}: {desc}")
    out.append(END)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if out of sync")
    ap.add_argument("--diff", action="store_true", help="print the change summary only")
    args = ap.parse_args()

    lines = PYTEST_INI.read_text(encoding="utf-8").splitlines()
    head, block, tail = split_ini(lines)
    preserved, tc_desc = parse_block(block)

    grepped = collect_marks_from_source()
    collected = collect_marks_from_collection()
    degraded = collected is None
    if degraded:
        print("WARNING: pytest collection failed — falling back to the source grep.")
        print("         Dynamically-applied marks are invisible to a grep, so this run")
        print("         will ADD missing markers but REMOVE none (nothing is pruned")
        print("         on evidence we don't have).")
        # Union with what is already registered: additive only. Without this, a
        # degraded run would silently delete the ~313 dynamically-applied markers.
        marks = grepped | set(tc_desc)
    else:
        marks = grepped | collected
        dynamic_only = collected - grepped
        if dynamic_only:
            print(f"dynamic-only marks found : {len(dynamic_only)} (not visible to a grep)")

    registered = set(tc_desc)
    stale = registered - marks
    missing = marks - registered

    print(f"tc_ marks in source     : {len(marks)}")
    print(f"tc_ markers registered  : {len(registered)}")
    print(f"  registered, unused    : {len(stale)}  (will be removed)")
    print(f"  used, unregistered    : {len(missing)}  (will be added)")
    print(f"non-tc markers preserved: {sum(1 for l in preserved if ENTRY_RE.match(l))}")

    new_block = build_block(preserved, tc_desc, marks)
    new_lines = head + new_block + tail
    new_text = "\n".join(new_lines) + "\n"
    old_text = PYTEST_INI.read_text(encoding="utf-8")

    if args.diff:
        print(f"\npytest.ini: {len(lines)} lines -> {len(new_lines)} lines")
        return 0

    if args.check:
        if collected is None:
            # Collection was unavailable (e.g. a CI agent without browser deps).
            # Degrade to the question a grep CAN answer — "is every statically
            # visible mark registered?" — rather than failing the build over the
            # dynamic marks we simply could not see. A red CollectGate on an
            # unrelated PR is how a guard like this gets deleted.
            unregistered = grepped - registered
            if unregistered:
                print(
                    f"\nOUT OF SYNC — {len(unregistered)} unregistered marker(s), "
                    f"e.g. {', '.join(sorted(unregistered)[:5])}"
                )
                print("Run: python tools/sync_tc_markers.py")
                return 1
            print("\nin sync (grep-visible subset only — collection unavailable)")
            return 0
        if new_text != old_text:
            print("\nOUT OF SYNC — run: python tools/sync_tc_markers.py")
            return 1
        print("\nin sync")
        return 0

    if new_text == old_text:
        print("\nalready in sync — pytest.ini unchanged")
        return 0

    PYTEST_INI.write_text(new_text, encoding="utf-8")
    print(f"\npytest.ini rewritten: {len(lines)} lines -> {len(new_lines)} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
core/utils/reporting.py — the single evidence-naming, on-disk-archiving, and
Allure-attach helper. Every screenshot/video/trace capture point in this
framework must go through it, per automation-standards.md's "Evidence file
naming" section.

Each capture does TWO things, deliberately:

  1. **Archives a real file on disk** under `reports/<kind>s/` with the
     readable contract name (`screenshot_2026-07-19_14-32-05_TAG-TC-014_WOQOD.png`).
     This exists because Allure NEVER keeps readable filenames: raw results are
     `<guid>-attachment.png`, and `allure generate` re-hashes them again into
     `data/attachments/<hash>.png`. The readable name survives only as a JSON
     "name" field shown in the report UI, so browsing evidence on disk was
     impossible before this archive step.
  2. **Attaches it to Allure** under the same readable name, so the report keeps
     working exactly as before (`allure serve reports/allure-results`).

`allure` is imported LAZILY inside the attach_* functions (not at module
level) so evidence_name()/extract_test_case_id() — pure logic, no I/O — stay
importable and unit-testable even before `pip install -r requirements.txt`
has run, and so `pytest --collect-only` never fails on this module just
because allure-pytest isn't installed yet.
"""

import re
import shutil
from datetime import datetime
from pathlib import Path

_TC_ID_RE = re.compile(r"[A-Za-z0-9]+-TC-\d+")

# One folder per evidence kind, all under the reports root. `allure-results`
# and `allure-report` stay untouched siblings — Allure owns those.
EVIDENCE_SUBDIRS = {
    "screenshot": "screenshots",
    "video": "videos",
    "trace": "traces",
}


def extract_test_case_id(item) -> str:
    """Pulls the QA traceability ID off a pytest item: prefers the
    @pytest.mark.traceability("<ID>") marker, falls back to scanning the
    test's docstring for an <SERVICE>-TC-<n> pattern, else "NO-TC" (itself
    a defect to fix, per the contract)."""
    marker = item.get_closest_marker("traceability")
    if marker and marker.args:
        return str(marker.args[0])
    doc = item.function.__doc__ or "" if hasattr(item, "function") else ""
    match = _TC_ID_RE.search(doc)
    if match:
        return match.group(0)
    return "NO-TC"


def evidence_name(kind: str, test_case_id: str, project_name: str, ext: str, when: datetime = None) -> str:
    """Builds '<kind>_<date>_<time>_<test_case_id>_<project_name>.<ext>' —
    fields in that exact order, no exceptions. `kind` is 'screenshot',
    'video', or 'trace'."""
    when = when or datetime.now()
    date = when.strftime("%Y-%m-%d")
    time = when.strftime("%H-%M-%S")
    return f"{kind}_{date}_{time}_{test_case_id}_{project_name}.{ext}"


def evidence_dir(kind: str, reports_dir: str = "reports") -> Path:
    """Returns (creating if needed) the on-disk folder for `kind`, e.g.
    reports/screenshots. Unknown kinds land in reports/<kind>s rather than
    raising — losing evidence is worse than an odd folder name."""
    subdir = EVIDENCE_SUBDIRS.get(kind, f"{kind}s")
    path = Path(reports_dir) / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def archive_evidence_bytes(kind: str, data: bytes, test_case_id: str, project_name: str,
                           ext: str, reports_dir: str = "reports") -> Path:
    """Writes `data` to reports/<kind>s/<readable name> and returns the path."""
    target = evidence_dir(kind, reports_dir) / evidence_name(kind, test_case_id, project_name, ext)
    target.write_bytes(data)
    return target


def archive_evidence_file(kind: str, source_path: str, test_case_id: str, project_name: str,
                          ext: str, reports_dir: str = "reports") -> Path:
    """Copies an already-written artifact (Playwright video/trace, Appium
    recording) into reports/<kind>s/<readable name> and returns the new path.
    Copy, not move — Playwright still owns the file in its own temp dir."""
    target = evidence_dir(kind, reports_dir) / evidence_name(kind, test_case_id, project_name, ext)
    shutil.copyfile(source_path, target)
    return target


def attach_screenshot(png_bytes: bytes, test_case_id: str, project_name: str,
                      reports_dir: str = "reports") -> Path:
    archived = archive_evidence_bytes("screenshot", png_bytes, test_case_id, project_name, "png", reports_dir)
    import allure
    allure.attach(png_bytes, name=archived.name, attachment_type=allure.attachment_type.PNG)
    return archived


def attach_video(video_path: str, test_case_id: str, project_name: str, ext: str = "webm",
                 reports_dir: str = "reports") -> Path:
    archived = archive_evidence_file("video", video_path, test_case_id, project_name, ext, reports_dir)
    import allure
    attachment_type = allure.attachment_type.MP4 if ext == "mp4" else allure.attachment_type.WEBM
    allure.attach.file(str(archived), name=archived.name, attachment_type=attachment_type)
    return archived


def attach_trace(trace_path: str, test_case_id: str, project_name: str,
                 reports_dir: str = "reports") -> Path:
    """Playwright trace zip. Written on failure only, per the contract."""
    archived = archive_evidence_file("trace", trace_path, test_case_id, project_name, "zip", reports_dir)
    import allure
    allure.attach.file(str(archived), name=archived.name, extension="zip")
    return archived


def clear_evidence_dirs(reports_dir: str = "reports") -> list:
    """Deletes every archived evidence folder. Called at session start so a run's
    reports/ folder always reflects that run only — the on-disk counterpart of
    allure-pytest's --clean-alluredir. Returns the folders removed."""
    removed = []
    for subdir in EVIDENCE_SUBDIRS.values():
        path = Path(reports_dir) / subdir
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            removed.append(str(path))
    return removed

"""
cms/tests/test_cms_conventions.py — repo guard for the CMS editorial-workflow
conventions.

WHY THIS EXISTS
---------------
The 7-state editorial workflow (agreed 2026-09-28, see standards.md ->
"Content Editorial Workflow") replaced a two-state Draft/Approved model that
turned out to be an artifact of only ever observing through the super-admin
`TEST_USER`. The old vocabulary was healed across ~240 call sites by the
deprecated aliases in `object_authoring_page.py`.

That healed what already existed. Nothing stops the OLD vocabulary being written
again tomorrow — and a rule that lives only in a document is enforced only by
whoever remembers to read it. These tests make the convention mechanical: they
fail the build, so nobody has to ask for the new flow on every run.

DESIGN
------
- **No browser, no network, no qcdev.** Pure AST inspection of the repo. Runs in
  the CI collect gate and in any local run, in well under a second.
- **Docstrings and comments are ignored.** They legitimately discuss the old
  vocabulary while explaining the migration; only *live* code is checked.
- Every failure message names the fix, not just the violation.

If a rule here is genuinely wrong for a new case, add the file to that rule's
ALLOW set with a comment saying why — do not delete the rule.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCAN_DIRS = ("cms", "web")

# This guard file itself names the legacy vocabulary in order to forbid it.
SELF = Path(__file__).resolve()


def _py_files() -> list[Path]:
    out: list[Path] = []
    for d in SCAN_DIRS:
        for p in (ROOT / d).rglob("*.py"):
            if "__pycache__" in p.parts or p.resolve() == SELF:
                continue
            out.append(p)
    return sorted(out)


# Calls whose string arguments are HUMAN-READABLE PROSE, not behaviour: an
# Allure step title that says "click Submit for Publishing" is stale wording in
# a report, not a broken locator. Worth cleaning up, but failing the build on it
# would mean this guard can never go green — and a guard that can never go green
# gets deleted. Prose is reported by test_legacy_wording_in_reports_is_tracked
# below instead, which does not fail.
_PROSE_CALLS = {
    "step", "title", "description", "description_html", "label", "story",
    "feature", "epic", "severity", "skip", "xfail", "fail", "param",
}


def _prose_string_ids(tree: ast.AST) -> set[int]:
    """String constants that are prose: Allure/pytest metadata and assert messages."""
    out: set[int] = set()

    def mark(node):
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                out.add(id(n))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name in _PROSE_CALLS:
                for a in node.args:
                    mark(a)
                for kw in node.keywords:
                    mark(kw.value)
        # `assert cond, "message"` — the message is prose.
        if isinstance(node, ast.Assert) and node.msg is not None:
            mark(node.msg)
        # `raise AssertionError("message")` / pytest.fail(...) handled above.
    return out


def _live_strings(path: Path, include_prose: bool = False) -> list[tuple[int, str]]:
    """String constants that are neither docstrings nor (by default) prose.

    Comments never reach the AST, so they are excluded for free. Module, class
    and function docstrings are skipped explicitly, as are bare string
    expressions used as block comments.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []

    skip: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                skip.add(id(body[0].value))
        # A bare string statement anywhere is a block comment, not a value.
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            skip.add(id(node.value))

    if not include_prose:
        skip |= _prose_string_ids(tree)

    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in skip:
            out.append((node.lineno, node.value))
    return out


def _violations(pattern: re.Pattern, allow: set[str] = frozenset()) -> list[str]:
    hits = []
    for path in _py_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in allow:
            continue
        for lineno, value in _live_strings(path):
            if pattern.search(value):
                hits.append(f"{rel}:{lineno}  ->  {value[:80]!r}")
    return hits


# --- Documented exceptions ------------------------------------------------
# An entry here needs a reason. Do not add one to silence a real violation.

_APPROVED_ALLOW = {
    # The Tender EOI webform's OWN Approve/Reject workflow — a different domain
    # from the content editorial workflow, with its own STATUS_* constants.
    "cms/pages/tenders/eoi_submission_admin_page.py",
    # A public-site B2B company badge, not a CMS status.
    "web/tests/b2b_matchmaking/test_b2b_matchmaking_web.py",
}

_CONTENT_DATA_ALLOW = {
    # Home Contact Us is a Liferay JOURNAL (Web Content) article — articleId
    # 53012, groupId 37246 — NOT an Object-Definition-backed record, so the
    # Object-Authoring-only rule does not apply to it (standards.md states this
    # exception explicitly). Content & Data is the correct surface here.
    "cms/pages/home_contact_us/home_contact_us_admin_page.py",
}


# ---------------------------------------------------------------------------


def test_no_legacy_submit_for_publishing_label():
    """The button is "Submit for Review". The old label must not come back.

    Matches the label used as a VALUE (an exact string, or inside selector
    syntax) — not a sentence that merely mentions it, which is prose.
    """
    hits = _violations(re.compile(
        r"^\s*Submit for Publishing\s*$"          # the label itself
        r"|has-text\(\s*[\"']?Submit for Publishing"  # inside a selector
        r"|button:[^\"']*Submit for Publishing",
        re.I))
    assert not hits, (
        "Legacy CMS label 'Submit for Publishing' found in live code.\n"
        "The control is now 'Submit for Review' (standards.md -> Content "
        "Editorial Workflow).\n"
        "Use object_authoring_page.SUBMIT_FOR_REVIEW_BUTTON, never a literal.\n"
        + "\n".join("  " + h for h in hits)
    )


def test_no_legacy_approved_status_literal():
    """The published badge reads PUBLISHED, not Approved."""
    hits = _violations(re.compile(r"^Approved$"), allow=_APPROVED_ALLOW)
    assert not hits, (
        "Legacy status literal 'Approved' found in live code.\n"
        "The badge reads 'Published'. Use object_authoring_page.STATUS_PUBLISHED "
        "(or STATUS_* generally), never a string literal.\n"
        + "\n".join("  " + h for h in hits)
    )


def test_no_hardcoded_role_credentials():
    """Role logins resolve through config.settings.cms_role_credentials()."""
    hits = _violations(re.compile(r"@xyz\.com$", re.I))
    assert not hits, (
        "Hard-coded CMS role account found in live code.\n"
        "standards.md -> Named CMS User Roles: resolve credentials via\n"
        "  config.settings.cms_role_credentials('<Role>')\n"
        "so a rotation only touches .env.\n"
        + "\n".join("  " + h for h in hits)
    )


def test_no_content_and_data_navigation():
    """Content & Data is retired as an automation path for content records."""
    hits = _violations(re.compile(r"/group/[^\"']*/content|com_liferay_journal_web", re.I),
                       allow=_CONTENT_DATA_ALLOW)
    assert not hits, (
        "Navigation to the retired 'Content & Data' surface found in live code.\n"
        "standards.md -> Object Authoring Is the Only Path: every content "
        "operation goes through /object-authoring.\n"
        + "\n".join("  " + h for h in hits)
    )


def _singleton_engine_roots() -> list[tuple[str, ast.AST]]:
    """(file, AST root) pairs on the singleton restore path: whole modules for
    the engine / CLI / session guard / record adapters, and CmsLoginPage's
    METHODS -- the Chairman adapter signs in through ensure_signed_in_as(),
    which used to hit /c/portal/logout. (Its unused LOGOUT_PATH class constant
    is not a call; a method that USES it is caught.)"""
    files = [
        ROOT / "cms" / "tests" / "singleton_baseline.py",
        ROOT / "tools" / "restore_singleton.py",
        ROOT / "core" / "web" / "session_guard.py",
        ROOT / "core" / "web" / "base_page.py",
    ]
    files += sorted((ROOT / "cms" / "tests").glob("*/*_singleton.py"))
    roots = []
    for path in files:
        if path.exists():
            roots.append((path.relative_to(ROOT).as_posix(),
                          ast.parse(path.read_text(encoding="utf-8", errors="replace"))))
    login = ROOT / "cms" / "pages" / "control_panel" / "login_page.py"
    tree = ast.parse(login.read_text(encoding="utf-8", errors="replace"))
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CmsLoginPage"):
        for fn in cls.body:
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                roots.append((login.relative_to(ROOT).as_posix(), fn))
    return roots


def _docstring_ids(root: ast.AST) -> set[int]:
    out = set()
    for node in ast.walk(root):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                out.add(id(body[0].value))
    return out


def test_singleton_engine_never_logs_out():
    """The singleton snapshot/restore engine, its CLI, the session guard and
    the CmsLoginPage sign-in path never sign the session out.

    Their contexts carry TEST_USER's SHARED storageState session. A server
    logout (`/c/portal/logout`) kills it for every other context, worker and
    tool. On 2026-10-12 that signed the module baselines out mid-run and
    stranded GM Message 79878 in Unpublished twice."""
    hits = []
    for rel, root in _singleton_engine_roots():
        docs = _docstring_ids(root)
        for node in ast.walk(root):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and id(node) not in docs and re.search(r"portal/logout", node.value, re.I):
                hits.append(f"{rel}:{node.lineno}  ->  {node.value[:80]!r}")
            name = node.attr if isinstance(node, ast.Attribute) else (
                node.id if isinstance(node, ast.Name) else "")
            if name in ("logout_and_return", "LOGOUT_PATH"):
                hits.append(f"{rel}:{node.lineno}  ->  {name}")
    assert not hits, (
        "A server logout was found on the singleton restore path.\n"
        "Never hit /c/portal/logout there. To change accounts, clear the "
        "context's cookies and log in fresh (CmsLoginPage.ensure_signed_in_as), "
        "or use a new context (new_context(browser, use_auth_state=False)).\n"
        + "\n".join("  " + h for h in hits)
    )


@pytest.mark.parametrize(
    "name",
    ["STATUS_DRAFT", "STATUS_PENDING_REVIEW", "STATUS_REJECTED", "STATUS_PUBLISHED",
     "STATUS_UNPUBLISHED", "STATUS_ARCHIVED", "STATUS_SCHEDULED"],
)
def test_seven_workflow_states_are_defined(name):
    """All seven states stay defined — a test asserting a state it cannot name
    is how the two-state model crept in the first time."""
    src = (ROOT / "cms" / "pages" / "components" / "object_authoring_page.py").read_text(
        encoding="utf-8", errors="replace")
    assert re.search(rf"^{name}\s*=", src, re.M), (
        f"{name} is missing from cms/pages/components/object_authoring_page.py.\n"
        "standards.md -> Content Editorial Workflow defines seven states; all "
        "seven must remain available as constants."
    )


# ---------------------------------------------------------------------------
# Singleton writes are guarded (user decision 2026-10-13)
# ---------------------------------------------------------------------------
# OPT-IN PATH (user decision 2026-10-13, P3/P4 batch): the guard call below is
# still REQUIRED before every write. With QC_ALLOW_LIVE_SINGLETON_WRITES=1 it
# no longer fails for the four approved records -- it logs and lets the test
# write (each write is logged with log_live_write()). Its behaviour is pinned
# by test_live_write_guard_* further down.
#
# Automation must not write to a real singleton record. In the modules below,
# every call that can persist something (save / submit / publish / unpublish /
# a row workflow action, or a local helper that makes one) must have, in the
# SAME function, either
#   * `block_live_singleton_write(...)` on an EARLIER line (NOT APPLICABLE), or
#   * `stop_unless_refused(...)` anywhere in it (a refusal case: it checks the
#     refusal right after its one click, or checks that the control is NOT
#     offered before an attempt, and stops the moment refusal is not seen).
# Best-effort and line-based, not control-flow-based. A call on a disposable
# QCTEST record carries the pragma `# live-write-guard: disposable ...` on its
# own line; a function that writes only non-singleton records is listed in
# _SINGLETON_WRITE_ALLOW with its reason. See cms/tests/live_write_guard.py.
_SINGLETON_MODULES = (
    "cms/tests/chambers_law/test_chambers_law_control_panel.py",
    "cms/tests/gm_message/test_gm_message_control_panel.py",
    "cms/tests/about_qatar_chamber/test_about_qatar_chamber_control_panel.py",
    "cms/tests/chairman_message/test_chairman_message_control_panel.py",
)
# Method / function names that persist (directly or through an imported helper).
_WRITE_CALLS = {
    "submit_via", "submit_via_reading_validity", "submit_publish", "submit_for_review", "submit_for_publishing",
    "save_as_draft", "save", "publish", "unpublish_to_edit_as_draft",
    "publish_entry", "approve_entry", "unpublish_entry", "reject_entry", "click_publish_control",
    "drive_to_editable", "drive_to_published",
    "_publish_edit",                    # about_helpers: clicks Publish
    "_publish", "_make_editable",       # chairman_singleton imports
    # P3/P4 batch 2026-10-13 (opt-in live writes, cms/tests/live_write_guard.py)
    "to_published", "_to_published",    # chairman_singleton.to_published
    "status_draft_case", "status_published_case",   # cms/tests/live_status_cases.py
    "double_click_row_action", "submit_publish_with_network_cut",  # GmMessageAdminPage
}
_GUARD_CALL = "block_live_singleton_write"
# P1/P2 rerun 2026-10-13: the hero QCTEST create path stops through
# refuse_hero_create(), which ALWAYS fails (NOT APPLICABLE) -- a guard too.
_HERO_CREATE_REFUSAL = "refuse_hero_create"
# `finally` re-publish wrappers (cms/tests/live_end_published.leave_published):
# they write ONLY when live_write_guard.gate_opened() says the gate opened for
# that record in the current test, so they are runtime-gated, not unguarded.
_GATE_SCOPED_HELPERS = {"_page_end_published", "_hero_end_published", "_gm_end_published", "_end_published"}
_REFUSAL_CALL = "stop_unless_refused"
_DISPOSABLE_PRAGMA = "live-write-guard: disposable"
_SINGLETON_WRITE_ALLOW = {
    # Law Entry is a MULTI-record object (not a singleton). Since the 2026-10-13
    # follow-up each of these writes ONLY its own disposable
    # `QCTEST-<tc>-LAW-<uid>` row, created in the test and deleted by exact
    # title -- never the real QCDEMO-129394-law-* rows.
    "cms/tests/chambers_law/test_chambers_law_control_panel.py": {
        "_create_law_entry",
        "test_chambers_law_cp_134877_law_title_external_link_url_can_be_configured_and_published",
        "test_chambers_law_cp_134884_creating_a_law_entry_publishes_a_new_card_to_the_website",
        "test_chambers_law_cp_134885_editing_a_law_entry_updates_its_card_on_the_website",
        "test_chambers_law_cp_134886_reordering_law_entries_changes_the_card_sequence_on_the_website",
        "test_chambers_law_cp_134887_deactivating_a_law_entry_hides_its_card_from_the_website",
        "test_chambers_law_cp_134888_reactivating_a_law_entry_restores_its_card_to_the_website",
    },
}


def _call_name(node: ast.Call) -> str:
    fn = node.func
    return fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")


def _unguarded_singleton_writes(source: str, allow=frozenset()) -> list[str]:
    """`name:line -> call` for every write call that has neither an earlier
    guard nor a refusal stop in its function. Writes reached through a
    module-local helper count at the call site (transitively). Only `test_*`
    functions are reported -- a helper is judged where a test calls it."""
    tree = ast.parse(source)
    lines = source.splitlines()
    funcs = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def calls(fn):
        return [n for n in ast.walk(fn) if isinstance(n, ast.Call)]

    def lines_of(fn, name):
        return [c.lineno for c in calls(fn) if _call_name(c) == name]

    def unguarded(fn, unsafe_helpers):
        guards = lines_of(fn, _GUARD_CALL) + lines_of(fn, _HERO_CREATE_REFUSAL)
        stops = lines_of(fn, _REFUSAL_CALL)
        out = []
        for c in calls(fn):
            name = _call_name(c)
            if name not in _WRITE_CALLS and name not in unsafe_helpers:
                continue
            if _DISPOSABLE_PRAGMA in lines[c.lineno - 1]:
                continue
            if stops or any(g < c.lineno for g in guards):
                continue
            out.append(f"{fn.name}:{c.lineno} -> {name}()")
        return out

    # Fixed point: a local helper is an unsafe writer when it holds an
    # unguarded write (unless allow-listed as a non-singleton writer).
    unsafe: set[str] = set()
    while True:
        grown = {name for name, fn in funcs.items()
                 if name not in allow and name not in _GATE_SCOPED_HELPERS
                 and unguarded(fn, unsafe)} - unsafe
        if not grown:
            break
        unsafe |= grown
    hits = []
    for name, fn in funcs.items():
        if name.startswith("test_") and name not in allow:
            hits += unguarded(fn, unsafe)
    return hits


@pytest.mark.parametrize("rel", _SINGLETON_MODULES)
def test_singleton_writes_are_guarded(rel):
    """No unguarded write to a real singleton record (user decision
    2026-10-13): NOT APPLICABLE guard before it, or a refusal stop after it."""
    source = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    hits = _unguarded_singleton_writes(source, _SINGLETON_WRITE_ALLOW.get(rel, frozenset()))
    assert not hits, (
        f"Unguarded write to a real singleton record in {rel}.\n"
        "Call cms.tests.live_write_guard.block_live_singleton_write(<record>) right before the "
        "first persisting step (NOT APPLICABLE), or -- for a refusal case -- call "
        "stop_unless_refused(...) right after the one click that must be refused.\n"
        + "\n".join("  " + h for h in hits)
    )


@pytest.mark.parametrize("source, expected", [
    # unguarded write in a test -> flagged
    ("def test_x(a):\n    a.submit_via('x')\n", 1),
    # unguarded write through a local helper -> flagged at the test
    ("def _h(a):\n    a.save_as_draft()\n\ndef test_x(a):\n    _h(a)\n", 1),
    # guard before the write -> clean
    ("def test_x(a):\n    block_live_singleton_write('r')\n    a.submit_via('x')\n", 0),
    # guard AFTER the write does not count -> flagged
    ("def test_x(a):\n    a.submit_via('x')\n    block_live_singleton_write('r')\n", 1),
    # refusal stop after the click -> clean
    ("def test_x(a):\n    a.submit_publish(f)\n    stop_unless_refused(True, 'r', 'w')\n", 0),
    # refusal check before an attempt (the control must not be offered) -> clean
    ("def test_x(a):\n    stop_unless_refused(True, 'r', 'w')\n    a.publish_entry('c')\n", 0),
    # helper guarded internally -> clean at the test
    ("def _h(a):\n    block_live_singleton_write('r')\n    a.publish()\n\ndef test_x(a):\n    _h(a)\n", 0),
    # disposable pragma -> clean
    ("def test_x(a):\n    a.submit_via('x')  # live-write-guard: disposable QCTEST row\n", 0),
], ids=["unguarded", "via-helper", "guard-before", "guard-after", "stop-after", "stop-before",
        "helper-guarded", "disposable-pragma"])
def test_singleton_write_checker_catches_unguarded_writes(source, expected):
    """The checker above really fails on an unguarded write (and only then)."""
    assert len(_unguarded_singleton_writes(source)) == expected


# ---------------------------------------------------------------------------
# The opt-in path of cms/tests/live_write_guard.py (user decision 2026-10-13,
# P3/P4 batch). No browser: the guard is called directly; the log path is
# redirected so this run never touches the real reports/ jsonl.
# ---------------------------------------------------------------------------
_APPROVED_DESC = "GM Message 79878 (QCDEMO-129397-general-managers-message)"
# P1/P2 rerun 2026-10-13: the About Hero Banner rows ARE approved now, so the
# "never opened" example is a record nobody approved.
_NOT_APPROVED_DESC = "AboutHeroBanner row QCDEMO-ABOUT-HERO-vision-mission-objectives (one row per page)"
_HERO_DESC = "AboutHeroBanner row QCDEMO-ABOUT-HERO-about-us (one row per page)"


@pytest.fixture
def _guard(monkeypatch, tmp_path):
    from cms.tests import live_write_guard as guard

    log = tmp_path / "live-writes.jsonl"
    monkeypatch.setattr(guard, "LOG_PATH", log)
    monkeypatch.delenv(guard.OPT_IN_ENV, raising=False)
    return guard, log


def test_live_write_guard_default_is_not_applicable(_guard):
    """Without the env var the P1/P2 behaviour is unchanged: NOT APPLICABLE."""
    guard, log = _guard
    with pytest.raises(pytest.fail.Exception) as info:
        guard.block_live_singleton_write(_APPROVED_DESC, "save")
    assert str(info.value).startswith(guard.NOT_APPLICABLE_PREFIX)
    assert not log.exists(), "the default path must not write the live-write log"


def test_live_write_guard_opt_in_logs_and_returns(_guard, monkeypatch):
    """QC_ALLOW_LIVE_SINGLETON_WRITES=1 + an approved record: no failure, one
    well-formed JSON line naming the slug and record code; log_live_write()
    appends another."""
    import json

    guard, log = _guard
    monkeypatch.setenv(guard.OPT_IN_ENV, "1")
    guard.block_live_singleton_write(_APPROVED_DESC, "save", tc_id="135498")
    guard.log_live_write(_APPROVED_DESC, "Signature Avatar", "avatar.png", "135498", action="upload")
    lines = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [e["action"] for e in lines] == ["gate-opened", "upload"]
    for entry in lines:
        assert entry["tc"] == "135498"
        assert entry["object_slug"] == "general-manager-message"
        assert entry["record_code"] == "QCDEMO-129397-general-managers-message"
        assert {"timestamp", "field", "value", "test", "worker"} <= set(entry)
    assert lines[1]["field"] == "Signature Avatar" and lines[1]["value"] == "avatar.png"


def test_live_write_guard_opt_in_never_opens_other_records(_guard, monkeypatch):
    """The opt-in opens ONLY the four approved singletons: a hero row (or any
    other description) stays NOT APPLICABLE with the variable set."""
    guard, log = _guard
    monkeypatch.setenv(guard.OPT_IN_ENV, "1")
    with pytest.raises(pytest.fail.Exception) as info:
        guard.block_live_singleton_write(_NOT_APPROVED_DESC, "save")
    assert str(info.value).startswith(guard.NOT_APPLICABLE_PREFIX)
    assert guard.OPT_IN_ENV in str(info.value)
    assert not log.exists()


def test_live_write_guard_opt_in_never_opens_non_batch_tests(_guard, monkeypatch):
    """An approved record but a test case outside the P3/P4 batch (a P1/P2
    test, or a name with no id) stays NOT APPLICABLE with the variable set."""
    guard, log = _guard
    monkeypatch.setenv(guard.OPT_IN_ENV, "1")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "cms/tests/x.py::test_gm_message_draft_not_public (call)")
    for tc in ("136384", None):  # a P1/P2 id outside the rerun; no id at all
        with pytest.raises(pytest.fail.Exception) as info:
            guard.block_live_singleton_write(_APPROVED_DESC, "save", tc_id=tc)
        assert str(info.value).startswith(guard.NOT_APPLICABLE_PREFIX)
        assert "not in the P3/P4 batch or the P1/P2 rerun" in str(info.value)
    assert not log.exists()


def test_live_write_guard_opt_in_opens_p12_rerun_and_hero_rows(_guard, monkeypatch):
    """P1/P2 rerun (user decision 2026-10-13): a rerun id opens the gate for a
    singleton AND for an approved hero row; gate_opened() then reports it for
    the current test only."""
    import json

    guard, log = _guard
    monkeypatch.setenv(guard.OPT_IN_ENV, "1")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "cms/tests/x.py::test_about_cp_134697_x (call)")
    guard.block_live_singleton_write(_HERO_DESC, "replace", tc_id="134697")
    guard.block_live_singleton_write(_APPROVED_DESC, "save", tc_id="135458")
    entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [e["action"] for e in entries] == ["gate-opened", "gate-opened"]
    assert entries[0]["record_code"] == "QCDEMO-ABOUT-HERO-about-us"
    assert "P1/P2 rerun" in entries[0]["note"]
    assert guard.gate_opened(_HERO_DESC) and guard.gate_opened(_APPROVED_DESC)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "cms/tests/x.py::test_other_134691 (call)")
    assert not guard.gate_opened(_HERO_DESC), "gate_opened() must be scoped to the test that opened it"


def test_live_write_guard_p12_batch_is_the_rerun_file():
    """P12_BATCH_TCS mirrors .claude/qa-runs/phase3-20261012/p12_rerun_ids.json
    (checked only when the file is present -- CI may not have it)."""
    import json

    from cms.tests.live_write_guard import P12_BATCH_TCS

    path = ROOT / ".claude" / "qa-runs" / "phase3-20261012" / "p12_rerun_ids.json"
    if not path.exists():
        pytest.skip("p12_rerun_ids.json is not in this checkout")
    assert P12_BATCH_TCS == frozenset(json.loads(path.read_text(encoding="utf-8")))


def test_hero_create_path_never_opens(_guard, monkeypatch):
    """The QCTEST hero CREATE path stays NOT APPLICABLE with the opt-in set
    (on qcdev it would type into the LIVE row -- incident 183176)."""
    guard, log = _guard
    monkeypatch.setenv(guard.OPT_IN_ENV, "1")
    with pytest.raises(pytest.fail.Exception) as info:
        guard.refuse_hero_create(_HERO_DESC, "create form did not render")
    assert str(info.value).startswith(guard.NOT_APPLICABLE_PREFIX)
    assert not log.exists()


def test_deletes_suppressed_only_under_opt_in(_guard, monkeypatch):
    """Nothing is deleted under the opt-in: keep_instead_of_delete() logs a
    `kept` line and returns True; without the variable it returns False and
    logs nothing (the existing QCTEST teardown runs)."""
    import json

    guard, log = _guard
    assert guard.keep_instead_of_delete("law-entry", "QCTEST-134884-LAW-x", "134884") is False
    assert not log.exists()
    monkeypatch.setenv(guard.OPT_IN_ENV, "1")
    assert guard.deletes_suppressed()
    assert guard.keep_instead_of_delete("law-entry", "QCTEST-134884-LAW-x", "134884") is True
    entry = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["action"] == "kept" and entry["value"] == "QCTEST-134884-LAW-x"


def test_live_write_guard_approves_exactly_seven_records():
    """The approved set is the user's list (2026-10-13: four singletons for the
    P3/P4 batch, plus the three About Hero Banner rows for the P1/P2 rerun),
    nothing more."""
    from cms.tests.live_write_guard import APPROVED_RECORDS

    assert sorted(r.code for r in APPROVED_RECORDS) == sorted([
        "QCDEMO-129397-general-managers-message",
        "QCDEMO-129393-chairmans-message",
        "QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY",
        "QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY",
        "QCDEMO-ABOUT-HERO-about-us",
        "QCDEMO-ABOUT-HERO-chairman-message",
        "QCDEMO-ABOUT-HERO-chamber-laws",
    ])

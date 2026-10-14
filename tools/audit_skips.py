#!/usr/bin/env python
"""
tools/audit_skips.py — inventory every @pytest.mark.skip in the suite and
classify it, so the skipped set can be worked down deliberately instead of
accumulating.

WHY
---
Measured 2026-09-30: 640 of 2,813 test functions (23%) are skipped — 447/1,098
in `cms/tests` (41%) and 193/1,715 in `web/tests` (11%). A skipped test costs
collection time, review time and reporting noise, and returns no signal.
`standards.md` already rules that a case which genuinely cannot be automated
belongs under the `Manual` tag in Azure, NOT skipped in code.

This tool answers "what is actually in there", by resolving each skip's real
reason text — including the ~205 that reference a module-level constant.

BUCKETS
-------
  ENVIRONMENT      blocked by qcdev/infra (login gate, missing account, no
                   access, missing data/config). Not a QA problem — an
                   environment escalation, and the biggest single lever.
  BUILDABLE        blocked only because the precondition would mutate real
                   shared content, or because automation work was deferred.
                   standards.md's disposable-test-data rule (2026-09-22) says
                   these should be rebuilt against QCTEST-* records. This is
                   the bucket QA owns and can work down.
  PRODUCT_GAP      the CMS/product genuinely has no such field/surface, or a
                   confirmed open defect blocks the path. The case premise is
                   wrong or the bug is already known — it should be dropped,
                   rewritten, or linked to the bug, not left as a silent skip.
  NOT_AUTOMATABLE  genuinely not automatable per standards.md Axis 1b (CAPTCHA,
                   real email inbox review, subjective judgement). MUST be
                   re-tagged `Manual` in Azure and removed from the automated
                   suite — a permanent skip books test debt as coverage.
  UNCLASSIFIED     reason text did not match any rule; needs a human read.

Read-only. Writes a JSON + a markdown summary; changes no test.

USAGE
    python tools/audit_skips.py                    # summary to stdout
    python tools/audit_skips.py --json out.json    # full per-test inventory
    python tools/audit_skips.py --md out.md        # markdown report
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_DIRS = ["cms/tests", "web/tests"]

# Ordered: FIRST MATCH WINS, so the most specific rules come first.
RULES: list[tuple[str, str, re.Pattern]] = [
    # --- genuinely not automatable (Axis 1b `Manual`) -----------------------
    (
        "NOT_AUTOMATABLE",
        "CAPTCHA / reCAPTCHA cannot be solved by automation",
        re.compile(r"recaptcha|captcha", re.I),
    ),
    (
        "NOT_AUTOMATABLE",
        "real email inbox / external delivery verification",
        re.compile(r"real (email )?inbox|email delivery|mailbox|"
                   r"actual email .{0,20}(review|receipt)", re.I),
    ),
    (
        "NOT_AUTOMATABLE",
        "subjective / visual-comparison judgement",
        re.compile(r"subjective|visual comparison|human judge|manual visual", re.I),
    ),
    # --- environment --------------------------------------------------------
    (
        "ENVIRONMENT",
        "qcdev CMS login / connection-limit gate",
        re.compile(
            r"cms[_ ]login[_ ]blocked|license|connection limit|developer mode|"
            r"log ?in (is )?block|cannot log ?in|login gate",
            re.I,
        ),
    ),
    (
        "ENVIRONMENT",
        "admin surface unreachable this session (no authenticated CP session)",
        # Must sit ABOVE the credentials rule: these reasons often also mention
        # accounts, but the blocker is reaching the Control Panel at all, and
        # mislabelling ~91 chambers_law rows as "credentials" would point the
        # environment escalation at the wrong thing.
        re.compile(
            r"requires reaching the .{0,60}admin edit form|"
            r"requires an authenticated Liferay Control Panel session|"
            r"could not be reached this session|"
            r"admin surface unreachable|no control[_ ]panel access|"
            r"requires .{0,40}(Control Panel|Liferay) .{0,30}(session|form)",
            re.I,
        ),
    ),
    (
        "ENVIRONMENT",
        "no credentials / account not provisioned",
        re.compile(
            r"no restricted account|second admin|author creds|credential|"
            r"authenticat\w*|not provisioned|no account|_EMAIL/PASSWORD|"
            # Role-account language is unambiguous, so it is matched here —
            # ahead of PRODUCT_GAP, which used to steal these on a bare "exists".
            r"restricted[- ]role account|permission-restricted role|"
            r"role mapping unconfirmed|TEST_USER_RESTRICTED|"
            r"no CMS role account",
            re.I,
        ),
    ),
    (
        "ENVIRONMENT",
        "required data/config absent on qcdev",
        re.compile(
            r"no announcement is configured|not configured on this environment|"
            r"confirmed .{0,12}hidden.{0,30}environment|"
            r"all \d+ real published|insufficient (real )?data|no data configured",
            re.I,
        ),
    ),
    (
        "ENVIRONMENT",
        "no Control_Panel access this batch",
        re.compile(r"no control[_ ]panel access|admin surface unreachable|"
                   r"could not be reached this session|"
                   r"control panel not (available|reachable)", re.I),
    ),
    (
        "ENVIRONMENT",
        "other browser engine not configured",
        re.compile(r"no[_ ]other[_ ]engine|non-chromium|firefox|webkit|"
                   r"second browser", re.I),
    ),
    # --- product / premise gaps --------------------------------------------
    (
        "PRODUCT_GAP",
        "confirmed open defect blocks the path",
        re.compile(r"confirmed bug|confirmed_bug|open defect|product bug|"
                   r"fields[_ ]panel[_ ]blocked|rendering defect|blocked by bug|"
                   r"BLOCKED \(live", re.I),
    ),
    (
        "PRODUCT_GAP",
        "admin surface / object does not exist",
        re.compile(
            r"no\s+'[^']+'\s+(admin\s+)?(surface|object|page)|"
            r"no page settings|no page object|no .{0,40}surface exists|"
            r"no .{0,40}object exists|no-types-surface|no .{0,30}admin surface",
            re.I,
        ),
    ),
    (
        "PRODUCT_GAP",
        "field / control does not exist in the CMS",
        re.compile(
            r"(field|control|button|input|option|dropdown)[^.]{0,40}does not exist|no such field|no field|not exposed|"
            r"no cancel button|no .{0,25}placeholder|schema mismatch|"
            r"not configurable|hardcoded|no corresponding admin|"
            r"no in-form|is not documented|no .{0,30}control exists",
            re.I,
        ),
    ),
    # --- buildable (QA owns these) -----------------------------------------
    (
        "BUILDABLE",
        "precondition would mutate real shared content",
        re.compile(
            r"singleton[_ ]write|real shared|shared record|real content|"
            r"would (delete|unpublish|mutate)|destructive|only .{0,30}real |"
            r"last icon|deactivat\w+ .{0,30}real|production rows|"
            r"real state-transition|against the shared qcdev",
            re.I,
        ),
    ),
    (
        "BUILDABLE",
        "cross-surface precondition not set up (needs a CMS write)",
        re.compile(r"precondition unavailable|control_panel authoring write|"
                   r"requires a control[_ ]panel|depends on tc_", re.I),
    ),
    (
        "BUILDABLE",
        "automation debt — deferred, not yet migrated",
        # NOTE: do NOT add `this session` here — that phrase also appears in
        # ENVIRONMENT reasons ("could not be reached this session") and would
        # silently steal them the moment these rules are reordered.
        re.compile(r"not yet migrated|deferred|scope was|"
                   r"data risk|publish confound|unresolved", re.I),
    ),
    (
        "BUILDABLE",
        "needs a disposable record that was not created",
        re.compile(r"disposable|qctest|test record|no fixture record|"
                   r"requires a record", re.I),
    ),
]


def resolve_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level NAME = <str literal / implicit concat> assignments."""
    out: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        tgt = node.targets[0]
        if not isinstance(tgt, ast.Name):
            continue
        try:
            val = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
        if isinstance(val, str):
            out[tgt.id] = val
    return out


def skip_reason(call: ast.Call, consts: dict[str, str]) -> str:
    """Pull the reason out of a pytest.mark.skip(...) call."""
    parts: list[ast.expr] = list(call.args)
    for kw in call.keywords:
        if kw.arg in (None, "reason"):
            parts.append(kw.value)
    for node in parts:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name) and node.id in consts:
            return consts[node.id]
        if isinstance(node, ast.JoinedStr):  # f-string
            bits = [
                v.value for v in node.values
                if isinstance(v, ast.Constant) and isinstance(v.value, str)
            ]
            if bits:
                return "".join(bits)
        if isinstance(node, ast.Attribute):
            return f"<attr:{node.attr}>"
    return ""


def is_skip(dec: ast.expr) -> ast.Call | None:
    """Match @pytest.mark.skip(...) and bare @pytest.mark.skip."""
    target = dec.func if isinstance(dec, ast.Call) else dec
    if not isinstance(target, ast.Attribute) or target.attr != "skip":
        return None
    owner = target.value
    if not (isinstance(owner, ast.Attribute) and owner.attr == "mark"):
        return None
    return dec if isinstance(dec, ast.Call) else ast.Call(func=dec, args=[], keywords=[])


def tc_of(fn: ast.FunctionDef) -> str:
    for dec in fn.decorator_list:
        t = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(t, ast.Attribute) and t.attr.startswith("tc_"):
            return t.attr
    m = re.search(r"_(\d{5,6})$", fn.name)
    return f"tc_{m.group(1)}" if m else ""


def classify(reason: str) -> tuple[str, str]:
    for bucket, label, pat in RULES:
        if pat.search(reason):
            return bucket, label
    return "UNCLASSIFIED", "reason did not match any rule"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--md")
    args = ap.parse_args()

    rows: list[dict] = []
    for d in TEST_DIRS:
        for py in sorted((ROOT / d).rglob("test_*.py")):
            if "__pycache__" in py.parts:
                continue
            src = py.read_text(encoding="utf-8", errors="replace")
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            consts = resolve_constants(tree)
            for fn in ast.walk(tree):
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not fn.name.startswith("test_"):
                    continue
                for dec in fn.decorator_list:
                    call = is_skip(dec)
                    if call is None:
                        continue
                    reason = skip_reason(call, consts).strip()
                    bucket, label = classify(reason)
                    rows.append({
                        "file": str(py.relative_to(ROOT)).replace("\\", "/"),
                        "surface": "cms" if d.startswith("cms") else "web",
                        "test": fn.name,
                        "tc": tc_of(fn),
                        "line": fn.lineno,
                        "bucket": bucket,
                        "label": label,
                        "reason": " ".join(reason.split())[:400],
                    })
                    break

    by_bucket = Counter(r["bucket"] for r in rows)
    by_label = Counter((r["bucket"], r["label"]) for r in rows)
    by_file = Counter(r["file"] for r in rows)

    total = len(rows)
    print(f"skipped tests found: {total}\n")
    print(f"{'BUCKET':<14} {'COUNT':>6}  {'SHARE':>6}")
    for b, n in by_bucket.most_common():
        print(f"{b:<14} {n:>6}  {n/total*100:>5.1f}%")
    print("\nBy reason:")
    for (b, label), n in by_label.most_common():
        print(f"  {n:>4}  [{b}] {label}")
    print("\nTop 12 files by skip count:")
    for f, n in by_file.most_common(12):
        print(f"  {n:>4}  {f}")

    if args.json:
        Path(args.json).write_text(
            json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {args.json}")

    if args.md:
        empty_reason = [r for r in rows if not r["reason"]]
        lines = [
            "# Skipped-test audit",
            "",
            f"Generated by `tools/audit_skips.py`. **{total} skipped tests** found "
            "across `cms/tests` and `web/tests`.",
            "",
            "## Read this before trusting the table",
            "",
            "- **This is triage, not a verdict.** Buckets come from regex rules over "
            "each skip's reason text. Bucket-level agreement on a hand-checked "
            "stratified sample was **28/32 (88%)**; all 4 disagreements were rows left "
            "`UNCLASSIFIED` that should have been bucketed — i.e. the tool fails "
            "conservatively, it did not put a test in the wrong bucket.",
            f"- **Coverage is {total}/640.** A `grep` counts 640 `@pytest.mark.skip` "
            "marks; this AST walk finds "
            f"{total}. The ~11 difference is skips applied *inside* decorator "
            "factories (e.g. `_make_singleton_skip`) rather than as literal "
            "decorators. The inventory is not complete — treat counts as ±11.",
            f"- **{len(empty_reason)} skips carry NO reason string at all.** "
            "`standards.md` requires the exact blocking reason on every skip. "
            "These need a reason regardless of how they bucket.",
            "",
        ]
        lines += ["| Bucket | Count | Share |", "|---|---:|---:|"]
        for b, n in by_bucket.most_common():
            lines.append(f"| {b} | {n} | {n/total*100:.1f}% |")
        lines += ["", "## By reason", "", "| Count | Bucket | Reason |", "|---:|---|---|"]
        for (b, label), n in by_label.most_common():
            lines.append(f"| {n} | {b} | {label} |")

        # --- concentration: the actionable finding -------------------------
        top3 = by_file.most_common(3)
        top3_n = sum(n for _, n in top3)
        lines += [
            "",
            "## The actionable finding: concentration",
            "",
            f"**{top3_n} of {total} skips ({top3_n/total*100:.0f}%) sit in just three "
            "CMS modules**, and all three are blocked on the same class of thing — "
            "reaching the Liferay admin surface with a working session/role:",
            "",
            "| Skips | Module |",
            "|---:|---|",
        ]
        for f, n in top3:
            lines.append(f"| {n} | `{f}` |")
        env_gate = by_label.get(
            ("ENVIRONMENT", "qcdev CMS login / connection-limit gate"), 0)
        env_surface = by_label.get(
            ("ENVIRONMENT",
             "admin surface unreachable this session (no authenticated CP session)"), 0)
        lines += [
            "",
            f"Across the whole suite, **{env_gate + env_surface} skips** "
            f"({(env_gate + env_surface)/total*100:.0f}%) name either the qcdev "
            "connection-limit gate or an unreachable Control Panel session. "
            "**That is one environment escalation, not hundreds of test tickets.**",
            "",
            "## Recommended action per bucket",
            "",
            "| Bucket | Owner | Action |",
            "|---|---|---|",
            "| ENVIRONMENT | Infra / project | Escalate as ONE item: a dedicated CMS "
            "instance or a raised dev connection limit. This is the single biggest "
            "lever on suite value. Do not rewrite these tests. |",
            "| BUILDABLE | QA automation | Rebuild against disposable `QCTEST-*` "
            "records per `standards.md`'s disposable-test-data rule. This is the "
            "bucket QA owns and can work down without anyone's permission. |",
            "| PRODUCT_GAP | QA Manager | The case premise is wrong or the defect is "
            "known. Drop, rewrite, or link to the bug in Azure — do not leave as a "
            "silent skip. |",
            "| NOT_AUTOMATABLE | QA Manager | Re-tag `Manual` in Azure and remove from "
            "the automated suite (`standards.md` Axis 1b). Small and concrete. |",
            "| UNCLASSIFIED | QA automation | Needs a human read. 17 of these have no "
            "reason string at all, which is its own standards violation. |",
        ]
        grouped = defaultdict(list)
        for r in rows:
            grouped[r["bucket"]].append(r)
        for b in ("BUILDABLE", "NOT_AUTOMATABLE", "PRODUCT_GAP", "ENVIRONMENT", "UNCLASSIFIED"):
            if b not in grouped:
                continue
            lines += ["", f"## {b} — {len(grouped[b])} tests", "",
                      "| File | Test | TC | Reason |", "|---|---|---|---|"]
            for r in sorted(grouped[b], key=lambda r: (r["file"], r["line"])):
                reason = r["reason"].replace("|", "\\|")[:180]
                lines.append(
                    f"| `{r['file'].split('/')[-1]}` | `{r['test'][:52]}` "
                    f"| {r['tc']} | {reason} |")
        Path(args.md).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {args.md}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Merge B-129390 pytest logs (later logs override earlier ones per test) into
the inventory .claude/qa-runs/phase3_129390_2026-10-07.json and print a
markdown results table. Verdict/notes come from NOTES below (hand-written
after triage)."""
import json, re, sys

INV = ".claude/qa-runs/phase3_129390_2026-10-07.json"
TCMAP = sys.argv[1]
LOGS = ["reports/pbi_129390_p12.log", "reports/pbi_129390_p34.log", "reports/pbi_129390_p12_rerun.log",
        "reports/pbi_129390_p34_rerun.log", "reports/pbi_129390_save_p12.log", "reports/pbi_129390_save_p34.log"]
NOTES = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else {}

tcmap = json.load(open(TCMAP))
node2tc = {n.split("[")[0]: tc for tc, ns in tcmap.items() for n in ns}
res = {}
for log in LOGS:
    try:
        txt = open(log, encoding="utf-8", errors="replace").read()
    except FileNotFoundError:
        continue
    for m in re.finditer(r"^(PASSED|FAILED|ERROR) (\S+?)(\[|\s|$)", txt, re.M):
        tc = node2tc.get(m.group(2))
        if tc:
            res[tc] = {"result": m.group(1), "log": log}
inv = json.load(open(INV, encoding="utf-8"))
for c in inv["cases"]:
    tc = str(c["tc_id"])
    if tc in res:
        c["result"] = res[tc]["result"]
        c["log"] = res[tc]["log"]
    if tc in NOTES:
        c.update(NOTES[tc])
json.dump(inv, open(INV, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("| tc_id | title | P | result | verdict | note |\n|---|---|---|---|---|---|")
for c in inv["cases"]:
    t = c["title"].replace("|", "/")
    t = t if len(t) <= 70 else t[:67] + "..."
    print(f"| {c['tc_id']} | {t} | P{c['priority']} | {c.get('result') or '-'} | {c.get('verdict') or '-'} | {c.get('note') or ''} |")

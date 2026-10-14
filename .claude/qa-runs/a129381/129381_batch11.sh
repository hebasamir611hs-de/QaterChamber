cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
echo "== probe10 (27 drafts provenance, read-only)"; python .claude/qa-runs/a129381/129381_probe10.py 2>&1 | grep -v base_page | tail -40
echo "== gactive2"; python .claude/qa-runs/a129381/129381_gactive.py 2>&1 | grep -v base_page | tail -60

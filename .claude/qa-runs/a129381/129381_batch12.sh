cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
echo "== gactive2 retry"; python .claude/qa-runs/a129381/129381_gactive.py 2>&1 | grep -v base_page | tail -60

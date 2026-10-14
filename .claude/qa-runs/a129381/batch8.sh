cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
echo "== manual9"; python .claude/qa-runs/a129381/manual9.py 2>&1 | grep -v base_page | tail -80
echo "== cleanup_all"; python .claude/qa-runs/a129381/cleanup_all.py 2>&1 | grep -v base_page
echo "== sync markers"; python tools/sync_tc_markers.py 2>&1 | tail -3

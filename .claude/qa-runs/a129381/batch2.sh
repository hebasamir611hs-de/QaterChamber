cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
TS=$(date +%H%M)
echo "== listrows pre"; python .claude/qa-runs/a129381/listrows.py 2>&1 | grep -v "base_page"
echo "== probe2"; python .claude/qa-runs/a129381/probe2.py 2>&1 | grep -v "base_page"
echo "== smoke 135560"
python -m pytest cms/tests/home_strategic_direction -k test_draft_not_public -n 0 --alluredir=reports/allure-results-phase3-129381-20261007-${TS}-smoke --no-clean-evidence -p no:cacheprovider 2>&1 | grep -v base_page | tail -30
echo "== listrows after smoke"; python .claude/qa-runs/a129381/listrows.py 2>&1 | grep -v "base_page"

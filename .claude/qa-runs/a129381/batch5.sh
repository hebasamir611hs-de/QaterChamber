cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
echo "== manual5"; python .claude/qa-runs/a129381/manual5.py 2>&1 | grep -v base_page | tail -5
echo "== listrows pre"; python .claude/qa-runs/a129381/listrows.py 2>&1 | grep -v "base_page"
echo "== web new + Figma tolerance heal rerun"
python -m pytest web/tests/home_strategic_direction -m "tc_135544 or tc_135545 or tc_135546 or tc_135547 or tc_135629 or tc_135631 or tc_135632 or tc_135519 or tc_135522 or tc_135526 or tc_135527" --alluredir=reports/allure-results-phase3-129381-20261007-web-p34-new --no-clean-evidence -p no:cacheprovider 2>&1 | grep -v base_page | grep -E "PASSED|FAILED|ERROR|passed|failed|error" | tail -20
echo "== CMS P3/P4 new"
python -m pytest cms/tests/home_strategic_direction -n 2 -m "tc_135539 or tc_135540 or tc_135541 or tc_135542 or tc_135543 or tc_135594 or tc_135595 or tc_135596 or tc_135597 or tc_135600 or tc_135604 or tc_135608 or tc_135612 or tc_135601 or tc_135605 or tc_135609 or tc_135618 or tc_135615 or tc_135616 or tc_135617 or tc_135630 or tc_135626 or tc_135627 or tc_135628 or tc_135633 or tc_135625" --alluredir=reports/allure-results-phase3-129381-20261007-cms-p34-new --no-clean-evidence -p no:cacheprovider 2>&1 | grep -v base_page | grep -E "PASSED|FAILED|ERROR|passed|failed|error" | tail -30
echo "== listrows post"; python .claude/qa-runs/a129381/listrows.py 2>&1 | grep -v "base_page"

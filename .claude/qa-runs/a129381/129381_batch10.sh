cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
echo "== probe9"; python .claude/qa-runs/a129381/129381_probe9.py 2>&1 | grep -v base_page | tail -3
echo "== gactive"; python .claude/qa-runs/a129381/129381_gactive.py 2>&1 | grep -v base_page | tail -60
echo "== web G-PROG/badge rerun"
python -m pytest web/tests/home_strategic_direction -m "tc_135516 or tc_135523 or tc_135532" --alluredir=reports/allure-results-phase3-129381-20261008-web-rerun-fix --no-clean-evidence -p no:cacheprovider 2>&1 | grep -E "PASSED|FAILED|passed|failed" | tail -6
echo "== CMS rerun-fix"
python -m pytest cms/tests/home_strategic_direction -m "tc_135539 or tc_135540 or tc_135541 or tc_135543 or tc_135551 or tc_135556 or tc_135560 or tc_135591 or tc_135592 or tc_135596 or tc_135597 or tc_135600 or tc_135601 or tc_135604 or tc_135605 or tc_135606 or tc_135608 or tc_135609 or tc_135610 or tc_135612 or tc_135613 or tc_135618 or tc_135619 or tc_135622 or tc_135626 or tc_135627 or tc_135628 or tc_135630" --alluredir=reports/allure-results-phase3-129381-20261008-cms-rerun-fix --no-clean-evidence -p no:cacheprovider 2>&1 | grep -v base_page | grep -E "PASSED|FAILED|passed|failed|WARNING.*lost" | tail -40
echo "== listing post"; python .claude/qa-runs/a129381/cleanup_all.py 2>&1 | grep -v base_page

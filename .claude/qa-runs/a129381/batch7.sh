cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8


echo "== CMS P3/P4 new + P1/P2 rerun-2"
python -m pytest cms/tests/home_strategic_direction -n 2 -m "tc_135539 or tc_135540 or tc_135541 or tc_135542 or tc_135543 or tc_135594 or tc_135595 or tc_135596 or tc_135597 or tc_135600 or tc_135604 or tc_135608 or tc_135612 or tc_135601 or tc_135605 or tc_135609 or tc_135618 or tc_135615 or tc_135616 or tc_135617 or tc_135630 or tc_135626 or tc_135627 or tc_135628 or tc_135633 or tc_135625 or tc_135551 or tc_135556 or tc_135560 or tc_135591 or tc_135592 or tc_135606 or tc_135610 or tc_135613 or tc_135619 or tc_135622" --alluredir=reports/allure-results-phase3-129381-20261008-cms-all2 --no-clean-evidence -p no:cacheprovider 2>&1 | grep -v base_page | grep -E "PASSED|FAILED|ERROR|passed|failed|error|WARNING.*lost" | tail -45
echo "== cleanup_all post"; python .claude/qa-runs/a129381/cleanup_all.py 2>&1 | grep -v base_page

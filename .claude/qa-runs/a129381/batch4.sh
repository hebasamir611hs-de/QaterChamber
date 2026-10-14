cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
echo "== cleanup"; python .claude/qa-runs/a129381/cleanup.py QCTEST-135557-edit-desc QCTEST-135556-new-card QCTEST-135551-author 2>&1 | grep -v base_page
echo "== listrows after cleanup"; python .claude/qa-runs/a129381/listrows.py 2>&1 | grep -v "base_page"
echo "== web 135529 rerun (after leftover cleanup)"
python -m pytest web/tests/home_strategic_direction -m "tc_135529" --alluredir=reports/allure-results-phase3-129381-20261007-web-p2-rerun2 --no-clean-evidence -p no:cacheprovider 2>&1 | grep -E "passed|failed|FAILED" | tail -3
echo "== CMS rerun (serial)"
python -m pytest cms/tests/home_strategic_direction -n 0 -m "tc_135556 or tc_135551 or tc_135560 or tc_135558 or tc_135559 or tc_135591 or tc_135562 or tc_135592 or tc_135606 or tc_135610 or tc_135603 or tc_135613 or tc_135614 or tc_135619 or tc_135622" --alluredir=reports/allure-results-phase3-129381-20261007-cms-rerun --no-clean-evidence -p no:cacheprovider 2>&1 | grep -v base_page | grep -E "PASSED|FAILED|ERROR|passed|failed|error" | tail -30
echo "== listrows post"; python .claude/qa-runs/a129381/listrows.py 2>&1 | grep -v "base_page"

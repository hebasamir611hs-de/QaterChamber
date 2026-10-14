cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
TS=$(date +%H%M)
echo "== listrows pre"; python .claude/qa-runs/a129381/listrows.py 2>&1 | grep -v "base_page"
echo "== CMS P1/P2"
python -m pytest cms/tests/home_strategic_direction -k "not test_abandon_add_form_discards_data" --alluredir=reports/allure-results-phase3-129381-20261007-${TS}-cms --no-clean-evidence -p no:cacheprovider 2>&1 | grep -v base_page | grep -E "PASSED|FAILED|ERROR|passed|failed|error" | tail -40
echo "== listrows mid"; python .claude/qa-runs/a129381/listrows.py 2>&1 | grep -v "base_page"
echo "== P3/P4 web + 135563"
python -m pytest web/tests/home_strategic_direction cms/tests/home_strategic_direction -m "tc_135515 or tc_135516 or tc_135517 or tc_135518 or tc_135519 or tc_135520 or tc_135521 or tc_135522 or tc_135523 or tc_135524 or tc_135525 or tc_135526 or tc_135527 or tc_135532 or tc_135533 or tc_135535 or tc_135536 or tc_135537 or tc_135563" --alluredir=reports/allure-results-phase3-129381-20261007-${TS}-p34 --no-clean-evidence -p no:cacheprovider 2>&1 | grep -v base_page | grep -E "PASSED|FAILED|ERROR|passed|failed|error" | tail -40
echo "== web P2 rerun (healed autoplay/stacking)"
python -m pytest web/tests/home_strategic_direction -m "tc_135529 or tc_135530 or tc_135531 or tc_135534 or tc_135552" --alluredir=reports/allure-results-phase3-129381-20261007-web-p2-rerun --no-clean-evidence -p no:cacheprovider 2>&1 | grep -v base_page | grep -E "PASSED|FAILED|ERROR|passed|failed|error" | tail -20
echo "== listrows post"; python .claude/qa-runs/a129381/listrows.py 2>&1 | grep -v "base_page"

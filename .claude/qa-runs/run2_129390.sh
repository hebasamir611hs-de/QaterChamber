#!/bin/bash
# B-129390 live batch 2: healed article save + orphan cleanup, then the article tests that save.
cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
STAMP=$(date +%H%M)
HI="$(cat 'C:/Users/HEBA~1.SAM/AppData/Local/Temp/claude/d--MCP-servers-QaterChamper/2e7244a1-8fff-40ce-8868-fc5fd0439745/scratchpad/hi.txt')"
LO="$(cat 'C:/Users/HEBA~1.SAM/AppData/Local/Temp/claude/d--MCP-servers-QaterChamper/2e7244a1-8fff-40ce-8868-fc5fd0439745/scratchpad/lo.txt')"
SAVING="tc_136508 or tc_136512 or tc_136516 or tc_136518 or tc_136523 or tc_136527 or tc_136531 or tc_136541 or tc_136555 or tc_136559 or tc_136563 or tc_136565 or tc_136510 or tc_136514 or tc_136517 or tc_136521 or tc_136525 or tc_136529 or tc_136533 or tc_136544 or tc_136548 or tc_136557 or tc_136561 or tc_136564 or tc_136567 or tc_136574 or tc_136546 or tc_136572 or tc_136498"
echo "== cleanup categories $(date)"
python .claude/qa-runs/cleanup_ic_129390.py > reports/cleanup-ic-129390.log 2>&1
grep -v base_page reports/cleanup-ic-129390.log | tail -15
echo "== heal rerun P1/P2 $(date)"
python -m pytest web/tests/home_quick_contact cms/tests/home_contact_us -m "tc_136483 or tc_136535 or tc_136537 or tc_136570 or tc_136539 or tc_136556 or tc_136558 or tc_136560 or tc_136562 or tc_136566 or tc_136568 or tc_136573 or tc_136575" --alluredir=reports/allure-results-phase3-129390-20261007-${STAMP}-p12-rerun --no-clean-evidence -p no:cacheprovider -q -rA > reports/pbi_129390_p12_rerun.log 2>&1
tail -3 reports/pbi_129390_p12_rerun.log
echo "== heal rerun P3/P4 $(date)"
python -m pytest web/tests/home_quick_contact cms/tests/home_contact_us -m "tc_136534 or tc_136538 or tc_136569 or tc_136536 or tc_136571 or tc_136550" --alluredir=reports/allure-results-phase3-129390-20261007-${STAMP}-p34-rerun --no-clean-evidence -p no:cacheprovider -q -rA > reports/pbi_129390_p34_rerun.log 2>&1
tail -3 reports/pbi_129390_p34_rerun.log
echo "== gate2 $(date)"
python .claude/qa-runs/gate2_129390.py > reports/gate2-129390.log 2>&1
grep -v base_page reports/gate2-129390.log | tail -6
if ! grep -q GATE_OK reports/gate2-129390.log; then echo "GATE2 FAILED - saving tests skipped"; SKIPSAVE=1; fi
if [ -z "$SKIPSAVE" ]; then
echo "== saving P1/P2 $(date)"
python -m pytest cms/tests/home_contact_us -m "($SAVING) and ($HI)" --alluredir=reports/allure-results-phase3-129390-20261007-${STAMP}-save-p12 --no-clean-evidence -p no:cacheprovider -q -rA > reports/pbi_129390_save_p12.log 2>&1
tail -3 reports/pbi_129390_save_p12.log
echo "== saving P3/P4 $(date)"
python -m pytest cms/tests/home_contact_us -m "($SAVING) and ($LO)" --alluredir=reports/allure-results-phase3-129390-20261007-${STAMP}-save-p34 --no-clean-evidence -p no:cacheprovider -q -rA > reports/pbi_129390_save_p34.log 2>&1
tail -3 reports/pbi_129390_save_p34.log
fi
echo "== manual2 $(date)"
python .claude/qa-runs/manual2_129390.py > reports/manual2-129390.log 2>&1
tail -1 reports/manual2-129390.log
echo "== final category check $(date)"
python .claude/qa-runs/cleanup_ic_129390.py > reports/cleanup-ic2-129390.log 2>&1
grep "^done" reports/cleanup-ic2-129390.log
echo "== end $(date)"

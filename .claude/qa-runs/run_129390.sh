#!/bin/bash
# B-129390 live batch (run inside b129390_live.sh, i.e. under the c7 lock).
cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
STAMP=$(date +%H%M)
HI="$(cat 'C:/Users/HEBA~1.SAM/AppData/Local/Temp/claude/d--MCP-servers-QaterChamper/2e7244a1-8fff-40ce-8868-fc5fd0439745/scratchpad/hi.txt')"
LO="$(cat 'C:/Users/HEBA~1.SAM/AppData/Local/Temp/claude/d--MCP-servers-QaterChamper/2e7244a1-8fff-40ce-8868-fc5fd0439745/scratchpad/lo.txt')"
SAVING="tc_136508 or tc_136512 or tc_136516 or tc_136518 or tc_136523 or tc_136527 or tc_136531 or tc_136541 or tc_136555 or tc_136559 or tc_136563 or tc_136565 or tc_136510 or tc_136514 or tc_136517 or tc_136521 or tc_136525 or tc_136529 or tc_136533 or tc_136544 or tc_136548 or tc_136557 or tc_136561 or tc_136564 or tc_136567 or tc_136574 or tc_136546 or tc_136572 or tc_136498"
echo "== gate $(date)"
python .claude/qa-runs/gate_129390.py > reports/gate-129390.log 2>&1
if grep -q GATE_OK reports/gate-129390.log; then EXCL=""; else EXCL=" and not ($SAVING)"; echo "GATE FAILED - saving article tests deselected"; fi
echo "== sync markers $(date)"
python tools/sync_tc_markers.py > reports/sync-markers-129390.log 2>&1; tail -3 reports/sync-markers-129390.log
echo "== P1/P2 $(date)"
python -m pytest web/tests/home_quick_contact cms/tests/home_contact_us -m "($HI)$EXCL" --alluredir=reports/allure-results-phase3-129390-20261007-${STAMP}-p12 --no-clean-evidence -p no:cacheprovider -q -rA > reports/pbi_129390_p12.log 2>&1
tail -5 reports/pbi_129390_p12.log
echo "== P3/P4 $(date)"
python -m pytest web/tests/home_quick_contact cms/tests/home_contact_us -m "($LO)$EXCL" --alluredir=reports/allure-results-phase3-129390-20261007-${STAMP}-p34 --no-clean-evidence -p no:cacheprovider -q -rA > reports/pbi_129390_p34.log 2>&1
tail -5 reports/pbi_129390_p34.log
echo "== manual $(date)"
python .claude/qa-runs/manual_129390.py > reports/manual-129390.log 2>&1
tail -2 reports/manual-129390.log
echo "== end $(date)"

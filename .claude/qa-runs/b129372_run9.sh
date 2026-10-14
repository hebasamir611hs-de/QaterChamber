#!/bin/bash
cd "/d/MCP servers/QaterChamper"
SP="C:/Users/HEBA~1.SAM/AppData/Local/Temp/claude/d--MCP-servers-QaterChamper/2e7244a1-8fff-40ce-8868-fc5fd0439745/scratchpad"
python -c "import os,time,sys
p='.claude/qa-runs/qcdev-browser-c7.lock'
for _ in range(1080):
    try: os.mkdir(p); open(p+'/owner','w').write(sys.argv[1]); sys.exit(0)
    except FileExistsError: time.sleep(10)
sys.exit('lock timeout')" B-129372 || exit 9
trap 'rm -rf .claude/qa-runs/qcdev-browser-c7.lock' EXIT
echo "LOCKED $(date +%H%M)"
export PYTHONIOENCODING=utf-8
unset QC_KEEP_QCTEST
echo "=== MANUAL3"; timeout 1500 python "$SP/b129372_manual3.py" > "$SP/b129372_manual3.json" 2> "$SP/b129372_manual3.err"; echo rc=$?
echo "=== CLEAN"; timeout 1200 python "$SP/cleanup_129372.py" --delete > "$SP/b129372_clean9.json" 2> "$SP/b129372_clean9.err"; echo rc=$?
echo DONE

#!/bin/bash
# Usage: b129390_live.sh <command...>  — acquires the c7 lock, runs, releases.
cd "/d/MCP servers/QaterChamper"
python -c "import os,time,sys
p='.claude/qa-runs/qcdev-browser-c7.lock'
for _ in range(1080):
    try: os.mkdir(p); open(p+'/owner','w').write(sys.argv[1]); sys.exit(0)
    except FileExistsError: time.sleep(10)
sys.exit('lock timeout')" B-129390 || exit 99
trap 'rm -rf .claude/qa-runs/qcdev-browser-c7.lock' EXIT
echo "LOCK ACQUIRED $(date)"
"$@"
echo "EXIT $?"

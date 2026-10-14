cd "/d/MCP servers/QaterChamper"
python -c "import os,time,sys
p='.claude/qa-runs/qcdev-browser-c7.lock'
for _ in range(1080):
    try: os.mkdir(p); open(p+'/owner','w').write(sys.argv[1]); sys.exit(0)
    except FileExistsError: time.sleep(10)
sys.exit('lock timeout')" A-129368 || exit 9
trap 'rm -rf .claude/qa-runs/qcdev-browser-c7.lock' EXIT
L=.claude/qa-runs/a129368
export PYTHONIOENCODING=utf-8
TS=$(date +%H%M)
python -m pytest $(cat $L/rerun_nodeids_lf.txt) -n 2 --alluredir=reports/allure-results-phase3-129368-20261007-$TS-rerun --no-clean-evidence -p no:cacheprovider > $L/run_rerun.log 2>&1
python $L/cleanup_and_repro.py cleanup > $L/cleanup3.json 2>$L/cleanup3.err
echo "TS=$TS" > $L/run3.done

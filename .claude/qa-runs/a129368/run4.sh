cd "/d/MCP servers/QaterChamper"
python -c "import os,time,sys
p='.claude/qa-runs/qcdev-browser-c7.lock'
for _ in range(1080):
    try: os.mkdir(p); open(p+'/owner','w').write(sys.argv[1]); sys.exit(0)
    except FileExistsError: time.sleep(10)
sys.exit('lock timeout')" A-129368 || exit 9
trap 'rm -rf .claude/qa-runs/qcdev-browser-c7.lock' EXIT
export PYTHONIOENCODING=utf-8
python .claude/qa-runs/a129368/repro4.py > .claude/qa-runs/a129368/repro4.json 2>.claude/qa-runs/a129368/repro4.err
TS=$(date +%H%M)
python -m pytest "cms/tests/home_promo_banners/test_home_promo_banners_control_panel.py::test_valid_redirect_url_ar_saved" "cms/tests/home_promo_banners/test_home_promo_banners_control_panel.py::test_invalid_redirect_url_ar_refused" "cms/tests/home_promo_banners/test_home_promo_banners_control_panel.py::test_oversized_or_unsupported_banner_image_refused[135232-en]" "cms/tests/home_promo_banners/test_home_promo_banners_control_panel.py::test_oversized_or_unsupported_banner_image_refused[135235-ar]" "cms/tests/home_promo_banners/test_home_promo_banners_control_panel.py::test_toggle_banner_active_status[135119-enable]" "cms/tests/home_promo_banners/test_home_promo_banners_control_panel.py::test_toggle_banner_active_status[135120-disable]" -n 2 --alluredir=reports/allure-results-phase3-129368-20261007-$TS-rerun2 --no-clean-evidence -p no:cacheprovider > .claude/qa-runs/a129368/run_rerun2.log 2>&1
python .claude/qa-runs/a129368/cleanup_and_repro.py cleanup > .claude/qa-runs/a129368/cleanup4.json 2>.claude/qa-runs/a129368/cleanup4.err
echo "TS=$TS" > .claude/qa-runs/a129368/run4.done

cd "/d/MCP servers/QaterChamper"
python -c "import os,time,sys
p='.claude/qa-runs/qcdev-browser-c7.lock'
for _ in range(1080):
    try: os.mkdir(p); open(p+'/owner','w').write(sys.argv[1]); sys.exit(0)
    except FileExistsError: time.sleep(10)
sys.exit('lock timeout')" A-129368 || exit 9
trap 'rm -rf .claude/qa-runs/qcdev-browser-c7.lock' EXIT
TS=$(date +%H%M)
L=.claude/qa-runs/a129368
python tools/sync_tc_markers.py > $L/sync.log 2>&1
W=web/tests/home_promo_banners/test_home_promo_banners_web.py
python -m pytest "$W::test_promo_banners_render_correctly_in_english_ltr" "$W::test_promo_banners_mirror_correctly_in_arabic_rtl" "$W::test_promo_banners_render_configured_image_and_en_alt_text" "$W::test_promo_banners_render_configured_image_and_ar_alt_text" "$W::test_promo_banners_multiple_active_banners_in_one_slider" "$W::test_promo_banners_visitor_can_view_and_click" --alluredir=reports/allure-results-phase3-129368-20261007-$TS-web --no-clean-evidence -p no:cacheprovider > $L/run_web_p2.log 2>&1
python -m pytest cms/tests/home_promo_banners --alluredir=reports/allure-results-phase3-129368-20261007-$TS --no-clean-evidence -p no:cacheprovider > $L/run_cms.log 2>&1
python -m pytest "$W::test_promo_banners_next_arrow_advances_slider" "$W::test_promo_banners_prev_arrow_and_dot_navigate_back" "$W::test_promo_banners_responsive_at_mobile_width" "$W::test_promo_banners_responsive_at_tablet_and_desktop_widths" --alluredir=reports/allure-results-phase3-129368-20261007-$TS-web-p3 --no-clean-evidence -p no:cacheprovider > $L/run_web_p3.log 2>&1
echo "TS=$TS" > $L/run1.done

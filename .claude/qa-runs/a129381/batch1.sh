cd "/d/MCP servers/QaterChamper"
export PYTHONIOENCODING=utf-8
echo "== probe"; python .claude/qa-runs/a129381/probe1.py
echo "== sync markers"; python tools/sync_tc_markers.py
echo "== web P2"
python -m pytest web/tests/home_strategic_direction -k "test_copy_matches_figma_exactly_no_truncation or test_only_one_pillar_card_visible_at_a_time or test_next_arrow_advances_vision_to_mission or test_prev_arrow_returns_mission_to_vision or test_renders_mirrored_in_arabic_rtl or test_visitor_views_published_section_end_to_end or test_visitor_navigates_forward_through_all_pillars or test_visitor_navigates_backward_through_all_pillars" --alluredir=reports/allure-results-phase3-129381-20261007-web-p2 --no-clean-evidence -p no:cacheprovider 2>&1 | tail -40

"""TC 135099 wrapper (QA lead approval 2026-10-18: "اعمل انت unpublish").
Unpublishes the 8 REAL hero slides other than QCDEMO-129367-HERO_BANNER_SLIDE-01,
by exact entry code, through each row's Unpublish action as the Site Content
Editor; runs the read-only web test; then re-publishes the same 8 through the
row's Publish action in `finally` and verifies them on a fresh list read.
Every write is logged to reports/live-writes-*.jsonl.
usage: python .claude/qa-runs/phase3-20261015/run_135099.py"""
import subprocess, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.components.object_authoring_page import (
    ObjectAuthoringPage as OAP, STATUS_PUBLISHED, STATUS_UNPUBLISHED)
from cms.pages.home_hero_banner.hero_banner_fields_admin_page import HeroSlideFieldsAdminPage as Slide
from cms.tests.live_write_guard import LiveRecord, log_live_write

KEEP = "QCDEMO-129367-HERO_BANNER_SLIDE-01"
OTHERS = ["QCDEMO-129367-HERO_BANNER_SLIDE-02",
          "dcec133b-0cae-a689-d72e-554a97ae4665", "c5f0718a-15fc-9723-6bc8-6c8af62ef106",
          "c96bde36-2ff6-012b-b2bf-8130b1d4a483", "e3db10f0-7c70-ae06-d89c-a3ec0018a3e2",
          "5fa3277c-b7e9-9d2b-ba90-6e79bdf0a34b", "addb3c87-34a5-ddbb-8774-c129151cc80d",
          "1efe5520-552f-95a8-dffb-51e320f1d3e6"]
NODE = "web/tests/home_hero_banner/test_home_hero_banner_web.py::test_single_slide_static"


def status(a, code):
    a.open_list(ROLE_EDITOR)
    a._search_rows(code)
    return a.row_status_text_by_code(code) if a._row_locator(code).count() else "?"


def act(a, code, action):
    a.open_list(ROLE_EDITOR)
    a._search_rows(code)
    log_live_write(LiveRecord("hero-banner-slide", code, code), "<workflow>",
                   "Unpublished" if action == "unpublish" else "Published", "135099", action=action,
                   note="135099 precondition (QA lead approved); restored in finally")
    OAP._run_row_action(a, code, action, comment="QA 135099 single-slide check")


with sync_playwright() as pw:
    b = launch_browser(pw)
    pg = new_context(b, use_auth_state=False).new_page()
    pg.on("dialog", lambda d: d.accept())
    a = Slide(pg)
    before = {c: status(a, c) for c in [KEEP] + OTHERS}
    print("before:", before, flush=True)
    assert all(v == STATUS_PUBLISHED for v in before.values()), "not every slide is Published at the start — stopping"
    done = []
    try:
        for c in OTHERS:
            act(a, c, "unpublish")
            done.append(c)
        print("unpublished:", {c: status(a, c) for c in OTHERS}, flush=True)
        r = subprocess.run([sys.executable, "-m", "pytest", NODE, "-n", "0", "--timeout=300",
                            "--alluredir=reports/allure-129367-1018-135099", "--no-clean-evidence", "-q",
                            "-p", "no:cacheprovider"], capture_output=True, text=True)
        print("TEST:", (r.stdout.strip().splitlines() or ["?"])[-1], flush=True)
    finally:
        for c in done:
            try:
                if status(a, c) == STATUS_UNPUBLISHED:
                    act(a, c, "publish")
            except Exception as exc:  # noqa: BLE001
                print("RESTORE FAILED", c, repr(exc)[:120], flush=True)
        after = {c: status(a, c) for c in [KEEP] + OTHERS}
        print("after:", after, flush=True)
        print("NOT RESTORED:", [c for c, v in after.items() if v != STATUS_PUBLISHED], flush=True)
    b.close()

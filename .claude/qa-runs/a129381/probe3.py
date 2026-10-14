"""READ-ONLY. (1) Inspect leftover entry d3a2a34e-... (id 555085): form values, History, screenshot.
(2) Carousel autoplay: does hover or reduced-motion pause it?"""
import json, sys, time
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from config.settings import web_url
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage
CODE = "d3a2a34e-fa5f-a15f-960f-cc234158ab89"
out = {}
with sync_playwright() as pw:
    b = launch_browser(pw)
    ctx = new_context(b, use_auth_state=False); pg = ctx.new_page()
    a = StrategicPillarCardAdminPage(pg); a.sign_in("Site Content Editor")
    a.open_entry_by_code(CODE, locale="en")
    pg.wait_for_timeout(3000)
    out["url"] = pg.url
    out["inputs"] = pg.evaluate("() => Array.from(document.querySelectorAll('input[name^=ObjectField_], input[id^=qc-ar-], textarea')).map(e => [e.name||e.id, e.value])")
    out["textbox_title"] = pg.get_by_role("textbox", name=a.label_pattern("Pillar Title")).evaluate_all("els=>els.map(e=>[e.name||e.id,e.value])")
    out["banner"] = [l for l in pg.locator("body").inner_text().splitlines() if "Editing" in l or "editing" in l][:3]
    pg.screenshot(path="reports/manual-repro-129381-leftover-555085.png", full_page=True)
    a.open_entries_list(locale="en")
    try:
        out["history"] = a.history_entries(CODE)
    except Exception as e:
        out["history"] = repr(e)
    ctx.close()
    JS = "() => document.querySelector('.qc-sd-card.is-active .qc-sd-card-title')?.textContent"
    for mode in ("hover", "reduce"):
        ctx = new_context(b, use_auth_state=False)
        pg = ctx.new_page()
        if mode == "reduce":
            pg.emulate_media(reduced_motion="reduce")
        pg.goto(web_url("/home"), wait_until="domcontentloaded")
        pg.locator(".qc-sd-stage").wait_for(timeout=30000)
        pg.locator(".qc-sd-stage").scroll_into_view_if_needed()
        if mode == "hover":
            pg.locator(".qc-sd-stage").hover()
        seq = []
        for i in range(24):
            seq.append(pg.evaluate(JS)); pg.wait_for_timeout(750)
        out["autoplay_" + mode] = seq
        ctx.close()
    b.close()
open(".claude/qa-runs/a129381/probe3.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out, ensure_ascii=False)[:3000])

"""READ-ONLY manual repro (anonymous): (1) /ar/home arrow positions + which arrow advances;
(2) mobile touch swipe (CDP touch) and mouse drag on the card. Screenshots to reports/."""
import sys, json
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from config.settings import web_url
ACT = "() => document.querySelector('.qc-sd-card.is-active .qc-sd-card-title')?.textContent"
out = {}
with sync_playwright() as pw:
    b = launch_browser(pw)
    ctx = new_context(b, use_auth_state=False, viewport=(1920, 1080)); pg = ctx.new_page()
    pg.goto(web_url("/home", locale="ar"), wait_until="domcontentloaded")
    st = pg.locator(".qc-sd-stage"); st.wait_for(timeout=30000); st.scroll_into_view_if_needed(); st.hover()
    out["ar_dir"] = pg.evaluate("() => document.documentElement.dir")
    out["ar_arrows"] = pg.evaluate("() => ['.qc-sd-arrow--prev','.qc-sd-arrow--next'].map(s => { const e=document.querySelector(s); const r=e.getBoundingClientRect(); return [s, Math.round(r.x), e.getAttribute('aria-label'), e.innerHTML.slice(0,160)]; })")
    pg.locator(".qc-sd-carousel").screenshot(path="reports/manual-repro-129381-135629-ar-arrows.png")
    before = pg.evaluate(ACT)
    left = pg.evaluate("() => { const p=document.querySelector('.qc-sd-arrow--prev').getBoundingClientRect().x, n=document.querySelector('.qc-sd-arrow--next').getBoundingClientRect().x; return p < n ? '.qc-sd-arrow--prev' : '.qc-sd-arrow--next'; }")
    pg.locator(left).click(); pg.wait_for_timeout(1500); st.hover()
    out["ar_click_left_arrow"] = [left, before, pg.evaluate(ACT)]
    ctx.close()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True); pg = ctx.new_page()
    pg.goto(web_url("/home"), wait_until="domcontentloaded")
    st = pg.locator(".qc-sd-stage"); st.wait_for(timeout=30000); st.scroll_into_view_if_needed()
    box = st.bounding_box(); y = box["y"] + box["height"] / 2; x0 = box["x"] + box["width"] * .85; x1 = box["x"] + box["width"] * .15
    out["listeners_hint"] = pg.evaluate("() => { const s=document.querySelector('[data-qc-sd-carousel]'); return {touchAction: getComputedStyle(document.querySelector('.qc-sd-stage')).touchAction}; }")
    before = pg.evaluate(ACT)
    cdp = ctx.new_cdp_session(pg)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y}]})
    for i in range(1, 11):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * i / 10, "y": y}]})
        pg.wait_for_timeout(16)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(1500)
    out["touch_swipe"] = [before, pg.evaluate(ACT)]
    pg.screenshot(path="reports/manual-repro-129381-135547-after-swipe.png")
    before = pg.evaluate(ACT)
    pg.mouse.move(x0, y); pg.mouse.down(); pg.mouse.move(x1, y, steps=10); pg.mouse.up(); pg.wait_for_timeout(1500)
    out["mouse_drag"] = [before, pg.evaluate(ACT)]
    ctx.close(); b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))

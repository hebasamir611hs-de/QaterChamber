"""READ-ONLY. (a) anonymous /home + /ar/home: sample the active pillar card and card opacities
for 12 s right after load (autoplay?). Screenshots to reports/manual-repro-129381-*.png."""
import json, sys, time
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from config.settings import web_url
out = {}
JS = ("() => Array.from(document.querySelectorAll('.qc-sd-card')).map(e => ({t: e.querySelector('.qc-sd-card-title')?.textContent,"
      " a: e.classList.contains('is-active'), o: getComputedStyle(e).opacity}))")
with sync_playwright() as pw:
    b = launch_browser(pw)
    for loc in ("en", "ar"):
        ctx = new_context(b, use_auth_state=False)
        pg = ctx.new_page()
        t0 = time.time()
        pg.goto(web_url("/home", locale=loc), wait_until="domcontentloaded")
        pg.locator(".qc-sd-stage").wait_for(timeout=30000)
        samples = []
        for i in range(25):
            samples.append({"t": round(time.time() - t0, 1), "cards": pg.evaluate(JS)})
            if i == 0:
                pg.locator(".qc-sd-stage").scroll_into_view_if_needed()
                pg.screenshot(path=f"reports/manual-repro-129381-carousel-{loc}-t0.png")
            pg.wait_for_timeout(500)
        pg.screenshot(path=f"reports/manual-repro-129381-carousel-{loc}-t12.png")
        out[loc] = samples
        out[loc + "_attrs"] = pg.evaluate("() => { const s=document.querySelector('.qc-sd-carousel, .qc-sd-stage'); return s ? Array.from(s.attributes).map(a=>a.name+'='+a.value) : [] }")
        ctx.close()
    b.close()
open(".claude/qa-runs/a129381/probe2.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
for loc in ("en", "ar"):
    print(loc, [(s["t"], [c["t"] for c in s["cards"] if c["a"]], [c["o"] for c in s["cards"]]) for s in out[loc]][:25])

"""Manual repro (Rule 3) for the 136088 typography finding — logged-out, 1920x1080, EN. Read-only."""
import json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import web_url
SEL = [".qc-about-tag", ".qc-about-heading", ".qc-about-desc", ".qc-about-badge-num", ".qc-about-badge-label",
       ".qc-about-readmore", ".qc-about-achievements-title", ".qc-about-counter-value", ".qc-about-counter-label"]
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_context(viewport={"width": 1920, "height": 1080}).new_page()
    pg.goto(web_url("/", locale="en"), wait_until="domcontentloaded", timeout=60000)
    s = pg.locator("section.qc-home-about-us"); s.wait_for(timeout=30000); s.scroll_into_view_if_needed()
    pg.wait_for_timeout(3000)  # manual repro only: let the counter animation finish before the screenshot
    out = {sel: pg.locator(f"section.qc-home-about-us {sel}").first.evaluate(
        "el => { const c = getComputedStyle(el); return {text: el.innerText.slice(0,60), family: c.fontFamily, size: c.fontSize, weight: c.fontWeight, lh: c.lineHeight, color: c.color}; }") for sel in SEL}
    s.screenshot(path="reports/manual-repro-129389-136088.png")
    json.dump(out, open("reports/manual-repro-129389-136088.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    b.close()
print("ok")

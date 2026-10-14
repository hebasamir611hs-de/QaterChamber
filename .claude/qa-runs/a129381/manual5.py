"""Step-5 manual repro, READ-ONLY, PBI 129381.
(A) Anonymous /home (1920x1080): computed styles of the Strategic Direction
    section vs the Figma tokens (.claude/qa-runs/129381.figma.json) — screenshot.
(B) Editor: full Object Authoring sidebar listing + the pillar-card form, to
    evidence that no section-level object (Section Tag/Heading/Description) exists.
(C) Carousel DOM around the "progress indicator" (peek strips)."""
import json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from config.settings import web_url, control_panel_url
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage

JS = """() => {
 const cs = (sel) => { const e = document.querySelector(sel); if (!e) return null; const c = getComputedStyle(e); const r = e.getBoundingClientRect();
   return {sel, color: c.color, bg: c.backgroundColor, bgimg: c.backgroundImage.slice(0,80), border: c.borderTopColor + ' ' + c.borderTopWidth,
     font: c.fontFamily.split(',')[0] + ' ' + c.fontWeight + ' ' + c.fontSize + '/' + c.lineHeight, radius: c.borderTopLeftRadius,
     pad: c.padding, w: Math.round(r.width*10)/10, h: Math.round(r.height*10)/10, x: Math.round(r.x), opacity: c.opacity}; };
 return ['.qc-home-strategic-direction', '.qc-sd-tag', '.qc-sd-heading', '.qc-sd-desc', '.qc-sd-card.is-active', '.qc-sd-card.is-active .qc-sd-card-title',
   '.qc-sd-card.is-active .qc-sd-card-desc p', '.qc-sd-card.is-active .qc-sd-card-icon', '.qc-sd-arrow--prev', '.qc-sd-arrow--next',
   '.qc-sd-stage', '.qc-sd-carousel', '.qc-sd-peek--1', '.qc-sd-peek--2', '.qc-home-strategic-direction-img'].map(cs);
}"""
out = {}
with sync_playwright() as pw:
    b = launch_browser(pw)
    ctx = new_context(b, use_auth_state=False, viewport=(1920, 1080))
    pg = ctx.new_page()
    pg.goto(web_url("/home"), wait_until="domcontentloaded")
    pg.locator(".qc-sd-stage").wait_for(timeout=30000)
    pg.locator(".qc-sd-stage").scroll_into_view_if_needed()
    pg.locator(".qc-sd-stage").hover()
    pg.wait_for_timeout(1500)
    out["section_class"] = pg.evaluate("() => { const s = document.querySelector('.qc-sd-stage').closest('section'); return s ? s.className : null }")
    out["styles"] = pg.evaluate(JS)
    out["carousel_html"] = pg.evaluate("() => (document.querySelector('.qc-sd-carousel')||document.querySelector('.qc-sd-stage')).outerHTML.replace(/\\s+/g,' ').slice(0,3000)")
    pg.locator(".qc-sd-stage").screenshot(path="reports/manual-repro-129381-figma-card.png")
    sec = pg.locator(".qc-sd-stage").locator("xpath=ancestor::section[1]")
    (sec if sec.count() else pg.locator(".qc-sd-stage")).screenshot(path="reports/manual-repro-129381-figma-section.png")
    ctx.close()

    ctx = new_context(b, use_auth_state=False)
    pg = ctx.new_page()
    a = StrategicPillarCardAdminPage(pg)
    a.sign_in("Site Content Editor")
    pg.goto(control_panel_url("/en/web/qatar-chamber/object-authoring"), wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)
    out["authoring_links"] = sorted(set(pg.eval_on_selector_all(
        "a[href*='manage-']", "els => els.map(e => e.textContent.trim() + ' -> ' + e.getAttribute('href'))")))
    pg.screenshot(path="reports/manual-repro-129381-135538-object-authoring.png", full_page=True)
    a.open_new_entry_form(locale="en")
    pg.wait_for_timeout(2000)
    out["form_labels"] = [t.strip() for t in pg.locator("label").all_inner_texts() if t.strip()]
    pg.screenshot(path="reports/manual-repro-129381-135538-form.png", full_page=True)
    ctx.close()
    b.close()
open(".claude/qa-runs/a129381/manual5.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out, ensure_ascii=False, indent=1)[:9000])

"""Read-only evidence (under c7 lock). A) .qc-promo-dots hiding rule: CSS rules + JS that touch it,
anonymous, 1920 and 375 widths, screenshots that include the dots region. B) the submit-button label
on manage-promotional-banner for Editor and Author, with screenshots. No record is created."""
import json
import sys

sys.path.insert(0, r"D:\MCP servers\QaterChamper")
from playwright.sync_api import sync_playwright

from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url, web_url

R = r"D:\MCP servers\QaterChamper\reports"
CSS_JS = r"""() => {
  const d = document.querySelector('.qc-promo-dots');
  const out = {exists: !!d};
  if (!d) return out;
  const cs = getComputedStyle(d);
  out.display = cs.display; out.visibility = cs.visibility; out.opacity = cs.opacity;
  out.hidden_attr = d.hidden; out.style_attr = d.getAttribute('style'); out.class = d.className;
  out.parent_display = getComputedStyle(d.parentElement).display;
  out.dots = d.querySelectorAll('.qc-promo-dot').length;
  out.slides = document.querySelectorAll('.qc-promo-slide:not([data-clone])').length;
  out.rules = [];
  const walk = (rules, media) => { for (const r of rules) {
      if (r.cssRules && (r.media || r.conditionText)) { walk(r.cssRules, (r.conditionText || (r.media && r.media.mediaText) || '')); continue; }
      if (r.selectorText && r.selectorText.includes('qc-promo-dots')) {
        out.rules.push({media: media || '', selector: r.selectorText, css: r.style.cssText, matches: (() => { try { return d.matches(r.selectorText); } catch (e) { return null; } })()});
      } } };
  for (const sh of document.styleSheets) { try { walk(sh.cssRules, ''); } catch (e) { out.rules.push({sheet_blocked: sh.href}); } }
  out.scripts = [];
  for (const s of document.querySelectorAll('script:not([src])')) {
    const t = s.textContent; let i = t.indexOf('qc-promo-dots');
    while (i >= 0 && out.scripts.length < 6) { out.scripts.push(t.slice(Math.max(0, i - 300), i + 300)); i = t.indexOf('qc-promo-dots', i + 1); }
  }
  return out;
}"""

out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for w, h in ((1920, 1080), (375, 812)):
        ctx = b.new_context(viewport={"width": w, "height": h})
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        page.goto(web_url("/home"), wait_until="load")
        sec = page.locator("section.qc-home-promotional-banners")
        sec.wait_for(timeout=40000)
        sec.scroll_into_view_if_needed()
        info = page.evaluate(CSS_JS)
        info["errors"] = errs[:6]
        srcs = page.evaluate("() => Array.from(document.querySelectorAll('script[src]')).map(s => s.src)")
        hits = []
        for src in srcs:
            if "qatarchamber" not in src and "ihorizons" not in src and not src.startswith("/"):
                continue
            try:
                txt = page.request.get(src).text()
            except Exception:  # noqa: BLE001
                continue
            i = txt.find("qc-promo-dots")
            if i >= 0:
                hits.append({"src": src, "snippet": txt[max(0, i - 400): i + 400]})
        info["external_js_hits"] = hits[:3]
        sec.screenshot(path=rf"{R}\manual-repro-129368-dots-section-{w}.png")
        out[f"{w}"] = info
        open("repro4_partial.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False))
        ctx.close()
    for role, tag in (("Site Content Editor", "editor"), ("Site Content Author", "author")):
        ctx = b.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        CmsLoginPage(page).ensure_signed_in_as(*cms_role_credentials(role), control_panel_url("/en/home"))
        page.goto(control_panel_url("/en/web/qatar-chamber/manage-promotional-banner"), wait_until="domcontentloaded")
        btn = page.locator('button[type="submit"][name="status"]').last
        btn.wait_for(timeout=40000)
        out[f"button_{tag}"] = page.locator('button[type="submit"][name="status"]').all_inner_texts()
        btn.scroll_into_view_if_needed()
        box = btn.bounding_box()
        page.screenshot(path=rf"{R}\manual-repro-129368-submit-label-{tag}.png", full_page=True,
                        clip={"x": 0, "y": max(0, box["y"] + page.evaluate("window.scrollY") - 250), "width": 1920, "height": 400})
        ctx.close()
    b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))

"""READ-ONLY probe, PBI 129381. Signs in as Editor, reads manage-strategic-pillar-card list
and the object-authoring sidebar. Creates/edits/deletes NOTHING."""
import json, sys, re
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url

out = {}
with sync_playwright() as pw:
    b = launch_browser(pw)
    ctx = new_context(b, use_auth_state=False)
    pg = ctx.new_page()
    email, pw_ = cms_role_credentials("Site Content Editor")
    CmsLoginPage(pg).ensure_signed_in_as(email, pw_, control_panel_url("/en/home"))
    pg.goto(control_panel_url("/en/web/qatar-chamber/object-authoring"), wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)
    body = pg.locator("body").inner_text()
    out["sidebar_strategic_lines"] = [l for l in body.splitlines() if re.search("(?i)strateg|pillar|direction", l)]
    out["manage_links"] = sorted(set(h for h in pg.eval_on_selector_all("a[href*='manage-']", "els=>els.map(e=>e.getAttribute('href'))") if "strateg" in h.lower()))
    pg.goto(control_panel_url("/en/web/qatar-chamber/manage-strategic-pillar-card"), wait_until="domcontentloaded")
    pg.locator("table tbody tr").first.wait_for(timeout=35000)
    pg.wait_for_timeout(6000)
    rows = pg.locator("table tbody tr")
    out["rows"] = []
    for i in range(rows.count()):
        r = rows.nth(i)
        tds = [t.strip() for t in r.locator("td").all_inner_texts()]
        attrs = r.evaluate("el=>Array.from(el.querySelectorAll('[data-qc-oel-delete],[data-qc-oel-unpublish],[data-qc-oel-history],a')).map(a=>({t:a.textContent.trim().slice(0,30),attrs:Array.from(a.attributes).filter(x=>x.name.startsWith('data-qc')||x.name=='href').map(x=>x.name+'='+x.value)}))")
        out["rows"].append({"tds": tds, "links": attrs})
    out["pager_text"] = [t for t in pg.locator(".pagination, nav[aria-label*='agination'], [class*='pagin']").all_inner_texts()][:3]
    out["search_input"] = pg.locator('input[placeholder^="Search entries"]').count()
    out["body_tail"] = pg.locator("body").inner_text()[-1500:]
    # open first row's edit form read-only to capture labels
    first_code = out["rows"][0]["tds"][0] if out["rows"] else ""
    pg.goto(control_panel_url("/en/web/qatar-chamber/manage-strategic-pillar-card"), wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)
    pg.wait_for_timeout(2000)
    out["new_form_controls"] = pg.evaluate("""()=>Array.from(document.querySelectorAll('input,textarea,select,button,[role=textbox],iframe')).map(e=>({tag:e.tagName,type:e.type||'',id:e.id||'',name:e.name||'',aria:e.getAttribute('aria-label')||'',title:e.title||'',txt:(e.tagName=='BUTTON'?e.textContent.trim().slice(0,40):''),req:e.required||false})).filter(x=>x.tag!='BUTTON'||x.txt)""")
    out["new_form_labels"] = pg.locator("label").all_inner_texts()
    pg.screenshot(path="reports/probe-129381-new-form.png", full_page=True)
    ctx.close(); b.close()
open(".claude/qa-runs/a129381/probe1.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("ok")

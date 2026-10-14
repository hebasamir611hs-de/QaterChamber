"""Read-only recon for PBI 129389 (B-129389, 2026-10-07). Never clicks a save/submit
button, never deletes. Output: reports/recon-129389.json + screenshots."""
import json, sys, re, os
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import cms_role_credentials, control_panel_url, web_url
from cms.pages.control_panel.login_page import CmsLoginPage

OUT = {}
BASE = control_panel_url("/web/qatar-chamber/")


def form_dump(pg):
    return pg.evaluate("""() => {
      const out = {};
      document.querySelectorAll('form input, form textarea, form select').forEach(e => {
        if (!e.name || e.type === 'hidden' && !/ObjectField|file/i.test(e.name)) return;
        out[e.name + (e.type==='checkbox'?'[cb]':'')] = e.type==='checkbox' ? e.checked : (e.value||'').slice(0,300);
      });
      out.__buttons = [...document.querySelectorAll('button, a.btn')].map(b => (b.innerText||'').trim()).filter(t => t && t.length < 60);
      out.__banner = (document.querySelector('.alert, .qc-oa-banner, [class*=banner]')||{}).innerText || '';
      out.__iframes = [...document.querySelectorAll('iframe[title="editor"]')].length;
      out.__labels = [...document.querySelectorAll('label')].map(l => l.innerText.trim()).filter(Boolean).slice(0,80);
      return out;
    }""")


def list_dump(pg):
    return pg.evaluate("""() => ({
      rows: [...document.querySelectorAll('table tbody tr')].map(r => ({
        text: r.innerText.replace(/\\s+/g,' ').slice(0,300),
        actions: [...r.querySelectorAll('[data-qc-oel-delete],[data-qc-oel-unpublish],[data-qc-oel-publish],[data-qc-oel-history],a,button')]
                 .map(a => [...a.attributes].filter(x=>x.name.startsWith('data-qc-oel')).map(x=>x.name+'='+x.value).join(' ') || (a.innerText||'').trim()).filter(Boolean)
      })),
      body: document.body.innerText.slice(0,1500)
    })""")


def settle(pg):
    pg.wait_for_load_state("domcontentloaded", timeout=60000)
    pg.locator('table tbody tr, button[type="submit"]:text-is("Save as Draft"), button:has-text("Submit for Review"), button:has-text("Publish")').first.wait_for(timeout=90000)
    pg.wait_for_timeout(2000)  # recon only: let late-bound widgets render


def safe(fn, key):
    try:
        OUT[key] = fn()
    except Exception as e:  # noqa
        OUT[key] = f"ERROR {type(e).__name__}: {str(e)[:300]}"
    print(key, "->", str(OUT[key])[:400])


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    # 1. Public, logged-out
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    for loc in (() if os.environ.get("SKIP_PUBLIC") else ("en", "ar")):
        def pub(loc=loc):
            pg.goto(web_url("/", locale=loc), wait_until="domcontentloaded", timeout=60000)
            pg.locator("section.qc-home-about-us").wait_for(timeout=30000)
            pg.locator("section.qc-home-about-us").scroll_into_view_if_needed()
            pg.screenshot(path=f"reports/recon-129389-public-{loc}.png", full_page=False)
            return pg.evaluate("""() => { const s = document.querySelector('section.qc-home-about-us'); const q = c => [...s.querySelectorAll(c)];
              return { dir: document.documentElement.dir, tag: (s.querySelector('.qc-about-tag')||{}).innerText, heading: (s.querySelector('.qc-about-heading')||{}).innerText,
               desc: ((s.querySelector('.qc-about-desc')||{}).innerText||'').slice(0,300), badge: (s.querySelector('.qc-about-badge')||{}).innerText,
               readmore: (s.querySelector('.qc-about-readmore')||{}).href, readmore_text: (s.querySelector('.qc-about-readmore')||{}).innerText,
               imgs: q('.qc-about-collage-item img').map(i => i.src), ach_title: (s.querySelector('.qc-about-achievements-title')||{}).innerText,
               counters: q('.qc-about-counter').map(c => c.innerText.replace(/\\s+/g,' ')) } }""")
        safe(pub, f"public_{loc}")
    ctx.close()

    # 2. Editor
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Site Content Editor")
    safe(lambda: (CmsLoginPage(pg).open_login().login(em, pw), "ok")[1], "editor_login")
    for slug in ("about-us-section", "about-us-counter"):
        def lst(slug=slug):
            pg.goto(control_panel_url(f"/en/web/qatar-chamber/manage-{slug}"), timeout=60000)
            settle(pg)
            pg.screenshot(path=f"reports/recon-129389-editor-{slug}.png", full_page=True)
            d = list_dump(pg)
            d["url"] = pg.url
            d["form_on_bare_url"] = form_dump(pg)
            return d
        safe(lst, f"editor_list_{slug}")
    for code, slug in [("QCDEMO-129389-ABOUT_US_SECTION-01", "about-us-section")] + [
            (f"QCDEMO-129389-ABOUT_US_COUNTER-0{i}", "about-us-counter") for i in range(1, 5)]:
        def edit(code=code, slug=slug):
            pg.goto(control_panel_url(f"/en/web/qatar-chamber/manage-{slug}?editEntry={code}"), timeout=60000)
            settle(pg)
            d = form_dump(pg)
            try:
                d["__desc"] = [pg.frame_locator('iframe[title="editor"]').nth(i).locator("body").inner_text()[:400] for i in range(d["__iframes"])]
            except Exception as e:  # noqa
                d["__desc"] = str(e)[:200]
            return d
        safe(edit, f"editor_edit_{code}")
    # Add-New on counter list (if a link exists) — open only, never save
    def addnew_counter():
        pg.goto(control_panel_url("/en/web/qatar-chamber/manage-about-us-counter"), timeout=60000)
        settle(pg)
        links = pg.locator('a:has-text("Add New"), button:has-text("Add New"), a:has-text("Add"), a:has-text("Cancel and add a new entry instead")')
        info = {"candidates": [links.nth(i).inner_text() for i in range(links.count())]}
        if links.count():
            links.first.click()
            settle(pg)
            info["url"] = pg.url
            info["form"] = form_dump(pg)
            pg.screenshot(path="reports/recon-129389-editor-counter-addnew.png", full_page=True)
        return info
    safe(addnew_counter, "editor_addnew_counter")
    def addnew_section():
        pg.goto(control_panel_url("/en/web/qatar-chamber/manage-about-us-section"), timeout=60000)
        settle(pg)
        links = pg.locator('a:has-text("Add New"), button:has-text("Add New"), a:has-text("Cancel and add a new entry instead")')
        info = {"candidates": [links.nth(i).inner_text() for i in range(links.count())]}
        if links.count():
            links.first.click()
            settle(pg)
            info["url"] = pg.url
            info["form"] = form_dump(pg)
            pg.screenshot(path="reports/recon-129389-editor-section-addnew.png", full_page=True)
        return info
    safe(addnew_section, "editor_addnew_section")
    ctx.close()

    # 3. Author — read submit label + row actions
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Site Content Author")
    safe(lambda: (CmsLoginPage(pg).open_login().login(em, pw), "ok")[1], "author_login")
    for slug in ("about-us-section", "about-us-counter"):
        def alst(slug=slug):
            pg.goto(control_panel_url(f"/en/web/qatar-chamber/manage-{slug}"), timeout=60000)
            settle(pg)
            d = list_dump(pg); d["form_on_bare_url"] = form_dump(pg); d["url"] = pg.url
            return d
        safe(alst, f"author_list_{slug}")
    ctx.close()

    # 4. Site member — bare goto
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Site Member")
    safe(lambda: (CmsLoginPage(pg).open_login().login(em, pw), "ok")[1], "member_login")
    def mem():
        r = pg.goto(control_panel_url("/en/web/qatar-chamber/manage-about-us-section"), timeout=60000)
        pg.wait_for_load_state("domcontentloaded")
        pg.screenshot(path="reports/recon-129389-member.png")
        return {"status": r.status if r else None, "url": pg.url, "title": pg.title(),
                "forms": pg.locator("form input[name*=ObjectField]").count(),
                "rows": pg.locator("table tbody tr").count(), "body": pg.inner_text("body")[:400]}
    safe(mem, "member_section")
    ctx.close()
    # 5. Logged-out bare goto
    ctx = b.new_context(); pg = ctx.new_page()
    def anon():
        r = pg.goto(control_panel_url("/en/web/qatar-chamber/manage-about-us-section"), timeout=60000)
        return {"status": r.status if r else None, "url": pg.url, "title": pg.title(),
                "forms": pg.locator("form input[name*=ObjectField]").count(), "body": pg.inner_text("body")[:300]}
    safe(anon, "anon_section")
    ctx.close()
    b.close()

json.dump(OUT, open(os.environ.get("RECON_OUT","reports/recon-129389.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done")

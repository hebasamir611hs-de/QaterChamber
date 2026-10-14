"""Read-only recon #2 for PBI 129390 (B-129390, 2026-10-08). Never saves,
submits, publishes or deletes. Output: reports/recon2-129390.json,
reports/recon2-129390-fragment.js, screenshots reports/recon2-129390-*.png."""
import json, os, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import cms_role_credentials, control_panel_url, web_url, settings
from cms.pages.control_panel.login_page import CmsLoginPage

OUT = {}
SHOT = "reports/recon2-129390-{}.png"
J = "com_liferay_journal_web_portlet_JournalPortlet"
EDIT_53012 = (f"/en/group/qatar-chamber/~/control_panel/manage?p_p_id={J}&p_p_lifecycle=0&p_p_state=maximized"
              f"&_{J}_mvcRenderCommandName=/journal/edit_article&_{J}_articleId=53012&_{J}_groupId=37246")
WC_SEARCH = (f"/en/group/qatar-chamber/~/control_panel/manage?p_p_id={J}&p_p_lifecycle=0&p_p_state=maximized"
             f"&_{J}_keywords=Contact&_{J}_mvcPath=/view.jsp&_{J}_navigation=all&_{J}_delta=50")


def safe(fn, key):
    try:
        OUT[key] = fn()
    except Exception as e:  # noqa
        OUT[key] = f"ERROR {type(e).__name__}: {str(e)[:300]}"
    print(key, "->", str(OUT[key])[:400])


def rows(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('table tbody tr')].map(r => r.innerText.replace(/\\s+/g,' ').slice(0,300))""")


def labels(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('input,textarea,select')].filter(e => e.type !== 'hidden' && (e.offsetWidth||e.offsetHeight))
        .map(e => { const l = e.id && document.querySelector('label[for="'+e.id+'"]'); return {label: l ? l.innerText.trim() : (e.getAttribute('aria-label')||''),
          name: (e.name||'').slice(-40), type: e.type, value: (e.value||'').slice(0,200), required: e.required, maxlength: e.getAttribute('maxlength'),
          min: e.getAttribute('min'), checked: e.type==='checkbox' ? e.checked : undefined}; })""")


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    # 1. Anonymous home: every qcdev /o/ request + the full fragment script
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    calls = []
    def on_resp(r):
        if "/o/" in r.url and "qcdev" in r.url and r.request.resource_type in ("xhr", "fetch"):
            try:
                body = r.text()[:1500]
            except Exception:  # noqa
                body = ""
            calls.append({"url": r.url, "status": r.status, "body": body})
    pg.on("response", on_resp)
    def anon_home():
        pg.goto(web_url("/"), wait_until="domcontentloaded", timeout=60000)
        pg.locator("section.qc-home-contact-us").wait_for(timeout=30000)
        pg.locator("section.qc-home-contact-us").scroll_into_view_if_needed()
        pg.wait_for_timeout(4000)  # recon only: let the fragment's fetches finish
        scripts = [s for s in pg.evaluate("() => [...document.scripts].map(x => x.textContent)") if "QC Home Contact Us" in s]
        open("reports/recon2-129390-fragment.js", "w", encoding="utf-8").write("\n\n/* ---- */\n\n".join(scripts))
        return {"calls": calls, "script_chars": sum(len(s) for s in scripts)}
    safe(anon_home, "anon_home")
    ctx.close()

    # 2. Editor: Inquiry list, Inquiry Category page size 50, Web Content menu entry
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Site Content Editor")
    CmsLoginPage(pg).open_login().login(em, pw)
    for slug in ("inquiry", "inquiry-category"):
        def lst(slug=slug):
            pg.goto(control_panel_url(f"/en/web/qatar-chamber/manage-{slug}"), timeout=60000)
            pg.locator('table tbody tr, button:has-text("Save as Draft")').first.wait_for(timeout=90000)
            pg.wait_for_timeout(2000)
            sel = pg.locator("select").filter(has=pg.locator('option[value="50"]'))
            if sel.count():
                sel.first.select_option("50")
                pg.wait_for_timeout(2500)
            pg.screenshot(path=SHOT.format(f"editor-{slug}"), full_page=True)
            return {"rows": rows(pg), "form": labels(pg),
                    "total": pg.evaluate("() => (document.body.innerText.match(/\\d+\\s+total|Showing[^\\n]+/)||[''])[0]")}
        safe(lst, f"editor_{slug}")
    def ic_row():
        pg.goto(control_panel_url("/en/web/qatar-chamber/manage-inquiry-category?editEntry=QCDEMO-129390-INQCAT-01"), timeout=60000)
        pg.locator('button:has-text("Save as Draft"), button:has-text("Publish")').first.wait_for(timeout=90000)
        pg.wait_for_timeout(2000)
        return {"url": pg.url, "form": labels(pg), "banner": pg.evaluate("() => (document.querySelector('[class*=banner], .alert')||{}).innerText || ''")}
    safe(ic_row, "editor_ic_row01_view")
    ctx.close()

    # 3. Form Manager: Inquiry submissions list
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Form Manager")
    CmsLoginPage(pg).open_login().login(em, pw)
    def fm():
        pg.goto(control_panel_url("/en/web/qatar-chamber/manage-inquiry"), timeout=60000)
        pg.locator('table tbody tr, button:has-text("Save as Draft")').first.wait_for(timeout=90000)
        pg.wait_for_timeout(2000)
        pg.screenshot(path=SHOT.format("formmgr-inquiry"), full_page=True)
        return {"rows": rows(pg)[:30], "form": labels(pg)}
    safe(fm, "formmgr_inquiry")
    ctx.close()

    # 4. TEST_USER: article 53012 Arabic values (read only) + Web Content search
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    CmsLoginPage(pg).open_login().login(settings.test_user, settings.test_password)
    def art_ar():
        pg.goto(control_panel_url(EDIT_53012), timeout=60000)
        pg.get_by_label("Section Heading").first.wait_for(timeout=60000)
        pg.wait_for_timeout(2000)
        en = labels(pg)
        tb = pg.locator('button:has-text("en-US")').first
        tb.click()
        pg.wait_for_timeout(800)
        opts = pg.evaluate("() => [...document.querySelectorAll('[role=menuitem], .dropdown-item')].filter(e => e.offsetWidth).map(e => e.innerText.trim()).slice(0,20)")
        ar = None
        target = pg.locator('[role=menuitem]:has-text("ar-SA"), .dropdown-item:has-text("ar-SA"), [role=menuitem]:has-text("Arabic")')
        if target.count():
            target.first.click()
            pg.wait_for_timeout(2500)
            ar = labels(pg)
            pg.screenshot(path=SHOT.format("admin-article-ar"), full_page=True)
        return {"en": en, "locale_options": opts, "ar": ar}
    safe(art_ar, "admin_article_ar")
    def wc():
        pg.goto(control_panel_url(WC_SEARCH), timeout=60000)
        pg.wait_for_timeout(6000)
        pg.screenshot(path=SHOT.format("admin-wc-search"), full_page=True)
        return {"url": pg.url, "rows": rows(pg)[:40],
                "cards": pg.evaluate("() => [...document.querySelectorAll('.card, .list-group-item, li.entry-card')].map(e => e.innerText.replace(/\\s+/g,' ').slice(0,200)).slice(0,40)")}
    safe(wc, "admin_wc_search")
    pg.goto(control_panel_url("/c/portal/update_language?languageId=en_US"), timeout=60000)
    ctx.close()
    b.close()

json.dump(OUT, open("reports/recon2-129390.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done")

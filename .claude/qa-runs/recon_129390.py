"""Read-only recon for PBI 129390 (B-129390, 2026-10-08). Never clicks a save /
submit / publish / delete control in the CMS, and never submits the public form
with valid data (empty / invalid submits are blocked client-side, nothing is
sent). Output: reports/recon-129390.json + reports/recon-129390-*.png."""
import json, os, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import cms_role_credentials, control_panel_url, web_url, settings
from cms.pages.control_panel.login_page import CmsLoginPage

OUT = {}
SHOT = "reports/recon-129390-{}.png"
J = "com_liferay_journal_web_portlet_JournalPortlet"
EDIT_53012 = (f"/group/qatar-chamber/~/control_panel/manage?p_p_id={J}&p_p_lifecycle=0&p_p_state=maximized"
              f"&_{J}_mvcRenderCommandName=/journal/edit_article&_{J}_articleId=53012&_{J}_groupId=37246")
ADD_52431 = (f"/group/qatar-chamber/~/control_panel/manage?p_p_id={J}&p_p_lifecycle=0&p_p_state=maximized"
             f"&_{J}_mvcRenderCommandName=/journal/edit_article&_{J}_groupId=37246&_{J}_folderId=0"
             f"&_{J}_ddmStructureId=52431")
WC_LIST = f"/group/qatar-chamber/~/control_panel/manage?p_p_id={J}"
MANAGE_IC = "/en/web/qatar-chamber/manage-inquiry-category"


def safe(fn, key):
    try:
        OUT[key] = fn()
    except Exception as e:  # noqa
        OUT[key] = f"ERROR {type(e).__name__}: {str(e)[:300]}"
    print(key, "->", str(OUT[key])[:500])


def form_dump(pg):
    return pg.evaluate("""() => {
      const out = {inputs: []};
      document.querySelectorAll('input, textarea, select').forEach(e => {
        if (e.type === 'hidden') return;
        const id = e.id; let lab = '';
        if (id) { const l = document.querySelector('label[for="'+id+'"]'); if (l) lab = l.innerText.trim(); }
        if (!lab) lab = e.getAttribute('aria-label') || '';
        out.inputs.push({tag: e.tagName, type: e.type, name: (e.name||'').slice(-60), label: lab.slice(0,80),
          value: (e.value||'').slice(0,200), maxlength: e.getAttribute('maxlength'), required: e.required,
          checked: e.type==='checkbox' ? e.checked : undefined, visible: !!(e.offsetWidth||e.offsetHeight)});
      });
      out.buttons = [...document.querySelectorAll('button, a.btn')].map(b => (b.innerText||'').trim()).filter(t => t && t.length < 60).slice(0,60);
      out.labels = [...document.querySelectorAll('label')].map(l => l.innerText.trim()).filter(Boolean).slice(0,80);
      out.body = document.body.innerText.slice(0,1500);
      return out;
    }""")


def section_dump(pg):
    return pg.evaluate("""() => { const s = document.querySelector('section.qc-home-contact-us'); if (!s) return null;
      const q = c => [...s.querySelectorAll(c)];
      const form = s.querySelector('form');
      return { dir: document.documentElement.dir, tag: (s.querySelector('.qc-contact-tag')||{}).innerText,
        heading: (s.querySelector('.qc-contact-heading')||{}).innerText, desc: (s.querySelector('.qc-contact-desc')||{}).innerText,
        items: q('.qc-contact-item-text').map(i => i.innerText), form_title: (s.querySelector('.qc-contact-form-title')||{}).innerText,
        labels: q('label').map(l => l.innerText), options: q('#qc-cu-category option').map(o => o.value + '=' + o.innerText),
        submit: (s.querySelector('.qc-contact-submit')||{}).innerText, map_src: (s.querySelector('iframe')||{}).src,
        captcha_html: ((s.querySelector('.qc-field--captcha')||{}).outerHTML||'').slice(0,800),
        recaptcha_iframes: document.querySelectorAll('iframe[src*="recaptcha"]').length,
        grecaptcha: typeof window.grecaptcha, form_attrs: form ? [...form.attributes].map(a => a.name+'='+a.value) : null,
        section_attrs: [...s.attributes].map(a => a.name+'='+a.value.slice(0,200)),
        data_attrs: q('[data-endpoint],[data-action],[data-url],[data-qc-endpoint]').map(e => e.outerHTML.slice(0,300)),
        scripts: [...document.scripts].map(x => x.textContent).filter(t => /qc-cu-|contact/i.test(t)).map(t => t.slice(0,3000)) } }""")


def errors(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('section.qc-home-contact-us .qc-field')].map(f => ({
        field: (f.querySelector('input,select,textarea')||{}).id || f.className,
        err: ((f.querySelector('.qc-field-error')||{}).innerText||'').trim(),
        aria_invalid: (f.querySelector('input,select,textarea')||{getAttribute:()=>null}).getAttribute('aria-invalid') }))""")


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    # 1. Public, logged-out
    if not os.environ.get("SKIP_PUBLIC"):
        ctx = b.new_context(viewport={"width": 1920, "height": 1080})
        pg = ctx.new_page()
        reqs = []
        pg.on("request", lambda r: reqs.append(r.method + " " + r.url) if r.method != "GET" else None)
        for loc in ("en", "ar"):
            def pub(loc=loc):
                pg.goto(web_url("/", locale=loc), wait_until="domcontentloaded", timeout=60000)
                pg.locator("section.qc-home-contact-us").wait_for(timeout=30000)
                pg.locator("section.qc-home-contact-us").scroll_into_view_if_needed()
                pg.wait_for_timeout(1500)  # recon only
                pg.screenshot(path=SHOT.format(f"public-{loc}"))
                d = section_dump(pg)
                d["binding"] = pg.evaluate("""() => { const s = document.querySelector('section.qc-home-contact-us');
                  let n = s, chain = []; for (let i = 0; i < 8 && n; i++, n = n.parentElement) chain.push(n.tagName + '#' + n.id + '.' + (n.className||'').toString().slice(0,120) + ' ' + [...n.attributes].filter(a => /data-|article/i.test(a.name)).map(a => a.name+'='+a.value.slice(0,80)).join(' '));
                  const html = document.documentElement.outerHTML; const hits = {};
                  for (const k of ['53012','articleId','data-analytics-asset-id','52431','journal']) { const i = html.indexOf(k); hits[k] = i < 0 ? null : html.slice(Math.max(0,i-150), i+150); }
                  return {chain, hits}; }""")
                pg.locator("section.qc-home-contact-us .qc-contact-submit").click()
                pg.wait_for_timeout(800)
                d["empty_submit_errors"] = errors(pg)
                pg.fill("#qc-cu-email", "abc@")
                pg.fill("#qc-cu-name", "   ")
                pg.fill("#qc-cu-message", "   ")
                pg.locator("section.qc-home-contact-us .qc-contact-submit").click()
                pg.wait_for_timeout(800)
                d["ws_invalid_errors"] = errors(pg)
                pg.fill("#qc-cu-email", "   ")
                pg.locator("section.qc-home-contact-us .qc-contact-submit").click()
                pg.wait_for_timeout(800)
                d["email_ws_errors"] = errors(pg)
                d["status"] = pg.inner_text("section.qc-home-contact-us .qc-contact-status")
                pg.screenshot(path=SHOT.format(f"public-{loc}-errors"))
                return d
            safe(pub, f"public_{loc}")
        OUT["public_nonget_requests"] = reqs[:40]
        ctx.close()

    # 2. Editor
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Site Content Editor")
    safe(lambda: (CmsLoginPage(pg).open_login().login(em, pw), "ok")[1], "editor_login")

    def oa_index():
        pg.goto(control_panel_url("/en/web/qatar-chamber/object-authoring"), timeout=60000)
        pg.wait_for_load_state("domcontentloaded"); pg.wait_for_timeout(4000)
        links = pg.evaluate("""() => [...document.querySelectorAll('a')].map(a => (a.innerText||'').trim()+' => '+a.getAttribute('href'))
              .filter(t => /manage-/.test(t))""")
        pg.screenshot(path=SHOT.format("editor-oa-index"), full_page=True)
        return {"count": len(links), "contactish": [l for l in links if any(k in l.lower() for k in ("contact", "inquir", "enquir", "submission", "form"))],
                "all": links}
    safe(oa_index, "editor_oa_index")

    def ic_list():
        r = pg.goto(control_panel_url(MANAGE_IC), timeout=60000)
        pg.wait_for_load_state("domcontentloaded")
        pg.locator('table tbody tr, button:has-text("Save as Draft")').first.wait_for(timeout=90000)
        pg.wait_for_timeout(2500)
        pg.screenshot(path=SHOT.format("editor-inquiry-category"), full_page=True)
        rows = pg.evaluate("""() => [...document.querySelectorAll('table tbody tr')].map(r => r.innerText.replace(/\\s+/g,' ').slice(0,250))""")
        return {"status": r.status if r else None, "url": pg.url, "rows": rows, "form": form_dump(pg)}
    safe(ic_list, "editor_inquiry_category")

    for key, path in (("editor_article_53012", EDIT_53012), ("editor_wc_list", WC_LIST)):
        def art(path=path, key=key):
            r = pg.goto(control_panel_url("/en" + path), timeout=60000)
            pg.wait_for_load_state("domcontentloaded"); pg.wait_for_timeout(6000)
            pg.screenshot(path=SHOT.format(key), full_page=True)
            d = form_dump(pg); d["status"] = r.status if r else None; d["url"] = pg.url
            return d
        safe(art, key)
    ctx.close()

    # 3. TEST_USER (super-admin) — only to read whether the article's Fields render
    #    and whether a same-structure article can be opened for creation (no save).
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text[:200]) if m.type == "error" else None)
    safe(lambda: (CmsLoginPage(pg).open_login().login(settings.test_user, settings.test_password), "ok")[1], "admin_login")
    for key, path in (("admin_article_53012", EDIT_53012), ("admin_add_52431", ADD_52431)):
        def art2(path=path, key=key):
            r = pg.goto(control_panel_url("/en" + path), timeout=60000)
            pg.wait_for_load_state("domcontentloaded"); pg.wait_for_timeout(8000)
            pg.screenshot(path=SHOT.format(key), full_page=True)
            d = form_dump(pg); d["status"] = r.status if r else None; d["url"] = pg.url
            d["console_errors"] = errs[-10:]
            return d
        safe(art2, key)
    ctx.close()

    def headless(pg, key):
        out = {}
        for k, u in (("structure", "/o/headless-delivery/v1.0/content-structures/52431"),
                     ("article", "/o/headless-delivery/v1.0/sites/37246/structured-contents/by-key/53012"),
                     ("same_structure", "/o/headless-delivery/v1.0/content-structures/52431/structured-contents?pageSize=50"),
                     ("ic_object", "/o/c/inquirycategories?pageSize=50")):
            try:
                r = pg.request.get(control_panel_url(u), headers={"Accept": "application/json"})
                out[k] = {"status": r.status, "body": r.text()[:6000]}
            except Exception as e:  # noqa
                out[k] = str(e)[:200]
        return out

    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    CmsLoginPage(pg).open_login().login(settings.test_user, settings.test_password)
    safe(lambda: headless(pg, "admin"), "admin_headless")
    ctx.close()

    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Form Manager")
    safe(lambda: (CmsLoginPage(pg).open_login().login(em, pw), "ok")[1], "formmgr_login")
    safe(oa_index, "formmgr_oa_index")
    ctx.close()

    # 4. Site member, 5. anonymous — bare goto, no session guard
    for who in ("member", "anon"):
        ctx = b.new_context(viewport={"width": 1920, "height": 1080})
        pg = ctx.new_page()
        if who == "member":
            em, pw = cms_role_credentials("Site Member")
            safe(lambda: (CmsLoginPage(pg).open_login().login(em, pw), "ok")[1], "member_login")
        for key, path in (("ic", MANAGE_IC), ("article", "/en" + EDIT_53012), ("oa", "/en/web/qatar-chamber/object-authoring")):
            def bare(path=path):
                r = pg.goto(control_panel_url(path), timeout=60000)
                pg.wait_for_load_state("domcontentloaded"); pg.wait_for_timeout(2500)
                pg.screenshot(path=SHOT.format(f"{who}-{key}"))
                return {"status": r.status if r else None, "url": pg.url, "title": pg.title(),
                        "object_fields": pg.locator('[name*="ObjectField_"]').count(),
                        "rows": pg.locator("table tbody tr").count(),
                        "buttons": pg.locator('button:text-is("Publish"), button:text-is("Save as Draft"), button:text-is("Submit for Review")').count(),
                        "body": pg.inner_text("body")[:400]}
            safe(bare, f"{who}_{key}")
        ctx.close()
    b.close()

json.dump(OUT, open(os.environ.get("RECON_OUT", "reports/recon-129390.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done")

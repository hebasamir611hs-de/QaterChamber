"""Locator probe for the Journal 'Contact Us Section' create / save / delete flow
(B-129390, 2026-10-08). Account: TEST_USER (the only account that can open
Web Content). Writes ONE disposable article titled QCTEST-129390-PROBE, Save as
Draft only (never Publish), then moves it to the Recycle Bin by exact title
and re-lists. Never touches article 53012. Output: reports/probe-129390.json."""
import json, sys, time
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import control_panel_url, settings
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_contact_us.home_contact_us_admin_page import NEW_ARTICLE_PATH, WEB_CONTENT_PATH, _J

TITLE = "QCTEST-129390-PROBE"
OUT = {}
SHOT = "reports/probe-129390-{}.png"


def step(key, fn):
    try:
        OUT[key] = fn()
    except Exception as e:  # noqa
        OUT[key] = f"ERROR {type(e).__name__}: {str(e)[:400]}"
    print(key, "->", str(OUT[key])[:600])


def ddm(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('[name*="ddm$$"]')].map(e => ({name: e.name.split('ddm$$')[1],
        visible: !!(e.offsetWidth||e.offsetHeight), value: (e.value||'').slice(0,80), tag: e.tagName}))""")


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    dialogs = []
    pg.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
    CmsLoginPage(pg).open_login().login(settings.test_user, settings.test_password)

    def open_new():
        pg.goto(control_panel_url(NEW_ARTICLE_PATH), timeout=60000)
        pg.locator('[name*="ddm$$sectionHeading$"]').first.wait_for(timeout=60000)
        pg.wait_for_timeout(2000)
        return {"ddm": ddm(pg), "toolbar_locale_buttons": pg.locator('button:has-text("en-US")').count()}
    step("open_new", open_new)

    def fill_en():
        pg.locator(f'input[name="_{_J}_titleMapAsXML"]').fill(TITLE)
        pg.locator('[name*="ddm$$sectionTag$"]').first.fill("Get in touch")
        pg.locator('[name*="ddm$$sectionHeading$"]').first.fill(TITLE + " heading")
        for ref, v in (("emailSupportAddress", "support@qcci.org"), ("telephoneNumber", "+974 44559111"),
                       ("locationAddress", "Lusail Boulevard 69, Doha, Qatar"), ("formRecipientEmail", "heba.samir611.hs@gmail.com"),
                       ("sendMessageButtonLabel", "Send Message")):
            pg.locator(f'[name*="ddm$${ref}$"]:visible').first.fill(v)
        return {"title": pg.locator(f'input[name="_{_J}_titleMapAsXML"]').input_value()}
    step("fill_en", fill_en)

    def locale_menu():
        btns = pg.locator('button:has-text("en-US")')
        info = {"count": btns.count(), "boxes": [btns.nth(i).bounding_box() for i in range(btns.count())]}
        btns.first.click()
        pg.wait_for_timeout(800)
        info["items"] = pg.evaluate("""() => [...document.querySelectorAll('[role=menuitem], .dropdown-item, [role=option]')]
            .filter(e => e.offsetWidth).map(e => (e.innerText||'').trim().replace(/\\s+/g,' ')).slice(0,40)""")
        pg.screenshot(path=SHOT.format("locale-menu"))
        return info
    step("locale_menu", locale_menu)

    def to_ar():
        item = pg.locator('[role=menuitem]:visible, .dropdown-item:visible, [role=option]:visible').filter(has_text="ar-SA").first
        item.click()
        pg.wait_for_timeout(2500)
        pg.screenshot(path=SHOT.format("ar"), full_page=True)
        return {"ddm": ddm(pg), "toolbar": pg.locator('button:has-text("ar-SA")').count()}
    step("to_ar", to_ar)

    def fill_ar():
        for ref, v in (("sectionTag", "تواصل معنا"), ("sectionHeading", TITLE + " عنوان"),
                       ("locationAddress", "الدوحة، قطر"), ("sendMessageButtonLabel", "إرسال الرسالة")):
            pg.locator(f'[name*="ddm$${ref}$"]:visible').first.fill(v)
        return {"ddm": ddm(pg)}
    step("fill_ar", fill_ar)

    def save():
        start = pg.url
        pg.locator('button:has-text("Save as Draft")').first.click()
        modal = pg.locator('.modal-dialog:visible, [role=dialog]:visible')
        try:
            modal.first.wait_for(timeout=8000)
            OUT["modal_title"] = modal.first.inner_text()[:200]
            modal.first.locator('button:has-text("Save as Draft")').click()
        except Exception as e:  # noqa
            OUT["modal_title"] = f"no modal {type(e).__name__}"
        pg.wait_for_load_state("domcontentloaded", timeout=60000)
        t0 = time.time()
        while time.time() - t0 < 45:
            if pg.locator('.alert-success, .alert-danger, [role=alert]').count():
                break
            pg.wait_for_timeout(500)
        pg.wait_for_timeout(1500)
        pg.screenshot(path=SHOT.format("after-save"), full_page=True)
        return {"start": start, "url": pg.url, "alerts": pg.locator('.alert, [role=alert]').all_inner_texts()[:5],
                "dialogs": dialogs[-3:], "elapsed": round(time.time() - t0, 1),
                "body_head": pg.inner_text("body")[:800]}
    step("save", save)

    def listing():
        pg.goto(control_panel_url(WEB_CONTENT_PATH + f"&_{_J}_keywords={TITLE}&_{_J}_navigation=all"), timeout=60000)
        pg.wait_for_load_state("networkidle")
        pg.wait_for_timeout(2000)
        pg.screenshot(path=SHOT.format("list"), full_page=True)
        hits = pg.locator(f'text="{TITLE}"')
        info = {"hits": hits.count(), "url": pg.url}
        if hits.count():
            h = hits.first
            info["hit_tag"] = h.evaluate("e => e.tagName + '.' + e.className")
            info["ancestors"] = h.evaluate("""e => { const out = []; let n = e; for (let i = 0; i < 8 && n; i++, n = n.parentElement)
                out.push(n.tagName + '.' + (n.className||'').toString().slice(0,80)); return out; }""")
            row = h.locator("xpath=ancestor::*[self::tr or self::li or contains(@class,'card') or contains(@class,'list-group-item')][1]")
            info["row_html"] = row.evaluate("e => e.outerHTML.slice(0, 2500)")
            info["row_buttons"] = row.locator("button").evaluate_all("els => els.map(b => (b.getAttribute('aria-label')||'') + '|' + (b.title||'') + '|' + b.className)")
        return info
    step("list", listing)

    def delete():
        hits = pg.locator(f'text="{TITLE}"')
        if not hits.count():
            return "no hit"
        row = hits.first.locator("xpath=ancestor::*[self::tr or self::li or contains(@class,'card') or contains(@class,'list-group-item')][1]")
        row.locator("button.dropdown-toggle, button[aria-haspopup], button[aria-label*='ction']").first.click()
        pg.wait_for_timeout(800)
        items = pg.evaluate("""() => [...document.querySelectorAll('[role=menuitem], .dropdown-item')].filter(e => e.offsetWidth)
            .map(e => (e.innerText||'').trim())""")
        pg.screenshot(path=SHOT.format("row-menu"))
        target = pg.locator('[role=menuitem]:has-text("Move to Recycle Bin"), .dropdown-item:has-text("Move to Recycle Bin"),'
                            '[role=menuitem]:text-is("Delete"), .dropdown-item:text-is("Delete")').first
        target.click()
        pg.wait_for_load_state("networkidle")
        pg.wait_for_timeout(2500)
        return {"menu": items, "dialogs": dialogs[-2:], "alerts": pg.locator('.alert, [role=alert]').all_inner_texts()[:3]}
    step("delete", delete)

    def relist():
        pg.goto(control_panel_url(WEB_CONTENT_PATH + f"&_{_J}_keywords={TITLE}&_{_J}_navigation=all"), timeout=60000)
        pg.wait_for_load_state("networkidle")
        pg.wait_for_timeout(2000)
        pg.screenshot(path=SHOT.format("relist"), full_page=True)
        return {"hits": pg.locator(f'text="{TITLE}"').count()}
    step("relist", relist)
    pg.goto(control_panel_url("/c/portal/update_language?languageId=en_US"), timeout=60000)
    ctx.close()
    b.close()

json.dump(OUT, open("reports/probe-129390.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done")

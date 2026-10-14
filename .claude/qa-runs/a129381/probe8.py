"""QCTEST-only. Exact test path ADMIN.create(title, submit=False) inside a TEST_USER-storageState
context (like the pytest `page` fixture), logging every non-GET request body and the title inputs
right before the save click. Then guarded delete."""
import sys, json, logging
sys.path.insert(0, ".")
logging.basicConfig(level=logging.WARNING)
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage
T = "QCTEST-129381-probe8"
log = []
with sync_playwright() as pw:
    b = launch_browser(pw); ctx = new_context(b, use_auth_state=True); pg = ctx.new_page()
    def onreq(r):
        if r.method != "GET" and ("/o/" in r.url or "manage" in r.url):
            log.append(f"{r.method} {r.url[:140]} BODY={(r.post_data or '')[:700]}")
    pg.on("request", onreq)
    pg.on("response", lambda r: log.append(f"  <- {r.status} {r.url[:120]}") if r.request.method != "GET" and "/o/" in r.url else None)
    a = StrategicPillarCardAdminPage(pg)
    a.open_form("Site Content Editor")
    a.fill_required(T, active=True, files=a.FILES)
    log.append("BEFORE SAVE: " + json.dumps(pg.evaluate("() => Array.from(document.querySelectorAll('input[name^=ObjectField_], input[id^=qc-ar-]')).map(e => [e.name||e.id, e.value])"), ensure_ascii=False))
    a.save_as_draft()
    log.append("URL AFTER SAVE: " + pg.url)
    pg.wait_for_timeout(5000)
    log.append("FORM AFTER SAVE: " + json.dumps(pg.evaluate("() => Array.from(document.querySelectorAll('input[name^=ObjectField_], input[id^=qc-ar-]')).map(e => [e.name||e.id, e.value])"), ensure_ascii=False))
    log.append("BANNER: " + str([l for l in pg.locator("body").inner_text().splitlines() if "Editing" in l][:1]))
    log.append("CODES: " + str(a._codes))
    log.append("CODE_FOR: " + a.code_for(T, refresh=True, wait=False))
    log.append("DELETE: " + str(a.delete_disposable(T)))
    ctx.close(); b.close()
print("\n".join(log))

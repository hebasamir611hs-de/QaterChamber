"""Find (and, only if its title is exactly QCTEST-129390-PROBE, delete) the
disposable probe article (B-129390, 2026-10-08). The Web Content list shows
"Web Content is temporarily unavailable.", so this uses the plain list URL and
the headless-delivery API (Basic auth as TEST_USER). Output reports/probe4-129390.json."""
import base64, json, os, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import control_panel_url, settings
from cms.pages.control_panel.login_page import CmsLoginPage

TITLE = "QCTEST-129390-PROBE"
DO_DELETE = os.environ.get("DO_DELETE") == "1"
OUT = {}
J = "com_liferay_journal_web_portlet_JournalPortlet"
AUTH = {"Authorization": "Basic " + base64.b64encode(f"{settings.test_user}:{settings.test_password}".encode()).decode(),
        "Accept": "application/json"}


def step(k, fn):
    try:
        OUT[k] = fn()
    except Exception as e:  # noqa
        OUT[k] = f"ERROR {type(e).__name__}: {str(e)[:300]}"
    print(k, "->", json.dumps(OUT[k], ensure_ascii=False)[:1500])


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    CmsLoginPage(pg).open_login().login(settings.test_user, settings.test_password)

    def plain_list():
        pg.goto(control_panel_url(f"/en/group/qatar-chamber/~/control_panel/manage?p_p_id={J}"), timeout=60000)
        pg.wait_for_timeout(5000)
        pg.screenshot(path="reports/probe4-129390-list.png", full_page=True)
        return {"body": pg.inner_text("body")[:800], "probe_hits": pg.locator(f'text="{TITLE}"').count()}
    step("plain_list", plain_list)

    def api(path, method="GET"):
        r = pg.request.fetch(control_panel_url(path), method=method, headers=AUTH)
        return {"status": r.status, "body": r.text()[:4000]}

    step("by_structure", lambda: api("/o/headless-delivery/v1.0/content-structures/52431/structured-contents?pageSize=100&fields=id,title,key,dateCreated,dateModified"))
    step("site_search", lambda: api(f"/o/headless-delivery/v1.0/sites/37246/structured-contents?search={TITLE}&fields=id,title,key,contentStructureId,dateCreated&flatten=true"))

    def maybe_delete():
        res = OUT.get("by_structure")
        if not isinstance(res, dict) or res.get("status") != 200:
            return "no structure listing"
        items = json.loads(res["body"]).get("items", []) if res["body"].strip().startswith("{") else []
        hits = [i for i in items if i.get("title") == TITLE]
        out = {"hits": hits}
        if DO_DELETE:
            for h in hits:
                assert h["title"].startswith("QCTEST-"), h
                out[f"delete_{h['id']}"] = api(f"/o/headless-delivery/v1.0/structured-contents/{h['id']}", "DELETE")
                out[f"after_{h['id']}"] = api(f"/o/headless-delivery/v1.0/structured-contents/{h['id']}?fields=id,title")
        return out
    step("probe_article", maybe_delete)
    ctx.close()
    b.close()
json.dump(OUT, open("reports/probe4-129390.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done")

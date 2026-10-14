"""READ-ONLY. Headless GET of all Strategic Pillar Card entries (as Editor session) to see real
titles/status/ids, plus pager/page-size HTML. No writes."""
import sys, json
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from config.settings import control_panel_url
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage
out = {}
with sync_playwright() as pw:
    b = launch_browser(pw); ctx = new_context(b, use_auth_state=False); pg = ctx.new_page()
    a = StrategicPillarCardAdminPage(pg); a.sign_in("Site Content Editor")
    for path in ("/o/c/strategicpillarcards/scopes/37246?pageSize=200&nestedFields=&flatten=true",
                 "/o/c/strategicpillarcards/scopes/37246?pageSize=200&search=QCTEST"):
        try:
            r = pg.request.get(control_panel_url(path), headers={"Accept": "application/json", "Accept-Language": "en-US"})
            j = r.json()
            out[path] = {"status": r.status, "total": j.get("totalCount"), "items": [
                {k: it.get(k) for k in ("id", "externalReferenceCode", "pillarTitle", "pillarTitle_i18n", "displayOrder", "activeStatus", "status", "dateCreated", "creator")}
                for it in j.get("items", [])]}
            for it in out[path]["items"]:
                if isinstance(it.get("status"), dict): it["status"] = it["status"].get("label")
                if isinstance(it.get("creator"), dict): it["creator"] = it["creator"].get("name")
        except Exception as e:  # noqa: BLE001
            out[path] = repr(e)[:300]
    try:
        a.open_entries_list(locale="en"); pg.wait_for_timeout(3000)
        out["selects"] = pg.evaluate("() => Array.from(document.querySelectorAll('select')).map(s => s.outerHTML.slice(0,500))")
        out["total_text"] = [t for t in pg.locator("body").inner_text().splitlines() if "total" in t.lower()][:5]
    except Exception as e:  # noqa: BLE001
        out["list"] = repr(e)[:300]
    ctx.close(); b.close()
print(json.dumps(out, ensure_ascii=False, indent=1)[:12000])

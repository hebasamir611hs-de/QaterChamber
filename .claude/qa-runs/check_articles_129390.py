"""Read-only: try to locate QCTEST-129390-PROBE / -GATE / -136543 by exact title (B-129390)."""
import base64, json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import control_panel_url, settings
from cms.pages.control_panel.login_page import CmsLoginPage
J = "com_liferay_journal_web_portlet_JournalPortlet"
T = ["QCTEST-129390-PROBE", "QCTEST-129390-GATE", "QCTEST-129390-136543"]
AUTH = {"Authorization": "Basic " + base64.b64encode(f"{settings.test_user}:{settings.test_password}".encode()).decode(), "Accept": "application/json"}
OUT = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True); pg = b.new_context(viewport={"width": 1920, "height": 1080}).new_page()
    CmsLoginPage(pg).open_login().login(settings.test_user, settings.test_password)
    pg.goto(control_panel_url(f"/en/group/qatar-chamber/~/control_panel/manage?p_p_id={J}"), timeout=60000); pg.wait_for_timeout(5000)
    body = pg.inner_text("body"); pg.screenshot(path="reports/cleanup-129390-wc-list.png")
    OUT["wc_list_unavailable"] = "temporarily unavailable" in body
    OUT["wc_list_hits"] = {t: pg.locator(f'text="{t}"').count() for t in T}
    for t in T:
        r = pg.request.get(control_panel_url(f"/o/headless-delivery/v1.0/sites/37246/structured-contents?search={t}&fields=id,title,key"), headers=AUTH)
        OUT[t] = [i for i in r.json().get("items", []) if i.get("title") == t] if r.status == 200 else r.status
    b.close()
print(json.dumps(OUT, ensure_ascii=False)); json.dump(OUT, open("reports/cleanup-129390-articles.json", "w"), indent=1)

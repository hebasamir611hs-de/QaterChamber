"""Gate #2 for PBI 129390 (B-129390, 2026-10-08), under the c7 lock, after the
save-outcome heal. (1) Round-trip one fresh QCTEST article: Save as Draft ->
articleId -> GET by-key -> DELETE -> 404. (2) Find the two earlier QCTEST
drafts that may exist (QCTEST-129390-PROBE 03:05, QCTEST-129390-GATE 03:29;
their saves were still in flight when their browser closed) by reading
by-key GETs on the articleIds just below the new one, and delete ONLY exact
QCTEST-129390-PROBE / QCTEST-129390-GATE titles. Output reports/gate2-129390.json"""
import json, sys, time
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import settings
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_contact_us.home_contact_us_admin_page import ContactUsSectionArticlePage

ORPHANS = {"QCTEST-129390-PROBE", "QCTEST-129390-GATE"}
OUT = {"ok": False}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    CmsLoginPage(pg).open_login().login(settings.test_user, settings.test_password)
    art = ContactUsSectionArticlePage(pg)
    title = "QCTEST-129390-GATE2"
    t0 = time.time()
    art.open_new_article()
    art.set_title(title)
    art.fill_all_valid(title, "en_US")
    res = art.save_as_draft()
    res["seconds"] = round(time.time() - t0, 1)
    pg.screenshot(path="reports/gate2-129390-save.png")
    OUT["save"] = res
    print("save", json.dumps(res)[:600])
    aid = res.get("article_id")
    if aid:
        OUT["lookup"] = art.lookup_article(aid)
        OUT["delete"] = art.delete_qctest_article(aid, title)
        OUT["ok"] = bool(res["saved"] and OUT["delete"].get("gone"))
        print("lookup", OUT["lookup"], "delete", OUT["delete"])
        if aid.isdigit():
            found, scanned = [], 0
            for k in range(int(aid) - 1, int(aid) - 8000, -1):
                scanned += 1
                look = art.lookup_article(str(k))
                if look["status"] == 200 and (look.get("title") or "").startswith("QCTEST-129390-"):
                    found.append({"article_id": str(k), **look,
                                  "delete": art.delete_qctest_article(str(k), look["title"])})
                    print("orphan", found[-1])
                    if len(found) >= 12:
                        break
            OUT["orphan_scan"] = {"scanned": scanned, "found": found}
    ctx.close()
    b.close()
json.dump(OUT, open("reports/gate2-129390.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("GATE_OK" if OUT["ok"] else "GATE_FAIL")
print("done")

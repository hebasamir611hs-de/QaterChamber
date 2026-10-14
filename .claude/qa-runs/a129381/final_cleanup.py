"""(1) Evidence for 135622: status + Active flag + public presence of QCTEST-129381-m9-active
(Editor unticked Active and published it in manual9). (2) Guarded delete of every entry whose own
form reads a title in this PBI's QCTEST namespace (all copies). (3) Final listing with statuses."""
import re, sys, json
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from config.settings import web_url
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage
MINE = re.compile(r"^QCTEST-(1355\d\d|1356\d\d|129381)-")
out = {}
with sync_playwright() as pw:
    b = launch_browser(pw); ctx = new_context(b, use_auth_state=False); pg = ctx.new_page()
    a = StrategicPillarCardAdminPage(pg); a.sign_in("Site Content Editor")
    t = "QCTEST-129381-m9-active"
    out["m9_active_status"] = a.raw_row_status(t)
    try:
        a.open_by_title(t); out["m9_active_flag"] = a.flag("active_status")
        pg.screenshot(path="reports/manual-repro-129381-135622-form-after-untick.png", full_page=True)
    except Exception as e:  # noqa: BLE001
        out["m9_active_flag"] = repr(e)[:200]
    actx = new_context(b, use_auth_state=False); anon = actx.new_page()
    seen = []
    for _ in range(2):
        anon.goto(web_url("/home"), wait_until="domcontentloaded"); anon.wait_for_timeout(4000)
        seen.append(t in anon.locator("body").inner_text())
    out["m9_active_public"] = seen
    actx.close()
    a.open_entries_list(locale="en"); a.filter_entries("")
    rows = [(c, i) for c, i in a._row_codes() if not c.startswith(a.REAL_CODE_PREFIX)]
    titles = sorted({a._read_title(c) or "" for c, i in rows} - {""})
    out["titled_found"] = titles
    out["deleted"] = {}
    for title in titles:
        if MINE.match(title):
            try:
                out["deleted"][title] = a.delete_disposable(title)
            except Exception as e:  # noqa: BLE001
                out["deleted"][title] = repr(e)[:200]
    a._UNTITLED.clear()
    a.open_entries_list(locale="en"); a.filter_entries("")
    st = [x.strip() for x in pg.locator("table tbody tr td:nth-child(2)").all_inner_texts()]
    left = []
    for (c, i), s in zip(a._row_codes(), st):
        if not c.startswith(a.REAL_CODE_PREFIX):
            left.append([i, c, s, a._read_title(c)])
    out["left"] = left
    ctx.close(); b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))

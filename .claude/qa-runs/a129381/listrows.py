"""READ-ONLY. As Editor: list manage-strategic-pillar-card rows; for each non-QCDEMO row open its
form and read Pillar Title (EN). Reports leftovers. Deletes nothing."""
import json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage
with sync_playwright() as pw:
    b = launch_browser(pw); ctx = new_context(b, use_auth_state=False); pg = ctx.new_page()
    a = StrategicPillarCardAdminPage(pg); a.sign_in("Site Content Editor")
    a.open_entries_list(locale="en"); a.filter_entries("")
    rows = a._row_codes(); res = []
    statuses = [t.strip() for t in pg.locator("table tbody tr td:nth-child(2)").all_inner_texts()]
    for (code, eid), st in zip(rows, statuses):
        title = ""
        if not code.startswith(a.REAL_CODE_PREFIX):
            try:
                title = a._read_title(code)
            except Exception as e:
                title = f"<unreadable {type(e).__name__}>"
        res.append({"code": code, "id": eid, "status": st, "title": title})
    print(json.dumps(res, ensure_ascii=False, indent=1))
    ctx.close(); b.close()

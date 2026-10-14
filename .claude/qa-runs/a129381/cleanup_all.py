"""List every non-QCDEMO pillar card, read its title (polled), and run the guarded delete ONLY
for titles matching this PBI's QCTEST namespace. Anything else is listed, never touched."""
import re, sys, json
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage
MINE = re.compile(r"^QCTEST-(1355\d\d|1356\d\d|129381)-")
with sync_playwright() as pw:
    b = launch_browser(pw); ctx = new_context(b, use_auth_state=False); pg = ctx.new_page()
    a = StrategicPillarCardAdminPage(pg); a.sign_in("Site Content Editor")
    a.open_entries_list(locale="en"); a.filter_entries("")
    rows = [(c, i) for c, i in a._row_codes() if not c.startswith(a.REAL_CODE_PREFIX)]
    found = [(c, i, a._title_of(c, i)) for c, i in rows]
    print("FOUND", json.dumps(found, ensure_ascii=False))
    for c, i, t in found:
        if t and MINE.match(t):
            print("DELETE", t, c, i, a.delete_disposable(t, "Site Content Editor"))
    a.open_entries_list(locale="en"); a.filter_entries("")
    left = [(c, i, a._title_of(c, i)) for c, i in a._row_codes() if not c.startswith(a.REAL_CODE_PREFIX)]
    print("LEFT", json.dumps(left, ensure_ascii=False))
    ctx.close(); b.close()

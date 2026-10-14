"""Guarded cleanup of this PBI's own QCTEST leftovers, by exact QCTEST title only
(StrategicPillarCardAdminPage.delete_disposable: QCTEST prefix, verified code, form re-read,
id not 49056/49082/49108, label==code, re-list verification). Never touches 555085 (empty title)."""
import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage
TITLES = sys.argv[1:]
with sync_playwright() as pw:
    b = launch_browser(pw); ctx = new_context(b, use_auth_state=False); pg = ctx.new_page()
    a = StrategicPillarCardAdminPage(pg)
    for t in TITLES:
        assert t.startswith("QCTEST-"), t
        print("DELETE", t, a.delete_disposable(t, "Site Content Editor"))
        print("  still present:", a.entry_exists(t, "Site Content Editor"))
    ctx.close(); b.close()

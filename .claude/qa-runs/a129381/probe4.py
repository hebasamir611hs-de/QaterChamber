"""QCTEST-only. Instrumented create (Save as Draft) of QCTEST-129381-probe4 as Editor, logging every
non-GET request and the row list before/after, then the guarded delete. Diagnoses the empty-title
duplicate seen after the smoke run (id 555085)."""
import json, sys, logging
sys.path.insert(0, ".")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage
T = "QCTEST-129381-probe4"
reqs = []
with sync_playwright() as pw:
    b = launch_browser(pw); ctx = new_context(b, use_auth_state=False); pg = ctx.new_page()
    pg.on("request", lambda r: reqs.append(f"{r.method} {r.url[:160]}") if r.method != "GET" else None)
    a = StrategicPillarCardAdminPage(pg); a.sign_in("Site Content Editor")
    a.open_entries_list(locale="en"); a.filter_entries("")
    print("ROWS BEFORE", a._row_codes())
    reqs.append("---- open form")
    a.open_form("Site Content Editor")
    a.fill_required(T, active=True, files=a.FILES)
    print("FORM after fill:", pg.evaluate("() => Array.from(document.querySelectorAll('input[name^=ObjectField_], input[id^=qc-ar-]')).map(e => [e.name||e.id, e.value])"))
    reqs.append("---- save as draft")
    a.save_as_draft()
    print("URL after save", pg.url)
    reqs.append("---- after save")
    a.open_entries_list(locale="en"); a.filter_entries("")
    print("ROWS AFTER", a._row_codes())
    print("CODES", a._codes)
    print("CODE_FOR", a.code_for(T, refresh=True))
    reqs.append("---- delete")
    print("DELETE", a.delete_disposable(T))
    a.open_entries_list(locale="en"); a.filter_entries("")
    print("ROWS END", a._row_codes())
    ctx.close(); b.close()
print("\n".join(r for r in reqs if "/o/" in r or "----" in r or "manage" in r or "upload" in r.lower()))

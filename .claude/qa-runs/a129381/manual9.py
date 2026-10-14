"""Step-5 manual repro (QCTEST only, Editor, fresh context, no storageState).
(a) Save as Draft of a new card: network ids + list rows/titles before and after.
(b) Published + Active card -> untick Active -> Publish: raw status + logged-out /home for 60 s.
Guarded delete of both QCTEST titles at the end."""
import sys, json, time
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from config.settings import web_url
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage
A, B = "QCTEST-129381-m9-draft", "QCTEST-129381-m9-active"
out = {"net": []}
def rows(a):
    a.open_entries_list(locale="en"); a.filter_entries("")
    return [(c, i) for c, i in a._row_codes() if not c.startswith(a.REAL_CODE_PREFIX)]
with sync_playwright() as pw:
    b = launch_browser(pw); ctx = new_context(b, use_auth_state=False); pg = ctx.new_page()
    pg.on("response", lambda r: out["net"].append(f"{r.request.method} {r.status} {r.url[:110]} {(r.request.post_data or '')[:160]}") if r.request.method in ("POST", "PUT", "PATCH") and "/o/" in r.url else None)
    a = StrategicPillarCardAdminPage(pg); a.sign_in("Site Content Editor")
    before = rows(a); out["rows_before"] = len(before)
    a.create(A, active=True, submit=False)
    out["url_after_draft_save"] = pg.url
    pg.wait_for_timeout(4000)
    after = rows(a)
    new = [r for r in after if r not in before]
    out["new_rows_after_draft"] = [(c, i, a._read_title(c)) for c, i in new]
    a.open_entries_list(locale="en"); a.filter_entries("")
    pg.screenshot(path="reports/manual-repro-129381-draft-twin-list.png", full_page=True)
    # (b)
    out["net"].append("---- (b)")
    a.create(B, active=True, submit=True)
    out["b_status_published"] = a.raw_row_status(B)
    anon_ctx = new_context(b, use_auth_state=False); anon = anon_ctx.new_page()
    anon.goto(web_url("/home"), wait_until="domcontentloaded"); anon.wait_for_timeout(3000)
    out["b_public_before"] = B in anon.locator("body").inner_text()
    a.open_by_title(B)
    a.set_flag("active_status", False)
    out["b_flag_before_submit"] = a.flag("active_status")
    a.submit_for_review()
    out["b_url_after"] = pg.url
    out["b_status_after_untick"] = a.raw_row_status(B)
    a.open_by_title(B)
    out["b_flag_after_reopen"] = a.flag("active_status")
    vis = []
    for _ in range(6):
        anon.goto(web_url("/home"), wait_until="domcontentloaded"); anon.wait_for_timeout(3000)
        vis.append(B in anon.locator("body").inner_text()); 
        if not vis[-1]: break
        time.sleep(7)
    out["b_public_after_polls"] = vis
    anon.locator(".qc-sd-stage").scroll_into_view_if_needed()
    anon.screenshot(path="reports/manual-repro-129381-135622-public-after-untick.png")
    a.open_entries_list(locale="en"); a.filter_entries("")
    pg.screenshot(path="reports/manual-repro-129381-135622-list-after-untick.png", full_page=True)
    anon_ctx.close()
    out["delete"] = {t: a.delete_disposable(t) for t in (A, B)}
    ctx.close(); b.close()
print(json.dumps(out, ensure_ascii=False, indent=1)[:8000])

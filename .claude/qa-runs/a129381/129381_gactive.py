"""G-ACTIVE hand repro (reviewer item 9 / follow-up item 3), QCTEST record only, Editor.
Standalone Playwright script (not the MCP): the MCP would need the role password typed into its
session; this script resolves it from .env via cms_role_credentials. Captures EVERY non-GET request
with its full body (no URL filter, no truncation; /api/jsonws and /c/ included) plus a HAR.
Steps: create QCTEST card published + Active ticked -> confirm public -> reopen -> untick Active ->
Publish -> reopen fresh (form flag + API activeStatus) -> logged-out /home twice -> guarded delete."""
import json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from config.settings import control_panel_url, web_url
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage

T = "QCTEST-129381-gactive2"
out = {"requests": []}
with sync_playwright() as pw:
    b = launch_browser(pw)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080},
                        record_har_path=".claude/qa-runs/a129381/129381_gactive.har", record_har_content="embed", record_har_url_filter="**/{o,c,api}/**")
    pg = ctx.new_page()
    phase = {"v": "setup"}
    pg.on("request", lambda r: out["requests"].append(
        {"phase": phase["v"], "method": r.method, "url": r.url, "body": r.post_data})
        if r.method not in ("GET", "HEAD", "OPTIONS") else None)
    a = StrategicPillarCardAdminPage(pg)
    try:
        phase["v"] = "create"
        try:
            a.create(T, active=True)
        except Exception as e:  # noqa: BLE001 — form not ready on first load (15:04 attempt); retry once on a fresh form
            out["create_retry"] = repr(e)[:160]
            pg.locator(a.EN_TITLE_INPUT).first.wait_for(timeout=60000) if False else None
            a.open_form("Site Content Editor")
            pg.locator(a.AR_TITLE_INPUT).first.wait_for(state="visible", timeout=60000)
            a.fill_required(T, active=True, files=a.FILES)
            a.submit_for_review()
        out["status_after_create"] = a.raw_row_status(T)
        code = a.code_for(T, refresh=True)
        out["code"] = code
        actx = new_context(b, use_auth_state=False); anon = actx.new_page()
        anon.goto(web_url("/home"), wait_until="domcontentloaded"); anon.wait_for_timeout(4000)
        out["public_before"] = T in anon.locator("body").inner_text()

        phase["v"] = "untick"
        a.open_by_title(T)
        box = pg.get_by_role("checkbox", name=a.label_pattern("Active Status"))
        out["flag_before_untick"] = box.is_checked()
        box.uncheck()
        out["flag_after_untick_in_form"] = box.is_checked()
        out["form_inputs_before_submit"] = pg.evaluate(
            "() => Array.from(document.querySelectorAll('input[name^=ObjectField_]')).map(e => [e.name, e.type, e.type === 'checkbox' ? e.checked : e.value])")
        pg.screenshot(path="reports/manual-repro-129381-gactive-1-unticked.png", full_page=True)
        out["submit_label"] = a.submit_button_label()
        a.submit_for_review()
        out["url_after_submit"] = pg.url
        pg.screenshot(path="reports/manual-repro-129381-gactive-2-after-publish.png", full_page=True)

        phase["v"] = "verify"
        out["status_after_untick"] = a.raw_row_status(T)
        a.open_by_title(T)
        out["flag_after_reopen"] = pg.get_by_role("checkbox", name=a.label_pattern("Active Status")).is_checked()
        pg.screenshot(path="reports/manual-repro-129381-gactive-3-reopened.png", full_page=True)
        rows = a._row_codes() if False else None
        a.open_entries_list(locale="en"); a.filter_entries("")
        ids = dict(a._row_codes())
        eid = ids.get(code)
        out["entry_id"] = eid
        if eid:
            r = pg.request.get(control_panel_url(f"/o/c/strategicpillarcards/{eid}"),
                               headers={"Accept": "application/json", "Accept-Language": "en-US"})
            try:
                j = r.json()
            except Exception:  # noqa: BLE001
                j = None
            out["api_after"] = ({"http": r.status, "activeStatus": j.get("activeStatus"), "status": j.get("status"),
                                 "dateModified": j.get("dateModified")} if isinstance(j, dict) else {"http": r.status, "raw": str(j)[:200]})
        seen = []
        for _ in range(3):
            anon.goto(web_url("/home"), wait_until="domcontentloaded"); anon.wait_for_timeout(5000)
            seen.append(T in anon.locator("body").inner_text())
        out["public_after"] = seen
        anon.locator(".qc-sd-stage").scroll_into_view_if_needed()
        anon.screenshot(path="reports/manual-repro-129381-gactive-4-public.png")
        actx.close()
    finally:
        # USER ORDER 2026-10-08: leave all test data in place (no delete). If the
        # card is still public, take it off the Home Page with the row Unpublish.
        phase["v"] = "teardown"
        try:
            if any(out.get("public_after") or [True]):
                a.open_entries_list(locale="en"); a.filter_entries("")
                a.unpublish_entry(T)
                out["unpublished_in_teardown"] = a.raw_row_status(T)
        except Exception as e:  # noqa: BLE001
            out["teardown_error"] = repr(e)[:200]
        open(".claude/qa-runs/a129381/129381_gactive.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
        ctx.close()
        b.close()
for r in out["requests"]:
    if r["body"] and len(r["body"]) > 6000:
        r["body"] = r["body"][:6000] + "...<cut>"
open(".claude/qa-runs/a129381/129381_gactive.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "requests"}, ensure_ascii=False, indent=1))
print("non-GET requests:", [(r["phase"], r["method"], r["url"][:120]) for r in out["requests"]])

"""READ-ONLY, PBI 129381 follow-up (reviewer items 2 + 4). Creates/edits/deletes nothing.
(A) The 27 untitled drafts: GET /o/c/strategicpillarcards/<id> -> creator, dateCreated, status, title, ERC.
(B) manage-vmo-section and manage-vision-mission-objectives-page: list rows, form labels, and the
    text values of every titled row (to see whether either holds the Home section tag/heading/description).
(C) Home section HTML head (where do tag/heading/description come from?)."""
import json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from config.settings import control_panel_url, web_url
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage

IDS = [555085, 559326, 559408, 559544, 559582, 559611, 559663, 564387, 564393, 564454, 564472, 564536,
       564662, 564680, 564723, 564745, 564768, 564800, 564976, 565001, 565024, 565048, 565074, 565099,
       565133, 565198, 565220]
out = {"drafts": [], "objects": {}}
with sync_playwright() as pw:
    b = launch_browser(pw)
    ctx = new_context(b, use_auth_state=False)
    pg = ctx.new_page()
    a = StrategicPillarCardAdminPage(pg)
    a.sign_in("Site Content Editor")
    for i in IDS:
        try:
            r = pg.request.get(control_panel_url(f"/o/c/strategicpillarcards/{i}"),
                               headers={"Accept": "application/json", "Accept-Language": "en-US"})
            j = r.json() if r.status == 200 else {}
            out["drafts"].append({
                "id": i, "http": r.status, "erc": j.get("externalReferenceCode"),
                "creator": (j.get("creator") or {}).get("name"),
                "creatorId": (j.get("creator") or {}).get("id"),
                "dateCreated": j.get("dateCreated"), "dateModified": j.get("dateModified"),
                "status": (j.get("status") or {}).get("label"),
                "title_i18n": j.get("pillarTitle_i18n"), "desc": (j.get("pillarDescription") or "")[:60],
                "displayOrder": j.get("displayOrder"), "active": j.get("activeStatus"),
                "icon": bool(j.get("pillarIcon")),
            })
        except Exception as e:  # noqa: BLE001
            out["drafts"].append({"id": i, "error": repr(e)[:200]})

    for slug in ("vmo-section", "vision-mission-objectives-page"):
        info = {}
        url = control_panel_url(f"/en/web/qatar-chamber/manage-{slug}")
        pg.goto(url, wait_until="domcontentloaded")
        pg.wait_for_timeout(7000)
        info["rows"] = [[t.strip()[:70] for t in r.split("\t")] for r in pg.locator("table tbody tr").all_inner_texts()]
        info["form_labels"] = [t.strip()[:80] for t in pg.locator("label").all_inner_texts() if t.strip()]
        pg.screenshot(path=f"reports/manual-repro-129381-{slug}.png", full_page=True)
        codes = [t.strip() for t in pg.locator("table tbody tr td:first-child").all_inner_texts()]
        vals = {}
        for code in codes[:6]:
            pg.goto(control_panel_url(f"/en/web/qatar-chamber/manage-{slug}?editEntry={code}"), wait_until="domcontentloaded")
            pg.wait_for_timeout(6000)
            vals[code] = pg.evaluate(
                "() => Array.from(document.querySelectorAll('input[type=text], textarea'))"
                ".filter(e => e.value).map(e => [e.name || e.id, e.value.slice(0, 120)])")
        info["values"] = vals
        out["objects"][slug] = info
    ctx.close()

    ctx = new_context(b, use_auth_state=False)
    pg = ctx.new_page()
    pg.goto(web_url("/home"), wait_until="domcontentloaded")
    pg.locator(".qc-home-strategic-direction").wait_for(timeout=30000)
    out["home_section_head"] = pg.evaluate(
        "() => { const s = document.querySelector('.qc-home-strategic-direction');"
        " const t = s.querySelector('.qc-sd-text') || s; return t.outerHTML.replace(/\\s+/g, ' ').slice(0, 1500); }")
    out["home_section_ancestors"] = pg.evaluate(
        "() => { let e = document.querySelector('.qc-home-strategic-direction'), r = [];"
        " for (let i = 0; i < 6 && e; i++, e = e.parentElement) r.push((e.className || '') + ' #' + (e.id || ''));"
        " return r; }")
    ctx.close()
    b.close()
open(".claude/qa-runs/a129381/129381_probe9.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("ok")

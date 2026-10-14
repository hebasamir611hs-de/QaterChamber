"""READ-ONLY provenance of the 27 untitled Strategic Pillar Card drafts (follow-up item 4).
The headless GET-by-id answers 404 for these drafts (probe9), so creator/date come from each row's
own History trail (row action `data-qc-oel-history` expands an in-table list; nothing is changed),
plus the list's Last-modified cell. Deletes nothing."""
import json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from core.web.browser import launch_browser, new_context
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import StrategicPillarCardAdminPage

IDS = sorted(StrategicPillarCardAdminPage.KNOWN_UNTITLED_IDS)
out = []
with sync_playwright() as pw:
    b = launch_browser(pw)
    ctx = new_context(b, use_auth_state=False)
    pg = ctx.new_page()
    a = StrategicPillarCardAdminPage(pg)
    a.sign_in("Site Content Editor")
    a.open_entries_list(locale="en")
    a.filter_entries("")
    rows = {i: c for c, i in a._row_codes()}
    for i in IDS:
        code = rows.get(i)
        rec = {"id": i, "code": code}
        if code:
            a.open_entries_list(locale="en")
            a.filter_entries("")
            row = pg.locator(f'table tbody tr:has-text("{code}")').first
            rec["list_status"] = row.locator("td").nth(1).inner_text().strip()
            rec["last_modified"] = row.locator("td").nth(2).inner_text().strip()
            try:
                hist = pg.locator(f'[data-qc-oel-history="{i}"]').first
                hist.click(force=True)
                lst = row.locator("xpath=following-sibling::tr[1]").locator("ul.qc-oel__history-list").first
                lst.wait_for(state="visible", timeout=8000)
                rec["history"] = [t.strip().replace("\n", " | ") for t in lst.locator("li").all_inner_texts()]
            except Exception as e:  # noqa: BLE001
                rec["history"] = f"unreadable: {type(e).__name__}"
        out.append(rec)
    ctx.close()
    b.close()
open(".claude/qa-runs/a129381/129381_probe10.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
for r in out:
    print(r)

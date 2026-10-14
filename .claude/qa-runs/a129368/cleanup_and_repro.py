"""Under the c7 lock. (1) List Promotional Banner rows; delete ONLY exact titles
starting with QCTEST-1351 / QCTEST-1352 (this PBI's ids), via delete_disposable
(which itself refuses non-QCTEST titles). (2) Manual repro of the pagination-dot
visibility finding in a fresh logged-out context, EN + AR, with screenshots."""
import json
import sys

sys.path.insert(0, r"D:\MCP servers\QaterChamper")
from playwright.sync_api import sync_playwright

from cms.pages.home_promo_banners.home_promo_banners_admin_page import PromotionalBannerAdminPage
from config.settings import web_url

mode = sys.argv[1]
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    if mode == "cleanup":
        ctx = b.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        admin = PromotionalBannerAdminPage(page)
        admin.open_list("Site Content Editor")
        rows = [r.split("\t")[0].strip() for r in page.locator("table tbody tr").all_inner_texts()]
        out["rows_before"] = rows
        targets = [t for t in rows if t.startswith(("QCTEST-1351", "QCTEST-1352"))]
        out["deleted"] = {t: admin.delete_disposable(t) for t in targets}
        admin.open_list("Site Content Editor")
        out["rows_after"] = [r.split("\t")[0].strip() for r in page.locator("table tbody tr").all_inner_texts()]
    else:
        for loc, path in (("en", "/home"), ("ar", "/home")):
            ctx = b.new_context(viewport={"width": 1920, "height": 1080})
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(web_url(path, locale=loc), wait_until="domcontentloaded")
            page.locator(".qc-promo-carousel").wait_for(timeout=40000)
            page.locator(".qc-promo-carousel").scroll_into_view_if_needed()
            page.wait_for_load_state("load")
            info = page.evaluate("""() => { const d = document.querySelector('.qc-promo-dots');
                const cs = d ? getComputedStyle(d) : null;
                return {exists: !!d, display: cs && cs.display, hidden_attr: d && d.hidden,
                        dots: d ? d.querySelectorAll('.qc-promo-dot').length : 0,
                        slides: document.querySelectorAll('.qc-promo-slide:not([data-clone])').length}; }""")
            info["errors"] = errors[:6]
            info["user"] = "anonymous"
            page.screenshot(path=rf"D:\MCP servers\QaterChamper\reports\manual-repro-129368-135105-{loc}.png", full_page=False,
                            clip=None)
            page.locator(".qc-promo-carousel").screenshot(
                path=rf"D:\MCP servers\QaterChamper\reports\manual-repro-129368-135105-{loc}-carousel.png")
            out[loc] = info
            ctx.close()
    b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))

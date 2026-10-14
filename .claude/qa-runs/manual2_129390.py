"""Manual round 2 + Step-5 repros for PBI 129390 (B-129390, 2026-10-08), under
the c7 lock. Read-only except nothing (no CMS write, no form submit).
 - 136482 dark-mode renders (EN/AR) via AccessibilityToolsComponent.enable_dark_mode()
 - stored-submission check (Form Manager, every page of manage-inquiry)
 - repro screenshots reports/manual-repro-129390-<tc>.png for the findings
Output reports/manual2-129390.json"""
import json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import cms_role_credentials, control_panel_url, web_url, settings
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_contact_us.home_contact_us_admin_page import ARTICLE_53012_EDIT_PATH, ContactUsSectionArticlePage
from web.pages.home_quick_contact.home_quick_contact_page import HomeQuickContactPage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

OUT = {}


def safe(k, fn):
    try:
        OUT[k] = fn()
    except Exception as e:  # noqa
        OUT[k] = f"ERROR {type(e).__name__}: {str(e)[:300]}"
    print(k, "->", json.dumps(OUT[k], ensure_ascii=False, default=str)[:900])


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    def dark(loc):
        ctx = b.new_context(viewport={"width": 1920, "height": 1080})
        pg = ctx.new_page()
        try:
            c = HomeQuickContactPage(pg)
            c.open_home_arabic() if loc == "ar" else c.open_home()
            AccessibilityToolsComponent(pg).enable_dark_mode()
            c.scroll_to_section(); pg.wait_for_timeout(1200)
            pg.locator(c.SECTION).screenshot(path=f"reports/manual-exec-129390-136482-{loc}-dark.png")
            return {"theme": pg.evaluate("() => document.documentElement.getAttribute('data-theme')"),
                    "dir": pg.evaluate("() => document.documentElement.dir"),
                    "heading_color": c.typography(c.HEADING)["color"],
                    "section_bg": pg.locator(c.SECTION).evaluate("el => getComputedStyle(el).backgroundColor"),
                    "form_bg": pg.locator(c.FORM_CARD).evaluate("el => getComputedStyle(el).backgroundColor"),
                    "label_color": c.typography(f"{c.SECTION} label")["color"], "overflow": c.has_page_horizontal_overflow()}
        finally:
            ctx.close()
    # 136482 is P4 — DEFERRED (P4, user 2026-10-08); its dark renders are not run.

    # Step-5 repro: public section vs Figma (EN desktop 1920) and AR
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    c = HomeQuickContactPage(pg)
    def pub():
        c.open_home(); c.scroll_to_section(); pg.wait_for_timeout(1500)
        pg.locator(c.SECTION).screenshot(path="reports/manual-repro-129390-136472-figma.png")
        tgt = c.element_box(c.DIRECTIONS_LINK)
        c.open_home_arabic(); c.scroll_to_section(); pg.wait_for_timeout(1500)
        pg.locator(c.SECTION).screenshot(path="reports/manual-repro-129390-G3-public-ar.png")
        return {"directions_box_1920": tgt}
    safe("public_repro", pub)
    ctx.close()
    ctx = b.new_context(viewport={"width": 375, "height": 812})
    pg = ctx.new_page()
    c = HomeQuickContactPage(pg)
    def mob():
        c.open_home(); c.scroll_to_section(); pg.wait_for_timeout(1200)
        pg.locator(c.LOCATION_ITEM).scroll_into_view_if_needed()
        pg.locator(c.LOCATION_ITEM).screenshot(path="reports/manual-repro-129390-136473.png")
        return {"directions_box_375": c.element_box(c.DIRECTIONS_LINK)}
    safe("mobile_repro", mob)
    ctx.close()

    # G1: Editor on the section's content
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Site Content Editor")
    CmsLoginPage(pg).open_login().login(em, pw)
    def g1():
        r = pg.goto(control_panel_url(ARTICLE_53012_EDIT_PATH), wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000)
        pg.screenshot(path="reports/manual-repro-129390-136483.png")
        return {"status": r.status if r else None, "body": pg.inner_text("body")[:300]}
    safe("g1_editor_article", g1)
    ctx.close()

    # G3: article 53012 ar-SA values (read only) for the side-by-side
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    CmsLoginPage(pg).open_login().login(settings.test_user, settings.test_password)
    def g3():
        art = ContactUsSectionArticlePage(pg)
        art.open_article_53012()
        art._field("Section Description").wait_for(timeout=60000)
        art.switch_content_locale("ar-SA")
        art._field("Section Description", "ar_SA").scroll_into_view_if_needed()
        pg.screenshot(path="reports/manual-repro-129390-G3-53012-ar.png", full_page=True)
        return {k: art.value(k, "ar_SA") for k in ("Section Description", "Location Address")}
    safe("g3_article_ar", g3)
    pg.goto(control_panel_url("/c/portal/update_language?languageId=en_US"))
    ctx.close()

    # Stored submissions — Form Manager, every page
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Form Manager")
    CmsLoginPage(pg).open_login().login(em, pw)
    def stored():
        pg.goto(control_panel_url("/en/web/qatar-chamber/manage-inquiry"), timeout=60000)
        pg.locator("table tbody tr").first.wait_for(timeout=90000)
        rows = []
        for _ in range(30):
            rows += pg.locator("table tbody tr").all_inner_texts()
            nxt = pg.locator('button:text-is("›"):visible')
            if not nxt.count() or nxt.last.is_disabled():
                break
            first = pg.locator("table tbody tr").first.inner_text()
            nxt.last.click()
            try:
                pg.wait_for_function("t => { const r = document.querySelector('table tbody tr'); return r && r.innerText !== t; }", arg=first, timeout=15000)
            except Exception:  # noqa
                break
        out = {tc: [r.replace("\n", " ")[:260] for r in rows if f"QCTEST-{tc}" in r] for tc in ("136485", "136495", "136472", "136553")}
        out["refs_0031_0032"] = [r.replace("\n", " ")[:260] for r in rows if "QC-INQ-2026-0031" in r or "QC-INQ-2026-0032" in r]
        pg.screenshot(path="reports/manual-exec-129390-stored-inquiries.png", full_page=True)
        return {"rows_seen": len(rows), **out}
    safe("stored", stored)
    ctx.close()
    b.close()
json.dump(OUT, open("reports/manual2-129390.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("done")

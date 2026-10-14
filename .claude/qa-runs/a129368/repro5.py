import sys, json
sys.path.insert(0, r"D:\MCP servers\QaterChamper")
from playwright.sync_api import sync_playwright
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url
R = r"D:\MCP servers\QaterChamper\reports"
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for role, tag in (("Site Content Editor", "editor"), ("Site Content Author", "author")):
        ctx = b.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        CmsLoginPage(page).ensure_signed_in_as(*cms_role_credentials(role), control_panel_url("/en/home"))
        page.goto(control_panel_url("/en/web/qatar-chamber/manage-promotional-banner"), wait_until="domcontentloaded")
        btn = page.locator('button[type="submit"][name="status"]').last
        btn.wait_for(timeout=40000)
        btn.scroll_into_view_if_needed()
        out[tag] = page.locator('button[type="submit"][name="status"]').all_inner_texts()
        btn.locator("xpath=ancestor::*[3]").screenshot(path=rf"{R}\manual-repro-129368-submit-label-{tag}.png")
        ctx.close()
    b.close()
print(json.dumps(out))

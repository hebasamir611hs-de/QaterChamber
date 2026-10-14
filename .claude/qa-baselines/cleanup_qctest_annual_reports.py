"""One-off cleanup: delete every QCTEST-prefixed entry left over in the
Annual Report admin object (manage-ann-rpt) after the upload/license outage
interrupted several test runs' teardown. Logs in fresh, does NOT touch any
non-QCTEST (real) row."""
import sys
sys.path.insert(0, ".")

from playwright.sync_api import sync_playwright
from config.settings import settings, control_panel_url
from cms.pages.control_panel.login_page import CmsLoginPage

deleted = []
skipped_non_qctest = 0

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    CmsLoginPage(page).open_login().login(settings.test_user, settings.test_password)
    page.goto(control_panel_url("/web/qatar-chamber/manage-ann-rpt"))
    page.wait_for_load_state("domcontentloaded")

    while True:
        page.wait_for_timeout(800)
        rows = page.locator("table tbody tr")
        count = rows.count()
        found_one = False
        for i in range(count):
            row = rows.nth(i)
            text = row.inner_text()
            if "QCTEST" in text:
                title_cell = row.locator("td").first
                title = title_cell.inner_text().strip()
                delete_link = row.locator('a:has-text("Delete")')
                if delete_link.count() > 0:
                    delete_link.first.click()
                    page.wait_for_timeout(300)
                    # confirm dialog if any
                    try:
                        confirm = page.get_by_role("button", name="Delete")
                        if confirm.count() > 0:
                            confirm.first.click()
                    except Exception:
                        pass
                    page.wait_for_timeout(800)
                    deleted.append(title)
                    found_one = True
                    break
        if not found_one:
            break
        if len(deleted) > 50:
            break

    context.close()
    browser.close()

print("DELETED:", len(deleted))
for t in deleted:
    print(" -", t)

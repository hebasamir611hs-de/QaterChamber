"""Tear down the disposable Inquiry Categories this PBI's run created
(B-129390, 2026-10-08) — needed because batch 1's pager locator hit a hidden
date-picker button, so its own teardown could not find rows past page 1.
Account: QC Site Content Editor. Deletes ONLY rows whose Category Label (EN or
AR) starts with one of this PBI's QCTEST-<tc> prefixes, re-reading each record
first; verifies by re-listing every page; reads the logged-out dropdown
before/after. Output reports/cleanup-ic-129390.json"""
import json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import cms_role_credentials, web_url
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_contact_us.home_contact_us_admin_page import (
    InquiryCategoryAdminPage, FIELD_CATEGORY_LABEL_EN, FIELD_CATEGORY_LABEL_AR)

OURS = tuple(f"QCTEST-{tc}" for tc in ("136534", "136535", "136536", "136537", "136538", "136539",
                                        "136540", "136569", "136570", "136571"))
OUT = {}


def dropdown(b):
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    pg.goto(web_url("/"), wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_function("() => document.querySelectorAll('#qc-cu-category option').length > 1", timeout=60000)
    opts = pg.locator("#qc-cu-category option").all_inner_texts()
    ctx.close()
    return opts


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    OUT["public_before"] = [o for o in dropdown(b) if "QCTEST" in o]
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    em, pw = cms_role_credentials("Site Content Editor")
    CmsLoginPage(pg).open_login().login(em, pw)
    ic = InquiryCategoryAdminPage(pg)
    codes = ic.entry_codes()
    OUT["all_codes"] = codes
    targets, others = [], []
    for code in codes:
        if code.startswith("QCDEMO-"):
            continue
        ic.open_entry_by_code(code, locale="en")
        en, ar = ic.field_value(FIELD_CATEGORY_LABEL_EN), ic.field_value(FIELD_CATEGORY_LABEL_AR)
        (targets if (en.startswith(OURS) or ar.startswith(OURS)) else others).append({"code": code, "en": en[:60], "ar": ar[:60]})
    OUT["targets"], OUT["not_ours"] = targets, others
    res = []
    for t in targets:
        try:
            res.append({**t, "gone": ic.delete_qctest(t["code"])})
        except Exception as e:  # noqa
            res.append({**t, "error": f"{type(e).__name__}: {str(e)[:200]}"})
        print(res[-1])
    OUT["deleted"] = res
    OUT["codes_after"] = ic.entry_codes()
    ctx.close()
    OUT["public_after"] = [o for o in dropdown(b) if "QCTEST" in o]
    b.close()
json.dump(OUT, open("reports/cleanup-ic-129390.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done", json.dumps({k: OUT[k] for k in ("public_before", "public_after")}, ensure_ascii=False))

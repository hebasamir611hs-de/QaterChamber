"""Pre-run gate for PBI 129390 (B-129390, 2026-10-08), under the c7 lock.
1. Look for the earlier probe article QCTEST-129390-PROBE in the DB-backed
   JSONWS article list (the Web Content UI list is unavailable) and, only if its
   title is exactly that, delete it by ID and re-check.
2. Round-trip ONE fresh QCTEST article: Save as Draft -> articleId from the URL
   -> headless GET by-key -> DELETE -> re-GET 404. Writes ok=true only if all
   of that works.
3. Read-only G3 evidence: article 53012's ar-SA translation state and values
   vs the public Arabic section. Nothing on 53012 is saved.
Output: reports/gate-129390.json"""
import base64, json, sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import control_panel_url, settings, web_url
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_contact_us.home_contact_us_admin_page import ContactUsSectionArticlePage

OUT = {"ok": False}
AUTH = "Basic " + base64.b64encode(f"{settings.test_user}:{settings.test_password}".encode()).decode()


def step(k, fn):
    try:
        OUT[k] = fn()
    except Exception as e:  # noqa
        OUT[k] = f"ERROR {type(e).__name__}: {str(e)[:400]}"
    print(k, "->", json.dumps(OUT[k], ensure_ascii=False, default=str)[:1500])


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    CmsLoginPage(pg).open_login().login(settings.test_user, settings.test_password)
    art = ContactUsSectionArticlePage(pg)

    def jsonws_articles():
        r = pg.request.post(control_panel_url("/api/jsonws/journal.journalarticle/get-articles"),
                            headers={"Authorization": AUTH}, form={"groupId": "37246", "folderId": "0"})
        txt = r.text()
        try:
            items = json.loads(txt)
        except Exception:  # noqa
            return {"status": r.status, "body": txt[:500]}
        hits = [{"articleId": a.get("articleId"), "title": a.get("titleCurrentValue") or a.get("title", "")[:200],
                 "status": a.get("status"), "version": a.get("version"), "ddmStructureId": a.get("DDMStructureId") or a.get("ddmStructureId")}
                for a in items if "QCTEST-129390" in json.dumps(a, ensure_ascii=False)]
        return {"status": r.status, "count": len(items), "qctest_129390": hits}
    step("jsonws_articles", jsonws_articles)

    def clean_probe():
        res = OUT.get("jsonws_articles")
        if not isinstance(res, dict):
            return "no listing"
        done = []
        for h in res.get("qctest_129390", []):
            if h["articleId"] and "QCTEST-129390-PROBE" in (h["title"] or ""):
                look = art.lookup_article(h["articleId"])
                if look.get("title") == "QCTEST-129390-PROBE":
                    done.append(art.delete_qctest_article(h["articleId"], "QCTEST-129390-PROBE"))
                else:
                    done.append({"articleId": h["articleId"], "lookup": look, "skipped": "title mismatch"})
        return done
    step("clean_probe", clean_probe)

    def roundtrip():
        title = "QCTEST-129390-GATE"
        art.open_new_article()
        art.set_title(title)
        art.fill_all_valid(title, "en_US")
        res = art.save_as_draft()
        pg.screenshot(path="reports/gate-129390-save.png")
        out = {"save": res}
        if res.get("article_id"):
            out["lookup"] = art.lookup_article(res["article_id"])
            out["delete"] = art.delete_qctest_article(res["article_id"], title)
        return out
    step("roundtrip", roundtrip)
    rt = OUT.get("roundtrip")
    OUT["ok"] = bool(isinstance(rt, dict) and rt.get("save", {}).get("saved") and rt.get("delete", {}).get("gone"))

    def g3():
        art.open_article_53012()
        art._field("Section Heading").wait_for(timeout=60000)
        en = {k: art.value(k) for k in art.FIELD_REFS}
        pg.locator('button:has-text("en-US")').first.click()
        items = pg.locator('[role="menuitem"]:visible, .dropdown-item:visible').all_inner_texts()
        pg.keyboard.press("Escape")
        ar = None
        try:
            art.switch_content_locale("ar-SA")
            ar = {k: art.value(k, "ar_SA") for k in art.FIELD_REFS}
            pg.screenshot(path="reports/gate-129390-53012-ar.png", full_page=True)
        except Exception as e:  # noqa
            ar = f"ERROR {type(e).__name__}"
        return {"en": en, "locale_items": items, "ar": ar}
    step("g3_53012", g3)
    ctx.close()

    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    def public_ar():
        pg.goto(web_url("/", locale="ar"), wait_until="domcontentloaded", timeout=60000)
        pg.locator("section.qc-home-contact-us").wait_for(timeout=30000)
        pg.wait_for_timeout(1500)
        return pg.evaluate("""() => { const s = document.querySelector('section.qc-home-contact-us');
            const t = c => ((s.querySelector(c)||{}).innerText||'').trim();
            return {tag: t('.qc-contact-tag'), heading: t('.qc-contact-heading'), desc: t('.qc-contact-desc'),
                    items: [...s.querySelectorAll('.qc-contact-item-text')].map(e => e.innerText), submit: t('[data-qc-submit-label]'),
                    map: (s.querySelector('iframe')||{}).src}; }""")
    step("public_ar", public_ar)
    ctx.close()
    b.close()

json.dump(OUT, open("reports/gate-129390.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("GATE_OK" if OUT["ok"] else "GATE_FAIL")
print("done")

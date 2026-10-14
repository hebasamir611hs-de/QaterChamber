"""PBI 129372 manual executions, round 4 (USER ORDER 22:45), live under the c7 lock.
A 135324 zero articles (visitor's articles response served empty; real data untouched)
B 135315 malformed Publication Date, by hand
C 135310 800 KB JPG thumbnail -> stored -> shown on the visitor's card, by hand
D Rule 5.2 UI check for 135282/135285/135289/135293 (section tag 51 / heading 201 accepted)
QCTEST records are torn down by exact value; public ones are deleted right after the read."""
import os, sys, json, time, datetime, importlib.util
sys.path.insert(0, os.getcwd())
from playwright.sync_api import sync_playwright
from config.settings import web_url
from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED
from cms.pages.home_latest_news.home_latest_news_admin_page import (
    HomeLatestNewsAdminPage, F_THUMBNAIL, F_PUB_DATE, F_ACTIVE,
    S_TAG, S_HEADING, S_HEADING_AR, S_DESC, S_DESC_AR, S_ACTIVE)
from web.pages.home_latest_news.home_latest_news_page import HomeLatestNewsPage

R = "reports/manual-exec-129372-"
THUMB = "cms/tests/home_latest_news/fixtures/news_thumbnail.png"
TODAY = datetime.date.today()
out = {}


def per_page_all(p):
    """Entries list shows 10 rows by default and the News list now has 11+ rows."""
    sel = p.locator("select:has(option:text-is('100'))").first
    try:
        sel.select_option(label="100")
        p.wait_for_timeout(1500)
    except Exception as e:
        out.setdefault("per_page_errors", []).append(str(e)[:120])


def row_count(admin, authoring, text):
    authoring.open_entries_list()
    per_page_all(admin.page)
    return admin.page.locator(f'{authoring.ENTRIES_TABLE_ROW}:has-text("{text}")').count()


def visitor(b, w=1920):
    ctx = b.new_context(viewport={"width": w, "height": 1080})
    return ctx, ctx.new_page()


with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)

    # ---------- A. 135324 ----------
    try:
        ctx, p = visitor(b)
        errs = []
        p.on("pageerror", lambda e: errs.append(str(e)[:200]))
        home = HomeLatestNewsPage(p)
        home.shape_news_items(lambda items: [])
        p.goto(web_url("/home"), wait_until="load")
        p.locator(home.SECTION).wait_for(state="attached", timeout=60000)
        p.wait_for_timeout(6000)  # evidence capture only: async render
        info = p.evaluate("""() => { const s = document.querySelector('section.qc-home-latest-news');
            const q = sel => s.querySelector(sel);
            const vis = el => !!el && getComputedStyle(el).display !== 'none' && getComputedStyle(el).visibility !== 'hidden' && el.getBoundingClientRect().height > 0;
            return { sectionVisible: vis(s), hiddenAttr: s.hidden, display: getComputedStyle(s).display,
              height: s.getBoundingClientRect().height,
              tag: q('.qc-ln-tag') && q('.qc-ln-tag').innerText, tagVisible: vis(q('.qc-ln-tag')),
              heading: q('.qc-ln-heading') && q('.qc-ln-heading').innerText, headingVisible: vis(q('.qc-ln-heading')),
              descVisible: vis(q('.qc-ln-desc')), cards: s.querySelectorAll('a.qc-ln-card').length,
              gridText: (q('.qc-ln-grid') || {innerText: ''}).innerText.slice(0, 200),
              overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth } }""")
        info["page_errors"] = errs
        out["A_135324"] = info
        y = p.evaluate("() => document.querySelector('section.qc-home-latest-news').getBoundingClientRect().top + window.scrollY")
        p.evaluate(f"window.scrollTo(0, {max(0, y - 100)})")
        p.wait_for_timeout(500)
        p.screenshot(path=R + "135324-zero.png")
        ctx.close()
    except Exception as e:
        out["A_error"] = str(e)[:300]

    ed = b.new_context(viewport={"width": 1600, "height": 1000})
    ep = ed.new_page()
    admin = HomeLatestNewsAdminPage(ep).sign_in_as("Site Content Editor")

    # ---------- B. 135315 ----------
    t = "QCTEST-135315-M Malformed Date"
    try:
        admin.delete_qctest_article(t)
        admin.fill_news_article(title=t, title_ar="QCTEST-135315-M ع", thumbnail=THUMB, active=False)
        box = admin.date_box(F_PUB_DATE)
        box.click()
        ep.keyboard.type("32/13/2026", delay=20)
        ep.keyboard.press("Tab")
        out["B_field_value"] = box.input_value()
        out["B_field_invalid"] = box.get_attribute("aria-invalid")
        out["B_hint_texts"] = [x for x in ep.locator("text=/dd\\/mm\\/yyyy/i").all_inner_texts()][:4]
        box.scroll_into_view_if_needed()
        ep.screenshot(path=R + "135315-1-typed.png")
        ep.locator(admin.news.SUBMIT_FOR_REVIEW_BUTTON).first.click()
        ep.wait_for_timeout(10000)  # evidence capture: whatever the form does after the click
        out["B_refusal_text"] = admin.refusal_text(admin.news)
        out["B_url_after"] = ep.url
        ep.screenshot(path=R + "135315-2-after-publish.png")
        out["B_rows_saved"] = row_count(admin, admin.news, t)
    except Exception as e:
        out["B_error"] = str(e)[:300]
    finally:
        admin.delete_qctest_article(t)

    # ---------- C. 135310 ----------
    t = "QCTEST-135310-M JPG Thumbnail"
    try:
        spec = importlib.util.spec_from_file_location("ff", "tools/fixture_factory.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        jpg = os.path.abspath("reports/thumbnail.jpg")
        open(jpg, "wb").write(mod.make_jpg(800 * 1024))
        admin.delete_qctest_article(t)
        admin.fill_news_article(t, "QCTEST-135310-M ع", TODAY, jpg, active=True)
        out["C_upload_name"] = admin.news.uploaded_filename(F_THUMBNAIL)
        ep.screenshot(path=R + "135310-1-uploaded.png")
        admin.news.save_as_draft()
        time.sleep(5)
        out["C_rows_after_draft"] = row_count(admin, admin.news, t)
        admin.news.open_entry_by_edit_link(t)
        out["C_stored_file"] = admin.news.current_file_name(F_THUMBNAIL)
        admin.news.submit_for_review()
        time.sleep(30)  # Publish commits in ~27-30 s on qcdev (measured 2026-09-15)
        vctx, vp = visitor(b)
        home = HomeLatestNewsPage(vp)
        out["C_on_home"] = home.reload_until_article_matches(t, True, timeout_ms=90000)
        if out["C_on_home"]:
            home.scroll_to_section()
            idx = home.card_index_by_title(t)
            img = home._card(idx).locator(home.CARD_IMAGE)
            out["C_card_img_src"] = (img.get_attribute("src") or "")[:160]
            out["C_card_img_loaded"] = img.evaluate("i => i.complete && i.naturalWidth > 0")
            vp.screenshot(path=R + "135310-2-card.png")
        vctx.close()
        os.remove(jpg)
    except Exception as e:
        out["C_error"] = str(e)[:300]
    finally:
        admin.delete_qctest_article(t)

    # ---------- D. Rule 5.2 UI check, section tag 51 / heading 201 ----------
    key = "QCTEST-RULE5-M وصف"
    vals = {
        S_TAG: ("QCTEST-135282-" + "x" * 60)[:51],
        "Section Tag — العربية": ("QCTEST-135285-" + "ع" * 60)[:51],
        S_HEADING: ("QCTEST-135289-" + "Heading " * 40)[:201],
        S_HEADING_AR: ("QCTEST-135293-" + "عنوان " * 60)[:201],
        S_DESC: "QCTEST-RULE5-M description",
        S_DESC_AR: key,
    }
    try:
        admin.open_new_section_form()
        for lbl, v in vals.items():
            admin.fill(lbl, v)
        out["D_kept_lengths"] = {lbl: len(admin.value(lbl)) for lbl in vals}
        admin.section.set_checkbox(S_ACTIVE, True)
        admin.section.submit_for_review()
        ep.wait_for_timeout(8000)  # evidence capture after Publish
        ep.screenshot(path=R + "rule5-1-cms-after-publish.png", full_page=True)
        for loc in ("en", "ar"):
            vctx, vp = visitor(b)
            home = HomeLatestNewsPage(vp)
            home.pick_section_record(key)
            vp.goto(web_url("/home", locale=loc), wait_until="domcontentloaded")
            vp.locator(home.HEADING).wait_for(timeout=60000)
            vp.wait_for_timeout(3000)  # evidence capture: fonts settle
            home.scroll_to_section()
            out[f"D_{loc}"] = vp.evaluate("""() => { const s = document.querySelector('section.qc-home-latest-news');
                const r = el => { const b = el.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.right), Math.round(b.height)]; };
                const t = s.querySelector('.qc-ln-tag'), h = s.querySelector('.qc-ln-heading'), head = s.querySelector('.qc-ln-head');
                return { tag: t.innerText.length, heading: h.innerText.length, tagBox: r(t), headingBox: r(h), headBox: r(head),
                  tagClipped: t.scrollWidth > t.clientWidth + 1, headingClipped: h.scrollWidth > h.clientWidth + 1,
                  ctaBox: r(s.querySelector('.qc-ln-viewall--top')),
                  overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth,
                  vw: window.innerWidth } }""")
            vp.screenshot(path=R + f"rule5-2-home-{loc}.png")
            vctx.close()
    except Exception as e:
        out["D_error"] = str(e)[:300]
    finally:
        out["D_deleted"] = admin.delete_verified_entry(admin.section, S_DESC_AR, key)
    ed.close()
    b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))

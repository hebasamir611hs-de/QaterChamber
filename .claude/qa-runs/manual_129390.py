"""Manual-case execution for PBI 129390 (B-129390, 2026-10-08), run under the c7
lock. Covers the Manual-tagged cases 136472, 136481, 136482, 136496, 136497,
136499, 136506, 136507, 136553, 136554 plus the stored-submission check for the
real sends made by pytest (136485, 136495).

Real public-form submissions made here (logged-out visitor, visitor email =
the team test inbox heba.samir611.hs@gmail.com):
  S-EN  QCTEST-136472 Ahmed Ali   (EN page)  -> 136472/136496/136497/136499/136507
  S-AR  QCTEST-136553 أحمد علي     (AR page)  -> 136553/136554
Writes nothing in the CMS. Output: reports/manual-129390.json and
reports/manual-exec-129390-<tc>.png."""
import json, sys, time
from datetime import datetime, timezone
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from config.settings import cms_role_credentials, control_panel_url, web_url
from cms.pages.control_panel.login_page import CmsLoginPage
from web.pages.home_quick_contact.home_quick_contact_page import HomeQuickContactPage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

INBOX = "heba.samir611.hs@gmail.com"
OUT = {"sends": []}
SHOT = "reports/manual-exec-129390-{}.png"
FIGMA = {  # .claude/qa-runs/129390.figma.json (node 849:15904, 1920 wide, EN desktop light)
    "tag": ("Contact US", 400, 16, 24, "#A66F43"),
    "heading": ("Connect with Qatar Chamber to Move Your Business Forward", 700, 36, 44, "#1D1D1B"),
    "desc": ("Get the support, services, and guidance your business needs to grow, connect, and operate with confidence in Qatar and beyond.", 400, 16, 24, "#6C6C6B"),
    "form_title": ("Get in touch with us", 700, 24, 32, "#911731"),
    "submit": ("Send Message", 600, 16, 24, "#FFFFFF"),
}
SEL = {"tag": ".qc-contact-tag", "heading": ".qc-contact-heading", "desc": ".qc-contact-desc",
       "form_title": ".qc-contact-form-title", "submit": "[data-qc-submit-label]"}


def safe(key, fn):
    try:
        OUT[key] = fn()
    except Exception as e:  # noqa
        OUT[key] = f"ERROR {type(e).__name__}: {str(e)[:400]}"
    print(key, "->", json.dumps(OUT[key], ensure_ascii=False, default=str)[:700])


def hexcol(rgb):
    import re
    n = re.findall(r"\d+", rgb or "")
    return "#" + "".join(f"{int(x):02X}" for x in n[:3]) if len(n) >= 3 else rgb


def anon(b, viewport=(1920, 1080)):
    ctx = b.new_context(viewport={"width": viewport[0], "height": viewport[1]})
    return ctx, ctx.new_page()


def send(pg, contact, name, msg, category, tc):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    posts = contact.watch_submissions()
    responses = []
    pg.on("response", lambda r: responses.append({"url": r.url, "status": r.status, "body": (r.text() if "qc-inquiry" in r.url else "")[:300]})
          if "qc-inquiry" in r.url else None)
    contact.fill_form(full_name=name, email=INBOX, category_label=category, message=f"{msg} [{stamp}]")
    contact.click_submit()
    status = contact.wait_for_status_text(45000)
    pg.wait_for_timeout(1000)
    pg.screenshot(path=SHOT.format(tc))
    rec = {"tc": tc, "sent_at": stamp, "visitor_name": name, "visitor_email": INBOX, "category": category,
           "status": status, "posts": len(posts), "server": responses[:2],
           "recaptcha_token_empty": any("recaptchaToken=&" in (p["body"] or "") for p in posts)}
    OUT["sends"].append(rec)
    return rec


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    # ---- 136472 (EN desktop 1920 vs Figma) + S-EN ----------------------------
    ctx, pg = anon(b)
    c = HomeQuickContactPage(pg)
    def t136472():
        c.open_home(); c.scroll_to_section(); pg.wait_for_timeout(1500)
        pg.locator(c.SECTION).screenshot(path=SHOT.format("136472-section"))
        typo = {k: c.typography(f"{c.SECTION} {s}") for k, s in SEL.items()}
        diffs = {}
        for k, (text, w, size, lh, col) in FIGMA.items():
            t = typo[k]
            live = {"text": t["text"], "weight": int(t["weight"]), "size": float(t["size"].rstrip("px")),
                    "line_height": t["line_height"], "color": hexcol(t["color"]), "transform": t["transform"], "family": t["family"]}
            d = {}
            if live["text"] != text and not (t["transform"] == "uppercase" and live["text"].upper() == text.upper()):
                d["text"] = (text, live["text"])
            if live["weight"] != w: d["weight"] = (w, live["weight"])
            if live["size"] != size: d["size"] = (size, live["size"])
            if live["line_height"] not in (f"{lh}px", f"{float(lh)}px"): d["line_height"] = (lh, live["line_height"])
            if live["color"].upper() != col.upper(): d["color"] = (col, live["color"])
            if "Cairo" not in live["family"]: d["family"] = ("Cairo", live["family"])
            diffs[k] = {"live": live, "diff": d}
        items = [pg.locator(c.CONTACT_ITEM_TEXT).nth(i).inner_text() for i in range(3)]
        fields = c.visible_form_field_ids()
        grid = c.grid_template_columns()
        return {"typography_vs_figma": diffs, "contact_items": items, "fields": fields, "grid_columns": grid,
                "captcha": c.captcha_state(), "map_src": c.map_iframe_src()}
    safe("136472_render", t136472)
    safe("136472_send", lambda: send(pg, c, "QCTEST-136472 Ahmed Ali", "QCTEST-136472 I would like more information about membership.", "General Inquiry", "136472"))
    ctx.close()

    # ---- 136481 Mobile Number field presence ---------------------------------
    ctx, pg = anon(b)
    c = HomeQuickContactPage(pg)
    def t136481():
        c.open_home(); c.scroll_to_section()
        pg.locator(c.FORM_CARD).screenshot(path=SHOT.format("136481"))
        return {"fields": c.visible_form_field_ids(), "labels": pg.locator(f"{c.SECTION} label").all_inner_texts(),
                "phone_required": pg.locator(c.PHONE_INPUT).get_attribute("required")}
    safe("136481", t136481)
    ctx.close()

    # ---- 136482 AR / mobile / dark / high-contrast renders --------------------
    def variant(tag, viewport, locale="en", mode=None):
        ctx, pg = anon(b, viewport)
        try:
            a = AccessibilityToolsComponent(pg)
            c = HomeQuickContactPage(pg)
            c.open_home_arabic() if locale == "ar" else c.open_home()
            if mode == "dark":
                a.switch_to_dark_mode()
            elif mode == "contrast":
                a.enable_high_contrast()
            c.scroll_to_section(); pg.wait_for_timeout(1200)
            pg.locator(c.SECTION).screenshot(path=SHOT.format(f"136482-{tag}"))
            html = pg.evaluate("() => ({theme: document.documentElement.getAttribute('data-theme'), cls: document.documentElement.className, dir: document.documentElement.dir})")
            return {"html": html, "overflow": c.has_page_horizontal_overflow(), "single_col": c.is_single_column_layout(),
                    "heading": c.heading_text(), "heading_color": c.typography(c.HEADING)["color"],
                    "section_bg": pg.locator(c.SECTION).evaluate("el => getComputedStyle(el).backgroundColor"),
                    "info_x": c.info_x(), "form_x": c.form_x()}
        finally:
            ctx.close()
    for tag, vp, loc, mode in (("ar-desktop", (1920, 1080), "ar", None), ("en-mobile", (375, 812), "en", None),
                               ("ar-mobile", (375, 812), "ar", None), ("en-dark", (1920, 1080), "en", "dark"),
                               ("ar-dark", (1920, 1080), "ar", "dark"), ("en-contrast", (1920, 1080), "en", "contrast")):
        safe(f"136482_{tag}", lambda tag=tag, vp=vp, loc=loc, mode=mode: variant(tag, vp, loc, mode))

    # ---- 136506 / 136507 CAPTCHA ---------------------------------------------
    ctx, pg = anon(b)
    c = HomeQuickContactPage(pg)
    def captcha():
        cfg = {}
        pg.on("response", lambda r: cfg.update({"config": r.text()[:300]}) if "qc-recaptcha-api/config" in r.url else None)
        c.open_home(); c.scroll_to_section(); pg.wait_for_timeout(2500)
        pg.locator(c.FORM_CARD).screenshot(path=SHOT.format("136506"))
        return {"widget": c.captcha_state(), **cfg}
    safe("136506_captcha", captcha)
    ctx.close()

    # ---- S-AR (136553 / 136554) -----------------------------------------------
    ctx, pg = anon(b)
    c = HomeQuickContactPage(pg)
    def ar_send():
        c.open_home_arabic(); c.scroll_to_section()
        return send(pg, c, "QCTEST-136553 أحمد علي", "QCTEST-136553 أرغب في معرفة المزيد عن الفعاليات.", "الفعاليات", "136553")
    safe("136553_send", ar_send)
    ctx.close()

    # ---- Stored submissions (Form Manager, read-only) -------------------------
    ctx, pg = anon(b)
    em, pw = cms_role_credentials("Form Manager")
    CmsLoginPage(pg).open_login().login(em, pw)
    def stored():
        pg.goto(control_panel_url("/en/web/qatar-chamber/manage-inquiry"), timeout=60000)
        pg.locator("table tbody tr").first.wait_for(timeout=90000)
        pg.wait_for_timeout(1500)
        sel = pg.locator("select").filter(has=pg.locator('option[value="50"]'))
        if sel.count():
            sel.first.select_option("50"); pg.wait_for_timeout(2500)
        rows = pg.locator("table tbody tr").all_inner_texts()
        out = {}
        for tc in ("136485", "136495", "136472", "136553"):
            out[tc] = [r.replace("\n", " ")[:300] for r in rows if f"QCTEST-{tc}" in r]
        pg.screenshot(path=SHOT.format("stored-inquiries"), full_page=True)
        return {"total_rows_seen": len(rows), "matches": out}
    safe("stored", stored)
    ctx.close()
    b.close()

json.dump(OUT, open("reports/manual-129390.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("done")

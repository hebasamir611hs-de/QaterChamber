"""Step-5 follow-up (Editor + anonymous, under c7 lock). QCTEST records only, deleted by exact title.
A) image refusal at Submit: EN >3 MB, EN .gif, AR .bmp — picker outcome, Submit refusal, persisted file.
B) inactive banner: workflow state from the edit form's "Editing <title> (<State>)" line, and
   anonymous /home absence."""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"D:\MCP servers\QaterChamper")
from PIL import Image
from playwright.sync_api import sync_playwright

from cms.pages.home_promo_banners.home_promo_banners_admin_page import PromotionalBannerAdminPage
from config.settings import web_url

IMG = r"D:\MCP servers\QaterChamper\cms\tests\home_promo_banners\fixtures\promo_banner_v2_qctest.png"
R = r"D:\MCP servers\QaterChamper\reports"
T = Path(tempfile.gettempdir())
big = T / "QCTEST-m3-big.jpg"
Image.frombytes("RGB", (1400, 1400), os.urandom(1400 * 1400 * 3)).save(big, "JPEG", quality=95)
gif = T / "QCTEST-m3.gif"
Image.new("RGB", (40, 20), (120, 20, 40)).save(gif, "GIF")
bmp = T / "QCTEST-m3.bmp"
Image.new("RGB", (40, 20), (120, 20, 40)).save(bmp, "BMP")
out = {"big_bytes": big.stat().st_size}
E = "Site Content Editor"


def edit_state(page, title):
    m = re.search(r"Editing\s+" + re.escape(title) + r"\s*\(([^)]+)\)", page.locator("body").inner_text())
    return m.group(1) if m else ""


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={"width": 1920, "height": 1080}).new_page()
    a = PromotionalBannerAdminPage(page)
    for key, other, fpath, tag in (("image_en", "image_ar", big, "en-big"), ("image_en", "image_ar", gif, "en-gif"),
                                   ("image_ar", "image_en", bmp, "ar-bmp")):
        title = f"QCTEST-135232-m3-{tag}"
        r = {}
        try:
            a.open_form(E)
            a.fill_required(title, skip=(key,), files={other: IMG}, active=False)
            try:
                r["picker_rejected"] = a.upload_rejected(key, str(fpath), tag=f"m3-{tag}")
            except Exception as e:  # noqa: BLE001
                r["picker_error"] = str(e)[:150]
            r["field_after_pick"] = a.uploaded_filename(a.spec(key).label)
            page.screenshot(path=rf"{R}\manual-repro-129368-image-{tag}-picked.png")
            a.submit_for_review()
            r["refusal"] = a.refusal_visible()
            r["refusal_text"] = a.refusal_text()[:220]
            page.screenshot(path=rf"{R}\manual-repro-129368-image-{tag}-submit.png")
            r["status"] = a.status_of(title, E)
            r["status_raw"] = a.last_status_raw
            if r["status"]:
                a.open_entry_by_edit_link(title)
                r["persisted_file"] = a.value(key)
        except Exception as e:  # noqa: BLE001
            r["error"] = str(e)[:250]
        finally:
            r["deleted"] = a.delete_disposable(title)
        out[tag] = r

    title = "QCTEST-135186-m3-inactive"
    r = {}
    actx = b.new_context(viewport={"width": 1920, "height": 1080})
    anon = actx.new_page()
    try:
        a.open_form(E)
        a.fill_required(title, files={"image_en": IMG, "image_ar": IMG}, active=False)
        a.submit_for_review()
        r["list_badge"] = a.status_of(title, E) and a.last_status_raw
        a.open_entry_by_edit_link(title)
        r["edit_state"] = edit_state(page, title)
        r["active_ticked"] = a.flag("active_status")
        r["unpublish_btn"] = page.locator(a.UNPUBLISH_BUTTON).count()
        page.screenshot(path=rf"{R}\manual-repro-129368-135186-inactive-edit.png")
        seen = []
        for _ in range(4):
            anon.goto(web_url("/home"), wait_until="domcontentloaded")
            anon.locator(".qc-promo-carousel").wait_for(timeout=40000)
            seen.append(anon.locator(f'.qc-promo-slide:not([data-clone]) img[alt="{title}"]').count())
            anon.wait_for_timeout(5000)
        r["anon_home_counts"] = seen
        # tick Active and re-submit: does it go live (proves state was Published underneath)?
        a.set_flag("active_status", True)
        a.submit_for_review()
        r["after_activate_badge"] = a.status_of(title, E)
        a.open_entry_by_edit_link(title)
        r["after_activate_edit_state"] = edit_state(page, title)
    except Exception as e:  # noqa: BLE001
        r["error"] = str(e)[:250]
    finally:
        r["deleted"] = a.delete_disposable(title)
        actx.close()
    out["inactive"] = r

    a.open_list(E)
    rows = [x.split("\t")[0].strip() for x in page.locator("table tbody tr").all_inner_texts()]
    out["swept"] = {t: a.delete_disposable(t) for t in rows if t.startswith(("QCTEST-1351", "QCTEST-1352"))}
    a.open_list(E)
    out["rows_final"] = [x.split("\t")[0].strip() for x in page.locator("table tbody tr").all_inner_texts()]
    b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))

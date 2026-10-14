"""Step-5 manual repro (Editor, under c7 lock), all on QCTEST records deleted by exact title.
A) 135232/135235: a 3.5 MB JPG into Banner Image (EN) and (AR) — does the picker attach it, and
   does Submit accept + persist it?
B) INACTIVE badge: an Editor-submitted banner with Active Status unticked — what does the list show,
   and what does the History trail / edit banner say about its workflow state?
C) cleanup sweep of this PBI's QCTEST rows."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"D:\MCP servers\QaterChamper")
from PIL import Image
from playwright.sync_api import sync_playwright

from cms.pages.home_promo_banners.home_promo_banners_admin_page import PromotionalBannerAdminPage

IMG = r"D:\MCP servers\QaterChamper\cms\tests\home_promo_banners\fixtures\promo_banner_v2_qctest.png"
R = r"D:\MCP servers\QaterChamper\reports"
big = Path(tempfile.gettempdir()) / "QCTEST-manual-135232-big.jpg"
Image.frombytes("RGB", (2600, 2600), os.urandom(2600 * 2600 * 3)).save(big, "JPEG", quality=100)
out = {"big_bytes": big.stat().st_size}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={"width": 1920, "height": 1080}).new_page()
    a = PromotionalBannerAdminPage(page)
    E = "Site Content Editor"
    for key, other, tag in (("image_en", "image_ar", "en"), ("image_ar", "image_en", "ar")):
        title = f"QCTEST-135232-manual-{tag}"
        r = {}
        try:
            a.open_form(E)
            a.fill_required(title, skip=(key,), files={other: IMG}, active=False)
            rejected = a.upload_rejected(key, str(big), tag=f"manual-{tag}")
            r["picker_rejected"] = rejected
            r["field_after_pick"] = a.uploaded_filename(a.spec(key).label)
            page.screenshot(path=rf"{R}\manual-repro-129368-135232-{tag}-picked.png")
            a.submit_for_review()
            r["refusal"] = a.refusal_visible()
            r["refusal_text"] = a.refusal_text()[:200]
            page.screenshot(path=rf"{R}\manual-repro-129368-135232-{tag}-submit.png")
            r["status"] = a.status_of(title, E)
            r["status_raw"] = a.last_status_raw
            if r["status"]:
                a.open_entry_by_edit_link(title)
                r["persisted_file"] = a.value(key)
        except Exception as e:  # noqa: BLE001
            r["error"] = str(e)[:300]
        finally:
            r["deleted"] = a.delete_disposable(title)
        out[key] = r

    title = "QCTEST-135186-manual-inactive"
    r = {}
    try:
        a.open_form(E)
        a.fill_required(title, files={"image_en": IMG, "image_ar": IMG}, active=False)
        a.submit_for_review()
        r["status_after_submit"] = a.status_of(title, E)
        r["raw"] = a.last_status_raw
        r["row_actions"] = page.evaluate(
            """t => { const tr = Array.from(document.querySelectorAll('table tbody tr')).find(x => x.innerText.includes(t));
            return tr ? Array.from(tr.querySelectorAll('*')).flatMap(e => Array.from(e.attributes).filter(x => x.name.startsWith('data-qc-oel-')).map(x => x.name)) : null; }""",
            title)
        page.screenshot(path=rf"{R}\manual-repro-129368-135186-inactive-list.png")
        r["history"] = a.history_entries(title)
        a.open_list(E)
        a.open_entry_by_edit_link(title)
        r["edit_banner"] = a.editing_banner_text()[:240]
        page.screenshot(path=rf"{R}\manual-repro-129368-135186-inactive-edit.png")
    except Exception as e:  # noqa: BLE001
        r["error"] = str(e)[:300]
    finally:
        r["deleted"] = a.delete_disposable(title)
    out["inactive"] = r

    a.open_list(E)
    rows = [x.split("\t")[0].strip() for x in page.locator("table tbody tr").all_inner_texts()]
    out["rows_before_sweep"] = rows
    out["swept"] = {t: a.delete_disposable(t) for t in rows if t.startswith(("QCTEST-1351", "QCTEST-1352"))}
    a.open_list(E)
    out["rows_final"] = [x.split("\t")[0].strip() for x in page.locator("table tbody tr").all_inner_texts()]
    b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))

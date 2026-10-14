"""
cms/tests/a9_cases.py - check bodies written by Engineer A9 (2026-10-07) for the cases of PBIs
130949 (Proposal for Research), 130947 (Certificate of Origin), 130717 (Request to Join a
Committee) and 130719 (Business Council Membership) that had never run because of automation
gaps. Not a test module: the test functions in each PBI's test file call these.

Rules applied (standards.md / bug-rules.md / CLAUDE.md):
  * accounts through cms_role_credentials() (Editor, Author, Contributor, Form Manager); never TEST_USER;
  * every record this code creates is a QCTEST record reached through "+ Add New" and deleted BY ID
    after its stored JSON is checked (title / relationship) - never by position;
  * public reads in a fresh logged-out context (new_context(browser, use_auth_state=False));
  * Documents & Media files are never deleted (uploads are logged as leftovers);
  * live records (99844, 99886, 441112) are written only inside reports/live-restore/a9_cycle.py
    (QC_A9_LIVE_RUN=<id>): snapshot -> this one test -> restore -> verify;
  * a missing toast or different wording is never asserted; char limits are N/A.
Evidence: reports/bug-evidence/a9-<group>/.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cms.pages.components.disposable_object_admin import ROLE_AUTHOR, ROLE_EDITOR
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.tests import live_b11 as lb
from config.settings import web_url

RUN = time.strftime("%m%d%H%M")
ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / "reports" / "bug-evidence"
LEFTOVERS = ROOT / "reports" / "live-restore" / "a9" / "leftovers.txt"
A9_GATE = "QC_A9_LIVE_RUN"
NEVER = {"181385", "208073", "183176"}
PFR_PATH = "/our-services/proposal-for-research"
COO_PATH = "/our-services/certificate-of-origin-online"
JOIN_PATH = "/web/qatar-chamber/request-to-join-a-committee"


def a9_gate(eid: str):
    return pytest.mark.skipif(
        os.environ.get(A9_GATE) != eid,
        reason=f"LIVE record {eid}: runs only under reports/live-restore/a9_cycle.py with {A9_GATE}={eid}")


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def log(msg: str):
    print(f"[a9] {msg}", flush=True)


def leftover(line: str):
    LEFTOVERS.parent.mkdir(parents=True, exist_ok=True)
    with LEFTOVERS.open("a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {line}\n")


def shot(p, group: str, name: str):
    d = EVID / f"a9-{group}"
    d.mkdir(parents=True, exist_ok=True)
    try:
        p.screenshot(path=str(d / f"{name}.png"), full_page=True)
    except Exception:  # noqa: BLE001 - evidence never masks the result
        pass


def dump(group: str, name: str, obj):
    d = EVID / f"a9-{group}"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def anon(browser, **kw):
    if kw.pop("accept_downloads", False):  # core new_context() has no downloads switch: a bare logged-out context
        vp = kw.pop("viewport", (1920, 1080))
        ctx = browser.new_context(accept_downloads=True, viewport={"width": vp[0], "height": vp[1]})
        return ctx, ctx.new_page()
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False, **kw)
    return ctx, ctx.new_page()


def visit(p, path, locale="en", settle=None):
    resp = p.goto(web_url(path, locale=locale), wait_until="domcontentloaded", timeout=60000)
    try:
        p.wait_for_load_state("networkidle", timeout=15000)
    except Exception:  # noqa: BLE001
        pass
    if settle:
        try:
            p.locator(settle).first.wait_for(state="attached", timeout=20000)
        except Exception:  # noqa: BLE001
            pass
    p.wait_for_timeout(1500)  # client-rendered fragments settle (measured ~1 s)
    return resp.status if resp else None


def poll(p, path, fn, locale="en", timeout=90.0, settle=None):
    """Reload the logged-out page until fn(page) -> (ok, info)."""
    t0 = time.monotonic()
    while True:
        http = visit(p, path, locale, settle)
        ok, info = fn(p)
        if ok or time.monotonic() - t0 > timeout:
            info = dict(info or {}, http=http, seconds=round(time.monotonic() - t0, 1))
            return ok, info
        p.wait_for_timeout(3000)


def get_json(admin, plural, eid):
    st, txt = lb.req(admin, "GET", f"/o/c/{plural}/{eid}")
    if st != 200:
        return None
    try:
        return json.loads(txt)
    except ValueError:
        return None


def editorial(admin, eid) -> str:
    st, txt = lb.req(admin, "GET", f"/o/qc-object-status/transitions/{eid}")
    try:
        return json.loads(txt).get("statusLabelEn", "") if st == 200 else ""
    except ValueError:
        return ""


def wait_editorial(admin, eid, want, timeout=45.0) -> str:
    t0 = time.monotonic()
    while True:
        st = editorial(admin, eid)
        if st == want or time.monotonic() - t0 > timeout:
            return st
        admin.page.wait_for_timeout(2000)


def open_by_id(admin, plural, eid, role=ROLE_EDITOR):
    """Open an existing record's edit form by its own ERC (read by id)."""
    assert str(eid) not in NEVER, f"refusing to open protected record {eid}"
    admin.open_list(role)
    data = get_json(admin, plural, eid)
    assert data, f"{plural}/{eid} unreadable"
    try:
        admin.open_entry_by_code(data["externalReferenceCode"], locale="en")
    except Exception as exc:  # noqa: BLE001 - previous save's redirect may abort it once
        if "ERR_ABORTED" not in str(exc):
            raise
        admin.page.wait_for_timeout(2000)
        admin.open_entry_by_code(data["externalReferenceCode"], locale="en")
    admin.page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).first.wait_for(state="visible", timeout=40000)
    admin.page.wait_for_timeout(1500)  # editors hydrate with the stored value (measured ~1 s)
    ident = admin._ident()
    ident["editing"] = (plural, str(eid))
    ident["pending"] = None
    return data


def saved(admin, eid) -> bool:
    ls = admin.last_save or {}
    return bool(ls.get("started")) and str(ls.get("id") or "") == str(eid)


def delete_by_id(admin, plural, eid, needle, guard, role=ROLE_EDITOR) -> bool:
    """Delete OUR record by id: its stored JSON must pass `guard` first. Never raises."""
    try:
        eid = str(eid)
        assert eid not in NEVER
        data = get_json(admin, plural, eid)
        if data is None:
            return True
        if not guard(data):
            leftover(f"NOT DELETED {plural}/{eid}: guard refused ({needle[:50]!r})")
            return False
        admin.open_list(role)
        box = admin.page.locator('input[placeholder^="Search entries"]')
        link = admin.page.locator(f'a[data-qc-oel-delete="{eid}"]')
        for _ in range(3):
            if link.count():
                break
            if box.count():
                box.fill(needle[:40])
                box.press("Enter")
            try:
                link.first.wait_for(state="attached", timeout=8000)
            except Exception:  # noqa: BLE001
                continue
        if not link.count():
            leftover(f"NOT DELETED {plural}/{eid}: no Delete control ({needle[:50]!r})")
            return False
        with admin.page.expect_response(lambda r: f"/o/qc-object-status/trash/{eid}" in r.url, timeout=30000) as ri:
            admin.page.once("dialog", lambda d: d.accept())
            link.first.click(force=True)
        ok = ri.value.status < 400
        if not ok:
            leftover(f"trash refused {plural}/{eid}: HTTP {ri.value.status}")
        log(f"deleted {plural}/{eid} ({needle[:40]!r}) -> {ri.value.status}")
        return ok
    except Exception as exc:  # noqa: BLE001
        leftover(f"delete error {plural}/{eid}: {str(exc)[:160]}")
        return False


def exact_file(src_or_bytes, name: str) -> str:
    dest = Path(tempfile.gettempdir()) / "qctest_a9" / name
    dest.parent.mkdir(exist_ok=True)
    if isinstance(src_or_bytes, (bytes, bytearray)):
        dest.write_bytes(src_or_bytes)
    else:
        shutil.copy(src_or_bytes, dest)
    return str(dest)


def make_pdf(size: int) -> bytes:
    from tools import fixture_factory as ff

    return ff.make_pdf(size)


def history(admin, eid, needle) -> list[dict]:
    """History trail (ul.qc-oel__history-list) of the row whose control carries this id, newest LAST."""
    box = admin.page.locator('input[placeholder^="Search entries"]')
    ctl = admin.page.locator(f'[data-qc-oel-history="{eid}"]')
    for _ in range(3):
        if ctl.count():
            break
        if box.count():
            box.fill(needle[:40])
            box.press("Enter")
        try:
            ctl.first.wait_for(state="attached", timeout=8000)
        except Exception:  # noqa: BLE001
            continue
    if not ctl.count():
        return []
    ctl.first.click(force=True)
    lst = admin.page.locator("ul.qc-oel__history-list").first
    try:
        lst.wait_for(state="visible", timeout=10000)
        lst.locator(".qc-oel__history-who:not(:empty)").first.wait_for(state="attached", timeout=10000)
    except Exception:  # noqa: BLE001
        pass
    items = lst.locator(":scope > li")
    out = []
    for i in range(items.count()):
        it = items.nth(i)

        def part(sel):
            n = it.locator(sel)
            return " ".join(n.first.inner_text().split()) if n.count() else ""

        out.append({"action": part(".qc-oel__history-action"), "who": part(".qc-oel__history-who"),
                    "when": part(".qc-oel__history-when"), "comment": part(".qc-oel__history-comment"),
                    "text": " ".join(it.inner_text().split())[:300]})
    out.reverse()
    return out


def parse_when(s: str):
    for fmt in ("%m/%d/%Y, %I:%M:%S %p", "%d/%m/%Y, %H:%M:%S", "%m/%d/%Y, %H:%M:%S", "%d/%m/%Y, %H:%M"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


# ===========================================================================
# 130949 PFR - Information Group / Group Item bed (QCTEST, Active, high order)
# ===========================================================================
SIG, SIGI = "serviceinformationgroups", "serviceinformationgroupitems"
REL = "r_serviceInformationGroupItems_c_serviceInformationGroupId"
GUIDE_JS = r"""(label) => {
  const g = [...document.querySelectorAll('.qc-pfr-guide')].find(x =>
     ((x.querySelector('p.qc-pfr-guide-label') || {}).innerText || '').trim() === label);
  if (!g) return null;
  const items = [...g.querySelectorAll('.qc-pfr-guide-item')];
  const list = g.querySelector('.qc-pfr-guide-list');
  const intro = g.querySelector('.qc-pfr-guide-intro');
  const gr = g.getBoundingClientRect();
  return {items: items.map(i => { const s = getComputedStyle(i);
            return {text: i.innerText.trim(), font: s.fontFamily, weight: s.fontWeight, size: s.fontSize,
                    lh: s.lineHeight, color: s.color, h: i.getBoundingClientRect().height}; }),
          dots: [...g.querySelectorAll('.qc-pfr-guide-dot')].map(d => d.className),
          introH: intro ? intro.getBoundingClientRect().height : null,
          list: list ? {h: list.getBoundingClientRect().height, n: list.children.length,
                        mt: getComputedStyle(list).marginTop, mb: getComputedStyle(list).marginBottom} : null,
          intro: intro ? intro.innerText.trim() : null,
          introBottom: intro ? intro.getBoundingClientRect().bottom : null,
          groupBottom: gr.bottom, groupPadBottom: getComputedStyle(g).paddingBottom,
          lastChild: g.lastElementChild ? g.lastElementChild.className : null};
}"""
STYLE_OK = {"weight": "400", "size": "14px", "lh": "22px", "color": "rgb(52, 52, 50)"}


def style_ok(item) -> bool:
    return "cairo" in item["font"].lower() and all(item[k] == v for k, v in STYLE_OK.items())


class GroupBed:
    """Two QCTEST Information Groups (Active, display order 9990/9991) with QCTEST Group Items linked
    through the 'Group Items' relationship picker. Item labels are the case's own texts (copied from the
    QCDEMO groups 99904 / 99932); the QCTEST group label carries the disposable prefix."""

    def __init__(self, browser):
        from cms.pages.proposal_for_research.proposal_for_research_admin_page import (
            GroupItemAdminPage, InformationGroupAdminPage)
        from core.web.browser import new_context

        self.ctx = new_context(browser, use_auth_state=False, viewport=(1920, 1080))
        self.page = self.ctx.new_page()
        self.g = InformationGroupAdminPage(self.page)
        self.i = GroupItemAdminPage(self.page)
        self.label_a = f"QCTEST-130949-A9{RUN} Preparing your proposal"
        self.label_b = f"QCTEST-130949-A9{RUN} Supporting information"
        self.groups: dict[str, str] = {}   # label -> id
        self.items: dict[str, list] = {"A": [], "B": []}  # [{id, en, ar, order, active}]

    # ---- create ------------------------------------------------------
    def _demo(self, gid):
        self.g.open_list(ROLE_EDITOR)
        st, txt = lb.req(self.g, "GET", f"/o/c/{SIGI}/scopes/37246?pageSize=100&sort=displayOrder:asc")
        items = [i for i in json.loads(txt)["items"] if str(i.get(REL)) == str(gid)]
        items.sort(key=lambda i: i["displayOrder"])
        return [((i["itemLabel_i18n"].get("en_US") or ""), (i["itemLabel_i18n"].get("ar_SA") or "")) for i in items]

    def create_group(self, label, order, intro=None):
        self.g.open_form(ROLE_EDITOR)
        self.g.fill_required(label, active=True)
        self.g.fill("display_order", str(order))
        if intro:
            self.g.fill("group_intro", intro[0])
            self.g.fill("group_intro", intro[1], locale="ar")
        self.g.submit_for_review()
        gid = self.g.id_for(label)
        assert gid, f"group {label!r}: the Editor submit stored no record ({self.g.save_counts()})"
        self.groups[label] = gid
        st = wait_editorial(self.g, gid, STATUS_PUBLISHED)
        assert st == STATUS_PUBLISHED, f"group {gid} is {st!r} after the Editor submit"
        log(f"group {gid} {label!r} Published")
        return gid

    def pick_group(self, label):
        p = self.i.page
        ids = p.evaluate(f"""() => {{ const h = document.querySelector('input[name="ObjectField_{REL}"]');
            const base = h.id.replace(/-value-input$/, ''); return [base + '-select-from-list-input', base + '-listbox']; }}""")
        combo = p.locator(f"#{ids[0]}")
        opt = p.locator(f'#{ids[1]} [role="option"]', has_text=label).first
        for attempt, typed in enumerate((label[:28], label, "")):
            combo.click()
            combo.fill("")
            if typed:
                combo.press_sequentially(typed, delay=20)
            else:
                p.locator(f'button[aria-controls="{ids[1]}"]').first.click()
            try:
                opt.wait_for(state="visible", timeout=10000)
                break
            except Exception:  # noqa: BLE001 - search result not loaded yet: try the next way
                if attempt == 2:
                    shot(p, "pfr", f"picker_fail_{RUN}")
                    dump("pfr", f"picker_fail_{RUN}", {"listbox": p.locator(f"#{ids[1]}").inner_html()[:3000]})
                    raise
        opt.click()
        val = p.locator(f'input[name="ObjectField_{REL}"]').input_value()
        assert val == self.groups[label], f"relationship picker holds {val!r}, not group {self.groups[label]}"

    def create_item(self, key, label, en, ar, order, active=True):
        self.i.open_form(ROLE_EDITOR)
        self.pick_group(label)
        self.i._ident()["pending"] = en
        self.i.fill("item_label", en)
        self.i.fill("item_label", ar, locale="ar")
        self.i.set_flag("active_status", active)
        box = self.i.page.locator('input[name="ObjectField_displayOrder"]').first
        for _ in range(3):  # condition: the value must still be in the input at submit time
            box.fill(str(order))
            box.press("Tab")
            self.i.page.wait_for_timeout(300)
            if box.input_value() == str(order):
                break
        self.i.submit_for_review()
        eid = (self.i.last_save or {}).get("id")
        assert eid, f"item {en!r}: no record stored ({self.i.save_counts()})"
        data = get_json(self.i, SIGI, eid)
        assert data and str(data.get(REL)) == str(self.groups[label]), (
            f"item {eid} is not linked to group {self.groups[label]}: {(data or {}).get(REL)!r}")
        assert en in (data.get("itemLabel_i18n") or {}).get("en_US", ""), f"item {eid} EN label stored {data.get('itemLabel_i18n')!r}"
        rec = {"id": str(eid), "en": en, "ar": ar, "order": order, "active": active}
        self.items[key].append(rec)
        log(f"item {eid} order={order} active={active} {en[:40]!r} -> group {self.groups[label]}")
        return rec

    def build(self):
        a = self._demo(99904)
        b = self._demo(99932)
        assert len(a) == 6 and len(b) == 4, f"QCDEMO groups changed: {len(a)} / {len(b)} bullets"
        self.demo = {"A": a, "B": b}
        self.create_group(self.label_a, 9990)
        self.create_group(self.label_b, 9991, intro=(
            "Relevant supporting materials may be included to provide additional context for the proposed research topic.",
            "يمكن إرفاق مواد داعمة ذات صلة لتوفير سياق إضافي لموضوع البحث المقترح."))
        # created in REVERSE display order, so a render that followed creation order would fail
        for n in range(6, 0, -1):
            en, ar = a[n - 1]
            self.create_item("A", self.label_a, re.sub(r"<[^>]+>", "", en), re.sub(r"<[^>]+>", "", ar), n * 100)
        for n in range(4, 0, -1):
            en, ar = b[n - 1]
            self.create_item("B", self.label_b, re.sub(r"<[^>]+>", "", en), re.sub(r"<[^>]+>", "", ar), n * 100)
        for k in self.items:
            self.items[k].sort(key=lambda r: r["order"])

    # ---- edit --------------------------------------------------------
    def edit_item(self, rec, **changes):
        open_by_id(self.i, SIGI, rec["id"])
        if "en" in changes:
            self.i.fill("item_label", changes["en"])
        if "order" in changes:
            box = self.i.page.locator('input[name="ObjectField_displayOrder"]').first
            box.fill(str(changes["order"]))
            box.press("Tab")
        if "active" in changes:
            self.i.set_flag("active_status", changes["active"])
        self.i.submit_for_review()
        assert saved(self.i, rec["id"]), f"edit of item {rec['id']} did not save ({self.i.save_counts()})"
        rec.update(changes)
        data = get_json(self.i, SIGI, rec["id"])
        st = editorial(self.i, rec["id"])
        log(f"item {rec['id']} edited {changes} -> status {st!r} stored active={data.get('activeStatus')} "
            f"order={data.get('displayOrder')} en={(data.get('itemLabel_i18n') or {}).get('en_US', '')[:50]!r}")
        if "en" in changes:
            assert changes["en"] in (data.get("itemLabel_i18n") or {}).get("en_US", ""), "edited EN label not stored"
        return data, st

    def delete_item(self, rec):
        gids = set(self.groups.values())
        ok = delete_by_id(self.i, SIGI, rec["id"], rec["en"],
                          lambda d: str(d.get(REL)) in gids and str(d.get("id")) == rec["id"])
        if ok:
            for k in self.items:
                self.items[k] = [r for r in self.items[k] if r["id"] != rec["id"]]
        return ok

    # ---- public ------------------------------------------------------
    def read(self, p, key, locale="en"):
        label = self.label_a if key == "A" else self.label_b
        if locale == "ar":
            label = f"{label} AR"
        return p.evaluate(GUIDE_JS, label)

    def teardown(self):
        # Groups first: the relationship cascades to its items. Deleting the items first left
        # group 510184 undeletable (trash HTTP 400 "Delete failed: null", run 2026-10-07).
        for label, gid in self.groups.items():
            ok = delete_by_id(self.g, SIG, gid, label, lambda d, gid=gid: str(d.get("id")) == str(gid)
                              and str(d.get("groupLabel", "")).startswith("QCTEST-"))
            if not ok:
                try:
                    self.g.open_list(ROLE_EDITOR)
                    self.g.filter_entries(label)
                    ctl = self.g.page.locator(f'[data-qc-oel-unpublish="{gid}"]')
                    if ctl.count():
                        self.g.page.once("dialog", lambda d: d.accept())
                        ctl.first.click(force=True)
                        self.g.page.wait_for_timeout(3000)
                    leftover(f"LEFTOVER {SIG}/{gid} {label!r} not deleted; unpublish attempted -> {editorial(self.g, gid)!r}")
                except Exception as exc:  # noqa: BLE001
                    leftover(f"LEFTOVER {SIG}/{gid}: {str(exc)[:120]}")
        for k in ("A", "B"):
            for rec in list(self.items[k]):
                if get_json(self.i, SIGI, rec["id"]) is not None:
                    self.delete_item(rec)
        try:
            self.ctx.close()
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture(scope="module")
def pfr_bed(browser):
    bed = GroupBed(browser)
    try:
        bed.build()
        yield bed
    finally:
        bed.teardown()


def _bullets(bed, browser, key, ok_fn, what, locale="en", tc=""):
    ctx, p = anon(browser, viewport=(1920, 1080))
    try:
        def fn(pg):
            g = bed.read(pg, key, locale)
            return (g is not None and ok_fn(g)), {"group": g}

        ok, info = poll(p, PFR_PATH, fn, locale=locale, settle=".qc-pfr-guide")
        try:
            p.locator(".qc-pfr-guides").first.scroll_into_view_if_needed(timeout=5000)
        except Exception:  # noqa: BLE001
            pass
        shot(p, "pfr", f"{tc}_{key}_{locale}")
        dump("pfr", f"{tc}_{key}_{locale}", info)
        log(f"tc_{tc} public {locale} group {key}: ok={ok} {json.dumps(info, ensure_ascii=False)[:500]}")
        assert ok, f"{what} ({locale.upper()}, logged out): observed {json.dumps(info.get('group'), ensure_ascii=False)[:600]}"
        return info["group"]
    finally:
        ctx.close()


def texts_of(g):
    return [i["text"] for i in (g or {}).get("items", [])]


def pfr_141250(bed, browser):
    """Bullet 1 of the QCTEST group holds the case's EN/AR label; both render exactly, in the case's style."""
    first = bed.items["A"][0]
    assert first["en"] == "The proposed research title or topic." and first["ar"] == "عنوان البحث أو الموضوع المقترح.", first
    data = get_json(bed.i, SIGI, first["id"])
    assert editorial(bed.i, first["id"]) == STATUS_PUBLISHED
    assert first["ar"] in (data.get("itemLabel_i18n") or {}).get("ar_SA", ""), "AR label not stored"
    for loc, want in (("en", first["en"]), ("ar", first["ar"])):
        _bullets(bed, browser, "A", lambda g, w=want: bool(g["items"]) and g["items"][0]["text"] == w and style_ok(g["items"][0]),
                 f"first bullet reads {want!r} in Cairo 400 14px/22px #343432", loc, "141250")


def pfr_141293(bed, browser):
    """Group 1 bullet 5 Active -> six bullets, the fifth reads the case text in the case style."""
    b5 = bed.items["A"][4]
    if not b5["active"]:
        bed.edit_item(b5, active=True)
    assert b5["en"] == "The expected value or potential benefit of the study.", b5
    _bullets(bed, browser, "A", lambda g: len(g["items"]) == 6 and g["items"][4]["text"] == b5["en"] and style_ok(g["items"][4]),
             "six bullets, the fifth reads the case text in Cairo 400 14px/22px #343432", tc="141293")


def pfr_141294(bed, browser):
    """Bullet 5 Inactive -> five bullets, its text absent, the rest in order, no empty row."""
    b5 = bed.items["A"][4]
    others = [r["en"] for r in bed.items["A"] if r is not b5]
    _, st = bed.edit_item(b5, active=False)
    log(f"tc_141294 editorial state after Publish with Active unticked: {st!r}")
    try:
        _bullets(bed, browser, "A", lambda g: texts_of(g) == others and all(i["h"] > 0 for i in g["items"]),
                 "five bullets without 'The expected value or potential benefit of the study.', order kept, no empty row",
                 tc="141294")
    finally:
        bed.edit_item(b5, active=True)


def pfr_141305(bed, browser):
    """Display Order 1..6 (records created 6..1): bullets render 1..6."""
    want = [r["en"] for r in bed.items["A"]]
    _bullets(bed, browser, "A", lambda g: texts_of(g) == want, f"bullets in Display Order {want}", tc="141305")


def pfr_141331(bed, browser):
    """Add a 7th bullet (order 7, Active) -> seven bullets, the seventh reads the case text."""
    en, ar = "QCTEST The proposed timeline for the study.", "الجدول الزمني المقترح للدراسة."
    rec = bed.create_item("A", bed.label_a, en, ar, 700)  # case: 7 (refused by the live x100 rule)
    assert editorial(bed.i, rec["id"]) == STATUS_PUBLISHED, "the new bullet is not Published"
    _bullets(bed, browser, "A", lambda g: len(g["items"]) == 7 and g["items"][6]["text"] == en and style_ok(g["items"][6]),
             "seven bullets, the seventh reads 'QCTEST The proposed timeline for the study.' in the case style", tc="141331")


def pfr_141332(bed, browser):
    """Edit bullet 1 of the 'Supporting information' group -> the new label renders, the old one is gone."""
    b1 = bed.items["B"][0]
    old = b1["en"]
    assert old == "Existing reports or studies.", b1
    new = "QCTEST Existing reports or studies."
    bed.edit_item(b1, en=new)
    _bullets(bed, browser, "B", lambda g: bool(g["items"]) and g["items"][0]["text"] == new and old not in texts_of(g),
             f"first bullet reads {new!r} and {old!r} is no longer rendered", tc="141332")


def pfr_141333(bed, browser):
    """Delete the bullet identified by its exact text -> six bullets, the text appears nowhere."""
    en = "QCTEST The proposed timeline for the study."
    rec = next((r for r in bed.items["A"] if r["en"] == en), None)
    if rec is None:
        rec = bed.create_item("A", bed.label_a, en, "الجدول الزمني المقترح للدراسة.", 700)
    data = get_json(bed.i, SIGI, rec["id"])
    assert en in (data.get("itemLabel_i18n") or {}).get("en_US", ""), f"record {rec['id']} does not hold {en!r}"
    assert bed.delete_item(rec), f"delete of bullet {rec['id']} did not run"
    ctx, p = anon(browser, viewport=(1920, 1080))
    try:
        def fn(pg):
            g = bed.read(pg, "A")
            return (g is not None and len(g["items"]) == 6 and en not in pg.locator("body").inner_text()), {"group": g}

        ok, info = poll(p, PFR_PATH, fn, settle=".qc-pfr-guide")
        shot(p, "pfr", "141333_A_en")
        dump("pfr", "141333_A_en", info)
        assert ok, f"after delete: expected six bullets and no {en!r} anywhere; observed {json.dumps(info, ensure_ascii=False)[:500]}"
    finally:
        ctx.close()


def pfr_141334(bed, browser):
    """'Available data...' -> order 1 and 'The proposed research title...' -> order 6: first/sixth swap, middle unchanged."""
    first, last = bed.items["A"][0], bed.items["A"][5]
    assert last["en"].startswith("Available data"), last
    middle = [r["en"] for r in bed.items["A"][1:5]]
    bed.edit_item(last, order=100)   # case: 1 and 6 (refused by the live x100 rule)
    bed.edit_item(first, order=600)
    try:
        _bullets(bed, browser, "A", lambda g: texts_of(g) == [last["en"]] + middle + [first["en"]],
                 "first bullet 'Available data, references, or supporting information.', sixth 'The proposed research title or topic.', middle unchanged",
                 tc="141334")
    finally:
        bed.edit_item(last, order=600)
        bed.edit_item(first, order=100)
        bed.items["A"].sort(key=lambda r: r["order"])


def pfr_141343(bed, browser):
    """All four bullets of the 'Supporting information' group Inactive, group Active -> label + intro, no list, no gap."""
    for rec in bed.items["B"]:
        bed.edit_item(rec, active=False)

    def ok(g):
        # live markup (QCDEMO and QCTEST alike): the intro sits INSIDE .qc-pfr-guide-list after an
        # "is-empty" dot; each bullet adds a plain dot + .qc-pfr-guide-item. So "no bullet list" means no
        # item, no plain dot, and the list no taller than the intro itself.
        no_items = not g["items"]
        no_markers = all("is-empty" in d for d in g.get("dots", []))
        no_list_space = g["list"] is None or g["list"]["h"] <= (g.get("introH") or 0) + 2
        return bool(g["intro"]) and no_items and no_markers and no_list_space

    g = _bullets(bed, browser, "B", ok, "group label and intro render with no bullet list, no empty marker and no blank list space",
                 tc="141343")
    gap = (g["groupBottom"] - g["introBottom"]) if g.get("introBottom") else None
    log(f"tc_141343 space between the intro bottom and the group bottom: {gap}px (group padding-bottom {g['groupPadBottom']}), "
        f"list={g['list']}, last child={g['lastChild']!r}")
    pad = float(re.sub(r"[^0-9.]", "", g["groupPadBottom"] or "0") or 0)
    assert gap is not None and gap <= pad + 2, (
        f"a blank vertical gap of {gap}px is left under the group intro (group padding {pad}px, list {g['list']})")


# ===========================================================================
# 130949 PFR - Resource Item document swap (File Type / File Size, bug #148025)
# ===========================================================================
DRI = "downloadableresourceitems"
CARD_JS = r"""(title) => {
  const c = [...document.querySelectorAll('article.qc-pfr-file')].find(a =>
      ((a.querySelector('h3.qc-pfr-file-title') || {}).innerText || '').trim() === title);
  if (!c) return null;
  const meta = [...c.querySelectorAll('.qc-pfr-file-metaval')].map(e => e.innerText.trim());
  const a = c.querySelector('a.qc-pfr-dl');
  return {meta, href: a ? a.getAttribute('href') : null, label: a ? a.innerText.trim() : null};
}"""


def _human(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB" if n >= 1024 * 1024 else f"{round(n / 1024)} KB"


def _abs(href: str) -> str:
    return web_url(href) if href.startswith("/") and not href.startswith("//") else href


def _card_probe(title, cond):
    def fn(pg):
        c = pg.evaluate(CARD_JS, title)
        return (c is not None and cond(c)), {"card": c}
    return fn


def _fill_if_editable(adm, key, value):
    """2026-10-07 ~12:30: File Type / File Size became read-only ("Filled in by the system when the record is
    saved") - the #148025 fix. Typed only while the field is still editable."""
    box = adm.page.locator(f'input[name="ObjectField_{"fileType" if key == "file_type" else "fileSize"}"]').first
    if box.count() and not box.evaluate("e => e.readOnly || e.disabled"):
        adm.fill(key, value)
        return True
    return False


def pfr_resource_swap(page, browser, tc, hold_open=False):
    from cms.pages.proposal_for_research.proposal_for_research_admin_page import ResourceItemAdminPage

    adm = ResourceItemAdminPage(page)
    title = f"QCTEST-{tc}-{RUN} Research Proposal Template"
    v1_bytes, v2_bytes = make_pdf(200 * 1024), make_pdf(int(1.2 * 1024 * 1024))
    v1 = exact_file(v1_bytes, f"QCTEST-130949-template-{tc}-{RUN}.pdf")
    v2 = exact_file(v2_bytes, f"QCTEST-130949-template-v2-{tc}-{RUN}.pdf")
    eid = None
    ctx, p = anon(browser, viewport=(1920, 1080), accept_downloads=True)
    try:
        adm.open_form(ROLE_EDITOR)
        adm.fill_required(title, active=True, skip=("file_type", "file_size"))
        _fill_if_editable(adm, "file_type", "PDF")
        _fill_if_editable(adm, "file_size", "200 KB")
        adm.fill("display_order", "9995")
        adm.upload_file(adm.spec("resource_file").label, v1)
        adm.submit_for_review()
        eid = adm.id_for(title)
        assert eid, f"{title!r}: nothing stored ({adm.save_counts()})"
        assert wait_editorial(adm, eid, STATUS_PUBLISHED) == STATUS_PUBLISHED
        leftover(f"D&M upload kept (never deleted): {Path(v1).name} via {DRI}/{eid}")

        ok, before = poll(p, PFR_PATH, _card_probe(title, lambda c: c["meta"][:1] == ["PDF"] and bool(c["meta"][1:])),
                          settle="article.qc-pfr-file")
        shot(p, "pfr", f"{tc}_1_before_swap")
        assert ok, f"precondition: the QCTEST card does not show PDF / 200 KB: {before}"
        old_href = before["card"]["href"]

        # Steps 1-3: open the Published record WITHOUT unpublishing, replace the file, save
        open_by_id(adm, DRI, eid)
        st_open = editorial(adm, eid)
        adm.upload_file(adm.spec("resource_file").label, v2)
        adm.submit_for_review()
        assert saved(adm, eid), f"the swap did not save ({adm.save_counts()})"
        leftover(f"D&M upload kept (never deleted): {Path(v2).name} via {DRI}/{eid}")
        after = get_json(adm, DRI, eid)
        st = wait_editorial(adm, eid, STATUS_PUBLISHED)
        adm.open_list(ROLE_EDITOR)
        hist = history(adm, eid, title)
        res = {"status_when_opened": st_open, "status_after": st, "stored_file": (after.get("resourceFile") or {}).get("name"),
               "stored_fileSize_field": after.get("fileSize"), "stored_fileType_field": after.get("fileType"),
               "actual_v2_size": len(v2_bytes), "history": hist}
        assert st_open == STATUS_PUBLISHED and st == STATUS_PUBLISHED, f"page status left Published during the swap: {res}"
        assert not any("unpublish" in (h["action"] + h["text"]).lower() for h in hist), f"an Unpublish was recorded: {hist}"
        assert Path(v2).stem.lower() in json.dumps(after.get("resourceFile") or {}).lower(), f"v2 file not stored: {res}"

        if hold_open:  # the visitor page loaded before the swap is still open: its Download target is requested
            r = ctx.request.get(_abs(old_href))
            res["stale_click"] = {"http": r.status, "disposition": r.headers.get("content-disposition"),
                                  "bytes": len(r.body()) if r.status == 200 else 0}
            log(f"tc_{tc} stale-page Download -> {res['stale_click']}")
            assert r.status in (200, 404) and (r.status != 200 or res["stale_click"]["bytes"] > 0), f"stale click: {res['stale_click']}"

        want_size = _human(len(v2_bytes))
        ok, now = poll(p, PFR_PATH, _card_probe(title, lambda c: Path(v2).stem.lower() in (c["href"] or "").lower()),
                       settle="article.qc-pfr-file")
        shot(p, "pfr", f"{tc}_2_after_swap")
        res["public_after"] = now
        card = now.get("card") or {}
        dl = ctx.request.get(_abs(card.get("href") or ""))
        res["download"] = {"http": dl.status, "bytes": len(dl.body()) if dl.status == 200 else 0,
                           "disposition": dl.headers.get("content-disposition")}
        dump("pfr", f"{tc}_swap", res)
        log(f"tc_{tc} {json.dumps(res, ensure_ascii=False, default=str)[:900]}")
        assert ok and dl.status == 200 and res["download"]["bytes"] == len(v2_bytes), f"the download does not serve v2: {res['download']}"
        assert card["meta"][0] == "PDF", f"file type on the card: {card['meta']}"
        assert card["meta"][1] == want_size, (
            f"bug #148025: the card still shows File Size {card['meta'][1]!r} after the document swap; the served "
            f"file is {len(v2_bytes)} bytes ({want_size}) - File Size is a free-text field and is not re-captured")
    finally:
        ctx.close()
        if eid:
            delete_by_id(adm, DRI, eid, title, lambda d: str(d.get("resourceTitle", "")).startswith("QCTEST-"))


# ===========================================================================
# 130949 PFR 141341 - audit trail (History) for a content change
# ===========================================================================
def pfr_141341(page, browser):
    from cms.pages.proposal_for_research.proposal_for_research_admin_page import OverviewInfoCardAdminPage

    adm = OverviewInfoCardAdminPage(page)
    title = f"QCTEST-141341-{RUN} audit"
    body = "QCTEST-130949 audit trail check."
    eid = None
    try:
        adm.open_form(ROLE_EDITOR)
        adm.fill_required(title, active=True,
                          files={"card_icon": str(ROOT / "cms/tests/made_in_qatar_expo/fixtures/valid_icon_200kb.png")})
        adm.fill("overview_body", body)
        t_local = datetime.now()
        adm.submit_for_review()
        eid = adm.id_for(title)
        assert eid and wait_editorial(adm, eid, STATUS_PUBLISHED) == STATUS_PUBLISHED, f"publish failed ({adm.save_counts()})"
        data = get_json(adm, "overviewsectionandinfocards", eid)
        assert body in (data.get("overviewBody") or ""), f"Overview Body EN stored {data.get('overviewBody')!r}"
        adm.open_list(ROLE_EDITOR)
        hist = history(adm, eid, title)
        shot(adm.page, "pfr", "141341_history")
        dump("pfr", "141341_history", {"publish_local_time": t_local.isoformat(), "history": hist, "record": eid})
        log(f"tc_141341 publish at {t_local:%H:%M:%S} local; History newest-last: {hist}")
        assert hist, "no audit entry (History) for the record"
        newest = hist[-1]
        when = parse_when(newest["when"])
        blob = (newest["action"] + " " + newest["text"]).lower()
        assert "editor" in (newest["who"] + newest["text"]).lower(), f"newest entry not attributed to the Site Content Editor: {newest}"
        assert when is None or abs((when - t_local).total_seconds()) < 300, f"timestamp {newest['when']!r} vs publish {t_local}"
        assert any(w in blob for w in ("publish", "approv")), (
            f"the most recent audit entry does not record the publish action; it reads {newest['action']!r} ({newest['text']!r})")
    finally:
        if eid:
            delete_by_id(adm, "overviewsectionandinfocards", eid, title,
                         lambda d: str(d.get("cardTitle", "")).startswith("QCTEST-"))


# ===========================================================================
# 130947 COO - Action Button Behavior on a QCTEST COO Section (own section key)
# ===========================================================================
COO_SECTIONS = "coosections"
BUTTON_JS = r"""(key) => {
  const s = document.getElementById('qc-coo-' + key);
  if (!s) return null;
  const a = [...s.querySelectorAll('a')].find(x => /Certificate of Origin \(PDF\)/.test(x.innerText));
  return {section: true, title: ((s.querySelector('h2,h3') || {}).innerText || '').trim(),
          a: a ? {label: a.innerText.trim(), href: a.getAttribute('href'), target: a.getAttribute('target'),
                  download: a.getAttribute('download'), rel: a.getAttribute('rel')} : null};
}"""


def coo_behavior(page, browser, tc, option):
    """Create a QCTEST COO Section (own key, Active) whose Action Button carries a QCTEST compliance-guide PDF
    with Action Button Behavior = `option`, publish it as Editor, then check the rendered button logged out."""
    from cms.pages.certificate_of_origin.certificate_of_origin_admin_page import CooSectionAdminPage

    adm = CooSectionAdminPage(page)
    key = f"qctest-a9-{tc}-{RUN}".lower()
    title = f"QCTEST-{tc}-{RUN} Documents Required"
    pdf_bytes = make_pdf(300 * 1024)
    pdf = exact_file(pdf_bytes, f"QCTEST-130947-compliance-guide-{tc}-{RUN}.pdf")
    eid = None
    ctx, p = anon(browser, viewport=(1920, 1080), accept_downloads=True)
    res = {"tc": tc, "option": option, "key": key}
    try:
        adm.open_form(ROLE_EDITOR)
        adm.fill_required(title, active=True)
        adm.fill("section_key", key)
        adm.fill("section_number", "09")  # required on the live form (read 2026-10-07), not in the page object
        adm.fill("section_badge", "QCTEST Badge")
        adm.fill("section_badge", "شارة اختبار", locale="ar")
        adm.fill("pdf_button_label", "Certificate of Origin (PDF)")
        adm.fill("pdf_button_label", "شهادة المنشأ (PDF)", locale="ar")
        res["behavior_options"] = adm.select_options("pdf_button_behavior")
        log(f"tc_{tc} Action Button Behavior options: {res['behavior_options']}")
        assert option in res["behavior_options"], f"Action Button Behavior offers {res['behavior_options']}, not {option!r}"
        adm.select_option("pdf_button_behavior", option)
        adm.upload_file(adm.spec("pdf_button_file").label, pdf)
        adm.submit_for_review()
        eid = adm.id_for(title)
        assert eid, f"{title!r}: nothing stored ({adm.save_counts()})"
        st = wait_editorial(adm, eid, STATUS_PUBLISHED)
        assert st == STATUS_PUBLISHED, f"section {eid} is {st!r} after the Editor's Publish"
        leftover(f"D&M upload kept (never deleted): {Path(pdf).name} via {COO_SECTIONS}/{eid}")
        data = get_json(adm, COO_SECTIONS, eid)
        res["stored_behaviour"] = data.get("pdfButtonBehaviour")

        def fn(pg):
            info = pg.evaluate(BUTTON_JS, key)
            return bool(info and info.get("a")), {"button": info}

        ok, info = poll(p, COO_PATH, fn, settle=f"#qc-coo-{key}")
        res["public"] = info
        try:
            p.locator(f"#qc-coo-{key}").scroll_into_view_if_needed(timeout=5000)
        except Exception:  # noqa: BLE001
            pass
        shot(p, "coo", f"{tc}_1_button")
        assert ok, f"the QCTEST section's 'Certificate of Origin (PDF)' button is not rendered: {info}"
        a = info["button"]["a"]
        btn = p.locator(f"#qc-coo-{key} a", has_text="Certificate of Origin (PDF)").first
        start_url = p.url
        scroll_before = p.evaluate("() => window.scrollY")
        if option == "Same Tab":
            res["step2_target"] = a["target"]
            assert a["target"] != "_blank", f"the anchor carries target={a['target']!r}"
            downloads, pages = [], []
            p.on("download", lambda d: downloads.append(d))
            ctx.on("page", lambda pg: pages.append(pg))
            btn.click()
            p.wait_for_timeout(5000)  # navigation or download starts from the click (measured < 3 s)
            res["after_click"] = {"url": p.url, "tabs": len(ctx.pages), "new_pages": len(pages),
                                  "download": downloads[0].suggested_filename if downloads else None}
            shot(p, "coo", f"{tc}_2_after_click")
            assert len(ctx.pages) == 1, f"a second tab opened: {res['after_click']}"
            assert not downloads and p.url != start_url, (
                f"the guide did not open in the current tab: the click "
                f"{'downloaded ' + repr(downloads[0].suggested_filename) if downloads else 'left the page at ' + p.url}")
            p.go_back()
            p.wait_for_timeout(2000)
            res["after_back"] = p.url
            assert COO_PATH in p.url, f"Back returned to {p.url}"
        elif option == "New Tab":
            res["step2_target"] = a["target"]
            assert a["target"] == "_blank", f"the anchor carries target={a['target']!r}, not _blank"
            downloads = []
            ctx.on("page", lambda pg: pg.on("download", lambda d: downloads.append(d.suggested_filename)))
            p.on("download", lambda d: downloads.append(d.suggested_filename))
            with ctx.expect_page(timeout=20000) as newp:
                btn.click()
            np_ = newp.value
            try:
                np_.wait_for_load_state("domcontentloaded", timeout=15000)
                loaded = True
            except Exception:  # noqa: BLE001 - an attachment response never loads a document
                loaded = False
            p.wait_for_timeout(2000)
            res["after_click"] = {"new_tab_url": np_.url, "new_tab_loaded_document": loaded, "downloads": downloads,
                                  "tabs": len(ctx.pages), "orig_url": p.url,
                                  "scroll_before": scroll_before, "scroll_after": p.evaluate("() => window.scrollY")}
            assert loaded and not downloads, (f"a second tab opened but the compliance guide is not shown in it: "
                                              f"{res['after_click']}")
            shot(p, "coo", f"{tc}_2_original_tab")
            assert len(ctx.pages) == 2 and p.url == start_url, f"new tab behaviour: {res['after_click']}"
            assert abs(res["after_click"]["scroll_after"] - scroll_before) < 5, f"scroll moved: {res['after_click']}"
        else:  # Download
            res["step3_attrs"] = {"target": a["target"], "download": a["download"]}
            pages = []
            ctx.on("page", lambda pg: pages.append(pg))
            with p.expect_download(timeout=30000) as dl:
                btn.click()
            d = dl.value
            path = d.path()
            size = Path(path).stat().st_size if path else 0
            res["after_click"] = {"file": d.suggested_filename, "size": size, "tabs": len(ctx.pages),
                                  "new_pages": len(pages), "url": p.url, "scroll_before": scroll_before,
                                  "scroll_after": p.evaluate("() => window.scrollY")}
            shot(p, "coo", f"{tc}_2_after_download")
            assert size > 0 and not pages and p.url == start_url, f"download behaviour: {res['after_click']}"
            assert "compliance-guide" in d.suggested_filename.lower(), f"downloaded {d.suggested_filename!r}"
    finally:
        dump("coo", f"{tc}_behavior", res)
        log(f"tc_{tc} {json.dumps(res, ensure_ascii=False, default=str)[:900]}")
        ctx.close()
        if eid:
            delete_by_id(adm, COO_SECTIONS, eid, title, lambda d: str(d.get("sectionTitle", "")).startswith("QCTEST-"))


# ===========================================================================
# 130947 COO 141174 - Created / Last Modified audit dates (QCTEST COO Page Content draft)
# ===========================================================================
BANNER_RE = re.compile(r"Editing (?P<title>.+?) \((?P<state>[^)]+)\)\.\s*Created (?P<created>[\d/]+, [\d:]+), "
                       r"last modified (?P<modified>[\d/]+, [\d:]+)")


def _banner(p) -> dict:
    txt = " ".join(p.locator("body").inner_text().split())
    m = BANNER_RE.search(txt)
    return m.groupdict() if m else {"raw": (re.search(r"Editing .{0,200}", txt) or [""])[0]}


def coo_141174(page):
    """Step 1 (create a NEW COO page record) cannot be performed: on this singleton the "+ Add New" control is
    rendered `hidden` (data-qc-oel-add, read 2026-10-07, a9/explore/addnew_coo-page-content.json). Steps 2-4
    run on the approved live record 93657 under a9_cycle (snapshot -> run -> restore): the editing banner
    ("Created ..., last modified ...") is the only place the dates are shown."""
    from cms.pages.certificate_of_origin.certificate_of_origin_admin_page import CooPageContentAdminPage

    eid = "93657"
    assert os.environ.get(A9_GATE) == eid
    adm = CooPageContentAdminPage(page)
    res = {"step1": "not performable: '+ Add New' is hidden on the COO Page Content singleton"}
    try:
        data = lb.open_live(adm, eid)
        b1 = _banner(adm.page)
        res["banner_1"] = b1
        res["api_1"] = {"dateCreated": data.get("dateCreated"), "dateModified": data.get("dateModified")}
        res["form_date_labels"] = adm.page.evaluate(
            "() => [...document.querySelectorAll('label')].map(l => l.innerText.trim()).filter(t => /created|modified/i.test(t))")
        res["date_inputs"] = adm.page.locator('input[name*="reated"], input[name*="odified"]').count()
        shot(adm.page, "coo", "141174_1_banner")
        log(f"tc_141174 banner={b1} date labels={res['form_date_labels']} inputs={res['date_inputs']}")
        assert b1.get("created") and b1.get("modified"), f"Created / Last Modified are not shown: {b1}"
        assert res["date_inputs"] == 0, "an editable Created / Modified date input exists"
        adm.page.wait_for_timeout(65000)  # the case: wait at least one minute before the edit
        adm.page.context.clear_cookies()  # qcdev drops idle sessions (~30 s): a fresh sign-in, then the form again
        lb.open_live(adm, eid)
        title = (data.get("pageTitle_i18n") or {}).get("en_US", "")
        adm.fill("page_title", f"{title} QCTEST-141174")
        lb.publish(adm, eid)
        data2 = lb.live_json(adm, eid)
        try:
            lb.open_live(adm, eid)
        except Exception as exc:  # noqa: BLE001 - qcdev session drop during the 65 s wait (run 2026-10-07)
            res["reopen_retry"] = str(exc)[:120]
            adm.page.context.clear_cookies()
            lb.open_live(adm, eid)
        b2 = _banner(adm.page)
        shot(adm.page, "coo", "141174_2_after_edit")
        res["banner_2"] = b2
        res["api_2"] = {"dateCreated": data2.get("dateCreated"), "dateModified": data2.get("dateModified")}
        adm.open_list(ROLE_EDITOR)
        res["history_newest"] = history(adm, eid, title)[-2:]
        log(f"tc_141174 {json.dumps(res, ensure_ascii=False)[:900]}")
        assert b2.get("created") == b1.get("created") and res["api_2"]["dateCreated"] == res["api_1"]["dateCreated"], \
            f"Created changed on edit: {b1} -> {b2}"
        assert b2.get("modified") != b1.get("modified") and res["api_2"]["dateModified"] > res["api_1"]["dateModified"], \
            f"Last Modified did not advance: {b1} -> {b2}"
        assert res["history_newest"], "the edit is not recorded in the History trail"
    finally:
        dump("coo", "141174_audit_dates", res)


# ===========================================================================
# 130719 BCMR 144497 - Author forces the Publish transition (QCTEST page entries, Page Visible unticked)
# ===========================================================================
def bcmr_144497(page, browser):
    """The Author has no "+ Add New" on this singleton (read 2026-10-07: the manage page previews the live
    page with Submit for Review disabled), so the targets are two QCTEST entries the EDITOR creates
    (Page Visible unticked) and unpublishes: A = target of the Author's forced Publish, B = where the
    Editor's own Publish row action is observed to learn the request shape. 183176 is never touched."""
    from cms.pages.business_council_membership.business_council_membership_admin_page import (
        BusinessCouncilRequestPageAdminPage as Page)
    from core.web.browser import new_context

    author = Page(page)
    ctx_e = new_context(browser, use_auth_state=False)
    editor = Page(ctx_e.new_page())
    plural = Page.PLURAL
    ta, tb = f"QCTEST-144497-{RUN} A", f"QCTEST-144497-{RUN} B"
    ids, res = {}, {}
    try:
        for t in (ta, tb):
            editor.open_form(ROLE_EDITOR)
            editor.fill_required(t, active=False)
            editor.submit_for_review()
            eid = editor.id_for(t)
            assert eid and eid not in NEVER, f"{t!r}: the Editor's submit stored nothing ({editor.save_counts()})"
            ids[t] = eid
            if editorial(editor, eid) == STATUS_PUBLISHED:
                editor.open_list(ROLE_EDITOR)
                editor.filter_entries(t)
                ctl = editor.page.locator(f'[data-qc-oel-unpublish="{eid}"]')
                if ctl.count():
                    editor.page.once("dialog", lambda d: d.accept())
                    ctl.first.click(force=True)
                    editor.page.wait_for_timeout(3000)
        res["ids"] = ids
        res["state_A_before"] = editorial(editor, ids[ta])
        res["state_B_before"] = editorial(editor, ids[tb])
        log(f"tc_144497 QCTEST targets {ids} states A={res['state_A_before']!r} B={res['state_B_before']!r}")

        # Steps 1-2: the Author's own view of the page object
        author.sign_in(ROLE_AUTHOR)
        author.open(author.manage_url())
        author.page.wait_for_timeout(4000)
        res["author_view"] = author.page.evaluate(r"""() => ({
            submit: [...document.querySelectorAll('button')].filter(b => /Submit|Publish/.test(b.innerText) && b.offsetParent !== null).map(b => [b.innerText.trim(), b.disabled]),
            add_new: document.body.innerText.includes('+ Add New'),
            publish_controls: document.querySelectorAll('[data-qc-oel-publish],[data-qc-oel-approve]').length})""")
        shot(author.page, "bcmr", "144497_1_author_view")
        assert not res["author_view"]["publish_controls"], f"the Author is offered a Publish/Approve control: {res['author_view']}"

        # Observation: the Editor's own Publish row action on B
        editor.open_list(ROLE_EDITOR)
        editor.filter_entries(tb)
        reqs = []
        editor.page.on("request", lambda r: reqs.append({"method": r.method, "url": r.url, "body": r.post_data or ""})
                       if r.method in ("POST", "PUT", "PATCH") and "/o/" in r.url else None)
        editor.page.on("dialog", lambda d: d.accept("QCTEST A9 144497 observation") if d.type == "prompt" else d.accept())
        ctl = None
        for action in ("publish", "approve"):
            c = editor.page.locator(f'[data-qc-oel-{action}="{ids[tb]}"]')
            if c.count():
                ctl, res["observed_action"] = c, action
                break
        assert ctl is not None, f"the Editor is offered no publish/approve row action on B {ids[tb]} (state {res['state_B_before']!r})"
        ctl.first.click(force=True)
        editor.page.wait_for_timeout(4000)
        res["observed_requests"] = reqs
        res["state_B_after_editor"] = editorial(editor, ids[tb])
        shape = next((r for r in reqs if ids[tb] in r["url"] or ids[tb] in r["body"]), None)
        log(f"tc_144497 Editor {res.get('observed_action')} on B sent {reqs} -> {res['state_B_after_editor']!r}")
        assert shape, f"no transition request carrying B's id was observed: {reqs}"

        # Step 3: replay that request shape as the AUTHOR on A (Author session + CSRF)
        url = shape["url"].replace(ids[tb], ids[ta])
        body = shape["body"].replace(ids[tb], ids[ta]) if shape["body"] else None
        author.open(author.manage_url())
        author.page.wait_for_function("() => !!(window.Liferay && Liferay.authToken)", timeout=30000)
        token = author.page.evaluate("() => Liferay.authToken")
        headers = {"accept": "application/json", "x-csrf-token": token}
        if body:
            headers["content-type"] = "application/json" if body.strip().startswith(("{", "[")) else "application/x-www-form-urlencoded"
        r = author.page.context.request.fetch(url, method=shape["method"], headers=headers,
                                              data=body.encode("utf-8") if body else None)
        res["forced"] = {"method": shape["method"], "url": url, "http": r.status, "resp": r.text()[:300]}
        author.page.wait_for_timeout(2000)
        res["state_A_after"] = editorial(editor, ids[ta])
        editor.open_list(ROLE_EDITOR)
        res["history_A"] = history(editor, ids[ta], ta)
        shot(editor.page, "bcmr", "144497_2_after_forced")
        log(f"tc_144497 forced as Author: {res['forced']} -> A {res['state_A_before']!r} -> {res['state_A_after']!r}")
        assert res["forced"]["http"] >= 400, f"the forced Publish transition was accepted (HTTP {res['forced']['http']})"
        assert res["state_A_after"] == res["state_A_before"], f"state changed: {res['state_A_before']!r} -> {res['state_A_after']!r}"
    finally:
        dump("bcmr", "144497_forced_publish", res)
        for t, eid in ids.items():
            delete_by_id(editor, plural, eid, t, lambda d, t=t: str(d.get("pageTitle", "")).startswith("QCTEST-144497-")
                         and str(d.get("id")) not in NEVER)
        ctx_e.close()


# ===========================================================================
# 130719 BCMR 144600 - concurrent review, then the request's audit trail (History)
# ===========================================================================
def bcmr_144600(page, browser):
    from cms.pages.business_council_membership.business_council_membership_admin_page import (
        BusinessCouncilMembershipRequestAdminPage as Sub)
    from cms.pages.join_committee.council_base import ROLE_FORM_MANAGER as FM
    from cms.tests.sectoral_committees import cc_checks as cc
    from core.web.browser import new_context

    sub = Sub(page)
    res = {}
    needle = cc.create_bcmr_submission(browser, 144600)
    res["needle"] = needle
    ctx_b = new_context(browser, use_auth_state=False)
    try:
        sub_b = Sub(ctx_b.new_page())
        row = sub.find_row(needle, FM, timeout_s=45)
        if row is None:
            shot(sub.page, "bcmr", "144600_0_form_manager_list")
            erow = sub.find_row(needle, ROLE_EDITOR, timeout_s=45)
            res["editor_row_actions"] = sub.row_actions(erow) if erow is not None else None
            res["editor_row_has_history"] = bool(erow is not None and erow.locator("[data-qc-oel-history]").count())
            shot(sub.page, "bcmr", "144600_0_editor_list")
        assert row is not None, (f"precondition (TC-127 / 144592 scenario) cannot be performed: {FM} cannot see the "
                                 f"QCTEST request {needle!r} (same root cause as 144592 / 144501); Editor view: "
                                 f"{res.get('editor_row_actions')} history={res.get('editor_row_has_history')}")
        eid = sub.entry_id(row)
        res["entry_id"] = eid
        assert sub_b.find_row(needle, FM) is not None
        res["approve_dialogs"] = sub.approve(needle, FM)
        res["reject_dialogs"] = sub_b.reject(needle, "QCTEST-144600 concurrent", FM)
        res["final_status"] = sub.request_status(needle, FM)
        row = sub.find_row(needle, FM)
        hist_ctl = row.locator("[data-qc-oel-history]") if row is not None else None
        res["history_control"] = bool(hist_ctl is not None and hist_ctl.count())
        shot(sub.page, "bcmr", "144600_1_row")
        assert res["history_control"], (
            "no audit-log surface: the submission row offers no History control (data-qc-oel-history) to "
            f"{FM}; row actions {sub.row_actions(row) if row is not None else None}")
        hist_ctl.first.click(force=True)
        lst = sub.page.locator("ul.qc-oel__history-list").first
        lst.wait_for(state="visible", timeout=10000)
        sub.page.wait_for_timeout(1500)
        items = lst.locator(":scope > li")
        res["history"] = [" ".join(items.nth(i).inner_text().split())[:200] for i in range(items.count())]
        shot(sub.page, "bcmr", "144600_2_history")
        log(f"tc_144600 {json.dumps(res, ensure_ascii=False)[:900]}")
        appr = [h for h in res["history"] if "approv" in h.lower()]
        rej = [h for h in res["history"] if "reject" in h.lower()]
        assert len(appr) <= 1 and len(rej) <= 1, f"duplicate audit entries: {res['history']}"
        assert len(set(res["history"])) == len(res["history"]), f"duplicate/ghost audit entries: {res['history']}"
        final = res["final_status"].casefold()
        want = {"approved": (1, 0), "rejected": (1, 1)}.get(final)
        assert want and (len(appr), len(rej)) in (want, (0, 1) if final == "rejected" else want), (
            f"audit entries do not match the applied transitions (final {final!r}): {res['history']}")
    finally:
        dump("bcmr", "144600_concurrent_audit", res)
        ctx_b.close()


# ===========================================================================
# 130717 Join - approval / rejection email cases: submission recorded for a manual inbox check
# ===========================================================================
# The user's own inbox, named by the user for these email cases (decision 2026-10-07).
USER_INBOX = "heba.samir611.hs@gmail.com"


def _create_join(browser, tc, email, rec):
    from cms.tests.sectoral_committees import cc_checks as cc
    from web.pages.join_committee.join_committee_page import JoinCommitteePage

    company = f"QCTEST-{tc}-{cc.RUN} Join Co"
    ctx, p = anon(browser)
    try:
        jc = JoinCommitteePage(p)
        jc.open_join_committee(locale="en")
        jc.fill_all_valid(overrides={"company_name": company, "applicant_name": f"QCTEST-{tc}-{cc.RUN}", "email": email})
        rec["submitted_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            jc.submit_and_wait_result(timeout=45000)
        except Exception:  # noqa: BLE001
            pass
        rec["public_result"] = jc.status_banner_text()[:200] if hasattr(jc, "status_banner_text") else ""
        shot(p, "join", f"{tc}_0_public_submit")
        assert jc.success_message_is_visible(), f"the public form did not accept the submission: {rec['public_result']!r}"
        rec["company"] = company
        return company
    finally:
        ctx.close()


def join_email(page, browser, tc, action):
    from cms.pages.join_committee.council_base import ROLE_FORM_MANAGER as FM
    from cms.pages.join_committee.join_committee_admin_page import CommitteeJoiningRequestAdminPage as Sub
    from cms.tests.sectoral_committees import cc_checks as cc

    rec = {"tc": tc, "action": action, "recipient": USER_INBOX,
           "expected": ("Approval Notification email (subject MSG-9) to the applicant's address" if action == "approve"
                        else "NO email to the applicant")}
    sub = Sub(page)
    try:
        needle = _create_join(browser, tc, USER_INBOX, rec)
        row = sub.find_row(needle, FM)
        assert row is not None, f"{FM} cannot see {needle!r}"
        rec["reference_entry_id"] = sub.entry_id(row)
        rec["status_before"] = sub.request_status(needle, FM)
        if action == "approve":
            rec["dialogs"] = sub.approve(needle, FM)
        else:
            rec["dialogs"] = sub.reject(needle, f"QCTEST-{tc} incomplete documents", FM)
        rec["action_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        rec["final_status"] = sub.request_status(needle, FM)
        shot(sub.page, "join", f"{tc}_after_{action}")
        want = cc.REQ_APPROVED if action == "approve" else cc.REQ_REJECTED
        assert rec["final_status"].casefold() == want, f"status after {action}: {rec['final_status']!r}"
    finally:
        dump("join", f"{tc}_email_pending", rec)
        log(f"tc_{tc} PENDING USER EMAIL CHECK {rec}")
    pytest.skip(f"PENDING USER EMAIL CHECK: {action} at {rec.get('action_utc')} UTC, entry {rec.get('reference_entry_id')} "
                f"({rec.get('company')}), recipient {USER_INBOX}: {rec['expected']}")


def bcmr_144586(page, browser):
    """New Request Notification to the ADMIN inbox (subject 'New Business Council Membership Request Submitted -
    <company>'). The applicant address used is the user's inbox; the admin inbox is not known to automation."""
    from cms.pages.business_council_membership.business_council_membership_admin_page import (
        BusinessCouncilMembershipRequestAdminPage as Sub)
    from cms.tests.sectoral_committees import cc_checks as cc
    from web.pages.business_council_membership.business_council_membership_page import BusinessCouncilMembershipPage

    tc = 144586
    company = f"QCTEST-{tc}-{cc.RUN} BC Co"
    rec = {"tc": tc, "applicant_email": USER_INBOX, "company": company,
           "expected_admin_subject": f"New Business Council Membership Request Submitted \u2013 {company}",
           "admin_inbox": "not configured for automation - the user checks it"}
    ctx, p = anon(browser)
    try:
        bc = BusinessCouncilMembershipPage(p)
        bc.open_membership_request(locale="en")
        data = {f"country_{i}": c for i, c in enumerate(("GB", "DE", "FR", "IT"), 1)}
        data.update({"applicant_name": f"QCTEST-{tc}-{cc.RUN}", "company_name": company, "cr_number": "1234567",
                     "owner_name": "QCTEST Owner", "email": USER_INBOX, "mobile_number": "55123456",
                     "company_activity": "QCTEST activity"})
        bc.fill_form(data)
        rec["submitted_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        bc.submit()
        ok = bc.has_submission_succeeded(timeout=45000)
        shot(p, "bcmr", "144586_public_submit")
        assert ok, "the public BCMR form did not accept the submission"
    finally:
        ctx.close()
    sub = Sub(page)
    row = sub.find_row(company, ROLE_EDITOR, timeout_s=60)
    rec["reference_entry_id"] = sub.entry_id(row) if row is not None else ""
    rec["status"] = sub.request_status(company, ROLE_EDITOR) if row is not None else "not listed"
    dump("bcmr", "144586_email_pending", rec)
    log(f"tc_144586 PENDING USER EMAIL CHECK {rec}")
    assert row is not None, f"the submission {company!r} is not listed"
    pytest.skip(f"PENDING USER EMAIL CHECK: submitted {rec['submitted_utc']} UTC, entry {rec['reference_entry_id']} "
                f"({company}), status {rec['status']}; expected admin subject {rec['expected_admin_subject']!r}")

# ===========================================================================
# CKEditor toolbar driving (real toolbar buttons, CKEditor 4 classic chrome)
# ===========================================================================
def _cke(page, ref):
    box = page.locator(f'div.cke[class*="ObjectField_{ref}"]').first
    box.wait_for(state="visible", timeout=30000)
    return box


def _cke_body(page, ref):
    return _cke(page, ref).frame_locator("iframe").locator("body")


def cke_clear(page, ref):
    body = _cke_body(page, ref)
    body.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.wait_for_timeout(300)


def cke_heading(page, ref):
    _cke(page, ref).locator("a.cke_combo_button").first.click()
    panel = page.frame_locator("iframe.cke_panel_frame").last
    opt = panel.locator("a").filter(has_text=re.compile(r"^\s*Heading"))
    opt.first.wait_for(state="visible", timeout=10000)
    name = " ".join(opt.first.inner_text().split())
    opt.first.click()
    return name


def cke_button(page, ref, name):
    _cke(page, ref).locator(f"a.cke_button__{name}").first.click()
    page.wait_for_timeout(300)


def cke_type(page, text):
    page.keyboard.type(text, delay=15)


def cke_link(page, ref, text, url):
    """Type `text`, select it, and turn it into a link through the toolbar's Link dialog."""
    cke_type(page, text)
    for _ in range(len(text)):
        page.keyboard.press("Shift+ArrowLeft")
    cke_button(page, ref, "link")
    dlg = page.locator(".cke_dialog_container").locator("visible=true").last
    dlg.wait_for(state="visible", timeout=10000)
    # the dialog's first text box is "Display Text"; the URL box is the one its "URL" label points to
    url_id = dlg.evaluate(r"""d => { const l = [...d.querySelectorAll('label')].find(x => x.innerText.trim() === 'URL');
                                     return l ? l.getAttribute('for') : null; }""")
    url_box = dlg.locator(f"#{url_id}") if url_id else dlg.locator("input.cke_dialog_ui_input_text:visible").nth(1)
    url_box.fill(url)
    page.wait_for_timeout(300)
    dlg.locator("a.cke_dialog_ui_button_ok").first.click()
    page.wait_for_timeout(500)
    page.keyboard.press("End")


def cke_html(page, ref) -> str:
    return _cke_body(page, ref).inner_html()


RICH_JS = r"""(sel) => {
  const root = document.querySelector(sel);
  if (!root) return null;
  return {html: root.innerHTML.slice(0, 3000),
          headings: [...root.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => [h.tagName, h.innerText.trim()]),
          ul_items: [...root.querySelectorAll('ul > li')].map(li => li.innerText.trim()),
          paragraphs: [...root.querySelectorAll('p')].map(p => p.innerText.trim()).filter(Boolean),
          links: [...root.querySelectorAll('a')].map(a => [a.innerText.trim(), a.href])};
}"""


def pfr_rich(page, browser, tc):
    """141362 (99844 heroDescription) / 141363 (99886 overviewBody): toolbar-authored heading, list and link."""
    from cms.pages.proposal_for_research.proposal_for_research_admin_page import (
        OverviewInfoCardAdminPage, ProposalPageAdminPage)
    from web.pages.proposal_for_research.proposal_for_research_page import ProposalForResearchPage as R

    if tc == 141362:
        eid, A, ref, plural = "99844", ProposalPageAdminPage, "heroDescription", "proposalforresearchpages"
        heading, paras, items = "QCTEST Research scope", [], ["Economic topics", "Business topics"]
        link_lead, link_text, url = "Read more from ", "Research & Studies", "https://qcdev.ihorizons.com/en/about"
        public_sel = R.HERO_DESCRIPTION
    else:
        eid, A, ref, plural = "99886", OverviewInfoCardAdminPage, "overviewBody", "overviewsectionandinfocards"
        heading = "QCTEST How proposals are reviewed"
        paras = ["QCTEST Proposals are reviewed by the Research and Studies Department.",
                 "QCTEST Each proposal is assessed for relevance and feasibility."]
        items = ["Submission", "Review", "Feedback"]
        link_lead, link_text, url = "For questions, ", "contact the department", "https://qcdev.ihorizons.com/en/contact-us"
        public_sel = f"{R.SECTION}:has({R.OVERVIEW_CARDS}) {R.SECTION_BODY}"
    assert os.environ.get(A9_GATE) == eid
    admin = A(page)
    lb.open_live(admin, eid)
    p = admin.page
    res = {"tc": tc, "record": eid}
    cke_clear(p, ref)
    res["heading_option"] = cke_heading(p, ref)
    cke_type(p, heading)
    p.keyboard.press("Enter")
    for para in paras:
        cke_type(p, para)
        p.keyboard.press("Enter")
    cke_button(p, ref, "bulletedlist")
    for i, it in enumerate(items):
        cke_type(p, it)
        p.keyboard.press("Enter")
    p.keyboard.press("Enter")  # an empty list item ends the list
    cke_type(p, link_lead)
    cke_link(p, ref, link_text, url)
    res["editor_html"] = cke_html(p, ref)
    shot(p, "pfr", f"{tc}_1_editor")
    log(f"tc_{tc} editor html: {res['editor_html'][:600]}")
    lb.publish(admin, eid)
    stored = lb.live_json(admin, eid)
    res["stored_html"] = (stored.get(f"{ref}_i18n") or {}).get("en_US") or stored.get(ref)
    dump("pfr", f"{tc}_rich", res)
    sh = res["stored_html"] or ""
    assert re.search(rf"<h[1-6][^>]*>\s*{re.escape(heading)}\s*</h[1-6]>", sh), f"stored HTML has no heading {heading!r}: {sh[:500]}"
    assert all(re.search(rf"<li[^>]*>\s*{re.escape(it)}\s*</li>", sh) for it in items), f"stored HTML list: {sh[:500]}"
    assert f'href="{url}"' in sh and link_text.replace("&", "&amp;") in sh, f"stored HTML link: {sh[:500]}"

    ctx, ap = anon(browser, viewport=(1920, 1080))
    try:
        def fn(pg):
            r = pg.evaluate(RICH_JS, public_sel)
            ok = (bool(r) and any(h[1] == heading for h in r["headings"]) and all(i in r["ul_items"] for i in items)
                  and any(a == link_text and h.rstrip("/") == url.rstrip("/") for a, h in r["links"]))
            return ok, {"render": r}

        ok, info = poll(ap, PFR_PATH, fn, settle=public_sel)
        res["public"] = info
        try:
            ap.locator(public_sel).first.scroll_into_view_if_needed(timeout=5000)
        except Exception:  # noqa: BLE001
            pass
        shot(ap, "pfr", f"{tc}_2_public")
        dump("pfr", f"{tc}_rich", res)
        assert ok, f"public render: {json.dumps(info, ensure_ascii=False)[:800]}"
        r = info["render"]
        if paras:
            assert all(pp in r["paragraphs"] for pp in paras), f"paragraphs are not separate <p>: {r['paragraphs']}"
        link = ap.locator(public_sel).first.locator("a", has_text=link_text).first
        res["public_link_attrs"] = link.evaluate("a => ({href: a.href, target: a.target})")
        link.scroll_into_view_if_needed()
        try:
            with ap.expect_navigation(timeout=25000):
                link.click()
        except Exception as exc:  # noqa: BLE001 - recorded; judged by the URL below
            res["navigation_error"] = str(exc)[:160]
        res["navigated_to"] = ap.url
        dump("pfr", f"{tc}_rich", res)
        assert ap.url.rstrip("/").split("?")[0] == url.rstrip("/"), f"the link navigated to {ap.url}"
    finally:
        ctx.close()


# ===========================================================================
# 130949 PFR weak passes redone from the opposite state (99844)
# ===========================================================================
def _pfr_set_status(admin, eid, value):
    lb.open_live(admin, eid)
    admin.fill("page_status", value)
    admin.submit_for_review()
    assert lb.saved(admin, eid), f"saving Status={value} did not reach {eid} ({admin.save_counts()})"
    return lb.live_json(admin, eid)


def pfr_opposite(page, browser, tc):
    """Precondition built live: 99844 set to Status 'Draft' (not public) and proven non-public; then the
    case's own steps from that state."""
    from cms.pages.proposal_for_research.proposal_for_research_admin_page import ProposalPageAdminPage
    from cms.tests import live_b11_cases as lc
    from web.pages.proposal_for_research.proposal_for_research_page import ProposalForResearchPage as R

    eid = "99844"
    assert os.environ.get(A9_GATE) == eid
    admin = ProposalPageAdminPage(page)
    res = {"tc": tc}
    rec = _pfr_set_status(admin, eid, "Draft")
    res["precondition"] = {"pageStatus": rec.get("pageStatus"), "editorial": lb.status_of(admin, eid)}
    ctx, ap = anon(browser, viewport=(1920, 1080))
    try:
        ok, info = poll(ap, PFR_PATH, lambda pg: (len(texts_hero(pg)) == 0, {"h1": texts_hero(pg)}), settle=R.HERO_TITLE,
                        timeout=75)
        res["precondition"]["public"] = info
        shot(ap, "pfr", f"{tc}_0_precondition_draft")
        assert (rec.get("pageStatus") or {}).get("key") == "draft" and ok, f"precondition Draft not reached: {res}"
        log(f"tc_{tc} precondition: {res['precondition']}")

        lb.open_live(admin, eid)
        res["status_field_when_opened"] = admin.value("page_status")
        if tc == 141283:
            opts = admin.select_options("page_status")
            res["options"] = opts
            assert opts == ["Draft", "Published", "Unpublished"], f"Page Status offers {opts!r}"
            admin.fill("page_status", "Published")
        btn = admin.page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).first
        res["publish_enabled"] = btn.is_enabled()
        assert res["publish_enabled"], "the Publish control is not enabled"
        admin.submit_for_review()
        assert lb.saved(admin, eid), f"Publish did not reach {eid} ({admin.save_counts()})"
        after = lb.live_json(admin, eid)
        res["after_publish"] = {"pageStatus": after.get("pageStatus"), "editorial": lb.wait_status(admin, eid)}
        log(f"tc_{tc} after Publish: {res['after_publish']}")
        assert res["after_publish"]["editorial"] == STATUS_PUBLISHED, (
            f"the record is {res['after_publish']['editorial']!r} after Publish (Status field "
            f"{(after.get('pageStatus') or {}).get('name')!r}) - it did not change to Published")
        if tc == 141209:
            def probe(pg):
                s = lc._pfr_state(pg, 200)
                secs = [re.sub(r"^\d+\s*", "", t) for t in s["sections"]]
                return (s["facts"] == lc.PFR_FACTS and secs == lc.PFR_SECTIONS and s["cards"] == lc.PFR_CARDS
                        and s["groups"] == lc.PFR_GROUPS and s["bullets"] == [6, 4] and s["resources"] == lc.PFR_RESOURCES), s
        else:
            def probe(pg):
                s = lc._pfr_state(pg, 200)
                return (s["title"] == ["Proposal for Research"] and len(s["sections"]) == 3), s
        ok, info = poll(ap, PFR_PATH, probe, settle=R.FACT_LABEL)
        res["public"] = info
        shot(ap, "pfr", f"{tc}_1_public_after_publish")
        assert ok and info.get("http") == 200, f"public page after Publish: {json.dumps(info, ensure_ascii=False)[:600]}"
    finally:
        dump("pfr", f"{tc}_opposite_state", res)
        ctx.close()


def texts_hero(pg):
    from web.pages.proposal_for_research.proposal_for_research_page import ProposalForResearchPage as R

    return lb.texts(pg, R.HERO_TITLE)


# ===========================================================================
# 130717 Join - page-content cases on the live record 441112 (a9_cycle only for writes)
# ===========================================================================
JOIN_ID = "441112"
FORM_STATE_JS = r"""() => {
  const t = document.querySelector('input[name="ObjectField_pageTitle"]');
  const btns = [...document.querySelectorAll('button')].filter(b => b.offsetParent !== null)
      .map(b => [b.innerText.trim(), b.disabled || b.classList.contains('disabled'), b.getAttribute('title') || '']).filter(b => b[0]);
  const body = document.body.innerText;
  return {title_input: !!t, title_value: t ? t.value : null, title_editable: t ? !(t.readOnly || t.disabled) : false,
          readonly_marks: (body.match(/\(Read Only\)/g) || []).length,
          banner: (body.match(/Editing [^\n]{0,160}/) || [''])[0],
          denied: /permission|not allowed|access denied/i.test(body) ? (body.match(/[^\n]*(permission|not allowed|access denied)[^\n]*/i) || [''])[0] : '',
          buttons: btns.slice(0, 30)};
}"""


def join_admin(page):
    from cms.pages.join_committee.join_committee_admin_page import RequestToJoinCommitteePageAdminPage as JP

    return JP(page)


def join_open(adm, role) -> dict:
    """Open the live page's manage screen as `role` (the singleton manage page renders the live form)."""
    err = ""
    try:
        adm.open_list(role)
    except Exception as exc:  # noqa: BLE001 - a role without access may get no list at all
        err = str(exc)[:200]
    adm.page.wait_for_timeout(2500)
    st = adm.page.evaluate(FORM_STATE_JS)
    st["open_error"] = err
    try:
        st["session"] = adm.page.evaluate(
            "() => ({signedIn: Liferay.ThemeDisplay.isSignedIn(), user: Liferay.ThemeDisplay.getUserName()})")
    except Exception:  # noqa: BLE001
        st["session"] = {"signedIn": False}
    # a refusal only counts when the role is really signed in (run 2026-10-07: a failed Form Manager login
    # landed on the public page and looked like a refusal)
    assert st["session"].get("signedIn"), f"{role} is not signed in on the manage page (not a refusal): {st}"
    ident = adm._ident()
    ident["editing"] = (adm.PLURAL, JOIN_ID)
    ident["pending"] = None
    return st


def _btn(st, word):
    return [b for b in st["buttons"] if word.lower() in b[0].lower()]


def join_143428(page, browser):
    from cms.pages.join_committee.join_committee_admin_page import CommitteeLookupStatusAdminPage as Lookup

    adm = join_admin(page)
    st = join_open(adm, ROLE_EDITOR)
    shot(adm.page, "join", "143428_1_page_edit_editor")
    lk = Lookup(page)
    lk.open_list(ROLE_EDITOR)
    lk_state = {"add_new": lk.page.locator('button:has-text("+ Add New"), a:has-text("+ Add New")').count(),
                "rows": lk.page.locator("table tbody tr").count(),
                "edit_links": lk.page.locator("table tbody tr a:has-text('Edit')").count()}
    shot(lk.page, "join", "143428_2_lookup_editor")
    dump("join", "143428", {"page_form": st, "lookup": lk_state})
    log(f"tc_143428 page form {st} lookup {lk_state}")
    assert st["title_input"] and st["title_editable"] and JOIN_ID and "Request to Join a Committee" in st["banner"], \
        f"the page edit screen did not open editable: {st}"
    assert any(not b[1] for b in _btn(st, "Publish")), f"no enabled Publish on the page edit screen: {st['buttons']}"
    assert lk_state["add_new"] and lk_state["rows"] and lk_state["edit_links"], f"lookup list not manageable: {lk_state}"


def join_143431(page, browser):
    from cms.pages.join_committee.council_base import ROLE_FORM_MANAGER as FM

    adm = join_admin(page)
    st = join_open(adm, FM)
    shot(adm.page, "join", "143431_1_page_edit_form_manager")
    dump("join", "143431", st)
    log(f"tc_143431 Form Manager on the page edit screen: {st}")
    editable = st["title_input"] and st["title_editable"] and any(not b[1] for b in _btn(st, "Publish") + _btn(st, "Submit"))
    assert not editable, (f"the Form Manager is NOT blocked: the page-content edit screen opens editable with an enabled "
                          f"submit ({st['buttons']}); no Access Denied (banner {st['banner']!r})")


def join_143419(page, browser):
    adm = join_admin(page)
    st = join_open(adm, ROLE_EDITOR)
    fields = {}
    for key, spec in adm.FIELDS.items():
        try:
            present = adm.field_present(key)
        except Exception:  # noqa: BLE001
            present = False
        fields[spec.label] = present
    labels = adm.page.evaluate("() => [...document.querySelectorAll('label')].map(l => l.innerText.trim())")
    adm.open_list(ROLE_EDITOR)
    stl, txt = lb.req(adm, "GET", "/o/c/committeelookupstatuses/scopes/37246?pageSize=200")
    keys = sorted({i.get("listKey") for i in json.loads(txt).get("items", [])}) if stl == 200 else []
    shot(adm.page, "join", "143419_1_edit_screen")
    res = {"form": st, "fields_present": fields, "lookup_lists": keys}
    dump("join", "143419", res)
    log(f"tc_143419 {json.dumps(res, ensure_ascii=False)[:900]}")
    need = ["Page Title", "Page Description", "Hero Background Image", "Section Heading", "Section Body",
            "Form Title", "Form Disclaimer", "Consent Statement", "Privacy Policy Link"]
    missing = [n for n in need if not any(lbl.startswith(n) for lbl in labels)]
    assert not missing and st["title_editable"], f"edit screen fields missing / not editable: {missing} {st}"
    assert len(keys) == 4, f"the case expects 4 lookup-list management entries; the lookup object holds lists {keys}"


def join_143500(page, browser):
    adm = join_admin(page)
    before = None
    adm.open_list(ROLE_EDITOR)
    before = get_json(adm, adm.PLURAL, JOIN_ID)
    join_open(adm, ROLE_EDITOR)
    exe = exact_file(b"MZ" + b"\0" * 2046, f"QCTEST-143500-{RUN}.exe")
    rejected = adm.upload_file_expect_rejected(adm.spec("hero_image").label, exe)
    msg = adm.page.evaluate(r"""() => [...document.querySelectorAll('.form-feedback-item, .alert, [role=alert], .text-danger, .help-block')]
        .map(e => e.innerText.trim()).filter(Boolean).slice(0, 6)""")
    shot(adm.page, "join", "143500_1_exe_rejected")
    after = get_json(adm, adm.PLURAL, JOIN_ID)
    res = {"rejected": rejected, "messages": msg, "hero_before": (before or {}).get("heroImage"),
           "hero_after": (after or {}).get("heroImage"), "dateModified": [before.get("dateModified"), after.get("dateModified")]}
    dump("join", "143500", res)
    log(f"tc_143500 {res}")
    assert rejected, f"the .exe was not rejected by the Hero Background Image picker: {res}"
    assert res["hero_before"] == res["hero_after"] and before.get("dateModified") == after.get("dateModified"), \
        f"the hero background changed: {res}"


def _join_edit_values(tc):
    return {"page_title": (f"Request to Join a Committee QCTEST {tc}", f"طلب الانضمام إلى لجنة QCTEST {tc}"),
            "section_intro": (f"QCTEST {tc} info section body.", f"QCTEST {tc} نص قسم المعلومات."),
            "form_intro": (f"QCTEST {tc} disclaimer text.", f"QCTEST {tc} نص إخلاء المسؤولية.")}


def _join_preview(adm):
    adm.open_list(ROLE_EDITOR)
    row = adm.page.locator(f'tr:has([data-qc-oel-history="{JOIN_ID}"])').first
    link = row.get_by_role("link", name="Preview")
    href = link.first.get_attribute("href") if link.count() else ""
    if not href:
        return {"preview": "no Preview link on the row"}
    from config.settings import control_panel_url

    adm.page.goto(control_panel_url(href) if href.startswith("/") else href, wait_until="domcontentloaded")
    adm.page.wait_for_timeout(3000)
    return {"preview_url": adm.page.url, "text": " ".join(adm.page.locator("body").inner_text().split())[:3000]}


def join_draft_preview_publish(page, browser, tc):
    """143436 / 143495: edit -> Save as Draft -> Preview -> Publish -> public EN/AR (live 441112)."""
    assert os.environ.get(A9_GATE) == JOIN_ID
    adm = join_admin(page)
    vals = _join_edit_values(tc)
    res, problems = {"tc": tc}, []
    adm.open_list(ROLE_EDITOR)
    adm.allow_live_write(JOIN_ID)
    try:
        st = join_open(adm, ROLE_EDITOR)
        res["form_before"] = st
        for key, (en, ar) in vals.items():
            adm.fill(key, en)
            adm.fill(key, ar, locale="ar")
        draft_btn = adm.page.locator(adm.SAVE_AS_DRAFT_BUTTON).first
        res["save_as_draft"] = {"visible": draft_btn.is_visible(), "enabled": draft_btn.is_enabled() if draft_btn.count() else False,
                                "title": draft_btn.get_attribute("title") if draft_btn.count() else None}
        shot(adm.page, "join", f"{tc}_1_edited")
        if res["save_as_draft"]["visible"] and res["save_as_draft"]["enabled"]:
            adm.save_as_draft()
            res["draft_saved"] = saved(adm, JOIN_ID)
            res["state_after_draft"] = editorial(adm, JOIN_ID)
            if not res["draft_saved"] or res["state_after_draft"] != "Draft":
                problems.append(f"Save as Draft: saved={res['draft_saved']} state={res['state_after_draft']!r}")
            res["preview"] = _join_preview(adm)
            shot(adm.page, "join", f"{tc}_2_preview")
            if not all(v[0] in res["preview"].get("text", "") for v in vals.values()):
                problems.append(f"Preview does not show the draft content: {res['preview'].get('text', '')[:200]!r}")
            join_open(adm, ROLE_EDITOR)
        else:
            problems.append(f"Save as Draft is not available on the Published page ({res['save_as_draft']}); "
                            "Draft / Preview steps could not be performed")
        adm.submit_for_review()
        res["publish_saved"] = saved(adm, JOIN_ID)
        res["state_after_publish"] = wait_editorial(adm, JOIN_ID, STATUS_PUBLISHED)
        stored = get_json(adm, adm.PLURAL, JOIN_ID)
        res["stored"] = {k: stored.get(f"{adm.spec(k).ref or k}_i18n") for k in ("section_intro",)}
        adm.open_list(ROLE_EDITOR)
        res["history"] = history(adm, JOIN_ID, "Request to Join a Committee")[-3:]
        if not res["publish_saved"] or res["state_after_publish"] != STATUS_PUBLISHED:
            problems.append(f"Publish: saved={res['publish_saved']} state={res['state_after_publish']!r}")
        for loc, idx in (("en", 0), ("ar", 1)):
            ctx, ap = anon(browser, viewport=(1920, 1080))
            try:
                ok, info = poll(ap, JOIN_PATH, lambda pg, i=idx: (all(v[i] in pg.locator("body").inner_text() for v in vals.values()),
                                                                     {"h1": lb.texts(pg, "h1")}), locale=loc)
                shot(ap, "join", f"{tc}_3_public_{loc}")
                res[f"public_{loc}"] = {"ok": ok, **info}
                if not ok:
                    problems.append(f"public {loc.upper()} does not show the published values: {info}")
            finally:
                ctx.close()
    finally:
        adm.revoke_live_write()
        dump("join", f"{tc}_draft_preview_publish", res)
        log(f"tc_{tc} {json.dumps(res, ensure_ascii=False, default=str)[:1200]}")
    assert not problems, " | ".join(problems)


def join_143496(page, browser):
    assert os.environ.get(A9_GATE) == JOIN_ID
    adm = join_admin(page)
    adm.open_list(ROLE_EDITOR)
    adm.filter_entries("Request to Join a Committee")
    ctl = adm.page.locator(f'[data-qc-oel-unpublish="{JOIN_ID}"]')
    assert ctl.count(), "the Editor is offered no Unpublish on the Published page"
    adm.page.on("dialog", lambda d: d.accept("QCTEST 143496 unpublish") if d.type == "prompt" else d.accept())
    ctl.first.click(force=True)
    adm.page.wait_for_timeout(3000)
    st = wait_editorial(adm, JOIN_ID, "Unpublished")
    adm.open_list(ROLE_EDITOR)
    hist = history(adm, JOIN_ID, "Request to Join a Committee")[-2:]
    shot(adm.page, "join", "143496_1_unpublished")
    # manual-style check (coordinator 2026-10-07): a FRESH no-cache logged-out context per poll, for 3 minutes
    trace, ok, info = [], False, {}
    t0 = time.monotonic()
    while time.monotonic() - t0 < 180:
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080},
                                  extra_http_headers={"Cache-Control": "no-cache, no-store", "Pragma": "no-cache"})
        ap = ctx.new_page()
        try:
            url = web_url(JOIN_PATH) + f"?nocache={int(time.time() * 1000)}"
            r = ap.goto(url, wait_until="domcontentloaded", timeout=60000)
            ap.wait_for_timeout(2000)
            h1 = lb.texts(ap, "h1")
            info = {"http": r.status if r else None, "h1": h1, "title": ap.title(), "t": round(time.monotonic() - t0, 1)}
            trace.append(info)
            ok = "Request to Join a Committee" not in " ".join(h1)
            if ok:
                shot(ap, "join", "143496_2_public_after_unpublish")
                break
            shot(ap, "join", "143496_2_public_after_unpublish")
        finally:
            ctx.close()
        time.sleep(10)
    info = dict(info, trace=trace)
    res = {"state": st, "history": hist, "public": info}
    dump("join", "143496", res)
    log(f"tc_143496 {res}")
    assert st == "Unpublished", f"state after Unpublish: {st!r}"
    assert ok and (info.get("http") or 0) in (200, 404, 403) , f"the page is still public after Unpublish: {info}"


def join_143437(page, browser):
    """Contributor attempts to Publish the live page: expected blocked, page state unchanged."""
    assert os.environ.get(A9_GATE) == JOIN_ID
    adm = join_admin(page)
    adm.open_list(ROLE_EDITOR)
    before = get_json(adm, adm.PLURAL, JOIN_ID)
    st_before = editorial(adm, JOIN_ID)
    st = join_open(adm, "Content Contributor")
    shot(adm.page, "join", "143437_1_contributor_form")
    res = {"form": st, "state_before": st_before}
    submit = adm.page.locator(adm.SUBMIT_FOR_REVIEW_BUTTON).first
    res["submit_present"] = bool(submit.count() and submit.is_visible())
    if res["submit_present"] and submit.is_enabled():
        adm.allow_live_write(JOIN_ID)
        try:
            adm.submit_for_review()
        finally:
            adm.revoke_live_write()
        res["save"] = {k: (adm.last_save or {}).get(k) for k in ("started", "id", "hidden_refusal", "edit_info")}
        res["writes"] = [(w["method"], w["status"]) for w in (adm.last_save or {}).get("writes", [])]
        shot(adm.page, "join", "143437_2_after_attempt")
    adm.open_list(ROLE_EDITOR)
    after = get_json(adm, adm.PLURAL, JOIN_ID)
    res["state_after"] = editorial(adm, JOIN_ID)
    res["dateModified"] = [before.get("dateModified"), after.get("dateModified")]
    dump("join", "143437", res)
    log(f"tc_143437 {json.dumps(res, ensure_ascii=False, default=str)[:1000]}")
    assert res["state_after"] == st_before and before.get("dateModified") == after.get("dateModified"), (
        f"the Contributor's Publish attempt was NOT blocked: state {st_before!r} -> {res['state_after']!r}, "
        f"dateModified {res['dateModified']}, writes {res.get('writes')}")


def join_143499(page, browser):
    """Valid JPG hero background -> Save -> Preview shows it. The image is then cleared again THROUGH THE
    FORM (Clear + Publish): file fields are never restored by PATCH."""
    assert os.environ.get(A9_GATE) == JOIN_ID
    adm = join_admin(page)
    adm.open_list(ROLE_EDITOR)
    before = get_json(adm, adm.PLURAL, JOIN_ID)
    assert not before.get("heroImage"), f"precondition: the live page already has a hero image {before.get('heroImage')}"
    from cms.tests.sectoral_committees import cc_checks as cc

    jpg = exact_file(Path(cc.runtime_fixture("hero_1mb.jpg", "jpg", 1024 * 1024)), f"QCTEST-143499-hero-{RUN}.jpg")
    res, problems = {}, []
    adm.allow_live_write(JOIN_ID)
    try:
        join_open(adm, ROLE_EDITOR)
        adm.upload_file(adm.spec("hero_image").label, jpg)
        res["readout"] = adm.uploaded_filename(adm.spec("hero_image").label)
        shot(adm.page, "join", "143499_1_uploaded")
        adm.submit_for_review()
        res["saved"] = saved(adm, JOIN_ID)
        after = get_json(adm, adm.PLURAL, JOIN_ID)
        res["stored"] = after.get("heroImage")
        leftover(f"D&M upload kept (never deleted): {Path(jpg).name} via {adm.PLURAL}/{JOIN_ID} -> {res['stored']}")
        res["preview"] = _join_preview(adm)
        shot(adm.page, "join", "143499_2_preview")
        res["preview_bg"] = adm.page.evaluate(r"""() => [...document.querySelectorAll('[style*="background"], img')]
             .map(e => (e.getAttribute('style') || e.getAttribute('src') || '')).filter(s => /QCTEST-143499|heroImage|documents/.test(s)).slice(0,5)""")
        if not res["saved"] or not res["stored"]:
            problems.append(f"the image was not saved: {res}")
        elif not res["preview_bg"]:
            problems.append("Preview does not show the uploaded hero background")
    finally:
        # restore through the form: Clear the file, Publish
        try:
            join_open(adm, ROLE_EDITOR)
            grp = adm.page.locator(".form-group", has_text="Hero Background Image").first
            grp.get_by_role("button", name="Clear").first.click()
            adm.page.wait_for_timeout(800)
            adm.submit_for_review()
            res["form_clear_saved"] = saved(adm, JOIN_ID)
            res["after_clear"] = (get_json(adm, adm.PLURAL, JOIN_ID) or {}).get("heroImage")
        except Exception as exc:  # noqa: BLE001 - the cycle's restore verifies and stops if this left a diff
            res["form_clear_error"] = str(exc)[:200]
        adm.revoke_live_write()
        dump("join", "143499", res)
        log(f"tc_143499 {json.dumps(res, ensure_ascii=False, default=str)[:1200]}")
    assert not problems, " | ".join(problems)


# ===========================================================================
# D&M deletion cases (USER DECISION 2026-10-07): only a QCTEST file WE uploaded in the same test may be deleted
# ===========================================================================
def _dm_doc(admin, doc_id):
    st, txt = lb.req(admin, "GET", f"/o/headless-delivery/v1.0/documents/{doc_id}")
    try:
        return st, (json.loads(txt) if st == 200 else {"raw": txt[:200]})
    except ValueError:
        return st, {"raw": txt[:200]}


def _dm_delete_ours(admin, doc_id, uploaded_name, res):
    """Delete ONE Documents & Media file by id, only when its stored title / file name is the QCTEST file this
    test uploaded."""
    st, doc = _dm_doc(admin, doc_id)
    name = (doc.get("title") or doc.get("fileName") or "") if isinstance(doc, dict) else ""
    res["dm_doc"] = {"id": doc_id, "http": st, "title": doc.get("title"), "fileName": doc.get("fileName")}
    assert st == 200 and name.startswith("QCTEST-") and Path(uploaded_name).stem in json.dumps(doc), (
        f"refusing to delete D&M file {doc_id}: it is not our QCTEST upload ({res['dm_doc']})")
    d_st, d_txt = lb.req(admin, "DELETE", f"/o/headless-delivery/v1.0/documents/{doc_id}")
    res["dm_delete"] = {"http": d_st, "resp": d_txt[:200]}
    res["dm_get_after"] = _dm_doc(admin, doc_id)[0]
    log(f"D&M delete of our QCTEST file {doc_id} ({name}): HTTP {d_st} -> GET after {res['dm_get_after']}")
    return d_st


def pfr_141344(page, browser):
    from cms.pages.proposal_for_research.proposal_for_research_admin_page import ResourceItemAdminPage

    adm = ResourceItemAdminPage(page)
    title = f"QCTEST-141344-{RUN} Research Proposal Template"
    pdf_b = make_pdf(200 * 1024)
    pdf = exact_file(pdf_b, f"QCTEST-130949-template-141344-{RUN}.pdf")
    eid, res = None, {}
    ctx, p = anon(browser, viewport=(1920, 1080), accept_downloads=True)
    try:
        adm.open_form(ROLE_EDITOR)
        adm.fill_required(title, active=True, skip=("file_type", "file_size"))
        _fill_if_editable(adm, "file_type", "PDF")
        _fill_if_editable(adm, "file_size", "200 KB")
        adm.fill("display_order", "9995")
        adm.upload_file(adm.spec("resource_file").label, pdf)
        adm.submit_for_review()
        eid = adm.id_for(title)
        assert eid and wait_editorial(adm, eid, STATUS_PUBLISHED) == STATUS_PUBLISHED
        data = get_json(adm, DRI, eid)
        doc_id = str((data.get("resourceFile") or {}).get("id"))
        ok, info = poll(p, PFR_PATH, _card_probe(title, lambda c: bool(c["href"])), settle="article.qc-pfr-file")
        href = info["card"]["href"]
        r1 = ctx.request.get(_abs(href))
        res["step1"] = {"http": r1.status, "bytes": len(r1.body()) if r1.status == 200 else 0, "href": href}
        assert r1.status == 200 and res["step1"]["bytes"] == len(pdf_b), f"step 1 download: {res['step1']}"
        # Step 2: delete OUR QCTEST file from Documents & Media, confirmed by name
        d_st = _dm_delete_ours(adm, doc_id, pdf, res)
        assert d_st in (200, 204), f"the D&M delete was refused: {res['dm_delete']}"
        # Step 3: fresh logged-out visitor
        ctx2, p2 = anon(browser, viewport=(1920, 1080), accept_downloads=True)
        try:
            http = visit(p2, PFR_PATH, settle="article.qc-pfr-file")
            card = p2.evaluate(CARD_JS, title)
            shot(p2, "pfr", "141344_after_dm_delete")
            res["step3"] = {"page_http": http, "card": card, "h1": lb.texts(p2, "h1")}
            if card and card.get("href"):
                r2 = ctx2.request.get(_abs(card["href"]))
                res["step3"]["download_http"] = r2.status
                res["step3"]["download_bytes"] = len(r2.body()) if r2.status == 200 else 0
        finally:
            ctx2.close()
        s3 = res["step3"]
        log(f"tc_141344 {json.dumps(res, ensure_ascii=False)[:900]}")
        assert s3["page_http"] == 200 and s3["h1"], f"the page itself broke after the file deletion: {s3}"
        handled = (not s3["card"] or not s3["card"].get("href")) or s3.get("download_http") in (404, 410)
        assert handled, f"the visitor is left with a silent / unhandled failure: {s3}"
    finally:
        dump("pfr", "141344_dm_delete", res)
        ctx.close()
        if eid:
            delete_by_id(adm, DRI, eid, title, lambda d: str(d.get("resourceTitle", "")).startswith("QCTEST-"))


def coo_141145(page, browser):
    from cms.pages.certificate_of_origin.certificate_of_origin_admin_page import CooDownloadCardAdminPage

    adm = CooDownloadCardAdminPage(page)
    title = f"QCTEST-141145-{RUN} Download the Application Form"
    pdf_b = make_pdf(150 * 1024)
    pdf = exact_file(pdf_b, f"QCTEST-130947-application-form-141145-{RUN}.pdf")
    eid, res = None, {}
    ctx, p = anon(browser, viewport=(1920, 1080), accept_downloads=True)
    card_js = r"""(t) => { const h = [...document.querySelectorAll('h2,h3,h4,p,span,strong')].find(e => e.innerText && e.innerText.trim() === t);
        if (!h) return null;
        let c = h.parentElement;   // climb to the smallest element holding a link AND only this one card title
        while (c && !c.querySelector('a')) c = c.parentElement;
        if (c && c.querySelectorAll('.qc-coo-download-text').length > 1) c = null;
        if (!c) return {title: t, card_class: null, label: null, href: null};
        const a = c.querySelector('a');
        return {title: t, card_class: (c.className || '').toString().slice(0, 80), label: a ? a.innerText.trim() : null,
                href: a ? a.getAttribute('href') : null}; }"""
    try:
        adm.open_form(ROLE_EDITOR)
        adm.fill_required(title, active=True)
        adm.fill("download_label", "Download")
        adm.fill("download_label", "تنزيل", locale="ar")
        adm.upload_file(adm.spec("application_form_file").label, pdf)
        adm.submit_for_review()
        eid = adm.id_for(title)
        assert eid and wait_editorial(adm, eid, STATUS_PUBLISHED) == STATUS_PUBLISHED, f"publish failed ({adm.save_counts()})"
        data = get_json(adm, "coodownloadcards", eid)
        doc_id = str((data.get("applicationFormFile") or {}).get("id"))

        def fn(pg):
            c = pg.evaluate(card_js, title)
            return bool(c and c.get("href")), {"card": c}

        ok, info = poll(p, COO_PATH, fn)
        assert ok, f"the QCTEST download card is not rendered: {info}"
        r1 = ctx.request.get(_abs(info["card"]["href"]))
        res["step1"] = {"http": r1.status, "bytes": len(r1.body()) if r1.status == 200 else 0, "card": info["card"]}
        assert r1.status == 200, f"step 1: {res['step1']}"
        d_st = _dm_delete_ours(adm, doc_id, pdf, res)
        res["step2_outcome"] = "deleted" if d_st in (200, 204) else f"blocked (HTTP {d_st})"
        ctx2, p2 = anon(browser, viewport=(1920, 1080), accept_downloads=True)
        try:
            http = visit(p2, COO_PATH)
            card = p2.evaluate(card_js, title)
            shot(p2, "coo", "141145_after_dm_delete")
            res["step3"] = {"page_http": http, "card": card}
            if card and card.get("href"):
                r2 = ctx2.request.get(_abs(card["href"]))
                res["step4"] = {"download_http": r2.status, "bytes": len(r2.body()) if r2.status == 200 else 0}
        finally:
            ctx2.close()
        log(f"tc_141145 {json.dumps(res, ensure_ascii=False)[:900]}")
        assert res["step3"]["page_http"] == 200 and res["step3"]["card"], f"step 3: {res['step3']}"
        s4 = res.get("step4") or {}
        # the case's step 4 itself predicts the broken download and says it "must be raised as a content-integrity
        # defect, since no CMS validation prevents" deleting a referenced file
        assert not (d_st in (200, 204) and s4.get("download_http") in (404, 410) or s4.get("bytes") == 0), (
            f"content-integrity defect (as the case states): the referenced file could be deleted from D&M "
            f"(HTTP {d_st}) and the published card now offers a broken download {s4}")
    finally:
        dump("coo", "141145_dm_delete", res)
        ctx.close()
        if eid:
            delete_by_id(adm, "coodownloadcards", eid, title, lambda d: str(d.get("cardTitle", "")).startswith("QCTEST-"))

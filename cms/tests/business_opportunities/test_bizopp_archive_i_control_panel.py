"""
cms/tests/business_opportunities/test_bizopp_archive_i_control_panel.py — Agent I,
PBI 130697, case 143389 (auto-archive on the Archive Date).

Live finding: Publish/Archive Date are DATE-only (`input[type=date]` + a calendar
with Today / Clear, no time part), so "archive 5 minutes later" cannot be set.
Two disposable records run together:
  (a) Publish = yesterday, Archive = today   (a normal, valid date pair)
  (b) Publish = today,     Archive = today   (accepted - known bug, equal dates)
`test_create` publishes them and persists their identity to STATE_FILE;
`test_monitor` watches them from a fresh logged-out context + the CMS list.
Records are NEVER deleted here unless they were observed Archived (then the
guarded single-record delete runs); otherwise they stay for the overnight check.
"""

from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timedelta

import allure
import pytest

from cms.pages.business_opportunities.opportunity_admin_page import (
    K_ARCHIVE_DATE,
    K_PUBLISH_DATE,
    ROLE_EDITOR,
    BizOppEntry,
    BizOppPublicView,
    OpportunityAdminPage,
)
from cms.tests.business_opportunities.a_support import AUTH_FREE_PAGE, create, login
from config.settings import PROJECT_ROOT

I_PREFIX = os.environ.get("BIZOPP_I_PREFIX", "QCTEST-130697-I-")  # retests: QCTEST-R30-<x>-
EVIDENCE_DIR = str(PROJECT_ROOT / "reports" / "evidence" / "130697_I")
STATE_FILE = os.environ.get("BIZOPP_I_STATE", str(PROJECT_ROOT / "reports" / "evidence" / "130697_I" / "state.json"))
MONITOR_MINUTES = float(os.environ.get("BIZOPP_I_MONITOR_MIN", "16"))
MONITOR_EVERY_S = float(os.environ.get("BIZOPP_I_EVERY_S", "150"))

_MARKERS = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130697,
            pytest.mark.tc_143389, pytest.mark.functional_low]


def _markers(fn):
    for m in reversed(_MARKERS):
        fn = m(fn)
    return fn


class _Keep:
    """Registry stand-in: the records are kept (see module docstring)."""

    def __init__(self):
        self.entries: list[BizOppEntry] = []

    def track(self, entry):
        self.entries.append(entry)
        return entry


def _d(delta: int) -> str:
    return (date.today() + timedelta(days=delta)).strftime("%d/%m/%Y")


def _iso(delta: int) -> str:
    return (date.today() + timedelta(days=delta)).isoformat()


@_markers
@AUTH_FREE_PAGE
def test_create(page):
    """Create (a) and (b), Active + Published, verify stored values by reopening."""
    stamp = datetime.now().strftime("%m%d%H%M%S")
    login(page, ROLE_EDITOR)
    admin = OpportunityAdminPage(page, I_PREFIX, EVIDENCE_DIR)  # I namespace (login() builds an A-prefixed page)
    keep, state = _Keep(), {"created_at": datetime.now().isoformat(timespec="seconds"), "records": {}}
    plan = {"a": (-1, 0), "b": (0, 0)}
    for tag, (pub, arc) in plan.items():
        title = f"{I_PREFIX}143389-{tag}-{stamp}"
        data = OpportunityAdminPage.default_data(title, publishDate=_d(pub), archiveDate=_d(arc))
        rec = {"title": title, "publish_date": _iso(pub), "archive_date": _iso(arc)}
        state["records"][tag] = rec
        try:
            entry = create(admin, keep, title, lambda a, d=data: a.fill_opportunity(d), publish=True)
        except AssertionError as exc:
            rec["create_error"] = str(exc)[:600]
            allure.attach(rec["create_error"], name=f"({tag}) creation refused")
            continue
        rec.update(entry_id=entry.entry_id, code=entry.code, prefix=entry.prefix)
        admin.open_entry_en(entry.code)
        rec["stored"] = {"publish_text": admin.date_text(K_PUBLISH_DATE), "publish_stored": admin.date_stored(K_PUBLISH_DATE),
                         "archive_text": admin.date_text(K_ARCHIVE_DATE), "archive_stored": admin.date_stored(K_ARCHIVE_DATE),
                         "active_status": admin.active_status_stored(), "title": admin.identity_value()}
        admin.evidence(f"{tag} reopened stored values")
        admin.open_list_all()
        rec["list_status"] = _list_column(admin, entry.entry_id, "STATUS")
    json.dump(state, open(STATE_FILE, "w", encoding="utf8"), indent=1, ensure_ascii=False)
    allure.attach(json.dumps(state, indent=1, ensure_ascii=False), name="state")
    print("STATE", json.dumps(state, indent=1))
    assert any("code" in r for r in state["records"].values()), "no record could be created"


@_markers
@AUTH_FREE_PAGE
def test_verify_stored(page):
    """Reopen each recorded record and capture the stored dates / Active Status / list status."""
    state = json.load(open(STATE_FILE, encoding="utf8"))
    login(page, ROLE_EDITOR)
    admin = OpportunityAdminPage(page, I_PREFIX, EVIDENCE_DIR)
    for tag, rec in state["records"].items():
        if "code" not in rec:   # refused at creation (e.g. (b) equal dates, bug 149513 fix)
            continue
        admin.open_entry_en(rec["code"])
        rec["stored"] = {"publish_text": admin.date_text(K_PUBLISH_DATE), "publish_stored": admin.date_stored(K_PUBLISH_DATE),
                         "archive_text": admin.date_text(K_ARCHIVE_DATE), "archive_stored": admin.date_stored(K_ARCHIVE_DATE),
                         "active_status": admin.active_status_stored(), "title": admin.identity_value(),
                         "lifecycle": admin.picklist_value("lifecycleStatus")}
        admin.evidence(f"{tag} reopened stored values")
        admin.open_list_all()
        entry = BizOppEntry(slug="business-opportunity", prefix=I_PREFIX, title=rec["title"], entry_id=rec["entry_id"], code=rec["code"])
        rec["list_status"] = _list_column(admin, entry.entry_id, "STATUS")
        print("STORED", tag, json.dumps(rec))
    json.dump(state, open(STATE_FILE, "w", encoding="utf8"), indent=1, ensure_ascii=False)


def _observe(browser_ctx_factory, admin, rec, tag) -> dict:
    """One timestamped observation of one record."""
    from cms.pages.business_opportunities.opportunity_admin_page import BizOppEntry as E
    entry = E(slug="business-opportunity", prefix=rec["prefix"], title=rec["title"], entry_id=rec["entry_id"], code=rec["code"])
    obs = {"t": datetime.now().strftime("%H:%M:%S"), "rec": tag}
    for tab in ("active", "archive"):
        view = BizOppPublicView(browser_ctx_factory()).open_listing("en", tab)
        card = view.card_for(rec["code"])
        titles = [c["title"] for c in view.cards()]
        obs[tab] = {"on_tab": bool(card) or rec["title"] in titles, "tabs": view.tabs()}
    det = BizOppPublicView(browser_ctx_factory()).open_detail(rec["code"])
    body = det.detail()
    obs["detail"] = {"h1": body["h1"], "has_title": rec["title"] in body["body"],
                     "submit_inquiry_cta": "submit inquiry" in body["body"].lower(),
                     "archived_word": any(w in body["body"].lower() for w in ("archived", "closed", "expired"))}
    admin.open_list_all()
    obs["cms_status"] = _list_column(admin, rec["entry_id"], "STATUS")
    # bug 149530 fix (2026-10-13): the list has a LIFECYCLE column (Published / Archived)
    # that turns Archived on the Archive Date; the STATUS badge is the workflow status.
    obs["cms_lifecycle"] = _list_lifecycle(admin, rec["entry_id"])
    return obs


_COLUMN_JS = """([id, col]) => {
    const heads = [...document.querySelectorAll('table thead th')].map(t => t.innerText.trim().toUpperCase());
    const li = heads.indexOf(col);
    for (const r of document.querySelectorAll('table tbody tr')) {
        const ids = [...r.querySelectorAll('*')].flatMap(n => [...n.attributes]
            .filter(a => a.name.startsWith('data-qc-oel-') && a.name !== 'data-qc-oel-label').map(a => a.value));
        if (!ids.includes(id)) continue;
        const tds = [...r.querySelectorAll('td')];
        return li >= 0 && tds[li] ? tds[li].innerText.trim() : '';
    }
    return '';
}"""


def _list_column(admin, entry_id: str, col: str) -> str:
    """Header-based cell read (the list gained LIFECYCLE / ARCHIVE DATE / DISPLAY ORDER columns)."""
    return admin.page.evaluate(_COLUMN_JS, [entry_id, col])


def _list_lifecycle(admin, entry_id: str) -> str:
    return _list_column(admin, entry_id, "LIFECYCLE")


@_markers
@AUTH_FREE_PAGE
def test_monitor(page, browser):
    from core.web.browser import new_context
    state = json.load(open(STATE_FILE, encoding="utf8"))
    login(page, ROLE_EDITOR)
    admin = OpportunityAdminPage(page, I_PREFIX, EVIDENCE_DIR)
    ctxs = []

    def anon():
        ctx = new_context(browser, use_auth_state=False)
        ctxs.append(ctx)
        return ctx.new_page()

    log = []
    end = time.monotonic() + MONITOR_MINUTES * 60
    try:
        while True:
            for tag, rec in state["records"].items():
                if "code" not in rec:
                    continue
                obs = _observe(anon, admin, rec, tag)
                log.append(obs)
                print("OBS", json.dumps(obs))
                for c in ctxs:
                    c.close()
                ctxs.clear()
            json.dump(log, open(STATE_FILE.replace("state.json", "monitor.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)
            if time.monotonic() > end or _archived_seen(log, state):
                break
            time.sleep(MONITOR_EVERY_S)
    finally:
        for c in ctxs:
            c.close()
    # Record (a): Publish = yesterday, Archive = today -> Lifecycle Archived (job every 5 min),
    # on the public Archive tab, off the Active tab, detail page still opens.
    last = [o for o in log if o["rec"] == "a"]
    assert last, "record (a) was not created / observed"
    final = last[-1]
    allure.attach(json.dumps(final, indent=1, ensure_ascii=False), name="final observation (a)")
    assert final.get("cms_lifecycle") == "Archived", (
        f"PRODUCT: CMS list Lifecycle for (a) is {final.get('cms_lifecycle')!r} (status {final['cms_status']!r}) "
        f"after {MONITOR_MINUTES} min, expected 'Archived'")
    assert final["archive"]["on_tab"] and not final["active"]["on_tab"], f"public tabs: {final}"
    assert final["detail"]["has_title"], f"archived detail page does not open: h1={final['detail']['h1']!r}"


def _archived_seen(log, state) -> bool:
    last = [o for o in log if o["rec"] == "a"]
    return bool(last) and last[-1].get("cms_lifecycle") == "Archived" and last[-1]["archive"]["on_tab"]

"""
cms/tests/live_b11.py - check bodies for the CONDITIONAL cases of PBIs 130947
(Certificate of Origin), 130949 (Proposal for Research) and 130720 (Partners
& Offers) that act on the LIVE records themselves (Engineer B11, 2026-10-04).
Not a test module.

User approval (2026-10-04, explicit and ID-named): "write and try" on
    93657 COO Page Content, 93663 / 93667 COO CTAs (loginCoo / verifyCertificate),
    93860 COO Documents Required accordion item,
    99844 Proposal for Research Page, 99886 first PFR Overview,
    167087 Partners Offers Page.
No other live id is ever written. Each test runs alone (-n 0) under
reports/live-restore/b11_cycle.py: full JSON snapshot + logged-out EN/AR
public capture BEFORE, the single test, then b11_live_restore.py restores the
record (PATCH by id + workflow row action) and verifies the read-back diff and
the public after-capture. These helpers never restore and never DELETE.

Why live and not QCTEST: the public pages read the oldest entry
(`?pageSize=1`) and the CTAs bind by key, so a QCTEST entry never reaches the
page (B10, 2026-10-04). The test case is the oracle: values the case names are
used verbatim. Canonical public paths come from the web page objects (the
cases' `/en/e-services/...` and `/our-services/information/...` are stale
aliases). Missing toasts / different wording are not asserted.

Account: QC Site Content Editor via cms_role_credentials('Site Content Editor')
(through open_list(ROLE_EDITOR)); public reads use a fresh logged-out context
(new_context(browser, use_auth_state=False)).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from config.settings import web_url

GATE_ENV = "QC_B11_LIVE_RUN"
LIVE = {
    "93657": "coopagecontents",
    "93663": "cooctas",
    "93667": "cooctas",
    "93860": "coodocumentrequirements",
    "99844": "proposalforresearchpages",
    "99886": "overviewsectionandinfocards",
    "167087": "partnersofferspages",
}
COO_PATH = "/our-services/certificate-of-origin-online"
PFR_PATH = "/our-services/proposal-for-research"
PO_PATH = "/web/qatar-chamber/partners-offers"


def gate(eid: str):
    return pytest.mark.skipif(
        os.environ.get(GATE_ENV) != eid,
        reason=(f"LIVE record {eid} (user-approved 2026-10-04, B11): runs only under "
                f"reports/live-restore/b11_cycle.py snapshot -> run -> restore, with {GATE_ENV}={eid}"),
    )


def squash(s) -> str:
    return " ".join(str(s or "").split())


# ---------------------------------------------------------------------------
# Control Panel side
# ---------------------------------------------------------------------------
def req(admin, method, path, body=None) -> tuple[int, str]:
    """qcdev 2026-10-04 ~18:05Z: an in-page fetch carrying content-type answers
    404 "Coming Soon", so reads go through the context's APIRequestContext
    (same cookies) with the CSRF token."""
    from config.settings import control_panel_url

    try:
        token = admin.page.evaluate("() => (window.Liferay && Liferay.authToken) || ''")
    except Exception:  # noqa: BLE001 - page navigating
        token = ""
    headers = {"accept": "application/json", "x-csrf-token": token}
    if body is not None:
        headers["content-type"] = "application/json"
    r = admin.page.context.request.fetch(control_panel_url(path), method=method, headers=headers,
                                         data=body.encode("utf-8") if body is not None else None)
    return r.status, r.text()


def live_json(admin, eid) -> dict:
    eid = str(eid)
    status, text = req(admin, "GET", f"/o/c/{LIVE[eid]}/{eid}")
    assert status == 200, f"GET live {eid}: HTTP {status} {text[:160]}"
    return json.loads(text)


_WF = {"approved": "Published", "draft": "Draft", "incomplete": "Draft", "pending": "Pending Review",
       "denied": "Rejected", "scheduled": "Scheduled", "expired": "Unpublished"}


def status_of(admin, eid) -> str:
    """Editorial state by id: the transitions endpoint's label, else the
    record's own Liferay workflow status."""
    st, txt = req(admin, "GET", f"/o/qc-object-status/transitions/{eid}")
    try:
        d = json.loads(txt) if st == 200 else {}
    except ValueError:
        d = {}
    label = d.get("statusLabelEn") or ""
    if label and (d.get("statusKey") or "").casefold() != "inactive":
        return label
    wf = (live_json(admin, eid).get("status") or {}).get("label", "")
    return _WF.get(wf.casefold(), f"Inactive/{wf}")


def _camel(key: str) -> str:
    parts = key.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def open_live(admin, eid) -> dict:
    """Sign in as the Site Content Editor and open the live record's edit form
    by its own ERC. The record is never registered in the identity table
    (teardown deletes resolve from it)."""
    eid = str(eid)
    assert eid in LIVE, f"{eid} is not an approved live id"
    assert os.environ.get(GATE_ENV) == eid, f"live write on {eid} outside its b11_cycle run"
    admin.open_list(ROLE_EDITOR)
    data = live_json(admin, eid)
    admin.open(admin._manage_url(edit_entry=data["externalReferenceCode"], locale="en"))
    admin.page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).first.wait_for(state="visible", timeout=40000)
    want = (data.get(_camel(admin.TITLE_FIELD) + "_i18n") or {}).get("en_US", "")
    box = admin.page.get_by_role("textbox", name=admin.label_pattern(admin.FIELDS[admin.TITLE_FIELD].label)).first
    for _ in range(40):  # condition: the form is hydrated with the record's own title
        if box.count() and box.input_value() == want:
            break
        admin.page.wait_for_timeout(500)
    assert box.input_value() == want, (
        f"the edit form does not hold live record {eid} (title {box.input_value()[:60]!r} != {want[:60]!r})")
    ident = admin._ident()
    ident["editing"] = (LIVE[eid], eid)
    ident["pending"] = None
    print(f"[live {eid}] form opened as {ROLE_EDITOR}; status={data.get('status', {}).get('label')!r} "
          f"dateModified={data.get('dateModified')}")
    return data


def saved(admin, eid) -> bool:
    ls = admin.last_save or {}
    return bool(ls.get("started")) and str(ls.get("id") or "") == str(eid)


def wait_status(admin, eid, want=STATUS_PUBLISHED, timeout=40.0) -> str:
    deadline = time.monotonic() + timeout
    while True:
        st = status_of(admin, str(eid))
        if st == want or time.monotonic() > deadline:
            return st
        admin.page.wait_for_timeout(2000)


def publish(admin, eid, expect_published=True):
    """The case's Publish (the form's submit). The write must reach the live
    record by id; with `expect_published` it must read Published by id."""
    admin.submit_for_review()
    assert saved(admin, eid), f"Publish did not save live record {eid} ({admin.save_counts()})"
    if expect_published:
        st = wait_status(admin, eid)
        assert st == STATUS_PUBLISHED, f"live record {eid} is {st!r} after the Editor's Publish"


def save_draft(admin, eid):
    btn = admin.page.locator(admin.SAVE_AS_DRAFT_BUTTON).first
    assert btn.count() and btn.is_visible() and btn.is_enabled(), "no enabled 'Save as Draft' on the live record"
    admin.save_as_draft()
    assert saved(admin, eid), f"Save as Draft stored nothing on {eid} ({admin.save_counts()})"


def assert_publish_blocked(admin, eid, before: dict, json_key: str, what: str):
    """Publish is blocked: nothing reaches the record (dateModified and the
    field are unchanged). The field flag is reported, not asserted (wording /
    toast are not bugs)."""
    admin.submit_for_review()
    ls = admin.last_save or {}
    after = live_json(admin, eid)
    print(f"[live {eid}] refusal signals: invalid_fields={ls.get('invalid_fields')} "
          f"hidden_refusal={ls.get('hidden_refusal')!r} {admin.save_counts()}")
    assert after.get("dateModified") == before.get("dateModified") and after.get(json_key) == before.get(json_key), (
        f"Publish was NOT blocked with {what}: the record was written "
        f"(dateModified {before.get('dateModified')} -> {after.get('dateModified')}, "
        f"{json_key} {str(before.get(json_key))[:80]!r} -> {str(after.get(json_key))[:80]!r})")


def clear_rich(admin, key, locale="en"):
    """Empty a rich-text field: select all + delete inside the field's own editor."""
    sel = admin._rich_iframe(key, locale)
    body = admin.page.frame_locator(sel).locator("body")
    body.wait_for(state="visible", timeout=30000)
    body.click()
    admin.page.keyboard.press("Control+A")
    admin.page.keyboard.press("Delete")
    admin.page.wait_for_timeout(500)
    left = squash(body.inner_text())
    assert not left, f"{key}/{locale} still holds {left[:80]!r} after clearing"


def row_action(admin, eid, action) -> list:
    """Click the live row's data-qc-oel-<action>="<id>" control (accepting the
    native dialogs, a prompt gets a QCTEST comment)."""
    admin.open_list(ROLE_EDITOR)
    ctl = admin.page.locator(f'[data-qc-oel-{action}="{eid}"]')
    try:
        ctl.first.wait_for(state="attached", timeout=20000)
    except Exception:  # noqa: BLE001
        raise AssertionError(f"{ROLE_EDITOR} is offered no {action!r} row action on live record {eid}")
    seen = []

    def on_dialog(d):
        seen.append([d.type, squash(d.message)[:160]])
        d.accept("QCTEST B11 automated case step") if d.type == "prompt" else d.accept()

    admin.page.on("dialog", on_dialog)
    try:
        ctl.first.click(force=True)
        admin.page.wait_for_timeout(2000)  # condition: dialogs fire from the click; list re-renders after
        try:
            admin.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:  # noqa: BLE001
            pass
    finally:
        admin.page.remove_listener("dialog", on_dialog)
    print(f"[live {eid}] row action {action}: dialogs {seen}")
    return seen


def exact_copy(fixture: str, name: str) -> str:
    dest = Path(tempfile.gettempdir()) / "qctest_b11" / name
    dest.parent.mkdir(exist_ok=True)
    shutil.copy(fixture, dest)
    return str(dest)


def log_upload_leftover(eid, data: dict, key: str):
    """Uploads land in Documents & Media; D&M files are never deleted by
    automation. The new file id is logged as a known leftover."""
    v = data.get(key) or {}
    line = (f"B11 2026-10-04 live {eid}: uploaded D&M file id={v.get('id')} name={v.get('name')!r} "
            f"left in Documents & Media (record restored to its own file id; D&M delete is off-limits)")
    print(line)
    try:
        with open("reports/live-restore/b11/dm_leftovers.txt", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Public side (fresh logged-out context every time)
# ---------------------------------------------------------------------------
def anon(browser):
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False)
    return ctx, ctx.new_page()


def visit(p, path, locale="en", settle_sel=None):
    resp = p.goto(web_url(path, locale=locale), wait_until="domcontentloaded", timeout=60000)
    try:
        p.wait_for_load_state("networkidle", timeout=15000)
    except Exception:  # noqa: BLE001
        pass
    if settle_sel:
        try:
            p.locator(settle_sel).first.wait_for(state="attached", timeout=20000)
        except Exception:  # noqa: BLE001 - absence is judged by the caller
            pass
    p.wait_for_timeout(1500)  # client-rendered fragment settles (measured ~1 s)
    return resp.status if resp else None


def poll_public(browser, path, probe, locale="en", timeout=75.0, settle_sel=None):
    """Reload a fresh logged-out page until probe(page, http) returns
    (True, info); returns (ok, info, seconds)."""
    ctx, p = anon(browser)
    t0 = time.monotonic()
    try:
        while True:
            http = visit(p, path, locale, settle_sel)
            ok, info = probe(p, http)
            if ok or time.monotonic() - t0 > timeout:
                return ok, info, round(time.monotonic() - t0, 1)
            p.wait_for_timeout(3000)
    finally:
        ctx.close()


def buttons(p, sel) -> list[dict]:
    loc = p.locator(sel)
    out = []
    for i in range(loc.count()):
        e = loc.nth(i)
        if not e.is_visible():
            continue
        out.append({"label": squash(e.inner_text()), "href": e.get_attribute("href") or "",
                    "target": e.get_attribute("target") or ""})
    return out


def texts(p, sel) -> list[str]:
    loc = p.locator(sel)
    return [squash(loc.nth(i).inner_text()) for i in range(loc.count()) if loc.nth(i).is_visible()]


def expect_public(browser, path, probe, what, locale="en", timeout=75.0, settle_sel=None):
    ok, info, secs = poll_public(browser, path, probe, locale, timeout, settle_sel)
    print(f"[public {locale}] {what}: ok={ok} after {secs}s info={json.dumps(info, ensure_ascii=False)[:600]}")
    assert ok, f"{locale.upper()} {path}: {what} - not seen within {timeout}s; observed {json.dumps(info, ensure_ascii=False)[:500]}"
    return info


def not_served(http, p, marker_sels) -> tuple[bool, dict]:
    present = {s: len(texts(p, s)) for s in marker_sels}
    gone = (http is not None and http >= 400) or not any(present.values())
    return gone, {"http": http, "present": present}

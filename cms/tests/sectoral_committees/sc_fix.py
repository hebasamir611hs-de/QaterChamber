"""
cms/tests/sectoral_committees/sc_fix.py - Engineer A5's 130716-only check
bodies (2026-10-04 triage of A4's run). Not a test module.

Kept apart from cc_checks.py (shared with A4's 130717/130718/130719) so no
shared function changes signature or behaviour.

Fixes, each with the run evidence that drove it:
  * check_mandate_scoped - cc.check_mandate read EVERY li.qc-sc-mandate-item
    on the page (the first committee's 11 bullets came back for the QCTEST
    row). The checklist is now read inside OUR committee row only.
    Teardown: a trashed mandate item still holds its relationship, so the
    committee's trash call answered HTTP 400 "Delete failed: null" and six
    Published + Active QCTEST committees stayed on the live page (run
    2026-10-04 16:41). Every QCTEST mandate this test created is now
    hard-deleted BY ID (after checking it is ours and linked to our
    committee) before the committee is trashed.
  * check_anonymous_write_refused_scoped - Committee Item is a SITE-scoped
    object: POST /o/c/committeeitems answers 409 "Conflict with
    postObjectEntry" for any caller (request shape, not auth). The
    anonymous write goes to /o/c/committeeitems/scopes/<siteId>.
"""

from __future__ import annotations

import json
import time

from cms.pages.certificate_of_origin.fragment_form_mixin import log_leftover
from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.tests.sectoral_committees import cc_checks as cc
from config.settings import control_panel_url, web_url

SITE_ID = "37246"  # scopeId of every Qatar Chamber object entry (read live 2026-10-04)
MANDATE_LI = "li.qc-sc-mandate-item"


def _row_bullets(anon, name, locale="en") -> list[str]:
    """The checklist items of the ONE public row whose text holds `name`
    (row expanded first)."""
    from cms.pages.join_committee.council_base import squash

    sc = cc._open_sc(anon, locale)
    cc._expand(anon, sc, ("row", name))
    row = anon.locator(sc.ROW).filter(has_text=name).first
    if not row.count():
        return []
    return [squash(t) for t in row.locator(MANDATE_LI).all_inner_texts()]


def _purge_trashed(admin, eid: str, committee_erc: str | None) -> None:
    """Hard-delete OUR QCTEST mandate item `eid` (already trashed, or never
    trashed) BY ID. Refuses unless the stored record is a QCTEST one linked to
    our committee."""
    if not eid:
        return
    page = admin.page
    try:
        if "/o/" in page.url or "qcdev" not in page.url:
            page.goto(control_panel_url("/en/web/qatar-chamber/manage-committee-mandate-item"),
                      wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
        token = page.evaluate("() => (window.Liferay && Liferay.authToken) || ''")
        req = page.context.request
        hdr = {"x-csrf-token": token, "accept": "application/json"}
        r = req.get(control_panel_url(f"/o/c/committeemandateitems/{eid}"), headers=hdr)
        if r.status == 404:
            return
        data = r.json() if r.ok else {}
        ours = str(data.get("friendlyUrlPath", "")).startswith("qctest-")
        linked = committee_erc is None or data.get("r_committeeMandateItems_c_committeeItemERC") == committee_erc
        if not (ours and linked):
            log_leftover(f"NOT PURGED committee-mandate-item id={eid}: not ours/linked ({data.get('friendlyUrlPath')!r})")
            return
        d = req.delete(control_panel_url(f"/o/c/committeemandateitems/{eid}"), headers=hdr)
        if d.status not in (200, 204, 404):
            log_leftover(f"purge refused committee-mandate-item id={eid}: HTTP {d.status}")
    except Exception as exc:  # noqa: BLE001 - teardown never masks the result
        log_leftover(f"purge error committee-mandate-item id={eid}: {str(exc)[:160]}")


def check_mandate_scoped(page, browser, item_cls, mandate_cls, tc, mode):
    """Same scenario as cc.check_mandate (mode: add | edit | reorder | remove |
    ar | remove_last), with the checklist read inside OUR committee row and a
    teardown that leaves no QCTEST committee behind."""
    item, mand = item_cls(page), mandate_cls(page)
    c = cc.title(tc, "cmte")
    b1, b2 = cc.title(tc, "item-1"), cc.title(tc, "item-2")
    ar1 = f"بند اختبار 1 {cc.RUN}"
    made, eids = [], {}
    ctx, anon = cc._anon(browser)

    def wait_bullets(pred, locale="en"):
        name = c if locale == "en" else f"{c} AR"
        deadline = time.monotonic() + cc.PUBLIC_POLL_S
        while True:
            got = _row_bullets(anon, name, locale)
            if pred(got) or time.monotonic() > deadline:
                return got
            anon.wait_for_timeout(3000)

    def add(b, order, ar):
        cc._publish(mand, b, extra={"committee": c, "display_order": order}, ar_extra={"bullet": ar})
        made.append(b)
        eids[b] = mand.id_for(b)

    try:
        cc._publish(item, c)
        assert cc.sc_probe(cc.DIRECTORY)(anon, c), f"precondition: committee {c!r} not listed ({cc._gates(item, c)})"
        add(b1, "100", ar1)
        if mode == "remove_last":
            got = wait_bullets(lambda g: any(b1 in x for x in g))
            assert any(b1 in x for x in got), f"precondition: {b1!r} not in the checklist {got!r}"
            ok = mand.delete_disposable(b1)
            still = mand.entry_exists(b1, ROLE_EDITOR)
            after = wait_bullets(lambda g: not any(b1 in x for x in g))
            print(f"[tc_{tc}] remove last bullet: delete_ran={ok} still_listed={still} public_after={after!r} "
                  f"committee={cc._gates(item, c)}")
            assert still and not ok, (
                f"the only mandate bullet of the Published committee {c!r} was removed (delete ran={ok}, "
                f"public checklist now {after!r}); the case expects a refusal")
            return
        add(b2, "200", f"بند اختبار 2 {cc.RUN}")
        got = wait_bullets(lambda g: len(g) >= 2)
        assert len(got) == 2 and b1 in got[0] and b2 in got[1], (
            f"checklist of {c!r} is {got!r}, expected [{b1!r}, {b2!r}]")
        if mode == "ar":
            ar = wait_bullets(lambda g: any(ar1 in x for x in g), locale="ar")
            assert any(ar1 in x for x in ar), f"AR checklist {ar!r} lacks the AR bullet"
        elif mode == "edit":
            new = f"{b2} edited"
            mand.open_list(ROLE_EDITOR)
            mand.open_entry_by_edit_link(b2)
            mand.fill("bullet", new)
            mand.submit_for_review()
            got = wait_bullets(lambda g: any(new in x for x in g))
            assert any(new in x for x in got), f"checklist {got!r} lacks the edited bullet {new!r}"
        elif mode == "reorder":
            mand.open_list(ROLE_EDITOR)
            mand.open_entry_by_edit_link(b2)
            mand.fill("display_order", "50")
            mand.submit_for_review()
            got = wait_bullets(lambda g: len(g) >= 2 and b2 in g[0])
            assert len(got) == 2 and b2 in got[0] and b1 in got[1], f"checklist order {got!r}, expected bullet 2 first"
        elif mode == "remove":
            assert mand.delete_disposable(b1), f"{b1!r}: delete did not run"
            made.remove(b1)
            got = wait_bullets(lambda g: len(g) == 1)
            assert len(got) == 1 and b2 in got[0], f"checklist after removal {got!r}, expected only {b2!r}"
    finally:
        for b in made:
            cc._delete(mand, b)
        erc = None
        try:
            erc = (item.entry_json(c) or {}).get("externalReferenceCode")
        except Exception:  # noqa: BLE001
            pass
        for eid in eids.values():
            _purge_trashed(mand, eid, erc)
        cc._delete(item, c)
        cc._close(ctx)


def check_anonymous_write_refused_scoped(browser, plural, body: dict, probe=None, page=None, name_key=None):
    """A logged-out POST to the SITE-scoped /o/c/<plural>/scopes/<siteId> is
    refused (401/403) and nothing is created; with `probe` the public page
    does not show the value."""
    ctx, anon = cc._anon(browser)
    try:
        anon.goto(web_url(cc.SC_PATH, locale="en"), wait_until="domcontentloaded")
        url = control_panel_url(f"/o/c/{plural}/scopes/{SITE_ID}")
        status, text = anon.evaluate(
            """async ([u, b]) => { const r = await fetch(u, {method: 'POST', credentials: 'same-origin',
                 headers: {'content-type': 'application/json', accept: 'application/json'}, body: b});
                 return [r.status, (await r.text()).slice(0, 300)]; }""",
            [url, json.dumps(body)])
        print(f"anonymous POST /o/c/{plural}/scopes/{SITE_ID}: HTTP {status} {text[:120]!r}")
        if 200 <= status < 300:
            log_leftover(f"ANON-CREATED {plural}: {text[:200]}")
            _drop_anon_created(page, plural, text, body.get(name_key) if name_key else None)
        assert status in (401, 403), f"anonymous write answered HTTP {status} (expected 401/403): {text[:160]!r}"
        if probe:
            name = next(iter(body.values()))
            assert not probe(anon, name, False), f"{name!r} appears on the public page"
    finally:
        cc._close(ctx)


def _drop_anon_created(page, plural, text, name):
    """Only when the product WRONGLY accepted the anonymous write: delete
    that one record BY ID as the Editor, after checking it carries our name."""
    if page is None or not name:
        return
    try:
        eid = str(json.loads(text).get("id", ""))
    except Exception:  # noqa: BLE001 - body truncated: id read below
        import re as _re
        m = _re.search(r'"id"\s*:\s*(\d+)', text)
        eid = m.group(1) if m else ""
    if not eid:
        log_leftover(f"ANON-CREATED {plural}: id unreadable, NOT deleted")
        return
    try:
        from cms.pages.control_panel.login_page import CmsLoginPage
        from config.settings import cms_role_credentials
        e, pw = cms_role_credentials(ROLE_EDITOR)
        CmsLoginPage(page).open_login().login(e, pw)
        token = page.evaluate("() => (window.Liferay && Liferay.authToken) || ''")
        hdr = {"x-csrf-token": token, "accept": "application/json"}
        r = page.context.request.get(control_panel_url(f"/o/c/{plural}/{eid}"), headers=hdr)
        if name not in r.text():
            log_leftover(f"ANON-CREATED {plural} id={eid}: stored record lacks {name!r}, NOT deleted")
            return
        d = page.context.request.delete(control_panel_url(f"/o/c/{plural}/{eid}"), headers=hdr)
        log_leftover(f"ANON-CREATED {plural} id={eid}: deleted by ID -> HTTP {d.status}")
    except Exception as exc:  # noqa: BLE001
        log_leftover(f"ANON-CREATED {plural} id={eid}: delete error {str(exc)[:160]}")


def check_number_derived(page, browser, admin_cls, tc, key, num_sel, item_sel, value="99"):
    """Case-faithful (146971 / 146935): the number field is read-only OR the
    public number is DERIVED. When the input is editable, a QCTEST record is
    published (Active ticked) with `value` typed, and the public badge must
    read its sequential position, not `value`."""
    admin = admin_cls(page)
    admin.open_form(ROLE_EDITOR)
    box = page.get_by_role("spinbutton", name=admin.label_pattern(admin_cls.FIELDS[key].label)).first
    if not box.is_editable():
        return
    t = cc.title(tc, "num99")
    ctx, anon = cc._anon(browser)
    try:
        cc._publish(admin, t, extra={key: value})
        expand = "lead" if "leader" in item_sel else None
        assert cc.sc_probe(None, expand)(anon, t), f"{t!r} not shown ({cc._gates(admin, t)})"
        items = anon.locator(item_sel)
        texts = [" ".join(x.split()) for x in items.all_inner_texts()]
        pos = next((i for i, x in enumerate(texts) if t in x), None)
        assert pos is not None, f"{t!r} not in {item_sel}"
        badge = " ".join(items.nth(pos).locator(num_sel).inner_text().split())
        assert badge == f"{pos + 1:02d}", (
            f"{admin_cls.FIELDS[key].label}: typed {value!r}, public number reads {badge!r}; expected the "
            f"sequential {pos + 1:02d} (the case: system-generated, cannot be overridden)")
    finally:
        cc._delete(admin, t)
        cc._close(ctx)

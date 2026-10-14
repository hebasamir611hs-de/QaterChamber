"""
cms/tests/sectoral_committees/live_checks.py - check bodies for the CONDITIONAL
cases that act on the three LIVE singleton page records (Engineer A6,
2026-10-04). Not a test module.

User approval (2026-10-04, explicit and ID-named): the tests may edit /
unpublish the live records 181385 (Sectoral Committees Page), 208073 (QAFL
Page Content) and 183176 (Business Council Request Page). The real data is
snapshot BEFORE and restored AFTER every single test by
reports/live-restore/live_restore.py, which runs in its own process. These
helpers therefore never try to restore anything themselves; they never
DELETE (the guard keeps blocking DELETE on every live id) and never register
the live id in the page object's identity table (teardown deletes resolve
from it).

The test case is the oracle: values the case names are used verbatim; where
the case leaves the value open, a QCTEST-marked value is used so the
propagation is provable. Missing toasts / wording are not asserted.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.join_committee.council_base import squash
from cms.tests.sectoral_committees import cc_checks as cc
from config.settings import web_url

SC_PATH = cc.SC_PATH
QAFL_PATH = cc.QAFL_PATH
BCMR_PATH = cc.BCMR_PATH


# ---------------------------------------------------------------------------
# Control Panel side
# ---------------------------------------------------------------------------
def ctx_get(admin, path):
    """READ through the context's APIRequestContext with accept-only headers
    (B11 2026-10-04: in-page fetch with json content-type + CSRF header is
    answered with the 'Coming Soon' 404 HTML since ~18:05Z)."""
    from config.settings import control_panel_url as _cpu
    try:
        r = admin.page.context.request.get(_cpu(path), headers={"accept": "application/json"}, timeout=60000)
        return r.status, r.text()
    except Exception as exc:  # noqa: BLE001
        return -1, str(exc)[:200]


_WF = {"approved": "Published", "draft": "Draft", "incomplete": "Draft", "pending": "Pending Review",
       "denied": "Rejected", "scheduled": "Scheduled", "expired": "Unpublished"}


def live_state(admin, live_id) -> str:
    """Editorial state of the live record: /o/qc-object-status/transitions/<id>
    statusLabelEn, falling back to the record's own Liferay status."""
    st, txt = ctx_get(admin, f"/o/qc-object-status/transitions/{live_id}")
    try:
        data = json.loads(txt) if st == 200 else {}
    except ValueError:
        data = {}
    if data and (data.get("statusKey") or "").casefold() != "inactive":
        return data.get("statusLabelEn") or data.get("statusLabel") or ""
    wf = (live_json(admin, live_id).get("status") or {}).get("label", "")
    return _WF.get(wf.casefold(), f"Inactive/{wf}")


def live_json(admin, live_id) -> dict:
    """READ of the live record; on an HTML / Coming-Soon / 404 answer (the
    session was signed out) one fresh re-login and one re-read. Never used for writes."""
    for attempt in (0, 1):
        status, text = ctx_get(admin, f"/o/c/{admin.PLURAL}/{live_id}")
        try:
            if status == 200:
                return json.loads(text)
        except ValueError:
            pass
        if attempt:
            break
        print(f"[live {live_id}] READ answered HTTP {status} non-JSON ({text[:60]!r}): re-login and re-read once")
        from cms.pages.certificate_of_origin import fragment_form_mixin as _ffm
        from config.settings import cms_role_credentials as _crc
        email, pw = _crc(ROLE_EDITOR)
        _ffm._ROLE_COOKIES.pop(email, None)
        admin._fresh_login(email, pw)
        admin.open(admin._manage_url(locale="en"))
    raise AssertionError(f"GET live {live_id}: HTTP {status} {text[:160]}")


def open_live(admin, live_id, role=ROLE_EDITOR) -> dict:
    """Sign in as `role`, install the guard, exempt ONLY `live_id` from it
    (PUT/PATCH), and open the live entry's edit form by its own ERC."""
    live_id = str(live_id)
    assert live_id in admin.LIVE_IDS, f"{live_id} is not an approved live id of {admin.SLUG}"
    admin.open_list(role)  # installs the guard and protects every listed id
    admin._protected().add(live_id)
    data = live_json(admin, live_id)
    admin.allow_live_write(live_id)
    # Run 2026-10-04 (tc_144518): the singleton edit form carries no "Cancel and
    # add new" link, so open_entry_by_code's settle never fires. The form is
    # ready when its submit is visible AND the title input holds the live title.
    admin.open(admin._manage_url(edit_entry=data["externalReferenceCode"], locale="en"))
    admin.page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).first.wait_for(state="visible", timeout=40000)
    parts = admin.TITLE_FIELD.split("_")
    want = (data.get(parts[0] + "".join(p.title() for p in parts[1:]) + "_i18n") or {}).get("en_US", "")
    box = admin.page.get_by_role("textbox", name=admin.label_pattern(admin.FIELDS[admin.TITLE_FIELD].label)).first
    for _ in range(30):
        if box.count() and box.input_value() == want:
            break
        admin.page.wait_for_timeout(500)
    assert box.input_value() == want, (
        f"the edit form does not hold live record {live_id} (title {box.input_value()[:60]!r} != {want[:60]!r})")
    # Run 2026-10-04 (183176 refusal cases): Submit clicked before the AR inputs
    # and the rich-text editors were hydrated was refused for THOSE (still empty)
    # fields. The form is ready only when every stored AR text value sits in its
    # qc-ar-<ref> input and every rich editor holding stored text shows it.
    _wait_hydrated(admin, data)
    # FINDING (control 2026-10-04, reports/live-restore/183176/control_*.json):
    # the live edit form, submitted UNCHANGED, is refused "Please complete the
    # required fields" with the three rich-text editors flagged - their
    # required-check is not synced from the loaded values. After a no-op
    # keystroke in each editor the same unchanged submit saves (PUT 200, record
    # unchanged). Every case primes the editors this way so a refusal / save is
    # attributable to the field the case changes, not to that defect.
    prime_rich(admin)
    ident = admin._ident()
    ident["editing"] = (admin.PLURAL, live_id)
    ident["pending"] = None
    banner = [ln for ln in admin.page.locator("body").inner_text().splitlines() if ln.startswith("Editing ")]
    print(f"[live {live_id}] form opened: {banner[:1]!r} status={data.get('status', {}).get('label')!r}")
    return data


def saved(admin, live_id) -> bool:
    ls = admin.last_save or {}
    return bool(ls.get("started")) and str(ls.get("id") or "") == str(live_id)


def publish_live(admin, live_id, expect_published=True):
    """Click the form's submit (Publish / Submit) and require the write to have
    reached the live record; with `expect_published` the record must read
    Published by ID."""
    admin.submit_for_review()
    assert saved(admin, live_id), f"the submit did not save live record {live_id} ({admin.save_counts()})"
    if expect_published:
        st = live_state(admin, live_id)
        assert st == STATUS_PUBLISHED, f"live record {live_id} is {st!r} after the Editor's submit"


def save_draft_live(admin, live_id):
    """The case's Save as Draft step: the control must be offered and enabled,
    and the draft must be stored on the record."""
    btn = admin.page.locator(admin.SAVE_AS_DRAFT_BUTTON).first
    offered = btn.count() > 0 and btn.is_visible() and btn.is_enabled()
    tip = (btn.get_attribute("title") or "") if btn.count() else ""
    assert offered, (f"{admin.SIDEBAR_LABEL}: the Editor is offered no enabled 'Save as Draft' on the live page "
                     f"record (present={btn.count() > 0}, title={tip!r}); the case saves a Draft")
    admin.save_as_draft()
    assert saved(admin, live_id), f"Save as Draft stored nothing on {live_id} ({admin.save_counts()})"


def fill_bi(admin, key, en=None, ar=None):
    if en is not None:
        admin.fill(key, en)
    if ar is not None:
        admin.fill(key, ar, locale="ar")


_SET_RICH_JS = """([sel, html]) => {
  const fr = document.querySelector(sel);
  if (!fr) return 'no-iframe';
  if (window.CKEDITOR) {
    for (const inst of Object.values(CKEDITOR.instances)) {
      try {
        if (inst.window && inst.window.$ && inst.window.$.frameElement === fr) {
          inst.setData(html); inst.fire('change'); inst.updateElement && inst.updateElement();
          return 'ckeditor';
        }
      } catch (e) {}
    }
  }
  const body = fr.contentDocument && fr.contentDocument.body;
  if (!body) return 'no-body';
  body.innerHTML = html;
  body.dispatchEvent(new Event('input', {bubbles: true}));
  return 'innerHTML';
}"""


def set_rich_html(admin, key, html, locale="en"):
    """Rich-text content with markup the keyboard cannot type (lists, links,
    source-mode script): CKEditor's own setData on the field's editor."""
    sel = admin._rich_iframe(key, locale)
    body = admin.page.frame_locator(sel).locator("body")
    body.wait_for(state="visible", timeout=30000)
    body.click()
    css = admin.page.locator(sel).first.evaluate(
        "f => { f.setAttribute('data-a6-rich', '1'); return 'iframe[data-a6-rich=\"1\"]'; }")
    try:
        how = admin.page.evaluate(_SET_RICH_JS, [css, html])
    finally:
        admin.page.locator(css).first.evaluate("f => f.removeAttribute('data-a6-rich')")
    print(f"[rich {key}/{locale}] set via {how}")
    assert how in ("ckeditor", "innerHTML"), f"could not set {key} {locale}: {how}"
    body.click()
    admin.page.keyboard.press("End")
    admin.page.wait_for_timeout(500)


def type_rich_bold(admin, key, before, bold, after, locale="en"):
    """Real keyboard typing with Ctrl+B around `bold` (the editor's own bold)."""
    sel = admin._rich_iframe(key, locale)
    body = admin.page.frame_locator(sel).locator("body")
    body.wait_for(state="visible", timeout=30000)
    body.click()
    kb = admin.page.keyboard
    kb.press("Control+A")
    kb.press("Delete")
    kb.type(before)
    kb.press("Control+B")
    kb.type(bold)
    kb.press("Control+B")
    kb.type(after)
    html = admin.page.frame_locator(sel).locator("body").inner_html()
    assert f"<strong>{bold}</strong>" in html or f"<b>{bold}</b>" in html, f"editor did not bold {bold!r}: {html[:200]}"


def clear_file(admin, key) -> str:
    """Remove the attached file of a file field (the field's own clear / remove
    control next to the filename readout). Returns how it was cleared."""
    label = admin.FIELDS[key].label
    hidden = admin.page.get_by_role("textbox", name=f"{label} Select File")
    # Live 2026-10-04 (183176 edit form): an existing file is NOT loaded into
    # the field - the input is empty, its placeholder reads "Current file: <name>
    # - pick a file to replace it", and the Remove button stays d-none. The
    # field is then already empty as the form will submit it.
    remove = hidden.locator("xpath=../..").locator("button[id$='-file-upload-remove-button']")
    if hidden.count() and not hidden.first.input_value() and remove.count() and not remove.first.is_visible():
        return f"field already empty on the edit form (placeholder {hidden.first.get_attribute('placeholder')!r})"
    holder = hidden.locator("xpath=..")
    for name in ("Clear", "Remove", "Delete", "Clear Selection", "Remove File"):
        b = holder.get_by_role("button", name=name)
        if b.count():
            b.first.click()
            admin.page.wait_for_timeout(800)
            return name
    # one level up (the readout + buttons wrapper)
    holder2 = holder.locator("xpath=..")
    btns = holder2.locator("button:not(:has-text('Select File'))")
    names = [squash(btns.nth(i).inner_text()) or (btns.nth(i).get_attribute("aria-label") or "")
             for i in range(btns.count())]
    for i, n in enumerate(names):
        if any(w in n.lower() for w in ("clear", "remove", "delete", "x")) or n in ("×", "✕"):
            btns.nth(i).click()
            admin.page.wait_for_timeout(800)
            return n
    raise AssertionError(f"{label}: no control to remove the attached file (buttons {names!r})")


def file_id(data: dict, json_key: str):
    v = data.get(json_key)
    return v.get("id") if isinstance(v, dict) else None


def row_action_live(admin, live_id, action, role=ROLE_EDITOR) -> list:
    """Click the live row's data-qc-oel-<action>="<id>" control, accepting
    every native dialog (a prompt gets a QCTEST comment)."""
    admin.open_list(role)
    admin._protected().add(str(live_id))
    ctl = admin.page.locator(f'[data-qc-oel-{action}="{live_id}"]')
    try:
        ctl.first.wait_for(state="attached", timeout=20000)
    except Exception:  # noqa: BLE001
        raise AssertionError(f"{role} is offered no {action!r} row action on live record {live_id}")
    seen = []

    def on_dialog(d):
        seen.append([d.type, squash(d.message)[:160]])
        d.accept("QCTEST A6 automated case step") if d.type == "prompt" else d.accept()

    admin.page.on("dialog", on_dialog)
    try:
        ctl.first.click(force=True)
        # condition: the dialogs fire from the click; the list re-renders after (live ~2 s)
        admin.page.wait_for_timeout(2000)
        try:
            admin.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:  # noqa: BLE001
            pass
    finally:
        admin.page.remove_listener("dialog", on_dialog)
    print(f"[live {live_id}] row action {action}: dialogs {seen}")
    return seen


def wait_status(admin, live_id, want, timeout=30.0) -> str:
    deadline = time.monotonic() + timeout
    while True:
        st = live_state(admin, str(live_id))
        if st == want or time.monotonic() > deadline:
            return st
        admin.page.wait_for_timeout(2000)


# ---------------------------------------------------------------------------
# Public side (fresh logged-out context every time)
# ---------------------------------------------------------------------------
def anon(browser, viewport=None):
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False, viewport=viewport)
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
        except Exception:  # noqa: BLE001 - absence is reported by the caller
            pass
    p.wait_for_timeout(1500)  # client-rendered fragment settles (measured ~1 s)
    return resp.status if resp else None


def text_of(p, sel) -> str:
    loc = p.locator(sel)
    return " | ".join(squash(t) for t in loc.all_inner_texts()) if loc.count() else ""


def poll_text(browser, path, sel, want, locale="en", timeout=60.0, interval=3.0, settle_sel=None,
              expect=True, prepare=None):
    """Reload a fresh logged-out page until `want in text(sel)` == expect.
    Returns (ok, last_text, seconds)."""
    ctx, p = anon(browser)
    t0 = time.monotonic()
    got = ""
    try:
        while True:
            visit(p, path, locale, settle_sel or sel)
            if prepare:
                prepare(p)
            got = text_of(p, sel)
            if (want in got) == expect or time.monotonic() - t0 > timeout:
                return (want in got) == expect, got, round(time.monotonic() - t0, 1)
            p.wait_for_timeout(int(interval * 1000))
    finally:
        cc._close(ctx)


def check_text_both(browser, path, sel, en, ar, timeout=60.0, interval=3.0, settle_sel=None, prepare=None,
                    attr=None):
    for loc, want in (("en", en), ("ar", ar)):
        if want is None:
            continue
        ok, got, secs = poll_text(browser, path, sel, want, loc, timeout, interval, settle_sel, prepare=prepare)
        if not ok and timeout < 60:
            late, got2, secs2 = poll_text(browser, path, sel, want, loc, 60.0, 3.0, settle_sel, prepare=prepare)
            raise AssertionError(f"{loc.upper()} {sel} does not show {want!r} within {timeout}s (shows {got[:200]!r}); "
                                 f"{'it appeared after ' + str(secs2) + 's' if late else 'not even after 60s'}")
        assert ok, f"{loc.upper()} public {sel} does not show {want!r} after {secs}s (shows {got[:200]!r})"


def served(browser, path, marker_sel, locale="en"):
    """(http, marker_text) for a fresh logged-out visit."""
    ctx, p = anon(browser)
    try:
        http = visit(p, path, locale, marker_sel)
        return http, text_of(p, marker_sel)
    finally:
        cc._close(ctx)


def assert_not_served(browser, path, marker_sel, locale, timeout=60.0):
    """The case: not-found / not served, never a stale 200 with content."""
    deadline = time.monotonic() + timeout
    while True:
        http, txt = served(browser, path, marker_sel, locale)
        gone = (http is not None and http >= 400) or not txt
        if gone or time.monotonic() > deadline:
            break
        time.sleep(3)
    assert gone, f"{locale.upper()} {path} still serves the content to a visitor: HTTP {http}, {marker_sel}={txt[:120]!r}"
    print(f"[public {locale}] not served: HTTP {http}, marker {txt[:60]!r}")
    return http


def assert_served(browser, path, marker_sel, locale, timeout=60.0):
    deadline = time.monotonic() + timeout
    while True:
        http, txt = served(browser, path, marker_sel, locale)
        if (http == 200 and txt) or time.monotonic() > deadline:
            break
        time.sleep(3)
    assert http == 200 and txt, f"{locale.upper()} {path}: HTTP {http}, {marker_sel}={txt[:80]!r} (expected 200 with content)"


def exact_name_copy(fixture: str, name: str) -> str:
    dest = Path(tempfile.gettempdir()) / "qctest_a6" / name
    dest.parent.mkdir(exist_ok=True)
    dest.write_bytes(Path(fixture).read_bytes())
    return str(dest)


def history_live(admin, live_id, role=ROLE_EDITOR) -> list[dict]:
    """The live row's History trail (newest first, as rendered), read by its
    own data-qc-oel-history="<id>" control."""
    admin.open_list(role)
    ctl = admin.page.locator(f'[data-qc-oel-history="{live_id}"]').first
    ctl.wait_for(state="attached", timeout=20000)
    ctl.click(force=True)
    hist = admin.page.locator(admin.HISTORY_LIST).first
    hist.wait_for(state="visible", timeout=15000)
    hist.locator(f"{admin.HISTORY_WHO}:not(:empty)").first.wait_for(state="attached", timeout=15000)
    items = hist.locator(":scope > li")
    out = []
    for i in range(items.count()):
        it = items.nth(i)

        def part(sel):
            n = it.locator(sel)
            return squash(n.first.inner_text()) if n.count() else ""

        out.append({"action": part(".qc-oel__history-action"), "who": part(admin.HISTORY_WHO),
                    "when": part(admin.HISTORY_WHEN), "comment": part(admin.HISTORY_COMMENT)})
    return out


def download_from(browser, path, link_sel, locale="en"):
    """Click the public download link logged out; (suggested_filename, bytes)."""
    ctx, p = anon(browser)
    try:
        visit(p, path, locale, link_sel)
        with p.expect_download(timeout=60000) as dl:
            p.locator(link_sel).first.click()
        d = dl.value
        dest = Path(tempfile.gettempdir()) / "qctest_a6" / f"dl_{d.suggested_filename}"
        dest.parent.mkdir(exist_ok=True)
        d.save_as(str(dest))
        return d.suggested_filename, dest.read_bytes()
    finally:
        cc._close(ctx)


def file_key(data: dict, needle: str) -> str | None:
    for k, v in data.items():
        if needle.lower() in k.lower() and not k.endswith("_i18n") and (isinstance(v, dict) or v is None):
            return k
    return None


_HYDRATION_JS = """(exp) => {
  const out = [];
  for (const [ref, ar] of Object.entries(exp.ar)) {
    const el = document.getElementById('qc-ar-' + ref);
    if (el && el.tagName !== 'TEXTAREA' && el.value !== ar) out.push('ar:' + ref);
  }
  const frames = [...document.querySelectorAll('iframe[title="editor"]')];
  const empty = frames.filter(f => { try { return !(f.contentDocument.body.innerText || '').trim(); } catch (e) { return true; } });
  if (empty.length > exp.emptyRichAllowed) out.push('rich-empty:' + empty.length);
  return out;
}"""


def _wait_hydrated(admin, data, timeout_s=30.0):
    ar = {k[:-5]: (v or {}).get("ar_SA", "") for k, v in data.items()
          if k.endswith("_i18n") and k != "friendlyUrlPath_i18n" and isinstance(v, dict) and v.get("ar_SA")}
    rich_refs = [s.ref for s in admin.FIELDS.values() if s.kind == "rich" and s.ref]
    stored_rich = sum(1 for r in rich_refs for loc in ("en_US", "ar_SA")
                      if ((data.get(f"{r}_i18n") or {}).get(loc) or "").strip())
    exp = {"ar": ar, "emptyRichAllowed": max(0, 2 * len(rich_refs) - stored_rich)}
    deadline = time.monotonic() + timeout_s
    missing = []
    while time.monotonic() < deadline:
        missing = admin.page.evaluate(_HYDRATION_JS, exp)
        if not missing:
            admin.page.wait_for_timeout(500)
            return
        admin.page.wait_for_timeout(500)
    raise AssertionError(f"the live edit form never finished loading the stored values: {missing}")


def prime_rich(admin):
    """A no-op keystroke (space + Backspace at the end) in every rich editor."""
    for key, spec in admin.FIELDS.items():
        if spec.kind != "rich":
            continue
        for loc in ("en", "ar"):
            body = admin.page.frame_locator(admin._rich_iframe(key, loc)).locator("body")
            body.click()
            admin.page.keyboard.press("Control+End")
            admin.page.keyboard.type(" ")
            admin.page.keyboard.press("Backspace")
    admin.page.wait_for_timeout(800)

"""
cms/tests/vision_mission_objectives/test_vmo_phase3_control_panel.py -- the
P1/P2 Control_Panel cases of PBI 129395 (QC-ABOUT-004, Vision, Mission,
Objectives), suite 134466. Scripted 2026-10-14 (Phase 3) on the forms read live
that day (cms/pages/vision_mission_objectives/vmo_admin_page.py, Phase-3 block).
The Azure case text is the oracle.

Records (all REAL, qcdev is shared)
-----------------------------------
* `vision-mission-objectives-page` -- the page singleton
  QCDEMO-129395-VISION-MISSION-OBJECTIVES-PAGE-main (Page Title, Hero Image,
  Intro Heading, Intro Description, Active Status).
* `vmo-section` -- QCDEMO-129395-VMO-VISION / -MISSION / -OBJECTIVES.

PBI running rules (QA lead, 2026-10-13/14): test data MAY be written to real
records; NOTHING is deleted; every persisted (or possibly persisted) write is
logged BEFORE its click to reports/live-writes-<date>.jsonl; a real record left
Unpublished is re-published. On top of that, every test here puts the values
it read before the test back in `finally` and leaves the record Published, so
the public About page is not left with test data.

Case-text mapping (the forms differ from the case wording):
* "Save" = the form's Publish control (status=0) -- the Editor's only submit
  on a Published row ("Publish puts your change on the website straight away").
  Save as Draft skips required-field validation, so it is never used for a
  refusal case.
* "Hero Banner (EN)" / "Hero Banner (AR)" -> the ONE `Hero Image` field.
* "Section Content" -> `Body Content`; "Active status" -> `Active Status`.
* Toast / message wording is recorded, never asserted (rule 17). The refusal
  proof is the stored value on a fresh read.

Accounts: QC Site Content Editor unless a case names another role (Author for
136170/136171); logged-out contexts for 136166/136173 and every public check.
"""

from __future__ import annotations

import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import allure
import pytest

from cms.pages.components.disposable_object_admin import (
    ROLE_AUTHOR,
    ROLE_EDITOR,
    DisposableObjectAdminPage,
)
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED, STATUS_UNPUBLISHED
from cms.pages.vision_mission_objectives.vmo_admin_page import (
    SLUG as SECTION_SLUG,
    VMO_PAGE_CODE,
    VMO_PAGE_SLUG,
    VMO_SECTION_CODES,
    VmoPageForm,
    VmoSectionForm,
)
from cms.tests.live_write_guard import LiveRecord, log_live_write
from cms.tests.singleton_baseline import drive_to_published, list_status
from config.settings import web_url
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from tools.fixture_factory import make_jpg, make_png
from web.pages.vision_mission_objectives.vmo_page import VMO_PATH, VmoPage

EN, AR = "en", "ar"
ONE_MB = 1024 * 1024
PUBLIC_TIMEOUT = 120.0

PAGE_REC = LiveRecord(VMO_PAGE_SLUG, VMO_PAGE_CODE, "VMO Page (singleton)")
SEC_REC = {k: LiveRecord(SECTION_SLUG, c, f"VMO Section {k}") for k, c in VMO_SECTION_CODES.items()}
SEC_LABEL = {"vision": "Vision", "mission": "Mission", "objectives": "Objectives"}


def _marks(*names):
    def deco(fn):
        for n in reversed(names):
            fn = getattr(pytest.mark, n)(fn)
        return fn
    return deco


COMMON = _marks("control_panel", "about", "pbi_129395")
GROUP = pytest.mark.xdist_group("vmo_129395")


# =============================================================================
# small utilities
# =============================================================================
def _attach(name: str, data) -> None:
    try:
        allure.attach(str(data), name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:  # noqa: BLE001 -- reporting never masks a result
        pass


def _wait(check, timeout: float, message: str) -> bool:
    try:
        wait_until(check, timeout=timeout, poll=3.0, message=message)
        return True
    except WaitTimeoutError:
        return False


def _norm(v) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def _norm_html(v) -> str:
    return re.sub(r">\s+<", "><", _norm(v))


def _fixture(name: str, maker, size: int) -> str:
    folder = Path(tempfile.gettempdir()) / "qc_vmo_129395"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    if not path.exists() or path.stat().st_size != size:
        path.write_bytes(maker(size))
    return str(path)


def _form(page, kind: str, role: str = ROLE_EDITOR):
    form = (VmoPageForm if kind == "page" else VmoSectionForm)(page)
    form.sign_in(role)
    return form


def _code(kind: str) -> str:
    return VMO_PAGE_CODE if kind == "page" else VMO_SECTION_CODES[kind]


def _rec(kind: str) -> LiveRecord:
    return PAGE_REC if kind == "page" else SEC_REC[kind]


def _label(form, key: str, loc: str) -> str:
    spec = form.spec(key)
    return f"{spec.label} ({loc.upper()})" if spec.bilingual else spec.label


def _get(form, key: str, loc: str = EN) -> str:
    kind = form.spec(key).kind
    if kind == "rich":
        return form.rich_html(loc)
    if kind == "file":
        return form.current_file_name(form.spec(key).label)
    return form.value(key, loc)


def _put(form, key: str, loc: str, value) -> None:
    kind = form.spec(key).kind
    if kind == "rich":
        form.set_rich_html(str(value), loc)
    elif kind == "checkbox":
        form.set_flag(key, str(value) == "True")
    else:
        form.fill(key, str(value), loc)


# =============================================================================
# write / restore helpers (every write logged BEFORE its click)
# =============================================================================
def _publish_changes(form, kind: str, tc: str, changes: dict, note: str):
    """Open the record, apply `changes` {(key, loc): value}, click Publish.
    Returns the controls still flagged invalid right after the click."""
    form.open_record(_code(kind))
    for (key, loc), value in changes.items():
        log_live_write(_rec(kind), _label(form, key, loc), value, tc, action="publish", note=note)
    for (key, loc), value in changes.items():
        _put(form, key, loc, value)
    return form.publish_click()


def _open_list(form):
    def _go():
        form.open_entries_list(locale=EN)
        return form
    return _go


def _ensure_published(form, kind: str, tc: str) -> str:
    code = _code(kind)
    status = list_status(_open_list(form), code)
    if status != STATUS_PUBLISHED:
        log_live_write(_rec(kind), "<workflow>", STATUS_PUBLISHED, tc, action="publish",
                       note=f"leave the real record Published (was {status!r})")

        def _submit_draft():
            form.open_record(code)
            form.publish_click()

        drive_to_published(_open_list(form), code, _submit_draft)
        status = list_status(_open_list(form), code)
    return status


@contextmanager
def _restoring(form, kind: str, tc: str, keys):
    """Reads `keys` [(key, loc)] before the test; in `finally` writes back any
    that changed (one Publish, logged) and leaves the record Published. A
    restore problem is attached, never masks the test's own result."""
    form.open_record(_code(kind))
    snap = {k: _get(form, *k) for k in keys}
    _attach(f"values before the test ({_code(kind)})", snap)
    try:
        yield snap
    finally:
        problem = ""
        try:
            form.open_record(_code(kind))
            current = {k: _get(form, *k) for k in keys}
            diff = {}
            for k, before in snap.items():
                kind_k = form.spec(k[0]).kind
                if kind_k == "file":
                    continue  # files are restored by the image helpers
                same = (_norm_html(current[k]) == _norm_html(before)) if kind_k == "rich" else (
                    _norm(current[k]) == _norm(before))
                if not same:
                    diff[k] = before
            if diff:
                _publish_changes(form, kind, tc, diff, note="restore the value read before the test")
            _attach("restore", {"rewritten": {str(k): v for k, v in diff.items()},
                                "end status": _ensure_published(form, kind, tc)})
        except Exception as exc:  # noqa: BLE001
            problem = repr(exc)
            _attach(f"RESTORE PROBLEM -- check {_code(kind)} by hand", problem)


def _restore_file(form, kind: str, tc: str, key: str, original: str) -> None:
    label = form.spec(key).label
    try:
        form.open_record(_code(kind))
        if form.current_file_name(label) == original:
            return
        if not original:
            # The record held NO file before the test (Hero Image, read live
            # 2026-10-14): the restore is removing the test file again.
            log_live_write(_rec(kind), label, "", tc, action="remove-file",
                           note="the record had no file before the test")
            form.remove_current_file(label)
            form.publish_click()
            form.open_record(_code(kind))
            _attach("file restore", {"wanted": "(none)", "now": form.current_file_name(label)})
            return
        log_live_write(_rec(kind), label, original, tc, action="upload",
                       note="restore the file the record held before the test")
        try:
            form.select_library_file(label, original)
        except Exception:  # noqa: BLE001 -- fall back to the root-listing picker
            form.open_record(_code(kind))
            form.select_existing_file(label, original)
        form.publish_click()
        form.open_record(_code(kind))
        _attach("file restore", {"wanted": original, "now": form.current_file_name(label)})
    except Exception as exc:  # noqa: BLE001
        _attach(f"FILE RESTORE PROBLEM -- re-select {original!r} on {_code(kind)} by hand", repr(exc))


# =============================================================================
# public page (fresh logged-out context)
# =============================================================================
@contextmanager
def _visitor(browser):
    ctx = new_context(browser, use_auth_state=False)
    try:
        vp = VmoPage(ctx.new_page())
        vp.dialogs = []
        vp.page.on("dialog", lambda d: (vp.dialogs.append(d.message), d.dismiss()))
        yield vp
    finally:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


def _public(vp: VmoPage, read, ok, locale: str = EN, timeout: float = PUBLIC_TIMEOUT):
    """Reloads the public page (cache-busted) until ok(read(vp)); returns the
    last value read."""
    seen = {"v": None}

    def _poll() -> bool:
        try:
            vp.open(web_url(VMO_PATH, locale=locale) + f"?qcnc={time.time_ns()}")
            seen["v"] = read(vp)
        except Exception as exc:  # noqa: BLE001 -- not rendered
            seen["v"] = f"<not rendered: {type(exc).__name__}>"
        return bool(ok(seen["v"]))

    _wait(_poll, timeout, "public VMO page never matched")
    return seen["v"]


def _numbers(vp: VmoPage) -> dict:
    out = {}
    for label in vp.visible_section_labels_in_order():
        try:
            out[label.strip()] = int(re.sub(r"\D", "", vp.section_number(label.strip())) or 0)
        except Exception:  # noqa: BLE001
            out[label.strip()] = None
    return out


# =============================================================================
# case helpers
# =============================================================================
def _valid_value(page, tc: str, kind: str, key: str, loc: str, value: str) -> None:
    form = _form(page, kind)
    with _restoring(form, kind, tc, [(key, loc)]) as snap:
        if _norm(snap[(key, loc)]) == _norm(value):
            with allure.step("The field already holds the case's value: save an interim value first"):
                _publish_changes(form, kind, tc, {(key, loc): f"QCTEST-{tc} interim"},
                                 note="interim value so the case's save is a real change")
        with allure.step(f"Enter {value!r} in {_label(form, key, loc)} and click Publish"):
            blocked = _publish_changes(form, kind, tc, {(key, loc): value}, note="the case's value")
        with allure.step("Reload the record"):
            form.open_record(_code(kind))
            stored, status = _get(form, key, loc), form.current_status()
        _attach("read back", {"stored": stored, "status": status, "blocked after click": blocked})
        assert _norm(stored) == _norm(value), f"{_label(form, key, loc)} reads {stored!r}, expected {value!r}"
        assert status == STATUS_PUBLISHED, f"record status is {status!r} after the save"


def _empty_attempt(form, kind: str, tc: str, key: str, loc: str, baseline: str) -> dict:
    """Empty one field and click Publish; returns what was shown and stored."""
    label = _label(form, key, loc)
    form.open_record(_code(kind))
    log_live_write(_rec(kind), label, "", tc, action="attempt",
                   note="Publish with the field empty; expected REFUSED")
    if form.spec(key).kind == "rich":
        form.clear_rich_like_a_user(loc)
    else:
        _put(form, key, loc, "")
    blocked = form.publish_click()
    shown = list(dict.fromkeys(getattr(form, "last_click_messages", []) + form.visible_form_messages()))
    bar = form.refusal_text()
    form.open_record(_code(kind))
    stored, status = _get(form, key, loc), form.current_status()
    same = (_norm_html(stored) == _norm_html(baseline)) if form.spec(key).kind == "rich" else (
        _norm(stored) == _norm(baseline))
    return {"field": label, "blocked": blocked, "shown": shown, "bar": bar, "stored": stored[:300],
            "status": status, "kept": same}


def _empty_refused(page, tc: str, kind: str, key: str, loc: str) -> None:
    form = _form(page, kind)
    with _restoring(form, kind, tc, [(key, loc)]) as snap:
        baseline = snap[(key, loc)]
        assert _norm(re.sub(r"<[^>]+>", "", baseline)), f"precondition: {key} ({loc}) is empty on the live record"
        with allure.step(f"Clear {_label(form, key, loc)} and click Publish; reload"):
            out = _empty_attempt(form, kind, tc, key, loc, baseline)
        _attach("outcome (wording recorded, not asserted)", out)
        assert out["kept"], (f"FINDING: Publish with an empty {out['field']} was ACCEPTED -- the stored value "
                             f"is now {out['stored']!r} (the previous value is put back in teardown)")
        assert out["status"] == STATUS_PUBLISHED, f"record status moved to {out['status']!r}"
        assert out["blocked"] or out["shown"] or out["bar"], "nothing was saved, but no validation message showed"


def _image_valid(page, tc: str, kind: str, key: str, path: str, tag: str) -> None:
    form = _form(page, kind)
    label = form.spec(key).label
    copy = DisposableObjectAdminPage.disposable_copy(path, tag)
    form.open_record(_code(kind))
    original = form.current_file_name(label)
    _attach("file before the test", original)
    try:
        with allure.step(f"Upload {Path(copy).name} ({Path(path).stat().st_size // 1024} KB) as {label}; Publish"):
            form.open_record(_code(kind))
            log_live_write(_rec(kind), label, Path(copy).name, tc, action="upload",
                           note="the case's valid image (the previous file is re-selected after the test)")
            form.upload_file(label, copy)
            preview = form.uploaded_filename(label)
            form.publish_click()
        with allure.step("Reload the record"):
            form.open_record(_code(kind))
            stored, status = form.current_file_name(label), form.current_status()
        _attach("read back", {"selected": preview, "stored": stored, "status": status})
        assert Path(copy).stem.lower() in stored.lower(), f"{label} reads {stored!r} after reload, not {Path(copy).name}"
        assert status == STATUS_PUBLISHED, f"record status is {status!r}"
    finally:
        _restore_file(form, kind, tc, key, original)
        _ensure_published(form, kind, tc)


def _injection(page, browser, tc: str, kind: str, key: str, value: str, public_read) -> None:
    form = _form(page, kind)
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    with _restoring(form, kind, tc, [(key, EN)]):
        with allure.step(f"Enter {value!r} in {_label(form, key, EN)} and click Publish"):
            blocked = _publish_changes(form, kind, tc, {(key, EN): value}, note="injection-style test string")
        with allure.step("Reopen the record in the CMS"):
            form.open_record(_code(kind))
            stored = _get(form, key, EN)
        with allure.step("Public page (logged out): the text renders as text, no script runs"), _visitor(browser) as vp:
            seen = _public(vp, public_read, lambda v: isinstance(v, str) and "QCTEST" in v)
            pub_dialogs = list(vp.dialogs)
        _attach("outcome", {"stored": stored, "blocked": blocked, "public text": seen,
                            "cms dialogs": dialogs, "public dialogs": pub_dialogs})
        assert not dialogs and not pub_dialogs, f"a script ran: CMS {dialogs}, public {pub_dialogs}"
        # The CMS may store the literal or strip the tags; either is safe. Tags
        # SHOWN AS TEXT on the site would be a (Low) bug -- PBI running rules,
        # rule 18 -- so the public text must not show raw markup.
        assert "QCTEST" in str(stored), f"the value was not saved: {stored!r}"
        assert not re.search(r"<\s*(script|img)\b", str(seen), re.I), f"raw HTML shown as text publicly: {seen!r}"


def _set_active_and_publish(page, tc: str, sections: dict) -> VmoSectionForm:
    """{section: bool} -> one Publish per section."""
    form = _form(page, "vision")
    for sec, active in sections.items():
        _publish_changes(form, sec, tc, {("active", EN): str(active)},
                         note=f"Active Status = {active} for the case")
    return form


@contextmanager
def _active_restored(page, tc: str, sections):
    form = _form(page, "vision")
    before = {}
    for sec in sections:
        form.open_record(_code(sec))
        before[sec] = str(form.flag("active"))
    _attach("Active Status before the test", before)
    try:
        yield before
    finally:
        for sec in sections:
            try:
                form.open_record(_code(sec))
                if str(form.flag("active")) != before[sec]:
                    _publish_changes(form, sec, tc, {("active", EN): before[sec]},
                                     note="restore Active Status read before the test")
                _ensure_published(form, sec, tc)
            except Exception as exc:  # noqa: BLE001
                _attach(f"RESTORE PROBLEM -- set Active Status of {_code(sec)} back to {before[sec]} by hand",
                        repr(exc))


# =============================================================================
# P1 -- access control
# =============================================================================
@allure.feature("VMO -- access")
@allure.title("Unauthenticated user opening the CMS management screen is denied (ADO-136166)")
@COMMON
@GROUP
@pytest.mark.auth
@pytest.mark.tc_136166
def test_136166_unauthenticated_management_screen_denied(browser):
    ctx = new_context(browser, use_auth_state=False)
    try:
        pg = ctx.new_page()
        form = VmoPageForm(pg)
        with allure.step("Logged out: open the CMS management screen URL directly"):
            pg.goto(form.manage_url(), wait_until="domcontentloaded")
            pg.wait_for_load_state("networkidle", timeout=30000)
        out = {"url": pg.url, "password_inputs": pg.locator('input[type="password"]').count(),
               "publish_controls": pg.locator(form.PUBLISH_SUBMIT).count(),
               "page_title_field": pg.get_by_role("textbox", name=form.label_pattern("Page Title")).count()}
        _attach("logged-out result", out)
        pg.screenshot(path="reports/vmo-136166-anon.png")
    finally:
        ctx.close()
    assert out["publish_controls"] == 0 and out["page_title_field"] == 0, f"CMS form rendered logged out: {out}"
    assert out["password_inputs"] > 0 or "login" in out["url"].lower(), f"no login screen shown: {out}"


@allure.feature("VMO -- access")
@allure.title("Forced browsing to the protected edit URL redirects to login (ADO-136173)")
@COMMON
@GROUP
@pytest.mark.auth
@pytest.mark.tc_136173
def test_136173_forced_browsing_edit_url_redirects_to_login(browser):
    ctx = new_context(browser, use_auth_state=False)
    try:
        pg = ctx.new_page()
        form = VmoPageForm(pg)
        edit_url = form._manage_url(edit_entry=VMO_PAGE_CODE)
        with allure.step(f"Fresh session (no CMS cookie): paste {edit_url}"):
            pg.goto(edit_url, wait_until="domcontentloaded")
            pg.wait_for_load_state("networkidle", timeout=30000)
        out = {"url": pg.url, "password_inputs": pg.locator('input[type="password"]').count(),
               "publish_controls": pg.locator(form.PUBLISH_SUBMIT).count(),
               "page_title_field": pg.get_by_role("textbox", name=form.label_pattern("Page Title")).count()}
        _attach("logged-out result", out)
    finally:
        ctx.close()
    assert out["publish_controls"] == 0 and out["page_title_field"] == 0, f"edit form rendered logged out: {out}"
    assert out["password_inputs"] > 0 or "login" in out["url"].lower(), f"not redirected to login: {out}"


@allure.feature("VMO -- access")
@allure.title("Site Content Author attempting to Publish directly is denied (ADO-136171)")
@COMMON
@GROUP
@pytest.mark.auth
@pytest.mark.tc_136171
def test_136171_author_cannot_publish_directly(page):
    form = _form(page, "page", ROLE_AUTHOR)
    with allure.step("As Site Content Author open the page record"):
        form.open_record(VMO_PAGE_CODE)
        note, controls, status = form.access_denied_note(), form.submit_controls_enabled(), form.current_status()
    _attach("author view", {"access denied note": note, "submit controls": controls, "status": status})
    publish_enabled = [k for k, on in controls.items() if on and k.strip().lower() in ("publish", "نشر")]
    assert not publish_enabled, f"Author is offered an enabled Publish control: {controls}"
    assert status == STATUS_PUBLISHED, f"record status is {status!r}"


@allure.feature("VMO -- validation")
@allure.title("Publish isn't available when the mandatory Page Title (EN) is missing (ADO-136188)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136188
def test_136188_publish_blocked_when_page_title_en_missing(page):
    _empty_refused(page, "136188", "page", "page_title", EN)


# =============================================================================
# P2 -- page record: access + lifecycle
# =============================================================================
@allure.feature("VMO -- access")
@allure.title("Site Content Editor opens the VMO page record with all fields editable (ADO-136167)")
@COMMON
@GROUP
@pytest.mark.auth
@pytest.mark.tc_136167
def test_136167_editor_opens_page_record(page):
    form = _form(page, "page")
    form.open_record(VMO_PAGE_CODE)
    labels = form.form_field_labels()
    controls = form.submit_controls_enabled()
    need = ["Page Title", "Hero Image", "Intro Heading", "Intro Description"]
    missing = [n for n in need if not any(l.startswith(n) for l in labels)]
    sections = _form(page, "vision")
    sections.open_entries_list(locale=EN)
    rows = {c: sections.row_status_text_by_code(c) for c in VMO_SECTION_CODES.values()}
    _attach("editor view", {"labels": labels, "controls": controls, "section rows": rows,
                            "denied": form.access_denied_note()})
    assert not missing, f"page record fields missing: {missing}"
    assert any(on for on in controls.values()), f"no enabled submit control for the Editor: {controls}"
    assert all(rows.values()), f"a section row is missing: {rows}"


@allure.feature("VMO -- lifecycle")
@allure.title("Site Content Editor can Publish the page (ADO-136168)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136168
def test_136168_editor_can_publish_page(page):
    form = _form(page, "page")
    try:
        form.open_entries_list(locale=EN)
        before = form.history_entries(VMO_PAGE_CODE)
    except Exception as exc:  # noqa: BLE001 -- evidence only
        before = [repr(exc)]
    with allure.step("Open the record and click Publish"):
        form.open_record(VMO_PAGE_CODE)
        log_live_write(PAGE_REC, "<workflow>", STATUS_PUBLISHED, "136168", action="publish",
                       note="Publish with the record's current values")
        blocked = form.publish_click()
        shown = list(dict.fromkeys(getattr(form, "last_click_messages", []) + form.visible_form_messages()))
    status = list_status(_open_list(form), VMO_PAGE_CODE)
    try:
        form.open_entries_list(locale=EN)
        after = form.history_entries(VMO_PAGE_CODE)
    except Exception as exc:  # noqa: BLE001 -- evidence only
        after = [repr(exc)]
    _attach("outcome", {"blocked": blocked, "messages (toast not asserted)": shown, "status": status,
                        "history before": before[:3], "history after": after[:3]})
    assert not blocked, f"Publish was blocked: {blocked}"
    assert status == STATUS_PUBLISHED, f"record status is {status!r} after Publish"


@allure.feature("VMO -- lifecycle")
@allure.title("Site Content Editor can Unpublish the page; it leaves the public site (ADO-136169)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136169
def test_136169_editor_can_unpublish_page(page, browser):
    form = _form(page, "page")
    try:
        with allure.step("Unpublish the Published page record (row action)"):
            form.open_entries_list(locale=EN)
            assert form.row_status_text_by_code(VMO_PAGE_CODE) == STATUS_PUBLISHED, "precondition: not Published"
            log_live_write(PAGE_REC, "<workflow>", STATUS_UNPUBLISHED, "136169", action="unpublish",
                           note="the case's Unpublish (re-published in finally)")
            form.unpublish_entry(VMO_PAGE_CODE, comment="QCTEST-136169")
            status = list_status(_open_list(form), VMO_PAGE_CODE)
        with allure.step("Public page (logged out) no longer shows the page content"), _visitor(browser) as vp:
            intro = _public(vp, lambda v: v.intro_heading_text() if v.is_intro_visible() else "",
                            lambda v: not (isinstance(v, str) and v.strip() and not v.startswith("<not")))
        _attach("outcome", {"status": status, "public intro after unpublish": intro})
        assert status == STATUS_UNPUBLISHED, f"status after Unpublish is {status!r}"
        assert not (isinstance(intro, str) and intro.strip() and not intro.startswith("<not")), (
            f"page still shows content publicly: {intro!r}")
    finally:
        _ensure_published(form, "page", "136169")


@allure.feature("VMO -- access")
@allure.title("Site Content Author can view and update the Intro Description as a draft (ADO-136170)")
@COMMON
@GROUP
@pytest.mark.auth
@pytest.mark.tc_136170
def test_136170_author_updates_intro_description_draft(page):
    form = _form(page, "page", ROLE_AUTHOR)
    form.open_record(VMO_PAGE_CODE)
    note, controls, status = form.access_denied_note(), form.submit_controls_enabled(), form.current_status()
    _attach("author view", {"access denied note": note, "submit controls": controls, "status": status})
    assert not note, (f"Author cannot open the Published page record for editing: {note!r} "
                      "(same root cause as bug #150341: Author can't edit a Published record)")
    editor = _form(page, "page")
    with _restoring(editor, "page", "136170", [("intro_desc", EN)]):
        try:
            form = _form(page, "page", ROLE_AUTHOR)
            form.open_record(VMO_PAGE_CODE)
            value = "<p>QCTEST-136170 Author draft update</p>"
            log_live_write(PAGE_REC, "Intro Description (EN)", value, "136170", action="save-draft",
                           note="Author Save as Draft")
            form.set_rich_html(value, EN)
            form.save_as_draft()
            shown = form.visible_form_messages()
            form.open_record(VMO_PAGE_CODE)
            stored = form.rich_html(EN)
            _attach("outcome", {"messages": shown, "stored": stored, "status": form.current_status()})
            assert "QCTEST-136170" in stored, f"Author's draft update did not persist: {stored!r}"
        finally:
            editor.sign_in(ROLE_EDITOR)  # the restore runs as the Editor


@allure.feature("VMO -- access")
@allure.title("An expired CMS session forces re-authentication; edits are not committed (ADO-136174)")
@COMMON
@GROUP
@pytest.mark.auth
@pytest.mark.tc_136174
def test_136174_expired_session_forces_reauth(page):
    form = _form(page, "page")
    with _restoring(form, "page", "136174", [("intro_heading", EN)]) as snap:
        marker = "QCTEST-136174 unsaved edit"
        with allure.step("Edit Intro Heading (EN), then expire the session (cookies cleared)"):
            form.open_record(VMO_PAGE_CODE)
            _put(form, "intro_heading", EN, marker)
            page.context.clear_cookies()
            log_live_write(PAGE_REC, "Intro Heading (EN)", marker, "136174", action="attempt",
                           note="Publish after the session expired; expected NOT committed")
        with allure.step("Click Publish"):
            try:
                page.locator(form.PUBLISH_SUBMIT).first.click(timeout=15000)
                page.wait_for_load_state("domcontentloaded", timeout=30000)
            except Exception as exc:  # noqa: BLE001 -- evidence
                _attach("click", repr(exc))
            landed = {"url": page.url, "password_inputs": page.locator('input[type="password"]').count(),
                      "text": page.locator("body").inner_text()[:600]}
            page.screenshot(path="reports/vmo-136174-after-expiry.png")
        with allure.step("Sign in again and read the stored value"):
            form = _form(page, "page")
            form.open_record(VMO_PAGE_CODE)
            stored = form.value("intro_heading", EN)
        _attach("outcome", {"landed": landed, "stored": stored, "before": snap[("intro_heading", EN)]})
        assert _norm(stored) == _norm(snap[("intro_heading", EN)]), (
            f"the edit was committed without a valid session: {stored!r}")
        reauth = landed["password_inputs"] > 0 or "login" in landed["url"].lower() or re.search(
            r"sign in|log in|session|تسجيل الدخول", landed["text"], re.I)
        assert reauth, f"no re-authentication prompt after the expired-session save: {landed}"


@allure.feature("VMO -- lifecycle")
@allure.title("Editor previews an edit before publishing; the public page is unchanged (ADO-136179)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136179
def test_136179_preview_matches_draft_not_public(page, browser):
    """The form's Preview renders the STORED record, so an edit is previewed
    the way an Editor does it on a Published record: "Unpublish to edit as
    draft", change Intro Heading (EN), Save as Draft, open the row's Preview.
    The case allows the public page to show "the previously published version
    (or nothing)" meanwhile. The value read before is put back and the record
    re-published in teardown."""
    from cms.pages.vision_mission_objectives.vmo_admin_page import VMO_PAGE_TITLE

    form = _form(page, "page")
    marker = "QCTEST-136179 preview"
    with _restoring(form, "page", "136179", [("intro_heading", EN)]):
        with allure.step("Unpublish to edit as draft, change Intro Heading (EN), Save as Draft"):
            form.open_record(VMO_PAGE_CODE)
            log_live_write(PAGE_REC, "<workflow>", STATUS_UNPUBLISHED, "136179", action="unpublish",
                           note="Unpublish to edit as draft (re-published in teardown)")
            form.unpublish_to_edit_as_draft()
            form.open_record(VMO_PAGE_CODE)
            _put(form, "intro_heading", EN, marker)
            log_live_write(PAGE_REC, "Intro Heading (EN)", marker, "136179", action="save-draft")
            form.save_as_draft()
        with allure.step("Open the record's Preview"):
            form.open_entries_list(locale=EN)
            url = form.row_preview_url(VMO_PAGE_TITLE)
            form.open(url)
            preview_text = form.rendered_body_text()
            page.screenshot(path="reports/vmo-136179-preview.png", full_page=True)
        with _visitor(browser) as vp:
            public = _public(vp, lambda v: v.intro_heading_text() if v.is_intro_visible() else "",
                             lambda v: isinstance(v, str), timeout=60)
        _attach("outcome", {"preview url": url, "preview shows the draft": marker in preview_text,
                            "public intro heading": public})
        assert marker in preview_text, "the Preview did not render the draft Intro Heading"
        assert marker not in str(public), f"the draft is public: {public!r}"


# =============================================================================
# P2 -- page record fields
# =============================================================================
@allure.feature("VMO -- page fields")
@allure.title("Valid Page Title (EN) is saved and persists after reload (ADO-136190)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136190
def test_136190_page_title_en_valid_saved(page):
    _valid_value(page, "136190", "page", "page_title", EN, "Vision · Mission · Objectives")


@allure.feature("VMO -- page fields")
@allure.title("Page Title (EN) cannot be saved empty (ADO-136191)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136191
def test_136191_page_title_en_empty_rejected(page):
    _empty_refused(page, "136191", "page", "page_title", EN)


@allure.feature("VMO -- page fields")
@allure.title("Page Title (EN) safely handles injection-style characters (ADO-136193)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136193
def test_136193_page_title_en_injection_safe(page, browser):
    _injection(page, browser, "136193", "page", "page_title",
               "<script>alert('QCTEST-136193')</script> QCTEST Vision & Mission — 2030",
               lambda v: v.hero_title_text())


@allure.feature("VMO -- page fields")
@allure.title("Page Title (AR) accepts a valid value and persists (ADO-136194)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136194
def test_136194_page_title_ar_valid_saved(page):
    _valid_value(page, "136194", "page", "page_title", AR, "الرؤية والرسالة والأهداف")


@allure.feature("VMO -- page fields")
@allure.title("Page Title (AR) cannot be saved empty (ADO-136195)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136195
def test_136195_page_title_ar_empty_rejected(page):
    _empty_refused(page, "136195", "page", "page_title", AR)


@allure.feature("VMO -- page fields")
@allure.title("Hero Banner (EN) accepts a valid JPG under 2 MB and persists (ADO-136197)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136197
def test_136197_hero_jpg_valid_saved(page):
    _image_valid(page, "136197", "page", "hero", _fixture("hero-en.jpg", make_jpg, int(1.2 * ONE_MB)),
                 "136197-hero-en")


@allure.feature("VMO -- page fields")
@allure.title("Hero Banner (AR) accepts a valid PNG under 2 MB and persists (ADO-136200)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136200
def test_136200_hero_png_valid_saved(page):
    # The form has ONE Hero Image (no AR twin): the AR case's PNG goes there.
    _image_valid(page, "136200", "page", "hero", _fixture("hero-ar.png", make_png, 900 * 1024),
                 "136200-hero-ar")


@allure.feature("VMO -- page fields")
@allure.title("Intro Heading (EN) accepts a valid value and persists (ADO-136202)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136202
def test_136202_intro_heading_en_valid_saved(page):
    _valid_value(page, "136202", "page", "intro_heading", EN, "Who We Are")


@allure.feature("VMO -- page fields")
@allure.title("Intro Heading (EN) cannot be saved empty (ADO-136203)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136203
def test_136203_intro_heading_en_empty_rejected(page):
    _empty_refused(page, "136203", "page", "intro_heading", EN)


@allure.feature("VMO -- page fields")
@allure.title("Intro Heading (AR) accepts a valid value and persists (ADO-136205)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136205
def test_136205_intro_heading_ar_valid_saved(page):
    _valid_value(page, "136205", "page", "intro_heading", AR, "من نحن")


@allure.feature("VMO -- page fields")
@allure.title("Intro Heading (AR) cannot be saved empty (ADO-136206)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136206
def test_136206_intro_heading_ar_empty_rejected(page):
    _empty_refused(page, "136206", "page", "intro_heading", AR)


@allure.feature("VMO -- page fields")
@allure.title("Publish is blocked when the Hero Banner is missing and all else is valid (ADO-136214)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136214
def test_136214_publish_blocked_when_hero_missing(page):
    form = _form(page, "page")
    label = form.spec("hero").label
    form.open_record(VMO_PAGE_CODE)
    original = form.current_file_name(label)
    assert original, "precondition: the page record holds no Hero Image"
    try:
        with allure.step(f"Remove {label} ('Undo remove' pending) and click Publish"):
            form.open_record(VMO_PAGE_CODE)
            form.remove_current_file(label)
            pending = form.file_removal_pending(label)
            log_live_write(PAGE_REC, label, "", "136214", action="attempt",
                           note=f"Publish with {label} removed (was {original!r}); expected REFUSED")
            blocked = form.publish_click()
            shown = list(dict.fromkeys(getattr(form, "last_click_messages", []) + form.visible_form_messages()))
        with allure.step("Reopen: the image is still set"):
            form.open_record(VMO_PAGE_CODE)
            stored, status = form.current_file_name(label), form.current_status()
        _attach("outcome", {"pending": pending, "blocked": blocked, "shown": shown, "stored": stored,
                            "status": status, "original": original})
        assert pending, "precondition: Remove file did not register"
        assert stored == original, (f"FINDING: Publish with no Hero Image was ACCEPTED (now {stored!r}); "
                                    "the previous file is re-selected in teardown")
        assert status == STATUS_PUBLISHED, f"record status moved to {status!r}"
    finally:
        _restore_file(form, "page", "136214", "hero", original)
        _ensure_published(form, "page", "136214")


@allure.feature("VMO -- lifecycle")
@allure.title("A network drop during Publish never leaves a partial state (ADO-136348)")
@COMMON
@GROUP
@pytest.mark.edge
@pytest.mark.tc_136348
def test_136348_network_drop_during_publish(page):
    form = _form(page, "page")
    with _restoring(form, "page", "136348", [("intro_heading", EN)]) as snap:
        marker = "QCTEST-136348 network drop"
        form.open_record(VMO_PAGE_CODE)
        _put(form, "intro_heading", EN, marker)
        log_live_write(PAGE_REC, "Intro Heading (EN)", marker, "136348", action="attempt",
                       note="Publish while the browser is offline")
        failed = []
        page.on("requestfailed", lambda r: failed.append(r.url))
        page.context.set_offline(True)
        try:
            try:
                page.locator(form.PUBLISH_SUBMIT).first.click(timeout=15000)
            except Exception as exc:  # noqa: BLE001
                _attach("click while offline", repr(exc))
            _wait(lambda: bool(failed), 20, "no request failed while offline")
        finally:
            page.context.set_offline(False)
        form.open_record(VMO_PAGE_CODE)
        stored, status = form.value("intro_heading", EN), form.current_status()
        _attach("outcome", {"failed requests": failed[:5], "stored": stored, "status": status,
                            "before": snap[("intro_heading", EN)]})
        assert status == STATUS_PUBLISHED, f"record left in {status!r} after the interrupted Publish"
        assert _norm(stored) in (_norm(snap[("intro_heading", EN)]), _norm(marker)), (
            f"partial/corrupted value stored: {stored!r}")


@allure.feature("VMO -- lifecycle")
@allure.title("Unpublishing the page leaves the Main Menu link with a graceful fallback (ADO-136350)")
@COMMON
@GROUP
@pytest.mark.edge
@pytest.mark.tc_136350
def test_136350_unpublished_page_menu_link_graceful(page, browser):
    form = _form(page, "page")
    try:
        form.open_entries_list(locale=EN)
        assert form.row_status_text_by_code(VMO_PAGE_CODE) == STATUS_PUBLISHED, "precondition: not Published"
        log_live_write(PAGE_REC, "<workflow>", STATUS_UNPUBLISHED, "136350", action="unpublish",
                       note="the case's Unpublish (re-published in finally)")
        form.unpublish_entry(VMO_PAGE_CODE, comment="QCTEST-136350")
        status = list_status(_open_list(form), VMO_PAGE_CODE)
        with _visitor(browser) as vp:
            pg = vp.page
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            vp.open(web_url("/", locale=EN) + f"?qcnc={time.time_ns()}")
            link = pg.locator('a[href*="vision-mission-objectives"]').first
            present = link.count() > 0
            resp_status = None
            if present:
                href = link.get_attribute("href")
                resp = pg.goto(href if href.startswith("http") else web_url(href), wait_until="domcontentloaded")
                resp_status = resp.status if resp else None
            body = pg.locator("body").inner_text()[:800]
            pg.screenshot(path="reports/vmo-136350-after-unpublish.png")
        _attach("outcome", {"status": status, "menu link present": present, "http": resp_status,
                            "page errors": errors, "body": body})
        assert status == STATUS_UNPUBLISHED, f"status after Unpublish is {status!r}"
        assert present, "the Main Menu link to the page disappeared"
        assert resp_status is not None and resp_status < 500, f"menu link leads to a server error: {resp_status}"
        assert body.strip(), "menu link leads to a blank page"
    finally:
        _ensure_published(form, "page", "136350")


# =============================================================================
# P2 -- section fields (Vision unless stated)
# =============================================================================
@allure.feature("VMO -- section fields")
@allure.title("Vision Section Label (EN) accepts a valid value and persists (ADO-136269)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136269
def test_136269_vision_label_en_valid(page):
    _valid_value(page, "136269", "vision", "label", EN, "Vision")


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Label (EN) cannot be saved empty (ADO-136272)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136272
def test_136272_vision_label_en_empty(page):
    _empty_refused(page, "136272", "vision", "label", EN)


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Label (AR) accepts a valid value and persists (ADO-136275)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136275
def test_136275_vision_label_ar_valid(page):
    _valid_value(page, "136275", "vision", "label", AR, "الرؤية")


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Label (AR) cannot be saved empty (ADO-136278)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136278
def test_136278_vision_label_ar_empty(page):
    _empty_refused(page, "136278", "vision", "label", AR)


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Headline (EN) accepts a valid value and persists (ADO-136280)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136280
def test_136280_vision_headline_en_valid(page):
    _valid_value(page, "136280", "vision", "headline", EN, "INTERNATIONAL LEADERSHIP")


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Headline (EN) cannot be saved empty (ADO-136282)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136282
def test_136282_vision_headline_en_empty(page):
    _empty_refused(page, "136282", "vision", "headline", EN)


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Headline (AR) accepts a valid value and persists (ADO-136285)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136285
def test_136285_vision_headline_ar_valid(page):
    _valid_value(page, "136285", "vision", "headline", AR, "الريادة الدولية")


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Headline (AR) cannot be saved empty (ADO-136286)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136286
def test_136286_vision_headline_ar_empty(page):
    _empty_refused(page, "136286", "vision", "headline", AR)


_BULLETS_EN = ("<ul><li>QCTEST Leadership</li><li>QCTEST Integrity</li><li>QCTEST Innovation</li>"
               "<li>QCTEST Partnership</li><li>QCTEST Excellence</li></ul>")
_BULLETS_AR = ("<ul><li>QCTEST الريادة</li><li>QCTEST النزاهة</li><li>QCTEST الابتكار</li>"
               "<li>QCTEST الشراكة</li><li>QCTEST التميز</li></ul>")


def _bullets_saved(page, tc: str, loc: str, html: str) -> None:
    form = _form(page, "vision")
    with _restoring(form, "vision", tc, [("body", loc)]):
        with allure.step(f"Enter a 5-item bullet list in Body Content ({loc.upper()}) and click Publish"):
            blocked = _publish_changes(form, "vision", tc, {("body", loc): html}, note="5-item bullet list")
        with allure.step("Reload the record"):
            form.open_record(VMO_SECTION_CODES["vision"])
            stored = form.rich_html(loc)
        _attach("read back", {"stored": stored, "blocked": blocked})
        assert stored.count("<li") == 5 and "<ul" in stored, f"bullet list not stored intact: {stored!r}"


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Content (EN) accepts a bulleted list and persists (ADO-136297)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136297
def test_136297_vision_body_en_bullets(page):
    _bullets_saved(page, "136297", EN, _BULLETS_EN)


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Content (EN) cannot be saved empty (ADO-136299)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136299
def test_136299_vision_body_en_empty(page):
    _empty_refused(page, "136299", "vision", "body", EN)


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Content (AR) accepts a bulleted list and persists (ADO-136305)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136305
def test_136305_vision_body_ar_bullets(page):
    _bullets_saved(page, "136305", AR, _BULLETS_AR)


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Content (AR) cannot be saved empty (ADO-136306)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136306
def test_136306_vision_body_ar_empty(page):
    _empty_refused(page, "136306", "vision", "body", AR)


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Image accepts a valid JPG under 2 MB and persists (ADO-136309)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136309
def test_136309_vision_image_jpg_valid(page):
    _image_valid(page, "136309", "vision", "image", _fixture("vision-section.jpg", make_jpg, int(1.5 * ONE_MB)),
                 "136309-vision")


def _order_saved(page, browser, tc: str, sec: str, value: str, position: int) -> None:
    form = _form(page, sec)
    with _restoring(form, sec, tc, [("order", EN)]) as snap:
        with allure.step(f"Enter {value} in Display Order and click Publish"):
            blocked = _publish_changes(form, sec, tc, {("order", EN): value}, note="the case's Display Order")
        form.open_record(_code(sec))
        stored = form.value("order", EN)
        with _visitor(browser) as vp:
            order = _public(vp, lambda v: v.visible_section_labels_in_order(),
                            lambda v: isinstance(v, list) and len(v) > position - 1
                            and v[position - 1].strip() == SEC_LABEL[sec])
        _attach("outcome", {"before": snap[("order", EN)], "stored": stored, "blocked": blocked,
                            "public order": order})
        assert stored == value, f"Display Order reads {stored!r}, expected {value}"
        assert isinstance(order, list) and len(order) >= position and order[position - 1].strip() == SEC_LABEL[sec], (
            f"{SEC_LABEL[sec]} is not at position {position} publicly: {order}")


@allure.feature("VMO -- section fields")
@allure.title("Vision Display Order accepts 1, persists, and Vision renders first (ADO-136318)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136318
def test_136318_vision_display_order_1(page, browser):
    _order_saved(page, browser, "136318", "vision", "1", 1)


@allure.feature("VMO -- section fields")
@allure.title("Mission Display Order accepts 2 and Mission renders second (ADO-136330)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136330
def test_136330_mission_display_order_2(page, browser):
    # Precondition from the case: Vision = 1 and Objectives = 3. Live they
    # are 100 / 300 (read 2026-10-14), so they are set first and put back.
    vision = _form(page, "vision")
    objectives = _form(page, "objectives")
    with _restoring(vision, "vision", "136330", [("order", EN)]),             _restoring(objectives, "objectives", "136330", [("order", EN)]):
        _publish_changes(vision, "vision", "136330", {("order", EN): "1"}, note="precondition Vision = 1")
        _publish_changes(objectives, "objectives", "136330", {("order", EN): "3"},
                         note="precondition Objectives = 3")
        _order_saved(page, browser, "136330", "mission", "2", 2)


@allure.feature("VMO -- section visibility")
@allure.title("Vision Active = ticked persists and Vision shows publicly (ADO-136323)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136323
def test_136323_vision_active_visible(page, browser):
    with _active_restored(page, "136323", ["vision"]):
        form = _set_active_and_publish(page, "136323", {"vision": True})
        form.open_record(VMO_SECTION_CODES["vision"])
        stored = form.flag("active")
        with _visitor(browser) as vp:
            shown = _public(vp, lambda v: v.is_section_visible("Vision"), lambda v: v is True)
        _attach("outcome", {"active after reload": stored, "public Vision visible": shown})
        assert stored is True, "Active Status did not persist as ticked"
        assert shown is True, "Vision is not shown on the public page"


@allure.feature("VMO -- section visibility")
@allure.title("Vision Active = unticked hides it publicly; still editable in CMS (ADO-136324)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136324
def test_136324_vision_inactive_hidden(page, browser):
    with _active_restored(page, "136324", ["vision"]):
        form = _set_active_and_publish(page, "136324", {"vision": False})
        with _visitor(browser) as vp:
            labels = _public(vp, lambda v: v.visible_section_labels_in_order(),
                             lambda v: isinstance(v, list) and v and "Vision" not in [x.strip() for x in v])
        form.open_record(VMO_SECTION_CODES["vision"])
        stored, editable = form.flag("active"), not form.access_denied_note()
        _attach("outcome", {"public sections": labels, "active after reload": stored, "editable": editable})
        assert isinstance(labels, list) and "Vision" not in [x.strip() for x in labels], (
            f"Vision still shows publicly: {labels}")
        assert stored is False and editable, f"record not editable / Active not unticked: {stored}, {editable}"


@contextmanager
def _orders_preset(page, tc: str, orders: dict):
    """The cases number the sections 1 / 2 / 3; live they are 100 / 200 / 300
    (read 2026-10-14). Sets the OTHER sections' Display Order for the case and
    puts the read values back afterwards."""
    forms = {sec: _form(page, sec) for sec in orders}
    from contextlib import ExitStack
    with ExitStack() as stack:
        for sec, value in orders.items():
            stack.enter_context(_restoring(forms[sec], sec, tc, [("order", EN)]))
            _publish_changes(forms[sec], sec, tc, {("order", EN): value}, note=f"precondition {sec} = {value}")
        yield


def _full_set(page, browser, tc: str, sec: str, order: str) -> None:
    form = _form(page, sec)
    keys = [("headline", EN), ("headline", AR), ("subheading", EN), ("subheading", AR), ("badge", EN),
            ("badge", AR), ("body", EN), ("body", AR), ("order", EN), ("active", EN)]
    values = {
        ("headline", EN): f"QCTEST-{tc} HEADLINE", ("headline", AR): f"QCTEST-{tc} عنوان",
        ("subheading", EN): f"QCTEST-{tc} subheading", ("subheading", AR): f"QCTEST-{tc} عنوان فرعي",
        ("badge", EN): f"QCTEST-{tc} badge", ("badge", AR): f"QCTEST-{tc} شارة",
        ("body", EN): f"<p>QCTEST-{tc} body text</p>", ("body", AR): f"<p>QCTEST-{tc} نص المحتوى</p>",
        ("order", EN): order, ("active", EN): "True",
    }
    with _restoring(form, sec, tc, keys):
        with allure.step(f"Enter a full valid EN+AR set on {SEC_LABEL[sec]} (Display Order {order}, Active) "
                         "and click Publish"):
            blocked = _publish_changes(form, sec, tc, values, note="full valid field set")
        form.open_record(_code(sec))
        stored = {f"{k[0]}:{k[1]}": _get(form, *k) for k in keys}
        with _visitor(browser) as vp:
            pub = _public(vp, lambda v: {"headline": v.section_headline(SEC_LABEL[sec]),
                                         "sub": v.section_subheading(SEC_LABEL[sec]),
                                         "body": v.section_paragraph_text(SEC_LABEL[sec]),
                                         "position": [x.strip() for x in v.visible_section_labels_in_order()]},
                          lambda v: isinstance(v, dict) and f"QCTEST-{tc}".lower() in v["headline"].lower())
        _attach("outcome", {"blocked": blocked, "stored": stored, "public": pub})
        assert not blocked, f"Publish was blocked: {blocked}"
        assert isinstance(pub, dict), f"{SEC_LABEL[sec]} did not render publicly: {pub}"
        assert f"QCTEST-{tc}".lower() in pub["headline"].lower(), f"public headline: {pub['headline']!r}"
        assert f"QCTEST-{tc}" in pub["sub"], f"public subheading: {pub['sub']!r}"
        assert f"QCTEST-{tc}" in pub["body"], f"public body: {pub['body']!r}"
        assert pub["position"].index(SEC_LABEL[sec]) == int(order) - 1, f"public order: {pub['position']}"


@allure.feature("VMO -- section fields")
@allure.title("All Mission fields save and publish as a complete valid set (ADO-136325)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136325
def test_136325_mission_full_valid_set(page, browser):
    with _orders_preset(page, "136325", {"vision": "1", "objectives": "3"}):
        _full_set(page, browser, "136325", "mission", "2")


@allure.feature("VMO -- section fields")
@allure.title("Mission Section Headline (AR) cannot be saved empty (ADO-136326)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136326
def test_136326_mission_headline_ar_empty(page):
    _empty_refused(page, "136326", "mission", "headline", AR)


@allure.feature("VMO -- section fields")
@allure.title("All Objectives fields save and publish as a complete valid set (ADO-136333)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136333
def test_136333_objectives_full_valid_set(page, browser):
    with _orders_preset(page, "136333", {"vision": "1", "mission": "2"}):
        _full_set(page, browser, "136333", "objectives", "3")


@allure.feature("VMO -- section fields")
@allure.title("Objectives Section Label (EN) cannot be saved empty (ADO-136334)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136334
def test_136334_objectives_label_en_empty(page):
    _empty_refused(page, "136334", "objectives", "label", EN)


@allure.feature("VMO -- section fields")
@allure.title("Objectives Image Badge Label (EN) safely handles injection-style characters (ADO-136338)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136338
def test_136338_objectives_badge_injection_safe(page, browser):
    _injection(page, browser, "136338", "objectives", "badge",
               "<img src=x onerror=alert('QCTEST-136338')> QCTEST Objectives",
               lambda v: v.page.locator(f"{v.section_locator('Objectives')} .qc-vmo-sec-badge").inner_text())


# =============================================================================
# P2 -- renumbering / fallback / repeated validation
# =============================================================================
@allure.feature("VMO -- section visibility")
@allure.title("Deactivating Vision renumbers Mission/Objectives to 01/02 (ADO-136341)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136341
def test_136341_deactivate_vision_renumbers(page, browser):
    with _active_restored(page, "136341", ["vision", "mission", "objectives"]) as before:
        assert all(v == "True" for v in before.values()), f"precondition: not all sections active: {before}"
        _set_active_and_publish(page, "136341", {"vision": False})
        with _visitor(browser) as vp:
            nums = _public(vp, _numbers, lambda v: isinstance(v, dict) and "Vision" not in v and v)
        _attach("public numbering", nums)
        assert nums == {"Mission": 1, "Objectives": 2}, f"public numbering after hiding Vision: {nums}"


@allure.feature("VMO -- section visibility")
@allure.title("Deactivating Mission and Objectives leaves only Vision as 01 (ADO-136342)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136342
def test_136342_deactivate_two_sections(page, browser):
    with _active_restored(page, "136342", ["vision", "mission", "objectives"]) as before:
        assert all(v == "True" for v in before.values()), f"precondition: not all sections active: {before}"
        _set_active_and_publish(page, "136342", {"mission": False, "objectives": False})
        with _visitor(browser) as vp:
            nums = _public(vp, _numbers, lambda v: isinstance(v, dict) and list(v) == ["Vision"])
        _attach("public numbering", nums)
        assert nums == {"Vision": 1}, f"public numbering after hiding Mission+Objectives: {nums}"


@allure.feature("VMO -- section visibility")
@allure.title("Reactivating Vision re-inserts it at its Display Order and renumbers (ADO-136343)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136343
def test_136343_reactivate_vision_renumbers(page, browser):
    with _active_restored(page, "136343", ["vision", "mission", "objectives"]) as before:
        assert all(v == "True" for v in before.values()), f"precondition: not all sections active: {before}"
        _set_active_and_publish(page, "136343", {"vision": False})
        with _visitor(browser) as vp:
            first = _public(vp, _numbers, lambda v: isinstance(v, dict) and v.get("Mission") == 1)
        _set_active_and_publish(page, "136343", {"vision": True})
        with _visitor(browser) as vp:
            nums = _public(vp, _numbers, lambda v: isinstance(v, dict) and v.get("Vision") == 1)
        _attach("public numbering", {"after hiding Vision": first, "after reactivating": nums})
        assert first == {"Mission": 1, "Objectives": 2}, f"precondition state not reached: {first}"
        assert nums == {"Vision": 1, "Mission": 2, "Objectives": 3}, f"numbering after reactivation: {nums}"


@allure.feature("VMO -- bilingual")
@allure.title("Missing Arabic Mission content falls back to English without breaking the AR page (ADO-136345)")
@COMMON
@GROUP
@pytest.mark.edge
@pytest.mark.tc_136345
def test_136345_missing_ar_content_falls_back(page, browser):
    form = _form(page, "mission")
    with _restoring(form, "mission", "136345", [("body", AR), ("body", EN)]) as snap:
        with allure.step("Clear Mission Body Content (AR), keep EN, click Publish"):
            form.open_record(VMO_SECTION_CODES["mission"])
            log_live_write(SEC_REC["mission"], "Body Content (AR)", "", "136345", action="publish",
                           note="AR body blank for the fallback case")
            form.clear_rich_like_a_user(AR)
            blocked = form.publish_click()
        form.open_record(VMO_SECTION_CODES["mission"])
        stored_ar = form.rich_html(AR)
        en_text = _norm(re.sub(r"<[^>]+>", " ", snap[("body", EN)]))
        with _visitor(browser) as vp:
            ar = _public(vp, lambda v: {
                "mission_body": v.page.locator(f"{v.section_chain_locator_by_index(1)} .qc-vmo-sec-rich").inner_text(),
                "vision_body": v.page.locator(f"{v.section_chain_locator_by_index(0)} .qc-vmo-sec-rich").inner_text(),
                "labels": v.visible_section_labels_in_order()},
                lambda v: isinstance(v, dict) and _norm(v["mission_body"])[:30] == en_text[:30], locale=AR)
        _attach("outcome", {"blocked": blocked, "stored AR": stored_ar, "EN text": en_text[:200], "AR page": ar})
        # Live 2026-10-14: the CMS stores the EN copy in a blank AR field (the
        # Arabic-twin sync), which IS the fallback the case asks for.
        stored_ar_text = _norm(re.sub(r"<[^>]+>", " ", stored_ar))
        if blocked or (stored_ar_text and stored_ar_text[:30] != en_text[:30]):
            pytest.fail(f"Publish with Mission AR content blank was refused / not applied (blocked {blocked}); "
                        "the fallback could not be observed", pytrace=False)
        assert isinstance(ar, dict), f"AR page did not render: {ar}"
        assert _norm(ar["mission_body"])[:30] == en_text[:30], (
            f"Mission AR body does not fall back to English: {ar['mission_body'][:120]!r}")
        assert _norm(ar["vision_body"]) and not re.fullmatch(r"[\x00-\x7F\s]*", ar["vision_body"]), (
            "Vision's Arabic content is broken on the AR page")


@allure.feature("VMO -- validation")
@allure.title("Empty Section Headline (EN) is refused identically on all three sections (ADO-136349)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136349
def test_136349_empty_headline_same_on_all_sections(page):
    outcomes = {}
    for sec in ("vision", "mission", "objectives"):
        form = _form(page, sec)
        with _restoring(form, sec, "136349", [("headline", EN)]) as snap:
            with allure.step(f"{SEC_LABEL[sec]}: clear Headline (EN) and click Publish"):
                outcomes[sec] = _empty_attempt(form, sec, "136349", "headline", EN, snap[("headline", EN)])
    _attach("outcomes", outcomes)
    kept = {s: o["kept"] for s, o in outcomes.items()}
    assert all(kept.values()), f"FINDING: an empty Headline (EN) was ACCEPTED on: {[s for s, k in kept.items() if not k]}"
    signals = {s: bool(o["blocked"] or o["shown"] or o["bar"]) for s, o in outcomes.items()}
    assert len(set(signals.values())) == 1, f"validation differs between sections: {signals}"


# =============================================================================
# P3 (high/medium importance) -- scripted 2026-10-14. Character-limit cases
# are Not Applicable (no char limits, user decision 2026-10-03) and have no
# test. Rule-17 cases (link format not validated, duplicate Display Order)
# are recorded as Passed without a test -- see the run report.
# =============================================================================
from tools.fixture_factory import make_gif  # noqa: E402


def _image_rejected(page, tc: str, kind: str, key: str, path: str, tag: str) -> None:
    """Unsupported / oversize image: the picker refuses it, or -- if it is
    accepted into the form -- Publish does not store it."""
    form = _form(page, kind)
    label = form.spec(key).label
    copy = DisposableObjectAdminPage.disposable_copy(path, tag)
    form.open_record(_code(kind))
    original = form.current_file_name(label)
    stored = original
    try:
        with allure.step(f"Upload {Path(copy).name} ({Path(path).stat().st_size // 1024} KB) as {label}"):
            form.open_record(_code(kind))
            log_live_write(_rec(kind), label, Path(copy).name, tc, action="attempt",
                           note="file the case expects REFUSED")
            rejected = form.upload_file_expect_rejected(label, copy)
            picker_said = ""
            try:
                picker_said = form.visible_form_messages()
            except Exception:  # noqa: BLE001
                pass
            if not rejected:
                form.publish_click()
        form.open_record(_code(kind))
        stored = form.current_file_name(label)
        _attach("outcome", {"rejected by picker": rejected, "messages": picker_said, "stored": stored,
                            "original": original})
        assert rejected or Path(copy).stem.lower() not in stored.lower(), (
            f"FINDING: {Path(copy).name} was accepted and stored as {label} ({stored!r})")
    finally:
        if stored != original:
            _restore_file(form, kind, tc, key, original)
        _ensure_published(form, kind, tc)


def _optional_empty_saves(page, tc: str, kind: str, key: str, loc: str) -> None:
    form = _form(page, kind)
    with _restoring(form, kind, tc, [(key, loc)]):
        with allure.step(f"Clear the optional {_label(form, key, loc)} and click Publish"):
            form.open_record(_code(kind))
            log_live_write(_rec(kind), _label(form, key, loc), "", tc, action="publish",
                           note="optional field left empty (restored after)")
            if form.spec(key).kind == "rich":
                form.clear_rich_like_a_user(loc)
            else:
                _put(form, key, loc, "")
            blocked = form.publish_click()
        form.open_record(_code(kind))
        stored, status = _get(form, key, loc), form.current_status()
        _attach("outcome", {"blocked": blocked, "stored": stored, "status": status})
        assert not _norm(re.sub(r"<[^>]+>", "", stored)), f"the field was not saved empty: {stored!r}"
        assert status == STATUS_PUBLISHED, f"record status is {status!r}"


def _rich_valid(page, tc: str, kind: str, loc: str, html: str) -> None:
    form = _form(page, kind)
    key = "intro_desc" if kind == "page" else "body"
    with _restoring(form, kind, tc, [(key, loc)]):
        blocked = _publish_changes(form, kind, tc, {(key, loc): html}, note="valid rich text")
        form.open_record(_code(kind))
        stored = form.rich_html(loc)
        _attach("outcome", {"blocked": blocked, "stored": stored})
        assert f"QCTEST-{tc}" in stored and "<strong>" in stored, f"rich text not stored intact: {stored!r}"


def _order_refused(page, tc: str, typed: str) -> None:
    form = _form(page, "vision")
    with _restoring(form, "vision", tc, [("order", EN)]) as snap:
        with allure.step(f"Type {typed!r} into Vision's Display Order and click Publish"):
            form.open_record(VMO_SECTION_CODES["vision"])
            box = page.get_by_role("spinbutton", name=form.label_pattern("Display Order"))
            box.click()
            box.press("Control+A")
            box.press("Delete")
            box.type(typed)
            entered = box.input_value()
            log_live_write(SEC_REC["vision"], "Display Order", typed, tc, action="attempt",
                           note="invalid Display Order; expected REFUSED")
            blocked = form.publish_click()
            shown = list(dict.fromkeys(getattr(form, "last_click_messages", []) + form.visible_form_messages()))
        form.open_record(VMO_SECTION_CODES["vision"])
        stored = form.value("order", EN)
        _attach("outcome", {"typed": typed, "field read": entered, "blocked": blocked, "shown": shown,
                            "stored": stored, "before": snap[("order", EN)]})
        assert stored == snap[("order", EN)], f"FINDING: Display Order {typed!r} was stored as {stored!r}"


@allure.feature("VMO -- page fields")
@allure.title("Hero Banner (EN) rejects an unsupported file format (ADO-136198)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136198
def test_136198_hero_unsupported_format(page):
    _image_rejected(page, "136198", "page", "hero", _fixture("hero.gif", make_gif, 400 * 1024), "136198-hero")


@allure.feature("VMO -- page fields")
@allure.title("Hero Banner (EN) rejects an image over the size limit (3.1 MB) (ADO-136199)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136199
def test_136199_hero_oversize(page):
    _image_rejected(page, "136199", "page", "hero", _fixture("hero-3_1mb.jpg", make_jpg, int(3.1 * ONE_MB)),
                    "136199-hero-big")


@allure.feature("VMO -- page fields")
@allure.title("Hero Banner (AR) rejects an image over the size limit (3.1 MB) (ADO-136201)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136201
def test_136201_hero_ar_oversize(page):
    # ONE Hero Image field serves both languages.
    _image_rejected(page, "136201", "page", "hero", _fixture("hero-ar-3_1mb.png", make_png, int(3.1 * ONE_MB)),
                    "136201-hero-ar-big")


@allure.feature("VMO -- page fields")
@allure.title("Intro Description (EN) accepts valid rich text and persists (ADO-136207)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136207
def test_136207_intro_desc_en_valid(page):
    _rich_valid(page, "136207", "page", EN, "<p>QCTEST-136207 <strong>Qatar Chamber</strong> intro text.</p>")


@allure.feature("VMO -- page fields")
@allure.title("Intro Description (EN) can be left empty and the page still saves (ADO-136210)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136210
def test_136210_intro_desc_en_optional(page):
    _optional_empty_saves(page, "136210", "page", "intro_desc", EN)


@allure.feature("VMO -- page fields")
@allure.title("Intro Description (AR) accepts valid rich text and persists (ADO-136211)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136211
def test_136211_intro_desc_ar_valid(page):
    _rich_valid(page, "136211", "page", AR, "<p>QCTEST-136211 <strong>غرفة قطر</strong> نص تعريفي.</p>")


@allure.feature("VMO -- lifecycle")
@allure.title("Canceling an in-progress page edit discards unsaved changes (ADO-136213)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136213
def test_136213_cancel_discards_unsaved(page):
    form = _form(page, "page")
    form.open_record(VMO_PAGE_CODE)
    before = form.value("intro_heading", EN)
    _put(form, "intro_heading", EN, "QCTEST-136213 unsaved")
    cancel = page.get_by_role("button", name=re.compile(r"^\s*Cancel\s*$", re.I)).or_(
        page.get_by_role("link", name=re.compile(r"^\s*Cancel\s*$", re.I)))
    used = "Cancel control" if cancel.count() else "navigated away (no Cancel control on the form)"
    page.once("dialog", lambda d: d.accept())
    if cancel.count():
        cancel.first.click()
    form.open_record(VMO_PAGE_CODE)
    stored = form.value("intro_heading", EN)
    _attach("outcome", {"how": used, "before": before, "stored": stored})
    assert stored == before, f"the unsaved edit persisted: {stored!r}"


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Subheading (EN) accepts a valid value and persists (ADO-136288)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136288
def test_136288_vision_subheading_en_valid(page):
    _valid_value(page, "136288", "vision", "subheading", EN, "Aligned with Qatar National Vision 2030")


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Subheading (EN) can be left empty (ADO-136292)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136292
def test_136292_vision_subheading_en_optional(page):
    _optional_empty_saves(page, "136292", "vision", "subheading", EN)


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Subheading (AR) accepts a valid value and persists (ADO-136293)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136293
def test_136293_vision_subheading_ar_valid(page):
    _valid_value(page, "136293", "vision", "subheading", AR, "منسجمة مع رؤية قطر الوطنية 2030")


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Image rejects an unsupported file format (ADO-136310)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136310
def test_136310_vision_image_unsupported(page):
    _image_rejected(page, "136310", "vision", "image", _fixture("vision.gif", make_gif, 400 * 1024),
                    "136310-vision")


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Image rejects an image over the size limit (3.1 MB) (ADO-136311)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136311
def test_136311_vision_image_oversize(page):
    _image_rejected(page, "136311", "vision", "image", _fixture("vision-3_1mb.jpg", make_jpg, int(3.1 * ONE_MB)),
                    "136311-vision-big")


@allure.feature("VMO -- section fields")
@allure.title("Vision Section Image can be left empty and the section still saves (ADO-136312)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136312
def test_136312_vision_image_optional(page):
    form = _form(page, "vision")
    label = form.spec("image").label
    form.open_record(VMO_SECTION_CODES["vision"])
    original = form.current_file_name(label)
    try:
        form.remove_current_file(label)
        log_live_write(SEC_REC["vision"], label, "", "136312", action="publish",
                       note="optional image removed (re-selected after)")
        blocked = form.publish_click()
        form.open_record(VMO_SECTION_CODES["vision"])
        stored, status = form.current_file_name(label), form.current_status()
        _attach("outcome", {"blocked": blocked, "stored": stored, "status": status, "original": original})
        assert not stored, f"the section did not save without an image (still {stored!r}; blocked {blocked})"
        assert status == STATUS_PUBLISHED, f"record status is {status!r}"
    finally:
        _restore_file(form, "vision", "136312", "image", original)
        _ensure_published(form, "vision", "136312")


@allure.feature("VMO -- section fields")
@allure.title("Vision Image Badge Label (EN) accepts a valid value and persists (ADO-136313)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136313
def test_136313_vision_badge_en_valid(page):
    _valid_value(page, "136313", "vision", "badge", EN, "Vision")


@allure.feature("VMO -- section fields")
@allure.title("Vision Image Badge Label (EN) can be left empty (ADO-136315)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136315
def test_136315_vision_badge_en_optional(page):
    _optional_empty_saves(page, "136315", "vision", "badge", EN)


@allure.feature("VMO -- section fields")
@allure.title("Vision Image Badge Label (AR) accepts a valid value and persists (ADO-136316)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136316
def test_136316_vision_badge_ar_valid(page):
    _valid_value(page, "136316", "vision", "badge", AR, "الرؤية")


@allure.feature("VMO -- section fields")
@allure.title("Vision Display Order rejects zero (ADO-136320)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136320
def test_136320_vision_order_zero(page):
    _order_refused(page, "136320", "0")


@allure.feature("VMO -- section fields")
@allure.title("Vision Display Order rejects a negative value (ADO-136321)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136321
def test_136321_vision_order_negative(page):
    _order_refused(page, "136321", "-1")


@allure.feature("VMO -- section fields")
@allure.title("Vision Display Order rejects a non-numeric value (ADO-136322)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136322
def test_136322_vision_order_non_numeric(page):
    _order_refused(page, "136322", "abc")


@allure.feature("VMO -- public rendering")
@allure.title("Mission Section Content renders as a single paragraph on the frontend (ADO-136328)")
@COMMON
@GROUP
@pytest.mark.ui
@pytest.mark.tc_136328
def test_136328_mission_single_paragraph(browser):
    with _visitor(browser) as vp:
        out = _public(vp, lambda v: {"bulleted": v.section_body_is_bulleted("Mission"),
                                     "paragraphs": v.page.locator(f"{v.section_locator('Mission')} .qc-vmo-sec-rich p").count(),
                                     "text": v.section_paragraph_text("Mission")[:300]},
                      lambda v: isinstance(v, dict), timeout=60)
    _attach("Mission body", out)
    assert isinstance(out, dict) and not out["bulleted"] and out["text"].strip(), f"Mission body: {out}"
    assert out["paragraphs"] <= 1, f"Mission renders {out['paragraphs']} paragraphs, not one"


@allure.feature("VMO -- section fields")
@allure.title("Mission Section Image rejects an image over the size limit (3.1 MB) (ADO-136329)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136329
def test_136329_mission_image_oversize(page):
    _image_rejected(page, "136329", "mission", "image",
                    _fixture("mission-3_1mb.jpg", make_jpg, int(3.1 * ONE_MB)), "136329-mission-big")


@allure.feature("VMO -- public rendering")
@allure.title("Mission's Section Image renders on the left side (ADO-136332)")
@COMMON
@GROUP
@pytest.mark.ui
@pytest.mark.tc_136332
def test_136332_mission_image_left(browser):
    with _visitor(browser) as vp:
        side = _public(vp, lambda v: v.section_image_side("Mission"), lambda v: v in ("start", "end"), timeout=60)
    _attach("Mission image side (LTR: start = left)", side)
    assert side == "start", f"Mission image side is {side!r}, expected left (start)"


@allure.feature("VMO -- public rendering")
@allure.title("Objectives' Section Content renders the 'Five Pillars' bulleted list (ADO-136337)")
@COMMON
@GROUP
@pytest.mark.ui
@pytest.mark.tc_136337
def test_136337_objectives_bulleted_list(browser):
    with _visitor(browser) as vp:
        out = _public(vp, lambda v: {"headline": v.section_headline("Objectives"),
                                     "bullets": v.section_bullet_texts("Objectives")},
                      lambda v: isinstance(v, dict), timeout=60)
    _attach("Objectives", out)
    assert isinstance(out, dict) and len(out["bullets"]) == 5, f"Objectives bullets: {out}"
    assert "five pillars" in out["headline"].lower(), f"Objectives headline: {out['headline']!r}"


@allure.feature("VMO -- section fields")
@allure.title("Objectives' Section Image rejects an unsupported file format (ADO-136339)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136339
def test_136339_objectives_image_unsupported(page):
    _image_rejected(page, "136339", "objectives", "image", _fixture("objectives.gif", make_gif, 400 * 1024),
                    "136339-objectives")


@allure.feature("VMO -- public rendering")
@allure.title("Objectives' Section Image renders on the right side (ADO-136340)")
@COMMON
@GROUP
@pytest.mark.ui
@pytest.mark.tc_136340
def test_136340_objectives_image_right(browser):
    with _visitor(browser) as vp:
        side = _public(vp, lambda v: v.section_image_side("Objectives"), lambda v: v in ("start", "end"),
                       timeout=60)
    _attach("Objectives image side (LTR: end = right)", side)
    assert side == "end", f"Objectives image side is {side!r}, expected right (end)"


@allure.feature("VMO -- public rendering")
@allure.title("An image embedded inside Section Content renders with the text (ADO-136344)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136344
def test_136344_embedded_image_renders(page, browser):
    with _visitor(browser) as vp:
        src = _public(vp, lambda v: v.section_image_src("Vision"), lambda v: isinstance(v, str) and v, timeout=60)
    assert src and not str(src).startswith("<not"), f"precondition: no Vision image URL to embed ({src!r})"
    absolute = src if src.startswith("http") else web_url(src)
    html = f'<p>QCTEST-136344 text with an image</p><p><img alt="QCTEST-136344" src="{absolute}" /></p>'
    form = _form(page, "vision")
    with _restoring(form, "vision", "136344", [("body", EN)]):
        _publish_changes(form, "vision", "136344", {("body", EN): html}, note="body with an embedded image")
        with _visitor(browser) as vp:
            out = _public(vp, lambda v: v.page.evaluate(
                "(sel) => { const i = document.querySelector(sel); return i ? "
                "{w: i.naturalWidth, alt: i.alt, text: i.closest('.qc-vmo-sec-rich').innerText} : null; }",
                f'.qc-vmo-section img[alt="QCTEST-136344"]'),
                lambda v: isinstance(v, dict) and v.get("w", 0) > 0)
        _attach("embedded image", out)
        assert isinstance(out, dict) and out["w"] > 0, f"embedded image did not render: {out}"
        assert "QCTEST-136344" in out["text"], "the text around the image is missing"


@allure.feature("VMO -- lifecycle")
@allure.title("Closing a Preview without publishing leaves the record intact (ADO-136346)")
@COMMON
@GROUP
@pytest.mark.functional_low
@pytest.mark.tc_136346
def test_136346_close_preview_leaves_record_intact(page):
    form = _form(page, "page")
    form.open_record(VMO_PAGE_CODE)
    before = {"heading": form.value("intro_heading", EN), "status": form.current_status()}
    _put(form, "intro_heading", EN, "QCTEST-136346 previewed, not published")
    link = page.get_by_role("link", name=re.compile("open in a new tab", re.I))
    opened = False
    if link.count():
        with page.context.expect_page(timeout=30000) as popup:
            link.first.click()
        preview = popup.value
        preview.wait_for_load_state("domcontentloaded")
        preview.close()
        opened = True
    form.open_record(VMO_PAGE_CODE)
    after = {"heading": form.value("intro_heading", EN), "status": form.current_status()}
    _attach("outcome", {"preview opened + closed": opened, "before": before, "after": after})
    assert opened, "no Preview link on the form"
    assert after == before, f"closing the Preview changed the record: {before} -> {after}"


@allure.feature("VMO -- lifecycle")
@allure.title("Rapidly double-clicking Publish does not create a duplicate publish (ADO-136347)")
@COMMON
@GROUP
@pytest.mark.edge
@pytest.mark.tc_136347
def test_136347_double_click_publish(page):
    form = _form(page, "page")
    with _restoring(form, "page", "136347", [("intro_heading", EN)]):
        form.open_entries_list(locale=EN)
        try:
            before = len(form.history_entries(VMO_PAGE_CODE))
        except Exception:  # noqa: BLE001
            before = None
        form.open_record(VMO_PAGE_CODE)
        _put(form, "intro_heading", EN, "QCTEST-136347 double click")
        log_live_write(PAGE_REC, "Intro Heading (EN)", "QCTEST-136347 double click", "136347", action="publish",
                       note="double-click Publish")
        writes = []
        page.on("request", lambda r: writes.append(r.method + " " + r.url) if r.method in ("POST", "PUT", "PATCH")
                and "/o/c/" in r.url else None)
        page.locator(form.PUBLISH_SUBMIT).first.dblclick()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        form.open_entries_list(locale=EN)
        status = form.row_status_text_by_code(VMO_PAGE_CODE)
        rows = [c for c, _ in form.row_statuses() if "VISION-MISSION-OBJECTIVES-PAGE" in c or c.startswith("Vision")]
        try:
            after = len(form.history_entries(VMO_PAGE_CODE))
        except Exception:  # noqa: BLE001
            after = None
        _attach("outcome", {"status": status, "rows": rows, "history before/after": [before, after],
                            "write requests": writes})
        assert status == STATUS_PUBLISHED, f"status after double-click is {status!r}"
        assert len(rows) <= 1, f"a duplicate record appeared: {rows}"
        if before is not None and after is not None:
            assert after - before <= 1, f"{after - before} publish events recorded for one double-click"


@allure.feature("VMO -- section visibility")
@allure.title("The page behaves correctly when all three sections are deactivated (ADO-136351)")
@COMMON
@GROUP
@pytest.mark.edge
@pytest.mark.tc_136351
def test_136351_all_sections_deactivated(page, browser):
    with _active_restored(page, "136351", ["vision", "mission", "objectives"]) as before:
        assert all(v == "True" for v in before.values()), f"precondition: not all sections active: {before}"
        _set_active_and_publish(page, "136351", {"vision": False, "mission": False, "objectives": False})
        with _visitor(browser) as vp:
            errors = []
            vp.page.on("pageerror", lambda e: errors.append(str(e)))
            out = _public(vp, lambda v: {"sections": v.section_count(), "hero": v.is_hero_visible(),
                                         "intro": v.is_intro_visible()},
                          lambda v: isinstance(v, dict) and v["sections"] == 0)
            vp.page.screenshot(path="reports/vmo-136351-no-sections.png", full_page=True)
        _attach("outcome", {"public": out, "page errors": errors})
        assert isinstance(out, dict) and out["sections"] == 0, f"sections still render: {out}"
        assert out["hero"] and out["intro"], f"the rest of the page broke: {out}"
        assert not errors, f"script errors on the page: {errors}"


@allure.feature("VMO -- lifecycle")
@allure.title("Two admins saving conflicting edits concurrently cause no silent data loss (ADO-136352)")
@COMMON
@GROUP
@pytest.mark.edge
@pytest.mark.tc_136352
def test_136352_concurrent_saves(page, browser):
    form = _form(page, "page")
    with _restoring(form, "page", "136352", [("intro_heading", EN), ("intro_heading", AR)]):
        ctx_b = new_context(browser, role=ROLE_EDITOR)
        try:
            form_b = VmoPageForm(ctx_b.new_page())
            form_b.sign_in(ROLE_EDITOR)
            form.open_record(VMO_PAGE_CODE)
            form_b.open_record(VMO_PAGE_CODE)
            _put(form, "intro_heading", EN, "QCTEST-136352 admin A")
            _put(form_b, "intro_heading", AR, "QCTEST-136352 المشرف ب")
            log_live_write(PAGE_REC, "Intro Heading (EN/AR)", "A: EN, B: AR", "136352", action="publish",
                           note="two concurrent Editor sessions")
            a_blocked = form.publish_click()
            b_blocked = form_b.publish_click()
            b_said = form_b.visible_form_messages()
        finally:
            ctx_b.close()
        form.open_record(VMO_PAGE_CODE)
        final = {"en": form.value("intro_heading", EN), "ar": form.value("intro_heading", AR)}
        _attach("outcome", {"a blocked": a_blocked, "b blocked": b_blocked, "b messages": b_said, "final": final})
        lost_a = "QCTEST-136352 admin A" not in final["en"]
        warned = bool(b_blocked) or any(re.search(r"conflict|modified|another|تعارض", m, re.I) for m in b_said)
        assert not lost_a or warned, f"silent data loss: A's edit was overwritten with no warning ({final})"


# =============================================================================
# Character limits -- QA lead decision 2026-10-14: the PBI 129395 field-table
# limit is binding (supersedes "no char limits", 2026-10-03). The case types
# limit + 1 characters and clicks Publish; the stored value must be refused
# or cut to the limit. Same-form failures are filed as ONE bug per form.
# The previous value is put back in teardown.
# =============================================================================
def _over_limit(page, tc: str, kind: str, key: str, loc: str, limit: int) -> None:
    form = _form(page, kind)
    rich = form.spec(key).kind == "rich"
    filler = "ع" if loc == AR else "x"
    text = (f"QCTEST-{tc} " + filler * (limit + 1))[:limit + 1]
    value = f"<p>{text}</p>" if rich else text
    with _restoring(form, kind, tc, [(key, loc)]):
        form.open_record(_code(kind))
        maxlength = None
        if not rich:
            label = form.spec(key).ar_label() if loc == AR else form.spec(key).label
            maxlength = page.get_by_role("textbox", name=form.label_pattern(label)).first.get_attribute("maxlength")
        with allure.step(f"Type {limit + 1} characters in {_label(form, key, loc)} and click Publish"):
            blocked = _publish_changes(form, kind, tc, {(key, loc): value},
                                       note=f"{limit + 1} characters (PBI limit {limit})")
        form.open_record(_code(kind))
        stored = _get(form, key, loc)
        stored_text = _norm(re.sub(r"<[^>]+>", "", stored)) if rich else stored
        _attach("char limit (PBI)", {"pbi_limit": limit, "typed": len(text), "maxlength attribute": maxlength,
                                     "blocked": blocked, "stored_length": len(stored_text)})
        assert len(stored_text) <= limit or "QCTEST" not in stored_text, (
            f"{_label(form, key, loc)} accepted {len(stored_text)} characters; the PBI limit is {limit} "
            f"(maxlength attribute: {maxlength})")


_LIMIT_CASES = [
    ("136192", "page", "page_title", EN, 100), ("136196", "page", "page_title", AR, 100),
    ("136204", "page", "intro_heading", EN, 100),
    ("136208", "page", "intro_desc", EN, 500), ("136212", "page", "intro_desc", AR, 500),
    ("136274", "vision", "label", EN, 100),
    ("136283", "vision", "headline", EN, 150), ("136335", "objectives", "headline", EN, 150),
    ("136290", "vision", "subheading", EN, 150), ("136295", "vision", "subheading", AR, 150),
    ("136301", "vision", "body", EN, 5000), ("136308", "vision", "body", AR, 5000),
    ("136327", "mission", "body", EN, 5000),
    ("136314", "vision", "badge", EN, 50), ("136317", "vision", "badge", AR, 50),
    ("136331", "mission", "badge", AR, 50),
]


def _make_limit_test(tc, kind, key, loc, limit):
    @allure.feature("VMO -- character limits")
    @allure.title(f"{kind} {key} ({loc.upper()}) rejects input over {limit} characters (ADO-{tc})")
    @COMMON
    @GROUP
    @pytest.mark.functional_low
    def _t(page):
        _over_limit(page, tc, kind, key, loc, limit)

    _t = getattr(pytest.mark, f"tc_{tc}")(_t)
    _t.__name__ = f"test_{tc}_{kind}_{key}_{loc}_over_{limit}"
    return _t


for _tc, _kind, _key, _loc, _limit in _LIMIT_CASES:
    globals()[f"test_{_tc}_{_kind}_{_key}_{_loc}_over_{_limit}"] = _make_limit_test(_tc, _kind, _key, _loc, _limit)


@allure.feature("VMO -- section visibility")
@allure.title("Reactivating Mission restores it to the sequence and renumbers 01/02/03 (ADO-136184)")
@COMMON
@GROUP
@pytest.mark.functional_high
@pytest.mark.tc_136184
def test_136184_reactivate_mission_renumbers(page, browser):
    with _active_restored(page, "136184", ["vision", "mission", "objectives"]) as before:
        assert all(v == "True" for v in before.values()), f"precondition: not all sections active: {before}"
        _set_active_and_publish(page, "136184", {"mission": False})
        with _visitor(browser) as vp:
            first = _public(vp, _numbers, lambda v: isinstance(v, dict) and "Mission" not in v and v.get("Objectives") == 2)
        _set_active_and_publish(page, "136184", {"mission": True})
        with _visitor(browser) as vp:
            nums = _public(vp, _numbers, lambda v: isinstance(v, dict) and v.get("Mission") == 2)
        _attach("public numbering", {"Mission inactive": first, "Mission reactivated": nums})
        assert first == {"Vision": 1, "Objectives": 2}, f"precondition state (TC-039) not reached: {first}"
        assert nums == {"Vision": 1, "Mission": 2, "Objectives": 3}, f"numbering after reactivating Mission: {nums}"

"""
cms/tests/certificate_of_origin/b_checks.py — check bodies for Engineer B's
Phase 3 modules (PBIs 130947, 130949), 2026-10-01, that the shared
cms/tests/authoring_checks.py does not cover (that file is shared and is not
edited). Part 1: character limits. Part 2: render / order / role shapes.

Not a test module. Part 1 implements the team's binding "Character-limit rules"
(phase3_2026-10-01b_councils_brief.md), which supersede the shared
authoring_checks.check_over_max_refused() for these PBIs:

  1. rich-text fields: no limit applies — those cases are skipped as NA in
     the test module, never routed here;
  2. implemented max > US limit: not a failure by itself. Fill to the
     implemented max, save, and check the admin form/list (and the public
     render where the case covers it) for broken layout. Broken = PRODUCT_BUG,
     owner FE (fallback Alaa). Fine = pass. US and implemented are recorded;
  3. implemented max < US limit: PRODUCT_BUG, owner Alaa.

No field on these forms carries a `maxlength` attribute (read live
2026-10-01), so the implemented max is observed through save + read-back on
a QCTEST Draft, then (non-singleton objects only) a submit with Active Status
unticked, so a submit-time check is seen without anything reaching visitors.
The public render is checked only where the case covers it, on a
non-singleton QCTEST record. Every record is deleted every run.
"""

from __future__ import annotations

import json
import sys
import time

import pytest

from cms.pages.certificate_of_origin.fragment_form_mixin import log_leftover
from cms.pages.components.disposable_object_admin import (
    DISPOSABLE_PREFIX, ROLE_AUTHOR, ROLE_EDITOR, chars, qctest_title,
)
from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import control_panel_url

# Liferay Objects' default Text-field ceiling; probed when US+1 is accepted.
LIFERAY_TEXT_CEILING = 280

# ---------------------------------------------------------------------------
# Unique disposable titles per run (review fix 2026-10-03): 23 undeletable
# QCTEST char-limit records from earlier runs share titles with these tests,
# so every title now ends in a run token: QCTEST-<tc>-<kind>-<MMDDHHMMSS>.
# Applied by the autouse fixture below, which the two test modules import;
# monkeypatch restores the shared helpers after each test, so no other
# module sees the token.
# ---------------------------------------------------------------------------
RUN_TOKEN = time.strftime("%m%d%H%M%S")


def run_title(tc_id, short: str) -> str:
    return f"{DISPOSABLE_PREFIX}{tc_id}-{short}-{RUN_TOKEN}"


@pytest.fixture(autouse=True)
def unique_qctest_titles(monkeypatch):
    from cms.tests import authoring_checks as ck

    monkeypatch.setattr(ck, "qctest_title", run_title)
    monkeypatch.setattr(sys.modules[__name__], "qctest_title", run_title)
    yield


INACTIVE_DRAFT_MSG = (
    "NEEDS_INVESTIGATION (candidate finding, not filed): Editor Publish with Active unticked "
    "leaves record in DRAFT (user-confirmed manually 2026-10-03); the case expects it Published but hidden"
)


def check_required_by_case(check, admin_cls, key, *args, **kwargs):
    """Run a refusal check for a field the CASE/PBI calls mandatory while the
    live form marks it optional. Per the user (2026-10-03) that mismatch IS a
    bug: a failure is reported as PRODUCT_BUG "PBI mandatory, form optional",
    collected for filing (never filed from here)."""
    spec = admin_cls.FIELDS[key]
    try:
        check(*args, **kwargs)
    except AssertionError as exc:
        if spec.required:
            raise
        raise AssertionError(
            f"PRODUCT_BUG (to file after user OK; user decision 2026-10-03): PBI mandatory, form "
            f"optional - the case expects Publish to be blocked when {spec.label!r} is empty / "
            f"whitespace-only; the live form marks the field optional and the record was stored. "
            f"Detail: {exc}"
        ) from None

_OVERFLOW_JS = "() => document.documentElement.scrollWidth > window.innerWidth + 1"


def _value_for(admin, tc_id: int, key: str, n: int, short: str) -> tuple[str, str]:
    """(title, value). On the title field the value IS the QCTEST title so the
    record stays findable and deletable by exact title."""
    if key == admin.TITLE_FIELD:
        v = (qctest_title(tc_id, short) + "-" + chars(n))[:n]
        return v, v
    return qctest_title(tc_id, short), chars(n)


def _save_and_read(admin, tc_id, key, n, short, files):
    """Store an n-char value in `key` (both language sides when bilingual) on
    a QCTEST record and measure it.

    Returns (title, stored_length | None, refused_at_submit).
    The Save as Draft is watched on the network (review fix 2026-10-03): the
    save is `POST edit_info_item` (302) then `PUT /o/c/<plural>/<id>`, and the
    record's ID comes from that write. Read-back, submit and delete then go
    by ID, never by the (long) title. No save request at all = the limit is
    enforced (the button stays disabled, no message shown). On a
    non-singleton object the record is then submitted with Active Status
    unticked so a submit-time check is observed too (nothing reaches
    visitors); singletons stay draft-only (refused_at_submit is None)."""
    title, value = _value_for(admin, tc_id, key, n, short)
    admin.open_form(ROLE_EDITOR)
    admin.fill_required(title, skip=(key,) if key != admin.TITLE_FIELD else (), files=files)
    admin.fill(key, value)
    if admin.spec(key).bilingual:
        admin.fill(key, value, locale="ar")
    typed = len(admin.value(key))
    if typed < n:
        return title, typed, None  # input-level truncation
    admin.save_as_draft()
    ls = admin.last_save
    if not ls["id"]:
        # nothing stored: no save request at all = enforced; a save that went
        # out and stored nothing is not measured (None)
        return title, None, (True if not ls["started"] else None)
    admin.open_entry_by_edit_link(title)
    stored = len(admin.value(key))
    if admin.SINGLETON:
        return title, stored, None
    admin.submit_for_review()
    refused = admin.refusal_visible()
    return title, stored, refused


def _verified_delete(admin, title: str, key: str | None = None) -> bool:
    """Teardown: delete our own QCTEST record by ID (see
    FragmentFormMixin.delete_disposable). A refused trash call (HTTP 400 on a
    record holding an over-limit value, seen 2026-10-02) is logged with the
    id and moved past - no unpublish / reset / re-delete loop. Never raises."""
    try:
        ok = admin.delete_disposable(title)
        if not ok:
            log_leftover(f"LEFTOVER {admin.SLUG} id={admin.id_for(title)} {title[:60]!r}")
        return ok
    except Exception as exc:  # noqa: BLE001 — teardown must not mask the test result
        log_leftover(f"teardown error {title[:60]!r}: {str(exc)[:160]}")
        return False


def _tag(singleton: bool) -> str:
    return " (draft-stored; submit-time limit not testable on a singleton)" if singleton else ""


def _layout_broken(page) -> bool:
    return bool(page.evaluate(_OVERFLOW_JS))


def check_limit_exact(page, browser, admin_cls, tc_id, key, us, files=None, probe=None):
    """Exactly `us` characters must be stored in full and accepted on submit
    (else rule 3, owner Alaa). With `probe` on a non-singleton object the
    value is also published with Active ticked and must render in full to a
    logged-out visitor."""
    admin = admin_cls(page)
    title = None
    label = admin_cls.FIELDS[key].label
    try:
        title, stored, refused = _save_and_read(admin, tc_id, key, us, "exact", files)
        assert stored == us, (
            f"PRODUCT_BUG (owner Alaa, rule 3): {label} US={us}, implemented<{us} "
            f"(stored {stored!r} of {us} characters){_tag(admin_cls.SINGLETON)}"
        )
        assert not refused, f"PRODUCT_BUG (owner Alaa, rule 3): {label} US={us}: a {us}-character value is refused on submit"
        print(f"[tc_{tc_id}] {key}: US={us}, exact {us} accepted{_tag(admin_cls.SINGLETON)}")
        if probe and not admin_cls.SINGLETON:
            _publish_and_check_render(page, browser, admin, title, key, probe)
    finally:
        if title:
            _verified_delete(admin, title, key)


def check_limit_over(page, browser, admin_cls, tc_id, key, us, files=None, probe=None):
    """Rule 2, phase3 brief Character-limit rules. A char-limit case is a
    product finding only under rule 2 (UI broken at the implemented max) or
    rule 3 (implemented max < US). Accepting a value above the US limit is
    expected and is never asserted as a refusal.

    `us`+1 characters: truncated or refused -> implemented == US, pass.
    Accepted -> measure the implemented max (fill to the Liferay ceiling and
    read back what is stored), then check the admin form/list (and the public
    render with `probe`) at that max. A Draft that never saves is a test-side
    failure (AUTOMATION), not a product verdict."""
    admin = admin_cls(page)
    titles = []
    label = admin_cls.FIELDS[key].label
    tag = _tag(admin_cls.SINGLETON)
    try:
        title, stored, refused = _save_and_read(admin, tc_id, key, us + 1, "over", files)
        titles.append(title)
        if stored is None and refused:
            print(f"[tc_{tc_id}] {key}: US={us}, implemented={us} (US+1 never commits: limit enforced, no message shown){tag}")
            return
        assert stored is not None, f"AUTOMATION: {title!r}: the Draft never saved (Save as Draft skips validation), so nothing was measured"
        if stored <= us or refused:
            print(f"[tc_{tc_id}] {key}: US={us}, implemented={us} (over-limit refused/truncated){tag}")
            return
        implemented, at = f">{us}", title
        t2, s2, r2 = _save_and_read(admin, tc_id, key, LIFERAY_TEXT_CEILING, "ceil", files)
        titles.append(t2)
        assert s2 is not None or r2, f"AUTOMATION: {t2!r}: the ceiling Draft never saved, so the implemented max was not measured"
        if s2 is None:
            # the ceiling never commits (enforced): the max lies in between
            implemented = f"{us + 1}..{LIFERAY_TEXT_CEILING - 1}"
        elif s2 == LIFERAY_TEXT_CEILING and not r2:
            implemented, at = f">={LIFERAY_TEXT_CEILING}", t2
        elif s2 < LIFERAY_TEXT_CEILING:
            # the stored value was cut: what is held IS the implemented max
            implemented, at = str(s2), t2
        else:
            # 280 stored but refused on submit: the max lies in between, and
            # the US+1 record (stored and accepted) is the largest proven value
            implemented = f"{us + 1}..{LIFERAY_TEXT_CEILING - 1}"
        print(f"[tc_{tc_id}] {key}: US={us}, implemented={implemented}{tag}")
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(at)
        assert not _layout_broken(page), (
            f"PRODUCT_BUG (owner FE, fallback Alaa, rule 2): {label} US={us}, "
            f"implemented={implemented}{tag}: admin form overflows horizontally"
        )
        admin.open_list(ROLE_EDITOR)
        admin.filter_entries(at)
        assert not _layout_broken(page), (
            f"PRODUCT_BUG (owner FE, fallback Alaa, rule 2): {label} US={us}, "
            f"implemented={implemented}{tag}: entries list overflows horizontally"
        )
        if probe and not admin_cls.SINGLETON:
            _publish_and_check_render(page, browser, admin, at, key, probe)
    finally:
        for t in titles:
            _verified_delete(admin, t, key)


def _publish_and_check_render(page, browser, admin, title, key, probe):
    from core.web.browser import new_context

    admin.open_list(ROLE_EDITOR)
    admin.open_entry_by_edit_link(title)
    value = admin.value(key)
    if admin.ACTIVE_FIELD and admin.ACTIVE_FIELD in admin.FIELDS:
        admin.set_flag(admin.ACTIVE_FIELD, True)
    admin.submit_for_review()
    status = admin.status_of(title, ROLE_EDITOR)
    assert status == STATUS_PUBLISHED, f"{title!r} is {status!r} after an Editor submit, not Published"
    ctx = new_context(browser, use_auth_state=False)
    try:
        anon = ctx.new_page()
        assert probe(anon, value), f"{key}: the {len(value)}-character value is not rendered in full publicly"
        assert not _layout_broken(anon), (
            f"PRODUCT_BUG (owner FE, fallback Alaa, rule 2): {key} at {len(value)} characters "
            "overflows the public page horizontally"
        )
    finally:
        ctx.close()


# ===========================================================================
# Part 2 — render / order / role shapes
# ===========================================================================
def _anon(browser):
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False)
    return ctx, ctx.new_page()


def _publish(admin, title, active=True, files=None, extra=None, skip=()):
    """Editor create -> Submit; asserts the privileged path lands on Published.
    The status is read BY ID (review fix 2026-10-03), not via the list."""
    admin.open_form(ROLE_EDITOR)
    admin.fill_required(title, active=active, files=files, skip=skip)
    for key, val in (extra or {}).items():
        admin.fill(key, val)
    admin.submit_for_review()
    eid = admin.id_for(title)
    assert eid, f"{title!r}: the Editor submit stored no record ({admin.save_counts()})"
    if active:
        status = admin.status_of(title, ROLE_EDITOR)  # by ID, with the Editor publish settle
        assert status == STATUS_PUBLISHED, f"{title!r} (id {eid}) is {status or 'unreadable'!r} after an Editor submit, not Published"
        return
    status = admin.status_by_id(eid, admin.plural_for(title))
    # Active Status unticked. The user checked this by hand on 2026-10-03:
    # the record stays in Draft. The case expects "Published but hidden".
    raw = getattr(admin, "last_status_raw", "")
    assert status != STATUS_DRAFT, f"{INACTIVE_DRAFT_MSG} (id {eid}, status {status!r}; {raw})"
    assert status == STATUS_PUBLISHED, (
        f"{title!r} (id {eid}) is {status or 'unreadable'!r} after an Editor Publish with Active unticked"
    )
    _assert_newest_history_is_editor_publish(admin, title)


def _assert_newest_history_is_editor_publish(admin, title) -> None:
    """The NEWEST History entry of the record (row located BY ID) must be the
    Editor's submit/publish."""
    eid = admin.id_for(title)
    admin.open_list(ROLE_EDITOR)
    hist = admin.history_entries(title)
    assert hist, f"{title!r} (id {eid}): no History trail recorded"
    newest = hist[-1]
    blob = " ".join(str(v) for v in newest.values()).casefold()
    assert "editor" in blob, f"{title!r} (id {eid}): newest History entry is not the Editor's: {newest!r}"
    assert any(w in blob for w in ("publish", "submit", "approv")), (
        f"{title!r} (id {eid}): newest History entry does not record a submit/publish: {newest!r}"
    )


def check_edit_published_updates(page, browser, admin_cls, tc_id, probe, key, new_value, files=None, extra=None):
    """The case path: Editor publishes a QCTEST record (Active ticked), edits
    `key` on the Published record and submits (Publish) again. It must stay
    Published, History must record the Editor's publish (the case's
    audit-log step), Active Status must still be ticked (gate 2), and a
    logged-out visitor sees the new value.

    b9 (2026-10-04): `extra` is filled at creation (e.g. a resource file, so
    the card renders its button as on the live page). When `key` is the
    object's title field, the new value keeps the QCTEST title as its prefix,
    so the teardown's by-ID delete still recognises the record as ours."""
    admin = admin_cls(page)
    title = qctest_title(tc_id, "edit")
    if key == admin_cls.TITLE_FIELD:
        new_value = f"{title} {new_value}"
    ctx, anon = _anon(browser)
    try:
        _publish(admin, title, files=files, extra=extra)
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        admin.fill(key, new_value)
        admin.submit_for_review()
        status = admin.status_of(title, ROLE_EDITOR)
        assert status == STATUS_PUBLISHED, f"{title!r} is {status or 'absent'!r} after editing a Published record"
        _assert_newest_history_is_editor_publish(admin, title)
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        assert admin.flag(admin.ACTIVE_FIELD), "Active Status is not ticked (second visibility gate)"
        assert probe(anon, new_value), f"{key}: visitor does not see the edited value {new_value!r}"
    finally:
        _verified_delete(admin, title)
        ctx.close()


def check_replace_file_published(page, browser, admin_cls, tc_id, probe, key, first, second, files=None):
    """A Published QCTEST record (Active ticked) carrying file `first` gets
    `second` uploaded in place WITHOUT unpublishing; it stays Published and
    the public page serves the new file (its stored name is in the page)."""
    admin = admin_cls(page)
    title = qctest_title(tc_id, "swap")
    ctx, anon = _anon(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True, files=files)
        admin.upload(key, first, tag=f"{tc_id}-v1")
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED, "precondition: record is not Published"
        admin.open_entry_by_edit_link(title)
        admin.upload(key, second, tag=f"{tc_id}-v2")
        new_name = admin.value(key)
        admin.submit_for_review()
        status = admin.status_of(title, ROLE_EDITOR)
        assert status == STATUS_PUBLISHED, f"{title!r} is {status or 'absent'!r} after the file swap (was Published)"
        assert probe(anon, title), f"{title!r} is not rendered to a logged-out visitor after the swap"
        stem = new_name.rsplit(".", 1)[0]
        assert stem and stem in anon.content(), f"the public page does not serve the replacement file {new_name!r}"
    finally:
        _verified_delete(admin, title)
        ctx.close()


def _expanded_probe(open_public):
    """Probe for content inside a collapsed accordion item: open the public
    page, expand the item whose header shows the record title, then read the
    visible text. Polls like the shared probe (60s), for the delivery lag."""
    from core.utils.waits import WaitTimeoutError, wait_until

    def probe(anon, title, text):
        seen = {"ok": False}

        def _ok():
            open_public(anon)
            header = anon.get_by_text(title, exact=False).first
            if header.count() == 0:
                return False
            header.click()
            anon.wait_for_timeout(1000)
            seen["ok"] = text in anon.locator("body").inner_text()
            return seen["ok"]

        try:
            wait_until(_ok, timeout=60.0, poll=3.0)
        except WaitTimeoutError:
            pass
        return seen["ok"]

    return probe


def check_valid_renders(page, browser, admin_cls, tc_id, key, en, ar=None, probe=None, files=None, extra=None,
                        expand_open=None):
    """Editor publishes a QCTEST record (Active ticked) holding `key`=en/ar;
    the values persist on reopen and a logged-out visitor sees `en`."""
    admin = admin_cls(page)
    spec = admin_cls.FIELDS[key]
    title = qctest_title(tc_id, "render")
    if key == admin_cls.TITLE_FIELD:
        title = qctest_title(tc_id, en)[: spec.max_len or None]
        en = title
    ctx, anon = _anon(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,) if key != admin_cls.TITLE_FIELD else (), active=True, files=files)
        if key != admin_cls.TITLE_FIELD:
            admin.fill(key, en)
        if ar is not None and spec.bilingual:
            admin.fill(key, ar, locale="ar")
        for k, v in (extra or {}).items():
            admin.fill(k, v)
        admin.submit_for_review()
        status = admin.status_of(title, ROLE_EDITOR)
        assert status == STATUS_PUBLISHED, f"{title!r} is {status or 'absent'!r} after an Editor submit"
        admin.open_entry_by_edit_link(title)
        assert admin.value(key) == en, f"{key} EN did not persist: {admin.value(key)!r}"
        if ar is not None and spec.bilingual:
            assert admin.value(key, "ar") == ar, f"{key} AR did not persist: {admin.value(key, 'ar')!r}"
        assert admin.flag(admin.ACTIVE_FIELD), "Active Status is not ticked (second visibility gate)"
        if expand_open is not None:
            # the case reads the content "when the item is expanded" (tc_141083)
            assert _expanded_probe(expand_open)(anon, title, en), (
                f"{key}={en!r} is Published + Active but not shown when its item {title!r} is expanded "
                "for a logged-out visitor. " + _diagnose_public(anon, admin, title, en)
            )
        elif probe and not probe(anon, en):
            raise AssertionError(
                f"{key}={en!r} is Published + Active but not rendered to a logged-out visitor. "
                + _diagnose_public(anon, admin, title, en)
            )
    finally:
        _verified_delete(admin, title)
        ctx.close()


def _diagnose_public(anon, admin, title, value) -> str:
    """Rule out our side before a "not rendered publicly" result counts
    (QA Manager, 2026-10-04): both gates by ID; up to 60s logged-out retry
    on the same URL/locale; what the page's own /o/c/ calls return (is the
    record there, at which position, with what pageSize / sort / filter);
    and whether the value is in the DOM but hidden (e.g. a collapsed panel)."""
    import json as _json
    import time as _time

    out = []
    eid, plural = admin.id_for(title), admin.plural_for(title)
    try:
        st = admin.status_by_id(eid, plural) if eid else ""
        data = admin.entry_json(title) or {}
        out.append(f"gates by id {eid}: status={st!r}, activeStatus={data.get('activeStatus')!r}")
    except Exception as exc:  # noqa: BLE001
        out.append(f"gates unreadable: {str(exc)[:80]}")
    url = anon.url
    out.append(f"public url={url}")
    calls = []

    def _on(resp):
        try:
            if "/o/c/" in resp.url and resp.request.method == "GET" and plural and f"/o/c/{plural}" in resp.url:
                d = resp.json()
                items = d.get("items", []) if isinstance(d, dict) else []
                ids = [str(i.get("id")) for i in items]
                pos = ids.index(str(eid)) + 1 if str(eid) in ids else 0
                calls.append(f"{resp.url.split('/o/c/', 1)[1][:110]} total={d.get('totalCount')} "
                             f"returned={len(items)} ours_at={pos or 'absent'}")
        except Exception:  # noqa: BLE001
            pass

    anon.on("response", _on)
    seen = False
    try:
        deadline = _time.monotonic() + 60
        while _time.monotonic() < deadline:
            anon.goto(url, wait_until="domcontentloaded")
            anon.wait_for_timeout(4000)
            if value in anon.locator("body").inner_text():
                seen = True
                break
    except Exception as exc:  # noqa: BLE001
        out.append(f"reload error {str(exc)[:80]}")
    finally:
        anon.remove_listener("response", _on)
    out.append(f"visible after 60s retry={seen}")
    try:
        in_dom = anon.evaluate("v => document.body.textContent.includes(v)", value)
        title_vis = title in anon.locator("body").inner_text()
        out.append(f"in DOM text (incl. hidden)={in_dom}, record title visible={title_vis}")
    except Exception:  # noqa: BLE001
        pass
    out.append("page API calls: " + ("; ".join(dict.fromkeys(calls)) or f"none for /o/c/{plural}"))
    return "DIAG: " + " | ".join(out) + " " + _json.dumps({"id": eid})


def check_inactive_hidden(page, browser, admin_cls, tc_id, probe, files=None):
    """Published but Active Status unticked: the visitor must not see it
    (gate 1 passes, gate 2 is the variable)."""
    admin = admin_cls(page)
    title = qctest_title(tc_id, "inactive")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, title, active=False, files=files)
        admin.open_entry_by_edit_link(title)
        assert not admin.flag(admin.ACTIVE_FIELD), "precondition: Active Status is ticked"
        assert not probe(anon, title, False), f"{title!r} is Inactive but rendered to a logged-out visitor"
    finally:
        _verified_delete(admin, title)
        ctx.close()


def _order(anon, open_public, a, b):
    open_public(anon)
    text = anon.locator("body").inner_text()
    if a not in text or b not in text:
        return None
    return "ab" if text.index(a) < text.index(b) else "ba"


def _wait_order(anon, open_public, a, b, want=None):
    from core.utils.waits import WaitTimeoutError, wait_until

    seen = {"o": None}

    def _ok():
        seen["o"] = _order(anon, open_public, a, b)
        return seen["o"] is not None and (want is None or seen["o"] == want)

    try:
        wait_until(_ok, timeout=30.0, poll=3.0)
    except WaitTimeoutError:
        pass
    return seen["o"]


def check_order_follows(page, browser, admin_cls, tc_id, open_public, files=None, key="display_order"):
    """Two QCTEST records (orders 9901 < 9902) render A before B; after A is
    moved to 9903 and re-submitted, B renders before A."""
    admin = admin_cls(page)
    a, b = qctest_title(tc_id, "ord-a"), qctest_title(tc_id, "ord-b")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, a, files=files, extra={key: "9901"})
        _publish(admin, b, files=files, extra={key: "9902"})
        first = _wait_order(anon, open_public, a, b)
        assert first == "ab", f"orders 9901/9902 rendered {first!r}, expected A before B"
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(a)
        admin.fill(key, "9903")
        admin.submit_for_review()
        assert admin.status_of(a, ROLE_EDITOR) == STATUS_PUBLISHED
        after = _wait_order(anon, open_public, a, b, want="ba")
        assert after == "ba", f"re-ordering in the Control Panel did not change the public order ({after!r})"
    finally:
        _verified_delete(admin, a)
        _verified_delete(admin, b)
        ctx.close()


def check_duplicate_order_stable(page, browser, admin_cls, tc_id, open_public, files=None, key="display_order"):
    """Two QCTEST records saved with the same Display Order: both render, and
    their relative order is identical on three reloads."""
    admin = admin_cls(page)
    a, b = qctest_title(tc_id, "dup-a"), qctest_title(tc_id, "dup-b")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, a, files=files, extra={key: "9901"})
        _publish(admin, b, files=files, extra={key: "9901"})
        assert _wait_order(anon, open_public, a, b) is not None, "both QCTEST records never rendered"
        orders = [_order(anon, open_public, a, b) for _ in range(3)]
        assert None not in orders, f"a record dropped out on reload: {orders!r}"
        assert len(set(orders)) == 1, f"relative order changed between renders: {orders!r}"
    finally:
        _verified_delete(admin, a)
        _verified_delete(admin, b)
        ctx.close()


def check_ar_fallback(page, browser, admin_cls, tc_id, key, en, probe_ar, files=None):
    """Optional bilingual `key` filled in EN only: publish is not blocked and
    the Arabic page renders the EN value as the fallback."""
    admin = admin_cls(page)
    title = qctest_title(tc_id, "fallback")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, title, files=files, extra={key: en})
        assert probe_ar(anon, en), f"Arabic page does not fall back to the EN value of {key} ({en!r})"
    finally:
        _verified_delete(admin, title)
        ctx.close()


def check_ar_required_refused(page, admin_cls, tc_id, key, files=None):
    """Mandatory bilingual `key` with EN filled and AR empty: Submit must be
    refused and nothing published."""
    admin = admin_cls(page)
    title = qctest_title(tc_id, "no-ar")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,) if key != admin_cls.TITLE_FIELD else (), files=files)
        if key != admin_cls.TITLE_FIELD:
            admin.fill(key, admin_cls.FIELDS[key].default or f"QCTEST {tc_id}")
        admin.fill(key, "", locale="ar")
        admin.submit_for_review()
        refused = admin.refusal_visible()
        status = admin.status_of(title, ROLE_EDITOR)
        assert refused, f"{key} AR empty: Submit raised no refusal (status {status or 'absent'!r})"
        assert status != STATUS_PUBLISHED, f"{key} AR empty: the record was Published"
    finally:
        _verified_delete(admin, title)


def check_unbound_key_not_rendered(page, browser, admin_cls, tc_id, key, bad_key, probe, files=None):
    """A key outside the defined set is refused, or, if accepted, the record
    is not bound anywhere on the public page."""
    admin = admin_cls(page)
    title = qctest_title(tc_id, "key")
    ctx, anon = _anon(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,), active=True, files=files)
        admin.fill(key, bad_key)
        admin.submit_for_review()
        if admin.refusal_visible():
            return
        assert not probe(anon, title, False), f"a CTA keyed {bad_key!r} was bound onto the public page"
    finally:
        _verified_delete(admin, title)
        ctx.close()


AUTHORING_SURFACE = "select[data-qc-oel-status-filter], table tbody tr"


def check_author_cannot_create(page, admin_cls, tc_id, files=None):
    """Site Content Author: the create form is not offered, or a save does not
    create a record (checked as Editor)."""
    admin = admin_cls(page)
    title = qctest_title(tc_id, "author-new")
    try:
        admin.sign_in(ROLE_AUTHOR)
        assert not admin.has_admin_toolbar(), "precondition: the session has the admin toolbar"
        resp = page.goto(admin.manage_url(), wait_until="domcontentloaded")
        # Review fix 2026-10-04: a withheld form only proves something when we
        # are signed in and ON the authoring surface (cf. check_admin_portlet_denied).
        assert CmsLoginPage(page).login_succeeded(), "Site Content Author did not sign in; a missing form would prove nothing"
        assert resp is None or resp.status < 400, f"manage page answered HTTP {resp.status}, not the authoring surface"
        try:
            page.locator(AUTHORING_SURFACE).first.wait_for(state="attached", timeout=35000)
        except Exception:  # noqa: BLE001
            raise AssertionError(
                f"NEEDS_INVESTIGATION: the authoring surface (entries list) did not render at {page.url}; "
                "cannot conclude the create form is withheld"
            ) from None
        if page.locator(admin.SAVE_AS_DRAFT_BUTTON).count() == 0:
            return
        admin.open_new_entry_form(locale="en")
        admin.fill_required(title, files=files)
        admin.save_as_draft()
        assert not admin.entry_exists(title, ROLE_EDITOR), f"Site Content Author created {title!r}"
    finally:
        _verified_delete(admin, title)


def check_admin_portlet_denied(page, role, path, forbidden=("Add Field", "Add User", "Add Role")):
    """`role` opens a Control Panel admin portlet: no management control is
    rendered and the refusal is positive (HTTP 401/403/404, sign-in, or
    permission text)."""
    from cms.pages.certificate_of_origin.certificate_of_origin_admin_page import CooPageContentAdminPage

    CooPageContentAdminPage(page).sign_in(role)  # per-worker cached role session, lands on /en/home
    lp = CmsLoginPage(page)
    assert lp.login_succeeded(), f"{role} did not sign in; the denial would prove nothing"
    resp = page.goto(control_panel_url(path), wait_until="domcontentloaded")
    for label in forbidden:
        offered = page.get_by_role("button", name=label).count() + page.get_by_role("link", name=label).count()
        assert offered == 0, f"{role} is offered {label!r}"
    body = page.locator("body").inner_text().casefold()
    denied = (resp is not None and resp.status in (401, 403, 404)) or any(
        s in body for s in ("permission", "do not have the roles", "access denied", "not found", "sign in")
    )
    assert denied, f"no positive denial for {role} at {path}"


def check_autocaptured(page, admin_cls, tc_id, key, files=None, upload=None):
    """`key` is populated by the system on save (optionally after an upload
    `upload=(file_key, path)`) and is not editable."""
    admin = admin_cls(page)
    title = qctest_title(tc_id, "auto")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,), files=files)
        if upload:
            admin.upload(upload[0], upload[1], tag=str(tc_id))
        admin.save_as_draft()
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        assert admin.value(key), f"{key} is empty: not captured automatically"
        editable = admin.field_editable(key) if hasattr(admin, "field_editable") else page.get_by_role(
            "textbox", name=admin.label_pattern(admin_cls.FIELDS[key].label)).first.is_editable()
        assert not editable, f"{key} is editable by the author"
    finally:
        _verified_delete(admin, title)


def check_options_exact(page, admin_cls, key, expected):
    """The dropdown offers exactly `expected` (order-insensitive). Read-only:
    the create form is opened and nothing is saved."""
    admin = admin_cls(page)
    admin.open_form(ROLE_EDITOR)
    opts = admin.select_options(key)
    assert sorted(opts) == sorted(expected), f"{key} offers {opts!r}, expected {expected!r}"


# ===========================================================================
# Part 3 — b9 (2026-10-04) re-checks for uploads and Preview
# ===========================================================================
_SIZE_REFUSAL_RE = r"accepts files up to|no larger than|too large|exceeds"


def check_oversize_refused(page, admin_cls, tc_id, key, fixture, files=None):
    """An over-size upload is refused, proven two ways (b9 live probe
    2026-10-04: the picker accepts the pick, then the field shows
    '"<name>" is 6.0 MB. <Field> accepts files up to 5 MB - choose a smaller
    file.' and clears its readout). The shared check read the readout
    before that client-side check ran, so it saw the name and called it
    accepted. Here: a positive refusal message (or a cleared readout) after
    the pick, AND after Save as Draft the record holds no file from this
    upload (read BY ID)."""
    import re as _re

    from core.utils.waits import WaitTimeoutError, wait_until

    admin = admin_cls(page)
    title = qctest_title(tc_id, "big")
    label = admin_cls.FIELDS[key].label
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,), files=files)
        admin.upload(key, fixture, tag=str(tc_id))
        stem = admin.__dict__.get("_qcb_uploads", {}).get(key, "").rsplit(".", 1)[0]
        seen = {"msg": "", "readout": None}

        def _refused():
            texts = page.locator(".alert-danger, .form-feedback-item, [role=alert]").all_inner_texts()
            hit = [" ".join(t.split()) for t in texts if _re.search(_SIZE_REFUSAL_RE, t, _re.I)]
            seen["msg"] = hit[0] if hit else ""
            try:
                seen["readout"] = admin.uploaded_filename(label)
            except Exception:  # noqa: BLE001
                seen["readout"] = None
            return bool(seen["msg"]) or (seen["readout"] == "")

        try:
            wait_until(_refused, timeout=15.0, poll=0.5, message="no refusal after the over-size pick")
        except WaitTimeoutError:
            pass
        print(f"[tc_{tc_id}] {key}: refusal message={seen['msg']!r} readout={seen['readout']!r}")
        assert seen["msg"] or seen["readout"] == "", (
            f"{key}: {fixture.rsplit('/', 1)[-1]} stayed attached with no refusal message (readout {seen['readout']!r})"
        )
        admin.save_as_draft()
        data = admin.entry_json(title)
        assert data is not None, f"AUTOMATION: the Draft {title!r} was not stored, so the stored file could not be read ({admin.save_counts()})"
        stored = [v.get("name") for v in data.values() if isinstance(v, dict) and stem and stem in json.dumps(v)]
        assert not stored, f"{key}: the over-size file was STORED on record {admin.id_for(title)}: {stored!r}"
    finally:
        _verified_delete(admin, title)


def check_preview_draft_renders(page, browser, admin_cls, tc_id, probe, files=None, wait_s: float = 45.0):
    """Editor Draft: the row's Preview link (the public page URL with
    `?qcPreview=<plural>:<id>`, read live 2026-10-04) renders the draft's
    title for the signed-in editor, and the public page does not. The shared
    check read the body straight after domcontentloaded, before the preview
    script had fetched the draft."""
    from core.utils.waits import WaitTimeoutError, wait_until

    admin = admin_cls(page)
    title = qctest_title(tc_id, "preview")
    ctx, anon = _anon(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True, files=files)
        admin.save_as_draft()
        assert admin.id_for(title), f"{title!r}: the Draft was not stored ({admin.save_counts()})"
        admin.open_list(ROLE_EDITOR)
        admin.filter_entries(title)
        link = admin._row_locator(title).get_by_role("link", name="Preview")
        assert link.count(), f"{title!r}: the row offers no Preview link"
        url = control_panel_url(link.first.get_attribute("href"))
        page.goto(url, wait_until="domcontentloaded")
        try:
            wait_until(lambda: title in page.locator("body").inner_text(), timeout=wait_s, poll=1.0,
                       message="preview never showed the draft title")
        except WaitTimeoutError:
            pass
        assert title in page.locator("body").inner_text(), f"Preview ({url}) did not render the draft content within {wait_s}s"
        assert not probe(anon, title, False), f"{title!r} (Draft) leaked to the public page"
    finally:
        _verified_delete(admin, title)
        ctx.close()

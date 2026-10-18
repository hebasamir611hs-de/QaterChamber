"""
cms/tests/home_hero_banner/test_home_hero_banner_control_panel.py —
PBI 129367 (QC-HOME-001 — Hero Banner), suite 134447: the slide / counter
lifecycle cases that need the public Home Page (publish, unpublish, Active
Status, Display Order, draft, delete).

REWRITTEN 2026-10-18. The previous version drove the REAL seeded rows
(QCDEMO-129367-HERO_BANNER_SLIDE-01/-02, ACHIEVEMENT_COUNTER-03) through the
old HeroBannerSlideAdminPage as the default `page` session. On the 2026-10-18
run it left -02 and counter -03 Unpublished on the live site (re-published by
hand), its hard-coded baselines (Display Order 100/200/300) no longer matched
qcdev (1/2/30), and `.qc-hero-title` matched every slide. Per CLAUDE.md #8
every case now builds its own disposable `QCTEST-<tc>-*` slide / counter:

  - Account: Site Content Editor through `cms_role_credentials()` (an
    Editor's Submit for Review publishes directly — standards.md workflow).
  - Public reads: a fresh logged-out context, polling the Home Page until
    the expected state shows (the delivery cache lags a save).
  - Display Order: multiples of 100 at 9500+ so a QCTEST row sorts after
    every real row; the real slides / counters keep their order.
  - Teardown, every run: the QCTEST row is unpublished and deleted by exact
    title (QCTEST cleanup policy). No real row is written.
  - A QCTEST slide published with Active Status ticked is briefly visible to
    visitors in the carousel (same as the fields module's 135022).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import allure
import pytest

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_INACTIVE,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.home_hero_banner.hero_banner_fields_admin_page import (
    AchievementCounterFieldsAdminPage as Counter,
    HeroSlideFieldsAdminPage as Slide,
)
from cms.tests import authoring_checks as ac
from cms.tests.live_write_guard import LiveRecord, log_live_write
from config.settings import control_panel_url
from core.utils.waits import WaitTimeoutError, wait_until

pytestmark = [pytest.mark.control_panel, pytest.mark.pbi_129367]

HOME = "/en/home"
HERO = ".qc-home-hero-banner"
# QA lead 2026-10-18: a change that reaches visitors after more than 90 s
# (delivery cache) is not an issue, so the public poll waits up to 3 minutes.
PUBLIC_BUDGET_S = 180


# ---------------------------------------------------------------------------
# public Home Page reads (logged-out context)
# ---------------------------------------------------------------------------
def _load_home(anon) -> None:
    """Fresh Home load. The slides are rendered client-side after
    DOMContentLoaded: reading at once returned ZERO titles while the record
    was Published + Active (135014 / 135017, 2026-10-18), so wait for the
    first slide title before any read."""
    import time

    anon.goto(control_panel_url(f"{HOME}?_={int(time.time())}"), wait_until="domcontentloaded")
    anon.locator(HERO).first.wait_for(timeout=30000)
    try:
        anon.locator(f"{HERO} .qc-hero-title").first.wait_for(state="attached", timeout=20000)
    except Exception:  # noqa: BLE001 — an empty hero is itself what the caller reads
        pass


def _hero_text(anon) -> str:
    _load_home(anon)
    return anon.locator(HERO).first.evaluate("e => e.textContent.replace(/\\s+/g, ' ')")


def _slide_titles(anon) -> list[str]:
    _load_home(anon)
    return [t.strip() for t in anon.locator(f"{HERO} .qc-hero-title").evaluate_all(
        "els => els.map(e => e.textContent.replace(/\\s+/g, ' '))")]


def _until(check, what: str) -> bool:
    """Reload-poll the public page until `check()` holds; False on timeout."""
    try:
        wait_until(check, timeout=PUBLIC_BUDGET_S, poll=5, message=what)
        return True
    except WaitTimeoutError:
        return False


def _in_hero(anon, text: str, expect: bool = True) -> bool:
    """Whether `text` is in the hero section, polled until it matches `expect`."""
    _until(lambda: (text in _hero_text(anon)) == expect, f"hero never {'showed' if expect else 'dropped'} {text!r}")
    return text in _hero_text(anon)


def _before(anon, first: str, second: str, reader) -> bool:
    """Whether `first` renders before `second`, polled until it does. On a
    timeout the visitor's last sequence is attached."""
    last = {"seq": None}

    def _order() -> bool:
        seq = last["seq"] = reader(anon)
        a, b = _index(seq, first), _index(seq, second)
        return a >= 0 and b >= 0 and a < b

    ok = _until(_order, f"{first!r} never rendered before {second!r}")
    if not ok:
        seq = last["seq"]
        shown = seq if isinstance(seq, list) else (seq or "")[:600]
        allure.attach(f"wanted {first!r} before {second!r}; visitor saw: {shown}",
                      name="order at failed public check", attachment_type=allure.attachment_type.TEXT)
    return ok


def _index(seq, text: str) -> int:
    if isinstance(seq, str):
        return seq.find(text)
    return next((i for i, t in enumerate(seq) if text in t), -1)


# ---------------------------------------------------------------------------
# QCTEST slide / counter helpers (Editor)
# ---------------------------------------------------------------------------
def _publish(admin, title: str, tc: int, active: bool = True, extra: dict | None = None) -> None:
    admin.open_form(ROLE_EDITOR)
    admin.fill_required(title, active=active)
    # fill_required() writes the title only when the title field is required;
    # no Achievement Counter field is, so the counter would be saved untitled
    # (seen 2026-10-18) and could never be found by its QCTEST title.
    admin.fill(admin.TITLE_FIELD, title)
    for key, val in (extra or {}).items():
        if admin.spec(key).kind == "checkbox":
            admin.set_flag(key, bool(val))
        else:
            admin.fill(key, val)
    if admin.ACTIVE_FIELD in admin.FIELDS:
        assert admin.flag(admin.ACTIVE_FIELD) is active, \
            f"{title!r}: Active Status checkbox reads {admin.flag(admin.ACTIVE_FIELD)} before submit, asked {active}"
    log_live_write(LiveRecord(admin.SLUG, title, "disposable QCTEST record"), "<create>", title, tc,
                   action="publish", note=f"QCTEST row, Active={active}, {extra or {}}; deleted in finally")
    # Evidence for the duplicate-record question (2026-10-18: one submit left
    # two identical QCTEST rows twice): every non-GET /o/ call of the submit.
    calls: list[str] = []

    def _rec(req):
        if req.method != "GET" and "/o/" in req.url:
            calls.append(f"{req.method} {req.url.split('ihorizons.com')[-1][:120]}")

    admin.page.on("request", _rec)
    try:
        admin.submit_for_review()
        admin.page.wait_for_timeout(3000)  # the Arabic-twin PUT follows the save by ~10 s at most
    finally:
        admin.page.remove_listener("request", _rec)
        allure.attach("\n".join(calls) or "(none)", name="submit network calls",
                      attachment_type=allure.attachment_type.TEXT)
    rows = admin.open_list(ROLE_EDITOR)._search_rows(title)
    assert len(rows) <= 1, f"{title!r}: ONE Submit for Review stored {len(rows)} records {rows}; calls: {calls}"
    want = _expected(admin, active)
    status = _wait_status(admin, title, want)
    assert status in want, f"{title!r}: Editor Submit for Review left it {status or 'absent'!r}, expected {want}"


# Published, or Published with Active Status unticked, which the list badges
# INACTIVE (PBI running rules #17: not a bug while the visitor sees no difference).
# INACTIVE is accepted ONLY when the case itself unticked Active Status: with
# Active ticked it would hide an Active value that did not persist.
LIVE_STATUSES = (STATUS_PUBLISHED, STATUS_INACTIVE)


def _expected(admin, active: bool) -> tuple:
    if active or admin.ACTIVE_FIELD not in admin.FIELDS:
        return (STATUS_PUBLISHED,)
    return (STATUS_INACTIVE, STATUS_PUBLISHED)


def _wait_status(admin, title: str, want: tuple = LIVE_STATUSES, timeout: float = 60) -> str:
    """The row's status, re-read until it is one of `want` (a fresh record
    reaches the search index a few seconds after its save)."""
    seen = {"s": ""}

    def _live() -> bool:
        seen["s"] = admin.status_of(title, ROLE_EDITOR)
        return seen["s"] in want

    try:
        wait_until(_live, timeout=timeout, poll=5)
    except WaitTimeoutError:
        pass
    return seen["s"]


def _edit_published(admin, title: str, tc: int, changes: dict) -> None:
    """Edit a Published QCTEST row (Unpublish to edit as draft when the form
    is read-only) and submit it again as Editor."""
    admin.open_list(ROLE_EDITOR)
    admin.open_entry_by_edit_link(title)
    key0 = next(iter(changes))
    title_box = admin.page.get_by_role("textbox", name=admin.label_pattern(admin.spec(admin.TITLE_FIELD).label))
    if not title_box.first.is_editable():
        admin.unpublish_to_edit_as_draft()
    for key, val in changes.items():
        if admin.spec(key).kind == "checkbox":
            admin.set_flag(key, bool(val))
        else:
            admin.fill(key, val)
    active = admin.flag(admin.ACTIVE_FIELD) if admin.ACTIVE_FIELD in admin.FIELDS else True
    if admin.ACTIVE_FIELD in changes:
        assert active is bool(changes[admin.ACTIVE_FIELD]), \
            f"{title!r}: Active Status checkbox reads {active} before submit, asked {changes[admin.ACTIVE_FIELD]}"
    log_live_write(LiveRecord(admin.SLUG, title, "disposable QCTEST record"), key0, repr(changes), tc,
                   action="publish")
    admin.submit_for_review()
    want = _expected(admin, active)
    status = _wait_status(admin, title, want)
    assert status in want, f"{title!r}: re-submit after edit left it {status or 'absent'!r}, expected {want}"


def _diag(admin, anon, title: str) -> str:
    """State at a failed public check, read BEFORE teardown deletes the row:
    list status, Active Status read back from the form, the visitor's slide
    titles. Attached to the report and returned for the assertion message."""
    parts = []
    try:
        parts.append(f"status={admin.status_of(title, ROLE_EDITOR)!r}")
        admin.open_entry_by_edit_link(title)
        if admin.ACTIVE_FIELD in admin.FIELDS:
            parts.append(f"active_stored={admin.flag(admin.ACTIVE_FIELD)}")
    except Exception as exc:  # noqa: BLE001
        parts.append(f"admin read failed: {exc!r}"[:160])
    try:
        titles = _slide_titles(anon)
        parts.append(f"public slides={len(titles)} {titles}")
    except Exception as exc:  # noqa: BLE001
        parts.append(f"public read failed: {exc!r}"[:160])
    text = " | ".join(parts)
    allure.attach(text, name="state at failed public check", attachment_type=allure.attachment_type.TEXT)
    return text


def _assert_hero(admin, anon, title: str, expect: bool, msg: str) -> None:
    if _in_hero(anon, title, expect) != expect:
        raise AssertionError(f"{msg} — {_diag(admin, anon, title)}")


def _retire(admin, title: str, tc: int) -> None:
    """Teardown: every row whose stored title is exactly `title` (more than one
    if a submit duplicated it) is unpublished if Published, then deleted by
    its code. A row is touched only after its title is read back."""
    from cms.pages.components.object_authoring_page import ObjectAuthoringPage as OAP

    for _ in range(4):
        try:
            admin.open_list(ROLE_EDITOR)
            codes = admin._search_rows(title)
            if not codes:
                return
            code = codes[0]
            admin.open_entry_by_code(code)
            if admin.value(admin.TITLE_FIELD) != title:
                return
            admin.open_list(ROLE_EDITOR)
            admin._search_rows(title)
            record = LiveRecord(admin.SLUG, title, code)
            if admin.row_status_text_by_code(code) == STATUS_PUBLISHED:
                log_live_write(record, "<workflow>", "Unpublished", tc, action="unpublish", note="teardown")
                OAP._run_row_action(admin, code, "unpublish")
                admin.open_list(ROLE_EDITOR)
                admin._search_rows(title)
            log_live_write(record, "<delete>", code, tc, action="delete", note="teardown (QCTEST)")
            OAP._run_row_action(admin, code, "delete")
        except Exception:  # noqa: BLE001 — teardown never masks the result
            return


def _counter_extra(value: str, order: str = "9900", on: bool = True) -> dict:
    return {"value": value, "display_order": order, "counter_active": on}


# ---------------------------------------------------------------------------
# slides
# ---------------------------------------------------------------------------
@allure.title("Valid Banner Image on a new slide is accepted and stays attached")
@pytest.mark.functional_high
@pytest.mark.tc_135010
def test_uploading_valid_banner_image_on_new_slide_succeeds(page):
    """Account: Editor. A 1200x500 PNG is uploaded on a new QCTEST slide,
    saved as Draft and read back after reopening."""
    path = Path(tempfile.gettempdir()) / "QCTEST-135010-banner.png"
    from PIL import Image

    Image.new("RGB", (1200, 500), (30, 60, 120)).save(path, "PNG")
    ac.check_valid_persists(page, Slide, 135010, "image", str(path), short="img")


@allure.title("Saving a slide as Draft does not publish it to the Home Page")
@pytest.mark.functional_high
@pytest.mark.tc_135019
def test_save_as_draft_does_not_publish_to_frontend(page, browser):
    """Account: Editor. Draft with Active Status ticked, so only the workflow
    gate keeps it off the carousel."""
    admin = Slide(page)
    title = ac.run_title(135019, "draft")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved as Draft"
        _assert_hero(admin, anon, title, False, f"Draft slide {title!r} is visible to visitors")
    finally:
        ac._close(ctx)
        _retire(admin, title, 135019)


@allure.title("Unpublishing a slide removes it from the Home Page")
@pytest.mark.functional_high
@pytest.mark.tc_135023
def test_unpublishing_slide_removes_it_from_home_page(page, browser):
    admin = Slide(page)
    title = ac.run_title(135023, "unpub")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish(admin, title, 135023)
        _assert_hero(admin, anon, title, True, f"precondition: published slide {title!r} is not on the Home Page")
        admin.open_list(ROLE_EDITOR)
        admin.unpublish_entry(title)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_UNPUBLISHED, f"{title!r} is not Unpublished"
        _assert_hero(admin, anon, title, False, f"Unpublished slide {title!r} is still on the Home Page")
    finally:
        ac._close(ctx)
        _retire(admin, title, 135023)


@allure.title("Re-publishing a previously unpublished slide restores it on the Home Page")
@pytest.mark.functional_high
@pytest.mark.tc_135024
def test_republishing_previously_unpublished_slide_restores_it(page, browser):
    """Publish -> Unpublish (gone) -> the row's Publish action -> back."""
    admin = Slide(page)
    title = ac.run_title(135024, "repub")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish(admin, title, 135024)
        _assert_hero(admin, anon, title, True, f"precondition: published slide {title!r} is not on the Home Page")
        admin.open_list(ROLE_EDITOR)
        admin.unpublish_entry(title)
        status = _wait_status(admin, title, (STATUS_UNPUBLISHED,))
        assert status == STATUS_UNPUBLISHED, f"{title!r} is {status!r} after Unpublish, not Unpublished"
        _assert_hero(admin, anon, title, False, f"precondition: {title!r} still shown after unpublish")
        admin.open_list(ROLE_EDITOR)
        admin.code_for(title)  # list filtered to the row, so its Publish action is on screen
        admin.publish_entry(title)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED, f"{title!r} was not re-published"
        _assert_hero(admin, anon, title, True, f"re-published slide {title!r} did not reappear on the Home Page")
    finally:
        ac._close(ctx)
        _retire(admin, title, 135024)


@allure.title("Enabling a slide's Active Status makes it appear on the Home Page")
@pytest.mark.functional_high
@pytest.mark.tc_135016
def test_enabling_slide_active_status_makes_it_eligible(page, browser):
    admin = Slide(page)
    title = ac.run_title(135016, "act-on")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish(admin, title, 135016, active=False)
        _assert_hero(admin, anon, title, False, f"precondition: inactive slide {title!r} is shown")
        _edit_published(admin, title, 135016, {"active_status": True})
        _assert_hero(admin, anon, title, True, f"slide {title!r} did not appear after Active Status was ticked")
    finally:
        ac._close(ctx)
        _retire(admin, title, 135016)


@allure.title("Disabling a slide's Active Status removes it from the Home Page")
@pytest.mark.functional_high
@pytest.mark.tc_135017
def test_disabling_slide_active_status_removes_it(page, browser):
    admin = Slide(page)
    title = ac.run_title(135017, "act-off")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish(admin, title, 135017, active=True)
        _assert_hero(admin, anon, title, True, f"precondition: active published slide {title!r} is not shown")
        _edit_published(admin, title, 135017, {"active_status": False})
        _assert_hero(admin, anon, title, False, f"slide {title!r} still shown with Active Status off")
    finally:
        ac._close(ctx)
        _retire(admin, title, 135017)


def _two_slides(admin, tc: int):
    a, b = ac.run_title(tc, "A"), ac.run_title(tc, "B")
    _publish(admin, a, tc, extra={"display_order": "9800"})
    _publish(admin, b, tc, extra={"display_order": "9900"})
    return a, b


@allure.title("Changing a slide's Display Order updates its position in the slider")
@pytest.mark.functional_high
@pytest.mark.timeout(1500)  # two slides + three public polls of up to 3 min each
@pytest.mark.tc_135014
def test_changing_slide_display_order_updates_frontend_position(page, browser):
    """Two QCTEST slides A=9800, B=9900; B is moved to 9700 and must render
    before A."""
    admin = Slide(page)
    ctx, anon = ac._anon_page(browser)
    a = b = ""
    try:
        a, b = _two_slides(admin, 135014)
        assert _before(anon, a, b, _slide_titles), f"precondition: {a!r} is not before {b!r}"
        _edit_published(admin, b, 135014, {"display_order": "9700"})
        assert _before(anon, b, a, _slide_titles), f"{b!r} (Display Order 9700) does not render before {a!r}"
    finally:
        ac._close(ctx)
        for t in (a, b):
            if t:
                _retire(admin, t, 135014)


@allure.title("Reverting a slide's Display Order restores its original position")
@pytest.mark.functional_low
@pytest.mark.timeout(1500)  # two slides + three public polls of up to 3 min each
@pytest.mark.tc_135015
def test_reverting_slide_display_order_restores_frontend_position(page, browser):
    """A=9800, B=9900 -> B=9700 (B first) -> B back to 9900 (A first again)."""
    admin = Slide(page)
    ctx, anon = ac._anon_page(browser)
    a = b = ""
    try:
        a, b = _two_slides(admin, 135015)
        _edit_published(admin, b, 135015, {"display_order": "9700"})
        assert _before(anon, b, a, _slide_titles), f"precondition: {b!r} was not moved before {a!r}"
        _edit_published(admin, b, 135015, {"display_order": "9900"})
        assert _before(anon, a, b, _slide_titles), f"reverted order not restored: {a!r} is not before {b!r}"
    finally:
        ac._close(ctx)
        for t in (a, b):
            if t:
                _retire(admin, t, 135015)


@allure.title("Deleting a slide removes it from the CMS and the Home Page")
@pytest.mark.functional_high
@pytest.mark.tc_135018
def test_delete_slide_removes_from_cms_and_public_site(page, browser):
    """Deletes ONLY its own QCTEST slide, by exact title (user approval
    2026-10-18 for QCTEST deletes on this case)."""
    admin = Slide(page)
    title = ac.run_title(135018, "del")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish(admin, title, 135018)
        _assert_hero(admin, anon, title, True, f"precondition: {title!r} is not on the Home Page")
        log_live_write(LiveRecord(admin.SLUG, title, "disposable QCTEST record"), "<delete>", title, 135018,
                       action="delete")
        assert admin.delete_disposable(title), f"{title!r}: delete did not run"
        assert not admin.entry_exists(title, ROLE_EDITOR), f"{title!r} is still in the CMS list"
        _assert_hero(admin, anon, title, False, f"deleted slide {title!r} is still on the Home Page")
    finally:
        ac._close(ctx)
        _retire(admin, title, 135018)


# ---------------------------------------------------------------------------
# achievement counters
# ---------------------------------------------------------------------------
@allure.title("Enabling a Counter's Active Status makes it appear on the Home Page")
@pytest.mark.functional_high
@pytest.mark.tc_135026
def test_enabling_counter_active_status_makes_it_appear(page, browser):
    admin = Counter(page)
    title = ac.run_title(135026, "on")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish(admin, title, 135026, active=True, extra=_counter_extra("71+", on=False))
        _assert_hero(admin, anon, title, False, f"precondition: inactive counter {title!r} is shown")
        _edit_published(admin, title, 135026, {"counter_active": True})
        _assert_hero(admin, anon, title, True, f"counter {title!r} did not appear after Counter Active Status was ticked")
    finally:
        ac._close(ctx)
        _retire(admin, title, 135026)


@allure.title("Disabling a Counter's Active Status removes it from the Home Page")
@pytest.mark.functional_high
@pytest.mark.tc_135027
def test_disabling_counter_active_status_removes_it(page, browser):
    admin = Counter(page)
    title = ac.run_title(135027, "off")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish(admin, title, 135027, active=True, extra=_counter_extra("72+"))
        _assert_hero(admin, anon, title, True, f"precondition: active counter {title!r} is not shown")
        _edit_published(admin, title, 135027, {"counter_active": False})
        _assert_hero(admin, anon, title, False, f"counter {title!r} still shown with Counter Active off")
    finally:
        ac._close(ctx)
        _retire(admin, title, 135027)


def _two_counters(admin, tc: int):
    a, b = ac.run_title(tc, "A"), ac.run_title(tc, "B")
    _publish(admin, a, tc, active=True, extra=_counter_extra("81+", "9800"))
    _publish(admin, b, tc, active=True, extra=_counter_extra("82+", "9900"))
    return a, b


@allure.title("Changing a Counter's Display Order updates its position in the row")
@pytest.mark.functional_low
@pytest.mark.tc_135028
def test_changing_counter_display_order_updates_frontend_position(page, browser):
    admin = Counter(page)
    ctx, anon = ac._anon_page(browser)
    a = b = ""
    try:
        a, b = _two_counters(admin, 135028)
        assert _before(anon, a, b, _hero_text), f"precondition: counter {a!r} is not before {b!r}"
        _edit_published(admin, b, 135028, {"display_order": "9700"})
        assert _before(anon, b, a, _hero_text), f"counter {b!r} (order 9700) does not render before {a!r}"
    finally:
        ac._close(ctx)
        for t in (a, b):
            if t:
                _retire(admin, t, 135028)


@allure.title("Reverting a Counter's Display Order restores its original position")
@pytest.mark.functional_low
@pytest.mark.tc_135029
def test_reverting_counter_display_order_restores_frontend_position(page, browser):
    admin = Counter(page)
    ctx, anon = ac._anon_page(browser)
    a = b = ""
    try:
        a, b = _two_counters(admin, 135029)
        _edit_published(admin, b, 135029, {"display_order": "9700"})
        assert _before(anon, b, a, _hero_text), f"precondition: counter {b!r} was not moved before {a!r}"
        _edit_published(admin, b, 135029, {"display_order": "9900"})
        assert _before(anon, a, b, _hero_text), f"reverted counter order not restored: {a!r} not before {b!r}"
    finally:
        ac._close(ctx)
        for t in (a, b):
            if t:
                _retire(admin, t, 135029)

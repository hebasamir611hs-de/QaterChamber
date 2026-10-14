"""
UPDATE 2026-10-13 (P3/P4 batch -- user decision, read this first): with
QC_ALLOW_LIVE_SINGLETON_WRITES=1 the write guard below OPENS for this
module's real singleton (cms/tests/live_write_guard.py): tests write test
data to it, never delete anything, log every persisted write to
reports/live-writes-20261013.jsonl, and leave the record Published. Without
the variable nothing changes (NOT APPLICABLE). Only this batch's test cases
open it (live_write_guard.P34_BATCH_TCS); P1/P2 tests stay NOT APPLICABLE.
P1/P2 RERUN 2026-10-13 (user decision, supersedes that last clause): the
rerun ids (live_write_guard.P12_BATCH_TCS) open it too, plus the real About
Hero Banner rows; their writes are logged first, nothing is deleted (QCTEST
rows are kept and logged), and a record left Unpublished / Draft / Pending
Review is re-published in `finally` (cms/tests/live_end_published.py).
The P3/P4 cases are scripted OFFLINE, not yet executed -- search for
"P3/P4 BATCH".

cms/tests/chairman_message/test_chairman_message_control_panel.py — the 40
Automation-tagged Control_Panel cases of PBI 129393 (QC-ABOUT-002, Chairman's
Message), from .claude/qa-runs/phase3-20261012/129393.todo.json. The Azure
title, steps and expected results are the oracle.

Scripted 2026-10-12, OFFLINE (no browser was available). Not yet executed.
Every `# VERIFY-LIVE:` marks an assumption to confirm on the first run.

Records
-------
* **Chairman Message Page** singleton `QCDEMO-129393-chairmans-message`
  (row 78261). TEST_OWNED, restored ONCE per run (user decision 2026-10-12):
  the `_singleton_baseline` module fixture (chairman_singleton.py, engine in
  cms/tests/singleton_baseline.py) captures every field EN/AR, Message Content
  as exact HTML (CKEditor `getData()/setData()` -- re-typing would flatten the
  live headings and links), the portrait file name + bytes, and the status to
  reports/backups/129393_chairman_message_<stamp>/ before the first
  CHAIRMAN_GROUP test, heals from an interrupted run's snapshot first, and
  restores + verifies by re-read once after the last. Per test, the gate only
  normalises the STATUS back to Published; `_test_owned()` is a runtime read
  of the values a test compares against and restores nothing. Killed run:
  `python tools/restore_singleton.py --pbi 129393`.
  All of these cases share `xdist_group("chairman_message_78261")`, the same
  group as the legacy module web/tests/about_chairman_message/
  test_chairman_message_control_panel.py, so the two never mutate 78261 at the
  same time. That legacy module duplicates 6 of these cases and should be
  retired.
* **About Hero Banner** (Guide §24: the page's banner lives here, not in the
  Chairman object's unused `heroBannerImage`). Hero field cases run on
  disposable `QCTEST-<tc>-HERO` rows. No page renders that page key. They are
  deleted by exact title on every run. TC 134760 alone reads and writes the real
  `chairman-message` row; that row is in the module snapshot, restored once.

Accounts: Site Content Editor for lifecycle and field work, Site Content Author
for 134771/134772, and the site-member account for 134773. All are resolved
through `cms_role_credentials()`, never TEST_USER. "Save" in a case means
Submit for Review as Editor, because Save as Draft skips required-field
validation. A published record has to be unpublished before it can be edited
(OBJECT-AUTHORING-GUIDE §4). Public checks run in a fresh logged-out context.

Wait budget per test, under the 300 s timeout: the gate's status step (at most
one publish confirm, 75 s), one publish confirm (75 s), one public poll (60 s),
plus navigation. No restore runs inside a test any more.

Upload sizes: by project rule, up to 3 MB accepted is OK. The oversize
assertions therefore use 3.1 MB. A 2.1 MB file is not asserted on.

Wording such as toasts and exact error text is attached to Allure, not asserted.
The behaviour is what is asserted: refusal, nothing persisted, and the status.

UPDATE 2026-10-13 (user decision -- supersedes the TEST_OWNED notes above):
automation no longer writes to the real singleton 78261 nor to the real About
Hero Banner `chairman-message` row. Every case that needs a saved / published /
unpublished change calls cms.tests.live_write_guard.block_live_singleton_write()
right before its first persisting step and is reported NOT APPLICABLE. On this
record that includes the refusal cases: every field edit here first needs
"Unpublish to edit as draft" (guide section 4), a successful status change on
the live record, so they are NOT APPLICABLE at that unpublish while the record
is Published. Read-only role / denial cases run fully. The `_singleton_baseline`
module fixture and the per-test `_singleton_gate` are NO LONGER WIRED (engine
kept in chairman_singleton.py / singleton_baseline.py). QCTEST hero rows run
only if a real, empty About Hero Banner create form exists; it is hidden on
qcdev, so those cases are NOT APPLICABLE too.
"""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path

import allure
import pytest

from cms.pages.chairman_message.chairman_message_admin_page import (
    CHAIRMAN_MESSAGE_ENTRY_CODE,
    HERO_PAGE_KEY,
    ChairmanHeroBannerAdminPage,
    ChairmanMessageAdminPage,
)
from cms.pages.components.disposable_object_admin import (
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_SITE_MEMBER,
    DisposableObjectAdminPage,
)
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.about_qatar_chamber.about_qatar_chamber_admin_page import AboutQatarChamberAdminPage
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import web_url
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from tools.fixture_factory import make_gif, make_jpg, make_png, make_svg
from cms.tests.chairman_message.chairman_singleton import (
    locales as _locales,
    make_editable as _make_editable,
    publish as _publish,
    read_field as _read,
    submit_form as _submit_form,
    write_field as _write,
)
from cms.tests.live_end_published import leave_published
from cms.tests.live_write_guard import (
    block_live_singleton_write,
    deletes_suppressed,
    log_live_write,
    refuse_hero_create,
    stop_unless_refused,
)
from web.pages.about_chairman_message.chairman_message_page import (
    CHAIRMAN_MESSAGE_PATH,
    ChairmanMessagePage,
)


PBI = "129393"
CHAIRMAN_GROUP = pytest.mark.xdist_group("chairman_message_78261")
# NOT WIRED (user decision 2026-10-13): `module_baseline_fixture(build_baseline)`
# and `singleton_gate("chairman_message_78261")` both write to 78261 / the
# chairman-message hero row (gate: approve/publish before every test; fixture:
# module-end restore). No test writes to them any more.
RECORD = "Chairman Message Page 78261 (QCDEMO-129393-chairmans-message)"
HERO_RECORD = "About Hero Banner row QCDEMO-ABOUT-HERO-chairman-message (one row per page)"
HERO_QCTEST_DESC = "About Hero Banner (one row per page; no visible empty create form for a QCTEST row)"
HERO_QCTEST_GROUP = pytest.mark.xdist_group("about_hero_qctest_129393")

PUBLISH_TIMEOUT = 75.0
UNPUBLISH_TIMEOUT = 30.0
PUBLIC_TIMEOUT = 60.0
ONE_MB = 1024 * 1024
AR = "ar"
EN = "en"

CASE_TITLE = "Chairman's Message"
CASE_NAME = "H.E. Sheikh Khalifa bin Jassim bin Mohammed Al Thani"
CASE_DESIGNATION = "Chairman of The Board"
CASE_PORTRAIT_ALT = "Chairman Sheikh Khalifa bin Jassim Al Thani"
CASE_HERO_ALT = "Qatar Chamber board room"
QC_URL = "https://www.qatarchamber.com"


# ---------------------------------------------------------------------------
# generic helpers
# ---------------------------------------------------------------------------
def _attach(name: str, data) -> None:
    try:
        allure.attach(str(data), name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:  # noqa: BLE001 — reporting never masks a result
        pass


def _fixture(name: str, maker, size: int) -> str:
    """Generates a sized fixture into the temp dir (no committed binaries)."""
    folder = Path(tempfile.gettempdir()) / "qc_chairman_message_129393"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    if not path.exists() or path.stat().st_size != size:
        path.write_bytes(maker(size))
    return str(path)


def _qctest_copy(path: str, tag: str) -> str:
    """Uniquely named `QCTEST-<tag>-<hex>.<ext>` copy for Documents & Media."""
    return DisposableObjectAdminPage.disposable_copy(path, tag)


def _stem(path: str) -> str:
    return Path(path).stem


def _wait(check, timeout: float, message: str) -> bool:
    try:
        wait_until(check, timeout=timeout, poll=2.0, message=message)
        return True
    except WaitTimeoutError:
        return False


# ---------------------------------------------------------------------------
# singleton record: read / write / lifecycle
# ---------------------------------------------------------------------------
# `_read` / `_write` / `_locales` / `_make_editable` / `_publish` are imported
# from chairman_singleton.py, which the module-end restore shares.


def _snapshot(admin: ChairmanMessageAdminPage, keys) -> dict:
    admin.open_record()
    snap = {"status": admin.current_status(), "fields": {}}
    for key in keys:
        for loc in _locales(key):
            snap["fields"][(key, loc)] = _read(admin, key, loc)
    _attach("current values (runtime read)", snap)
    return snap


@contextmanager
def _test_owned(page, keys, label: str):
    """Editor session on the singleton; RUNTIME read of `keys` + status,
    yields (admin, current values). Restores no field values (user decision
    2026-10-12). `label` stays for call-site compatibility.

    P1/P2 RERUN 2026-10-13 (user decision): when the write gate opened for
    78261 in this test, the record is driven back to Published in `finally`
    (Unpublished -> row action `[data-qc-oel-publish]`, verified on a fresh
    list read; logged first) -- live_end_published.leave_published."""
    admin = ChairmanMessageAdminPage(page)
    admin.sign_in(ROLE_EDITOR)
    with _end_published(admin, None):
        yield admin, _snapshot(admin, keys)


def _end_published(admin: ChairmanMessageAdminPage, tc):
    def _submit_draft() -> None:
        admin.open_record()
        _submit_form(admin)

    return leave_published(RECORD, lambda: admin.open_entries_list(locale=EN),
                           CHAIRMAN_MESSAGE_ENTRY_CODE, _submit_draft, tc)


def _logged_make_editable(admin: ChairmanMessageAdminPage, tc: str, note: str = "") -> None:
    """_make_editable(), with the row Unpublish logged BEFORE it is clicked
    (only a Published / Pending Review record is moved)."""
    admin.open_record()
    if admin.current_status() in (STATUS_PUBLISHED, STATUS_PENDING_REVIEW):
        log_live_write(RECORD, "<workflow>", STATUS_UNPUBLISHED, tc, action="unpublish",
                       note=note or "make the form editable (row Unpublish; re-published in finally)")
    _make_editable(admin)


# ---------------------------------------------------------------------------
# public surface (fresh logged-out context)
# ---------------------------------------------------------------------------
@contextmanager
def _visitor(browser):
    ctx = new_context(browser, use_auth_state=False)
    try:
        yield ChairmanMessagePage(ctx.new_page())
    finally:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


def _public(pub: ChairmanMessagePage, check, expect: bool = True, timeout: float = PUBLIC_TIMEOUT):
    """Reloads the public page until `check(pub)` == expect or timeout; a page
    that does not render counts as "not showing". Returns the last value."""
    seen = {"v": not expect}

    def _poll() -> bool:
        try:
            pub.open(web_url(CHAIRMAN_MESSAGE_PATH))
            seen["v"] = check(pub)
        except Exception:  # noqa: BLE001 — not rendered
            seen["v"] = False if isinstance(expect, bool) else None
        return seen["v"] == expect

    _wait(_poll, timeout, "public Chairman's Message page never matched")
    return seen["v"]


def _public_once(pub: ChairmanMessagePage, read):
    """One load of the public page and one read; "" when it does not render."""
    try:
        pub.open(web_url(CHAIRMAN_MESSAGE_PATH))
        return read(pub)
    except Exception:  # noqa: BLE001
        return ""


def _body(pub: ChairmanMessagePage) -> str:
    return pub.text("body")


# ---------------------------------------------------------------------------
# field-case helpers (one per field type)
# ---------------------------------------------------------------------------
def _valid_value(page, tc: str, key: str, value: str, locale: str = EN) -> None:
    with _test_owned(page, (key,), f"tc_{tc}") as (admin, snap):
        block_live_singleton_write(RECORD, f"unpublish + publish of {key} ({locale}) = {value[:60]!r}")
        if snap["fields"][(key, locale)] == value:
            # Restore-once (2026-10-12): state carries over between cases.
            with allure.step(f"Interim write: {key} ({locale}) already reads the case's value"):
                _attach("note", "field already held the case's value; interim QCTEST value saved first")
                _make_editable(admin)
                _write(admin, key, f"QCTEST-{tc} interim", locale)
                _publish(admin)
        with allure.step(f"Enter {value[:60]!r} in {key} ({locale}) and Save (Submit for Review as Editor)"):
            _make_editable(admin)
            _write(admin, key, value, locale)
            _publish(admin)
        with allure.step("Reload the record"):
            admin.open_record()
            stored = _read(admin, key, locale)
        assert stored == value, f"{key} ({locale}) reads {stored!r}, expected {value!r}"


def _empty_refused(page, tc: str, key: str, locale: str = EN, also_ar_ui: bool = False) -> None:
    with _test_owned(page, (key,), f"tc_{tc}") as (admin, snap):
        baseline = snap["fields"][(key, locale)]
        assert baseline.strip(), f"precondition: {key} ({locale}) is empty on the live record"
        uis = (EN, AR) if also_ar_ui else (EN,)
        outcomes = {}
        for ui in uis:
            with allure.step(f"[{ui.upper()} interface] Clear {key} ({locale}) and Save"):
                if snap["status"] == STATUS_PUBLISHED:
                    # Editing first needs "Unpublish to edit as draft" -- a
                    # SUCCESSFUL status change on the live record (2026-10-13).
                    block_live_singleton_write(RECORD, f"setup Unpublish before clearing {key} ({locale})")
                _logged_make_editable(admin, tc)
                status_before = admin.current_status()
                if ui == AR:
                    admin.open_record(locale=AR)
                _write(admin, key, "", locale)
                log_live_write(RECORD, f"{key} ({locale})", "", tc, action="attempt",
                               note=f"[{ui.upper()} UI] Save with the field empty; expected REFUSED")
                # Label-independent (value="0") in BOTH interfaces (FIX
                # 2026-10-13, 134793/134821): after the setup Unpublish the
                # record is Unpublished, whose value=0 control reads "Save
                # Changes" -- the "Submit for Review"/"Publish" text match
                # found nothing and timed out after 30 s.
                admin.submit_via(admin.PUBLISH_SUBMIT)
                outcomes[ui] = {"refused": admin.refusal_visible(), "text": admin.refusal_text()}
            with allure.step("Reload the record"):
                admin.open_record()
                outcomes[ui]["after"] = _read(admin, key, locale)
                outcomes[ui]["status"] = admin.current_status()
                outcomes[ui]["status_before"] = status_before
            stop_unless_refused(
                outcomes[ui]["after"] == baseline and outcomes[ui]["status"] == status_before, RECORD,
                f"[{ui.upper()} UI] Save with an empty {key} ({locale})", outcomes[ui])
        _attach("outcomes (wording recorded, not asserted)", outcomes)
        for ui, out in outcomes.items():
            assert out["refused"], f"[{ui}] empty {key} ({locale}) was not refused on Save"
            assert out["after"] == baseline, f"[{ui}] {key} ({locale}) changed to {out['after']!r}"
            assert out["status"] == out["status_before"], (
                f"[{ui}] record status moved {out['status_before']!r} -> {out['status']!r}")


def _message_with(baseline_html: str, marker_html: str) -> str:
    return f"{baseline_html}{marker_html}"


# ---------------------------------------------------------------------------
# About Hero Banner — disposable QCTEST rows
# ---------------------------------------------------------------------------
def _hero_key(tc: str) -> str:
    return f"QCTEST-{tc}-HERO"


def _hero(page) -> ChairmanHeroBannerAdminPage:
    hero = ChairmanHeroBannerAdminPage(page)
    hero.sign_in(ROLE_EDITOR)
    return hero


def _hero_create(hero: ChairmanHeroBannerAdminPage, key: str, image: str | None, alt: str,
                 publish: bool = True) -> dict:
    _hero_cleanup(hero, key)  # sweep a leftover from a dead run
    # User decision 2026-10-13: one row per page, create form hidden -> a
    # QCTEST row can only be made through a genuine, EMPTY create form; else
    # the case needs the real row and is NOT APPLICABLE.
    try:
        hero.open_new()
    except Exception as exc:  # noqa: BLE001
        refuse_hero_create(HERO_QCTEST_DESC, f"create form did not render: {exc!r}")
    if not AboutQatarChamberAdminPage(hero.page).hero_create_form_usable():
        refuse_hero_create(HERO_QCTEST_DESC, f"url {hero.page.url} is not an EMPTY create form")
    hero.fill_page_key(key)
    if image:
        hero.upload_file(hero.IMAGE_LABEL, image)
    hero.fill_alt_text(alt)
    if publish:
        hero.submit_for_review()
    else:
        hero.save_as_draft()
    said = {"refused": hero.refusal_visible(), "text": hero.refusal_text()}
    said["listed"] = hero.entry_exists(key, ROLE_EDITOR)
    said["status"] = hero.row_status_text(key) if said["listed"] else ""
    _attach("hero save outcome", said)
    return said


def _hero_cleanup(hero: ChairmanHeroBannerAdminPage, key: str) -> None:
    """Exact-key QCTEST teardown -- skipped under the opt-in (user decision
    2026-10-13: nothing is deleted). No QCTEST hero row can be created any
    more (refuse_hero_create), so there is nothing to keep or log."""
    if deletes_suppressed():
        _attach("hero cleanup skipped", f"{key}: deletes suppressed (QC_ALLOW_LIVE_SINGLETON_WRITES=1)")
        return
    hero.delete_disposable(key)


def _hero_open(hero: ChairmanHeroBannerAdminPage, key: str, locale: str = EN) -> ChairmanHeroBannerAdminPage:
    return hero.open_by_key(key, locale)


# ===========================================================================
# Rendering / lifecycle cases
# ===========================================================================
@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Rich text")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the message rich text renders headings, paragraphs, bullets, and inline links")
@allure.label("pbi", PBI)
@allure.label("testcase", "134759")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.tc_134759
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134759")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134759_message_rich_text_renders_all_element_types(page, browser):
    html = ("<h2>QCTEST-134759 Heading</h2><p>QCTEST-134759 paragraph one.</p>"
            "<p>QCTEST-134759 paragraph two.</p><ul><li>QCTEST item 1</li><li>QCTEST item 2</li>"
            f"<li>QCTEST item 3</li></ul><p><a href=\"{QC_URL}\">QCTEST-134759 link</a></p>")
    with _test_owned(page, ("message",), "tc_134759") as (admin, _snap):
        with allure.step("Set Message Content (EN) to heading + 2 paragraphs + 3 bullets + 1 link and publish"):
            block_live_singleton_write(RECORD, "unpublish + publish of Message Content (EN)")
            _make_editable(admin)
            admin.set_message_html(html, EN)
            _publish(admin)
        with _visitor(browser) as pub:
            with allure.step("Open the public page in English and inspect the message block"):
                shown = _public(pub, lambda p: "QCTEST-134759 paragraph two." in _body(p))
                links = pub.body_links() if shown else []
                body = _body(pub) if shown else ""
            assert shown, "the published rich text never reached the public page"
            assert "QCTEST-134759 Heading" in body and "QCTEST-134759 paragraph one." in body
            assert pub.body_list_count() >= 1, "no bulleted list rendered in the message body"
            for item in ("QCTEST item 1", "QCTEST item 2", "QCTEST item 3"):
                assert item in body, f"bullet {item!r} not rendered"
            assert any(lk["text"] == "QCTEST-134759 link" and (lk["href"] or "").rstrip("/") == QC_URL
                       for lk in links), f"inline link not rendered as an anchor to {QC_URL}: {links!r}"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Alt text")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that both the Hero Banner and the Chairman Portrait expose their configured alt text")
@allure.label("pbi", PBI)
@allure.label("testcase", "134760")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.accessibility
@pytest.mark.pbi_129393
@pytest.mark.tc_134760
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134760")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134760_hero_and_portrait_expose_their_alt_text(page, browser):
    # Two TEST_OWNED records: the singleton (portrait alt) and the REAL
    # About Hero Banner row for page key `chairman-message` (hero alt),
    # resolved by exact page key, never by position. Both are in the module
    # snapshot and restored once at module end -- no per-test restore.
    hero = ChairmanHeroBannerAdminPage(page)
    with _test_owned(page, ("portrait_alt",), "tc_134760") as (admin, _snap):
        with allure.step("Open the real chairman-message hero row"):
            hero.open_by_key(HERO_PAGE_KEY)
            _attach("hero row (runtime read)", {"alt": hero.alt_text(), "status": hero.current_status()})
        with allure.step(f"Set Hero Banner Alt Text to {CASE_HERO_ALT!r} and publish"):
            block_live_singleton_write(HERO_RECORD, "unpublish + publish of Banner Image Alt Text")
            if hero.current_status() == STATUS_PUBLISHED:
                hero.unpublish_to_edit_as_draft()
                _wait(lambda: hero.reopen().current_status() != STATUS_PUBLISHED, UNPUBLISH_TIMEOUT, "hero")
            hero.fill_alt_text(CASE_HERO_ALT)
            hero.publish()
            hero.wait_for_status(STATUS_PUBLISHED, timeout=PUBLISH_TIMEOUT)
        with allure.step(f"Set Chairman Portrait Alt Text to {CASE_PORTRAIT_ALT!r} and publish"):
            _make_editable(admin)
            admin.set_text("portrait_alt", CASE_PORTRAIT_ALT, EN)
            _publish(admin)
        with _visitor(browser) as pub:
            with allure.step("Inspect both alt values on the public page"):
                hero_alt = _public(pub, lambda p: p.hero_accessible_label(), expect=CASE_HERO_ALT)
                portrait_alt = pub.portrait_alt_text()
        assert hero_alt == CASE_HERO_ALT, f"Hero Banner alt reads {hero_alt!r}"
        assert portrait_alt == CASE_PORTRAIT_ALT, f"Chairman Portrait alt reads {portrait_alt!r}"
        assert hero_alt != portrait_alt


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that a Site Content Editor can create, edit, preview, publish, and unpublish the Chairman's Message page")
@allure.label("pbi", PBI)
@allure.label("testcase", "134770")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134770
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134770")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134770_site_content_editor_full_lifecycle(page):
    # Account: QC Site Content Editor. "Create" on a singleton is the edit of
    # its one record (singletons offer no add-new entry).
    with _test_owned(page, ("page_title",), "tc_134770") as (admin, _snap):
        with allure.step("Open the record as Site Content Editor"):
            admin.open_record()
            controls = admin.control_state()
            _attach("controls on open", controls)
        assert controls["unpublish"] == (True, True), f"Unpublish control not enabled: {controls!r}"
        with allure.step(f"Edit Page Title (EN) to {CASE_TITLE!r} and save as draft"):
            block_live_singleton_write(RECORD, "Editor unpublish / save draft / publish / unpublish")
            _logged_make_editable(admin, "134770")
            admin.set_text("page_title", CASE_TITLE, EN)
            log_live_write(RECORD, "Page Title (EN)", CASE_TITLE, "134770", action="save-draft",
                           note="Save as Draft")
            admin.save_as_draft()
        with allure.step("Preview"):
            admin.open_entries_list(locale=EN)
            url = admin.row_preview_url_by_code(CHAIRMAN_MESSAGE_ENTRY_CODE)
            banner = admin.preview_banner_text(url) if url else ""
            preview_body = admin.body_text() if url else ""
        assert url, "the record row offers no Preview link"
        assert banner, "Preview did not render its preview banner"
        assert "Access Denied" not in preview_body
        with allure.step("Publish"):
            admin.open_record()
            log_live_write(RECORD, "<form submit>", f"Page Title (EN) = {CASE_TITLE}", "134770",
                           action="publish", note="Submit for Review as Site Content Editor")
            _publish(admin)
        with allure.step("Unpublish"):
            admin.open_record()
            log_live_write(RECORD, "<workflow>", STATUS_UNPUBLISHED, "134770", action="unpublish",
                           note="the case's Unpublish step (re-published in finally)")
            admin.unpublish_to_edit_as_draft()
            admin.wait_for_status(STATUS_UNPUBLISHED, timeout=UNPUBLISH_TIMEOUT)
            assert "Access Denied" not in admin.body_text()


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that a Site Content Author can view and update assigned Chairman's Message content")
@allure.label("pbi", PBI)
@allure.label("testcase", "134771")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134771
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134771")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134771_site_content_author_can_update_message(page):
    # Account: QC Site Content Author. Restore runs as Editor (approves a
    # Pending Review version first if the Author's save produced one).
    marker = "<p>QCTEST-134771 author update</p>"
    with _test_owned(page, ("message",), "tc_134771") as (admin, snap):
        with allure.step("Sign in as Site Content Author and open the record"):
            admin.sign_in(ROLE_AUTHOR)
            assert not admin.has_admin_toolbar(), "precondition: session is not the Author role"
            admin.open_record()
            controls = admin.control_state()
            _attach("Author controls", controls)
        assert controls["save_draft"][1] or controls["unpublish"][1], (
            f"the record did not open in editable mode for the Author: {controls!r}")
        with allure.step("Update Message Content (EN) and save"):
            block_live_singleton_write(RECORD, f"Author's Message Content save; controls {controls}")
            if controls["unpublish"][1] and not controls["save_draft"][1]:
                admin.unpublish_to_edit_as_draft()
                admin.open_record()
            admin.set_message_html(_message_with(snap["fields"][("message", EN)], marker), EN)
            admin.save_as_draft()
            denied = "Access Denied" in admin.body_text()
        with allure.step("Re-open as the Author"):
            admin.open_record()
            stored = admin.message_html(EN)
        assert not denied, "Access Denied shown to the Author on save"
        assert "QCTEST-134771 author update" in stored, "the Author's change was not saved"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that a Site Content Author cannot publish the Chairman's Message page")
@allure.label("pbi", PBI)
@allure.label("testcase", "134772")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129393
@pytest.mark.tc_134772
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134772")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134772_site_content_author_cannot_publish(page):
    # Account: QC Site Content Author. The live record is Published, so the
    # "attempt" is made through every publish-capable control the Author is
    # shown; none may be offered. Nothing is clicked that could alter 78261.
    with _test_owned(page, (), "tc_134772") as (admin, snap):
        with allure.step("Sign in as Site Content Author and locate the publish controls"):
            admin.sign_in(ROLE_AUTHOR)
            assert not admin.has_admin_toolbar(), "precondition: session is not the Author role"
            admin.open_entries_list(locale=EN)
            row_actions = admin.row_actions_for_record()
            admin.open_record()
            controls = admin.control_state()
            _attach("Author row actions / form controls", {"row": row_actions, "form": controls})
        with allure.step("Check the publication state"):
            admin.open_record()
            status = admin.current_status()
        for action in ("data-qc-oel-publish", "data-qc-oel-approve", "data-qc-oel-unpublish"):
            assert action not in row_actions, f"Author is offered row action {action}"
        assert not controls["unpublish"][1], "Author can Unpublish (publish control) the record"
        assert status == snap["status"], f"publication state changed to {status!r}"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that a user without the required permission is denied access to the Chairman's Message page record")
@allure.label("pbi", PBI)
@allure.label("testcase", "134773")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129393
@pytest.mark.tc_134773
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134773")
@pytest.mark.timeout(300)
def test_134773_user_without_permission_is_denied(page):
    # Account: the site-member account (no CMS role) — the negative case.
    admin = ChairmanMessageAdminPage(page)
    with allure.step("Sign in as a site member"):
        admin.sign_in(ROLE_SITE_MEMBER)
        assert CmsLoginPage(page).login_succeeded(), "the site member did not sign in"
    outcomes = {}
    for ui in (EN, AR):
        with allure.step(f"[{ui.upper()} interface] Open the record for editing"):
            status = admin.open_record_raw(locale=ui)
            outcomes[ui] = {"http": status, "form": admin.has_object_form(),
                            "text": admin.body_text()[:400]}
    _attach("denial outcomes (wording recorded)", outcomes)
    for ui, out in outcomes.items():
        assert not out["form"], f"[{ui}] the record opened in editable mode for a site member"
        assert out["http"] in (401, 403, 404) or any(
            s in out["text"].casefold() for s in ("access denied", "permission", "رفض", "صلاحية", "not found")
        ), f"[{ui}] no positive denial signal: {out!r}"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Publish")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that publishing the Chairman's Message page makes the content visible on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "134774")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134774
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134774")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134774_publish_makes_content_visible(page, browser):
    paragraph = "QCTEST-134774 body paragraph of the Chairman's message."
    html = f"<h2>Dear members and visitors</h2><p>{paragraph}</p>"
    keys = ("page_title", "message", "name", "designation")
    with _test_owned(page, keys, "tc_134774") as (admin, _snap):
        with allure.step("Set Page Title, Message Content, Chairman Name and Designation (EN), then Publish"):
            block_live_singleton_write(RECORD, "unpublish + publish of title / message / name / designation")
            _make_editable(admin)
            admin.set_text("page_title", CASE_TITLE, EN)
            admin.set_message_html(html, EN)
            admin.set_text("name", CASE_NAME, EN)
            admin.set_text("designation", CASE_DESIGNATION, EN)
            _publish(admin)
        with _visitor(browser) as pub:
            with allure.step("Open the public page in English after the cache refresh"):
                shown = _public(pub, lambda p: paragraph in _body(p))
                title, name, desig = (pub.hero_title_text(), pub.name_text(), pub.designation_text()) if shown else ("", "", "")
                body = _body(pub) if shown else ""
        assert shown, "the published content never reached the public page"
        assert title.strip() == CASE_TITLE, f"title reads {title!r}"
        assert "Dear members and visitors" in body
        assert name.strip() == CASE_NAME, f"name reads {name!r}"
        assert desig.strip() == CASE_DESIGNATION, f"designation reads {desig!r}"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Unpublish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that unpublishing the Chairman's Message page removes it from the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "134776")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134776
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134776")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134776_unpublish_removes_page_from_website(page, browser):
    with _test_owned(page, ("name", "designation"), "tc_134776") as (admin, snap):
        name = snap["fields"][("name", EN)]
        block_live_singleton_write(RECORD, "Unpublish")
        assert snap["status"] == STATUS_PUBLISHED, f"precondition: record is {snap['status']!r}, not Published"
        with allure.step("Click Unpublish"):
            admin.open_record()
            admin.unpublish_to_edit_as_draft()
            admin.wait_for_status(STATUS_UNPUBLISHED, timeout=UNPUBLISH_TIMEOUT)
        with _visitor(browser) as pub:
            with allure.step("Open the public URL with no CMS login"):
                seen = {"rendered": False, "has_name": True}

                def _gone() -> bool:
                    try:
                        body = _body(pub.open_en_expecting_no_content())
                    except Exception:  # noqa: BLE001 — not rendered: not the standard page
                        return False
                    seen.update(rendered=bool(body.strip()), has_name=bool(name) and name in body)
                    return seen["rendered"] and not seen["has_name"]

                _wait(_gone, PUBLIC_TIMEOUT, "public page kept serving the message")
                _attach("public after unpublish", seen)
                still = seen["has_name"] or not seen["rendered"]
        with allure.step("Re-open the record in the CMS"):
            admin.open_record()
            kept = {"portrait": admin.portrait_name(), "name": admin.text_of("name"),
                    "designation": admin.text_of("designation"), "message": admin.message_html(EN),
                    "controls": admin.control_state()}
            _attach("record after unpublish", kept)
        assert not still, f"the public URL did not show the standard not-available page: {seen!r}"
        assert kept["portrait"] and kept["name"] == name and kept["message"].strip()
        assert kept["designation"] == snap["fields"][("designation", EN)]
        assert kept["controls"]["save_draft"][1], "the unpublished record is not editable"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Draft")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that draft Chairman's Message content is visible only in the CMS and not on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "134777")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134777
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134777")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134777_draft_content_is_cms_only(page, browser):
    # VERIFY-LIVE: editing requires Unpublish first (guide §4); the case
    # expects the previously published message to stay live meanwhile. Scripted
    # as the case states — a dark page is a finding for triage, not a pass.
    with _test_owned(page, ("message", "name"), "tc_134777") as (admin, snap):
        with allure.step("Add 'DRAFT-ONLY-129393' to Message Content (EN) and Save as draft"):
            block_live_singleton_write(RECORD, "unpublish + Save as Draft of Message Content")
            _make_editable(admin)
            admin.set_message_html(_message_with(snap["fields"][("message", EN)], "<p>DRAFT-ONLY-129393</p>"), EN)
            admin.save_as_draft()
            admin.wait_for_status(STATUS_DRAFT, timeout=UNPUBLISH_TIMEOUT)
        with _visitor(browser) as pub:
            with allure.step("Search the public page for the draft paragraph"):
                leaked = _public(pub, lambda p: "DRAFT-ONLY-129393" in _body(p), expect=False)
                live_name = snap["fields"][("name", EN)]
                previous_live = _public(pub, lambda p: live_name in p.name_text())
        with allure.step("Re-open the record in the CMS"):
            admin.open_record()
            stored = admin.message_html(EN)
        assert not leaked, "the draft paragraph is visible on the public page"
        assert previous_live, "the public page no longer shows the previously published message"
        assert "DRAFT-ONLY-129393" in stored, "the CMS record does not hold the draft paragraph"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Preview")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that Preview renders unpublished Chairman's Message content without publishing it")
@allure.label("pbi", PBI)
@allure.label("testcase", "134778")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134778
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134778")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134778_preview_renders_unpublished_content(page, browser):
    with _test_owned(page, ("message",), "tc_134778") as (admin, snap):
        with allure.step("Add 'PREVIEW-ONLY-129393', save as draft, click Preview"):
            block_live_singleton_write(RECORD, "unpublish + Save as Draft of Message Content")
            _make_editable(admin)
            admin.set_message_html(_message_with(snap["fields"][("message", EN)], "<p>PREVIEW-ONLY-129393</p>"), EN)
            admin.save_as_draft()
            admin.open_entries_list(locale=EN)
            url = admin.row_preview_url_by_code(CHAIRMAN_MESSAGE_ENTRY_CODE)
            assert url, "the record row offers no Preview link"
            admin.open(url)
            previewed = "PREVIEW-ONLY-129393" in admin.body_text()
        with allure.step("Check the record status and the public page"):
            admin.open_record()
            status = admin.current_status()
            with _visitor(browser) as pub:
                leaked = _public(pub, lambda p: "PREVIEW-ONLY-129393" in _body(p), expect=False)
        assert previewed, "Preview did not render the unpublished paragraph"
        assert status == STATUS_DRAFT, f"record status is {status!r} after Preview, expected Draft"
        assert not leaked, "the preview-only paragraph is visible on the public page"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Cache / audit log")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that publishing the Chairman's Message page updates the page cache and writes an audit log entry")
@allure.label("pbi", PBI)
@allure.label("testcase", "134779")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.tc_134779
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134779")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134779_publish_refreshes_cache_and_writes_audit_entry(page, browser):
    # The publish is made as the Site Content Editor; the Liferay Audit portlet
    # is an administrator surface (FIX 2026-10-13: read in the Editor session
    # its table never rendered -> 60 s timeout), so the audit trail is READ in
    # a separate TEST_USER context. Read-only there; the acting account is
    # still the Editor, and the audit row must name it.
    audit_ctx = new_context(browser)
    auditor = ChairmanMessageAdminPage(audit_ctx.new_page())
    try:
        _test_134779_body(page, browser, auditor)
    finally:
        try:
            audit_ctx.close()
        except Exception:  # noqa: BLE001
            pass


def _test_134779_body(page, browser, auditor) -> None:
    with _test_owned(page, ("message",), "tc_134779") as (admin, snap):
        with allure.step("Note the audit trail before publishing"):
            admin.open_entries_list(locale=EN)
            entry_id = admin.record_entry_id()
            before = auditor.audit_rows_for(entry_id)
        with allure.step("Add 'CACHE-CHECK-129393' to Message Content (EN) and Publish"):
            block_live_singleton_write(RECORD, "unpublish + publish of Message Content")
            _logged_make_editable(admin, "134779")
            admin.set_message_html(_message_with(snap["fields"][("message", EN)], "<p>CACHE-CHECK-129393</p>"), EN)
            log_live_write(RECORD, "Message Content (EN)", "<current message> + <p>CACHE-CHECK-129393</p>",
                           "134779", action="publish", note="Submit for Review as Site Content Editor")
            _publish(admin)
        with _visitor(browser) as pub:
            with allure.step("Open the public page after the cache refresh"):
                served = _public(pub, lambda p: "CACHE-CHECK-129393" in _body(p))
        with allure.step("Open the audit log filtered to this record"):
            after = auditor.audit_rows_for(entry_id)
            _attach("audit rows (newest first)", after[:5])
        assert served, "the public page still serves the cached, pre-publish content"
        assert entry_id, "could not read the record's entry id"
        assert len(after) > len(before), "no new audit-log entry was written for the publish"
        assert after[0][1].strip(), "the newest audit entry names no acting user"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a hyperlink configured in the message content opens its destination from the public page")
@allure.label("pbi", PBI)
@allure.label("testcase", "134780")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.redirect
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134780
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134780")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134780_message_hyperlink_opens_destination(page, browser):
    label = "Qatar National Vision 2030"
    with _test_owned(page, ("message",), "tc_134780") as (admin, snap):
        with allure.step(f"Add a link {label!r} -> {QC_URL} inside Message Content (EN) and publish"):
            block_live_singleton_write(RECORD, "unpublish + publish of a Message Content link")
            _make_editable(admin)
            admin.set_message_html(_message_with(
                snap["fields"][("message", EN)], f'<p><a href="{QC_URL}">{label}</a></p>'), EN)
            _publish(admin)
        with _visitor(browser) as pub:
            with allure.step("Locate the link on the public page"):
                found = _public(pub, lambda p: any(lk["text"] == label for lk in p.body_links()))
                links = pub.body_links() if found else []
            with allure.step(f"Click {label!r}"):
                landed = ""
                if found:
                    pub.click(f'{pub.BODY_LINKS}:has-text("{label}")')
                    ctx_pages = pub.page.context.pages
                    _wait(lambda: "qatarchamber.com" in ctx_pages[-1].url, 30, "navigation")
                    landed = ctx_pages[-1].url
        assert found, f"the link {label!r} is not rendered in the message: {links!r}"
        assert "qatarchamber.com" in landed, f"clicking the link landed on {landed!r}"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Chairman Portrait")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that replacing the Chairman Portrait updates the image shown on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "134783")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134783
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134783")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134783_replacing_portrait_updates_website(page, browser):
    new_file = _qctest_copy(_fixture("chairman-new.jpg", make_jpg, 900 * 1024), "134783-chairman-new")
    with _test_owned(page, ("portrait", "portrait_alt"), "tc_134783") as (admin, _snap):
        with _visitor(browser) as pub:
            old_src = _public_once(pub, lambda p: p.get_attribute(p.PORTRAIT_IMG, "src") or "")
        with allure.step("Replace the portrait with chairman-new.jpg (900 KB), update its alt text, publish"):
            block_live_singleton_write(RECORD, "unpublish + publish of a replacement portrait")
            _make_editable(admin)
            admin.upload_file(admin.spec("portrait").label, new_file)
            admin.set_text("portrait_alt", "QCTEST-134783 new portrait", EN)
            _publish(admin)
        with _visitor(browser) as pub:
            with allure.step("Open the public page after the cache refresh"):
                shown = _public(pub, lambda p: _stem(new_file) in (p.get_attribute(p.PORTRAIT_IMG, "src") or ""))
                src = pub.get_attribute(pub.PORTRAIT_IMG, "src") if shown else ""
                deco = pub.portrait_deco_box() if shown else None
        assert shown, "the public portrait does not serve chairman-new.jpg"
        assert src != old_src, "the previous portrait is still served"
        assert deco, "the maroon decorative backing element is missing"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Chairman Portrait")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that uploading a Chairman Portrait for the first time publishes it to the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "134784")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134784
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134784")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134784_first_portrait_upload_publishes(page, browser):
    # Precondition "no portrait set" is reached on the live record with the
    # two-phase remove → save → upload sequence (object_authoring_page
    # remove_current_file docstring); the baseline file is re-selected after.
    png = _qctest_copy(_fixture("chairman.png", make_png, int(1.4 * ONE_MB)), "134784-chairman")
    with _test_owned(page, ("portrait", "portrait_alt"), "tc_134784") as (admin, _snap):
        with allure.step("Reach the empty-portrait precondition"):
            block_live_singleton_write(RECORD, "unpublish + remove/save, then publish a first portrait")
            _make_editable(admin)
            admin.remove_current_file(admin.spec("portrait").label)
            admin.save_as_draft()
            admin.open_record()
            assert admin.portrait_name() == "", "precondition: the portrait field is not empty"
        with allure.step("Upload chairman.png (1.4 MB), set its alt text, publish"):
            admin.upload_file(admin.spec("portrait").label, png)
            admin.set_text("portrait_alt", CASE_PORTRAIT_ALT, EN)
            _publish(admin)
        with _visitor(browser) as pub:
            with allure.step("Open the public page after the cache refresh"):
                shown = _public(pub, lambda p: _stem(png) in (p.get_attribute(p.PORTRAIT_IMG, "src") or ""))
                alt = pub.portrait_alt_text() if shown else ""
                radius = pub.portrait_style().get("borderRadius", "") if shown else ""
                deco = pub.portrait_deco_box() if shown else None
        assert shown, "the public portrait does not serve chairman.png"
        assert alt == CASE_PORTRAIT_ALT, f"portrait alt reads {alt!r}"
        assert radius == "16px", f"portrait corner radius is {radius!r}"
        assert deco, "the maroon decorative rectangle is missing"


@allure.epic("About Us")
@allure.feature("Chairman's Message")
@allure.story("Name / Designation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that Chairman Name and Designation are entered once and populate both the Name Card and the Signature block")
@allure.label("pbi", PBI)
@allure.label("testcase", "134787")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.dataintegrity
@pytest.mark.regression
@pytest.mark.pbi_129393
@pytest.mark.tc_134787
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134787")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134787_name_and_designation_feed_name_card_and_signature(page, browser):
    with _test_owned(page, ("name", "designation"), "tc_134787") as (admin, _snap):
        with allure.step("Confirm exactly one Name and one Designation field per language"):
            admin.open_record()
            counts = {lbl: admin.field_count(lbl) for lbl in (
                "Chairman Name", "Chairman Name — العربية",
                "Chairman Designation", "Chairman Designation — العربية")}
            sig_fields = admin.field_count("Signature Name") + admin.field_count("Signature Designation")
            _attach("field counts", counts)
        assert all(c == 1 for c in counts.values()), f"field counts: {counts!r}"
        assert sig_fields == 0, "a separate signature-block field exists"
        with allure.step("Change Name and Designation (EN), then publish"):
            block_live_singleton_write(RECORD, "unpublish + publish of Name / Designation")
            _make_editable(admin)
            admin.set_text("name", CASE_NAME, EN)
            admin.set_text("designation", CASE_DESIGNATION, EN)
            _publish(admin)
        with _visitor(browser) as pub:
            with allure.step("Read the Name Card and the Signature block"):
                shown = _public(pub, lambda p: p.name_text().strip() == CASE_NAME)
                got = {"name": pub.name_text(), "desig": pub.designation_text(), "regards": pub.sig_regards_text(),
                       "sig_name": pub.sig_name_text(), "sig_desig": pub.sig_desig_text()} if shown else {}
                _attach("public values", got)
        assert shown, "the Name Card never showed the new name"
        assert got["desig"].strip() == CASE_DESIGNATION
        assert got["regards"].strip() == "Best Regards,"
        assert got["sig_name"].strip() == CASE_NAME and got["sig_desig"].strip() == CASE_DESIGNATION, (
            f"signature block mismatch: {got!r}")


# ===========================================================================
# Field cases — singleton record (TEST_OWNED)
# ===========================================================================
def _field_case(story: str):
    def deco(fn):
        for d in (allure.epic("About Us"), allure.feature("Chairman's Message"), allure.story(story),
                  allure.severity(allure.severity_level.NORMAL), allure.label("pbi", PBI)):
            fn = d(fn)
        return fn
    return deco


@_field_case("Page Title")
@allure.title("Verify that a valid English Page Title is accepted and saved")
@allure.label("testcase", "134788")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134788
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134788")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134788_valid_english_page_title_saved(page):
    _valid_value(page, "134788", "page_title", CASE_TITLE, EN)


@_field_case("Page Title")
@allure.title("Verify that an empty English Page Title is rejected on save")
@allure.label("testcase", "134789")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134789
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134789")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134789_empty_english_page_title_rejected(page):
    _empty_refused(page, "134789", "page_title", EN)


@_field_case("Page Title")
@allure.title("Verify that a valid Arabic Page Title is accepted and saved")
@allure.label("testcase", "134792")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.pbi_129393
@pytest.mark.tc_134792
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134792")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134792_valid_arabic_page_title_saved(page):
    _valid_value(page, "134792", "page_title", "رسالة رئيس مجلس الإدارة", AR)


@_field_case("Page Title")
@allure.title("Verify that a missing Arabic Page Title is rejected with the Arabic-title-required message")
@allure.label("testcase", "134793")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.pbi_129393
@pytest.mark.tc_134793
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134793")
# 600 s (2026-10-13): two interfaces (EN + AR), each behind an Unpublish,
# plus the finally re-publish measured ~6 min live; at 300 s the thread
# timeout hard-exited mid re-publish and left the record Unpublished.
@pytest.mark.timeout(600)
@CHAIRMAN_GROUP
def test_134793_missing_arabic_page_title_rejected(page):
    # Repeated under the Arabic CMS interface (step 3).
    _empty_refused(page, "134793", "page_title", AR, also_ar_ui=True)


@_field_case("Chairman Portrait")
@allure.title("Verify that a valid PNG Chairman Portrait under 2 MB is accepted")
@allure.label("testcase", "134804")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134804
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134804")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134804_valid_png_portrait_accepted(page):
    png = _qctest_copy(_fixture("chairman.png", make_png, int(1.4 * ONE_MB)), "134804-chairman")
    with _test_owned(page, ("portrait",), "tc_134804") as (admin, _snap):
        with allure.step("Upload chairman.png (PNG, 1.4 MB) and Save"):
            block_live_singleton_write(RECORD, "unpublish + publish of a valid portrait")
            _make_editable(admin)
            admin.upload_file(admin.spec("portrait").label, png)
            _publish(admin)
        with allure.step("Reload the record"):
            admin.open_record()
            stored = admin.portrait_name()
        assert _stem(png) in stored, f"the Chairman Portrait field shows {stored!r}"


@_field_case("Chairman Portrait")
@allure.title("Verify that a Chairman Portrait in an unsupported format is rejected with the JPG-or-PNG message")
@allure.label("testcase", "134805")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134805
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134805")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134805_unsupported_portrait_format_rejected(page):
    gif = _qctest_copy(_fixture("chairman.gif", make_gif, 600 * 1024), "134805-chairman")
    with _test_owned(page, ("portrait",), "tc_134805") as (admin, snap):
        with allure.step("Upload chairman.gif (GIF, 600 KB) to the Chairman Portrait field"):
            if snap["status"] == STATUS_PUBLISHED:
                block_live_singleton_write(RECORD, "setup Unpublish before the portrait picker")
            _make_editable(admin)
            rejected = admin.upload_file_expect_rejected(admin.spec("portrait").label, gif)
        with allure.step("Reload the record (nothing saved)"):
            admin.open_record()
            stored = admin.portrait_name()
        assert rejected, "the GIF portrait was accepted by the upload"
        assert stored == snap["fields"][("portrait", EN)], f"stored portrait changed to {stored!r}"


@_field_case("Chairman Portrait")
@allure.title("Verify that a Chairman Portrait above 2 MB is rejected at the size boundary")
@allure.label("testcase", "134806")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134806
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134806")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134806_oversize_portrait_rejected(page):
    exact = _qctest_copy(_fixture("chairman-2mb.png", make_png, 2 * ONE_MB), "134806-chairman-2mb")
    over = _qctest_copy(_fixture("chairman-oversize.png", make_png, int(3.1 * ONE_MB)), "134806-oversize")
    with _test_owned(page, ("portrait",), "tc_134806") as (admin, _snap):
        with allure.step("Upload chairman-2mb.png (exactly 2 MB) and Save"):
            # The boundary case starts with a SUCCESSFUL 2 MB save (2026-10-13).
            block_live_singleton_write(RECORD, "unpublish + publish of the exactly-2 MB portrait")
            _make_editable(admin)
            admin.upload_file(admin.spec("portrait").label, exact)
            _publish(admin)
            admin.open_record()
            stored = admin.portrait_name()
        assert _stem(exact) in stored, f"the exactly-2 MB portrait was not saved (field shows {stored!r})"
        with allure.step("Upload a 3.1 MB PNG to the same field (2.1 MB is inside the 3 MB tolerance)"):
            _make_editable(admin)
            rejected = admin.upload_file_expect_rejected(admin.spec("portrait").label, over)
            admin.open_record()
            after = admin.portrait_name()
        assert rejected, "a 3.1 MB portrait was accepted"
        assert after == stored, f"the stored portrait changed to {after!r}"


@_field_case("Chairman Portrait")
@allure.title("Verify that publishing without a Chairman Portrait is blocked")
@allure.label("testcase", "134807")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134807
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134807")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134807_publish_without_portrait_blocked(page):
    with _test_owned(page, ("portrait",), "tc_134807") as (admin, snap):
        with allure.step("Empty the Chairman Portrait field and click Publish"):
            if snap["status"] == STATUS_PUBLISHED:
                block_live_singleton_write(RECORD, "setup Unpublish before emptying the portrait")
            _make_editable(admin)
            status_before = admin.current_status()
            admin.remove_current_file(admin.spec("portrait").label)
            admin.submit_for_review()
            refused = admin.refusal_visible()
            _attach("refusal text", admin.refusal_text())
        with allure.step("Check the record status"):
            admin.open_record()
            status, stored = admin.current_status(), admin.portrait_name()
        stop_unless_refused(stored == snap["fields"][("portrait", EN)] and status == status_before, RECORD,
                            "Publish with the Chairman Portrait removed",
                            {"refused": refused, "stored": stored, "status": status})
        assert refused, "publishing without a Chairman Portrait was not blocked"
        assert status == status_before and status != STATUS_PUBLISHED, f"record status is {status!r}"
        assert stored == snap["fields"][("portrait", EN)], f"the portrait changed to {stored!r}"


@_field_case("Chairman Portrait")
@allure.title("Verify that valid Chairman Portrait Alt Text is accepted and saved")
@allure.label("testcase", "134808")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.accessibility
@pytest.mark.pbi_129393
@pytest.mark.tc_134808
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134808")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134808_valid_portrait_alt_text_saved(page):
    _valid_value(page, "134808", "portrait_alt", CASE_PORTRAIT_ALT, EN)


@_field_case("Chairman Portrait")
@allure.title("Verify that empty Chairman Portrait Alt Text is rejected on save")
@allure.label("testcase", "134809")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.accessibility
@pytest.mark.pbi_129393
@pytest.mark.tc_134809
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134809")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134809_empty_portrait_alt_text_rejected(page):
    _empty_refused(page, "134809", "portrait_alt", EN)


@_field_case("Name / Designation")
@allure.title("Verify that a valid Chairman Name is accepted and saved")
@allure.label("testcase", "134812")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134812
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134812")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134812_valid_chairman_name_saved(page):
    _valid_value(page, "134812", "name", CASE_NAME, EN)


@_field_case("Name / Designation")
@allure.title("Verify that an empty Chairman Name is rejected on save")
@allure.label("testcase", "134813")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134813
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134813")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134813_empty_chairman_name_rejected(page):
    _empty_refused(page, "134813", "name", EN)


@_field_case("Name / Designation")
@allure.title("Verify that a valid Chairman Designation is accepted and saved")
@allure.label("testcase", "134816")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134816
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134816")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134816_valid_chairman_designation_saved(page):
    _valid_value(page, "134816", "designation", CASE_DESIGNATION, EN)


@_field_case("Name / Designation")
@allure.title("Verify that an empty Chairman Designation is rejected on save")
@allure.label("testcase", "134817")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134817
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134817")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134817_empty_chairman_designation_rejected(page):
    _empty_refused(page, "134817", "designation", EN)


_EN_600 = (
    "<h2>Dear members and visitors</h2>"
    "<p>QCTEST-134820 It is my pleasure to welcome you to the Qatar Chamber website, the gateway to the "
    "private sector of the State of Qatar. The Chamber continues to support businesses, investors and "
    "entrepreneurs through services, partnerships and initiatives that strengthen the national economy.</p>"
    "<p>We remain committed to the goals of Qatar National Vision 2030, to a diversified economy, and to "
    "a business environment that rewards innovation, quality and sustainable growth across every sector.</p>"
)
_AR_600 = (
    "<h2>السادة الأعضاء والزوار</h2>"
    "<p>QCTEST-134824 يسعدني أن أرحب بكم في الموقع الإلكتروني لغرفة قطر، بوابة القطاع الخاص في دولة قطر. "
    "تواصل الغرفة دعم الشركات والمستثمرين ورواد الأعمال من خلال الخدمات والشراكات والمبادرات التي تعزز "
    "الاقتصاد الوطني وتدعم التنمية المستدامة.</p>"
    "<p>ونحن ملتزمون بتحقيق أهداف رؤية قطر الوطنية 2030، وبناء اقتصاد متنوع، وبيئة أعمال تكافئ الابتكار "
    "والجودة والنمو المستدام في جميع القطاعات الاقتصادية في الدولة.</p>"
)


@_field_case("Message Content")
@allure.title("Verify that valid English Message Content is accepted and saved")
@allure.label("testcase", "134820")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134820
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134820")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134820_valid_english_message_saved(page):
    with _test_owned(page, ("message",), "tc_134820") as (admin, _snap):
        with allure.step("Enter a ~600-character body with the salutation heading and two paragraphs; Save"):
            block_live_singleton_write(RECORD, "unpublish + publish of Message Content (EN)")
            _make_editable(admin)
            admin.set_message_html(_EN_600, EN)
            _publish(admin)
        with allure.step("Reload the record"):
            admin.open_record()
            stored = admin.message_html(EN)
        assert "Dear members and visitors" in stored and "<h2" in stored, "salutation heading not preserved"
        assert stored.count("<p") >= 2 and "QCTEST-134820" in stored, f"paragraphs not preserved: {stored[:300]!r}"


@_field_case("Message Content")
@allure.title("Verify that empty English Message Content is rejected on save")
@allure.label("testcase", "134821")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134821
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134821")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134821_empty_english_message_rejected(page):
    _empty_refused(page, "134821", "message", EN)


@_field_case("Message Content")
@allure.title("Verify that valid Arabic Message Content is accepted and saved with RTL text preserved")
@allure.label("testcase", "134824")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.rtl
@pytest.mark.pbi_129393
@pytest.mark.tc_134824
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134824")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134824_valid_arabic_message_saved_rtl(page):
    with _test_owned(page, ("message",), "tc_134824") as (admin, _snap):
        with allure.step("Enter a ~600-character Arabic body with 'السادة الأعضاء والزوار'; Save"):
            block_live_singleton_write(RECORD, "unpublish + publish of Message Content (AR)")
            _make_editable(admin)
            admin.set_message_html(_AR_600, AR)
            _publish(admin)
        with allure.step("Reload the record"):
            admin.open_record()
            stored = admin.message_html(AR)
            direction = admin.message_direction(AR)
        assert "السادة الأعضاء والزوار" in stored, "the Arabic salutation was not preserved"
        assert "QCTEST-134824" in stored, "the Arabic body was not saved"
        assert direction == "rtl", f"the Arabic editor renders {direction!r}, not rtl"


@_field_case("Message Content")
@allure.title("Verify that empty Arabic Message Content is rejected on save")
@allure.label("testcase", "134825")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.pbi_129393
@pytest.mark.tc_134825
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134825")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134825_empty_arabic_message_rejected(page):
    _empty_refused(page, "134825", "message", AR)


@_field_case("Hyperlink")
@allure.title("Verify that an invalid Hyperlink URL is rejected on save")
@allure.label("testcase", "134832")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134832
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134832")
@pytest.mark.timeout(300)
@CHAIRMAN_GROUP
def test_134832_invalid_hyperlink_url_rejected(page):
    bad = "www,qatarchamber,com"
    with _test_owned(page, ("hyperlink_url",), "tc_134832") as (admin, snap):
        with allure.step(f"Enter {bad!r} as the Hyperlink URL and Save"):
            if snap["status"] == STATUS_PUBLISHED:
                block_live_singleton_write(RECORD, "setup Unpublish before entering a bad Hyperlink URL")
            _make_editable(admin)
            status_before = admin.current_status()
            admin.fill("hyperlink_url", bad)
            admin.submit_for_review()
            refused = admin.refusal_visible()
            _attach("refusal text", admin.refusal_text())
        with allure.step("Reload the record"):
            admin.open_record()
            stored, status = admin.value("hyperlink_url"), admin.current_status()
        stop_unless_refused(stored != bad and status == status_before, RECORD,
                            f"Save with Hyperlink URL {bad!r}", {"refused": refused, "stored": stored})
        assert refused, "the invalid Hyperlink URL was not refused"
        assert stored == snap["fields"][("hyperlink_url", EN)] and stored != bad, f"Hyperlink URL stored {stored!r}"
        assert status == status_before, f"record status moved to {status!r}"


# ===========================================================================
# Hero Banner field cases — disposable QCTEST About Hero Banner rows
# ===========================================================================
@_field_case("Hero Banner")
@allure.title("Verify that a valid JPG Hero Banner under 2 MB is accepted")
@allure.label("testcase", "134796")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134796
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134796")
@pytest.mark.timeout(300)
@HERO_QCTEST_GROUP
def test_134796_valid_jpg_hero_banner_accepted(page):
    hero, key = _hero(page), _hero_key("134796")
    jpg = _qctest_copy(_fixture("hero.jpg", make_jpg, 900 * 1024), "134796-hero")
    try:
        with allure.step("Upload hero.jpg (JPG, 900 KB) to the Hero Banner field and Save"):
            said = _hero_create(hero, key, jpg, "QCTEST hero banner")
        with allure.step("Reload the record"):
            stored = _hero_open(hero, key).image_name() if said["listed"] else ""
        assert not said["refused"] and said["listed"], f"the hero record was not saved: {said!r}"
        assert _stem(jpg) in stored, f"Hero Banner field shows {stored!r}"
    finally:
        _hero_cleanup(hero, key)


@_field_case("Hero Banner")
@allure.title("Verify that a Hero Banner in an unsupported format is rejected with the JPG-or-PNG message")
@allure.label("testcase", "134797")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134797
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134797")
@pytest.mark.timeout(300)
@HERO_QCTEST_GROUP
def test_134797_unsupported_hero_format_rejected(page):
    hero, key = _hero(page), _hero_key("134797")
    jpg = _qctest_copy(_fixture("hero.jpg", make_jpg, 900 * 1024), "134797-hero")
    svg = _fixture("hero.svg", make_svg, 300 * 1024)
    try:
        said = _hero_create(hero, key, jpg, "QCTEST hero banner")
        assert said["listed"], f"precondition: disposable hero row not created: {said!r}"
        outcomes = {}
        for ui in (EN, AR):
            with allure.step(f"[{ui.upper()} interface] Upload hero.svg (SVG, 300 KB)"):
                _hero_open(hero, key, ui)
                outcomes[ui] = {"accepted": hero.attempt_upload_by_field(
                    "ObjectField_bannerImage", _qctest_copy(svg, f"134797-{ui}")),
                    "picker": getattr(hero, "last_picker_text", "")}
        with allure.step("Reload: the stored banner is unchanged"):
            stored = _hero_open(hero, key).image_name()
        _attach("outcomes (wording recorded, not asserted)", outcomes)
        for ui, out in outcomes.items():
            assert not out["accepted"], f"[{ui}] the SVG Hero Banner was accepted"
        assert _stem(jpg) in stored, f"the stored Hero Banner changed to {stored!r}"
    finally:
        _hero_cleanup(hero, key)


@_field_case("Hero Banner")
@allure.title("Verify that a Hero Banner above 2 MB is rejected at the size boundary")
@allure.label("testcase", "134798")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134798
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134798")
@pytest.mark.timeout(300)
@HERO_QCTEST_GROUP
def test_134798_oversize_hero_banner_rejected(page):
    hero, key = _hero(page), _hero_key("134798")
    exact = _qctest_copy(_fixture("hero-2mb.jpg", make_jpg, 2 * ONE_MB), "134798-hero-2mb")
    over = _fixture("hero-oversize-3mb.jpg", make_jpg, int(3.1 * ONE_MB))
    try:
        with allure.step("Upload hero-2mb.jpg (exactly 2 MB) and Save"):
            said = _hero_create(hero, key, exact, "QCTEST hero banner")
            stored = _hero_open(hero, key).image_name() if said["listed"] else ""
        assert said["listed"] and _stem(exact) in stored, f"the 2 MB banner was not saved: {said!r} / {stored!r}"
        outcomes = {}
        for ui in (EN, AR):
            with allure.step(f"[{ui.upper()} interface] Upload a 3.1 MB JPG (2.1 MB is inside the 3 MB tolerance)"):
                _hero_open(hero, key, ui)
                outcomes[ui] = {"accepted": hero.attempt_upload_by_field(
                    "ObjectField_bannerImage", _qctest_copy(over, f"134798-{ui}")),
                    "picker": getattr(hero, "last_picker_text", "")}
        after = _hero_open(hero, key).image_name()
        _attach("outcomes", outcomes)
        for ui, out in outcomes.items():
            assert not out["accepted"], f"[{ui}] a 3.1 MB Hero Banner was accepted"
        assert after == stored, f"the stored Hero Banner changed to {after!r}"
    finally:
        _hero_cleanup(hero, key)


@_field_case("Hero Banner")
@allure.title("Verify that publishing without a Hero Banner is blocked")
@allure.label("testcase", "134799")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134799
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134799")
@pytest.mark.timeout(300)
@HERO_QCTEST_GROUP
def test_134799_publish_without_hero_banner_blocked(page):
    hero, key = _hero(page), _hero_key("134799")
    try:
        with allure.step("Click Publish on a hero record with no Hero Banner"):
            said = _hero_create(hero, key, None, "QCTEST hero without image")
        assert said["refused"], f"publishing without a Hero Banner was not blocked: {said!r}"
        assert said["status"] != STATUS_PUBLISHED, f"the record was published: {said!r}"
    finally:
        _hero_cleanup(hero, key)


@_field_case("Hero Banner")
@allure.title("Verify that valid Hero Banner Alt Text is accepted and saved")
@allure.label("testcase", "134800")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.accessibility
@pytest.mark.pbi_129393
@pytest.mark.tc_134800
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134800")
@pytest.mark.timeout(300)
@HERO_QCTEST_GROUP
def test_134800_valid_hero_alt_text_saved(page):
    hero, key = _hero(page), _hero_key("134800")
    jpg = _qctest_copy(_fixture("hero.jpg", make_jpg, 900 * 1024), "134800-hero")
    try:
        with allure.step(f"Enter {CASE_HERO_ALT!r} in Hero Banner Alt Text and Save"):
            said = _hero_create(hero, key, jpg, CASE_HERO_ALT)
        with allure.step("Reload the record"):
            stored = _hero_open(hero, key).alt_text() if said["listed"] else None
        assert not said["refused"] and said["listed"], f"the hero record was not saved: {said!r}"
        assert stored == CASE_HERO_ALT, f"Hero Banner Alt Text reads {stored!r}"
    finally:
        _hero_cleanup(hero, key)


@_field_case("Hero Banner")
@allure.title("Verify that empty Hero Banner Alt Text is rejected on save")
@allure.label("testcase", "134801")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.accessibility
@pytest.mark.pbi_129393
@pytest.mark.tc_134801
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134801")
@pytest.mark.timeout(300)
@HERO_QCTEST_GROUP
def test_134801_empty_hero_alt_text_rejected(page):
    hero, key = _hero(page), _hero_key("134801")
    jpg = _qctest_copy(_fixture("hero.jpg", make_jpg, 900 * 1024), "134801-hero")
    previous = "QCTEST previous alt text"
    try:
        said = _hero_create(hero, key, jpg, previous, publish=False)
        assert said["listed"], f"precondition: disposable hero row not created: {said!r}"
        with allure.step("Clear Hero Banner Alt Text and Save"):
            _hero_open(hero, key)
            hero.fill_alt_text("")
            hero.submit_for_review()  # live-write-guard: disposable QCTEST hero row
            refused = hero.refusal_visible()
            _attach("refusal text", hero.refusal_text())
        with allure.step("Reload the record"):
            stored = _hero_open(hero, key).alt_text()
            status = hero.row_status_text(key)
        assert refused, "empty Hero Banner Alt Text was not refused"
        assert stored == previous, f"Hero Banner Alt Text changed to {stored!r}"
        assert status != STATUS_PUBLISHED
    finally:
        _hero_cleanup(hero, key)



# ===========================================================================
# P3/P4 BATCH -- 2026-10-13 (scripted OFFLINE, NOT executed): 134829 134831
# 134834 134835 134836, from .claude/qa-runs/phase3-20261012/129393.p34.todo.json
# (the case text is the oracle).
#
# USER DECISION 2026-10-13 (P3/P4 batch only): these cases MAY write test
# data to the real singleton 78261 (QCDEMO-129393-chairmans-message) -- ONLY
# when the run sets QC_ALLOW_LIVE_SINGLETON_WRITES=1; without it
# block_live_singleton_write() reports them NOT APPLICABLE, unchanged. Nothing
# is ever deleted; every persisted write is logged BEFORE its click to
# reports/live-writes-20261013.jsonl for the user's manual cleanup. Each case
# leaves 78261 Published (picklist + workflow).
#
# Account: QC Site Content Editor (`_test_owned` signs the session in as the
# Editor; never TEST_USER). "Save" / "Publish" = the form's status=0 control.
# A Published record is unpublished first (guide section 4); a form submit
# on an Unpublished record stores without publishing, so the record is then
# driven to Published through the documented row transitions
# (chairman_singleton.to_published). Public checks: fresh logged-out context.
# ===========================================================================
from cms.tests.chairman_message.chairman_singleton import to_published as _to_published
from cms.tests.live_status_cases import PicklistRecord, status_draft_case, status_published_case
from cms.tests.live_write_guard import log_live_write

P34_WORKFLOW_BUDGET = 150.0


def _p34_editable(admin: ChairmanMessageAdminPage, tc: str) -> None:
    """Published -> Unpublished, logged before the click."""
    admin.open_record()
    if admin.current_status() == STATUS_PUBLISHED:
        log_live_write(RECORD, "<workflow>", STATUS_UNPUBLISHED, tc, action="unpublish",
                       note="make the form editable (guide section 4)")
        _make_editable(admin)
    admin.open_record()


def _p34_published(admin: ChairmanMessageAdminPage, tc: str) -> str:
    """Leave the record Published (documented transitions), logged first."""
    admin.open_record()
    status = admin.current_status()
    if status != STATUS_PUBLISHED:
        log_live_write(RECORD, "<workflow>", STATUS_PUBLISHED, tc, action="publish",
                       note=f"the case's Publish / end state (was {status})")
        _to_published(admin, budget=P34_WORKFLOW_BUDGET)
        admin.open_record()
    return admin.current_status()


@contextmanager
def _p34_end_published(admin: ChairmanMessageAdminPage, tc: str):
    """Wraps a writing case: 78261 is always driven back to Published. A
    failed restore never masks the case's own failure; on a passing case it
    fails the test (the live page is not Published)."""
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        problem = ""
        try:
            _p34_published(admin, tc)
        except Exception as exc:  # noqa: BLE001 -- reported below
            problem = repr(exc)
            _attach("END STATE NOT RESTORED -- check 78261 by hand", problem)
        if problem and not failed:
            raise AssertionError(f"the case passed but {RECORD} was not left Published: {problem}")


def _p34_click_save(admin: ChairmanMessageAdminPage) -> dict:
    """The form's Save / Publish control (status=0, label-independent)."""
    admin.submit_via(admin.PUBLISH_SUBMIT)
    refused = admin.refusal_visible()
    return {"refusal": admin.refusal_text() if refused else "", "success": ""}


def _p34_empty_optional(page, browser, tc: str, key: str, label: str, check: str) -> None:
    """134829 / 134834: an OPTIONAL field left empty does not block Publish;
    the public EN page renders the message with no broken link."""
    with _test_owned(page, (key,), f"tc_{tc}") as (admin, snap), _p34_end_published(admin, tc):
        _attach(f"{label} before (precondition: empty)", repr(snap["fields"][(key, EN)]))
        with allure.step(f"Leave {label} empty, keep every mandatory field, click Publish"):
            _p34_editable(admin, tc)
            _write(admin, key, "", EN)
            log_live_write(RECORD, f"{label} (EN)", "", tc, action="publish", note="case step 2: left empty")
            said = _p34_click_save(admin)
            status = _p34_published(admin, tc)
        with allure.step("Reload the record"):
            admin.open_record()
            stored = _read(admin, key, EN)
        _attach("save outcome (wording/toast is a note, not asserted)", said)
        assert not said["refusal"], f"Publish with an empty {label} was refused: {said['refusal']!r}"
        assert stored == "", f"{label} reads {stored!r} after the save, expected empty"
        assert status == STATUS_PUBLISHED, f"the record is {status!r} after Publish"
        with allure.step("Open the Chairman's Message page in English (logged-out visitor)"):
            with _visitor(browser) as pub:
                rendered = _public(pub, lambda p: bool(p.all_key_sections_visible().get("message_body")))
                anchors = _public_once(pub, lambda p: p.content_anchors()) or []
        _attach("content anchors on the public page", anchors)
        assert rendered, "the public Chairman's Message page did not render the message"
        if check == "label":
            empty = [a for a in anchors if (a.get("href") or "").strip() and not a.get("text")]
            assert not empty, f"an empty / broken link label is displayed: {empty}"
        else:
            bad = [a for a in anchors
                   if (a.get("href") or "").strip().lower() in ("", "#", "http://", "https://", "about:blank")
                   or (a.get("href") or "").strip().lower().startswith("javascript:")]
            assert not bad, f"an anchor points to an empty or malformed destination: {bad}"


@_field_case("Hyperlink Title")
@allure.title("Verify that an empty Hyperlink Title is allowed because the field is optional")
@allure.label("testcase", "134829")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134829
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134829")
@pytest.mark.timeout(480)
@CHAIRMAN_GROUP
def test_134829_empty_hyperlink_title_allowed(page, browser):
    block_live_singleton_write(RECORD, "publish with an empty Hyperlink Title", tc_id="134829")
    _p34_empty_optional(page, browser, "134829", "hyperlink_title", "Hyperlink Title", "label")


@_field_case("Hyperlink URL")
@allure.title("Verify that a valid Hyperlink URL is accepted and saved")
@allure.label("testcase", "134831")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134831
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134831")
@pytest.mark.timeout(480)
@CHAIRMAN_GROUP
def test_134831_valid_hyperlink_url_saved(page):
    tc = "134831"
    block_live_singleton_write(RECORD, f"save of Hyperlink URL {QC_URL}", tc_id=tc)
    with _test_owned(page, ("hyperlink_url",), f"tc_{tc}") as (admin, snap), _p34_end_published(admin, tc):
        if snap["fields"][("hyperlink_url", EN)] == QC_URL:
            # Already the case's value: an interim valid URL first, so the
            # case's own save is a real change.
            with allure.step("Interim write: the field already holds the case's value"):
                _p34_editable(admin, tc)
                interim = f"{QC_URL}/?qctest={tc}"
                admin.fill("hyperlink_url", interim)
                log_live_write(RECORD, "Hyperlink URL (EN)", interim, tc, action="publish", note="interim value")
                _p34_click_save(admin)
        with allure.step(f"Enter {QC_URL!r} as the Hyperlink URL and click Save"):
            _p34_editable(admin, tc)
            admin.fill("hyperlink_url", QC_URL)
            log_live_write(RECORD, "Hyperlink URL (EN)", QC_URL, tc, action="publish", note="case step 2")
            said = _p34_click_save(admin)
        with allure.step("Reload the record"):
            admin.open_record()
            stored = admin.value("hyperlink_url")
        _attach("save outcome (wording/toast is a note, not asserted)", said)
        assert not said["refusal"], f"the save was refused: {said['refusal']!r}"
        assert stored == QC_URL, f"Hyperlink URL reads {stored!r}, expected {QC_URL!r}"


@_field_case("Hyperlink URL")
@allure.title("Verify that an empty Hyperlink URL is allowed because the field is optional")
@allure.label("testcase", "134834")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134834
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134834")
@pytest.mark.timeout(480)
@CHAIRMAN_GROUP
def test_134834_empty_hyperlink_url_allowed(page, browser):
    block_live_singleton_write(RECORD, "publish with an empty Hyperlink URL", tc_id="134834")
    _p34_empty_optional(page, browser, "134834", "hyperlink_url", "Hyperlink URL", "href")


def _p34_picklist(admin: ChairmanMessageAdminPage) -> PicklistRecord:
    return PicklistRecord(
        record=RECORD,
        entry_code=CHAIRMAN_MESSAGE_ENTRY_CODE,
        form=admin,
        open_form=lambda: admin.open_record(),
        save=lambda _authoring: _p34_click_save(admin),
        open_list=lambda: admin.open_entries_list(locale=EN),
        budget=P34_WORKFLOW_BUDGET,
    )


@_field_case("Status")
@allure.title("Verify that the Status dropdown offers and stores the Draft value")
@allure.label("testcase", "134835")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134835
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134835")
@pytest.mark.timeout(480)
@CHAIRMAN_GROUP
def test_134835_status_dropdown_stores_draft(page):
    block_live_singleton_write(RECORD, "Status picklist = Draft, then back to Published", tc_id="134835")
    admin = ChairmanMessageAdminPage(page)
    admin.sign_in(ROLE_EDITOR)
    # "The dropdown lists exactly Draft and Published" -> exact set asserted;
    # the observed list is attached either way.
    status_draft_case(_p34_picklist(admin), "134835", exact_options=True)


@_field_case("Status")
@allure.title("Verify that the Status dropdown offers and stores the Published value")
@allure.label("testcase", "134836")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.tc_134836
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134836")
@pytest.mark.timeout(480)
@CHAIRMAN_GROUP
def test_134836_status_dropdown_stores_published(page):
    block_live_singleton_write(RECORD, "Status picklist Draft precondition, then Published", tc_id="134836")
    admin = ChairmanMessageAdminPage(page)
    admin.sign_in(ROLE_EDITOR)
    status_published_case(_p34_picklist(admin), "134836")

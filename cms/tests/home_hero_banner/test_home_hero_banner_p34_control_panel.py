"""
cms/tests/home_hero_banner/test_home_hero_banner_p34_control_panel.py —
PBI 129367 (QC-HOME-001 — Hero Banner), suite 134447: the P3 cases classed
High / Medium for the 2026-10-15 Phase 3 run (PBI running rules, rule 2).
Low and character-limit cases are not scripted here.

Same ground rules as test_home_hero_banner_fields_control_panel.py: disposable
`QCTEST-<tc>-*` slides / counters, Site Content Editor unless the case names
the Author, nothing deleted (run with QC_ALLOW_LIVE_SINGLETON_WRITES=1; rows
are kept and logged), message wording not asserted (rule 17), public reads in
a logged-out context.

Disclosed adaptations:
  - 135077 / 135075 / 135094: Display Order values 9900 instead of 1 (multiples
    of 100, after every real row); -1 and 0 are typed as the case says.
  - 135092: a 3.5 MB icon. The case says 2.5 MB, but up to 3 MB accepted is the
    project's tolerance, so only > 3 MB accepted could be a finding.
  - 135090: a PNG icon (the case's SVG is a D&M type question, not a size one).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import allure
import pytest

from cms.pages.components.disposable_object_admin import ROLE_AUTHOR, ROLE_EDITOR
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
)
from cms.pages.home_hero_banner.hero_banner_fields_admin_page import (
    AchievementCounterFieldsAdminPage as Counter,
    HeroSlideFieldsAdminPage as Slide,
)
from cms.tests import authoring_checks as ac
from config.settings import control_panel_url
from cms.tests.live_write_guard import LiveRecord, log_live_write

pytestmark = [pytest.mark.control_panel, pytest.mark.pbi_129367]


def _img(tag: str, fmt: str, side: int, noisy: bool = False) -> str:
    from PIL import Image

    path = Path(tempfile.gettempdir()) / f"QCTEST-{tag}.{fmt.lower()}"
    if noisy:
        img = Image.frombytes("RGB", (side, side), os.urandom(side * side * 3))
    else:
        img = Image.new("RGB", (side, side), (40, 90, 30))
    img.save(path, "JPEG" if fmt.lower() == "jpg" else fmt.upper(), **({"quality": 100} if fmt == "jpg" else {}))
    return str(path)


def _big_png(tag: str) -> str:
    path = _img(tag, "png", 1100, noisy=True)
    assert Path(path).stat().st_size > 3 * 1024 * 1024, f"{path} is only {Path(path).stat().st_size} bytes"
    return path


# ---------------------------------------------------------------------------
# forms render
# ---------------------------------------------------------------------------
@allure.title("Hero Banner admin form renders all fields of the field table")
@pytest.mark.ui
@pytest.mark.tc_134995
def test_slide_form_renders_all_fields(page):
    ac.check_form_renders(page, Slide, ["image", "title_en", "title_ar", "subtitle_en", "subtitle_ar",
                                        "b1_label_en", "b1_label_ar", "b1_link", "b2_label_en",
                                        "b2_label_ar", "b2_link", "display_order", "active_status"])


@allure.title("Achievement Counter admin form renders all counter fields")
@pytest.mark.ui
@pytest.mark.tc_134996
def test_counter_form_renders_all_fields(page):
    ac.check_form_renders(page, Counter, ["title_en", "title_ar", "value", "display_order", "counter_active"])
    assert page.get_by_role("textbox", name=Counter(page).label_pattern("Counter Icon Select File")).count() \
        or page.locator('input[name="ObjectField_counterIcon"]').count(), "Counter Icon picker is missing"


# ---------------------------------------------------------------------------
# lifecycle
# ---------------------------------------------------------------------------
@allure.title("Author submitting a draft slide lands on Pending Review, not public")
@pytest.mark.functional_high
@pytest.mark.tc_135020
def test_author_submit_draft_slide_pending_review(page, browser):
    """Account: Site Content Author (the case's review path — an Editor's
    submit publishes straight away)."""
    admin = Slide(page)
    title = ac.run_title(135020, "author")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.open_form(ROLE_AUTHOR)
        assert not admin.has_admin_toolbar(), ac.NOT_ROLE
        admin.fill_required(title, active=True)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_DRAFT, f"{title!r} was not saved as Draft"
        admin.open_entry_by_edit_link(title)
        admin.submit_for_review()
        status = admin.status_of(title, ROLE_AUTHOR)
        assert status == STATUS_PENDING_REVIEW, f"Author submit left the slide {status!r}, not Pending Review"
        anon.goto(control_panel_url("/en/home"), wait_until="domcontentloaded")
        assert title not in anon.locator("body").inner_text(), "a Pending Review slide is visible to visitors"
    finally:
        ac._close(ctx)
        ac.dispose(admin, title, 135020)


@allure.title("Preview shows the draft slide as it will appear, without publishing")
@pytest.mark.functional_high
@pytest.mark.tc_135021
def test_preview_draft_slide(page, browser):
    """Account: Editor. Healed 2026-10-15: with Active Status unticked the
    Preview renders no slide at all (run 1), so the Draft is saved with Active
    ticked — the workflow gate (Draft) still keeps it off the live carousel,
    and the logged-out read below checks exactly that."""
    admin = Slide(page)
    title = ac.run_title(135021, "preview")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True)
        admin.fill("b1_label_en", "Preview CTA One")
        admin.fill("b2_label_en", "Preview CTA Two")
        admin.save_as_draft()
        admin.open_list(ROLE_EDITOR)
        url = admin.row_preview_url(title)
        assert url, f"{title!r}: the row offers no Preview link"
        admin.open(url)
        page.wait_for_load_state("domcontentloaded")
        body = page.locator("body").inner_text()
        for text in (title, "Preview CTA One", "Preview CTA Two"):
            assert text in body, f"Preview does not render {text!r}"
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, "Preview changed the record's status"
        anon.goto(control_panel_url("/en/home"), wait_until="domcontentloaded")
        assert title not in anon.locator("body").inner_text(), "the previewed draft leaked to visitors"
    finally:
        ac._close(ctx)
        ac.dispose(admin, title, 135021)


@allure.title("Success toast is in Arabic when the CMS UI language is Arabic")
@pytest.mark.functional_high
@pytest.mark.tc_135030
def test_success_toast_arabic_when_ui_arabic(page):
    """Account: Editor. The CMS UI is switched to Arabic through the URL locale
    (/ar/), never through the shared account's language preference (locale
    drift, qa-environment-notes § 2). The QCTEST slide is filled and saved as
    Draft through the English UI (English-only locators), reopened under /ar/
    and published there; Active Status stays unticked so it never reaches the
    live carousel. The submit button is picked by its DOM position among the
    form's status buttons, read on the English form, because its label is
    localised."""
    import re

    from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
    from cms.tests.home_hero_banner.test_home_hero_banner_fields_control_panel import _retire_slide

    admin = Slide(page)
    title = ac.run_title(135030, "ar-toast")
    status_buttons = 'form button[type="submit"][name="status"]'
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=False)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved as Draft"
        admin.open_entry_by_edit_link(title)
        labels = [t.strip() for t in page.locator(status_buttons).all_inner_texts()]
        submit_idx = next((i for i, t in enumerate(labels) if t in ("Submit for Review", "Publish")), None)
        assert submit_idx is not None, f"no Submit for Review button on the English form: {labels}"
        # The edit URL may carry /en/ or no locale segment at all
        # (https://qcdev…/web/qatar-chamber/manage-…?editEntry=…, seen 2026-10-18).
        if re.search(r"ihorizons\.com/en(/|$)", page.url):
            ar_url = re.sub(r"ihorizons\.com/en(/|$)", r"ihorizons.com/ar\1", page.url, count=1)
        else:
            ar_url = re.sub(r"ihorizons\.com/", "ihorizons.com/ar/", page.url, count=1)
        assert ar_url != page.url, f"could not build the Arabic URL from {page.url}"
        # domcontentloaded, not load/networkidle: the chatbot widget keeps the
        # network busy and `load` did not fire within 30 s (2026-10-18).
        page.goto(ar_url, wait_until="domcontentloaded")
        page.locator(status_buttons).nth(submit_idx).wait_for(state="visible", timeout=30000)
        assert page.locator("html").get_attribute("lang", timeout=10000).lower().startswith("ar"), \
            "the CMS UI did not switch to Arabic"
        log_live_write(LiveRecord("hero-banner-slide", title, "disposable QCTEST record"), "<workflow>",
                       "Published (Active unticked)", 135030, action="publish", note="unpublished in finally")
        page.on("dialog", lambda d: d.accept())
        page.locator(status_buttons).nth(submit_idx).click()
        # Rule 17: a missing / differently worded toast is not a bug, so the
        # toast is read if it shows (up to 15 s) and never blocks the case.
        try:
            page.locator(admin.SAVE_SUCCESS_TOAST).first.wait_for(state="visible", timeout=15000)
        except Exception:  # noqa: BLE001
            pass
        text = " ".join(page.locator(admin.SAVE_SUCCESS_TOAST).all_inner_texts()).strip()
        allure.attach(text or "(no toast shown)", name="toast text", attachment_type=allure.attachment_type.TEXT)
        page.screenshot(path="reports/manual-exec-129367-135030-ar-submit.png")
        from cms.tests.home_hero_banner.test_home_hero_banner_control_panel import LIVE_STATUSES, _wait_status

        status = _wait_status(admin, title)
        assert status in LIVE_STATUSES, f"{title!r} was not published from the Arabic UI (status {status!r})"
        if text:
            assert re.search(r"[؀-ۿ]", text), f"the success toast is not in Arabic: {text!r}"
    finally:
        _retire_slide(admin, title, 135030)


# ---------------------------------------------------------------------------
# optional fields left empty (P3 Low, run on the QA lead's request 2026-10-18)
# ---------------------------------------------------------------------------
def _saved_entry_code(page) -> str:
    """The entry code a save lands on (`?previewEntry=<code>`)."""
    import re

    m = re.search(r"previewEntry=([0-9a-f-]{36})", page.url)
    return m.group(1) if m else ""


def _delete_by_code(admin, code: str, tc: int, marker: str = "") -> None:
    """Teardown for a row this test created itself and identified by the code
    its own save returned (it has no QCTEST title by design of the case)."""
    from cms.pages.components.object_authoring_page import ObjectAuthoringPage as OAP

    if not code:
        return
    try:
        admin.open_list(ROLE_EDITOR)
        admin._search_rows(code if not marker else marker)
        log_live_write(LiveRecord(admin.SLUG, marker or code, code), "<delete>", code, tc, action="delete",
                       note="row created by this test (code from its own save URL)")
        OAP._run_row_action(admin, code, "delete")
    except Exception:  # noqa: BLE001 — teardown never masks the result
        pass


@allure.title("Empty Banner Subtitle (EN) is accepted and the slide renders without a subtitle")
@pytest.mark.functional_low
@pytest.mark.tc_135044
def test_empty_subtitle_en_accepted(page):
    """Editor saves a QCTEST slide with Subtitle (EN) empty; it saves, and the
    reopened form keeps the subtitle empty."""
    admin = Slide(page)
    title = ac.run_title(135044, "no-sub-en")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title)
        admin.fill("subtitle_ar", "تمكين القطاع الخاص")
        admin.save_as_draft()
        assert not admin.refusal_visible(2000), f"save was refused: {admin.refusal_text()}"
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved"
        admin.open_entry_by_edit_link(title)
        assert admin.value("subtitle_en") == "", f"Subtitle (EN) stored {admin.value('subtitle_en')!r}"
    finally:
        ac.dispose(admin, title, 135044)


@allure.title("Empty Banner Subtitle (AR) is accepted")
@pytest.mark.functional_low
@pytest.mark.tc_135047
def test_empty_subtitle_ar_accepted(page):
    admin = Slide(page)
    title = ac.run_title(135047, "no-sub-ar")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title)
        admin.fill("subtitle_en", "Empowering Qatar's private sector.")
        admin.save_as_draft()
        assert not admin.refusal_visible(2000), f"save was refused: {admin.refusal_text()}"
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved"
        admin.open_entry_by_edit_link(title)
        assert admin.value("subtitle_ar") == "", f"Subtitle (AR) stored {admin.value('subtitle_ar')!r}"
    finally:
        ac.dispose(admin, title, 135047)


@allure.title("A counter with every field empty saves")
@pytest.mark.functional_low
@pytest.mark.tc_135081
def test_counter_all_fields_empty_saves(page):
    """Editor saves an Achievement Counter with every field empty (the case's
    "all counter fields left blank"). It has no title to find it by, so the
    row is identified by the code its own save returns, and deleted by it."""
    admin = Counter(page)
    code = ""
    try:
        admin.open_form(ROLE_EDITOR)
        admin.save_as_draft()
        code = _saved_entry_code(page)
        assert not admin.refusal_visible(2000), f"save was refused: {admin.refusal_text()}"
        assert code, f"no saved entry code in {page.url} — the empty counter was not stored"
        admin.open_list(ROLE_EDITOR)
        assert admin._search_rows(code) == [code], f"the empty counter {code} is not in the list"
    finally:
        _delete_by_code(admin, code, 135081)


@allure.title("Empty Counter Title (AR) is accepted")
@pytest.mark.functional_low
@pytest.mark.tc_135084
def test_empty_counter_title_ar_accepted(page):
    _counter_saved(page, 135084, "no-ar", {"value": "50K+", "display_order": "9900"}, {"title_ar": ""})


@allure.title("Empty Counter Icon is accepted")
@pytest.mark.functional_low
@pytest.mark.tc_135093
def test_empty_counter_icon_accepted(page):
    """No icon attached; the counter saves and reopens with its value."""
    _counter_saved(page, 135093, "no-icon", {"value": "60K+", "display_order": "9900"}, {"value": "60K+"})


@allure.title("Counter with Title and Display Order both empty saves")
@pytest.mark.functional_low
@pytest.mark.tc_135096
def test_counter_title_and_order_empty_saves(page):
    """Counter Title (EN) and Counter Display Order empty; Counter Value
    carries a unique marker so the row can be found and read back."""
    import uuid

    admin = Counter(page)
    marker = f"Q96{uuid.uuid4().hex[:5]}"
    code = ""
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("value", marker)
        admin.save_as_draft()
        code = _saved_entry_code(page)
        assert not admin.refusal_visible(2000), f"save was refused: {admin.refusal_text()}"
        assert code, f"no saved entry code in {page.url} — the counter was not stored"
        admin.open_entry_by_code(code)
        assert admin.value("value") == marker, f"Counter Value stored {admin.value('value')!r}"
        # The case asserts only that the save succeeds. An empty Counter Display
        # Order is stored as the platform default 0 (read 2026-10-18), noted only.
        allure.attach(f"display_order stored {admin.value('display_order')!r}", name="stored display order",
                      attachment_type=allure.attachment_type.TEXT)
        assert admin.value("title_en") == "", f"Counter Title (EN) stored {admin.value('title_en')!r}"
        assert admin.value("display_order") in ("", "0"), f"Display Order stored {admin.value('display_order')!r}"
    finally:
        _delete_by_code(admin, code, 135096, marker)


# ---------------------------------------------------------------------------
# whitespace-only mandatory values
# ---------------------------------------------------------------------------
WHITESPACE = [
    pytest.param("title_en", id="135038", marks=pytest.mark.tc_135038),
    pytest.param("title_ar", id="135042", marks=pytest.mark.tc_135042),
    pytest.param("b1_label_en", id="135052", marks=pytest.mark.tc_135052),
    pytest.param("b1_label_ar", id="135056", marks=pytest.mark.tc_135056),
    pytest.param("b1_link", id="135061", marks=pytest.mark.tc_135061),
    pytest.param("b2_label_en", id="135065", marks=pytest.mark.tc_135065),
    pytest.param("b2_label_ar", id="135069", marks=pytest.mark.tc_135069),
    pytest.param("b2_link", id="135074", marks=pytest.mark.tc_135074),
]


@allure.title("Whitespace-only mandatory Hero Banner field is refused")
@pytest.mark.parametrize("key", WHITESPACE)
def test_whitespace_only_refused(page, request, key):
    ac.check_whitespace_refused(page, Slide, int(request.node.callspec.id), key)


# ---------------------------------------------------------------------------
# optional subtitle + display order
# ---------------------------------------------------------------------------
SUBTITLE = [
    pytest.param("subtitle_en", "Empowering Qatar's private sector since 1963.", id="135043",
                 marks=pytest.mark.tc_135043),
    pytest.param("subtitle_ar", "تمكين القطاع الخاص القطري منذ عام 1963.", id="135046",
                 marks=pytest.mark.tc_135046),
]


@allure.title("Valid Banner Subtitle within the limit is saved")
@pytest.mark.parametrize("key,value", SUBTITLE)
def test_valid_subtitle_saved(page, request, key, value):
    ac.check_valid_persists(page, Slide, int(request.node.callspec.id), key, value, short=key.replace("_", "-"))


@allure.title("Valid positive Display Order is saved")
@pytest.mark.tc_135075
def test_valid_display_order_saved(page):
    ac.check_valid_persists(page, Slide, 135075, "display_order", "9800", short="order")


@allure.title("Empty Display Order is refused")
@pytest.mark.tc_135076
def test_empty_display_order_refused(page):
    ac.check_empty_refused(page, Slide, 135076, "display_order")


@allure.title("Negative and zero Display Order are refused")
@pytest.mark.tc_135077
@pytest.mark.parametrize("bad", ["-1", "0"])
def test_negative_or_zero_display_order_refused(page, bad):
    ac.check_value_refused(page, Slide, 135077, "display_order", bad, short=f"order{bad}")


# ---------------------------------------------------------------------------
# Achievement Counter
# ---------------------------------------------------------------------------
def _counter_saved(page, tc: int, short: str, fill: dict, check: dict, files: dict | None = None) -> None:
    """Editor saves a QCTEST counter (Counter Title (EN) carries the QCTEST
    name) as Draft, reopens it and reads `check` back."""
    admin = Counter(page)
    title = ac.run_title(tc, short)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("title_en", title)
        for key, val in fill.items():
            admin.fill(key, val)
        for key, path in (files or {}).items():
            admin.upload_file(key, path)
        admin.save_as_draft()
        assert not admin.refusal_visible(2000), f"save was refused: {admin.refusal_text()}"
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved"
        admin.open_entry_by_edit_link(title)
        for key, want in check.items():
            got = admin.flag(key) if isinstance(want, bool) else admin.value(key)
            assert got == want, f"{key}: stored {got!r}, expected {want!r}"
        for key in files or {}:
            assert admin.current_file_name(key) or admin.page.locator('input[name="ObjectField_counterIcon"]').input_value(), \
                f"{key}: no file attached after save + reopen"
    finally:
        ac.dispose(admin, title, tc)


@allure.title("Valid Counter Title (EN) is saved")
@pytest.mark.tc_135080
def test_valid_counter_title_en_saved(page):
    _counter_saved(page, 135080, "Members", {"value": "50K+", "display_order": "9900"}, {"value": "50K+"})


@allure.title("Valid Counter Title (AR) is saved")
@pytest.mark.tc_135083
def test_valid_counter_title_ar_saved(page):
    _counter_saved(page, 135083, "Members-ar", {"title_ar": "الأعضاء", "value": "50K+", "display_order": "9900"},
                   {"title_ar": "الأعضاء"})


@allure.title("Valid Counter Icon upload is accepted")
@pytest.mark.tc_135090
def test_valid_counter_icon_accepted(page):
    _counter_saved(page, 135090, "icon", {"value": "50K+", "display_order": "9900"}, {},
                   files={"Counter Icon": _img("135090-members-icon", "png", 64)})


@allure.title("Counter Icon in an unsupported format is refused")
@pytest.mark.tc_135091
def test_counter_icon_unsupported_refused(page):
    admin = Counter(page)
    title = ac.run_title(135091, "icon-bad")
    bad = Path(tempfile.gettempdir()) / "QCTEST-135091-icon.exe"
    bad.write_bytes(b"MZ" + os.urandom(2048))
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("title_en", title)
        log_live_write(LiveRecord("achievement-counter", title, "disposable QCTEST record"), "Counter Icon",
                       bad.name, 135091, action="attempt")
        assert admin.upload_file_expect_rejected("Counter Icon", admin.disposable_copy(str(bad), "135091")), \
            "an .exe was accepted as Counter Icon"
    finally:
        ac.dispose(admin, title, 135091)


@allure.title("Counter Icon over the size limit is refused")
@pytest.mark.tc_135092
def test_counter_icon_over_size_refused(page):
    admin = Counter(page)
    title = ac.run_title(135092, "icon-big")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("title_en", title)
        log_live_write(LiveRecord("achievement-counter", title, "disposable QCTEST record"), "Counter Icon",
                       "3.5 MB png", 135092, action="attempt")
        assert admin.upload_file_expect_rejected("Counter Icon", admin.disposable_copy(_big_png("135092-icon-large"), "135092")), \
            "a > 3 MB icon was accepted"
    finally:
        ac.dispose(admin, title, 135092)


@allure.title("Counter Display Order is accepted with a Counter Title set")
@pytest.mark.tc_135094
def test_counter_display_order_accepted(page):
    _counter_saved(page, 135094, "order", {"value": "50K+", "display_order": "9900"}, {"display_order": "9900"})


@allure.title("Counter Display Order is required once Counter Title is set")
@pytest.mark.tc_135095
def test_counter_display_order_required_with_title(page):
    admin = Counter(page)
    title = ac.run_title(135095, "no-order")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("title_en", title)
        admin.fill("value", "50K+")
        ac._submit_and_expect_refusal(admin, title, "Counter Display Order empty with Counter Title set")
    finally:
        ac.dispose(admin, title, 135095)


@allure.title("Counter Active Status = True is saved")
@pytest.mark.tc_135097
def test_counter_active_true_saved(page):
    _counter_saved(page, 135097, "active-on", {"value": "50K+", "display_order": "9900", "counter_active": "true"},
                   {"counter_active": True})


@allure.title("Counter Active Status = False is saved")
@pytest.mark.tc_135098
def test_counter_active_false_saved(page):
    _counter_saved(page, 135098, "active-off", {"value": "50K+", "display_order": "9900", "counter_active": ""},
                   {"counter_active": False})

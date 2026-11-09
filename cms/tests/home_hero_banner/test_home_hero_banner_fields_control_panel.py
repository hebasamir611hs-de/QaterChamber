"""
cms/tests/home_hero_banner/test_home_hero_banner_fields_control_panel.py —
PBI 129367 (QC-HOME-001 — Hero Banner), suite 134447: the P1/P2 field and
access cases, added 2026-10-15 (Phase 3).

Every case runs on a disposable `QCTEST-<tc_id>-*` Hero Banner Slide or
Achievement Counter (HeroSlideFieldsAdminPage / AchievementCounterFieldsAdminPage),
through cms/tests/authoring_checks.py. Account: Site Content Editor, except the
denial case (Site Member). The two real QCDEMO slides and three real counters
are never opened for edit.

Nothing is deleted on qcdev (PBI running rules, rule 10): run with
`QC_ALLOW_LIVE_SINGLETON_WRITES=1` and every QCTEST row is kept and logged to
reports/live-writes-*.jsonl for the QA lead to clean.

Disclosed adaptations:
  - Display Order 9900 instead of the cases' small numbers (multiples of 100,
    after every real slide).
  - "Saved" is read back from a Draft (Save as Draft + reopen). Publishing a
    QCTEST slide would put it into the live Home Page carousel.
  - Message wording is not asserted (PBI running rules, rule 17): the
    behaviour is — refused, and nothing published.
  - 135034 uses a 3.5 MB JPEG, as the case says. Up to 3 MB accepted is the
    project's tolerance, so only > 3 MB accepted is a finding.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import allure
import pytest

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.components.object_authoring_page import STATUS_DRAFT
from cms.pages.home_hero_banner.hero_banner_fields_admin_page import (
    AchievementCounterFieldsAdminPage as Counter,
    HeroSlideFieldsAdminPage as Slide,
)
from cms.tests import authoring_checks as ac
from cms.tests.live_write_guard import LiveRecord, log_live_write

pytestmark = [pytest.mark.control_panel, pytest.mark.pbi_129367]


def _png(tag: str, size: int) -> str:
    """A real PNG of about `size` bytes (random pixels do not compress)."""
    from PIL import Image

    side = max(40, int((size / 3) ** 0.5))
    path = Path(tempfile.gettempdir()) / f"QCTEST-{tag}.png"
    Image.frombytes("RGB", (side, side), os.urandom(side * side * 3)).save(path, "PNG")
    return str(path)


def _gif(tag: str) -> str:
    from PIL import Image

    path = Path(tempfile.gettempdir()) / f"QCTEST-{tag}.gif"
    Image.new("RGB", (400, 300), (120, 20, 40)).save(path, "GIF")
    return str(path)


def _big_jpg(tag: str) -> str:
    from PIL import Image

    path = Path(tempfile.gettempdir()) / f"QCTEST-{tag}-big.jpg"
    Image.frombytes("RGB", (2600, 2600), os.urandom(2600 * 2600 * 3)).save(path, "JPEG", quality=100)
    assert path.stat().st_size > 3 * 1024 * 1024, f"generated file is only {path.stat().st_size} bytes"
    return str(path)


# ---------------------------------------------------------------------------
# access
# ---------------------------------------------------------------------------
@allure.title("Site Content Editor can open Hero Banner management with the add form enabled")
@pytest.mark.auth
@pytest.mark.tc_135002
def test_editor_can_access_hero_banner_management(page):
    """Account: Site Content Editor. The manage page renders the create form
    (Save as Draft + Submit enabled) and the slide list."""
    admin = Slide(page)
    admin.open_form(ROLE_EDITOR)
    assert page.locator(admin.SAVE_AS_DRAFT_BUTTON).first.is_enabled(), "Save as Draft is not enabled"
    assert page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).first.is_enabled(), "Submit is not enabled"
    ac.check_form_renders(page, Slide, ["image", "title_en", "title_ar", "b1_link", "display_order"])


@allure.title("User without Hero Banner permission is denied Hero Banner management")
@pytest.mark.auth
@pytest.mark.tc_135003
def test_user_without_permission_denied_hero_banner(page):
    """Account: Site Member (signs in, no CMS role) — the account without the
    Hero Banner permission. Behaviour asserted: no form, no rows, a denial
    signal. The exact message wording is noted, not asserted (rule 17)."""
    ac.check_member_denied(page, Slide)


# ---------------------------------------------------------------------------
# Banner Image
# ---------------------------------------------------------------------------
@allure.title("Banner Image within size and format limits is accepted")
@pytest.mark.tc_135031
def test_banner_image_valid_upload_accepted(page):
    """qc-hero.png of about 1.8 MB is uploaded through the picker and stays
    attached after save + reopen."""
    ac.check_valid_persists(page, Slide, 135031, "image", _png("135031-qc-hero", int(1.8 * 1024 * 1024)),
                            short="img")


@allure.title("Slide without a Banner Image is refused")
@pytest.mark.tc_135032
def test_banner_image_missing_refused(page):
    ac.check_empty_refused(page, Slide, 135032, "image")


@allure.title("Banner Image in an unsupported format (.gif) is refused")
@pytest.mark.tc_135033
def test_banner_image_gif_refused(page):
    ac.check_file_refused(page, Slide, 135033, "image", _gif("135033-banner"))


@allure.title("Banner Image over 2 MB (3.5 MB) is refused")
@pytest.mark.tc_135034
def test_banner_image_over_size_refused(page):
    ac.check_file_refused(page, Slide, 135034, "image", _big_jpg("135034-banner-large"))


# ---------------------------------------------------------------------------
# text fields: valid value persists / empty value refused
# ---------------------------------------------------------------------------
VALID = [
    pytest.param("title_en", "Driving Business Growth", id="135035", marks=pytest.mark.tc_135035),
    pytest.param("title_ar", "دفع نمو الأعمال", id="135039", marks=pytest.mark.tc_135039),
    pytest.param("b1_label_en", "Explore Services", id="135049", marks=pytest.mark.tc_135049),
    pytest.param("b1_label_ar", "استكشف الخدمات", id="135053", marks=pytest.mark.tc_135053),
    pytest.param("b1_link", "https://qatarchamber.com/about-us", id="135057", marks=pytest.mark.tc_135057),
    pytest.param("b2_label_en", "Join Now", id="135062", marks=pytest.mark.tc_135062),
    pytest.param("b2_label_ar", "انضم الآن", id="135066", marks=pytest.mark.tc_135066),
    pytest.param("b2_link", "https://qatarchamber.com/membership", id="135070", marks=pytest.mark.tc_135070),
]


@allure.title("Valid Hero Banner field value is saved")
@pytest.mark.parametrize("key,value", VALID)
def test_valid_field_value_saved(page, request, key, value):
    tc = int(request.node.callspec.id)
    if key == Slide.TITLE_FIELD:
        value = f"{value} {ac._RUN_UID}"  # nothing is deleted, so a rerun must not collide
    ac.check_valid_persists(page, Slide, tc, key, value, short=key.replace("_", "-"))


EMPTY = [
    pytest.param("title_en", id="135036", marks=pytest.mark.tc_135036),
    pytest.param("title_ar", id="135040", marks=pytest.mark.tc_135040),
    pytest.param("b1_label_en", id="135050", marks=pytest.mark.tc_135050),
    pytest.param("b1_label_ar", id="135054", marks=pytest.mark.tc_135054),
    pytest.param("b1_link", id="135058", marks=pytest.mark.tc_135058),
    pytest.param("b2_label_en", id="135063", marks=pytest.mark.tc_135063),
    pytest.param("b2_label_ar", id="135067", marks=pytest.mark.tc_135067),
    pytest.param("b2_link", id="135071", marks=pytest.mark.tc_135071),
]


@allure.title("Empty mandatory Hero Banner field is refused")
@pytest.mark.parametrize("key", EMPTY)
def test_empty_mandatory_field_refused(page, request, key):
    ac.check_empty_refused(page, Slide, int(request.node.callspec.id), key)


INVALID_URL = [
    pytest.param("b1_link", id="135059", marks=pytest.mark.tc_135059),
    pytest.param("b2_link", id="135072", marks=pytest.mark.tc_135072),
]


@allure.title("Invalid URL format for a button link is refused")
@pytest.mark.parametrize("key", INVALID_URL)
def test_invalid_button_link_refused(page, request, key):
    """`not-a-url`. PBI running rules, rule 17: an accepted malformed link is
    NOT a bug on this project (no URL validation) — a failure here is
    recorded and reviewed, not filed."""
    ac.check_value_refused(page, Slide, int(request.node.callspec.id), key, "not-a-url", short="badurl")


# ---------------------------------------------------------------------------
# Active Status
# ---------------------------------------------------------------------------
def _active_saved(page, tc_id: int, active: bool) -> None:
    admin = Slide(page)
    title = ac.run_title(tc_id, f"active-{'on' if active else 'off'}")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=not active)
        admin.save_as_draft()
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        admin.set_flag("active_status", active)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} not listed after save"
        admin.open_entry_by_edit_link(title)
        assert admin.flag("active_status") is active, f"Active Status did not persist as {active}"
    finally:
        ac.dispose(admin, title, tc_id)


@allure.title("Slide Active Status = True is saved")
@pytest.mark.tc_135078
def test_active_status_true_saved(page):
    _active_saved(page, 135078, True)


@allure.title("Slide Active Status = False is saved")
@pytest.mark.tc_135079
def test_active_status_false_saved(page):
    _active_saved(page, 135079, False)


# ---------------------------------------------------------------------------
# Achievement Counter
# ---------------------------------------------------------------------------
@allure.title("Counter Value is accepted with a Counter Title set")
@pytest.mark.tc_135086
def test_counter_value_accepted_with_title(page):
    """Counter Title (EN) carries the QCTEST name; Value = 50K+."""
    admin = Counter(page)
    # Counter Title is capped at 30 characters on the form ("is 35 characters;
    # the maximum is 30", read live 2026-10-18), so the QCTEST name is kept short.
    title = ac.run_title(135086, "AM")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("title_en", title)
        admin.fill("title_ar", "الأعضاء النشطون")
        admin.fill("value", "50K+")
        admin.fill("display_order", "9900")
        admin.save_as_draft()
        assert not admin.refusal_visible(2000), f"save was refused: {admin.refusal_text()}"
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved"
        admin.open_entry_by_edit_link(title)
        assert admin.value("value") == "50K+", f"Counter Value did not persist: {admin.value('value')!r}"
    finally:
        ac.dispose(admin, title, 135086)


@allure.title("Counter Value is required once Counter Title is set")
@pytest.mark.tc_135087
def test_counter_value_required_with_title(page):
    """Counter Title set, Value empty, Submit: must be refused and nothing
    published. The counter form marks no field required (read live
    2026-10-15), so this checks the conditional rule the PBI states."""
    admin = Counter(page)
    # Unique per run (2026-10-18): the counter list shows codes, so the status
    # lookup is a text search — a leftover Published "QCTEST-135087-Active-
    # Members-<uid>" row from an older run matched the bare title and read as
    # "Published despite the refusal".
    title = ac.run_title(135087, f"Active-Members-{os.urandom(3).hex()}")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("title_en", title)
        admin.fill("title_ar", "الأعضاء النشطون")
        admin.fill("display_order", "9900")
        ac._submit_and_expect_refusal(admin, title, "Counter Value empty with Counter Title set")
    finally:
        ac.dispose(admin, title, 135087)


@allure.title("Slide with no counter title or value saves")
@pytest.mark.tc_135089
def test_slide_without_counters_saves(page):
    """A slide saved with no counter data (Counters Active Status unticked)
    saves with no counter validation."""
    admin = Slide(page)
    title = ac.run_title(135089, "no-counters")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title)
        admin.set_flag("counters_active", False)
        admin.save_as_draft()
        assert not admin.refusal_visible(2000), f"save was refused: {admin.refusal_text()}"
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved"
    finally:
        ac.dispose(admin, title, 135089)


# ---------------------------------------------------------------------------
# lifecycle (rewritten 2026-10-15 from the old module, which picked a library
# image that no longer exists and edited the real QCDEMO-02 slide)
# ---------------------------------------------------------------------------
def _publish_slide(admin: Slide, title: str, active: bool) -> None:
    """Shared with the lifecycle module (2026-10-18): logs the submit's network
    calls, refuses a duplicated record, polls the status (Published, or
    INACTIVE when Active Status is unticked)."""
    from cms.tests.home_hero_banner.test_home_hero_banner_control_panel import _publish

    _publish(admin, title, None, active=active)


def _retire_slide(admin: Slide, title: str, tc: int) -> None:
    """Unpublish (never delete) so a QCTEST slide leaves the live carousel."""
    from cms.pages.components.object_authoring_page import STATUS_PUBLISHED

    try:
        admin.open_list(ROLE_EDITOR)
        if admin.row_status_text(title) == STATUS_PUBLISHED:
            log_live_write(LiveRecord("hero-banner-slide", title, "disposable QCTEST record"),
                              "<workflow>", "Unpublished", tc, action="unpublish", note="teardown")
            admin.unpublish_entry(title)
    except Exception:  # noqa: BLE001 — teardown never masks the result
        pass
    ac.dispose(admin, title, tc)


@allure.title("Site Content Editor creates a new Hero Banner slide with all mandatory fields")
@pytest.mark.functional_high
@pytest.mark.tc_135009
def test_create_slide_with_mandatory_fields(page):
    admin = Slide(page)
    title = ac.run_title(135009, "new-slide")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title)
        admin.save_as_draft()
        assert not admin.refusal_visible(2000), f"save was refused: {admin.refusal_text()}"
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved"
        admin.open_entry_by_edit_link(title)
        for key in ("title_ar", "b1_label_en", "b1_link", "b2_label_en", "b2_link", "display_order"):
            assert admin.value(key) == Slide.FIELDS[key].default, f"{key} stored {admin.value(key)!r}"
        assert admin.value("image"), "Banner Image is not attached after save"
    finally:
        ac.dispose(admin, title, 135009)


@allure.title("Site Content Editor edits a published slide's title")
@pytest.mark.functional_high
@pytest.mark.tc_135013
def test_edit_published_slide_title(page):
    """The case's "Growth" -> "Sustainable Growth" on a QCTEST slide published
    with Active Status unticked (so it never shows in the live carousel); the
    real slides are not touched."""
    from cms.pages.components.object_authoring_page import STATUS_PUBLISHED

    admin = Slide(page)
    title = ac.run_title(135013, "Growth")
    new = ac.run_title(135013, "Sustainable-Growth")
    try:
        _publish_slide(admin, title, active=False)
        admin.open_entry_by_edit_link(title)
        if page.get_by_role("textbox", name=admin.label_pattern("Banner Title (EN)")).is_editable() is False:
            admin.unpublish_to_edit_as_draft()
        admin.fill("title_en", new)
        log_live_write(LiveRecord("hero-banner-slide", title, "disposable QCTEST record"), "Banner Title (EN)",
                          new, 135013, action="publish")
        admin.submit_for_review()
        from cms.tests.home_hero_banner.test_home_hero_banner_control_panel import LIVE_STATUSES, _wait_status

        status = _wait_status(admin, new)
        assert status in LIVE_STATUSES, f"edited slide {new!r} is {status or 'absent'!r}, not Published"
        admin.open_entry_by_edit_link(new)
        assert admin.value("title_en") == new, f"title stored {admin.value('title_en')!r}"
    finally:
        _retire_slide(admin, new, 135013)
        _retire_slide(admin, title, 135013)


@allure.title("Publishing a slide makes it visible on the Home Page")
@pytest.mark.functional_high
@pytest.mark.tc_135022
def test_published_slide_visible_on_home(page, browser):
    admin = Slide(page)
    title = ac.run_title(135022, "live")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish_slide(admin, title, active=True)
        from config.settings import control_panel_url

        # Healed 2026-10-15: page.url carries an /en prefix, so the old split
        # built ".../en/en/home" and never read the real Home Page.
        home_url = control_panel_url("/en/home")

        def _seen() -> bool:
            anon.goto(home_url, wait_until="domcontentloaded")
            return anon.locator(f"text={title}").count() > 0

        from core.utils.waits import WaitTimeoutError, wait_until
        try:
            wait_until(_seen, timeout=90, poll=5)
        except WaitTimeoutError:
            pass
        assert anon.locator(f"text={title}").count() > 0, f"published slide {title!r} is not in the Home Page slider"
    finally:
        ac._close(ctx)
        _retire_slide(admin, title, 135022)


@allure.title("Editor adds a new Achievement Counter item with valid data")
@pytest.mark.tc_135025
def test_add_achievement_counter_item(page):
    """Counters are their own object (read live 2026-10-15) — there is no
    slide-to-counter link field; the slide shows counters through its
    "Counters Active Status". The item is saved as a Draft QCTEST counter."""
    admin = Counter(page)
    title = ac.run_title(135025, "Members")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("title_en", title)
        admin.fill("title_ar", "الأعضاء")
        admin.fill("value", "50K+")
        admin.fill("display_order", "9900")
        admin.set_flag("counter_active", True)
        admin.save_as_draft()
        assert not admin.refusal_visible(2000), f"save was refused: {admin.refusal_text()}"
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved"
        admin.open_entry_by_edit_link(title)
        assert (admin.value("title_ar"), admin.value("value")) == ("الأعضاء", "50K+")
    finally:
        ac.dispose(admin, title, 135025)

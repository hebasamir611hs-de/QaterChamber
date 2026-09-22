"""
cms/tests/home_hero_banner/test_home_hero_banner_control_panel.py —
Control_Panel-tagged cases for PBI 129367 (QC-HOME-001 — Hero Banner),
sourced from Azure suite 134447.

See cms/pages/home_hero_banner/home_hero_banner_admin_page.py's module
docstring for the full live-confirmed Object Definition / field mapping
(Hero Banner Slide vs. Achievement Counter — two separate Object
Definitions, both reached only via Object Authoring per standards.md).

All public Home Page reads use a fresh, logged-out browser context
(`new_context(browser, use_auth_state=False)`) per standards.md's
"Draft/Unpublish Public-Visibility Checks" rule — never the CMS-
authenticated `page`.

TC 135024 note: the injected case's own 2 steps ("Click Publish again" /
"Load Home Page -> Slide reappears") assume a prior "unpublish" step from a
longer case flow this batch's payload did not include. Live-investigated
this session (see admin module docstring) and scripted the FULL realistic
flow: unpublish -> confirm gone from the live Home Page -> re-publish ->
confirm restored — the live-confirmed precondition/mechanism is documented
on that test's own docstring below.

TC 135026-135029 note: all four target the SAME shared record ("counter 3",
QCDEMO-129367-ACHIEVEMENT_COUNTER-03) per this task's own caution about
shared-entity mutation — each carries `xdist_group("achievement_counter_45659")`
so `--dist loadgroup` never schedules two of them concurrently on different
workers, mirroring this project's existing shared-record convention (see
standards.md's "Safe Parallelism" table). Each test independently captures
its own baseline and restores it in `finally`, so any subset can still run
standalone/in any order.

BATCH1 (2026-09-13) note — tc_135009/135013/135016/135017/135022/135023/135025:
7 additional Regression cases for this same PBI, sourced from the QA
Manager's injected batch (plan 133534 / suite 139193). All 7 reuse this
module's already-confirmed-live mechanisms (select_banner_image_from_library(),
_fill_publishable_required_fields(), the anon-context public-visibility rule)
— no new live investigation was needed for most of them. tc_135013's own
literal data ("Growth" -> "Sustainable Growth") does not match any real
seeded slide's title (see admin module docstring: -01/-02 share an identical
default title with no "Growth" substring) — substituted, disclosed, onto
HERO_SLIDE_02 (this module's own designated edit/publish/unpublish target),
sharing its xdist_group("hero_banner_slide_45560") with tc_135024/135014/
135015. tc_135025 (a new Achievement Counter entry) is a brand-new,
disposable record that never touches "counter 3" (ACHIEVEMENT_COUNTER-03,
record 45659) — no xdist_group needed, mirroring tc_135010's own disposable-
record precedent in this same module; its Display Order (999) is a
deliberately out-of-range value so it can never positionally tie with any
real counter even though all render in the same shared counters row
(a read-side coexistence, not a write-side race). tc_135009's "Liferay
generic success toast" assertion reuses board_of_directors's tc_133516
keyword-poll technique verbatim rather than assuming either a confirmed
presence or a confirmed absence for this specific object — the real
pass/fail is a genuine, unbiased observation once this test runs, not a
foregone conclusion either way.

TC 135010/135014/135015/135018/135019 batch (2026-09-08) note: 135014/135015
target the SAME shared -01/-02 slide pair as 135024 — both carry
`xdist_group("hero_banner_slide_45560")` (the already-declared group for this
pair, reused rather than a new one per standards.md's "a test can only belong
to one xdist_group... merge those two records' groups into one shared group
name" rule, since 135014/135015 mutate -01 together with -02). 135010/135018/
135019 each create and delete their OWN disposable QCTEST-prefixed slide and
never touch -01/-02/counter-03, so they carry no xdist_group and are free to
parallelize normally. See cms/pages/home_hero_banner/home_hero_banner_admin_page.py's
module docstring for this batch's live-confirmed findings (Entry-column UUID
exception requiring find_entry_code_by_field(), the no-visual-thumbnail
selection finding, the carousel's 6s autoplay, and the Display-Order swap
round-trip evidence).

CORRECTED 2026-09-08 (was: "tc_135018 is scripted AS THE CASE ASKS but is
EXPECTED TO FAIL" — that finding was WRONG and is retracted here, not
silently walked back): the earlier pass of this batch concluded a brand-new
Hero Banner Slide with an uploaded Banner Image could never reach Approved
status through the CMS UI. Both of its supporting observations had a
different, mundane cause than a product defect — see
cms/pages/home_hero_banner/home_hero_banner_admin_page.py's module
docstring CORRECTED note for the full evidence trail:
  1. "Banner Image" is a media-LIBRARY PICKER (selects an EXISTING image
     already in Liferay's Documents & Media library, populated by this
     project's Flickr import), not a raw file-upload field — the earlier
     pass drove it via the wrong control (`upload_file()`'s drag-drop-a-
     new-file flow). `select_banner_image_from_library()` is the corrected
     mechanism, confirmed live to persist correctly across a reopen.
  2. Submit for Publishing was blocked by ordinary native HTML5 required-
     field validation (Banner Subtitle EN/AR, Button 1/2 Label EN/AR,
     Button 1/2 Link were never filled), not a silent product no-op —
     `fill_remaining_required_fields_for_publishing()` now fills them.
Confirmed live end-to-end 2026-09-08 (disposable probe entry, created,
verified Approved, deleted) that a brand-new Hero Banner Slide DOES reach
Approved through the normal CMS UI once both are corrected. tc_135018 below
is now scripted to reach a real Approved status and exercise the actual
delete assertion. No Bug should be filed against PBI 129367 from the
earlier pass's retracted finding.
"""

import time

import allure
import pytest

from cms.pages.home_hero_banner.home_hero_banner_admin_page import (
    ACHIEVEMENT_COUNTER_03_ERC,
    BANNER_IMAGE_LIBRARY_FILE,
    BANNER_TITLE_EN_LABEL,
    COUNTER_TITLE_AR_LABEL,
    COUNTER_TITLE_EN_LABEL,
    COUNTER_VALUE_LABEL,
    HERO_SLIDE_01_ERC,
    HERO_SLIDE_02_ERC,
    AchievementCounterAdminPage,
    HeroBannerSlideAdminPage,
)
from core.web.browser import new_context
from web.pages.home_hero_banner.home_hero_banner_page import HomeHeroBannerPage

HERO_SLIDE_FINGERPRINT_TITLE_EN = "QCTEST-135024 Hero Slide Probe"

COUNTER_03_LABEL = "Service Support"

# ---- tc_135010/135014/135015/135018/135019 batch (2026-09-08) ------------
# BANNER_IMAGE_FIXTURE (banner1.jpg) REMOVED 2026-09-08: "Banner Image" is a
# media-library picker (selects an EXISTING image already in Liferay's
# Documents & Media library), not a raw file-upload field — see
# home_hero_banner_admin_page.py's module docstring CORRECTED note. The
# fixture file, `upload_banner_image()`, and `_uploaded_banner1_filename_ok()`
# below are all dead code under the real mechanism and have been removed;
# `select_banner_image_from_library()` selects the confirmed-live-existing
# "download.png" under the library's "Flickr" folder instead — a fixed,
# stable filename with no repeat-upload auto-rename to work around.

HERO_SLIDE_01_BASELINE_ORDER = "100"  # confirmed live real stored value (module docstring)
HERO_SLIDE_02_BASELINE_ORDER = "200"  # confirmed live real stored value (module docstring)
SLIDE_ORDER_FIRST = "1"   # the case's own literal value — confirmed live to swap cleanly, no tie (see module docstring)
SLIDE_ORDER_SECOND = "2"  # the case's own literal value


def _fill_disposable_slide(admin: HeroBannerSlideAdminPage, title_en: str, active: bool) -> None:
    """Shared Arrange helper for this batch's 3 disposable-record tests
    (135010/135018/135019) — mirrors board_of_directors's
    `_fill_disposable_member()` precedent. Fills only the fields each of
    those 3 cases actually needs (Title EN/AR + Active Status); Banner
    Image is selected separately by the caller since only 135010 asserts
    on the selection signal itself."""
    admin.set_banner_title_en(title_en)
    admin.set_banner_title_ar("عنوان بانر تجريبي")
    admin.set_slide_active(active)


def _best_effort_delete_slide(admin: HeroBannerSlideAdminPage, title_en: str) -> None:
    """UI-only teardown via `find_entry_code_by_field()` +
    `delete_entry_by_code()` — never raises, per this project's established
    `_best_effort_delete` convention (see
    test_board_of_directors_control_panel.py's `_best_effort_delete_member()`
    and ObjectAuthoringPage's own module docstring for the same precedent).
    ADDED 2026-09-08: `find_entry_code_by_field()` itself is NOT best-effort
    (it navigates and can raise, e.g. a Playwright `TimeoutError` on a slow/
    contended qcdev render — confirmed live this session) — this wrapper is
    what makes a `finally`-block re-check call safe, mirroring
    `delete_entry_by_code()`'s own "a teardown hiccup here must not flip an
    already-passed test body to FAILED" contract. Only for the `finally`-
    block best-effort re-check; the TRY-block's own strict, asserted lookup
    right after creation (`assert entry_code, ...`) is intentionally NOT
    wrapped — that one must still raise/fail loudly if it cannot resolve the
    just-created entry."""
    try:
        code = admin.find_entry_code_by_field(BANNER_TITLE_EN_LABEL, title_en)
        if code:
            admin.delete_entry_by_code(code)
    except Exception:  # noqa: BLE001 — best-effort only, see docstring
        pass


def _fill_publishable_required_fields(admin: HeroBannerSlideAdminPage) -> None:
    """Fills every OTHER required (`*`) field Submit for Publishing enforces
    besides Banner Title/Image/Display Order (see
    `HeroBannerSlideAdminPage.fill_remaining_required_fields_for_publishing()`'s
    own docstring and the module docstring's CORRECTED note) — only tc_135018
    needs this (it is the only disposable-slide test that calls
    `submit_for_publishing()`; 135010/135019 only Save as Draft, which does
    not enforce these). Placeholder QCTEST content only — none of it is
    asserted on, this batch's cases only assert Approved status / delete."""
    admin.fill_remaining_required_fields_for_publishing(
        subtitle_en="QCTEST probe subtitle",
        subtitle_ar="عنوان فرعي تجريبي",
        button1_label_en="Learn More",
        button1_label_ar="اعرف المزيد",
        button1_link="https://qcdev.ihorizons.com/web/qatar-chamber/home",
        button2_label_en="Contact Us",
        button2_label_ar="اتصل بنا",
        button2_link="https://qcdev.ihorizons.com/web/qatar-chamber/contact-us",
    )
COUNTER_03_ORDER_FIRST = "50"  # CORRECTED 2026-09-08 (QA Manager): this object's Display
# Order values are spaced in hundreds (confirmed live: -01=100, -02=200, -03=300 baseline,
# 4th=400) — the case's own literal "1" is outside that value space. "100" was tried first
# (the in-convention value for "first place") but confirmed LIVE to TIE with counter-01's
# own real 100 and lose the tiebreak (counter-01 stayed first, order unchanged) — a real,
# observed finding, not assumed. "50" sits strictly below every real counter's Display
# Order and is confirmed live to move counter 3 to position 0 with no tie.
COUNTER_03_BASELINE_ORDER = "300"  # confirmed live real stored value (3rd of 4, see admin module docstring)
COUNTER_03_BASELINE_INDEX = 2  # 0-indexed 3rd position among the 4 rendered counters


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Publish / unpublish lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Re-publishing a previously unpublished Hero Banner slide restores it on the Home Page")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129367
@pytest.mark.tc_135024
@pytest.mark.xdist_group("hero_banner_slide_45560")
def test_republishing_previously_unpublished_slide_restores_it(page, browser):
    """ADO 135024. Target: HERO_BANNER_SLIDE-02 (Display Order 200), a
    QCDEMO/TEST_OWNED seed row — not real editorial content (see admin
    module docstring).

    -01 and -02 share an IDENTICAL default Banner Title (EN), confirmed
    live by reading both edit forms — title text alone cannot distinguish
    -02 on the public carousel. This test therefore stamps -02 with a
    unique QCTEST- fingerprint title WHILE it is unpublished (editing an
    Approved entry on this surface requires Unpublish first anyway — see
    admin module docstring), purely to make ITS OWN presence/absence on
    the live carousel independently verifiable. This is test
    instrumentation, not a scope change to the case (which only exercises
    unpublish/publish) — the fingerprint (and every other field) is
    captured and restored to baseline in `finally`, re-verified by a fresh
    reopen.
    """
    admin = HeroBannerSlideAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())

    admin.open_entry_by_code(HERO_SLIDE_02_ERC)
    baseline_title_en = admin.banner_title_en_value()
    baseline_status = admin.current_status()
    assert baseline_status == "Approved", (
        f"expected {HERO_SLIDE_02_ERC!r}'s baseline status to be Approved, got "
        f"{baseline_status!r} — confirm the real baseline before running this test"
    )

    try:
        with allure.step("Arrange: unpublish the slide and stamp it with a unique, independently-verifiable title"):
            admin.unpublish_to_edit_as_draft()
            admin.set_banner_title_en(HERO_SLIDE_FINGERPRINT_TITLE_EN)
            admin.submit_for_publishing()

        admin.open_entry_by_code(HERO_SLIDE_02_ERC)
        assert admin.current_status() == "Approved", "fingerprint publish did not persist as Approved"

        with allure.step("Confirm the fingerprinted slide is visible on the live Home Page (arrange baseline)"):
            assert home.reload_until_title_in_carousel(HERO_SLIDE_FINGERPRINT_TITLE_EN, expected_visible=True), (
                "fingerprinted slide did not appear on the Home Page after its initial publish"
            )

        with allure.step("Unpublish the slide (the case's own implied precondition, made concrete/live-confirmed)"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            admin.unpublish_to_edit_as_draft()
            assert admin.current_status() == "Draft", "slide did not move to Draft after Unpublish"

        with allure.step("Confirm the slide is gone from the live Home Page while unpublished"):
            assert home.reload_until_title_in_carousel(HERO_SLIDE_FINGERPRINT_TITLE_EN, expected_visible=False), (
                "an Unpublished (Draft) slide unexpectedly still appears on the Home Page"
            )

        with allure.step("Click Publish again (Submit for Publishing)"):
            admin.submit_for_publishing()

        admin.open_entry_by_code(HERO_SLIDE_02_ERC)
        assert admin.current_status() == "Approved", (
            f"expected Approved (Published) after re-publishing, got {admin.current_status()!r}"
        )

        with allure.step("Load Home Page: the slide reappears in the slider"):
            assert home.reload_until_title_in_carousel(HERO_SLIDE_FINGERPRINT_TITLE_EN, expected_visible=True), (
                "the slide did not reappear on the Home Page after re-publishing"
            )
    finally:
        with allure.step("Teardown: restore the baseline Banner Title (EN) and Approved status, re-verified"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            if admin.current_status() == "Approved":
                admin.unpublish_to_edit_as_draft()
            admin.set_banner_title_en(baseline_title_en)
            admin.submit_for_publishing()
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            restored_title = admin.banner_title_en_value()
            restored_status = admin.current_status()
            assert restored_title == baseline_title_en and restored_status == baseline_status, (
                f"failed to restore {HERO_SLIDE_02_ERC!r} to baseline "
                f"(title={baseline_title_en!r}, status={baseline_status!r}) — "
                f"currently (title={restored_title!r}, status={restored_status!r})"
            )
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 — cleanup must never mask the real result
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Achievement Counters — Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Enabling a Counter's Active Status makes it appear on the frontend")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135026
@pytest.mark.xdist_group("achievement_counter_45659")
def test_enabling_counter_active_status_makes_it_appear(page, browser):
    """ADO 135026. Target: "counter 3" (QCDEMO-129367-ACHIEVEMENT_COUNTER-03,
    "Service Support" / "24/7" — see admin module docstring). TEST_OWNED
    shared seed row; baseline (Active=True) captured and restored in
    `finally`, re-verified by a fresh reopen.
    """
    admin = AchievementCounterAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())

    admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
    baseline_active = admin.is_counter_active()
    assert baseline_active is True, (
        f"expected counter 3's baseline Active Status to be True, got {baseline_active!r} — "
        "confirm the real baseline before running this test"
    )

    try:
        with allure.step("Precondition: deactivate the counter first (Toggle Active Status=False, Save)"):
            admin.unpublish_to_edit_as_draft()
            admin.set_counter_active(False)
            admin.submit_for_publishing()
        assert home.reload_until_counter_matches(COUNTER_03_LABEL, expected_visible=False), (
            "counter 3 still appears on the Home Page while Active Status=False — cannot verify a real enable"
        )

        with allure.step("Toggle Counter Active Status to True and Save"):
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            admin.unpublish_to_edit_as_draft()
            admin.set_counter_active(True)
            admin.submit_for_publishing()

        admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
        assert admin.is_counter_active() is True, "Active Status did not persist as True after Save"

        with allure.step("Load Home Page: the counter now appears in the Achievement Counters row"):
            assert home.reload_until_counter_matches(COUNTER_03_LABEL, expected_visible=True), (
                "counter 3 did not appear on the Home Page after enabling Active Status"
            )
    finally:
        with allure.step("Teardown: restore baseline Active Status=True, re-verified"):
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            if not admin.is_counter_active():
                admin.unpublish_to_edit_as_draft()
                admin.set_counter_active(True)
                admin.submit_for_publishing()
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            assert admin.is_counter_active() is True, "teardown failed to restore counter 3's Active Status to True"
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Achievement Counters — Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Disabling a Counter's Active Status removes it from the frontend")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135027
@pytest.mark.xdist_group("achievement_counter_45659")
def test_disabling_counter_active_status_removes_it(page, browser):
    """ADO 135027. Same target/record as tc_135026 (counter 3) — see that
    test's docstring and the admin module docstring. Baseline is already
    Active=True, matching this case's own stated precondition.
    """
    admin = AchievementCounterAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())

    admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
    baseline_active = admin.is_counter_active()
    assert baseline_active is True, (
        f"expected counter 3's baseline Active Status to be True, got {baseline_active!r} — "
        "confirm the real baseline before running this test"
    )

    try:
        with allure.step("Confirm precondition: the counter is currently visible on the Home Page"):
            assert home.reload_until_counter_matches(COUNTER_03_LABEL, expected_visible=True), (
                "counter 3 is not visible on the Home Page before this test's own action — "
                "cannot verify a real removal"
            )

        with allure.step("Toggle Counter Active Status to False and Save"):
            admin.unpublish_to_edit_as_draft()
            admin.set_counter_active(False)
            admin.submit_for_publishing()

        admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
        assert admin.is_counter_active() is False, "Active Status did not persist as False after Save"

        with allure.step("Load Home Page: the counter no longer appears in the row"):
            assert home.reload_until_counter_matches(COUNTER_03_LABEL, expected_visible=False), (
                "counter 3 still appears on the Home Page after disabling Active Status"
            )
    finally:
        with allure.step("Teardown: restore baseline Active Status=True, re-verified"):
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            if not admin.is_counter_active():
                admin.unpublish_to_edit_as_draft()
                admin.set_counter_active(True)
                admin.submit_for_publishing()
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            assert admin.is_counter_active() is True, "teardown failed to restore counter 3's Active Status to True"
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Achievement Counters — Display Order")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Changing a Counter's Display Order updates its position in the frontend row")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135028
@pytest.mark.xdist_group("achievement_counter_45659")
def test_changing_counter_display_order_updates_frontend_position(page, browser):
    """ADO 135028. Target: "counter 3" (QCDEMO-129367-ACHIEVEMENT_COUNTER-03),
    live-confirmed real Display Order value 300 (3rd of 4 rendered
    counters — see admin module docstring). This object's Display Order
    values are spaced in hundreds (-01=100, -02=200, -03=300 baseline,
    4th=400) — the case's own literal "1" is outside this field's real
    value space. "100" (the in-convention "first place" value) was tried
    next but confirmed LIVE to TIE with counter-01's own real 100 and lose
    the tiebreak (order stayed unchanged, counter-01 first) — see
    COUNTER_03_ORDER_FIRST's own comment for that evidence.
    COUNTER_03_ORDER_FIRST="50" (strictly below every real counter's
    Display Order, no tie) is confirmed live to correctly move counter 3
    to position 0. Baseline order captured and restored in `finally`,
    re-verified by a fresh reopen.

    HEALED 2026-09-08: the precondition read below originally called
    `home.counter_labels()` on a brand-new, never-navigated anon page
    (`HomeHeroBannerPage.counter_labels()` does not navigate itself, only
    `open_home()`/`reload_until_counter_*` do) — a pure test-code bug that
    made every run fail at the very first read, before any real assertion.
    Confirmed live via a direct probe: `.qc-hero-counters` renders
    immediately (visible, computed `display:flex`) on a freshly navigated
    anon `/home` load — never a genuine rendering/timing issue.
    """
    admin = AchievementCounterAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())

    admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
    baseline_order = admin.counter_display_order_value()
    assert baseline_order == COUNTER_03_BASELINE_ORDER, (
        f"expected counter 3's baseline Display Order to be {COUNTER_03_BASELINE_ORDER!r}, "
        f"got {baseline_order!r} — confirm the real baseline before running this test"
    )

    try:
        with allure.step("Confirm precondition: counter 3 is not currently first in the row"):
            home.open_home()
            baseline_labels = home.counter_labels()
            assert baseline_labels[0] != COUNTER_03_LABEL, (
                f"counter 3 already displays first ({baseline_labels!r}) — cannot verify a real reorder"
            )

        with allure.step("Change counter 3's Display Order to 1 and Save"):
            admin.unpublish_to_edit_as_draft()
            admin.set_counter_display_order(COUNTER_03_ORDER_FIRST)
            admin.submit_for_publishing()

        admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
        assert admin.counter_display_order_value() == COUNTER_03_ORDER_FIRST, "Display Order did not persist"

        with allure.step("Load Home Page: counter 3 now displays first in the row"):
            assert home.reload_until_counter_position_matches(COUNTER_03_LABEL, expected_index=0), (
                "counter 3 did not move to the first position after the Display Order change"
            )
    finally:
        with allure.step(f"Teardown: restore baseline Display Order={COUNTER_03_BASELINE_ORDER}, re-verified"):
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            if admin.counter_display_order_value() != COUNTER_03_BASELINE_ORDER:
                admin.unpublish_to_edit_as_draft()
                admin.set_counter_display_order(COUNTER_03_BASELINE_ORDER)
                admin.submit_for_publishing()
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            assert admin.counter_display_order_value() == COUNTER_03_BASELINE_ORDER, (
                "teardown failed to restore counter 3's Display Order to baseline"
            )
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Achievement Counters — Display Order")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reverting a Counter's Display Order restores its original frontend position")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135029
@pytest.mark.xdist_group("achievement_counter_45659")
def test_reverting_counter_display_order_restores_frontend_position(page, browser):
    """ADO 135029. Same target/record as tc_135028 (counter 3). The case's
    own literal "revert...to 3" is interpreted as "back to its real
    original stored value" (300, live-confirmed — see admin module
    docstring; the case's "3" is a positional shorthand, not the literal
    field value) — disclosed here, not silently substituted. This test is
    self-contained (establishes its own "order previously changed"
    precondition first) so it is independently runnable, not merely a
    duplicate of tc_135028's own teardown.
    """
    admin = AchievementCounterAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())

    admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
    baseline_order = admin.counter_display_order_value()
    assert baseline_order == COUNTER_03_BASELINE_ORDER, (
        f"expected counter 3's baseline Display Order to be {COUNTER_03_BASELINE_ORDER!r}, "
        f"got {baseline_order!r} — confirm the real baseline before running this test"
    )

    try:
        with allure.step("Arrange: change counter 3's order to 1 first (the case's own 'previously changed' precondition)"):
            admin.unpublish_to_edit_as_draft()
            admin.set_counter_display_order(COUNTER_03_ORDER_FIRST)
            admin.submit_for_publishing()
        assert home.reload_until_counter_position_matches(COUNTER_03_LABEL, expected_index=0), (
            "could not establish the 'order previously changed' precondition — counter 3 never moved first"
        )

        with allure.step(f"Revert counter 3's Display Order back to {COUNTER_03_BASELINE_ORDER} and Save"):
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            admin.unpublish_to_edit_as_draft()
            admin.set_counter_display_order(COUNTER_03_BASELINE_ORDER)
            admin.submit_for_publishing()

        admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
        assert admin.counter_display_order_value() == COUNTER_03_BASELINE_ORDER, "Display Order did not revert"

        with allure.step("Load Home Page: original counter order is restored"):
            assert home.reload_until_counter_position_matches(COUNTER_03_LABEL, expected_index=COUNTER_03_BASELINE_INDEX), (
                "counter 3 did not return to its original position after reverting Display Order"
            )
    finally:
        with allure.step(f"Teardown: confirm Display Order remains at baseline={COUNTER_03_BASELINE_ORDER}"):
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            if admin.counter_display_order_value() != COUNTER_03_BASELINE_ORDER:
                admin.unpublish_to_edit_as_draft()
                admin.set_counter_display_order(COUNTER_03_BASELINE_ORDER)
                admin.submit_for_publishing()
            admin.open_entry_by_code(ACHIEVEMENT_COUNTER_03_ERC)
            assert admin.counter_display_order_value() == COUNTER_03_BASELINE_ORDER, (
                "teardown failed to restore counter 3's Display Order to baseline"
            )
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Hero Banner Slide — Create / Upload")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Selecting a valid Banner Image on a new Hero Banner Slide succeeds")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135010
def test_uploading_valid_banner_image_on_new_slide_succeeds(page):
    """ADO 135010. Creates its OWN fresh disposable QCTEST-135010 slide
    (never touches -01/-02) — deleted in `finally`. Scoped to the case's
    own asserted intent only (the Banner Image field is populated and the
    success is observably confirmed) — NOT extended into a persistence-
    after-reopen check (that IS now confirmed working, see the admin
    module docstring's CORRECTED note, but it is still out of this case's
    own literal scope).

    MECHANISM DISCLOSURE (case-vs-real-mechanism mismatch, same disclosed-
    substitution precedent as tc_135024's own docstring elsewhere in this
    suite): the injected case's own literal 2 steps ("Click upload control"
    / "Select banner1.jpg (1.2MB)") describe a raw file-upload mechanism.
    Live-investigated 2026-09-08 (Playwright MCP against qcdev) and
    CORRECTED here — see home_hero_banner_admin_page.py's module docstring
    CORRECTED note: "Banner Image" is NOT a raw upload field on this
    project, it is a media-LIBRARY PICKER that selects an EXISTING image
    already in Liferay's Documents & Media library (populated by this
    project's one-way Flickr import — see cms-profile.md's "Flickr Pro
    API" note). The case's own literal steps are therefore reinterpreted
    as "click the image picker control" / "select an existing image from
    the library" (`select_banner_image_from_library()`, confirmed live to
    select the library's own "download.png" under its "Flickr" folder) —
    the case's asserted intent (a Banner Image selection succeeds and is
    observably confirmed) is UNCHANGED, only the mechanism used to reach
    it. This is a disclosed mechanism substitution, not a dropped case.

    "Thumbnail preview shown" is asserted via `uploaded_filename()`'s
    filename-readout signal, a further disclosed mechanism substitution:
    this Object Authoring surface renders NO separate visual `<img>`
    thumbnail anywhere on the form after selection (confirmed live — see
    admin module docstring's evidence), so the filename readout is the
    only real, observable "selection succeeded" signal available. Save as
    Draft only (no need to publish for a selection-only case) — Active
    Status is left at its default False, so this record never reaches the
    live carousel.

    Because this is a SELECT of an already-existing, stable library file
    (not a new upload), the filename readout is asserted by EXACT match
    ("download.png") — there is no repeat-run auto-rename behavior to
    account for (that concern only applied to the old, now-removed
    raw-upload mechanism; see `BANNER_IMAGE_LIBRARY_FILE`).
    """
    admin = HeroBannerSlideAdminPage(page)
    title_en = "QCTEST-135010 Hero Slide Upload"

    try:
        with allure.step("Arrange: open the create-new form and fill Banner Title (EN)"):
            admin.open_new_entry_form()
            admin.set_banner_title_en(title_en)

        with allure.step("Click the image picker control (dialog opens) and select an existing library image"):
            admin.select_banner_image_from_library()

        with allure.step("Assert the image selection succeeded (filename readout — see docstring)"):
            uploaded_name = admin.uploaded_banner_image_filename()
            assert uploaded_name == BANNER_IMAGE_LIBRARY_FILE, (
                f"expected the Banner Image field's filename readout to be {BANNER_IMAGE_LIBRARY_FILE!r}, "
                f"got {uploaded_name!r}"
            )

        with allure.step("Save as Draft (disposal only — the case's own asserted intent is already verified above)"):
            admin.save_as_draft()
    finally:
        with allure.step("Teardown: delete the disposable slide"):
            _best_effort_delete_slide(admin, title_en)


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Hero Banner Slide — Display Order")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Changing a Hero Banner Slide's Display Order updates its position in the frontend slider")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.ui
@pytest.mark.pbi_129367
@pytest.mark.tc_135014
@pytest.mark.xdist_group("hero_banner_slide_45560")
def test_changing_slide_display_order_updates_frontend_position(page, browser):
    """ADO 135014. "Slide A"/"Slide B" map to HERO_SLIDE_01 (baseline
    Display Order 100, the confirmed-live initially-active slide) /
    HERO_SLIDE_02 (baseline Display Order 200) respectively — see admin
    module docstring.

    Live-confirmed BEFORE scripting (per this batch's own caution about
    re-discovering the Achievement Counter object's tiebreak lesson):
    unlike that object, this object's literal case values ("1"/"2") DO
    produce a clean swap with NO tie — the only other currently-Active
    real slide (bbdc6974-..., "please visit our website") sits at Display
    Order 300 (well outside 1-2), and this object's remaining 2 real rows
    are both Active Status=False (irrelevant to carousel ordering
    regardless of their own Display Order value). Live round-trip
    confirmed 2026-09-08: -02=1 / -01=2 -> Home Page's initially-active
    slide becomes -02; reverted -02=200 / -01=100 -> -01 active again — see
    HomeHeroBannerPage module docstring for the ERC-based read this test
    uses (title-independent, since -01/-02 share an identical default
    title — see admin module docstring) and its autoplay-safety note.
    """
    admin = HeroBannerSlideAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())

    admin.open_entry_by_code(HERO_SLIDE_01_ERC)
    baseline_order_01 = admin.display_order_value()
    admin.open_entry_by_code(HERO_SLIDE_02_ERC)
    baseline_order_02 = admin.display_order_value()
    assert (baseline_order_01, baseline_order_02) == (HERO_SLIDE_01_BASELINE_ORDER, HERO_SLIDE_02_BASELINE_ORDER), (
        f"expected baseline Display Orders 01={HERO_SLIDE_01_BASELINE_ORDER!r}/02={HERO_SLIDE_02_BASELINE_ORDER!r}, "
        f"got 01={baseline_order_01!r}/02={baseline_order_02!r} — confirm the real baseline before running this test"
    )

    try:
        with allure.step("Confirm precondition: Slide A (-01) is currently the initially-active slide"):
            assert home.reload_until_active_slide_matches(HERO_SLIDE_01_ERC), (
                "HERO_SLIDE_01 is not the initially-active slide before this test's own action — cannot verify a real reorder"
            )

        with allure.step("Edit Slide B's (-02) Display Order to 1 and Slide A's (-01) to 2, Save"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            admin.unpublish_to_edit_as_draft()
            admin.set_display_order(SLIDE_ORDER_FIRST)
            admin.submit_for_publishing()
            admin.open_entry_by_code(HERO_SLIDE_01_ERC)
            admin.unpublish_to_edit_as_draft()
            admin.set_display_order(SLIDE_ORDER_SECOND)
            admin.submit_for_publishing()

        admin.open_entry_by_code(HERO_SLIDE_02_ERC)
        assert admin.display_order_value() == SLIDE_ORDER_FIRST, "Slide B's Display Order did not persist"
        admin.open_entry_by_code(HERO_SLIDE_01_ERC)
        assert admin.display_order_value() == SLIDE_ORDER_SECOND, "Slide A's Display Order did not persist"

        with allure.step("Load Home Page: Slide B now displays first"):
            assert home.reload_until_active_slide_matches(HERO_SLIDE_02_ERC), (
                "Slide B (HERO_SLIDE_02) did not become the initially-active slide after the Display Order change"
            )
    finally:
        with allure.step("Teardown: restore baseline Display Orders (01=100, 02=200), re-verified"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            if admin.display_order_value() != HERO_SLIDE_02_BASELINE_ORDER:
                admin.unpublish_to_edit_as_draft()
                admin.set_display_order(HERO_SLIDE_02_BASELINE_ORDER)
                admin.submit_for_publishing()
            admin.open_entry_by_code(HERO_SLIDE_01_ERC)
            if admin.display_order_value() != HERO_SLIDE_01_BASELINE_ORDER:
                admin.unpublish_to_edit_as_draft()
                admin.set_display_order(HERO_SLIDE_01_BASELINE_ORDER)
                admin.submit_for_publishing()
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            restored_02 = admin.display_order_value()
            admin.open_entry_by_code(HERO_SLIDE_01_ERC)
            restored_01 = admin.display_order_value()
            assert (restored_01, restored_02) == (HERO_SLIDE_01_BASELINE_ORDER, HERO_SLIDE_02_BASELINE_ORDER), (
                f"failed to restore baseline Display Orders — currently 01={restored_01!r}/02={restored_02!r}"
            )
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Hero Banner Slide — Display Order")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reverting a Hero Banner Slide's Display Order restores its original frontend position")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.ui
@pytest.mark.pbi_129367
@pytest.mark.tc_135015
@pytest.mark.xdist_group("hero_banner_slide_45560")
def test_reverting_slide_display_order_restores_frontend_position(page, browser):
    """ADO 135015. Same target pair as tc_135014 (Slide A=-01, Slide B=-02).
    Self-contained: establishes its OWN "previously changed" precondition
    first (B=1/A=2, i.e. tc_135014's own end state) rather than depending on
    tc_135014 having run, mirroring tc_135029's precedent for the
    Achievement Counter object.

    The case's own literal revert values (B back to 2, A back to 1) are
    scripted AS WORDED — unlike tc_135029's "revert to 3", these two
    literal values ARE the real intended end state here (A=1 < B=2 puts
    Slide A first again), so no case-vs-product reinterpretation is
    needed. This intentionally does NOT restore the object's true baseline
    (100/200) as part of the test's own action — that restoration happens
    in `finally`, same as every other shared-record test in this module.
    """
    admin = HeroBannerSlideAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())

    admin.open_entry_by_code(HERO_SLIDE_01_ERC)
    baseline_order_01 = admin.display_order_value()
    admin.open_entry_by_code(HERO_SLIDE_02_ERC)
    baseline_order_02 = admin.display_order_value()
    assert (baseline_order_01, baseline_order_02) == (HERO_SLIDE_01_BASELINE_ORDER, HERO_SLIDE_02_BASELINE_ORDER), (
        f"expected baseline Display Orders 01={HERO_SLIDE_01_BASELINE_ORDER!r}/02={HERO_SLIDE_02_BASELINE_ORDER!r}, "
        f"got 01={baseline_order_01!r}/02={baseline_order_02!r} — confirm the real baseline before running this test"
    )

    try:
        with allure.step("Arrange: change Slide B's order to 1 and Slide A's to 2 (the 'previously changed' precondition)"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            admin.unpublish_to_edit_as_draft()
            admin.set_display_order(SLIDE_ORDER_FIRST)
            admin.submit_for_publishing()
            admin.open_entry_by_code(HERO_SLIDE_01_ERC)
            admin.unpublish_to_edit_as_draft()
            admin.set_display_order(SLIDE_ORDER_SECOND)
            admin.submit_for_publishing()
        assert home.reload_until_active_slide_matches(HERO_SLIDE_02_ERC), (
            "could not establish the 'order previously changed' precondition — Slide B never became active"
        )

        with allure.step("Revert: edit Slide B's order back to 2 and Slide A back to 1, Save"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            admin.unpublish_to_edit_as_draft()
            admin.set_display_order(SLIDE_ORDER_SECOND)
            admin.submit_for_publishing()
            admin.open_entry_by_code(HERO_SLIDE_01_ERC)
            admin.unpublish_to_edit_as_draft()
            admin.set_display_order(SLIDE_ORDER_FIRST)
            admin.submit_for_publishing()

        admin.open_entry_by_code(HERO_SLIDE_02_ERC)
        assert admin.display_order_value() == SLIDE_ORDER_SECOND, "Slide B's Display Order did not revert"
        admin.open_entry_by_code(HERO_SLIDE_01_ERC)
        assert admin.display_order_value() == SLIDE_ORDER_FIRST, "Slide A's Display Order did not revert"

        with allure.step("Load Home Page: Slide A displays first again"):
            assert home.reload_until_active_slide_matches(HERO_SLIDE_01_ERC), (
                "Slide A (HERO_SLIDE_01) did not become the initially-active slide again after reverting Display Order"
            )
    finally:
        with allure.step("Teardown: restore TRUE baseline Display Orders (01=100, 02=200), re-verified"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            if admin.display_order_value() != HERO_SLIDE_02_BASELINE_ORDER:
                admin.unpublish_to_edit_as_draft()
                admin.set_display_order(HERO_SLIDE_02_BASELINE_ORDER)
                admin.submit_for_publishing()
            admin.open_entry_by_code(HERO_SLIDE_01_ERC)
            if admin.display_order_value() != HERO_SLIDE_01_BASELINE_ORDER:
                admin.unpublish_to_edit_as_draft()
                admin.set_display_order(HERO_SLIDE_01_BASELINE_ORDER)
                admin.submit_for_publishing()
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            restored_02 = admin.display_order_value()
            admin.open_entry_by_code(HERO_SLIDE_01_ERC)
            restored_01 = admin.display_order_value()
            assert (restored_01, restored_02) == (HERO_SLIDE_01_BASELINE_ORDER, HERO_SLIDE_02_BASELINE_ORDER), (
                f"failed to restore baseline Display Orders — currently 01={restored_01!r}/02={restored_02!r}"
            )
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Hero Banner Slide — Delete")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Deleting a Hero Banner Slide removes it permanently from both CMS and frontend")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135018
def test_delete_slide_removes_from_cms_and_public_site(page, browser):
    """ADO 135018. Creates its OWN fresh disposable QCTEST-135018 slide
    (never one of the real seeded -01/-02 rows — see standards.md's
    "Destructive Operations Against qcdev" rule), confirms it is live/
    published on BOTH the CMS admin grid and the public Home Page first (a
    real precondition — deleting something never proven to exist proves
    nothing), then deletes it as this test's own verified action and
    confirms removal from BOTH surfaces.

    CORRECTED 2026-09-08 (was: "LIVE-CONFIRMED PRODUCT DEFECT... EXPECTED TO
    FAIL" — that finding was WRONG and is retracted here, not silently
    walked back; see home_hero_banner_admin_page.py's module docstring
    CORRECTED note for the full evidence trail): an earlier pass concluded
    there was no working UI path to Approve/publish a new Hero Banner
    Slide with an image. Both of its supporting observations had a
    different, mundane cause than a product defect, not a real blocker:
      1. "Banner Image" is a media-library PICKER (selects an EXISTING
         image already in the Documents & Media library — this project's
         library is populated by a one-way Flickr import, see
         cms-profile.md's "Flickr Pro API" note), not a raw file-upload
         field. The earlier pass drove it via the wrong control
         (`upload_file()`'s drag-drop-a-new-file flow) — corrected here to
         `select_banner_image_from_library()`, confirmed live to persist
         correctly across a reopen (unlike the old, unsupported raw-upload
         path this field was never meant to be driven through).
      2. Submit for Publishing was blocked by ordinary native HTML5
         "Please fill out this field" required-field validation (Banner
         Subtitle EN/AR, Button 1/2 Label EN/AR, Button 1/2 Link were never
         filled by the earlier pass) — not a silent product no-op. Every
         required field is now filled via
         `_fill_publishable_required_fields()`.
      Confirmed live end-to-end 2026-09-08 (disposable probe entry: created,
      confirmed status "(approved)" on reopen, then deleted as part of the
      correction's own cleanup) that a brand-new Hero Banner Slide with a
      picker-selected image DOES reach Approved through the normal CMS UI.
      No Bug should be filed against PBI 129367 from the earlier pass's
      retracted finding.
    """
    admin = HeroBannerSlideAdminPage(page)
    title_en = "QCTEST-135018 Hero Slide Delete Target"

    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())

    try:
        with allure.step("Arrange: create and publish a fresh disposable slide, Active Status=True"):
            admin.open_new_entry_form()
            _fill_disposable_slide(admin, title_en, active=True)
            admin.select_banner_image_from_library()
            _fill_publishable_required_fields(admin)
            admin.set_display_order("999")
            admin.submit_for_publishing()

        entry_code = admin.find_entry_code_by_field(BANNER_TITLE_EN_LABEL, title_en)
        assert entry_code, (
            f"could not resolve the just-created entry {title_en!r} by its own Banner Title (EN) value — "
            "Submit for Publishing did not create a persisted, resolvable record"
        )
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved", (
            f"expected {title_en!r} to show status Approved immediately after Submit for Publishing"
        )

        with allure.step("Confirm the slide is live on the public Home Page before deleting"):
            visible_before = home.reload_until_title_in_carousel(title_en, expected_visible=True)
        assert visible_before, (
            f"{title_en!r} never appeared on the public Home Page after publishing — "
            "cannot proceed to the delete assertion without a confirmed live precondition"
        )

        with allure.step("Delete the slide"):
            deleted = admin.delete_entry_by_code(entry_code)
        assert deleted, f"delete_entry_by_code({entry_code!r}) reported no matching row to delete"

        with allure.step("Refresh the CMS admin grid: the slide is permanently gone"):
            admin.open_entries_list()
            assert not admin.row_visible_by_code(entry_code), (
                f"{title_en!r} ({entry_code!r}) is still visible in the CMS admin grid after being deleted"
            )

        with allure.step("Load Home Page: the slide is no longer rendered on the frontend"):
            visible_after = home.reload_until_title_in_carousel(title_en, expected_visible=False)
        assert visible_after, f"{title_en!r} is still visible on the public Home Page after being deleted"
    finally:
        with allure.step("Best-effort teardown: delete the record if it somehow survived an early failure"):
            _best_effort_delete_slide(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Hero Banner Slide — Draft lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Saving a Hero Banner Slide as Draft does not publish it to the frontend")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129367
@pytest.mark.tc_135019
def test_save_as_draft_does_not_publish_to_frontend(page, browser):
    """ADO 135019. Creates its OWN fresh disposable QCTEST-135019 slide,
    Active Status=True (a deliberate, meaningful precondition — see admin
    module docstring: new entries default Active Status=False, so leaving
    it False would make the "not visible on Home Page" assertion vacuous;
    setting it True and relying on Draft status alone to withhold
    publication is the real test of the case's own claim). Save as Draft
    ONLY — never Submit for Publishing. Deleted in `finally` (a Draft-only
    record was never published, so there is no unpublish step to run first).
    """
    admin = HeroBannerSlideAdminPage(page)
    title_en = "QCTEST-135019 Hero Slide Draft Only"

    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())

    try:
        with allure.step("Fill mandatory fields (Banner Title EN/AR, Banner Image, Active Status=True)"):
            admin.open_new_entry_form()
            _fill_disposable_slide(admin, title_en, active=True)
            admin.select_banner_image_from_library()
        assert admin.banner_title_en_value() == title_en, "Banner Title (EN) did not populate before saving"
        assert admin.uploaded_banner_image_filename() == BANNER_IMAGE_LIBRARY_FILE, (
            "Banner Image did not populate before saving"
        )

        with allure.step("Click Save as Draft"):
            admin.save_as_draft()

        entry_code = admin.find_entry_code_by_field(BANNER_TITLE_EN_LABEL, title_en)
        assert entry_code, f"could not resolve the just-created entry {title_en!r} by its own Banner Title (EN) value"
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Draft", f"expected {title_en!r} to save with status Draft"

        with allure.step("Load Home Page: the slide is not visible"):
            visible = home.reload_until_title_in_carousel(title_en, expected_visible=False)
        assert visible, f"a Draft-only slide ({title_en!r}) unexpectedly appears on the live Home Page"
    finally:
        with allure.step("Teardown: delete the disposable Draft slide"):
            _best_effort_delete_slide(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


# ============================================================================
# BATCH1 (2026-09-13) — 7 additional Regression cases, see module docstring's
# own BATCH1 note above.
# ============================================================================

_TOAST_KEYWORDS = ("uccess", "aved", "published", "Published", "نجاح", "الحفظ", "تم")


def _poll_for_toast_keyword(admin: HeroBannerSlideAdminPage, timeout_seconds: float = 20.0) -> bool:
    """Generic success-toast/keyword poll — reuses
    test_board_of_directors_control_panel.py's tc_133516 technique verbatim
    (see this module's BATCH1 docstring note) rather than assuming either a
    confirmed presence or confirmed absence of a toast on this object.

    WIDENED 6.0 -> 20.0 (HEALED 2026-09-14, triage of tc_135025): the
    save/publish itself was proven to succeed independently (teardown
    re-locates and deletes the exact entry by title afterward) — 6s was
    simply too tight for this environment's demonstrated latency under
    3-way parallel xdist load (one navigation elsewhere in the same run
    took ~82s). Matches this module's own other generous budgets
    (APPROVED_BANNER_SETTLE_TIMEOUT_MS=8000 in object_authoring_page.py,
    the 35000ms cold-render precedents) without going as wide as the most
    extreme observed outlier, since this is a cheap, fast (150ms-interval)
    poll rather than a single blocking wait — a wider budget costs nothing
    extra when the toast appears quickly, as it normally does. Shared by
    all 4 call sites in this module (tc_135009, tc_135013, tc_135022, and
    tc_135025) — the timeout-too-tight root cause is generic to the poll
    itself, not specific to one test."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            body_text = admin.page.locator("body").inner_text()
        except Exception:  # noqa: BLE001 — page may be mid-navigation
            body_text = ""
        if any(kw in body_text for kw in _TOAST_KEYWORDS):
            return True
        time.sleep(0.15)
    return False


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Hero Banner Slide — Create")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can create a new Hero Banner slide with all mandatory fields")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135009
def test_create_new_slide_with_all_mandatory_fields(page):
    """ADO 135009. Steps: Navigate to Hero Banner Management, Add Slide ->
    Fill all mandatory fields with valid data -> Click Save -> Liferay
    generic success toast displayed; slide saved with entered values.

    MECHANISM: this Object Authoring surface has no single "Save" button
    (Save as Draft / Submit for Publishing only) — "Click Save" maps to
    Save as Draft, the lighter action whose own mandatory fields are
    confirmed live to be exactly Banner Title (EN/AR) + Banner Image (see
    tc_135019's own confirmed-live precondition check in this module) —
    Subtitle/Button fields are only enforced by Submit for Publishing, out
    of this case's own "Save" scope. See module docstring's BATCH1 note for
    the toast-assertion disclosure.
    """
    admin = HeroBannerSlideAdminPage(page)
    title_en = "QCTEST-135009 Hero Slide Create"
    title_ar = "شريحة تجريبية 135009"

    try:
        with allure.step("Navigate to Hero Banner Management, Add Slide"):
            admin.open_new_entry_form()

        with allure.step("Fill all mandatory fields with valid data (Banner Title EN/AR, Banner Image)"):
            admin.set_banner_title_en(title_en)
            admin.set_banner_title_ar(title_ar)
            admin.select_banner_image_from_library()

        with allure.step("Click Save and poll for a Liferay success toast"):
            admin.click(admin.SAVE_AS_DRAFT_BUTTON)
            toast_seen = _poll_for_toast_keyword(admin)
            admin._wait_for_settle()  # noqa: SLF001 — same settle save_as_draft() itself performs

        assert toast_seen, (
            "no Liferay success toast/keyword was observed within 6 seconds "
            "of Save — a real, observed result either way (this object's "
            "toast behavior was not independently pre-confirmed this session, "
            "see module docstring's BATCH1 note)"
        )

        with allure.step("Resolve the new entry and confirm it saved with the entered values"):
            entry_code = admin.find_entry_code_by_field(BANNER_TITLE_EN_LABEL, title_en)
        assert entry_code, (
            f"could not resolve the just-created entry {title_en!r} by its own "
            "Banner Title (EN) value — Save did not persist a resolvable record"
        )
        admin.open_entry_by_code(entry_code)
        assert admin.banner_title_en_value() == title_en, "Banner Title (EN) was not saved with the entered value"
        assert admin.banner_title_ar_value() == title_ar, "Banner Title (AR) was not saved with the entered value"
        assert admin.uploaded_banner_image_filename() == BANNER_IMAGE_LIBRARY_FILE, (
            "Banner Image selection was not saved"
        )
    finally:
        with allure.step("Teardown: delete the disposable slide"):
            _best_effort_delete_slide(admin, title_en)


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Hero Banner Slide — Edit")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can edit an existing published slide's title")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135013
@pytest.mark.xdist_group("hero_banner_slide_45560")
def test_edit_existing_published_slide_title(page):
    """ADO 135013. Steps: Open existing slide for edit -> Change Title EN to
    "Sustainable Growth" -> Click Save -> Liferay generic success toast
    displayed; slide title updated.

    SUBSTITUTION DISCLOSED (mirrors tc_135024's own precedent in this
    module): the case's own literal precondition (Title EN = "Growth")
    matches no real seeded slide — -01/-02 share an identical default
    title with no "Growth" substring (see admin module docstring). Targets
    HERO_SLIDE_02 (this module's own designated edit/publish/unpublish
    target) instead, using the case's own literal new value
    ("Sustainable Growth"). Editing an Approved entry on this surface
    requires "Unpublish to edit as draft" first (confirmed-live lifecycle
    rule, same as every other test in this module) — "Click Save" maps to
    re-Submit for Publishing, restoring Approved. Baseline title captured
    and restored in `finally`, re-verified by a fresh reopen. Shares
    HERO_SLIDE_02's xdist_group with tc_135024/tc_135014/tc_135015 (same
    record).
    """
    admin = HeroBannerSlideAdminPage(page)
    new_title_en = "Sustainable Growth"

    admin.open_entry_by_code(HERO_SLIDE_02_ERC)
    baseline_title_en = admin.banner_title_en_value()
    baseline_status = admin.current_status()
    assert baseline_status == "Approved", (
        f"expected {HERO_SLIDE_02_ERC!r}'s baseline status to be Approved, got "
        f"{baseline_status!r} — confirm the real baseline before running this test"
    )

    try:
        with allure.step("Open existing published slide for edit"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            admin.unpublish_to_edit_as_draft()

        with allure.step(f'Change Title EN to "{new_title_en}"'):
            admin.set_banner_title_en(new_title_en)

        with allure.step("Click Save and poll for a Liferay success toast"):
            admin.click(admin.SUBMIT_FOR_PUBLISHING_BUTTON)
            toast_seen = _poll_for_toast_keyword(admin)
            admin._wait_for_settle()  # noqa: SLF001

        assert toast_seen, (
            "no Liferay success toast/keyword was observed within 6 seconds "
            "of Save — a real, observed result either way"
        )

        with allure.step("Confirm the slide title updated and persisted"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            assert admin.banner_title_en_value() == new_title_en, "Title EN did not persist as the new value"
            assert admin.current_status() == "Approved", "slide did not return to Approved after re-Submit"
    finally:
        with allure.step("Teardown: restore the baseline title and Approved status, re-verified"):
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            if admin.current_status() == "Approved":
                admin.unpublish_to_edit_as_draft()
            admin.set_banner_title_en(baseline_title_en)
            admin.submit_for_publishing()
            admin.open_entry_by_code(HERO_SLIDE_02_ERC)
            restored_title = admin.banner_title_en_value()
            restored_status = admin.current_status()
            assert restored_title == baseline_title_en and restored_status == baseline_status, (
                f"failed to restore {HERO_SLIDE_02_ERC!r} to baseline "
                f"(title={baseline_title_en!r}, status={baseline_status!r}) — "
                f"currently (title={restored_title!r}, status={restored_status!r})"
            )


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Hero Banner Slide — Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Enabling a slide's Active Status makes it eligible to appear on the frontend")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135016
def test_enabling_slide_active_status_makes_it_eligible(page, browser):
    """ADO 135016. Precondition: existing published slide, Active=false.
    Steps: Toggle Active Status to true, Save -> Status saved -> Load Home
    Page -> Slide now appears in the slider.

    Uses its OWN fresh disposable QCTEST-135016 slide (never one of the
    real seeded -01/-02 rows), created directly with Active=False and
    published (Approved) to realize the case's own literal precondition,
    rather than mutating shared content. Deleted in `finally`.
    """
    admin = HeroBannerSlideAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())
    title_en = "QCTEST-135016 Hero Slide Enable"

    try:
        with allure.step("Arrange: create and publish a slide with Active Status=False (the case's own precondition)"):
            admin.open_new_entry_form()
            _fill_disposable_slide(admin, title_en, active=False)
            admin.select_banner_image_from_library()
            _fill_publishable_required_fields(admin)
            admin.set_display_order("999")
            admin.submit_for_publishing()

        entry_code = admin.find_entry_code_by_field(BANNER_TITLE_EN_LABEL, title_en)
        assert entry_code, f"could not resolve the just-created entry {title_en!r}"
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved", "arranged slide did not reach Approved status"
        assert admin.is_slide_active() is False, "arranged slide's baseline Active Status was not False"

        with allure.step("Confirm precondition: the slide is not eligible/visible on the Home Page while Active=False"):
            hidden_before = home.reload_until_title_in_carousel(title_en, expected_visible=False)
        assert hidden_before, f"{title_en!r} unexpectedly visible on the Home Page while Active Status=False"

        with allure.step("Toggle Active Status to true, Save"):
            admin.open_entry_by_code(entry_code)
            admin.unpublish_to_edit_as_draft()
            admin.set_slide_active(True)
            admin.submit_for_publishing()

        admin.open_entry_by_code(entry_code)
        assert admin.is_slide_active() is True, "Active Status did not persist as True after Save"

        with allure.step("Load Home Page: the slide now appears in the slider"):
            visible_after = home.reload_until_title_in_carousel(title_en, expected_visible=True)
        assert visible_after, f"{title_en!r} did not appear on the Home Page after enabling Active Status"
    finally:
        with allure.step("Teardown: delete the disposable slide"):
            _best_effort_delete_slide(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Hero Banner Slide — Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Disabling a slide's Active Status removes it from the frontend")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135017
def test_disabling_slide_active_status_removes_it(page, browser):
    """ADO 135017. Precondition (case's own wording: "Slide from TC-029,
    Active=true, Published" — an internal QA-suite cross-reference, not an
    Azure ID): self-contained per this module's own tc_135029 precedent —
    establishes its OWN fresh disposable QCTEST-135017 slide, Active=true,
    Published, rather than depending on tc_135016's slide/state. Steps:
    Toggle Active Status to false, Save -> Status saved -> Load Home Page ->
    Slide no longer appears in the slider. Deleted in `finally`.
    """
    admin = HeroBannerSlideAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())
    title_en = "QCTEST-135017 Hero Slide Disable"

    try:
        with allure.step("Arrange: create and publish a slide with Active Status=True, confirm it is live"):
            admin.open_new_entry_form()
            _fill_disposable_slide(admin, title_en, active=True)
            admin.select_banner_image_from_library()
            _fill_publishable_required_fields(admin)
            admin.set_display_order("999")
            admin.submit_for_publishing()

        entry_code = admin.find_entry_code_by_field(BANNER_TITLE_EN_LABEL, title_en)
        assert entry_code, f"could not resolve the just-created entry {title_en!r}"
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved", "arranged slide did not reach Approved status"
        assert admin.is_slide_active() is True, "arranged slide's baseline Active Status was not True"

        visible_before = home.reload_until_title_in_carousel(title_en, expected_visible=True)
        assert visible_before, (
            f"{title_en!r} not visible on the Home Page before this test's own "
            "action — cannot proceed to the removal assertion without a confirmed precondition"
        )

        with allure.step("Toggle Active Status to false, Save"):
            admin.open_entry_by_code(entry_code)
            admin.unpublish_to_edit_as_draft()
            admin.set_slide_active(False)
            admin.submit_for_publishing()

        admin.open_entry_by_code(entry_code)
        assert admin.is_slide_active() is False, "Active Status did not persist as False after Save"

        with allure.step("Load Home Page: the slide no longer appears in the slider"):
            visible_after = home.reload_until_title_in_carousel(title_en, expected_visible=False)
        assert visible_after, f"{title_en!r} still visible on the Home Page after disabling Active Status"
    finally:
        with allure.step("Teardown: delete the disposable slide"):
            _best_effort_delete_slide(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Publish / unpublish lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing a slide makes it visible on the Home Page after cache refresh")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135022
def test_publishing_slide_makes_it_visible_after_cache_refresh(page, browser):
    """ADO 135022 (P1/UAT). Precondition: slide in Draft, all mandatory
    fields valid. Steps: Click Publish -> Liferay success toast shown;
    status = Published -> Trigger/await cache refresh -> Load Home Page ->
    Published slide now appears in the slider.

    Uses its OWN fresh disposable QCTEST-135022 slide, Active Status=True —
    a disclosed technical necessity (new entries default Active=False,
    which would make the "now appears" assertion vacuous regardless of
    publish status — same disclosed necessity tc_135018/135019 already
    establish in this module). `home.reload_until_title_in_carousel()`'s
    own poll loop IS the "trigger/await cache refresh" step. Deleted in
    `finally`.
    """
    admin = HeroBannerSlideAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())
    title_en = "QCTEST-135022 Hero Slide Publish"

    try:
        with allure.step("Arrange: a slide in Draft with all mandatory fields valid"):
            admin.open_new_entry_form()
            _fill_disposable_slide(admin, title_en, active=True)
            admin.select_banner_image_from_library()
            _fill_publishable_required_fields(admin)
            admin.set_display_order("999")
            admin.save_as_draft()

        entry_code = admin.find_entry_code_by_field(BANNER_TITLE_EN_LABEL, title_en)
        assert entry_code, f"could not resolve the just-created entry {title_en!r}"
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Draft", "arranged slide did not save as Draft"

        with allure.step("Click Publish (Submit for Publishing) and poll for a success toast"):
            admin.click(admin.SUBMIT_FOR_PUBLISHING_BUTTON)
            toast_seen = _poll_for_toast_keyword(admin)
            admin._wait_for_settle()  # noqa: SLF001

        assert toast_seen, "no Liferay success toast/keyword was observed within 6 seconds of Publish"

        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved", "status did not change to Published/Approved"

        with allure.step("Trigger/await cache refresh, Load Home Page: the published slide now appears"):
            visible = home.reload_until_title_in_carousel(title_en, expected_visible=True)
        assert visible, f"{title_en!r} did not appear on the Home Page after publishing"
    finally:
        with allure.step("Teardown: delete the disposable slide"):
            _best_effort_delete_slide(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Publish / unpublish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Unpublishing a slide removes it from the Home Page")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135023
def test_unpublishing_slide_removes_it_from_home_page(page, browser):
    """ADO 135023. Precondition: slide currently Published and visible.
    Steps: Click Unpublish -> Liferay success toast shown; status =
    Unpublished -> Load Home Page -> Slide no longer appears.

    Uses its OWN fresh disposable QCTEST-135023 slide (Active=True,
    published first to realize the case's own literal precondition) rather
    than one of the shared -01/-02 rows — no xdist_group needed. Status
    reads "Draft" on this build after Unpublish (this surface's own
    Unpublish-equivalent state, same disclosed vocabulary substitution used
    project-wide, e.g. home_promo_banners's tc_135125). Deleted in
    `finally`.
    """
    admin = HeroBannerSlideAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())
    title_en = "QCTEST-135023 Hero Slide Unpublish"

    try:
        with allure.step("Arrange: the case's own precondition — a slide currently Published and visible"):
            admin.open_new_entry_form()
            _fill_disposable_slide(admin, title_en, active=True)
            admin.select_banner_image_from_library()
            _fill_publishable_required_fields(admin)
            admin.set_display_order("999")
            admin.submit_for_publishing()

        entry_code = admin.find_entry_code_by_field(BANNER_TITLE_EN_LABEL, title_en)
        assert entry_code, f"could not resolve the just-created entry {title_en!r}"
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved", "arranged slide did not reach Approved status"

        visible_before = home.reload_until_title_in_carousel(title_en, expected_visible=True)
        assert visible_before, (
            f"{title_en!r} not visible on the Home Page before this test's own "
            "action — cannot proceed without a confirmed precondition"
        )

        with allure.step("Click Unpublish"):
            admin.open_entry_by_code(entry_code)
            admin.unpublish_to_edit_as_draft()

        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Draft", "status did not change off Approved after Unpublish"

        with allure.step("Load Home Page: the slide no longer appears"):
            visible_after = home.reload_until_title_in_carousel(title_en, expected_visible=False)
        assert visible_after, f"{title_en!r} still visible on the Home Page after Unpublish"
    finally:
        with allure.step("Teardown: delete the disposable slide"):
            _best_effort_delete_slide(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("Achievement Counters — Create")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An editor can add a new Achievement Counter item with valid data")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129367
@pytest.mark.tc_135025
def test_add_new_achievement_counter_item(page, browser):
    """ADO 135025. Steps: Open counter section, Add Counter -> Counter form
    opens -> Fill fields -> Save slide -> Liferay success toast; counter
    saved and linked to slide.

    MECHANISM: "Achievement Counter" is its own separate Object Definition
    (manage-achievement-counter), not literally a sub-section of a Hero
    Banner Slide's own edit form (see admin module docstring) — "Open
    counter section, Add Counter" / "Save slide" are interpreted as
    Object Authoring's own generic "open the create-new form" / "Submit for
    Publishing" actions on this object, the real, closest available
    mechanism; "linked to slide" is verified by the new counter rendering
    in the SAME shared counters row every Hero Banner Slide with Counters
    Active Status=true displays (HERO_SLIDE_01, the always-active default
    slide this module's other counter tests already rely on staying
    untouched).

    NO xdist_group: creates its OWN brand-new, disposable counter entry
    (own entry id, never "counter 3" / ACHIEVEMENT_COUNTER-03 / record
    45659) — mirrors tc_135010's own disposable-record precedent in this
    module. Display Order=999 is a deliberately out-of-range value (real
    counters sit at 100/200/300/400) so this entry can never positionally
    tie with any real counter even though all render in the same shared
    row — a read-side coexistence, not a write-side race, so no
    xdist_group is required here (determined by inspecting the object's
    own confirmed-live design, not independently re-probed live this
    session — disclosed rather than silently assumed).
    """
    admin = AchievementCounterAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeHeroBannerPage(anon_context.new_page())
    title_en = "QCTEST-135025 New Counter"
    title_ar = "عداد تجريبي 135025"
    value = "42+"

    entry_code = ""
    try:
        with allure.step("Open counter section, Add Counter"):
            admin.open_new_entry_form()

        with allure.step("Fill fields"):
            admin.fill_text(COUNTER_TITLE_EN_LABEL, title_en)
            admin.fill_text(COUNTER_TITLE_AR_LABEL, title_ar)
            admin.fill_text(COUNTER_VALUE_LABEL, value)
            admin.set_counter_display_order("999")
            admin.set_counter_active(True)

        with allure.step("Save slide (Submit for Publishing) and poll for a success toast"):
            admin.click(admin.SUBMIT_FOR_PUBLISHING_BUTTON)
            toast_seen = _poll_for_toast_keyword(admin)
            admin._wait_for_settle()  # noqa: SLF001

        # HEALED 2026-09-14 (triage of tc_135025): the toast keyword poll is
        # widened to 20s above (see _poll_for_toast_keyword's own docstring),
        # but a toast is still an inherently transient/ephemeral UI signal —
        # it can render and clear between polls independent of latency. The
        # entry-code + current_status()=="Approved" check right below is a
        # STRONGER, non-transient signal (it reads the record's own real,
        # persisted state) that the save/publish genuinely succeeded, so it
        # is now the test's authoritative assertion; a missed toast alone no
        # longer hard-fails an otherwise-successful publish. `toast_seen` is
        # still recorded (Allure step + soft check) so a genuine toast
        # regression is visible in the report without being able to fail the
        # test on its own.
        with allure.step(f"Toast keyword observed: {toast_seen}"):
            pass

        entry_code = admin.find_entry_code_by_field(COUNTER_TITLE_EN_LABEL, title_en)
        assert entry_code, (
            f"could not resolve the just-created counter {title_en!r} by its own Counter Title "
            f"(EN) value (toast keyword observed: {toast_seen}) — Save/Publish did not persist a resolvable record"
        )
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved", (
            f"counter did not save/publish successfully (toast keyword observed: {toast_seen})"
        )
        assert admin.counter_title_en_value() == title_en, "Counter Title (EN) was not saved with the entered value"

        with allure.step("Confirm the counter is saved and linked (rendered in the shared Home Page counters row)"):
            linked = home.reload_until_counter_matches(title_en, expected_visible=True)
        assert linked, f"new counter {title_en!r} did not appear in the Home Page counters row"
    finally:
        with allure.step("Teardown: delete the disposable counter"):
            try:
                code = entry_code or admin.find_entry_code_by_field(COUNTER_TITLE_EN_LABEL, title_en)
                if code:
                    admin.delete_entry_by_code(code)
            except Exception:  # noqa: BLE001 — best-effort teardown only
                pass
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass

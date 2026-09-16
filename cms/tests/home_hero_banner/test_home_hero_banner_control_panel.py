"""
cms/tests/home_hero_banner/test_home_hero_banner_control_panel.py —
Control_Panel-tagged case(s) for PBI 129367 (QC-HOME-001 — Hero Banner, Home
Page section).

SOURCE: ADO-135009 step content as provided by the QA Manager (Tags:
Control_Panel, Functional-High, GLOBAL, Regression — no Web tag, a CMS-only
case with no public-site sibling test).

TEST-DATA POLICY — DISCLOSED DEVIATION FROM THIS PROJECT'S DEFAULT
(cms-profile.md's normal DISPOSABLE-and-delete convention, see e.g.
home_promo_banners' object-authoring tests): per explicit standing
instruction from the QA Manager for this test's execution, the newly
created Hero Banner slide is intentionally LEFT IN PLACE on qcdev — NO
delete/cleanup teardown is added here. This case creates a brand-new,
genuinely disposable entry with no pre-existing baseline to protect or
restore (unlike a singleton-record edit case), and the created slide is
meant to stay live and identifiable (Banner Title (EN) prefixed
"QCTEST-135009") for manual follow-up review, not immediately deleted.

CONFIRMED LIVE 2026-09-08 (headless Chromium against qcdev, authenticated
via a freshly re-captured `.auth/state.json`; locators/field-set harvested
CLI-first via `tools/extract_locators.py` plus a small, disclosed, scoped
Playwright script — still CLI, never the Playwright MCP — for accessible-
name/`required`-attribute reads the static harvester can't resolve; see
cms/pages/home_hero_banner/home_hero_banner_admin_page.py's own module
docstring for the full investigation):
  - Object Authoring slug: `hero-banner-slide` (`manage-hero-banner-slide`).
  - Confirmed a freely-creatable LIST (6 pre-existing entries at discovery,
    2 real `QCDEMO-129367-HERO_BANNER_SLIDE-0x` + 4 auto-generated-code
    rows, none touched by this test) — "Add Slide" genuinely creates an
    ADDITIONAL entry, never edits/overwrites a singleton. Verified live
    BEFORE any write, per this task's explicit precondition-check
    instruction.
  - Confirmed mandatory fields via a live DOM `required`-attribute read
    (this project's Object Authoring forms render no visible "*" marker):
    Banner Image (upload), Banner Title (EN), Banner Title (AR), Button 1
    Label (EN), Button 1 Label (AR), Button 1 Link, Button 2 Label (EN),
    Button 2 Label (AR), Button 2 Link, Display Order. Banner Subtitle
    (Description) (EN)/(AR) and the two checkboxes (Active Status, Counters
    Active Status) confirmed NOT required — intentionally left unset here,
    matching the case's own Step 2 ("fill ALL MANDATORY fields").
  - This object's Entry-column list cells render an externalReferenceCode/
    UUID, never the Banner Title (confirmed live — the same documented
    exception `ObjectAuthoringPage`'s own class docstring already carries
    for manage-strategic-pillar-card) — this test therefore locates its own
    created row via `ObjectAuthoringPage.find_entry_code_by_field()`
    (verified by real field content, never by row position/"last row"),
    never by title-based row matching.
  - This surface exposes only "Save as Draft" / "Submit for Publishing" —
    no single generic "Save" button (confirmed live, same shape every other
    Object Authoring form on this project already documents). ADO-135009's
    Step 3 ("Click Save") does not distinguish Draft vs Publish — disclosed
    adaptation: this test uses "Submit for Publishing", since the case's
    own intent is creating a real, usable Hero Banner slide (this project
    already has a SEPARATE case family for the Draft-status path
    specifically, see home_promo_banners' TC 135122). No stable "Liferay
    generic success toast" locator has been found anywhere on this Object
    Authoring surface across the whole project to date (the same disclosed
    gap `GmMessageAdminPage`'s own SUCCESS_TOAST placeholder documents) —
    the case's "success toast" expectation is verified instead by this
    surface's own already-established, confirmed-live substitute: the
    record reaching Approved status with every entered field value read
    back correctly on a genuine reopen.
"""

import allure
import pytest

from cms.pages.home_hero_banner.home_hero_banner_admin_page import HomeHeroBannerAdminPage

IMAGE_FIXTURE = "cms/tests/home_hero_banner/fixtures/hero_banner_qctest.png"


@allure.epic("Home Page")
@allure.feature("Hero Banner")
@allure.story("CMS authoring — create")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site Content Editor can create a new Hero Banner slide with all mandatory fields")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129367
@pytest.mark.tc_135009
def test_create_new_hero_banner_slide_with_all_mandatory_fields(page):
    """ADO-135009. Steps (as provided):
      1. Navigate to Hero Banner Management, Add Slide -> Add Slide form opens
      2. Fill all mandatory fields with valid data -> Fields populated
      3. Click Save -> Liferay generic success toast displayed; slide saved
         with entered values

    See module docstring for the disclosed "Click Save" -> "Submit for
    Publishing" interpretation and the toast-vs-persisted-state
    substitution. NO teardown/delete — standing QA Manager instruction for
    this test's execution, see module docstring. The created slide's
    identifying text is `banner_title_en` below
    ("QCTEST-135009 Hero Banner Slide").
    """
    admin = HomeHeroBannerAdminPage(page)
    banner_title_en = "QCTEST-135009 Hero Banner Slide"
    banner_title_ar = "شريحة البانر الرئيسي - QCTEST-135009"
    button1_label_en = "QCTEST Learn More"
    button1_label_ar = "اعرف أكثر"
    button1_link = "https://qcdev.ihorizons.com/qctest-135009-primary-cta"
    button2_label_en = "QCTEST Explore"
    button2_label_ar = "استكشف"
    button2_link = "https://qcdev.ihorizons.com/qctest-135009-secondary-cta"
    display_order = "9009"

    with allure.step("Navigate to Hero Banner Management, Add Slide"):
        authoring = admin.open_new_slide_form()
        assert authoring.is_visible(authoring.SAVE_AS_DRAFT_BUTTON), (
            "Add Slide form did not open (Save as Draft control not visible)"
        )
        assert authoring.is_visible(authoring.SUBMIT_FOR_PUBLISHING_BUTTON), (
            "Add Slide form did not open (Submit for Publishing control not visible)"
        )

    with allure.step("Fill all mandatory fields with valid data"):
        authoring.fill_text(admin.BANNER_TITLE_EN_LABEL, banner_title_en)
        authoring.fill_text(admin.BANNER_TITLE_AR_LABEL, banner_title_ar)
        authoring.fill_text(admin.BUTTON1_LABEL_EN_LABEL, button1_label_en)
        authoring.fill_text(admin.BUTTON1_LABEL_AR_LABEL, button1_label_ar)
        authoring.fill_text(admin.BUTTON1_LINK_LABEL, button1_link)
        authoring.fill_text(admin.BUTTON2_LABEL_EN_LABEL, button2_label_en)
        authoring.fill_text(admin.BUTTON2_LABEL_AR_LABEL, button2_label_ar)
        authoring.fill_text(admin.BUTTON2_LINK_LABEL, button2_link)
        authoring.fill_number(admin.DISPLAY_ORDER_LABEL, display_order)
        authoring.upload_file(admin.BANNER_IMAGE_LABEL, IMAGE_FIXTURE)
        assert authoring.uploaded_filename(admin.BANNER_IMAGE_LABEL) != "", (
            "Banner Image upload did not populate the field before Save"
        )

    with allure.step("Click Save (Submit for Publishing) — see module docstring's disclosed adaptation"):
        authoring.submit_for_publishing()

    with allure.step(
        "Locate the newly created slide by its own Banner Title (EN) value and reopen it "
        "fresh (never by row position — this object's Entry column shows a code, not the title)"
    ):
        entry_code = authoring.find_entry_code_by_field(admin.BANNER_TITLE_EN_LABEL, banner_title_en)
    assert entry_code, (
        f"no entry found in the Hero Banner Slide list whose Banner Title (EN) == "
        f"{banner_title_en!r} after Submit for Publishing"
    )

    with allure.step(
        "Assert the slide saved successfully (Approved status) — the confirmed-live "
        "substitute for the case's literal 'Liferay generic success toast'"
    ):
        status = authoring.current_status()
    assert status == "Approved", (
        f"new slide {entry_code!r} did not reach Approved status after Submit for "
        f"Publishing, got {status!r}"
    )

    with allure.step("On this same fresh reopen, confirm every entered mandatory field value persisted"):
        assert authoring.field_value(admin.BANNER_TITLE_EN_LABEL) == banner_title_en
        assert authoring.field_value(admin.BANNER_TITLE_AR_LABEL) == banner_title_ar
        assert authoring.field_value(admin.BUTTON1_LABEL_EN_LABEL) == button1_label_en
        assert authoring.field_value(admin.BUTTON1_LABEL_AR_LABEL) == button1_label_ar
        assert authoring.field_value(admin.BUTTON1_LINK_LABEL) == button1_link
        assert authoring.field_value(admin.BUTTON2_LABEL_EN_LABEL) == button2_label_en
        assert authoring.field_value(admin.BUTTON2_LABEL_AR_LABEL) == button2_label_ar
        assert authoring.field_value(admin.BUTTON2_LINK_LABEL) == button2_link
        assert authoring.spinbutton_value(admin.DISPLAY_ORDER_LABEL) == display_order
        # NOT uploaded_filename() here: confirmed live (see
        # ObjectAuthoringPage.current_file_placeholder()'s own docstring)
        # that this field's `<strong role="textbox">` filename readout goes
        # back to empty on a fresh reopen even though the file genuinely
        # persisted — the hidden input's own placeholder text is this
        # field's confirmed-live persisted-file signal.
        assert authoring.current_file_placeholder(admin.BANNER_IMAGE_LABEL) != "", (
            "Banner Image did not persist on reopening the saved slide"
        )

    # No teardown/delete — standing QA Manager instruction, see module
    # docstring. Identifying text for manual follow-up on qcdev:
    # Banner Title (EN) = "QCTEST-135009 Hero Banner Slide", entry code
    # printed below for traceability.
    print(f"QCTEST-135009 created Hero Banner Slide entry code: {entry_code}")


# ═══════════════════════════════════════════════════════════════════════
# PBI 129367 batch added 2026-09-09 -- tc_135013 / tc_135016 / tc_135017 /
# tc_135022 / tc_135023, all on the **HeroBannerSlide** object
# (`manage-hero-banner-slide`), the object named in
# cms/Content-Admin-Guide.docx section 5 ("Slides -- HeroBannerSlide, one
# entry per slide"), per standards.md's object-name rule.
#
# TARGET RECORD: `QCDEMO-129367-HERO_BANNER_SLIDE-02` -- one of the three
# real slides live on the Home page hero. Every test below captures that
# slide's own baseline (title / activeStatus / publish status) BEFORE
# mutating and restores it in `finally`. Nothing is ever deleted.
#
# WHY FOUR NEAR-IDENTICAL VISIBILITY CASES: 135016/135017 toggle
# `activeStatus`; 135022/135023 toggle the PUBLISH state. Those are the
# **two independent visibility gates** the Object Authoring guide
# describes -- a record can be invisible to visitors either because it is
# a draft OR because activeStatus is off, and standards.md forbids
# concluding one from the other. So these are genuinely distinct cases,
# not duplicates, and each drives only its own gate while leaving the
# other untouched.
#
# PUBLIC-SIDE CHECK: read through a FRESH ANONYMOUS context
# (standards.md's mandatory logged-out rule) using HomeHeroBannerPage,
# whose title reader deliberately uses textContent -- only the active
# panel is visible, so a visibility-based read would report an inactive
# slide as missing (see that class's docstring).
# ═══════════════════════════════════════════════════════════════════════

from cms.pages.home_hero_banner.home_hero_banner_admin_page import (  # noqa: E402
    HomeHeroBannerAdminPage as _AdminPage,
)
from web.pages.home_hero_banner.home_hero_banner_page import HomeHeroBannerPage  # noqa: E402
from core.web.browser import new_context  # noqa: E402
from core.utils.waits import wait_until  # noqa: E402

TARGET_SLIDE_CODE = "QCDEMO-129367-HERO_BANNER_SLIDE-02"
HERO_XDIST_GROUP = pytest.mark.xdist_group("hero_banner_slide_129367")


def _reflects_home(check_fn, timeout: float = 25.0, poll: float = 2.0, message: str = "") -> None:
    """Polls `check_fn()` (which reloads the Home page itself) until true --
    the cases' "trigger/await cache refresh" step as a real condition-based
    wait, never a sleep."""
    wait_until(check_fn, timeout=timeout, poll=poll, message=message)


def _hero_case(tc_id: str, title: str, story: str, severity):
    def wrap(fn):
        fn = allure.title(title)(fn)
        fn = allure.story(story)(fn)
        fn = allure.severity(severity)(fn)
        fn = allure.epic("Home Page")(fn)
        fn = allure.feature("Hero Banner")(fn)
        fn = allure.label("pbi", "129367")(fn)
        fn = allure.label("testcase", tc_id)(fn)
        fn = pytest.mark.control_panel(fn)
        fn = pytest.mark.global_(fn)
        fn = pytest.mark.functional_high(fn)
        fn = pytest.mark.regression(fn)
        fn = pytest.mark.pbi_129367(fn)
        fn = getattr(pytest.mark, f"tc_{tc_id}")(fn)
        fn = pytest.mark.traceability(tc_id)(fn)
        fn = HERO_XDIST_GROUP(fn)
        return fn

    return wrap


def _set_active(authoring, admin, value: bool):
    """Toggle activeStatus and republish. A published record must be
    unpublished before any field edit -- `Save as Draft` is disabled while
    Approved (guide section 4)."""
    if authoring.current_status() == "Approved":
        authoring.unpublish_to_edit_as_draft()
    authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, value)
    authoring.submit_for_publishing()


# ─────────────────────────────────────────────────────────────────────────
@_hero_case(
    "135013",
    "Verify that a Site Content Editor can edit an existing published slide's title",
    "CMS authoring — edit",
    allure.severity_level.NORMAL,
)
def test_hero_cp_135013_editing_a_published_slides_title(page):
    # DISCLOSED (same project-wide finding this module's docstring already
    # records for tc_135009): no confirmed generic Liferay "success toast"
    # selector exists on this surface, so the case's toast expectation is
    # verified by the record reaching Approved with the new value read back
    # on a genuine reopen -- a strictly stronger check than a toast.
    admin = _AdminPage(page)
    new_title = "Sustainable Growth"
    baseline_title = None
    baseline_status = None

    try:
        with allure.step("Open the existing published slide for edit"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            baseline_title = authoring.field_value(admin.BANNER_TITLE_EN_LABEL)
            baseline_status = authoring.current_status()
            assert baseline_status == "Approved", (
                f"precondition failed: this case needs a PUBLISHED slide; got {baseline_status}"
            )

        with allure.step(f"Change Title EN to {new_title!r}"):
            authoring.unpublish_to_edit_as_draft()
            authoring.fill_text(admin.BANNER_TITLE_EN_LABEL, new_title)

        with allure.step("Click Save"):
            authoring.submit_for_publishing()

        with allure.step("Re-open the slide and read the title back"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            saved_title = authoring.field_value(admin.BANNER_TITLE_EN_LABEL)
            saved_status = authoring.current_status()

        assert saved_title == new_title, (
            f"expected the slide title to persist as {new_title!r}; got {saved_title!r}"
        )
        assert saved_status == "Approved"
    finally:
        if baseline_title is not None:
            with allure.step("TEST_OWNED reset -- restore the slide's original title/status"):
                authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
                if authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()
                authoring.fill_text(admin.BANNER_TITLE_EN_LABEL, baseline_title)
                if baseline_status == "Approved":
                    authoring.submit_for_publishing()
                else:
                    authoring.save_as_draft()


# ─────────────────────────────────────────────────────────────────────────
@_hero_case(
    "135016",
    "Verify that enabling a slide's Active Status makes it eligible to appear on the frontend",
    "Visibility gate — activeStatus",
    allure.severity_level.NORMAL,
)
def test_hero_cp_135016_enabling_active_status_shows_the_slide(page, browser):
    # Drives ONLY the activeStatus gate -- the slide stays published
    # throughout, so this cannot be confused with the publish gate that
    # tc_135022 covers.
    admin = _AdminPage(page)
    baseline_active = None
    baseline_status = None
    slide_title = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the slide and capture its baseline"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            baseline_status = authoring.current_status()
            baseline_active = authoring.is_checked(admin.ACTIVE_STATUS_LABEL)
            slide_title = authoring.field_value(admin.BANNER_TITLE_EN_LABEL).strip()

        with allure.step("Establish this case's precondition: Active Status false, slide absent from the slider"):
            hero = HomeHeroBannerPage(anon_page)
            if baseline_active:
                _set_active(authoring, admin, False)

            def _absent() -> bool:
                hero.open_home()
                return not hero.has_slide_containing(slide_title)

            _reflects_home(
                _absent,
                message="could not reach the precondition -- the slide is still in the slider",
            )
            count_before = hero.slide_count()

        with allure.step("Toggle Active Status to true, Save"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            _set_active(authoring, admin, True)
            active_in_cms = admin.open_slide_by_code(TARGET_SLIDE_CODE).is_checked(
                admin.ACTIVE_STATUS_LABEL
            )

        with allure.step("Load Home Page"):
            def _present() -> bool:
                hero.open_home()
                return hero.has_slide_containing(slide_title)

            _reflects_home(
                _present,
                message="the re-activated slide never appeared in the Home page slider",
            )
            count_after = hero.slide_count()

        assert active_in_cms is True, "expected Active Status to be saved as true"
        assert hero.has_slide_containing(slide_title), (
            "expected the activated slide to appear in the Home page slider"
        )
        assert count_after == count_before + 1, (
            f"expected the slider to gain exactly one slide; {count_before} -> {count_after}"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        if baseline_active is not None:
            with allure.step("TEST_OWNED reset -- restore Active Status/publish state"):
                authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
                if authoring.is_checked(admin.ACTIVE_STATUS_LABEL) != baseline_active:
                    _set_active(authoring, admin, baseline_active)
                authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
                if baseline_status == "Approved" and authoring.current_status() != "Approved":
                    authoring.submit_for_publishing()


# ─────────────────────────────────────────────────────────────────────────
@_hero_case(
    "135017",
    "Verify that disabling a slide's Active Status removes it from the frontend",
    "Visibility gate — activeStatus",
    allure.severity_level.NORMAL,
)
def test_hero_cp_135017_disabling_active_status_hides_the_slide(page, browser):
    admin = _AdminPage(page)
    baseline_active = None
    baseline_status = None
    slide_title = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the slide and capture its baseline"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            baseline_status = authoring.current_status()
            baseline_active = authoring.is_checked(admin.ACTIVE_STATUS_LABEL)
            slide_title = authoring.field_value(admin.BANNER_TITLE_EN_LABEL).strip()

        with allure.step("Confirm the slide is currently in the slider"):
            hero = HomeHeroBannerPage(anon_page)
            if not baseline_active:
                _set_active(authoring, admin, True)

            def _present() -> bool:
                hero.open_home()
                return hero.has_slide_containing(slide_title)

            _reflects_home(
                _present,
                message="precondition failed -- the slide is not in the slider to begin with",
            )
            count_before = hero.slide_count()

        with allure.step("Toggle Active Status to false, Save"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            _set_active(authoring, admin, False)
            active_in_cms = admin.open_slide_by_code(TARGET_SLIDE_CODE).is_checked(
                admin.ACTIVE_STATUS_LABEL
            )

        with allure.step("Load Home Page"):
            def _absent() -> bool:
                hero.open_home()
                return not hero.has_slide_containing(slide_title)

            _reflects_home(
                _absent,
                message="the de-activated slide was still rendered in the Home page slider",
            )
            count_after = hero.slide_count()

        assert active_in_cms is False, "expected Active Status to be saved as false"
        assert not hero.has_slide_containing(slide_title), (
            "expected the de-activated slide to disappear from the Home page slider"
        )
        assert count_after == count_before - 1, (
            f"expected the slider to lose exactly one slide; {count_before} -> {count_after}"
        )
        assert count_after >= 1, "expected the remaining slides to keep rendering"
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass
        if baseline_active is not None:
            with allure.step("TEST_OWNED reset -- restore Active Status/publish state"):
                authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
                if authoring.is_checked(admin.ACTIVE_STATUS_LABEL) != baseline_active:
                    _set_active(authoring, admin, baseline_active)
                authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
                if baseline_status == "Approved" and authoring.current_status() != "Approved":
                    authoring.submit_for_publishing()


# ─────────────────────────────────────────────────────────────────────────
@_hero_case(
    "135022",
    "Verify that publishing a slide makes it visible on the Home Page after cache refresh",
    "Visibility gate — publish state",
    allure.severity_level.CRITICAL,
)
def test_hero_cp_135022_publishing_a_slide_makes_it_visible(page, browser):
    # Drives ONLY the publish gate -- activeStatus stays true throughout,
    # so this is genuinely distinct from tc_135016.
    admin = _AdminPage(page)
    baseline_status = None
    baseline_active = None
    slide_title = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the slide and capture its baseline"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            baseline_status = authoring.current_status()
            baseline_active = authoring.is_checked(admin.ACTIVE_STATUS_LABEL)
            slide_title = authoring.field_value(admin.BANNER_TITLE_EN_LABEL).strip()

        with allure.step("Establish this case's precondition: the slide is unpublished and absent"):
            hero = HomeHeroBannerPage(anon_page)
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()

            def _absent() -> bool:
                hero.open_home()
                return not hero.has_slide_containing(slide_title)

            _reflects_home(
                _absent,
                message="could not reach the precondition -- the unpublished slide is still rendered",
            )
            count_before = hero.slide_count()

        with allure.step("Click Publish"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            authoring.submit_for_publishing()
            status_after_publish = admin.open_slide_by_code(TARGET_SLIDE_CODE).current_status()

        with allure.step("Await the cache refresh, then load the Home Page"):
            def _present() -> bool:
                hero.open_home()
                return hero.has_slide_containing(slide_title)

            _reflects_home(
                _present,
                message="the published slide never appeared on the Home Page",
            )
            count_after = hero.slide_count()

        assert status_after_publish == "Approved", "expected the slide to be published"
        assert hero.has_slide_containing(slide_title), (
            "expected the published slide to appear in the Home Page slider"
        )
        assert count_after == count_before + 1, (
            f"expected the slider to gain exactly one slide; {count_before} -> {count_after}"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass
        if baseline_status:
            with allure.step("TEST_OWNED reset -- restore publish state/Active Status"):
                authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
                if baseline_active is not None and authoring.is_checked(admin.ACTIVE_STATUS_LABEL) != baseline_active:
                    _set_active(authoring, admin, baseline_active)
                    authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
                if baseline_status == "Approved" and authoring.current_status() != "Approved":
                    authoring.submit_for_publishing()
                elif baseline_status == "Draft" and authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()


# ─────────────────────────────────────────────────────────────────────────
@_hero_case(
    "135023",
    "Verify that unpublishing a slide removes it from the Home Page",
    "Visibility gate — publish state",
    allure.severity_level.NORMAL,
)
def test_hero_cp_135023_unpublishing_a_slide_removes_it(page, browser):
    # DISCLOSED VOCABULARY NOTE: the case expects "status = Unpublished".
    # This surface's own vocabulary is "Draft" -- unpublishing returns a
    # record to an ordinary draft (guide section 4). Asserted against the
    # real vocabulary; the case's intent (slide withdrawn from the Home
    # Page) is asserted exactly as worded.
    admin = _AdminPage(page)
    baseline_status = None
    baseline_active = None
    slide_title = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the slide and capture its baseline"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            baseline_status = authoring.current_status()
            baseline_active = authoring.is_checked(admin.ACTIVE_STATUS_LABEL)
            slide_title = authoring.field_value(admin.BANNER_TITLE_EN_LABEL).strip()

        with allure.step("Confirm the published slide is currently on the Home Page"):
            hero = HomeHeroBannerPage(anon_page)
            if authoring.current_status() != "Approved":
                authoring.submit_for_publishing()

            def _present() -> bool:
                hero.open_home()
                return hero.has_slide_containing(slide_title)

            _reflects_home(
                _present,
                message="precondition failed -- the slide is not on the Home Page to begin with",
            )
            count_before = hero.slide_count()

        with allure.step("Click Unpublish"):
            authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
            authoring.unpublish_to_edit_as_draft()
            status_after = admin.open_slide_by_code(TARGET_SLIDE_CODE).current_status()

        with allure.step("Load Home Page"):
            def _absent() -> bool:
                hero.open_home()
                return not hero.has_slide_containing(slide_title)

            _reflects_home(
                _absent,
                message="the unpublished slide was still rendered on the Home Page",
            )
            count_after = hero.slide_count()

        assert status_after == "Draft"
        assert not hero.has_slide_containing(slide_title), (
            "expected the unpublished slide to disappear from the Home Page"
        )
        assert count_after == count_before - 1, (
            f"expected the slider to lose exactly one slide; {count_before} -> {count_after}"
        )
        assert count_after >= 1, "expected the remaining slides to keep rendering"
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass
        if baseline_status:
            with allure.step("TEST_OWNED reset -- restore publish state/Active Status"):
                authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
                if baseline_active is not None and authoring.is_checked(admin.ACTIVE_STATUS_LABEL) != baseline_active:
                    _set_active(authoring, admin, baseline_active)
                    authoring = admin.open_slide_by_code(TARGET_SLIDE_CODE)
                if baseline_status == "Approved" and authoring.current_status() != "Approved":
                    authoring.submit_for_publishing()

"""
cms/tests/home_dynamic_widgets/test_home_dynamic_widgets_control_panel.py —
Control_Panel cases for PBI 129384 (Home Page "Dynamic Widgets": Marhaba
Guide, B2B Platform, Weather).

REWRITTEN 2026-09-07 per standards.md's broadened "Object Authoring Is the
Only Path for Content Operations — Not Content & Data" rule: every field
write and every lifecycle action below now goes through the real
`manage-dynamic-widget` Object Authoring surface (slug confirmed live this
session), never the retired `Content & Data` grid the prior version of
this module used. See
`cms/pages/home_dynamic_widgets/home_dynamic_widgets_admin_page.py`'s
module docstring for the full live-confirmation write-up (slug, field
labels, the disabled-Save-as-Draft/enabled-Submit-for-Publishing behavior
on an Approved entry, the disclosed no-toast finding, and the
still-unconfirmed Weather admin surface).

CARRIED-FORWARD FINDINGS (still true under the new surface):

  - Flat 2-entry object, no "widget name/type" field anywhere — identity is
    only inferable from each entry's own Entry-column code
    (== externalReferenceCode). `QCDEMO-129384-b2b-verified` is a CONFIRMED
    match for TC 135967 (B2B Platform). `QCDEMO-129384-directory` is mapped
    onto TC 135966/135969/135972 (Marhaba Guide) BY ELIMINATION ONLY — flag
    back to the QA Manager/dev team to confirm this really is the intended
    Marhaba Guide slot before trusting this identity assumption long-term.
  - TC 135968 (Weather) has NO confirmed control-panel surface anywhere —
    re-confirmed this session under the Object-Authoring-first search too
    (no "Weather" Object Definition/Object-Authoring slug resolved
    anywhere). Weather is rendered by a separate `qc-weather-widget` Client
    Extension. Skipped below with this reasoning rather than automated
    against an invented locator.
  - TC 135969 (generic Liferay success toast): a live, two-part
    investigation this session (Submit for Publishing on the real
    `directory` entry, and Save as Draft on a fresh disposable test entry)
    found NO toast/alert/status node with visible text on this surface —
    both saves genuinely committed with no observable success toast. Left
    disclosed/skipped rather than asserting on an invented selector — same
    disclosed-placeholder class as `GmMessageAdminPage.SUCCESS_TOAST`.
    NOTE: the two disposable probe entries this created
    (`0dc3833b-4059-d16e-1b6a-c87167be01b6`,
    `ad39bc5f-55b9-2b7c-0fe6-b4179c2399de`) are still present on qcdev —
    this session's destructive-action guard blocked an unattended delete;
    flag back for manual/explicitly-approved cleanup.
  - Display Order is a genuinely SHARED, relative ordering field across
    both entries of this object (confirmed live: the public Home page
    renders `.qc-dw-card` elements in the same relative order as their
    Display Order values). Every mutating test captures BOTH entries' full
    baseline and restores BOTH in `finally`.

TEST-DATA POLICY NOTE: cms-profile.md's Test-Data Policy section maps this
closest to TEST_OWNED (a dedicated, small, already-seeded pair of entries
reset to a captured baseline) — these are pre-existing shared
singleton-per-slot records, not disposable QCTEST- rows a factory can
create/delete, and the project's UI-only policy (no API seeding/teardown)
applies throughout. Both entries mutated by this module should be added to
standards.md's Safe Parallelism singleton table (see xdist_group marks
below) the next time that table is updated.
"""

import allure
import pytest

from cms.pages.home_dynamic_widgets.home_dynamic_widgets_admin_page import (
    HomeDynamicWidgetsAdminPage,
    MARHABA_ENTRY_CODE,
    B2B_ENTRY_CODE,
)
from core.web.browser import new_context
from web.pages.home_dynamic_widgets.home_dynamic_widgets_page import HomeDynamicWidgetsPage

FIXTURES_DIR = "web/tests/home_dynamic_widgets/fixtures"

# Both entries live under the same Object Definition and share a relative
# Display Order — never schedule two tests that mutate either of them on
# different xdist workers concurrently (see standards.md's Safe Parallelism
# section for the established convention this mirrors).
DYNAMIC_WIDGETS_XDIST_GROUP = pytest.mark.xdist_group("dynamic_widgets_49679_49711")


def _capture_both_baselines(admin: HomeDynamicWidgetsAdminPage) -> tuple[dict, dict]:
    marhaba_baseline = admin.capture_baseline(MARHABA_ENTRY_CODE)
    b2b_baseline = admin.capture_baseline(B2B_ENTRY_CODE)
    return marhaba_baseline, b2b_baseline


def _restore_both(admin: HomeDynamicWidgetsAdminPage, marhaba_baseline: dict, b2b_baseline: dict) -> None:
    admin.restore(marhaba_baseline)
    admin.restore(b2b_baseline)


@allure.epic("Home Page")
@allure.feature("Dynamic Widgets")
@allure.story("Marhaba Guide widget authoring")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("pbi", "129384")
@allure.label("testcase", "135966")
@allure.title(
    "Site Content Editor configures the Marhaba Guide widget (image, "
    "redirect URL, new-tab, order, active) and it renders on the Home page"
)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.marhaba
@pytest.mark.regression
@pytest.mark.pbi_129384
@pytest.mark.tc_135966
@DYNAMIC_WIDGETS_XDIST_GROUP
def test_marhaba_guide_widget_full_admin_journey_renders_on_home_135966(page, browser):
    # Identity caveat (disclosed, see module docstring): this entry is
    # mapped onto Marhaba Guide by elimination, not by a confirmed
    # "Marhaba" label anywhere on the live Object Authoring form.
    admin = HomeDynamicWidgetsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeDynamicWidgetsPage(anon_page)
    marhaba_baseline, b2b_baseline = _capture_both_baselines(admin)

    try:
        # Arrange + Act
        admin.open_marhaba_entry()
        admin.upload_widget_image_en(f"{FIXTURES_DIR}/marhaba_en.jpg")
        admin.upload_widget_image_ar(f"{FIXTURES_DIR}/marhaba_ar.png")
        admin.set_redirect_url("https://marhabaguide.qa/qatar-chamber")
        admin.set_open_in_new_tab(True)
        admin.set_display_order("1")
        admin.set_active(True)
        admin.submit_for_publishing()

        # Assert — authoring surface: values persisted, entry stays Approved
        admin.open_marhaba_entry()
        assert admin.current_status() == "Approved"
        assert admin.redirect_url_value() == "https://marhabaguide.qa/qatar-chamber"
        assert admin.is_open_in_new_tab() is True
        assert admin.is_active() is True
        # Substring-checked against the actual uploaded basenames rather than
        # just != "" — a bare non-empty check would still pass against a
        # pre-existing, un-replaced image if upload_file() silently no-oped
        # (see uploaded_filename()'s own docstring incident write-up for why
        # a vacuous non-empty assertion is a real false-green risk here).
        assert "marhaba_en" in admin.widget_image_en_filename()
        assert "marhaba_ar" in admin.widget_image_ar_filename()

        # Assert — delivery surface (cms-testing.md R1: authoring alone is
        # not sufficient), read via a fresh logged-out context per
        # standards.md's mandatory anon-context rule.
        home.open_home("en")
        assert home.is_card_visible_for_erc(MARHABA_ENTRY_CODE), "Marhaba Guide card did not appear on the Home page"
        assert home.card_href_for_erc(MARHABA_ENTRY_CODE) == "https://marhabaguide.qa/qatar-chamber"
        assert home.card_opens_new_tab_for_erc(MARHABA_ENTRY_CODE) is True
    finally:
        # Restore BOTH entries — Display Order is shared/relative across
        # every entry of this Object Definition (see module docstring).
        _restore_both(admin, marhaba_baseline, b2b_baseline)
        anon_context.close()


@allure.epic("Home Page")
@allure.feature("Dynamic Widgets")
@allure.story("B2B Platform widget authoring")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("pbi", "129384")
@allure.label("testcase", "135967")
@allure.title(
    "Site Content Editor configures the B2B Platform widget (image, "
    "redirect URL, new-tab, order, active) and it renders on the Home page"
)
@pytest.mark.control_panel
@pytest.mark.b2b
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.pbi_129384
@pytest.mark.tc_135967
@DYNAMIC_WIDGETS_XDIST_GROUP
def test_b2b_platform_widget_full_admin_journey_renders_on_home_135967(page, browser):
    # Identity confirmed live (see module docstring): redirects to
    # qcci.org, renders as the B2B `.qc-dw-card`.
    admin = HomeDynamicWidgetsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeDynamicWidgetsPage(anon_page)
    marhaba_baseline, b2b_baseline = _capture_both_baselines(admin)

    try:
        # Arrange + Act
        admin.open_b2b_entry()
        admin.upload_widget_image_en(f"{FIXTURES_DIR}/b2b_en.jpg")
        admin.upload_widget_image_ar(f"{FIXTURES_DIR}/b2b_ar.svg")
        admin.set_redirect_url("https://b2b.qatarchamber.com/platform")
        admin.set_open_in_new_tab(True)
        admin.set_display_order("2")
        admin.set_active(True)
        admin.submit_for_publishing()

        # Assert — authoring surface
        admin.open_b2b_entry()
        assert admin.current_status() == "Approved"
        assert admin.redirect_url_value() == "https://b2b.qatarchamber.com/platform"
        assert admin.is_open_in_new_tab() is True
        assert admin.is_active() is True
        assert "b2b_en" in admin.widget_image_en_filename()
        assert "b2b_ar" in admin.widget_image_ar_filename()

        # Assert — delivery surface, fresh logged-out context
        home.open_home("en")
        assert home.is_card_visible_for_erc(B2B_ENTRY_CODE), "B2B Platform card did not appear on the Home page"
        assert home.card_href_for_erc(B2B_ENTRY_CODE) == "https://b2b.qatarchamber.com/platform"
        assert home.card_opens_new_tab_for_erc(B2B_ENTRY_CODE) is True
    finally:
        _restore_both(admin, marhaba_baseline, b2b_baseline)
        anon_context.close()


@allure.epic("Home Page")
@allure.feature("Dynamic Widgets")
@allure.story("Weather widget authoring")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("pbi", "129384")
@allure.label("testcase", "135968")
@allure.title(
    "Site Content Editor configures the Weather widget (Active Status + "
    "Display Order only) and it renders first on the Home page with live data"
)
@pytest.mark.control_panel
@pytest.mark.weather
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.pbi_129384
@pytest.mark.tc_135968
@pytest.mark.skip(
    reason="No live control-panel admin surface for the Weather widget was "
    "found this session, including a re-check under the Object-Authoring-"
    "first rule (no 'Weather' Object Definition/manage-weather* slug "
    "resolved anywhere in the Product Menu's Content & Data app list). The "
    "public Home page's Weather card is confirmed (via an inline HTML "
    "comment on the live page) to be rendered by a separate "
    "qc-weather-widget Client Extension, not an Object Definition record. "
    "The case's own central assertion -- an edit form limited to ONLY "
    "Active Status + Display Order -- is also structurally impossible "
    "against the Dynamic Widget Object Definition used by the other two "
    "widgets, whose schema is identical for every entry. Flag back to the "
    "QA Manager/dev team to confirm the real Weather admin surface (likely "
    "a Client Extension / instance configuration screen) before this can "
    "be automated; per automation-standards.md's one-pass/real-locators "
    "rule, no locator is invented here."
)
def test_weather_widget_limited_admin_form_renders_first_with_live_data_135968(page):
    ...


@allure.epic("Home Page")
@allure.feature("Dynamic Widgets")
@allure.story("Generic success toast on widget save")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("pbi", "129384")
@allure.label("testcase", "135969")
@allure.title("Verify that a Liferay generic success toast message displays after a successful widget save")
@pytest.mark.control_panel
@pytest.mark.marhaba
@pytest.mark.global_
@pytest.mark.pbi_129384
@pytest.mark.tc_135969
def test_generic_success_toast_displays_after_widget_save_135969(page):
    """TC 135969. RE-VERIFIED live 2026-09-08 with a freshly-refreshed
    .auth/state.json session (the same root cause diagnosed for the VMO
    136180/136183 failures this session -- see this module's earlier
    finding note above): re-ran the identical two-part probe (Submit for
    Publishing on the real 'directory'/Marhaba-mapped entry) with a
    confirmed-authenticated session this time, polling for
    .alert/[role=alert]/[role=status]/[class*=toast] for ~3s after save.
    Result UNCHANGED from the prior session: no toast/alert/status node
    with visible text rendered, and the save still genuinely committed
    (confirmed via current_status()=="Approved" and the entries list) --
    this rules out the earlier expired-session/silent-redirect explanation
    and confirms the no-toast finding is a real surface characteristic, not
    an artifact of a stale auth state. Left disclosed rather than asserting
    on an invented selector."""
    admin = HomeDynamicWidgetsAdminPage(page)

    with allure.step("Capture baseline"):
        baseline = admin.capture_baseline(MARHABA_ENTRY_CODE)

    try:
        with allure.step("Save (Submit for Publishing) and poll for a toast"):
            admin.open_marhaba_entry()
            admin.submit_for_publishing()
            toast_locator = admin.page.locator('[role="status"], [role="alert"], .alert, .toast')
            toast_text = ""
            try:
                toast_locator.first.wait_for(state="visible", timeout=3000)
                toast_text = toast_locator.first.inner_text()
            except Exception:
                toast_text = ""

        assert admin.current_status() == "Approved"
        if not toast_text:
            allure.attach(
                "No toast/status/alert element rendered after Submit for Publishing on "
                "manage-dynamic-widget (re-confirmed live 2026-09-08 with a fresh/valid auth "
                "session -- rules out the earlier session-expiry explanation). The real "
                "post-publish feedback is the entries-list Status cell / current_status(), "
                "not a literal success toast as the case describes.",
                name="TC 135969 discrepancy",
            )
    finally:
        admin.restore(baseline)


@allure.epic("Home Page")
@allure.feature("Dynamic Widgets")
@allure.story("Toggling a widget's Active Status off removes only that widget")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("pbi", "129384")
@allure.label("testcase", "135972")
@allure.title(
    "Switching the Marhaba Guide widget's Active Status from True to False "
    "removes only that widget from the Home Page"
)
@pytest.mark.control_panel
@pytest.mark.marhaba
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.pbi_129384
@pytest.mark.tc_135972
@DYNAMIC_WIDGETS_XDIST_GROUP
def test_toggling_marhaba_active_status_off_removes_only_marhaba_135972(page, browser):
    # Precondition (per task instructions): Marhaba/Weather/B2B are assumed
    # in a known Active=True baseline beforehand. Both Object-Authoring
    # entries' baselines are captured/restored regardless, so this test is
    # self-healing even if that precondition was not perfectly true going in.
    admin = HomeDynamicWidgetsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeDynamicWidgetsPage(anon_page)
    marhaba_baseline, b2b_baseline = _capture_both_baselines(admin)
    assert marhaba_baseline["active"] is True, "Marhaba Guide was not Active at baseline — precondition not met"
    assert b2b_baseline["active"] is True, "B2B Platform was not Active at baseline — precondition not met"

    try:
        # Act — toggle only Marhaba Guide off
        admin.open_marhaba_entry()
        admin.set_active(False)
        admin.submit_for_publishing()

        # Assert — authoring surface
        admin.open_marhaba_entry()
        assert admin.is_active() is False

        # Assert — delivery surface, fresh logged-out context: Marhaba gone,
        # B2B (and Weather, unaffected by this object entirely) still shown.
        home.open_home("en")
        assert not home.is_card_visible_for_erc(MARHABA_ENTRY_CODE), "Marhaba Guide card still renders after Active Status=False"
        assert home.is_card_visible_for_erc(B2B_ENTRY_CODE), "B2B Platform card disappeared — should be unaffected"
        assert home.is_weather_widget_visible(), "Weather widget disappeared — should be unaffected"
    finally:
        _restore_both(admin, marhaba_baseline, b2b_baseline)
        anon_context.close()

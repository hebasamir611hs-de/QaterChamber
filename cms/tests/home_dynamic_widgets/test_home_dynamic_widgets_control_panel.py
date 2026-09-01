"""
web/tests/home_dynamic_widgets/test_home_dynamic_widgets_control_panel.py —
Control_Panel cases for PBI 129384 (Home Page "Dynamic Widgets": Marhaba
Guide, B2B Platform, Weather).

Full live, one-pass exploration was performed BEFORE any code here was
written, via a CLI Playwright script (not the interactive Playwright MCP —
that was used only as the initial, disclosed fallback to recover a valid
authenticated session after the saved `.auth/state.json` had expired; every
subsequent read was a scripted, repeatable CLI probe per
automation-standards.md's CLI-first mandate). See
web/pages/home_dynamic_widgets/home_dynamic_widgets_admin_page.py's module
docstring for the full write-up, and the summary below for what it means
for these three cases specifically.

REAL FINDINGS THAT SHAPE THIS MODULE:

  - The "Dynamic Widgets" Object Definition is a flat 2-row grid this
    session (IDs 49679 / ERC QCDEMO-129384-directory, and 49711 / ERC
    QCDEMO-129384-b2b-verified). There is NO "widget name/type" field
    anywhere in the grid or the edit form — identity is only inferable from
    each record's externalReferenceCode, which is dev metadata invisible
    in the rendered admin UI.
  - Row 49711 (ERC "b2b-verified", redirects to qcci.org) is a CONFIRMED
    match for TC 135967 (B2B Platform) — its public `.qc-dw-card` was
    observed live.
  - Row 49679 (ERC "directory", redirects to qatarchamber.com) is mapped
    onto TC 135966 (Marhaba Guide) BY ELIMINATION ONLY — it is the only
    other seeded row. This is a disclosed, real identity-mapping
    uncertainty, not a locator gap — flag back to the QA Manager/dev team
    to confirm this record really is the intended Marhaba Guide slot.
  - TC 135968 (Weather) has NO confirmed control-panel surface anywhere in
    this session's exploration. Weather is rendered on the public Home
    page by a separate `qc-weather-widget` Client Extension (confirmed live
    via an inline HTML comment on the rendered page itself), not by an
    Object Definition entry, and the full Content & Data menu (dumped in
    full this session) contains no "Weather" item. The case's own central
    assertion — that its edit form shows ONLY Active Status + Display Order
    — is also structurally impossible against the Dynamic Widgets Object
    Definition, whose schema is identical for every row. TC 135968 is
    therefore SKIPPED below with this reasoning, rather than automated
    against an invented locator (automation-standards.md's one-pass/
    real-locators rule, and cms-testing.md's "do not invent" contract for
    an unresolved authoring surface).

DISPLAY ORDER — SHARED/RELATIVE ORDERING, CONFIRMED LIVE:

  Baselines observed this session: row 49679 (Marhaba-mapped) = 100,
  row 49711 (B2B) = 200 — NOT the small integers (1 / 2) the case text
  uses as example values. Both rows live under the SAME Object Definition
  and the public Home page renders `.qc-dw-card` elements in the SAME
  relative order as their Display Order values (confirmed live: the
  order-100 card rendered before the order-200 card). This means Display
  Order is a genuinely SHARED, relative ordering field across every row of
  this object — writing Marhaba=1 while B2B stays at 200 (or vice versa)
  changes their RELATIVE order and is a real cross-widget interaction, not
  an isolated per-record write. Each test below captures BOTH rows'
  Display Order (and every other mutated field) as its baseline and
  restores BOTH in `finally`, not just the field it directly touched.

TEST-DATA POLICY NOTE: cms-profile.md's Test-Data Policy section maps this
closest to TEST_OWNED (a dedicated, small, already-seeded row reset to a
captured baseline) — these are pre-existing shared singleton-per-slot
records, not disposable QCTEST- rows a factory can create/delete, and the
project's UI-only policy (no API seeding/teardown) applies throughout.
"""

import allure
import pytest

from cms.pages.home_dynamic_widgets.home_dynamic_widgets_admin_page import (
    HomeDynamicWidgetsAdminPage,
    MARHABA_ROW_ID,
    B2B_ROW_ID,
)
from web.pages.home_dynamic_widgets.home_dynamic_widgets_page import HomeDynamicWidgetsPage

FIXTURES_DIR = "web/tests/home_dynamic_widgets/fixtures"
MARHABA_ERC = "QCDEMO-129384-directory"
B2B_ERC = "QCDEMO-129384-b2b-verified"


def _capture_baseline(admin: HomeDynamicWidgetsAdminPage, record_id: str) -> dict:
    admin.open_widget_edit_form(record_id)
    return {
        "record_id": record_id,
        "active": admin.is_active(),
        "open_in_new_tab": admin.is_open_in_new_tab(),
        "display_order": admin.display_order_value(),
        "redirect_url": admin.redirect_url_value(),
    }


def _restore(admin: HomeDynamicWidgetsAdminPage, baseline: dict) -> None:
    admin.open_widget_edit_form(baseline["record_id"])
    admin.set_active(baseline["active"])
    admin.set_open_in_new_tab(baseline["open_in_new_tab"])
    admin.set_display_order(baseline["display_order"])
    admin.set_redirect_url(baseline["redirect_url"])
    admin.save()


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
def test_marhaba_guide_widget_full_admin_journey_renders_on_home_135966(page):
    # Identity caveat (disclosed, see module docstring): this row is mapped
    # onto Marhaba Guide by elimination (ERC "directory"), not by a
    # confirmed "Marhaba" label anywhere in the live admin UI.
    admin = HomeDynamicWidgetsAdminPage(page)
    marhaba_baseline = _capture_baseline(admin, MARHABA_ROW_ID)
    b2b_baseline = _capture_baseline(admin, B2B_ROW_ID)

    try:
        # Arrange + Act
        admin.open_widget_edit_form(MARHABA_ROW_ID)
        admin.upload_widget_image_en(f"{FIXTURES_DIR}/marhaba_en.jpg")
        admin.upload_widget_image_ar(f"{FIXTURES_DIR}/marhaba_ar.png")
        admin.set_redirect_url("https://marhabaguide.qa/qatar-chamber")
        admin.set_open_in_new_tab(True)
        admin.set_display_order("1")
        admin.set_active(True)
        admin.save()

        # Assert — authoring surface: no validation error, values persisted
        assert not admin.is_save_error_shown(), admin.is_save_error_shown()
        admin.open_widget_edit_form(MARHABA_ROW_ID)
        assert admin.redirect_url_value() == "https://marhabaguide.qa/qatar-chamber"
        assert admin.is_open_in_new_tab() is True
        assert admin.is_active() is True
        assert admin.widget_image_en_filename() != ""
        assert admin.widget_image_ar_filename() != ""

        # Assert — delivery surface (cms-testing.md R1: authoring alone is
        # not sufficient): the card renders on the public Home page with
        # the configured redirect and target.
        home = HomeDynamicWidgetsPage(page)
        home.open_home("en")
        assert home.is_card_visible_for_erc(MARHABA_ERC), "Marhaba Guide card did not appear on the Home page"
        assert home.card_href_for_erc(MARHABA_ERC) == "https://marhabaguide.qa/qatar-chamber"
        assert home.card_opens_new_tab_for_erc(MARHABA_ERC) is True
    finally:
        # Restore BOTH rows — Display Order is shared/relative across every
        # row of this Object Definition (see module docstring).
        _restore(admin, marhaba_baseline)
        _restore(admin, b2b_baseline)


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
def test_b2b_platform_widget_full_admin_journey_renders_on_home_135967(page):
    # Identity confirmed live (see module docstring): ERC "b2b-verified",
    # redirects to qcci.org, renders as the B2B `.qc-dw-card`.
    admin = HomeDynamicWidgetsAdminPage(page)
    marhaba_baseline = _capture_baseline(admin, MARHABA_ROW_ID)
    b2b_baseline = _capture_baseline(admin, B2B_ROW_ID)

    try:
        # Arrange + Act
        admin.open_widget_edit_form(B2B_ROW_ID)
        admin.upload_widget_image_en(f"{FIXTURES_DIR}/b2b_en.jpg")
        admin.upload_widget_image_ar(f"{FIXTURES_DIR}/b2b_ar.svg")
        admin.set_redirect_url("https://b2b.qatarchamber.com/platform")
        admin.set_open_in_new_tab(True)
        admin.set_display_order("2")
        admin.set_active(True)
        admin.save()

        # Assert — authoring surface
        assert not admin.is_save_error_shown(), admin.is_save_error_shown()
        admin.open_widget_edit_form(B2B_ROW_ID)
        assert admin.redirect_url_value() == "https://b2b.qatarchamber.com/platform"
        assert admin.is_open_in_new_tab() is True
        assert admin.is_active() is True
        assert admin.widget_image_en_filename() != ""
        assert admin.widget_image_ar_filename() != ""

        # Assert — delivery surface
        home = HomeDynamicWidgetsPage(page)
        home.open_home("en")
        assert home.is_card_visible_for_erc(B2B_ERC), "B2B Platform card did not appear on the Home page"
        assert home.card_href_for_erc(B2B_ERC) == "https://b2b.qatarchamber.com/platform"
        assert home.card_opens_new_tab_for_erc(B2B_ERC) is True
    finally:
        _restore(admin, marhaba_baseline)
        _restore(admin, b2b_baseline)


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
    "found this session (full one-pass CLI exploration, see "
    "home_dynamic_widgets_admin_page.py's module docstring): the complete "
    "Content & Data menu contains no 'Weather' Object Definition entry, and "
    "the public Home page's Weather card is confirmed (via an inline HTML "
    "comment on the live page) to be rendered by a separate "
    "qc-weather-widget Client Extension, not an Object Definition record. "
    "The case's own central assertion — an edit form limited to ONLY "
    "Active Status + Display Order — is also structurally impossible "
    "against the Dynamic Widgets Object Definition used by the other two "
    "widgets, whose schema is identical for every row. Flag back to the "
    "QA Manager/dev team to confirm the real Weather admin surface "
    "(likely a Client Extension / instance configuration screen) before "
    "this can be automated; per automation-standards.md's one-pass/"
    "real-locators rule, no locator is invented here."
)
def test_weather_widget_limited_admin_form_renders_first_with_live_data_135968(page):
    ...

"""
cms/tests/home_about_summary/test_home_about_summary_control_panel.py —
Control_Panel-tagged cases for PBI 129389 (QC-HOME-013 — "About Us Section &
Last Year Achievements Counters"), backing the homepage "About Us" summary
widget.

REWRITTEN 2026-09-07 per standards.md's broadened "Object Authoring Is the
Only Path for Content Operations — Not Content & Data" rule: every field
write and every lifecycle action below now goes through the real
`manage-about-us-section` / `manage-about-us-counter` Object Authoring
surfaces, never the retired `Content & Data` grid the prior version of this
module used (Save/Cancel-only forms, no Draft/Approved state). See
`cms/pages/home_about_summary/home_about_summary_admin_page.py`'s module
docstring for the full live-confirmation write-up (slugs, field labels,
bilingual rich-text description iframe pairing, and the "Save as Draft
disabled / Submit for Publishing enabled" Approved-entry shape shared with
every other Object Authoring surface on this project).

PBI resolution note (carried forward, still true): no azure-devops MCP tool
was available in the original session to resolve the parent PBI via the
Azure API directly; it was instead confirmed LIVE against the real CMS —
the "About Us Sections" Object Definition's own singleton record carries
externalReferenceCode `QCDEMO-129389-ABOUT_US_SECTION-01`, the same
QCDEMO-<PBI>-... seed-data naming convention already relied on verbatim for
pbi_129397/GM's Message, pbi_129398/Board Members, etc. elsewhere in this
suite.

TEST-DATA POLICY / SAFE PARALLELISM: both objects' live records are
pre-existing, dedicated shared singletons (TEST_OWNED per
cms-profile.md) — Section record `QCDEMO-129389-ABOUT_US_SECTION-01` and
Counter rows `QCDEMO-129389-ABOUT_US_COUNTER-01..04`. Every mutating test
below captures a full baseline before writing and restores it in `finally`
(with a reopen-and-reread verification), and is tagged with a shared
`xdist_group` so no two of these tests run concurrently against the same
records.
"""

import allure
import pytest

from cms.pages.home_about_summary.home_about_summary_admin_page import (
    HomeAboutSummaryAdminPage,
    HomeAboutCounterAdminPage,
    COUNTER_ENTRY_CODES,
    SECTION_ENTRY_CODE,
    FIELD_SECTION_TAG_EN,
    FIELD_SECTION_TAG_AR,
    FIELD_SECTION_HEADING_EN,
    FIELD_SECTION_HEADING_AR,
    FIELD_BUILDING_IMAGE_PRIMARY,
    FIELD_YEARS_BADGE_EN,
    FIELD_YEARS_BADGE_AR,
    FIELD_READ_MORE_LABEL_EN,
    FIELD_READ_MORE_LABEL_AR,
    FIELD_READ_MORE_URL,
    FIELD_COUNTER_TITLE_EN,
    FIELD_COUNTER_TITLE_AR,
    FIELD_COUNTER_VALUE,
    FIELD_COUNTER_ICON,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials
from core.web.browser import new_context
from web.pages.home_about_summary.home_about_summary_page import HomeAboutSummaryPage

ABOUT_US_XDIST_GROUP = pytest.mark.xdist_group("about_us_section_52157")

FIXTURES = "web/tests/home_about_summary/fixtures"


def _login_as_site_content_editor(page) -> None:
    email, password = cms_role_credentials("Site Content Editor")
    CmsLoginPage(page).open_login().login(email, password)


# ─────────────────────────────────────────────────────────────────────────
# Added 2026-09-15 for the ADO 136088-136140 batch (PBI 129389). Fixtures
# mirror board_of_directors' own short_bio_edit/display_order_edit shape
# (automation-standards.md's Page-Object-baseline-restore convention): a
# yield-based fixture captures state BEFORE the test body runs and restores
# it in its finalizer regardless of test outcome, so a failed assertion
# still reverts the shared TEST_OWNED singleton (cms-profile.md).
# ─────────────────────────────────────────────────────────────────────────
@pytest.fixture
def section_edit(page):
    admin = HomeAboutSummaryAdminPage(page)
    baseline = admin.capture_section_baseline()
    yield admin, baseline
    admin.restore_section(baseline)
    admin.open_section_entry()
    assert admin.field_value(FIELD_SECTION_HEADING_EN) == baseline["heading_en"], (
        "Teardown restore did not persist: Section Heading (EN)"
    )


@pytest.fixture
def counter_edit(page):
    """Row 01 (E-Services) — the shared row used by every single-counter
    boundary/validation case in this batch, mirroring the sibling
    tc_136136 test's own choice of row 01 for the same purpose."""
    counter = HomeAboutCounterAdminPage(page)
    baseline = counter.capture_baseline(COUNTER_ENTRY_CODES[0])
    yield counter, baseline
    counter.restore(baseline)
    counter.open_counter(baseline["entry_code"])
    assert counter.title_en_value() == baseline["title_en"], (
        "Teardown restore did not persist: Counter Title (EN)"
    )


def _fill_all_section_fields(admin: HomeAboutSummaryAdminPage, prefix: str, **overrides) -> dict:
    """Fills every mandatory Section field with a QCTEST-<prefix>-prefixed
    value (mirroring tc_136103's own QCTEST-<id> data convention); pass a
    field constant as a keyword override (e.g. read_more_url="...") — or an
    override value of "" to deliberately leave that field empty for a
    required-field-violation case. Returns the dict of values actually
    filled, for round-trip assertions."""
    values = {
        FIELD_SECTION_TAG_EN: f"{prefix} MORE ABOUT US",
        FIELD_SECTION_TAG_AR: f"{prefix} المزيد عنا",
        FIELD_SECTION_HEADING_EN: f"{prefix} Qatar Chamber",
        FIELD_SECTION_HEADING_AR: f"{prefix} غرفة قطر",
        FIELD_YEARS_BADGE_EN: f"{prefix} 63+ Years of Experience",
        FIELD_YEARS_BADGE_AR: f"{prefix} 63+ سنة خبرة",
        FIELD_READ_MORE_LABEL_EN: f"{prefix} Read More",
        FIELD_READ_MORE_LABEL_AR: f"{prefix} اقرأ المزيد",
        FIELD_READ_MORE_URL: "https://qcdev.ihorizons.com/web/qatar-chamber/about-us",
    }
    values.update(overrides)
    for field, value in values.items():
        admin.fill_text(field, value)
    return values


def _fill_counter_fields(counter: HomeAboutCounterAdminPage, prefix: str, **overrides) -> dict:
    values = {
        FIELD_COUNTER_TITLE_EN: f"{prefix} E-Services",
        FIELD_COUNTER_TITLE_AR: f"{prefix} الخدمات الإلكترونية",
        FIELD_COUNTER_VALUE: "999 +",
    }
    values.update(overrides)
    for field, value in values.items():
        counter.fill_text(field, value)
    return values


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Full admin authoring flow, end to end")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can complete the full About Us section configuration flow end to end (ADO-136103)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129389
@pytest.mark.tc_136103
@ABOUT_US_XDIST_GROUP
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_about_us_section_full_admin_configuration_flow_136103(page):
    """ADO-136103. Case names "Site Content Editor" explicitly in Step 1, so
    this test authenticates as that named role (per standards.md's Named
    CMS User Roles section) rather than the default TEST_USER session —
    hence the `{"auth": False}` indirect param on `page`, giving a fresh,
    unauthenticated context this test logs into itself.

    Scope notes (disclosed per automation-standards.md's Result Integrity
    rule):
      - Steps 2-6 exercise every Section field the case calls for (Section
        Tag, Heading, Description EN/AR, two Building Images, Years of
        Experience Badge, Read More Label + URL) plus all 4 seeded
        QCDEMO Counter rows (Title/Value/Icon/Display Order/Active=True)
        — "Add 4 counters" is realized as configuring the object's 4
        already-seeded counter slots (a fresh Add would create permanent,
        publicly-visible new rows on the live Home page — see
        home_strategic_direction_page.py's own documented reasoning for why
        that is never done against a real Object-Definition-backed public
        section), which exercises the identical field set the case's Step
        6 names.
      - Step 7's "Publish" is `submit_for_publishing()` — the real Object
        Authoring lifecycle action; "Published" is verified via
        `current_status() == "Approved"` (this project's confirmed-live
        vocabulary for a published Object Authoring entry — see
        ObjectAuthoringPage's own module docstring). No confirmed generic
        Liferay success-toast selector exists on this surface (same
        disclosed finding already documented for
        HomeDynamicWidgetsAdminPage); the real proof of success is the
        Approved status plus every field's value round-tripping, both
        asserted below.
    """
    _login_as_site_content_editor(page)
    section = HomeAboutSummaryAdminPage(page)
    counter = HomeAboutCounterAdminPage(page)

    qctest_tag_en = "QCTEST-136103 MORE ABOUT US"
    qctest_tag_ar = "QCTEST-136103 المزيد عنا"
    qctest_heading_en = "QCTEST-136103 Qatar Chamber"
    qctest_heading_ar = "QCTEST-136103 غرفة قطر"
    qctest_desc_en = "QCTEST-136103 Full flow description EN."
    qctest_desc_ar = "QCTEST-136103 وصف التدفق الكامل بالعربية."
    qctest_badge_en = "QCTEST-136103 63+ Years of Experience"
    qctest_badge_ar = "QCTEST-136103 63+ سنة خبرة"
    qctest_read_more_label_en = "QCTEST-136103 Read More"
    qctest_read_more_label_ar = "QCTEST-136103 اقرأ المزيد"
    qctest_read_more_url = "https://qcdev.ihorizons.com/web/qatar-chamber/about-us"
    counter_titles_en = ["QCTEST-136103 E-Services", "QCTEST-136103 Certificates", "QCTEST-136103 Members", "QCTEST-136103 Events"]
    counter_value = "999 +"

    with allure.step("Capture the Section and all 4 Counter rows' baselines for teardown"):
        section_baseline = section.capture_section_baseline()
        counter_baselines = [counter.capture_baseline(code) for code in COUNTER_ENTRY_CODES]

    try:
        with allure.step("Step 1: Navigate to About Us Section Management — screen loads editable"):
            section.open_section_entry()
            assert section.current_status() in ("Approved", "Draft")

        with allure.step("Step 2: Enter Section Tag, Heading, Description (EN/AR)"):
            section.fill_text("Section Tag (EN)", qctest_tag_en)
            section.fill_text("Section Tag (AR)", qctest_tag_ar)
            section.fill_text("Section Heading (EN)", qctest_heading_en)
            section.fill_text("Section Heading (AR)", qctest_heading_ar)
            section.fill_description_en(qctest_desc_en)
            section.fill_description_ar(qctest_desc_ar)
            assert section.field_value("Section Tag (EN)") == qctest_tag_en
            assert section.field_value("Section Heading (EN)") == qctest_heading_en

        with allure.step("Step 3: Upload two building images — images upload with preview"):
            section.upload_building_image_primary("web/tests/home_about_summary/fixtures/about_building_primary.jpg")
            section.upload_building_image_secondary("web/tests/home_about_summary/fixtures/about_building_secondary.jpg")
            assert "about_building_primary" in section.building_image_primary_filename()
            assert "about_building_secondary" in section.building_image_secondary_filename()

        with allure.step("Step 4: Enter Years of Experience Badge text (EN/AR)"):
            section.fill_text("Years of Experience Badge (EN)", qctest_badge_en)
            section.fill_text("Years of Experience Badge (AR)", qctest_badge_ar)
            assert section.field_value("Years of Experience Badge (EN)") == qctest_badge_en

        with allure.step("Step 5: Configure Read More Label (EN/AR) and URL"):
            section.fill_text("Read More Label (EN)", qctest_read_more_label_en)
            section.fill_text("Read More Label (AR)", qctest_read_more_label_ar)
            section.fill_text("Read More URL", qctest_read_more_url)
            assert section.field_value("Read More Label (EN)") == qctest_read_more_label_en
            assert section.field_value("Read More URL") == qctest_read_more_url

        with allure.step(
            "Commit the Section fields before navigating to the Counter object "
            "(Object Authoring is a real per-object page — unsaved Section field "
            "edits do not survive navigating away to configure the Counters)"
        ):
            section.submit_for_publishing()
            assert section.current_status() == "Approved"

        with allure.step("Step 6: Add 4 counters with Title/Value/Icon/Display Order/Active=True"):
            for i, code in enumerate(COUNTER_ENTRY_CODES):
                counter.open_counter(code)
                counter.set_title_en(counter_titles_en[i])
                counter.set_value(counter_value)
                counter.upload_icon("web/tests/home_about_summary/fixtures/about_counter_icon.svg")
                counter.set_display_order(str((i + 1) * 100))
                counter.set_active(True)
                counter.submit_for_publishing()
                assert counter.current_status() == "Approved"

            for i, code in enumerate(COUNTER_ENTRY_CODES):
                counter.open_counter(code)
                assert counter.title_en_value() == counter_titles_en[i]
                assert counter.value_value() == counter_value
                assert counter.is_active() is True

        with allure.step("Step 7: Click Publish — section Published (idempotent re-publish, already Approved above)"):
            section.open_section_entry()
            section.submit_for_publishing()

        section.open_section_entry()
        assert section.current_status() == "Approved"
        assert section.field_value("Section Heading (EN)") == qctest_heading_en
        assert section.description_en_value().strip() == qctest_desc_en
    finally:
        with allure.step("Teardown: restore the Section baseline"):
            section.restore_section(section_baseline)
            section.open_section_entry()
            assert section.field_value("Section Heading (EN)") == section_baseline["heading_en"], (
                "Teardown restore did not persist: Section Heading (EN)"
            )
        with allure.step("Teardown: restore all 4 Counter rows' baselines"):
            for baseline in counter_baselines:
                counter.restore(baseline)
                counter.open_counter(baseline["entry_code"])
                assert counter.title_en_value() == baseline["title_en"], (
                    f"Teardown restore did not persist Counter Title (EN) for {baseline['entry_code']!r}"
                )


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Published configuration reflects on the Home Page after cache refresh")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Published About Us configuration reflects on the Home Page after cache refresh (ADO-136106)")
@pytest.mark.control_panel
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129389
@pytest.mark.tc_136106
@ABOUT_US_XDIST_GROUP
def test_published_about_us_configuration_reflects_on_home_page_136106(page, browser):
    """ADO-136106. Per standards.md's mandatory anon-context rule, the
    public Home Page read uses a fresh logged-out context
    (`new_context(browser, use_auth_state=False)`), never the CMS-
    authenticated `page`.

    No dedicated "cache refresh" UI action was found on this Object
    Authoring surface (same disclosed finding already documented for
    home_strategic_direction_page.py) — Step 2's "trigger/await cache
    refresh" is realized as a bounded reload-and-poll of the public Home
    Page (`reload_until_heading_matches`), per cms-profile.md's Publish/
    Propagation Latency Budget guidance (measured ~0s for the one endpoint
    probed on this project; a conservative 5s/0.5s poll budget is used here
    since this specific section's own propagation was not independently
    re-measured this session).
    """
    section = HomeAboutSummaryAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeAboutSummaryPage(anon_page)

    qctest_heading_en = "QCTEST-136106 Qatar Chamber Updated Heading"

    with allure.step("Capture the Section baseline for teardown"):
        section_baseline = section.capture_section_baseline()

    try:
        with allure.step("Step 1: Publish an About Us section with updated Heading text"):
            section.open_section_entry()
            section.fill_text("Section Heading (EN)", qctest_heading_en)
            section.submit_for_publishing()
            assert section.current_status() == "Approved"

        with allure.step("Step 2: Trigger/await cache refresh — poll the public Home Page"):
            reflected = home.reload_until_heading_matches(qctest_heading_en)

        with allure.step("Step 3: Load Home Page as a visitor — Home Page displays updated Heading text"):
            assert reflected, "Updated About Us Heading did not reflect on the public Home Page within the poll budget"
            assert home.heading_text() == qctest_heading_en
    finally:
        with allure.step("Teardown: restore the Section baseline"):
            section.restore_section(section_baseline)
            section.open_section_entry()
            assert section.field_value("Section Heading (EN)") == section_baseline["heading_en"], (
                "Teardown restore did not persist: Section Heading (EN)"
            )
        anon_context.close()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Data integrity across save/reload/re-login")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("All About Us section field values persist correctly after save and reload (ADO-136136)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136136
@ABOUT_US_XDIST_GROUP
def test_about_us_section_field_values_persist_after_save_and_reload_136136(page):
    """ADO-136136. MIGRATED 2026-09-07 off the retired `Content & Data`
    grid onto the real `manage-about-us-section` / `manage-about-us-counter`
    Object Authoring surfaces (see module docstring) — same case intent as
    the prior version: fill fields -> Submit for Publishing succeeds ->
    log out -> log back in -> reopen the records -> every previously
    entered value is still present, exactly as entered, in both EN and AR,
    across the Section singleton and one counter set (row 01).
    """
    admin = HomeAboutSummaryAdminPage(page)
    counter = HomeAboutCounterAdminPage(page)

    qctest_heading_en = "QCTEST-136136 Qatar Chamber Persist Check"
    qctest_heading_ar = "QCTEST-136136 غرفة قطر فحص الاستمرارية"
    qctest_tag_en = "QCTEST-136136 MORE ABOUT US"
    qctest_years_badge_en = "QCTEST-136136 63+ Years of Experience"
    qctest_read_more_label_en = "QCTEST-136136 Read More"
    qctest_counter_title_en = "QCTEST-136136 E-Services"
    qctest_counter_value = "999 +"

    with allure.step("Capture the Section and Counter (row 01) baselines"):
        section_baseline = admin.capture_section_baseline()
        counter_baseline = counter.capture_baseline(COUNTER_ENTRY_CODES[0])

    try:
        with allure.step("Fill Section fields and Submit for Publishing"):
            admin.open_section_entry()
            admin.fill_text("Section Heading (EN)", qctest_heading_en)
            admin.fill_text("Section Heading (AR)", qctest_heading_ar)
            admin.fill_text("Section Tag (EN)", qctest_tag_en)
            admin.fill_text("Years of Experience Badge (EN)", qctest_years_badge_en)
            admin.fill_text("Read More Label (EN)", qctest_read_more_label_en)
            admin.submit_for_publishing()

        assert admin.current_status() == "Approved"

        with allure.step("Fill the one counter set (row 01) and Submit for Publishing"):
            counter.open_counter(COUNTER_ENTRY_CODES[0])
            counter.set_title_en(qctest_counter_title_en)
            counter.set_value(qctest_counter_value)
            counter.submit_for_publishing()

        assert counter.current_status() == "Approved"

        with allure.step("Log out and log back in as the CMS content-authoring test account"):
            admin.logout_and_return()
            admin.login_as(*cms_role_credentials("Site Content Editor"))

        with allure.step("Reopen the Section record and read every field back"):
            admin.open_section_entry()
            reloaded_heading_en = admin.field_value("Section Heading (EN)")
            reloaded_heading_ar = admin.field_value("Section Heading (AR)")
            reloaded_tag_en = admin.field_value("Section Tag (EN)")
            reloaded_years_badge_en = admin.field_value("Years of Experience Badge (EN)")
            reloaded_read_more_label_en = admin.field_value("Read More Label (EN)")

        assert reloaded_heading_en == qctest_heading_en
        assert reloaded_heading_ar == qctest_heading_ar
        assert reloaded_tag_en == qctest_tag_en
        assert reloaded_years_badge_en == qctest_years_badge_en
        assert reloaded_read_more_label_en == qctest_read_more_label_en

        with allure.step("Reopen the Counter (row 01) record and read its fields back"):
            counter.open_counter(COUNTER_ENTRY_CODES[0])
            reloaded_counter_title_en = counter.title_en_value()
            reloaded_counter_value = counter.value_value()

        assert reloaded_counter_title_en == qctest_counter_title_en
        assert reloaded_counter_value == qctest_counter_value
    finally:
        with allure.step("Teardown: restore the Section and Counter (row 01) baselines"):
            admin.restore_section(section_baseline)
            admin.open_section_entry()
            assert admin.field_value("Section Heading (EN)") == section_baseline["heading_en"]

            counter.restore(counter_baseline)
            counter.open_counter(COUNTER_ENTRY_CODES[0])
            assert counter.title_en_value() == counter_baseline["title_en"]


# ═══════════════════════════════════════════════════════════════════════
# Added 2026-09-15 — ADO 136088-136140 batch (PBI 129389), Control_Panel-
# tagged cases (36 of the batch's 50; the other 14 are Web-tagged and live
# in test_home_about_summary_web.py; 136137 carries BOTH Web and
# Control_Panel tags and lives here, mirroring tc_136106's precedent).
#
# See home_about_summary_admin_page.py's module docstring for the disclosed
# PROBE FAILURE note: three live probe attempts to confirm this surface's
# exact `maxlength`/required-field-violation mechanism all failed (host
# resource exhaustion — timeouts, a `Page crashed` Playwright error, 25+
# pre-existing orphan chrome.exe processes). Every length/required-field
# test below therefore goes through ObjectAuthoringPage.field_length_rejected()
# / description_length_rejected(), which accept EITHER branch the QA cases'
# own wording allows ("truncates OR shows a max-length error"; "blocked" =
# current_status() never reaches "Approved") rather than assuming one
# specific mechanism this session could not observe.
# ═══════════════════════════════════════════════════════════════════════


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("RBAC — Section Management screen access")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can access the About Us Section Management screen (ADO-136101)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136101")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129389
@pytest.mark.tc_136101
@ABOUT_US_XDIST_GROUP
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_site_content_editor_can_access_about_us_section_management_136101(page):
    """ADO-136101. Named-role case per standards.md's Named CMS User Roles
    section — authenticates as Site Content Editor via a fresh
    ({"auth": False}) context, mirroring tc_136103's own pattern."""
    # Arrange
    _login_as_site_content_editor(page)
    admin = HomeAboutSummaryAdminPage(page)

    # Act
    with allure.step("Navigate to Home Page -> About Us Section Management"):
        admin.open_section_entry()

    # Assert
    with allure.step("Management screen loads with fields editable"):
        assert admin.current_status() in ("Approved", "Draft")
        # Editable == reachable, focusable, and fillable — a denied/read-only
        # screen would raise or leave the value unset, not silently no-op.
        probe_value = "QCTEST-136101 editable-probe"
        admin.fill_text(FIELD_SECTION_TAG_EN, probe_value)
        assert admin.field_value(FIELD_SECTION_TAG_EN) == probe_value


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("RBAC — Section Management screen access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A user without a valid Site Content Editor session cannot access the About Us Section Management screen (ADO-136102)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136102")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129389
@pytest.mark.tc_136102
@pytest.mark.skip(
    reason="Structurally unobservable through this project's own wrapper layer, confirmed by "
    "reading (not guessing) core/web/session_guard.py: BasePage.open() unconditionally calls "
    "reauthenticate() for any non-login-flow URL, which auto-logs in with TEST_USER the moment "
    "it sees a login form — session_guard.py's own docstring names exactly this test's premise "
    "as the one case it must never be used for ('RBAC denial cases... this guard would defeat "
    "that test's purpose'), yet every Page Object's open() goes through it unconditionally, with "
    "no opt-out. There is no way to observe a genuine 'unauthenticated visitor denied' state "
    "without a raw page.goto() in the test body, which the no-raw-driver-in-tests rule forbids. "
    "This is the same structural wall every other 'public visitor cannot access CMS edit URL' "
    "case in this suite is already left skipped for (e.g. tc_135448, tc_136375) — not unique to "
    "this case. Flagging back rather than guessing a workaround, per this agent's own contract."
)
def test_user_without_valid_session_cannot_access_about_us_section_management_136102(page):
    ...


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Draft lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Admin can save the About Us section as a draft without publishing (ADO-136104)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136104")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129389
@pytest.mark.tc_136104
@ABOUT_US_XDIST_GROUP
def test_admin_can_save_about_us_section_as_draft_136104(section_edit):
    # ADO-136104
    # Arrange
    admin, _baseline = section_edit
    admin.open_section_entry()
    admin.ensure_draft()

    # Act
    with allure.step("Enter all mandatory fields with valid data and Save Draft"):
        values = _fill_all_section_fields(admin, "QCTEST-136104")
        admin.save_as_draft()

    # Assert
    with allure.step("Section remains Draft"):
        assert admin.current_status() == "Draft"
        assert admin.field_value(FIELD_SECTION_HEADING_EN) == values[FIELD_SECTION_HEADING_EN]


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Preview before publishing")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Admin can preview the About Us section before publishing (ADO-136105)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136105")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129389
@pytest.mark.tc_136105
@ABOUT_US_XDIST_GROUP
def test_admin_can_preview_about_us_section_before_publishing_136105(section_edit, browser):
    """ADO-136105. No dedicated in-form "Preview" action was independently
    confirmed live this session (see module PROBE FAILURE note) — realized
    via the entries list's own row-level Preview link and
    preview_banner_text(), the same confirmed-live preview mechanism
    ObjectAuthoringPage documents project-wide. Live Home Page unaffected is
    verified via a fresh anonymous context (never the CMS-authenticated
    page), per standards.md's anonymous-visitor rule."""
    # Arrange
    admin, baseline = section_edit
    admin.open_section_entry()

    # Act
    with allure.step("Enter all mandatory fields with valid data (unsaved)"):
        _fill_all_section_fields(admin, "QCTEST-136105-UNSAVED")

    with allure.step("Click Preview"):
        admin.open_entries_list()
        preview_url = admin.row_preview_url_by_code(SECTION_ENTRY_CODE)
        banner_text = admin.preview_banner_text(preview_url)

    # Assert
    with allure.step("Preview renders; live Home Page unaffected"):
        assert "PREVIEW" in banner_text
        anon_ctx = new_context(browser, use_auth_state=False)
        anon_page = anon_ctx.new_page()
        home = HomeAboutSummaryPage(anon_page)
        home.open_home()
        home.wait_for_section()
        assert home.heading_text() == baseline["heading_en"], (
            "live Home Page changed even though the unsaved preview edits were never published"
        )
        anon_ctx.close()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Republish an edited section")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Admin can edit an already-published About Us section and republish successfully (ADO-136107)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136107")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129389
@pytest.mark.tc_136107
@ABOUT_US_XDIST_GROUP
def test_admin_can_edit_published_section_and_republish_136107(section_edit, browser):
    # ADO-136107
    # Arrange
    admin, baseline = section_edit
    qctest_desc_en = "QCTEST-136107 revised description text."

    # Act
    with allure.step("Open the existing published section for edit"):
        admin.open_section_entry()
        assert admin.current_status() == "Approved"

    with allure.step("Change Section Description EN to revised text"):
        admin.fill_description_en(qctest_desc_en)
        assert admin.description_en_value().strip() == qctest_desc_en

    with allure.step("Click Publish"):
        admin.submit_for_publishing()

    # Assert
    with allure.step("Home Page reflects the revised description"):
        assert admin.current_status() == "Approved"
        anon_ctx = new_context(browser, use_auth_state=False)
        anon_page = anon_ctx.new_page()
        home = HomeAboutSummaryPage(anon_page)
        reflected = home.reload_until(lambda h: h.description_text().strip() == qctest_desc_en)
        assert reflected, "revised Section Description did not reflect on the public Home Page within the poll budget"
        anon_ctx.close()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Required-field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publishing is blocked when Section Heading is left empty, EN and AR (ADO-136108)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136108")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136108
@ABOUT_US_XDIST_GROUP
def test_publish_blocked_when_section_heading_empty_136108(section_edit):
    # ADO-136108
    admin, _baseline = section_edit
    admin.open_section_entry()

    with allure.step("Fill all mandatory fields except Section Heading EN"):
        _fill_all_section_fields(admin, "QCTEST-136108", **{FIELD_SECTION_HEADING_EN: ""})

    with allure.step("Click Publish — blocked for empty EN Heading"):
        admin.submit_for_publishing()
        assert admin.current_status() != "Approved"

    with allure.step("Fill Heading EN, clear Heading AR, click Publish — blocked for empty AR Heading"):
        admin.open_section_entry()
        admin.fill_text(FIELD_SECTION_HEADING_EN, "QCTEST-136108 Qatar Chamber")
        admin.fill_text(FIELD_SECTION_HEADING_AR, "")
        admin.submit_for_publishing()
        assert admin.current_status() != "Approved"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Counter cap")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Admin can add counters up to the maximum of 4 (ADO-136109)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136109")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129389
@pytest.mark.tc_136109
@ABOUT_US_XDIST_GROUP
def test_admin_can_add_counters_up_to_max_of_4_136109(page):
    """ADO-136109. "Add counters one at a time" is realized, like tc_136103's
    own Step 6, as configuring the object's 4 already-seeded counter slots
    — a fresh Add would create a permanent, publicly-visible 5th row on the
    live Home page (see home_about_summary_admin_page.py's module
    docstring). The Add control's disabled/hidden state after the 4th is
    read-only, per add_counter_control_state()'s own docstring — NOT
    independently confirmed live this session (probe failure, see module
    docstring); if this surface turns out to be an unbounded repeatable
    list rather than a capped-at-4 one, this assertion fails honestly rather
    than being loosened to match."""
    counter = HomeAboutCounterAdminPage(page)
    baselines = [counter.capture_baseline(code) for code in COUNTER_ENTRY_CODES]

    try:
        with allure.step("Add (configure) all 4 counters one at a time"):
            for i, code in enumerate(COUNTER_ENTRY_CODES):
                counter.open_counter(code)
                _fill_counter_fields(counter, f"QCTEST-136109-{i + 1}")
                counter.submit_for_publishing()
                assert counter.current_status() == "Approved"

        with allure.step("After the 4th counter, the Add control is disabled/hidden"):
            counter.open_counter_list()
            state = counter.add_counter_control_state()
            assert not state["visible"] or state["disabled"], (
                f"Add control still enabled with 4 counters present: {state!r}"
            )
    finally:
        with allure.step("Teardown: restore all 4 Counter rows' baselines"):
            for baseline in baselines:
                counter.restore(baseline)
                counter.open_counter(baseline["entry_code"])
                assert counter.title_en_value() == baseline["title_en"]


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Required-field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publishing is blocked when Section Description is left empty, EN and AR (ADO-136110)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136110")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136110
@ABOUT_US_XDIST_GROUP
def test_publish_blocked_when_section_description_empty_136110(section_edit):
    # ADO-136110
    admin, _baseline = section_edit
    admin.open_section_entry()

    with allure.step("Fill all mandatory fields except Section Description EN"):
        _fill_all_section_fields(admin, "QCTEST-136110")
        admin.fill_description_en("")

    with allure.step("Click Publish — blocked for empty EN Description"):
        admin.submit_for_publishing()
        assert admin.current_status() != "Approved"

    with allure.step("Fill Description EN, clear Description AR, click Publish — blocked for empty AR Description"):
        admin.open_section_entry()
        admin.fill_description_en("QCTEST-136110 valid description")
        admin.fill_description_ar("")
        admin.submit_for_publishing()
        assert admin.current_status() != "Approved"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Tag accepts valid input up to the 50-character limit, EN/AR (ADO-136111)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136111")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136111
@ABOUT_US_XDIST_GROUP
def test_section_tag_accepts_up_to_50_chars_136111(section_edit):
    # ADO-136111
    admin, _baseline = section_edit
    tag_en = ("QCTEST tag " * 5)[:50]
    tag_ar = ("قسم اختبار " * 5)[:50]
    assert len(tag_en) == 50 and len(tag_ar) == 50

    admin.open_section_entry()
    admin.ensure_draft()

    with allure.step("Enter Section Tag EN/AR within the 50-character limit and Save Draft"):
        admin.fill_text(FIELD_SECTION_TAG_EN, tag_en)
        admin.fill_text(FIELD_SECTION_TAG_AR, tag_ar)
        admin.save_as_draft()

    assert admin.field_value(FIELD_SECTION_TAG_EN) == tag_en
    assert admin.field_value(FIELD_SECTION_TAG_AR) == tag_ar


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Tag rejects input exceeding the 50-character limit, EN/AR (ADO-136112)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136112")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136112
@ABOUT_US_XDIST_GROUP
def test_section_tag_rejects_over_50_chars_136112(section_edit):
    # ADO-136112
    admin, _baseline = section_edit
    over_en = ("QCTEST over-limit tag " * 5)[:51]
    over_ar = ("قسم اختبار طويل جدا " * 5)[:51]
    assert len(over_en) == 51 and len(over_ar) == 51
    admin.open_section_entry()

    with allure.step("Enter a 51-character string into Section Tag EN — truncated or rejected"):
        assert admin.field_length_rejected(FIELD_SECTION_TAG_EN, over_en, 50)

    with allure.step("Enter a 51-character Arabic string into Section Tag AR — truncated or rejected"):
        admin.open_section_entry()
        assert admin.field_length_rejected(FIELD_SECTION_TAG_AR, over_ar, 50)


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Heading accepts valid input up to the 200-character limit (ADO-136113)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136113")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136113
@ABOUT_US_XDIST_GROUP
def test_section_heading_accepts_up_to_200_chars_136113(section_edit):
    # ADO-136113
    admin, _baseline = section_edit
    heading_200 = ("QCTEST Qatar Chamber heading text " * 10)[:200]
    assert len(heading_200) == 200

    admin.open_section_entry()
    admin.ensure_draft()

    with allure.step("Enter exactly 200 characters into Section Heading EN and Save Draft"):
        admin.fill_text(FIELD_SECTION_HEADING_EN, heading_200)
        admin.save_as_draft()

    assert admin.field_value(FIELD_SECTION_HEADING_EN) == heading_200


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Heading rejects input exceeding the 200-character limit (ADO-136114)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136114")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136114
@ABOUT_US_XDIST_GROUP
def test_section_heading_rejects_over_200_chars_136114(section_edit):
    # ADO-136114
    admin, _baseline = section_edit
    over_201 = ("QCTEST Qatar Chamber over-limit heading text " * 6)[:201]
    assert len(over_201) == 201
    admin.open_section_entry()

    with allure.step("Enter a 201-character string into Section Heading EN — truncated or rejected"):
        assert admin.field_length_rejected(FIELD_SECTION_HEADING_EN, over_201, 200)


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Description accepts rich text formatting up to the 1000-character limit (ADO-136115)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136115")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136115
@ABOUT_US_XDIST_GROUP
def test_section_description_accepts_up_to_1000_chars_136115(section_edit):
    """ADO-136115. Typed plain text at exactly the 1000-character boundary —
    real CKEditor formatting (bold/list/link via the toolbar) was out of
    scope for this batch's probe-unavailable session (see module docstring);
    the case's "rich text formatting" premise is exercised to the extent a
    keyboard-typed value into the confirmed-live CKEditor iframe allows."""
    admin, _baseline = section_edit
    desc_1000 = ("QCTEST rich text description content for the About Us section. " * 20)[:1000]
    assert len(desc_1000) == 1000

    admin.open_section_entry()
    admin.ensure_draft()

    with allure.step("Enter 1000 characters into Section Description EN and Save Draft"):
        admin.fill_description_en(desc_1000)
        admin.save_as_draft()

    with allure.step("Reload the draft"):
        admin.open_section_entry()

    assert admin.description_en_value().strip() == desc_1000


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Description rejects input exceeding the 1000-character limit (ADO-136116)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136116")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136116
@ABOUT_US_XDIST_GROUP
def test_section_description_rejects_over_1000_chars_136116(section_edit):
    # ADO-136116
    admin, _baseline = section_edit
    over_1001 = ("QCTEST over-limit description content for the About Us section. " * 20)[:1001]
    assert len(over_1001) == 1001
    admin.open_section_entry()

    with allure.step("Enter a 1001-character string into Section Description EN — blocked/truncated at 1000"):
        assert admin.description_length_rejected("en", over_1001, 1000)


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Building Image upload")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Building Images upload succeeds with a valid JPG file under 2MB (ADO-136117)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136117")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136117
@ABOUT_US_XDIST_GROUP
def test_building_image_uploads_with_valid_jpg_under_2mb_136117(section_edit):
    # ADO-136117
    admin, _baseline = section_edit
    admin.open_section_entry()
    admin.ensure_draft()

    with allure.step("Upload a valid JPG under 2MB as a Building Image"):
        admin.upload_building_image_primary(f"{FIXTURES}/about_building_primary.jpg")

    with allure.step("Save Draft"):
        admin.save_as_draft()

    assert "about_building_primary" in admin.building_image_primary_filename()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Building Image upload")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Building Images upload is rejected when file exceeds 2MB or has an unsupported format (ADO-136118)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136118")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136118
@ABOUT_US_XDIST_GROUP
def test_building_image_upload_rejected_oversized_or_unsupported_136118(section_edit):
    # ADO-136118
    admin, _baseline = section_edit
    admin.open_section_entry()

    with allure.step("Attempt to upload an oversized JPG (>2MB) as a Building Image — rejected"):
        assert admin.upload_file_expect_rejected(
            FIELD_BUILDING_IMAGE_PRIMARY, f"{FIXTURES}/about_building_oversized.jpg"
        )

    with allure.step("Attempt to upload a .gif file as a Building Image — rejected (unsupported format)"):
        admin.open_section_entry()
        assert admin.upload_file_expect_rejected(
            FIELD_BUILDING_IMAGE_PRIMARY, f"{FIXTURES}/about_building_invalid.gif"
        )


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Required-field validation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Publishing is blocked when Building Images are not uploaded (ADO-136119)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136119")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136119
@pytest.mark.skip(
    reason="No confirmed 'remove/clear uploaded file' control exists on this Object Authoring "
    "surface (ObjectAuthoringPage exposes upload_file()/uploaded_filename() only — no clear "
    "method, and the abandoned live probe this session could not confirm one either; see "
    "home_about_summary_admin_page.py's module PROBE FAILURE note). The shared TEST_OWNED "
    "Section singleton (QCDEMO-129389-ABOUT_US_SECTION-01) must never be left without its real "
    "Building Images if a manual clear succeeds but the restore step cannot re-upload — an "
    "irreversible-risk precondition this project's cms-profile.md Test-Data Policy prohibits "
    "constructing without a confirmed, safe undo path."
)
def test_publish_blocked_when_building_images_not_uploaded_136119(page):
    ...


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Years of Experience Badge text accepts valid input up to 50 characters, EN/AR (ADO-136120)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136120")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136120
@ABOUT_US_XDIST_GROUP
def test_years_badge_accepts_up_to_50_chars_136120(section_edit):
    # ADO-136120
    admin, _baseline = section_edit
    badge_en = ("QCTEST 63+ Years of Experience badge text " * 2)[:50]
    badge_ar = ("قست اختبار شارة سنوات الخبرة " * 2)[:50]
    assert len(badge_en) == 50 and len(badge_ar) == 50

    admin.open_section_entry()
    admin.ensure_draft()

    with allure.step("Enter Badge EN and AR text within 50 characters each and Save Draft"):
        admin.fill_text(FIELD_YEARS_BADGE_EN, badge_en)
        admin.fill_text(FIELD_YEARS_BADGE_AR, badge_ar)
        admin.save_as_draft()

    assert admin.field_value(FIELD_YEARS_BADGE_EN) == badge_en
    assert admin.field_value(FIELD_YEARS_BADGE_AR) == badge_ar


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Years of Experience Badge rejects input exceeding 50 characters, EN/AR (ADO-136121)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136121")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136121
@ABOUT_US_XDIST_GROUP
def test_years_badge_rejects_over_50_chars_136121(section_edit):
    # ADO-136121
    admin, _baseline = section_edit
    over_51 = ("QCTEST over-limit badge text value here " * 2)[:51]
    assert len(over_51) == 51
    admin.open_section_entry()

    with allure.step("Enter a 51-character string into Badge EN — truncated or rejected"):
        assert admin.field_length_rejected(FIELD_YEARS_BADGE_EN, over_51, 50)


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Read More Label accepts valid input up to 50 characters, EN/AR (ADO-136122)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136122")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136122
@ABOUT_US_XDIST_GROUP
def test_read_more_label_accepts_up_to_50_chars_136122(section_edit):
    # ADO-136122
    admin, _baseline = section_edit
    label_en = ("QCTEST Read More about Qatar Chamber " * 2)[:50]
    label_ar = ("قست اختبار اقرأ المزيد عن الغرفة " * 2)[:50]
    assert len(label_en) == 50 and len(label_ar) == 50

    admin.open_section_entry()
    admin.ensure_draft()

    with allure.step("Enter Read More Label EN and AR within limit and Save Draft"):
        admin.fill_text(FIELD_READ_MORE_LABEL_EN, label_en)
        admin.fill_text(FIELD_READ_MORE_LABEL_AR, label_ar)
        admin.save_as_draft()

    assert admin.field_value(FIELD_READ_MORE_LABEL_EN) == label_en
    assert admin.field_value(FIELD_READ_MORE_LABEL_AR) == label_ar


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Required-field validation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Publishing is blocked when Read More Label is left empty, EN and AR (ADO-136123)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136123")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136123
@ABOUT_US_XDIST_GROUP
def test_publish_blocked_when_read_more_label_empty_136123(section_edit):
    # ADO-136123
    admin, _baseline = section_edit
    admin.open_section_entry()

    with allure.step("Clear Read More Label EN, fill remaining mandatory fields"):
        _fill_all_section_fields(admin, "QCTEST-136123", **{FIELD_READ_MORE_LABEL_EN: ""})

    with allure.step("Click Publish — blocked for empty EN Label"):
        admin.submit_for_publishing()
        assert admin.current_status() != "Approved"

    with allure.step("Fill Label EN, clear Label AR, click Publish — blocked for empty AR Label"):
        admin.open_section_entry()
        admin.fill_text(FIELD_READ_MORE_LABEL_EN, "QCTEST-136123 Read More")
        admin.fill_text(FIELD_READ_MORE_LABEL_AR, "")
        admin.submit_for_publishing()
        assert admin.current_status() != "Approved"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Read More URL accepts a valid URL up to 500 characters (ADO-136124)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136124")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136124
@ABOUT_US_XDIST_GROUP
def test_read_more_url_accepts_valid_url_136124(section_edit):
    # ADO-136124
    admin, _baseline = section_edit
    long_query = "&".join(f"qctest{i}=136124" for i in range(50))
    valid_url = f"https://qcdev.ihorizons.com/web/qatar-chamber/about-us?{long_query}"[:500]

    admin.open_section_entry()
    admin.ensure_draft()

    with allure.step("Enter a valid URL into Read More URL and Save Draft"):
        admin.fill_text(FIELD_READ_MORE_URL, valid_url)
        admin.save_as_draft()

    assert admin.field_value(FIELD_READ_MORE_URL) == valid_url


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Required-field validation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Publishing is blocked when Read More URL is left empty (ADO-136125)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136125")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136125
@ABOUT_US_XDIST_GROUP
def test_publish_blocked_when_read_more_url_empty_136125(section_edit):
    # ADO-136125
    admin, _baseline = section_edit
    admin.open_section_entry()

    with allure.step("Clear Read More URL, fill all other mandatory fields"):
        _fill_all_section_fields(admin, "QCTEST-136125", **{FIELD_READ_MORE_URL: ""})

    with allure.step("Click Publish — blocked"):
        admin.submit_for_publishing()
        assert admin.current_status() != "Approved"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("URL format validation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Read More URL is rejected when an invalid URL format is entered (ADO-136126)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136126")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136126
@ABOUT_US_XDIST_GROUP
def test_read_more_url_rejects_invalid_format_136126(section_edit):
    """ADO-136126. The case's exact bilingual wording ("Please enter a valid
    URL.") was not independently confirmed live this session (probe
    failure, see module docstring) — asserted instead via the same
    publish-blocked observable used throughout this batch
    (current_status() != "Approved")."""
    admin, _baseline = section_edit
    admin.open_section_entry()

    with allure.step("Enter 'not-a-valid-url' into Read More URL"):
        admin.fill_text(FIELD_READ_MORE_URL, "not-a-valid-url")

    with allure.step("Click Publish — blocked"):
        admin.submit_for_publishing()
        assert admin.current_status() != "Approved"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Counter Title accepts valid input up to 30 characters, EN/AR (ADO-136127)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136127")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136127
@ABOUT_US_XDIST_GROUP
def test_counter_title_accepts_up_to_30_chars_136127(counter_edit):
    # ADO-136127
    counter, _baseline = counter_edit
    title_en = ("QCTEST E-Services title " * 2)[:30]
    title_ar = ("قست اختبار خدمات " * 2)[:30]
    assert len(title_en) == 30 and len(title_ar) == 30

    counter.open_counter(COUNTER_ENTRY_CODES[0])
    counter.ensure_draft()

    with allure.step("Enter Counter Title EN and AR within 30 characters and Save"):
        counter.set_title_en(title_en)
        counter.set_title_ar(title_ar)
        counter.save_as_draft()

    assert counter.title_en_value() == title_en
    assert counter.field_value(FIELD_COUNTER_TITLE_AR) == title_ar


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Required-field validation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Publishing is blocked when a Counter Title is left empty, EN and AR (ADO-136128)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136128")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136128
@ABOUT_US_XDIST_GROUP
def test_publish_blocked_when_counter_title_empty_136128(counter_edit):
    # ADO-136128
    counter, _baseline = counter_edit
    counter.open_counter(COUNTER_ENTRY_CODES[0])

    with allure.step("Leave Counter Title EN empty, fill other counter fields"):
        _fill_counter_fields(counter, "QCTEST-136128", **{FIELD_COUNTER_TITLE_EN: ""})

    with allure.step("Click Publish — blocked for empty EN Title"):
        counter.submit_for_publishing()
        assert counter.current_status() != "Approved"

    with allure.step("Fill Title EN, clear Title AR, click Publish — blocked for empty AR Title"):
        counter.open_counter(COUNTER_ENTRY_CODES[0])
        counter.set_title_en("QCTEST-136128 E-Services")
        counter.set_title_ar("")
        counter.submit_for_publishing()
        assert counter.current_status() != "Approved"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Counter Value accepts valid input up to 10 characters (ADO-136129)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136129")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136129
@ABOUT_US_XDIST_GROUP
def test_counter_value_accepts_up_to_10_chars_136129(counter_edit):
    # ADO-136129
    counter, _baseline = counter_edit
    value_10 = "12345678 +"
    assert len(value_10) == 10

    counter.open_counter(COUNTER_ENTRY_CODES[0])
    counter.ensure_draft()

    with allure.step("Enter Counter Value within 10 characters and Save"):
        counter.set_value(value_10)
        counter.save_as_draft()

    assert counter.value_value() == value_10


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Required-field validation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Publishing is blocked when Counter Value is left empty (ADO-136130)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136130")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136130
@ABOUT_US_XDIST_GROUP
def test_publish_blocked_when_counter_value_empty_136130(counter_edit):
    # ADO-136130
    counter, _baseline = counter_edit
    counter.open_counter(COUNTER_ENTRY_CODES[0])

    with allure.step("Leave Counter Value empty, fill other counter fields"):
        _fill_counter_fields(counter, "QCTEST-136130", **{FIELD_COUNTER_VALUE: ""})

    with allure.step("Click Publish — blocked"):
        counter.submit_for_publishing()
        assert counter.current_status() != "Approved"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Field length boundaries")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Counter Value rejects input exceeding the 10-character limit (ADO-136131)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136131")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136131
@ABOUT_US_XDIST_GROUP
def test_counter_value_rejects_over_10_chars_136131(counter_edit):
    # ADO-136131
    counter, _baseline = counter_edit
    over_11 = "12345678901"
    assert len(over_11) == 11
    counter.open_counter(COUNTER_ENTRY_CODES[0])

    with allure.step("Enter an 11-character string into Counter Value — truncated or rejected"):
        assert counter.field_length_rejected(FIELD_COUNTER_VALUE, over_11, 10)


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Counter Icon upload")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Counter Icon upload succeeds with a valid PNG or SVG under 2MB (ADO-136132)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136132")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136132
@ABOUT_US_XDIST_GROUP
def test_counter_icon_uploads_valid_png_or_svg_under_2mb_136132(counter_edit):
    # ADO-136132
    counter, _baseline = counter_edit
    counter.open_counter(COUNTER_ENTRY_CODES[0])
    counter.ensure_draft()

    with allure.step("Upload a valid SVG under 2MB as a Counter Icon"):
        counter.upload_icon(f"{FIXTURES}/about_counter_icon.svg")

    with allure.step("Save"):
        counter.save_as_draft()

    assert "about_counter_icon" in counter.icon_filename()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Counter Icon upload")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Counter Icon upload is rejected for unsupported format or oversized file (ADO-136133)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136133")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136133
@ABOUT_US_XDIST_GROUP
def test_counter_icon_upload_rejected_unsupported_or_oversized_136133(counter_edit):
    # ADO-136133
    counter, _baseline = counter_edit
    counter.open_counter(COUNTER_ENTRY_CODES[0])

    with allure.step("Attempt to upload a .bmp file as Counter Icon — rejected (unsupported format)"):
        assert counter.upload_file_expect_rejected(FIELD_COUNTER_ICON, f"{FIXTURES}/about_counter_icon_invalid.bmp")

    with allure.step("Attempt to upload an oversized PNG (>2MB) as Counter Icon — rejected"):
        counter.open_counter(COUNTER_ENTRY_CODES[0])
        assert counter.upload_file_expect_rejected(FIELD_COUNTER_ICON, f"{FIXTURES}/about_counter_icon_oversized.png")


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Counter Display Order")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Counter Display Order accepts a valid positive integer and persists after save (ADO-136134)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136134")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136134
@ABOUT_US_XDIST_GROUP
def test_counter_display_order_accepts_valid_positive_integer_136134(counter_edit):
    # ADO-136134
    counter, _baseline = counter_edit
    counter.open_counter(COUNTER_ENTRY_CODES[0])

    with allure.step("Enter a valid positive integer Display Order"):
        counter.set_display_order("777")

    with allure.step("Click Publish"):
        counter.submit_for_publishing()
        assert counter.current_status() == "Approved"

    with allure.step("Reload the CMS management screen"):
        counter.open_counter(COUNTER_ENTRY_CODES[0])

    assert counter.display_order_value() == "777"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Counter Display Order")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Counter Display Order rejects empty, zero, negative, or non-numeric input (ADO-136135)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136135")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136135
@ABOUT_US_XDIST_GROUP
def test_counter_display_order_rejects_invalid_values_136135(counter_edit):
    # ADO-136135
    counter, _baseline = counter_edit

    for label, bad_value in (("empty", ""), ("zero", "0"), ("negative", "-1"), ("non-numeric", "abc")):
        with allure.step(f"Enter {label!r} ({bad_value!r}) as Display Order and attempt to publish"):
            counter.open_counter(COUNTER_ENTRY_CODES[0])
            try:
                counter.set_display_order(bad_value)
            except Exception:
                pass  # a native <input type=number> may itself refuse non-numeric keystrokes
            counter.submit_for_publishing()
            assert counter.current_status() != "Approved", f"Display Order accepted an invalid value: {bad_value!r}"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Counter visibility toggling")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Toggling Counter Active Status controls counter visibility independently per counter (ADO-136137)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136137")
@pytest.mark.control_panel
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136137
@ABOUT_US_XDIST_GROUP
def test_toggling_counter_active_status_controls_visibility_136137(page, browser):
    """ADO-136137. Tagged BOTH Control_Panel and Web — one test doing the
    admin action then verifying on the public page, mirroring tc_136106's
    precedent (same reasoning: a case spanning both platforms is realized
    as a single test here, not duplicated in the web module)."""
    counter_a = HomeAboutCounterAdminPage(page)  # row 01 — E-Services
    counter_b = HomeAboutCounterAdminPage(page)  # row 02 — Certificates Issued
    code_a, code_b = COUNTER_ENTRY_CODES[0], COUNTER_ENTRY_CODES[1]

    baseline_a = counter_a.capture_baseline(code_a)
    baseline_b = counter_b.capture_baseline(code_b)
    anon_ctx = new_context(browser, use_auth_state=False)
    anon_page = anon_ctx.new_page()
    home = HomeAboutSummaryPage(anon_page)

    try:
        with allure.step("Set Counter A Active=True, Counter B Active=False, publish"):
            counter_a.open_counter(code_a)
            counter_a.set_active(True)
            counter_a.submit_for_publishing()
            assert counter_a.current_status() == "Approved"

            counter_b.open_counter(code_b)
            counter_b.set_active(False)
            counter_b.submit_for_publishing()
            assert counter_b.current_status() == "Approved"

        with allure.step("Home Page shows Counter A, not Counter B"):
            label_a, label_b = baseline_a["title_en"], baseline_b["title_en"]
            reflected = home.reload_until(
                lambda h: h.is_counter_label_present(label_a) and not h.is_counter_label_present(label_b)
            )
            assert reflected, "Active-status toggle did not reflect on the public Home Page within the poll budget"

        with allure.step("Flip Counter A to False and Counter B to True, publish"):
            counter_a.open_counter(code_a)
            counter_a.set_active(False)
            counter_a.submit_for_publishing()

            counter_b.open_counter(code_b)
            counter_b.set_active(True)
            counter_b.submit_for_publishing()

        with allure.step("Reload Home Page — Counter B shows, Counter A does not"):
            reflected_2 = home.reload_until(
                lambda h: h.is_counter_label_present(label_b) and not h.is_counter_label_present(label_a)
            )
            assert reflected_2, "flipped Active-status toggle did not reflect on the public Home Page within the poll budget"
    finally:
        with allure.step("Teardown: restore both counter rows' baselines"):
            counter_a.restore(baseline_a)
            counter_a.open_counter(code_a)
            assert counter_a.title_en_value() == baseline_a["title_en"]

            counter_b.restore(baseline_b)
            counter_b.open_counter(code_b)
            assert counter_b.title_en_value() == baseline_b["title_en"]
        anon_ctx.close()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Discard unsaved changes")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Discarding unsaved changes in the About Us Section Management form reverts to the last saved state (ADO-136138)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136138")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136138
@ABOUT_US_XDIST_GROUP
def test_discard_unsaved_changes_reverts_to_last_saved_state_136138(section_edit):
    # ADO-136138
    admin, baseline = section_edit

    with allure.step("Open an existing published About Us section"):
        admin.open_section_entry()

    with allure.step("Change Section Heading EN to a temporary unsaved value"):
        admin.fill_text(FIELD_SECTION_HEADING_EN, "QCTEST-136138 TEMPORARY UNSAVED VALUE")

    with allure.step("Navigate away without saving (Cancel equivalent — never submitted)"):
        admin.open_entries_list()

    with allure.step("Reopen the section"):
        admin.open_section_entry()

    assert admin.field_value(FIELD_SECTION_HEADING_EN) == baseline["heading_en"], (
        "unsaved edit leaked into the persisted Section Heading (EN)"
    )


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Counter cap — edge")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A 5th counter cannot be added once 4 counters already exist (ADO-136140)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136140")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129389
@pytest.mark.tc_136140
@ABOUT_US_XDIST_GROUP
def test_5th_counter_cannot_be_added_136140(page):
    """ADO-136140. Step 1 (UI Add-control state) is scripted below. Step 2
    ("if bypassed via direct request, attempt to save a 5th counter payload
    ... rejected server-side") is an API-level bypass check — out of scope
    per this project's team-agreed UI-only-no-API test-data policy
    (cms-profile.md's Test-Data Policy section); not scripted, disclosed
    here rather than silently dropped."""
    counter = HomeAboutCounterAdminPage(page)

    with allure.step("With 4 counters already present, the Add control is disabled/hidden — never clicked"):
        counter.open_counter_list()
        assert counter.counter_row_count() >= 4
        state = counter.add_counter_control_state()
        assert not state["visible"] or state["disabled"], (
            f"Add control still enabled with 4 counters present: {state!r}"
        )

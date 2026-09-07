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
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials
from core.web.browser import new_context
from web.pages.home_about_summary.home_about_summary_page import HomeAboutSummaryPage

ABOUT_US_XDIST_GROUP = pytest.mark.xdist_group("about_us_section_52157")


def _login_as_site_content_editor(page) -> None:
    email, password = cms_role_credentials("Site Content Editor")
    CmsLoginPage(page).open_login().login(email, password)


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

"""
cms/tests/home_about_summary/test_home_about_summary_control_panel.py —
Control_Panel-tagged cases for PBI 129389 (QC-HOME-013 — "About Us Section &
Last Year Achievements Counters"), backing the homepage "About Us" summary
widget.

PBI resolution note (per this task's instruction to resolve via the parent/
TestedBy-Reverse link, not guess): no azure-devops MCP tool was available in
this session's toolset, so the ID could not be confirmed through the Azure
API directly. It was instead confirmed LIVE against the real CMS: the "About
Us Sections" Object Definition's own singleton record carries
externalReferenceCode `QCDEMO-129389-ABOUT_US_SECTION-01` (see
HomeAboutSummaryAdminPage's module docstring for the full exploration
trail) — the "129389" embedded there is the product team's own seed-data
naming convention for this PBI (the same convention already relied on
verbatim for pbi_129397/GM's Message, pbi_129398/Board Members, etc.
elsewhere in this suite), not an inferred/guessed number.
"""

import allure
import pytest

from cms.pages.home_about_summary.home_about_summary_admin_page import (
    HomeAboutSummaryAdminPage,
)
from config.settings import settings


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
@pytest.mark.xdist_group("home_about_summary_52157")
def test_about_us_section_field_values_persist_after_save_and_reload_136136(page):
    """ADO-136136. Confirms no data loss occurs on a full save/reload cycle
    across all field types on the About Us Section singleton record (ID
    52157) plus one counter set (About Us Counters row 01, ERC
    QCDEMO-129389-ABOUT_US_COUNTER-01) — matching the case's own "one
    counter set" wording in Step 1.

    Scope/mechanism notes (disclosed per automation-standards.md's Result
    Integrity rule):
      - This homepage section is backed by TWO Object Definitions in the
        live CMS ("About Us Sections" + "About Us Counters") — see
        HomeAboutSummaryAdminPage's module docstring for the live
        exploration that found this. Both are exercised here since the
        case's Step 1 explicitly calls for "one counter set" alongside the
        section's own mandatory/optional fields.
      - TEST_OWNED shared singleton per cms-profile.md's Test-Data Policy:
        both records are dedicated CMS content this session did not create
        (About Us Section 52157 is a singleton — "Showing 1 to 1 of 1
        entries" confirmed live; Counter row 01 is one of 4 seeded QCDEMO
        rows). This test captures each record's CURRENT field values as the
        baseline before mutating, edits with concrete QCTEST-prefixed
        bilingual data, and ALWAYS restores the captured baseline in a
        `finally` block — never leaving either shared record mutated even
        on failure.
      - The case's Expected-column steps are shifted by one relative to
        their Actions (Step 1's action maps to Step 2's expected text, Step
        2's action maps to Step 3's expected text, etc. — a transcription
        artifact in the source case). This test asserts the case's actual
        INTENT instead of the literal shifted text: fill fields -> Publish
        (Save) succeeds with no validation error -> log out -> log back in
        as the content-authoring test account -> reopen the records ->
        every previously entered value is still present, exactly as
        entered, in both EN and AR.
      - Step 3 ("log back in as Site Content Editor") uses the same
        TEST_USER/TEST_PASSWORD account already used by every other
        Control_Panel test in this suite (cms-profile.md flags this
        account's exact role mapping as unconfirmed but it is the only
        provisioned CMS-authoring account available) — a literal, separate
        "Site Content Editor"-only account is not provisioned
        (TEST_USER_RESTRICTED is a different, still-blocked account per
        cms-profile.md).
      - Neither form on this page has a Status/Publish control distinct
        from Save (confirmed live — same shape as gm_message_admin_page.py
        and org_structure_admin_page.py) and no success toast selector is
        confirmed; "Publish succeeds" is verified via the negative signal
        (`is_save_error_shown()` is False), and the real proof of
        persistence is the post-re-login reopen-and-compare in this test's
        main assertion block, per the case's actual Step 4 intent.
      - Building Image (Primary/Secondary/Tertiary) upload fields on the
        About Us Section form are NOT re-uploaded (no confirmed, safe
        download-then-restore round trip this session — same reasoning
        already applied to GM Portrait Image/Hero Banner in
        gm_message_admin_page.py's own test module); Section Description
        (AR/EN) rich-text fields are also left untouched this pass (no
        CKEditor Source-mode locator confirmed live for this specific form)
        — every other visible field (8 text fields on the Section form + 4
        on the Counter form, one of which is a checkbox left untouched to
        avoid disabling the live counter) is exercised, which already
        covers every field TYPE the case's Step 1 calls for (mandatory
        text, optional text, and the "one counter set").
    """
    admin = HomeAboutSummaryAdminPage(page)

    qctest_heading_en = "QCTEST-136136 Qatar Chamber Persist Check"
    qctest_heading_ar = "QCTEST-136136 غرفة قطر فحص الاستمرارية"
    qctest_tag_en = "QCTEST-136136 MORE ABOUT US"
    qctest_years_badge_en = "QCTEST-136136 63+ Years of Experience"
    qctest_read_more_label_en = "QCTEST-136136 Read More"
    qctest_counter_title_en = "QCTEST-136136 E-Services"
    qctest_counter_value = "999 +"

    with allure.step("Open the About Us Section singleton record"):
        admin.open_about_us_section_edit_form()

    with allure.step("Capture the current (baseline) Section field values for teardown"):
        baseline_heading_en = admin.field_value(admin.SECTION_HEADING_EN)
        baseline_heading_ar = admin.field_value(admin.SECTION_HEADING_AR)
        baseline_tag_en = admin.field_value(admin.SECTION_TAG_EN)
        baseline_years_badge_en = admin.field_value(admin.SECTION_YEARS_BADGE_EN)
        baseline_read_more_label_en = admin.field_value(admin.SECTION_READ_MORE_LABEL_EN)

    with allure.step("Open the About Us Counter (row 01) record and capture its baseline"):
        admin.open_counter_01_edit_form()
        baseline_counter_title_en = admin.field_value(admin.COUNTER_TITLE_EN)
        baseline_counter_value = admin.field_value(admin.COUNTER_VALUE)

    try:
        with allure.step("Fill all exercised mandatory/optional Section fields with distinct values (EN + AR)"):
            admin.open_about_us_section_edit_form()
            admin.fill_text_field(admin.SECTION_HEADING_EN, qctest_heading_en)
            admin.fill_text_field(admin.SECTION_HEADING_AR, qctest_heading_ar)
            admin.fill_text_field(admin.SECTION_TAG_EN, qctest_tag_en)
            admin.fill_text_field(admin.SECTION_YEARS_BADGE_EN, qctest_years_badge_en)
            admin.fill_text_field(admin.SECTION_READ_MORE_LABEL_EN, qctest_read_more_label_en)

        # Assert: fields accept the new input before Save (Step 1's "fill" half).
        assert admin.field_value(admin.SECTION_HEADING_EN) == qctest_heading_en
        assert admin.field_value(admin.SECTION_HEADING_AR) == qctest_heading_ar

        with allure.step("Click Save (this form's Publish action) on the Section record"):
            admin.save()

        # Assert: Publish (Save) succeeds — no validation error surfaced.
        assert not admin.is_save_error_shown(), admin.save_error_text()

        with allure.step("Fill the one counter set (About Us Counters row 01) with a distinct value"):
            admin.open_counter_01_edit_form()
            admin.fill_text_field(admin.COUNTER_TITLE_EN, qctest_counter_title_en)
            admin.fill_text_field(admin.COUNTER_VALUE, qctest_counter_value)
            admin.save()

        # Assert: the counter set's Save also succeeds.
        assert not admin.is_save_error_shown(), admin.save_error_text()

        with allure.step("Log out of the Control Panel"):
            admin.logout()

        with allure.step('Log back in as the CMS content-authoring test account ("Site Content Editor" — see docstring)'):
            admin.login_as(settings.test_user, settings.test_password)

        with allure.step("Navigate back to the About Us Section record and read every field back"):
            admin.open_about_us_section_edit_form()
            reloaded_heading_en = admin.field_value(admin.SECTION_HEADING_EN)
            reloaded_heading_ar = admin.field_value(admin.SECTION_HEADING_AR)
            reloaded_tag_en = admin.field_value(admin.SECTION_TAG_EN)
            reloaded_years_badge_en = admin.field_value(admin.SECTION_YEARS_BADGE_EN)
            reloaded_read_more_label_en = admin.field_value(admin.SECTION_READ_MORE_LABEL_EN)

        # Assert: Step 4 — all previously entered Section values display
        # exactly as entered, no data loss, across the logout/login cycle.
        assert reloaded_heading_en == qctest_heading_en
        assert reloaded_heading_ar == qctest_heading_ar
        assert reloaded_tag_en == qctest_tag_en
        assert reloaded_years_badge_en == qctest_years_badge_en
        assert reloaded_read_more_label_en == qctest_read_more_label_en

        with allure.step("Navigate back to the About Us Counter (row 01) record and read its fields back"):
            admin.open_counter_01_edit_form()
            reloaded_counter_title_en = admin.field_value(admin.COUNTER_TITLE_EN)
            reloaded_counter_value = admin.field_value(admin.COUNTER_VALUE)

        # Assert: Step 4 — the one counter set also persisted exactly as
        # entered, no data loss.
        assert reloaded_counter_title_en == qctest_counter_title_en
        assert reloaded_counter_value == qctest_counter_value
    finally:
        with allure.step("Teardown: restore the baseline Section field values so the shared singleton record is never left mutated"):
            admin.open_about_us_section_edit_form()
            admin.fill_text_field(admin.SECTION_HEADING_EN, baseline_heading_en)
            admin.fill_text_field(admin.SECTION_HEADING_AR, baseline_heading_ar)
            admin.fill_text_field(admin.SECTION_TAG_EN, baseline_tag_en)
            admin.fill_text_field(admin.SECTION_YEARS_BADGE_EN, baseline_years_badge_en)
            admin.fill_text_field(admin.SECTION_READ_MORE_LABEL_EN, baseline_read_more_label_en)
            admin.save()
            assert not admin.is_save_error_shown(), (
                "Teardown restore of the About Us Section record itself "
                "failed validation: " + admin.save_error_text()
            )
            # Same false-green hardening already applied to the GM's
            # Message teardown against its own shared singleton (record
            # 79878, see test_gm_message_control_panel.py): re-open and
            # re-read the persisted values back rather than trusting the
            # absence of a validation error alone.
            admin.open_about_us_section_edit_form()
            reread_heading_en = admin.field_value(admin.SECTION_HEADING_EN)
            reread_heading_ar = admin.field_value(admin.SECTION_HEADING_AR)
            reread_tag_en = admin.field_value(admin.SECTION_TAG_EN)
            reread_years_badge_en = admin.field_value(admin.SECTION_YEARS_BADGE_EN)
            reread_read_more_label_en = admin.field_value(admin.SECTION_READ_MORE_LABEL_EN)
            assert reread_heading_en == baseline_heading_en, (
                f"Teardown restore did not persist: Section Heading (EN) reads "
                f"{reread_heading_en!r}, expected {baseline_heading_en!r}."
            )
            assert reread_heading_ar == baseline_heading_ar, (
                f"Teardown restore did not persist: Section Heading (AR) reads "
                f"{reread_heading_ar!r}, expected {baseline_heading_ar!r}."
            )
            assert reread_tag_en == baseline_tag_en, (
                f"Teardown restore did not persist: Section Tag (EN) reads "
                f"{reread_tag_en!r}, expected {baseline_tag_en!r}."
            )
            assert reread_years_badge_en == baseline_years_badge_en, (
                f"Teardown restore did not persist: Years of Experience Badge (EN) "
                f"reads {reread_years_badge_en!r}, expected {baseline_years_badge_en!r}."
            )
            assert reread_read_more_label_en == baseline_read_more_label_en, (
                f"Teardown restore did not persist: Read More Label (EN) reads "
                f"{reread_read_more_label_en!r}, expected {baseline_read_more_label_en!r}."
            )

        with allure.step("Teardown: restore the baseline Counter (row 01) field values"):
            admin.open_counter_01_edit_form()
            admin.fill_text_field(admin.COUNTER_TITLE_EN, baseline_counter_title_en)
            admin.fill_text_field(admin.COUNTER_VALUE, baseline_counter_value)
            admin.save()
            assert not admin.is_save_error_shown(), (
                "Teardown restore of the About Us Counter record itself "
                "failed validation: " + admin.save_error_text()
            )
            admin.open_counter_01_edit_form()
            reread_counter_title_en = admin.field_value(admin.COUNTER_TITLE_EN)
            reread_counter_value = admin.field_value(admin.COUNTER_VALUE)
            assert reread_counter_title_en == baseline_counter_title_en, (
                f"Teardown restore did not persist: Counter Title (EN) reads "
                f"{reread_counter_title_en!r}, expected {baseline_counter_title_en!r}."
            )
            assert reread_counter_value == baseline_counter_value, (
                f"Teardown restore did not persist: Counter Value reads "
                f"{reread_counter_value!r}, expected {baseline_counter_value!r}."
            )

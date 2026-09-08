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

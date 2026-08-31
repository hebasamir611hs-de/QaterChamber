"""
web/tests/home_about_summary/test_home_about_summary_web.py — About Us
Section & Last Year Achievements Counters (PBI 129389 / QC-HOME-013), Web
platform.

Source: 7 approved, Automation-tagged, UI-category, Web-platform cases read
verbatim from the injected batch for this PBI (ADO TC 136088, 136089, 136090,
136091, 136093, 136094, 136097). Per this run's explicit scope instruction,
only the UI-category/Automation-tagged cases are automated here —
Functional/Edge/Compatibility/Auth-tagged cases sharing the ABOUT tag on this
same PBI are out of scope for this batch and are NOT authored below. No
Control_Panel-tagged cases were handed off for this PBI in this batch either
(see the sibling home_about_summary_admin_page.py skeleton).

Axis markers applied: every case here carries `Web` (Platform ->
@pytest.mark.web), `UI` (Category -> @pytest.mark.ui), and `ABOUT` (Service ->
@pytest.mark.about, per active/standards.md's Service/Module Codes table).
None of the 7 cases' own `Tags` include `Regression` or any Axis-5 business
keyword (`Bilingual`/`FigmaVerified`/etc.) in this injected batch, so no
`regression` marker and no Axis-5 marker are applied — read verbatim, not
inferred from case behavior. `UAT` is present on 3 of the 7 cases (136088,
136091, 136094) but per the marker table UAT drives the client doc only and
gets no pytest marker.

Known real-environment findings surfaced while scripting these (full detail
in web/pages/home_about_summary/home_about_summary_page.py's docstring, which
documents the live CLI-extraction/script-probe evidence for every value
below). Per this project's established convention, a live-observed value is
kept as the asserted target when the case has no independent literal
value to check against (e.g. the counters' settled numbers — there is no
Control_Panel access in this run's scope to read the "configured Counter
Value" independently of the live render):
  - TC 136088: CONFIRMED LIVE, genuine pass — collage, badge, tag/heading/
    description, Read More CTA, and the 4-counter block all render
    simultaneously once the section scrolls into view.
  - TC 136089: CONFIRMED LIVE, genuine pass — exactly 2 collage images, both
    fully loaded (no broken-image icon), with genuinely overlapping bounding
    boxes.
  - TC 136090: CONFIRMED LIVE, genuine pass — badge reads "62+" / "Years of
    Experience", positioned `absolute`/`z-index:3`, and its box measurably
    overlaps the primary collage image (a real overlay, not just adjacent).
  - TC 136091: CONFIRMED LIVE, genuine pass — EN and AR each render distinct,
    correct tag/heading/description text, with `dir="rtl"` in Arabic.
  - TC 136093: CONFIRMED LIVE, genuine pass — "Last Year Achievements" /
    "إنجازات العام الماضي" renders bold (font-weight 700) directly above the
    counter row, no overlap.
  - TC 136094: CONFIRMED LIVE, genuine pass — all 4 counters read a literal
    "0" the instant the section scrolls into view, then animate upward and
    settle at 145 / 70,000 / 210,000 / 200 for E-Services / Certificates
    Issued / Documents Attested / Business Events respectively (see the Page
    Object's `wait_for_counters_to_settle()` for the poll-until-stable wait
    strategy — never a fixed sleep for an arbitrary duration).
  - TC 136097: CONFIRMED LIVE, genuine pass — the AR media/content halves are
    the true mirror of EN's, and neither language shows horizontal page
    overflow/clipping at 1920x1080.
"""

import allure
import pytest

from web.pages.home_about_summary.home_about_summary_page import HomeAboutSummaryPage

PBI = "129389"

EXPECTED_TAG_EN = "MORE ABOUT US"
EXPECTED_HEADING_EN = "Qatar Chamber"
EXPECTED_TAG_AR = "اعرف المزيد عنّا"
EXPECTED_HEADING_AR = "غرفة قطر"

EXPECTED_BADGE_NUM = "62+"
EXPECTED_BADGE_LABEL = "Years of Experience"

EXPECTED_ACHIEVEMENTS_TITLE_EN = "Last Year Achievements"

EXPECTED_COUNTER_LABELS = ["E-Services", "Certificates Issued", "Documents Attested", "Business Events"]
EXPECTED_COUNTER_VALUES = [145, 70000, 210000, 200]


# ── TC 136088 — About Us section renders all elements (Figma-verified) ──────
@allure.epic("ABOUT")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Section renders all sub-elements")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The About Us section renders all elements correctly on the Home Page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.traceability("ABOUT-ABOUTUS-TC-136088")
def test_about_us_section_renders_all_elements(page):
    # ABOUT-ABOUTUS-TC-136088 | PBI 129389
    # Arrange
    about = HomeAboutSummaryPage(page)

    # Act
    with allure.step("Navigate to the Home Page as a public visitor and scroll to the About Us section"):
        about.open_home()
        about.scroll_to_section()

    with allure.step("Inspect the image collage, badge overlay, tag/heading/description, Read More CTA, and counter block"):
        collage_visible = about.is_collage_visible()
        badge_visible = about.is_badge_visible()
        tag_visible = about.is_tag_visible()
        heading_visible = about.is_heading_visible()
        description_visible = about.is_description_visible()
        readmore_visible = about.is_readmore_visible()
        counters_visible = about.is_counters_visible()
        counter_count = about.counter_count()

    # Assert
    assert about.is_section_visible()
    assert collage_visible, "expected the image collage to be visible"
    assert badge_visible, "expected the badge overlay to be visible"
    assert tag_visible, "expected the section tag to be visible"
    assert heading_visible, "expected the heading to be visible"
    assert description_visible, "expected the description to be visible"
    assert readmore_visible, "expected the Read More CTA to be visible"
    assert counters_visible, "expected the counter block to be visible"
    assert counter_count == 4, f"expected 4 counters, got {counter_count}"


# ── TC 136089 — Building image collage overlapping layout ───────────────────
@allure.epic("ABOUT")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Image collage layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The building image collage displays with correct overlapping layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.traceability("ABOUT-ABOUTUS-TC-136089")
def test_image_collage_displays_with_overlapping_layout(page):
    # ABOUT-ABOUTUS-TC-136089 | PBI 129389
    # Arrange
    about = HomeAboutSummaryPage(page)

    # Act
    with allure.step("Load the Home Page with the About Us section visible"):
        about.open_home()
        about.scroll_to_section()

    with allure.step("Locate the About Us image collage"):
        image_count = about.collage_image_count()
        images_loaded = about.collage_images_loaded()
        images_overlap = about.collage_images_overlap()

    # Assert
    assert about.is_section_visible()
    assert image_count == 2, f"expected 2 collage images, got {image_count}"
    assert images_loaded, "expected both collage images to be fully loaded with no broken-image icon"
    assert images_overlap, "expected the two collage images to render overlapping per the layout"


# ── TC 136090 — Years of Experience badge overlay ────────────────────────────
@allure.epic("ABOUT")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Badge overlay content and position")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Years of Experience badge overlay displays the configured numeric value and label")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.traceability("ABOUT-ABOUTUS-TC-136090")
def test_years_of_experience_badge_displays_value_and_label(page):
    # ABOUT-ABOUTUS-TC-136090 | PBI 129389
    # Arrange
    about = HomeAboutSummaryPage(page)

    # Act
    with allure.step("Load the Home Page with the About Us section visible"):
        about.open_home()
        about.scroll_to_section()

    with allure.step("Locate the badge overlay on the image collage"):
        badge_num = about.badge_num_text()
        badge_label = about.badge_label_text()
        badge_style = about.badge_style()
        badge_overlaps = about.badge_overlaps_collage()

    # Assert
    assert about.is_section_visible()
    assert badge_num == EXPECTED_BADGE_NUM, f"expected badge numeric value {EXPECTED_BADGE_NUM!r}, got {badge_num!r}"
    assert badge_label == EXPECTED_BADGE_LABEL, f"expected badge label {EXPECTED_BADGE_LABEL!r}, got {badge_label!r}"
    assert badge_style["position"] == "absolute", "expected the badge to be positioned as an overlay"
    assert badge_overlaps, "expected the badge overlay to visually overlap the image collage"


# ── TC 136091 — Tag/heading/description in the visitor's active language ────
@allure.epic("ABOUT")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Bilingual tag/heading/description rendering")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The About Us section tag, heading, and description display in the visitor's active language")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.traceability("ABOUT-ABOUTUS-TC-136091")
def test_tag_heading_description_display_in_active_language(page):
    # ABOUT-ABOUTUS-TC-136091 | PBI 129389
    # Arrange
    about = HomeAboutSummaryPage(page)

    # Act
    with allure.step("Load the Home Page with site language set to English"):
        about.open_home()
        about.scroll_to_section()

    with allure.step("Inspect the EN tag/heading/description text and layout direction"):
        en_dir = about.page_direction()
        en_tag = about.tag_text()
        en_heading = about.heading_text()
        en_description = about.description_text()

    with allure.step("Switch site language to Arabic, reload the Home Page, and inspect the tag/heading/description"):
        about.open_home_arabic()
        about.scroll_to_section()
        ar_dir = about.page_direction()
        ar_tag = about.tag_text()
        ar_heading = about.heading_text()
        ar_description = about.description_text()

    # Assert
    assert en_dir == "ltr", f"expected LTR layout in English, got dir={en_dir!r}"
    assert en_tag == EXPECTED_TAG_EN
    assert en_heading == EXPECTED_HEADING_EN
    assert en_description, "expected a non-empty EN description"
    assert ar_dir == "rtl", f"expected RTL layout in Arabic, got dir={ar_dir!r}"
    assert ar_tag == EXPECTED_TAG_AR
    assert ar_heading == EXPECTED_HEADING_AR
    assert ar_description, "expected a non-empty AR description"
    assert ar_description != en_description, "expected the AR description to be translated, not the EN copy"


# ── TC 136093 — Achievements sub-heading above the counter block ────────────
@allure.epic("ABOUT")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Achievements sub-heading position")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The achievements sub-heading displays above the counter block")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.traceability("ABOUT-ABOUTUS-TC-136093")
def test_achievements_subheading_displays_above_counter_block(page):
    # ABOUT-ABOUTUS-TC-136093 | PBI 129389
    # Arrange
    about = HomeAboutSummaryPage(page)

    # Act
    with allure.step("Load the Home Page with the About Us section visible"):
        about.open_home()
        about.scroll_to_section()

    with allure.step("Locate the achievements sub-heading above the counter block"):
        title_text = about.achievements_title_text()
        title_style = about.achievements_title_style()
        title_above_counters = about.achievements_title_is_above_counters()

    # Assert
    assert about.is_section_visible()
    assert title_text == EXPECTED_ACHIEVEMENTS_TITLE_EN
    assert int(title_style["fontWeight"]) >= 700, f"expected a bold sub-heading, got font-weight {title_style['fontWeight']!r}"
    assert title_above_counters, "expected the sub-heading to be positioned directly above the counter row"


# ── TC 136094 — All 4 counters animate from 0 to their configured value ─────
@allure.epic("ABOUT")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Achievement counters animation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("All 4 configured counters display with icon, animated value, and label")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.traceability("ABOUT-ABOUTUS-TC-136094")
def test_counters_animate_from_zero_to_configured_value(page):
    # ABOUT-ABOUTUS-TC-136094 | PBI 129389
    # Arrange
    about = HomeAboutSummaryPage(page)

    # Act
    # NOTE on the starting-value read: the count-up animation is triggered by
    # an IntersectionObserver the instant the counter block enters the
    # viewport, so reading counter_numbers() AFTER scroll_to_section() races
    # the browser's first animation frame (CLI-verified live: a rapid
    # 10ms-interval poll right after scroll_into_view_if_needed() returned
    # showed the values already climbing — e.g. ['3 +','2K +','5K +','4 +']
    # on the very first read, non-deterministic run to run). The Home Page
    # loads scrolled to the top with this section below the fold (CLI-
    # verified: not yet intersecting the viewport), so the counters' static
    # "0"-padded markup can be read deterministically, with no race, BEFORE
    # scroll_to_section() ever triggers the observer.
    with allure.step("Load the Home Page and read the counters before they enter the viewport"):
        about.open_home()
        starting_numbers = about.counter_numbers()

    with allure.step("Scroll the counter block into view and wait for the count-up animation to complete"):
        about.scroll_to_section()
        icons_loaded = about.counter_icons_loaded()
        labels = about.counter_labels()
        about.wait_for_counters_to_settle()
        final_numbers = about.counter_numbers()

    # Assert
    assert about.is_counters_visible()
    assert icons_loaded, "expected all 4 counter icons to be fully loaded"
    assert labels == EXPECTED_COUNTER_LABELS, f"expected counter labels {EXPECTED_COUNTER_LABELS!r}, got {labels!r}"
    assert starting_numbers == [0, 0, 0, 0], (
        f"expected each counter to start at 0 before animating, got {starting_numbers!r}"
    )
    assert final_numbers == EXPECTED_COUNTER_VALUES, (
        f"expected final counter values {EXPECTED_COUNTER_VALUES!r}, got {final_numbers!r}"
    )


# ── TC 136097 — Arabic (RTL) rendering mirrors the About Us layout ──────────
@allure.epic("ABOUT")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("RTL layout mirroring")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Arabic (RTL) rendering of the About Us section mirrors layout correctly")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.traceability("ABOUT-ABOUTUS-TC-136097")
def test_arabic_rtl_rendering_mirrors_layout(page):
    # ABOUT-ABOUTUS-TC-136097 | PBI 129389
    # Arrange
    about = HomeAboutSummaryPage(page)

    # Act
    with allure.step("Load the EN Home Page and read the media/content column order"):
        about.open_home()
        about.scroll_to_section()
        en_media_x = about.media_x()
        en_content_x = about.content_x()
        en_overflow = about.has_page_horizontal_overflow()

    with allure.step("Switch site language to Arabic, load the Home Page, and inspect the section layout direction"):
        about.open_home_arabic()
        about.scroll_to_section()
        ar_dir = about.section_direction()
        ar_media_x = about.media_x()
        ar_content_x = about.content_x()
        ar_overflow = about.has_page_horizontal_overflow()

    # Assert
    assert ar_dir == "rtl", f"expected the section direction to be rtl in Arabic, got {ar_dir!r}"
    assert en_media_x is not None and en_content_x is not None
    assert ar_media_x is not None and ar_content_x is not None
    assert en_media_x < en_content_x, "expected the EN media column to render left of the content column"
    assert ar_media_x > ar_content_x, (
        "expected the AR layout to mirror EN — media column right of the content column"
    )
    assert not en_overflow, "expected no horizontal clipping/overflow on the EN Home Page"
    assert not ar_overflow, "expected no horizontal clipping/overflow on the AR Home Page"

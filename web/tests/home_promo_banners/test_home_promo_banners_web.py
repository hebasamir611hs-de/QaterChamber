"""
web/tests/home_promo_banners/test_home_promo_banners_web.py — Promotional
Banners / Ad Slots (PBI 129368 / QC-HOME-002), Web platform.

Source: 9 approved, Automation-tagged, UI-category, Web-platform cases handed
off for this PBI (ADO TC 135105, 135106, 135107, 135108, 135174, 135175,
135176, 135179, 135180). Control_Panel-tagged cases for this same PBI are
explicit Phase-2 scope and are NOT in this file (see the sibling
test_home_promo_banners_control_panel.py skeleton).

Per automation-standards.md's Axis-1 marker rule ("`UAT` gets no marker — it
drives the client doc, not a pytest slice"), TC 135174's UAT tag is recorded
in its traceability comment/docstring below but does NOT get a
`@pytest.mark.uat` marker — no such marker exists in the project's tag
taxonomy/pytest.ini, and inventing one would deviate from the contract.

Known real-environment findings surfaced while scripting these (full detail
in web/pages/home_promo_banners/home_promo_banners_page.py's docstring):
  - CONFIRMED PRODUCT DEFECT — the pagination-dots container
    (`.qc-promo-dots`) renders `display:none` at every point observed (EN,
    AR, before/after arrow clicks), driven by two real JS console errors on
    every page load. The dots' internal state (aria-selected) still tracks
    correctly, but nothing is ever visually shown, and a direct Playwright
    click on a dot is not even dispatchable. TC 135105/106/107/108 each
    assert this real, expected-by-the-case dot behaviour and each will FAIL
    honestly against the live defect — that is the correct, non-fabricated
    result, not a framework bug.
  - The nav arrows are opaque white CIRCLES (`border-radius: 50%`,
    `background-color: rgb(255, 255, 255)`), not the "semi-transparent
    rounded squares" TC 135105/106 describe — scripted per the case's
    literal wording, will fail honestly on that sub-assertion.
  - TC 135174/135175's example alt text/image filenames
    (`promo-en.jpg` / "Qatar Chamber Annual Forum 2026") do not match the
    live, configured banners. Scripted against the REAL observed EN/AR alt
    text per this batch's own instruction to prefer the live value.
  - TC 135176 requires a single-active-banner CMS state that does not exist
    on qcdev today (3 active banners are live) and cannot be configured by
    this agent (Control_Panel/CMS tooling is explicit out-of-scope for this
    run) — SKIPPED with a concrete reason, never fabricated as a pass.
"""

import allure
import pytest

from web.pages.home_promo_banners.home_promo_banners_page import HomePromoBannersPage

PBI = "129368"


@allure.epic("GLOBAL")
@allure.feature("Promotional Banners / Ad Slots")
@allure.story("Renders correctly in English (LTR)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The promotional banners section renders correctly in English (LTR)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129368
@pytest.mark.traceability("GLOBAL-PROMOBANNER-TC-135105")
def test_promo_banners_render_correctly_in_english_ltr(page):
    # GLOBAL-PROMOBANNER-TC-135105 | PBI 129368
    # Arrange
    promo = HomePromoBannersPage(page)

    # Act
    with allure.step("Navigate to Home Page with English selected"):
        promo.open_home()

    with allure.step("Scroll to the promotional banners section"):
        promo.scroll_to_section()

    with allure.step("Inspect the rendered slide's image, pagination dots, and nav arrows"):
        page_dir = promo.page_direction()
        carousel_dir = promo.carousel_direction()
        current_alt = promo.current_slide_alt_text()
        active_index = promo.active_dot_index()
        dots_visible = promo.is_dots_container_visible()
        prev_rounded_square = promo.is_arrow_rounded_square("prev")
        next_rounded_square = promo.is_arrow_rounded_square("next")
        prev_semi_transparent = promo.is_arrow_semi_transparent("prev")
        next_semi_transparent = promo.is_arrow_semi_transparent("next")
        arrows_vertically_centered = (
            promo.is_arrow_vertically_centered_on_image("prev")
            and promo.is_arrow_vertically_centered_on_image("next")
        )

    # Assert
    assert page_dir == "ltr"
    assert carousel_dir == "ltr"
    assert promo.is_carousel_visible()
    assert current_alt, "expected the current banner image to carry a non-empty alt attribute"
    assert dots_visible, "expected the pagination dots bottom-left with the active dot as an elongated pill"
    assert active_index >= 0 and promo.is_dot_elongated_pill(active_index), \
        "expected the active dot to render as an elongated pill"
    assert prev_rounded_square and next_rounded_square, \
        "expected the nav arrows to render as rounded squares, not full circles"
    assert prev_semi_transparent and next_semi_transparent, \
        "expected the nav arrows to render semi-transparent, not fully opaque"
    assert arrows_vertically_centered, "expected both nav arrows centered on the image's vertical center"


@allure.epic("GLOBAL")
@allure.feature("Promotional Banners / Ad Slots")
@allure.story("Mirrors correctly in Arabic (RTL)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The promotional banners section mirrors correctly in Arabic (RTL)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129368
@pytest.mark.traceability("GLOBAL-PROMOBANNER-TC-135106")
def test_promo_banners_mirror_correctly_in_arabic_rtl(page):
    # GLOBAL-PROMOBANNER-TC-135106 | PBI 129368
    # Arrange
    promo = HomePromoBannersPage(page)

    # Act
    with allure.step("Navigate to Home Page with Arabic selected"):
        promo.open_home_arabic()

    with allure.step("Scroll to the promotional banners section"):
        promo.scroll_to_section()

    with allure.step("Inspect the rendered AR slide, pagination dots, and nav-arrow mirroring"):
        page_dir = promo.page_direction()
        carousel_dir = promo.carousel_direction()
        current_alt = promo.current_slide_alt_text()
        dots_visible = promo.is_dots_container_visible()
        prev_x = promo.arrow_x_position("prev")
        next_x = promo.arrow_x_position("next")

    # Assert
    assert page_dir == "rtl"
    assert carousel_dir == "rtl"
    assert promo.is_carousel_visible()
    assert current_alt, "expected the current AR banner image to carry a non-empty alt attribute"
    assert prev_x is not None and next_x is not None
    assert prev_x > next_x, "expected the Previous arrow to mirror to the RIGHT side and Next to the LEFT under RTL"
    assert dots_visible, "expected the pagination dots to mirror to the opposite (RTL-correct) side, with no overlap/clipping"
    assert not promo.has_page_horizontal_overflow(), "expected no overlap/clipping (no horizontal page overflow) in RTL"


@allure.epic("GLOBAL")
@allure.feature("Promotional Banners / Ad Slots")
@allure.story("Next-arrow control advances the slider")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking the next-arrow control advances the banner slider")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129368
@pytest.mark.traceability("GLOBAL-PROMOBANNER-TC-135107")
def test_promo_banners_next_arrow_advances_slider(page):
    # GLOBAL-PROMOBANNER-TC-135107 | PBI 129368
    # Arrange
    promo = HomePromoBannersPage(page)

    # Act
    with allure.step("Load Home Page with 3 active banners published"):
        promo.open_home()
        promo.scroll_to_section()

    with allure.step("Note the active dot (slide 1)"):
        slide_1_index = promo.active_dot_index()
        slide_1_alt = promo.current_slide_alt_text()

    with allure.step("Click the right nav arrow"):
        promo.click_next()

    with allure.step("Read the resulting active slide/dot"):
        slide_2_index = promo.active_dot_index()
        slide_2_alt = promo.current_slide_alt_text()

    # Assert
    assert slide_1_index == 0, "expected slide 1's dot active before interaction"
    assert promo.is_dots_container_visible(), "expected the pagination dots visible so slide 1's pill state is observable"
    assert promo.is_dot_elongated_pill(slide_1_index), "expected slide 1's dot to be the elongated pill before the click"
    assert slide_2_index == 1, "expected slide 2 to become active after one Next-arrow click"
    assert slide_2_alt != slide_1_alt, "expected the displayed banner image to change after advancing"
    assert promo.is_dot_elongated_pill(slide_2_index), "expected slide 2's dot to become the elongated pill"
    assert promo.is_dot_small_circle(slide_1_index), "expected slide 1's dot to return to a small circle"


@allure.epic("GLOBAL")
@allure.feature("Promotional Banners / Ad Slots")
@allure.story("Previous-arrow / pagination-dot navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking the previous-arrow / a pagination dot navigates back to a prior slide")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129368
@pytest.mark.traceability("GLOBAL-PROMOBANNER-TC-135108")
def test_promo_banners_prev_arrow_and_dot_navigate_back(page):
    # GLOBAL-PROMOBANNER-TC-135108 | PBI 129368
    # Arrange
    promo = HomePromoBannersPage(page)

    # Act — reach slide 2 first (mirrors the case's "From slide 2" precondition)
    with allure.step("Load Home Page and advance to slide 2"):
        promo.open_home()
        promo.scroll_to_section()
        promo.click_next()
        slide_2_index = promo.active_dot_index()

    with allure.step("Click the left nav arrow"):
        promo.click_prev()
        slide_1_index = promo.active_dot_index()
        slide_1_alt = promo.current_slide_alt_text()

    with allure.step("Click directly on slide 3's pagination dot"):
        promo.click_dot(2)
        slide_3_index = promo.active_dot_index()
        slide_3_alt = promo.current_slide_alt_text()

    # Assert
    assert slide_2_index == 1, "expected slide 2 active before clicking Previous"
    assert slide_1_index == 0, "expected slide 1 to display after clicking Previous"
    assert promo.is_dot_elongated_pill(slide_1_index), "expected slide 1's dot to become the elongated pill"
    assert slide_3_index == 2, "expected slide 3 to display immediately after clicking its pagination dot"
    assert slide_3_alt != slide_1_alt, "expected the displayed banner image to change to slide 3"
    assert promo.is_dot_elongated_pill(slide_3_index), "expected slide 3's dot to become the elongated pill"


@allure.epic("GLOBAL")
@allure.feature("Promotional Banners / Ad Slots")
@allure.story("Configured banner image and EN alt text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The promotional banners section renders with the configured banner image and EN alt text")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129368
@pytest.mark.traceability("GLOBAL-PROMOBANNER-TC-135174")
def test_promo_banners_render_configured_image_and_en_alt_text(page):
    # GLOBAL-PROMOBANNER-TC-135174 | PBI 129368 | UAT (Axis-1 tag recorded
    # here per automation-standards.md — no pytest marker for UAT, see
    # module docstring)
    # Real, live-observed value used below (see Page-Object docstring): the
    # case's example alt text "Qatar Chamber Annual Forum 2026" and image
    # "promo-en.jpg" do not match the actual configured banner on qcdev —
    # the real first configured banner's alt is "Verified by Qatar Chamber
    # — stand out with trusted verification" served from
    # promo-verified-laptop-desktop*.png.
    # Arrange
    promo = HomePromoBannersPage(page)
    expected_alt = "Verified by Qatar Chamber — stand out with trusted verification"

    # Act
    with allure.step("Set browser locale to English and navigate to Home Page"):
        promo.open_home()

    with allure.step("Scroll to the promotional banners section"):
        promo.scroll_to_section()

    with allure.step("Read the configured banner image and its alt attribute"):
        alt_text = promo.real_slide_alt_text(0)
        src = promo.real_slide_src(0)

    # Assert
    assert promo.page_direction() == "ltr"
    assert promo.is_carousel_visible()
    assert src, "expected a configured banner image source"
    assert alt_text == expected_alt, (
        f"expected the live-configured EN alt text {expected_alt!r}, got {alt_text!r}"
    )


@allure.epic("GLOBAL")
@allure.feature("Promotional Banners / Ad Slots")
@allure.story("Configured banner image and AR alt text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The promotional banners section renders with the configured banner image and AR alt text")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129368
@pytest.mark.traceability("GLOBAL-PROMOBANNER-TC-135175")
def test_promo_banners_render_configured_image_and_ar_alt_text(page):
    # GLOBAL-PROMOBANNER-TC-135175 | PBI 129368
    # Real, live-observed value used below (see Page-Object docstring): the
    # case's example image "promo-ar.jpg" does not match the actual
    # configured banner on qcdev; the real first configured banner's AR alt
    # is the live, translated, non-empty value asserted below.
    # Arrange
    promo = HomePromoBannersPage(page)
    expected_alt = "موثّق من غرفة قطر — تميّز بتوثيق يعكس مصداقية عملك"

    # Act
    with allure.step("Set browser locale to Arabic and navigate to Home Page"):
        promo.open_home_arabic()

    with allure.step("Scroll to the promotional banners section"):
        promo.scroll_to_section()

    with allure.step("Read the configured banner image and its alt attribute"):
        alt_text = promo.real_slide_alt_text(0)
        src = promo.real_slide_src(0)

    # Assert
    assert promo.page_direction() == "rtl"
    assert promo.is_carousel_visible()
    assert src, "expected a configured banner image source"
    assert alt_text == expected_alt, (
        f"expected the live-configured AR alt text {expected_alt!r}, got {alt_text!r}"
    )


@allure.epic("GLOBAL")
@allure.feature("Promotional Banners / Ad Slots")
@allure.story("Single active banner displays statically")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A single active banner displays statically without slider/cycling controls")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129368
@pytest.mark.traceability("GLOBAL-PROMOBANNER-TC-135176")
@pytest.mark.skip(
    reason="Precondition requires publishing exactly ONE active promotional "
    "banner in the CMS. qcdev currently has 3 active banners live and no "
    "single-active-banner state exists; Control_Panel/CMS content "
    "configuration is explicit out-of-scope for this Web-only automation "
    "batch (PBI 129368). Pending CMS setup — not fabricated as a pass."
)
def test_promo_banners_single_active_banner_displays_statically(page):
    # GLOBAL-PROMOBANNER-TC-135176 | PBI 129368
    # Arrange
    promo = HomePromoBannersPage(page)

    # Act
    with allure.step("Load Home Page (precondition: exactly one active banner published)"):
        promo.open_home()
        promo.scroll_to_section()

    with allure.step("Inspect the section for arrows/dots"):
        prev_visible = promo.is_arrow_visible("prev")
        next_visible = promo.is_arrow_visible("next")
        dots_visible = promo.is_dots_container_visible()

    # Assert
    assert promo.is_carousel_visible()
    assert promo.real_slide_count() == 1, "expected exactly one active banner configured"
    assert not prev_visible and not next_visible, "expected no arrow icons with a single active banner"
    assert not dots_visible, "expected no dot/pill indicator rendered with a single active banner"


@allure.epic("GLOBAL")
@allure.feature("Promotional Banners / Ad Slots")
@allure.story("Responsive at mobile width")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The promotional banners section is fully responsive at mobile width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129368
@pytest.mark.traceability("GLOBAL-PROMOBANNER-TC-135179")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_promo_banners_responsive_at_mobile_width(page):
    # GLOBAL-PROMOBANNER-TC-135179 | PBI 129368
    # Arrange
    promo = HomePromoBannersPage(page)

    # Act
    with allure.step("Load Home Page at 375x812"):
        promo.open_home()

    with allure.step("Scroll to the promotional banners section"):
        promo.scroll_to_section()

    with allure.step("Measure the banner image against its container, and the page for overflow"):
        image_matches_container = promo.image_width_matches_container()
        has_overflow = promo.has_page_horizontal_overflow()

    # Assert
    assert promo.is_carousel_visible()
    assert image_matches_container, "expected the banner image to scale to its container's full width"
    assert not has_overflow, "expected no horizontal overflow/clipping at mobile width"


@allure.epic("GLOBAL")
@allure.feature("Promotional Banners / Ad Slots")
@allure.story("Responsive at tablet and desktop widths")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The promotional banners section is fully responsive at tablet and desktop widths")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129368
@pytest.mark.traceability("GLOBAL-PROMOBANNER-TC-135180")
def test_promo_banners_responsive_at_tablet_and_desktop_widths(page):
    # GLOBAL-PROMOBANNER-TC-135180 | PBI 129368
    # Resizes the SAME page's viewport twice via Playwright's
    # `page.set_viewport_size()` — the case explicitly resizes to two
    # widths in sequence (768x1024 then 1440x900) rather than being two
    # separate parametrized tests. Arrange/Act/Assert still holds: each
    # width's measurements are taken before its own assertions run below.

    # Arrange
    promo = HomePromoBannersPage(page)

    # Act — tablet width (768x1024)
    with allure.step("Resize to 768x1024 and load Home Page"):
        page.set_viewport_size({"width": 768, "height": 1024})
        promo.open_home()
        promo.scroll_to_section()

    with allure.step("Inspect the section at tablet width"):
        tablet_image_matches_container = promo.image_width_matches_container()
        tablet_has_overflow = promo.has_page_horizontal_overflow()

    # Act — desktop width (1440x900)
    with allure.step("Resize to 1440x900 and reload Home Page"):
        page.set_viewport_size({"width": 1440, "height": 900})
        promo.open_home()
        promo.scroll_to_section()

    with allure.step("Inspect the section at desktop width"):
        desktop_image_matches_container = promo.image_width_matches_container()
        desktop_has_overflow = promo.has_page_horizontal_overflow()

    # Assert
    assert tablet_image_matches_container, "expected no overflow/misalignment at tablet width (768x1024)"
    assert not tablet_has_overflow, "expected no horizontal overflow at tablet width (768x1024)"
    assert desktop_image_matches_container, "expected no overflow/misalignment at desktop width (1440x900)"
    assert not desktop_has_overflow, "expected no horizontal overflow at desktop width (1440x900)"

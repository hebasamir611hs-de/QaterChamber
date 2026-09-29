"""
web/tests/home_featured_event/test_home_featured_event_web.py — Upcoming
Featured Event (PBI 129382 / QC-HOME-006), Web platform.

Source: 18 approved, Automation-tagged, UI-category, Web-platform cases
handed off for this PBI (ADO TC 135634-135650, 135652 — 135651 is not part
of the handed-off set). Control_Panel-tagged cases for this same PBI
(135653-135657) are explicit Phase-2 scope, scripted separately in
test_home_featured_event_control_panel.py.

Per automation-standards.md's Tag-Taxonomy mapping (active/standards.md),
every case here carries `EVENT` (Service axis -> @pytest.mark.event) and
`UI` (Category axis -> @pytest.mark.ui). None of these 18 cases carry the
`Regression` tag, so no test below carries @pytest.mark.regression. Two
tags present on the source cases are deliberately NOT turned into markers:
`HomePage` and `DesignVerified` are not part of the taxonomy documented in
active/standards.md's "Tag Taxonomy" (Axis 1/1b/2/3/4/5) — mirroring this
project's own established precedent (test_home_strategic_direction_web.py,
also a Home-page-section PBI, applies no such marker either). Only
`Bilingual` (present on TC 135646/135647) maps to a registered Axis-5
marker (@pytest.mark.bilingual).

Line-height comparisons below are rounded to the nearest whole pixel before
comparison (`_px()`) — CSS line-height is a continuous, font-metric-derived
value (e.g. Cairo Bold's real line-height computes to 38.1px, not exactly
38px), and rounding sub-pixel rendering noise to the nearest integer is
applied uniformly to every line-height assertion in this file, never
selectively to force a specific case green. Every other property (hex
colors, font-size, font-weight, border-width, padding) is asserted at full
precision with NO rounding/tolerance — where those genuinely differ from
the case's stated Figma spec, the test is scripted to fail honestly (see
the full findings list in the sibling home_featured_event_page.py's
docstring, not repeated in full here).
"""

import allure
import pytest

from config.settings import web_url
from web.pages.home_featured_event.home_featured_event_page import HomeFeaturedEventPage

PBI = "129382"


def _px(value: str) -> int:
    """Rounds a computed CSS pixel string ('38.1px') to the nearest int
    pixel — see module docstring for why this, and only this, is rounded."""
    return round(float(value.replace("px", "")))


def _padding_vh(padding: str) -> tuple:
    """Parses a 2-value CSS padding shorthand ('12px 22px') into
    (vertical, horizontal) ints."""
    parts = padding.replace("px", "").split()
    if len(parts) == 1:
        v = round(float(parts[0]))
        return v, v
    return round(float(parts[0])), round(float(parts[1]))


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Upcoming Events badge")
@allure.severity(allure.severity_level.MINOR)
@allure.title('The "Upcoming Events" badge renders with the Figma-specified colors')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135634")
def test_badge_renders_with_figma_colors(page):
    # EVENT-FEATUREDEVENT-TC-135634 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with a pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Locate the 'Upcoming Events' badge and inspect its style"):
        style = featured_event.badge_style()

    # Assert
    assert featured_event.is_section_visible()
    assert style["colorHex"] == "#A66F43"
    assert style["backgroundColorHex"] == "#F6F0EC"
    assert style["borderWidth"] == "1px"
    assert style["borderColorHex"] == "#D7BEAA", (
        f"expected badge border #D7BEAA, got {style['borderColorHex']!r} "
        "(live product value — see Page-Object docstring)"
    )


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Section heading typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title('The section heading "What\'s Coming Up" renders with the Figma-specified typography and color')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135635")
def test_heading_renders_with_figma_typography(page):
    # EVENT-FEATUREDEVENT-TC-135635 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with a pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Locate the heading text and inspect its typography"):
        heading_text = featured_event.heading_text()
        style = featured_event.heading_style()

    # Assert
    assert heading_text == "What's Coming Up"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "30px"
    assert _px(style["lineHeight"]) == 38
    assert style["colorHex"] == "#1D1D1B"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Section description copy and typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The section description renders with the exact copy and Figma-specified typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135636")
def test_description_copy_and_typography(page):
    # EVENT-FEATUREDEVENT-TC-135636 | PBI 129382
    expected_copy = (
        "Explore Qatar Chamber's upcoming events, business delegations, "
        "forums, and meetings designed to connect companies, investors, "
        "and partners across Qatar's business community."
    )
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with a pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Locate the section description and inspect its copy and typography"):
        desc_text = featured_event.description_text()
        style = featured_event.description_style()

    # Assert
    assert desc_text == expected_copy, (
        f"expected the exact case copy, got {desc_text!r} — live page uses a "
        "typographic apostrophe (') where the case specifies a straight one (')"
    )
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "400"
    assert style["fontSize"] == "18px", f"expected 18px, got {style['fontSize']!r} (live product value)"
    assert _px(style["lineHeight"]) == 28, f"expected 28px, got {style['lineHeight']!r} (live product value)"
    assert style["colorHex"] == "#7C7B7B", f"expected #7C7B7B, got {style['colorHex']!r} (live product value)"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("View All CTA pill button")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The "View All" CTA button renders per the Figma pill-button spec')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135637")
def test_view_all_cta_pill_button_spec(page):
    # EVENT-FEATUREDEVENT-TC-135637 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with a pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Locate the 'View All' button and inspect its style"):
        style = featured_event.cta_style("top")
        has_icon = featured_event.cta_has_icon("top")

    # Assert
    assert style["backgroundColorHex"] == "#911731"
    assert style["colorHex"] == "#FFFFFF"
    assert style["borderRadius"] == "9999px"
    assert has_icon, "expected an arrow-up-right icon inside the View All button"
    vertical, horizontal = _padding_vh(style["padding"])
    assert vertical == 12
    assert horizontal == 18, f"expected 18px horizontal padding, got {horizontal}px (live product value)"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Event category badges pill style")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The event category badges render with the Figma-specified pill style")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135638")
def test_category_badges_pill_style(page):
    # EVENT-FEATUREDEVENT-TC-135638 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with a pinned event tagged 'Chamber Events' and 'Business'"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Locate the two category badges and inspect their style"):
        count = featured_event.category_tag_count()
        labels = [featured_event.category_tag_text(i) for i in range(count)]
        styles = [featured_event.category_tag_style(i) for i in range(count)]

    # Assert
    assert count == 2
    assert labels == ["Chamber Events", "Business"]
    for style in styles:
        assert style["backgroundColorHex"] == "#F6F6F6", (
            f"expected #F6F6F6, got {style['backgroundColorHex']!r} (live product value)"
        )
        assert style["colorHex"] == "#6C6C6B"
        assert style["borderWidth"] == "1px"
        assert style["borderColorHex"] == "#DEDEDD"
        assert style["borderRadius"] == "9999px"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Pinned event title typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The pinned event title renders with the Figma-specified typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135639")
def test_event_title_typography(page):
    # EVENT-FEATUREDEVENT-TC-135639 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with the pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Locate the event title text and inspect its typography"):
        title_text = featured_event.title_text()
        style = featured_event.title_style()

    # Assert
    assert title_text == "Meeting business delegation of the Novgorod Region's government"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "24px"
    assert _px(style["lineHeight"]) == 32, f"expected 32px, got {style['lineHeight']!r} (live product value)"
    assert style["colorHex"] == "#1D1D1B"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Date/Time/Location icon-buttons")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Date, Time, and Location icon-buttons render as maroon 48px circles per Figma")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135640")
def test_meta_icon_buttons_are_maroon_48px_circles(page):
    # EVENT-FEATUREDEVENT-TC-135640 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with a pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Locate the Date, Time, and Location icon-buttons and measure each"):
        styles = [featured_event.meta_icon_style(i) for i in range(3)]

    # Assert
    for style in styles:
        assert style["borderRadius"] == "50%"
        assert style["backgroundColorHex"] == "#911731"
        assert style["width"] == 48, f"expected 48px diameter, got {style['width']}px (live product value)"
        assert style["height"] == 48, f"expected 48px diameter, got {style['height']}px (live product value)"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Date/Time/Location labels and values")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Date/Time/Location labels and values render with the Figma-specified colors and fonts")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135641")
def test_meta_label_and_value_typography(page):
    # EVENT-FEATUREDEVENT-TC-135641 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with the pinned event dated 19 November 2025, 09:30 A.M."):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Locate the Date label/value and inspect both"):
        label_text = featured_event.date_label_text()
        value_text = featured_event.date_value_text()
        label_style = featured_event.date_label_style()
        value_style = featured_event.date_value_style()

    # Assert
    assert label_text == "Date"
    assert value_text == "19 November 2025"
    # Label: Cairo Regular 14px/22px #A8A8A7
    assert label_style["fontWeight"] == "400"
    assert label_style["fontSize"] == "14px", f"expected 14px, got {label_style['fontSize']!r} (live product value)"
    assert _px(label_style["lineHeight"]) == 22, (
        f"expected 22px, got {label_style['lineHeight']!r} (live product value)"
    )
    assert label_style["colorHex"] == "#A8A8A7", (
        f"expected #A8A8A7, got {label_style['colorHex']!r} (live product value)"
    )
    # Value: Cairo Semibold 16px/24px #4A4A49
    assert value_style["fontWeight"] == "600"
    assert value_style["fontSize"] == "16px"
    assert _px(value_style["lineHeight"]) == 24, (
        f"expected 24px, got {value_style['lineHeight']!r} (live product value)"
    )
    assert value_style["colorHex"] == "#4A4A49", (
        f"expected #4A4A49, got {value_style['colorHex']!r} (live product value)"
    )


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Two-column section layout spacing")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The section layout matches the Figma two-column spacing spec")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135642")
def test_section_two_column_layout_spacing(page):
    # EVENT-FEATUREDEVENT-TC-135642 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with a pinned event at desktop resolution 1920x1080"):
        featured_event.open_home()

    with allure.step("Measure the section's outer padding"):
        vertical_padding = featured_event.section_vertical_padding()
        gutter = featured_event.section_outer_gutter()

    with allure.step("Measure the gap between the image column and the details column"):
        gap = featured_event.column_gap()

    # Assert
    assert vertical_padding["paddingTop"] == "64px"
    assert vertical_padding["paddingBottom"] == "64px"
    assert gutter["left"] == 300, f"expected 300px, got {gutter['left']}px (live product value)"
    assert gutter["right"] == 300, f"expected 300px, got {gutter['right']}px (live product value)"
    assert gap == "48px"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Event image container")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The event image renders at the Figma-specified height within a 16px-rounded container")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135643")
def test_event_image_container_spec(page):
    # EVENT-FEATUREDEVENT-TC-135643 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with a pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Measure the image height and container corner radius"):
        style = featured_event.image_container_style()

    # Assert
    assert style["borderRadius"] == "16px"
    assert style["height"] == 350, f"expected 350px, got {style['height']}px (live product value)"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Divider line between detail rows")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The divider line between event detail rows renders with the Figma-specified color and thickness")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135644")
def test_divider_color_and_thickness(page):
    # EVENT-FEATUREDEVENT-TC-135644 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with a pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Inspect the divider line's color and thickness"):
        style = featured_event.divider_style()

    # Assert
    assert style["backgroundColorHex"] == "#E9DBD0", (
        f"expected #E9DBD0, got {style['backgroundColorHex']!r} (live product value)"
    )
    assert style["height"] == 1


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Section absent when no event pinned")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Upcoming Event section does not render on the Home Page when no event is pinned")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135645")
@pytest.mark.skip(
    reason="Precondition requires emptying the Pin Configuration in the Liferay "
    "CMS. A real event IS currently pinned/active on qcdev and this Web-only "
    "automation batch carries no Control_Panel credentials this session "
    "(TEST_USER/TEST_PASSWORD are unset in .env) to unpin it — pending CMS "
    "access, not fabricated as a pass."
)
def test_section_absent_when_no_event_pinned(page):
    # EVENT-FEATUREDEVENT-TC-135645 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Ensure no event is pinned in Pin Configuration (precondition)"):
        pass  # requires Control_Panel access — see skip reason

    with allure.step("Load the Home Page"):
        featured_event.open(web_url("/home"))

    with allure.step("Inspect the area where the Upcoming Event section would appear"):
        section_absent = featured_event.is_section_absent()

    # Assert
    assert section_absent, "expected no Upcoming Event section, no placeholder, no broken layout gap"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Arabic (RTL) rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Upcoming Event section renders correctly in Arabic (RTL) layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135646")
def test_section_renders_correctly_in_arabic_rtl(page):
    # EVENT-FEATUREDEVENT-TC-135646 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Set the site language to Arabic and load the Home Page with a pinned event"):
        featured_event.open_home_arabic()
        featured_event.scroll_to_section()

    with allure.step("Inspect column order, text alignment, and overflow"):
        page_dir = featured_event.page_direction()
        section_dir = featured_event.section_direction()
        media_x = featured_event.media_x()
        details_x = featured_event.details_x()
        has_overflow = featured_event.has_page_horizontal_overflow()

    # Assert
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert featured_event.is_section_visible()
    assert media_x is not None and details_x is not None
    assert media_x > details_x, "expected the image column to mirror to the RIGHT under RTL"
    assert not has_overflow, "expected no visual overlap or clipping in RTL"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("English (LTR) rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Upcoming Event section renders correctly in English (LTR) layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135647")
def test_section_renders_correctly_in_english_ltr(page):
    # EVENT-FEATUREDEVENT-TC-135647 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Set the site language to English and load the Home Page with a pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Inspect column order and text alignment"):
        page_dir = featured_event.page_direction()
        section_dir = featured_event.section_direction()
        media_x = featured_event.media_x()
        details_x = featured_event.details_x()

    # Assert
    assert page_dir == "ltr"
    assert section_dir == "ltr"
    assert featured_event.is_section_visible()
    assert media_x is not None and details_x is not None
    assert media_x < details_x, "expected the image column on the LEFT, details on the RIGHT under LTR"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Responsive at mobile viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Upcoming Event section is fully responsive at a 375px mobile viewport")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135648")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_responsive_at_mobile_375(page):
    # EVENT-FEATUREDEVENT-TC-135648 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Set the browser viewport to 375px width and load the Home Page"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Inspect the layout of the image and details columns"):
        stacked = featured_event.is_stacked_vertically()
        has_overflow = featured_event.has_page_horizontal_overflow()

    # Assert
    assert featured_event.is_section_visible()
    assert stacked, "expected the image and details columns to stack vertically at 375px"
    assert not has_overflow, "expected no overlapping or clipped content at 375px"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Responsive at tablet viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Upcoming Event section is fully responsive at a 768px tablet viewport")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135649")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_responsive_at_tablet_768(page):
    # EVENT-FEATUREDEVENT-TC-135649 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Set the browser viewport to 768px width and load the Home Page"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Inspect the layout of the image and details columns"):
        has_overflow = featured_event.has_page_horizontal_overflow()
        media_box = featured_event.media_box()
        details_box = featured_event.details_box()

    # Assert
    assert featured_event.is_section_visible()
    assert not has_overflow, "expected no horizontal scroll at 768px"
    assert media_box and details_box, "expected both columns present at 768px"
    no_overlap = (media_box["x"] + media_box["width"] <= details_box["x"] + 1) or \
        (details_box["x"] + details_box["width"] <= media_box["x"] + 1) or \
        (media_box["y"] + media_box["height"] <= details_box["y"] + 1)
    assert no_overlap, "expected the image and details columns not to overlap at 768px"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Loading placeholder while fetching")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A loading placeholder displays while the pinned event data is being fetched")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135650")
def test_loading_placeholder_while_fetching(page):
    # EVENT-FEATUREDEVENT-TC-135650 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Throttle network to slow 3G"):
        featured_event.throttle_network_slow_3g()

    with allure.step("Load the Home Page"):
        featured_event.start_navigating_to_home_without_waiting()

    with allure.step("Observe the Upcoming Event section area during the fetch"):
        skeleton_seen = featured_event.is_skeleton_visible()
        featured_event.wait_for(featured_event.SECTION, timeout=30000)
        section_loaded = featured_event.is_section_visible()

    # Assert
    assert skeleton_seen, (
        "expected a loading skeleton/placeholder in the section area during the "
        "fetch — none exists in the live markup (this section is server-rendered "
        "with the event data already in the initial HTML; see Page-Object docstring)"
    )
    assert section_loaded, "expected the real content to replace the placeholder once loaded"


@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.story("Pagination indicator with a single pinned event")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The pagination indicator below the pinned event shows a single active state when only one event is pinned")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129382
@pytest.mark.traceability("EVENT-FEATUREDEVENT-TC-135652")
def test_pagination_single_active_state(page):
    # EVENT-FEATUREDEVENT-TC-135652 | PBI 129382
    # Arrange
    featured_event = HomeFeaturedEventPage(page)

    # Act
    with allure.step("Load the Home Page with exactly one pinned event"):
        featured_event.open_home()
        featured_event.scroll_to_section()

    with allure.step("Locate the pagination indicator below the event card"):
        pagination_present = featured_event.pagination_indicator_present()

    # Assert
    assert featured_event.is_section_visible()
    assert not pagination_present, (
        "expected no pagination/dots indicator implying additional unpinned "
        "items — none exists in the live markup with a single pinned event"
    )

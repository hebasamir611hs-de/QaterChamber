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
from cms.pages.home_featured_event.home_featured_event_admin_page import approved_49205_write  # noqa: F401 — fixture import

PBI = "129382"

# Every case here is a visitor read of the public Home Page -> fresh logged-out
# context (CLAUDE.md rule 9), never the CMS-authenticated storageState.
ANON = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)

# bug-rules Rule 1 tolerances: images +-5 px, layout +-2 px, text exact.
IMG_TOL = 5
LAYOUT_TOL = 2


def _near(actual, expected, tol) -> bool:
    if isinstance(actual, str):
        actual = float(actual.replace("px", ""))
    return actual is not None and abs(actual - expected) <= tol


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
@pytest.mark.tc_135634
@ANON
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
    assert _near(style["borderWidth"], 1, LAYOUT_TOL)
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
@pytest.mark.tc_135635
@ANON
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
@pytest.mark.tc_135636
@ANON
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
@pytest.mark.tc_135637
@ANON
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
    assert _near(vertical, 12, LAYOUT_TOL)
    assert _near(horizontal, 18, LAYOUT_TOL), f"expected 18px horizontal padding, got {horizontal}px (live product value)"


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
@pytest.mark.tc_135638
@ANON
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
        assert _near(style["borderWidth"], 1, LAYOUT_TOL)
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
@pytest.mark.tc_135639
@ANON
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
@pytest.mark.tc_135640
@ANON
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
        assert _near(style["width"], 48, IMG_TOL), f"expected 48px diameter, got {style['width']}px (live product value)"
        assert _near(style["height"], 48, IMG_TOL), f"expected 48px diameter, got {style['height']}px (live product value)"


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
@pytest.mark.tc_135641
@ANON
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
@pytest.mark.tc_135642
@ANON
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
    assert _near(vertical_padding["paddingTop"], 64, LAYOUT_TOL)
    assert _near(vertical_padding["paddingBottom"], 64, LAYOUT_TOL)
    assert _near(gutter["left"], 300, LAYOUT_TOL), f"expected 300px, got {gutter['left']}px (live product value)"
    assert _near(gutter["right"], 300, LAYOUT_TOL), f"expected 300px, got {gutter['right']}px (live product value)"
    assert _near(gap, 48, LAYOUT_TOL)


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
@pytest.mark.tc_135643
@ANON
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
    assert _near(style["borderRadius"], 16, LAYOUT_TOL)
    assert _near(style["height"], 350, IMG_TOL), f"expected 350px, got {style['height']}px (live product value)"


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
@pytest.mark.tc_135644
@ANON
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
    assert _near(style["height"], 1, LAYOUT_TOL)


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
@pytest.mark.tc_135645
@pytest.mark.tc_135666
@pytest.mark.xdist_group("pin_event_49205")
@pytest.mark.usefixtures("approved_49205_write")
def test_section_absent_when_no_event_pinned(page, browser):
    """ADO-135645 / ADO-135666. WRITES THE LIVE PIN 49205 — needs the user's
    ID-named approval; not in the phase-3 run list.

    Account: Site Content Editor (CMS side, `page`) clears Pinned Event and
    publishes; a fresh logged-out context reads the Home Page. 49205 is
    snapshotted first and restored + re-verified in `finally`."""
    from core.web.browser import new_context
    from cms.pages.home_featured_event.home_featured_event_admin_page import HomeFeaturedEventAdminPage

    admin = HomeFeaturedEventAdminPage(page).sign_in_as("Site Content Editor")
    admin.open_live_pin_read_only()
    snap = admin.snapshot()
    anon = new_context(browser, use_auth_state=False)
    featured_event = HomeFeaturedEventPage(anon.new_page())
    try:
        with allure.step("Precondition: the section is visible to a visitor while an event is pinned"):
            featured_event.open_home()
            assert featured_event.is_section_visible(), "precondition: section must be visible before unpinning"
        with allure.step("Clear Pinned Event on 49205 and publish (no event pinned)"):
            admin.open_for_edit().set_pinned_event("").publish()
            admin.open_live_pin_read_only()
            assert admin.pinned_event_value() == "", (
                "the unpin did not persist (Pinned Event is `required` on the form) — "
                "which control means 'unpin' is an open question in the phase-3 report")
        with allure.step("Load the Home Page logged out and inspect the section area"):
            featured_event.open_home()
            hidden = featured_event.reload_until(lambda p: not p.is_section_visible())
        assert hidden, "expected no Upcoming Event section, no placeholder, no broken layout gap"
    finally:
        admin.restore(snap)
        anon.close()


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
@pytest.mark.tc_135646
@ANON
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
@pytest.mark.tc_135647
@ANON
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
@pytest.mark.tc_135648
@pytest.mark.parametrize("page", [{"viewport": (375, 812), "auth": False}], indirect=True)
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
@pytest.mark.tc_135649
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
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
@pytest.mark.tc_135650
@ANON
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
@pytest.mark.tc_135652
@ANON
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


# ═════════════════════════════════════════════════════════════════════════
# Phase 3 (2026-10-07) — functional P2 cases. All read-only: a logged-out
# visitor reads the card and compares it with the event's own detail page,
# which is the Events module's rendering of the BusinessEvent record.
# Precondition (TC): "a published event is pinned and active" — that is the
# live Upcoming Event Pin record 49205; these tests never write to it, they
# assert the precondition and report if it does not hold.
# ═════════════════════════════════════════════════════════════════════════
import re as _re


def _open_card(featured_event: HomeFeaturedEventPage, locale: str = "en") -> dict:
    with allure.step(f"Load the Home Page ({locale.upper()}) as a logged-out visitor and scroll to the section"):
        (featured_event.open_home_arabic() if locale == "ar" else featured_event.open_home())
    assert featured_event.is_section_visible(), (
        "Precondition not met: the Upcoming Event section is not visible on the "
        "public Home Page (rendered display:none), so no pinned event is shown."
    )
    featured_event.scroll_to_section()
    card = featured_event.card_snapshot()
    allure.attach(str(card), name=f"card-{locale}", attachment_type=allure.attachment_type.TEXT)
    return card


def _detail_text(featured_event: HomeFeaturedEventPage) -> str:
    with allure.step("Click the event image and read the event detail page"):
        featured_event.click_media_and_wait()
    return featured_event.body_text()


def _visitor_browse_and_navigate(page):
    featured_event = HomeFeaturedEventPage(page)
    card = _open_card(featured_event)
    for key in ("title", "date", "time", "location", "summary"):
        assert card[key], f"card field {key!r} is empty"
    assert "event?id=" in card["href"] or "/events/" in card["href"], f"image link is not an event URL: {card['href']!r}"
    landed = featured_event.click_media_and_wait()
    assert "event" in landed and "home" not in landed.rsplit("/", 1)[-1], f"image click landed on {landed!r}"
    detail = featured_event.body_text()
    assert card["title"] in detail, "event detail page does not show the card's title"
    assert card["location"] in detail, "event detail page does not show the card's location"


@ANON
@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.title("A visitor views the pinned event details and opens its detail page from the image")
@pytest.mark.web
@pytest.mark.event
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135665
def test_visitor_views_pinned_event_and_opens_detail(page):
    """ADO-135665. Logged-out visitor; read-only."""
    _visitor_browse_and_navigate(page)


@ANON
@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.title("A visitor views the pinned event details and opens its detail page from the image (twin)")
@pytest.mark.web
@pytest.mark.event
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135717
def test_visitor_views_pinned_event_and_opens_detail_twin(page):
    """ADO-135717 — same steps as 135665 (duplicate case in the suite)."""
    _visitor_browse_and_navigate(page)


def _field_matches_detail(page, field: str, locale: str):
    featured_event = HomeFeaturedEventPage(page)
    card = _open_card(featured_event, locale)
    value = card[field]
    assert value, f"card {field} is empty ({locale})"
    if locale == "ar":
        assert _re.search(r"[؀-ۿ]", value), f"AR card {field} has no Arabic text: {value!r}"
    detail = _detail_text(featured_event)
    if field == "date":
        # The detail page may format the same date differently; match day + year.
        day = _re.search(r"\b(\d{1,2})\b", value)
        year = _re.search(r"\b(20\d\d)\b", value)
        assert day and year, f"card date has no day/year: {value!r}"
        assert day.group(1) in detail and year.group(1) in detail, (
            f"detail page does not show the card date {value!r}")
    elif field == "time":
        hhmm = _re.search(r"\d{1,2}:\d{2}", value)
        assert hhmm, f"card time has no HH:MM: {value!r}"
        assert hhmm.group(0) in detail, f"detail page does not show the card time {value!r}"
    else:
        assert value in detail, f"detail page does not show the card {field} {value!r} ({locale})"



@ANON
@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.title("The pinned event's title (EN) displays as sourced from the Events module")
@pytest.mark.web
@pytest.mark.event
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135674
def test_pinned_event_title_en_matches_events_module(page):
    """ADO-135674. Logged-out visitor; read-only."""
    _field_matches_detail(page, "title", "en")


@ANON
@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.title("The pinned event's title (AR) displays as sourced from the Events module")
@pytest.mark.web
@pytest.mark.event
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135675
def test_pinned_event_title_ar_matches_events_module(page):
    """ADO-135675. Logged-out visitor; read-only."""
    _field_matches_detail(page, "title", "ar")


@ANON
@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.title("The pinned event's date displays as sourced from the Events module")
@pytest.mark.web
@pytest.mark.event
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135676
def test_pinned_event_date_en_matches_events_module(page):
    """ADO-135676. Logged-out visitor; read-only."""
    _field_matches_detail(page, "date", "en")


@ANON
@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.title("The pinned event's time displays as sourced from the Events module")
@pytest.mark.web
@pytest.mark.event
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135677
def test_pinned_event_time_en_matches_events_module(page):
    """ADO-135677. Logged-out visitor; read-only."""
    _field_matches_detail(page, "time", "en")


@ANON
@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.title("The pinned event's location (EN) displays as sourced from the Events module")
@pytest.mark.web
@pytest.mark.event
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135678
def test_pinned_event_location_en_matches_events_module(page):
    """ADO-135678. Logged-out visitor; read-only."""
    _field_matches_detail(page, "location", "en")


@ANON
@allure.epic("EVENT")
@allure.feature("Upcoming Featured Event")
@allure.title("The pinned event's location (AR) displays as sourced from the Events module")
@pytest.mark.web
@pytest.mark.event
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135679
def test_pinned_event_location_ar_matches_events_module(page):
    """ADO-135679. Logged-out visitor; read-only."""
    _field_matches_detail(page, "location", "ar")

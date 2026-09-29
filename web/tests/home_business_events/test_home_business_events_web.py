"""
web/tests/home_business_events/test_home_business_events_web.py —
Business Events Section (PBI 129383 / QC-HOME-007), Web platform.

Source: 17 approved, Automation-tagged, UI-category, Web-platform cases handed
off for this PBI (ADO TC 135720-135736). No Control_Panel-tagged cases exist
for this PBI in this batch (see the sibling
test_home_business_events_control_panel.py skeleton — untouched).

Known real-environment findings surfaced while scripting these (full detail
in web/pages/home_business_events/home_business_events_page.py's docstring,
which documents the live CLI/script-extraction evidence for every value
below). Per this batch's convention, the case's stated Figma tokens are kept
as the asserted target throughout — a live mismatch is scripted to FAIL
HONESTLY, never quietly re-targeted at the observed value:
  - TC 135724: the section background is a solid maroon color with two subtle
    linear-gradient overlays — NOT a photo, and no decorative circular
    graphic elements exist anywhere in the section's DOM.
  - TC 135725: badge background/border do not match the stated tokens (no
    border exists on the badge at all); text color and pill shape do match.
  - TC 135726: heading copy/weight/color match; font-size (32px, not 30px)
    and line-height (38.4px, not 38px) do not.
  - TC 135727: description copy/weight match; font-size (16px, not 18px),
    line-height (25.6px, not 28px), and color (82%-opacity white, not solid
    #EDEDED) do not.
  - TC 135728: "All" tab's active bg/text match exactly; inactive tabs' text
    color matches but they carry no outline/border at all; the white pill
    container is real but its padding is 5px, not 4px.
  - TC 135729: the live CTA's text is "All Events", not "Explore All Events";
    only the tab-bar-adjacent (top) variant is visible at 1920x1080, not a
    below-grid variant; its border color doesn't match the stated token.
  - TC 135730: card images measure ~250x167px with 0px corner radius, not the
    stated 312x168px / 8px radius.
  - TC 135731: badge border-radius (6px) and pill styling match exactly;
    background color does not match the stated token.
  - TC 135732: title copy/weight/color match; font-size (17px, not 16px) and
    line-height (22.95px, not 24px) do not.
  - TC 135733/135734: icons measure 16x16px, not the stated 18x18px; text
    color/font-family match, font-size/line-height do not.
  - TC 135735: CONFIRMED LIVE — the 2x2 grid's vertical+horizontal seams are
    real (per-card border-left/border-top, both exactly 1px at the grid
    midpoint); their color is 16%-opacity white, not the stated 20%.
  - TC 135736: CONFIRMED LIVE — a real active-pill/inactive-dot pagination
    indicator exists and matches the stated shapes closely; exact px sizes
    and the inactive outline color do not match the stated tokens.
  - TC 135720/135721: CONFIRMED LIVE, genuine passes — the section, badge,
    heading, description, and 3-tab filter bar all render on load, and the
    whole section re-renders correctly mirrored under Arabic/RTL with real
    Arabic copy in every field.

Data-setup note (TC 135722/135723/135735/135736): publishing new events, or
an event with a 200-character title/Location, is a Control_Panel/CMS action
out of scope for this Web-only UI batch (see Page Object docstring for full
detail):
  - TC 135735/135736 need no synthetic setup at all — the live qcdev
    environment already carries 6 published events (a real 2x2 first page +
    a real second page), which already satisfies both cases' stated
    preconditions exactly as given.
  - TC 135722/135723 inject a genuine 200-character, real-word (space
    -separated, not one unbroken string) title/Location string directly into
    an already-rendered card via `page.evaluate()`, then measure the actual
    browser-computed layout that results. This exercises the real, shipped
    CSS truncation/wrap contract at the true 200-char boundary without
    needing CMS access to publish the data — the assertions still fail
    honestly if that live CSS does not behave as expected.
"""

import allure
import pytest

from web.pages.home_business_events.home_business_events_page import HomeBusinessEventsPage

PBI = "129383"

EXPECTED_BADGE_TEXT = "Business Events"
EXPECTED_HEADING_TEXT = "Explore Qatar Chamber Events"
EXPECTED_DESCRIPTION_TEXT = (
    "Explore Qatar Chamber's upcoming events, business meetings, forums, and "
    "delegations that connect Qatar's business community locally and globally."
)
EXPECTED_TABS = ["All", "Chamber Events", "Global Events"]

# Live-confirmed Arabic copy (AR homepage, TC 135721).
AR_BADGE_TEXT = "فعاليات الأعمال"
AR_HEADING_TEXT = "استكشف فعاليات غرفة قطر"
AR_DESCRIPTION_TEXT = (
    "تعرّف على فعاليات غرفة قطر القادمة، ولقاءات الأعمال، والمنتديات، والوفود "
    "التجارية التي تربط مجتمع الأعمال في قطر بالفرص المحلية والدولية."
)

# Genuine, real-word 200-character boundary strings (space-separated, not one
# unbroken run of characters — see module docstring's Data-setup note: an
# unbroken 200-char string defeats whitespace-based wrapping and produces
# HORIZONTAL overflow instead of the vertical-clamp/wrap behavior a real,
# sentence-like 200-char title or Location value would actually trigger).
TITLE_200 = (
    "Qatar Chamber International Business Delegation Forum for Economic "
    "Cooperation Summit on Public Private Partnership Investment "
    "Opportunities Across the Qatar National Vision Trade Council Annual "
    "Networking Event Program "
)[:200]
LOCATION_200 = (
    "Qatar Chamber Head Office Conference Hall Complex Building Number "
    "Fourteen West Bay Business District Diplomatic Area near Doha Corniche "
    "Waterfront Second Floor Meeting Rooms A and B Doha State of Qatar "
)[:200]


# ── TC 135720 — Section renders with tag/heading/description/tab bar ───────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Section renders on Home Page load")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Business Events section renders with the section tag, heading, description, and filter tab bar")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135720")
def test_section_renders_with_tag_heading_description_and_tab_bar(page):
    # EVENT-BUSINESSEVENTS-TC-135720 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Home Page (EN locale)"):
        be.open_home()

    with allure.step("Scroll to the Business Events section"):
        be.scroll_to_section()

    with allure.step("Read the badge, heading, description, and filter tab labels"):
        badge_text = be.badge_text()
        heading_text = be.heading_text()
        description_text = be.description_text()
        tab_texts = be.tab_texts()

    # Assert
    assert be.is_section_visible()
    assert badge_text == EXPECTED_BADGE_TEXT
    assert heading_text == EXPECTED_HEADING_TEXT
    assert description_text == EXPECTED_DESCRIPTION_TEXT
    assert tab_texts == EXPECTED_TABS, f"expected filter tabs {EXPECTED_TABS}, got {tab_texts}"


# ── TC 135721 — Arabic (RTL) mirrored layout (Bilingual) ────────────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Renders mirrored and correctly in Arabic (RTL)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Business Events section renders correctly in Arabic with a mirrored layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135721")
def test_renders_mirrored_in_arabic_rtl(page):
    # EVENT-BUSINESSEVENTS-TC-135721 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Switch to the Arabic Home Page"):
        be.open_home_arabic()

    with allure.step("Scroll to the Business Events section"):
        be.scroll_to_section()

    with allure.step("Read the section's direction, copy, and tab labels"):
        page_dir = be.page_direction()
        section_dir = be.section_direction()
        badge_text = be.badge_text()
        heading_text = be.heading_text()
        description_text = be.description_text()
        head_align = be.heading_style()["textAlign"]

    # Assert
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert badge_text == AR_BADGE_TEXT
    assert heading_text == AR_HEADING_TEXT
    assert description_text == AR_DESCRIPTION_TEXT
    assert head_align == "start", (
        f"expected the heading to use the logical 'start' text-align (right-aligned under RTL), got {head_align!r}"
    )


# ── TC 135722 — 200-char title truncates with ellipsis, no layout break ────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Card title truncation at max length")
@allure.severity(allure.severity_level.MINOR)
@allure.title("An event card with a 200-character title truncates instead of breaking the card layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135722")
def test_max_length_title_truncates_without_breaking_card_layout(page):
    # EVENT-BUSINESSEVENTS-TC-135722 | PBI 129383
    # Publishing an event with a 200-char title is a Control_Panel/CMS action
    # out of scope for this Web-only batch (see module docstring's Data-setup
    # note) — a genuine 200-char, real-word title is injected into an
    # already-rendered live card, then the resulting real layout is measured.
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to Home Page - Business Events section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Record the card's box before the title change"):
        box_before = be.card_box(0)

    with allure.step("Set the card's title to a 200-character value and measure the resulting layout"):
        metrics = be.inject_card_title(TITLE_200, 0)
        box_after = be.card_box(0)

    # Assert
    assert len(TITLE_200) == 200
    assert metrics["afterW"] == metrics["beforeW"], "expected the title box width to stay unchanged"
    assert metrics["afterH"] == metrics["beforeH"], "expected the title box height to stay clamped/unchanged"
    assert metrics["scrollWidth"] == metrics["clientWidth"], (
        f"expected no horizontal overflow, got scrollWidth={metrics['scrollWidth']} "
        f"vs clientWidth={metrics['clientWidth']}"
    )
    assert metrics["scrollHeight"] > metrics["clientHeight"], (
        "expected the 200-char title to overflow vertically (proving truncation is actually clipping something)"
    )
    assert round(box_after["width"]) == round(box_before["width"]), "expected the card width to stay unchanged"
    assert round(box_after["height"]) == round(box_before["height"]), "expected the card height to stay unchanged"


# ── TC 135723 — 200-char Location does not overflow the card ───────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Card Location handling at max length")
@allure.severity(allure.severity_level.MINOR)
@allure.title("An event card with a 200-character Location value displays without overflowing the card")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135723")
def test_max_length_location_does_not_overlap_meta_row(page):
    # EVENT-BUSINESSEVENTS-TC-135723 | PBI 129383
    # Same data-setup approach as TC 135722 — see module docstring.
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to Home Page - Business Events section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Set the card's Location to a 200-character value and measure the resulting layout"):
        result = be.inject_card_location(LOCATION_200, 0)

    # Assert
    assert len(LOCATION_200) == 200
    meta_before, meta_after = result["meta_box_before"], result["meta_box_after"]
    assert meta_before == meta_after, "expected the date/time meta row to stay in place, unaffected by the Location change"
    loc_after = result["loc_wrap_box_after"]
    meta_bottom = meta_after["y"] + meta_after["height"]
    assert loc_after["y"] >= meta_bottom, (
        f"expected the Location row (top={loc_after['y']}) not to overlap the date/time row "
        f"(bottom={meta_bottom})"
    )


# ── TC 135724 — Section background gradient + decorative circles ───────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Section background style")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Business Events section background renders with the exact maroon-gradient photo overlay and decorative circular graphics")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135724")
def test_section_background_gradient_and_decorative_graphics(page):
    # EVENT-BUSINESSEVENTS-TC-135724 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Inspect the section's background container"):
        style = be.section_style()
        decorative_circles = page.locator(
            "section.qc-home-business-events svg[class*='circle'], "
            "section.qc-home-business-events [class*='decorative'], "
            "section.qc-home-business-events [class*='circle']"
        ).count()

    # Assert
    assert be.is_section_visible()
    assert "url(" in (style["backgroundImage"] or ""), (
        f"expected a photo background-image with an 80% opacity maroon overlay, got {style['backgroundImage']!r}"
    )
    assert decorative_circles > 0, "expected decorative translucent circular graphics positioned per the Figma frame"


# ── TC 135725 — "Business Events" badge exact style ─────────────────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Badge style")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The "Business Events" badge renders with the exact Figma-specified style')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135725")
def test_badge_exact_style(page):
    # EVENT-BUSINESSEVENTS-TC-135725 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Inspect the badge above the heading"):
        text = be.badge_text()
        style = be.badge_style()

    # Assert
    assert text == EXPECTED_BADGE_TEXT
    assert style["color"] == "rgb(255, 255, 255)"
    assert style["backgroundColor"] == "rgba(29, 29, 27, 0.2)", (
        f"expected badge background rgba(29,29,27,0.2), got {style['backgroundColor']!r}"
    )
    assert style["border"] == "1px solid rgba(145, 23, 49, 0.3)", (
        f"expected badge border 1px solid rgba(145,23,49,0.3), got {style['border']!r}"
    )
    assert style["borderRadius"] == "9999px", "expected a fully rounded pill shape"


# ── TC 135726 — Section heading exact copy/font/size/color ─────────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Heading text and typography")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The section heading renders with the exact Figma copy, font, size, and color")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135726")
def test_heading_exact_copy_and_typography(page):
    # EVENT-BUSINESSEVENTS-TC-135726 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Inspect the heading below the badge"):
        text = be.heading_text()
        style = be.heading_style()

    # Assert
    assert text == EXPECTED_HEADING_TEXT
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "30px", f"expected heading font-size 30px, got {style['fontSize']!r}"
    assert style["lineHeight"] == "38px", f"expected heading line-height 38px, got {style['lineHeight']!r}"
    assert style["color"] == "rgb(255, 255, 255)"


# ── TC 135727 — Section description exact copy/font/size/color ─────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Description text and typography")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The section description renders with the exact Figma copy, font, size, and color")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135727")
def test_description_exact_copy_and_typography(page):
    # EVENT-BUSINESSEVENTS-TC-135727 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Inspect the description text below the heading"):
        text = be.description_text()
        style = be.description_style()

    # Assert
    assert text == EXPECTED_DESCRIPTION_TEXT
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "400"
    assert style["fontSize"] == "18px", f"expected description font-size 18px, got {style['fontSize']!r}"
    assert style["lineHeight"] == "28px", f"expected description line-height 28px, got {style['lineHeight']!r}"
    assert style["color"] == "rgb(237, 237, 237)", (  # #EDEDED
        f"expected description color #EDEDED, got {style['color']!r}"
    )


# ── TC 135728 — Filter tab bar active/inactive/container styling ───────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Filter tab bar style")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The filter tab bar renders with the exact Figma active/inactive/container styling")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135728")
def test_filter_tab_bar_exact_styling(page):
    # EVENT-BUSINESSEVENTS-TC-135728 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section with default state (All active)"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Inspect the filter tab bar"):
        all_active = be.is_tab_active("all")
        all_style = be.tab_style("all")
        chamber_style = be.tab_style("chamber")
        global_style = be.tab_style("global")
        container_style = be.tablist_style()

    # Assert
    assert all_active, "expected the 'All' tab to be active by default"
    assert all_style["backgroundColor"] == "rgb(145, 23, 49)", (  # #911731
        f"expected 'All' tab background #911731, got {all_style['backgroundColor']!r}"
    )
    assert all_style["color"] == "rgb(255, 255, 255)"
    assert all_style["borderRadius"] == "9999px"
    for label, style in (("Chamber Events", chamber_style), ("Global Events", global_style)):
        assert style["backgroundColor"] in ("rgba(0, 0, 0, 0)", "transparent", "rgb(255, 255, 255)"), (
            f"expected {label} tab transparent/white background, got {style['backgroundColor']!r}"
        )
        assert style["color"] == "rgb(74, 74, 74)", (  # #4A4A49
            f"expected {label} tab text color #4A4A49, got {style['color']!r}"
        )
        assert style["border"] not in ("0px none rgb(74, 74, 74)", "0px none rgba(0, 0, 0, 0)"), (
            f"expected {label} tab to have a pill outline border, got {style['border']!r}"
        )
    assert container_style["backgroundColor"] == "rgb(255, 255, 255)"
    assert container_style["padding"] == "4px", f"expected tab bar container padding 4px, got {container_style['padding']!r}"


# ── TC 135729 — "Explore All Events" CTA distinct from the tab bar ─────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Explore All Events CTA style")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The "Explore All Events" CTA button renders with the exact Figma style and icon, distinct from the filter tab bar')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135729")
def test_explore_all_events_cta_style(page):
    # EVENT-BUSINESSEVENTS-TC-135729 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step('Inspect the "Explore All Events" button below the card grid'):
        text = be.cta_top_text()
        style = be.cta_top_style()
        has_icon = be.cta_top_has_icon()
        cta_box = be.cta_top_box()
        tab_box = be.tablist_box()

    # Assert
    assert text == "Explore All Events", f"expected CTA text 'Explore All Events', got {text!r}"
    assert style["backgroundColor"] == "rgb(255, 255, 255)"
    assert style["border"] == "1px solid rgb(222, 222, 221)", (  # #DEDEDD
        f"expected CTA border 1px solid #DEDEDD, got {style['border']!r}"
    )
    assert style["color"] == "rgb(74, 74, 74)"  # #4A4A49
    assert has_icon, "expected an arrow-up-right icon on the CTA button"
    assert style["borderRadius"] == "9999px"
    assert cta_box["y"] > tab_box["y"] + tab_box["height"], (
        "expected the CTA button to be positioned below the filter tab bar, not beside it"
    )


# ── TC 135730 — Event card image dimensions and corner radius ──────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Card image geometry")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Event card images render at the exact Figma dimensions and corner radius")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135730")
def test_card_image_dimensions_and_radius(page):
    # EVENT-BUSINESSEVENTS-TC-135730 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Inspect the image area of the first event card"):
        box = be.card_image_box(0)
        style = be.card_image_style(0)

    # Assert
    assert round(box["width"]) == 312, f"expected card image width 312px, got {box['width']}"
    assert round(box["height"]) == 168, f"expected card image height 168px, got {box['height']}"
    assert style["borderRadius"] == "8px", f"expected card image corner radius 8px, got {style['borderRadius']!r}"


# ── TC 135731 — Event card category/sector badge style ─────────────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Card category/sector badge style")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Event card category and sector badges render with the exact Figma style")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135731")
def test_card_category_and_sector_badge_style(page):
    # EVENT-BUSINESSEVENTS-TC-135731 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step('Locate the card for "Qatar Investment Forum for International Partnership Opportunities"'):
        titles = [be.card_title_text(i) for i in range(be.total_card_count())]
        target_index = titles.index("Qatar Investment Forum for International Partnership Opportunities")

    with allure.step("Inspect its category and sector badges"):
        category_text = be.card_category_badge_text(target_index)
        sector_text = be.card_sector_badge_text(target_index)
        category_style = be.card_category_badge_style(target_index)
        sector_style = be.card_sector_badge_style(target_index)

    # Assert
    assert category_text == "Global Events"
    assert sector_text == "Investment"
    for label, style in (("category", category_style), ("sector", sector_style)):
        assert style["color"] == "rgb(255, 255, 255)"
        assert style["backgroundColor"] == "rgba(29, 29, 27, 0.2)", (
            f"expected {label} badge background rgba(29,29,27,0.2), got {style['backgroundColor']!r}"
        )
        assert style["borderRadius"] == "6px", f"expected {label} badge corner radius 6px, got {style['borderRadius']!r}"


# ── TC 135732 — Event card title exact font/size/color ──────────────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Card title typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The event card title renders with the exact Figma font, size, and color")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135732")
def test_card_title_exact_typography(page):
    # EVENT-BUSINESSEVENTS-TC-135732 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Inspect the first event card's title text"):
        style = be.card_title_style(0)

    # Assert
    assert style["color"] == "rgb(255, 255, 255)"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "16px", f"expected card title font-size 16px, got {style['fontSize']!r}"
    assert style["lineHeight"] == "24px", f"expected card title line-height 24px, got {style['lineHeight']!r}"


# ── TC 135733 — Event card date/time icon+text exact style ─────────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Card date/time icon and text style")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The event card date and time icons and text render with the exact Figma style")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135733")
def test_card_date_time_icon_and_text_style(page):
    # EVENT-BUSINESSEVENTS-TC-135733 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step('Locate the card showing date "22 April 2025" and time "10:30 A.M."'):
        be.open_home()
        be.scroll_to_section()
        dates = [be.card_date_text(i) for i in range(be.total_card_count())]
        target_index = dates.index("22 April 2025")

    with allure.step("Inspect the date and time icon/text pairs"):
        date_icon_box = be.card_date_icon_box(target_index)
        time_icon_box = be.card_time_icon_box(target_index)
        time_text = be.card_time_text(target_index)
        date_text_style = be.card_meta_text_style(target_index, 0)
        time_text_style = be.card_meta_text_style(target_index, 1)

    # Assert
    assert time_text == "10:30 A.M."
    for label, box in (("calendar", date_icon_box), ("clock", time_icon_box)):
        assert round(box["width"]) == 18 and round(box["height"]) == 18, (
            f"expected the {label} icon at 18x18px, got {box}"
        )
    for label, style in (("date", date_text_style), ("time", time_text_style)):
        assert style["color"] == "rgb(255, 255, 255)", f"expected {label} text white, got {style['color']!r}"
        assert "Cairo" in style["fontFamily"]
        assert style["fontSize"] == "14px", f"expected {label} text font-size 14px, got {style['fontSize']!r}"
        assert style["lineHeight"] == "22px", f"expected {label} text line-height 22px, got {style['lineHeight']!r}"


# ── TC 135734 — Event card location icon+text exact style ──────────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Card location icon and text style")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The event card location icon and text render with the exact Figma style")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135734")
def test_card_location_icon_and_text_style(page):
    # EVENT-BUSINESSEVENTS-TC-135734 | PBI 129383
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step('Locate a card showing location "Qatar Chamber - Lusail (4th floor)"'):
        be.open_home()
        be.scroll_to_section()
        locations = [be.card_location_text(i) for i in range(be.total_card_count())]
        target_index = next(i for i, loc in enumerate(locations) if "Lusail" in loc)

    with allure.step("Inspect the location icon/text pair"):
        icon_box = be.card_location_icon_box(target_index)
        text_style = be.card_location_text_style(target_index)
        location_text = be.card_location_text(target_index)

    # Assert
    assert "Lusail (4th floor)" in location_text
    assert round(icon_box["width"]) == 18 and round(icon_box["height"]) == 18, (
        f"expected the marker-pin icon at 18x18px, got {icon_box}"
    )
    assert text_style["color"] == "rgb(255, 255, 255)"
    assert "Cairo" in text_style["fontFamily"]
    assert text_style["fontSize"] == "14px", f"expected location text font-size 14px, got {text_style['fontSize']!r}"
    assert text_style["lineHeight"] == "22px", f"expected location text line-height 22px, got {text_style['lineHeight']!r}"


# ── TC 135735 — 2x2 grid divider lines ──────────────────────────────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("2x2 grid divider lines")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The divider lines in the 2x2 card grid render with the exact Figma style")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135735")
def test_grid_divider_lines_style(page):
    # EVENT-BUSINESSEVENTS-TC-135735 | PBI 129383
    # Publishing exactly 4 events is a Control_Panel/CMS action out of scope
    # here — the live qcdev environment already shows a real 2x2 grid on the
    # first page (4 of its 6 published events), which already satisfies this
    # case's precondition with zero synthetic setup (see module docstring).
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section (first page = 4 cards, a real 2x2 grid)"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Inspect the divider lines between the 4 cards"):
        page_1_count = be.page_1_card_count()
        vertical = be.card_border(1)  # 2nd card (top-right) carries the vertical seam
        horizontal = be.card_border(2)  # 3rd card (bottom-left) carries the horizontal seam

    # Assert
    assert page_1_count == 4, f"expected a 2x2 grid (4 cards) on the first page, got {page_1_count}"
    assert vertical["borderLeftWidth"] == "1px", f"expected a 1px vertical divider, got {vertical['borderLeftWidth']!r}"
    assert vertical["borderLeftColor"] == "rgba(255, 255, 255, 0.2)", (
        f"expected divider color rgba(255,255,255,0.2), got {vertical['borderLeftColor']!r}"
    )
    assert horizontal["borderTopWidth"] == "1px", f"expected a 1px horizontal divider, got {horizontal['borderTopWidth']!r}"
    assert horizontal["borderTopColor"] == "rgba(255, 255, 255, 0.2)", (
        f"expected divider color rgba(255,255,255,0.2), got {horizontal['borderTopColor']!r}"
    )


# ── TC 135736 — Carousel pagination indicator style ─────────────────────────
@allure.epic("EVENT")
@allure.feature("Business Events Section")
@allure.story("Carousel pagination indicator style")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The carousel pagination indicator renders with the exact Figma active/inactive styling")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129383
@pytest.mark.traceability("EVENT-BUSINESSEVENTS-TC-135736")
def test_pagination_indicator_style(page):
    # EVENT-BUSINESSEVENTS-TC-135736 | PBI 129383
    # Publishing 5+ events is a Control_Panel/CMS action out of scope here —
    # the live qcdev environment already carries 6 published events (more
    # than the 4-per-page default), which already produces a real, second
    # pagination page with zero synthetic setup (see module docstring).
    # Arrange
    be = HomeBusinessEventsPage(page)

    # Act
    with allure.step("Navigate to the Business Events section (6 events -> default 4 cards + pagination)"):
        be.open_home()
        be.scroll_to_section()

    with allure.step("Inspect the pagination indicator below the card grid"):
        dot_count = be.dot_count()
        active_box = be.dot_box(0)
        active_style = be.dot_style(0)
        inactive_box = be.dot_box(1)
        inactive_style = be.dot_style(1)

    # Assert
    assert dot_count == 2, f"expected a 2-page pagination indicator, got {dot_count} page(s)"
    assert be.is_dot_active(0), "expected the first page to be active by default"
    assert round(active_box["width"]) == 36 and round(active_box["height"]) == 12, (
        f"expected the active page as a 36x12px pill, got {active_box}"
    )
    assert active_style["backgroundColor"] == "rgb(255, 255, 255)"
    assert round(inactive_box["width"]) == 12 and round(inactive_box["height"]) == 12, (
        f"expected the inactive page as a 12x12px dot, got {inactive_box}"
    )
    assert inactive_style["border"] == "1px solid rgb(205, 150, 162)", (  # #CD96A2
        f"expected the inactive dot outlined in #CD96A2, got {inactive_style['border']!r}"
    )

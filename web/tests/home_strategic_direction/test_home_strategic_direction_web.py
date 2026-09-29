"""
web/tests/home_strategic_direction/test_home_strategic_direction_web.py —
Strategic Direction Section (PBI 129381 / QC-HOME-005), Web platform.

Source: 23 approved, Automation-tagged, UI-category, Web-platform cases handed
off for this PBI (ADO TC 135515-135537). Control_Panel-tagged cases for this
same PBI are explicit out-of-scope for this run and are NOT in this file (see
the sibling test_home_strategic_direction_control_panel.py skeleton).

Priority note: the injected batch gave an explicit priority for TC 135522-
135537 (P2/P3/P4 as marked per case) but NOT for TC 135515-135521 — those 7
are the same kind of literal Figma-token (color/font/px) assertion as the
explicitly-P4 TC 135522-135527 in the same visual-QA cluster, so this batch
treats them as P4 too (Allure severity MINOR) rather than guessing a higher
priority the source data never stated.

Known real-environment findings surfaced while scripting these (full detail
in web/pages/home_strategic_direction/home_strategic_direction_page.py's
docstring, which documents the live CLI-extraction/inspection evidence for
every value below). Per this batch's instruction, the case's stated Figma
tokens are kept as the asserted target throughout — a live mismatch is
scripted to FAIL HONESTLY, never quietly re-targeted at the observed value:
  - TC 135515: section's real rendered background (read from its gradient's
    first color stop, since its own background-color is transparent by
    design) is #F9F2EC, not the case's stated #F6F0EC.
  - TC 135516: badge text color #A66F43 matches exactly; badge background is
    transparent (not #F6F0EC); badge border computes to #E4D0BC, not #D7BEAA.
  - TC 135517: text/weight/size match; computed line-height is 37.5px, not
    the stated 38px; color #1D1D1B matches exactly.
  - TC 135518: text/weight/size match; computed line-height is 25.6px, not
    the stated 24px; color computes to #6C6C6B, not the stated #7C7B7B.
  - TC 135519: card background #E9DBD0 and border-radius 16px match exactly;
    border color-channel matches #A66F43 but is rendered at 45% alpha
    (`rgba(166,111,67,0.45)`, not the plain solid `rgb(...)` the case
    implies); card width computes to 508px, not the stated 516px.
  - TC 135520: weight/size match; computed line-height is 28px, not the
    stated 30px; color #A66F43 matches exactly.
  - TC 135521: text matches verbatim; weight/size match; computed line-height
    is 22.4px vs. the stated 22px; color computes to #4A423B, not the stated
    #343432.
  - TC 135522: arrows are circular and opaque white (both match); measured
    44x44px, not the stated 40x40px; border computes to #E4D0BC, not the
    stated #E9DBD0.
  - TC 135523: no discrete "N of 3" indicator exists live — the closest
    structural analog is two static decorative "peek" strips. Their
    border-radius (bottom corners 16px, top corners 0) matches the case's
    stated shape exactly; their fill colors (#DDC9B6/#D3BCA6) do not match
    the case's stated #D7BEAA/#B3845F.
  - TC 135524: mandala opacity computes to 0.3 (30%), not the stated ~20%;
    it does animate/rotate (confirmed non-"none" animation-name).
  - TC 135525: top/bottom padding (80px) matches exactly; the effective
    left/right content gap measures 336px, not the stated 300px.
  - TC 135526: carousel container measures 620px wide (not 636px); the
    arrow-to-card gap measures ~12px (not 20px).
  - TC 135527: pillar icon measures 64x64px (not 72x72px); card padding is
    22px top/bottom (not 20px; 24px left/right does match); the icon-to-text
    gap computes to a 8px/20px row/column pair, not a single 16px.
  - TC 135528/135529/135530/135531/135533: CONFIRMED LIVE, genuine passes —
    real copy with no truncation, exactly one active card at a time, and
    working Next/Previous navigation with a real 0.42s timed cross-fade.
  - TC 135532: CONFIRMED LIVE — the two decorative "peek" strips are
    byte-identical in color and width before and after every Next-arrow
    click (checked across all 3 pillars); there is no observable "1-of-3 ->
    2-of-3" progress state to advance. Scripted per the case's literal
    expected result; will fail honestly, not a framework defect.
  - TC 135534: CONFIRMED LIVE (AR) — RTL direction, Arabic copy on every
    field, and the two-column layout genuinely swaps sides (text block moves
    from the left to the right half of the section, the carousel from right
    to left).
  - TC 135535/135536/135537: CONFIRMED LIVE — no horizontal overflow at
    375x812, 768x1024, or 1920x1080; the 1920px spacing tokens (padding/
    carousel width) carry the same TC 135525/135526 mismatches noted above.
"""

import allure
import pytest

from web.pages.home_strategic_direction.home_strategic_direction_page import HomeStrategicDirectionPage

PBI = "129381"

EXPECTED_BADGE_TEXT = "Strategic Pillars"
EXPECTED_HEADING_TEXT = "Our Strategic Direction"
EXPECTED_DESCRIPTION_TEXT = (
    "Discover the principles that guide Qatar Chamber’s role in supporting "
    "the business community, strengthening economic growth, and shaping a "
    "competitive future for Qatar."
)
EXPECTED_VISION_TITLE = "Vision"
EXPECTED_VISION_DESC = (
    "To achieve global leadership among chambers of commerce by advancing "
    "Qatar National Vision 2030, empowering the private sector, and "
    "positioning Qatar as a gateway for local and international business "
    "opportunities."
)

# Live-confirmed Arabic copy (AR homepage, TC 135534) — used as the expected
# value per this batch's "prefer the real observed live value" instruction.
AR_BADGE_TEXT = "الركائز الاستراتيجية"
AR_HEADING_TEXT = "توجهنا الاستراتيجي"
AR_DESCRIPTION_TEXT = (
    "تعرّف على المبادئ التي توجه دور غرفة قطر في دعم مجتمع الأعمال، "
    "وتعزيز النمو الاقتصادي، والمساهمة في بناء مستقبل أكثر تنافسية لدولة قطر."
)
AR_VISION_TITLE = "الرؤية"
AR_VISION_DESC = (
    "تحقيق الريادة العالمية بين غرف التجارة على مستوى المنطقة والعالم، من خلال "
    "دعم رؤية قطر الوطنية 2030، وتمكين القطاع الخاص من النمو والمنافسة، "
    "وترسيخ مكانة قطر كبوابة رئيسية للفرص التجارية المحلية والدولية."
)


# ── TC 135515 — Section background color ───────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Section background color")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Strategic Direction section renders with the Figma-specified background color")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135515")
def test_section_background_color(page):
    # ABOUT-STRATEGICDIRECTION-TC-135515 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the Strategic Direction section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the section's rendered background color"):
        bg_hex = sd.section_background_hex()

    # Assert
    assert sd.is_section_visible()
    assert bg_hex == "#F6F0EC", f"expected section background #F6F0EC, got {bg_hex!r}"


# ── TC 135516 — "Strategic Pillars" badge style ─────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Badge style")
@allure.severity(allure.severity_level.MINOR)
@allure.title('The "Strategic Pillars" badge renders with its Figma-specified color, background, and border')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135516")
def test_badge_style(page):
    # ABOUT-STRATEGICDIRECTION-TC-135516 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the badge's text and computed style"):
        text = sd.badge_text()
        style = sd.badge_style()

    # Assert
    assert text == EXPECTED_BADGE_TEXT
    assert style["color"] == "rgb(166, 111, 67)"  # #A66F43
    assert style["backgroundColor"] == "rgb(246, 240, 236)", (  # #F6F0EC
        f"expected badge background #F6F0EC, got {style['backgroundColor']!r}"
    )
    assert style["border"] == "1px solid rgb(215, 190, 170)", (  # #D7BEAA
        f"expected badge border 1px solid #D7BEAA, got {style['border']!r}"
    )


# ── TC 135517 — Heading text and typography ─────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Heading text and typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title('The section heading reads "Our Strategic Direction" in the Figma-specified typography')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135517")
def test_heading_text_and_typography(page):
    # ABOUT-STRATEGICDIRECTION-TC-135517 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the heading's text and computed style"):
        text = sd.heading_text()
        style = sd.heading_style()

    # Assert
    assert text == EXPECTED_HEADING_TEXT
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "30px"
    assert style["lineHeight"] == "38px", f"expected line-height 38px, got {style['lineHeight']!r}"
    assert style["color"] == "rgb(29, 29, 27)"  # #1D1D1B


# ── TC 135518 — Description text and typography ─────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Description text and typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The section description renders the exact Figma-specified copy and typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135518")
def test_description_text_and_typography(page):
    # ABOUT-STRATEGICDIRECTION-TC-135518 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the description's text and computed style"):
        text = sd.description_text()
        style = sd.description_style()

    # Assert
    assert text == EXPECTED_DESCRIPTION_TEXT
    assert style["fontWeight"] == "400"
    assert style["fontSize"] == "16px"
    assert style["lineHeight"] == "24px", f"expected line-height 24px, got {style['lineHeight']!r}"
    assert style["color"] == "rgb(124, 123, 123)", (  # #7C7B7B
        f"expected description color #7C7B7B, got {style['color']!r}"
    )


# ── TC 135519 — Pillar card container style ─────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Pillar card container style")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The active pillar card renders with its Figma-specified background, border, radius, shadow, and width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135519")
def test_pillar_card_container_style(page):
    # ABOUT-STRATEGICDIRECTION-TC-135519 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the active pillar card's computed style"):
        style = sd.active_card_style()

    # Assert
    assert style["backgroundColor"] == "rgb(233, 219, 208)"  # #E9DBD0
    assert style["border"] == "1px solid rgb(166, 111, 67)", (  # #A66F43
        f"expected card border 1px solid #A66F43, got {style['border']!r}"
    )
    assert style["borderRadius"] == "16px"
    assert style["boxShadow"] != "none", "expected a drop shadow on the pillar card"
    assert style["width"] == "516px", f"expected card width 516px, got {style['width']!r}"


# ── TC 135520 — Pillar title typography ─────────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Pillar title typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title('The "Vision" pillar title renders in the Figma-specified typography')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135520")
def test_pillar_title_typography(page):
    # ABOUT-STRATEGICDIRECTION-TC-135520 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the active (Vision) pillar's title text and computed style"):
        title_text = sd.active_card_title_text()
        style = sd.active_card_title_style()

    # Assert
    assert title_text == EXPECTED_VISION_TITLE
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "20px"
    assert style["lineHeight"] == "30px", f"expected line-height 30px, got {style['lineHeight']!r}"
    assert style["color"] == "rgb(166, 111, 67)"  # #A66F43


# ── TC 135521 — Vision pillar description text and typography ──────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Vision pillar description text and typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Vision pillar's description renders the exact Figma-specified copy and typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135521")
def test_vision_pillar_description_text_and_typography(page):
    # ABOUT-STRATEGICDIRECTION-TC-135521 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the active (Vision) pillar's description text and computed style"):
        desc_text = sd.active_card_description_text()
        style = sd.active_card_description_style()

    # Assert
    assert desc_text == EXPECTED_VISION_DESC
    assert style["fontWeight"] == "400"
    assert style["fontSize"] == "14px"
    assert style["lineHeight"] == "22px", f"expected line-height 22px, got {style['lineHeight']!r}"
    assert style["color"] == "rgb(52, 52, 50)", (  # #343432
        f"expected Vision description color #343432, got {style['color']!r}"
    )


# ── TC 135522 — Nav arrow style (P4) ─────────────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Carousel nav-arrow style")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The carousel nav arrows render as the Figma-specified circular, white, bordered controls")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135522")
def test_nav_arrow_style(page):
    # ABOUT-STRATEGICDIRECTION-TC-135522 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Measure both nav arrows and read their computed style"):
        next_size = sd.arrow_box_size("next")
        prev_size = sd.arrow_box_size("prev")
        next_style = sd.arrow_style("next")

    # Assert
    assert round(next_size["width"]) == 40 and round(next_size["height"]) == 40, (
        f"expected 40x40px arrows, got {next_size}"
    )
    assert round(prev_size["width"]) == 40 and round(prev_size["height"]) == 40, (
        f"expected 40x40px arrows, got {prev_size}"
    )
    assert sd.is_arrow_circular("next") and sd.is_arrow_circular("prev"), "expected fully circular arrows"
    assert next_style["backgroundColor"] == "rgb(255, 255, 255)"
    assert next_style["border"] == "1px solid rgb(233, 219, 208)", (  # #E9DBD0
        f"expected arrow border 1px solid #E9DBD0, got {next_style['border']!r}"
    )


# ── TC 135523 — Progress indicator style (P4) ───────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Progress indicator style")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The progress indicator renders with the Figma-specified stroke colors and corner radii")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135523")
def test_progress_indicator_style(page):
    # ABOUT-STRATEGICDIRECTION-TC-135523 | PBI 129381
    # The live DOM's closest structural analog to a "progress indicator" is
    # the pair of decorative stacked-card "peek" strips behind the active
    # card (see Page Object docstring) — asserted against per the case's
    # literal stated tokens.
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read both progress-indicator strips' computed style"):
        peek_1 = sd.peek_style(1)
        peek_2 = sd.peek_style(2)

    # Assert
    assert peek_1["borderRadius"] == "0px 0px 16px 16px", "expected bottom corners 16px, top corners 0"
    assert peek_2["borderRadius"] == "0px 0px 16px 16px", "expected bottom corners 16px, top corners 0"
    assert peek_1["backgroundColor"] == "rgb(215, 190, 170)", (  # #D7BEAA
        f"expected first stroke color #D7BEAA, got {peek_1['backgroundColor']!r}"
    )
    assert peek_2["backgroundColor"] == "rgb(179, 132, 95)", (  # #B3845F
        f"expected second stroke color #B3845F, got {peek_2['backgroundColor']!r}"
    )


# ── TC 135524 — Mandala background graphic (P4) ─────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Decorative background graphic")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The decorative Mandala graphic animates at the Figma-specified opacity without obscuring the foreground")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135524")
def test_mandala_background_graphic(page):
    # ABOUT-STRATEGICDIRECTION-TC-135524 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the Mandala graphic's computed style"):
        style = sd.mandala_style()
        is_animating = sd.is_mandala_animating()

    # Assert
    assert style["opacity"] == "0.2", f"expected ~20% opacity (0.2), got {style['opacity']!r}"
    assert is_animating, "expected the Mandala graphic to be rotating/animating"
    assert sd.is_section_visible()
    assert sd.is_arrow_visible("next") and sd.is_arrow_visible("prev"), (
        "expected the nav arrows to remain visible/interactable over the decorative graphic"
    )
    assert sd.is_active_card_visible(), "expected the pillar card to remain visible over the decorative graphic"


# ── TC 135525 — Section padding at 1920px (P4) ──────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Section padding at desktop width")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The section renders with the Figma-specified padding on a 1920px viewport")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135525")
def test_section_padding_at_1920_viewport(page):
    # ABOUT-STRATEGICDIRECTION-TC-135525 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page (1920x1080 default viewport) and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Measure the section's top/bottom padding and effective left/right content gap"):
        padding = sd.section_padding()
        gaps = sd.section_content_side_gaps()

    # Assert
    assert padding["top"] == 80 and padding["bottom"] == 80, f"expected 80px top/bottom padding, got {padding}"
    assert round(gaps["left"]) == 300, f"expected 300px left content gap, got {gaps['left']}"
    assert round(gaps["right"]) == 300, f"expected 300px right content gap, got {gaps['right']}"


# ── TC 135526 — Carousel container geometry (P4) ────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Carousel container geometry")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The carousel container (arrow + card + arrow) matches the Figma-specified width and gap")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135526")
def test_carousel_container_geometry(page):
    # ABOUT-STRATEGICDIRECTION-TC-135526 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Measure the carousel container's width and the arrow-to-card gaps"):
        box = sd.carousel_box()
        prev_gap = sd.arrow_to_card_gap("prev")
        next_gap = sd.arrow_to_card_gap("next")

    # Assert
    assert round(box["width"]) == 636, f"expected carousel container width 636px, got {box['width']}"
    assert round(prev_gap) == 20, f"expected a 20px gap between the previous arrow and the card, got {prev_gap}"
    assert round(next_gap) == 20, f"expected a 20px gap between the next arrow and the card, got {next_gap}"


# ── TC 135527 — Pillar icon and header-row geometry (P4) ────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Pillar icon and header-row geometry")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The pillar icon and its header row match the Figma-specified size, padding, and gap")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135527")
def test_pillar_icon_and_header_row_geometry(page):
    # ABOUT-STRATEGICDIRECTION-TC-135527 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Measure the active pillar's icon and read the card's padding/gap"):
        icon_size = sd.active_card_icon_size()
        card_style = sd.active_card_style()

    # Assert
    assert round(icon_size["width"]) == 72 and round(icon_size["height"]) == 72, (
        f"expected a 72x72px pillar icon, got {icon_size}"
    )
    assert card_style["paddingTop"] == "20px", f"expected 20px top padding, got {card_style['paddingTop']!r}"
    assert card_style["paddingBottom"] == "20px", f"expected 20px bottom padding, got {card_style['paddingBottom']!r}"
    assert card_style["paddingLeft"] == "24px"
    assert card_style["paddingRight"] == "24px"
    assert card_style["gap"] == "16px", f"expected a 16px icon-to-text gap, got {card_style['gap']!r}"


# ── TC 135528 — Copy matches Figma exactly, no truncation/placeholder (Regression) ──
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Copy correctness — no truncation or placeholder text")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The badge, heading, description, and Vision-pillar copy match the Figma-verified strings exactly")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135528")
def test_copy_matches_figma_exactly_no_truncation(page):
    # ABOUT-STRATEGICDIRECTION-TC-135528 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the badge, heading, description, and Vision-pillar copy"):
        badge_text = sd.badge_text()
        heading_text = sd.heading_text()
        description_text = sd.description_text()
        pillar_title = sd.active_card_title_text()
        pillar_desc = sd.active_card_description_text()

    # Assert
    assert badge_text == EXPECTED_BADGE_TEXT
    assert heading_text == EXPECTED_HEADING_TEXT
    assert description_text == EXPECTED_DESCRIPTION_TEXT
    assert pillar_title == EXPECTED_VISION_TITLE
    assert pillar_desc == EXPECTED_VISION_DESC
    for label, text in (
        ("badge", badge_text), ("heading", heading_text), ("description", description_text),
        ("pillar title", pillar_title), ("pillar description", pillar_desc),
    ):
        assert text and "lorem" not in text.lower() and "..." not in text, (
            f"expected non-truncated, non-placeholder {label} text, got {text!r}"
        )


# ── TC 135529 — Only one pillar card visible at a time (Regression) ────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Only one pillar card is visible at a time")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Exactly one pillar card (Vision) is visible on initial load — Mission/Objectives are not simultaneously visible")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135529")
def test_only_one_pillar_card_visible_at_a_time(page):
    # ABOUT-STRATEGICDIRECTION-TC-135529 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read which pillar card(s) are currently visible (computed opacity > 0)"):
        visible_titles = sd.visible_card_titles()
        total_cards = sd.card_count()

    # Assert
    assert total_cards == 3, f"expected 3 pillar cards in the deck, got {total_cards}"
    assert visible_titles == [EXPECTED_VISION_TITLE], (
        f"expected only Vision visible on initial load, got {visible_titles}"
    )


# ── TC 135530 — Right arrow advances Vision -> Mission (Regression) ────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Next-arrow control advances the pillar carousel")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking the right nav arrow advances the pillar carousel from Vision to Mission")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135530")
def test_next_arrow_advances_vision_to_mission(page):
    # ABOUT-STRATEGICDIRECTION-TC-135530 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Note the active pillar before interaction"):
        before = sd.active_card_title_text()

    with allure.step("Click the right (next) nav arrow"):
        sd.click_next()
        after = sd.active_card_title_text()

    # Assert
    assert before == EXPECTED_VISION_TITLE, "expected Vision active before interaction"
    assert after == "Mission", f"expected Mission active after one Next-arrow click, got {after!r}"


# ── TC 135531 — Left arrow returns Mission -> Vision ────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Previous-arrow control returns to the prior pillar")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking the left nav arrow from Mission returns the pillar carousel to Vision")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135531")
def test_prev_arrow_returns_mission_to_vision(page):
    # ABOUT-STRATEGICDIRECTION-TC-135531 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act — reach Mission first (mirrors the case's "From Mission" precondition)
    with allure.step("Navigate to Home Page and advance to Mission"):
        sd.open_home()
        sd.scroll_to_section()
        sd.click_next()
        mid = sd.active_card_title_text()

    with allure.step("Click the left (previous) nav arrow"):
        sd.click_prev()
        after = sd.active_card_title_text()

    # Assert
    assert mid == "Mission", "expected Mission active before clicking Previous"
    assert after == EXPECTED_VISION_TITLE, f"expected Vision active after clicking Previous, got {after!r}"


# ── TC 135532 — Progress indicator updates 1-of-3 -> 2-of-3 ─────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Progress indicator updates when advancing")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The progress indicator updates from 1-of-3 to 2-of-3 when advancing from Vision to Mission")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135532")
def test_progress_indicator_updates_on_advance(page):
    # ABOUT-STRATEGICDIRECTION-TC-135532 | PBI 129381
    # CONFIRMED LIVE: the two "peek" strips (the closest structural analog to
    # a progress indicator — see Page Object docstring) are identical in
    # color/width before and after every Next-arrow click, across all 3
    # pillars. This test is scripted per the case's literal expected result
    # and is expected to fail honestly against that real gap, not a
    # framework defect.
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Snapshot the progress indicator before advancing"):
        before = sd.peek_snapshot()

    with allure.step("Click the next arrow to advance from Vision (1-of-3) to Mission (2-of-3)"):
        sd.click_next()

    with allure.step("Snapshot the progress indicator after advancing"):
        after = sd.peek_snapshot()

    # Assert
    assert sd.active_card_title_text() == "Mission"
    assert before != after, (
        "expected the progress indicator to change when advancing from pillar 1-of-3 to 2-of-3, "
        f"but it was identical before and after: {before}"
    )


# ── TC 135533 — Visible transition/animation on card switch ────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Visible transition when switching pillar cards")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Switching pillar cards plays a visible transition/animation rather than an instant hard-cut")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135533")
def test_visible_transition_on_card_switch(page):
    # ABOUT-STRATEGICDIRECTION-TC-135533 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page and scroll to the section"):
        sd.open_home()
        sd.scroll_to_section()

    with allure.step("Read the active card's transition duration"):
        duration = sd.card_transition_duration_seconds()

    # Assert
    assert duration > 0, (
        f"expected a real, timed transition (> 0s) when switching pillar cards, got {duration}s "
        "(an instant hard-cut)"
    )


# ── TC 135534 — Arabic RTL mirroring (Bilingual, Regression) ───────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Renders mirrored and correctly in Arabic (RTL)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Strategic Direction section renders in Arabic with a fully mirrored, right-to-left layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135534")
def test_renders_mirrored_in_arabic_rtl(page):
    # ABOUT-STRATEGICDIRECTION-TC-135534 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Navigate to Home Page with Arabic selected"):
        sd.open_home_arabic()

    with allure.step("Scroll to the Strategic Direction section"):
        sd.scroll_to_section()

    with allure.step("Read the section's direction, copy, and two-column layout order"):
        page_dir = sd.page_direction()
        section_dir = sd.section_direction()
        badge_text = sd.badge_text()
        heading_text = sd.heading_text()
        description_text = sd.description_text()
        pillar_title = sd.active_card_title_text()
        pillar_desc = sd.active_card_description_text()
        text_x = sd.text_block_x()
        carousel_x = sd.carousel_x()

    # Assert
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert badge_text == AR_BADGE_TEXT
    assert heading_text == AR_HEADING_TEXT
    assert description_text == AR_DESCRIPTION_TEXT
    assert pillar_title == AR_VISION_TITLE
    assert pillar_desc == AR_VISION_DESC
    assert text_x is not None and carousel_x is not None
    assert text_x > carousel_x, (
        "expected the text block to mirror to the RIGHT half and the carousel to the LEFT half under RTL"
    )
    assert not sd.has_page_horizontal_overflow(), "expected no overlap/clipping (no horizontal overflow) in RTL"


# ── TC 135535 — Fully responsive at 375px ───────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Responsive at mobile width (375px)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Strategic Direction section is fully responsive at 375px with no clipping or overlap")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135535")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_responsive_at_375px(page):
    # ABOUT-STRATEGICDIRECTION-TC-135535 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Load Home Page at 375x812"):
        sd.open_home()

    with allure.step("Scroll to the Strategic Direction section"):
        sd.scroll_to_section()

    with allure.step("Measure the section for overflow/clipping"):
        has_overflow = sd.has_page_horizontal_overflow()
        stage_box = sd.stage_box()

    # Assert
    assert not has_overflow, "expected no horizontal scroll/clipping at 375px"
    assert sd.is_badge_visible() and sd.is_heading_visible() and sd.is_description_visible(), (
        "expected the badge, heading, and description to remain visible without overlap at 375px"
    )
    assert sd.is_active_card_visible()
    assert stage_box["width"] <= 375, f"expected the pillar stage to fit within the 375px viewport, got {stage_box}"


# ── TC 135536 — Fully responsive at 768px ───────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Responsive at tablet width (768px)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Strategic Direction section is fully responsive at 768px with proportional scaling")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135536")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_responsive_at_768px(page):
    # ABOUT-STRATEGICDIRECTION-TC-135536 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Load Home Page at 768x1024"):
        sd.open_home()

    with allure.step("Scroll to the Strategic Direction section"):
        sd.scroll_to_section()

    with allure.step("Measure the section for overflow/clipping"):
        has_overflow = sd.has_page_horizontal_overflow()
        stage_box = sd.stage_box()

    # Assert
    assert not has_overflow, "expected no clipping at 768px"
    assert sd.is_badge_visible() and sd.is_heading_visible() and sd.is_description_visible(), (
        "expected proportional scaling with no overlap at 768px"
    )
    assert sd.is_active_card_visible()
    assert stage_box["width"] <= 768, f"expected the pillar stage to fit within the 768px viewport, got {stage_box}"


# ── TC 135537 — Fully responsive at 1920px matching Figma spacing tokens ───
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Responsive at desktop width (1920px) matches Figma spacing tokens")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Strategic Direction section at 1920px matches the Figma-specified spacing tokens")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129381
@pytest.mark.traceability("ABOUT-STRATEGICDIRECTION-TC-135537")
def test_responsive_at_1920px_matches_figma_spacing(page):
    # ABOUT-STRATEGICDIRECTION-TC-135537 | PBI 129381
    # Arrange
    sd = HomeStrategicDirectionPage(page)

    # Act
    with allure.step("Load Home Page at the default 1920x1080 viewport"):
        sd.open_home()

    with allure.step("Scroll to the Strategic Direction section"):
        sd.scroll_to_section()

    with allure.step("Measure the section padding and carousel container width"):
        padding = sd.section_padding()
        gaps = sd.section_content_side_gaps()
        carousel_box = sd.carousel_box()

    # Assert
    assert padding["top"] == 80 and padding["bottom"] == 80, f"expected 80px top/bottom padding, got {padding}"
    assert round(gaps["left"]) == 300, f"expected 300px left padding, got {gaps['left']}"
    assert round(gaps["right"]) == 300, f"expected 300px right padding, got {gaps['right']}"
    assert round(carousel_box["width"]) == 636, f"expected a 636px carousel container, got {carousel_box['width']}"

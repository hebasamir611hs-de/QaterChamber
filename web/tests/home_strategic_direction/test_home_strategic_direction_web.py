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


# Rule 1 (bug-rules.md): images +/-5 px, layout +/-2 px, text exact.
IMG_TOL, LAYOUT_TOL = 5, 2


def _near(value, target, tol=LAYOUT_TOL) -> bool:
    v = float(str(value).replace("px", "")) if value not in (None, "") else float("nan")
    return abs(v - target) <= tol

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
@pytest.mark.tc_135515
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135516
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
    # Badge background NOT asserted (reviewer 2026-10-08): the Figma text
    # "Label" frame has no fill; the badge sits on the identical #F6F0EC
    # section colour, so a transparent background renders the same.
    assert "rgb(215, 190, 170)" in style["border"], (  # #D7BEAA stroke (width 0.5 vs 1 px is within +/-2)
        f"expected badge stroke #D7BEAA, got {style['border']!r}"
    )
    assert (style["fontWeight"], style["fontSize"], style["lineHeight"]) == ("400", "14px", "22px"), (
        f"badge text: Figma Cairo 400 14/22, live {style['fontWeight']} {style['fontSize']}/{style['lineHeight']}"
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
@pytest.mark.tc_135517
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135518
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135519
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
    assert _near(style["width"], 516), f"expected card width 516px (+/-2), got {style['width']!r}"


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
@pytest.mark.tc_135520
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135521
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135522
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
    assert _near(next_size["width"], 40) and _near(next_size["height"], 40), (
        f"expected 40x40px arrows, got {next_size}"
    )
    assert _near(prev_size["width"], 40) and _near(prev_size["height"], 40), (
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
@pytest.mark.tc_135523
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_progress_indicator_style(page):
    """TC 135523 — RE-SCOPED 2026-10-08 (reviewer item 13): Figma has no
    "1 of 3" indicator; it draws two stacked strips under the card (476 and
    436 px wide, 18 px each, fill #D7BEAA, stroke #B3845F). Live renders the
    next two cards behind the active one. Measured against Figma with Rule 1
    tolerances (layout +/-2 px, colour exact). Anonymous visitor."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    sd.scroll_to_section()
    strips = sd.stack_strips()
    allure.attach(str(strips), "stacked strips", allure.attachment_type.TEXT)
    assert all(strips), f"expected two stacked strips under the card, got {strips}"
    for strip, width in zip(strips, (476, 436)):
        assert _near(strip["width"], width), f"strip {strip['depth']}: width {strip['width']} vs Figma {width}"
        assert _near(strip["band"], 18), f"strip {strip['depth']}: visible band {strip['band']} vs Figma 18"
        assert strip["bg"] == "rgb(215, 190, 170)", f"strip {strip['depth']}: fill {strip['bg']} vs Figma #D7BEAA"
        assert strip["border"] == "rgb(179, 132, 95)", f"strip {strip['depth']}: stroke {strip['border']} vs Figma #B3845F"


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
@pytest.mark.tc_135524
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135525
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
    assert _near(gaps["left"], 300), f"expected 300px left content gap, got {gaps['left']}"
    assert _near(gaps["right"], 300), f"expected 300px right content gap, got {gaps['right']}"


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
@pytest.mark.tc_135526
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
    assert _near(box["width"], 636), f"expected carousel container width 636px, got {box['width']}"
    assert _near(prev_gap, 20), f"expected a 20px gap between the previous arrow and the card, got {prev_gap}"
    assert _near(next_gap, 20), f"expected a 20px gap between the next arrow and the card, got {next_gap}"


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
@pytest.mark.tc_135527
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
    assert _near(icon_size["width"], 72, IMG_TOL) and _near(icon_size["height"], 72, IMG_TOL), (
        f"expected a 72x72px pillar icon, got {icon_size}"
    )
    assert _near(card_style["paddingTop"], 20), f"expected 20px top padding, got {card_style['paddingTop']!r}"
    assert _near(card_style["paddingBottom"], 20), f"expected 20px bottom padding, got {card_style['paddingBottom']!r}"
    assert _near(card_style["paddingLeft"], 24)
    assert _near(card_style["paddingRight"], 24)
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
@pytest.mark.tc_135528
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135529
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135530
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135531
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135532
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_progress_indicator_updates_on_advance(page):
    """TC 135532 — RE-SCOPED 2026-10-08 (reviewer item 13): no "1 of 3"
    state exists in Figma or the PBI. What the design shows on every card is
    the two-strip stack; after Next the new active card (Mission) must carry
    the same two strips, so the deck cue follows the navigation."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    sd.scroll_to_section()
    before = sd.stack_strips()
    sd.click_next()
    # the deck re-stacks with a ~0.42 s transition; read once it has settled
    after = sd.stack_strips()
    for _ in range(20):
        if all(after) and all(x["band"] > 0 for x in after):
            break
        page.wait_for_timeout(250)
        after = sd.stack_strips()
    allure.attach(f"{before} | {after}", "strips before/after", allure.attachment_type.TEXT)
    assert sd.active_card_title_text() == "Mission"
    assert all(after), f"stacked strips missing after advancing: {after}"
    for b0, a0 in zip(before, after):
        assert _near(a0["width"], b0["width"]) and _near(a0["band"], b0["band"]), (
            f"strip geometry changed after advancing: {b0} -> {a0}"
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
@pytest.mark.tc_135533
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135534
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
@pytest.mark.tc_135535
@pytest.mark.parametrize("page", [{"viewport": (375, 812), "auth": False}], indirect=True)
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
@pytest.mark.tc_135536
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
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
@pytest.mark.tc_135537
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
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
    assert _near(gaps["left"], 300), f"expected 300px left padding, got {gaps['left']}"
    assert _near(gaps["right"], 300), f"expected 300px right padding, got {gaps['right']}"
    assert _near(carousel_box["width"], 636), f"expected a 636px carousel container, got {carousel_box['width']}"


# ── TC 135552 — Visitor views the fully published section end-to-end ──────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Visitor views the published section")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A logged-out visitor sees the tag, heading, description and the Vision pillar card")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129381
@pytest.mark.tc_135552
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_visitor_views_published_section_end_to_end(page):
    """TC 135552 — anonymous visitor (logged-out context). Precondition: the
    3 real pillar cards (Vision/Mission/Objectives) are Published + Active;
    this test does not change them."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    sd.scroll_to_section()

    assert sd.is_section_visible(), "Strategic Direction section is not rendered"
    assert sd.badge_text() == EXPECTED_BADGE_TEXT
    assert sd.heading_text() == EXPECTED_HEADING_TEXT
    assert sd.description_text() == EXPECTED_DESCRIPTION_TEXT
    assert sd.active_card_title_text() == EXPECTED_VISION_TITLE
    assert sd.active_card_description_text() == EXPECTED_VISION_DESC
    size = sd.active_card_icon_size()
    assert size["width"] > 0 and size["height"] > 0, "Vision pillar icon is not rendered"


# ── TC 135553 — Forward through all three cards ────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Visitor navigates forward through the pillars")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Right arrow walks Vision -> Mission -> Objectives")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129381
@pytest.mark.tc_135553
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_visitor_navigates_forward_through_all_pillars(page):
    """TC 135553 — anonymous visitor."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    sd.scroll_to_section()

    seen = [sd.active_card_title_text()]
    sd.click_next()
    seen.append(sd.active_card_title_text())
    sd.click_next()
    seen.append(sd.active_card_title_text())

    assert seen == ["Vision", "Mission", "Objectives"], f"forward sequence was {seen}"


# ── TC 135554 — Backward through all three cards ───────────────────────────
@allure.epic("ABOUT")
@allure.feature("Strategic Direction Section")
@allure.story("Visitor navigates backward through the pillars")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Left arrow walks Objectives -> Mission -> Vision")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129381
@pytest.mark.tc_135554
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_visitor_navigates_backward_through_all_pillars(page):
    """TC 135554 — anonymous visitor. "Load carousel on Objectives" is reached
    with two right-arrow clicks from the initial Vision card."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    sd.scroll_to_section()
    sd.click_next()
    sd.click_next()
    assert sd.active_card_title_text() == "Objectives", "precondition: carousel not on Objectives"

    seen = []
    sd.click_prev()
    seen.append(sd.active_card_title_text())
    sd.click_prev()
    seen.append(sd.active_card_title_text())

    assert seen == ["Mission", "Vision"], f"backward sequence was {seen}"


# =============================================================================
# USER ORDER 2026-10-07 22:45 — every case executed (P3/P4 web edges,
# compatibility). All logged out.
# =============================================================================
def _walk_both_arrows(sd) -> tuple:
    start = sd.active_card_title_text()
    sd.click_next()
    after_next = sd.active_card_title_text()
    sd.click_prev()
    back = sd.active_card_title_text()
    return start, after_next, back


def _engine_case(page, tc: int) -> None:
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    sd.scroll_to_section()
    assert sd.is_section_visible() and sd.heading_text() == EXPECTED_HEADING_TEXT
    start, after_next, back = _walk_both_arrows(sd)
    page.screenshot(path=f"reports/manual-exec-129381-{tc}.png")
    allure.attach("\n".join(errors) or "<none>", "page errors", allure.attachment_type.TEXT)
    assert (start, after_next, back) == ("Vision", "Mission", "Vision"), f"arrow walk: {start}->{after_next}->{back}"
    assert not errors, f"uncaught page errors: {errors}"


@allure.label("pbi", PBI)
@allure.title("Strategic Direction renders and navigates in Chrome (desktop)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.pbi_129381
@pytest.mark.tc_135544
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_renders_in_chrome(page):
    """TC 135544 — Chromium (Chrome engine), anonymous."""
    _engine_case(page, 135544)


@allure.label("pbi", PBI)
@allure.title("Strategic Direction renders and navigates in Safari (WebKit, desktop)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.pbi_129381
@pytest.mark.tc_135545
@pytest.mark.parametrize("page", [{"auth": False, "engine": "webkit"}], indirect=True)
def test_renders_in_safari(page):
    """TC 135545 — Playwright WebKit (Safari engine), anonymous."""
    _engine_case(page, 135545)


@allure.label("pbi", PBI)
@allure.title("Strategic Direction renders and navigates in Firefox (desktop)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.pbi_129381
@pytest.mark.tc_135546
@pytest.mark.parametrize("page", [{"auth": False, "engine": "firefox"}], indirect=True)
def test_renders_in_firefox(page):
    """TC 135546 — Playwright Firefox, anonymous."""
    _engine_case(page, 135546)


@allure.label("pbi", PBI)
@allure.title("Swipe left on a touch device advances to the next pillar")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.pbi_129381
@pytest.mark.tc_135547
def test_touch_swipe_advances(browser):
    """TC 135547 — mobile touch emulation (390x844, hasTouch, isMobile),
    anonymous. A real touch swipe right-to-left is dispatched through CDP
    Input.dispatchTouchEvent on the visible card."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    try:
        pg = ctx.new_page()
        sd = HomeStrategicDirectionPage(pg)
        sd.open_home()
        sd.scroll_to_section()
        before = sd.active_card_title_text()
        box = pg.locator(sd.STAGE).bounding_box()
        y = box["y"] + box["height"] / 2
        x0, x1 = box["x"] + box["width"] * 0.85, box["x"] + box["width"] * 0.15
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y}]})
        for i in range(1, 9):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * i / 8, "y": y}]})
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        try:
            pg.wait_for_function(
                "(old) => { const t = document.querySelector('.qc-sd-card.is-active .qc-sd-card-title'); return t && t.textContent !== old; }",
                arg=before, timeout=5000)
        except Exception:  # noqa: BLE001 — asserted below
            pass
        after = sd.active_card_title_text()
        pg.screenshot(path="reports/manual-exec-129381-135547.png")
        assert (before, after) == ("Vision", "Mission"), f"swipe left: {before!r} -> {after!r}"
    finally:
        ctx.close()


@allure.label("pbi", PBI)
@allure.title("Arabic (RTL): the visually-forward arrow advances to the next pillar")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.pbi_129381
@pytest.mark.tc_135629
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_rtl_arrow_direction(page):
    """TC 135629 — /ar/home, anonymous. In RTL the forward arrow sits on the
    LEFT; clicking it must move Vision (الرؤية) to Mission (الرسالة)."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home_arabic()
    sd.scroll_to_section()
    assert sd.active_card_title_text() == AR_VISION_TITLE
    next_x, prev_x = sd.arrow_x_position("next"), sd.arrow_x_position("prev")
    left_arrow = sd.ARROW_NEXT if next_x < prev_x else sd.ARROW_PREV
    allure.attach(f"next x={next_x}, prev x={prev_x}; left arrow={left_arrow}", "arrow positions", allure.attachment_type.TEXT)
    assert next_x < prev_x, f"forward arrow is not on the left in RTL (next x={next_x}, prev x={prev_x})"
    sd._click_arrow_and_wait_for_change(left_arrow)
    assert sd.active_card_title_text() == "الرسالة", f"left (forward) arrow went to {sd.active_card_title_text()!r}"


@allure.label("pbi", PBI)
@allure.title("Right arrow on the last card loops or is disabled — no broken state")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.pbi_129381
@pytest.mark.tc_135631
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_right_arrow_on_last_card(page):
    """TC 135631 — anonymous."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    sd.click_next()
    sd.click_next()
    assert sd.active_card_title_text() == "Objectives"
    disabled = page.locator(sd.ARROW_NEXT).is_disabled()
    if not disabled:
        sd.click_next()
    title = sd.active_card_title_text()
    assert title.strip(), "blank card after the last-card right arrow"
    assert disabled or title == "Vision", f"right arrow on the last card went to {title!r}"


@allure.label("pbi", PBI)
@allure.title("Left arrow on the first card loops or is disabled — no broken state")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.pbi_129381
@pytest.mark.tc_135632
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_left_arrow_on_first_card(page):
    """TC 135632 — anonymous."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    assert sd.active_card_title_text() == "Vision"
    disabled = page.locator(sd.ARROW_PREV).is_disabled()
    if not disabled:
        sd.click_prev()
    title = sd.active_card_title_text()
    assert title.strip(), "blank card after the first-card left arrow"
    assert disabled or title == "Objectives", f"left arrow on the first card went to {title!r}"

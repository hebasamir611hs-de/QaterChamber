"""
web/tests/home_media_gallery/test_home_media_gallery_web.py — Media Gallery
Section (PBI 129388 / QC-HOME-012), Web platform.

Source: 7 approved, Automation-tagged, UI-category, Web-platform cases
handed off for this run (ADO TC 133637-133643), read verbatim from Azure
DevOps via review_test_coverage. Functional/Edge/Compatibility/Auth cases on
this same PBI are explicit out-of-scope for this run (per the QA Manager's
instruction) and are NOT in this file. No Control_Panel cases were included
in this batch either (see the sibling test_home_media_gallery_control_panel.py
skeleton, untouched).

TC 133640 ("video card renders all required elements") is NOT scripted here —
see home_media_gallery_page.py's docstring for why (no video content exists
anywhere in this environment to CLI-extract real locators from; scripting it
would mean inventing selectors that have never been observed to render).
Reported to the QA Manager as BLOCKED, not silently skipped.

Known real-environment findings surfaced while scripting these (full detail
in web/pages/home_media_gallery/home_media_gallery_page.py's docstring, which
documents the live CLI-extraction/inspection evidence for every value below).
Per this project's Result Integrity rule, the case's stated Figma tokens/test
data are kept as the asserted target throughout — a live mismatch is scripted
to FAIL HONESTLY, never quietly re-targeted at the observed value:
  - TC 133637: badge text/color/background/border/radius/font-family/weight/
    size all match exactly; computed line-height is 16px, not the case's
    stated 24px.
  - TC 133638: heading and description text match verbatim; weight/size/color
    match on both; computed line-heights are 38.1px/28.08px, not the case's
    stated 38px/28px (sub-pixel rounding).
  - TC 133639: CONFIRMED LIVE, genuine pass — "All Media" renders active,
    "Video" (the tab's real live name — the case says "Videos") and "Albums"
    render inactive at exactly #6C6C6B; clicking "Video" swaps the active
    state onto it.
  - TC 133640: BLOCKED — not scripted (see above).
  - TC 133641: real, live album cards exist (badge "Album", white bold
    title, calendar+date, dot separator, image-icon+"N photos", no
    play-button element) but none is titled "Private Sector Networking
    Reception" — the real live albums are test/seed fixture titles
    ("Second_test_Album_QChamber", "First_Test_Album_QChamber",
    "Third_Test_Album_QChamber"). Scripted per the case's literal title;
    will fail honestly on the "card is present" assertion — a real content
    gap, not a framework defect.
  - TC 133642: CONFIRMED LIVE, genuine pass — RTL direction, Arabic copy on
    badge/heading/description/tabs, the head-text block shifts from the left
    to the right half of the section, the card meta-row's icon/text order
    visually flips, and the "Explore More" arrow's transform becomes a
    horizontal flip (`matrix(-1, 0, 0, 1, 0, 0)`) vs. `none` in EN.
  - TC 133643: heading does not truncate and there is no page-level
    horizontal overflow at 375px; the 3 filter tabs remain reachable via a
    horizontally-scrollable strip. HOWEVER: CONFIRMED LIVE, the card grid
    renders as a 2-column layout at 375px, not the case's stated single
    column — scripted per the case's literal expected result and will fail
    honestly against this real, measured layout.
"""

import allure
import pytest

from web.pages.home_media_gallery.home_media_gallery_page import HomeMediaGalleryPage

PBI = "129388"

EXPECTED_BADGE_TEXT = "Media Center"
EXPECTED_HEADING_TEXT = "Gallery & Media Showcase"
EXPECTED_DESCRIPTION_TEXT = "Discover Qatar Chamber's latest photos, videos, and media highlights."
NAMED_VIDEO_CARD_TITLE = "Qatar Chamber Digital Services Launch"
NAMED_ALBUM_CARD_TITLE = "Private Sector Networking Reception"

# Live-confirmed Arabic copy (AR homepage, TC 133642) — used as the expected
# value per this project's "prefer the real observed live value" instruction.
AR_BADGE_TEXT = "المركز الإعلامي"
AR_HEADING_TEXT = "معرض الصور والوسائط"
AR_DESCRIPTION_TEXT = "استعرض أبرز الصور والفيديوهات من أنشطة ومبادرات غرفة قطر وتغطياتها الإعلامية."


# ── TC 133637 — Section badge renders per verified Figma tokens ────────────
@allure.epic("MEDIA")
@allure.feature("Media Gallery Section")
@allure.story("Section badge style")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Media Gallery section badge renders per the verified Figma design tokens")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129388
@pytest.mark.traceability("MEDIA-GALLERY-TC-133637")
def test_section_badge_renders_per_figma_tokens(page):
    # MEDIA-GALLERY-TC-133637 | PBI 129388
    # Arrange
    mg = HomeMediaGalleryPage(page)

    # Act
    with allure.step("Navigate to the Home Page (EN) and scroll to the Media Gallery section"):
        mg.open_home()
        mg.scroll_to_section()

    with allure.step("Read the badge's text and computed style"):
        text = mg.badge_text()
        style = mg.badge_style()

    # Assert
    assert mg.is_section_visible()
    assert text == EXPECTED_BADGE_TEXT
    assert style["color"] == "rgb(166, 111, 67)"  # #A66F43
    assert style["backgroundColor"] == "rgb(246, 240, 236)", (  # #F6F0EC
        f"expected badge background #F6F0EC, got {style['backgroundColor']!r}"
    )
    assert style["border"] == "1px solid rgb(215, 190, 170)", (  # #D7BEAA
        f"expected badge border 1px solid #D7BEAA, got {style['border']!r}"
    )
    assert style["borderRadius"] == "9999px", "expected a fully rounded pill shape"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "400"
    assert style["fontSize"] == "16px"
    assert style["lineHeight"] == "24px", f"expected line-height 24px, got {style['lineHeight']!r}"


# ── TC 133638 — Heading and description render per verified Figma tokens ───
@allure.epic("MEDIA")
@allure.feature("Media Gallery Section")
@allure.story("Heading and description text and typography")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Media Gallery section heading and description render per the verified Figma design tokens")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129388
@pytest.mark.traceability("MEDIA-GALLERY-TC-133638")
def test_heading_and_description_render_per_figma_tokens(page):
    # MEDIA-GALLERY-TC-133638 | PBI 129388
    # Arrange
    mg = HomeMediaGalleryPage(page)

    # Act
    with allure.step("Navigate to the Home Page and scroll to the section"):
        mg.open_home()
        mg.scroll_to_section()

    with allure.step("Read the heading's and description's text and computed style"):
        heading_text = mg.heading_text()
        heading_style = mg.heading_style()
        description_text = mg.description_text()
        description_style = mg.description_style()

    # Assert
    assert heading_text == EXPECTED_HEADING_TEXT
    assert heading_style["fontWeight"] == "700"
    assert heading_style["fontSize"] == "30px"
    assert heading_style["lineHeight"] == "38px", (
        f"expected heading line-height 38px, got {heading_style['lineHeight']!r}"
    )
    assert heading_style["color"] == "rgb(29, 29, 27)"  # #1D1D1B

    assert description_text == EXPECTED_DESCRIPTION_TEXT
    assert description_style["fontWeight"] == "400"
    assert description_style["fontSize"] == "18px"
    assert description_style["lineHeight"] == "28px", (
        f"expected description line-height 28px, got {description_style['lineHeight']!r}"
    )
    assert description_style["color"] == "rgb(124, 123, 123)", (  # #7C7B7B
        f"expected description color #7C7B7B, got {description_style['color']!r}"
    )


# ── TC 133639 — Active/inactive filter tab states are visually distinct ────
@allure.epic("MEDIA")
@allure.feature("Media Gallery Section")
@allure.story("Filter tab active/inactive states")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The active and inactive Media Gallery filter tab states are visually distinct")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129388
@pytest.mark.traceability("MEDIA-GALLERY-TC-133639")
def test_active_and_inactive_tab_states_are_visually_distinct(page):
    # MEDIA-GALLERY-TC-133639 | PBI 129388
    # The case's step says 'Click the "Videos" tab' — the tab's real, live
    # accessible name is "Video" (singular). See Page Object docstring: this
    # is a locator-selection note, not an asserted content mismatch, since
    # the case's expected result is about active/inactive STYLING only.
    # Arrange
    mg = HomeMediaGalleryPage(page)

    # Act
    with allure.step("Navigate to the Home Page and scroll to the section (3 tabs visible)"):
        mg.open_home()
        mg.scroll_to_section()
        tab_texts_before = mg.tab_texts()

    with allure.step("Read all 3 tabs' computed style before interacting"):
        all_media_style_before = mg.tab_style("All Media")
        video_style_before = mg.tab_style("Video")
        albums_style_before = mg.tab_style("Albums")

    with allure.step('Click the "Video" tab and re-inspect all 3 tabs'):
        mg.click_tab("Video")
        all_media_style_after = mg.tab_style("All Media")
        video_style_after = mg.tab_style("Video")
        albums_style_after = mg.tab_style("Albums")

    # Assert
    assert tab_texts_before == ["All Media", "Video", "Albums"]
    assert mg.is_tab_active("All Media") is False  # active moved to Video
    assert mg.is_tab_active("Video") is True

    # Before: All Media active, Video/Albums inactive grey #6C6C6B
    assert all_media_style_before["color"] == "rgb(255, 255, 255)"
    assert video_style_before["color"] == "rgb(108, 108, 107)", (  # #6C6C6B
        f"expected inactive Video-tab color #6C6C6B, got {video_style_before['color']!r}"
    )
    assert albums_style_before["color"] == "rgb(108, 108, 107)", (  # #6C6C6B
        f"expected inactive Albums-tab color #6C6C6B, got {albums_style_before['color']!r}"
    )

    # After: Video active, All Media/Albums inactive grey #6C6C6B
    assert video_style_after["color"] == "rgb(255, 255, 255)"
    assert all_media_style_after["color"] == "rgb(108, 108, 107)", (
        f"expected inactive All-Media-tab color #6C6C6B after switch, got {all_media_style_after['color']!r}"
    )
    assert albums_style_after["color"] == "rgb(108, 108, 107)", (
        f"expected inactive Albums-tab color #6C6C6B after switch, got {albums_style_after['color']!r}"
    )


# ── TC 133641 — Album card renders required elements, no play-button overlay ──
@allure.epic("MEDIA")
@allure.feature("Media Gallery Section")
@allure.story("Album card layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An album card renders all required elements and omits the play-button overlay")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129388
@pytest.mark.traceability("MEDIA-GALLERY-TC-133641")
def test_album_card_renders_required_elements_no_play_button(page):
    # MEDIA-GALLERY-TC-133641 | PBI 129388
    # Scripted per the case's literal named fixture. CONFIRMED LIVE: no album
    # titled "Private Sector Networking Reception" exists in this
    # environment (see Page Object docstring for the real live album
    # titles) — this is expected to fail honestly on the presence assertion,
    # not a framework defect.
    # Arrange
    mg = HomeMediaGalleryPage(page)

    # Act
    with allure.step("Navigate to the Home Page and scroll to the section"):
        mg.open_home()
        mg.scroll_to_section()

    with allure.step(f'Locate the album card titled "{NAMED_ALBUM_CARD_TITLE}"'):
        card = mg.card_locator_by_title(NAMED_ALBUM_CARD_TITLE)
        present = mg.is_element_present(card)

    with allure.step("Inspect the card's badge, title, meta row, and play-button overlay"):
        badge_text = mg.card_badge_text(card) if present else None
        title_style = mg.card_title_style(card) if present else None
        meta_texts = mg.card_meta_texts(card) if present else None
        has_separator = mg.card_has_meta_separator(card) if present else None
        has_play_button = mg.card_has_play_button(card) if present else None

    # Assert
    assert present, (
        f'expected an album card titled "{NAMED_ALBUM_CARD_TITLE}" under All Media/Albums, but no such '
        f"card exists in this environment (real live album titles: {mg.card_titles()!r})"
    )
    assert badge_text == "Album"
    assert title_style["color"] == "rgb(255, 255, 255)"
    assert title_style["fontWeight"] == "700"
    assert len(meta_texts) >= 2, f"expected a date item and a photo-count item, got {meta_texts!r}"
    assert "photo" in meta_texts[-1].lower(), f"expected a '<N> photos' meta item, got {meta_texts!r}"
    assert has_separator, "expected a dot separator between the meta items"
    assert not has_play_button, "expected NO play-button overlay on an album card"


# ── TC 133642 — Media Gallery mirrors correctly in RTL (Arabic) ────────────
@allure.epic("MEDIA")
@allure.feature("Media Gallery Section")
@allure.story("Renders mirrored and correctly in Arabic (RTL)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Media Gallery section mirrors correctly in RTL (Arabic)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.pbi_129388
@pytest.mark.traceability("MEDIA-GALLERY-TC-133642")
def test_media_gallery_mirrors_correctly_in_rtl(page):
    # MEDIA-GALLERY-TC-133642 | PBI 129388
    # Arrange
    mg = HomeMediaGalleryPage(page)

    # Act
    with allure.step("Switch site language to Arabic and navigate to the Home Page"):
        mg.open_home_arabic()

    with allure.step("Scroll to the Media Gallery section"):
        mg.scroll_to_section()

    with allure.step("Read direction, copy, tab order, card meta-row order, and the Explore CTA arrow"):
        page_dir = mg.page_direction()
        section_dir = mg.section_direction()
        badge_text = mg.badge_text()
        heading_text = mg.heading_text()
        description_text = mg.description_text()
        heading_align = mg.heading_style()["textAlign"]
        first_card = mg.page.locator(mg.CARD).first
        icon_before_text = mg.meta_icon_before_text_visually(first_card)
        arrow_transform = mg.explore_arrow_transform()

    # Assert
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert badge_text == AR_BADGE_TEXT
    assert heading_text == AR_HEADING_TEXT
    assert description_text == AR_DESCRIPTION_TEXT
    assert heading_align == "start", "expected right-aligned (logical 'start') text under RTL"
    assert icon_before_text is False, (
        "expected the card meta-row's icon/text order to mirror (text before icon) under RTL"
    )
    assert arrow_transform == "matrix(-1, 0, 0, 1, 0, 0)", (
        f"expected the Explore More CTA arrow to mirror direction (horizontal flip) under RTL, "
        f"got transform {arrow_transform!r}"
    )
    assert not mg.has_page_horizontal_overflow(), "expected no clipping/overlap (no horizontal overflow) in RTL"


# ── TC 133643 — Media Gallery renders correctly on a mobile viewport ───────
@allure.epic("MEDIA")
@allure.feature("Media Gallery Section")
@allure.story("Responsive at mobile width (375px)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Media Gallery section renders correctly on a mobile viewport")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129388
@pytest.mark.traceability("MEDIA-GALLERY-TC-133643")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_renders_correctly_on_mobile_viewport(page):
    # MEDIA-GALLERY-TC-133643 | PBI 129388
    # Arrange
    mg = HomeMediaGalleryPage(page)

    # Act
    with allure.step("Load Home Page at a 375px-wide viewport"):
        mg.open_home()

    with allure.step("Scroll to the Media Gallery section"):
        mg.scroll_to_section()

    with allure.step("Inspect header text wrapping, tab layout, and card stacking"):
        heading_overflow = mg.heading_overflow_state()
        tabs_overflow_x = mg.tabs_overflow_x()
        tabs_flex_wrap = mg.tabs_flex_wrap()
        is_single_column = mg.is_single_column_layout()
        has_page_overflow = mg.has_page_horizontal_overflow()

    # Assert
    assert mg.is_section_visible()
    assert heading_overflow["textOverflow"] != "ellipsis", "expected the heading to wrap, not truncate"
    assert heading_overflow["scrollWidth"] <= heading_overflow["clientWidth"] + 1, (
        f"expected no heading clipping at 375px, got {heading_overflow}"
    )
    assert tabs_overflow_x in ("auto", "scroll") or tabs_flex_wrap == "wrap", (
        "expected the filter tabs to remain usable (stacked or horizontally scrollable) at 375px, "
        f"got overflow-x={tabs_overflow_x!r} flex-wrap={tabs_flex_wrap!r}"
    )
    assert not has_page_overflow, "expected no page-level horizontal scrollbar at 375px"
    assert is_single_column, (
        "expected media cards to stack in a single column at 375px, but they render in multiple "
        f"columns (card x positions: {mg.card_x_positions()!r})"
    )

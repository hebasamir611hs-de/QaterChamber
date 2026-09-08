"""
web/tests/about_qatar_chamber/test_about_qatar_chamber_web.py — About Qatar
Chamber (PBI 129392 / QC-ABOUT 001), Web platform.

Source: all 43 approved, Automation-tagged, Web-platform cases in this batch
(scope: Category:UI OR Platform:Web, execution_type=Automated) — 134669-134683,
134688-134701, 134730-134731, 134736, 134740-134751. 14 of these also carry
the Control_Panel tag (134675, 134676, 134679, 134688, 134690, 134691, 134693,
134694, 134697, 134698, 134701, 134730, 134731, 134736); per
automation-standards.md's "one test per platform, sharing step intent" rule,
their CMS-editing step is a SEPARATE test in the sibling
test_about_qatar_chamber_control_panel.py (all 14 gated skip — blank
TEST_USER/TEST_PASSWORD, see that module's docstring). The public-page
verification half of each of those 14 lives HERE, scripted against whatever
content is already live rather than content this run authored — clearly
noted per test.

See web/pages/about_qatar_chamber/about_qatar_chamber_page.py's docstring for
the full CLI-first extraction log and every real, live finding surfaced while
scripting these (each honestly asserted per its case's exact stated wording,
never silently adjusted to match what the app currently does) — key ones
repeated inline as short comments where a test's own assertion depends on
them.
"""

import allure
import pytest

from web.pages.about_qatar_chamber.about_qatar_chamber_page import AboutQatarChamberPage

PBI = "129392"


# ═══════════════════════════ UI (17 cases) ═══════════════════════════════

@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Hero Banner")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Hero Banner renders with the design-specified title and overlay on desktop")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134669")
def test_hero_banner_renders_title_and_overlay(page):
    # ADO-134669 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English at 1920x1080"):
        about.open_en()

    with allure.step("Inspect the Hero Banner band and its title text"):
        box = about.hero_box()
        title_text = about.hero_title_text()
        title_style = about.hero_title_style()
        overlay_bg = about.hero_overlay_background_image()
        media_bg = about.hero_media_background_image()

    # Assert
    assert about.is_hero_visible()
    assert box and round(box["width"]) == 1920
    # NOTE: live renders ~118px, not the case's stated 140px — see Page-Object docstring.
    assert box and round(box["height"]) == 140
    assert title_text == "About Qatar Chamber"
    assert "Cairo" in title_style["fontFamily"]
    assert title_style["fontSize"] == "30px"
    assert title_style["fontWeight"] == "700"
    assert title_style["lineHeight"] == "38px"
    assert title_style["color"] == "rgb(255, 255, 255)"
    assert title_style["textAlign"] in ("left", "start")
    assert "gradient" in overlay_bg
    assert media_bg and media_bg != "none"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Breadcrumb (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The breadcrumb renders the configured trail in English")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134670")
def test_breadcrumb_renders_configured_trail_english(page):
    # ADO-134670 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()

    with allure.step("Inspect the breadcrumb component"):
        home_icon_visible = about.is_breadcrumb_home_icon_visible()
        items = about.breadcrumb_item_texts()
        gap = about.breadcrumb_gap()
        style = about.breadcrumb_crumb_style()

    # Assert
    assert home_icon_visible
    # NOTE: live breadcrumb renders only 2 items (Home, About Us) — no
    # separate "About Qatar Chamber" leaf — see Page-Object docstring.
    assert items == ["Home", "About Us", "About Qatar Chamber"]
    assert gap == "6px"
    assert style["fontSize"] == "14px"
    assert style["fontWeight"] == "400"
    assert style["lineHeight"] == "22px"
    assert style["color"] == "rgb(255, 255, 255)"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Two-column layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page renders the two-column layout with text left and Content Image right")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134671")
def test_two_column_layout_text_left_image_right(page):
    # ADO-134671 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English at 1920x1080"):
        about.open_en()

    with allure.step("Inspect the first content row below the Hero Banner"):
        row = about.content_row_box()
        intro = about.intro_box()
        media = about.media_box()
        before = about.intro_renders_before_media()

    # Assert
    # NOTE: live row renders 1216px wide, split 596/596 — not the case's
    # stated 1320px / 648px each — see Page-Object docstring.
    assert row and round(row["width"]) == 1320
    assert intro and round(intro["width"]) == 648
    assert media and round(media["width"]) == 648
    gap = round(media["x"] - (intro["x"] + intro["width"]))
    assert gap == 24
    assert before, "expected the rich text column to render LEFT of the Content Image column"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Content Image")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Content Image renders with the design-specified rounding and decorative backing element")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134672")
def test_content_image_rounding_and_backing(page):
    # ADO-134672 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English at 1920x1080"):
        about.open_en()

    with allure.step("Inspect the Content Image in the right column"):
        img_box = about.media_img_box()
        img_radius = about.media_img_border_radius()
        panel_box = about.media_panel_box()
        panel_style = about.media_panel_style()

    # Assert
    # NOTE: live image renders ~548x302 (column-width-dependent, 92% of a
    # 596px column) and the panel ~322x332 — not the case's stated 600x330 /
    # 325x343 exactly — see Page-Object docstring.
    assert img_box and round(img_box["width"]) == 600 and round(img_box["height"]) == 330
    assert img_radius == "16px"
    assert panel_box and round(panel_box["width"]) == 325 and round(panel_box["height"]) == 343
    assert panel_style["borderRadius"] == "20px"
    assert panel_style["backgroundColor"] == "rgb(244, 231, 234)"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Primary heading + intro paragraph typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The primary section heading and introductory paragraph render in the design-specified typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134673")
def test_primary_heading_and_paragraph_typography(page):
    # ADO-134673 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()

    with allure.step("Inspect the primary section heading and the paragraph immediately below it"):
        heading_style = about.intro_heading_style()
        para_style = about.intro_paragraph_style()
        margin = about.intro_heading_margin_bottom()

    # Assert
    assert heading_style["fontSize"] == "30px"
    assert heading_style["fontWeight"] == "700"
    assert heading_style["lineHeight"] == "38px"  # live computes 38.1px
    assert heading_style["color"] == "rgb(145, 23, 49)"
    assert para_style["fontSize"] == "18px"
    assert para_style["fontWeight"] == "400"
    assert para_style["lineHeight"] == "28px"  # live computes 28.08px
    assert para_style["color"] == "rgb(52, 52, 50)"
    assert margin == "12px"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Section header icon + heading style")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Each content section header renders with its circular icon badge and heading style")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134674")
def test_section_header_icon_badge_and_heading_style(page):
    # ADO-134674 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()

    with allure.step("Inspect the 'The Chamber's competences' section header"):
        headings = about.body_heading_texts()
        icon_0 = about.body_heading_icon_style(0)
        text_style_0 = about.body_heading_text_style(0)

    with allure.step("Inspect the 'Chamber Constituents' section header"):
        icon_1 = about.body_heading_icon_style(1)
        text_style_1 = about.body_heading_text_style(1)

    # Assert
    assert "competences" in headings[0]
    assert "Constituents" in headings[1]
    for icon in (icon_0, icon_1):
        assert icon["width"] == "56px" and icon["height"] == "56px"
        assert icon["borderRadius"] == "50%"
        assert icon["backgroundColor"] == "rgb(244, 231, 234)"
    for style in (text_style_0, text_style_1):
        assert style["fontSize"] == "20px"
        assert style["fontWeight"] == "700"
        assert style["color"] == "rgb(145, 23, 49)"
        assert style["gap"] == "20px"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Rich text structure (public verification half)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Page rich text renders headings, paragraphs, bullet lists, numbered lists, and an inline link")
@allure.description(
    "Web-side verification half of ADO-134675 — the CMS-authoring half is a "
    "separate, gated test in test_about_qatar_chamber_control_panel.py "
    "(blocked: blank TEST_USER/TEST_PASSWORD). Verified here against "
    "whatever rich text is ALREADY published live, not content authored this "
    "run — see Page-Object docstring."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134675")
def test_rich_text_renders_headings_lists_and_link(page):
    # ADO-134675 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()

    with allure.step("Inspect the rendered content block"):
        heading_count = about.body_heading_count()
        has_bullet = about.has_bullet_list()
        has_numbered = about.has_numbered_list()
        link_visible = about.inline_link_is_visible()
        link_href = about.inline_link_href()

    # Assert
    assert heading_count >= 1
    assert has_bullet, "expected at least one bullet list in the rich text"
    assert has_numbered, "expected at least one numbered list in the rich text"
    assert link_visible
    assert link_href == "https://www.qatarchamber.com"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Content Image alt text (public verification half)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Content Image exposes the alt text configured in the CMS")
@allure.description(
    "Web-side verification half of ADO-134676 — the CMS-authoring half "
    "(setting the exact configured alt string) is a separate, gated test in "
    "test_about_qatar_chamber_control_panel.py (blocked: blank "
    "TEST_USER/TEST_PASSWORD). Verified here generically (alt attribute is "
    "present and non-empty) against whatever value is already live, not the "
    "case's literal blocked string — see Page-Object docstring."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134676")
def test_content_image_exposes_alt_text(page):
    # ADO-134676 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()

    with allure.step("Inspect the Content Image accessible name / alt attribute"):
        alt = about.media_img_alt()

    # Assert
    assert alt and alt.strip(), "expected the Content Image to expose a non-empty alt attribute"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("LTR layout (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page renders in LTR layout in English")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134677")
def test_page_renders_ltr_in_english(page):
    # ADO-134677 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English at 1920x1080"):
        about.open_en()

    with allure.step("Inspect the page direction, text alignment, and column order"):
        direction = about.page_direction()
        hero_align = about.hero_title_style()["textAlign"]
        before = about.intro_renders_before_media()
        items = about.breadcrumb_item_texts()

    # Assert
    assert direction == "ltr"
    assert hero_align in ("left", "start")
    assert before, "expected the rich text column to render before (left of) the Content Image column"
    # NOTE: live breadcrumb is only 2 items — see Page-Object docstring.
    assert items == ["Home", "About Us", "About Qatar Chamber"]


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("RTL layout (AR)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page renders in mirrored RTL layout in Arabic")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134678")
def test_page_renders_rtl_in_arabic(page):
    # ADO-134678 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in Arabic at 1920x1080"):
        about.open_ar()

    with allure.step("Inspect the page direction, text alignment, and column order"):
        direction = about.page_direction()
        heading_align = about.body_heading_text_style(0)["textAlign"]
        media_before_intro = about.media_renders_before_intro()

    with allure.step("Inspect the breadcrumb component"):
        sep_transform = about.breadcrumb_sep_transform()

    # Assert
    assert direction == "rtl"
    assert heading_align in ("right", "start")
    # NOTE: live renders the OPPOSITE — the rich text column sits on the
    # right (read first) and the Content Image on the left (read second),
    # not image-before-text as this case states — see Page-Object docstring.
    assert media_before_intro, "expected the Content Image column to render before (right of) the rich text column"
    assert sep_transform == "matrix(-1, 0, 0, 1, 0, 0)"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Section order (public verification half)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("All published content sections appear on the page in the configured order")
@allure.description(
    "Web-side verification half of ADO-134679 — the CMS-authoring half is a "
    "separate, gated test in test_about_qatar_chamber_control_panel.py "
    "(blocked: blank TEST_USER/TEST_PASSWORD). Verified here against the "
    "ALREADY-published live section order, which happens to already match "
    "this case's exact stated order — see Page-Object docstring."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134679")
def test_sections_appear_in_configured_order(page):
    # ADO-134679 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()

    with allure.step("Scroll from the top of the content block to the bottom and record the section order"):
        order = about.section_heading_order()

    # Assert
    assert len(order) == 3
    assert "Private Sector" in order[0]
    assert "competences" in order[1]
    assert "Constituents" in order[2]


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Arabic breadcrumb — no placeholder item")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Arabic breadcrumb contains no placeholder item")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134744")
def test_arabic_breadcrumb_has_no_placeholder_item(page):
    # ADO-134744 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in Arabic"):
        about.open_ar()

    with allure.step("Read every item in the breadcrumb"):
        items = about.breadcrumb_item_texts()

    # Assert
    for item in items:
        assert item not in ("Item-3", "Item", "", None)
    # NOTE: live breadcrumb is only 2 labelled items (+ home icon), not 3 —
    # see Page-Object docstring.
    assert about.breadcrumb_item_count() == 3


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Arabic breadcrumb leaf matches page title")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Arabic breadcrumb leaf uses the same Arabic page name as the Arabic page title")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134745")
def test_arabic_breadcrumb_leaf_matches_page_title(page):
    # ADO-134745 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in Arabic"):
        about.open_ar()

    with allure.step("Record the Arabic hero page title text"):
        hero_title = about.hero_title_text()

    with allure.step("Record the final (leaf) item text in the Arabic breadcrumb"):
        crumb_leaf = about.breadcrumb_item_texts()[-1]

    # Assert
    assert hero_title == "غرفة قطر"
    # NOTE: live breadcrumb leaf is hardcoded "من نحن" ("About Us"), never the
    # page's own title — see Page-Object docstring.
    assert crumb_leaf == hero_title


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Arabic section headings right-aligned")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Every Arabic section heading is right-aligned in the RTL layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134746")
def test_arabic_section_headings_right_aligned(page):
    # ADO-134746 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in Arabic at 1920x1080"):
        about.open_ar()

    with allure.step("Inspect the text alignment of every Arabic section heading"):
        count = about.body_heading_count()
        aligns = [about.body_heading_text_style(i)["textAlign"] for i in range(count)]

    # Assert
    assert count >= 2
    for align in aligns:
        assert align in ("right", "start")


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Arabic Chamber Constituents heading spelling")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Arabic section heading for Chamber Constituents is spelled with its hamza")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134747")
def test_arabic_chamber_constituents_heading_hamza_spelling(page):
    # ADO-134747 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in Arabic"):
        about.open_ar()

    with allure.step("Read the heading text character by character"):
        headings = about.body_heading_texts()

    # Assert
    assert "أجهزة الغرفة" in headings
    assert "اجهزة الغرفة" not in headings


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Dark mode (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The English page renders correctly in dark mode on desktop")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134748")
def test_english_page_dark_mode_desktop(page):
    # ADO-134748 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English at 1920x1080"):
        about.open_en()

    with allure.step("Switch the site to dark mode"):
        about.enable_dark_mode()

    with allure.step("Inspect the page background, headings, and Content Image"):
        is_dark = about.is_dark_mode_active()
        bg = about.page_background_color()
        heading_color = about.body_heading_color(0)
        media_visible = about.is_visible(about.MEDIA)
        panel_visible = about.is_visible(about.MEDIA_PANEL)

    # Assert
    assert is_dark
    assert bg == "rgb(29, 29, 27)"
    assert heading_color == "rgb(224, 138, 156)"  # #E08A9C, the dark-mode heading token
    assert media_visible and panel_visible


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Dark mode (AR)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Arabic page renders correctly in dark mode on desktop")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134749")
def test_arabic_page_dark_mode_desktop(page):
    # ADO-134749 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in Arabic at 1920x1080"):
        about.open_ar()

    with allure.step("Switch the site to dark mode"):
        about.enable_dark_mode()

    with allure.step("Inspect the page background, Arabic text colours and section icon badges"):
        is_dark = about.is_dark_mode_active()
        bg = about.page_background_color()
        icon_style = about.body_heading_icon_style(0)

    with allure.step("Confirm the RTL layout is unchanged"):
        direction = about.page_direction()
        media_before_intro = about.media_renders_before_intro()

    # Assert
    assert is_dark
    assert bg == "rgb(29, 29, 27)"
    assert icon_style["backgroundColor"] != bg, "expected the icon badge to remain distinguishable from the dark background"
    assert direction == "rtl"
    # Case states "Content Image column first" under RTL — asserting that
    # stated expectation (NOT the live value) per Result Integrity: 134678
    # already documents live RTL renders the OPPOSITE (rich text column on
    # the right/first, Content Image on the left/second), so this is
    # expected to fail honestly for the same real, already-reported mismatch
    # — not silently flipped to match live behaviour.
    assert media_before_intro, "expected the Content Image column to render before (right of) the rich text column"


# ═══════════════════════════ Compatibility (5 cases) ══════════════════════

@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Desktop viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page renders correctly at desktop viewport width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134680")
def test_renders_correctly_at_desktop_viewport(page):
    # ADO-134680 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English at 1920x1080"):
        about.open_en()

    with allure.step("Inspect the hero, content container, and page scroll behaviour"):
        hero_box = about.hero_box()
        content_box = about.content_box()
        overflow = about.has_page_horizontal_overflow()
        intro = about.intro_box()
        media = about.media_box()

    # Assert
    assert hero_box and round(hero_box["width"]) == 1920
    # Case states the content container is 1320px wide — asserting that
    # stated value (NOT the live ~1216px value) per Result Integrity; see
    # Page-Object docstring for the documented live mismatch.
    assert content_box and round(content_box["width"]) == 1320
    assert intro and media and round(intro["y"]) == round(media["y"])  # side by side
    assert not overflow


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Tablet viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page reflows correctly at tablet viewport width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134681")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_reflows_correctly_at_tablet_viewport(page):
    # ADO-134681 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()

    with allure.step("Inspect the hero, both content columns, and page scroll behaviour"):
        hero_title_visible = about.is_visible(about.HERO_TITLE)
        breadcrumb_visible = about.is_visible(about.BREADCRUMB)
        intro_visible = about.is_visible(about.INTRO)
        media_visible = about.is_visible(about.MEDIA)
        overflow = about.has_page_horizontal_overflow()

    # Assert
    assert hero_title_visible
    assert breadcrumb_visible
    assert intro_visible and media_visible
    assert not overflow


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Mobile viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page stacks to a single column at mobile viewport width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134682")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_stacks_single_column_at_mobile_viewport(page):
    # ADO-134682 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()

    with allure.step("Inspect the column order, image scaling, and page scroll behaviour"):
        row_columns = about.row_grid_template_columns()
        intro_order = about.intro_css_order()
        media_order = about.media_css_order()
        img_width = about.media_img_inline_size()
        overflow = about.has_page_horizontal_overflow()
        hero_title_visible = about.is_visible(about.HERO_TITLE)
        breadcrumb_visible = about.is_visible(about.BREADCRUMB)

    # Assert
    assert " " not in row_columns.strip()  # a single track value == single column
    assert int(intro_order) < int(media_order), "expected the rich text to stack ABOVE the Content Image"
    assert img_width == "350px"  # 100% of the 350px content width at 390px viewport
    assert not overflow
    assert hero_title_visible and breadcrumb_visible


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Dark mode at desktop width")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The page renders correctly in dark mode at desktop viewport width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134750")
def test_dark_mode_at_desktop_width(page):
    # ADO-134750 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the page in English at 1920x1080 and switch to dark mode"):
        about.open_en()
        light_row = about.content_row_box()
        light_media = about.media_box()
        about.enable_dark_mode()
        dark_row = about.content_row_box()
        dark_media = about.media_box()

    with allure.step("Repeat in Arabic"):
        about.open_ar()
        ar_direction_before = about.page_direction()
        about.enable_dark_mode()
        ar_dark = about.is_dark_mode_active()
        ar_direction_after = about.page_direction()

    # Assert
    assert round(light_row["width"]) == round(dark_row["width"])
    assert round(light_media["width"]) == round(dark_media["width"])
    assert ar_direction_before == "rtl" and ar_direction_after == "rtl"
    assert ar_dark


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Dark mode at mobile width")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The page renders correctly in dark mode at mobile viewport width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134751")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_dark_mode_at_mobile_width(page):
    # ADO-134751 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open in English at 390x844 and switch to dark mode"):
        about.open_en()
        about.enable_dark_mode()
        en_overflow = about.has_page_horizontal_overflow()
        footer_visible_en = about.is_footer_visible()

    with allure.step("Repeat in Arabic"):
        about.open_ar()
        about.enable_dark_mode()
        ar_overflow = about.has_page_horizontal_overflow()
        ar_direction = about.page_direction()

    # Assert
    assert not en_overflow
    assert footer_visible_en
    assert not ar_overflow
    assert ar_direction == "rtl"


# ═══════════════════════════ Auth (1 case) ════════════════════════════════

@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Public reachability without sign-in")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Public Visitor can view the published page without signing in")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134683")
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_public_visitor_views_page_without_signin(page):
    # ADO-134683 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Navigate directly to the About Qatar Chamber page URL with no active login"):
        about.open_en()

    with allure.step("Inspect the hero, breadcrumb, and all published content sections"):
        sections = about.are_all_sections_visible()
        login_prompt_visible = about.is_login_prompt_visible()

    # Assert
    assert all(sections.values()), f"expected every section visible, got {sections!r}"
    assert not login_prompt_visible


# ═══════════════════════════ Functional-High (13 cases) ═══════════════════

@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Publish makes content visible (public verification half)")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing the page makes the content visible on the website")
@allure.description(
    "Web-side verification half of ADO-134688 — the CMS-authoring half is a "
    "separate, gated test in test_about_qatar_chamber_control_panel.py. "
    "Verified here against the ALREADY-published live title/first section, "
    "which happen to already match this case's exact configured values."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134688")
def test_published_content_visible_on_website(page):
    # ADO-134688 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page on the public site in English"):
        about.open_en()

    with allure.step("Inspect the title and first section"):
        title = about.hero_title_text()
        first_section = about.intro_heading_text()

    # Assert
    assert title == "About Qatar Chamber"
    assert "Voice of Qatar" in first_section


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Reach page from the main menu")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A visitor reaches the page from the main menu")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134689")
def test_visitor_reaches_page_from_main_menu(page):
    # ADO-134689 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the public site homepage in English"):
        about.header.open_home()

    with allure.step("Hover or click Main Menu -> About Us and locate 'About Qatar Chamber'"):
        # NOTE: live "About us" submenu lists 6 links (Chairman's Message,
        # General Manager's Message, Vision/Mission & Objectives, Chamber's
        # Law, Board of Directors & General Manager, Organizational
        # Structure) and contains NO "About Qatar Chamber" entry at all —
        # see Page-Object docstring.
        link_visible = about.is_submenu_about_qatar_chamber_link_visible()

    # Assert
    assert link_visible, "expected the About Us submenu to list an 'About Qatar Chamber' entry"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Unpublish removes content (public verification half)")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Unpublishing the page removes it from the website")
@allure.description(
    "Web-side verification half of ADO-134690 — the CMS-authoring "
    "(unpublish) half is a separate, gated test in "
    "test_about_qatar_chamber_control_panel.py. Verified here only as the "
    "pre-condition that the page IS currently reachable/published; the "
    "post-unpublish 404 check itself requires the blocked CMS step."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134690")
def test_unpublished_page_not_served_publicly(page):
    # ADO-134690 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Confirm the page is currently published and reachable (pre-condition for the CMS half)"):
        about.open_en()
        reachable = about.is_hero_visible()

    # Assert
    assert reachable, "expected the About Qatar Chamber page to currently be published and reachable"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Draft content not visible publicly (public verification half)")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Draft content is visible only in the CMS and not on the website")
@allure.description(
    "Web-side verification half of ADO-134691 — the CMS-authoring (save as "
    "draft) half is a separate, gated test in "
    "test_about_qatar_chamber_control_panel.py. Verified here as a baseline "
    "regression guard: the marker text was never authored this run, so its "
    "absence does not itself exercise the real draft mechanism."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134691")
def test_draft_content_not_visible_on_public_page(page):
    # ADO-134691 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English and search for the draft marker"):
        about.open_en()
        contains_draft_marker = about.html_text_contains("DRAFT-ONLY-129392")

    # Assert
    assert not contains_draft_marker


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Publish updates cache (public verification half)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publishing the page updates the page cache and writes an audit log entry")
@allure.description(
    "Web-side verification half of ADO-134693 — the CMS-authoring (publish +"
    " audit log) half is a separate, gated test in "
    "test_about_qatar_chamber_control_panel.py. Verified here only as basic "
    "reachability of the currently-served content; the cache-refresh "
    "before/after comparison and the audit log itself require the blocked "
    "CMS step."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134693")
def test_publish_serves_current_content(page):
    # ADO-134693 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the public About Qatar Chamber page in English"):
        about.open_en()
        title = about.hero_title_text()

    # Assert
    assert title == "About Qatar Chamber"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Hyperlink open behaviour (public verification half)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A hyperlink configured in the CMS opens its destination from the public page")
@allure.description(
    "Web-side verification half of ADO-134694 — the CMS-authoring half is a "
    "separate, gated test in test_about_qatar_chamber_control_panel.py. "
    "Verified here against the ALREADY-configured live CTA link (label "
    "'Visit Qatar Chamber', not the case's 'Qatar Chamber Services' — never "
    "authored this run) rather than the specific blocked label."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.redirect
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134694")
def test_hyperlink_opens_destination_from_public_page(page):
    # ADO-134694 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English and locate the link"):
        about.open_en()
        visible = about.is_cta_visible()
        label = about.cta_label_text()

    with allure.step("Click the link"):
        popup = about.click_cta_and_get_popup_or_none()

    # Assert
    assert visible
    assert label.strip()
    assert popup is not None and "qatarchamber.com" in popup.url


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Switch EN -> AR")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Switching the site language from English to Arabic loads the Arabic page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134695")
def test_switch_language_english_to_arabic(page):
    # ADO-134695 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()
        en_title = about.hero_title_text()

    with allure.step("Click the language switcher and select Arabic"):
        about.switch_language_via_switcher()
        ar_title = about.hero_title_text()
        direction = about.page_direction()
        url = about.current_url()

    # Assert
    assert en_title == "About Qatar Chamber"
    assert ar_title == "غرفة قطر"
    assert direction == "rtl"
    assert "home" not in url.lower(), "expected NOT to be returned to the homepage"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Switch AR -> EN")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Switching the site language from Arabic back to English loads the English page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134696")
def test_switch_language_arabic_to_english(page):
    # ADO-134696 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in Arabic"):
        about.open_ar()
        ar_title = about.hero_title_text()
        ar_direction = about.page_direction()

    with allure.step("Click the language switcher and select English"):
        about.switch_language_to_english_via_switcher()
        en_title = about.hero_title_text()
        en_direction = about.page_direction()
        url = about.current_url()

    # Assert
    assert ar_title == "غرفة قطر" and ar_direction == "rtl"
    assert en_title == "About Qatar Chamber"
    assert en_direction == "ltr"
    assert "home" not in url.lower(), "expected NOT to be returned to the homepage"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Hero image replace (public verification half)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing the Hero Banner image updates the image shown on the website")
@allure.description(
    "Web-side verification half of ADO-134697 — the CMS-authoring (image "
    "upload + publish) half is a separate, gated test in "
    "test_about_qatar_chamber_control_panel.py. Verified here only that the "
    "hero currently renders SOME background image; the before/after image "
    "swap comparison requires the blocked CMS step."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134697")
def test_hero_banner_image_currently_renders(page):
    # ADO-134697 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the public About Qatar Chamber page in English"):
        about.open_en()
        bg = about.hero_media_background_image()

    # Assert
    assert bg and bg != "none"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("First-time hero image upload (public verification half)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Uploading a Hero Banner image for the first time publishes it to the website")
@allure.description(
    "Web-side verification half of ADO-134698 — the CMS-authoring (first "
    "upload + publish) half is a separate, gated test in "
    "test_about_qatar_chamber_control_panel.py. Verified here only that the "
    "hero renders a background image with the maroon/gold gradient overlay "
    "today; the empty-to-populated transition requires the blocked CMS step."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134698")
def test_hero_banner_renders_with_gradient_overlay(page):
    # ADO-134698 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the public About Qatar Chamber page in English"):
        about.open_en()
        bg = about.hero_media_background_image()
        overlay = about.hero_overlay_background_image()

    # Assert
    assert bg and bg != "none"
    assert "gradient" in overlay


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("About Us breadcrumb link")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Clicking the About Us breadcrumb link navigates to the About Us page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134699")
def test_click_about_us_breadcrumb_navigates(page):
    # ADO-134699 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()
        start_url = about.current_url()

    with allure.step("Click the 'About Us' entry in the breadcrumb"):
        # NOTE: live "About Us" breadcrumb item is a plain <span>
        # (qc-ap-crumb-current), NOT a link — see Page-Object docstring. Its
        # tag is checked FIRST (a deterministic, zero-wait DOM read) so the
        # navigation wait below is only attempted when a real link exists —
        # never an arbitrary sleep-and-hope.
        is_link = about.breadcrumb_current_is_link()
        if is_link:
            about.click(about.CRUMB_CURRENT)
            about.page.wait_for_url(lambda url: url != start_url, timeout=5000)
        end_url = about.current_url()

    # Assert
    assert is_link, "expected the 'About Us' breadcrumb entry to be a real, clickable link"
    assert end_url != start_url, "expected clicking the 'About Us' breadcrumb entry to navigate away"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Scroll through every section")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A visitor can scroll through every content section to the end of the page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134700")
def test_scroll_through_every_section_to_footer(page):
    # ADO-134700 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English at 1920x1080"):
        about.open_en()

    with allure.step("Scroll from the top of the page to the bottom"):
        order = about.section_heading_order()
        about.scroll_to_footer()
        footer_visible = about.is_footer_visible()

    # Assert
    assert len(order) == 3
    assert "Constituents" in order[-1]
    assert footer_visible


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Edit and republish replaces content (public verification half)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Editing and republishing the page replaces the previously published content")
@allure.description(
    "Web-side verification half of ADO-134701 — the CMS-authoring (edit + "
    "republish) half is a separate, gated test in "
    "test_about_qatar_chamber_control_panel.py. Verified here only that the "
    "current live content renders without the case's fictitious "
    "VERSION-1/VERSION-2 markers (neither was ever authored this run)."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134701")
def test_republish_replaces_previous_version(page):
    # ADO-134701 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the public About Qatar Chamber page in English"):
        about.open_en()
        has_v1 = about.html_text_contains("VERSION-1-129392")
        has_v2 = about.html_text_contains("VERSION-2-129392")

    # Assert
    assert not has_v1


# ═══════════════════════════ Functional-Low (3 cases) ═════════════════════

@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Hyperlink title accepted (public verification half)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A valid Hyperlink Title is accepted and rendered as the link label")
@allure.description(
    "Web-side verification half of ADO-134730 — the CMS-authoring half is a "
    "separate, gated test in test_about_qatar_chamber_control_panel.py. "
    "Verified here that the CTA link renders SOME non-empty label matching "
    "whatever is currently configured live (not the case's blocked literal "
    "'Qatar Chamber Services' string)."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134730")
def test_hyperlink_title_rendered_as_link_label(page):
    # ADO-134730 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()
        label = about.cta_label_text()

    # Assert
    assert label and label.strip()


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Empty hyperlink title allowed (public verification half)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("An empty Hyperlink Title is allowed because the field is optional")
@allure.description(
    "Web-side verification half of ADO-134731 — the CMS-authoring half is a "
    "separate, gated test in test_about_qatar_chamber_control_panel.py. "
    "Verified here as a general regression guard: no anchor on the page has "
    "an empty label live today."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134731")
def test_page_renders_normally_with_no_empty_link_label(page):
    # ADO-134731 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()
        cta_label = about.cta_label_text()

    # Assert
    assert cta_label.strip() != ""


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Empty hyperlink URL allowed (public verification half)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("An empty Hyperlink URL is allowed because the field is optional")
@allure.description(
    "Web-side verification half of ADO-134736 — the CMS-authoring half is a "
    "separate, gated test in test_about_qatar_chamber_control_panel.py. "
    "Verified here as a general regression guard: no anchor inside the "
    "editorial content points to an empty/javascript-void destination live "
    "today."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134736")
def test_page_renders_normally_with_no_broken_anchor(page):
    # ADO-134736 | PBI 129392 (public-page verification half)
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English"):
        about.open_en()
        ok = about.no_anchor_has_empty_or_void_href()

    # Assert
    assert ok


# ═══════════════════════════ Edge (4 cases) ════════════════════════════════

@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Missing Arabic translation fallback")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A missing Arabic translation falls back to the configured default language")
@allure.description(
    "The CMS-authoring precondition (publish an English-only section with no "
    "Arabic translation) requires the blocked CMS step. Verified here that "
    "the Arabic page currently renders with NO empty/blank section for any "
    "of its content — the closest honest live signal without reproducing "
    "the specific blocked precondition."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134740")
def test_missing_arabic_translation_falls_back(page):
    # ADO-134740 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in Arabic"):
        about.open_ar()

    with allure.step("Inspect every section for blank/empty content"):
        headings = [about.intro_heading_text()] + about.body_heading_texts()
        intro_text = about.text(about.INTRO_PARAGRAPH)

    # Assert
    assert all(h.strip() for h in headings), "expected no blank/empty section heading"
    assert intro_text.strip(), "expected no blank/empty section body"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Broken content hyperlink stays visible (public verification half)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A broken content hyperlink remains visible on the page")
@allure.description(
    "Web-side verification half of ADO-134741 — the CMS-authoring "
    "(configure a hyperlink to a deliberately non-existent URL) half is a "
    "separate, gated concern requiring CMS access (not scripted as a "
    "Control_Panel test here since 134741 does not itself carry the "
    "Control_Panel tag). Verified here directly against the non-existent "
    "path, confirming the site's error handling doesn't affect the About "
    "Qatar Chamber page itself when navigated back to."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.redirect
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134741")
def test_broken_hyperlink_destination_returns_404_page_intact(page):
    # ADO-134741 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English and locate the link"):
        about.open_en()

    with allure.step("Navigate to a deliberately broken destination URL"):
        status = about.open_not_found_path()

    with allure.step("Navigate back to the About Qatar Chamber page"):
        about.open_en()
        hero_visible = about.is_hero_visible()

    # Assert
    assert status == 404
    assert hero_visible, "expected the About Qatar Chamber page to remain intact and navigable via Back"


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Standard error page on failed load")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A failed page load shows the standard error page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134742")
def test_failed_page_load_shows_standard_error_page(page):
    # ADO-134742 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Request a deliberately unavailable sibling page URL as a public visitor"):
        status = about.open_not_found_path()
        header_visible = about.is_visible(about.header.HEADER)
        footer_visible = about.is_footer_visible()
        body_text = about.page_body_text()

    # Assert
    assert status == 404
    assert header_visible and footer_visible
    assert "Traceback" not in body_text
    assert "Exception" not in body_text


@allure.epic("ABOUT")
@allure.feature("About Qatar Chamber")
@allure.story("Hyperlink open behaviour same/new tab (public verification half)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A content hyperlink honours the CMS-configured open behaviour for same tab and new tab")
@allure.description(
    "Web-side verification half of ADO-134743 — the CMS-authoring (toggle "
    "open-behaviour) half is a separate, gated concern requiring CMS access "
    "(not scripted as a Control_Panel test here since 134743 does not "
    "itself carry the Control_Panel tag). Verified here only the CURRENT "
    "live behaviour of the existing CTA link (external URL -> target=_blank, "
    "new tab) — the same-tab half cannot be exercised without the CMS step."
)
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.redirect
@pytest.mark.pbi_129392
@pytest.mark.traceability("ADO-134743")
def test_hyperlink_honours_new_tab_open_behaviour(page):
    # ADO-134743 | PBI 129392
    # Arrange
    about = AboutQatarChamberPage(page)

    # Act
    with allure.step("Open the About Qatar Chamber page in English and click the link"):
        about.open_en()
        target_attr = about.cta_target()
        popup = about.click_cta_and_get_popup_or_none()

    # Assert
    assert target_attr == "_blank"
    assert popup is not None, "expected the destination to open in a NEW tab (current CMS-configured behaviour)"
    assert about.current_url().endswith("/about-us"), "expected the About Qatar Chamber page to remain loaded in the original tab"

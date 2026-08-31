"""
web/tests/home_podcast/test_home_podcast_web.py — Qatar Chamber Podcast
Section (PBI 129387 / QC-HOME-011), Web platform.

Source: 7 approved, Automation-tagged, UI-category, Web-platform cases handed
off for this PBI (ADO TC 133950-133956). Control_Panel-tagged cases for this
same PBI are out-of-scope for this run and are NOT in this file (see the
sibling test_home_podcast_control_panel.py skeleton).

No explicit priority was provided with this batch, so every case here is
scripted at Allure severity NORMAL rather than guessing a tier the source
data never stated.

Known real-environment findings surfaced while scripting these (full detail
in web/pages/home_podcast/home_podcast_page.py's docstring, which documents
the live CLI-extraction/inspection evidence for every value below). Per this
project's Result Integrity rule, a live mismatch below is scripted to FAIL
HONESTLY against the case's literal stated value, never quietly re-targeted
at the observed one:
  - TC 133950: CONFIRMED LIVE, genuine pass — RTL direction, a full mirror of
    the thumbnail/text block positions, a visually mirrored player-control
    order (back/play/fwd -> fwd/play/back left-to-right), and non-empty
    Arabic copy on the title, description, and both tag pills.
  - TC 133951: CONFIRMED LIVE — the section's own background genuinely
    changes from #4A0D1C (maroon) to #1D1D1B when the global Dark Mode
    toggle is switched on; the case expects it to stay unchanged. Scripted
    to fail honestly against that real, observed change.
  - TC 133952: the meta row's structure/styling (4 items, dot-separated,
    icon order, Cairo Regular 14px/22px white) matches exactly; the literal
    content ("Episode 24"/"42 MIN") does not — live reads "Episode 3"/
    "20 SEC" (date and play count DO match exactly).
  - TC 133953: the tag pills' styling (Cairo Regular 14px/22px white,
    rgba(29,29,27,0.4) background, 6px radius) matches exactly on both
    pills; the literal "52 Episodes" text does not — live reads "3
    Episodes" ("Weekly" matches exactly).
  - TC 133954: CONFIRMED LIVE, full genuine pass — pill shape, white fill,
    1px border, exact copy, Cairo SemiBold 16px/24px #4A4A49, 10px/16px
    padding, and an arrow icon.
  - TC 133955: skip icons (36x36), the maroon glowing circular Play button
    (#911731), the 8px light-grey (#EDEDED) progress track, and the Cairo
    Medium 14px/22px white time text all match exactly; the Mute button is
    present. The idle-state time text reads "0:00 / 0:00" (metadata not yet
    loaded), not a shown duration — the case's literal "0:00 / 0:35 (or
    actual duration)" implies a duration is already visible at rest.
  - TC 133956: skip buttons grow 36->44px and the Play button grows 48->64px
    on a 375px viewport with no control overlap; the volume control
    (`.qc-pod-vol`) is not merely smaller on mobile — it renders
    `display: none` (absent entirely), not the case's expected "larger tap
    target".
"""

import allure
import pytest

from web.pages.home_podcast.home_podcast_page import HomePodcastPage

PBI = "129387"

EXPECTED_META_FULL_TEXT = "Episode 24 • May 10, 2026 • 42 MIN • 12.4K plays"
EXPECTED_TAG_TEXTS = ["52 Episodes", "Weekly"]
EXPECTED_EXPLORE_TEXT = "Explore More"
EXPECTED_IDLE_TIME_TEXT = "0:00 / 0:35"

# Live-confirmed Arabic copy (AR homepage, TC 133950) — used as the expected
# value per this project's "prefer the real observed live value" convention
# for bilingual-mirroring assertions.
AR_TITLE_TEXT = "بودكاست غرفة قطر"
AR_TAG_TEXTS = ["3 حلقة", "أسبوعيًا"]


# ── TC 133950 — Arabic (RTL) mirroring ──────────────────────────────────────
@allure.epic("MEDIA")
@allure.feature("Qatar Chamber Podcast Section")
@allure.story("Renders mirrored and correctly in Arabic (RTL)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Podcast section mirrors correctly in Arabic (RTL)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129387
@pytest.mark.traceability("MEDIA-PODCAST-TC-133950")
def test_podcast_section_mirrors_correctly_in_arabic_rtl(page):
    # MEDIA-PODCAST-TC-133950 | PBI 129387
    # Arrange
    pod = HomePodcastPage(page)

    # Act
    with allure.step("Switch site language to Arabic and load the Home page"):
        pod.open_home_arabic()

    with allure.step("Scroll to the Podcast section"):
        pod.scroll_to_section()

    with allure.step("Inspect layout direction, text alignment, and mirrored positions"):
        page_dir = pod.page_direction()
        section_dir = pod.section_direction()
        media_box = pod.media_box()
        body_box = pod.body_box()
        controls_order = pod.controls_visual_order()
        title_text = pod.title_text()
        description_text = pod.description_text()
        tag_texts = pod.tag_texts()
        has_overflow = pod.has_page_horizontal_overflow()

    # Assert
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert media_box["x"] > body_box["x"], (
        "expected the thumbnail block to mirror to the RIGHT of the text/controls block under RTL, "
        f"got media_x={media_box['x']}, body_x={body_box['x']}"
    )
    assert controls_order == ["fwd", "play", "back"], (
        f"expected the player control order to be visually mirrored (fwd, play, back), got {controls_order}"
    )
    assert title_text == AR_TITLE_TEXT
    assert tag_texts == AR_TAG_TEXTS
    for label, text in (("title", title_text), ("description", description_text)):
        assert text and "..." not in text, f"expected non-truncated Arabic {label} text, got {text!r}"
    assert not has_overflow, "expected no overlap/clipping (no horizontal overflow) in RTL"


# ── TC 133951 — Dark-gradient theme persists across global light/dark toggle ─
@allure.epic("MEDIA")
@allure.feature("Qatar Chamber Podcast Section")
@allure.story("Retains its dark-gradient theme regardless of global light/dark mode")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Podcast section retains its dark-gradient theme regardless of the global light/dark toggle")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129387
@pytest.mark.traceability("MEDIA-PODCAST-TC-133951")
def test_podcast_section_retains_dark_gradient_theme_regardless_of_global_toggle(page):
    # MEDIA-PODCAST-TC-133951 | PBI 129387
    # CONFIRMED LIVE: the section's own background genuinely repaints when
    # the global Dark Mode toggle is switched on (see Page Object docstring).
    # Scripted per the case's literal expected result ("unchanged"); expected
    # to fail honestly against that real, observed change, not a framework
    # defect.
    # Arrange
    pod = HomePodcastPage(page)

    # Act
    with allure.step("Load the Home page in light mode and note the Podcast section's background"):
        pod.open_home()
        pod.scroll_to_section()
        light_bg = pod.section_background_color()

    with allure.step("Toggle the site to dark mode via the Accessibility panel"):
        pod.enable_dark_mode()

    with allure.step("Re-inspect the Podcast section's background"):
        dark_bg = pod.section_background_color()

    # Assert
    assert light_bg == "rgb(74, 13, 28)", f"expected the light-mode background #4A0D1C, got {light_bg!r}"
    assert dark_bg == light_bg, (
        "expected the Podcast section's background to stay unchanged after the global dark-mode toggle, "
        f"but it changed from {light_bg!r} to {dark_bg!r}"
    )


# ── TC 133952 — Episode meta row format ─────────────────────────────────────
@allure.epic("MEDIA")
@allure.feature("Qatar Chamber Podcast Section")
@allure.story("Episode meta row format")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The episode meta row displays episode number, date, duration, and play count in the exact specified format")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129387
@pytest.mark.traceability("MEDIA-PODCAST-TC-133952")
def test_episode_meta_row_format(page):
    # MEDIA-PODCAST-TC-133952 | PBI 129387
    # Arrange
    pod = HomePodcastPage(page)

    # Act
    with allure.step("Load the Home page"):
        pod.open_home()

    with allure.step("Inspect the meta row under the episode title"):
        pod.scroll_to_section()
        full_text = pod.meta_full_text()
        dot_count = pod.meta_dot_count()
        style = pod.meta_item_style(0)

    # Assert
    assert pod.is_section_visible()
    assert full_text == EXPECTED_META_FULL_TEXT, f"expected {EXPECTED_META_FULL_TEXT!r}, got {full_text!r}"
    assert dot_count == 3, f"expected 3 dot separators between 4 meta items, got {dot_count}"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "400"
    assert style["fontSize"] == "14px"
    assert style["lineHeight"] == "22px"
    assert style["color"] == "rgb(255, 255, 255)"


# ── TC 133953 — Episode-count/frequency tag pill styling ────────────────────
@allure.epic("MEDIA")
@allure.feature("Qatar Chamber Podcast Section")
@allure.story("Episode-count and frequency tag pill styling")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The episode-count and frequency tags render with the specified pill styling")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129387
@pytest.mark.traceability("MEDIA-PODCAST-TC-133953")
def test_episode_count_and_frequency_tag_pill_styling(page):
    # MEDIA-PODCAST-TC-133953 | PBI 129387
    # Arrange
    pod = HomePodcastPage(page)

    # Act
    with allure.step("Load the Home page"):
        pod.open_home()

    with allure.step("Inspect the two tag pills above the episode heading"):
        pod.scroll_to_section()
        tag_texts = pod.tag_texts()
        style = pod.tag_style(0)

    # Assert
    assert pod.is_section_visible()
    assert tag_texts == EXPECTED_TAG_TEXTS, f"expected {EXPECTED_TAG_TEXTS!r}, got {tag_texts!r}"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "400"
    assert style["fontSize"] == "14px"
    assert style["lineHeight"] == "22px"
    assert style["color"] == "rgb(255, 255, 255)"
    assert style["backgroundColor"] == "rgba(29, 29, 27, 0.4)", (
        f"expected pill background rgba(29, 29, 27, 0.4), got {style['backgroundColor']!r}"
    )
    assert style["borderRadius"] == "6px"


# ── TC 133954 — "Explore More" button matches Figma ────────────────────────
@allure.epic("MEDIA")
@allure.feature("Qatar Chamber Podcast Section")
@allure.story('"Explore More" button styling')
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The "Explore More" button renders per the verified Figma design')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129387
@pytest.mark.traceability("MEDIA-PODCAST-TC-133954")
def test_explore_more_button_matches_figma_design(page):
    # MEDIA-PODCAST-TC-133954 | PBI 129387
    # Arrange
    pod = HomePodcastPage(page)

    # Act
    with allure.step("Load the Home page"):
        pod.open_home()

    with allure.step('Inspect the "Explore More" button in the Podcast section'):
        pod.scroll_to_section()
        text = pod.explore_button_text("top")
        style = pod.explore_button_style("top")
        has_icon = pod.has_explore_button_arrow_icon("top")

    # Assert
    assert pod.is_explore_button_visible("top")
    assert text == EXPECTED_EXPLORE_TEXT
    assert style["borderRadius"] == "9999px", "expected a pill-shaped button"
    assert style["backgroundColor"] == "rgb(255, 255, 255)"
    assert style["border"] == "1px solid rgb(222, 222, 221)", f"expected a 1px border, got {style['border']!r}"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "600"
    assert style["fontSize"] == "16px"
    assert style["lineHeight"] == "24px"
    assert style["color"] == "rgb(74, 74, 73)", f"expected text color #4A4A49, got {style['color']!r}"
    assert style["padding"] == "10px 16px"
    assert has_icon, "expected an arrow-up-right icon on the Explore More button"


# ── TC 133955 — Audio player control icons (idle state) ────────────────────
@allure.epic("MEDIA")
@allure.feature("Qatar Chamber Podcast Section")
@allure.story("Audio player control icons match the verified Figma design")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The audio player control icons render per the verified Figma design in their idle state")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129387
@pytest.mark.traceability("MEDIA-PODCAST-TC-133955")
def test_audio_player_control_icons_idle_state(page):
    # MEDIA-PODCAST-TC-133955 | PBI 129387
    # Arrange
    pod = HomePodcastPage(page)

    # Act
    with allure.step("Load the Home page"):
        pod.open_home()

    with allure.step("Inspect the audio player's visual controls in their idle state"):
        pod.scroll_to_section()
        back_box = pod.skip_button_box("back")
        fwd_box = pod.skip_button_box("fwd")
        play_style = pod.play_button_style()
        is_circular = pod.is_play_button_circular()
        scrub_box = pod.scrub_box()
        scrub_style = pod.scrub_style()
        time_style = pod.time_style()
        time_text = pod.time_text()
        mute_visible = pod.is_mute_button_visible()

    # Assert
    assert round(back_box["width"]) == 36 and round(back_box["height"]) == 36, (
        f"expected a 36px skip-back icon, got {back_box}"
    )
    assert round(fwd_box["width"]) == 36 and round(fwd_box["height"]) == 36, (
        f"expected a 36px skip-forward icon, got {fwd_box}"
    )
    assert is_circular, "expected a circular Play button"
    assert play_style["backgroundColor"] == "rgb(145, 23, 49)", (
        f"expected the Play button color #911731, got {play_style['backgroundColor']!r}"
    )
    assert play_style["boxShadow"] != "none", "expected a glow/shadow on the Play button"
    assert round(scrub_box["height"]) == 8, f"expected an 8px-tall progress bar, got {scrub_box}"
    assert scrub_style["backgroundColor"] == "rgb(237, 237, 237)", (
        f"expected a light-grey #EDEDED progress track, got {scrub_style['backgroundColor']!r}"
    )
    assert "Cairo" in time_style["fontFamily"]
    assert time_style["fontWeight"] == "500"
    assert time_style["fontSize"] == "14px"
    assert time_style["lineHeight"] == "22px"
    assert time_style["color"] == "rgb(255, 255, 255)"
    assert time_text == EXPECTED_IDLE_TIME_TEXT, f"expected idle time text {EXPECTED_IDLE_TIME_TEXT!r}, got {time_text!r}"
    assert mute_visible, "expected a volume-max icon/control to be present"


# ── TC 133956 — Touch-friendly player layout on mobile viewport ────────────
@allure.epic("MEDIA")
@allure.feature("Qatar Chamber Podcast Section")
@allure.story("Player controls adapt to a touch-friendly layout on mobile")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The player controls adapt to a touch-friendly layout on a 375px mobile viewport")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129387
@pytest.mark.traceability("MEDIA-PODCAST-TC-133956")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_player_controls_touch_friendly_on_mobile_viewport(page):
    # MEDIA-PODCAST-TC-133956 | PBI 129387
    # Arrange
    pod = HomePodcastPage(page)

    # Act
    with allure.step("Load the Home page on a 375px mobile viewport"):
        pod.open_home()

    with allure.step("Scroll to the Podcast section"):
        pod.scroll_to_section()

    with allure.step("Inspect the player control sizes, spacing, and overlap"):
        back_box = pod.skip_button_box("back")
        fwd_box = pod.skip_button_box("fwd")
        play_box = pod.play_button_box()
        volume_visible = pod.is_volume_control_visible()
        controls_overlap = pod.player_controls_overlap()
        has_overflow = pod.has_page_horizontal_overflow()

    # Assert — desktop baselines (36x36 skip icons, 48x48 Play button) are
    # CLI-confirmed in home_podcast_page.py's docstring / TC 133955's own pass.
    assert not has_overflow, "expected the Home page to load responsively with no horizontal overflow at 375px"
    assert back_box["width"] > 36 and back_box["height"] > 36, (
        f"expected a larger-than-desktop (36x36) skip-back tap target on mobile, got {back_box}"
    )
    assert fwd_box["width"] > 36 and fwd_box["height"] > 36, (
        f"expected a larger-than-desktop (36x36) skip-forward tap target on mobile, got {fwd_box}"
    )
    assert play_box["width"] > 48 and play_box["height"] > 48, (
        f"expected a larger-than-desktop (48x48) Play tap target on mobile, got {play_box}"
    )
    assert not controls_overlap, "expected no overlapping player controls on mobile"
    assert volume_visible, "expected the volume control to remain visible with a larger tap target on mobile"

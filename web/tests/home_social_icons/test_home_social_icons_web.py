"""
web/tests/home_social_icons/test_home_social_icons_web.py — Home Page
"Social Media Icons" widget (PBI 129373 / QC-HOME-004B), Web platform.

Distinct from the footer's own social icons (PBI 129366 / QC-GBL-004,
web/tests/components/test_footer_web.py) — see
web/pages/home_social_icons/home_social_icons_page.py's docstring for the
class-name collision between the two (`a.qc-social-link` resolves to 16
elements site-wide: 8 in each widget) and how it is scoped away.

Source: 14 approved, Automation-tagged cases handed off for this PBI
(ADO-131133..131145, 131147; ADO-131146 not included in this batch), all
Platform=Web -> this module. Scope for this run is UI category + Web
platform only; Control_Panel/admin is explicitly out of scope
(web/pages/home_social_icons/home_social_icons_admin_page.py and
test_home_social_icons_control_panel.py are left untouched).

UAT tag: several cases below carry Azure's `UAT` tag. Per
automation-standards.md's Axis-1 table, UAT drives the client acceptance
doc, not a pytest marker/slice — it is recorded in each such test's docstring
comment only, never as an invented `@pytest.mark.uat`.

Real, CLI-verified findings from the extraction pass (full detail in the
Page Object's docstring — summarized per case below; each test is scripted
per its case's exact stated expected result regardless of what was found
live, per automation-standards.md's Result Integrity section):
  - ADO-131133 (section order): MATCHES — the widget renders directly after
    Latest News, nothing in between.
  - ADO-131134 (desktop container): padding/gap/background/border-radius all
    differ from the case's stated Figma tokens; the border's first colour
    stop (#E3C5CB) matches exactly, but a two-stop gradient border is not
    verifiable via a plain CSS `border` read.
  - ADO-131135/131136 (desktop heading/subtext typography): colours match
    exactly; several font-size/line-height values differ slightly from the
    stated tokens.
  - ADO-131137/131138 (mobile 375px heading/subtext typography): heading
    font-size matches; several other values (notably subtext font-size,
    which does not scale down at all on mobile) differ from the stated
    tokens.
  - ADO-131139/131140 (icon row): justify-content matches on both desktop
    and mobile; gap and desktop flex-wrap differ from the stated tokens; no
    clipping/overlap on mobile.
  - ADO-131141 (order): the live first-five order MATCHES exactly, verified
    against the live site (Control_Panel/CMS access to inspect a literal
    "Display Order" field is out of scope this run) — 8 platforms are live,
    not the 5 the case's precondition describes.
  - ADO-131142 (inactive icon): no icon is currently configured
    Active Status=False in this environment (Control_Panel out of scope
    this run) — a genuine precondition gap, scripted as a closed-set proxy
    check instead of the untestable negative scenario.
  - ADO-131143 (LinkedIn link): the new-tab mechanism matches; the literal
    URL differs from the case's stated value (no "www.", no hyphen).
  - ADO-131144/131145 (RTL/LTR): both MATCH — a genuine full logical mirror.
  - ADO-131147 (hover): no hover-specific visual change was found live
    (cursor:pointer is the browser's unconditional anchor default, not a
    hover effect) — a real mismatch against the case's expected result.
"""

import allure
import pytest

from web.pages.home_social_icons.home_social_icons_page import HomeSocialIconsPage

PBI = "129373"


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Section renders directly after Latest News")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Social Media Icons section renders directly after Latest News on the Home page (EN)")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131133")
def test_social_icons_section_renders_directly_after_latest_news(page):
    # ADO-131133 | PBI 129373 | UAT (recorded per Axis-1: no pytest marker)
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page (EN) and scroll past the Latest News grid"):
        social.open_home()

    with allure.step("Read the text of the section immediately before this widget"):
        previous_section_text = social.previous_section_text()

    # Assert
    assert social.is_widget_visible()
    assert "latest news" in previous_section_text.lower(), (
        f"expected the Social Media Icons section to follow Latest News directly, "
        f"previous section text was: {previous_section_text!r}"
    )


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Desktop container style matches Figma")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The container's desktop padding, gap, background gradient, border, and radius match Figma")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131134")
def test_social_icons_desktop_container_style_matches_figma(page):
    # ADO-131134 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page on desktop viewport"):
        social.open_home()

    with allure.step("Read the container's computed style"):
        style = social.container_style()

    # Assert
    assert style["padding"] == "20px 32px"
    assert style["gap"] == "24px"
    assert "rgb(251, 246, 248)" in style["backgroundImage"]  # #FBF6F8
    assert "rgb(246, 246, 246)" in style["backgroundImage"]  # #F6F6F6
    assert style["borderWidth"] == "1px"
    assert style["borderColor"] == "rgb(227, 197, 203)"  # #E3C5CB (gradient start)
    assert style["borderRadius"] == "12px"


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Desktop heading typography")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The heading "Find us on social media" matches Figma desktop typography')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131135")
def test_social_icons_heading_desktop_typography_matches_figma(page):
    # ADO-131135 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page on desktop viewport"):
        social.open_home()

    with allure.step("Read the heading's text and computed style"):
        text = social.heading_text()
        style = social.heading_style()

    # Assert
    assert text == "Find us on social media"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "24px"
    assert style["lineHeight"] == "32px"
    assert style["color"] == "rgb(145, 23, 49)"  # #911731


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Desktop subtext typography")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The subtext matches Figma desktop typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131136")
def test_social_icons_subtext_desktop_typography_matches_figma(page):
    # ADO-131136 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page on desktop viewport"):
        social.open_home()

    with allure.step("Read the subtext's computed style"):
        style = social.subtext_style()

    # Assert
    assert style["fontWeight"] == "400"
    assert style["fontSize"] == "18px"
    assert style["lineHeight"] == "28px"
    assert style["color"] == "rgb(108, 108, 107)"  # #6C6C6B


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Mobile heading typography")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The heading matches Figma mobile (375px) typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131137")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_social_icons_heading_mobile_typography_matches_figma(page):
    # ADO-131137 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page at mobile viewport 375x812"):
        social.open_home()

    with allure.step("Read the heading's computed style"):
        style = social.heading_style()

    # Assert
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "20px"
    assert style["lineHeight"] == "30px"
    assert style["color"] == "rgb(145, 23, 49)"  # #911731


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Mobile subtext typography")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The subtext matches Figma mobile (375px) typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131138")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_social_icons_subtext_mobile_typography_matches_figma(page):
    # ADO-131138 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page at mobile viewport 375x812"):
        social.open_home()

    with allure.step("Read the subtext's computed style"):
        style = social.subtext_style()

    # Assert
    assert style["fontWeight"] == "400"
    assert style["fontSize"] == "14px"
    assert style["lineHeight"] == "22px"
    assert style["color"] == "rgb(108, 108, 107)"  # #6C6C6B


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Desktop icon row layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The desktop icon row shows 8 active icons, right-aligned in a single non-wrapping row")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131139")
def test_social_icons_desktop_icon_row_layout(page):
    # ADO-131139 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page on desktop viewport"):
        social.open_home()

    with allure.step("Read the icon row's computed style and icon count"):
        style = social.icon_row_style()
        count = social.icon_count()
        single_row = social.icons_render_on_single_row()

    # Assert
    assert count == 8
    assert style["justifyContent"] == "flex-end"
    assert style["gap"] == "12px"
    assert style["flexWrap"] == "nowrap"
    assert single_row, "expected all 8 icons on a single row on desktop"


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Mobile icon row layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The mobile (375px) icon row shows 8 active icons, centered, wrapping with no clipping/overlap")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131140")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_social_icons_mobile_icon_row_layout(page):
    # ADO-131140 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page at mobile viewport 375x812"):
        social.open_home()

    with allure.step("Read the icon row's computed style, count, and geometry"):
        style = social.icon_row_style()
        count = social.icon_count()
        fits = social.icons_fit_within_viewport()
        no_overlap = social.icons_do_not_overlap()

    # Assert
    assert count == 8
    assert style["justifyContent"] == "center"
    assert style["gap"] == "12px"
    assert style["flexWrap"] == "wrap"
    assert fits, "an icon clipped outside the 375px viewport"
    assert no_overlap, "two or more icons overlap on mobile"


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Icon display order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The first 5 icons render left-to-right in the configured Display Order (EN)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131141")
def test_social_icons_render_in_configured_display_order(page):
    # ADO-131141 | PBI 129373 | UAT (recorded per Axis-1: no pytest marker)
    # NOTE: Control_Panel/CMS access to inspect a literal "Display Order"
    # field is out of scope for this Web-platform batch — verified against
    # the live configured order instead, per this case's own stated
    # fallback. See Page-Object docstring for the full finding.
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page (EN)"):
        social.open_home()

    with allure.step("Read each icon's aria-label in left-to-right DOM order"):
        labels = social.icon_labels()

    # Assert
    assert labels[:5] == ["Facebook", "X", "LinkedIn", "Instagram", "YouTube"], (
        f"expected the first 5 icons in Display Order 1-5, got: {labels[:5]}"
    )


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Inactive icon is not displayed")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An icon with Active Status=False is not displayed; only active icons render")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131142")
def test_social_icons_inactive_icon_is_not_displayed(page):
    # ADO-131142 | PBI 129373
    # NOTE (precondition gap, not a fabricated pass): no icon is currently
    # configured Active Status=False in this environment, and toggling that
    # flag requires Control_Panel/CMS access, out of scope for this
    # Web-platform batch. Scripted as the closest verifiable proxy — the
    # rendered icon set is a closed, deduplicated match against the current
    # live/active catalog — rather than asserting the untestable literal
    # negative scenario. See Page-Object docstring for the full finding.
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page (EN)"):
        social.open_home()

    with allure.step("Read the rendered icon set"):
        labels = social.icon_labels()
        matches_live_catalog = social.rendered_platforms_match_live_catalog()

    # Assert
    assert matches_live_catalog, (
        f"rendered icon set does not match the known live/active catalog: {labels}"
    )


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("LinkedIn icon opens the company page in a new tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking the LinkedIn icon opens the company LinkedIn page in a new tab, leaving Home unchanged")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131143")
def test_social_icons_linkedin_opens_company_page_in_new_tab(page):
    # ADO-131143 | PBI 129373 | UAT (recorded per Axis-1: no pytest marker)
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page (EN)"):
        social.open_home()
        original_url = social.page.url

    with allure.step("Click the LinkedIn icon"):
        new_page = social.click_linkedin_in_new_tab()

    # Assert
    try:
        assert new_page.url.startswith("https://www.linkedin.com/company/qatar-chamber"), (
            f"expected the new tab to open the Qatar Chamber LinkedIn company page, got: {new_page.url}"
        )
        assert social.page.url == original_url, "the original Home tab's URL changed"
        assert social.is_widget_visible(), "the original Home tab should remain open and unchanged"
    finally:
        new_page.close()


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Arabic (RTL) layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("In Arabic (RTL), the heading/subtext are right-aligned and the icon row mirrors, with no clipping")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131144")
def test_social_icons_arabic_rtl_layout(page):
    # ADO-131144 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page in Arabic"):
        social.open_home_arabic()

    with allure.step("Read direction, alignment, and icon-row geometry"):
        direction = social.document_direction()
        heading_style = social.heading_style()
        subtext_style = social.subtext_style()
        row_style = social.icon_row_style()
        x_positions = social.icon_x_positions()
        no_overlap = social.icons_do_not_overlap()

    # Assert
    assert direction == "rtl"
    assert row_style["direction"] == "rtl"
    assert heading_style["textAlign"] == "start"
    assert subtext_style["textAlign"] == "start"
    assert row_style["justifyContent"] == "flex-end"
    assert x_positions == sorted(x_positions, reverse=True), (
        "expected icons to mirror right-to-left (descending x) in Arabic"
    )
    assert no_overlap, "Arabic icon row has overlapping icons"


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("English (LTR) layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("In English (LTR), the heading/subtext are left-aligned and the icon row is right-anchored")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131145")
def test_social_icons_english_ltr_layout(page):
    # ADO-131145 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page in English"):
        social.open_home()

    with allure.step("Read direction, alignment, and icon-row geometry"):
        direction = social.document_direction()
        heading_style = social.heading_style()
        subtext_style = social.subtext_style()
        row_style = social.icon_row_style()
        x_positions = social.icon_x_positions()
        no_overlap = social.icons_do_not_overlap()

    # Assert
    assert direction == "ltr"
    assert heading_style["textAlign"] == "start"
    assert subtext_style["textAlign"] == "start"
    assert row_style["justifyContent"] == "flex-end"
    assert x_positions == sorted(x_positions), (
        "expected icons to flow left-to-right (ascending x) in English"
    )
    assert no_overlap, "English icon row has overlapping icons"


@allure.epic("HOME")
@allure.feature("Social Media Icons")
@allure.story("Icon hover state")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Hovering an icon on desktop shows a visible hover state and pointer cursor")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.traceability("ADO-131147")
def test_social_icons_hover_shows_visible_state_and_pointer_cursor(page):
    # ADO-131147 | PBI 129373
    # Arrange
    social = HomeSocialIconsPage(page)

    # Act
    with allure.step("Open the Home page on desktop viewport"):
        social.open_home()

    with allure.step("Snapshot the Facebook icon's style before and after hovering it"):
        before, after = social.hover_facebook_icon_before_after()

    # Assert
    assert after["cursor"] == "pointer"
    changed = any(before[k] != after[k] for k in ("color", "opacity", "transform", "backgroundColor", "boxShadow"))
    assert changed, "expected a visible hover state (color/opacity/scale change) on the icon"

"""
web/tests/components/test_header_web.py — Site Header (PBI 129363 /
QC-GBL-001), Web platform.

Source: 4 approved, Automation-tagged cases handed off for this PBI (ADO
#134232, #134233, #134240, #134246). All are Platform=Web -> this module
(test_header_web.py); Control_Panel-tagged cases for the same PBI (#134247,
#134248) are explicit Phase-2 scope and are NOT in this file.

Known real-environment findings surfaced while scripting these (see
web/pages/components/header_component.py docstring for the full extraction
log): the live header nav has 11 top-level items, not 10; the rendered logo
is 138x48, not 180x48; the header container's box-shadow computes to "none";
the search icon performs a client-side route change rather than opening an
overlay; and keyboard Tab from a fresh page load never reaches the logo
(trapped between a reCAPTCHA badge iframe and <body>). Each test below is
scripted per its approved case's stated expected result regardless — a
mismatch against these findings is a legitimate, honestly-reported failure,
not something silently adjusted here.

--- Second batch (ADO #134234, #134237, #134239, #134244, #134249) ---
Previously excluded: these 5 carried BOTH Automation and Manual tags on the
same case (an Axis-1b conflict), which blocked automating them and was
flagged back at the source instead of resolved here. The user has since
fixed the tagging conflict in Azure DevOps directly; re-fetched, all 5 now
carry Automation only. Appended below, same module/platform as the first 4.

Real findings from this second extraction pass (see the Page Object's
docstring for the full log): of the 11 nav items, exactly 3 (About us, Our
Services, B2B) carry a chevron + mega-menu, the other 8 carry neither
(#134234, #134249 both a genuine match against the live site); the logo's
alt text is genuinely bilingual (EN "Qatar Chamber" / AR "غرفة قطر") but
still renders 138x48 in both languages, not the case's stated 180x48
(#134237); the language switcher's size/radius/label/font-family/size match
the case's stated values but its background-color, font-weight, and text
color do not (#134239). All scripted per each case's exact stated values —
a mismatch is a legitimate, honestly-reported failure, not silently adjusted.
"""

import allure
import pytest

from web.pages.components.header_component import HeaderComponent

PBI = "129363"


@allure.epic("GLOBAL")
@allure.feature("Site Header")
@allure.story("Header renders with logo, nav, language switcher, and icons")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Site header renders with logo, navigation, language switcher, and icons on desktop")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129363
@pytest.mark.traceability("ADO-134232")
def test_header_renders_logo_nav_language_switcher_and_icons(page):
    # ADO-134232 | PBI 129363
    # Arrange
    header = HeaderComponent(page)

    # Act
    with allure.step("Open a published page (home) on desktop viewport"):
        header.open_home()

    with allure.step("Read the header container's layout style"):
        container_style = header.container_style()

    with allure.step("Read the logo's rendered size and position"):
        logo_size = header.logo_size()
        logo_leftmost = header.is_logo_leftmost()

    with allure.step("Read the nav bar's item count"):
        nav_item_count = header.nav_item_count()

    with allure.step("Read the language switcher and icon buttons' visibility/position"):
        language_switcher_visible = header.is_language_switcher_visible()
        utility_cluster_rightmost = header.is_utility_cluster_rightmost()

    # Assert
    assert header.is_header_visible()
    assert container_style["display"] == "flex"
    assert container_style["flexDirection"] == "row"
    assert container_style["padding"] == "16px 24px"
    assert container_style["backgroundColor"] == "rgb(255, 255, 255)"
    assert container_style["boxShadow"] == "rgba(0, 0, 0, 0.25) 0px 0px 14px 0px"
    assert logo_size == {"width": 180, "height": 48}
    assert logo_leftmost
    assert nav_item_count == 10
    assert language_switcher_visible
    assert utility_cluster_rightmost


@allure.epic("GLOBAL")
@allure.feature("Site Header")
@allure.story("Nav item labels")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Each of the 10 nav items renders with its exact verbatim label")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129363
@pytest.mark.traceability("ADO-134233")
def test_header_nav_items_render_exact_verbatim_labels(page):
    # ADO-134233 | PBI 129363
    # Arrange
    header = HeaderComponent(page)

    # Act
    with allure.step("Open a published page (home)"):
        header.open_home()

    with allure.step("Read each nav item label left to right"):
        labels = header.nav_item_labels()

    with allure.step("Read each nav item's font/color, to confirm uniform styling"):
        styles = header.nav_item_font_styles()

    # Assert
    assert len(labels) == 10
    assert all(label == label.strip() for label in labels), "a label has leading/trailing whitespace (wrapping/truncation artifact)"
    assert all(label for label in labels), "an empty nav label indicates truncation"
    fonts = {(s["fontFamily"], s["fontSize"], s["color"]) for s in styles}
    assert len(fonts) == 1, f"nav items do not share one consistent font/color: {fonts}"


@allure.epic("GLOBAL")
@allure.feature("Site Header")
@allure.story("Search overlay")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking the search icon opens a search overlay with expected/standard rendering")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129363
@pytest.mark.traceability("ADO-134240")
def test_header_search_icon_opens_search_overlay(page):
    # ADO-134240 | PBI 129363
    # Arrange
    header = HeaderComponent(page)

    # Act
    with allure.step("Open a published page (home)"):
        header.open_home()

    with allure.step("Click the search icon button"):
        header.open_search()

    with allure.step("Read the resulting search overlay's contents"):
        overlay_open = header.is_search_overlay_open()
        overlay_input_visible = header.is_search_overlay_input_visible()
        overlay_submit_visible = header.is_search_overlay_submit_visible()

    # Assert
    assert overlay_open, "expected a search overlay over the current page"
    assert overlay_input_visible
    assert overlay_submit_visible


@allure.epic("GLOBAL")
@allure.feature("Site Header")
@allure.story("Logo keyboard focus state")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A focus state displays on the logo when navigated to via keyboard Tab")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129363
@pytest.mark.traceability("ADO-134246")
def test_header_logo_shows_focus_state_on_keyboard_tab(page):
    # ADO-134246 | PBI 129363
    # Arrange
    header = HeaderComponent(page)

    # Act
    with allure.step("Open a published page (home)"):
        header.open_home()

    with allure.step("Press Tab until focus reaches the logo element"):
        reached_logo = header.focus_logo_via_tab()

    with allure.step("Read whether a visible focus indicator displays around the logo"):
        focus_indicator_visible = header.is_logo_focus_indicator_visible() if reached_logo else False

    # Assert
    assert reached_logo, "keyboard Tab never reached the logo element"
    assert focus_indicator_visible


@allure.epic("GLOBAL")
@allure.feature("Site Header")
@allure.story("Nav sub-menu chevron affordance")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Nav items with a sub-menu display a chevron-down dropdown affordance; items with none do not")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.navigation
@pytest.mark.pbi_129363
@pytest.mark.traceability("ADO-134234")
def test_header_nav_items_with_submenu_show_chevron_affordance(page):
    # ADO-134234 | PBI 129363
    # Arrange
    header = HeaderComponent(page)

    # Act
    with allure.step("Open a published page (home)"):
        header.open_home()

    with allure.step("Inspect a nav item configured with sub-menu items"):
        with_submenu_shows_chevron = header.nav_item_with_submenu_shows_chevron()

    with allure.step("Inspect a nav item configured with no sub-menu"):
        without_submenu_has_no_chevron = header.nav_item_without_submenu_has_no_chevron()

    # Assert
    assert with_submenu_shows_chevron, "a nav item with a configured sub-menu should show a chevron-down icon beside its label"
    assert without_submenu_has_no_chevron, "a nav item with no sub-menu should show no chevron icon"


@allure.epic("GLOBAL")
@allure.feature("Site Header")
@allure.story("Logo size and alt text per language")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The logo displays the correct size and alt text per language")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129363
@pytest.mark.traceability("ADO-134237")
def test_header_logo_shows_correct_size_and_alt_text_per_language(page):
    # ADO-134237 | PBI 129363
    # Arrange
    header = HeaderComponent(page)

    # Act
    with allure.step("Open page in EN"):
        header.open_home()

    with allure.step("Inspect logo image size and alt attribute"):
        logo_size_en = header.logo_size()
        logo_alt_en = header.logo_alt_text()

    with allure.step("Switch to AR"):
        header.switch_to_arabic()

    with allure.step("Inspect logo alt attribute again"):
        logo_alt_ar = header.logo_alt_text()

    # Assert
    assert logo_size_en == {"width": 180, "height": 48}
    assert logo_alt_en == "Qatar Chamber"
    assert logo_alt_ar, "expected a non-empty Arabic alt attribute after switching to AR"
    assert logo_alt_ar != logo_alt_en, "alt attribute should update to the Arabic alt text on AR"


@allure.epic("GLOBAL")
@allure.feature("Site Header")
@allure.story("Language switcher inactive-language label and styling")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The language switcher displays the correct label/styling for the inactive language")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129363
@pytest.mark.traceability("ADO-134239")
def test_header_language_switcher_shows_correct_inactive_language_label(page):
    # ADO-134239 | PBI 129363
    # Arrange
    header = HeaderComponent(page)

    # Act
    with allure.step("Open the site with language EN active"):
        header.open_home()

    with allure.step("Read the language switcher's rendered style"):
        style = header.language_switcher_style()

    with allure.step("Inspect language switcher button label"):
        label = header.language_switcher_label()

    # Assert
    assert style["width"] == 32
    assert style["height"] == 32
    assert style["borderRadius"] == "8px"
    assert style["backgroundColor"] == "rgb(237, 237, 237)"  # #EDEDED
    assert label == "AR"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "400"  # "Regular"
    assert style["fontSize"] == "14px"
    assert style["color"] == "rgb(108, 108, 107)"  # #6C6C6B


@allure.epic("GLOBAL")
@allure.feature("Site Header")
@allure.story("Header persists identically across pages")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The header persists identically across different pages of the site")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129363
@pytest.mark.traceability("ADO-134244")
def test_header_persists_identically_across_pages(page):
    # ADO-134244 | PBI 129363
    # Arrange
    header = HeaderComponent(page)

    # Act
    with allure.step("Open the Home page"):
        header.open_home()
        home_fingerprint = header.header_fingerprint()

    with allure.step("Open the About Us page via the header's own nav link"):
        header.open_about_us_via_nav()
        about_us_fingerprint = header.header_fingerprint()

    with allure.step("Open the Home page, then the Contact Us page via the header's own nav link"):
        header.open_home()
        header.open_contact_us_via_nav()
        contact_us_fingerprint = header.header_fingerprint()

    # Assert
    assert home_fingerprint == about_us_fingerprint, "header rendering differs between Home and About Us"
    assert home_fingerprint == contact_us_fingerprint, "header rendering differs between Home and Contact Us"


@allure.epic("GLOBAL")
@allure.feature("Site Header")
@allure.story("Nav dropdown collapsed state")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The nav dropdown remains collapsed until user interaction")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129363
@pytest.mark.traceability("ADO-134249")
def test_header_nav_dropdown_remains_collapsed_until_interaction(page):
    # ADO-134249 | PBI 129363
    # Arrange
    header = HeaderComponent(page)

    # Act
    with allure.step("Open a published page (home)"):
        header.open_home()

    with allure.step("Inspect a nav item with sub-menu before hovering"):
        submenu_collapsed = header.is_nav_submenu_collapsed_before_interaction()
        chevron_visible = header.nav_item_with_submenu_shows_chevron()

    # Assert
    assert submenu_collapsed, "the dropdown panel should not be rendered/visible before interaction"
    assert chevron_visible, "the chevron affordance should still show before interaction"

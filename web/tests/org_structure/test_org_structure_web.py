"""
web/tests/org_structure/test_org_structure_web.py — Web-tagged cases for
PBI 129399 (QC-ABOUT-007 — Organizational Structure), sourced verbatim from
the approved/injected Azure DevOps suite (see the automate-test-case batch
report for the full per-case classification, including the cases BLOCKED
below rather than scripted).

Real department names used (e.g. "Board of Directors (General Assembly)",
"General Director Office", "Legal Affairs Department", "Finance &
Administration Sector") come from the live qcdev.ihorizons.com tree
confirmed via Playwright MCP snapshot on 2026-08-23 — NOT invented, and NOT
always identical in wording to a case's own department-name wording (e.g.
133282 says "Finance Department"/"Finance"; the live tree's matching node is
"Finance & Administration Sector"). Where a case names a specific
department/unit that does not exist in the current environment at all
(Finance Department w/ no photo, Audit Unit, Legacy Unit, Payroll Unit), the
case is BLOCKED, not silently re-targeted at a substitute node.
"""

import allure
import pytest

from web.pages.org_structure.org_structure_page import OrgStructurePage


# ---------------------------------------------------------------------------
# 133251 — top-level structural elements render
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Page renders all top-level structural elements")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Organizational Structure page renders hero, title, breadcrumb, and toolbar")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133251")
def test_org_structure_top_level_elements_render(page):
    org_page = OrgStructurePage(page)

    with allure.step("Navigate to About Us > Organizational Structure"):
        org_page.open_org_structure()

    # Assert
    assert org_page.is_page_title_visible()
    assert org_page.page_title_text() == "Organizational Structure"
    assert org_page.is_breadcrumb_visible()
    assert org_page.is_toolbar_visible()
    assert org_page.is_chart_visible()


# ---------------------------------------------------------------------------
# 133252 — Page Title Figma tokens
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Page Title matches the Figma-verified design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133252")
def test_org_structure_page_title_design_tokens(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    style = org_page.node_computed_style(
        org_page.PAGE_TITLE, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )

    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("700", "bold")
    assert style["fontSize"] == "30px"
    assert style["lineHeight"] == "38px"
    assert style["color"] == "rgb(255, 255, 255)"


# ---------------------------------------------------------------------------
# 133253 — breadcrumb "Home" label Figma tokens
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Breadcrumb "Home" label matches the Figma-verified design tokens')
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133253")
def test_org_structure_breadcrumb_home_design_tokens(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    style = org_page.node_computed_style(
        org_page.BREADCRUMB_HOME_LINK, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )

    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("400", "normal")
    assert style["fontSize"] == "14px"
    assert style["lineHeight"] == "22px"
    assert style["color"] == "rgb(255, 255, 255)"


# ---------------------------------------------------------------------------
# 133254 — search field placeholder Figma tokens
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Search field placeholder matches the Figma-verified design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133254")
def test_org_structure_search_placeholder_design_tokens(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    placeholder = page.locator(org_page.SEARCH_INPUT).get_attribute("placeholder")
    style = org_page.node_computed_style(
        org_page.SEARCH_INPUT,
        ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color", "borderWidth", "borderRadius"],
    )

    assert placeholder == "Search departments, leaders or titles..."
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("400", "normal")
    assert style["fontSize"] == "14px"
    assert style["lineHeight"] == "22px"
    assert style["color"] == "rgb(168, 168, 167)"
    assert style["borderWidth"] == "1px"
    assert style["borderRadius"] == "8px"


# ---------------------------------------------------------------------------
# 133255 — toolbar pill buttons Figma tokens
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Toolbar buttons match the Figma-verified pill design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133255")
def test_org_structure_toolbar_button_design_tokens(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    style = org_page.node_computed_style(
        org_page.EXPAND_ALL_BTN,
        [
            "fontFamily", "fontWeight", "fontSize", "lineHeight", "color",
            "backgroundColor", "borderWidth", "borderRadius",
        ],
    )

    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("600", "semibold")
    assert style["fontSize"] == "14px"
    assert style["lineHeight"] == "22px"
    assert style["color"] == "rgb(74, 74, 73)"
    assert style["backgroundColor"] == "rgb(255, 255, 255)"
    assert style["borderWidth"] == "1px"
    assert style["borderRadius"] in ("9999px", "624.9375px")


# ---------------------------------------------------------------------------
# 133256 — Department Name node-card token
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Department Name on a node card matches the Figma-verified design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133256")
def test_org_structure_department_name_design_tokens(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()
    department = "Board of Directors (General Assembly)"

    assert org_page.is_node_visible(department)

    style = org_page.node_computed_style(
        org_page.node_dept_locator(department),
        ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"],
    )

    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("500", "medium")
    assert style["fontSize"] == "16px"
    assert style["lineHeight"] == "24px"
    assert style["color"] == "rgb(145, 23, 49)"


# ---------------------------------------------------------------------------
# 133257 — Person Name node-card token
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Person Name on a node card matches the Figma-verified design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133257")
def test_org_structure_person_name_design_tokens(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()
    department = "Board of Directors (General Assembly)"

    style = org_page.node_computed_style(
        org_page.node_person_name_locator(department),
        ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"],
    )

    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("500", "medium")
    assert style["fontSize"] == "14px"
    assert style["lineHeight"] == "22px"
    assert style["color"] == "rgb(29, 29, 27)"


# ---------------------------------------------------------------------------
# 133258 — Person Title node-card token
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Person Title on a node card matches the Figma-verified design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133258")
def test_org_structure_person_title_design_tokens(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()
    department = "Board of Directors (General Assembly)"

    style = org_page.node_computed_style(
        org_page.node_person_title_locator(department),
        ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"],
    )

    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("400", "normal")
    assert style["fontSize"] == "12px"
    assert style["lineHeight"] == "18px"
    assert style["color"] == "rgb(168, 168, 167)"


# ---------------------------------------------------------------------------
# 133260 — connector lines depict parent/child relationships
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Chart connectors")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Connector lines correctly depict parent-child relationships in the chart")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133260")
def test_org_structure_connectors_depict_parent_child(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    # Assert: "General Director Office" renders as a structural (and
    # therefore connector-linked) child of "Board of Directors (General
    # Assembly)", and is NOT nested under an unrelated node.
    assert org_page.is_child_nested_under_parent(
        "Board of Directors (General Assembly)", "General Director Office"
    )
    assert not org_page.is_child_nested_under_parent(
        "General Director Office", "Board of Directors (General Assembly)"
    )


# ---------------------------------------------------------------------------
# 133261 — RTL mirroring in Arabic
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Organizational Structure page renders mirrored in Arabic (RTL)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129399
@pytest.mark.traceability("133261")
def test_org_structure_renders_rtl_in_arabic(page):
    org_page = OrgStructurePage(page)

    with allure.step("Load the page in the Arabic locale"):
        org_page.open_org_structure(locale="ar")

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")

    # Assert
    assert dir_attr == "rtl"
    assert org_page.is_toolbar_visible()
    assert org_page.is_chart_visible()


# ---------------------------------------------------------------------------
# 133262 — Arabic text on nodes/toolbar
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Node and toolbar text displays in Arabic when the AR locale is active")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129399
@pytest.mark.traceability("133262")
def test_org_structure_arabic_locale_text(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure(locale="ar")

    search_placeholder = page.locator(org_page.SEARCH_INPUT).get_attribute("placeholder")

    # Assert: toolbar search placeholder is Arabic script, not the EN default.
    assert search_placeholder is not None
    assert search_placeholder != "Search departments, leaders or titles..."
    assert any("؀" <= ch <= "ۿ" for ch in search_placeholder)


# ---------------------------------------------------------------------------
# 133263 — mobile viewport responsiveness (375px)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Organizational Structure page is responsive on a mobile viewport")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129399
@pytest.mark.traceability("133263")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_org_structure_responsive_mobile_viewport(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert
    assert scroll_width <= client_width + 1  # no horizontal overflow
    assert org_page.is_toolbar_visible()
    assert org_page.is_chart_visible()


# ---------------------------------------------------------------------------
# 133265 — fullscreen toggle icon reflects state
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Toolbar controls")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Fullscreen toggle icon visually reflects the current view state")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129399
@pytest.mark.traceability("133265")
def test_org_structure_fullscreen_icon_reflects_state(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    pressed_before = page.locator(org_page.FULLSCREEN_TOGGLE_BTN).get_attribute("aria-pressed")

    with allure.step("Click the fullscreen toggle icon"):
        org_page.toggle_fullscreen()

    pressed_after = page.locator(org_page.FULLSCREEN_TOGGLE_BTN).get_attribute("aria-pressed")

    # Assert
    assert org_page.is_fullscreen_active()
    assert pressed_after != pressed_before


# ---------------------------------------------------------------------------
# 133267 — renders on latest Chrome desktop (framework's default engine)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Compatibility / Browser matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Org chart renders correctly on the latest Chrome desktop browser")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129399
@pytest.mark.traceability("133267")
def test_org_structure_renders_on_chrome(page):
    # core/web/browser.py launches Chromium unconditionally — this IS the
    # "latest Chrome desktop" run for this framework.
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    # Assert
    assert org_page.is_chart_visible()
    assert org_page.is_toolbar_visible()
    org_page.expand_all()
    org_page.collapse_all()
    org_page.reset_view()


# ---------------------------------------------------------------------------
# 133269 — tablet-sized viewport (768px)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Org chart renders correctly on a tablet-sized viewport (768px)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129399
@pytest.mark.traceability("133269")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_org_structure_tablet_viewport(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert
    assert scroll_width <= client_width + 1
    assert org_page.is_toolbar_visible()
    assert org_page.is_chart_visible()


# ---------------------------------------------------------------------------
# 133271 — unauthenticated visitor can view the published page
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Public access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unauthenticated public visitor can view the published Organizational Structure page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129399
@pytest.mark.traceability("133271")
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_org_structure_unauthenticated_visitor_can_view(page):
    org_page = OrgStructurePage(page)

    with allure.step("Without logging in, navigate to About Us > Organizational Structure"):
        org_page.open_org_structure()

    # Assert
    assert org_page.is_chart_visible()
    assert org_page.is_toolbar_visible()
    assert "login" not in page.url.lower()


# ---------------------------------------------------------------------------
# 133277 — default load: fully expanded at 100% zoom
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Default chart state")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Tree loads fully expanded at 100% zoom by default")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133277")
def test_org_structure_default_expanded_at_100_percent(page):
    org_page = OrgStructurePage(page)

    with allure.step("From the homepage, open Main Menu > About Us > Organizational Structure"):
        org_page.open_org_structure()

    # Assert
    assert org_page.zoom_percentage() == 100
    assert org_page.is_node_visible("Board of Directors (General Assembly)")
    assert org_page.is_node_visible("General Director Office")
    assert org_page.is_node_visible("Legal Affairs Department")


# ---------------------------------------------------------------------------
# 133278 — clicking a parent node collapses its branch, no reload
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Expand / collapse")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking a parent node collapses its branch without a page reload")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133278")
def test_org_structure_click_parent_collapses_branch(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()
    url_before = page.url

    with allure.step('Click the "General Director Office" node'):
        org_page.toggle_branch("General Director Office")

    # Assert
    assert not org_page.is_branch_expanded("General Director Office")
    assert not org_page.is_node_visible("Legal Affairs Department")
    assert page.url == url_before
    assert org_page.is_node_visible("Board of Directors (General Assembly)")


# ---------------------------------------------------------------------------
# 133279 — clicking a collapsed parent re-expands its branch
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Expand / collapse")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a collapsed parent node re-expands its branch")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133279")
def test_org_structure_click_collapsed_parent_re_expands(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()
    org_page.toggle_branch("General Director Office")
    assert not org_page.is_node_visible("Legal Affairs Department")

    with allure.step('With "General Director Office" collapsed, click it again'):
        org_page.toggle_branch("General Director Office")

    # Assert
    assert org_page.is_branch_expanded("General Director Office")
    assert org_page.is_node_visible("Legal Affairs Department")


# ---------------------------------------------------------------------------
# 133280 — Expand All expands every branch
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Expand / collapse")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Expand All expands every branch regardless of prior collapsed state")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133280")
def test_org_structure_expand_all_expands_every_branch(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    with allure.step("Collapse two separate branches manually"):
        org_page.toggle_branch("General Director Office")
        org_page.toggle_branch("Board of Directors (General Assembly)")
    assert not org_page.is_node_visible("Legal Affairs Department")

    with allure.step('Click "Expand All"'):
        org_page.expand_all()

    # Assert
    assert org_page.is_node_visible("General Director Office")
    assert org_page.is_node_visible("Legal Affairs Department")


# ---------------------------------------------------------------------------
# 133281 — Collapse All collapses the entire tree to root level
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Expand / collapse")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Collapse All collapses the entire tree to root level")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133281")
def test_org_structure_collapse_all_to_root(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()
    assert org_page.is_node_visible("General Director Office")

    with allure.step('Click "Collapse All"'):
        org_page.collapse_all()

    # Assert
    assert org_page.is_node_visible("Board of Directors (General Assembly)")
    assert not org_page.is_node_visible("General Director Office")


# ---------------------------------------------------------------------------
# 133282 — searching for a department highlights/navigates to the match
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Search")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Searching for a department name highlights and navigates to the matching node")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133282")
def test_org_structure_search_highlights_matching_node(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    with allure.step('Type "Finance" into the search field'):
        org_page.search("Finance")

    matches = org_page.matched_department_texts()

    # Assert: the finance-named node is highlighted (live tree's finance
    # node is "Finance & Administration Sector" — see module docstring).
    assert any("Finance" in m for m in matches)
    assert org_page.is_node_visible("Finance & Administration Sector")


# ---------------------------------------------------------------------------
# 133283 — non-matching search shows empty-result state, no crash
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Search")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Searching for a non-matching term displays an empty-result state without breaking the chart")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133283")
def test_org_structure_search_no_match_empty_state(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    with allure.step('Type "Nonexistent Dept XYZ" into the search field'):
        org_page.search("Nonexistent Dept XYZ")

    # Assert
    assert org_page.is_empty_state_visible()
    assert org_page.empty_state_text() == "No departments match your search."
    assert org_page.is_chart_visible()


# ---------------------------------------------------------------------------
# 133284 — zoom controls resize chart and update % indicator
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Zoom controls")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Zoom controls resize the chart within configured limits and update the percentage indicator")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133284")
def test_org_structure_zoom_controls_update_indicator(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()
    assert org_page.zoom_percentage() == 100

    with allure.step("Click zoom-in three times"):
        org_page.click_zoom_in(3)
    zoomed_in = org_page.zoom_percentage()

    with allure.step("Click zoom-out five times"):
        org_page.click_zoom_out(5)
    zoomed_out = org_page.zoom_percentage()

    # Assert
    assert zoomed_in > 100
    assert zoomed_out < zoomed_in
    assert zoomed_out >= 1  # never below a real (non-negative/zero) minimum


# ---------------------------------------------------------------------------
# 133285 — Reset View restores default zoom, position, expand state
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Zoom controls")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Reset View restores default zoom, position, and expand state")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133285")
def test_org_structure_reset_view_restores_defaults(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    with allure.step("Zoom to a non-default level and collapse one branch"):
        org_page.click_zoom_in(5)
        org_page.toggle_branch("General Director Office")
    assert org_page.zoom_percentage() != 100
    assert not org_page.is_node_visible("Legal Affairs Department")

    with allure.step('Click "Reset View"'):
        org_page.reset_view()

    # Assert
    assert org_page.zoom_percentage() == 100
    assert org_page.is_node_visible("Legal Affairs Department")


# ---------------------------------------------------------------------------
# 133286 — fullscreen toggle enters and exits fullscreen mode
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Toolbar controls")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Fullscreen toggle enters and exits fullscreen mode correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133286")
def test_org_structure_fullscreen_enter_and_exit(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    with allure.step("Click the fullscreen icon"):
        org_page.toggle_fullscreen()
    assert org_page.is_fullscreen_active()

    with allure.step("Click the icon again (exit)"):
        org_page.toggle_fullscreen()

    # Assert
    assert not org_page.is_fullscreen_active()


# ---------------------------------------------------------------------------
# 133287 — standard error page when content is unavailable
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Negative / error handling")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Standard error page is shown when the Organizational Structure page fails to load")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129399
@pytest.mark.traceability("133287")
def test_org_structure_standard_error_page_on_unavailable_content(page):
    org_page = OrgStructurePage(page)

    from config.settings import web_url

    with allure.step("Navigate to the Organizational Structure URL while content is unavailable"):
        resp = page.goto(
            web_url("/web/qatar-chamber/about-us/organizational-structure-unavailable-content-check")
        )

    # Assert
    assert resp is not None
    assert resp.status == 404
    assert not org_page.is_chart_visible()


# ---------------------------------------------------------------------------
# 133365 — collapsing a top-level parent hides all nested descendants
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Collapsing a top-level parent hides all descendants across every nested level")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129399
@pytest.mark.traceability("133365")
def test_org_structure_collapse_hides_all_nested_descendants(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()
    assert org_page.is_node_visible("Legal Affairs Department")
    assert org_page.is_node_visible("General Director Office")

    with allure.step('Click the "Board of Directors (General Assembly)" node to collapse it'):
        org_page.toggle_branch("Board of Directors (General Assembly)")

    # Assert: not just the direct child, but the grandchild too, is hidden.
    assert not org_page.is_node_visible("General Director Office")
    assert not org_page.is_node_visible("Legal Affairs Department")


# ---------------------------------------------------------------------------
# 133366 — Reset View with search + non-default zoom both active
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reset View restores defaults correctly when search filter and non-default zoom are both active")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129399
@pytest.mark.traceability("133366")
def test_org_structure_reset_view_with_search_and_zoom_active(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    with allure.step("Zoom to a non-default level"):
        org_page.click_zoom_in(5)

    with allure.step('Enter "Finance" in the search field'):
        org_page.search("Finance")
    assert any("Finance" in m for m in org_page.matched_department_texts())

    with allure.step('Click "Reset View"'):
        org_page.reset_view()

    # Assert
    assert org_page.zoom_percentage() == 100
    assert org_page.is_node_visible("Legal Affairs Department")


# ---------------------------------------------------------------------------
# 133372 — rapid repeated Expand All / Collapse All clicks stay stable
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Rapid repeated clicks on Expand All / Collapse All do not break the chart's render state")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129399
@pytest.mark.traceability("133372")
def test_org_structure_rapid_expand_collapse_stays_stable(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()

    with allure.step('Rapidly click "Collapse All" then "Expand All" five times'):
        for _ in range(5):
            org_page.collapse_all()
            org_page.expand_all()

    # Assert: ends fully expanded, no duplicated nodes, no frozen UI.
    assert org_page.is_node_visible("Legal Affairs Department")
    assert page.locator(org_page.node_dept_locator("Legal Affairs Department")).count() == 1
    assert org_page.is_toolbar_visible()


# ---------------------------------------------------------------------------
# 133374 — zoom clamps at configured minimum/maximum
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Organizational Structure")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Zooming reaches and clamps at the configured minimum/maximum zoom limits")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129399
@pytest.mark.traceability("133374")
def test_org_structure_zoom_clamps_at_limits(page):
    org_page = OrgStructurePage(page)
    org_page.open_org_structure()
    assert org_page.zoom_percentage() == 100

    with allure.step("Click zoom-in repeatedly well past the visually apparent maximum"):
        org_page.click_zoom_in(50)
    max_zoom = org_page.zoom_percentage()
    org_page.click_zoom_in(1)

    with allure.step("Click zoom-out repeatedly well past the visually apparent minimum"):
        org_page.click_zoom_out(80)
    min_zoom = org_page.zoom_percentage()
    org_page.click_zoom_out(1)

    # Assert: an extra click at each extreme changes nothing further (clamped).
    assert org_page.zoom_percentage() == min_zoom
    org_page.click_zoom_in(50)
    assert org_page.zoom_percentage() == max_zoom

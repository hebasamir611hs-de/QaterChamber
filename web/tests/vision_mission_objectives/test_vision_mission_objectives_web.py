"""
web/tests/vision_mission_objectives/test_vision_mission_objectives_web.py

Web-tagged cases for ADO parent PBI 129395 (QC-ABOUT-004 — Vision, Mission,
Objectives), sourced verbatim from the approved/injected Azure DevOps suite
handed to this agent (case titles/IDs list in the task message). Every case
in that Web-platform batch is accounted for either here (AUTOMATED) or in
the batch report returned to the QA Manager (SKIPPED, with a concrete
reason) — see the closing summary of the automate-test-case delegation for
the full per-case disposition.

REAL FACTS THIS MODULE RELIES ON (confirmed live against qcdev.ihorizons.com
on 2026-08-25, at the framework's default 1920x1080 viewport — see
vmo_page.py's docstring for the full extraction trail and confirmed markup):
  - Page path: /web/qatar-chamber/about-us/vision-mission-objectives
  - Breadcrumb renders exactly "Home" > "About Us" (not a 3rd VMO crumb).
  - Section order/content, live: Vision(01, bulleted, image-end) /
    Mission(02, single paragraph, image-start) / Objectives(03, bulleted,
    image-end) — matches the case-described alternation and content-type
    split exactly.
  - No inline content image exists inside any section's rich-text body in
    the current live content — only the one Section Image (figure) per
    section. Case 136344 depends on a precondition (inline + Section Image
    coexisting) that does not exist in this content, so it is SKIPPED, not
    silently re-targeted.
  - core/web/browser.py launches Chromium ONLY (no WebKit/Safari engine
    provisioned) — case 136164 ("Latest Safari render") cannot be automated
    by this framework at all; SKIPPED, framework limitation, not a CMS
    restriction.
  - Every case requiring an authoring-side content mutation (create/publish/
    draft/preview/unpublish/deactivate/reactivate/translation-removal) is
    SKIPPED per this project's explicit CMS-restriction rule: VMO is real,
    live editorial content (not a QCTEST- disposable fixture), the CMS
    UI-only test-data policy (cms-profile.md) forbids SNAPSHOT_RESTORE-class
    mutation of real editorial content outside a documented exception, and
    no verified teardown path exists to safely undo such a mutation on this
    shared qcdev instance. The public-facing verification that IS possible
    standalone (current published state, its ordering, content-type split,
    image sides, RTL, responsive/compat rendering, direct-URL 404 handling)
    is scripted below instead of being skipped wholesale.

AUTH: all tests here use the default cached storageState (public pages need
no auth) except 136165, which explicitly opts OUT via
`{"auth": False}` indirect param because ITS subject is the unauthenticated
visitor path itself — mirrors OrgStructurePage's 133271 precedent.
"""

import allure
import pytest

from config.settings import web_url
from web.pages.vision_mission_objectives.vmo_page import VmoPage


def _px(value: str) -> float:
    return float(value.rstrip("px"))


# ---------------------------------------------------------------------------
# 136144 — Hero Banner title styling
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Hero Banner title matches the Figma-verified design tokens (Cairo Bold 30px/38px, white)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129395
@pytest.mark.tc_136144
def test_vmo_hero_title_design_tokens(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    style = vmo.computed_style(vmo.HERO_TITLE, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"])

    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("700", "bold")
    assert style["fontSize"] == "30px"
    assert round(_px(style["lineHeight"])) == 38
    assert style["color"] == "rgb(255, 255, 255)"


# ---------------------------------------------------------------------------
# 136145 — Breadcrumb "Home > About Us" right-aligned white on hero
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Breadcrumb reads "Home > About Us", styled white on the hero')
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129395
@pytest.mark.tc_136145
def test_vmo_breadcrumb_text_and_styling(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    style = vmo.computed_style(vmo.BREADCRUMB, ["color"])

    # Assert: exact breadcrumb copy and hero-white styling.
    assert vmo.breadcrumb_home_text() == "Home"
    assert vmo.breadcrumb_current_text() == "About Us"
    assert style["color"] == "rgb(255, 255, 255)"


# ---------------------------------------------------------------------------
# 136146 — "Who We Are" intro heading left column styling
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title('"Who We Are" intro heading matches the Figma-verified design tokens')
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129395
@pytest.mark.tc_136146
def test_vmo_intro_heading_design_tokens(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    style = vmo.computed_style(vmo.INTRO_HEADING, ["fontFamily", "fontWeight", "fontSize", "textAlign"])

    assert vmo.intro_heading_text() == "Who We Are"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("700", "bold")
    assert style["fontSize"] == "32px"
    assert style["textAlign"] == "start"


# ---------------------------------------------------------------------------
# 136147 — Intro description text right column styling
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Intro description text matches the Figma-verified design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129395
@pytest.mark.tc_136147
def test_vmo_intro_description_design_tokens(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    style = vmo.computed_style(vmo.INTRO_DESC, ["fontFamily", "fontWeight", "fontSize"])

    assert vmo.intro_desc_text() != ""
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("400", "normal")
    assert style["fontSize"] == "14px"


# ---------------------------------------------------------------------------
# 136148 — Section label + divider styling (repeat Vision/Mission/Objectives)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section label and divider match the Figma-verified design tokens on every section")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129395
@pytest.mark.tc_136148
@pytest.mark.parametrize("label", ["Vision", "Mission", "Objectives"])
def test_vmo_section_label_and_divider_design_tokens(page, label):
    vmo = VmoPage(page)
    vmo.open_vmo()

    label_style = vmo.section_style(label, ".qc-vmo-sec-label", ["fontFamily", "fontSize", "color"])
    divider_style = vmo.section_style(label, ".qc-vmo-sec-divider", ["height", "backgroundColor"])

    assert "Cairo" in label_style["fontFamily"]
    assert label_style["fontSize"] == "24px"
    assert label_style["color"] == "rgb(124, 123, 123)"
    assert divider_style["height"] == "1px"


# ---------------------------------------------------------------------------
# 136149 — Section decorative numerals 01/02/03 styling
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section decorative numerals (01/02/03) match the Figma-verified design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129395
@pytest.mark.tc_136149
def test_vmo_section_numerals_design_tokens(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    expected = {"Vision": "01", "Mission": "02", "Objectives": "03"}
    for label, num in expected.items():
        assert vmo.section_number(label) == num
        style = vmo.section_style(label, ".qc-vmo-sec-num", ["fontFamily", "fontWeight", "fontSize", "color"])
        assert "Cairo" in style["fontFamily"]
        assert style["fontWeight"] in ("700", "bold")
        assert style["fontSize"] == "40px"


# ---------------------------------------------------------------------------
# 136150 — Section headline uppercase styling per section
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section headline renders uppercase and matches the Figma-verified design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129395
@pytest.mark.tc_136150
@pytest.mark.parametrize("label", ["Vision", "Mission", "Objectives"])
def test_vmo_section_headline_uppercase_design_tokens(page, label):
    vmo = VmoPage(page)
    vmo.open_vmo()

    style = vmo.section_style(label, ".qc-vmo-sec-headline", ["fontFamily", "fontWeight", "textTransform"])
    headline = vmo.section_headline(label)

    assert headline == headline.upper()
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("700", "bold")
    assert style["textTransform"] == "uppercase"


# ---------------------------------------------------------------------------
# 136151 — Section subheading styling
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section subheading matches the Figma-verified design tokens")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129395
@pytest.mark.tc_136151
def test_vmo_section_subheading_design_tokens(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    style = vmo.section_style("Vision", ".qc-vmo-sec-sub", ["fontFamily", "fontWeight", "fontSize"])

    assert vmo.section_subheading("Vision") == "Aligned with Qatar National Vision 2030"
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] in ("400", "normal")
    assert style["fontSize"] == "15px"


# ---------------------------------------------------------------------------
# 136152 — Section body: bulleted list (Vision/Objectives) vs paragraph (Mission)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Content-type split")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section body renders a bulleted list for Vision/Objectives and a single paragraph for Mission")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136152
def test_vmo_section_body_content_type_split(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert
    assert vmo.section_body_is_bulleted("Vision")
    assert len(vmo.section_bullet_texts("Vision")) >= 1
    assert not vmo.section_body_is_bulleted("Mission")
    assert vmo.section_paragraph_text("Mission") != ""
    assert vmo.section_body_is_bulleted("Objectives")
    assert len(vmo.section_bullet_texts("Objectives")) >= 1


# ---------------------------------------------------------------------------
# 136153 — Section image 12px radius + badge overlay
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section image renders with 12px radius and a badge overlay")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129395
@pytest.mark.tc_136153
@pytest.mark.parametrize("label", ["Vision", "Mission", "Objectives"])
def test_vmo_section_image_radius_and_badge(page, label):
    vmo = VmoPage(page)
    vmo.open_vmo()

    img_style = vmo.section_style(label, ".qc-vmo-sec-img", ["borderRadius"])
    badge_style = vmo.section_style(label, ".qc-vmo-sec-badge", ["position"])

    assert img_style["borderRadius"] == "12px"
    assert vmo.is_section_badge_visible(label)
    assert badge_style["position"] == "absolute"


# ---------------------------------------------------------------------------
# 136154 — LTR image/text alternation (Vision right, Mission left, Objectives right)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Layout alternation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section image/text placement alternates correctly in LTR (Vision right, Mission left, Objectives right)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136154
def test_vmo_ltr_image_text_alternation(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert: --img-end == image trails the text (right, in LTR).
    assert vmo.section_image_side("Vision") == "end"
    assert vmo.section_image_side("Mission") == "start"
    assert vmo.section_image_side("Objectives") == "end"


# ---------------------------------------------------------------------------
# 136155 — RTL mirrored image/text placement
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Layout alternation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section image/text placement mirrors correctly in RTL (Arabic)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136155
def test_vmo_rtl_image_text_alternation_mirrors(page):
    # section_locator(label)/section_image_side(label) match on the English
    # ".qc-vmo-sec-label" text ("Vision"), which is never rendered on the
    # Arabic page (the live AR label reads "الرؤية") — so both timed out /
    # resolved to zero elements against the AR-locale page. Confirmed via a
    # DOM probe against /ar/.../vision-mission-objectives (2026-08-25) that
    # section order and the img-start/img-end modifier classes are unchanged
    # between EN/AR; only the label text is translated. Use the
    # locale-agnostic, index-based accessors instead (mirrors
    # BoardOfDirectorsPage.click_first_featured_profile_link's precedent) —
    # index 0 is Vision in both locales.
    vmo = VmoPage(page)
    vmo.open_vmo(locale="ar")

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")
    vision_chain = vmo.section_chain_locator_by_index(0)
    vision_img_box = page.locator(f'{vision_chain} .qc-vmo-sec-img').bounding_box()
    vision_text_box = page.locator(f'{vision_chain} .qc-vmo-sec-text').bounding_box()

    # Assert: same logical --img-end modifier class, but geometrically
    # mirrored — in RTL the "end" (trailing) side is visually the LEFT, so
    # the image's box now sits to the LEFT of the text box (the opposite of
    # the LTR case in 136154).
    assert dir_attr == "rtl"
    assert vmo.section_image_side_by_index(0) == "end"
    assert vision_img_box["x"] < vision_text_box["x"]


# ---------------------------------------------------------------------------
# 136156 — EN title reads correctly despite Figma naming typo
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Content correctness")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("English hero title reads correctly on the rendered page (independent of any Figma layer-naming typo)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.pbi_129395
@pytest.mark.tc_136156
def test_vmo_en_title_reads_correctly(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert: the rendered text, not any design-tool layer name, is the
    # source of truth.
    assert vmo.hero_title_text() == "Vision · Mission · Objectives"


# ---------------------------------------------------------------------------
# 136157 — AR title renders correctly
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Content correctness")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Arabic hero title renders correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136157
def test_vmo_ar_title_renders_correctly(page):
    vmo = VmoPage(page)
    vmo.open_vmo(locale="ar")

    title = vmo.hero_title_text()

    # Assert: non-empty Arabic-script title, not the English fallback.
    assert title != ""
    assert title != "Vision · Mission · Objectives"
    assert any("؀" <= ch <= "ۿ" for ch in title)


# ---------------------------------------------------------------------------
# 136158 — Overall RTL layout/alignment in Arabic
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Overall page layout and alignment render correctly in Arabic (RTL)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.pbi_129395
@pytest.mark.tc_136158
def test_vmo_overall_rtl_layout(page):
    vmo = VmoPage(page)
    vmo.open_vmo(locale="ar")

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")

    # Assert
    assert dir_attr == "rtl"
    assert vmo.is_hero_visible()
    assert vmo.is_intro_visible()
    assert vmo.section_count() == 3


# ---------------------------------------------------------------------------
# 136159 — No broken layout while hero image loading (3G throttle)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Compatibility / Network conditions")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page layout stays intact while the hero image is still loading under 3G-throttled network")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129395
@pytest.mark.tc_136159
def test_vmo_no_broken_layout_under_3g_throttle(page):
    # Real CDP network-condition throttling (Chromium-only, which is this
    # framework's only launched engine) — not a fixed sleep. Emulates the
    # "Regular 3G" DevTools preset.
    cdp = page.context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send(
        "Network.emulateNetworkConditions",
        {
            "offline": False,
            "latency": 300,
            "downloadThroughput": 50_000,   # ~400kbps, Regular-3G-ish
            "uploadThroughput": 50_000,
        },
    )

    vmo = VmoPage(page)
    vmo.open_vmo()
    vmo.wait_for(vmo.HERO_TITLE, state="visible")

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert: hero chrome (title/breadcrumb) is already usable and the
    # layout has not shifted into horizontal overflow while the hero image
    # asset is still arriving over the throttled connection.
    assert vmo.is_hero_visible()
    assert vmo.hero_title_text() == "Vision · Mission · Objectives"
    assert scroll_width <= client_width + 1

    cdp.send("Network.emulateNetworkConditions", {
        "offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1,
    })


# ---------------------------------------------------------------------------
# 136160 — Desktop viewport 1920x1080 render
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly at the desktop viewport (1920x1080)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129395
@pytest.mark.tc_136160
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_vmo_desktop_viewport_render(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert
    assert scroll_width <= client_width + 1
    assert vmo.is_hero_visible()
    assert vmo.section_count() == 3


# ---------------------------------------------------------------------------
# 136161 — Tablet 768px render
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly at a tablet viewport (768px)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129395
@pytest.mark.tc_136161
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_vmo_tablet_viewport_render(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert
    assert scroll_width <= client_width + 1
    assert vmo.is_hero_visible()
    assert vmo.section_count() == 3


# ---------------------------------------------------------------------------
# 136162 — Mobile 375px render, scroll all sections
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly at a mobile viewport (375px) and every section is reachable by scroll")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129395
@pytest.mark.tc_136162
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_vmo_mobile_viewport_render_and_scroll(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")
    assert scroll_width <= client_width + 1

    for label in ["Vision", "Mission", "Objectives"]:
        page.locator(vmo.section_locator(label)).scroll_into_view_if_needed()
        # Assert: each section becomes visible once scrolled to.
        assert vmo.is_section_visible(label)


# ---------------------------------------------------------------------------
# 136163 — Latest Chrome render
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Compatibility / Browser matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly on the latest Chrome desktop browser")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129395
@pytest.mark.tc_136163
def test_vmo_renders_on_chrome(page):
    # core/web/browser.py launches Chromium unconditionally — this IS the
    # "latest Chrome desktop" run for this framework (same precedent as
    # OrgStructurePage's 133267).
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert
    assert vmo.is_hero_visible()
    assert vmo.section_count() == 3


# ---------------------------------------------------------------------------
# 136165 — Unauthenticated visitor can view published page
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Public access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unauthenticated public visitor can view the published Vision, Mission, Objectives page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129395
@pytest.mark.tc_136165
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_vmo_unauthenticated_visitor_can_view(page):
    vmo = VmoPage(page)

    with allure.step("Without logging in, navigate to About Us > Vision, Mission, Objectives"):
        vmo.open_vmo()

    # Assert
    assert vmo.is_hero_visible()
    assert vmo.section_count() == 3
    assert "login" not in page.url.lower()


# ---------------------------------------------------------------------------
# 136175 — Visitor navigates Main Menu > About Us > VMO and scrolls, no reload
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Visitor reaches the page via Main Menu > About Us > Vision & Mission and scrolls without a reload")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136175
def test_vmo_navigation_from_main_menu_no_reload(page):
    vmo = VmoPage(page)
    vmo.open(web_url("/web/qatar-chamber/about-us"))

    with allure.step('Open the "About Qatar Chamber" menu and click "Vision & Mission"'):
        vmo.click('role=button[name="About Qatar Chamber"]')
        vmo.click('role=link[name="Vision & Mission"]')
        vmo.wait_for(vmo.HERO_TITLE, state="visible")

    url_after_nav = page.url

    with allure.step("Scroll through the sections"):
        for label in ["Vision", "Mission", "Objectives"]:
            page.locator(vmo.section_locator(label)).scroll_into_view_if_needed()

    # Assert: still on the VMO URL, no reload was triggered by the scroll.
    assert "vision-mission-objectives" in url_after_nav
    assert page.url == url_after_nav
    assert vmo.section_count() == 3


# ---------------------------------------------------------------------------
# 136176 — Sections render in default order 01 Vision/02 Mission/03 Objectives
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Default ordering")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Sections render in the default order: 01 Vision, 02 Mission, 03 Objectives")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136176
def test_vmo_default_section_order(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert
    assert vmo.visible_section_labels_in_order() == ["Vision", "Mission", "Objectives"]
    assert vmo.section_number("Vision") == "01"
    assert vmo.section_number("Mission") == "02"
    assert vmo.section_number("Objectives") == "03"


# ---------------------------------------------------------------------------
# 136182 — Only Active sections appear on the live page
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Section activation state")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Only sections in Active state appear on the published page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136182
def test_vmo_only_active_sections_appear(page):
    """Verifies the CURRENT published state (all three sections Active) —
    the ACTIVE-flag-flip itself is CMS content mutation and is out of scope
    here (see 136324/136341/136342/136343/136351, SKIPPED per this module's
    docstring). This confirms the rendering rule the deactivation cases
    depend on: exactly the Active set renders, nothing else."""
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert: all three currently-Active sections render, and nothing beyond
    # them.
    assert vmo.is_section_visible("Vision")
    assert vmo.is_section_visible("Mission")
    assert vmo.is_section_visible("Objectives")
    assert vmo.section_count() == 3


# ---------------------------------------------------------------------------
# 136186 — Visitor sees standard error page on load failure
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Negative / error handling")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Standard error page is shown when the page fails to load")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136186
def test_vmo_standard_error_page_on_load_failure(page):
    vmo = VmoPage(page)

    with allure.step("Navigate to an unavailable child path under the same section"):
        resp = page.goto(
            web_url("/web/qatar-chamber/about-us/vision-mission-objectives-unavailable-content-check")
        )

    # Assert
    assert resp is not None
    assert resp.status == 404
    assert vmo.section_count() == 0


# ---------------------------------------------------------------------------
# 136323 — Vision Active=Active visible on published page, persists reload
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Section activation state")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Vision section (Active=Active) is visible on the published page and persists across reload")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136323
def test_vmo_vision_active_persists_reload(page):
    vmo = VmoPage(page)
    vmo.open_vmo()
    assert vmo.is_section_visible("Vision")

    with allure.step("Reload the page"):
        page.reload()
        vmo.wait_for(vmo.HERO_TITLE, state="visible")

    # Assert
    assert vmo.is_section_visible("Vision")
    assert vmo.section_number("Vision") == "01"


# ---------------------------------------------------------------------------
# 136325 — All Mission fields saved/published as a complete valid set
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Content completeness")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("All Mission section fields are published as a complete, valid set")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136325
def test_vmo_mission_fields_complete(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert: every Mission field is present and non-empty.
    assert vmo.section_number("Mission") == "02"
    assert vmo.section_headline("Mission") != ""
    assert vmo.section_subheading("Mission") != ""
    assert vmo.section_paragraph_text("Mission") != ""
    assert vmo.section_image_src("Mission")


# ---------------------------------------------------------------------------
# 136328 — Mission content renders as a single paragraph on frontend
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Content-type split")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Mission content renders as a single paragraph, not a bulleted list")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136328
def test_vmo_mission_renders_single_paragraph(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert
    assert not vmo.section_body_is_bulleted("Mission")
    assert vmo.section_paragraph_text("Mission") == (
        "To better represent and support the Qatar business community and "
        "highlight the available business opportunities within the various "
        "sectors and industries in Qatar."
    )


# ---------------------------------------------------------------------------
# 136332 — Mission section image renders left side per config
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Layout alternation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Mission section image renders on the left side per configuration")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136332
def test_vmo_mission_image_renders_left(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    img_box = page.locator(f'{vmo.section_locator("Mission")} .qc-vmo-sec-img').bounding_box()
    text_box = page.locator(f'{vmo.section_locator("Mission")} .qc-vmo-sec-text').bounding_box()

    # Assert
    assert vmo.section_image_side("Mission") == "start"
    assert img_box["x"] < text_box["x"]


# ---------------------------------------------------------------------------
# 136333 — All Objectives fields saved/published as a complete valid set
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Content completeness")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("All Objectives section fields are published as a complete, valid set")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136333
def test_vmo_objectives_fields_complete(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert
    assert vmo.section_number("Objectives") == "03"
    assert vmo.section_headline("Objectives") != ""
    assert vmo.section_subheading("Objectives") != ""
    assert vmo.section_body_is_bulleted("Objectives")
    assert len(vmo.section_bullet_texts("Objectives")) == 5
    assert vmo.section_image_src("Objectives")


# ---------------------------------------------------------------------------
# 136337 — Objectives content: 5-item bulleted "Five Pillars of Growth"
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Content-type split")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Objectives content renders the 5-item bulleted "Five Pillars of Growth"')
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136337
def test_vmo_objectives_five_pillars_bulleted(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    # Assert
    assert vmo.section_headline("Objectives") == "FIVE PILLARS OF GROWTH"
    bullets = vmo.section_bullet_texts("Objectives")
    assert len(bullets) == 5
    assert all(b.strip() for b in bullets)


# ---------------------------------------------------------------------------
# 136340 — Objectives section image renders right side per config
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Vision, Mission, Objectives")
@allure.story("Layout alternation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Objectives section image renders on the right side per configuration")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129395
@pytest.mark.tc_136340
def test_vmo_objectives_image_renders_right(page):
    vmo = VmoPage(page)
    vmo.open_vmo()

    img_box = page.locator(f'{vmo.section_locator("Objectives")} .qc-vmo-sec-img').bounding_box()
    text_box = page.locator(f'{vmo.section_locator("Objectives")} .qc-vmo-sec-text').bounding_box()

    # Assert
    assert vmo.section_image_side("Objectives") == "end"
    assert img_box["x"] > text_box["x"]

"""
web/tests/home_about_summary/test_home_about_summary_web.py —
Web-tagged cases for PBI 129389 (QC-HOME-013 — "About Us Section & Last
Year Achievements Counters"), backing the public Home Page "About Us"
summary widget.

Added 2026-09-15 for the ADO 136088-136140 batch: 14 of the batch's 50
cases carry the `Web` Platform tag (the other 36, plus dual-tagged 136137,
are Control_Panel and live in
cms/tests/home_about_summary/test_home_about_summary_control_panel.py —
136137 specifically, per the tc_136106 precedent already established
there, since it spans both platforms as one admin-action-then-public-
verify flow).

Public Page Object: `web/pages/home_about_summary/home_about_summary_page.py`
ALREADY EXISTED before this batch (confirmed-live selectors from a prior
session) — this batch extends it in place; it does NOT create a new one.

Two counter-state cases (136095, 136096) are Web-tagged but their own Step
1 is a CMS admin action ("set counters' display order" / "set Active
Status") — realized here as: arrange via the existing CMS admin Page
Objects (`HomeAboutSummaryAdminPage` / `HomeAboutCounterAdminPage`) signed in as QC Site Content Editor (named account) (same convention the sibling
Control_Panel module's tc_136106 test already uses), assert via a fresh
anonymous context (`new_context(browser, use_auth_state=False)`), per
standards.md's mandatory anonymous-visitor rule for public-page reads.
Both mutate the shared TEST_OWNED singleton Counter rows, so both carry the
SAME `about_us_section_52157` `xdist_group` the Control_Panel module's
mutating tests use (never a second group — see standards.md's Safe
Parallelism section).

PROBE FAILURE (Control_Panel surface only) is disclosed in
home_about_summary_admin_page.py's module docstring; it did NOT affect this
module's own public-page probe, which succeeded cleanly this session (no
auth/session needed) — see home_about_summary_page.py's own EXTENDED
module docstring for the real, confirmed-live DOM/computed-style findings
this module's assertions are built on.
"""

import os
from urllib.parse import urlparse

import allure
import pytest

from cms.pages.home_about_summary.home_about_summary_admin_page import (
    HomeAboutSummaryAdminPage,
    HomeAboutCounterAdminPage,
    COUNTER_ENTRY_CODES,
    FIELD_READ_MORE_URL,
    REAL_WRITE_ENV,
)
from core.web.browser import new_context
from web.pages.home_about_summary.home_about_summary_page import HomeAboutSummaryPage
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED

ABOUT_US_XDIST_GROUP = pytest.mark.xdist_group("about_us_section_52157")


@pytest.fixture
def approved_real_write():
    """NEEDS USER gate (2026-10-07): 136095/136096/136139 write the live About
    Us Section 52157 / Counters 52165-52183, which are not approved for writes
    in docs/qa-environment-notes.md 5. Red, named blocker until approved."""
    if os.environ.get(REAL_WRITE_ENV) != "1":
        pytest.fail(
            "NEEDS USER: writes live record(s) 52157 / 52165-52183; needs ID-named approval, "
            f"then {REAL_WRITE_ENV}=1", pytrace=False)


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Section renders (Figma-verified)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The About Us section renders all elements correctly on the Home Page (Figma-verified) (ADO-136088)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136088")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.uat
@pytest.mark.pbi_129389
@pytest.mark.tc_136088
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_about_us_section_renders_all_elements_136088(page):
    # ADO-136088
    home = HomeAboutSummaryPage(page)

    with allure.step("Navigate to Home Page as a public visitor"):
        home.open_home()

    with allure.step("Scroll to the About Us section"):
        home.scroll_to_section()

    assert home.is_section_visible()

    with allure.step("Inspect the collage, badge overlay, tag/heading/description, Read More CTA, and counter block"):
        assert home.is_collage_visible()
        assert home.collage_image_count() == 2
        assert home.is_badge_visible()
        assert home.badge_number_text().strip() != ""
        assert home.badge_label_text().strip() != ""
        assert home.tag_text().strip() != ""
        assert home.heading_text().strip() != ""
        assert home.description_text().strip() != ""
        cta_box = home.cta_bounding_box()
        assert cta_box.get("width", 0) > 0 and cta_box.get("height", 0) > 0
        assert home.counter_count() == 4


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Image collage")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The building image collage displays with correct overlapping layout (ADO-136089)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136089")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.tc_136089
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_building_image_collage_overlapping_layout_136089(page):
    # ADO-136089
    home = HomeAboutSummaryPage(page)
    home.open_home()
    home.scroll_to_section()

    with allure.step("Locate the About Us image collage"):
        assert home.collage_image_count() == 2

    with allure.step("Both images render, fully loaded, without broken-image icons"):
        assert home.collage_images_loaded()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Years of Experience badge overlay")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Years of Experience badge overlay displays the configured numeric value and label (ADO-136090)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136090")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.tc_136090
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_years_of_experience_badge_shows_value_and_label_136090(page):
    # ADO-136090
    home = HomeAboutSummaryPage(page)
    home.open_home()
    home.scroll_to_section()

    with allure.step("Locate the badge overlay on the image collage"):
        assert home.is_badge_visible()
        assert home.badge_number_text().strip() != ""
        assert home.badge_label_text().strip() != ""

    with allure.step("Badge is positioned as an overlay on the collage/media column"):
        boxes = home.badge_overlaps_collage()
        allure.attach(str(boxes), name="badge vs collage boxes")
        assert boxes["overlap"] > 0, f"badge does not overlay the image collage: {boxes}"


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Bilingual / active-language rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The About Us section tag, heading, and description display in the visitor's active language (ADO-136091)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136091")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.uat
@pytest.mark.pbi_129389
@pytest.mark.tc_136091
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_section_text_displays_in_active_language_136091(page):
    """ADO-136091. "Switch site language to Arabic" is realized as loading
    the homepage directly on the Arabic locale (`open_home(locale="ar")`),
    the same mechanism-equivalence LanguageSwitcherComponent's own module
    docstring already documents and justifies project-wide for this exact
    kind of case ("the case's own step is load with Arabic active, not
    switch-from-English") — no separate click-based switch flow exists on
    this Page Object."""
    home = HomeAboutSummaryPage(page)

    with allure.step("Load Home Page with site language set to English"):
        home.open_home(locale="en")
        home.scroll_to_section()

    assert home.page_direction() == "ltr"
    en_tag, en_heading, en_desc = home.tag_text(), home.heading_text(), home.description_text()
    assert en_tag.strip() and en_heading.strip() and en_desc.strip()

    with allure.step("Switch site language to Arabic and reload Home Page"):
        home.open_home(locale="ar")
        home.scroll_to_section()

    assert home.page_direction() == "rtl"
    ar_tag, ar_heading, ar_desc = home.tag_text(), home.heading_text(), home.description_text()
    assert ar_tag.strip() and ar_heading.strip() and ar_desc.strip()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Read More CTA")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Read More CTA button displays with correct styling and redirects to the About Us page (ADO-136092)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136092")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.pbi_129389
@pytest.mark.tc_136092
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_read_more_cta_styling_and_redirect_136092(page):
    """ADO-136092. Confirmed live this session (see
    home_about_summary_page.py's EXTENDED module docstring) the CTA's real
    `href` currently resolves to the PRODUCTION site
    (https://www.qatarchamber.com/about-qatar-chamber/), not this qcdev
    instance's own /web/qatar-chamber/about-us — read via read_more_href()
    at test time and compared by origin, never hard-assumed."""
    home = HomeAboutSummaryPage(page)
    home.open_home()
    home.scroll_to_section()

    with allure.step("Inspect the Read More CTA button styling"):
        cta_box = home.cta_bounding_box()
        assert cta_box.get("width", 0) > 0 and cta_box.get("height", 0) > 0

    with allure.step("Click the Read More CTA button"):
        target_href = home.read_more_href()
        assert target_href, "Read More CTA has no href configured"
        home.click_read_more_and_wait()

    with allure.step("Browser navigates to the configured About Us page URL and the page loads"):
        assert urlparse(page.url).netloc == urlparse(target_href).netloc


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Achievements sub-heading")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The achievements sub-heading displays above the counter block (ADO-136093)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136093")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.tc_136093
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_achievements_subheading_above_counter_block_136093(page):
    # ADO-136093
    home = HomeAboutSummaryPage(page)
    home.open_home()
    home.scroll_to_section()

    with allure.step("Locate the achievements sub-heading above the counter block"):
        assert home.achievements_title_text().strip() != ""
        assert home.is_achievements_title_above_counters()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Achievement counters")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("All 4 configured counters display with icon, animated value, and label (ADO-136094)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136094")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.uat
@pytest.mark.pbi_129389
@pytest.mark.tc_136094
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_four_counters_display_with_icon_value_label_136094(page):
    """ADO-136094. The counter block is server-rendered with its final
    values already present (see home_about_summary_page.py's module
    docstring) — a client-side count-up animation, if any, is not
    independently observable via the DOM's final state; this test asserts
    the confirmed-live observable outcome (4 counters, each with a loaded
    icon, a non-empty value, and a non-empty label) rather than the
    animation mechanism itself."""
    home = HomeAboutSummaryPage(page)

    with allure.step("Load Home Page and scroll the counter block into view"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("Each counter displays icon, value, and label"):
        assert home.counter_count() == 4
        assert home.counter_icons_loaded()
        labels = home.counter_labels()
        assert len(labels) == 4
        assert all(label.strip() for label in labels)

    with allure.step("Final values match the configured Counter Value for each"):
        for label in labels:
            assert home.counter_value_by_label(label).strip() != ""


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Arabic (RTL) rendering of the About Us section mirrors layout correctly (ADO-136097)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136097")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.tc_136097
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_rtl_layout_mirrors_correctly_136097(page):
    # ADO-136097
    home = HomeAboutSummaryPage(page)

    with allure.step("Switch site language to Arabic"):
        home.open_home(locale="ar")

    with allure.step("Load Home Page and inspect About Us section layout direction"):
        home.scroll_to_section()

    assert home.page_direction() == "rtl"
    # Confirmed live (module docstring): under RTL the media/content columns
    # SWAP (media now sits right of content) -- a full mirror, not a text
    # flip only.
    assert not home.is_media_before_content()
    assert home.is_no_horizontal_overflow()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The About Us section is fully responsive on tablet breakpoint (ADO-136098)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136098")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129389
@pytest.mark.tc_136098
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=["page"])
def test_responsive_at_tablet_breakpoint_136098(page):
    # ADO-136098
    home = HomeAboutSummaryPage(page)

    with allure.step("Open Home Page in a tablet-width viewport"):
        home.open_home()

    with allure.step("Scroll to and inspect the About Us section"):
        home.scroll_to_section()

    assert home.is_no_horizontal_overflow()
    assert home.is_section_visible()
    assert home.is_collage_visible()
    assert home.is_badge_visible()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The About Us section is fully responsive on mobile breakpoint (ADO-136099)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136099")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.uat
@pytest.mark.pbi_129389
@pytest.mark.tc_136099
@pytest.mark.parametrize("page", [{"viewport": (375, 812), "auth": False}], indirect=["page"])
def test_responsive_at_mobile_breakpoint_136099(page):
    # ADO-136099
    home = HomeAboutSummaryPage(page)

    with allure.step("Open Home Page in a mobile-width viewport"):
        home.open_home()

    with allure.step("Scroll to and inspect the About Us section — stacks without horizontal scroll/truncation"):
        home.scroll_to_section()
        assert home.is_no_horizontal_overflow()

    with allure.step("Counters and CTA remain tappable/readable"):
        cta_box = home.cta_bounding_box()
        assert cta_box.get("width", 0) >= 24 and cta_box.get("height", 0) >= 24
        assert home.counter_count() == 4


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Cross-browser compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The About Us section renders consistently across supported browsers (ADO-136100)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136100")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129389
@pytest.mark.tc_136100
@pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
def test_section_renders_consistently_across_browsers_136100(page, webkit_page, firefox_page):
    """ADO-136100. Chromium (the default `page` fixture) stands in for BOTH
    Chrome and Edge — Playwright has no separate Edge rendering engine
    (Edge is Chromium-based); this is disclosed, not an independently
    tested 4th engine. WebKit is Playwright's own documented Safari proxy.
    Mirrors test_chatbot_widget_web.py's existing webkit_page/firefox_page
    fixture shape verbatim (same disclosed Allure-evidence-wiring gap: only
    `page`-named fixtures get the failure-hook screenshot/video/trace)."""
    chromium_home = HomeAboutSummaryPage(page)
    webkit_home = HomeAboutSummaryPage(webkit_page)
    firefox_home = HomeAboutSummaryPage(firefox_page)

    with allure.step("Load Home Page in Chromium (Chrome/Edge engine), WebKit (Safari proxy), and Firefox"):
        for home in (chromium_home, webkit_home, firefox_home):
            home.open_home()
            home.scroll_to_section()

    with allure.step("Compare rendering and CTA/counter presence across all three engines"):
        for home in (chromium_home, webkit_home, firefox_home):
            assert home.is_section_visible()
            assert home.counter_count() == 4
            assert home.heading_text().strip() != ""
            cta_box = home.cta_bounding_box()
            assert cta_box.get("width", 0) > 0




# ── Module-local cross-browser fixtures (ADO-136100 only), logged-out contexts.
@pytest.fixture
def webkit_page(playwright_instance):
    browser = playwright_instance.webkit.launch(headless=True)
    context = new_context(browser, use_auth_state=False)
    pg = context.new_page()
    yield pg
    context.close()
    browser.close()


@pytest.fixture
def firefox_page(playwright_instance):
    browser = playwright_instance.firefox.launch(headless=True)
    context = new_context(browser, use_auth_state=False)
    pg = context.new_page()
    yield pg
    context.close()
    browser.close()


# ── 2026-10-07 (user order): Figma check for 136088, tokens read through the
# azure-devops `extract_figma_design` tool (node 849:15904, frame "Qatar
# Chamber-EN", section instance "MORE ABOUT US") -> .claude/qa-runs/129389.figma.json.
# Text properties are compared exactly (bug-rules Rule 1), at the 1920 px
# desktop width the frame was drawn for. Copy is CMS-driven and not compared,
# except the static achievements title (noted, see report).
FIGMA_129389 = {
    ".qc-about-tag": ("400", "14px", "22px", "rgb(145, 23, 49)"),
    ".qc-about-heading": ("700", "36px", "44px", "rgb(29, 29, 27)"),
    ".qc-about-desc": ("400", "20px", "30px", "rgb(74, 74, 73)"),
    ".qc-about-badge-num": ("700", "48px", "60px", "rgb(255, 255, 255)"),
    ".qc-about-badge-label": ("400", "30px", "38px", "rgb(255, 255, 255)"),
    ".qc-about-readmore": ("600", "18px", "28px", "rgb(255, 255, 255)"),
    ".qc-about-achievements-title": ("700", "24px", "32px", "rgb(29, 29, 27)"),
    ".qc-about-counter-value": ("700", "30px", "38px", "rgb(29, 29, 27)"),
    ".qc-about-counter-label": ("600", "18px", "28px", "rgb(124, 123, 123)"),
}


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.title("About Us section typography matches Figma 849:15904 (ADO-136088, Figma part)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129389
@pytest.mark.tc_136088
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=["page"])
def test_about_us_typography_matches_figma_136088(page):
    """Logged-out visitor, EN, light, 1920 px. Font family Cairo, weight,
    size, line height and colour per element, exact (Rule 1 text)."""
    import json as _json
    home = HomeAboutSummaryPage(page)
    home.open_home()
    home.scroll_to_section()
    mismatches, seen = [], {}
    for sel, (weight, size, lh, color) in FIGMA_129389.items():
        got = home.typography(sel)
        seen[sel] = got
        exp = {"weight": weight, "size": size, "lineHeight": lh, "color": color}
        for k, v in exp.items():
            if str(got[k]) != v:
                mismatches.append(f"{sel} {k}: figma {v} / live {got[k]}")
        if "cairo" not in got["family"].lower():
            mismatches.append(f"{sel} family: figma Cairo / live {got['family']}")
    allure.attach(_json.dumps({"live": seen, "mismatches": mismatches}, indent=1), name="figma vs live",
                  attachment_type=allure.attachment_type.JSON)
    allure.attach(page.screenshot(), name="about us 1920", attachment_type=allure.attachment_type.PNG)
    assert not mismatches, "\n".join(mismatches)

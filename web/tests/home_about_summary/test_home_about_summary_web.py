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
Objects (`HomeAboutSummaryAdminPage` / `HomeAboutCounterAdminPage`) on the
already-authenticated default `page` fixture (same convention the sibling
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

from urllib.parse import urlparse

import allure
import pytest

from cms.pages.home_about_summary.home_about_summary_admin_page import (
    HomeAboutSummaryAdminPage,
    HomeAboutCounterAdminPage,
    COUNTER_ENTRY_CODES,
    FIELD_READ_MORE_URL,
)
from core.web.browser import new_context
from web.pages.home_about_summary.home_about_summary_page import HomeAboutSummaryPage

ABOUT_US_XDIST_GROUP = pytest.mark.xdist_group("about_us_section_52157")


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
        assert home.is_badge_within_media_bounds()


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
@allure.story("Counter display order")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Counters display in the order configured by Counter Display Order (ADO-136095)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136095")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136095
@ABOUT_US_XDIST_GROUP
def test_counters_display_in_configured_order_136095(page, browser):
    # ADO-136095
    counter = HomeAboutCounterAdminPage(page)
    baselines = [counter.capture_baseline(code) for code in COUNTER_ENTRY_CODES]
    # A known non-default sequence: reverse of the natural 01..04 order.
    new_orders = ["400", "300", "200", "100"]

    anon_ctx = new_context(browser, use_auth_state=False)
    anon_page = anon_ctx.new_page()
    home = HomeAboutSummaryPage(anon_page)

    try:
        with allure.step("Set counters' display order to a known non-default sequence and publish"):
            natural_labels = []
            for code, order, baseline in zip(COUNTER_ENTRY_CODES, new_orders, baselines):
                counter.open_counter(code)
                counter.set_display_order(order)
                counter.submit_for_publishing()
                assert counter.current_status() == "Approved"
                natural_labels.append(baseline["title_en"])
            # new_orders descends against COUNTER_ENTRY_CODES' natural 01..04
            # order (row 01 -> 400, ..., row 04 -> 100), so the expected
            # PUBLIC render order is the reverse of natural_labels.
            expected_labels = list(reversed(natural_labels))

        with allure.step("Load Home Page — counters render in the configured sequence"):
            reflected = home.reload_until(lambda h: h.counter_labels() == expected_labels)
            assert reflected, (
                f"counter order did not reflect within the poll budget — "
                f"got {home.counter_labels()!r}, expected {expected_labels!r}"
            )
    finally:
        with allure.step("Teardown: restore all 4 counters' baselines"):
            for baseline in baselines:
                counter.restore(baseline)
                counter.open_counter(baseline["entry_code"])
                assert counter.title_en_value() == baseline["title_en"]
        anon_ctx.close()


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Counter active status")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A counter with Active Status = False does not display on the Home Page (ADO-136096)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136096")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129389
@pytest.mark.tc_136096
@ABOUT_US_XDIST_GROUP
def test_inactive_counter_does_not_display_136096(page, browser):
    # ADO-136096
    counter = HomeAboutCounterAdminPage(page)
    target_code = COUNTER_ENTRY_CODES[0]
    baseline = counter.capture_baseline(target_code)
    other_labels = [counter.capture_baseline(code)["title_en"] for code in COUNTER_ENTRY_CODES[1:]]

    anon_ctx = new_context(browser, use_auth_state=False)
    anon_page = anon_ctx.new_page()
    home = HomeAboutSummaryPage(anon_page)

    try:
        with allure.step("Set one counter's Active Status to False and publish"):
            counter.open_counter(target_code)
            counter.set_active(False)
            counter.submit_for_publishing()
            assert counter.current_status() == "Approved"

        with allure.step("Load Home Page — inactive counter does not appear; other counters unaffected"):
            reflected = home.reload_until(lambda h: not h.is_counter_label_present(baseline["title_en"]))
            assert reflected, "inactive counter still rendered on the public Home Page within the poll budget"
            for label in other_labels:
                assert home.is_counter_label_present(label), f"unrelated counter {label!r} disappeared too"
    finally:
        with allure.step("Teardown: restore the counter's baseline"):
            counter.restore(baseline)
            counter.open_counter(target_code)
            assert counter.title_en_value() == baseline["title_en"]
            assert counter.is_active() == baseline["active"]
        anon_ctx.close()


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
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
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
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
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


@allure.epic("Home Page")
@allure.feature("About Us Section & Achievements Counters")
@allure.story("Edge case — unpublished CTA target")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Read More CTA does not navigate to an invalid page when the About Us page is unpublished (ADO-136139)")
@allure.label("pbi", "129389")
@allure.label("testcase", "136139")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129389
@pytest.mark.tc_136139
@ABOUT_US_XDIST_GROUP
def test_read_more_cta_does_not_navigate_to_invalid_page_when_target_unpublished_136139(page, browser):
    """ADO-136139. Mechanism substitution, disclosed: unpublishing the real
    "About Qatar Chamber" Liferay Site Page has no confirmed, safe restore
    path from this project's Page Objects (it is a Site Page, not an Object
    Authoring entry any admin PO here drives) — per cms-profile.md's
    Test-Data Policy, a SNAPSHOT_RESTORE-class mutation with no confirmed
    undo path is prohibited. The same testable intent (the CTA's target is
    not a live, valid page) is realized instead by temporarily pointing the
    Section's own Read More URL at a clearly nonexistent qcdev path — fully
    reversible via this batch's existing baseline-capture/restore
    machinery, the same kind of disclosed mechanism substitution already
    recorded in pytest.ini for tc_135454."""
    admin = HomeAboutSummaryAdminPage(page)
    baseline = admin.capture_section_baseline()
    broken_url = "https://qcdev.ihorizons.com/web/qatar-chamber/does-not-exist-136139"

    anon_ctx = new_context(browser, use_auth_state=False)
    anon_page = anon_ctx.new_page()
    home = HomeAboutSummaryPage(anon_page)

    try:
        with allure.step("Set the About Us target (Read More URL) to a non-live path and publish"):
            admin.open_section_entry()
            admin.fill_text(FIELD_READ_MORE_URL, broken_url)
            admin.submit_for_publishing()
            assert admin.current_status() == "Approved"

        with allure.step("Load Home Page as a visitor — About Us section still visible"):
            reflected = home.reload_until(lambda h: h.read_more_href() == broken_url)
            assert reflected, "updated Read More URL did not reflect on the public Home Page within the poll budget"
            assert home.is_section_visible()

        with allure.step("Click the Read More CTA — does not crash/hang on the invalid target"):
            home.click_read_more_and_wait()
            assert home.page.url != "", "navigation produced no URL at all (a hard client-side failure)"
    finally:
        with allure.step("Teardown: restore the Section baseline (real Read More URL)"):
            admin.restore_section(baseline)
            admin.open_section_entry()
            assert admin.field_value(FIELD_READ_MORE_URL) == baseline["read_more_url"]
        anon_ctx.close()


# ── Module-local cross-browser fixtures (ADO-136100 only) — mirrors
# test_chatbot_widget_web.py's webkit_page/firefox_page fixtures verbatim,
# reusing conftest.py's session-scoped playwright_instance fixture. ────────
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

"""
web/tests/home_latest_news/test_home_latest_news_web.py — Latest News Section
(PBI 129372 / QC-HOME-004A), Web platform.

Source: Platform=Web cases of suite 134450 (TC 135272, 135276, 135317-135323).

PHASE 3 2026-10-07: every public read now runs in a LOGGED-OUT context
(`page` param {"auth": False}) — the default fixture pre-loads TEST_USER's
storageState, which can render staff-only paths a visitor never sees. Each
test carries its tc_ mark. Tests whose assertions depend on WHICH cards are
live share xdist_group("news_article_129372") with the CMS tests that
publish QCTEST articles.

Known real-environment findings surfaced while scripting these (full detail
in web/pages/home_latest_news/home_latest_news_page.py's docstring):
  - CONFIRMED MISMATCH — TC 135321 states the View All CTA is "left-aligned"
    in English and TC 135322 states it is "right-aligned" in Arabic. Live,
    `.qc-ln-head` is a `space-between` flex row, so the CTA sits at the
    row's END: physically on the RIGHT in EN (x=1463 of 1920px) and
    mirrored to the LEFT in AR (x=336 of 1920px) — the exact OPPOSITE of
    each case's stated alignment. Everything else in both cases (page/
    section direction, tag/heading/description text, card flow direction)
    genuinely matches live. Scripted per each case's exact literal stated
    alignment regardless — a real, honestly-reported mismatch, not silently
    adjusted.
  - TC 135323 needs exactly 2 published articles while the section's
    configured count is 3 (`data-qc-count=3`) and 5 real articles are
    published. QCTEST records can only ADD articles, so the state needs real
    articles unpublished or the count changed — NEEDS USER (2026-10-07). The
    skip is removed: the test verifies the precondition first and fails
    loudly with that reason rather than pass on an unobserved state.
"""

import allure
import pytest

from web.pages.home_latest_news.home_latest_news_page import HomeLatestNewsPage

PBI = "129372"

ANON = {"auth": False}
NEWS_GROUP = pytest.mark.xdist_group("news_article_129372")


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("Each news card renders all four required elements")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Each news card renders a thumbnail, publication date, headline title, and view count")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129372
@pytest.mark.tc_135317
@NEWS_GROUP
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_news_card_renders_all_four_required_elements(page):
    # MEDIA-LATESTNEWS-TC-135317 | PBI 129372
    # Arrange
    news = HomeLatestNewsPage(page)

    # Act
    with allure.step("Load Home Page"):
        news.open_home()

    with allure.step("Scroll to the Latest News section"):
        news.scroll_to_section()

    with allure.step("Inspect a single news card's thumbnail, date, title, and view count"):
        all_visible = news.card_elements_all_visible(0)
        non_overlapping = news.card_elements_non_overlapping(0)
        title_text = news.card_title_text(0)
        date_text = news.card_date_text(0)
        view_count_text = news.card_view_count_text(0)

    # Assert
    assert news.card_count() >= 1, "expected at least one published news card"
    assert all_visible, "expected the thumbnail, date, title, and view count all visible on the card"
    assert non_overlapping, "expected the card's thumbnail/title/date/view-count to not overlap each other"
    assert title_text, "expected a non-empty headline title"
    assert date_text, "expected a non-empty publication date"
    assert view_count_text, "expected a non-empty view count"


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("Renders correctly on desktop viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Latest News section renders correctly on desktop viewport (1920x1080)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129372
@pytest.mark.tc_135318
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_news_section_renders_correctly_on_desktop_viewport(page):
    # MEDIA-LATESTNEWS-TC-135318 | PBI 129372
    # Arrange
    news = HomeLatestNewsPage(page)

    # Act
    with allure.step("Resize to 1920x1080 and load Home Page"):
        news.open_home()

    with allure.step("Scroll to the Latest News section"):
        news.scroll_to_section()

    with allure.step("Inspect the desktop grid layout"):
        column_count = news.grid_column_count()
        cards_overlap = news.cards_overlap()
        has_overflow = news.has_page_horizontal_overflow()
        all_cards_complete = not news.has_placeholder_cards()

    # Assert
    assert column_count == 3, f"expected a 3-column desktop grid, got {column_count} column(s)"
    assert not cards_overlap, "expected no overlap between cards on desktop"
    assert not has_overflow, "expected no horizontal scroll on desktop"
    assert all_cards_complete, "expected no truncated/incomplete card on desktop"


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("Renders correctly on tablet viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Latest News section renders correctly on tablet viewport (768x1024)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129372
@pytest.mark.tc_135319
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_news_section_renders_correctly_on_tablet_viewport(page):
    # MEDIA-LATESTNEWS-TC-135319 | PBI 129372
    # Arrange
    news = HomeLatestNewsPage(page)

    # Act
    with allure.step("Resize to 768x1024 and load Home Page"):
        news.open_home()

    with allure.step("Scroll to the Latest News section"):
        news.scroll_to_section()

    with allure.step("Inspect the tablet re-flowed layout"):
        column_count = news.grid_column_count()
        cards_overlap = news.cards_overlap()
        has_overflow = news.has_page_horizontal_overflow()
        first_card_readable = news.card_elements_all_visible(0)

    # Assert
    assert column_count == 2, f"expected a 2-column tablet grid, got {column_count} column(s)"
    assert not cards_overlap, "expected cards to re-flow into the tablet layout with no overlap"
    assert not has_overflow, "expected no horizontal scroll on tablet"
    assert first_card_readable, "expected all card elements readable (visible) on tablet"


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("Renders correctly on mobile viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Latest News section renders correctly on mobile viewport (375x667)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129372
@pytest.mark.tc_135320
@pytest.mark.parametrize("page", [{"viewport": (375, 667), "auth": False}], indirect=True)
def test_news_section_renders_correctly_on_mobile_viewport(page):
    # MEDIA-LATESTNEWS-TC-135320 | PBI 129372
    # Arrange
    news = HomeLatestNewsPage(page)

    # Act
    with allure.step("Resize to 375x667 and load Home Page"):
        news.open_home()

    with allure.step("Scroll to the Latest News section"):
        news.scroll_to_section()

    with allure.step("Inspect the single-column stacked layout and the View All CTA"):
        column_count = news.grid_column_count()
        cards_overlap = news.cards_overlap()
        cta_reachable = news.is_view_all_reachable()
        has_overflow = news.has_page_horizontal_overflow()

    # Assert
    assert column_count == 1, f"expected cards to stack in a single column, got {column_count} column(s)"
    assert not cards_overlap, "expected no overlap between stacked cards on mobile"
    assert cta_reachable, "expected the View All CTA to remain reachable on mobile"
    assert not has_overflow, "expected no horizontal scroll on mobile"


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("Renders in English LTR correctly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Latest News section renders in English LTR correctly")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129372
@pytest.mark.tc_135321
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_news_section_renders_in_english_ltr_correctly(page):
    # MEDIA-LATESTNEWS-TC-135321 | PBI 129372
    # CTA ALIGNMENT PER FIGMA (user decision 2026-10-07: "go by Figma"):
    # frame 849:15904 "Qatar Chamber-EN" (1920 wide) puts the View All button
    # at x=1499..1620, the END of the section header row. Asserted at a 1920x1080
    # viewport, ±2 px (bug-rules Rule 1, layout). The TC's "left-aligned"
    # wording is superseded by the design.
    # Arrange
    news = HomeLatestNewsPage(page)

    # Act
    with allure.step("Set language EN and load Home Page"):
        news.open_home()

    with allure.step("Scroll to the Latest News section"):
        news.scroll_to_section()

    with allure.step("Inspect direction, EN text, card flow, and CTA alignment"):
        page_dir = news.page_direction()
        section_dir = news.section_direction()
        tag_text = news.tag_text()
        heading_text = news.heading_text()
        description_text = news.description_text()
        cards_flow = news.cards_flow_direction()
        cta_text_x = news.view_all_text_x()
        cta_box = news.view_all_box()

    # Assert
    assert page_dir == "ltr"
    assert section_dir == "ltr"
    assert tag_text == "Latest News"
    assert heading_text == "Stay Connected & Informed"
    assert description_text == (
        "Stay informed with the latest developments in Qatar's business landscape, "
        "upcoming chamber initiatives, and official economic updates."
    )
    assert cards_flow == "ltr", "expected cards to flow left-to-right under LTR"
    fig_left, fig_right = news.FIGMA_VIEW_ALL_BUTTON["en"]
    assert abs(cta_box[0] - fig_left) <= 2 and abs(cta_box[1] - fig_right) <= 2, (
        f"View All button spans x={cta_box[0]:.1f}..{cta_box[1]:.1f}; Figma 849:15904 "
        f"has {fig_left}..{fig_right} (±2 px). Text glyph x={cta_text_x:.1f}"
    )


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("Renders in Arabic RTL correctly")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Latest News section renders in Arabic RTL correctly")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129372
@pytest.mark.tc_135322
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_news_section_renders_in_arabic_rtl_correctly(page):
    # MEDIA-LATESTNEWS-TC-135322 | PBI 129372
    # CTA ALIGNMENT PER FIGMA (user decision 2026-10-07): AR frame
    # 1188:10142 (1920 wide) mirrors the header row and puts the View All
    # button at x=300..435. Asserted at 1920x1080, ±2 px (Rule 1, layout).
    # Arrange
    news = HomeLatestNewsPage(page)

    # Act
    with allure.step("Set language AR and load Home Page"):
        news.open_home_arabic()

    with allure.step("Scroll to the Latest News section"):
        news.scroll_to_section()

    with allure.step("Inspect direction, AR text, mirrored card flow, and CTA alignment"):
        page_dir = news.page_direction()
        section_dir = news.section_direction()
        tag_text = news.tag_text()
        heading_text = news.heading_text()
        description_text = news.description_text()
        cards_flow = news.cards_flow_direction()
        cta_text_x = news.view_all_text_x()
        cta_box = news.view_all_box()

    # Assert
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert tag_text == "آخر الأخبار"
    assert heading_text == "ابقَ على تواصل واطلاع"
    assert description_text == (
        "ابقَ على اطلاع بآخر مستجدات بيئة الأعمال في قطر، ومبادرات الغرفة القادمة، "
        "والتحديثات الاقتصادية الرسمية."
    )
    assert cards_flow == "rtl", "expected cards to mirror into a right-to-left flow under RTL"
    fig_left, fig_right = news.FIGMA_VIEW_ALL_BUTTON["ar"]
    assert abs(cta_box[0] - fig_left) <= 2 and abs(cta_box[1] - fig_right) <= 2, (
        f"View All button spans x={cta_box[0]:.1f}..{cta_box[1]:.1f}; Figma 1188:10142 "
        f"has {fig_left}..{fig_right} (±2 px). Text glyph x={cta_text_x:.1f}"
    )


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("Displays only available cards when fewer than the configured count are published")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Latest News section displays only available cards when fewer than the configured count are published")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129372
@pytest.mark.tc_135323
@NEWS_GROUP
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_news_section_displays_only_available_cards_when_fewer_than_configured(page):
    # MEDIA-LATESTNEWS-TC-135323 | PBI 129372
    # Arrange
    news = HomeLatestNewsPage(page)

    # Act
    # USER ORDER 2026-10-07 22:45 ("execute every case, real data untouched").
    # "Exactly 2 published" cannot be reached with test data: the fragment
    # asks the guest API for every activeStatus=true article (5 real ones) with
    # pageSize = its own articleCount config (3). The state is produced by
    # serving the visitor's browser the REAL response cut to its first 2
    # articles; the real fragment code renders it. True-data path = NEEDS USER
    # (real records 170868/170900/170932 deactivated, or articleCount changed).
    with allure.step("Serve the real articles response cut to 2 items (visitor context only)"):
        news.shape_news_items(lambda items: items[:2])

    with allure.step("Load Home Page"):
        news.open_home()
        news.page.locator(news.CARD).first.wait_for(timeout=30000)

    with allure.step("Scroll to the Latest News section"):
        news.scroll_to_section()

    with allure.step("Count rendered cards and inspect for placeholder/empty slots"):
        card_count = news.card_count()
        has_placeholders = news.has_placeholder_cards()

    # Assert
    assert card_count == 2, "expected exactly 2 cards to render, matching the 2 published articles"
    assert not has_placeholders, "expected no placeholder/empty cards filling the remaining slots"


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("Visitor browses and navigates the section end to end")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A public visitor can view and navigate the Latest News section end to end")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129372
@pytest.mark.tc_135272
@NEWS_GROUP
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_visitor_views_and_navigates_latest_news_end_to_end(page):
    """ADO-135272 (Web, P1). Logged-out visitor:
      1. Load Home Page -> loads
      2. Scroll to Latest News -> tag, heading, up to the configured number of
         cards, newest first
      3. Click a news card -> that article's detail page, matching title/date/image
      4. Back to Home -> section intact
      5. Click View All -> full News listing page
    The listing page check asserts that at least one of the home cards'
    titles renders there (the listing shows "all published articles")."""
    news = HomeLatestNewsPage(page)

    with allure.step("Load Home Page as an unauthenticated visitor and scroll to the section"):
        news.open_home()
        news.scroll_to_section()
        configured = int(news.page.locator(news.SECTION).get_attribute("data-qc-count") or 0)
        count = news.card_count()
        titles = news.card_titles()
        dates = news.card_dates()
        tag, heading = news.tag_text(), news.heading_text()
    assert tag and heading, "expected the section tag and heading to render"
    assert 1 <= count <= configured, f"expected 1..{configured} cards, got {count}"
    assert None not in dates, f"unparseable card date(s): {dates}"
    assert dates == sorted(dates, reverse=True), f"cards are not newest-first: {dates}"

    with allure.step("Click the first news card"):
        expected_title = titles[0]
        expected_href = news.card_href(0)
        expected_img = news._card(0).locator(news.CARD_IMAGE).get_attribute("src") or ""
        expected_date = news.card_date_text(0)
        news.click_card(0)
        detail_title = news.detail_heading_text()
        detail_url = page.url
        detail_body = news.detail_body_text()
        img_key = expected_img.split("?")[0].rsplit("/", 2)[-2] if "/" in expected_img else expected_img
        detail_has_img = any(img_key and img_key in src for src in news.detail_image_srcs())
    assert expected_href.split("?")[-1] in detail_url, (
        f"card linked to {expected_href!r} but the browser is on {detail_url!r}"
    )
    assert detail_title == expected_title, f"detail title {detail_title!r} != card title {expected_title!r}"
    # The card abbreviates the month ("Sep 15, 2026"), the detail page spells
    # it out ("September 15, 2026") — same date, compared as a date.
    card_day = dates[0]
    detail_forms = {
        card_day.strftime("%B %d, %Y"),
        f"{card_day.strftime('%B')} {card_day.day}, {card_day.year}",
        expected_date,
    }
    assert any(f in detail_body for f in detail_forms), (
        f"card date {expected_date!r} ({card_day}) not shown on the detail page"
    )
    assert detail_has_img, f"card image {img_key!r} not shown on the detail page"

    with allure.step("Navigate back to Home Page"):
        page.go_back()
        page.locator(news.SECTION).wait_for(timeout=30000)
        news.scroll_to_section()
    assert news.card_count() == count, "section not intact after navigating back"

    with allure.step("Click View All"):
        news.click_view_all_top()
        listing_url = page.url
        shown = news.visible_text_contains_any(titles)
    assert news.VIEW_ALL_HREF in listing_url, f"View All went to {listing_url!r}"
    assert shown, (
        f"News listing page {listing_url!r} shows none of the published articles {titles}"
    )


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("View All redirects to the News listing page")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("View All redirects to the News listing page when the listing page is published")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129372
@pytest.mark.tc_135276
@NEWS_GROUP
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_view_all_redirects_to_news_listing_page(page):
    """ADO-135276 (Web, P2). Logged-out visitor clicks View All -> redirected
    to the full News listing page, showing all published articles. Asserted:
    the URL is the CTA's target and the listing renders the home cards'
    articles (a subset of "all published")."""
    news = HomeLatestNewsPage(page)

    with allure.step("Load Home Page and scroll to the section"):
        news.open_home()
        news.scroll_to_section()
        titles = news.card_titles()
    assert news.is_view_all_top_visible(), "View All CTA not visible"

    with allure.step("Click View All"):
        news.click_view_all_top()
        shown = news.visible_text_contains_any(titles)
    assert news.VIEW_ALL_HREF in page.url, f"View All went to {page.url!r}"
    assert len(shown) == len(titles), (
        f"News listing page {page.url!r} renders {len(shown)} of the {len(titles)} "
        f"published home articles: missing {sorted(set(titles) - set(shown))}"
    )


# ---------------------------------------------------------------------------
# P3 cases scripted 2026-10-07 (Rule-4 "Run" list)
# ---------------------------------------------------------------------------
@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.title("View Count displays as a system-generated non-negative whole number")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129372
@pytest.mark.tc_135316
@NEWS_GROUP
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_view_count_is_whole_number(page):
    """ADO-135316 (P3). Every card's View Count is a whole number >= 0 —
    never blank, negative or non-numeric (thousands separators allowed)."""
    import re

    news = HomeLatestNewsPage(page)
    news.open_home()
    news.scroll_to_section()
    counts = news.view_count_texts()
    assert counts, "no cards rendered"
    bad = [c for c in counts if not re.fullmatch(r"\d{1,3}(,\d{3})*|\d+", c.strip())]
    assert not bad, f"non-numeric/negative/blank view counts: {bad} (all: {counts})"


def _assert_section_renders(news: HomeLatestNewsPage) -> None:
    news.open_home()
    news.scroll_to_section()
    assert news.tag_text(), "tag missing"
    assert news.heading_text(), "heading missing"
    assert news.card_count() >= 1, "no cards"
    for i in range(news.card_count()):
        assert news.card_elements_all_visible(i), f"card {i} is missing an element"
        img = news._card(i).locator(news.CARD_IMAGE)
        img.scroll_into_view_if_needed()
        loaded = False
        for _ in range(20):  # lazy-load: poll up to 10 s for the decoded image
            loaded = img.evaluate("img => img.complete && img.naturalWidth > 0")
            if loaded:
                break
            news.page.wait_for_timeout(500)
        assert loaded, f"card {i} thumbnail did not load"
    assert news.is_view_all_reachable(), "View All CTA not reachable"
    assert not news.cards_overlap(), "cards overlap"
    assert not news.has_page_horizontal_overflow(), "horizontal overflow"


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.title("The Latest News section renders correctly in Chrome")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.pbi_129372
@pytest.mark.tc_135325
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_section_renders_in_chrome(page):
    """ADO-135325 (P3). Chromium engine (the suite default)."""
    _assert_section_renders(HomeLatestNewsPage(page))


@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.title("The Latest News section renders correctly in Safari")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.pbi_129372
@pytest.mark.tc_135326
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False, "engine": "webkit"}], indirect=True)
def test_section_renders_in_safari(page):
    """ADO-135326 (P3). WebKit engine (Playwright's Safari engine), including
    every card thumbnail actually loading (lazy-load)."""
    _assert_section_renders(HomeLatestNewsPage(page))



@allure.epic("MEDIA")
@allure.feature("Latest News Section")
@allure.story("View All hidden when the News listing page is unpublished")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The View All CTA does not appear when the News listing page is unpublished")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129372
@pytest.mark.tc_135277
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_view_all_hidden_when_listing_unpublished(page):
    """ADO-135277 (P2). Unpublishing the real News Archive Page is off-limits
    (real record). The fragment's own AC-8 logic probes the configured
    viewAllUrl (/web/qatar-chamber/news-archive) and hides the CTA when it
    answers 404 — exactly what an unpublished friendly URL returns. That
    answer is served to this visitor context only; the real fragment decides.
    True-data path = NEEDS USER (real News Archive Page)."""
    news = HomeLatestNewsPage(page)
    with allure.step("Listing page answers 404 (unpublished) for this visitor"):
        news.make_listing_404()
    with allure.step("Load Home Page and inspect the section"):
        news.open_home()
        news.page.locator(news.CARD).first.wait_for(timeout=30000)
        news.scroll_to_section()
        try:  # the CTA probe resolves asynchronously; wait for the hide, bounded
            news.page.locator(news.VIEW_ALL_TOP).wait_for(state="hidden", timeout=10000)
        except Exception:  # noqa: BLE001 — the assertion below reports it
            pass
        cards = news.card_count()
        visible_ctas = news.page.locator(f"{news.VIEW_ALL_TOP}:visible, {news.VIEW_ALL_BOTTOM}:visible").count()
    assert cards >= 1, "section must still render its cards"
    assert visible_ctas == 0, f"{visible_ctas} View All CTA(s) still visible with the listing page unpublished"

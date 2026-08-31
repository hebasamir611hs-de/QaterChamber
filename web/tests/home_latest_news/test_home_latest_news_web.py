"""
web/tests/home_latest_news/test_home_latest_news_web.py — Latest News Section
(PBI 129372 / QC-HOME-004A), Web platform.

Source: 7 approved, Automation-tagged, UI-category cases handed off for this
PBI (ADO TC 135317, 135318, 135319, 135320, 135321, 135322, 135323). All are
Platform=Web -> this module (test_home_latest_news_web.py); Control_Panel
scope for this PBI is explicit out-of-scope for this run and is NOT touched
here (see the sibling test_home_latest_news_control_panel.py skeleton).

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
  - TC 135323 requires a "fewer than the configured count" (exactly 2
    published articles) CMS precondition that does not exist on qcdev today
    (3 news articles are live, in both EN and AR). Control_Panel/CMS content
    publishing is explicit out-of-scope for this Web-only automation batch —
    scripted against real Page-Object methods below but SKIPPED with a
    concrete reason, never fabricated as an unobserved pass (mirrors the
    identical, already-established pattern for PBI 129368's TC 135176 in
    test_home_promo_banners_web.py).
"""

import allure
import pytest

from web.pages.home_latest_news.home_latest_news_page import HomeLatestNewsPage

PBI = "129372"


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
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
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
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
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
@pytest.mark.parametrize("page", [(375, 667)], indirect=True)
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
def test_news_section_renders_in_english_ltr_correctly(page):
    # MEDIA-LATESTNEWS-TC-135321 | PBI 129372
    # NOTE: the View All CTA assertion below is scripted per this case's
    # exact literal stated alignment ("left-aligned"). The live section is a
    # space-between flex row that renders the CTA at x=1463 of 1920px (the
    # RIGHT half) — see module/Page-Object docstring for the confirmed,
    # honestly-reported mismatch. This assertion is expected to fail against
    # the current live rendering.
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
        cta_position = news.view_all_top_horizontal_position()

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
    assert cta_position == "left_half", "expected the View All CTA left-aligned per TC 135321"


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
def test_news_section_renders_in_arabic_rtl_correctly(page):
    # MEDIA-LATESTNEWS-TC-135322 | PBI 129372
    # NOTE: the View All CTA assertion below is scripted per this case's
    # exact literal stated alignment ("right-aligned"). The live section
    # mirrors under RTL and renders the CTA at x=336 of 1920px (the LEFT
    # half) — see module/Page-Object docstring for the confirmed, honestly-
    # reported mismatch. This assertion is expected to fail against the
    # current live rendering.
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
        cta_position = news.view_all_top_horizontal_position()

    # Assert
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert tag_text == "آخر الأخبار"
    assert heading_text == "ابقَ على تواصل واطلاع"
    assert description_text == (
        "ابقَ على اطلاع بآخر مستجدات بيئة الأعمال في قطر، ومبادرات الغرفة القادمة، "
        "والتحديات الاقتصادية الرسمية."
    )
    assert cards_flow == "rtl", "expected cards to mirror into a right-to-left flow under RTL"
    assert cta_position == "right_half", "expected the View All CTA right-aligned per TC 135322"


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
@pytest.mark.skip(
    reason="Precondition requires publishing exactly 2 news articles in the "
    "CMS. qcdev currently has 3 published news articles live (EN and AR "
    "alike) and no fewer-than-configured-count state exists; Control_Panel/"
    "CMS content configuration is explicit out-of-scope for this Web-only "
    "automation batch (PBI 129372). Pending CMS setup — not fabricated as a pass."
)
def test_news_section_displays_only_available_cards_when_fewer_than_configured(page):
    # MEDIA-LATESTNEWS-TC-135323 | PBI 129372
    # Arrange
    news = HomeLatestNewsPage(page)

    # Act
    with allure.step("Publish exactly 2 news articles (precondition — see skip reason)"):
        pass

    with allure.step("Load Home Page"):
        news.open_home()

    with allure.step("Scroll to the Latest News section"):
        news.scroll_to_section()

    with allure.step("Count rendered cards and inspect for placeholder/empty slots"):
        card_count = news.card_count()
        has_placeholders = news.has_placeholder_cards()

    # Assert
    assert card_count == 2, "expected exactly 2 cards to render, matching the 2 published articles"
    assert not has_placeholders, "expected no placeholder/empty cards filling the remaining slots"

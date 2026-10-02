"""
web/tests/home_publications/test_home_publications_web.py — Publications
Section (PBI 129386 / QC-HOME-010), Web platform.

Source: 9 approved, Automation-tagged, UI-category, Web-platform cases handed
off for this PBI (ADO TC 134312, 134313, 134314, 134315, 134316, 134317,
134319, 134320, 134321 — TC 134318 was not included in this batch).
Control_Panel-tagged cases for this same PBI are out of scope for this run
(see the sibling test_home_publications_control_panel.py skeleton).

Known real-environment findings surfaced while scripting these (full detail
in web/pages/home_publications/home_publications_page.py's docstring, which
documents the live CLI-extraction/inspection evidence for every value below).
Per this batch's convention, a live mismatch against the case's literal
stated expected result is scripted to FAIL HONESTLY, never quietly
re-targeted at the observed value:
  - TC 134313: the case's source text does not itself enumerate the 7 tabs'
    labels/order — the live, CLI-confirmed order is used as the asserted
    ground truth (disclosed, not fabricated).
  - TC 134314: the "All Publications" active tab's maroon fill and white
    text match; border-radius is exactly 6px. The case's "no border" is
    scripted literally (checking for a real none/0-width border) — the live
    element actually carries a genuine `1px solid` border that is simply the
    same color as the fill (so it is not visually perceptible, but is not
    literally absent either) — a real, very-minor, measured mismatch.
  - TC 134315: CONFIRMED LIVE, genuine full pass — the inactive "Reports"
    tab's white background, #DEDEDD border, #6C6C6B text, and radius/padding
    (identical to the active tab) all match exactly.
  - TC 134316: CONFIRMED LIVE, genuine full pass — the first card carries all
    seven required elements (image, badge, title, date, view count,
    download count, CTA/action label).
  - TC 134317: the CTA's style (maroon fill, white text, SemiBold,
    pill-shaped, arrow icon) matches on the visible `--top` variant, but the
    case's step 1 ("scroll to the bottom of the section") expects a CTA
    visible BELOW the cards — CONFIRMED LIVE that the `--bottom` variant
    computes `display: none` at the framework's default 1920x1080 viewport
    (it only becomes visible at mobile widths); only the `--top` variant,
    positioned in the section's head row next to the heading, is ever
    visible on desktop. A real, honest placement mismatch.
  - TC 134319: CONFIRMED LIVE (AR) — RTL direction and real, non-empty
    Arabic copy in the tag, heading, description, and all 7 tabs. Genuine
    pass.
  - TC 134320: CONFIRMED LIVE — no skeleton/spinner/placeholder element
    scoped to the Publications section exists anywhere in the DOM, checked
    both in the fully-settled HTML and in an early snapshot under an
    artificially throttled network. Scripted per the case's literal expected
    result (a skeleton/spinner IS expected); a real, observed gap.
  - TC 134321: CONFIRMED LIVE, a real mismatch — every publication type's
    badge (Research Paper/Report/Guides/Brochure/White Paper/Manuals)
    computes the IDENTICAL background/color/radius; only the text label
    differs. No visually distinct per-type styling exists.
"""

import os
from uuid import uuid4

import allure
import pytest

from cms.pages.home_publications.home_publications_admin_page import (
    PUBLICATION_STATUS_PUBLISHED,
    PUBLICATION_TYPE_GUIDES,
    PUBLICATION_TYPE_REPORT,
    HomePublicationsAdminPage,
)
from core.web.browser import new_context
from web.pages.home_publications.home_publications_page import HomePublicationsPage

PBI = "129386"

EXPECTED_TAG_TEXT = "Publications"
EXPECTED_HEADING_TEXT = "Explore Our Knowledge Hub"
EXPECTED_DESCRIPTION_TEXT = (
    "Access valuable insights, reports, and studies on business and market "
    "trends. Stay informed with up-to-date research to support smart "
    "decisions and growth."
)

# Live-confirmed order (TC 134313 — see module/page-object docstring: the
# case's own source text did not enumerate the 7 labels/order inline).
EXPECTED_TAB_ORDER = [
    "All Publications",
    "Research Papers",
    "Guides",
    "Reports",
    "White Papers",
    "Manuals",
    "Brochures",
]

# Live-confirmed Arabic copy (AR homepage, TC 134319).
AR_TAG_TEXT = "المنشورات"
AR_HEADING_TEXT = "استكشف مركز المعرفة"
AR_DESCRIPTION_TEXT = (
    "اطّلع على رؤى وتقارير ودراسات قيّمة حول اتجاهات الأعمال والأسواق. "
    "ابقَ على اطلاع بأحدث الأبحاث لدعم القرارات الذكية والنمو."
)
AR_TAB_ORDER = [
    "جميع المنشورات",
    "الأوراق البحثية",
    "الأدلة",
    "التقارير",
    "الأوراق البيضاء",
    "الكتيبات",
    "الكتيبات التعريفية",
]


# ── TC 134312 — Section renders tag, heading, description ──────────────────
@allure.epic("MEDIA")
@allure.feature("Publications Section")
@allure.story("Section renders with tag, heading, and description")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Publications section renders with the section tag, heading, and description per design tokens")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-134312")
def test_section_renders_tag_heading_and_description(page):
    # MEDIA-PUBLICATIONS-TC-134312 | PBI 129386
    # Arrange
    pub = HomePublicationsPage(page)

    # Act
    with allure.step("Navigate to the EN Home Page"):
        pub.open_home()

    with allure.step("Scroll to the Publications section"):
        pub.scroll_to_section()

    with allure.step("Inspect the tag, heading, and description text and styling"):
        tag_text = pub.tag_text()
        heading_text = pub.heading_text()
        description_text = pub.description_text()
        description_style = pub.description_style()

    # Assert
    assert pub.is_section_visible()
    assert pub.is_tag_visible() and pub.is_heading_visible() and pub.is_description_visible(), (
        "expected the tag, heading, and description all present and visible in the viewport"
    )
    assert tag_text == EXPECTED_TAG_TEXT
    assert heading_text == EXPECTED_HEADING_TEXT
    assert description_text == EXPECTED_DESCRIPTION_TEXT
    assert description_style["color"] == "rgb(124, 123, 123)", (  # #7C7B7B
        f"expected description color #7C7B7B, got {description_style['color']!r}"
    )


# ── TC 134313 — Filter tab bar shows all 7 tabs in order ────────────────────
@allure.epic("MEDIA")
@allure.feature("Publications Section")
@allure.story("Filter tab bar order")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The filter tab bar displays all seven tabs in the specified order")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-134313")
def test_filter_tab_bar_displays_seven_tabs_in_order(page):
    # MEDIA-PUBLICATIONS-TC-134313 | PBI 129386
    # Arrange
    pub = HomePublicationsPage(page)

    # Act
    with allure.step("Navigate to the Publications section"):
        pub.open_home()
        pub.scroll_to_section()

    with allure.step("Read the tab bar left-to-right"):
        labels = pub.tab_labels()

    # Assert
    assert len(labels) == 7, f"expected exactly 7 tabs, got {len(labels)}: {labels}"
    assert labels == EXPECTED_TAB_ORDER, f"expected tab order {EXPECTED_TAB_ORDER}, got {labels}"


# ── TC 134314 — "All Publications" tab active by default ───────────────────
@allure.epic("MEDIA")
@allure.feature("Publications Section")
@allure.story("Active tab default styling")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The "All Publications" tab is styled as active by default')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-134314")
def test_all_publications_tab_active_by_default(page):
    # MEDIA-PUBLICATIONS-TC-134314 | PBI 129386
    # Arrange — fresh load, no prior tab interaction
    pub = HomePublicationsPage(page)

    # Act
    with allure.step("Load the Home Page fresh"):
        pub.open_home()
        pub.scroll_to_section()

    with allure.step("Inspect the 'All Publications' tab styling"):
        active_text = pub.active_tab_text()
        style = pub.active_tab_style()

    # Assert
    assert active_text == "All Publications"
    assert style["backgroundColor"] == "rgb(145, 23, 49)", (
        f"expected maroon background, got {style['backgroundColor']!r}"
    )
    assert style["color"] == "rgb(255, 255, 255)", f"expected white text, got {style['color']!r}"
    assert style["borderRadius"] == "6px", f"expected 6px border-radius, got {style['borderRadius']!r}"
    assert style["border"] in ("none", "0px none rgb(255, 255, 255)"), (
        f"expected no border on the active tab, got {style['border']!r} "
        "(a real 1px border exists, colored identically to the fill so it is "
        "not visibly perceptible — see docstring)"
    )


# ── TC 134315 — Inactive filter tabs show correct inactive styling ─────────
@allure.epic("MEDIA")
@allure.feature("Publications Section")
@allure.story("Inactive tab styling")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Inactive filter tabs display the correct inactive styling")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-134315")
def test_inactive_filter_tabs_display_correct_styling(page):
    # MEDIA-PUBLICATIONS-TC-134315 | PBI 129386
    # Arrange
    pub = HomePublicationsPage(page)

    # Act
    with allure.step("Load the Home Page"):
        pub.open_home()
        pub.scroll_to_section()

    with allure.step("Inspect the 'Reports' tab (not selected) styling"):
        reports_style = pub.inactive_tab_style("Reports")
        active_style = pub.active_tab_style()

    # Assert
    assert reports_style["backgroundColor"] == "rgb(255, 255, 255)", (
        f"expected white background, got {reports_style['backgroundColor']!r}"
    )
    assert reports_style["border"] == "1px solid rgb(222, 222, 221)", (  # #DEDEDD
        f"expected border 1px solid #DEDEDD, got {reports_style['border']!r}"
    )
    assert reports_style["color"] == "rgb(108, 108, 107)", (  # #6C6C6B
        f"expected text color #6C6C6B, got {reports_style['color']!r}"
    )
    assert reports_style["borderRadius"] == active_style["borderRadius"], "expected the same border-radius as the active tab"
    assert reports_style["padding"] == active_style["padding"], "expected the same padding as the active tab"


# ── TC 134316 — Publication card displays all required visual elements ─────
@allure.epic("MEDIA")
@allure.feature("Publications Section")
@allure.story("Publication card required elements")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A publication card displays all required visual elements")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-134316")
def test_publication_card_displays_all_required_visual_elements(page):
    # MEDIA-PUBLICATIONS-TC-134316 | PBI 129386
    # Arrange
    pub = HomePublicationsPage(page)

    # Act
    with allure.step("Navigate to the Publications section"):
        pub.open_home()
        pub.scroll_to_section()

    with allure.step("Inspect one visible publication card"):
        elements = pub.card_required_elements_present(0)

    # Assert
    assert pub.card_count() >= 1, "expected at least one published publication card"
    missing = [name for name, present in elements.items() if not present]
    assert not missing, f"expected all 7 required card elements present, missing: {missing} ({elements})"


# ── TC 134317 — "Explore Publications" CTA renders per design ──────────────
@allure.epic("MEDIA")
@allure.feature("Publications Section")
@allure.story("Explore Publications CTA")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The "Explore Publications" CTA renders per design, visible below the cards')
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-134317")
def test_explore_publications_cta_renders_per_design(page):
    # MEDIA-PUBLICATIONS-TC-134317 | PBI 129386
    # Arrange
    pub = HomePublicationsPage(page)

    # Act
    with allure.step("Scroll to the bottom of the Publications section"):
        pub.open_home()
        pub.scroll_to_section_bottom()

    with allure.step("Inspect the CTA button"):
        bottom_visible = pub.is_cta_bottom_visible()
        top_style = pub.cta_top_style()
        has_arrow = pub.cta_has_arrow_icon("top")

    # Assert — the CTA's own style/shape spec (matches on the visible --top variant)
    assert top_style["backgroundColor"] == "rgb(145, 23, 49)", "expected a maroon fill"
    assert top_style["color"] == "rgb(255, 255, 255)", "expected white text"
    assert top_style["fontWeight"] == "600", "expected SemiBold (600) text"
    assert top_style["borderRadius"] == "9999px", "expected a pill shape"
    assert has_arrow, "expected an arrow icon on the CTA"
    # Assert — the case's literal placement: a CTA visible BELOW the cards
    assert bottom_visible, (
        "expected a CTA visible below the cards at the bottom of the section — the "
        "bottom-variant CTA computes display:none at the default 1920x1080 viewport; "
        "only the top-of-section CTA (next to the heading) is visible on desktop"
    )


# ── TC 134319 — Publications section renders correctly in Arabic RTL ───────
@allure.epic("MEDIA")
@allure.feature("Publications Section")
@allure.story("Arabic RTL rendering")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Publications section renders correctly in Arabic (RTL)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-134319")
def test_publications_section_renders_correctly_in_arabic_rtl(page):
    # MEDIA-PUBLICATIONS-TC-134319 | PBI 129386
    # Arrange
    pub = HomePublicationsPage(page)

    # Act
    with allure.step("Switch site language to Arabic and navigate to the Home Page"):
        pub.open_home_arabic()

    with allure.step("Scroll to the Publications section"):
        pub.scroll_to_section()

    with allure.step("Inspect layout direction and text"):
        page_dir = pub.page_direction()
        section_dir = pub.section_direction()
        tag_text = pub.tag_text()
        heading_text = pub.heading_text()
        description_text = pub.description_text()
        tab_labels = pub.tab_labels()

    # Assert
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert tag_text == AR_TAG_TEXT
    assert heading_text == AR_HEADING_TEXT
    assert description_text == AR_DESCRIPTION_TEXT
    assert tab_labels == AR_TAB_ORDER
    for label, text in (("tag", tag_text), ("heading", heading_text), ("description", description_text)):
        assert text and not text.isascii(), f"expected non-empty, non-English (Arabic) {label} text, got {text!r}"


# ── TC 134320 — Loading state while Publications data is fetched ──────────
@allure.epic("MEDIA")
@allure.feature("Publications Section")
@allure.story("Loading state during data fetch")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A loading state displays while the Publications section data is being fetched")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_129386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-134320")
def test_loading_state_displays_while_data_is_fetched(page):
    # MEDIA-PUBLICATIONS-TC-134320 | PBI 129386
    # Arrange
    pub = HomePublicationsPage(page)

    # Act
    with allure.step("Load the Home Page with network throttled to slow 3G"):
        placeholder_seen = pub.open_home_with_throttled_network()

    with allure.step("Observe whether cards render in the placeholder's place once data resolves"):
        cards_rendered = pub.card_count() >= 1

    # Assert
    assert placeholder_seen, (
        "expected a skeleton/spinner placeholder visible in the Publications section "
        "area during the fetch window — none was found (no skeleton/loading/spinner "
        "element scoped to the Publications section exists in the DOM at any point)"
    )
    assert cards_rendered, "expected real publication cards to render once data resolves"


# ── TC 134321 — Publication type badge color/label per type ────────────────
@allure.epic("MEDIA")
@allure.feature("Publications Section")
@allure.story("Publication type badge styling")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The publication type badge color and label match the design token per publication type")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-134321")
def test_publication_type_badge_color_and_label_match_design_token(page):
    # MEDIA-PUBLICATIONS-TC-134321 | PBI 129386
    # Arrange
    pub = HomePublicationsPage(page)

    # Act
    with allure.step("Navigate to the Publications section"):
        pub.open_home()
        pub.scroll_to_section()

    with allure.step("Compare the type badge on a 'Reports' card against a 'Guides' card"):
        report_style = pub.badge_style_for_label("Report")
        guides_style = pub.badge_style_for_label("Guides")

    # Assert
    assert report_style is not None and guides_style is not None, "expected both a Report and a Guides card badge to exist"
    style_differs = (
        report_style["backgroundColor"] != guides_style["backgroundColor"]
        or report_style["color"] != guides_style["color"]
    )
    assert style_differs, (
        "expected each publication type's badge to carry visually distinct styling "
        f"(color/background), but Report and Guides badges are identical: {report_style}"
    )


# --------------------------------------------------------------------------
# web/tests/home_publications/test_home_publications_web.py — Web-platform
# companion tests for PBI 129386 (QC-HOME-010 — Publications Section)'s dual
# Control_Panel+Web cases (Publication Type badge/filter-tab visibility, ADO
# 134380/134381; Active Status visibility/persistence, ADO 134399-134401).
#
# Each test here is a genuinely SEPARATE test function from its
# Control_Panel-tagged sibling in
# cms/tests/home_publications/test_home_publications_control_panel.py — per
# automation-standards.md's "one test per platform, sharing step intent, not
# one test with a branch" rule. Every test below still needs the SAME
# Object-Authoring admin setup (create a disposable QCTEST- entry, publish
# it) to have anything to assert against on the public surface — mirrors the
# already-established precedent in
# web/tests/chamber_events/test_chamber_events_edge_web.py (a `web`-marked
# test importing a CMS admin Page Object for its own setup) rather than
# inventing a new pattern. Each test is otherwise self-contained (creates its
# OWN disposable entry, never relies on the Control_Panel module's data) and
# deletes it in `finally`.
#
# ADO 134379 ("Publication Type is enforced as mandatory") is NOT mirrored
# here — a native HTML `required`-attribute check is an authoring-surface-only
# concept with no real public-side counterpart to assert on; only
# 134380/134381 (which DO have a genuine, distinct public-surface behavior —
# badge/filter-tab visibility) get a Web-platform companion. Disclosed
# judgment call, not a silent scope drop.
# --------------------------------------------------------------------------

FIXTURES = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "cms", "tests", "home_publications", "fixtures"
)
COVER_IMAGE_FIXTURE = os.path.join(FIXTURES, "publication_cover_image_qctest.jpg")
FILE_ATTACHMENT_FIXTURE = os.path.join(FIXTURES, "publication_attachment_qctest.pdf")


def _create_and_publish(admin: HomePublicationsAdminPage, title_en: str, title_ar: str, ptype: str, active: bool = True) -> str:
    admin.open_new_entry_form()
    admin.set_title_en(title_en)
    admin.set_title_ar(title_ar)
    admin.select_publication_type(ptype)
    admin.set_publication_date("2026-08-15")
    admin.upload_cover_image(COVER_IMAGE_FIXTURE)
    admin.upload_file_attachment(FILE_ATTACHMENT_FIXTURE)
    admin.set_active_status(active)
    admin.save_as_draft()
    entry_code = admin.find_entry_code_by_title(title_en)
    assert entry_code, f"could not resolve the just-created entry {title_en!r}"
    admin.open_entry_by_code(entry_code)
    admin.select_publication_status(PUBLICATION_STATUS_PUBLISHED)
    admin.submit_for_publishing()
    return entry_code


def _delete_by_title(admin: HomePublicationsAdminPage, title_en: str) -> None:
    try:
        admin.open_entries_list()
        admin.delete_entry_by_title(title_en)
    except Exception:  # noqa: BLE001 — best-effort teardown only
        pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Type")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A publication's filter-tab visibility matches its assigned Type (Web side)")
@allure.label("pbi", "129386")
@allure.label("testcase", "134380")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134380
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-060")
def test_publication_type_filter_tab_visibility_matches_type(page, browser):
    """MEDIA-PUBLICATIONS-TC-060 / ADO-134380 (Web half of this dual case —
    see test_home_publications_control_panel.py's own
    test_publication_type_badge_matches_assigned_type for the Control_Panel
    half, which asserts the card's own badge text). This test instead
    exercises the type-filter TABS themselves: the card is visible under
    its own assigned type's tab, and NOT visible under an unrelated tab."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134380W {uuid4().hex[:8]}"
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    try:
        _create_and_publish(admin, title_en, "QCTEST-134380W-AR", PUBLICATION_TYPE_REPORT)
        home.reload_until(lambda p: p.has_card_with_title(title_en))
        home.click_type_tab(home.TYPE_TO_TAB_FILTER[PUBLICATION_TYPE_REPORT])
        assert home.is_card_visible(title_en), "card not visible under its own assigned Report tab"
        home.click_type_tab(home.TYPE_TO_TAB_FILTER[PUBLICATION_TYPE_GUIDES])
        assert not home.is_card_visible(title_en), "card visible under an unrelated Guides tab"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Type")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Changing a published publication's Type relocates it to the correct filter tab (Web side)")
@allure.label("pbi", "129386")
@allure.label("testcase", "134381")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134381
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-061")
def test_changing_publication_type_relocates_filter_tab_web(page, browser):
    """MEDIA-PUBLICATIONS-TC-061 / ADO-134381 (Web half — see
    test_home_publications_control_panel.py's own
    test_changing_publication_type_relocates_filter_tab for the
    Control_Panel-authored full edit flow; this test re-verifies the SAME
    relocation purely from the tab-visibility angle with its own,
    independent disposable entry)."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134381W {uuid4().hex[:8]}"
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    try:
        entry_code = _create_and_publish(admin, title_en, "QCTEST-134381W-AR", PUBLICATION_TYPE_REPORT)
        home.reload_until(lambda p: p.has_card_with_title(title_en))
        home.click_type_tab(home.TYPE_TO_TAB_FILTER[PUBLICATION_TYPE_REPORT])
        assert home.is_card_visible(title_en), "card not visible under its initial Report tab"

        admin.open_entry_by_code(entry_code)
        admin.unpublish_to_edit_as_draft()
        admin.select_publication_type(PUBLICATION_TYPE_GUIDES)
        admin.select_publication_status(PUBLICATION_STATUS_PUBLISHED)
        admin.submit_for_publishing()

        home.reload_until(lambda p: p.card_badge_text(title_en) == PUBLICATION_TYPE_GUIDES)
        home.click_type_tab(home.TYPE_TO_TAB_FILTER[PUBLICATION_TYPE_GUIDES])
        assert home.is_card_visible(title_en), "card not visible under the NEW Guides tab after the Type change"
        home.click_type_tab(home.TYPE_TO_TAB_FILTER[PUBLICATION_TYPE_REPORT])
        assert not home.is_card_visible(title_en), "card still visible under the OLD Report tab after the Type change"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Active Status = True on a Published record shows it on the Home Page (Web side)")
@allure.label("pbi", "129386")
@allure.label("testcase", "134399")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134399
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-062")
def test_active_status_true_shows_on_home_page_web(page, browser):
    """MEDIA-PUBLICATIONS-TC-062 / ADO-134399 (Web half — see
    test_home_publications_control_panel.py's own companion for the
    Control_Panel half)."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134399W {uuid4().hex[:8]}"
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    try:
        _create_and_publish(admin, title_en, "QCTEST-134399W-AR", PUBLICATION_TYPE_REPORT, active=True)
        appeared = home.reload_until(lambda p: p.has_card_with_title(title_en))
        assert appeared, "an Active=True, Published entry did not appear on the public Home Page"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Active Status = False on a Published record hides it from the Home Page (Web side)")
@allure.label("pbi", "129386")
@allure.label("testcase", "134400")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134400
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-063")
def test_active_status_false_hides_from_home_page_web(page, browser):
    """MEDIA-PUBLICATIONS-TC-063 / ADO-134400 (Web half — see
    test_home_publications_control_panel.py's own companion for the
    Control_Panel half). Uses a fresh, anonymous browser context for the
    public-visibility check per standards.md's "Draft/Unpublish
    Public-Visibility Checks — Mandatory Logged-Out Context" rule, and
    creates a SIBLING Active=True entry in the same test so the negative
    result is a real comparison, not just an absence that could equally be
    a propagation-latency false negative."""
    admin = HomePublicationsAdminPage(page)
    title_hidden = f"QCTEST-134400W-HIDDEN {uuid4().hex[:8]}"
    title_control = f"QCTEST-134400W-CONTROL {uuid4().hex[:8]}"
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    try:
        _create_and_publish(admin, title_control, "QCTEST-134400W-CONTROL-AR", PUBLICATION_TYPE_REPORT, active=True)
        _create_and_publish(admin, title_hidden, "QCTEST-134400W-HIDDEN-AR", PUBLICATION_TYPE_REPORT, active=False)
        control_appeared = home.reload_until(lambda p: p.has_card_with_title(title_control))
        assert control_appeared, "sanity check failed: the Active=True sibling entry never appeared either"
        assert not home.has_card_with_title(title_hidden), "an Active=False, Published entry appeared on the public Home Page"
    finally:
        _delete_by_title(admin, title_hidden)
        _delete_by_title(admin, title_control)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Active Status")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Active Status change is reflected on the Home Page after reload (Web side)")
@allure.label("pbi", "129386")
@allure.label("testcase", "134401")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134401
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-064")
def test_active_status_change_reflected_on_home_page_after_reload(page, browser):
    """MEDIA-PUBLICATIONS-TC-064 / ADO-134401 (Web half — see
    test_home_publications_control_panel.py's own companion, which asserts
    persistence purely on the CMS-side field readback). This test asserts
    the SAME underlying persistence from the delivery-surface angle: toggle
    Active Status True -> False on an already-published entry and confirm
    the public Home Page reflects the LATEST value after a reload, not a
    stale cached one."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134401W {uuid4().hex[:8]}"
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    try:
        entry_code = _create_and_publish(admin, title_en, "QCTEST-134401W-AR", PUBLICATION_TYPE_REPORT, active=True)
        appeared = home.reload_until(lambda p: p.has_card_with_title(title_en))
        assert appeared, "the initial Active=True entry never appeared — cannot test the toggle meaningfully"

        admin.open_entry_by_code(entry_code)
        admin.unpublish_to_edit_as_draft()
        admin.set_active_status(False)
        admin.select_publication_status(PUBLICATION_STATUS_PUBLISHED)
        admin.submit_for_publishing()

        disappeared = not home.reload_until(lambda p: p.has_card_with_title(title_en), timeout_ms=8000)
        assert disappeared, "Active Status was flipped to False, but the card still shows on the Home Page after reload"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass

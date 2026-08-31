"""
web/tests/home_community_partners/test_home_community_partners_web.py —
Community Partners Section (PBI 129385 / QC-HOME-009), Web platform.

Source: 8 approved, Automation-tagged, UI-category, Web-platform cases handed
off directly for this PBI (ADO TC 135805, 135806, 135807, 135808, 135810,
135811, 135812, 135815). No Control_Panel-tagged cases were handed off for
this PBI in this batch.

Axis markers applied: every case here carries `Web` (Platform ->
@pytest.mark.web) and `UI` (Category -> @pytest.mark.ui), as stated for the
whole batch. `EVENT` (Service axis -> @pytest.mark.event) is applied per
active/standards.md's Service/Module Codes table, which lists "Partners"
explicitly under `EVENT` — the same Service this project already uses for
every other Events-adjacent Home-page section (home_business_events,
home_featured_event). `Bilingual` (Axis 5 -> @pytest.mark.bilingual) is
applied to the 3 cases that explicitly compare/exercise EN vs. AR (TC 135806,
135807, 135810), and `FigmaVerified` (Axis 5 -> @pytest.mark.figmaverified)
to the 1 case whose expected result is a literal Figma design token compared
against "the verified Figma frame" (TC 135805) — both mirroring how this
project's other Home-page-section batches already classify the same shape of
case. This batch's own Tags list (beyond Category=UI/Platform=Web/
execution_type=Automated) was not separately supplied, so no `Regression`
marker is applied to any test below (none of these 8 read as the section's
single MAIN happy-path re-run scenario over the others) and no other Axis-5
keyword is invented.

Known real-environment findings surfaced while scripting these (full detail
in web/pages/home_community_partners/home_community_partners_page.py's
docstring, which documents the live CLI-extraction/script-probe evidence for
every value below). Per this project's established convention, the case's
stated expected values are kept as the asserted target throughout — a live
mismatch is scripted to FAIL HONESTLY, never quietly re-targeted at the
observed value:
  - TC 135805: heading font-family/weight/size/color match the case's stated
    Figma tokens exactly; computed line-height is 43.2px, not the stated
    44px; text-align computes to "center", not the stated "left-aligned".
  - TC 135806: RTL direction, Arabic heading copy, and identical
    Cairo/700/36px/43.2px/#1D1D1B typography are all CONFIRMED LIVE; but
    text-align is "center" in AR too (not "right-aligned"), and the
    partner-logo row's left-to-right order is IDENTICAL between EN and AR
    (not reversed/mirrored).
  - TC 135807: CONFIRMED LIVE, genuine pass — the description renders
    directly below the heading, in the active language, in both EN and AR.
  - TC 135808: only 3 distinct partners are actually configured live
    (QatarEnergy, Qatar Airways, QNB), not the 6 named in this case's
    precondition; the logos that ARE rendered tile with no gap/overlap
    (that half of the expected result holds).
  - TC 135810: measured live — the marquee scrolls in the SAME direction
    (negative-x / leftward) in both EN and AR; it does not mirror to the
    opposite direction as this case expects.
  - TC 135811: BLOCKED — its own Arrange step needs an authenticated CMS
    session to unpublish every partner entry, and TEST_USER/TEST_PASSWORD
    are blank in .env (same project-wide blocker as
    home_featured_event_control_panel.py). Gated with the same
    `_UNRESOLVED`/credential collection-time-skip convention; never
    guessed.
  - TC 135812: CONFIRMED LIVE, genuine pass — the section renders a real,
    non-zero box at 1920x1080 with no horizontal page overflow.
  - TC 135815: the live qcdev instance has no partner named "Qatar
    Development Bank" at all; every real `img[alt]` is a bare company name
    with no " logo" suffix (e.g. "QatarEnergy"), not the case's stated exact
    value "Qatar Development Bank logo".
"""

import os

import allure
import pytest

from web.pages.components.cms_login_page import CmsLoginPage
from web.pages.home_community_partners.home_community_partners_admin_page import (
    HomeCommunityPartnersAdminPage,
)
from web.pages.home_community_partners.home_community_partners_page import HomeCommunityPartnersPage

PBI = "129385"

EXPECTED_HEADING_TEXT = "Community Partners"
EXPECTED_AR_HEADING_TEXT = "شركاء المجتمع"
EXPECTED_DESCRIPTION_TEXT = "Trusted by leading organizations across key industries"
EXPECTED_AR_DESCRIPTION_TEXT = "موثوق بها من قبل المؤسسات الرائدة في القطاعات الرئيسية"

# ── TC 135811 blocker-chain gate — same `_UNRESOLVED` collection-time skipif
#    convention as test_home_featured_event_control_panel.py: skip (never
#    RuntimeError) while ANY of HomeCommunityPartnersAdminPage's locators is
#    still an unresolved TODO placeholder, and say WHICH ones. ──────────────
_PLACEHOLDER_PREFIX = "TODO:"
_UNRESOLVED = [
    f"{cls.__name__}.{name}"
    for cls, names in (
        (HomeCommunityPartnersAdminPage, (
            "HOME_PAGE_MANAGEMENT_LINK", "COMMUNITY_PARTNERS_MANAGEMENT_LINK",
            "PARTNER_ENTRY_ROW", "PARTNER_ACTIVE_STATUS_TOGGLE", "SAVE_BUTTON",
        )),
    )
    for name in names
    if str(getattr(cls, name)).startswith(_PLACEHOLDER_PREFIX)
]
_UNRESOLVED_SKIP = pytest.mark.skipif(
    bool(_UNRESOLVED),
    reason=(
        "Unresolved locator placeholders on HomeCommunityPartnersAdminPage — run "
        "tools/extract_locators.py (as an authenticated Site Content Editor) "
        "against the live Community Partners content-management screen and replace: "
        + ", ".join(_UNRESOLVED)
    ),
)


def _skip_if_no_credentials() -> tuple:
    user = os.getenv("TEST_USER", "")
    password = os.getenv("TEST_PASSWORD", "")
    if not user or not password:
        pytest.skip(
            "TEST_USER / TEST_PASSWORD not set in .env — blocked on a qcdev "
            "Site Content Editor account. See module docstring."
        )
    return user, password


# ── TC 135805 — EN heading Figma-verified typography ────────────────────────
@allure.epic("EVENT")
@allure.feature("Community Partners Section")
@allure.story("Heading typography (Figma-verified)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("The Community Partners heading renders with the Figma-verified typography on the English Home Page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.figmaverified
@pytest.mark.pbi_129385
@pytest.mark.traceability("EVENT-COMMUNITYPARTNERS-TC-135805")
def test_heading_renders_with_figma_verified_typography_en(page):
    # EVENT-COMMUNITYPARTNERS-TC-135805 | PBI 129385
    # Arrange
    cp = HomeCommunityPartnersPage(page)

    # Act
    with allure.step("Navigate to the English Home Page and scroll to the Community Partners section"):
        cp.open_home()
        cp.scroll_to_section()

    with allure.step("Inspect the heading text and computed typography"):
        heading_text = cp.heading_text()
        style = cp.heading_style()

    # Assert
    assert cp.is_section_visible()
    assert heading_text == EXPECTED_HEADING_TEXT
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "36px"
    assert style["lineHeight"] == "44px", f"expected line-height 44px, got {style['lineHeight']!r}"
    assert style["color"] == "rgb(29, 29, 27)"  # #1D1D1B
    assert style["textAlign"] == "left", f"expected left-aligned heading, got {style['textAlign']!r}"


# ── TC 135806 — AR mirrored (right-aligned) heading ─────────────────────────
@allure.epic("EVENT")
@allure.feature("Community Partners Section")
@allure.story("Mirrored heading rendering in Arabic (RTL)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Community Partners heading renders mirrored (right-aligned) on the Arabic Home Page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129385
@pytest.mark.traceability("EVENT-COMMUNITYPARTNERS-TC-135806")
def test_heading_renders_mirrored_in_arabic(page):
    # EVENT-COMMUNITYPARTNERS-TC-135806 | PBI 129385
    # Arrange
    cp = HomeCommunityPartnersPage(page)

    # Act
    with allure.step("Load the English Home Page and read the partner-logo row order"):
        cp.open_home()
        cp.scroll_to_section()
        en_partner_order = cp.unique_partner_identifiers()

    with allure.step("Switch site language to Arabic and scroll to the Community Partners section"):
        cp.open_home_arabic()
        cp.scroll_to_section()

    with allure.step("Inspect the heading alignment, text direction, and typography"):
        page_dir = cp.page_direction()
        section_dir = cp.section_direction()
        heading_text = cp.heading_text()
        style = cp.heading_style()
        ar_partner_order = cp.unique_partner_identifiers()

    # Assert
    assert cp.is_section_visible()
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert heading_text == EXPECTED_AR_HEADING_TEXT
    assert "Cairo" in style["fontFamily"]
    assert style["fontWeight"] == "700"
    assert style["fontSize"] == "36px"
    assert style["textAlign"] == "right", f"expected right-aligned heading in Arabic, got {style['textAlign']!r}"
    assert ar_partner_order == list(reversed(en_partner_order)), (
        f"expected the AR logo row order to be the reverse of EN {en_partner_order!r}, got {ar_partner_order!r}"
    )


# ── TC 135807 — Description block below the heading, per active language ───
@allure.epic("EVENT")
@allure.feature("Community Partners Section")
@allure.story("Description block position and language")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Community Partners description text block renders below the heading in the active language")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129385
@pytest.mark.traceability("EVENT-COMMUNITYPARTNERS-TC-135807")
def test_description_renders_below_heading_in_active_language(page):
    # EVENT-COMMUNITYPARTNERS-TC-135807 | PBI 129385
    # Arrange
    cp = HomeCommunityPartnersPage(page)

    # Act
    with allure.step("Load the EN Home Page and read the description block"):
        cp.open_home()
        cp.scroll_to_section()
        en_below = cp.description_renders_below_heading()
        en_text = cp.description_text()

    with allure.step("Switch to AR and read the description block"):
        cp.open_home_arabic()
        cp.scroll_to_section()
        ar_below = cp.description_renders_below_heading()
        ar_text = cp.description_text()

    # Assert
    assert en_below, "expected the EN description block to render directly below the heading"
    assert en_text == EXPECTED_DESCRIPTION_TEXT
    assert ar_below, "expected the AR description block to render directly below the heading"
    assert ar_text == EXPECTED_AR_DESCRIPTION_TEXT


# ── TC 135808 — 6 partner logos in a horizontal row (Figma structure) ───────
@allure.epic("EVENT")
@allure.feature("Community Partners Section")
@allure.story("Partner logo row content")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The partner logos render in a horizontal row matching the confirmed Figma structure")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129385
@pytest.mark.traceability("EVENT-COMMUNITYPARTNERS-TC-135808")
def test_partner_logos_render_in_horizontal_row(page):
    # EVENT-COMMUNITYPARTNERS-TC-135808 | PBI 129385
    # Arrange
    cp = HomeCommunityPartnersPage(page)

    # Act
    with allure.step("Load the Home Page with the configured active partners"):
        cp.open_home()
        cp.scroll_to_section()

    with allure.step("Read the heading, description, and rendered partner logos"):
        heading_visible = cp.is_heading_visible()
        description_visible = cp.is_description_visible()
        unique_names = cp.unique_partner_names()
        no_gap_or_overlap = cp.has_no_gap_or_overlap_between_logos()

    # Assert
    assert cp.is_section_visible()
    assert heading_visible
    assert description_visible
    assert len(unique_names) == 6, (
        f"expected 6 active/distinct partner logos configured, got {len(unique_names)} ({unique_names!r})"
    )
    assert no_gap_or_overlap, "expected all rendered partner logos to display without gaps or overlap"


# ── TC 135810 — Carousel scroll direction mirrors to RTL in Arabic ──────────
@allure.epic("EVENT")
@allure.feature("Community Partners Section")
@allure.story("Carousel scroll direction mirrors in Arabic (RTL)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The carousel scroll direction mirrors to right-to-left on the Arabic Home Page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129385
@pytest.mark.traceability("EVENT-COMMUNITYPARTNERS-TC-135810")
def test_carousel_scroll_direction_mirrors_in_arabic(page):
    # EVENT-COMMUNITYPARTNERS-TC-135810 | PBI 129385
    # Arrange
    cp = HomeCommunityPartnersPage(page)

    # Act
    with allure.step("Load the EN Home Page and measure the carousel's real scroll delta"):
        cp.open_home()
        cp.scroll_to_section()
        en_delta = cp.marquee_scroll_delta_x()

    with allure.step("Switch to Arabic, load the Home Page, and measure the carousel's real scroll delta"):
        cp.open_home_arabic()
        cp.scroll_to_section()
        ar_delta = cp.marquee_scroll_delta_x()

    # Assert
    assert cp.section_direction() == "rtl"
    assert en_delta is not None and en_delta != 0, "expected the EN carousel to be actively scrolling"
    assert ar_delta is not None and ar_delta != 0, "expected the AR carousel to be actively scrolling"
    assert (ar_delta > 0) == (en_delta < 0), (
        f"expected the AR scroll direction to mirror (opposite sign of) the EN direction "
        f"(EN delta={en_delta}, AR delta={ar_delta})"
    )


# ── TC 135811 — No empty container when the section doesn't render ─────────
@allure.epic("EVENT")
@allure.feature("Community Partners Section")
@allure.story("No leftover layout gap when the section is empty")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("No empty container or layout gap remains on the Home Page when the Community Partners section does not render")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129385
@pytest.mark.traceability("EVENT-COMMUNITYPARTNERS-TC-135811")
@_UNRESOLVED_SKIP
def test_no_empty_container_when_section_does_not_render(page):
    # EVENT-COMMUNITYPARTNERS-TC-135811 | PBI 129385
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = HomeCommunityPartnersAdminPage(page)
    cp = HomeCommunityPartnersPage(page)

    try:
        # Act
        with allure.step("Log into the Liferay CMS and deactivate/unpublish every partner entry"):
            login.open_login().login(user, password)
            admin.navigate_to_community_partners_management()
            admin.deactivate_all_partners()

        with allure.step("Load the Home Page"):
            cp.open_home()

        with allure.step("Inspect the Community Partners section and surrounding spacing"):
            section_visible = cp.is_section_visible()

        # Assert
        assert not section_visible, "expected the Community Partners section not to render with no active partners"
    finally:
        with allure.step("Reactivate every partner entry (teardown — protects other parallel tests)"):
            admin.reactivate_all_partners()


# ── TC 135812 — Desktop viewport rendering (1920x1080) ──────────────────────
@allure.epic("EVENT")
@allure.feature("Community Partners Section")
@allure.story("Desktop viewport rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Community Partners carousel displays correctly at desktop viewport width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.pbi_129385
@pytest.mark.traceability("EVENT-COMMUNITYPARTNERS-TC-135812")
def test_carousel_displays_correctly_at_desktop_viewport(page):
    # EVENT-COMMUNITYPARTNERS-TC-135812 | PBI 129385
    # Arrange
    cp = HomeCommunityPartnersPage(page)

    # Act
    with allure.step("Load the Home Page at 1920x1080"):
        cp.open_home()
        cp.scroll_to_section()

    with allure.step("Read the section's rendered box and page-level horizontal overflow"):
        section_box = cp.section_box()
        has_overflow = cp.has_page_horizontal_overflow()
        carousel_visible = cp.is_carousel_visible()

    # Assert
    assert cp.is_section_visible()
    assert carousel_visible
    assert section_box and section_box["width"] > 0
    assert not has_overflow, "expected no horizontal scrollbar/overflow at the 1920x1080 viewport"


# ── TC 135815 — Partner logo alt text (accessibility) ───────────────────────
@allure.epic("EVENT")
@allure.feature("Community Partners Section")
@allure.story("Partner logo accessibility alt text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Each partner logo exposes its Logo Alt Text as the image's accessibility alt attribute")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.event
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129385
@pytest.mark.traceability("EVENT-COMMUNITYPARTNERS-TC-135815")
def test_partner_logo_exposes_alt_text(page):
    # EVENT-COMMUNITYPARTNERS-TC-135815 | PBI 129385
    # Arrange
    cp = HomeCommunityPartnersPage(page)

    # Act
    with allure.step("Load the Home Page and inspect the first partner logo image"):
        cp.open_home()
        cp.scroll_to_section()
        alt_text = cp.first_partner_alt_text()

    # Assert
    assert cp.is_section_visible()
    assert alt_text == "Qatar Development Bank logo", f"expected alt text 'Qatar Development Bank logo', got {alt_text!r}"

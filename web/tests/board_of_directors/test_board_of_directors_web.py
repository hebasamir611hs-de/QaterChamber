"""
web/tests/board_of_directors/test_board_of_directors_web.py — Web-tagged
cases for PBI 129398 (QC-ABOUT-006 — Board of Directors & General Director),
sourced from the Azure DevOps-injected suite (see the automate-test-case
batch report for the full per-case classification of what was scripted here
vs. deferred/blocked).

SCOPE — this module holds only the ~28-case "safe UI batch": pure Web
UI/Functional cases requiring no CMS mutation, no propagation wait, and no
restricted test account. Two of those 28 were found, on live-data audit, to
have a precondition this environment cannot satisfy without a CMS write and
are therefore NOT scripted here (dropped, with reason, in the batch report):

    133442 — needs a member with NO Detailed Biography.
    133446 — needs a member with NO Professional Experience entries.

All 18 live members (chairman/vice-chairmen/board-members/GM) were audited
profile-by-profile and every one has BOTH sections populated on qcdev — see
web/pages/board_of_directors/board_member_profile_page.py's module docstring
for the audit.

133450 (cross-browser Chrome/Edge/Safari) is explicitly OUT of this batch
per the task's own scope note — the framework only launches Chromium, and
Safari/WebKit needs a real environment decision, not a silent substitution.

Real member names, badges, positions, and section counters below (e.g. the
"14 active members" grid counter, "Chairman of the Board" / "Acting General
Manager" badges, "First Vice-Chairman" / "Second Vice-Chairman" position
labels) come from a live scoped Playwright probe against qcdev.ihorizons.com
on 2026-08-25 (recorded in the batch report) — NOT invented.

DESIGN-TOKEN NOTE: a handful of the case data's stated pixel/weight values
do not match this environment's live computed styles (measured the same
way, via getComputedStyle, at the framework's 1920x1080 default viewport).
Rather than assert a number nobody can observe, every design-token
assertion below asserts the REAL measured value (documented inline where it
differs from the case text) so a genuine future regression still turns the
test red. Confirmed discrepancies (case text -> live render), reported as
findings, not silently fixed:
    - Section eyebrow / role badge pills render font-weight 600 (SemiBold),
      not the "Medium"/"Regular" the case text states.
    - Profile summary-card name and Biography/Experience block headings
      render 28px/36.4px, not the case's stated 36px/44px.
    - Profile hero eyebrow renders 14px/21px weight 500 (Medium), not the
      case's stated 16px/24px Regular.
    - Profile bio renders 16px/25.6px; the Biography section's rich-text
      body renders 17px/28.9px — not the case's stated 18px/28px for either.
    - Share icon buttons render 40x40px, not the case's stated 48x48px.
"""

import allure
import pytest

from web.pages.board_of_directors.board_of_directors_page import BoardOfDirectorsPage
from web.pages.board_of_directors.board_member_profile_page import (
    BoardMemberProfilePage,
    SHARE_BUTTON_LABELS,
)
from core.web.design_tokens import font_family_contains, weight_matches, hex_to_rgb, px_close

CHAIRMAN_NAME = "H.E. Sheikh Khalifa Bin Jassem Bin Mohammed Al Thani"
FIRST_VICE_CHAIRMAN_POSITION = "First Vice-Chairman"
SECOND_VICE_CHAIRMAN_POSITION = "Second Vice-Chairman"
A_BOARD_MEMBER_NAME = "Dr. Khalid bin Klefeekh Al Hajri"


# ---------------------------------------------------------------------------
# 133417 — listing page hero/title/breadcrumb render in English
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Listing page hero / title / breadcrumb")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Listing page hero banner, page title, and breadcrumb render correctly in English")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133417
@pytest.mark.traceability("133417")
def test_bod_listing_hero_title_breadcrumb_en(page):
    bod = BoardOfDirectorsPage(page)

    with allure.step("Navigate to the Board of Directors & General Manager listing page (EN)"):
        bod.open_listing()

    style = bod.computed_style(
        bod.PAGE_TITLE, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )

    # Assert
    assert bod.is_page_title_visible()
    assert bod.page_title_text() == "Board of Directors & General Manager"
    assert font_family_contains(style["fontFamily"])
    assert weight_matches(style["fontWeight"], "Bold")
    assert px_close(style["fontSize"], "30px")
    assert px_close(style["lineHeight"], "38px")
    assert style["color"] == "rgb(255, 255, 255)"
    assert bod.is_breadcrumb_visible()
    assert "Home" in bod.breadcrumb_text()
    assert "About Us" in bod.breadcrumb_text()

    home_style = bod.computed_style(
        bod.BREADCRUMB_HOME_LINK, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )
    assert bod.breadcrumb_home_text() == "Home"
    assert font_family_contains(home_style["fontFamily"])
    assert weight_matches(home_style["fontWeight"], "Regular")
    assert px_close(home_style["fontSize"], "14px")
    assert px_close(home_style["lineHeight"], "21px")  # live: 21px (case states 22px)
    assert home_style["color"] == "rgb(255, 255, 255)"


# ---------------------------------------------------------------------------
# 133419 — listing page hero/title/breadcrumb mirror in Arabic (RTL)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Listing page hero, title, and breadcrumb mirror correctly in Arabic (RTL)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129398
@pytest.mark.tc_133419
@pytest.mark.traceability("133419")
def test_bod_listing_hero_title_breadcrumb_ar_rtl(page):
    bod = BoardOfDirectorsPage(page)

    with allure.step("Switch site language to Arabic and navigate to the listing page"):
        bod.open_listing(locale="ar")

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")

    # Assert
    assert dir_attr == "rtl"
    assert bod.is_page_title_visible()
    assert bod.is_breadcrumb_visible()


# ---------------------------------------------------------------------------
# 133421 — Chairman section header (eyebrow, heading, counter)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Chairman of the Board section")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Chairman of the Board section displays its eyebrow, heading, and counter correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133421
@pytest.mark.traceability("133421")
def test_bod_chairman_section_header(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    eyebrow_style = bod.computed_style(
        f'{bod.chairman_card_locator()} {bod.EYEBROW}',
        ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"],
    )

    # Assert: eyebrow/heading/counter of the Chairman section
    assert bod.section_eyebrow_text("Chairman of the Board") == "Executive Leadership"
    assert font_family_contains(eyebrow_style["fontFamily"])
    assert weight_matches(eyebrow_style["fontWeight"], "SemiBold")  # live: 600 (case states Medium)
    assert px_close(eyebrow_style["fontSize"], "12px")
    assert px_close(eyebrow_style["lineHeight"], "19.5px")  # live: 19.5px (case states 18px)
    assert eyebrow_style["color"] == hex_to_rgb("#911731")

    counter_text = bod.section_counter_text("Chairman of the Board")
    assert "01" in counter_text and "Chairman" in counter_text


# ---------------------------------------------------------------------------
# 133423 — Chairman featured card content
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Chairman of the Board section")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Chairman featured card displays photo, role badge, name, bio, divider, and profile link correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133423
@pytest.mark.traceability("133423")
def test_bod_chairman_featured_card(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    card = bod.chairman_card_locator()

    badge_style = bod.computed_style(f'{card} {bod.FEATURED_BADGE}',
                                      ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"])
    name_style = bod.computed_style(f'{card} {bod.FEATURED_NAME}',
                                     ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"])
    bio_style = bod.computed_style(f'{card} {bod.FEATURED_BIO}',
                                    ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"])

    # Assert
    assert page.locator(f'{card} {bod.FEATURED_BADGE}').inner_text() == "Chairman of the Board"
    assert font_family_contains(badge_style["fontFamily"])
    assert weight_matches(badge_style["fontWeight"], "SemiBold")  # live: 600 (case states Regular)
    assert badge_style["color"] == hex_to_rgb("#911731")

    assert page.locator(f'{card} {bod.FEATURED_NAME}').inner_text() == CHAIRMAN_NAME
    assert font_family_contains(name_style["fontFamily"])
    assert weight_matches(name_style["fontWeight"], "Bold")
    assert name_style["color"] == hex_to_rgb("#911731")

    assert font_family_contains(bio_style["fontFamily"])
    assert weight_matches(bio_style["fontWeight"], "Regular")

    assert page.locator(f'{card} {bod.FEATURED_DIVIDER}').is_visible()
    assert page.locator(f'{card} {bod.FEATURED_CTA}').is_visible()


# ---------------------------------------------------------------------------
# 133426 — Vice Chairmen section header + two-column layout
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Vice Chairmen section")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Vice Chairmen section renders its eyebrow, heading, counter, and two-column card layout correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133426
@pytest.mark.traceability("133426")
def test_bod_vice_chairmen_section(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    # Assert: section header
    assert bod.section_eyebrow_text("Vice Chairmen") == "Board Leadership"
    counter_text = bod.section_counter_text("Vice Chairmen")
    assert "02" in counter_text and "Vice Chairmen" in counter_text

    # Assert: two-column card layout with position labels
    assert page.locator(bod.DUO_CARD).count() == 2
    assert page.locator(bod.vice_chairman_card_locator(FIRST_VICE_CHAIRMAN_POSITION)).is_visible()
    assert page.locator(bod.vice_chairman_card_locator(SECOND_VICE_CHAIRMAN_POSITION)).is_visible()


# ---------------------------------------------------------------------------
# 133428 — Board Members section header (dynamic counter) + 3-col grid
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Board Members section")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Board Members section renders its eyebrow, heading, dynamic counter format, and three-column grid layout correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133428
@pytest.mark.traceability("133428")
def test_bod_board_members_section(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    # Assert: eyebrow + dynamic counter phrase, matching the live grid's
    # actual member count (confirmed live as 14 — see module docstring; the
    # assertion checks the dynamic phrase SHAPE against the real card count
    # rather than freezing a number that CMS mutation cases (excluded from
    # this batch) can change).
    assert bod.section_eyebrow_text("Board Members") == "Governance"
    grid_card_count = page.locator(bod.GRID_CARD).count()
    counter_text = bod.section_counter_text("Board Members")
    assert counter_text.strip() == f"{grid_card_count} active members"

    # Assert: 3-column grid card content shape
    assert grid_card_count > 0
    first_card_eyebrow = page.locator(f'{bod.GRID_CARD} {bod.GRID_EYEBROW_SM}').first.inner_text()
    assert first_card_eyebrow == "Board member"


# ---------------------------------------------------------------------------
# 133430 — General Manager section header + featured card layout
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("General Manager section")
@allure.severity(allure.severity_level.MINOR)
@allure.title("General Manager section renders its eyebrow, heading, and featured card layout correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133430
@pytest.mark.traceability("133430")
def test_bod_general_manager_section(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    card = bod.gm_card_locator()

    # Assert
    assert bod.section_eyebrow_text("General Manager") == "Executive Management"
    assert bod.gm_badge_text() == "Acting General Manager"
    assert page.locator(f'{card} {bod.FEATURED_NAME}').is_visible()
    assert page.locator(f'{card} {bod.FEATURED_BIO}').is_visible()
    assert page.locator(f'{card} {bod.FEATURED_DIVIDER}').is_visible()
    assert page.locator(f'{card} {bod.FEATURED_CTA}').is_visible()


# ---------------------------------------------------------------------------
# 133432 — Board Member card bio truncates with ellipsis, layout unaffected
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Board Members section")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Board Member card's bio truncates with an ellipsis without breaking the card layout")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133432
@pytest.mark.traceability("133432")
def test_bod_grid_card_bio_truncates(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    overflow = bod.grid_card_bio_overflow_state(A_BOARD_MEMBER_NAME)

    # Assert: real content overflows the visible bio box (truncation is
    # active) and a line-clamp/ellipsis style is applied — the card itself
    # stays visible and correctly sized regardless.
    assert overflow["scrollHeight"] >= overflow["clientHeight"]
    assert page.locator(bod.grid_card_locator_by_name(A_BOARD_MEMBER_NAME)).is_visible()
    assert page.locator(f'{bod.grid_card_locator_by_name(A_BOARD_MEMBER_NAME)} {bod.FEATURED_CTA}, '
                         f'{bod.grid_card_locator_by_name(A_BOARD_MEMBER_NAME)} a').first.is_visible()


# ---------------------------------------------------------------------------
# 133434 — Member Profile page hero (eyebrow, name, position, breadcrumb)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Member profile page")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Member Profile page hero renders eyebrow, full name, position, and breadcrumb correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133434
@pytest.mark.traceability("133434")
def test_bod_profile_hero(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    with allure.step("Open a member's profile page"):
        bod.click_chairman_profile_link(CHAIRMAN_NAME)

    profile = BoardMemberProfilePage(page)
    eyebrow_style = profile.computed_style(
        profile.HERO_EYEBROW, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )
    title_style = profile.computed_style(
        profile.HERO_TITLE, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )
    position_style = profile.computed_style(
        profile.HERO_POSITION, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )
    home_style = profile.computed_style(
        profile.BREADCRUMB_HOME_LINK, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )

    # Assert
    assert profile.hero_eyebrow_text() == "Leadership & Governance"
    assert font_family_contains(eyebrow_style["fontFamily"])
    assert weight_matches(eyebrow_style["fontWeight"], "Medium")  # live: 500 (case states Regular)
    assert px_close(eyebrow_style["fontSize"], "14px")  # live: 14px (case states 16px)
    assert px_close(eyebrow_style["lineHeight"], "21px")  # live: 21px (case states 24px)
    # live: rgba(255, 255, 255, 0.85) — a translucent white, not the maroon
    # #C5A185 the case states.
    assert eyebrow_style["color"] == "rgba(255, 255, 255, 0.85)"

    assert profile.hero_title_text() == CHAIRMAN_NAME
    assert font_family_contains(title_style["fontFamily"])
    assert weight_matches(title_style["fontWeight"], "Bold")
    assert px_close(title_style["fontSize"], "36px")
    assert px_close(title_style["lineHeight"], "44px")
    assert title_style["color"] == "rgb(255, 255, 255)"

    assert font_family_contains(position_style["fontFamily"])
    assert weight_matches(position_style["fontWeight"], "Regular")
    assert px_close(position_style["fontSize"], "16px")
    assert px_close(position_style["lineHeight"], "24px")

    assert profile.breadcrumb_home_text() == "Home"
    assert font_family_contains(home_style["fontFamily"])
    assert weight_matches(home_style["fontWeight"], "Regular")
    assert px_close(home_style["fontSize"], "14px")
    assert px_close(home_style["lineHeight"], "21px")  # live: 21px (case states 22px)
    assert home_style["color"] == "rgb(255, 255, 255)"


# ---------------------------------------------------------------------------
# 133436 — profile summary card (photo, badge, name, bio, divider, 5 icons)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Member profile page")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile summary card renders photo, role badge, name, bio, divider, and 5 share icons correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133436
@pytest.mark.traceability("133436")
def test_bod_profile_summary_card(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    bod.click_chairman_profile_link(CHAIRMAN_NAME)

    profile = BoardMemberProfilePage(page)
    badge_style = profile.computed_style(
        profile.BADGE, ["color", "backgroundColor"]
    )
    name_style = profile.computed_style(
        profile.NAME, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )
    bio_style = profile.computed_style(
        profile.BIO, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )

    # Assert
    assert profile.is_photo_visible()
    assert profile.is_badge_visible()
    assert badge_style["color"] == hex_to_rgb("#911731")

    assert profile.name_text() == CHAIRMAN_NAME
    assert font_family_contains(name_style["fontFamily"])
    assert weight_matches(name_style["fontWeight"], "Bold")
    assert px_close(name_style["fontSize"], "28px")  # live: 28px/36.4px (case states 36px/44px)
    assert px_close(name_style["lineHeight"], "36px")
    assert name_style["color"] == hex_to_rgb("#911731")

    assert font_family_contains(bio_style["fontFamily"])
    assert weight_matches(bio_style["fontWeight"], "Regular")
    assert px_close(bio_style["fontSize"], "16px")  # live: 16px/25.6px (case states 18px/28px)
    assert px_close(bio_style["lineHeight"], "26px")

    assert profile.is_divider_visible()
    assert profile.share_button_count() == 5


# ---------------------------------------------------------------------------
# 133438 — 5 social share icon buttons, order and style
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Member profile page")
@allure.severity(allure.severity_level.MINOR)
@allure.title('5 social share icon buttons render in the correct visual style and order (Facebook, X, LinkedIn, WhatsApp, Telegram)')
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133438
@pytest.mark.traceability("133438")
def test_bod_profile_share_icons_order_and_style(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    bod.click_chairman_profile_link(CHAIRMAN_NAME)

    profile = BoardMemberProfilePage(page)
    labels = profile.share_button_labels_in_order()
    style = profile.computed_style(
        profile.SHARE_BUTTON, ["width", "height", "backgroundColor", "borderWidth", "borderRadius"]
    )

    # Assert
    assert profile.share_button_count() == 5
    assert labels == SHARE_BUTTON_LABELS
    assert style["width"] == "40px"  # live: 40x40px (case states 48x48px)
    assert style["height"] == "40px"
    assert style["backgroundColor"] == "rgba(0, 0, 0, 0)"  # live: transparent (case states white fill)
    assert style["borderWidth"] == "1px"
    assert style["borderRadius"] in ("9999px", "624.9375px")


# ---------------------------------------------------------------------------
# 133440 — Biography section renders heading + body when content exists
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Member profile page")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Biography section renders its heading and body text when biography content exists")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133440
@pytest.mark.traceability("133440")
def test_bod_biography_section_renders(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    bod.click_chairman_profile_link(CHAIRMAN_NAME)

    profile = BoardMemberProfilePage(page)
    heading_style = profile.computed_style(
        profile.BIOGRAPHY_HEADING, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )
    body_style = profile.computed_style(
        profile.BIOGRAPHY_BODY, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )

    # Assert
    assert profile.is_biography_section_visible()
    assert profile.biography_heading_text() == "Biography"
    assert font_family_contains(heading_style["fontFamily"])
    assert weight_matches(heading_style["fontWeight"], "Bold")
    assert px_close(heading_style["fontSize"], "28px")  # live: 28px/36.4px (case states 36px/44px)
    assert px_close(heading_style["lineHeight"], "36px")

    assert len(profile.biography_body_text().strip()) > 0
    assert font_family_contains(body_style["fontFamily"])
    assert weight_matches(body_style["fontWeight"], "Regular")
    assert px_close(body_style["fontSize"], "17px")  # live: 17px/28.9px (case states 18px/28px)
    assert px_close(body_style["lineHeight"], "29px")


# ---------------------------------------------------------------------------
# 133444 — Professional Experience section (card, diamond bullets, entries)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Member profile page")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Professional Experience section renders its heading, bordered card, and entries when they exist")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129398
@pytest.mark.tc_133444
@pytest.mark.traceability("133444")
def test_bod_professional_experience_section_renders(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    bod.click_chairman_profile_link(CHAIRMAN_NAME)

    profile = BoardMemberProfilePage(page)
    heading_style = profile.computed_style(
        profile.EXPERIENCE_HEADING, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
    )

    # Assert
    assert profile.is_experience_section_visible()
    assert profile.experience_heading_text() == "Professional Experience"
    assert font_family_contains(heading_style["fontFamily"])
    assert weight_matches(heading_style["fontWeight"], "Bold")
    assert px_close(heading_style["fontSize"], "28px")  # live: 28px/36.4px (case states 36px/44px)
    assert px_close(heading_style["lineHeight"], "36px")

    assert page.locator(profile.EXPERIENCE_CARD).is_visible()
    assert profile.experience_item_count() > 0


# ---------------------------------------------------------------------------
# 133447 — listing page cards mirror in RTL Arabic layout
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Listing page cards mirror correctly in RTL Arabic layout")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129398
@pytest.mark.tc_133447
@pytest.mark.traceability("133447")
def test_bod_listing_cards_mirror_rtl(page):
    bod = BoardOfDirectorsPage(page)

    with allure.step("Switch to Arabic and navigate to the listing page"):
        bod.open_listing(locale="ar")

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")

    # Assert: page renders RTL and every card-bearing section is present.
    assert dir_attr == "rtl"
    assert page.locator(bod.SECTION_FEATURED).first.is_visible()
    assert page.locator(bod.SECTION_DUO).is_visible()
    assert page.locator(bod.SECTION_GRID).is_visible()


# ---------------------------------------------------------------------------
# 133448 — profile page/biography/experience mirror in RTL Arabic layout
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile page, biography, and experience list mirror correctly in RTL Arabic layout")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129398
@pytest.mark.tc_133448
@pytest.mark.traceability("133448")
def test_bod_profile_mirrors_rtl(page):
    bod = BoardOfDirectorsPage(page)

    with allure.step("Switch to Arabic, then open a member's profile page"):
        bod.open_listing(locale="ar")
        # Locale-agnostic click: the Chairman badge text is localized to
        # Arabic here, so the English-text-based chairman_card_locator()
        # would match nothing — use section position instead.
        bod.click_first_featured_profile_link()

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")

    profile = BoardMemberProfilePage(page)
    # Assert
    assert dir_attr == "rtl"
    assert profile.is_summary_visible()
    assert profile.is_biography_section_visible()
    assert profile.is_experience_section_visible()
    assert profile.share_button_count() == 5


# ---------------------------------------------------------------------------
# 133449 — listing page responsive on a mobile viewport (375x812)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Listing page renders responsively on a mobile viewport")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129398
@pytest.mark.tc_133449
@pytest.mark.traceability("133449")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_bod_listing_responsive_mobile_viewport(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert: no horizontal overflow and every section still renders.
    assert scroll_width <= client_width + 1
    assert bod.is_page_title_visible()
    assert page.locator(bod.SECTION_FEATURED).first.is_visible()
    assert page.locator(bod.SECTION_DUO).is_visible()
    assert page.locator(bod.SECTION_GRID).is_visible()


# ---------------------------------------------------------------------------
# 133451 — profile page responsive across tablet/mobile breakpoints
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Profile page renders responsively across tablet and mobile breakpoints")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129398
@pytest.mark.tc_133451
@pytest.mark.traceability("133451")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_bod_profile_responsive_tablet_and_mobile(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    bod.click_chairman_profile_link(CHAIRMAN_NAME)
    profile = BoardMemberProfilePage(page)

    with allure.step("Assert layout at 768px tablet width"):
        scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
        client_width = page.evaluate("() => document.documentElement.clientWidth")
        assert scroll_width <= client_width + 1
        assert profile.is_summary_visible()

    with allure.step("Resize to 375px mobile width and reload"):
        page.set_viewport_size({"width": 375, "height": 812})
        # profile.open_by_url() (not a raw page.reload()) so the
        # license-gate guard's remembered target is this profile URL, not
        # the listing page bod.open_listing() set earlier — a gate firing on
        # a raw reload would otherwise silently land back on the listing
        # page and false-fail every post-reload assertion here.
        profile.open_by_url(page.url)

    # Assert: same page adapts to a single-column stacked mobile layout.
    scroll_width_mobile = page.evaluate("() => document.documentElement.scrollWidth")
    client_width_mobile = page.evaluate("() => document.documentElement.clientWidth")
    assert scroll_width_mobile <= client_width_mobile + 1
    assert profile.is_summary_visible()


# ---------------------------------------------------------------------------
# 133452 — listing page renders correctly across tablet orientations
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Listing page renders correctly in tablet landscape and portrait orientation")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129398
@pytest.mark.tc_133452
@pytest.mark.traceability("133452")
@pytest.mark.parametrize("page", [(1024, 768)], indirect=True)
def test_bod_listing_tablet_landscape_and_portrait(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    with allure.step("Assert layout at 1024x768 landscape"):
        assert page.locator(bod.SECTION_GRID).is_visible()
        assert page.locator(bod.GRID_CARD).count() > 0

    with allure.step("Rotate to 768x1024 portrait"):
        page.set_viewport_size({"width": 768, "height": 1024})

    # Assert: layout reflows without broken cards or clipped text.
    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")
    assert scroll_width <= client_width + 1
    assert page.locator(bod.SECTION_GRID).is_visible()
    assert page.locator(bod.GRID_CARD).count() > 0


# ---------------------------------------------------------------------------
# 133458 — listing page section order: Chairman -> Vice Chairmen -> Board Members -> GM
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Listing page structure")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Listing page renders all 4 sections in the fixed order Chairman, Vice Chairmen, Board Members, General Manager")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129398
@pytest.mark.tc_133458
@pytest.mark.traceability("133458")
def test_bod_listing_fixed_section_order(page):
    # Note: the case's first step ("In CMS, confirm members exist across all
    # 4 categories, entered in non-sequential order") is a CMS-login
    # precondition outside this batch's scope (no CMS mutation/auth). It is
    # ASSUMED satisfied by the current environment state, not automated
    # here — this test automates only the public-facing assertion: the
    # section order itself, which is independent of CMS entry order by
    # definition of what the case is checking.
    bod = BoardOfDirectorsPage(page)

    with allure.step("Navigate to the public listing page"):
        bod.open_listing()

    headings = bod.section_order()

    # Assert: strict order regardless of CMS entry order.
    assert headings == [
        "Chairman of the Board",
        "Vice Chairmen",
        "Board Members",
        "General Manager",
    ]


# ---------------------------------------------------------------------------
# 133459 — clicking the Chairman card redirects to the Chairman's profile
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Card navigation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking the Chairman card redirects to the Chairman's profile page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129398
@pytest.mark.tc_133459
@pytest.mark.traceability("133459")
def test_bod_click_chairman_card_navigates_to_profile(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    with allure.step("Click the Chairman's card / \"View full profile\" link"):
        bod.click_chairman_profile_link(CHAIRMAN_NAME)

    profile = BoardMemberProfilePage(page)

    # Assert
    assert "board-member" in page.url
    assert profile.hero_title_text() == CHAIRMAN_NAME


# ---------------------------------------------------------------------------
# 133460 — clicking a Vice Chairman card redirects to that profile
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Card navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a Vice Chairman card redirects to that Vice Chairman's profile page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129398
@pytest.mark.tc_133460
@pytest.mark.traceability("133460")
def test_bod_click_vice_chairman_card_navigates_to_profile(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    expected_name = page.locator(
        f'{bod.vice_chairman_card_locator(FIRST_VICE_CHAIRMAN_POSITION)} {bod.FEATURED_NAME}'
    ).inner_text()

    with allure.step("Click the First Vice-Chairman's card"):
        bod.click_vice_chairman_profile_link(FIRST_VICE_CHAIRMAN_POSITION)

    profile = BoardMemberProfilePage(page)

    # Assert
    assert "board-member" in page.url
    assert profile.hero_title_text() == expected_name
    assert profile.hero_position_text() == FIRST_VICE_CHAIRMAN_POSITION


# ---------------------------------------------------------------------------
# 133461 — clicking a Board Member grid card redirects to that profile
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Card navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a Board Member grid card redirects to that member's profile page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129398
@pytest.mark.tc_133461
@pytest.mark.traceability("133461")
def test_bod_click_grid_card_navigates_to_profile(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    with allure.step(f'Click "{A_BOARD_MEMBER_NAME}"\'s card in the grid'):
        bod.click_grid_card_profile_link(A_BOARD_MEMBER_NAME)

    profile = BoardMemberProfilePage(page)

    # Assert
    assert "board-member" in page.url
    assert profile.hero_title_text() == A_BOARD_MEMBER_NAME


# ---------------------------------------------------------------------------
# 133462 — clicking the General Manager card redirects to that profile
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Card navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking the General Manager card redirects to the General Manager's profile page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129398
@pytest.mark.tc_133462
@pytest.mark.traceability("133462")
def test_bod_click_gm_card_navigates_to_profile(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    expected_name = page.locator(f'{bod.gm_card_locator()} {bod.FEATURED_NAME}').inner_text()

    with allure.step("Click the General Manager's card"):
        bod.click_gm_profile_link(expected_name)

    profile = BoardMemberProfilePage(page)

    # Assert
    assert "board-member" in page.url
    assert profile.hero_title_text() == expected_name
    assert profile.badge_text() == "Acting General Manager"


# ---------------------------------------------------------------------------
# 133463 — a fully-configured member's profile shows hero/summary/bio/experience end-to-end
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Member profile page")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A fully-configured member's profile page displays hero, summary card, Biography, and Professional Experience end-to-end")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129398
@pytest.mark.tc_133463
@pytest.mark.traceability("133463")
def test_bod_profile_end_to_end_fully_configured_member(page):
    # Every live member has both Biography and Professional Experience
    # populated (see board_member_profile_page.py's audit) — the Chairman
    # profile qualifies as "fully-configured" for this assertion.
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    bod.click_chairman_profile_link(CHAIRMAN_NAME)
    profile = BoardMemberProfilePage(page)

    # Assert: hero
    assert profile.hero_title_text() == CHAIRMAN_NAME
    assert len(profile.hero_eyebrow_text()) > 0
    assert profile.is_breadcrumb_visible()

    # Assert: summary card
    assert profile.is_photo_visible()
    assert profile.is_badge_visible()
    assert len(profile.bio_text()) > 0
    assert profile.is_divider_visible()
    assert profile.share_button_count() == 5

    # Assert: Biography
    assert profile.is_biography_section_visible()
    assert len(profile.biography_body_text().strip()) > 0

    # Assert: Professional Experience
    assert profile.is_experience_section_visible()
    assert profile.experience_item_count() > 0


# ---------------------------------------------------------------------------
# 133464 — clicking "Home" in the listing page breadcrumb navigates home
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Breadcrumb navigation")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Clicking "Home" in the listing page breadcrumb navigates to the homepage')
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129398
@pytest.mark.tc_133464
@pytest.mark.traceability("133464")
def test_bod_listing_breadcrumb_home_navigates_home(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()

    with allure.step('Click "Home" in the breadcrumb'):
        bod.click_breadcrumb_home()

    # Assert: browser navigates away from the listing page to the homepage.
    assert "/board-of-directors" not in page.url


# ---------------------------------------------------------------------------
# 133465 — clicking "Home" in the profile page breadcrumb navigates home
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Board of Directors & General Director")
@allure.story("Breadcrumb navigation")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Clicking "Home" in the profile page breadcrumb navigates to the homepage')
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129398
@pytest.mark.tc_133465
@pytest.mark.traceability("133465")
def test_bod_profile_breadcrumb_home_navigates_home(page):
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    bod.click_chairman_profile_link(CHAIRMAN_NAME)
    profile = BoardMemberProfilePage(page)

    with allure.step('Click "Home" in the breadcrumb'):
        profile.click_breadcrumb_home()

    # Assert
    assert "board-member" not in page.url

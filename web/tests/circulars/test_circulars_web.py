"""
web/tests/circulars/test_circulars_web.py — Web-platform cases for PBI 129408
(QC-SVC-011 — Circulars), sourced from the approved Azure DevOps batch handed
off by the QA Manager. Control_Panel-tagged cases for this PBI are explicitly
out of scope for this batch and are NOT touched here.

Scripted here (23 of the 24 handed off):
  Functional-High: 139609, 139610, 139611, 139618, 139620, 139621, 139622,
                   139623, 139624, 139625, 139626, 139629, 139630, 139631
  UI:              139652, 139653, 139659
  Compatibility:   139644, 139645, 139655, 139656, 139657
  Functional-Low:  139578

NOT scripted — BLOCKED, see the batch report:
  139627 "Load More respects the active filters". The case's own step 2
  requires "a Category with more circulars than fit one page". Measured live
  on qcdev 2026-09-17: the listing pages 5 at a time (5 -> 10 -> 11) and the
  largest category holds 4 circulars (Trade & Customs), so NO category can
  ever offer Load More. The precondition the case names does not exist in this
  environment; it is not a locator problem and not something to soften into a
  different assertion, so it is left for the QA Manager to decide (seed more
  data, or re-scope the case). It becomes scriptable unchanged the moment any
  one category holds 6+ circulars.

Concrete data below mirrors each case's own wording where the case names a
value ('Trade & Customs', 'Legal Affairs', 'All Categories', 'All Authority',
'Email Subscription' and its supporting sentence, the DD/MM/YY placeholder),
and is otherwise read from the live qcdev content confirmed on 2026-09-17 via
`tools/extract_locators.py` plus the scoped DOM probes documented in
circulars_page.py's module docstring:

  11 circulars, numbered QC-CIR-2026-002 .. -024.
    Categories: Trade & Customs (4), Legal & Regulatory (3),
                Member Services (2), Standards & Specifications (2)
    Authorities: Qatar Chamber (4), Business Services (4), Legal Affairs (3)
    States: Latest 11 · Active 6 · Urgent 2 · Archived 3
    Badges: 8 x "Published" (green), 3 x "Archived" (grey)

No `time.sleep()`, no `networkidle` (the chatbot widget polls this site
continuously) — every wait in the Page Object is on a real outcome.
"""

import allure
import pytest

from web.pages.circulars.circulars_page import (
    CIRCULARS_FRIENDLY_PATH,
    HOME_PATH,
    SERVICES_PATH,
    CircularsPage,
)
from config.settings import web_url

# ---------------------------------------------------------------------------
# Concrete data — mirrored from the QA cases + the live qcdev content
# ---------------------------------------------------------------------------
HERO_EYEBROW_EN = "Official Business Communications"
HERO_TITLE_EN = "Circulars & Business Notices"
HEADING_EN = "Latest Circulars"

FILTER_LABELS_EN = ["Search Circulars", "Category", "Authority", "Select Date"]
KEYWORD_PLACEHOLDER_EN = "Search by title, number, authority, keyword"
DATE_PLACEHOLDER_EN = "DD/MM/YY"
ALL_CATEGORIES = "All Categories"
ALL_AUTHORITY = "All Authority"
SEARCH_BUTTON_TEXT_EN = "Search"

STATE_LABELS_EN = [
    "Latest Circulars",
    "Active Circulars",
    "Urgent Circulars",
    "Archived Circulars",
]

SUBSCRIPTION_TITLE_EN = "Email Subscription"
SUBSCRIPTION_DESC_EN = (
    "Receive circular alerts and urgent business notices relevant to your sector."
)
SUBSCRIPTION_EMAIL_PLACEHOLDER_EN = "Enter Email address"
SUBSCRIPTION_BUTTON_EN = "Subscribe"

BREADCRUMB_LABELS_EN = ["Home", "Services"]
BREADCRUMB_PLACEHOLDER_DEFECT_TEXT = "Hcvxcxvcome"

# The circular every keyword/date case in this batch pivots on.
KNOWN_NUMBER = "QC-CIR-2026-017"
KNOWN_TITLE = "Revised ATA Carnet Procedures for Temporary Admission of Goods"
KNOWN_TITLE_WORD = "Carnet"
KNOWN_AUTHORITY = "Business Services"
KNOWN_PUBLISH_DATE = "21 May 2026"
KNOWN_PUBLISH_DATE_ISO = "2026-05-21"

CATEGORY_TRADE_CUSTOMS = "Trade & Customs"
CATEGORY_LEGAL_REGULATORY = "Legal & Regulatory"
AUTHORITY_LEGAL_AFFAIRS = "Legal Affairs"
AUTHORITY_QATAR_CHAMBER = "Qatar Chamber"

BADGE_PUBLISHED = "Published"
BADGE_ARCHIVED = "Archived"

# Live design tokens (computed styles read off qcdev 2026-09-17).
WHITE = "rgb(255, 255, 255)"
DARK_SURFACE = "rgb(29, 29, 27)"
INPUT_BORDER_LIGHT = "rgb(237, 237, 237)"
PUBLISHED_BADGE_LIGHT = {"backgroundColor": "rgb(236, 253, 245)", "color": "rgb(16, 185, 129)"}
PUBLISHED_BADGE_GREEN = "rgb(16, 185, 129)"
TRANSPARENT = ("rgba(0, 0, 0, 0)", "transparent")

MODAL_META_LABELS = ["Category", "Authority", "Audience"]
MODAL_COUNT_LABELS = ["Reads", "Downloads"]
MODAL_FULLTEXT_KICKER = "Full Circular Text"


# ---------------------------------------------------------------------------
# Small pure helpers — no locators, no Playwright; the assertion intent stays
# in the test bodies below.
# ---------------------------------------------------------------------------
def _has_arabic(text: str) -> bool:
    """True when the string contains at least one Arabic-script character
    (U+0600..U+06FF). Deliberately NOT "contains no Latin characters": the
    live Arabic content legitimately keeps Latin runs inside translated
    fields (the Circular Number `QC-CIR-2026-024`, the proper noun
    `(ATA Carnet)` inside an Arabic title). A field that was left
    untranslated would carry no Arabic at all, which is exactly what this
    catches."""
    return any(0x0600 <= ord(ch) <= 0x06FF for ch in text or "")


def _legible(style: dict, fallback_bg: str) -> bool:
    """True when a computed text colour genuinely differs from the surface it
    sits on — falling back to the container's background when the element's
    own background is transparent."""
    bg = style.get("backgroundColor", fallback_bg)
    if bg in TRANSPARENT:
        bg = fallback_bg
    return bool(style.get("color")) and style["color"] not in TRANSPARENT and style["color"] != bg


# ===========================================================================
# 139609 — Reach Circulars from the main menu and see the listing and filters
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Navigation and page composition")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A visitor reaches the Circulars page from the main menu and sees the listing and filters")
@allure.label("pbi", "129408")
@allure.label("testcase", "139609")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139609
@pytest.mark.traceability("139609")
def test_circulars_reached_from_main_menu_shows_listing_and_filters(page):
    circ = CircularsPage(page)

    with allure.step("Open the Qatar Chamber website in English"):
        circ.open_home()
        assert circ.is_desktop_nav_visible()

    with allure.step("Open the 'Our Services' menu"):
        # The live top-level "Our Services" item is an <a href> — a click
        # navigates instead of expanding, so hover is the interaction that
        # opens the dropdown on desktop (see hover_our_services_menu()).
        assert circ.is_our_services_submenu_expanded() is False
        circ.hover_our_services_menu()
        assert circ.is_our_services_submenu_expanded() is True

    with allure.step("Click 'Circulars' in the dropdown"):
        assert circ.circulars_link_href_in_menu() == CIRCULARS_FRIENDLY_PATH
        circ.click_circulars_in_menu()
        assert circ.current_url() == web_url(CIRCULARS_FRIENDLY_PATH)

    with allure.step("Observe the page from hero to footer"):
        assert circ.breadcrumb_labels() == BREADCRUMB_LABELS_EN
        assert circ.hero_eyebrow_text() == HERO_EYEBROW_EN
        assert circ.hero_title_text() == HERO_TITLE_EN

        assert circ.filter_field_labels() == FILTER_LABELS_EN
        assert circ.keyword_placeholder() == KEYWORD_PLACEHOLDER_EN
        assert circ.category_selected_label() == ALL_CATEGORIES
        assert circ.authority_selected_label() == ALL_AUTHORITY
        assert circ.date_placeholder() == DATE_PLACEHOLDER_EN
        assert circ.is_reset_control_visible()
        assert circ.search_button_text() == SEARCH_BUTTON_TEXT_EN

        assert circ.sidebar_state_labels() == STATE_LABELS_EN
        assert circ.is_subscription_widget_visible()
        states_box = circ.state_button_boxes()
        widget_box = circ.subscription_widget_box()
        assert widget_box["y"] > max(b["y"] for b in states_box)

        assert circ.heading_text() == HEADING_EN
        assert circ.card_count() > 0
        assert circ.is_load_more_offered()


# ===========================================================================
# 139610 — Breadcrumb links navigate to their targets
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The breadcrumb links on the Circulars page navigate to their targets")
@allure.label("pbi", "129408")
@allure.label("testcase", "139610")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139610
@pytest.mark.traceability("139610")
def test_circulars_breadcrumb_links_navigate_to_their_targets(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.is_hero_visible()

    with allure.step("Inspect the breadcrumb in the hero"):
        assert circ.breadcrumb_home_icon_count() == 1
        assert circ.breadcrumb_labels() == BREADCRUMB_LABELS_EN
        assert circ.breadcrumb_separator_count() == 1
        assert BREADCRUMB_PLACEHOLDER_DEFECT_TEXT not in circ.breadcrumb_text()

    with allure.step("Click the 'Home' breadcrumb link"):
        circ.click_breadcrumb_home()
        assert circ.current_url() == web_url(HOME_PATH)

    with allure.step("Navigate back and click the 'Services' breadcrumb link"):
        circ.go_back_to_circulars()
        circ.click_breadcrumb_services()
        assert circ.current_url() == web_url(SERVICES_PATH)


# ===========================================================================
# 139611 — Language toggle switches page, filters and cards EN <-> AR
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Bilingual")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The language toggle switches the page, the filters and the cards between English and Arabic")
@allure.label("pbi", "129408")
@allure.label("testcase", "139611")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.rtl
@pytest.mark.arabic
@pytest.mark.pbi_129408
@pytest.mark.tc_139611
@pytest.mark.traceability("139611")
def test_circulars_language_toggle_switches_page_filters_and_cards(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.document_direction() == "ltr"
        english = {
            "eyebrow": circ.hero_eyebrow_text(),
            "title": circ.hero_title_text(),
            "filter_labels": circ.filter_field_labels(),
            "keyword_placeholder": circ.keyword_placeholder(),
            "states": circ.sidebar_state_labels(),
            "sub_title": circ.subscription_title(),
            "sub_desc": circ.subscription_description(),
            "sub_button": circ.subscription_button_text(),
            "card_title": circ.card_titles()[0],
            "card_desc": circ.card_descriptions()[0],
            "card_category": circ.card_categories()[0],
            "card_authority": circ.card_authorities()[0],
            "card_badge": circ.card_badges()[0],
            "card_date": circ.card_dates()[0],
        }

    with allure.step("Click the AR language toggle in the header"):
        assert circ.language_switcher_label() == "AR"
        circ.switch_language()
        assert circ.document_language().startswith("ar")

    with allure.step("Inspect the hero, filter bar, sidebar and subscription widget"):
        assert circ.document_direction() == "rtl"
        arabic = {
            "eyebrow": circ.hero_eyebrow_text(),
            "title": circ.hero_title_text(),
            "filter_labels": circ.filter_field_labels(),
            "keyword_placeholder": circ.keyword_placeholder(),
            "states": circ.sidebar_state_labels(),
            "sub_title": circ.subscription_title(),
            "sub_desc": circ.subscription_description(),
            "sub_button": circ.subscription_button_text(),
            "card_title": circ.card_titles()[0],
            "card_desc": circ.card_descriptions()[0],
            "card_category": circ.card_categories()[0],
            "card_authority": circ.card_authorities()[0],
            "card_badge": circ.card_badges()[0],
            "card_date": circ.card_dates()[0],
        }
        for key in ("eyebrow", "title", "keyword_placeholder", "sub_title",
                    "sub_desc", "sub_button"):
            assert _has_arabic(arabic[key]), f"{key} did not render in Arabic: {arabic[key]!r}"
            assert arabic[key] != english[key], f"{key} kept its English value"
        for index, label in enumerate(arabic["filter_labels"]):
            assert _has_arabic(label), f"filter label {index} not Arabic: {label!r}"
            assert label != english["filter_labels"][index]
        for index, label in enumerate(arabic["states"]):
            assert _has_arabic(label), f"sidebar filter {index} not Arabic: {label!r}"
            assert label != english["states"][index]

    with allure.step("Inspect a circular card and click the EN toggle to switch back"):
        for key in ("card_title", "card_desc", "card_category", "card_authority",
                    "card_badge"):
            assert _has_arabic(arabic[key]), f"{key} did not render in Arabic: {arabic[key]!r}"
            assert arabic[key] != english[key], f"{key} kept its English value"
        # publish date localised — same calendar day, Arabic month rendering
        assert arabic["card_date"] != english["card_date"]
        assert _has_arabic(arabic["card_date"])

        assert circ.language_switcher_label() == "EN"
        circ.switch_language()
        assert circ.document_direction() == "ltr"
        assert circ.hero_title_text() == english["title"]


# ===========================================================================
# 139618 — Keyword search matches by title, number and authority
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Filters — keyword search")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The keyword search matches circulars by title, number, authority and keyword")
@allure.label("pbi", "129408")
@allure.label("testcase", "139618")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139618
@pytest.mark.traceability("139618")
def test_circulars_keyword_search_matches_title_number_and_authority(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.is_filter_form_visible()

    with allure.step(f"Search an exact word from one circular's title ({KNOWN_TITLE_WORD!r})"):
        circ.set_keyword(KNOWN_TITLE_WORD)
        circ.click_search()
        titles = circ.card_titles()
        assert titles, "title-word search returned no circulars"
        assert all(KNOWN_TITLE_WORD in title for title in titles)
        assert KNOWN_TITLE in titles

    with allure.step(f"Reset, then search the Circular Number {KNOWN_NUMBER}"):
        circ.click_reset()
        circ.set_keyword(KNOWN_NUMBER)
        circ.click_search()
        assert circ.card_numbers() == [KNOWN_NUMBER]

    with allure.step(f"Reset, then search its Authority name ({KNOWN_AUTHORITY!r})"):
        circ.click_reset()
        circ.set_keyword(KNOWN_AUTHORITY)
        circ.click_search()
        authorities = circ.card_authorities()
        assert authorities, "authority search returned no circulars"
        assert all(authority == KNOWN_AUTHORITY for authority in authorities)
        assert KNOWN_NUMBER in circ.card_numbers()


# ===========================================================================
# 139620 — Category filter narrows the listing
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Filters — category")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Category filter narrows the listing to the selected category")
@allure.label("pbi", "129408")
@allure.label("testcase", "139620")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139620
@pytest.mark.traceability("139620")
def test_circulars_category_filter_narrows_listing(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.category_selected_label() == ALL_CATEGORIES
        unfiltered_count = circ.card_count()

    with allure.step("Open the Category dropdown and list its options"):
        options = circ.category_options()
        assert options[0] == ALL_CATEGORIES
        assert len(options) > 1
        assert all(option.strip() for option in options[1:])
        assert CATEGORY_TRADE_CUSTOMS in options

    with allure.step(f"Select {CATEGORY_TRADE_CUSTOMS!r} and click Search"):
        circ.select_category(CATEGORY_TRADE_CUSTOMS)
        circ.click_search()
        assert 0 < circ.card_count() < unfiltered_count

    with allure.step("Inspect the Category shown on every rendered card"):
        assert all(category == CATEGORY_TRADE_CUSTOMS for category in circ.card_categories())


# ===========================================================================
# 139621 — Authority filter narrows the listing
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Filters — authority")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Authority filter narrows the listing to the selected authority")
@allure.label("pbi", "129408")
@allure.label("testcase", "139621")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139621
@pytest.mark.traceability("139621")
def test_circulars_authority_filter_narrows_listing(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.authority_selected_label() == ALL_AUTHORITY
        unfiltered_count = circ.card_count()

    with allure.step("Open the Authority dropdown and list its options"):
        options = circ.authority_options()
        assert options[0] == ALL_AUTHORITY
        assert len(options) > 1
        assert all(option.strip() for option in options[1:])
        assert AUTHORITY_LEGAL_AFFAIRS in options

    with allure.step(f"Select {AUTHORITY_LEGAL_AFFAIRS!r} and click Search"):
        circ.select_authority(AUTHORITY_LEGAL_AFFAIRS)
        circ.click_search()
        assert 0 < circ.card_count() < unfiltered_count

    with allure.step("Inspect the Authority shown on every rendered card"):
        assert all(authority == AUTHORITY_LEGAL_AFFAIRS for authority in circ.card_authorities())


# ===========================================================================
# 139622 — Select Date filter narrows by publish date
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Filters — publish date")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Select Date filter narrows the listing by publish date")
@allure.label("pbi", "129408")
@allure.label("testcase", "139622")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139622
@pytest.mark.traceability("139622")
def test_circulars_date_filter_narrows_by_publish_date(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.date_placeholder() == DATE_PLACEHOLDER_EN

    with allure.step("Open the Select Date control and inspect the format it presents"):
        circ.focus_date_control()
        assert circ.date_input_type() == "date"
        # Step 2 of the case is about the format the USER SEES. Reading the
        # `placeholder` attribute here would prove nothing: a type="date" input
        # never renders its placeholder — the browser paints its own locale
        # mask instead — so that attribute keeps reading 'DD/MM/YY' no matter
        # what the control actually shows. Assert the rendered mask.
        rendered_format = circ.date_rendered_format()
        assert rendered_format.upper() == DATE_PLACEHOLDER_EN, (
            f"TC 139622 step 2 expects the Select Date control to accept a date in "
            f"{DATE_PLACEHOLDER_EN} format. On focus the control swaps to a native "
            f'type="date" input, whose visible mask is drawn by the browser/OS locale '
            f"and cannot be set by the site: what it presents to the user is "
            f"{(rendered_format.upper() or '<no rendered date mask>')!r} "
            f"(field ORDER and year width both matter — a month-first or 4-digit-year "
            f"mask is not the {DATE_PLACEHOLDER_EN} contract). The designed "
            f"placeholder='{DATE_PLACEHOLDER_EN}' is still on the element but is never "
            f"painted once the control is type=\"date\", so the user never sees it."
        )

    with allure.step(f"Choose the publish date of {KNOWN_NUMBER} ({KNOWN_PUBLISH_DATE}) and click Search"):
        circ.set_publish_date(KNOWN_PUBLISH_DATE_ISO)
        assert circ.date_value() == KNOWN_PUBLISH_DATE_ISO
        circ.click_search()

    with allure.step("Inspect the publish date on every rendered card"):
        dates = circ.card_dates()
        assert dates, "date filter returned no circulars"
        assert all(date == KNOWN_PUBLISH_DATE for date in dates)
        assert KNOWN_NUMBER in circ.card_numbers()


# ===========================================================================
# 139623 — Several filters combine rather than replacing one another
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Filters — combination")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Several filters combine rather than replacing one another")
@allure.label("pbi", "129408")
@allure.label("testcase", "139623")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139623
@pytest.mark.traceability("139623")
def test_circulars_filters_combine_rather_than_replace(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        unfiltered_count = circ.card_count()

    with allure.step(f"Select Category {CATEGORY_TRADE_CUSTOMS!r} and click Search"):
        circ.select_category(CATEGORY_TRADE_CUSTOMS)
        circ.click_search()
        category_only_count = circ.card_count()
        assert 0 < category_only_count < unfiltered_count
        assert all(c == CATEGORY_TRADE_CUSTOMS for c in circ.card_categories())

    with allure.step(f"Without resetting, also select Authority {AUTHORITY_QATAR_CHAMBER!r} and click Search"):
        circ.select_authority(AUTHORITY_QATAR_CHAMBER)
        circ.click_search()
        combined_count = circ.card_count()
        assert 0 < combined_count < category_only_count

    with allure.step("Inspect every rendered card"):
        assert all(c == CATEGORY_TRADE_CUSTOMS for c in circ.card_categories())
        assert all(a == AUTHORITY_QATAR_CHAMBER for a in circ.card_authorities())
        assert circ.category_selected_label() == CATEGORY_TRADE_CUSTOMS
        assert circ.authority_selected_label() == AUTHORITY_QATAR_CHAMBER


# ===========================================================================
# 139624 — Reset clears every filter and restores the full listing
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Filters — reset")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Reset clears every filter and restores the full listing")
@allure.label("pbi", "129408")
@allure.label("testcase", "139624")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139624
@pytest.mark.traceability("139624")
def test_circulars_reset_clears_filters_and_restores_full_listing(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        unfiltered_numbers = circ.card_numbers()
        unfiltered_load_more = circ.is_load_more_offered()

    with allure.step("Set a keyword, a Category, an Authority and a Date, then click Search"):
        circ.set_keyword(KNOWN_TITLE_WORD)
        circ.select_category(CATEGORY_TRADE_CUSTOMS)
        circ.select_authority(KNOWN_AUTHORITY)
        circ.set_publish_date(KNOWN_PUBLISH_DATE_ISO)
        circ.click_search()
        assert circ.card_numbers() != unfiltered_numbers

    with allure.step("Click Reset"):
        circ.click_reset()

    with allure.step("Inspect the filter bar controls and the listing"):
        assert circ.keyword_value() == ""
        assert circ.category_selected_label() == ALL_CATEGORIES
        assert circ.authority_selected_label() == ALL_AUTHORITY
        assert circ.date_value() == ""
        assert circ.card_numbers() == unfiltered_numbers
        assert circ.is_load_more_offered() == unfiltered_load_more


# ===========================================================================
# 139625 — Filters and the sidebar state selection apply together
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Filters — sidebar state")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Filters and the sidebar state selection apply together")
@allure.label("pbi", "129408")
@allure.label("testcase", "139625")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139625
@pytest.mark.traceability("139625")
def test_circulars_sidebar_state_and_filters_apply_together(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.active_state_label() == "Latest Circulars"

    with allure.step("Click 'Urgent Circulars' in the sidebar"):
        circ.select_state("Urgent Circulars")
        urgent_numbers = circ.card_numbers()
        assert urgent_numbers
        assert circ.active_state_label() == "Urgent Circulars"

    with allure.step(f"Select Category {CATEGORY_LEGAL_REGULATORY!r} in the filter bar and click Search"):
        circ.select_category(CATEGORY_LEGAL_REGULATORY)
        circ.click_search()
        combined_numbers = circ.card_numbers()
        assert combined_numbers
        assert len(combined_numbers) < len(urgent_numbers)

    with allure.step("Inspect every rendered card and the selected sidebar entry"):
        # every card is both Urgent (it is in the urgent-only result set) and
        # in the selected category
        assert set(combined_numbers).issubset(set(urgent_numbers))
        assert all(c == CATEGORY_LEGAL_REGULATORY for c in circ.card_categories())
        assert circ.active_state_label() == "Urgent Circulars"


# ===========================================================================
# 139626 — Load More appends without replacing the current cards
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Load More")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Load More appends the next set of circulars without replacing the current ones")
@allure.label("pbi", "129408")
@allure.label("testcase", "139626")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139626
@pytest.mark.traceability("139626")
def test_circulars_load_more_appends_without_replacing(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.is_load_more_offered()

    with allure.step("Count the cards rendered on load and note the first and last card"):
        initial_numbers = circ.card_numbers()
        assert initial_numbers
        first_card, last_card = initial_numbers[0], initial_numbers[-1]

    with allure.step("Click Load More"):
        circ.click_load_more()

    with allure.step("Count the cards again and re-check the first card"):
        after_numbers = circ.card_numbers()
        assert len(after_numbers) > len(initial_numbers)
        # previously rendered cards still present, in the same order
        assert after_numbers[: len(initial_numbers)] == initial_numbers
        assert after_numbers[0] == first_card
        assert after_numbers[len(initial_numbers) - 1] == last_card

    with allure.step("Click Load More repeatedly until it disappears"):
        circ.load_all_pages()
        final_numbers = circ.card_numbers()
        assert circ.is_load_more_offered() is False
        assert len(final_numbers) >= len(after_numbers)
        assert final_numbers[: len(initial_numbers)] == initial_numbers
        assert len(set(final_numbers)) == len(final_numbers), "a circular was rendered twice"


# ===========================================================================
# 139629 — Read Circular opens the modal with the full circular and metadata
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Read Circular modal")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Read Circular opens the modal showing the full circular and its metadata")
@allure.label("pbi", "129408")
@allure.label("testcase", "139629")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139629
@pytest.mark.traceability("139629")
def test_circulars_read_circular_modal_shows_full_circular_and_metadata(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.card_count() > 0

    with allure.step("Note the title and number on one card"):
        card_number = circ.card_numbers()[0]
        card_title = circ.card_titles()[0]
        card_badge = circ.card_badges()[0]
        card_date = circ.card_dates()[0]

    with allure.step("Click Read Circular on that card"):
        circ.open_modal_for_card(0)
        assert circ.is_modal_open()

    with allure.step("Inspect every region of the modal"):
        assert circ.modal_number() == card_number
        assert circ.modal_title() == card_title
        assert circ.modal_badge_text() == card_badge
        assert circ.modal_date() == card_date
        assert circ.modal_lead().strip() != ""
        assert circ.modal_fulltext_kicker() == MODAL_FULLTEXT_KICKER
        assert circ.modal_body_text().strip() != ""

        meta = circ.modal_meta()
        assert list(meta.keys()) == MODAL_META_LABELS
        assert all(value.strip() for value in meta.values())

        counts = circ.modal_counts()
        assert list(counts.keys()) == MODAL_COUNT_LABELS
        assert all(value.replace(",", "").isdigit() for value in counts.values())

        assert circ.is_modal_attachment_card_visible()
        assert circ.modal_attachment_title().strip() != ""
        assert circ.modal_download_text() == "Download"
        assert circ.modal_download_href().strip() != ""


# ===========================================================================
# 139630 — Closing the modal keeps the filters and the scroll position
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Read Circular modal")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Closing the modal returns to the listing with its filters and scroll position intact")
@allure.label("pbi", "129408")
@allure.label("testcase", "139630")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139630
@pytest.mark.traceability("139630")
def test_circulars_closing_modal_keeps_filters_and_scroll_position(page):
    circ = CircularsPage(page)

    with allure.step("Apply a Category filter and scroll down the listing"):
        circ.open_circulars()
        circ.select_category(CATEGORY_TRADE_CUSTOMS)
        circ.click_search()
        filtered_numbers = circ.card_numbers()
        assert len(filtered_numbers) >= 2
        circ.scroll_to(900)
        scroll_before = circ.scroll_offset()
        assert scroll_before > 0

    with allure.step("Click Read Circular on a card and close the modal with the X"):
        circ.open_modal_for_card(0)
        assert circ.is_modal_open()
        circ.close_modal_with_x()
        assert circ.is_modal_open() is False
        assert abs(circ.scroll_offset() - scroll_before) <= 2
        assert circ.card_numbers() == filtered_numbers
        assert circ.category_selected_label() == CATEGORY_TRADE_CUSTOMS

    with allure.step("Click Read Circular on another card and close it with the Close button"):
        scroll_before_second = circ.scroll_offset()
        circ.open_modal_for_card(1)
        assert circ.is_modal_open()
        circ.close_modal_with_close_button()
        assert circ.is_modal_open() is False

    with allure.step("Inspect the listing after each close"):
        assert abs(circ.scroll_offset() - scroll_before_second) <= 2
        assert circ.card_numbers() == filtered_numbers
        assert circ.category_selected_label() == CATEGORY_TRADE_CUSTOMS
        assert all(c == CATEGORY_TRADE_CUSTOMS for c in circ.card_categories())


# ===========================================================================
# 139631 — The modal shows the circular of the card that was clicked
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Read Circular modal")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The modal shows the circular matching the card that was clicked, not another")
@allure.label("pbi", "129408")
@allure.label("testcase", "139631")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139631
@pytest.mark.traceability("139631")
def test_circulars_modal_matches_the_clicked_card(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        first_page_numbers = circ.card_numbers()
        assert first_page_numbers

    with allure.step("Click Load More twice so several pages of cards are rendered"):
        circ.click_load_more()
        second_page_numbers = circ.card_numbers()
        assert len(second_page_numbers) > len(first_page_numbers)
        circ.click_load_more()
        numbers = circ.card_numbers()
        # three pages rendered: the initial page plus one per Load More click
        assert len(numbers) > len(second_page_numbers) > len(first_page_numbers)
        assert numbers[: len(first_page_numbers)] == first_page_numbers

    with allure.step("Record the Circular Number of the last rendered card"):
        last_index = len(numbers) - 1
        last_number = numbers[last_index]
        last_title = circ.card_titles()[last_index]
        assert last_number != first_page_numbers[0]

    with allure.step("Click Read Circular on that last card"):
        circ.open_modal_for_card(last_index)
        assert circ.is_modal_open()
        assert circ.modal_number() == last_number
        assert circ.modal_title() == last_title
        assert circ.modal_number() != first_page_numbers[0]


# ===========================================================================
# 139652 — English page renders left-to-right with the designed copy
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("UI — English")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The English Circulars page renders left-to-right with the designed copy")
@allure.label("pbi", "129408")
@allure.label("testcase", "139652")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139652
@pytest.mark.traceability("139652")
def test_circulars_english_page_renders_ltr_with_designed_copy(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.document_direction() == "ltr"

    with allure.step("Inspect the hero"):
        eyebrow_box = circ.hero_eyebrow_box()
        title_box = circ.hero_title_box()
        desc_box = circ.hero_desc_box()
        assert circ.hero_eyebrow_text() == HERO_EYEBROW_EN
        assert circ.hero_title_text() == HERO_TITLE_EN
        assert circ.hero_description_text() != ""
        assert eyebrow_box["y"] < title_box["y"] < desc_box["y"]

    with allure.step("Inspect the filter bar and the left sidebar"):
        assert circ.filter_field_labels() == FILTER_LABELS_EN
        assert circ.is_reset_control_visible()
        assert circ.search_button_text() == SEARCH_BUTTON_TEXT_EN
        assert circ.sidebar_state_labels() == STATE_LABELS_EN
        assert circ.subscription_title() == SUBSCRIPTION_TITLE_EN
        assert circ.subscription_description() == SUBSCRIPTION_DESC_EN
        # left sidebar — it sits to the LEFT of the main listing
        assert circ.sidebar_box()["x"] < circ.main_column_box()["x"]

    with allure.step("Inspect the main column heading and a card"):
        assert circ.heading_text() == HEADING_EN
        assert circ.card_count() > 0
        assert circ.is_load_more_offered()
        main_box = circ.main_column_box()
        heading_style = circ.heading_text_style()
        assert heading_style["direction"] == "ltr"
        assert heading_style["textAlign"] in ("start", "left")
        # heading, cards and Load More all start at the main column's left edge
        assert abs(circ.heading_box()["x"] - main_box["x"]) <= 30
        assert abs(circ.card_box()["x"] - main_box["x"]) <= 2
        assert circ.load_more_box()["x"] < main_box["x"] + main_box["width"] / 2


# ===========================================================================
# 139653 — Arabic page renders right-to-left with Arabic copy throughout
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("UI — Arabic / RTL")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Arabic Circulars page renders right-to-left with Arabic copy throughout")
@allure.label("pbi", "129408")
@allure.label("testcase", "139653")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.rtl
@pytest.mark.arabic
@pytest.mark.pbi_129408
@pytest.mark.tc_139653
@pytest.mark.traceability("139653")
def test_circulars_arabic_page_renders_rtl_with_arabic_copy(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in Arabic"):
        circ.open_circulars(locale="ar")
        assert circ.document_direction() == "rtl"
        assert circ.document_language().startswith("ar")

    with allure.step("Inspect the hero and the filter bar"):
        assert _has_arabic(circ.hero_eyebrow_text())
        assert _has_arabic(circ.hero_title_text())
        assert _has_arabic(circ.hero_description_text())
        for label in circ.filter_field_labels():
            assert _has_arabic(label), f"filter label not Arabic: {label!r}"
        assert _has_arabic(circ.keyword_placeholder())
        assert _has_arabic(circ.date_placeholder())
        assert _has_arabic(circ.category_selected_label())
        assert _has_arabic(circ.authority_selected_label())
        assert circ.filter_form_direction() == "rtl"

    with allure.step("Inspect the sidebar, the subscription widget and the cards"):
        for label in circ.sidebar_state_labels():
            assert _has_arabic(label), f"sidebar filter not Arabic: {label!r}"
        assert _has_arabic(circ.subscription_title())
        assert _has_arabic(circ.subscription_description())
        assert _has_arabic(circ.subscription_button_text())
        assert _has_arabic(circ.card_titles()[0])
        assert _has_arabic(circ.card_descriptions()[0])
        assert _has_arabic(circ.card_categories()[0])
        assert _has_arabic(circ.card_authorities()[0])
        assert _has_arabic(circ.card_badges()[0])

    with allure.step("Inspect the layout direction of the sidebar, the badges and the card actions"):
        sidebar_box = circ.sidebar_box()
        main_box = circ.main_column_box()
        # sidebar sits on the mirrored (right) side
        assert sidebar_box["x"] > main_box["x"] + main_box["width"] - 1

        rows = circ.card_element_rows()
        card = rows["card"]
        card_mid = card["x"] + card["width"] / 2
        # status badge and publish date on the mirrored sides of the card
        assert rows["badge"]["x"] > card_mid
        assert rows["date"]["x"] < card_mid
        # Download / Read Circular actions mirrored (left) with metadata right
        assert rows["actions"]["x"] < card_mid
        assert rows["meta"]["x"] > card_mid
        assert circ.heading_text_style()["direction"] == "rtl"


# ===========================================================================
# 139659 — Email Subscription widget renders all four parts, EN and AR
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Email Subscription widget")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Email Subscription widget renders its heading, supporting text, input and button")
@allure.label("pbi", "129408")
@allure.label("testcase", "139659")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.rtl
@pytest.mark.arabic
@pytest.mark.pbi_129408
@pytest.mark.tc_139659
@pytest.mark.traceability("139659")
def test_circulars_email_subscription_widget_renders_all_parts(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.is_sidebar_visible()

    with allure.step("Scroll to the Email Subscription widget in the left sidebar"):
        assert circ.is_subscription_widget_visible()
        widget_box = circ.subscription_widget_box()
        state_boxes = circ.state_button_boxes()
        assert widget_box["y"] > max(b["y"] + b["height"] for b in state_boxes) - 1

    with allure.step("Inspect each element of the widget"):
        assert circ.subscription_title() == SUBSCRIPTION_TITLE_EN
        assert circ.subscription_description() == SUBSCRIPTION_DESC_EN
        assert circ.subscription_email_placeholder() == SUBSCRIPTION_EMAIL_PLACEHOLDER_EN
        assert circ.subscription_button_text() == SUBSCRIPTION_BUTTON_EN
        assert circ.subscription_parts_are_unclipped()

    with allure.step("Switch to Arabic and inspect the same widget"):
        circ.switch_language()
        assert circ.document_direction() == "rtl"
        assert circ.is_subscription_widget_visible()
        assert _has_arabic(circ.subscription_title())
        assert _has_arabic(circ.subscription_description())
        assert _has_arabic(circ.subscription_email_placeholder())
        assert _has_arabic(circ.subscription_button_text())
        assert circ.subscription_parts_are_unclipped()
        assert circ.subscription_form_direction() == "rtl"
        # Subscribe button mirrored with the rest of the widget
        ar_widget = circ.subscription_widget_box()
        ar_button = circ.subscription_button_box()
        assert ar_button["x"] >= ar_widget["x"]
        assert ar_button["x"] + ar_button["width"] <= ar_widget["x"] + ar_widget["width"] + 1


# ===========================================================================
# 139644 — Light mode rendering
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Compatibility — light mode")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Circulars page renders correctly in light mode")
@allure.label("pbi", "129408")
@allure.label("testcase", "139644")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.pbi_129408
@pytest.mark.tc_139644
@pytest.mark.traceability("139644")
def test_circulars_renders_correctly_in_light_mode(page):
    circ = CircularsPage(page)

    with allure.step("Set the site appearance to light mode"):
        circ.open_circulars()
        # light is this site's default theme (data-theme on <html>)
        assert circ.theme() == "light"

    with allure.step("Open the public Circulars page in English"):
        assert circ.card_count() > 0
        assert circ.has_horizontal_scrollbar() is False

    with allure.step("Inspect the page background, header, filter bar and sidebar"):
        assert circ.page_background_style()["backgroundColor"] == WHITE
        assert circ.site_header_style()["backgroundColor"] == WHITE

        keyword_style = circ.keyword_input_style()
        assert keyword_style["backgroundColor"] == WHITE
        assert keyword_style["borderStyle"] == "solid"
        assert keyword_style["borderWidth"] == "1px"
        assert keyword_style["borderColor"] == INPUT_BORDER_LIGHT

        state_styles = circ.state_button_styles()
        assert len(state_styles) == len(STATE_LABELS_EN)
        for state_style in state_styles:
            assert _legible(state_style, WHITE)

    with allure.step("Inspect a circular card, its status badge and the subscription widget"):
        assert circ.card_surface_style()["backgroundColor"] == WHITE

        circ.select_state("Active Circulars")
        published = circ.badge_style()
        assert circ.card_badges()[0] == BADGE_PUBLISHED
        assert published == PUBLISHED_BADGE_LIGHT
        assert _legible(published, WHITE)

        circ.select_state("Archived Circulars")
        archived = circ.badge_style()
        assert circ.card_badges()[0] == BADGE_ARCHIVED
        assert _legible(archived, WHITE)
        assert archived != published

        sub_input = circ.subscription_input_style()
        sub_button = circ.subscription_button_style()
        assert _legible(sub_input, WHITE)
        assert _legible(sub_button, WHITE)


# ===========================================================================
# 139645 — Dark mode rendering (page + modal)
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Compatibility — dark mode")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Circulars page and modal render correctly in dark mode")
@allure.label("pbi", "129408")
@allure.label("testcase", "139645")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139645
@pytest.mark.traceability("139645")
def test_circulars_renders_correctly_in_dark_mode(page):
    circ = CircularsPage(page)

    with allure.step("Set the site appearance to dark mode"):
        circ.open_circulars()
        circ.enable_dark_mode()
        assert circ.theme() == "dark"

    with allure.step("Open the public Circulars page in English"):
        assert circ.card_count() > 0
        assert circ.has_horizontal_scrollbar() is False
        body_bg = circ.page_background_style()["backgroundColor"]
        assert body_bg == DARK_SURFACE
        # no unstyled light-mode remnants on the section's own surfaces
        assert circ.section_style()["backgroundColor"] != WHITE
        assert circ.card_surface_style()["backgroundColor"] != WHITE

    with allure.step("Inspect the header, filter bar, sidebar and cards"):
        assert circ.site_header_style()["backgroundColor"] == DARK_SURFACE
        assert circ.card_surface_style()["backgroundColor"] == DARK_SURFACE
        assert circ.keyword_input_style()["backgroundColor"] == DARK_SURFACE

        dark_surfaces = {
            "filter label": circ.filter_label_style(),
            "keyword input": circ.keyword_input_style(),
            "category select": circ.category_select_style(),
            "card title": circ.card_title_style(),
            "card metadata value": circ.card_cell_value_style(),
            "sidebar state filter": circ.state_button_styles()[0],
        }
        for name, style in dark_surfaces.items():
            assert _legible(style, DARK_SURFACE), f"illegible in dark mode: {name}"

    with allure.step("Open a circular with Read Circular and inspect the modal"):
        circ.open_modal_for_card(0)
        assert circ.is_modal_open()
        assert circ.modal_dialog_style()["backgroundColor"] == DARK_SURFACE
        for name, style in circ.modal_region_styles().items():
            assert _legible(style, DARK_SURFACE), f"illegible in dark modal: {name}"

        badge = circ.modal_badge_style()
        assert circ.modal_badge_text() == BADGE_PUBLISHED
        assert badge["color"] == PUBLISHED_BADGE_GREEN
        assert _legible(badge, DARK_SURFACE)
        assert badge["backgroundColor"] != PUBLISHED_BADGE_LIGHT["backgroundColor"]


# ===========================================================================
# 139655 — Desktop viewport (1920x1080)
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Compatibility — desktop viewport")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Circulars page renders correctly at desktop viewport width")
@allure.label("pbi", "129408")
@allure.label("testcase", "139655")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139655
@pytest.mark.traceability("139655")
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_circulars_renders_correctly_at_desktop_viewport(page):
    circ = CircularsPage(page)

    with allure.step("Set the browser viewport to 1920x1080 and open the page"):
        circ.open_circulars()
        assert page.viewport_size == {"width": 1920, "height": 1080}

    with allure.step("Page loads with no horizontal scrollbar"):
        assert circ.has_horizontal_scrollbar() is False

    with allure.step("Inspect the hero, filter bar and the two-column layout"):
        # four controls plus Reset and Search on ONE row
        assert len(circ.filter_field_boxes()) == 4
        assert circ.filter_field_row_count() == 1
        # Fields + actions measured in ONE atomic round-trip: sampling them
        # separately lets a layout shift between the two calls land straight
        # in the comparison below.
        geometry = circ.filter_row_geometry()
        fields = geometry["fields"]
        actions = geometry["actions"]
        row_top = min(f["y"] for f in fields)
        row_bottom = max(f["y"] + f["height"] for f in fields)
        # The case claims the four controls plus Reset and Search render on
        # ONE row — it says nothing about pixel containment or alignment. So
        # assert the actions group SHARES the field row: its box overlaps the
        # field-row band by at least half its own height. A group that wrapped
        # onto a second row sits wholly below `row_bottom`, giving zero or
        # negative overlap, so this still fails outright on a real break.
        # (Observation, deliberately NOT asserted: at this viewport the
        # actions group measures ~4px below the inputs' bottom edge despite
        # `align-items: flex-end` and matching 44px control heights — an open
        # design-drift note, outside this case's contract.)
        overlap = min(actions["y"] + actions["height"], row_bottom) - max(actions["y"], row_top)
        assert overlap >= actions["height"] / 2, (
            f"Reset/Search does not share the filter row: actions "
            f"{actions['y']}..{actions['y'] + actions['height']} vs field row "
            f"{row_top}..{row_bottom} (overlap {overlap}px)"
        )
        assert actions["x"] > max(f["x"] for f in fields)
        assert circ.is_desktop_nav_visible()
        assert circ.is_mobile_hamburger_visible() is False

        # two columns — sidebar BESIDE the main listing, not stacked
        sidebar = circ.sidebar_box()
        main = circ.main_column_box()
        assert sidebar["x"] + sidebar["width"] <= main["x"] + 1
        assert abs(sidebar["y"] - main["y"]) <= 4

    with allure.step("Inspect a card and open the modal"):
        card = circ.card_box()
        assert abs(card["width"] - main["width"]) <= 2  # full-width row
        assert circ.card_badges()[0].strip() != ""
        assert len(circ.card_meta_labels()) == 2
        assert circ.card_action_count() == 2

        circ.open_modal_for_card(0)
        metrics = circ.modal_metrics()
        modal_centre = metrics["x"] + metrics["width"] / 2
        assert abs(modal_centre - metrics["viewportWidth"] / 2) <= 2
        assert metrics["scrollHeight"] <= metrics["clientHeight"] + 1  # nothing clipped


# ===========================================================================
# 139656 — Tablet viewport (768x1024)
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Compatibility — tablet viewport")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Circulars page renders correctly at tablet viewport width")
@allure.label("pbi", "129408")
@allure.label("testcase", "139656")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139656
@pytest.mark.traceability("139656")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_circulars_renders_correctly_at_tablet_viewport(page):
    circ = CircularsPage(page)

    with allure.step("Set the browser viewport to 768x1024 and open the page"):
        circ.open_circulars()
        assert page.viewport_size == {"width": 768, "height": 1024}

    with allure.step("Page loads with no horizontal scrollbar and no clipped content"):
        assert circ.has_horizontal_scrollbar() is False
        assert circ.first_card_parts_within_card()

    with allure.step("Inspect the filter bar and the sidebar"):
        fields = circ.filter_field_boxes()
        assert len(fields) == 4
        # controls WRAP onto more than one row rather than shrinking
        assert circ.filter_field_row_count() > 1
        assert all(f["width"] >= 200 for f in fields)

        sidebar = circ.sidebar_box()
        main = circ.main_column_box()
        assert sidebar is not None and sidebar["width"] > 0 and sidebar["height"] > 0
        assert circ.is_sidebar_visible()  # did not disappear
        assert circ.are_state_filters_reachable()
        # the sidebar either narrows or moves above the listing
        assert sidebar["width"] < main["width"] or sidebar["y"] < main["y"]

    with allure.step("Inspect the cards and open the modal"):
        assert circ.card_count() > 0
        assert circ.first_card_parts_within_card()
        circ.open_modal_for_card(0)
        metrics = circ.modal_metrics()
        assert metrics["width"] <= metrics["viewportWidth"]
        assert metrics["height"] <= metrics["viewportHeight"]
        # content scrollable rather than cut off
        assert metrics["overflowY"] in ("auto", "scroll")
        assert metrics["scrollHeight"] > metrics["clientHeight"]


# ===========================================================================
# 139657 — Mobile viewport (390x844)
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Compatibility — mobile viewport")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Circulars page renders correctly at mobile viewport width")
@allure.label("pbi", "129408")
@allure.label("testcase", "139657")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139657
@pytest.mark.traceability("139657")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_circulars_renders_correctly_at_mobile_viewport(page):
    circ = CircularsPage(page)

    with allure.step("Set the browser viewport to 390x844 and open the page"):
        circ.open_circulars()
        assert page.viewport_size == {"width": 390, "height": 844}

    with allure.step("Page loads with no horizontal scrollbar and no overflowing text"):
        assert circ.has_horizontal_scrollbar() is False
        assert circ.first_card_parts_within_card()
        # the desktop nav is replaced by the mobile menu at this width
        assert circ.is_mobile_hamburger_visible()
        assert circ.is_desktop_nav_visible() is False

    with allure.step("Inspect the hero, filter bar and sidebar filters"):
        hero_copy = circ.hero_copy_box()
        hero_art = circ.hero_art_box()
        assert abs(hero_copy["x"] - hero_art["x"]) <= 2          # stacked, not side by side
        assert hero_art["y"] >= hero_copy["y"] + hero_copy["height"] - 2

        assert circ.filter_field_column_count() == 1     # single column
        assert circ.filter_field_row_count() == 4

        assert circ.are_state_filters_reachable()
        assert circ.is_subscription_widget_visible()

    with allure.step("Inspect the cards, open the modal and tap Download"):
        rows = circ.card_element_rows()
        assert rows["meta"]["y"] + rows["meta"]["height"] <= rows["actions"]["y"] + 1

        circ.open_modal_for_card(0)
        metrics = circ.modal_metrics()
        assert metrics["width"] >= metrics["viewportWidth"] * 0.85
        assert metrics["height"] >= metrics["viewportHeight"] * 0.85
        assert metrics["overflowY"] in ("auto", "scroll")
        assert metrics["scrollHeight"] > metrics["clientHeight"]

        tap_target = circ.modal_download_tap_target()
        assert tap_target["width"] > 0 and tap_target["height"] > 0
        delivery = circ.trigger_modal_download()
        assert delivery["status"] == 200
        assert "attachment" in delivery["content_disposition"]
        assert delivery["content_type"].strip() != ""


# ===========================================================================
# 139578 — Card badge: Published for Active/Urgent, Archived for archived
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("Circulars")
@allure.story("Card status badge")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The card badge renders Published for Active and Urgent circulars and Archived for archived ones")
@allure.label("pbi", "129408")
@allure.label("testcase", "139578")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129408
@pytest.mark.tc_139578
@pytest.mark.traceability("139578")
def test_circulars_card_badge_reflects_circular_status(page):
    circ = CircularsPage(page)

    with allure.step("Open the public Circulars page in English"):
        circ.open_circulars()
        assert circ.card_count() > 0

    with allure.step("Locate a circular whose Status is Active and inspect its badge"):
        circ.select_state("Active Circulars")
        assert circ.card_count() > 0
        assert all(badge == BADGE_PUBLISHED for badge in circ.card_badges())
        active_badge = circ.badge_style()
        assert active_badge["color"] == PUBLISHED_BADGE_GREEN

    with allure.step("Locate a circular whose Status is Urgent and inspect its badge"):
        circ.select_state("Urgent Circulars")
        assert circ.card_count() > 0
        assert all(badge == BADGE_PUBLISHED for badge in circ.card_badges())
        urgent_badge = circ.badge_style()
        assert urgent_badge["color"] == PUBLISHED_BADGE_GREEN
        assert urgent_badge == active_badge  # identical to the Active badge

    with allure.step("Switch to the Archived filter and inspect an archived circular's badge"):
        circ.select_state("Archived Circulars")
        assert circ.card_count() > 0
        assert all(badge == BADGE_ARCHIVED for badge in circ.card_badges())
        archived_badge = circ.badge_style()
        assert archived_badge["color"] != PUBLISHED_BADGE_GREEN
        assert archived_badge != active_badge  # visually distinct from the green badge

"""
web/tests/b2b_matchmaking/test_b2b_matchmaking_web.py — Web-platform cases for
PBI 129409 (QC-SVC-012 — B2B Matchmaking), sourced from the approved Azure
DevOps batch handed off by the QA Manager. Control_Panel-tagged cases for this
PBI are explicitly out of scope for this batch and are NOT touched here.

Scripted here (28 of the 30 handed off):
  Functional-High: 139793, 139794, 139795, 139796, 139797, 139798, 139802,
                   139804, 139805, 139806
  UI:              139824, 139825
  Compatibility:   139828, 139829, 139830, 139833, 139834
  Functional-Low:  139693, 139696, 139698, 139699, 139700, 139757, 139762,
                   139765, 139777, 139780, 139783

NOT scripted — BLOCKED, see the batch report:
  139800 "Load More appends the next page of companies and respects the active
         filters" and
  139803 "The popup shows the company matching the card that was clicked"
         (its step 2 requires "Click Load More twice so several pages of cards
         are rendered").
  Both need Load More. Measured live on qcdev 2026-09-17:
  `GET /o/qc-b2b-matchmaking/companies?page=1&pageSize=12` returns
  `totalCount: 3, totalPages: 1`, and the fragment's own
  `data-qc-b2b-page-size` is 12 — so `[data-qc-b2b-more]` renders with the
  `hidden` attribute and Load More is NEVER offered in this environment.
  The precondition those cases name does not exist here; it is not a locator
  problem and not something to soften into a different assertion, so it is
  left for the QA Manager to decide (seed 13+ approved companies, or re-scope).
  Both become scriptable unchanged the moment the directory holds more
  companies than one page.

Sub-clauses of otherwise-scripted cases that are BLOCKED by the same data gap
and are therefore NOT asserted (called out again in the test that owns them):
  * 139793 / 139824 — "…above a Load More button" / "above a full-width Load
    More button". With 3 companies against a page size of 12 the control is
    correctly hidden, so there is no rendered Load More to place the grid
    above.
  * 139796 step 4 — "The grid narrows AGAIN". The three approved companies
    give Qatar=2 -> Qatar+Energy=1, so no name fragment added on top can
    reduce the set below 1. Steps 2 and 3 (strict narrowing 3 -> 2 -> 1) and
    step 4's "every rendered card matches all three criteria at once" ARE
    asserted.
  * 139830 step 4 — "…CAPTCHA … reachable and operable by touch". The Contact
    webform's `[data-qc-recaptcha-field]` renders `hidden` (reCAPTCHA
    Enterprise SCORE key — see below), so there is no CAPTCHA control for a
    visitor to reach or operate. Its PRESENCE on the form is asserted; the
    submit-through-CAPTCHA portion is reported blocked rather than faked.

--- reCAPTCHA (nothing here solves, stubs or bypasses one) ---

reCAPTCHA Enterprise is loaded site-wide. Re-measured live 2026-09-17 (qcdev,
at 1920x1080 and 768x1024): **BOTH** forms' CAPTCHA fields are `hidden` (score
key). The Registration form's field carries a "Security Check *" label but the
element itself is `<div class="qc-field" data-qc-recaptcha-field hidden>`
inside `[data-qc-b2breg-form]` — `display: none`, null `offsetParent`, 0x0
rect. An earlier revision of this docstring claimed that field was "real,
visible"; it is not, and that wrong premise is what made
`registration_fields_are_untruncated()` score a deliberately hidden field as a
truncated one (139829). Both forms validate
their own required fields CLIENT-SIDE FIRST — submitting with a blank required
field paints the inline `[data-qc-e="<field>"]` message and never reaches the
CAPTCHA or the network. That was confirmed by driving each form live, which is
why 139762 / 139765 / 139777 / 139780 / 139783 are scripted in full rather
than reported blocked.

--- Live content baseline (qcdev, 2026-09-17) ---

Three approved companies, and nothing else:

  Helios Solar Qatar        | Qatar   | Energy    | Yousef Al-Mannai / CEO      | QC-9087  | Qatar Chamber | Business expansion
  Doha Logistics Hub        | Qatar   | Logistics | Fatima Al-Kuwari / Director of Trade | QC-4412 | Qatar Chamber | Import / export
  Nordwind Renewables GmbH  | Germany | Energy    | Katrin Vogel / Head of Partnerships  | HH-88213 | IHK Hamburg  | Investments

Concrete data below mirrors each case's own wording where the case names a
value ('zzzqaqa_nomatch', 'All Countries', 'All Industries', the five
registration section names, the Email/Phone options), and is otherwise read
from that live content.

No `time.sleep()`, no `networkidle` (the chatbot widget polls this site
continuously) — every wait in the Page Object is on a real outcome.
"""

import allure
import pytest

from config.settings import web_url
from web.pages.b2b_matchmaking.b2b_matchmaking_page import (
    B2B_FRIENDLY_PATH,
    HOME_PATH,
    REGISTRATION_PATH,
    SERVICES_PATH,
    B2bMatchmakingPage,
)

# ---------------------------------------------------------------------------
# Concrete data — mirrored from the QA cases + the live qcdev content
# ---------------------------------------------------------------------------
HERO_EYEBROW_EN = "International Business Platform"
HERO_TITLE_EN = "B2B Connect"
CTA_LABEL_EN = "Register Your Company"

SEARCH_LABELS_EN = ["Company Name", "Business Offer From", "Industry Type"]
ALL_COUNTRIES = "All Countries"
ALL_INDUSTRIES = "All Industries"
SEARCH_BUTTON_TEXT_EN = "Search"

BREADCRUMB_LABELS_EN = ["Home", "Services"]
BREADCRUMB_PLACEHOLDER_DEFECT_TEXT = "Hcvxcxvcome"

NO_MATCH_FRAGMENT = "zzzqaqa_nomatch"

# The three approved companies on qcdev.
COMPANY_HELIOS = "Helios Solar Qatar"
COMPANY_DOHA = "Doha Logistics Hub"
COMPANY_NORDWIND = "Nordwind Renewables GmbH"
ALL_COMPANY_NAMES = [COMPANY_HELIOS, COMPANY_DOHA, COMPANY_NORDWIND]
APPROVED_COMPANY_COUNT = 3

COUNTRY_QATAR = "Qatar"
COUNTRY_GERMANY = "Germany"
INDUSTRY_ENERGY = "Energy"
INDUSTRY_LOGISTICS = "Logistics"

# Qatar + Energy is the one country/industry pair that co-occurs, and 'Solar'
# is a fragment of the single company in that subset (139796).
NAME_FRAGMENT_IN_SUBSET = "Solar"
# A MIDDLE fragment of 'Doha Logistics Hub' — neither a prefix nor the whole
# name, which is exactly what 139693 asks for.
MIDDLE_NAME_FRAGMENT = "ogistics"

BADGE_APPROVED_EN = "Approved"

# Company Details popup — the regions 139802 enumerates.
DETAILS_FIELD_TERMS_EN = [
    "Business Offer From",
    "Contact Person",
    "Designation",
    "Registered Chamber",
    "Looking For",
    "Organization Membership Number",
]
DETAILS_SECTION_HEADS_EN = ["Summary of Offer", "Potential Partners", "Company Description"]

# Contact Company webform.
CONTACT_METHOD_OPTIONS_EN = ["Email", "Phone"]
CONTACT_METHOD_EMAIL = "email"
CONTACT_METHOD_PHONE = "phone"
CONTACT_FORM_DATA = {
    "firstName": "Aisha",
    "lastName": "Rahman",
    "industryType": "logistics",
    "whatAreYouLookingFor": "importExport",
    "commentsOrQuestions": "Please share your export capacity for Q1 2027.",
}
CONTACT_EMAIL_BRANCH_DATA = {
    "email": "aisha.rahman@example.com",
    "confirmEmail": "aisha.rahman@example.com",
}
CONTACT_PHONE_BRANCH_DATA = {"phone": "+974 5551 2345"}

# B2B Registration form — the five sections 139806 names, and the mandatory
# values 139777 / 139780 / 139783 complete around the one they leave blank.
REGISTRATION_SECTIONS_EN = [
    "Company Information",
    "Chamber Details",
    "Contact Person",
    "Business Details",
    "Media & Documents",
]
REGISTRATION_FORM_DATA = {
    "companyName": "Meridian Trading WLL",
    "businessOfferFrom": "Qatar",
    "industryType": "logistics",
    "whatAreYouLookingFor": "importExport",
    "companyProfileUrl": "https://meridian-trading.example.com",
    "registeredChamberName": "Qatar Chamber",
    "chamberEmailForVerification": "verify@qatarchamber.example.com",
    "contactPerson": "Noor Al-Sulaiti",
    "email": "noor.alsulaiti@example.com",
    "mobileNumber": "+974 5551 9876",
    "summaryOfOffer": "Bonded warehousing and regional freight forwarding.",
    "companyDescription": "Meridian Trading moves industrial cargo across the GCC.",
    "potentialPartners": "Industrial exporters and port operators.",
}

# Live design tokens (computed styles read off qcdev 2026-09-17).
WHITE = "rgb(255, 255, 255)"
MAROON = "rgb(145, 23, 49)"
DARK_SURFACE = "rgb(29, 29, 27)"
TRANSPARENT = ("rgba(0, 0, 0, 0)", "transparent")
CARD_RADIUS_DESIGNED = "10px"
HERO_BANNER_DESIGNED = {"width": 424, "height": 322}


# ---------------------------------------------------------------------------
# Small pure helpers — no locators, no Playwright; the assertion intent stays
# in the test bodies below.
# ---------------------------------------------------------------------------
def _has_arabic(text: str) -> bool:
    """True when the string contains at least one Arabic-script character
    (U+0600..U+06FF). Deliberately NOT "contains no Latin characters": live
    Arabic content legitimately keeps Latin runs inside translated fields
    (a membership number, a proper noun). A field left untranslated carries
    no Arabic at all, which is what this catches."""
    return any(0x0600 <= ord(ch) <= 0x06FF for ch in text or "")


def _legible(style: dict, fallback_bg: str) -> bool:
    """True when a computed text colour genuinely differs from the surface it
    sits on — falling back to the container's background when the element's
    own background is transparent."""
    bg = style.get("backgroundColor", fallback_bg)
    if bg in TRANSPARENT:
        bg = fallback_bg
    color = style.get("color")
    return bool(color) and color not in TRANSPARENT and color != bg


def _is_dark(color: str) -> bool:
    """True when an rgb()/rgba() colour is a dark surface (mean channel below
    mid-grey) — used by the dark-mode case, which asserts the palette flipped
    rather than merely that something is visible."""
    if not color or color in TRANSPARENT:
        return False
    nums = [int(n) for n in "".join(c if c.isdigit() else " " for c in color).split()[:3]]
    return len(nums) == 3 and sum(nums) / 3 < 128


def _boxes_overlap(a: dict, b: dict, tolerance: int = 2) -> bool:
    return not (
        a["x"] + a["width"] <= b["x"] + tolerance
        or b["x"] + b["width"] <= a["x"] + tolerance
        or a["y"] + a["height"] <= b["y"] + tolerance
        or b["y"] + b["height"] <= a["y"] + tolerance
    )


def _effective_alignment(style: dict) -> str:
    """Resolve `text-align: start` against the element's own direction, so an
    alignment assertion reads what the user sees rather than a CSS keyword."""
    align = style["textAlign"]
    if align in ("start", "auto", ""):
        return "left" if style["direction"] == "ltr" else "right"
    if align == "end":
        return "right" if style["direction"] == "ltr" else "left"
    return align


# ===========================================================================
# 139793 — Reach B2B Matchmaking from the main menu and see hero, search, grid
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Navigation and page composition")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A visitor reaches the B2B Matchmaking page from the main menu and sees the hero, search bar and company grid")
@allure.label("pbi", "129409")
@allure.label("testcase", "139793")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139793
@pytest.mark.traceability("139793")
def test_b2b_reached_from_main_menu_shows_hero_search_and_grid(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the Qatar Chamber website in English"):
        b2b.open_home()
        assert b2b.is_desktop_nav_visible()

    with allure.step("Click 'Our Services' in the main menu"):
        # The live top-level "Our Services" item is an <a href> — a click
        # navigates instead of expanding, so hover is the interaction that
        # opens the dropdown on desktop (see hover_our_services_menu()).
        assert b2b.is_our_services_submenu_expanded() is False, (
            "the Our Services submenu is already expanded before any hover — items visible: "
            f"{b2b.our_services_submenu_labels()}"
        )
        b2b.hover_our_services_menu()
        assert b2b.is_our_services_submenu_expanded() is True, (
            "the Our Services submenu did not expand on hover — items visible: "
            f"{b2b.our_services_submenu_labels()}"
        )

    with allure.step("Click 'B2B Matchmaking' in the dropdown"):
        assert b2b.b2b_matchmaking_link_count_in_our_services() == 1, (
            "'B2B Matchmaking' is not offered in the 'Our Services' dropdown. "
            f"That dropdown offers: {b2b.our_services_submenu_labels()}"
        )
        assert b2b.b2b_matchmaking_link_href_in_our_services() == B2B_FRIENDLY_PATH
        b2b.click_b2b_matchmaking_in_our_services()
        assert b2b.current_url() == web_url(B2B_FRIENDLY_PATH)

    with allure.step("Observe the page from hero to footer"):
        assert b2b.breadcrumb_labels() == BREADCRUMB_LABELS_EN
        hero = b2b.hero_style()
        assert hero["backgroundColor"] not in TRANSPARENT and _is_dark(hero["backgroundColor"])
        assert b2b.hero_eyebrow_text() == HERO_EYEBROW_EN
        assert b2b.hero_title_text() == HERO_TITLE_EN
        assert b2b.hero_lede_text() != ""
        assert b2b.cta_label_text() == CTA_LABEL_EN
        assert b2b.cta_icon_count() == 1

        geometry = b2b.hero_geometry()
        assert geometry["copy"]["x"] + geometry["copy"]["width"] <= geometry["art"]["x"] + 2, (
            "the CTA/hero copy block is not beside the hero banner image"
        )

        assert b2b.search_field_labels() == SEARCH_LABELS_EN
        assert b2b.is_reset_control_visible()
        assert b2b.search_button_text() == SEARCH_BUTTON_TEXT_EN

        assert b2b.card_count() > 0
        assert b2b.grid_column_count() == 3
        # "…above a Load More button" is NOT asserted: with 3 approved
        # companies against a page size of 12 the control is correctly hidden
        # and there is nothing rendered to sit below the grid. See the module
        # docstring's blocked-sub-clause list.


# ===========================================================================
# 139794 — Breadcrumb links navigate to their targets
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The breadcrumb links on the B2B Matchmaking page navigate to their targets")
@allure.label("pbi", "129409")
@allure.label("testcase", "139794")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139794
@pytest.mark.traceability("139794")
def test_b2b_breadcrumb_links_navigate_to_their_targets(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.is_hero_visible()

    with allure.step("Inspect the breadcrumb in the hero"):
        assert b2b.breadcrumb_home_icon_count() == 1
        assert b2b.breadcrumb_labels() == BREADCRUMB_LABELS_EN
        assert b2b.breadcrumb_separator_count() == 1
        assert b2b.breadcrumb_chevron_count() == 1
        assert BREADCRUMB_PLACEHOLDER_DEFECT_TEXT not in b2b.breadcrumb_text()

    with allure.step("Click the 'Home' breadcrumb link"):
        b2b.click_breadcrumb_home()
        assert b2b.current_url() == web_url(HOME_PATH)

    with allure.step("Navigate back and click the 'Services' breadcrumb link"):
        b2b.go_back_to_b2b_matchmaking()
        b2b.click_breadcrumb_services()
        assert b2b.current_url() == web_url(SERVICES_PATH)


# ===========================================================================
# 139795 — Language toggle switches page, search bar and cards EN <-> AR
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Bilingual")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The language toggle switches the page, the search bar and the cards between English and Arabic")
@allure.label("pbi", "129409")
@allure.label("testcase", "139795")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.rtl
@pytest.mark.arabic
@pytest.mark.pbi_129409
@pytest.mark.tc_139795
@pytest.mark.traceability("139795")
def test_b2b_language_toggle_switches_page_search_bar_and_cards(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.document_direction() == "ltr"
        english = {
            "eyebrow": b2b.hero_eyebrow_text(),
            "title": b2b.hero_title_text(),
            "lede": b2b.hero_lede_text(),
            "cta": b2b.cta_label_text(),
            "labels": b2b.search_field_labels(),
            "placeholder": b2b.company_name_placeholder(),
            "country_all": b2b.country_selected_label(),
            "industry_all": b2b.industry_selected_label(),
            "search_button": b2b.search_button_text(),
            "card_name": b2b.card_names()[0],
            "card_industry": b2b.card_industries()[0],
            "card_country": b2b.card_countries()[0],
            "card_badge": b2b.card_badges()[0],
            "card_date": b2b.card_dates()[0],
        }
        english_geometry = b2b.search_row_geometry()

    with allure.step("Click the AR language toggle in the header"):
        assert b2b.language_switcher_label() == "AR"
        b2b.switch_language()
        assert b2b.document_language().startswith("ar")

    with allure.step("Inspect the hero, the search bar and the grid"):
        assert b2b.document_direction() == "rtl"
        arabic = {
            "eyebrow": b2b.hero_eyebrow_text(),
            "title": b2b.hero_title_text(),
            "lede": b2b.hero_lede_text(),
            "cta": b2b.cta_label_text(),
            "labels": b2b.search_field_labels(),
            "placeholder": b2b.company_name_placeholder(),
            "country_all": b2b.country_selected_label(),
            "industry_all": b2b.industry_selected_label(),
            "search_button": b2b.search_button_text(),
            "card_name": b2b.card_names()[0],
            "card_industry": b2b.card_industries()[0],
            "card_country": b2b.card_countries()[0],
            "card_badge": b2b.card_badges()[0],
            "card_date": b2b.card_dates()[0],
        }
        for key in ("eyebrow", "title", "lede", "cta", "placeholder", "country_all",
                    "industry_all", "search_button"):
            assert _has_arabic(arabic[key]), f"{key} did not render in Arabic: {arabic[key]!r}"
            assert arabic[key] != english[key], f"{key} kept its English value"
        for index, label in enumerate(arabic["labels"]):
            assert _has_arabic(label), f"search label {index} not Arabic: {label!r}"
            assert label != english["labels"][index]
        # `card_name` is deliberately NOT in the Arabic loop below. The
        # product stores exactly ONE `companyName` with no locale variant —
        # the API returns 'Helios Solar Qatar' identically under ar_SA — and a
        # company's trade name is a proper noun, not a translated field. It is
        # asserted as an IDENTITY check instead: the same name on both
        # locales. (`industryTypeLabel` and `whatAreYouLookingForLabel` ARE
        # localised, and stay asserted below.)
        assert arabic["card_name"] == english["card_name"], (
            "the company card's trade name is not identical across locales: "
            f"EN {english['card_name']!r} vs AR {arabic['card_name']!r}"
        )
        # `card_country` STAYS in the loop on purpose. Country IS a controlled
        # vocabulary the page localises elsewhere (the filter's 'All Countries'
        # renders in Arabic), yet the card still prints 'QATAR'/'GERMANY' in
        # English under ar_SA — measured live 2026-09-17. That is a real
        # localisation gap; this assertion is expected to fail until it is
        # fixed and must not be relaxed.
        for key in ("card_industry", "card_country", "card_badge", "card_date"):
            assert _has_arabic(arabic[key]), f"card {key} did not render in Arabic: {arabic[key]!r}"

        assert b2b.search_form_direction() == "rtl"
        arabic_geometry = b2b.search_row_geometry()
        # Mirrored: the field that sat leftmost in English sits rightmost in
        # Arabic, and the Search/Reset group swaps to the opposite side.
        assert english_geometry["fields"][0]["x"] < english_geometry["actions"]["x"]
        assert arabic_geometry["fields"][0]["x"] > arabic_geometry["actions"]["x"]

    with allure.step("Open a company card and click the EN toggle to switch back"):
        b2b.open_card(0)
        assert b2b.details_dialog_direction() == "rtl"
        arabic_terms = b2b.details_field_terms()
        assert arabic_terms, "the Company Details popup rendered no field labels"
        for term in arabic_terms:
            assert _has_arabic(term), f"popup label not Arabic: {term!r}"
        assert _has_arabic(b2b.details_heading())
        # The popup is a modal (aria-modal, with a backdrop): the header's
        # language switcher is not reachable while it is open, so it is closed
        # first. Mechanical only — no expectation of the case is relaxed.
        b2b.close_details_popup()

        assert b2b.language_switcher_label() == "EN"
        b2b.switch_language()
        assert b2b.document_direction() == "ltr"
        assert b2b.hero_title_text() == english["title"]


# ===========================================================================
# 139796 — Multiple search filters combine with AND
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Filters — combination")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Multiple B2B search filters combine with AND rather than replacing one another")
@allure.label("pbi", "129409")
@allure.label("testcase", "139796")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139796
@pytest.mark.traceability("139796")
def test_b2b_multiple_filters_combine_with_and(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        full_count = b2b.card_count()
        assert full_count == APPROVED_COMPANY_COUNT

    with allure.step("Select a Business Offer From country and Search"):
        b2b.select_country(COUNTRY_QATAR).click_search()
        country_names = b2b.card_names()
        country_count = len(country_names)
        assert country_count < full_count
        assert all(c == COUNTRY_QATAR.upper() for c in b2b.card_countries())

    with allure.step("Without resetting, also select an Industry Type and Search"):
        b2b.select_industry(INDUSTRY_ENERGY).click_search()
        combined_names = b2b.card_names()
        assert len(combined_names) < country_count, (
            "adding the Industry Type filter did not narrow the country result"
        )
        assert len(combined_names) < full_count, "the grid reverted to the whole grid"
        assert all(i == INDUSTRY_ENERGY for i in b2b.card_industries())
        assert all(c == COUNTRY_QATAR.upper() for c in b2b.card_countries())

    with allure.step("Also type a company-name fragment and Search"):
        b2b.set_company_name(NAME_FRAGMENT_IN_SUBSET).click_search()
        # Step 4's "narrows again" is NOT asserted — with three approved
        # companies the Qatar+Energy subset is already a single card, so no
        # fragment can reduce it further. See the module docstring.
        final_names = b2b.card_names()
        assert final_names, "the three-filter search returned nothing"
        assert set(final_names) <= set(combined_names)
        for index, name in enumerate(final_names):
            assert NAME_FRAGMENT_IN_SUBSET.lower() in name.lower()
            assert b2b.card_industries()[index] == INDUSTRY_ENERGY
            assert b2b.card_countries()[index] == COUNTRY_QATAR.upper()


# ===========================================================================
# 139797 — Reset clears every search filter and restores the full grid
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Filters — reset")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Reset clears every B2B search filter and restores the full approved grid")
@allure.label("pbi", "129409")
@allure.label("testcase", "139797")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139797
@pytest.mark.traceability("139797")
def test_b2b_reset_clears_filters_and_restores_full_grid(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        full_names = b2b.card_names()
        assert len(full_names) == APPROVED_COMPANY_COUNT

    with allure.step("Set a name fragment, a country and an industry, then Search"):
        b2b.set_company_name(NAME_FRAGMENT_IN_SUBSET)
        b2b.select_country(COUNTRY_QATAR)
        b2b.select_industry(INDUSTRY_ENERGY)
        b2b.click_search()
        assert b2b.card_count() < len(full_names)

    with allure.step("Click the reset control"):
        b2b.click_reset()

    with allure.step("Inspect the three filter controls"):
        assert b2b.company_name_value() == ""
        assert b2b.country_selected_label() == ALL_COUNTRIES
        assert b2b.industry_selected_label() == ALL_INDUSTRIES

    with allure.step("Count the rendered cards"):
        assert b2b.card_names() == full_names


# ===========================================================================
# 139798 — A search with no matches shows the empty-state message
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Filters — empty state")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A B2B search with no matches shows the empty-state message rather than a blank region")
@allure.label("pbi", "129409")
@allure.label("testcase", "139798")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139798
@pytest.mark.traceability("139798")
def test_b2b_search_with_no_matches_shows_empty_state(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        full_names = b2b.card_names()
        assert full_names

    with allure.step(f"Type '{NO_MATCH_FRAGMENT}' into Company Name and Search"):
        b2b.set_company_name(NO_MATCH_FRAGMENT).click_search()

    with allure.step("Inspect the results area"):
        message = b2b.status_text()
        assert message, "the results area rendered no empty-state message"
        assert b2b.card_count() == 0, "an unfiltered or broken card frame is still rendered"
        assert NO_MATCH_FRAGMENT not in message or len(message) > len(NO_MATCH_FRAGMENT)
        assert b2b.is_load_more_offered() is False, (
            f"Load More is offered on this result set ({b2b.card_count()} cards, "
            f"page size {b2b.page_size()})"
        )

    with allure.step("Click Reset and inspect the grid again"):
        b2b.click_reset()
        assert b2b.card_names() == full_names


# ===========================================================================
# 139802 — Clicking a company card opens the popup without a page reload
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Company Details popup")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Clicking a company card opens the Company Details popup without a page reload")
@allure.label("pbi", "129409")
@allure.label("testcase", "139802")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139802
@pytest.mark.traceability("139802")
def test_b2b_card_click_opens_details_popup_without_reload(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.card_count() > 0

    with allure.step("Record the browser navigation state and the name on one card"):
        url_before = b2b.current_url()
        card_name = b2b.card_names()[0]
        card_industry = b2b.card_industries()[0]
        # A same-document marker: it only survives while this document lives,
        # so a reload (even to the same URL) would wipe it.
        b2b.plant_no_reload_sentinel("139802")

    with allure.step("Click that card"):
        b2b.open_card(0)
        assert b2b.is_details_popup_open() is True, (
            f"the Company Details popup did not open — {b2b.card_count()} cards on "
            f"{b2b.current_url()}"
        )
        assert b2b.current_url() == url_before
        assert b2b.no_reload_sentinel() == "139802", "the page reloaded when the card was clicked"

    with allure.step("Inspect every region of the popup"):
        assert b2b.is_details_logo_rendered() is True, (
            f"the popup rendered no company logo (popup open={b2b.is_details_popup_open()})"
        )
        assert b2b.details_company_name() == card_name
        assert b2b.details_industry() == card_industry

        fields = b2b.details_fields()
        for term in DETAILS_FIELD_TERMS_EN:
            assert term in fields, f"the popup does not show '{term}'"
            assert fields[term] != "", f"'{term}' rendered empty"

        sections = b2b.details_sections()
        for heading in DETAILS_SECTION_HEADS_EN:
            assert heading in sections, f"the popup does not show '{heading}'"
            assert sections[heading] != "", f"'{heading}' rendered empty"

        profile_links = [
            (label, href)
            for label, href in b2b.details_hyperlinks()
            if href and href.startswith("http")
        ]
        assert profile_links, (
            "the popup shows no company profile hyperlink — it rendered these "
            f"links: {b2b.details_hyperlinks()}"
        )

        assert b2b.is_details_close_action_visible() is True, (
            f"the popup shows no Close action (popup open={b2b.is_details_popup_open()})"
        )
        assert b2b.is_details_contact_action_visible() is True, (
            f"the popup shows no Contact action (popup open={b2b.is_details_popup_open()})"
        )


# ===========================================================================
# 139804 — Closing the popup returns to the grid with filters and scroll intact
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Company Details popup")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Closing the Company Details popup returns to the grid with its filters and scroll position intact")
@allure.label("pbi", "129409")
@allure.label("testcase", "139804")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139804
@pytest.mark.traceability("139804")
def test_b2b_closing_popup_keeps_filters_and_scroll_position(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Apply an Industry Type filter and scroll down the grid"):
        b2b.open_b2b_matchmaking()
        b2b.select_industry(INDUSTRY_ENERGY).click_search()
        filtered_names = b2b.card_names()
        assert filtered_names
        b2b.scroll_to(900)
        scroll_before = b2b.scroll_offset()
        b2b.plant_no_reload_sentinel("139804")

    with allure.step("Click a card to open the popup"):
        b2b.open_card(0)
        assert b2b.is_details_popup_open() is True, (
            f"the Company Details popup did not open on {b2b.current_url()}"
        )

    with allure.step("Click Close"):
        b2b.close_details_popup()
        assert b2b.is_details_popup_open() is False, (
            f"the Company Details popup is still open after Close on {b2b.current_url()}"
        )

    with allure.step("Inspect the grid"):
        assert b2b.no_reload_sentinel() == "139804", "closing the popup reloaded the page"
        assert b2b.industry_selected_label() == INDUSTRY_ENERGY
        assert b2b.card_names() == filtered_names
        assert abs(b2b.scroll_offset() - scroll_before) <= 2, (
            f"the grid moved: scrolled to {scroll_before}, returned at {b2b.scroll_offset()}"
        )


# ===========================================================================
# 139805 — Contact opens the webform with the company pre-filled
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Contact Company webform")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Contact action in the popup opens the webform with the company pre-filled and read-only")
@allure.label("pbi", "129409")
@allure.label("testcase", "139805")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139805
@pytest.mark.traceability("139805")
def test_b2b_contact_action_opens_webform_with_company_prefilled(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.card_count() > 0

    with allure.step("Click a company card and record its name and contact person"):
        b2b.open_card(0)
        company_name = b2b.details_company_name()
        contact_person = b2b.details_fields()["Contact Person"]
        assert company_name and contact_person

    with allure.step("Click Contact in the popup"):
        b2b.open_contact_form()
        assert b2b.is_contact_form_open() is True, (
            "the Contact webform did not open from the popup (details popup open="
            f"{b2b.is_details_popup_open()})"
        )

    with allure.step("Inspect the first two fields of the webform"):
        assert b2b.contact_company_name_shown() == company_name
        assert b2b.contact_company_contact_shown() == contact_person
        # Read-only in the strongest sense a visitor can observe: the panel
        # exposes no control they can type into at all.
        assert b2b.contact_company_panel_editable_count() == 0, (
            "the pre-filled company values expose an editable control: "
            f"{b2b.contact_company_panel_control_tags()}"
        )


# ===========================================================================
# 139806 — The Register Your Company CTA opens the B2B Registration form
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("B2B Registration form")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Register Your Company CTA opens the B2B Registration form with its five sections")
@allure.label("pbi", "129409")
@allure.label("testcase", "139806")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139806
@pytest.mark.traceability("139806")
def test_b2b_register_cta_opens_registration_form(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.is_hero_visible()

    with allure.step("Inspect the hero CTA"):
        assert b2b.cta_icon_count() == 1
        assert b2b.cta_label_text() == CTA_LABEL_EN

    with allure.step("Click 'Register Your Company'"):
        b2b.click_register_cta()
        assert b2b.current_url() == web_url(REGISTRATION_PATH)
        assert b2b.is_registration_form_visible() is True, (
            "the B2B Registration form did not open — the CTA landed on "
            f"{b2b.current_url()} with the title {b2b.page_title()!r}"
        )

    with allure.step("Inspect the form's sections"):
        assert b2b.registration_section_count() == 5
        assert b2b.registration_section_titles() == REGISTRATION_SECTIONS_EN
        field_names = b2b.registration_field_names()
        for name in (
            list(B2bMatchmakingPage.REGISTRATION_REQUIRED_TEXT_FIELDS)
            + list(B2bMatchmakingPage.REGISTRATION_REQUIRED_SELECTS)
            + ["yearOfEstablishment", "videoLink", "chamberMembershipNumber", "designation",
               "companyLogo", "companyProfileDocument"]
        ):
            assert name in field_names, f"the registration form has no '{name}' field"
        mandatory = b2b.registration_mandatory_labels()
        assert len(mandatory) >= len(B2bMatchmakingPage.REGISTRATION_REQUIRED_TEXT_FIELDS)


# ===========================================================================
# 139824 — English page renders LTR with the designed copy
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("UI — English")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The English B2B Matchmaking page renders left-to-right with the designed copy")
@allure.label("pbi", "129409")
@allure.label("testcase", "139824")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139824
@pytest.mark.traceability("139824")
def test_b2b_english_page_renders_ltr_with_designed_copy(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.document_direction() == "ltr"

    with allure.step("Inspect the hero"):
        assert b2b.hero_eyebrow_text() == HERO_EYEBROW_EN
        assert b2b.hero_title_text() == HERO_TITLE_EN
        geometry = b2b.hero_geometry()
        eyebrow_box = b2b.hero_eyebrow_box()
        title_box = b2b.hero_title_box()
        assert eyebrow_box["y"] < title_box["y"], "the eyebrow does not sit above 'B2B Connect'"
        lede_box = b2b.hero_lede_box()
        assert lede_box["width"] <= geometry["copy"]["width"] + 2, (
            "the hero description is not constrained to its designed column"
        )
        assert lede_box["width"] < b2b.viewport_size()["width"]
        assert b2b.cta_icon_count() == 1
        assert b2b.cta_label_text() == CTA_LABEL_EN
        assert geometry["copy"]["x"] + geometry["copy"]["width"] <= geometry["art"]["x"] + 2

    with allure.step("Inspect the search bar"):
        assert b2b.search_field_labels() == SEARCH_LABELS_EN
        row = b2b.search_row_geometry()
        assert len(row["fields"]) == 3
        trailing_edge = max(f["x"] + f["width"] for f in row["fields"])
        assert row["actions"]["x"] >= trailing_edge - 2, (
            "the reset control and Search button are not on the trailing side"
        )
        assert b2b.is_reset_control_visible()

    with allure.step("Inspect the grid and the Load More button"):
        assert b2b.grid_column_count() == 3
        # The "full-width Load More button" clause is NOT asserted: with 3
        # approved companies against a page size of 12 the control is
        # correctly hidden. See the module docstring's blocked-sub-clause list.
        for which in ("card_name", "card_industry"):
            assert _effective_alignment(b2b.text_alignment(which)) == "left"


# ===========================================================================
# 139825 — Arabic page renders RTL with Arabic copy throughout
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("UI — Arabic")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Arabic B2B Matchmaking page renders right-to-left with Arabic copy throughout")
@allure.label("pbi", "129409")
@allure.label("testcase", "139825")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.rtl
@pytest.mark.arabic
@pytest.mark.pbi_129409
@pytest.mark.tc_139825
@pytest.mark.traceability("139825")
def test_b2b_arabic_page_renders_rtl_with_arabic_copy(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in Arabic"):
        b2b.open_b2b_matchmaking(locale="ar")
        assert b2b.document_direction() == "rtl"

    with allure.step("Inspect the hero and the search bar"):
        for value in (b2b.hero_eyebrow_text(), b2b.hero_title_text(), b2b.hero_lede_text(),
                      b2b.cta_label_text(), b2b.company_name_placeholder(),
                      b2b.search_button_text()):
            assert _has_arabic(value), f"not rendered in Arabic: {value!r}"
        for label in b2b.search_field_labels():
            assert _has_arabic(label), f"search label not Arabic: {label!r}"
        assert _effective_alignment(b2b.text_alignment("hero_title")) == "right"
        assert _effective_alignment(b2b.text_alignment("search_label")) == "right"

    with allure.step("Inspect the grid and a company card"):
        # Company trade names are proper nouns stored once (`companyName` has
        # no locale variant — the API returns the same string under ar_SA), so
        # the Arabic page is expected to render them UNCHANGED. Asserted as an
        # identity check against the approved English names rather than as an
        # "is Arabic" check, which the product could never satisfy.
        arabic_names = b2b.card_names()
        assert sorted(arabic_names) == sorted(ALL_COMPANY_NAMES), (
            "the Arabic grid does not show the same company trade names as the "
            f"English one: AR {arabic_names} vs approved {ALL_COMPANY_NAMES}"
        )
        for industry in b2b.card_industries():
            assert _has_arabic(industry), f"card industry left untranslated: {industry!r}"
        for country in b2b.card_countries():
            assert _has_arabic(country), f"card country left untranslated: {country!r}"

    with allure.step("Inspect the layout direction of the search controls and the card"):
        assert b2b.search_form_direction() == "rtl"
        row = b2b.search_row_geometry()
        leading_field_edge = min(f["x"] for f in row["fields"])
        assert row["actions"]["x"] + row["actions"]["width"] <= leading_field_edge + 2, (
            "the Search button is not on the mirrored side of the search controls"
        )
        card = b2b.card_geometry(0)
        assert card["logo"]["x"] > card["head"]["x"], (
            "the card logo is not on the mirrored side of its text"
        )
        assert card["flag"]["x"] + card["flag"]["width"] >= (
            card["country"]["x"] + card["country"]["width"] - 2
        ), "the country flag is not mirrored to match"


# ===========================================================================
# 139828 — Desktop viewport 1920x1080
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Compatibility — desktop")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The B2B Matchmaking page renders correctly at desktop viewport width (1920x1080)")
@allure.label("pbi", "129409")
@allure.label("testcase", "139828")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139828
@pytest.mark.traceability("139828")
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_b2b_renders_correctly_at_desktop_viewport(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Set the browser viewport to 1920x1080"):
        assert page.viewport_size == {"width": 1920, "height": 1080}

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.has_horizontal_scrollbar() is False, (
            f"the page scrolls horizontally at viewport {b2b.viewport_size()}"
        )

    with allure.step("Inspect the hero and search bar"):
        geometry = b2b.hero_geometry()
        assert geometry["copy"]["x"] + geometry["copy"]["width"] <= geometry["art"]["x"] + 2
        assert b2b.hero_image_size() == HERO_BANNER_DESIGNED
        row = b2b.search_row_geometry()
        rows = {round(f["y"]) for f in row["fields"]} | {round(row["actions"]["y"])}
        assert b2b.search_field_row_count() == 1, "the three search controls are not on one row"
        assert min(rows) >= row["fields"][0]["y"] - 60

    with allure.step("Inspect the company grid and open a popup"):
        assert b2b.grid_column_count() == 3
        assert b2b.cards_per_row() == 3
        b2b.open_card(0)
        geo = b2b.details_dialog_geometry()
        dialog, viewport = geo["dialog"], geo["viewport"]
        assert dialog["x"] >= 0 and dialog["y"] >= 0
        assert dialog["x"] + dialog["width"] <= viewport["width"] + 1
        assert dialog["y"] + dialog["height"] <= viewport["height"] + 1
        centre = dialog["x"] + dialog["width"] / 2
        assert abs(centre - viewport["width"] / 2) <= 4, "the popup is not centred"
        assert b2b.details_company_name() != ""
        assert len(b2b.details_fields()) == len(DETAILS_FIELD_TERMS_EN)
        assert len(b2b.details_sections()) == len(DETAILS_SECTION_HEADS_EN)


# ===========================================================================
# 139829 — Tablet viewport 768x1024
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Compatibility — tablet")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The B2B Matchmaking page renders correctly at tablet viewport width (768x1024)")
@allure.label("pbi", "129409")
@allure.label("testcase", "139829")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139829
@pytest.mark.traceability("139829")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_b2b_renders_correctly_at_tablet_viewport(page):
    """768px is an UNDESIGNED width: the Figma component set "B2B Connect"
    (#3323:131245) ships only desktop 1920 and mobile 390 variants. The
    assertions below therefore encode only what this case itself claims —
    reflow without overlap, more than one row of search controls, fewer grid
    columns, a popup that fits with scrollable content, and registration
    fields that stack rather than truncate. No desktop specific (3 cards per
    row, fixed widths) is imported here."""
    b2b = B2bMatchmakingPage(page)

    with allure.step("Set the browser viewport to 768x1024"):
        assert page.viewport_size == {"width": 768, "height": 1024}

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.has_horizontal_scrollbar() is False, (
            f"the page scrolls horizontally at viewport {b2b.viewport_size()}"
        )
        assert b2b.card_parts_within_card(0) is True, (
            f"part of card 0 sits outside the card box: {b2b.card_geometry(0)}"
        )

    with allure.step("Inspect the hero and search bar"):
        geometry = b2b.hero_geometry()
        assert _boxes_overlap(geometry["copy"], geometry["art"]) is False, (
            "the hero text and image overlap"
        )
        assert b2b.search_field_row_count() > 1, (
            "the search controls did not wrap onto more than one row"
        )
        for field in b2b.search_field_boxes():
            assert field["width"] > 0 and field["height"] > 0

    with allure.step("Inspect the grid, open a popup and open the registration form"):
        desktop_columns = 3
        assert b2b.grid_column_count() < desktop_columns, (
            "the grid did not reflow to fewer columns"
        )

        b2b.open_card(0)
        geo = b2b.details_dialog_geometry()
        dialog, viewport = geo["dialog"], geo["viewport"]
        assert dialog["x"] >= -1 and dialog["y"] >= -1
        assert dialog["x"] + dialog["width"] <= viewport["width"] + 1
        assert dialog["y"] + dialog["height"] <= viewport["height"] + 1
        assert geo["overflowY"] in ("auto", "scroll"), (
            "the popup's content region is not scrollable"
        )
        b2b.close_details_popup()

        assert b2b.is_registration_form_visible() is True, (
            f"the B2B Registration form is not visible on {b2b.current_url()}"
        )
        assert b2b.registration_field_row_count() > 1, (
            "the registration form's fields did not stack"
        )
        assert b2b.registration_fields_are_untruncated() is True, (
            "registration fields are clipped by their wrapper or by the viewport at "
            f"{b2b.viewport_size()}: {b2b.registration_truncated_fields()}"
        )


# ===========================================================================
# 139830 — Mobile viewport 390x844
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Compatibility — mobile")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The B2B Matchmaking page and its Contact webform are usable at mobile viewport width (390x844)")
@allure.label("pbi", "129409")
@allure.label("testcase", "139830")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139830
@pytest.mark.traceability("139830")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_b2b_is_usable_at_mobile_viewport(page):
    """Step 4's CAPTCHA clause is only PARTLY covered, deliberately. The
    Contact webform's `[data-qc-recaptcha-field]` renders `hidden` on this
    site (reCAPTCHA Enterprise score key), so there is no CAPTCHA control a
    visitor can reach or operate by touch, and the submit-through-CAPTCHA
    portion of this case is reported BLOCKED rather than stubbed, bypassed or
    faked. Its PRESENCE on the form is asserted below; the fields, the
    conditional block and the Submit button are asserted reachable and
    operable in full."""
    b2b = B2bMatchmakingPage(page)

    with allure.step("Set the browser viewport to 390x844"):
        assert page.viewport_size == {"width": 390, "height": 844}

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.has_horizontal_scrollbar() is False, (
            f"the page scrolls horizontally at viewport {b2b.viewport_size()}"
        )
        assert b2b.card_parts_within_card(0) is True, (
            f"part of card 0 sits outside the card box: {b2b.card_geometry(0)}"
        )

    with allure.step("Inspect the hero, search bar and grid"):
        geometry = b2b.hero_geometry()
        assert geometry["art"]["y"] >= geometry["copy"]["y"] + geometry["copy"]["height"] - 2, (
            "the hero did not stack vertically"
        )
        assert b2b.search_field_column_count() == 1, (
            "the search controls did not stack into a single column"
        )
        assert b2b.grid_column_count() == 1
        assert b2b.cards_per_row() == 1

    with allure.step("Open a company card, then open the Contact Company webform"):
        b2b.open_card(0)
        geo = b2b.details_dialog_geometry()
        dialog, viewport = geo["dialog"], geo["viewport"]
        # "full-screen or near-full-screen": at least 80% of the viewport in
        # both dimensions, and fitting inside it.
        assert dialog["width"] >= viewport["width"] * 0.8
        assert dialog["height"] >= viewport["height"] * 0.8
        assert dialog["x"] + dialog["width"] <= viewport["width"] + 1
        assert geo["overflowY"] in ("auto", "scroll")
        assert geo["scrollHeight"] > geo["clientHeight"], (
            "the popup's content is not actually scrollable"
        )

        b2b.open_contact_form()
        b2b.fill_contact_fields(CONTACT_FORM_DATA)
        b2b.fill_contact_fields(CONTACT_EMAIL_BRANCH_DATA)

        operable = b2b.are_contact_fields_operable_by_touch()
        unreachable = [name for name, ok in operable.items() if not ok]
        assert not unreachable, f"not reachable/operable by touch at 390px: {unreachable}"

        captcha = b2b.captcha_field_state("contact")
        assert b2b.is_recaptcha_script_loaded() is True, (
            "the reCAPTCHA Enterprise script (#qc-recaptcha-enterprise-js) is not loaded on "
            f"{b2b.current_url()}"
        )
        assert captcha["present"] is True, "the webform ships no CAPTCHA protection at all"

        cf_geo = b2b.contact_dialog_geometry()
        assert cf_geo["dialog"]["width"] <= cf_geo["viewport"]["width"] + 1
        assert cf_geo["overflowY"] in ("auto", "scroll")


# ===========================================================================
# 139833 — Light mode
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Compatibility — light mode")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The B2B Matchmaking page renders correctly in light mode")
@allure.label("pbi", "129409")
@allure.label("testcase", "139833")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.pbi_129409
@pytest.mark.tc_139833
@pytest.mark.traceability("139833")
def test_b2b_renders_correctly_in_light_mode(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Set the site appearance to light mode"):
        b2b.open_b2b_matchmaking()
        assert b2b.theme() == "light"

    with allure.step("Open the public B2B Matchmaking page in English"):
        assert b2b.card_count() > 0

    with allure.step("Inspect the header, hero and search bar"):
        assert b2b.site_header_style()["backgroundColor"] == WHITE
        assert b2b.page_background_style()["backgroundColor"] == WHITE
        search = b2b.search_form_style()
        assert search["backgroundColor"] == WHITE
        assert search["borderStyle"] != "none" and search["borderWidth"] != "0px", (
            f"the search bar renders no border at all: {search}"
        )
        assert search["borderColor"] == MAROON, (
            f"the search bar's border is not maroon: {search['borderColor']}"
        )
        button = b2b.search_button_style()
        assert button["backgroundColor"] == MAROON
        assert button["color"] == WHITE

    with allure.step("Inspect a company card, its Approved badge and the popup"):
        card = b2b.card_style()
        assert card["backgroundColor"] == WHITE
        assert card["borderStyle"] == "solid" and card["borderWidth"] != "0px"
        assert card["borderRadius"] == CARD_RADIUS_DESIGNED, (
            f"the card corner radius is {card['borderRadius']}, not the designed "
            f"{CARD_RADIUS_DESIGNED}"
        )
        assert b2b.card_badges()[0] == BADGE_APPROVED_EN
        assert _legible(b2b.badge_style(), WHITE) is True, (
            f"the Approved badge is not legible on white: {b2b.badge_style()}"
        )

        b2b.open_card(0)
        regions = b2b.details_region_styles()
        assert regions["dialog"]["backgroundColor"] == WHITE
        for name in ("name", "field_term", "field_value", "section_heading", "section_body"):
            assert _legible(regions[name], WHITE) is True, f"popup {name} is not legible"


# ===========================================================================
# 139834 — Dark mode
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Compatibility — dark mode")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The B2B Matchmaking page, popup and forms render correctly in dark mode")
@allure.label("pbi", "129409")
@allure.label("testcase", "139834")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139834
@pytest.mark.traceability("139834")
def test_b2b_renders_correctly_in_dark_mode(page):
    """Dark mode on this site is a site-wide `data-theme="dark"` attribute
    driven by the Accessibility Tools panel — NOT `prefers-color-scheme`, so a
    Playwright `color_scheme="dark"` context would change nothing. The
    existing AccessibilityToolsComponent is composed to drive the real
    switch."""
    b2b = B2bMatchmakingPage(page)

    with allure.step("Set the site appearance to dark mode"):
        b2b.open_b2b_matchmaking()
        b2b.enable_dark_mode()
        assert b2b.theme() == "dark"

    with allure.step("Open the public B2B Matchmaking page in English"):
        assert b2b.card_count() > 0

    with allure.step("Inspect the header, hero, search bar and grid"):
        page_bg = b2b.page_background_style()["backgroundColor"]
        assert _is_dark(page_bg), f"the page background stayed light: {page_bg}"
        assert _is_dark(b2b.site_header_style()["backgroundColor"])
        search_bg = b2b.search_form_style()["backgroundColor"]
        assert _is_dark(search_bg), f"the search bar stayed light: {search_bg}"
        card_bg = b2b.card_style()["backgroundColor"]
        assert _is_dark(card_bg), f"the cards stayed light: {card_bg}"

        assert _legible(b2b.search_label_style(), search_bg) is True, (
            f"the search label is not legible: {b2b.search_label_style()} on {search_bg}"
        )
        assert _legible(b2b.name_input_style(), search_bg) is True, (
            f"the Company Name input is not legible: {b2b.name_input_style()} on {search_bg}"
        )
        assert _legible(b2b.card_name_style(), card_bg) is True, (
            f"the card company name is not legible: {b2b.card_name_style()} on {card_bg}"
        )
        assert _legible(b2b.card_industry_style(), card_bg) is True, (
            f"the card industry is not legible: {b2b.card_industry_style()} on {card_bg}"
        )
        assert _legible(b2b.card_country_style(), card_bg) is True, (
            f"the card country is not legible: {b2b.card_country_style()} on {card_bg}"
        )
        assert _legible(b2b.badge_style(), card_bg) is True, (
            f"the Approved badge is not legible: {b2b.badge_style()} on {card_bg}"
        )
        assert _legible(b2b.status_style(), page_bg) is True, (
            f"the result-count status is not legible: {b2b.status_style()} on {page_bg}"
        )

    with allure.step("Open a company card, then open the Contact Company webform"):
        b2b.open_card(0)
        popup = b2b.details_region_styles()
        popup_bg = popup["dialog"]["backgroundColor"]
        assert _is_dark(popup_bg), f"the popup stayed light: {popup_bg}"
        for name in ("name", "industry", "field_term", "field_value", "section_heading",
                     "section_body", "contact"):
            assert _legible(popup[name], popup_bg) is True, f"popup {name} is not readable"

        b2b.open_contact_form()
        form = b2b.contact_form_region_styles()
        form_bg = form["dialog"]["backgroundColor"]
        assert _is_dark(form_bg), f"the Contact webform stayed light: {form_bg}"
        for name in ("title", "legend", "label", "input", "company_panel",
                     "conditional_label", "conditional_input", "submit", "cancel"):
            assert _legible(form[name], form_bg) is True, f"webform {name} is not readable"
        assert b2b.is_contact_submit_operable_by_touch() is True, (
            "the Send Request button is not operable by touch — per-control state: "
            f"{b2b.are_contact_fields_operable_by_touch()}"
        )


# ===========================================================================
# 139693 — The Company Name filter matches partially
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Filters — company name")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Company Name filter matches partially rather than requiring an exact name")
@allure.label("pbi", "129409")
@allure.label("testcase", "139693")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139693
@pytest.mark.traceability("139693")
def test_b2b_company_name_filter_matches_partially(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.card_count() > 0
        assert b2b.company_name_value() == ""

    with allure.step("Note the full name of an approved company in the grid"):
        full_name = COMPANY_DOHA
        assert full_name in b2b.card_names()

    with allure.step("Type a middle fragment of that name into Company Name and Search"):
        assert MIDDLE_NAME_FRAGMENT in full_name
        assert not full_name.lower().startswith(MIDDLE_NAME_FRAGMENT.lower())
        b2b.set_company_name(MIDDLE_NAME_FRAGMENT).click_search()

    with allure.step("Inspect every rendered card"):
        names = b2b.card_names()
        assert full_name in names, (
            f"the fragment {MIDDLE_NAME_FRAGMENT!r} did not return {full_name!r}"
        )
        for name in names:
            assert MIDDLE_NAME_FRAGMENT.lower() in name.lower()


# ===========================================================================
# 139696 — The Business Offer From filter narrows by exact match
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Filters — business offer from")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Business Offer From filter narrows the grid by exact match")
@allure.label("pbi", "129409")
@allure.label("testcase", "139696")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139696
@pytest.mark.traceability("139696")
def test_b2b_business_offer_from_filter_narrows_by_exact_match(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        full_count = b2b.card_count()
        assert full_count == APPROVED_COMPANY_COUNT

    with allure.step(f"Select '{COUNTRY_QATAR}' in Business Offer From and Search"):
        b2b.select_country(COUNTRY_QATAR).click_search()
        assert b2b.card_count() < full_count

    with allure.step("Inspect every rendered card"):
        countries = b2b.card_countries()
        assert countries
        for country in countries:
            assert country.upper() == COUNTRY_QATAR.upper(), (
                f"a near/partial match leaked into the result: {country!r}"
            )

    with allure.step(f"Reset, select '{COUNTRY_GERMANY}' and Search"):
        b2b.click_reset()
        assert b2b.country_selected_label() == ALL_COUNTRIES
        b2b.select_country(COUNTRY_GERMANY).click_search()
        countries = b2b.card_countries()
        assert countries
        for country in countries:
            assert country.upper() == COUNTRY_GERMANY.upper()


# ===========================================================================
# 139698 — The Industry Type filter narrows by exact match
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Filters — industry type")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Industry Type filter narrows the grid by exact match")
@allure.label("pbi", "129409")
@allure.label("testcase", "139698")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139698
@pytest.mark.traceability("139698")
def test_b2b_industry_type_filter_narrows_by_exact_match(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        full_count = b2b.card_count()
        assert full_count == APPROVED_COMPANY_COUNT

    with allure.step(f"Select '{INDUSTRY_ENERGY}' in Industry Type and Search"):
        b2b.select_industry(INDUSTRY_ENERGY).click_search()
        assert b2b.card_count() < full_count

    with allure.step("Inspect every rendered card"):
        industries = b2b.card_industries()
        assert industries
        for industry in industries:
            assert industry == INDUSTRY_ENERGY, (
                f"a near/partial match leaked into the result: {industry!r}"
            )

    with allure.step(f"Reset, select '{INDUSTRY_LOGISTICS}' and Search"):
        b2b.click_reset()
        assert b2b.industry_selected_label() == ALL_INDUSTRIES
        b2b.select_industry(INDUSTRY_LOGISTICS).click_search()
        industries = b2b.card_industries()
        assert industries
        for industry in industries:
            assert industry == INDUSTRY_LOGISTICS


# ===========================================================================
# 139699 — Contact — Company Name is auto-filled and cannot be edited
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Contact Company webform")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Contact — Company Name is auto-filled from the selected company and cannot be edited")
@allure.label("pbi", "129409")
@allure.label("testcase", "139699")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139699
@pytest.mark.traceability("139699")
def test_b2b_contact_company_name_is_autofilled_and_read_only(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.card_count() > 0

    with allure.step("Click a company card and note the company name and contact person"):
        b2b.open_card(0)
        company_name = b2b.details_company_name()
        contact_person = b2b.details_fields()["Contact Person"]
        assert company_name and contact_person

    with allure.step("Click Contact in the popup and inspect the auto-filled fields"):
        b2b.open_contact_form()
        assert b2b.contact_company_name_shown() == company_name

    with allure.step("Attempt to edit the Contact — Company Name"):
        b2b.try_to_edit_contact_company_name("Another Company WLL")
        assert b2b.contact_company_name_shown() == company_name, (
            "the pre-filled company name changed — the request could be redirected"
        )
        assert b2b.contact_company_panel_editable_count() == 0, (
            "the company panel exposes an editable control: "
            f"{b2b.contact_company_panel_control_tags()}"
        )


# ===========================================================================
# 139700 — Contact — Company Contact Person is auto-filled and cannot be edited
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Contact Company webform")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Contact — Company Contact Person is auto-filled from the company's registered contact and cannot be edited")
@allure.label("pbi", "129409")
@allure.label("testcase", "139700")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139700
@pytest.mark.traceability("139700")
def test_b2b_contact_company_contact_person_is_autofilled_and_read_only(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the public B2B Matchmaking page in English"):
        b2b.open_b2b_matchmaking()
        assert b2b.card_count() > 0

    with allure.step("Click a company card and note the company name and contact person"):
        b2b.open_card(0)
        contact_person = b2b.details_fields()["Contact Person"]
        assert contact_person

    with allure.step("Click Contact in the popup and inspect the auto-filled fields"):
        b2b.open_contact_form()
        assert b2b.contact_company_contact_shown() == contact_person

    with allure.step("Attempt to edit the Contact — Company Contact Person"):
        b2b.try_to_edit_contact_company_contact("Someone Else")
        assert b2b.contact_company_contact_shown() == contact_person, (
            "the pre-filled contact person changed — the request could be redirected"
        )
        assert b2b.contact_company_panel_editable_count() == 0, (
            "the company panel exposes an editable control: "
            f"{b2b.contact_company_panel_control_tags()}"
        )


# ===========================================================================
# 139757 — Preferred Method of Contact offers Email and Phone, defaults Email
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Contact Company webform")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Preferred Method of Contact offers exactly Email and Phone and defaults to Email")
@allure.label("pbi", "129409")
@allure.label("testcase", "139757")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139757
@pytest.mark.traceability("139757")
def test_b2b_preferred_method_of_contact_options_and_default(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open a company card and click Contact in the popup"):
        b2b.open_b2b_matchmaking()
        b2b.open_card(0)
        b2b.open_contact_form()
        assert b2b.is_contact_form_open() is True, (
            "the Contact webform did not open from the popup (details popup open="
            f"{b2b.is_details_popup_open()})"
        )

    with allure.step("Inspect the Preferred Method of Contact before any selection"):
        assert b2b.contact_method_selected_label() == "Email"

    with allure.step("Open the dropdown and list every option"):
        options = b2b.contact_method_options()
        assert options == CONTACT_METHOD_OPTIONS_EN, (
            f"the dropdown offers {options}, not exactly Email and Phone"
        )

    with allure.step("Select Phone, then select Email again"):
        b2b.select_contact_option("preferredMethodOfContact", CONTACT_METHOD_PHONE)
        assert b2b.contact_method_selected_label() == "Phone"
        assert b2b.is_contact_phone_branch_visible() is True, (
            "the Phone branch did not render after selecting Phone — the method shown is "
            f"{b2b.contact_method_selected_label()!r} and the visible branch fields are "
            f"{b2b.contact_branch_field_labels()}"
        )
        assert b2b.is_contact_email_branch_visible() is False, (
            "the Email branch is still rendered while the method shown is "
            f"{b2b.contact_method_selected_label()!r} — visible branch fields: "
            f"{b2b.contact_branch_field_labels()}"
        )

        b2b.select_contact_option("preferredMethodOfContact", CONTACT_METHOD_EMAIL)
        assert b2b.contact_method_selected_label() == "Email"
        assert b2b.is_contact_email_branch_visible() is True, (
            "the Email branch did not render after selecting Email — the method shown is "
            f"{b2b.contact_method_selected_label()!r} and the visible branch fields are "
            f"{b2b.contact_branch_field_labels()}"
        )
        assert b2b.is_contact_phone_branch_visible() is False, (
            "the Phone branch is still rendered while the method shown is "
            f"{b2b.contact_method_selected_label()!r} — visible branch fields: "
            f"{b2b.contact_branch_field_labels()}"
        )


# ===========================================================================
# 139762 — Submitting with the conditional branch left empty is blocked
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Contact Company webform — validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Submitting the Contact webform with the conditional branch left empty is blocked")
@allure.label("pbi", "129409")
@allure.label("testcase", "139762")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139762
@pytest.mark.traceability("139762")
def test_b2b_contact_form_blocks_submit_with_empty_conditional_branch(page):
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open a company card and click Contact in the popup"):
        b2b.open_b2b_matchmaking()
        b2b.open_card(0)
        b2b.open_contact_form()

    with allure.step("Set the method to Email and leave Email and Confirm Email empty"):
        b2b.select_contact_option("preferredMethodOfContact", CONTACT_METHOD_EMAIL)
        assert b2b.contact_field_value("email") == ""
        assert b2b.contact_field_value("confirmEmail") == ""

    with allure.step("Complete every other field and click Submit"):
        b2b.fill_contact_fields(CONTACT_FORM_DATA)
        b2b.submit_contact_form()
        assert b2b.is_contact_success_shown() is False, "the request was submitted anyway"
        assert b2b.contact_field_error("email") != ""
        assert b2b.contact_field_error("confirmEmail") != ""

    with allure.step("Switch to Phone, leave Phone empty and click Submit again"):
        b2b.select_contact_option("preferredMethodOfContact", CONTACT_METHOD_PHONE)
        assert b2b.is_contact_phone_branch_visible() is True, (
            "the Phone branch did not render after switching the method to Phone — the "
            f"method shown is {b2b.contact_method_selected_label()!r} and the visible "
            f"branch fields are {b2b.contact_branch_field_labels()}"
        )
        assert b2b.contact_field_value("phone") == ""
        b2b.submit_contact_form()
        assert b2b.is_contact_success_shown() is False, "the request was submitted anyway"
        assert b2b.contact_field_error("phone") != ""


# ===========================================================================
# 139765 — Submitting with an empty Comments / Questions is blocked
# ===========================================================================
@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("Contact Company webform — validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Submitting the Contact webform with an empty Comments / Questions is blocked")
@allure.label("pbi", "129409")
@allure.label("testcase", "139765")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139765
@pytest.mark.traceability("139765")
def test_b2b_contact_form_blocks_submit_with_empty_comments(page):
    """Step 3 reads "Pass the CAPTCHA and click Submit". Measured live: this
    form's CAPTCHA field renders `hidden` (reCAPTCHA Enterprise score key —
    there is nothing for a visitor to pass) and the form's own client-side
    required-field validation fires before any CAPTCHA/network step, so the
    expected result is reachable exactly as written. No CAPTCHA is stubbed,
    solved or bypassed here."""
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open a company card and click Contact in the popup"):
        b2b.open_b2b_matchmaking()
        b2b.open_card(0)
        b2b.open_contact_form()

    with allure.step("Complete every mandatory field except Comments / Questions"):
        b2b.fill_contact_fields(CONTACT_FORM_DATA, skip=("commentsOrQuestions",))
        b2b.fill_contact_fields(CONTACT_EMAIL_BRANCH_DATA)
        assert b2b.contact_field_value("commentsOrQuestions") == ""
        for name, value in CONTACT_FORM_DATA.items():
            if name == "commentsOrQuestions":
                continue
            assert b2b.contact_field_value(name) == value

    with allure.step("Click Submit"):
        b2b.submit_contact_form()
        assert b2b.is_contact_success_shown() is False, "the request was submitted anyway"
        assert b2b.contact_field_error("commentsOrQuestions") != "", (
            "no inline validation error was shown on Comments / Questions"
        )

    with allure.step("Inspect the form"):
        for name, value in CONTACT_FORM_DATA.items():
            if name == "commentsOrQuestions":
                continue
            assert b2b.contact_field_value(name) == value, f"{name} lost its value"
        for name, value in CONTACT_EMAIL_BRANCH_DATA.items():
            assert b2b.contact_field_value(name) == value, f"{name} lost its value"


# ===========================================================================
# 139777 / 139780 / 139783 — Registration form required-field validation
# ===========================================================================
def _open_registration_form_via_cta(b2b: B2bMatchmakingPage) -> None:
    """Step 1 of 139777 / 139780 / 139783, written exactly as the cases state
    it: open the B2B Matchmaking page and click Register Your Company in the
    hero, then require the B2B Registration form to have loaded."""
    b2b.open_b2b_matchmaking()
    b2b.click_register_cta()
    assert b2b.is_registration_form_visible() is True, (
        "the B2B Registration form did not load — 'Register Your Company' landed on "
        f"{b2b.current_url()} with the title {b2b.page_title()!r}"
    )


def _assert_registration_blocked_on(b2b: B2bMatchmakingPage, missing_field: str) -> None:
    b2b.fill_registration_fields(REGISTRATION_FORM_DATA, skip=(missing_field,))
    b2b.check_registration_consent()
    assert b2b.registration_field_value(missing_field) == ""

    b2b.submit_registration_form()
    assert b2b.is_registration_success_shown() is False, "the registration was submitted anyway"
    assert b2b.registration_field_error(missing_field) != "", (
        f"no inline validation error was shown on {missing_field}"
    )

    for name, value in REGISTRATION_FORM_DATA.items():
        if name == missing_field:
            continue
        assert b2b.registration_field_value(name) == value, f"{name} lost its value"


@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("B2B Registration form — validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Submitting the B2B Registration form with an empty Summary of Offer is blocked")
@allure.label("pbi", "129409")
@allure.label("testcase", "139777")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139777
@pytest.mark.traceability("139777")
def test_b2b_registration_blocks_submit_with_empty_summary_of_offer(page):
    """Step 3 reads "Pass the CAPTCHA and click Submit". Re-measured live
    2026-09-17: the registration form's `[data-qc-recaptcha-field]` is
    `hidden` (score key) exactly like the Contact webform's — its
    "Security Check *" label exists but the field itself is not rendered, so
    there is nothing for a visitor to pass. The form's own client-side
    required-field validation fires FIRST in any case — submitting with a
    blank mandatory field paints the inline error without reaching the
    CAPTCHA or the network. Nothing here stubs, solves or bypasses it."""
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the page and click Register Your Company in the hero"):
        _open_registration_form_via_cta(b2b)

    with allure.step("Complete every mandatory field except Summary of Offer, then Submit"):
        _assert_registration_blocked_on(b2b, "summaryOfOffer")


@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("B2B Registration form — validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Submitting the B2B Registration form with an empty Company Description is blocked")
@allure.label("pbi", "129409")
@allure.label("testcase", "139780")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139780
@pytest.mark.traceability("139780")
def test_b2b_registration_blocks_submit_with_empty_company_description(page):
    """See test_b2b_registration_blocks_submit_with_empty_summary_of_offer for
    the CAPTCHA note that applies to this case's step 3 as well."""
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the page and click Register Your Company in the hero"):
        _open_registration_form_via_cta(b2b)

    with allure.step("Complete every mandatory field except Company Description, then Submit"):
        _assert_registration_blocked_on(b2b, "companyDescription")


@allure.epic("Our Services")
@allure.feature("B2B Matchmaking")
@allure.story("B2B Registration form — validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Submitting the B2B Registration form with an empty Potential Partners is blocked")
@allure.label("pbi", "129409")
@allure.label("testcase", "139783")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_129409
@pytest.mark.tc_139783
@pytest.mark.traceability("139783")
def test_b2b_registration_blocks_submit_with_empty_potential_partners(page):
    """See test_b2b_registration_blocks_submit_with_empty_summary_of_offer for
    the CAPTCHA note that applies to this case's step 3 as well."""
    b2b = B2bMatchmakingPage(page)

    with allure.step("Open the page and click Register Your Company in the hero"):
        _open_registration_form_via_cta(b2b)

    with allure.step("Complete every mandatory field except Potential Partners, then Submit"):
        _assert_registration_blocked_on(b2b, "potentialPartners")

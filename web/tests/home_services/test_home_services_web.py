"""
web/tests/home_services/test_home_services_web.py — Our Services Section
(PBI 129371 / QC-HOME-003), Web platform.

Source: the 17 approved, Automation-tagged, Web-platform cases injected in
Test Plan 133534 (ADO TC 135329-135345, 135353, 135414).

Rewritten 2026-10-21 against a re-verified live page:
  - Every test runs in a fresh LOGGED-OUT context (`"auth": False`) and
    navigates with `open_anonymous` — public site, read-only.
  - Expected card sets are not hardcoded. `open_home_with_oracle()` captures
    the public service-cards JSON the section itself renders from, and each
    filter assertion compares the rendered cards with the cards CONFIGURED
    for that tab (`assignedTab`). The data changes on shared qcdev; the
    filtering rule the cases describe does not.
  - TC 135353 / 135414 need a live CMS write in their own Arrange step
    (deactivate every service card / unpublish the listing page). Live CMS
    writes are forbidden for this run, so both are SKIPPED with that reason.
  - TC 135345: the live tab label is "Information" (case: "Information
    Services"); the tab is selected by its `data-key`, and the label
    difference is reported as an observation, not asserted away.
"""

import json

import allure
import pytest

from web.pages.home_services.home_services_page import HomeServicesPage

PBI = "129371"
EPIC = "SVC"
FEATURE = "Our Services Section"

ANON = {"auth": False}
DESKTOP = {"auth": False, "viewport": (1920, 1080)}
TABLET = {"auth": False, "viewport": (768, 1024)}
MOBILE = {"auth": False, "viewport": (375, 812)}
LAYOUT_TOL = 2  # bug-rules: layout ±2 px

EXPECTED_TAG_TEXT = "Our Services"
EXPECTED_HEADING_TEXT = "Services We Provide"
EXPECTED_DESCRIPTION_TEXT = (
    "We provide a range of services for companies, entrepreneurs, and "
    "investors from membership services to international certifications."
)
EXPECTED_TABS = ["All Services", "Membership", "Legal", "E-Services", "Information"]
CTA_LABEL = "View All Services"
LEGAL_CONSULTING = "Legal Consulting"

AR_TAG_TEXT = "خدماتنا"
AR_HEADING_TEXT = "الخدمات التي نقدمها"
AR_DESCRIPTION_TEXT = (
    "نقدم مجموعة متكاملة من الخدمات لدعم الشركات ورواد الأعمال "
    "والمستثمرين، تشمل خدمات العضوية والشهادات الدولية وغيرها من "
    "الحلول التي تسهّل ممارسة الأعمال."
)
AR_TABS = ["جميع الخدمات", "العضوية", "الخدمات القانونية", "الخدمات الإلكترونية", "المعلومات"]

_CMS_WRITE_FORBIDDEN = "needs live CMS write — forbidden"


def _open_section(page, locale: str = "en") -> HomeServicesPage:
    svc = HomeServicesPage(page).open_home_with_oracle(locale)
    svc.scroll_to_section()
    return svc


def _url_tail(url: str) -> str:
    """Comparable tail of a configured URL: drops the scheme and the Liferay
    site prefix (/web/qatar-chamber) the friendly URL may or may not show."""
    return url.split("://")[-1].split("/web/qatar-chamber")[-1].rstrip("/")


def _assert_tab_filter(svc: HomeServicesPage, which: str) -> None:
    expected = svc.expected_titles_for_tab(which)
    svc.click_tab(which)
    rendered = set(svc.card_titles())
    assert svc.is_tab_active(which), f"expected the '{which}' tab to become active"
    assert expected, f"no service card is configured for the '{which}' tab — nothing to filter"
    assert rendered == expected, (
        f"'{which}' tab should show only its assigned cards; "
        f"missing {sorted(expected - rendered)}, unexpected {sorted(rendered - expected)}"
    )


# ── TC 135329 — English (LTR) render ────────────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Section renders correctly per locale")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Our Services section renders correctly in English (LTR)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.uat
@pytest.mark.pbi_129371
@pytest.mark.tc_135329
@pytest.mark.traceability("ADO-135329")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_section_renders_correctly_in_english_ltr(page):
    # Arrange / Act
    with allure.step("Load the English Home Page and scroll to Our Services"):
        svc = _open_section(page, "en")

    # Assert
    assert svc.page_direction() == "ltr", "site should render LTR in English"
    assert svc.is_section_visible()
    assert svc.tag_text() == EXPECTED_TAG_TEXT
    assert svc.heading_text() == EXPECTED_HEADING_TEXT
    assert svc.description_text() == EXPECTED_DESCRIPTION_TEXT
    assert svc.is_tablist_visible()
    assert svc.tab_texts() == EXPECTED_TABS
    assert svc.head_text_align() in ("start", "left"), "tag/heading/description should be left-aligned"
    tabs = svc.tablist_box()
    head = svc.head_text_box()
    assert abs(tabs["x"] - head["x"]) <= LAYOUT_TOL, (
        f"tab bar should be left-aligned with the heading block (tabs x={tabs['x']}, head x={head['x']})"
    )
    assert set(svc.card_titles()) == svc.expected_titles_for_tab("all"), (
        "every published service card should render"
    )


# ── TC 135330 — Arabic (RTL) render ─────────────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Section renders correctly per locale")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Our Services section renders correctly in Arabic (RTL)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.uat
@pytest.mark.pbi_129371
@pytest.mark.tc_135330
@pytest.mark.traceability("ADO-135330")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_section_renders_correctly_in_arabic_rtl(page):
    # Arrange / Act
    with allure.step("Load the Arabic Home Page and scroll to Our Services"):
        svc = _open_section(page, "ar")

    # Assert
    assert svc.page_direction() == "rtl", "site should render RTL in Arabic"
    assert svc.section_direction() == "rtl"
    assert svc.tag_text() == AR_TAG_TEXT
    assert svc.heading_text() == AR_HEADING_TEXT
    assert svc.description_text() == AR_DESCRIPTION_TEXT
    assert svc.tab_texts() == AR_TABS
    assert svc.head_text_align() in ("start", "right"), "tag/heading/description should be right-aligned"
    tabs, head = svc.tablist_box(), svc.head_text_box()
    assert abs((tabs["x"] + tabs["width"]) - (head["x"] + head["width"])) <= LAYOUT_TOL, (
        "tab bar should be right-aligned with the heading block under RTL "
        f"(tabs right={tabs['x'] + tabs['width']}, head right={head['x'] + head['width']})"
    )
    assert svc.tab_x("all") > svc.tab_x("information"), (
        "tabs should be mirrored: All Services right-most, Information left-most"
    )
    assert set(svc.card_titles()) == svc.expected_titles_for_tab("all"), (
        "cards should render with their configured AR titles"
    )
    assert svc.truncated_card_titles() == [], "AR card titles should not be truncated"
    assert svc.clamped_card_descriptions() == [], "AR card descriptions should not be truncated"


# ── TC 135331 — All Services tab active by default ──────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Default tab state on load")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The All Services tab is active by default on section load")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_129371
@pytest.mark.tc_135331
@pytest.mark.traceability("ADO-135331")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_all_services_tab_active_by_default(page):
    with allure.step("Load the Home Page and scroll to Our Services"):
        svc = _open_section(page)

    assert svc.is_tab_active("all"), "All Services should carry the active-tab indicator by default"
    active, inactive = svc.tab_visual_style("all"), svc.tab_visual_style("membership")
    assert active != inactive, (
        f"All Services should look visibly active vs an inactive tab (active {active}, inactive {inactive})"
    )
    assert set(svc.card_titles()) == svc.expected_titles_for_tab("all"), (
        "every published service card should display by default"
    )


# ── TC 135332 — Public visitor views the section without authentication ────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Unauthenticated public access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Public Visitor can view the published Our Services section without authentication")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129371
@pytest.mark.tc_135332
@pytest.mark.traceability("ADO-135332")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_public_visitor_can_view_section_without_authentication(page):
    with allure.step("Open the Home Page without logging in and scroll to Our Services"):
        svc = _open_section(page)

    with allure.step("Interact with the section: click the Membership tab"):
        svc.click_tab("membership")

    assert svc.is_section_visible()
    assert svc.heading_text() == EXPECTED_HEADING_TEXT
    assert svc.is_tab_active("membership"), "the section should be interactive for a visitor"
    assert svc.no_login_prompt_present(), "no login prompt should appear"
    assert "/login" not in page.url and "/c/portal/login" not in page.url


# ── TC 135335 — clicking a filter tab shows only its assigned cards ────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Filter tab narrows the card set")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking a filter tab displays only cards assigned to that tab")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129371
@pytest.mark.tc_135335
@pytest.mark.traceability("ADO-135335")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_clicking_filter_tab_displays_only_assigned_cards(page):
    with allure.step("Scroll to the section with All Services active"):
        svc = _open_section(page)
        assert svc.is_tab_active("all"), "All Services should be active before filtering"
        all_titles = set(svc.card_titles())

    with allure.step("Click the 'Membership' tab"):
        _assert_tab_filter(svc, "membership")

    assert all_titles - set(svc.card_titles()), "other (non-Membership) cards should be hidden"


# ── TC 135336 — returning to All Services restores the full card set ───────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Restoring the unfiltered card set")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking back to All Services after a filter restores the full card set")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135336
@pytest.mark.traceability("ADO-135336")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_clicking_all_services_after_filter_restores_full_card_set(page):
    with allure.step("Activate the Membership tab"):
        svc = _open_section(page)
        _assert_tab_filter(svc, "membership")

    with allure.step("Click the All Services tab"):
        svc.click_tab("all")

    assert svc.is_tab_active("all"), "All Services should become active again"
    assert set(svc.card_titles()) == svc.expected_titles_for_tab("all"), (
        "every published service card should display again"
    )


# ── TC 135337 — Read More redirects to the detailed service page ───────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Read More navigation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking Read More on a service card redirects to the detailed service page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129371
@pytest.mark.tc_135337
@pytest.mark.traceability("ADO-135337")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_read_more_redirects_to_detailed_service_page(page):
    with allure.step("Locate the Legal Consulting card"):
        svc = _open_section(page)
        assert svc.is_card_present(LEGAL_CONSULTING), "the Legal Consulting card should be on the section"
        svc.bring_card_into_view(LEGAL_CONSULTING)
        parts = svc.card_has_parts(LEGAL_CONSULTING)
        configured = svc.configured_redirect_url(LEGAL_CONSULTING)

    assert parts["icon"], "card should show its icon"
    assert parts["title"] == LEGAL_CONSULTING
    assert parts["description"], "card should show a short description"
    assert parts["read_more"], "card should show a Read More link"
    assert configured, "Legal Consulting has no configured detail-page URL"

    with allure.step("Click its Read More link"):
        start_url = page.url
        svc.click_card_readmore_by_title(LEGAL_CONSULTING)
        page.wait_for_url(lambda url: url != start_url, wait_until="commit", timeout=15000)

    assert page.url.rstrip("/").endswith(_url_tail(configured)), (
        f"should land on the configured detail page {configured!r}, landed on {page.url!r}"
    )
    status = svc.landed_status()
    assert status < 400, f"detail page {page.url!r} answered HTTP {status}"


# ── TC 135338 — View All Services CTA redirects to the listing page ────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("View All Services CTA navigation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking View All Services CTA redirects to the Our Services listing page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129371
@pytest.mark.tc_135338
@pytest.mark.traceability("ADO-135338")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_view_all_services_cta_redirects_to_listing_page(page):
    with allure.step("Scroll to the section and read the CTA"):
        svc = _open_section(page)
        configured = svc.configured_view_all_url()

    assert svc.is_cta_top_visible(), "the CTA button should be visible"
    assert svc.cta_top_text() == CTA_LABEL
    assert configured, "the section has no configured listing-page URL"

    with allure.step("Click View All Services"):
        start_url = page.url
        svc.click_cta_top()
        page.wait_for_url(lambda url: url != start_url, wait_until="commit", timeout=15000)

    assert page.url.rstrip("/").endswith(_url_tail(configured)), (
        f"should land on the configured listing page {configured!r}, landed on {page.url!r}"
    )
    status = svc.landed_status()
    assert status < 400, f"listing page {page.url!r} answered HTTP {status}"


# ── TC 135339 — responsive at mobile width (375px) ──────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The section is fully responsive at mobile width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135339
@pytest.mark.traceability("ADO-135339")
@pytest.mark.parametrize("page", [MOBILE], indirect=True)
def test_section_responsive_at_mobile_width(page):
    with allure.step("Load the Home Page at 375px and scroll to Our Services"):
        svc = _open_section(page)
        head, tabs, card = svc.head_text_box(), svc.tablist_box(), svc.card_box(0)

    assert svc.is_section_visible()
    assert svc.is_tablist_visible()
    assert svc.total_card_count() > 0
    assert svc.has_no_horizontal_overflow(), "no horizontal page scroll at 375px"
    assert tabs["y"] >= head["y"] + head["height"] - LAYOUT_TOL, "tab bar should stack below the heading block"
    assert card["y"] >= tabs["y"] + tabs["height"] - LAYOUT_TOL, "cards should stack below the tab bar"


# ── TC 135340 — responsive at tablet width (768px) ──────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The section is fully responsive at tablet width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135340
@pytest.mark.traceability("ADO-135340")
@pytest.mark.parametrize("page", [TABLET], indirect=True)
def test_section_responsive_at_tablet_width(page):
    with allure.step("Load the Home Page at 768px and scroll to Our Services"):
        svc = _open_section(page)
        head, tabs, card = svc.head_text_box(), svc.tablist_box(), svc.card_box(0)
        tab = svc.tab_box("all")

    assert svc.is_tablist_visible()
    assert svc.total_card_count() > 0
    assert svc.has_no_horizontal_overflow(), "no horizontal page scroll at 768px"
    assert tabs["y"] >= head["y"] + head["height"] - LAYOUT_TOL, "tab bar should not overlap the heading block"
    assert card["y"] >= tabs["y"] + tabs["height"] - LAYOUT_TOL, "cards should not overlap the tab bar"
    assert tab["height"] >= 24, f"tab should be tappable (>=24px tall), got {tab['height']}"


# ── TC 135341 — responsive at desktop width (1920px) ────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The section is fully responsive at desktop width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135341
@pytest.mark.traceability("ADO-135341")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_section_responsive_at_desktop_width(page):
    with allure.step("Load the Home Page at 1920px and scroll to Our Services"):
        svc = _open_section(page)
        head, tabs, cta, card = svc.head_text_box(), svc.tablist_box(), svc.cta_top_box(), svc.card_box(0)

    assert svc.is_cta_top_visible()
    assert svc.has_no_horizontal_overflow(), "no horizontal page scroll at 1920px"
    assert abs(cta["y"] - head["y"]) <= LAYOUT_TOL, "CTA should sit on the heading row"
    assert cta["x"] > head["x"] + head["width"], "CTA should sit right of the heading block"
    assert tabs["y"] >= head["y"] + head["height"] - LAYOUT_TOL, "tab row should sit below the heading/CTA row"
    assert card["y"] >= tabs["y"] + tabs["height"] - LAYOUT_TOL, "card row should sit below the tab row"
    assert abs(card["x"] - tabs["x"]) <= LAYOUT_TOL, "first card should align with the tab bar's left edge"


# ── TC 135342 — Membership tab filter ───────────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Per-category filter accuracy")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Membership tab filter shows only Membership-assigned cards")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135342
@pytest.mark.traceability("ADO-135342")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_membership_tab_shows_only_membership_cards(page):
    svc = _open_section(page)
    with allure.step("Click the Membership tab"):
        _assert_tab_filter(svc, "membership")


# ── TC 135343 — Legal tab filter ────────────────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Per-category filter accuracy")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Legal tab filter shows only Legal-assigned cards")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135343
@pytest.mark.traceability("ADO-135343")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_legal_tab_shows_only_legal_cards(page):
    svc = _open_section(page)
    with allure.step("Click the Legal tab"):
        _assert_tab_filter(svc, "legal")


# ── TC 135344 — E-Services tab filter ───────────────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Per-category filter accuracy")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("E-Services tab filter shows only E-Services-assigned cards")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135344
@pytest.mark.traceability("ADO-135344")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_eservices_tab_shows_only_eservices_cards(page):
    svc = _open_section(page)
    with allure.step("Click the E-Services tab"):
        _assert_tab_filter(svc, "eservices")


# ── TC 135345 — Information Services tab filter ─────────────────────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Per-category filter accuracy")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Information Services tab filter shows only Information-assigned cards")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135345
@pytest.mark.traceability("ADO-135345")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_information_tab_shows_only_information_cards(page):
    # Live label is "Information" (case: "Information Services") — selected by data-key.
    svc = _open_section(page)
    with allure.step("Click the Information tab"):
        _assert_tab_filter(svc, "information")


# ── TC 135353 — section absent when no service card is published ──────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Section absent when zero cards are published")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Our Services section does not render on the Home Page when no service card is published")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129371
@pytest.mark.tc_135353
@pytest.mark.traceability("ADO-135353")
@pytest.mark.xdist_group("service_card_real_rows")
@pytest.mark.skip(reason=(
    "Not reachable even with a reversible change (run live 2026-10-21, 2 attempts): the first "
    "real card QCDEMO-129371-SERVICE_CARD-01 (48209) cannot be saved at all -- its stored Image "
    "Thumbnail is a .jpg and the field now accepts only .png/.svg, so the Object Authoring submit "
    "is refused (PUT /o/c/servicecards/48209 -> 400 'The file extension \"jpg\" is invalid for "
    "object field \"imageThumbnail\"'; form: 'Image Thumbnail: a .jpg file is not allowed'). "
    "Unticking Active Status would require replacing the real image, which cannot be put back "
    "(the field refuses the original .jpg). Nothing was changed; card 48209 verified unchanged"
))
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_section_not_rendered_when_no_service_card_published(page, real_records):
    """ADO-135353 | PBI 129371.

    Precondition (QA lead instruction 2026-10-21, reversible real writes):
    no service card active + published. A QCTEST card can only add one, so
    EVERY Service Card record that is Active right now (read off the stored
    list at run time -- 17 on 2026-10-21: 16 real cards plus another run's
    leftover `QCTEST-135400-redirect` 842246, treated as real: snapshotted
    and restored, never deleted) gets Active Status unticked, submitted in
    place on the saved TEST_USER session (the Editor login was locked that
    day; a content precondition, not a workflow case). Snapshot + screenshot
    first; `real_records` re-ticks and verifies every card in teardown.
    Public reads: fresh logged-out `page`."""
    svc = HomeServicesPage(page)
    cards = {"slug": "service-card", "plural": "servicecards", "label": "Active Status",
             "api_field": "activeStatus"}

    with allure.step("Baseline (logged out): the Our Services section renders"):
        svc.open_home_settled()
        assert svc.is_section_present(), "baseline: Our Services section not rendered before the change"

    with allure.step("CMS: set Active Status = False on every active service card and publish"):
        active = real_records.codes_where(cards["slug"], cards["plural"], "activeStatus", True, status="approved")
        allure.attach(json.dumps(active), name="active service cards before",
                      attachment_type=allure.attachment_type.JSON)
        assert active, "precondition: no active service card to deactivate"
        for code in active:
            real_records.change(code=code, value=False, **cards)
        still = real_records.codes_where(cards["slug"], cards["plural"], "activeStatus", True, status="approved")
        assert still == [], f"precondition not reached: still active {still}"

    with allure.step("Navigate to the Home page (logged out), polled up to 3 min"):
        def _absent() -> bool:
            svc.open_home_settled()
            return not svc.is_section_present()

        absent = _poll_public(_absent)
        state = {"section_nodes": page.locator(svc.SECTION).count(), "visible": svc.is_section_visible(),
                 "cards": page.locator(svc.CARD).count()}
        allure.attach(json.dumps(state), name="135353 evidence", attachment_type=allure.attachment_type.JSON)
        allure.attach(page.screenshot(full_page=True), name="Home, zero active service cards",
                      attachment_type=allure.attachment_type.PNG)

    # Assert
    assert absent, f"the Our Services section should be absent entirely; observed {state}"


def _poll_public(predicate, timeout: float = 180.0, poll: float = 10.0) -> bool:
    """Public propagation poll (QA lead: a change landing within 3 min is fine)."""
    from core.utils.waits import WaitTimeoutError, wait_until

    try:
        wait_until(predicate, timeout=timeout, poll=poll)
        return True
    except WaitTimeoutError:
        return False


# ── TC 135414 — CTA absent when the listing page is unpublished ────────────
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("CTA hidden when its target page is unpublished")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The View All Services CTA does not appear when the Our Services listing page is unpublished")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.edge
@pytest.mark.pbi_129371
@pytest.mark.tc_135414
@pytest.mark.traceability("ADO-135414")
@pytest.mark.skip(reason=(
    "Not reachable even with a reversible change (re-checked 2026-10-21): the Our Services "
    "listing page is the Liferay SITE PAGE /web/qatar-chamber/our-services (Pages layer), not a "
    "content record -- the live Object Authoring sidebar has no object behind it (only Service "
    "Card / Filter Tab / Our Services Section / Tab Mapping, and Member Services Page for "
    "/our-services/member-services). Unpublishing a page is a layout change, which CLAUDE.md #6 "
    "and standards.md ('Fragments and Page Layout Are Off-Limits') forbid outright; no QCTEST "
    "record can produce the state"
))
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_view_all_cta_not_rendered_when_listing_page_unpublished(page):
    svc = _open_section(page)
    assert not svc.is_cta_top_visible(), "the View All Services CTA should not render"

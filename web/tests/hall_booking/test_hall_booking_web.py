"""
web/tests/hall_booking/test_hall_booking_web.py — Web-tagged (Platform=Web,
NO Control_Panel) cases for PBI 129411 (QC-SVC-014 — Hall Booking), sourced
from Azure DevOps suite 140080 (plan 137724). These are the 10 public-facing
UI cases already filtered down to `Tag=Web` with no `Control_Panel` tag —
pure public-site behavior, no CMS/admin steps.

All 10 carry the `Regression` QA tag (main functional scenarios for this
feature) and the `Web` Platform tag; several also carry `UAT`, `RTL`,
`Arabic` (tc_140040 only) or explicit priority notes — reflected below as
`@pytest.mark.regression` + `@pytest.mark.web` + `@pytest.mark.svc`
(SVC service/module — Halls Reservation lives under "Our Services" per
standards.md's Service/Module Codes table) + the matching Category
(`functional_low`/`functional_high`) marker, plus `rtl`/`arabic` on
tc_140040. `UAT` itself carries no pytest marker per
automation-standards.md (it drives the client doc, not a pytest slice).

CAPTCHA (tc_140016 / tc_140019 / tc_140045): see
web/pages/hall_booking/hall_booking_page.py's module docstring for the full,
live-confirmed evidence trail (Google reCAPTCHA Enterprise, INVISIBLE mode,
no checkbox/challenge UI exists to interact with; client-side field
validation intercepts before it ever executes on the two negative cases, and
it was confirmed live to pass silently on tc_140045's real submission from
this same scripted, headless session). No prior automated webform test in
this repo (`web/` or `cms/`) had an established CAPTCHA-handling pattern —
none was found on grep — so `submit_request()` simply clicks Submit; nothing
is being overridden or invented beyond that.

Disposable test data: every field filled in tc_140016/tc_140019/tc_140045
uses an obviously-fake `QCTEST-` prefixed value (or a syntactically-valid
but clearly-fake `qctest.hallbooking@example.com`/`5550xxxx` for the
fields whose input type requires a realistic-shaped value), per this
project's disposable-test-data convention for a live shared qcdev
environment. tc_140045 creates one real, disposable Hall Booking
submission record (no teardown path/admin surface for this object was in
scope for this Web-only batch) — consistent with the read-mostly nature
expected of this batch per the task's own constraints.

===========================================================================
VISUAL/RENDERING BATCH (2026-09-16) — 15 more Web-only cases, added below
===========================================================================
The QA Manager identified 17 more cases from the same Azure suite that are
about visual/rendering appearance (images, icons, rich-text markup, badges,
gallery media) rather than field-validation logic. All 17 were originally
written as CMS-write-then-verify-on-Web cases (dual-tagged `Web` AND
`Control_Panel`). Per explicit instruction, NO Control_Panel work was done
for this batch (no CMS login, no Object Authoring, no content mutation) —
every one of the 15 tests below is scoped down to "verify the CURRENTLY
already-published rendering on the live public page exactly as it exists
today," treating each case's "...is saved and rendered..." wording as
"...is CURRENTLY rendered...".

Of the 17, TWO were NOT automated at all and carry no test here — 139946
and 139997 — because they inherently require a CMS-created EMPTY-value
precondition that has no live counterpart on the published page. Left for
the QA Manager to mark Not Applicable in Azure.

All locators used below came from a disclosed, scripted CLI probe (a plain
Playwright script run in the shell, not the Playwright MCP —
`tools/extract_locators.py` only harvests interactive/labelled elements and
does not surface `<img>`/CSS-mask-icon/rich-text containers at all) — see
`web/pages/hall_booking/hall_booking_page.py`'s own "VISUAL/RENDERING
BATCH" docstring section for the full live-confirmed DOM evidence trail
this batch's Page-Object methods are built on.

Markers: these are appearance/rendering checks, not MAIN functional
scenarios, so none carry `@pytest.mark.regression` (mirrors standards.md's
"do not tag deep field-validation/cosmetic cases as Regression" guidance,
extended here to rendering-appearance checks for the same reason). All
carry `@pytest.mark.web` + `@pytest.mark.svc` (same SVC module as the rest
of this file) + `@pytest.mark.ui` (Category axis — visual/rendering) +
`@pytest.mark.pbi_129411` + their own `tc_<id>`.

Of the 15, 14 are real, live-confirmed PASSing checks. ONE — tc_139856
(Hero Description rich text) — is SKIPPED, not scripted as a pass: the
Hero Description field is confirmed live to be a PLAIN text field (no
`qc-hb-rt` rich-text wrapper, unlike every sibling body-copy field on this
page), and its current content has no rich-text markup at all to verify
rendering of. This is a genuine live-data/architecture gap, disclosed
honestly per this project's Result Integrity rule rather than papered over
with a fabricated pass.
"""

import allure
import pytest

from web.pages.hall_booking.hall_booking_page import (
    HALL_NAME_GRAND,
    HALL_NAME_SHEIKH_NASSER,
    HALLS_BOOKING_PATH,
    HOME_PATH,
    HallBookingPage,
)

SERVICES_PATH = "/web/qatar-chamber/our-services"


def _is_arabic_text(text: str) -> bool:
    return any("؀" <= ch <= "ۿ" for ch in text)


# ---------------------------------------------------------------------------
# 139866 — Reserve a Hall CTA opens the modal with no hall pre-selected
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Reservation modal — CTA behavior")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reserve a Hall CTA opens the reservation modal with no hall pre-selected")
@allure.label("pbi", "129411")
@allure.label("testcase", "139866")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129411
@pytest.mark.tc_139866
@pytest.mark.traceability("139866")
def test_hall_booking_hero_cta_opens_modal_unselected(page):
    """QA traceability: SVC-HALLBOOKING-TC-139866 (Azure Test Case 139866)."""
    hb_page = HallBookingPage(page)

    # Arrange
    with allure.step("Open the public Halls Booking page in English"):
        hb_page.open_halls_booking()
    assert hb_page.is_hero_cta_visible()
    url_before = page.url

    # Act
    with allure.step("Click Reserve a Hall in the hero"):
        hb_page.click_hero_cta()
        hb_page.wait_for_modal_open()

    # Assert: modal opened over the page, no reload
    assert hb_page.is_modal_open()
    assert page.url == url_before
    assert hb_page.selected_hall_value() == ""

    with allure.step("Close the modal and click Reserve a Hall again"):
        hb_page.close_modal()
        hb_page.click_hero_cta()
        hb_page.wait_for_modal_open()

    # Assert: reopens in the same unselected state
    assert hb_page.selected_hall_value() == ""


# ---------------------------------------------------------------------------
# 140016 — submitting with an empty Email Address is blocked
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Reservation form — mandatory field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Submitting the reservation request with an empty Email Address is blocked")
@allure.label("pbi", "129411")
@allure.label("testcase", "140016")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129411
@pytest.mark.tc_140016
@pytest.mark.traceability("140016")
def test_hall_booking_submit_blocked_when_email_missing(page):
    """QA traceability: SVC-HALLBOOKING-TC-140016 (Azure Test Case 140016)."""
    hb_page = HallBookingPage(page)

    # Arrange
    with allure.step("Open the page and click Reserve a Hall to open the modal"):
        hb_page.open_halls_booking()
        hb_page.click_hero_cta()
        hb_page.wait_for_modal_open()

    with allure.step("Complete every mandatory field except Email Address"):
        filled = hb_page.fill_all_mandatory_fields(exclude=("emailAddress",))
    assert hb_page.field_value("companyEnglishName") == filled["companyEnglishName"]
    assert hb_page.field_value("emailAddress") == ""

    # Act
    with allure.step("Pass the CAPTCHA (invisible/automatic — see module docstring) and click Submit Request"):
        hb_page.submit_request()
        hb_page.wait_for_field_error("emailAddress")

    # Assert: blocked with an inline error on Email Address, modal stays open
    assert hb_page.is_field_error_visible("emailAddress")
    assert hb_page.field_error_text("emailAddress") != ""
    assert hb_page.is_form_view_visible()
    assert not hb_page.is_success_view_visible()

    # Assert: every other field still holds its entered value
    assert hb_page.field_value("companyEnglishName") == filled["companyEnglishName"]
    assert hb_page.field_value("companyArabicName") == filled["companyArabicName"]
    assert hb_page.field_value("commercialRegistrationNumber") == filled["commercialRegistrationNumber"]
    assert hb_page.field_value("mobileNumber") == filled["mobileNumber"]
    assert hb_page.selected_hall_value() == filled["selectedHall"]


# ---------------------------------------------------------------------------
# 140019 — submitting with an empty Mobile Number is blocked
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Reservation form — mandatory field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Submitting the reservation request with an empty Mobile Number is blocked")
@allure.label("pbi", "129411")
@allure.label("testcase", "140019")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129411
@pytest.mark.tc_140019
@pytest.mark.traceability("140019")
def test_hall_booking_submit_blocked_when_mobile_missing(page):
    """QA traceability: SVC-HALLBOOKING-TC-140019 (Azure Test Case 140019)."""
    hb_page = HallBookingPage(page)

    # Arrange
    with allure.step("Open the page and click Reserve a Hall to open the modal"):
        hb_page.open_halls_booking()
        hb_page.click_hero_cta()
        hb_page.wait_for_modal_open()

    with allure.step("Complete every mandatory field except Mobile Number"):
        filled = hb_page.fill_all_mandatory_fields(exclude=("mobileNumber",))
    assert hb_page.field_value("companyEnglishName") == filled["companyEnglishName"]
    assert hb_page.field_value("mobileNumber") == ""

    # Act
    with allure.step("Pass the CAPTCHA (invisible/automatic — see module docstring) and click Submit Request"):
        hb_page.submit_request()
        hb_page.wait_for_field_error("mobileNumber")

    # Assert: blocked with an inline error on Mobile Number, modal stays open
    assert hb_page.is_field_error_visible("mobileNumber")
    assert hb_page.field_error_text("mobileNumber") != ""
    assert hb_page.is_form_view_visible()
    assert not hb_page.is_success_view_visible()

    # Assert: every other field still holds its entered value
    assert hb_page.field_value("companyEnglishName") == filled["companyEnglishName"]
    assert hb_page.field_value("companyArabicName") == filled["companyArabicName"]
    assert hb_page.field_value("commercialRegistrationNumber") == filled["commercialRegistrationNumber"]
    assert hb_page.field_value("emailAddress") == filled["emailAddress"]


# ---------------------------------------------------------------------------
# 140024 — opening the modal from a hall card pre-selects that hall
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Reservation modal — CTA behavior")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Opening the reservation modal from a hall card pre-selects that hall")
@allure.label("pbi", "129411")
@allure.label("testcase", "140024")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129411
@pytest.mark.tc_140024
@pytest.mark.traceability("140024")
def test_hall_booking_hall_card_preselects_hall(page):
    """QA traceability: SVC-HALLBOOKING-TC-140024 (Azure Test Case 140024)."""
    hb_page = HallBookingPage(page)

    # Arrange
    with allure.step("Open the public Halls Booking page in English"):
        hb_page.open_halls_booking()
    assert hb_page.hall_card_count() >= 2

    with allure.step("Scroll to Section 03 Available Halls and note the second hall's name"):
        second_hall_name = hb_page.hall_name_at(1)
    assert second_hall_name == HALL_NAME_GRAND  # live-confirmed order (see Page Object docstring)

    # Act
    with allure.step("Click 'Select for reservation' on that hall's card"):
        hb_page.click_select_for_reservation(1)
        hb_page.wait_for_modal_open()

    # Assert: pre-selected with exactly that hall — not the first hall, not the placeholder
    assert hb_page.is_modal_open()
    assert hb_page.selected_hall_value() == second_hall_name
    assert hb_page.selected_hall_value() != ""
    assert hb_page.selected_hall_value() != HALL_NAME_SHEIKH_NASSER


# ---------------------------------------------------------------------------
# 140037 — reached from the main menu, every published section renders
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Page structure — all published sections render")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Visitor reaches the Halls Booking page from the main menu and sees every published section")
@allure.label("pbi", "129411")
@allure.label("testcase", "140037")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129411
@pytest.mark.tc_140037
@pytest.mark.traceability("140037")
def test_hall_booking_reachable_from_main_menu_all_sections_render(page):
    """QA traceability: SVC-HALLBOOKING-TC-140037 (Azure Test Case 140037)."""
    hb_page = HallBookingPage(page)

    # Act
    with allure.step("Open the Qatar Chamber website, click Our Services > Halls Booking in the main menu"):
        hb_page.navigate_via_main_menu()

    # Assert: landed on the Halls Booking page
    assert page.url.rstrip("/").endswith(HALLS_BOOKING_PATH)

    # Assert: breadcrumb, eyebrow, title, description, hero CTA
    assert hb_page.is_breadcrumb_visible()
    breadcrumb = hb_page.breadcrumb_text()
    assert "Home" in breadcrumb
    assert "Services" in breadcrumb
    assert hb_page.eyebrow_text() == "Facilities Reservation Service"
    assert hb_page.page_title_text() == "Halls Booking"
    assert hb_page.hero_desc_text() != ""
    assert hb_page.is_hero_cta_visible()

    # Assert: quick facts
    facts_text = hb_page.quick_facts_text()
    assert "Available Halls" in facts_text and "3 Halls" in facts_text
    assert "Largest Capacity" in facts_text and "140 Guests" in facts_text
    assert "Suitable Events" in facts_text and "Business & Corporate" in facts_text
    assert "Reservation Method" in facts_text and "Online Request" in facts_text

    # Assert: sticky index lists all 4 sections
    labels = hb_page.index_item_labels()
    assert len(labels) == 4
    assert any("Overview" in label for label in labels)
    assert any("Reservation Guidelines" in label for label in labels)
    assert any("Available Halls" in label for label in labels)
    assert any("Media Gallery" in label for label in labels)

    # Assert: all four sections render
    assert hb_page.is_section_visible(hb_page.SECTION_01_OVERVIEW)
    assert hb_page.is_section_visible(hb_page.SECTION_02_GUIDELINES)
    assert hb_page.is_section_visible(hb_page.SECTION_03_HALLS)
    assert hb_page.is_section_visible(hb_page.SECTION_04_GALLERY)

    # Assert: closing "Ready to reserve a hall" banner
    assert hb_page.is_visible(hb_page.BANNER)
    assert "Ready to reserve a hall" in hb_page.banner_text()


# ---------------------------------------------------------------------------
# 140038 — clicking a section-index entry scrolls to that section and marks it active
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Sticky section index")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a section-index entry scrolls to that section and marks it active")
@allure.label("pbi", "129411")
@allure.label("testcase", "140038")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129411
@pytest.mark.tc_140038
@pytest.mark.traceability("140038")
def test_hall_booking_section_index_click_scrolls_and_marks_active(page):
    """QA traceability: SVC-HALLBOOKING-TC-140038 (Azure Test Case 140038)."""
    hb_page = HallBookingPage(page)

    # Arrange
    with allure.step("Open the page"):
        hb_page.open_halls_booking()
    assert hb_page.is_section_index_visible()

    # Act
    with allure.step("Click '03 Available Halls' in the sticky index"):
        hb_page.click_index_item(2)

    # Assert: '03 Available Halls' is marked active, index stays sticky
    assert "Available Halls" in hb_page.active_index_text()
    assert hb_page.is_index_item_active(2)
    assert hb_page.is_section_index_visible()

    # Act: scroll back up via real wheel events (see Page Object docstring —
    # a synthetic window.scrollTo() does NOT trigger this scroll-spy)
    with allure.step("Scroll back up to the top of the page"):
        hb_page.scroll_by_wheel(-400, steps=20)

    # Assert: the active marker followed the section back into view
    assert not hb_page.is_index_item_active(2)


# ---------------------------------------------------------------------------
# 140039 — breadcrumb links navigate to their targets
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Breadcrumb navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Breadcrumb links on the Halls Booking hero navigate to their targets")
@allure.label("pbi", "129411")
@allure.label("testcase", "140039")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129411
@pytest.mark.tc_140039
@pytest.mark.traceability("140039")
def test_hall_booking_breadcrumb_links_navigate(page):
    """QA traceability: SVC-HALLBOOKING-TC-140039 (Azure Test Case 140039, Priority 2)."""
    hb_page = HallBookingPage(page)

    # Arrange
    with allure.step("Open the page"):
        hb_page.open_halls_booking()

    # Assert: breadcrumb shows Home icon, Home, separator, Services — no Figma placeholder text
    breadcrumb_text = hb_page.breadcrumb_text()
    assert "Home" in breadcrumb_text
    assert "Services" in breadcrumb_text
    assert "Hcvxcxvcome" not in breadcrumb_text

    # Act
    with allure.step("Click 'Home' breadcrumb link"):
        hb_page.click_breadcrumb_home()

    # Assert: navigates to the Qatar Chamber home page
    assert page.url.rstrip("/").endswith(HOME_PATH)

    # Act
    with allure.step("Navigate back and click 'Services' breadcrumb link"):
        hb_page.open_halls_booking()
        hb_page.click_breadcrumb_services()

    # Assert: navigates to the Services landing page
    assert page.url.rstrip("/").endswith(SERVICES_PATH)


# ---------------------------------------------------------------------------
# 140040 — language toggle switches the page and the modal between EN/AR
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Language toggle switches the whole page and the modal between English and Arabic")
@allure.label("pbi", "129411")
@allure.label("testcase", "140040")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.rtl
@pytest.mark.arabic
@pytest.mark.pbi_129411
@pytest.mark.tc_140040
@pytest.mark.traceability("140040")
def test_hall_booking_language_toggle_switches_page_and_modal(page):
    """QA traceability: SVC-HALLBOOKING-TC-140040 (Azure Test Case 140040)."""
    hb_page = HallBookingPage(page)

    # Arrange
    with allure.step("Open the page in English"):
        hb_page.open_halls_booking()
    assert hb_page.html_dir() != "rtl"
    assert hb_page.page_title_text() == "Halls Booking"

    # Act
    with allure.step("Click the AR language toggle in the header"):
        hb_page.click_language_toggle()

    # Assert: page reloads in Arabic, RTL
    assert hb_page.html_dir() == "rtl"
    assert _is_arabic_text(hb_page.page_title_text())
    assert _is_arabic_text(hb_page.eyebrow_text())
    assert hb_page.is_section_visible(hb_page.SECTION_01_OVERVIEW)
    assert hb_page.is_section_visible(hb_page.SECTION_02_GUIDELINES)
    assert hb_page.is_section_visible(hb_page.SECTION_03_HALLS)
    assert hb_page.is_section_visible(hb_page.SECTION_04_GALLERY)
    assert _is_arabic_text(hb_page.hall_name_at(0))

    # Act: open the modal, inspect it in RTL, then switch back to EN
    with allure.step("Open the reservation modal and inspect it in Arabic"):
        hb_page.click_hero_cta()
        hb_page.wait_for_modal_open()

    assert hb_page.modal_dialog_direction() == "rtl"
    assert _is_arabic_text(hb_page.modal_title_text())

    with allure.step("Close the modal and click the EN toggle"):
        hb_page.close_modal()
        hb_page.click_language_toggle()

    # Assert: page returns to English, LTR
    assert hb_page.html_dir() != "rtl"
    assert hb_page.page_title_text() == "Halls Booking"


# ---------------------------------------------------------------------------
# 140041 — clicking a Reservation Guidelines question expands/collapses it
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Reservation Guidelines accordion")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a Reservation Guidelines question expands it, a second click collapses it")
@allure.label("pbi", "129411")
@allure.label("testcase", "140041")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129411
@pytest.mark.tc_140041
@pytest.mark.traceability("140041")
def test_hall_booking_accordion_expand_collapse(page):
    """QA traceability: SVC-HALLBOOKING-TC-140041 (Azure Test Case 140041)."""
    hb_page = HallBookingPage(page)

    # Arrange
    with allure.step("Open the page and scroll to Section 02 Reservation Guidelines"):
        hb_page.open_halls_booking()
    assert hb_page.accordion_item_count() >= 1
    assert not hb_page.is_accordion_expanded(0)
    assert hb_page.is_accordion_body_hidden(0)
    url_before = page.url

    # Act
    with allure.step("Click the first guideline"):
        hb_page.click_accordion_item(0)

    # Assert: expands, no reload, no URL change
    assert hb_page.is_accordion_expanded(0)
    assert not hb_page.is_accordion_body_hidden(0)
    assert hb_page.accordion_body_text(0) != ""
    assert page.url == url_before

    # Act
    with allure.step("Click the same guideline again"):
        hb_page.click_accordion_item(0)

    # Assert: collapses again
    assert not hb_page.is_accordion_expanded(0)
    assert hb_page.is_accordion_body_hidden(0)


# ---------------------------------------------------------------------------
# 140045 — Done button on the success screen returns the visitor to the page
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Reservation form — successful submission")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Done button on the success screen returns the visitor to the Halls Booking page")
@allure.label("pbi", "129411")
@allure.label("testcase", "140045")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129411
@pytest.mark.tc_140045
@pytest.mark.traceability("140045")
def test_hall_booking_success_screen_done_returns_to_page(page):
    """QA traceability: SVC-HALLBOOKING-TC-140045 (Azure Test Case 140045)."""
    hb_page = HallBookingPage(page)

    # Arrange
    with allure.step("Open the page and click Reserve a Hall to open the modal"):
        hb_page.open_halls_booking()
        scroll_before = page.evaluate("() => window.scrollY")
        hb_page.click_hero_cta()
        hb_page.wait_for_modal_open()

    # Act
    with allure.step("Complete and submit the request (disposable QCTEST- data, CAPTCHA is invisible/automatic)"):
        hb_page.fill_all_mandatory_fields()
        hb_page.submit_request()
        hb_page.wait_for_success_view()

    # Assert: success screen with a reference number
    assert hb_page.is_success_view_visible()
    assert not hb_page.is_form_view_visible()
    reference = hb_page.success_reference_text()
    assert reference != ""

    # Act
    with allure.step("Click Done on the success screen"):
        hb_page.click_done()
        hb_page.wait_for_modal_closed()

    # Assert: success screen closes, Halls Booking page visible again at its
    # previous scroll position (the case's own steps never scroll away from
    # the top before opening the modal, so the previous position is the top)
    assert not hb_page.is_modal_open()
    assert hb_page.is_hero_cta_visible()
    scroll_after = page.evaluate("() => window.scrollY")
    assert scroll_after == scroll_before

    # Act
    with allure.step("Reopen the modal"):
        hb_page.click_hero_cta()
        hb_page.wait_for_modal_open()

    # Assert: reopening presents an empty form, not the submitted values or the success screen
    assert hb_page.is_form_view_visible()
    assert not hb_page.is_success_view_visible()
    assert hb_page.field_value("companyEnglishName") == ""
    assert hb_page.field_value("emailAddress") == ""
    assert hb_page.selected_hall_value() == ""


# ===========================================================================
# VISUAL/RENDERING BATCH (2026-09-16) — see module docstring's own section
# ===========================================================================

# ---------------------------------------------------------------------------
# 139856 — Hero Description rich text markup (SKIPPED — live-data/
# architecture gap, see module + Page-Object docstrings)
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — rich text")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Hero Description renders its rich-text markup")
@allure.label("pbi", "129411")
@allure.label("testcase", "139856")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139856
@pytest.mark.traceability("139856")
@pytest.mark.skip(
    reason="Live-data/architecture gap: the Hero Description field "
    "(p.qc-hb-hero-desc) is confirmed live to be a PLAIN text field, not a "
    "rich-text field — it carries no `qc-hb-rt` wrapper class, unlike every "
    "sibling body-copy field on this page (Overview Body, Halls Intro, Hall "
    "Description, Banner Body all do). Its current content is a single "
    "unformatted sentence with no bold/italic/list/link markup to verify "
    "rendering of. Not automated as a pass; requires Control_Panel access "
    "to confirm whether this is expected (plain-text-by-design) or a "
    "missed rich-text field — out of scope for this Web-only batch."
)
def test_hall_booking_hero_description_rich_text(page):
    """QA traceability: SVC-HALLBOOKING-TC-139856 (Azure Test Case 139856).
    SKIPPED — see skip reason above."""
    hb_page = HallBookingPage(page)
    hb_page.open_halls_booking()
    assert hb_page.hero_desc_text() != ""


# ---------------------------------------------------------------------------
# 139859 — Hero Banner image renders
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — images")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero Banner image renders with a valid, loaded source")
@allure.label("pbi", "129411")
@allure.label("testcase", "139859")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139859
@pytest.mark.traceability("139859")
def test_hall_booking_hero_image_renders(page):
    """QA traceability: SVC-HALLBOOKING-TC-139859 (Azure Test Case 139859)."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the public Halls Booking page"):
        hb_page.open_halls_booking()

    with allure.step("Inspect the hero banner image"):
        state = hb_page.hero_image_state()

    # Assert: a real, loaded photo — not a broken/missing image
    assert state["exists"], "hero banner <img> not found in the DOM"
    assert state["src"] != ""
    assert state["loaded"] is True
    assert state["width"] > 0
    assert state["height"] > 0


# ---------------------------------------------------------------------------
# 139869 — Quick-Fact icons render
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — icons")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Each Quick-Fact item shows a real icon graphic, not a broken/missing icon")
@allure.label("pbi", "129411")
@allure.label("testcase", "139869")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139869
@pytest.mark.traceability("139869")
def test_hall_booking_quick_fact_icons_render(page):
    """QA traceability: SVC-HALLBOOKING-TC-139869 (Azure Test Case 139869).
    Icons here are a CSS mask-icon pattern (`.qc-hb-fact-icon .qc-hb-mask`,
    `mask-image: url(...)`), not `<img>`/`<svg>` — see Page Object docstring."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page"):
        hb_page.open_halls_booking()

    with allure.step("Inspect all 4 quick-fact icons (Available Halls, Largest "
                      "Capacity, Suitable Events, Reservation Method)"):
        fact_count = hb_page.fact_count()
        assert fact_count == 4
        states = [hb_page.fact_icon_state(i) for i in range(fact_count)]

    # Assert: every fact shows a real, non-broken icon graphic
    for i, state in enumerate(states):
        assert state["exists"], f"quick-fact {i} has no icon element"
        assert state["mask_image"] not in ("none", ""), f"quick-fact {i} icon has no mask-image"
        assert state["width"] > 0 and state["height"] > 0, f"quick-fact {i} icon has zero size"


# ---------------------------------------------------------------------------
# 139887 — Section Numbering renders as a two-digit badge
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — section numbering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Each sticky section-index entry shows its number as a zero-padded two-digit badge")
@allure.label("pbi", "129411")
@allure.label("testcase", "139887")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139887
@pytest.mark.traceability("139887")
def test_hall_booking_section_numbering_badges(page):
    """QA traceability: SVC-HALLBOOKING-TC-139887 (Azure Test Case 139887)."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page"):
        hb_page.open_halls_booking()

    with allure.step("Read the numbering badge of each of the 4 section-index entries"):
        labels = hb_page.index_item_labels()
        assert len(labels) == 4
        numbers = [hb_page.index_item_number_text(i) for i in range(4)]

    # Assert: zero-padded two-digit badges, in order, matching 01..04
    assert numbers == ["01", "02", "03", "04"]
    for n in numbers:
        assert len(n) == 2 and n.isdigit()


# ---------------------------------------------------------------------------
# 139901 — Overview Body rich text renders its markup
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — rich text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 01 Overview body renders its rich-text markup, no raw tags leaking through")
@allure.label("pbi", "129411")
@allure.label("testcase", "139901")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139901
@pytest.mark.traceability("139901")
def test_hall_booking_overview_body_rich_text(page):
    """QA traceability: SVC-HALLBOOKING-TC-139901 (Azure Test Case 139901).
    Current live content exercises only <p> paragraphs (no bold/italic/list/
    link instance exists on this page today) — the assertion below is
    scoped to what IS live: real parsed formatting elements, non-empty
    text, and no literal tag leakage — not a specific bold/italic/list/link
    check, since none currently exists to check."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and inspect Section 01's Overview body"):
        hb_page.open_halls_booking()
        state = hb_page.overview_body_state()

    assert state["exists"], "Overview body rich-text container not found"
    assert state["visible"] is True
    assert state["inner_text"].strip() != ""
    assert state["formatted_element_count"] >= 1
    assert state["has_raw_tag_leak"] is False


# ---------------------------------------------------------------------------
# 139904 — Checklist Card icons render
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — icons")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Each Section 01 checklist card shows a real icon graphic")
@allure.label("pbi", "129411")
@allure.label("testcase", "139904")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139904
@pytest.mark.traceability("139904")
def test_hall_booking_checklist_card_icons_render(page):
    """QA traceability: SVC-HALLBOOKING-TC-139904 (Azure Test Case 139904).
    Same CSS mask-icon pattern as the quick facts — see Page Object docstring."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and inspect Section 01's checklist cards"):
        hb_page.open_halls_booking()
        card_count = hb_page.checklist_card_count()
        assert card_count >= 1
        states = [hb_page.checklist_card_icon_state(i) for i in range(card_count)]

    for i, state in enumerate(states):
        assert state["exists"], f"checklist card {i} has no icon element"
        assert state["mask_image"] not in ("none", ""), f"checklist card {i} icon has no mask-image"
        assert state["width"] > 0 and state["height"] > 0, f"checklist card {i} icon has zero size"


# ---------------------------------------------------------------------------
# 139930 — Guideline Content rich text renders its markup (after expanding)
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — rich text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An expanded Reservation Guideline renders its rich-text markup, no raw tags leaking through")
@allure.label("pbi", "129411")
@allure.label("testcase", "139930")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139930
@pytest.mark.traceability("139930")
def test_hall_booking_guideline_content_rich_text(page):
    """QA traceability: SVC-HALLBOOKING-TC-139930 (Azure Test Case 139930).
    Reuses tc_140041's accordion-expand interaction. DISCLOSED CONTENT
    CAVEAT (confirmed live via DOM probe): all 5 accordion bodies currently
    render the identical literal placeholder copy "[Content pending] No
    body copy for this guideline exists in the approved Figma design... To
    be supplied by the Product Owner." This test asserts on the RENDERING
    MECHANISM (the placeholder text itself renders cleanly as real markup,
    no tag leakage) — it does not, and cannot, assert on final guideline
    copy or a specific bold/italic/list/link instance, since none exists
    live today."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and expand the first Reservation Guideline"):
        hb_page.open_halls_booking()
        hb_page.click_accordion_item(0)
        assert hb_page.is_accordion_expanded(0)

    with allure.step("Inspect the expanded guideline's body content"):
        state = hb_page.accordion_body_state(0)

    assert state["exists"]
    assert state["visible"] is True
    assert state["inner_text"].strip() != ""
    assert state["formatted_element_count"] >= 1
    assert state["has_raw_tag_leak"] is False


# ---------------------------------------------------------------------------
# 139945 — Halls Section Intro rich text renders its markup
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — rich text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 03's intro paragraph renders its rich-text markup, no raw tags leaking through")
@allure.label("pbi", "129411")
@allure.label("testcase", "139945")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139945
@pytest.mark.traceability("139945")
def test_hall_booking_halls_section_intro_rich_text(page):
    """QA traceability: SVC-HALLBOOKING-TC-139945 (Azure Test Case 139945).
    A real intro paragraph IS present live (confirmed via DOM probe):
    "Review hall specs, capacity, and select the ideal hall for your
    event" — not a live-data gap."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and inspect Section 03's intro"):
        hb_page.open_halls_booking()
        state = hb_page.halls_intro_state()

    assert state["exists"], "Section 03 intro rich-text container not found"
    assert state["visible"] is True
    assert state["inner_text"].strip() != ""
    assert state["formatted_element_count"] >= 1
    assert state["has_raw_tag_leak"] is False


# ---------------------------------------------------------------------------
# 139951 — Hall Image renders
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — images")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Each hall card in Section 03 shows a real, loaded hall image")
@allure.label("pbi", "129411")
@allure.label("testcase", "139951")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139951
@pytest.mark.traceability("139951")
def test_hall_booking_hall_images_render(page):
    """QA traceability: SVC-HALLBOOKING-TC-139951 (Azure Test Case 139951)."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and inspect every hall card's image"):
        hb_page.open_halls_booking()
        hall_count = hb_page.hall_card_count()
        assert hall_count >= 1
        states = [hb_page.hall_image_state(i) for i in range(hall_count)]

    for i, state in enumerate(states):
        assert state["exists"], f"hall card {i} has no image element"
        assert state["src"] != "", f"hall card {i} image has no src"
        assert state["loaded"] is True, f"hall card {i} image did not load (broken/placeholder)"
        assert state["width"] > 0 and state["height"] > 0, f"hall card {i} image has zero size"


# ---------------------------------------------------------------------------
# 139954 — Hall Description rich text renders its markup
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — rich text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Each hall card's description renders its rich-text markup, no raw tags leaking through")
@allure.label("pbi", "129411")
@allure.label("testcase", "139954")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139954
@pytest.mark.traceability("139954")
def test_hall_booking_hall_description_rich_text(page):
    """QA traceability: SVC-HALLBOOKING-TC-139954 (Azure Test Case 139954).
    Every hall card exposes its description directly in the card body
    (`.qc-hb-hall-desc`) — confirmed live as the only surface this content
    is exposed on; there is no separate detail-expansion for it."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and inspect every hall card's description"):
        hb_page.open_halls_booking()
        hall_count = hb_page.hall_card_count()
        assert hall_count >= 1
        states = [hb_page.hall_description_state(i) for i in range(hall_count)]

    for i, state in enumerate(states):
        assert state["exists"], f"hall card {i} has no description container"
        assert state["visible"] is True
        assert state["inner_text"].strip() != "", f"hall card {i} description is empty"
        assert state["formatted_element_count"] >= 1
        assert state["has_raw_tag_leak"] is False


# ---------------------------------------------------------------------------
# 139957 — Capacity renders as the hall's capacity badge
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — badges")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Each hall card shows its capacity as a distinct visual badge, not plain inline text")
@allure.label("pbi", "129411")
@allure.label("testcase", "139957")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139957
@pytest.mark.traceability("139957")
def test_hall_booking_capacity_badge_renders(page):
    """QA traceability: SVC-HALLBOOKING-TC-139957 (Azure Test Case 139957).
    Live text is "N Persons" (e.g. "140 Persons"), not the task's
    illustrative "up to N guests" wording — the case is about the capacity
    being rendered as a distinct visual badge element (its own class, its
    own icon), not the exact copy, so the wording difference is not a
    defect here."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and inspect every hall card's capacity badge"):
        hb_page.open_halls_booking()
        hall_count = hb_page.hall_card_count()
        assert hall_count >= 1

    for i in range(hall_count):
        badge_text = hb_page.hall_capacity_badge_text(i)
        assert badge_text.strip() != "", f"hall card {i} has no capacity text"
        assert any(ch.isdigit() for ch in badge_text), f"hall card {i} capacity has no number: {badge_text!r}"
        assert hb_page.is_hall_capacity_badge_distinct(i), (
            f"hall card {i} capacity is not rendered as its own distinct badge element"
        )


# ---------------------------------------------------------------------------
# 139983 — Image/Video Thumbnail renders in the Media Gallery
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — media gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Every Media Gallery tile shows a real, loaded thumbnail")
@allure.label("pbi", "129411")
@allure.label("testcase", "139983")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139983
@pytest.mark.traceability("139983")
def test_hall_booking_gallery_thumbnails_render(page):
    """QA traceability: SVC-HALLBOOKING-TC-139983 (Azure Test Case 139983).
    All 3 live gallery tiles are photo-album tiles (each backed by a real
    hall photo as its thumbnail) — none is a bare single image/video tile
    today, but the ask ("gallery tiles show real loaded thumbnails")
    applies identically to an album tile's own thumbnail image."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and inspect every gallery tile's thumbnail"):
        hb_page.open_halls_booking()
        tile_count = hb_page.gallery_tile_count()
        assert tile_count >= 1
        states = [hb_page.gallery_tile_thumbnail_state(i) for i in range(tile_count)]

    for i, state in enumerate(states):
        assert state["exists"], f"gallery tile {i} has no thumbnail image"
        assert state["src"] != "", f"gallery tile {i} thumbnail has no src"
        assert state["loaded"] is True, f"gallery tile {i} thumbnail did not load (broken/placeholder)"


# ---------------------------------------------------------------------------
# 139996 — Banner Body rich text renders its markup
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — rich text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The bottom 'Ready to reserve a hall' banner body renders its rich-text markup")
@allure.label("pbi", "129411")
@allure.label("testcase", "139996")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_139996
@pytest.mark.traceability("139996")
def test_hall_booking_banner_body_rich_text(page):
    """QA traceability: SVC-HALLBOOKING-TC-139996 (Azure Test Case 139996)."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and inspect the bottom banner's body"):
        hb_page.open_halls_booking()
        state = hb_page.banner_body_state()

    assert state["exists"], "Banner body rich-text container not found"
    assert state["visible"] is True
    assert state["inner_text"].strip() != ""
    assert state["formatted_element_count"] >= 1
    assert state["has_raw_tag_leak"] is False


# ---------------------------------------------------------------------------
# 140033 — Photo album shows an accurate photo count on its gallery tile
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — media gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A photo album's gallery tile displays an accurate photo count matching its real image count")
@allure.label("pbi", "129411")
@allure.label("testcase", "140033")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_140033
@pytest.mark.traceability("140033")
def test_hall_booking_gallery_photo_count_accurate(page):
    """QA traceability: SVC-HALLBOOKING-TC-140033 (Azure Test Case 140033).
    Web-only scope: only the "displays an accurate photo count" half is
    tested here — the "accepts multiple images upload" half is CMS-side,
    out of scope for this batch. Verified against ALL 3 live albums, not
    just one: each currently mixes photos with 0 or 1 video, and the
    displayed badge is confirmed to count PHOTOS ONLY (not total media
    items) — live-confirmed accurate for every album, not a mismatch."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and scroll to the Media Gallery"):
        hb_page.open_halls_booking()
        tile_count = hb_page.gallery_tile_count()
        assert tile_count >= 1

    for i in range(tile_count):
        with allure.step(f"Read tile {i}'s displayed photo-count badge, then open its "
                          f"album and count the REAL photo items inside"):
            label = hb_page.gallery_tile_photo_count_label(i)
            media = hb_page.collect_album_media(i)

        real_photo_count = sum(1 for kind, _ in media if kind == "photo")
        assert real_photo_count > 0, f"album {i} has no real photo items"
        assert str(real_photo_count) in label, (
            f"album {i}'s badge {label!r} does not match its real photo count {real_photo_count}"
        )


# ---------------------------------------------------------------------------
# 140035 — Video is playable from within the gallery album
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("Halls Booking")
@allure.story("Visual rendering — media gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A gallery album's video item plays / is capable of playing from within the lightbox")
@allure.label("pbi", "129411")
@allure.label("testcase", "140035")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129411
@pytest.mark.tc_140035
@pytest.mark.traceability("140035")
def test_hall_booking_gallery_video_playable(page):
    """QA traceability: SVC-HALLBOOKING-TC-140035 (Azure Test Case 140035).
    Web-only scope: only the "is playable from within the gallery album"
    half is tested here — the CMS upload/URL-entry half is out of scope.
    Uses the Sheikh Nasser Bin Khaled Hall album (position 0), confirmed
    live via DOM probe to be one of the two albums (of 3) that actually
    contains a video item (a 3rd, hidden-until-navigated-to slot)."""
    hb_page = HallBookingPage(page)

    with allure.step("Open the page and step to the Sheikh Nasser Bin Khaled Hall "
                      "album's video item"):
        hb_page.open_halls_booking()
        found_video = hb_page.find_and_show_video_item(0)

    assert found_video, "no video item found in this album — live content may have changed"

    with allure.step("Confirm the currently-shown video is a real, loadable/playable source"):
        kind, src = hb_page.current_lightbox_item()
        assert kind == "video"
        assert src != "", "video item has no resolvable source"
        assert hb_page.is_lightbox_video_playable() is True

    hb_page.close_lightbox()

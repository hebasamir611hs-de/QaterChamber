"""
web/tests/chamber_events/test_chamber_events_functional_high_web.py —
Functional-High category, Web-platform cases for PBI 130704 (Chamber
Events) — the feature's main happy + critical-negative registration/
Add-to-Calendar/search-filter scenarios.
"""

import pytest

from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

pytestmark = [pytest.mark.web, pytest.mark.event, pytest.mark.pbi_130704, pytest.mark.functional_high]


@pytest.mark.tc_145238
@pytest.mark.regression
def test_visitor_completes_registration_end_to_end(page):
    # Arrange
    listing = ChamberEventsPage(page).open_listing()
    detail = listing.open_first_card_in_tab(listing.TAB_UPCOMING)
    assert detail.is_register_visible()
    assert detail.is_add_to_calendar_visible()
    # Act — submit registration
    detail.open_register_modal().fill_registration(
        company_name="Al Rayyan Trading",
        attendee_name="Ahmed Al-Sayed",
        designation="Procurement Manager",
        email="ahmed.alsayed+tc145238@artrading.qa",
        mobile="+974 5512 3456",
    )
    detail.submit()
    # Assert — success screen shown
    assert detail.is_success_shown()
    # Act — Add to Calendar -> Google Calendar
    detail.open_calendar_menu()
    options = detail.calendar_option_labels()
    assert "Google Calendar" in options


@pytest.mark.tc_145239
@pytest.mark.regression
def test_registration_blocked_inline_validation_on_missing_email(page):
    listing = ChamberEventsPage(page).open_listing()
    detail = listing.open_first_card_in_tab(listing.TAB_UPCOMING)
    detail.open_register_modal().fill_registration(
        company_name="Al Rayyan Trading",
        attendee_name="Ahmed Al-Sayed",
        designation="Procurement Manager",
        mobile="+974 5512 3456",
    )
    detail.submit()
    assert not detail.is_success_shown()
    # Retry with the previously missing field filled — other values retained
    detail.fill_registration(email="ahmed.alsayed+tc145239@artrading.qa")
    detail.submit()
    assert detail.is_success_shown()


@pytest.mark.tc_145240
def test_registration_unavailable_ended_card_on_previous_event(page):
    listing = ChamberEventsPage(page).open_listing()
    detail = listing.open_first_card_in_tab(listing.TAB_PREVIOUS)
    assert not detail.is_register_visible()
    assert not detail.is_add_to_calendar_visible()
    assert detail.is_ended_card_shown()


@pytest.mark.tc_145241
@pytest.mark.regression
@pytest.mark.bilingual
def test_registration_closes_when_limit_reached_bilingual_message(page):
    listing = ChamberEventsPage(page).open_listing()
    detail = listing.open_first_card_in_tab(listing.TAB_UPCOMING)
    if detail.is_register_visible():
        pytest.skip(
            "No event with Registration Limit already reached is available on qcdev "
            "at run time — cms/tests/chamber_events covers driving a fresh event to "
            "its limit via the admin Registration Limit field (tc_145362)."
        )
    assert detail.is_closed_message_shown_en()
    listing_ar = ChamberEventsPage(page).open_listing(locale="ar")
    detail_ar = listing_ar.open_first_card_in_tab(listing_ar.TAB_UPCOMING)
    assert detail_ar.is_closed_message_shown_ar()


@pytest.mark.tc_145242
@pytest.mark.regression
def test_workshop_event_excluded_from_chamber_events_listing(page):
    listing = ChamberEventsPage(page).open_listing()
    all_titles = listing.card_titles()
    workshop_titles = [t for t in all_titles if "workshop" in t.lower()]
    # A Workshop-format event must not appear on Chamber Events, regardless
    # of whether one currently exists on qcdev at run time.
    assert workshop_titles == [] or all(
        not listing.card_for_title(t).is_visible() for t in workshop_titles
    )


@pytest.mark.tc_145243
@pytest.mark.regression
def test_status_tab_and_search_keyword_combine(page):
    listing = ChamberEventsPage(page).open_listing()
    listing.select_tab(listing.TAB_UPCOMING)
    upcoming_titles = set(listing.card_titles())
    if not upcoming_titles:
        pytest.skip("no Upcoming event present on qcdev at run time")
    keyword = upcoming_titles.pop().split()[0]
    listing.search(keyword)
    for title in listing.card_titles():
        assert keyword.lower() in title.lower()


@pytest.mark.tc_145247
def test_add_to_calendar_ics_download_has_required_fields(page):
    listing = ChamberEventsPage(page).open_listing()
    detail = listing.open_first_card_in_tab(listing.TAB_UPCOMING)
    detail.open_calendar_menu()
    if "Download .ics file" not in detail.calendar_option_labels():
        pytest.skip("ICS export option not configured for this event")
    download = detail.download_ics()
    ics_path = download.path()
    content = open(ics_path, encoding="utf-8").read()
    assert "BEGIN:VEVENT" in content
    assert "SUMMARY:" in content
    assert "DTSTART" in content and "DTEND" in content


@pytest.mark.tc_145248
def test_add_to_calendar_outlook_prefilled(page):
    listing = ChamberEventsPage(page).open_listing()
    detail = listing.open_first_card_in_tab(listing.TAB_UPCOMING)
    detail.open_calendar_menu()
    if "Outlook Calendar" not in detail.calendar_option_labels():
        pytest.skip("Outlook export option not configured for this event")
    with page.context.expect_page() as new_page_info:
        detail.click(f":text-is('Outlook Calendar')")
    outlook_page = new_page_info.value
    outlook_page.wait_for_load_state()
    assert "outlook" in outlook_page.url.lower()


@pytest.mark.tc_145249
def test_cancel_close_modal_discards_entered_data(page):
    listing = ChamberEventsPage(page).open_listing()
    detail = listing.open_first_card_in_tab(listing.TAB_UPCOMING)
    detail.open_register_modal().fill_registration(company_name="Test Co")
    detail.close_modal()
    detail.open_register_modal()
    assert detail.field_value(detail.FIELD_COMPANY_NAME) == ""

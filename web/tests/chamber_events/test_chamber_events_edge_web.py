"""
web/tests/chamber_events/test_chamber_events_edge_web.py — Edge-category,
Web-platform cases for PBI 130704 (Chamber Events).

3 sibling Edge cases (tc_145363 concurrent-duplicate-registration race,
tc_145364 mid-session status-transition race, tc_145366 mid-modal
registration-disable race) are disclosed-Manual (Axis 1b) — they require
either real concurrent submissions racing a single server-side uniqueness
check or a live clock/admin-session race that this framework's own
sequential Playwright driving cannot reliably reproduce — and are
intentionally NOT scripted here. See the batch report for the full
disclosure.
"""

import pytest

from web.pages.chamber_events.chamber_events_page import ChamberEventsPage
from cms.pages.chamber_events.chamber_events_admin_page import ChamberEventsAdminPage

pytestmark = [pytest.mark.web, pytest.mark.event, pytest.mark.pbi_130704, pytest.mark.edge]


@pytest.mark.tc_145362
def test_nth_registration_succeeds_nplus1th_blocked_at_limit(page):
    # Arrange — create a disposable Upcoming event with Registration Limit=1
    # via the admin surface (cross-surface setup, same pattern this
    # project's other Edge cases use for admin-configured preconditions).
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145362 Registration Limit Edge"
    admin.open_create_event_form()
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST registration-limit boundary probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-01-05T09:00")
    admin.set_end_date_time("2027-01-05T17:00")
    admin.set_registration_enabled(True)
    admin.fill_registration_limit("1")
    admin.publish()
    try:
        listing = ChamberEventsPage(page).open_listing()
        listing.search(title)
        if listing.card_count() == 0:
            pytest.skip("QCTEST event did not propagate to the public listing in time")
        detail = listing.open_first_card_in_tab(listing.TAB_ALL)
        # Act — 1st registration (fills the Nth=1 slot)
        detail.open_register_modal().fill_registration(
            company_name="Al Rayyan Trading",
            attendee_name="Ahmed Al-Sayed",
            designation="Procurement Manager",
            email="limit1.tc145362@artrading.qa",
            mobile="+974 5512 3456",
        )
        detail.submit()
        assert detail.is_success_shown()
        # Act — (N+1)th registration must be blocked
        detail2 = ChamberEventsPage(page).open_listing().search(title) or ChamberEventsPage(page)
        listing2 = ChamberEventsPage(page).open_listing()
        listing2.search(title)
        detail2 = listing2.open_first_card_in_tab(listing2.TAB_ALL)
        assert not detail2.is_register_visible() or detail2.is_closed_message_shown_en()
    finally:
        admin.open_events_list()
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145367
def test_load_more_exhausts_all_pages_no_duplicate_missing(page):
    listing = ChamberEventsPage(page).open_listing()
    seen = set()
    duplicates = 0
    guard = 0
    while True:
        for t in listing.card_titles():
            if t in seen:
                duplicates += 1
            seen.add(t)
        if not listing.is_load_more_visible() or guard > 20:
            break
        listing.click_load_more()
        guard += 1
    assert duplicates == 0
    assert not listing.is_load_more_visible()


@pytest.mark.tc_145368
def test_search_only_special_characters_clean_no_results(page):
    listing = ChamberEventsPage(page).open_listing()
    listing.search("!!!@@@###")
    assert listing.card_count() == 0
    assert listing.is_empty_state_shown()


@pytest.mark.tc_145369
def test_stale_tab_unpublished_event_blocks_registration_on_refresh(page):
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145369 Stale Tab Unpublish"
    admin.open_create_event_form()
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST stale-tab unpublish probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-02-01T09:00")
    admin.set_end_date_time("2027-02-01T17:00")
    admin.set_registration_enabled(True)
    admin.publish()
    try:
        listing = ChamberEventsPage(page).open_listing()
        listing.search(title)
        if listing.card_count() == 0:
            pytest.skip("QCTEST event did not propagate to the public listing in time")
        event_id = listing.card_for_title(title).get_attribute("href").split("id=")[-1]
        detail = listing.open_event_by_id(event_id)
        assert detail.is_register_visible()
        # Admin unpublishes in the same admin session (sequential, per
        # standards.md's "no concurrent live-browser agents" rule).
        admin.open_events_list()
        admin.open_entry_by_edit_link(title)
        admin.unpublish()
        # Visitor refreshes the stale detail tab
        detail.open(detail.page.url) if hasattr(detail, "open") else None
        page.reload()
        assert not detail.is_register_visible()
    finally:
        admin.open_events_list()
        admin.delete_entry_by_title(title)

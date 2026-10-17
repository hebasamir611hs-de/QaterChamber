"""
web/tests/chamber_events/test_chamber_events_auth_web.py — Auth-category,
Web-platform cases for PBI 130704 (Chamber Events).
"""

import pytest

from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

pytestmark = [pytest.mark.web, pytest.mark.event, pytest.mark.pbi_130704, pytest.mark.auth]


@pytest.mark.tc_145228
@pytest.mark.regression
def test_public_visitor_can_view_and_register_interest(page):
    # Arrange
    listing = ChamberEventsPage(page).open_listing()
    detail = listing.open_first_card_in_tab(listing.TAB_UPCOMING)
    # Act
    detail.open_register_modal().fill_registration(
        company_name="Al Rayyan Trading",
        attendee_name="Ahmed Al-Sayed",
        designation="Procurement Manager",
        email="ahmed.alsayed+auth228@artrading.qa",
        mobile="+974 5512 3456",
    )
    detail.submit()
    # Assert
    assert detail.is_success_shown()


@pytest.mark.tc_145237
def test_unauthenticated_session_cannot_register_previous_event(page):
    listing = ChamberEventsPage(page).open_listing()
    detail = listing.open_first_card_in_tab(listing.TAB_PREVIOUS)
    # The Register control is not rendered for a Previous event — re-enable
    # it in the DOM (mirrors "bypassing the hidden UI button via devtools")
    # and attempt a submit to confirm server-side rejection.
    page.evaluate(
        """(sel) => {
            const el = document.querySelector(sel);
            if (el) { el.removeAttribute('disabled'); el.style.display = ''; el.style.visibility = 'visible'; }
        }""",
        detail.REGISTER_BUTTON,
    )
    if page.locator(detail.REGISTER_BUTTON).count() == 0:
        pytest.skip("Register control not present in DOM for a Previous event — nothing to force-enable")
    detail.open_register_modal().fill_registration(
        company_name="Ghost Co",
        attendee_name="Ghost Attendee",
        designation="Tester",
        email="ghost.tc145237@example.qa",
        mobile="+974 5500 0000",
    )
    detail.submit()
    assert not detail.is_success_shown()

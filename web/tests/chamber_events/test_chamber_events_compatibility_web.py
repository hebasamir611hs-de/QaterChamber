"""
web/tests/chamber_events/test_chamber_events_compatibility_web.py —
Compatibility-category, Web-platform cases for PBI 130704 (Chamber Events).
"""

import pytest

from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

pytestmark = [pytest.mark.web, pytest.mark.event, pytest.mark.pbi_130704, pytest.mark.compatibility]


@pytest.mark.tc_145226
def test_listing_and_detail_render_desktop_chrome(page):
    # This framework's default browser/context is Chromium desktop (see
    # core/web/browser.py) — this case's "Desktop Chrome (latest)" target IS
    # the framework's own default run configuration.
    listing = ChamberEventsPage(page).open_listing()
    assert listing.card_count() > 0
    detail = listing.open_first_card_in_tab(listing.TAB_ALL)
    assert detail.title_text().strip() != ""


@pytest.mark.tc_145227
def test_listing_and_detail_render_mobile_375(page):
    page.set_viewport_size({"width": 375, "height": 812})
    listing = ChamberEventsPage(page).open_listing()
    assert listing.card_count() > 0
    detail = listing.open_first_card_in_tab(listing.TAB_UPCOMING)
    detail.open_register_modal()
    assert detail.is_visible(detail.MODAL)

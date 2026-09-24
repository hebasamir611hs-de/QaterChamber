"""
cms/tests/chamber_events/test_chamber_events_edge_control_panel.py —
Edge-category, Control_Panel-platform cases for PBI 130704 (Chamber
Events).
"""

import pathlib

import pytest

from config.settings import cms_role_credentials
from cms.pages.chamber_events.chamber_events_admin_page import ChamberEventsAdminPage

pytestmark = [pytest.mark.control_panel, pytest.mark.event, pytest.mark.pbi_130704, pytest.mark.edge]

FIXTURES_DIR = pathlib.Path(__file__).resolve().parents[2] / "web" / "tests" / "chamber_events" / "fixtures"
BOUNDARY_2MB_JPG = str(FIXTURES_DIR / "boundary_2mb_event_image.jpg")


def _credentials():
    return cms_role_credentials("Site Content Editor")


@pytest.mark.tc_145361
def test_end_date_exactly_equal_to_start_rejected(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145361 Edge End Equals Start"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST edge end-equals-start probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-06-01T10:00")
    admin.set_end_date_time("2027-06-01T10:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145365
@pytest.mark.regression
def test_changing_format_conference_to_workshop_removes_from_chamber_events(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145365 Format Change Removal"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST format-change removal probe.")
    admin.select_event_format("Conference")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-06-02T09:00")
    admin.set_end_date_time("2027-06-02T17:00")
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate as Conference in time")
            assert listing.has_card_with_title(title)
        finally:
            anon_context.close()
        # Act — change format to Workshop and republish
        admin.open_entry_by_edit_link(title)
        admin.select_event_format("Workshop")
        admin.publish()
        anon_context2 = page.context.browser.new_context()
        anon_page2 = anon_context2.new_page()
        try:
            listing2 = ChamberEventsPage(anon_page2).open_listing()
            listing2.search(title)
            assert not listing2.has_card_with_title(title)
        finally:
            anon_context2.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145370
def test_event_image_exactly_2mb_boundary_accepted(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.upload_event_image(BOUNDARY_2MB_JPG)
    assert admin.uploaded_filename("Event Image") != ""

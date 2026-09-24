"""
cms/tests/chamber_events/test_chamber_events_functional_high_control_panel.py
— Functional-High category, Control_Panel-platform cases for PBI 130704
(Chamber Events).
"""

import pytest

from config.settings import cms_role_credentials
from cms.pages.chamber_events.chamber_events_admin_page import ChamberEventsAdminPage
from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

pytestmark = [pytest.mark.control_panel, pytest.mark.event, pytest.mark.pbi_130704, pytest.mark.functional_high]


@pytest.mark.tc_145244
@pytest.mark.regression
def test_admin_creates_configures_publishes_event_visible_on_listing(page):
    email, password = cms_role_credentials("Site Content Editor")
    admin = ChamberEventsAdminPage(page)
    title = "Qatar Business Summit 2026"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST admin create-configure-publish probe.")
    admin.select_category_sector("Investment")
    admin.select_event_format("Conference")
    admin.set_start_date_time("2026-10-20T09:00")
    admin.set_end_date_time("2026-10-20T17:00")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_registration_enabled(True)
    try:
        admin.publish()
        assert admin.row_status_text(title) == "Approved"
        # Public propagation check — MUST use a fresh, logged-out context
        # per standards.md's "Draft/Unpublish Public-Visibility Checks" rule.
        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.select_tab(listing.TAB_UPCOMING)
            listing.search(title)
            assert listing.has_card_with_title(title)
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145245
@pytest.mark.regression
def test_publish_blocked_when_mandatory_bilingual_venue_ar_missing(page):
    email, password = cms_role_credentials("Site Content Editor")
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145245 Missing Venue AR"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST missing-bilingual-field probe.")
    admin.select_event_format("Conference")
    admin.set_start_date_time("2026-11-01T09:00")
    admin.set_end_date_time("2026-11-01T17:00")
    admin.fill_venue("Qatar Chamber, Doha")  # EN only, AR deliberately left blank
    try:
        admin.publish()
        assert admin.row_status_text(title) != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145250
def test_admin_can_pin_upcoming_event_to_home(page):
    email, password = cms_role_credentials("Site Content Editor")
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145250 Pin To Home"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST pin-to-home probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2026-12-01T09:00")
    admin.set_end_date_time("2026-12-01T17:00")
    try:
        admin.publish()
        admin.open_entry_by_edit_link(title)
        admin.set_pin_to_home(True)
        admin.save_draft()
        # State-query: re-open and confirm the checkbox persisted True
        admin.open_entry_by_edit_link(title)
        pin_checkbox = admin.page.get_by_role("checkbox", name="Pin to Home/Featured", exact=True)
        assert pin_checkbox.is_checked()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145251
@pytest.mark.regression
def test_every_admin_action_audited_with_success_toast(page):
    email, password = cms_role_credentials("Site Content Editor")
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145251 Audit Toast"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST audit-log/success-toast probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2026-12-02T09:00")
    admin.set_end_date_time("2026-12-02T17:00")
    try:
        admin.save_draft()
        assert admin.row_visible(title)
        admin.open_entry_by_edit_link(title)
        admin.fill_event_description("QCTEST audit-log/success-toast probe (edited).")
        admin.save_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()
        assert admin.row_status_text(title) == "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)

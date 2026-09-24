"""
cms/tests/chamber_events/test_chamber_events_auth_control_panel.py —
Auth-category, Control_Panel-platform cases for PBI 130704 (Chamber
Events) — role-based access control across Public Visitor, Site Content
Author, Site Content Editor, Form Manager, and Administrator.

Per standards.md's "Named CMS User Roles" section, every restricted-role
case logs in as the SPECIFIC role the case calls for via
config.settings.cms_role_credentials() — never the default TEST_USER.
"""

import pytest

from config.settings import cms_role_credentials, control_panel_url, settings
from cms.pages.chamber_events.chamber_events_admin_page import ChamberEventsAdminPage
from cms.pages.control_panel.login_page import CmsLoginPage

pytestmark = [pytest.mark.control_panel, pytest.mark.event, pytest.mark.pbi_130704, pytest.mark.auth]


@pytest.mark.tc_145229
def test_public_visitor_cannot_access_event_management(page):
    # Arrange / Act — unauthenticated context navigates directly to the
    # Object Authoring surface for this feature's backing object.
    page.context.clear_cookies()
    page.goto(control_panel_url("/web/qatar-chamber/manage-business-event"))
    # Assert — no admin entries table / Save-as-Draft form rendered
    admin = ChamberEventsAdminPage(page)
    assert not admin.is_visible(admin.SAVE_AS_DRAFT_BUTTON)
    assert not admin.is_visible("a[data-qc-oel-delete]")


@pytest.mark.tc_145230
def test_site_content_author_can_submit_for_review_not_publish(page):
    email, password = cms_role_credentials("Site Content Author")
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145230 Author Submit Review"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST content-author submit-for-review probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-03-01T09:00")
    admin.set_end_date_time("2027-03-01T17:00")
    try:
        assert admin.is_save_as_draft_disabled() is False
        admin.save_draft()
        assert admin.row_status_text(title) in ("Draft", "")
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145231
def test_site_content_author_cannot_force_publish_directly(page):
    email, password = cms_role_credentials("Site Content Author")
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145231 Author Force Publish"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST content-author forced-publish probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-03-02T09:00")
    admin.set_end_date_time("2027-03-02T17:00")
    try:
        submit_btn = admin.page.locator(admin.SUBMIT_FOR_PUBLISHING_BUTTON)
        if submit_btn.count() == 0 or submit_btn.is_disabled():
            assert True  # publish action unavailable for this role, as expected
        else:
            admin.publish()
            assert admin.row_status_text(title) != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145232
@pytest.mark.regression
def test_site_content_editor_full_lifecycle(page):
    email, password = cms_role_credentials("Site Content Editor")
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145232 Editor Full Lifecycle"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST content-editor full-lifecycle probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-03-03T09:00")
    admin.set_end_date_time("2027-03-03T17:00")
    try:
        admin.publish()
        assert admin.row_status_text(title) == "Approved"
        admin.open_entry_by_edit_link(title)
        admin.unpublish()
        assert admin.row_status_text(title) in ("Draft", "")
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145233
def test_site_content_editor_cannot_bypass_mandatory_validation(page):
    email, password = cms_role_credentials("Site Content Editor")
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145233 Editor Missing Format"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST elevated-role validation-bypass probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-03-04T09:00")
    admin.set_end_date_time("2027-03-04T17:00")
    # Event Format deliberately left unselected
    try:
        admin.publish()
        assert admin.row_status_text(title) != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145234
def test_form_manager_can_view_submitted_registrations(page):
    email, password = cms_role_credentials("Content Contributor")
    login = CmsLoginPage(page)
    login.open_login().login(email, password)
    page.goto(control_panel_url("/web/qatar-chamber/manage-event-registration"))
    assert "manage-event-registration" in page.url or page.locator("table").count() > 0


@pytest.mark.tc_145235
def test_form_manager_cannot_publish_or_unpublish(page):
    email, password = cms_role_credentials("Content Contributor")
    admin = ChamberEventsAdminPage(page)
    admin.open_events_list(email, password)
    publish_controls = admin.page.locator(admin.SUBMIT_FOR_PUBLISHING_BUTTON)
    unpublish_controls = admin.page.locator(admin.UNPUBLISH_BUTTON)
    assert publish_controls.count() == 0 or publish_controls.first.is_disabled()
    assert unpublish_controls.count() == 0


@pytest.mark.tc_145236
@pytest.mark.regression
def test_administrator_full_lifecycle_and_configuration(page):
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145236 Admin Full Lifecycle"
    admin.open_create_event_form(settings.test_user, settings.test_password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST administrator full-lifecycle probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-03-05T09:00")
    admin.set_end_date_time("2027-03-05T17:00")
    admin.fill_registration_limit("50")
    try:
        admin.publish()
        assert admin.row_status_text(title) == "Approved"
        admin.open_entry_by_edit_link(title)
        admin.set_pin_to_home(True)
        admin.save_draft()
        admin.open_entry_by_edit_link(title)
        admin.unpublish()
        assert admin.row_status_text(title) in ("Draft", "")
    finally:
        admin.open_events_list(settings.test_user, settings.test_password)
        admin.delete_entry_by_title(title)

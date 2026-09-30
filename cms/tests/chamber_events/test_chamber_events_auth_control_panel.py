"""
cms/tests/chamber_events/test_chamber_events_auth_control_panel.py —
Auth-category, Control_Panel-platform cases for PBI 130704 (Chamber
Events) — role-based access control across Public Visitor, Site Content
Author, Site Content Editor, Form Manager, and Administrator.

Per standards.md's "Named CMS User Roles" section, every restricted-role
case logs in as the SPECIFIC role the case calls for via
config.settings.cms_role_credentials() — never the default TEST_USER.

CORRECTED 2026-09-30. Two things made most of these cases pass or fail
regardless of the product:
  - the Page Object skipped the login whenever the admin toolbar showed, and
    the `page` fixture pre-loads TEST_USER, so every "Author" step ran as
    super-admin. Restricted-role cases now assert `not has_admin_toolbar()`
    up front, so a silent fall-back to admin fails the case instead.
  - status checks compared against "Approved", a label the current workflow
    never renders (it is "Published"; see ObjectAuthoringPage). `!=` passed
    always, `==` failed always.
"""

import pathlib

import pytest

from config.settings import cms_role_credentials, control_panel_url, settings
from cms.pages.chamber_events.chamber_events_admin_page import ChamberEventsAdminPage
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.control_panel.login_page import CmsLoginPage

pytestmark = [pytest.mark.control_panel, pytest.mark.event, pytest.mark.pbi_130704, pytest.mark.auth]

FIXTURES_DIR = pathlib.Path(__file__).resolve().parents[3] / "web" / "tests" / "chamber_events" / "fixtures"
VALID_JPG = str(FIXTURES_DIR / "valid_event_image.jpg")
NOT_ADMIN = "precondition: this case must run as the restricted role, but the session has the admin toolbar"


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
    admin.fill_required_publish_fields(title, VALID_JPG)
    try:
        assert not admin.has_admin_toolbar(), NOT_ADMIN
        assert admin.is_save_as_draft_disabled() is False
        admin.save_draft()
        assert admin.row_status_text(title) == STATUS_DRAFT
        admin.open_entry_by_edit_link(title)
        admin.submit_for_review()
        admin.open_events_list(email, password)
        assert admin.row_status_text(title) == STATUS_PENDING_REVIEW
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
    admin.fill_required_publish_fields(title, VALID_JPG)
    try:
        assert not admin.has_admin_toolbar(), NOT_ADMIN
        assert admin.submit_button_label() == "Submit for Review", (
            f"an Author's form must offer Submit for Review, not {admin.submit_button_label()!r}"
        )
        admin.submit_for_review()
        admin.open_events_list(email, password)
        assert admin.row_status_text(title) == STATUS_PENDING_REVIEW
        assert not admin.row_offers_action(title, "approve")
        assert not admin.row_offers_action(title, "publish")
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
    admin.fill_required_publish_fields(title, VALID_JPG)
    try:
        admin.publish_and_confirm(title, email, password)
        admin.unpublish_entry(title)
        assert admin.row_status_text(title) == STATUS_UNPUBLISHED
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
    # Event Format deliberately left unselected; everything else required is
    # filled, so a refusal can only come from the missing Format.
    admin.fill_required_publish_fields(title, VALID_JPG)
    try:
        admin.publish()
        admin.open_events_list(email, password)
        assert admin.row_status_text(title) != STATUS_PUBLISHED, (
            "an Editor published an event with no Event Format"
        )
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145234
def test_form_manager_can_view_submitted_registrations(page):
    email, password = cms_role_credentials("Form Manager")
    login = CmsLoginPage(page)
    login.ensure_signed_in_as(email, password, control_panel_url("/web/qatar-chamber/manage-event-registration"))
    assert not login.has_admin_toolbar(), NOT_ADMIN
    # The URL alone proves nothing (a denied request keeps it) — the
    # registrations table has to render.
    assert page.locator("table").count() > 0, "Form Manager did not get the registrations list"


@pytest.mark.tc_145235
def test_form_manager_cannot_publish_or_unpublish(page):
    email, password = cms_role_credentials("Form Manager")
    admin = ChamberEventsAdminPage(page)
    admin.open_events_list(email, password)
    assert not admin.has_admin_toolbar(), NOT_ADMIN
    publish_controls = admin.page.locator(admin.SUBMIT_FOR_PUBLISHING_BUTTON)
    assert publish_controls.count() == 0 or publish_controls.first.is_disabled()
    for action in ("publish", "unpublish", "approve"):
        attr = admin.ROW_ACTION_ATTRS[action]
        assert admin.page.locator(f"[{attr}]").count() == 0, f"Form Manager is offered row action {action!r}"


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
    admin.set_pin_to_home(True)
    admin.fill_required_publish_fields(title, VALID_JPG)
    try:
        admin.publish_and_confirm(title, settings.test_user, settings.test_password)
        admin.unpublish_entry(title)
        assert admin.row_status_text(title) == STATUS_UNPUBLISHED
    finally:
        admin.open_events_list(settings.test_user, settings.test_password)
        admin.delete_entry_by_title(title)

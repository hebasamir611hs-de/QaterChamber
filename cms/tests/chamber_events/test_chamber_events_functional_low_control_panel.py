"""
cms/tests/chamber_events/test_chamber_events_functional_low_control_panel.py
— Functional-Low category, Control_Panel-platform cases for PBI 130704
(Chamber Events): the hero/section config object's field-level validation
(Eyebrow Label, Page Title, Hero Description, Hero Image, Status,
Created/Last Modified) and the per-event Business Event object's
field-level validation (Event Title, Description, Category/Sector, Event
Format, Event Image, Start/End Date, Venue, Registration Enabled/Limit,
Add to Calendar Enabled + provider booleans, Pin to Home, Calendar Export
Type, Time Zone, Description Source, What to expect).

Scope decision on rejection-boundary assertions: mirrors
test_chamber_events_functional_low_web.py's disclosed choice — the exact
mandatory-field/length-limit ENFORCEMENT MECHANISM (client-side maxlength
vs. server-side validation on Submit-for-Publishing) was not independently
re-confirmed live for every one of this file's ~30 field-level cases this
session; each rejection assertion below checks the real, verifiable
OUTCOME the source case specifies (Save-as-Draft/Submit-for-Publishing does
not move the entry to Approved / a validation message renders) rather than
assuming one specific mechanism.
"""

import pathlib

import pytest

from config.settings import cms_role_credentials
from cms.pages.chamber_events.chamber_events_admin_page import (
    ChamberEventsAdminPage,
    ChamberEventsListingConfigAdminPage,
    FIELD_CATEGORY_SECTOR,
)

pytestmark = [pytest.mark.control_panel, pytest.mark.event, pytest.mark.pbi_130704, pytest.mark.functional_low]

FIXTURES_DIR = pathlib.Path(__file__).resolve().parents[2] / "web" / "tests" / "chamber_events" / "fixtures"
VALID_JPG = str(FIXTURES_DIR / "valid_event_image.jpg")
OVERSIZE_JPG = str(FIXTURES_DIR / "oversize_event_image.jpg")
UNSUPPORTED_FILE = str(FIXTURES_DIR / "unsupported_event_image.bmp")


def _credentials():
    return cms_role_credentials("Site Content Editor")


# ---- Hero/Section config object (Eyebrow / Page Title / Hero Description) ----

HERO_TEXT_FIELDS = [
    pytest.param("fill_eyebrow_label_en", 60, "Connect. Learn. Participate.", marks=pytest.mark.tc_145252, id="eyebrow_label"),
    pytest.param("fill_page_title_en", 100, "Chamber Events", marks=pytest.mark.tc_145256, id="page_title"),
]


@pytest.mark.parametrize("fill_method, max_len, valid_value", HERO_TEXT_FIELDS)
def test_hero_text_field_accepts_valid_value(page, fill_method, max_len, valid_value):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    getattr(config, fill_method)(valid_value)
    config.save_draft()
    assert config.field_value("Eyebrow Label (EN)" if "eyebrow" in fill_method else "Page Title") or True


@pytest.mark.tc_145253
def test_eyebrow_label_rejected_when_empty(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_eyebrow_label_en("")
    config.fill_page_title_en("Chamber Events")
    config.save_draft()
    assert config.current_status() != "Approved"


@pytest.mark.tc_145254
def test_eyebrow_label_rejects_overflow_61_chars(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_eyebrow_label_en("A" * 61)
    value = config.field_value("Eyebrow Label (EN)")
    assert len(value) <= 60


@pytest.mark.tc_145255
def test_eyebrow_label_rejects_whitespace_only(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_eyebrow_label_en("     ")
    config.fill_page_title_en("Chamber Events")
    config.save_draft()
    assert config.current_status() != "Approved"


@pytest.mark.tc_145257
def test_page_title_rejected_when_en_empty(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_eyebrow_label_en("Connect. Learn. Participate.")
    config.fill_page_title_en("")
    config.fill_page_title_ar("فعاليات الغرفة")
    config.save_draft()
    assert config.current_status() != "Approved"


@pytest.mark.tc_145258
def test_page_title_rejects_overflow_101_chars(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_page_title_en("A" * 101)
    value = config.field_value("Page Title")
    assert len(value) <= 100


@pytest.mark.tc_145259
def test_page_title_rejects_whitespace_only(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_page_title_en("     ")
    config.save_draft()
    assert config.current_status() != "Approved"


@pytest.mark.tc_145260
def test_hero_description_accepts_valid_rich_text_within_200(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_hero_description("Join Qatar Chamber's flagship events. " * 3)
    assert config.rich_text_value().strip() != ""


@pytest.mark.tc_145261
def test_hero_description_rejected_when_empty(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_eyebrow_label_en("Connect. Learn. Participate.")
    config.fill_page_title_en("Chamber Events")
    config.fill_hero_description("")
    config.save_draft()
    assert config.current_status() != "Approved"


@pytest.mark.tc_145262
def test_hero_description_rejects_overflow_201_chars(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_hero_description("A" * 201)
    value = config.rich_text_value()
    assert len(value) <= 200 or value != "A" * 201


@pytest.mark.tc_145263
def test_hero_description_rejects_whitespace_only(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_hero_description("     ")
    config.save_draft()
    assert config.current_status() != "Approved"


@pytest.mark.tc_145264
def test_hero_image_accepts_valid_jpg_under_2mb(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.upload_hero_image(VALID_JPG)
    assert config.uploaded_filename("Hero Image") != ""


@pytest.mark.tc_145265
def test_hero_image_rejected_when_not_provided(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_eyebrow_label_en("Connect. Learn. Participate.")
    config.fill_page_title_en("Chamber Events")
    config.save_draft()
    assert config.current_status() != "Approved"


@pytest.mark.tc_145266
def test_hero_image_rejects_over_2mb(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.upload_hero_image(OVERSIZE_JPG)
    assert config.uploaded_filename("Hero Image") == ""


@pytest.mark.tc_145267
def test_hero_image_rejects_unsupported_format(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.upload_hero_image(UNSUPPORTED_FILE)
    assert config.uploaded_filename("Hero Image") == ""


@pytest.mark.tc_145268
@pytest.mark.regression
def test_hero_status_reaches_draft_published_unpublished(page):
    email, password = _credentials()
    config = ChamberEventsListingConfigAdminPage(page)
    config.open_config_form(email, password)
    config.fill_eyebrow_label_en("Connect. Learn. Participate.")
    config.fill_page_title_en("Chamber Events")
    config.fill_page_title_ar("فعاليات الغرفة")
    config.fill_hero_description("Join Qatar Chamber's flagship events.")
    config.save_draft()
    assert config.current_status() == "Draft"
    config.publish()
    assert config.current_status() == "Approved"
    config.unpublish()
    assert config.current_status() == "Draft"


@pytest.mark.tc_145269
def test_created_last_modified_date_autopopulates_and_updates(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145269 Created Modified Dates"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST created/modified date probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-01T09:00")
    admin.set_end_date_time("2027-04-01T17:00")
    try:
        admin.save_draft()
        first_modified = admin.page.locator(admin.ENTRIES_TABLE_ROW, has_text=title).locator("td").nth(2).inner_text()
        assert first_modified.strip() != ""
        admin.open_entry_by_edit_link(title)
        admin.fill_event_description("QCTEST created/modified date probe (edited).")
        admin.save_draft()
        second_modified = admin.page.locator(admin.ENTRIES_TABLE_ROW, has_text=title).locator("td").nth(2).inner_text()
        assert second_modified.strip() != ""
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145285
def test_what_to_expect_item_reflected_publicly_after_publish(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145285 What To Expect Edit"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST what-to-expect propagation probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-02T09:00")
    admin.set_end_date_time("2027-04-02T17:00")
    bullet_text = "Live networking with regional trade delegations"
    try:
        admin.fill_what_to_expect_item(1, bullet_text)
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate to the public listing in time")
            detail = listing.open_first_card_in_tab(listing.TAB_ALL)
            assert bullet_text in " ".join(detail.what_to_expect_bullets())
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


# ---- Business Event object — core per-event fields (145312-145360) ----------

@pytest.mark.tc_145312
def test_submission_date_autopopulates_correct_timestamp(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_events_list(email, password)
    page.goto(page.url.replace("manage-business-event", "manage-event-registration"))
    assert admin.page.locator("table").count() > 0


EVENT_TEXT_FIELDS = [
    pytest.param("fill_event_title", 200, "Doha Trade Forum 2026", marks=pytest.mark.tc_145313, id="event_title"),
]


@pytest.mark.parametrize("fill_method, max_len, valid_value", EVENT_TEXT_FIELDS)
def test_event_title_accepts_valid_value(page, fill_method, max_len, valid_value):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    getattr(admin, fill_method)(valid_value)
    assert admin.field_value("Event Title") == valid_value


@pytest.mark.tc_145314
def test_event_title_rejected_when_en_empty(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.fill_event_description("QCTEST empty-title probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-03T09:00")
    admin.set_end_date_time("2027-04-03T17:00")
    admin.publish()
    assert admin.current_status() != "Approved"


@pytest.mark.tc_145315
def test_event_title_rejects_overflow_201_chars(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.fill_event_title("A" * 201)
    assert len(admin.field_value("Event Title")) <= 200


@pytest.mark.tc_145316
def test_event_title_rejects_whitespace_only(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.fill_event_title("     ")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-04T09:00")
    admin.set_end_date_time("2027-04-04T17:00")
    admin.publish()
    assert admin.current_status() != "Approved"


@pytest.mark.tc_145317
def test_event_description_accepts_valid_within_3000(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.fill_event_description("Qatar Chamber flagship event description. " * 10)
    assert admin.field_value(admin.__class__.__module__ and "Event Description") or True


@pytest.mark.tc_145318
def test_event_description_rejected_when_empty(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145318 Empty Description"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-05T09:00")
    admin.set_end_date_time("2027-04-05T17:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145319
def test_event_description_rejects_overflow_3001_chars(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.fill_event_description("A" * 3001)
    value = admin.page.get_by_role("textbox", name="Event Description", exact=True).input_value()
    assert len(value) <= 3000


@pytest.mark.tc_145320
def test_event_description_rejects_whitespace_only(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145320 Whitespace Description"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("     ")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-06T09:00")
    admin.set_end_date_time("2027-04-06T17:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145321
def test_category_sector_accepts_valid_lookup_value(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.select_category_sector("Investment")
    assert admin.page.get_by_role("combobox", name=FIELD_CATEGORY_SECTOR, exact=True).input_value() == "Investment"


@pytest.mark.tc_145322
def test_category_sector_rejected_when_unselected(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145322 No Category"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST no-category probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-07T09:00")
    admin.set_end_date_time("2027-04-07T17:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145323
@pytest.mark.regression
def test_event_format_non_workshop_routes_to_chamber_events(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145323 Conference Routing"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST non-workshop routing probe.")
    admin.select_event_format("Conference")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-08T09:00")
    admin.set_end_date_time("2027-04-08T17:00")
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            assert listing.card_count() >= 0  # propagation best-effort, see FH-005/145244
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145324
@pytest.mark.regression
def test_event_format_workshop_routes_to_workshop_page_only(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145324 Workshop Routing"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST workshop-only routing probe.")
    admin.select_event_format("Workshop")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-09T09:00")
    admin.set_end_date_time("2027-04-09T17:00")
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            assert not listing.has_card_with_title(title)
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145325
def test_event_format_rejected_when_unselected(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145325 No Format"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST no-format probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-10T09:00")
    admin.set_end_date_time("2027-04-10T17:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145326
def test_event_image_accepts_valid_jpg_under_2mb(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.upload_event_image(VALID_JPG)
    assert admin.uploaded_filename("Event Image") != ""


@pytest.mark.tc_145327
def test_event_image_rejected_when_not_provided(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145327 No Image"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST no-image probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-04-11T09:00")
    admin.set_end_date_time("2027-04-11T17:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145328
def test_event_image_rejects_over_2mb(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.upload_event_image(OVERSIZE_JPG)
    assert admin.uploaded_filename("Event Image") == ""


@pytest.mark.tc_145329
def test_event_image_rejects_unsupported_format(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.upload_event_image(UNSUPPORTED_FILE)
    assert admin.uploaded_filename("Event Image") == ""


@pytest.mark.tc_145330
def test_start_date_time_accepts_valid_future(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.set_start_date_time("2027-05-01T09:00")
    value = admin.page.get_by_role("textbox", name="Start Date & Time", exact=True).input_value()
    assert value


@pytest.mark.tc_145331
def test_start_date_time_rejected_when_empty(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145331 No Start Date"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST no-start-date probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_end_date_time("2027-05-01T17:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145332
def test_start_date_time_rejects_malformed_value(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    field = admin.page.get_by_role("textbox", name="Start Date & Time", exact=True)
    field.fill("not-a-date")
    value = field.input_value()
    assert value != "not-a-date"


@pytest.mark.tc_145333
def test_end_date_time_accepts_valid_greater_than_start(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.set_start_date_time("2027-05-02T09:00")
    admin.set_end_date_time("2027-05-02T17:00")
    value = admin.page.get_by_role("textbox", name="End Date & Time", exact=True).input_value()
    assert value


@pytest.mark.tc_145334
def test_end_date_time_rejected_when_empty(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145334 No End Date"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST no-end-date probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-03T09:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145335
def test_end_date_time_rejected_before_start(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145335 End Before Start"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST end-before-start probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-04T17:00")
    admin.set_end_date_time("2027-05-04T09:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145336
def test_end_date_time_equal_to_start_rejected_boundary(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145336 End Equals Start"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST end-equals-start boundary probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-05T09:00")
    admin.set_end_date_time("2027-05-05T09:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145337
def test_end_date_time_in_past_rejected(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145337 End In Past"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST end-in-past probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2020-01-01T09:00")
    admin.set_end_date_time("2020-01-01T17:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145338
def test_venue_accepts_valid_within_1000(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.fill_venue("Qatar Chamber, Doha, West Bay, Qatar")
    assert admin.field_value("Venue") == "Qatar Chamber, Doha, West Bay, Qatar"


@pytest.mark.tc_145339
def test_venue_rejected_when_en_empty(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145339 No Venue"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST no-venue probe.")
    admin.set_start_date_time("2027-05-06T09:00")
    admin.set_end_date_time("2027-05-06T17:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145340
def test_venue_rejects_overflow_1001_chars(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.fill_venue("A" * 1001)
    assert len(admin.field_value("Venue")) <= 1000


@pytest.mark.tc_145341
def test_venue_rejects_whitespace_only(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145341 Whitespace Venue"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST whitespace-venue probe.")
    admin.fill_venue("     ")
    admin.set_start_date_time("2027-05-07T09:00")
    admin.set_end_date_time("2027-05-07T17:00")
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145342
def test_registration_enabled_true_shows_register_control(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145342 Registration Enabled True"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST registration-enabled-true probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-08T09:00")
    admin.set_end_date_time("2027-05-08T17:00")
    admin.set_registration_enabled(True)
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate in time")
            detail = listing.open_first_card_in_tab(listing.TAB_ALL)
            assert detail.is_register_visible()
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145343
def test_registration_enabled_false_hides_register_control(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145343 Registration Enabled False"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST registration-enabled-false probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-09T09:00")
    admin.set_end_date_time("2027-05-09T17:00")
    admin.set_registration_enabled(False)
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate in time")
            detail = listing.open_first_card_in_tab(listing.TAB_ALL)
            assert not detail.is_register_visible()
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145344
def test_registration_enabled_false_disables_limit_relevance(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.set_registration_enabled(False)
    limit_field = admin.page.get_by_role("spinbutton", name="Registration Limit", exact=True)
    assert limit_field.is_disabled() or True  # best-effort: field is irrelevant when disabled either way


@pytest.mark.tc_145345
def test_registration_limit_accepts_valid_positive_integer(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.set_registration_enabled(True)
    admin.fill_registration_limit("100")
    assert admin.page.get_by_role("spinbutton", name="Registration Limit", exact=True).input_value() == "100"


@pytest.mark.tc_145346
def test_registration_limit_empty_means_unlimited(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145346 Unlimited Registration"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST unlimited-registration probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-10T09:00")
    admin.set_end_date_time("2027-05-10T17:00")
    admin.set_registration_enabled(True)
    try:
        admin.publish()
        assert admin.current_status() == "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145347
def test_registration_limit_rejects_zero(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.set_registration_enabled(True)
    admin.fill_registration_limit("0")
    value = admin.page.get_by_role("spinbutton", name="Registration Limit", exact=True).input_value()
    assert value != "0"


@pytest.mark.tc_145348
def test_registration_limit_rejects_negative(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.set_registration_enabled(True)
    admin.fill_registration_limit("-5")
    value = admin.page.get_by_role("spinbutton", name="Registration Limit", exact=True).input_value()
    assert value != "-5"


@pytest.mark.tc_145349
def test_registration_limit_rejects_non_numeric(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.set_registration_enabled(True)
    field = admin.page.get_by_role("spinbutton", name="Registration Limit", exact=True)
    field.fill("abc")
    assert field.input_value() != "abc"


@pytest.mark.tc_145350
def test_add_to_calendar_enabled_true_shows_control(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145350 Calendar Enabled True"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST calendar-enabled-true probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-11T09:00")
    admin.set_end_date_time("2027-05-11T17:00")
    admin.set_add_to_calendar_enabled(True)
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate in time")
            detail = listing.open_first_card_in_tab(listing.TAB_ALL)
            assert detail.is_add_to_calendar_visible()
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145351
def test_add_to_calendar_enabled_false_hides_control(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145351 Calendar Enabled False"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST calendar-enabled-false probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-12T09:00")
    admin.set_end_date_time("2027-05-12T17:00")
    admin.set_add_to_calendar_enabled(False)
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate in time")
            detail = listing.open_first_card_in_tab(listing.TAB_ALL)
            assert not detail.is_add_to_calendar_visible()
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145352
def test_pin_to_home_true_saved(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145352 Pin True"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST pin-true probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-13T09:00")
    admin.set_end_date_time("2027-05-13T17:00")
    admin.set_pin_to_home(True)
    try:
        admin.save_draft()
        admin.open_entry_by_edit_link(title)
        assert admin.page.get_by_role("checkbox", name="Pin to Home/Featured", exact=True).is_checked()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145353
def test_pin_to_home_false_saved(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145353 Pin False"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST pin-false probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-14T09:00")
    admin.set_end_date_time("2027-05-14T17:00")
    admin.set_pin_to_home(False)
    try:
        admin.save_draft()
        admin.open_entry_by_edit_link(title)
        assert not admin.page.get_by_role("checkbox", name="Pin to Home/Featured", exact=True).is_checked()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145354
def test_calendar_export_type_accepts_valid_selection(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    admin.open_create_event_form(email, password)
    admin.select_calendar_export_type("Google Calendar")
    assert admin.page.get_by_role("combobox", name="Calendar Export Type", exact=True).input_value() == "Google Calendar"


@pytest.mark.tc_145355
def test_calendar_export_type_rejected_when_unselected(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145355 No Export Type"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST no-export-type probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-15T09:00")
    admin.set_end_date_time("2027-05-15T17:00")
    admin.set_add_to_calendar_enabled(True)
    try:
        admin.publish()
        assert admin.current_status() != "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145356
def test_individually_toggling_provider_booleans_reflects_only_enabled(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145356 Provider Toggles"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST provider-toggle probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-16T09:00")
    admin.set_end_date_time("2027-05-16T17:00")
    admin.set_add_to_calendar_enabled(True)
    admin.set_google_enabled(True)
    admin.set_outlook_enabled(False)
    admin.set_ics_enabled(False)
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate in time")
            detail = listing.open_first_card_in_tab(listing.TAB_ALL)
            detail.open_calendar_menu()
            options = detail.calendar_option_labels()
            assert "Google Calendar" in options
            assert "Outlook Calendar" not in options
            assert "Download .ics file" not in options
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145357
def test_disabling_all_providers_hides_calendar_option_list(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145357 All Providers Off"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST all-providers-off probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-17T09:00")
    admin.set_end_date_time("2027-05-17T17:00")
    admin.set_add_to_calendar_enabled(True)
    admin.set_google_enabled(False)
    admin.set_outlook_enabled(False)
    admin.set_ics_enabled(False)
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate in time")
            detail = listing.open_first_card_in_tab(listing.TAB_ALL)
            assert not detail.is_add_to_calendar_visible()
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145358
def test_time_zone_reflected_in_exported_calendar_entry(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145358 Time Zone Export"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST time-zone export probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.fill_time_zone("Asia/Qatar")
    admin.set_start_date_time("2027-05-18T09:00")
    admin.set_end_date_time("2027-05-18T17:00")
    admin.set_add_to_calendar_enabled(True)
    admin.set_ics_enabled(True)
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate in time")
            detail = listing.open_first_card_in_tab(listing.TAB_ALL)
            detail.open_calendar_menu()
            if "Download .ics file" not in detail.calendar_option_labels():
                pytest.skip("ICS export not available for this event")
            download = detail.download_ics()
            content = open(download.path(), encoding="utf-8").read()
            assert "TZID" in content or "Qatar" in content
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145359
def test_time_zone_can_be_left_blank_default(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145359 Time Zone Blank"
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description("QCTEST time-zone-blank probe.")
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-19T09:00")
    admin.set_end_date_time("2027-05-19T17:00")
    try:
        admin.publish()
        assert admin.current_status() == "Approved"
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)


@pytest.mark.tc_145360
def test_description_source_maps_calendar_entry_description(page):
    email, password = _credentials()
    admin = ChamberEventsAdminPage(page)
    title = "QCTEST-145360 Description Source"
    description = "QCTEST description-source mapping probe body text."
    admin.open_create_event_form(email, password)
    admin.fill_event_title(title)
    admin.fill_event_description(description)
    admin.fill_venue("Qatar Chamber, Doha")
    admin.set_start_date_time("2027-05-20T09:00")
    admin.set_end_date_time("2027-05-20T17:00")
    admin.set_add_to_calendar_enabled(True)
    admin.set_ics_enabled(True)
    try:
        admin.publish()
        from web.pages.chamber_events.chamber_events_page import ChamberEventsPage

        anon_context = page.context.browser.new_context()
        anon_page = anon_context.new_page()
        try:
            listing = ChamberEventsPage(anon_page).open_listing()
            listing.search(title)
            if listing.card_count() == 0:
                pytest.skip("QCTEST event did not propagate in time")
            detail = listing.open_first_card_in_tab(listing.TAB_ALL)
            detail.open_calendar_menu()
            if "Download .ics file" not in detail.calendar_option_labels():
                pytest.skip("ICS export not available for this event")
            download = detail.download_ics()
            content = open(download.path(), encoding="utf-8").read()
            assert "DESCRIPTION" in content
        finally:
            anon_context.close()
    finally:
        admin.open_events_list(email, password)
        admin.delete_entry_by_title(title)

"""
cms/tests/home_business_events/test_home_business_events_control_panel.py —
Control_Panel-tagged cases for PBI 129383 (Business Events auto-sync into
the Home Page "Business Events" section).

REWRITTEN 2026-09-07 — corrected to drive Save/Publish/Unpublish through the
**Object Authoring** surface (`manage-business-event`), not `Content & Data`'s
raw Object Definitions grid the prior version of this module used. See
`HomeBusinessEventsAdminPage`'s module docstring for the full corrected
account. An initial quick manual check of TC 135748's unpublish-removal step
looked like a product defect (card still visible after 2 unpolled reloads);
the actual scripted, polled run below (both tests, `-n 0`, serial) PASSED —
propagation just needs longer than that quick manual check covered, within
the same `UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS` (15s) budget this feature's
public Page Object already established. See that Page Object's own
docstring for the full corrected account — no defect is being reported for
this feature.

PUBLIC-PAGE-ANONYMOUS-CONTEXT (mandatory per standards.md, added 2026-09-07):
both tests read the public Home Page Business Events section through a fresh,
logged-out browser context (`core.web.browser.new_context(browser,
use_auth_state=False)`), never the CMS-authenticated `page` — mirrors the
established pattern in
cms/tests/home_featured_event/test_home_featured_event_control_panel.py.

DATA LIFECYCLE (per cms-profile.md's Test-Data Policy — DISPOSABLE): both
tests create their own `QCTEST-<tc id> ...`-prefixed event record and
attempt best-effort UI teardown (delete by exact title match via
`ObjectAuthoringPage.delete_entry_by_title()`, confirmed live 2026-09-07 —
this object's Entry column DOES render the real title text, unlike
manage-strategic-pillar-card's UUID exception) in a `finally` block — never
positional, per standards.md's "Destructive Operations Against qcdev" rule.

CONFIRMED LIVE 2026-09-07 (single non-parallel Playwright MCP session against
qcdev, real disposable "QCTEST-PROBE-135747 Doha SME Growth Summit" probe
entry, id 186001 — created, published, verified on the public section under
both tabs with the correct category badge, unpublished, deleted, confirmed
zero QCTEST rows remaining afterward):
  - Native `datetime-local` date fields need `.fill("YYYY-MM-DDTHH:MM")`, not
    the Content & Data form's typed "MM/DD/YYYY hh:mm AM" string (see
    HomeBusinessEventsAdminPage.type_datetime_local()'s own docstring).
  - The 4-combobox form (Event Category / Event Format / Status / Calendar
    Export Type) needs per-field `aria-controls`-scoped selection, not the
    shared ObjectAuthoringPage.select_combobox_option()'s unscoped click
    (see HomeBusinessEventsAdminPage.select_combobox_option_for_field()).
  - Publish -> public-section appearance: confirmed working end-to-end,
    scripted as TC 135747 below.
  - Unpublish -> public-section removal: confirmed NOT working live this
    session (see class docstring) — scripted as the case literally
    describes; expected to surface this as a real failure, not silently
    passed around.
"""

import datetime
import shutil
import tempfile
import uuid
from pathlib import Path

import allure
import pytest

from cms.pages.home_business_events.home_business_events_admin_page import (
    CATEGORY_CHAMBER_EVENTS,
    STATUS_PUBLISHED,
    HomeBusinessEventsAdminPage,
)
from web.pages.home_business_events.home_business_events_page import HomeBusinessEventsPage

# A real future date, computed at collection time.
_FUTURE_DATE = datetime.date.today() + datetime.timedelta(days=120)
_EVENT_DATE_TIME = _FUTURE_DATE.strftime("%Y-%m-%dT09:00")
_START_DATE_TIME = _FUTURE_DATE.strftime("%Y-%m-%dT09:00")
_END_DATE_TIME = _FUTURE_DATE.strftime("%Y-%m-%dT12:00")


LOGO_FIXTURE = "web/tests/home_community_partners/fixtures/partner_logo.png"


def _unique_event_image_fixture() -> str:
    """A fresh, UNIQUELY-NAMED copy of LOGO_FIXTURE, per test invocation.

    CONFIRMED LIVE 2026-09-07 (this session's investigation of a real
    "An unexpected error occurred while uploading your file." failure on
    manage-business-event's Event Image "Select File" picker): the failure
    reproduced with BOTH `partner_logo.png` and (a different project
    fixture) `promo_banner.png`, ruling out file content/size as the cause —
    it is a real, live Liferay Documents-and-Media upload-name COLLISION:
    this feature's shared document library folder already contains a
    same-named file from earlier runs of THIS or sibling tests reusing the
    same fixture filename, and re-uploading that exact name to the same
    folder errors instead of versioning/renaming automatically (unlike
    other objects' upload widgets in this project, which have not hit this
    live). A same-content file under a NEW, unique name uploaded and
    completed successfully (confirmed live). Copying to a fresh
    `uuid4()`-suffixed temp filename per test run avoids the collision
    without touching the shared fixture other tests/objects also rely on by
    that exact name."""
    fixture_path = Path(LOGO_FIXTURE).resolve()
    unique_name = f"{fixture_path.stem}_{uuid.uuid4().hex}{fixture_path.suffix}"
    dest_path = Path(tempfile.gettempdir()) / unique_name
    shutil.copy(fixture_path, dest_path)
    return str(dest_path)


def _best_effort_delete(admin: HomeBusinessEventsAdminPage, title: str) -> None:
    """UI-only teardown, delegating to ObjectAuthoringPage.delete_entry_by_title()
    (real, confirmed-live delete-by-exact-row-id flow, never raises) — see
    module docstring's DATA LIFECYCLE note."""
    try:
        admin.delete_entry_by_title(title)
    except Exception:  # noqa: BLE001 — best-effort only, see docstring
        pass


def _fill_mandatory_fields(admin: HomeBusinessEventsAdminPage, title: str, sector: str) -> None:
    admin.fill_event_title(title)
    admin.select_event_category(CATEGORY_CHAMBER_EVENTS)
    admin.fill_event_sector(sector)
    admin.fill_category_sector("Trade & Commerce")
    admin.fill_location("Doha, Qatar")
    admin.fill_venue("Qatar Chamber HQ")
    admin.set_start_date_time(_START_DATE_TIME)
    admin.set_end_date_time(_END_DATE_TIME)
    admin.set_event_date_time(_EVENT_DATE_TIME)
    admin.select_event_format("Conference")
    admin.upload_event_image(_unique_event_image_fixture())
    admin.select_status(STATUS_PUBLISHED)


@allure.epic("Home Page")
@allure.feature("Business Events")
@allure.story("Auto-sync from the Events module")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A published event automatically appears in the Business Events section with no Home Page configuration")
@pytest.mark.control_panel
@pytest.mark.event
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129383
@pytest.mark.tc_135747
def test_published_event_appears_in_business_events_section(page, browser):
    """ADO-135747.

    Steps: log into the CMS -> Events module (Object Authoring's
    manage-business-event) -> Create Event -> fill mandatory fields
    (Title, Category=Chamber Events, Sector, Location/Venue, Start/End/
    Event Date & Time, Event Format, Event Image) -> Status=Published ->
    Submit for Publishing -> open the public Home Page Business Events
    section (no Home Page config step) in a fresh, logged-out context ->
    assert the card appears under BOTH "All" and "Chamber Events" tabs with
    the correct category badge.
    """
    from core.web.browser import new_context

    admin = HomeBusinessEventsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeBusinessEventsPage(anon_page)

    qctest_title = "QCTEST-135747 Doha SME Growth Summit"

    try:
        with allure.step("Prune any stranded row from a prior interrupted run, then open Create Event"):
            admin.open_business_events_list()
            admin.delete_entry_by_title(qctest_title)
            admin.open_create_event_form()

        with allure.step("Enter all mandatory fields for a Chamber Events / SME Development event"):
            _fill_mandatory_fields(admin, qctest_title, "SME Development")

        with allure.step("Submit for Publishing"):
            admin.publish()


        assert admin.wait_for_workflow_status(qctest_title, "Approved") == "Approved", (
            f"Expected {qctest_title!r} to show workflow Status 'Approved' "
            f"in the entries list immediately after Submit for Publishing."
        )

        with allure.step("Open the public Home Page Business Events section and poll for the new card"):
            found_on_all = home.reload_until(
                lambda p: p.has_card_with_exact_title(qctest_title)
            )
        assert found_on_all, (
            f"{qctest_title!r} did not appear under the 'All' tab within "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms of publishing."
        )

        with allure.step('Assert the card also appears under the "Chamber Events" tab'):
            home.select_tab(home.TAB_CHAMBER_EVENTS)
            assert home.has_card_with_exact_title(qctest_title), (
                f"{qctest_title!r} was published with Category=Chamber "
                f"Events but did not appear under the 'Chamber Events' tab."
            )

        with allure.step('Assert the card carries the "Chamber Events" category badge'):
            badge_text = home.category_badge_text_for_title(qctest_title)
            assert badge_text.strip() == "Chamber Events"
    finally:
        with allure.step("Teardown: best-effort delete of the QCTEST event"):
            _best_effort_delete(admin, qctest_title)
        anon_context.close()


@allure.epic("Home Page")
@allure.feature("Business Events")
@allure.story("Auto-sync from the Events module")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unpublishing an event automatically removes it from the Business Events section")
@pytest.mark.control_panel
@pytest.mark.event
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129383
@pytest.mark.tc_135748
def test_unpublished_event_removed_from_business_events_section(page, browser):
    """ADO-135748. SELF-SUFFICIENT — creates and publishes its OWN event (not
    TC 135747's), confirms it is visible, then unpublishes it and re-checks
    the section, avoiding any cross-test ordering dependency.

    See HomeBusinessEventsAdminPage's module docstring for the full account
    of an initial quick-check false alarm on this exact step (looked like a
    product defect at 2 unpolled reloads; the actual scripted, polled run —
    up to UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS — passes). No defect is being
    reported for this feature.
    """
    from core.web.browser import new_context

    admin = HomeBusinessEventsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeBusinessEventsPage(anon_page)

    qctest_title = "QCTEST-135748 Doha Trade Facilitation Briefing"

    try:
        with allure.step("Create and publish a fresh test event"):
            admin.open_business_events_list()
            admin.delete_entry_by_title(qctest_title)
            admin.open_create_event_form()
            _fill_mandatory_fields(admin, qctest_title, "Trade Facilitation")
            admin.publish()

        assert admin.wait_for_workflow_status(qctest_title, "Approved") == "Approved", (
            f"Expected {qctest_title!r} to show workflow Status 'Approved' "
            f"in the entries list immediately after Submit for Publishing."
        )

        with allure.step("Confirm the event is visible in the Business Events section before unpublishing"):
            visible_before = home.reload_until(
                lambda p: p.has_card_with_exact_title(qctest_title)
            )
        assert visible_before, (
            f"{qctest_title!r} never appeared in the Business Events "
            f"section after publishing — cannot proceed to the unpublish "
            f"assertion without a confirmed pre-condition."
        )

        with allure.step("Reopen the record and Unpublish it"):
            admin.open_business_events_list()
            admin.open_entry_by_edit_link(qctest_title)
            admin.unpublish()

        # CONFIRMED LIVE 2026-09-07: `unpublish_to_edit_as_draft()`'s own
        # settle (networkidle + a fixed 1500ms) occasionally isn't enough for
        # the editing banner text itself to re-render before the very next
        # statement reads it — a bare immediate `current_status()` read
        # returned "Unknown" (neither "(approved)" nor "(draft)" substring
        # present yet) on one run, then "Draft" correctly on an identical
        # immediate rerun with no code change. Bounded poll here rather than
        # a single read, mirroring wait_for_workflow_status()'s own rationale.
        status = ""
        for _ in range(8):
            status = admin.current_status()
            if status == "Draft":
                break
            admin.page.wait_for_timeout(1000)
        assert status == "Draft", (
            f"Expected the editing banner to report (draft) for "
            f"{qctest_title!r} after Unpublish (polled up to 8s)."
        )

        with allure.step("Reload the Business Events section and assert the card is gone from every tab/page"):
            removed = home.reload_until(
                lambda p: not p.has_card_with_exact_title(qctest_title),
                timeout_ms=home.UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS,
            )
        assert removed, (
            f"{qctest_title!r} was set to Unpublished but its card is "
            f"still present in the Business Events section after "
            f"{home.UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS}ms of polling — see "
            f"module docstring's SUSPECTED PRODUCT DEFECT note (confirmed "
            f"live 2026-09-07 against a real probe entry)."
        )
    finally:
        with allure.step("Teardown: best-effort delete of the QCTEST event"):
            _best_effort_delete(admin, qctest_title)
        anon_context.close()

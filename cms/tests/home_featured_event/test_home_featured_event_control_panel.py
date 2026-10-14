"""
cms/tests/home_featured_event/test_home_featured_event_control_panel.py —
Control_Panel cases for PBI 129382 (Home Page "Upcoming Featured Event").

Rewritten 2026-10-07 (phase 3):
  - Surface: Object Authoring, `manage-upcoming-event-pin` (object
    `UpcomingEventPin`, Content-Admin-Guide §10). The old Content & Data path
    and the TEST_USER fallback login are gone.
  - Every test names the account it runs as, resolved through
    `cms_role_credentials()`. TEST_USER is never used.
  - Public checks use a fresh logged-out context.

TWO KINDS OF TEST IN THIS FILE
  1. READ-ONLY (no xdist group): open forms and lists, never save. Safe to run.
  2. WRITES TO THE LIVE PIN 49205 (`xdist_group("pin_event_49205")`): every
     case whose steps pin / unpin / re-save the configuration. 49205 is the
     real Home Page pin, so these need the user's ID-named approval before
     they run. They are real tests — snapshot first, verified restore in
     `finally` — and they are NOT in the phase-3 run list until approved.

The 2026-08-31 "confirmed defect" (pinnedEvent ignored by the Home card) was
observed as TEST_USER through Content & Data, before the 7-state workflow
rules. It is unverified under the current flow; 135669 below re-tests it.
"""

import allure
import pytest

from cms.pages.home_featured_event.home_featured_event_admin_page import (  # noqa: F401 — fixture import
    HomeFeaturedEventAdminPage,
    approved_49205_write,
)
from web.pages.home_featured_event.home_featured_event_page import HomeFeaturedEventPage

EDITOR = "Site Content Editor"
AUTHOR = "Site Content Author"
MEMBER = "Site Member"
ACCESS_DENIED_EN = "Access Denied. You do not have permission to perform this action."
LOGGED_OUT = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)

common = [
    allure.epic("Home Page"),
    allure.feature("Upcoming Featured Event"),
    pytest.mark.control_panel,
    pytest.mark.event,
    pytest.mark.pbi_129382,
]


def _marks(fn):
    for m in reversed(common):
        fn = m(fn)
    return fn


# ═════════════════════════════════ READ-ONLY ═════════════════════════════════

@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135653
@allure.title("The Upcoming Event Pin configuration is reachable from Object Authoring")
def test_pin_configuration_reachable_from_authoring(page):
    """ADO-135653. Account: Site Content Editor. Read-only."""
    admin = HomeFeaturedEventAdminPage(page).sign_in_as(EDITOR)
    with allure.step("Open Object Authoring and pick 'Upcoming Event Pin' from the sidebar"):
        admin.open_object_authoring_index()
        assert admin.sidebar_has_entry(), "'Upcoming Event Pin' is missing from the Object Authoring sidebar"
        admin.open_from_sidebar()
    assert admin.pin_form_present(), "the Pin configuration form does not show Pinned Event + Active Status"


@_marks
@pytest.mark.security
@pytest.mark.tc_135661
@allure.title("A Site Content Editor gets read/write access to the Pin configuration")
def test_editor_has_read_write_access(page):
    """ADO-135661. Account: Site Content Editor. Read-only: proves the
    controls are editable and the live row offers edit/workflow actions,
    never saves."""
    admin = HomeFeaturedEventAdminPage(page).sign_in_as(EDITOR)
    admin.open_entries_list()
    actions = admin.live_pin_row_actions()
    allure.attach(str(sorted(actions)), name="row actions on 49205", attachment_type=allure.attachment_type.TEXT)
    assert "edit" in actions, f"Editor is not offered Edit on the live pin: {actions}"
    assert "unpublish" in actions, f"Editor is not offered Unpublish on the live pin: {actions}"
    admin.open_live_pin_read_only()
    assert admin.pin_form_editable(), "Pinned Event / Active Status are not editable for the Editor"


@_marks
@pytest.mark.security
@pytest.mark.tc_135662
@allure.title("A user without Home Page permission is denied the Pin configuration")
def test_site_member_denied_pin_configuration(page):
    """ADO-135662. Account: Site Member (signs in, holds no content role).
    Asserts the denial positively: login succeeded, and the manage page
    renders neither the form nor any entries. The exact 'Access Denied' copy
    is recorded, not asserted (message wording is not a bug on this project)."""
    admin = HomeFeaturedEventAdminPage(page).sign_in_as(MEMBER)
    admin.open_manage_page_raw()
    body = admin.body_text()
    allure.attach(body[:1500], name="what the Site Member sees", attachment_type=allure.attachment_type.TEXT)
    assert not admin.login_form_visible(), "Site Member login did not hold — denial would be meaningless"
    assert not admin.pin_form_present(), "Site Member can see the Pin configuration form"
    assert page.locator("table tbody tr", has_text=admin.LIVE_PIN_CODE).count() == 0, "Site Member sees the pin entries"
    allure.attach(str(ACCESS_DENIED_EN in body), name="EN Access Denied copy shown", attachment_type=allure.attachment_type.TEXT)


@_marks
@pytest.mark.security
@pytest.mark.tc_135663
@LOGGED_OUT
@allure.title("Logged out: the Pin configuration URL redirects to the Liferay login")
def test_logged_out_direct_url_redirects_to_login(page):
    """ADO-135663. Account: none (fresh logged-out context)."""
    admin = HomeFeaturedEventAdminPage(page)
    admin.open_manage_page_raw()
    allure.attach(page.url, name="landed on", attachment_type=allure.attachment_type.TEXT)
    assert not admin.pin_form_present(), "the Pin configuration form rendered without a session"
    assert admin.login_form_visible(), (
        f"expected a redirect to the Liferay login page, landed on {page.url} "
        f"({page.title()!r})")


@_marks
@pytest.mark.security
@pytest.mark.tc_135664
@allure.title("A Site Content Author cannot change the live Pin configuration")
def test_author_cannot_change_live_pin(page):
    """ADO-135664. Account: Site Content Author. Read-only — never clicks
    Save. Asserts the live pin's row offers the Author no edit / publish /
    unpublish / delete action. Whether the bilingual 'Access Denied' copy
    appears is recorded, not asserted."""
    admin = HomeFeaturedEventAdminPage(page).sign_in_as(AUTHOR)
    admin.open_entries_list()
    actions = admin.live_pin_row_actions()
    allure.attach(str(sorted(actions)), name="Author row actions on 49205", attachment_type=allure.attachment_type.TEXT)
    forbidden = actions & {"edit", "publish", "unpublish", "delete", "approve", "archive"}
    assert not forbidden, f"Author is offered write actions on the live pin: {forbidden}"


@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135672
@allure.title("Pin configuration exposes only Pinned Event + Active Status (no manual event fields)")
def test_pin_configuration_has_no_manual_event_detail_fields(page):
    """ADO-135672 step 2. Account: Site Content Editor. Read-only: opens the
    live pin's form, never saves. Steps 1 and 3 (select + save + Home check)
    write to 49205 — see test_pinned_event_details_sourced_from_events_module."""
    admin = HomeFeaturedEventAdminPage(page).sign_in_as(EDITOR)
    admin.open_live_pin_read_only()
    names = admin.object_field_names()
    allure.attach(str(sorted(names)), name="ObjectField_* on the form", attachment_type=allure.attachment_type.TEXT)
    assert names == {"pinnedEvent", "activeStatus"}, f"unexpected fields on the Pin form: {names}"


@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135654
@allure.title("The Event Selector lists the published events")
def test_event_selector_lists_published_events(page):
    """ADO-135654. Account: Site Content Editor. Opens the NEW-entry form
    (not the live record), focuses the Pinned Event control, never saves."""
    admin = HomeFeaturedEventAdminPage(page).sign_in_as(EDITOR)
    admin.authoring.open_new_entry_form(locale="en")
    allure.attach(admin.pinned_event_input_type(), name="Pinned Event input type", attachment_type=allure.attachment_type.TEXT)
    opened = admin.open_pinned_event_selector()
    assert opened, "focusing Pinned Event opens no event list (the control is a plain text input)"
    assert admin.selector_option_texts(), "the Event Selector opened but lists no events"


# ══════════════════ WRITES TO LIVE PIN 49205 — APPROVAL REQUIRED ══════════════════
# Not in the phase-3 run list. Each snapshots 49205 first and restores it in
# `finally` with a reopen-and-compare check.

def _anon_home(browser):
    from core.web.browser import new_context
    ctx = new_context(browser, use_auth_state=False)
    return ctx, HomeFeaturedEventPage(ctx.new_page())


def _published_event_href(browser) -> str:
    """The detail URL of a published event, read from the public Events listing."""
    ctx, home = _anon_home(browser)
    try:
        from config.settings import control_panel_url
        home.open(control_panel_url("/web/qatar-chamber/events"))
        link = home.page.locator('a[href*="event?id="]').first
        link.wait_for(state="attached", timeout=30000)
        return link.get_attribute("href")
    finally:
        ctx.close()


def _pin_and_check(page, browser, value: str, active: bool, visible_before: bool = False, expect_stored: bool = True):
    """Editor writes (value, active) to 49205, publishes, then hands back a
    fresh logged-out Home Page. Returns (admin, snapshot, home, ctx); the
    caller restores in `finally`.

    visible_before: assert the section is visible to a visitor BEFORE the
      write — a "hidden after" assertion is meaningless otherwise (the live
      pin can already be hidden for an unrelated reason, see report G1).
    expect_stored: reopen the record and assert the write actually persisted
      (Pinned Event is `required`, so a refused publish writes nothing)."""
    admin = HomeFeaturedEventAdminPage(page).sign_in_as(EDITOR)
    admin.open_live_pin_read_only()
    snap = admin.snapshot()
    allure.attach(str(snap), name="49205 snapshot", attachment_type=allure.attachment_type.TEXT)
    ctx, home = _anon_home(browser)
    if visible_before:
        home.open_home()
        assert home.is_section_visible(), "precondition: section must be visible to a visitor before the change"
    admin.open_for_edit().set_pinned_event(value).set_active(active).publish()
    if expect_stored:
        admin.open_live_pin_read_only()
        stored = admin.snapshot()
        if stored != {"pinnedEvent": value, "activeStatus": active}:
            admin.restore(snap)
            ctx.close()
            pytest.fail(f"the write did not persist on 49205: stored {stored}")
    return admin, snap, home, ctx


@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135669
@pytest.mark.xdist_group("pin_event_49205")
@pytest.mark.usefixtures("approved_49205_write")
@allure.title("Pinning a published event with Active Status on shows it on the Home Page")
def test_pin_published_event_shows_on_home(page, browser):
    """ADO-135669. Account: Site Content Editor (Publish goes live directly).
    WRITES 49205 — approval required."""
    href = _published_event_href(browser)
    admin, snap, home, ctx = _pin_and_check(page, browser, href, True)
    try:
        shown = home.reload_until(lambda p: p.is_section_visible() and p.media_href().endswith(href.split("/")[-1]))
        assert shown, f"Home card did not switch to the pinned event {href}"
    finally:
        admin.restore(snap)
        ctx.close()


@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135670
@pytest.mark.xdist_group("pin_event_49205")
@pytest.mark.usefixtures("approved_49205_write")
@allure.title("Unpinning the featured event hides the Upcoming Events section")
def test_unpin_hides_section(page, browser):
    """ADO-135670. Account: Site Content Editor. Unpin = clear Pinned Event
    and publish. WRITES 49205 — approval required."""
    admin, snap, home, ctx = _pin_and_check(page, browser, "", True, visible_before=True)
    try:
        assert home.reload_until(lambda p: not p.is_section_visible()), "section still visible after unpinning"
    finally:
        admin.restore(snap)
        ctx.close()


@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135671
@pytest.mark.xdist_group("pin_event_49205")
@pytest.mark.usefixtures("approved_49205_write")
@allure.title("Pinning a different event replaces the featured one with no duplicate section")
def test_repin_replaces_without_duplicate(page, browser):
    """ADO-135671 (P3, previously scripted). Account: Site Content Editor.
    WRITES 49205 — approval required."""
    href = _published_event_href(browser)
    admin, snap, home, ctx = _pin_and_check(page, browser, href, True)
    try:
        home.reload_until(lambda p: p.is_section_visible())
        assert home.page.locator(home.SECTION).count() == 1, "more than one Upcoming Event section rendered"
        assert home.media_href().endswith(href.split("/")[-1]), "the card still shows the previous event"
    finally:
        admin.restore(snap)
        ctx.close()


@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135673
@pytest.mark.tc_135705
@pytest.mark.xdist_group("pin_event_49205")
@pytest.mark.usefixtures("approved_49205_write")
@allure.title("Active Status off hides the section while an event stays pinned")
def test_active_status_off_hides_section(page, browser):
    """ADO-135673 / ADO-135705. Account: Site Content Editor. WRITES 49205."""
    href = _published_event_href(browser)
    admin, snap, home, ctx = _pin_and_check(page, browser, href, True)
    try:
        assert home.reload_until(lambda p: p.is_section_visible()), "precondition: section not visible with the event pinned + active"
        admin.open_for_edit().set_active(False).publish()
        admin.open_live_pin_read_only()
        assert admin.is_active() is False and admin.pinned_event_value() == href, "Active Status off did not persist (or the pin was lost)"
        assert home.reload_until(lambda p: not p.is_section_visible()), "section visible with Active Status off"
    finally:
        admin.restore(snap)
        ctx.close()


@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135704
@pytest.mark.tc_135698
@pytest.mark.xdist_group("pin_event_49205")
@pytest.mark.usefixtures("approved_49205_write")
@allure.title("Saving a published event with Active Status on stores the pin and shows the section")
def test_active_status_on_stores_pin_and_shows_section(page, browser):
    """ADO-135704 / ADO-135698. Account: Site Content Editor. WRITES 49205."""
    href = _published_event_href(browser)
    admin, snap, home, ctx = _pin_and_check(page, browser, href, True)
    try:
        admin.open_live_pin_read_only()
        assert admin.pinned_event_value() == href and admin.is_active(), "pin not stored"
        assert home.reload_until(lambda p: p.is_section_visible()), "section not visible with Active Status on"
    finally:
        admin.restore(snap)
        ctx.close()


@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135672
@pytest.mark.xdist_group("pin_event_49205")
@pytest.mark.usefixtures("approved_49205_write")
@allure.title("The pinned event's card details come from the Events module record")
def test_pinned_event_details_sourced_from_events_module(page, browser):
    """ADO-135672 steps 1 + 3. Account: Site Content Editor. WRITES 49205."""
    href = _published_event_href(browser)
    admin, snap, home, ctx = _pin_and_check(page, browser, href, True)
    try:
        assert home.reload_until(lambda p: p.is_section_visible()), "section not visible"
        card = home.card_snapshot()
        home.open(href)
        detail = home.body_text()
        assert card["title"] in detail and card["location"] in detail, f"card {card} differs from the event record"
    finally:
        admin.restore(snap)
        ctx.close()


@_marks
@pytest.mark.functional_high
@pytest.mark.tc_135701
@pytest.mark.xdist_group("pin_event_49205")
@pytest.mark.usefixtures("approved_49205_write")
@allure.title("Active Status on with no Pinned Event is refused")
def test_active_without_pinned_event_refused(page, browser):
    """ADO-135701. Account: Site Content Editor. WRITES 49205 if the product
    accepts the save — approval required."""
    admin, snap, home, ctx = _pin_and_check(page, browser, "", True, expect_stored=False)
    try:
        admin.open_live_pin_read_only()
        assert admin.pinned_event_value() == snap["pinnedEvent"], "an empty Pinned Event was saved with Active Status on"
    finally:
        admin.restore(snap)
        ctx.close()


@_marks
@pytest.mark.security
@pytest.mark.tc_135716
@pytest.mark.xdist_group("pin_event_49205")
@pytest.mark.usefixtures("approved_49205_write")
@allure.title("A user without permission cannot save the pin through a direct request")
def test_direct_save_request_rejected(page, browser):
    """ADO-135716. Account: Site Member. Sends a direct PATCH to 49205 that
    re-states its CURRENT values; the expected outcome is a 401/403 and no
    change. If the server wrongly accepts it, 49205 is written — approval
    required."""
    from config.settings import control_panel_url
    admin = HomeFeaturedEventAdminPage(page).sign_in_as(EDITOR)
    admin.open_live_pin_read_only()
    snap = admin.snapshot()
    admin.sign_in_as(MEMBER)
    admin.open(control_panel_url("/home"))
    status = page.evaluate(
        """async ([u, body]) => (await fetch(u, {method: 'PATCH', credentials: 'include',
             headers: {'Content-Type': 'application/json', 'x-csrf-token': (window.Liferay && Liferay.authToken) || ''},
             body: JSON.stringify(body)})).status""",
        [control_panel_url(f"/o/c/upcomingeventpins/{admin.LIVE_PIN_ID}"), snap],
    )
    admin.sign_in_as(EDITOR)
    admin.open_live_pin_read_only()
    assert admin.snapshot() == snap, "49205 changed after the Site Member's direct request"
    assert status in (401, 403), f"direct save by Site Member returned HTTP {status}"

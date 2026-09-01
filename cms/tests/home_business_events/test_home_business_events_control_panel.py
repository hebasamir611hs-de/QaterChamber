"""
web/tests/home_business_events/test_home_business_events_control_panel.py —
Control_Panel-tagged cases for PBI 129383 (Business Events auto-sync into
the Home Page "Business Events" section).

Scope this batch (2026-08-31, single non-parallel Playwright MCP session
against qcdev — see home_business_events_admin_page.py's module docstring
for the full live-exploration record this batch is built on):

  - TC 135747 (tc_135747): an event published in the Events module
    automatically appears in the public Business Events section with no
    Home Page configuration step.
  - TC 135748 (tc_135748): unpublishing an event automatically removes it
    from the Business Events section. Made SELF-SUFFICIENT per the task's
    explicit instruction (create-then-unpublish its own event, no ordering
    dependency on TC 135747's run).

DISCLOSED SUBSTITUTION (same pattern already established by
gm_message_admin_page.py / test_gm_message_control_panel.py's tc_135453):
this Object Definition's create/edit form exposes only Save/Cancel plus a
Status combobox (Draft / Published / Unpublished) — there is no separate
"Submit for Review" step or button anywhere on the form (confirmed live via
a full button-text dump of the rendered form). Both TCs' "submit for
review, publish" / "unpublish" steps are satisfied by setting Status via
`select_status()`.

DATA LIFECYCLE (per cms-profile.md's Test-Data Policy — DISPOSABLE):
both tests create their own `QCTEST-<tc id> ...`-prefixed event record and
attempt best-effort UI teardown (open the Business Events list, locate the
row by its exact title, delete it) in a `finally` block. cms-profile.md's
current team decision is UI-only teardown with no API-based delete
available; a delete/kebab action on this Object Definition's list grid was
NOT independently confirmed live this session (no real Save was completed
to produce a live row to test deletion against — see
home_business_events_admin_page.py's SAVE/TOAST note). `_best_effort_delete()`
below therefore tries the same "row kebab -> Delete" shape already
confirmed on other Object Definition grids in this project
(BoardMembersAdminPage's own precedent) but swallows a failure rather than
failing the test on cleanup — a leftover `QCTEST-`-prefixed row is
disclosed as an accepted, identifiable, prunable artifact per
cms-profile.md's own namespace-prefix convention, never silently hidden.

ENVIRONMENT FINDING, disclosed rather than worked around silently: this
session reproduced (twice, independently) a spontaneous navigation away
from this exact admin form to an UNRELATED record
(`QCDEMO-129381-STRATEGIC_PILLAR_CARD-02`, a different PBI's Object
Definition) immediately after an in-form interaction — see
home_business_events_admin_page.py's module docstring for the full
investigation (Escape-key and interaction-type were both ruled out as the
sole trigger via isolated live re-tests). No `QCTEST`-prefixed record was
left behind by that investigation (confirmed live: the list showed zero
`QCTEST` matches immediately after). If this run also hits it, the
resulting failure is this documented, real qcdev/Liferay-admin-SPA
environment behavior — not a locator defect in HomeBusinessEventsAdminPage.

OPEN QUESTION carried into both tests: which date field
(`eventDateTime` vs `startDateTime`/`endDateTime`) actually drives the
public card's rendered date/time line was not resolved live (no completed
Save to read a card back against). Both tests fill all three with the same
future value so the assertion does not depend on the answer.

FOLLOW-UP INVESTIGATION (2026-08-31, root-causing a batch pytest run's
failures on tc_135747/tc_135748 — re-verified LIVE against qcdev this
session with real network-response capture):
  - `test_published_event_appears_in_business_events_section` failed with
    "Save reported a validation error" whose CAPTURED diagnostic text was
    the entire page navigation menu — this was traced to the failing
    assertion's OWN `admin.page.locator('body').inner_text()[:300]` debug
    slice, not to `is_save_error_shown()`/`save_error_text()` being
    over-broad. Both were re-confirmed live to correctly resolve to the
    real, field-specific banner every time. The REAL cause: this form's
    mandatory-field set is larger than originally scripted — Category /
    Sector (`categorySector`, a field SEPARATE from Event Sector), Event
    Format, and Event Image are ALSO confirmed-live required, and neither
    original test filled any of the three, so Save genuinely failed
    validation every run (confirmed live: filling all three lets a real
    create POST fire and return 200). Both tests now fill all three; the
    failure message now uses `admin.save_error_text()` (added this session)
    instead of the raw body slice.
  - `test_unpublished_event_removed_from_business_events_section`'s reported
    30s timeout is the SAME root cause, one step further downstream: Save
    never actually created a row (blocked by the same missing mandatory
    fields), so `admin.wait_for(admin.row_for_title(qctest_title),
    timeout=15000)` after "Confirm...before unpublishing" legitimately never
    resolves, and per BasePage.wait_for()'s own documented recovery path
    (see gm_message_admin_page.py's ROW_ID_LINK docstring for the identical
    class of cascade), a failed wait can chain into an un-timed-out
    `session_guard.reauthenticate()` re-navigation that hits Playwright's
    own 30s default — the observed "30s timeout" symptom. Filling the real
    mandatory fields (so Save actually succeeds and a row exists to reopen)
    removes the precondition for this cascade; it was not a separate defect
    in the reopen/unpublish step itself.
  - `_best_effort_delete()`'s prior implementation reopened the EDIT form
    and clicked a bare `button:has-text("Delete")`, confirmed live this
    session to be the Event Image field's own per-file delete control, not
    a record-delete action — every prior QCTEST-135747/135748 teardown
    attempt was a silent no-op. Delegates to the admin Page Object's new
    `delete_row_by_title()` (the real list-kebab delete flow) now.
  - Investigation records created live this session ("...VERIFY", row
    112951) were deleted via the real list-kebab flow and confirmed absent
    from the list afterward — no orphaned QCTEST-prefixed record was left
    by this investigation.

FOLLOW-UP SESSION (2026-09-01, data-safety check after an overnight batch
pytest run was interrupted by machine sleep / net::ERR_NETWORK_CHANGED /
net::ERR_NETWORK_IO_SUSPENDED — root-causing the resulting STRICT MODE
VIOLATION on the public section's category-badge locator, "resolved to 2
elements"):
  - Live admin-grid check found 3 real leftover QCTEST rows: 113026 and
    113270 (both "QCTEST-135747 Doha SME Growth Summit", both
    Status=Published — the duplicate the public-page assertion collided
    on), and 113291 ("QCTEST-135748 Doha Trade Facilitation Briefing",
    Status=Published — a record stranded mid-flow by the interrupted
    overnight run BEFORE its own unpublish/delete steps ran). All three
    deleted live via HomeBusinessEventsAdminPage.delete_row_by_title();
    the grid was re-confirmed to show zero QCTEST-prefixed rows afterward.
  - ROOT CAUSE of the duplicate accumulating across runs: confirmed live
    that `delete_row_by_title()` only ever deleted the FIRST row matching
    `title` (a `:has-text` SUBSTRING match plus `kebab.first.click()`) —
    whenever a stranded duplicate from an earlier interrupted run already
    existed, one call only ever removed one of the two same-titled rows,
    silently leaving the other behind every run. Fixed to loop over EXACT
    (`:text-is`) matches, re-navigating the list between deletions, until
    none remain — see that method's own updated docstring in
    home_business_events_admin_page.py for the full account, including a
    separately confirmed-live #qcChatbot-launcher-intercepts-the-kebab-click
    finding now handled by core/web/overlays.py.
  - `test_unpublished_event_removed_from_business_events_section` (TC
    135748)'s reported 15s timeout on `admin.wait_for(row_link,
    timeout=15000)` WAS reproduced as a real, standalone code defect this
    session — NOT network fallout, contrary to this docstring's own
    initial (now superseded) assessment. `row_for_title()`'s previous
    locator, `f'{self.LIST_ROW} a:text-is("{title}")'`, assumed the Event
    Title cell itself contained the row's anchor. Confirmed live via a
    direct DOM query against the real, live grid (headers mapped to find
    the actual "Event Title" column index): the Event Title cell is a BARE
    `<td>` with no `<a>` inside it at all, and a same-session live check —
    `a:text-is(<a real, currently-rendered Event Title>)` — returned ZERO
    matches for a genuine row, not just a QCTEST one. This locator could
    never resolve for ANY title, which is exactly why the 15s wait ran out
    its full budget rather than finding a stale/wrong element; it was not
    dependent on the overnight network interruption at all. The row's only
    real anchor is its ID cell's edit link, `td.cell-id a` — the SAME class
    CommunityPartnersAdminPage's own ROW_ID_LINK precedent already
    documents for this admin-grid family (see that Page Object's own
    ROW_ID_LINK note for the identical bug class). `row_for_title()` is
    fixed to scope the row by its title cell (`:has(td:text-is(...))`,
    confirmed live to resolve to exactly 1 row for a real title) and return
    that row's `td.cell-id a` link instead — see
    home_business_events_admin_page.py's own updated docstring.

FOLLOW-UP SESSION (2026-09-01, live-investigating TC 135748's REPORTED 15s
timeout on `admin.wait_for(row_link, timeout=15000)` a second time — the
`td.cell-id a` heal recorded above was RE-CONFIRMED correct this session,
NOT the cause here): pagination was checked live and ruled out (13 rows,
single page, next/prev both `disabled` — a newly-created row is never
sorted onto a later page on this grid). The real cause this time: two rows
(115322, 115365) both carried the exact title "QCTEST-135748 Doha Trade
Facilitation Briefing", both Published — a stray duplicate left by an
earlier run that crashed before reaching this test's own `finally`
teardown. `row_for_title()`'s locator has no `.first`, so
`wait_for(row_link, timeout=15000)` (called `first=False`) hit a genuine
Playwright strict-mode violation on the 2 matches, which the recovery path
(license-gate/reauth clear) cannot fix and re-raised — surfacing as a
misleading "not found within 15s" rather than naming the real collision.
Both stray rows were deleted live; a fresh `open_business_events_list()`
navigation afterward confirmed zero QCTEST-135748 rows remained. Fix (full
account in `HomeBusinessEventsAdminPage.row_for_title()`'s own updated
docstring): the test now calls `delete_row_by_title(qctest_title)` once
before creating its own record (so a future crash-before-teardown can't
poison the next run), and asserts `rows_matching_title(qctest_title) == 1`
immediately before reopening the row, so a future duplicate fails loudly
and names the real problem instead of a phantom timeout. `.first` and an
"unpublish every matching row" loop were both considered and rejected —
TC 135748 is about ONE event's unpublish removing it from the public
section, and silently acting on an arbitrary row among duplicates (or
unpublishing all of them) would make a pass prove nothing about that
mechanism.

FOLLOW-UP SESSION (2026-09-01, live-investigating TWO NEW distinct
failures — a public-page strict-mode violation on tc_135747's category
badge, and tc_135748's "found 0" admin rows persisting even after the
`_row_by_title()` heal above):
  - tc_135747's "2 elements" collision on `.qc-be-badge--category` was
    confirmed live to be PURE DATA POLLUTION, not a locator/DOM defect: a
    direct outerHTML dump of a real card confirmed exactly ONE
    `.qc-be-badge--category` element per card (no separate mobile/desktop
    duplicate rendering) — the "2 elements" was two full DUPLICATE admin
    rows (115508, 115597) both titled "QCTEST-135747 Doha SME Growth
    Summit", both Published, left behind by an earlier interrupted run.
    Both deleted live; `card_for_exact_title()`/`category_badge_text_for_title()`
    need no change.
  - tc_135748's "found 0" is a DIFFERENT, real code gap — NOT explainable
    by data pollution (a stale same-titled row can only ever inflate
    `rows_matching_title()`'s count, never make it 0). Root-caused live:
    `save()`'s prior flat `wait_for_timeout(2000)` treated "the Save button
    was clicked" as "the record was persisted". Confirmed live this
    session, with a REAL reproduced failing create (Event Title left
    empty): `is_save_error_shown()` returned False even on this genuine
    failure (no banner text rendered in this failure shape) and
    `status_value()` reads the combobox's pre-Save DOM selection regardless
    of whether the POST committed — so both of the test's own post-Save
    asserts can pass vacuously while nothing was actually created,
    cascading into the "found 0" a few steps downstream. Confirmed live the
    real discriminator: every genuine commit navigates the URL to include
    `externalReferenceCode=<uuid>` (two independent real Saves observed
    this session); the empty-title failing Save's URL never gained it. Both
    tests now assert `admin.is_entry_persisted()` immediately after
    `admin.save()` (see that method's own new docstring in
    home_business_events_admin_page.py), and tc_135748 additionally
    re-checks `rows_matching_title(qctest_title) == 1` right after its own
    create — before the public-page poll — so a future non-commit fails at
    the real point of failure instead of resurfacing as a misleading
    downstream message. Both full TC flows (create -> publish -> verify ->
    unpublish -> verify removed, for 135748; create -> publish -> verify
    under All and Chamber Events tabs and the category badge, for 135747)
    were live-reproduced end-to-end this session and passed; all QCTEST-
    prefixed rows created during this investigation were deleted and the
    admin grid was confirmed to show zero afterward.
"""

import datetime

import allure
import pytest

from cms.pages.home_business_events.home_business_events_admin_page import HomeBusinessEventsAdminPage
from web.pages.home_business_events.home_business_events_page import HomeBusinessEventsPage

# A real future date, computed at collection time (never a fixed past-dated
# literal like the task brief's own flagged "5 May 2025" example) — see
# HomeBusinessEventsAdminPage's confirmed-live accepted format
# (DATE_FORMAT_EXAMPLE = "MM/DD/YYYY hh:mm AM").
_FUTURE_EVENT_DATE = (datetime.date.today() + datetime.timedelta(days=120)).strftime("%m/%d/%Y")
_START_DATE_TIME = f"{_FUTURE_EVENT_DATE} 10:00 AM"
_END_DATE_TIME = f"{_FUTURE_EVENT_DATE} 12:00 PM"


LOGO_FIXTURE = "web/tests/home_community_partners/fixtures/partner_logo.png"


def _best_effort_delete(admin: HomeBusinessEventsAdminPage, title: str) -> None:
    """UI-only teardown per cms-profile.md's current team decision — locate
    the row by its exact title and delete it via the row's own LIST-SCREEN
    kebab menu.

    HEALED (2026-08-31, follow-up session fixing the batch pytest run's
    failures): the PRIOR version of this helper reopened the record's EDIT
    form and clicked a bare `button:has-text("Delete")` — confirmed live
    this session that this resolves to the Event Image field's OWN per-file
    "Delete" button (removes just the uploaded image), NOT a record-delete
    action; the edit form has no delete button of its own (Save/Cancel
    only). That version was a silent no-op that never actually deleted a
    QCTEST record — delegating to
    HomeBusinessEventsAdminPage.delete_row_by_title() (the real, confirmed-
    live list-kebab delete flow, same pattern already proven on
    CommunityPartnersAdminPage) fixes that."""
    try:
        admin.delete_row_by_title(title)
    except Exception:  # noqa: BLE001 — best-effort only, see docstring
        pass


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
def test_published_event_appears_in_business_events_section(page):
    """ADO-135747.

    Steps (mapped onto the confirmed-live form, see module docstring's
    disclosed substitution): log into the CMS -> Events module (Business
    Events Object Definition) -> Create Event -> fill mandatory fields
    (Title, Category=Chamber Events, Sector, Location/Venue, Start/End/
    Event Date & Time) -> Status=Published -> Save -> no validation error
    -> open the public Home Page Business Events section (no Home Page
    config step) -> assert the card appears under BOTH "All" and "Chamber
    Events" tabs.
    """
    admin = HomeBusinessEventsAdminPage(page)
    home = HomeBusinessEventsPage(page)

    qctest_title = "QCTEST-135747 Doha SME Growth Summit"

    try:
        with allure.step("Log into the CMS and open Content & Data > Business Events > Add Business Event"):
            admin.open_business_events_list()
            # Idempotent-test guard (mirrors tc_135748's own, added
            # 2026-09-01): a run that crashed before reaching this test's
            # own teardown can strand a same-titled row from a previous
            # attempt, which then collides with this run's own card on the
            # public page (a Playwright strict-mode "2 elements" violation
            # on the badge locator, not a locator defect).
            admin.delete_row_by_title(qctest_title)
            admin.open_business_events_list()
            admin.open_create_event_form()

        with allure.step("Enter all mandatory fields for a Chamber Events / SME Development event"):
            admin.fill_text_field(admin.EVENT_TITLE, qctest_title)
            admin.select_combobox_option(admin.EVENT_CATEGORY_CONTAINER, "Chamber Events")
            admin.fill_text_field(admin.EVENT_SECTOR, "SME Development")
            # Category / Sector (categorySector) is a SEPARATE mandatory
            # field from Event Sector — confirmed live this follow-up
            # session (see admin Page Object's MANDATORY FIELDS note); the
            # prior batch's Save genuinely failed validation without it.
            admin.fill_text_field(admin.CATEGORY_SECTOR, "Trade & Commerce")
            admin.fill_text_field(admin.LOCATION, "Doha, Qatar")
            admin.fill_text_field(admin.VENUE, "Qatar Chamber HQ")
            admin.fill_date_field(admin.START_DATE_TIME, _START_DATE_TIME)
            admin.fill_date_field(admin.END_DATE_TIME, _END_DATE_TIME)
            admin.fill_date_field(admin.EVENT_DATE_TIME, _START_DATE_TIME)
            # Event Format is also confirmed-live mandatory — see the same
            # note.
            admin.select_combobox_option(admin.EVENT_FORMAT_CONTAINER, "Conference")
            # Event Image is also confirmed-live mandatory.
            admin.upload_event_image(LOGO_FIXTURE)

        with allure.step('Set Status to "Published" and Save'):
            admin.select_status("Published")
            admin.save()

        # Assert: the record saves with no validation error and Status now
        # reads "Published" (the confirmed real publish mechanism on this
        # form — see module docstring's disclosed substitution). Uses
        # save_error_text() (added this session) for the diagnostic, not a
        # raw body[:300] slice — that raw slice is what produced the
        # misleading "entire nav menu" dump in the prior batch (this admin
        # SPA's Product Menu panel sits at/near the top of `body`'s own
        # text; is_save_error_shown() itself was never broad — see
        # save_error_text()'s own docstring).
        assert not admin.is_save_error_shown(), (
            f"Save reported a validation error: {admin.save_error_text()!r}"
        )
        assert admin.status_value() == "Published"
        # HEALED (2026-09-01, see admin Page Object's save()/is_entry_persisted()
        # docstrings): the two asserts above can BOTH pass on a Save that
        # never actually committed — is_save_error_shown() was live-confirmed
        # False even on a genuine empty-title failure, and status_value()
        # only reads the pre-Save combobox selection back out of the DOM.
        # is_entry_persisted() checks the one signal confirmed live to
        # actually distinguish a real commit (the URL gaining
        # `externalReferenceCode=`) — asserted here, immediately after Save,
        # so a silent non-commit fails at THIS step naming the real problem
        # instead of surfacing several steps downstream as a confusing
        # "card never appeared" or "found 0 rows" failure.
        assert admin.is_entry_persisted(), (
            f"Save did not persist a real record for {qctest_title!r} — no "
            f"externalReferenceCode ever appeared in the URL "
            f"({admin.page.url!r}) within {admin.SAVE_COMMIT_TIMEOUT_MS}ms."
        )

        with allure.step("Open the public Home Page Business Events section and poll for the new card"):
            found_on_all = home.reload_until(
                lambda p: p.has_card_with_exact_title(qctest_title)
            )
        assert found_on_all, (
            f"{qctest_title!r} did not appear under the 'All' tab within "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms of publishing (see module "
            f"docstring's propagation-budget note)."
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
        with allure.step("Teardown: best-effort delete of the QCTEST event (see module docstring)"):
            _best_effort_delete(admin, qctest_title)


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
def test_unpublished_event_removed_from_business_events_section(page):
    """ADO-135748. SELF-SUFFICIENT per the task's explicit instruction —
    creates and publishes its OWN event (not TC 135747's), confirms it is
    visible, then unpublishes it and re-checks the section, avoiding any
    cross-test ordering dependency under pytest-xdist parallelism.
    """
    admin = HomeBusinessEventsAdminPage(page)
    home = HomeBusinessEventsPage(page)

    qctest_title = "QCTEST-135748 Doha Trade Facilitation Briefing"

    try:
        with allure.step("Create and publish a fresh test event"):
            admin.open_business_events_list()
            # Idempotent-test guard, added 2026-09-01 (see admin Page
            # Object's row_for_title() docstring, "SECOND, DISTINCT ROOT
            # CAUSE"): a run that crashed before reaching this test's own
            # teardown can strand a same-titled row from a previous attempt.
            # Pruning it here, before creating this run's own record, keeps
            # a crash-before-teardown from poisoning the NEXT run the way it
            # poisoned this one (two live QCTEST-135748 rows, 115322 and
            # 115365, were found and deleted this session).
            admin.delete_row_by_title(qctest_title)
            admin.open_business_events_list()
            admin.open_create_event_form()
            admin.fill_text_field(admin.EVENT_TITLE, qctest_title)
            admin.select_combobox_option(admin.EVENT_CATEGORY_CONTAINER, "Chamber Events")
            admin.fill_text_field(admin.EVENT_SECTOR, "Trade Facilitation")
            # Category / Sector, Event Format, Event Image are all
            # confirmed-live mandatory (see admin Page Object's MANDATORY
            # FIELDS note) — omitting them is what made the original batch's
            # Save genuinely fail validation.
            admin.fill_text_field(admin.CATEGORY_SECTOR, "Trade & Commerce")
            admin.fill_text_field(admin.LOCATION, "Doha, Qatar")
            admin.fill_text_field(admin.VENUE, "Qatar Chamber HQ")
            admin.fill_date_field(admin.START_DATE_TIME, _START_DATE_TIME)
            admin.fill_date_field(admin.END_DATE_TIME, _END_DATE_TIME)
            admin.fill_date_field(admin.EVENT_DATE_TIME, _START_DATE_TIME)
            admin.select_combobox_option(admin.EVENT_FORMAT_CONTAINER, "Conference")
            admin.upload_event_image(LOGO_FIXTURE)
            admin.select_status("Published")
            admin.save()

        assert not admin.is_save_error_shown(), (
            f"Save reported a validation error: {admin.save_error_text()!r}"
        )
        assert admin.status_value() == "Published"
        # HEALED (2026-09-01, root-causing this test's OWN reported "expected
        # exactly 1 admin row ... found 0" failure — see admin Page Object's
        # save()/is_entry_persisted() docstrings for the full account): the
        # two asserts above are BOTH satisfiable by a Save that never
        # actually committed (is_save_error_shown() was live-confirmed False
        # even on a genuine empty-title failure; status_value() only reads
        # the pre-Save combobox selection back out of the DOM). Asserting
        # is_entry_persisted() here — immediately after Save, before the
        # public-page poll or the reopen step — fails at the real point of
        # failure instead of resurfacing several steps later as a confusing
        # "found 0 rows" message that looks like a locator/data-hygiene bug.
        assert admin.is_entry_persisted(), (
            f"Save did not persist a real record for {qctest_title!r} — no "
            f"externalReferenceCode ever appeared in the URL "
            f"({admin.page.url!r}) within {admin.SAVE_COMMIT_TIMEOUT_MS}ms."
        )
        # Second guard, same root cause: confirm the ADMIN grid (not just the
        # URL) shows exactly this run's own fresh row before touching the
        # public-page poll at all — a fast, precise failure point rather than
        # trusting the public page's poll (which only checks title text and
        # would pass just as easily against a stale same-titled leftover).
        admin.open_business_events_list()
        created_count = admin.rows_matching_title(qctest_title)
        assert created_count == 1, (
            f"expected exactly 1 admin row titled {qctest_title!r} "
            f"immediately after creating it, found {created_count} — see "
            f"is_entry_persisted()'s own docstring on why a persisted-URL "
            f"check alone is not sufficient to rule out a duplicate."
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

        with allure.step('Reopen the record and set Status to "Unpublished"'):
            admin.open_business_events_list()
            # Fail loud on a duplicate BEFORE touching row_for_title()'s own
            # non-`.first` locator — see that method's own docstring
            # ("SECOND, DISTINCT ROOT CAUSE", 2026-09-01): a same-titled
            # duplicate previously turned into a Playwright strict-mode
            # violation that surfaced as a misleading 15s "not found"
            # timeout instead of naming the real problem.
            match_count = admin.rows_matching_title(qctest_title)
            assert match_count == 1, (
                f"expected exactly 1 admin row titled {qctest_title!r} "
                f"before reopening it, found {match_count} — stale QCTEST "
                f"data from an interrupted prior run; prune it (e.g. via "
                f"delete_row_by_title()) before rerunning this test."
            )
            row_link = admin.row_for_title(qctest_title)
            admin.wait_for(row_link, timeout=15000)
            admin.click(row_link)
            admin.wait_for(admin.EVENT_TITLE, timeout=15000)
            admin.select_status("Unpublished")
            admin.save()

        assert not admin.is_save_error_shown(), (
            f"Save reported a validation error: {admin.save_error_text()!r}"
        )
        assert admin.status_value() == "Unpublished"

        with allure.step("Reload the Business Events section and assert the card is gone from every tab/page"):
            # UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS (not the shared
            # RELOAD_POLL_TIMEOUT_MS default) — see HomeBusinessEventsPage's
            # module docstring, 2026-09-01 live measurement: real propagation
            # for this direction measured ~2.3s (upper bound), but the
            # original 5s budget still failed under a real pytest run's
            # added render/page-load variance. 15000ms is a ~6.5x safety
            # multiple over the measured figure, not an arbitrary round
            # number.
            removed = home.reload_until(
                lambda p: not p.has_card_with_exact_title(qctest_title),
                timeout_ms=home.UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS,
            )
        assert removed, (
            f"{qctest_title!r} was set to Unpublished but its card is "
            f"still present in the Business Events section after "
            f"{home.UNPUBLISH_REMOVAL_POLL_TIMEOUT_MS}ms of polling."
        )
    finally:
        with allure.step("Teardown: best-effort delete of the QCTEST event (see module docstring)"):
            _best_effort_delete(admin, qctest_title)

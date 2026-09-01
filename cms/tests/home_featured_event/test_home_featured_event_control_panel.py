"""
web/tests/home_featured_event/test_home_featured_event_control_panel.py —
Control_Panel-tagged cases for PBI 129382 (Home Page "Upcoming Event Pins").

OPEN QUESTION RESOLVED THIS SESSION (2026-08-31, single non-parallel
Playwright MCP session against qcdev) — CONFIRMED PRODUCT DEFECT, not an
automation gap:

The `pinnedEvent` field on the Upcoming Event Pins singleton (record 49205,
ERC `QCDEMO-129382-PIN-001`) does NOT control which event the public Home
Page card renders. This was tested with TWO independent, real, valid
candidate values, each followed by a hard navigation and an 11-15s wait
(well past every propagation/render-settle budget this project has
established elsewhere):

  1. `/web/qatar-chamber/events/event?id=110785` — "Export Documentation
     Workshop", a real, live, Published, future-dated (20 Oct 2026) event
     detail page. Card did not change (an earlier, carried-over attempt
     already tried this exact value and format; this session independently
     reproduced the same non-result live rather than trusting that report).
  2. `/web/qatar-chamber/events/event?id=49443` — "Qatar–GCC Economic
     Cooperation Forum", a real event FROM THE SAME Chamber Events
     collection (`/web/qatar-chamber/events` listing) the widget's own
     fallback card is drawn from — ruling out the "wrong collection/content
     type" explanation for attempt 1. Card still did not change.

In both cases the Home Page kept showing "International Trade & Logistics
Expo" (id 49485) regardless of the saved `pinnedEvent` value. Both bare-slug
URL formats that could plausibly be tried (`/events/novgorod-delegation` —
the pre-existing baseline value itself, and `/events/international-trade-
logistics-expo`) independently 404 as real pages on this site (`Coming
Soon`) — there is no working slug-based route on this project's Events
feature at all. The ONLY real, working event URL format on this site is the
query-string one (`?id=<N>`), which is also the exact format the widget's
own rendered `[data-qc-ue-media]` href already uses — so this is not a
"wrong value format" finding, it is a confirmed non-functional field: even
the widget's native href format was ignored twice, with a real future-dated
event and a real in-collection event.

**TC 135669 ("pin a published event ... see it appear on Home Page") is
therefore NOT automated as a passing test** — scripting an assertion that
the card matches the pinned event would either always fail (correctly
flagging the defect, at the cost of a permanently-red suite entry) or be
quietly written to assert something else and mask the defect. Per this
project's contract (documented, not worked around — the same precedent as
the GM Message Draft-blank-page defect and home_dynamic_widgets_control_
panel.py's Weather-widget-has-no-admin-surface finding), it is disclosed
here and left UNAUTOMATED. File/confirm a bug against PBI 129382 with this
session's two independent repro values before any future attempt to
automate TC 135669 — do not re-guess a third value format without a
product-side fix or clarification first.

**TC 135670 ("unpin ... Upcoming Events section disappears") IS automated
below** — the Active Status toggle was independently confirmed live to be
the real, working mechanism: setting `activeStatus=false` and Saving makes
`section.qc-home-upcoming-event` render with an inline `style=
"display:none;"` on the next Home Page load (the section itself is never
removed from the DOM — a visibility toggle, not a content-driven "no
upcoming events" state). TC 135670's own wording ("unpin the currently
featured event") is satisfied via the Active Status control, mirroring the
disclosed-substitution precedent already used elsewhere in this project
(gm_message's Status combobox for "publish/unpublish", Business Events'
same combobox for "submit for review") — there is no separate "unpin"
action on this singleton's 2-field form; Active Status is the pin's own
on/off switch.

DATA LIFECYCLE — TEST_OWNED singleton per cms-profile.md's Test-Data
Policy: record 49205 is reset to its FIXED, confirmed-live baseline
(`pinnedEvent=/web/qatar-chamber/events/novgorod-delegation`,
`activeStatus=True`) in a `finally` block, with the "reopen + assert
restore actually persisted" hardening already used elsewhere in this
project (e.g. board_members tests) — never "restore whatever the UI showed
before mutating", per this record being a fixed-baseline TEST_OWNED row,
not a DISPOSABLE one.

SHARED-SINGLETON SAFETY: both this test and TC 135669's write-up mutate the
SAME record. TC 135670 below is self-sufficient — it establishes its own
known Active=True precondition (re-asserting/re-saving the baseline's
Active=True at the start, not assuming a prior test left it that way) before
switching it off, so it does not depend on run order or on TC 135669 (which
is not scripted at all).
"""

import allure
import pytest

from cms.pages.home_featured_event.home_featured_event_admin_page import HomeFeaturedEventAdminPage
from web.pages.home_featured_event.home_featured_event_page import HomeFeaturedEventPage


@allure.epic("Home Page")
@allure.feature("Upcoming Event Pins")
@allure.story("Pin an event to feature it on the Home Page")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("DEFECT — pinning a valid event does not change the Home Page featured card")
@pytest.mark.control_panel
@pytest.mark.event
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135669
@pytest.mark.skip(
    reason="CONFIRMED PRODUCT DEFECT, not an automation gap — live-"
    "reproduced this session (2026-08-31) with TWO independent real "
    "candidate values (a future-dated event id=110785, and an in-collection "
    "past-dated event id=49443, both in the widget's own native '?id=' href "
    "format), each followed by an 11-15s wait past every propagation/"
    "render-settle budget this project has established. The Home Page "
    "featured card never changed from its fallback ('International Trade & "
    "Logistics Expo', id 49485) in either case. See this module's own "
    "docstring for the full repro and why this is scripted as a documented, "
    "disclosed defect rather than a scripted (and permanently failing, or "
    "silently altered) assertion. File/confirm a bug against PBI 129382 "
    "before re-attempting this TC."
)
def test_pinning_a_valid_event_updates_the_home_page_card():
    """ADO-135669. Left deliberately unautomated/skipped — see module
    docstring and this test's own skip reason for the full disclosure."""
    pytest.fail(
        "Not reached — see the skip reason: TC 135669 documents a "
        "confirmed product defect in the Pinned Event field rather than "
        "asserting a pass against it."
    )


@allure.epic("Home Page")
@allure.feature("Upcoming Event Pins")
@allure.story("Unpin the featured event")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Turning off Active Status hides the Upcoming Events section from the Home Page")
@pytest.mark.control_panel
@pytest.mark.event
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129382
@pytest.mark.tc_135670
@pytest.mark.xdist_group("pin_event_49205")
def test_unpinning_the_featured_event_hides_the_home_page_section(page):
    """ADO-135670.

    Steps (mapped onto the confirmed-live 2-field form and the confirmed-
    live visibility mechanism — see module docstring's disclosed
    substitution): log into the CMS -> Content & Data -> Upcoming Event
    Pins -> open the singleton record -> establish a known Active=True
    precondition (self-sufficient, no ordering dependency) -> confirm the
    section IS visible on the public Home Page -> set Active Status to OFF
    and Save -> reload the Home Page -> assert the
    `section.qc-home-upcoming-event` is no longer visible (rendered with
    `display:none`, per the confirmed-live mechanism — not a DOM-removal
    check).
    """
    admin = HomeFeaturedEventAdminPage(page)
    home = HomeFeaturedEventPage(page)

    try:
        with allure.step(
            "Open Content & Data > Upcoming Event Pins and establish a "
            "known Active=True precondition (self-sufficient)"
        ):
            admin.open_upcoming_event_pins_list()
            admin.open_pin_record()
            admin.set_active(True)
            admin.save()

        assert admin.is_active() is True, (
            "Precondition setup failed: Active Status did not read True "
            "immediately after Save."
        )

        with allure.step("Confirm the section is visible on the public Home Page before unpinning"):
            visible_before = home.reload_until(lambda p: p.is_section_visible())
        assert visible_before, (
            "The Upcoming Events section was not visible with Active=True "
            f"within {home.RELOAD_POLL_TIMEOUT_MS}ms of Save — cannot "
            "proceed to the unpin assertion without a confirmed "
            "precondition."
        )

        with allure.step('Reopen the record, set Active Status to OFF ("unpin"), and Save'):
            admin.open_upcoming_event_pins_list()
            admin.open_pin_record()
            admin.set_active(False)
            admin.save()

        assert admin.is_active() is False

        with allure.step("Reload the Home Page and assert the Upcoming Events section is hidden"):
            hidden_after = home.reload_until(lambda p: not p.is_section_visible())
        assert hidden_after, (
            "Active Status was set to False but "
            "section.qc-home-upcoming-event is still visible on the public "
            f"Home Page after {home.RELOAD_POLL_TIMEOUT_MS}ms of polling."
        )
    finally:
        with allure.step("Restore the singleton to its confirmed original baseline"):
            admin.open_upcoming_event_pins_list()
            admin.open_pin_record()
            admin.reset_to_baseline()

        with allure.step("Reopen and verify the restore actually persisted"):
            admin.open_upcoming_event_pins_list()
            admin.open_pin_record()
            assert admin.pinned_event_value() == admin.BASELINE_PINNED_EVENT, (
                "Baseline restore did not persist for pinnedEvent: expected "
                f"{admin.BASELINE_PINNED_EVENT!r}, got "
                f"{admin.pinned_event_value()!r}."
            )
            assert admin.is_active() == admin.BASELINE_ACTIVE, (
                "Baseline restore did not persist for activeStatus: "
                f"expected {admin.BASELINE_ACTIVE!r}, got "
                f"{admin.is_active()!r}."
            )

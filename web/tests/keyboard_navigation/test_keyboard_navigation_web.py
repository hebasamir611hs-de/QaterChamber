"""web/tests/keyboard_navigation/test_keyboard_navigation_web.py —
PBI 131054 "QC - 001 - Keyboard Navigation" (GLOBAL service), Web platform.

Source: the 36 approved, `Automation`-tagged cases of Azure Test Plan 137724 /
suite 140392. (#141801, "focus indicator in Dark theme", is tagged `Manual`
and is deliberately absent.) All 36 are Platform=Web, so all 36 live in this
single module; no Control_Panel/CMS test was written or run for this PBI, and
nothing in this batch creates, edits, publishes or deletes any CMS content.

THE ONE SANCTIONED WRITE
------------------------
ADO-141821 and ADO-141830 each submit the PUBLIC Contact Us webform once, with
the case's own identifiable data (John Tester / john.tester@example.com /
General Inquiry / "Testing keyboard-only submission"). That is a public-webform
submission, not a CMS content mutation, and it is in scope for this batch — but
each full run leaves two real inquiry records on qcdev. Stated here and in both
docstrings so it is never a surprise.

EVERY TEST RUNS LOGGED OUT
--------------------------
Each test parametrises the `page` fixture with `{"auth": False}` so the browser
context loads NO cached storageState, and every navigation goes through
`BasePage.open_anonymous()`. This is not stylistic:
  * an authenticated Liferay session renders the admin control menu above the
    page, inserting extra tab stops and changing the very tab ORDER most of
    these cases assert on;
  * ADO-141827 is literally the assertion that a public visitor is never
    interrupted by an authentication prompt;
  * standards.md's "Draft/Unpublish Public-Visibility Checks — Mandatory
    Logged-Out Context" rule.
Every expectation encoded below was measured live in a genuinely signed-out
context (`body.signed-out.public-page`), qcdev, 2026-09-23.

SIX SKIPPED CASES — CONCRETE BLOCKERS, NOT FAKED ASSERTIONS
------------------------------------------------------------
* #141807, #141817, #141818, #141831, #141836 — all five need the site
  Announcement/Alert popup open. **It cannot render on qcdev right now.** Its
  module (`/o/qc-announcement-popup/qc-announcement-popup.js`) loads on every
  page and calls `GET /o/qc-newsletter/announcement-popups`, which returns
  `{"items":[],"status":"ok"}` — no announcement is configured — so
  `#qc-announcement-popup-root` is never injected (verified absent on `/`,
  `/home`, `/web/qatar-chamber/contact-us` and `/ar/home`). Creating an
  announcement is a CMS write, excluded from this batch. The popup was NOT
  faked with a stubbed API response: with no observed schema for a populated
  payload, any injected body would make the modal under test a test artifact
  rather than the product's.
* #141805 — needs the About Us "Vision / Mission / Objective" TABBED block.
  Neither `/about-us` nor `/about-us/vision-mission-objectives` renders any
  `[role="tab"]` or `[class*="tab"]` element; VMO is a stack of
  `.qc-vmo-section` blocks. Substituting the homepage's `button.qc-os-tab`
  filter tabs would be a different control on a different page, so the case is
  skipped rather than re-pointed.

DEVIATIONS FROM THE WRITTEN CASES — RECORDED, NOT SILENTLY "FIXED"
-------------------------------------------------------------------
1. **#141806** names the mega-menu item "Legal Service"; the live "Our
   Services" panel item is **"Legal Consultation"**. Scripted against the real
   label.
2. **#141809 / #141828** describe tabbing to a "primary nav link" at 768px.
   Live, `nav.qc-nav` computes to `display: none` at 768px and ZERO top-level
   nav links are rendered — the `button.qc-hamburger` drawer IS the primary
   navigation at that breakpoint. The tests open the drawer with the keyboard
   first and then reach a primary nav link. The case's intent (a primary nav
   link receives keyboard focus with a visible indicator in the tablet layout)
   is unchanged; only the route to it differs.
3. **#141821 / #141830** do not list a Subject, but the form's own JS
   validator rejects an empty `#qc-cu-subject`. The tests fill it with the
   case's own message string so the record stays identifiable, and mirror the
   four case-named values exactly.
4. **#141825 / #141826** ("navigation order follows a logical reading
   sequence"): the assertions are (a) the tab order is exactly the document
   order of the same elements — the formal meaning of "no jumps"/"nothing
   skipped" — and (b) the header's on-screen stops progress left-to-right
   (EN) / right-to-left (AR). A raw element-by-element geometric check over
   the hero was deliberately NOT used: the hero carousel's prev/next arrows
   sit visually above the slide's buttons but are DOM-ordered after them (a
   standard carousel pattern), so a naive geometric assertion would red on a
   layout choice the case does not actually condemn. Reported as a scoping
   decision, not applied silently.
5. The first THREE tab stops on every page are off-screen screen-reader
   affordances — `a#qc-skip-link`, Liferay's own `a.sr-only-focusable` "Skip
   to Main Content", and its "Open Accessibility Menu" button (whose `id` is
   regenerated on every render — never locate it by id). Reading-order checks
   therefore run over the first N stops that are actually positioned in the
   document (`docY >= 0`); those three are correct a11y behaviour, not a
   defect.

EXPECTED RED — READ BEFORE TRIAGING
-------------------------------------
**#141835 is expected to FAIL on a live run, and that is the correct
outcome.** The footer newsletter email input (`input.qc-footer-input`, tab
stop ~161 of 166 on the homepage) has a completely suppressed focus style.
Confirmed by direct focused-vs-unfocused computed-style comparison, not just
by the walk: `outline: none 0px`, `box-shadow: none`, `border: none 0px`,
`background: rgba(0,0,0,0)` — byte-identical in both states. Every other stop
on the homepage renders `outline: solid 2px rgb(145,23,49)`. This is a real
product accessibility defect (WCAG 2.4.7 Focus Visible), so the test fails
honestly rather than being narrowed to pass. #141834's own comparison, by
contrast, was measured clean live (2026-09-28: 185 clickable elements, 229
focus stops, the ring closing on press 230, zero mouse-only).

Both whole-page audits now REFUSE to judge a truncated walk — see
`_assert_walk_completed` and `FULL_WALK_MAX_PRESSES`.

TOOLING DISCLOSURE
------------------
Every locator and behavioural fact came from the SHELL — `tools/
extract_locators.py` plus scoped Playwright probe scripts run with `python`.
The Playwright MCP was available this session and was **not used at all**.
"""

import time
import uuid

import allure
import pytest

from web.pages.keyboard_navigation.keyboard_navigation_page import (
    ABOUT_US_PATH_MARKER,
    CONTACT_US_PATH_MARKER,
    MOBILE_VIEWPORT,
    OUR_SERVICES_PATH_MARKER,
    TABLET_VIEWPORT,
    KeyboardNavigationPage,
)

PBI = "131054"

# ── Fixture params (see module docstring: every test is logged out) ───────
ANON = {"auth": False}
ANON_MOBILE = {"auth": False, "viewport": MOBILE_VIEWPORT}
ANON_TABLET = {"auth": False, "viewport": TABLET_VIEWPORT}
ANON_FIREFOX = {"auth": False, "engine": "firefox"}
ANON_EDGE = {"auth": False, "engine": "msedge"}

# ── Concrete data mirrored from the cases ─────────────────────────────────
NAV_ABOUT_US = "About us"
NAV_CONTACT_US = "Contact us"
MEGA_MENU_TRIGGER = "Our Services"
# ADO-141806 says "Legal Service"; the live panel item is "Legal Consultation".
MEGA_MENU_ITEM = "Legal Consultation"
MEGA_MENU_FIRST_ITEM = "Member's Services"

CONTACT_NAME = "John Tester"
CONTACT_EMAIL = "john.tester@example.com"
CONTACT_CATEGORY = "General Inquiry"
CONTACT_MESSAGE = "Testing keyboard-only submission"
# Not named by the case, but mandatory in the live form (deviation 3 above).
CONTACT_SUBJECT = "Testing keyboard-only submission"


def _unique_contact_identity(tc_id: str) -> tuple[str, str]:
    """A per-run unique (email, subject) pair for a Contact Us submission.

    AUTOMATION BUG FIX 2026-09-27 (ADO-141830): #141821 and #141830 both
    submitted BYTE-IDENTICAL Contact Us data in the same run, so the
    product's duplicate-submission guard — working exactly as designed —
    rejected whichever ran second and #141830 went red on a test-data
    collision, not on a product defect. The email local part and the subject
    now carry a per-run token, so no two submissions are duplicates of each
    other or of a previous run's.

    The record stays obviously identifiable as automation: the local part
    keeps `john.tester` and gains a `qaauto` marker, and the subject keeps the
    case's own wording with a `QA_AUTO` suffix. Nothing is deleted afterwards
    — teardown of a real qcdev submission is a destructive operation that is
    not in this batch's scope.
    """
    token = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    local, _, domain = CONTACT_EMAIL.partition("@")
    return (
        f"{local}.qaauto.{token.replace('-', '.')}@{domain}",
        f"{CONTACT_SUBJECT} [QA_AUTO {tc_id} {token}]",
    )

# Press budget for the two whole-page focus audits (#141834, #141835).
#
# MEASURED LIVE on qcdev, EN homepage, 1920x1080, logged out, 2026-09-28:
#   * 185 mouse-clickable elements (`clickable_element_keys()`), identical
#     before and after the walk;
#   * 229 real focus stops — the ring holds more stops than clickable
#     elements because it also visits non-clickable focusables (the three
#     screen-reader affordances, an <iframe> container that takes four
#     consecutive stops, tabindex'd containers);
#   * the ring CLOSED on press 230.
# The previous budget was 200, set against a 154-clickable / 166-stop
# homepage (2026-09-23). The page grew past it, the walk was TRUNCATED at
# press 200 — 30 elements short of the footer — and #141835 passed
# vacuously over a partial set while the footer newsletter input's missing
# focus ring (Azure bug #147180) sat just beyond the cut. 400 is ~1.7x the
# measured ring, so the same growth again is still covered, and it is still
# a bound: the walk can never run away on a page whose focusable set shifts
# underneath it. Truncation is now a hard FAILURE (see the two audits
# below), never a silent partial pass, so an out-of-date budget can only
# produce a loud red, never a false green.
FULL_WALK_MAX_PRESSES = 400
# Enough to cover the header (18 stops) plus the hero and the first content
# section for the reading-order cases.
READING_ORDER_PRESSES = 30
# Coverage floors for the document-order check. A focus stop can legitimately
# fall outside the pre-walk clickable snapshot for two measured reasons:
#   * an <iframe> container (2 of the 166 stops on a full homepage walk), and
#   * the homepage HERO CAROUSEL, which auto-rotates DURING the walk — its 5
#     slide dots and 2 slide CTAs can be recorded under a different identity
#     (active-class / href / label) than the snapshot holds. Measured live
#     across runs: 0-4 of the first 30 homepage stops, 0 on the Arabic home.
# The floors below exist so a future DOM change that pushed most stops out of
# the snapshot could not hollow the order assertion into a vacuous pass.
HERO_CHURN_COVERAGE_SLACK = 8   # homepage walks that cross the hero carousel
HEADER_ONLY_COVERAGE_FLOOR = 4  # the first 5 stops: skip links + logo + nav
# The header occupies the first 18 stops on both locales (3 off-screen
# screen-reader affordances + logo + 11 nav links + 3 utility controls).
HEADER_STOP_COUNT = 18


# ── Pure helpers over recorded focus stops (no locators, no page access) ──
def _assert_walk_completed(walk: dict, page_label: str) -> list:
    """Gate EVERY whole-page focus audit: a walk that ran out of presses
    before the focus ring closed has only seen a PREFIX of the page, so any
    "across every focusable element" assertion made over it is vacuous.

    Fails loudly with the numbers needed to act (stops recorded, budget
    used) and returns the stops only when the walk genuinely completed.

    FALSE-GREEN FIX 2026-09-28 (ADO-141835): #141835 passed while the
    product defect it exists to catch sat beyond a truncated walk. See
    `BasePage.focus_walk`'s own note and FULL_WALK_MAX_PRESSES above.
    """
    assert walk["completed"], (
        f"the {page_label} focus walk was TRUNCATED: {walk['presses']} key "
        f"presses (the whole {walk['max_presses']}-press budget) recorded "
        f"{len(_real_stops(walk['stops']))} focus stops WITHOUT the ring "
        f"closing, so only part of the page was visited. This assertion "
        f"covers every focusable element on the page and must not be judged "
        f"on a partial set — raise FULL_WALK_MAX_PRESSES above the page's "
        f"real ring size and re-measure."
    )
    return walk["stops"]


def _real_stops(stops: list) -> list:
    """Stops where something other than <body> actually holds focus."""
    return [s for s in stops if s and not s["isBody"]]


def _positioned_stops(stops: list) -> list:
    """Stops that are rendered inside the document flow — excludes the three
    off-screen screen-reader affordances (docY < 0) described in the module
    docstring."""
    return [s for s in _real_stops(stops) if s["rendered"] and s["docY"] >= 0]


def _keys(stops: list) -> list:
    return [s["key"] for s in _real_stops(stops)]


def _document_order_check(focus_keys: list, document_keys: list) -> tuple:
    """`(violations, judged)` — positions where the tab order departs from
    document order (the formal meaning of "no jumps / nothing skipped"),
    plus how many stops were actually compared.

    A focus stop absent from the document snapshot (an element that appeared
    or vanished mid-walk, or one outside the clickable selector set such as
    an `<iframe>` container) cannot be placed in document order and is
    skipped. `judged` is returned so the caller can assert a COVERAGE FLOOR:
    without it, a future DOM change that moved most stops out of the snapshot
    would hollow this check out into a vacuous pass while still reading like
    a real order assertion."""
    positions = []
    for key in focus_keys:
        if key in document_keys:
            positions.append((key, document_keys.index(key)))
    violations = []
    for (prev_key, prev_pos), (key, pos) in zip(positions, positions[1:]):
        if pos <= prev_pos:
            violations.append(f"{prev_key!r} (doc #{prev_pos}) -> {key!r} (doc #{pos})")
    return violations, len(positions)


def _horizontal_order_violations(stops: list, rtl: bool = False) -> list:
    """Stops whose horizontal position moves against the reading direction
    within the same row. Rows are compared by document Y with a tolerance,
    because a header's controls are vertically centred at slightly different
    offsets (16/20/24px live) while being visually one row."""
    violations = []
    row_tolerance = 24
    for previous, current in zip(stops, stops[1:]):
        same_row = abs(current["docY"] - previous["docY"]) <= row_tolerance
        if not same_row:
            continue
        moved_back = (
            current["docX"] > previous["docX"] if rtl else current["docX"] < previous["docX"]
        )
        if moved_back:
            violations.append(
                f"{previous['tag']}.{previous['className'][:30]} at x={previous['docX']}"
                f" -> {current['tag']}.{current['className'][:30]} at x={current['docX']}"
            )
    return violations


def _collect_desktop_keyboard_observations(kb: KeyboardNavigationPage) -> dict:
    """Shared observation collector for the three cross-browser cases
    (#141812 Chrome, #141813 Firefox, #141832 Edge). Returns raw observations
    only — every assertion stays in the individual test."""
    observations = {}

    kb.open_home()
    observations["nav_labels"] = kb.nav_link_labels()
    observations["reached_about_us_by_tab"] = kb.reach_nav_link_by_tab(NAV_ABOUT_US)
    observations["about_us_focus"] = kb.active_element()

    kb.activate_focused_element(wait_for_navigation=True, url_marker=ABOUT_US_PATH_MARKER)
    observations["url_after_enter"] = kb.current_url()
    observations["heading_after_enter"] = kb.page_heading_text()

    kb.open_home()
    kb.open_mega_menu_with_arrow(MEGA_MENU_TRIGGER)
    observations["mega_menu_expanded"] = kb.nav_link_aria(MEGA_MENU_TRIGGER)["expanded"]
    observations["mega_menu_panel_visible"] = kb.is_mega_menu_panel_visible(MEGA_MENU_TRIGGER)
    observations["mega_menu_first_focus"] = kb.active_element()
    kb.press_key("ArrowDown")
    observations["mega_menu_second_focus"] = kb.active_element()

    return observations


# ═════════════════════════════════════════════════════════════════════════
# Focus-indicator visibility (Axis 4 = UI)
# ═════════════════════════════════════════════════════════════════════════

@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A primary navigation link shows a visible focus indicator (Light theme)")
@allure.label("pbi", PBI)
@allure.label("testcase", "141800")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141800
@pytest.mark.traceability("ADO-141800")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_primary_nav_link_shows_visible_focus_indicator(page):
    """ADO-141800 | PBI 131054 — homepage, EN, Light theme: tabbing to the
    "About us" top-level nav link surrounds it with a clearly visible focus
    indicator, distinguishable from its unfocused state."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()
    unfocused_style = kb.focus_style(kb.nav_link(NAV_ABOUT_US))

    # Act
    reached = kb.reach_nav_link_by_tab(NAV_ABOUT_US)
    focused = kb.active_element()

    # Assert
    assert reached, (
        f"{NAV_ABOUT_US!r} never received focus within 20 Tab presses; "
        f"focus stopped on {focused}"
    )
    assert focused["hasVisibleFocusIndicator"], (
        f"focused {NAV_ABOUT_US!r} renders no visible focus indicator: "
        f"outline={focused['outlineStyle']} {focused['outlineWidth']} "
        f"{focused['outlineColor']}, box-shadow={focused['boxShadow']}"
    )
    focused_style = kb.focus_style(kb.nav_link(NAV_ABOUT_US))
    assert focused_style != unfocused_style, (
        "the focused nav link renders identically to its unfocused state — "
        f"{focused_style}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A page button shows a visible focus indicator")
@allure.label("pbi", PBI)
@allure.label("testcase", "141802")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141802
@pytest.mark.traceability("ADO-141802")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_contact_us_submit_button_shows_visible_focus_indicator(page):
    """ADO-141802 | PBI 131054 — Contact Us: tabbing to the inquiry form's
    Submit button (live label "Submit Inquiry") shows a visible focus
    outline. No form data is entered and nothing is submitted."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_contact_us()
    unfocused_style = kb.focus_style(kb.CONTACT_SUBMIT_BUTTON)

    # Act
    reached = kb.press_tab_until_focused(kb.CONTACT_SUBMIT_BUTTON, max_presses=60)
    focused = kb.active_element()

    # Assert
    assert reached, f"the Submit button never received focus; focus stopped on {focused}"
    assert focused["hasVisibleFocusIndicator"], (
        "the focused Submit button renders no visible focus indicator: "
        f"outline={focused['outlineStyle']} {focused['outlineWidth']}, "
        f"box-shadow={focused['boxShadow']}"
    )
    assert kb.focus_style(kb.CONTACT_SUBMIT_BUTTON) != unfocused_style, (
        "the focused Submit button renders identically to its unfocused state"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A form input shows a visible focus indicator")
@allure.label("pbi", PBI)
@allure.label("testcase", "141803")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141803
@pytest.mark.traceability("ADO-141803")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_contact_us_name_input_border_changes_on_focus(page):
    """ADO-141803 | PBI 131054 — Contact Us "Full Name" text input: on focus
    its border/outline visibly changes from the unfocused rendering."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_contact_us()
    unfocused_style = kb.focus_style(kb.CONTACT_NAME_INPUT)

    # Act
    reached = kb.press_tab_until_focused(kb.CONTACT_NAME_INPUT, max_presses=60)
    focused = kb.active_element()
    focused_style = kb.focus_style(kb.CONTACT_NAME_INPUT)

    # Assert
    assert reached, f"the Name input never received focus; focus stopped on {focused}"
    assert focused_style != unfocused_style, (
        "the Name input renders identically focused and unfocused: "
        f"{focused_style}"
    )
    assert focused["hasVisibleFocusIndicator"], (
        "the focused Name input renders neither an outline nor a box-shadow: "
        f"outline={focused['outlineStyle']} {focused['outlineWidth']}, "
        f"box-shadow={focused['boxShadow']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An accordion header shows a visible focus indicator")
@allure.label("pbi", PBI)
@allure.label("testcase", "141804")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141804
@pytest.mark.traceability("ADO-141804")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_faq_accordion_header_shows_visible_focus_indicator(page):
    """ADO-141804 | PBI 131054 — FAQ Knowledge Base: tabbing to the first
    (collapsed) accordion header shows a visible focus outline BEFORE the
    section is expanded."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_faq()
    collapsed_before = kb.accordion_expanded_state(0)

    # Act
    reached = kb.reach_first_accordion_header_by_tab()
    focused = kb.active_element()

    # Assert
    assert collapsed_before == "false", (
        f"precondition failed: the first accordion header is aria-expanded="
        f"{collapsed_before!r}, expected 'false' (collapsed) on page load"
    )
    assert reached, f"the first accordion header never received focus; focus stopped on {focused}"
    assert kb.accordion_expanded_state(0) == "false", (
        "the accordion expanded merely on receiving focus — the case requires "
        "the focus indicator to be visible while it is still collapsed"
    )
    assert focused["hasVisibleFocusIndicator"], (
        "the focused accordion header renders no visible focus indicator: "
        f"outline={focused['outlineStyle']} {focused['outlineWidth']}, "
        f"box-shadow={focused['boxShadow']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A tab control shows a visible focus indicator")
@allure.label("pbi", PBI)
@allure.label("testcase", "141805")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141805
@pytest.mark.traceability("ADO-141805")
@pytest.mark.parametrize("page", [ANON], indirect=True)
@pytest.mark.skip(
    reason="BLOCKED — the case's subject does not exist on this build. It "
    "requires the About Us page's Vision/Mission/Objective TABBED block "
    "(\"Vision\" active by default, Tab to the \"Mission\" tab control). "
    "Verified live read-only on qcdev 2026-09-23: neither "
    "/web/qatar-chamber/about-us nor "
    "/web/qatar-chamber/about-us/vision-mission-objectives renders any "
    "[role='tab'] or [class*='tab'] element — VMO is a stack of "
    ".qc-vmo-section blocks with no tab control at all. Not re-pointed at the "
    "homepage's button.qc-os-tab filter tabs, which are a different control "
    "on a different page."
)
def test_vision_mission_objectives_tab_control_shows_visible_focus_indicator(page):
    """ADO-141805 | PBI 131054 — About Us Vision/Mission/Objective tabbed
    block: tabbing to the "Mission" tab control shows a visible focus
    outline. SKIPPED — no tab control exists (see the skip reason)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_vision_mission_objectives()

    # Act
    tab_controls = kb.tab_control_count()
    reached = kb.press_tab_until_focused(kb.TAB_CONTROL, max_presses=60)
    focused = kb.active_element()

    # Assert
    assert tab_controls > 0, "the Vision/Mission/Objective block renders no tab control"
    assert reached, f"no tab control received focus; focus stopped on {focused}"
    assert focused["hasVisibleFocusIndicator"], (
        "the focused tab control renders no visible focus indicator: "
        f"outline={focused['outlineStyle']} {focused['outlineWidth']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A mega-menu item shows a visible focus indicator")
@allure.label("pbi", PBI)
@allure.label("testcase", "141806")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141806
@pytest.mark.traceability("ADO-141806")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_mega_menu_item_shows_visible_focus_indicator(page):
    """ADO-141806 | PBI 131054 — header mega-menu under "Our Services":
    opening it from the keyboard and arrowing to an item shows a visible
    focus outline on that item. The case names "Legal Service"; the live
    panel item is "Legal Consultation" (recorded deviation 1)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    kb.open_mega_menu_with_arrow(MEGA_MENU_TRIGGER)
    item_labels = kb.mega_menu_item_labels(MEGA_MENU_TRIGGER)
    reached = kb.press_tab_until_focused(
        kb.mega_menu_item(MEGA_MENU_TRIGGER, MEGA_MENU_ITEM), max_presses=20
    )
    focused = kb.active_element()

    # Assert
    assert MEGA_MENU_ITEM in item_labels, (
        f"{MEGA_MENU_ITEM!r} is not among the {MEGA_MENU_TRIGGER!r} mega-menu "
        f"items: {item_labels}"
    )
    assert kb.is_mega_menu_panel_visible(MEGA_MENU_TRIGGER), (
        f"the {MEGA_MENU_TRIGGER!r} mega-menu panel did not open from the keyboard"
    )
    assert reached, (
        f"{MEGA_MENU_ITEM!r} never received focus inside the open panel; "
        f"focus stopped on {focused}"
    )
    assert focused["hasVisibleFocusIndicator"], (
        f"the focused mega-menu item {MEGA_MENU_ITEM!r} renders no visible focus "
        f"indicator: outline={focused['outlineStyle']} {focused['outlineWidth']}, "
        f"box-shadow={focused['boxShadow']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A modal close control shows a visible focus indicator")
@allure.label("pbi", PBI)
@allure.label("testcase", "141807")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141807
@pytest.mark.traceability("ADO-141807")
@pytest.mark.parametrize("page", [ANON], indirect=True)
@pytest.mark.skip(
    reason="BLOCKED — needs the Global Announcement/Alert popup open on "
    "homepage load. No announcement is configured on qcdev: "
    "GET /o/qc-newsletter/announcement-popups returns "
    "{\"items\":[],\"status\":\"ok\"} (verified read-only 2026-09-23), so "
    "#qc-announcement-popup-root is never injected on /, /home, "
    "/web/qatar-chamber/contact-us or /ar/home. Creating an announcement is a "
    "CMS write, excluded from this Web-only batch, and the payload was NOT "
    "stubbed — no populated response schema has ever been observed."
)
def test_announcement_modal_close_control_shows_visible_focus_indicator(page):
    """ADO-141807 | PBI 131054 — the announcement popup's close ("x") control
    shows a visible focus outline when tabbed to. SKIPPED — the popup cannot
    render on qcdev (see the skip reason)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home_keeping_announcement()

    # Act
    showing = kb.is_announcement_popup_showing()
    reached = kb.reach_announcement_close_by_tab()
    focused = kb.active_element()

    # Assert
    assert showing, "the announcement popup did not appear on homepage load"
    assert reached, f"the popup's close control never received focus; focus stopped on {focused}"
    assert focused["hasVisibleFocusIndicator"], (
        "the focused close control renders no visible focus indicator: "
        f"outline={focused['outlineStyle']} {focused['outlineWidth']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The focus indicator remains visible at mobile viewport")
@allure.label("pbi", PBI)
@allure.label("testcase", "141808")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141808
@pytest.mark.traceability("ADO-141808")
@pytest.mark.parametrize("page", [ANON_MOBILE], indirect=True)
def test_focus_indicator_visible_at_mobile_viewport(page):
    """ADO-141808 | PBI 131054 — homepage at 375px: the mobile menu toggle
    receives focus with a visible outline, correctly positioned inside the
    mobile layout (i.e. rendered within the 375px-wide viewport)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    hamburger_visible = kb.is_hamburger_visible()
    reached = kb.reach_hamburger_by_tab()
    focused = kb.active_element()

    # Assert
    assert hamburger_visible, "the mobile menu toggle is not rendered at 375px"
    assert reached, f"the mobile menu toggle never received focus; focus stopped on {focused}"
    assert focused["hasVisibleFocusIndicator"], (
        "the focused mobile menu toggle renders no visible focus indicator: "
        f"outline={focused['outlineStyle']} {focused['outlineWidth']}, "
        f"box-shadow={focused['boxShadow']}"
    )
    assert 0 <= focused["x"] and focused["x"] + focused["width"] <= MOBILE_VIEWPORT[0], (
        "the focused toggle's focus ring is positioned outside the 375px "
        f"mobile layout: x={focused['x']}, width={focused['width']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The focus indicator remains visible at tablet viewport")
@allure.label("pbi", PBI)
@allure.label("testcase", "141809")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141809
@pytest.mark.traceability("ADO-141809")
@pytest.mark.parametrize("page", [ANON_TABLET], indirect=True)
def test_focus_indicator_visible_at_tablet_viewport(page):
    """ADO-141809 | PBI 131054 — homepage at 768px: a primary nav link
    receives focus with a visible, correctly-positioned outline. At 768px
    `nav.qc-nav` is display:none and the hamburger drawer IS the primary
    navigation, so the drawer is opened from the keyboard first (recorded
    deviation 2)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    hamburger_visible = kb.is_hamburger_visible()
    kb.reach_hamburger_by_tab()
    kb.open_drawer_with_enter()
    reached = kb.reach_nav_link_by_tab(NAV_ABOUT_US)
    focused = kb.active_element()

    # Assert
    assert hamburger_visible, "the drawer toggle is not rendered at 768px"
    assert reached, (
        f"the {NAV_ABOUT_US!r} primary nav link never received focus in the "
        f"tablet layout; focus stopped on {focused}"
    )
    assert focused["hasVisibleFocusIndicator"], (
        "the focused nav link renders no visible focus indicator at 768px: "
        f"outline={focused['outlineStyle']} {focused['outlineWidth']}, "
        f"box-shadow={focused['boxShadow']}"
    )
    assert 0 <= focused["x"] and focused["x"] + focused["width"] <= TABLET_VIEWPORT[0], (
        "the focused nav link's focus ring is positioned outside the 768px "
        f"tablet layout: x={focused['x']}, width={focused['width']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus-indicator visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The skip-to-content link is revealed only on keyboard focus")
@allure.label("pbi", PBI)
@allure.label("testcase", "141810")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141810
@pytest.mark.traceability("ADO-141810")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_skip_link_is_revealed_only_on_keyboard_focus(page):
    """ADO-141810 | PBI 131054 — homepage: before any key press the skip
    link is not visibly rendered (it sits above the viewport's top edge);
    after ONE Tab it is focused and visibly displayed at the top."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    offscreen_before = kb.is_skip_link_offscreen()
    kb.press_key("Tab")
    focused = kb.active_element()
    kb.wait_for_skip_link_revealed()
    top_after = kb.skip_link_viewport_top()

    # Assert
    assert offscreen_before, (
        "the skip link is already visibly rendered before any key press "
        f"(top={kb.skip_link_viewport_top()})"
    )
    assert focused["id"] == "qc-skip-link", (
        f"the first Tab focused {focused['tag']}#{focused['id']}."
        f"{focused['className'][:40]}, not the skip link"
    )
    assert top_after >= 0, (
        f"the skip link is still rendered off-screen while focused (top={top_after})"
    )
    assert focused["hasVisibleFocusIndicator"], (
        "the revealed skip link renders no visible focus indicator: "
        f"outline={focused['outlineStyle']} {focused['outlineWidth']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Semantic HTML & ARIA")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Interactive elements expose semantic HTML and ARIA")
@allure.label("pbi", PBI)
@allure.label("testcase", "141811")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.pbi_131054
@pytest.mark.tc_141811
@pytest.mark.traceability("ADO-141811")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_interactive_elements_expose_semantic_html_and_aria(page):
    """ADO-141811 | PBI 131054 — the primary nav sits inside a <nav>
    landmark with an accessible name; the mega-menu toggle exposes
    aria-expanded and aria-haspopup reflecting its open/closed state; and a
    form submit control is a native <button> with an accessible name."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    landmark_tag = kb.nav_landmark_tag()
    landmark_name = kb.nav_landmark_accessible_name()
    aria_closed = kb.nav_link_aria(MEGA_MENU_TRIGGER)
    kb.open_mega_menu_with_arrow(MEGA_MENU_TRIGGER)
    aria_open = kb.nav_link_aria(MEGA_MENU_TRIGGER)
    kb.open_contact_us()
    submit = kb.submit_button_semantics()

    # Assert
    assert landmark_tag == "nav", (
        f"the primary navigation is inside a <{landmark_tag}>, not a <nav> landmark"
    )
    assert landmark_name, "the <nav> landmark exposes no accessible name (aria-label)"
    assert aria_closed["haspopup"] == "true", (
        f"the {MEGA_MENU_TRIGGER!r} toggle exposes aria-haspopup="
        f"{aria_closed['haspopup']!r}, expected 'true'"
    )
    assert aria_closed["expanded"] == "false", (
        f"the closed {MEGA_MENU_TRIGGER!r} toggle exposes aria-expanded="
        f"{aria_closed['expanded']!r}, expected 'false'"
    )
    assert aria_open["expanded"] == "true", (
        f"the opened {MEGA_MENU_TRIGGER!r} toggle exposes aria-expanded="
        f"{aria_open['expanded']!r}, expected 'true'"
    )
    assert submit["tag"] == "button" or submit["role"] == "button", (
        f"the Contact Us submit control is a <{submit['tag']}> with role="
        f"{submit['role']!r} — expected a native <button> or role='button'"
    )
    assert submit["accessibleName"], "the submit control exposes no accessible name"


# ═════════════════════════════════════════════════════════════════════════
# Compatibility (Axis 4 = Compatibility)
# ═════════════════════════════════════════════════════════════════════════

@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Browser & viewport compatibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Keyboard navigation works consistently on Desktop Chrome")
@allure.label("pbi", PBI)
@allure.label("testcase", "141812")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.pbi_131054
@pytest.mark.tc_141812
@pytest.mark.traceability("ADO-141812")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_keyboard_navigation_on_desktop_chrome(page):
    """ADO-141812 | PBI 131054 — Chromium desktop: Tab reaches the primary
    nav, Enter activates a link and navigates, and arrow keys open a
    mega-menu and move focus between its items."""
    # Arrange
    kb = KeyboardNavigationPage(page)

    # Act
    seen = _collect_desktop_keyboard_observations(kb)

    # Assert
    assert seen["reached_about_us_by_tab"], (
        f"Tab never reached the {NAV_ABOUT_US!r} nav link on Chromium; "
        f"focus stopped on {seen['about_us_focus']}"
    )
    assert ABOUT_US_PATH_MARKER in seen["url_after_enter"], (
        f"Enter on the focused nav link did not navigate to About Us — "
        f"landed on {seen['url_after_enter']}"
    )
    assert seen["heading_after_enter"], "the About Us destination rendered no <h1> heading"
    assert seen["mega_menu_expanded"] == "true", (
        f"ArrowDown did not expand the mega-menu (aria-expanded="
        f"{seen['mega_menu_expanded']!r})"
    )
    assert seen["mega_menu_panel_visible"], "the mega-menu panel did not render"
    assert seen["mega_menu_first_focus"]["key"] != seen["mega_menu_second_focus"]["key"], (
        "a second ArrowDown did not move focus to another mega-menu item "
        f"(stayed on {seen['mega_menu_first_focus']['text']!r})"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Browser & viewport compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Keyboard navigation works consistently on Desktop Firefox")
@allure.label("pbi", PBI)
@allure.label("testcase", "141813")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.pbi_131054
@pytest.mark.tc_141813
@pytest.mark.traceability("ADO-141813")
@pytest.mark.parametrize("page", [ANON_FIREFOX], indirect=True)
def test_keyboard_navigation_on_desktop_firefox(page):
    """ADO-141813 | PBI 131054 — the SAME assertions as #141812, on a real
    Gecko engine: the `page` fixture's `{"engine": "firefox"}` param launches
    Playwright's bundled Firefox (confirmed available here, 119.0) via
    core/web/browser.py::launch_firefox_browser. Never chromium."""
    # Arrange
    kb = KeyboardNavigationPage(page)

    # Act
    seen = _collect_desktop_keyboard_observations(kb)

    # Assert
    assert seen["reached_about_us_by_tab"], (
        f"Tab never reached the {NAV_ABOUT_US!r} nav link on Firefox; "
        f"focus stopped on {seen['about_us_focus']}"
    )
    assert ABOUT_US_PATH_MARKER in seen["url_after_enter"], (
        f"Enter on the focused nav link did not navigate to About Us on Firefox — "
        f"landed on {seen['url_after_enter']}"
    )
    assert seen["heading_after_enter"], "the About Us destination rendered no <h1> heading"
    assert seen["mega_menu_expanded"] == "true", (
        f"ArrowDown did not expand the mega-menu on Firefox (aria-expanded="
        f"{seen['mega_menu_expanded']!r})"
    )
    assert seen["mega_menu_panel_visible"], "the mega-menu panel did not render on Firefox"
    assert seen["mega_menu_first_focus"]["key"] != seen["mega_menu_second_focus"]["key"], (
        "a second ArrowDown did not move focus to another mega-menu item on Firefox"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Browser & viewport compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Keyboard navigation works consistently on Desktop Edge")
@allure.label("pbi", PBI)
@allure.label("testcase", "141832")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.pbi_131054
@pytest.mark.tc_141832
@pytest.mark.traceability("ADO-141832")
@pytest.mark.parametrize("page", [ANON_EDGE], indirect=True)
def test_keyboard_navigation_on_desktop_edge(page):
    """ADO-141832 | PBI 131054 — the SAME assertions as #141812, on the
    locally installed Microsoft Edge: the `page` fixture's
    `{"engine": "msedge"}` param launches chromium with `channel="msedge"`
    (confirmed available here, 153.0.4234.48) via
    core/web/browser.py::launch_edge_browser. Never plain chromium."""
    # Arrange
    kb = KeyboardNavigationPage(page)

    # Act
    seen = _collect_desktop_keyboard_observations(kb)

    # Assert
    assert seen["reached_about_us_by_tab"], (
        f"Tab never reached the {NAV_ABOUT_US!r} nav link on Edge; "
        f"focus stopped on {seen['about_us_focus']}"
    )
    assert ABOUT_US_PATH_MARKER in seen["url_after_enter"], (
        f"Enter on the focused nav link did not navigate to About Us on Edge — "
        f"landed on {seen['url_after_enter']}"
    )
    assert seen["heading_after_enter"], "the About Us destination rendered no <h1> heading"
    assert seen["mega_menu_expanded"] == "true", (
        f"ArrowDown did not expand the mega-menu on Edge (aria-expanded="
        f"{seen['mega_menu_expanded']!r})"
    )
    assert seen["mega_menu_panel_visible"], "the mega-menu panel did not render on Edge"
    assert seen["mega_menu_first_focus"]["key"] != seen["mega_menu_second_focus"]["key"], (
        "a second ArrowDown did not move focus to another mega-menu item on Edge"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Browser & viewport compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Keyboard navigation works consistently at Tablet viewport (Chrome)")
@allure.label("pbi", PBI)
@allure.label("testcase", "141828")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.pbi_131054
@pytest.mark.tc_141828
@pytest.mark.traceability("ADO-141828")
@pytest.mark.parametrize("page", [ANON_TABLET], indirect=True)
def test_keyboard_navigation_at_tablet_viewport(page):
    """ADO-141828 | PBI 131054 — Chromium at 768px: Tab reaches the primary
    navigation and Enter activates a link. At 768px the primary navigation is
    the hamburger drawer (recorded deviation 2), so it is opened from the
    keyboard first.

    AUTOMATION BUG FIX 2026-09-27 (ADO-141828): this test used to target
    'About us', which at 768px is a PARENT drawer item (aria-haspopup="true",
    6 children). Enter on a parent correctly EXPANDS its submenu rather than
    navigating, so the wait for an /about-us URL timed out — a test-target
    defect, not a product defect. It now targets 'Contact us', a CHILDLESS
    drawer item on this build (verified live at 768x1024 by a scoped shell
    probe, 2026-09-27). The case's intent — Enter activates the focused
    drawer item — is unchanged, and the parent-item behaviour is asserted
    explicitly below so the retarget cannot hide a regression."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    reached_toggle = kb.reach_hamburger_by_tab()
    kb.open_drawer_with_enter()
    expanded = kb.hamburger_aria_expanded()
    parent_aria = kb.nav_link_aria(NAV_ABOUT_US)
    reached_link = kb.reach_nav_link_by_tab(NAV_CONTACT_US, max_presses=60)
    kb.activate_focused_element(
        wait_for_navigation=True, url_marker=CONTACT_US_PATH_MARKER
    )

    # Assert
    assert reached_toggle, "Tab never reached the drawer toggle at 768px"
    assert expanded == "true", (
        f"Enter on the drawer toggle left aria-expanded={expanded!r}, expected 'true'"
    )
    assert parent_aria.get("haspopup") == "true", (
        f"the {NAV_ABOUT_US!r} drawer item no longer declares a submenu "
        f"({parent_aria}); if it has become a plain link, this test's "
        f"retarget onto {NAV_CONTACT_US!r} should be revisited"
    )
    assert reached_link, f"Tab never reached the {NAV_CONTACT_US!r} link inside the open drawer"
    assert CONTACT_US_PATH_MARKER in kb.current_url(), (
        f"Enter on the focused nav link did not navigate to "
        f"{NAV_CONTACT_US!r} at 768px — landed on {kb.current_url()}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Browser & viewport compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Keyboard navigation works consistently at Mobile viewport (Chrome)")
@allure.label("pbi", PBI)
@allure.label("testcase", "141833")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.pbi_131054
@pytest.mark.tc_141833
@pytest.mark.traceability("ADO-141833")
@pytest.mark.parametrize("page", [ANON_MOBILE], indirect=True)
def test_keyboard_navigation_at_mobile_viewport(page):
    """ADO-141833 | PBI 131054 — Chromium at 375px: Tab reaches the mobile
    menu toggle, Enter opens the menu, and Tab then moves through the opened
    mobile menu items in logical (document) order."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    reached_toggle = kb.reach_hamburger_by_tab()
    kb.open_drawer_with_enter()
    expanded = kb.hamburger_aria_expanded()
    first_item = kb.active_element()
    stops = _real_stops(kb.tab_sequence(5))
    document_keys = kb.clickable_element_keys()

    # Assert
    assert reached_toggle, "Tab never reached the mobile menu toggle at 375px"
    assert expanded == "true", (
        f"Enter on the toggle left aria-expanded={expanded!r}, expected 'true'"
    )
    assert "qc-nav-link" in first_item["className"], (
        "opening the drawer did not move focus onto its first menu item — focus "
        f"is on {first_item['tag']}.{first_item['className'][:40]}"
    )
    assert len(stops) == 5, (
        f"only {len(stops)} of 5 Tab presses landed on a real element inside the "
        "opened mobile menu"
    )
    walked_keys = [first_item["key"]] + _keys(stops)
    assert len(set(walked_keys)) == len(walked_keys), (
        f"Tab revisited an element inside the mobile menu: {walked_keys}"
    )
    violations, judged = _document_order_check(walked_keys, document_keys)
    assert judged >= len(walked_keys) - 1, (
        f"only {judged} of {len(walked_keys)} mobile-menu stops could be placed "
        "in document order — the order check would be near-vacuous"
    )
    assert not violations, (
        f"mobile menu tab order departs from document order: {violations}"
    )


# ═════════════════════════════════════════════════════════════════════════
# Key behaviour (Axis 4 = Functional-Low)
# ═════════════════════════════════════════════════════════════════════════

@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Mega-menu keyboard behaviour")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Arrow keys expand and navigate a mega-menu's items")
@allure.label("pbi", PBI)
@allure.label("testcase", "141814")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141814
@pytest.mark.traceability("ADO-141814")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_arrow_keys_expand_and_navigate_mega_menu(page):
    """ADO-141814 | PBI 131054 — Tab to "Our Services"; Down Arrow opens the
    panel and sets aria-expanded "true"; repeated Down Arrow moves focus
    sequentially through its items."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    reached = kb.reach_nav_link_by_tab(MEGA_MENU_TRIGGER)
    aria_before = kb.nav_link_aria(MEGA_MENU_TRIGGER)
    kb.press_key("ArrowDown")
    kb.wait_for_mega_menu_expanded(MEGA_MENU_TRIGGER, expanded=True)
    aria_after = kb.nav_link_aria(MEGA_MENU_TRIGGER)
    first_item = kb.active_element()
    arrowed = _real_stops(kb.tab_sequence(3, key="ArrowDown"))
    panel_labels = kb.mega_menu_item_labels(MEGA_MENU_TRIGGER)

    # Assert
    assert reached, f"Tab never reached the {MEGA_MENU_TRIGGER!r} trigger"
    assert aria_before["expanded"] == "false", (
        f"the {MEGA_MENU_TRIGGER!r} trigger was already expanded before ArrowDown "
        f"(aria-expanded={aria_before['expanded']!r})"
    )
    assert aria_after["expanded"] == "true", (
        f"ArrowDown left aria-expanded={aria_after['expanded']!r}, expected 'true'"
    )
    assert kb.is_mega_menu_panel_visible(MEGA_MENU_TRIGGER), (
        "aria-expanded flipped to 'true' but the panel is not rendered"
    )
    assert first_item["text"] == MEGA_MENU_FIRST_ITEM, (
        f"ArrowDown focused {first_item['text']!r}, expected the panel's first "
        f"item {MEGA_MENU_FIRST_ITEM!r}"
    )
    stepped = [first_item["text"]] + [s["text"] for s in arrowed]
    assert len(set(stepped)) == len(stepped), (
        f"repeated ArrowDown did not move focus sequentially: {stepped}"
    )
    assert stepped == panel_labels[: len(stepped)], (
        f"ArrowDown visited {stepped}, expected the panel's own order "
        f"{panel_labels[: len(stepped)]}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Mega-menu keyboard behaviour")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Escape collapses an open mega-menu and returns focus to its trigger")
@allure.label("pbi", PBI)
@allure.label("testcase", "141815")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141815
@pytest.mark.traceability("ADO-141815")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_escape_collapses_open_mega_menu(page):
    """ADO-141815 | PBI 131054 — with the mega-menu open and an item
    focused, Escape collapses it (aria-expanded "false") and focus returns to
    the "Our Services" top-level trigger."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()
    kb.open_mega_menu_with_arrow(MEGA_MENU_TRIGGER)
    focused_item = kb.active_element()

    # Act
    kb.collapse_mega_menu_with_escape(MEGA_MENU_TRIGGER)
    aria_after = kb.nav_link_aria(MEGA_MENU_TRIGGER)
    focus_after = kb.active_element()

    # Assert
    assert focused_item["text"] in kb.mega_menu_item_labels(MEGA_MENU_TRIGGER), (
        f"precondition failed: focus was on {focused_item['text']!r}, not on a "
        f"{MEGA_MENU_TRIGGER!r} mega-menu item"
    )
    assert aria_after["expanded"] == "false", (
        f"Escape left aria-expanded={aria_after['expanded']!r}, expected 'false'"
    )
    assert not kb.is_mega_menu_panel_visible(MEGA_MENU_TRIGGER), (
        "Escape set aria-expanded='false' but the panel is still rendered"
    )
    assert focus_after["text"] == MEGA_MENU_TRIGGER, (
        f"after Escape focus is on {focus_after['text']!r}, expected it to return "
        f"to the {MEGA_MENU_TRIGGER!r} trigger"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Tab order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Tab moves focus forward through interactive elements in order")
@allure.label("pbi", PBI)
@allure.label("testcase", "141816")
@pytest.mark.regression
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141816
@pytest.mark.traceability("ADO-141816")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_tab_moves_focus_forward_in_order(page):
    """ADO-141816 | PBI 131054 — homepage EN, Light theme: five Tab presses
    advance focus by exactly one interactive element each, with nothing
    skipped and no element revisited, and the recorded sequence follows the
    document's own order."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()
    document_keys = kb.clickable_element_keys()

    # Act
    stops = kb.tab_sequence(5)

    # Assert
    real = _real_stops(stops)
    assert len(real) == 5, (
        f"only {len(real)} of 5 Tab presses landed on a real element; the "
        f"sequence was {[s and (s['tag'], s['className'][:25]) for s in stops]}"
    )
    keys = _keys(stops)
    assert len(set(keys)) == 5, f"Tab revisited an element within five presses: {keys}"
    violations, judged = _document_order_check(keys, document_keys)
    assert judged >= HEADER_ONLY_COVERAGE_FLOOR, (
        f"only {judged} of 5 stops could be placed in document order — the "
        "order check would be near-vacuous"
    )
    assert not violations, f"tab order departs from document order: {violations}"


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Modal focus management")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Opening a modal via keyboard traps focus inside it")
@allure.label("pbi", PBI)
@allure.label("testcase", "141817")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141817
@pytest.mark.traceability("ADO-141817")
@pytest.mark.parametrize("page", [ANON], indirect=True)
@pytest.mark.skip(
    reason="BLOCKED — needs the Announcement popup open. No announcement is "
    "configured on qcdev: GET /o/qc-newsletter/announcement-popups returns "
    "{\"items\":[],\"status\":\"ok\"} (verified read-only 2026-09-23), so "
    "#qc-announcement-popup-root is never injected on any page. Creating one "
    "is a CMS write, excluded from this Web-only batch; the API response was "
    "NOT stubbed."
)
def test_open_modal_traps_focus_inside_it(page):
    """ADO-141817 | PBI 131054 — with the announcement popup open, tabbing
    more times than it has focusable elements cycles focus only among the
    popup's own elements and never reaches the page behind it. SKIPPED — the
    popup cannot render on qcdev (see the skip reason)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home_keeping_announcement()
    showing = kb.is_announcement_popup_showing()
    focusables = kb.announcement_focusable_count()

    # Act
    records = kb.tab_recording_announcement_containment(focusables + 3)

    # Assert
    assert showing, "the announcement popup did not appear on homepage load"
    assert focusables > 0, "the announcement popup exposes no focusable element"
    escaped = [r["focus"] for r in records if not r["inside_popup"]]
    assert not escaped, (
        f"focus left the modal while it was open: "
        f"{[(s['tag'], s['className'][:30]) for s in escaped]}"
    )
    assert len({r['focus']['key'] for r in records}) <= focusables, (
        "the walk reached more distinct elements than the popup contains, so "
        "focus did not cycle only among the popup's own elements"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Modal focus management")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Closing a modal via keyboard returns focus to its trigger")
@allure.label("pbi", PBI)
@allure.label("testcase", "141818")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141818
@pytest.mark.traceability("ADO-141818")
@pytest.mark.parametrize("page", [ANON], indirect=True)
@pytest.mark.skip(
    reason="BLOCKED — needs the Announcement popup open. No announcement is "
    "configured on qcdev: GET /o/qc-newsletter/announcement-popups returns "
    "{\"items\":[],\"status\":\"ok\"} (verified read-only 2026-09-23), so "
    "#qc-announcement-popup-root is never injected on any page. Creating one "
    "is a CMS write, excluded from this Web-only batch; the API response was "
    "NOT stubbed."
)
def test_closing_modal_via_keyboard_returns_focus_to_trigger(page):
    """ADO-141818 | PBI 131054 — with the popup open, Tab to its close
    control and press Enter; the popup closes and focus returns to the
    element that originally triggered it. SKIPPED — the popup cannot render
    on qcdev (see the skip reason)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home_keeping_announcement()
    showing = kb.is_announcement_popup_showing()
    trigger_before = kb.active_element()

    # Act
    reached_close = kb.reach_announcement_close_by_tab()
    kb.press_key("Enter")
    focus_after = kb.active_element()

    # Assert
    assert showing, "the announcement popup did not appear on homepage load"
    assert reached_close, "the popup's close control never received focus"
    assert not kb.is_announcement_popup_showing(), "Enter on the close control did not close the popup"
    assert focus_after["key"] == trigger_before["key"], (
        f"focus landed on {focus_after['tag']}.{focus_after['className'][:30]} "
        "instead of returning to the element that triggered the popup"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Tab order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Shift+Tab moves focus backward in order")
@allure.label("pbi", PBI)
@allure.label("testcase", "141819")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141819
@pytest.mark.traceability("ADO-141819")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_shift_tab_moves_focus_backward_in_order(page):
    """ADO-141819 | PBI 131054 — Tab forward five times, then Shift+Tab five
    times: the backward sequence is the exact reverse of the forward order,
    ending with no element focused (focus resting on <body>)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    forward = kb.tab_sequence(5)
    backward = kb.tab_sequence(5, key="Shift+Tab")

    # Assert
    forward_keys = _keys(forward)
    assert len(forward_keys) == 5, f"the forward walk landed on {len(forward_keys)} elements, not 5"
    # Shift+Tab from stop 5 goes to stops 4, 3, 2, 1 and then off the start of
    # the document, so the first four backward stops mirror the forward order.
    backward_keys = [s["key"] for s in backward[:4]]
    assert backward_keys == list(reversed(forward_keys[:4])), (
        f"the backward order {backward_keys} is not the reverse of the forward "
        f"order {list(reversed(forward_keys[:4]))}"
    )
    assert backward[4]["isBody"], (
        "after stepping back past the first interactive element, focus should "
        f"rest on <body> (no element focused) — it is on "
        f"{backward[4]['tag']}.{backward[4]['className'][:30]}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Keyboard activation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Enter activates a focused link and navigates")
@allure.label("pbi", PBI)
@allure.label("testcase", "141820")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141820
@pytest.mark.traceability("ADO-141820")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_enter_activates_focused_link_and_navigates(page):
    """ADO-141820 | PBI 131054 — focus the "About us" nav link and press
    Enter; the browser navigates to the About Us page (URL and page heading
    both confirm the destination)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    reached = kb.reach_nav_link_by_tab(NAV_ABOUT_US)
    kb.activate_focused_element(wait_for_navigation=True, url_marker=ABOUT_US_PATH_MARKER)

    # Assert
    assert reached, f"Tab never reached the {NAV_ABOUT_US!r} nav link"
    assert ABOUT_US_PATH_MARKER in kb.current_url(), (
        f"Enter did not navigate to About Us — landed on {kb.current_url()}"
    )
    assert kb.page_heading_text(), "the About Us destination rendered no <h1> heading"


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Keyboard activation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Enter activates a focused button and triggers its action")
@allure.label("pbi", PBI)
@allure.label("testcase", "141821")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141821
@pytest.mark.traceability("ADO-141821")
@pytest.mark.xdist_group("contact_us_public_webform")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_enter_activates_focused_button_and_triggers_its_action(page):
    """ADO-141821 | PBI 131054 — Contact Us, form filled via keyboard: focus
    the Submit button and press Enter; the form submits and a confirmation
    message is displayed.

    SIDE EFFECT: this creates a REAL Contact Us inquiry record on qcdev. It
    is a public-webform submission, not a CMS content mutation, and is in
    scope for this batch. The data is the case's own identifiable test data
    (see #141830): John Tester / john.tester@example.com / General Inquiry /
    "Testing keyboard-only submission". Subject is also filled because the
    form's own validator requires it (recorded deviation 3).
    """
    # Arrange
    kb = KeyboardNavigationPage(page).open_contact_us()

    # Act
    kb.complete_contact_form_with_keyboard(
        name=CONTACT_NAME,
        email=CONTACT_EMAIL,
        category=CONTACT_CATEGORY,
        subject=CONTACT_SUBJECT,
        message=CONTACT_MESSAGE,
    )
    reached_submit = kb.reach_submit_button_by_tab()
    focused = kb.active_element()
    kb.press_key("Enter")
    kb.wait_for_contact_status_banner()
    status = kb.contact_status()

    # Assert
    assert reached_submit, (
        f"Tab never reached the Submit button; focus stopped on "
        f"{focused['tag']}.{focused['className'][:30]}"
    )
    assert kb.CONTACT_STATUS_SUCCESS_CLASS in status["classes"], (
        f"Enter on the focused Submit button did not produce a confirmation "
        f"message — the banner reads {status['text']!r} with classes "
        f"{status['classes']!r}"
    )
    assert status["text"], "the confirmation banner is displayed but carries no message text"


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Skip to content")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The skip-to-content link moves focus to the main content area")
@allure.label("pbi", PBI)
@allure.label("testcase", "141822")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141822
@pytest.mark.traceability("ADO-141822")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_skip_link_moves_focus_to_main_content(page):
    """ADO-141822 | PBI 131054 — homepage: one Tab reveals the skip link,
    Enter activates it, and focus moves into the main content region,
    bypassing the header and navigation."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    kb.press_key("Tab")
    focused_skip = kb.active_element()
    kb.wait_for_skip_link_revealed()
    kb.press_key("Enter")
    kb.wait_for_focus_inside_main_content()

    # Assert
    assert focused_skip["id"] == "qc-skip-link", (
        f"the first Tab focused {focused_skip['tag']}#{focused_skip['id']}, "
        "not the skip link"
    )
    assert kb.is_focus_inside_main_content(), (
        "activating the skip link did not move focus into the main content "
        f"region — focus is on {kb.active_element()}"
    )
    assert not kb.is_focus_inside_header(), (
        "focus is still inside the header after activating the skip link"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus state")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A generic interactive element enters a focused state via Tab")
@allure.label("pbi", PBI)
@allure.label("testcase", "141823")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141823
@pytest.mark.traceability("ADO-141823")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_footer_link_enters_focused_state_via_tab(page):
    """ADO-141823 | PBI 131054 — tabbing to a page footer link makes
    `document.activeElement` that footer link element. Run on the FAQ page
    rather than the homepage: it reaches the footer in far fewer Tab presses
    and has no auto-rotating carousel in between."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_faq()

    # Act
    reached = kb.reach_first_footer_link_by_tab()
    focused = kb.active_element()

    # Assert
    assert reached, (
        f"Tab never reached the first footer link; focus stopped on "
        f"{focused['tag']}.{focused['className'][:40]}"
    )
    assert kb.is_focused(kb.first_footer_link()), (
        "document.activeElement is not the footer link element"
    )
    assert focused["tag"] == "a", (
        f"the focused footer element is a <{focused['tag']}>, expected a link"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Focus state")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An element's focused state clears when focus moves on")
@allure.label("pbi", PBI)
@allure.label("testcase", "141824")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141824
@pytest.mark.traceability("ADO-141824")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_focused_state_clears_when_focus_moves_on(page):
    """ADO-141824 | PBI 131054 — Tab to element A (the "About us" nav link),
    then Tab again to element B; A no longer shows any focus indicator and
    renders in its default state."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()
    element_a = kb.nav_link(NAV_ABOUT_US)
    default_style = kb.focus_style(element_a)

    # Act
    reached_a = kb.reach_nav_link_by_tab(NAV_ABOUT_US)
    focused_style = kb.focus_style(element_a)
    kb.press_key("Tab")
    element_b = kb.active_element()
    # The focus ring is CSS-transitioned out, so element A still reports a
    # decaying box-shadow for a few frames after focus leaves it. Bounded
    # condition-based wait, then read — never a sleep, never a weaker check.
    settled = kb.wait_for_computed_style(element_a, default_style)
    style_after_moving_on = kb.focus_style(element_a)

    # Assert
    assert reached_a, f"Tab never reached element A ({NAV_ABOUT_US!r})"
    assert focused_style != default_style, (
        "precondition failed: element A renders identically focused and "
        "unfocused, so 'the focused state cleared' could not be observed"
    )
    assert not kb.is_focused(element_a), (
        "element A is still document.activeElement after Tab moved focus on"
    )
    assert element_b["key"], "Tab did not move focus onto a second element"
    assert settled and style_after_moving_on == default_style, (
        f"element A still renders a focus style after focus moved to element B: "
        f"{style_after_moving_on} vs default {default_style}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Tab order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Navigation order follows a logical reading sequence in English (LTR)")
@allure.label("pbi", PBI)
@allure.label("testcase", "141825")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141825
@pytest.mark.traceability("ADO-141825")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_navigation_order_follows_logical_reading_sequence_in_english(page):
    """ADO-141825 | PBI 131054 — homepage EN: the tab order through the
    header, hero and first content section follows the document's own
    sequence with no jumps, and the header's positioned stops progress
    left-to-right (see recorded deviation 4 for the exact scope)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()
    document_keys = kb.clickable_element_keys()

    # Act
    stops = kb.tab_sequence(READING_ORDER_PRESSES)

    # Assert
    assert kb.document_direction() != "rtl", (
        f"precondition failed: the English homepage reports dir="
        f"{kb.document_direction()!r}"
    )
    keys = _keys(stops)
    assert len(keys) == READING_ORDER_PRESSES, (
        f"only {len(keys)} of {READING_ORDER_PRESSES} Tab presses landed on a "
        "real element"
    )
    assert len(set(keys)) == len(keys), "the tab walk revisited an element"
    order_violations, judged = _document_order_check(keys, document_keys)
    assert judged >= len(keys) - HERO_CHURN_COVERAGE_SLACK, (
        f"only {judged} of {len(keys)} stops could be placed in document order "
        "— the order check would be near-vacuous"
    )
    assert not order_violations, (
        f"tab order jumps away from document order: {order_violations}"
    )
    header_stops = _positioned_stops(stops[:HEADER_STOP_COUNT])
    assert len(header_stops) >= 10, (
        f"only {len(header_stops)} positioned header stops were recorded — too "
        "few to judge reading order"
    )
    horizontal_violations = _horizontal_order_violations(header_stops, rtl=False)
    assert not horizontal_violations, (
        f"header tab order moves right-to-left in an LTR layout: {horizontal_violations}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Tab order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Navigation order follows a logical reading sequence in Arabic (RTL)")
@allure.label("pbi", PBI)
@allure.label("testcase", "141826")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141826
@pytest.mark.traceability("ADO-141826")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_navigation_order_follows_logical_reading_sequence_in_arabic(page):
    """ADO-141826 | PBI 131054 — homepage in Arabic (RTL): the tab order is
    the mirrored right-to-left, top-to-bottom sequence matching the RTL
    layout, with no jumps away from document order."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home(locale="ar")
    document_keys = kb.clickable_element_keys()

    # Act
    stops = kb.tab_sequence(READING_ORDER_PRESSES)

    # Assert
    assert kb.document_direction() == "rtl", (
        f"precondition failed: the Arabic homepage reports dir="
        f"{kb.document_direction()!r}, expected 'rtl'"
    )
    keys = _keys(stops)
    assert len(keys) == READING_ORDER_PRESSES, (
        f"only {len(keys)} of {READING_ORDER_PRESSES} Tab presses landed on a "
        "real element"
    )
    assert len(set(keys)) == len(keys), "the tab walk revisited an element"
    order_violations, judged = _document_order_check(keys, document_keys)
    assert judged >= len(keys) - HERO_CHURN_COVERAGE_SLACK, (
        f"only {judged} of {len(keys)} stops could be placed in document order "
        "— the order check would be near-vacuous"
    )
    assert not order_violations, (
        f"tab order jumps away from document order: {order_violations}"
    )
    header_stops = _positioned_stops(stops[:HEADER_STOP_COUNT])
    assert len(header_stops) >= 10, (
        f"only {len(header_stops)} positioned header stops were recorded — too "
        "few to judge reading order"
    )
    horizontal_violations = _horizontal_order_violations(header_stops, rtl=True)
    assert not horizontal_violations, (
        f"header tab order moves left-to-right in an RTL layout: {horizontal_violations}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Public visitor access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Public Visitor can use keyboard navigation without authentication")
@allure.label("pbi", PBI)
@allure.label("testcase", "141827")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.pbi_131054
@pytest.mark.tc_141827
@pytest.mark.traceability("ADO-141827")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_public_visitor_can_navigate_by_keyboard_without_authentication(page):
    """ADO-141827 | PBI 131054 — a fresh anonymous session with no login:
    Tab moves through the header nav, Enter activates a link, and no
    authentication prompt interrupts at any point. The context is created
    with `auth: False` (no cached storageState) and navigation uses
    `open_anonymous()`, so the session is genuinely logged out."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    signed_out_at_start = kb.is_signed_out()
    login_prompt_at_start = kb.is_login_form_present()
    reached = kb.reach_nav_link_by_tab(NAV_ABOUT_US)
    kb.activate_focused_element(wait_for_navigation=True, url_marker=ABOUT_US_PATH_MARKER)
    login_prompt_after = kb.is_login_form_present()

    # Assert
    assert signed_out_at_start, (
        "the session is not signed out — the public-visitor premise does not hold"
    )
    assert not login_prompt_at_start, "an authentication prompt was present on page load"
    assert reached, f"Tab never reached the {NAV_ABOUT_US!r} nav link as an anonymous visitor"
    assert ABOUT_US_PATH_MARKER in kb.current_url(), (
        f"Enter did not navigate to About Us — landed on {kb.current_url()}"
    )
    assert not login_prompt_after, (
        "an authentication prompt interrupted the anonymous keyboard journey"
    )
    assert kb.is_signed_out(), "the session became authenticated during the journey"


# ═════════════════════════════════════════════════════════════════════════
# End-to-end flows (Axis 4 = Functional-High)
# ═════════════════════════════════════════════════════════════════════════

@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("End-to-end keyboard journey")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A visitor can navigate the entire homepage using only the keyboard")
@allure.label("pbi", PBI)
@allure.label("testcase", "141829")
@pytest.mark.regression
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.pbi_131054
@pytest.mark.tc_141829
@pytest.mark.traceability("ADO-141829")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_visitor_can_navigate_entire_homepage_with_keyboard_only(page):
    """ADO-141829 | PBI 131054 — homepage EN, Light theme, fresh session, no
    mouse at any point: Tab through the header items, open the "Our Services"
    mega-menu with an Arrow key and select an item with Enter (which
    navigates to that service's page), Tab through body content and activate
    a link with Enter, then Shift+Tab back exactly one element."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act — header
    header_stops = _real_stops(kb.tab_sequence(6))

    # Act — mega-menu opened and an item selected, keyboard only
    kb.open_mega_menu_with_arrow(MEGA_MENU_TRIGGER)
    selected_item = kb.active_element()
    kb.activate_focused_element(wait_for_navigation=True,
                                url_marker=OUR_SERVICES_PATH_MARKER)
    service_url = kb.current_url()
    service_heading = kb.page_heading_text()

    # Act — body content: tab on, then step back exactly one element.
    # The RAW sequence is kept (not the filtered one) so "exactly one element
    # back" is indexed against the presses that actually happened.
    body_stops = kb.tab_sequence(8)
    before_step_back = kb.active_element()
    kb.press_shift_tab()
    after_step_back = kb.active_element()

    # Assert
    assert len(header_stops) == 6, (
        f"only {len(header_stops)} of 6 header Tab presses landed on a real element"
    )
    assert selected_item["text"] == MEGA_MENU_FIRST_ITEM, (
        f"the keyboard-opened mega-menu focused {selected_item['text']!r}, "
        f"expected {MEGA_MENU_FIRST_ITEM!r}"
    )
    assert OUR_SERVICES_PATH_MARKER in service_url, (
        f"Enter on the mega-menu item did not navigate into Our Services — "
        f"landed on {service_url}"
    )
    assert service_heading, "the service destination page rendered no <h1> heading"
    assert len(_real_stops(body_stops)) == 8, (
        f"only {len(_real_stops(body_stops))} of 8 Tab presses landed on a real "
        "element on the destination page"
    )
    assert after_step_back["key"] == body_stops[-2]["key"], (
        f"Shift+Tab moved focus to {after_step_back['text']!r} instead of exactly "
        f"one element back from {before_step_back['text']!r}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("End-to-end keyboard journey")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A visitor can complete and submit Contact Us entirely via keyboard")
@allure.label("pbi", PBI)
@allure.label("testcase", "141830")
@pytest.mark.regression
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.pbi_131054
@pytest.mark.tc_141830
@pytest.mark.traceability("ADO-141830")
@pytest.mark.xdist_group("contact_us_public_webform")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_visitor_can_complete_and_submit_contact_us_via_keyboard(page):
    """ADO-141830 | PBI 131054 — Contact Us, EN, keyboard only. The case's
    concrete data, mirrored exactly: Name = "John Tester", Email =
    "john.tester@example.com", Category = "General Inquiry" (selected with
    arrow keys), Message = "Testing keyboard-only submission". Tab to Submit,
    press Enter; the form submits and a confirmation message is displayed.

    SIDE EFFECT: this writes a REAL inquiry submission record on qcdev. That
    is a public-webform write, not a CMS content mutation, and is in scope —
    but each full run leaves one such record (two counting #141821).
    Subject is also filled ("Testing keyboard-only submission") because the
    form's own JS validator rejects an empty #qc-cu-subject; the case does
    not name it (recorded deviation 3).
    """
    # Arrange
    # AUTOMATION BUG FIX 2026-09-27 (ADO-141830): #141821 submits byte-
    # identical Contact Us data earlier in the same run, so the product's
    # duplicate-submission guard (working as designed) rejected this one. The
    # email local part and the subject are uniquified per run; the record
    # stays clearly identifiable as automation. See
    # _unique_contact_identity(). The xdist_group is unchanged, so this test
    # still shares a worker with #141821 and the two never submit
    # concurrently.
    contact_email, contact_subject = _unique_contact_identity("ADO-141830")
    kb = KeyboardNavigationPage(page).open_contact_us()

    # Act
    reached = kb.complete_contact_form_with_keyboard(
        name=CONTACT_NAME,
        email=contact_email,
        category=CONTACT_CATEGORY,
        subject=contact_subject,
        message=CONTACT_MESSAGE,
    )
    values = kb.contact_field_values()
    reached_submit = kb.reach_submit_button_by_tab()
    kb.press_key("Enter")
    kb.wait_for_contact_status_banner()
    status = kb.contact_status()

    # Assert
    assert all(reached[field] for field in ("name", "email", "category", "subject", "message")), (
        f"not every form field was reachable by Tab alone: {reached}"
    )
    assert values == {
        "name": CONTACT_NAME,
        "email": contact_email,
        "category": CONTACT_CATEGORY,
        "subject": contact_subject,
        "message": CONTACT_MESSAGE,
    }, f"keyboard entry did not land the case's data in the form: {values}"
    assert reached_submit, "Tab never reached the Submit button"
    assert kb.CONTACT_STATUS_SUCCESS_CLASS in status["classes"], (
        f"the keyboard-only submission did not produce a confirmation message — "
        f"the banner reads {status['text']!r} with classes {status['classes']!r}"
    )
    assert status["text"], "the confirmation banner is displayed but carries no message text"


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Modal focus management")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Keyboard navigation recovers when an unexpected modal opens mid-sequence")
@allure.label("pbi", PBI)
@allure.label("testcase", "141831")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.pbi_131054
@pytest.mark.tc_141831
@pytest.mark.traceability("ADO-141831")
@pytest.mark.parametrize("page", [ANON], indirect=True)
@pytest.mark.skip(
    reason="BLOCKED — needs the Announcement popup to open mid-sequence. No "
    "announcement is configured on qcdev: GET "
    "/o/qc-newsletter/announcement-popups returns "
    "{\"items\":[],\"status\":\"ok\"} (verified read-only 2026-09-23), so "
    "#qc-announcement-popup-root is never injected on any page. Creating one "
    "is a CMS write, excluded from this Web-only batch; the API response was "
    "NOT stubbed."
)
def test_keyboard_navigation_recovers_when_modal_opens_mid_sequence(page):
    """ADO-141831 | PBI 131054 — homepage EN: begin tabbing the header, then
    the Announcement popup opens mid-sequence; focus stays confined to the
    popup; Enter on its close control closes it, focus returns to the
    triggering element and normal Tab order resumes with nothing skipped.
    SKIPPED — the popup cannot render on qcdev (see the skip reason)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()
    before_stops = _real_stops(kb.tab_sequence(3))

    # Act — the reload is what re-triggers the popup on this site
    kb.open_home_keeping_announcement()
    showing = kb.is_announcement_popup_showing()
    trigger_before = kb.active_element()
    confined = kb.tab_recording_announcement_containment(
        kb.announcement_focusable_count() + 2
    )
    kb.reach_announcement_close_by_tab()
    kb.press_key("Enter")
    focus_after_close = kb.active_element()
    resumed = _real_stops(kb.tab_sequence(3))

    # Assert
    assert len(before_stops) == 3, "the header tab sequence did not start cleanly"
    assert showing, "the announcement popup did not open mid-sequence"
    assert all(r["inside_popup"] for r in confined), (
        "focus escaped the popup while it was open: "
        f"{[r['focus']['tag'] for r in confined if not r['inside_popup']]}"
    )
    assert not kb.is_announcement_popup_showing(), "Enter on the close control did not close the popup"
    assert focus_after_close["key"] == trigger_before["key"], (
        "focus did not return to the element that triggered the popup"
    )
    assert len(resumed) == 3 and len({s["key"] for s in resumed}) == 3, (
        f"normal Tab order did not resume cleanly after the popup closed: "
        f"{[s['text'] for s in resumed]}"
    )


# ═════════════════════════════════════════════════════════════════════════
# Negative / audit (Axis 4 = Edge)
# ═════════════════════════════════════════════════════════════════════════

@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Whole-page keyboard audit")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("No interactive element on the homepage is reachable only by mouse")
@allure.label("pbi", PBI)
@allure.label("testcase", "141834")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.pbi_131054
@pytest.mark.tc_141834
@pytest.mark.traceability("ADO-141834")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_no_homepage_element_is_reachable_only_by_mouse(page):
    """ADO-141834 | PBI 131054 — enumerate every clickable element on the
    homepage via DOM inspection, Tab through the whole page recording every
    element that receives focus, and confirm every mouse-clickable element
    also appears in the keyboard-focusable list.

    The clickable set is snapshotted BEFORE and AFTER the walk and only the
    intersection is judged: the homepage hero is an auto-rotating carousel,
    so an element that appeared or vanished mid-walk is churn, not a
    keyboard gap. Measured live 2026-09-28: 185 clickable, 229 focus stops,
    the ring closing on press 230, identical before/after snapshots, zero
    mouse-only elements.

    The walk must have COMPLETED before the comparison means anything — a
    truncated walk trivially "proves" that every element it never reached is
    mouse-only. `_assert_walk_completed` gates it.
    """
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()
    clickable_before = kb.clickable_element_keys()

    # Act
    walk = kb.focus_walk(FULL_WALK_MAX_PRESSES)
    clickable_after = kb.clickable_element_keys()

    # Assert
    stops = _assert_walk_completed(walk, "homepage")
    focusable = set(_keys(stops))
    stable_clickable = [k for k in clickable_before if k in clickable_after]
    assert stable_clickable, "no clickable element was found on the homepage at all"
    assert focusable, "the tab walk never reached a single element"
    mouse_only = [k for k in stable_clickable if k not in focusable]
    assert not mouse_only, (
        f"{len(mouse_only)} of {len(stable_clickable)} mouse-clickable elements are "
        f"never reachable by keyboard (walk recorded {len(focusable)} focus stops "
        f"in {len(stops)} presses): {mouse_only[:10]}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Whole-page keyboard audit")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The focus indicator never becomes invisible while tabbing")
@allure.label("pbi", PBI)
@allure.label("testcase", "141835")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.pbi_131054
@pytest.mark.tc_141835
@pytest.mark.traceability("ADO-141835")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_focus_indicator_never_becomes_invisible_while_tabbing(page):
    """ADO-141835 | PBI 131054 — Tab through every interactive element on the
    homepage and inspect each focused element's computed style; no element
    may have a fully suppressed focus style (outline:none with no visible
    replacement).

    `<iframe>` stops are excluded: when focus enters an embedded document the
    activeElement is the iframe CONTAINER, whose own computed outline says
    nothing about the focus ring rendered inside it.

    EXPECTED RED, see the module docstring: `input.qc-footer-input` (the
    footer newsletter email field) renders outline:none, box-shadow:none and
    an unchanged border both focused and unfocused. That is a real WCAG 2.4.7
    defect on the product (Azure bug #147180), so this test fails honestly
    rather than being narrowed to pass.

    FALSE-GREEN FIX 2026-09-28: this test PASSED on the 2026-09-27 run. It
    was not fixed and the defect was not fixed — the homepage had grown to
    185 clickable elements, the 200-press walk stopped ~30 elements short of
    the footer, and the audit was judged on a partial set that happened to
    contain no offender. The walk is now gated on completion
    (`_assert_walk_completed`) and the budget re-measured, so this can only
    fail-loud, never pass-vacuous.
    """
    # Arrange
    kb = KeyboardNavigationPage(page).open_home()

    # Act
    walk = kb.focus_walk(FULL_WALK_MAX_PRESSES)

    # Assert
    stops = _assert_walk_completed(walk, "homepage")
    inspected = [s for s in _real_stops(stops) if s["tag"] != "iframe"]
    assert len(inspected) > 50, (
        f"only {len(inspected)} focus stops were inspected — too few for a "
        "whole-page focus-visibility audit"
    )
    suppressed = [
        f"{s['tag']}.{s['className'][:40]} (outline={s['outlineStyle']} "
        f"{s['outlineWidth']}, box-shadow={s['boxShadow'][:40]})"
        for s in inspected
        if not s["hasVisibleFocusIndicator"]
    ]
    assert not suppressed, (
        f"{len(suppressed)} of {len(inspected)} focusable elements render no "
        f"visible focus indicator: {suppressed}"
    )


@allure.epic("GLOBAL")
@allure.feature("Keyboard Navigation")
@allure.story("Modal focus management")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Focus can never become trapped outside an open modal")
@allure.label("pbi", PBI)
@allure.label("testcase", "141836")
@pytest.mark.accessibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.pbi_131054
@pytest.mark.tc_141836
@pytest.mark.traceability("ADO-141836")
@pytest.mark.parametrize("page", [ANON], indirect=True)
@pytest.mark.skip(
    reason="BLOCKED — needs the Announcement popup open. No announcement is "
    "configured on qcdev: GET /o/qc-newsletter/announcement-popups returns "
    "{\"items\":[],\"status\":\"ok\"} (verified read-only 2026-09-23), so "
    "#qc-announcement-popup-root is never injected on any page. Creating one "
    "is a CMS write, excluded from this Web-only batch; the API response was "
    "NOT stubbed."
)
def test_focus_never_becomes_trapped_outside_an_open_modal(page):
    """ADO-141836 | PBI 131054 — with the announcement popup open, press Tab
    repeatedly well beyond the popup's focusable count and then Shift+Tab the
    same way; focus never lands on any element behind the popup. SKIPPED —
    the popup cannot render on qcdev (see the skip reason)."""
    # Arrange
    kb = KeyboardNavigationPage(page).open_home_keeping_announcement()
    showing = kb.is_announcement_popup_showing()
    focusables = kb.announcement_focusable_count()

    # Act
    forward_escapes = []
    for _ in range(focusables * 3):
        kb.press_key("Tab")
        if not kb.is_focus_inside_announcement():
            forward_escapes.append(kb.active_element())
    backward_escapes = []
    for _ in range(focusables * 3):
        kb.press_key("Shift+Tab")
        if not kb.is_focus_inside_announcement():
            backward_escapes.append(kb.active_element())

    # Assert
    assert showing, "the announcement popup did not appear on homepage load"
    assert focusables > 0, "the announcement popup exposes no focusable element"
    assert not forward_escapes, (
        f"Tab escaped the open modal onto the page behind it: "
        f"{[(s['tag'], s['className'][:30]) for s in forward_escapes[:5]]}"
    )
    assert not backward_escapes, (
        f"Shift+Tab escaped the open modal onto the page behind it: "
        f"{[(s['tag'], s['className'][:30]) for s in backward_escapes[:5]]}"
    )

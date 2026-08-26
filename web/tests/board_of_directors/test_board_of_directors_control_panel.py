"""
web/tests/board_of_directors/test_board_of_directors_control_panel.py —
Control_Panel-tagged cases for PBI 129398 (QC-ABOUT-006 — Board of Directors
& General Director), scoped to the PAGE-LEVEL admin surface: Liferay's Page
Design / Fragment Configuration panel (Site Builder > Page Tree > About Us >
"Board of Directors & General Manager" > Edit > click the page's fragment).
See web/pages/board_of_directors/board_of_directors_admin_page.py's module
docstring for the full live-verified field inventory this batch is built on.

⚠ NOT PARALLEL-SAFE: every test in this module edits the SAME shared Liferay
page draft (there is one fragment/widget for the whole public page). Run this
module with `-n 0` (or `--dist loadfile` restricted to this file) — the
default `-n 2` in pytest.ini would let two workers race on one draft and one
worker's Discard Draft could wipe the other's in-flight edit.

SOURCE BATCH — 15 cases were handed in for this surface (133517-133529,
133538, 133618). A live pass against the real config panel (2026-08-25,
qcdev, TEST_USER, 1920x1080) found the panel's actual field inventory does
not match 14 of the 15 case premises. Per automation-standards.md's Result
integrity rules, a case whose target field doesn't exist is DROPPED with
evidence here, not force-fitted onto an unrelated field or narrowed to pass:

  DROPPED — no Page Title (EN) / (AR) field exists anywhere in General,
  Styles, or Advanced (confirmed via full-panel text dump, not a partial
  glance):
    133517 (PT-EN accepts valid value), 133518 (PT-EN rejects empty),
    133519 (PT-EN rejects >100 chars), 133520 (PT-AR accepts valid value),
    133521 (PT-AR rejects empty), 133522 (PT-AR rejects >100 chars),
    133523 (PT EN/AR persist after reload).

  DROPPED — "Hero banner image URL (optional)" exists, but as a PLAIN
  TEXT/URL input, not a file-upload control: no file picker, no
  accept="image/*", no client/server size-limit affordance observed
  anywhere in the DOM. The field's own label states "(optional)", directly
  contradicting the mandatory-field premise of 133529. There is nothing to
  upload and nothing to reject a format/size against as these cases require:
    133524 (JPG upload), 133525 (PNG upload), 133526 (SVG upload),
    133527 (>2MB rejected), 133528 (unsupported format rejected),
    133529 (cannot save without Hero Banner).

  DROPPED — no per-section "Eyebrow Label" (EN or AR) field exists for any
  of the 4 sections (Chairman/Vice Chairmen/Board Members/General Manager);
  each section's eyebrow/heading text is hardcoded in the single page
  fragment, not exposed as a configurable field anywhere in the panel:
    133530 (Chairman Eyebrow EN valid), 133531 (Eyebrow EN rejects empty),
    133532 (Eyebrow EN rejects >100 chars), 133533 (Eyebrow AR valid),
    133538 (all 4 sections' eyebrows save/display independently).

  AUTOMATED — fits the surface exactly as confirmed live:
    133618 (no Board Members Count/Counter field anywhere in the panel —
    a pure negative-existence check the panel supports cleanly: the same
    full-panel text dump used to drop the eyebrow/title cases above is
    the direct evidence this one passes on).

Any case value entered by a test in this module is a QCTEST- prefixed
throwaway (per cms-profile.md's Test-Data Policy) and is reverted via
Discard Draft in a fixture teardown — this surface is real, shared page
content, not a disposable CMS record, so SNAPSHOT_RESTORE-style caution
applies even though nothing here mutates a persisted field.
"""

import time

import allure
import pytest

from web.pages.board_of_directors.board_of_directors_admin_page import BoardOfDirectorsAdminPage
from web.pages.board_of_directors.board_members_admin_page import BoardMembersAdminPage
from web.pages.board_of_directors.board_of_directors_page import BoardOfDirectorsPage


@pytest.fixture
def bod_admin_page(page):
    admin = BoardOfDirectorsAdminPage(page)
    admin.open_page_design_editor()
    admin.open_data_source_panel()
    yield admin
    # Safe teardown for a draft-based surface: Discard Draft undoes any
    # field edit made during the test without mutating real page content —
    # never Publish from a test in this module.
    if admin.is_discard_draft_available():
        admin.discard_draft()


@allure.label("pbi", "129398")
@allure.label("testcase", "133618")
@allure.title("Verify that the Board Members counter has no manual override field in the CMS")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133618
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.edge
def test_board_members_counter_has_no_manual_override_field(bod_admin_page):
    # QA-133618 — "14 active members" must be system-calculated only; no
    # editable Count/Counter field may exist anywhere in the page-level
    # content form (the fragment's General/DATA SOURCE panel).
    # Arrange: bod_admin_page fixture already has the config panel open on
    # its General tab (DATA SOURCE group).

    # Act: read the full rendered panel text once.
    panel_text = bod_admin_page.data_source_panel_text()

    # Assert: none of the panel's labels reference a manual count/counter
    # override — only the confirmed, unrelated fields are present.
    for forbidden in ("Count", "Counter", "Board Members Count"):
        assert forbidden not in panel_text, (
            f"unexpected manual-override field found in the page-level config "
            f"panel: {forbidden!r} — the Board Members counter must be "
            f"system-calculated only, per QA-133618"
        )
    # Positive confirmation the panel we inspected is the right, live one
    # (guards against a false green from an empty/broken panel read).
    assert bod_admin_page.has_field_labeled("Members endpoint")


# ============================================================================
# PER-MEMBER surface — Content & Data > Board Members (objectDefinitionId=
# 80051), see web/pages/board_of_directors/board_members_admin_page.py's
# module docstring for the full live-verified field inventory this batch is
# built on. This is a SEPARATE Liferay Object Definition from the
# page-fragment surface above — do not confuse the two.
#
# SCOPE OF THIS BATCH (2026-08-25): time-boxed against a live qcdev
# congestion window (2 of 3 full navigation attempts failed at login before
# succeeding on the 3rd — see the batch report). Only the fields confirmed
# live by a role-based harvest were used for assertions (Short Bio, Display
# Order) — Full Name / Position Label / Role Badge Label / Photo Alt Text /
# Active Status / Enable Share Icons remain text-anchored,
# NOT independently role-confirmed (see board_members_admin_page.py), and
# are deliberately NOT scripted this batch rather than risk a false-green
# test on an unverified locator. See the batch report for the full
# automated/dropped/deferred breakdown.
#
# Test-data approach: cms-profile.md's Test-Data Policy prefers DISPOSABLE
# QCTEST- records, but creating one requires the Full Name/Member Category
# fields above that are NOT role-confirmed this session — using them here
# would compound one unverified locator on top of another. Instead, this
# batch uses a REVERTIBLE SCOPED EDIT on an existing "Board Member"-category
# record (never Chairman/General Manager — those are confirmed SINGULAR
# featured slots on the public page per board_of_directors_page.py's
# chairman_card_locator()/gm_card_locator(), so a second record in either
# category would displace real content, not just add a test one — the
# reason 133546/133549/133629 are dropped, see the batch report). The
# fixture captures the field's original value and restores it in teardown
# BEFORE any assertion runs (yield-based finalizer, never inline
# post-assert code) — a failed assertion still reverts the real content.
@pytest.fixture
def board_member_row(page):
    admin = BoardMembersAdminPage(page)
    admin.open_board_members_list()
    # Grid-only "Board Member" category cell text, never Chairman/Vice
    # Chairman/General Manager — see docstring above for why.
    admin.click(f'{admin.LIST_ROW}:has-text("Board Member") >> nth=0 >> {admin.ROW_ID_LINK}')
    admin.wait_for(admin.SAVE_BUTTON)
    yield admin


@pytest.fixture
def short_bio_edit(page, board_member_row):
    admin = board_member_row
    original_value = admin.field_value(admin.SHORT_BIO)
    yield admin, original_value
    # Finalizer: revert to the captured original value regardless of the
    # test outcome, then Save — real editorial content is never left
    # mutated (cms-profile.md's SNAPSHOT_RESTORE caution, applied here as a
    # scoped revert since Test-Data Policy's UI-only decision rules out an
    # API-based restore).
    admin.type(admin.SHORT_BIO, original_value)
    admin.save()


@pytest.fixture
def display_order_edit(page, board_member_row):
    admin = board_member_row
    original_value = admin.field_value(admin.DISPLAY_ORDER)
    yield admin, original_value
    admin.type(admin.DISPLAY_ORDER, original_value)
    admin.save()


@allure.label("pbi", "129398")
@allure.label("testcase", "133580")
@allure.title("Verify that Short Bio (EN) accepts a valid value within the configured word/character range")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133580
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_low
def test_short_bio_en_accepts_valid_value_and_propagates(short_bio_edit, page):
    # QA-133580 — a valid Short Bio (EN) save must persist in the CMS and
    # propagate to the public Board of Directors grid card within the
    # measured ~0s / 5s-poll-budget (cms-profile.md).
    admin, original_value = short_bio_edit
    new_bio = f"QCTEST-{original_value[:40]} short bio propagation probe"

    # Act
    admin.type(admin.SHORT_BIO, new_bio)
    admin.save()

    # Assert: saved without a validation error.
    assert not admin.is_save_error_shown(), (
        f"unexpected validation error saving a valid Short Bio: {admin.save_error_text() if admin.is_save_error_shown() else ''}"
    )

    # Assert: propagates to the public listing within the 5s/0.5s poll
    # budget — client-rendered from /o/qc-board/members, so poll the DOM
    # after a real navigation/reload, never a raw HTTP fetch.
    bod = BoardOfDirectorsPage(page)
    bod.open_listing()
    deadline = time.monotonic() + 5
    seen = False
    while time.monotonic() < deadline:
        page.reload()
        if new_bio[:30] in page.locator("body").inner_text():
            seen = True
            break
        time.sleep(0.5)
    assert seen, "edited Short Bio did not propagate to the public listing within the 5s poll budget"


@allure.label("pbi", "129398")
@allure.label("testcase", "133581")
@allure.title("Verify that Short Bio (EN) rejects an empty value")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133581
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_low
def test_short_bio_en_rejects_empty_value(short_bio_edit):
    # QA-133581 — clearing Short Bio (EN) and attempting to Save must be
    # blocked with a validation error, not silently accepted.
    admin, _original_value = short_bio_edit

    # Act
    admin.type(admin.SHORT_BIO, "")
    admin.save()

    # Assert
    assert admin.is_save_error_shown(), "Short Bio (EN) empty value was accepted — expected a validation error"


@allure.label("pbi", "129398")
@allure.label("testcase", "133582")
@allure.title("Verify that Short Bio (EN) is accepted at exactly the 400-character boundary")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133582
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_low
def test_short_bio_en_accepts_400_char_boundary(short_bio_edit):
    # QA-133582 — exactly 400 characters is the documented upper boundary
    # and must be accepted, not off-by-one rejected.
    admin, _original_value = short_bio_edit
    boundary_value = ("QCTEST boundary bio " * 20)[:400]
    assert len(boundary_value) == 400

    # Act
    admin.type(admin.SHORT_BIO, boundary_value)
    admin.save()

    # Assert
    assert not admin.is_save_error_shown(), (
        f"exactly-400-character Short Bio was rejected: {admin.save_error_text() if admin.is_save_error_shown() else ''}"
    )


@allure.label("pbi", "129398")
@allure.label("testcase", "133583")
@allure.title("Verify that Short Bio (EN) rejects a value exceeding 400 characters")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133583
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.functional_low
def test_short_bio_en_rejects_over_400_chars(short_bio_edit):
    # QA-133583 — 401 characters (one past the documented boundary) must be
    # rejected with a validation error.
    admin, _original_value = short_bio_edit
    over_boundary_value = ("QCTEST over-boundary bio " * 20)[:401]
    assert len(over_boundary_value) == 401

    # Act
    admin.type(admin.SHORT_BIO, over_boundary_value)
    admin.save()

    # Assert
    assert admin.is_save_error_shown(), "401-character Short Bio was accepted — expected a validation error at >400 chars"


@allure.label("pbi", "129398")
@allure.label("testcase", "133604")
@allure.title("Verify that Display Order accepts a valid unique positive integer within its section")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133604
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.functional_low
def test_display_order_accepts_valid_positive_integer(display_order_edit):
    # QA-133604 — a valid, section-unique positive integer must save
    # cleanly. Uses a high value (999) deliberately unlikely to collide
    # with any real member's existing Display Order in the Board Members
    # grid section.
    admin, _original_value = display_order_edit

    # Act
    admin.type(admin.DISPLAY_ORDER, "999")
    admin.save()

    # Assert
    assert not admin.is_save_error_shown(), (
        f"a valid positive Display Order (999) was rejected: {admin.save_error_text() if admin.is_save_error_shown() else ''}"
    )


@allure.label("pbi", "129398")
@allure.label("testcase", "133605")
@allure.title("Verify that Display Order rejects a value of zero with the exact bilingual error message")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133605
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.functional_low
def test_display_order_rejects_zero(display_order_edit):
    # QA-133605 — Display Order = 0 must be rejected. The case also
    # requires an EXACT bilingual error message; that exact copy was not
    # captured live this session (time-boxed out — see the batch report),
    # so this test asserts the validation-blocks-save behavior only, not
    # the literal message text — narrower than the case's full premise,
    # not force-fitted to claim more than was verified.
    admin, _original_value = display_order_edit

    # Act
    admin.type(admin.DISPLAY_ORDER, "0")
    admin.save()

    # Assert
    assert admin.is_save_error_shown(), "Display Order = 0 was accepted — expected a validation error"


@allure.label("pbi", "129398")
@allure.label("testcase", "133606")
@allure.title("Verify that Display Order rejects a negative value with the exact bilingual error message")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133606
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.functional_low
def test_display_order_rejects_negative_value(display_order_edit):
    # QA-133606 — same message-text caveat as 133605 above: behavior-only
    # assertion, exact bilingual copy not captured live this session.
    admin, _original_value = display_order_edit

    # Act
    admin.type(admin.DISPLAY_ORDER, "-1")
    admin.save()

    # Assert
    assert admin.is_save_error_shown(), "a negative Display Order (-1) was accepted — expected a validation error"


@allure.label("pbi", "129398")
@allure.label("testcase", "133607")
@allure.title("Verify that Display Order rejects an empty value")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133607
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.functional_low
def test_display_order_rejects_empty_value(display_order_edit):
    # QA-133607 — clearing Display Order and attempting Save must be
    # blocked.
    admin, _original_value = display_order_edit

    # Act
    admin.type(admin.DISPLAY_ORDER, "")
    admin.save()

    # Assert
    assert admin.is_save_error_shown(), "an empty Display Order was accepted — expected a validation error"


@allure.label("pbi", "129398")
@allure.label("testcase", "133608")
@allure.title("Verify that Display Order rejects non-numeric input")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.pbi_129398
@pytest.mark.tc_133608
@pytest.mark.about
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.functional_low
def test_display_order_rejects_non_numeric_input(display_order_edit):
    # QA-133608 — a non-numeric Display Order must be blocked, not
    # silently coerced.
    admin, _original_value = display_order_edit

    # Act
    admin.type(admin.DISPLAY_ORDER, "abc")
    admin.save()

    # Assert
    assert admin.is_save_error_shown(), "non-numeric Display Order ('abc') was accepted — expected a validation error"

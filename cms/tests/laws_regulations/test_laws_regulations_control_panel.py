"""
cms/tests/laws_regulations/test_laws_regulations_control_panel.py —
Control_Panel cases for PBI 130699 "QC - Business Gateway - 006 - Laws &
Regulations" (Engineer A batch: 140087, 140088, 140089, 140090, 140095,
140105, 140106, 140108, 140153, 140154).

Object: Law Regulation (`manage-law-regulation`) — see
cms/pages/laws_regulations/laws_regulations_admin_page.py for the live field
set. Public surface: /web/qatar-chamber/laws-regulations (see
web/pages/laws_regulations/laws_regulations_page.py).

HOW THE CASES MAP ONTO THE REAL OBJECT (not re-authoring — the mapping):
  - The cases describe ONE page record with a repeatable "Law Card" section
    that is saved and then "published as a page". The live model is one Law
    Regulation ENTRY per card, each with its own lifecycle. "Add a card" =
    create an entry; "save and publish the page" = the entry's own
    role-dependent submit (Editor: "Publish"); "open the card" = open the
    entry. Every one of the eight case fields exists on the entry.
  - "Audit log" = the entry's History trail (action / actor / timestamp) —
    the per-record audit record on this surface; there is no site-wide
    audit-log screen here.
  - Seeded cards the cases assume (QCTEST-130699-LAW-A/-B, "...Commercial
    Companies Law", "...Disposable Law D", ...) do not exist on qcdev. Per
    the Destructive-Precondition rule each test creates its own disposable
    copy, titled `QCTEST-130699-<tc_id>-<case title>`, and tears it down.
  - Display Order values the cases dictate (30, 6, 5, 40) are scaled x100
    (3000, 600, 500, 4000) per the Object Authoring 100-grid convention
    (orchestrator instruction); only their relative order is asserted.

ACCOUNT PINNING: Editor = QC Site Content Editor (userId 156488), Author =
QC Site Content Author (userId 156492). Each role test signs in inside an
auth-free context and re-checks the signed-in userId before every lifecycle
assertion, because core/web/session_guard.reauthenticate() silently re-logs
a dropped session in as TEST_USER. If the pinned account cannot sign in the
test SKIPS with the exact reason — it never falls back to TEST_USER.

TEARDOWN: `disposable` tracks every CreatedEntry the test captured at
creation and deletes exactly those (id + exact title + QCTEST-130699- prefix
re-verified immediately before each click) from a TEST_USER setup-level
context — cleanup only, never an assertion. Anything it cannot remove fails
the teardown loudly.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

import allure
import pytest

from cms.pages.laws_regulations.laws_regulations_admin_page import (
    MSG_DRAFT_SAVED,
    OPEN_BEHAVIOR_NEW_TAB,
    REAL_REFERENCE_ENTRY_CODE,
    REAL_REFERENCE_TITLE,
    REAL_REFERENCE_TITLE_AR,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    LawsRegulationsAdminPage,
)
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
)
from cms.tests.laws_regulations.lawreg_support import (
    AUTH_FREE_PAGE,
    PBI,
    PUBLISH_CONFIRM_TIMEOUT,
    _assert_still_pinned,
    _chip,
    _create,
    _pinned_login,
    _public,
    _public_until,
    _register_if_created,
    _require_no_leftovers,
    _title,
    _typography_mismatches,
    _wait_row_status,
)
from core.utils.waits import WaitTimeoutError, wait_until
from web.pages.laws_regulations.laws_regulations_page import LawsRegulationsPage

# Fixtures `disposable`, `anon_pages`, `admin_reader` and the shared helpers
# above were moved (unchanged) to this folder's conftest.py / lawreg_support.py
# so the field-validation module reuses them.

pytestmark = [
    pytest.mark.control_panel,
    pytest.mark.pbi_130699,
    pytest.mark.invest,
    # Every test adds/removes cards on the SAME public grid and several assert
    # the relative order of the other cards — never run two at once.
    pytest.mark.xdist_group("laws_regulations_130699"),
]

# How far the History timestamp may sit from the moment the test saved.
HISTORY_CLOCK_TOLERANCE = timedelta(minutes=5)

RAW_KEY_OR_PLACEHOLDER = re.compile(r"\{\d*\}|\$\{|^[a-z0-9]+(-[a-z0-9]+){2,}$|\bnull\b|\bundefined\b")


def _success_banners(admin) -> list[str]:
    return [
        text for text in admin.feedback_banners()
        if not text.startswith("Editing") and "not saved" not in text
    ]


def _capture_success_banners(admin, context: str) -> list[str]:
    """Reads (never asserts) the post-save success banners, so a create can
    register its record for teardown before anything is asserted."""
    try:
        wait_until(lambda: _success_banners(admin), timeout=15.0, poll=0.5)
    except WaitTimeoutError:
        pass
    allure.attach("\n".join(admin.feedback_banners()) or "(no banner)", name=f"feedback after {context}")
    return _success_banners(admin)


def _assert_generic_success_message(admin, context: str) -> None:
    """Case wording: 'the Liferay generic success message is displayed in the
    CMS UI language (English session -> English text; no raw message key, no
    untranslated placeholder)'."""
    _check_success_messages(_capture_success_banners(admin, context), context)


def _check_success_messages(messages: list[str], context: str) -> None:
    assert messages, (
        f"no success message was shown after {context} (the save itself went through — the page "
        f"reloaded with no confirmation banner)"
    )
    for text in messages:
        assert text.isascii(), f"success message after {context} is not in the English UI language: {text!r}"
        assert not RAW_KEY_OR_PLACEHOLDER.search(text), (
            f"success message after {context} shows a raw key/placeholder: {text!r}"
        )


def _parse_history_when(when: str) -> datetime | None:
    for fmt in ("%m/%d/%Y, %I:%M:%S %p", "%m/%d/%Y, %I:%M %p"):
        try:
            return datetime.strptime(when.strip(), fmt)
        except ValueError:
            continue
    return None


def _assert_history_records(admin, entry, actor: str, action_pattern: str, saved_at: datetime) -> None:
    history = admin.history(entry)
    allure.attach(repr(history), name=f"History of {entry.title}")
    matching = [
        h for h in history
        if h["who"] == actor and re.search(action_pattern, h["action"], re.I)
    ]
    assert matching, (
        f"no History entry names {actor!r} with an action matching /{action_pattern}/ "
        f"for {entry.title!r}; History reads {history}"
    )
    stamps = [_parse_history_when(h["when"]) for h in matching]
    assert any(s and abs(s - saved_at) <= HISTORY_CLOCK_TOLERANCE for s in stamps), (
        f"History entries by {actor!r} carry timestamps {[h['when'] for h in matching]}, none "
        f"within {HISTORY_CLOCK_TOLERANCE} of the save at {saved_at:%m/%d/%Y %I:%M:%S %p}"
    )


# =============================================================================
# Functional-High
# =============================================================================
@AUTH_FREE_PAGE
@pytest.mark.tc_140087
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.functional_high
@pytest.mark.workflow
@allure.label("pbi", PBI)
@allure.label("testcase", "140087")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor adds a Law card and it appears on the public page after publish")
def test_editor_adds_law_card_visible_publicly_after_publish(page, disposable, anon_pages):
    """140087. Editor creates + publishes a card; public page renders it with
    the case's chip, after LAW-B; History records the action.
    Conflict flagged: the chip renders Law Number verbatim, so Law Number '25'
    yields '25 · 2005', not the case's 'Law No. 25 · 2005'."""
    admin = LawsRegulationsAdminPage(page)
    editor_name = _pinned_login(admin, ROLE_EDITOR)
    title = _title("140087", "Commercial Register Law")
    law_b_title = _title("140087", "LAW-B")
    _require_no_leftovers(admin, title, law_b_title)

    # Arrange — the disposable stand-in for the seeded card this one must follow.
    _create(admin, disposable, {
        "law_number": "20", "law_number_ar": "قانون رقم (20)", "year": "2004",
        "law_title": law_b_title, "law_title_ar": "QCTEST-130699-LAW-B",
        "external_url": "https://www.almeezan.qa/", "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "2000", "active_status": True,
    }, publish=True)

    # Step 1 — the Law Card list opens with the existing cards.
    admin.open_list()
    assert admin.is_list_readable(), "the Law Regulation entries list did not open with its existing cards"

    # Step 2 — all eight field values are accepted.
    admin.open_new_form()
    admin.fill_law({
        "law_number": "25", "law_number_ar": "قانون رقم (25)", "year": "2005",
        "law_title": title, "law_title_ar": "QCTEST-130699-قانون السجل التجاري رقم (25) لسنة 2005.",
        "external_url": "https://www.almeezan.qa/LawPage.aspx?id=2571&language=en",
        "open_behavior": OPEN_BEHAVIOR_NEW_TAB, "display_order": "3000", "active_status": True,
    })
    assert admin.field_errors() == [] and admin.invalid_field_count() == 0, (
        f"validation errors shown on valid input: {admin.field_errors()}"
    )

    # Step 3 — save and publish; generic English success message.
    _assert_still_pinned(admin, ROLE_EDITOR)
    saved_at = datetime.now()
    admin.submit()
    went_through = admin.save_redirected()
    diagnostics = f"{admin.field_errors()} {admin.refusal_bar_text()!r}"
    success_messages = _capture_success_banners(admin, "publishing a new Law card")
    # Register BEFORE any assertion so a failing assert never orphans the record.
    entry = _register_if_created(admin, disposable, title)
    assert went_through, f"publish refused: {diagnostics}"
    assert entry is not None, f"{title!r} went through but is not listed exactly once"
    _check_success_messages(success_messages, "publishing a new Law card")
    _assert_still_pinned(admin, ROLE_EDITOR)
    status = _wait_row_status(admin, entry, STATUS_PUBLISHED, PUBLISH_CONFIRM_TIMEOUT)
    assert status == STATUS_PUBLISHED, f"an Editor's publish left the card in {status!r}, not Published"
    admin.open_entry(entry)
    stored = admin.read_law()
    assert stored["active_status"] is True, "Active Status is not ticked on the published card"
    assert stored["law_title_ar"], "the Arabic title was not stored with the new card"

    # Step 4 — anonymous public page, exact title, chip, order after LAW-B.
    public = _public_until(anon_pages, lambda p: p.has_card(title) and p.has_card(law_b_title),
                           f"{title!r} never appeared on the public Laws & Regulations page")
    card = public.card(title)
    assert card["title"] == title
    assert card["index"] > public.card(law_b_title)["index"], (
        f"{title!r} (Display Order 3000) renders at position {card['index']}, not after "
        f"{law_b_title!r} (Display Order 2000) at {public.card(law_b_title)['index']}"
    )
    assert card["chip"] == _chip("25", "2005"), (
        f"chip reads {card['chip']!r}, case expects {_chip('25', '2005')!r} "
        f"(the renderer prints the stored Law Number verbatim — see report)"
    )
    chip_style = public.card_text_style(title, "chip")
    problems = _typography_mismatches(chip_style, "Cairo", "600", "14px", "22px", ("center",), "rgb(108, 108, 107)")
    assert not problems, f"chip typography differs from the case (Cairo 600 14px/22px CENTER #6C6C6B): {problems}"

    # Step 5 — audit record: actor, action, timestamp.
    _assert_history_records(admin, entry, editor_name, r"creat|publish|approv|submit", saved_at)


@AUTH_FREE_PAGE
@pytest.mark.tc_140088
@pytest.mark.regression
@pytest.mark.functional_high
@allure.label("pbi", PBI)
@allure.label("testcase", "140088")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Editing a Law card's title and URL updates the public page after publish")
def test_editor_edits_law_card_title_and_url(page, disposable, anon_pages):
    """140088. Law Number is not under test here, so the seed follows the live
    convention (Law Number stored as 'Law No. 11'; the chip prints it verbatim)."""
    admin = LawsRegulationsAdminPage(page)
    editor_name = _pinned_login(admin, ROLE_EDITOR)
    title = _title("140088", "Commercial Companies Law")
    new_title = _title("140088", "Commercial Companies Law (Updated)")
    new_url = "https://www.almeezan.qa/LawPage.aspx?id=3956&language=en"
    _require_no_leftovers(admin, title, new_title)

    # Arrange — the card this case edits, with the case's stored values.
    entry = _create(admin, disposable, {
        "law_number": "Law No. 11", "law_number_ar": "قانون رقم (11)", "year": "2015",
        "law_title": title, "law_title_ar": "QCTEST-130699-قانون الشركات التجارية",
        "external_url": "https://www.almeezan.qa/", "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "600", "active_status": True,
    }, publish=True)
    assert _wait_row_status(admin, entry, STATUS_PUBLISHED, PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED

    # Step 1 — the card opens with its stored values.
    admin.open_entry(entry)
    stored = admin.read_law()
    assert (stored["law_number"], stored["year"], stored["display_order"], stored["active_status"]) == (
        "Law No. 11", "2015", "600", True
    ), f"stored values differ: {stored}"

    # Step 2 — new title and URL accepted.
    admin.fill_law_title(new_title).fill_external_url(new_url)
    assert admin.field_errors() == [] and admin.invalid_field_count() == 0, admin.field_errors()

    # Step 3 — publish; success message; audit entry for the edit.
    _assert_still_pinned(admin, ROLE_EDITOR)
    entry = disposable.add_title(entry, new_title)  # known to teardown BEFORE the rename is sent
    saved_at = datetime.now()
    admin.submit()
    assert admin.save_redirected(), f"publish refused: {admin.field_errors()} {admin.refusal_bar_text()!r}"
    _assert_generic_success_message(admin, "publishing the edited Law card")
    _assert_still_pinned(admin, ROLE_EDITOR)
    assert _wait_row_status(admin, entry, STATUS_PUBLISHED, PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    _assert_history_records(admin, entry, editor_name, r"publish|approv|updat|edit|submit", saved_at)

    # Step 4 — public card: new title, chip, typography, link target.
    public = _public_until(anon_pages, lambda p: p.has_card(new_title) and not p.has_card(title),
                           f"the public card never changed to {new_title!r}")
    card = public.card(new_title)
    assert card["chip"] == _chip("11", "2015"), f"chip reads {card['chip']!r}, case expects {_chip('11', '2015')!r}"
    assert card["href"] == new_url, f"card links to {card['href']!r}, expected exactly {new_url!r}"
    followed = public.follow_card_link(new_title)
    allure.attach(repr(followed), name="external link click")
    assert followed["opened_new_tab"], "clicking the external-link icon did not open the source"
    assert followed["clicked_href"] == new_url
    assert followed["final_url"].startswith("https://www.almeezan.qa/"), followed
    title_style = public.card_text_style(new_title, "title")
    problems = _typography_mismatches(title_style, "Cairo", "600", "18px", "28px", ("left", "start"), "rgb(29, 29, 27)")
    assert not problems, f"card title typography differs from the case (Cairo 600 18px/28px LEFT #1D1D1B): {problems}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140089
@pytest.mark.regression
@pytest.mark.functional_high
@allure.label("pbi", PBI)
@allure.label("testcase", "140089")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Deleting a Law card removes it from the public page")
def test_editor_deletes_law_card_removed_publicly(page, disposable, anon_pages):
    """140089. Deletes ONLY the card this test created, found by exact title
    and captured id. Step 3's 'publish the page' has no counterpart: a delete
    is immediate and the surface shows no message after it (conflict)."""
    admin = LawsRegulationsAdminPage(page)
    _pinned_login(admin, ROLE_EDITOR)
    title = _title("140089", "Disposable Law D")
    _require_no_leftovers(admin, title)

    entry = _create(admin, disposable, {
        "law_number": "99", "law_number_ar": "قانون رقم (99)", "year": "2024",
        "law_title": title, "law_title_ar": "QCTEST-130699-قانون قابل للحذف",
        "external_url": "https://www.almeezan.qa/", "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "9900", "active_status": True,
    }, publish=True)
    assert _wait_row_status(admin, entry, STATUS_PUBLISHED, PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    before = _public_until(anon_pages, lambda p: p.has_card(title), f"{title!r} never went live")
    others_before = [t for t in before.visible_card_titles() if t != title]

    # Step 1 — found by exact title (not position); Law Number 99, Year 2024.
    admin.open_list()
    rows = admin.rows_with_exact_title(title)
    assert [r["entry_id"] for r in rows] == [entry.entry_id], f"exact-title lookup returned {rows}"
    admin.open_entry(entry)
    assert (admin.law_number(), admin.year()) == ("99", "2024")

    # Step 2 — delete + confirm; the card leaves the CMS list.
    _assert_still_pinned(admin, ROLE_EDITOR)
    deleted = admin.delete_disposable_entry(entry)
    if deleted:
        disposable.mark_removed(entry)
    assert deleted, f"{title!r} is still on the Law Regulation list after Delete"

    # Step 4 — gone from every page of the public grid; others unchanged.
    after = _public_until(anon_pages, lambda p: not p.has_card(title),
                          f"{title!r} is still rendered on the public page after deletion")
    assert not after.is_load_more_visible(), "Load More was not exhausted before checking absence"
    assert after.visible_card_titles() == others_before, (
        "the surviving cards changed after the deletion:\n"
        f"before: {others_before}\nafter:  {after.visible_card_titles()}"
    )


@AUTH_FREE_PAGE
@pytest.mark.tc_140090
@pytest.mark.regression
@pytest.mark.functional_high
@allure.label("pbi", PBI)
@allure.label("testcase", "140090")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Reordering two Law cards changes their order on the public page")
def test_editor_reorders_two_law_cards(page, disposable, anon_pages):
    """140090. Case Display Orders 5/6 scaled to 500/600."""
    admin = LawsRegulationsAdminPage(page)
    _pinned_login(admin, ROLE_EDITOR)
    labour = _title("140090", "Labour Law and its Amendments")
    companies = _title("140090", "Commercial Companies Law")
    _require_no_leftovers(admin, labour, companies)

    labour_entry = _create(admin, disposable, {
        "law_number": "14", "law_number_ar": "قانون رقم (14)", "year": "2004",
        "law_title": labour, "law_title_ar": "QCTEST-130699-قانون العمل",
        "external_url": "https://www.almeezan.qa/", "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "500", "active_status": True,
    }, publish=True)
    companies_entry = _create(admin, disposable, {
        "law_number": "11", "law_number_ar": "قانون رقم (11)", "year": "2015",
        "law_title": companies, "law_title_ar": "QCTEST-130699-قانون الشركات التجارية",
        "external_url": "https://www.almeezan.qa/", "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "600", "active_status": True,
    }, publish=True)
    for e in (labour_entry, companies_entry):
        assert _wait_row_status(admin, e, STATUS_PUBLISHED, PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    before = _public_until(anon_pages, lambda p: p.has_card(labour) and p.has_card(companies),
                           "the two cards never went live")
    others_before = [t for t in before.visible_card_titles() if t not in (labour, companies)]

    # Step 1 — both listed with Display Order 500 / 600.
    admin.open_entry(labour_entry)
    assert admin.display_order() == "500"
    admin.open_entry(companies_entry)
    assert admin.display_order() == "600"

    # Step 2 + 3 — swap the values and publish each card.
    for entry, value in ((labour_entry, "600"), (companies_entry, "500")):
        admin.open_entry(entry)
        admin.fill_display_order(value)
        assert admin.field_errors() == [] and admin.invalid_field_count() == 0, admin.field_errors()
        _assert_still_pinned(admin, ROLE_EDITOR)
        admin.submit()
        assert admin.save_redirected(), f"publish refused: {admin.field_errors()} {admin.refusal_bar_text()!r}"
        _assert_generic_success_message(admin, f"publishing {entry.title!r}")
        assert _wait_row_status(admin, entry, STATUS_PUBLISHED, PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED

    # Step 4 — Commercial Companies now renders first; everything else unchanged.
    after = _public_until(
        anon_pages,
        lambda p: p.has_card(labour) and p.has_card(companies)
        and p.card(companies)["index"] < p.card(labour)["index"],
        f"{companies!r} never rendered before {labour!r}",
    )
    assert [t for t in after.visible_card_titles() if t not in (labour, companies)] == others_before, (
        "the other cards changed position after the reorder"
    )


@AUTH_FREE_PAGE
@pytest.mark.tc_140095
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.functional_high
@allure.label("pbi", PBI)
@allure.label("testcase", "140095")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A draft Law card does not appear on the public Laws & Regulations page")
def test_draft_law_card_not_visible_publicly(page, disposable, anon_pages):
    """140095. Active Status ticked, state Draft: only the workflow gate hides it."""
    admin = LawsRegulationsAdminPage(page)
    _pinned_login(admin, ROLE_EDITOR)
    title = _title("140095", "Unpublished Law E")
    _require_no_leftovers(admin, title)
    live_before = _public(anon_pages).visible_card_titles()

    # Step 1 + 2 — create with Active Status on, save as Draft only.
    entry = _create(admin, disposable, {
        "law_number": "30", "law_number_ar": "قانون رقم (30)", "year": "2006",
        "law_title": title, "law_title_ar": "QCTEST-130699-قانون غير منشور",
        "external_url": "https://www.almeezan.qa/", "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "3000", "active_status": True,
    }, publish=False)
    _assert_still_pinned(admin, ROLE_EDITOR)
    admin.open_list()
    assert admin.row_status(entry) == STATUS_DRAFT, f"the card is {admin.row_status(entry)!r}, not Draft"
    admin.open_entry(entry)
    assert (admin.law_number(), admin.year(), admin.active_status()) == ("30", "2006", True)

    # Step 3 — only previously published cards render; not in delivered source.
    public = _public(anon_pages)
    assert not public.is_load_more_visible(), "Load More was not exhausted"
    assert not public.has_card(title), f"the Draft card {title!r} is rendered to an anonymous visitor"
    assert public.visible_card_titles() == live_before, "the published set changed after saving a draft"
    assert not public.delivered_source_contains(title), (
        f"{title!r} appears in the page source / data delivered to an anonymous visitor"
    )

    # Step 4 — search shows the empty state.
    public.search("Unpublished Law E")
    assert public.visible_card_count() == 0, f"search returned {public.visible_card_titles()}"
    assert public.is_empty_state_visible(), "no empty-state message after a no-match search"
    assert public.empty_state_text() == "No laws or regulations match your search."


# =============================================================================
# Auth
# =============================================================================
@AUTH_FREE_PAGE
@pytest.mark.tc_140105
@pytest.mark.auth
@allure.label("pbi", PBI)
@allure.label("testcase", "140105")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Author can view and update Laws & Regulations content")
def test_author_can_view_and_update_own_law_card(page, disposable):
    """140105. The Author edits a card it owns (role sheet: Authors edit OWN
    content). Conflict flagged: the case's 'hero fields' do not exist — there
    is no Laws & Regulations page object; the hero copy is static fragment text."""
    admin = LawsRegulationsAdminPage(page)
    _pinned_login(admin, ROLE_AUTHOR)
    title = _title("140105", "Labour Law and its Amendments")
    new_title = _title("140105", "Labour Law and its Amendments (Author edit)")
    _require_no_leftovers(admin, title, new_title)

    # Step 1 — the list is readable without a permission error.
    admin.open_list()
    assert admin.is_list_readable(), "the Author could not read the Law Regulation list"

    entry = _create(admin, disposable, {
        "law_number": "14", "law_number_ar": "قانون رقم (14)", "year": "2004",
        "law_title": title, "law_title_ar": "QCTEST-130699-قانون العمل",
        "external_url": "https://www.almeezan.qa/", "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "1400", "active_status": True,
    }, publish=False)
    # Step 2 — the title field accepts the new value.
    admin.open_entry(entry)
    admin.fill_law_title(new_title)
    assert admin.law_title() == new_title

    # Step 3 — save, reopen, new title + Last Modified at the save time.
    _assert_still_pinned(admin, ROLE_AUTHOR)
    entry = disposable.add_title(entry, new_title)  # known to teardown BEFORE the rename is sent
    saved_at = datetime.now()
    admin.save_draft()
    _assert_still_pinned(admin, ROLE_AUTHOR)
    assert admin.save_redirected(), f"save refused: {admin.field_errors()} {admin.refusal_bar_text()!r}"
    assert admin.wait_for_feedback(MSG_DRAFT_SAVED), f"no success message; banners {admin.feedback_banners()}"
    _assert_generic_success_message(admin, "the Author's save")
    admin.open_entry(entry)
    assert admin.law_title() == new_title
    admin.open_list()
    modified_after = admin.row_modified(entry)
    stamp = _parse_history_when(modified_after)
    assert stamp and abs(stamp - saved_at) <= HISTORY_CLOCK_TOLERANCE, (
        f"Last Modified {modified_after!r} does not match the save time {saved_at:%m/%d/%Y %I:%M:%S %p}"
    )


@AUTH_FREE_PAGE
@pytest.mark.tc_140106
@pytest.mark.auth
@allure.label("pbi", PBI)
@allure.label("testcase", "140106")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Author cannot publish Laws & Regulations content directly")
def test_author_cannot_publish_law_card(page, disposable, anon_pages):
    """140106. The 'direct URL' attempt is not made: the only publish
    endpoints are REST calls, and this project's CMS automation makes no API
    calls (cms-profile). The UI attempt is the Author's own submit control."""
    admin = LawsRegulationsAdminPage(page)
    _pinned_login(admin, ROLE_AUTHOR)
    title = _title("140106", "Author Publish Attempt")
    _require_no_leftovers(admin, title)
    entry = _create(admin, disposable, {
        "law_number": "15", "law_number_ar": "قانون رقم (15)", "year": "2010",
        "law_title": title, "law_title_ar": "QCTEST-130699-محاولة نشر",
        "external_url": "https://www.almeezan.qa/", "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "1500", "active_status": True,
    }, publish=False)

    # Step 1 + 2 — editable; Save as Draft yes, Publish / Unpublish no.
    admin.open_entry(entry)
    actions = admin.form_action_labels()
    allure.attach(repr(actions), name="Author form actions")
    assert admin.is_save_as_draft_enabled(), "Save as Draft is not available to the Author"
    assert "Publish" not in actions, f"a Publish action is offered to the Author: {actions}"
    assert not any(a.startswith("Unpublish") for a in actions), f"an Unpublish action is offered: {actions}"
    admin.open_list()
    row_actions = admin.row_actions(entry)
    assert not {"publish", "approve", "unpublish"} & set(row_actions), (
        f"the Author's row offers workflow actions {row_actions}"
    )

    # Step 3 — the attempt is refused: not Published, not public.
    admin.open_entry(entry)
    _assert_still_pinned(admin, ROLE_AUTHOR)
    admin.submit()
    assert admin.save_redirected(), f"submit refused: {admin.field_errors()} {admin.refusal_bar_text()!r}"
    _assert_still_pinned(admin, ROLE_AUTHOR)
    admin.open_list()
    status = admin.row_status(entry)
    assert status != STATUS_PUBLISHED, "the Author's submit published the card directly"
    assert status == STATUS_PENDING_REVIEW, f"the Author's submit left the card in {status!r}"
    assert not _public(anon_pages).has_card(title), "the Author's card is visible to anonymous visitors"


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@pytest.mark.tc_140108
@pytest.mark.auth
@allure.label("pbi", PBI)
@allure.label("testcase", "140108")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An anonymous visitor cannot reach the CMS authoring view of Laws & Regulations")
def test_anonymous_visitor_cannot_reach_authoring_view(page, anon_pages, admin_reader):
    """140108. Read-only against a REAL record: the anonymous requests are GETs
    that must be refused; Last modified is read (never changed) through a
    TEST_USER reader. The POST publish endpoint is not called (no API calls)."""
    admin_reader.open_list()
    real_rows = admin_reader.rows_with_exact_title(REAL_REFERENCE_TITLE)
    assert len(real_rows) == 1, f"reference record {REAL_REFERENCE_TITLE!r} not uniquely listed: {real_rows}"
    modified_before = real_rows[0]["modified"]

    anon = LawsRegulationsAdminPage(page)
    # Step 1 — no authenticated session (read on a public page of this context).
    LawsRegulationsPage(page).open_page()
    assert anon.signed_in_user() == ("", ""), "the fresh browser session is already signed in"

    # Stored CMS content an anonymous response must never carry. The entry code
    # is only forbidden where the visitor did NOT put it in the URL: Liferay
    # echoes the requested URL (currentURL, the AR language-switch redirect)
    # into every page, including its 404 — observed live 2026-09-29.
    content_markers = (
        REAL_REFERENCE_TITLE_AR, "Law Regulation entries", "Law Number — العربية", "Save as Draft",
    )
    # Step 2 — the authoring view is refused; no field values leak.
    for label, url, forbidden_markers in (
        ("authoring view", anon.manage_url(), content_markers + (REAL_REFERENCE_ENTRY_CODE,)),
        ("edit action URL", anon.manage_url(edit_entry=REAL_REFERENCE_ENTRY_CODE), content_markers),
    ):
        result = anon.anonymous_probe(url)
        allure.attach(f"status={result['status']} final_url={result['final_url']}\n\n{result['body_text'][:3000]}",
                      name=f"anonymous {label}")
        assert not result["signed_in"], f"requesting the {label} signed the visitor in"
        assert not result["authoring_form_present"], f"the {label} rendered the authoring form anonymously"
        assert not result["entries_table_present"], f"the {label} rendered the entries list anonymously"
        assert result["status"] in (401, 403, 404) or result["login_form_shown"], (
            f"the {label} answered {result['status']} at {result['final_url']} — neither a "
            f"permission-denied response nor the sign-in page"
        )
        leaked = [m for m in forbidden_markers if m in result["html"]]
        assert not leaked, f"the anonymous {label} response exposes CMS content: {leaked}"

    # Step 3 — published content and its Last Modified are unchanged.
    public = LawsRegulationsPage(anon_pages()).open_page()
    public.load_all()
    card = public.card(REAL_REFERENCE_TITLE)
    assert card is not None, f"the published card {REAL_REFERENCE_TITLE!r} is gone from the public page"
    assert card["chip"] == "Law No. 11 · 2015", f"the published card changed: {card}"
    admin_reader.open_list()
    assert admin_reader.rows_with_exact_title(REAL_REFERENCE_TITLE)[0]["modified"] == modified_before, (
        "the reference record's Last Modified changed during the anonymous attempts"
    )


# =============================================================================
# Edge
# =============================================================================
@AUTH_FREE_PAGE
@pytest.mark.tc_140153
@pytest.mark.edge
@pytest.mark.bilingual
@allure.label("pbi", PBI)
@allure.label("testcase", "140153")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Law card missing its Arabic title falls back to English on the Arabic page")
def test_english_only_law_card_falls_back_on_arabic_page(page, disposable, anon_pages):
    """140153. Conflicts flagged: 'Law Title — العربية' is REQUIRED on the live
    form, and the list script copies a new record's missing Arabic from
    English — both contradict 'no Arabic title stored'. Step 1 surfaces that."""
    admin = LawsRegulationsAdminPage(page)
    _pinned_login(admin, ROLE_EDITOR)
    title = _title("140153", "English Only Law G")
    _require_no_leftovers(admin, title)

    # Step 1 — stored and published with only the English title.
    admin.open_new_form()
    admin.fill_law({
        "law_number": "40", "law_number_ar": "قانون رقم (40)", "year": "2002",
        "law_title": title, "external_url": "https://www.almeezan.qa/",
        "open_behavior": OPEN_BEHAVIOR_NEW_TAB, "display_order": "4000", "active_status": True,
    })
    if admin.is_field_required(admin.LAW_TITLE_LABEL + admin.ARABIC_SUFFIX):
        pytest.skip(
            "PRECONDITION unreachable: Arabic Law Title is required on the live form and is "
            "back-filled from English — case conflict, raised to QA Manager"
        )
    _assert_still_pinned(admin, ROLE_EDITOR)
    admin.submit()
    went_through = admin.save_redirected()
    diagnostics = (
        f"'Law Title — العربية' says {admin.native_validation_message('Law Title' + admin.ARABIC_SUFFIX)!r}; "
        f"field errors {admin.field_errors()}"
    )
    # Register whatever got created BEFORE asserting.
    entry = _register_if_created(admin, disposable, title)
    assert went_through, f"the CMS refused to store the card without an Arabic title — {diagnostics}"
    assert entry is not None, f"{title!r} went through but is not listed exactly once"
    assert _wait_row_status(admin, entry, STATUS_PUBLISHED, PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    admin.open_entry(entry)
    assert admin.law_title_ar() == "", (
        f"an Arabic title was stored anyway: {admin.law_title_ar()!r} (the surface back-fills it)"
    )

    # Step 2 — English grid: exact title and chip.
    english = _public_until(anon_pages, lambda p: p.has_card(title), f"{title!r} never went live")
    assert english.card(title)["chip"] == _chip("40", "2002"), english.card(title)

    # Step 3 — Arabic page: still rendered, English fallback, Arabic chrome.
    arabic = _public_until(anon_pages, lambda p: p.has_card(title),
                           f"{title!r} is missing from the Arabic page", locale="ar")
    assert arabic.card(title)["title"] == title
    assert arabic.layout_dir() == "rtl"
    assert arabic.hero_title_text() == "القوانين واللوائح"
    assert arabic.search_placeholder() == "بحث.."
    assert arabic.blank_or_raw_card_texts() == [], arabic.blank_or_raw_card_texts()


@AUTH_FREE_PAGE
@pytest.mark.tc_140154
@pytest.mark.edge
@pytest.mark.redirect
@allure.label("pbi", PBI)
@allure.label("testcase", "140154")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A Law card with a broken link stays visible while its destination returns 404")
def test_broken_link_law_card_stays_visible(page, disposable, anon_pages):
    admin = LawsRegulationsAdminPage(page)
    _pinned_login(admin, ROLE_EDITOR)
    title = _title("140154", "Broken Link Law H")
    broken_url = "https://www.almeezan.qa/QCTEST-130699-broken-link"
    _require_no_leftovers(admin, title)
    entry = _create(admin, disposable, {
        "law_number": "77", "law_number_ar": "قانون رقم (77)", "year": "2020",
        "law_title": title, "law_title_ar": "QCTEST-130699-رابط معطل",
        "external_url": "https://www.almeezan.qa/", "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "7700", "active_status": True,
    }, publish=True)
    assert _wait_row_status(admin, entry, STATUS_PUBLISHED, PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED

    # Step 1 — the broken URL is accepted and stored; resolution not required.
    admin.open_entry(entry)
    admin.fill_external_url(broken_url)
    assert admin.field_errors() == [] and admin.invalid_field_count() == 0, admin.field_errors()
    _assert_still_pinned(admin, ROLE_EDITOR)
    admin.submit()
    assert admin.save_redirected(), f"publish refused: {admin.field_errors()} {admin.refusal_bar_text()!r}"
    assert _wait_row_status(admin, entry, STATUS_PUBLISHED, PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    admin.open_entry(entry)
    assert admin.external_url() == broken_url

    # Step 2 — still rendered normally, no error banner.
    public = _public_until(anon_pages, lambda p: (p.card(title) or {}).get("href") == broken_url,
                           f"{title!r} never went live with the broken URL")
    card = public.card(title)
    assert card["visible"] and card["chip"] and card["title"] == title, card
    classes = card["classes"].split()
    flagged = [c for c in classes if re.search(r"disabled|error|broken|invalid|inactive", c, re.I)]
    assert "qc-lawreg-card" in classes and not flagged and card["opacity"] == "1", (
        f"the card is styled differently (greyed/flagged): {card}"
    )
    assert public.status_text() == "", f"the grid shows a status/error banner: {public.status_text()!r}"

    # Step 3 — destination 404s; the page stays fully functional.
    cards_before_click = public.visible_card_count()
    errors_before = len(public.console_errors)
    followed = public.follow_card_link(title)
    allure.attach(repr(followed), name="broken link click")
    assert followed["opened_new_tab"] and followed["clicked_href"] == broken_url, followed
    assert followed["status"] == 404, (
        f"the destination answered {followed['status']} at {followed['final_url']}, not the host's 404"
    )
    assert public.hero_title_text() == "Laws & Regulations", "the Laws & Regulations page lost its content"
    public.search("Broken Link Law H")
    assert public.visible_card_titles() == [title], f"search broke: {public.visible_card_titles()}"
    public.search("")
    assert not public.is_empty_state_visible(), "clearing the search left the empty state up"
    public.load_all()
    assert public.visible_card_count() == cards_before_click, (
        f"the grid no longer reaches every card via Load More: {public.visible_card_count()} "
        f"of {cards_before_click}"
    )
    assert public.new_console_errors(errors_before) == [], public.new_console_errors(errors_before)

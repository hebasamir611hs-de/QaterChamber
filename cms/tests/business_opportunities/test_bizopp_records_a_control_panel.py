"""
cms/tests/business_opportunities/test_bizopp_records_a_control_panel.py —
P2 record lifecycle / date / persistence cases for PBI 130697 (Business
Opportunities), Azure suite 140361, on `manage-business-opportunity` (Agent A).

Accounts: Site Content Editor (156488); 143387 (Administrator-worded, no
duplicate) runs as TEST_USER = Administrator (user decision 2026-10-07). The
Administrator-worded members of duplicate groups (143384, 143386, 143388) share
their group's single Editor script (brief rule 12).

Duplicate groups (one script, every tc marker, same outcome):
  {143204, 143240, 143388} Archive Date equal to / before Publish Date rejected
  {143222, 143384} Save Draft
  {143231, 143385} Draft not on the public listing
  {143223, 143386} Publish -> visible on the public Active tab

Substitutions disclosed:
  - 143387 "Sort Order = 5": the form has no "Sort Order"; its ordering field is
    "Display Order" on the 100-grid (brief rule 3) -> run with 500.
  - Dates are entered dd/mm/yyyy (the form's own date box) — the case's
    yyyy-mm-dd values are the same dates.
  - 143389 (auto-archive on the Archive Date): Publish/Archive Date are DATE
    fields (day granularity, no time) — brief rule 14 -> Blocked.
"""

from __future__ import annotations

from datetime import date, timedelta

import allure
import pytest

from cms.pages.business_opportunities.opportunity_admin_page import (
    K_ARCHIVE_DATE,
    K_DISPLAY_ORDER,
    K_PUBLISH_DATE,
    K_TITLE,
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    ROLE_EDITOR,
    BizOppPublicView,
    OpportunityAdminPage,
)
from cms.tests.business_opportunities.a_support import (  # noqa: F401 — fixtures
    ROLE_ADMINISTRATOR,
    login_any,
    A_GROUP,
    AUTH_FREE_PAGE,
    EPIC,
    a_name,
    anon_pages,
    assert_not_public,
    create_opportunity,
    disposable,
    has,
    history,
    login,
    pinned,
    public_until,
    require_active_status,
    today_ddmmyyyy,
)

FEATURE = "Business Opportunities — Control Panel (records)"


def _markers(*tcs, category="functional_low", regression=False):
    def deco(fn):
        marks = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130697, A_GROUP,
                 getattr(pytest.mark, category)]
        if regression:
            marks.append(pytest.mark.regression)
        for m in marks:
            fn = m(fn)
        for tc in tcs:
            fn = getattr(pytest.mark, f"tc_{tc}")(fn)
        return fn
    return deco


def _attempt_save(admin: OpportunityAdminPage, disposable, data: dict, draft: bool = True) -> dict:
    """Create-form save that may be REFUSED: fills `data`, clicks Save as Draft
    (or Publish), registers anything that got created for teardown, and
    returns the outcome evidence (never asserts)."""
    ids_before = admin.snapshot_ids()
    admin.open_create_form_en()
    admin.fill_opportunity(data)
    pinned(admin, ROLE_EDITOR)
    admin.click_save_as_draft() if draft else admin.click_publish()
    outcome = admin.save_outcome()
    outcome["messages"] = admin.all_messages_text()
    outcome["editbar"] = admin.editbar_texts()
    admin.evidence(f"{data[K_TITLE]} {'draft' if draft else 'publish'} attempt")
    entry = None
    try:
        entry = admin.identify_created_entry(data[K_TITLE], ids_before)
        if entry:
            disposable.track(entry)
    except Exception as exc:  # noqa: BLE001
        allure.attach(repr(exc), name="registration failed")
    outcome["created"] = entry
    allure.attach(repr(outcome), name=f"save attempt {data[K_TITLE]}")
    return outcome


# ===========================================================================
# 143202 — Archive Date after Publish Date accepted
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dates")
@allure.title("An Archive Date set after the Publish Date is accepted")
@_markers("143202")
def test_archive_date_after_publish_date_accepted(page, disposable):
    # Azure TC 143202 | Site Content Editor | Publish = today, Archive = today + 90.
    editor = login(page, ROLE_EDITOR)
    publish, archive = today_ddmmyyyy(0), today_ddmmyyyy(90)
    data = OpportunityAdminPage.default_data(a_name("143202", "dates accepted"), active_status=False,
                                             **{K_PUBLISH_DATE: publish, K_ARCHIVE_DATE: archive})
    entry = create_opportunity(editor, disposable, data, publish=False)
    assert has(editor.create_banners, MSG_DRAFT_SAVED), f"no {MSG_DRAFT_SAVED!r}: {editor.create_banners}"
    editor.open_entry_en(entry.code)
    stored = (editor.date_text(K_PUBLISH_DATE), editor.date_text(K_ARCHIVE_DATE))
    allure.attach(repr(stored), name="stored dates")
    assert stored == (publish, archive), f"stored dates {stored} != entered {(publish, archive)}"


# ===========================================================================
# 143204 / 143240 / 143388 — Archive Date equal to / before Publish Date rejected
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dates")
@allure.title("An Archive Date equal to or before the Publish Date is rejected at save")
@_markers("143204", "143240", "143388", category="edge")
@pytest.mark.functional_low
def test_archive_date_not_after_publish_date_rejected(page, disposable):
    # Azure TCs 143204 / 143240 / 143388 (duplicates) | Site Content Editor.
    # Equal (today / today) and before (today / today-5); both via Save as Draft
    # (the case's "Save") and, if a draft slips through, via Publish too.
    editor = login(page, ROLE_EDITOR)
    today = today_ddmmyyyy(0)
    results = {}
    for label, archive in (("equal", today), ("before", today_ddmmyyyy(-5))):
        data = OpportunityAdminPage.default_data(a_name("143204", f"archive {label}"), active_status=False,
                                                 **{K_PUBLISH_DATE: today, K_ARCHIVE_DATE: archive})
        draft = _attempt_save(editor, disposable, data, draft=True)
        results[f"{label} / Save as Draft"] = draft
        if draft["went_through"] or draft["created"]:
            publish_data = dict(data, **{K_TITLE: a_name("143204", f"archive {label} publish")})
            results[f"{label} / Publish"] = _attempt_save(editor, disposable, publish_data, draft=False)
    summary = {k: {"saved": bool(v["went_through"] or v["created"]), "messages": v["messages"]}
               for k, v in results.items()}
    allure.attach("\n".join(f"{k}: {v}" for k, v in summary.items()), name="archive-date rule outcomes")
    accepted = {k: v for k, v in summary.items() if v["saved"]}
    assert not accepted, (
        f"PRODUCT: an Archive Date not after the Publish Date was SAVED (expected 'Archive Date must be after "
        f"Publish Date' and nothing stored): {accepted}")
    no_message = {k: v["messages"] for k, v in summary.items() if "Archive Date" not in v["messages"]}
    assert not no_message, f"refused, but without an Archive Date validation message: {no_message}"


# ===========================================================================
# 143222 / 143384 — Save Draft
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Draft")
@allure.title("Save Draft stores an opportunity without publishing it and shows the success message")
@_markers("143222", "143384")
def test_save_draft_stores_record_unpublished(page, anon_pages, disposable):
    # Azure TCs 143222 / 143384 (duplicates) | Site Content Editor (143384 names
    # an Administrator — no such account; the Editor is the closest real role).
    editor = login(page, ROLE_EDITOR)
    title = a_name("143222", "save draft")
    data = OpportunityAdminPage.default_data(title)  # Active ticked: only the workflow gate hides it
    entry = create_opportunity(editor, disposable, data, publish=False)
    assert has(editor.create_banners, MSG_DRAFT_SAVED), (
        f"no Liferay success message {MSG_DRAFT_SAVED!r} after Save as Draft: {editor.create_banners}")
    editor.open_list_all()
    raw = editor.row_status_raw(entry)
    assert editor.row_status_of(entry) == "Draft", f"the management list shows status {raw!r}, not a Draft badge"
    assert_not_public(anon_pages, entry, title)


# ===========================================================================
# 143231 / 143385 — Draft not on the public listing (tabs, search, detail URL)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Draft")
@allure.title("A Draft opportunity does not appear on the public listing (Active, Archive, search, detail URL)")
@_markers("143231", "143385")
def test_draft_not_on_public_listing(page, anon_pages, disposable):
    # Azure TCs 143231 / 143385 (duplicates) | Site Content Editor + logged-out visitor.
    editor = login(page, ROLE_EDITOR)
    title = a_name("143231", "draft hidden")
    entry = create_opportunity(editor, disposable, OpportunityAdminPage.default_data(title), publish=False)
    editor.open_list_all()
    assert editor.row_status_of(entry) == "Draft", f"status {editor.row_status_raw(entry)!r}"
    editor.open_entry_en(entry.code)
    assert editor.active_status_stored() == "true", "Active Status not stored ticked (the draft gate must be the one hiding it)"
    assert_not_public(anon_pages, entry, title)
    search = BizOppPublicView(anon_pages()).open_listing("en")
    search.search(title)
    found = [c["title"] for c in search.cards()]
    search.screenshot("143231 public search for the draft title")
    allure.attach(repr(found), name="public search results")
    assert title not in found, f"the Draft record is returned by the public search: {found}"


# ===========================================================================
# 143223 / 143386 — Publish -> public Active tab
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish")
@allure.title("Publishing a Draft opportunity makes it visible on the public Active tab")
@_markers("143223", "143386", regression=True)
def test_publish_draft_shows_on_active_tab(page, anon_pages, disposable):
    # Azure TCs 143223 / 143386 (duplicates) | Site Content Editor.
    editor = login(page, ROLE_EDITOR)
    title = a_name("143223", "publish")
    entry = create_opportunity(editor, disposable, OpportunityAdminPage.default_data(title), publish=False)
    # Step 1 — the Draft record opens with status Draft.
    editor.open_entry_en(entry.code)
    assert editor.current_status() == "Draft", f"editing bar: {editor.editbar_texts()}"
    # Step 2 — Publish.
    pinned(editor, ROLE_EDITOR)
    editor.click_publish()
    banners = editor.success_messages(MSG_SAVED_AND_PUBLISHED) if editor.save_went_through() else editor.editbar_texts()
    editor.evidence("143223 published")
    assert editor.save_went_through(), f"Publish did not go through: {editor.save_outcome()}"
    assert has(banners, MSG_SAVED_AND_PUBLISHED), f"no success message after Publish: {banners}"
    assert editor.wait_status(entry, ("Published",)) == "Published", "status did not reach Published"
    history(editor, entry)
    # Step 3 — public Active tab: card, title, tag, working View Details link.
    require_active_status(editor, entry)
    view, _ = public_until(anon_pages, lambda v: bool(v.card_for(entry.code)),
                           f"DELIVERY: {title!r} never appeared on the logged-out Active tab")
    card = view.card_for(entry.code)
    view.screenshot("143223 public active tab")
    allure.attach(repr(card), name="public card")
    assert card["title"] == title, f"card title {card['title']!r} != {title!r}"
    assert "Energy" in card["tag"] and "Equity" in card["tag"], f"card tag {card['tag']!r} (expected Energy x Equity)"
    detail = BizOppPublicView(anon_pages()).open_detail(entry.code).detail()
    assert title in detail["body"], "View Details target does not render the record's title"


# ===========================================================================
# 143387 — Publish Date / Archive Date / Display Order persist
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Persistence")
@allure.title("Publish Date, Archive Date and Sort (Display) Order persist after save and reload")
@_markers("143387")
def test_dates_and_display_order_persist(page, disposable):
    # Azure TC 143387 | Administrator = TEST_USER (user decision 2026-10-07) |
    # Case dates 2026-10-01 / 2026-12-31 (a 91-day window) -> dates RELATIVE to today (today-6 /
    # today+85, same shape: publish already started, archive ~3 months ahead) so the case keeps
    # working after 2026; Sort Order 5 -> Display Order 500 (100-grid).
    editor, _ = login_any(page, ROLE_ADMINISTRATOR)
    publish_dt, archive_dt = date.today() + timedelta(days=-6), date.today() + timedelta(days=85)
    data = OpportunityAdminPage.default_data(a_name("143387", "persist"), active_status=False,
                                             **{K_PUBLISH_DATE: publish_dt.strftime("%d/%m/%Y"),
                                                K_ARCHIVE_DATE: archive_dt.strftime("%d/%m/%Y"),
                                                K_DISPLAY_ORDER: "500"})
    entry = create_opportunity(editor, disposable, data, publish=False, role=ROLE_ADMINISTRATOR)
    assert has(editor.create_banners, MSG_DRAFT_SAVED), f"no save confirmation: {editor.create_banners}"
    editor.open_list_all()  # navigate away
    editor.open_entry_en(entry.code)
    stored = {"publish": editor.date_stored(K_PUBLISH_DATE), "archive": editor.date_stored(K_ARCHIVE_DATE),
              "display_order": editor.text_value(K_DISPLAY_ORDER)}
    allure.attach(repr(stored), name="stored values after reopen")
    expected = {"publish": publish_dt.isoformat(), "archive": archive_dt.isoformat(), "display_order": "500"}
    assert stored == expected, f"stored after reopen {stored} != entered {expected}"


# ===========================================================================
# 143389 — auto-archive on the Archive Date (Blocked)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Dates")
@allure.title("A Published opportunity auto-transitions to Archived on its Archive Date")
@_markers("143389")
@pytest.mark.skip(reason="BLOCKED (brief rule 14): Archive Date is a DATE field (dd/mm/yyyy, no time), so a QCTEST "
                         "record cannot be set to archive a few minutes ahead; the transition can only be observed "
                         "across a day boundary. Question: may a QCTEST record with Archive Date = tomorrow stay "
                         "Published overnight to be checked the next day?")
def test_auto_archive_on_archive_date():
    pass

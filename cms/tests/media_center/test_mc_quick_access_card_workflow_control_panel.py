"""
cms/tests/media_center/test_mc_quick_access_card_workflow_control_panel.py — QAC agent.

Workflow / role / preview / toast / history cases of PBI 130709 (suite 140368)
on `manage-media-center-quick-access-card`. Same data rules and disclosed
substitutions as test_mc_quick_access_card_control_panel.py, plus:
  - Every role runs in its own fresh logged-out context signed in with
    cms_role_credentials(<role>); the signed-in userId is re-checked before a
    role-dependent assertion (a dropped session would be re-authenticated as
    TEST_USER by the session guard).
  - "forced request for the approve action" -> the POST the row action itself
    sends (/o/qc-object-status/approve/<id>, CSRF token via Liferay.Util.fetch)
    issued from the Author's session.
  - Preview / draft cases run from the Site Content Author account (rules 5).
  - Public steps that come before a CMS step are evaluated, their failure is
    kept and re-raised at the end of the test (never swallowed), so the CMS
    steps still run and are asserted.
"""

from __future__ import annotations

import re
from time import monotonic

import allure
import pytest

from core.utils.waits import WaitTimeoutError, wait_until

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.media_center.mc_quick_access_card_admin_page import (
    MSG_ACCESS_DENIED,
    MSG_ACCESS_DENIED_AR,
    MSG_DRAFT_SAVED,
    MSG_SUBMITTED_FOR_REVIEW,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_FORM_MANAGER,
    ROLE_MEMBER,
    QacEntry,
)
from cms.tests.media_center.qac_support import (  # noqa: F401 — fixtures
    PUBLISH_CONFIRM_TIMEOUT,
    QAC01,
    VIDEO_LIBRARY,
    attach,
    card_data,
    create,
    create_ok,
    edit,
    expected_index,
    find,
    public_until,
    qac,
    real_cards,
    real_guard,
    real_session,
    guarded_edit,
    record_finding,
    require_active,
    require_role,
    save,
    stored,
)

pytestmark = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.pbi_130709,
              pytest.mark.xdist_group("mc_qac_130709")]

EPIC = "Media Center"
FEATURE = "Quick Access Card — Control Panel (workflow & roles)"
ARABIC = re.compile(r"[؀-ۿ]")


def _labels(tc: str, qa: str, title: str):
    allure.dynamic.epic(EPIC)
    allure.dynamic.feature(FEATURE)
    allure.dynamic.title(title)
    allure.dynamic.label("testcase", tc)
    allure.dynamic.label("pbi", "130709")
    allure.dynamic.label("qa_id", qa)


class Late:
    """Collects a public-step failure that precedes CMS steps; re-raised at the end."""

    def __init__(self):
        self.failures: list[str] = []

    def run(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AssertionError as exc:
            self.failures.append(str(exc).splitlines()[0])
            return None

    def raise_if_any(self):
        assert not self.failures, "EARLIER PUBLIC STEP(S) FAILED: " + " || ".join(self.failures)


def _hidden(visitor, title: str, locale: str = "en") -> list[dict]:
    visitor.open_hub(locale)
    return [c for c in visitor.cards() if c["title"] == title]


def _parts_loaded(admin) -> dict:
    parts = admin.manage_page_parts()
    attach("manage page parts", {k: v for k, v in parts.items() if k != "body"})
    return parts


# ===========================================================================
@pytest.mark.tc_149252
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.uat
def test_editor_created_card_is_published_in_order_and_navigates(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-198 — Editor publishes a card: in its Display Order slot, arrow opens the destination.

    Healed 2026-10-13 (bug 149913 fix): the six quick-access cards are a FIXED
    set — the manage page no longer offers Add New (asserted), so the Editor's
    publish is exercised on the real Video Library card under
    snapshot -> edit -> restore -> diff (real_guard)."""
    _labels("149252", "MEDIA-MCHUB-TC-198", "Editor-published card in its Display Order slot")
    # NOTE: the Editor CREATE part of TC149252 is not reachable now (no Add New; Author has no Edit).
    sessions, admin, ref = real_session(qac, real_guard, "QCDEMO-130709-CARD-02")
    admin.open_list_all()
    parts = _parts_loaded(admin)
    offered = admin.add_new_offered()
    admin.evidence("149252_manage_list")
    attach("Add New controls", offered)
    assert not offered, f"PRODUCT: Add New is still offered on a fixed-block object: {offered}"
    assert parts["list"] and parts["preview"], f"manage page parts missing: {parts}"
    order_before = real_guard.snapshots[ref.code]["displayOrder"]
    title = "QCTEST-R30-D Video Library"
    result = guarded_edit(real_guard, admin, ref, {"cardTitle": title}, "149252")
    assert result["went_through"], f"the Editor's publish was refused: {result.get('evidence')}"
    admin.open_list_all()
    assert admin.wait_row_status(ref, (STATUS_PUBLISHED,), 120) == STATUS_PUBLISHED
    require_active(admin, ref)
    values = stored(admin, ref)
    assert values["cardTitle"] == title and str(values["displayOrder"]) == str(order_before), \
        f"stored values after publish: {values}"
    visitor = sessions.visitor()
    cards = public_until(visitor, lambda c: find(c, ref.code).get("title") == title,
        f"card title = {title!r}", "149252", budget=False)
    assert find(cards, ref.code).get("href") == VIDEO_LIBRARY, f"card href: {find(cards, ref.code)}"
    landed = visitor.follow_card(ref.code)
    attach("navigation", landed)
    assert landed["url"].split("?")[0].rstrip("/").endswith(VIDEO_LIBRARY), f"the arrow opened {landed['url']!r}"


@pytest.mark.tc_149253
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.uat
def test_author_card_waits_in_pending_review_until_editor_approves(qac, real_cards):
    """MEDIA-MCHUB-TC-199 — Author has no create/edit/submit path on the fixed cards.

    Converted 2026-10-13 (user decision: BY DESIGN, Add New removed)."""
    _labels("149253", "MEDIA-MCHUB-TC-199", "Author has no Add New / Edit / Submit on the fixed cards")
    # NOTE: Author submit -> Pending Review -> Editor approve is not reachable by design now (no Add New, no Author Edit).
    sessions, _ = qac
    author = sessions.admin(ROLE_AUTHOR)
    require_role(author, ROLE_AUTHOR)
    author.open_list_all()
    offered = author.add_new_offered()
    rows = author.list_rows()
    author.evidence("149253_author_list")
    edit_links = author.page.locator('tbody tr a[href*="editEntry="]').count()
    submit_actions = author.page.locator("tbody tr [data-qc-oel-submit], tbody tr [data-qc-oel-resubmit], "
                                         "tbody tr [data-qc-oel-publish], tbody tr [data-qc-oel-approve]").count()
    attach("Author list", {"add_new": offered, "rows": len(rows), "edit_links": edit_links, "submit": submit_actions})
    assert rows, "PRECONDITION: the Author sees no card rows"
    assert not offered, f"the Author is offered Add New: {offered}"
    assert edit_links == 0, f"the Author is offered Edit on {edit_links} row(s)"
    assert submit_actions == 0, f"the Author is offered {submit_actions} submit/publish/approve control(s)"


@pytest.mark.tc_149255
@pytest.mark.functional_high
@pytest.mark.workflow
def test_preview_renders_draft_card_en_ar_but_visitors_do_not_see_it(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-201 — Preview panel renders the card inside the Media Center hub in EN and AR.

    Healed 2026-10-13 (bugs 149906 / 149913): Add New is gone and the Site
    Content Author has no Edit on any of the six fixed cards, so no draft
    card can be made without drafting (de facto unpublishing) a real card,
    which is forbidden. The Preview is exercised READ-ONLY on the real
    published Photo Gallery card as the Editor: the frame must be the hub
    (not the field list) with the card, EN left-to-right and AR right-to-left."""
    _labels("149255", "MEDIA-MCHUB-TC-201", "Preview renders the card in the Media Center hub (EN/AR)")
    # NOTE: the draft + logged-out-visitor part of TC149255 is not reachable now (Author has no Edit, no Add New).
    real_guard.take("QCDEMO-130709-CARD-01")  # read-only snapshot (restore is a no-op diff)
    title_ar = real_guard.snapshots["QCDEMO-130709-CARD-01"].get("cardTitle_i18n", {}).get("ar_SA", "")
    assert title_ar, "PRECONDITION: the snapshot has no Arabic card title"
    sessions, _ = qac
    editor = sessions.admin(ROLE_EDITOR)
    editor.open_list_all()
    real = [r for r in editor.list_rows() if r["code"] == "QCDEMO-130709-CARD-01"]
    assert real, "PRECONDITION: the real Photo Gallery card is not listed"
    entry = QacEntry(real[0]["title"].strip(), real[0]["entry_id"], real[0]["code"])
    attach("draft step not runnable", "No Add New and no Author edit on the fixed cards; preview checked "
           "on the published real card (read-only).")
    editor.click_row_preview(entry)
    en = editor.preview_frame_text((entry.title,), 45)
    editor.evidence("149255_preview_en")
    attach("preview EN", en)
    assert "/media-center?" in en.get("frame_url", ""), f"the preview frame is not the hub: {en.get('frame_url')!r}"
    assert "Explore the hub" in en.get("frame_text", "") and entry.title in en.get("frame_text", ""), \
        f"the preview does not render the Media Center hub with the card (frame {en.get('frame_url')!r})"
    editor.click_preview_locale("ar")
    seen = {"ar": {}}

    def _ar_loaded() -> bool:
        seen["ar"] = editor.preview_frame_text((), 5)
        return seen["ar"].get("frame_dir") == "rtl" and title_ar in seen["ar"].get("frame_text", "")

    wait_until(_ar_loaded, timeout=45.0, poll=1.0)  # WaitTimeoutError fails the test with its reason
    ar = seen["ar"]
    editor.evidence("149255_preview_ar")
    attach("preview AR", ar)
    assert ar.get("frame_dir") == "rtl" and title_ar in ar.get("frame_text", ""), \
        f"the AR preview lacks {title_ar!r} right-to-left: {ar.get('frame_url')!r} dir={ar.get('frame_dir')!r}"

@pytest.mark.tc_149256
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.regression
def test_unpublish_removes_card_and_grid_reflows(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-202 — Unpublish -> UNPUBLISHED, card gone, the other cards close the gap.

    Healed 2026-10-13: no Add New, so a real card (CARD-02, guard-approved) is
    unpublished for the shortest possible window, re-published through the row
    action at once, and restored + diffed by real_guard."""
    _labels("149256", "MEDIA-MCHUB-TC-202", "Unpublish removes the card from the hub")
    sessions, _ = qac
    ref = real_guard.take("QCDEMO-130709-CARD-02")
    admin = sessions.admin(ROLE_EDITOR)
    visitor = sessions.visitor()
    before = public_until(visitor, lambda c: bool(find(c, ref.code)), "card shown", "149256", budget=False)
    expected_rest = [c["erc"] for c in before if c["erc"] != ref.code]
    admin.open_list_all()
    real_guard.check_before_edit(ref.code)
    failure = None
    try:
        dialogs = admin.run_real_row_action(ref, "unpublish", real_guard)
        attach("unpublish dialogs", dialogs)
        started = monotonic()
        status = admin.wait_row_status(ref, (STATUS_UNPUBLISHED,), 60)
        try:
            assert status == STATUS_UNPUBLISHED, f"after Unpublish the badge reads {status!r} (expected UNPUBLISHED)"
            cards = public_until(visitor, lambda c: not find(c, ref.code), "card gone", "149256", started=started)
            assert [c["erc"] for c in cards] == expected_rest,                 f"the remaining cards do not close the gap in order: {[c['erc'] for c in cards]}"
        except AssertionError as exc:
            failure = exc
    finally:
        admin.open_list_all()
        if admin.row_status_of(ref) != STATUS_PUBLISHED:
            attach("re-publish dialogs", admin.run_real_row_action(ref, "publish", real_guard))
            admin.wait_row_status(ref, (STATUS_PUBLISHED,), PUBLISH_CONFIRM_TIMEOUT)
        real_guard.record_written(ref.code)
    assert admin.row_status_of(ref) == STATUS_PUBLISHED, "the real card was not re-published"
    public_until(visitor, lambda c: bool(find(c, ref.code)), "card back", "149256", budget=False)
    if failure:
        raise failure


@pytest.mark.tc_149257
@pytest.mark.functional_high
@pytest.mark.workflow
def test_unpublished_card_can_be_published_again(qac, real_cards):
    """MEDIA-MCHUB-TC-203 — Unpublished -> Publish -> back on the hub."""
    _labels("149257", "MEDIA-MCHUB-TC-203", "Unpublished card can be published again")
    sessions, registry = qac
    admin = sessions.admin(ROLE_EDITOR)
    entry = create_ok(admin, registry, dict(QAC01), "149257")
    admin.open_list_all()
    admin.run_row_action(entry, "unpublish")
    assert admin.wait_row_status(entry, (STATUS_UNPUBLISHED,), 60) == STATUS_UNPUBLISHED, "PRECONDITION: not Unpublished"
    require_active(admin, entry)
    admin.open_list_all()
    dialogs = admin.run_row_action(entry, "publish")
    attach("publish dialogs", dialogs)
    started = monotonic()
    status = admin.wait_row_status(entry, (STATUS_PUBLISHED,), 120)
    assert status == STATUS_PUBLISHED, f"after Publish the badge reads {status!r}"
    attach("public step adapted (user decision 2026-10-12)", "The six quick-access cards are FIXED by design (hub maxCards=6): a 7th card never renders publicly; QCTEST card visibility is not asserted.")


@pytest.mark.tc_149280
@pytest.mark.ui
def test_success_toasts_in_english(qac, real_cards):
    """MEDIA-MCHUB-TC-226 — 'Draft saved.' then 'Saved and submitted for review.' (Editor)."""
    _labels("149280", "MEDIA-MCHUB-TC-226", "English success toasts after Save as Draft / Submit")
    sessions, registry = qac
    admin = sessions.admin(ROLE_EDITOR)
    data = card_data("QCTEST Toast Card", "QCTEST بطاقة الإشعار", "QCTEST toast card.", "QCTEST بطاقة الإشعار.", 1000)
    entry, result = create(admin, registry, data, "149280", publish=False)
    assert result["went_through"] and entry is not None, f"Save as Draft failed: {result}"
    draft_msgs = " | ".join(result.get("editbar", []))
    admin.open_list_all()
    draft_badge = admin.row_status_of(entry)
    admin.open_entry(entry.code)
    submit = save(admin, ROLE_EDITOR, True)
    submit["screenshot"] = admin.evidence("149280_after_submit")
    attach("submit", submit)
    submit_msgs = " | ".join(submit.get("editbar", []))
    status = admin.wait_row_status(entry, (STATUS_PUBLISHED,), 120)
    assert MSG_DRAFT_SAVED in draft_msgs, f"Save as Draft message: {draft_msgs!r}"
    assert draft_badge == STATUS_DRAFT, f"after Save as Draft the badge reads {draft_badge!r}"
    assert submit["went_through"], f"submit refused: {submit['evidence']}"
    assert status == STATUS_PUBLISHED, f"after submit the badge reads {status!r}"
    if MSG_SUBMITTED_FOR_REVIEW not in submit_msgs:
        record_finding("149280", "WORDING", expected=MSG_SUBMITTED_FOR_REVIEW, shown=submit_msgs,
                       screenshot=submit["screenshot"])


@pytest.mark.tc_149281
@pytest.mark.ui
@pytest.mark.bilingual
def test_success_toast_in_arabic_ui(qac, real_cards):
    """MEDIA-MCHUB-TC-227 — Arabic success toast in the AR interface."""
    _labels("149281", "MEDIA-MCHUB-TC-227", "Arabic success toast in the AR UI")
    sessions, registry = qac
    admin = sessions.admin(ROLE_EDITOR)
    data = card_data("QCTEST AR Toast", "QCTEST إشعار عربي", "QCTEST AR toast card.", "QCTEST بطاقة إشعار عربي.", 1000)
    entry = create_ok(admin, registry, data, "149281", publish=False)
    admin.open_entry(entry.code, locale="ar")
    button = admin.submit_button_text_any()
    assert ARABIC.search(button), f"the interface is not Arabic (button {button!r})"
    require_role(admin, ROLE_EDITOR)
    admin.click_submit_any_locale()
    went = admin.save_went_through()
    msgs = admin.success_messages("", 3.0)
    shot = admin.evidence("149281_ar_toast")
    attach("AR toast", {"went_through": went, "editbar": msgs})
    assert went, f"submit refused: {admin.refusal_evidence()}"
    status = admin.wait_row_status(entry, (STATUS_PUBLISHED,), 120)
    assert status == STATUS_PUBLISHED, f"after submit the badge reads {status!r}"
    success = [m for m in msgs if not m.startswith("Editing") and ARABIC.search(m)]
    assert success, f"no Arabic success message after submit in the AR UI: {msgs!r} ({shot})"


@pytest.mark.tc_149282
@pytest.mark.functional_high
@pytest.mark.workflow
def test_history_records_each_change_with_actor_and_time(qac, real_cards):
    """MEDIA-MCHUB-TC-228 — Draft (T1), publish (T2), unpublish (T3) recorded in History."""
    _labels("149282", "MEDIA-MCHUB-TC-228", "History records draft / publish / unpublish")
    sessions, registry = qac
    admin = sessions.admin(ROLE_EDITOR)
    data = card_data("QCTEST History Card", "QCTEST بطاقة السجل", "QCTEST history card.", "QCTEST بطاقة السجل.", 1000)
    entry = create_ok(admin, registry, data, "149282", publish=False)
    admin.open_entry(entry.code)
    assert save(admin, ROLE_EDITOR, True)["went_through"], "PRECONDITION: publish (T2) failed"
    assert admin.wait_row_status(entry, (STATUS_PUBLISHED,), 120) == STATUS_PUBLISHED
    admin.open_list_all()
    admin.run_row_action(entry, "unpublish")
    status = admin.wait_row_status(entry, (STATUS_UNPUBLISHED,), 60)
    assert status == STATUS_UNPUBLISHED, f"after Unpublish the badge reads {status!r}"
    trail = admin.history(entry)
    admin.evidence("149282_history")
    attach("history", trail)
    editor_name = admin.signed_in_user()[1]
    mine = [h for h in trail if editor_name in h["who"] and h["when"]]
    actions = [h["action"].lower() for h in mine]
    assert len(mine) >= 3, f"History holds {len(mine)} timestamped Editor entries, expected draft+publish+unpublish: {trail}"
    assert any(a in ("created", "saved as draft") or "draft" in a for a in actions), f"no draft-save entry: {trail}"
    assert any(a in ("approved", "published") for a in actions), f"no publish entry: {trail}"
    assert any(a == "unpublished" for a in actions), f"no unpublish entry: {trail}"


@pytest.mark.tc_149330
@pytest.mark.auth
@pytest.mark.workflow
@pytest.mark.regression
def test_author_cannot_approve_pending_card(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-276 — no Approve for the Author; a forced approve is refused with Access Denied.

    Healed 2026-10-13 (bug 149913): the Author can no longer create (no Add New)
    nor edit the six fixed cards, so no Pending Review card can be made. The
    forced approve is POSTed from the Author's session against a real card
    under snapshot -> restore -> diff; the role check must refuse it (403)."""
    _labels("149330", "MEDIA-MCHUB-TC-276", "Author cannot approve a card (forced approve refused)")
    # NOTE: the Author submit -> Pending Review part of TC149330 is not reachable now (Author has no Edit, no Add New).
    sessions, _ = qac
    ref = real_guard.take("QCDEMO-130709-CARD-01")
    author = sessions.admin(ROLE_AUTHOR)
    require_role(author, ROLE_AUTHOR)
    author.open_list_all()
    rows = [r for r in author.list_rows() if r["entry_id"] == ref.entry_id]
    assert rows, "PRECONDITION: the Author does not see the card row"
    entry = QacEntry(rows[0]["title"].strip(), ref.entry_id, rows[0]["code"])
    actions = author.row_actions(entry)
    attach("Author row actions", actions)
    assert not {"approve", "publish"} & set(actions), f"the Author is offered {actions}"
    real_guard.check_before_edit(ref.code)
    try:
        forced = author.forced_transition("approve", ref.entry_id)
    finally:
        real_guard.record_written(ref.code)
    author.evidence("149330_after_forced")
    attach("forced approve", forced)
    assert forced["status"] == 403, f"PRODUCT: the forced approve answered {forced}"
    assert MSG_ACCESS_DENIED in forced["body"], f"PRODUCT: no Access Denied message: {forced}"
    assert real_guard.written[ref.code].get("dateModified") == real_guard.snapshots[ref.code].get("dateModified"), \
        "PRODUCT: the forced approve modified the card"


@pytest.mark.tc_149331
@pytest.mark.auth
@pytest.mark.workflow
def test_author_cannot_edit_card_not_assigned_to_them(qac, real_cards):
    """MEDIA-MCHUB-TC-277 — Author cannot edit the Editor's card."""
    _labels("149331", "MEDIA-MCHUB-TC-277", "Author cannot edit a card that is not theirs")
    sessions, registry = qac
    editor = sessions.admin(ROLE_EDITOR)
    entry = create_ok(editor, registry, dict(QAC01), "149331")
    require_active(editor, entry)
    author = sessions.admin(ROLE_AUTHOR)
    author.open_list_all()
    has_edit = author.row_has_edit_link(entry)
    outcome = {"edit_link": has_edit, "actions": author.row_actions(entry)}
    if has_edit:
        author.open_entry(entry.code)
        outcome["form_visible"] = author.form_visible()
        if outcome["form_visible"]:
            author.fill_en("cardTitle", "QCTEST Author Edit")
            res = save(author, ROLE_AUTHOR, True)
            outcome.update({"went_through": res["went_through"], "messages": res["messages"]})
    outcome["screenshot"] = author.evidence("149331_author")
    attach("Author edit attempt", outcome)
    title_after = stored(editor, entry)["cardTitle"]
    if title_after != entry.title:  # put the identity back for the guarded teardown
        editor.fill_en("cardTitle", entry.title)
        save(editor, ROLE_EDITOR, True)
    assert title_after == "QCTEST Media Kit", f"PRODUCT: the Author changed the title to {title_after!r}"
    if outcome.get("went_through") is False and MSG_ACCESS_DENIED not in outcome.get("messages", ""):
        record_finding("149331", "WORDING", expected=MSG_ACCESS_DENIED, shown=outcome.get("messages"))
    # Public step on a REAL card (read-only): the Author has no Edit on it either
    # and its public title is unchanged (a QCTEST card never renders: fixed six cards).
    real = QacEntry("Photo Gallery", "206466", "QCDEMO-130709-CARD-01")
    author.open_list_all()
    assert not author._row_a(real).first.locator('a[href*="editEntry="]').count(), "the Author has Edit on a real card"
    public_until(sessions.visitor(), lambda c: find(c, real.code).get("title") == "Photo Gallery",
        "real card title unchanged", "149331", budget=False)


@pytest.mark.tc_149333
@pytest.mark.auth
@pytest.mark.workflow
def test_form_manager_cannot_create_hub_content(qac, real_cards):
    """MEDIA-MCHUB-TC-279 — Form Manager has no add form / Access Denied."""
    _labels("149333", "MEDIA-MCHUB-TC-279", "Form Manager cannot create or edit hub content")
    sessions, registry = qac
    editor = sessions.admin(ROLE_EDITOR)
    ids_before = editor.snapshot_ids()
    fm = sessions.admin(ROLE_FORM_MANAGER, open_list=False)
    fm.open_manage_page_raw()
    body = fm.wait_body_contains((MSG_ACCESS_DENIED, "entries"), 30.0)
    form = fm.form_visible()
    outcome = {"form_visible": form, "access_denied_shown": MSG_ACCESS_DENIED in body, "body": body[:600]}
    if form:
        data = card_data("QCTEST Form Manager Card", "QCTEST بطاقة مدير النماذج", "QCTEST form manager card.",
        "QCTEST بطاقة مدير النماذج.", 1000)
        fm.fill_card(data)
        res = save(fm, ROLE_FORM_MANAGER, True)
        outcome.update({"went_through": res["went_through"], "messages": res["messages"]})
    outcome["screenshot"] = fm.evidence("149333_form_manager")
    attach("Form Manager attempt", outcome)
    new = [r for r in editor.new_rows_since(ids_before) if r["title"].strip() == "QCTEST Form Manager Card"]
    for row in new:
        registry.track(editor.adopt(QacEntry(row["title"].strip(), row["entry_id"], row["code"])))
    assert not new, f"PRODUCT: the Form Manager created {new}"
    assert not _hidden(sessions.visitor(), "QCTEST Form Manager Card")
    assert not form or outcome.get("went_through") is False, "PRODUCT: the Form Manager's save went through"
    assert not form or MSG_ACCESS_DENIED in outcome.get("messages", "") or outcome["access_denied_shown"], \
        f"the Form Manager gets an add form and no Access Denied message: {outcome}"


@pytest.mark.tc_149337
@pytest.mark.auth
@pytest.mark.bilingual
def test_access_denied_message_in_arabic_for_site_member(qac):
    """MEDIA-MCHUB-TC-283 — 'تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء.'"""
    _labels("149337", "MEDIA-MCHUB-TC-283", "Arabic Access Denied for a site member")
    sessions, _ = qac
    member = sessions.admin(ROLE_MEMBER, open_list=False)
    member.open_manage_page_raw("ar")
    body = member.wait_body_contains((MSG_ACCESS_DENIED_AR,), 30.0)
    shot = member.evidence("149337_member_ar")
    parts = member.manage_page_parts()
    attach("site member AR page", {"url": member.page.url, "title": member.page.title(), "body": body[:800],
        "form": parts["form"], "rows": parts["rows"]})
    assert not parts["form"] and parts["rows"] == 0, "PRODUCT: the site member can see the authoring list/form"
    assert MSG_ACCESS_DENIED_AR in body, \
        f"the AR page does not show the Arabic Access Denied message (title {member.page.title()!r}; {shot})"

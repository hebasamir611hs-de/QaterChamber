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
def test_editor_created_card_is_published_in_order_and_navigates(qac, real_cards):
    """MEDIA-MCHUB-TC-198 — Editor create+publish: 7th card, arrow opens the destination."""
    _labels("149252", "MEDIA-MCHUB-TC-198", "Editor-created card published in its Display Order slot")
    sessions, registry = qac
    admin = sessions.admin(ROLE_EDITOR)
    parts = _parts_loaded(admin)
    assert parts["list"] and parts["form"] and parts["preview"], f"manage page parts missing: {parts}"
    entry, result = create(admin, registry, dict(QAC01), "149252")
    assert result["went_through"] and entry is not None, f"create failed: {result}"
    if not result.get("arabic_saved"):
        record_finding("149252", "INFO", note="'Arabic content saved for this record.' not shown (guide 5)",
                       editbar=result.get("editbar"))
    started = monotonic()
    admin.open_list_all()
    row = admin.row_of(entry)
    assert row["code"] and row["entry_id"], f"no system identifier on the row: {row}"
    assert admin.row_status_of(entry) == STATUS_PUBLISHED
    require_active(admin, entry)
    values = stored(admin, entry)
    assert values["cardTitle_ar"] == QAC01["cardTitle_ar"] and \
        values["cardDescription_ar"] == QAC01["cardDescription_ar"], f"the Arabic content was not stored: {values}"
    attach("public step adapted (user decision 2026-10-12)", "The six quick-access cards are FIXED by design (hub maxCards=6): a 7th card never renders publicly; QCTEST card visibility is not asserted.")
    visitor = sessions.visitor()
    public_until(visitor, lambda c: find(c, "QCDEMO-130709-CARD-02").get("href") == VIDEO_LIBRARY,
                 "a card whose Destination Link is /web/qatar-chamber/video-library", "149252", budget=False)
    landed = visitor.follow_card("QCDEMO-130709-CARD-02")  # read-only: real card with the same destination
    attach("navigation", landed)
    assert landed["url"].split("?")[0].rstrip("/").endswith(VIDEO_LIBRARY), f"the arrow opened {landed['url']!r}"


@pytest.mark.tc_149253
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.uat
def test_author_card_waits_in_pending_review_until_editor_approves(qac, real_cards):
    """MEDIA-MCHUB-TC-199 — Author submit -> Pending Review (hidden) -> Editor approve -> live."""
    _labels("149253", "MEDIA-MCHUB-TC-199", "Author card: Pending Review until the Editor approves")
    sessions, registry = qac
    author = sessions.admin(ROLE_AUTHOR)
    data = card_data("QCTEST Author Card", "QCTEST بطاقة المؤلف", "QCTEST Card submitted by the author.",
                     "QCTEST بطاقة أرسلها المؤلف.", 800)
    entry, result = create(author, registry, data, "149253", role=ROLE_AUTHOR)
    assert result["went_through"] and entry is not None, f"the Author's submit failed: {result}"
    shown = " | ".join(result.get("editbar", []))
    if MSG_SUBMITTED_FOR_REVIEW not in shown:
        record_finding("149253", "WORDING", expected=MSG_SUBMITTED_FOR_REVIEW, shown=shown)
    status = author.wait_row_status(entry, (STATUS_PENDING_REVIEW,), 60)
    assert status == STATUS_PENDING_REVIEW, f"the Author's submit landed on {status!r}"
    visitor = sessions.visitor()
    assert not _hidden(visitor, "QCTEST Author Card"), "a Pending Review card is visible to visitors"
    editor = sessions.admin(ROLE_EDITOR)
    editor.adopt(entry)
    editor.open_list_all()
    dialogs = editor.run_row_action(entry, "approve", "")
    attach("approve dialogs", dialogs)
    started = monotonic()
    status = editor.wait_row_status(entry, (STATUS_PUBLISHED,), 120)
    assert status == STATUS_PUBLISHED, f"after Approve the badge reads {status!r}"
    trail = editor.history(entry)
    attach("history", trail)
    author_name = author.signed_in_user()[1]
    editor_name = editor.signed_in_user()[1]
    assert any(author_name in h["who"] and h["when"] for h in trail), f"History lacks the Author's submit: {trail}"
    assert any(editor_name in h["who"] and h["when"] for h in trail), f"History lacks the Editor's publish: {trail}"
    attach("public step adapted (user decision 2026-10-12)", "The six quick-access cards are FIXED by design (hub maxCards=6): a 7th card never renders publicly; QCTEST card visibility is not asserted.")


@pytest.mark.tc_149255
@pytest.mark.functional_high
@pytest.mark.workflow
def test_preview_renders_draft_card_en_ar_but_visitors_do_not_see_it(qac, real_cards):
    """MEDIA-MCHUB-TC-201 — Preview panel renders the draft card in EN and AR."""
    _labels("149255", "MEDIA-MCHUB-TC-201", "Preview renders a draft card in EN/AR, not public")
    sessions, registry = qac
    author = sessions.admin(ROLE_AUTHOR)
    data = card_data("QCTEST Preview Card", "QCTEST بطاقة المعاينة", "QCTEST Preview card.", "QCTEST بطاقة معاينة.", 800)
    entry = create_ok(author, registry, data, "149255", role=ROLE_AUTHOR, publish=False)
    author.open_list_all()
    assert author.row_status_of(entry) == STATUS_DRAFT
    parts = _parts_loaded(author)
    late = Late()
    author.click_row_preview(entry)
    en = author.preview_frame_text(("QCTEST Preview Card",))
    author.evidence("149255_preview_en")
    attach("preview EN", en)
    banner_ok = "unpublished (draft)" in en.get("frame_text", "") or "draft" in en.get("frame_text", "").lower()
    if not ("Explore the hub" in en.get("frame_text", "") and "QCTEST Preview Card" in en.get("frame_text", "")):
        late.failures.append(f"the preview does not render the Media Center hub with the card (panel "
                             f"{en.get('panel_text', '')[:120]!r}, frame {en.get('frame_url')!r})")
    author.click_preview_locale("ar")
    ar = author.preview_frame_text(("QCTEST بطاقة المعاينة",))
    author.evidence("149255_preview_ar")
    attach("preview AR", ar)
    visitor = sessions.visitor()
    assert not _hidden(visitor, "QCTEST Preview Card"), "the draft card is visible to a logged-out visitor"
    assert banner_ok, f"no draft banner in the preview: {en.get('frame_text', '')[:300]!r}"
    assert "QCTEST بطاقة المعاينة" in ar.get("frame_text", "") and ar.get("frame_dir") == "rtl", \
        f"the AR preview does not show the Arabic title right-to-left: {ar.get('frame_text', '')[:200]!r}"
    late.raise_if_any()


@pytest.mark.tc_149256
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.regression
def test_unpublish_removes_card_and_grid_reflows(qac, real_cards):
    """MEDIA-MCHUB-TC-202 — Unpublish -> UNPUBLISHED, card gone, six real cards fill the grid."""
    _labels("149256", "MEDIA-MCHUB-TC-202", "Unpublish removes the card from the hub")
    sessions, registry = qac
    admin = sessions.admin(ROLE_EDITOR)
    entry = create_ok(admin, registry, dict(QAC01), "149256")
    require_active(admin, entry)
    idx = expected_index(real_cards, 700)
    visitor = sessions.visitor()
    late = Late()
    attach("public step adapted (user decision 2026-10-12)", "The six quick-access cards are FIXED by design (hub maxCards=6): a 7th card never renders publicly; QCTEST card visibility is not asserted.")
    admin.open_list_all()
    dialogs = admin.run_row_action(entry, "unpublish")
    attach("unpublish dialogs", dialogs)
    started = monotonic()
    status = admin.wait_row_status(entry, (STATUS_UNPUBLISHED,), 60)
    assert status == STATUS_UNPUBLISHED, f"after Unpublish the badge reads {status!r} (expected UNPUBLISHED)"
    real = [c["code"] for c in real_cards["cards"] if c["active"] and c["status"] == "PUBLISHED"]
    cards = public_until(visitor, lambda c: not find(c, entry.code), "QAC-01 gone", "149256", started=started)
    assert [c["erc"] for c in cards] == sorted(real, key=lambda k: [x["order"] for x in real_cards["cards"]
                                                                   if x["code"] == k][0]), \
        f"the six configured cards do not fill the grid in order: {[c['erc'] for c in cards]}"
    late.raise_if_any()


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
def test_author_cannot_approve_pending_card(qac, real_cards):
    """MEDIA-MCHUB-TC-276 — no Approve for the Author; a forced approve is refused."""
    _labels("149330", "MEDIA-MCHUB-TC-276", "Author cannot approve a Pending Review card")
    sessions, registry = qac
    author = sessions.admin(ROLE_AUTHOR)
    data = card_data("QCTEST Author Card", "QCTEST بطاقة المؤلف", "QCTEST Card submitted by the author.",
                     "QCTEST بطاقة أرسلها المؤلف.", 800)
    entry, result = create(author, registry, data, "149330", role=ROLE_AUTHOR)
    assert result["went_through"] and entry is not None, f"PRECONDITION: Author submit failed: {result}"
    assert author.wait_row_status(entry, (STATUS_PENDING_REVIEW,), 60) == STATUS_PENDING_REVIEW
    actions = author.row_actions(entry)
    attach("Author row actions", actions)
    assert not {"approve", "publish"} & set(actions), f"the Author is offered {actions}"
    require_role(author, ROLE_AUTHOR)
    forced = author.forced_transition("approve", entry.entry_id)
    author.evidence("149330_after_forced")
    attach("forced approve", forced)
    status = author.wait_row_status(entry, (STATUS_PENDING_REVIEW, STATUS_PUBLISHED), 20)
    assert not _hidden(sessions.visitor(), "QCTEST Author Card"), "the Author's card is public"
    assert status == STATUS_PENDING_REVIEW, f"PRODUCT: after the forced approve the badge reads {status!r}"
    assert forced["status"] >= 400, f"PRODUCT: the forced approve answered {forced}"
    if MSG_ACCESS_DENIED not in forced["body"]:
        record_finding("149330", "WORDING", expected=MSG_ACCESS_DENIED, shown=forced)


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
